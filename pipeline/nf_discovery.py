"""Piste des non-déposants de la découverte (§10.4, §14, D-0044) : qui, dans EDGAR, nomme un
groupe économique qui ne dépose pas lui-même, SoftBank.

La piste a ses extraits, sa file et son état de lecture, distincts de la découverte d'origine
(D-0036), dont le lexique, le classement et la file ne changent pas. Les archives des Notes
Data Sets sont retirées et scannées avec le lexique d'ensemble, pour savoir quelles autres
cibles une ligne nomme ; ne sont gardées que les lignes qui nomment un non-déposant.

    python -m pipeline.nf_discovery fetch         # archives retirées et scannées
    python -m pipeline.nf_discovery snapshot      # état des unités avant un lexique enrichi (D-0058, point 24)
    python -m pipeline.nf_discovery search [new]  # recherche plein texte des EX-10 ; « new » : termes non encore cherchés
    python -m pipeline.nf_discovery verify        # EX-10 tirés, règles du lexique appliquées
    python -m pipeline.nf_discovery candidates    # candidats, classement, unités, règle de lecture
    python -m pipeline.nf_discovery prepare N     # blocs des N unités retenues suivantes
    python -m pipeline.nf_discovery own           # unités du document d'enregistrement d'un non-déposant
    python -m pipeline.nf_discovery prepare_own   # blocs de ses unités retenues
    python -m pipeline.nf_discovery status
"""
import datetime as dt
import hashlib
import json
import re
import sys

import pandas as pd

from . import cache, config, net
from . import discovery as D

MANIFEST = D.BASE / "manifest_nf.jsonl"
SUBDIR = "nf"
EFTS_HITS = config.DB_DIR / "nf_discovery_efts.parquet"
EX10 = config.DB_DIR / "nf_discovery_ex10.parquet"
MENTIONS = config.DB_DIR / "nf_discovery_mentions.parquet"
CANDIDATES = config.DB_DIR / "nf_discovery_candidates.parquet"
UNITS = config.DB_DIR / "nf_discovery_units.parquet"
CATALOG = config.DB_DIR / "nf_discovery_blocks.jsonl"
BUILT = config.DB_DIR / "nf_discovery_built.jsonl"


# -- lexique ------------------------------------------------------------------------------

def nf_lexicon(cfg=None):
    """Termes de la piste (`discovery.non_filer.lexicon`), au format du lexique d'origine."""
    cfg = cfg or config.load()
    d = (cfg.get("discovery") or {}).get("non_filer") or {}
    return [{"term": e["term"], "ref": e["ref"], "case": bool(e.get("case_sensitive")),
             "from": e.get("valid_from"), "to": e.get("valid_to")} for e in d.get("lexicon") or []]


def nf_refs(cfg=None):
    return {e["ref"] for e in nf_lexicon(cfg)}


def union_lexicon(cfg=None):
    """Lexique d'ensemble : celui de la découverte d'origine, puis les termes de la piste. Les
    co-mentions (groupe, laboratoire ou Stargate dans la même unité) s'y lisent."""
    cfg = cfg or config.load()
    return D.lexicon(cfg) + nf_lexicon(cfg)


def version(cfg=None):
    return D.lexicon_version(union_lexicon(cfg))


def is_non_filer(ref):
    """Groupe économique qui ne dépose pas (§10.4) : laboratoire ou autre non-déposant."""
    return str(ref).startswith(("LAB:", "NF:"))


# -- archives -----------------------------------------------------------------------------

def manifest():
    if not MANIFEST.exists():
        return {}
    out = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        out[r["name"]] = r
    return out


def scanned_archives(lv=None):
    lv = lv or version()
    return [n for n, r in manifest().items() if r.get("status") == "scanned" and r.get("lexicon_version") == lv]


def coverage_ok():
    todo = {a["name"] for a in D.in_period(D.archive_list(), D.period_start())}
    return todo <= set(scanned_archives())


def _scan_job(name, zpath, lex, excluded, keep, meta):
    """Scan d'une archive dans un processus à part ; les extraits vont sous {archive}/nf/. La
    table `sub` et la liste des valeurs tronquées ne dépendent pas du lexique : la découverte
    d'origine les garde déjà."""
    h = hashlib.sha256()
    with open(zpath, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    out, stats = D.scan(zpath, lex, excluded, keep_refs=keep)
    d = D.BASE / name / SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    for k, df in out.items():
        if k in ("sub", "truncated"):
            continue
        df.to_parquet(d / f"{k}.parquet", index=False, compression="zstd")
    return dict(meta, status="scanned", sha256=h.hexdigest(), bytes=zpath.stat().st_size, stats=stats)


def fetch(only=None, workers=3):
    """Téléchargement par le client unique (§9.5), de la plus récente archive à la plus
    ancienne ; scan en parallèle, sans requête réseau ; l'archive est effacée après le scan."""
    from concurrent.futures import ProcessPoolExecutor, FIRST_COMPLETED, wait
    cfg = config.load()
    lex = union_lexicon(cfg)
    lv = D.lexicon_version(lex)
    keep = nf_refs(cfg)
    todo = D.in_period(D.archive_list(), D.period_start(cfg))
    done = manifest()
    client = net.SecClient(config.as_of(), cfg)
    excluded = D.group_ciks(cfg)
    tmpdir = D.BASE / "tmp"
    tmpdir.mkdir(parents=True, exist_ok=True)
    pending = {}

    def drain(block):
        if not pending:
            return
        fin = wait(list(pending), return_when=FIRST_COMPLETED)[0] if block else [f for f in pending if f.done()]
        for f in fin:
            name, zpath = pending.pop(f)
            rec = f.result()
            with open(MANIFEST, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            zpath.unlink()
            print(name, json.dumps(rec["stats"]), flush=True)

    with ProcessPoolExecutor(max_workers=workers) as ex:
        for a in todo:
            if only and a["name"] not in only:
                continue
            if a["name"] in done and done[a["name"]].get("lexicon_version") == lv:
                continue
            while len(pending) >= workers:
                drain(True)
            zpath = tmpdir / (a["name"] + ".nf.zip")
            t0 = dt.datetime.now(dt.timezone.utc)
            try:
                _, headers = client.get(a["url"], timeout=900, dest=zpath)
            except net.NotCollected as exc:
                rec = {"name": a["name"], "url": a["url"], "status": "not_collected", "reason": str(exc),
                       "lexicon_version": lv, "retrieved": t0.isoformat(timespec="seconds")}
                with open(MANIFEST, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(a["name"], "not_collected", exc, flush=True)
                continue
            meta = {"name": a["name"], "url": a["url"], "last_modified": headers.get("Last-Modified"),
                    "filed_from": a["filed_from"], "filed_to": a["filed_to"],
                    "retrieved": t0.isoformat(timespec="seconds"), "lexicon_version": lv}
            pending[ex.submit(_scan_job, a["name"], zpath, lex, excluded, keep, meta)] = (a["name"], zpath)
            drain(False)
        while pending:
            drain(True)


def status():
    cfg = config.load()
    lv = version(cfg)
    todo = D.in_period(D.archive_list(), D.period_start(cfg))
    ok = set(scanned_archives(lv))
    print(f"piste des non-déposants : lexique {lv} ; archives {len(ok & {a['name'] for a in todo})}/{len(todo)} scannées")
    for p in (EFTS_HITS, EX10, CANDIDATES, UNITS, CATALOG):
        print(" ", p.name, "présent" if p.exists() else "absent")


# -- recherche plein texte : EX-10 qui nomment un non-déposant (D-0044, point 4) -------------

QUERY_LOG = config.WORK / "discovery" / "efts_queries_nf.jsonl"


def search(rate=None, new_only=False):
    """La phrase de chaque terme de la piste, du 2017-01-01 à as_of, sur les formulaires racines
    des EX-10 (D-0036, point 5) ; pas de Form D. `new_only` : seuls les termes absents des résultats
    déjà gardés sont cherchés, et leurs résultats s'ajoutent aux anciens (D-0058, point 24)."""
    cfg = config.load()
    client = net.SecClient(config.as_of(), cfg)
    if rate:
        client.min_interval = 1.0 / rate
    old = pd.read_parquet(EFTS_HITS) if new_only and EFTS_HITS.exists() else None
    done = set(old["term"]) if old is not None else set()
    rows = []
    for e in nf_lexicon(cfg):
        if e["term"] in done:
            continue
        rows += D.harvest(client, e["term"], D.EX10_FORMS,
                          keep=lambda s: str(s.get("file_type") or "").upper().startswith("EX-10"), log=QUERY_LOG)
        print(e["term"], len(rows), client.stats["requests"], flush=True)
    df = pd.DataFrame(rows)
    if old is not None:
        df = pd.concat([old, df], ignore_index=True)
    df.to_parquet(EFTS_HITS, index=False)
    print("hits", len(df), "requêtes", client.stats["requests"])


def verify(rate=4.0):
    """EX-10 de déposants hors des groupes : pièce tirée, texte normalisé, termes du lexique
    d'ensemble en mots entiers, hors du nom du déposant. Une pièce est une mention de la piste si
    elle nomme un non-déposant ; les autres cibles qu'elle nomme sont ses co-mentions (R1)."""
    from concurrent.futures import ThreadPoolExecutor
    cfg = config.load()
    lex = union_lexicon(cfg)
    rx, _ = D.compile_lexicon(lex)
    keep = nf_refs(cfg)
    excluded = D.group_ciks(cfg)
    client = net.SecClient(config.as_of(), cfg)
    client.min_interval = 1.0 / rate
    h = pd.read_parquet(EFTS_HITS)
    h = h[h["file_type"].fillna("").str.upper().str.startswith("EX-10")].drop_duplicates("id")

    def one(r):
        names = D._display(r["display_names"])
        filers = [(n, c) for n, c in names if str(int(c)) not in excluded]
        if not filers:
            return None
        name, cik10 = filers[0]
        acc = r["adsh"]
        path = cache.archive_path(cik10, acc, r["file"])
        try:
            if path.exists():
                raw = cache.read(path)
            else:
                url = f"{D.SEC}/Archives/edgar/data/{int(cik10)}/{acc.replace('-', '')}/{r['file']}"
                raw, _ = client.get(url)
                cache.write(path, raw)
        except net.NotCollected as exc:
            return {"id": r["id"], "status": "not_collected", "reason": str(exc)}
        text, how = D.plain_text(raw)
        period = (r["file_date"] or "").replace("-", "")
        hits = D.find_mentions(text, rx, lex, lambda t: D.own_name_spans(t, [n for n, _ in names]))
        refs, terms, first = set(), set(), None
        for i, a, b in hits:
            e = lex[i]
            if not D.ref_valid(e, period):
                continue
            refs.add(e["ref"])
            terms.add(e["term"])
            if e["ref"] in keep:
                first = a if first is None else min(first, a)
        nf = refs & keep
        return {"id": r["id"], "status": "verified" if nf else "no_mention", "cik": str(int(cik10)),
                "filer": name, "adsh": acc, "file": r["file"], "file_type": r["file_type"], "form": r["form"],
                "file_date": r["file_date"], "groups": sorted(nf), "co_refs": ";".join(sorted(refs - keep)),
                "terms": ";".join(sorted(terms)), "chars": len(text), "first_mention_char": first,
                "text_method": how}

    def safe(r):
        try:
            return one(r)
        except Exception as exc:                 # une pièce illisible ne coupe pas la vérification
            return {"id": r["id"], "status": "parse_failed", "reason": f"{type(exc).__name__}: {exc}"[:300]}

    rows = []
    with ThreadPoolExecutor(max_workers=8) as tp:
        for out in tp.map(safe, [r for _, r in h.iterrows()]):
            if out:
                rows.append(out)
    df = pd.DataFrame(rows)
    df.to_parquet(EX10, index=False)
    print(df["status"].value_counts().to_dict() if len(df) else {}, client.stats["requests"])
    return df


# -- mentions, candidats, unités et règle de lecture (D-0044, point 5) -----------------------

def note_mentions(cfg=None):
    """Une ligne par (ligne de txt retenue, non-déposant nommé), avec les autres cibles nommées
    dans la même valeur à la date du dépôt (co-mentions)."""
    cfg = cfg or config.load()
    lex = union_lexicon(cfg)
    by_term = {(e["term"], e["ref"]): e for e in lex}
    keep = nf_refs(cfg)
    rows = []
    for name in scanned_archives():
        d = D.BASE / name
        p = d / SUBDIR / "txt.parquet"
        if not p.exists():
            continue
        txt = pd.read_parquet(p)
        if txt.empty:
            continue
        sub = pd.read_parquet(d / "sub.parquet", columns=D.SUB_COLS)
        txt = txt.merge(sub, on="adsh", how="left")
        for r in txt.itertuples(index=False):
            refs, terms = set(), set()
            for term, ref, a, b in json.loads(r.mentions):
                e = by_term.get((term, ref))
                if e is None or not D.ref_valid(e, r.period):
                    continue
                refs.add(ref)
                terms.add(term)
            nf = refs & keep
            if not nf:
                continue
            cls = "related_party" if D.RELATED_TAG.search(r.tag) else "note"
            for g in sorted(nf):
                rows.append({"archive": name, "adsh": r.adsh, "cik": r.cik, "filer": r.name, "form": r.form,
                             "filed": r.filed, "period": r.period, "tag": r.tag, "version": r.version,
                             "value_sha": hashlib.sha256(r.value.encode("utf-8")).hexdigest()[:16],
                             "chars": len(r.value), "truncated": bool(r.truncated), "class": cls, "group": g,
                             "co_refs": ";".join(sorted(refs - keep)), "terms": ";".join(sorted(terms))})
    return pd.DataFrame(rows)


def all_mentions(cfg=None):
    """Mentions des notes et des EX-10 vérifiés ; une ligne par (document, non-déposant)."""
    cfg = cfg or config.load()
    nm = note_mentions(cfg)
    amts = D.documented_amounts(set(nm["adsh"]), lex=nf_lexicon(cfg), archives=scanned_archives(),
                                subdir=SUBDIR) if len(nm) else {}
    rows = []
    for r in nm.to_dict("records"):
        a = amts.get((r["adsh"], r["group"]))
        rows.append({"cik": str(r["cik"]), "filer": r["filer"], "class": r["class"], "group": r["group"],
                     "adsh": r["adsh"], "doc": r["tag"], "form": r["form"], "date": r["filed"], "period": r["period"],
                     "amount": a[0] if a else None, "amount_basis": (f"num:{a[1]}:{a[2]}:{a[3]}:{a[4]}" if a else None),
                     "archive": r["archive"], "value_sha": r["value_sha"], "chars": r["chars"], "terms": r["terms"],
                     "truncated": r["truncated"], "co_refs": r["co_refs"]})
    if EX10.exists():
        ex = pd.read_parquet(EX10)
        ex = ex[ex["status"] == "verified"]
        for r in ex.itertuples(index=False):
            for g in r.groups:
                rows.append({"cik": r.cik, "filer": r.filer, "class": "contract", "group": g, "adsh": r.adsh,
                             "doc": r.file, "form": r.form, "date": (r.file_date or "").replace("-", ""),
                             "period": None, "amount": None, "amount_basis": None, "archive": None,
                             "value_sha": None, "chars": r.chars, "terms": r.terms, "truncated": False,
                             "co_refs": r.co_refs or ""})
    return pd.DataFrame(rows)


def _split_refs(s):
    return [x for x in (s or "").split(";") if x]


def rank_candidates(m):
    """Classement de D-0036 : classe de mention, montant documenté décroissant (sans montant
    ensuite), nombre de cibles nommées (non-déposant et co-mentions), accession."""
    out = []
    for cik, g in m.groupby("cik"):
        best = min(D.CLASS_ORDER[c] for c in g["class"])
        best_rows = g[g["class"].map(D.CLASS_ORDER) == best]
        amts = [a for a in g["amount"] if a is not None and a == a]
        targets = set(g["group"]) | {x for s in g["co_refs"] for x in _split_refs(s)}
        out.append({"cik": cik, "filer": g.sort_values("date")["filer"].iloc[-1],
                    "best_class": [k for k, v in D.CLASS_ORDER.items() if v == best][0],
                    "documented_amount": max(amts) if amts else None,
                    "n_targets": len(targets), "targets": ";".join(sorted(targets)),
                    "first_accession": min(best_rows["adsh"]), "n_mentions": len(g),
                    "n_documents": g[["adsh", "doc"]].drop_duplicates().shape[0],
                    "classes": ";".join(sorted(g["class"].unique(), key=D.CLASS_ORDER.get))})
    c = pd.DataFrame(out)
    c["_cls"] = c["best_class"].map(D.CLASS_ORDER)
    c["_noamt"] = c["documented_amount"].isna()
    c["_amt"] = -c["documented_amount"].fillna(0)
    c = c.sort_values(["_cls", "_noamt", "_amt", "n_targets", "first_accession"],
                      ascending=[True, True, True, False, True]).drop(columns=["_cls", "_noamt", "_amt"])
    c.insert(0, "rank", range(1, len(c) + 1))
    return c.reset_index(drop=True)


def reading_units(m, c):
    """Unités dans l'ordre de D-0036 (point 8) : (A) en-têtes d'EX-10 et notes du dépôt le plus
    récent de chaque candidat, dans l'ordre du classement ; (B) ses autres notes, du plus récent au
    plus ancien. Un texte identique n'est qu'une unité ; les co-mentions d'une unité réunissent
    celles de ses lignes."""
    rank = dict(zip(c["cik"], c["rank"]))
    units, seen = [], set()
    notes = m[m["class"].isin(["related_party", "note"])]
    exs = m[m["class"] == "contract"]

    def co_of(rows):
        return ";".join(sorted({x for s in rows["co_refs"] for x in _split_refs(s)}))
    for cik in c["cik"]:
        r = rank[cik]
        e = exs[exs["cik"] == cik]
        for x in e.drop_duplicates(["adsh", "doc"]).sort_values("date", ascending=False).itertuples(index=False):
            same = e[(e["adsh"] == x.adsh) & (e["doc"] == x.doc)]
            units.append({"pass": "A", "rank": r, "cik": cik, "kind": "exhibit_header", "adsh": x.adsh,
                          "doc": x.doc, "date": x.date, "archive": None, "value_sha": None,
                          "groups": ";".join(sorted(same["group"])), "co_refs": co_of(same), "latest": True})
        n = notes[notes["cik"] == cik]
        if n.empty:
            continue
        docs = n.drop_duplicates(["adsh", "doc"]).sort_values(["date", "adsh"], ascending=[False, False])
        latest = docs["adsh"].iloc[0]
        for x in docs.itertuples(index=False):
            if x.value_sha in seen:
                continue
            seen.add(x.value_sha)
            same = n[(n["adsh"] == x.adsh) & (n["doc"] == x.doc)]
            units.append({"pass": "A" if x.adsh == latest else "B", "rank": r, "cik": cik, "kind": "note",
                          "adsh": x.adsh, "doc": x.doc, "date": x.date, "archive": x.archive,
                          "value_sha": x.value_sha, "groups": ";".join(sorted(same["group"])),
                          "co_refs": co_of(same), "latest": x.adsh == latest})
    u = pd.DataFrame(units)
    u["_p"] = u["pass"].map({"A": 0, "B": 1})
    u = u.sort_values(["_p", "rank", "date", "adsh", "doc"], ascending=[True, True, False, False, True],
                      kind="mergesort").drop(columns=["_p"])
    u.insert(0, "order", range(1, len(u) + 1))
    return u.reset_index(drop=True)


def select_units(u, c, cap):
    """Règle de lecture fixée avant de voir les candidats (D-0044, point 5) : (R1) unité qui nomme
    aussi un groupe, un laboratoire ou Stargate ; (R2) note du dépôt le plus récent d'un candidat
    qui a un montant documenté. R1 puis R2, chacun dans l'ordre de la file ; au-delà du plafond,
    l'unité retenue reste non traitée. Colonnes ajoutées : rule, queue (rang dans la file
    retenue), status (queued, over_cap, out_of_rule)."""
    has_amt = set(c.loc[c["documented_amount"].notna(), "cik"])
    u = u.copy()
    r1 = u["co_refs"].fillna("") != ""
    r2 = (~r1) & (u["kind"] == "note") & u["latest"].astype(bool) & u["cik"].isin(has_amt)
    u["rule"] = None
    u.loc[r1, "rule"] = "R1"
    u.loc[r2, "rule"] = "R2"
    sel = pd.concat([u[r1], u[r2]])                 # R1 puis R2, chacun dans l'ordre de la file
    pos = {o: i + 1 for i, o in enumerate(sel["order"])}
    u["queue"] = u["order"].map(pos)
    u["status"] = "out_of_rule"
    u.loc[u["queue"].notna() & (u["queue"] <= cap), "status"] = "queued"
    u.loc[u["queue"].notna() & (u["queue"] > cap), "status"] = "over_cap"
    return u


UNIT_KEY = ["kind", "adsh", "doc", "value_sha"]


def own_group_ciks(cfg=None, ref="NF:SOFTBANK"):
    """CIK (sans zéros) -> date d'entrée des déposants du groupe non déposant lui-même : déposants
    rattachés par extrait avec leur CIK (D-0055, point 8) et CIK propres de SoftBank (D-0058, point 4)."""
    cfg = cfg or config.load()
    out = {str(int(c["cik"])): c.get("valid_from") or "none" for c in cfg.get("confirmed_entities") or []
           if c.get("group") == ref and str(c.get("cik") or "").strip().isdigit()}
    for c in ((cfg.get("softbank_deep") or {}).get("own_ciks") or []) if ref == "NF:SOFTBANK" else []:
        out.setdefault(str(int(c["cik"])), "none")
    return out


def select_with_prior(u, c, prior, cap, file, own=None):
    """File propre des unités nouvelles (D-0058, point 24) : une unité déjà connue de `prior` (état
    gardé sous sa clé) garde sa règle, son rang et son état ; les unités que nul terme antérieur ne
    faisait naître forment une file à part, R1 puis R2, avec son propre plafond. Une unité nouvelle
    tirée d'un dépôt propre du groupe (`own` : CIK -> date d'entrée), déjà lu comme texte du groupe,
    n'entre pas dans la file (état own_group)."""
    def key(df):
        return ["|".join("" if v is None or v != v else str(v) for v in r)
                for r in df[UNIT_KEY].itertuples(index=False, name=None)]
    u = u.copy()
    pk = dict(zip(key(prior), prior.to_dict("records")))
    u["_k"] = key(u)
    old = u[u["_k"].isin(pk)].copy()
    for col in ("rule", "queue", "status"):
        old[col] = [pk[k].get(col) for k in old["_k"]]
    old["file"] = [pk[k].get("file") or "D-0044" for k in old["_k"]]
    fresh = u[~u["_k"].isin(pk)].drop(columns=["_k"])
    own = own or {}
    mine = [str(int(r.cik)) in own and (own[str(int(r.cik))] == "none" or
            str(r.date or "").replace("-", "") >= own[str(int(r.cik))].replace("-", ""))
            for r in fresh.itertuples(index=False)]
    mine = pd.Series(mine, index=fresh.index, dtype=bool)
    new = select_units(fresh[~mine], c, cap)
    grp = fresh[mine].copy()
    grp["rule"], grp["queue"], grp["status"] = None, None, "own_group"
    new = pd.concat([new, grp])
    new["file"] = file
    out = pd.concat([old.drop(columns=["_k"]), new], ignore_index=True)
    return out.sort_values("order", kind="mergesort").reset_index(drop=True)


def prior_path(cfg=None):
    nf = ((cfg or config.load())["discovery"].get("non_filer") or {}).get("reading") or {}
    f = nf.get("new_file") or {}
    return (config.DB_DIR / f["prior"]) if f.get("prior") else None


def snapshot():
    """État des unités avant l'enrichissement du lexique, gardé une fois (D-0058, point 24)."""
    p = prior_path()
    if p is None:
        raise SystemExit("aucune file nouvelle configurée (discovery.non_filer.reading.new_file)")
    if p.exists():
        print("état déjà gardé :", p.name)
        return
    pd.read_parquet(UNITS).to_parquet(p, index=False)
    print("état gardé :", p.name, len(pd.read_parquet(p)), "unités")


def build_candidates():
    cfg = config.load()
    reading = (cfg["discovery"].get("non_filer") or {}).get("reading") or {}
    cap = int(reading.get("cap_units", 300))
    m = all_mentions(cfg)
    c = rank_candidates(m)
    nf = reading.get("new_file") or {}
    pp = prior_path(cfg)
    if nf and pp is not None and pp.exists():
        u = select_with_prior(reading_units(m, c), c, pd.read_parquet(pp), int(nf.get("cap_units", cap)),
                              nf["decision"], own=own_group_ciks(cfg))
    else:
        u = select_units(reading_units(m, c), c, cap)
    m.to_parquet(MENTIONS, index=False)
    c.to_parquet(CANDIDATES, index=False)
    u.to_parquet(UNITS, index=False)
    print("mentions", len(m), "candidats", len(c), "unités", len(u))
    print(c.groupby("best_class").size().to_dict())
    print(u.groupby(["status", "rule", "kind"], dropna=False).size().to_dict())
    return m, c, u


# -- préparation des blocs retenus, dans l'ordre de la file ----------------------------------

def built_units():
    """État des unités préparées, sous leur clé (accession, document) : un lexique enrichi ne
    décale rien (D-0044, point 5)."""
    if not BUILT.exists():
        return {}
    out = {}
    for l in BUILT.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        out[(r["adsh"], r["doc"])] = r
    return out


class _Archive:
    """Extraits de la piste d'une archive (sub de la découverte d'origine), chargés une fois."""
    _cache = {}

    @classmethod
    def get(cls, name):
        if name not in cls._cache:
            if len(cls._cache) > 3:
                cls._cache.pop(next(iter(cls._cache)))
            d = D.BASE / name
            nd = d / SUBDIR
            sub = pd.read_parquet(d / "sub.parquet")
            ren = pd.read_parquet(nd / "ren.parquet")
            pre = pd.read_parquet(nd / "pre.parquet", columns=["adsh", "report", "tag", "version"])
            num = pd.read_parquet(nd / "num.parquet")
            dim = pd.read_parquet(nd / "dim.parquet")
            cls._cache[name] = {"sub": sub.set_index("adsh"), "ren": ren, "pre": pre, "num": num,
                                "dims": dict(zip(dim["dimhash"], dim["segments"]))}
        return cls._cache[name]


def _groups(u):
    return _split_refs(u["groups"]) + _split_refs(u["co_refs"])


def _note_block(u, client):
    a = _Archive.get(u["archive"])
    sub_row = a["sub"].loc[u["adsh"]].to_dict()
    sub_row["adsh"] = u["adsh"]
    pre = a["pre"]
    p = pre[(pre["adsh"] == u["adsh"]) & (pre["tag"] == u["doc"])]
    if p.empty:
        return None, "report_not_found"
    report = str(sorted(p["report"].astype(int))[0])
    ren_f = a["ren"][a["ren"]["adsh"] == u["adsh"]]
    rr = ren_f[ren_f["report"].astype(str) == report]
    shortname = rr["shortname"].iloc[0] if len(rr) else None
    fam = D.note_family(ren_f, report, shortname)
    tags = set(pre[(pre["adsh"] == u["adsh"]) & (pre["report"].astype(str).isin(fam))]["tag"])
    num = a["num"]
    num = num[(num["adsh"] == u["adsh"]) & (num["tag"].isin(tags))]
    m = {"adsh": u["adsh"], "class": "related_party" if D.RELATED_TAG.search(u["doc"]) else "note",
         "groups": _groups(u), "terms": None, "tag": u["doc"]}
    try:
        b = D.note_block(client, m, sub_row, report, shortname, num, a["dims"], f"nf{int(u['order']):07d}")
    except net.NotCollected as exc:
        return None, f"not_collected: {exc}"
    b["block_kind"] = "discovery_note"
    return b, None


def _exhibit_block(u, client):
    from . import blocks, sections
    from .graph import normalize_name
    ex = pd.read_parquet(EX10)
    r = ex[(ex["adsh"] == u["adsh"]) & (ex["file"] == u["doc"])].iloc[0]
    cik10 = str(r["cik"]).zfill(10)
    raw = cache.read(cache.archive_path(cik10, r["adsh"], r["file"]))
    head = sections.first_page(raw)
    fd = r["file_date"]
    return {"content_key": blocks.content_key(head, []), "block_kind": "discovery_exhibit_header",
            "signal_class": 5, "sort_key": f"nf{int(u['order']):07d}", "group_id": "CP:" + normalize_name(r["filer"]),
            "cik": cik10, "accession": r["adsh"], "form": r["form"], "filing_date": fd, "acceptance": None,
            "knowledge_date": fd, "period_start": None, "period_end": fd, "document": r["file"],
            "locator": {"file": r["file"], "accession": r["adsh"], "cik": cik10, "byte_range": None},
            "text": head, "candidate_facts": [], "chars": len(head),
            "normalizer_version": config.NORMALIZER_VERSION, "delimiter_version": config.DELIMITER_VERSION,
            "exhibit_type": r["file_type"], "filing_status": "filed", "assurance_level": "not_applicable",
            "tier": "D", "filer_name": r["filer"], "mention_class": "contract", "groups_named": _groups(u),
            "terms": r["terms"]}, None


def prepare(n=50, rate=4.0):
    """Blocs des `n` unités retenues suivantes de la file (une requête par page R), ajoutés au
    catalogue de la piste."""
    cfg = config.load()
    client = net.SecClient(config.as_of(), cfg)
    client.min_interval = 1.0 / rate
    units = pd.read_parquet(UNITS)
    units = units[units["status"] == "queued"]
    if "file" in units:
        units = units.assign(_f=(units["file"] != "D-0044").astype(int)).sort_values(["_f", "queue"])
    else:
        units = units.sort_values("queue")
    done = built_units()
    todo = [u for u in units.to_dict("records") if (u["adsh"], u["doc"]) not in done][:n]
    nb = 0
    for u in todo:
        b, err = (_exhibit_block if u["kind"] == "exhibit_header" else _note_block)(u, client)
        if b:
            b.update({"unit_order": int(u["order"]), "nf_queue": int(u["queue"]), "nf_rule": u["rule"]})
            with open(CATALOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(b, ensure_ascii=False) + "\n")
            nb += 1
        rec = {"order": int(u["order"]), "queue": int(u["queue"]), "rank": int(u["rank"]), "cik": u["cik"],
               "kind": u["kind"], "adsh": u["adsh"], "doc": u["doc"], "rule": u["rule"],
               "content_key": b["content_key"] if b else None, "error": err}
        with open(BUILT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"blocs préparés : {nb} sur {len(todo)} unités ; requêtes {client.stats['requests']}")


def prepare_body(adsh, doc):
    """Corps d'un EX-10 dont l'en-tête, lu, montre un groupe partie (D-0044, point 5) : lu après
    les notes, sous le même rang que son en-tête ; tiré du cache, sans requête."""
    from . import blocks, sections
    cat = [json.loads(x) for x in open(CATALOG, encoding="utf-8")]
    head = next(b for b in cat if b["accession"] == adsh and b["document"] == doc
                and b["block_kind"] == "discovery_exhibit_header")
    if any(b["accession"] == adsh and b["document"] == doc and b["block_kind"] == "discovery_exhibit_body"
           for b in cat):
        print("corps déjà au catalogue")
        return
    raw = cache.read(cache.archive_path(head["cik"], adsh, doc))
    full = sections.full_text(raw)
    b = dict(head)
    b.update({"content_key": blocks.content_key(full, []), "block_kind": "discovery_exhibit_body",
              "sort_key": head["sort_key"] + "b", "text": full, "chars": len(full), "nf_rule": head["nf_rule"] + "-corps",
              "requires": {"header_content_key": head["content_key"], "exhibit_type": head["exhibit_type"]}})
    with open(CATALOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(b, ensure_ascii=False) + "\n")
    print(f"corps ajouté : {b['content_key']} ({len(full)} caractères)")


# -- document d'enregistrement de la tête d'un groupe non déposant (D-0054, point 13) ----------
# La règle du nom propre écarte les pièces d'un déclarant qui est lui-même la tête du non-déposant :
# son S-1 entre dans la piste comme texte propre de son groupe, lu en entier (D-0033).

OWN_UNITS = config.DB_DIR / "nf_discovery_own_units.parquet"


def own_filings(cfg=None):
    cfg = cfg or config.load()
    return ((cfg.get("discovery") or {}).get("non_filer") or {}).get("own_filings") or []


def own_filer_ciks(cfg=None):
    """CIK (sans zéros) du déclarant -> groupe non déposant dont il est la tête."""
    return {str(int(f["cik"])): f["ref"] for f in own_filings(cfg)}


NOTES_SET = re.compile(
    r"^notes to (the )?(unaudited )?(condensed )?(consolidated )?(interim )?financial statements", re.I)
NOTE_TITLE = re.compile(r"^\W{0,3}(?:note\s+)?(\d{1,2})\s*[\.\-–—:]\s*[-–—]?\s*(\S.*)$", re.I)
SET_END = re.compile(
    r"^(condensed )?consolidated (balance sheets?|statements? of)|^part ii\b|^information not required in"
    r"|^\*?listed in alphabetical order|^(lead |joint )?(book-?running managers?|bookrunners)\b|^through and including\b", re.I)
PAGE_NOISE = re.compile(
    r"^F-\d+$|^notes to (the )?(unaudited )?(condensed )?(consolidated )?(interim )?financial statements(\s*\(continued\))?$"
    r"|^table of contents$", re.I)


TOC_ROW = re.compile(r"^(.+?)\s*\|\s*(?:[ivxlc]+|[A-Z]{0,2}-?\d+)$", re.I)


def toc_section(raw, title):
    """Section d'un document d'enregistrement, de son titre au titre suivant du sommaire (titres
    lus dans les lignes « Titre | page » du début du document) ; None sans entrée au sommaire."""
    from . import sections, textnorm
    lines = sections._lines(raw)
    toc = [m.group(1).strip().lower() for m in (TOC_ROW.match(t.strip()) for t, _ in lines[:600]) if m]
    tl = title.lower()
    if tl not in toc:
        return None
    others = set(toc) - {tl}
    start = next((i for i, (t, h) in enumerate(lines) if h and t.strip().lower() == tl and not TOC_ROW.match(t.strip())), None)
    if start is None:
        return None
    end = next((j for j in range(start + 1, len(lines)) if lines[j][1] and lines[j][0].strip().lower() in others), len(lines))
    return textnorm.lines_to_text([ln for ln in lines[start:end] if not PAGE_NOISE.search(ln[0].strip())])


def financial_notes_html(raw, running_headers=()):
    """Notes des états financiers d'un document d'enregistrement en HTML : un jeu s'ouvre à un titre
    « Notes to ... Financial Statements » suivi de la note 1 ; une note va de son titre « N. TITRE »
    (numérotation suivie, titre court) au titre suivant ; un jeu se ferme au titre d'un état
    financier ou à la partie II. Les pieds de page (F-n) et les titres courants sont retirés."""
    from . import sections, textnorm
    lines = sections._lines(raw)
    heads = {h.upper() for h in running_headers}
    out, cur_set, expect, cur = [], -1, None, None

    def close(end):
        if cur is not None:
            body = [ln for ln in lines[cur["start"]:end]
                    if not PAGE_NOISE.search(ln[0].strip()) and ln[0].strip().upper() not in heads]
            cur["text"] = textnorm.lines_to_text(body)
            out.append(cur)

    i = 0
    while i < len(lines):
        t = lines[i][0].strip()
        m = NOTE_TITLE.match(t) if len(t) < 120 else None
        if expect is None:
            if NOTES_SET.search(t) and len(t) < 160:
                expect = 1
                cur_set += 1
        elif m and int(m.group(1)) == expect and (m.group(2).isupper() or t.lower().startswith("note")):
            close(i)
            cur = {"set": cur_set, "number": expect, "title": m.group(2).strip(), "start": i}
            expect += 1
        elif cur is not None and SET_END.search(t) and len(t) < 160:
            close(i)
            cur, expect = None, None
            continue
        i += 1
    close(len(lines))
    return out


def _co_mentions(text, rx, lex, names, own_ref, period):
    refs = set()
    for i, a, b in D.find_mentions(text, rx, lex, lambda t: D.own_name_spans(t, names)):
        e = lex[i]
        if D.ref_valid(e, period):
            refs.add(e["ref"])
    return sorted(refs - {own_ref})


def own_filing_units(cfg=None, fetch=True):
    """Unités du document d'enregistrement de chaque tête de non-déposant (D-0054, point 13) :
    pièces EX-10 (en-tête), Item 404 et notes des états financiers du document principal, toutes lues
    comme le texte d'un groupe ; la liste des filiales (EX-21) au niveau 1. Les co-mentions du lexique
    d'ensemble sont gardées pour information."""
    from . import edgar
    cfg = cfg or config.load()
    lex = union_lexicon(cfg)
    rx, _ = D.compile_lexicon(lex)
    e = edgar.Edgar(net.SecClient(config.as_of(), cfg), config.as_of()) if fetch else None
    rows = []
    for f in own_filings(cfg):
        cik10, acc, names = str(f["cik"]).zfill(10), f["accession"], [f["filer"]]
        period = str(f["filed"]).replace("-", "")

        def raw_of(doc):
            p = cache.archive_path(cik10, acc, doc)
            return cache.read(p) if p.exists() or e is None else e.archive(cik10, acc, doc)
        docs = edgar.parse_sgml_header(raw_of(f"{acc}-index-headers.html"))["documents"]
        base = {"ref": f["ref"], "cik": str(int(f["cik"])), "filer": f["filer"], "adsh": acc, "form": f["form"],
                "date": period}
        for d in docs:
            t = d["TYPE"].upper().strip()
            if re.match(r"^EX-10(\.\d+[A-Z]?)?$", t):
                text, _ = D.plain_text(raw_of(d["FILENAME"]))
                co = _co_mentions(text, rx, lex, names, f["ref"], period)
                rows.append(dict(base, kind="exhibit_header", doc=d["FILENAME"], exhibit_type=t, section=None,
                                 chars=len(text), co_refs=";".join(co)))
            elif t.startswith("EX-21") and d["FILENAME"] == f.get("entity_list"):
                rows.append(dict(base, kind="entity_list", doc=d["FILENAME"], exhibit_type=t, section=None,
                                 chars=None, co_refs=""))
        raw = raw_of(f["primary"])
        sec = toc_section(raw, "Certain Relationships and Related Party Transactions")
        if sec:
            rows.append(dict(base, kind="item_404", doc=f["primary"] + "#item404", exhibit_type=None,
                             section="Certain Relationships and Related Party Transactions", chars=len(sec),
                             co_refs=";".join(_co_mentions(sec, rx, lex, names, f["ref"], period))))
        for n in financial_notes_html(raw, running_headers=[f["filer"].upper().replace("LTD", "LIMITED"), f["filer"].upper()]):
            rows.append(dict(base, kind="note", doc=f"{f['primary']}#s{n['set'] + 1}n{n['number']:02d}", exhibit_type=None,
                             section=f"{n['number']}. {n['title']}", note_set=n["set"], chars=len(n["text"]),
                             co_refs=";".join(_co_mentions(n["text"], rx, lex, names, f["ref"], period))))
    u = pd.DataFrame(rows)
    if u.empty:
        return u
    u["rule"] = "own_text"                    # lu en entier, comme le texte d'un groupe (D-0033)
    u.loc[u["kind"] == "entity_list", "rule"] = "N1"
    u["status"] = "queued"
    u.insert(0, "order", range(1, len(u) + 1))
    u.to_parquet(OWN_UNITS, index=False)
    print(u.groupby(["kind", "status"]).size().to_dict())
    return u


def _own_block(u, f):
    """Bloc d'une unité du document d'enregistrement : en-tête de pièce, Item 404, note ou liste des
    filiales ; les lignes vont au groupe non déposant (load.line_group)."""
    from . import blocks, sections
    cik10, acc = str(f["cik"]).zfill(10), f["accession"]
    sk = f"nfo{int(u['order']):05d}"
    common = {"signal_class": 5, "sort_key": sk, "group_id": f["ref"], "cik": cik10, "accession": acc,
              "form": f["form"], "filing_date": f["filed"], "acceptance": None, "knowledge_date": f["filed"],
              "normalizer_version": config.NORMALIZER_VERSION, "delimiter_version": config.DELIMITER_VERSION,
              "filing_status": "filed", "filer_name": f["filer"], "groups_named": [f["ref"]] + _split_refs(u["co_refs"]),
              "nf_rule": u["rule"], "own_filing": True}
    doc = u["doc"].split("#")[0]
    raw = cache.read(cache.archive_path(cik10, acc, doc))
    if u["kind"] in ("exhibit_header", "entity_list"):
        text = sections.first_page(raw) if u["kind"] == "exhibit_header" else sections.full_text(raw)
        kind = "discovery_exhibit_header" if u["kind"] == "exhibit_header" else "discovery_entity_list"
        return dict(common, content_key=blocks.content_key(text, []), block_kind=kind, period_start=None,
                    period_end=f["filed"], document=doc, locator={"file": doc, "accession": acc, "cik": cik10, "byte_range": None},
                    text=text, candidate_facts=[], chars=len(text), exhibit_type=u["exhibit_type"],
                    assurance_level="not_applicable", tier="D", mention_class="contract")
    if u["kind"] == "item_404":
        text = toc_section(raw, "Certain Relationships and Related Party Transactions")
        return dict(common, content_key=blocks.content_key(text, []), block_kind="discovery_item_404", period_start=None,
                    period_end=f["filed"], document=doc, locator={"file": doc, "accession": acc, "cik": cik10, "byte_range": None,
                                                                   "section": u["section"]},
                    text=text, candidate_facts=[], chars=len(text), note_label=u["section"],
                    assurance_level="not_applicable", tier="C", mention_class="related_party")
    sets = f.get("note_sets") or []
    notes = financial_notes_html(raw, running_headers=[f["filer"].upper().replace("LTD", "LIMITED"), f["filer"].upper()])
    n = next(x for x in notes if f"{doc}#s{x['set'] + 1}n{x['number']:02d}" == u["doc"])
    st = sets[n["set"]] if n["set"] < len(sets) else {}
    tier, assurance, _ = D.form_evidence(f["form"], "FY" if st.get("assurance") == "audited" else None)
    return dict(common, content_key=blocks.content_key(n["text"], []), block_kind="discovery_note",
                period_start=st.get("period_start"), period_end=st.get("period_end"), document=doc,
                locator={"file": doc, "accession": acc, "cik": cik10, "byte_range": None, "section": u["section"]},
                text=n["text"], candidate_facts=[], chars=len(n["text"]),
                note_label=f"{st.get('label', '')} — note {u['section']}", assurance_level=assurance, tier=tier,
                mention_class="related_party" if D.RELATED_TAG.search(n["title"].replace(" ", "")) else "note")


def prepare_own():
    """Blocs des unités retenues du document d'enregistrement, ajoutés au catalogue de la piste ;
    l'état se garde sous la clé (accession, document)."""
    fs = {f["accession"]: f for f in own_filings()}
    u = pd.read_parquet(OWN_UNITS)
    done = built_units()
    todo = [x for x in u[u["status"] == "queued"].to_dict("records") if (x["adsh"], x["doc"]) not in done]
    for x in todo:
        b = _own_block(x, fs[x["adsh"]])
        with open(CATALOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(b, ensure_ascii=False) + "\n")
        rec = {"order": int(x["order"]), "queue": None, "rank": None, "cik": x["cik"], "kind": x["kind"], "adsh": x["adsh"],
               "doc": x["doc"], "rule": x["rule"], "content_key": b["content_key"], "error": None, "own_filing": True}
        with open(BUILT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"blocs préparés : {len(todo)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "fetch":
        fetch(only=set(sys.argv[2:]) or None)
    elif cmd == "snapshot":
        snapshot()
    elif cmd == "search":
        search(new_only="new" in sys.argv[2:],
               rate=next((float(a) for a in sys.argv[2:] if a.replace(".", "", 1).isdigit()), None))
    elif cmd == "verify":
        verify()
    elif cmd == "candidates":
        build_candidates()
    elif cmd == "prepare":
        prepare(int(sys.argv[2]) if len(sys.argv) > 2 else 50)
    elif cmd == "body":
        prepare_body(sys.argv[2], sys.argv[3])
    elif cmd == "own":
        own_filing_units()
    elif cmd == "prepare_own":
        prepare_own()
    else:
        status()
