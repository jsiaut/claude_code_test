"""D-0068 : RPO total tiré de l'axe d'horizon (volet 1), dépendance du carnet de E.3 (volet 2), carnet contracté par
client nommé et loyers à recevoir d'un bailleur (volet 3), montage `backlog`."""
import datetime as dt
import json
import unittest
from decimal import Decimal

from pipeline import backlog as B
from pipeline import config, quantities, rank2, reader
from pipeline.measures import cell

TIMING = B.TIMING
CUST = B.CUSTOMER_AXIS


def dims(*pairs):
    return json.dumps([list(p) for p in pairs])


def line(n, statement, basis="rpo", amount=None, pe=None, ev=None, ik=None, kd="2025-05-14", tier="B", client="C1",
         seller="S", currency=None):
    return {"obs_key": f"ck{n}/p/0", "kind": "observation", "validation_state": "valid", "group_id": seller,
            "_client": client, "backlog_basis": basis, "backlog_statement": statement, "amount": amount,
            "period_end": pe, "event_date": ev, "instrument_key": ik, "knowledge_date": kd, "tier": tier,
            "accession": f"0000000000-25-{n:06d}", "currency": currency, "unit": currency or "USD"}


def rpo(g, pe, v, view="as_known", measure="rpo_total"):
    return cell(measure, g, None, pe, view, "2026-10-07", value=Decimal(v), unit="USD",
                terms=[{"value": Decimal(v), "fact_key": f"f:{g}:{pe}", "knowledge_date": pe, "tier": "B"}])


def rpo_nd(g, pe, reason="not_disclosed", view="as_known"):
    return cell("rpo_total", g, None, pe, view, "2026-10-07", status="not_determinable", nd_reason=reason)


class NextDay(unittest.TestCase):
    def test_single_next_day_fact_is_the_total(self):
        """Volet 1 : un seul fait sur l'axe d'horizon, au lendemain de la date, sans total balisé ni autre tranche."""
        nxt = dims((TIMING, "typed:2025-10-01"))
        rows = [("a", "acc1", "2025-09-30", nxt, 1),
                # un fait à deux axes (client et horizon) n'empêche ni ne fait la règle
                ("a2", "acc1", "2025-09-30", dims((CUST, "x:OpenAIMember"), (TIMING, "typed:2025-10-01")), 2),
                # total balisé : rien à dériver
                ("b", "acc2", "2025-09-30", nxt, 1), ("b0", "acc2", "2025-09-30", None, 0),
                # deux tranches : ni l'une ni l'autre n'est le total
                ("c", "acc3", "2025-09-30", nxt, 1), ("c2", "acc3", "2025-09-30", dims((TIMING, "typed:2026-10-01")), 1),
                # une seule tranche, qui commence plus tard : ce n'est pas le total
                ("d", "acc4", "2025-09-30", dims((TIMING, "typed:2026-10-01")), 1),
                # un autre axe seul (produit) : jamais
                ("e", "acc5", "2025-09-30", dims(("srt:ProductOrServiceAxis", "x:CloudMember")), 1)]
        self.assertEqual(quantities.rpo_next_day(rows), {"a"})


class Schema(unittest.TestCase):
    base = {"kind": "observation", "quote": "remaining performance obligations of $11.9 billion with OpenAI",
            "counterparty_name": "OpenAI", "counterparty_evidence": "named"}

    def test_carnet_line(self):
        ok = {**self.base, "backlog_basis": "rpo", "backlog_statement": "remaining", "amount": "11900000000",
              "unit": "USD", "amount_origin": "narrative_only", "amount_qualifier": "approximately", "period_end": "2025-03-31"}
        self.assertEqual(reader.schema_errors(ok), [])
        e = reader.schema_errors({**ok, "backlog_basis": None})
        self.assertTrue(any("base et son énoncé" in x for x in e))
        e = reader.schema_errors({**ok, "family": "commercial"})
        self.assertTrue(any("descriptive" in x for x in e))
        e = reader.schema_errors({**ok, "period_end": None})
        self.assertTrue(any("period_end" in x for x in e))
        e = reader.schema_errors({**ok, "counterparty_evidence": "derivable", "derivation_method": "dimension_member_label"})
        self.assertTrue(any("nomme le client" in x for x in e))
        exc = {**self.base, "backlog_basis": "rpo", "backlog_statement": "excluded", "period_end": "2025-03-31"}
        self.assertEqual(reader.schema_errors(exc), [])
        e = reader.schema_errors({**exc, "amount": "1", "unit": "USD", "amount_origin": "narrative_only",
                                  "amount_qualifier": "exact"})
        self.assertTrue(any("aucun montant" in x for x in e))
        e = reader.schema_errors({**self.base, "backlog_basis": "lease", "backlog_statement": "contract_value"})
        self.assertTrue(any("montant" in x for x in e))
        e = reader.schema_errors({**self.base, "backlog_basis": "rent", "backlog_statement": "remaining"})
        self.assertTrue(any("hors énumération" in x for x in e))


class Members(unittest.TestCase):
    cands = {"LAB:OPENAI": {"OpenAI", "OpenAI Group PBC", "OpenAI Global, LLC"}, "LAB:ANTHROPIC": {"Anthropic, PBC", "Anthropic"},
             "CP:open inc": {"Open Inc."}}

    def test_longest_name_in_member(self):
        self.assertEqual(B.member_group("amzn:OpenAIGroupPBCMember", self.cands), "LAB:OPENAI")
        self.assertEqual(B.member_group("amzn:AnthropicMember", self.cands), "LAB:ANTHROPIC")
        # une catégorie de clients ne nomme aucun client ; un nom trop court ne compte pas
        self.assertIsNone(B.member_group("msft:CommercialCustomersMember", self.cands))
        self.assertIsNone(B.member_group("x:AIMember", {"G": {"AI"}}))
        # deux groupes se partagent le nom le plus long : aucun
        self.assertIsNone(B.member_group("x:AcmeMember", {"G1": {"Acme Corp"[:4]}, "G2": {"ACME"}}))

    def test_tagged_customer_rpo(self):
        rows = [{"fact_key": "b", "group_id": "AMZN", "concept": B.RPO, "period_type": "instant", "period_end": "2026-03-31",
                 "dims": dims((CUST, "amzn:OpenAIGroupPBCMember"), (TIMING, "typed:2026-04-01")), "value": 1000,
                 "unit": "USD", "knowledge_date": "2026-04-30", "tier": "B"},
                # même solde repris au trimestre suivant sous l'horizon d'une autre date : écarté
                {"fact_key": "b2", "group_id": "AMZN", "concept": B.RPO, "period_type": "instant", "period_end": "2026-03-31",
                 "dims": dims((CUST, "amzn:OpenAIGroupPBCMember"), (TIMING, "typed:2026-07-01")), "value": 1000,
                 "unit": "USD", "knowledge_date": "2026-07-31", "tier": "B"},
                {"fact_key": "h", "group_id": "AMZN", "concept": "amzn:RevenueRemainingPerformanceObligationAmountPeriodIncreaseDecrease",
                 "period_type": "duration", "period_start": "2026-04-01", "period_end": "2026-06-30",
                 "dims": dims((CUST, "amzn:AnthropicMember"), (TIMING, "typed:2026-07-01")), "value": 50, "unit": "USD"},
                {"fact_key": "m", "group_id": "MSFT", "concept": B.RPO, "period_type": "instant", "period_end": "2026-06-30",
                 "dims": dims((CUST, "msft:CommercialCustomersMember")), "value": 5, "unit": "USD"}]
        got = B.tagged_customer_rpo(rows, lambda s: self.cands)
        self.assertEqual([(f["fact_key"], f["counterparty"], f["kind"]) for f in got],
                         [("b", "LAB:OPENAI", "balance"), ("h", "LAB:ANTHROPIC", "change")])


class Dependency(unittest.TestCase):
    """Volet 2 : numérateur attribué par le fournisseur, au niveau A à C, connu à la coupure ; jamais borné."""

    def cells(self, tagged=(), lines=(), rpo_cells=(), rpo12=(), buys=True, t="2025-03-31", cut="2025-05-30",
              view="as_known"):
        I = B.Inputs(tagged, lines, rpo_cells, rpo12)
        return {c["term"]: c for c in B.dependency_cells(I, "S", "C1", t, view, cut, cut, buys)}

    def test_remaining_line(self):
        cs = self.cells(lines=[line(1, "remaining", amount="300", pe="2025-03-31")], rpo_cells=[rpo("S", "2025-03-31", 1000)])
        self.assertEqual((cs["total"]["status"], cs["total"]["value"]), ("computed", Decimal("0.3")))
        self.assertEqual(json.loads(cs["total"]["flags"])["source"], "line_remaining")
        # la part au-delà de douze mois n'est pas écrite : non déterminée, même avec le RPO au-delà de douze mois
        cs = self.cells(lines=[line(1, "remaining", amount="300", pe="2025-03-31")], rpo_cells=[rpo("S", "2025-03-31", 1000)],
                        rpo12=[rpo("S", "2025-03-31", 600, measure="rpo_beyond_12m")])
        self.assertEqual((cs["beyond_12m"]["status"], cs["beyond_12m"]["nd_reason"]), ("not_determinable", "not_disclosed"))

    def test_knowledge_cut_and_tier(self):
        late = line(1, "remaining", amount="300", pe="2025-03-31", kd="2025-08-01")
        cs = self.cells(lines=[late], rpo_cells=[rpo("S", "2025-03-31", 1000)])
        self.assertEqual(cs["total"]["nd_reason"], "anonymous")
        d = line(2, "remaining", amount="300", pe="2025-03-31", tier="D")
        self.assertEqual(self.cells(lines=[d], rpo_cells=[rpo("S", "2025-03-31", 1000)])["total"]["nd_reason"], "anonymous")

    def test_exclusion_is_zero_without_other_contract(self):
        exc = line(1, "excluded", pe="2025-03-31", ik="msa")
        val = line(2, "contract_value", amount="11900", ev="2025-03-10", ik="msa")
        cs = self.cells(lines=[exc, val], rpo_cells=[rpo("S", "2025-03-31", 1000)],
                        rpo12=[rpo("S", "2025-03-31", 600, measure="rpo_beyond_12m")])
        self.assertEqual((cs["total"]["status"], cs["total"]["value"]), ("computed", Decimal(0)))
        self.assertEqual((cs["beyond_12m"]["status"], cs["beyond_12m"]["value"]), ("computed", Decimal(0)))
        # un autre contrat signé avant la date : la cellule reste non déterminée
        other = line(3, "contract_value", amount="4000", ev="2025-01-10", ik="order-2")
        cs = self.cells(lines=[exc, val, other], rpo_cells=[rpo("S", "2025-03-31", 1000)])
        self.assertEqual((cs["total"]["status"], cs["total"]["nd_reason"]), ("not_determinable", "anonymous"))
        self.assertIn("contract_values", json.loads(cs["total"]["flags"]))

    def test_tagged_balance_and_reasons(self):
        bal = {"fact_key": "b", "group_id": "S", "counterparty": "C1", "kind": "balance", "period_end": "2025-03-31",
               "value": Decimal(250), "unit": "USD", "knowledge_date": "2025-04-30", "tier": "B", "is_tagged": True}
        cs = self.cells(tagged=[bal], rpo_cells=[rpo("S", "2025-03-31", 1000)])
        self.assertEqual((cs["total"]["value"], json.loads(cs["total"]["lineage"])), (Decimal("0.25"), ["b"]))
        # aucun RPO publié : le motif de rpo_total ; aucune vente documentée : précondition non remplie
        cs = self.cells(tagged=[bal], rpo_cells=[rpo_nd("S", "2025-03-31", "concept_unresolved")])
        self.assertEqual(cs["total"]["nd_reason"], "concept_unresolved")
        self.assertEqual(self.cells(rpo_cells=[rpo("S", "2025-03-31", 1000)], buys=False)["total"]["nd_reason"],
                         "precondition_not_met")
        # une hausse n'est jamais un numérateur ; elle reste en drapeau
        chg = dict(bal, fact_key="h", kind="change", period_end="2025-03-31")
        cs = self.cells(tagged=[chg], rpo_cells=[rpo("S", "2025-03-31", 1000)])
        self.assertEqual(cs["total"]["nd_reason"], "anonymous")
        self.assertEqual(json.loads(cs["total"]["flags"])["changes"], ["h"])

    def test_e3_reads_total_term(self):
        """E.3 porte sur le RPO de fin d'exercice : la table des exercices garde le terme `total`."""
        import inspect
        from pipeline import circularity
        src = inspect.getsource(circularity.pair_measures)
        self.assertIn('if c_["term"] != "beyond_12m"', src)
        self.assertIn('at="quarter_end"', src)


class Share(unittest.TestCase):
    """Volet 3 : exact si le reste est écrit, borné par la valeur publiée des contrats sinon ; jamais de total."""
    q = {"S": [dt.date(2025, 3, 31), dt.date(2025, 6, 30), dt.date(2025, 9, 30)]}

    def cells(self, lines, rpo_cells=(), lease=()):
        I = B.Inputs((), lines, rpo_cells, (), lease)
        return {(c["term"], c["period_end"]): c for c in B.share_cells(I, self.q, "2026-10-07")}

    def test_bound_by_contract_values(self):
        lines = [line(1, "contract_value", amount="400", ev="2025-02-01", ik="a"),
                 line(2, "change", amount="100", pe="2025-05-15", ik="a"),
                 line(3, "contract_value", amount="900", ev="2025-08-01", ik="b")]
        dens = [rpo("S", d, 1000) for d in ("2025-03-31", "2025-06-30", "2025-09-30")]
        cs = self.cells(lines, dens)
        self.assertEqual(sorted(cs), [("rpo", "2025-03-31"), ("rpo", "2025-06-30"), ("rpo", "2025-09-30")])
        c = cs[("rpo", "2025-03-31")]
        self.assertEqual((c["status"], c["value_lower"], c["value_upper"], c["bound_basis"]),
                         ("bounded", Decimal(0), Decimal("0.4"), "published_contract_value"))
        self.assertEqual(cs[("rpo", "2025-06-30")]["value_upper"], Decimal("0.5"))     # hausse après la valeur
        c = cs[("rpo", "2025-09-30")]
        self.assertEqual((c["value_upper"], json.loads(c["flags"])["capped"]), (Decimal(1), True))   # plafonnée à 1
        self.assertIn("hypothesis", json.loads(c["flags"]))

    def test_total_value_first_and_contract_without_value(self):
        lines = [line(1, "contract_value", amount="400", ev="2025-02-01", ik="a"),
                 line(2, "total_contract_value", amount="700", pe="2025-06-30")]
        cs = self.cells(lines, [rpo("S", "2025-06-30", 1000)])
        self.assertEqual(cs[("rpo", "2025-06-30")]["value_upper"], Decimal("0.7"))
        # un contrat qui paraît sans valeur : la somme ne majore rien
        lines = [line(1, "contract_value", amount="400", ev="2025-02-01", ik="a"),
                 line(2, "included_no_amount", pe="2025-03-31", ik="b")]
        c = self.cells(lines, [rpo("S", "2025-03-31", 1000)])[("rpo", "2025-03-31")]
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "not_disclosed"))
        self.assertEqual(json.loads(c["flags"])["included_no_amount"], ["obs:ck2/p/0"])

    def test_exact_remaining_and_terms_apart(self):
        lines = [line(1, "remaining", basis="lease", amount="250", pe="2025-06-30"),
                 line(2, "contract_value", amount="400", ev="2025-02-01", ik="a", tier="E"),     # EX-99 : jamais
                 line(3, "contract_value", basis="unspecified", amount="10", ev="2025-02-01", ik="z")]
        cs = self.cells(lines, [rpo("S", "2025-06-30", 1000)],
                        [rpo("S", "2025-06-30", 500, measure="lessor_lease_receipts")])
        self.assertEqual(sorted(cs), [("lease", "2025-06-30")])
        c = cs[("lease", "2025-06-30")]
        self.assertEqual((c["status"], c["value"]), ("computed", Decimal("0.5")))
        self.assertEqual(json.loads(c["flags"])["unspecified_lines"], ["obs:ck3/p/0"])

    def test_exact_date_without_denominator_and_currency(self):
        lines = [line(1, "remaining", amount="250", pe="2025-05-01")]
        c = self.cells(lines, [rpo("S", "2025-06-30", 1000)])[("rpo", "2025-05-01")]
        self.assertEqual((c["status"], c["nd_reason"]), ("not_determinable", "not_disclosed"))
        lines = [line(1, "remaining", amount="250", pe="2025-06-30", currency="EUR")]
        c = self.cells(lines, [rpo("S", "2025-06-30", 1000)])[("rpo", "2025-06-30")]
        self.assertEqual(c["nd_reason"], "mixed_currency")


class Lessor(unittest.TestCase):
    def test_lessor_receipts_sum_of_two_published(self):
        import duckdb
        con = duckdb.connect()
        con.execute((config.ROOT / "schema.sql").read_text(encoding="utf-8"))

        def f(fk, concept, pe, v, acc, kd, n_dims=0, dims_=None):
            con.execute("INSERT INTO facts (fact_key, source, group_id, accession, form, concept, period_type, period_end, "
                        "dims, n_dims, value, unit, knowledge_date, tier, is_tagged) VALUES "
                        "(?, 'instance', 'APLD', ?, '10-K', ?, 'instant', ?, ?, ?, ?, 'USD', ?, 'A', true)",
                        [fk, acc, concept, pe, dims_, n_dims, v, kd])
        f("o1", rank2.LESSOR_CONCEPTS[0], "2025-05-31", 700, "acc1", "2025-07-30")
        f("s1", rank2.LESSOR_CONCEPTS[1], "2025-05-31", 300, "acc1", "2025-07-30")
        f("o2", rank2.LESSOR_CONCEPTS[0], "2025-05-31", 710, "acc2", "2026-07-30")      # revue l'année suivante
        f("d1", rank2.LESSOR_CONCEPTS[0], "2025-05-31", 99, "acc1", "2025-07-30", 1, dims(("srt:RangeAxis", "x")))
        cs = {c["view"]: c for c in rank2.lessor_lease_receipts(con, ["APLD"], "2026-10-07")}
        self.assertEqual((cs["as_known"]["value"], json.loads(cs["as_known"]["flags"])["sum_of_two"]), (Decimal(1000), True))
        self.assertEqual(cs["revised"]["value"], Decimal(1010))


class Montage(unittest.TestCase):
    def test_qualifier_needs_client_name_and_backlog_term(self):
        qf = B.qualifier({"OpenAI", "Microsoft Corporation"})
        self.assertTrue(qf("Our remaining performance obligations exclude the contract with OpenAI."))
        self.assertFalse(qf("Our remaining performance obligations were $10 billion."))
        self.assertFalse(qf("OpenAI agreed to purchase compute capacity."))
        self.assertFalse(qf("our backlog with openai"))                  # noms tels qu'écrits, casse comprise
        self.assertIsNone(B.qualifier(set()))
        self.assertEqual(B.sellers([("C", "S", "commercial", ""), ("S", "S", "commercial", ""), ("D", "S", "financing", ""),
                                    ("E", "S", "commercial", "eliminated"), ("C", "X", "commercial", "")], {"S"}), {"S": {"C"}})

    def test_spec(self):
        sp = config.load()["montages"]["backlog"]
        self.assertEqual((sp["source"], sp["window"], sp["complement"], sp["evidence"], sp["decision"]),
                         ("backlog", 1, "all", "registry", "D-0068"))
        self.assertTrue(sp["skip_read"] and sp["skip_risk_factors"] and sp["dedupe"])
        self.assertNotIn("order", sp)                                     # des plus anciennes aux plus récentes
        self.assertEqual(sp["vocabulary"], B.VOCAB)
        self.assertEqual(tuple(sp["forms"]), B.FORMS)


if __name__ == "__main__":
    unittest.main()
