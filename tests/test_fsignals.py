"""Signaux lus dans le texte (§4.5) : date de publicité d'un signal révélé par un amendement (D-0043) ; groupe sans aucun
rapport périodique (D-0057).

Lancement : python3 -m unittest discover -s tests -t .
"""
import unittest

import pandas as pd

from pipeline import fsignals as S


class FirstReport(unittest.TestCase):
    reps = pd.DataFrame({"accessionNumber": ["acc-10k", "acc-10ka"], "filingDate": ["2025-02-27", "2026-03-02"]})
    bl = [{"accession": "acc-10k", "content_key": "ck-orig"}, {"accession": "acc-10ka", "content_key": "ck-amend"}]

    def test_weakness_revealed_by_amendment(self):
        # le 10-K d'origine juge le contrôle efficace ; le 10-K/A de 2026 révèle la faiblesse
        obs = {"ck-orig": [{"signal": "material_weakness", "signal_present": False}],
               "ck-amend": [{"signal": "material_weakness", "signal_present": True}]}
        self.assertEqual(S._first_report(self.reps, self.bl, obs, "material_weakness"), "2026-03-02")

    def test_weakness_in_original_report(self):
        obs = {"ck-orig": [{"signal": "material_weakness", "signal_present": True}],
               "ck-amend": [{"signal": "material_weakness", "signal_present": True}]}
        self.assertEqual(S._first_report(self.reps, self.bl, obs, "material_weakness"), "2025-02-27")


class SansRapportPeriodique(unittest.TestCase):
    """SK hynix n'a déposé aucun 20-F avant l'as_of : ses trimestres n'ont aucun rapport, sans erreur (D-0057)."""
    filings = pd.DataFrame({"group_id": ["ASML"], "form": ["20-F"], "reportDate": ["2025-12-31"],
                            "filingDate": ["2026-02-11"], "accessionNumber": ["acc-asml"]})

    def test_groupe_sans_rapport(self):
        import datetime as dt
        m = S.reports_by_quarter(self.filings, "SKHY", {"end": dt.date(2025, 12, 31)})
        self.assertTrue(m.empty)
        self.assertIn("filingDate", m.columns)

    def test_groupe_avec_rapport(self):
        import datetime as dt
        m = S.reports_by_quarter(self.filings, "ASML", {"end": dt.date(2025, 12, 31)})
        self.assertEqual(list(m["accessionNumber"]), ["acc-asml"])


if __name__ == "__main__":
    unittest.main()
