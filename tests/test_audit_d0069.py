"""D-0069 : un test par défaut relevé par l'audit du 22 octobre 2026 — F1 à CFO négatif, variation du
nombre moyen dilué d'actions, dette du levier, clôtures du statut « financé », sauts d'un facteur 100,
date limite d'un 20-F.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import unittest
from decimal import Decimal

import duckdb
import pandas as pd

from pipeline import assemble, circularity, fsignals, load, rank2
from pipeline.measures import Series, cell, quarter_measures

D = dt.date.fromisoformat
AS_OF = "2026-10-07"


def quarters(*fys):
    """Trimestres civils des exercices donnés."""
    out = []
    for y in fys:
        for s, e in (("01-01", "03-31"), ("04-01", "06-30"), ("07-01", "09-30"), ("10-01", "12-31")):
            out.append({"start": D(f"{y}-{s}"), "end": D(f"{y}-{e}"), "fy_end": D(f"{y}-12-31")})
    return out


def occurrences(rows, group="G"):
    """Occurrences au format de model.occurrences_df : (grandeur, concept, début, fin, valeur, accession, date)."""
    recs = []
    for i, (qn, concept, s, e, v, acc, filed) in enumerate(rows):
        recs.append({"group_id": group, "quantity": qn, "concept": concept,
                     "period_type": "instant" if s is None else "duration",
                     "period_start": D(s) if s else None, "period_end": D(e), "value": float(v),
                     "fact_key": f"f{i}", "accession": acc, "knowledge_date": D(filed), "tier": "A",
                     "decimals": -6, "decimals_inf": False, "precision_known": True, "is_tagged": True,
                     "order_key": (filed, acc, 1, -6, 0)})
    return pd.DataFrame(recs)


def series(rows, fys):
    return Series(occurrences(rows), "G", {"quarters": quarters(*fys)})


class F1(unittest.TestCase):
    """Point 2 : capex supérieur au CFO deux trimestres de suite, CFO négatif compris."""

    def run_f1(self, pairs):
        qs = quarters(2024)[:len(pairs)]
        cells = []
        for q, (capex, cfo) in zip(qs, pairs):
            st = "computed" if cfo > 0 else "not_determinable"
            cells.append(cell("capex_to_cfo", "G", q["start"], q["end"], "as_known", AS_OF, term="without",
                              value=Decimal(capex) / Decimal(cfo) if cfo > 0 else None, numerator=Decimal(capex),
                              denominator=Decimal(cfo), status=st, nd_reason=None if cfo > 0 else "denominator_nonpositive",
                              terms=[{"value": Decimal(capex), "fact_key": f"c{q['end']}", "knowledge_date": str(q["end"])},
                                     {"value": Decimal(cfo), "fact_key": f"o{q['end']}", "knowledge_date": str(q["end"])}]))
        # un dépôt hors de la fenêtre : un groupe sans aucun dépôt ne se présente pas en production
        filings = pd.DataFrame([{"group_id": "G", "form": "10-Q", "filingDate": "2019-05-01", "reportDate": "2019-03-31",
                                 "accessionNumber": "acc-0", "items": "", "acceptanceDateTime": "2019-05-01T16:00:00.000Z",
                                 "primaryDocument": "q.htm", "is_predecessor": False},
                                {"group_id": "G", "form": "8-K", "filingDate": "2019-05-02", "reportDate": "2019-05-02",
                                 "accessionNumber": "acc-1", "items": "2.02", "acceptanceDateTime": "2019-05-02T16:00:00.000Z",
                                 "primaryDocument": "k.htm", "is_predecessor": False}])
        out = fsignals.fragility_events(["G"], {"G": qs}, pd.DataFrame(cells), [], {}, filings, set(), {}, AS_OF)
        return [(c["period_end"], c["status"], c["value_text"], c["nd_reason"])
                for c in out if c["breakdown_key"] == "F1"]

    def test_negative_cfo_two_quarters(self):
        f1 = self.run_f1([(2247, -118), (2453, -251)])
        self.assertEqual(f1[0][1:], ("not_determinable", None, "prior_period_missing"))
        self.assertEqual(f1[1][1:], ("computed", "event", None))

    def test_negative_then_positive_cfo_above_capex(self):
        f1 = self.run_f1([(100, -10), (100, 500), (100, 50)])
        self.assertEqual([x[2] for x in f1[1:]], ["no_event", "no_event"])

    def test_positive_cfo_below_capex(self):
        f1 = self.run_f1([(100, 50), (100, 60)])
        self.assertEqual(f1[1][2], "event")


class DilutedShares(unittest.TestCase):
    """Point 3 : deux faits directs de trois mois d'un même dépôt, jamais une différence de cumuls."""

    def cell_for(self, rows, q_end, cutoff):
        S = series(rows, (2020, 2021))
        q = next(x for x in S.quarters if x["end"] == D(q_end))
        out = rank2.quarter_rank2(S, "G", q, D(cutoff), "revised", AS_OF)
        return next(c for c in out if c["measure"] == "eq_diluted_share_count_change")

    def test_q4_without_direct_fact(self):
        # le 10-K ne donne que l'exercice ; le 10-Q du T3 donne neuf mois : aucune valeur de T4 n'est dérivée
        rows = [("diluted_shares_weighted", "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding", s, e, v, acc, f)
                for s, e, v, acc, f in (("2021-01-01", "2021-12-31", 1000, "k21", "2022-02-01"),
                                        ("2021-01-01", "2021-09-30", 990, "q321", "2021-11-01"),
                                        ("2020-01-01", "2020-12-31", 950, "k21", "2022-02-01"),
                                        ("2020-10-01", "2020-12-31", 960, "k20", "2021-02-01"))]
        c = self.cell_for(rows, "2021-12-31", AS_OF)
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "not_disclosed"))

    def test_stock_split_mixes_no_bases(self):
        # T2 2021 : 500 au 10-Q de 2021, 10 000 au 10-Q de 2022 après un fractionnement 20:1 ; T2 2020 : 480, au
        # 10-Q de 2021 seulement. La vue révisée prend les deux faits du même dépôt.
        rows = [("diluted_shares_weighted", "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding", s, e, v, acc, f)
                for s, e, v, acc, f in (("2021-04-01", "2021-06-30", 500, "q221", "2021-07-30"),
                                        ("2020-04-01", "2020-06-30", 480, "q221", "2021-07-30"),
                                        ("2021-04-01", "2021-06-30", 10000, "q222", "2022-07-29"))]
        c = self.cell_for(rows, "2021-06-30", AS_OF)
        self.assertEqual(c["status"], "computed")
        self.assertAlmostEqual(float(c["value"]), 20 / 480, places=6)

    def test_no_common_filing(self):
        rows = [("diluted_shares_weighted", "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding", s, e, v, acc, f)
                for s, e, v, acc, f in (("2021-04-01", "2021-06-30", 500, "q221", "2021-07-30"),
                                        ("2020-04-01", "2020-06-30", 480, "q220", "2020-07-30"))]
        c = self.cell_for(rows, "2021-06-30", AS_OF)
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "recast_boundary"))


class Debt(unittest.TestCase):
    """Point 4 : les emprunts à court terme ne s'ajoutent qu'à une dette qui les exclut."""

    def lev(self, current_concept, total_only=False):
        rows = []
        for q in quarters(2024):
            s, e = q["start"].isoformat(), q["end"].isoformat()
            rows += [("operating_income", "us-gaap:OperatingIncomeLoss", s, e, 1000, "q" + e, e),
                     ("depreciation_expense", "us-gaap:Depreciation", s, e, 1000, "q" + e, e)]
        if total_only:
            rows.append(("debt_carrying_amount", current_concept, None, "2024-12-31", 53029, "k24", "2025-02-01"))
        else:
            rows += [("debt_current", current_concept, None, "2024-12-31", 4695, "k24", "2025-02-01"),
                     ("debt_noncurrent", "us-gaap:LongTermDebtNoncurrent", None, "2024-12-31", 48334, "k24", "2025-02-01")]
        rows.append(("short_term_borrowings", "us-gaap:CommercialPaper", None, "2024-12-31", 3200, "k24", "2025-02-01"))
        S = series(rows, (2024,))
        out = quarter_measures(S, "G", S.quarters[-1], D(AS_OF), "revised", AS_OF)
        c = next(x for x in out if x["measure"] == "lev_debt_and_leases_to_operating_income_plus_da" and x["term"] == "debt")
        return c["numerator"]

    def test_debt_current_contains_commercial_paper(self):
        self.assertEqual(Decimal(self.lev("us-gaap:DebtCurrent")), Decimal(53029))

    def test_long_term_debt_current_gets_short_term_borrowings(self):
        self.assertEqual(Decimal(self.lev("us-gaap:LongTermDebtCurrent")), Decimal(56229))

    def test_combined_total_contains_short_term(self):
        self.assertEqual(Decimal(self.lev("us-gaap:DebtLongtermAndShorttermCombinedAmount", total_only=True)),
                         Decimal(53029))
        self.assertEqual(Decimal(self.lev("us-gaap:LongTermDebt", total_only=True)), Decimal(56229))


def edge(key, frm, to, d, kd, ik, edge_type="loan_or_facility", event_type=None, stage="drawn_or_paid", tier="A",
         nature="financing_cash"):
    o = {"obs_key": key, "event_type": event_type, "knowledge_date": kd, "amount_nature": nature, "group_id": frm}
    return {"link_key": "edge:" + key, "from_group": frm, "to_group": to, "family": "financing", "stage": stage,
            "tier": tier, "edge_type": edge_type, "instrument_key": ik, "_obs": o, "_date": D(d)}


class Closures(unittest.TestCase):
    """Point 5 : une clôture ne ferme que son instrument, dans l'un ou l'autre sens, une fois connue."""
    qs = quarters(2024)

    def status(self, edges, cut, others=()):
        p = circularity.Pair("S", "C")
        p.edges = edges
        closings = circularity.closing_index(list(edges) + list(others)) if others else None
        st = circularity.financed_status(p, self.qs, lambda q: D(cut), 8, False, closings)
        return st["exposure_outstanding"][D("2024-12-31")]

    def holdings(self):
        # deux instruments détenus par S dans C : un prêt (K1) et des titres (K2), constatés au T1 2022
        return [edge("h1", "S", "C", "2022-03-31", "2022-05-01", "s:k1", nature="investment_carrying_amount",
                     event_type="recognition", stage="recognized"),
                edge("h2", "S", "C", "2022-03-31", "2022-05-01", "s:k2", edge_type="equity_primary",
                     nature="investment_carrying_amount", event_type="recognition", stage="recognized")]

    def test_disposal_closes_its_instrument_only(self):
        # cession des titres K2 à C : la trésorerie va de C à S
        sale = edge("x2", "C", "S", "2024-06-30", "2024-08-01", "s:k2", edge_type="equity_primary",
                    event_type="disposal", stage="settled")
        st, keys = self.status(self.holdings() + [sale], "2025-02-01")
        self.assertEqual(st, "active")
        self.assertEqual(keys, ["edge:h1"])

    def test_closure_counts_once_known(self):
        rep = edge("x1", "C", "S", "2024-06-30", "2025-03-01", "s:k1", event_type="repayment", stage="settled")
        sale = edge("x2", "C", "S", "2024-06-30", "2024-08-01", "s:k2", edge_type="equity_primary",
                    event_type="disposal", stage="settled")
        st, keys = self.status(self.holdings() + [rep, sale], "2025-02-01")
        self.assertEqual((st, keys), ("active", ["edge:h1"]))       # le remboursement n'est pas encore connu
        st, keys = self.status(self.holdings() + [rep, sale], "2025-04-01")
        self.assertEqual(st, "lapsed")

    def test_signed_disposal_closes_nothing(self):
        sale = edge("x2", "C", "S", "2024-06-30", "2024-08-01", "s:k2", edge_type="equity_primary",
                    event_type="disposal", stage="signed")
        st, keys = self.status(self.holdings() + [sale], "2025-02-01")
        self.assertEqual(sorted(keys), ["edge:h1", "edge:h2"])

    def test_sale_to_a_third_party(self):
        # les titres K2 vendus à un tiers T : l'arête de la vente va de T à S, hors de la paire (S, C)
        sale = edge("x2", "T", "S", "2024-06-30", "2024-08-01", "s:k2", edge_type="equity_primary",
                    event_type="disposal", stage="settled")
        st, keys = self.status(self.holdings(), "2025-02-01", others=[sale])
        self.assertEqual(keys, ["edge:h1"])

    def test_unkeyed_holding_closed_by_same_edge_type(self):
        h = edge("h3", "S", "C", "2022-03-31", "2022-05-01", None, nature="investment_carrying_amount",
                 event_type="recognition", stage="recognized")
        rep = edge("x3", "S", "C", "2024-06-30", "2024-08-01", "s:abs", event_type="repayment", stage="settled")
        st, keys = self.status([h, rep], "2025-02-01")
        self.assertEqual(st, "lapsed")


class ScaleJumps(unittest.TestCase):
    """Point 6 : un saut confirmé par companyfacts n'est pas conflicting ; non confirmé, son doublon l'est aussi."""

    def facts(self, cf_value):
        con = duckdb.connect()
        con.execute("""CREATE TABLE facts (fact_key VARCHAR, source VARCHAR, accession VARCHAR, concept VARCHAR,
                       entity_id VARCHAR, group_id VARCHAR, period_type VARCHAR, period_start DATE, period_end DATE,
                       unit VARCHAR, dims VARCHAR, n_dims INTEGER, reporting_scope VARCHAR, value DECIMAL(38,6),
                       decimals INTEGER, decimals_inf BOOLEAN, knowledge_date DATE, conflict BOOLEAN)""")
        rows = [("i1", "instance", "a1", -8000000, -5, "2024-03-31", "2024-05-01"),
                ("i2", "instance", "a2", -1069000000, -5, "2024-06-30", "2024-08-01"),
                ("c1", "companyfacts", "a1", -8000000, None, "2024-03-31", "2024-05-01")]
        if cf_value is not None:
            rows.append(("c2", "companyfacts", "a2", cf_value, None, "2024-06-30", "2024-08-01"))
        for k, src, acc, v, dec, pe, kd in rows:
            ps = (D(pe) - dt.timedelta(days=90)).replace(day=1)
            con.execute("INSERT INTO facts VALUES (?, ?, ?, 'us-gaap:OperatingIncomeLoss', 'e', 'G', 'duration', ?, ?, "
                        "'USD', '[]', 0, 'consolidated', ?, ?, false, ?, false)", [k, src, acc, ps, D(pe), v, dec, D(kd)])
        load.mark_conflicts(con, 100)
        return {r[0] for r in con.execute("SELECT fact_key FROM facts WHERE conflict").fetchall()}

    def test_confirmed_jump(self):
        self.assertEqual(self.facts(-1069000000), set())

    def test_confirmed_within_rounding(self):
        self.assertEqual(self.facts(-1069040000), set())

    def test_unconfirmed_jump_marks_its_duplicate(self):
        self.assertEqual(self.facts(-1069), {"i2", "c2"})

    def test_jump_without_duplicate(self):
        self.assertEqual(self.facts(None), {"i2"})


class Deadline(unittest.TestCase):
    """Point 7 : quatre mois pour un 20-F, la catégorie pour un 10-K, selon le formulaire de l'exercice."""
    p0 = {"meta": {"1": {"group": "F", "is_predecessor": False, "category": "Large accelerated filer"}}}
    filings = pd.DataFrame({"group_id": ["F", "F", "F"], "form": ["20-F", "20-F", "10-K"],
                            "reportDate": ["2023-06-30", "2024-06-30", "2025-06-30"]})

    def test_20f_and_switch_to_10k(self):
        fn = assemble.deadline_fn(self.p0, ["F"], self.filings)["F"]
        self.assertEqual(fn(D("2024-06-30")), D("2024-10-31"))
        self.assertEqual(fn(D("2025-06-30")), D("2025-08-29"))
        self.assertEqual(fn(D("2026-06-30")), D("2026-08-29"))     # dernier formulaire antérieur : 10-K

    def test_month_end(self):
        self.assertEqual(assemble.plus_months(D("2025-12-31"), 4), D("2026-04-30"))
        self.assertEqual(assemble.plus_months(D("2024-10-27"), 4), D("2025-02-27"))


if __name__ == "__main__":
    unittest.main()
