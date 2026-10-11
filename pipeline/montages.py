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
    python -m pipeline.montages prepare             # fenêtres de tous les montages -> db/montages_blocks.jsonl
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
    own = (filer or "").lower()
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
    c = net.SecClient(D.AS_OF, config.load())
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
                            "names": s.get("display_names"), "ciks": s.get("ciks")})
        totals.append({"query": qd["q"], "cik_filter": qd.get("cik"), "total": n, "relation": tot.get("relation"),
                       "url": url})
        D._log_query({"montage": mid, "query": qd["q"], "cik": qd.get("cik"), "start": start, "end": end,
                      "total": n, "status": "complete"}, config.WORK / "montages" / "efts_queries.jsonl")
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
    docs, holdings = {}, {}
    for h in hits:
        if h["form"] in HOLDINGS_FORMS:
            holdings[h["form"]] = holdings.get(h["form"], 0) + 1
            continue
        if not h.get("file"):
            continue
        cik = str((h.get("ciks") or [""])[0]).zfill(10)
        name = re.sub(r"\s+\(.*$", "", (h.get("names") or [""])[0]).strip()
        docs.setdefault((h["adsh"], h["file"]), {"adsh": h["adsh"], "file": h["file"], "form": h["form"],
                                                 "file_type": h["file_type"], "file_date": h["file_date"],
                                                 "cik": cik, "filer": name, "source": "efts", "queries": set()})
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
    if mid == FIRST:
        info["owl_name"] = names.get(str(spec["periodic"][0]).zfill(10))
    else:
        info["periodic_names"] = names
    info_path.write_text(json.dumps(info))
    print(len(rows), "pièces ;", sum(r["state"] == "fetched" for r in rows), "tirées ; relevés écartés", holdings)


def paragraphs(text):
    return [p for p in (x.strip() for x in text.split("\n")) if p]


def windows(paras, rx):
    """Fenêtres de lecture : paragraphes qui nomment un terme qualifiant, deux avant, deux après,
    fondues quand elles se chevauchent (D-0046, points 4, 8 et 9)."""
    hits = [i for i, p in enumerate(paras) if rx is not None and rx.search(p)]
    spans = []
    for i in hits:
        a, b = max(0, i - WINDOW), min(len(paras), i + WINDOW + 1)
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


def _order_key(d, k, spec):
    """Ordre de lecture : dates de dépôt croissantes (D-0046) ; pour un montage à `focus`, autres
    déposants, puis pièces de 8-K du déposant central, puis ses rapports périodiques, puis le reste,
    chaque classe du plus récent au plus ancien (D-0049, point 11)."""
    focus = spec.get("focus")
    if not focus:
        return (d["file_date"], d["adsh"], d["file"], k)
    own = (d["filer"] or "").lower()
    cls = 0 if focus not in own else 1 if d["form"] in ("8-K", "8-K/A") else 2 if d["form"] in ("10-Q", "10-K") else 3
    neg = "".join(chr(0x10FFFF - ord(c)) for c in d["file_date"])   # plus récent d'abord
    return (cls, neg, d["adsh"], d["file"], k)


def _prepare_one(mid, spec, groups_by_cik):
    from . import blocks
    from .graph import normalize_name
    _, docs_path, info_path = _paths(mid)
    if not docs_path.exists():
        return []
    docs = pd.read_parquet(docs_path)
    units, no_window, excluded = [], [], []
    for d in docs.to_dict("records"):
        if not d["state"].startswith(("cached", "fetched")):
            continue
        rule = _excluded(d, spec)
        if rule:
            excluded.append({"adsh": d["adsh"], "file": d["file"], "form": d["form"], "filer": d["filer"],
                             "reason": rule["reason"]})
            continue
        raw = cache.read(cache.archive_path(d["cik"], d["adsh"], d["file"]))
        text, how = D.plain_text(raw)
        paras = paragraphs(text)
        sp = windows(paras, qualify_rx(d["filer"], spec))
        if not sp:
            no_window.append({"adsh": d["adsh"], "file": d["file"], "form": d["form"], "filer": d["filer"]})
            continue
        for k, (a, b) in enumerate(sp):
            units.append((d, k, "\n".join(paras[a:b]), how))
    units.sort(key=lambda u: _order_key(u[0], u[1], spec))
    if spec.get("dedupe"):           # un texte distinct se lit une fois (D-0049, point 11)
        seen, kept, dup = set(), [], []
        for u in units:
            ck = blocks.content_key(u[2], [])
            if ck in seen:
                dup.append({"adsh": u[0]["adsh"], "file": u[0]["file"], "window": u[1]})
                continue
            seen.add(ck)
            kept.append(u)
        units = kept
    else:
        dup = []
    noted = noted_rx(spec)
    out, over = [], []
    for n, (d, k, text, how) in enumerate(units):
        if n >= spec["cap"]:
            over.append({"adsh": d["adsh"], "file": d["file"], "window": k})
            continue
        grp = groups_by_cik.get(d["cik"]) or ("CP:" + normalize_name(d["filer"]))
        tier, assurance, status = D.form_evidence(d["form"], None)
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
                    "terms": sorted(set(noted.findall(text))), "queries": d["queries"], "montage": mid})
    info = json.loads(info_path.read_text())
    info.update({"no_window": no_window, "over_cap": over, "units": len(units) + len(dup), "excluded": excluded,
                 "duplicates": dup})
    info_path.write_text(json.dumps(info, ensure_ascii=False))
    print(mid, ":", len(units) + len(dup), "fenêtres ;", len(units), "textes distincts ;", len(out), "blocs ;",
          len(no_window), "pièces sans fenêtre ;", len(excluded), "pièces écartées ;", len(over), "au-delà du plafond")
    return out


def prepare():
    """Blocs des fenêtres de chaque montage, dans l'ordre des dates de dépôt ; plafond par montage."""
    p0 = json.loads((config.DB_DIR / "phase0.json").read_text())
    groups_by_cik = {str(cik).zfill(10): m["group"] for cik, m in p0["meta"].items()}
    out = []
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
        terms = " », « ".join(re.sub(r"\\b", "", t["rx"]) for t in spec["terms"])
        for form, n in sorted((info.get("holdings_not_read") or {}).items()):
            ex(f"holdings:{form}", "out_of_scope",
               f"{n} résultat(s) de la recherche plein texte en {form} : relevés de portefeuille, non lus (D-0046, point 8)")
        for d in info.get("no_window") or []:
            detail = ("aucun paragraphe ne nomme un terme qualifiant hors du nom du déposant "
                      "(« Beignet », « Richland Parish », « Meta », « Blue Owl » ; D-0046, points 8 et 9)") if mid == FIRST else \
                     f"aucun paragraphe ne nomme un terme qualifiant hors du nom du déposant (« {terms} » ; {dec})"
            ex(f"{d['adsh']}/{d['file']}", "out_of_scope", f"{d['filer']} ({d['form']}) : {detail}", d["adsh"])
        for d in info.get("excluded") or []:
            ex(f"{d['adsh']}/{d['file']}", "out_of_scope", f"{d['filer']} ({d['form']}) : {d['reason']} ({dec})", d["adsh"])
        for d in info.get("over_cap") or []:
            ex(f"{d['adsh']}/{d['file']}#{d['window']}", "not_processed",
               f"fenêtre au-delà du plafond de {spec['cap']} unités ({'D-0046, point 4' if mid == FIRST else dec})", d["adsh"])
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "search":
        search(sys.argv[2])
    elif cmd == "fetch":
        fetch(sys.argv[2])
    elif cmd == "prepare":
        prepare()
    else:
        print(__doc__)
