"""Exposition d'un fournisseur sur un laboratoire (D-0059, point 11) : un cumul versé publié au coût est
un état, la dernière valeur connue ; une réévaluation sur prix observables est un flux du résultat ;
les apports en numéraire s'additionnent.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import unittest

from pipeline import circularity as C


def edge(key, ik, date, amount, nature, basis=None, event="funding", edge_type="equity_primary"):
    return {"link_key": key, "instrument_key": ik, "family": "financing", "edge_type": edge_type, "from_group": "MSFT",
            "to_group": "LAB:OPENAI", "edge_evidence": "amount", "_date": dt.date.fromisoformat(date), "tier": "A",
            "_obs": {"amount": amount, "unit": "USD", "event_type": event, "amount_nature": nature,
                     "measurement_basis": basis, "knowledge_date": date}}


class Exposure(unittest.TestCase):
    def run_pair(self, edges):
        p = C.Pair("MSFT", "LAB:OPENAI")
        p.edges = edges
        quarters = [{"end": dt.date(2026, 6, 30)}]
        ev = {("MSFT", "LAB:OPENAI"): {"F": {"as_known": {"exposure_outstanding": {dt.date(2026, 6, 30): ("active", [])}}}}}
        out = C.counterparty_exposure({("MSFT", "LAB:OPENAI"): p}, ev, {"MSFT": {"quarters": quarters}}, "2026-10-07",
                                      text_done=frozenset({"MSFT"}))
        return {c["breakdown_key"]: c["value"] for c in out}

    def test_cumulative_cost_is_a_state(self):
        got = self.run_pair([edge("a", "msft:x", "2025-09-30", "11600000000", "other", "cost"),
                             edge("b", "msft:x", "2025-12-31", "11700000000", "other", "cost"),
                             edge("c", "msft:x", "2026-06-30", "11900000000", "other", "cost")])
        self.assertEqual(got["exposed_assets/cost/equity_investment"], 11900000000)

    def test_cash_contributions_add_up(self):
        got = self.run_pair([edge("a", "amzn:n", "2023-09-30", "1250000000", "financing_cash"),
                             edge("b", "amzn:n", "2024-03-31", "2750000000", "financing_cash")])
        self.assertEqual(got["exposed_assets/cost/equity_investment"], 4000000000)

    def test_observable_price_adjustment_is_not_an_exposure(self):
        got = self.run_pair([edge("a", "amzn:p", "2026-06-30", "92500000000", "investment_carrying_amount", "carrying_amount",
                                  event="recognition"),
                             edge("b", "amzn:p", "2026-06-30", "50500000000", "other", event="observable_price_adjustment")])
        self.assertEqual(got, {"exposed_assets/carrying_amount/equity_investment": 92500000000})
