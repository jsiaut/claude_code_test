"""Suffixes de forme juridique (D-0022, D-0054) : une dénomination légale complète est une entité propre,
y compris sous une forme ponctuée (« L.P. », « p.l.c. », « S.à r.l. ») ou étrangère (AS, ASA, AB, Oy, ehf, DA, Ltda).

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import entities as E
from pipeline.graph import normalize_name


def legal(name):
    n = normalize_name(name)
    return bool(E.LEGAL_SUFFIX.search(n)) and not E.DESCRIPTIVE.match(n)


class LegalSuffix(unittest.TestCase):
    def test_formes_ponctuees(self):
        for name in ("Sandton Capital Solutions Master Fund V, L.P.", "THE LAW DEBENTURE TRUST CORPORATION p.l.c.",
                     "AF Realizations S.à r.l.", "Dell International L.L.C.", "JPMorgan Chase Bank, N.A.",
                     "Wells Fargo Bank, National Association", "U.S. Bank Trust Company, National Association"):
            self.assertTrue(legal(name), name)

    def test_formes_etrangeres(self):
        for name in ("Aker ASA", "Nscale Drift II AS", "Skandinaviska Enskilda Banken AB", "Nebius Compute II Oy",
                     "Nscale Services Iceland III ehf", "Nscale Norway DC DA", "Nscale Services Japan GK",
                     "Pátria Investimentos Ltda"):
            self.assertTrue(legal(name), name)

    def test_descriptions_et_noms_courts(self):
        for name in ("certain lenders", "the holders", "an affiliate of OpenAI Group PBC", "Macquarie", "Sandton",
                     "City National Bank", "Texas"):
            self.assertFalse(legal(name), name)


if __name__ == "__main__":
    unittest.main()
