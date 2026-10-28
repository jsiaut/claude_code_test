"""Contrôles C8, C11 et C12 (§8.3), sur les faits de l'instance de chaque dépôt.

C8 publie le résidu entre la variation de la dette et les émissions moins les
remboursements : un résidu n'est pas une erreur, ce sont les éléments non monétaires
(amortissement des décotes, change, acquisitions, conversions) et les flux nets non
balisés (billets de trésorerie), publiés comme tels, jamais équilibrés.
C11 et C12 rapprochent les secteurs et la ventilation du revenu du revenu consolidé.
Les membres d'un axe se lisent dans la linkbase de présentation du dépôt, rôle par rôle :
seuls les membres de premier niveau d'un tableau se somment (un membre imbriqué est une
composante de son parent, et deux tableaux sur un même axe sont deux ventilations). Un même tableau
peut aussi en porter plusieurs : une somme qui dépasse le total se relit par ses ventilations (D-0080).
"""
import datetime as dt
import itertools
import json
from collections import defaultdict
from decimal import Decimal

import pandas as pd

from .controls import ctrl

SEG_AXIS = "us-gaap:StatementBusinessSegmentsAxis"
CONS_AXIS = "srt:ConsolidationItemsAxis"
OPERATING = "us-gaap:OperatingSegmentsMember"
RECON = {"us-gaap:IntersegmentEliminationMember", "us-gaap:CorporateNonSegmentMember",
         "us-gaap:MaterialReconcilingItemsMember", "us-gaap:SegmentReconcilingItemsMember"}
# axes de ventilation du revenu (ASC 606-10-50-5) ; les clients majeurs n'en sont pas une
DISAGG_AXES = ("srt:ProductOrServiceAxis", "srt:StatementGeographicalAxis",
               "us-gaap:TimingOfTransferOfGoodOrServiceAxis", "us-gaap:ContractWithCustomerSalesChannelAxis")
HALF = Decimal("0.5")
MAX_MEMBERS = 12      # au-delà, 4 083 sous-ensembles : la recherche des ventilations ne se fait pas (D-0080)


def _tol(d, inf):
    if inf is True:
        return Decimal(0)
    if d is None or d != d:
        return None
    return HALF * Decimal(10) ** (-int(d))


def _sum_tol(rows):
    tols = [_tol(x.decimals, x.decimals_inf) for x in rows]
    if any(t is None for t in tols):
        return sum(t or Decimal(0) for t in tols), "inferred"
    return sum(tols), "declared"


def _why(s, total, missing, below=None):
    """Code d'explication factuel d'un écart de somme : la présentation d'un tableau à plat ne
    dit pas quels membres sont des sous-totaux ou des sous-ensembles d'autres membres (un
    pays et sa région, une famille et ses lignes), si bien qu'une somme qui dépasse le total
    se publie comme telle, sans choisir les membres qui la feraient passer."""
    if s > total:
        return "sum_exceeds_total"
    if missing:
        return "members_missing"
    return below or "sum_below_total"


def ventilations(members, total):
    """Sous-ensembles d'au moins deux membres d'un tableau qui somment au total, à la tolérance d'arrondi près :
    un même tableau peut porter plusieurs ventilations du revenu (D-0080). `members` et `total` sont des lignes de
    faits (value, decimals, decimals_inf) ; renvoie des tuples d'indices, du plus petit au plus grand."""
    if len(members) > MAX_MEMBERS:
        return []
    vals = [(Decimal(str(x.value)), _tol(x.decimals, x.decimals_inf) or Decimal(0)) for x in members]
    tv, tt = Decimal(str(total.value)), _tol(total.decimals, total.decimals_inf) or Decimal(0)
    return [s for n in range(2, len(vals) + 1) for s in itertools.combinations(range(len(vals)), n)
            if abs(sum(vals[i][0] for i in s) - tv) <= sum(vals[i][1] for i in s) + tt]


def _facts(con, quantity):
    df = con.execute(f"""
        SELECT f.fact_key, f.group_id, f.accession, f.form, f.concept, f.period_type, f.period_start, f.period_end,
               f.dims, f.n_dims, f.value, f.decimals, f.decimals_inf, f.knowledge_date
        FROM facts f JOIN concept_map m ON m.accession = f.accession AND m.concept = f.concept AND m.group_id = f.group_id
        WHERE m.quantity = '{quantity}' AND f.source = 'instance' AND f.value IS NOT NULL
          AND NOT coalesce(f.conflict, false) AND f.unit = 'USD'
        ORDER BY f.accession, f.fact_key""").fetchdf()
    for c in ("period_start", "period_end"):
        df[c] = [None if pd.isna(x) else x for x in pd.to_datetime(df[c]).dt.date]
    return df


def role_children(pres_acc):
    """Enfants de chaque parent, rôle par rôle, dans l'ordre de présentation d'un dépôt."""
    out = []
    for role, pr in pres_acc.groupby("role"):
        kids = defaultdict(list)
        for r in pr.sort_values("ord", kind="stable").itertuples():
            kids[r.parent].append(r.child)
        out.append((role, kids))
    return out


def axis_tables(pres_acc, axis, children=None):
    """Ventilations publiées sur un axe : (rôle, membres de premier niveau) par tableau. `children`
    (role_children du même dépôt) évite de retrier la présentation pour chaque axe."""
    out = []
    if pres_acc is None:
        return out
    for role, kids in (children if children is not None else role_children(pres_acc)):
        if axis not in kids:
            continue
        top = []
        skip = ("Axis", "Table", "LineItems", "Abstract")
        for c in kids[axis]:
            # le domaine porte le premier niveau ; un membre accroché à l'axe en fait partie
            if c.endswith("Domain") or (len(kids[axis]) == 1 and kids.get(c)):
                top += [m for m in kids.get(c, []) if not m.endswith(skip)]
            elif not c.endswith(skip):
                top.append(c)
        top = tuple(dict.fromkeys(top))
        if len(top) >= 2 and all(t != top for _, t in out):
            out.append((role, top))
    return out


def segments_and_disaggregation(con, as_of):
    out = []
    df = _facts(con, "revenue_total")
    con.register("c11_accs", df[["accession"]].drop_duplicates())
    pres = con.execute("""SELECT accession, role, parent, child, ord FROM pres
                           WHERE accession IN (SELECT accession FROM c11_accs)
                           ORDER BY accession, role, parent, ord, child""").fetchdf()
    con.unregister("c11_accs")
    pres_by = dict(tuple(pres.groupby("accession")))
    for acc, fa in df.groupby("accession"):
        g = fa["group_id"].iloc[0]
        totals = {(r.concept, r.period_start, r.period_end): r for r in fa[fa["n_dims"] == 0].itertuples()}
        by_axis = defaultdict(lambda: defaultdict(dict))   # axe -> clé -> membre -> fait
        seg = defaultdict(dict)
        rec = defaultdict(list)
        for r in fa[fa["n_dims"] > 0].itertuples():
            d = {a: m for a, m in json.loads(r.dims)}
            key = (r.concept, r.period_start, r.period_end)
            if SEG_AXIS in d and set(d) <= {SEG_AXIS, CONS_AXIS} and d.get(CONS_AXIS, OPERATING) == OPERATING:
                seg[key][d[SEG_AXIS]] = r
            elif set(d) == {CONS_AXIS} and d[CONS_AXIS] in RECON:
                rec[key].append(r)
            elif len(d) == 1:
                a = next(iter(d))
                by_axis[a][key][d[a]] = r
        pa = pres_by.get(acc)
        children = role_children(pa) if pa is not None else None
        seg_tables = axis_tables(pa, SEG_AXIS, children)
        for key, members in seg.items():
            t = totals.get(key)
            if t is None:
                continue
            # un tableau sectoriel dont les membres couvrent ceux qui sont publiés à cette date
            tables = [(role, top) for role, top in seg_tables if set(members) & set(top)]
            role, top = max(tables, key=lambda x: len(set(members) & set(x[1]))) if tables else (None, tuple(members))
            rs = [members[m] for m in top if m in members]
            parts = rs + rec.get(key, [])
            s = sum(Decimal(str(x.value)) for x in parts)
            tol, basis = _sum_tol(parts + [t])
            okay = abs(s - Decimal(str(t.value))) <= tol
            missing = [m for m in top if m not in members]
            out.append(ctrl("c11_segments", g, key[1], key[2], "as_known", as_of, "ok" if okay else "mismatch", acc,
                            breakdown=key[0], lhs=s, rhs=Decimal(str(t.value)), tol=tol, basis=basis,
                            explanation=None if okay else _why(s, Decimal(str(t.value)), missing,
                                                               "reconciliation_not_tagged" if not rec.get(key) else None),
                            evidence={"segments": [x.fact_key for x in rs], "reconciling": [x.fact_key for x in rec.get(key, [])],
                                      "total": t.fact_key, "role": role, "members_missing": missing}))
        for axis in DISAGG_AXES:
            tables = axis_tables(pa, axis, children)
            for key, members in by_axis.get(axis, {}).items():
                t = totals.get(key)
                if t is None:
                    continue
                for role, top in tables:
                    names = [m for m in top if m in members]
                    rs = [members[m] for m in names]
                    if len(rs) < 2:
                        continue
                    s = sum(Decimal(str(x.value)) for x in rs)
                    tol, basis = _sum_tol(rs + [t])
                    okay = abs(s - Decimal(str(t.value))) <= tol
                    missing = [m for m in top if m not in members]
                    bk = f"{key[0]}|{axis}|{role.rsplit('/', 1)[-1]}"
                    ev = {"members": [x.fact_key for x in rs], "total": t.fact_key, "role": role, "members_missing": missing}
                    vs = ventilations(rs, t) if not okay and s > Decimal(str(t.value)) else []
                    if vs:
                        # plusieurs ventilations dans un tableau : ok si chaque membre est dans l'une d'elles (D-0080)
                        ev["ventilations"] = [[rs[i].fact_key for i in v] for v in vs]
                        outside = [names[i] for i in range(len(rs)) if not any(i in v for v in vs)]
                        if not outside:
                            first = [rs[i] for i in vs[0]]
                            vtol, vbasis = _sum_tol(first + [t])
                            out.append(ctrl("c12_revenue_disaggregation", g, key[1], key[2], "as_known", as_of, "ok", acc,
                                            breakdown=bk, lhs=sum(Decimal(str(x.value)) for x in first),
                                            rhs=Decimal(str(t.value)), tol=vtol, basis=vbasis, evidence=ev))
                        else:
                            ev["outside"] = outside
                            out.append(ctrl("c12_revenue_disaggregation", g, key[1], key[2], "as_known", as_of,
                                            "not_testable", acc, breakdown=bk, evidence=ev,
                                            reason="membres qui se recoupent : une partie seulement somme au total"))
                        continue
                    out.append(ctrl("c12_revenue_disaggregation", g, key[1], key[2], "as_known", as_of,
                                    "ok" if okay else "mismatch", acc, breakdown=bk, lhs=s, rhs=Decimal(str(t.value)),
                                    tol=tol, basis=basis,
                                    explanation=None if okay else _why(s, Decimal(str(t.value)), missing), evidence=ev))
    return out


def debt_rollforward(con, as_of):
    """C8 : variation de la dette − (émissions − remboursements) = résidu, par 10-K.
    La dette est la valeur comptable rattachée (annexe B) ; le résidu se publie, nommé."""
    out = []
    debt = _facts(con, "debt_carrying_amount")
    pro = _facts(con, "debt_proceeds")
    rep = _facts(con, "debt_repayments")
    annual = con.execute("""SELECT DISTINCT group_id, accession FROM facts
                            WHERE source = 'instance' AND form IN ('10-K', '10-K/A', '10-KT', '20-F', '20-F/A')""").fetchall()
    debt = debt[debt["n_dims"] == 0]
    for g, acc in annual:
        fa = debt[debt["accession"] == acc]
        ends = sorted({e for e in fa["period_end"] if e is not None})
        if len(ends) < 2:
            out.append(ctrl("c8_debt_rollforward", g, None, None, "as_known", as_of, "not_testable", acc,
                            breakdown=acc, reason="dette non balisée aux deux dates du bilan de ce 10-K"))
            continue
        e1, e0 = ends[-1], ends[-2]
        b1 = max(fa[fa["period_end"] == e1].itertuples(), key=lambda x: (x.decimals_inf is True, x.decimals or -99))
        b0 = max(fa[fa["period_end"] == e0].itertuples(), key=lambda x: (x.decimals_inf is True, x.decimals or -99))
        p = [x for x in pro[(pro["accession"] == acc) & (pro["n_dims"] == 0) & (pro["period_end"] == e1)].itertuples()
             if x.period_start and (x.period_start - e0).days in range(0, 8)]
        r = [x for x in rep[(rep["accession"] == acc) & (rep["n_dims"] == 0) & (rep["period_end"] == e1)].itertuples()
             if x.period_start and (x.period_start - e0).days in range(0, 8)]
        ps = (p or r)[0].period_start if (p or r) else e0 + dt.timedelta(days=1)
        if not p and not r:
            out.append(ctrl("c8_debt_rollforward", g, ps, e1, "as_known", as_of, "not_testable", acc,
                            reason="émissions et remboursements de dette non balisés dans le tableau des flux"))
            continue
        dv = Decimal(str(b1.value)) - Decimal(str(b0.value))
        flows = sum((Decimal(str(x.value)) for x in p), Decimal(0)) - sum((Decimal(str(x.value)) for x in r), Decimal(0))
        tol, basis = _sum_tol([b1, b0] + p + r)
        okay = abs(dv - flows) <= tol
        out.append(ctrl("c8_debt_rollforward", g, ps, e1, "as_known", as_of, "ok" if okay else "mismatch", acc,
                        lhs=dv, rhs=flows, tol=tol, basis=basis,
                        explanation=None if okay else "residual_noncash_or_untagged_flows",
                        evidence={"debt": [b0.fact_key, b1.fact_key], "debt_concept": b1.concept,
                                  "proceeds": [x.fact_key for x in p], "repayments": [x.fact_key for x in r],
                                  "residual": str(dv - flows),
                                  "note": "résidu = éléments non monétaires (décotes, frais d'émission, change, "
                                          "acquisitions, conversions) et flux nets non balisés ; publié, jamais équilibré"}))
    return out
