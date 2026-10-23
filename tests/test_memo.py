"""Réassemblage plus rapide (D-0062) : chaque raccourci rend exactement ce que rendait le calcul d'avant.
Le mémo des plages de citations et celui des étapes se reprennent tant que leurs entrées n'ont pas
changé, et se recalculent sinon ; config.yaml lu une fois par version du fichier ; la recherche des
valeurs par positions et l'index des noms des BDC donnent le même résultat que le calcul ligne à ligne.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import json
import pathlib
import tempfile
import unittest
from decimal import Decimal

import pandas as pd

from pipeline import cache, config, controls_more, load, memo, model, textnorm


class _Paths:
    """Remplace des chemins de config le temps d'un test."""

    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = getattr(config, k)
            setattr(config, k, v)

    def __exit__(self, *a):
        for k, v in self.old.items():
            setattr(config, k, v)


class ConfigLoad(unittest.TestCase):
    def test_each_call_gets_its_own_copy_and_a_new_version_is_reread(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "config.yaml"
            p.write_text("as_of: 2026-01-02\na: {b: 1}\n", encoding="utf-8")     # la clé as_of est obligatoire (D-0073)
            with _Paths(CONFIG_PATH=p):
                c = config.load()
                c["a"]["b"] = 99
                self.assertEqual(config.load(), {"as_of": "2026-01-02", "a": {"b": 1}})
                p.write_text("as_of: 2026-01-02\na: {b: 2}\nz: 0\n", encoding="utf-8")
                self.assertEqual(config.load(), {"as_of": "2026-01-02", "a": {"b": 2}, "z": 0})


class QuoteRangesMemo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.paths = _Paths(CACHE=root / "cache")
        self.paths.__enter__()
        self.raw = ("<html><p>Intro.</p><p>an agreement with Core<span style='x'>Weave</span>, Inc. dated</p>"
                    "<p>Other text with CoreWeave, Inc. again</p></html>").encode("utf-8")
        cache.write(cache.archive_path("0000000001", "0000000001-26-000001", "doc.htm"), self.raw)
        self.block = {"locator": {"cik": "0000000001", "accession": "0000000001-26-000001", "file": "doc.htm",
                                  "byte_range": [30, len(self.raw)]}}
        self.memo_path = root / "memo" / "quote_ranges.json"

    def tearDown(self):
        self.paths.__exit__()
        self.tmp.cleanup()

    def ranges(self):
        return load.QuoteRanges(path=self.memo_path)

    def test_same_locator_as_direct_search_then_reused(self):
        quotes = ["with CoreWeave, Inc.", "Other text", "absent from the document"]
        r = self.ranges()
        keys = [r.request(self.block, q) for q in quotes]
        r.resolve()
        for q, k in zip(quotes, keys):
            self.assertEqual(r.locator(self.block, q, k), load._locate(self.block, q))
        self.assertEqual(r.searched, 3)
        r.save()
        r2 = self.ranges()
        keys2 = [r2.request(self.block, q) for q in quotes]
        r2.resolve()
        self.assertEqual(r2.searched, 0)                     # tout vient du mémo
        self.assertEqual([r2.locator(self.block, q, k) for q, k in zip(quotes, keys2)],
                         [load._locate(self.block, q) for q in quotes])

    def test_changed_document_or_code_is_searched_again(self):
        r = self.ranges()
        r.request(self.block, "Other text")
        r.resolve()
        r.save()
        cache.write(cache.archive_path("0000000001", "0000000001-26-000001", "doc.htm"), self.raw + b"<p>more</p>")
        r2 = self.ranges()
        r2.request(self.block, "Other text")
        r2.resolve()
        self.assertEqual(r2.searched, 1)
        d = json.loads(self.memo_path.read_text())
        d["version"] = "autre code"
        self.memo_path.write_text(json.dumps(d))
        self.assertEqual(self.ranges().known, {})

    def test_missing_document_gives_no_range_like_direct_search(self):
        b = {"locator": {"cik": "0000000002", "accession": "x", "file": "absent.htm", "byte_range": [0, 1]}}
        r = self.ranges()
        k = r.request(b, "anything")
        self.assertIsNone(k)
        self.assertEqual(r.locator(b, "anything", k), load._locate(b, "anything"))


def occ(rows):
    """Table d'occurrences comme occurrences_df la rend : dates en objets date (NaT si absentes)."""
    cols = ["period_type", "period_start", "period_end", "knowledge_date", "value", "order_key", "fact_key",
            "accession", "concept", "tier", "decimals", "decimals_inf", "precision_known", "is_tagged"]
    df = pd.DataFrame({c: pd.Series([r[i] for r in rows], dtype=object) for i, c in enumerate(cols)})
    df["period_type"] = pd.Categorical(df["period_type"], categories=["instant", "duration"], ordered=True)
    df["value"] = df["value"].astype(float)
    return df


D = dt.date


class TermValueByPositions(unittest.TestCase):
    """La recherche par positions rend le même dictionnaire que le filtrage ligne à ligne."""

    def setUp(self):
        k = lambda acc, rank: ("2026-01-01 00:00:00", acc, 1, -6, rank)
        self.o = occ([
            ["duration", D(2025, 1, 1), D(2025, 3, 31), D(2025, 5, 1), 10.0, k("a1", 1), "f1", "a1", "c", "B", -6, False, True, True],
            ["duration", D(2025, 1, 2), D(2025, 3, 30), D(2025, 6, 1), 11.0, k("a2", 1), "f2", "a2", "c", "B", -6, False, True, True],
            ["duration", D(2025, 1, 2), D(2025, 3, 30), D(2025, 6, 1), 11.0, k("a2", 1), "f3", "a2", "c", "B", -6, False, True, True],
            ["duration", D(2024, 4, 1), D(2025, 3, 31), D(2025, 5, 1), 40.0, k("a1", 2), "f4", "a1", "c", "B", -6, False, True, True],
            ["instant", pd.NaT, D(2025, 3, 31), D(2025, 5, 1), 7.0, k("a1", 3), "f5", "a1", "c", "B", -6, False, True, True],
            ["instant", pd.NaT, D(2025, 4, 2), D(2025, 7, 1), 8.0, k("a3", 1), "f6", "a3", "c", "B", -6, False, True, True],
            ["duration", D(2025, 1, 1), D(2025, 3, 31), D(2025, 9, 1), float("nan"), k("a0", 1), "f7", "a0", "c", "B",
             -6, False, True, True],
        ])
        self.ix = model.occurrence_index(self.o)

    def test_same_result_on_every_period_and_cutoff(self):
        self.assertIsNotNone(self.ix)
        periods = [(D(2025, 1, 1), D(2025, 3, 31), False), (D(2024, 4, 1), D(2025, 3, 31), False),
                   (None, D(2025, 3, 31), True), (None, D(2025, 3, 31), False), (D(2025, 1, 1), None, False),
                   (D(2023, 1, 1), D(2023, 3, 31), False), (None, D(2025, 4, 1), True)]
        for start, end, inst in periods:
            for cutoff in (D(2025, 4, 30), D(2025, 5, 1), D(2025, 6, 15), D(2025, 12, 31)):
                slow = model.term_value(self.o, start, end, inst, cutoff)
                fast = model.term_value(self.o, start, end, inst, cutoff, ix=self.ix)
                self.assertEqual(fast, slow, (start, end, inst, cutoff))

    def test_tie_keeps_the_first_row_and_revision_is_seen(self):
        t = model.term_value(self.o, D(2025, 1, 1), D(2025, 3, 31), False, D(2025, 6, 15), ix=self.ix)
        self.assertEqual((t["fact_key"], t["value"], t["revised"]), ("f2", Decimal("11.0"), True))

    def test_non_date_values_fall_back_to_row_by_row(self):
        o = self.o.copy()
        o["period_end"] = o["period_end"].astype(object)
        o.loc[0, "period_end"] = "2025-03-31"
        self.assertIsNone(model.occurrence_index(o))


class AxisTables(unittest.TestCase):
    def test_children_computed_once_give_the_same_tables(self):
        pres = pd.DataFrame([
            ["r1", "srt:ProductOrServiceAxis", "srt:ProductsAndServicesDomain", 1],
            ["r1", "srt:ProductsAndServicesDomain", "a:CloudMember", 2],
            ["r1", "srt:ProductsAndServicesDomain", "a:AdsMember", 1],
            ["r2", "srt:StatementGeographicalAxis", "a:UsMember", 1],
            ["r2", "srt:StatementGeographicalAxis", "a:EuMember", 2],
            ["r2", "srt:StatementGeographicalAxis", "a:EuAbstract", 3],
        ], columns=["role", "parent", "child", "ord"])
        kids = controls_more.role_children(pres)
        for axis in ("srt:ProductOrServiceAxis", "srt:StatementGeographicalAxis", "x:None"):
            self.assertEqual(controls_more.axis_tables(pres, axis, kids), controls_more.axis_tables(pres, axis))
        self.assertEqual(controls_more.axis_tables(pres, "srt:ProductOrServiceAxis", kids),
                         [("r1", ("a:AdsMember", "a:CloudMember"))])


class LenderNameIndex(unittest.TestCase):
    """Le rattachement par premier mot rend le nom que rendait le balayage de tous les noms."""

    def test_same_hit_as_full_scan(self):
        from pipeline import lender
        keys = sorted(["x ai holdings corp", "x ai corp", "inc", " corp inc", "oracle corp", "blue owl capital inc",
                       "owl rock capital corp"], key=len, reverse=True)
        find = lender.name_finder(keys)
        for ident in ["x ai holdings corp term loan", "x ai corp revolver", "oracle corp yucca growth llc", "acme inc",
                      "blue owl capital inc first lien", "nothing here", "the owl rock capital corp note", "a  corp inc b"]:
            t = " " + ident + " "
            self.assertEqual(find(t), next((k for k in keys if " " + k + " " in t), None), ident)


class StepMemo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = memo.MEMO
        memo.MEMO = pathlib.Path(self.tmp.name) / "memo"

    def tearDown(self):
        memo.MEMO = self.old
        self.tmp.cleanup()

    def test_value_is_reused_for_the_same_inputs_only(self):
        calls = []

        def compute():
            calls.append(1)
            return [{"v": Decimal("1.5"), "d": D(2025, 1, 1)}]
        a = memo.Memo("fp1").value("step", compute, key="k")
        b = memo.Memo("fp1").value("step", compute, key="k")
        c = memo.Memo("fp2").value("step", compute, key="k")
        d = memo.Memo("fp1", use=False).value("step", compute, key="k")
        self.assertEqual((a, len(calls)), (b, 3))
        self.assertEqual(a, c)
        self.assertEqual(a, d)
        self.assertLessEqual(len(list(memo.MEMO.glob("step-*.pkl"))), memo.KEEP)

    def test_database_snapshot(self):
        import duckdb
        db = pathlib.Path(self.tmp.name) / "model.duckdb"

        def build():
            con = duckdb.connect(str(db))
            con.execute("CREATE TABLE t AS SELECT 1 AS x")
            return con, {"rows": 1}
        con, info = memo.Memo("fp").database("base", db, build)
        con.execute("INSERT INTO t VALUES (2)")       # l'exécution continue sur la base, pas sur la copie
        con.close()
        con2, info2 = memo.Memo("fp").database("base", db, lambda: self.fail("la base devait venir du mémo"))
        self.assertEqual((con2.execute("SELECT count(*) FROM t").fetchone()[0], info2), (1, info))

    def test_fingerprint_ignores_observations_only(self):
        root = pathlib.Path(self.tmp.name) / "repo"
        for d in ("pipeline", "db", "work/observations", "work/tenders", "cache"):
            (root / d).mkdir(parents=True)
        (root / "pipeline" / "a.py").write_text("x = 1\n")
        (root / "schema.sql").write_text("-- s\n")
        (root / "config.yaml").write_text("a: 1\n")
        (root / "db" / "f.parquet").write_bytes(b"1")
        (root / "work" / "observations" / "ck.jsonl").write_text("{}\n")
        with _Paths(ROOT=root, CONFIG_PATH=root / "config.yaml", DB_DIR=root / "db", WORK=root / "work",
                    CACHE=root / "cache"):
            fp = memo.inputs_fingerprint()
            (root / "work" / "observations" / "ck.jsonl").write_text('{"changed": 1}\n')
            (root / "work" / "tmp_assemble.log").write_text("journal\n")
            self.assertEqual(memo.inputs_fingerprint(), fp)
            (root / "work" / "tenders" / "r.jsonl").write_text("{}\n")
            fp2 = memo.inputs_fingerprint()
            self.assertNotEqual(fp2, fp)
            (root / "db" / "f.parquet").write_bytes(b"22")
            self.assertNotEqual(memo.inputs_fingerprint(), fp2)


class Locate(unittest.TestCase):
    def test_locate_in_text_is_locate_in_raw(self):
        raw = "<p>an agreement with Core<b>Weave</b>, Inc.</p>".encode("cp1252")
        self.assertEqual(textnorm.locate_in_raw(raw, "with CoreWeave, Inc."),
                         textnorm.locate_in_text(textnorm.decode(raw), textnorm.raw_encoding(raw), "with CoreWeave, Inc."))


if __name__ == "__main__":
    unittest.main()
