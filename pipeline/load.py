"""Construction de la base : les huit tables recalculées intégralement à chaque exécution
depuis le cache et les fichiers d'observations (§7, §9.6)."""
import json
import re
from decimal import Decimal, InvalidOperation

import pandas as pd

from . import config, reader, textnorm
from .foreign import block_framework

DB_PATH = config.DB_DIR / "model.duckdb"

FACT_COLS = ["fact_key", "source", "cik", "entity_id", "group_id", "accession", "form", "filing_date",
             "acceptance_datetime", "doc_rank", "occ_rank", "concept", "concept_ns", "taxonomy_version",
             "period_type", "period_start", "period_end", "unit", "currency", "dims", "n_dims", "framework",
             "reporting_scope", "value", "value_text", "value_rounded", "decimals", "decimals_inf",
             "precision_known", "is_nil", "is_fixed_zero", "locator", "is_tagged", "tier",
             "filing_status", "assurance_level", "knowledge_date", "fy", "fp", "model_quantity", "conflict"]


def connect(fresh=False, path=None):
    path = path or DB_PATH
    config.DB_DIR.mkdir(exist_ok=True)
    if fresh and path.exists():
        path.unlink()
    con = config.duckdb_connect(path)
    if fresh:
        con.execute((config.ROOT / "schema.sql").read_text(encoding="utf-8"))
    return con


def _rounded(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    d = Decimal(str(v))
    return d != d.quantize(Decimal("0.000001"))


def compact_locator(df):
    """Emplacement d'un fait (§7 ; D-0072, point 3 a). Fait d'instance : l'`id` du fait dans l'instance, ou « # » suivi
    du rang d'occurrence s'il n'en a pas. Fait `companyfacts` : la ressource de l'API ; le concept, l'unité et la période
    sont dans la clé et les colonnes. Les autres sources gardent le leur (plage d'octets et citation d'un texte)."""
    inst = df["source"] == "instance"
    if inst.any():
        df.loc[inst, "locator"] = [f if isinstance(f, str) and f else f"#{int(r)}"
                                   for f, r in zip(df.loc[inst, "fact_id"], df.loc[inst, "occ_rank"])]
    cf = df["source"] == "companyfacts"
    if cf.any():
        df.loc[cf, "locator"] = ["companyfacts/CIK" + str(c) for c in df.loc[cf, "cik"]]
    return df


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
    df = compact_locator(df)
    for c in FACT_COLS:
        if c not in df.columns:
            df[c] = None
    df = df[FACT_COLS]
    df["acceptance_datetime"] = pd.to_datetime(df["acceptance_datetime"], utc=True, errors="coerce").dt.tz_localize(None)
    con.register("df_facts", df)
    con.execute("""INSERT INTO facts SELECT
        fact_key, source, cik, entity_id, group_id, accession, form, CAST(filing_date AS DATE),
        acceptance_datetime, doc_rank, occ_rank, concept, concept_ns, taxonomy_version,
        period_type, CAST(period_start AS DATE), CAST(period_end AS DATE), unit, currency, dims, n_dims,
        framework, reporting_scope, CAST(value AS DECIMAL(38,6)), value_text, value_rounded, decimals,
        decimals_inf, precision_known, is_nil, is_fixed_zero, locator, is_tagged, tier,
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
    # saut d'échelle : confirmé, donc pas conflicting, quand le fait companyfacts du même dépôt (extraction
    # de la SEC, le rôle que §7.3 donne à num) lui est égal à la tolérance d'arrondi près ; non confirmé,
    # il reste hors des sommes avec son doublon companyfacts éventuel (D-0069, point 6)
    con.execute(f"""
      CREATE OR REPLACE TEMP TABLE scale_jumps AS
        SELECT fact_key FROM (
          SELECT fact_key, value, lag(value) OVER (
                   PARTITION BY group_id, concept, unit, dims, period_type,
                                round(coalesce(date_diff('day', period_start, period_end), 0) / 30)
                   ORDER BY period_end, period_start, knowledge_date, accession, fact_key) AS prev
          FROM facts WHERE value IS NOT NULL AND source = 'instance' AND n_dims = 0 AND unit = 'USD'
            AND NOT coalesce(conflict, false))
        WHERE prev IS NOT NULL AND prev <> 0 AND value <> 0
          AND (abs(value / prev) >= {scale_jump_factor} OR abs(prev / value) >= {scale_jump_factor})""")
    same = """b.source = 'companyfacts' AND b.accession = a.accession AND b.concept = a.concept
              AND b.period_type = a.period_type AND b.period_start IS NOT DISTINCT FROM a.period_start
              AND b.period_end = a.period_end AND b.unit IS NOT DISTINCT FROM a.unit AND b.n_dims = 0"""
    con.execute(f"""
      CREATE OR REPLACE TEMP TABLE scale_unconfirmed AS
        SELECT a.fact_key FROM facts a JOIN scale_jumps j USING (fact_key)
        WHERE NOT EXISTS (SELECT 1 FROM facts b WHERE {same} AND b.value IS NOT NULL
                          AND abs(b.value - a.value) <= coalesce({tol.format(d='a.decimals')}, 0)
                                                        + coalesce({tol.format(d='b.decimals')}, 0))""")
    con.execute(f"""
      UPDATE facts SET conflict = true WHERE fact_key IN (
        SELECT fact_key FROM scale_unconfirmed
        UNION SELECT b.fact_key FROM facts a JOIN scale_unconfirmed u USING (fact_key) JOIN facts b ON {same})""")
    return con.execute("SELECT count(*) FROM facts WHERE conflict").fetchone()[0]


# -- observations --------------------------------------------------------------------

OBS_COLS = None


def canonical_filers(catalog):
    """Dénomination courante de chaque déposant découvert : celle de son dépôt le plus récent. Un même
    CIK est une même entité (§10.2) ; une ancienne dénomination (« Iris Energy », devenue « IREN »)
    n'en fait pas un autre groupe."""
    best = {}
    for b in catalog:
        if not str(b.get("block_kind", "")).startswith("discovery_") or not b.get("filer_name"):
            continue
        c = str(int(b["cik"]))
        k = (str(b.get("filing_date") or ""), b["filer_name"])
        if c not in best or k > best[c]:
            best[c] = k
    return {c: v[1] for c, v in best.items()}


def config_group_ciks():
    """CIK (sans zéros) -> groupe de config.yaml, prédécesseurs compris (phase 0)."""
    p = config.DB_DIR / "phase0.json"
    if not p.exists():
        return {}
    meta = json.loads(p.read_text())["meta"]
    return {str(int(c)): m["group"] for c, m in meta.items()}


def attached_filer_ciks(cfg=None):
    """CIK (sans zéros) d'un déposant rattaché à un groupe par extrait -> (groupe, entrée) : ses dépôts
    vont à ce groupe aux dates de l'appartenance (Athene Holding Ltd., D-0055, point 8)."""
    cfg = cfg or config.load()
    return {str(int(c["cik"])): (c["group"], c.get("valid_from") or "none")
            for c in cfg.get("confirmed_entities") or [] if str(c.get("cik") or "").strip().isdigit()}


def line_group(b, as_group, canon, attached=None):
    """Groupe des lignes d'un bloc lu hors de la liste d'un groupe suivi, ou None pour garder celui du
    bloc : un déposant découvert devenu groupe de config.yaml (D-0043) ou dont un montage a lu les dépôts
    (D-0053, point 7) passe à son groupe ; un déposant rattaché à un groupe par extrait aussi, pour ses
    dépôts postérieurs à l'entrée (D-0055, point 8) ; un autre déposant découvert forme le groupe de sa
    contrepartie."""
    kind = str(b.get("block_kind", ""))
    cik = str(int(b["cik"])) if str(b.get("cik") or "").strip().isdigit() else None
    if kind.startswith("discovery_") and cik in as_group:
        return as_group[cik]
    if kind == "montage_text" and str(b.get("group_id") or "").startswith("CP:") and cik in as_group:
        return as_group[cik]
    if (kind.startswith("discovery_") or kind == "montage_text") and cik in (attached or {}):
        g, frm = attached[cik]
        if frm == "none" or str(b.get("filing_date") or "") >= str(frm):
            return g
    if kind.startswith("discovery_") and cik in canon:
        from .graph import normalize_name
        return "CP:" + normalize_name(canon[cik])
    return None


def load_observations(con, catalog, as_of, use_memo=True):
    """Charge la passe la plus récente de chaque bloc dont la clé existe encore, après
    validation sémantique ; une ligne rejetée devient une exclusion validation_failed.
    use_memo=False ignore les plages de citations déjà trouvées et les cherche toutes."""
    cat = {b["content_key"]: b for b in catalog}
    canon = canonical_filers(catalog)
    # un déposant découvert devenu groupe de config.yaml (D-0043) : ses lignes vont à son groupe ; la
    # tête d'un groupe non déposant qui a déposé son document d'enregistrement (D-0054, point 13) aussi
    as_group = config_group_ciks()
    from .nf_discovery import own_filer_ciks
    as_group.update(own_filer_ciks())
    attached = attached_filer_ciks()
    rows, excl = [], []
    # deux temps : les lignes se valident fichier par fichier (texte du bloc normalisé une fois), les
    # citations à localiser s'accumulent ; elles se cherchent ensuite document par document (mémo des
    # plages déjà trouvées, voir QuoteRanges), puis les lignes s'écrivent dans l'ordre d'avant
    ranges = QuoteRanges(use_memo=use_memo)
    staged = []
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
                    staged.append(("excl", _excl("observation_line", f"{ck}/{r['pass_id']}/schema", "validation_failed",
                                                 "; ".join(r.get("errors", [])), b, as_of, raw=r.get("raw"))))
        text_norm = textnorm.norm_for_match(b["text"]).lower()
        for n, l in enumerate(lines):
            asked = []
            errs, _ = semantic_errors(l, b, text_norm=text_norm, locate=lambda blk, q: asked.append(q))
            q = asked[0] if asked else None
            staged.append(("line", b, n, l, errs, q, ranges.request(b, q) if q is not None else None))
    ranges.resolve()
    for item in staged:
        if item[0] == "excl":
            excl.append(item[1])
            continue
        _, b, n, l, errs, q, key = item
        locator = ranges.locator(b, q, key) if q is not None else None
        state = "valid" if not errs else "rejected_semantic"
        row = _obs_row(l, b, n, state, errs, locator)
        g = line_group(b, as_group, canon, attached)
        if g:
            row["group_id"] = g
        rows.append(row)
        if errs:
            excl.append(_excl("observation_line", row["obs_key"], "validation_failed", "; ".join(errs), b,
                              as_of, raw=json.dumps(l, ensure_ascii=False)))
    ranges.save()
    if rows:
        df = pd.DataFrame(rows)
        con.register("df_obs", df)
        cols = ", ".join(df.columns)
        con.execute(f"INSERT INTO observations ({cols}) SELECT {cols} FROM df_obs")
        con.unregister("df_obs")
    return rows, excl


# D-0067, point 5 : une capacité se lit dans sa citation, avec son unité, en chiffres ou en lettres jusqu'à vingt
_CAP_WORDS = {w: i for i, w in enumerate(("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                          "fourteen fifteen sixteen seventeen eighteen nineteen twenty").split())}
_CAP_UNITS = {"MW": r"(?:MWs?|mega-?watts?)", "GW": r"(?:GWs?|giga-?watts?)"}
_CAP_NUM = r"(\d[\d,]*(?:\.\d+)?|" + "|".join(sorted(_CAP_WORDS, key=len, reverse=True)) + r"|an?)"
_CAP_QUAL = r"(?:(?:additional|more|new|incremental|further|total|aggregate)\s+)?"   # « 3.8 additional gigawatts » (point 16)
_CAP_PAREN = r"(?:\(\s*(\d[\d,]*(?:\.\d+)?)\s*\)\s*)?"   # « one (1) gigawatt », le chiffre entre parenthèses doit égaler le mot


def capacity_in_quote(quote, value, unit):
    """La capacité `value` (MW ou GW, telle qu'écrite) figure dans la citation, accolée à son unité :
    « 200 MW », « 1.2GW », « six gigawatts », « a gigawatt », « 1,000-megawatt », ou séparée d'elle par un seul
    qualificatif d'une liste fermée (« 3.8 additional gigawatts ») ; un mot suivi du même chiffre entre parenthèses
    vaut ce nombre (« one (1) gigawatt »)."""
    if not quote or value is None or unit not in _CAP_UNITS:
        return False
    rx = re.compile(r"(?<![\w.])" + _CAP_NUM + r"\s*-?\s*" + _CAP_PAREN + _CAP_QUAL + _CAP_UNITS[unit] + r"\b", re.I)
    want = Decimal(str(value))
    for m in rx.finditer(textnorm.norm_for_match(quote)):
        g = m.group(1).lower()
        try:
            got = Decimal(1) if g in ("a", "an") else Decimal(_CAP_WORDS[g]) if g in _CAP_WORDS else Decimal(g.replace(",", ""))
            if m.group(2) is not None and Decimal(m.group(2).replace(",", "")) != got:
                continue
        except InvalidOperation:
            continue
        if got == want:
            return True
    return False


def semantic_errors(line, block, text_norm=None, locate=None):
    """Citation retrouvée mot pour mot, contrepartie présente dans le bloc, montant égal
    au fait candidat quand l'origine est tagged_reference (§7.4). `text_norm` : texte du bloc
    déjà normalisé ; `locate` remplace la localisation directe de la citation (load_observations
    la diffère pour chercher les citations document par document)."""
    errs = []
    if text_norm is None:
        text_norm = textnorm.norm_for_match(block["text"]).lower()
    locator = None
    q = line.get("quote")
    if q:
        if textnorm.norm_for_match(q).lower() not in text_norm:
            errs.append("citation introuvable mot pour mot dans le bloc")
        else:
            locator = (locate or _locate)(block, q)
    if line.get("exhibit_title") and textnorm.norm_for_match(line["exhibit_title"]).lower() not in text_norm:
        errs.append("titre de pièce introuvable dans le bloc")
    cp = line.get("counterparty_name")
    if cp and line.get("counterparty_evidence") in ("named", "derivable"):
        if textnorm.norm_for_match(cp).lower() not in text_norm:
            # libellés de membre en clair (apostrophes typographiques comprises), même normalisation que le texte
            cands = textnorm.norm_for_match(" ".join(json.dumps(c.get("dims"), ensure_ascii=False)
                                                     for c in block.get("candidate_facts") or [])).lower()
            if line.get("derivation_method") != "dimension_member_label" or \
                    textnorm.norm_for_match(cp).lower() not in cands:
                errs.append("contrepartie absente du bloc")
    if line.get("amount_origin") == "tagged_reference":
        cand = next((c for c in block.get("candidate_facts") or [] if c["fact_key"] == line.get("candidate_fact_key")), None)
        if cand is None:
            errs.append("candidate_fact_key absent des faits candidats du bloc")
        elif line.get("amount") is not None and abs(Decimal(str(line["amount"]))) != abs(Decimal(str(cand["value"]))):
            # montants en valeur absolue (guide de lecture) : une perte balisée en négatif reste le même fait
            errs.append("montant différent du fait candidat")
    if line.get("amount_origin") == "narrative_only" and line.get("amount") is not None:
        # même valeur ET même période (ou ligne sans période) : un montant d'une autre
        # période, égal par hasard à un fait balisé, reste un texte non balisé
        # même date aussi : la fin de période de la ligne, sinon sa date d'événement, comprise dans la
        # période du fait ; un plafond daté du jour de l'accord ou un encours d'une autre date n'est
        # pas le même fait qu'un remboursement de même montant
        pe, ed = line.get("period_end"), line.get("event_date")

        def same_date(c):
            ce, cs = str(c.get("period_end") or "")[:10], str(c.get("period_start") or "")[:10]
            if pe:
                return ce == pe
            if ed:
                return ce == ed or (len(cs) == 10 and cs <= ed <= ce)
            return True
        same = [c for c in block.get("candidate_facts") or []
                if abs(Decimal(str(c["value"]))) == abs(Decimal(str(line["amount"]))) and same_date(c)]
        if same:
            errs.append("montant présent dans un fait candidat : tagged_reference attendu")
    if line.get("amount") is not None and line.get("unit") in ("USD", "EUR", "GBP", "JPY") and \
            line.get("currency") not in (None, line.get("unit")):
        errs.append("unité et devise incohérentes")
    if line.get("capacity_value") is not None and not capacity_in_quote(q, line["capacity_value"], line.get("capacity_unit")):
        errs.append("capacité introuvable dans la citation avec son unité (D-0067, point 5)")
    from .ppe_notes import semantic_errors as component_errors     # composante et état nommés (D-0076, point 5)
    errs += component_errors(line)
    return errs, locator


def _locate(block, quote):
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


QUOTE_RANGES = config.DB_DIR / "memo" / "quote_ranges.json"
_PENDING, _FAILED = object(), object()
PARALLEL_MIN_DOCS = 8        # au-delà, la recherche se répartit sur un pool de processus (D-0072, point 3 b)
FAILED = "failed"            # plage d'un document illisible ou d'une recherche en erreur, entre processus


def ranges_of_document(job):
    """Plages des citations d'un document en cache : ([(clé, plage, None ou FAILED)], citations cherchées). Le document
    est décompressé et décodé une fois ; une erreur de lecture vaut FAILED pour toutes ses citations, une erreur de
    recherche pour la seule citation (comme la recherche en série d'avant)."""
    from pathlib import Path
    from . import cache as cachemod
    path, items = job
    try:
        raw = cachemod.read(Path(path))
        text, enc = textnorm.decode(raw), textnorm.raw_encoding(raw)
    except Exception:
        return [(k, FAILED) for k, _, _ in items], 0
    out, n = [], 0
    for k, start, quote in items:
        try:
            start_char = len(textnorm.decode(raw[:start])) if start else 0
            r = textnorm.locate_in_text(text, enc, quote, start_char)
            out.append((k, list(r) if r else None))
            n += 1
        except Exception:
            out.append((k, FAILED))
    return out, n


class QuoteRanges:
    """Plages d'octets des citations dans leur document en cache (§9.2), gardées d'un réassemblage
    à l'autre dans db/memo : une plage ne dépend que du document, du début du bloc, de la citation et
    du code qui la cherche. La clé porte la taille et la date de modification du document, et le mémo
    l'empreinte de ce code (textnorm.py, cache.py, cette classe, ranges_of_document) : un document ou un code modifié se
    recherche. Les citations à chercher le sont document par document, chacun décompressé et décodé
    une fois. Le mémo ne garde que les clés de la dernière exécution ; le supprimer ne change rien
    aux tables, seulement à la durée (même calcul que _locate)."""

    def __init__(self, path=QUOTE_RANGES, use_memo=True):
        self.path = path
        self.version = self.code_version()
        self.known = {}
        if use_memo and path.exists():
            try:
                d = json.loads(path.read_text(encoding="utf-8"))
                if d.get("version") == self.version:
                    self.known = d["ranges"]
            except (OSError, ValueError, KeyError, TypeError):
                self.known = {}
        self.used, self.todo, self.searched = {}, {}, 0

    @classmethod
    def code_version(cls):
        import hashlib
        import inspect
        h = hashlib.sha256()
        for name in ("textnorm.py", "cache.py"):
            h.update((config.ROOT / "pipeline" / name).read_bytes())
        h.update(inspect.getsource(cls).encode("utf-8"))
        h.update(inspect.getsource(ranges_of_document).encode("utf-8"))   # la recherche d'un document (D-0072)
        return h.hexdigest()

    def request(self, block, quote):
        """Clé de la plage d'une citation, mise en attente si elle n'est pas connue ; None si le
        document n'est pas lisible en cache (la plage vaut alors None, comme dans _locate)."""
        import hashlib
        from . import cache as cachemod
        loc = block.get("locator") or {}
        try:
            p = cachemod.archive_path(loc["cik"], loc["accession"], loc["file"])
            st = p.stat()
        except Exception:
            return None
        start = (loc.get("byte_range") or [0])[0]
        k = "\t".join([str(p.relative_to(config.ROOT)) if p.is_relative_to(config.ROOT) else str(p),
                       str(st.st_size), str(st.st_mtime_ns), json.dumps(start),
                       hashlib.sha256(quote.encode("utf-8")).hexdigest()])
        if k not in self.used:
            if k in self.known:
                self.used[k] = self.known[k]
            else:
                self.used[k] = _PENDING
                self.todo.setdefault(p, []).append((k, start, quote))
        return k

    def resolve(self):
        """Cherche les citations en attente, un document à la fois. Au-delà de PARALLEL_MIN_DOCS documents, les documents
        se répartissent sur un pool de processus (D-0072, point 3 b) ; chacun est cherché d'un bloc, par le même calcul,
        et les plages se rangent par clé, dans le même ordre."""
        import os
        jobs = [(str(p), self.todo[p]) for p in sorted(self.todo, key=str)]
        if len(jobs) > PARALLEL_MIN_DOCS:
            import multiprocessing
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=os.cpu_count() or 1,
                                     mp_context=multiprocessing.get_context("spawn")) as pp:
                results = list(pp.map(ranges_of_document, jobs, chunksize=4))
        else:
            results = [ranges_of_document(j) for j in jobs]
        for found, n in results:
            for k, r in found:
                self.used[k] = _FAILED if r == FAILED else r
            self.searched += n
        self.todo = {}

    def locator(self, block, quote, key):
        """Même texte que _locate : localisation du bloc, citation, plage (None si introuvable)."""
        loc = dict(block.get("locator") or {})
        loc["quote"] = quote
        r = self.used.get(key) if key is not None else None
        loc["quote_byte_range"] = r if isinstance(r, list) else None
        return json.dumps(loc, ensure_ascii=False)

    def save(self):
        ranges = {k: v for k, v in self.used.items() if v is None or isinstance(v, list)}
        if ranges == self.known:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps({"version": self.version, "ranges": ranges}, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)


def _line_level(b, l):
    """Niveau et assurance d'une ligne : ceux de son bloc, sauf dans un jeu de notes qui mêle exercices audités et
    période intermédiaire non auditée (D-0077, point 9) : une ligne datée après `audited_through` est de niveau C."""
    cut, end = b.get("audited_through"), l.get("period_end") or l.get("event_date")
    if cut and end and str(end)[:10] > cut:
        return "C", "unaudited"
    return b.get("tier"), b.get("assurance_level")


def _obs_row(l, b, n, state, errs, locator):
    known = {k: l.get(k) for k in reader.LINE_FIELDS}
    tier, assurance = _line_level(b, l)
    row = {
        "obs_key": f"{b['content_key']}/{l.get('pass_id')}/{n}", "content_key": b["content_key"],
        "pass_as_of": l.get("as_of"), "pass_id": l.get("pass_id"), "line_no": n,
        "block_kind": b["block_kind"], "doc_key": f"{b['cik']}/{b['accession']}/{b['document']}",
        "group_id": b["group_id"], "cik": b["cik"], "accession": b["accession"], "form": b["form"],
        "item": b.get("item"), "exhibit_type": b.get("exhibit_type"), "knowledge_date": b["knowledge_date"],
        "filing_status": b.get("filing_status", "filed"), "assurance_level": assurance,
        "tier": tier, "framework": block_framework(b), "locator": locator, "validation_state": state,
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


EXCL_DUPLICATES = {"dropped": 0, "collision_keys": 0, "examples": []}   # D-0069, point 9


def insert_exclusions(con, rows):
    """Une exclusion par clé, la première ; les doublons écartés sont comptés dans EXCL_DUPLICATES."""
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    dup = df.duplicated("exclusion_key", keep=False)
    if dup.any():
        sub = df[dup].astype(str)
        distinct = sub.groupby("exclusion_key", sort=False).apply(lambda x: len(x.drop_duplicates()), include_groups=False)
        EXCL_DUPLICATES["dropped"] += len(sub) - len(distinct)
        EXCL_DUPLICATES["collision_keys"] += int((distinct > 1).sum())
        EXCL_DUPLICATES["examples"] = (EXCL_DUPLICATES["examples"] + list(distinct[distinct > 1].index[:10]))[:10]
    df = df.drop_duplicates("exclusion_key")
    for c in ("exclusion_key", "item_kind", "item_key", "reason", "detail", "group_id", "accession",
              "content_key", "invariant", "raw", "as_of"):
        if c not in df.columns:
            df[c] = None
    con.register("df_ex", df)
    con.execute("""INSERT INTO exclusions SELECT exclusion_key, item_kind, item_key, reason, detail, group_id,
                   accession, content_key, invariant, raw, as_of FROM df_ex""")
    con.unregister("df_ex")
    return len(df)
