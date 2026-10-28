"""D-0080 : composantes d'un total d'état (C1, C2) et ventilations d'un même tableau (C12).

Lancement : python3 -m unittest tests.test_d0080 -v
"""
import datetime as dt
import json
import unittest
from collections import namedtuple

import duckdb
import pandas as pd

from pipeline import controls as K
from pipeline import controls_more as KM

D = dt.date(2018, 5, 31)
US = "us-gaap:"


def filing(pres, calc, facts, crdr=None):
    """Un dépôt minimal : présentation (rôle, parent, enfant, ordre), calcul (rôle, parent, enfant, poids) et faits
    instantanés non dimensionnés au 2018-05-31."""
    p = pd.DataFrame([{"role": r, "statement_kind": k, "parent": a, "child": b, "ord": float(o)} for r, k, a, b, o in pres])
    c = pd.DataFrame([{"role": r, "parent": a, "child": b, "weight": w} for r, a, b, w in calc],
                     columns=["role", "parent", "child", "weight"])
    f = pd.DataFrame([{"fact_key": f"k{i}", "concept": k, "period_type": "instant", "period_start": None, "period_end": D,
                       "n_dims": 0, "value": v, "decimals": 0, "decimals_inf": False, "conflict": False}
                      for i, (k, v) in enumerate(facts.items())])
    return K.Filing("acc", f, p, c, crdr or {})


def check(F, total, kinds, statement, family=False):
    out = []
    for role, comps, w in F.siblings(total, kinds, statement=statement):
        if family:
            comps, w = [x for x in comps if K._same_family(x, total)], {}
        out.append(K.sum_check("c", F, "G", total, comps, w, "instant", None, D, "as_known", "2026-10-27", "10-K"))
    return [(r["status"], r["explanation_code"]) for r in out if r]


class StatementComponents(unittest.TestCase):
    def test_enfants_de_calcul_seuls_des_qu_un_arc_existe(self):
        # Oracle : les capitaux propres y compris minoritaires = capitaux propres + minoritaires ; le passif courant,
        # le passif non courant et les engagements sont des voisines, composantes du total du passif et des capitaux
        R, BS, A = "r", "balance_sheet", US + "LiabilitiesAndStockholdersEquityAbstract"
        lines = ["LiabilitiesCurrent", "LiabilitiesNoncurrent", "CommitmentsAndContingencies", "StockholdersEquity",
                 "MinorityInterest", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
                 "LiabilitiesAndStockholdersEquity"]
        pres = [(R, BS, A, US + c, i) for i, c in enumerate(lines)]
        tot, lse = US + lines[5], US + lines[6]
        calc = [(R, tot, US + "StockholdersEquity", 1.0), (R, tot, US + "MinorityInterest", 1.0)] + \
               [(R, lse, US + c, 1.0) for c in lines[:3]] + [(R, lse, tot, 1.0)]
        F = filing(pres, calc, {US + "LiabilitiesCurrent": 50, US + "LiabilitiesNoncurrent": 80, US + "StockholdersEquity": 45,
                                US + "MinorityInterest": 1, tot: 46, lse: 176},
                   {US + c: "credit" for c in lines})
        self.assertEqual(check(F, tot, {BS}, statement=False), [("mismatch", "components_missing")])
        self.assertEqual(check(F, tot, {BS}, statement=True), [("ok", None)])

    def test_sans_arc_jamais_une_voisine_du_total(self):
        R, BS, A = "r", "balance_sheet", US + "Abstract1"
        pres = [(R, BS, A, US + "Peer", 0), (R, BS, A, US + "X", 1), (R, BS, A, US + "Y", 2), (R, BS, A, US + "T", 3)]
        calc = [(R, US + "Parent", US + "Peer", 1.0), (R, US + "Parent", US + "T", 1.0)]
        F = filing(pres, calc, {US + "Peer": 100, US + "X": 10, US + "Y": 5, US + "T": 15})
        self.assertEqual(check(F, US + "T", {BS}, statement=False), [("mismatch", "sum_differs")])
        self.assertEqual(check(F, US + "T", {BS}, statement=True), [("ok", None)])

    def test_echeancier_de_c10_inchange(self):
        # AMD : le calcul de la note décompose le total des paiements en passif plus intérêts implicites ; les
        # tranches annuelles sont dans un second réseau. C10 garde les tranches, lues dans la présentation.
        R, N, A = "r", "note_details", US + "CommitmentsAndContingenciesDisclosureAbstract"
        tot = US + "LesseeOperatingLeaseLiabilityPaymentsDue"
        tranches = [tot + s for s in ("NextTwelveMonths", "YearTwo", "AfterYearTwo")]
        pres = [(R, N, A, c, i) for i, c in enumerate(tranches + [tot])]
        calc = [(R, tot, US + "OperatingLeaseLiability", 1.0), (R, tot, US + "LesseeOperatingLeaseLiabilityUndiscountedExcessAmount", 1.0)]
        F = filing(pres, calc, {tranches[0]: 100, tranches[1]: 80, tranches[2]: 104, tot: 284, US + "OperatingLeaseLiability": 250,
                                US + "LesseeOperatingLeaseLiabilityUndiscountedExcessAmount": 34})
        self.assertEqual(check(F, tot, {N}, statement=False, family=True), [("ok", None)])
        # la règle des états, appliquée ici, ne laisserait aucune tranche
        self.assertEqual(check(F, tot, {N}, statement=True, family=True), [("not_testable", None)])


Fact = namedtuple("Fact", "value decimals decimals_inf")


def facts(*vals):
    return [Fact(v, 0, False) for v in vals]


class Ventilations(unittest.TestCase):
    def test_deux_ventilations_completes(self):
        # Backblaze : B2 + Computer Backup, et Consumption + Subscription + Physical Media
        vs = KM.ventilations(facts(60, 40, 50, 30, 20), Fact(100, 0, False))
        self.assertIn((0, 1), vs)
        self.assertIn((2, 3, 4), vs)
        self.assertEqual({i for v in vs for i in v}, {0, 1, 2, 3, 4})

    def test_membre_qui_recoupe(self):
        # Meta : « US » à côté de « US & Canada »
        vs = KM.ventilations(facts(78866, 46569, 53817, 21714, 74780), Fact(200966, 0, False))
        self.assertEqual(vs, [(0, 1, 2, 3)])

    def test_tableau_partiel_sans_ventilation(self):
        # Oracle : Software et Cloud avec leurs parties, dans un tableau qui ne couvre pas tout le revenu
        self.assertEqual(KM.ventilations(facts(655, 4895, 5550, 4219, 7388, 11607), Fact(19345, 0, False)), [])

    def test_un_membre_seul_ne_fait_pas_une_ventilation(self):
        self.assertEqual(KM.ventilations(facts(100, 30, 70), Fact(100, 0, False)), [(1, 2)])

    def test_tolerance_d_arrondi(self):
        self.assertEqual(KM.ventilations([Fact(60.4, 0, False), Fact(39.4, 0, False)], Fact(100, 0, False)), [(0, 1)])
        self.assertEqual(KM.ventilations([Fact(60.4, 0, False), Fact(38.0, 0, False)], Fact(100, 0, False)), [])


class C12Statuses(unittest.TestCase):
    """Le contrôle de bout en bout, sur une base en mémoire : ok si chaque membre est dans une ventilation,
    not_testable si un membre reste hors de toutes, sum_exceeds_total sinon."""

    def run_c12(self, members, total):
        con = duckdb.connect()
        con.execute("""CREATE TABLE facts (fact_key VARCHAR, group_id VARCHAR, accession VARCHAR, form VARCHAR, concept VARCHAR,
                       period_type VARCHAR, period_start DATE, period_end DATE, dims VARCHAR, n_dims INTEGER, value DOUBLE,
                       decimals INTEGER, decimals_inf BOOLEAN, knowledge_date DATE, source VARCHAR, conflict BOOLEAN, unit VARCHAR)""")
        con.execute("CREATE TABLE concept_map (accession VARCHAR, group_id VARCHAR, concept VARCHAR, quantity VARCHAR)")
        con.execute("CREATE TABLE pres (accession VARCHAR, role VARCHAR, parent VARCHAR, child VARCHAR, ord DOUBLE)")
        rev, axis, dom = US + "Revenues", "srt:ProductOrServiceAxis", "srt:ProductsAndServicesDomain"
        con.execute("INSERT INTO concept_map VALUES ('a', 'G', ?, 'revenue_total')", [rev])
        rows = [("t", None, total)] + [(f"m{i}", m, v) for i, (m, v) in enumerate(members)]
        for k, m, v in rows:
            dims = json.dumps([[axis, m]]) if m else "[]"
            con.execute("INSERT INTO facts VALUES (?, 'G', 'a', '10-K', ?, 'duration', '2022-01-01', '2022-12-31', ?, ?, ?, 0, false,"
                        " '2023-02-01', 'instance', false, 'USD')", [k, rev, dims, 1 if m else 0, v])
        con.execute("INSERT INTO pres VALUES ('a', 'r/Disagg', ?, ?, 1)", [axis, dom])
        for i, (m, _) in enumerate(members):
            con.execute("INSERT INTO pres VALUES ('a', 'r/Disagg', ?, ?, ?)", [dom, m, float(i)])
        out = [r for r in KM.segments_and_disaggregation(con, "2026-10-27") if r["control"] == "c12_revenue_disaggregation"]
        return [(r["status"], r["explanation_code"], json.loads(r["evidence"]).get("outside")) for r in out]

    def test_statuts(self):
        self.assertEqual(self.run_c12([("x:B2", 60), ("x:CB", 40), ("x:Cons", 50), ("x:Sub", 30), ("x:Phys", 20)], 100),
                         [("ok", None, None)])
        self.assertEqual(self.run_c12([("x:USC", 78866), ("x:EU", 46569), ("x:AP", 53817), ("x:RW", 21714), ("x:US", 74780)], 200966),
                         [("not_testable", None, ["x:US"])])
        self.assertEqual(self.run_c12([("x:Lic", 655), ("x:Sup", 4895), ("x:Soft", 5550), ("x:App", 4219), ("x:Inf", 7388),
                                       ("x:Cloud", 11607)], 19345), [("mismatch", "sum_exceeds_total", None)])
        self.assertEqual(self.run_c12([("x:A", 60), ("x:B", 40)], 100), [("ok", None, None)])


if __name__ == "__main__":
    unittest.main()
