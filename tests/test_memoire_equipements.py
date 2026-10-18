"""ASML et SK hynix, émetteurs privés étrangers, et Samsung, non-déposant (D-0057) : noms qualifiants des unités
6-K de chaque groupe, jamais le groupe lui-même ; terme de Samsung dans la piste des non-déposants ; nom au rendu de
chaque groupe de config.yaml ; notes du 424B4 de SK hynix, qui tient lieu de rapports périodiques sans instance XBRL
financière (D-0057, point 14), découpées en HTML et lues par familles de titres ; items d'un 20-F numérotés dans la
seule table de correspondance (ASML, D-0057, point 15).

Lancement : python3 -m unittest discover -s tests -v
"""
import re
import unittest

from pipeline import config, regdoc, render, sections, sixk
from pipeline import discovery as D
from pipeline import nf_discovery as NF


class NomsDes6K(unittest.TestCase):
    def test_asml_jamais_son_propre_nom(self):
        rx = sixk.lexicon_rx("ASML", config.load())
        self.assertIsNone(rx.search("ASML reports third-quarter results"))
        for s in ("shipments to TSMC", "a supply deal with SK Hynix", "Samsung Electronics", "Intel orders"):
            self.assertTrue(rx.search(s), s)

    def test_sk_hynix_jamais_son_propre_nom(self):
        rx = sixk.lexicon_rx("SKHY", config.load())
        for s in ("SK hynix announces results", "SK Hynix Inc."):
            self.assertIsNone(rx.search(s), s)
        for s in ("EUV tools from ASML", "Samsung", "NVIDIA HBM orders"):
            self.assertTrue(rx.search(s), s)

    def test_unites_des_groupes_precedents_inchangees(self):
        """Les noms propres de TSMC (D-0056) ne gagnent ni ASML, ni SK hynix, ni Samsung (D-0057, point 10)."""
        rx = sixk.lexicon_rx("TSM", config.load())
        for s in ("ASML", "SK hynix", "Samsung"):
            self.assertIsNone(rx.search(s), s)


class PisteSamsung(unittest.TestCase):
    def test_terme_en_mot_entier_insensible_a_la_casse(self):
        lex = [e for e in NF.nf_lexicon(config.load()) if e["ref"] == "NF:SAMSUNG"]
        self.assertEqual([e["term"] for e in lex], ["Samsung"])
        rx, _ = D.compile_lexicon(lex)
        for s in ("supply agreement with Samsung Electronics Co., Ltd.", "SAMSUNG DISPLAY CO., LTD.", "Samsung's"):
            self.assertTrue(rx.search(s), s)
        self.assertIsNone(rx.search("SamsungPay"))


class NomsAuRendu(unittest.TestCase):
    def test_chaque_groupe_a_un_nom(self):
        cfg = config.load()
        self.assertEqual([g for g in cfg["groups"] if g not in render.GROUP_NAMES], [])
        self.assertEqual(render.n_groups(cfg), render.NUM_FR[len(cfg["groups"])])
        self.assertEqual(render.group_label("NF:SAMSUNG"), "Samsung")


def _page(n, header):
    """Pied de page « F-n » suivi des titres courants de la page suivante."""
    return f"<p>F-{n}</p>" + "".join(f"<p><b>{h}</b></p>" for h in header)


ANNUAL = ["Table of Contents", "Example Co. and Subsidiaries", "Notes to the Consolidated Financial Statement",
          "Years ended December 31, 2025, 2024 and 2023"]
INTERIM = ["Table of Contents", "Example Co. and Subsidiaries",
           "Notes to the Condensed Consolidated Interim Financial Statements", "March 31, 2026 (Unaudited)"]
DOC = ("<html><body>"
       "<p>Notes to the Consolidated Financial Statements | F-11</p>"
       "<p><b>Consolidated Statements of Cash Flows</b></p><p>Cash flows from operating activities | 1 | 2</p>"
       + _page(10, ANNUAL) +
       "<p><b>1. General Information</b></p><p>The Group manufactures memory.</p>"
       "<p><b>2. Material Accounting Policies</b></p><p>(1) Basis of preparation</p><p>Prepared under IFRS.</p>"
       "<p>(2) Property, plant and equipment</p><p>Buildings are depreciated over 10 to 50 years.</p>"
       + _page(11, ANNUAL) +
       "<p><b>2. Material Accounting Policies, Continued</b></p><p>(2) Property, plant and equipment, Continued</p>"
       "<p>Machinery is depreciated over 5 years.</p><p>(3) Leases</p><p>Lessee accounting.</p>"
       "<p><b>3. Operating Segment and Entity-wide Information</b></p><p>The Group has a single reportable segment.</p>"
       "<p>(2) Revenue of W1 million, or 23.9% of the Group's revenue, is derived from an external customer A.</p>"
       "<p><b>4. Borrowings</b></p><p>Commercial Paper | Shinhan Bank | 300,000</p>"
       + _page(12, ANNUAL) +
       "<p><b>4. Borrowings, Continued</b></p><p>Long-term borrowings | MUFG and others | 3,473,363</p>"
       "<p><b>5. Transactions with Related Parties and Others</b></p><p>SK Square Co., Ltd. is the largest shareholder.</p>"
       + _page(13, ANNUAL) +
       "<p><b>5. Transactions with Related Parties and Others, Continued</b></p><p>Sales to related parties | 12</p>"
       "<p><b>6. Subsequent Event</b></p><p>None.</p>"
       + _page(14, ANNUAL[:2]) +
       "<p><b>Condensed Consolidated Interim Statements of Financial Position</b></p><p>Assets | 1 | 2</p>"
       + _page(15, INTERIM) +
       "<p><b>1. General Information</b></p><p>Interim information.</p>"
       + _page(16, INTERIM) +
       "<p><b>1. General Information, Continued</b></p><p>Subsidiaries.</p>"
       "<p><b>2. Leases</b></p><p>Right-of-use assets | 820</p>"
       + _page(17, INTERIM) +
       "<p><b>2. Leases, Continued</b></p><p>Lease liabilities | 526</p>"
       + _page(18, ["Table of Contents"]) +
       "<p><b>17,790,000 Common Shares</b></p><p>BofA Securities | Citigroup</p>"
       "</body></html>").encode()
SPEC = {"group": "SKHY", "accession": "0000000000-26-000001", "primary": "doc.htm", "decision": "D-0057",
        "note_sets": [{"period_start": "2023-01-01", "period_end": "2025-12-31", "label": "annuels", "assurance": "audited"},
                      {"period_start": "2026-01-01", "period_end": "2026-03-31", "label": "intermédiaires",
                       "assurance": "unaudited"}]}
FILING = {"group_id": "SKHY", "cik": "0002120882", "accession": "0000000000-26-000001", "form": "424B4",
          "filing_date": "2026-07-10", "acceptance": None, "report_date": None}


class DocumentDEnregistrement(unittest.TestCase):
    """Notes d'un document d'enregistrement en HTML (D-0057, point 14)."""

    @classmethod
    def setUpClass(cls):
        cls.sets = regdoc.note_sets(DOC)

    def test_deux_jeux_numerotation_suivie(self):
        self.assertEqual([[n["title"] for n in s["notes"]] for s in self.sets],
                         [["General Information", "Material Accounting Policies", "Operating Segment and Entity-wide Information",
                           "Borrowings", "Transactions with Related Parties and Others", "Subsequent Event"],
                          ["General Information", "Leases"]])

    def test_pieds_de_page_et_titres_courants_retires(self):
        for s in self.sets:
            for n in s["notes"]:
                for noise in ("Table of Contents", "Example Co. and Subsidiaries", "Notes to the", "F-1", "Common Shares", "BofA"):
                    self.assertNotIn(noise, n["text"], (n["title"], noise))
                self.assertIsNone(re.search(r"(?m)^\d{1,2}\. .*, Continued$", n["text"]), n["title"])
        debt = self.sets[0]["notes"][3]["text"]
        self.assertIn("Shinhan Bank", debt)
        self.assertIn("MUFG and others", debt)
        self.assertNotIn("4. Borrowings, Continued", debt)
        self.assertIn("Lease liabilities | 526", self.sets[1]["notes"][1]["text"])

    def test_familles_par_titre(self):
        expect = {"Borrowings": "debt_note", "Transactions with Related Parties and Others": "related_party_note",
                  "Investments in Associates and Joint Ventures": "investment_note", "Leases": "lease_note",
                  "Commitments and Contingencies": "commitments_note", "Revenue": "revenue_note",
                  "Property, Plant and Equipment": "lever_note", "Critical Accounting Estimates and Assumptions": "lever_note",
                  "General Information": None, "Subsequent Event": None, "Derivative Financial Instruments": None}
        self.assertEqual({t: regdoc.note_kind(t) for t in expect}, expect)

    def test_principe_des_immobilisations_et_clients(self):
        ppe = regdoc.ppe_policy(self.sets[0]["notes"][1])
        self.assertIn("10 to 50 years", ppe)
        self.assertIn("Machinery is depreciated over 5 years", ppe)
        self.assertNotIn("Lessee accounting", ppe)
        cust = regdoc.customer_paragraphs(self.sets[0]["notes"][2])
        self.assertIn("external customer A", cust)
        self.assertNotIn("single reportable segment", cust)

    def test_blocs_et_niveaux(self):
        bl = regdoc.document_blocks(SPEC, FILING, DOC)
        got = [(b["block_kind"], b["tier"], b["assurance_level"], b["period_end"]) for b in bl]
        self.assertEqual(got, [("lever_note", "A", "audited", "2025-12-31"), ("concentration_text", "A", "audited", "2025-12-31"),
                               ("debt_note", "A", "audited", "2025-12-31"), ("related_party_note", "A", "audited", "2025-12-31"),
                               ("lease_note", "C", "unaudited", "2026-03-31")])
        with self.assertRaises(ValueError):
            regdoc.document_blocks(dict(SPEC, note_sets=SPEC["note_sets"][:1]), FILING, DOC)

    def test_sk_hynix_dans_config(self):
        cfg = config.load()
        spec = [s for s in cfg["registration_text"] if s["group"] == "SKHY"]
        self.assertEqual([s["accession"] for s in spec], ["0001193125-26-299963"])
        self.assertEqual([st["assurance"] for st in spec[0]["note_sets"]], ["audited", "unaudited"])
        self.assertEqual(str(cfg["reporting_start"]["SKHY"]["fiscal_year"][0]), "2023-01-01")
        self.assertEqual(cfg["group_frameworks"]["SKHY"], "ifrs")


def _xref_doc(controls_after_footer=False, contracts="Appendix - Material contracts"):
    """20-F à table de correspondance, sur le modèle des rapports annuels d'ASML."""
    foot = lambda n: f"<p>ANNUAL REPORT | APPENDICES | {n}</p>"
    ctl = ("<p><b>Disclosure controls and procedures</b></p><p>Management concluded that disclosure controls are "
           "effective.</p>")
    if controls_after_footer:
        # titre de page linéarisé après le pied de sa page : le texte précède le titre
        appendices = ("<p><b>Appendix - Material contracts</b></p><p>Framework agreement with Carl Zeiss SMT GmbH.</p>"
                      + foot(301) + "<p><b>Appendix - Documents on display</b></p>" + ctl + foot(302)
                      + "<p><b>Appendix - Controls and procedures</b></p><p>Financial calendar.</p>" + foot(303)
                      + "<p><b>Appendix - Financial calendar</b></p>")
    else:
        appendices = ("<p><b>Appendix - Material contracts</b></p><p>Framework agreement with Carl Zeiss SMT GmbH.</p>"
                      + foot(301) + "<p><b>Appendix - Controls and procedures</b></p>" + ctl + foot(302)
                      + "<p><b>Appendix - Financial calendar</b></p><p>April 15, 2026</p>" + foot(303))
    table = ("<p><b>Appendix - Reference table 20-F</b></p>"
             "<p>7 | Major Shareholders and Related Party Transactions</p>"
             "<p>B. Related Party Transactions | Note 26 Related parties and variable interest entities | 323</p>"
             "<p>C. Interests of Experts and Counsel | Not applicable</p>"
             "<p>10 | Additional Information</p>"
             f"<p>C. Material Contracts | {contracts} | 301</p>"
             "<p>D. Exchange Controls | Appendix - Exchange controls | 330</p>"
             "<p>15 | Controls and Procedures | Appendix - Controls and procedures | 302</p>"
             "<p>16A | Audit Committee Financial Expert | Board | 90</p>")
    return ("<html><body><p>Our business.</p>" + foot(299) + foot(300) + appendices + table + "</body></html>").encode()


class TableDeCorrespondance20F(unittest.TestCase):
    """Items 15, 7.B et 10.C d'un 20-F qui ne les numérote que dans sa table de correspondance (D-0057, point 15)."""

    def test_sections_designees(self):
        x = sections.xref_20f(_xref_doc())
        self.assertEqual(x["7.B"][0], "note")
        self.assertEqual(x["15"][0], "section")
        self.assertTrue(x["15"][1].startswith("Appendix - Controls and procedures\nDisclosure controls and procedures"))
        self.assertNotIn("April 15, 2026", x["15"][1])
        self.assertNotIn("ANNUAL REPORT", x["15"][1])
        self.assertIn("Carl Zeiss SMT GmbH", x["10.C"][1])

    def test_titre_apres_son_contenu(self):
        x = sections.xref_20f(_xref_doc(controls_after_footer=True))
        self.assertIn("disclosure controls are effective", x["15"][1])
        self.assertNotIn("Financial calendar.", x["15"][1])

    def test_aucun_contrat_et_sans_table(self):
        x = sections.xref_20f(_xref_doc(contracts="None"))
        self.assertEqual(x["10.C"], ("none", ["None"]))
        self.assertIsNone(sections.xref_20f(b"<html><body><p>Item 15. Controls and Procedures</p></body></html>"))


if __name__ == "__main__":
    unittest.main()
