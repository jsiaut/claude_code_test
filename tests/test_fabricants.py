"""Fabricants (D-0056) : rattachements par extrait d'Intel, de Micron et de TSMC lus dans config.yaml. Une filiale
cédée sort à la date citée (Altera), une coentreprise entre à sa réalisation (Arizona Fab LLC), une entité à
intérêts variables consolidée par Micron reçoit les lignes d'Intel (IMFT), un nom court défini par un extrait
va à la tête de son groupe.

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

from pipeline import config
from pipeline import entities as E


def registry():
    cfg = config.load()
    meta = {"0000050863": {"group": "INTC", "is_predecessor": False, "name": "INTEL CORP", "formerNames": []},
            "0000723125": {"group": "MU", "is_predecessor": False, "name": "MICRON TECHNOLOGY INC", "formerNames": []},
            "0001046179": {"group": "TSM", "is_predecessor": False,
                           "name": "TAIWAN SEMICONDUCTOR MANUFACTURING CO LTD", "formerNames": []}}
    others = {"Foundry JV Holdco LLC": False, "Grange Newco LLC": False, "AP Grange Holdings, LLC": False}
    return E.build({"meta": meta}, cfg, others)[1]


class Fabricants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = registry()

    def group(self, name, date):
        return E.resolve(self.reg, name, date)[1]

    def test_cession_d_altera(self):
        self.assertEqual(self.group("Altera Corporation", "2025-06-28"), "INTC")
        self.assertEqual(self.group("Altera", "2025-09-11"), "INTC")
        self.assertEqual(self.group("Altera Corporation", "2025-12-27"), "CP:altera corp")

    def test_coentreprise_d_arizona_a_sa_realisation(self):
        self.assertEqual(self.group("Arizona Fab LLC", "2022-11-21"), "CP:arizona fab llc")
        self.assertEqual(self.group("Arizona Fab LLC", "2022-12-31"), "INTC")

    def test_imft_consolidee_par_micron(self):
        for name in ("IM Flash Technologies, LLC", "IMFT"):
            self.assertEqual(self.group(name, "2018-12-29"), "MU", name)
        eid = E.resolve(self.reg, "IMFT", "2018-12-29")[0]
        self.assertEqual(self.reg.treatment_at(eid, "2018-12-29"), "vie_consolidated")

    def test_noms_courts_definis_par_un_extrait(self):
        self.assertEqual(self.group("Intel", "2020-03-12"), "INTC")
        self.assertEqual(self.group("Micron", "2019-10-31"), "MU")
        self.assertEqual(self.group("TSMC", "2026-08-11"), "TSM")
        self.assertEqual(self.group("Taiwan Semiconductor Manufacturing Company", "2020-05-05"), "TSM")

    def test_societes_associees_de_tsmc_hors_du_groupe(self):
        for name in ("VIS", "SSMC", "GUC", "Xintec"):
            g = self.group(name, "2025-12-31")
            self.assertIsNotNone(g, name)
            self.assertNotEqual(g, "TSM", name)

    def test_associes_et_coentreprise_irlandaise_entites_propres(self):
        """Véhicules des associés minoritaires (Brookfield, Apollo) et Grange Newco LLC, qu'aucun extrait ne dit
        consolidée : entités et groupes propres (D-0056, point 6 ; D-0050, point 4)."""
        for name in ("Foundry JV Holdco LLC", "AP Grange Holdings, LLC", "Grange Newco LLC"):
            self.assertTrue(str(self.group(name, "2024-12-28")).startswith("CP:"), name)


if __name__ == "__main__":
    unittest.main()
