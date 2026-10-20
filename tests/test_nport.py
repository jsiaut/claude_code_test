"""Volet F de D-0058 : positions de SoftBank dans les Form N-PORT Data Sets et mesure nport_price_to_par.

Lancement : python3 -m unittest discover -s tests -t .
"""
import io
import json
import tempfile
import unittest
import zipfile
from decimal import Decimal
from pathlib import Path

import pandas as pd

from pipeline import nport as P

C = {"tables": {"holding": "FUND_REPORTED_HOLDING", "identifiers": "IDENTIFIERS", "debt": "DEBT_SECURITY",
                "submission": "SUBMISSION", "registrant": "REGISTRANT", "fund": "FUND_REPORTED_INFO"},
     "holding": {"accession": "ACCESSION_NUMBER", "holding_id": "HOLDING_ID", "issuer_name": "ISSUER_NAME",
                 "issuer_lei": "ISSUER_LEI"},
     "identifiers": {"holding_id": "HOLDING_ID"}, "debt": {"holding_id": "HOLDING_ID"},
     "submission": {"accession": "ACCESSION_NUMBER"}, "registrant": {"accession": "ACCESSION_NUMBER"},
     "fund": {"accession": "ACCESSION_NUMBER"}}


def tsv(rows):
    return "\n".join("\t".join(r) for r in rows) + "\n"


class Scan(unittest.TestCase):
    def test_keeps_softbank_names_and_their_leis(self):
        hold = [["ACCESSION_NUMBER", "HOLDING_ID", "ISSUER_NAME", "ISSUER_LEI", "BALANCE"],
                ["A1", "1", "SoftBank Group Corp", "LEI-SB", "100"],
                ["A1", "2", "SBG 5.125 2027", "LEI-SB", "50"],          # même LEI, autre nom : gardée
                ["A2", "3", "Softbank Corp.", "N/A", "10"],
                ["A2", "4", "Toyota Motor Corp", "LEI-T", "70"]]
        with tempfile.TemporaryDirectory() as d:
            zp = Path(d) / "2025q1_nport.zip"
            with zipfile.ZipFile(zp, "w") as z:
                z.writestr("FUND_REPORTED_HOLDING.tsv", tsv(hold))
                z.writestr("IDENTIFIERS.tsv", tsv([["HOLDING_ID", "IDENTIFIER_ISIN"], ["1", "XS1"], ["4", "JP9"]]))
                z.writestr("DEBT_SECURITY.tsv", tsv([["HOLDING_ID", "MATURITY_DATE"], ["2", "2027-09-19"]]))
                z.writestr("SUBMISSION.tsv", tsv([["ACCESSION_NUMBER", "FILING_DATE"], ["A1", "2025-02-27"], ["A2", "2025-02-28"], ["A3", "x"]]))
                z.writestr("REGISTRANT.tsv", tsv([["ACCESSION_NUMBER", "CIK"], ["A1", "1"], ["A3", "3"]]))
                z.writestr("FUND_REPORTED_INFO.tsv", tsv([["ACCESSION_NUMBER", "SERIES_ID"], ["A2", "S2"]]))
            out, stats, found = P.scan_archive(zp, leis=(), c=C)
        self.assertEqual(sorted(out["holding"]["HOLDING_ID"]), ["1", "2", "3"])
        self.assertEqual(found, ["LEI-SB"])                       # « N/A » n'est pas un LEI
        self.assertEqual(stats["by_name"], 2)
        self.assertEqual(sorted(out["identifiers"]["HOLDING_ID"]), ["1"])
        self.assertEqual(sorted(out["submission"]["ACCESSION_NUMBER"]), ["A1", "A2"])


class Measure(unittest.TestCase):
    def positions(self):
        base = {"unit": "PA", "asset_cat": "DBT", "payoff": "Long", "currency": "USD", "issuer_name": "SOFTBANK GROUP CORP",
                "title": "SOFTBANK 5.125 09/19/27", "maturity": "2027-09-19", "cusip": "000000000", "cik": None}
        rows = [  # série S1 : dépôt initial puis amendement, qui le remplace
            dict(base, series_id="S1", report_date="2025-03-31", filing_date="2025-05-20", accession="A1",
                 isin="XS1684384867", value_local="90", balance="100"),
            dict(base, series_id="S1", report_date="2025-03-31", filing_date="2025-06-02", accession="A1-amd",
                 isin="XS1684384867", value_local="95", balance="100"),
            dict(base, series_id="S2", report_date="2025-03-31", filing_date="2025-05-21", accession="A2",
                 isin="XS1684384867", value_local="180", balance="200"),
            dict(base, series_id="S3", report_date="2025-03-31", filing_date="2025-05-22", accession="A3",
                 isin="N/A", value_local="50", balance="50", cusip="J7596PAW9"),        # sans ISIN : CUSIP
            dict(base, series_id="S4", report_date="2025-03-31", filing_date="2025-05-22", accession="A4",
                 isin="JP3436100006", value_local="10", balance="10", unit="NS", asset_cat="EC")]   # actions : hors mesure
        return pd.DataFrame(rows)

    def test_latest_filing_of_each_series_replaces_the_earlier(self):
        p = P.latest_by_fund(self.positions())
        self.assertEqual(sorted(p["accession"]), ["A1-amd", "A2", "A3", "A4"])

    def test_closed_end_funds_without_series_are_their_registrants(self):
        x = self.positions().iloc[[1, 2]].assign(series_id=None, cik=["0001190935", "0001554697"])
        self.assertEqual(sorted(P.latest_by_fund(x)["accession"]), ["A1-amd", "A2"])

    def test_ratio_by_security_and_date(self):
        r = P.price_to_par(self.positions()).set_index("security")
        self.assertEqual(r.loc["XS1684384867", "ratio"], Decimal("275") / Decimal("300"))
        self.assertEqual(int(r.loc["XS1684384867", "n_series"]), 2)
        self.assertEqual(r.loc["XS1684384867", "principal"], Decimal("300"))
        self.assertIn("CUSIP:J7596PAW9", r.index)
        self.assertNotIn("JP3436100006", r.index)

    def test_cusip_only_position_takes_the_isin_given_to_the_same_cusip(self):
        x = self.positions()
        x.loc[[0, 1, 2, 3], "cusip"] = "J7596PAN9"
        x.loc[3, "isin"] = None
        self.assertEqual(P.security_keys(x)[3], "XS1684384867")
        x.loc[4, "cusip"] = "J7596PAN9"                     # même CUSIP sous deux ISIN : pas de rattachement
        self.assertEqual(P.security_keys(x)[3], "CUSIP:J7596PAN9")
        self.assertIsNone(P.security_keys(pd.DataFrame({"isin": ["N/A"], "cusip": ["000000000"]}))[0])

    def test_short_positions_and_other_issuers_stay_out(self):
        x = self.positions().iloc[[1]]
        rows = [x.assign(payoff="Short", accession="S")]
        # titre de Sprint déclaré sous le LEI de SoftBank Group : nom de Sprint
        rows.append(x.assign(isin="US85208NAE04", issuer_name="SPRINT SPECTRUM / SPEC I", title="Sprint Spectrum Co LLC"))
        # titre de Drawbridge déclaré sous le nom de la société mère : l'intitulé ne nomme jamais SoftBank
        rows.append(x.assign(isin="US26150TAA79", issuer_name="SoftBank Group Corp.", title="Drawbridge Special Opportunities Fund, LP"))
        kept, steps = P.selection(pd.concat([x] + rows, ignore_index=True))
        self.assertEqual(list(kept["security"]), ["XS1684384867"])
        self.assertEqual(steps["not_long"], 1)
        self.assertEqual(steps["securities_out"], ["US26150TAA79", "US85208NAE04"])


class Publication(unittest.TestCase):
    def test_last_modified_is_read_from_the_response_headers(self):
        from requests.structures import CaseInsensitiveDict
        h = CaseInsensitiveDict({"last-modified": "Thu, 08 Oct 2026 14:02:11 GMT"})   # en-têtes de requests
        self.assertEqual(P._published(h), ("Thu, 08 Oct 2026 14:02:11 GMT", "2026-10-08"))
        self.assertEqual(P._published(None), (None, None))

    def test_second_pass_counts_as_applied(self):
        self.assertEqual(P.applied({"leis_found": ["A", "B"], "leis_applied": []}), {"A", "B"})


class Leis(unittest.TestCase):
    def test_a_lei_is_softbank_s_only_when_most_of_its_positions_carry_the_name(self):
        hold = pd.DataFrame({"ISSUER_NAME": ["SoftBank Group Corp", "SoftBank Group Corp.", "SPRINT SPECTRUM / SPEC I",
                                             "SoftBank Group Corp.", "Sprint Corp", "Sprint Corporation",
                                             "CDS_SN SOFTBANK GROUP CORP", "Goldman Sachs International", "SoftBank Corp."],
                             "ISSUER_LEI": ["LEI-SBG", "LEI-SBG", "LEI-SBG", "LEI-SPRINT", "LEI-SPRINT", "LEI-SPRINT",
                                            "LEI-GSI", "LEI-GSI", "N/A"]})
        ev = P.lei_evidence(hold, c=C)
        self.assertEqual(ev["LEI-SBG"], {"positions": 3, "named": 2})
        self.assertNotIn("N/A", ev)
        self.assertEqual(P.accepted(ev), {"LEI-SBG"})      # Sprint 1 sur 3, Goldman 1 sur 2 : refusés


class Render(unittest.TestCase):
    def test_security_title_names_issuer_coupon_maturity_and_currency(self):
        from pipeline.render import nport_title
        fl = {"issuer": "SOFTBANK GROUP CORP", "coupon": "5.125", "maturity": "2027-09-19", "currency": "USD"}
        self.assertEqual(nport_title("XS1684384867", fl), "SoftBank Group 5,125 %, échéance 2027-09-19 (USD, XS1684384867)")
        fl = {"issuer": "SOFTBANK CORP", "coupon": "6", "maturity": "2035-07-09", "currency": "EUR"}
        self.assertEqual(nport_title("XS3317460700", fl), "SoftBank Corp. 6 %, échéance 2035-07-09 (EUR, XS3317460700)")


# -- D-0065 : non-cotés du modèle --------------------------------------------------------------------

def ent(eid, name, cik=None, status="confirmed", kind="entity", ref="none"):
    from pipeline.graph import normalize_name
    return {"entity_id": eid, "record_kind": kind, "ref": ref, "name": name, "normalized_name": normalize_name(name),
            "cik": cik, "status": status, "valid_from": "none", "valid_to": None, "legal_date": None,
            "common_control_start": None, "consolidation_treatment": None}


def mem(eid, ref, frm="none"):
    return {"entity_id": eid, "record_kind": "membership", "ref": ref, "name": None, "normalized_name": None,
            "status": "confirmed", "valid_from": frm, "valid_to": None, "legal_date": None, "common_control_start": None,
            "consolidation_treatment": "parent"}


ROWS = [ent("e:ant", "Anthropic PBC"), mem("e:ant", "LAB:ANTHROPIC"),
        ent("e:oai", "OpenAI Global, LLC"), mem("e:oai", "LAB:OPENAI"),
        ent("e:xai", "X.AI Holdings Corp."), mem("e:xai", "SPCX"),
        ent("e:spx", "SPACE EXPLORATION TECHNOLOGIES CORP", cik="1181412"), mem("e:spx", "SPCX"),
        ent("e:cru", "Crusoe Energy Systems, Inc."), mem("e:cru", "CP:crusoe energy systems inc"),
        ent("e:mis", "Mistral AI"), mem("e:mis", "CP:mistral ai"),
        ent("e:syn", "a syndicate of banks"), ent("e:pen", "Scale AI", status="pending"),
        ent("e:mix", "XIUC, X., x.AI, and Elon Musk")]
CFG = {"labs": ["OpenAI", "Anthropic"], "discovery": {"lexicon": {"seed": [{"term": "xAI"}, {"term": "X.AI"}],
                                                                    "confirmed": [{"term": "X Corp"}]},
                                                       "non_filer": {"lexicon": [{"term": "Lambda Labs"}]}}}

UC = {"tables": C["tables"],
      "holding": {"accession": "ACCESSION_NUMBER", "holding_id": "HOLDING_ID", "issuer_name": "ISSUER_NAME",
                  "title": "ISSUER_TITLE", "fair_value_level": "FAIR_VALUE_LEVEL", "asset_cat": "ASSET_CAT"},
      "identifiers": {"holding_id": "HOLDING_ID"}, "debt": {"holding_id": "HOLDING_ID"},
      "submission": {"accession": "ACCESSION_NUMBER"}, "registrant": {"accession": "ACCESSION_NUMBER"},
      "fund": {"accession": "ACCESSION_NUMBER"}}


class UnlistedLexicon(unittest.TestCase):
    def test_parts_and_dotless_variants(self):
        lx = P.lexicon(ROWS, CFG)
        k, legal = lx["keep"], lx["legal"]
        self.assertEqual(legal["anthropic pbc"], "e:ant")
        self.assertEqual(legal["xai holdings corp"], "e:xai")             # variante sans points du nom d'origine
        self.assertEqual(k["crusoe energy systems"], "b")                 # base de deux mots au moins
        self.assertNotIn("anthropic", legal)                              # nom court : jamais une dénomination
        self.assertEqual(k["anthropic"], "c")
        self.assertEqual(k["mistral ai"], "d")                            # nom sans forme juridique : gardé, non rattaché
        self.assertNotIn("a syndicate of banks", k)                       # description
        self.assertNotIn("scale ai", k)                                   # entité en attente
        self.assertFalse(any("musk" in s for s in k))                     # suite de parties jointes par « and »
        self.assertTrue(lx["version"].startswith("lx-"))
        self.assertEqual(lx["version"], P.lexicon(ROWS, CFG)["version"])

    def test_attribution_by_a_leading_legal_name(self):
        legal = P.lexicon(ROWS, CFG)["legal"]
        self.assertEqual(P.attribute("ANTHROPIC, PBC Series F Preferred", legal), ("e:ant", "anthropic pbc"))
        self.assertEqual(P.attribute("XAI HOLDINGS CORP", legal)[0], "e:xai")
        self.assertEqual(P.attribute("Sydecar Anthropic PBC SPV LLC", legal), (None, None))    # véhicule : ne commence pas
        self.assertEqual(P.attribute("DXYZ OpenAI I LLC", legal), (None, None))
        self.assertEqual(P.attribute("Crusoe Energy Systems LLC", legal), (None, None))      # autre forme juridique
        self.assertEqual(P.attribute("OpenAI Global LLC Holdings LP", legal), (None, "openai global llc"))


class UnlistedScan(unittest.TestCase):
    def test_keeps_self_valued_positions_and_counts_the_quoted_ones(self):
        hold = [["ACCESSION_NUMBER", "HOLDING_ID", "ISSUER_NAME", "ISSUER_TITLE", "FAIR_VALUE_LEVEL", "ASSET_CAT"],
                ["A1", "1", "Anthropic PBC", "Series E Preferred", "3", "EP"],
                ["A1", "2", "Space Exploration Technologies Corp", "Class A", "1", "EC"],      # cotée : comptée seulement
                ["A1", "3", "MW LSVC SPV LLC", "OpenAI Global units", "N/A", "OTHER"],         # par l'intitulé : gardée
                ["A2", "4", "Toyota Motor Corp", "Toyota", "1", "EC"],
                ["A2", "5", "Lambda Labs Inc", "Series C", "", "EP"]]
        lx = P.lexicon(ROWS, CFG)
        with tempfile.TemporaryDirectory() as d:
            zp = Path(d) / "2025q1_nport.zip"
            with zipfile.ZipFile(zp, "w") as z:
                z.writestr("FUND_REPORTED_HOLDING.tsv", tsv(hold))
                z.writestr("IDENTIFIERS.tsv", tsv([["HOLDING_ID", "IDENTIFIER_ISIN"], ["1", "N/A"], ["4", "JP9"]]))
                z.writestr("DEBT_SECURITY.tsv", tsv([["HOLDING_ID", "MATURITY_DATE"]]))
                z.writestr("SUBMISSION.tsv", tsv([["ACCESSION_NUMBER", "REPORT_DATE"], ["A1", "2025-03-31"], ["A2", "2025-03-31"]]))
                z.writestr("REGISTRANT.tsv", tsv([["ACCESSION_NUMBER", "CIK"], ["A1", "1"], ["A2", "2"]]))
                z.writestr("FUND_REPORTED_INFO.tsv", tsv([["ACCESSION_NUMBER", "SERIES_ID"], ["A1", "S1"]]))
            out, stats, cnt = P.scan_unlisted(zp, lx, c=UC)
        self.assertEqual(sorted(out["holding"]["HOLDING_ID"]), ["1", "3", "5"])
        self.assertEqual(stats["matched"], 4)
        self.assertEqual(stats["matched_by_level"], {"": 1, "1": 1, "3": 1, "N/A": 1})
        c = {(r.kind, r.key, r.level): r.n for r in cnt.itertuples()}
        self.assertEqual(c[("entity", "e:spx", "1")], 1)
        self.assertEqual(c[("entity", "e:ant", "3")], 1)
        self.assertEqual(c[("string", "openai global", "N/A")], 1)   # base la plus longue contenue
        self.assertEqual(sorted(out["identifiers"]["HOLDING_ID"]), ["1"])
        self.assertEqual(sorted(out["submission"]["ACCESSION_NUMBER"]), ["A1", "A2"])


class UnlistedMeasure(unittest.TestCase):
    def positions(self):
        base = {"unit": "NS", "asset_cat": "EP", "payoff": "Long", "currency": "USD", "fair_value_level": "3",
                "issuer_name": "Anthropic PBC", "title": "Series F", "isin": None, "cusip": "N/A", "cik": "0000000001",
                "restricted": "Y", "series_name": "Fund One", "registrant_name": "Trust One"}
        rows = [dict(base, series_id="S1", report_date="2025-03-31", filing_date="2025-05-20", accession="A1",
                     balance="100", value_usd="5600", value_local="5600"),
                dict(base, series_id="S1", report_date="2025-03-31", filing_date="2025-06-02", accession="A1-amd",
                     balance="100", value_usd="6000", value_local="6000"),                      # l'amendement remplace
                dict(base, series_id="S1", report_date="2025-02-28", filing_date="2025-04-20", accession="A0",
                     balance="100", value_usd="5000", value_local="5000"),                      # même trimestre, plus tôt
                dict(base, series_id="S2", report_date="2025-01-31", filing_date="2025-03-20", accession="A2",
                     balance="10", value_usd="500", value_local="500"),
                dict(base, series_id="S3", report_date="2025-03-31", filing_date="2025-05-21", accession="A3",
                     balance="10", value_usd="700", value_local="700", fair_value_level="2"),    # niveau 2 : hors mesure
                dict(base, series_id="S4", report_date="2025-03-31", filing_date="2025-05-21", accession="A4",
                     issuer_name="Space Exploration Technologies Corp", balance="10", value_usd="1500", value_local="1500"),
                dict(base, series_id="S4", report_date="2026-06-30", filing_date="2026-08-21", accession="A5",
                     issuer_name="Space Exploration Technologies Corp", balance="10", value_usd="2500", value_local="2500")]
        return P.attributed(pd.DataFrame(rows), ROWS)

    def test_level_3_shares_before_listing(self):
        sel, steps = P.mark_selection(self.positions(), "2026-10-07", {"e:spx": "2026-06-12"})
        self.assertEqual(steps["not_level_3"], 1)
        self.assertEqual(steps["listed_at_date"], 1)                       # SpaceX après son 424B4
        self.assertEqual(sorted(sel["accession"]), ["A0", "A1", "A1-amd", "A2", "A4"])
        unknown, st = P.mark_selection(self.positions(), "2026-10-07", {"e:spx": None})
        self.assertEqual(st["listing_unknown"], 2)
        always, st = P.mark_selection(self.positions(), "2026-10-07", {"e:spx": ""})
        self.assertEqual(st["listed_at_date"], 2)

    def test_cells_per_share_and_held_by_quarter(self):
        import pipeline.nport as N
        p = self.positions()
        old = N.u_positions, N.u_manifest, N.listing
        N.u_positions, N.u_manifest, N.listing = (lambda *a, **k: p.drop(columns=["entity_id", "legal_form", "node"])), \
            (lambda: {"x": {}}), (lambda *a, **k: {"e:spx": "2026-06-12"})
        try:
            cells = N.u_cells("2026-10-07", ROWS)
        finally:
            N.u_positions, N.u_manifest, N.listing = old
        mk = {(c["subject"], c["counterparty"], c["period_end"]): c for c in cells if c["measure"] == "nport_equity_mark"}
        c = mk[("LAB:ANTHROPIC", "series:S1", "2025-03-31")]
        self.assertEqual(Decimal(c["value"]), Decimal("60"))
        self.assertEqual(c["breakdown_key"], "EP|TITLE:series f")
        self.assertEqual(c["unit"], "USD")
        self.assertEqual(Decimal(mk[("SPCX", "series:S4", "2025-03-31")]["value"]), Decimal("150"))
        held = {(c["subject"], c["period_end"]): c for c in cells if c["measure"] == "nport_equity_held"}
        h = held[("LAB:ANTHROPIC", "2025-03-31")]
        self.assertEqual(Decimal(h["value"]), Decimal("6500"))             # S1 au 31 mars (amendement) et S2 au 31 janvier
        self.assertEqual(json.loads(h["flags"])["series"], 2)
        self.assertNotIn(("SPCX", "2026-06-30"), held)

    def test_listing_date_reads_the_first_ipo_prospectus_in_all_pages(self):
        from pipeline import cache, config
        with tempfile.TemporaryDirectory() as d:
            old = config.CACHE
            config.CACHE = Path(d)
            try:
                main = {"filings": {"recent": {"form": ["10-Q", "424B4"], "filingDate": ["2026-08-01", "2026-06-12"]},
                                    "files": [{"name": "CIK0000000009-submissions-001.json"}]}}
                cache.write(cache.api_path("0000000009", "submissions", "2026-10-07"), json.dumps(main).encode())
                self.assertIsNone(P.listing_date("9", "2026-10-07"))          # page ancienne absente : inconnue
                old_page = {"form": ["424B1", "D"], "filingDate": ["2001-03-02", "2000-01-01"]}
                cache.write(cache.api_path("0000000009", "submissions-001", "2026-10-07"), json.dumps(old_page).encode())
                self.assertEqual(P.listing_date("9", "2026-10-07"), "2001-03-02")
                self.assertEqual(P.listing_date("9", "2000-06-30"), "")         # après l'as_of : ignoré
            finally:
                config.CACHE = old

    def test_quarter_end(self):
        self.assertEqual([P.quarter_end(d) for d in ("2025-01-31", "2025-03-31", "2025-11-30")],
                         ["2025-03-31", "2025-03-31", "2025-12-31"])


class UnlistedCorrections(unittest.TestCase):
    """D-0065, point 15 : corrections fixées avant le calcul."""

    def test_a_vehicle_word_after_the_legal_name_leaves_it_unattributed(self):
        legal = P.lexicon(ROWS, CFG)["legal"]
        self.assertEqual(P.attribute("Anthropic PBC Private Equity (SPV Ravine Master Aggr", legal), (None, "anthropic pbc"))
        self.assertEqual(P.attribute("Anthropic PBC SER H-1 CVT PFD PP", legal)[0], "e:ant")

    def test_majority_of_quoted_equity_positions_lists_an_entity_in_its_archive(self):
        import pipeline.nport as N
        with tempfile.TemporaryDirectory() as d:
            saved = N.BASE
            N.BASE = Path(d)
            try:
                for arch, rows in (("2021q1", [("e:aig", "1", 30), ("e:aig", "3", 2), ("e:ant", "1", 1), ("e:ant", "2", 4), ("e:ant", "3", 600)]),
                                   ("2019q4", [("e:aig", "3", 5)])):
                    (Path(d) / arch / "unlisted").mkdir(parents=True)
                    pd.DataFrame([{"kind": "entity", "key": k, "level": lv, "asset_cat": "EC", "n": n} for k, lv, n in rows]
                                 + [{"kind": "entity", "key": "e:aig", "level": "2", "asset_cat": "DBT", "n": 900}]).to_parquet(
                        Path(d) / arch / "unlisted" / "counts.parquet")
                m = {"2021q1": {"status": "scanned"}, "2019q4": {"status": "scanned"}}
                q = N.quoted_archives(m)
            finally:
                N.BASE = saved
        self.assertEqual(q, {("e:aig", "2021q1")})          # la dette ne compte pas ; Anthropic reste non cotée
        p = UnlistedMeasure().positions().assign(archive="2021q1")
        p.loc[p["entity_id"] == "e:ant", "archive"] = "2021q1"
        sel, steps = P.mark_selection(p, "2026-10-07", {"e:spx": "2026-06-12"}, {("e:ant", "2021q1")})
        self.assertEqual(steps["quoted_in_archive"], 4)    # positions de niveau 3 d'Anthropic dans une archive cotée
        sel, steps = P.mark_selection(p, "2026-10-07", {"e:spx": "2026-06-12"}, {("e:spx", "2021q1")})
        self.assertEqual(steps["quoted_in_archive"], 0)    # une entité à symbole suit sa date de cotation


class UnlistedFetch(unittest.TestCase):
    def test_overlapped_pulls_skip_late_archives_and_delete_zips(self):
        import pipeline.nport as N
        from requests.structures import CaseInsensitiveDict
        hold = [["ACCESSION_NUMBER", "HOLDING_ID", "ISSUER_NAME", "ISSUER_TITLE", "FAIR_VALUE_LEVEL", "ASSET_CAT"],
                ["A1", "1", "Anthropic PBC", "Series E", "3", "EP"]]
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("FUND_REPORTED_HOLDING.tsv", tsv(hold))
            for t, hdr in (("IDENTIFIERS", "HOLDING_ID"), ("DEBT_SECURITY", "HOLDING_ID"), ("SUBMISSION", "ACCESSION_NUMBER"),
                           ("REGISTRANT", "ACCESSION_NUMBER"), ("FUND_REPORTED_INFO", "ACCESSION_NUMBER")):
                z.writestr(f"{t}.tsv", tsv([[hdr]]))
        lm = {"2026q3": "Wed, 07 Oct 2026 16:13:21 GMT", "2026q2": "Thu, 08 Oct 2026 10:00:00 GMT", "2026q1": "Mon, 06 Apr 2026 14:13:33 GMT"}

        class Client:
            def __init__(self, *a, **k):
                self.calls = []

            def get(self, url, timeout=None, dest=None):
                name = url.rsplit("/", 1)[-1][:6]
                self.calls.append(name)
                Path(dest).write_bytes(buf.getvalue())
                return None, CaseInsensitiveDict({"Last-Modified": lm[name]})
        arch = [{"name": n, "url": f"https://www.sec.gov/files/{n}_nport.zip", "filed_from": "2026-01-01", "filed_to": "2026-09-30"}
                for n in ("2026q3", "2026q2", "2026q1")]
        saved = (N.BASE, N.U_MANIFEST, N.MANIFEST, N.archive_list, N.lexicon, N.cols, N.net.SecClient, N.config.load)
        with tempfile.TemporaryDirectory() as d:
            N.BASE, N.U_MANIFEST, N.MANIFEST = Path(d), Path(d) / "u.jsonl", Path(d) / "m.jsonl"
            cfg = {"nport": {"period": ["2019-10-01", "2026-10-07"], "columns": UC, "unlisted": {}}, "as_of": "2026-10-07"}
            N.archive_list = lambda html=None: arch
            lex = saved[4]
            N.lexicon = lambda cfg=None, ent_rows=None: lex(ROWS, CFG)
            N.cols = lambda cfg=None: UC
            N.net.SecClient = Client
            N.config.load = lambda *a, **k: cfg
            try:
                N.fetch_unlisted()
                m = N.u_manifest()
                left = sorted(p.name for p in Path(d).glob("*.zip"))
                kept = pd.read_parquet(Path(d) / "2026q1" / "unlisted" / "holding.parquet")
            finally:
                (N.BASE, N.U_MANIFEST, N.MANIFEST, N.archive_list, N.lexicon, N.cols, N.net.SecClient, N.config.load) = saved
        self.assertEqual({k: r["status"] for k, r in m.items()}, {"2026q3": "scanned", "2026q2": "after_as_of", "2026q1": "scanned"})
        self.assertEqual(left, [])
        self.assertEqual(list(kept["HOLDING_ID"]), ["1"])
        self.assertTrue(m["2026q1"]["sha256"])



class UnlistedRender(unittest.TestCase):
    def test_section_lists_nodes_by_held_value(self):
        import duckdb
        from pipeline import config
        from pipeline import render as R
        con = duckdb.connect()
        con.execute((config.ROOT / "schema.sql").read_text(encoding="utf-8"))

        def m(measure, subject, pe, value, cp="none", bk="none", flags=None, unit="USD"):
            con.execute("INSERT INTO measures (measure, subject, counterparty, period_start, period_end, view, as_of, term, "
                        "breakdown_key, financing_policy, constant_perimeter, variant, status, value, unit, flags) VALUES "
                        "(?, ?, ?, 'none', ?, 'as_known', '2026-10-07', 'none', ?, 'none', 'none', 'none', 'computed', ?, ?, ?)",
                        [measure, subject, cp, pe, bk, value, unit, json.dumps(flags or {})])
        m("nport_equity_held", "LAB:ANTHROPIC", "2025-12-31", 2_500_000, flags={"series": 3, "positions": 4})
        m("nport_equity_held", "LAB:ANTHROPIC", "2026-06-30", 9_000_000, flags={"series": 5, "positions": 6})
        m("nport_equity_held", "LAB:OPENAI", "2026-06-30", 1_000_000, flags={"series": 1, "positions": 1})
        m("nport_equity_mark", "LAB:ANTHROPIC", "2026-06-30", 180.5, cp="series:S1", bk="EP|TITLE:series f",
          flags={"series_name": "Fund One", "title": "Series F"})
        m("nport_equity_mark", "LAB:ANTHROPIC", "2026-06-30", 95.25, cp="series:S2", bk="EC|TITLE:common",
          flags={"series_name": "Fund Two", "title": "Common"})
        T = R.Tokens(con, "synthesis.md")
        L = R.unlisted_section(con, T)
        rows = [x for x in L if x.startswith("| Anthropic") or x.startswith("| OpenAI")]
        self.assertTrue(rows[0].startswith("| Anthropic | 2026-06-30 | 9 M$ | 5 |"))
        self.assertIn("95,25 USD – 180,50 USD (2026-06-30)", rows[0])
        self.assertIn("2025-12-31 (2 M$)", rows[0])
        self.assertTrue(rows[1].startswith("| OpenAI |"))
        S = R.unlisted_series(con, R.Tokens(con, "series.md"))
        self.assertTrue(any(x.startswith("| Fund One | Series F (EP) | 2026-06-30 (180,50 USD)") for x in S))


if __name__ == "__main__":
    unittest.main()
