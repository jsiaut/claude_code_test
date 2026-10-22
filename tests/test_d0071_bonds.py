"""D-0071, volet B : obligations d'Oracle, de CoreWeave et de Beignet dans les Form N-PORT Data Sets, même mesure
que celles de SoftBank (nport_price_to_par).

Lancement : python3 -m unittest discover -s tests -t .
"""
import json
import tempfile
import unittest
import zipfile
from decimal import Decimal
from pathlib import Path

import pandas as pd

from pipeline import nport as P

ISS = [{"node": "ORCL", "names": ["oracle corp"], "title": "ORACLE"},
       {"node": "CRWV", "names": ["coreweave"], "title": "COREWEAVE"},
       {"node": "CP:beignet investor llc", "names": ["beignet investor"], "title": "BEIGNET"}]
C = {"tables": {"holding": "FUND_REPORTED_HOLDING", "identifiers": "IDENTIFIERS", "debt": "DEBT_SECURITY",
                "submission": "SUBMISSION", "registrant": "REGISTRANT", "fund": "FUND_REPORTED_INFO"},
     "holding": {"accession": "ACCESSION_NUMBER", "holding_id": "HOLDING_ID", "issuer_name": "ISSUER_NAME",
                 "issuer_lei": "ISSUER_LEI", "asset_cat": "ASSET_CAT"},
     "identifiers": {"holding_id": "HOLDING_ID"}, "debt": {"holding_id": "HOLDING_ID"},
     "submission": {"accession": "ACCESSION_NUMBER"}, "registrant": {"accession": "ACCESSION_NUMBER"},
     "fund": {"accession": "ACCESSION_NUMBER"}}


def tsv(rows):
    return "\n".join("\t".join(r) for r in rows) + "\n"


class Names(unittest.TestCase):
    def test_a_name_begins_with_a_configured_name_and_stops_at_a_word_end(self):
        node = P.bond_namer(ISS)
        self.assertEqual(node("ORACLE CORP"), "ORCL")
        self.assertEqual(node("Oracle Corporation"), "ORCL")
        self.assertEqual(node("ORACLE CORP/DE"), "ORCL")
        self.assertIsNone(node("Oracle Corporate Holdings"))          # « corp » n'y est pas un mot
        self.assertIsNone(node("VANTAGE ORACLE TX"))                  # point 4 : écartés par la règle
        self.assertIsNone(node("ORACLE VISION HOLDCO"))
        self.assertIsNone(node("ORACLE"))                             # nom court : seulement par un LEI accepté
        self.assertEqual(node("CoreWeave Compute Acquisition Co. IV, LLC"), "CRWV")   # filiale qui porte le nom
        self.assertEqual(node("BEIGNET INVESTOR, LLC"), "CP:beignet investor llc")
        self.assertIsNone(node(None))
        self.assertIsNone(node(""))


class Scan(unittest.TestCase):
    def test_keeps_recognized_names_their_leis_and_counts_the_others(self):
        hold = [["ACCESSION_NUMBER", "HOLDING_ID", "ISSUER_NAME", "ISSUER_LEI", "ASSET_CAT"],
                ["A1", "1", "ORACLE CORP", "LEI-ORCL", "DBT"],
                ["A1", "2", "Oracle 2.95 2030", "LEI-ORCL", "DBT"],        # même LEI, nom court : second passage
                ["A1", "3", "VANTAGE ORACLE TX", "LEI-V", "DBT"],          # préfiltre, écarté et compté
                ["A2", "4", "CoreWeave Compute Acquisition Co. IV, LLC", "N/A", "DBT"],
                ["A2", "5", "Beignet Investor LLC", "LEI-B", "DBT"],
                ["A2", "6", "Microsoft Corp", "LEI-M", "DBT"],
                ["A3", "7", "ORACLE VISION HOLDCO", "LEI-OV", "EC"]]
        with tempfile.TemporaryDirectory() as d:
            zp = Path(d) / "2026q1_nport.zip"
            with zipfile.ZipFile(zp, "w") as z:
                z.writestr("FUND_REPORTED_HOLDING.tsv", tsv(hold))
                z.writestr("IDENTIFIERS.tsv", tsv([["HOLDING_ID", "IDENTIFIER_ISIN"], ["1", "US68389XCJ28"], ["6", "US5949"]]))
                z.writestr("DEBT_SECURITY.tsv", tsv([["HOLDING_ID", "MATURITY_DATE"], ["2", "2030-11-15"], ["7", "x"]]))
                z.writestr("SUBMISSION.tsv", tsv([["ACCESSION_NUMBER", "FILING_DATE"], ["A1", "2026-02-27"], ["A2", "x"], ["A3", "y"]]))
                z.writestr("REGISTRANT.tsv", tsv([["ACCESSION_NUMBER", "CIK"], ["A1", "1"], ["A3", "3"]]))
                z.writestr("FUND_REPORTED_INFO.tsv", tsv([["ACCESSION_NUMBER", "SERIES_ID"], ["A2", "S2"]]))
            out, stats, found, cnt = P.scan_bonds(zp, ISS, leis=(), c=C)
        self.assertEqual(sorted(out["holding"]["HOLDING_ID"]), ["1", "2", "4", "5"])
        self.assertEqual(found, ["LEI-B", "LEI-ORCL"])               # « N/A » n'est pas un LEI
        self.assertEqual(stats["by_name"], {"CP:beignet investor llc": 1, "CRWV": 1, "ORCL": 1})
        self.assertEqual(stats["by_lei_only"], 1)
        self.assertEqual(sorted(out["identifiers"]["HOLDING_ID"]), ["1"])
        self.assertEqual(sorted(out["debt"]["HOLDING_ID"]), ["2"])
        self.assertEqual(sorted(out["submission"]["ACCESSION_NUMBER"]), ["A1", "A2"])
        self.assertEqual(sorted(zip(cnt["issuer_name"], cnt["n"])), [("ORACLE VISION HOLDCO", 1), ("VANTAGE ORACLE TX", 1)])
        self.assertEqual(stats["other_names"], 2)


class Leis(unittest.TestCase):
    def test_a_lei_belongs_to_the_node_whose_name_most_of_its_positions_carry(self):
        names = ["ORACLE CORP", "Oracle Corp.", "ORACLE 4.3 2034",                 # L1 : Oracle, 2 sur 3
                 "CoreWeave, Inc.", "Core Scientific", "Core Scientific Inc",       # L2 : CoreWeave, 1 sur 3
                 "Beignet Investor LLC",                                            # L3 : Beignet, 1 sur 1
                 "ORACLE CORP", "CoreWeave Inc", "COREWEAVE INC",                   # L4 : CoreWeave, 2 sur 3
                 "ORACLE CORP"]
        leis = ["L1", "L1", "L1", "L2", "L2", "L2", "L3", "L4", "L4", "L4", "N/A"]
        ev = P.bond_lei_evidence(pd.DataFrame({"ISSUER_NAME": names, "ISSUER_LEI": leis}), ISS, c=C)
        self.assertEqual(ev["L1"], {"positions": 3, "named": {"ORCL": 2}})
        self.assertEqual(ev["L4"], {"positions": 3, "named": {"CRWV": 2, "ORCL": 1}})
        self.assertNotIn("N/A", ev)
        self.assertEqual(P.bond_accepted(ev), {"L1": "ORCL", "L3": "CP:beignet investor llc", "L4": "CRWV"})


BASE = {"unit": "PA", "asset_cat": "DBT", "payoff": "Long", "currency": "USD", "cusip": "000000000", "cik": None,
        "report_date": "2026-03-31", "filing_date": "2026-05-20", "coupon": "2.95", "maturity": "2030-11-15",
        "fair_value_level": "2", "IS_CONVTIBLE_MANDATORY": None, "IS_CONVTIBLE_CONTINGENT": None}


def pos(sec, name, node, title, series, value, balance="100", **kw):
    return dict(BASE, isin=sec, issuer_name=name, name_node=node, title=title, series_id=series,
                accession=f"{sec}-{series}", value_local=value, value_usd=value, balance=balance, **kw)


def positions():
    rows = [pos("US68389XCJ28", "ORACLE CORP", "ORCL", "Oracle Corp 2.95% 11/15/2030", f"S{i}", "80") for i in range(3)]
    rows += [pos("US123CERNER1", "Cerner Corp", None, "Cerner Corp 2.5%", f"S{i}", "99") for i in range(2)]   # LEI seul
    rows += [pos("US21873SAA01", "CoreWeave Compute Acquisition Co. IV, LLC", "CRWV",
                  "CoreWeave Compute Acquisition Co IV LLC 9.25% 2030", "S9", "101", coupon="9.25", maturity="2030-06-01",
                  fair_value_level="3")]
    rows += [pos("US999VANTAG1", "ORACLE CORP", "ORCL", "Vantage Data Centers Issuer 2031", "S8", "95")]   # intitulé
    rows += [pos("US68389XCJ28", "ORACLE CORP", "ORCL", "Oracle Corp 2.95% 11/15/2030", "S7", "80", payoff="Short")]
    rows += [pos("US68389X1054", "ORACLE CORP", "ORCL", "Oracle Corp", "S6", "150", unit="NS", asset_cat="EC")]
    rows += [pos("US07738AAA19", "Beignet Investor LLC", "CP:beignet investor llc", "BEIGNET INVESTOR LLC 6.581% 05/30/49",
                 f"B{i}", "104", coupon="6.581", maturity="2049-05-30", IS_CONVTIBLE_MANDATORY=None) for i in range(25)]
    return pd.DataFrame(rows)


class Selection(unittest.TestCase):
    def test_debt_in_principal_long_identified_and_issued_by_a_node(self):
        kept, steps = P.bond_selection(positions(), ISS)
        self.assertEqual(steps["not_debt_in_principal"], 1)
        self.assertEqual(steps["not_long"], 1)
        self.assertEqual(steps["securities_kept"], {"CP:beignet investor llc": ["US07738AAA19"], "CRWV": ["US21873SAA01"],
                                                    "ORCL": ["US68389XCJ28"]})
        self.assertEqual(steps["securities_out"], ["US123CERNER1", "US999VANTAG1"])
        self.assertEqual(steps["not_bond_issuer"], 3)
        self.assertEqual(set(kept.loc[kept["security"] == "US21873SAA01", "node"]), {"CRWV"})


class Cells(unittest.TestCase):
    def test_cells_by_node_with_capped_accessions_and_the_convertible_flag(self):
        p = positions()
        p.loc[p["isin"] == "US21873SAA01", "IS_CONVTIBLE_MANDATORY"] = "N"     # Item C.9.f rempli : convertible
        cs = {(c["subject"], c["breakdown_key"]): c for c in P.bond_cells("2026-10-07", ISS, p=p)}
        self.assertEqual(sorted(cs), [("CP:beignet investor llc", "US07738AAA19"), ("CRWV", "US21873SAA01"),
                                      ("ORCL", "US68389XCJ28")])
        o = cs[("ORCL", "US68389XCJ28")]
        self.assertEqual(Decimal(str(o["value"])), Decimal("0.8"))
        self.assertEqual(o["measure"], "nport_price_to_par")
        fl = json.loads(o["flags"])
        self.assertEqual((fl["n_series"], fl["perspective"], fl["convertible"]), (3, "counterparty", False))
        self.assertIn("D-0071", fl["basis"])
        b = json.loads(cs[("CP:beignet investor llc", "US07738AAA19")]["flags"])
        self.assertEqual((b["filings"], len(b["accessions"]), b["n_series"]), (25, 20, 25))
        self.assertTrue(json.loads(cs[("CRWV", "US21873SAA01")]["flags"])["convertible"])


class Render(unittest.TestCase):
    def test_bond_title_names_issuer_coupon_maturity_currency_and_conversion(self):
        from pipeline.render import bond_title
        fl = {"issuer": "ORACLE CORP", "coupon": "2.95", "maturity": "2030-11-15", "currency": "USD", "convertible": False}
        self.assertEqual(bond_title("US68389XCJ28", fl), "ORACLE CORP 2,95 %, échéance 2030-11-15 (USD, US68389XCJ28)")
        fl = dict(fl, issuer="COREWEAVE INC", coupon="1.75", maturity="2031-12-01", convertible=True)
        self.assertEqual(bond_title("US21873SAB83", fl),
                         "COREWEAVE INC 1,75 %, convertible, échéance 2031-12-01 (USD, US21873SAB83)")
        fl = dict(fl, issuer="ORACLE CORP", coupon=".04698559", maturity="2029-02-04", convertible=False)
        self.assertEqual(bond_title("US68389XDV47", fl),
                         "ORACLE CORP 4,699 % (déclaré en fraction), échéance 2029-02-04 (USD, US68389XDV47)")
        self.assertTrue(bond_title("X", dict(fl, coupon="0")).startswith("ORACLE CORP 0 %,"))


if __name__ == "__main__":
    unittest.main()
