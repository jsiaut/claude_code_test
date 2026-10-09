"""Phase 3 : assembler, mesurer (§11.1). Tout se recalcule depuis le cache et les fichiers
d'observations (§9.6) ; les huit tables sont exportées en Parquet, triées par clé primaire.

    python -m pipeline.assemble 2026-10-07
"""
import datetime as dt
import json
import sys
import time
from collections import Counter
from decimal import Decimal

import pandas as pd

from . import (annex_e, circularity, config, controls, controls_more, dimensional, documents, entities, events,
               fsignals, lender, links, load, measures, model, rank2, reader)
from .registry import MEASURES

NONE = "none"
TABLES = {"documents": ["doc_key"], "facts": ["fact_key"], "observations": ["obs_key"],
          "entities": ["entity_id", "record_kind", "ref", "valid_from"], "links": ["link_key"],
          "measures": ["measure", "subject", "counterparty", "period_start", "period_end", "view", "as_of", "term",
                       "breakdown_key", "financing_policy", "constant_perimeter", "variant"],
          "controls": ["control", "subject", "period_start", "period_end", "view", "as_of", "breakdown_key",
                       "mapping_variant"],
          "exclusions": ["exclusion_key"]}
MEASURE_PK = TABLES["measures"]
CTRL_PK = TABLES["controls"]


def _d(x):
    if x in (None, "", NONE) or (isinstance(x, float) and x != x):
        return None
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])


def insert(con, table, rows, cols=None):
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    cols = cols or [c[0] for c in con.execute(f"DESCRIBE {table}").fetchall()]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]
    pk = TABLES[table]
    df = df.drop_duplicates(pk, keep="last")
    types = {c[0]: c[1] for c in con.execute(f"DESCRIBE {table}").fetchall()}
    sel = []
    for c in cols:
        t = types[c]
        if t.startswith("DECIMAL"):
            df[c] = df[c].map(lambda v: None if v is None or (isinstance(v, float) and v != v) or v == "" else str(v))
            sel.append(f"CAST({c} AS {t}) AS {c}")
        elif t in ("DATE", "TIMESTAMP"):
            df[c] = df[c].map(lambda v: None if v is None or (isinstance(v, float) and v != v) or v in ("none", "", "NaT")
                              else str(v).replace("Z", "").replace("T", " ") if t == "TIMESTAMP" else str(v)[:10])
            sel.append(f"TRY_CAST({c} AS {t}) AS {c}")
        else:
            sel.append(c)
    con.register("df_ins", df)
    con.execute(f"INSERT INTO {table} SELECT {', '.join(sel)} FROM df_ins")
    con.unregister("df_ins")
    return len(df)


def windows(p0):
    out = {}
    for g, cal in p0["calendars"].items():
        w = cal["window"]
        out[g] = {k: _d(w[k]) for k in ("window_start", "extended_start", "reading_start", "window_first_fy_end")}
    return out


def deadline_fn(p0, groups):
    days = {"Large accelerated filer": 60, "Accelerated filer": 75}
    out = {}
    for g in groups:
        cat = next((m.get("category") for c, m in p0["meta"].items() if m["group"] == g and not m["is_predecessor"]), None)
        n = days.get(cat, 90)
        out[g] = (lambda n: (lambda fe: fe + dt.timedelta(days=n)))(n)
    return out


def run(as_of):
    t0 = time.time()
    cfg = config.load()
    p0 = json.loads((config.DB_DIR / "phase0.json").read_text())
    groups = [g for g in cfg["groups"] if g in p0["calendars"]]
    as_of_d = dt.date.fromisoformat(as_of)
    stats = {"as_of": as_of, "groups": groups}

    # 1. base XBRL : faits, correspondance de concepts, occurrences
    con, info = model.build_base(as_of)
    stats["base"] = info
    print("base", info, round(time.time() - t0), flush=True)

    # 2. observations validées (passe la plus récente de chaque bloc)
    catalog = reader.load_catalog()
    obs_rows, obs_excl = load.load_observations(con, catalog, as_of)
    valid = [o for o in obs_rows if o["validation_state"] == "valid"]
    stats["observations"] = {"lines": len(obs_rows), "valid": len(valid),
                             "kinds": dict(Counter(o["kind"] for o in obs_rows)),
                             "rejected_semantic": sum(1 for o in obs_rows if o["validation_state"] != "valid")}

    # 3. entités et arêtes
    discovered = {(b["filer_name"], str(int(b["cik"]))) for b in catalog
                  if b["block_kind"].startswith("discovery_") and b.get("filer_name")}
    ent_rows, reg = entities.build(p0, cfg, links.counterparty_names(obs_rows), discovered)
    edges, pend = links.build_edges(obs_rows, reg)
    rels = links.instrument_relations(edges)
    for o in obs_rows:
        e = entities.resolve(reg, o.get("counterparty_name"), links.edge_date(o))[0] if o.get("counterparty_name") else None
        o["counterparty_entity_id"] = e
    con.execute("UPDATE observations SET counterparty_entity_id = NULL")
    upd = pd.DataFrame([{"obs_key": o["obs_key"], "eid": o["counterparty_entity_id"]} for o in obs_rows
                        if o.get("counterparty_entity_id")])
    if not upd.empty:
        con.register("upd", upd)
        con.execute("UPDATE observations SET counterparty_entity_id = upd.eid FROM upd WHERE observations.obs_key = upd.obs_key")
        con.unregister("upd")

    # 4. calendriers et fenêtres
    cals = model.calendars()
    gw = windows(p0)
    deadlines = deadline_fn(p0, groups)
    quarters_by_group = {g: [q for q in cals[g]["quarters"] if q["start"] and q["end"] >= gw[g]["window_start"]
                             and q["end"] <= as_of_d] for g in groups}
    years_by_group = {g: circularity.fiscal_years(cals[g]["quarters"], gw[g]["window_start"], as_of_d) for g in groups}
    filings = pd.read_parquet(config.DB_DIR / "filings.parquet")
    filings["filingDate"] = filings["filingDate"].map(_d)

    # 5. mesures de rang 1 tirées des faits (phase 1), puis mesures dimensionnelles ; mesures de
    # rang 2 tirées des faits, codées après la seconde page (§11.1)
    cells = measures.group_measures(con, groups, as_of)
    cells += rank2.group_rank2(con, groups, as_of)
    cells += rank2.rpo_beyond(con, groups, as_of) + rank2.segments(con, groups, as_of) + \
        rank2.segment_expenses(con, groups, as_of) + rank2.supplier_concentration(con, groups, as_of)
    scope = cfg.get("scope") if isinstance(cfg.get("scope"), list) else []
    lender_excl = []
    if "lender" in scope:
        # bloc lender de §14 : positions des BDC rattachées aux entités du registre
        hold, bnum = lender.matched_holdings(lender.legal_names(ent_rows), ent_rows)
        insert(con, "facts", lender.bdc_facts(bnum))
        cells += lender.measures_cells(hold, as_of)
        lender_excl = lender.exclusions(as_of)
        stats["lender"] = {"facts": len(bnum), "holdings": len(hold), "bdc": int(hold["bdc_cik"].nunique()) if len(hold) else 0,
                           "groups": sorted(hold["group"].dropna().unique()) if len(hold) else [],
                           "ambiguous_identifiers": len(lender.AMBIGUOUS)}
    cells += dimensional.useful_lives(con, groups, None, as_of)
    lnc = dimensional.leases_not_commenced(con, groups, {g: [(a, b) for a, b, _ in years_by_group[g]] for g in groups}, as_of)
    cells += lnc
    lnc_keys = {(c["subject"], c["period_end"], c["term"]) for c in lnc if c["status"] == "computed"}
    cells = [c for c in cells if not (c["measure"] == "lease_not_commenced_bridge" and c["view"] == "revised"
                                      and c["status"] == "not_determinable"
                                      and (c["subject"], c["period_end"], c["term"]) in lnc_keys)]
    conc_cells, named_conc = dimensional.concentration(con, groups, as_of)
    cells += conc_cells
    occ = model.occurrences_df(con)
    series = {g: measures.Series(occ, g, cals[g]) for g in groups}

    def revenue(s, fs, fe, cutoff):
        t = series[s].duration("revenue_total", fs, fe, cutoff)
        return (t["value"], [t]) if t else (None, [])

    # 6. signaux de structure et signaux lus
    err = {}
    for g, acc, d in con.execute("""SELECT group_id, accession, min(filing_date) FROM facts
                                    WHERE concept = 'dei:DocumentFinStmtErrorCorrectionFlag'
                                      AND lower(coalesce(value_text, '')) = 'true' GROUP BY 1, 2""").fetchall():
        err.setdefault(g, []).append((acc, d))
    fl = filings.rename(columns={})
    sig_cells = events.structural_signals(groups, quarters_by_group, fl, as_of, err)
    blocks = {b["content_key"]: b for b in catalog}
    blocks_by_acc = {}
    for b in blocks.values():
        blocks_by_acc.setdefault(b["accession"], []).append(b)
    read_cks = {p.stem for p in config.OBS_DIR.glob("*.jsonl") if not p.name.endswith(".rejected.jsonl")}
    # groupes dont tout le texte du catalogue est lu, bloc text compris (§11.1, E.0) : un corps de
    # pièce exclu avec son motif (financial_parties_only) ne compte pas comme non lu
    text_open = isinstance(cfg.get("scope"), list) and "text" in cfg["scope"]
    unread = {b["group_id"] for b in catalog if b["content_key"] not in read_cks
              and not (b["block_kind"] == "exhibit_body" and not (text_open and reader.text_body(b)))}
    text_done = frozenset(g for g in groups if text_open and g not in unread)
    # une archive illisible laisse la recherche incomplète sur les trimestres dont la fenêtre de
    # rétrospection de F (huit trimestres, §3.2) couvre sa période
    lookback_days = 92 * cfg["thresholds"]["financed_lookback_quarters"]
    failed_until = {}
    for f in json.loads((config.DB_DIR / "phase1_failures.json").read_text()):
        r = filings[filings["accessionNumber"] == f["accession"]]
        if r.empty or not _d(r.iloc[0]["reportDate"]):
            continue
        g, until = r.iloc[0]["group_id"], _d(r.iloc[0]["reportDate"]) + dt.timedelta(days=lookback_days)
        failed_until[g] = max(failed_until.get(g, until), until)
    stats["text_done_groups"] = sorted(text_done)
    obs_by_ck = {}
    for o in valid:
        obs_by_ck.setdefault(o["content_key"], []).append(o)
    parsed = set(pd.read_parquet(config.DB_DIR / "xbrl_documents.parquet")["accession"])
    sig_cells += fsignals.observed_signals(groups, quarters_by_group, filings, blocks_by_acc, obs_by_ck, read_cks,
                                           parsed, as_of)
    report_end_of = {a: _d(r) for a, r in zip(filings["accessionNumber"], filings["reportDate"]) if r}
    debt_note_accs = frozenset(b["accession"] for b in catalog if b["block_kind"] == "debt_note")
    sig_cells += fsignals.covenant_signals(groups, quarters_by_group, valid, as_of, report_end_of, text_done, filings,
                                           debt_note_accs)
    sig_cells += fsignals.pledged_signals(groups, quarters_by_group, valid, as_of, report_end_of, text_done, filings,
                                          debt_note_accs)
    cells += rank2.lease_not_commenced(cells, valid, report_end_of, as_of)
    lever = rank2.depreciation_lever(cells, valid, as_of)
    cells += lever + rank2.lever_restatement(con, lever, as_of)
    cells += sig_cells

    # 7. flux après financement des contreparties, matrice d'exposition tirée du texte
    mdf = pd.DataFrame(cells)
    cells = [c for c in cells if c["measure"] != "fcf_after_counterparty_financing"]
    cells += fsignals.counterparty_financing(groups, quarters_by_group, edges, mdf, as_of, text_done)
    cells += fsignals.exposure_from_observations(valid, as_of)

    # 8. circularité : paires, statut financé, dépendances, couverture, exposition par contrepartie
    pairs = circularity.build_pairs(edges, set(groups))
    censored = {"CRWV"}        # history_left_censored (plan.md, phase 0)
    rd = model.original_report_dates(con)
    # notes de revenu des 10-K lues (bloc text) : leurs exercices ne sont plus « non traités »
    fil = pd.read_parquet(config.DB_DIR / "filings.parquet", columns=["accessionNumber", "reportDate"])
    acc_rd = {a: str(r)[:10] for a, r in zip(fil["accessionNumber"], fil["reportDate"])
              if r is not None and len(str(r)) >= 10 and str(r)[:4].isdigit()}
    rev_read = frozenset((o["group_id"], dt.date.fromisoformat(acc_rd[o["accession"]])) for o in obs_rows
                         if o["block_kind"] == "revenue_note" and str(o.get("form") or "").startswith("10-K")
                         and o["validation_state"] == "valid" and o["accession"] in acc_rd)
    # découverte ouverte (§14, D-0037) : état de la recherche côté client hors périmètre
    client_state = None
    if isinstance(cfg.get("scope"), list) and "discovery" in cfg["scope"]:
        from . import discovery
        client_state = discovery.client_states(read_cks, min(w["extended_start"] for w in gw.values()))
    pc, ev = circularity.pair_measures(pairs, cals, gw, revenue, conc_cells, named_conc, obs_rows, reg, as_of,
                                       deadlines, rd, cfg["thresholds"]["financed_lookback_quarters"], censored,
                                       rev_notes_read=rev_read, text_done=text_done, failed_until=failed_until,
                                       client_state=client_state)
    cells += pc
    cells += circularity.coverage_cells(groups, cals, gw, revenue, conc_cells, named_conc, pairs, edges, as_of, ev,
                                        text_done)
    cells += circularity.counterparty_exposure(pairs, ev, cals, as_of, text_done)
    cells += annex_e.evaluate(ev, cfg, gw, deadlines, as_of)
    stats["pairs"] = {f"{s}->{c}": {"structure": e["structure"], "linkage": e["linkage"], "conclusion": e["conclusion"],
                                    "edges": len(e["pair"].edges),
                                    "active_quarters": sum(1 for v in e["F"]["as_known"]["exposure_outstanding"].values()
                                                           if v[0] == "active")}
                      for (s, c), e in sorted(ev.items())}

    # 9. événements de l'annexe F
    mdf = pd.DataFrame(cells)
    obs_by_group = {}
    for o in valid:
        obs_by_group.setdefault(o["group_id"], []).append(o)
    cells += fsignals.fragility_events(groups, quarters_by_group, mdf, sig_cells, obs_by_group, filings, read_cks,
                                       blocks_by_acc, as_of, text_done)

    # 10. invariants d'agrégat (§7.6) sur les sommes d'arêtes
    inv_excl = invariants(cells, edges, rels, reg)

    # 11. univers attendu : chaque cellule attendue a un état (§7.5)
    cells, missing = fill_expected(cells, as_of)
    stats["expected_missing_filled"] = missing
    n_meas = insert(con, "measures", cells)

    # 12. contrôles
    ctrl = controls.run(con, as_of)
    ctrl += c5_bilateral(ev, gw, as_of)
    ctrl += controls_more.debt_rollforward(con, as_of)
    ctrl += controls_more.segments_and_disaggregation(con, as_of)
    ctrl = control_views(ctrl, filings)
    n_ctrl = insert(con, "controls", ctrl)

    # 13. paires non additives : lignes de montant et relations candidates
    amount_rows = amount_rows_for_pairs(edges, valid, con)
    cand, counts = links.pair_candidates(cfg["non_additive_pairs"], amount_rows)
    stats["non_additive_candidates"] = counts
    link_rows = [{k: v for k, v in l.items() if not k.startswith("_")} for l in edges] + rels + cand
    n_links = insert(con, "links", link_rows)
    n_ent = insert(con, "entities", ent_rows)

    # 14. documents
    failed = {f["accession"] for f in json.loads((config.DB_DIR / "phase1_failures.json").read_text())}
    used = set(con.execute("SELECT DISTINCT accession FROM facts").fetchdf()["accession"]) | {b["accession"] for b in catalog}
    docs = documents.build(as_of, used, failed)
    n_docs = insert(con, "documents", docs)

    # 15. exclusions
    excl = list(obs_excl) + inv_excl + lender_excl + exclusions(con, catalog, read_cks, ent_rows, filings, failed, as_of, p0)
    n_excl = load.insert_exclusions(con, excl)

    # 16. export
    out = config.ROOT / "tables"
    out.mkdir(exist_ok=True)
    for t, pk in TABLES.items():
        con.execute(f"COPY (SELECT * FROM {t} ORDER BY {', '.join(pk)}) TO '{out / (t + '.parquet')}' (FORMAT PARQUET)")
    stats["rows"] = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABLES}
    stats["seconds"] = round(time.time() - t0)
    (config.ROOT / "work" / "tmp" / "assemble_stats.json").write_text(json.dumps(stats, indent=1, default=str))
    print(json.dumps(stats["rows"]), stats["seconds"], "s", flush=True)
    return con, stats


def invariants(cells, edges, rels, reg):
    """§7.6 sur les sommes d'arêtes : niveau E ou F, devises mêlées, chevauchement non
    résolu, entité pending. Une violation exclut l'agrégat (invalid_aggregate)."""
    by = {l["link_key"]: l for l in edges}
    unresolved = {(r["a_key"], r["b_key"]) for r in rels if r["resolution"] == "unresolved"}
    out = []
    for c in cells:
        if c["measure"] not in ("counterparty_exposure", "fcf_after_counterparty_financing", "documented_revenue_dependency"):
            continue
        fl = json.loads(c["flags"]) if c.get("flags") else {}
        keys = fl.get("links") or (fl.get("financing_given", []) + fl.get("repayments_received", []))
        ls = [by[k] for k in keys if k in by]
        if not ls:
            continue
        bad = []
        if any(l["tier"] in ("E", "F") for l in ls):
            bad.append("a")
        if len({l["_obs"].get("unit") for l in ls}) > 1:
            bad.append("b")
        ks = {l["link_key"] for l in ls}
        if any(a in ks and b in ks for a, b in unresolved):
            bad.append("d")
        if any(l["from_group"] is None or l["to_group"] is None for l in ls):
            bad.append("g")
        if bad:
            # motif de la cellule : l'invariant violé, le plus spécifique d'abord ; (a) niveau E ou F :
            # une pièce non admissible dans un agrégat, précondition de la somme non remplie
            reason = {"d": "blocked_overlap", "b": "mixed_currency", "g": "pending_entity",
                      "a": "precondition_not_met"}
            c["status"] = "blocked_overlap" if bad == ["d"] else "not_determinable"
            c["nd_reason"] = next(reason[x] for x in ("d", "b", "g", "a") if x in bad)
            c["value"] = None
            out.append({"exclusion_key": f"invalid_aggregate:{c['measure']}:{c['subject']}:{c['counterparty']}:{c['period_end']}:{c['breakdown_key']}",
                        "item_kind": "aggregate", "item_key": f"{c['measure']}/{c['subject']}/{c['counterparty']}/{c['period_end']}",
                        "reason": "invalid_aggregate", "detail": "invariant(s) " + ",".join(bad), "group_id": c["subject"],
                        "invariant": ",".join(bad), "as_of": c["as_of"]})
    return out


def fill_expected(cells, as_of):
    exp = pd.read_parquet(config.DB_DIR / "expected_universe.parquet")
    have = {}
    for c in cells:
        have.setdefault((c["measure"], c["subject"], c["counterparty"], c["period_end"], c["term"]), []).append(c)
    added = 0
    out = list(cells)
    for r in exp.itertuples():
        if r.measure == "fragility_event":
            hit = [c for c in have.get((r.measure, r.subject, r.counterparty, r.period_end, r.term), [])
                   if c["breakdown_key"] == r.breakdown_key]
        else:
            hit = have.get((r.measure, r.subject, r.counterparty, r.period_end, r.term), [])
        if r.measure in ("exposure_matrix", "depreciation_life_published", "customer_concentration_anonymous",
                         "earnings_bridge_pretax", "named_edge_coverage", "visible_pairs_count", "lease_not_commenced_bridge",
                         "liq_principal_due_to_cash", "finance_lease_additions", "stock_paid_additions",
                         "vendor_financed_additions"):
            hit = hit or [c for c in cells if c["measure"] == r.measure and c["subject"] == r.subject
                          and c["period_end"] == r.period_end]
        if hit:
            continue
        for view in ("as_known", "revised") if MEASURES[r.measure][2] not in ("event",) and r.measure not in (
                "fragility_event", "named_edge_coverage", "visible_pairs_count") and not r.measure.startswith("sig_") else ("as_known",):
            out.append(measures.cell(r.measure, r.subject, None if r.period_start in (None, NONE) else r.period_start,
                                     r.period_end, view, as_of, term=r.term, breakdown=r.breakdown_key,
                                     status="not_determinable",
                                     nd_reason="concept_unresolved" if r.measure in ("depreciation_life_published",
                                                                                     "customer_concentration_anonymous") else "not_disclosed",
                                     flags={"expected_basis": r.basis}))
            added += 1
    return out, added


def control_views(rows, filings):
    """Un contrôle se calcule dans chaque dépôt qui publie la période ; il s'écrit une fois par
    vue (§8.3) : as_known lit le premier dépôt qui l'a publiée, revised le dernier connu à la
    date as_of. Les statuts obtenus dans les autres dépôts restent dans les preuves : un écart
    vu dans un comparatif n'est pas effacé par un accord vu ailleurs."""
    known = {}
    for f in filings.to_dict("records"):
        known[f["accessionNumber"]] = (str(f.get("acceptanceDateTime") or f.get("filingDate") or ""), f["accessionNumber"])
    keep, groups = [], {}
    pk = [c for c in CTRL_PK if c != "view"]
    for r in rows:
        if r["view"] != "as_known" or not r.get("accession"):
            keep.append(r)
            continue
        groups.setdefault(tuple(r[c] for c in pk), []).append(r)
    for key, rs in groups.items():
        rs = sorted(rs, key=lambda r: known.get(r["accession"], ("9999", r["accession"])))
        tested = [f"{r['accession']}:{r['status']}" for r in rs]
        for view, r, basis in (("as_known", rs[0], "first_publication"), ("revised", rs[-1], "latest_publication")):
            ev = json.loads(r["evidence"]) if r.get("evidence") else {}
            if len(rs) > 1:
                ev["filings_tested"] = tested
            ev["view_basis"] = basis
            keep.append({**r, "view": view, "evidence": json.dumps(ev, sort_keys=True, default=str)})
    return keep


def c5_bilateral(ev, gw, as_of):
    """C5 : écart entre les deux déclarations d'un même accord, à 45 jours près, sur quatre
    paires de bases comparables ; sinon not_testable."""
    out = []
    for (s, c), e in sorted(ev.items()):
        p = e["pair"]
        persp = {}
        for l in p.edges:
            if l["edge_evidence"] != "amount" or not l.get("instrument_key"):
                continue
            persp.setdefault(l["instrument_key"], {}).setdefault(l["_obs"]["group_id"], []).append(l)
        both = {ik: d for ik, d in persp.items() if s in d and c in d}
        ws = gw[s]["window_start"]
        if not both:
            out.append(controls.ctrl("c5_bilateral", s, ws, dt.date.fromisoformat(as_of), "as_known", as_of, "not_testable",
                                     breakdown=c, reason="aucun accord déclaré par les deux parties avec des bases comparables",
                                     evidence={"edges": len(p.edges)}))
            continue
        for ik, d in sorted(both.items()):
            a, b = d[s][0], d[c][0]
            if abs((a["_date"] - b["_date"]).days) > 45 or a["_obs"].get("unit") != b["_obs"].get("unit"):
                out.append(controls.ctrl("c5_bilateral", s, ws, dt.date.fromisoformat(as_of), "as_known", as_of,
                                         "not_testable", breakdown=f"{c}/{ik}", reason="dates à plus de 45 jours ou unités différentes"))
                continue
            va, vb = Decimal(str(a["amount"])), Decimal(str(b["amount"]))
            out.append(controls.ctrl("c5_bilateral", s, ws, dt.date.fromisoformat(as_of), "as_known", as_of,
                                     "ok" if va == vb else "mismatch", breakdown=f"{c}/{ik}", lhs=va, rhs=vb, tol=Decimal(0),
                                     explanation=None if va == vb else "bilateral_difference_published",
                                     evidence={"a": a["link_key"], "b": b["link_key"]}))
    return out


def amount_rows_for_pairs(edges, valid, con):
    rows = []
    for o in valid:
        if o["kind"] != "observation" or o.get("amount") is None:
            continue
        rows.append({"key": "obs:" + o["obs_key"], "group": o["group_id"],
                     "date": str(_d(o.get("period_end")) or _d(o.get("event_date")) or ""),
                     "instrument_key": o.get("instrument_key"), "category_id": o.get("category_id"),
                     "measurement_basis": o.get("measurement_basis"), "component_kind": o.get("component_kind"),
                     "stage": o.get("stage"), "block": o.get("exposure_block"),
                     "counterparty_group": o.get("counterparty_entity_id"), "source_perspective": "reporting_entity"})
    for g, q, pe, fk in con.execute("""SELECT group_id, model_quantity, CAST(period_end AS VARCHAR), min(fact_key)
                                     FROM facts WHERE model_quantity IN ('rpo_total', 'contract_liabilities',
                                       'accounts_payable', 'unpaid_capex') AND n_dims = 0 AND value IS NOT NULL
                                       AND source = 'instance'
                                     GROUP BY 1, 2, 3""").fetchall():
        rows.append({"key": fk, "group": g, "date": pe, "quantity": q})
    return rows


def exclusions(con, catalog, read_cks, ent_rows, filings, failed, as_of, p0):
    out = []

    def ex(kind, key, reason, detail, group=None, acc=None, ck=None):
        out.append({"exclusion_key": f"{reason}:{key}", "item_kind": kind, "item_key": key, "reason": reason,
                    "detail": detail, "group_id": group, "accession": acc, "content_key": ck, "as_of": as_of})
    sc = config.load().get("scope")
    text_open = isinstance(sc, list) and "text" in sc
    seen = set()
    for b in catalog:
        if b["content_key"] in seen:
            continue
        seen.add(b["content_key"])
        if b["content_key"] in read_cks:
            continue
        if b["block_kind"] == "exhibit_body" and not (text_open and reader.text_body(b)):
            ex("block", b["content_key"], "financial_parties_only",
               f"{b.get('exhibit_type')} {b.get('document')} : parties non déposantes établissements financiers seulement (en-tête lu)",
               b["group_id"], b["accession"], b["content_key"])
        elif b["block_kind"] == "exhibit_body":
            ex("block", b["content_key"], "not_processed",
               f"{b.get('exhibit_type')} {b.get('document')} : corps arrêté à l'en-tête au premier passage, bloc text de §14 non encore lu",
               b["group_id"], b["accession"], b["content_key"])
        elif b.get("signal_class") == 3:
            ex("block", b["content_key"], "not_processed", f"{b['block_kind']} : bloc text de §14 non encore lu",
               b["group_id"], b["accession"], b["content_key"])
        elif b["block_kind"].startswith("discovery_"):
            ex("block", b["content_key"], "not_processed",
               f"{b['block_kind']} de {b.get('filer_name')} : bloc discovery de §14 préparé, non encore lu",
               b["group_id"], b["accession"], b["content_key"])
        else:
            ex("block", b["content_key"], "not_processed", "bloc de la tranche non lu", b["group_id"], b["accession"],
               b["content_key"])
    for acc in sorted(failed):
        ex("filing", acc, "parse_failed", "archive XBRL illisible (phase 1)", acc=acc)
    for r in ent_rows:
        if r["record_kind"] == "entity" and r["status"] == "pending":
            ex("entity", r["entity_id"], "pending_entity", f"« {r['name']} » : identité non affirmée par une pièce (§10.2)")
    for row in con.execute("""SELECT fact_key, group_id, accession, concept FROM facts WHERE conflict""").fetchall():
        ex("fact", row[0], "conflicting", f"{row[3]} : écart supérieur à la tolérance d'arrondi ou saut d'échelle", row[1], row[2])
    drs = filings[filings["form"].fillna("").str.startswith("DRS")]
    for r in drs.itertuples():
        ex("filing", r.accessionNumber, "submitted_draft", f"{r.form} soumis, pas déposé (§2.1)", r.group_id, r.accessionNumber)
    for g in ("CRWV",):
        ex("group", g, "history_left_censored",
           "premier dépôt après le début de la période de lecture, aucun prédécesseur (plan.md)", g)
    ex("aggregate", "datacenter_securitizations", "not_public",
       "couche titrisée des datacenters : selon une réponse du personnel de la SEC du 29 juillet 2026, ces titres ne sont pas des asset-backed securities ; non documentable à la ligne (§5.2)")
    if not text_open:
        text_out = ("notes d'investissements, de dette, de baux et d'engagements ; texte autour des faits de concentration ; "
                    "8-K items 2.01 et 2.03 (bloc text de §14)")
        for g in p0["groups"]:
            ex("group", f"{g}:text_outside_first_pass", "not_processed", text_out, g)
    if isinstance(sc, list) and "discovery" in sc:
        out += discovery_exclusions(as_of)
    return out


def discovery_exclusions(as_of):
    """Bloc `discovery` (§14, D-0036) : unités de la file dont le bloc n'est pas encore préparé
    (non lues), archives de la période non tirées (leurs paires portent search_incomplete) et
    requêtes saturées sur un seul jour."""
    from . import discovery
    out = []

    def ex(kind, key, reason, detail, group=None, acc=None):
        out.append({"exclusion_key": f"{reason}:{key}", "item_kind": kind, "item_key": key, "reason": reason,
                    "detail": detail, "group_id": group, "accession": acc, "content_key": None, "as_of": as_of})
    if discovery.UNITS.exists():
        built = discovery.built_units()
        units = pd.read_parquet(discovery.UNITS)
        for u in units.itertuples(index=False):
            b = built.get(u.order)
            if b and b.get("content_key"):
                continue
            why = (b or {}).get("error") or "unité de la file de la découverte non encore préparée ni lue"
            ex("document", f"discovery:{u.adsh}/{u.doc}", "not_processed" if not (b or {}).get("error") else "not_collected",
               f"rang {u.rank}, passe {u._asdict()['pass']}, {u.kind} : {why} ; groupes nommés {u.groups}",
               "CP:cik" + str(u.cik), u.adsh)
    todo = discovery.in_period(discovery.archive_list(), discovery.period_start())
    done = set(discovery.scanned_archives())
    for a in todo:
        if a["name"] not in done:
            ex("period", f"notes:{a['name']}", "not_processed",
               f"archive des Notes Data Sets non tirée ({a['filed_from']} au {a['filed_to']}) : ses paires portent search_incomplete")
    qlog = discovery.QUERY_LOG
    if qlog.exists():
        for l in qlog.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            if r.get("status") == "saturated_single_day":
                ex("query", f"efts:{r['term']}:{r['start']}", "not_collected",
                   f"recherche plein texte saturée sur un jour ({r['term']}, {r['start']}) : résultats au-delà de 10 000 non vus")
    return out


if __name__ == "__main__":
    # l'ordre d'itération des ensembles de chaînes ne doit pas dépendre du processus (§9.6)
    if __import__("os").environ.get("PYTHONHASHSEED") != "0":
        __import__("os").environ["PYTHONHASHSEED"] = "0"
        __import__("os").execv(sys.executable, [sys.executable, "-m", "pipeline.assemble", *sys.argv[1:]])
    run(sys.argv[1])
