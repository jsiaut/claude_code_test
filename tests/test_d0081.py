"""D-0081 : une clé hors du schéma est refusée à l'insertion ; les paramètres de queue des grandes fabriques se
nomment à l'appel, si bien qu'un argument décalé lève une erreur.

Lancement : python3 -m unittest tests.test_d0081 -v
"""
import inspect
import unittest

import duckdb
import pandas as pd

from pipeline import assemble, circularity, config, controls, labs, lender, measures


def base():
    con = duckdb.connect()
    con.execute((config.ROOT / "schema.sql").read_text(encoding="utf-8"))
    return con


class StrictInsert(unittest.TestCase):
    def row(self, **kw):
        return {**controls.ctrl("c1_balance_components", "AMD", None, "2025-03-29", "as_known", "2026-10-27", "ok", "acc",
                                breakdown="us-gaap:Assets"), **kw}

    def test_cle_hors_du_schema_refusee(self):
        con = base()
        with self.assertRaisesRegex(ValueError, r"controls : clés hors du schéma \['explanaton_code'\]"):
            assemble.insert(con, "controls", [self.row(explanaton_code="sum_differs")])
        self.assertEqual(con.execute("SELECT count(*) FROM controls").fetchone()[0], 0)

    def test_ligne_juste_et_colonne_absente(self):
        con = base()
        r = self.row()
        del r["evidence"]
        self.assertEqual(assemble.insert(con, "controls", [r]), 1)
        self.assertEqual(con.execute("SELECT status, evidence FROM controls").fetchone(), ("ok", None))

    def test_faits_des_notes_data_sets_dans_le_schema(self):
        f = {"source": "nds", "fact_key": "nds:1", "value": "12", "concept": "us-gaap:Revenues", "cik": "0000001",
             "accession": "0000001-26-000001", "form": "10-K", "filing_date": "2026-02-01", "version": "us-gaap/2025",
             "period_type": "duration", "period_end": "2025-12-31", "unit": "USD", "dims": "[]", "dims_list": [],
             "locator": "a.zip:num.tsv", "tier": "A", "knowledge_date": "2026-02-01"}
        cols = {c[0] for c in base().execute("DESCRIBE facts").fetchall()}
        self.assertLessEqual(set(labs.nds_fact_rows([f])[0]), cols)

    def test_faits_des_bdc_dans_le_schema(self):
        num = pd.DataFrame([{"holding": "First lien loan", "adsh": "0000002-26-000001", "tag": "InvestmentOwnedAtFairValue",
                             "identifier": "Example LLC", "other_axes": "", "form": "10-K", "cik": 2, "filed": "20260201",
                             "version": "us-gaap/2025", "qtrs": 0, "date": "2025-12-31", "uom": "USD", "value": "1000",
                             "archive": "b.zip"}])
        cols = {c[0] for c in base().execute("DESCRIBE facts").fetchall()}
        self.assertLessEqual(set(lender.bdc_facts(num)[0]), cols)


class KeywordOnly(unittest.TestCase):
    def kinds(self, fn, first_named):
        ps = list(inspect.signature(fn).parameters.values())
        i = [p.name for p in ps].index(first_named)
        return {p.kind for p in ps[:i]}, {p.kind for p in ps[i:]}

    def test_parametres_de_queue_nommes(self):
        K, P = inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD
        for fn, first in ((measures.cell, "term"), (controls.ctrl, "breakdown"), (circularity.pair_measures, "cals"),
                          (circularity.dependency_cells, "cut")):
            head, tail = self.kinds(fn, first)
            self.assertEqual((head, tail), ({P}, {K}), fn.__name__)

    def test_argument_decale_leve_une_erreur(self):
        with self.assertRaises(TypeError):
            measures.cell("fcf_basic", "AMD", None, "2025-03-29", "as_known", "2026-10-27", "none")
        with self.assertRaises(TypeError):
            controls.ctrl("c1_balance_components", "AMD", None, "2025-03-29", "as_known", "2026-10-27", "ok", "acc",
                          "us-gaap:Assets")


if __name__ == "__main__":
    unittest.main()
