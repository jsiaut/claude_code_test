"""D-0073 : une seule source pour l'as_of, la clé as_of de config.yaml ; bornes `as_of` ; gardes contre deux as_of.

Lancement : python3 -m unittest discover -s tests -t .
"""
import json
import re
import tempfile
import unittest
from pathlib import Path

import yaml

from pipeline import config

ROOT = Path(__file__).resolve().parents[1]


class _Attrs:
    """Remplace des attributs de modules le temps d'un test."""
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


class SingleSource(unittest.TestCase):
    def test_key_is_the_as_of_and_an_argument_must_equal_it(self):
        with tempfile.TemporaryDirectory() as d, _config(d, 'as_of: "2026-03-31"\n'):
            self.assertEqual(config.as_of(), "2026-03-31")
            self.assertEqual(config.as_of("2026-03-31"), "2026-03-31")
            with self.assertRaises(SystemExit) as cm:
                config.as_of("2026-10-07")
            self.assertIn("D-0073", str(cm.exception))

    def test_missing_or_malformed_key_stops(self):
        for text in ("a: 1\n", 'as_of: "2026-13-01"\n', "as_of: as_of\n", "as_of: 20261007\n"):
            with tempfile.TemporaryDirectory() as d, _config(d, text):
                with self.assertRaises(SystemExit, msg=text):
                    config.load()

    def test_unquoted_yaml_date_is_read_as_text(self):
        with tempfile.TemporaryDirectory() as d, _config(d, "as_of: 2026-03-31\n"):
            self.assertEqual(config.load()["as_of"], "2026-03-31")


class Bounds(unittest.TestCase):
    def test_token_replaced_in_values_only(self):
        node = {"as_of": "as_of", "period": ["2019-01-01", "as_of"], "x": {"end": "as_of", "start": "2017-01-01"},
                "note": "publiée après l'as_of", "status": "after_as_of", "n": [{"tickers": "as_of"}, 3, None]}
        out = config.resolve_as_of(node, "2026-03-31")
        self.assertEqual(out, {"as_of": "2026-03-31", "period": ["2019-01-01", "2026-03-31"],
                               "x": {"end": "2026-03-31", "start": "2017-01-01"}, "note": "publiée après l'as_of",
                               "status": "after_as_of", "n": [{"tickers": "2026-03-31"}, 3, None]})

    def test_load_follows_the_key(self):
        text = 'as_of: "2026-03-31"\nnport: {period: ["2019-10-01", as_of], unlisted: {tickers: as_of}}\n'
        with tempfile.TemporaryDirectory() as d, _config(d, text):
            c = config.load()
            self.assertEqual(c["nport"]["period"], ["2019-10-01", "2026-03-31"])
            from pipeline import nport
            self.assertEqual(nport.tickers_day(c), "2026-03-31")
            self.assertEqual(nport.tickers_day({"nport": {"unlisted": {"tickers": "2026-01-02"}}}), "2026-01-02")

    def test_repository_bounds_are_written_as_of(self):
        """Les 19 bornes de D-0073 (point 2) s'écrivent `as_of` dans config.yaml et valent l'as_of une fois lues."""
        raw = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        c, a = config.load(), config.as_of()
        paths = [("lender_liabilities", "tenders", "window", 1), ("softbank_deep", "period", 1),
                 *[("montages", m, "period", 1) for m in ("meta_hyperion", "athene_whco", "galaxy_helios",
                                                         "softbank_corpus", "stargate", "labs_corpus", "labs_tagged",
                                                         "anthropic_chain", "sec_letters", "labs_contracts", "labs_events",
                                                         "backlog", "backlog_values")],
                 ("montages", "labs_contracts", "replay", "end"), ("nport", "period", 1),
                 ("nport", "unlisted", "tickers"), ("ownership", "period", 1)]
        self.assertEqual(len(paths), 19)

        def get(node, path):
            for k in path:
                node = node[k]
            return node
        for path in paths:
            self.assertEqual(get(raw, path), config.AS_OF_TOKEN, path)
            self.assertEqual(get(c, path), a, path)


class NoHardCodedDate(unittest.TestCase):
    def test_no_constant_and_no_quoted_as_of_in_code(self):
        from pipeline import discovery, lender_liabilities, sb_own
        for m in (discovery, lender_liabilities, sb_own):
            self.assertFalse(hasattr(m, "AS_OF"), m.__name__)
        a = config.as_of()
        for f in sorted((ROOT / "pipeline").glob("*.py")):
            text = f.read_text(encoding="utf-8")
            self.assertNotIn(f'"{a}"', text, f.name)
            self.assertNotIn(f"'{a}'", text, f.name)
            self.assertNotIn("import AS_OF", text, f.name)
        self.assertIsNone(re.search(r"^AS_OF\s*\??=", (ROOT / "Makefile").read_text(encoding="utf-8"), re.M))

    def test_in_period_defaults_to_the_key(self):
        from pipeline import discovery
        a = config.as_of()
        arch = [{"name": "avant", "filed_from": "2019-01-01", "filed_to": "2019-03-31"},
                {"name": "après", "filed_from": "9999-01-01", "filed_to": "9999-03-31"}]
        self.assertEqual([x["name"] for x in discovery.in_period(arch, "2017-01-01")], ["avant"])
        self.assertEqual([x["name"] for x in discovery.in_period(arch, "2017-01-01", a)], ["avant"])


class Guards(unittest.TestCase):
    def test_check_as_of(self):
        a = config.as_of()
        self.assertEqual(config.check_as_of(a, "x.json", "refaire"), a)
        with self.assertRaises(SystemExit) as cm:
            config.check_as_of("2001-01-01", "x.json", "refaire")
        self.assertIn("x.json porte l'as_of 2001-01-01", str(cm.exception))
        self.assertIn("refaire", str(cm.exception))

    def test_commands_refuse_another_argument_before_any_request(self):
        from pipeline import formd, lender_liabilities, phase2_fetch
        for fn in (formd.collect, lender_liabilities.announcement_units, phase2_fetch.run):
            with self.assertRaises(SystemExit, msg=fn.__module__):
                fn("2001-01-01")

    def test_assemble_and_phase1_stop_on_another_phase0(self):
        from pipeline import assemble, phase1_run
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "phase0.json").write_text(json.dumps({"as_of": "2001-01-01", "calendars": {}}))
            with _Attrs((config, "DB_DIR", Path(d))):
                for fn in (assemble.run, phase1_run.run):
                    with self.assertRaises(SystemExit) as cm:
                        fn(config.as_of())
                    self.assertIn("relancer la phase 0", str(cm.exception))

    def test_render_stops_on_tables_of_another_as_of(self):
        from pipeline import render
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "work" / "tmp" / "assemble_stats.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"as_of": "2001-01-01"}))
            with _Attrs((config, "ROOT", Path(d))):
                with self.assertRaises(SystemExit) as cm:
                    render.main()
                self.assertIn("relancer l'assemblage", str(cm.exception))

    def test_reader_pass_of_another_as_of_stops_and_no_file_takes_the_key(self):
        from pipeline import reader
        with tempfile.TemporaryDirectory() as d:
            run = Path(d) / "run.json"
            with _Attrs((reader, "RUN", run), (reader, "LIST", None)):
                info = reader._run_info()
                self.assertEqual(info["as_of"], config.as_of())        # jamais la date du jour
                run.write_text(json.dumps({"as_of": config.as_of(), "pass_id": "p1"}))
                self.assertEqual(reader._run_info(), {"as_of": config.as_of(), "pass_id": "p1"})
                run.write_text(json.dumps({"as_of": "2001-01-01", "pass_id": "p0"}))
                with self.assertRaises(SystemExit) as cm:
                    reader._run_info()
                self.assertIn("ouvrir une passe nouvelle", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
