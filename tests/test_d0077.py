"""D-0077 : document d'enregistrement d'un laboratoire (S-1 d'Anthropic) lu comme son texte propre.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import json
import unittest

import pandas as pd

from pipeline import assemble
from pipeline import circularity as C
from pipeline import entities as E
from pipeline import fsignals as Fs
from pipeline import links, load, nf_discovery
from pipeline import nf_discovery as N
from pipeline.graph import normalize_name


def entity(eid, name, group, rule="executor_decision"):
    return [{"record_kind": "entity", "entity_id": eid, "name": name, "normalized_name": normalize_name(name),
             "status": "confirmed"},
            {"record_kind": "membership", "entity_id": eid, "ref": group, "status": "confirmed", "valid_from": "none",
             "valid_to": None, "consolidation_treatment": "parent", "resolution_rule": rule}]


REG = E.Registry(entity("name:anthropic pbc", "Anthropic PBC", "LAB:ANTHROPIC")
                 + entity("lab:anthropic", "Anthropic", "LAB:ANTHROPIC", rule="config_seed")
                 + entity("cik:1018724", "Amazon.com, Inc.", "AMZN", rule="same_cik"))


def line(payer, payee, group="LAB:ANTHROPIC"):
    return {"kind": "observation", "validation_state": "valid", "obs_key": "k1", "family": "commercial",
            "edge_type": "purchase_commitment", "counterparty_evidence": "named", "counterparty_name": payee,
            "payer": payer, "payee": payee, "group_id": group, "tier": "C", "stage": "signed",
            "amount": "1000000000", "unit": "USD", "currency": "USD", "amount_nature": "commitment_unexecuted",
            "amount_qualifier": "exact", "period_end": "2026-06-30", "knowledge_date": "2026-10-26"}


class _OwnFilers:
    def __init__(self, refs):
        self.refs, self.old = refs, None

    def __enter__(self):
        self.old = nf_discovery.own_filer_ciks
        nf_discovery.own_filer_ciks = lambda cfg=None: dict(self.refs)

    def __exit__(self, *a):
        nf_discovery.own_filer_ciks = self.old


class LabOwnFiling(unittest.TestCase):
    def test_the_company_designe_le_laboratoire(self):
        with _OwnFilers({"2130357": "LAB:ANTHROPIC"}):
            edges, _ = links.build_edges([line("the Company", "Amazon.com, Inc.")], REG)
        e = edges[0]
        self.assertEqual((e["from_entity"], e["from_group"], e["to_group"]), ("lab:anthropic", "LAB:ANTHROPIC", "AMZN"))
        self.assertEqual(e["source_perspective"], "reporting_entity")

    def test_sans_document_propre_le_laboratoire_n_a_pas_de_tete(self):
        # un laboratoire qui n'a pas déposé : « the Company » d'un bloc à son nom ne le désigne pas
        with _OwnFilers({}):
            edges, _ = links.build_edges([line("the Company", "Amazon.com, Inc.")], REG)
        self.assertNotEqual(edges[0]["from_group"], "LAB:ANTHROPIC")


TOC = [("SUMMARY | 1", False), ("MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION | 5", False),
       ("BUSINESS | 9", False), ("EXPERTS | 12", False)]


class ProspectusSections(unittest.TestCase):
    def test_titres_coupes_et_ordre_du_sommaire(self):
        lines = TOC + [("Summary", True), ("Our business is described below.", False),
                       ("Management\u2019s Discussion and Analysis of", True), ("Financial Condition", True),
                       ("Revenue grew.", False),
                       ("Business", True), ("We sell models.", False)]
        secs, missing = N.prospectus_sections(lines)
        self.assertEqual([(t, a, b) for _, t, a, b in secs],
                         [("SUMMARY", 4, 6), ("MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION", 6, 9),
                          ("BUSINESS", 9, 11)])
        self.assertEqual(missing, ["EXPERTS"])

    def test_un_titre_se_cherche_apres_le_precedent(self):
        # « Business », titre plus haut que le résumé, n'ouvre pas la section : on le cherche après le titre précédent
        lines = [("BUSINESS OVERVIEW | 1", False), ("BUSINESS | 2", False),
                 ("Business", True), ("Early mention.", False), ("Business Overview", True), ("Text.", False),
                 ("Business", True), ("Real section.", False)]
        secs, _ = N.prospectus_sections(lines)
        self.assertEqual([(t, a) for _, t, a, _ in secs], [("BUSINESS OVERVIEW", 4), ("BUSINESS", 6)])

    def test_rangee_de_tableau_jamais_titre(self):
        self.assertEqual(N._title_at([("Business | 2024 | 2025", True)], 0, "business"), 0)
        self.assertEqual(N._title_at([("Business", False)], 0, "business"), 1)


def m(t, head=False, par=False):
    return (t, head, par)


class SplitSection(unittest.TestCase):
    def test_intertitres_puis_regroupement(self):
        marked = [m("H1", True), m("a" * 10), m("H2", True), m("b" * 10), m("H3", True), m("c" * 10)]
        blocks = N.split_section(marked, 30)
        self.assertEqual([[x[0] for x in b] for b in blocks], [["H1", "a" * 10, "H2", "b" * 10], ["H3", "c" * 10]])

    def test_segment_long_coupe_aux_paragraphes_jamais_dedans(self):
        marked = [m("H", True), m("x" * 20, par=True), m("y" * 20), m("z" * 20, par=True), m("w" * 20)]
        blocks = N.split_section(marked, 45)
        self.assertEqual([[x[0][0] for x in b] for b in blocks], [["H", "x", "y"], ["z", "w"]])
        # un paragraphe plus long que le plafond reste entier
        one = N.split_section([m("H", True), m("q" * 50, par=True), m("r" * 50)], 30)
        self.assertEqual([[x[0][0] for x in b] for b in one], [["H"], ["q", "r"]])

    def test_intertitre_en_italique_suit_sa_legende(self):
        marked = [m("H1", True), m("text one."), m("Sub heading", par=True), m("Year Ended", True), m("row | 1")]
        blocks = N.split_section(marked, 25)
        self.assertEqual([x[0] for x in blocks[-1]][:2], ["Sub heading", "Year Ended"])


class Paragraphs(unittest.TestCase):
    HTML = (b'<html><body><div style="background-color:#FFF;border:1px solid #CCC">'
            b'<div style="position:absolute;top:20pt">Table of Contents</div>'
            b'<div style="position:absolute;top:72pt">first line</div>'
            b'<div style="position:absolute;top:83.4pt">second line</div>'
            b'<div style="position:absolute;top:103.8pt">new paragraph</div></div>'
            b'<div style="background-color:#FFF;border:1px solid #CCC">'
            b'<div style="position:absolute;top:20pt">Table of Contents</div>'
            b'<div style="position:absolute;top:72pt">after page break</div></div></body></html>')

    def test_ecart_vertical_et_saut_de_page(self):
        seq = N.paragraph_starts(self.HTML, noise=lambda t: t == "Table of Contents")
        self.assertEqual(seq, [("Table of Contents", False), ("first line", False), ("second line", False),
                               ("new paragraph", True), ("Table of Contents", False), ("after page break", False)])

    def test_alignement_par_suite_commune(self):
        lines = [("first line", False), ("x | y", False), ("second line", False), ("new paragraph", True)]
        seq = [("first line", False), ("x", False), ("y", False), ("second line", False), ("new paragraph", True)]
        self.assertEqual([p for _, _, p in N.mark_paragraphs(lines, seq)], [False, False, False, True])


class NotesHeadings(unittest.TestCase):
    HTML = (b"<html><body><div><b>Notes to Consolidated Financial Statements</b></div>"
            b"<div><b>1. Description of Business</b></div><div>The Company is a lab. Amounts are in the</div>"
            b"<div>consolidated statements of cash flows. More text.</div>"
            b"<div><b>2. Redeemable Preferred Stock and</b></div><div><b>Stockholders' Deficit</b></div><div>Text.</div>"
            b"<div><b>Part II</b></div></body></html>")

    def test_titres_en_casse_de_titre_et_fin_de_jeu_sur_un_titre(self):
        notes = N.financial_notes_html(self.HTML, headings=True)
        self.assertEqual([(n["number"], n["title"]) for n in notes],
                         [(1, "Description of Business"), (2, "Redeemable Preferred Stock and Stockholders' Deficit")])
        self.assertIn("consolidated statements of cash flows", notes[0]["text"])

    def test_sans_option_rien_ne_change(self):
        # règle de D-0054 : un titre de note en casse de titre n'ouvre pas de note
        self.assertEqual(N.financial_notes_html(self.HTML), [])


class LineLevel(unittest.TestCase):
    def test_ligne_apres_la_derniere_date_auditee(self):
        b = {"tier": "A", "assurance_level": "audited", "audited_through": "2025-12-31"}
        self.assertEqual(load._line_level(b, {"period_end": "2026-06-30"}), ("C", "unaudited"))
        self.assertEqual(load._line_level(b, {"period_end": "2025-12-31"}), ("A", "audited"))
        self.assertEqual(load._line_level(b, {"event_date": "2026-02-01"}), ("C", "unaudited"))
        self.assertEqual(load._line_level({"tier": "C", "assurance_level": "not_applicable"}, {"period_end": "2026-06-30"}),
                         ("C", "not_applicable"))



class Integration(unittest.TestCase):
    """Intégration (D-0077, point 12) : chaque entité nommée par le S-1 cite son extrait ; une désignation de fonds
    gérés reste en attente (D-0055, point 5) ; une appartenance que le texte n'écrit pas ne se suppose pas."""

    def setUp(self):
        from pipeline import config
        self.cfg = config.load()

    def test_entrees_citent_leur_extrait(self):
        rows = [c for k in ("confirmed_entities", "own_entities", "entity_aliases") for c in self.cfg[k]
                if c.get("decision") == "D-0077"]
        self.assertEqual(len(rows), 8)
        for c in rows:
            self.assertRegex(c["block"], r"^[0-9a-f]{64}$")
            self.assertEqual(c["accession"], "0001628280-26-067168")
            self.assertTrue(c["quote"].strip())

    def test_rattachements(self):
        names = ["SpaceX.AI LLC", "AI Infrastructure OpCo II, LLC", "Anthropic Public Benefit Fund",
                 "Long-Term Benefit Trust", "Spark Capital", "an entity managed by Apollo Global Management, Inc.",
                 "AI Infrastructure OpCo, LLC"]
        _, reg = E.build({"meta": {}}, self.cfg, {n: False for n in names})
        g = lambda n: E.resolve(reg, n, "2026-10-26")[1]
        self.assertEqual(g("SpaceX.AI LLC"), "SPCX")
        self.assertEqual(g("AI Infrastructure OpCo II, LLC"), "LAB:ANTHROPIC")
        self.assertEqual(g("Anthropic Public Benefit Fund"), "LAB:ANTHROPIC")
        self.assertEqual(g("Long-Term Benefit Trust"), "LAB:ANTHROPIC")
        self.assertEqual(g("Spark Capital"), "CP:spark capital")
        self.assertIsNone(g("an entity managed by Apollo Global Management, Inc."))
        self.assertEqual(g("AI Infrastructure OpCo, LLC"), "CP:ai infrastructure opco llc")


def fin(key, ik, date, amount, group, nature="financing_cash", basis="principal", event="funding",
        edge_type="convertible_or_safe", unit="USD", frm="AMZN", to="LAB:ANTHROPIC"):
    return {"link_key": "edge:" + key, "instrument_key": ik, "family": "financing", "edge_type": edge_type,
            "from_group": frm, "to_group": to, "edge_evidence": "amount", "_date": dt.date.fromisoformat(date), "tier": "A",
            "unit": unit, "amount": amount, "elimination_status": "not_applicable",
            "_obs": {"amount": amount, "unit": unit, "event_type": event, "amount_nature": nature,
                     "measurement_basis": basis, "knowledge_date": date, "group_id": group}}


class Perspective(unittest.TestCase):
    """Point 10 : une perspective par paire ; un encours est un état ; une ligne sans numéraire n'est pas un apport ;
    l'invariant (e) écarte un agrégat qui mêle les deux perspectives d'une même contrepartie."""

    def exposure(self, edges, s="AMZN"):
        p = C.Pair(s, "LAB:ANTHROPIC")
        p.edges = edges
        q = dt.date(2026, 6, 30)
        ev = {(s, "LAB:ANTHROPIC"): {"F": {"as_known": {"exposure_outstanding": {q: ("active", [])}}}}}
        out = C.counterparty_exposure({(s, "LAB:ANTHROPIC"): p}, ev, {s: {"quarters": [{"end": q}]}}, "2026-10-27",
                                      text_done=frozenset({s}))
        return {c["breakdown_key"]: (c["value"], json.loads(c["flags"]).get("perspective")) for c in out}

    def test_les_lignes_du_groupe_mesure_l_emportent(self):
        got = self.exposure([fin("a", "amzn:n", "2023-09-30", "1250000000", "AMZN"),
                             fin("b", "amzn:n", "2024-03-31", "2750000000", "AMZN"),
                             fin("c", "anthropic:n23", "2023-09-30", "1200000000", "LAB:ANTHROPIC"),
                             fin("d", "anthropic:n23", "2024-03-31", "2800000000", "LAB:ANTHROPIC")])
        self.assertEqual(got, {"exposed_assets/cost/equity_investment": (4000000000, "reporting_entity")})

    def test_une_perspective_par_ligne_de_la_matrice(self):
        # NVIDIA publie la juste valeur de sa participation ; CoreWeave, le soutien de capacité et l'achat d'actions
        got = self.exposure([fin("a", "nvda:crwv", "2025-04-27", "1000000000", "NVDA", nature="fair_value", basis="fair_value",
                                 event="recognition", edge_type="equity_primary", frm="NVDA"),
                             fin("b", "crwv:spa", "2026-01-23", "2000000000", "CRWV", basis=None, edge_type="equity_primary",
                                 frm="NVDA")], s="NVDA")
        self.assertEqual(got, {"exposed_assets/fair_value/equity_investment": (1000000000, "reporting_entity"),
                               "exposed_assets/cost/equity_investment": (2000000000, "counterparty")})

    def test_sinon_les_lignes_d_autrui_dites_comme_telles(self):
        got = self.exposure([fin("a", "anthropic:g23", "2023-09-30", "500000000", "LAB:ANTHROPIC", frm="GOOGL"),
                             fin("b", "anthropic:g23", "2024-09-30", "750000000", "LAB:ANTHROPIC", frm="GOOGL")], s="GOOGL")
        self.assertEqual(got, {"exposed_assets/cost/equity_investment": (1250000000, "counterparty")})

    def test_encours_etat_perime_par_une_fin_du_meme_instrument(self):
        got = self.exposure([fin("a", "anthropic:n23", "2023-09-30", "1200000000", "LAB:ANTHROPIC"),
                             fin("b", "anthropic:n23", "2025-12-31", "2600000000", "LAB:ANTHROPIC", basis="outstanding_balance",
                                 event=None),
                             fin("c", "anthropic:n23", "2026-06-30", "2200000000", "LAB:ANTHROPIC", basis="outstanding_balance",
                                 event=None),
                             fin("d", "anthropic:g23", "2025-12-31", "750000000", "LAB:ANTHROPIC", basis="outstanding_balance",
                                 event=None),
                             fin("e", "anthropic:g23", "2026-01-31", "3300000", "LAB:ANTHROPIC", nature="financing_noncash",
                                 basis=None, event="conversion", unit="shares")])
        self.assertEqual(got["exposed_assets/cost/equity_investment"][0], 1200000000)
        self.assertEqual(got["exposed_assets/outstanding_balance/equity_investment"][0], 2200000000)

    def test_billet_sans_numeraire_n_est_pas_un_apport(self):
        got = self.exposure([fin("a", "anthropic:n23", "2024-03-31", "2800000000", "LAB:ANTHROPIC"),
                             fin("b", "anthropic:n23", "2025-12-31", "3100000000", "LAB:ANTHROPIC", nature="financing_noncash",
                                 event="amendment")])
        self.assertEqual(got, {"exposed_assets/cost/equity_investment": (2800000000, "counterparty")})

    def test_flux_apres_financement(self):
        q = {"start": dt.date(2026, 4, 1), "end": dt.date(2026, 6, 30)}
        m = pd.DataFrame([{"measure": "fcf_basic", "subject": "AMZN", "period_end": "2026-06-30", "view": v,
                           "status": "computed", "value": "1000", "nd_reason": None, "lineage": "[]", "knowledge_date": None}
                          for v in ("revised", "as_known")])
        edges = [fin("a", "amzn:h", "2026-06-30", "500", "AMZN", basis=None),
                 fin("b", "anthropic:h", "2026-05-31", "500", "LAB:ANTHROPIC", basis=None),
                 fin("c", "anthropic:n23", "2026-06-30", "220", "LAB:ANTHROPIC", basis="outstanding_balance", event=None),
                 fin("d", "x:loan", "2026-05-15", "100", "CP:x", basis=None, frm="AMZN", to="CP:x")]
        out = [c for c in Fs.counterparty_financing(["AMZN"], {"AMZN": [q]}, edges, m, "2026-10-27",
                                                    text_done=frozenset({"AMZN"})) if c["view"] == "as_known"]
        self.assertEqual(out[0]["value"], 400)
        fl = json.loads(out[0]["flags"])
        self.assertEqual((fl["financing_given"], fl["financing_given_counterparty"]), (["edge:a"], ["edge:d"]))

    def test_invariant_e(self):
        edges = [fin("a", "amzn:n", "2024-03-31", "100", "AMZN"), fin("b", "anthropic:n", "2024-03-31", "100", "LAB:ANTHROPIC"),
                 fin("c", "x:loan", "2024-03-31", "100", "CP:x", to="CP:x")]
        cell = lambda keys, measure="counterparty_exposure": {
            "measure": measure, "subject": "AMZN", "counterparty": "LAB:ANTHROPIC", "period_end": "2026-06-30",
            "breakdown_key": "none", "as_of": "2026-10-27", "status": "computed", "value": 200, "nd_reason": None,
            "flags": json.dumps({"links": keys})}
        mixed = cell(["edge:a", "edge:b"])
        out = assemble.invariants([mixed], edges, [], None)
        self.assertEqual((mixed["status"], mixed["nd_reason"], mixed["value"]), ("not_determinable", "mixed_perspective", None))
        self.assertEqual(out[0]["invariant"], "e")
        # deux contreparties, une perspective chacune : ventilé, admis
        fcf = cell(["edge:a", "edge:c"], "fcf_after_counterparty_financing")
        self.assertEqual(assemble.invariants([fcf], edges, [], None), [])


if __name__ == "__main__":
    unittest.main()
