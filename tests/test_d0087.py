"""D-0087 : gardes de lecture à la soumission (G1 à G4), contrôle d'avant réassemblage (`reader check`), ouverture
d'une passe (`reader open-pass`), et nettoyage (diff d'une annexe, adresse de contact masquée et hors de l'index).

Lancement : python3 -m unittest tests.test_d0087 -v
"""
import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from decimal import Decimal

from pipeline import config, guards, reader

TEXT = ("The Company borrowed $2.2 billion under the Credit Agreement with Example Bank, N.A. in May 2026. "
        "Interest expense on the loan was $18.6 million for the quarter. Mr. Smith signed the agreement.")
BLOCK = {"content_key": "k1", "block_kind": "debt_note", "group_id": "TEST", "cik": "1", "accession": "a-1",
         "document": "d.htm", "form": "10-Q", "knowledge_date": "2026-11-10", "signal_class": 3, "sort_key": "0",
         "text": TEXT, "candidate_facts": []}


def obs(**kw):
    return {"kind": "observation", "quote": "The Company borrowed $2.2 billion under the Credit Agreement", **kw}


def amount(value, quote=None, **kw):
    line = obs(**{"amount": value, "unit": "USD", "currency": "USD", "amount_origin": "narrative_only",
                  "amount_qualifier": "exact", **kw})
    if quote is not None:
        line["quote"] = quote
    return line


@contextlib.contextmanager
def workspace(blocks=(BLOCK,), run=None):
    """Lecteur branché sur un répertoire temporaire : catalogue, observations, état et passe, sans db/ ni work/."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "blocks.jsonl").write_text("".join(json.dumps(b) + "\n" for b in blocks), encoding="utf-8")
        saved = {(m, k): getattr(m, k) for m, k in (
            (reader, "CATALOG"), (reader, "CATALOG_EXT"), (reader, "CATALOG_DISC"), (reader, "CATALOG_NF"),
            (reader, "CATALOG_MT"), (reader, "CATALOG_6K"), (reader, "CATALOG_SB"), (reader, "STATE"), (reader, "RUN"),
            (reader, "LIST"), (config, "OBS_DIR"))}
        try:
            reader.CATALOG = d / "blocks.jsonl"
            for k in ("CATALOG_EXT", "CATALOG_DISC", "CATALOG_NF", "CATALOG_MT", "CATALOG_6K", "CATALOG_SB"):
                setattr(reader, k, d / f"absent_{k}.jsonl")
            reader.STATE, reader.RUN, reader.LIST = d / "tmp" / "reading_state.json", d / "tmp" / "run.json", None
            config.OBS_DIR = d / "obs"
            if run:
                reader.RUN.parent.mkdir(parents=True)
                reader.RUN.write_text(json.dumps({"as_of": config.as_of(), "pass_id": run}))
            yield d
        finally:
            for (m, k), v in saved.items():
                setattr(m, k, v)


def submit(d, lines, **kw):
    """Soumet des lignes au bloc k1 : (code de retour, sortie, lignes écrites)."""
    f = d / "lines.jsonl"
    f.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines), encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = reader.cmd_submit("k1", str(f), **kw)
    p = config.OBS_DIR / "k1.jsonl"
    written = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else None
    return rc, out.getvalue(), written


class FinancingPrice(unittest.TestCase):
    """G1 : intérêts et commissions ne portent pas la famille `financing`."""

    def test_interets_et_commissions_sous_financing_refuses(self):
        for nature in ("interest", "fee"):
            e = reader.schema_errors(obs(family="financing", edge_type="loan_or_facility", amount_nature=nature))
            self.assertTrue(any("prix d'un financement" in x for x in e), nature)

    def test_ce_qui_reste_permis(self):
        for line in (obs(amount_nature="interest"),                                   # sans famille : le sens de la trésorerie
                     obs(family="commercial", edge_type="purchase", amount_nature="fee"),      # commission d'un service acheté
                     obs(family="financing", edge_type="loan_or_facility", amount_nature="financing_cash",
                         event_type="repayment"),                                     # clôture (D-0069, point 5)
                     {"kind": "abstention", "abstention_reason": "no_amount"}):
            self.assertEqual(reader.schema_errors(line), [], line)


class NaturalPersons(unittest.TestCase):
    """G2 : le relevé de D-0078 à la soumission ; rien ne s'écrit, pas même parmi les rejets."""

    def test_champs_du_releve(self):
        self.assertEqual(guards.person_mentions({"ultimate_obligor": "Mr. Smith"}), [("ultimate_obligor", "Mr. Smith")])
        self.assertEqual(guards.person_mentions({"party_role": "guarantor (John Q. Public)"})[0][0], "party_role")
        self.assertEqual(guards.person_mentions({"instrument_key": "tsla:musk_loan_2026"}),
                         [("instrument_key", "tsla:musk_loan_2026")])
        self.assertEqual(guards.person_mentions({"payer": "Charles Schwab & Co., Inc.", "note": None, "quote": ""}), [])

    def test_refus_meme_avec_final(self):
        bad = obs(note="signé par Mr. Smith")
        for kw in ({}, {"final": True}, {"confirm": True}):
            with workspace() as d:
                rc, out, written = submit(d, [obs(), bad], **kw)
                self.assertEqual(rc, 2, kw)
                self.assertIn("personne physique", out)
                self.assertIn("ligne 2", out)
                self.assertIsNone(written)
                self.assertFalse((config.OBS_DIR / "k1.rejected.jsonl").exists())


class AmountInQuote(unittest.TestCase):
    """G3 : un montant narratif se lit dans sa citation, sinon c'est une alerte."""

    def test_valeurs_lues_dans_une_citation(self):
        v = guards.quote_values("a facility of $3.5 billion, of which $500M drawn and US$1.5bn undrawn")
        self.assertTrue({Decimal("3500000000"), Decimal("500000000"), Decimal("1500000000")} <= v)
        self.assertNotIn(Decimal("3.5"), v)                       # un nombre qui porte son échelle ne vaut qu'à elle
        self.assertIn(Decimal("0.62"), guards.quote_values("accounted for 62% of our revenue"))
        self.assertIn(Decimal("8837748000000"), guards.quote_values("(as of December 31, 2024: W8,837,748 million)"))
        # nombre nu d'un tableau : à l'unité, ou à l'échelle que le tableau écrit hors de la citation
        self.assertTrue({Decimal("1234"), Decimal("1234000000")} <= guards.quote_values("Total debt | 1,234 | (56)"))
        self.assertNotIn(Decimal("234"), guards.quote_values("1,234"))

    def test_alertes(self):
        self.assertEqual(guards.amount_alerts(amount("2200000000")), [])
        self.assertEqual(len(guards.amount_alerts(amount("2600000000"))), 1)          # D-0084, point 14
        self.assertEqual(guards.amount_alerts(amount("2600000000", amount_origin="tagged_reference")), [])
        self.assertEqual(guards.amount_alerts(amount("0", quote="there were no borrowings outstanding")), [])
        self.assertEqual(guards.amount_alerts(amount("-18600000", quote="interest of $(18.6) million")), [])
        self.assertEqual(guards.amount_alerts({"kind": "abstention", "amount": "5"}), [])
        rng = amount(None, quote="between $1.0 billion and $1.5 billion", amount_lower="1000000000",
                     amount_upper="1600000000")
        self.assertEqual([a.split()[0] for a in guards.amount_alerts(rng)], ["amount_upper"])

    def test_une_alerte_bloque_puis_se_confirme(self):
        wrong = amount("2600000000")
        with workspace() as d:
            rc, out, written = submit(d, [wrong])
            self.assertEqual(rc, 1)
            self.assertIn("ALERTES DE LECTURE", out)
            self.assertIsNone(written)
            rc, out, written = submit(d, [wrong], confirm=True)
            self.assertEqual((rc, len(written)), (0, 1))
        with workspace() as d:                                    # --final écrit aussi une ligne en alerte
            self.assertEqual(submit(d, [wrong], final=True)[0], 0)
        with workspace() as d:                                    # une erreur bloque toujours, alerte confirmée ou non
            rc, out, written = submit(d, [obs(quote="phrase absente du bloc")], confirm=True)
            self.assertEqual(rc, 1)
            self.assertIn("citation introuvable", out)
            self.assertIsNone(written)

    def test_ligne_sans_alerte_ecrite_d_emblee(self):
        with workspace() as d:
            rc, out, written = submit(d, [amount("2200000000")])
            self.assertEqual((rc, len(written)), (0, 1))
            self.assertEqual(written[0]["as_of"], config.as_of())


class Duplicates(unittest.TestCase):
    """G4 : une ligne déjà écrite dans la passe ne s'écrit pas deux fois (D-0085, point 11)."""

    def test_double_soumission(self):
        lines = [amount("2200000000"), obs(signal="pledged_assets", signal_present=True)]
        with workspace(run="2026-11-23T10:00:00Z") as d:
            self.assertEqual(len(submit(d, lines)[2]), 2)
            rc, out, written = submit(d, lines)
            self.assertEqual((rc, len(written)), (0, 2))
            self.assertIn("2 ligne(s) déjà écrite(s)", out)
            # un morceau suivant du même bloc s'ajoute ; une ligne répétée dans la soumission ne compte qu'une fois
            more = obs(quote="Interest expense on the loan was $18.6 million for the quarter", amount_nature="interest")
            self.assertEqual(len(submit(d, [more, more])[2]), 3)

    def test_une_autre_passe_reecrit_la_ligne(self):
        with workspace(run="2026-11-23T10:00:00Z") as d:
            submit(d, [amount("2200000000")])
            reader.RUN.write_text(json.dumps({"as_of": config.as_of(), "pass_id": "2026-11-23T12:00:00Z"}))
            self.assertEqual(len(submit(d, [amount("2200000000")])[2]), 2)


class CheckBeforeAssembly(unittest.TestCase):
    """`reader check` : les gardes sur la passe chargée des blocs de l'as_of courant."""

    def run_check(self, files, keys=None):
        with workspace() as d:
            config.OBS_DIR.mkdir(parents=True)
            for k, lines in files.items():
                (config.OBS_DIR / f"{k}.jsonl").write_text("".join(json.dumps(l) + "\n" for l in lines), encoding="utf-8")
            if keys is not None:
                (d / "liste.txt").write_text("\n".join(keys) + "\n")
                reader.LIST = str(d / "liste.txt")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = reader.cmd_check()
            return rc, out.getvalue()

    def test_erreurs_alertes_et_passes(self):
        a, p = config.as_of(), "2026-11-23T10:00:00Z"
        cur = {"as_of": a, "pass_id": p}
        files = {
            "aa": [{**cur, **amount("2200000000")}],
            "bb": [{**cur, **obs(family="financing", edge_type="loan_or_facility", amount_nature="interest")},
                   {**cur, **amount("2600000000")}],
            "cc": [{**cur, **obs()}, {**cur, **obs()}],
            # passe remplacée et exécution antérieure : hors du contrôle
            "dd": [{"as_of": a, "pass_id": "2026-11-01T00:00:00Z", **obs(note="Mr. Smith")}, {**cur, **obs()}],
            "ee": [{"as_of": "2026-10-07", "pass_id": "2026-10-07T16:30:00Z", **amount("2600000000")}],
        }
        rc, out = self.run_check(files)
        self.assertEqual(rc, 1)
        self.assertIn("contrôlé : 6 ligne(s)", out)
        self.assertIn("dans 4 bloc(s) ; 2 erreur(s), 1 alerte(s)", out)
        self.assertIn("ERREUR bb ligne 1", out)
        self.assertIn("ALERTE bb ligne 2", out)
        self.assertIn("ERREUR cc ligne 2 : ligne en double", out)
        rc, out = self.run_check(files, keys=["aa", "dd", "absent"])
        self.assertEqual(rc, 0)
        self.assertIn("contrôlé : 2 ligne(s)", out)


class OpenPass(unittest.TestCase):
    def open(self, **kw):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = reader.cmd_open_pass(**kw)
        return rc, out.getvalue()

    def test_passe_de_l_execution(self):
        with workspace():
            rc, out = self.open()
            run = json.loads(reader.RUN.read_text())
            self.assertEqual((rc, run["as_of"]), (0, config.as_of()))
            self.assertRegex(run["pass_id"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertEqual(reader._run_info(), run)
            self.assertEqual(self.open()[0], 0)                               # déjà ouverte : gardée
            self.assertEqual(json.loads(reader.RUN.read_text()), run)
            self.assertEqual(self.open(pass_id="2026-11-23T18:00:00Z")[0], 2)  # une autre au même as_of : refus
            self.assertEqual(self.open(pass_id="23 novembre")[0], 2)
            reader.RUN.write_text(json.dumps({"as_of": "2026-10-07", "pass_id": "2026-10-07T16:30:00Z"}))
            self.assertEqual(self.open(pass_id="2026-11-23T18:00:00Z")[0], 0)  # passe d'une autre exécution : remplacée
            self.assertEqual(json.loads(reader.RUN.read_text())["pass_id"], "2026-11-23T18:00:00Z")

    def test_passe_d_une_liste(self):
        with workspace() as d:
            reader.LIST = str(d / "repass_x.txt")
            self.assertEqual(self.open(pass_id="2026-11-23T18:00:00Z")[0], 0)
            self.assertFalse(reader.RUN.exists())
            run = json.loads((reader.RUN.parent / "run_repass_x.json").read_text())
            self.assertEqual(run, {"as_of": config.as_of(), "pass_id": "2026-11-23T18:00:00Z"})
            self.assertEqual(reader._run_info(), run)


class CleanUp(unittest.TestCase):
    """Nettoyage de D-0087 : diff d'une annexe réduit à sa section, adresse de contact masquée et hors de l'index."""

    def test_diff_d_une_annexe_sur_sa_seule_section(self):
        from pipeline import render
        old = {"annex_f": {"events": {"F1": {"observable": "a"}}}, "confirmed_entities": [{"name": "X"}]}
        new = {"annex_f": {"events": {"F1": {"observable": "a"}, "F11": {"observable": "b"}}},
               "confirmed_entities": [{"name": "X"}, {"name": "Y"}], "annex_e": {"ids": [1]}}
        d = render.annex_diff("annex_f", old, new)
        self.assertIn("+    F11:", d)
        self.assertNotIn("confirmed_entities", d)
        self.assertNotIn("name: Y", d)
        self.assertEqual(render.annex_diff("annex_f", new, new), "")
        self.assertIn("+annex_e:", render.annex_diff("annex_e", old, new))

    def test_masquage_par_la_variable_ou_le_fichier(self):
        import os
        cfg = {"user_agent": {"value_sources": ["env:D0087_TEST_UA", "file:secrets/absent_d0087.txt"]}}
        self.assertEqual(config.contact_addresses(cfg), [])
        self.assertEqual(config.mask_contact("écrire à a@b.example", cfg), "écrire à a@b.example")
        os.environ["D0087_TEST_UA"] = "a@b.example projet_de_test"
        try:
            self.assertEqual(config.contact_addresses(cfg), ["a@b.example"])
            self.assertEqual(config.mask_contact("écrire à a@b.example", cfg), "écrire à <adresse masquée>")
        finally:
            del os.environ["D0087_TEST_UA"]

    def test_l_adresse_de_contact_n_est_pas_dans_l_index(self):
        """Avant chaque commit (le crochet lance `make check`) : aucun fichier de l'index ne porte l'adresse de contact
        du User-Agent. Le message ne cite que les fichiers, jamais l'adresse."""
        import subprocess
        addrs = config.contact_addresses()
        if not addrs:
            self.skipTest("User-Agent absent : aucune adresse à chercher")
        for a in addrs:
            r = subprocess.run(["git", "grep", "--cached", "-l", "-F", "-e", a], capture_output=True, text=True,
                               cwd=config.ROOT)
            if r.returncode not in (0, 1):
                self.skipTest("pas un dépôt git")
            self.assertEqual(r.stdout.split(), [], "l'adresse de contact est dans des fichiers de l'index")


if __name__ == "__main__":
    unittest.main()
