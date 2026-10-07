"""Univers attendu des cellules de rang 1 (§7.5), engendré par règle, sans regarder les
données : depuis les obligations de publication (ASC 842, 280, 460, 810, 405-50 et 606
pour les exercices ; Reg S-X article 10 et ASC 270 pour les périodes intermédiaires).

Chaque cellule attendue a sa ligne et un coverage_state ; not_applicable exige une
pièce. Les cellules par paire s'engendrent en phase 3, pour chaque paire à financement
documenté (§3.6), par la même règle.
"""
import datetime as dt

# mesure -> (terms, fréquence de l'obligation, fondement)
GROUP_TIER1 = {
    "capex_to_cfo": (["with", "without"], "quarter", "ASC 230 ; Reg S-X 10-01 (tableau des flux intermédiaire)"),
    "capex_cash": (["none"], "quarter", "ASC 230"),
    "finance_lease_additions": (["none"], "fiscal_year", "ASC 842-20-50-4(g)"),
    "vendor_financed_additions": (["none"], "fiscal_year", "ASC 230-10-50-3"),
    "stock_paid_additions": (["none"], "fiscal_year", "ASC 230-10-50-3"),
    "fcf_basic": (["none"], "quarter", "ASC 230"),
    "fcf_after_finance_leases": (["none"], "quarter", "ASC 230 ; ASC 842-20-50-4"),
    "fcf_after_counterparty_financing": (["none"], "quarter", "ASC 230"),
    "lease_not_commenced_bridge": (["opening", "additions", "commenced", "closing"], "fiscal_year", "ASC 842-20-50-3(b)"),
    "exposure_matrix": (["none"], "fiscal_year", "ASC 440-10-50-4 (obligations d'achat)"),
    "receivables_collection_period": (["none"], "quarter", "ASC 310 ; ASC 606-10-50-8"),
    "rpo_total": (["none"], "quarter", "ASC 606-10-50-13 ; ASC 270"),
    "revenue_growth": (["yoy", "ttm"], "quarter", "ASC 606 ; ASC 270"),
    "depreciation_life_published": (["lower", "upper", "point"], "fiscal_year", "ASC 360-10-50-1"),
    "earnings_bridge_pretax": (["investment_gain_loss", "investment_impairment"], "fiscal_year", "ASC 321-10-50 ; ASC 323-10-50"),
    "liq_principal_due_to_cash": (["horizon_12m", "horizon_24m"], "fiscal_year", "ASC 470-10-50-1"),
    "lev_debt_and_leases_to_operating_income_plus_da": (["debt", "leases"], "quarter", "ASC 470 ; ASC 842 ; ASC 270"),
    "sig_covenant_events": (["none"], "quarter", "Reg S-K Item 303 ; 8-K items 1.01, 2.04"),
    "sig_late_filing": (["none"], "quarter", "Rule 12b-25"),
    "sig_distress_8k_items": (["none"], "quarter", "Form 8-K items 1.03, 2.04, 2.06, 3.01"),
    "sig_auditor_change_or_nonreliance": (["none"], "quarter", "Form 8-K items 4.01, 4.02"),
    "sig_material_weakness": (["none"], "quarter", "Reg S-K Item 308 ; 10-K Item 9A ; 10-Q Part I Item 4"),
    "sig_going_concern": (["none"], "quarter", "ASC 205-40-50"),
    "named_edge_coverage": (["named", "anonymous", "residual"], "fiscal_year", "ASC 280-10-50-42"),
    "customer_concentration_anonymous": (["none"], "fiscal_year", "ASC 280-10-50-42 ; ASC 275-10-50-18"),
    "visible_pairs_count": (["none"], "fiscal_year", "§3.6"),
}
EVENTS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"]


# Début de l'obligation de publier, par fréquence (introductions en bourse récentes) :
# trimestres à partir du premier 10-Q ; exercices présentés par le document d'enregistrement
# (Reg S-X 3-01, 3-02). Avant, la cellule est not_applicable avec sa pièce.
REPORTING_START = {
    "SPCX": {"quarter": ("2026-04-01", "EFFECT 9999999995-26-001968 du 2026-06-11 ; premier 10-Q 0001628280-26-052535 (T2 2026)"),
             "fiscal_year": ("2023-01-01", "424B4 0001628280-26-042639 : exercices 2023 à 2025 présentés (Reg S-X 3-02)")},
    "CRWV": {"quarter": ("2025-01-01", "424B4 0001193125-25-067651 du 2025-03-31 ; premier 10-Q pour le T1 2025"),
             "fiscal_year": ("2022-01-01", "424B4 0001193125-25-067651 : exercices 2022 à 2024 présentés (Reg S-X 3-02)")},
}


def generate(calendars, as_of, reporting_start=REPORTING_START):
    """calendars : {groupe: {years, window}} de phase0.json ; reporting_start :
    {groupe: {fréquence: (date, pièce)}} début de l'obligation de publication."""
    rows = []
    as_of_d = dt.date.fromisoformat(as_of)
    for g, cal in calendars.items():
        win = cal["window"]
        if not win:
            continue
        ws = dt.date.fromisoformat(win["window_start"])
        rs_all = (reporting_start or {}).get(g, {})
        quarters, years = [], []
        for y in cal["years"]:
            fe = dt.date.fromisoformat(y["fy_end"]) if y.get("fy_end") else None
            start = dt.date.fromisoformat(y["fy_start"]) if y.get("fy_start") else None
            for qe in y["q_ends"]:
                qe_d = dt.date.fromisoformat(qe)
                if qe_d >= ws and qe_d <= as_of_d:
                    quarters.append((start, qe_d, fe))
                start = qe_d + dt.timedelta(days=1)
            if fe and fe >= ws and fe <= as_of_d and not y.get("in_progress"):
                years.append((dt.date.fromisoformat(y["fy_start"]) if y.get("fy_start") else None, fe))
        for m, (terms, freq, basis) in GROUP_TIER1.items():
            periods = quarters if freq == "quarter" else [(s, e, e) for s, e in years]
            rs = rs_all.get(freq)
            for (ps, pe, _fe) in periods:
                for t in terms:
                    state, evidence = "unknown", None
                    if rs and pe < dt.date.fromisoformat(rs[0]):
                        state, evidence = "not_applicable", rs[1]
                    rows.append({"measure": m, "subject": g, "counterparty": "none",
                                 "period_start": ps.isoformat() if ps else "none", "period_end": pe.isoformat(),
                                 "term": t, "breakdown_key": "none", "period_kind": freq,
                                 "basis": basis, "expected_state": state, "not_applicable_evidence": evidence})
        rs = rs_all.get("quarter")
        for (ps, pe, _fe) in quarters:
            for ev in EVENTS:
                state, evidence = "unknown", None
                if rs and pe < dt.date.fromisoformat(rs[0]):
                    state, evidence = "not_applicable", rs[1]
                rows.append({"measure": "fragility_event", "subject": g, "counterparty": "none",
                             "period_start": ps.isoformat() if ps else "none", "period_end": pe.isoformat(),
                             "term": "none", "breakdown_key": ev, "period_kind": "quarter",
                             "basis": "annexe F", "expected_state": state, "not_applicable_evidence": evidence})
    return rows
