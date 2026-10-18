"""Amendements de D-0056 avant lecture : Item 9A ou Item 4 d'un rapport qui ne numérote ses items que dans son
index de correspondance (Intel) ; titres des notes de dette d'un 20-F en IFRS et équivalents ifrs-full des notes
de leviers et de revenu (TSMC).

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import sections, text_catalog as TC

EVAL = ("<p>Based on management's evaluation, as of the end of the period covered by this report, our principal executive "
        "officer and principal financial officer have concluded that our disclosure controls and procedures are effective at "
        "the reasonable assurance level.</p>")
NO_CHANGE = ("<p>There were no changes to our internal control over financial reporting during the quarter that have "
             "materially affected, or are reasonably likely to materially affect, our internal control.</p>")


def doc(index=True):
    return ("<html><body><p>Controls and Procedures | 41</p>"
            "<p>Quantitative and Qualitative Disclosures About Market Risk</p><p>We are affected by changes in rates.</p>"
            "<p>Controls and Procedures</p><p>Inherent Limitations on Effectiveness of Controls</p>"
            "<p>Our management does not expect that our disclosure controls will prevent all errors and all fraud.</p>"
            f"<p>Evaluation of Disclosure Controls and Procedures</p>{EVAL}"
            "<p>Other Key Information | 43</p><p>Table of Contents</p>"
            f"<p>Changes in Internal Control Over Financial Reporting</p>{NO_CHANGE}"
            "<p>Issuer Purchases of Equity Securities</p><p>We have an ongoing authorization to repurchase shares.</p>"
            + ("<p>Form 10-Q Cross-Reference Index</p><p>Item 4. | Controls and Procedures | Page 41</p>" if index else "")
            + "</body></html>").encode()


class ControlsXref(unittest.TestCase):
    def test_section_across_a_page_break(self):
        t = sections.controls_xref(doc())
        self.assertIsNotNone(t)
        self.assertIn("are effective at the reasonable assurance level", t)
        self.assertIn("There were no changes to our internal control", t)     # après le pied de page
        self.assertNotIn("Other Key Information | 43", t)
        self.assertNotIn("repurchase", t)                                     # titre suivant : fin de section
        self.assertNotIn("changes in rates", t)

    def test_needs_the_cross_reference_index(self):
        self.assertIsNone(sections.controls_xref(doc(index=False)))
        self.assertIsNone(sections.item_4_10q(doc()))                         # aucun titre « Item 4 » dans le corps


class IfrsText(unittest.TestCase):
    def test_debt_note_titles(self):
        debt = dict(TC.NOTE_SPECS)["debt_note"]
        for title in ("BONDS PAYABLE", "LONG-TERM BANK LOANS", "Short-term Loans and Bonds Payable", "Borrowings"):
            self.assertTrue(debt.search(title), title)
        for title in ("NOTES AND ACCOUNTS RECEIVABLE, NET", "FINANCIAL ASSETS AT AMORTIZED COST", "PLEDGED ASSETS"):
            self.assertFalse(debt.search(title), title)

    def test_dimensioned_note_blocks(self):
        axis = "ifrs-full:BorrowingsByNameAxis"
        tbs = [{"concept": "ifrs-full:DisclosureOfBorrowingsExplanatory", "dims": [(axis, "tsm:BondsPayableMember")]},
               {"concept": "ifrs-full:DisclosureOfBorrowingsExplanatory", "dims": [(axis, "tsm:LongTermBankLoansMember")]},
               {"concept": "ifrs-full:DisclosureOfLeasesExplanatory", "dims": []},
               {"concept": "ifrs-full:DisclosureOfLeasesExplanatory", "dims": [("ifrs-full:SegmentsAxis", "tsm:XMember")]}]
        by_concept, dimmed = TC.text_blocks_by_concept(tbs)
        self.assertEqual(set(by_concept), {"ifrs-full:DisclosureOfLeasesExplanatory"})   # le bloc sans dimension prime
        self.assertEqual(len(dimmed["ifrs-full:DisclosureOfBorrowingsExplanatory"]), 2)  # un bloc par membre
        self.assertNotIn("ifrs-full:DisclosureOfLeasesExplanatory", dimmed)

    def test_concentration_parent_note(self):
        rdef = ("1178 - Disclosure - Operating Segments Information - Major Customers Representing at Least 10 Percent "
                "of Net Revenue (Detail)")
        self.assertEqual(TC.conc_parent_title(rdef, ifrs=True), "Operating Segments Information")
        # règle us-gaap inchangée : le titre avant « (Details) », sous-titre compris
        self.assertEqual(TC.conc_parent_title("0000071 - Disclosure - Revenue - Concentration (Details)"), "Revenue - Concentration")
        self.assertEqual(TC.conc_parent_title("0000071 - Disclosure - Revenue (Details)"), "Revenue")

    def test_ifrs_equivalents(self):
        self.assertIn("ifrs-full:DisclosureOfPropertyPlantAndEquipmentExplanatory", TC.LEVER_CONCEPTS)
        self.assertIn("ifrs-full:DisclosureOfAccountingJudgementsAndEstimatesExplanatory", TC.LEVER_CONCEPTS)
        self.assertIn("ifrs-full:DisclosureOfRevenueFromContractsWithCustomersExplanatory", TC.REVENUE_CONCEPTS)
        self.assertIn("ifrs-full:DepreciationPropertyPlantAndEquipment", TC.LEVER_FACTS)
        self.assertIn("us-gaap:PropertyPlantAndEquipmentUsefulLife", TC.LEVER_FACTS)


if __name__ == "__main__":
    unittest.main()
