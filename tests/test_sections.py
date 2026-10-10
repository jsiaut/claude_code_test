"""Délimitation des sections par leurs titres (§9.2) : Item 9A, délimitation `d4` (D-0043).

Lancement : python3 -m unittest discover -s tests -t .
"""
import unittest

from pipeline import sections

FILLER = "The Company maintains disclosure controls and procedures designed to ensure timely reporting. " * 4


def page(*paragraphs):
    return ("<html><body>" + "".join(f"<p>{p}</p>" for p in paragraphs) + "</body></html>").encode("utf-8")


class Item9A(unittest.TestCase):
    def test_amendment_without_item_9b(self):
        # un 10-K/A ne reprend que les items qu'il modifie : la puce de sa note explicative
        # n'ouvre pas la section, et l'Item 15 la ferme
        raw = page("EXPLANATORY NOTE", "This Amendment amends the following items:",
                   "•Item 8 - Financial Statements and Supplementary Data;",
                   "•Item 9A - Controls and Procedures; and",
                   "•Item 15 - Exhibits and Financial Statement Schedules.",
                   "Item 8. Financial Statements and Supplementary Data", "Revenue grew. " * 60,
                   "Item 9A. Controls and Procedures", FILLER,
                   "concluded that our internal control over financial reporting was not effective.",
                   "PART IV", "Item 15. Exhibits and Financial Statement Schedules", "Exhibit list. " * 60)
        text = sections.item_9a(raw)
        self.assertTrue(text.startswith("Item 9A. Controls and Procedures"))
        self.assertIn("was not effective", text)
        self.assertNotIn("Item 15", text)
        self.assertNotIn("Revenue grew", text)
        self.assertNotIn("Exhibit list", text)

    def test_annual_report_ends_at_item_9b(self):
        raw = page("Item 9A. Controls and Procedures", FILLER, "Item 9B. Other Information", "None. " * 60,
                   "PART III", "Item 10. Directors", "Board. " * 60)
        text = sections.item_9a(raw)
        self.assertTrue(text.startswith("Item 9A. Controls and Procedures"))
        self.assertNotIn("Item 9B", text)
        self.assertNotIn("None.", text)


if __name__ == "__main__":
    unittest.main()
