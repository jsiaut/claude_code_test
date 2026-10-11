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


class GalaxyAmendment(unittest.TestCase):
    """D-0049, point 11 : pièces écartées, ordre des classes, plus récent d'abord."""

    @staticmethod
    def _d(filer, form, ft, f, date):
        return {"filer": filer, "form": form, "file_type": ft, "file": f, "file_date": date, "adsh": "x"}

    def test_exclusions(self):
        sp, d = S["galaxy_helios"], self._d
        self.assertIsNotNone(M._excluded(d("Galaxy Digital Inc.", "424B3", "424B3", "a.htm", "2026-01-01"), sp))
        self.assertIsNotNone(M._excluded(d("Galaxy Digital Inc.", "8-K", "EX-99.2", "exhibit992-q12026overvie.htm", "2026-04-28"), sp))
        self.assertIsNotNone(M._excluded(d("Galaxy Digital Inc.", "8-K", "EX-99.1", "glxy-2026331xpressrelease.htm", "2026-04-28"), sp))
        self.assertIsNone(M._excluded(d("Galaxy Digital Inc.", "8-K", "EX-4.1", "closing8-kxex41indenture.htm", "2026-07-28"), sp))
        self.assertIsNone(M._excluded(d("CoreWeave, Inc.", "424B4", "424B4", "x.htm", "2025-03-31"), sp))

    def test_order(self):
        sp, d = S["galaxy_helios"], self._d
        docs = [d("Galaxy Digital Inc.", "10-Q", "10-Q", "q1", "2026-05-08"), d("Galaxy Digital Inc.", "10-Q", "10-Q", "q2", "2026-08-10"),
                d("Galaxy Digital Inc.", "8-K", "EX-4.1", "ind", "2026-07-28"), d("MSD Investment Corp.", "10-Q", "10-Q", "m", "2026-05-14")]
        self.assertEqual([x["file"] for x in sorted(docs, key=lambda x: M._order_key(x, 0, sp))], ["m", "ind", "q2", "q1"])

    def test_first_montages_keep_date_order(self):
        for mid in ("meta_hyperion", "athene_whco"):
            a = {"filer": "X", "form": "8-K", "file": "a", "file_date": "2025-01-01", "adsh": "1"}
            self.assertLess(M._order_key(a, 0, S[mid]), M._order_key(dict(a, file_date="2026-01-01"), 0, S[mid]))


class CounterpartyMembership(unittest.TestCase):
    """D-0049, point 13 : filiale d'une contrepartie rattachée par extrait au groupe de la contrepartie."""

    def test_vehicle_joins_counterparty_group_only_by_extract(self):
        from pipeline import entities as E
        cfg = {"labs": [], "confirmed_entities": [
            {"name": "Galaxy Helios I LLC", "group": "CP:galaxy digital inc", "treatment": "consolidated_subsidiary",
             "valid_from": "none", "decision": "D-0049", "block": "x", "accession": "y",
             "quote": "Galaxy Helios I LLC, a wholly owned subsidiary of GDH LP"}]}
        rows, reg = E.build({"meta": {}}, cfg, {"Galaxy Helios LLC": False, "Galaxy Helios I LLC": False})
        self.assertEqual(E.resolve(reg, "Galaxy Helios I LLC", "2026-06-30")[1], "CP:galaxy digital inc")
        self.assertEqual(E.resolve(reg, "Galaxy Helios LLC", "2026-06-30")[1], "CP:galaxy helios llc")   # pas de fusion
        kinds = {r["name"]: r["group_kind"] for r in rows if r["record_kind"] == "entity"}
        self.assertEqual(kinds["Galaxy Helios I LLC"], "counterparty_group")


if __name__ == "__main__":
    unittest.main()
