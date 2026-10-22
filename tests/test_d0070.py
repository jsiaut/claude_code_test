"""D-0070 : localisation d'une citation qui porte des points de conduite (ligne de tableau d'un
prospectus).

Lancement : python3 -m unittest discover -s tests -t .
"""
import re
import time
import unittest

from pipeline import textnorm


def word_pattern_before(word):
    """Motif d'un mot avant D-0070 : un groupe par signe."""
    parts = []
    for ch in word:
        if ch.isalnum():
            parts.append(re.escape(ch))
        else:
            parts.append(r"(?:" + textnorm._ENT + r"|<[^>]*>|[^\w\s<>]){1,3}")
    return textnorm._TAGS.join(parts)


DOTS = "." * 68
ROW = ("<tr><td><p>Entities affiliated with Alpha Wave<sup>(2)</sup> " + DOTS + "</p></td>"
       "<td><p>{shares}</p></td><td><p>${amount}</p></td></tr>")


class DotLeaders(unittest.TestCase):

    def test_row_with_leaders_is_located_quickly(self):
        # la première ligne porte le même libellé et d'autres chiffres : la recherche y échoue
        # avant de trouver la bonne, ce qui faisait exploser le retour arrière d'un groupe par point
        raw = ("<table>" + ROW.format(shares="1,123,398", amount="99,999,947")
               + ROW.format(shares="1,241,982", amount="44,999,989") + "</table>")
        quote = "Entities affiliated with Alpha Wave(2) " + DOTS + " | 1,241,982 | $44,999,989"
        t0 = time.time()
        r = textnorm.locate_in_raw(raw.encode("utf-8"), quote)
        self.assertLess(time.time() - t0, 2.0)
        self.assertIsNotNone(r)
        found = raw.encode("utf-8")[r[0]:r[1]].decode()
        self.assertTrue(found.startswith("Entities affiliated with Alpha Wave"))
        self.assertTrue(found.endswith("44,999,989"))
        self.assertIn("1,241,982", found)
        self.assertNotIn("1,123,398", found)

    def test_short_or_unmatched_runs_keep_their_pattern(self):
        # le motif de toute citation déjà lue reste le même : moins de cinq signes, ou des signes
        # que la classe de ponctuation ne reconnaît pas (« _ » est un caractère de mot)
        for w in ("[****]", "Inc.", "(“Microsoft”)", "[___________]", "USD", "$1,000.00", "...."):
            self.assertEqual(textnorm._word_pattern(w), word_pattern_before(w), w)
        self.assertNotEqual(textnorm._word_pattern("....."), word_pattern_before("....."))


if __name__ == "__main__":
    unittest.main()
