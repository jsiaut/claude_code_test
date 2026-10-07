"""Normaliseur de texte versionné (§9.2). Sa version entre dans les clés de cache.

Décodage (EDGAR mêle ASCII, Latin-1 et UTF-8), entités, forme Unicode, constructions
iXBRL (ix:header, ix:exclude et ix:hidden exclus, ix:continuation rattaché),
tableaux linéarisés selon leur structure (parseur d'arbre, pas machine à états).
"""
import re
import unicodedata

from lxml import etree, html

from .config import NORMALIZER_VERSION

VERSION = NORMALIZER_VERSION

BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "section",
         "article", "center", "blockquote", "pre", "ul", "ol", "dl", "dt", "dd", "hr", "title",
         "body", "html", "page", "header", "footer", "caption", "thead", "tbody", "tfoot"}
CELL = {"td", "th"}
SKIP = {"script", "style", "head", "ix:header", "ix:exclude", "ix:hidden", "noscript",
        "xbrli:context", "xbrli:unit"}
HEADING = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BOLD_STYLE = re.compile(r"font-weight\s*:\s*(bold|[6-9]00)", re.I)
_UNDER_STYLE = re.compile(r"text-decoration[^;]*underline", re.I)
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none", re.I)

_PUNCT = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "″": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-",
    "−": "-", "­": "", "​": "", "‌": "", "‍": "", "﻿": "",
    "•": "•", " ": " ", " ": " ", " ": " ", " ": " ",
})
_WS = re.compile(r"[ \t\r\f\v]+")


def decode(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1252")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def norm_inline(s: str) -> str:
    """Normalisation d'un fragment de texte : forme Unicode, ponctuation, espaces."""
    s = unicodedata.normalize("NFKC", s).translate(_PUNCT)
    return _WS.sub(" ", s.replace("\n", " "))


def norm_for_match(s: str) -> str:
    """Forme de comparaison des citations : même normalisation, espaces réduits."""
    return re.sub(r"\s+", " ", norm_inline(s)).strip()


def parse_html(raw: bytes):
    text = decode(raw)
    # supprime la déclaration XML qui gêne le parseur HTML
    text = re.sub(r"^\s*<\?xml[^>]*\?>", "", text)
    parser = html.HTMLParser(huge_tree=True, remove_comments=True, encoding=None)
    try:
        return html.document_fromstring(text, parser=parser)
    except (etree.ParserError, ValueError):
        return html.fragment_fromstring(text, create_parent="div", parser=parser)


def _tag(el):
    t = el.tag
    if not isinstance(t, str):
        return ""
    return t.lower()


class Linearizer:
    """Linéarise un arbre HTML en lignes ; chaque ligne garde un indice de titre
    (gras, souligné, balise de titre ou capitales courtes)."""

    def __init__(self):
        self.lines = []      # (texte, is_heading_like)
        self.buf = []        # (fragment, bold)

    def flush(self):
        if not self.buf:
            return
        text = "".join(f for f, _ in self.buf)
        text = _WS.sub(" ", text).strip()
        if text:
            nonspace = [b for f, b in self.buf if f.strip()]
            bold = bool(nonspace) and all(nonspace)
            letters = [c for c in text if c.isalpha()]
            caps = len(text) <= 150 and len(letters) >= 4 and \
                sum(c.isupper() for c in letters) / len(letters) > 0.8
            self.lines.append((text, bold or caps))
        self.buf = []

    def add(self, s, bold):
        if s:
            self.buf.append((norm_inline(s), bold))

    def walk(self, el, bold=False):
        tag = _tag(el)
        if tag in SKIP:
            self.add_tail(el, bold)
            return
        style = el.get("style") or ""
        if _HIDDEN_STYLE.search(style):
            self.add_tail(el, bold)
            return
        b = bold or tag in ("b", "strong") or tag in HEADING or bool(_BOLD_STYLE.search(style)) \
            or tag == "u" or bool(_UNDER_STYLE.search(style))
        if tag == "table":
            self.flush()
            self.table(el, b)
            self.add_tail(el, bold)
            return
        is_block = tag in BLOCK
        if is_block:
            self.flush()
        if el.text:
            self.add(el.text, b)
        for ch in el:
            self.walk(ch, b)
        if is_block:
            self.flush()
        self.add_tail(el, bold)

    def add_tail(self, el, bold):
        if el.tail:
            self.add(el.tail, bold)

    def table(self, tbl, bold):
        for tr in tbl.iter():
            if _tag(tr) != "tr":
                continue
            cells = []
            row_bold = []
            for td in tr:
                if _tag(td) not in CELL:
                    continue
                sub = Linearizer()
                sub.walk_cell(td)
                txt = " ".join(t for t, _ in sub.lines).strip()
                cells.append(txt)
                row_bold.append(all(h for _, h in sub.lines) if sub.lines else False)
            merged = _merge_cells(cells)
            if merged:
                text = " | ".join(merged)
                nb = [bb for c, bb in zip(cells, row_bold) if c]
                self.lines.append((text, bool(nb) and all(nb) and len(merged) == 1))

    def walk_cell(self, td):
        if td.text:
            self.add(td.text, False)
        for ch in td:
            self.walk(ch, False)
        self.flush()


def _merge_cells(cells):
    """Recolle les cellules « $ », « ) », « % » des tableaux financiers EDGAR."""
    out = []
    pending_prefix = ""
    for c in cells:
        c = c.strip()
        if not c:
            continue
        if c in ("$", "€", "£", "¥", "(", "$(", "($"):
            pending_prefix += c
            continue
        if c in (")", "%", ")%", "%)") and out:
            out[-1] = out[-1] + c
            continue
        out.append((pending_prefix + c) if pending_prefix else c)
        pending_prefix = ""
    return out


def linearize(root):
    lin = Linearizer()
    lin.walk(root)
    lin.flush()
    return lin.lines


def lines_to_text(lines):
    return "\n".join(t for t, _ in lines)


def html_fragment_lines(fragment: str):
    """Linéarise un fragment HTML (valeur d'un bloc de texte d'instance)."""
    if not re.search(r"<[a-zA-Z]", fragment or ""):
        return [(norm_inline(l).strip(), False) for l in (fragment or "").splitlines() if l.strip()]
    root = parse_html(fragment.encode("utf-8"))
    return linearize(root)


# -- localisation en octets bruts ------------------------------------------------

_ENT = r"(?:&[#\w]+;)"
_GAP = r"(?:\s|" + _ENT + r"|<[^>]*>)+"


_TAGS = r"(?:<[^>]*>)*"


def _word_pattern(word):
    parts = []
    for ch in word:
        if ch.isalnum():
            parts.append(re.escape(ch))
        else:
            parts.append(r"(?:" + _ENT + r"|<[^>]*>|[^\w\s<>]){1,3}")
    # un nom peut être coupé par une balise (§9.2)
    return _TAGS.join(parts)


def quote_pattern(quote, max_words=25):
    words = norm_for_match(quote).split(" ")
    words = [w for w in words if w][:max_words]
    if not words:
        return None
    return re.compile(_GAP.join(_word_pattern(w) for w in words), re.S)


def locate_in_raw(raw: bytes, quote: str, start_char=0):
    """Plage d'octets bruts d'une citation dans le fichier en cache, ou None."""
    text = decode(raw)
    pat = quote_pattern(quote)
    if pat is None:
        return None
    m = pat.search(text, start_char)
    if not m and start_char:
        m = pat.search(text)
    if not m:
        return None
    enc = "utf-8"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        enc = "cp1252"
    b0 = len(text[:m.start()].encode(enc, "replace"))
    b1 = b0 + len(text[m.start():m.end()].encode(enc, "replace"))
    return b0, b1
