"""Phase 3 : assembler, mesurer (§11.1). Tout se recalcule depuis le cache et les fichiers
d'observations (§9.6) ; les huit tables sont exportées en Parquet, triées par clé primaire.

    python -m pipeline.assemble                 # reprend du mémo ce qui n'a pas changé (D-0062)
    python -m pipeline.assemble --sans-cache    # recalcule tout, mêmes tables à l'octet près
    python -m pipeline.assemble --apercu        # arêtes, paires et exposition comparées aux tables

L'as_of est la clé as_of de config.yaml (D-0073) ; un argument daté reste accepté s'il lui est égal.

Le mémo (db/memo, voir memo.py) garde les étapes qui ne lisent pas les observations et les plages des
citations : seules les observations peuvent changer pour qu'une étape soit reprise.
"""
import datetime as dt
import json
import subprocess
import sys
import time
from collections import Counter
from decimal import Decimal

import pandas as pd

from . import (annex_e, backlog, circularity, config, controls, controls_more, dimensional, documents, entities, events,
               fsignals, lender, lender_liabilities, lender_portfolio, links, load, measures, memo, model, montages, rank2,
               sb_own, sixk, reader)
from .phase0 import PERIODIC as PERIODIC_FORMS
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


PK_DUPLICATES = {}      # doublons de clé primaire écartés par insert, par table (D-0069, point 9)
PK_COLLISIONS = {}      # clés en collision, toutes, écrites dans work/tmp/pk_collisions.json


def insert(con, table, rows, cols=None):
    """Insère des lignes ; deux lignes de même clé primaire n'en font qu'une, la dernière, et le doublon est
    compté dans PK_DUPLICATES : identique, ou en collision quand les deux lignes diffèrent."""
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    cols = cols or [c[0] for c in con.execute(f"DESCRIBE {table}").fetchall()]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]
    pk = TABLES[table]
    dup = df.duplicated(pk, keep=False)
    if dup.any():
        sub = df[dup].astype(str)
        distinct = sub.groupby(pk, sort=False).apply(lambda x: len(x.drop_duplicates()), include_groups=False)
        rec = PK_DUPLICATES.setdefault(table, {"dropped": 0, "collision_keys": 0, "by_first_key": {}, "examples": []})
        rec["dropped"] += len(sub) - len(distinct)
        coll = [list(k) if isinstance(k, tuple) else [k] for k in distinct[distinct > 1].index]
        rec["collision_keys"] += len(coll)
        for k in coll:
            rec["by_first_key"][k[0]] = rec["by_first_key"].get(k[0], 0) + 1
        rec["examples"] = (rec["examples"] + coll[:10])[:10]
        PK_COLLISIONS.setdefault(table, []).extend(coll)
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


def phase1_failures():
    """Échecs de la phase 1, sauf l'amendement sans instance XBRL : il ne contient aucun état
    financier (tout état financier d'un rapport périodique est balisé, Reg S-T 405) et ne remplace
    que des pièces ou la partie III ; rien n'y est illisible."""
    out = []
    for f in json.loads((config.DB_DIR / "phase1_failures.json").read_text()):
        if str(f.get("form") or "").endswith("/A") and f.get("error") == "pas d'instance XBRL dans le dépôt":
            continue
        out.append(f)
    return out


def windows(p0):
    out = {}
    for g, cal in p0["calendars"].items():
        w = cal["window"]
        out[g] = {k: _d(w[k]) for k in ("window_start", "extended_start", "reading_start", "window_first_fy_end")}
    return out


def plus_months(d, n):
    """d plus n mois ; une fin de mois donne la fin du mois d'arrivée."""
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    last = ((dt.date(y + 1, 1, 1) if m == 12 else dt.date(y, m + 1, 1)) - dt.timedelta(days=1)).day
    return dt.date(y, m, last if (d + dt.timedelta(days=1)).day == 1 else min(d.day, last))


def deadline_fn(p0, groups, filings=None):
    """Date limite de dépôt du rapport annuel de chaque exercice (E.0) : quatre mois après la fin
    d'exercice pour un 20-F, sinon 60, 75 ou 90 jours selon la catégorie du déposant. Le formulaire est
    celui du rapport annuel original de l'exercice, à défaut celui du dernier antérieur (D-0069, point 7)."""
    days = {"Large accelerated filer": 60, "Accelerated filer": 75}
    fil = filings if filings is not None else pd.read_parquet(config.DB_DIR / "filings.parquet")
    ann = fil[fil["form"].isin(("10-K", "10-KT", "20-F", "40-F")) & fil["reportDate"].notna()]
    out = {}
    for g in groups:
        cat = next((m.get("category") for c, m in p0["meta"].items() if m["group"] == g and not m["is_predecessor"]), None)
        reps = sorted({(_d(r), f) for r, f in ann.loc[ann["group_id"] == g, ["reportDate", "form"]].itertuples(index=False)})

        def fn(fe, n=days.get(cat, 90), reps=reps):
            near = [f for r, f in reps if abs((r - fe).days) <= 7]
            before = [f for r, f in reps if r < fe]
            form = near[-1] if near else (before[-1] if before else None)
            return plus_months(fe, 4) if form == "20-F" else fe + dt.timedelta(days=n)
        out[g] = fn
    return out


def run(as_of, use_cache=True, apercu=False):
    """Les huit tables. use_cache=False recalcule tout (le mémo est réécrit). apercu=True s'arrête
    après les paires et l'exposition, sans rien exporter, et renvoie ce qu'il faut pour les comparer
    aux tables (voir apercu)."""
    t0 = time.time()
    as_of = config.as_of(as_of)
    cfg = config.load()
    p0 = json.loads((config.DB_DIR / "phase0.json").read_text())
    config.check_as_of(p0["as_of"], "db/phase0.json", "relancer la phase 0")     # inventaire et fenêtres au même as_of
    groups = [g for g in cfg["groups"] if g in p0["calendars"]]
    as_of_d = dt.date.fromisoformat(as_of)
    stats = {"as_of": as_of, "groups": groups}
    # exécution précédente : le dernier commit des tables que cet assemblage remplace ; delta.md s'y compare
    # (D-0069, point 8)
    prev = subprocess.run(["git", "log", "-1", "--format=%H %cI", "--", "tables/measures.parquet"],
                          capture_output=True, text=True, cwd=config.ROOT).stdout.split()
    stats["previous_tables"] = {"commit": prev[0], "date": prev[1]} if len(prev) == 2 else None
    PK_DUPLICATES.clear()
    PK_COLLISIONS.clear()
    load.EXCL_DUPLICATES.update(dropped=0, collision_keys=0, examples=[])
    # étapes qui ne lisent pas les observations : reprises du mémo si rien d'autre n'a changé (D-0062)
    M = memo.Memo(memo.inputs_fingerprint(), use=use_cache)

    # 1. base XBRL : faits, correspondance de concepts, occurrences
    # l'aperçu travaille sur sa propre base : celle du dernier réassemblage reste intacte
    db_path = config.DB_DIR / "apercu.duckdb" if apercu else load.DB_PATH
    con, info = M.database("base", db_path, lambda: model.build_base(as_of, db_path), key=as_of)
    stats["base"] = info
    print("base", info, round(time.time() - t0), flush=True)

    # 2. observations validées (passe la plus récente de chaque bloc)
    catalog = reader.load_catalog()
    obs_rows, obs_excl = load.load_observations(con, catalog, as_of, use_memo=use_cache)
    valid = [o for o in obs_rows if o["validation_state"] == "valid"]
    stats["observations"] = {"lines": len(obs_rows), "valid": len(valid),
                             "kinds": dict(Counter(o["kind"] for o in obs_rows)),
                             "rejected_semantic": sum(1 for o in obs_rows if o["validation_state"] != "valid")}

    # 3. entités et arêtes
    canon = load.canonical_filers(catalog)
    discovered = {(n, c) for c, n in canon.items()}
    former = {(b["filer_name"], str(int(b["cik"]))) for b in catalog
              if b["block_kind"].startswith("discovery_") and b.get("filer_name")} - discovered
    ent_rows, reg = entities.build(p0, cfg, links.counterparty_names(obs_rows), discovered, former)
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
    # dépôts du déclarant légal antérieurs à une fusion inversée : hors du groupe (D-0043)
    from .phase0 import pre_combination_accessions
    pre_acc = pre_combination_accessions(filings.to_dict("records"), cfg)
    filings = filings[~filings["accessionNumber"].isin(pre_acc)].reset_index(drop=True)
    stats["pre_combination_filings"] = len(pre_acc)

    # 5. mesures de rang 1 tirées des faits (phase 1), puis mesures dimensionnelles ; mesures de
    # rang 2 tirées des faits, codées après la seconde page (§11.1)
    cells = M.value("facts_measures", lambda: (
        measures.group_measures(con, groups, as_of) + rank2.group_rank2(con, groups, as_of) +
        rank2.rpo_beyond(con, groups, as_of) + rank2.segments(con, groups, as_of) +
        rank2.segment_expenses(con, groups, as_of) + rank2.supplier_concentration(con, groups, as_of) +
        rank2.lessor_lease_receipts(con, groups, as_of)), key=as_of)
    # D-0068, volet 1 : un RPO total tiré du fait « à partir du lendemain de la clôture » le dit en drapeau
    next_day = {r[0] for r in con.execute("SELECT fact_key FROM rpo_next_day").fetchall()}
    for c in cells:
        if c["measure"] == "rpo_total" and c.get("lineage") and next_day & set(json.loads(c["lineage"])):
            fl = json.loads(c["flags"]) if c.get("flags") else {}
            c["flags"] = json.dumps(dict(fl, derived_from="timing_axis_next_day"), sort_keys=True, default=str)
    # l'aperçu ne compare pas ces cellules, mais une mesure qu'il compare peut en avoir (exposure_matrix)
    facts_ids = {id(c) for c in cells}
    scope = cfg.get("scope") if isinstance(cfg.get("scope"), list) else []
    lender_excl = []
    added = []          # faits ajoutés en cours d'exécution : leur empreinte entre dans la clé des étapes qui les lisent
    if "lender" in scope:
        # bloc lender de §14 : positions des BDC rattachées aux entités du registre ; le rattachement ne
        # dépend que des lignes du registre (et des données des BDC), ses listes d'écarts comprises
        def holdings():
            hold, bnum = lender.matched_holdings(lender.legal_names(ent_rows), ent_rows)
            return hold, bnum, dict(lender.AMBIGUOUS), list(lender.SUBTOTALS)
        hold, bnum, ambiguous, subtotals = M.value("lender_holdings", holdings, key=memo.digest(ent_rows))
        lender.AMBIGUOUS.clear()
        lender.AMBIGUOUS.update(ambiguous)
        lender.SUBTOTALS[:] = subtotals
        bdc_rows = lender.bdc_facts(bnum)
        insert(con, "facts", bdc_rows)
        added.append(bdc_rows)
        cells += lender.measures_cells(hold, as_of)
        lender_excl = lender.exclusions(as_of)
        stats["lender"] = {"facts": len(bnum), "holdings": len(hold), "bdc": int(hold["bdc_cik"].nunique()) if len(hold) else 0,
                           "groups": sorted(hold["group"].dropna().unique()) if len(hold) else [],
                           "ambiguous_identifiers": len(lender.AMBIGUOUS)}
    # bloc labs (D-0060, volet 3) : faits balisés qui nomment un laboratoire ; ceux des Notes Data Sets entrent
    # dans facts (source nds_num), avec leur accession et leur emplacement, comme les faits des BDC
    lab_facts = []
    if "labs" in scope:
        from . import labs
        lab_facts, lab_st = labs.retained()
        nds_rows = labs.nds_fact_rows(lab_facts)
        insert(con, "facts", nds_rows)
        added.append(nds_rows)
        groups_by_cik = {str(c).zfill(10): m["group"] for c, m in p0["meta"].items()}
        lab_cells = [] if apercu else labs.tagged_value_cells(lab_facts, reg, obs_rows, as_of, groups_by_cik)
        cells += lab_cells
        stats["labs_tagged"] = {**lab_st, "cells": len(lab_cells),
                                "conflicts": sum(1 for c in lab_cells if c["flags"] and '"conflict"' in c["flags"])}
    added_key = f"{as_of}|{memo.digest(added)}"
    if not apercu:
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
    sig_cells = [] if apercu else events.structural_signals(groups, quarters_by_group, fl, as_of, err, valid)
    # un même texte revient parfois à l'identique dans plusieurs dépôts (Item 4 d'Amazon d'un
    # trimestre à l'autre, doute sur la continuité de Core Scientific) : lu une fois, il reste
    # rattaché à chacun de ses dépôts (D-0043)
    blocks_by_acc = {}
    for b in catalog:
        lst = blocks_by_acc.setdefault(b["accession"], [])
        if all(x["content_key"] != b["content_key"] for x in lst):
            lst.append(b)
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
    for f in phase1_failures():
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
    report_end_of = {a: _d(r) for a, r in zip(filings["accessionNumber"], filings["reportDate"]) if r}
    debt_note_accs = frozenset(b["accession"] for b in catalog if b["block_kind"] == "debt_note")
    if not apercu:
        sig_cells += fsignals.observed_signals(groups, quarters_by_group, filings, blocks_by_acc, obs_by_ck, read_cks,
                                               parsed, as_of)
        sig_cells += fsignals.covenant_signals(groups, quarters_by_group, valid, as_of, report_end_of, text_done, filings,
                                               debt_note_accs)
        sig_cells += fsignals.pledged_signals(groups, quarters_by_group, valid, as_of, report_end_of, text_done, filings,
                                              debt_note_accs)
    cells += rank2.lease_not_commenced(cells, valid, report_end_of, as_of)
    if not apercu:
        lever = rank2.depreciation_lever(cells, valid, as_of)
        cells += lever + rank2.lever_restatement(con, lever, as_of)
    cells += sig_cells

    # 7. flux après financement des contreparties, matrice d'exposition tirée du texte
    if not apercu:
        mdf = pd.DataFrame(cells)
        cells = [c for c in cells if c["measure"] != "fcf_after_counterparty_financing"]
        cells += fsignals.counterparty_financing(groups, quarters_by_group, edges, mdf, as_of, text_done)
    cells += fsignals.exposure_from_observations(valid, as_of)

    # 8. circularité : paires, statut financé, dépendances, couverture, exposition par contrepartie
    pairs = circularity.build_pairs(edges, set(groups))
    # history_left_censored (phase 0) : premier dépôt du groupe, ou réalisation d'une fusion inversée
    # (D-0043), postérieur au début de la période de lecture
    censored = {g for g in groups if p0["calendars"][g].get("history_left_censored")}
    rd = model.original_report_dates(con)
    # notes de revenu des 10-K lues (bloc text) : leurs exercices ne sont plus « non traités »
    fil = pd.read_parquet(config.DB_DIR / "filings.parquet", columns=["accessionNumber", "reportDate"])
    acc_rd = {a: str(r)[:10] for a, r in zip(fil["accessionNumber"], fil["reportDate"])
              if r is not None and len(str(r)) >= 10 and str(r)[:4].isdigit()}
    rev_read = frozenset((o["group_id"], dt.date.fromisoformat(acc_rd[o["accession"]])) for o in obs_rows
                         if o["block_kind"] == "revenue_note" and str(o.get("form") or "").startswith(("10-K", "20-F"))
                         and o["validation_state"] == "valid" and o["accession"] in acc_rd)
    # découverte ouverte (§14, D-0037) : état de la recherche côté client hors périmètre
    client_state = None
    if isinstance(cfg.get("scope"), list) and "discovery" in cfg["scope"]:
        from . import discovery
        # dénominations d'EDGAR : ne dépendent que du cache, reprises du mémo
        client_state = discovery.client_states(read_cks, min(w["extended_start"] for w in gw.values()),
                                               names=M.value("edgar_names", discovery.edgar_names))
    # D-0068 : carnet attribué par le vendeur (faits balisés par client, lignes de carnet) et ses dénominateurs publiés
    lex_terms = {}
    for k in ("seed", "confirmed"):
        for x in ((cfg.get("discovery") or {}).get("lexicon") or {}).get(k) or []:
            lex_terms.setdefault(x["ref"], set()).add(x["term"])
    clients_of = backlog.sellers([(l["from_group"], l["to_group"], l["family"], l["elimination_status"]) for l in edges],
                                 set(groups))
    lab_groups = {r["ref"] for r in ent_rows if r["record_kind"] == "membership" and str(r["ref"]).startswith("LAB:")}
    group_names = {}

    def names_of(g):
        if g not in group_names:
            group_names[g] = circularity.names_of_group(reg, g) | lex_terms.get(g, set())
        return group_names[g]
    tagged_rpo = [f for f in backlog.tagged_customer_rpo(
        rank2._facts(con, "dims LIKE '%srt:MajorCustomersAxis%' AND concept LIKE '%RemainingPerformanceObligation%' "
                          "AND value IS NOT NULL").to_dict("records"),
        lambda s: {g: names_of(g) for g in (clients_of.get(s, set()) | lab_groups) if g != s}) if f["group_id"] in groups]
    carnet = [o for o in backlog.carnet_lines(obs_rows, lambda n, d: entities.resolve(reg, n, d)[1]
                                               or entities.resolve(reg, n, d, "revised")[1]) if o["group_id"] in groups]
    known = backlog.known_values(edges)
    bl = backlog.Inputs(tagged_rpo, carnet, *([c for c in cells if c["measure"] == m]
                                              for m in ("rpo_total", "rpo_beyond_12m", "lessor_lease_receipts")),
                        known=known)
    stats["backlog"] = {"tagged_customer_rpo": len(tagged_rpo), "carnet_lines": len(carnet), "pairs": len(bl.pairs()),
                        "known_value_edges": len(known)}
    # D-0071, volet A : déclarations de détention (13F, 13D, 13G) ; une sortie publiée ferme les détentions en actions
    own_exits, own_excl = {}, []
    if "ownership" in scope:
        from . import ownership
        ocells, oexits, own_excl, ost = M.value("ownership", lambda: ownership.build(ent_rows, reg, as_of),
                                                key=memo.digest([ent_rows, as_of]))
        cells += ocells
        own_exits = ownership.closing_ends(oexits)
        stats["ownership"] = dict(ost, exits_by_pair={f"{s}->{c}": [e["date"] for e in v] for (s, c), v in sorted(oexits.items())})
    pc, ev = circularity.pair_measures(pairs, cals, gw, revenue, conc_cells, named_conc, obs_rows, reg, as_of,
                                       deadlines, rd, cfg["thresholds"]["financed_lookback_quarters"], censored,
                                       rev_notes_read=rev_read, text_done=text_done, failed_until=failed_until,
                                       client_state=client_state, backlog=bl,
                                       closings=circularity.closing_index(edges), exits=own_exits)
    cells += pc
    # D-0068, volet 3 : part du carnet contracté d'un vendeur attribuée à un client nommé (rang 2, §14)
    cells += backlog.share_cells(bl, {g: [q["end"] for q in cals[g]["quarters"] if q["end"] <= as_of_d] for g in groups},
                                 as_of)
    cells += circularity.coverage_cells(groups, cals, gw, revenue, conc_cells, named_conc, pairs, edges, as_of, ev,
                                        text_done)
    cells += circularity.counterparty_exposure(pairs, ev, cals, as_of, text_done)
    # bloc labs (D-0060, volet 4) : grand livre par laboratoire, au dernier montant connu de chaque instrument
    if "labs" in scope:
        ledger = labs.ledger_cells(edges, as_of)
        cells += ledger
        stats["labs_ledger"] = {"cells": len(ledger), "partners": len({(c["subject"], c["counterparty"]) for c in ledger})}
    # bloc paths de §14 : cycles orientés de longueur 2 ou 3 entre groupes (documented_path, E.6, D-0041)
    path_list = None
    if "paths" in scope:
        from . import paths as path_block
        pcfg = cfg.get("paths") or {}
        path_cells, path_list = path_block.path_measures(
            edges, obs_rows, reg, groups, gw, as_of, text_done, {k: e["linkage"] for k, e in ev.items()},
            tuple(pcfg.get("lengths", (2, 3))), int(pcfg.get("temporal_max_quarters", 4)))
        cells += path_cells
        stats["paths"] = {"cycles": len(path_list), "by_length": dict(Counter(len(x["nodes"]) for x in path_list)),
                          "by_temporal_conclusion": dict(Counter(f"{x['temporal']}|{x['conclusion']}" for x in path_list))}
    cells += annex_e.evaluate(ev, cfg, gw, deadlines, as_of, paths=path_list)
    if apercu:
        # aperçu : les invariants d'agrégat et l'univers attendu, comme aux étapes 10 et 11, puis arrêt ;
        # `computed` : les cellules que l'aperçu a calculées (l'univers attendu en ajoute pour toutes les mesures)
        invariants(cells, edges, rels, reg)
        computed = [c for c in cells if id(c) not in facts_ids]
        cells, _ = fill_expected(cells, as_of)
        stats["memo"] = {"hits": M.hits, "misses": M.misses}
        stats["seconds"] = round(time.time() - t0)
        return {"cells": cells, "computed": computed, "edges": edges, "ev": ev, "paths": path_list, "stats": stats}
    # bloc form_d de §14 : montant vendu par offre, émetteurs du périmètre et véhicules tiers (D-0041)
    formd_rels, formd_excl = [], []
    if "form_d" in scope:
        from . import formd
        fcells, formd_rels, formd_excl, fst = formd.build(reg, as_of, cfg, p0)
        cells += fcells
        stats["form_d"] = fst
    # volet F de D-0058 : obligations de SoftBank valorisées par les fonds (Form N-PORT Data Sets)
    nport_excl = []
    if "nport" in scope:
        from . import nport
        ncells = M.value("nport", lambda: nport.cells(as_of), key=as_of)
        cells += ncells
        nport_excl = nport.exclusions(as_of)
        stats["nport"] = {"cells": len(ncells), "securities": len({c["breakdown_key"] if isinstance(c, dict) else c.breakdown_key
                                                                   for c in ncells})}
        # D-0065 et D-0066 : non-cotés du modèle et marques de crédit ; le rattachement dépend des lignes du registre
        ucells, uexcl = M.value("nport_unlisted", lambda: nport.unlisted(as_of, ent_rows, reg), key=memo.digest([ent_rows, as_of]))
        cells += ucells
        nport_excl += uexcl
        stats["nport_unlisted"] = {m: sum(1 for c in ucells if (c["measure"] if isinstance(c, dict) else c.measure) == m)
                                   for m in ("nport_equity_mark", "nport_equity_held", "nport_credit_mark")}
        # D-0071, volet B : obligations d'Oracle, de CoreWeave et de Beignet, même mesure que celles de SoftBank
        bcells = M.value("nport_bonds", lambda: nport.bond_cells(as_of), key=as_of)
        cells += bcells
        nport_excl += nport.bond_exclusions(as_of)
        stats["nport_bonds"] = dict(Counter(c["subject"] if isinstance(c, dict) else c.subject for c in bcells))
    # D-0067 : clauses des contrats, capacités et événements propres aux laboratoires (hors annexe F)
    if "labs" in scope:
        from . import lab_terms
        party_terms = {b["content_key"]: b["party_terms"] for b in catalog if b.get("party_terms")}
        filer_names = {b["content_key"]: b["filer_name"] for b in catalog
                       if str(b.get("group_id") or "").startswith("CP:") and b.get("filer_name")}
        lt = lab_terms.cells(valid, reg, [c for c in cells if isinstance(c, dict) and c.get("measure") == "nport_equity_mark"],
                             as_of, party_terms, filer_names)
        cells += lt
        stats["lab_terms"] = dict(Counter(f"{c['measure']}|{c.get('value_text') or c['status']}"
                                          if c["measure"] == "lab_event" else c["measure"] for c in lt))
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
    # bloc lender_portfolio (D-0045) : portefeuille entier de chaque BDC, puis F11 à F13 par véhicule
    lp_excl = []
    if "lender_portfolio" in scope:
        lp = M.value("lender_portfolio", lambda: lender_portfolio.cells(as_of), key=as_of)
        cells += lp
        lp_excl = lender_portfolio.exclusions(as_of)
        stats["lender_portfolio"] = {
            "vehicles": len({c["subject"] for c in lp}),
            "cells": dict(Counter(f"{c['measure']}|{c['status']}" for c in lp if c["measure"] != "fragility_event")),
            "events": dict(Counter(f"{c['breakdown_key']}|{c['value_text'] or c['nd_reason']}" for c in lp
                                   if c["measure"] == "fragility_event"))}
    # bloc lender_liabilities (D-0047) : passif des mêmes véhicules, offres de rachat, F14 à F16
    ll_excl = []
    if "lender_liabilities" in scope:
        ll = M.value("lender_liabilities", lambda: lender_liabilities.cells(as_of), key=as_of)
        cells += ll
        ll_excl = lender_liabilities.exclusions(as_of)
        stats["lender_liabilities"] = {
            "vehicles": len({c["subject"] for c in ll}),
            "cells": dict(Counter(f"{c['measure']}|{c['status']}" for c in ll if c["measure"] != "fragility_event")),
            "events": dict(Counter(f"{c['breakdown_key']}|{c['value_text'] or c['nd_reason']}" for c in ll
                                   if c["measure"] == "fragility_event"))}

    # 10. invariants d'agrégat (§7.6) sur les sommes d'arêtes
    inv_excl = invariants(cells, edges, rels, reg)

    # 11. univers attendu : chaque cellule attendue a un état (§7.5)
    cells, missing = fill_expected(cells, as_of)
    stats["expected_missing_filled"] = missing
    insert(con, "measures", cells)

    # 12. contrôles (ceux qui ne lisent que les faits : repris du mémo, faits ajoutés compris dans la clé)
    ctrl = M.value("controls", lambda: controls.run(con, as_of), key=added_key)
    ctrl += c5_bilateral(ev, gw, as_of)
    ctrl += M.value("controls_more", lambda: controls_more.debt_rollforward(con, as_of) +
                    controls_more.segments_and_disaggregation(con, as_of), key=added_key)
    ctrl = control_views(ctrl, filings)
    insert(con, "controls", ctrl)

    # 13. paires non additives : lignes de montant et relations candidates
    amount_rows = amount_rows_for_pairs(edges, valid, con)
    cand, counts = links.pair_candidates(cfg["non_additive_pairs"], amount_rows)
    stats["non_additive_candidates"] = counts
    link_rows = [{k: v for k, v in l.items() if not k.startswith("_")} for l in edges] + rels + cand + formd_rels
    insert(con, "links", link_rows)
    insert(con, "entities", ent_rows)

    # 14. documents
    failed = {f["accession"] for f in phase1_failures()}
    used = set(con.execute("SELECT DISTINCT accession FROM facts").fetchdf()["accession"]) | {b["accession"] for b in catalog}
    if "form_d" in scope:
        from . import formd
        if formd.FILINGS.exists():
            fd = pd.read_parquet(formd.FILINGS, columns=["adsh", "parse_state"])
            used |= set(fd.loc[fd["parse_state"] == "parsed", "adsh"])
    docs = M.value("documents", lambda: documents.build(as_of, used, failed),
                   key=memo.digest([as_of, sorted(map(str, used)), sorted(failed)]))
    insert(con, "documents", docs)

    # 15. exclusions
    # bloc montages (D-0046) : relevés de portefeuille non lus, pièces sans fenêtre, fenêtres au-delà du plafond
    mt_excl = montages.exclusions(as_of) if "montages" in scope else []
    # 6-K des groupes émetteurs étrangers (D-0048) : sans fenêtre, hors texte, au-delà du plafond
    mt_excl += sixk.exclusions(as_of)
    # dépôts propres de SoftBank et déposants contrôlés (D-0058, volets B et C) : plafonds et formulaires non lus
    mt_excl += sb_own.exclusions(as_of)
    excl = list(obs_excl) + inv_excl + lender_excl + lp_excl + ll_excl + mt_excl + formd_excl + nport_excl + own_excl + \
        exclusions(con, catalog, read_cks, ent_rows, filings, failed, as_of, p0)
    load.insert_exclusions(con, excl)

    # 16. export
    out = config.ROOT / "tables"
    out.mkdir(exist_ok=True)
    for t, pk in TABLES.items():
        con.execute(f"COPY (SELECT * FROM {t} ORDER BY {', '.join(pk)}) TO '{out / (t + '.parquet')}' "
                    "(FORMAT PARQUET, COMPRESSION ZSTD)")
    stats["rows"] = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABLES}
    stats["pk_duplicates"] = dict(PK_DUPLICATES, exclusions=load.EXCL_DUPLICATES)
    (config.ROOT / "work" / "tmp" / "pk_collisions.json").write_text(json.dumps(PK_COLLISIONS, indent=0, default=str))
    stats["memo"] = {"hits": M.hits, "misses": M.misses}
    stats["seconds"] = round(time.time() - t0)
    (config.ROOT / "work" / "tmp" / "assemble_stats.json").write_text(json.dumps(stats, indent=1, default=str))
    print(json.dumps(stats["rows"]), stats["seconds"], "s", "; mémo repris :", ", ".join(M.hits) or "rien",
          flush=True)
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
        if len({l["_obs"].get("framework") for l in ls} - {None, NONE}) > 1:
            bad.append("f")          # aucune somme entre cadres comptables (US GAAP et IFRS), bloc foreign
        if any(l["from_group"] is None or l["to_group"] is None for l in ls):
            bad.append("g")
        if bad:
            # motif de la cellule : l'invariant violé, le plus spécifique d'abord ; (a) niveau E ou F :
            # une pièce non admissible dans un agrégat, précondition de la somme non remplie
            reason = {"d": "blocked_overlap", "b": "mixed_currency", "f": "mixed_framework", "g": "pending_entity",
                      "a": "precondition_not_met"}
            c["status"] = "blocked_overlap" if bad == ["d"] else "not_determinable"
            c["nd_reason"] = next(reason[x] for x in ("d", "b", "f", "g", "a") if x in bad)
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
    for g, cal in p0["calendars"].items():
        if not cal.get("history_left_censored"):
            continue
        rc = cal.get("reverse_combination")
        hb = cal.get("history_break")
        if rc:
            ex("group", g, "history_left_censored",
               f"fusion inversée réalisée le {rc['consummation']} : l'historique du groupe est celui de "
               f"l'acquéreur comptable ({rc['accounting_acquirer']}), publié par les rapports postérieurs ; "
               "rien avant (D-0043)", g)
        elif hb:
            what = {"divestiture": "cession d'un périmètre", "framework_change": "changement de référentiel comptable"}
            ex("group", g, "history_left_censored",
               f"rupture d'historique le {hb['effective']} ({what.get(hb.get('kind'), hb.get('kind'))}) : avant, "
               f"{hb.get('before')} ; l'historique du groupe commence aux rapports postérieurs (D-0048)", g)
        else:
            ex("group", g, "history_left_censored",
               "premier dépôt après le début de la période de lecture, aucun prédécesseur (plan.md)", g)
    inv = pd.read_parquet(config.DB_DIR / "inventory.parquet", columns=["group_id", "form", "inv_class"])
    for g, sub in inv[inv["inv_class"] == "pre_combination"].groupby("group_id"):
        rc = p0["calendars"][g].get("reverse_combination") or {}
        hb = p0["calendars"][g].get("history_break") or {}
        n_per = int(sub["form"].isin(PERIODIC_FORMS).sum())
        if hb:
            ex("group", f"{g}:pre_combination", "out_of_scope",
               f"{len(sub)} dépôts de la période de lecture, dont {n_per} rapports périodiques, sont antérieurs à la "
               f"rupture d'historique du {hb.get('effective')} ({hb.get('before')}) : hors des séries et du texte du "
               "groupe (D-0048)", g)
            continue
        ex("group", f"{g}:pre_combination", "out_of_scope",
           f"{len(sub)} dépôts de la période de lecture, dont {n_per} rapports périodiques, présentent le déclarant "
           f"légal ({rc.get('legal_registrant')}) avant la fusion inversée du {rc.get('consummation')} : autre "
           "entité que le groupe, hors des séries et du texte (D-0043)", g)
    for g, sub in inv[inv["inv_class"] == "post_succession"].groupby("group_id"):
        ex("group", f"{g}:post_succession", "out_of_scope",
           f"{len(sub)} rapports périodiques d'un prédécesseur portent sur des périodes closes après sa succession : "
           "rapports d'une filiale du groupe, hors de ses séries et de son texte (D-0055)", g)
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
        # un déposant devenu groupe de config.yaml (D-0043) : ses dépôts se lisent par le catalogue du
        # groupe ; ses unités non préparées sortent de la file de la découverte
        cfg = config.load()
        as_group = {str(int(c)): g for g, c in cfg["groups"].items()}
        superseded = Counter()
        # dictionnaires et non itertuples : la colonne « pass » est un mot réservé que itertuples renomme
        for u in units.to_dict("records"):
            b = built.get(u["order"])
            if b and b.get("content_key"):
                continue
            if str(u["cik"]) in as_group:
                superseded[as_group[str(u["cik"])]] += 1
                continue
            why = (b or {}).get("error") or "unité de la file de la découverte non encore préparée ni lue"
            ex("document", f"discovery:{u['adsh']}/{u['doc']}", "not_processed" if not (b or {}).get("error") else "not_collected",
               f"rang {u['rank']}, passe {u['pass']}, {u['kind']} : {why} ; groupes nommés {u['groups']}",
               "CP:cik" + str(u["cik"]), u["adsh"])
        for g, n in sorted(superseded.items()):
            ex("group", f"{g}:discovery_units", "out_of_scope",
               f"{n} unités de la file de la découverte tirées des dépôts du groupe, ajouté à config.yaml après "
               "la découverte : ces dépôts se lisent par le catalogue du groupe (D-0043)", g)
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
    nf_discovery_exclusions(ex, todo)
    return out


def nf_discovery_exclusions(ex, todo):
    """Piste des non-déposants (D-0044) : une unité non lue reste visible, avec la règle qui l'écarte
    (hors de la règle, au-delà du plafond) ou son état (retenue, non encore lue) ; une archive non
    scannée sous le lexique de la piste laisse l'inventaire incomplet. Les exclusions passent par
    `ex`, qui les ajoute à celles de la découverte."""
    from . import nf_discovery as NF
    if not NF.UNITS.exists():
        return
    read_cks = {p.stem for p in config.OBS_DIR.glob("*.jsonl") if not p.name.endswith(".rejected.jsonl")}
    built = NF.built_units()
    units = pd.read_parquet(NF.UNITS)
    for u in units.to_dict("records"):
        b = built.get((u["adsh"], u["doc"]))
        if b and b.get("content_key") and b["content_key"] in read_cks:
            continue
        reason = "not_processed"
        if u["status"] == "own_group":
            why, reason = (f"dépôt propre d'une entité du groupe non déposant, lu comme texte du groupe "
                           f"({u.get('file')}) : pas une unité de la piste"), "out_of_scope"
        elif u["status"] == "out_of_rule":
            why = ("hors de la règle de lecture (D-0044) : ni co-mention d'un groupe, d'un laboratoire ou de "
                   "Stargate, ni note du dernier dépôt d'un candidat à montant documenté")
        elif u["status"] == "over_cap":
            why = f"retenue ({u['rule']}), au-delà du plafond de lecture ({u.get('file') or 'D-0044'})"
        elif b and b.get("error"):
            why, reason = b["error"], "not_collected"
        else:
            why = f"retenue ({u['rule']}), non encore préparée ni lue"
        ex("document", f"discovery_nf:{u['adsh']}/{u['doc']}", reason,
           f"piste des non-déposants ({u['groups']}), rang {u['rank']}, passe {u['pass']}, {u['kind']} : {why}",
           "CP:cik" + str(u["cik"]), u["adsh"])
    done_nf = set(NF.scanned_archives())
    for a in todo:
        if a["name"] not in done_nf:
            ex("period", f"notes_nf:{a['name']}", "not_processed",
               f"archive des Notes Data Sets non scannée pour la piste des non-déposants ({a['filed_from']} au {a['filed_to']})")


if __name__ == "__main__":
    # les tables ne dépendent pas de l'ordre d'itération des ensembles de chaînes (§9.6) : mêmes tables à l'octet près
    # sous PYTHONHASHSEED=0 et 1 (D-0072, point 3 e), d'où la fin de la relance du script
    args = sys.argv[1:]
    as_of_arg = config.as_of(next((a for a in args if not a.startswith("--")), None))     # D-0073
    if "--apercu" in args:
        from . import apercu
        apercu.main(as_of_arg, use_cache="--sans-cache" not in args)
    else:
        run(as_of_arg, use_cache="--sans-cache" not in args)
