"""D-0083 : après un as_of tiré en semaine, la fenêtre suivante d'une recherche plein texte reprend ce jour, pour les
dépôts acceptés après le tirage ; les fenêtres antérieures gardent leurs bornes, et les résultats ne se doublent pas
(point 5). Un symbole réservé pendant l'enregistrement d'une introduction n'est pas une cotation (point 11).

Lancement : python3 -m unittest tests.test_d0083 -v
"""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from pipeline import cache, config, discovery, nport


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


class RegistrationListing(unittest.TestCase):
    """Point 11 : sans prospectus d'introduction, une entité dont le premier dépôt est un enregistrement d'introduction
    n'est cotée qu'au premier dépôt de prise d'effet ou de cotation, et ne l'est pas sans lui."""

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.old, config.CACHE = config.CACHE, Path(self.d.name)

    def tearDown(self):
        config.CACHE = self.old
        self.d.cleanup()

    def _subs(self, cik, filings):
        recent = {"form": [f for _, f in filings], "filingDate": [d for d, _ in filings]}
        cache.write(cache.api_path(str(cik).zfill(10), "submissions", "2026-10-31"),
                    json.dumps({"filings": {"recent": recent, "files": []}}).encode())

    REG = [("2026-10-26", "S-1"), ("2026-10-09", "DRS/A"), ("2026-06-01", "DRS")]

    def test_symbol_reserved_during_registration_is_not_a_listing(self):
        self._subs(7, self.REG)
        self.assertEqual(nport.listing_date("7", "2026-10-31"), nport.NOT_LISTED)
        rows = [{"record_kind": "entity", "entity_id": "name:x pbc", "cik": "7"}]
        self.assertEqual(nport.listing(rows, "2026-10-31", {"0000000007": ["ANT"]}), {})

    def test_effectiveness_or_exchange_registration_dates_the_listing(self):
        self._subs(7, [("2026-11-06", "EFFECT"), ("2026-11-04", "8-A12B")] + self.REG)
        self.assertEqual(nport.listing_date("7", "2026-11-30"), "2026-11-04")
        self.assertEqual(nport.listing_date("7", "2026-10-31"), nport.NOT_LISTED)    # après l'as_of : ignorés
        rows = [{"record_kind": "entity", "entity_id": "name:x pbc", "cik": "7"}]
        self.assertEqual(nport.listing(rows, "2026-11-30", {"0000000007": ["ANT"]}), {"name:x pbc": "2026-11-04"})

    def test_an_ipo_prospectus_still_gives_the_date(self):
        self._subs(7, [("2026-11-07", "424B4"), ("2026-11-06", "EFFECT")] + self.REG)
        self.assertEqual(nport.listing_date("7", "2026-11-30"), "2026-11-07")

    def test_other_entities_without_prospectus_stay_listed_over_the_period(self):
        self._subs(8, [("2026-08-01", "10-Q"), ("2026-03-01", "10-K"), ("2025-05-01", "S-1"), ("2003-02-01", "10-K")])
        self.assertEqual(nport.listing_date("8", "2026-10-31"), "")
        self._subs(9, [("2026-09-01", "S-1"), ("2024-01-15", "D")])        # premier dépôt un Form D : hors de la règle
        self.assertEqual(nport.listing_date("9", "2026-10-31"), "")


if __name__ == "__main__":
    unittest.main()
