"""D-0089 : aucune ligne chargée de famille `financing` ne porte le prix d'un financement (point 3) ; la table des faits
s'écrit en groupes de lignes à frontières stables, mêmes lignes et même ordre (point 4).

Lancement : python3 -m unittest tests.test_d0089 -v
"""
import json
import pathlib
import tempfile
import unittest
import unittest.mock
import zlib

import duckdb

from pipeline import config, export, guards


def _loaded_lines():
    """Lignes de la passe chargée de chaque bloc lu : la plus récente par (as_of, passe)."""
    for p in sorted(config.OBS_DIR.glob("*.jsonl")):
        if p.name.endswith(".rejected.jsonl"):
            continue
        rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        if not rows:
            continue
        last = max((r.get("as_of"), r.get("pass_id")) for r in rows)
        for r in rows:
            if (r.get("as_of"), r.get("pass_id")) == last:
                yield p.name[:12], r


class PriceOfFinancing(unittest.TestCase):
    """Intérêts et commissions suivent la trésorerie, sans famille ni type d'arête (garde G1, D-0087)."""

    def test_no_loaded_line_is_a_financing_interest_or_fee(self):
        bad = [(k, r.get("instrument_key")) for k, r in _loaded_lines() if guards.flow_errors(r)]
        self.assertEqual(bad, [])

    def test_the_correction_pass_is_registered(self):
        self.assertIn("2026-11-24T09:46:31Z", config.load()["reading"]["correction_passes"])

    def test_interest_income_follows_cash(self):
        # produits d'intérêts d'Applied Digital sur son billet à vue : l'emprunteur paie, la société reçoit
        rows = [r for k, r in _loaded_lines() if k.startswith("608a744075")
                and r.get("instrument_key") == "apld:base_electron_demand_note" and r.get("amount_nature") == "interest"]
        self.assertEqual([(r["payer"], r["payee"], r.get("family"), r.get("edge_type")) for r in rows],
                         [("Base Electron Corp.", "the Company", None, None)])


class StableRowGroups(unittest.TestCase):
    """Frontières des groupes de lignes de `facts` : fixées par les clés, pas par le nombre de lignes."""

    @staticmethod
    def _keys(units, per=3):
        return sorted(f"{u}/doc.xml#{i}" for u in units for i in range(per))

    @staticmethod
    def _cut_units(keys):
        return {export.filing_unit(keys[i]) for i in export.stable_cuts(keys)[1:]}

    def test_filing_unit(self):
        self.assertEqual(export.filing_unit("0000002488-18-000068/amd-20180331.xml#1"), "0000002488-18-000068")
        self.assertEqual(export.filing_unit("cf/0000002488-15-000067/dei:EntityCommonStockSharesOutstanding/shares//2015-10-29"),
                         "cf/0000002488-15-000067")
        self.assertEqual(export.filing_unit("bdc/0000950170-23-017436/0c8eafb2dddd/InvestmentOwnedAtCost"),
                         "bdc/0000950170-23-017436")
        self.assertEqual(export.filing_unit("html/0001628280-26-042639/x.htm#t58r10/2024"), "html/0001628280-26-042639")
        self.assertEqual(export.filing_unit("nds/0001108524-26-000190/C/us-gaap/2026/20260131/4/pure/0x0/0"),
                         "nds/0001108524-26-000190")

    def test_a_cut_starts_a_filing_whose_checksum_is_a_multiple(self):
        units = [f"{i:010d}-26-{i:06d}" for i in range(1, 400)]
        keys = self._keys(units)
        cuts = export.stable_cuts(keys)
        self.assertEqual(cuts[0], 0)
        for i in cuts[1:]:
            u = export.filing_unit(keys[i])
            self.assertNotEqual(export.filing_unit(keys[i - 1]), u)                 # première ligne de son dépôt
            self.assertEqual(zlib.crc32(u.encode()) % export.FACTS_EVERY, 0)
        expected = {u for u in units[1:] if zlib.crc32(u.encode()) % export.FACTS_EVERY == 0}
        self.assertEqual(self._cut_units(keys), expected)

    def test_a_new_filing_moves_no_other_boundary(self):
        units = [f"{i:010d}-26-{i:06d}" for i in range(1, 400)]
        before = self._cut_units(self._keys(units))
        new = "0000000200-27-000001"                                                # s'insère au milieu
        after = self._cut_units(self._keys(units + [new]))
        self.assertEqual(after - {new}, before)

    def test_a_long_group_is_relieved(self):
        # aucun dépôt multiple de FACTS_EVERY : la relève coupe à un multiple de FACTS_RELIEF une fois le plafond atteint
        units = [u for u in (f"{i:010d}-26-{i:06d}" for i in range(1, 4000))
                 if zlib.crc32(u.encode()) % export.FACTS_EVERY]
        with unittest.mock.patch.object(export, "FACTS_MAX_ROWS", 300):
            keys = self._keys(units)
            cuts = export.stable_cuts(keys)
        self.assertGreater(len(cuts), 1)
        for a, b in zip(cuts, cuts[1:]):
            self.assertGreaterEqual(b - a, 300)
            self.assertEqual(zlib.crc32(export.filing_unit(keys[b]).encode()) % export.FACTS_RELIEF, 0)

    def test_same_rows_same_order_same_types(self):
        con = duckdb.connect()
        con.execute("""CREATE TABLE facts AS SELECT printf('%010d-26-%06d/x.xml#%d', a, a, i) AS fact_key,
                       CAST(a * 1.5 AS DECIMAL(38,6)) AS value, DATE '2026-01-01' + CAST(i AS INTEGER) AS period_end,
                       TIMESTAMP '2026-01-01 10:00:00' AS acceptance_datetime, i % 2 = 0 AS is_nil, CAST(i AS INTEGER) AS n_dims,
                       CASE WHEN i = 0 THEN NULL ELSE 'USD' END AS unit
                       FROM range(1, 300) t(a), range(0, 4) u(i)""")
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        a, b, c = (pathlib.Path(d.name) / n for n in ("stable.parquet", "duckdb.parquet", "again.parquet"))
        groups = export.write_facts(con, a)
        export.write_table(con, "facts", ["fact_key"], b)
        export.write_facts(con, c)
        self.assertGreater(groups, 1)
        self.assertEqual(a.read_bytes(), c.read_bytes())                            # écriture déterministe
        q = duckdb.connect()
        self.assertEqual(q.execute(f"DESCRIBE SELECT * FROM '{a}'").fetchall(), q.execute(f"DESCRIBE SELECT * FROM '{b}'").fetchall())
        self.assertEqual(q.execute(f"SELECT * FROM '{a}'").fetchall(), q.execute(f"SELECT * FROM '{b}'").fetchall())
        self.assertEqual(q.execute(f"SELECT count(DISTINCT row_group_id) FROM parquet_metadata('{a}')").fetchone()[0], groups)

    def test_assemble_exports_facts_through_stable_groups(self):
        import inspect
        from pipeline import assemble
        self.assertIn("export.write_facts(con", inspect.getsource(assemble.run))


if __name__ == "__main__":
    unittest.main()
