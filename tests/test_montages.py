"""Bloc montages (D-0046, D-0049) : termes qualifiants hors du nom du déposant, fenêtres de paragraphes.

Lancement : python3 -m unittest discover -s tests -t .
"""
import unittest

from pipeline import montages as M

S = M.specs()


class Qualify(unittest.TestCase):
    def test_own_name_never_qualifies(self):
        sp = S["meta_hyperion"]
        meta, owl, other = (M.qualify_rx("Meta Platforms, Inc.", sp), M.qualify_rx("Blue Owl Real Estate Net Lease Trust", sp),
                            M.qualify_rx("Boeing Co", sp))
        self.assertIsNone(meta.search("Meta reported revenue growth."))
        self.assertTrue(meta.search("an affiliate of funds managed by Blue Owl Capital, Inc."))
        self.assertIsNone(owl.search("Blue Owl Capital Inc. manages the fund."))
        self.assertTrue(owl.search("a campus leased to Meta Platforms, Inc."))
        self.assertTrue(other.search("Beignet Investor LLC 6.581% notes"))
        self.assertIsNone(other.search("Hyperion Refinance S.a r.l (dba Howden Group)"))   # Hyperion seul : ambigu
        self.assertIsNone(other.search("metadata and Metaverse"))                           # mot entier, majuscule

    def test_apollo_and_athene_do_not_qualify_each_other(self):
        sp = S["athene_whco"]
        ath, avgo = M.qualify_rx("Athene Holding Ltd.", sp), M.qualify_rx("Broadcom Inc.", sp)
        self.assertIsNone(ath.search("Athene is a subsidiary of Apollo Global Management."))
        self.assertTrue(ath.search("a capital solution agreement with Broadcom Inc."))
        self.assertTrue(ath.search("WHCO has a purchase obligation"))
        self.assertIsNone(avgo.search("Broadcom reported revenue."))
        self.assertTrue(avgo.search("funds managed by Apollo"))

    def test_helios_only_in_galaxy_or_coreweave(self):
        sp = S["galaxy_helios"]
        glxy, crwv, other = (M.qualify_rx("Galaxy Digital Inc.", sp), M.qualify_rx("CoreWeave, Inc.", sp),
                             M.qualify_rx("Helios Technologies, Inc.", sp))
        self.assertTrue(glxy.search("the Helios data center campus"))
        self.assertIsNone(glxy.search("Galaxy reported trading revenue."))
        self.assertTrue(crwv.search("our lease at Helios"))
        self.assertIsNone(crwv.search("CoreWeave reported revenue."))
        self.assertIsNone(other.search("Helios Technologies reported revenue."))
        self.assertTrue(other.search("leased to CoreWeave"))


class Windows(unittest.TestCase):
    def test_two_paragraphs_each_side_merged(self):
        paras = [f"p{i}" for i in range(12)]
        paras[3] = "Blue Owl"
        paras[6] = "Blue Owl again"
        paras[11] = "Beignet"
        rx = M.qualify_rx("Meta Platforms, Inc.", S["meta_hyperion"])
        self.assertEqual(M.windows(paras, rx), [[1, 12]])   # fenêtres contiguës fondues


if __name__ == "__main__":
    unittest.main()
