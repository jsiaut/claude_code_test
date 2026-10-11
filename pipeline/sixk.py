"""Unités 6-K des groupes émetteurs privés étrangers (D-0048, point 6).

Un 6-K n'a pas d'items. Ses unités sont les paragraphes du document principal et des annexes 99
qui nomment un terme du lexique de `config.yaml` (`foreign_6k`), avec deux paragraphes de part et
d'autre, fondus quand ils se chevauchent (règle de D-0046) ; bloc `foreign_6k_text`. Un terme se
lit en mot entier, sans égard à la casse, sous les formes que `config.yaml` écrit (singulier et
pluriel) ; un nom de groupe ou de laboratoire suit la casse du lexique de la découverte, et
jamais le nom du déposant lui-même (D-0046, point 9). Plafond par groupe, du plus récent au plus ancien ; au-delà, `not_processed`.
Un 6-K est furnished (niveau E), sauf mention expresse d'incorporation par référence dans un
document d'enregistrement, lue dans le 6-K lui-même (D-0042) : niveau C.

    python -m pipeline.sixk fetch      # en-têtes SGML, documents principaux et annexes 99 en cache
    python -m pipeline.sixk prepare    # fenêtres -> db/foreign_6k_blocks.jsonl
"""
import json
import re
import sys

import pandas as pd

from . import blocks, cache, config, edgar, net
from . import discovery as D
from .catalog import _filing
from .edgar import cik10
from .foreign import INCORP

CATALOG = config.DB_DIR / "foreign_6k_blocks.jsonl"
DOCS = config.DB_DIR / "foreign_6k_docs.parquet"
INFO = config.DB_DIR / "foreign_6k_info.json"
TEXT_EXT = re.compile(r"\.(htm|html|txt)$", re.I)


def settings(cfg=None):
    return (cfg or config.load()).get("foreign_6k") or {}


def lexicon_rx(group, cfg=None):
    """Lexique d'un groupe : termes de D-0048 (singulier ou pluriel, casse indifférente), noms des
    groupes et des laboratoires (casse du lexique de la découverte), sauf ceux du groupe lui-même."""
    cfg = cfg or config.load()
    s = settings(cfg)
    parts = [r"\b" + r"\s+".join(re.escape(w) for w in t.split()) + r"\b" for t in s.get("lexicon") or []]
    names = list(((cfg.get("discovery") or {}).get("lexicon") or {}).get("seed") or []) + list(s.get("group_names") or [])
    named = []
    for n in names:
        if n.get("ref") == group:
            continue
        rx = r"\b" + re.escape(n["term"]) + r"\b"
        named.append(rx if n.get("case_sensitive") else "(?i:" + rx + ")")
    return re.compile("(?i:" + "|".join(parts) + ")" + ("|" + "|".join(named) if named else ""))


def filings(cfg=None):
    """6-K des groupes de `foreign_6k`, dans la période de lecture, hors ruptures d'historique."""
    cfg = cfg or config.load()
    s = settings(cfg)
    inv = pd.read_parquet(config.DB_DIR / "inventory.parquet")
    k = inv[inv["group_id"].isin(s.get("groups") or []) & inv["form"].isin(s.get("forms") or [])
            & (inv["inv_class"] != "pre_combination")]
    return k.sort_values(["acceptanceDateTime", "accessionNumber"], ascending=False)


def fetch(rate=4.0):
    """En-tête SGML de chaque 6-K (types des pièces, §2.3), puis son document principal et ses
    annexes 99 au format texte ; une pièce déjà en cache ne se tire pas."""
    cfg = config.load()
    client = net.SecClient(D.AS_OF, cfg)
    client.min_interval = 1.0 / rate
    ed = edgar.Edgar(client, D.AS_OF)
    rows = []
    for r in filings(cfg).to_dict("records"):
        cik, acc = cik10(r["filer_cik"]), r["accessionNumber"]
        try:
            docs = ed.sgml_documents(cik, acc)["documents"]
        except net.NotCollected as exc:
            rows.append({"group_id": r["group_id"], "cik": cik, "adsh": acc, "file": None, "type": None,
                         "description": None, "seq": None, "state": f"not_collected: {exc}"})
            continue
        for i, d in enumerate(docs):
            t = (d.get("TYPE") or "").upper().strip()
            if not (t.startswith("6-K") or t.startswith("EX-99")):
                continue
            name = d.get("FILENAME") or ""
            state = "cached" if ed.archive_cached(cik, acc, name) else "fetched"
            if not TEXT_EXT.search(name):
                state = "not_text"
            elif state == "fetched":
                try:
                    ed.archive(cik, acc, name)
                except net.NotCollected as exc:
                    state = f"not_collected: {exc}"
            rows.append({"group_id": r["group_id"], "cik": cik, "adsh": acc, "file": name, "type": t,
                         "description": d.get("DESCRIPTION"), "seq": i, "state": state})
    pd.DataFrame(rows).to_parquet(DOCS, index=False)
    INFO.write_text(json.dumps({"requests": client.stats}))
    print(len(rows), "pièces ;", sum(x["state"] == "fetched" for x in rows), "tirées ;",
          sum(x["state"] == "not_text" for x in rows), "hors texte ;", client.stats)


def paragraphs(text):
    return [p for p in (x.strip() for x in text.split("\n")) if p]


def windows(paras, rx, width=2):
    """Paragraphes qui nomment un terme, `width` avant et après, fondus quand ils se chevauchent."""
    spans = []
    for i, p in enumerate(paras):
        if not rx.search(p):
            continue
        a, b = max(0, i - width), min(len(paras), i + width + 1)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    return spans


def incorporation(texts):
    """Mention expresse d'incorporation par référence dans un document d'enregistrement (§2.1)."""
    for name, text in texts:
        flat = re.sub(r"\s+", " ", text)
        m = INCORP.search(flat)
        if m:
            s = flat.rfind(".", 0, m.start()) + 1
            e = flat.find(".", m.end())
            return True, flat[s:e + 1 if e > 0 else m.end() + 200].strip()[:600], name
    return False, None, None


def prepare():
    """Blocs des fenêtres, du 6-K le plus récent au plus ancien ; plafond par groupe."""
    cfg = config.load()
    s = settings(cfg)
    cap, width = int(s.get("cap_per_group") or 80), int(s.get("window") or 2)
    inv = {r["accessionNumber"]: r for r in filings(cfg).to_dict("records")}
    docs = pd.read_parquet(DOCS)
    out, over, no_window, not_text = [], [], [], []
    n_by = {}
    for acc, r in inv.items():
        g = r["group_id"]
        rx = lexicon_rx(g, cfg)
        f = _filing(r)
        dd = docs[(docs["adsh"] == acc)].sort_values("seq").to_dict("records")
        texts = []
        for d in dd:
            if d["state"] == "not_text":
                not_text.append({"adsh": acc, "file": d["file"], "type": d["type"], "group_id": g})
                continue
            if not str(d["state"]).startswith(("cached", "fetched")):
                continue
            text, how = D.plain_text(cache.read(cache.archive_path(d["cik"], acc, d["file"])))
            texts.append((d["file"], text, how, d))
        inc, quote, inc_doc = incorporation([(n, t) for n, t, _, _ in texts])
        units = []
        for name, text, how, d in texts:
            paras = paragraphs(text)
            for k, (a, b) in enumerate(windows(paras, rx, width)):
                units.append((d, k, "\n".join(paras[a:b]), how))
        if not units:
            no_window.append({"adsh": acc, "group_id": g, "documents": [n for n, _, _, _ in texts]})
        for d, k, text, how in units:
            n = n_by.get(g, 0)
            n_by[g] = n + 1
            if n >= cap:
                over.append({"adsh": acc, "file": d["file"], "window": k, "group_id": g})
                continue
            b = blocks._block("foreign_6k_text", f, text, [], d["file"], None, exhibit_type=d["type"],
                              sgml_description=d["description"], window=k, text_extraction=how,
                              terms=sorted({m.group(0) for m in rx.finditer(text)}))
            b["signal_class"] = 3
            b["sort_key"] = f"{b['sort_key']}:{int(d['seq']):03d}:{k:03d}"
            b["filing_status"], b["assurance_level"], b["tier"] = "furnished", "not_applicable", "E"
            b["incorporated_by_reference"], b["incorporation_quote"], b["incorporation_document"] = inc, quote, inc_doc
            if inc:
                # admissible : exposé à la Section 11 par l'incorporation (§2.1, D-0042)
                b["filing_status"], b["assurance_level"], b["tier"] = "filed", "unaudited", "C"
            out.append(b)
    tmp = CATALOG.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for b in out:
            fh.write(json.dumps(b, ensure_ascii=False, default=str) + "\n")
    tmp.replace(CATALOG)
    info = json.loads(INFO.read_text()) if INFO.exists() else {}
    info.update({"filings": len(inv), "blocks": len(out), "units_by_group": n_by, "no_window": no_window,
                 "over_cap": over, "not_text": not_text})
    INFO.write_text(json.dumps(info, ensure_ascii=False))
    print(len(inv), "6-K ;", n_by, "fenêtres ;", len(out), "blocs ;", len(no_window), "6-K sans fenêtre ;",
          len(over), "au-delà du plafond ;", len(not_text), "pièces hors texte")


def exclusions(as_of):
    """6-K sans fenêtre, pièces hors texte, fenêtres au-delà du plafond (D-0048, point 6)."""
    if not INFO.exists():
        return []
    info = json.loads(INFO.read_text())
    out = []

    def ex(key, reason, detail, group, acc):
        out.append({"exclusion_key": f"{reason}:foreign_6k:{key}", "item_kind": "document", "item_key": f"foreign_6k:{key}",
                    "reason": reason, "detail": detail, "group_id": group, "accession": acc, "content_key": None,
                    "as_of": as_of})
    for d in info.get("no_window") or []:
        ex(d["adsh"], "out_of_scope", "6-K dont aucun paragraphe ne nomme un terme du lexique (D-0048, point 6)",
           d["group_id"], d["adsh"])
    for d in info.get("not_text") or []:
        ex(f"{d['adsh']}/{d['file']}", "out_of_scope",
           f"{d['type']} {d['file']} : pièce hors texte (image ou PDF), non lue (D-0048, point 6)", d["group_id"], d["adsh"])
    for d in info.get("over_cap") or []:
        ex(f"{d['adsh']}/{d['file']}#{d['window']}", "not_processed",
           "fenêtre 6-K au-delà du plafond de 80 unités par groupe (D-0048, point 6)", d["group_id"], d["adsh"])
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "prepare":
        prepare()
    else:
        print(__doc__)
