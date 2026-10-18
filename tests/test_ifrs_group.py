"""Groupe en IFRS (D-0056, point 5) : candidats ifrs-full des grandeurs, cadre des notes, totaux des
contrôles C1 et C2, noms qualifiants des 6-K propres à TSMC.

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import config, controls, foreign, quantities, sixk


class IfrsCandidates(unittest.TestCase):
    def test_after_us_gaap_and_known_quantities(self):
        cfg = config.load()
        q = quantities.quantity_definitions(cfg)
        for name, cands in cfg["concept_anchors_ifrs"].items():
            self.assertIn(name, q, name)
            got = q[name]["candidates"]
            first_ifrs = next(i for i, c in enumerate(got) if c.startswith("ifrs-full:"))
            # les candidats us-gaap passent d'abord ; aucun us-gaap après un ifrs-full
            self.assertTrue(all(c.startswith("ifrs-full:") for c in got[first_ifrs:]), name)
            self.assertEqual(got[first_ifrs:], [f"ifrs-full:{c}" for c in dict.fromkeys(cands)], name)

    def test_first_present_in_filer_linkbase(self):
        q = quantities.quantity_definitions()["capex_cash"]
        ifrs_filer = {"ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": {"cash_flow"}}
        us_filer = {"us-gaap:PaymentsToAcquirePropertyPlantAndEquipment": {"cash_flow"}}

        def chosen(present):
            return next((c for c in q["candidates"] if (present.get(c) or set()) & q["statements"]), None)
        self.assertEqual(chosen(ifrs_filer), "ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities")
        self.assertEqual(chosen(us_filer), "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment")


class Framework(unittest.TestCase):
    def test_notes_of_an_ifrs_group(self):
        self.assertEqual(foreign.block_framework({"block_kind": "debt_note", "group_id": "TSM"}), "ifrs")
        self.assertEqual(foreign.block_framework({"block_kind": "debt_note", "group_id": "NVDA"}), "us_gaap")
        self.assertIsNone(foreign.block_framework({"block_kind": "exhibit_body", "group_id": "TSM"}))

    def test_control_totals(self):
        self.assertIn("ifrs-full:Assets", controls.BS_TOTALS)
        self.assertIn("ifrs-full:CashFlowsFromUsedInOperatingActivities", controls.CF_TOTALS)


class SixKNames(unittest.TestCase):
    def test_names_for_tsmc_only(self):
        tsm, nbis = sixk.lexicon_rx("TSM"), sixk.lexicon_rx("NBIS")
        self.assertTrue(tsm.search("a capacity agreement with Intel"))
        self.assertTrue(tsm.search("Micron announced"))
        self.assertFalse(nbis.search("Micron announced"))
        self.assertFalse(tsm.search("intel inside"))      # nom de groupe : casse du lexique
        self.assertTrue(nbis.search("a loan from the bank"))


if __name__ == "__main__":
    unittest.main()
