"""Bloc montages (D-0046) : termes qualifiants hors du nom du déposant, fenêtres de paragraphes.

Lancement : python3 -m unittest discover -s tests -t .
"""
import unittest

from pipeline import montages as M


class Qualify(unittest.TestCase):
    def test_own_name_never_qualifies(self):
        meta, owl, other = (M.qualify_rx("Meta Platforms, Inc."), M.qualify_rx("Blue Owl Real Estate Net Lease Trust"),
                            M.qualify_rx("Boeing Co"))
        self.assertIsNone(meta.search("Meta reported revenue growth."))
        self.assertTrue(meta.search("an affiliate of funds managed by Blue Owl Capital, Inc."))
        self.assertIsNone(owl.search("Blue Owl Capital Inc. manages the fund."))
        self.assertTrue(owl.search("a campus leased to Meta Platforms, Inc."))
        self.assertTrue(other.search("Beignet Investor LLC 6.581% notes"))
        self.assertIsNone(other.search("Hyperion Refinance S.a r.l (dba Howden Group)"))   # Hyperion seul : ambigu
        self.assertIsNone(other.search("metadata and Metaverse"))                           # mot entier, majuscule


class Windows(unittest.TestCase):
    def test_two_paragraphs_each_side_merged(self):
        paras = [f"p{i}" for i in range(12)]
        paras[3] = "Blue Owl"
        paras[6] = "Blue Owl again"
        paras[11] = "Beignet"
        self.assertEqual(M.windows(paras, M.qualify_rx("Meta Platforms, Inc.")), [[1, 12]])   # fenêtres contiguës fondues


if __name__ == "__main__":
    unittest.main()
