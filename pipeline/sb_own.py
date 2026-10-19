"""Volets B et C de D-0058 : dépôts EDGAR propres des entités de SoftBank et des déposants qu'elle contrôle.

La phase 0 lit les submissions complètes de chaque CIK de `softbank_deep` (toutes les pages de `filings.files`,
sans filtre de date, §9.4) et compte les formulaires de la période ; les constats vont dans decisions.md avant
tout catalogue et toute lecture (D-0058, points 4, 5 et 12).

    python -m pipeline.sb_own inventory      # submissions des CIK de softbank_deep -> db/sb_inventory.parquet
    python -m pipeline.sb_own headers        # en-têtes SGML des 13D, 13G, formulaires 3 à 5 et 13F : émetteur visé
    python -m pipeline.sb_own fetch          # pièces des volets B et C, en cache (réseau, client unique)
    python -m pipeline.sb_own prepare        # blocs des volets B et C -> db/sb_blocks.jsonl, sans réseau
"""
import json
import re
import sys
from collections import Counter

import pandas as pd

from . import config, net
from .edgar import Edgar, cik10, parse_sgml_header

AS_OF = "2026-10-07"
INV = config.DB_DIR / "sb_inventory.parquet"
META = config.DB_DIR / "sb_inventory_meta.json"
FILINGS = config.DB_DIR / "sb_filings.parquet"
SCHEDULES = ("SC 13D", "SC 13D/A", "SCHEDULE 13D", "SCHEDULE 13D/A", "SC 13G", "SC 13G/A", "SCHEDULE 13G", "SCHEDULE 13G/A")
OWNERSHIP = ("3", "3/A", "4", "4/A", "5", "5/A")
HOLDINGS = ("13F-HR", "13F-HR/A")
FIELDS = ("accessionNumber", "form", "filingDate", "reportDate", "acceptanceDateTime", "primaryDocument",
          "primaryDocDescription", "items", "size", "isXBRL")


def spec(cfg=None):
    return (cfg or config.load())["softbank_deep"]


def inventory(rate=4.0):
    """Submissions de chaque CIK, par le client unique et journalisé (§9.5) ; une page manquante rend le CIK incomplet."""
    cfg = config.load()
    sp = spec(cfg)
    client = net.SecClient(AS_OF, cfg)
    client.min_interval = 1.0 / rate
    ed = Edgar(client, AS_OF)
    rows, meta = [], {}
    for e in sp["own_ciks"] + sp["controlled"]:
        c = cik10(e["cik"])
        try:
            main, subs, pages, complete = ed.submissions(c)
        except net.NotCollected as exc:
            meta[c] = {"listed_name": e["name"], "status": f"not_collected: {exc}"[:300]}
            continue
        meta[c] = {"listed_name": e["name"], "name": main.get("name"), "role": e.get("role", "own"), "complete": complete,
                   "pages": pages, "filings": len(subs), "tickers": main.get("tickers"), "exchanges": main.get("exchanges"),
                   "entityType": main.get("entityType"), "sic": main.get("sic"), "category": main.get("category"),
                   "formerNames": main.get("formerNames"), "status": "collected"}
        for s in subs:
            rows.append({"cik": c, "filer": main.get("name"), "role": e.get("role", "own"), **{k: s.get(k) for k in FIELDS}})
    df = pd.DataFrame(rows)
    df.to_parquet(INV, index=False)
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print("requêtes", client.stats.get("requests"), "; CIK", len(meta), "; dépôts", len(df))
    return df


def summary(period=None):
    """Comptes par CIK et par formulaire dans la période (constats de la phase 0)."""
    sp = spec()
    start, end = period or sp["period"]
    df = pd.read_parquet(INV)
    meta = json.loads(META.read_text())
    w = df[(df["filingDate"] >= start) & (df["filingDate"] <= end)]
    for c, m in meta.items():
        x = w[w["cik"] == c]
        allx = df[df["cik"] == c]
        span = f"{allx['filingDate'].min()} → {allx['filingDate'].max()}" if len(allx) else "aucun dépôt"
        print(f"{c} {m.get('name') or m['listed_name']} [{m.get('role')}] {m.get('status')} complet={m.get('complete')} "
              f"dépôts={len(allx)} ({span}) ; période={len(x)} {dict(Counter(x['form']).most_common(12))}")
    return w


def _block(text, label):
    """Dénomination et CIK du premier bloc `label` (SUBJECT COMPANY, ISSUER) de l'en-tête SGML."""
    i = text.find(label)
    if i < 0:
        return None, None
    seg = text[i:i + 1500]
    n = re.search(r"COMPANY CONFORMED NAME:\s*([^\r\n<]+)", seg)
    c = re.search(r"CENTRAL INDEX KEY:\s*(\d+)", seg)
    return (n.group(1).strip() if n else None), (cik10(c.group(1)) if c else None)


def headers(rate=4.0):
    """En-tête SGML de chaque dépôt distinct des CIK propres (13D, 13G, formulaires 3 à 5, 13F) dans la période :
    émetteur visé et pièces ; une requête par dépôt, en cache (D-0058, point 4)."""
    cfg = config.load()
    start, end = spec(cfg)["period"]
    df = pd.read_parquet(INV)
    own = df[(df["role"] == "own") & (df["filingDate"] >= start) & (df["filingDate"] <= end)
             & df["form"].isin(SCHEDULES + OWNERSHIP + HOLDINGS)]
    client = net.SecClient(AS_OF, cfg)
    client.min_interval = 1.0 / rate
    ed = Edgar(client, AS_OF)
    rows = []
    for x in own.drop_duplicates("accessionNumber").itertuples(index=False):
        r = {"accession": x.accessionNumber, "form": x.form, "filingDate": x.filingDate, "filer_cik": x.cik,
             "filer": x.filer, "primaryDocument": x.primaryDocument, "state": "collected"}
        try:
            raw = ed.archive(x.cik, x.accessionNumber, f"{x.accessionNumber}-index-headers.html")
        except net.NotCollected as exc:
            rows.append({**r, "state": f"not_collected: {exc}"[:200]})
            continue
        text = raw.decode("utf-8", "replace").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        label = "SUBJECT COMPANY:" if x.form in SCHEDULES else "ISSUER:" if x.form in OWNERSHIP else None
        name, c = _block(text, label) if label else (None, None)
        docs = parse_sgml_header(raw)["documents"]
        rows.append({**r, "issuer": name, "issuer_cik": c,
                     "documents": json.dumps([{k: d.get(k) for k in ("TYPE", "FILENAME", "DESCRIPTION")} for d in docs])})
    out = pd.DataFrame(rows)
    out.to_parquet(FILINGS, index=False)
    print("requêtes", client.stats.get("requests"), "; dépôts", len(out), dict(Counter(out["state"].str[:13])))
    return out


# émetteurs du modèle dans une table d'information 13F (dénomination de l'émetteur, capitales) : groupes de config.yaml
# et déposants contrôlés par SoftBank (D-0058, point 4) ; filtre mécanique avant lecture
MODEL_ISSUERS = [
    ("NVDA", r"\bNVIDIA\b"), ("GOOGL", r"\bALPHABET\b"), ("AMZN", r"\bAMAZON\.?COM\b|\bAMAZON COM\b"),
    ("META", r"\bMETA PLATFORMS\b|\bFACEBOOK\b"), ("MSFT", r"\bMICROSOFT\b"), ("ORCL", r"\bORACLE\b"),
    ("CRWV", r"\bCOREWEAVE\b"), ("SPCX", r"\bSPACE EXPLORATION\b|\bSPACEX\b"), ("AMD", r"\bADVANCED MICRO\b"),
    ("AVGO", r"\bBROADCOM\b|\bAVAGO\b"), ("MRVL", r"\bMARVELL\b"), ("WULF", r"\bTERAWULF\b"), ("CIFR", r"\bCIPHER MINING\b"),
    ("CORZ", r"\bCORE SCIENTIFIC\b"), ("NBIS", r"\bNEBIUS\b|\bYANDEX\b"), ("IREN", r"\bIREN\b|\bIRIS ENERGY\b"),
    ("APLD", r"\bAPPLIED DIGITAL\b|\bAPPLIED BLOCKCHAIN\b"), ("DELL", r"\bDELL TECHNOLOGIES\b"), ("SMCI", r"\bSUPER MICRO\b"),
    ("HUT", r"\bHUT 8\b"), ("GLXY", r"\bGALAXY DIGITAL\b"), ("AKAM", r"\bAKAMAI\b"), ("BLZE", r"\bBACKBLAZE\b"),
    ("RIOT", r"\bRIOT (?:PLATFORMS|BLOCKCHAIN)\b"), ("OWL", r"\bBLUE OWL\b"), ("APO", r"\bAPOLLO GLOBAL\b"), ("BX", r"\bBLACKSTONE\b"),
    ("INTC", r"\bINTEL CORP\b"), ("MU", r"\bMICRON TECHNOLOGY\b"), ("TSM", r"\bTAIWAN SEMICONDUCTOR\b"), ("ASML", r"\bASML\b"),
    ("SKHY", r"\bSK HYNIX\b"), ("ARM", r"\bARM HOLDINGS\b"), ("SBE", r"\bSB ENERGY\b"), ("DBRG", r"\bDIGITALBRIDGE\b"),
    ("SPRINT", r"\bSPRINT CORP\b"), ("FORTRESS", r"\bFORTRESS INVESTMENT GROUP\b"),
]
CONTROLLED = {"0001973239": "ARM", "0002133037": "SBE", "0001679688": "DBRG"}
# entités de SoftBank que le point 9 de D-0058 nomme avec leurs dates (Sprint de 2013 à 2020, Fortress de 2017 à 2024) :
# émetteurs de la première classe du volet B, sans rattachement tant qu'un bloc lu n'affirme pas le contrôle
SB_ENTITY_ISSUERS = {"0000101830": "SPRINT", "0001380393": "FORTRESS"}


def model_issuer(cik=None, name=None, cfg=None, forms=False):
    """Émetteur du modèle : groupe de config.yaml (par CIK), déposant de `softbank_deep.controlled` ou, pour l'ordre des
    13D et 13G, entité de SoftBank du point 9 (Sprint, Fortress) ; les formulaires 3 à 5 s'en tiennent aux émetteurs que
    le point 4 énumère (`forms`). Pour une ligne 13F, par la dénomination de l'émetteur."""
    cfg = cfg or config.load()
    if cik:
        heads = {cik10(v): k for k, v in cfg["groups"].items()}
        return (heads.get(cik10(cik)) or CONTROLLED.get(cik10(cik))
                or (None if forms else SB_ENTITY_ISSUERS.get(cik10(cik))))
    if name:
        u = name.upper()
        return next((g for g, rx in MODEL_ISSUERS if re.search(rx, u)), None)
    return None


C_FILINGS = {   # volet C (D-0058, points 5 et 16) : formulaires lus par déposant contrôlé
    "0002133037": {"forms": ("S-1", "S-1/A"), "docs": (r"^S-1(/A)?$", r"^EX-10", r"^EX-21")},
    "0001973239": {"forms": ("20-F", "424B4", "6-K", "6-K/A"), "docs": (r"^20-F$", r"^424B4$", r"^EX-8", r"^6-K(/A)?$", r"^EX-99")},
    "0001679688": {"accessions": ("0001104659-26-112148", "0001104659-25-125221"), "docs": (r"^8-K$", r"^EX-2\.1$")},
}


def _c_filings(inv):
    out = []
    for c, r in C_FILINGS.items():
        x = inv[inv["cik"] == c]
        if "forms" in r:
            x = x[x["form"].isin(r["forms"])]
        if "accessions" in r:
            x = x[x["accessionNumber"].isin(r["accessions"])]
        x = x[(x["filingDate"] >= spec()["period"][0]) & (x["filingDate"] <= AS_OF)]
        out += [(c, a, f, d) for a, f, d in zip(x["accessionNumber"], x["form"], x["filingDate"])]
    return out


def fetch(rate=4.0):
    """Pièces des volets B et C : documents principaux et EX-99 des 13D et 13G, formulaires 3 et 4 d'un émetteur
    du modèle, tables d'information des 13F ; documents des déposants contrôlés (C_FILINGS). Chaque pièce se
    tire une fois, en cache, par le client unique (§9.5)."""
    cfg = config.load()
    client = net.SecClient(AS_OF, cfg)
    client.min_interval = 1.0 / rate
    ed = Edgar(client, AS_OF)
    f = pd.read_parquet(FILINGS)
    todo = []
    for x in f.itertuples(index=False):
        docs = json.loads(x.documents or "[]")
        if x.form in SCHEDULES:
            todo += [(x.filer_cik, x.accession, d["FILENAME"]) for d in docs
                     if d["TYPE"] in SCHEDULES or str(d["TYPE"]).upper().startswith("EX-99")]
        elif x.form in OWNERSHIP and model_issuer(cik=x.issuer_cik, cfg=cfg) and docs:
            todo.append((x.filer_cik, x.accession, docs[0]["FILENAME"]))
        elif x.form in HOLDINGS:
            todo += [(x.filer_cik, x.accession, d["FILENAME"]) for d in docs if d["TYPE"] == "INFORMATION TABLE"]
    inv = pd.read_parquet(INV)
    for c, acc, form, date in _c_filings(inv):
        raw = ed.archive(c, acc, f"{acc}-index-headers.html")
        rx = [re.compile(p, re.I) for p in C_FILINGS[c]["docs"]]
        todo += [(c, acc, d["FILENAME"]) for d in parse_sgml_header(raw)["documents"]
                 if any(r.search(str(d.get("TYPE") or "")) for r in rx)]
    state = Counter()
    for c, acc, doc in todo:
        try:
            ed.archive(c, acc, doc)
            state["ok"] += 1
        except net.NotCollected:
            state["not_collected"] += 1
    print("pièces", len(todo), dict(state), "; requêtes", client.stats.get("requests"))

# -- blocs des volets B et C (sans réseau) ------------------------------------------------------------------

BLOCKS = config.DB_DIR / "sb_blocks.jsonl"
UNITS_INFO = config.DB_DIR / "sb_units_info.json"
# coupe d'un 13D ou d'un 13G : annexes qui listent administrateurs et dirigeants, signatures (D-0058, point 4)
CUT = re.compile(r"^\W{0,3}(?:(?:schedule|annex|appendix|exhibit)\s+[a-z0-9]{1,3}\b.{0,160}(?:director|officer|managing member|"
                 r"general partner|controlling person|executive)|(?:information (?:concerning|regarding|with respect to) the )?"
                 r"(?:directors and executive officers|executive officers and directors)\b|signatures?\W{0,3}$)", re.I)
CAP_B = 200


def _filer_names():
    return {c: m.get("name") for c, m in json.loads(META.read_text()).items()}


def _xml_text(raw, skip=("signature",)):
    """Texte d'un formulaire XML (13D et 13G de 2025, formulaires 3 et 4) : une ligne « champ : valeur » par
    élément renseigné ; les blocs de signature sont omis."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(raw)
    out = []

    def walk(el, path):
        tag = el.tag.split("}")[-1]
        if any(s in tag.lower() for s in skip):
            return
        txt = (el.text or "").strip()
        if txt:
            out.append(f"{'/'.join(path + [tag])}: {re.sub(r'\s+', ' ', txt)}")
        for ch in el:
            walk(ch, path + [tag])
    walk(root, [])
    return "\n".join(out)


ITEM_HEAD = re.compile(r"^\W{0,3}item\s*(\d{1,2})\b", re.I)
FOOTNOTE = re.compile(r"^\s*(?:\(\d{1,2}\)|\*{1,3}|[†‡]|\[\d{1,2}\]|notes?\s*\d*\s*[:.\-–]|footnotes?\b)", re.I)
BOILER = re.compile(r"remainder of this cover page|deemed to be .?filed|persons who respond to the collection|SEC 1745|"
                    r"currently valid OMB|not required to respond", re.I)


def item_range(form):
    """Items lus : 2 à 7 d'un 13D, 1 à 4 d'un 13G (D-0058, point 4)."""
    return (2, 7) if "13D" in form.upper() else (1, 4)


def _xml_items(raw, lo, hi, notes):
    """XML d'un 13D ou d'un 13G : éléments des items lo à hi, chemin court (« item4/… : valeur ») ; pour un 13G, les
    commentaires des personnes déclarantes, qui sont ses notes. Jamais la page de garde, les personnes autorisées ni
    les signatures."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(raw)
    out, foot = [], []

    def walk(el, path):
        tag = el.tag.split("}")[-1]
        if "signature" in tag.lower() or tag == "authorizedPersons":
            return
        p = path + [tag]
        txt = re.sub(r"\s+", " ", (el.text or "").strip())
        items = [x for x in p if re.fullmatch(r"item\d{1,2}", x)]
        if txt and items and lo <= int(items[0][4:]) <= hi:
            out.append(f"{'/'.join(p[p.index(items[0]):])}: {txt}")
        elif txt and notes and tag == "comments" and "coverPageHeaderReportingPersonDetails" in p:
            if txt not in foot:
                foot.append(txt)
        for ch in el:
            walk(ch, p)
    walk(root, [])
    if foot:
        out += ["Notes de la page de garde :"] + foot
    return "\n".join(out)


def schedule_text(raw, doc, form):
    """Texte d'un 13D (Items 2 à 7) ou d'un 13G (Items 1 à 4 et notes), sans la page de garde ; coupé avant les
    annexes qui listent administrateurs et dirigeants, avant les signatures et, pour un 13G, à l'Item 5. Les notes d'un
    13G sont les notes de bas de page de sa page de garde, hors mentions types (D-0058, points 4 et 17). XML : mêmes
    items, voir `_xml_items`."""
    from . import discovery as D
    lo, hi = item_range(form)
    if doc.lower().endswith(".xml"):
        return _xml_items(raw, lo, hi, notes=hi == 4), "xml"
    text, how = D.plain_text(raw)
    lines = text.split("\n")
    heads = {}
    for i, l in enumerate(lines):
        m = ITEM_HEAD.search(l) if len(l) < 300 else None
        if m:
            heads[i] = int(m.group(1))
    start = next((i for i in sorted(heads) if lo <= heads[i] <= hi), None)
    if start is None:
        return "", how
    end = next((j for j in range(start + 1, len(lines))
                if heads.get(j, 0) > hi or (len(lines[j].strip()) < 200 and CUT.search(lines[j].strip()))), len(lines))
    body = [l for l in lines[start:end] if l.strip()]
    if hi == 4:
        foot = [l.strip() for l in lines[:start] if FOOTNOTE.match(l) and not BOILER.search(l) and len(l.strip()) > 3]
        if foot:
            body += ["Notes de la page de garde :"] + foot
    return "\n".join(body).strip(), how


def holdings_rows(raw):
    """Lignes d'une table d'information 13F : émetteur, catégorie, CUSIP, valeur, nombre, type, option."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(raw)
    rows = []
    for it in root.iter():
        if it.tag.split("}")[-1] != "infoTable":
            continue
        d = {}
        for el in it.iter():
            k = el.tag.split("}")[-1]
            if el.text and el.text.strip() and k not in d:
                d[k] = el.text.strip()
        rows.append(d)
    return rows


def _period_of(raw_header):
    h = parse_sgml_header(raw_header)["header"]
    v = (h.get("CONFORMED PERIOD OF REPORT") or [None])[0]
    return f"{v[:4]}-{v[4:6]}-{v[6:8]}" if v and len(v) == 8 else None


def _block(ck_text, kind, group, cik, acc, form, fdate, doc, extra, sort_key):
    from . import blocks
    from . import discovery as D
    tier, assurance, status = D.form_evidence(form, None)
    return {"content_key": blocks.content_key(ck_text, []), "block_kind": kind, "signal_class": 5, "sort_key": sort_key,
            "group_id": group, "cik": cik10(cik), "accession": acc, "form": form, "filing_date": fdate, "acceptance": None,
            "knowledge_date": fdate, "period_start": None, "period_end": fdate, "document": doc,
            "locator": {"file": doc, "accession": acc, "cik": cik10(cik), "byte_range": None}, "text": ck_text,
            "candidate_facts": [], "chars": len(ck_text), "normalizer_version": config.NORMALIZER_VERSION,
            "delimiter_version": config.DELIMITER_VERSION, "filing_status": status, "assurance_level": assurance,
            "tier": tier, **extra}


def blocks_b(cfg=None):
    """Volet B : 13D et 13G (document principal coupé, pièces EX-99 par leur en-tête), formulaires 3 et 4 d'un émetteur
    du modèle, lignes 13F des émetteurs du modèle. Une unité par dépôt. Ordre : émetteurs du modèle, puis les autres,
    du plus récent au plus ancien ; texte identique lu une fois ; plafond de 200 unités pour l'ensemble du volet
    (D-0058, points 4 et 17)."""
    from . import cache, sections
    from . import blocks as B
    cfg = cfg or config.load()
    f = pd.read_parquet(FILINGS)
    names = _filer_names()
    info, lists = Counter(), {"over_cap": [], "ownership_out_of_scope": [], "holdings_without_model_row": [],
                              "other_forms": []}
    units, seen = [], set()
    # 13D et 13G
    sched = f[f["form"].isin(SCHEDULES)]
    for x in sched.itertuples(index=False):
        docs = json.loads(x.documents or "[]")
        main = next((d for d in docs if d["TYPE"] in SCHEDULES), None)
        if main is None:
            info["schedule_without_main"] += 1
            continue
        raw = cache.read(cache.archive_path(x.filer_cik, x.accession, main["FILENAME"]))
        text, how = schedule_text(raw, main["FILENAME"], x.form)
        text = f"{x.form} déposé le {x.filingDate} par {x.filer} ; émetteur visé : {x.issuer} (CIK {x.issuer_cik})\n" + text
        ck = B.content_key(text, [])
        if ck in seen:
            info["schedule_duplicate"] += 1
            continue
        seen.add(ck)
        model = model_issuer(cik=x.issuer_cik, cfg=cfg)
        extra = {"filer_name": names.get(x.filer_cik) or x.filer, "issuer_name": x.issuer, "issuer_cik": x.issuer_cik,
                 "model_issuer": model, "text_extraction": how, "sb_volet": "B"}
        blk = [_block(text, "ownership_schedule", "NF:SOFTBANK", x.filer_cik, x.accession, x.form, x.filingDate,
                      main["FILENAME"], extra, None)]
        for d in docs:
            if not str(d["TYPE"]).upper().startswith("EX-99"):
                continue
            pth = cache.archive_path(x.filer_cik, x.accession, d["FILENAME"])
            if not pth.exists():
                info["exhibit_not_collected"] += 1
                continue
            r = cache.read(pth)
            try:
                et = sections.first_page(r) if d["FILENAME"].lower().endswith((".htm", ".html")) else r.decode("utf-8", "replace")[:12000]
            except Exception:
                info["exhibit_unreadable"] += 1
                continue
            et = f"{d['TYPE']} du {x.form} déposé le {x.filingDate} par {x.filer} (émetteur visé : {x.issuer})\n" + et
            blk.append(_block(et, "ownership_exhibit_header", "NF:SOFTBANK", x.filer_cik, x.accession, x.form, x.filingDate,
                              d["FILENAME"], dict(extra, exhibit_type=d["TYPE"]), None))
        units.append({"kind": "schedule", "model": model, "date": x.filingDate, "acc": x.accession, "form": x.form,
                      "label": f"{x.form} de {x.filer} sur {x.issuer}", "blocks": blk})
    # formulaires 3 et 4 d'un émetteur du modèle ; les autres sont comptés hors périmètre
    own = f[f["form"].isin(OWNERSHIP)]
    for x in own.itertuples(index=False):
        model = model_issuer(cik=x.issuer_cik, cfg=cfg, forms=True)
        if not model:
            lists["ownership_out_of_scope"].append({"acc": x.accession, "form": x.form, "date": x.filingDate,
                                                    "filer": x.filer, "issuer": x.issuer})
            continue
        docs = json.loads(x.documents or "[]")
        raw = cache.read(cache.archive_path(x.filer_cik, x.accession, docs[0]["FILENAME"]))
        text = f"Formulaire {x.form} déposé le {x.filingDate} par {x.filer} ; émetteur : {x.issuer}\n" + _xml_text(raw)
        units.append({"kind": "ownership", "model": model, "date": x.filingDate, "acc": x.accession, "form": x.form,
                      "label": f"formulaire {x.form} de {x.filer} sur {x.issuer}",
                      "blocks": [_block(text, "ownership_form", "NF:SOFTBANK", x.filer_cik, x.accession, x.form,
                                        x.filingDate, docs[0]["FILENAME"],
                                        {"filer_name": names.get(x.filer_cik) or x.filer, "issuer_name": x.issuer,
                                         "issuer_cik": x.issuer_cik, "model_issuer": model, "sb_volet": "B"}, None)]})
    # 13F : page de garde et lignes des émetteurs du modèle
    for x in f[f["form"].isin(HOLDINGS)].itertuples(index=False):
        docs = json.loads(x.documents or "[]")
        it = next((d for d in docs if d["TYPE"] == "INFORMATION TABLE"), None)
        if it is None:
            info["holdings_without_table"] += 1
            continue
        rows = holdings_rows(cache.read(cache.archive_path(x.filer_cik, x.accession, it["FILENAME"])))
        period = _period_of(cache.read(cache.archive_path(x.filer_cik, x.accession, f"{x.accession}-index-headers.html")))
        keep = [(model_issuer(name=r.get("nameOfIssuer"), cfg=cfg), r) for r in rows]
        keep = [(g, r) for g, r in keep if g]
        info["holdings_rows"] += len(rows)
        info["holdings_rows_model"] += len(keep)
        if not keep:
            lists["holdings_without_model_row"].append({"acc": x.accession, "form": x.form, "date": x.filingDate,
                                                        "filer": x.filer, "rows": len(rows)})
            continue
        unit = "milliers de dollars" if x.filingDate < "2023-01-03" else "dollars"
        lines = [f"{x.form} de {x.filer}, déposé le {x.filingDate}, période du rapport {period} ; {len(rows)} lignes, dont "
                 f"{len(keep)} d'émetteurs du modèle ci-dessous ; valeurs déclarées en {unit} (règle du formulaire selon la "
                 "date de dépôt), à vérifier par le rapport valeur / nombre",
                 "émetteur | catégorie | CUSIP | valeur | nombre | type | option | discrétion"]
        for g, r in keep:
            lines.append(" | ".join(str(r.get(k, "")) for k in ("nameOfIssuer", "titleOfClass", "cusip", "value", "sshPrnamt",
                                                                 "sshPrnamtType", "putCall", "investmentDiscretion")))
        units.append({"kind": "holdings", "model": "13F", "date": x.filingDate, "acc": x.accession, "form": x.form,
                      "label": f"{x.form} de {x.filer}, période {period}",
                      "blocks": [_block("\n".join(lines), "holdings_13f", "NF:SOFTBANK", x.filer_cik, x.accession, x.form,
                                        x.filingDate, it["FILENAME"],
                                        {"filer_name": names.get(x.filer_cik) or x.filer, "period_of_report": period,
                                         "sb_volet": "B", "model_issuers": sorted({g for g, _ in keep})}, None)]})
    # autres formulaires des CIK propres dans la période : comptés, non lus ; les Form D relèvent du bloc form_d
    start, end = spec(cfg)["period"]
    inv = pd.read_parquet(INV)
    inv = inv[(inv["role"] == "own") & (inv["filingDate"] >= start) & (inv["filingDate"] <= end)
              & ~inv["form"].isin(SCHEDULES + OWNERSHIP + HOLDINGS + ("D", "D/A"))]
    for x in inv.drop_duplicates("accessionNumber").itertuples(index=False):
        lists["other_forms"].append({"acc": x.accessionNumber, "form": x.form, "date": x.filingDate, "filer": x.filer})
    # ordre et plafond
    units.sort(key=lambda u: (u["model"] is None, _neg(u["date"]), _neg(u["acc"])))
    out = []
    for n, u in enumerate(units, 1):
        info[f"units:{u['kind']}"] += 1
        if n > CAP_B:
            info[f"over_cap:{u['kind']}"] += 1
            lists["over_cap"].append({"acc": u["acc"], "form": u["form"], "date": u["date"], "label": u["label"],
                                      "blocks": len(u["blocks"])})
            continue
        for k, blk in enumerate(u["blocks"]):
            blk["sort_key"] = f"sbb:{n:05d}:{k:02d}"
            blk["sb_unit"] = n
            out.append(blk)
            info[f"blocks:{blk['block_kind']}"] += 1
    info["ownership_out_of_scope"] = len(lists["ownership_out_of_scope"])
    info["holdings_without_model_row"] = len(lists["holdings_without_model_row"])
    info["other_forms"] = dict(Counter(d["form"] for d in lists["other_forms"]))
    return out, dict(info), lists


def _neg(v):
    """Clé de tri décroissante pour une chaîne (date ISO ou numéro d'accès)."""
    return tuple(-ord(c) for c in str(v))


NOTE_SET = re.compile(r"^notes to (the )?(unaudited )?(condensed )?(consolidated )?(interim )?financial statements(\s*\(unaudited\))?\s*$", re.I)
NOTE_END = re.compile(r"^(condensed )?consolidated (interim )?(balance sheets?|statements? of)\b|of registrant|parent company only|"
                      r"^report of independent|^schedule i\b|^part ii+\b|^item\s+\d{1,2}[a-z]?\.\s|^b\.\s+significant changes\b", re.I)
NOTE_NOISE = re.compile(r"^notes to (the )?(unaudited )?(condensed )?(consolidated )?(interim )?financial statements|^F-\d+$|^\d{1,3}$|"
                        r"^table of contents$|^\(unaudited\)$", re.I)
BACK_COVER = (re.compile(r"^([\d,]+ )?Shares$"), re.compile(r"Common Stock|Ordinary Shares|American Depositary Shares"))
TITLE_SBE = re.compile(r"^Note\s+(\d{1,2})\.\s*(\S.*)$")
TITLE_ARM = re.compile(r"^(\d{1,2})\s+[-–—]\s+(\S.*)$")


def split_notes(raw, title_rx, noise=None):
    """Jeux de notes d'un document HTML : un jeu s'ouvre à un titre courant « Notes to ... Financial Statements » suivi,
    à moins de quinze lignes, du titre de la note 1 ; une note va de son titre (numérotation suivie) au titre suivant ;
    un jeu se ferme au titre d'un état financier, des notes de la société mère, de l'item suivant d'un rapport annuel,
    de la quatrième de couverture d'un prospectus ou de la fin du document. Titres courants (dont `noise`, en-tête au
    nom de la société) et numéros de page retirés (D-0058, point 5)."""
    from . import sections, textnorm
    lines = sections._lines(raw)
    out, i, si = [], 0, -1
    while i < len(lines):
        t = lines[i][0].strip()
        if not (len(t) < 160 and NOTE_SET.match(t)):
            i += 1
            continue
        first = next((j for j in range(i + 1, min(i + 15, len(lines)))
                      if lines[j][1] and (m := title_rx.match(lines[j][0].strip())) and m.group(1) == "1"), None)
        if first is None:
            i += 1
            continue
        si += 1
        notes, expect, cur, j = [], 1, None, first
        while j < len(lines):
            tj = lines[j][0].strip()
            # titre d'un état financier ou des notes de la société mère : ligne de titre, sans deux-points final
            if lines[j][1] and len(tj) < 160 and not tj.endswith(":") and NOTE_END.search(tj) and not NOTE_SET.match(tj):
                break
            if (lines[j][1] and BACK_COVER[0].match(tj) and j + 1 < len(lines) and lines[j + 1][1]
                    and BACK_COVER[1].search(lines[j + 1][0])):
                if cur is not None and cur["lines"] and noise is None and cur["lines"][-1][1]:
                    cur["lines"].pop()                   # nom de la société en tête de la couverture
                break
            m = title_rx.match(tj) if lines[j][1] and len(tj) < 160 else None
            if m and int(m.group(1)) == expect:
                cur = {"number": expect, "title": m.group(2).strip(), "lines": []}
                notes.append(cur)
                expect += 1
            elif m and int(m.group(1)) == 1 and expect > 2:
                break                                    # jeu suivant
            if cur is not None and not NOTE_NOISE.match(tj) and not (noise is not None and lines[j][1] and noise.match(tj)):
                cur["lines"].append(lines[j])
            j += 1
        for n in notes:
            n["text"] = textnorm.lines_to_text(n.pop("lines"))
        out.append({"set": si, "notes": notes})
        i = j
    return out


TOC_ROW = re.compile(r"\.{4,}|\s\d{1,3}\s*$")     # ligne de table des matières : points de conduite, numéro de page


def heading_section(raw, rx):
    """Section d'un prospectus de son titre en capitales (éventuellement sur deux lignes) au titre en capitales
    suivant ; la plus longue des sections candidates, hors lignes de la table des matières (D-0058, point 16)."""
    from . import sections, textnorm
    lines = sections._lines(raw)

    def caps(k):
        s = lines[k][0].strip()
        return lines[k][1] and 0 < len(s) < 120 and s.upper() == s and re.search(r"[A-Z]{4}", s)
    best = None
    for i, (tx, h) in enumerate(lines):
        if not (h and len(tx) < 160 and rx.search(tx.strip())) or TOC_ROW.search(tx):
            continue
        j = i + 1
        while j < len(lines) and caps(j) and len(lines[j][0].strip()) < 40:
            j += 1
        end = next((k for k in range(j, len(lines)) if caps(k)), len(lines))
        if best is None or end - i > best[1] - best[0]:
            best = (i, end)
    if not best:
        return None
    return textnorm.lines_to_text([ln for ln in lines[best[0]:best[1]] if not NOTE_NOISE.match(ln[0].strip())])


ARM_NAME, SBE_NAME, DBRG_NAME = "Arm Holdings plc", "SB Energy, Inc.", "DigitalBridge Group, Inc."
DBRG_CLOSING = "0001104659-26-112148"
CAP_6K = 80
LATEST_20F = "0001973239-26-000097"
RP_TITLES = ("Certain Relationships and Related Party Transactions", "Related Party Transactions")
RP_HEAD = re.compile(r"^CERTAIN RELATIONSHIPS AND RELATED PART")
SBE_HEADER = re.compile(r"^SB Energy, Inc\.$")
SBE_SETS = ("comptes annuels audités", "comptes intermédiaires non audités au 30 juin 2026")


def _cp(name):
    from .graph import normalize_name
    return "CP:" + normalize_name(name)


def arm_6k_rx(cfg=None):
    """Lexique des unités 6-K d'Arm : termes de D-0048 et noms des groupes, laboratoires et non-déposants, jamais
    SoftBank, groupe d'Arm (D-0058, point 5)."""
    cfg = cfg or config.load()
    s = cfg.get("foreign_6k") or {}
    parts = [r"\b" + r"\s+".join(re.escape(w) for w in x.split()) + r"\b" for x in s.get("lexicon") or []]
    names = list(((cfg.get("discovery") or {}).get("lexicon") or {}).get("seed") or []) + list(s.get("group_names") or [])
    for v in (s.get("group_names_by_group") or {}).values():
        names += list(v)
    names += [{"term": "ASML", "ref": "ASML", "case_sensitive": True}, {"term": "SK hynix", "ref": "SKHY"},
              {"term": "TSMC", "ref": "TSM", "case_sensitive": True}, {"term": "Samsung", "ref": "NF:SAMSUNG"}]
    named, seen = [], set()
    for n in names:
        if n.get("ref") == "NF:SOFTBANK" or n["term"] in seen:
            continue
        seen.add(n["term"])
        rx = r"\b" + re.escape(n["term"]) + r"\b"
        named.append(rx if n.get("case_sensitive") else "(?i:" + rx + ")")
    return re.compile("(?i:" + "|".join(parts) + ")|" + "|".join(named))


def _docs(cik, acc):
    from . import cache
    return parse_sgml_header(cache.read(cache.archive_path(cik, acc, f"{acc}-index-headers.html")))["documents"]


def _related_section(raw):
    from .nf_discovery import toc_section
    for title in RP_TITLES:
        s = toc_section(raw, title)
        if s:
            return s, title
    return None, None


def blocks_c(cfg=None):
    """Volet C : documents des déposants contrôlés, lus comme texte de leur propre groupe de contrepartie jusqu'au
    rattachement par extrait (D-0058, points 5 et 16)."""
    from . import cache, regdoc, sections
    from . import discovery as D
    from . import sixk
    cfg = cfg or config.load()
    inv = pd.read_parquet(INV)
    out, info, lists = [], Counter(), {"notes_not_selected": [], "arm_6k_over_cap": []}

    def raw_of(c, acc, doc):
        return cache.read(cache.archive_path(c, acc, doc))

    def add(text, kind, name, c, acc, form, fdate, doc, extra, sk):
        if not text or not text.strip():
            info[f"vide:{kind}"] += 1
            return
        out.append(_block(text, kind, _cp(name), c, acc, form, fdate, doc, dict({"filer_name": name, "sb_volet": "C"}, **extra), sk))
        info[f"{name}:{kind}"] += 1

    # SB Energy : S-1 et ses deux amendements ; prospectus du dernier, EX-10 et EX-21 des trois
    sbe = inv[(inv["cik"] == "0002133037") & inv["form"].isin(["S-1", "S-1/A"])].sort_values("filingDate")
    last = sbe.iloc[-1]
    seen = set()
    for x in sbe.itertuples(index=False):
        for d in _docs(x.cik, x.accessionNumber):
            ty = str(d["TYPE"]).upper()
            if ty.startswith("EX-10") or ty.startswith("EX-21"):
                r = raw_of(x.cik, x.accessionNumber, d["FILENAME"])
                text = sections.first_page(r) if ty.startswith("EX-10") else sections.full_text(r)
                if text in seen:
                    info["SB Energy:duplicate_exhibit"] += 1
                    continue
                seen.add(text)
                kind = "discovery_exhibit_header" if ty.startswith("EX-10") else "discovery_entity_list"
                add(text, kind, SBE_NAME, x.cik, x.accessionNumber, x.form, x.filingDate, d["FILENAME"],
                    {"exhibit_type": ty, "mention_class": "contract" if kind.endswith("header") else "entity_list"},
                    f"sbc:sbe:{x.filingDate}:{d['FILENAME']}")
    raw = raw_of(last.cik, last.accessionNumber, last.primaryDocument)
    add(heading_section(raw, RP_HEAD), "discovery_item_404", SBE_NAME, last.cik, last.accessionNumber, last.form,
        last.filingDate, last.primaryDocument, {"note_label": RP_TITLES[0], "mention_class": "related_party"}, "sbc:sbe:404")
    for s in split_notes(raw, TITLE_SBE, noise=SBE_HEADER):
        label = SBE_SETS[s["set"]] if s["set"] < len(SBE_SETS) else f"jeu {s['set'] + 1}"
        for nt in s["notes"]:
            fam = regdoc.note_kind(nt["title"]) or ("segment_note" if regdoc.SEGMENT.search(nt["title"]) else None)
            add(nt["text"], "discovery_note", SBE_NAME, last.cik, last.accessionNumber, last.form, last.filingDate,
                last.primaryDocument, {"note_label": f"{label}, note {nt['number']}. {nt['title']}", "note_family": fam,
                                       "note_set": s["set"],
                                       "mention_class": "related_party" if fam == "related_party_note" else "note"},
                f"sbc:sbe:s{s['set'] + 1}n{nt['number']:02d}")
    # Arm : 20-F (toutes les notes du dernier ; familles retenues des précédents), Item 7.B, pièce 8.1 du dernier,
    # parties liées du 424B4, unités 6-K
    arm = inv[inv["cik"] == "0001973239"]
    for x in arm[arm["form"] == "20-F"].sort_values("filingDate").itertuples(index=False):
        raw = raw_of(x.cik, x.accessionNumber, x.primaryDocument)
        latest = x.accessionNumber == LATEST_20F
        for s in split_notes(raw, TITLE_ARM):
            for nt in s["notes"]:
                fam = regdoc.note_kind(nt["title"]) or ("segment_note" if regdoc.SEGMENT.search(nt["title"]) else None)
                if not latest and fam is None:
                    info["Arm:note_not_selected"] += 1
                    lists["notes_not_selected"].append({"acc": x.accessionNumber, "form": x.form, "date": x.filingDate,
                                                        "note": f"{nt['number']}. {nt['title']}"})
                    continue
                add(nt["text"], "discovery_note", ARM_NAME, x.cik, x.accessionNumber, x.form, x.filingDate, x.primaryDocument,
                    {"note_label": f"20-F {x.reportDate}, note {nt['number']}. {nt['title']}", "note_family": fam,
                     "mention_class": "related_party" if fam == "related_party_note" else "note"},
                    f"sbc:arm:{x.filingDate}:s{s['set'] + 1}n{nt['number']:02d}")
        add(sections.item_7b_20f(raw), "discovery_item_404", ARM_NAME, x.cik, x.accessionNumber, x.form, x.filingDate,
            x.primaryDocument, {"note_label": f"20-F {x.reportDate}, Item 7.B", "mention_class": "related_party"},
            f"sbc:arm:{x.filingDate}:7b")
        if latest:
            for d in _docs(x.cik, x.accessionNumber):
                if str(d["TYPE"]).upper().startswith("EX-8"):
                    add(sections.full_text(raw_of(x.cik, x.accessionNumber, d["FILENAME"])), "discovery_entity_list", ARM_NAME,
                        x.cik, x.accessionNumber, x.form, x.filingDate, d["FILENAME"],
                        {"exhibit_type": d["TYPE"], "mention_class": "entity_list"}, f"sbc:arm:{x.filingDate}:ex8")
    for x in arm[arm["form"] == "424B4"].itertuples(index=False):
        sec, title = _related_section(raw_of(x.cik, x.accessionNumber, x.primaryDocument))
        add(sec, "discovery_item_404", ARM_NAME, x.cik, x.accessionNumber, x.form, x.filingDate, x.primaryDocument,
            {"note_label": f"424B4, {title}", "mention_class": "related_party"}, "sbc:arm:424b4")
    rx = arm_6k_rx(cfg)
    wins = []
    for x in arm[arm["form"].isin(["6-K", "6-K/A"])].sort_values(["filingDate", "accessionNumber"], ascending=False).itertuples(index=False):
        for d in _docs(x.cik, x.accessionNumber):
            ty = str(d["TYPE"]).upper()
            if not (ty.startswith("6-K") or ty.startswith("EX-99")) or not d["FILENAME"].lower().endswith((".htm", ".html", ".txt")):
                continue
            text, _ = D.plain_text(raw_of(x.cik, x.accessionNumber, d["FILENAME"]))
            paras = sixk.paragraphs(text)
            for k, (a, b) in enumerate(sixk.windows(paras, rx)):
                wins.append((x, d, k, "\n".join(paras[a:b])))
    seen6 = set()
    n6 = 0
    for x, d, k, text in wins:
        if text in seen6:
            info["Arm:6k_duplicate"] += 1
            continue
        seen6.add(text)
        if n6 >= CAP_6K:
            info["Arm:6k_over_cap"] += 1
            lists["arm_6k_over_cap"].append({"acc": x.accessionNumber, "form": x.form, "date": x.filingDate,
                                             "file": d["FILENAME"], "window": k})
            continue
        n6 += 1
        add(text, "montage_text", ARM_NAME, x.cik, x.accessionNumber, x.form, x.filingDate, d["FILENAME"],
            {"exhibit_type": d["TYPE"], "window": k, "montage": "sb_arm_6k"}, f"sbc:arm6k:{n6:05d}")
    info["Arm:6k_windows"] = len(wins)
    # DigitalBridge : items du 8-K de réalisation (hors 9.01) ; en-tête de la convention de fusion, pièce 2.1 du 8-K de
    # l'accord (D-0058, points 5 et 16)
    for acc in ("0001104659-26-112148", "0001104659-25-125221"):
        x = inv[(inv["cik"] == "0001679688") & (inv["accessionNumber"] == acc)].iloc[0]
        items = {}
        if acc == DBRG_CLOSING:
            raw = raw_of(x.cik, acc, x.primaryDocument)
            plain, _ = D.plain_text(raw)
            m = re.search(r"(?m)^Introductory Note\s*$", plain)
            e = re.search(r"(?m)^Item\s+\d\.\d\d\b", plain[m.end():]) if m else None
            if m and e:
                items["introductory_note"] = plain[m.start():m.end() + e.start()].strip()
            items.update(sections.eight_k_sections(raw))
        for it, text in items.items():
            if it.startswith("9."):
                continue
            add(text, "montage_text", DBRG_NAME, x.cik, acc, x.form, x.filingDate, x.primaryDocument,
                {"item": it, "montage": "sb_dbrg_8k"}, f"sbc:dbrg:{x.filingDate}:{it}")
        for d in _docs(x.cik, acc):
            if str(d["TYPE"]).upper() == "EX-2.1":
                add(sections.first_page(raw_of(x.cik, acc, d["FILENAME"])), "discovery_exhibit_header", DBRG_NAME, x.cik, acc,
                    x.form, x.filingDate, d["FILENAME"], {"exhibit_type": d["TYPE"], "mention_class": "contract"},
                    f"sbc:dbrg:{x.filingDate}:ex21")
    return out, dict(info), lists


def prepare():
    """Blocs des volets B et C, écrits d'un coup (remplacement atomique) ; volume compté par sorte et par déposant."""
    b, ib, lb = blocks_b()
    c, ic, lc = blocks_c()
    out = b + c
    tmp = BLOCKS.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for x in out:
            fh.write(json.dumps(x, ensure_ascii=False, default=str) + "\n")
    tmp.replace(BLOCKS)
    vol = Counter()
    chars = Counter()
    keys = set()
    for x in out:
        k = (x["sb_volet"], x["block_kind"], x["filer_name"])
        if x["content_key"] in keys:
            continue
        keys.add(x["content_key"])
        vol[k] += 1
        chars[k] += x["chars"]
    UNITS_INFO.write_text(json.dumps({"B": ib, "C": ic, "lists": {**lb, **lc},
                                      "volume": {" | ".join(k): [vol[k], chars[k]] for k in vol}},
                                     ensure_ascii=False, indent=1, default=str))
    for k in sorted(vol):
        print(" | ".join(k), vol[k], chars[k])
    print("B", ib)
    print("C", ic)
    print("blocs", len(out), "textes distincts", len(keys), "caractères", sum(chars.values()))



def exclusions(as_of):
    """Unités des volets B et C au-delà de leur plafond, formulaires hors périmètre ou non lus, notes non retenues des
    20-F antérieurs d'Arm (D-0058, points 4, 5 et 17)."""
    if not UNITS_INFO.exists():
        return []
    lists = json.loads(UNITS_INFO.read_text()).get("lists") or {}
    out = []

    def ex(key, reason, detail, group, acc):
        out.append({"exclusion_key": f"{reason}:sb_own:{key}", "item_kind": "document", "item_key": f"sb_own:{key}",
                    "reason": reason, "detail": detail, "group_id": group, "accession": acc, "content_key": None,
                    "as_of": as_of})
    for d in lists.get("over_cap") or []:
        ex(d["acc"], "not_processed", f"{d['label']} ({d['date']}) : unité du volet B au-delà du plafond de 200 (D-0058, "
           "point 4)", "NF:SOFTBANK", d["acc"])
    for d in lists.get("ownership_out_of_scope") or []:
        ex(d["acc"], "out_of_scope", f"formulaire {d['form']} de {d['filer']} sur {d['issuer']} ({d['date']}) : émetteur hors "
           "du modèle (D-0058, point 4)", "NF:SOFTBANK", d["acc"])
    for d in lists.get("holdings_without_model_row") or []:
        ex(d["acc"], "out_of_scope", f"{d['form']} de {d['filer']} ({d['date']}) : {d['rows']} lignes, aucune d'un émetteur du "
           "modèle (D-0058, point 4)", "NF:SOFTBANK", d["acc"])
    for d in lists.get("other_forms") or []:
        ex(d["acc"], "out_of_scope", f"{d['form']} de {d['filer']} ({d['date']}) : formulaire compté, non lu (D-0058, point 4)",
           "NF:SOFTBANK", d["acc"])
    for d in lists.get("notes_not_selected") or []:
        ex(f"{d['acc']}#{d['note']}", "out_of_scope", f"20-F d'Arm du {d['date']}, note {d['note']} : hors des familles lues "
           "dans les rapports antérieurs au dernier (D-0058, point 5)", _cp(ARM_NAME), d["acc"])
    for d in lists.get("arm_6k_over_cap") or []:
        ex(f"{d['acc']}/{d['file']}#{d['window']}", "not_processed", "fenêtre 6-K d'Arm au-delà du plafond de 80 unités "
           "(D-0058, point 5 ; D-0048, point 6)", _cp(ARM_NAME), d["acc"])
    return out

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "inventory":
        inventory()
        summary()
    elif cmd == "summary":
        summary()
    elif cmd == "headers":
        headers()
    elif cmd == "fetch":
        fetch()
    elif cmd == "prepare":
        prepare()
    else:
        print(__doc__)
