"""Item 13 d'un 10-K (D-0055) : pour un groupe qui ne dépose aucune circulaire, l'information de l'Item 404
se lit dans la partie III du rapport annuel, de l'Item 13 au titre d'item suivant ; un simple renvoi à une
circulaire n'est pas une section.

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import sections

BODY = "<p>Tax Receivable Agreements. We used a portion of the proceeds to purchase interests from our partners.</p>" * 30


def doc(item13):
    return ("<html><body><p>Table of Contents</p><p>Item 13. Certain Relationships and Related Transactions | 250</p>"
            "<p>Item 12. Security Ownership of Certain Beneficial Owners</p><p>Ownership table.</p>"
            f"<p>Item 13. Certain Relationships and Related Transactions, and Director Independence</p>{item13}"
            "<p>Item 14. Principal Accountant Fees and Services</p><p>Fees paid to the auditor.</p>"
            "</body></html>").encode()


class Item13(unittest.TestCase):
    def test_section_redigee(self):
        t = sections.item_13_10k(doc(BODY))
        self.assertIsNotNone(t)
        self.assertIn("Tax Receivable Agreements", t)
        self.assertNotIn("Principal Accountant Fees", t)
        self.assertNotIn("Ownership table", t)

    def test_renvoi_a_une_circulaire(self):
        renvoi = "<p>The information required by this item is incorporated by reference to our Proxy Statement.</p>"
        self.assertIsNone(sections.item_13_10k(doc(renvoi)))


if __name__ == "__main__":
    unittest.main()
