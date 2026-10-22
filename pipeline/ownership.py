"""D-0071, volet A : déclarations de détention (13F, 13D, 13G) des paires du statut « financé », sans lecture de texte.

Paires de la configuration (point 3) : S un groupe, C un déclarant, au moins une arête de financement en titres. Se
tirent une fois par le client unique, en dépôt complet (`{accession}.txt`), les 13F-HR et 13F-HR/A des financeurs
qui en déposent, et les annexes 13D et 13G dont l'accession figure dans les submissions de S et de C, déposés dans la
période. Ne se lisent que des champs : page de couverture et table d'information des 13F ; nombre d'actions, part de
la catégorie et date de l'événement des 13D et 13G (champs XML, ou gabarit de la page de couverture avant le
2024-12-18). Les noms qu'un dépôt porte (signataires, personnes déclarantes) ne sont jamais lus.

Mesures descriptives, à la perspective du déclarant : `ownership_position` (actions de C que S déclare au 13F, par
date de portefeuille, avec la valeur déclarée) et `ownership_stake` (part de la catégorie et actions déclarées au 13D
ou au 13G, à la date de l'événement). Elles n'entrent ni dans le revenu, ni dans l'exposition, les paires ou
l'annexe F. Une sortie publiée ferme les détentions en actions de la paire (`equity_primary`) au sens de §3.2 ; une
position n'en ouvre jamais.

    python -m pipeline.ownership plan     # dépôts à lire, d'après les submissions en cache (sans tirage)
    python -m pipeline.ownership fetch    # submissions des contreparties, puis dépôts (client unique)
    python -m pipeline.ownership volume   # décomptes, sans valeur
"""
import datetime as dt
import html
import json
import re
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation

from . import cache, config, edgar

BASE = config.CACHE / "ownership"
MANIFEST = BASE / "manifest.jsonl"
F13 = ("13F-HR", "13F-HR/A")
DG = ("SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A", "SCHEDULE 13D", "SCHEDULE 13D/A", "SCHEDULE 13G", "SCHEDULE 13G/A")
HOLDINGS_REPORT = "13F HOLDINGS REPORT"     # un rapport combiné laisse des lignes à un autre gestionnaire


def cfg_own(cfg=None):
    return (cfg or config.load()).get("ownership") or {}


def pairs(cfg=None):
    """Paires (S, C, CIK de C) du point 3, dans l'ordre de la configuration."""
    return [(p["s"], p["c"], str(p["cik"]).zfill(10)) for p in cfg_own(cfg).get("pairs") or []]


def group_cik(g, cfg=None):
    return str(((cfg or config.load()).get("groups") or {})[g]).zfill(10)


def _dec(x):
    try:
        v = Decimal(str(x).replace(",", "").strip())
        return v if v.is_finite() else None
    except (InvalidOperation, AttributeError, TypeError, ValueError):
        return None


# -- dépôts à lire ---------------------------------------------------------------------------------------

def submissions(E, cik, fetch=False):
    """Lignes des submissions d'un déposant, toutes pages ; None si elles ne sont pas en cache et que `fetch` est faux
    (l'assemblage ne tire rien)."""
    if not fetch and not cache.api_path(edgar.cik10(cik), "submissions", E.as_of).exists():
        return None
    return E.submissions(cik)[1]


def plan(E, cfg=None, fetch=False):
    """Dépôts à lire et paires sans submissions. Un 13F se lit une fois par financeur ; un 13D ou un 13G une fois par
    paire. Chaque entrée : kind, s, c (None pour un 13F), cik du déposant, accession, form, filed, report_date."""
    cfg = cfg or config.load()
    o = cfg_own(cfg)
    lo, hi = o["period"]
    filers = set(o.get("thirteen_f_filers") or [])
    subs, out, missing, seen = {}, [], [], set()

    def rows_of(cik):
        if cik not in subs:
            subs[cik] = submissions(E, cik, fetch)
        return subs[cik]
    for s, c, ccik in pairs(cfg):
        scik = group_cik(s, cfg)
        srows = rows_of(scik)
        if srows is None:
            missing.append((s, c))
            continue
        srows = [r for r in srows if lo <= r["filingDate"] <= hi]
        if s in filers:
            for r in srows:
                if r["form"] in F13 and (s, r["accessionNumber"]) not in seen:
                    seen.add((s, r["accessionNumber"]))
                    out.append({"kind": "13f", "s": s, "c": None, "cik": scik, "accession": r["accessionNumber"],
                                "form": r["form"], "filed": r["filingDate"], "report_date": r.get("reportDate") or None})
        crows = rows_of(ccik)
        if crows is None:
            missing.append((s, c))
            continue
        caccs = {r["accessionNumber"] for r in crows if r["form"] in DG}
        for r in srows:
            if r["form"] in DG and r["accessionNumber"] in caccs:
                out.append({"kind": "13dg", "s": s, "c": c, "cik": scik, "subject_cik": ccik,
                            "accession": r["accessionNumber"], "form": r["form"], "filed": r["filingDate"],
                            "report_date": r.get("reportDate") or None})
    return out, missing


def manifest():
    if not MANIFEST.exists():
        return {}
    return {r["accession"]: r for r in (json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l)}


def _append(rec):
    BASE.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def doc_name(f):
    return f"{f['accession']}.txt"


def fetch():
    """Submissions des contreparties qui manquent, puis chaque dépôt du plan, par le client unique ; un dépôt déjà en
    cache ne se tire pas."""
    from . import net
    from .discovery import AS_OF
    cfg = config.load()
    E = edgar.Edgar(net.SecClient(AS_OF, cfg), AS_OF)
    todo, missing = plan(E, cfg, fetch=True)
    print("dépôts au plan :", len(todo), dict(Counter(f["kind"] for f in todo)), "; paires sans submissions :", missing,
          flush=True)
    for f in todo:
        if E.archive_cached(f["cik"], f["accession"], doc_name(f)):
            continue
        try:
            raw = E.archive(f["cik"], f["accession"], doc_name(f))
            rec = dict(f, status="fetched", bytes=len(raw))
        except net.NotCollected as exc:
            rec = dict(f, status="not_collected", reason=str(exc)[:300])
        _append(rec)
        print(f["kind"], f["s"], f["c"], f["accession"], rec["status"], flush=True)


def raw_of(E, f):
    """Dépôt complet en cache, ou None (jamais tiré pendant l'assemblage)."""
    if not E.archive_cached(f["cik"], f["accession"], doc_name(f)):
        return None
    return cache.read(cache.archive_path(edgar.cik10(f["cik"]), f["accession"], doc_name(f)))


# -- lecture des champs ------------------------------------------------------------------------------------

_DOC = re.compile(rb"<DOCUMENT>(.*?)</DOCUMENT>", re.S | re.I)
_TYPE = re.compile(rb"<TYPE>([^\r\n<]+)", re.I)
_XML = re.compile(rb"<XML>(.*?)</XML>", re.S | re.I)
_TEXT = re.compile(rb"<TEXT>(.*?)</TEXT>", re.S | re.I)


def documents(raw):
    """Pièces d'un dépôt complet : [(type, contenu, xml)] ; le contenu XML d'une pièce s'il y en a un, son texte sinon."""
    out = []
    for m in _DOC.finditer(raw):
        body = m.group(1)
        t, x, tx = _TYPE.search(body), _XML.search(body), _TEXT.search(body)
        out.append((t.group(1).decode("ascii", "replace").strip().upper() if t else "",
                    x.group(1) if x else (tx.group(1) if tx else body), bool(x)))
    return out


_ROLE = re.compile(r"^(SUBJECT COMPANY|FILED BY|FILER|REPORTING-OWNER):\s*$", re.M)


def header(raw):
    """En-tête SGML d'un dépôt complet : type, période, date de dépôt, CIK des sociétés visées et des déposants (les
    noms ne se lisent pas)."""
    h = raw.split(b"</SEC-HEADER>", 1)[0].decode("utf-8", "replace")

    def one(k):
        m = re.search(rf"^\s*{k}:\s*(\S.*)$", h, re.M)
        return m.group(1).strip() if m else None
    parts = _ROLE.split(h)
    roles = {}
    for i in range(1, len(parts) - 1, 2):
        m = re.search(r"CENTRAL INDEX KEY:\s*(\d+)", parts[i + 1])
        if m:
            roles.setdefault(parts[i], []).append(m.group(1).zfill(10))
    return {"type": one("CONFORMED SUBMISSION TYPE"), "period": one("CONFORMED PERIOD OF REPORT"),
            "filed": one("FILED AS OF DATE"), "subject": roles.get("SUBJECT COMPANY", []),
            "filed_by": roles.get("FILED BY", []) + roles.get("FILER", []) + roles.get("REPORTING-OWNER", [])}


def _xml(b):
    from lxml import etree
    parser = etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False, no_network=True)
    return etree.fromstring(b.strip(), parser=parser)


def _all(el, *names):
    """Textes non vides des éléments descendants de ces noms locaux (sans espace de noms), dans l'ordre du document."""
    cond = " or ".join(f"local-name()='{n}'" for n in names)
    return [e.text.strip() for e in el.xpath(f".//*[{cond}]") if e.text and e.text.strip()]


def _first(el, *names):
    v = _all(el, *names)
    return v[0] if v else None


def _date(v):
    """Date d'un champ (« 06-30-2026 », « 06/30/2026 », « 20260630 », « June 30, 2026 », « 2026-06-30 »), ou None."""
    if not v:
        return None
    s = re.sub(r"\s+", " ", str(v).strip().replace(" ", " "))
    for fmt in ("%m-%d-%Y", "%m/%d/%Y", "%Y%m%d", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_13f(raw):
    """Page de couverture et table d'information d'un 13F, par leurs champs XML ; le bloc de signature ne se lit pas."""
    docs = documents(raw)
    cover = next((b for t, b, x in docs if x and t.startswith("13F-HR")), None)
    table = next((b for t, b, x in docs if x and "INFORMATION TABLE" in t), None)
    if cover is None:
        return {"ok": False, "reason": "page de couverture XML absente"}
    c = _xml(cover)
    out = {"ok": True, "period": _date(_first(c, "periodOfReport") or _first(c, "reportCalendarOrQuarter")),
           "amendment": (_first(c, "isAmendment") or "").lower() == "true",
           "amendment_type": (_first(c, "amendmentType") or "").upper() or None,
           "report_type": (_first(c, "reportType") or "").upper() or None,
           "confidential": (_first(c, "isConfidentialOmitted") or "").lower() == "true",
           "entries": _first(c, "tableEntryTotal"), "lines": []}
    if out["period"] is None:
        return {"ok": False, "reason": "date de portefeuille illisible"}
    if table is not None:
        for e in _xml(table).xpath(".//*[local-name()='infoTable']"):
            out["lines"].append({"issuer": _first(e, "nameOfIssuer"), "class": _first(e, "titleOfClass"),
                                 "cusip": (_first(e, "cusip") or "").upper(), "value": _first(e, "value"),
                                 "shares": _first(e, "sshPrnamt"), "type": (_first(e, "sshPrnamtType") or "").upper(),
                                 "put_call": _first(e, "putCall")})
    elif out["report_type"] != "13F NOTICE REPORT" and int(_dec(out["entries"]) or 0) > 0:
        return {"ok": False, "reason": "table d'information XML absente"}
    return out


# Gabarit de la page de couverture des annexes 13D et 13G (avant le 2024-12-18) : rangées numérotées, libellés fixés
# par le formulaire ; seuls se lisent le nombre total d'actions, la part de la catégorie et la date de l'événement.
AGG_RX = re.compile(r"aggregate\s+amount\s+beneficially\s+owned\s+by\s+each\s+reporting\s+person\W{0,12}?"
                    r"(\d[\d,]*(?:\.\d+)?|-0-|none|nil)(?![\w-])", re.I)
PCT_RX = re.compile(r"percent\s+of\s+class\s+represented\s+by\s+amount\s+in\s+row\s*\(?\s*\d{1,2}\s*\)?\W{0,12}?"
                    r"(\d{1,3}(?:\.\d+)?)\s*%", re.I)
EVENT_RX = re.compile(r"([A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\W{0,40}?\(?\s*date\s+of\s+event\s+"
                      r"which\s+requires\s+filing", re.I)
_ZERO = {"-0-", "none", "nil"}


def page_text(b):
    """Texte d'une pièce HTML ou texte : balises retirées, entités décodées, espaces réduits."""
    s = b.decode("utf-8", "replace")
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s).replace(" ", " ")).strip()


def parse_13dg(raw):
    """Nombre total d'actions et part de la catégorie de chaque personne déclarante, et date de l'événement, d'une
    annexe 13D ou 13G : champs XML, à défaut gabarit de la page de couverture. Les noms ne se lisent pas."""
    docs = documents(raw)
    h = header(raw)
    form = (h.get("type") or "").upper()
    main = next(((t, b, x) for t, b, x in docs if t.startswith(("SCHEDULE 13", "SC 13"))), None)
    if main is None:
        return {"ok": False, "reason": "pièce principale absente", "header": h}
    t, b, is_xml = main
    out = {"header": h, "form": form or t, "format": "xml" if is_xml else "html"}
    if is_xml:
        root = _xml(b)
        ev = _date(_first(root, "eventDateRequiresFilingThisStatement", "dateOfEvent"))
        persons = root.xpath(".//*[local-name()='coverPageHeaderReportingPersonDetails' or "
                             "local-name()='reportingPersonInfo']")
        rows = []
        for p in persons:
            sh = _dec(_first(p, "reportingPersonBeneficiallyOwnedAggregateNumberOfShares", "aggregateAmountOwned"))
            pc = _dec(_first(p, "classPercent", "percentOfClass"))
            rows.append((sh, pc))
        klass = _first(root, "securitiesClassTitle", "titleOfClassOfSecurities")
    else:
        text = page_text(b)
        ev_m = EVENT_RX.search(text)
        ev = _date(ev_m.group(1).replace(".", "")) if ev_m else None
        sh = [m.group(1) for m in AGG_RX.finditer(text)]
        pc = [m.group(1) for m in PCT_RX.finditer(text)]
        rows = [(Decimal(0) if s.lower() in _ZERO else _dec(s), _dec(p)) for s, p in zip(sh, pc)] if len(sh) == len(pc) else []
        if not rows and sh and not pc:
            rows = [(Decimal(0) if s.lower() in _ZERO else _dec(s), None) for s in sh]
        klass = None
    rows = [(s, p) for s, p in rows if s is not None]
    if not rows:
        return dict(out, ok=False, reason="nombre d'actions illisible")
    if ev is None:
        return dict(out, ok=False, reason="date de l'événement illisible")
    top = max(rows, key=lambda r: (r[0], r[1] or Decimal(0)))
    return dict(out, ok=True, event_date=ev, shares=top[0], percent=top[1], persons=len(rows),
                zero=all(s == 0 for s, _ in rows), klass=klass)


# -- rattachement des lignes de 13F -------------------------------------------------------------------------

STATE_SUFFIX = re.compile(r"\s*/\s*[a-z]{2}$")


def legal_forms(ent_rows):
    """Dénominations légales de la règle des BDC (D-0022 ; nport.legal_forms), et les noms d'entités confirmées qui le
    deviennent sans le suffixe d'État que porte le nom conforme d'EDGAR (« rivian automotive inc / de » : « rivian
    automotive inc »)."""
    from .entities import LEGAL_SUFFIX
    from .nport import legal_forms as lf
    out = dict(lf(ent_rows))
    for r in ent_rows:
        if r["record_kind"] not in ("entity", "alias") or r.get("status") == "pending":
            continue
        n = (r.get("normalized_name") or "").strip()
        g = STATE_SUFFIX.sub("", n)
        if g != n and LEGAL_SUFFIX.search(g) and len(g.split()) >= 2:
            out.setdefault(g, r["entity_id"])
    return out


def attribute_lines(lines, legal, node_at):
    """Nœud de chaque ligne de 13F : l'émetteur commence par une dénomination légale (règle des BDC), puis toute ligne
    au même préfixe CUSIP de six caractères si ce préfixe ne désigne qu'un nœud. `lines` : dictionnaires avec issuer,
    cusip et period ; `node_at(entity_id, date)`. Renvoie [(nœud, règle)] dans l'ordre des lignes."""
    from .nport import attribute
    memo, named = {}, []
    for x in lines:
        n = x.get("issuer") or ""
        if n not in memo:
            memo[n] = attribute(n, legal)[0] if n else None
        e = memo[n]
        named.append(node_at(e, x["period"]) if e else None)
    by_prefix = {}
    for x, nd in zip(lines, named):
        if nd and len(x.get("cusip") or "") >= 6:
            by_prefix.setdefault(x["cusip"][:6], set()).add(nd)
    out = []
    for x, nd in zip(lines, named):
        if nd:
            out.append((nd, "legal_name"))
            continue
        ps = by_prefix.get((x.get("cusip") or "")[:6]) if len(x.get("cusip") or "") >= 6 else None
        out.append((next(iter(ps)), "cusip_prefix") if ps and len(ps) == 1 else (None, None))
    return out


def effective(filings):
    """Lignes en vigueur par date de portefeuille, sur les 13F lus d'un déposant, dans l'ordre de dépôt : un amendement
    RESTATEMENT (ou un nouveau dépôt initial) remplace le dépôt, un amendement NEW HOLDINGS ajoute ses lignes.
    {date: {"lines", "accessions", "filed", "confidential", "report_type"}}."""
    out = {}
    for f in sorted(filings, key=lambda f: (f["filed"], f["accession"])):
        p = f["parsed"]
        d = out.get(p["period"])
        if d is None or not p["amendment"] or p["amendment_type"] != "NEW HOLDINGS":
            d = out[p["period"]] = {"lines": [], "accessions": [], "filed": None, "confidential": False,
                                    "report_type": p["report_type"]}
        d["lines"] += [dict(x, accession=f["accession"], filed=f["filed"]) for x in p["lines"]]
        d["accessions"].append(f["accession"])
        d["filed"] = f["filed"]
        d["confidential"] = d["confidential"] or p["confidential"]
    return out


def thousands(filed, cfg=None):
    """Valeurs des 13F en milliers de dollars avant la date de la configuration (règle de la SEC), en dollars ensuite."""
    return filed < (cfg_own(cfg).get("dollars_from") or "2023-01-03")


def positions_and_exits(s, eff, targets, cfg=None):
    """Positions de S en actions de chaque C de `targets`, par date de portefeuille (lignes SH, hors options), et sorties
    publiées : un rapport complet de S sans ligne de C après un rapport qui en portait, aucun des deux ne déclarant de
    traitement confidentiel (D-0071, point 3). Les lignes portent leur nœud (`node`)."""
    pos, exits, skipped = {}, {}, Counter()
    dates = sorted(eff)
    for d in dates:
        for c in targets:
            ls = [x for x in eff[d]["lines"] if x.get("node") == c and x.get("type") == "SH" and not x.get("put_call")]
            if ls:
                pos[(c, d)] = ls
    for c in targets:
        for i in range(1, len(dates)):
            prev, cur = dates[i - 1], dates[i]
            if (c, prev) not in pos or (c, cur) in pos:
                continue
            if eff[prev]["confidential"] or eff[cur]["confidential"]:
                skipped["confidential"] += 1
            elif eff[cur]["report_type"] != HOLDINGS_REPORT:
                skipped["not_holdings_report"] += 1
            else:
                exits.setdefault(c, []).append({"date": cur, "known": eff[cur]["filed"], "source": "13F",
                                                "accessions": eff[cur]["accessions"], "previous": prev})
    return pos, exits, skipped


# -- cellules, sorties, exclusions --------------------------------------------------------------------------

POSITION_BASIS = ("actions d'un émetteur que le financeur déclare au 13F (table d'information, lignes SH hors options), "
                  "au dernier état des amendements pour la date de portefeuille ; perspective du déclarant, descriptive : "
                  "hors du revenu, de l'exposition, des paires et de l'annexe F (D-0071, point 3)")
STAKE_BASIS = ("part de la catégorie et actions déclarées par le financeur à la page de couverture d'une annexe 13D ou "
               "13G, à la date de l'événement ; perspective du déclarant, descriptive : hors du revenu, de l'exposition, "
               "des paires et de l'annexe F (D-0071, point 3)")


def build(ent_rows, reg, as_of, cfg=None):
    """Cellules ownership_position et ownership_stake, sorties par paire {(S, C): [(date, date de connaissance)]},
    exclusions et décomptes, sur les dépôts en cache (l'assemblage ne tire rien)."""
    from .measures import cell
    cfg = cfg or config.load()
    E = edgar.Edgar(None, as_of)
    todo, missing = plan(E, cfg)
    legal = legal_forms(ent_rows)
    node_at = lambda e, d: reg.group_at(e, d, "as_known")
    man = manifest()
    cells, excl, exits, stats = [], [], {}, Counter()
    targets = {}
    for s, c, _ in pairs(cfg):
        targets.setdefault(s, []).append(c)

    def ex(f, reason, detail):
        excl.append({"exclusion_key": f"{reason}:ownership:{f['accession']}", "item_kind": "filing",
                     "item_key": f"ownership:{f['accession']}", "reason": reason, "detail": detail + " (D-0071, point 3)",
                     "group_id": f["s"], "accession": f["accession"], "content_key": None, "as_of": as_of})
    for s, c in missing:
        excl.append({"exclusion_key": f"not_collected:ownership:{s}:{c}", "item_kind": "query",
                     "item_key": f"ownership:{s}:{c}", "reason": "not_collected",
                     "detail": "submissions de la contrepartie non tirées : déclarations de détention non cherchées "
                               "(D-0071, point 3)", "group_id": s, "accession": None, "content_key": None, "as_of": as_of})
    # 13F : une fois par financeur
    by_s = {}
    for f in (f for f in todo if f["kind"] == "13f"):
        raw = raw_of(E, f)
        if raw is None:
            ex(f, "not_collected", (man.get(f["accession"]) or {}).get("reason") or f"{f['form']} non tiré")
            stats["13f_not_collected"] += 1
            continue
        p = parse_13f(raw)
        if not p["ok"]:
            ex(f, "parse_failed", f"{f['form']} illisible : {p['reason']}")
            stats["13f_parse_failed"] += 1
            continue
        by_s.setdefault(f["s"], []).append(dict(f, parsed=p))
        stats["13f_read"] += 1
    for s, fs in sorted(by_s.items()):
        eff = effective(fs)
        lines = [dict(x, period=d) for d, e in eff.items() for x in e["lines"]]
        for x, (nd, rule) in zip(lines, attribute_lines(lines, legal, node_at)):
            x["node"], x["rule"] = nd, rule
        for d, e in eff.items():
            e["lines"] = [x for x in lines if x["period"] == d]
        pos, ex13, skipped = positions_and_exits(s, eff, targets.get(s, []), cfg)
        stats.update({f"13f_exit_skipped_{k}": v for k, v in skipped.items()})
        nxt = {(c, e["previous"]): e for c, es in ex13.items() for e in es}
        for (c, d), ls in sorted(pos.items()):
            sh = sum(_dec(x["shares"]) or 0 for x in ls)
            val = sum((_dec(x["value"]) or 0) * (1000 if thousands(x["filed"], cfg) else 1) for x in ls)
            cells.append(cell("ownership_position", s, None, d, "as_known", as_of, counterparty=c, value=sh, unit="shares",
                              knowledge_date=max(x["filed"] for x in ls),
                              flags={"perspective": "filer", "value_usd": str(val), "lines": len(ls),
                                     "cusips": sorted({x["cusip"] for x in ls}), "classes": sorted({x["class"] or "" for x in ls}),
                                     "rules": sorted({x["rule"] for x in ls}), "accessions": sorted({x["accession"] for x in ls}),
                                     "value_in_thousands": any(thousands(x["filed"], cfg) for x in ls),
                                     "confidential": eff[d]["confidential"], "basis": POSITION_BASIS,
                                     **({"exit_next": {k: nxt[(c, d)][k] for k in ("date", "known", "accessions")}}
                                        if (c, d) in nxt else {})}))
            stats["positions"] += 1
        for c, es in ex13.items():
            exits.setdefault((s, c), []).extend(es)
    # 13D et 13G : une fois par paire, sur le sens que l'en-tête établit (S déposant, C société visée)
    for f in (f for f in todo if f["kind"] == "13dg"):
        raw = raw_of(E, f)
        if raw is None:
            ex(f, "not_collected", (man.get(f["accession"]) or {}).get("reason") or f"{f['form']} non tiré")
            stats["13dg_not_collected"] += 1
            continue
        p = parse_13dg(raw)
        h = p["header"]
        if f["subject_cik"] not in h["subject"] or f["cik"] not in h["filed_by"]:
            stats["13dg_other_direction"] += 1
            continue
        if not p["ok"]:
            ex(f, "parse_failed", f"{f['form']} illisible : {p['reason']}")
            stats["13dg_parse_failed"] += 1
            continue
        stats[f"13dg_read_{p['format']}"] += 1
        fl = {"perspective": "filer", "form": f["form"], "shares": str(p["shares"]), "persons": p["persons"],
              "format": p["format"], "filed": f["filed"], "class": p.get("klass"), "basis": STAKE_BASIS}
        if p["percent"] is None:
            cells.append(cell("ownership_stake", f["s"], None, p["event_date"], "as_known", as_of, counterparty=f["c"],
                              breakdown=f["accession"], status="not_determinable", nd_reason="not_disclosed",
                              knowledge_date=f["filed"], flags=dict(fl, note="part de la catégorie illisible")))
        else:
            cells.append(cell("ownership_stake", f["s"], None, p["event_date"], "as_known", as_of, counterparty=f["c"],
                              breakdown=f["accession"], value=p["percent"] / 100, unit="pure", knowledge_date=f["filed"],
                              flags=fl))
        stats["stakes"] += 1
        if p["zero"]:
            exits.setdefault((f["s"], f["c"]), []).append({"date": p["event_date"], "known": f["filed"],
                                                           "source": f["form"], "accessions": [f["accession"]]})
    stats["exits"] = sum(len(v) for v in exits.values())
    stats["pairs_with_exit"] = len(exits)
    return cells, exits, excl, dict(stats)


def closing_ends(exits):
    """Sorties d'une paire sous la forme que lit le statut « financé » : (date, date de connaissance)."""
    return {k: [(dt.date.fromisoformat(e["date"]), dt.date.fromisoformat(e["known"])) for e in v] for k, v in exits.items()}


def volume():
    """Décomptes des dépôts au plan, tirés et lus, sans aucune valeur (consignés avant calcul)."""
    from .discovery import AS_OF
    cfg = config.load()
    E = edgar.Edgar(None, AS_OF)
    todo, missing = plan(E, cfg)
    out = {"pairs": len(pairs(cfg)), "pairs_without_submissions": missing,
           "plan": dict(Counter(f"{f['kind']}|{f['s']}" + (f"->{f['c']}" if f["c"] else "") for f in todo))}
    read = Counter()
    for f in todo:
        raw = raw_of(E, f)
        if raw is None:
            read[f"{f['kind']}|not_collected"] += 1
            continue
        if f["kind"] == "13f":
            p = parse_13f(raw)
            read[f"13f|{'ok' if p['ok'] else p['reason']}"] += 1
            if p["ok"]:
                read[f"13f|{p['report_type']}|{'amendment ' + str(p['amendment_type']) if p['amendment'] else 'initial'}"] += 1
                read["13f|confidential"] += int(p["confidential"])
        else:
            p = parse_13dg(raw)
            h = p["header"]
            if f["subject_cik"] not in h["subject"] or f["cik"] not in h["filed_by"]:
                read["13dg|other_direction"] += 1
                continue
            read[f"13dg|{p['format']}|{'ok' if p['ok'] else p['reason']}"] += 1
            read["13dg|zero_shares"] += int(bool(p.get("zero")))
    out["read"] = dict(sorted(read.items()))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if cmd == "plan":
        from .discovery import AS_OF
        todo, missing = plan(edgar.Edgar(None, AS_OF), config.load())
        print(len(todo), "dépôts au plan :", dict(Counter(f"{f['kind']}|{f['s']}" + (f"->{f['c']}" if f["c"] else "")
                                                           for f in todo)), "; paires sans submissions :", missing)
    elif cmd == "fetch":
        fetch()
    elif cmd == "volume":
        print(json.dumps(volume(), ensure_ascii=False, indent=1, default=str))
