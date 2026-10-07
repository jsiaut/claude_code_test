"""Catalogue du bloc `text` de §14 : le reste du texte des groupes de `config.yaml`, sur la
même période que la tranche (fenêtre allongée et huit trimestres qui la précèdent).

Notes d'investissements (participations qui ne sont pas des parties liées), de dette, de baux
et d'engagements, texte autour des faits de concentration, 8-K items 2.01 et 2.03, corps des
EX-10 et EX-4 arrêtés à leur en-tête au premier passage. Les blocs se servent comme ceux de la
tranche (§7.4) : texte normalisé et faits candidats, clé de contenu, du plus récent au plus
ancien.
"""
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict

import pandas as pd

from . import blocks, cache, config, sections, textnorm, xbrl
from .catalog import _cache_member, _filing
from .edgar import cik10

# rôles de note, par définition de rôle (§9.2) ; une note peut relever de deux familles
NOTE_SPECS = [
    ("investment_note", re.compile(r"\binvestments?\b|equity[\s-]+method|marketable|equity securities|"
                                   r"variable interest|\bvie\b|other income", re.I)),
    ("debt_note", re.compile(r"\bdebt\b|borrowing|credit (facilit|agreement)|notes payable|senior notes|"
                             r"convertible (senior )?notes|financing (arrangement|obligation)|commercial paper|"
                             r"\bloans? payable", re.I)),
    ("lease_note", re.compile(r"\bleases?\b|leasing", re.I)),
    ("commitments_note", re.compile(r"commitments?|contingenc|guarantee|purchase obligation", re.I)),
]
CONC_CONCEPT = "us-gaap:ConcentrationRiskPercentage1"
CONC_RX = re.compile(r"customer|client|concentration|\d+\s?%|percent", re.I)


def note_blocks(filing, files, inst_name, tb_concepts, facts_rows, labels):
    """Blocs des notes de la tranche `text` d'un rapport périodique."""
    facts, tblocks, _ = xbrl.parse_instance(files[inst_name], tb_concepts)
    lb = xbrl.parse_linkbases({n: b for n, b in files.items()
                               if n.lower().endswith((".xsd", ".xml")) and n != inst_name
                               and n != "FilingSummary.xml"})
    raw = files[inst_name]
    out = []
    seen = set()
    by_concept = {tb["concept"]: tb for tb in tblocks if not tb["dims"]}
    for kind, rx in NOTE_SPECS:
        notes, details = blocks.note_roles(lb, rx)
        if not notes:
            continue
        note_concepts = blocks.concepts_in_roles(lb, notes)
        detail_concepts = blocks.concepts_in_roles(lb, details)
        cands = [f for f in facts_rows if f["concept"] in detail_concepts and f.get("value") is not None]
        for c in sorted(note_concepts):
            tb = by_concept.get(c)
            if tb is None or c in seen:
                continue
            text = textnorm.lines_to_text(textnorm.html_fragment_lines(tb["text"]))
            if not text.strip():
                continue
            seen.add(c)
            loc = blocks._fact_byte_range(raw, tb.get("fact_id"))
            cand = [blocks._cand(f, labels) for f in cands]
            out.append(blocks._block(kind, filing, text, cand, inst_name, loc,
                                     note_label=c + " | " + "; ".join(blocks._role_def(lb, r) for r in notes)))
    # texte autour des faits de concentration : les paragraphes de la note qui les porte
    conc_roles = [r for r, arcs in lb["pres"].items() if any(CONC_CONCEPT in (a[0], a[1]) for a in arcs)]
    if conc_roles:
        conc_facts = [f for f in facts_rows if f["concept"] == CONC_CONCEPT and f.get("value") is not None]
        for r in conc_roles:
            rdef = blocks._role_def(lb, r)
            # la note parente : bloc de texte d'un rôle de note de même titre (avant « (Details) »)
            title = re.split(r"\s*\((details|tables|narrative)", rdef.split(" - ", 2)[-1], flags=re.I)[0].strip()
            for nr, nd in lb["roles"].items():
                if xbrl.statement_kind(nd) != "note" or title.lower() not in (nd or "").lower():
                    continue
                for c in blocks.concepts_in_roles(lb, [nr]):
                    tb = by_concept.get(c)
                    if tb is None:
                        continue
                    lines = textnorm.lines_to_text(textnorm.html_fragment_lines(tb["text"])).split("\n")
                    keep = [ln for ln in lines if CONC_RX.search(ln) and re.search(r"customer|client", ln, re.I)]
                    if not keep:
                        continue
                    text = "\n".join(keep)
                    loc = blocks._fact_byte_range(raw, tb.get("fact_id"))
                    cand = [blocks._cand(f, labels) for f in conc_facts]
                    out.append(blocks._block("concentration_text", filing, text, cand, inst_name, loc,
                                             note_label=c + " | " + nd + " (paragraphes des clients)"))
    return out


ITEMS_TEXT = {"2.01": "item_8k_201", "2.03": "item_8k_203"}


def eight_k_blocks(stats, fetch=True):
    """Sections des items 2.01 et 2.03 des 8-K des groupes, sur la période de la tranche ; un
    document principal absent du cache se tire (client SEC, journal)."""
    inv = pd.read_parquet(config.DB_DIR / "inventory.parquet")
    k8 = inv[inv["form"].isin(["8-K", "8-K/A"]) & inv["items"].fillna("").str.contains(r"2\.01|2\.03")]
    client = None
    out = []
    for r in k8.sort_values("filingDate").to_dict("records"):
        cik, acc, doc = r["filer_cik"], r["accessionNumber"], r["primaryDocument"]
        p = cache.archive_path(cik10(cik), acc, doc)
        if not p.exists():
            if not fetch:
                stats["8k_primary_missing"] += 1
                continue
            if client is None:
                from . import edgar, net
                client = edgar.Edgar(net.SecClient("2026-10-07"), "2026-10-07")
            try:
                client.archive(cik10(cik), acc, doc)
            except Exception:
                stats["8k_primary_not_collected"] += 1
                continue
        raw = cache.read(p)
        secs = sections.eight_k_sections(raw)
        items = {x.strip() for x in (r["items"] or "").split(",")}
        f = _filing(r)
        for it, kind in ITEMS_TEXT.items():
            if it not in items:
                continue
            text = secs.get(it)
            if not text:
                stats[f"8k_item_{it}_not_found"] += 1
                continue
            b = blocks._block(kind, f, text, [], doc, None, item=it)
            b["signal_class"] = 3
            b["filing_status"], b["assurance_level"], b["tier"] = "filed", "not_applicable", "C"
            out.append(b)
    return out


def iter_periodic(limit=None):
    inv = pd.read_parquet(config.DB_DIR / "inventory.parquet")
    xd = pd.read_parquet(config.DB_DIR / "xbrl_documents.parquet").set_index("accession")
    per = inv[inv["inv_class"] == "periodic"]
    n = 0
    for r in per.to_dict("records"):
        acc = r["accessionNumber"]
        if acc not in xd.index:
            continue
        yield r, xd.loc[acc]
        n += 1
        if limit and n >= limit:
            return


def build(as_of, limit=None):
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
    out, stats = [], Counter()
    out += eight_k_blocks(stats)
    for r, d in iter_periodic(limit):
        acc, cik = r["accessionNumber"], r["filer_cik"]
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
            stats["instance_missing"] += 1
            continue
        files[inst] = data
        f = _filing(r)
        try:
            bl = note_blocks(f, files, inst, tb_by.get(acc) or None,
                             facts_by.get(acc, pd.DataFrame()).to_dict("records"), lab_by.get(acc, {}))
        except Exception:
            stats["parse_failed"] += 1
            continue
        for b in bl:
            b["signal_class"] = 3
            b["filing_status"] = "filed"
            b["assurance_level"] = "audited" if f["form"].startswith("10-K") else "reviewed"
            b["tier"] = "A" if f["form"].startswith("10-K") else "B"
            out.append(b)
    return out, stats


if __name__ == "__main__":
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
    out, stats = build("2026-10-07", lim)
    by = defaultdict(lambda: [0, 0, set()])
    for b in out:
        x = by[b["block_kind"]]
        x[0] += 1
        if b["content_key"] not in x[2]:
            x[1] += b["chars"]
            x[2].add(b["content_key"])
    for k, (n, ch, keys) in sorted(by.items()):
        print(k, n, len(keys), ch)
    print(dict(stats))
    with open(config.DB_DIR / "text_blocks_ext.jsonl", "w", encoding="utf-8") as fh:
        for b in out:
            fh.write(json.dumps(b, ensure_ascii=False, default=str) + "\n")
