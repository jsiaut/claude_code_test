"""Bloc `form_d` de §14 : montants vendus par offre de Form D (D-0041).

Deux populations, distinguées par le CIK de l'émetteur (annexe D) :

- **émetteur du périmètre** (`issuer_is_subject` vrai) : Form D déposés par une entité d'un
  groupe de `config.yaml` (têtes de groupe, prédécesseurs, entités à CIK du registre, X.AI Corp.
  compris). Ce sont des faits sur cette entité (§10.3), rattachés au groupe qui la contient à la
  date du dépôt, dans chaque vue ;
- **véhicule tiers** (`issuer_is_subject` faux) : émetteur hors des groupes dont la dénomination,
  ou la description des titres offerts, nomme un laboratoire (OpenAI, Anthropic) ou un groupe qui
  ne dépose encore aucun rapport périodique (SpaceX et xAI, CoreWeave avant leur premier 10-Q),
  selon les termes et les règles de casse du lexique de la découverte. Il mesure une demande
  d'exposition secondaire et n'entre jamais dans une mesure de financement du nœud sous-jacent ;
  sa série se publie par véhicule et par trimestre, tant que le sous-jacent ne dépose pas.

Mesure : `form_d_offering_amount`, par offre (clé : CIK de l'émetteur et date de première vente),
sur le dernier dépôt connu : un D et ses D/A ne se somment jamais, chaque dépôt `replaces` le
précédent. Le montant est vendu cumulé depuis la première vente, jamais une valorisation, et il
peut inclure du non monétaire : ce n'est pas du numéraire primaire sans autre pièce.
"""
import datetime as dt
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

import pandas as pd

from . import cache, config, discovery, edgar, net
from .graph import normalize_name
from .links import relation
from .measures import cell

NONE = "none"
FILINGS = config.DB_DIR / "formd_filings.parquet"
PERIODIC = ("10-K", "10-Q", "10-KT", "10-QT", "20-F", "40-F")
BASIS = ("montant vendu cumulé depuis la première vente de l'offre, sur le dernier dépôt connu (un D et ses D/A ne se "
         "somment pas) ; jamais une valorisation ; peut inclure du non monétaire, ce n'est pas du numéraire primaire "
         "sans autre pièce (§14)")


def _d(x):
    if x in (None, "", NONE) or (isinstance(x, float) and x != x):
        return None
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def _txt(el, path):
    x = el.find(path) if el is not None else None
    return x.text.strip() if x is not None and x.text and x.text.strip() else None


def amount(s):
    try:
        v = Decimal(str(s).replace(",", "").strip())
        return v if v.is_finite() else None
    except (InvalidOperation, AttributeError, TypeError):
        return None


def parse(raw):
    """Champs utiles d'un Form D (XML de la soumission électronique)."""
    root = ET.fromstring(raw)
    pi = root.find("primaryIssuer")
    od = root.find("offeringData")
    tof = od.find("typeOfFiling") if od is not None else None
    fs = tof.find("dateOfFirstSale") if tof is not None else None
    sec = od.find("typesOfSecuritiesOffered") if od is not None else None
    types = sorted(c.tag for c in sec if (c.text or "").strip().lower() == "true") if sec is not None else []
    related = []
    for rp in root.iter("relatedPersonInfo"):
        n = rp.find("relatedPersonName")
        related.append(" ".join(x for x in (_txt(n, "firstName"), _txt(n, "lastName")) if x and x.lower() not in ("n/a", "-", "(none)")))
    others = [(_txt(i, "cik"), _txt(i, "entityName")) for i in root.iter("issuer")]
    return {"submission_type": _txt(root, "submissionType"),
            "issuer_cik": str(int(_txt(pi, "cik"))) if _txt(pi, "cik") else None,
            "issuer_name": _txt(pi, "entityName"),
            "other_issuers": json.dumps(others) if others else None,
            "is_amendment": (_txt(tof, "newOrAmendment/isAmendment") or "").lower() == "true",
            "previous_accession": _txt(tof, "newOrAmendment/previousAccessionNumber"),
            "first_sale": _txt(fs, "value"),
            "yet_to_occur": (_txt(fs, "yetToOccur") or "").lower() == "true",
            "industry_group": _txt(od, "industryGroup/industryGroupType"),
            "fund_type": _txt(od, "industryGroup/investmentFundInfo/investmentFundType"),
            "securities": ";".join(types),
            "securities_other": _txt(sec, "descriptionOfOtherType"),
            "business_combination": (_txt(od, "businessCombinationTransaction/isBusinessCombinationTransaction")
                                     or "").lower() == "true",
            "total_offering_amount": _txt(od, "offeringSalesAmounts/totalOfferingAmount"),
            "total_amount_sold": _txt(od, "offeringSalesAmounts/totalAmountSold"),
            "total_remaining": _txt(od, "offeringSalesAmounts/totalRemaining"),
            "sales_clarification": _txt(od, "offeringSalesAmounts/clarificationOfResponse"),
            "investors": _txt(od, "investors/totalNumberAlreadyInvested"),
            "signature_date": _txt(od, "signatureBlock/signature/signatureDate"),
            "related_persons": ";".join(r for r in related if r)}


# -- périmètre : qui dépose, et depuis quand ------------------------------------------------

def first_periodic(cfg=None):
    """Date du premier rapport périodique (10-K, 10-Q, 20-F, 40-F) déposé par chaque groupe,
    prédécesseurs compris ; None si le groupe n'en a jamais déposé."""
    cfg = cfg or config.load()
    f = pd.read_parquet(config.DB_DIR / "filings.parquet", columns=["group_id", "form", "filingDate"])
    f = f[f["form"].isin(PERIODIC)]
    out = {g: None for g in cfg["groups"]}
    for g, d in f.groupby("group_id")["filingDate"].min().items():
        out[g] = _d(d)
    return out


def non_filer(ref, t, first):
    """Le sous-jacent ne dépose aucun rapport périodique à la date t : un laboratoire ne dépose
    jamais (§10.4) ; un groupe, tant que son premier rapport périodique n'est pas déposé."""
    if str(ref).startswith("LAB:"):
        return True
    if ref not in first:
        return False
    return first[ref] is None or first[ref] > t


def vehicle_lexicon(cfg, first, start):
    """Termes du lexique dont la cible peut être un non-déposant pendant la période : les
    laboratoires, et les groupes dont le premier rapport périodique suit le début de la série."""
    lex = discovery.lexicon(cfg)
    keep = []
    for e in lex:
        r = e["ref"]
        if str(r).startswith("LAB:") or (r in first and (first[r] is None or first[r] > start)):
            keep.append(e)
    return keep


def targets(text, lex):
    """Cibles nommées dans un texte, en mots entiers, avec les règles de casse du lexique."""
    out = set()
    if not isinstance(text, str) or not text:
        return out
    for e in lex:
        rx = re.escape(e["term"])
        if re.search(r"(?<![\w.])" + rx + r"(?![\w])", text, 0 if e["case"] else re.I):
            out.add(e["ref"])
    return out


def series_start(p0=None):
    """Début de la série des véhicules : le plus ancien début de fenêtre allongée des groupes."""
    p0 = p0 or json.load(open(config.DB_DIR / "phase0.json", encoding="utf-8"))
    starts = [c["window"]["extended_start"] for c in p0["calendars"].values() if c.get("window")]
    return _d(min(starts))


# -- collecte ----------------------------------------------------------------------------

def collect(as_of=discovery.AS_OF, rate=4.0):
    """Form D des deux populations : ceux des entités des groupes (submissions, puis XML ; une
    quarantaine de requêtes) et ceux des véhicules, tirés par la recherche plein texte de la
    découverte et déjà en cache (aucune requête). Écrit FILINGS."""
    cfg = config.load()
    client = net.SecClient(as_of, cfg)
    client.min_interval = 1.0 / rate
    ed = edgar.Edgar(client, as_of)
    rows = []

    def one(cik, acc, form, fdate, population, doc="primary_doc.xml"):
        r = {"population": population, "cik": str(int(cik)), "adsh": acc, "form": form, "file_date": str(fdate)[:10],
             "file": doc, "parse_state": "parsed", "reason": None}
        try:
            raw = ed.archive(cik, acc, doc)
            r.update(parse(raw))
        except net.NotCollected as exc:
            r.update(parse_state="not_collected", reason=str(exc)[:300])
        except ET.ParseError as exc:
            r.update(parse_state="parse_failed", reason=f"ParseError: {exc}"[:300])
        rows.append(r)

    # 1. émetteurs du périmètre : têtes de groupe et prédécesseurs (submissions de la phase 0)
    fil = pd.read_parquet(config.DB_DIR / "filings.parquet")
    d = fil[fil["form"].isin(["D", "D/A"])]
    for x in d.itertuples(index=False):
        one(x.filer_cik, x.accessionNumber, x.form, x.filingDate, "subject")
    # entités à CIK des groupes hors des têtes (X.AI Corp. et filiales du registre) : leurs submissions
    heads = {str(int(c)) for c in fil["filer_cik"].dropna().unique()}
    extra = sorted(c for c in discovery.group_ciks(cfg) if c not in heads)
    sub_status = {}
    for c in extra:
        try:
            _, subs, pages, complete = ed.submissions(c)
        except net.NotCollected as exc:
            sub_status[c] = f"not_collected: {exc}"[:200]
            continue
        sub_status[c] = "complete" if complete else "incomplete"
        for s in subs:
            if s.get("form") in ("D", "D/A"):
                one(c, s["accessionNumber"], s["form"], s["filingDate"], "subject")
    # 2. véhicules : Form D vérifiés de la recherche plein texte (en cache)
    v = pd.read_parquet(config.DB_DIR / "discovery_formd.parquet")
    v = v[v["status"].isin(["verified", "no_mention"])]
    for x in v.itertuples(index=False):
        one(x.cik, x.adsh, x.form, x.file_date, "vehicle_candidate", x.file or "primary_doc.xml")
    df = pd.DataFrame(rows).drop_duplicates(["adsh", "file"])
    df.to_parquet(FILINGS, index=False)
    meta = {"as_of": as_of, "requests": client.stats["requests"], "extra_ciks": sub_status,
            "rows": int(len(df)), "by_population": df["population"].value_counts().to_dict(),
            "parse_states": df["parse_state"].value_counts().to_dict()}
    (config.DB_DIR / "formd_collect.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print(json.dumps(meta, ensure_ascii=False))
    return df


# -- offres et cellules -----------------------------------------------------------------

def offerings(df):
    """Regroupe les dépôts par offre : CIK de l'émetteur et date de première vente ; un D/A sans
    date reprend celle du dépôt qu'il amende (previousAccessionNumber)."""
    df = df[df["parse_state"] == "parsed"]
    df = df.astype(object).where(df.notna(), None)          # valeurs absentes : None, jamais NaN
    by_acc = {r["adsh"]: r for r in df.to_dict("records")}

    def fs(r, seen=()):
        if r.get("first_sale"):
            return r["first_sale"]
        p = r.get("previous_accession")
        if p and p in by_acc and p not in seen:
            return fs(by_acc[p], seen + (p,))
        return None
    out = {}
    for r in df.to_dict("records"):
        f = fs(r)
        key = f"{r['issuer_cik']}|{f or 'yet_to_occur'}"
        out.setdefault(key, []).append(r)
    for k in out:
        out[k].sort(key=lambda r: (r["file_date"], r["adsh"]))
    return out


def homonyms(cfg):
    """Émetteurs écartés : le terme y désigne autre chose qu'une exposition à la cible (homonyme, ou
    promoteur du fonds), décision motivée par le dépôt lui-même."""
    return {str(int(h["cik"])): h for h in ((cfg.get("form_d") or {}).get("excluded_issuers") or [])}


def quarter_ends(start, end):
    out = []
    y, m = start.year, ((start.month - 1) // 3 + 1) * 3
    while True:
        last = (dt.date(y + (m == 12), 1 if m == 12 else m + 1, 1) - dt.timedelta(days=1))
        if last > end:
            return out
        if last >= start:
            out.append(last)
        y, m = (y + 1, 3) if m == 12 else (y, m + 3)


def build(reg, as_of, cfg=None, p0=None):
    """Cellules form_d_offering_amount, relations `replaces` et exclusions du bloc."""
    cfg = cfg or config.load()
    as_of_d = _d(as_of)
    if not FILINGS.exists():
        return [], [], [], {"collected": False}
    df = pd.read_parquet(FILINGS)
    df = df.astype(object).where(df.notna(), None)          # valeurs absentes : None, jamais NaN
    df = df[df["file_date"].map(lambda x: _d(x) is not None and _d(x) <= as_of_d)]
    first = first_periodic(cfg)
    start = series_start(p0)
    vlex = vehicle_lexicon(cfg, first, start)
    homo = homonyms(cfg)
    groups = set(cfg["groups"])
    # entité du registre par CIK (têtes de groupe « cik:… », filiales « name:… » portant leur CIK)
    eid_of = {}
    for eid, e in reg.entities.items():
        if e.get("cik") not in (None, "", NONE) and str(e.get("cik")).strip().isdigit():
            eid_of.setdefault(str(int(e["cik"])), eid)
    cells, rels, excl = [], [], []
    stats = {"collected": True, "subject_offerings": 0, "vehicle_offerings": 0, "vehicles": set(),
             "vehicle_cells": 0, "subject_cells": 0, "by_ref": {}}

    def ex(key, reason, detail, acc=None, group=None):
        excl.append({"exclusion_key": f"{reason}:formd:{key}", "item_kind": "filing", "item_key": f"formd:{key}",
                     "reason": reason, "detail": detail, "group_id": group, "accession": acc, "content_key": None,
                     "as_of": as_of})
    for r in df[df["parse_state"] != "parsed"].to_dict("records"):
        ex(r["adsh"], r["parse_state"], f"Form D de l'émetteur {r['cik']} : {r['reason']}", r["adsh"])
    offs = offerings(df)
    for key, fl in sorted(offs.items()):
        last = fl[-1]
        icik = last["issuer_cik"]
        # un D et ses D/A : chaque dépôt remplace le précédent (§8.2, §14)
        for a, b in zip(fl[1:], fl[:-1]):
            rels.append(relation("formd:" + a["adsh"], "formd:" + b["adsh"], "replaces", key, "resolved_rule",
                                 "§14 : chaque dépôt d'une offre de Form D remplace le précédent ; jamais sommés"))
        first_sale = next((r["first_sale"] for r in fl if r.get("first_sale")), None)
        base_flags = {"issuer_cik": icik, "issuer_name": last["issuer_name"], "offering_key": key,
                      "filings": [r["adsh"] for r in fl], "basis": BASIS,
                      "business_combination": any(r["business_combination"] for r in fl),
                      "securities": last["securities"], "industry_group": last["industry_group"],
                      "fund_type": last["fund_type"]}
        # émetteur du périmètre : CIK d'une entité des groupes, ou dénomination légale d'une entité du
        # registre qui appartient à un groupe (résolution par nom normalisé, comme toute contrepartie, §10.2)
        eid = eid_of.get(icik) or eid_of.get(str(last["cik"]))
        by_name = reg.names.get(normalize_name(last["issuer_name"] or ""))
        if eid is None and by_name and any(m["ref"] in groups for m in reg.members.get(by_name, [])):
            eid = by_name
        in_group = bool(eid) and any(m["ref"] in groups for m in reg.members.get(eid, []))
        if in_group or any(r["population"] == "subject" for r in fl):
            # faits sur l'entité émettrice, rattachés à son groupe à la date du dernier dépôt, dans chaque vue
            ld = _d(last["file_date"])
            for view in ("as_known", "revised"):
                g = reg.group_at(eid, ld, view) if eid else None
                if g is None:
                    ex(key, "pending_entity", f"Form D de {last['issuer_name']} (CIK {icik}) : entité hors du registre")
                    break
                ext = _d(((p0 or {}).get("calendars", {}).get(g, {}).get("window") or {}).get("extended_start")) or start
                if ld < ext:
                    ex(key + f"|{view}", "out_of_scope",
                       f"offre {key} de {last['issuer_name']} : dernier dépôt ({ld}) avant la fenêtre allongée ({ext})",
                       last["adsh"], g)
                    continue
                v = amount(last["total_amount_sold"])
                cells.append(cell("form_d_offering_amount", g, first_sale, ld, view, as_of, breakdown=key,
                                  value=v, unit="USD" if v is not None else None,
                                  status="computed" if v is not None else "not_determinable",
                                  nd_reason=None if v is not None else "not_disclosed", knowledge_date=ld,
                                  flags=dict(base_flags, issuer_is_subject=True, accession=last["adsh"],
                                             total_offering_amount=last["total_offering_amount"],
                                             investors=last["investors"])))
                stats["subject_cells"] += 1
            stats["subject_offerings"] += 1
            continue
        # véhicule : cible nommée par la dénomination ou par la description des titres offerts
        refs = set()
        for r in fl:
            refs |= targets(r["issuer_name"], vlex) | targets(r.get("securities_other"), vlex)
        if not refs:
            continue
        if icik in homo:
            h = homo[icik]
            ex(key, "out_of_scope", f"{last['issuer_name']} (CIK {icik}) : {h['evidence']} ({h['decision']})", last["adsh"])
            continue
        stats["vehicle_offerings"] += 1
        stats["vehicles"].add(icik)
        vname = last["issuer_name"]
        cp = "CP:" + normalize_name(vname)
        for ref in sorted(refs):
            n = 0
            for t in quarter_ends(start, as_of_d):
                known = [r for r in fl if _d(r["file_date"]) <= t]
                if not known or not non_filer(ref, t, first):
                    continue
                k = known[-1]
                v = amount(k["total_amount_sold"])
                cells.append(cell("form_d_offering_amount", ref, first_sale, t, "as_known", as_of, counterparty=cp,
                                  breakdown=key, value=v, unit="USD" if v is not None else None,
                                  status="computed" if v is not None else "not_determinable",
                                  nd_reason=None if v is not None else "not_disclosed", knowledge_date=_d(k["file_date"]),
                                  flags=dict(base_flags, issuer_is_subject=False, accession=k["adsh"],
                                             vehicle=vname, multiple_targets=len(refs) > 1,
                                             securities_other=k.get("securities_other"))))
                n += 1
            stats["vehicle_cells"] += n
            stats["by_ref"][ref] = stats["by_ref"].get(ref, 0) + (1 if n else 0)
    stats["vehicles"] = len(stats["vehicles"])
    stats["series_start"] = str(start)
    stats["first_periodic"] = {g: str(d) if d else None for g, d in first.items()}
    return cells, rels, excl, stats


if __name__ == "__main__":
    import sys
    collect(*(sys.argv[1:2] or [discovery.AS_OF]))
