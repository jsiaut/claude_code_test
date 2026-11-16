"""D-0086 : positions des 13F sans pièce de financement (volet A, attribution par abréviation du point 6), typologie du
Bulletin BRI n° 137 (volet B, points 4 et 7), unités prioritaires de la découverte.

Lancement : python3 -m unittest tests.test_d0086 -v
"""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline import discovery, ownership, typology


class Abreviation(unittest.TestCase):
    LEGAL = {"space exploration technologies corp": "cik:spacex", "coreweave inc": "cik:crwv",
             "alpha beta systems inc": "cik:a1", "alpha beta solutions inc": "cik:a2"}

    def test_un_mot_tronque(self):
        self.assertEqual(ownership.abbreviation_of("SPACE EXPLORATION TECHN CORP", self.LEGAL), "cik:spacex")

    def test_refus(self):
        for name in ("SPACE EXPLOR TECHN CORP",      # deux mots tronqués
                     "SPACE EXPLORATION TEC CORP",    # troncature de moins de quatre lettres
                     "SPACE EXPLORATION TECHN INC",   # autre forme juridique
                     "SPACE EXPLORATION CORP",        # nombre de mots différent
                     "ALPHA BETA SOLU INC",           # une seule candidate, mais voir ci-dessous
                     ):
            got = ownership.abbreviation_of(name, self.LEGAL)
            if name == "ALPHA BETA SOLU INC":
                self.assertEqual(got, "cik:a2")
            else:
                self.assertIsNone(got, name)
        self.assertIsNone(ownership.abbreviation_of("ALPHA BETA SYST INC", dict(self.LEGAL, **{"alpha beta systemic inc":
                                                                                                "cik:a3"})))

    def test_attribution_garde_le_nom_legal_d_abord(self):
        lines = [{"issuer": "COREWEAVE INC", "cusip": "21873S108", "period": "2026-06-30"},
                 {"issuer": "SPACE EXPLORATION TECHN CORP", "cusip": "84612X100", "period": "2026-06-30"}]
        legal = {"coreweave inc": "cik:crwv", "space exploration technologies corp": "cik:spacex"}
        got = ownership.attribute_lines(lines, legal, lambda e, d: {"cik:crwv": "CRWV", "cik:spacex": "SPCX"}[e])
        self.assertEqual(got, [("CRWV", "legal_name"), ("SPCX", "abbreviation")])


class PositionsDocumentees(unittest.TestCase):
    def test_arêtes_qui_documentent(self):
        edges = [{"family": "financing", "edge_type": "equity_primary", "from_group": "NVDA", "to_group": "CRWV"},
                 {"family": "financing", "edge_type": "loan_or_facility", "from_group": "NVDA", "to_group": "X"},
                 {"family": "customer_consideration", "edge_type": "equity_or_warrants_to_customer",
                  "from_group": "MRVL", "to_group": "AMZN"},
                 {"family": "financing", "edge_type": "equity_primary", "from_group": "A", "to_group": "B",
                  "elimination_status": "eliminated"}]
        self.assertEqual(ownership.documented_holdings(edges), {("NVDA", "CRWV"), ("AMZN", "MRVL")})

    def test_nom_normalise(self):
        self.assertEqual(ownership.issuer_norm("QUALCOMM INC/DE"), "qualcomm inc")
        self.assertEqual(ownership.issuer_norm("Astera Labs, Inc."), "astera labs inc")
        self.assertEqual(ownership.issuer_norm("ASTERA LABS INC"), "astera labs inc")

    def test_index_des_candidats(self):
        c = pd.DataFrame([{"rank": 7, "cik": "1", "filer": "Astera Labs, Inc."}, {"rank": 9, "cik": "2", "filer": "X Corp"}])
        u = pd.DataFrame([{"order": 10, "cik": "1", "groups": "AMZN"}, {"order": 11, "cik": "1", "groups": "MSFT;AMZN"},
                          {"order": 12, "cik": "2", "groups": None}])
        by_name, by_cik = ownership.candidates_index(c, u, {11})
        self.assertEqual(by_name["astera labs inc"], ("1", 7, "Astera Labs, Inc."))
        self.assertEqual([(x["order"], x["built"]) for x in by_cik["1"]], [(10, False), (11, True)])
        self.assertEqual(by_cik["2"][0]["groups"], set())

    def test_dernier_13f(self):
        todo = [{"kind": "13f", "s": "NVDA", "report_date": "2026-03-31"}, {"kind": "13f", "s": "NVDA", "report_date": "2026-06-30"},
                {"kind": "13f", "s": "NVDA", "report_date": "2026-06-30", "accession": "amendement"},
                {"kind": "13dg", "s": "NVDA", "report_date": None}]
        self.assertEqual(len(ownership.latest_13f(todo)), 2)


def e(fam, a, b, d="2024-06-30", key=None, stage="drawn_or_paid", **kw):
    return dict({"link_kind": "edge", "family": fam, "from_group": a, "to_group": b, "_date": dt.date.fromisoformat(d)
                 if d else None, "link_key": key or f"{fam}:{a}>{b}:{d}", "stage": stage}, **kw)


class TypologieBRI(unittest.TestCase):
    NODES = {"NVDA", "CRWV", "MSFT", "LAB:OPENAI", "NF:SOFTBANK"}

    def test_types(self):
        edges = [e("financing", "MSFT", "LAB:OPENAI"), e("commercial", "LAB:OPENAI", "MSFT"),        # type 1
                 e("financing", "NF:SOFTBANK", "LAB:OPENAI"), e("commercial", "NF:SOFTBANK", "LAB:OPENAI"),  # type 2
                 e("financing", "NVDA", "CRWV"), e("commercial", "CRWV", "NVDA"), e("commercial", "NVDA", "CRWV"),  # 3
                 e("financing", "NVDA", "LAB:OPENAI", stage="signed")]                                # seul
        rel, cc = typology.classify(edges, self.NODES)
        self.assertEqual({k: v["type"] for k, v in rel.items()},
                         {("MSFT", "LAB:OPENAI"): "supplier_investor", ("NF:SOFTBANK", "LAB:OPENAI"): "customer_investor",
                          ("NVDA", "CRWV"): "reciprocal", ("NVDA", "LAB:OPENAI"): "financing_only"})
        self.assertEqual(rel[("NVDA", "LAB:OPENAI")]["stage"], "signed")
        self.assertEqual(cc, [])

    def test_fenetres_et_perimetre(self):
        edges = [e("financing", "MSFT", "LAB:OPENAI", "2020-06-30"), e("commercial", "LAB:OPENAI", "MSFT", "2023-06-30"),
                 e("financing", "NVDA", "CRWV", None), e("financing", "NVDA", "OWL"), e("financing", "NVDA", "NVDA"),
                 e("customer_consideration", "NVDA", "CRWV"),
                 e("commercial", "NF:SOFTBANK", "LAB:OPENAI", "2028-12-31"), e("financing", "NF:SOFTBANK", "LAB:OPENAI")]
        rel, cc = typology.classify(edges, self.NODES, dt.date(2021, 1, 1), dt.date(2025, 12, 31))
        self.assertEqual(set(rel), {("NF:SOFTBANK", "LAB:OPENAI")})          # 2020 hors fenêtre, sans date écartée
        self.assertEqual(rel[("NF:SOFTBANK", "LAB:OPENAI")]["type"], "financing_only")   # achat daté de 2028
        rel, cc = typology.classify(edges, self.NODES)                         # fenêtre ouverte (point 7)
        self.assertEqual(rel[("MSFT", "LAB:OPENAI")]["type"], "supplier_investor")
        self.assertEqual(rel[("NF:SOFTBANK", "LAB:OPENAI")]["type"], "customer_investor")
        self.assertIn(("NVDA", "CRWV"), rel)
        self.assertNotIn(("NVDA", "OWL"), rel)
        self.assertEqual(cc, [("NVDA", "CRWV")])

    def test_perimetre(self):
        cfg = {"groups": {"NVDA": "1", "OWL": "2"}, "labs": ["OpenAI"], "non_filers": [{"ref": "NF:SOFTBANK"}],
               "bis_typology": {"excluded_groups": ["OWL"]}}
        self.assertEqual(typology.perimeter(cfg), {"NVDA", "LAB:OPENAI", "NF:SOFTBANK"})

    def test_cellules(self):
        cfg = {"groups": {"MSFT": "1"}, "labs": ["OpenAI"], "non_filers": [],
               "bis_typology": {"windows": [[None, None], ["2021-01-01", "2025-12-31"]]}}
        edges = [e("financing", "MSFT", "LAB:OPENAI"), e("commercial", "LAB:OPENAI", "MSFT")]
        cs, st = typology.cells(edges, "2026-11-14", cfg)
        self.assertEqual([(c["period_start"], c["period_end"], c["value_text"]) for c in cs],
                         [("none", "2026-11-14", "supplier_investor"), ("2021-01-01", "2025-12-31", "supplier_investor")])
        self.assertEqual(json.loads(cs[0]["flags"])["bis_type"], 1)


class UnitesPrioritaires(unittest.TestCase):
    def test_selection(self):
        with tempfile.TemporaryDirectory() as d:
            units = Path(d) / "u.parquet"
            pd.DataFrame([{"order": 3, "cik": "1", "groups": "NVDA", "kind": "note"},
                          {"order": 1, "cik": "1", "groups": "AMZN", "kind": "note"},
                          {"order": 2, "cik": "1", "groups": "NVDA;AMZN", "kind": "exhibit_header"},
                          {"order": 4, "cik": "9", "groups": "NVDA", "kind": "note"}]).to_parquet(units)
            old_units, old_built = discovery.UNITS, discovery.built_units
            discovery.UNITS, discovery.built_units = units, lambda: {3: {}}
            try:
                cells = [{"subject": "NVDA", "flags": json.dumps({"candidate": {"cik": "1", "units_naming_holder": 2}})},
                         {"subject": "AMZN", "flags": json.dumps({"candidate": {"cik": "9", "units_naming_holder": 0}})},
                         {"subject": "GOOGL", "flags": json.dumps({})}]
                self.assertEqual([u["order"] for u in discovery.priority_units(cells)], [2])
            finally:
                discovery.UNITS, discovery.built_units = old_units, old_built


if __name__ == "__main__":
    unittest.main()
