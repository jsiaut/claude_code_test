"""Piste des non-déposants de la découverte (D-0044) : filtre du scan, règle de lecture, plafond.

Lancement : python3 -m unittest discover -s tests -t .
"""
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

    def test_new_units_form_their_own_capped_file(self):
        """D-0058, point 24 : l'état d'une unité connue se garde sous sa clé ; les unités nouvelles
        forment une file propre, R1 puis R2, avec leur plafond."""
        u, c = self.units()
        u["value_sha"] = None
        prior = N.select_units(u[u["order"].isin([1, 2, 3])], c, cap=1)          # 2 au-delà du plafond
        more = pd.DataFrame([{"order": o, "pass": "B", "rank": 1, "cik": "1", "kind": "note", "latest": False,
                              "co_refs": "NVDA", "groups": "NF:SOFTBANK", "adsh": f"a{o}", "doc": f"d{o}",
                              "value_sha": None} for o in (6, 7)])
        s = N.select_with_prior(pd.concat([u, more], ignore_index=True), c, prior, cap=2, file="D-0058")
        s = s.set_index("order")
        self.assertEqual([s.loc[o, "status"] for o in (1, 2, 3)], ["queued", "over_cap", "out_of_rule"])
        self.assertEqual([s.loc[o, "file"] for o in (1, 4)], ["D-0044", "D-0058"])
        self.assertEqual([int(s.loc[o, "queue"]) for o in (4, 6, 7)], [1, 2, 3])      # file nouvelle
        self.assertEqual([s.loc[o, "status"] for o in (4, 6, 7, 5)], ["queued", "queued", "over_cap", "out_of_rule"])

    def test_own_filings_of_the_group_stay_out_of_the_new_file(self):
        u, c = self.units()
        u["value_sha"], u["date"] = None, "20260601"
        prior = N.select_units(u[u["order"] == 3], c, cap=10)
        s = N.select_with_prior(u, c, prior, cap=10, file="D-0058", own={"1": "2026-09-30", "2": "none"})
        s = s.set_index("order")
        self.assertEqual(s.loc[1, "status"], "queued")            # dépôt antérieur à l'entrée du déposant
        self.assertEqual(s.loc[3, "status"], "out_of_rule")       # unité connue : état gardé
        u.loc[u["order"] == 1, "date"] = "20261001"
        s = N.select_with_prior(u, c, prior, cap=10, file="D-0058", own={"1": "2026-09-30"}).set_index("order")
        self.assertEqual(s.loc[1, "status"], "own_group")
        self.assertTrue(pd.isna(s.loc[1, "queue"]))


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


def html(*lines):
    return ("<html><body>" + "".join(f"<p>{l}</p>" for l in lines) + "</body></html>").encode("utf-8")


class OwnFiling(unittest.TestCase):
    """Document d'enregistrement de la tête d'un groupe non déposant (D-0054, point 13)."""

    def test_notes_cut_by_numbered_titles_in_each_set(self):
        raw = html("Index to Consolidated Financial Statements",
                   "Notes to Consolidated Financial Statements | F-7",
                   "CONSOLIDATED BALANCE SHEETS", "Total assets | 10",
                   "NOTES TO CONSOLIDATED FINANCIAL STATEMENTS",
                   "1. BASIS OF PREPARATION", "The company was formed in 2024.",
                   "2. DEBT", "1. The facility bears interest.", "F-9", "EXAMPLE LIMITED",
                   "NOTES TO CONSOLIDATED FINANCIAL STATEMENTS", "The loan matures in 2030.",
                   "CONDENSED CONSOLIDATED BALANCE SHEETS", "Total assets | 12",
                   "NOTES TO CONDENSED CONSOLIDATED FINANCIAL STATEMENTS",
                   "1. OVERVIEW", "Interim overview.", "PART II", "Exhibits")
        notes = N.financial_notes_html(raw, running_headers=["EXAMPLE LIMITED"])
        self.assertEqual([(n["set"], n["number"], n["title"]) for n in notes],
                         [(0, 1, "BASIS OF PREPARATION"), (0, 2, "DEBT"), (1, 1, "OVERVIEW")])
        debt = notes[1]["text"]
        self.assertIn("1. The facility bears interest.", debt)      # puce numérotée, pas un titre
        self.assertIn("The loan matures in 2030.", debt)             # la note continue après le saut de page
        self.assertNotIn("F-9", debt)
        self.assertNotIn("EXAMPLE LIMITED", debt)
        self.assertNotIn("Total assets", debt)
        self.assertNotIn("Exhibits", notes[2]["text"])

    def test_section_bounded_by_next_table_of_contents_title(self):
        raw = html("Principal Shareholders | 141", "Certain Relationships and Related Party Transactions | 143",
                   "Description of Certain Indebtedness | 149",
                   "<b>Certain Relationships and Related Party Transactions</b>", "We sold shares to an investor.",
                   "<b>DESCRIPTION OF CERTAIN INDEBTEDNESS</b>", "Vendor financing.")
        sec = N.toc_section(raw, "Certain Relationships and Related Party Transactions")
        self.assertIn("We sold shares to an investor.", sec)
        self.assertNotIn("Vendor financing.", sec)

    def test_lines_of_the_registrant_go_to_its_non_filer_group(self):
        from pipeline.load import line_group
        b = {"block_kind": "discovery_note", "cik": "0002110365", "group_id": "NF:NSCALE"}
        self.assertEqual(line_group(b, {"2110365": "NF:NSCALE"}, {"2110365": "NSCALE Ltd"}), "NF:NSCALE")
        self.assertEqual(line_group(b, {}, {"2110365": "NSCALE Ltd"}), "CP:nscale ltd")   # sans l'entrée : groupe de contrepartie


if __name__ == "__main__":
    unittest.main()


class Efts(unittest.TestCase):
    """Une réponse d'erreur du service de recherche (« errorType ») n'est jamais gardée en cache."""

    def test_error_body_is_retried_and_never_cached(self):
        import json as _json
        import tempfile
        from pathlib import Path
        from pipeline import discovery as D
        bodies = [_json.dumps({"errorType": "ConnectionError"}).encode(),
                  _json.dumps({"hits": {"total": {"value": 0, "relation": "eq"}, "hits": []}}).encode()]

        class Client:
            def get(self, url):
                return bodies.pop(0), None
        old = D.SEARCH_DIR
        with tempfile.TemporaryDirectory() as d:
            D.SEARCH_DIR = Path(d)
            try:
                data, _, cached = D._efts(Client(), {"q": '"X"'}, retries=2, pause=0)
                self.assertIn("hits", data)
                self.assertFalse(cached)
                kept = list(Path(d).glob("*/*.json.zst"))
                self.assertEqual(len(kept), 1)
                data2, _, cached2 = D._efts(Client(), {"q": '"X"'}, retries=0, pause=0)   # relue du cache
                self.assertTrue(cached2)
            finally:
                D.SEARCH_DIR = old

