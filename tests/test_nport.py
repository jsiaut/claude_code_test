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
        base = {"unit": "PA", "asset_cat": "DBT", "payoff": "Long", "currency": "USD", "issuer_name": "SOFTBANK GROUP CORP",
                "title": "SOFTBANK 5.125 09/19/27", "maturity": "2027-09-19", "cusip": "000000000", "cik": None}
        rows = [  # série S1 : dépôt initial puis amendement, qui le remplace
            dict(base, series_id="S1", report_date="2025-03-31", filing_date="2025-05-20", accession="A1",
                 isin="XS1684384867", value_local="90", balance="100"),
            dict(base, series_id="S1", report_date="2025-03-31", filing_date="2025-06-02", accession="A1-amd",
                 isin="XS1684384867", value_local="95", balance="100"),
            dict(base, series_id="S2", report_date="2025-03-31", filing_date="2025-05-21", accession="A2",
                 isin="XS1684384867", value_local="180", balance="200"),
            dict(base, series_id="S3", report_date="2025-03-31", filing_date="2025-05-22", accession="A3",
                 isin="N/A", value_local="50", balance="50", cusip="J7596PAW9"),        # sans ISIN : CUSIP
            dict(base, series_id="S4", report_date="2025-03-31", filing_date="2025-05-22", accession="A4",
                 isin="JP3436100006", value_local="10", balance="10", unit="NS", asset_cat="EC")]   # actions : hors mesure
        return pd.DataFrame(rows)

    def test_latest_filing_of_each_series_replaces_the_earlier(self):
        p = P.latest_by_fund(self.positions())
        self.assertEqual(sorted(p["accession"]), ["A1-amd", "A2", "A3", "A4"])

    def test_closed_end_funds_without_series_are_their_registrants(self):
        x = self.positions().iloc[[1, 2]].assign(series_id=None, cik=["0001190935", "0001554697"])
        self.assertEqual(sorted(P.latest_by_fund(x)["accession"]), ["A1-amd", "A2"])

    def test_ratio_by_security_and_date(self):
        r = P.price_to_par(self.positions()).set_index("security")
        self.assertEqual(r.loc["XS1684384867", "ratio"], Decimal("275") / Decimal("300"))
        self.assertEqual(int(r.loc["XS1684384867", "n_series"]), 2)
        self.assertEqual(r.loc["XS1684384867", "principal"], Decimal("300"))
        self.assertIn("CUSIP:J7596PAW9", r.index)
        self.assertNotIn("JP3436100006", r.index)

    def test_cusip_only_position_takes_the_isin_given_to_the_same_cusip(self):
        x = self.positions()
        x.loc[[0, 1, 2, 3], "cusip"] = "J7596PAN9"
        x.loc[3, "isin"] = None
        self.assertEqual(P.security_keys(x)[3], "XS1684384867")
        x.loc[4, "cusip"] = "J7596PAN9"                     # même CUSIP sous deux ISIN : pas de rattachement
        self.assertEqual(P.security_keys(x)[3], "CUSIP:J7596PAN9")
        self.assertIsNone(P.security_keys(pd.DataFrame({"isin": ["N/A"], "cusip": ["000000000"]}))[0])

    def test_short_positions_and_other_issuers_stay_out(self):
        x = self.positions().iloc[[1]]
        rows = [x.assign(payoff="Short", accession="S")]
        # titre de Sprint déclaré sous le LEI de SoftBank Group : nom de Sprint
        rows.append(x.assign(isin="US85208NAE04", issuer_name="SPRINT SPECTRUM / SPEC I", title="Sprint Spectrum Co LLC"))
        # titre de Drawbridge déclaré sous le nom de la société mère : l'intitulé ne nomme jamais SoftBank
        rows.append(x.assign(isin="US26150TAA79", issuer_name="SoftBank Group Corp.", title="Drawbridge Special Opportunities Fund, LP"))
        kept, steps = P.selection(pd.concat([x] + rows, ignore_index=True))
        self.assertEqual(list(kept["security"]), ["XS1684384867"])
        self.assertEqual(steps["not_long"], 1)
        self.assertEqual(steps["securities_out"], ["US26150TAA79", "US85208NAE04"])


class Publication(unittest.TestCase):
    def test_last_modified_is_read_from_the_response_headers(self):
        from requests.structures import CaseInsensitiveDict
        h = CaseInsensitiveDict({"last-modified": "Thu, 08 Oct 2026 14:02:11 GMT"})   # en-têtes de requests
        self.assertEqual(P._published(h), ("Thu, 08 Oct 2026 14:02:11 GMT", "2026-10-08"))
        self.assertEqual(P._published(None), (None, None))

    def test_second_pass_counts_as_applied(self):
        self.assertEqual(P.applied({"leis_found": ["A", "B"], "leis_applied": []}), {"A", "B"})


class Leis(unittest.TestCase):
    def test_a_lei_is_softbank_s_only_when_most_of_its_positions_carry_the_name(self):
        hold = pd.DataFrame({"ISSUER_NAME": ["SoftBank Group Corp", "SoftBank Group Corp.", "SPRINT SPECTRUM / SPEC I",
                                             "SoftBank Group Corp.", "Sprint Corp", "Sprint Corporation",
                                             "CDS_SN SOFTBANK GROUP CORP", "Goldman Sachs International", "SoftBank Corp."],
                             "ISSUER_LEI": ["LEI-SBG", "LEI-SBG", "LEI-SBG", "LEI-SPRINT", "LEI-SPRINT", "LEI-SPRINT",
                                            "LEI-GSI", "LEI-GSI", "N/A"]})
        ev = P.lei_evidence(hold, c=C)
        self.assertEqual(ev["LEI-SBG"], {"positions": 3, "named": 2})
        self.assertNotIn("N/A", ev)
        self.assertEqual(P.accepted(ev), {"LEI-SBG"})      # Sprint 1 sur 3, Goldman 1 sur 2 : refusés


if __name__ == "__main__":
    unittest.main()
