"""Blocs naturels de la tranche à fort signal (§7.4, §9.2, §11.1).

Un bloc : un bloc de texte de note (textBlockItemType rattaché à un rôle de note) et
ses tableaux linéarisés, une section délimitée par son titre (Item 404, Item 9A,
Item 4 de la partie I d'un 10-Q, items 1.01, 1.02, 3.03 et 8.01 d'un 8-K), une pièce
EX-10 ou EX-4 annexée à ces 8-K, servie d'abord par sa première page. Le code le
sert avec les faits candidats qu'il contient et leurs valeurs, jamais en HTML brut.

La clé de contenu est le sha256 de la version du normaliseur, du texte normalisé
et des faits candidats pris par leurs valeurs, sans identifiant d'occurrence (§9.6).
"""
import hashlib
import json
import re

from . import textnorm, xbrl
from .config import NORMALIZER_VERSION, DELIMITER_VERSION

RELATED_RX = re.compile(r"related[\s-]+part(y|ies)|related[\s-]+person", re.I)
GOING_CONCERN_RX = re.compile(r"going\s+concern", re.I)
GC_DOUBT_RX = re.compile(r"substantial\s+doubt", re.I)


def content_key(text, candidates):
    cands = sorted(json.dumps({k: c.get(k) for k in ("concept", "value", "unit", "period_start",
                                                      "period_end", "dims")},
                              sort_keys=True, default=str) for c in candidates)
    h = hashlib.sha256()
    h.update(NORMALIZER_VERSION.encode())
    h.update(b"\n")
    h.update(text.encode("utf-8"))
    h.update(b"\n")
    h.update("\n".join(cands).encode("utf-8"))
    return h.hexdigest()


def _role_def(lb, role):
    return lb["roles"].get(role, "") or ""


def note_roles(lb, pattern):
    notes, details = [], []
    for role, rdef in lb["roles"].items():
        if not pattern.search(rdef or ""):
            continue
        kind = xbrl.statement_kind(rdef)
        if kind == "note":
            notes.append(role)
        elif kind in ("note_details", "note_tables"):
            details.append(role)
    return notes, details


def concepts_in_roles(lb, roles):
    out = set()
    for r in roles:
        for frm, to, *_ in lb["pres"].get(r, []):
            out.add(frm)
            out.add(to)
    return out


def instance_blocks(filing, files, inst_name, tb_concepts, facts_rows, labels):
    """Blocs des notes balisées d'un rapport périodique : parties liées et continuité
    d'exploitation. facts_rows : faits numériques du dépôt (lignes de la table facts)."""
    facts, tblocks, _ = xbrl.parse_instance(files[inst_name], tb_concepts)
    lb = xbrl.parse_linkbases({n: b for n, b in files.items()
                               if n.lower().endswith((".xsd", ".xml")) and n != inst_name
                               and n != "FilingSummary.xml"})
    raw = files[inst_name]
    out = []
    specs = [("related_party_note", RELATED_RX), ("going_concern", GOING_CONCERN_RX)]
    for kind, rx in specs:
        notes, details = note_roles(lb, rx)
        note_concepts = concepts_in_roles(lb, notes)
        if kind == "going_concern":
            note_concepts.add("us-gaap:SubstantialDoubtAboutGoingConcernTextBlock")
        detail_concepts = concepts_in_roles(lb, details)
        cands = [f for f in facts_rows if f["concept"] in detail_concepts and f.get("value") is not None]
        for tb in tblocks:
            if tb["concept"] not in note_concepts or tb["dims"]:
                continue
            lines = textnorm.html_fragment_lines(tb["text"])
            text = textnorm.lines_to_text(lines)
            if not text.strip():
                continue
            if kind == "going_concern" and not GC_DOUBT_RX.search(text) and \
                    tb["concept"] != "us-gaap:SubstantialDoubtAboutGoingConcernTextBlock":
                continue
            loc = _fact_byte_range(raw, tb.get("fact_id"))
            cand = [_cand(f, labels) for f in cands]
            out.append(_block(kind, filing, text, cand, inst_name, loc,
                              note_label=tb["concept"] + " | " + "; ".join(_role_def(lb, r) for r in notes)))
    return out


def going_concern_fallback(filing, files, inst_name, tb_concepts):
    """À défaut de bloc balisé de doute sur la continuité d'exploitation, le passage
    correspondant de la note 1 (§11.1) : premier bloc de note dont le texte associe
    « substantial doubt » et « going concern »."""
    facts, tblocks, _ = xbrl.parse_instance(files[inst_name], tb_concepts)
    raw = files[inst_name]
    for tb in sorted(tblocks, key=lambda t: t["occ_rank"]):
        if tb["dims"]:
            continue
        txt = textnorm.lines_to_text(textnorm.html_fragment_lines(tb["text"]))
        paras = [p for p in txt.split("\n") if GOING_CONCERN_RX.search(p) and GC_DOUBT_RX.search(p)]
        if paras:
            loc = _fact_byte_range(raw, tb.get("fact_id"))
            return _block("going_concern", filing, "\n".join(paras), [], inst_name, loc,
                          note_label=tb["concept"] + " (passage)")
    return None


def _fact_byte_range(raw, fact_id):
    if not fact_id:
        return None
    m = re.search(rb'\bid="' + re.escape(fact_id.encode()) + rb'"', raw)
    if not m:
        return None
    start = raw.rfind(b"<", 0, m.start())
    tag = re.match(rb"<([\w:\-\.]+)", raw[start:start + 300])
    if not tag:
        return [start, m.end()]
    end_tag = b"</" + tag.group(1) + b">"
    end = raw.find(end_tag, m.end())
    return [start, (end + len(end_tag)) if end >= 0 else m.end()]


def _cand(f, labels):
    dims = json.loads(f.get("dims") or "[]")
    dl = [[a, m, labels.get(m)] for a, m in dims]
    return {"fact_key": f["fact_key"], "concept": f["concept"], "value": str(f["value"]),
            "unit": f.get("unit"), "period_start": str(f.get("period_start") or ""),
            "period_end": str(f.get("period_end") or ""),
            "dims": json.dumps(dl) if dl else "[]", "decimals": f.get("decimals")}


def _block(kind, filing, text, cands, document, byte_range, **extra):
    ck = content_key(text, cands)
    return {
        "content_key": ck, "block_kind": kind, "signal_class": 1 if kind in (
            "related_party_note", "item_404", "item_9a", "item_4_10q", "going_concern",
            "spacex_annual_note") else 2,
        "sort_key": _recency_key(filing), "group_id": filing["group_id"], "cik": filing["cik"],
        "accession": filing["accession"], "form": filing["form"],
        "filing_date": filing["filing_date"], "acceptance": filing.get("acceptance"),
        "knowledge_date": filing["filing_date"], "period_start": filing.get("period_start"),
        "period_end": filing.get("report_date"), "document": document,
        "locator": {"file": document, "accession": filing["accession"], "cik": filing["cik"],
                    "byte_range": byte_range},
        "text": text, "candidate_facts": cands, "chars": len(text),
        "normalizer_version": NORMALIZER_VERSION, "delimiter_version": DELIMITER_VERSION,
        **extra,
    }


def _recency_key(filing):
    """Tri lexical croissant = du plus récent au plus ancien (§11.1)."""
    a = re.sub(r"\D", "", str(filing.get("acceptance") or filing["filing_date"]))[:14].ljust(14, "0")
    return f"{99999999999999 - int(a):014d}:{filing['accession']}"
