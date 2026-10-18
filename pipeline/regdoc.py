"""Document d'enregistrement qui tient lieu de rapports périodiques (D-0057, point 14).

Un émetteur introduit en Bourse qui n'a déposé aucun rapport périodique avant l'as_of, et dont le
document d'enregistrement ne porte aucune instance XBRL financière (SK hynix, 424B4 du 2026-07-10),
n'a pas de rôles de notes. Ses jeux d'états financiers se découpent en HTML et leurs notes se lisent
comme les notes balisées d'un 20-F (D-0048, D-0056) :
- mêmes familles, reconnues au titre de la note au lieu de la définition du rôle
  (`text_catalog.NOTE_SPECS`) : participations, dette, baux, engagements ;
- note de parties liées, note de revenu, notes des leviers (immobilisations corporelles,
  estimations et jugements, paragraphe des immobilisations de la note des principes comptables) et
  paragraphes des clients de la note sectorielle (texte de concentration, IFRS 8.34) ;
- les autres notes ne sont pas lues, comme les rôles d'un 20-F hors de ces familles.
Les jeux et leur assurance sont fixés dans `config.yaml` (`registration_text`) avant toute lecture.
"""
import re
from collections import Counter

from . import blocks, cache, config, sections, textnorm

# titre courant d'un jeu de notes (singulier ou pluriel) ; ligne de titre, jamais une ligne du sommaire
NOTES_HEAD = re.compile(r"^notes to (the )?(unaudited )?(condensed )?(consolidated )?(interim )?financial statements?"
                        r"(\s*\(continued\))?$", re.I)
NOTE_TITLE = re.compile(r"^(\d{1,2})\.\s+(\S.*)$")
CONTINUED = re.compile(r",\s*continued\)?$", re.I)
# fin d'un jeu : titre d'un état financier ou d'un rapport d'audit (le jeu suivant commence après)
SET_END = re.compile(r"^(condensed )?consolidated (interim )?(statements?|balance sheets?) of\b|^report of independent", re.I)
FOOTER = re.compile(r"^F-\d{1,3}$")
SUBSECTION = re.compile(r"^\((\d{1,2})\)\s*\|?\s*(\S.*)$")

RELATED = re.compile(r"related[\s-]+part", re.I)
REVENUE = re.compile(r"^revenues?\b|revenue from contracts", re.I)
LEVER = re.compile(r"property,? plant,? and equipment|critical accounting (estimates|judge?ments)|"
                   r"accounting (estimates|judge?ments)", re.I)
POLICIES = re.compile(r"accounting policies", re.I)
PPE_POLICY = re.compile(r"^property,? plant,? and equipment$", re.I)
SEGMENT = re.compile(r"segment", re.I)


def _families():
    from .text_catalog import NOTE_SPECS
    return NOTE_SPECS


def note_kind(title):
    """Famille d'une note d'après son titre ; la première famille reconnue l'emporte, dans l'ordre des
    rôles d'un rapport balisé (parties liées, participations, dette, baux, engagements), puis revenu
    et leviers ; None pour une note qui n'est pas lue."""
    if RELATED.search(title):
        return "related_party_note"
    for kind, rx in _families():
        if rx.search(title):
            return kind
    if REVENUE.search(title):
        return "revenue_note"
    if LEVER.search(title):
        return "lever_note"
    return None


def _running_headers(lines, feet):
    """Titres courants du document : lignes de titre qui suivent un pied de page « F-n », avant tout titre
    de note, sur au moins trois pages."""
    c = Counter()
    for i in feet:
        j = i + 1
        while j < len(lines) and lines[j][1] and j - i <= 8:
            t = lines[j][0].strip()
            if NOTE_TITLE.match(t):
                break
            c[t] += 1
            j += 1
    return {t for t, n in c.items() if n >= 3}


def note_sets(raw):
    """Jeux de notes d'un document en HTML : [{set, notes: [{number, title, text, lines}]}].

    Un jeu s'ouvre à un titre « Notes to the ... Financial Statement(s) » suivi, à moins de douze
    lignes, du titre de la note 1 ; une note va de son titre « N. Titre » (numérotation suivie) au
    titre suivant ; un jeu se ferme au titre d'un état financier ou d'un rapport d'audit, ou après le
    dernier pied de page « F-n ». Les pieds de page, les titres courants qui les suivent et les
    titres « N. Titre, Continued » sont retirés."""
    lines = sections._lines(raw)
    feet = [i for i, (t, _) in enumerate(lines) if FOOTER.match(t.strip())]
    doc_end = (feet[-1] + 1) if feet else len(lines)
    bounds = []
    i = 0
    while i < doc_end:
        first = _set_start(lines, i, doc_end)
        if first is None:
            i += 1
            continue
        # le titre d'un état financier, d'un rapport d'audit ou du jeu suivant ferme le jeu
        end = next((j for j in range(first + 1, doc_end) if lines[j][1] and "|" not in lines[j][0]
                    and (SET_END.match(lines[j][0].strip()) or _set_start(lines, j, doc_end) is not None)), doc_end)
        bounds.append((first, end))
        i = end
    out = []
    rh = _running_headers(lines, feet)
    for si, (lo, hi) in enumerate(bounds):
        keep, after_foot = [], False
        for j in range(lo, hi):
            t, h = lines[j][0].strip(), lines[j][1]
            if FOOTER.match(t):
                after_foot = True
                continue
            if after_foot and h and (t in rh or (NOTE_TITLE.match(t) and CONTINUED.search(t))):
                continue
            after_foot = False
            if h and NOTE_TITLE.match(t) and CONTINUED.search(t):
                continue
            keep.append((j, lines[j]))
        notes, expect, cur = [], 1, None
        for j, (t, h) in keep:
            m = NOTE_TITLE.match(t.strip()) if h and len(t) < 160 else None
            if m and int(m.group(1)) == expect:
                cur = {"number": expect, "title": m.group(2).strip(), "lines": []}
                notes.append(cur)
                expect += 1
            if cur is not None:
                cur["lines"].append((t, h))
        for n in notes:
            n["text"] = textnorm.lines_to_text(n["lines"])
        out.append({"set": si, "notes": notes})
    return out


def _set_start(lines, i, doc_end):
    """Indice du titre de la note 1 si la ligne i est le titre courant d'un jeu qui s'ouvre (la note 1
    suit à moins de douze lignes, sans « Continued »), sinon None."""
    t, h = lines[i][0].strip(), lines[i][1]
    if not (h and "|" not in t and NOTES_HEAD.match(t)):
        return None
    for j in range(i + 1, min(i + 12, doc_end)):
        tj = lines[j][0].strip()
        m = NOTE_TITLE.match(tj) if lines[j][1] else None
        if m and m.group(1) == "1" and not CONTINUED.search(tj):
            return j
    return None


def ppe_policy(note):
    """Paragraphe des immobilisations corporelles de la note des principes comptables : de la
    sous-section « (n) Property, plant and equipment » à la sous-section suivante."""
    ls = note["lines"]
    start = next((k for k, (t, _) in enumerate(ls)
                  if (m := SUBSECTION.match(t.strip())) and PPE_POLICY.match(m.group(2).strip())), None)
    if start is None:
        return None
    num = SUBSECTION.match(ls[start][0].strip()).group(1)
    end = next((k for k in range(start + 1, len(ls))
                if (m := SUBSECTION.match(ls[k][0].strip())) and m.group(1) != num), len(ls))
    return textnorm.lines_to_text(ls[start:end])


def customer_paragraphs(note):
    """Paragraphes des clients de la note sectorielle (IFRS 8.34), comme `concentration_text`."""
    from .text_catalog import CONC_RX
    keep = [t for t, _ in note["lines"] if CONC_RX.search(t) and re.search(r"customer|client", t, re.I)]
    return "\n".join(keep) or None


def specs(cfg=None):
    cfg = cfg or config.load()
    return cfg.get("registration_text") or []


def document_blocks(spec, filing, raw):
    """Blocs d'un document d'enregistrement de `registration_text`."""
    sets = note_sets(raw)
    ns = spec["note_sets"]
    if len(sets) != len(ns):
        raise ValueError(f"{spec['accession']} : {len(sets)} jeux de notes découpés, {len(ns)} fixés dans config.yaml")
    out = []
    for s, st in zip(sets, ns):
        f = dict(filing, period_start=st["period_start"], report_date=st["period_end"])
        audited = st["assurance"] == "audited"
        label = st["label"]

        def add(kind, text, note_label):
            b = blocks._block(kind, f, text, [], spec["primary"], None, note_label=note_label, note_set=label)
            b["signal_class"] = 1 if kind == "related_party_note" else 3
            b["filing_status"] = "filed"
            b["assurance_level"] = "audited" if audited else "unaudited"
            b["tier"] = "A" if audited else "C"
            b["registration_text"] = spec["decision"]
            out.append(b)

        for n in s["notes"]:
            head = f"{label} — note {n['number']}. {n['title']}"
            kind = note_kind(n["title"])
            if kind:
                add(kind, n["text"], head)
            if POLICIES.search(n["title"]):
                txt = ppe_policy(n)
                if txt:
                    add("lever_note", txt, head + " (immobilisations corporelles)")
            if SEGMENT.search(n["title"]):
                txt = customer_paragraphs(n)
                if txt:
                    add("concentration_text", txt, head + " (paragraphes des clients)")
    return out


def build(stats):
    """Blocs de tous les documents de `registration_text`, pour le catalogue du bloc `text`."""
    import json
    from .catalog import _filing
    idx = {r["accession"]: r for r in json.loads((config.DB_DIR / "filing_index.json").read_text())}
    out = []
    for spec in specs():
        r = idx[spec["accession"]]
        raw = cache.read(cache.archive_path(r["cik"], r["accession"], spec["primary"]))
        bl = document_blocks(spec, _filing(r), raw)
        stats["registration_text_blocks"] += len(bl)
        out += bl
    return out
