"""Mesures des positions de BDC (D-0045, point 5) : une valeur vide ou illisible du principal, d'un taux ou du coût
compte comme non balisée, jamais comme un zéro, et n'interrompt pas l'assemblage (D-0057).

Lancement : python3 -m unittest discover -s tests -v
"""
import unittest

import pandas as pd

from pipeline import lender


def pos(**kw):
    base = {"group": "CP:x", "bdc_cik": "1", "date": "2023-03-31", "instrument_class": "debt", "filed": "20230510",
            "entity_id": "name:x", "bdc_name": "BDC", "archive": "2023q2", "adsh": "0000000001-23-000001", "form": "10-Q",
            "cost": "100", "fair_value": "95",
            "fact_keys": {"InvestmentOwnedAtCost": "k-cost", "InvestmentOwnedAtFairValue": "k-fv"},
            "principal": "100", "unfunded_commitment": None, "rate": "0.12", "rate_pik": "0.02",
            "has_perf": False, "nonperforming": False}
    base.update(kw)
    return base


def by_bdc(cells, measure):
    return [c for c in cells if c["measure"] == measure and c["counterparty"] == "cik:1"]


class ValeursIllisibles(unittest.TestCase):
    def test_taux_capitalise_vide(self):
        hold = pd.DataFrame([pos(), pos(adsh="0000000001-23-000002", rate_pik="")])
        (c,) = by_bdc(lender.measures_cells(hold, "2026-10-07"), "bdc_pik_share")
        self.assertEqual(c["status"], "partial")          # la position au taux vide n'entre pas dans le rapport
        self.assertAlmostEqual(float(c["value"]), 0.02 / 0.12, places=6)

    def test_cout_vide(self):
        hold = pd.DataFrame([pos(), pos(adsh="0000000001-23-000002", cost="")])
        (c,) = by_bdc(lender.measures_cells(hold, "2026-10-07"), "bdc_fv_to_cost")
        self.assertEqual(c["status"], "partial")
        self.assertAlmostEqual(float(c["value"]), 0.95, places=6)

    def test_aucune_valeur_lisible(self):
        hold = pd.DataFrame([pos(rate_pik="", principal="n/a")])
        (c,) = by_bdc(lender.measures_cells(hold, "2026-10-07"), "bdc_pik_share")
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "not_tagged"))


if __name__ == "__main__":
    unittest.main()
