"""Lecture des instances XBRL et de leurs métadonnées (§7.2, §9.3).

L'identité sémantique d'un fait : concept sans version, entité, période, unité,
dimensions canoniques, cadre comptable, périmètre de présentation. La version de
taxonomie est un attribut (§7.2). Une instance extraite est déjà à l'échelle : on
ne réapplique pas scale ; decimals est une précision, pas un multiplicateur (§7.3).
"""
import json
import re
from decimal import Decimal, InvalidOperation

from lxml import etree

NS_XBRLI = "http://www.xbrl.org/2003/instance"
NS_XBRLDI = "http://xbrl.org/2006/xbrldi"
NS_LINK = "http://www.xbrl.org/2003/linkbase"
NS_XLINK = "http://www.w3.org/1999/xlink"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_IX = "http://www.xbrl.org/2013/inlineXBRL"

_STD = [
    (re.compile(r"^http://fasb\.org/(us-gaap|srt|us-types|us-roles)/(\d{4}(?:-\d\d-\d\d)?)$"), None),
    (re.compile(r"^http://xbrl\.sec\.gov/([a-z\-]+)/(\d{4}(?:[-q]\d+)?(?:-\d\d-\d\d)?)$"), None),
    (re.compile(r"^http://xbrl\.ifrs\.org/taxonomy/(\d{4}-\d\d-\d\d)/(ifrs-full|ifrs-smes)$"), "ifrs"),
]
_FRAMEWORK = {"us-gaap": "us_gaap", "srt": "srt", "dei": "dei", "ifrs-full": "ifrs"}


def split_namespace(ns, nsmap_rev):
    """Renvoie (préfixe canonique, version) ; une extension garde le préfixe du déposant."""
    for rx, kind in _STD:
        m = rx.match(ns or "")
        if m:
            if kind == "ifrs":
                return m.group(2), m.group(1)
            return m.group(1), m.group(2)
    if ns == "http://www.xbrl.org/2003/iso4217":
        return "iso4217", None
    return nsmap_rev.get(ns, "ext"), None


SEC_STD_PREFIXES = {"dei", "ecd", "ffd", "country", "currency", "exch", "naics", "sic", "stpr",
                    "cyd", "rxp", "spac", "snj", "vip", "oef", "sro", "sbs", "cef", "invest",
                    "iso4217", "us-types", "us-roles"}


def framework_of(prefix):
    if prefix in _FRAMEWORK:
        return _FRAMEWORK[prefix]
    if prefix in SEC_STD_PREFIXES:
        return "other"
    return "extension"


def _qname_text(text, nsmap, nsmap_rev):
    """Convertit 'prefix:Local' d'un membre ou d'un axe en préfixe canonique sans version."""
    text = (text or "").strip()
    if ":" in text:
        p, local = text.split(":", 1)
        ns = nsmap.get(p)
        cp, _ = split_namespace(ns, nsmap_rev) if ns else (p, None)
        return f"{cp}:{local}"
    return text


def parse_decimal(text):
    t = (text or "").strip()
    if not t:
        return None
    try:
        return Decimal(t)
    except InvalidOperation:
        return None


def _unit_string(u, nsmap):
    def meas(el):
        txt = (el.text or "").strip()
        return txt.split(":", 1)[1] if ":" in txt else txt
    div = u.find(f"{{{NS_XBRLI}}}divide")
    if div is not None:
        num = [meas(m) for m in div.find(f"{{{NS_XBRLI}}}unitNumerator").iter(f"{{{NS_XBRLI}}}measure")]
        den = [meas(m) for m in div.find(f"{{{NS_XBRLI}}}unitDenominator").iter(f"{{{NS_XBRLI}}}measure")]
        return "*".join(num) + "/" + "*".join(den)
    return "*".join(meas(m) for m in u.iter(f"{{{NS_XBRLI}}}measure"))


_CURRENCY = re.compile(r"^[A-Z]{3}$")


def parse_instance(data: bytes, text_block_concepts=None):
    """Parse une instance (traditionnelle ou extraite *_htm.xml).

    Renvoie (facts, text_blocks, meta). Chaque fait porte son rang d'occurrence dans
    le fichier, stable d'une exécution à l'autre (§7.2).
    """
    parser = etree.XMLParser(huge_tree=True, recover=True, remove_comments=True)
    root = etree.fromstring(data, parser)
    nsmap = {k: v for k, v in (root.nsmap or {}).items() if k}
    nsmap_rev = {v: k for k, v in nsmap.items()}
    contexts = {}
    for ctx in root.iter(f"{{{NS_XBRLI}}}context"):
        cid = ctx.get("id")
        ent = ctx.find(f"{{{NS_XBRLI}}}entity")
        ident = ent.find(f"{{{NS_XBRLI}}}identifier") if ent is not None else None
        dims = []
        for holder in (ent, ctx.find(f"{{{NS_XBRLI}}}scenario")):
            if holder is None:
                continue
            for em in holder.iter(f"{{{NS_XBRLDI}}}explicitMember"):
                dims.append((_qname_text(em.get("dimension"), nsmap, nsmap_rev),
                             _qname_text(em.text, nsmap, nsmap_rev)))
            for tm in holder.iter(f"{{{NS_XBRLDI}}}typedMember"):
                val = "".join(tm.itertext()).strip()
                dims.append((_qname_text(tm.get("dimension"), nsmap, nsmap_rev), "typed:" + val))
        per = ctx.find(f"{{{NS_XBRLI}}}period")
        inst = per.find(f"{{{NS_XBRLI}}}instant") if per is not None else None
        if inst is not None:
            ptype, start, end = "instant", None, inst.text.strip()[:10]
        else:
            s = per.find(f"{{{NS_XBRLI}}}startDate") if per is not None else None
            e = per.find(f"{{{NS_XBRLI}}}endDate") if per is not None else None
            ptype = "duration"
            start = s.text.strip()[:10] if s is not None else None
            end = e.text.strip()[:10] if e is not None else None
        dims.sort()
        contexts[cid] = {
            "cik": (ident.text or "").strip() if ident is not None else None,
            "period_type": ptype, "start": start, "end": end,
            "dims": dims,
        }
    units = {u.get("id"): _unit_string(u, nsmap) for u in root.iter(f"{{{NS_XBRLI}}}unit")}
    facts, blocks = [], []
    rank = 0
    skip_ns = {NS_XBRLI, NS_LINK}
    for el in root:
        if not isinstance(el.tag, str):
            continue
        qn = etree.QName(el)
        if qn.namespace in skip_ns:
            continue
        ctx_ref = el.get("contextRef")
        if ctx_ref is None:
            continue  # tuples et autres éléments sans contexte : ignorés
        rank += 1
        prefix, version = split_namespace(qn.namespace, nsmap_rev)
        concept = f"{prefix}:{qn.localname}"
        ctx = contexts.get(ctx_ref, {})
        unit_ref = el.get("unitRef")
        is_nil = el.get(f"{{{NS_XSI}}}nil") in ("true", "1")
        rec = {
            "occ_rank": rank, "concept": concept, "concept_ns": qn.namespace,
            "taxonomy_version": version, "framework": framework_of(prefix),
            "fact_id": el.get("id"), "context_id": ctx_ref,
            "cik": ctx.get("cik"), "period_type": ctx.get("period_type"),
            "period_start": ctx.get("start"), "period_end": ctx.get("end"),
            "dims": ctx.get("dims", []), "is_nil": is_nil,
        }
        if unit_ref is not None:
            unit = units.get(unit_ref, unit_ref)
            dec = el.get("decimals")
            rec.update({
                "unit": unit, "currency": unit if _CURRENCY.match(unit or "") else None,
                "value": None if is_nil else parse_decimal(el.text),
                "decimals": None if dec in (None, "INF") else int(dec),
                "decimals_inf": dec == "INF",
                "value_text": None,
            })
            facts.append(rec)
        else:
            text = el.text or ""
            is_block = (text_block_concepts is not None and concept in text_block_concepts) or \
                       (text_block_concepts is None and (qn.localname.endswith("TextBlock")
                                                         or re.search(r"<(p|div|table|span)\b", text[:2000], re.I)))
            if is_block:
                rec["text"] = text
                blocks.append(rec)
            else:
                rec.update({"unit": None, "currency": None, "value": None, "decimals": None,
                            "decimals_inf": None, "value_text": text.strip()[:4000]})
                facts.append(rec)
    meta = {"nsmap": nsmap, "n_contexts": len(contexts), "n_units": len(units)}
    return facts, blocks, meta


def canonical_dims(dims):
    return json.dumps([list(d) for d in sorted(dims)], separators=(",", ":"))


# -- linkbases --------------------------------------------------------------------

def _loc_concept(href):
    frag = href.split("#", 1)[-1]
    if "_" in frag:
        p, local = frag.split("_", 1)
        return f"{p}:{local}"
    return frag


def parse_linkbases(files):
    """files : dict nom -> bytes (schéma .xsd et linkbases). Renvoie rôles, présentation,
    calcul et libellés. Les préfixes sont ceux des identifiants d'éléments."""
    roles, pres, calc, labels = {}, {}, {}, {}
    parser = etree.XMLParser(huge_tree=True, recover=True, remove_comments=True)
    for name, data in files.items():
        if not name.lower().endswith((".xml", ".xsd")):
            continue
        try:
            root = etree.fromstring(data, parser)
        except etree.XMLSyntaxError:
            continue
        if root is None:
            continue
        for rt in root.iter(f"{{{NS_LINK}}}roleType"):
            d = rt.find(f"{{{NS_LINK}}}definition")
            roles[rt.get("roleURI")] = (d.text or "").strip() if d is not None else ""
        for kind, arc_tag, store in (("presentationLink", "presentationArc", pres),
                                     ("calculationLink", "calculationArc", calc)):
            for link in root.iter(f"{{{NS_LINK}}}{kind}"):
                role = link.get(f"{{{NS_XLINK}}}role")
                locs = {}
                for loc in link.iter(f"{{{NS_LINK}}}loc"):
                    locs[loc.get(f"{{{NS_XLINK}}}label")] = _loc_concept(loc.get(f"{{{NS_XLINK}}}href", ""))
                arcs = store.setdefault(role, [])
                for arc in link.iter(f"{{{NS_LINK}}}{arc_tag}"):
                    frm = locs.get(arc.get(f"{{{NS_XLINK}}}from"))
                    to = locs.get(arc.get(f"{{{NS_XLINK}}}to"))
                    if frm is None or to is None:
                        continue
                    order = float(arc.get("order") or 0)
                    if kind == "presentationLink":
                        arcs.append((frm, to, order, arc.get("preferredLabel")))
                    else:
                        arcs.append((frm, to, order, float(arc.get("weight") or 1)))
        for link in root.iter(f"{{{NS_LINK}}}labelLink"):
            locs = {}
            for loc in link.iter(f"{{{NS_LINK}}}loc"):
                locs[loc.get(f"{{{NS_XLINK}}}label")] = _loc_concept(loc.get(f"{{{NS_XLINK}}}href", ""))
            labs = {}
            for lab in link.iter(f"{{{NS_LINK}}}label"):
                labs.setdefault(lab.get(f"{{{NS_XLINK}}}label"), []).append(
                    (lab.get(f"{{{NS_XLINK}}}role"), "".join(lab.itertext()).strip()))
            for arc in link.iter(f"{{{NS_LINK}}}labelArc"):
                c = locs.get(arc.get(f"{{{NS_XLINK}}}from"))
                for role, text in labs.get(arc.get(f"{{{NS_XLINK}}}to"), []):
                    labels.setdefault(c, {})[(role or "").rsplit("/", 1)[-1]] = text
    return {"roles": roles, "pres": pres, "calc": calc, "labels": labels}


def parse_metalinks(data: bytes):
    """MetaLinks.json : types, définitions, références ASC, rapports (rôles et catégories)."""
    j = json.loads(data)
    inst = j.get("instance", {})
    out = {"tags": {}, "reports": {}, "std_ref": j.get("std_ref", {})}
    for _, body in inst.items():
        for tag, t in body.get("tag", {}).items():
            lang = t.get("lang", {}).get("en-us", {}).get("role", {})
            out["tags"][tag.replace("_", ":", 1)] = {
                "xbrltype": t.get("xbrltype"), "crdr": t.get("crdr"),
                "label": lang.get("label"), "terse": lang.get("terseLabel"),
                "documentation": lang.get("documentation"),
                "presentation": t.get("presentation", []), "auth_ref": t.get("auth_ref", []),
            }
        for rid, r in body.get("report", {}).items():
            out["reports"][rid] = {"role": r.get("role"), "longName": r.get("longName"),
                                   "shortName": r.get("shortName"), "menuCat": r.get("menuCat"),
                                   "groupType": r.get("groupType"), "subGroupType": r.get("subGroupType"),
                                   "order": r.get("order")}
    return out


def parse_filing_summary(data: bytes):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(data, parser)
    reps = []
    for r in root.iter("Report"):
        g = lambda t: (r.findtext(t) or "").strip()
        reps.append({"short": g("ShortName"), "long": g("LongName"), "role": g("Role"),
                     "menu": g("MenuCategory"), "position": g("Position"), "html": g("HtmlFileName")})
    return reps


def text_block_concepts_from_metalinks(ml):
    return {c for c, t in ml["tags"].items() if (t.get("xbrltype") or "").endswith("textBlockItemType")}


def statement_kind(role_definition):
    """Classe un rôle « 0000003 - Statement - CONSOLIDATED BALANCE SHEETS »."""
    d = (role_definition or "").lower()
    parts = [p.strip() for p in d.split(" - ")]
    cat = parts[1] if len(parts) >= 3 else ""
    title = " - ".join(parts[2:]) if len(parts) >= 3 else parts[-1]
    if cat == "statement" or "statement" in cat:
        if "parenthetical" in title:
            return "statement_parenthetical"
        if "cash flow" in title:
            return "cash_flow"
        if "balance sheet" in title or "financial position" in title or "financial condition" in title:
            return "balance_sheet"
        if "comprehensive income" in title and "income statement" not in title and \
                "operations and comprehensive" not in title and "income and comprehensive" not in title:
            return "comprehensive_income"
        if any(k in title for k in ("operations", "income", "earnings")):
            return "income_statement"
        if any(k in title for k in ("equity", "stockholders", "shareholders", "mezzanine")):
            return "equity_statement"
        return "statement_other"
    if cat in ("disclosure",):
        if "(details" in title:
            return "note_details"
        if "(tables" in title:
            return "note_tables"
        if "(policies" in title:
            return "note_policies"
        return "note"
    if cat == "document":
        return "cover"
    return "other"
