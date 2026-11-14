"""D-0085, point 13 : une ligne du catalogue des 6-K échappe U+2028 et U+2029, que str.splitlines() prendrait pour des
fins de ligne ; la valeur lue ne change pas.

Lancement : python3 -m unittest tests.test_d0085 -v
"""
import json
import unittest

from pipeline import sixk


class LigneDuCatalogue(unittest.TestCase):
    def test_sans_separateur_brut(self):
        b = {"text": "a b c é", "n": 1}
        s = sixk._line(b)
        self.assertNotIn(" ", s)
        self.assertNotIn(" ", s)
        self.assertTrue(s.endswith("\n"))
        self.assertEqual(len(s.splitlines()), 1)
        self.assertEqual(json.loads(s), b)

    def test_catalogue_present_lisible_par_splitlines(self):
        if not sixk.CATALOG.exists():
            self.skipTest("catalogue des 6-K absent (conteneur neuf)")
        t = sixk.CATALOG.read_text(encoding="utf-8")
        self.assertEqual([json.loads(x) for x in t.splitlines() if x.strip()],
                         [json.loads(x) for x in t.split("\n") if x.strip()])


if __name__ == "__main__":
    unittest.main()
