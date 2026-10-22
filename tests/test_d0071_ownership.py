"""D-0071, volet A : déclarations de détention (13F, 13D, 13G), lues par leurs champs, et sorties qui ferment les
détentions en actions du statut « financé ».

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import unittest
from decimal import Decimal

from pipeline import circularity
from pipeline import ownership as O

D = dt.date.fromisoformat

HEADER = b"""<SEC-DOCUMENT>0001045810-25-000001.txt : 20250515
<SEC-HEADER>0001045810-25-000001.hdr.sgml : 20250515
ACCESSION NUMBER:\t\t0001045810-25-000001
CONFORMED SUBMISSION TYPE:\tSCHEDULE 13G
PUBLIC DOCUMENT COUNT:\t\t1
FILED AS OF DATE:\t\t20250515
SUBJECT COMPANY:\t

\tCOMPANY DATA:\t
\t\tCOMPANY CONFORMED NAME:\t\t\tCoreWeave, Inc.
\t\tCENTRAL INDEX KEY:\t\t\t0001769628

FILED BY:\t\t

\tCOMPANY DATA:\t
\t\tCOMPANY CONFORMED NAME:\t\t\tNVIDIA CORP
\t\tCENTRAL INDEX KEY:\t\t\t0001045810
</SEC-HEADER>
"""


def doc(type_, body, xml=True):
    inner = b"<XML>\n" + body + b"\n</XML>" if xml else body
    return b"<DOCUMENT>\n<TYPE>" + type_ + b"\n<SEQUENCE>1\n<FILENAME>x\n<TEXT>\n" + inner + b"\n</TEXT>\n</DOCUMENT>\n"


COVER = b"""<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/thirteenffiler">
 <headerData><submissionType>13F-HR</submissionType><filerInfo><periodOfReport>%s</periodOfReport></filerInfo></headerData>
 <formData><coverPage><reportCalendarOrQuarter>%s</reportCalendarOrQuarter><isAmendment>%s</isAmendment>%s
  <reportType>%s</reportType></coverPage>
  <summaryPage><tableEntryTotal>2</tableEntryTotal><isConfidentialOmitted>%s</isConfidentialOmitted></summaryPage>
  <signatureBlock><name>NE PAS LIRE</name></signatureBlock></formData>
</edgarSubmission>"""
TABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">%s</informationTable>"""
ROW = (b"<infoTable><nameOfIssuer>%s</nameOfIssuer><titleOfClass>COM CL A</titleOfClass><cusip>%s</cusip>"
       b"<value>%s</value><shrsOrPrnAmt><sshPrnamt>%s</sshPrnamt><sshPrnamtType>%s</sshPrnamtType></shrsOrPrnAmt>%s"
       b"</infoTable>")


def thirteen_f(period, rows, amendment=None, confidential=False, report=b"13F HOLDINGS REPORT"):
    amd = b"<amendmentInfo><amendmentType>" + amendment + b"</amendmentType></amendmentInfo>" if amendment else b""
    cover = COVER % (period, period, b"true" if amendment else b"false", amd, report, b"true" if confidential else b"false")
    table = TABLE % b"".join(ROW % (n, c, v, s, t, (b"<putCall>" + pc + b"</putCall>") if pc else b"")
                             for n, c, v, s, t, pc in rows)
    return HEADER.replace(b"SCHEDULE 13G", b"13F-HR") + doc(b"13F-HR", cover) + doc(b"INFORMATION TABLE", table)


class Header(unittest.TestCase):
    def test_subject_and_filer_ciks_without_names(self):
        h = O.header(HEADER)
        self.assertEqual((h["type"], h["filed"]), ("SCHEDULE 13G", "20250515"))
        self.assertEqual(h["subject"], ["0001769628"])
        self.assertEqual(h["filed_by"], ["0001045810"])
        self.assertNotIn("name", h)


class ThirteenF(unittest.TestCase):
    def test_cover_and_information_table_fields(self):
        raw = thirteen_f(b"03-31-2025", [(b"COREWEAVE INC", b"21873S108", b"1000", b"24182460", b"SH", None),
                                         (b"COREWEAVE INC", b"21873S108", b"10", b"5000", b"SH", b"Call")])
        p = O.parse_13f(raw)
        self.assertTrue(p["ok"])
        self.assertEqual((p["period"], p["amendment"], p["report_type"], p["confidential"]),
                         ("2025-03-31", False, "13F HOLDINGS REPORT", False))
        self.assertEqual([(x["cusip"], x["shares"], x["type"], x["put_call"]) for x in p["lines"]],
                         [("21873S108", "24182460", "SH", None), ("21873S108", "5000", "SH", "Call")])
        self.assertNotIn(b"NE PAS LIRE".decode(), repr(p))       # le bloc de signature ne se lit pas

    def test_restatement_replaces_and_new_holdings_add(self):
        base = {"kind": "13f", "s": "NVDA"}
        fs = [dict(base, accession="a1", filed="2025-05-15",
                   parsed=O.parse_13f(thirteen_f(b"03-31-2025", [(b"A CORP", b"000001101", b"1", b"1", b"SH", None)]))),
              dict(base, accession="a2", filed="2025-06-01",
                   parsed=O.parse_13f(thirteen_f(b"03-31-2025", [(b"B CORP", b"000002101", b"1", b"2", b"SH", None)],
                                                 amendment=b"NEW HOLDINGS"))),
              dict(base, accession="a3", filed="2025-08-14",
                   parsed=O.parse_13f(thirteen_f(b"06-30-2025", [(b"A CORP", b"000001101", b"1", b"3", b"SH", None)]))),
              dict(base, accession="a4", filed="2025-09-01",
                   parsed=O.parse_13f(thirteen_f(b"06-30-2025", [(b"C CORP", b"000003101", b"1", b"4", b"SH", None)],
                                                 amendment=b"RESTATEMENT")))]
        eff = O.effective(fs)
        self.assertEqual(sorted(x["issuer"] for x in eff["2025-03-31"]["lines"]), ["A CORP", "B CORP"])
        self.assertEqual([x["issuer"] for x in eff["2025-06-30"]["lines"]], ["C CORP"])
        self.assertEqual(eff["2025-06-30"]["accessions"], ["a4"])

    def test_values_in_thousands_before_2023(self):
        self.assertTrue(O.thousands("2022-11-14"))
        self.assertFalse(O.thousands("2023-01-03"))


class Attribution(unittest.TestCase):
    def test_legal_name_then_cusip_prefix_that_designates_one_node(self):
        legal = O.legal_forms([{"entity_id": "e:rivn", "record_kind": "entity", "name": "RIVIAN AUTOMOTIVE, INC. / DE",
                                "normalized_name": "rivian automotive inc / de", "status": "confirmed", "cik": "1874178"},
                               {"entity_id": "e:crwv", "record_kind": "entity", "name": "CoreWeave, Inc.",
                                "normalized_name": "coreweave inc", "status": "confirmed", "cik": "1769628"}])
        self.assertEqual(legal.get("rivian automotive inc"), "e:rivn")          # sans le suffixe d'État d'EDGAR
        node = {"e:rivn": "CP:rivian", "e:crwv": "CRWV"}
        lines = [{"issuer": "RIVIAN AUTOMOTIVE INC", "cusip": "76954A103", "period": "2022-03-31"},
                 {"issuer": "RIVIAN AUTOMOTIVE INC COM", "cusip": "76954A103", "period": "2022-06-30"},
                 {"issuer": "RIVIAN AUTO", "cusip": "76954A103", "period": "2022-09-30"},     # préfixe : Rivian seul
                 {"issuer": "COREWEAVE INC", "cusip": "21873S108", "period": "2025-03-31"},
                 {"issuer": "SOMETHING ELSE", "cusip": "21873S999", "period": "2025-03-31"},  # même préfixe : CoreWeave
                 {"issuer": "UNKNOWN", "cusip": "999999101", "period": "2025-03-31"}]
        got = O.attribute_lines(lines, legal, lambda e, d: node[e])
        self.assertEqual(got, [("CP:rivian", "legal_name"), ("CP:rivian", "legal_name"), ("CP:rivian", "cusip_prefix"),
                               ("CRWV", "legal_name"), ("CRWV", "cusip_prefix"), (None, None)])
        lines.append({"issuer": "RIVIAN AUTOMOTIVE INC", "cusip": "21873S000", "period": "2025-03-31"})   # préfixe disputé
        got = O.attribute_lines(lines, legal, lambda e, d: node[e])
        self.assertEqual(got[4], (None, None))


def eff_of(*periods):
    """Lignes en vigueur : (date, a une ligne de C, confidentiel, type de rapport)."""
    out = {}
    for d, has, conf, rt in periods:
        ls = [{"node": "CRWV", "type": "SH", "put_call": None, "shares": "10", "value": "1", "filed": d}] if has else []
        ls.append({"node": "OTHER", "type": "SH", "put_call": None, "shares": "1", "value": "1", "filed": d})
        out[d] = {"lines": ls, "accessions": ["acc-" + d], "filed": d[:8] + "28", "confidential": conf, "report_type": rt}
    return out


class Exits(unittest.TestCase):
    H = O.HOLDINGS_REPORT

    def test_a_complete_report_without_the_line_after_one_with_it(self):
        pos, ex, sk = O.positions_and_exits("NVDA", eff_of(("2025-03-31", True, False, self.H),
                                                           ("2025-06-30", False, False, self.H),
                                                           ("2025-09-30", False, False, self.H)), ["CRWV"])
        self.assertEqual(sorted(pos), [("CRWV", "2025-03-31")])
        self.assertEqual([(e["date"], e["previous"]) for e in ex["CRWV"]], [("2025-06-30", "2025-03-31")])

    def test_confidential_or_combined_reports_prove_no_exit(self):
        _, ex, sk = O.positions_and_exits("NVDA", eff_of(("2025-03-31", True, False, self.H),
                                                         ("2025-06-30", False, True, self.H)), ["CRWV"])
        self.assertEqual((ex, dict(sk)), ({}, {"confidential": 1}))
        _, ex, sk = O.positions_and_exits("NVDA", eff_of(("2025-03-31", True, False, self.H),
                                                         ("2025-06-30", False, False, "13F COMBINATION REPORT")), ["CRWV"])
        self.assertEqual((ex, dict(sk)), ({}, {"not_holdings_report": 1}))

    def test_options_and_principal_amounts_are_not_shares_held(self):
        e = eff_of(("2025-03-31", True, False, self.H), ("2025-06-30", True, False, self.H))
        e["2025-06-30"]["lines"][0]["put_call"] = "Put"
        pos, ex, _ = O.positions_and_exits("NVDA", e, ["CRWV"])
        self.assertEqual(sorted(pos), [("CRWV", "2025-03-31")])
        self.assertEqual([x["date"] for x in ex["CRWV"]], ["2025-06-30"])


XML_13G = b"""<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g">
 <formData><coverPageHeader><securitiesClassTitle>Class A Common Stock</securitiesClassTitle>
  <eventDateRequiresFilingThisStatement>%s</eventDateRequiresFilingThisStatement></coverPageHeader>
  <coverPageHeaderReportingPersonDetails><reportingPersonName>NE PAS LIRE</reportingPersonName>
   <reportingPersonBeneficiallyOwnedAggregateNumberOfShares>%s</reportingPersonBeneficiallyOwnedAggregateNumberOfShares>
   <classPercent>%s</classPercent></coverPageHeaderReportingPersonDetails></formData>
</edgarSubmission>"""
HTML_13G = (b"<html><body><p>SCHEDULE 13G</p><p>CoreWeave, Inc.</p><p>December 31, 2024</p>"
            b"<p>(Date of Event Which Requires Filing of this Statement)</p><table><tr><td>9.</td><td>Aggregate Amount "
            b"Beneficially Owned by Each Reporting Person</td><td>%s</td></tr><tr><td>11.</td><td>Percent of Class "
            b"Represented by Amount in Row (9)</td><td>%s</td></tr></table><p>Signature NE PAS LIRE</p></body></html>")


class Schedules(unittest.TestCase):
    def test_xml_cover_fields(self):
        raw = HEADER + doc(b"SCHEDULE 13G", XML_13G % (b"03/31/2025", b"24182460", b"5.96"))
        p = O.parse_13dg(raw)
        self.assertTrue(p["ok"], p.get("reason"))
        self.assertEqual((p["format"], p["event_date"], p["shares"], p["percent"], p["zero"]),
                         ("xml", "2025-03-31", Decimal("24182460"), Decimal("5.96"), False))
        self.assertNotIn("NE PAS LIRE", repr(p))

    def test_html_cover_template_and_zero_shares(self):
        raw = HEADER.replace(b"SCHEDULE 13G", b"SC 13G/A") + doc(b"SC 13G/A", HTML_13G % (b"18,033,758", b"5.2%"), xml=False)
        p = O.parse_13dg(raw)
        self.assertEqual((p["format"], p["event_date"], p["shares"], p["percent"]),
                         ("html", "2024-12-31", Decimal("18033758"), Decimal("5.2")))
        raw = HEADER.replace(b"SCHEDULE 13G", b"SC 13G/A") + doc(b"SC 13G/A", HTML_13G % (b"-0-", b"0%"), xml=False)
        p = O.parse_13dg(raw)
        self.assertEqual((p["shares"], p["percent"], p["zero"]), (Decimal(0), Decimal(0), True))
        self.assertNotIn("NE PAS LIRE", repr(p))

    def test_unreadable_cover_is_not_a_value(self):
        raw = HEADER + doc(b"SC 13G", b"<html><body>Item 4. See attached.</body></html>", xml=False)
        p = O.parse_13dg(raw)
        self.assertFalse(p["ok"])


def quarters(*fys):
    out = []
    for y in fys:
        for s, e in (("01-01", "03-31"), ("04-01", "06-30"), ("07-01", "09-30"), ("10-01", "12-31")):
            out.append({"start": D(f"{y}-{s}"), "end": D(f"{y}-{e}"), "fy_end": D(f"{y}-12-31")})
    return out


def edge(key, d, kd, edge_type):
    o = {"obs_key": key, "event_type": "recognition", "knowledge_date": kd, "amount_nature": "investment_carrying_amount",
         "group_id": "S"}
    return {"link_key": "edge:" + key, "from_group": "S", "to_group": "C", "family": "financing", "stage": "recognized",
            "tier": "A", "edge_type": edge_type, "instrument_key": None, "_obs": o, "_date": D(d)}


class FinancedStatus(unittest.TestCase):
    """Point 3 : une sortie publiée ferme les détentions en actions de la paire, une fois connue ; jamais les autres."""
    qs = quarters(2025)

    def status(self, edges, exits, cut):
        p = circularity.Pair("S", "C")
        p.edges = edges
        st = circularity.financed_status(p, self.qs, lambda q: D(cut), 8, False, None, exits)
        return st["exposure_outstanding"][D("2025-12-31")]

    def test_exit_closes_equity_once_known(self):
        eq = [edge("h1", "2025-03-31", "2025-05-01", "equity_primary")]
        ex = [(D("2025-06-30"), D("2025-08-14"))]
        self.assertEqual(self.status(eq, ex, "2026-02-01")[0], "lapsed")
        self.assertEqual(self.status(eq, ex, "2025-08-01")[0], "active")       # sortie pas encore connue
        self.assertEqual(self.status(eq, None, "2026-02-01")[0], "active")

    def test_exit_leaves_convertibles_and_later_purchases_open(self):
        cv = [edge("h2", "2025-03-31", "2025-05-01", "convertible_or_safe")]
        self.assertEqual(self.status(cv, [(D("2025-06-30"), D("2025-08-14"))], "2026-02-01"), ("active", ["edge:h2"]))
        later = [edge("h3", "2025-09-30", "2025-11-01", "equity_primary")]
        self.assertEqual(self.status(later, [(D("2025-06-30"), D("2025-08-14"))], "2026-02-01"), ("active", ["edge:h3"]))


if __name__ == "__main__":
    unittest.main()
