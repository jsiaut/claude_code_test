"""Bloc montages (D-0046, D-0049) : termes qualifiants hors du nom du déposant, fenêtres de paragraphes.

Lancement : python3 -m unittest discover -s tests -t .
"""
import unittest

from pipeline import montages as M

S = M.specs()


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
