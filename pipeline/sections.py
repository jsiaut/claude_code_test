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
    merged = False
    if not starts:
        # titre fondu dans son paragraphe (mise en page sans blocs) : la ligne qui commence
        # par le titre ouvre la section, et la ligne qui commence par un titre majeur la ferme (d3)
        starts = [i for i, (t, h) in enumerate(lines) if len(t) >= 160 and ITEM_404_HEAD.search(t)
                  and not TOC_ROW.search(t)]
        merged = True
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
# titres majeurs d'un DEF 14A qui ferment la section Item 404
MAJOR_PROXY = re.compile(
    r"^\W{0,3}(executive\s+compensation|compensation\s+discussion|director\s+compensation|"
    r"security\s+ownership|beneficial\s+ownership|stock\s+ownership|delinquent\s+section|section\s+16\(a\)|"
    r"stockholder\s+proposals?|shareholder\s+proposals?|audit\s+committee\s+report|report\s+of\s+the\s+audit|"
    r"proposal\s+(no\.?\s*)?\d|proposal\s+(one|two|three|four|five)|other\s+matters|householding|"
    r"questions\s+and\s+answers|equity\s+compensation\s+plan|pay\s+versus\s+performance|annual\s+report|"
    r"board\s+of\s+directors|corporate\s+governance|additional\s+information|submission\s+of|"
    r"general\s+information|information\s+about|the\s+board|our\s+board|human\s+capital|ceo\s+pay\s+ratio|"
    r"compensation\s+committee\s+report|principal\s+accountant|ratification|advisory\s+vote|"
    r"environmental|sustainability|appendix|annex\s+[a-z]|audit\s+(and\s+\w+\s+)?committee\s+report|"
    r"item\s+\d+\s*[-:.]|director\s+independence|compensation\s+committee\s+interlocks|"
    r"consideration\s+of\s+director|board'?s\s+role|management\s+succession|executive\s+sessions|"
    r"notes\s+to\s+the|financial\s+statements|report\s+of\s+independent|independent\s+registered|"
    r"[\w ,&]{3,60}\bcommittee$|principal\s+(and\s+selling\s+)?(stock|share)holders|"
    r"selling\s+(stock|share)holders|description\s+of\s+capital|shares\s+eligible|underwriting|"
    r"material\s+u\.?s\.?\s+federal|legal\s+matters|experts$|where\s+you\s+can\s+find|"
    r"management$|executive\s+officers\s+and\s+directors|additional\s+meeting)", re.I)
ITEM_404_HEAD = re.compile(
    r"^\W{0,3}(certain\s+relationships\s+and\s+related|related[\s-]+(person|party)\s+transactions?\b|"
    r"transactions?\s+with\s+related\s+(persons?|parties)|review\s+of\s+transactions\s+with\s+related|"
    r"(and\s+)?related\s+(person|party)\s+transactions?$|policies\s+and\s+procedures\s+for\s+related)", re.I)
PAGE_FURNITURE = re.compile(r"proxy\s+statement|^\d{1,3}$|^table\s+of\s+contents$|annual\s+meeting\s+of|"
                            r"^back\s+to\s+contents$|notice\s+of\s+(annual\s+)?meeting", re.I)


TOC_ROW = re.compile(r"\|\s*\d{1,3}\s*$")
PAGE_NUMBER = re.compile(r"^\d{1,3}$")
SENTENCE = re.compile(r"[.:]\s+[A-Z(]\w*\s+\w+")


def item_404(raw, max_chars=60000):
    """Section Item 404 : du premier titre « Certain Relationships... » ou « Related Person
    Transactions » hors sommaire jusqu'au titre majeur suivant du DEF 14A (en-têtes et pieds
    de page ignorés), plafonnée à max_chars ; la section la plus longue l'emporte (sommaire)."""
    lines = _lines(raw)
    # un titre ouvre la ligne et ne se termine pas par une ponctuation de phrase (renvois écartés)
    # une entrée de sommaire (titre suivi de son numéro de page, sur la ligne ou la suivante)
    # n'ouvre pas la section (d3)
    starts = [i for i, (t, h) in enumerate(lines) if len(t) < 160 and ITEM_404_HEAD.search(t)
              and not t.rstrip().endswith((".", '"', ",", ";")) and (h or len(t) < 90)
              and not TOC_ROW.search(t)
              and not (i + 1 < len(lines) and PAGE_NUMBER.match(lines[i + 1][0].strip()))]
    merged = False
    if not starts:
        # titre fondu dans son paragraphe (mise en page sans blocs) : la ligne qui commence
        # par le titre ouvre la section, et la ligne qui commence par un titre majeur la ferme (d3)
        starts = [i for i, (t, h) in enumerate(lines) if len(t) >= 160 and ITEM_404_HEAD.search(t)
                  and not TOC_ROW.search(t)]
        merged = True
    best = None
    for s in starts:
        e = len(lines)
        size = 0
        for j in range(s + 1, len(lines)):
            t, h = lines[j]
            size += len(t)
            if PAGE_FURNITURE.search(t) and len(t) < 120:
                continue
            # un titre majeur, pas une puce qui commence par les mêmes mots (« Director
            # compensation. Any compensation... ») : marqué titre, ou sans phrase (d3)
            if len(t) < 150 and MAJOR_PROXY.search(t) and size > 300 and not ITEM_404_START.search(t) \
                    and (h or not SENTENCE.search(t)):
                e = j
                break
            if merged and MAJOR_PROXY.search(t) and size > 300 and not ITEM_404_START.search(t[:200]):
                e = j
                break
            if size > max_chars:
                e = j
                break
        body = [t for t, _ in lines[s:e] if not (PAGE_FURNITURE.search(t) and len(t) < 120)]
        text_size = sum(len(t) for t in body)
        if text_size >= 300 and (best is None or text_size > best[2]):
            best = (s, e, text_size, body)
    if not best:
        return None
    return "\n".join(best[3])


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
