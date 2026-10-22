"""Signaux structurels (§4.5) tirés des formulaires et des items de 8-K. Les événements de l'annexe F
se calculent dans fsignals.py ; l'ancienne règle F1 d'ici, qui n'était plus appelée, a été retirée
(D-0069, point 9).

Chaque signal est une cellule de measures qui porte la période concernée et la date de publicité de
sa pièce. Une source non lue ne passe jamais pour un trimestre sans signal. Aucune somme.
"""
import datetime as dt
import json

import pandas as pd

from .measures import cell

NT_FORMS = {"NT 10-K", "NT 10-Q", "NT 10-K/A", "NT 10-Q/A", "NT 20-F", "NT 20-F/A"}
SIX_K = {"6-K", "6-K/A"}
# trimestre sous le régime des émetteurs privés étrangers : des 6-K, aucun 8-K. Un 6-K n'a pas
# d'items (D-0048, point 6) et n'est lu que par unités plafonnées : l'absence d'un signal tiré
# des items de 8-K n'y est pas établie
REGIME_6K = ("trimestre sous le régime des émetteurs privés étrangers : 6-K sans items, aucun 8-K ; "
             "6-K lus par unités plafonnées (D-0048)")


def regime_6k(sub):
    """Accessions des 6-K du trimestre s'il n'a que des 6-K (aucun 8-K), sinon liste vide."""
    forms = sub["form"].fillna("")
    if forms.isin(["8-K", "8-K/A"]).any():
        return []
    return sorted(set(sub.loc[forms.isin(SIX_K), "accessionNumber"]))
DISTRESS = {"1.03", "2.04", "2.06", "3.01"}
AUDITOR = {"4.01", "4.02"}


def _in(d, ps, pe):
    return d is not None and ps <= d <= pe


def structural_signals(groups, quarters_by_group, filings, as_of, error_flags, observations=()):
    """Signaux lus dans la structure : formulaires NT, items de 8-K, drapeau de correction. Sous le
    régime 6-K, les signaux d'items de 8-K ne sont établis que par une observation lue (D-0048)."""
    out = []
    nonrel = {}
    for o in observations:
        if o.get("signal") == "nonreliance" and o.get("signal_present") is True:
            nonrel.setdefault(o["group_id"], []).append(o)
    for g in groups:
        fg = filings[filings["group_id"] == g]
        for q in quarters_by_group[g]:
            ps, pe = q["start"], q["end"]
            sub = fg[(fg["filingDate"] >= ps) & (fg["filingDate"] <= pe)]
            nt = sub[sub["form"].isin(NT_FORMS)]
            out.append(_sig("sig_late_filing", g, ps, pe, as_of, nt, "formulaires NT déposés dans le trimestre"))
            six = regime_6k(sub)
            if six:
                out += _regime_6k_signals(g, ps, pe, as_of, six, error_flags, nonrel.get(g, []))
                continue
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


def _regime_6k_signals(g, ps, pe, as_of, six, error_flags, nonrel):
    """Items de détresse et changement d'auditeur ou correction d'erreur, trimestre sous régime 6-K :
    événement si le drapeau de correction balisé ou une observation lue l'établit ; sinon non établi."""
    out = [cell("sig_distress_8k_items", g, ps, pe, "as_known", as_of, status="not_determinable",
                nd_reason="not_collected", coverage="not_collected",
                flags={"basis": REGIME_6K, "accessions": six})]
    rows = [{"accessionNumber": a[0], "filingDate": str(_d(a[1])), "form": "flag", "items": "error_correction"}
            for a in error_flags.get(g, []) if _in(_d(a[1]), ps, pe)]
    hits = [o for o in nonrel if _in(_d(o.get("event_date") or o.get("knowledge_date")), ps, pe)]
    rows += [{"accessionNumber": o.get("accession"), "filingDate": str(_d(o.get("knowledge_date"))), "form": "6-K",
              "items": "nonreliance (texte lu)"} for o in hits]
    if rows:
        c = _sig("sig_auditor_change_or_nonreliance", g, ps, pe, as_of, pd.DataFrame(rows),
                 "dei:DocumentFinStmtErrorCorrectionFlag ; signal lu dans un 6-K (D-0048)")
        if hits:
            fl = json.loads(c["flags"])
            fl["observations"] = sorted(o["obs_key"] for o in hits)
            c["flags"] = json.dumps(fl, sort_keys=True, default=str)
        out.append(c)
    else:
        out.append(cell("sig_auditor_change_or_nonreliance", g, ps, pe, "as_known", as_of, status="not_determinable",
                        nd_reason="not_collected", coverage="not_collected",
                        flags={"basis": REGIME_6K, "accessions": six}))
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


def _d(x):
    if x is None or x == "" or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])
