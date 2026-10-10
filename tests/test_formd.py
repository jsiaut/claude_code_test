"""Bloc `form_d` de §14 (D-0041) : offres, dernier dépôt connu, cibles des véhicules.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import unittest

import pandas as pd

from pipeline import formd as F

XML = """<?xml version="1.0"?><edgarSubmission><submissionType>{t}</submissionType>
<primaryIssuer><cik>0002000001</cik><entityName>{name}</entityName></primaryIssuer>
<relatedPersonsList><relatedPersonInfo><relatedPersonName><firstName>n/a</firstName><lastName>Sponsor LLC</lastName>
</relatedPersonName></relatedPersonInfo></relatedPersonsList>
<offeringData><industryGroup><industryGroupType>Pooled Investment Fund</industryGroupType></industryGroup>
<typeOfFiling><newOrAmendment><isAmendment>{amend}</isAmendment>{prev}</newOrAmendment>{fs}</typeOfFiling>
<typesOfSecuritiesOffered><isPooledInvestmentFundType>true</isPooledInvestmentFundType></typesOfSecuritiesOffered>
<businessCombinationTransaction><isBusinessCombinationTransaction>false</isBusinessCombinationTransaction></businessCombinationTransaction>
<offeringSalesAmounts><totalOfferingAmount>Indefinite</totalOfferingAmount><totalAmountSold>{sold}</totalAmountSold>
</offeringSalesAmounts></offeringData></edgarSubmission>"""


def doc(t="D", name="OpenAI Fund a Series of X LLC", sold="1000", fs="2024-05-01", prev=None):
    return XML.format(t=t, name=name, sold=sold, amend="true" if prev else "false",
                      prev=f"<previousAccessionNumber>{prev}</previousAccessionNumber>" if prev else "",
                      fs=f"<dateOfFirstSale><value>{fs}</value></dateOfFirstSale>" if fs else
                      "<dateOfFirstSale><yetToOccur>true</yetToOccur></dateOfFirstSale>").encode()


def row(adsh, date, **kw):
    r = {"population": "vehicle_candidate", "cik": "2000001", "adsh": adsh, "form": kw.get("t", "D"),
         "file_date": date, "parse_state": "parsed"}
    r.update(F.parse(doc(**kw)))
    return r


class Parse(unittest.TestCase):
    def test_fields(self):
        r = F.parse(doc(t="D/A", prev="0002000001-24-000001"))
        self.assertEqual((r["issuer_cik"], r["total_amount_sold"], r["first_sale"], r["is_amendment"],
                          r["previous_accession"]), ("2000001", "1000", "2024-05-01", True, "0002000001-24-000001"))
        self.assertEqual(r["related_persons"], "Sponsor LLC")


class Offerings(unittest.TestCase):
    def test_amendment_without_date_joins_its_offering_and_last_filing_wins(self):
        df = pd.DataFrame([row("0002000001-24-000001", "2024-05-10", sold="1000"),
                           row("0002000001-25-000001", "2025-05-10", t="D/A", sold="2500", fs=None,
                               prev="0002000001-24-000001"),
                           row("0002000001-25-000009", "2025-09-01", sold="70", fs="2025-08-20")])
        offs = F.offerings(df)
        self.assertEqual(sorted(offs), ["2000001|2024-05-01", "2000001|2025-08-20"])
        self.assertEqual([r["total_amount_sold"] for r in offs["2000001|2024-05-01"]], ["1000", "2500"])


class Targets(unittest.TestCase):
    LEX = [{"term": "OpenAI", "ref": "LAB:OPENAI", "case": False}, {"term": "xAI", "ref": "SPCX", "case": True},
           {"term": "X Corp", "ref": "SPCX", "case": True}]

    def test_whole_word_and_case_rules(self):
        self.assertEqual(F.targets("OPENAI SPV I LLC", self.LEX), {"LAB:OPENAI"})
        self.assertEqual(F.targets("XAI Fund LLC", self.LEX), set())          # « xAI » sensible à la casse
        self.assertEqual(F.targets("Fearless xAI SPV 1 LLC", self.LEX), {"SPCX"})
        self.assertEqual(F.targets("OpenAIX Partners", self.LEX), set())

    def test_non_filer_by_quarter(self):
        first = {"SPCX": dt.date(2026, 8, 4), "NVDA": dt.date(1999, 6, 15)}
        self.assertTrue(F.non_filer("LAB:OPENAI", dt.date(2026, 9, 30), first))
        self.assertTrue(F.non_filer("SPCX", dt.date(2026, 6, 30), first))
        self.assertFalse(F.non_filer("SPCX", dt.date(2026, 9, 30), first))
        self.assertFalse(F.non_filer("NVDA", dt.date(2021, 3, 31), first))

    def test_quarter_ends(self):
        self.assertEqual(F.quarter_ends(dt.date(2025, 11, 2), dt.date(2026, 7, 1)),
                         [dt.date(2025, 12, 31), dt.date(2026, 3, 31), dt.date(2026, 6, 30)])


if __name__ == "__main__":
    unittest.main()
