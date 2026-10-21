"""D-0067 : contrats et calendrier des capacités (volet 8), événements propres aux laboratoires (volet 9)."""
import datetime as dt
import re
import unittest
from decimal import Decimal

from pipeline import config, lab_terms as LT, load, montages as M, reader
from pipeline import entities as E


def _reg():
    names = ["OpenAI OpCo, LLC", "Anthropic, PBC", "Fluidstack Ltd", "Advanced Micro Devices, Inc."]
    return E.build({"meta": {}}, config.load(), {n: False for n in names})[1]


def obs(n, **kw):
    o = {"obs_key": f"ck{n}/p/0", "kind": "observation", "validation_state": "valid", "group_id": "AMD",
         "accession": f"0000000000-26-00000{n}", "form": "8-K", "exhibit_type": "EX-4.1", "knowledge_date": "2025-10-06",
         "tier": "D", "quote": "the Warrantholder", "counterparty_name": "OpenAI OpCo, LLC"}
    o.update(kw)
    return o


class Schema(unittest.TestCase):
    def test_capacity_fields(self):
        base = {"kind": "observation", "quote": "200 MW of critical IT load"}
        self.assertEqual(reader.schema_errors({**base, "capacity_value": "200", "capacity_unit": "MW",
                                               "capacity_kind": "hosting", "capacity_qualifier": "exact"}), [])
        e = reader.schema_errors({**base, "capacity_value": "200"})
        self.assertTrue(any("unité" in x for x in e) and any("genre" in x for x in e) and any("qualificatif" in x for x in e))
        e = reader.schema_errors({**base, "capacity_value": "200", "capacity_unit": "MW", "capacity_kind": "hosting",
                                  "capacity_qualifier": "exact", "family": "commercial"})
        self.assertTrue(any("descriptive" in x for x in e))
        self.assertTrue(reader.schema_errors({**base, "capacity_unit": "MW"}))
        self.assertTrue(reader.schema_errors({**base, "capacity_unit": "kW", "capacity_value": "1"}))
        self.assertEqual(reader.schema_errors({**base, "clause_kind": "vesting_tranche"}), [])
        self.assertTrue(reader.schema_errors({**base, "clause_kind": "warranty"}))
        self.assertEqual(reader.schema_errors({**base, "signal": "site_delay", "signal_present": True}), [])

    def test_capacity_in_quote(self):
        ok = [("contracted 200 MW of critical IT load", "200", "MW"), ("a 1.2GW campus", "1.2", "GW"),
              ("six gigawatts of AMD GPUs", "6", "GW"), ("deploy a gigawatt", "1", "GW"), ("a 1,000-megawatt site", "1000", "MW")]
        for q, v, u in ok:
            self.assertTrue(load.capacity_in_quote(q, v, u), q)
        for q, v, u in [("1,000 MW", "100", "MW"), ("200 MW", "200", "GW"), ("v2.5 GW", "5", "GW"), ("Section 200 MW", "20", "MW")]:
            self.assertFalse(load.capacity_in_quote(q, v, u), q)
        blk = {"text": "We have contracted 200 MW of critical IT load with Fluidstack.", "candidate_facts": []}
        line = {"kind": "observation", "quote": "We have contracted 200 MW of critical IT load",
                "capacity_value": "300", "capacity_unit": "MW"}
        errs, _ = load.semantic_errors(line, blk, locate=lambda b, q: None)
        self.assertTrue(any("capacité" in e for e in errs))
        errs, _ = load.semantic_errors({**line, "capacity_value": "200"}, blk, locate=lambda b, q: None)
        self.assertEqual(errs, [])


class Units(unittest.TestCase):
    SPEC = M.specs()["labs_contracts"]
    EV = M.specs()["labs_events"]

    def test_party_and_clauses(self):
        d = {"filer": "Cerebras Systems Inc."}
        text = ("MASTER RELATIONSHIP AGREEMENT governs the provision of the Services by Cerebras Systems Inc. to "
                "OpenAI OpCo, LLC (\"OpenAI\")\n" + "x " * 2000 + "\nEither Party may terminate this Agreement for convenience.")
        q, party = M.qualifier(d, self.SPEC, text)
        self.assertTrue(party)
        self.assertTrue(q("Either Party may terminate this Agreement for convenience."))
        self.assertTrue(q("The first tranche shall vest upon delivery of 250 MW."))
        self.assertFalse(q("Notices shall be sent by courier."))
        q2, party2 = M.qualifier(d, self.SPEC, "x " * 2000 + "\nOpenAI Contract means the master services agreement.")
        self.assertFalse(party2)
        self.assertTrue(q2("OpenAI Contract means the master services agreement."))
        self.assertFalse(q2("Either Party may terminate this Agreement for convenience."))

    def test_require_and_window(self):
        q, _ = M.qualifier({"filer": "Alphabet Inc."}, self.EV, "")
        self.assertTrue(q("Anthropic will have access to more than a gigawatt of capacity."))
        self.assertTrue(q("the start of the OpenAI campus was delayed to 2027"))
        self.assertFalse(q("We partner with Anthropic to offer Claude models."))
        self.assertFalse(q("We contracted 200 MW of critical IT load."))
        self.assertFalse(q("OpenAI uses our so-called Stargate site."))   # « called » hors d'une garantie
        self.assertTrue(q("The guarantee was called after OpenAI's default."))
        paras = ["a", "b", "Anthropic signed for 1 GW", "c", "d", "e", "OpenAI delayed", "f"]
        self.assertEqual(M.windows(paras, q, 1), [[1, 4], [5, 8]])
        self.assertEqual(M.windows(paras, q), [[0, 8]])

    def test_file_types_and_evidence(self):
        rx = re.compile(self.SPEC["file_type_rx"])
        for ft, keep in (("EX-10.1", True), ("EX-10", True), ("EX-4.1", True), ("EX-2.1", True), ("EX-10.11", True),
                         ("EX-101.INS", False), ("EX-21.1", False), ("EX-99.1", False), ("EX-23", False)):
            self.assertEqual(bool(rx.search(ft)), keep, ft)
        ev = lambda form, ft, items=None: M.evidence({"form": form, "file_type": ft, "items": items, "adsh": "x"}, self.SPEC)
        self.assertEqual(ev("10-Q", "EX-10.7"), ("D", "not_applicable", "filed"))
        self.assertEqual(ev("S-1", "EX-10.11")[0], "D")
        self.assertEqual(ev("8-K", "EX-99.1"), ("E", "unaudited", "furnished"))
        self.assertEqual(ev("10-K", "10-K")[0], "A")
        self.assertEqual(M.evidence({"source": "block", "tier": "B", "assurance_level": "reviewed", "filing_status": "filed",
                                     "form": "10-Q"}, self.EV), ("B", "reviewed", "filed"))


class Cells(unittest.TestCase):
    AS_OF = "2026-10-07"

    def test_quarters(self):
        q = LT.quarters(dt.date(2026, 10, 7))
        self.assertEqual(q[0], (dt.date(2021, 1, 1), dt.date(2021, 3, 31)))
        self.assertEqual(q[-1], (dt.date(2026, 7, 1), dt.date(2026, 9, 30)))
        self.assertEqual(len(q), 23)

    def test_clause_and_capacity(self):
        reg = _reg()
        rows = [obs(1, clause_kind="vesting_tranche", amount="26666667", unit="shares", event_type="warrant_vesting",
                    conditionality="conditional", trigger_description="premier GW livré", redacted=True,
                    instrument_key="amd:openai_warrant_2025"),
                obs(2, clause_kind="termination_right", conditionality="optional", period_label="upon 90 days' notice"),
                obs(3, capacity_value="1", capacity_unit="GW", capacity_kind="compute", capacity_qualifier="exact",
                    stage="signed", quote="the first 1 gigawatt of AMD Instinct MI450 GPUs for OpenAI", counterparty_name=None),
                obs(4, capacity_value="200", capacity_unit="MW", capacity_kind="hosting", capacity_qualifier="exact",
                    quote="200 MW of critical IT load for Fluidstack", counterparty_name="Fluidstack Ltd", group_id="WULF")]
        cl = LT.clause_cells(rows, reg, self.AS_OF)
        self.assertEqual(len(cl), 2)
        self.assertTrue(all(c["counterparty"] == "LAB:OPENAI" and c["subject"] == "AMD" for c in cl))
        self.assertEqual((cl[0]["value"], cl[0]["unit"]), (Decimal("26666667"), "shares"))
        self.assertEqual((cl[1]["value"], cl[1]["value_text"]), (None, "termination_right"))
        cap = LT.capacity_cells(rows, reg, self.AS_OF)
        self.assertEqual(len(cap), 1)                   # le bail de Fluidstack ne nomme aucun laboratoire
        self.assertEqual((cap[0]["value"], cap[0]["unit"], cap[0]["counterparty"]), (Decimal("1"), "GW", "LAB:OPENAI"))
        self.assertIn('"capacity_kind": "compute"', cap[0]["flags"])

    def test_events(self):
        reg = _reg()
        mk = lambda fund, pe, v: {"measure": "nport_equity_mark", "view": "as_known", "subject": "LAB:ANTHROPIC",
                                  "counterparty": fund, "breakdown_key": "EC|TITLE:anthropic pbc", "period_end": pe,
                                  "value": Decimal(v), "knowledge_date": pe}
        marks = [mk("cik:1", "2025-09-30", "140"), mk("cik:1", "2025-12-31", "203"), mk("cik:1", "2026-03-31", "180"),
                 mk("cik:2", "2026-06-30", "300")]
        rows = [obs(5, signal="site_delay", signal_present=True, event_date="2026-05-14",
                    quote="the Anthropic site was delayed", counterparty_name=None),
                obs(6, signal="exclusivity_end", signal_present=False, event_date="2026-05-14")]
        cells = LT.event_cells(rows, reg, marks, self.AS_OF)
        self.assertEqual(len(cells), 2 * 5 * 23)
        get = lambda lab, lid, pe: next(c for c in cells if c["subject"] == lab and c["breakdown_key"] == lid
                                        and c["period_end"] == pe)
        self.assertEqual(get("LAB:ANTHROPIC", "L3", "2026-03-31")["value_text"], "event")
        self.assertEqual(get("LAB:ANTHROPIC", "L3", "2025-12-31")["value_text"], "no_event")
        c = get("LAB:ANTHROPIC", "L3", "2025-09-30")
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "prior_period_missing"))
        self.assertEqual(get("LAB:ANTHROPIC", "L3", "2026-06-30")["nd_reason"], "prior_period_missing")
        self.assertEqual(get("LAB:ANTHROPIC", "L3", "2025-06-30")["nd_reason"], "not_disclosed")
        self.assertEqual(get("LAB:ANTHROPIC", "L5", "2026-06-30")["value_text"], "event")
        self.assertEqual(get("LAB:OPENAI", "L5", "2026-06-30")["status"], "not_determinable")
        c = get("LAB:OPENAI", "L2", "2026-06-30")       # signal_present faux : pas d'événement
        self.assertEqual((c["status"], c["nd_reason"], c["coverage_state"]), ("not_determinable", "not_processed", "not_processed"))
        l4 = LT.event_cells([obs(7, family="credit_support", trigger_occurred="yes", event_date="2024-02-01")], reg, [], self.AS_OF)
        self.assertEqual(next(c for c in l4 if c["subject"] == "LAB:OPENAI" and c["breakdown_key"] == "L4"
                              and c["period_end"] == "2024-03-31")["value_text"], "event")


if __name__ == "__main__":
    unittest.main()
