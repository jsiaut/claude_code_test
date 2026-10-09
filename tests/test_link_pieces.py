"""Pièces de lien d'une paire (§3.4, D-0039) : l'extrait nomme les deux parties, et les parties
de la ligne sont S et C. Une ligne d'un tiers qui nomme l'une des deux n'est pas une pièce.

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import circularity as C
from pipeline import entities as E
from pipeline.graph import normalize_name


def entity(eid, name, group):
    return [{"record_kind": "entity", "entity_id": eid, "name": name, "normalized_name": normalize_name(name),
             "status": "confirmed"},
            {"record_kind": "membership", "entity_id": eid, "ref": group, "status": "confirmed"}]


REG = E.Registry(entity("e:nvda", "NVIDIA Corporation", "NVDA") + entity("e:crwv", "CoreWeave, Inc.", "CRWV")
                 + entity("e:iren", "IREN Limited", "CP:iren ltd"))


def line(group, payer, payee, quote):
    return {"kind": "observation", "validation_state": "valid", "link_category": "L1", "group_id": group,
            "payer": payer, "payee": payee, "counterparty_name": payee, "quote": quote,
            "event_date": "2025-06-30", "obs_key": f"{group}/{payer}/{payee}"}


class LinkPieces(unittest.TestCase):
    def setUp(self):
        self.pair = C.Pair("NVDA", "CRWV")
        self.s_names = C.names_of_group(REG, "NVDA")
        # le défaut corrigé : la contrepartie d'une ligne déposée par C (« NVIDIA Corporation ») entrait
        # dans les noms de C ; la règle des parties doit tenir même avec cet ensemble
        self.c_names = C.names_of_group(REG, "CRWV") | {"NVIDIA Corporation"}

    def pieces(self, *obs):
        return [o["obs_key"] for o in C.link_pieces(self.pair, list(obs), REG, self.s_names, self.c_names)]

    def test_line_of_c_naming_s_is_a_piece(self):
        o = line("CRWV", "the Company", "NVIDIA Corporation",
                 "In connection with the agreement, the Company issued to NVIDIA Corporation a warrant.")
        self.assertEqual(self.pieces(o), [o["obs_key"]])

    def test_third_party_line_naming_s_is_not_a_piece(self):
        o = line("CP:iren ltd", "the Company", "NVIDIA Corporation",
                 "In connection with its arrangements with NVIDIA Corporation for the supply of GPUs, the Company granted rights.")
        self.assertEqual(self.pieces(o), [])

    def test_line_of_s_about_another_client_is_not_a_piece(self):
        o = line("NVDA", "OpenAI", "NVIDIA Corporation",
                 "OpenAI, as the tenant, will utilize capacity to deploy the platform of NVIDIA Corporation.")
        self.assertEqual(self.pieces(o), [])

    def test_the_group_designates_the_filer(self):
        pair = C.Pair("NVDA", "CP:iren ltd")
        o = line("CP:iren ltd", "the Company", "NVIDIA Corporation",
                 "This amount will be capitalized as part of the cost of the GPUs acquired from NVIDIA Corporation "
                 "and is recognized as the underlying GPUs are received by the Group.")
        got = C.link_pieces(pair, [o], REG, C.names_of_group(REG, "NVDA"), C.names_of_group(REG, "CP:iren ltd"))
        self.assertEqual([x["obs_key"] for x in got], [o["obs_key"]])

    def test_party_groups_maps_self_reference_to_the_filer(self):
        o = line("CP:iren ltd", "the Company", "NVIDIA Corporation", "")
        self.assertEqual(C.party_groups(o, REG), {"CP:iren ltd", "NVDA"})


if __name__ == "__main__":
    unittest.main()
