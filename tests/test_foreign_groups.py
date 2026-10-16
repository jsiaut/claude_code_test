"""Groupes émetteurs privés étrangers (D-0048) : sections du 20-F, unités 6-K, exercices sans
rapport trimestriel, ruptures d'historique.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import unittest

import pandas as pd

from pipeline import annex_e, calendar, events, phase0, sections, sixk

FILLER = "Management evaluated the effectiveness of the disclosure controls and procedures. " * 5


def page(*paragraphs):
    return ("<html><body>" + "".join(f"<p>{p}</p>" for p in paragraphs) + "</body></html>").encode("utf-8")


TOC = ("Item 7. | Major Shareholders and Related Party Transactions | 56", "Item 8. | Financial Information | 58",
       "Item 10. | Additional Information | 60", "Item 11. | Quantitative and Qualitative Disclosures | 75",
       "Item 15. | Controls and Procedures | 76", "Item 16A. | Audit Committee Financial Expert | 78")


class TwentyF(unittest.TestCase):
    def test_unlettered_subsections(self):
        # Nebius : sous-sections sans lettre ; sommaire et note des états financiers écartés
        raw = page(*TOC, "Item 7. Major Shareholders and Related Party Transactions.", "Major Shareholders",
                   "Holdings table. " * 40, "Related Party Transactions", "None.", "Item 8. Financial Information.",
                   "Item 10. Additional Information.", "Articles of Association", "Rights. " * 40, "Material Contracts",
                   "Share Purchase Agreement", "On February 4, 2024, the Company entered into a share purchase agreement.",
                   "Exchange Controls", "No exchange controls.", "Item 11. Quantitative and Qualitative Disclosures.",
                   "Item 15. Controls and Procedures.", FILLER, "Management concluded that internal control was not effective.",
                   "Item 16A. Audit Committee Financial Expert.", "Mr. X qualifies.",
                   "Notes to the consolidated financial statements", "Related Party Transactions",
                   "The Company sold services to an affiliate. " * 30)
        self.assertEqual(sections.item_7b_20f(raw), "Related Party Transactions\nNone.")
        c = sections.item_10c_20f(raw)
        self.assertTrue(c.startswith("Material Contracts"))
        self.assertIn("share purchase agreement", c)
        self.assertNotIn("exchange controls", c.lower())
        i15 = sections.item_15_20f(raw)
        self.assertTrue(i15.startswith("Item 15. Controls and Procedures."))
        self.assertIn("not effective", i15)
        self.assertNotIn("Audit Committee", i15)

    def test_lettered_subsections(self):
        raw = page("Item 7. Major Shareholders and Related Party Transactions", "A. Major Shareholders", "Table. " * 40,
                   "B. Related Party Transactions", "We lease offices from an entity controlled by a director.",
                   "C. Interests of Experts and Counsel", "Not applicable.", "Item 8. Financial Information",
                   "Item 10. Additional Information", "B. Memorandum and Articles", "Text. " * 40,
                   "C. Material Contracts", "Loan agreement with a bank.", "D. Exchange Controls", "None.",
                   "Item 11. Market Risk")
        self.assertEqual(sections.item_7b_20f(raw),
                         "B. Related Party Transactions\nWe lease offices from an entity controlled by a director.")
        self.assertEqual(sections.item_10c_20f(raw), "C. Material Contracts\nLoan agreement with a bank.")

    def test_missing_item(self):
        self.assertIsNone(sections.item_15_20f(page("Item 9A. Controls and Procedures", FILLER)))


CFG = {"foreign_6k": {"lexicon": ["agreement", "agreements", "notes due", "credit facility", "credit facilities", "lease"],
                      "group_names": [{"term": "Nebius", "ref": "NBIS"},
                                      {"term": "IREN", "ref": "IREN", "case_sensitive": True}]},
       "discovery": {"lexicon": {"seed": [{"term": "Microsoft", "ref": "MSFT"},
                                          {"term": "Meta", "ref": "META", "case_sensitive": True}]}}}


class SixK(unittest.TestCase):
    def test_lexicon_excludes_own_name(self):
        rx = sixk.lexicon_rx("NBIS", CFG)
        self.assertIsNone(rx.search("Nebius reports results"))
        self.assertTrue(rx.search("IREN signs with Microsoft"))
        rx = sixk.lexicon_rx("IREN", CFG)
        self.assertIsNone(rx.search("IREN reports results"))
        self.assertTrue(rx.search("a deal with nebius"))

    def test_terms_whole_words_and_case(self):
        rx = sixk.lexicon_rx("NBIS", CFG)
        self.assertTrue(rx.search("new Credit Facilities were signed"))
        self.assertTrue(rx.search("Convertible Senior Notes Due 2030"))
        self.assertIsNone(rx.search("the leaseholds and the agreementless"))
        self.assertIsNone(rx.search("a siren and metadata"))           # IREN et Meta : casse et mot entier
        self.assertIsNone(rx.search("iren"))
        self.assertTrue(rx.search("Meta"))

    def test_windows_merge(self):
        rx = sixk.lexicon_rx("NBIS", CFG)
        paras = [f"p{i}" for i in range(15)]
        paras[3], paras[6], paras[12] = "an agreement", "a lease", "Microsoft"
        self.assertEqual(sixk.windows(paras, rx, 2), [[1, 9], [10, 15]])
        paras[11] = "credit facility"                                  # fenêtres contiguës : fondues
        self.assertEqual(sixk.windows(paras, rx, 2), [[1, 15]])

    def test_incorporation(self):
        t = ("This report on Form 6-K is hereby incorporated by reference into the Company's registration statements "
             "on Form F-3 (File No. 333-1). Other text.")
        inc, quote, doc = sixk.incorporation([("d.htm", "Press release."), ("e.htm", t)])
        self.assertTrue(inc)
        self.assertEqual(doc, "e.htm")
        self.assertIn("incorporated by reference", quote)
        self.assertEqual(sixk.incorporation([("d.htm", "Press release.")])[0], False)


class AnnualOnly(unittest.TestCase):
    def test_year_without_quarterly_reports_is_split(self):
        f = [{"form": "20-F", "reportDate": "2024-12-31"}, {"form": "20-F", "reportDate": "2025-12-31"}]
        years = calendar.fiscal_calendar(f, "1231", "2026-10-07")
        y = [x for x in years if x["fy_end"] == dt.date(2025, 12, 31)][0]
        self.assertEqual(y["q_ends"], [dt.date(2025, 3, 31), dt.date(2025, 6, 30), dt.date(2025, 9, 30),
                                       dt.date(2025, 12, 31)])
        self.assertEqual(y["quarters_source"], "synthetic")

    def test_june_year_end(self):
        self.assertEqual(calendar._three_month_ends(dt.date(2024, 7, 1)),
                         [dt.date(2024, 9, 30), dt.date(2024, 12, 31), dt.date(2025, 3, 31)])
        self.assertEqual(calendar._year_before(dt.date(2025, 6, 30)), dt.date(2024, 7, 1))

    def test_transition_period_is_its_own_length(self):
        # D-0053, point 5 : six mois de transition, deux trimestres, jamais douze mois
        f = [{"form": "10-Q", "reportDate": "2023-09-30"}, {"form": "10-KT", "reportDate": "2023-12-31"},
             {"form": "10-Q", "reportDate": "2024-03-31"}, {"form": "10-K", "reportDate": "2024-12-31"}]
        tp = {"start": "2023-07-01", "end": "2023-12-31"}
        years = calendar.apply_transition(calendar.fiscal_calendar(f, "1231", "2026-10-07"), tp)
        t = [x for x in years if x["fy_end"] == dt.date(2023, 12, 31)][0]
        self.assertEqual(t["fy_start"], dt.date(2023, 7, 1))
        self.assertEqual(t["q_ends"], [dt.date(2023, 9, 30), dt.date(2023, 12, 31)])
        self.assertTrue(t["transition"])
        qs = [q for q in calendar.quarters(years) if q["fy_end"] == dt.date(2023, 12, 31)]
        self.assertEqual([(q["start"], q["end"]) for q in qs],
                         [(dt.date(2023, 7, 1), dt.date(2023, 9, 30)), (dt.date(2023, 10, 1), dt.date(2023, 12, 31))])
        nxt = [x for x in years if x["fy_end"] == dt.date(2024, 12, 31)][0]
        self.assertEqual(nxt["fy_start"], dt.date(2024, 1, 1))

    def test_transition_without_quarterly_report(self):
        f = [{"form": "10-KT", "reportDate": "2023-12-31"}]
        years = calendar.apply_transition(calendar.fiscal_calendar(f, "1231", "2026-10-07"),
                                          {"start": "2023-07-01", "end": "2023-12-31"})
        self.assertEqual(years[0]["q_ends"], [dt.date(2023, 9, 30), dt.date(2023, 12, 31)])
        self.assertEqual(years[0]["quarters_source"], "synthetic")

    def test_first_year_of_a_new_registrant(self):
        # D-0054, point 11 : un seul 10-Q dans l'exercice d'introduction ; trimestres de trois mois
        f = [{"form": "10-Q", "reportDate": "2021-09-30"}, {"form": "10-K", "reportDate": "2021-12-31"},
             {"form": "10-Q", "reportDate": "2022-03-31"}, {"form": "10-K", "reportDate": "2022-12-31"}]
        years = calendar.fiscal_calendar(f, "1231", "2026-10-07")
        years[0]["fy_start"] = dt.date(2021, 1, 1)
        years = calendar.fill_first_year(years, {"fy_end": "2021-12-31"})
        y = years[0]
        self.assertEqual(y["q_ends"], [dt.date(2021, 3, 31), dt.date(2021, 6, 30), dt.date(2021, 9, 30),
                                       dt.date(2021, 12, 31)])
        self.assertEqual(y["synthetic_q_ends"], [dt.date(2021, 3, 31), dt.date(2021, 6, 30)])
        qs = [q for q in calendar.quarters(years) if q["fy_end"] == dt.date(2021, 12, 31)]
        self.assertEqual(qs[2]["start"], dt.date(2021, 7, 1))     # le trimestre déposé garde trois mois


class Breaks(unittest.TestCase):
    def test_history_break_like_reverse_combination(self):
        cfg = {"reverse_combinations": {"WULF": {"consummation": "2021-12-13", "accounting_acquirer": "TeraCub"}},
               "history_breaks": {"NBIS": {"effective": "2024-07-12", "kind": "divestiture"}}}
        b = phase0.breaks(cfg)
        self.assertEqual(b["WULF"]["kind"], "reverse_combination")
        self.assertEqual(b["NBIS"]["consummation"], "2024-07-12")
        old = {"form": "20-F", "reportDate": "2023-12-31", "filingDate": "2024-03-01", "accessionNumber": "a",
               "is_predecessor": False}
        new = {"form": "20-F", "reportDate": "2024-12-31", "filingDate": "2025-04-30", "accessionNumber": "b",
               "is_predecessor": False}
        self.assertTrue(phase0.pre_combination(old, b["NBIS"]))
        self.assertFalse(phase0.pre_combination(new, b["NBIS"]))


class Regime6K(unittest.TestCase):
    """Signaux tirés des items de 8-K, trimestre sans 8-K mais avec des 6-K (D-0048)."""

    def setUp(self):
        d = dt.date
        self.q = {"G": [{"start": d(2025, 1, 1), "end": d(2025, 3, 31)}, {"start": d(2025, 7, 1), "end": d(2025, 9, 30)}]}
        self.filings = pd.DataFrame([
            {"group_id": "G", "form": "6-K", "accessionNumber": "s1", "filingDate": d(2025, 3, 20), "items": None},
            {"group_id": "G", "form": "8-K", "accessionNumber": "e1", "filingDate": d(2025, 8, 1), "items": "7.01"}])

    def cells(self, obs=()):
        out = events.structural_signals(["G"], self.q, self.filings, "2026-10-07", {}, obs)
        return {(c["measure"], c["period_end"]): c for c in out}

    def test_absence_not_established_under_6k(self):
        c = self.cells()
        for m in ("sig_distress_8k_items", "sig_auditor_change_or_nonreliance"):
            self.assertEqual(c[(m, "2025-03-31")]["status"], "not_determinable")
            self.assertEqual(c[(m, "2025-03-31")]["nd_reason"], "not_collected")
            self.assertEqual(c[(m, "2025-09-30")]["value_text"], "no_event")

    def test_observed_nonreliance_is_an_event(self):
        o = {"group_id": "G", "signal": "nonreliance", "signal_present": True, "event_date": "2025-03-20",
             "knowledge_date": "2025-03-20", "accession": "s1", "obs_key": "k/p/0"}
        c = self.cells([o])[("sig_auditor_change_or_nonreliance", "2025-03-31")]
        self.assertEqual((c["status"], c["value_text"], c["knowledge_date"]), ("computed", "event", "2025-03-20"))


class CustomerConsideration(unittest.TestCase):
    def test_capitalized_supplier_rights_are_not_customer_consideration(self):
        # IREN : droits remis à NVIDIA, capitalisés dans le coût des GPU (lien L3, pas E.5)
        self.assertFalse(annex_e.customer_consideration(
            {"link_category": "L3", "family": "commercial", "edge_type": "purchase", "amount_nature": "purchase_capitalized"}))
        self.assertTrue(annex_e.customer_consideration(
            {"link_category": "L3", "family": "customer_consideration", "edge_type": "equity_or_warrants_to_customer",
             "amount_nature": "consideration_payable_to_customer"}))


if __name__ == "__main__":
    unittest.main()
