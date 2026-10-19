"""Volet F de D-0058 : positions de SoftBank dans les Form N-PORT Data Sets et mesure nport_price_to_par.

Lancement : python3 -m unittest discover -s tests -t .
"""
import io
import tempfile
import unittest
import zipfile
from decimal import Decimal
from pathlib import Path

import pandas as pd

from pipeline import nport as P

C = {"tables": {"holding": "FUND_REPORTED_HOLDING", "identifiers": "IDENTIFIERS", "debt": "DEBT_SECURITY",
                "submission": "SUBMISSION", "registrant": "REGISTRANT", "fund": "FUND_REPORTED_INFO"},
     "holding": {"accession": "ACCESSION_NUMBER", "holding_id": "HOLDING_ID", "issuer_name": "ISSUER_NAME",
                 "issuer_lei": "ISSUER_LEI"},
     "identifiers": {"holding_id": "HOLDING_ID"}, "debt": {"holding_id": "HOLDING_ID"},
     "submission": {"accession": "ACCESSION_NUMBER"}, "registrant": {"accession": "ACCESSION_NUMBER"},
     "fund": {"accession": "ACCESSION_NUMBER"}}


def tsv(rows):
    return "\n".join("\t".join(r) for r in rows) + "\n"


class Scan(unittest.TestCase):
    def test_keeps_softbank_names_and_their_leis(self):
        hold = [["ACCESSION_NUMBER", "HOLDING_ID", "ISSUER_NAME", "ISSUER_LEI", "BALANCE"],
                ["A1", "1", "SoftBank Group Corp", "LEI-SB", "100"],
                ["A1", "2", "SBG 5.125 2027", "LEI-SB", "50"],          # même LEI, autre nom : gardée
                ["A2", "3", "Softbank Corp.", "N/A", "10"],
                ["A2", "4", "Toyota Motor Corp", "LEI-T", "70"]]
        with tempfile.TemporaryDirectory() as d:
            zp = Path(d) / "2025q1_nport.zip"
            with zipfile.ZipFile(zp, "w") as z:
                z.writestr("FUND_REPORTED_HOLDING.tsv", tsv(hold))
                z.writestr("IDENTIFIERS.tsv", tsv([["HOLDING_ID", "IDENTIFIER_ISIN"], ["1", "XS1"], ["4", "JP9"]]))
                z.writestr("DEBT_SECURITY.tsv", tsv([["HOLDING_ID", "MATURITY_DATE"], ["2", "2027-09-19"]]))
                z.writestr("SUBMISSION.tsv", tsv([["ACCESSION_NUMBER", "FILING_DATE"], ["A1", "2025-02-27"], ["A2", "2025-02-28"], ["A3", "x"]]))
                z.writestr("REGISTRANT.tsv", tsv([["ACCESSION_NUMBER", "CIK"], ["A1", "1"], ["A3", "3"]]))
                z.writestr("FUND_REPORTED_INFO.tsv", tsv([["ACCESSION_NUMBER", "SERIES_ID"], ["A2", "S2"]]))
            out, stats, found = P.scan_archive(zp, leis=(), c=C)
        self.assertEqual(sorted(out["holding"]["HOLDING_ID"]), ["1", "2", "3"])
        self.assertEqual(found, ["LEI-SB"])                       # « N/A » n'est pas un LEI
        self.assertEqual(stats["by_name"], 2)
        self.assertEqual(sorted(out["identifiers"]["HOLDING_ID"]), ["1"])
        self.assertEqual(sorted(out["submission"]["ACCESSION_NUMBER"]), ["A1", "A2"])


class Measure(unittest.TestCase):
    def positions(self):
        base = {"unit": "PA", "asset_cat": "DBT", "currency": "USD", "issuer_name": "SOFTBANK GROUP CORP",
                "title": "SOFTBANK 5.125 09/19/27", "maturity": "2027-09-19", "cusip": "83404D"}
        rows = [  # série S1 : dépôt initial puis amendement, qui le remplace
            dict(base, series_id="S1", report_date="2025-03-31", filing_date="2025-05-20", accession="A1",
                 isin="XS1", value_local="90", balance="100"),
            dict(base, series_id="S1", report_date="2025-03-31", filing_date="2025-06-02", accession="A1-amd",
                 isin="XS1", value_local="95", balance="100"),
            dict(base, series_id="S2", report_date="2025-03-31", filing_date="2025-05-21", accession="A2",
                 isin="XS1", value_local="180", balance="200"),
            dict(base, series_id="S3", report_date="2025-03-31", filing_date="2025-05-22", accession="A3",
                 isin=None, value_local="50", balance="50", cusip="83404E"),        # sans ISIN : CUSIP
            dict(base, series_id="S4", report_date="2025-03-31", filing_date="2025-05-22", accession="A4",
                 isin="JP9", value_local="10", balance="10", unit="NS", asset_cat="EC")]   # actions : hors mesure
        return pd.DataFrame(rows)

    def test_latest_filing_of_each_series_replaces_the_earlier(self):
        p = P.latest_by_series(self.positions())
        self.assertEqual(sorted(p["accession"]), ["A1-amd", "A2", "A3", "A4"])

    def test_ratio_by_security_and_date(self):
        r = P.price_to_par(self.positions()).set_index("security")
        self.assertEqual(r.loc["XS1", "ratio"], Decimal("275") / Decimal("300"))
        self.assertEqual(int(r.loc["XS1", "n_series"]), 2)
        self.assertEqual(r.loc["XS1", "principal"], Decimal("300"))
        self.assertIn("CUSIP:83404E", r.index)
        self.assertNotIn("JP9", r.index)


if __name__ == "__main__":
    unittest.main()
