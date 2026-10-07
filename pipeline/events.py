"""Signaux (§4.5) et événements de fragilité (annexe F).

Chaque événement est une cellule de measures (fragility_event, l'identifiant dans
breakdown_key) qui porte la période concernée et la date de publicité de sa pièce.
Une source non lue ne passe jamais pour un trimestre sans événement. Aucune somme.
"""
import datetime as dt
import json
from decimal import Decimal

import pandas as pd

from . import config
from .measures import cell

NT_FORMS = {"NT 10-K", "NT 10-Q", "NT 10-K/A", "NT 10-Q/A"}
DISTRESS = {"1.03", "2.04", "2.06", "3.01"}
AUDITOR = {"4.01", "4.02"}


def _in(d, ps, pe):
    return d is not None and ps <= d <= pe


def structural_signals(groups, quarters_by_group, filings, as_of, error_flags):
    """Signaux lus dans la structure : formulaires NT, items de 8-K, drapeau de correction."""
    out = []
    for g in groups:
        fg = filings[filings["group_id"] == g]
        for q in quarters_by_group[g]:
            ps, pe = q["start"], q["end"]
            sub = fg[(fg["filingDate"] >= ps) & (fg["filingDate"] <= pe)]
            nt = sub[sub["form"].isin(NT_FORMS)]
            out.append(_sig("sig_late_filing", g, ps, pe, as_of, nt, "formulaires NT déposés dans le trimestre"))
            ek = sub[sub["form"].isin(["8-K", "8-K/A"])]
            dist = ek[ek["items"].fillna("").map(lambda s: bool({x.strip() for x in s.split(",")} & DISTRESS))]
            out.append(_sig("sig_distress_8k_items", g, ps, pe, as_of, dist, "8-K items 1.03, 2.04, 2.06, 3.01"))
            aud = ek[ek["items"].fillna("").map(lambda s: bool({x.strip() for x in s.split(",")} & AUDITOR))]
            corr = [a for a in error_flags.get(g, []) if _in(a[1], ps, pe)]
            extra = pd.DataFrame([{"accessionNumber": a[0], "filingDate": a[1], "form": "flag", "items": "error_correction"}
                                  for a in corr])
            aud = pd.concat([aud, extra]) if not extra.empty else aud
            out.append(_sig("sig_auditor_change_or_nonreliance", g, ps, pe, as_of, aud,
                            "8-K items 4.01, 4.02 ; dei:DocumentFinStmtErrorCorrectionFlag"))
    return out


def _sig(measure, g, ps, pe, as_of, rows, basis):
    if rows is None or rows.empty:
        return cell(measure, g, ps, pe, "as_known", as_of, value_text="no_event", status="computed",
                    flags={"basis": basis, "source": "submissions, toutes pages"})
    accs = sorted(set(rows["accessionNumber"]))
    kd = str(max(rows["filingDate"]))
    return cell(measure, g, ps, pe, "as_known", as_of, value_text="event", status="computed",
                knowledge_date=kd, flags={"basis": basis, "accessions": accs,
                                          "items": sorted(set(rows["items"].fillna("")))})


def observed_signal(measure, signal, g, q, as_of, obs_q, read_state):
    """Signal lu dans le texte : présent si une observation valide l'établit ; absent si la
    source du trimestre a été lue sans l'établir ; sinon not_processed."""
    ps, pe = q["start"], q["end"]
    hits = [o for o in obs_q if o.get("signal") == signal and o.get("signal_present") is True]
    if hits:
        return cell(measure, g, ps, pe, "as_known", as_of, value_text="event", status="computed",
                    knowledge_date=str(max(o["knowledge_date"] for o in hits)),
                    flags={"observations": [o["obs_key"] for o in hits]})
    if read_state == "read":
        return cell(measure, g, ps, pe, "as_known", as_of, value_text="no_event", status="computed",
                    flags={"observations": [o["obs_key"] for o in obs_q if o.get("signal") == signal]})
    if read_state == "scanned":
        return cell(measure, g, ps, pe, "as_known", as_of, value_text="no_event", status="computed",
                    flags={"basis": "aucun bloc ni passage de doute dans les blocs de texte de l'instance"})
    return cell(measure, g, ps, pe, "as_known", as_of, status="not_determinable", nd_reason=read_state,
                coverage="not_processed" if read_state == "not_processed" else "unknown")


def fragility_events(groups, quarters_by_group, measures_df, sig_cells, obs_by_group, as_of):
    """Annexe F, F1 à F10, une cellule par groupe, observable et trimestre."""
    out = []
    m = measures_df
    sig = {(c["measure"], c["subject"], c["period_end"]): c for c in sig_cells}
    for g in groups:
        qs = quarters_by_group[g]
        mg = m[(m["subject"] == g) & (m["view"] == "as_known")]

        def get(measure, pe, term="none", breakdown="none"):
            r = mg[(mg["measure"] == measure) & (mg["period_end"] == str(pe)) & (mg["term"] == term)
                   & (mg["breakdown_key"] == breakdown)]
            return r.iloc[0] if not r.empty else None
        prev = None
        prev_growth = None
        for q in qs:
            ps, pe = q["start"], q["end"]

            def ev(fid, status, value_text=None, nd=None, flags=None, kd=None, coverage="observed"):
                out.append(cell("fragility_event", g, ps, pe, "as_known", as_of, breakdown=fid, status=status,
                                value_text=value_text, nd_reason=nd, flags=flags, knowledge_date=kd,
                                coverage=coverage))
            # F1 : capex décaissé > CFO deux trimestres de suite
            c = get("capex_to_cfo", pe, "without")
            cur = None
            if c is not None and c["numerator"] is not None and c["denominator"] is not None and not pd.isna(c["numerator"]):
                cur = Decimal(str(c["numerator"])) > Decimal(str(c["denominator"]))
            if cur is None:
                ev("F1", "not_determinable", nd=(c["nd_reason"] if c is not None else "term_missing") or "term_missing")
            elif prev is None:
                ev("F1", "not_determinable", nd="prior_period_missing")
            else:
                ev("F1", "computed", "event" if (cur and prev) else "no_event", kd=c["knowledge_date"],
                   flags={"lineage": c["lineage"]})
            prev = cur
            # F2 : fcf_after_counterparty_financing négatif
            f2 = get("fcf_after_counterparty_financing", pe)
            if f2 is not None and f2["status"] == "computed":
                ev("F2", "computed", "event" if Decimal(str(f2["value"])) < 0 else "no_event")
            else:
                ev("F2", "not_determinable", nd="not_processed", coverage="not_processed")
            # F3 : backstop ou garantie dont trigger_occurred = yes
            hits = [o for o in obs_by_group.get(g, []) if o.get("trigger_occurred") == "yes"
                    and _in(_d(o.get("event_date") or o.get("period_end")), ps, pe)]
            if hits:
                ev("F3", "computed", "event", flags={"observations": [o["obs_key"] for o in hits]})
            else:
                ev("F3", "not_determinable", nd="not_processed", coverage="not_processed")
            # F4, F5, F10 : signaux
            for fid, meas in (("F4", "sig_covenant_events"), ("F5", "sig_material_weakness"), ("F10", "sig_going_concern")):
                s = sig.get((meas, g, str(pe)))
                if s is None:
                    ev(fid, "not_determinable", nd="not_processed", coverage="not_processed")
                elif s["status"] == "computed":
                    ev(fid, "computed", s["value_text"], kd=s.get("knowledge_date"), flags=json.loads(s["flags"]) if s.get("flags") else None)
                else:
                    ev(fid, "not_determinable", nd=s.get("nd_reason") or "not_processed", coverage=s.get("coverage_state") or "not_processed")
            # F6 : dépréciation d'investissement (exercice : dernier trimestre)
            if q["end"] == q["fy_end"]:
                c6 = get("earnings_bridge_pretax", pe, "investment_impairment")
                if c6 is not None and c6["status"] == "computed":
                    ev("F6", "computed", "event" if Decimal(str(c6["value"])) != 0 else "no_event", kd=c6["knowledge_date"])
                else:
                    ev("F6", "not_determinable", nd=(c6["nd_reason"] if c6 is not None else "term_missing") or "term_missing")
            else:
                ev("F6", "not_determinable", nd="annual_only")
            # F7 : baisse d'une durée d'amortissement publiée (exercice)
            if q["end"] == q["fy_end"]:
                c7 = mg[(mg["measure"] == "depreciation_life_published") & (mg["period_end"] == str(pe))]
                if c7.empty:
                    ev("F7", "not_determinable", nd="concept_unresolved")
                else:
                    flags = [json.loads(x) for x in c7["flags"].dropna()]
                    down = [f for f in flags if f.get("decrease")]
                    ev("F7", "computed", "event" if down else "no_event", flags={"decreases": down} if down else None)
            else:
                ev("F7", "not_determinable", nd="annual_only")
            # F8 : croissance en glissement annuel qui passe sous zéro
            gr = get("revenue_growth", pe, "yoy")
            val = Decimal(str(gr["value"])) if gr is not None and gr["status"] == "computed" else None
            if val is None:
                ev("F8", "not_determinable", nd=(gr["nd_reason"] if gr is not None else "term_missing") or "term_missing")
            elif prev_growth is None:
                ev("F8", "not_determinable", nd="prior_period_missing")
            else:
                ev("F8", "computed", "event" if (val < 0 and prev_growth >= 0) else "no_event", kd=gr["knowledge_date"])
            prev_growth = val
            # F9 : item 1.02 sur un contrat de capacité
            o9 = [o for o in obs_by_group.get(g, []) if o.get("block_kind") == "item_8k_102"
                  and _in(_d(o.get("knowledge_date")), ps, pe)]
            if any(o.get("signal") == "capacity_contract_termination" and o.get("signal_present") for o in o9):
                ev("F9", "computed", "event", flags={"observations": [o["obs_key"] for o in o9]})
            else:
                ev("F9", "computed", "no_event", flags={"basis": "sections 1.02 de la tranche lues"} if o9 else
                   {"basis": "aucun 8-K item 1.02 dans le trimestre"})
    return out


def _d(x):
    if x is None or x == "" or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])
