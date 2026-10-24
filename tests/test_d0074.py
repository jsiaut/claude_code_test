"""D-0074 : mise à jour d'une exécution à l'autre (fenêtres des recherches, ressources vivantes datées, files plafonnées).

Lancement : python3 -m unittest discover -s tests -t .
"""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline import cache, config, discovery, edgar, lender, update


class _Attrs:
    def __init__(self, *triples):
        self.triples, self.old = triples, []

    def __enter__(self):
        for mod, k, v in self.triples:
            self.old.append((mod, k, getattr(mod, k)))
            setattr(mod, k, v)

    def __exit__(self, *a):
        for mod, k, v in reversed(self.old):
            setattr(mod, k, v)


def _config(d, text):
    p = Path(d) / "config.yaml"
    p.write_text(text, encoding="utf-8")
    return _Attrs((config, "CONFIG_PATH", p))


UPDATE = 'as_of: "2026-10-24"\nas_of_previous: ["2026-10-07"]\n'


class Windows(unittest.TestCase):
    def test_cut_at_previous_as_of(self):
        with tempfile.TemporaryDirectory() as d, _config(d, UPDATE):
            self.assertEqual(config.previous_as_of(), "2026-10-07")
            self.assertEqual(config.search_windows("2017-01-01"),
                             [("2017-01-01", "2026-10-07"), ("2026-10-08", "2026-10-24")])
            self.assertEqual(config.search_windows("2026-10-07"),
                             [("2026-10-07", "2026-10-07"), ("2026-10-08", "2026-10-24")])
            self.assertEqual(config.search_windows("2026-10-10"), [("2026-10-10", "2026-10-24")])

    def test_first_execution_has_one_window(self):
        with tempfile.TemporaryDirectory() as d, _config(d, 'as_of: "2026-10-07"\n'):
            self.assertIsNone(config.previous_as_of())
            self.assertEqual(config.search_windows("2017-01-01"), [("2017-01-01", "2026-10-07")])

    def test_previous_must_be_increasing_and_before_as_of(self):
        for prev in ('["2026-10-24"]', '["2026-10-07", "2026-01-01"]', '["2026-10-07", "2026-10-07"]', '["x"]'):
            with tempfile.TemporaryDirectory() as d, _config(d, f'as_of: "2026-10-24"\nas_of_previous: {prev}\n'):
                with self.assertRaises(SystemExit, msg=prev):
                    config.load()


class DatedResources(unittest.TestCase):
    def test_version_served_at_as_of(self):
        with tempfile.TemporaryDirectory() as d, _Attrs((config, "CACHE", Path(d))):
            legacy = Path(d) / "x" / "page.html"
            self.assertIsNone(cache.dated(("x",), "page", ".html", "2026-10-24", legacy=legacy))
            cache.write(legacy, b"v0")
            self.assertEqual(cache.dated(("x",), "page", ".html", "2026-10-07", legacy=legacy), legacy)
            cache.write(cache.dated_path(("x",), "page", ".html", "2026-10-09"), b"v1")
            cache.write(cache.dated_path(("x",), "page", ".html", "2026-10-24"), b"v2")
            # la plus récente au plus de l'as_of ; à défaut l'ancien nom fixe, puis la plus ancienne datée
            self.assertEqual(cache.dated(("x",), "page", ".html", "2026-10-24", legacy=legacy).name,
                             "page_2026-10-24.html.zst")
            self.assertEqual(cache.dated(("x",), "page", ".html", "2026-10-20", legacy=legacy).name,
                             "page_2026-10-09.html.zst")
            self.assertEqual(cache.dated(("x",), "page", ".html", "2026-10-07", legacy=legacy), legacy)
            self.assertEqual(cache.dated(("x",), "page", ".html", "2026-10-07").name, "page_2026-10-09.html.zst")

    def test_pulled_once_per_execution(self):
        class Client:
            calls = 0

            def get(self, url):
                Client.calls += 1
                return b"<html>" + url.encode() + b"</html>", {}
        with tempfile.TemporaryDirectory() as d, _Attrs((config, "CACHE", Path(d))):
            c = Client()
            raw, p = edgar.dated_resource(c, "https://www.sec.gov/p", ("x",), "page", ".html", "2026-10-24")
            raw2, _ = edgar.dated_resource(c, "https://www.sec.gov/p", ("x",), "page", ".html", "2026-10-24")
            self.assertEqual((raw, raw2, Client.calls, p.name), (raw, raw, 1, "page_2026-10-24.html.zst"))
            edgar.dated_resource(c, "https://www.sec.gov/p", ("x",), "page", ".html", "2026-11-30")
            self.assertEqual(Client.calls, 2)                  # une exécution nouvelle retire, sans écraser
            self.assertTrue(cache.dated_path(("x",), "page", ".html", "2026-10-24").exists())

    def test_bdc_page_links(self):
        html = ('<a href="/files/datastandardsinnovation/data/business-development-company-bdc-data-sets/2026_09_bdc.zip" '
                'download>2026 September BDC</a><a href="/files/datastandardsinnovation/data/'
                'business-development-company-bdc-data-sets/2025q4_bdc.zip">x</a><a href="/files/other.zip">y</a>')
        links = lender.archive_links(html)
        self.assertEqual(list(links), ["2026_09_bdc", "2025q4_bdc"])
        self.assertTrue(links["2026_09_bdc"].startswith("https://www.sec.gov/files/"))


class Admission(unittest.TestCase):
    def test_first_execution_is_the_plain_cap(self):
        a = update.Admission(2)
        self.assertEqual([a.take(k, "2026-01-01", g) for k, g in
                          [("a", "G"), ("b", "G"), ("c", "G"), ("d", "H")]], [True, True, False, True])

    def test_old_units_keep_their_state_new_ones_get_their_own_queue(self):
        a = update.Admission(2, admitted={"r1", "r2"}, since="2026-10-07")
        got = [a.take("n1", "2026-10-20"), a.take("r1", "2026-09-01"), a.take("x", "2026-09-02"),
               a.take("n2", "2026-10-08"), a.take("n3", "2026-10-21"), a.take("r2", "2026-10-07")]
        self.assertEqual(got, [True, True, False, True, False, True])

    def test_catalog_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.jsonl"
            self.assertEqual(update.catalog_keys(p), set())
            p.write_text("\n".join(json.dumps(b) for b in [{"content_key": "k1", "montage": "m"},
                                                          {"content_key": "k2", "montage": "z"}]) + "\n")
            self.assertEqual(update.catalog_keys(p, where=lambda b: b["montage"] == "m"), {"k1"})


class AdditiveSearch(unittest.TestCase):
    def test_keep_new_rows(self):
        old = pd.DataFrame([{"term": "A", "id": "1"}, {"term": "A", "id": "1"}, {"term": "B", "id": "2"}])
        new = pd.DataFrame([{"term": "A", "id": "1"}, {"term": "A", "id": "3"}])
        out = discovery.keep_new_rows(old, new, ["term", "id"])
        self.assertEqual(list(zip(out["term"], out["id"])), [("A", "1"), ("A", "1"), ("B", "2"), ("A", "3")])
        self.assertIs(discovery.keep_new_rows(old, pd.DataFrame(), ["term", "id"]), old)
        self.assertIs(discovery.keep_new_rows(None, new, ["term", "id"]), new)

    def test_only_new_windows_of_known_terms_are_searched(self):
        calls = []

        def harvest(client, term, forms, start, end, keep=None, log=None):
            calls.append((term, tuple(forms), start, end))
            return [{"term": term, "id": f"{term}:{forms[0]}:{end}"}]

        class NoNet:
            def __init__(self, *a, **k):
                self.stats = {"requests": 0}

            def get(self, url):
                raise AssertionError(url)
        with tempfile.TemporaryDirectory() as d, _config(d, UPDATE):
            hits = Path(d) / "efts.parquet"
            pd.DataFrame([{"term": "A", "id": "old"}]).to_parquet(hits, index=False)
            with _Attrs((discovery, "harvest", harvest), (discovery, "EFTS_HITS", hits),
                        (discovery, "lexicon", lambda cfg=None: [{"term": "A"}, {"term": "B"}]),
                        (discovery.net, "SecClient", NoNet), (config, "WORK", Path(d) / "work"),
                        (config, "DB_DIR", Path(d))):
                discovery.search()
            out = pd.read_parquet(hits)
        new = ("2026-10-08", "2026-10-24")
        self.assertEqual([c for c in calls if c[0] == "A"],
                         [("A", tuple(discovery.EX10_FORMS)) + new, ("A", ("D",)) + new])
        self.assertEqual(len([c for c in calls if c[0] == "B"]), 4)      # terme jamais cherché : toutes les fenêtres
        self.assertEqual(out["id"].iloc[0], "old")                         # résultats gardés en tête, dans leur ordre
        self.assertEqual(len(out), 1 + 6)

    def test_window_logged_once(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "q.jsonl"
            rec = {"term": "A", "start": "2026-10-08", "end": "2026-10-24", "status": "complete"}
            discovery._log_query(rec, log)
            discovery._log_query(dict(rec), log)
            discovery._log_query(dict(rec, end="2026-10-25"), log)
            self.assertEqual(len(log.read_text().splitlines()), 2)


class CarryOver(unittest.TestCase):
    def test_previous_blocks_verbatim_new_period_appended(self):
        prev = [{"content_key": "a", "filing_date": "2026-09-01", "x": 1}, {"content_key": "b", "filing_date": "2026-10-07"}]
        rec = [{"content_key": "b", "filing_date": "2026-10-07", "x": "recalcul"},       # ancienne : reprise telle quelle
               {"content_key": "c", "filing_date": "2026-10-20"},
               {"content_key": "a", "filing_date": "2026-10-21"},                       # texte déjà au catalogue : une lecture
               {"content_key": "z", "filing_date": "2026-08-01"}]                       # ancienne, absente : reste dehors
        self.assertEqual(update.carry_over(prev, rec, "2026-10-07"), prev + [{"content_key": "c", "filing_date": "2026-10-20"}])
        self.assertEqual(update.carry_over(prev, rec, None), rec)

    def test_previous_state_copied_once(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "cat.jsonl"
            p.write_text("v1\n")
            snap = update.previous_state(p, "2026-10-07")
            p.write_text("v2\n")
            self.assertEqual(update.previous_state(p, "2026-10-07"), snap)
            self.assertEqual((snap.name, snap.read_text()), ("cat.2026-10-07.jsonl", "v1\n"))


class Queues(unittest.TestCase):
    def test_discovery_units_keep_their_order(self):
        cols = ["order", "pass", "rank", "cik", "kind", "adsh", "doc", "date", "archive", "value_sha", "groups"]
        prev = pd.DataFrame([[1, "A", 1, "1", "exhibit_header", "a1", "d1", "2026-01-01", None, None, "G"],
                             [2, "A", 2, "2", "note", "a2", "d2", "2026-02-01", "x", "s2", "G"]], columns=cols)
        rec = pd.DataFrame([[1, "A", 1, "9", "exhibit_header", "a9", "d9", "2026-10-20", None, None, "G"],
                            [2, "A", 3, "1", "exhibit_header", "a1", "d1", "2026-01-01", None, None, "G"],
                            [3, "B", 4, "2", "note", "a2", "d2", "2026-02-01", "x", "s2", "G"]], columns=cols)
        from pipeline import discovery as D
        out = D.extend_units(prev, rec)
        self.assertEqual(list(zip(out["order"], out["adsh"], out["rank"])), [(1, "a1", 1), (2, "a2", 2), (3, "a9", 1)])

    def test_non_filer_units_new_file_with_its_own_cap(self):
        from pipeline import nf_discovery as NF
        cols = ["order", "pass", "rank", "cik", "kind", "adsh", "doc", "date", "value_sha", "co_refs", "latest",
                "groups", "rule", "queue", "status", "file"]
        prev = pd.DataFrame([[1, "A", 1, 11, "exhibit_header", "p1", "d", "2026-01-01", None, "G", True, "NF:X",
                              "R1", 1, "queued", "D-0044"]], columns=cols)
        rec = pd.DataFrame([[1, "A", 1, 12, "exhibit_header", "n1", "d", "2026-10-20", None, "G", True, "NF:X"],
                            [2, "A", 2, 11, "exhibit_header", "p1", "d", "2026-01-01", None, "G", True, "NF:X"],
                            [3, "A", 3, 13, "exhibit_header", "n2", "d", "2026-10-21", None, "G", True, "NF:X"],
                            [4, "A", 4, 14, "exhibit_header", "n3", "d", "2026-10-22", None, "", True, "NF:X"]],
                           columns=cols[:12])
        c = pd.DataFrame({"cik": [11, 12, 13, 14], "documented_amount": [None] * 4})
        out = NF.extend_with_prior(prev, rec, c, 1, "D-0074")
        self.assertEqual(out.iloc[0].to_dict(), prev.iloc[0].to_dict())                 # ancienne, telle quelle
        new = out.iloc[1:]
        self.assertEqual(list(new["adsh"]), ["n1", "n2", "n3"])
        self.assertEqual(list(new["order"]), [2, 3, 4])
        self.assertEqual(list(new["status"]), ["queued", "over_cap", "out_of_rule"])  # plafond de la file à part
        self.assertEqual(set(new["file"]), {"D-0074"})


    def test_foreign_prepares_only_new_period_units(self):
        from pipeline import foreign as F
        self.assertTrue(F.new_period({"date": "20210428"}, ""))             # première exécution : toutes
        self.assertFalse(F.new_period({"date": "20210428"}, "2026-10-07"))  # ancienne, état gardé
        self.assertFalse(F.new_period({"date": "20261007"}, "2026-10-07"))  # le jour de l'as_of précédent compris
        self.assertTrue(F.new_period({"date": "20261013"}, "2026-10-07"))


    def test_foreign_issuer_retained_only_if_a_unit_is_prepared(self):
        from pipeline import foreign as F
        inv = pd.DataFrame({"cik": ["1878848", "1263043", "999"]})
        sel = [{"cik": 1878848, "order": 10}, {"cik": 1263043, "order": 20}, {"cik": 1263043, "order": 21}]
        r = F.retention(inv, sel, {10: {}})
        self.assertEqual(r["selected"].tolist(), [True, False, False])
        self.assertEqual(r["held"].tolist(), [False, True, False])       # unités anciennes gardées, « non traitées »
        self.assertEqual(F.retention(inv, sel, {10: {}, 20: {}, 21: {}})["selected"].tolist(), [True, True, False])

    def test_unlisted_nport_lexicon_frozen_in_update(self):
        from pipeline import nport as N
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "lx.json"
            p.write_text(json.dumps({"version": "lx-old", "parts": {}, "legal": {}, "keep": {}}), encoding="utf-8")
            old_lp, old_prev = N.lexicon_path, N.config.previous_as_of
            N.lexicon_path = lambda v: p
            try:
                done = {"2026q3": {"status": "scanned", "lexicon": "lx-old", "retrieved": "2026-10-20T17:43:09+00:00"}}
                N.config.previous_as_of = lambda: "2026-10-07"
                self.assertEqual(N.frozen_lexicon(done)["version"], "lx-old")    # exécution nouvelle : lexique figé
                N.config.previous_as_of = lambda: None
                self.assertIsNone(N.frozen_lexicon(done))                        # première exécution : celui du jour
            finally:
                N.lexicon_path, N.config.previous_as_of = old_lp, old_prev


class DeltaAcrossRuns(unittest.TestCase):
    def test_cells_matched_across_as_of(self):
        import duckdb
        from pipeline import render as R
        con = duckdb.connect()
        con.execute("""CREATE TABLE c AS SELECT * FROM (VALUES ('q', '2026-06-30', '2026-10-24'), ('w', '2026-10-24', '2026-10-24'),
                       ('v', '2026-03-31', '2026-03-01'), ('n', '2026-09-30', '2026-10-24')) t(measure, period_end, as_of)""")
        con.execute("""CREATE TABLE p AS SELECT * FROM (VALUES ('q', '2026-06-30', '2026-10-07'), ('w', '2026-10-07', '2026-10-07'),
                       ('v', '2026-03-31', '2026-03-01')) t(measure, period_end, as_of)""")
        k = ("measure", "period_end", "as_of")
        rows = con.execute(f"SELECT c.measure FROM c JOIN p ON {R._same_run(k, '2026-10-24', '2026-10-07')} ORDER BY 1").fetchall()
        # trimestre, fenêtre jusqu'à la date de coupure et millésime daté se rapprochent ; le trimestre nouveau non
        self.assertEqual([r[0] for r in rows], ["q", "v", "w"])
        same = con.execute(f"SELECT count(*) FROM c JOIN p ON {R._same_run(k, '2026-10-07', '2026-10-07')}").fetchone()[0]
        self.assertEqual(same, 1)          # même as_of des deux côtés : égalité simple, seul le millésime se rapproche


class Phase0Index(unittest.TestCase):
    def test_argument_must_equal_the_key(self):
        from pipeline import phase0_index
        with self.assertRaises(SystemExit):
            phase0_index.run("2001-01-01")


if __name__ == "__main__":
    unittest.main()
