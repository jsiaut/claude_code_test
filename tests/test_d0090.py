"""D-0090 : Anthropic, laboratoire devenu déposant, est un groupe de config.yaml sous sa référence de laboratoire ;
`company_tickers.json` résout son symbole comme pour tout groupe (§10.1).

Lancement : python3 -m unittest tests.test_d0090 -v
"""
import unittest

from pipeline import config, phase0, render

REF = "LAB:ANTHROPIC"


class _Edgar:
    def __init__(self, rows):
        self._rows = rows

    def tickers(self):
        return {str(i): r for i, r in enumerate(self._rows)}


class GroupTicker(unittest.TestCase):
    def test_a_group_is_its_ticker_unless_mapped(self):
        cfg = {"group_tickers": {REF: "ANT"}}
        self.assertEqual(phase0.group_ticker("NVDA", cfg), "NVDA")
        self.assertEqual(phase0.group_ticker(REF, cfg), "ANT")
        self.assertEqual(phase0.group_ticker("nvda", {}), "NVDA")

    def test_the_ticker_file_resolves_the_cik(self):
        e = _Edgar([{"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
                    {"cik_str": 2130357, "ticker": "ANT", "title": "Anthropic, PBC"}])
        cfg = {"groups": {"NVDA": "0001045810", REF: "0000000001"}, "group_tickers": {REF: "ANT"}, "predecessors": {}}
        groups, excluded = phase0.resolve(e, cfg)
        self.assertEqual(excluded, [])
        self.assertEqual(groups[REF]["cik"], "0002130357")           # le fichier fait foi, pas le CIK indicatif
        self.assertFalse(groups[REF]["hint_matches"])
        self.assertEqual(groups["NVDA"]["cik"], "0001045810")

    def test_an_unresolved_ticker_excludes_the_group(self):
        cfg = {"groups": {REF: "0002130357"}, "group_tickers": {REF: "ANT"}, "predecessors": {}}
        groups, excluded = phase0.resolve(_Edgar([]), cfg)
        self.assertEqual(groups, {})
        self.assertEqual([x["group"] for x in excluded], [REF])


class AnthropicIsAGroupAndALab(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load()

    def test_configuration(self):
        cfg = self.cfg
        self.assertEqual(cfg["groups"][REF], "0002130357")
        self.assertEqual(cfg["group_tickers"], {REF: "ANT"})
        self.assertIn("Anthropic", cfg["labs"])                       # reste un laboratoire
        self.assertIn(REF, [g for e in cfg["group_entry"] for g in e["groups"]])
        self.assertEqual(sorted(cfg["reporting_start"][REF]), ["fiscal_year", "quarter"])
        # tout groupe a sa date d'entrée, une seule fois (§9.6)
        entered = [g for e in cfg["group_entry"] for g in e["groups"]]
        self.assertEqual(sorted(entered), sorted(cfg["groups"]))

    def test_the_cik_seed_is_the_only_head(self):
        # l'entrée d'entité confirmée qui tenait le rôle de tête ferait double emploi avec l'entité du CIK
        heads = [c for c in self.cfg["confirmed_entities"] if c.get("group") == REF and c.get("treatment") == "parent"]
        self.assertEqual(heads, [])

    def test_render_names_the_group(self):
        self.assertEqual(render.GROUP_NAMES[REF], "Anthropic")
        self.assertEqual(render.group_label(REF), "Anthropic")
        self.assertIn(len(self.cfg["groups"]), render.NUM_FR)


if __name__ == "__main__":
    unittest.main()
