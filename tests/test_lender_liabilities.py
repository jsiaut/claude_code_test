"""Bloc lender_liabilities (D-0047) : couverture et levier, offres de rachat, F15 et F16.

Lancement : python3 -m unittest discover -s tests -t .
"""
import json
import unittest
from decimal import Decimal

import pandas as pd

from pipeline import lender_liabilities as LL

CFG = {"coverage_scale": {"ratio": [1, 100], "percent": [100, 1000], "per_thousand": [1000, 10000]},
       "tenders": {"window": ["2022-10-01", "2026-10-07"], "program_min_offers": 4, "program_gap_days_max": 120,
                   "interruption_days": 120, "listing_forms": ["8-A12B"], "exit_forms": ["N-54C", "15-12G"]}}


def row(cov=None, li=None, na=None, se=None, assets=None):
    return {"cik": "0000000001", "period": "20260630", "filed": "20260805", "adsh": "0001-26-000001", "archive": "a",
            "archive_sha256": "s", "form": "10-Q", "name": "Fonds", "coverage_raw": cov, "liabilities": li,
            "assets_net": na, "stockholders_equity": se, "assets": assets}


class Balance(unittest.TestCase):
    def cells(self, r):
        return {c["measure"]: c for c in LL.vehicle_cells(r, "2026-10-07", CFG)}

    def test_scale_bands(self):
        self.assertEqual(LL.coverage_value(1.85, CFG), (Decimal("1.85"), "ratio"))
        self.assertEqual(LL.coverage_value(185, CFG), (Decimal("1.85"), "percent"))
        self.assertEqual(LL.coverage_value(1850, CFG), (Decimal("1.85"), "per_thousand"))
        self.assertEqual(LL.coverage_value(0.5, CFG)[0], None)

    def test_debt_to_net_assets_derived_from_coverage(self):
        c = self.cells(row(cov=2.0, li=110, na=100))
        self.assertEqual(c["bdc_liab_asset_coverage"]["value"], Decimal("2"))
        self.assertEqual(c["bdc_liab_debt_to_net_assets"]["value"], Decimal("1"))
        self.assertEqual(c["bdc_liab_liabilities_to_net_assets"]["value"], Decimal("1.1"))

    def test_threshold_tagged_instead_of_ratio_is_conflicting(self):
        # passif 50, actif net 260 : la couverture vaut au moins 1 + 260 ÷ 50 = 6,2 ; 1,5 est le seuil légal
        c = self.cells(row(cov=1.5, li=50, na=260))
        self.assertEqual(c["bdc_liab_asset_coverage"]["nd_reason"], "conflicting")
        self.assertEqual(c["bdc_liab_debt_to_net_assets"]["nd_reason"], "conflicting")

    def test_net_assets_sign_error_corrected_by_identity(self):
        c = self.cells(row(li=1500, na=-1300, assets=2800))
        self.assertAlmostEqual(c["bdc_liab_liabilities_to_net_assets"]["value"], Decimal(1500) / Decimal(1300),
                               delta=Decimal("1e-6"))
        self.assertIn("sign_corrected", c["bdc_liab_liabilities_to_net_assets"]["flags"])
        self.assertEqual(self.cells(row(li=10, se=-5, assets=3))["bdc_liab_liabilities_to_net_assets"]["nd_reason"],
                         "denominator_nonpositive")


class Offers(unittest.TestCase):
    def test_security_class(self):
        t = "Fonds\n(Name of Filing Person)\nClass I, Class D and Class S Shares of Beneficial Interest\n(Title of Class of Securities)"
        self.assertEqual(LL.security_class(t)[0], "common")
        self.assertEqual(LL.security_class("Fonds\n5.75% Convertible Notes due 2023\n(Title of Class of Securities)")[0], "debt")
        self.assertEqual(LL.security_class("X\n5.35% Series A Preferred Stock\n(Titles of Classes of Securities)")[0], "preferred")

    def test_referenced_date(self):
        t = "This Amendment No. 1 amends the Tender Offer Statement on Schedule TO filed with the SEC on May 1, 2024 (the Schedule TO)."
        self.assertEqual(str(LL.referenced_date(t)), "2024-05-01")

    def test_class_parts_need_a_named_class(self):
        s = ("approximately 93,650,433 Class S Shares, 21,440,559 Class D Shares and 348,729,633 Class I Shares were "
             "validly tendered")
        self.assertEqual(LL.class_parts(s), ["93650433", "21440559", "348729633"])
        self.assertEqual(LL.class_parts("approximately 2,309,063 Shares were validly tendered ... by approximately "
                                        "1,180,395 Shares"), [])

    def test_outcomes(self):
        pro = LL.tender_outcome({"tendered": "463820625", "tendered_unit": "shares", "accepted": "105851996",
                                 "accepted_unit": "shares", "offer_max": "5.00", "offer_max_unit": "pct",
                                 "tendered_pct": "21.9", "proration": True})
        self.assertEqual(pro["f15"], "event")
        self.assertEqual(pro["demand"][0], Decimal("4.38"))
        allr = LL.tender_outcome({"tendered": "100", "tendered_unit": "shares", "accepted": "all",
                                  "offer_max": "200", "offer_max_unit": "shares"})
        self.assertEqual((allr["acceptance"][0], allr["demand"][0], allr["f15"]), (Decimal(1), Decimal("0.5"), "no_event"))
        zero = LL.tender_outcome({"tendered": "0", "tendered_unit": "shares"})
        self.assertEqual((zero["acceptance"], zero["f15"]), ("denominator_nonpositive", "no_event"))
        pct = LL.tender_outcome({"accepted": "3000000", "accepted_unit": "shares", "acceptance_pct": "69.3", "proration": True})
        self.assertEqual((pct["acceptance"][0], pct["f15"]), (Decimal("0.693"), "event"))
        mix = LL.tender_outcome({"tendered": "4910881.567", "tendered_unit": "shares", "accepted": "47026423.73",
                                 "accepted_unit": "usd", "proration": True})
        self.assertEqual((mix["acceptance"], mix["f15"]), ("precondition_not_met", "event"))
        unknown = LL.tender_outcome({"tendered": "92729.642", "tendered_unit": "shares"})
        self.assertEqual(unknown["f15"], "not_disclosed")

    def test_zero_quote_and_digits(self):
        rec = {"tendered": "0", "tendered_unit": "shares", "tendered_quote": "No Shares were validly tendered."}
        self.assertEqual(LL.check_reading(rec, ["2. No Shares were validly tendered. Signature"]), [])
        bad = {"tendered": "1000", "tendered_unit": "shares", "tendered_quote": "A total of 999 Shares were validly tendered."}
        self.assertTrue(LL.check_reading(bad, ["A total of 999 Shares were validly tendered."]))


class Program(unittest.TestCase):
    def offers(self, dates):
        return [{"cik": "0000000001", "entity": "Fonds", "offer_key": f"1|{d}", "offer_accession": d, "offer_date": d,
                 "in_window": True} for d in dates]

    def inv(self, rows=()):
        return pd.DataFrame(list(rows) or [{"cik": "x", "form": "10-Q", "accession": "a", "filing_date": "2026-01-01"}])

    def test_interruption_after_regular_series(self):
        ev = LL.program_events(self.offers(["2025-01-02", "2025-04-01", "2025-07-01", "2025-10-01"]), self.inv(),
                               "2026-10-07", CFG)
        self.assertEqual([(e["last_offer"], e["outcome"]) for e in ev], [("2025-10-01", "event")])
        self.assertEqual(ev[0]["date"], "2026-01-29")

    def test_next_offer_listing_and_censoring(self):
        ds = ["2025-01-02", "2025-04-01", "2025-07-01", "2025-10-01", "2026-01-05"]
        ev = LL.program_events(self.offers(ds), self.inv(), "2026-03-01", CFG)
        self.assertEqual([e["outcome"] for e in ev], ["no_event", "end_offset_exceeded"])
        inv = self.inv([{"cik": "0000000001", "form": "8-A12B", "accession": "b", "filing_date": "2025-12-15"}])
        ev = LL.program_events(self.offers(ds[:4]), inv, "2026-10-07", CFG)
        self.assertEqual((ev[0]["outcome"], ev[0]["motive"]), ("no_event", "listing"))

    def test_irregular_series_has_no_cell(self):
        self.assertEqual(LL.program_events(self.offers(["2024-01-02", "2024-09-01", "2025-01-02", "2025-04-01"]),
                                           self.inv(), "2026-10-07", CFG), [])


if __name__ == "__main__":
    unittest.main()
