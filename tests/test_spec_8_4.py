"""Tests unitaires de §8.4 : seulement le code qu'aucun contrôle comptable n'atteint.

Lancement : python3 -m unittest discover -s tests -v
Un test ne se corrige que s'il est lui-même faux, jamais pour faire passer le code.
"""
import datetime as dt
import json
import unittest
from decimal import Decimal

from pipeline import assemble, blocks, documents, links, load, phase1, quantities, reader, spacex_d1, textnorm, xbrl


def instance(body, us_gaap_version="2024"):
    """Instance XBRL extraite minimale (un contexte de trimestre, un d'instant, des unités)."""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:us-gaap="http://fasb.org/us-gaap/{us_gaap_version}" xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
  xmlns:acme="http://acme.example/20250331">
  <xbrli:context id="q1"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000001</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-03-31</xbrli:endDate></xbrli:period></xbrli:context>
  <xbrli:context id="i1"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000001</xbrli:identifier>
    <xbrli:segment><xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">acme:CloudMember</xbrldi:explicitMember></xbrli:segment></xbrli:entity>
    <xbrli:period><xbrli:instant>2025-03-31</xbrli:instant></xbrli:period></xbrli:context>
  <xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
  <xbrli:unit id="eur"><xbrli:measure>iso4217:EUR</xbrli:measure></xbrli:unit>
  <xbrli:unit id="shares"><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unit>
  <xbrli:unit id="pure"><xbrli:measure>xbrli:pure</xbrli:measure></xbrli:unit>
  <xbrli:unit id="usdPerShare"><xbrli:divide>
    <xbrli:unitNumerator><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unitNumerator>
    <xbrli:unitDenominator><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unitDenominator></xbrli:divide></xbrli:unit>
  {body}
</xbrli:xbrl>""".encode("utf-8")


def by_concept(facts):
    return {f["concept"]: f for f in facts}


class ScaleSignDecimalsFixedZero(unittest.TestCase):
    """Une instance extraite est déjà à l'échelle : scale ne se réapplique pas, le signe est
    dans la valeur, decimals est une précision, un zéro fixe (ixt:fixed-zero) vaut 0 (§7.3)."""

    def setUp(self):
        facts, _, _ = xbrl.parse_instance(instance("""
  <us-gaap:NetIncomeLoss contextRef="q1" unitRef="usd" decimals="-6" id="a">-1500000000</us-gaap:NetIncomeLoss>
  <us-gaap:EffectiveIncomeTaxRateContinuingOperations contextRef="q1" unitRef="pure" decimals="3">-0.025</us-gaap:EffectiveIncomeTaxRateContinuingOperations>
  <us-gaap:PaymentsOfDividends contextRef="q1" unitRef="usd" decimals="INF">0</us-gaap:PaymentsOfDividends>
  <us-gaap:Goodwill contextRef="i1" unitRef="usd" decimals="-5">250000000</us-gaap:Goodwill>
  <us-gaap:InterestExpense contextRef="q1" unitRef="usd" xsi:nil="true"/>"""))
        self.f = by_concept(facts)

    def test_scale_not_reapplied_negative_value_kept(self):
        f = self.f["us-gaap:NetIncomeLoss"]
        self.assertEqual(f["value"], Decimal("-1500000000"))
        self.assertEqual(f["decimals"], -6)

    def test_negative_scale_percent_already_applied(self):
        # un pourcentage balisé avec scale="-2" arrive déjà divisé : -0.025, jamais -2.5 ni -0.00025
        self.assertEqual(self.f["us-gaap:EffectiveIncomeTaxRateContinuingOperations"]["value"], Decimal("-0.025"))

    def test_decimals_is_precision_not_multiplier(self):
        f = self.f["us-gaap:Goodwill"]
        self.assertEqual(f["value"], Decimal("250000000"))
        self.assertEqual(f["decimals"], -5)
        self.assertFalse(f["decimals_inf"])

    def test_decimals_inf(self):
        f = self.f["us-gaap:PaymentsOfDividends"]
        self.assertIsNone(f["decimals"])
        self.assertTrue(f["decimals_inf"])

    def test_fixed_zero_is_zero_not_absent(self):
        f = self.f["us-gaap:PaymentsOfDividends"]
        self.assertEqual(f["value"], Decimal("0"))
        self.assertFalse(f["is_nil"])

    def test_nil_is_absent_not_zero(self):
        f = self.f["us-gaap:InterestExpense"]
        self.assertTrue(f["is_nil"])
        self.assertIsNone(f["value"])

    def test_html_cell_dash_is_fixed_zero(self):
        # états HTML (D1) : un tiret est un zéro publié, une cellule vide est une absence
        self.assertEqual(spacex_d1._num("—"), Decimal("0"))
        self.assertEqual(spacex_d1._num("-"), Decimal("0"))
        self.assertEqual(spacex_d1._num("$ —"), Decimal("0"))
        self.assertIsNone(spacex_d1._num(""))

    def test_html_cell_parentheses_are_negative(self):
        self.assertEqual(spacex_d1._num("(1,234)"), Decimal("-1234"))
        self.assertEqual(spacex_d1._num("$(955)"), Decimal("-955"))
        self.assertEqual(spacex_d1._num("16,055"), Decimal("16055"))

    def test_text_scale_of_a_table(self):
        # un tableau « in millions » affiche des nombres nus qui valent aussi à cette échelle
        vals = reader.text_values("(in millions) | Revenue | 1,234 | (56)")
        self.assertIn(Decimal("1234000000"), vals)
        self.assertIn(Decimal("1234"), vals)
        self.assertIn(Decimal("3.5") * 10 ** 9, reader.text_values("a facility of $3.5 billion"))


class TextNormalizer(unittest.TestCase):
    """Entités HTML, espace insécable, nom coupé par une balise, constructions iXBRL (§9.2)."""

    def lines(self, fragment):
        return [t for t, _ in textnorm.linearize(textnorm.parse_html(fragment.encode("utf-8")))]

    def test_html_entities_and_typographic_quotes(self):
        self.assertEqual(self.lines("<p>AT&amp;T&#160;Inc. signed the &#8220;Agreement&#8221; &mdash; today</p>"),
                         ['AT&T Inc. signed the "Agreement" - today'])

    def test_non_breaking_space(self):
        self.assertEqual(textnorm.norm_for_match("Microsoft Corporation (“Microsoft”)"),
                         'Microsoft Corporation ("Microsoft")')

    def test_name_split_by_a_tag(self):
        raw = "<p>an agreement with Core<span style='font-weight:bold'>Weave</span>, Inc. dated</p>"
        self.assertEqual(self.lines(raw), ["an agreement with CoreWeave, Inc. dated"])
        # la citation se retrouve aussi dans le fichier brut, balise au milieu du nom
        r = textnorm.locate_in_raw(raw.encode("utf-8"), "with CoreWeave, Inc.")
        self.assertIsNotNone(r)
        self.assertEqual(raw.encode("utf-8")[r[0]:r[1]].decode(), "with Core<span style='font-weight:bold'>Weave</span>, Inc.")

    def test_ixbrl_constructs(self):
        raw = ("<div><ix:header><ix:hidden><ix:nonnumeric name='dei:EntityRegistrantName'>HIDDEN</ix:nonnumeric>"
               "</ix:hidden></ix:header><p>Revenue was $<ix:nonfraction name='us-gaap:Revenues' scale='6' "
               "decimals='-6'>1,234</ix:nonfraction> million<ix:exclude> EXCLUDED</ix:exclude>.</p>"
               "<p style='display:none'>INVISIBLE</p></div>")
        out = self.lines(raw)
        self.assertEqual(out, ["Revenue was $1,234 million."])

    def test_decoding(self):
        self.assertEqual(textnorm.decode(b"\xef\xbb\xbfCaf\xc3\xa9"), "Café")      # BOM UTF-8 retirée
        self.assertEqual(textnorm.decode(b"Caf\xe9 \x93x\x94"), "Café “x”")        # repli cp1252


class UnitsAndCurrencies(unittest.TestCase):

    def setUp(self):
        facts, _, _ = xbrl.parse_instance(instance("""
  <us-gaap:Revenues contextRef="q1" unitRef="usd" decimals="-6">1000000</us-gaap:Revenues>
  <us-gaap:OtherIncome contextRef="q1" unitRef="eur" decimals="-6">2000000</us-gaap:OtherIncome>
  <us-gaap:EarningsPerShareBasic contextRef="q1" unitRef="usdPerShare" decimals="2">1.25</us-gaap:EarningsPerShareBasic>
  <us-gaap:WeightedAverageNumberOfSharesOutstandingBasic contextRef="q1" unitRef="shares" decimals="-5">100000</us-gaap:WeightedAverageNumberOfSharesOutstandingBasic>"""))
        self.f = by_concept(facts)

    def test_units_and_currency(self):
        self.assertEqual((self.f["us-gaap:Revenues"]["unit"], self.f["us-gaap:Revenues"]["currency"]), ("USD", "USD"))
        self.assertEqual((self.f["us-gaap:OtherIncome"]["unit"], self.f["us-gaap:OtherIncome"]["currency"]), ("EUR", "EUR"))

    def test_ratio_units_have_no_currency(self):
        eps = self.f["us-gaap:EarningsPerShareBasic"]
        self.assertEqual(eps["unit"], "USD/shares")
        self.assertIsNone(eps["currency"])
        sh = self.f["us-gaap:WeightedAverageNumberOfSharesOutstandingBasic"]
        self.assertEqual((sh["unit"], sh["currency"]), ("shares", None))

    def test_line_with_unit_and_other_currency_is_rejected(self):
        block = {"text": "We paid EUR 5 million.", "candidate_facts": []}
        errs, _ = load.semantic_errors({"quote": "We paid EUR 5 million.", "amount": "5000000", "unit": "USD",
                                        "currency": "EUR", "amount_origin": "verbatim"}, block)
        self.assertIn("unité et devise incohérentes", errs)


class IdentityAndPeriods(unittest.TestCase):
    """Identité sans version de taxonomie ; trimestres choisis par dates, sans fy ni fp (§7.2, §7.3)."""

    def test_identity_without_taxonomy_version(self):
        body = '<us-gaap:Revenues contextRef="q1" unitRef="usd" decimals="-6">1000000</us-gaap:Revenues>'
        f23 = xbrl.parse_instance(instance(body, "2023"))[0][0]
        f25 = xbrl.parse_instance(instance(body, "2025"))[0][0]
        self.assertEqual(f23["concept"], f25["concept"])
        self.assertEqual(f23["concept"], "us-gaap:Revenues")
        self.assertEqual((f23["taxonomy_version"], f25["taxonomy_version"]), ("2023", "2025"))

    def test_dimension_members_without_version(self):
        f = xbrl.parse_instance(instance(
            '<us-gaap:Goodwill contextRef="i1" unitRef="usd" decimals="-6">5000000</us-gaap:Goodwill>', "2022"))[0][0]
        self.assertEqual(f["dims"], [("us-gaap:StatementBusinessSegmentsAxis", "acme:CloudMember")])
        self.assertEqual(f["framework"], "us_gaap")

    def test_quarters_selected_by_dates_without_fy_fp(self):
        # exercice de 52-53 semaines : bornes à quelques jours des fins de mois, aucun champ fy ni fp
        d = dt.date
        cal = [{"start": d(2024, 1, 29), "end": d(2024, 4, 28), "fy_end": d(2025, 1, 26), "q": 1},
               {"start": d(2024, 4, 29), "end": d(2024, 7, 28), "fy_end": d(2025, 1, 26), "q": 2},
               {"start": d(2024, 7, 29), "end": d(2024, 10, 27), "fy_end": d(2025, 1, 26), "q": 3}]

        def v(ps, pe, val, key):
            return {"period_start": ps, "period_end": pe, "value": val, "fact_key": key, "accession": key,
                    "knowledge_date": d(2024, 11, 20)}
        values = [v(d(2024, 1, 29), d(2024, 4, 28), "100", "q1"),
                  v(d(2024, 1, 29), d(2024, 7, 28), "250", "h1"),          # cumul de six mois seulement
                  v(d(2024, 7, 29), d(2024, 10, 26), "180", "q3")]         # fin à un jour de l'exercice
        out = {r["q"]: r for r in quantities.derive_quarters(values, cal, instant=False)}
        self.assertEqual((out[1]["value"], out[1]["method"]), (Decimal("100"), "direct"))
        self.assertEqual((out[2]["value"], out[2]["method"]), (Decimal("150"), "ytd_difference"))
        self.assertEqual(out[2]["lineage"], ["h1", "q1"])           # le trimestre calculé garde ses termes
        self.assertEqual((out[3]["value"], out[3]["method"]), (Decimal("180"), "direct"))

    def test_cumulative_never_taken_for_a_quarter(self):
        d = dt.date
        cal = [{"start": d(2025, 1, 1), "end": d(2025, 3, 31), "fy_end": d(2025, 12, 31), "q": 1},
               {"start": d(2025, 4, 1), "end": d(2025, 6, 30), "fy_end": d(2025, 12, 31), "q": 2}]
        values = [{"period_start": d(2025, 1, 1), "period_end": d(2025, 6, 30), "value": "500", "fact_key": "h1",
                   "accession": "a", "knowledge_date": d(2025, 8, 1)}]
        out = {r["q"]: r for r in quantities.derive_quarters(values, cal, instant=False)}
        self.assertEqual(out[2]["status"], "not_determinable")   # pas de Q1 : le cumul ne passe pas pour Q2
        self.assertEqual(out[1]["status"], "not_determinable")


class OverlapBlocksASum(unittest.TestCase):
    """Aucune somme à travers un chevauchement non résolu ni entre devises (§7.6 d et b)."""

    def edge(self, key, unit="USD", tier="A"):
        return {"link_key": key, "tier": tier, "from_group": "NVDA", "to_group": "CRWV", "_obs": {"unit": unit}}

    def cell(self, keys):
        return {"measure": "counterparty_exposure", "subject": "NVDA", "counterparty": "CRWV",
                "period_end": "2025-12-31", "breakdown_key": "exposed_assets/cost/equity_investment",
                "as_of": "2026-10-07", "status": "computed", "nd_reason": None, "value": Decimal("3"),
                "flags": json.dumps({"links": keys})}

    def test_unresolved_overlap_blocks_the_sum(self):
        c = self.cell(["e1", "e2"])
        rels = [{"a_key": "e1", "b_key": "e2", "resolution": "unresolved"}]
        excl = assemble.invariants([c], [self.edge("e1"), self.edge("e2")], rels, None)
        self.assertEqual((c["status"], c["nd_reason"], c["value"]), ("blocked_overlap", "blocked_overlap", None))
        self.assertEqual([x["invariant"] for x in excl], ["d"])

    def test_resolved_overlap_does_not_block(self):
        c = self.cell(["e1", "e2"])
        rels = [{"a_key": "e1", "b_key": "e2", "resolution": "resolved_rule"}]
        self.assertEqual(assemble.invariants([c], [self.edge("e1"), self.edge("e2")], rels, None), [])
        self.assertEqual(c["value"], Decimal("3"))

    def test_mixed_currencies_block_the_sum(self):
        c = self.cell(["e1", "e2"])
        excl = assemble.invariants([c], [self.edge("e1"), self.edge("e2", unit="EUR")], [], None)
        self.assertEqual([x["invariant"] for x in excl], ["b"])
        self.assertEqual((c["status"], c["nd_reason"], c["value"]), ("not_determinable", "mixed_currency", None))


class DeterministicIdentifiers(unittest.TestCase):
    """Les identifiants ne dépendent que du contenu, jamais d'un ordre ni d'un rang d'occurrence (§9.6)."""

    def test_content_key_ignores_candidate_order_and_occurrence(self):
        a = {"fact_key": "acc/doc#1", "concept": "us-gaap:Revenues", "value": "1", "unit": "USD",
             "period_start": "2025-01-01", "period_end": "2025-03-31", "dims": []}
        b = dict(a, fact_key="acc/doc#2", concept="us-gaap:CostOfRevenue", value="2")
        a2 = dict(a, fact_key="other/doc#99")                    # autre occurrence du même fait
        k1 = blocks.content_key("Note 3. Revenue", [a, b])
        self.assertEqual(k1, blocks.content_key("Note 3. Revenue", [b, a2]))
        self.assertNotEqual(k1, blocks.content_key("Note 3. Revenue.", [a, b]))
        self.assertEqual(len(k1), 64)

    def test_link_key_is_stable(self):
        self.assertEqual(links._key("obs", "abc", 1), links._key("obs", "abc", 1))
        self.assertNotEqual(links._key("obs", "abc", 1), links._key("obs", "abc", 2))

    def test_occurrence_rank_is_stable(self):
        body = ('<us-gaap:Revenues contextRef="q1" unitRef="usd" decimals="-6">1</us-gaap:Revenues>'
                '<us-gaap:CostOfRevenue contextRef="q1" unitRef="usd" decimals="-6">2</us-gaap:CostOfRevenue>')
        r1 = [(f["concept"], f["occ_rank"]) for f in xbrl.parse_instance(instance(body))[0]]
        r2 = [(f["concept"], f["occ_rank"]) for f in xbrl.parse_instance(instance(body))[0]]
        self.assertEqual(r1, r2)
        self.assertEqual([r for _, r in r1], [1, 2])

    def test_observation_key(self):
        b = {"content_key": "c" * 64, "block_kind": "debt_note", "cik": "1", "accession": "a", "document": "d",
             "group_id": "NVDA", "form": "10-K", "knowledge_date": "2025-02-26"}
        line = {"kind": "observation", "pass_id": "2026-10-07T16:30:00Z"}
        k = load._obs_row(line, b, 3, "valid", [], None)["obs_key"]
        self.assertEqual(k, "c" * 64 + "/2026-10-07T16:30:00Z/3")
        self.assertEqual(k, load._obs_row(line, b, 3, "valid", [], None)["obs_key"])


class Tier(unittest.TestCase):
    """Niveau de preuve (§2.2) : A audité, B revu, C autre passage déposé, D contrat, E pointeur."""

    def test_tier_by_form(self):
        self.assertEqual(phase1.tier_for_form("10-K"), ("A", "audited", "filed"))
        self.assertEqual(phase1.tier_for_form("10-Q/A"), ("B", "reviewed", "filed"))
        self.assertEqual(phase1.tier_for_form("8-K"), (None, None, None))     # attend son instance

    def test_tier_by_document(self):
        c = documents._classify
        self.assertEqual(c("instance", "10-K", None, None)[3], "A")
        self.assertEqual(c("instance", "10-Q", None, None)[3], "B")
        self.assertEqual(c("instance", "S-4", None, None)[3], "C")
        self.assertEqual(c("exhibit", "8-K", "EX-10.1", "1.01")[3], "D")
        self.assertEqual(c("exhibit", "8-K", "EX-4.1", "2.03")[3], "D")
        self.assertEqual(c("main", "DEF 14A", None, None)[3], "C")
        self.assertEqual(c("main", "8-K", None, "1.01,9.01")[3], "C")
        self.assertEqual(c("main", "8-K", None, "2.02,9.01")[:2], ("furnished", "pointer"))
        self.assertEqual(c("main", "8-K", None, "2.02,9.01")[3], "E")
        self.assertEqual(c("main", "DRS", None, None)[3], "E")


class QuoteVerification(unittest.TestCase):
    """Citation retrouvée mot pour mot (après normalisation), contrepartie présente, montant balisé (§7.4)."""

    block = {"text": "On March 30, 2026, CoreWeave entered into a Credit Agreement with MUFG Bank, Ltd. "
                     "providing for loans of up to $8.5 billion. The company’s net loss was $(1,200) million.",
             "candidate_facts": [{"fact_key": "k1", "concept": "us-gaap:NetIncomeLoss", "value": "-1200000000",
                                  "unit": "USD", "period_start": "2025-01-01", "period_end": "2025-12-31", "dims": []}]}

    def test_verbatim_quote_after_normalization(self):
        errs, _ = load.semantic_errors({"quote": "Credit Agreement with MUFG Bank, Ltd. providing for loans",
                                        "counterparty_name": "MUFG Bank, Ltd.", "counterparty_evidence": "named"},
                                       self.block)
        self.assertEqual(errs, [])
        errs, _ = load.semantic_errors({"quote": "The company's net loss"}, self.block)  # apostrophe droite
        self.assertEqual(errs, [])

    def test_paraphrase_is_rejected(self):
        errs, _ = load.semantic_errors({"quote": "Credit Agreement with MUFG providing loans"}, self.block)
        self.assertIn("citation introuvable mot pour mot dans le bloc", errs)

    def test_counterparty_must_be_in_block(self):
        errs, _ = load.semantic_errors({"quote": "CoreWeave entered into a Credit Agreement",
                                        "counterparty_name": "JPMorgan Chase Bank, N.A.",
                                        "counterparty_evidence": "named"}, self.block)
        self.assertIn("contrepartie absente du bloc", errs)

    def test_tagged_reference_amount_in_absolute_value(self):
        line = {"quote": "net loss was $(1,200) million", "amount": "1200000000",
                "amount_origin": "tagged_reference", "candidate_fact_key": "k1"}
        self.assertEqual(load.semantic_errors(line, self.block)[0], [])
        bad = dict(line, amount="1300000000")
        self.assertIn("montant différent du fait candidat", load.semantic_errors(bad, self.block)[0])

    def test_narrative_amount_equal_to_a_tagged_fact_of_the_same_date(self):
        line = {"quote": "net loss was $(1,200) million", "amount": "1200000000", "amount_origin": "narrative_only",
                "period_end": "2025-12-31"}
        self.assertIn("montant présent dans un fait candidat : tagged_reference attendu",
                      load.semantic_errors(line, self.block)[0])
        other_date = dict(line, period_end="2024-12-31")
        self.assertEqual(load.semantic_errors(other_date, self.block)[0], [])


if __name__ == "__main__":
    unittest.main()
