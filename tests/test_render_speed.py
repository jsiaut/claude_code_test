"""Rendu plus rapide (D-0063) : chaque raccourci rend ce que rendait la requête d'avant. Tables lues
en mémoire, index de one(), lignées des nombres publiés lues d'un bloc, arêtes citées cherchées par
préfixe, ordre fixé des requêtes qui n'en avaient pas.

Lancement : python3 -m unittest discover -s tests -t .
"""
import csv
import json
import pathlib
import tempfile
import unittest

import duckdb

from pipeline import config
from pipeline import render as R

PK = ("measure", "subject", "counterparty", "period_start", "period_end", "view", "as_of", "term", "breakdown_key",
      "financing_policy", "constant_perimeter", "variant")
TABLES = ("measures", "controls", "exclusions", "links", "observations", "entities", "facts", "documents")
ORDER = {"measures": ", ".join(PK), "links": "link_key", "observations": "obs_key", "facts": "fact_key",
         "controls": "control", "exclusions": "exclusion_key", "entities": "entity_id", "documents": "doc_key"}
P1, P2 = "2026-10-09T15:20:00Z", "2026-10-01T10:00:00Z"
CK = "a" * 64


def base():
    """Base en mémoire au schéma du dépôt, avec quelques lignes de chaque sorte."""
    con = duckdb.connect()
    con.execute((config.ROOT / "schema.sql").read_text(encoding="utf-8"))

    def m(subject, ps, pe, value, lineage=None, flags=None, measure="fcf_basic"):
        con.execute(f"INSERT INTO measures (measure, subject, counterparty, period_start, period_end, view, as_of, term, "
                    f"breakdown_key, financing_policy, constant_perimeter, variant, status, value, lineage, flags) VALUES "
                    f"(?, ?, 'none', ?, ?, 'as_known', '2026-10-07', 'none', 'none', 'none', 'none', 'none', 'computed', ?, ?, ?)",
                    [measure, subject, ps, pe, value, lineage, flags])
    # deux cellules sous la même clé de one() (débuts de période différents) : la première dans l'ordre de la table
    m("AAA", "2025-01-02", "2025-03-31", 2, json.dumps(["f2", "obs:" + CK + f"/{P1}/1"]), json.dumps({"links": ["edge:e1"]}))
    m("AAA", "2025-01-01", "2025-03-31", 1, json.dumps(["f1", "f3", "f1"]), None)
    m("BBB", "2025-01-01", "2025-03-31", 5, None, json.dumps({"links": ["edge:absent"]}))
    for k, acc in (("f1", "0001-26-000001"), ("f2", "0001-26-000002"), ("f3", "0001-26-000003")):
        con.execute("INSERT INTO facts (fact_key, source, concept, is_tagged, accession, locator, tier) "
                    "VALUES (?, 'instance', 'us-gaap:X', true, ?, '{}', 'B')", [k, acc])

    def o(ck, pass_id, n, kind="revenue_note"):
        con.execute("INSERT INTO observations (obs_key, content_key, pass_as_of, pass_id, line_no, block_kind, kind, "
                    "validation_state, accession, locator, tier) VALUES (?, ?, '2026-10-07', ?, ?, ?, 'observation', 'valid', "
                    "'0001-26-000009', '{}', 'B')", [f"{ck}/{pass_id}/{n}", ck, pass_id, n, kind])
    o(CK, P1, 1)
    o(CK, P1, 2)
    o("b" * 64, P1, 0, "discovery_note")        # bloc de la découverte : hors du bloc text
    o("c" * 64, P2, 0)                          # passe antérieure au bloc text

    def e(key, evidence):
        con.execute("INSERT INTO links (link_key, link_kind, family, edge_evidence, evidence_keys) "
                    "VALUES (?, 'edge', 'financing', 'amount', ?)", [key, evidence])
    e("edge:e1", json.dumps([CK + f"/{P1}/12"]))            # la clé de la ligne 1 est une sous-chaîne de celle-ci
    e("edge:e2", json.dumps([CK + f"/{P1}/2", "x"]))
    e("edge:e3", None)
    e("edge:e4", json.dumps(["b" * 64 + f"/{P1}/0"]))
    e("edge:e5", json.dumps(["c" * 64 + f"/{P2}/0"]))
    e("edge:e6", "[]")
    return con


def numbers_csv_before(con, rows, path):
    """numbers_csv tel qu'il était avant D-0063 : quatre requêtes par nombre publié."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["document", "token", "kind", "cell_key", "field", "value", "text", "term_key", "accession",
                    "locator", "is_tagged", "tier"])
        for r in rows:
            terms = []
            if r["kind"] == "measure":
                k = json.loads(r["key"])
                c = R.q(con, """SELECT lineage, flags FROM measures WHERE measure = ? AND subject = ? AND counterparty = ?
                                AND period_start = ? AND period_end = ? AND view = ? AND as_of = ? AND term = ?
                                AND breakdown_key = ? AND financing_policy = ? AND constant_perimeter = ? AND variant = ?""",
                        *[k[x] for x in PK])
                if c:
                    lin = json.loads(c[0]["lineage"]) if c[0]["lineage"] else []
                    fl = json.loads(c[0]["flags"]) if c[0]["flags"] else {}
                    fkeys = [x for x in lin if not x.startswith("obs:")]
                    okeys = [x[4:] for x in lin if x.startswith("obs:")]
                    for lk in fl.get("links") or []:
                        ev = R.q(con, "SELECT evidence_keys FROM links WHERE link_key = ?", lk)
                        if ev and ev[0]["evidence_keys"]:
                            okeys += json.loads(ev[0]["evidence_keys"])
                    if fkeys:
                        for f in R.q(con, f"""SELECT fact_key, accession, locator, is_tagged, tier FROM facts
                                              WHERE fact_key IN ({','.join('?' * len(fkeys))}) ORDER BY fact_key""", *fkeys):
                            terms.append((f["fact_key"], f["accession"], f["locator"], f["is_tagged"], f["tier"]))
                    if okeys:
                        for x in R.q(con, f"""SELECT obs_key, accession, locator, tier FROM observations
                                              WHERE obs_key IN ({','.join('?' * len(okeys))}) ORDER BY obs_key""", *okeys):
                            terms.append((x["obs_key"], x["accession"], x["locator"], False, x["tier"]))
            if not terms:
                terms = [(None, None, None, None, None)]
            for t in terms:
                w.writerow([r["document"], r["token"], r["kind"], r["key"], r["field"], r["value"], r["text"], *t])


class NumbersCsv(unittest.TestCase):
    def test_same_file_as_one_query_per_number(self):
        con = base()
        T = R.Tokens(con, "synthesis.md")
        for c in R.q(con, "SELECT * FROM measures"):
            T.m(c)
        T.n("controls", {"x": 1}, 3)
        missing = dict(zip(PK, ("fcf_basic", "ZZZ", "none", "none", "2025-03-31", "as_known", "2026-10-07", "none", "none",
                                "none", "none", "none")))
        T._reg("measure", missing, "value", 1, "1")
        with tempfile.TemporaryDirectory() as d:
            a, b = pathlib.Path(d) / "a.csv", pathlib.Path(d) / "b.csv"
            R.numbers_csv(con, T.rows, a)
            numbers_csv_before(con, T.rows, b)
            self.assertEqual(a.read_text(encoding="utf-8"), b.read_text(encoding="utf-8"))
            self.assertIn("f3", a.read_text(encoding="utf-8"))


class EdgesCiting(unittest.TestCase):
    def test_same_edges_as_the_like_query(self):
        con = base()
        like = {r[0] for r in con.execute("""SELECT l.link_key FROM links l WHERE l.link_kind = 'edge' AND EXISTS (
                    SELECT 1 FROM observations o WHERE o.pass_id >= ? AND CAST(o.block_kind AS VARCHAR) NOT LIKE 'discovery_%'
                    AND l.evidence_keys LIKE '%' || o.obs_key || '%')""", [P1]).fetchall()}
        self.assertEqual(set(R.edges_citing(con, P1)), like)
        self.assertEqual(like, {"edge:e1", "edge:e2"})

    def test_like_wildcard_in_a_key_falls_back_to_the_query(self):
        con = base()
        con.execute("UPDATE observations SET obs_key = obs_key || '_x' WHERE line_no = 2")
        self.assertIsNone(R.edges_citing(con, P1))


class OneIndexAndMemoryTables(unittest.TestCase):
    def test_index_returns_the_query_row_and_a_copy(self):
        src = base()
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "tables").mkdir()
            for t in TABLES:
                src.execute(f"COPY (SELECT * FROM {t} ORDER BY {ORDER[t]}) TO '{root / 'tables' / (t + '.parquet')}' "
                            "(FORMAT PARQUET)")
            old = config.ROOT
            config.ROOT = root
            try:
                con = duckdb.connect()
                R.load(con, "2026-10-07")
                plain = duckdb.connect()                   # même tables, sans index : la requête d'avant
                for t in TABLES:
                    plain.execute(f"CREATE VIEW {t} AS SELECT * FROM '{root / 'tables' / (t + '.parquet')}'")
                for subj in ("AAA", "BBB", "ZZZ"):
                    self.assertEqual(R.one(con, "fcf_basic", subj, "2025-03-31"),
                                     R.one(plain, "fcf_basic", subj, "2025-03-31"))
                first = R.one(con, "fcf_basic", "AAA", "2025-03-31")
                self.assertEqual(first["period_start"], "2025-01-01")
                first["value"] = None
                self.assertIsNotNone(R.one(con, "fcf_basic", "AAA", "2025-03-31")["value"])
                self.assertEqual(con.execute("SELECT table_type FROM information_schema.tables WHERE table_name = 'measures'")
                                 .fetchone()[0], "BASE TABLE")
            finally:
                config.ROOT = old
                R._ONE.clear()



class CounterpartyGroupName(unittest.TestCase):
    """D-0064 : une filiale rattachée par extrait à un groupe de contrepartie ne lui donne pas son nom ; la tête
    (même nom normalisé que la clé) passe d'abord, et un groupe sans tête garde le plus petit nom de ses membres."""

    def test_head_name_first(self):
        con = duckdb.connect()
        con.execute("CREATE TABLE entities (entity_id VARCHAR, record_kind VARCHAR, ref VARCHAR, name VARCHAR, normalized_name VARCHAR)")
        rows = [("e1", "entity", None, "Fluidstack Ltd.", "fluidstack ltd"),
                ("e2", "entity", None, "Fluidstack CS I Inc.", "fluidstack cs i inc"),
                ("e2", "membership", "CP:fluidstack ltd", None, None),
                ("e3", "entity", None, "Galaxy Helios I LLC", "galaxy helios i llc"),
                ("e3", "membership", "CP:sans tete", None, None)]
        con.executemany("INSERT INTO entities VALUES (?, ?, ?, ?, ?)", rows)
        names = R.cp_names(con)
        self.assertEqual(names["CP:fluidstack ltd"], "Fluidstack Ltd.")
        self.assertEqual(names["CP:fluidstack cs i inc"], "Fluidstack CS I Inc.")
        self.assertEqual(names["CP:sans tete"], "Galaxy Helios I LLC")


if __name__ == "__main__":
    unittest.main()
