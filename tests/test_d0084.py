"""D-0084 : mode de reconstruction, sur un conteneur neuf. Catalogues et files se recalculent sur toute la période,
puis se ramènent aux clés que garde le commit de référence ; hors de ce mode, rien ne change.

Lancement : python3 -m unittest tests.test_d0084 -v
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline import config, discovery, montages, reconstruction, update


class _Mode:
    """Mode de reconstruction actif, avec des clés gardées données."""

    def __init__(self, keys=(), accessions=()):
        self.k, self.a = frozenset(keys), frozenset(accessions)

    def __enter__(self):
        self.env = os.environ.get(reconstruction.ENV)
        os.environ[reconstruction.ENV] = "abc1234"
        self.old = reconstruction.keys, reconstruction.accessions
        reconstruction.keys = lambda: self.k
        reconstruction.accessions = lambda: self.a
        return self

    def __exit__(self, *a):
        reconstruction.keys, reconstruction.accessions = self.old
        if self.env is None:
            os.environ.pop(reconstruction.ENV, None)
        else:
            os.environ[reconstruction.ENV] = self.env


class Switch(unittest.TestCase):
    def test_off_by_default(self):
        self.assertIsNone(reconstruction.reference()) if not os.environ.get(reconstruction.ENV) else None

    def test_previous_run_is_ignored_in_reconstruction(self):
        with _Mode():
            self.assertIsNone(config.previous_as_of())

    def test_previous_run_is_kept_outside(self):
        if os.environ.get(reconstruction.ENV):
            self.skipTest("mode de reconstruction actif dans l'environnement")
        prev = config._parsed()["as_of_previous"]
        self.assertEqual(config.previous_as_of(), prev[-1] if prev else None)


class Admission(unittest.TestCase):
    def test_kept_keys_only_without_cap(self):
        with _Mode(keys={"k1", "k2", "k3"}, accessions={"0001-26-1"}):
            adm = update.Admission(1, (), "2026-10-27")
            self.assertTrue(adm.take("k1", "2020-01-01"))
            self.assertTrue(adm.take("k2", "2026-10-30"))           # au-delà du plafond, mais gardée
            self.assertTrue(adm.take("0001-26-1", "2026-10-30"))     # clé d'accession
            self.assertFalse(adm.take("k9", "2026-10-30"))          # ni lue ni arrêtée à l'en-tête

    def test_outside_the_mode_the_cap_holds(self):
        if os.environ.get(reconstruction.ENV):
            self.skipTest("mode de reconstruction actif dans l'environnement")
        adm = update.Admission(1, ())
        self.assertTrue(adm.take("a", "2026-10-30"))
        self.assertFalse(adm.take("b", "2026-10-30"))


class Searches(unittest.TestCase):
    def test_rows_seen_twice_count_once(self):
        df = pd.DataFrame([{"term": "Oracle", "id": "x:1"}, {"term": "Oracle", "id": "x:1"},
                           {"term": "Oracle", "id": "x:2"}])
        with _Mode():
            self.assertEqual(discovery.keep_new_rows(None, df, ["term", "id"])["id"].tolist(), ["x:1", "x:2"])

    def test_versioned_query_logs_are_not_rewritten(self):
        with tempfile.TemporaryDirectory() as d, _Mode():
            old = config.WORK
            config.WORK = Path(d)
            try:
                log = Path(d) / "discovery" / "efts_queries.jsonl"
                discovery._log_query({"term": "Oracle", "start": "2017-01-01"}, log)
                self.assertFalse(log.exists())
                self.assertTrue((Path(d) / "tmp" / "reconstruction" / "discovery" / "efts_queries.jsonl").exists())
            finally:
                config.WORK = old


class HistoryAccessions(unittest.TestCase):
    def test_read_filings_of_now_excluded_filers_stay_read(self):
        with _Mode():
            old = reconstruction.accessions_of
            reconstruction.accessions_of = lambda prefix: frozenset({"0001083301-26-000166"}) \
                if prefix == "discovery_" else frozenset()
            try:
                self.assertEqual(discovery._history_accessions(), {"0001083301-26-000166"})
            finally:
                reconstruction.accessions_of = old
        if not os.environ.get(reconstruction.ENV):
            self.assertEqual(discovery._history_accessions(), set())


class Montages(unittest.TestCase):
    def test_a_read_window_is_never_already_read(self):
        from pipeline import blocks
        paras = ["Paragraph one names Blue Owl.", "Paragraph two."]
        ck = blocks.content_key("\n".join(paras), [])
        with _Mode(keys={ck}):
            self.assertTrue(montages._kept(paras))
            self.assertFalse(montages._kept(["Other text."]))
        if not os.environ.get(reconstruction.ENV):
            self.assertFalse(montages._kept(paras))


class Restrict(unittest.TestCase):
    def test_catalog_keeps_kept_keys_in_order_once(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.jsonl"
            rows = [{"content_key": k, "n": i} for i, k in enumerate(["b", "x", "a", "b"])]
            p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            with _Mode(keys={"a", "b"}):
                r = reconstruction.restrict([p])
            kept = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([(x["content_key"], x["n"]) for x in kept], [("b", 0), ("a", 2)])
            self.assertEqual(r["c.jsonl"], {"kept": 2, "removed": 2})


if __name__ == "__main__":
    unittest.main()
