"""D-0083 : après un as_of tiré en semaine, la fenêtre suivante d'une recherche plein texte reprend ce jour, pour les
dépôts acceptés après le tirage ; les fenêtres antérieures gardent leurs bornes, et les résultats ne se doublent pas.

Lancement : python3 -m unittest tests.test_d0083 -v
"""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline import config, discovery


class _Config:
    def __init__(self, text):
        self.text = text

    def __enter__(self):
        self.d = tempfile.TemporaryDirectory()
        p = Path(self.d.name) / "config.yaml"
        p.write_text(self.text, encoding="utf-8")
        self.old, config.CONFIG_PATH = config.CONFIG_PATH, p
        return self

    def __exit__(self, *a):
        config.CONFIG_PATH = self.old
        self.d.cleanup()


BASE = 'as_of: "2026-10-31"\nas_of_previous: ["2026-10-07", "2026-10-24", "2026-10-27"]\n'


class OverlapWindows(unittest.TestCase):
    def test_window_after_a_weekday_as_of_takes_its_day_again(self):
        with _Config(BASE + 'search_overlap_from: "2026-10-27"\n'):
            self.assertEqual(config.search_windows("2017-01-01"),
                             [("2017-01-01", "2026-10-07"), ("2026-10-08", "2026-10-24"), ("2026-10-25", "2026-10-27"),
                              ("2026-10-27", "2026-10-31")])

    def test_earlier_windows_keep_their_bounds(self):
        with _Config(BASE + 'search_overlap_from: "2026-10-27"\n'):
            self.assertEqual(config.search_windows("2017-01-01")[:3],
                             [("2017-01-01", "2026-10-07"), ("2026-10-08", "2026-10-24"), ("2026-10-25", "2026-10-27")])

    def test_without_the_key_windows_do_not_overlap(self):
        with _Config(BASE):
            self.assertEqual(config.search_windows("2017-01-01")[-1], ("2026-10-28", "2026-10-31"))

    def test_results_of_the_day_seen_twice_are_kept_once(self):
        old = pd.DataFrame([{"term": "Oracle", "id": "0001-26-1:ex10.htm", "file_date": "2026-10-27"}])
        new = pd.DataFrame([{"term": "Oracle", "id": "0001-26-1:ex10.htm", "file_date": "2026-10-27"},
                            {"term": "Oracle", "id": "0001-26-2:ex10.htm", "file_date": "2026-10-27"}])
        out = discovery.keep_new_rows(old, new, ["term", "id"])
        self.assertEqual(out["id"].tolist(), ["0001-26-1:ex10.htm", "0001-26-2:ex10.htm"])


if __name__ == "__main__":
    unittest.main()
