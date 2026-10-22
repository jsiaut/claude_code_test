"""D-0072 : emplacement compact des faits (§7) et recherche des citations répartie sur un pool de processus.

Lancement : python3 -m unittest discover -s tests -t .
"""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline import cache, load


class Locator(unittest.TestCase):
    def test_instance_fact_id_or_rank_api_resource_and_text_unchanged(self):
        text_loc = '{"file": "x.htm", "accession": "a", "byte_range": [1, 9], "quote": "q"}'
        df = pd.DataFrame([
            {"source": "instance", "fact_id": "f-908", "occ_rank": 908, "cik": "0000002488", "locator": '{"json": 1}'},
            {"source": "instance", "fact_id": None, "occ_rank": 12, "cik": "0000002488", "locator": '{"json": 2}'},
            {"source": "companyfacts", "fact_id": None, "occ_rank": None, "cik": "0000002488", "locator": '{"api": 1}'},
            {"source": "html_parse", "fact_id": None, "occ_rank": None, "cik": "0001181412", "locator": text_loc},
            {"source": "bdc_num", "fact_id": None, "occ_rank": None, "cik": None, "locator": "2023q2_bdc.zip:datasets/num.tsv"}])
        out = load.compact_locator(df.copy())
        self.assertEqual(list(out["locator"]), ["f-908", "#12", "companyfacts/CIK0000002488", text_loc,
                                                "2023q2_bdc.zip:datasets/num.tsv"])

    def test_fact_id_left_the_schema(self):
        self.assertNotIn("fact_id", load.FACT_COLS)
        self.assertIn("locator", load.FACT_COLS)
        schema = (Path(load.config.ROOT) / "schema.sql").read_text(encoding="utf-8")
        facts = schema.split("CREATE TABLE facts (", 1)[1].split(");", 1)[0]
        self.assertNotIn("fact_id", facts)
        self.assertIn("locator VARCHAR", facts)


def html(i):
    return (f"<html><body><p>Document {i}.</p><p>We paid <b>$1,{i:03d}</b> million to Example Corp. in fiscal "
            f"{2020 + i % 5}.</p><table><tr><td>Line {i}</td><td>{i * 7}</td></tr></table></body></html>").encode("utf-8")


class ParallelQuotes(unittest.TestCase):
    def test_pool_gives_the_same_ranges_as_the_serial_search(self):
        with tempfile.TemporaryDirectory() as d:
            todo, expect = {}, {}
            for i in range(12):
                p = Path(d) / f"doc{i}.htm.zst"
                cache.write(p, html(i))
                items = [(f"k{i}a", 0, f"We paid $1,{i:03d} million to Example Corp."),     # trouvée, balise sautée
                         (f"k{i}b", 0, "absent de ce document")]                             # introuvable : None
                todo[p] = items
            todo[Path(d) / "absent.htm.zst"] = [("kx", 0, "document illisible")]             # lecture en échec
            for p, items in todo.items():
                found, _ = load.ranges_of_document((str(p), items))
                expect.update(found)
            q = load.QuoteRanges(path=Path(d) / "ranges.json", use_memo=False)
            q.todo = dict(todo)
            q.used = {k: load._PENDING for items in todo.values() for k, _, _ in items}
            self.assertGreater(len(q.todo), load.PARALLEL_MIN_DOCS)                      # le pool sert
            q.resolve()
        got = {k: (load.FAILED if v is load._FAILED else v) for k, v in q.used.items()}
        self.assertEqual(got, expect)
        self.assertIsInstance(got["k3a"], list)
        self.assertIsNone(got["k3b"])
        self.assertEqual(got["kx"], load.FAILED)
        self.assertEqual(q.searched, 24)
        self.assertEqual(list(q.used), [k for items in todo.values() for k, _, _ in items])   # ordre des clés gardé


if __name__ == "__main__":
    unittest.main()
