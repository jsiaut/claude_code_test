"""Décision D1 (§10.3) : la série annuelle de SpaceX lue dans le 424B4.

Les états annuels du 424B4 se lisent avec un parseur HTML ; chaque ligne reçoit la
model_quantity du concept du 10-Q dont le libellé correspond, la valeur servant
seulement à vérifier, jamais à apparier. Chaque chiffre porte is_tagged = false.
On vérifie les équations internes (C1, C2, C6) et on recoupe avec le bilan comparatif
du 10-Q au 31 décembre 2025, à la tolérance d'arrondi. Un écart inexpliqué écarte la
série annuelle avec son motif.
"""
import json
import re
from decimal import Decimal

import pandas as pd

from . import cache, config, textnorm

CIK = "0001181412"
ACC_424B4 = "0001628280-26-042639"
DOC_424B4 = "spaceexplorationtechnologi.htm"
ACC_10Q = "0001628280-26-052535"
KNOWLEDGE_DATE = "2026-06-12"
TABLES = {"balance_sheet": 58, "income_statement": 59, "cash_flow": 62}

_MONTHS = r"(january|february|march|april|may|june|july|august|september|october|november|december)"


def norm_label(s):
    s = textnorm.norm_for_match(s).lower()
    s = re.sub(r"\.{3,}", " ", s)
    s = re.sub(r"\(\s*[a-z]\s*\)", " ", s)              # renvois (a)
    s = re.sub(r"\(related party[^)]*\)", " ", s)
    s = re.sub(_MONTHS + r"\s+\d{1,2},?\s*\d{0,4}", " ", s)
    s = re.sub(r"\$?\(?-?[\d,]*\.?\d+\)?", " ", s)
    s = re.sub(r"\b(and|at|as of|respectively)\b", " ", s)
    s = re.sub(r"[^a-z ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # « Income (loss) » du prospectus et « Loss » du 10-Q désignent la même ligne
    s = re.sub(r"\b(income|earnings) loss\b|\bloss (income|earnings)\b", "loss", s)
    s = re.sub(r"^net income\b", "net loss", s)
    return s


FIXED_ZERO = ("-", "—", "–")


def _num(cell):
    """Valeur d'une cellule d'état financier : parenthèses négatives ; un tiret est un zéro
    publié (l'équivalent HTML de ixt:fixed-zero), une cellule vide une absence (§7.3, §3.5)."""
    c = cell.replace("$", "").replace(",", "").strip()
    if c == "":
        return None
    if c in FIXED_ZERO:
        return Decimal(0)
    neg = c.startswith("(") and c.endswith(")")
    c = c.strip("()")
    try:
        v = Decimal(c)
    except Exception:
        return None
    return -v if neg else v


def parse_table(table):
    rows = []
    for tr in table.iter("tr"):
        cells = []
        for td in tr:
            if td.tag in ("td", "th"):
                lin = textnorm.Linearizer()
                lin.walk_cell(td)
                cells.append(" ".join(t for t, _ in lin.lines).strip())
        cells = textnorm._merge_cells(cells)
        if not cells:
            continue
        label = cells[0]
        vals = [_num(c) for c in cells[1:]]
        rows.append((label, cells[1:], vals))
    return rows


def _locate_near(text, raw, label, start_char, window=400_000):
    """Plage d'octets bruts d'un libellé, cherchée dans la région du tableau."""
    words = " ".join(textnorm.norm_for_match(re.sub(r"\.{3,}", " ", label)).split()[:8])
    pat = textnorm.quote_pattern(words)
    if pat is None:
        return None
    m = pat.search(text, start_char, start_char + window)
    if not m:
        return None
    b0 = len(text[:m.start()].encode("utf-8"))
    return b0, b0 + len(text[m.start():m.end()].encode("utf-8"))


def negated_concepts(con, kind):
    """Concepts présentés avec un libellé « negated » dans l'état du 10-Q : la valeur
    affichée est l'opposée du fait balisé."""
    rows = con.execute(f"""SELECT DISTINCT child FROM pres WHERE accession = '{ACC_10Q}'
        AND statement_kind = '{kind}' AND preferred_label ILIKE '%negated%'""").fetchall()
    return {r[0] for r in rows}


def label_index(con, kind):
    df = con.execute(f"""SELECT DISTINCT p.child AS concept, l.label FROM pres p
        JOIN labels l ON l.accession = p.accession AND l.concept = p.child
        WHERE p.accession = '{ACC_10Q}' AND p.statement_kind = '{kind}'""").fetchdf()
    idx = {}
    for c, lab in df.itertuples(index=False):
        if c.endswith("Abstract") or c.endswith("Axis") or c.endswith("Member") or c.endswith("Table"):
            continue
        idx.setdefault(norm_label(lab), set()).add(c)
    return idx


def aux_connection():
    """Connexion autonome pour D1 : linkbases, libellés, correspondance et faits du 10-Q,
    sans dépendre de la base complète (qui inclut le résultat de D1)."""
    import duckdb
    from . import quantities
    con = duckdb.connect()
    for name in ("pres", "labels"):
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM '{config.DB_DIR / (name + '.parquet')}'")
    quantities.map_concepts(con)
    con.execute(f"""CREATE TABLE facts AS SELECT concept, CAST(value AS DOUBLE) AS value, period_type,
                    CAST(period_end AS DATE) AS period_end, n_dims, accession
                    FROM '{config.DB_DIR / 'facts_instances.parquet'}' WHERE accession = '{ACC_10Q}'""")
    return con


def run(con):
    raw = cache.read(cache.archive_path(CIK, ACC_424B4, DOC_424B4))
    root = textnorm.parse_html(raw)
    tables = root.xpath("//table")
    qmap = dict(con.execute(f"SELECT concept, quantity FROM concept_map WHERE accession = '{ACC_10Q}'").fetchall())
    facts, unmatched, report = [], [], {}
    text = textnorm.decode(raw)
    for kind, ti in TABLES.items():
        rows = parse_table(tables[ti])
        # début de la région du tableau dans le fichier brut : première ligne libellée
        first = next((lab for lab, _, vals in rows if any(x is not None for x in vals)), None)
        region = _locate_near(text, raw, first, 0, len(text)) if first else None
        region_char = len(raw[:region[0]].decode("utf-8", "replace")) if region else 0
        loc_cache = {}
        idx = label_index(con, kind)
        negated = negated_concepts(con, kind)
        header_years = []
        for label, cells, vals in rows[:3]:
            header_years += re.findall(r"\b(20\d\d)\b", label + " " + " ".join(cells))
        years = [y for y in header_years if y][-len(rows[3][2]):] if rows else []
        for ri, (label, cells, vals) in enumerate(rows):
            if not any(v is not None for v in vals):
                continue
            nl = norm_label(label)
            concepts = idx.get(nl)
            if not concepts:
                # premier segment du libellé, s'il est unique parmi les libellés du 10-Q
                head = norm_label(re.split(r"[,;(]", label)[0])
                cand = {c for k, cs in idx.items() if k.split(" ")[:len(head.split())] == head.split() for c in cs}
                concepts = cand if len(cand) == 1 else None
            if not concepts or len(concepts) != 1:
                unmatched.append({"statement": kind, "label": label})
                continue
            concept = next(iter(concepts))
            for y, v, raw_cell in zip(years, vals, cells):
                if v is None:
                    continue
                fixed_zero = raw_cell.replace("$", "").strip() in FIXED_ZERO
                if kind == "balance_sheet":
                    ps, pe, pt = None, f"{y}-12-31", "instant"
                else:
                    ps, pe, pt = f"{y}-01-01", f"{y}-12-31", "duration"
                if concept in negated:
                    v = -v
                value = v if concept.startswith("us-gaap:EarningsPerShare") else v * Decimal(1_000_000)
                if label not in loc_cache:
                    loc_cache[label] = _locate_near(text, raw, label, region_char)
                loc = loc_cache[label]
                facts.append({
                    "fact_key": f"html/{ACC_424B4}/{DOC_424B4}#t{ti}r{ri}/{y}",
                    "source": "html_parse", "cik": CIK, "entity_id": "group:SPCX", "group_id": "SPCX",
                    "accession": ACC_424B4, "form": "424B4", "filing_date": KNOWLEDGE_DATE,
                    "acceptance_datetime": "2026-06-12T00:00:00", "doc_rank": 0, "occ_rank": None,
                    "concept": concept, "concept_ns": None, "taxonomy_version": None, "period_type": pt,
                    "period_start": ps, "period_end": pe,
                    "unit": "USD/shares" if concept.startswith("us-gaap:EarningsPerShare") else
                    ("shares" if "Shares" in concept else "USD"),
                    "currency": None if "Shares" in concept or concept.startswith("us-gaap:EarningsPerShare") else "USD",
                    "dims": "[]", "n_dims": 0, "framework": "us_gaap", "reporting_scope": "as_reported",
                    "value": str(value if "Shares" not in concept else v * Decimal(1_000_000)),
                    "value_text": None, "decimals": -6 if not concept.startswith("us-gaap:EarningsPerShare") else 2,
                    "decimals_inf": False, "precision_known": True, "is_nil": False, "is_fixed_zero": fixed_zero,
                    "fact_id": None,
                    "locator": json.dumps({"file": DOC_424B4, "accession": ACC_424B4, "cik": CIK,
                                           "byte_range": list(loc) if loc else None, "quote": label[:200],
                                           "table_index": ti}),
                    "is_tagged": False, "tier": "A", "filing_status": "filed", "assurance_level": "audited",
                    "knowledge_date": KNOWLEDGE_DATE, "fy": None, "fp": None, "frame": None,
                    "model_quantity": qmap.get(concept),
                })
        report[kind] = {"rows": len(rows), "years": years}
    df = pd.DataFrame(facts)
    df.to_parquet(config.DB_DIR / "facts_html.parquet")
    return df, unmatched, report


def verify(df, con):
    """Équations internes (C1, C2, C6) et recoupement avec le bilan comparatif du 10-Q,
    à la tolérance d'arrondi : ½·10^6 par terme publié en millions."""
    out = []
    v = {}
    for r in df.itertuples():
        v[(r.concept.split(":", 1)[1], r.period_end)] = Decimal(r.value)
    half = Decimal(500_000)

    def check(control, pe, total, comps, signs=None):
        t = v.get((total, pe))
        vals = [(c, v.get((c, pe))) for c in comps]
        got = [(c, x) for c, x in vals if x is not None]
        if t is None or not got:
            return
        s = sum((signs or {}).get(c, 1) * x for c, x in got)
        tol = half * (len(got) + 1)
        out.append({"control": control, "period_end": pe, "total": total, "lhs": s, "rhs": t,
                    "missing": [c for c, x in vals if x is None],
                    "status": "ok" if abs(s - t) <= tol else "mismatch"})
    for y in ("2025", "2024"):
        pe = f"{y}-12-31"
        check("c1_balance_components", pe, "AssetsCurrent",
              ["CashAndCashEquivalentsAtCarryingValue", "MarketableSecuritiesCurrent",
               "AccountsReceivableNetCurrent", "InventoryNet", "PrepaidExpenseAndOtherAssetsCurrent"])
        check("c1_balance_components", pe, "Assets",
              ["AssetsCurrent", "PropertyPlantAndEquipmentNet", "FinanceLeaseRightOfUseAsset",
               "IntangibleAssetsNetExcludingGoodwill", "CryptoAssetFairValueNoncurrent", "Goodwill",
               "DeferredIncomeTaxAssetsNet", "OtherAssetsNoncurrent"])
    for y in ("2025", "2024", "2023"):
        pe = f"{y}-12-31"
        check("c2_cash_flow_components", pe, "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
              ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInInvestingActivities",
               "NetCashProvidedByUsedInFinancingActivities",
               "EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"])
        check("c6_income_articulation", pe, "OperatingIncomeLoss", [])
    # C6 : résultat net du compte de résultat = première ligne du tableau des flux
    for y in ("2025", "2024", "2023"):
        pe = f"{y}-12-31"
        nets = df[(df.concept == "us-gaap:NetIncomeLoss") & (df.period_end == pe)]["value"].map(Decimal).tolist()
        if len(nets) >= 2:
            out.append({"control": "c6_income_articulation", "period_end": pe, "total": "NetIncomeLoss",
                        "lhs": nets[0], "rhs": nets[1], "missing": [],
                        "status": "ok" if abs(nets[0] - nets[1]) <= 2 * half else "mismatch"})
    # recoupement : faits du 424B4 au 2025-12-31 contre faits non dimensionnés du 10-Q à la même date
    q = con.execute(f"""SELECT concept, value FROM facts WHERE accession = '{ACC_10Q}' AND value IS NOT NULL
                        AND period_type = 'instant' AND period_end = DATE '2025-12-31' AND n_dims = 0""").fetchall()
    tenq = {c: Decimal(str(x)) for c, x in q}
    for r in df[(df.period_type == "instant") & (df.period_end == "2025-12-31")].itertuples():
        if r.concept in tenq:
            diff = abs(Decimal(r.value) - tenq[r.concept])
            out.append({"control": "d1_crosscheck_10q", "period_end": "2025-12-31", "total": r.concept,
                        "lhs": Decimal(r.value), "rhs": tenq[r.concept], "missing": [],
                        "status": "ok" if diff <= half * 2 else "mismatch"})
    return out
