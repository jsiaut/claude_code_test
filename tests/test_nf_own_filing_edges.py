"""Document d'enregistrement de la tête d'un non-déposant (D-0054, point 13) : « the Company » de ses
lignes désigne la tête du groupe, confirmée par extrait, et non un nom en attente.

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import entities as E
from pipeline import links
from pipeline.graph import normalize_name


def entity(eid, name, group, rule="executor_decision"):
    return [{"record_kind": "entity", "entity_id": eid, "name": name, "normalized_name": normalize_name(name),
             "status": "confirmed"},
            {"record_kind": "membership", "entity_id": eid, "ref": group, "status": "confirmed", "valid_from": "none",
             "valid_to": None, "consolidation_treatment": "parent", "resolution_rule": rule}]


REG = E.Registry(entity("name:nscale ltd", "Nscale Limited", "NF:NSCALE")
                 + entity("cik:1045810", "NVIDIA Corporation", "NVDA", rule="same_cik"))


def line(payer, payee, group="NF:NSCALE"):
    return {"kind": "observation", "validation_state": "valid", "obs_key": "k1", "family": "financing",
            "edge_type": "convertible_or_safe", "counterparty_evidence": "named", "counterparty_name": payer,
            "payer": payer, "payee": payee, "group_id": group, "tier": "C", "stage": "signed",
            "amount": "1000000000", "unit": "USD", "currency": "USD", "amount_nature": "financing_cash",
            "amount_qualifier": "exact", "period_end": "2026-09-15", "knowledge_date": "2026-09-18"}


class OwnFilingEdges(unittest.TestCase):
    def test_the_company_designe_la_tete(self):
        edges, pend = links.build_edges([line("NVIDIA Corporation", "the Company")], REG)
        self.assertEqual((edges[0]["from_group"], edges[0]["to_group"]), ("NVDA", "NF:NSCALE"))
        self.assertEqual(edges[0]["to_entity"], "name:nscale ltd")

    def test_bloc_d_un_tiers_inchange(self):
        # bloc d'un déposant découvert : « the Company » reste ce déposant (groupe de contrepartie)
        edges, _ = links.build_edges([line("NVIDIA Corporation", "the Company", group="CP:acme inc")], REG)
        self.assertEqual(edges[0]["to_group"], "CP:acme inc")


if __name__ == "__main__":
    unittest.main()
