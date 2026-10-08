"""Signaux lus dans le texte (§4.5), flux après financement des contreparties (§4.4),
événements de l'annexe F et lignes de la matrice d'exposition tirées des observations.

Une source non lue ne passe jamais pour un trimestre sans événement : chaque cellule dit
si sa source a été lue (computed), lue en partie (partial, not_processed) ou non (not_determinable).
"""
import datetime as dt
import json
from decimal import Decimal

import pandas as pd

from .measures import cell

NONE = "none"
PERIODIC = {"10-K", "10-K/A", "10-Q", "10-Q/A", "10-KT", "10-KT/A", "10-QT", "10-QT/A"}
COVENANT = {"covenant_amendment", "covenant_waiver", "covenant_breach"}


def _d(x):
    if x in (None, "", NONE) or (isinstance(x, float) and x != x):
        return None
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])


def reports_by_quarter(filings, g, q):
    f = filings[(filings["group_id"] == g) & (filings["form"].isin(PERIODIC))]
    rd = f["reportDate"].map(_d)
    m = f[rd.map(lambda x: x is not None and abs((x - q["end"]).days) <= 3)]
    return m.sort_values("filingDate")


def observed_signals(groups, quarters_by_group, filings, blocks_by_acc, obs_by_ck, read_cks, parsed_accs, as_of):
    out = []
    for g in groups:
        for q in quarters_by_group[g]:
            ps, pe = q["start"], q["end"]
            reps = reports_by_quarter(filings, g, q)
            accs = list(reps["accessionNumber"])
            # faiblesse significative : Item 9A (10-K) ou Item 4 (10-Q)
            bl = [b for a in accs for b in blocks_by_acc.get(a, []) if b["block_kind"] in ("item_9a", "item_4_10q")]
            if not accs:
                out.append(cell("sig_material_weakness", g, ps, pe, "as_known", as_of, status="not_determinable",
                                nd_reason="not_disclosed", flags={"basis": "aucun rapport périodique pour ce trimestre"}))
            elif not bl:
                out.append(cell("sig_material_weakness", g, ps, pe, "as_known", as_of, status="not_determinable",
                                nd_reason="parse_failed", coverage="parse_failed",
                                flags={"basis": "section Item 9A ou Item 4 non délimitée", "accessions": accs}))
            elif not all(b["content_key"] in read_cks for b in bl):
                out.append(cell("sig_material_weakness", g, ps, pe, "as_known", as_of, status="not_determinable",
                                nd_reason="not_processed", coverage="not_processed"))
            else:
                lines = [o for b in bl for o in obs_by_ck.get(b["content_key"], []) if o.get("signal") == "material_weakness"]
                hits = [o for o in lines if o.get("signal_present") is True]
                kd = str(min(reps["filingDate"]))
                out.append(cell("sig_material_weakness", g, ps, pe, "as_known", as_of,
                                value_text="event" if hits else "no_event", status="computed", knowledge_date=kd,
                                flags={"observations": [o["obs_key"] for o in (hits or lines)], "accessions": accs}))
            # continuité d'exploitation : bloc balisé ou passage de la note 1, cherché dans l'instance
            gc = [b for a in accs for b in blocks_by_acc.get(a, []) if b["block_kind"] == "going_concern"]
            if not accs:
                out.append(cell("sig_going_concern", g, ps, pe, "as_known", as_of, status="not_determinable",
                                nd_reason="not_disclosed", flags={"basis": "aucun rapport périodique pour ce trimestre"}))
            elif gc:
                lines = [o for b in gc for o in obs_by_ck.get(b["content_key"], []) if o.get("signal") == "going_concern"]
                hits = [o for o in lines if o.get("signal_present") is True]
                out.append(cell("sig_going_concern", g, ps, pe, "as_known", as_of, value_text="event" if hits else "no_event",
                                status="computed", knowledge_date=str(min(reps["filingDate"])),
                                flags={"observations": [o["obs_key"] for o in lines]}))
            elif any(a in parsed_accs for a in accs):
                out.append(cell("sig_going_concern", g, ps, pe, "as_known", as_of, value_text="no_event", status="computed",
                                knowledge_date=str(min(reps["filingDate"])),
                                flags={"basis": "ni bloc SubstantialDoubtAboutGoingConcernTextBlock ni passage de doute dans la note 1 de l'instance",
                                       "accessions": accs}))
            else:
                out.append(cell("sig_going_concern", g, ps, pe, "as_known", as_of, status="not_determinable",
                                nd_reason="not_collected", coverage="not_collected",
                                flags={"basis": "instance XBRL du rapport non lue", "accessions": accs}))
    return out


def debt_note_quarters(obs, report_end_of):
    """(groupe, fin de trimestre) dont la note de dette du rapport périodique a été lue (bloc
    `text` de §14) : toute ligne, abstention comprise, d'un bloc debt_note."""
    out = set()
    for o in obs:
        if o.get("block_kind") == "debt_note" and o.get("accession") in report_end_of:
            out.add((o["group_id"], report_end_of[o["accession"]]))
    return out


def _read_for(read_q, g, pe):
    return any(gg == g and d is not None and abs((d - pe).days) <= 7 for gg, d in read_q)


def covenant_signals(groups, quarters_by_group, obs, as_of, report_end_of=None):
    """sig_covenant_events : manquements, dérogations et amendements de clauses financières.
    Lus dans les items de 8-K et leurs pièces (tranche complète) et, si le bloc `text` est
    ouvert, dans la note de dette de chaque rapport périodique : un trimestre sans événement
    est computed si cette note est lue, partial sinon."""
    out = []
    read_q = debt_note_quarters(obs, report_end_of or {})
    for g in groups:
        evs = [o for o in obs if o["group_id"] == g and o.get("signal") in COVENANT and o.get("signal_present") is True
               and o["validation_state"] == "valid"]
        for q in quarters_by_group[g]:
            ps, pe = q["start"], q["end"]
            hits = [o for o in evs if (_d(o.get("event_date")) or _d(o.get("knowledge_date"))) is not None
                    and ps <= (_d(o.get("event_date")) or _d(o.get("knowledge_date"))) <= pe]
            if hits:
                out.append(cell("sig_covenant_events", g, ps, pe, "as_known", as_of, value_text="event", status="computed",
                                knowledge_date=str(min(_d(o["knowledge_date"]) for o in hits)),
                                flags={"observations": [o["obs_key"] for o in hits],
                                       "signals": sorted({o["signal"] for o in hits}),
                                       "judgment_sensitive": any(o.get("judgment_sensitive") for o in hits)}))
            elif _read_for(read_q, g, pe):
                out.append(cell("sig_covenant_events", g, ps, pe, "as_known", as_of, value_text="no_event", status="computed",
                                flags={"basis": "items 1.01, 1.02, 3.03 et 8.01 des 8-K et leurs pièces, note de dette du rapport lue"}))
            else:
                out.append(cell("sig_covenant_events", g, ps, pe, "as_known", as_of, value_text="no_event", status="partial",
                                nd_reason="not_processed", coverage="not_processed",
                                flags={"basis": "items 1.01, 1.02, 3.03 et 8.01 des 8-K et leurs pièces lus ; note de dette de ce trimestre non lue"}))
    return out


def pledged_signals(groups, quarters_by_group, obs, as_of, report_end_of):
    """sig_pledged_assets : actifs nantis et trésorerie restreinte au profit de prêteurs (§4.5),
    lus dans les notes de dette et les contrats ; un trimestre dont la note de dette n'est pas lue
    reste indéterminé, jamais « sans nantissement »."""
    out = []
    read_q = debt_note_quarters(obs, report_end_of)
    for g in groups:
        # une sûreté conditionnelle dont le déclencheur n'a pas joué (dépôt de garantie en espèces
        # exigé seulement en cas de défaut d'un prêteur, par exemple) n'est pas un actif nanti
        evs = [o for o in obs if o["group_id"] == g and o.get("signal") == "pledged_assets"
               and o.get("signal_present") is True and o["validation_state"] == "valid"
               and not (o.get("conditionality") == "conditional" and o.get("trigger_occurred") != "yes")]
        for q in quarters_by_group[g]:
            ps, pe = q["start"], q["end"]
            hits = []
            for o in evs:
                d = _d(o.get("event_date")) or _d(o.get("period_end")) or \
                    report_end_of.get(o.get("accession")) or _d(o.get("knowledge_date"))
                if d is not None and ps <= d <= pe + dt.timedelta(days=7):
                    hits.append(o)
            if hits:
                out.append(cell("sig_pledged_assets", g, ps, pe, "as_known", as_of, value_text="event", status="computed",
                                knowledge_date=str(min(_d(o["knowledge_date"]) for o in hits)),
                                flags={"observations": [o["obs_key"] for o in hits]}))
            elif _read_for(read_q, g, pe):
                out.append(cell("sig_pledged_assets", g, ps, pe, "as_known", as_of, value_text="no_event", status="computed",
                                flags={"basis": "note de dette du rapport lue, aucun nantissement relevé"}))
            else:
                out.append(cell("sig_pledged_assets", g, ps, pe, "as_known", as_of, status="not_determinable",
                                nd_reason="not_processed", coverage="not_processed"))
    return out


def counterparty_financing(groups, quarters_by_group, edges, measures_df, as_of):
    """fcf_after_counterparty_financing = fcf_basic − financements en numéraire accordés à des
    contreparties nommées + remboursements reçus ; partial au premier passage."""
    out = []
    m = measures_df[(measures_df["measure"] == "fcf_basic")]
    for g in groups:
        given = [l for l in edges if l["from_group"] == g and l["family"] == "financing" and l["edge_evidence"] == "amount"
                 and l["unit"] == "USD" and l["_obs"].get("amount_nature") == "financing_cash"
                 and l["_obs"].get("event_type") not in ("repayment", "conversion") and not l.get("_dup_of")
                 and l["elimination_status"] != "eliminated"]
        back = [l for l in edges if l["to_group"] == g and l["family"] == "financing" and l["edge_evidence"] == "amount"
                and l["unit"] == "USD" and l["_obs"].get("event_type") == "repayment" and not l.get("_dup_of")
                and l["elimination_status"] != "eliminated" and l["from_group"] != g]
        for q in quarters_by_group[g]:
            ps, pe = q["start"], q["end"]
            for view in ("revised", "as_known"):
                r = m[(m["subject"] == g) & (m["period_end"] == str(pe)) & (m["view"] == view)]
                if r.empty or r.iloc[0]["status"] != "computed":
                    out.append(cell("fcf_after_counterparty_financing", g, ps, pe, view, as_of, status="not_determinable",
                                    nd_reason=(r.iloc[0]["nd_reason"] if not r.empty and r.iloc[0]["nd_reason"] else "term_missing")))
                    continue
                fcf = Decimal(str(r.iloc[0]["value"]))
                gq = [l for l in given if l["_date"] and ps <= l["_date"] <= pe]
                bq = [l for l in back if l["_date"] and ps <= l["_date"] <= pe]
                v = fcf - sum((Decimal(str(l["amount"])) for l in gq), Decimal(0)) + \
                    sum((Decimal(str(l["amount"])) for l in bq), Decimal(0))
                out.append(cell("fcf_after_counterparty_financing", g, ps, pe, view, as_of, value=v, unit="USD",
                                status="partial", nd_reason="not_processed", coverage="not_processed",
                                flags={"fcf_basic_lineage": r.iloc[0]["lineage"],
                                       "financing_given": [l["link_key"] for l in gq],
                                       "repayments_received": [l["link_key"] for l in bq],
                                       "basis": "financements lus dans la tranche ; notes d'investissements hors tranche"}))
    return out


def exposure_from_observations(obs, as_of):
    """Lignes de la matrice d'exposition tirées du texte : une cellule par ligne, jamais de total."""
    out = []
    for o in obs:
        if o["kind"] != "observation" or o["validation_state"] != "valid":
            continue
        if o.get("exposure_block") in (None, NONE) or o.get("amount") is None:
            continue
        if o.get("tier") not in ("A", "B", "C", "D"):
            continue
        d = _d(o.get("period_end")) or _d(o.get("event_date")) or _d(o.get("knowledge_date"))
        basis = o.get("measurement_basis") or NONE
        key = f"{o['exposure_block']}/{basis}/{o.get('category_id') or 'other'}/obs:{o['obs_key']}"
        out.append(cell("exposure_matrix", o["group_id"], None, d, "as_known", as_of, breakdown=key,
                        value=Decimal(str(o["amount"])), unit=o.get("unit"),
                        terms=[{"value": Decimal(str(o["amount"])), "fact_key": "obs:" + o["obs_key"],
                                "knowledge_date": str(o.get("knowledge_date")), "tier": o.get("tier"),
                                "is_tagged": o.get("amount_origin") == "tagged_reference"}],
                        flags={"counterparty": o.get("counterparty_name"), "ultimate_obligor": o.get("ultimate_obligor"),
                               "seniority": o.get("seniority"), "recourse": o.get("recourse"),
                               "is_ring_fenced": o.get("is_ring_fenced"), "conditionality": o.get("conditionality"),
                               "trigger_description": o.get("trigger_description"),
                               "trigger_occurred": o.get("trigger_occurred"), "amount_qualifier": o.get("amount_qualifier"),
                               "currency": o.get("currency"), "instrument_key": o.get("instrument_key")}))
    return out


def fragility_events(groups, quarters_by_group, measures_df, sig_cells, obs_by_group, filings, read_cks,
                     blocks_by_acc, as_of):
    """Annexe F, F1 à F10 : une cellule par groupe, observable et trimestre, jamais de somme."""
    out = []
    m = measures_df
    sig = {(c["measure"], c["subject"], c["period_end"]): c for c in sig_cells}
    eightk = filings[filings["form"].isin(["8-K", "8-K/A"])]
    for g in groups:
        qs = quarters_by_group[g]
        mg = m[(m["subject"] == g) & (m["view"] == "as_known")]

        def get(measure, pe, term=NONE, breakdown=NONE):
            r = mg[(mg["measure"] == measure) & (mg["period_end"] == str(pe)) & (mg["term"] == term)
                   & (mg["breakdown_key"] == breakdown)]
            return r.iloc[0] if not r.empty else None
        prev = prev_growth = None
        for q in qs:
            ps, pe = q["start"], q["end"]

            def ev(fid, status, value_text=None, nd=None, flags=None, kd=None, coverage="observed"):
                out.append(cell("fragility_event", g, ps, pe, "as_known", as_of, breakdown=fid, status=status,
                                value_text=value_text, nd_reason=nd, flags=flags, knowledge_date=kd,
                                coverage=coverage))
            # F1 : capex décaissé > CFO deux trimestres de suite
            c = get("capex_to_cfo", pe, "without")
            cur = None
            if c is not None and c["status"] == "computed" and c["numerator"] is not None and not pd.isna(c["numerator"]):
                cur = Decimal(str(c["numerator"])) > Decimal(str(c["denominator"]))
            if cur is None:
                ev("F1", "not_determinable", nd=(c["nd_reason"] if c is not None and c["nd_reason"] else "term_missing"))
            elif prev is None:
                ev("F1", "not_determinable", nd="prior_period_missing")
            else:
                ev("F1", "computed", "event" if (cur and prev) else "no_event", kd=c["knowledge_date"],
                   flags={"lineage": c["lineage"]})
            prev = cur
            # F2 : fcf_after_counterparty_financing négatif (calculable seulement si complet)
            f2 = get("fcf_after_counterparty_financing", pe)
            if f2 is not None and f2["status"] == "computed":
                ev("F2", "computed", "event" if Decimal(str(f2["value"])) < 0 else "no_event")
            else:
                ev("F2", "not_determinable", nd="not_processed", coverage="not_processed",
                   flags={"basis": "flux après financement des contreparties partiel : notes d'investissements hors tranche"})
            # F3 : backstop ou garantie dont le déclencheur est survenu
            hits = [o for o in obs_by_group.get(g, []) if o.get("trigger_occurred") == "yes"
                    and o.get("category_id") in ("guarantee", "capacity_backstop", "residual_value_guarantee",
                                                 "credit_enhancement", "backstop")
                    and (_d(o.get("event_date")) or _d(o.get("knowledge_date"))) is not None
                    and ps <= (_d(o.get("event_date")) or _d(o.get("knowledge_date"))) <= pe]
            if hits:
                ev("F3", "computed", "event", flags={"observations": [o["obs_key"] for o in hits]},
                   kd=str(min(_d(o["knowledge_date"]) for o in hits)))
            else:
                ev("F3", "partial", "no_event", nd="not_processed", coverage="not_processed",
                   flags={"basis": "garanties et soutiens lus dans les 8-K de la tranche ; notes d'engagements hors tranche"})
            # F4, F5, F10 : signaux
            for fid, meas in (("F4", "sig_covenant_events"), ("F5", "sig_material_weakness"), ("F10", "sig_going_concern")):
                s = sig.get((meas, g, str(pe)))
                if s is None:
                    ev(fid, "not_determinable", nd="not_processed", coverage="not_processed")
                else:
                    ev(fid, s["status"], s.get("value_text"), nd=s.get("nd_reason"), kd=s.get("knowledge_date"),
                       flags=json.loads(s["flags"]) if s.get("flags") else None,
                       coverage=s.get("coverage_state") or "observed")
            # F6 : dépréciation d'investissement (exercice)
            if q["end"] == q["fy_end"]:
                c6 = get("earnings_bridge_pretax", pe, "investment_impairment")
                if c6 is not None and c6["status"] == "computed":
                    ev("F6", "computed", "event" if Decimal(str(c6["value"])) != 0 else "no_event", kd=c6["knowledge_date"],
                       flags={"lineage": c6["lineage"]})
                else:
                    ev("F6", "not_determinable", nd=(c6["nd_reason"] if c6 is not None and c6["nd_reason"] else "term_missing"))
            else:
                ev("F6", "not_determinable", nd="annual_only")
            # F7 : baisse d'une durée d'amortissement publiée (exercice)
            if q["end"] == q["fy_end"]:
                c7 = mg[(mg["measure"] == "depreciation_life_published") & (mg["period_end"] == str(pe))]
                if c7.empty:
                    ev("F7", "not_determinable", nd="concept_unresolved")
                else:
                    flags = [json.loads(x) for x in c7["flags"].dropna()]
                    down = [f["decrease"] for f in flags if f.get("decrease")]
                    ev("F7", "computed", "event" if down else "no_event", flags={"decreases": down} if down else None,
                       kd=str(c7["knowledge_date"].dropna().max()) if c7["knowledge_date"].notna().any() else None)
            else:
                ev("F7", "not_determinable", nd="annual_only")
            # F8 : croissance en glissement annuel qui passe sous zéro
            gr = get("revenue_growth", pe, "yoy")
            val = Decimal(str(gr["value"])) if gr is not None and gr["status"] == "computed" else None
            if val is None:
                ev("F8", "not_determinable", nd=(gr["nd_reason"] if gr is not None and gr["nd_reason"] else "term_missing"))
            elif prev_growth is None:
                ev("F8", "not_determinable", nd="prior_period_missing")
            else:
                ev("F8", "computed", "event" if (val < 0 and prev_growth >= 0) else "no_event", kd=gr["knowledge_date"])
            prev_growth = val
            # F9 : item 1.02 sur un contrat de capacité ; la structure dit s'il y a eu un 1.02
            k = eightk[(eightk["group_id"] == g) & eightk["filingDate"].map(lambda x: ps <= _d(x) <= pe)
                       & eightk["items"].fillna("").map(lambda s: "1.02" in [x.strip() for x in s.split(",")])]
            if k.empty:
                ev("F9", "computed", "no_event", flags={"basis": "aucun 8-K item 1.02 dans le trimestre (submissions, toutes pages)"})
            else:
                accs = list(k["accessionNumber"])
                bl = [b for a in accs for b in blocks_by_acc.get(a, []) if b["block_kind"] == "item_8k_102"]
                if not bl or not all(b["content_key"] in read_cks for b in bl):
                    ev("F9", "not_determinable", nd="not_processed", coverage="not_processed", flags={"accessions": accs})
                else:
                    o9 = [o for o in obs_by_group.get(g, []) if o["content_key"] in {b["content_key"] for b in bl}]
                    hit = [o for o in o9 if o.get("signal") == "capacity_contract_termination" and o.get("signal_present")]
                    ev("F9", "computed", "event" if hit else "no_event", kd=str(min(k["filingDate"])),
                       flags={"accessions": accs, "observations": [o["obs_key"] for o in (hit or o9)]})
    return out
