"""Bloc `montages` (D-0046, D-0049) : nommer les parties d'un montage que les notes d'un groupe
décrivent sans les nommer, par les pièces qui le décrivent.

Chaque montage est décrit dans config.yaml (`montages`) : période, requêtes de la recherche plein
texte d'EDGAR, déposants dont les rapports périodiques se tirent, termes qualifiants, plafond.
Unités : les paragraphes qui nomment un terme qualifiant, avec deux paragraphes avant et deux après,
fondus quand ils se chevauchent (D-0046, points 4, 8 et 9). Un terme ne qualifie jamais une pièce
d'un déposant dont il est le nom (`owner`) ; `only_in` le réserve aux pièces de déposants nommés.
Chaque pièce se tire une fois, en cache, par le client SEC journalisé.

    python -m pipeline.montages search <montage>    # recherche plein texte -> work/tmp
    python -m pipeline.montages fetch <montage>     # pièces en cache, relevés de portefeuille comptés
    python -m pipeline.montages corpus <montage>    # montage de corpus : documents des groupes déjà en cache
    python -m pipeline.montages prepare             # fenêtres de tous les montages -> db/montages_blocks.jsonl
    python -m pipeline.montages prepare <montage>   # ce montage seul ; les blocs des autres restent tels quels

Les formulaires de `count_only_forms` (Form D du montage Stargate, D-0058, point 7) sont comptés, non tirés.

Un montage de corpus (`source: corpus`, D-0058, point 3) ne cherche ni ne tire rien : ses pièces sont
les documents des groupes déjà en cache. Trois options : `skip_read` (une fenêtre dont chaque paragraphe
qualifiant est déjà dans un bloc lu du même dépôt n'est pas servie), `skip_risk_factors` (ni une fenêtre
dont chaque paragraphe qualifiant est dans la section des facteurs de risque, §14) et l'ordre
`recent_first` (du dépôt le plus récent au plus ancien).

Options de D-0064 : `forms` par requête (formulaires racines de la recherche, pièces comprises), `priority`
(classes de lecture, chacune du plus récent au plus ancien), `evidence: triplet` (pièce de 8-K classée par son
triplet, comme le registre des documents) et `pdf_text` (lettres en PDF lues par leur texte extrait).

D-0066 : `evidence: triplet` posé sur tous les montages, les items manquants lus dans les dépôts de la phase 0 ;
`retier` recalcule en place le niveau des blocs déjà préparés (textes, clés et lignes inchangés) ; un montage à
`source: span` lit un passage fixé (motifs de début et de fin), les lignes du document jointes.

    python -m pipeline.montages retier              # niveau des blocs préparés, par le triplet

D-0067 (volets 8 et 9) : source `hits` (pages de la recherche de la découverte déjà en cache, relues sans requête,
filtrées par type de pièce), source `lab_corpus` (documents des groupes, pièces des autres montages et blocs lus de la
découverte qui nomment un terme), test de partie (`party_chars`) et termes de clause (`clause_terms`), condition
`require` (un paragraphe qualifie s'il nomme aussi l'un des termes requis), largeur `window`, lecture complémentaire
(`complement` : une fenêtre déjà lue se sert pour les seules clauses, capacités et événements), ordre `party_first`,
niveau `evidence: registry` (comme le registre des documents, tous formulaires).

    python -m pipeline.montages replay <montage>    # source `hits` : pages en cache -> work/tmp, aucune requête
    python -m pipeline.montages lab_corpus <montage> # source `lab_corpus` : documents en cache, aucune requête

D-0068 (point 6) : source `backlog`, documents en cache des vendeurs (groupes vers lesquels va une arête commerciale d'un
client nommé) ; un paragraphe qualifie s'il nomme l'un des clients de son vendeur et un terme de carnet (`vocabulary`).

    python -m pipeline.montages backlog_corpus <montage>   # source `backlog` : documents en cache, aucune requête
    python -m pipeline.montages values_corpus <montage>    # source `edge_values` : blocs lus qui portent une arête de valeur
"""
import json
import re
import sys

import pandas as pd

from . import cache, config, net
from . import discovery as D

CATALOG = config.DB_DIR / "montages_blocks.jsonl"
HOLDINGS_FORMS = {"NPORT-P", "NPORT-P/A", "NT NPORT-P", "N-CSR", "N-CSR/A", "N-CSRS", "N-MFP3", "13F-HR", "13F-HR/A",
                  "N-PX", "N-PX/A", "486BPOS", "POS EX", "11-K"}
WINDOW = 2
FIRST = "meta_hyperion"        # montage de D-0046 : chemins et clés d'origine, inchangés


def specs(cfg=None):
    cfg = cfg or config.load()
    return cfg.get("montages") or {}


def _paths(mid):
    """Fichiers d'un montage ; ceux de D-0046 gardent leur nom d'origine."""
    if mid == FIRST:
        return (config.ROOT / "work" / "tmp" / "montages_hits.json", config.DB_DIR / "montages_docs.parquet",
                config.DB_DIR / "montages_info.json")
    return (config.ROOT / "work" / "tmp" / f"montages_hits_{mid}.json", config.DB_DIR / f"montages_docs_{mid}.parquet",
            config.DB_DIR / f"montages_info_{mid}.json")


def qualify_rx(filer, spec):
    """Termes qualifiants d'une pièce : jamais le nom de son déposant (D-0046, point 9) ; un terme
    `only_in` ne qualifie que les pièces des déposants nommés (D-0049, point 4)."""
    own = (filer if isinstance(filer, str) else "").lower()     # nom absent (NaN d'un relevé, D-0067) : aucun
    t = []
    for term in spec["terms"]:
        if any(o in own for o in term.get("owner") or []):
            continue
        if term.get("only_in") and not any(o in own for o in term["only_in"]):
            continue
        t.append(term["rx"])
    return re.compile("|".join(t)) if t else None


def noted_rx(spec):
    return re.compile("|".join(spec["noted_terms"]))


def _client(rate=4.0):
    c = net.SecClient(config.as_of(), config.load())
    c.min_interval = 1.0 / rate
    return c


def search(mid, rate=4.0):
    """Toutes les pages de chaque requête du montage, tous formulaires, sur sa période (D-0049) ;
    pages gardées en cache (cache/search) et requêtes consignées."""
    spec = specs()[mid]
    client = _client(rate)
    start, end = spec["period"]
    hits_path = _paths(mid)[0]
    out, totals = [], []
    for qd in spec["queries"]:
        params = {"q": qd["q"], "dateRange": "custom", "startdt": start, "enddt": end}
        if qd.get("cik"):
            params["ciks"] = qd["cik"]
        if qd.get("forms"):                         # formulaires racines, pièces comprises (D-0064)
            params["forms"] = ",".join(qd["forms"])
        data, url, _ = D._efts(client, dict(params, **{"from": 0}))
        tot = data["hits"]["total"]
        n = tot["value"]
        pages = [data] + [D._efts(client, dict(params, **{"from": f}))[0] for f in range(100, min(n, 10000), 100)]
        for page in pages:
            for h in page["hits"]["hits"]:
                s = h["_source"]
                out.append({"query": qd["q"], "cik_filter": qd.get("cik"), "id": h["_id"],
                            "adsh": s.get("adsh") or h["_id"].split(":")[0],
                            "file": h["_id"].split(":", 1)[1] if ":" in h["_id"] else None,
                            "file_type": s.get("file_type"), "form": s.get("form"), "file_date": s.get("file_date"),
                            "names": s.get("display_names"), "ciks": s.get("ciks"), "items": s.get("items"),
                            "file_description": s.get("file_description")})
        totals.append({"query": qd["q"], "cik_filter": qd.get("cik"), "total": n, "relation": tot.get("relation"),
                       "url": url})
        D._log_query({"montage": mid, "query": qd["q"], "cik": qd.get("cik"), "forms": qd.get("forms"), "start": start,
                      "end": end, "total": n, "status": "complete"}, config.WORK / "montages" / "efts_queries.jsonl")
    hits_path.parent.mkdir(parents=True, exist_ok=True)
    hits_path.write_text(json.dumps(out, ensure_ascii=False))
    for t in totals:
        print(t["query"], t["cik_filter"] or "", t["total"], t["relation"] or "")
    return totals


def periodic(client, cik, start, end):
    """Rapports périodiques (10-Q, 10-K) d'un déposant, déposés dans la période."""
    cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    p = config.CACHE / "edgar" / "submissions" / f"CIK{cik}.json.zst"
    if p.exists():
        sub = json.loads(cache.read(p))
    else:
        raw, _ = client.get(url)
        cache.write(p, raw)
        sub = json.loads(raw)
    r = sub["filings"]["recent"]
    out = []
    for form, acc, date, doc in zip(r["form"], r["accessionNumber"], r["filingDate"], r["primaryDocument"]):
        if form in ("10-Q", "10-K") and start <= date <= end:
            out.append({"adsh": acc, "file": doc, "form": form, "file_type": form, "file_date": date,
                        "cik": cik, "filer": sub["name"], "source": "periodic"})
    return out, sub["name"]


def fetch(mid, rate=4.0):
    """Pièces narratives des résultats et rapports périodiques des déposants nommés ; les relevés
    de portefeuille sont comptés, pas tirés (D-0046, point 8)."""
    spec = specs()[mid]
    hits_path, docs_path, info_path = _paths(mid)
    start, end = spec["period"]
    client = _client(rate)
    hits = json.loads(hits_path.read_text())
    docs, holdings, counted = {}, {}, {}
    count_only = set(spec.get("count_only_forms") or [])
    for h in hits:
        if h["form"] in HOLDINGS_FORMS:
            holdings[h["form"]] = holdings.get(h["form"], 0) + 1
            continue
        if h["form"] in count_only:          # formulaires d'un autre bloc (Form D : bloc `form_d`), comptés, non tirés
            counted[h["form"]] = counted.get(h["form"], 0) + 1
            continue
        if not h.get("file"):
            continue
        cik = str((h.get("ciks") or [""])[0]).zfill(10)
        name = re.sub(r"\s+\(.*$", "", (h.get("names") or [""])[0]).strip()
        docs.setdefault((h["adsh"], h["file"]), {"adsh": h["adsh"], "file": h["file"], "form": h["form"],
                                                 "file_type": h["file_type"], "file_date": h["file_date"],
                                                 "cik": cik, "filer": name, "source": "efts", "queries": set(),
                                                 "items": ",".join(h.get("items") or []) or None})
        docs[(h["adsh"], h["file"])]["queries"].add(h["query"] + (f" [CIK {h['cik_filter']}]" if h.get("cik_filter") else ""))
    names = {}
    for c in spec.get("periodic") or []:
        rows, nm = periodic(client, c, start, end)
        names[str(c).zfill(10)] = nm
        for d in rows:
            docs.setdefault((d["adsh"], d["file"]), {**d, "queries": set()})
    rows = []
    for (adsh, f), d in sorted(docs.items(), key=lambda kv: (kv[1]["file_date"], kv[0])):
        path = cache.archive_path(d["cik"], adsh, f)
        state = "cached"
        if not path.exists():
            url = f"https://www.sec.gov/Archives/edgar/data/{int(d['cik'])}/{adsh.replace('-', '')}/{f}"
            try:
                raw, _ = client.get(url)
                cache.write(path, raw)
                state = "fetched"
            except net.NotCollected as exc:
                state = f"not_collected: {exc}"
        rows.append({**d, "queries": ";".join(sorted(d["queries"])), "state": state})
    pd.DataFrame(rows).to_parquet(docs_path, index=False)
    info = {"holdings_not_read": holdings, "requests": client.stats}
    if count_only:
        info["forms_not_read"] = counted
    if mid == FIRST:
        info["owl_name"] = names.get(str(spec["periodic"][0]).zfill(10))
    else:
        info["periodic_names"] = names
    info_path.write_text(json.dumps(info))
    print(len(rows), "pièces ;", sum(r["state"] == "fetched" for r in rows), "tirées ; relevés écartés", holdings,
          *(["; formulaires comptés", counted] if count_only else []))


def corpus(mid):
    """Pièces d'un montage de corpus (D-0058, point 3) : documents principaux et pièces des groupes de
    config.yaml déjà en cache, en HTML ou en texte, déposés dans la période ; aucune requête. Un
    pré-filtre sur les octets, insensible à la casse, écarte les documents qui ne nomment aucun terme."""
    spec = specs()[mid]
    _, docs_path, info_path = _paths(mid)
    start, end = spec["period"]
    meta = json.loads((config.DB_DIR / "phase0.json").read_text())["meta"]
    groups = set(config.load()["groups"]) if spec.get("groups", "all") == "all" else set(spec["groups"])
    d = pd.read_parquet(config.ROOT / "tables" / "documents.parquet",
                        columns=["cik", "group_id", "accession", "document", "form", "sgml_type", "filing_date", "resource_kind"])
    d = d[d["group_id"].isin(groups) & d["resource_kind"].isin(["primary_document", "exhibit"])
          & d["document"].str.lower().str.endswith((".htm", ".html", ".txt"))]
    d = d.assign(file_date=d["filing_date"].astype(str))
    d = d[(d["file_date"] >= start) & (d["file_date"] <= end)].drop_duplicates(["accession", "document"])
    pre = re.compile("|".join(t["rx"] for t in spec["terms"]).encode(), re.I)
    rows, scanned = [], 0
    for x in d.sort_values(["file_date", "accession", "document"]).itertuples(index=False):
        path = cache.archive_path(x.cik, x.accession, x.document)
        if not path.exists():
            continue
        scanned += 1
        if not pre.search(cache.read(path)):
            continue
        rows.append({"adsh": x.accession, "file": x.document, "form": x.form, "file_type": x.sgml_type or x.form,
                     "file_date": x.file_date, "cik": x.cik, "filer": (meta.get(x.cik) or {}).get("name") or x.group_id,
                     "source": "corpus", "queries": "", "state": "cached"})
    pd.DataFrame(rows).to_parquet(docs_path, index=False)
    info_path.write_text(json.dumps({"source": "corpus", "documents_in_period": int(len(d)), "documents_scanned": scanned,
                                     "documents_named": len(rows)}))
    print(mid, ":", len(d), "documents dans la période ;", scanned, "en cache ;", len(rows), "nomment un terme")


def replay(mid):
    """Source `hits` (D-0067, point 3) : pages de la recherche plein texte de la découverte déjà en cache, relues par
    un client sans réseau (une page absente arrête tout, aucune requête) ; un résultat se garde si son type de pièce
    vérifie `file_type_rx`. Même format que `search`, pour `fetch`."""
    spec = specs()[mid]
    r = spec["replay"]

    class _NoNet:
        stats = {"requests": 0}
        min_interval = 0

        def get(self, url):
            raise RuntimeError(f"{mid} : page de recherche absente du cache, aucune requête (D-0067, point 3) : {url}")
    keep = re.compile(spec["file_type_rx"])
    log = config.WORK / "montages" / f"replay_{mid}.jsonl"
    out = []
    for term in r["terms"]:
        for h in D.harvest(_NoNet(), term, r.get("forms") or D.EX10_FORMS, start=r.get("start", D.START),
                           end=r.get("end"), keep=lambda x: bool(keep.search(str(x.get("file_type") or "").upper())),
                           log=log):
            out.append({"query": term, "cik_filter": None, "id": h["id"], "adsh": h["adsh"], "file": h["file"],
                        "file_type": h["file_type"], "form": h["form"], "file_date": h["file_date"],
                        "names": h["display_names"], "ciks": h["ciks"], "items": h["items"], "file_description": None})
    hits_path = _paths(mid)[0]
    hits_path.parent.mkdir(parents=True, exist_ok=True)
    hits_path.write_text(json.dumps(out, ensure_ascii=False))
    print(mid, ":", len(out), "résultats ;", len({(h["adsh"], h["file"]) for h in out}), "pièces distinctes")
    return out


def lab_corpus(mid):
    """Source `lab_corpus` (D-0067, point 4) : documents des groupes en cache (registre des documents), pièces des
    autres montages (sauf ceux de `exclude_montages`) et blocs lus de la découverte qui nomment un terme, déposés dans
    la période ; aucune requête. Un bloc de la découverte dont le document est en cache le donne ; sinon (note des Notes
    Data Sets), le texte du bloc tient lieu de document (`source: block`)."""
    from . import reader
    spec = specs()[mid]
    _, docs_path, info_path = _paths(mid)
    start, end = spec["period"]
    meta = json.loads((config.DB_DIR / "phase0.json").read_text())["meta"]
    pre = re.compile("|".join(t["rx"] for t in spec["terms"]).encode(), re.I)
    skip = set()
    for other in spec.get("exclude_montages") or []:
        op = _paths(other)[1]
        if op.exists():
            skip |= {(a, f) for a, f in pd.read_parquet(op, columns=["adsh", "file"]).itertuples(index=False)}
    rows, seen, counts = [], set(), {"groups": 0, "montages": 0, "discovery": 0, "blocks": 0}
    catalog = reader.load_catalog()
    # déposant hors des groupes (Cerebras, SB Energy, Nscale…) : le nom que portent ses blocs déjà au catalogue
    from collections import Counter
    by_cik = {}
    for b in catalog:
        if isinstance(b.get("filer_name"), str) and b["filer_name"]:
            by_cik.setdefault(str(b.get("cik") or "").zfill(10), Counter())[b["filer_name"]] += 1
    cat_name = {c: n.most_common(1)[0][0] for c, n in by_cik.items()}

    def add(r, src):
        k = (r["adsh"], r["file"])
        if k in seen or k in skip or not (start <= str(r["file_date"])[:10] <= end):
            return
        seen.add(k)
        rows.append({**r, "source": src, "queries": "", "state": "cached"})
        counts[src] += 1
    d = pd.read_parquet(config.ROOT / "tables" / "documents.parquet",
                        columns=["cik", "group_id", "accession", "document", "form", "sgml_type", "filing_date",
                                 "resource_kind", "items"])
    d = d[d["resource_kind"].isin(["primary_document", "exhibit"]) & d["document"].str.lower().str.endswith((".htm", ".html", ".txt"))]
    for x in d.drop_duplicates(["accession", "document"]).sort_values(["filing_date", "accession", "document"]).itertuples(index=False):
        path = cache.archive_path(x.cik, x.accession, x.document)
        if path.exists() and pre.search(cache.read(path)):
            add({"adsh": x.accession, "file": x.document, "form": x.form, "file_type": x.sgml_type or x.form,
                 "file_date": str(x.filing_date)[:10], "cik": x.cik, "items": x.items,
                 "filer": (meta.get(x.cik) or {}).get("name") or cat_name.get(str(x.cik).zfill(10))
                 or _text_or_none(x.group_id) or ""}, "groups")
    for other, ospec in specs().items():
        op = _paths(other)[1]
        if other == mid or other in (spec.get("exclude_montages") or []) or not op.exists():
            continue
        for x in pd.read_parquet(op).to_dict("records"):
            if not str(x.get("state") or "").startswith(("cached", "fetched")) or x.get("source") == "block":
                continue
            # D-0067, point 14 : un document en texte seulement (un PDF se lit par le montage qui en a l'option) ; une
            # pièce que la règle d'un montage écarte le reste (texte extrait d'une lettre lue en PDF, D-0064, point 12)
            if not str(x["file"]).lower().endswith((".htm", ".html", ".txt")) or \
                    _excluded({**x, "filer": _text_or_none(x.get("filer")) or ""}, ospec):
                continue
            path = cache.archive_path(str(x["cik"]).zfill(10), x["adsh"], x["file"])
            if path.exists() and pre.search(cache.read(path)):
                add({"adsh": x["adsh"], "file": x["file"], "form": x["form"], "file_type": x.get("file_type"),
                     "file_date": str(x["file_date"])[:10], "cik": str(x["cik"]).zfill(10), "items": x.get("items"),
                     "filer": _text_or_none(x.get("filer")) or ""}, "montages")
    rx = re.compile("|".join(t["rx"] for t in spec["terms"]))
    for b in catalog:
        if b.get("block_kind") == "montage_text" or not str(b.get("block_kind") or "").startswith("discovery_"):
            continue
        if not (config.OBS_DIR / f"{b['content_key']}.jsonl").exists():
            continue
        t = b["text"] if isinstance(b["text"], str) else "\n".join(b["text"])
        if not rx.search(t):
            continue
        base = {"adsh": b["accession"], "form": b.get("form"), "file_date": str(b.get("filing_date"))[:10],
                "cik": str(b["cik"]).zfill(10), "items": b.get("item"), "filer": b.get("filer_name")}
        doc = b.get("document") or ""
        if doc.lower().endswith((".htm", ".html", ".txt")) and cache.archive_path(base["cik"], b["accession"], doc).exists():
            add({**base, "file": doc, "file_type": b.get("exhibit_type") or b.get("form")}, "discovery")
        else:
            add({**base, "file": f"block:{b['content_key']}", "file_type": b.get("exhibit_type"),
                 "block_key": b["content_key"], "tier": b.get("tier"), "assurance_level": b.get("assurance_level"),
                 "filing_status": b.get("filing_status")}, "blocks")
    pd.DataFrame(rows).to_parquet(docs_path, index=False)
    info_path.write_text(json.dumps({"source": "lab_corpus", "documents_named": len(rows), "by_source": counts,
                                     "excluded_pieces": len(skip)}))
    print(mid, ":", len(rows), "documents nomment un terme ;", counts)


def backlog_names(cfg=None):
    """Montage `backlog` (D-0068, point 6) : pour chaque vendeur, les noms de ses clients nommés (arête commerciale du
    client vers lui, tables du dernier assemblage), tels que le registre (entités et alias) et le lexique les écrivent ;
    trois caractères au moins."""
    from . import backlog
    cfg = cfg or config.load()
    ln = pd.read_parquet(config.ROOT / "tables" / "links.parquet",
                         columns=["link_kind", "family", "from_group", "to_group", "elimination_status"])
    ln = ln[ln["link_kind"] == "edge"]
    clients = backlog.sellers(zip(ln["from_group"], ln["to_group"], ln["family"], ln["elimination_status"].fillna("")),
                              set(cfg["groups"]))
    ent = pd.read_parquet(config.ROOT / "tables" / "entities.parquet", columns=["entity_id", "record_kind", "ref", "name"])
    members, names = {}, {}
    for r in ent.itertuples(index=False):
        if r.record_kind == "membership":
            members.setdefault(r.ref, set()).add(r.entity_id)
        elif r.record_kind in ("entity", "alias") and isinstance(r.name, str):
            names.setdefault(r.entity_id, set()).add(r.name)
    terms = {}
    lex = (cfg.get("discovery") or {}).get("lexicon") or {}
    for k in ("seed", "confirmed"):
        for x in lex.get(k) or []:
            terms.setdefault(x["ref"], set()).add(x["term"])

    def of(g):
        return {n for e in members.get(g, ()) for n in names.get(e, ())} | terms.get(g, set())
    return {s: {n for c in cs for n in of(c) if len(n) >= 3} for s, cs in clients.items()}


def backlog_corpus(mid):
    """Source `backlog` (D-0068, point 6) : documents en cache des vendeurs (registre des documents), documents
    principaux et pièces, formulaires de `forms`, déposés dans la période ; pièces EX-99 écartées (furnished, niveau E) ;
    aucune requête. Un pré-filtre sur les octets écarte les documents sans terme de carnet."""
    from . import backlog
    spec = specs()[mid]
    _, docs_path, info_path = _paths(mid)
    start, end = spec["period"]
    meta = json.loads((config.DB_DIR / "phase0.json").read_text())["meta"]
    names = backlog_names()
    d = pd.read_parquet(config.ROOT / "tables" / "documents.parquet",
                        columns=["cik", "group_id", "accession", "document", "form", "sgml_type", "filing_date",
                                 "resource_kind", "items"])
    # une pièce EX-99 que le registre ne type pas se reconnaît à son nom de fichier (D-0068, point 15)
    d = d[d["group_id"].isin(list(names)) & d["resource_kind"].isin(["primary_document", "exhibit"])
          & d["form"].isin(spec.get("forms") or backlog.FORMS)
          & d["document"].str.lower().str.endswith((".htm", ".html", ".txt"))
          & ~d["sgml_type"].fillna("").str.upper().str.startswith("EX-99")
          & ~(d["sgml_type"].isna() & d["document"].str.contains(backlog.EX99_FILE, case=False, regex=True))]
    d = d.assign(file_date=d["filing_date"].astype(str).str[:10])
    d = d[(d["file_date"] >= start) & (d["file_date"] <= end)].drop_duplicates(["accession", "document"])
    pre = re.compile(backlog.PREFILTER)
    rows, scanned = [], 0
    for x in d.sort_values(["file_date", "accession", "document"]).itertuples(index=False):
        path = cache.archive_path(x.cik, x.accession, x.document)
        if not path.exists():
            continue
        scanned += 1
        if not pre.search(cache.read(path)):
            continue
        rows.append({"adsh": x.accession, "file": x.document, "form": x.form, "file_type": x.sgml_type or x.form,
                     "file_date": x.file_date, "cik": x.cik, "items": x.items, "group_id": x.group_id,
                     "filer": (meta.get(x.cik) or {}).get("name") or x.group_id,
                     "source": "backlog", "queries": "", "state": "cached"})
    pd.DataFrame(rows).to_parquet(docs_path, index=False)
    info_path.write_text(json.dumps({"source": "backlog", "sellers": len(names), "documents_in_period": int(len(d)),
                                     "documents_scanned": scanned, "documents_named": len(rows)}))
    print(mid, ":", len(names), "vendeurs ;", len(d), "documents dans la période ;", scanned, "en cache ;", len(rows),
          "nomment un terme de carnet")


def values_corpus(mid):
    """Source `edge_values` (D-0068, point 15) : les blocs lus qui portent une arête de valeur, arête commerciale du
    client vers le vendeur (engagement d'achat ou bail de capacité), montant en USD, niveau A à D, au stade `signed` ou
    `available`, tirée d'une ligne déposée par le vendeur lui-même (tables du dernier assemblage). Le texte du bloc tient
    lieu de document (`source: block`) ; les citations de ses lignes font les paragraphes qualifiants. Aucune requête."""
    from . import reader
    specs()[mid]                        # identifiant de montage inconnu : KeyError, comme avant
    _, docs_path, info_path = _paths(mid)
    groups = set(config.load()["groups"])
    ln = pd.read_parquet(config.ROOT / "tables" / "links.parquet",
                         columns=["link_key", "link_kind", "family", "edge_type", "from_group", "to_group", "amount", "unit",
                                  "stage", "tier", "elimination_status", "evidence_keys"])
    e = ln[(ln["link_kind"] == "edge") & (ln["family"] == "commercial")
           & ln["edge_type"].isin(["purchase_commitment", "capacity_lease"]) & ln["amount"].notna() & (ln["unit"] == "USD")
           & ln["tier"].isin(["A", "B", "C", "D"]) & ln["stage"].isin(["signed", "available"])
           & (ln["elimination_status"] != "eliminated") & ln["to_group"].isin(groups) & ln["from_group"].notna()
           & (ln["from_group"] != ln["to_group"])]
    ob = pd.read_parquet(config.ROOT / "tables" / "observations.parquet",
                         columns=["obs_key", "content_key", "group_id", "quote"]).set_index("obs_key")
    quotes, edges = {}, {}
    for r in e.itertuples(index=False):
        for k in json.loads(r.evidence_keys or "[]"):
            if k not in ob.index or ob.at[k, "group_id"] != r.to_group:     # ligne déposée par le vendeur lui-même
                continue
            ck = ob.at[k, "content_key"]
            quotes.setdefault(ck, set()).add(ob.at[k, "quote"])
            edges.setdefault(ck, set()).add(r.link_key)
    catalog = {b["content_key"]: b for b in reader.load_catalog()}
    rows = []
    for ck in sorted(quotes):
        b = catalog.get(ck)
        if b is None:
            continue
        rows.append({"adsh": b["accession"], "file": f"block:{ck}", "block_key": ck, "form": b.get("form"),
                     "file_type": b.get("exhibit_type"), "file_date": str(b.get("filing_date"))[:10],
                     "cik": str(b["cik"]).zfill(10), "items": b.get("item"), "group_id": b["group_id"],
                     "filer": b.get("filer_name") if isinstance(b.get("filer_name"), str) else b["group_id"],
                     "tier": b.get("tier"), "assurance_level": b.get("assurance_level"),
                     "filing_status": b.get("filing_status"), "quotes": json.dumps(sorted(quotes[ck]), ensure_ascii=False),
                     "edges": json.dumps(sorted(edges[ck])), "source": "block", "queries": "", "state": "cached"})
    pd.DataFrame(rows).to_parquet(docs_path, index=False)
    info_path.write_text(json.dumps({"source": "edge_values", "value_edges": int(len(e)),
                                     "edges_filed_by_seller": sum(len(v) for v in edges.values()), "blocks": len(rows)}))
    print(mid, ":", len(e), "arêtes de valeur ;", sum(len(v) for v in edges.values()), "tirées d'une ligne du vendeur ;",
          len(rows), "blocs lus")


def quote_test(quotes):
    """Un paragraphe qualifie s'il contient l'une des citations, ou s'il est contenu dans une citation qui court sur
    plusieurs paragraphes (même normalisation que la validation des citations)."""
    from . import textnorm
    qs = [textnorm.norm_for_match(q).lower() for q in quotes if isinstance(q, str) and q.strip()]

    def t(p):
        n = textnorm.norm_for_match(p).lower()
        return any(q in n or (len(n) > 40 and n in q) for q in qs)
    return t


# section des facteurs de risque (§14 : une mention n'y fait jamais une unité ; D-0058, point 3)
RF_HEAD = re.compile(r"^\W{0,3}(?:(?:item\s*)?1a\b\.?|(?:item\s*)?3\.?\s*d\b\.?|d\.)?\s*[:.\-–—]?\s*risk\s+factors\.?\s*$", re.I)
RF_END = re.compile(r"^\W{0,3}(?:item\s*(?:1b|1c|2|3|4|5|6|7|7a|8|9|9a|10)\b|part\s+ii\b|unresolved staff comments\b|"
                    r"cautionary (?:note|statement)s?\b|special note|forward[\s-]+looking statements\b|use of proceeds\b|"
                    r"dividend policy\b|capitalization\b|dilution\b|market,?\s+(?:and\s+)?industry\b|"
                    r"management['’]?s discussion)", re.I)
HEAD_MAX = 120


def risk_factor_span(paras):
    """Paragraphes de la section des facteurs de risque, [début, fin[, ou None : du titre « Risk Factors »
    (Item 1A, Item 3.D, titre d'un prospectus) au titre majeur suivant ; la plus longue des sections
    candidates, ce qui écarte les entrées de la table des matières (D-0058, point 3)."""
    best = None
    for s, p in enumerate(paras):
        if len(p) > HEAD_MAX or not RF_HEAD.search(p):
            continue
        e = len(paras)
        for j in range(s + 1, len(paras)):
            if len(paras[j]) <= HEAD_MAX and RF_END.search(paras[j]):
                e = j
                break
        size = sum(len(x) for x in paras[s:e])
        if best is None or size > best[2]:
            best = (s, e, size)
    return (best[0], best[1]) if best else None


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


def read_texts(mid):
    """Textes des blocs déjà lus, par accession, hors des blocs de ce montage (D-0058, point 3)."""
    from . import reader
    out = {}
    for b in reader.load_catalog():
        if b.get("montage") == mid or not (config.OBS_DIR / f"{b['content_key']}.jsonl").exists():
            continue
        t = b["text"] if isinstance(b["text"], str) else "\n".join(b["text"])
        out.setdefault(b.get("accession"), []).append(_norm(t))
    return out


def covered(para, texts):
    """Un paragraphe figure mot pour mot, aux blancs près, dans l'un des textes lus du même dépôt."""
    p = _norm(para)
    return bool(p) and any(p in t for t in texts)


NUMBERED = re.compile(r"^\d{1,3}\.\s")


def pdf_paragraphs(pages):
    """Paragraphes du texte d'un PDF extrait page par page en mode « layout » de pypdf, qui rend un saut
    vertical par une ligne vide : les lignes d'un paragraphe se joignent, les blancs répétés se réduisent
    à un ; un paragraphe finit sur une ligne vide, en fin de page, ou avant une ligne qui ouvre un
    commentaire numéroté (« 1. ») (D-0064)."""
    out = []
    for page in pages:
        cur = []
        for line in (page or "").split("\n"):
            line = re.sub(r"\s+", " ", line).strip()
            if not line or NUMBERED.match(line):
                if cur:
                    out.append(" ".join(cur))
                cur = [line] if line else []
                continue
            cur.append(line)
        if cur:
            out.append(" ".join(cur))
    return "\n".join(out)


def document_text(raw, spec):
    """Texte d'une pièce de montage. Un montage à `pdf_text` (lettres UPLOAD du personnel de la SEC, D-0064) lit
    un PDF par son texte extrait (pypdf, mode « layout », page par page ; mode simple pour une page que le
    premier ne lit pas), en paragraphes ; un PDF illisible ou sans texte (image numérisée) n'a aucun paragraphe.
    Tout le reste passe par le normaliseur, comme avant."""
    if spec.get("pdf_text") and raw[:5] == b"%PDF-":
        import io
        from pypdf import PdfReader
        try:
            texts = []
            for page in PdfReader(io.BytesIO(raw)).pages:
                try:
                    texts.append(page.extract_text(extraction_mode="layout"))
                except Exception:
                    texts.append(page.extract_text())
        except Exception:
            return "", "pdf_unreadable"
        text = pdf_paragraphs(texts)
        return text, "pdf_text" if text else "pdf_no_text"
    return D.plain_text(raw)


def paragraphs(text):
    return [p for p in (x.strip() for x in text.split("\n")) if p]


def _test(rx):
    """Un paragraphe qualifie-t-il ? `rx` : expression compilée, prédicat (D-0067) ou None."""
    if rx is None:
        return lambda p: False
    return rx if callable(rx) else (lambda p: bool(rx.search(p)))


def qualifier(d, spec, text):
    """Prédicat des paragraphes qualifiants d'une pièce, et si le laboratoire y est partie (D-0067, points 3 et 4) :
    termes du montage (qualify_rx) ; dans une pièce dont un terme figure dans ses `party_chars` premiers caractères,
    les termes de clause (`clause_terms`) qualifient aussi ; avec `require`, un paragraphe ne qualifie que s'il nomme
    aussi l'un des termes requis, dans le même paragraphe."""
    rx = qualify_rx(d["filer"], spec)
    if rx is None:
        return None, False
    party = bool(spec.get("party_chars")) and bool(rx.search(text[:spec["party_chars"]]))
    if party:                 # noms du laboratoire lus dans le préambule (D-0067, point 15)
        d["party_terms"] = sorted({m.group(0) for m in rx.finditer(text[:spec["party_chars"]])})
    clause = re.compile("|".join(spec["clause_terms"]), re.I) if party and spec.get("clause_terms") else None
    req = re.compile("|".join(spec["require"]), re.I) if spec.get("require") else None

    def q(p):
        if not (rx.search(p) or (clause is not None and clause.search(p))):
            return False
        return req is None or bool(req.search(p))
    return q, party


def windows(paras, rx, width=WINDOW):
    """Fenêtres de lecture : paragraphes qui nomment un terme qualifiant, deux avant, deux après,
    fondues quand elles se chevauchent (D-0046, points 4, 8 et 9) ; `width` paragraphes de part et
    d'autre pour un montage à `window` (D-0067)."""
    test = _test(rx)
    hits = [i for i, p in enumerate(paras) if test(p)]
    spans = []
    for i in hits:
        a, b = max(0, i - width), min(len(paras), i + width + 1)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    return spans


def _excluded(d, spec):
    """Règle d'exclusion du montage qui écarte une pièce (D-0049, point 11), ou None."""
    own = (d["filer"] or "").lower()
    for r in spec.get("exclude") or []:
        if r.get("filer") and r["filer"] not in own:
            continue
        if r.get("forms") and d["form"] not in r["forms"]:
            continue
        if r.get("file_types") and d.get("file_type") not in r["file_types"]:
            continue
        if r.get("file_rx") and not re.search(r["file_rx"], d["file"] or "", re.I):
            continue
        return r
    return None


_FILING_ITEMS = {}


def filing_items():
    """Items des 8-K des dépôts de la phase 0 (db/filings.parquet), par accession : secours des montages dont
    la recherche n'a pas gardé les items (D-0066, point 5)."""
    if not _FILING_ITEMS:
        p = config.DB_DIR / "filings.parquet"
        if p.exists():
            f = pd.read_parquet(p, columns=["accessionNumber", "items"])
            _FILING_ITEMS.update({a: i for a, i in zip(f["accessionNumber"], f["items"]) if isinstance(i, str) and i})
    return _FILING_ITEMS


def _text_or_none(v):
    return v if isinstance(v, str) and v and v.upper() not in ("NAN", "NONE") else None


def evidence(d, spec):
    """Niveau de preuve d'une pièce de montage : par son formulaire (D.form_evidence), comme avant. Un montage à
    `evidence: triplet` (D-0064 ; D-0066, point 5) classe une pièce de 8-K par son triplet, comme le registre des
    documents (§2.1, §2.3) : le type de pièce vient du montage, les items de la recherche plein texte, à défaut
    des dépôts de la phase 0 ; contrat (EX-10, EX-4, EX-2) D, EX-99 furnished E, document principal dont les
    items sont tous 2.02, 7.01 ou 9.01 furnished E, le reste C."""
    if d.get("source") == "block" and d.get("tier"):     # bloc de la découverte (D-0067) : son niveau, tel quel
        return d["tier"], d.get("assurance_level"), d.get("filing_status")
    if spec.get("evidence") == "registry":                # D-0067 : comme le registre des documents, tous formulaires
        from . import documents
        ft = (_text_or_none(d.get("file_type")) or "").upper()
        items = _text_or_none(d.get("items")) or filing_items().get(d.get("adsh"))
        status, _, assurance, tier = documents._classify("exhibit" if ft.startswith("EX-") else "primary_document",
                                                        d["form"], ft, items)
        return tier, assurance, status
    if spec.get("evidence") == "triplet" and d["form"] in ("8-K", "8-K/A"):
        from . import documents
        ft = (_text_or_none(d.get("file_type")) or "").upper()
        items = _text_or_none(d.get("items")) or filing_items().get(d.get("adsh"))
        status, _, assurance, tier = documents._classify("exhibit" if ft.startswith("EX-") else "primary_document",
                                                        d["form"], ft, items)
        return tier, assurance, status
    return D.form_evidence(d["form"], None)


def retier():
    """Niveau des blocs déjà préparés des montages à `evidence: triplet`, recalculé en place (D-0066, point 5) :
    les textes, les clés de contenu et les lignes ne changent pas ; seuls le niveau, l'assurance et le statut de
    dépôt suivent le triplet. Renvoie les changements comptés par (montage, ancien niveau, nouveau niveau)."""
    from collections import Counter
    sp = specs()
    docs = {}
    for mid, spec in sp.items():
        p = _paths(mid)[1]
        if spec.get("evidence") == "triplet" and p.exists():
            for r in pd.read_parquet(p).to_dict("records"):
                docs[(mid, r["adsh"], r["file"])] = r
    changed, out = Counter(), []
    with open(CATALOG, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh]
    for b in rows:
        spec = sp.get(b.get("montage")) or {}
        if spec.get("evidence") == "triplet" and b.get("form") in ("8-K", "8-K/A"):
            d = docs.get((b["montage"], b["accession"], b["document"])) or {
                "adsh": b["accession"], "form": b["form"], "file_type": b.get("exhibit_type")}
            tier, assurance, status = evidence(d, spec)
            if (tier, assurance, status) != (b.get("tier"), b.get("assurance_level"), b.get("filing_status")):
                changed[(b["montage"], b.get("tier"), tier)] += 1
                b = dict(b, tier=tier, assurance_level=assurance, filing_status=status)
        out.append(b)
    tmp = CATALOG.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for b in out:
            fh.write(json.dumps(b, ensure_ascii=False) + "\n")
    tmp.replace(CATALOG)
    return changed


def span_blocks(mid, spec, groups_by_cik):
    """Montage à `source: span` (D-0066, point 7) : les paragraphes du document, ici des lignes, se joignent par une
    espace ; chaque passage va de la première occurrence du motif de début à la fin de la première occurrence, après
    elle, du motif de fin. Les paragraphes couverts sont notés avec le bloc."""
    import bisect
    from . import blocks
    from .graph import normalize_name
    out = []
    for n, s in enumerate(spec.get("spans") or []):
        cik = str(s["cik"]).zfill(10)
        raw = cache.read(cache.archive_path(cik, s["accession"], s["file"]))
        text, how = document_text(raw, spec)
        norm = [re.sub(r"\s+", " ", x).strip() for x in paragraphs(text)]
        offs, pos = [], 0
        for x in norm:
            offs.append(pos)
            pos += len(x) + 1
        joined = " ".join(norm)
        ms = re.search(s["start"], joined)
        me = re.compile(s["end"]).search(joined, ms.start()) if ms else None
        if not ms or not me:
            raise ValueError(f"{mid} : passage introuvable dans {s['accession']}/{s['file']}")
        unit = joined[ms.start():me.end()]
        a, b = bisect.bisect_right(offs, ms.start()) - 1, bisect.bisect_right(offs, me.end() - 1) - 1
        d = {"adsh": s["accession"], "form": s["form"], "file_type": s.get("file_type")}
        tier, assurance, status = evidence(d, spec)
        fd = s["filing_date"]
        out.append({"content_key": blocks.content_key(unit, []), "block_kind": "montage_text", "signal_class": 5,
                    "sort_key": f"mt:{mid}:{n:05d}", "group_id": groups_by_cik.get(cik) or ("CP:" + normalize_name(s["filer"])),
                    "cik": cik, "accession": s["accession"], "form": s["form"], "filing_date": fd, "acceptance": None,
                    "knowledge_date": fd, "period_start": None, "period_end": fd, "document": s["file"],
                    "locator": {"file": s["file"], "accession": s["accession"], "cik": cik, "byte_range": None},
                    "text": unit, "candidate_facts": [], "chars": len(unit),
                    "normalizer_version": config.NORMALIZER_VERSION, "delimiter_version": config.DELIMITER_VERSION,
                    "filing_status": status, "assurance_level": assurance, "tier": tier, "filer_name": s["filer"],
                    "exhibit_type": s.get("file_type"), "window": 0, "text_extraction": how,
                    "terms": sorted(set(noted_rx(spec).findall(unit))), "queries": [], "montage": mid,
                    "span": {"start": s["start"], "end": s["end"], "paragraphs": [a, b]}})
    return out


def priority_class(text, spec):
    """Classe d'une fenêtre pour un montage à `priority` (D-0064) : rang de la première expression qui la
    nomme ; les fenêtres qui n'en nomment aucune viennent après."""
    for i, rx in enumerate(spec.get("priority") or []):
        if re.search(rx, text):
            return i
    return len(spec.get("priority") or [])


def _order_key(d, k, spec, text=None):
    """Ordre de lecture : dates de dépôt croissantes (D-0046) ; pour un montage à `focus`, autres
    déposants, puis pièces de 8-K du déposant central, puis ses rapports périodiques, puis le reste,
    chaque classe du plus récent au plus ancien (D-0049, point 11). Un montage à `priority` range ses
    fenêtres par classe (priority_class), puis du plus récent au plus ancien (D-0064)."""
    neg = "".join(chr(0x10FFFF - ord(c)) for c in d["file_date"])   # plus récent d'abord
    if spec.get("priority"):
        return (priority_class(text or "", spec), neg, d["adsh"], d["file"], k)
    if spec.get("order") == "recent_first":                         # D-0058, point 3
        return (neg, d["adsh"], d["file"], k)
    if spec.get("order") == "party_first":                          # D-0067, point 3
        return (0 if d.get("party") else 1, neg, d["adsh"], d["file"], k)
    focus = spec.get("focus")
    if not focus:
        return (d["file_date"], d["adsh"], d["file"], k)
    own = (d["filer"] or "").lower()
    cls = 0 if focus not in own else 1 if d["form"] in ("8-K", "8-K/A") else 2 if d["form"] in ("10-Q", "10-K") else 3
    return (cls, neg, d["adsh"], d["file"], k)


def _prepare_one(mid, spec, groups_by_cik):
    if spec.get("source") == "tagged":          # paragraphes qui portent un fait balisé (D-0060, point 4)
        from . import labs
        return labs.prepare_units(mid, spec, groups_by_cik)
    if spec.get("source") == "span":            # passage fixé d'un document (D-0066, point 7)
        return span_blocks(mid, spec, groups_by_cik)
    from . import blocks
    from .graph import normalize_name
    _, docs_path, info_path = _paths(mid)
    if not docs_path.exists():
        return []
    docs = pd.read_parquet(docs_path)
    if spec.get("source") == "backlog":          # noms des clients de chaque vendeur (D-0068, point 6)
        from . import backlog
        client_names = backlog_names()
    units, no_window, excluded, risk, already = [], [], [], [], []
    read_by_acc = read_texts(mid) if spec.get("skip_read") else {}
    comp = spec.get("complement")                 # lecture complémentaire (D-0067, point 6) : "party" ou "all"
    block_text = {}
    if "source" in docs.columns and (docs["source"] == "block").any():
        from . import reader
        block_text = {b["content_key"]: (b["text"] if isinstance(b["text"], str) else "\n".join(b["text"]))
                      for b in reader.load_catalog()}
    for d in docs.to_dict("records"):
        if not d["state"].startswith(("cached", "fetched")):
            continue
        rule = _excluded(d, spec)
        if rule:
            excluded.append({"adsh": d["adsh"], "file": d["file"], "form": d["form"], "filer": d["filer"],
                             "reason": rule["reason"]})
            continue
        if d.get("source") == "block":            # note lue de la découverte : le texte du bloc (D-0067, point 4)
            text, how = block_text.get(d["block_key"]) or "", "block"
        else:
            raw = cache.read(cache.archive_path(d["cik"], d["adsh"], d["file"]))
            text, how = document_text(raw, spec)
        paras = paragraphs(text)
        if spec.get("source") == "backlog":      # un client du vendeur et un terme de carnet (D-0068, point 6)
            rx = backlog.qualifier(client_names.get(d["group_id"], ()), spec.get("vocabulary") or backlog.VOCAB)
        elif spec.get("source") == "edge_values":  # paragraphes qui portent une arête de valeur (D-0068, point 15)
            rx = quote_test(json.loads(d.get("quotes") or "[]"))
        elif spec.get("party_chars") or spec.get("require"):
            rx, d["party"] = qualifier(d, spec, text)
        else:
            rx = qualify_rx(d["filer"], spec)
        test = _test(rx)
        sp = windows(paras, rx, spec.get("window", WINDOW))
        if not sp:
            no_window.append({"adsh": d["adsh"], "file": d["file"], "form": d["form"], "filer": d["filer"],
                              **({"text_extraction": how} if how in ("pdf_unreadable", "pdf_no_text") else {})})
            continue
        rf = risk_factor_span(paras) if spec.get("skip_risk_factors") else None
        texts = read_by_acc.get(d["adsh"]) or []
        for k, (a, b) in enumerate(sp):
            hits = [i for i in range(a, b) if test(paras[i])]
            ref = {"adsh": d["adsh"], "file": d["file"], "form": d["form"], "filer": d["filer"], "window": k}
            if rf and all(rf[0] <= i < rf[1] for i in hits):        # facteur de risque (§14 ; D-0058, point 3)
                risk.append(ref)
                continue
            if texts and all(covered(paras[i], texts) for i in hits):   # déjà dans un bloc lu du même dépôt
                if comp == "all" or (comp == "party" and d.get("party")):
                    units.append((d, k, "\n".join(paras[a:b]), how, "complement"))
                    continue
                already.append(ref)
                continue
            units.append((d, k, "\n".join(paras[a:b]), how, "complete" if comp else None))
    units.sort(key=lambda u: _order_key(u[0], u[1], spec, u[2]))
    if spec.get("source") == "edge_values":
        # une fenêtre qui reprend tout son bloc lu en aurait la clé : une ligne en tête la nomme (D-0068, point 15)
        from . import reader
        known_keys = {b["content_key"] for b in reader.load_catalog() if b.get("montage") != mid}
        units = [(d, k, (f"[D-0068, point 15 : paragraphes du bloc {d['block_key'][:12]}]\n" + text)
                  if blocks.content_key(text, []) in known_keys else text, how, reading)
                 for d, k, text, how, reading in units]
    if spec.get("dedupe"):           # un texte distinct se lit une fois (D-0049, point 11)
        seen, kept, dup = set(), [], []
        # D-0067 : une fenêtre dont le texte est déjà un bloc d'un autre catalogue ou montage n'est pas servie ; ses
        # lignes sont celles de ce bloc, que le chargement rattache à un seul bloc par clé
        if comp:
            from . import reader
            elsewhere = {b["content_key"] for b in reader.load_catalog() if b.get("montage") != mid}
        else:
            elsewhere = set()
        for u in units:
            ck = blocks.content_key(u[2], [])
            if ck in seen or ck in elsewhere:
                dup.append({"adsh": u[0]["adsh"], "file": u[0]["file"], "window": u[1],
                            **({"elsewhere": True} if ck in elsewhere else {})})
                continue
            seen.add(ck)
            kept.append(u)
        units = kept
    else:
        dup = []
    noted = noted_rx(spec)
    out, over = [], []
    for n, (d, k, text, how, reading) in enumerate(units):
        if n >= spec["cap"]:
            over.append({"adsh": d["adsh"], "file": d["file"], "window": k})
            continue
        grp = groups_by_cik.get(d["cik"]) or ("CP:" + normalize_name(d["filer"]))
        tier, assurance, status = evidence(d, spec)
        fd = d["file_date"]
        out.append({"content_key": blocks.content_key(text, []), "block_kind": "montage_text", "signal_class": 5,
                    "sort_key": f"mt{n:05d}" if mid == FIRST else f"mt:{mid}:{n:05d}",
                    "group_id": grp, "cik": d["cik"], "accession": d["adsh"],
                    "form": d["form"], "filing_date": fd, "acceptance": None, "knowledge_date": fd,
                    "period_start": None, "period_end": fd, "document": d["file"],
                    "locator": {"file": d["file"], "accession": d["adsh"], "cik": d["cik"], "byte_range": None},
                    "text": text, "candidate_facts": [], "chars": len(text),
                    "normalizer_version": config.NORMALIZER_VERSION, "delimiter_version": config.DELIMITER_VERSION,
                    "filing_status": status, "assurance_level": assurance, "tier": tier, "filer_name": d["filer"],
                    "exhibit_type": d["file_type"], "window": k, "text_extraction": how,
                    "terms": sorted(set(noted.findall(text))), "queries": d["queries"], "montage": mid,
                    **({"reading": reading, "party": bool(d.get("party"))} if reading else {}),
                    **({"party_terms": d["party_terms"]} if reading and d.get("party") and d.get("party_terms") else {})})
    info = json.loads(info_path.read_text())
    info.update({"no_window": no_window, "over_cap": over, "units": len(units) + len(dup), "excluded": excluded,
                 "duplicates": dup, "risk_factors": risk, "already_read": already})
    info_path.write_text(json.dumps(info, ensure_ascii=False))
    print(mid, ":", len(units) + len(dup), "fenêtres ;", len(units), "textes distincts ;", len(out), "blocs ;",
          len(no_window), "pièces sans fenêtre ;", len(excluded), "pièces écartées ;", len(over), "au-delà du plafond",
          *([f"; {len(risk)} dans un facteur de risque ; {len(already)} déjà lues"]
            if spec.get("source") == "corpus" or spec.get("skip_risk_factors") or spec.get("skip_read") else []),
          *([f"; lecture complète {sum(1 for b in out if b.get('reading') == 'complete')}, complémentaire "
             f"{sum(1 for b in out if b.get('reading') == 'complement')}"] if comp else []))
    return out


def merge_catalog(existing, new, only):
    """Catalogue après la préparation d'un seul montage : les blocs des autres montages restent tels quels,
    dans leur ordre ; ceux du montage préparé sont remplacés."""
    return [b for b in existing if b.get("montage") != only] + list(new)


def prepare(only=None):
    """Blocs des fenêtres de chaque montage, dans l'ordre des dates de dépôt ; plafond par montage. Avec
    `only`, seul ce montage est préparé : les blocs déjà au catalogue pour les autres ne bougent pas."""
    p0 = json.loads((config.DB_DIR / "phase0.json").read_text())
    groups_by_cik = {str(cik).zfill(10): m["group"] for cik, m in p0["meta"].items()}
    out = []
    if only:
        existing = [json.loads(x) for x in open(CATALOG, encoding="utf-8")] if CATALOG.exists() else []
        out = merge_catalog(existing, _prepare_one(only, specs()[only], groups_by_cik), only)
    else:
        for mid, spec in specs().items():
            out += _prepare_one(mid, spec, groups_by_cik)
    tmp = CATALOG.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for b in out:
            fh.write(json.dumps(b, ensure_ascii=False) + "\n")
    tmp.replace(CATALOG)


def exclusions(as_of):
    """Relevés de portefeuille non lus, pièces sans fenêtre qualifiante, fenêtres au-delà du plafond."""
    out = []
    for mid, spec in specs().items():
        info_path = _paths(mid)[2]
        if not info_path.exists():
            continue
        info = json.loads(info_path.read_text())
        dec = spec.get("decision", "D-0046")
        pre = "montages" if mid == FIRST else f"montages:{mid}"

        def ex(key, reason, detail, acc=None):
            out.append({"exclusion_key": f"{reason}:{pre}:{key}", "item_kind": "document", "item_key": f"{pre}:{key}",
                        "reason": reason, "detail": detail, "group_id": None, "accession": acc, "content_key": None,
                        "as_of": as_of})
        terms = " », « ".join(t.get("label") or re.sub(r"\\b", "", t["rx"]) for t in spec.get("terms") or [])
        if spec.get("source") in ("corpus", "tagged", "lab_corpus", "backlog", "edge_values"):
            # montage de corpus (D-0058, point 3) : un document sans terme n'est pas une exclusion, ses blocs se lisent
            # par le catalogue du groupe ; une fenêtre d'un facteur de risque est hors champ (§14), et au-delà du
            # plafond, une fenêtre reste à lire
            pt = {"tagged": 4, "lab_corpus": 4, "backlog": 6, "edge_values": 15}.get(spec.get("source"), 3)   # D-0060, D-0058, D-0067, D-0068
            for d in info.get("risk_factors") or []:
                ex(f"{d['adsh']}/{d['file']}#{d['window']}", "out_of_scope",
                   f"{d['filer']} ({d['form']}) : fenêtre dans la section des facteurs de risque (§14 ; {dec}, point {pt})", d["adsh"])
            for d in info.get("over_cap") or []:
                ex(f"{d['adsh']}/{d['file']}#{d['window']}", "not_processed",
                   f"fenêtre au-delà du plafond de {spec['cap']} unités ({dec}, point {pt})", d["adsh"])
            continue
        for form, n in sorted((info.get("holdings_not_read") or {}).items()):
            ex(f"holdings:{form}", "out_of_scope",
               f"{n} résultat(s) de la recherche plein texte en {form} : relevés de portefeuille, non lus (D-0046, point 8)")
        for form, n in sorted((info.get("forms_not_read") or {}).items()):
            ex(f"forms:{form}", "out_of_scope",
               f"{n} résultat(s) de la recherche plein texte en {form} : formulaire d'un autre bloc (`form_d`), compté, non tiré ({dec})")
        for d in info.get("no_window") or []:
            if d.get("text_extraction"):          # PDF illisible ou sans texte : rien à chercher (D-0064)
                ex(f"{d['adsh']}/{d['file']}", "out_of_scope",
                   f"{d['filer']} ({d['form']}) : PDF sans texte extractible ({d['text_extraction']}), aucun paragraphe ({dec})",
                   d["adsh"])
                continue
            detail = ("aucun paragraphe ne nomme un terme qualifiant hors du nom du déposant "
                      "(« Beignet », « Richland Parish », « Meta », « Blue Owl » ; D-0046, points 8 et 9)") if mid == FIRST else \
                     f"aucun paragraphe ne nomme un terme qualifiant hors du nom du déposant (« {terms} » ; {dec})"
            ex(f"{d['adsh']}/{d['file']}", "out_of_scope", f"{d['filer']} ({d['form']}) : {detail}", d["adsh"])
        for d in info.get("excluded") or []:
            ex(f"{d['adsh']}/{d['file']}", "out_of_scope", f"{d['filer']} ({d['form']}) : {d['reason']} ({dec})", d["adsh"])
        for d in info.get("risk_factors") or []:      # §14 ; D-0058, point 20, que l'export omettait (D-0064)
            ex(f"{d['adsh']}/{d['file']}#{d['window']}", "out_of_scope",
               f"{d['filer']} ({d['form']}) : fenêtre dans la section des facteurs de risque (§14 ; {dec})", d["adsh"])
        # déposant devenu groupe suivi (D-0053, point 7) : ses dépôts se lisent par le catalogue du groupe
        docs_path = _paths(mid)[1]
        filer_cik = {}
        if docs_path.exists() and info.get("over_cap"):
            docs = pd.read_parquet(docs_path, columns=["adsh", "cik"])
            filer_cik = {a: str(int(c)) for a, c in zip(docs["adsh"], docs["cik"]) if str(c).strip().isdigit()}
        from .load import config_group_ciks
        as_group = config_group_ciks()
        for d in info.get("over_cap") or []:
            grp = as_group.get(filer_cik.get(d["adsh"], ""))
            if grp:
                ex(f"{d['adsh']}/{d['file']}#{d['window']}", "out_of_scope",
                   f"fenêtre au-delà du plafond de {spec['cap']} unités, dépôt du groupe {grp} lu par son catalogue (D-0053, point 7)",
                   d["adsh"])
                continue
            ex(f"{d['adsh']}/{d['file']}#{d['window']}", "not_processed",
               f"fenêtre au-delà du plafond de {spec['cap']} unités ({'D-0046, point 4' if mid == FIRST else dec})", d["adsh"])
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "search":
        search(sys.argv[2])
    elif cmd == "fetch":
        fetch(sys.argv[2])
    elif cmd == "corpus":
        corpus(sys.argv[2])
    elif cmd == "replay":
        replay(sys.argv[2])
    elif cmd == "lab_corpus":
        lab_corpus(sys.argv[2])
    elif cmd == "backlog_corpus":
        backlog_corpus(sys.argv[2])
    elif cmd == "values_corpus":
        values_corpus(sys.argv[2])
    elif cmd == "prepare":
        prepare(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "retier":
        for k, n in sorted(retier().items()):
            print(*k, n)
    else:
        print(__doc__)
