"""Piste des non-déposants de la découverte (D-0044) : filtre du scan, règle de lecture, plafond.

Lancement : python3 -m unittest discover -s tests -t .
"""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import pandas as pd

from pipeline import discovery as D
from pipeline import entities as E
from pipeline import nf_discovery as N

LEX = [{"term": "NVIDIA", "ref": "NVDA", "case": False, "from": None, "to": None},
       {"term": "SoftBank", "ref": "NF:SOFTBANK", "case": False, "from": None, "to": None}]
TXT_COLS = ["adsh", "tag", "version", "ddate", "qtrs", "iprx", "lang", "dcml", "durp", "datp", "dimh", "dimn",
            "coreg", "escaped", "srclen", "txtlen", "footnote", "footlen", "context", "value"]


def tsv(cols, rows):
    return "\t".join(cols) + "\n" + "".join("\t".join(r) + "\n" for r in rows)


def archive(path, values):
    """Archive minimale des Notes Data Sets : un dépôt, une ligne de `txt` par valeur."""
    txt = [["0001-26-000001", f"Note{i}TextBlock", "us-gaap/2025", "20251231", "4", "0", "en-US", "", "", "",
            "0x00000000", "0", "", "0", str(len(v)), str(len(v)), "", "", "c", v] for i, v in enumerate(values)]
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("sub.tsv", tsv(["adsh", "cik", "name", "former"], [["0001-26-000001", "0000000123", "Example Corp", ""]]))
        zf.writestr("txt.tsv", tsv(TXT_COLS, txt))
        zf.writestr("num.tsv", tsv(["adsh", "tag", "dimh", "value"], [["0001-26-000001", "Revenues", "0x00000000", "1"]]))
        zf.writestr("dim.tsv", tsv(["dimhash", "segments"], [["0x00000000", ""]]))
        zf.writestr("tag.tsv", tsv(["tag", "version"], [["Revenues", "us-gaap/2025"]]))
        zf.writestr("pre.tsv", tsv(["adsh", "report", "tag", "version"], [["0001-26-000001", "1", "Revenues", "us-gaap/2025"]]))
        zf.writestr("ren.tsv", tsv(["adsh", "report", "shortname"], [["0001-26-000001", "1", "Notes"]]))


class Scan(unittest.TestCase):
    def test_keep_refs_keeps_only_non_filer_lines_with_their_co_mentions(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.zip"
            archive(p, ["We sell GPUs to NVIDIA.", "SoftBank invested in us; NVIDIA is a customer.",
                        "SoftBank Group Corp. holds 12% of our shares."])
            out, stats = D.scan(p, LEX, set(), keep_refs={"NF:SOFTBANK"})
            self.assertEqual(len(out["txt"]), 2)
            self.assertEqual(stats["other_refs_only_rows"], 1)
            refs = [sorted({m[1] for m in json.loads(x)}) for x in out["txt"]["mentions"]]
            self.assertEqual(refs, [["NF:SOFTBANK", "NVDA"], ["NF:SOFTBANK"]])
            out0, _ = D.scan(p, LEX, set())          # sans filtre : les trois lignes, comme avant
            self.assertEqual(len(out0["txt"]), 3)


class Selection(unittest.TestCase):
    def units(self):
        rows = [(1, "A", 1, "1", "exhibit_header", True, "NVDA"),   # R1
                (2, "A", 1, "1", "note", True, ""),                 # R2 : candidat à montant documenté
                (3, "A", 2, "2", "note", True, ""),                 # ni R1 ni R2
                (4, "B", 1, "1", "note", False, "LAB:OPENAI"),      # R1, dépôt plus ancien
                (5, "B", 1, "1", "note", False, "")]                # R2 ne vaut que pour le dernier dépôt
        u = pd.DataFrame([{"order": o, "pass": p, "rank": r, "cik": c, "kind": k, "latest": l, "co_refs": co,
                           "groups": "NF:SOFTBANK", "adsh": f"a{o}", "doc": f"d{o}"} for o, p, r, c, k, l, co in rows])
        c = pd.DataFrame({"cik": ["1", "2"], "documented_amount": [1e9, None]})
        return u, c

    def test_rules_and_queue_order(self):
        u, c = self.units()
        s = N.select_units(u, c, cap=10).set_index("order")
        self.assertEqual([s.loc[o, "rule"] for o in (1, 2, 4)], ["R1", "R2", "R1"])
        self.assertEqual([s.loc[o, "status"] for o in (3, 5)], ["out_of_rule", "out_of_rule"])
        self.assertEqual([int(s.loc[o, "queue"]) for o in (1, 4, 2)], [1, 2, 3])   # R1, puis R2

    def test_cap(self):
        u, c = self.units()
        s = N.select_units(u, c, cap=2).set_index("order")
        self.assertEqual([s.loc[o, "status"] for o in (1, 4, 2)], ["queued", "queued", "over_cap"])


class NonFiler(unittest.TestCase):
    def test_prefixes(self):
        self.assertTrue(N.is_non_filer("NF:SOFTBANK"))
        self.assertTrue(N.is_non_filer("LAB:OPENAI"))
        self.assertFalse(N.is_non_filer("CP:softbank group corp"))
        self.assertFalse(N.is_non_filer("NVDA"))


class LevelOne(unittest.TestCase):
    """Niveau 1 (D-0044, point 7) : alias du groupe, entités désignées « SoftBank », noms sans extrait."""

    def test_resolution(self):
        cfg = {"labs": [], "non_filers": [{"name": "SoftBank", "ref": "NF:SOFTBANK"}],
               "confirmed_entities": [
                   {"name": "SoftBank Group Corp.", "group": "NF:SOFTBANK", "treatment": "parent"},
                   {"name": "SVF Yellow (USA) Corporation", "group": "NF:SOFTBANK", "treatment": "undetermined"}],
               "entity_aliases": [{"alias": "SoftBank", "of": "NF:SOFTBANK"}, {"alias": "SBG", "of": "NF:SOFTBANK"}]}
        names = ["Softbank", "SBG", "SVF Yellow (USA) Corporation", "SoftBank Group Corporation", "SoftBank Group"]
        _, reg = E.build({"meta": {}}, cfg, {n: False for n in names})
        g = {n: E.resolve(reg, n, "2024-06-30")[1] for n in names}
        self.assertEqual([g[n] for n in names[:4]], ["NF:SOFTBANK"] * 4)
        self.assertIsNone(g["SoftBank Group"])      # nom sans extrait : en attente, hors du groupe


if __name__ == "__main__":
    unittest.main()
