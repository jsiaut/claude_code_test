"""Bloc `montages` (D-0046) : nommer le financeur d'un montage que les notes d'un groupe décrivent
sans le nommer (« the Venture » de Meta en Louisiane), par les pièces qui le décrivent.

Sources : la recherche plein texte d'EDGAR (requêtes fixées par D-0046, point 3) et les rapports
périodiques de Blue Owl Capital Inc. de la période. Unités : les paragraphes qui nomment un terme
du lexique, avec deux paragraphes avant et après (D-0046, points 4 et 8). Chaque pièce se tire une
fois, en cache, par le client SEC journalisé.

    python -m pipeline.montages fetch      # pièces en cache, résultats de la recherche
    python -m pipeline.montages prepare    # fenêtres -> db/montages_blocks.jsonl
"""
import datetime as dt
import json
import re
import sys

import pandas as pd

from . import cache, config, net
from . import discovery as D

HITS = config.ROOT / "work" / "tmp" / "montages_hits.json"
DOCS = config.DB_DIR / "montages_docs.parquet"
CATALOG = config.DB_DIR / "montages_blocks.jsonl"
INFO = config.DB_DIR / "montages_info.json"
OWL_CIK = "0001823945"
START, END = "2025-10-01", "2026-10-07"
HOLDINGS_FORMS = {"NPORT-P", "NPORT-P/A", "NT NPORT-P", "N-CSR", "N-CSR/A", "N-CSRS", "N-MFP3", "13F-HR", "13F-HR/A",
                  "N-PX", "N-PX/A", "486BPOS", "POS EX", "11-K"}
QUALIFY = re.compile(r"\bBeignet\b|Richland Parish|\bMeta\b")


def qualify_rx(filer):
    """Termes qualifiants d'une pièce : jamais le nom de son déposant (D-0046, point 9)."""
    t = [r"\bBeignet\b", r"Richland Parish"]
    own = (filer or "").lower()
    if not own.startswith("meta platforms"):
        t.append(r"\bMeta\b")
    if "blue owl" not in own:
        t.append(r"\bBlue Owl\b")
    return re.compile("|".join(t))
TERMS = re.compile(r"\bBeignet\b|Richland Parish|\bMeta\b|\bHyperion\b|\bBlue Owl\b")
CAP = 40
WINDOW = 2


def _client(rate=4.0):
    c = net.SecClient(D.AS_OF, config.load())
    c.min_interval = 1.0 / rate
    return c


def owl_periodic(client):
    """Rapports périodiques de Blue Owl Capital Inc. déposés dans la période (D-0046, point 3)."""
    url = f"https://data.sec.gov/submissions/CIK{OWL_CIK}.json"
    p = config.CACHE / "edgar" / "submissions" / f"CIK{OWL_CIK}.json.zst"
    if p.exists():
        sub = json.loads(cache.read(p))
    else:
        raw, _ = client.get(url)
        cache.write(p, raw)
        sub = json.loads(raw)
    r = sub["filings"]["recent"]
    out = []
    for form, acc, date, doc in zip(r["form"], r["accessionNumber"], r["filingDate"], r["primaryDocument"]):
        if form in ("10-Q", "10-K") and START <= date <= END:
            out.append({"adsh": acc, "file": doc, "form": form, "file_type": form, "file_date": date,
                        "cik": OWL_CIK, "filer": sub["name"], "source": "owl_periodic"})
    return out, sub["name"]


def fetch(rate=4.0):
    """Pièces narratives des résultats et rapports de Blue Owl Capital Inc. ; les relevés de
    portefeuille sont comptés, pas tirés (D-0046, point 8)."""
    client = _client(rate)
    hits = json.loads(HITS.read_text())
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
    owl, owl_name = owl_periodic(client)
    for d in owl:
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
    pd.DataFrame(rows).to_parquet(DOCS, index=False)
    INFO.write_text(json.dumps({"holdings_not_read": holdings, "owl_name": owl_name, "requests": client.stats}))
    print(len(rows), "pièces ;", sum(r["state"] == "fetched" for r in rows), "tirées ; relevés écartés", holdings)


def paragraphs(text):
    return [p for p in (x.strip() for x in text.split("\n")) if p]


def windows(paras, rx=QUALIFY):
    """Fenêtres de lecture : paragraphes qui nomment un terme qualifiant, deux avant, deux après,
    fondues quand elles se chevauchent (D-0046, points 4, 8 et 9)."""
    hits = [i for i, p in enumerate(paras) if rx.search(p)]
    spans = []
    for i in hits:
        a, b = max(0, i - WINDOW), min(len(paras), i + WINDOW + 1)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    return spans


def prepare():
    """Blocs des fenêtres, dans l'ordre des dates de dépôt ; plafond de 40 unités."""
    from . import blocks
    from .graph import normalize_name
    cfg = config.load()
    groups_by_cik = {}
    p0 = json.loads((config.DB_DIR / "phase0.json").read_text())
    for cik, m in p0["meta"].items():
        groups_by_cik[str(cik).zfill(10)] = m["group"]
    docs = pd.read_parquet(DOCS)
    units, no_window = [], []
    for d in docs.to_dict("records"):
        if not d["state"].startswith(("cached", "fetched")):
            continue
        raw = cache.read(cache.archive_path(d["cik"], d["adsh"], d["file"]))
        text, how = D.plain_text(raw)
        paras = paragraphs(text)
        sp = windows(paras, qualify_rx(d["filer"]))
        if not sp:
            no_window.append({"adsh": d["adsh"], "file": d["file"], "form": d["form"], "filer": d["filer"]})
            continue
        for k, (a, b) in enumerate(sp):
            units.append((d, k, "\n".join(paras[a:b]), how))
    units.sort(key=lambda u: (u[0]["file_date"], u[0]["adsh"], u[0]["file"], u[1]))
    out, over = [], []
    for n, (d, k, text, how) in enumerate(units):
        if n >= CAP:
            over.append({"adsh": d["adsh"], "file": d["file"], "window": k})
            continue
        grp = groups_by_cik.get(d["cik"]) or ("CP:" + normalize_name(d["filer"]))
        tier, assurance, status = D.form_evidence(d["form"], None)
        fd = d["file_date"]
        out.append({"content_key": blocks.content_key(text, []), "block_kind": "montage_text", "signal_class": 5,
                    "sort_key": f"mt{n:05d}", "group_id": grp, "cik": d["cik"], "accession": d["adsh"],
                    "form": d["form"], "filing_date": fd, "acceptance": None, "knowledge_date": fd,
                    "period_start": None, "period_end": fd, "document": d["file"],
                    "locator": {"file": d["file"], "accession": d["adsh"], "cik": d["cik"], "byte_range": None},
                    "text": text, "candidate_facts": [], "chars": len(text),
                    "normalizer_version": config.NORMALIZER_VERSION, "delimiter_version": config.DELIMITER_VERSION,
                    "filing_status": status, "assurance_level": assurance, "tier": tier, "filer_name": d["filer"],
                    "exhibit_type": d["file_type"], "window": k, "text_extraction": how,
                    "terms": sorted(set(TERMS.findall(text))), "queries": d["queries"]})
    with open(CATALOG, "w", encoding="utf-8") as fh:
        for b in out:
            fh.write(json.dumps(b, ensure_ascii=False) + "\n")
    info = json.loads(INFO.read_text())
    info.update({"no_window": no_window, "over_cap": over, "units": len(units)})
    INFO.write_text(json.dumps(info, ensure_ascii=False))
    print(len(units), "fenêtres ;", len(out), "blocs ;", len(no_window), "pièces sans fenêtre ;", len(over), "au-delà du plafond")


def exclusions(as_of):
    """Relevés de portefeuille non lus, pièces sans fenêtre qualifiante, fenêtres au-delà du plafond."""
    if not INFO.exists():
        return []
    info = json.loads(INFO.read_text())
    out = []

    def ex(key, reason, detail, acc=None):
        out.append({"exclusion_key": f"{reason}:montages:{key}", "item_kind": "document", "item_key": f"montages:{key}",
                    "reason": reason, "detail": detail, "group_id": None, "accession": acc, "content_key": None,
                    "as_of": as_of})
    for form, n in sorted((info.get("holdings_not_read") or {}).items()):
        ex(f"holdings:{form}", "out_of_scope",
           f"{n} résultat(s) de la recherche plein texte en {form} : relevés de portefeuille, non lus (D-0046, point 8)")
    for d in info.get("no_window") or []:
        ex(f"{d['adsh']}/{d['file']}", "out_of_scope",
           f"{d['filer']} ({d['form']}) : aucun paragraphe ne nomme un terme qualifiant hors du nom du déposant "
           "(« Beignet », « Richland Parish », « Meta », « Blue Owl » ; D-0046, points 8 et 9)", d["adsh"])
    for d in info.get("over_cap") or []:
        ex(f"{d['adsh']}/{d['file']}#{d['window']}", "not_processed",
           "fenêtre au-delà du plafond de 40 unités (D-0046, point 4)", d["adsh"])
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "prepare":
        prepare()
    else:
        print(__doc__)
