"""Volets B et C de D-0058 : coupe des 13D et 13G, notes des déposants contrôlés, section d'un prospectus, ordre et
plafond du volet B.

Lancement : python3 -m unittest discover -s tests -t .
"""
import re
import unittest

from pipeline import sb_own as S

SCHED_D = b"""<html><body>
<p>CUSIP No. 123456789</p>
<p>1. NAMES OF REPORTING PERSONS</p><p>SoftBank Group Corp.</p>
<p>(1) Based on 100 shares outstanding.</p>
<p>Item 1. Security and Issuer</p><p>Common stock of Example Corp.</p>
<p>Item 2. Identity and Background</p><p>SVF Holdco is a wholly owned subsidiary of SoftBank Group Corp.</p>
<p>Item 4. Purpose of Transaction</p><p>The shares were acquired for investment.</p>
<p>Item 6. Contracts, Arrangements</p><p>SVF Holdco entered into a margin loan with a bank syndicate.</p>
<p>Item 7. Material to be Filed as Exhibits</p><p>99.1 Joint Filing Agreement</p>
<p>SIGNATURE</p><p>After reasonable inquiry, I certify.</p>
<p>Schedule A - Directors and Executive Officers of SoftBank Group Corp.</p><p>Name | Citizenship</p>
</body></html>"""

SCHED_G = b"""<html><body>
<p>1. NAMES OF REPORTING PERSONS</p><p>SoftBank Vision Fund (AIV M1) L.P.</p>
<p>* The remainder of this cover page shall be filled out for a reporting person's initial filing.</p>
<p>** Calculated based upon 85,754,101 shares outstanding.</p>
<p>Item 1(a) | Name of Issuer:</p><p>Example Health, Inc.</p>
<p>Item 2(a) | Name of Person Filing:</p><p>SoftBank Vision Fund (AIV M1) L.P.</p>
<p>Item 4. | Ownership.</p><p>See the cover pages.</p>
<p>Item 5. | Ownership of Five Percent or Less of a Class.</p><p>Not applicable.</p>
<p>Item 9. | Notice of Dissolution of Group.</p><p>Not applicable.</p>
</body></html>"""

XML_G = b"""<?xml version="1.0"?><edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
<headerData><submissionType>SCHEDULE 13G</submissionType></headerData>
<formData>
<coverPageHeaderReportingPersonDetails><reportingPersonName>SoftBank Group Corp.</reportingPersonName>
<classPercent>90.7</classPercent><comments>Based on 676,000,000 shares outstanding.</comments></coverPageHeaderReportingPersonDetails>
<items><item1><issuerName>PayPay Corporation</issuerName></item1>
<item4><amountBeneficiallyOwned>613,638,240</amountBeneficiallyOwned></item4>
<item5><notApplicableFlag>Y</notApplicableFlag></item5></items>
<signatureInformation><signatureDetails><signature>A person</signature></signatureDetails></signatureInformation>
</formData></edgarSubmission>"""

XML_D = b"""<?xml version="1.0"?><edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13D">
<formData><coverPageHeader><authorizedPersons><notificationInfo><personName>A person</personName></notificationInfo>
</authorizedPersons></coverPageHeader>
<reportingPersons><reportingPersonInfo><reportingPersonName>SoftBank Group Corp.</reportingPersonName>
<comments>Cover note.</comments></reportingPersonInfo></reportingPersons>
<items1To7><item1><securityTitle>Common Stock</securityTitle></item1>
<item2><filingPersonName>SoftBank Group Corp. and its wholly owned subsidiary SoftBank Group Capital Ltd</filingPersonName></item2>
<item6><contractDescription>Margin loan agreement.</contractDescription></item6></items1To7>
</formData></edgarSubmission>"""

NOTES = b"""<html><body>
<p><b>Consolidated Balance Sheets</b></p><p>Total assets | 100</p>
<p><b>Notes to Consolidated Financial Statements</b></p>
<p><b>Note 1. Organization</b></p><p>The Company was formed in 2020.</p>
<p><b>SB Energy, Inc.</b></p><p><b>(unaudited)</b></p>
<p><b>Note 2. Debt</b></p><p><b>Consolidated statements of operations by segment:</b></p><p>Term loan details.</p><p>F-12</p>
<p><b>Note 3. Subsequent events</b></p><p>On August 17, 2026, NVIDIA agreed to invest.</p>
<p><b>SB Energy, Inc.</b></p><p><b>Shares</b></p><p><b>Common Stock</b></p><p>J.P. Morgan | Goldman Sachs</p>
<p><b>PART II</b></p><p><b>Item 13. Other expenses</b></p>
</body></html>"""

NOTES_ARM = b"""<html><body>
<p><b>Notes to the Consolidated Financial Statements</b></p>
<p><b>1 - Description of Business</b></p><p>Arm licenses its architecture.</p>
<p><b>2 - Related Party Transactions</b></p><p>SoftBank Group Corp. is the parent of the Company.</p>
<p><b>B. Significant Changes</b></p><p>No significant changes.</p>
<p><b>Item 9. The Offer and Listing</b></p><p>Our ADSs trade on Nasdaq.</p>
</body></html>"""

PROSPECTUS = b"""<html><body>
<p><b>TABLE OF CONTENTS</b></p>
<p>CERTAIN RELATIONSHIPS AND RELATED PARTY TRANSACTIONS ........ 180</p>
<p><b>CERTAIN RELATIONSHIPS AND RELATED PARTY</b></p><p><b>TRANSACTIONS</b></p>
<p>SoftBank Group Corp. provides us with a credit facility of $500 million.</p>
<p>We lease office space from an affiliate of SoftBank.</p>
<p><b>PRINCIPAL STOCKHOLDERS</b></p><p>The table below lists holders.</p>
</body></html>"""


class Schedules(unittest.TestCase):
    def test_item_range(self):
        self.assertEqual(S.item_range("SC 13D/A"), (2, 7))
        self.assertEqual(S.item_range("SCHEDULE 13D"), (2, 7))
        self.assertEqual(S.item_range("SC 13G"), (1, 4))
        self.assertEqual(S.item_range("SCHEDULE 13G/A"), (1, 4))

    def test_13d_items_2_to_7_without_cover_signature_or_annex(self):
        t, _ = S.schedule_text(SCHED_D, "x.htm", "SC 13D")
        self.assertTrue(t.startswith("Item 2. Identity and Background"))
        self.assertIn("margin loan", t)
        self.assertIn("99.1 Joint Filing Agreement", t)
        for absent in ("NAMES OF REPORTING PERSONS", "Security and Issuer", "SIGNATURE", "I certify", "Citizenship",
                       "Based on 100 shares"):
            self.assertNotIn(absent, t)

    def test_13g_items_1_to_4_and_cover_notes(self):
        t, _ = S.schedule_text(SCHED_G, "x.htm", "SC 13G")
        self.assertTrue(t.startswith("Item 1(a)"))
        self.assertIn("See the cover pages.", t)
        self.assertNotIn("Five Percent or Less", t)
        self.assertNotIn("Dissolution", t)
        self.assertIn("Notes de la page de garde :", t)
        self.assertIn("Calculated based upon 85,754,101 shares outstanding.", t)
        self.assertNotIn("remainder of this cover page", t)       # mention type

    def test_xml_13g(self):
        t, how = S.schedule_text(XML_G, "primary_doc.xml", "SCHEDULE 13G")
        self.assertEqual(how, "xml")
        self.assertIn("item1/issuerName: PayPay Corporation", t)
        self.assertIn("item4/amountBeneficiallyOwned: 613,638,240", t)
        self.assertNotIn("item5", t)
        self.assertNotIn("classPercent", t)                       # page de garde
        self.assertIn("Based on 676,000,000 shares outstanding.", t)
        self.assertNotIn("A person", t)                           # signature

    def test_xml_13d(self):
        t, _ = S.schedule_text(XML_D, "primary_doc.xml", "SCHEDULE 13D/A")
        self.assertIn("item2/filingPersonName: SoftBank Group Corp.", t)
        self.assertIn("item6/contractDescription: Margin loan agreement.", t)
        self.assertNotIn("securityTitle", t)                      # Item 1
        self.assertNotIn("A person", t)                           # personnes autorisées
        self.assertNotIn("Cover note.", t)                        # page de garde d'un 13D

    def test_model_issuer_classes(self):
        self.assertEqual(S.model_issuer(cik="1973239"), "ARM")
        self.assertEqual(S.model_issuer(cik="101830"), "SPRINT")              # entité du point 9 : ordre des 13D
        self.assertIsNone(S.model_issuer(cik="101830", forms=True))           # formulaires 3 à 5 : énumération
        self.assertEqual(S.model_issuer(name="NVIDIA CORPORATION"), "NVDA")
        self.assertIsNone(S.model_issuer(name="T-MOBILE US INC"))

    def test_descending_key(self):
        xs = ["2021-03-18", "2026-05-29", "2024-01-02"]
        self.assertEqual(sorted(xs, key=S._neg), ["2026-05-29", "2024-01-02", "2021-03-18"])


class Notes(unittest.TestCase):
    def test_sbe_notes_close_at_back_cover(self):
        sets = S.split_notes(NOTES, S.TITLE_SBE, noise=S.SBE_HEADER)
        self.assertEqual(len(sets), 1)
        notes = sets[0]["notes"]
        self.assertEqual([n["number"] for n in notes], [1, 2, 3])
        self.assertIn("Term loan details.", notes[1]["text"])     # titre de tableau à deux-points : pas une fin
        self.assertNotIn("F-12", notes[1]["text"])
        last = notes[2]["text"]
        self.assertIn("NVIDIA agreed to invest", last)
        for absent in ("SB Energy, Inc.", "Shares", "J.P. Morgan", "PART II", "(unaudited)"):
            self.assertNotIn(absent, last)
        self.assertNotIn("SB Energy, Inc.", notes[0]["text"])

    def test_arm_notes_close_at_next_item(self):
        notes = S.split_notes(NOTES_ARM, S.TITLE_ARM)[0]["notes"]
        self.assertEqual([n["title"] for n in notes], ["Description of Business", "Related Party Transactions"])
        self.assertNotIn("Significant Changes", notes[1]["text"])
        self.assertNotIn("Nasdaq", notes[1]["text"])

    def test_heading_section_skips_table_of_contents(self):
        t = S.heading_section(PROSPECTUS, S.RP_HEAD)
        self.assertIn("credit facility of $500 million", t)
        self.assertIn("affiliate of SoftBank", t)
        self.assertNotIn("PRINCIPAL STOCKHOLDERS", t)
        self.assertNotIn("........", t)


if __name__ == "__main__":
    unittest.main()
