"""Mesures de rang 2 tirées des faits balisés (§4.2 à §4.6, §5.5, §6.2), codées après la
seconde page (§11.1) : rentabilité, fonds de roulement, liquidité et couverture, flux après
rémunération en actions, capitaux propres et dilution, qualité du résultat.

Mêmes règles que le rang 1 : une variation en glissement annuel ou sur douze mois glissants,
un terme manquant rend un ratio `not_determinable` et une somme `partial`, jamais complétée par
un zéro ; aucune arithmétique sur un chiffre lu dans le texte ; toute arithmétique ici porte
sur des faits balisés, avec leurs clés en lignée.
"""
import datetime as dt
import json
from decimal import Decimal

from . import model
from .measures import NONE, Series, _ratio, cell

QUARTER_FLOWS = {"gross_profit", "cost_of_revenue", "operating_income", "revenue_total", "capex_cash", "cfo",
                 "sbc_expense", "net_income", "depreciation_expense", "rou_obtained_operating_lease",
                 "capitalized_interest", "pik_interest", "interest_expense", "diluted_shares_weighted"}


def _nd(S, qn, r):
    """Motif d'une valeur absente : concept non résolu pour ce groupe, sinon non publié."""
    if not S.has(qn):
        return "concept_unresolved"
    return r if r and r != "concept_unresolved" else "not_disclosed"


def group_rank2(con, groups, as_of):
    occ = model.occurrences_df(con)
    cals = model.calendars()
    rd = model.original_report_dates(con)
    as_of_d = dt.date.fromisoformat(as_of)
    out = []
    for g in groups:
        cal = cals[g]
        ws = dt.date.fromisoformat(cal["window"]["window_start"])
        S = Series(occ, g, cal)
        quarters = [q for q in S.quarters if q["end"] >= ws and q["end"] <= as_of_d]
        for view in ("revised", "as_known"):
            for q in quarters:
                cutoff = as_of_d if view == "revised" else (rd.get((g, q["end"])) or as_of_d)
                out += quarter_rank2(S, g, q, cutoff, view, as_of)
            years = sorted({q["fy_end"] for q in quarters if q["fy_end"] and q["fy_end"] <= as_of_d})
            for fe in years:
                fqs = S.fy.get(fe, [])
                if not fqs or fqs[0]["start"] is None:
                    continue
                cutoff = as_of_d if view == "revised" else (rd.get((g, fe)) or as_of_d)
                out += annual_rank2(S, g, fqs[0]["start"], fe, cutoff, view, as_of)
    return out


def _ratio_cell(m, g, ps, pe, view, as_of, num, t_num, r_num, den, t_den, r_den, S, qn_num, qn_den,
                term=NONE, unit="pure", flags=None, breakdown=NONE):
    if num is None or den is None:
        r = _nd(S, qn_num, r_num) if num is None else _nd(S, qn_den, r_den)
        return cell(m, g, ps, pe, view, as_of, term=term, breakdown=breakdown, status="not_determinable",
                    nd_reason=r, terms=t_num + t_den, flags=flags)
    v, r = _ratio(num, den)
    return cell(m, g, ps, pe, view, as_of, term=term, breakdown=breakdown, value=v, numerator=num,
                denominator=den, unit=unit, terms=t_num + t_den, flags=flags,
                status="computed" if v is not None else "not_determinable", nd_reason=r)


def quarter_rank2(S, g, q, cutoff, view, as_of):
    ps, pe = q["start"], q["end"]
    out = []
    rev, t_rev, r_rev = S.quarter("revenue_total", q, cutoff)
    # marge brute : GrossProfit publié, sinon revenu − coût des ventes présenté (§4.2)
    gp, t_gp, r_gp = S.quarter("gross_profit", q, cutoff)
    fl = None
    if gp is None:
        cor, t_cor, r_cor = S.quarter("cost_of_revenue", q, cutoff)
        if cor is not None and rev is not None:
            gp, t_gp, r_gp, fl = rev - cor, t_cor, None, {"gross_profit_basis": "revenue_minus_cost_of_revenue"}
        else:
            r_gp = _nd(S, "cost_of_revenue", r_cor) if not S.has("gross_profit") else r_gp
    out.append(_ratio_cell("gross_margin", g, ps, pe, view, as_of, gp, t_gp, r_gp, rev, t_rev, r_rev, S,
                           "gross_profit" if S.has("gross_profit") else "cost_of_revenue", "revenue_total", flags=fl))
    oi, t_oi, r_oi = S.quarter("operating_income", q, cutoff)
    out.append(_ratio_cell("operating_margin", g, ps, pe, view, as_of, oi, t_oi, r_oi, rev, t_rev, r_rev, S,
                           "operating_income", "revenue_total"))
    capex, t_capex, r_capex = S.quarter("capex_cash", q, cutoff)
    out.append(_ratio_cell("capex_to_revenue", g, ps, pe, view, as_of, capex, t_capex, r_capex, rev, t_rev, r_rev, S,
                           "capex_cash", "revenue_total"))
    # flux après rémunération en actions ; rémunération en actions ÷ CFO ; écart CFO − résultat
    cfo, t_cfo, r_cfo = S.quarter("cfo", q, cutoff)
    sbc, t_sbc, r_sbc = S.quarter("sbc_expense", q, cutoff)
    if cfo is not None and capex is not None and sbc is not None:
        out.append(cell("fcf_after_sbc", g, ps, pe, view, as_of, value=cfo - capex - sbc, unit="USD",
                        terms=t_cfo + t_capex + t_sbc))
    else:
        r = (_nd(S, "cfo", r_cfo) if cfo is None else _nd(S, "capex_cash", r_capex) if capex is None
             else _nd(S, "sbc_expense", r_sbc))
        out.append(cell("fcf_after_sbc", g, ps, pe, view, as_of, status="not_determinable", nd_reason=r,
                        terms=t_cfo + t_capex + t_sbc))
    out.append(_ratio_cell("sbc_to_cfo", g, ps, pe, view, as_of, sbc, t_sbc, r_sbc, cfo, t_cfo, r_cfo, S,
                           "sbc_expense", "cfo"))
    ni, t_ni, r_ni = S.quarter("net_income", q, cutoff)
    if cfo is not None and ni is not None:
        da, t_da, _ = S.quarter("depreciation_expense", q, cutoff)
        comp = {"depreciation_and_amortization": str(da) if da is not None else None,
                "share_based_compensation": str(sbc) if sbc is not None else None}
        out.append(cell("cfo_net_income_gap", g, ps, pe, view, as_of, value=cfo - ni, unit="USD",
                        terms=t_cfo + t_ni, flags={"components_tagged": comp,
                                                   "note": "écart CFO − résultat net ; composantes balisées en regard, sans reste calculé"}))
    else:
        out.append(cell("cfo_net_income_gap", g, ps, pe, view, as_of, status="not_determinable",
                        nd_reason=_nd(S, "cfo", r_cfo) if cfo is None else _nd(S, "net_income", r_ni)))
    # intérêts capitalisés, intérêts payés en nature, droits d'utilisation obtenus (location simple)
    for m, qn in (("capitalized_interest", "capitalized_interest"), ("cov_pik_interest", "pik_interest"),
                  ("operating_lease_rou_additions", "rou_obtained_operating_lease")):
        v, t, r = S.quarter(qn, q, cutoff)
        out.append(cell(m, g, ps, pe, view, as_of, value=v, unit="USD", terms=t,
                        status="computed" if v is not None else "not_determinable",
                        nd_reason=None if v is not None else _nd(S, qn, r)))
    # couverture des intérêts sur douze mois glissants, sans et avec réintégration des intérêts capitalisés
    oi_t, t_oit, r_oit = S.ttm("operating_income", q, cutoff)
    ie_t, t_iet, r_iet = S.ttm("interest_expense", q, cutoff)
    out.append(_ratio_cell("cov_interest_coverage", g, ps, pe, view, as_of, oi_t, t_oit, r_oit, ie_t, t_iet, r_iet,
                           S, "operating_income", "interest_expense", term="without"))
    ci_t, t_cit, r_cit = S.ttm("capitalized_interest", q, cutoff)
    if ie_t is not None and ci_t is not None:
        out.append(_ratio_cell("cov_interest_coverage", g, ps, pe, view, as_of, oi_t, t_oit, r_oit, ie_t + ci_t,
                               t_iet + t_cit, None, S, "operating_income", "interest_expense", term="with"))
    else:
        out.append(cell("cov_interest_coverage", g, ps, pe, view, as_of, term="with", status="not_determinable",
                        nd_reason=_nd(S, "interest_expense", r_iet) if ie_t is None else _nd(S, "capitalized_interest", r_cit)))
    # fonds de roulement : quatre termes, solde net et variation (§4.2)
    wc = {}
    for term, qn in (("receivables", "accounts_receivable_net"), ("inventories", "inventories"),
                     ("payables", "accounts_payable"), ("contract_liabilities", "contract_liabilities_current")):
        t = S.instant(qn, pe, cutoff)
        wc[term] = t
        out.append(cell("working_capital", g, None, pe, view, as_of, term=term, value=t["value"] if t else None,
                        unit="USD", terms=[t] if t else [], status="computed" if t else "not_determinable",
                        nd_reason=None if t else _nd(S, qn, None)))
    have = {k: v for k, v in wc.items() if v}
    if have:
        net = sum((v["value"] if k in ("receivables", "inventories") else -v["value"]) for k, v in have.items())
        st = "computed" if len(have) == 4 else "partial"
        out.append(cell("working_capital", g, None, pe, view, as_of, term="net", value=net, unit="USD",
                        terms=list(have.values()), status=st, nd_reason=None if st == "computed" else "term_missing",
                        flags={"terms_missing": sorted(set(wc) - set(have))} if st == "partial" else None))
        pq = S.prior(q, 1)
        if pq:
            prev = {}
            for term, qn in (("receivables", "accounts_receivable_net"), ("inventories", "inventories"),
                             ("payables", "accounts_payable"), ("contract_liabilities", "contract_liabilities_current")):
                t = S.instant(qn, pq["end"], cutoff)
                if t:
                    prev[term] = t
            if set(prev) == set(have):
                pnet = sum((v["value"] if k in ("receivables", "inventories") else -v["value"]) for k, v in prev.items())
                out.append(cell("working_capital", g, ps, pe, view, as_of, term="change", value=net - pnet, unit="USD",
                                terms=list(have.values()) + list(prev.values()), status=st,
                                nd_reason=None if st == "computed" else "term_missing"))
            else:
                out.append(cell("working_capital", g, ps, pe, view, as_of, term="change", status="not_determinable",
                                nd_reason="prior_period_missing"))
        else:
            out.append(cell("working_capital", g, ps, pe, view, as_of, term="change", status="not_determinable",
                            nd_reason="prior_period_missing"))
    else:
        for term in ("net", "change"):
            out.append(cell("working_capital", g, None if term == "net" else ps, pe, view, as_of, term=term,
                            status="not_determinable", nd_reason="term_missing"))
    # capitaux propres et déficit cumulé ; variation du nombre moyen dilué d'actions (glissement annuel)
    for term, qn in (("equity", "stockholders_equity"), ("accumulated_deficit", "accumulated_deficit")):
        t = S.instant(qn, pe, cutoff)
        out.append(cell("eq_equity_and_accumulated_deficit", g, None, pe, view, as_of, term=term,
                        value=t["value"] if t else None, unit="USD", terms=[t] if t else [],
                        status="computed" if t else "not_determinable", nd_reason=None if t else _nd(S, qn, None)))
    sh, t_sh, r_sh = S.quarter("diluted_shares_weighted", q, cutoff)
    p4 = S.prior(q, 4)
    if sh is not None and p4:
        sh0, t_sh0, r_sh0 = S.quarter("diluted_shares_weighted", p4, cutoff)
        if sh0:
            v, r = _ratio(sh - sh0, sh0)
            out.append(cell("eq_diluted_share_count_change", g, ps, pe, view, as_of, value=v, numerator=sh - sh0,
                            denominator=sh0, unit="pure", terms=t_sh + t_sh0,
                            status="computed" if v is not None else "not_determinable", nd_reason=r))
        else:
            out.append(cell("eq_diluted_share_count_change", g, ps, pe, view, as_of, status="not_determinable",
                            nd_reason=_nd(S, "diluted_shares_weighted", r_sh0)))
    else:
        out.append(cell("eq_diluted_share_count_change", g, ps, pe, view, as_of, status="not_determinable",
                        nd_reason=_nd(S, "diluted_shares_weighted", r_sh) if sh is None else "prior_period_missing"))
    # facilités confirmées non tirées ; acomptes clients ; part des en-cours
    t = S.instant("undrawn_committed_facilities", pe, cutoff)
    out.append(cell("liq_undrawn_committed_facilities", g, None, pe, view, as_of, value=t["value"] if t else None,
                    unit="USD", terms=[t] if t else [], status="computed" if t else "not_determinable",
                    nd_reason=None if t else _nd(S, "undrawn_committed_facilities", None)))
    t = S.instant("contract_liabilities", pe, cutoff) or S.instant("contract_liabilities_current", pe, cutoff)
    out.append(cell("customer_advances", g, None, pe, view, as_of, value=t["value"] if t else None, unit="USD",
                    terms=[t] if t else [], status="computed" if t else "not_determinable",
                    nd_reason=None if t else _nd(S, "contract_liabilities", None),
                    flags={"note": "passifs de contrat ; seuls les acomptes à composante de financement publiée "
                                   "entrent dans la mesure miroir (§3.3)"} if t else None))
    cip = S.instant("construction_in_progress", pe, cutoff)
    gross = S.instant("gross_depreciable_ppe", pe, cutoff)
    out.append(_ratio_cell("cip_share", g, None, pe, view, as_of, cip["value"] if cip else None, [cip] if cip else [],
                           None, gross["value"] if gross else None, [gross] if gross else [], None, S,
                           "construction_in_progress", "gross_depreciable_ppe"))
    return out


def annual_rank2(S, g, fs, fe, cutoff, view, as_of):
    out = []
    # capex en droits constatés : décaissé + variation de l'impayé publié d'un exercice à l'autre (§5.5)
    capex = S.duration("capex_cash", fs, fe, cutoff)
    un1 = S.duration("unpaid_capex", fs, fe, cutoff) or S.instant("unpaid_capex", fe, cutoff)
    prev_fe = fs - dt.timedelta(days=1)
    fqs_prev = S.fy.get(prev_fe) or next((v for k, v in S.fy.items() if k and abs((k - prev_fe).days) <= 7), None)
    un0 = None
    if fqs_prev and fqs_prev[0]["start"]:
        un0 = S.duration("unpaid_capex", fqs_prev[0]["start"], fqs_prev[-1]["end"], cutoff) or \
            S.instant("unpaid_capex", fqs_prev[-1]["end"], cutoff)
    if capex and un1 and un0:
        out.append(cell("capex_accrual", g, fs, fe, view, as_of, value=capex["value"] + un1["value"] - un0["value"],
                        unit="USD", terms=[capex, un1, un0],
                        flags={"basis": "impayé publié pour chaque exercice lu comme l'encours de fin d'exercice",
                               "judgment_sensitive": True}))
    else:
        out.append(cell("capex_accrual", g, fs, fe, view, as_of, status="not_determinable",
                        nd_reason=(_nd(S, "capex_cash", None) if not capex else _nd(S, "unpaid_capex", None)
                                   if not un1 else "prior_period_missing")))
    # durée d'utilité implicite : brut amortissable moyen (hors terrains et en-cours) ÷ dotations
    def depreciable(end):
        g_ = S.instant("gross_depreciable_ppe", end, cutoff)
        if not g_:
            return None, []
        land = S.instant("land", end, cutoff)
        cip = S.instant("construction_in_progress", end, cutoff)
        return g_["value"] - (land["value"] if land else 0) - (cip["value"] if cip else 0), \
            [x for x in (g_, land, cip) if x]
    d1, t1 = depreciable(fe)
    d0, t0 = depreciable(fqs_prev[-1]["end"]) if fqs_prev else (None, [])
    dep = S.duration("depreciation_expense", fs, fe, cutoff)
    if d1 is not None and d0 is not None and dep and dep["value"] > 0:
        avg = (d1 + d0) / 2
        out.append(cell("implied_useful_life", g, fs, fe, view, as_of, value=avg / dep["value"], numerator=avg,
                        denominator=dep["value"], unit="years", terms=t1 + t0 + [dep],
                        flags={"note": "dotations du tableau des flux (amortissement des incorporels compris) : "
                                       "durée implicite par défaut", "land_or_cip_untagged": len(t1) < 3}))
    else:
        out.append(cell("implied_useful_life", g, fs, fe, view, as_of, status="not_determinable",
                        nd_reason=(_nd(S, "gross_depreciable_ppe", None) if d1 is None else "prior_period_missing"
                                   if d0 is None else _nd(S, "depreciation_expense", None))))
    # part des effets publiés du pont dans le résultat avant impôt (§6.2) : seulement si celui-ci
    # est positif et dépasse 5 % du revenu ; un terme non publié rend la part partielle
    pretax = S.duration("pretax_income_continuing", fs, fe, cutoff)
    rev = S.duration("revenue_total", fs, fe, cutoff)
    effects, missing = [], []
    for qn, sign in (("investment_gain_loss", 1), ("investment_impairment", -1), ("equity_method_income", 1),
                     ("dilution_gain", 1), ("capitalized_interest", 1)):
        t = S.duration(qn, fs, fe, cutoff)
        if t:
            effects.append((qn, sign, t))
        else:
            missing.append(qn)
    if not pretax or not rev:
        out.append(cell("earnings_bridge_share", g, fs, fe, view, as_of, status="not_determinable",
                        nd_reason=_nd(S, "pretax_income_continuing", None) if not pretax else _nd(S, "revenue_total", None)))
    elif pretax["value"] <= 0:
        out.append(cell("earnings_bridge_share", g, fs, fe, view, as_of, status="not_determinable",
                        nd_reason="denominator_nonpositive", terms=[pretax]))
    elif pretax["value"] <= Decimal("0.05") * rev["value"]:
        out.append(cell("earnings_bridge_share", g, fs, fe, view, as_of, status="not_determinable",
                        nd_reason="denominator_below_threshold", terms=[pretax, rev]))
    elif not effects:
        out.append(cell("earnings_bridge_share", g, fs, fe, view, as_of, status="not_determinable",
                        nd_reason="term_missing", terms=[pretax]))
    else:
        tot = sum(sign * t["value"] for _, sign, t in effects)
        out.append(cell("earnings_bridge_share", g, fs, fe, view, as_of, value=tot / pretax["value"], numerator=tot,
                        denominator=pretax["value"], unit="pure", terms=[t for _, _, t in effects] + [pretax],
                        status="computed" if not missing else "partial", nd_reason=None if not missing else "term_missing",
                        flags={"effects": {qn: str(sign * t["value"]) for qn, sign, t in effects},
                               "effects_missing": missing}))
    return out


# -- mesures lues dans les faits dimensionnés de l'instance -----------------------------------

def _facts(con, where):
    df = con.execute(f"""SELECT fact_key, group_id, accession, form, concept, period_type, period_start, period_end,
                                 dims, n_dims, value, value_text, decimals, decimals_inf, knowledge_date, tier, is_tagged
                          FROM facts WHERE source = 'instance' AND NOT coalesce(conflict, false) AND {where}
                          ORDER BY group_id, knowledge_date, accession, fact_key""").fetchdf()
    from .measures import ds
    for c in ("period_start", "period_end", "knowledge_date"):
        df[c] = [ds(x) for x in df[c]]
    return df


def _term(r):
    return {"value": Decimal(str(r.value)), "fact_key": r.fact_key, "knowledge_date": r.knowledge_date,
            "tier": r.tier, "is_tagged": bool(r.is_tagged)}


def _by_view(df, keycols):
    """Pour chaque clé : le premier dépôt qui la publie (as_known) et le dernier (revised)."""
    out = []
    for key, g in df.groupby(keycols, sort=True, dropna=False):
        g = g.sort_values(["knowledge_date", "accession"])
        out.append((key, "as_known", g.iloc[0]))
        out.append((key, "revised", g.iloc[-1]))
    return out


def rpo_beyond(con, groups, as_of):
    """rpo_beyond_12m = RPO total × (1 − part attendue dans les 12 mois), seulement si la part est
    publiée pour un horizon de 12 mois commençant le lendemain de la date du bilan."""
    import datetime as _dt
    out = []
    tot = _facts(con, "concept = 'us-gaap:RevenueRemainingPerformanceObligation' AND n_dims = 0 AND value IS NOT NULL")
    pct = _facts(con, "concept = 'us-gaap:RevenueRemainingPerformanceObligationPercentage' AND n_dims = 1")
    per = _facts(con, "concept = 'us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionPeriod1' AND n_dims = 1")
    hz = {(r.accession, r.dims): (r.value_text or "") for r in per.itertuples()}
    for (g, pe), view, r in _by_view(tot[tot["group_id"].isin(groups)], ["group_id", "period_end"]):
        start = (_dt.date.fromisoformat(pe) + _dt.timedelta(days=1)).isoformat()
        cands = pct[(pct["accession"] == r.accession) & pct["dims"].str.contains(f"typed:{start}", regex=False)]
        p12 = [c for c in cands.itertuples() if hz.get((c.accession, c.dims)) in ("P12M", "P1Y")]
        if p12:
            c = p12[0]
            v = Decimal(str(r.value)) * (1 - Decimal(str(c.value)))
            out.append(cell("rpo_beyond_12m", g, None, pe, view, as_of, value=v, unit="USD", terms=[_term(r), _term(c)],
                            flags={"share_within_12m": str(c.value)}))
        else:
            hzs = sorted({hz.get((c.accession, c.dims)) for c in cands.itertuples()} - {None, ""})
            out.append(cell("rpo_beyond_12m", g, None, pe, view, as_of, status="not_determinable",
                            nd_reason="not_disclosed", terms=[_term(r)],
                            flags={"horizons_published": hzs} if hzs else None))
    return out


SEG = "us-gaap:StatementBusinessSegmentsAxis"
OPSEG = ["srt:ConsolidationItemsAxis", "us-gaap:OperatingSegmentsMember"]


def _segment_member(dims):
    d = json.loads(dims)
    axes = {a for a, _ in d}
    if SEG not in axes or not axes <= {SEG, OPSEG[0]}:
        return None
    if OPSEG[0] in axes and [OPSEG[0], dict(d)[OPSEG[0]]] != OPSEG:
        return None
    return dict(d)[SEG]


def segments(con, groups, as_of):
    """segment_revenue et segment_profit : faits dimensionnés par secteur, tels que balisés
    (§4.2) ; le résultat sectoriel est OperatingIncomeLoss par secteur, sinon la marge brute
    sectorielle, libellé du concept en drapeau ; deux résultats ne se comparent qu'à concept égal."""
    out = []
    cmap = con.execute("SELECT DISTINCT group_id, concept FROM concept_map WHERE quantity = 'revenue_total'").fetchall()
    rev_concepts = {}
    for g, c in cmap:
        rev_concepts.setdefault(g, set()).add(c)
    df = _facts(con, f"dims LIKE '%StatementBusinessSegmentsAxis%' AND period_type = 'duration' AND value IS NOT NULL")
    df = df[df["group_id"].isin(groups)]
    df["member"] = df["dims"].map(_segment_member)
    df = df[df["member"].notna()]
    for m, concepts in (("segment_revenue", None), ("segment_profit", ["us-gaap:OperatingIncomeLoss", "us-gaap:GrossProfit"])):
        if m == "segment_revenue":
            sel = df[[c in rev_concepts.get(g, ()) for g, c in zip(df["group_id"], df["concept"])]]
        else:
            sel = df[df["concept"].isin(concepts)]
            # un seul concept par groupe : le premier de la liste qu'il balise par secteur
            keep = []
            for g, x in sel.groupby("group_id"):
                c0 = next(c for c in concepts if c in set(x["concept"]))
                keep.append(x[x["concept"] == c0])
            sel = __import__("pandas").concat(keep) if keep else sel.iloc[0:0]
        for (g, mem, ps, pe), view, r in _by_view(sel, ["group_id", "member", "period_start", "period_end"]):
            out.append(cell(m, g, ps, pe, view, as_of, breakdown=mem, value=Decimal(str(r.value)), unit="USD",
                            terms=[_term(r)], flags={"concept": r.concept} if m == "segment_profit" else None))
    return out


def supplier_concentration(con, groups, as_of):
    """supplier_concentration : parts publiées d'achats ou de coûts par fournisseur (§3.6), telles
    que balisées ; un fournisseur anonyme reste anonyme."""
    out = []
    df = _facts(con, "concept = 'us-gaap:ConcentrationRiskPercentage1' AND dims LIKE '%SupplierConcentrationRiskMember%' AND value IS NOT NULL")
    df = df[df["group_id"].isin(groups)]
    df["key"] = df["dims"].map(lambda d: json.dumps([x for x in json.loads(d) if x[0] != "us-gaap:ConcentrationRiskByTypeAxis"]))
    for (g, key, ps, pe), view, r in _by_view(df, ["group_id", "key", "period_start", "period_end"]):
        out.append(cell("supplier_concentration", g, ps, pe, view, as_of, breakdown=key[:500], value=Decimal(str(r.value)),
                        unit="pure", terms=[_term(r)]))
    return out


# -- mesures alimentées par le texte (bloc text de §14) ---------------------------------------

def _obs_date(o, report_end_of):
    from .measures import ds
    for k in ("period_end", "event_date"):
        v = ds(o.get(k))
        if v != NONE:
            return dt.date.fromisoformat(v)
    d = report_end_of.get(o.get("accession"))
    return d


def lease_not_commenced(cells, obs, report_end_of, as_of):
    """Baux signés non commencés (ASC 842-20-50-3(b)) lus dans les notes de baux : une cellule de
    la matrice d'exposition par groupe et date (flux non actualisés), et la clôture et
    l'ouverture du pont annuel ; les nouveaux baux et les baux commencés restent non publiés."""
    out = []
    lines = [o for o in obs if o.get("category_id") == "lease_not_commenced" and o.get("amount") is not None
             and o.get("unit") == "USD" and o["validation_state"] == "valid" and o.get("kind") == "observation"]
    by = {}
    for o in lines:
        d = _obs_date(o, report_end_of)
        if d:
            by.setdefault((o["group_id"], d), []).append(o)

    def value_at(g, d):
        hits = [v for (gg, dd), v in by.items() if gg == g and abs((dd - d).days) <= 7]
        hits = [o for v in hits for o in v]
        if not hits:
            return None
        amounts = {}
        for o in hits:
            amounts.setdefault(o.get("instrument_key") or o["obs_key"], o)
        tot = sum(Decimal(str(o["amount"])) for o in amounts.values())
        terms = [{"value": Decimal(str(o["amount"])), "fact_key": "obs:" + o["obs_key"],
                  "knowledge_date": o.get("knowledge_date"), "tier": o.get("tier"), "is_tagged": False} for o in amounts.values()]
        return tot, terms, len(amounts), hits
    # matrice d'exposition à chaque date lue
    for (g, d), v in sorted(by.items()):
        tot, terms, n, hits = value_at(g, d)
        out.append(cell("exposure_matrix", g, None, d, "as_known", as_of,
                        breakdown="contractual_outflows/undiscounted/lease_not_commenced/total", value=tot, unit="USD",
                        terms=terms, status="computed" if n == 1 else "partial", nd_reason=None if n == 1 else "term_missing",
                        flags={"observations": [o["obs_key"] for o in hits], "lines": n,
                               "note": None if n == 1 else "plusieurs lignes, additivité non démontrée"}))
    # pont annuel : remplace ouverture et clôture indéterminées
    repl = {}
    for c in cells:
        if c["measure"] != "lease_not_commenced_bridge" or c["term"] not in ("opening", "closing"):
            continue
        g, fs, fe = c["subject"], dt.date.fromisoformat(c["period_start"]), dt.date.fromisoformat(c["period_end"])
        d = fe if c["term"] == "closing" else fs - dt.timedelta(days=1)
        r = value_at(g, d)
        if r:
            tot, terms, n, hits = r
            repl[id(c)] = cell("lease_not_commenced_bridge", g, fs, fe, c["view"], as_of, term=c["term"], value=tot,
                               unit="USD", terms=terms, status="computed" if n == 1 else "partial",
                               nd_reason=None if n == 1 else "term_missing",
                               flags={"observations": [o["obs_key"] for o in hits], "is_tagged": False})
    cells[:] = [repl.get(id(c), c) for c in cells]
    return out


LEVER_NOTE_RX = __import__("re").compile(r"^\s*effet\s*:\s*([+\-−])\s*(résultat opérationnel|resultat operationnel|dotations?)",
                                         __import__("re").I)      # « résultat net » : effet net d'impôt, jamais retraité


def depreciation_lever(cells, obs, as_of):
    """depreciation_life_change_effect et lever_restatement (levier 1 de §6.1) : l'effet publié
    d'un changement de durée d'utilité, pour sa seule période (ASC 250-10-50-4), puis publié,
    retraité et écart du résultat opérationnel de la même période ; sans effet publié, rien
    n'est retraité. Le signe vient de la note de la ligne (« effet : + résultat » ou
    « effet : − résultat »), écrite par le lecteur d'après le texte."""
    out = []
    lines = [o for o in obs if o.get("kind") == "observation" and o["validation_state"] == "valid"
             and o.get("block_kind") == "lever_note" and o.get("event_type") == "measurement_change"
             and o.get("amount") is not None and o.get("unit") == "USD"]
    seen = set()
    for o in lines:
        m = LEVER_NOTE_RX.match(o.get("note") or "")
        ps, pe = o.get("period_start"), o.get("period_end")
        if not m or not ps or not pe:
            continue
        key = (o["group_id"], ps, pe, o.get("instrument_key") or o["obs_key"])
        if key in seen:
            continue
        seen.add(key)
        sign = Decimal(1) if m.group(1) == "+" else Decimal(-1)
        on_income = m.group(2).lower().startswith("r")
        v = sign * Decimal(str(o["amount"])) * (1 if on_income else -1)
        term = {"value": Decimal(str(o["amount"])), "fact_key": "obs:" + o["obs_key"],
                "knowledge_date": o.get("knowledge_date"), "tier": o.get("tier"), "is_tagged": False}
        out.append(cell("depreciation_life_change_effect", o["group_id"], ps, pe, "as_known", as_of,
                        breakdown=o.get("instrument_key") or NONE, value=v, unit="USD", terms=[term],
                        flags={"effect_on_income": str(v), "note": o.get("note"), "observation": o["obs_key"],
                               "judgment_sensitive": True}))
    return out


def lever_restatement(con, effects, as_of):
    """Pour chaque effet publié de changement de durée d'utilité : résultat opérationnel publié de
    la même période, retraité (publié − effet) et écart (§6.4) ; jamais le retraité seul."""
    out = []
    if not effects:
        return out
    occ = model.occurrences_df(con)
    cals = model.calendars()
    as_of_d = dt.date.fromisoformat(as_of)
    for e in effects:
        g = e["subject"]
        S = Series(occ, g, cals[g])
        ps, pe = dt.date.fromisoformat(e["period_start"]), dt.date.fromisoformat(e["period_end"])
        pub = S.duration("operating_income", ps, pe, as_of_d)
        key = e["breakdown_key"]
        if not pub:
            for term in ("published", "restated", "difference"):
                out.append(cell("lever_restatement", g, ps, pe, "as_known", as_of, term=term, breakdown=f"depreciation_life|{key}",
                                status="not_determinable", nd_reason="term_missing"))
            continue
        eff = Decimal(str(e["value"]))
        terms = [pub, {"value": abs(eff), "fact_key": json.loads(e["lineage"])[0], "knowledge_date": e["knowledge_date"],
                       "tier": None, "is_tagged": False}]
        for term, v in (("published", pub["value"]), ("restated", pub["value"] - eff), ("difference", eff)):
            out.append(cell("lever_restatement", g, ps, pe, "as_known", as_of, term=term, breakdown=f"depreciation_life|{key}",
                            value=v, unit="USD", terms=terms,
                            flags={"basis": "résultat opérationnel publié moins l'effet publié du changement de durée, "
                                            "pour la seule période de l'effet"}))
    return out
