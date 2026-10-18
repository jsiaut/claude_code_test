"""ASML et SK hynix, émetteurs privés étrangers, et Samsung, non-déposant (D-0057) : noms qualifiants des unités
6-K de chaque groupe, jamais le groupe lui-même ; terme de Samsung dans la piste des non-déposants ; nom au rendu de
chaque groupe de config.yaml.

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import config, render, sixk
from pipeline import discovery as D
from pipeline import nf_discovery as NF


class NomsDes6K(unittest.TestCase):
    def test_asml_jamais_son_propre_nom(self):
        rx = sixk.lexicon_rx("ASML", config.load())
        self.assertIsNone(rx.search("ASML reports third-quarter results"))
        for s in ("shipments to TSMC", "a supply deal with SK Hynix", "Samsung Electronics", "Intel orders"):
            self.assertTrue(rx.search(s), s)

    def test_sk_hynix_jamais_son_propre_nom(self):
        rx = sixk.lexicon_rx("SKHY", config.load())
        for s in ("SK hynix announces results", "SK Hynix Inc."):
            self.assertIsNone(rx.search(s), s)
        for s in ("EUV tools from ASML", "Samsung", "NVIDIA HBM orders"):
            self.assertTrue(rx.search(s), s)

    def test_unites_des_groupes_precedents_inchangees(self):
        """Les noms propres de TSMC (D-0056) ne gagnent ni ASML, ni SK hynix, ni Samsung (D-0057, point 10)."""
        rx = sixk.lexicon_rx("TSM", config.load())
        for s in ("ASML", "SK hynix", "Samsung"):
            self.assertIsNone(rx.search(s), s)


class PisteSamsung(unittest.TestCase):
    def test_terme_en_mot_entier_insensible_a_la_casse(self):
        lex = [e for e in NF.nf_lexicon(config.load()) if e["ref"] == "NF:SAMSUNG"]
        self.assertEqual([e["term"] for e in lex], ["Samsung"])
        rx, _ = D.compile_lexicon(lex)
        for s in ("supply agreement with Samsung Electronics Co., Ltd.", "SAMSUNG DISPLAY CO., LTD.", "Samsung's"):
            self.assertTrue(rx.search(s), s)
        self.assertIsNone(rx.search("SamsungPay"))


class NomsAuRendu(unittest.TestCase):
    def test_chaque_groupe_a_un_nom(self):
        cfg = config.load()
        self.assertEqual([g for g in cfg["groups"] if g not in render.GROUP_NAMES], [])
        self.assertEqual(render.n_groups(cfg), render.NUM_FR[len(cfg["groups"])])
        self.assertEqual(render.group_label("NF:SAMSUNG"), "Samsung")


if __name__ == "__main__":
    unittest.main()
