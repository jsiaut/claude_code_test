"""Délimitation des sections par leurs titres (§9.2) et première page des pièces.

Les Items d'un 10-K, l'Item 4 de la partie I d'un 10-Q, la section de l'Item 404 d'un
DEF 14A et les items d'un 8-K se délimitent par leurs titres. Une table des matières
répète les titres : la section retenue est la plus longue entre un titre et le titre
de fin suivant, ce qui écarte les entrées de sommaire.
"""
import re

from . import textnorm

_ITEM = r"^\W{0,3}item\s*"


def _lines(raw):
    root = textnorm.parse_html(raw)
    return textnorm.linearize(root)


def _longest_section(lines, start_rx, end_rx, min_chars=200, start_filter=None):
    starts = [i for i, (t, _) in enumerate(lines) if start_rx.search(t) and len(t) < 400]
    best = None
    for s in starts:
        if start_filter and not start_filter(lines, s):
            continue
        e = len(lines)
        for j in range(s + 1, len(lines)):
            if end_rx.search(lines[j][0]) and len(lines[j][0]) < 400:
                e = j
                break
        size = sum(len(t) for t, _ in lines[s:e])
        if size >= min_chars and (best is None or size > best[2]):
            best = (s, e, size)
    if best is None:
        return None
    s, e, _ = best
    return lines[s:e]


ITEM_9A = re.compile(_ITEM + r"9a\b", re.I)
ITEM_9A_END = re.compile(_ITEM + r"(9b|9c|10)\b|^\W{0,3}part\s+iii\b", re.I)


def item_9a(raw):
    sec = _longest_section(_lines(raw), ITEM_9A, ITEM_9A_END)
    return textnorm.lines_to_text(sec) if sec else None


ITEM_4 = re.compile(_ITEM + r"4\b", re.I)
ITEM_4_END = re.compile(r"^\W{0,3}part\s+ii\b|" + _ITEM + r"1\.?\s*(legal|\|)|" + _ITEM + r"1a\b", re.I)


def _is_controls(lines, i):
    window = " ".join(t for t, _ in lines[i:i + 3]).lower()
    return "control" in window and "mine safety" not in lines[i][0].lower()


def item_4_10q(raw):
    sec = _longest_section(_lines(raw), ITEM_4, ITEM_4_END, start_filter=_is_controls)
    return textnorm.lines_to_text(sec) if sec else None


EIGHT_K_ITEM = re.compile(_ITEM + r"(\d{1,2}\.\d{2})\b", re.I)
SIGNATURE = re.compile(r"^\W{0,3}signatures?\b", re.I)


def eight_k_sections(raw):
    """Découpe un 8-K par ses titres « Item x.xx » ; renvoie {item: texte}."""
    lines = _lines(raw)
    heads = []
    for i, (t, _) in enumerate(lines):
        m = EIGHT_K_ITEM.match(t)
        if m and len(t) < 400:
            heads.append((i, m.group(1)))
    out = {}
    for k, (i, item) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        for j in range(i + 1, end):
            if SIGNATURE.match(lines[j][0]):
                end = j
                break
        text = textnorm.lines_to_text(lines[i:end])
        # garde la version la plus longue si un item est répété (sommaire, rappel)
        if item not in out or len(text) > len(out[item]):
            out[item] = text
    return out


ITEM_404_START = re.compile(
    r"(certain\s+relationships\s+and\s+related|related[\s-]+(person|party)\s+transactions?|"
    r"transactions?\s+with\s+related\s+(persons?|parties)|related[\s-]+(person|party)\s+transaction\s+polic)",
    re.I)
ITEM_404_CONT = re.compile(r"related|transaction|relationship|polic|procedure|review|approval|"
                           r"indebtedness|employment of|family", re.I)


def item_404(raw, max_chars=60000):
    """Section Item 404 : du premier titre « Certain Relationships... » ou
    « Related Person Transactions » hors sommaire jusqu'au titre suivant étranger au sujet."""
    lines = _lines(raw)
    starts = [i for i, (t, h) in enumerate(lines) if h and ITEM_404_START.search(t) and len(t) < 200]
    best = None
    for s in starts:
        e = len(lines)
        size = 0
        for j in range(s + 1, len(lines)):
            t, h = lines[j]
            size += len(t)
            if h and len(t) < 200 and not ITEM_404_CONT.search(t) and size > 300:
                e = j
                break
            if size > max_chars:
                e = j
                break
        text_size = sum(len(t) for t, _ in lines[s:e])
        if text_size >= 300 and (best is None or text_size > best[2]):
            best = (s, e, text_size)
    if not best:
        return None
    return textnorm.lines_to_text(lines[best[0]:best[1]])


_PAGE_BREAK = re.compile(rb"page-break-(before|after)\s*:\s*always|break-(before|after)\s*:\s*page|<hr[^>]*>",
                         re.I)


def first_page(raw, min_chars=1500, max_chars=12000):
    """Première page d'une pièce : texte avant le premier saut de page, étendu au
    suivant si elle fait moins de min_chars (page de garde), plafonné à max_chars."""
    cut = None
    for m in _PAGE_BREAK.finditer(raw):
        part = raw[:m.start()]
        text = textnorm.lines_to_text(_lines(part + b"</body></html>")) if part.strip() else ""
        if len(text) >= min_chars:
            cut = text
            break
    if cut is None:
        cut = textnorm.lines_to_text(_lines(raw))
    if len(cut) > max_chars:
        cut = cut[:max_chars].rsplit("\n", 1)[0]
    return cut


def full_text(raw):
    return textnorm.lines_to_text(_lines(raw))


def document_title(text, n=6):
    """Premières lignes non vides d'une pièce (pour la règle des amendements, §11.1)."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return " ".join(lines[:n])[:500]


AMEND_EX10 = re.compile(r"\b(amendment|waiver|consent)\b", re.I)
AMENDED_RESTATED = re.compile(
    r"^\W*((first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|\d+(st|nd|rd|th))\s+)?"
    r"amended\s+and\s+restated\b", re.I)
SUPPLEMENTAL_INDENTURE = re.compile(
    r"^\W*((first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|"
    r"\w+teenth|\w+tieth|\w+-\w+|\d+(st|nd|rd|th))\s+)?supplemental\s+indenture\b", re.I)


def amendment_rule(exhibit_type, title, eight_k_items):
    """Corps lu quelles que soient les parties (§11.1) : EX-10 dont le titre contient
    Amendment, Waiver ou Consent en mot entier, sauf s'il commence (ordinal mis à part)
    par Amended and Restated ; EX-4 « Supplemental Indenture » si le 8-K porte 3.03."""
    t = (title or "").strip()
    et = (exhibit_type or "").upper()
    if et.startswith("EX-10"):
        return bool(AMEND_EX10.search(t)) and not AMENDED_RESTATED.search(t)
    if et.startswith("EX-4"):
        return bool(SUPPLEMENTAL_INDENTURE.search(t)) and "3.03" in (eight_k_items or set())
    return False
