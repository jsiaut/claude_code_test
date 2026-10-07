"""Construction de la base : les huit tables recalculées intégralement à chaque exécution
depuis le cache et les fichiers d'observations (§7, §9.6)."""
import json
from decimal import Decimal

import duckdb
import pandas as pd

from . import config, reader, textnorm
from .registry import ENUMS

DB_PATH = config.DB_DIR / "model.duckdb"

FACT_COLS = ["fact_key", "source", "cik", "entity_id", "group_id", "accession", "form", "filing_date",
             "acceptance_datetime", "doc_rank", "occ_rank", "concept", "concept_ns", "taxonomy_version",
             "period_type", "period_start", "period_end", "unit", "currency", "dims", "n_dims", "framework",
             "reporting_scope", "value", "value_text", "value_rounded", "decimals", "decimals_inf",
             "precision_known", "is_nil", "is_fixed_zero", "fact_id", "locator", "is_tagged", "tier",
             "filing_status", "assurance_level", "knowledge_date", "fy", "fp", "model_quantity", "conflict"]


def connect(fresh=False):
    config.DB_DIR.mkdir(exist_ok=True)
    if fresh and DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    if fresh:
        con.execute((config.ROOT / "schema.sql").read_text(encoding="utf-8"))
    return con


def _rounded(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    d = Decimal(str(v))
    return d != d.quantize(Decimal("0.000001"))


def load_facts(con):
    frames = []
    for name in ("facts_companyfacts.parquet", "facts_instances.parquet", "facts_html.parquet"):
        p = config.DB_DIR / name
        if p.exists():
            frames.append(pd.read_parquet(p))
    df = pd.concat(frames, ignore_index=True)
    df["value_rounded"] = df["value"].map(_rounded)
    df["model_quantity"] = None
    df["conflict"] = False
    for c in FACT_COLS:
        if c not in df.columns:
            df[c] = None
    df = df[FACT_COLS]
    df["acceptance_datetime"] = pd.to_datetime(df["acceptance_datetime"], utc=True, errors="coerce").dt.tz_localize(None)
    con.register("df_facts", df)
    con.execute(f"""INSERT INTO facts SELECT
        fact_key, source, cik, entity_id, group_id, accession, form, CAST(filing_date AS DATE),
        acceptance_datetime, doc_rank, occ_rank, concept, concept_ns, taxonomy_version,
        period_type, CAST(period_start AS DATE), CAST(period_end AS DATE), unit, currency, dims, n_dims,
        framework, reporting_scope, CAST(value AS DECIMAL(38,6)), value_text, value_rounded, decimals,
        decimals_inf, precision_known, is_nil, is_fixed_zero, fact_id, locator, is_tagged, tier,
        filing_status, assurance_level, CAST(knowledge_date AS DATE), fy, fp, model_quantity, conflict
        FROM df_facts""")
    con.unregister("df_facts")
    return len(df)


def mark_conflicts(con, scale_jump_factor):
    """Deux faits d'une même identité dans un même dépôt sont conflicting si leur écart
    dépasse la tolérance d'arrondi de leurs deux précisions (des doublons cohérents ne
    le sont pas) ; un saut d'un facteur 100 entre deux périodes successives de même
    longueur aussi, tant que num des Notes Data Sets ne l'a pas confirmé (§7.3). L'ordre
    est total (date de connaissance, accession, clé du fait) : le résultat ne dépend pas
    de l'ordre de lecture."""
    tol = "(CASE WHEN {d}_inf THEN 0 WHEN {d} IS NULL THEN NULL ELSE 0.5 * pow(10, -{d}) END)"
    con.execute(f"""
      UPDATE facts SET conflict = true WHERE fact_key IN (
        SELECT a.fact_key FROM facts a JOIN facts b
          ON a.accession = b.accession AND a.concept = b.concept AND a.entity_id = b.entity_id
         AND a.period_type = b.period_type AND a.period_start IS NOT DISTINCT FROM b.period_start
         AND a.period_end = b.period_end AND a.unit IS NOT DISTINCT FROM b.unit AND a.dims = b.dims
         AND a.reporting_scope = b.reporting_scope AND a.fact_key <> b.fact_key
        WHERE a.source = 'instance' AND b.source = 'instance' AND a.value IS NOT NULL AND b.value IS NOT NULL
          AND abs(a.value - b.value) > coalesce({tol.format(d='a.decimals')}, 0) + coalesce({tol.format(d='b.decimals')}, 0))""")
    con.execute(f"""
      UPDATE facts SET conflict = true WHERE fact_key IN (
        SELECT fact_key FROM (
          SELECT fact_key, value, lag(value) OVER (
                   PARTITION BY group_id, concept, unit, dims, period_type,
                                round(coalesce(date_diff('day', period_start, period_end), 0) / 30)
                   ORDER BY period_end, period_start, knowledge_date, accession, fact_key) AS prev
          FROM facts WHERE value IS NOT NULL AND source = 'instance' AND n_dims = 0 AND unit = 'USD'
            AND NOT coalesce(conflict, false))
        WHERE prev IS NOT NULL AND prev <> 0 AND value <> 0
          AND (abs(value / prev) >= {scale_jump_factor} OR abs(prev / value) >= {scale_jump_factor}))""")
    return con.execute("SELECT count(*) FROM facts WHERE conflict").fetchone()[0]


# -- observations --------------------------------------------------------------------

OBS_COLS = None


def load_observations(con, catalog, as_of):
    """Charge la passe la plus récente de chaque bloc dont la clé existe encore, après
    validation sémantique ; une ligne rejetée devient une exclusion validation_failed."""
    cat = {b["content_key"]: b for b in catalog}
    rows, excl = [], []
    for p in sorted(config.OBS_DIR.glob("*.jsonl")):
        if p.name.endswith(".rejected.jsonl"):
            continue
        ck = p.stem
        b = cat.get(ck)
        lines = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        if b is None:
            continue  # bloc absent de l'exécution courante : fichier conservé, non chargé
        if not lines:
            continue
        last = max((l.get("as_of"), l.get("pass_id")) for l in lines)
        lines = [l for l in lines if (l.get("as_of"), l.get("pass_id")) == last]
        rej = config.OBS_DIR / f"{ck}.rejected.jsonl"
        if rej.exists():
            for r in (json.loads(x) for x in rej.read_text(encoding="utf-8").splitlines() if x.strip()):
                if (r.get("as_of"), r.get("pass_id")) == last:
                    excl.append(_excl("observation_line", f"{ck}/{r['pass_id']}/schema", "validation_failed",
                                      "; ".join(r.get("errors", [])), b, as_of, raw=r.get("raw")))
        for n, l in enumerate(lines):
            errs, locator = semantic_errors(l, b)
            state = "valid" if not errs else "rejected_semantic"
            row = _obs_row(l, b, n, state, errs, locator)
            rows.append(row)
            if errs:
                excl.append(_excl("observation_line", row["obs_key"], "validation_failed", "; ".join(errs), b,
                                  as_of, raw=json.dumps(l, ensure_ascii=False)))
    if rows:
        df = pd.DataFrame(rows)
        con.register("df_obs", df)
        cols = ", ".join(df.columns)
        con.execute(f"INSERT INTO observations ({cols}) SELECT {cols} FROM df_obs")
        con.unregister("df_obs")
    return rows, excl


def semantic_errors(line, block):
    """Citation retrouvée mot pour mot, contrepartie présente dans le bloc, montant égal
    au fait candidat quand l'origine est tagged_reference (§7.4)."""
    errs = []
    text_norm = textnorm.norm_for_match(block["text"]).lower()
    locator = None
    q = line.get("quote")
    if q:
        if textnorm.norm_for_match(q).lower() not in text_norm:
            errs.append("citation introuvable mot pour mot dans le bloc")
        else:
            locator = _locate(block, q)
    if line.get("exhibit_title") and textnorm.norm_for_match(line["exhibit_title"]).lower() not in text_norm:
        errs.append("titre de pièce introuvable dans le bloc")
    cp = line.get("counterparty_name")
    if cp and line.get("counterparty_evidence") in ("named", "derivable"):
        if textnorm.norm_for_match(cp).lower() not in text_norm:
            cands = " ".join(json.dumps(c.get("dims")) for c in block.get("candidate_facts") or []).lower()
            if line.get("derivation_method") != "dimension_member_label" or cp.lower() not in cands:
                errs.append("contrepartie absente du bloc")
    if line.get("amount_origin") == "tagged_reference":
        cand = next((c for c in block.get("candidate_facts") or [] if c["fact_key"] == line.get("candidate_fact_key")), None)
        if cand is None:
            errs.append("candidate_fact_key absent des faits candidats du bloc")
        elif line.get("amount") is not None and Decimal(str(line["amount"])) != Decimal(str(cand["value"])):
            errs.append("montant différent du fait candidat")
    if line.get("amount_origin") == "narrative_only" and line.get("amount") is not None:
        # même valeur ET même période (ou ligne sans période) : un montant d'une autre
        # période, égal par hasard à un fait balisé, reste un texte non balisé
        pe = line.get("period_end")
        same = [c for c in block.get("candidate_facts") or []
                if Decimal(str(c["value"])) == Decimal(str(line["amount"]))
                and (pe is None or str(c.get("period_end") or "")[:10] == pe)]
        if same:
            errs.append("montant présent dans un fait candidat : tagged_reference attendu")
    if line.get("amount") is not None and line.get("unit") in ("USD", "EUR", "GBP", "JPY") and \
            line.get("currency") not in (None, line.get("unit")):
        errs.append("unité et devise incohérentes")
    return errs, locator


def _locate(block, quote):
    from .config import CACHE
    from . import cache as cachemod
    loc = dict(block.get("locator") or {})
    loc["quote"] = quote
    try:
        p = cachemod.archive_path(loc["cik"], loc["accession"], loc["file"])
        raw = cachemod.read(p)
        start = (loc.get("byte_range") or [0])[0]
        start_char = len(textnorm.decode(raw[:start])) if start else 0
        r = textnorm.locate_in_raw(raw, quote, start_char)
        loc["quote_byte_range"] = list(r) if r else None
    except Exception:
        loc["quote_byte_range"] = None
    return json.dumps(loc, ensure_ascii=False)


def _obs_row(l, b, n, state, errs, locator):
    known = {k: l.get(k) for k in reader.LINE_FIELDS}
    row = {
        "obs_key": f"{b['content_key']}/{l.get('pass_id')}/{n}", "content_key": b["content_key"],
        "pass_as_of": l.get("as_of"), "pass_id": l.get("pass_id"), "line_no": n,
        "block_kind": b["block_kind"], "doc_key": f"{b['cik']}/{b['accession']}/{b['document']}",
        "group_id": b["group_id"], "cik": b["cik"], "accession": b["accession"], "form": b["form"],
        "item": b.get("item"), "exhibit_type": b.get("exhibit_type"), "knowledge_date": b["knowledge_date"],
        "filing_status": b.get("filing_status", "filed"), "assurance_level": b.get("assurance_level"),
        "tier": b.get("tier"), "locator": locator, "validation_state": state,
        "validation_error": "; ".join(errs) if errs else None,
    }
    for k, v in known.items():
        if k in ("quote",):
            row[k] = v
        elif k == "kind":
            row["kind"] = v
        else:
            row[k] = v
    return row


def _excl(item_kind, item_key, reason, detail, b, as_of, raw=None):
    return {"exclusion_key": f"{reason}:{item_key}", "item_kind": item_kind, "item_key": item_key,
            "reason": reason, "detail": detail, "group_id": b.get("group_id") if b else None,
            "accession": b.get("accession") if b else None, "content_key": b.get("content_key") if b else None,
            "invariant": None, "raw": raw, "as_of": as_of}


def insert_exclusions(con, rows):
    if not rows:
        return 0
    df = pd.DataFrame(rows).drop_duplicates("exclusion_key")
    for c in ("exclusion_key", "item_kind", "item_key", "reason", "detail", "group_id", "accession",
              "content_key", "invariant", "raw", "as_of"):
        if c not in df.columns:
            df[c] = None
    con.register("df_ex", df)
    con.execute("""INSERT INTO exclusions SELECT exclusion_key, item_kind, item_key, reason, detail, group_id,
                   accession, content_key, invariant, raw, as_of FROM df_ex""")
    con.unregister("df_ex")
    return len(df)
