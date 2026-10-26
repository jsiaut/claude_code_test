"""D-0076 : composition des en-cours et des actifs pas encore en service, telle que l'écrivent les notes. Lexique,
renvois de bas de tableau, fenêtres, lignes d'en-cours nues, contrôles des lignes de composante, mesure descriptive et
préparation d'un montage nouveau.

Lancement : python3 -m unittest discover -s tests -t .
"""
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from pipeline import config, load, montages, ppe_notes, reader

RX = ppe_notes.lexicon(montages.specs()["ppe_components"])


class Lexicon(unittest.TestCase):
    """Le lexique fixé dans config.yaml (point 4)."""

    def test_variants(self):
        for t in ("Construction in progress", "Construction-in-process", "assets under construction",
                  "equipment not placed into service", "assets not yet placed in service",
                  "assets not ready for their intended use", "servers pending deployment", "undeployed miners",
                  "components stored by our suppliers", "machinery in transit", "computer equipment under installation"):
            self.assertTrue(RX.search(t), t)

    def test_under_construction_alone_does_not_qualify(self):
        self.assertIsNone(RX.search("leases of data centers under construction"))


class Windows(unittest.TestCase):
    """Renvois rattachés par leur marque, fenêtres d'un paragraphe de part et d'autre, lignes nues non servies."""

    TABLE = ["Property, plant, and equipment consisted of the following:",
             "As of | September 3, 2026 | August 28, 2025",
             "Land | $ 1 | $ 1",
             "Buildings | 20 | 18",
             "Equipment (1) | 100 | 90",
             "Construction in progress (2) | 50 | 40",
             "Software | 3 | 3",
             "Total | 174 | 152",
             "(1) Includes costs related to equipment not placed into service of $6.12 billion as of September 3, 2026.",
             "(2) Primarily includes building-related construction and tool installation.",
             "Depreciation expense was $8 billion."]

    def test_marks(self):
        self.assertEqual(ppe_notes.foot_mark("(1) Includes costs"), "1")
        self.assertEqual(ppe_notes.foot_mark("(a) | Includes servers not yet placed in service"), "a")
        self.assertIsNone(ppe_notes.foot_mark("Equipment (1) | 100 | 90"))
        self.assertEqual(ppe_notes.row_marks("Equipment (1) | 100 | 90"), {"1"})
        self.assertEqual(ppe_notes.row_marks("Construction in progress(2) | 50"), {"2"})
        self.assertEqual(ppe_notes.row_marks("Gains (losses) on sales | 3"), set())

    def test_footnotes_join_their_rows(self):
        q = ppe_notes.qualifying(self.TABLE, RX)
        # la ligne d'en-cours amène son renvoi (2) ; le renvoi (1) amène la ligne Equipment (1)
        self.assertEqual(q, [4, 5, 8, 9])
        ws, bare = ppe_notes.units(self.TABLE, RX)
        self.assertEqual(bare, 0)
        self.assertEqual([(a, b) for a, b, _ in ws], [(3, 11)])

    def test_bare_cip_row_is_not_served(self):
        paras = ["Land | 1 | 1", "Construction in progress | 5 | 4", "Total | 6 | 5",
                 "Depreciation expense was $1 million.", "", "Other text.", "More text.",
                 "Construction in progress, net | 2 | 1", "Total | 3 | 2"]
        ws, bare = ppe_notes.units([p for p in paras if p], RX)
        self.assertEqual((ws, bare), ([], 2))

    def test_text_window_kept_next_to_a_bare_row(self):
        paras = ["Construction in progress | 5 | 4",
                 "Construction in progress primarily consists of servers and network equipment not yet placed in service."]
        ws, bare = ppe_notes.units(paras, RX)
        self.assertEqual(([(a, b) for a, b, _ in ws], bare), ([(0, 2)], 0))

    def test_footnote_row_variant(self):
        paras = ["Servers (a) | 10 | 9", "Total | 10 | 9", "(a) | Includes servers not yet placed in service."]
        self.assertEqual(ppe_notes.qualifying(paras, RX), [0, 2])

    def test_role_title(self):
        self.assertEqual(ppe_notes.role_title("0000012 - Disclosure - Property and Equipment (Details)"), "property and equipment")
        self.assertEqual(ppe_notes.role_title("9952161 - Disclosure - Property, Plant, and Equipment"),
                         "property, plant, and equipment")
        self.assertEqual(ppe_notes.role_title("0000040 - Disclosure - Property and Equipment - Schedule (Details)"),
                         "property and equipment")
        self.assertEqual(ppe_notes.role_title("0000041 - Disclosure - Property and Equipment (Details Narrative)"),
                         "property and equipment")


def line(**kw):
    base = {"kind": "observation", "quote": "Includes costs related to equipment not placed into service of $6.12 billion",
            "asset_component": "unspecified", "asset_state": "not_in_service", "component_of": "ppe_class",
            "component_statement": "amount", "amount": "6120000000", "unit": "USD", "currency": "USD",
            "amount_origin": "narrative_only", "amount_qualifier": "exact", "period_end": "2026-09-03",
            "note": "ligne de composante (D-0076)"}
    base.update(kw)
    return {k: v for k, v in base.items() if v is not None}


class ReaderChecks(unittest.TestCase):
    """Contrôles du lecteur (point 7)."""

    def test_valid_line(self):
        self.assertEqual(reader.schema_errors(line()), [])

    def test_four_fields(self):
        self.assertTrue(any("quatre champs" in e for e in reader.schema_errors(line(asset_state=None))))

    def test_descriptive(self):
        self.assertTrue(any("descriptive" in e for e in reader.schema_errors(line(family="commercial"))))

    def test_amount_rules(self):
        self.assertTrue(any("porte son montant" in e for e in reader.schema_errors(
            line(amount=None, unit=None, currency=None, amount_origin=None, amount_qualifier=None))))
        self.assertTrue(any("aucun montant" in e for e in reader.schema_errors(line(component_statement="primarily"))))

    def test_date_required(self):
        self.assertTrue(any("sa date" in e for e in reader.schema_errors(line(period_end=None))))

    def test_other_lines_untouched(self):
        self.assertEqual(ppe_notes.schema_errors({"kind": "observation", "quote": "x", "family": "commercial"}), [])


class QuoteWords(unittest.TestCase):
    """La citation nomme la composante et l'état choisis (point 5)."""

    BLOCK = {"text": "Construction in progress includes servers and network assets components stored by our suppliers.",
             "candidate_facts": [], "locator": {}}

    def errs(self, **kw):
        return load.semantic_errors(line(**kw), self.BLOCK, locate=lambda b, q: None)[0]

    def test_component_word(self):
        q = "servers and network assets components stored by our suppliers"
        self.assertEqual(self.errs(quote=q, asset_component="it_equipment", asset_state="at_suppliers",
                                   component_of="construction_in_progress", component_statement="includes",
                                   amount=None, unit=None, currency=None, amount_origin=None, amount_qualifier=None), [])
        e = self.errs(quote=q, asset_component="facilities", asset_state="at_suppliers",
                      component_of="construction_in_progress", component_statement="includes",
                      amount=None, unit=None, currency=None, amount_origin=None, amount_qualifier=None)
        self.assertTrue(any("composante facilities" in x for x in e))

    def test_state_word(self):
        q = "servers and network assets components stored by our suppliers"
        e = self.errs(quote=q, asset_component="it_equipment", asset_state="in_transit",
                      component_of="construction_in_progress", component_statement="includes",
                      amount=None, unit=None, currency=None, amount_origin=None, amount_qualifier=None)
        self.assertTrue(any("état in_transit" in x for x in e))

    def test_hard_drives(self):
        """Point 16 : les disques durs sont du matériel informatique."""
        q = "primarily comprised of hard drives that are not yet deployed"
        block = {"text": "Construction-in-progress is " + q + ".", "candidate_facts": [], "locator": {}}
        kw = dict(quote=q, asset_state="not_in_service", component_of="construction_in_progress", component_statement="primarily",
                  amount=None, unit=None, currency=None, amount_origin=None, amount_qualifier=None)
        self.assertEqual(load.semantic_errors(line(asset_component="it_equipment", **kw), block, locate=lambda b, x: None)[0], [])
        e = load.semantic_errors(line(asset_component="mining_equipment", **kw), block, locate=lambda b, x: None)[0]
        self.assertTrue(any("composante mining_equipment" in x for x in e))


def obs(key, kd, **kw):
    o = {"obs_key": key, "kind": "observation", "validation_state": "valid", "group_id": "MU", "knowledge_date": kd,
         "tier": "A", "accession": "acc-" + key, "form": "10-K", "obs_quote": None}
    o.update(line(**kw))
    return o


class Cells(unittest.TestCase):
    """`ppe_component_disclosed` (point 6) : premier et dernier dépôt, montant tel qu'écrit, en-cours balisé à côté."""

    def cip_at(self, g, pe, cutoff):
        if g != "MU":
            return None, "concept_unresolved"
        return {"value": Decimal("11400000000"), "fact_key": "f:cip", "knowledge_date": cutoff, "tier": "A",
                "is_tagged": True, "concept": "us-gaap:ConstructionInProgressGross", "unit": "USD"}, None

    def test_views_and_values(self):
        lines = [obs("a/1/0", "2026-10-20"), obs("b/1/0", "2026-12-20", amount="6130000000"),
                 obs("a/1/1", "2026-10-20", component_statement="primarily", asset_component="facilities",
                     asset_state="under_construction", component_of="construction_in_progress",
                     quote="Primarily includes building-related construction", amount=None, unit=None, currency=None,
                     amount_origin=None, amount_qualifier=None)]
        cells = ppe_notes.component_cells(lines, self.cip_at, "2026-12-31")
        comp = {(c["breakdown_key"], c["view"]): c for c in cells if c["term"] == "component"}
        k = "ppe_class|unspecified|not_in_service|amount"
        self.assertEqual(comp[(k, "as_known")]["value"], Decimal("6120000000"))
        self.assertEqual(comp[(k, "revised")]["value"], Decimal("6130000000"))
        p = comp[("construction_in_progress|facilities|under_construction|primarily", "as_known")]
        self.assertIsNone(p["value"])
        self.assertEqual(p["value_text"], "primarily")
        cip = [c for c in cells if c["term"] == "cip_tagged"]
        self.assertEqual(len(cip), 2)                          # une date, deux vues
        self.assertTrue(all(c["value"] == Decimal("11400000000") and c["unit"] == "USD" for c in cip))
        self.assertEqual(json.loads(cip[0]["lineage"]), ["f:cip"])

    def test_written_class_splits_the_key(self):
        a = obs("a/1/0", "2026-10-20", instrument_key="land and buildings", asset_component="facilities",
                asset_state="under_construction", quote="assets under construction for land and buildings of EUR 79.0 million")
        b = obs("a/1/1", "2026-10-20", instrument_key="leasehold improvements", asset_component="facilities",
                asset_state="under_construction", quote="leasehold improvements of EUR 7.8 million", amount="7800000")
        keys = {c["breakdown_key"] for c in ppe_notes.component_cells([a, b], self.cip_at, "2026-12-31") if c["term"] == "component"}
        self.assertEqual(keys, {"ppe_class|facilities|under_construction|amount|land and buildings",
                                "ppe_class|facilities|under_construction|amount|leasehold improvements"})

    def test_no_tagged_cip(self):
        lines = [dict(obs("a/1/0", "2026-10-20"), group_id="MSFT")]
        cip = [c for c in ppe_notes.component_cells(lines, self.cip_at, "2026-12-31") if c["term"] == "cip_tagged"]
        self.assertEqual({(c["status"], c["nd_reason"]) for c in cip}, {("not_determinable", "concept_unresolved")})

    def test_tier_e_and_abstentions_excluded(self):
        lines = [dict(obs("a/1/0", "2026-10-20"), tier="E"), dict(obs("a/1/1", "2026-10-20"), kind="abstention")]
        self.assertEqual(ppe_notes.component_cells(lines, self.cip_at, "2026-12-31"), [])


class Evidence(unittest.TestCase):
    """Niveau des fenêtres : celui du registre des documents pour un rapport périodique (point 4)."""

    def test_same_as_registry(self):
        from pipeline import documents
        for form in ("10-K", "10-K/A", "10-KT", "10-Q", "20-F"):
            st, _, assurance, tier = documents._classify("primary_document", form, "", None)
            self.assertEqual(ppe_notes.evidence(form), (st, assurance, tier), form)
        self.assertEqual(ppe_notes.evidence("424B4", "audited"), ("filed", "audited", "A"))
        self.assertEqual(ppe_notes.evidence("424B4", "unaudited"), ("filed", "unaudited", "C"))


class NewMontage(unittest.TestCase):
    """Un montage nouveau se prépare sur toute sa période (point 4)."""

    def test_is_new(self):
        with tempfile.TemporaryDirectory() as d:
            info = Path(d) / "info.json"
            with mock.patch.object(montages, "_paths", lambda mid: (None, None, info)):
                self.assertTrue(montages.is_new("x"))                     # jamais préparé
                info.write_text(json.dumps({"units": 3}))
                self.assertFalse(montages.is_new("x"))                    # préparé à une exécution précédente
                info.write_text(json.dumps({"first_as_of": config.as_of()}))
                self.assertTrue(montages.is_new("x"))                     # préparé dans l'exécution courante


if __name__ == "__main__":
    unittest.main()
