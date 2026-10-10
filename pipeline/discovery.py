"""Bloc `discovery` de §14 : qui, hors des groupes de `config.yaml`, nomme un groupe.

Le fichier `txt` des Notes Data Sets rattache chaque bloc de texte de tous les déposants à sa
note : un scan du lexique dit qui nomme un groupe, et où, sans télécharger un document. Les
archives se tirent de la plus récente à la plus ancienne ; une période non tirée devient une
exclusion, et ses paires portent `search_incomplete`. La clé de `num` inclut `dimh`, faute de
quoi un total et ses ventilations fusionneraient.

    python -m pipeline.discovery fetch            # archives de la période de lecture, scannées
    python -m pipeline.discovery status           # archives tirées, restantes, lexique

Faute de place, une archive n'est pas gardée entière : son empreinte, sa taille, sa date et
son URL vont au manifeste, et ce que le scan retient (soumissions, lignes de `txt` qui nomment
un groupe, faits de `num`, dimensions, balises, présentation et rendu des dépôts retenus) va
sous `cache/datasets/notes/{archive}/`, avec la version du lexique qui l'a filtré (§9.6).
"""
import datetime as dt
import hashlib
import io
import json
import re
import sys
import zipfile

import pandas as pd

from . import cache, config, net

AS_OF = "2026-10-07"
BASE = config.CACHE / "datasets" / "notes"
MANIFEST = BASE / "manifest.jsonl"
PAGE = ("notes", "financial-statement-notes-data-sets_2026-10-09.html.zst")
SEC = "https://www.sec.gov"

# Taxonomies dont les faits ne sont pas des notes : page de couverture (dei), informations
# sur les initiés (ecd), droits de dépôt (ffd), cybersécurité de l'Item 1C (cyd), prospectus
# et facteurs de risque des fonds (cef, oef, rr, vip), listes de référence. Une mention n'y
# fait pas un candidat (§14 : jamais dans un facteur de risque).
NOT_NOTES = ("dei/", "ecd/", "ffd/", "cyd/", "cef/", "oef/", "rr/", "vip/", "country/",
             "currency/", "exch/", "naics/", "sic/", "stpr/", "spac/", "sro/", "snj/")

LEGAL_TOKENS = {"inc", "corp", "corporation", "co", "company", "ltd", "limited", "plc", "llc",
                "lp", "llp", "sa", "ag", "nv", "se", "the", "holdings", "holding", "group"}


# -- lexique (§14, §10.2) ---------------------------------------------------------------

def lexicon(cfg=None):
    """Le lexique initial de `config.yaml` (termes, cible, règles de casse) et les entités
    confirmées des groupes : anciennes dénominations et filiales du registre, chacune avec la
    date d'entrée dans le groupe. Une entrée : terme, cible, sensible à la casse, date."""
    cfg = cfg or config.load()
    d = cfg["discovery"]["lexicon"]
    out = []
    for e in d["seed"] + d.get("confirmed", []):
        out.append({"term": e["term"], "ref": e["ref"], "case": bool(e.get("case_sensitive")),
                    "from": e.get("valid_from"), "to": e.get("valid_to")})
    return out


def lexicon_version(lex):
    blob = json.dumps(lex, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "lx-" + hashlib.sha256(blob).hexdigest()[:12]


def _term_rx(e):
    t = re.escape(e["term"])
    return t if e["case"] else f"(?i:{t})"


def compile_lexicon(lex):
    """Une expression en mots entiers, avec un groupe nommé par entrée ; le préfiltre en
    minuscules écarte d'abord, en C, les lignes sans aucun terme."""
    parts = [f"(?P<t{i}>{_term_rx(e)})" for i, e in enumerate(lex)]
    rx = re.compile(r"(?<![\w.])(?:" + "|".join(parts) + r")(?![\w])")
    low = sorted({e["term"].lower() for e in lex})
    return rx, low


def own_name_spans(text_low, names):
    """Plages du texte occupées par le nom du déposant lui-même (dénomination de `sub`,
    ancienne dénomination) : une occurrence qui en fait partie ne nomme pas un autre."""
    spans = []
    for n in names:
        if not n:
            continue
        full = re.sub(r"[^\w\- ]+", " ", n.lower())
        full = re.sub(r"\s+", " ", full).strip()
        toks = full.split()
        core = " ".join(t for t in toks if t not in LEGAL_TOKENS)
        for v in {full, core}:
            if len(v) < 3:
                continue
            for m in re.finditer(re.escape(v), text_low):
                spans.append((m.start(), m.end()))
    return spans


def find_mentions(value, rx, lex, own_spans_fn):
    """Occurrences des termes dans la valeur, hors du nom propre du déposant."""
    hits = []
    spans = None
    for m in rx.finditer(value):
        i = int(m.lastgroup[1:])
        if spans is None:
            spans = own_spans_fn(value.lower())
        if any(a < m.end() and m.start() < b for a, b in spans):
            continue
        hits.append((i, m.start(), m.end()))
    return hits


# -- archives ---------------------------------------------------------------------------

def archive_list():
    """Archives publiées sur la page des jeux de données (tirée le 2026-10-09)."""
    html = cache.read(cache.other_path(*PAGE)).decode("utf-8", "replace")
    rows = re.findall(r'<a href="(/files/dera/data/financial-statement-notes-data-sets/[^"]+\.zip)"'
                      r'[^>]*>([^<]*)</a>.*?views-field-filesize">([^<]*)<', html, re.S)
    out = []
    for u, label, size in rows:
        name = u.rsplit("/", 1)[1][:-4]
        m = re.match(r"(\d{4})(?:q(\d)|_(\d\d))", name)
        y, q, mo = int(m.group(1)), m.group(2), m.group(3)
        if q:
            start = dt.date(y, 3 * int(q) - 2, 1)
            end = (dt.date(y + (int(q) == 4), (3 * int(q)) % 12 + 1, 1) - dt.timedelta(days=1))
        else:
            start = dt.date(y, int(mo), 1)
            end = dt.date(y + (int(mo) == 12), int(mo) % 12 + 1, 1) - dt.timedelta(days=1)
        out.append({"name": name, "url": SEC + u, "label": label.strip(), "size": size.strip(),
                    "filed_from": start.isoformat(), "filed_to": end.isoformat()})
    return out


def period_start(cfg=None):
    """Début de la période de lecture la plus ancienne des groupes (fenêtre allongée et huit
    trimestres qui la précèdent, §11.1), lu dans les calendriers de la phase 0."""
    p = json.load(open(config.DB_DIR / "phase0.json", encoding="utf-8"))
    starts = [c["window"]["reading_start"] for c in p["calendars"].values() if c.get("window")]
    return min(starts)


def in_period(archives, start, as_of=AS_OF):
    return [a for a in archives if a["filed_to"] >= start and a["filed_from"] <= as_of]


def manifest():
    if not MANIFEST.exists():
        return {}
    out = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        out[r["name"]] = r
    return out


def group_ciks(cfg=None):
    """CIK des groupes, de leurs prédécesseurs et des entités du registre qui leur
    appartiennent ou appartiennent à un laboratoire : leurs dépôts ne sont pas des candidats."""
    cfg = cfg or config.load()
    ciks = {str(int(c)) for c in cfg["groups"].values()}
    for g, d in (cfg.get("predecessors") or {}).items():
        ciks |= {str(int(c)) for c in d.values()}
    for c in (cfg.get("cik_hints") or {}).values():
        ciks.add(str(int(c)))
    ent = config.TABLES / "entities.parquet"
    if ent.exists():
        import duckdb
        rows = duckdb.connect().execute(
            f"""select e.cik from '{ent}' e join '{ent}' m on m.entity_id = e.entity_id
                where e.record_kind = 'entity' and m.record_kind = 'membership' and e.cik is not null
                  and (m.ref in ({",".join("'" + g + "'" for g in cfg["groups"])}) or m.ref like 'LAB:%')""").fetchall()
        ciks |= {str(int(r[0])) for r in rows}
    return ciks


def _read_tsv(zf, name, col=None, values=None, quoting=3):
    """Lecture par morceaux, filtrée sur une colonne : `num` et `pre` d'une archive trimestrielle
    dépassent la mémoire s'ils sont lus d'un coup. `dim.tsv` met entre guillemets les segments
    qui contiennent une tabulation (identifiants de positions de BDC) : il se lit avec les
    guillemets (quoting=0), les autres fichiers sans."""
    parts = []
    with zf.open(name) as fh:
        for ch in pd.read_csv(fh, sep="\t", dtype=str, keep_default_na=False, quoting=quoting,
                              on_bad_lines="warn", encoding="utf-8", encoding_errors="replace",
                              chunksize=500_000):
            parts.append(ch if col is None else ch[ch[col].isin(values)])
    return pd.concat(parts, ignore_index=True)


def scan(zpath, lex, excluded_ciks):
    """Scan d'une archive : lignes de `txt` qui nomment un terme du lexique, hors des dépôts
    des groupes et hors des taxonomies qui ne sont pas des notes ; puis, pour les dépôts
    retenus, `num`, `dim`, `tag` (balises propres), `pre` et `ren`."""
    rx, low = compile_lexicon(lex)
    zf = zipfile.ZipFile(zpath)
    sub = _read_tsv(zf, "sub.tsv")
    sub["cik"] = sub["cik"].str.lstrip("0")
    names = {r.adsh: (r.name, r.former) for r in sub[["adsh", "name", "former"]].itertuples(index=False)}
    excl = set(sub.loc[sub["cik"].isin(excluded_ciks), "adsh"])
    stats = {"txt_rows": 0, "txt_bytes": 0, "prefilter": 0, "hit_rows": 0, "truncated_rows": 0,
             "truncated_hit_rows": 0, "excluded_group_rows": 0, "excluded_not_note_rows": 0,
             "own_name_only_rows": 0}
    keep = []
    trunc = []                      # valeurs tronquées : la partie coupée n'est pas scannée
    with zf.open("txt.tsv") as fh:
        f = io.TextIOWrapper(fh, encoding="utf-8", errors="replace", newline="\n")
        header = f.readline().rstrip("\n").split("\t")
        ix = {c: i for i, c in enumerate(header)}
        for line in f:
            stats["txt_rows"] += 1
            stats["txt_bytes"] += len(line)
            p = line.rstrip("\n").split("\t")
            if len(p) != len(header):
                continue
            v = p[ix["value"]]
            tl = p[ix["txtlen"]]
            # tronquée : moins de 90 % de la longueur d'origine (txtlen) ; de petits écarts
            # viennent de la normalisation des blancs, pas d'une coupure (annexe D)
            truncated = tl.isdigit() and int(tl) > len(v) + 64 and len(v.encode("utf-8")) < 0.9 * int(tl)
            if truncated:
                stats["truncated_rows"] += 1
                trunc.append({c: p[ix[c]] for c in ("adsh", "tag", "version", "ddate", "qtrs", "iprx",
                                                     "dimh", "txtlen", "srclen")} | {"len": len(v)})
            vl = v.lower()
            if not any(t in vl for t in low):
                continue
            stats["prefilter"] += 1
            if not rx.search(v):
                continue
            adsh = p[ix["adsh"]]
            if adsh in excl:
                stats["excluded_group_rows"] += 1
                continue
            if p[ix["version"]].startswith(NOT_NOTES):
                stats["excluded_not_note_rows"] += 1
                continue
            nm = names.get(adsh, ("", ""))
            hits = find_mentions(v, rx, lex, lambda t: own_name_spans(t, nm))
            if not hits:
                stats["own_name_only_rows"] += 1
                continue
            stats["hit_rows"] += 1
            if truncated:
                stats["truncated_hit_rows"] += 1
            rec = {c: p[i] for c, i in ix.items()}
            rec["mentions"] = json.dumps([[lex[i]["term"], lex[i]["ref"], a, b] for i, a, b in hits])
            rec["truncated"] = truncated
            keep.append(rec)
    hits = pd.DataFrame(keep, columns=header + ["mentions", "truncated"])
    adshs = set(hits["adsh"])
    out = {"sub": sub, "txt": hits,
           "truncated": pd.DataFrame(trunc, columns=["adsh", "tag", "version", "ddate", "qtrs", "iprx", "dimh",
                                                     "txtlen", "srclen", "len"])}
    num = _read_tsv(zf, "num.tsv", "adsh", adshs)
    out["num"] = num
    dimh = set(num["dimh"]) | set(hits["dimh"])
    out["dim"] = _read_tsv(zf, "dim.tsv", "dimhash", dimh, quoting=0)   # `dimhash` dans dim.tsv, `dimh` ailleurs
    out["tag"] = _read_tsv(zf, "tag.tsv", "version", adshs)  # balises propres des dépôts retenus
    out["pre"] = _read_tsv(zf, "pre.tsv", "adsh", adshs)
    out["ren"] = _read_tsv(zf, "ren.tsv", "adsh", adshs)
    stats.update({k + "_kept": len(v) for k, v in out.items()})
    stats["filers_hit"] = int(sub[sub["adsh"].isin(adshs)]["cik"].nunique())
    return out, stats


def _scan_job(name, zpath, lex, excluded, meta):
    """Scan d'une archive téléchargée, dans un processus à part ; écrit les extraits et rend la
    ligne du manifeste (le manifeste n'est écrit que par le processus principal)."""
    h = hashlib.sha256()
    with open(zpath, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    out, stats = scan(zpath, lex, excluded)
    d = BASE / name
    d.mkdir(parents=True, exist_ok=True)
    for k, df in out.items():
        df.to_parquet(d / f"{k}.parquet", index=False, compression="zstd")
    rec = dict(meta, status="scanned", sha256=h.hexdigest(), bytes=zpath.stat().st_size, stats=stats)
    return rec


def fetch(only=None, keep_zip=False, workers=3):
    """Téléchargement séquentiel par le client unique (§9.5), de la plus récente archive à la
    plus ancienne ; le scan de chaque archive se fait en parallèle, sans requête réseau."""
    from concurrent.futures import ProcessPoolExecutor, FIRST_COMPLETED, wait
    cfg = config.load()
    lex = lexicon(cfg)
    lv = lexicon_version(lex)
    start = period_start(cfg)
    todo = in_period(archive_list(), start)
    done = manifest()
    client = net.SecClient(AS_OF, cfg)
    excluded = group_ciks(cfg)
    tmpdir = BASE / "tmp"
    tmpdir.mkdir(parents=True, exist_ok=True)
    pending = {}

    def drain(block):
        if not pending:
            return
        fin, _ = wait(list(pending), return_when=FIRST_COMPLETED) if block else (
            [f for f in pending if f.done()], None)
        for f in fin:
            name, zpath = pending.pop(f)
            rec = f.result()
            with open(MANIFEST, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if not keep_zip:
                zpath.unlink()
            print(name, json.dumps(rec["stats"]), flush=True)

    with ProcessPoolExecutor(max_workers=workers) as ex:
        for a in todo:                   # la page liste de la plus récente à la plus ancienne
            if only and a["name"] not in only:
                continue
            if a["name"] in done and done[a["name"]].get("lexicon_version") == lv:
                continue
            while len(pending) >= workers:
                drain(True)
            zpath = tmpdir / (a["name"] + ".zip")
            t0 = dt.datetime.now(dt.timezone.utc)
            try:
                _, headers = client.get(a["url"], timeout=900, dest=zpath)
            except net.NotCollected as exc:
                rec = {"name": a["name"], "url": a["url"], "status": "not_collected",
                       "reason": str(exc), "lexicon_version": lv, "retrieved": t0.isoformat(timespec="seconds")}
                with open(MANIFEST, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(a["name"], "not_collected", exc, flush=True)
                continue
            meta = {"name": a["name"], "url": a["url"], "last_modified": headers.get("Last-Modified"),
                    "filed_from": a["filed_from"], "filed_to": a["filed_to"],
                    "retrieved": t0.isoformat(timespec="seconds"), "lexicon_version": lv,
                    "kept_zip": keep_zip}
            pending[ex.submit(_scan_job, a["name"], zpath, lex, excluded, meta)] = (a["name"], zpath)
            drain(False)
        while pending:
            drain(True)


def status():
    cfg = config.load()
    lex = lexicon(cfg)
    lv = lexicon_version(lex)
    todo = in_period(archive_list(), period_start(cfg))
    done = manifest()
    ok = [a["name"] for a in todo if done.get(a["name"], {}).get("lexicon_version") == lv
          and done[a["name"]]["status"] == "scanned"]
    print(f"lexique {lv} ({len(lex)} termes) ; période depuis {period_start(cfg)} ; "
          f"archives {len(ok)}/{len(todo)} scannées")
    print("restantes :", [a["name"] for a in todo if a["name"] not in ok])



# -- recherche plein texte : EX-10 et Form D que les archives ne couvrent pas (§14) ----------

EFTS = "https://efts.sec.gov/LATEST/search-index"
# formulaires racines qui portent des EX-10 déposés (filed) ; un 6-K est furnished (§2.1) :
# ses pièces ne sont pas cherchées
EX10_FORMS = ["8-K", "10-K", "10-Q", "S-1", "S-4", "S-11", "F-1", "F-4", "10-12B", "10-12G",
              "20-F", "40-F"]
SEARCH_DIR = config.CACHE / "search"
QUERY_LOG = config.WORK / "discovery" / "efts_queries.jsonl"
START = "2017-01-01"


def _efts(client, params):
    """Une page de résultats : réponse gardée sous cache/search/{sha256 de la requête}/{date}
    (§9.6), et la requête consignée pour être reproductible."""
    import urllib.parse
    url = EFTS + "?" + urllib.parse.urlencode(params)
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    d = SEARCH_DIR / key
    hit = sorted(d.glob("*.json.zst")) if d.exists() else []
    if hit:
        return json.loads(cache.read(hit[-1])), url, True
    body, _ = client.get(url)
    cache.write(d / f"{dt.date.today().isoformat()}.json.zst", body)
    return json.loads(body), url, False


def _log_query(rec):
    QUERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(QUERY_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _split(a, b):
    da, db = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    mid = da + (db - da) // 2
    return (a, mid.isoformat()), ((mid + dt.timedelta(days=1)).isoformat(), b)


def harvest(client, term, forms, start=START, end=AS_OF, keep=lambda s: True):
    """Toutes les pages d'une requête ; une requête saturée (10 000 résultats) se resserre
    sur deux périodes plus courtes, jusqu'à passer sous le plafond."""
    out = []
    stack = [(start, end)]
    while stack:
        a, b = stack.pop()
        params = {"q": f'"{term}"', "dateRange": "custom", "startdt": a, "enddt": b,
                  "forms": ",".join(forms)}
        data, url, cached = _efts(client, dict(params, **{"from": 0}))
        tot = data["hits"]["total"]
        if tot.get("relation") == "gte" or tot["value"] >= 10000:
            if a == b:
                _log_query({"term": term, "forms": forms, "start": a, "end": b, "total": tot,
                            "status": "saturated_single_day"})
            else:
                stack.extend(_split(a, b))
                continue
        n = tot["value"]
        # pages suivantes sur quatre fils : le client garde son limiteur et son journal (§9.5)
        from concurrent.futures import ThreadPoolExecutor
        offs = list(range(100, min(n, 10000), 100))
        with ThreadPoolExecutor(max_workers=4) as tp:
            rest = list(tp.map(lambda f: _efts(client, dict(params, **{"from": f}))[0], offs))
        pages = 1 + len(offs)
        for page in [data] + rest:
            for h in page["hits"]["hits"]:
                s = h["_source"]
                if keep(s):
                    out.append({"term": term, "id": h["_id"], "adsh": s.get("adsh") or h["_id"].split(":")[0],
                                "file": h["_id"].split(":", 1)[1] if ":" in h["_id"] else None,
                                "file_type": s.get("file_type"), "form": s.get("form"),
                                "root_forms": s.get("root_forms"), "file_date": s.get("file_date"),
                                "period_ending": s.get("period_ending"), "ciks": s.get("ciks"),
                                "display_names": s.get("display_names"), "items": s.get("items")})
        _log_query({"term": term, "forms": forms, "start": a, "end": b, "total": n, "pages": pages,
                    "url": EFTS + "?q=" + params["q"], "status": "complete"})
    return out


def search(rate=None):
    """EX-10 et Form D qui nomment un terme du lexique, du 2017-01-01 à as_of."""
    cfg = config.load()
    client = net.SecClient(AS_OF, cfg)
    if rate:
        client.min_interval = 1.0 / rate
    lex = lexicon(cfg)
    rows = []
    for e in lex:
        rows += harvest(client, e["term"], EX10_FORMS,
                        keep=lambda s: str(s.get("file_type") or "").upper().startswith("EX-10"))
        rows += harvest(client, e["term"], ["D"], keep=lambda s: True)
        print(e["term"], len(rows), client.stats["requests"], flush=True)
    df = pd.DataFrame(rows)
    out = config.WORK / "discovery"
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.DB_DIR / "discovery_efts.parquet", index=False)
    print("hits", len(df), "requêtes", client.stats["requests"])


# -- mentions, montants documentés, candidats (§14) ---------------------------------------

CLASS_ORDER = {"contract": 0, "related_party": 1, "note": 2, "form_d": 3}
RELATED_TAG = re.compile(r"RelatedPart", re.I)
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def camel_spaced(s):
    """« GoogleLLC » -> « Google LLC », « Amazon.comInc. » -> « Amazon.com Inc. » : un nom de
    membre de dimension se compare au lexique mot par mot."""
    return _CAMEL.sub(" ", s)


def ref_valid(e, period):
    """Une entrée datée du lexique (ancienne dénomination, filiale entrée à une date) ne
    nomme le groupe que si la période du dépôt recoupe sa validité."""
    if not period:
        return True
    end = dt.date(int(period[:4]), int(period[4:6]), int(period[6:8]))
    start = end - dt.timedelta(days=365)
    if e.get("from") and end < dt.date.fromisoformat(e["from"]):
        return False
    if e.get("to") and start > dt.date.fromisoformat(e["to"]):
        return False
    return True


def scanned_archives(lv=None):
    lv = lv or lexicon_version(lexicon())
    m = manifest()
    return [n for n, r in m.items() if r.get("status") == "scanned" and r.get("lexicon_version") == lv]


SUB_COLS = ["adsh", "cik", "name", "former", "sic", "countryba", "countryinc", "form", "period",
            "fy", "fp", "filed", "accepted", "afs", "fye", "instance", "prevrpt"]


def note_mentions():
    """Une ligne par (ligne de txt retenue, groupe nommé à la date du dépôt)."""
    lex = lexicon()
    by_term = {(e["term"], e["ref"]): e for e in lex}
    rows = []
    for name in scanned_archives():
        d = BASE / name
        txt = pd.read_parquet(d / "txt.parquet")
        if txt.empty:
            continue
        sub = pd.read_parquet(d / "sub.parquet", columns=SUB_COLS)
        txt = txt.merge(sub, on="adsh", how="left")
        for r in txt.itertuples(index=False):
            ms = json.loads(r.mentions)
            groups, terms = set(), set()
            for term, ref, a, b in ms:
                e = by_term.get((term, ref))
                if e is None or not ref_valid(e, r.period):
                    continue
                groups.add(ref)
                terms.add(term)
            if not groups:
                continue
            cls = "related_party" if RELATED_TAG.search(r.tag) else "note"
            for g in sorted(groups):
                rows.append({"archive": name, "adsh": r.adsh, "cik": r.cik, "filer": r.name, "form": r.form,
                             "filed": r.filed, "period": r.period, "fy": r.fy, "fp": r.fp,
                             "tag": r.tag, "version": r.version, "ddate": r.ddate, "qtrs": r.qtrs,
                             "dimh": r.dimh, "iprx": r.iprx, "context": r.context,
                             "value_sha": hashlib.sha256(r.value.encode("utf-8")).hexdigest()[:16],
                             "chars": len(r.value), "truncated": bool(r.truncated), "class": cls,
                             "group": g, "terms": ";".join(sorted(terms)), "source": "notes"})
    return pd.DataFrame(rows)


def documented_amounts(adshs):
    """Montant documenté par (dépôt, groupe), tiré de `num` (§14) : le plus grand montant en
    USD d'un fait dont un membre de dimension nomme le groupe, hors du nom propre du déposant.
    Jamais d'une observation ; sans tel fait, pas de montant."""
    lex = lexicon()
    rx, low = compile_lexicon(lex)
    out = {}
    for name in scanned_archives():
        d = BASE / name
        num = pd.read_parquet(d / "num.parquet", columns=["adsh", "tag", "ddate", "qtrs", "uom", "dimh", "value"])
        num = num[(num["adsh"].isin(adshs)) & (num["uom"] == "USD") & (num["dimh"] != "0x00000000")]
        if num.empty:
            continue
        dim = pd.read_parquet(d / "dim.parquet")
        sub = pd.read_parquet(d / "sub.parquet", columns=["adsh", "name", "former", "period"])
        names = {r.adsh: (r.name, r.former, r.period) for r in sub.itertuples(index=False)}
        seg_hits = {}
        for r in dim.itertuples(index=False):
            segs = r.segments or ""
            refs = set()
            for part in segs.split(";"):
                if "=" not in part:
                    continue
                mem = part.split("=", 1)[1]
                for text in {mem, camel_spaced(mem)}:
                    for m in rx.finditer(text):
                        e = lex[int(m.lastgroup[1:])]
                        refs.add((e["term"], e["ref"], text[m.start():m.end()], text))
            if refs:
                seg_hits[r.dimhash] = refs
        num = num[num["dimh"].isin(seg_hits)]
        for r in num.itertuples(index=False):
            nm = names.get(r.adsh, ("", "", None))
            for term, ref, hit, text in seg_hits[r.dimh]:
                e = next(x for x in lex if x["term"] == term and x["ref"] == ref)
                if not ref_valid(e, nm[2]):
                    continue
                spans = own_name_spans(text.lower(), nm[:2])
                i = text.find(hit)
                if any(a < i + len(hit) and i < b for a, b in spans):
                    continue
                try:
                    v = abs(float(r.value))
                except (TypeError, ValueError):
                    continue
                k = (r.adsh, ref)
                if v > out.get(k, (-1,))[0]:
                    out[k] = (v, r.tag, r.ddate, r.qtrs, r.dimh)
    return out


# -- blocs à lire : la page R de chaque note qui nomme un groupe (§14, §7.4) -----------------

DISC_CATALOG = config.DB_DIR / "discovery_blocks.jsonl"
ANNUAL = {"10-K", "10-K/A", "10-KT", "10-KT/A", "20-F", "20-F/A", "40-F", "40-F/A"}
INTERIM = {"10-Q", "10-Q/A", "10-QT", "10-QT/A"}


def form_evidence(form, fp):
    """Niveau de preuve d'une note selon son formulaire (§2.2, annexe A) : états annuels
    audités (A), intermédiaires revus (B), autres notes déposées (C), 6-K furnished (E)."""
    if form in ANNUAL:
        return "A", "audited", "filed"
    if form in INTERIM:
        return "B", "reviewed", "filed"
    if form.startswith("6-K"):
        return "E", "not_applicable", "furnished"
    if form.split("/")[0] in ("S-1", "F-1", "S-4", "F-4", "S-11", "10-12B", "10-12G") and fp == "FY":
        return "A", "audited", "filed"
    return "C", "not_applicable", "filed"


def _date(ymd):
    return dt.date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8]))


def fact_dates(ddate, qtrs, datp, durp):
    """Dates d'un fait de num : `ddate` est la fin de mois la plus proche ; dans les archives,
    `datp` est l'écart en jours (de -15 à 15) et la date réelle vaut ddate - datp (accord du
    7 septembre 2025 : ddate 20250831, datp -7) ; `durp` est l'écart de durée en fraction
    d'année (1/365 = un jour) par rapport à qtrs trimestres de 365/4 jours."""
    end = _date(ddate)
    try:
        end = end - dt.timedelta(days=int(round(float(datp or 0))))
    except (TypeError, ValueError):
        pass
    q = int(qtrs or 0)
    if q == 0:
        return None, end
    try:
        dur = int(round(q * 365 / 4 + float(durp or 0) * 365))
    except (TypeError, ValueError):
        dur = int(round(q * 365 / 4))
    return end - dt.timedelta(days=dur - 1), end


def candidate_facts(text, num, dims):
    """Faits de num du dépôt dont la valeur paraît dans le texte de la note (D-0017), avec
    leurs membres de dimension ; clé : archive, accession, balise, version, dates, unité,
    dimh, iprx (la clé de num inclut dimh, §14)."""
    from .reader import text_values
    from decimal import Decimal, InvalidOperation
    vals = text_values(text)
    out = []
    for r in num.itertuples(index=False):
        try:
            v = Decimal(str(r.value))
        except (InvalidOperation, TypeError):
            continue
        if v not in vals and -v not in vals:
            continue
        ps, pe = fact_dates(r.ddate, r.qtrs, r.datp, r.durp)
        segs = dims.get(r.dimh, "") if r.dimh != "0x00000000" else ""
        dl = [[p.split("=", 1)[0], p.split("=", 1)[1], None] for p in segs.split(";") if "=" in p]
        prefix = r.version.split("/")[0] if "/" in r.version else "custom"
        out.append({"fact_key": f"nds/{r.adsh}/{r.tag}/{r.version}/{r.ddate}/{r.qtrs}/{r.uom}/{r.dimh}/{r.iprx}",
                    "concept": f"{prefix}:{r.tag}", "value": str(v), "unit": r.uom,
                    "period_start": str(ps or ""), "period_end": str(pe),
                    "dims": json.dumps(dl) if dl else "[]",
                    "decimals": None if str(r.dcml) == "32767" else r.dcml})
    out.sort(key=lambda c: c["fact_key"])
    return out


def r_page_text(raw):
    """Texte d'une page R : le titre de la note, puis le contenu de chaque cellule de texte
    (`td class="text"`) linéarisé comme un fragment, paragraphes et tableaux gardés ; sans
    cela, toute la note tiendrait sur une seule ligne de tableau, impossible à découper (§7.4)."""
    from . import textnorm
    root = textnorm.parse_html(raw)
    tds = root.xpath('//td[@class="text"]')
    if not tds:
        return textnorm.lines_to_text(textnorm.linearize(root))
    lin = textnorm.Linearizer()
    for th in root.xpath('//th[contains(concat(" ", normalize-space(@class), " "), " tl ")]')[:1]:
        lin.add(th.text_content(), True)
        lin.flush()
    for td in tds:
        lin.walk_cell(td)
    return textnorm.lines_to_text(lin.lines)


def note_family(ren_f, report, shortname):
    """Pages de la note : elle-même, ses tableaux et ses détails, rattachés par le rendu
    (`parentreport`, `ultparentrpt`) ou, à défaut, par le préfixe de leur nom court."""
    out = {str(report)}
    sn = (shortname or "").strip().lower()
    for r in ren_f.itertuples(index=False):
        if str(r.ultparentrpt) == str(report) or str(r.parentreport) == str(report):
            out.add(str(r.report))
        elif r.menucat in ("T", "D") and sn and str(r.shortname).strip().lower().startswith(sn):
            out.add(str(r.report))
    return out


def note_block(client, m, sub_row, report, shortname, num, dims, sort_key):
    """Bloc d'une note : page R du dépôt, en cache comme toute pièce d'archive, linéarisée par
    le normaliseur des autres blocs ; faits candidats tirés de num."""
    from . import blocks, textnorm
    cik10 = str(sub_row["cik"]).zfill(10)
    acc = m["adsh"]
    doc = f"R{report}.htm"
    path = cache.archive_path(cik10, acc, doc)
    if path.exists():
        raw = cache.read(path)
    else:
        url = f"{SEC}/Archives/edgar/data/{int(sub_row['cik'])}/{acc.replace('-', '')}/{doc}"
        raw, _ = client.get(url)
        cache.write(path, raw)
    text = r_page_text(raw)
    cands = candidate_facts(text, num, dims)
    tier, assurance, status = form_evidence(sub_row["form"], sub_row.get("fp"))
    period = sub_row.get("period")
    pe = f"{period[:4]}-{period[4:6]}-{period[6:8]}" if period else None
    filed = sub_row["filed"]
    filed = f"{filed[:4]}-{filed[4:6]}-{filed[6:8]}"
    ck = blocks.content_key(text, cands)
    return {"content_key": ck, "block_kind": "discovery_note", "signal_class": 5, "sort_key": sort_key,
            "group_id": "CP:" + __import__("pipeline.graph", fromlist=["x"]).normalize_name(sub_row["name"]),
            "cik": cik10, "accession": acc, "form": sub_row["form"], "filing_date": filed,
            "acceptance": sub_row.get("accepted"), "knowledge_date": filed, "period_start": None,
            "period_end": pe, "document": doc,
            "locator": {"file": doc, "accession": acc, "cik": cik10, "byte_range": None},
            "text": text, "candidate_facts": cands, "chars": len(text),
            "normalizer_version": config.NORMALIZER_VERSION, "delimiter_version": config.DELIMITER_VERSION,
            "note_label": shortname, "filing_status": status, "assurance_level": assurance, "tier": tier,
            "filer_name": sub_row["name"], "mention_class": m["class"], "groups_named": m["groups"],
            "terms": m["terms"], "txt_tag": m["tag"]}


# -- vérification des résultats de la recherche plein texte ----------------------------------
# La recherche ne voit ni la casse ni le nom propre du déposant, et ne rend que des
# métadonnées : chaque pièce retenue se tire (une requête) et le code y applique les règles du
# lexique avant d'en faire une mention.

_NAME_RX = re.compile(r"^(.*?)\s+(?:\([^)]*\)\s+)?\(CIK (\d{10})\)\s*$")


def _display(names):
    out = []
    for n in (list(names) if names is not None else []):
        m = _NAME_RX.match(n.strip())
        if m:
            out.append((m.group(1).strip(), m.group(2)))
    return out


def efts_hits():
    p = config.DB_DIR / "discovery_efts.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


def _valid_terms_only(h, lex):
    """Une pièce ne se tire que si l'un des termes qui l'ont trouvée peut nommer un groupe à sa
    date (entrées datées du lexique) ; une ligne par pièce."""
    by_term = {}
    for e in lex:
        by_term.setdefault(e["term"], []).append(e)
    ok = set()
    for r in h.itertuples(index=False):
        period = (r.file_date or "").replace("-", "")
        if any(ref_valid(e, period) for e in by_term.get(r.term, [])):
            ok.add(r.id)
    return h[h["id"].isin(ok)].drop_duplicates("id")


def verify_exhibits(rate=4.0):
    """EX-10 de déposants hors des groupes : pièce tirée, texte normalisé, termes du lexique
    en mots entiers, hors du nom du déposant ; un terme daté ne nomme le groupe qu'à sa date."""
    from . import sections
    cfg = config.load()
    lex = lexicon(cfg)
    rx, low = compile_lexicon(lex)
    excluded = group_ciks(cfg)
    client = net.SecClient(AS_OF, cfg)
    client.min_interval = 1.0 / rate
    h = efts_hits()
    h = h[h["file_type"].fillna("").str.upper().str.startswith("EX-10")]
    h = _valid_terms_only(h, lex)
    rows = []
    from concurrent.futures import ThreadPoolExecutor

    def one(r):
        names = _display(r["display_names"])
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
                url = f"{SEC}/Archives/edgar/data/{int(cik10)}/{acc.replace('-', '')}/{r['file']}"
                raw, _ = client.get(url)
                cache.write(path, raw)
        except net.NotCollected as exc:
            return {"id": r["id"], "status": "not_collected", "reason": str(exc)}
        text, how = plain_text(raw)
        period = (r["file_date"] or "").replace("-", "")
        hits = find_mentions(text, rx, lex, lambda t: own_name_spans(t, [n for n, _ in names]))
        refs, terms, first = set(), set(), None
        for i, a, b in hits:
            e = lex[i]
            if not ref_valid(e, period):
                continue
            refs.add(e["ref"])
            terms.add(e["term"])
            first = a if first is None else min(first, a)
        return {"id": r["id"], "status": "verified" if refs else "no_mention", "cik": str(int(cik10)),
                "filer": name, "adsh": acc, "file": r["file"], "file_type": r["file_type"], "form": r["form"],
                "file_date": r["file_date"], "groups": sorted(refs), "terms": ";".join(sorted(terms)),
                "chars": len(text), "first_mention_char": first, "text_method": how}

    def safe(r):
        try:
            return one(r)
        except Exception as exc:                 # une pièce illisible ne coupe pas la vérification
            return {"id": r["id"], "status": "parse_failed", "reason": f"{type(exc).__name__}: {exc}"[:300]}

    with ThreadPoolExecutor(max_workers=8) as tp:
        for out in tp.map(safe, [r for _, r in h.iterrows()]):
            if out:
                rows.append(out)
    df = pd.DataFrame(rows)
    df.to_parquet(config.DB_DIR / "discovery_ex10.parquet", index=False)
    print(df["status"].value_counts().to_dict() if len(df) else {}, client.stats["requests"])
    return df


def plain_text(raw):
    """Texte d'une pièce par le normaliseur ; un HTML trop imbriqué pour le linéariseur (profondeur
    de récursion) se lit en retirant les balises, ce qui suffit à y chercher un terme."""
    from . import sections, textnorm
    try:
        return sections.full_text(raw), "linearized"
    except RecursionError:
        t = textnorm.decode(raw)
        t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
        t = re.sub(r"<[^>]+>", " ", t)
        import html as _html
        return re.sub(r"\s+", " ", _html.unescape(t)), "tags_stripped"


def _xml_text(raw):
    t = textnorm_decode(raw)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def textnorm_decode(raw):
    from . import textnorm
    return textnorm.decode(raw)


def verify_form_d(rate=4.0):
    """Form D : XML tiré, termes du lexique dans tout le document, nom de l'émetteur compris
    (un véhicule nommé d'après un laboratoire est la mention que §14 décrit) ; montant vendu
    de l'offre (`totalAmountSold`), cumulé depuis la première vente, en USD."""
    cfg = config.load()
    lex = lexicon(cfg)
    rx, low = compile_lexicon(lex)
    excluded = group_ciks(cfg)
    client = net.SecClient(AS_OF, cfg)
    client.min_interval = 1.0 / rate
    h = efts_hits()
    h = h[h["root_forms"].map(lambda x: "D" in list(x) if x is not None else False)]
    h = _valid_terms_only(h, lex)
    rows = []
    from concurrent.futures import ThreadPoolExecutor

    def one(r):
        names = _display(r["display_names"])
        filers = [(n, c) for n, c in names if str(int(c)) not in excluded]
        if not filers:
            return None
        name, cik10 = filers[0]
        acc = r["adsh"]
        fname = r["file"] or "primary_doc.xml"
        path = cache.archive_path(cik10, acc, fname)
        try:
            if path.exists():
                raw = cache.read(path)
            else:
                url = f"{SEC}/Archives/edgar/data/{int(cik10)}/{acc.replace('-', '')}/{fname}"
                raw, _ = client.get(url)
                cache.write(path, raw)
        except net.NotCollected as exc:
            return {"id": r["id"], "status": "not_collected", "reason": str(exc)}
        xml = textnorm_decode(raw)
        text = _xml_text(raw)
        period = (r["file_date"] or "").replace("-", "")
        refs, terms = set(), set()
        for m in rx.finditer(text):
            e = lex[int(m.lastgroup[1:])]
            if ref_valid(e, period):
                refs.add(e["ref"])
                terms.add(e["term"])

        def tag(t):
            m = re.search(rf"<{t}>\s*([^<]*?)\s*</{t}>", xml)
            return m.group(1) if m else None
        sold = tag("totalAmountSold")
        first_sale = tag("dateOfFirstSale") or tag("value")
        return {"id": r["id"], "status": "verified" if refs else "no_mention", "cik": str(int(cik10)),
                "filer": name, "adsh": acc, "file": fname, "form": r["form"], "file_date": r["file_date"],
                "groups": sorted(refs), "terms": ";".join(sorted(terms)),
                "issuer_name": tag("entityName"), "total_amount_sold": sold,
                "total_offering_amount": tag("totalOfferingAmount"), "first_sale": first_sale,
                "is_amendment": tag("isAmendment"), "industry": tag("industryGroupType")}

    def safe(r):
        try:
            return one(r)
        except Exception as exc:                 # une pièce illisible ne coupe pas la vérification
            return {"id": r["id"], "status": "parse_failed", "reason": f"{type(exc).__name__}: {exc}"[:300]}

    with ThreadPoolExecutor(max_workers=8) as tp:
        for out in tp.map(safe, [r for _, r in h.iterrows()]):
            if out:
                rows.append(out)
    df = pd.DataFrame(rows)
    df.to_parquet(config.DB_DIR / "discovery_formd.parquet", index=False)
    print(df["status"].value_counts().to_dict() if len(df) else {}, client.stats["requests"])
    return df


# -- candidats classés et file de lecture (D-0036) -------------------------------------------

CANDIDATES = config.DB_DIR / "discovery_candidates.parquet"
UNITS = config.DB_DIR / "discovery_units.parquet"


def _num_amount(x):
    try:
        v = float(str(x).replace(",", ""))
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def all_mentions():
    """Mentions des trois sources : notes (txt), EX-10 vérifiés, Form D vérifiés ; une ligne
    par (document, groupe)."""
    nm = note_mentions()
    amts = documented_amounts(set(nm["adsh"])) if len(nm) else {}
    rows = []
    for r in nm.to_dict("records"):
        a = amts.get((r["adsh"], r["group"]))
        rows.append({"cik": str(r["cik"]), "filer": r["filer"], "class": r["class"], "group": r["group"],
                     "adsh": r["adsh"], "doc": r["tag"], "form": r["form"], "date": r["filed"], "period": r["period"],
                     "amount": a[0] if a else None, "amount_basis": (f"num:{a[1]}:{a[2]}:{a[3]}:{a[4]}" if a else None),
                     "archive": r["archive"], "value_sha": r["value_sha"], "chars": r["chars"], "terms": r["terms"],
                     "truncated": r["truncated"]})
    p = config.DB_DIR / "discovery_ex10.parquet"
    if p.exists():
        ex = pd.read_parquet(p)
        ex = ex[ex["status"] == "verified"]
        for r in ex.itertuples(index=False):
            for g in r.groups:
                rows.append({"cik": r.cik, "filer": r.filer, "class": "contract", "group": g, "adsh": r.adsh,
                             "doc": r.file, "form": r.form, "date": (r.file_date or "").replace("-", ""),
                             "period": None, "amount": None, "amount_basis": None, "archive": None,
                             "value_sha": None, "chars": r.chars, "terms": r.terms, "truncated": False})
    p = config.DB_DIR / "discovery_formd.parquet"
    if p.exists():
        fd = pd.read_parquet(p)
        fd = fd[fd["status"] == "verified"]
        for r in fd.itertuples(index=False):
            amt = _num_amount(r.total_amount_sold)
            for g in r.groups:
                rows.append({"cik": r.cik, "filer": r.filer, "class": "form_d", "group": g, "adsh": r.adsh,
                             "doc": r.file, "form": r.form, "date": (r.file_date or "").replace("-", ""),
                             "period": None, "amount": amt,
                             "amount_basis": "form_d:totalAmountSold" if amt is not None else None,
                             "archive": None, "value_sha": None, "chars": 0, "terms": r.terms, "truncated": False})
    return pd.DataFrame(rows)


def rank_candidates(m):
    """Classement fixé d'avance (§14, D-0036) : classe de mention, montant documenté
    décroissant (sans montant ensuite), nombre de groupes nommés, accession."""
    out = []
    for cik, g in m.groupby("cik"):
        best = min(CLASS_ORDER[c] for c in g["class"])
        best_rows = g[g["class"].map(CLASS_ORDER) == best]
        amts = [a for a in g["amount"] if a is not None and a == a]
        out.append({"cik": cik, "filer": g.sort_values("date")["filer"].iloc[-1],
                    "best_class": [k for k, v in CLASS_ORDER.items() if v == best][0],
                    "documented_amount": max(amts) if amts else None,
                    "n_groups": g["group"].nunique(), "groups": ";".join(sorted(g["group"].unique())),
                    "first_accession": min(best_rows["adsh"]),
                    "n_mentions": len(g), "n_documents": g[["adsh", "doc"]].drop_duplicates().shape[0],
                    "classes": ";".join(sorted(g["class"].unique(), key=CLASS_ORDER.get))})
    c = pd.DataFrame(out)
    c["_cls"] = c["best_class"].map(CLASS_ORDER)
    c["_noamt"] = c["documented_amount"].isna()
    c["_amt"] = -c["documented_amount"].fillna(0)
    c = c.sort_values(["_cls", "_noamt", "_amt", "n_groups", "first_accession"],
                      ascending=[True, True, True, False, True]).drop(columns=["_cls", "_noamt", "_amt"])
    c.insert(0, "rank", range(1, len(c) + 1))
    return c.reset_index(drop=True)


def reading_units(m, c):
    """Unités de lecture dans l'ordre de la file (D-0036, point 8) : (A) en-têtes d'EX-10 et
    notes du dépôt le plus récent de chaque candidat, dans l'ordre du classement ; (B) ses autres
    notes, du plus récent au plus ancien ; un texte identique n'est qu'une unité."""
    rank = dict(zip(c["cik"], c["rank"]))
    units, seen = [], set()
    notes = m[m["class"].isin(["related_party", "note"])]
    exs = m[m["class"] == "contract"]
    for cik in c["cik"]:
        r = rank[cik]
        for x in exs[exs["cik"] == cik].drop_duplicates(["adsh", "doc"]).sort_values("date", ascending=False).itertuples(index=False):
            units.append({"pass": "A", "rank": r, "cik": cik, "kind": "exhibit_header", "adsh": x.adsh,
                          "doc": x.doc, "date": x.date, "archive": None, "value_sha": None,
                          "groups": ";".join(sorted(exs[(exs["adsh"] == x.adsh) & (exs["doc"] == x.doc)]["group"]))})
        n = notes[notes["cik"] == cik]
        if n.empty:
            continue
        docs = n.drop_duplicates(["adsh", "doc"]).sort_values(["date", "adsh"], ascending=[False, False])
        latest = docs["adsh"].iloc[0]
        for x in docs.itertuples(index=False):
            if x.value_sha in seen:
                continue
            seen.add(x.value_sha)
            units.append({"pass": "A" if x.adsh == latest else "B", "rank": r, "cik": cik, "kind": "note",
                          "adsh": x.adsh, "doc": x.doc, "date": x.date, "archive": x.archive,
                          "value_sha": x.value_sha,
                          "groups": ";".join(sorted(n[(n["adsh"] == x.adsh) & (n["doc"] == x.doc)]["group"]))})
    u = pd.DataFrame(units)
    u["_p"] = u["pass"].map({"A": 0, "B": 1, "C": 2})
    u = u.sort_values(["_p", "rank", "date", "adsh", "doc"], ascending=[True, True, False, False, True],
                      kind="mergesort").drop(columns=["_p"])
    u.insert(0, "order", range(1, len(u) + 1))
    return u.reset_index(drop=True)


def build_candidates():
    m = all_mentions()
    c = rank_candidates(m)
    u = reading_units(m, c)
    m.to_parquet(config.DB_DIR / "discovery_mentions.parquet", index=False)
    c.to_parquet(CANDIDATES, index=False)
    u.to_parquet(UNITS, index=False)
    print("mentions", len(m), "candidats", len(c), "unités", len(u))
    print(c.groupby("best_class").size().to_dict())
    print(u.groupby(["pass", "kind"]).size().to_dict())
    return m, c, u


# -- préparation des blocs par tranches, dans l'ordre de la file ------------------------------

BUILT = config.DB_DIR / "discovery_built.jsonl"


def built_units():
    if not BUILT.exists():
        return {}
    out = {}
    for l in BUILT.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        out[r["order"]] = r
    return out


class _Archive:
    """Extraits d'une archive, chargés une fois."""
    _cache = {}

    @classmethod
    def get(cls, name):
        if name not in cls._cache:
            if len(cls._cache) > 3:
                cls._cache.pop(next(iter(cls._cache)))
            d = BASE / name
            sub = pd.read_parquet(d / "sub.parquet")
            ren = pd.read_parquet(d / "ren.parquet")
            pre = pd.read_parquet(d / "pre.parquet", columns=["adsh", "report", "tag", "version"])
            num = pd.read_parquet(d / "num.parquet")
            dim = pd.read_parquet(d / "dim.parquet")
            cls._cache[name] = {"sub": sub.set_index("adsh"), "ren": ren, "pre": pre, "num": num,
                                "dims": dict(zip(dim["dimhash"], dim["segments"]))}
        return cls._cache[name]


def _exhibit_block(u, client):
    from . import blocks, sections
    from .graph import normalize_name
    ex = pd.read_parquet(config.DB_DIR / "discovery_ex10.parquet")
    r = ex[(ex["adsh"] == u["adsh"]) & (ex["file"] == u["doc"])].iloc[0]
    cik10 = str(r["cik"]).zfill(10)
    raw = cache.read(cache.archive_path(cik10, r["adsh"], r["file"]))
    head = sections.first_page(raw)
    ck = blocks.content_key(head, [])
    fd = r["file_date"]
    return {"content_key": ck, "block_kind": "discovery_exhibit_header", "signal_class": 5,
            "sort_key": f"{u['order']:07d}", "group_id": "CP:" + normalize_name(r["filer"]), "cik": cik10,
            "accession": r["adsh"], "form": r["form"], "filing_date": fd, "acceptance": None,
            "knowledge_date": fd, "period_start": None, "period_end": fd, "document": r["file"],
            "locator": {"file": r["file"], "accession": r["adsh"], "cik": cik10, "byte_range": None},
            "text": head, "candidate_facts": [], "chars": len(head),
            "normalizer_version": config.NORMALIZER_VERSION, "delimiter_version": config.DELIMITER_VERSION,
            "exhibit_type": r["file_type"], "filing_status": "filed", "assurance_level": "not_applicable",
            "tier": "D", "filer_name": r["filer"], "mention_class": "contract", "groups_named": u["groups"].split(";"),
            "terms": r["terms"], "unit_order": int(u["order"])}


def _note_unit_block(u, client):
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
    fam = note_family(ren_f, report, shortname)
    tags = set(pre[(pre["adsh"] == u["adsh"]) & (pre["report"].astype(str).isin(fam))]["tag"])
    num = a["num"]
    num = num[(num["adsh"] == u["adsh"]) & (num["tag"].isin(tags))]
    m = {"adsh": u["adsh"], "class": "related_party" if RELATED_TAG.search(u["doc"]) else "note",
         "groups": u["groups"].split(";"), "terms": None, "tag": u["doc"]}
    try:
        b = note_block(client, m, sub_row, report, shortname, num, a["dims"], f"{u['order']:07d}")
    except net.NotCollected as exc:
        return None, f"not_collected: {exc}"
    b["unit_order"] = int(u["order"])
    b["block_kind"] = "discovery_note"
    return b, None


def prepare(n=50, rate=4.0):
    """Construit les blocs des `n` unités suivantes de la file qui ne le sont pas encore (une
    requête par page R) et les ajoute au catalogue de la découverte."""
    cfg = config.load()
    client = net.SecClient(AS_OF, cfg)
    client.min_interval = 1.0 / rate
    units = pd.read_parquet(UNITS)
    done = built_units()
    todo = [u for u in units.to_dict("records") if u["order"] not in done][:n]
    nb = 0
    for u in todo:
        if u["kind"] == "exhibit_header":
            b, err = _exhibit_block(u, client), None
        else:
            b, err = _note_unit_block(u, client)
        rec = {"order": int(u["order"]), "rank": int(u["rank"]), "cik": u["cik"], "kind": u["kind"],
               "adsh": u["adsh"], "doc": u["doc"], "content_key": b["content_key"] if b else None, "error": err}
        if b:
            with open(DISC_CATALOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(b, ensure_ascii=False) + "\n")
            nb += 1
        with open(BUILT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"blocs préparés : {nb} sur {len(todo)} unités ; requêtes {client.stats['requests']}")


# -- recherche complète côté client (E.0) une fois la découverte ouverte (D-0037) ------------

PERIODIC = {"10-K", "10-K/A", "10-KT", "10-KT/A", "10-Q", "10-Q/A", "10-QT", "10-QT/A",
            "20-F", "20-F/A", "40-F", "40-F/A"}
LOOKUP = ("edgar", "cik-lookup-data_2026-10-09.txt.zst")


def edgar_names():
    """Dénomination normalisée -> CIK, depuis la liste des noms d'EDGAR (§9.4)."""
    from .graph import normalize_name
    p = cache.other_path(*LOOKUP)
    if not p.exists():
        return {}
    out = {}
    for l in cache.read(p).decode("latin-1").splitlines():
        parts = l.rsplit(":", 2)
        if len(parts) == 3 and parts[1].isdigit():
            out.setdefault(normalize_name(parts[0]), set()).add(str(int(parts[1])))
    return out


def periodic_filings():
    """Rapports périodiques de chaque CIK dans les archives scannées : (cik -> [(form, filed)])."""
    out = {}
    for name in scanned_archives():
        sub = pd.read_parquet(BASE / name / "sub.parquet", columns=["cik", "form", "filed"])
        sub = sub[sub["form"].isin(PERIODIC)]
        for r in sub.itertuples(index=False):
            out.setdefault(str(int(r.cik)), []).append((r.form, r.filed))
    return out


def coverage_ok():
    """Toutes les archives de la période sont scannées sous le lexique courant."""
    todo = {a["name"] for a in in_period(archive_list(), period_start())}
    return todo <= set(scanned_archives())


def client_states(read_cks, extended_start):
    """État de la recherche côté client pour chaque contrepartie hors périmètre, par sa
    dénomination normalisée : (complète, motif, cik). Un client sans CIK sous sa dénomination
    ne dépose pas ; un CIK sans rapport périodique depuis le début de la fenêtre allongée n'a
    pas de notes à lire ; un déposant périodique n'est complet que si toutes ses unités qui
    nomment le fournisseur sont lues. Une archive non tirée laisse la recherche incomplète."""
    from .graph import normalize_name
    names = edgar_names()
    per = periodic_filings()
    units = pd.read_parquet(UNITS) if UNITS.exists() else pd.DataFrame()
    built = built_units()
    cands = pd.read_parquet(CANDIDATES) if CANDIDATES.exists() else pd.DataFrame()
    filer_cik = {normalize_name(n): str(c) for n, c in zip(cands.get("filer", []), cands.get("cik", []))}
    complete_cov = coverage_ok()
    ext = extended_start.strftime("%Y%m%d") if hasattr(extended_start, "strftime") else str(extended_start)
    # fournisseurs que le lexique nomme : un groupe ajouté après le scan (D-0043) n'y figure pas, et
    # les notes des déposants qui le nomment n'ont jamais été cherchées
    searched = {e["ref"] for e in lexicon()}

    def state(norm, s):
        if not complete_cov:
            return False, "search_incomplete", None
        ciks = {filer_cik[norm]} if norm in filer_cik else names.get(norm, set())
        if not ciks:
            return True, None, None                      # non-déposant (§10.4)
        cik = sorted(ciks)[0]
        reps = [f for c in ciks for f in per.get(c, []) if f[1] >= ext]
        if not reps:
            return True, None, cik                       # aucun rapport périodique dans la fenêtre
        if s not in searched:
            return False, "search_incomplete", cik
        if units.empty:
            return False, "not_processed", cik
        mine = units[(units["cik"].isin(ciks)) & (units["groups"].str.split(";").map(lambda g: s in g))]
        for u in mine.itertuples(index=False):
            b = built.get(u.order)
            if not b or not b.get("content_key") or b["content_key"] not in read_cks:
                return False, "not_processed", cik
        return True, None, cik
    return state

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "fetch":
        fetch(only=set(sys.argv[2:]) or None)
    elif cmd == "search":
        search(rate=float(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif cmd == "candidates":
        build_candidates()
    elif cmd == "prepare":
        prepare(int(sys.argv[2]) if len(sys.argv) > 2 else 50)
    elif cmd == "verify":
        verify_exhibits()
        verify_form_d()
    else:
        status()
