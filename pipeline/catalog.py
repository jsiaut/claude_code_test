"""Catalogue des blocs de la tranche à fort signal (§11.1, phase 2), recalculé à chaque
exécution depuis le cache. Écrit db/blocks.jsonl, que le lecteur sert dans l'ordre du signal."""
import io
import json
import re
import zipfile
from collections import defaultdict

import pandas as pd

from . import blocks, cache, config, sections, textnorm, xbrl
from .edgar import cik10

EX10 = re.compile(r"^EX-10(\.\d+[A-Z]?)?$", re.I)
EX4 = re.compile(r"^EX-4(\.\d+[A-Z]?)?$", re.I)
FIRST_PASS_ITEMS = {"1.01": "item_8k_101", "1.02": "item_8k_102", "3.03": "item_8k_303", "8.01": "item_8k_801"}


def _cache_member(cik, acc, name, zip_bytes):
    """Écrit dans le cache un document extrait de l'archive -xbrl.zip (même octets que sur EDGAR)."""
    p = cache.archive_path(cik10(cik), acc, name)
    if p.exists():
        return cache.read(p)
    if zip_bytes is None:
        return None
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        if name not in zf.namelist():
            return None
        data = zf.read(name)
    cache.write(p, data)
    return data


def _filing(r, form=None):
    return {"group_id": r["group_id"], "cik": r["filer_cik"] if "filer_cik" in r else r["cik"],
            "accession": r["accessionNumber"] if "accessionNumber" in r else r["accession"],
            "form": form or r["form"], "filing_date": str(r.get("filingDate") or r.get("filing_date"))[:10],
            "acceptance": r.get("acceptanceDateTime") or r.get("acceptance"),
            "report_date": str(r.get("reportDate") or r.get("report_date") or "")[:10] or None}


def evidence_attrs(kind, form):
    """filing_status, assurance, tier d'un bloc (§2.2)."""
    if kind in ("related_party_note", "going_concern", "spacex_annual_note"):
        if form.startswith("10-K") or form == "424B4":
            return "filed", "audited", "A"
        return "filed", "reviewed", "B"
    if kind in ("exhibit_header", "exhibit_body"):
        return "filed", "not_applicable", "D"
    return "filed", "not_applicable", "C"


def build(as_of):
    out = []
    stats = defaultdict(int)
    inv = pd.read_parquet(config.DB_DIR / "inventory.parquet")
    xd = pd.read_parquet(config.DB_DIR / "xbrl_documents.parquet").set_index("accession")
    facts = pd.read_parquet(config.DB_DIR / "facts_instances.parquet",
                            columns=["fact_key", "accession", "concept", "value", "unit", "period_start",
                                     "period_end", "dims", "decimals"])
    facts = facts[facts["value"].notna()]
    facts_by = dict(tuple(facts.groupby("accession")))
    labels = pd.read_parquet(config.DB_DIR / "labels.parquet")
    labels = labels[labels["label_role"].isin(["label", "terseLabel"])]
    lab_by = {a: dict(zip(g["concept"], g["label"])) for a, g in labels.groupby("accession")}
    tags = pd.read_parquet(config.DB_DIR / "tags.parquet", columns=["accession", "concept", "xbrltype"])
    tb_by = {a: set(g[g["xbrltype"].fillna("").str.endswith("textBlockItemType")]["concept"])
             for a, g in tags.groupby("accession")}

    # 1. rapports périodiques : notes balisées, Item 9A, Item 4
    per = inv[inv["inv_class"] == "periodic"]
    for r in per.to_dict("records"):
        acc = r["accessionNumber"]
        if acc not in xd.index:
            stats["periodic_without_xbrl"] += 1
            continue
        d = xd.loc[acc]
        cik = r["filer_cik"]
        zb = cache.read(cache.archive_path(cik10(cik), acc, d["zip"])) if d["zip"] else None
        files = {}
        if zb:
            with zipfile.ZipFile(io.BytesIO(zb)) as zf:
                for n in zf.namelist():
                    if n.lower().endswith((".xsd", ".xml")):
                        files[n] = zf.read(n)
        inst = d["instance"]
        data = _cache_member(cik, acc, inst, zb)
        if data is None:
            p = cache.archive_path(cik10(cik), acc, inst)
            data = cache.read(p) if p.exists() else None
        if data is None:
            stats["instance_missing"] += 1
            continue
        files[inst] = data
        f = _filing(r)
        frows = facts_by.get(acc, pd.DataFrame()).to_dict("records")
        labs = lab_by.get(acc, {})
        tbc = tb_by.get(acc) or None
        try:
            bl = blocks.instance_blocks(f, files, inst, tbc, frows, labs)
        except Exception as exc:  # parse_failed : l'élément est écarté avec son motif
            stats["instance_blocks_failed"] += 1
            bl = []
        if not any(b["block_kind"] == "going_concern" for b in bl):
            gc = blocks.going_concern_fallback(f, files, inst, tbc)
            if gc:
                bl.append(gc)
            else:
                stats["going_concern_none_found"] += 1
        for b in bl:
            b["filing_status"], b["assurance_level"], b["tier"] = evidence_attrs(b["block_kind"], f["form"])
            out.append(b)
        # Item 9A (10-K) et Item 4 de la partie I (10-Q), délimités par leur titre
        prim = r["primaryDocument"]
        raw = _cache_member(cik, acc, prim, zb)
        if raw is None:
            stats["primary_missing"] += 1
            continue
        kind = "item_9a" if r["form"].startswith("10-K") else "item_4_10q"
        text = sections.item_9a(raw) if kind == "item_9a" else sections.item_4_10q(raw)
        if not text:
            stats[f"{kind}_not_found"] += 1
            continue
        b = blocks._block(kind, f, text, [], prim, None, item="9A" if kind == "item_9a" else "4")
        b["filing_status"], b["assurance_level"], b["tier"] = evidence_attrs(kind, f["form"])
        out.append(b)

    # 2. DEF 14A : Item 404
    idx = json.loads((config.DB_DIR / "filing_index.json").read_text())
    for r in idx:
        if r["inv_class"] != "proxy":
            continue
        raw = cache.read(cache.archive_path(r["cik"], r["accession"], r["primary"]))
        text = sections.item_404(raw)
        f = _filing(r)
        if not text:
            stats["item_404_not_found"] += 1
            continue
        b = blocks._block("item_404", f, text, [], r["primary"], None, item="404")
        b["filing_status"], b["assurance_level"], b["tier"] = evidence_attrs("item_404", f["form"])
        out.append(b)

    # 3. 424B4 des introductions récentes : Item 404 et note de parties liées des états annuels
    for r in idx:
        if r["inv_class"] != "ipo" or r["form"] != "424B4":
            continue
        raw = cache.read(cache.archive_path(r["cik"], r["accession"], r["primary"]))
        f = _filing(r)
        text = sections.item_404(raw, max_chars=120000)
        if text:
            b = blocks._block("item_404", f, text, [], r["primary"], None, item="404")
            b["filing_status"], b["assurance_level"], b["tier"] = evidence_attrs("item_404", "424B4")
            out.append(b)
        note = related_party_note_html(raw)
        if note:
            b = blocks._block("related_party_note", f, note, [], r["primary"], None,
                              note_label="note de parties liées des états annuels audités (424B4)")
            b["filing_status"], b["assurance_level"], b["tier"] = evidence_attrs("related_party_note", "424B4")
            out.append(b)
        else:
            stats["ipo_related_note_not_found"] += 1

    # 4. 8-K de la tranche : sections des items et pièces EX-10 / EX-4
    for r in idx:
        if r["inv_class"] != "8k_first_pass":
            continue
        f = _filing(r)
        items = {x.strip() for x in (r["items"] or "").split(",")}
        raw = cache.read(cache.archive_path(r["cik"], r["accession"], r["primary"]))
        secs = sections.eight_k_sections(raw)
        for it, kind in FIRST_PASS_ITEMS.items():
            if it not in items:
                continue
            text = secs.get(it)
            if not text:
                stats[f"8k_item_{it}_not_found"] += 1
                continue
            b = blocks._block(kind, f, text, [], r["primary"], None, item=it)
            b["filing_status"], b["assurance_level"], b["tier"] = evidence_attrs(kind, "8-K")
            out.append(b)
        for doc in r.get("documents") or []:
            t = doc["TYPE"].upper().strip()
            if not (EX10.match(t) or EX4.match(t)):
                continue
            raw_ex = cache.read(cache.archive_path(r["cik"], r["accession"], doc["FILENAME"]))
            head = sections.first_page(raw_ex)
            full = sections.full_text(raw_ex)
            hb = blocks._block("exhibit_header", f, head, [], doc["FILENAME"], None, exhibit_type=t,
                               item=",".join(sorted(items)), sgml_description=doc.get("DESCRIPTION"))
            hb["filing_status"], hb["assurance_level"], hb["tier"] = evidence_attrs("exhibit_header", "8-K")
            out.append(hb)
            bb = blocks._block("exhibit_body", f, full, [], doc["FILENAME"], None, exhibit_type=t,
                               item=",".join(sorted(items)), sgml_description=doc.get("DESCRIPTION"),
                               requires={"header_content_key": hb["content_key"], "exhibit_type": t,
                                         "items": sorted(items), "group_id": f["group_id"]})
            bb["filing_status"], bb["assurance_level"], bb["tier"] = evidence_attrs("exhibit_body", "8-K")
            out.append(bb)
    # occurrences multiples d'une même clé de contenu : une seule lecture, provenance gardée
    occ = defaultdict(list)
    for b in out:
        occ[b["content_key"]].append(f"{b['accession']}/{b['document']}")
    for b in out:
        b["occurrences"] = occ[b["content_key"]]
    config.DB_DIR.mkdir(exist_ok=True)
    with open(config.DB_DIR / "blocks.jsonl", "w", encoding="utf-8") as fh:
        for b in out:
            fh.write(json.dumps(b, ensure_ascii=False, default=str) + "\n")
    return out, dict(stats)


NOTE_HEAD = re.compile(r"^\W{0,3}(note\s+)?\d{1,2}\s*[\.\-–—:]?\s*[-–—]?\s*related[\s-]+part(y|ies)", re.I)
NEXT_NOTE = re.compile(r"^\W{0,3}note\s+\d{1,2}\b|^\W{0,3}\d{1,2}\s*[\.\-–—]\s*[A-Z]", re.I)


def related_party_note_html(raw):
    """Note de parties liées d'états financiers en HTML (424B4) : du titre « Note N -
    Related Party Transactions » des états annuels audités jusqu'au titre de note suivant."""
    lines = sections._lines(raw)
    starts = [i for i, (t, _) in enumerate(lines) if NOTE_HEAD.search(t) and len(t) < 120]
    best = None
    for s in starts:
        e = len(lines)
        for j in range(s + 1, min(len(lines), s + 400)):
            if NEXT_NOTE.search(lines[j][0]) and len(lines[j][0]) < 120 and not NOTE_HEAD.search(lines[j][0]):
                e = j
                break
        size = sum(len(t) for t, _ in lines[s:e])
        # la première note complète (états annuels audités) précède celle des états intermédiaires
        if size > 300 and best is None:
            best = (s, e)
    if not best:
        return None
    return textnorm.lines_to_text(lines[best[0]:best[1]])
