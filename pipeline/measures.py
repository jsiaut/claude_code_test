"""Mesures de rang 1 tirées des faits balisés, sans texte (§4, §5, §6, §11.1).

Une variation se calcule en glissement annuel ou sur douze mois glissants (§4.1) ;
un terme manquant rend un ratio not_determinable et une somme partial, jamais estimé ;
aucun score composite. Ratios arrondis à six décimales (ROUND_HALF_EVEN), règle déclarée.
"""
import datetime as dt
import json
from decimal import ROUND_HALF_EVEN, Decimal

from . import model
from .registry import MEASURES

Q6 = Decimal("0.000001")
NONE = "none"


def _q(x):
    return None if x is None else Decimal(x).quantize(Q6, rounding=ROUND_HALF_EVEN)


def ds(x):
    """Date d'une clé de cellule ou de contrôle : 'AAAA-MM-JJ', ou 'none' ; jamais une heure
    ni 'NaT' (un Timestamp de pandas se lit sinon '2025-12-31 00:00:00' et ne se rapproche plus)."""
    if x is None or (isinstance(x, float) and x != x) or x is getattr(__import__("pandas"), "NaT"):
        return NONE
    if isinstance(x, dt.datetime):
        return x.date().isoformat()
    if isinstance(x, dt.date):
        return x.isoformat()
    s = str(x)
    if s in ("", NONE, "NaT", "None", "nan"):
        return NONE
    return s[:10] if len(s) >= 10 and s[4] == "-" and s[7] == "-" else s


class Cell(dict):
    pass


def cell(measure, subject, ps, pe, view, as_of, term=NONE, breakdown=NONE, value=None, status="computed",
         nd_reason=None, terms=(), numerator=None, denominator=None, unit=None, flags=None,
         coverage="observed", knowledge_date=None, value_text=None, counterparty=NONE, policy=NONE,
         perimeter=NONE, variant=NONE, lower=None, upper=None, bound_basis=None):
    terms = [t for t in terms if t]
    prof = {}
    tot = sum(abs(Decimal(t["value"])) for t in terms) or Decimal(1)
    for t in terms:
        prof[t.get("tier") or "?"] = prof.get(t.get("tier") or "?", Decimal(0)) + abs(Decimal(t["value"])) / tot
    rank, _, kind, _ = MEASURES[measure]
    if status in ("not_determinable",) and coverage == "observed":
        coverage = {"not_processed": "not_processed", "not_disclosed": "not_disclosed",
                    "concept_unresolved": "not_disclosed", "term_missing": "not_disclosed",
                    "conflicting": "conflicting"}.get(nd_reason, "unknown")
    return Cell(measure=measure, subject=subject, counterparty=counterparty,
                period_start=ds(ps), period_end=ds(pe),
                view=view, as_of=as_of, term=term, breakdown_key=breakdown, financing_policy=policy,
                constant_perimeter=perimeter, variant=variant, rank=rank, period_kind=kind,
                value=_q(value) if value is not None else None, value_text=value_text,
                value_lower=_q(lower), value_upper=_q(upper), bound_basis=bound_basis,
                numerator=_q(numerator), denominator=_q(denominator), unit=unit,
                currency="USD" if unit == "USD" else None, status=status, nd_reason=nd_reason,
                coverage_state=coverage,
                evidence_profile=json.dumps({k: float(round(v, 4)) for k, v in sorted(prof.items())}) if terms else None,
                lineage=json.dumps(sorted({t["fact_key"] for t in terms})) if terms else None,
                knowledge_date=(lambda k: None if k == NONE else k)(ds(knowledge_date or max((str(t["knowledge_date"]) for t in terms), default=None))),
                is_tagged=all(t.get("is_tagged", True) for t in terms) if terms else None,
                flags=json.dumps(flags, sort_keys=True, default=str) if flags else None)


class Series:
    """Accès aux valeurs trimestrielles et annuelles d'un groupe, à une date de coupure."""

    def __init__(self, occ, group, cal):
        self.group = group
        self.occ = occ[occ["group_id"] == group]
        self.by_q = {q: d for q, d in self.occ.groupby("quantity")}
        self.quarters = [q for q in cal["quarters"] if q["start"] is not None]
        self.fy = {}
        for q in cal["quarters"]:
            self.fy.setdefault(q["fy_end"], []).append(q)

    def has(self, qn):
        return qn in self.by_q

    def instant(self, qn, end, cutoff):
        o = self.by_q.get(qn)
        if o is None:
            return None
        return model.term_value(o, None, end, True, cutoff)

    def duration(self, qn, start, end, cutoff):
        o = self.by_q.get(qn)
        if o is None:
            return None
        return model.term_value(o, start, end, False, cutoff)

    def quarter(self, qn, q, cutoff):
        """Valeur d'un trimestre : directe, sinon différence de cumuls ; renvoie
        (valeur, termes, motif)."""
        o = self.by_q.get(qn)
        if o is None:
            return None, [], "concept_unresolved"
        t = model.term_value(o, q["start"], q["end"], False, cutoff)
        if t:
            return t["value"], [t], None
        fqs = self.fy.get(q["fy_end"], [])
        i = next((k for k, x in enumerate(fqs) if x["end"] == q["end"]), None)
        if not i:
            return None, [], "not_disclosed"
        fy_start = fqs[0]["start"]
        cur = model.term_value(o, fy_start, q["end"], False, cutoff)
        prev = model.term_value(o, fy_start, fqs[i - 1]["end"], False, cutoff) if i > 1 else \
            model.term_value(o, fqs[0]["start"], fqs[0]["end"], False, cutoff)
        if cur and prev:
            if cur["revised"] != prev["revised"]:
                return None, [cur, prev], "recast_boundary"
            return cur["value"] - prev["value"], [cur, prev], None
        return None, [x for x in (cur, prev) if x], "term_missing"

    def ttm(self, qn, q, cutoff):
        idx = next((k for k, x in enumerate(self.quarters) if x["end"] == q["end"]), None)
        if idx is None or idx < 3:
            return None, [], "prior_period_missing"
        vals, terms = [], []
        for x in self.quarters[idx - 3: idx + 1]:
            v, t, r = self.quarter(qn, x, cutoff)
            if v is None:
                return None, terms + t, r or "term_missing"
            vals.append(v)
            terms += t
        return sum(vals), terms, None

    def prior(self, q, n=4):
        idx = next((k for k, x in enumerate(self.quarters) if x["end"] == q["end"]), None)
        if idx is None or idx < n:
            return None
        return self.quarters[idx - n]


def _ratio(num, den):
    if num is None or den is None:
        return None, "term_missing"
    if den <= 0:
        return None, "denominator_nonpositive"
    return Decimal(num) / Decimal(den), None


def group_measures(con, groups, as_of, observations=None):
    occ = model.occurrences_df(con)
    cals = model.calendars()
    rd = model.original_report_dates(con)
    as_of_d = dt.date.fromisoformat(as_of)
    out = []
    for g in groups:
        cal = cals[g]
        win = cal["window"]
        ws = dt.date.fromisoformat(win["window_start"])
        S = Series(occ, g, cal)
        quarters = [q for q in S.quarters if q["end"] >= ws and q["end"] <= as_of_d]
        for view in ("revised", "as_known"):
            for q in quarters:
                cutoff = as_of_d if view == "revised" else (rd.get((g, q["end"])) or as_of_d)
                if view == "as_known" and (g, q["end"]) not in rd:
                    if g == "SPCX" or q.get("in_progress"):
                        pass
                out += quarter_measures(S, g, q, cutoff, view, as_of)
            years = sorted({q["fy_end"] for q in quarters if q["fy_end"] and q["fy_end"] <= as_of_d})
            for fe in years:
                fqs = S.fy.get(fe, [])
                if not fqs or fqs[0]["start"] is None:
                    continue
                cutoff = as_of_d if view == "revised" else (rd.get((g, fe)) or as_of_d)
                out += annual_measures(S, g, fqs[0]["start"], fe, cutoff, view, as_of)
    return out


def quarter_measures(S, g, q, cutoff, view, as_of):
    ps, pe = q["start"], q["end"]
    out = []
    flags = {}
    capex, t_capex, r_capex = S.quarter("capex_cash", q, cutoff)
    cfo, t_cfo, r_cfo = S.quarter("cfo", q, cutoff)
    capex_fl = {"capex_definition": "productive_assets_incl_intangibles"} \
        if any(t.get("concept") == "us-gaap:PaymentsToAcquireProductiveAssets" for t in t_capex) else None
    # capex_cash
    out.append(cell("capex_cash", g, ps, pe, view, as_of, value=capex, unit="USD", terms=t_capex, flags=capex_fl,
                    status="computed" if capex is not None else "not_determinable", nd_reason=r_capex))
    # capex_to_cfo, sans et avec additions non monétaires
    v, r = _ratio(capex, cfo) if capex is not None and cfo is not None else (None, r_capex or r_cfo)
    out.append(cell("capex_to_cfo", g, ps, pe, view, as_of, term="without", value=v, terms=t_capex + t_cfo,
                    numerator=capex, denominator=cfo, status="computed" if v is not None else "not_determinable",
                    nd_reason=r, flags=capex_fl))
    adds = []
    miss = None
    for qn in ("rou_obtained_finance_lease", "vendor_financed_ppe_additions", "stock_paid_ppe_additions"):
        a, ta, ra = S.quarter(qn, q, cutoff)
        if a is None:
            miss = miss or (ra if ra != "concept_unresolved" else "term_missing")
        else:
            adds.append((a, ta))
    if miss is None and capex is not None and cfo is not None:
        num = capex + sum(a for a, _ in adds)
        v2, r2 = _ratio(num, cfo)
        out.append(cell("capex_to_cfo", g, ps, pe, view, as_of, term="with", value=v2, numerator=num,
                        denominator=cfo, terms=t_capex + t_cfo + [t for _, ts in adds for t in ts],
                        status="computed" if v2 is not None else "not_determinable", nd_reason=r2))
    else:
        out.append(cell("capex_to_cfo", g, ps, pe, view, as_of, term="with", status="not_determinable",
                        nd_reason=miss or r_capex or r_cfo, terms=t_capex + t_cfo))
    # flux disponibles
    if cfo is not None and capex is not None:
        fcf = cfo - capex
        out.append(cell("fcf_basic", g, ps, pe, view, as_of, value=fcf, unit="USD", terms=t_capex + t_cfo,
                        flags=capex_fl))
        flp, t_flp, r_flp = S.quarter("finance_lease_principal_payments", q, cutoff)
        if flp is not None:
            out.append(cell("fcf_after_finance_leases", g, ps, pe, view, as_of, value=fcf - flp, unit="USD",
                            terms=t_capex + t_cfo + t_flp))
        else:
            out.append(cell("fcf_after_finance_leases", g, ps, pe, view, as_of, status="not_determinable",
                            nd_reason="term_missing" if r_flp != "concept_unresolved" else "concept_unresolved",
                            terms=t_capex + t_cfo))
    else:
        r = r_cfo or r_capex
        for m in ("fcf_basic", "fcf_after_finance_leases"):
            out.append(cell(m, g, ps, pe, view, as_of, status="not_determinable", nd_reason=r,
                            terms=t_capex + t_cfo))
    # financement de contreparties nommées : texte hors tranche au premier passage (§11.1)
    out.append(cell("fcf_after_counterparty_financing", g, ps, pe, view, as_of, status="not_determinable",
                    nd_reason="not_processed", coverage="not_processed"))
    # délai de recouvrement : créances (et actifs de contrat) rapportés au revenu du trimestre
    rev, t_rev, r_rev = S.quarter("revenue_total", q, cutoff)
    rec = S.instant("accounts_receivable_net", pe, cutoff) or S.instant("receivables", pe, cutoff)
    days = (pe - ps).days + 1
    if rec and rev is not None and rev > 0:
        out.append(cell("receivables_collection_period", g, ps, pe, view, as_of, breakdown="receivables",
                        value=rec["value"] / rev * days, numerator=rec["value"], denominator=rev,
                        terms=[rec] + t_rev, unit="days"))
    else:
        out.append(cell("receivables_collection_period", g, ps, pe, view, as_of, breakdown="receivables",
                        status="not_determinable",
                        nd_reason="denominator_nonpositive" if (rev is not None and rev <= 0) else (r_rev or "term_missing")))
    ca = S.instant("contract_assets", pe, cutoff)
    if rec and ca and rev is not None and rev > 0:
        out.append(cell("receivables_collection_period", g, ps, pe, view, as_of,
                        breakdown="receivables_and_contract_assets",
                        value=(rec["value"] + ca["value"]) / rev * days, numerator=rec["value"] + ca["value"],
                        denominator=rev, terms=[rec, ca] + t_rev, unit="days"))
    else:
        out.append(cell("receivables_collection_period", g, ps, pe, view, as_of,
                        breakdown="receivables_and_contract_assets", status="not_determinable",
                        nd_reason="term_missing" if not ca else (r_rev or "term_missing")))
    # RPO
    rpo = S.instant("rpo_total", pe, cutoff)
    out.append(cell("rpo_total", g, None, pe, view, as_of, value=rpo["value"] if rpo else None, unit="USD",
                    terms=[rpo] if rpo else [], status="computed" if rpo else "not_determinable",
                    nd_reason=None if rpo else ("concept_unresolved" if not S.has("rpo_total") else "not_disclosed")))
    # croissance du revenu
    pq = S.prior(q, 4)
    if pq and rev is not None:
        prev, t_prev, r_prev = S.quarter("revenue_total", pq, cutoff)
        fl = {}
        if abs(((pe - ps).days) - ((pq["end"] - pq["start"]).days)) > 3:
            fl["unequal_period_length"] = True
        v, r = _ratio(rev - prev, prev) if prev is not None else (None, r_prev or "term_missing")
        out.append(cell("revenue_growth", g, ps, pe, view, as_of, term="yoy", value=v, numerator=rev - prev if prev is not None else None,
                        denominator=prev, terms=t_rev + t_prev, flags=fl or None,
                        status="computed" if v is not None else "not_determinable", nd_reason=r))
    else:
        out.append(cell("revenue_growth", g, ps, pe, view, as_of, term="yoy", status="not_determinable",
                        nd_reason=r_rev or "prior_period_missing", terms=t_rev))
    ttm, t_ttm, r_ttm = S.ttm("revenue_total", q, cutoff)
    pq4 = S.prior(q, 4)
    if ttm is not None and pq4:
        ttm0, t0, r0 = S.ttm("revenue_total", pq4, cutoff)
        v, r = _ratio(ttm - ttm0, ttm0) if ttm0 is not None else (None, r0 or "term_missing")
        out.append(cell("revenue_growth", g, ps, pe, view, as_of, term="ttm", value=v, terms=t_ttm + t0,
                        numerator=(ttm - ttm0) if ttm0 is not None else None, denominator=ttm0,
                        status="computed" if v is not None else "not_determinable", nd_reason=r))
    else:
        out.append(cell("revenue_growth", g, ps, pe, view, as_of, term="ttm", status="not_determinable",
                        nd_reason=r_ttm or "prior_period_missing"))
    # levier : dette et passifs locatifs ÷ (résultat opérationnel + dotations), douze mois glissants
    oi, t_oi, r_oi = S.ttm("operating_income", q, cutoff)
    da, t_da, r_da = S.ttm("depreciation_expense", q, cutoff)
    den = (oi + da) if (oi is not None and da is not None) else None
    debt_terms = [S.instant(x, pe, cutoff) for x in ("debt_current", "debt_noncurrent")]
    debt_alt = S.instant("debt_carrying_amount", pe, cutoff)
    stb = S.instant("short_term_borrowings", pe, cutoff)
    if all(debt_terms):
        debt = sum(t["value"] for t in debt_terms) + (stb["value"] if stb else 0)
        dts = debt_terms + ([stb] if stb else [])
    elif debt_alt:
        debt = debt_alt["value"] + (stb["value"] if stb else 0)
        dts = [debt_alt] + ([stb] if stb else [])
    else:
        debt, dts = None, []
    v, r = _ratio(debt, den) if den is not None else (None, r_oi or r_da or "term_missing")
    out.append(cell("lev_debt_and_leases_to_operating_income_plus_da", g, ps, pe, view, as_of, term="debt",
                    value=v, numerator=debt, denominator=den, terms=dts + t_oi + t_da,
                    status="computed" if v is not None else "not_determinable",
                    nd_reason=r if v is None else None))
    lease_terms = [S.instant(x, pe, cutoff) for x in ("operating_lease_liability_current",
                                                      "operating_lease_liability_noncurrent",
                                                      "finance_lease_liability_current",
                                                      "finance_lease_liability_noncurrent")]
    have = [t for t in lease_terms if t]
    if have and len(have) == len([x for x in ("operating_lease_liability_current", "operating_lease_liability_noncurrent",
                                              "finance_lease_liability_current", "finance_lease_liability_noncurrent")
                                  if S.has(x)]):
        leases = sum(t["value"] for t in have)
        v, r = _ratio(leases, den) if den is not None else (None, r_oi or r_da or "term_missing")
        out.append(cell("lev_debt_and_leases_to_operating_income_plus_da", g, ps, pe, view, as_of, term="leases",
                        value=v, numerator=leases, denominator=den, terms=have + t_oi + t_da,
                        status="computed" if v is not None else "not_determinable", nd_reason=r if v is None else None))
    else:
        out.append(cell("lev_debt_and_leases_to_operating_income_plus_da", g, ps, pe, view, as_of, term="leases",
                        status="not_determinable", nd_reason="term_missing"))
    return out


def annual_measures(S, g, fs, fe, cutoff, view, as_of):
    out = []
    # échéances de principal ÷ trésorerie
    cash = S.instant("cash_and_equivalents", fe, cutoff)
    d12 = S.instant("debt_principal_due_12m", fe, cutoff)
    d24 = S.instant("debt_principal_due_year2", fe, cutoff)
    for term, terms in (("horizon_12m", [d12]), ("horizon_24m", [d12, d24])):
        if all(terms) and cash:
            num = sum(t["value"] for t in terms)
            v, r = _ratio(num, cash["value"])
            out.append(cell("liq_principal_due_to_cash", g, fs, fe, view, as_of, term=term, value=v, numerator=num,
                            denominator=cash["value"], terms=terms + [cash],
                            status="computed" if v is not None else "not_determinable", nd_reason=r))
        else:
            out.append(cell("liq_principal_due_to_cash", g, fs, fe, view, as_of, term=term, status="not_determinable",
                            nd_reason="term_missing" if S.has("debt_principal_due_12m") else "concept_unresolved"))
    # échéancier des obligations d'achat (matrice d'exposition, flux non actualisés)
    buckets = [("total", "purchase_obligation_total"), ("remainder_of_fiscal_year", "purchase_obligation_remainder"),
               ("within_12m", "purchase_obligation_12m"), ("year_2", "purchase_obligation_year2"),
               ("year_3", "purchase_obligation_year3"), ("year_4", "purchase_obligation_year4"),
               ("year_5", "purchase_obligation_year5"), ("after_year_5", "purchase_obligation_after5")]
    for label, qn in buckets:
        t = S.instant(qn, fe, cutoff)
        key = f"contractual_outflows/undiscounted/purchase_obligation/{label}"
        if t:
            out.append(cell("exposure_matrix", g, None, fe, view, as_of, breakdown=key, value=t["value"],
                            unit="USD", terms=[t]))
        elif label == "total":
            out.append(cell("exposure_matrix", g, None, fe, view, as_of, breakdown=key, status="not_determinable",
                            nd_reason="not_disclosed" if S.has(qn) else "concept_unresolved"))
    # pont des baux non commencés : ouverture et clôture balisées par dimension ; flux non publiés
    for term in ("opening", "additions", "commenced", "closing"):
        out.append(cell("lease_not_commenced_bridge", g, fs, fe, view, as_of, term=term, status="not_determinable",
                        nd_reason="concept_unresolved" if term in ("opening", "closing") else "not_disclosed"))
    # additions non monétaires d'immobilisations (§5.5)
    for m, qn in (("finance_lease_additions", "rou_obtained_finance_lease"),
                  ("vendor_financed_additions", "vendor_financed_ppe_additions"),
                  ("stock_paid_additions", "stock_paid_ppe_additions")):
        t = S.duration(qn, fs, fe, cutoff)
        out.append(cell(m, g, fs, fe, view, as_of, value=t["value"] if t else None, unit="USD",
                        terms=[t] if t else [], status="computed" if t else "not_determinable",
                        nd_reason=None if t else ("not_disclosed" if S.has(qn) else "concept_unresolved")))
    # pont de résultat : gains de réévaluation et dépréciations d'investissements
    for term, qn in (("investment_gain_loss", "investment_gain_loss"), ("investment_impairment", "investment_impairment")):
        t = S.duration(qn, fs, fe, cutoff)
        fl = {"price_setting_participation": "unknown"} if term == "investment_gain_loss" else None
        out.append(cell("earnings_bridge_pretax", g, fs, fe, view, as_of, term=term,
                        value=t["value"] if t else None, unit="USD", terms=[t] if t else [], flags=fl,
                        status="computed" if t else "not_determinable",
                        nd_reason=None if t else ("not_disclosed" if S.has(qn) else "concept_unresolved")))
    return out
