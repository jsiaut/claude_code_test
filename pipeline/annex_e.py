"""Confrontation des mesures à l'annexe E (critères commités avant la première requête).

Chaque issue est une cellule annex_e_outcome ; breakdown_key = « énoncé|point de grille|
date_basis ». Vue principale as_known : chaque exercice s'évalue aux dépôts connus à la date
limite de dépôt de son rapport annuel, plafonnée à l'as_of ; l'as_of de la cellule porte
cette date. Une mesure not_determinable conduit toujours à indeterminate, avec son motif.
"""
import datetime as dt
from collections import Counter
from decimal import Decimal

from .measures import cell

NONE = "none"


def _d(x):
    if x in (None, "", NONE):
        return None
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def bk(stmt, grid=NONE, basis=NONE):
    return f"{stmt}|{grid}|{basis}"


def _ok(c):
    return c is not None and c["status"] in ("computed", "bounded")


def _lo(c):
    return Decimal(str(c["value_lower"] if c.get("value_lower") is not None else c["value"]))


def _hi(c):
    return Decimal(str(c["value_upper"] if c.get("value_upper") is not None else c["value"]))


def _excl(c):
    import json
    f = json.loads(c["flags"]) if c.get("flags") else {}
    return bool(f.get("upper_exclusive"))


def grid_outcome(cells_by_year, s, crit):
    """E.2 et E.3 au point s : supported, refuted ou indeterminate (avec motif)."""
    years = sorted(cells_by_year)
    ev = [(y, c) for y, c in ((y, cells_by_year[y]) for y in years) if _ok(c)]
    sup_run = 0
    best = 0
    for y in years:
        c = cells_by_year[y]
        if _ok(c) and _lo(c) >= s:
            sup_run += 1
            best = max(best, sup_run)
        else:
            sup_run = 0
    if best >= crit["supported"]["min_consecutive_fiscal_years"]:
        return "supported", None
    half = s / 2
    if len(ev) >= crit["refuted"]["min_evaluable_fiscal_years"] and all(
            _hi(c) < half or (_hi(c) == half and _excl(c)) for _, c in ev):
        return "refuted", None
    if not ev:
        reasons = Counter(cells_by_year[y].get("nd_reason") or "not_processed" for y in years)
        return "indeterminate", (reasons.most_common(1)[0][0] if reasons else "not_processed")
    if len(ev) < crit["refuted"]["min_evaluable_fiscal_years"]:
        return "indeterminate", "precondition_not_met"
    return "indeterminate", "interval_straddles_threshold"


def evaluate(ev, cfg, groups_window, deadlines, as_of, paths=None):
    E = cfg["annex_e"]
    grid = [Decimal(str(x)) for x in E["conventions"]["grid"]["high"]]
    head = Decimal(str(E["conventions"]["grid"]["headline"]))
    as_of_d = dt.date.fromisoformat(as_of)
    out = []
    tally = {"E1": [], "E2": []}
    reasons = Counter()
    for (s, c), e in sorted(ev.items()):
        ws = groups_window[s]["window_start"]
        ext = groups_window[s]["extended_start"]
        F = e["F"]["as_known"]["exposure_outstanding"]
        active_ext = [q for q, v in F.items() if v[0] == "active" and q >= ext]
        # E.1 lien documenté, sur les paires où F est active au moins un trimestre
        if active_ext:
            if e["pieces"]:
                o, why = "supported", None
            elif e.get("search_complete"):
                o, why = "not_supported", None      # recherche complète au sens de E.0, aucune pièce L1 à L5
            else:
                o, why = "indeterminate", e.get("search_reason") or "search_incomplete"
            known, full = e["contract"]
            out.append(cell("annex_e_outcome", s, ext, as_of_d, "as_known", as_of, counterparty=c,
                            breakdown=bk("E1"), value_text=o, status="computed" if why is None else "not_determinable",
                            nd_reason=why, flags={"link_pieces": sorted(x["obs_key"] for x in e["pieces"]),
                                                  "active_quarters": [str(q) for q in sorted(active_ext)],
                                                  "contract_coverage": f"{len(full)}/{len(known)}"}))
            tally["E1"].append(o)
            if why:
                reasons[why] += 1
        # E.2 dépendance de revenu, E.3 dépendance du carnet : par exercice, grille
        years = e["years"]
        if active_ext and years:
            dep = {y: cs.get("documented_revenue_dependency") for y, cs in years.items()
                   if cs.get("documented_revenue_dependency")}
            back = {y: cs.get("documented_backlog_dependency") for y, cs in years.items()
                    if cs.get("documented_backlog_dependency")}
            last = max(years)
            cell_as_of = min(deadlines[s](last), as_of_d).isoformat()
            for stmt, cells_by_year in (("E2", dep), ("E3", back)):
                if not cells_by_year:
                    continue
                for sp in grid:
                    o, why = grid_outcome(cells_by_year, sp, E["statements"]["E2"])
                    out.append(cell("annex_e_outcome", s, ws, last, "as_known", cell_as_of, counterparty=c,
                                    breakdown=bk(stmt, f"{sp:.2f}"), value_text=o,
                                    status="computed" if why is None else "not_determinable", nd_reason=why,
                                    flags={"headline": sp == head,
                                           "years": {str(y): {"status": x["status"], "lower": x.get("value_lower"),
                                                              "upper": x.get("value_upper"),
                                                              "nd_reason": x.get("nd_reason")}
                                                     for y, x in sorted(cells_by_year.items())}}))
                    if stmt == "E2" and sp == head:
                        tally["E2"].append(o)
                        if why:
                            reasons[why] += 1
        # E.4 chronologie (descriptif), deux bases de dates
        p = e["pair"]
        fin_commit = [l for l in p.fin if l["_obs"].get("event_type") in ("commitment", "signing")]
        fin_pay = [l for l in p.fin if l["_obs"].get("event_type") in ("funding", "drawdown", "payment")
                   or l["stage"] == "drawn_or_paid"]
        pur_commit = [l for l in p.com if l["edge_type"] == "purchase_commitment"]
        pur_pay = [l for l in p.com if l["edge_type"] in ("purchase", "prepayment") and l["stage"] in
                   ("drawn_or_paid", "settled", "delivered", "recognized")]
        if p.fin and pur_commit:
            for basis, fins, purs in (("commitment", fin_commit, pur_commit), ("payment", fin_pay, pur_pay)):
                tf = [_d(l["_obs"].get("event_date")) for l in fins]
                tp = [_d(l["_obs"].get("event_date")) or _d(l["_obs"].get("period_end")) for l in purs]
                if not fins or not purs or any(x is None for x in tf) or any(x is None for x in tp):
                    o, why = "indeterminate", "date_missing"
                else:
                    hit = any(t - dt.timedelta(days=90) <= u <= t + dt.timedelta(days=365) for t in tf for u in tp)
                    o, why = ("compatible" if hit else "incompatible"), None
                out.append(cell("annex_e_outcome", s, ws, as_of_d, "as_known", as_of, counterparty=c,
                                breakdown=bk("E4", NONE, basis), value_text=o,
                                status="computed" if why is None else "not_determinable", nd_reason=why,
                                flags={"descriptive": True, "presented_as_proof": False,
                                       "financing_links": [l["link_key"] for l in fins],
                                       "purchase_links": [l["link_key"] for l in purs]}))
        # E.5 contrepartie au client (unilatéral) : publiée et comptabilisée en réduction du revenu
        l3 = [o for o in e["pieces"] if o.get("link_category") == "L3" and o["group_id"] == s]
        rec = [cs.get("consideration_to_customer") for cs in years.values()
               if cs.get("consideration_to_customer") and cs["consideration_to_customer"]["status"] == "computed"]
        if p.com or p.fin:
            o = "supported" if (l3 or rec) else "indeterminate"
            out.append(cell("annex_e_outcome", s, ws, as_of_d, "as_known", as_of, counterparty=c,
                            breakdown=bk("E5"), value_text=o,
                            status="computed" if o == "supported" else "not_determinable",
                            nd_reason=None if o == "supported" else
                                      ("not_disclosed" if e.get("s_text_done") else "not_processed"),
                            flags={"l3_pieces": [x["obs_key"] for x in l3], "unilateral": True}))
    # E.6 cycles (descriptif) : décompte des documented_path par valeur de temporal et par conclusion
    def tally6(ps):
        cnt = {}
        for p_ in ps:
            cnt.setdefault(p_["temporal"], Counter())[p_["conclusion"]] += 1
        return {k: dict(v) for k, v in sorted(cnt.items())}
    for s in sorted({k[0] for k in ev}):
        if paths is None:
            out.append(cell("annex_e_outcome", s, groups_window[s]["window_start"], as_of_d, "as_known", as_of,
                            breakdown=bk("E6"), value_text="descriptive", status="not_determinable",
                            nd_reason="not_processed", flags={"basis": "documented_path relève du bloc paths de §14, non ouvert"}))
            continue
        mine = [p_ for p_ in paths if s in p_["nodes"]]
        out.append(cell("annex_e_outcome", s, groups_window[s]["window_start"], as_of_d, "as_known", as_of,
                        breakdown=bk("E6"), value_text="descriptive", status="computed", value=len(mine),
                        flags={"counts": tally6(mine), "paths": [p_["key"] for p_ in mine],
                               "basis": "cycles orientés de longueur 2 ou 3 qui passent par le groupe (bloc paths, §14)"}))
    if paths is not None:
        out.append(cell("annex_e_outcome", "ALL", None, as_of_d, "as_known", as_of, breakdown=bk("E6"),
                        value_text="descriptive", status="computed", value=len(paths),
                        flags={"counts": tally6(paths), "by_length": dict(Counter(len(p_["nodes"]) for p_ in paths)),
                               "basis": "chaque cycle compté une fois (bloc paths, §14) ; issue descriptive, hors de E.7"}))
    # E.7 non-discrimination, E.8 agrégation, E.9 engagements de rendu
    allo = tally["E1"] + tally["E2"]
    n = len(allo)
    ind = sum(1 for x in allo if x == "indeterminate")
    share = Decimal(ind) / Decimal(n) if n else None
    thr = Decimal(str(E["rules"]["E7"]["indeterminate_share_greater_than"]))
    if share is None:
        out.append(cell("annex_e_outcome", "ALL", None, as_of_d, "as_known", as_of, breakdown=bk("E7", f"{head:.2f}"),
                        value_text="indeterminate", status="not_determinable", nd_reason="no_financed_pair",
                        flags={"basis": "aucune paire à financement établi : E.1 et E.2 sans issue"}))
    else:
        txt = "non_discrimination" if share > thr else "discrimination_possible"
        out.append(cell("annex_e_outcome", "ALL", None, as_of_d, "as_known", as_of, breakdown=bk("E7", f"{head:.2f}"),
                        value=share, numerator=ind, denominator=n, value_text=txt, unit="pure",
                        flags={"headline_result": E["rules"]["E7"]["headline_result"] if share > thr else None,
                               "reasons": dict(reasons), "outcomes_E1": dict(Counter(tally["E1"])),
                               "outcomes_E2": dict(Counter(tally["E2"]))}))
    shares = {}
    for stmt in ("E1", "E2", "E3", "E4", "E5"):
        cs = [c for c in out if c["measure"] == "annex_e_outcome" and c["breakdown_key"].startswith(stmt + "|")
              and (stmt not in ("E2", "E3") or c["breakdown_key"].split("|")[1] == f"{head:.2f}")]
        cnt = Counter(c["value_text"] for c in cs)
        shares[stmt] = {k: {"pairs": v, "share": round(v / len(cs), 4)} for k, v in cnt.items()} if cs else {}
    out.append(cell("annex_e_outcome", "ALL", None, as_of_d, "as_known", as_of, breakdown=bk("E8"),
                    value_text="per_pair", status="computed",
                    flags={"rule": E["rules"]["E8"]["rule"], "shares_by_statement": shares}))
    out.append(cell("annex_e_outcome", "ALL", None, as_of_d, "as_known", as_of, breakdown=bk("E9"),
                    value_text="applied", status="computed",
                    flags={"empty_numerator_published_with": E["rules"]["E9"]["empty_numerator"]["publish_alongside"]}))
    return out
