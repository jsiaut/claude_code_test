"""Bloc `labs` (D-0060) : faits balisés qui nomment un laboratoire (volet 3) et grand livre par laboratoire
(volet 4). Un membre ne nomme un laboratoire que par un mot de la casse en chameau, jamais par complément ; une
instance l'emporte sur les Notes Data Sets du même dépôt ; un conflit exige une partie qui n'est pas un
laboratoire ; le grand livre garde le dernier montant connu, jamais une somme.

Lancement : python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import unittest
from decimal import Decimal

from pipeline import labs as L
from pipeline import sections


def fact(fk, acc, concept, dims, value, source="instance", unit="USD", pe="2026-06-30", ps=None, group="MSFT", cik=None,
         qtrs=None):
    lab, mem, compl = L.fact_lab(concept, dims)
    return {"fact_key": fk, "accession": acc, "concept": concept, "dims_list": dims, "value": value, "value_text": None,
            "unit": unit, "period_end": pe, "period_start": ps, "period_type": "duration" if ps else "instant",
            "group_id": group, "cik": cik, "form": "10-Q", "source": source, "lab": lab, "member": mem,
            "complement": compl, "filer_name": None, "qtrs": qtrs, "tier": "B", "knowledge_date": "2026-07-30"}


class MemberRule(unittest.TestCase):
    def test_camel_case_word(self):
        for name, lab in (("OpenAIGlobalLlcMember", "LAB:OPENAI"), ("AnthropicPBCMember", "LAB:ANTHROPIC"),
                          ("LeaseAgreementWithAnthropicPbcMember", "LAB:ANTHROPIC"), ("OpenAIInc", "LAB:OPENAI"),
                          ("EquitySecuritiesWithoutReadilyDeterminableFairValueAnthropic", "LAB:ANTHROPIC"),
                          ("AnthropicMember", "LAB:ANTHROPIC"), ("OPENAIWarrantMember", "LAB:OPENAI")):
            self.assertEqual(L.member_lab(name), (lab, False), name)

    def test_not_a_lab(self):
        for name in ("PhilanthropicContributionsMember", "OpenAirMarketsMember", "OpenaiMember", "CustomerAMember"):
            self.assertEqual(L.member_lab(name), (None, False), name)

    def test_complement_names_no_lab(self):
        self.assertEqual(L.member_lab("EquitySecuritiesWithoutReadilyDeterminableFairValueOtherThanAnthropic"), (None, True))
        self.assertEqual(L.member_lab("InvestmentsExcludingOpenAIMember"), (None, True))
        # « Exceptional » n'est pas « Except » suivi d'une majuscule
        self.assertEqual(L.member_lab("ExceptionalAnthropicMember"), ("LAB:ANTHROPIC", False))

    def test_fact_lab_reads_members_then_extension_concepts(self):
        self.assertEqual(L.fact_lab("us-gaap:Revenue", [["srt:MajorCustomersAxis", "amzn:OpenAIGroupPBCMember"]]),
                         ("LAB:OPENAI", "amzn:OpenAIGroupPBCMember", False))
        self.assertEqual(L.fact_lab("us-gaap:Revenue", [["x:Axis", "typed:OpenAI"]]), (None, None, False))
        self.assertEqual(L.fact_lab("abc:AnthropicPrepaidCompute", []), ("LAB:ANTHROPIC", None, False))
        self.assertEqual(L.fact_lab("us-gaap:AnthropicLikeName", []), (None, None, False))   # concept standard

    def test_segments(self):
        self.assertEqual(L.segments_dims("CounterpartyName=Anthropic;RelatedPartyTransactionsByRelatedParty=AffiliatedEntity;"),
                         [["CounterpartyName", "Anthropic"], ["RelatedPartyTransactionsByRelatedParty", "AffiliatedEntity"]])


class Retained(unittest.TestCase):
    def test_instance_prevails_and_complement_counted(self):
        inst = [fact("i1", "A1", "us-gaap:X", [["a:Ax", "a:AnthropicMember"]], "5")]
        nds = [fact("n1", "A1", "us-gaap:X", [["Ax", "Anthropic"]], "5", source="nds", group=None, cik="0000000001"),
               fact("n2", "A2", "us-gaap:Y", [["Ax", "OpenAIInc"]], "7", source="nds", group=None, cik="0000000002"),
               fact("n3", "A2", "us-gaap:Z", [["Ax", "FairValueOtherThanAnthropic"]], "9", source="nds", group=None,
                    cik="0000000002")]
        L_INST = L.INSTANCES
        try:
            L.INSTANCES = L.config.ROOT / "does-not-exist.parquet"
            kept, st = L.retained(inst=inst, nds=nds)
        finally:
            L.INSTANCES = L_INST
        self.assertEqual(sorted(f["fact_key"] for f in kept), ["i1", "n2"])
        self.assertEqual((st["nds_in_instance"], st["complement"]), (1, 1))


class TaggedCells(unittest.TestCase):
    def cells(self, facts, obs=()):
        return L.tagged_value_cells(facts, None, list(obs), "2026-10-07", groups_by_cik={})

    def test_one_cell_per_fact_duplicates_collapse(self):
        f1 = fact("i1", "A1", "us-gaap:X", [["a:Ax", "a:AnthropicMember"]], "191")
        f2 = fact("i2", "A1", "us-gaap:X", [["a:Ax", "a:AnthropicMember"]], "191")
        f3 = fact("i3", "A1", "us-gaap:X", [["a:Ax", "a:AnthropicMember"]], "96")
        out = self.cells([f1, f2, f3])
        self.assertEqual(sorted(c["value"] for c in out), [Decimal("96"), Decimal("191")])
        self.assertEqual(len({c["breakdown_key"] for c in out}), 2)
        self.assertTrue(all(c["counterparty"] == "LAB:ANTHROPIC" and c["measure"] == "lab_tagged_value" for c in out))

    def test_outside_graph_keeps_its_cik(self):
        f = fact("n1", "A9", "us-gaap:X", [["Ax", "Anthropic"]], "3", source="nds", group=None, cik="0001108524", qtrs=1)
        c = self.cells([f])[0]
        self.assertEqual(c["subject"], "cik:0001108524")
        self.assertIn("outside_graph", c["flags"])
        self.assertTrue(c["breakdown_key"].endswith("|qtrs=1"))

    def test_conflict_needs_a_non_lab_party_in_a_quote_naming_the_lab(self):
        f = fact("i1", "APO1", "apo:CapitalSolutionAgreementAmount", [["srt:CounterpartyNameAxis", "apo:AnthropicMember"]],
                 "35000000000", group="APO")
        broadcom = {"kind": "observation", "validation_state": "valid", "accession": "APO1", "amount": "35000000000",
                    "counterparty_name": "Broadcom Inc.",
                    "quote": "a $35 billion capital solution agreement with Broadcom Inc., which facilitates Anthropic, PBC's compute"}
        lab_line = {**broadcom, "counterparty_name": "OpenAI Group PBC", "quote": "OpenAI ... $35 billion"}
        no_lab = {**broadcom, "quote": "a $35 billion agreement with Broadcom Inc."}
        self.assertIn("Broadcom Inc.", self.cells([f], [broadcom])[0]["flags"])
        self.assertNotIn("conflict", self.cells([f], [lab_line, no_lab])[0]["flags"] or "")


def edge(key, fg, tg, date, amount, family="financing", et="equity_primary", ik="i", nature="financing_cash",
         unit="USD", elim="not_applicable", kd=None):
    return {"link_key": key, "link_kind": "edge", "from_group": fg, "to_group": tg, "family": family, "edge_type": et,
            "instrument_key": ik, "amount_nature": nature, "unit": unit, "amount": amount, "stage": "drawn_or_paid",
            "_date": dt.date.fromisoformat(date) if date else None, "knowledge_date": kd or date, "tier": "B",
            "elimination_status": elim, "source_perspective": "reporting_entity",
            "_obs": {"obs_key": f"ck/{key}", "accession": f"acc-{key}", "form": "10-Q", "group_id": fg,
                     "period_end": date, "event_type": "funding"}}


class Ledger(unittest.TestCase):
    def test_latest_amount_never_a_sum(self):
        out = L.ledger_cells([edge("a", "AMZN", "LAB:OPENAI", "2026-03-31", "15000000000"),
                              edge("b", "AMZN", "LAB:OPENAI", "2026-06-30", "13700000000"),
                              edge("c", "AMZN", "LAB:OPENAI", "2026-07-31", "21300000000")], "2026-10-07")
        self.assertEqual(len(out), 1)
        c = out[0]
        self.assertEqual((c["value"], c["period_end"], c["subject"], c["counterparty"]),
                         (Decimal("21300000000"), "2026-07-31", "AMZN", "LAB:OPENAI"))
        self.assertIn('"n_amounts": 3', c["flags"])
        self.assertIn("obs:ck/c", c["lineage"])

    def test_direction_units_and_exclusions(self):
        out = L.ledger_cells([edge("a", "LAB:OPENAI", "MSFT", "2026-06-30", "250000000000", family="commercial",
                                   et="purchase_commitment", ik="azure", nature="capacity_commitment"),
                              edge("b", "AMD", "LAB:OPENAI", "2026-06-27", "160000000", family="customer_consideration",
                                   et="equity_or_warrants_to_customer", ik="w", nature="consideration_payable_to_customer",
                                   unit="shares"),
                              edge("c", "AMD", "LAB:OPENAI", "2026-06-27", "5", ik="w2", unit="USD"),
                              edge("d", "MSFT", "LAB:OPENAI", "2026-06-30", None),                  # relation, sans montant
                              edge("e", "MSFT", "MSFT", "2026-06-30", "1"),                         # aucun laboratoire
                              edge("f", "AMZN", "LAB:ANTHROPIC", "2026-06-30", "1", elim="eliminated")], "2026-10-07")
        got = sorted((c["subject"], c["breakdown_key"].split("|")[0], c["unit"]) for c in out)
        self.assertEqual(got, [("AMD", "to_lab", "USD"), ("AMD", "to_lab", "shares"), ("MSFT", "from_lab", "USD")])


class Markers(unittest.TestCase):
    def test_marker_follows_the_fact_and_hidden_facts_vanish(self):
        raw = (b'<html><body><ix:header><ix:hidden><ix:nonNumeric id="h1" name="x:Y">P20Y</ix:nonNumeric></ix:hidden>'
               b'</ix:header><p>The Tenant Lease is for <ix:nonFraction id="f1" name="x:MW">191</ix:nonFraction> MW.</p>'
               b'<p>Other <ix:nonFraction id="f2" name="x:Z">5</ix:nonFraction>.</p></body></html>')
        text = sections.full_text(L.mark_facts(raw, {"f1", "h1"}))
        self.assertIn(L.MARK.format("f1") + "191", text)
        self.assertNotIn(L.MARK.format("h1"), text)
        self.assertNotIn(L.MARK.format("f2"), text)
        self.assertEqual(L.MARK_RX.sub("", text).count("191"), 1)


if __name__ == "__main__":
    unittest.main()
