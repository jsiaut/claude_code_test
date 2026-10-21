"""Bloc montages (D-0046, D-0049) : termes qualifiants hors du nom du déposant, fenêtres de paragraphes.

Lancement : python3 -m unittest discover -s tests -t .
"""
import contextlib
import io
import json
import pathlib
import tempfile
import unittest

from pipeline import discovery as D
from pipeline import montages as M

S = M.specs()


def _pdf(pages):
    """PDF minimal en Helvetica : une ligne de texte par élément de chaque page, une chaîne vide saute une ligne."""
    objs, kids = ["<< /Type /Catalog /Pages 2 0 R >>", None], []
    for lines in pages:
        body = "BT /F1 11 Tf 72 720 Td 14 TL " + " ".join(
            "T* " if not x else "(" + x.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") ' "
            for x in lines) + "ET"
        objs.append(f"<< /Length {len(body)} >>\nstream\n{body}\nendstream")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {len(objs)} 0 R "
                    "/Resources << /Font << /F1 FONT 0 R >> >> >>")
        kids.append(len(objs))
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objs = [o.replace("FONT", str(len(objs))) if o else o for o in objs]
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>"
    out, offs = io.BytesIO(), []
    out.write(b"%PDF-1.4\n")
    for i, o in enumerate(objs, 1):
        offs.append(out.tell())
        out.write(f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1"))
    x = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for o in offs:
        out.write(f"{o:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode())
    return out.getvalue()


class Qualify(unittest.TestCase):
    def test_own_name_never_qualifies(self):
        sp = S["meta_hyperion"]
        meta, owl, other = (M.qualify_rx("Meta Platforms, Inc.", sp), M.qualify_rx("Blue Owl Real Estate Net Lease Trust", sp),
                            M.qualify_rx("Boeing Co", sp))
        self.assertIsNone(meta.search("Meta reported revenue growth."))
        self.assertTrue(meta.search("an affiliate of funds managed by Blue Owl Capital, Inc."))
        self.assertIsNone(owl.search("Blue Owl Capital Inc. manages the fund."))
        self.assertTrue(owl.search("a campus leased to Meta Platforms, Inc."))
        self.assertTrue(other.search("Beignet Investor LLC 6.581% notes"))
        self.assertIsNone(other.search("Hyperion Refinance S.a r.l (dba Howden Group)"))   # Hyperion seul : ambigu
        self.assertIsNone(other.search("metadata and Metaverse"))                           # mot entier, majuscule

    def test_apollo_and_athene_do_not_qualify_each_other(self):
        sp = S["athene_whco"]
        ath, avgo = M.qualify_rx("Athene Holding Ltd.", sp), M.qualify_rx("Broadcom Inc.", sp)
        self.assertIsNone(ath.search("Athene is a subsidiary of Apollo Global Management."))
        self.assertTrue(ath.search("a capital solution agreement with Broadcom Inc."))
        self.assertTrue(ath.search("WHCO has a purchase obligation"))
        self.assertIsNone(avgo.search("Broadcom reported revenue."))
        self.assertTrue(avgo.search("funds managed by Apollo"))

    def test_helios_only_in_galaxy_or_coreweave(self):
        sp = S["galaxy_helios"]
        glxy, crwv, other = (M.qualify_rx("Galaxy Digital Inc.", sp), M.qualify_rx("CoreWeave, Inc.", sp),
                             M.qualify_rx("Helios Technologies, Inc.", sp))
        self.assertTrue(glxy.search("the Helios data center campus"))
        self.assertIsNone(glxy.search("Galaxy reported trading revenue."))
        self.assertTrue(crwv.search("our lease at Helios"))
        self.assertIsNone(crwv.search("CoreWeave reported revenue."))
        self.assertIsNone(other.search("Helios Technologies reported revenue."))
        self.assertTrue(other.search("leased to CoreWeave"))


class Windows(unittest.TestCase):
    def test_two_paragraphs_each_side_merged(self):
        paras = [f"p{i}" for i in range(12)]
        paras[3] = "Blue Owl"
        paras[6] = "Blue Owl again"
        paras[11] = "Beignet"
        rx = M.qualify_rx("Meta Platforms, Inc.", S["meta_hyperion"])
        self.assertEqual(M.windows(paras, rx), [[1, 12]])   # fenêtres contiguës fondues


class GalaxyAmendment(unittest.TestCase):
    """D-0049, point 11 : pièces écartées, ordre des classes, plus récent d'abord."""

    @staticmethod
    def _d(filer, form, ft, f, date):
        return {"filer": filer, "form": form, "file_type": ft, "file": f, "file_date": date, "adsh": "x"}

    def test_exclusions(self):
        sp, d = S["galaxy_helios"], self._d
        self.assertIsNotNone(M._excluded(d("Galaxy Digital Inc.", "424B3", "424B3", "a.htm", "2026-01-01"), sp))
        self.assertIsNotNone(M._excluded(d("Galaxy Digital Inc.", "8-K", "EX-99.2", "exhibit992-q12026overvie.htm", "2026-04-28"), sp))
        self.assertIsNotNone(M._excluded(d("Galaxy Digital Inc.", "8-K", "EX-99.1", "glxy-2026331xpressrelease.htm", "2026-04-28"), sp))
        self.assertIsNone(M._excluded(d("Galaxy Digital Inc.", "8-K", "EX-4.1", "closing8-kxex41indenture.htm", "2026-07-28"), sp))
        self.assertIsNone(M._excluded(d("CoreWeave, Inc.", "424B4", "424B4", "x.htm", "2025-03-31"), sp))

    def test_order(self):
        sp, d = S["galaxy_helios"], self._d
        docs = [d("Galaxy Digital Inc.", "10-Q", "10-Q", "q1", "2026-05-08"), d("Galaxy Digital Inc.", "10-Q", "10-Q", "q2", "2026-08-10"),
                d("Galaxy Digital Inc.", "8-K", "EX-4.1", "ind", "2026-07-28"), d("MSD Investment Corp.", "10-Q", "10-Q", "m", "2026-05-14")]
        self.assertEqual([x["file"] for x in sorted(docs, key=lambda x: M._order_key(x, 0, sp))], ["m", "ind", "q2", "q1"])

    def test_first_montages_keep_date_order(self):
        for mid in ("meta_hyperion", "athene_whco"):
            a = {"filer": "X", "form": "8-K", "file": "a", "file_date": "2025-01-01", "adsh": "1"}
            self.assertLess(M._order_key(a, 0, S[mid]), M._order_key(dict(a, file_date="2026-01-01"), 0, S[mid]))


class CounterpartyMembership(unittest.TestCase):
    """D-0049, point 13 : filiale d'une contrepartie rattachée par extrait au groupe de la contrepartie."""

    def test_vehicle_joins_counterparty_group_only_by_extract(self):
        from pipeline import entities as E
        cfg = {"labs": [], "confirmed_entities": [
            {"name": "Galaxy Helios I LLC", "group": "CP:galaxy digital inc", "treatment": "consolidated_subsidiary",
             "valid_from": "none", "decision": "D-0049", "block": "x", "accession": "y",
             "quote": "Galaxy Helios I LLC, a wholly owned subsidiary of GDH LP"}]}
        rows, reg = E.build({"meta": {}}, cfg, {"Galaxy Helios LLC": False, "Galaxy Helios I LLC": False})
        self.assertEqual(E.resolve(reg, "Galaxy Helios I LLC", "2026-06-30")[1], "CP:galaxy digital inc")
        self.assertEqual(E.resolve(reg, "Galaxy Helios LLC", "2026-06-30")[1], "CP:galaxy helios llc")   # pas de fusion
        kinds = {r["name"]: r["group_kind"] for r in rows if r["record_kind"] == "entity"}
        self.assertEqual(kinds["Galaxy Helios I LLC"], "counterparty_group")



class FilerBecomesGroup(unittest.TestCase):
    """D-0053, point 7 : lignes d'un montage lues dans les dépôts d'un déposant devenu groupe suivi."""

    def test_montage_lines_follow_the_filer_group(self):
        from pipeline.load import line_group
        as_group = {"1859392": "GLXY"}
        b = {"block_kind": "montage_text", "group_id": "CP:galaxy digital inc", "cik": "0001859392"}
        self.assertEqual(line_group(b, as_group, {}), "GLXY")
        # dépôt d'un autre déposant (CoreWeave lu pour le même montage) : le groupe du bloc reste
        self.assertIsNone(line_group(dict(b, cik="0001769628"), as_group, {}))
        # bloc d'un groupe suivi : inchangé
        self.assertIsNone(line_group(dict(b, group_id="CRWV"), as_group, {}))

    def test_attached_filer(self):
        """D-0055, point 8 : les dépôts d'Athene Holding Ltd., rattachée à APO au 1er janvier 2022 par extrait,
        vont au groupe après cette date ; avant, le bloc garde son groupe."""
        from pipeline.load import line_group
        att = {"1527469": ("APO", "2022-01-01")}
        b = {"block_kind": "montage_text", "group_id": "CP:athene holding ltd", "cik": "0001527469",
             "filing_date": "2026-08-07"}
        self.assertEqual(line_group(b, {}, {}, att), "APO")
        self.assertIsNone(line_group(dict(b, filing_date="2021-11-09"), {}, {}, att))
        self.assertIsNone(line_group(b, {}, {}))

    def test_discovery_lines(self):
        from pipeline.load import line_group
        b = {"block_kind": "discovery_note", "group_id": "X", "cik": "0000000042"}
        self.assertEqual(line_group(b, {"42": "HUT"}, {}), "HUT")
        self.assertEqual(line_group(b, {}, {"42": "Acme Corp."}), "CP:acme corp")


if __name__ == "__main__":
    unittest.main()


class CorpusSoftBank(unittest.TestCase):
    """D-0058, point 3 : montage de corpus, termes, facteurs de risque, blocs déjà lus, plus récent d'abord."""

    def test_terms(self):
        rx = M.qualify_rx("NVIDIA CORP", S["softbank_corpus"])
        for s in ("SoftBank Group Corp.", "Softbank", "Arm Holdings plc", "ARM Limited", "SVF II Finco Cayman L.P.",
                  "Ampere Computing Holdings LLC", "affiliates of SB Energy", "the Stargate project"):
            self.assertTrue(rx.search(s), s)
        for s in ("the NVIDIA Ampere architecture", "Arm-based CPUs", "SVF", "SVF III", "a Vision Fund", "SBG", "stargate"):
            self.assertIsNone(rx.search(s), s)

    def test_risk_factors_10k(self):
        paras = ["Table of Contents", "Item 1A. | Risk Factors | 12", "Item 1. Business", "SoftBank is a customer.",
                 "Item 1A. Risk Factors", "Risks Related to Our Business", "We depend on SoftBank.", "Item 1B. Unresolved Staff Comments",
                 "None.", "Item 7. Management's Discussion", "SoftBank paid $10 million."]
        self.assertEqual(M.risk_factor_span(paras), (4, 7))

    def test_risk_factors_prospectus_and_toc(self):
        paras = ["RISK FACTORS", "CAUTIONARY NOTE REGARDING FORWARD-LOOKING STATEMENTS", "PROSPECTUS SUMMARY",
                 "RISK FACTORS", "Investing in our stock involves risk.", "SoftBank controls us.",
                 "SPECIAL NOTE REGARDING FORWARD-LOOKING STATEMENTS", "USE OF PROCEEDS"]
        self.assertEqual(M.risk_factor_span(paras), (3, 6))       # la plus longue : la table des matières est écartée
        self.assertIsNone(M.risk_factor_span(["Summary of Risk Factors", "SoftBank"]))

    def test_covered(self):
        texts = [M._norm("Note 1\nOn November 25, 2025,   SoftBank Group Corp. acquired\nall of the equity interests of Ampere.")]
        self.assertTrue(M.covered("On November 25, 2025, SoftBank Group Corp. acquired all of the equity interests of Ampere.", texts))
        self.assertFalse(M.covered("SoftBank Group Corp. acquired Graphcore.", texts))

    def test_recent_first(self):
        sp = S["softbank_corpus"]
        a = {"filer": "X", "form": "10-Q", "file": "a", "file_date": "2025-01-01", "adsh": "1"}
        self.assertLess(M._order_key(dict(a, file_date="2026-03-11"), 0, sp), M._order_key(a, 0, sp))


class Stargate(unittest.TestCase):
    """D-0058, points 7 et 20 : « Stargate » en casse exacte, hors des pièces d'un déposant à son nom ; Form D
    comptés, non tirés ; préparation d'un seul montage."""

    def test_terms(self):
        sp = S["stargate"]
        rx = M.qualify_rx("Oracle Corporation", sp)
        self.assertTrue(rx.search("the Stargate project with OpenAI and SoftBank"))
        self.assertIsNone(rx.search("a stargate-themed fund"))
        self.assertIsNone(rx.search("STARGATE"))
        self.assertIsNone(M.qualify_rx("Blue Owl GP Stakes Stargate LP", sp))
        self.assertEqual(sp["count_only_forms"], ["D", "D/A"])
        self.assertEqual((sp["cap"], sp["order"]), (60, "recent_first"))

    def test_prepare_one_montage_keeps_the_others(self):
        old = [{"content_key": "a", "montage": "meta_hyperion"}, {"content_key": "b", "montage": "stargate"},
               {"content_key": "c", "montage": "softbank_corpus"}]
        new = [{"content_key": "d", "montage": "stargate"}]
        self.assertEqual([b["content_key"] for b in M.merge_catalog(old, new, "stargate")], ["a", "c", "d"])


class CorpusLabs(unittest.TestCase):
    """D-0059, point 3 : « OpenAI » et « Anthropic » en mots entiers et en casse exacte ; « Anthropic Capital »,
    gérant homonyme, ne qualifie pas ; « Open AI », « ChatGPT », « Claude » et « Stargate » sont seulement comptés."""

    def test_terms(self):
        sp = S["labs_corpus"]
        rx = M.qualify_rx("AMAZON COM INC", sp)
        for s in ("our investment in Anthropic, PBC", "OpenAI OpCo, LLC", "OpenAI's compute commitments", "ANTHROPIC PBC",
                  "OPENAI GROUP PBC", "Anthropic and OpenAI"):
            self.assertTrue(rx.search(s), s)
        for s in ("Anthropic Capital Partners, LLC", "ANTHROPIC CAPITAL MANAGEMENT", "an anthropic approach", "openai",
                  "an Open AI ecosystem", "ChatGPT Enterprise", "Claude models", "the Stargate project"):
            self.assertIsNone(rx.search(s), s)
        self.assertEqual((sp["source"], sp["cap"], sp["order"]), ("corpus", 300, "recent_first"))
        self.assertTrue(sp["skip_read"] and sp["skip_risk_factors"] and sp["dedupe"])
        noted = M.noted_rx(sp)
        self.assertEqual(sorted(set(noted.findall("ChatGPT, Claude, Open AI and the Stargate project"))),
                         ["ChatGPT", "Claude", "Open AI", "Stargate"])

    def test_lab_entities(self):
        """D-0059, point 5 : une entité de laboratoire n'entre que par un extrait cité (règle A ou B), au traitement
        indéterminé sans les mots de D-0050 ; une désignation (« an affiliate of OpenAI ») reste en attente (D-0032, point 5)."""
        from pipeline import config
        from pipeline import entities as E
        cfg = config.load()
        d59 = [c for c in cfg["confirmed_entities"] if c.get("decision") == "D-0059"]
        self.assertTrue(d59)
        for c in d59:
            self.assertIn(c["group"], ("LAB:OPENAI", "LAB:ANTHROPIC"))
            self.assertRegex(c["block"], r"^[0-9a-f]{64}$")
            self.assertRegex(c["accession"], r"^\d{10}-\d{2}-\d{6}$")
            self.assertTrue(c["quote"].strip() and c["membership_note"].strip())
            self.assertEqual(c["treatment"], "undetermined")
        names = ["OpenAI Global, LLC", "OpenAI OpCo LLC", "Anthropic, PBC", "an affiliate of OpenAI"]
        _, reg = E.build({"meta": {}}, cfg, {n: False for n in names})
        g = lambda n: E.resolve(reg, n, "2026-06-30")[1]
        self.assertEqual(g("OpenAI Global, LLC"), "LAB:OPENAI")
        self.assertEqual(g("OpenAI OpCo LLC"), "LAB:OPENAI")
        self.assertEqual(g("Anthropic, PBC"), "LAB:ANTHROPIC")
        self.assertIsNone(g("an affiliate of OpenAI"))

    def test_names_resolved_at_integration(self):
        """D-0059, intégration : noms encore en attente après le premier réassemblage, rattachés par extrait ; sans extrait
        qui le définit, « Uber » reste en attente."""
        from pipeline import config
        from pipeline import entities as E
        cfg = config.load()
        names = ["Fluidstack", "Fluidstack Ltd.", "Sanmina", "Sanmina Corporation", "Uber"]
        _, reg = E.build({"meta": {}}, cfg, {n: False for n in names})
        g = lambda n: E.resolve(reg, n, "2026-06-30")[1]
        self.assertEqual(g("Fluidstack"), g("Fluidstack Ltd."))
        self.assertEqual(g("Fluidstack"), "CP:fluidstack ltd")
        self.assertEqual(g("Sanmina"), "CP:sanmina corp")
        self.assertIsNone(g("Uber"))


class AnthropicChain(unittest.TestCase):
    """D-0064, point 3 : « Fluidstack » hors des pièces d'un déposant à son nom, « Anthropic » sans le gérant
    homonyme ; 8-K et 8-K/A, pièces comprises ; classes de lecture, puis du plus récent au plus ancien."""

    def test_terms(self):
        sp = S["anthropic_chain"]
        rx = M.qualify_rx("TeraWulf Inc.", sp)
        for s in ("a lease with Fluidstack", "FluidStack Ltd.", "FLUIDSTACK USA I INC.", "Anthropic, PBC", "ANTHROPIC PBC"):
            self.assertTrue(rx.search(s), s)
        for s in ("Anthropic Capital Partners", "ANTHROPIC CAPITAL", "fluid stacking", "an anthropic view"):
            self.assertIsNone(rx.search(s), s)
        own = M.qualify_rx("Fluidstack Ltd", sp)
        self.assertIsNone(own.search("Fluidstack signed a lease"))
        self.assertTrue(own.search("for Anthropic"))
        self.assertTrue(all(q["forms"] == ["8-K"] for q in sp["queries"]))   # forme racine : 8-K/A compris (point 10)
        self.assertEqual((sp["cap"], sp["order"]), (225, "recent_first"))          # D-0066, point 6 (plafond initial : 80)

    def test_priority_then_recent_first(self):
        sp = S["anthropic_chain"]
        self.assertEqual(M.priority_class("a lease with Fluidstack for Anthropic", sp), 0)
        self.assertEqual(M.priority_class("Anthropic will use up to one million TPUs", sp), 1)
        self.assertEqual(M.priority_class("200 MW of critical IT load for Anthropic", sp), 1)
        self.assertEqual(M.priority_class("Anthropic is one of our customers", sp), 2)
        d = lambda f, date: {"filer": "X", "form": "8-K", "file": f, "file_date": date, "adsh": f}
        units = [(d("old_fs", "2024-01-02"), 0, "Fluidstack"), (d("new_gen", "2026-09-01"), 0, "Anthropic is a customer"),
                 (d("new_dc", "2026-08-01"), 0, "an Anthropic data center"), (d("new_fs", "2026-07-01"), 0, "FluidStack")]
        units.sort(key=lambda u: M._order_key(u[0], u[1], sp, u[2]))
        self.assertEqual([u[0]["file"] for u in units], ["new_fs", "old_fs", "new_dc", "new_gen"])
        a = {"filer": "X", "form": "8-K", "file": "a", "file_date": "2025-01-01", "adsh": "1"}
        self.assertLess(M._order_key(dict(a, file_date="2026-01-01"), 0, S["stargate"]), M._order_key(a, 0, S["stargate"]))

    def test_triplet_evidence(self):
        """Une pièce de 8-K se classe par son triplet, comme le registre des documents (§2.1, §2.3) ; les autres
        montages gardent le niveau du formulaire."""
        sp, ev = S["anthropic_chain"], M.evidence
        self.assertEqual(sp["evidence"], "triplet")
        d = lambda ft, items, form="8-K": {"form": form, "file_type": ft, "items": items}
        self.assertEqual(ev(d("EX-99.1", "1.01,7.01,9.01"), sp), ("E", "unaudited", "furnished"))
        self.assertEqual(ev(d("EX-10.1", "1.01,9.01"), sp), ("D", "not_applicable", "filed"))
        self.assertEqual(ev(d("8-K", "7.01,9.01"), sp), ("E", "unaudited", "furnished"))
        self.assertEqual(ev(d("8-K", "1.01,2.03,9.01"), sp), ("C", "unaudited", "filed"))
        self.assertEqual(ev(d("8-K/A", "2.02", "8-K/A"), sp)[0], "E")
        # D-0066, point 5 : tous les montages ; une pièce d'un autre formulaire garde le niveau de son formulaire. Les
        # montages de D-0067 suivent le registre des documents pour tous les formulaires, triplet compris pour les 8-K
        self.assertTrue(all(v.get("evidence") in ("triplet", "registry") for v in S.values()))
        self.assertEqual({m for m, v in S.items() if v.get("evidence") == "registry"}, {"labs_contracts", "labs_events"})
        for ft, items in (("EX-10.1", "1.01,9.01"), ("EX-99.1", "7.01"), (None, "7.01,9.01"), (None, "1.01,2.03,9.01")):
            self.assertEqual(ev(d(ft, items), S["labs_contracts"]), ev(d(ft, items), sp))
        self.assertEqual(ev(d("EX-99.1", "7.01"), S["stargate"]), ("E", "unaudited", "furnished"))
        self.assertEqual(ev(d("EX-4.1", "1.01,2.03,9.01"), S["galaxy_helios"])[0], "D")
        self.assertEqual(ev(d(None, None, "424B4"), S["spacex_anthropic"])[0], "C")
        self.assertEqual(ev(d("EX-99.1", None, "6-K"), {})[0], M.D.form_evidence("6-K", None)[0])

    def test_fluidstack_entities_by_extract(self):
        """D-0064, point 6 : Fluidstack CS I Inc. rejoint Fluidstack Ltd. par l'extrait qui la dit filiale indirecte à
        100 % ; Fluidstack USA I à IV restent des contreparties propres ; deux alias nés d'un extrait qui les définit."""
        from pipeline import config
        from pipeline import entities as E
        names = ["Fluidstack CS I Inc.", "Fluidstack USA I Inc.", "Abernathy Joint Venture", "Fluidstack USA III"]
        _, reg = E.build({"meta": {}}, config.load(), {n: False for n in names})
        g = lambda n: E.resolve(reg, n, "2026-06-30")[1]
        self.assertEqual(g("Fluidstack CS I Inc."), "CP:fluidstack ltd")
        self.assertEqual(g("Fluidstack USA I Inc."), "CP:fluidstack usa i inc")
        self.assertEqual(g("Abernathy Joint Venture"), "CP:fs cs i llc")
        self.assertEqual(g("Fluidstack USA III"), "CP:fluidstack usa iii inc")

    def test_chain_aliases_by_extract(self):
        """D-0066 : « AWS » (8-K d'Amazon) et « Cerebras » (S-1 de Cerebras), alias nés d'un extrait qui les définit ;
        la cible déposante découverte garde son CIK, comme Sprint Corporation (D-0022)."""
        from pipeline import config
        from pipeline import entities as E
        rows, reg = E.build({"meta": {}}, config.load(), {"AWS": False, "Cerebras": False},
                            discovered=[("CEREBRAS SYSTEMS INC.", "2021728")])
        r = lambda n: E.resolve(reg, n, "2026-06-30")
        self.assertEqual(r("AWS")[:2], ("name:amazon web services inc", "AMZN"))
        self.assertEqual(r("Cerebras")[:2], ("name:cerebras systems inc", "CP:cerebras systems inc"))
        ent = [x for x in rows if x["entity_id"] == "name:cerebras systems inc" and x["record_kind"] == "entity"]
        self.assertEqual([(x["cik"], x["is_filer"]) for x in ent], [("2021728", True)])

    def test_search_sends_forms(self):
        """Les formulaires racines d'une requête vont dans `forms`, et dans le journal des requêtes."""
        spec = {"period": ["2023-01-01", "2026-10-07"], "queries": [{"q": '"Fluidstack"', "forms": ["8-K", "8-K/A"]},
                                                                    {"q": '"Anthropic"'}]}
        sent, logged = [], []

        def efts(client, params):
            sent.append(params)
            return {"hits": {"total": {"value": 0, "relation": "eq"}, "hits": []}}, "url", False
        saved = (M.specs, M._client, M._paths, D._efts, D._log_query)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            M.specs = lambda cfg=None: {"t": spec}
            M._client = lambda rate=4.0: None
            M._paths = lambda mid: (pathlib.Path(tmp) / "hits.json", None, None)
            D._efts = efts
            D._log_query = lambda rec, log=None: logged.append(rec)
            try:
                M.search("t")
            finally:
                M.specs, M._client, M._paths, D._efts, D._log_query = saved
        self.assertEqual(sent[0]["forms"], "8-K,8-K/A")
        self.assertNotIn("forms", sent[1])
        self.assertEqual([r["forms"] for r in logged], [["8-K", "8-K/A"], None])


class Retier(unittest.TestCase):
    """D-0066, point 5 : les blocs déjà préparés gardent texte, clé et lignes ; seul le niveau suit le triplet."""

    def test_blocks_of_8k_follow_their_triplet_in_place(self):
        import pandas as pd
        b = lambda m, acc, doc, form, ft, tier, ck: {"montage": m, "accession": acc, "document": doc, "form": form,
                                                     "exhibit_type": ft, "tier": tier, "assurance_level": "not_applicable",
                                                     "filing_status": "filed", "content_key": ck, "text": ck}
        cat = [b("t", "0001-26-000001", "ex99.htm", "8-K", "EX-99.1", "C", "k1"),
               b("t", "0001-26-000002", "ex10.htm", "8-K", "EX-10.1", "C", "k2"),
               b("t", "0001-26-000003", "q.htm", "10-Q", None, "B", "k3"),
               b("u", "0001-26-000004", "ex99.htm", "8-K", "EX-99.1", "C", "k4")]
        with tempfile.TemporaryDirectory() as tmp:
            cp = pathlib.Path(tmp) / "blocks.jsonl"
            cp.write_text("".join(json.dumps(x) + "\n" for x in cat))
            docs = pathlib.Path(tmp) / "docs.parquet"
            pd.DataFrame([{"adsh": "0001-26-000001", "file": "ex99.htm", "form": "8-K", "file_type": "EX-99.1", "items": "7.01,9.01"},
                          {"adsh": "0001-26-000002", "file": "ex10.htm", "form": "8-K", "file_type": "EX-10.1",
                           "items": "1.01,9.01"}]).to_parquet(docs)
            saved = M.CATALOG, M.specs, M._paths
            M.CATALOG = cp
            M.specs = lambda cfg=None: {"t": {"evidence": "triplet"}, "u": {}}
            M._paths = lambda mid: (None, docs if mid == "t" else pathlib.Path(tmp) / "none.parquet", None)
            try:
                ch = M.retier()
            finally:
                M.CATALOG, M.specs, M._paths = saved
            out = [json.loads(x) for x in cp.read_text().splitlines()]
        self.assertEqual(dict(ch), {("t", "C", "E"): 1, ("t", "C", "D"): 1})
        self.assertEqual([x["tier"] for x in out], ["E", "D", "B", "C"])
        self.assertEqual([x["content_key"] for x in out], ["k1", "k2", "k3", "k4"])
        self.assertEqual((out[0]["filing_status"], out[0]["assurance_level"]), ("furnished", "unaudited"))


class Span(unittest.TestCase):
    """D-0066, point 7 : un passage fixé d'un document, lignes jointes, de la première occurrence du début à la fin."""

    def test_passage_joins_lines_from_start_to_end(self):
        lines = ["Prospectus summary", "capacity to customers. For example, in May 2026, we entered into Cloud Services",
                 "Agreements with Anthropic PBC, with respect to compute. Pursuant to these agreements, the customer has",
                 "agreed to pay us $1.25 billion per month. The agreements may be terminated by either party upon 90",
                 "days' notice. The customer will retain its data.", "Business",
                 "For example, in May 2026, we entered into Cloud Services Agreements with Anthropic PBC again."]
        spec = {"source": "span", "evidence": "triplet", "noted_terms": [r"\bAnthropic\b"],
                "spans": [{"cik": "1181412", "accession": "0001-26-000001", "file": "s.htm", "form": "424B4",
                           "filing_date": "2026-06-12", "filer": "SPACE EXPLORATION TECHNOLOGIES CORP",
                           "start": "For example, in May 2026, we entered into Cloud Services Agreements with Anthropic",
                           "end": r"upon 90 days' notice\."}]}
        saved = M.cache.read, M.document_text
        M.cache.read = lambda path: b""
        M.document_text = lambda raw, sp: ("\n".join(lines), "linearized")
        try:
            b, = M.span_blocks("spacex_anthropic", spec, {"0001181412": "SPCX"})
        finally:
            M.cache.read, M.document_text = saved
        self.assertTrue(b["text"].startswith("For example, in May 2026, we entered"))
        self.assertTrue(b["text"].endswith("upon 90 days' notice."))
        self.assertIn("$1.25 billion per month", b["text"])
        self.assertEqual(b["span"]["paragraphs"], [1, 4])
        self.assertEqual((b["tier"], b["filing_status"], b["group_id"], b["terms"]), ("C", "filed", "SPCX", ["Anthropic"]))
        self.assertEqual(S["spacex_anthropic"]["source"], "span")


class SecLetters(unittest.TestCase):
    """D-0064, point 4 : lettres du personnel de la SEC (UPLOAD) et réponses des sociétés (CORRESP), niveau E,
    `correspondence` ; texte des PDF en paragraphes, pour ce montage seul."""

    def test_correspondence_tier(self):
        for f in ("CORRESP", "UPLOAD", "DRSLTR"):
            self.assertEqual(D.form_evidence(f, None), ("E", "not_applicable", "correspondence"))
        self.assertEqual(D.form_evidence("8-K", None), ("C", "not_applicable", "filed"))
        self.assertEqual(D.form_evidence("6-K", None), ("E", "not_applicable", "furnished"))
        sp = S["sec_letters"]
        self.assertTrue(all(q["forms"] == ["CORRESP", "UPLOAD"] for q in sp["queries"]))
        rx = M.qualify_rx("MICROSOFT CORP", sp)
        self.assertTrue(rx.search("your investment in OpenAI"))
        self.assertTrue(rx.search("revenue from Anthropic"))
        self.assertIsNone(rx.search("Anthropic Capital Management"))
        self.assertTrue(sp["pdf_text"])
        self.assertFalse(any(v.get("pdf_text") for k, v in S.items() if k != "sec_letters"))

    def test_pdf_paragraphs(self):
        pages = ["Division of Corporation Finance\n\n   Re:   Example Corp\n         Form 10-K\n\n"
                 "1.   Please tell us how you account   for your\n      investment in OpenAI.\n"
                 "2.   We note your disclosure.\n\nResponse: We account for it\nunder the equity method.",
                 "of the Company.\n3. Please revise.", None]
        self.assertEqual(M.pdf_paragraphs(pages).split("\n"),
                         ["Division of Corporation Finance", "Re: Example Corp Form 10-K",
                          "1. Please tell us how you account for your investment in OpenAI.",
                          "2. We note your disclosure.", "Response: We account for it under the equity method.",
                          "of the Company.", "3. Please revise."])

    def test_pdf_text_only_where_asked(self):
        raw = _pdf([["Division of Corporation Finance", "", "1. Please tell us how you account for your",
                     "investment in OpenAI.", "", "Response: We account for it."], ["2. Please revise."]])
        text, how = M.document_text(raw, {"pdf_text": True})
        self.assertEqual(how, "pdf_text")
        self.assertEqual(text.split("\n"), ["Division of Corporation Finance",
                                            "1. Please tell us how you account for your investment in OpenAI.",
                                            "Response: We account for it.", "2. Please revise."])
        self.assertNotEqual(M.document_text(raw, {})[1], "pdf_text")      # sans l'option : le normaliseur, comme avant
        self.assertEqual(M.document_text(_pdf([[]]), {"pdf_text": True}), ("", "pdf_no_text"))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(M.document_text(b"%PDF-1.4 broken", {"pdf_text": True}), ("", "pdf_unreadable"))
        html = b"<html><body><p>Your investment in OpenAI.</p></body></html>"
        self.assertEqual(M.document_text(html, {"pdf_text": True}), D.plain_text(html))


class ExportedExclusions(unittest.TestCase):
    """Une fenêtre d'un montage tiré d'EDGAR dans un facteur de risque sort en `out_of_scope` (D-0058, point 20,
    que l'export omettait ; D-0064) ; un PDF sans texte aussi, avec son motif ; un terme se cite par son libellé."""

    def test_exclusions(self):
        spec = {"decision": "D-0064", "terms": [{"rx": r"\bAnthropic\b(?! Capital)", "label": "Anthropic"}], "cap": 80}
        info = {"risk_factors": [{"adsh": "0001-26-000001", "file": "a.htm", "form": "8-K", "filer": "X Corp", "window": 2}],
                "no_window": [{"adsh": "0000000000-26-000002", "file": "l.pdf", "form": "UPLOAD", "filer": "Y Corp",
                               "text_extraction": "pdf_no_text"},
                              {"adsh": "0001-26-000003", "file": "b.htm", "form": "8-K", "filer": "Z Corp"}]}
        saved = (M.specs, M._paths)
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "info.json"
            p.write_text(json.dumps(info))
            M.specs = lambda cfg=None: {"t": spec}
            M._paths = lambda mid: (None, pathlib.Path(tmp) / "docs.parquet", p)
            try:
                rows = {r["exclusion_key"]: r for r in M.exclusions("2026-10-07")}
            finally:
                M.specs, M._paths = saved
        self.assertEqual(len(rows), 3)
        self.assertIn("facteurs de risque", rows["out_of_scope:montages:t:0001-26-000001/a.htm#2"]["detail"])
        self.assertIn("pdf_no_text", rows["out_of_scope:montages:t:0000000000-26-000002/l.pdf"]["detail"])
        self.assertIn("« Anthropic »", rows["out_of_scope:montages:t:0001-26-000003/b.htm"]["detail"])
