"""Grandeurs du modèle : correspondance de concepts, vues et séries (§7.2, §7.3, §8.3).

La correspondance se fixe par règle, avant les contrôles : un concept n'est retenu pour
une grandeur que s'il figure dans la linkbase de présentation du déposant pour l'état
concerné et si sa définition correspond (pour un concept standard, la liste de
candidats est fixée d'avance d'après les définitions us-gaap ; pour une extension,
seulement si elle est l'enfant d'un concept déjà rattaché et cite le même paragraphe
ASC). Le premier candidat présent l'emporte. Après un mismatch, la correspondance ne
change que sur une pièce nouvelle (decisions.md).
"""
import datetime as dt
import json
from decimal import Decimal

from . import config

BS = {"balance_sheet"}
IS = {"income_statement", "comprehensive_income"}
CF = {"cash_flow"}
NOTES = {"note_details", "note_tables", "note", "note_policies"}
ANY = BS | IS | CF | NOTES | {"statement_other", "equity_statement", "statement_parenthetical"}

# grandeur -> (candidats sans version, états admis, type de période)
# Ancrées : config.yaml (concept_anchors, concept_anchors_to_verify).
# Non ancrées : candidats standard dont la définition correspond (consignés dans concepts.csv).
STATEMENT_OF = {
    "revenue_total": IS, "net_income": IS, "operating_income": IS, "pretax_income_continuing": IS,
    "total_assets": BS, "current_assets": BS, "total_liabilities": BS, "current_liabilities": BS,
    "temporary_equity": BS, "equity_including_nci": BS, "cash_and_equivalents": BS,
    "restricted_cash_current": BS | NOTES, "restricted_cash_noncurrent": BS | NOTES,
    "cash_and_restricted_cash_total": CF | BS | NOTES, "cfo": CF, "cfi": CF, "cff": CF,
    "capex_cash": CF, "unpaid_capex": CF | NOTES, "eps_diluted": IS,
    "diluted_shares_weighted": IS | NOTES, "net_income_to_common_diluted": IS | NOTES,
    "rpo_total": NOTES, "contract_liabilities": BS | NOTES,
    "operating_lease_liability_current": BS | NOTES, "operating_lease_liability_noncurrent": BS | NOTES,
    "operating_lease_payments_undiscounted": NOTES, "operating_lease_imputed_interest": NOTES,
    "finance_lease_liability_current": BS | NOTES, "finance_lease_liability_noncurrent": BS | NOTES,
    "finance_lease_payments_undiscounted": NOTES, "finance_lease_imputed_interest": NOTES,
    "capitalized_interest": NOTES | CF | IS, "short_term_investments": BS,
    "undrawn_committed_facilities": NOTES, "dividends_paid": CF, "dividends_declared": NOTES | {"equity_statement"},
    "profit_including_nci": IS | CF, "vendor_financed_ppe_additions": CF | NOTES,
    "stock_paid_ppe_additions": CF | NOTES, "debt_proceeds": CF, "debt_repayments": CF,
    "rou_obtained_finance_lease": NOTES | CF, "rou_obtained_operating_lease": NOTES | CF,
    "finance_lease_principal_payments": CF | NOTES, "pik_interest": CF | NOTES | IS,
    "equity_method_income": IS | NOTES, "dilution_gain": IS | NOTES | CF,
    "investment_gain_loss": NOTES | IS | CF, "investment_impairment": NOTES | IS | CF,
    "gross_profit": IS, "cost_of_revenue": IS, "receivables": BS, "inventories": BS,
    "accounts_payable": BS, "contract_liabilities_current": BS | NOTES,
}

UNANCHORED = {
    "income_tax_expense": (["us-gaap:IncomeTaxExpenseBenefit"], IS),
    "effective_tax_rate": (["us-gaap:EffectiveIncomeTaxRateContinuingOperations"], NOTES),
    "retained_earnings": (["us-gaap:RetainedEarningsAccumulatedDeficit"], BS),
    "fx_effect_on_cash": (["us-gaap:EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                           "us-gaap:EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations"], CF),
    "depreciation_expense": (["us-gaap:DepreciationDepletionAndAmortization",
                              "us-gaap:DepreciationAmortizationAndAccretionNet",
                              "us-gaap:DepreciationAndAmortization", "us-gaap:Depreciation"], CF),
    "gross_depreciable_ppe": (["us-gaap:PropertyPlantAndEquipmentGross"], NOTES | BS),
    "land": (["us-gaap:Land"], NOTES | BS),
    "construction_in_progress": (["us-gaap:ConstructionInProgressGross"], NOTES | BS),
    "debt_carrying_amount": (["us-gaap:LongTermDebt", "us-gaap:DebtLongtermAndShorttermCombinedAmount"], NOTES | BS),
    "debt_current": (["us-gaap:LongTermDebtCurrent", "us-gaap:DebtCurrent"], BS | NOTES),
    "debt_noncurrent": (["us-gaap:LongTermDebtNoncurrent"], BS | NOTES),
    "short_term_borrowings": (["us-gaap:ShortTermBorrowings", "us-gaap:CommercialPaper"], BS | NOTES),
    "debt_principal_due_12m": (["us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths"], NOTES),
    "debt_principal_due_year2": (["us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo"], NOTES),
    "contract_assets": (["us-gaap:ContractWithCustomerAssetNetCurrent", "us-gaap:ContractWithCustomerAssetNet"], BS | NOTES),
    "sbc_expense": (["us-gaap:ShareBasedCompensation", "us-gaap:AllocatedShareBasedCompensationExpense"], CF | NOTES),
    "interest_expense": (["us-gaap:InterestExpense", "us-gaap:InterestExpenseNonoperating",
                          "us-gaap:InterestExpenseDebt", "us-gaap:InterestAndDebtExpense"], IS | NOTES),
    "interest_paid": (["us-gaap:InterestPaidNet", "us-gaap:InterestPaid"], CF | NOTES),
    "purchase_obligation_total": (["us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount",
                                   "us-gaap:PurchaseObligation"], NOTES),
    "purchase_obligation_12m": (["us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceOnFirstAnniversary",
                                 "us-gaap:UnrecordedUnconditionalPurchaseObligationDueInNextRollingTwelveMonths",
                                 "us-gaap:PurchaseObligationDueInNextTwelveMonths"], NOTES),
    "purchase_obligation_year2": (["us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceOnSecondAnniversary",
                                   "us-gaap:UnrecordedUnconditionalPurchaseObligationDueInRollingYearTwo",
                                   "us-gaap:PurchaseObligationDueInSecondYear"], NOTES),
    "purchase_obligation_year3": (["us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceOnThirdAnniversary",
                                   "us-gaap:UnrecordedUnconditionalPurchaseObligationDueInRollingYearThree",
                                   "us-gaap:PurchaseObligationDueInThirdYear"], NOTES),
    "purchase_obligation_year4": (["us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceOnFourthAnniversary",
                                   "us-gaap:UnrecordedUnconditionalPurchaseObligationDueInRollingYearFour",
                                   "us-gaap:PurchaseObligationDueInFourthYear"], NOTES),
    "purchase_obligation_year5": (["us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceOnFifthAnniversary",
                                   "us-gaap:UnrecordedUnconditionalPurchaseObligationDueInRollingYearFive",
                                   "us-gaap:PurchaseObligationDueInFifthYear"], NOTES),
    "purchase_obligation_after5": (["us-gaap:UnrecordedUnconditionalPurchaseObligationDueAfterFiveYears",
                                    "us-gaap:UnrecordedUnconditionalPurchaseObligationDueInRollingAfterYearFive",
                                    "us-gaap:PurchaseObligationDueAfterFifthYear"], NOTES),
    "purchase_obligation_remainder": (["us-gaap:UnrecordedUnconditionalPurchaseObligationDueInRemainderOfFiscalYear",
                                       "us-gaap:PurchaseObligationFutureMinimumPaymentsRemainderOfFiscalYear"], NOTES),
    "useful_life": (["us-gaap:PropertyPlantAndEquipmentUsefulLife"], NOTES),
    "concentration_pct": (["us-gaap:ConcentrationRiskPercentage1"], NOTES),
    "rpo_pct_expected": (["us-gaap:RevenueRemainingPerformanceObligationPercentage"], NOTES),
    "accounts_receivable_net": (["us-gaap:AccountsReceivableNetCurrent", "us-gaap:ReceivablesNetCurrent"], BS),
    "cash_equivalents_and_marketable": (["us-gaap:CashCashEquivalentsAndShortTermInvestments"], BS),
    "marketable_securities_current": (["us-gaap:MarketableSecuritiesCurrent", "us-gaap:AvailableForSaleSecuritiesDebtSecuritiesCurrent"], BS),
    "accumulated_deficit": (["us-gaap:RetainedEarningsAccumulatedDeficit"], BS),
    "stockholders_equity": (["us-gaap:StockholdersEquity"], BS),
    "doc_error_correction_flag": (["dei:DocumentFinStmtErrorCorrectionFlag"], {"cover"}),
}

DURATION_HINT = {  # grandeurs instantanées ; les autres sont des flux
    "total_assets", "current_assets", "total_liabilities", "current_liabilities", "temporary_equity",
    "equity_including_nci", "cash_and_equivalents", "restricted_cash_current", "restricted_cash_noncurrent",
    "cash_and_restricted_cash_total", "rpo_total", "contract_liabilities",
    "operating_lease_liability_current", "operating_lease_liability_noncurrent",
    "operating_lease_payments_undiscounted", "operating_lease_imputed_interest",
    "finance_lease_liability_current", "finance_lease_liability_noncurrent",
    "finance_lease_payments_undiscounted", "finance_lease_imputed_interest", "short_term_investments",
    "undrawn_committed_facilities", "receivables", "inventories", "accounts_payable",
    "contract_liabilities_current", "retained_earnings", "gross_depreciable_ppe", "land",
    "construction_in_progress", "debt_carrying_amount", "debt_current", "debt_noncurrent",
    "short_term_borrowings", "debt_principal_due_12m", "debt_principal_due_year2", "contract_assets",
    "purchase_obligation_total", "purchase_obligation_12m", "purchase_obligation_year2",
    "purchase_obligation_year3", "purchase_obligation_year4", "purchase_obligation_year5",
    "purchase_obligation_after5", "purchase_obligation_remainder", "accounts_receivable_net",
    "cash_equivalents_and_marketable", "marketable_securities_current", "accumulated_deficit",
    "stockholders_equity",
}


def quantity_definitions(cfg=None):
    cfg = cfg or config.load()
    q = {}
    for name, cands in cfg["concept_anchors"].items():
        q[name] = {"candidates": [f"us-gaap:{c}" for c in cands], "statements": STATEMENT_OF.get(name, ANY),
                   "anchored": True}
    for name, cands in cfg["concept_anchors_to_verify"].items():
        if name in ("segment_axis", "going_concern_text_block"):
            continue
        q[name] = {"candidates": [f"us-gaap:{c}" for c in cands], "statements": STATEMENT_OF.get(name, ANY),
                   "anchored": True, "to_verify": True}
    for name, (cands, st) in UNANCHORED.items():
        q.setdefault(name, {"candidates": cands, "statements": st, "anchored": False})
    for name, d in q.items():
        d["instant"] = name in DURATION_HINT
    return q


def map_concepts(con, cfg=None):
    """Correspondance par dépôt : pour chaque groupe, grandeur et dépôt dont la linkbase
    a été lue, le premier candidat présent dans un rôle de l'état concerné."""
    qdefs = quantity_definitions(cfg)
    present = con.execute("""
        SELECT accession, group_id, statement_kind, concept FROM (
          SELECT accession, group_id, statement_kind, child AS concept FROM pres
          UNION SELECT accession, group_id, statement_kind, parent AS concept FROM pres)
    """).fetchall()
    by_acc = {}
    for acc, g, kind, c in present:
        by_acc.setdefault((acc, g), {}).setdefault(c, set()).add(kind)
    rows = []
    for (acc, g), concepts in by_acc.items():
        for qn, d in qdefs.items():
            chosen = None
            for cand in d["candidates"]:
                kinds = concepts.get(cand)
                if kinds and (kinds & d["statements"]):
                    chosen = (cand, sorted(kinds & d["statements"])[0])
                    break
            if chosen:
                rows.append((g, qn, acc, chosen[0], "anchor_first_present" if d["anchored"]
                             else "definition_first_present", chosen[1]))
    con.execute("DROP TABLE IF EXISTS concept_map")
    con.execute("""CREATE TABLE concept_map (group_id VARCHAR, quantity VARCHAR, accession VARCHAR,
                   concept VARCHAR, rule VARCHAR, statement_kind VARCHAR)""")
    if rows:
        con.executemany("INSERT INTO concept_map VALUES (?,?,?,?,?,?)", rows)
    return len(rows)


def occurrences(con):
    """Occurrences admissibles des grandeurs : faits non dimensionnés, périmètre publié,
    rattachés par la correspondance du dépôt qui les porte."""
    con.execute("DROP VIEW IF EXISTS q_occ")
    con.execute("""
      CREATE VIEW q_occ AS
      SELECT m.quantity, f.group_id, f.fact_key, f.accession, f.form, f.concept, f.period_type,
             f.period_start, f.period_end, f.unit, f.value, f.decimals, f.decimals_inf,
             f.precision_known, f.knowledge_date, f.acceptance_datetime, f.source,
             f.doc_rank, f.occ_rank, f.tier, f.is_tagged, f.conflict
      FROM facts f JOIN concept_map m
        ON m.accession = f.accession AND m.concept = f.concept AND m.group_id = f.group_id
      WHERE f.n_dims = 0 AND f.reporting_scope = 'as_reported' AND f.value IS NOT NULL
        AND NOT coalesce(f.is_nil, false)
    """)


def select_view(con, view, as_of, knowledge_cutoff=None):
    """Une valeur par (grandeur, groupe, période, unité) : la dernière occurrence selon
    l'ordre total (acceptation, accession, rang du document, rang de l'occurrence),
    connue à la date de coupure (as_known) ou à as_of (revised). Les instances priment
    sur companyfacts pour une même accession (decimals connu)."""
    cutoff = knowledge_cutoff or as_of
    return con.execute(f"""
      SELECT * FROM (
        SELECT *, row_number() OVER (
          PARTITION BY quantity, group_id, period_type, period_start, period_end, unit
          ORDER BY acceptance_datetime DESC NULLS LAST, accession DESC,
                   CASE source WHEN 'instance' THEN 0 ELSE 1 END, doc_rank DESC NULLS LAST,
                   CASE WHEN decimals_inf THEN 99 ELSE coalesce(decimals, -99) END DESC,
                   occ_rank DESC NULLS LAST, fact_key DESC) AS rn
        FROM q_occ WHERE knowledge_date <= DATE '{cutoff}') WHERE rn = 1
    """).fetchdf()


def _close(a, b, tol=3):
    if a is None or b is None:
        return a is None and b is None
    return abs((a - b).days) <= tol


def derive_quarters(values, quarters_list, instant):
    """values : liste de dicts (period_start, period_end, value, fact_key, accession,
    knowledge_date). Renvoie une valeur par trimestre fiscal avec méthode et lignage.

    Un trimestre obtenu par différence de cumuls garde les clés de ses termes (§7.3)."""
    def find(start, end):
        for v in values:
            ps = v["period_start"]
            pe = v["period_end"]
            if _close(pe, end) and (instant or _close(ps, start)):
                return v
        return None

    out = []
    by_fy = {}
    for q in quarters_list:
        by_fy.setdefault(q["fy_end"], []).append(q)
    for fy_end, qs in by_fy.items():
        fy_start = qs[0]["start"]
        for i, q in enumerate(qs):
            rec = {"start": q["start"], "end": q["end"], "fy_end": fy_end, "q": q["q"]}
            if instant:
                v = find(None, q["end"])
                rec.update(_ok(v, "direct") if v else _nd("not_disclosed"))
                out.append(rec)
                continue
            v = find(q["start"], q["end"])
            if v:
                rec.update(_ok(v, "direct"))
            elif i > 0 and fy_start is not None:
                cur = find(fy_start, q["end"])
                prev = find(fy_start, qs[i - 1]["end"]) if i > 1 else find(qs[0]["start"], qs[0]["end"])
                if cur and prev:
                    rec.update({"value": Decimal(cur["value"]) - Decimal(prev["value"]),
                                "method": "ytd_difference", "status": "computed",
                                "lineage": [cur["fact_key"], prev["fact_key"]],
                                "accessions": sorted({cur["accession"], prev["accession"]}),
                                "knowledge_date": max(cur["knowledge_date"], prev["knowledge_date"]),
                                "terms": [cur, prev]})
                else:
                    rec.update(_nd("term_missing"))
            else:
                rec.update(_nd("not_disclosed"))
            out.append(rec)
    return out


def _ok(v, method):
    return {"value": Decimal(v["value"]), "method": method, "status": "computed",
            "lineage": [v["fact_key"]], "accessions": [v["accession"]],
            "knowledge_date": v["knowledge_date"], "terms": [v]}


def _nd(reason):
    return {"value": None, "method": None, "status": "not_determinable", "nd_reason": reason,
            "lineage": [], "accessions": [], "knowledge_date": None, "terms": []}
