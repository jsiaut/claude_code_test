"""D-0078 : partie désignée par un terme défini (D-0039 précisé), plafond d'engagement périmé par un tirage, et garde :
aucune ligne chargée ne nomme une personne physique.

Lancement : python3 -m unittest tests.test_d0078 -v
"""
import datetime as dt
import json
import pathlib
import re
import tempfile
import unittest

import pandas as pd

from pipeline import circularity as C
from pipeline import config
from pipeline import entities as E
from pipeline import render as R
from pipeline.graph import normalize_name


def entity(eid, name, group):
    return [{"record_kind": "entity", "entity_id": eid, "name": name, "normalized_name": normalize_name(name),
             "status": "confirmed"},
            {"record_kind": "membership", "entity_id": eid, "ref": group, "status": "confirmed"}]


REG = E.Registry(entity("e:avgo", "Broadcom Inc.", "AVGO") + entity("e:anth", "Anthropic, PBC", "LAB:ANTHROPIC")
                 + entity("e:amzn", "Amazon.com NV Investment Holdings LLC", "AMZN")
                 + entity("e:oai", "OpenAI Group PBC", "LAB:OPENAI"))

NPA = ('This NOTE PURCHASE AGREEMENT (this "Agreement") is made as of March 31, 2026 (the "Effective Date"), by and '
       'between ANTHROPIC, PBC, a Delaware public benefit corporation (the "Company"), and BROADCOM INC. (the "Investor").')
ECL = ('This equity commitment letter agreement (this "Agreement") confirms the commitments made among (a) Amazon.com NV '
       'Investment Holdings LLC, a Nevada limited liability company (the "Holder"), and (c) OpenAI Group PBC, a Delaware '
       'public benefit corporation (the "Company").')


def line(group, payer, payee, quote, doc="d1"):
    return {"kind": "observation", "validation_state": "valid", "link_category": "L1", "group_id": group,
            "payer": payer, "payee": payee, "counterparty_name": payer if payee == "the Company" else payee,
            "quote": quote, "event_date": "2026-03-31", "obs_key": f"{group}/{doc}/{quote[:12]}", "doc_key": doc}


class DefinedTerms(unittest.TestCase):
    def pieces(self, pair, o, defs):
        s_names, c_names = C.names_of_group(REG, pair.s), C.names_of_group(REG, pair.c)
        return [x["obs_key"] for x in C.link_pieces(pair, [o], REG, s_names, c_names, defs)]

    def test_le_terme_defini_au_preambule_nomme_la_partie(self):
        pair = C.Pair("AVGO", "LAB:ANTHROPIC")
        o = line("LAB:ANTHROPIC", "BROADCOM INC.", "the Company",
                 "the Company may issue Notes to the Investor on any Quarterly Due Date")
        defs = {"d1": C.term_definitions(NPA)}
        self.assertEqual(self.pieces(pair, o, defs), [o["obs_key"]])
        # sans le texte du document, « the Investor » ne nomme personne (règle de D-0039)
        self.assertEqual(self.pieces(pair, o, None), [])
        # le terme d'un autre document ne vaut pas
        self.assertEqual(self.pieces(pair, o, {"d2": C.term_definitions(NPA)}), [])

    def test_terme_compose_n_est_pas_le_terme(self):
        pair = C.Pair("AVGO", "LAB:ANTHROPIC")
        o = line("LAB:ANTHROPIC", "BROADCOM INC.", "the Company",
                 "pursuant to any Investor Agreement, the Company shall pay the Quarterly Fees")
        self.assertEqual(self.pieces(pair, o, {"d1": C.term_definitions(NPA)}), [])

    def test_the_company_defini_comme_l_autre_partie(self):
        pair = C.Pair("AMZN", "LAB:OPENAI")
        defs = {"d1": C.term_definitions(ECL)}
        both = line("AMZN", "Amazon.com NV Investment Holdings LLC", "OpenAI Group PBC",
                    "the obligation of the Company to sell and issue to the Holder any Eligible Shares shall terminate")
        self.assertEqual(self.pieces(pair, both, defs), [both["obs_key"]])
        # « the Company » est ici OpenAI : il ne désigne plus Amazon, déposant de la lettre
        only_c = line("AMZN", "Amazon.com NV Investment Holdings LLC", "OpenAI Group PBC",
                      "the Company (OpenAI Group PBC) shall sell and issue the Eligible Shares")
        self.assertEqual(self.pieces(pair, only_c, None), [only_c["obs_key"]])
        self.assertEqual(self.pieces(pair, only_c, defs), [])

    def test_definitions_qui_ne_designent_pas_une_partie(self):
        s, c = {"Broadcom Inc."}, {"Anthropic, PBC"}
        text = ('ANTHROPIC, PBC NOTE PURCHASE AGREEMENT This NOTE PURCHASE AGREEMENT (this "Agreement") is made. '
                'Broadcom Inc. hereby agrees to act as notes collateral agent (the "Notes Collateral Agent"). '
                '"Lease Agreement" means the lease dated as of the Effective Date, between Broadcom Inc. and AI '
                'Infrastructure OpCo II, LLC. "Investor" means Broadcom Inc. and its Affiliates. '
                'Broadcom Inc. (the "Lender"); Anthropic, PBC (the "Lender").')
        got = C.defined_parties(C.term_definitions(text), s, c)
        # « Lender » se rapporte aux deux parties : il ne compte pas
        self.assertEqual(got, {"Investor": "s"})
        self.assertEqual(C.defined_parties(C.term_definitions(
            'and Google LLC (together with its subsidiaries and Affiliates, the "Investor").'), {"Google LLC"}, c),
            {"Investor": "s"})
        self.assertEqual(C.defined_parties(C.term_definitions(
            'Amazon Web Services (collectively with its affiliates "Customer")'), {"Marvell"}, {"Amazon Web Services"}),
            {"Customer": "c"})


def edge(key, ik, date, amount, group, nature, basis, event, stage, cat=None):
    return {"link_key": "edge:" + key, "instrument_key": ik, "family": "financing", "edge_type": "equity_primary",
            "from_group": "AMZN", "to_group": "LAB:ANTHROPIC", "edge_evidence": "amount",
            "_date": dt.date.fromisoformat(date), "tier": "A", "unit": "USD", "amount": amount,
            "elimination_status": "not_applicable",
            "_obs": {"amount": amount, "unit": "USD", "event_type": event, "amount_nature": nature,
                     "measurement_basis": basis, "stage": stage, "category_id": cat, "knowledge_date": date,
                     "group_id": group}}


def cap(key, ik, date, amount, group="LAB:ANTHROPIC"):
    return edge(key, ik, date, amount, group, "commitment_unexecuted", "commitment_cap", "signing", "signed",
                "uncalled_commitment")


def draw(key, ik, date, amount, group="LAB:ANTHROPIC"):
    return edge(key, ik, date, amount, group, "financing_cash", None, "funding", "drawn_or_paid")


CAPS = "contractual_outflows/commitment_cap/uncalled_commitment"


class StaleCaps(unittest.TestCase):
    """Un plafond suivi d'un tirage en numéraire du même instrument, vu de la même perspective, daté après lui et au
    plus tard à t, sort de sa ligne ; la ligne est partielle, ou indéterminée s'il ne lui reste rien."""

    def exposure(self, edges):
        p = C.Pair("AMZN", "LAB:ANTHROPIC")
        p.edges = edges
        q = dt.date(2026, 6, 30)
        ev = {("AMZN", "LAB:ANTHROPIC"): {"F": {"as_known": {"exposure_outstanding": {q: ("active", [])}}}}}
        out = C.counterparty_exposure({("AMZN", "LAB:ANTHROPIC"): p}, ev, {"AMZN": {"quarters": [{"end": q}]}},
                                      "2026-10-27", text_done=frozenset({"AMZN"}))
        return {c["breakdown_key"]: (c["value"], c["status"], c["nd_reason"], json.loads(c["flags"]).get("stale_caps"))
                for c in out}

    def test_plafond_tire_sort_de_sa_ligne(self):
        got = self.exposure([cap("a", "anthropic:x", "2025-01-31", "1400000000"),
                             cap("b", "anthropic:y", "2025-11-18", "15000000000"),
                             draw("c", "anthropic:x", "2025-06-30", "1400000000")])
        self.assertEqual(got[CAPS], (15000000000, "partial", "term_missing", ["edge:a"]))
        self.assertEqual(got["exposed_assets/cost/equity_investment"], (1400000000, "computed", None, None))

    def test_sans_autre_plafond_la_ligne_est_indeterminee(self):
        got = self.exposure([cap("a", "anthropic:x", "2025-01-31", "1400000000"),
                             draw("c", "anthropic:x", "2025-06-30", "1400000000")])
        self.assertEqual(got[CAPS], (None, "not_determinable", "term_missing", ["edge:a"]))

    def test_plafond_qui_reste(self):
        computed = (1400000000, "computed", None, None)
        # tirage vu de l'autre perspective, tirage antérieur au plafond, tirage après t, autre instrument
        for d in (draw("c", "anthropic:x", "2025-06-30", "1400000000", group="AMZN"),
                  draw("c", "anthropic:x", "2024-12-31", "1400000000"),
                  draw("c", "anthropic:x", "2026-07-15", "1400000000"),
                  draw("c", "anthropic:z", "2025-06-30", "1400000000")):
            self.assertEqual(self.exposure([cap("a", "anthropic:x", "2025-01-31", "1400000000"), d])[CAPS], computed)


# -- garde : aucune ligne chargée ne nomme une personne physique (D-0078, points 3 et 6) ----------------------------

FIELDS = ("quote", "note", "counterparty_name", "payer", "payee", "period_label", "trigger_description", "exhibit_title")
FIRST = """Aaron Adam Alan Albert Alex Alexander Alice Amanda Amit Amy Andrea Andrew Andy Angela Ann Anna Anne Anthony
Antonio Arthur Barbara Ben Benjamin Bill Bob Brad Bradley Brian Bruce Carl Carlos Carol Catherine Charles Charlie Chris
Christine Christopher Colin Craig Dan Daniel Dave David Dean Deborah Dennis Diana Diane Donald Doug Douglas Edward
Elizabeth Elon Emily Eric Erik Frank Fred Gary George Glenn Gordon Grace Greg Gregory Gwynne Harold Harry Heather Helen
Henry Hock Howard Ian Ira Jack Jacob James Jamie Jane Janet Jason Jay Jeff Jeffrey Jennifer Jensen Jeremy Jerry Jessica
Jim Joan Joe Joel John Jon Jonathan Jordan Jose Joseph Josh Joshua Juan Judith Julia Julie Justin Karen Kate Katherine
Keith Kelly Ken Kenneth Kevin Kim Kimbal Larry Laura Lauren Lawrence Lee Leon Linda Lisa Lori Louis Marc Margaret Maria
Marie Mark Martin Mary Masayoshi Matt Matthew Michael Michelle Mike Nancy Nathan Nazar Neil Nicholas Nick Nicole Pamela
Patricia Patrick Paul Peter Philip Rachel Rajeev Ralph Ray Raymond Rebecca Reid Richard Rick Robert Robin Roger Ronald
Rose Russell Ryan Safra Sam Samuel Sandra Sara Sarah Satya Scott Sean Sergey Sharon Stephen Steve Steven Sundar Susan
Syed Ted Thomas Tim Timothy Todd Tom Tony Victor Walter Wayne Wes William""".split()
SURNAMES = """Altman Amodei Ballmer Belardi Benioff Bezos Birchall Brin Catz Denholm Ellison Feldman Gracias Hoffman Huang
Intrator Jassy Masaitis McCabe Moussouris Musk Nadella Novak Pichai Prager Schmidt Shotwell Suleyman Sutardja Varjabedian
Yaccarino Zuckerberg""".split()
PATTERNS = [
    re.compile(r"\b(?:" + "|".join(FIRST) + r")\s+(?:[A-Z]\.\s+)?[A-Z][a-zA-Z'\-]+"),
    re.compile(r"\b(?:" + "|".join(SURNAMES) + r")\b"),
    re.compile(r"\b(?:Mr|Ms|Mrs|Dr|Messrs)\.\s+[A-Z][a-z]+|\bM\.\s+[A-Z][a-z]+|\bMme\s+[A-Z]|\bJudge\s+[A-Z]"),
    re.compile(r"\b[A-Z][a-z]{2,} [A-Z]\. [A-Z][a-z]{2,}\b"),
    re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)? (?:v\.|c\.) [A-Z]"),
    re.compile(r"(?:Family|Revocable|Living|Irrevocable) Trust"),
]
KEY_SURNAMES = re.compile(r"(?:^|[:_\-])(" + "|".join(s.lower() for s in SURNAMES) + r")(?:[_\-]|$)")
# noms de sociétés, de fondations, de lieux, de projets et tournures admis (D-0078, point 6), retirés avant le relevé
ALLOWED = sorted("""Carl Zeiss|Ben Milam|Frank Funds|BCH San Jose LLC|Jane Street|Jordan HPC|Sharon AI|John Wiley|Apollo Rose
|Lawrence Investments|Grace Blackwell|Louis Energy|USMIO Charlie LLC|Angela Bridge|Martin Merger Sub|Raymond James|Ernst & Young LLP
|Raymond Chabot|James River|George Town|Howard Street|Dave Inc|Grace Period|Saint Lawrence|Bradley Woods|Trade Mark Licence
|B. Riley|Term Loan A. The|Company A. Intel|Texas v. Meta|Brandt Dr. S.|Green Earth Liang's Inc.|Green Earth Liang
|The Jen-Hsun and Lori Huang Foundation|Huang Foundation|McCabe Petroleum|Ellison Institute|Ellison Medical|Musk Industries
|Harbor Gates|Kohlberg Kravis Roberts|Kravis Roberts|Hong Kong|Kleiner Perkins|Janus Henderson|The Washington Post""".replace("\n", "").split("|"),
                 key=len, reverse=True)


def person_hits(df):
    out = []
    for f in FIELDS:
        for k, t in zip(df["obs_key"], df[f]):
            if not isinstance(t, str) or not t:
                continue
            for a in ALLOWED:
                t = t.replace(a, " ")
            out += [(k, f, m.group(0)) for rx in PATTERNS for m in rx.finditer(t)]
    out += [(k, "instrument_key", ik) for k, ik in zip(df["obs_key"], df["instrument_key"])
            if isinstance(ik, str) and KEY_SURNAMES.search(ik.lower())]
    return out


class NoNaturalPerson(unittest.TestCase):
    def test_le_releve_trouve_les_motifs(self):
        df = pd.DataFrame([{"obs_key": "k", "instrument_key": "wulf:prager_exchange_warrants_2023",
                            **{f: None for f in FIELDS},
                            "note": "contrat avec James R. Belardi ; Moussouris v. Microsoft ; M. Hao ; Booth Family Trust",
                            "quote": "Robin L. Washington will serve", "payer": "Green Earth Liang's Inc."}])
        got = {m for _, _, m in person_hits(df)}
        self.assertTrue({"James R. Belardi", "Moussouris v. M", "M. Hao", "Family Trust", "Robin L. Washington",
                         "wulf:prager_exchange_warrants_2023"} <= got)
        self.assertFalse(any("Liang" in m for m in got))

    def test_aucune_ligne_chargee_ne_nomme_une_personne(self):
        p = config.TABLES / "observations.parquet"
        if not p.exists():
            self.skipTest("tables absentes")
        df = pd.read_parquet(p, columns=["obs_key", "instrument_key", *FIELDS])
        hits = person_hits(df)
        self.assertEqual(hits[:20], [], f"{len(hits)} mention(s) d'une personne physique")


class CorrectionPasses(unittest.TestCase):
    """Point 7 : un bloc lu avant l'ouverture du bloc text et repris par une passe de correction reste hors de son
    rendement."""

    def test_bloc_lu_avant_l_ouverture_hors_du_rendement(self):
        from tests.test_render_speed import CK, P1, base
        con = base()
        self.assertEqual(set(R.edges_citing(con, P1)), {"edge:e1", "edge:e2"})
        self.assertEqual(R.edges_citing(con, P1, [CK]), [])
        old = config.OBS_DIR
        with tempfile.TemporaryDirectory() as d:
            config.OBS_DIR = pathlib.Path(d)
            try:
                f = config.OBS_DIR / f"{CK}.jsonl"
                f.write_text(json.dumps({"pass_id": "2026-10-01T00:00:00Z"}) + "\n" + json.dumps({"pass_id": P1}) + "\n")
                self.assertEqual(R.corrected_outside(con, {P1}, "2026-10-07T16:30:00Z"), [CK])
                # première passe après l'ouverture : le bloc reste dans le rendement
                f.write_text(json.dumps({"pass_id": "2026-10-08T00:00:00Z"}) + "\n" + json.dumps({"pass_id": P1}) + "\n")
                self.assertEqual(R.corrected_outside(con, {P1}, "2026-10-07T16:30:00Z"), [])
                self.assertEqual(R.corrected_outside(con, set(), "2026-10-07T16:30:00Z"), [])
            finally:
                config.OBS_DIR = old


if __name__ == "__main__":
    unittest.main()
