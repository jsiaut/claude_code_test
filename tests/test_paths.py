"""Bloc `paths` de §14 (D-0041) : cycles orientés de longueur 2 ou 3, `temporal`, pièces des
paires d'arêtes consécutives et conclusion.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import json
import unittest

from pipeline import entities as E
from pipeline import paths as P
from pipeline.graph import normalize_name


def entity(eid, name, group):
    return [{"record_kind": "entity", "entity_id": eid, "name": name, "normalized_name": normalize_name(name),
             "status": "confirmed"},
            {"record_kind": "membership", "entity_id": eid, "ref": group, "status": "confirmed"}]


REG = E.Registry(entity("e:nvda", "NVIDIA Corporation", "NVDA") + entity("e:crwv", "CoreWeave, Inc.", "CRWV")
                 + entity("e:oai", "OpenAI OpCo, LLC", "LAB:OPENAI"))
GROUPS = {"NVDA", "CRWV"}
GW = {g: {"window_start": dt.date(2021, 1, 1)} for g in GROUPS}


def edge(f, t, family, date, key, stage="recognized", event="recognition", filer=None, cp=None):
    o = {"obs_key": key, "group_id": filer or f, "counterparty_name": cp, "period_start": None, "period_end": None,
         "event_type": event}
    return {"link_key": "edge:" + key, "from_group": f, "to_group": t, "family": family, "stage": stage,
            "elimination_status": "not_applicable", "_obs": o, "_date": dt.date.fromisoformat(date)}


def piece(key, filer, payer, payee, cp, quote, cat="L1"):
    return {"obs_key": key, "kind": "observation", "validation_state": "valid", "link_category": cat,
            "group_id": filer, "payer": payer, "payee": payee, "counterparty_name": cp, "quote": quote,
            "event_date": "2025-06-30"}


class Cycles(unittest.TestCase):
    def test_two_and_three_cycles_through_a_group(self):
        edges = [edge("NVDA", "LAB:OPENAI", "financing", "2025-09-30", "a"),
                 edge("LAB:OPENAI", "CRWV", "commercial", "2025-12-31", "b"),
                 edge("CRWV", "NVDA", "commercial", "2026-03-31", "c"),
                 edge("NVDA", "CRWV", "financing", "2025-06-30", "d")]
        found = P.cycles(P.graph(edges), GROUPS)
        self.assertEqual(found, [("CRWV", "NVDA"), ("CRWV", "NVDA", "LAB:OPENAI")])

    def test_repayment_and_intragroup_edges_are_not_path_edges(self):
        edges = [edge("NVDA", "CRWV", "financing", "2025-06-30", "d"),
                 edge("CRWV", "NVDA", "financing", "2025-09-30", "r", stage="settled", event="repayment"),
                 edge("NVDA", "NVDA", "commercial", "2025-09-30", "i")]
        self.assertEqual(P.cycles(P.graph(edges), GROUPS), [])

    def test_temporal_uses_the_closest_choice_of_edges(self):
        steps = [[edge("A", "B", "financing", "2021-03-31", "x"), edge("A", "B", "financing", "2025-03-31", "y")],
                 [edge("B", "A", "commercial", "2025-12-31", "z")]]
        self.assertEqual(P.temporal(steps), ("yes", 3))
        self.assertEqual(P.temporal([[steps[0][0]], steps[1]])[0], "no")
        self.assertEqual(P.temporal([[], steps[1]]), ("unknown", None))


class Conclusion(unittest.TestCase):
    def measures(self, edges, obs):
        cells, ps = P.path_measures(edges, obs, REG, GROUPS, GW, "2026-10-07")
        return {c["breakdown_key"]: (c["value_text"], json.loads(c["flags"])) for c in cells}

    def test_two_cycle_with_pair_piece_is_documented(self):
        edges = [edge("NVDA", "CRWV", "financing", "2025-06-30", "d"),
                 edge("CRWV", "NVDA", "commercial", "2025-09-30", "c", filer="CRWV", cp="NVIDIA Corporation")]
        obs = [piece("p", "CRWV", "NVIDIA Corporation", "the Company", "NVIDIA Corporation",
                     "The Company purchases GPUs from NVIDIA Corporation, which funded the Company for these purchases.")]
        v, f = self.measures(edges, obs)["CRWV>NVDA"]
        self.assertEqual(v, "documented_dependency")
        self.assertEqual(f["step_pieces"], [["p"], ["p"]])

    def test_three_cycle_needs_a_piece_naming_three_parties_at_each_join(self):
        edges = [edge("NVDA", "LAB:OPENAI", "financing", "2025-09-30", "a"),
                 edge("LAB:OPENAI", "CRWV", "commercial", "2025-12-31", "b"),
                 edge("CRWV", "NVDA", "commercial", "2026-03-31", "c")]
        # nomme OpenAI et NVIDIA seulement : pièce de la paire, pas de la jonction en OpenAI
        obs = [piece("q", "NVDA", "NVIDIA Corporation", "OpenAI OpCo, LLC", "OpenAI OpCo, LLC",
                     "NVIDIA Corporation invested in OpenAI OpCo, LLC to fund purchases of NVIDIA systems.")]
        v, f = self.measures(edges, obs)["CRWV>NVDA>LAB:OPENAI"]
        self.assertEqual(v, "commercial_with_financing")
        self.assertEqual(f["step_pieces"], [[], [], []])
        self.assertEqual(f["temporal"], "yes")

    def test_commercial_only_cycle_is_reciprocal(self):
        edges = [edge("NVDA", "CRWV", "commercial", "2025-06-30", "x"),
                 edge("CRWV", "NVDA", "commercial", "2025-06-30", "y")]
        v, f = self.measures(edges, [])["CRWV>NVDA"]
        self.assertEqual(v, "reciprocal_commercial_only")


if __name__ == "__main__":
    unittest.main()
