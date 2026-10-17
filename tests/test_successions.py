"""Successions (§10.1, D-0055) : la date de succession d'un prédécesseur se lit dans config.yaml, et ses
rapports périodiques de périodes closes après elle sont des rapports de filiale, hors du groupe.

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import config
from pipeline import graph
from pipeline import phase0
from pipeline.graph import normalize_name


def p0(meta):
    return {"meta": meta}


class Successions(unittest.TestCase):
    def test_date_lue_dans_la_configuration(self):
        cfg = config.load()
        rows = graph.seed_entities(p0({"0001649338": {"group": "AVGO", "is_predecessor": True,
                                                      "name": "Broadcom Ltd", "formerNames": []}}), cfg)
        m = [r for r in rows if r["entity_id"] == "cik:0001649338" and r["record_kind"] == "membership"]
        self.assertEqual((m[0]["ref"], m[0]["valid_to"]), ("AVGO", "2018-04-04"))
        self.assertEqual(m[0]["evidence"], "8-K12B 0001193125-18-107559")

    def test_predecesseur_filiale_apres_la_succession(self):
        """Garde de D-0055 : un prédécesseur rattaché par extrait après sa succession (AAM, filiale d'AGM au
        1er janvier 2022) reste tête de son groupe avant la date ; une autre entité datée forme son propre groupe."""
        from pipeline import entities as E
        cfg = dict(config.load())
        cfg["confirmed_entities"] = [
            {"name": "Apollo Asset Management, Inc.", "group": "APO", "treatment": "consolidated_subsidiary",
             "valid_from": "2022-01-01", "decision": "D-0055", "block": "x", "accession": "y", "quote": "z"},
            {"name": "Athene Holding Ltd.", "group": "APO", "treatment": "consolidated_subsidiary",
             "valid_from": "2022-01-01", "decision": "D-0055", "block": "x", "accession": "y", "quote": "z"}]
        cfg["own_entities"], cfg["entity_aliases"] = [], []
        meta = {"0001411494": {"group": "APO", "is_predecessor": True, "name": "Apollo Asset Management, Inc.",
                               "formerNames": []},
                "0001858681": {"group": "APO", "is_predecessor": False, "name": "Apollo Global Management, Inc.",
                               "formerNames": []}}
        rows, reg = E.build(p0(meta), cfg, {})
        aam = "cik:0001411494"
        self.assertEqual(reg.group_at(aam, "2021-06-30"), "APO")
        self.assertEqual(reg.group_at(aam, "2022-06-30"), "APO")
        self.assertEqual(reg.treatment_at(aam, "2022-06-30"), "consolidated_subsidiary")
        self.assertFalse(any(r["entity_id"] == aam and str(r["ref"]).startswith("CP:") for r in rows
                             if r["record_kind"] == "membership"))
        ahl = reg.names[normalize_name("Athene Holding Ltd.")]
        self.assertEqual(reg.group_at(ahl, "2021-06-30"), "CP:athene holding ltd")
        self.assertEqual(reg.group_at(ahl, "2022-06-30"), "APO")

    def test_rapport_de_filiale_apres_la_succession(self):
        succ = {"0000000001": {"date": "2022-01-01"}}
        base = {"is_predecessor": True, "filer_cik": "0000000001"}
        self.assertTrue(phase0.post_succession({**base, "form": "10-Q", "reportDate": "2022-03-31"}, succ))
        # exercice clos avant la succession, déposé après : rapport du groupe
        self.assertFalse(phase0.post_succession({**base, "form": "10-K", "reportDate": "2021-12-31"}, succ))
        # les autres dépôts du prédécesseur restent (8-K du jour de la succession)
        self.assertFalse(phase0.post_succession({**base, "form": "8-K", "reportDate": "2022-01-01"}, succ))
        # le successeur n'est jamais visé
        self.assertFalse(phase0.post_succession({**base, "is_predecessor": False, "form": "10-Q",
                                                 "reportDate": "2022-03-31"}, succ))


if __name__ == "__main__":
    unittest.main()
