"""Bloc lender_portfolio (D-0045) : mesures de portefeuille d'une BDC et événements F11 à F13.

Lancement : python3 -m unittest discover -s tests -t .
"""
import unittest
from decimal import Decimal

import pandas as pd

from pipeline import lender_portfolio as LP

HEAD = ["adsh", "tag", "version", "ddate", "qtrs", "uom", "segments", "dimn", "value", "footnote", "footlen"]


def pos(ident, cls="debt", cost=None, fv=None, principal=None, rate=None, pik=None, unfunded=None, perf=False,
        nonperf=False, industry=None):
    return {"archive": "a", "archive_sha256": "s", "adsh": "0001-26-000001", "cik": "0000000001", "name": "Fonds",
            "former": "", "form": "10-Q", "period": "20260630", "filed": "20260805", "identifier": ident,
            "other_axes": "", "instrument_class": cls, "cost": cost, "fair_value": fv, "principal": principal,
            "principal_usd": principal is not None, "rate": rate, "rate_pik": pik, "unfunded_commitment": unfunded,
            "has_perf": perf, "nonperforming": nonperf, "industry": industry}


class Holdings(unittest.TestCase):
    def test_status_and_sector_axes_leave_the_position_key(self):
        seg = ("InvestmentIdentifierAxis(us-gaap/2025)=Acme Corp, First lien loan(0001-26-000001);"
               "FinancialInstrumentPerformanceStatusAxis(us-gaap/2025)=NonaccrualMember(0001-26-000001);"
               "IndustrySectorAxis(us-gaap/2025)=SoftwareMember(0001-26-000001);")
        lines = [["0001-26-000001", "InvestmentOwnedAtCost", "us-gaap/2025", "20260630", "0", "USD", seg, "3", "100", "", ""],
                 ["0001-26-000001", "InvestmentOwnedAtFairValue", "us-gaap/2025", "20260630", "0", "USD", seg, "3", "90", "", ""],
                 ["0001-26-000001", "InvestmentOwnedAtCost", "us-gaap/2025", "20251231", "0", "USD", seg, "3", "7", "", ""]]
        h = LP.holdings_of(lines, "20260630", HEAD)
        self.assertEqual(len(h), 1)
        r = next(iter(h.values()))
        self.assertEqual((r["cost"], r["fair_value"], r["nonperforming"], r["industry"]), (100.0, 90.0, True, "SoftwareMember"))


class VehicleCells(unittest.TestCase):
    def cells(self, rows):
        return {c["measure"]: c for c in LP.vehicle_cells(pd.DataFrame(rows), "0000000001", "2026-06-30", "2026-10-07",
                                                          {"software_coverage_min": 0.9})}

    def test_measures(self):
        c = self.cells([pos("A, First lien loan", cost=100, fv=95, principal=100, rate=0.10, pik=0.02, unfunded=10),
                        pos("B, Second lien loan", cost=50, fv=40, principal=50, rate=0.12),
                        pos("C, Common stock", cls="equity", cost=20, fv=30)])
        self.assertEqual(c["bdc_portfolio_fv_to_cost"]["value"], Decimal("135") / Decimal("150"))   # prêts seulement
        pik = c["bdc_portfolio_pik_share"]
        self.assertEqual(pik["status"], "bounded")                    # B sans taux PIK balisé : borne basse
        self.assertEqual(pik["value_lower"], Decimal("2") / Decimal("16"))
        self.assertEqual(c["bdc_portfolio_non_accrual_share"]["nd_reason"], "not_tagged")
        self.assertAlmostEqual(c["bdc_portfolio_unfunded_ratio"]["value_lower"], Decimal("10") / Decimal("165"),
                               delta=Decimal("1e-6"))       # cellules arrondies à six décimales
        self.assertEqual(c["bdc_portfolio_software_share"]["nd_reason"], "not_tagged")

    def test_non_accrual_and_sector_when_tagged(self):
        c = self.cells([pos("A, First lien loan", cost=100, fv=60, perf=True, nonperf=True, industry="SoftwareMember"),
                        pos("B, First lien loan", cost=300, fv=300, industry="HealthcareMember")])
        na = c["bdc_portfolio_non_accrual_share"]
        self.assertEqual((na["status"], na["value_lower"]), ("bounded", Decimal("0.25")))
        self.assertAlmostEqual(c["bdc_portfolio_software_share"]["value"], Decimal("60") / Decimal("360"),
                               delta=Decimal("1e-6"))
        self.assertEqual(c["bdc_portfolio_software_share"]["status"], "computed")

    def test_unlabelled_loans_scale_errors_and_coverage(self):
        # identifiants sans mot d'instrument : le principal en fait des prêts ; un coût à mille fois le principal
        # est une erreur d'échelle écartée ; un coût manquant sur plus de 10 % de la juste valeur : non déterminable
        c = self.cells([pos("Acme Holdings, Inc. 1", cls="unclassified", cost=98, fv=99, principal=100, rate=0.1),
                        pos("Beta Holdings, Inc.", cls="unclassified", cost=50_000, fv=49, principal=50, rate=0.1),
                        pos("Gamma, First lien loan", unfunded=5)])
        fv = c["bdc_portfolio_fv_to_cost"]
        self.assertEqual(fv["status"], "computed")
        self.assertAlmostEqual(fv["value"], Decimal("99") / Decimal("98"), delta=Decimal("1e-6"))
        self.assertIn('"scale_errors_excluded": 1', fv["flags"])
        c2 = self.cells([pos("A, First lien loan", cost=100, fv=100, principal=100),
                         pos("B, First lien loan", fv=50, principal=50)])
        self.assertEqual(c2["bdc_portfolio_fv_to_cost"]["nd_reason"], "not_tagged")
        self.assertEqual(c2["bdc_portfolio_pik_share"]["nd_reason"], "not_tagged")   # aucun taux total balisé


class Events(unittest.TestCase):
    def series(self, vals, dates):
        return {"cik:1": {d: {"bdc_portfolio_fv_to_cost": {"status": "computed", "value": v, "value_lower": None,
                                                           "knowledge_date": d}} for d, v in zip(dates, vals)}}

    def ev(self, vals, dates):
        out = LP.events_cells(self.series(vals, dates), "2026-10-07", 120)
        return [(c["period_end"], c["status"], c["value_text"], c["nd_reason"]) for c in out if c["breakdown_key"] == "F11"]

    def test_two_consecutive_declines(self):
        e = self.ev([1.00, 0.99, 0.98, 0.985], ["2025-12-31", "2026-03-31", "2026-06-30", "2026-09-30"])
        self.assertEqual([x[1:] for x in e], [("not_determinable", None, "prior_period_missing")] * 2 +
                         [("computed", "event", None), ("computed", "no_event", None)])

    def test_gap_is_not_a_quarter_without_event(self):
        e = self.ev([1.00, 0.99, 0.98], ["2025-06-30", "2026-03-31", "2026-06-30"])
        self.assertEqual(e[-1][1:], ("not_determinable", None, "prior_period_missing"))


if __name__ == "__main__":
    unittest.main()
