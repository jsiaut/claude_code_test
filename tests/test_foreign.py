"""Bloc `foreign` de §14 (D-0042) : cadre comptable des pièces, incorporation par référence des
6-K, invariant (f) — aucune somme entre US GAAP et IFRS.

Lancement : python3 -m unittest discover -s tests -t .
"""
import json
import unittest

from pipeline import assemble
from pipeline import foreign as F


def edge(key, framework, amount="100"):
    o = {"obs_key": key, "framework": framework, "unit": "USD"}
    return {"link_key": "edge:" + key, "tier": "A", "from_group": "NVDA", "to_group": "CP:x", "_obs": o,
            "amount": amount}


class Framework(unittest.TestCase):
    def test_block_framework(self):
        self.assertEqual(F.block_framework({"block_kind": "discovery_note", "framework": "ifrs", "form": "20-F"}), "ifrs")
        self.assertEqual(F.block_framework({"block_kind": "discovery_note", "form": "10-K"}), "us_gaap")
        self.assertEqual(F.block_framework({"block_kind": "related_party_note", "form": "10-K"}), "us_gaap")
        self.assertIsNone(F.block_framework({"block_kind": "discovery_exhibit_header", "form": "8-K"}))

    def test_incorporation_statement(self):
        yes = ("This report on Form 6-K shall be deemed to be incorporated by reference into the registration "
               "statements on Form S-8 (File No. 333-1) of the Company.")
        self.assertTrue(F.INCORP.search(yes))
        self.assertTrue(F.INCORP.search("is incorporated by reference in each of our Registration Statements on Form F-3"))
        self.assertIsNone(F.INCORP.search("The information in this report is not incorporated by reference."))


class SameCik(unittest.TestCase):
    def test_latest_filer_name_wins(self):
        from pipeline import load
        cat = [{"block_kind": "discovery_note", "cik": "0001878848", "filer_name": "IRIS ENERGY LTD",
                "filing_date": "2023-09-13"},
               {"block_kind": "discovery_note", "cik": "0001878848", "filer_name": "IREN Ltd", "filing_date": "2026-08-27"},
               {"block_kind": "related_party_note", "cik": "0001045810", "filer_name": "NVIDIA CORP", "filing_date": "2026-08-27"}]
        self.assertEqual(load.canonical_filers(cat), {"1878848": "IREN Ltd"})


class InvariantF(unittest.TestCase):
    def cell(self, keys):
        return {"measure": "counterparty_exposure", "subject": "NVDA", "counterparty": "CP:x", "period_end": "2026-06-30",
                "breakdown_key": "none", "as_of": "2026-10-07", "status": "computed", "value": 200, "nd_reason": None,
                "flags": json.dumps({"links": keys})}

    def test_sum_across_frameworks_is_excluded(self):
        edges = [edge("a", "us_gaap"), edge("b", "ifrs")]
        c = self.cell(["edge:a", "edge:b"])
        out = assemble.invariants([c], edges, [], None)
        self.assertEqual((c["status"], c["nd_reason"], c["value"]), ("not_determinable", "mixed_framework", None))
        self.assertEqual(out[0]["invariant"], "f")

    def test_contract_without_framework_does_not_trigger(self):
        edges = [edge("a", "us_gaap"), edge("b", None)]
        c = self.cell(["edge:a", "edge:b"])
        self.assertEqual(assemble.invariants([c], edges, [], None), [])
        self.assertEqual(c["status"], "computed")


if __name__ == "__main__":
    unittest.main()
