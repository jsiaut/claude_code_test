"""D-0075 : en-cours publiés comme membre de l'axe des classes d'immobilisations, dénominateur du même poste, durée
implicite sans les en-cours, variation des en-cours ÷ capex et intérêts capitalisés ÷ en-cours moyen.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import json
import unittest
from decimal import Decimal

import duckdb
import pandas as pd

from pipeline import quantities, rank2
from pipeline.measures import Series

D = dt.date.fromisoformat
AS_OF = "2026-10-24"
AXIS = "us-gaap:PropertyPlantAndEquipmentByTypeAxis"
GROSS = "us-gaap:PropertyPlantAndEquipmentGross"
ROU = quantities.PPE_ROU_GROSS
CIP = "us-gaap:ConstructionInProgressGross"
CFG = {"cip_dimensional": {"axis": AXIS, "members": ["us-gaap:ConstructionInProgressMember", "nbis:AssetsNotInUseMember"],
                           "lines": [GROSS, ROU]}}


def dims(*pairs):
    return json.dumps([list(p) for p in pairs], separators=(",", ":"))


class Admission(unittest.TestCase):
    """Les faits admis par la règle : liste fermée de membres et de postes, linkbase, en-cours sans dimension prioritaire."""

    def setUp(self):
        self.con = con = duckdb.connect()
        con.execute("""CREATE TABLE facts (fact_key VARCHAR, source VARCHAR, accession VARCHAR, group_id VARCHAR,
                       concept VARCHAR, dims VARCHAR, n_dims INTEGER, period_type VARCHAR, period_end DATE,
                       reporting_scope VARCHAR, value DOUBLE, is_nil BOOLEAN)""")
        con.execute("""CREATE TABLE pres (accession VARCHAR, group_id VARCHAR, child VARCHAR, parent VARCHAR,
                       statement_kind VARCHAR)""")
        con.execute("""CREATE TABLE concept_map (group_id VARCHAR, quantity VARCHAR, accession VARCHAR, concept VARCHAR,
                       rule VARCHAR, statement_kind VARCHAR)""")
        cip = dims((AXIS, "us-gaap:ConstructionInProgressMember"))
        rows = [
            ("ok", "a1", GROSS, cip, 1),                                                  # admis
            ("nbis", "a1", ROU, dims((AXIS, "nbis:AssetsNotInUseMember")), 1),            # membre propre, second poste
            ("deposit", "a1", GROSS, dims((AXIS, "wulf:DepositsonminersMember")), 1),     # acomptes : hors liste
            ("net", "a1", "us-gaap:PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization",
             cip, 1),                                                                     # poste net : hors liste
            ("two_dims", "a1", GROSS, dims((AXIS, "us-gaap:ConstructionInProgressMember"),
                                           ("us-gaap:StatementBusinessSegmentsAxis", "x:CloudMember")), 2),
            ("nondim_wins", "a2", GROSS, cip, 1),                                         # le dépôt balise CIP sans dimension
            ("no_pres", "a3", GROSS, cip, 1),                                             # poste absent de la linkbase
        ]
        for k, acc, concept, d, n in rows:
            con.execute("INSERT INTO facts VALUES (?, 'instance', ?, 'G', ?, ?, ?, 'instant', DATE '2026-06-30', "
                        "'as_reported', 100, false)", [k, acc, concept, d, n])
        con.execute("INSERT INTO facts VALUES ('a2_cip', 'instance', 'a2', 'G', ?, '[]', 0, 'instant', DATE '2026-06-30', "
                    "'as_reported', 100, false)", [CIP])
        for acc in ("a1", "a2"):
            for concept in (GROSS, ROU):
                con.execute("INSERT INTO pres VALUES (?, 'G', ?, 'x:Table', 'note_details')", [acc, concept])
        con.execute("INSERT INTO pres VALUES ('a3', 'G', ?, 'x:Table', 'income_statement')", [GROSS])
        con.execute("INSERT INTO concept_map VALUES ('G', 'construction_in_progress', 'a2', ?, 'definition_first_present', "
                    "'note_details')", [CIP])

    def test_closed_lists(self):
        self.assertEqual(quantities.cip_dimensional(self.con, CFG), 2)
        got = {r[0] for r in self.con.execute("SELECT fact_key FROM cip_dim").fetchall()}
        self.assertEqual(got, {"ok", "nbis"})

    def test_no_list_no_fact(self):
        self.assertEqual(quantities.cip_dimensional(self.con, {"cip_dimensional": {}}), 0)

    def test_table_total_is_an_instant_quantity(self):
        q = quantities.quantity_definitions()["ppe_and_finance_rou_gross"]
        self.assertEqual((q["candidates"], q["instant"]), ([ROU], True))


def quarters(*fys):
    out = []
    for y in fys:
        for s, e in (("01-01", "03-31"), ("04-01", "06-30"), ("07-01", "09-30"), ("10-01", "12-31")):
            out.append({"start": D(f"{y}-{s}"), "end": D(f"{y}-{e}"), "fy_end": D(f"{y}-12-31")})
    return out


def series(rows, fys=(2025, 2026)):
    """Occurrences au format de model.occurrences_df : (grandeur, concept, début, fin, valeur, accession, date)."""
    recs = []
    for i, (qn, concept, s, e, v, acc, filed) in enumerate(rows):
        recs.append({"group_id": "G", "quantity": qn, "concept": concept,
                     "period_type": "instant" if s is None else "duration",
                     "period_start": D(s) if s else None, "period_end": D(e), "value": float(v),
                     "fact_key": f"f{i}", "accession": acc, "knowledge_date": D(filed), "tier": "A",
                     "decimals": -6, "decimals_inf": False, "precision_known": True, "is_tagged": True,
                     "order_key": (filed, acc, 1, -6, 0)})
    return Series(pd.DataFrame(recs), "G", {"quarters": quarters(*fys)})


class CipShare(unittest.TestCase):
    """Dénominateur : le total du poste qui porte l'en-cours, à défaut celui du tableau (D-0075)."""

    def share(self, rows):
        return rank2.cip_share_cell(series(rows), "G", D("2026-06-30"), D(AS_OF), "as_known", AS_OF)

    def test_same_line_total(self):
        c = self.share([("construction_in_progress", GROSS, None, "2026-06-30", 11918, "q2", "2026-08-10"),
                        ("gross_depreciable_ppe", GROSS, None, "2026-06-30", 40000, "q2", "2026-08-10"),
                        ("ppe_and_finance_rou_gross", ROU, None, "2026-06-30", 42000, "q2", "2026-08-10")])
        self.assertEqual((c["status"], c["denominator"]), ("computed", Decimal("40000")))
        self.assertEqual(json.loads(c["flags"])["denominator"], "gross_depreciable_ppe")

    def test_table_total_when_the_line_has_none(self):
        # Meta : classes sur le brut, total du tableau sur le poste qui comprend les droits d'utilisation
        c = self.share([("construction_in_progress", GROSS, None, "2026-06-30", 80345, "q2", "2026-07-30"),
                        ("ppe_and_finance_rou_gross", ROU, None, "2026-06-30", 300000, "q2", "2026-07-30")])
        self.assertEqual((c["status"], c["denominator"]), ("computed", Decimal("300000")))
        self.assertEqual(json.loads(c["flags"]), {"cip_line": GROSS, "denominator": "ppe_and_finance_rou_gross"})

    def test_rou_line_takes_its_own_total(self):
        c = self.share([("construction_in_progress", ROU, None, "2026-06-30", 11424, "k", "2026-10-09"),
                        ("gross_depreciable_ppe", GROSS, None, "2026-06-30", 120000, "k", "2026-10-09"),
                        ("ppe_and_finance_rou_gross", ROU, None, "2026-06-30", 134176, "k", "2026-10-09")])
        self.assertEqual(c["denominator"], Decimal("134176"))

    def test_untagged_cip_unchanged(self):
        c = self.share([("construction_in_progress", CIP, None, "2026-06-30", 48546, "q", "2026-09-10"),
                        ("gross_depreciable_ppe", GROSS, None, "2026-06-30", 153596, "q", "2026-09-10")])
        self.assertEqual((c["denominator"], c["flags"]), (Decimal("153596"), None))

    def test_missing_total_reason_is_the_line(self):
        c = self.share([("construction_in_progress", GROSS, None, "2026-06-30", 100, "q2", "2026-08-10"),
                        ("gross_depreciable_ppe", GROSS, None, "2025-12-31", 900, "k", "2026-02-10")])
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "not_disclosed"))


class CipFlows(unittest.TestCase):
    """Variation des en-cours ÷ capex décaissé ; intérêts capitalisés ÷ en-cours moyen, trimestre non annualisé."""

    def flows(self, rows, end="2026-06-30"):
        S = series(rows)
        q = next(x for x in S.quarters if x["end"] == D(end))
        capex, t_capex, r_capex = S.quarter("capex_cash", q, D(AS_OF))
        return {c["measure"]: c for c in rank2.cip_flows(S, "G", q, D(AS_OF), "as_known", AS_OF, capex, t_capex, r_capex)}

    def test_values(self):
        c = self.flows([("construction_in_progress", GROSS, None, "2026-03-31", 9581, "q1", "2026-05-10"),
                        ("construction_in_progress", GROSS, None, "2026-06-30", 11918, "q2", "2026-08-10"),
                        ("capex_cash", "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment", "2026-04-01", "2026-06-30",
                         4674, "q2", "2026-08-10"),
                        ("capitalized_interest", "us-gaap:InterestCostsCapitalized", "2026-04-01", "2026-06-30",
                         107, "q2", "2026-08-10")])
        ch, ci = c["cip_change_to_capex"], c["capitalized_interest_to_cip"]
        self.assertEqual((ch["numerator"], ch["denominator"], ch["value"]),
                         (Decimal("2337"), Decimal("4674"), Decimal("0.5")))
        self.assertEqual((ci["numerator"], ci["denominator"]), (Decimal("107"), Decimal("10749.5")))
        self.assertIsNone(ch["flags"])

    def test_placed_in_service_gives_a_negative_share(self):
        c = self.flows([("construction_in_progress", GROSS, None, "2026-03-31", 500, "q1", "2026-05-10"),
                        ("construction_in_progress", GROSS, None, "2026-06-30", 400, "q2", "2026-08-10"),
                        ("capex_cash", "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment", "2026-04-01", "2026-06-30",
                         200, "q2", "2026-08-10")])
        self.assertEqual(c["cip_change_to_capex"]["value"], Decimal("-0.5"))

    def test_prior_quarter_missing(self):
        c = self.flows([("construction_in_progress", GROSS, None, "2026-06-30", 400, "q2", "2026-08-10")])
        self.assertEqual({m: x["nd_reason"] for m, x in c.items()},
                         {"cip_change_to_capex": "prior_period_missing", "capitalized_interest_to_cip": "prior_period_missing"})

    def test_line_change_is_flagged(self):
        c = self.flows([("construction_in_progress", GROSS, None, "2026-03-31", 500, "q1", "2026-05-10"),
                        ("construction_in_progress", ROU, None, "2026-06-30", 600, "q2", "2026-08-10"),
                        ("capex_cash", "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment", "2026-04-01", "2026-06-30",
                         200, "q2", "2026-08-10")])
        self.assertEqual(json.loads(c["cip_change_to_capex"]["flags"]), {"cip_lines": sorted([GROSS, ROU])})


class ImpliedLife(unittest.TestCase):
    """CoreWeave, exercice 2025 : la base amortissable perd ses en-cours publiés sous dimension (6,98 ans, et non 9,54)."""

    def test_dimensional_cip_leaves_the_base(self):
        rows = [("gross_depreciable_ppe", GROSS, None, "2024-12-31", 12880, "k24", "2025-03-01"),
                ("gross_depreciable_ppe", GROSS, None, "2025-12-31", 33941, "k25", "2026-03-01"),
                ("construction_in_progress", GROSS, None, "2024-12-31", 3201, "k24", "2025-03-01"),
                ("construction_in_progress", GROSS, None, "2025-12-31", 9376, "k25", "2026-03-01"),
                ("depreciation_expense", "us-gaap:DepreciationDepletionAndAmortization", "2025-01-01", "2025-12-31",
                 2454, "k25", "2026-03-01")]
        S = series(rows, fys=(2024, 2025))
        out = rank2.annual_rank2(S, "G", D("2025-01-01"), D("2025-12-31"), D(AS_OF), "as_known", AS_OF)
        c = next(x for x in out if x["measure"] == "implied_useful_life")
        self.assertEqual(round(c["value"], 2), Decimal("6.98"))


if __name__ == "__main__":
    unittest.main()
