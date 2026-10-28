"""D-0082 : lignes de dette plus étroites que leur grandeur, retenues seules ; dotations du levier (ligne globale, ou
dotation des immobilisations plus amortissement des incorporels) ; durée implicite sur la seule dotation des
immobilisations ; révision jugée à la tolérance d'arrondi ; StockIssued1 retiré des additions payées en titres.

Lancement : python3 -m unittest tests.test_d0082 -v
"""
import datetime as dt
import json
import unittest
from decimal import Decimal

import duckdb
import pandas as pd

from pipeline import model, quantities, rank2
from pipeline.measures import Series, annual_measures, quarter_measures

D = dt.date.fromisoformat
AS_OF = "2026-10-27"


def quarters(*fys):
    out = []
    for y in fys:
        for s, e in (("01-01", "03-31"), ("04-01", "06-30"), ("07-01", "09-30"), ("10-01", "12-31")):
            out.append({"start": D(f"{y}-{s}"), "end": D(f"{y}-{e}"), "fy_end": D(f"{y}-12-31")})
    return out


def series(rows, fys=(2025,)):
    """rows : (grandeur, concept, début, fin, valeur, accession, date de dépôt[, decimals])."""
    recs = []
    for i, r in enumerate(rows):
        qn, concept, s, e, v, acc, filed = r[:7]
        dec = r[7] if len(r) > 7 else -6
        recs.append({"group_id": "G", "quantity": qn, "concept": concept,
                     "period_type": "instant" if s is None else "duration",
                     "period_start": D(s) if s else None, "period_end": D(e), "value": float(v),
                     "fact_key": f"f{i}", "accession": acc, "knowledge_date": D(filed), "tier": "A",
                     "decimals": dec, "decimals_inf": False, "precision_known": True, "is_tagged": True,
                     "order_key": (filed, acc, 1, dec if dec is not None else -99, 0)})
    return Series(pd.DataFrame(recs), "G", {"quarters": quarters(*fys)})


def mapping(lines):
    """Correspondance d'un dépôt dont la linkbase de présentation porte `lines` : (type d'état, concept)."""
    con = duckdb.connect()
    con.execute("""CREATE TABLE pres (accession VARCHAR, group_id VARCHAR, statement_kind VARCHAR, parent VARCHAR,
                                      child VARCHAR)""")
    for kind, c in lines:
        con.execute("INSERT INTO pres VALUES ('a', 'G', ?, 'us-gaap:LiabilitiesAbstract', ?)", [kind, c])
    quantities.map_concepts(con)
    return {q: (c, r) for q, c, r in con.execute("SELECT quantity, concept, rule FROM concept_map").fetchall()}


BS = "balance_sheet"


class SoleDebtLine(unittest.TestCase):
    """Point 1 : billets, et billets et emprunts, retenus comme seule ligne de dette de leur position au bilan."""

    def test_oracle(self):
        m = mapping([(BS, "us-gaap:NotesPayableCurrent"), (BS, "us-gaap:LongTermNotesAndLoans")])
        self.assertEqual(m["debt_current"], ("us-gaap:NotesPayableCurrent", "definition_sole_debt_line"))
        self.assertEqual(m["debt_noncurrent"], ("us-gaap:LongTermNotesAndLoans", "definition_sole_debt_line"))

    def test_another_line_of_the_same_position_rules_it_out(self):
        # Galaxy : deux lignes courantes ; la ligne non courante reste seule de sa position
        m = mapping([(BS, "us-gaap:NotesPayableCurrent"), (BS, "us-gaap:LoansPayableCurrent"),
                     (BS, "us-gaap:LongTermNotesPayable")])
        self.assertNotIn("debt_current", m)
        self.assertEqual(m["debt_noncurrent"][0], "us-gaap:LongTermNotesPayable")

    def test_two_noncurrent_candidates_rule_each_other_out(self):
        m = mapping([(BS, "us-gaap:LongTermNotesAndLoans"), (BS, "us-gaap:LongTermNotesPayable")])
        self.assertNotIn("debt_noncurrent", m)

    def test_extension_debt_line_rules_it_out(self):
        m = mapping([(BS, "us-gaap:NotesPayableCurrent"), (BS, "x:RecourseDebtNonCurrent")])
        self.assertNotIn("debt_current", m)

    def test_short_term_borrowings_and_other_extensions_do_not(self):
        m = mapping([(BS, "us-gaap:NotesPayableCurrent"), (BS, "us-gaap:ShortTermBorrowings"),
                     (BS, "x:DebtSecuritiesMember"), (BS, "x:FinanceLeaseLiabilityAndFinancingObligationCurrent")])
        self.assertEqual(m["debt_current"][0], "us-gaap:NotesPayableCurrent")

    def test_earlier_candidate_still_first(self):
        m = mapping([("note_details", "us-gaap:LongTermDebtCurrent"), (BS, "us-gaap:NotesPayableCurrent")])
        self.assertEqual(m["debt_current"], ("us-gaap:LongTermDebtCurrent", "definition_first_present"))

    def test_notes_payable_current_gets_short_term_borrowings(self):
        rows = []
        for q in quarters(2025):
            s, e = q["start"].isoformat(), q["end"].isoformat()
            rows += [("operating_income", "us-gaap:OperatingIncomeLoss", s, e, 1000, "q" + e, e),
                     ("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", s, e, 250, "q" + e, e)]
        rows += [("debt_current", "us-gaap:NotesPayableCurrent", None, "2025-12-31", 7625, "k", "2026-02-01"),
                 ("debt_noncurrent", "us-gaap:LongTermNotesAndLoans", None, "2025-12-31", 117712, "k", "2026-02-01"),
                 ("short_term_borrowings", "us-gaap:CommercialPaper", None, "2025-12-31", 663, "k", "2026-02-01")]
        S = series(rows)
        out = quarter_measures(S, "G", S.quarters[-1], D(AS_OF), "revised", AS_OF)
        c = next(x for x in out if x["measure"] == "lev_debt_and_leases_to_operating_income_plus_da" and x["term"] == "debt")
        self.assertEqual((c["numerator"], c["denominator"], c["flags"]), (Decimal(126000), Decimal(5000), None))


class DepreciationAndAmortization(unittest.TestCase):
    """Point 2 : dotations du trimestre, ligne globale ou dotation des immobilisations plus amortissement des incorporels."""

    def rows(self, total=None, dep=None, amort=None, skip_amort=()):
        out = []
        for q in quarters(2025):
            s, e = q["start"].isoformat(), q["end"].isoformat()
            out.append(("operating_income", "us-gaap:OperatingIncomeLoss", s, e, 1000, "q" + e, e))
            if total is not None:
                out.append(("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", s, e, total, "q" + e, e))
            if dep is not None:
                out.append(("ppe_depreciation", "us-gaap:Depreciation", s, e, dep, "q" + e, e))
            if amort is not None and e not in skip_amort:
                out.append(("intangible_amortization", "us-gaap:AmortizationOfIntangibleAssets", s, e, amort, "q" + e, e))
        return out

    def da(self, rows):
        S = series(rows)
        return S.da(S.quarters[-1], D(AS_OF)), S.da_ttm(S.quarters[-1], D(AS_OF))

    def lev_flags(self, rows):
        S = series(rows + [("debt_current", "us-gaap:LongTermDebtCurrent", None, "2025-12-31", 100, "k", "2026-02-01"),
                           ("debt_noncurrent", "us-gaap:LongTermDebtNoncurrent", None, "2025-12-31", 900, "k", "2026-02-01")])
        out = quarter_measures(S, "G", S.quarters[-1], D(AS_OF), "revised", AS_OF)
        c = next(x for x in out if x["measure"] == "lev_debt_and_leases_to_operating_income_plus_da" and x["term"] == "debt")
        return c["denominator"], json.loads(c["flags"]) if c["flags"] else None

    def test_total_line_first(self):
        (v, _, r, b), (ttm, _, _, bases) = self.da(self.rows(total=300, dep=200, amort=50))
        self.assertEqual((v, r, b, ttm, bases), (Decimal(300), None, "total_line", Decimal(1200), {"total_line"}))
        self.assertEqual(self.lev_flags(self.rows(total=300, dep=200, amort=50)), (Decimal(5200), None))

    def test_depreciation_plus_amortization(self):
        (v, terms, r, b), (ttm, _, _, _) = self.da(self.rows(dep=200, amort=50))
        self.assertEqual((v, r, b, len(terms), ttm), (Decimal(250), None, "depreciation_plus_intangible_amortization", 2,
                                                       Decimal(1000)))
        self.assertEqual(self.lev_flags(self.rows(dep=200, amort=50)),
                         (Decimal(5000), {"da_basis": ["depreciation_plus_intangible_amortization"]}))

    def test_depreciation_only_when_amortization_never_tagged(self):
        (v, _, r, b), _ = self.da(self.rows(dep=200))
        self.assertEqual((v, r, b), (Decimal(200), None, "depreciation_only"))
        self.assertEqual(self.lev_flags(self.rows(dep=200)), (Decimal(4800), {"da_basis": ["depreciation_only"]}))

    def test_amortization_tagged_but_missing_for_the_quarter(self):
        (v, _, r, b), (ttm, _, rt, _) = self.da(self.rows(dep=200, amort=50, skip_amort=("2025-12-31",)))
        self.assertEqual((v, r, b, ttm, rt), (None, "term_missing", None, None, "term_missing"))

    def test_nothing_tagged(self):
        (v, _, r, _), _ = self.da([("operating_income", "us-gaap:OperatingIncomeLoss", "2025-10-01", "2025-12-31", 1,
                                    "q", "2026-02-01")])
        self.assertEqual((v, r), (None, "concept_unresolved"))

    def test_total_line_at_a_recast_boundary_is_not_replaced(self):
        # T4 = exercice − neuf mois ; l'exercice a été retraité au-delà de l'arrondi, les neuf mois non
        rows = [("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01", "2025-12-31", 1200,
                 "k25", "2026-02-01", 0),
                ("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01", "2025-12-31", 1300,
                 "k26", "2026-03-01", 0),
                ("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01", "2025-09-30", 900,
                 "q3", "2025-11-01", 0),
                ("ppe_depreciation", "us-gaap:Depreciation", "2025-10-01", "2025-12-31", 280, "k25", "2026-02-01", 0)]
        (v, _, r, _), _ = self.da(rows)
        self.assertEqual((v, r), (None, "recast_boundary"))


class ImpliedLife(unittest.TestCase):
    """Point 2 : brut amortissable moyen ÷ dotation des immobilisations corporelles, jamais la ligne globale."""

    def life(self, extra):
        rows = [("gross_depreciable_ppe", "us-gaap:PropertyPlantAndEquipmentGross", None, "2024-12-31", 6500, "k24",
                 "2025-02-01"),
                ("gross_depreciable_ppe", "us-gaap:PropertyPlantAndEquipmentGross", None, "2025-12-31", 7408, "k25",
                 "2026-02-01")] + extra
        S = series(rows, (2024, 2025))
        out = rank2.annual_rank2(S, "G", D("2025-01-01"), D("2025-12-31"), D(AS_OF), "revised", AS_OF)
        return next(x for x in out if x["measure"] == "implied_useful_life")

    def test_depreciation(self):
        c = self.life([("ppe_depreciation", "us-gaap:Depreciation", "2025-01-01", "2025-12-31", 574, "k25", "2026-02-01"),
                       ("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01",
                        "2025-12-31", 8636, "k25", "2026-02-01")])
        self.assertEqual((c["status"], c["denominator"], round(c["value"], 2)), ("computed", Decimal(574), Decimal("12.11")))
        self.assertIn("hors amortissement des incorporels", json.loads(c["flags"])["note"])

    def test_total_line_alone_is_not_used(self):
        c = self.life([("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01",
                        "2025-12-31", 8636, "k25", "2026-02-01")])
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "concept_unresolved"))


class RevisionWithinRounding(unittest.TestCase):
    """Point 3 : deux occurrences qui ne diffèrent que dans leur tolérance d'arrondi ne font pas une révision."""

    def test_unit_change_is_not_a_revision(self):
        # CoreWeave, premier semestre 2025 : milliers dans le 10-Q de 2025, millions dans celui de 2026
        self.assertFalse(model.revised([1002978000.0, 1003000000.0], [-3, -6], [False, False], ["q25", "q26"]))

    def test_same_number_at_two_precisions_is_not_a_revision(self):
        # Oracle, 10-K de 2026 : 3 129 M$ et « 3,1 milliards »
        self.assertFalse(model.revised([3129000000.0, 3100000000.0], [-6, -8], [False, False], ["k26", "k26"]))

    def test_restatement_beyond_rounding_is_a_revision(self):
        self.assertTrue(model.revised([1002978000.0, 1010000000.0], [-3, -6], [False, False], ["q25", "q26"]))
        self.assertTrue(model.revised([10.0, 10.000001], [None, None], [True, True], ["a", "b"]))

    def test_pairwise_overlap_is_not_enough(self):
        # chaque valeur est proche de celle du milieu, pas l'une de l'autre
        self.assertTrue(model.revised([3129e6, 3100e6, 3149e6], [-6, -8, -6], [False] * 3, ["a", "a", "b"]))

    def test_companyfacts_takes_the_precision_of_its_filing(self):
        vals, decs = [1002978000.0, 1002978000.0, 1003000000.0, 1003000000.0], [None, -3, None, -6]
        self.assertFalse(model.revised(vals, decs, [None, False, None, False], ["q25", "q25", "q26", "q26"]))
        self.assertTrue(model.revised([1002978000.0, 1003000000.0], [None, None], [None, None], ["q25", "q26"]))

    def test_quarter_from_cumulative_terms(self):
        # T2 = semestre − T1 ; le semestre est publié à deux précisions dans deux dépôts
        rows = [("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01", "2025-03-31",
                 443497000, "q1", "2025-05-15", -3),
                ("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01", "2025-06-30",
                 1002978000, "q2", "2025-08-13", -3),
                ("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01", "2025-06-30",
                 1003000000, "q26", "2026-08-12", -6)]
        S = series(rows)
        v, terms, r = S.quarter("depreciation_expense", S.quarters[1], D(AS_OF))
        self.assertEqual((v, r), (Decimal("1003000000.0") - Decimal("443497000.0"), None))
        self.assertEqual([t["revised"] for t in terms], [False, False])


class StockIssued(unittest.TestCase):
    """Point 4 : les additions payées en titres n'ont plus de candidat."""

    def test_no_candidate(self):
        self.assertEqual(quantities.quantity_definitions()["stock_paid_ppe_additions"]["candidates"], [])

    def test_measure_is_not_determinable(self):
        S = series([("cfo", "us-gaap:NetCashProvidedByUsedInOperatingActivities", "2025-01-01", "2025-12-31", 1, "k",
                     "2026-02-01")])
        out = annual_measures(S, "G", D("2025-01-01"), D("2025-12-31"), D(AS_OF), "revised", AS_OF)
        c = next(x for x in out if x["measure"] == "stock_paid_additions")
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "concept_unresolved"))


if __name__ == "__main__":
    unittest.main()
