"""Bloc `lender_liabilities` (D-0047) : le passif des BDC de l'univers de D-0045.

Mesures de bilan par véhicule et date de bilan (vue as_known) : ratio de couverture publié, levier
qui s'en déduit, passif total ÷ actif net. Offres de rachat (SC TO-I) : demandes et acceptations
lues dans l'amendement final, une cellule par offre. Événements F14 à F16 de l'annexe F, une cellule
par véhicule et date ou par offre, jamais de somme entre véhicules. Règles de D-0047, fixées avant
tout calcul et toute lecture.

    python -m pipeline.lender_liabilities extract     # archives en cache -> db/bdc_liabilities.parquet
    python -m pipeline.lender_liabilities inventory   # listes de dépôts EDGAR des véhicules (submissions)
    python -m pipeline.lender_liabilities fetch       # documents principaux des amendements des offres
    python -m pipeline.lender_liabilities classify    # classe des titres visés par chaque offre utile
    python -m pipeline.lender_liabilities show N K    # unités de lecture des offres, K à partir de N
    python -m pipeline.lender_liabilities check F     # contrôle des relevés d'un fichier JSONL
"""
import datetime as dt
import io
import json
import re
import sys
import zipfile
from decimal import Decimal

import pandas as pd

from . import cache, config, lender, net
from .lender_portfolio import _d, as_known

OUT = config.DB_DIR / "bdc_liabilities.parquet"
INFO = config.DB_DIR / "bdc_liabilities.json"
INV = config.DB_DIR / "bdc_filings_inventory.parquet"
OFFERS = config.DB_DIR / "bdc_tender_offers.parquet"
WORK = config.ROOT / "work" / "tenders"
READINGS = WORK / "tender_readings.jsonl"
ANNOUNCEMENTS = WORK / "announcements.jsonl"
AS_OF = "2026-10-07"
CONCEPTS = {"Liabilities": "liabilities", "AssetsNet": "assets_net", "StockholdersEquity": "stockholders_equity",
            "Assets": "assets", "InvestmentCompanySeniorSecurityIndebtednessAssetCoverageRatio": "coverage_raw"}
OPEN_DAYS = 60                      # offre sans amendement, SC TO-I de moins de 60 jours : réputée ouverte (D-0047, point 9)
BOUND_TOLERANCE = Decimal("0.98")   # dette de premier rang au principal, passif à la valeur comptable (D-0047, point 9)
SIGN_TOLERANCE = Decimal("0.01")
MEASURE_IDS = ("bdc_liab_asset_coverage", "bdc_liab_debt_to_net_assets", "bdc_liab_liabilities_to_net_assets")
TENDER_IDS = ("bdc_tender_acceptance_ratio", "bdc_tender_demand_ratio")


def _cfg():
    return config.load().get("lender_liabilities") or {}


def _f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


# -- faits de bilan ---------------------------------------------------------------------------

def extract():
    """Faits non dimensionnels à la date du bilan du dépôt, dans num.tsv de chaque archive
    (D-0047, point 4) ; seul le concept standard du ratio de couverture sert."""
    tags = {t.encode() for t in CONCEPTS}
    rows, info = [], {"lines_malformed": {}, "archives": [], "duplicates": 0}
    for p in lender.archives():
        raw = cache.read(p)
        sha = cache.sha256(raw)
        zf = zipfile.ZipFile(io.BytesIO(raw))
        with zf.open("datasets/sub.tsv") as fh:
            sub = pd.read_csv(fh, sep="\t", dtype=str, keep_default_na=False, quoting=3)
        sub = sub.drop_duplicates("adsh").set_index("adsh")
        per = {a: str(r["period"])[:8] for a, r in sub.iterrows()}
        facts, bad = {}, 0
        with zf.open("datasets/num.tsv") as fh:
            head = fh.readline().decode().rstrip("\n").split("\t")
            ix = {k: i for i, k in enumerate(head)}
            for line in fh:
                f = line.split(b"\t", 3)
                if f[1] not in tags:
                    continue
                f = line.decode("utf-8", "replace").rstrip("\n").split("\t")
                if len(f) != len(head):
                    bad += 1
                    continue
                a, t, ver = f[ix["adsh"]], f[ix["tag"]], f[ix["version"]]
                if f[ix["segments"]] or f[ix["qtrs"]] != "0" or per.get(a) != f[ix["ddate"]]:
                    continue
                if not ver.split("/")[0] in ("us-gaap", "us-gaap-sup"):
                    continue       # concepts propres aux déclarants : non utilisés
                col = CONCEPTS[t]
                d = facts.setdefault(a, {})
                if col in d:
                    info["duplicates"] += 1
                    continue       # le premier fait l'emporte
                d[col] = _f(f[ix["value"]])
                if col == "coverage_raw":
                    d["coverage_uom"] = f[ix["uom"]]
        for a in per:
            s = sub.loc[a]
            rows.append({"archive": p.name[:-4], "archive_sha256": sha, "adsh": a, "cik": str(s["cik"]).zfill(10),
                         "name": s["name"], "former": s.get("former", ""), "form": s["form"], "period": per[a],
                         "filed": str(s["filed"]), **{c: None for c in list(CONCEPTS.values()) + ["coverage_uom"]},
                         **facts.get(a, {})})
        info["lines_malformed"][p.name[:-4]] = bad
        info["archives"].append({"archive": p.name[:-4], "sha256": sha, "filings": len(per)})
        print(p.name, len(per), "dépôts", flush=True)
    df = pd.DataFrame(rows).drop_duplicates("adsh", keep="first")   # une accession dans deux archives
    df.to_parquet(OUT, index=False)
    prev = json.loads(INFO.read_text()) if INFO.exists() else {}
    INFO.write_text(json.dumps({**prev, **info}, default=str))
    return df


def coverage_value(raw, cfg=None):
    """Ratio de couverture publié, ramené en ratio par la règle d'échelle (D-0047, point 4).
    Renvoie (valeur, bande) ; valeur None hors des bandes."""
    if raw is None or raw != raw:
        return None, None
    sc = (cfg or _cfg()).get("coverage_scale") or {}
    v = Decimal(str(raw))
    lo, hi = sc.get("ratio", [1, 100])
    if Decimal(str(lo)) <= v < Decimal(str(hi)):
        return v, "ratio"
    lo, hi = sc.get("percent", [100, 1000])
    if Decimal(str(lo)) <= v < Decimal(str(hi)):
        return v / 100, "percent"
    lo, hi = sc.get("per_thousand", [1000, 10000])
    if Decimal(str(lo)) <= v < Decimal(str(hi)):
        return v / 1000, "per_thousand"
    return None, "out_of_band"


def _present(x):
    return x is not None and x == x


def net_assets(r):
    """Actif net (D-0047, points 4 et 9) : AssetsNet, à défaut StockholdersEquity. Une valeur de signe
    contraire à actif total − passif total, et de même valeur absolue à 1 % près, est une erreur de
    signe du déclarant : sa valeur absolue sert. Renvoie (valeur, concept, correction)."""
    col = next((c for c in ("assets_net", "stockholders_equity") if _present(r.get(c))), None)
    if col is None:
        return None, None, None
    v = Decimal(str(r[col]))
    if v < 0 and _present(r.get("assets")) and _present(r.get("liabilities")):
        ident = Decimal(str(r["assets"])) - Decimal(str(r["liabilities"]))
        if ident > 0 and abs(ident - abs(v)) <= SIGN_TOLERANCE * ident:
            return abs(v), col, "sign_corrected"
    return v, col, None


def vehicle_cells(r, as_of, cfg):
    """Les trois mesures de bilan d'un véhicule à une date (D-0047, points 4 et 9)."""
    from .measures import cell
    subj, date, kd = f"cik:{r['cik']}", _d(r["period"]), _d(r["filed"])
    base = {"accession": r["adsh"], "archive": r["archive"], "archive_sha256": r["archive_sha256"],
            "form": r["form"], "vehicle": r["name"]}
    out = []

    def put(measure, **kw):
        out.append(cell(measure, subj, None, date, "as_known", as_of, unit="pure", knowledge_date=kd, **kw))
    na, na_col, na_fix = net_assets(r)
    li = Decimal(str(r["liabilities"])) if _present(r.get("liabilities")) else None
    cov, band = coverage_value(r["coverage_raw"], cfg)
    # contrôle par l'identité du bilan : la dette de premier rang ne dépasse pas le passif total, donc
    # couverture >= 1 + actif net ÷ passif total (D-0047, point 9)
    bound = (1 + na / li) if (cov is not None and na is not None and na > 0 and li is not None and li > 0) else None
    conflict = bound is not None and cov < bound * BOUND_TOLERANCE
    if not _present(r["coverage_raw"]):
        put("bdc_liab_asset_coverage", status="not_determinable", nd_reason="not_tagged",
            flags={**base, "note": "ratio de couverture standard non balisé à la date du bilan"})
    elif cov is None:
        put("bdc_liab_asset_coverage", status="not_determinable", nd_reason="parse_failed",
            flags={**base, "published": str(r["coverage_raw"]), "scale": band,
                   "note": "valeur publiée hors des bandes d'échelle (D-0047, point 4)"})
    elif conflict:
        put("bdc_liab_asset_coverage", status="not_determinable", nd_reason="conflicting",
            flags={**base, "published": str(r["coverage_raw"]), "scale": band, "lower_bound": str(round(bound, 4)),
                   "note": "ratio publié sous 1 + actif net ÷ passif total : ce n'est pas le ratio du véhicule "
                           "(souvent le seuil légal balisé à sa place ; D-0047, point 9)"})
    else:
        put("bdc_liab_asset_coverage", value=cov, status="computed",
            flags={**base, "published": str(r["coverage_raw"]), "scale": band,
                   "lower_bound": str(round(bound, 4)) if bound is not None else "not_testable"})
    if cov is None or conflict:
        put("bdc_liab_debt_to_net_assets", status="not_determinable",
            nd_reason="not_tagged" if not _present(r["coverage_raw"]) else ("conflicting" if conflict else "parse_failed"),
            flags=base)
    elif cov <= 1:
        put("bdc_liab_debt_to_net_assets", status="not_determinable", nd_reason="denominator_nonpositive",
            flags={**base, "coverage": str(cov)})
    else:
        put("bdc_liab_debt_to_net_assets", value=1 / (cov - 1), numerator=Decimal(1), denominator=cov - 1,
            status="computed", flags={**base, "coverage": str(cov), "derived_from": "bdc_liab_asset_coverage"})
    if na is None or li is None:
        put("bdc_liab_liabilities_to_net_assets", status="not_determinable", nd_reason="not_tagged",
            flags={**base, "note": "passif total ou actif net non balisé à la date du bilan"})
    elif na <= 0:
        put("bdc_liab_liabilities_to_net_assets", status="not_determinable", nd_reason="denominator_nonpositive",
            flags={**base, "net_assets_concept": na_col})
    else:
        put("bdc_liab_liabilities_to_net_assets", value=li / na, numerator=li, denominator=na, status="computed",
            flags={**base, "net_assets_concept": na_col, **({"net_assets_sign": na_fix} if na_fix else {})})
    return out


# -- inventaire EDGAR ---------------------------------------------------------------------------

def _client(rate=4.0):
    c = net.SecClient(AS_OF, config.load())
    c.min_interval = 1.0 / rate
    return c


def _submissions(client, cik):
    """Liste des dépôts d'un véhicule, en cache ; pages anciennes tirées si la liste récente ne remonte
    pas au début de la fenêtre (D-0047, point 5)."""
    start = (_cfg().get("tenders") or {}).get("window", ["2022-10-01"])[0]
    p = config.CACHE / "edgar" / "submissions" / f"CIK{cik}.json.zst"
    if p.exists():
        sub = json.loads(cache.read(p))
    else:
        raw, _ = client.get(f"https://data.sec.gov/submissions/CIK{cik}.json")
        cache.write(p, raw)
        sub = json.loads(raw)
    pages = [sub["filings"]["recent"]]
    for fdesc in sub["filings"].get("files") or []:
        if fdesc.get("filingTo", "9999") < start:
            continue
        q = config.CACHE / "edgar" / "submissions" / (fdesc["name"] + ".zst")
        if q.exists():
            pages.append(json.loads(cache.read(q)))
        else:
            raw, _ = client.get(f"https://data.sec.gov/submissions/{fdesc['name']}")
            cache.write(q, raw)
            pages.append(json.loads(raw))
    return sub, pages


def inventory(rate=4.0):
    """Dépôts EDGAR de chaque véhicule de l'univers : formulaire, date, document principal, items."""
    df = pd.read_parquet(OUT)
    ciks = sorted(df["cik"].unique())
    client = _client(rate)
    rows, failed = [], []
    for n, cik in enumerate(ciks):
        try:
            sub, pages = _submissions(client, cik)
        except net.NotCollected as exc:
            failed.append({"cik": cik, "error": str(exc)})
            continue
        for pg in pages:
            keys = ("form", "accessionNumber", "filingDate", "primaryDocument", "items", "acceptanceDateTime")
            cols = [pg.get(k) or [""] * len(pg["form"]) for k in keys]
            for form, acc, date, doc, items, acc_t in zip(*cols):
                rows.append({"cik": cik, "entity": sub.get("name"), "form": form, "accession": acc, "filing_date": date,
                             "primary_document": doc, "items": items, "acceptance": acc_t})
        if n % 20 == 0:
            print(n, cik, sub.get("name"), flush=True)
    inv = pd.DataFrame(rows).drop_duplicates(["cik", "accession"])
    inv.to_parquet(INV, index=False)
    info = json.loads(INFO.read_text()) if INFO.exists() else {}
    info.update({"inventory_failed": failed, "inventory_requests": client.stats})
    INFO.write_text(json.dumps(info, default=str))
    print(len(inv), "dépôts ;", len(failed), "véhicules sans liste")


# -- offres de rachat ---------------------------------------------------------------------------

def build_offers(inv, cfg=None):
    """Offres : un SC TO-I et les SC TO-I/A qui le suivent jusqu'au SC TO-I suivant du même véhicule
    (D-0047, point 5). Toutes les offres de l'inventaire ; `in_window` marque celles de la fenêtre."""
    t = (cfg or _cfg()).get("tenders") or {}
    ini, ame = t.get("initial_form", "SC TO-I"), t.get("amendment_form", "SC TO-I/A")
    lo, hi = t.get("window", ["2022-10-01", AS_OF])
    sel = inv[inv["form"].isin([ini, ame]) & (inv["filing_date"] <= hi)]      # rien après as_of
    sel = sel.sort_values(["cik", "filing_date", "acceptance", "accession"])
    out, orphans = [], []
    for cik, g in sel.groupby("cik", sort=True):
        cur = None
        for r in g.itertuples():
            if r.form == ini:
                cur = {"cik": cik, "entity": r.entity, "offer_accession": r.accession, "offer_date": r.filing_date,
                       "offer_document": r.primary_document, "amendments": []}
                out.append(cur)
            elif cur is not None:
                cur["amendments"].append({"accession": r.accession, "date": r.filing_date,
                                          "document": r.primary_document})
            else:
                orphans.append({"cik": cik, "accession": r.accession, "date": r.filing_date})
    for o in out:
        o["in_window"] = lo <= o["offer_date"] <= hi
        o["offer_key"] = f"{o['cik']}|{o['offer_accession']}"
    return out, orphans


def _doc_path(cik, acc, doc):
    return cache.archive_path(cik, acc, doc)


def fetch(rate=4.0):
    """Documents principaux du SC TO-I et de chacun de ses amendements, pour les offres de la fenêtre."""
    inv = pd.read_parquet(INV)
    offers, orphans = build_offers(inv)
    client = _client(rate)
    states = {}
    todo = []
    for o in offers:
        if not o["in_window"]:
            continue
        todo.append((o["cik"], o["offer_accession"], o["offer_document"]))
        for a in o["amendments"]:
            todo.append((o["cik"], a["accession"], a["document"]))
    for n, (cik, acc, doc) in enumerate(todo):
        if not doc:
            states[f"{acc}/"] = "no_primary_document"
            continue
        p = _doc_path(cik, acc, doc)
        if p.exists():
            states[f"{acc}/{doc}"] = "cached"
            continue
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}"
        try:
            raw, _ = client.get(url)
            cache.write(p, raw)
            states[f"{acc}/{doc}"] = "fetched"
        except net.NotCollected as exc:
            states[f"{acc}/{doc}"] = f"not_collected: {exc}"
        if n % 100 == 0:
            print(n, "/", len(todo), flush=True)
    rows = [{**{k: v for k, v in o.items() if k != "amendments"}, "amendments": json.dumps(o["amendments"])}
            for o in offers]
    pd.DataFrame(rows).to_parquet(OFFERS, index=False)
    info = json.loads(INFO.read_text()) if INFO.exists() else {}
    info.update({"offers_total": len(offers), "offers_in_window": sum(o["in_window"] for o in offers),
                 "amendments_orphan": orphans, "fetch_states": states, "fetch_requests": client.stats})
    INFO.write_text(json.dumps(info, default=str))
    print(len(todo), "documents ;", sum(v == "fetched" for v in states.values()), "tirés ;",
          sum(v.startswith("not_collected") for v in states.values()), "non obtenus")


CLASS_LABEL = re.compile(r"\(?\s*titles? of class(es)? of securities\s*\)?", re.I)
CLASS_ITEM = re.compile(r"title of the securities that are the subject of the [^.]{0,200}?\bare\s+([^.;(]{3,200})", re.I)


def security_class(text):
    """Classe des titres visés par l'offre, lue sur la page de garde du SC TO-I (« Title of Class of
    Securities ») : common (parts ordinaires, toutes classes), preferred, debt, unknown (D-0047, point 9)."""
    ps = paragraphs(text)
    title = None
    for i, p in enumerate(ps):
        m = CLASS_LABEL.search(p)
        if not m:
            continue
        before = p[:m.start()].strip(" _-|")
        if re.search(r"[A-Za-z]{3}", before):
            title = before
        else:
            j = i - 1
            while j >= 0 and not re.search(r"[A-Za-z]{3}", ps[j]):
                j -= 1
            title = ps[j] if j >= 0 else None
        break
    if not title:
        m = CLASS_ITEM.search(" ".join(ps))      # à défaut de page de garde : l'item 2(b) du Schedule TO
        title = m.group(1).strip() if m else None
    if not title:
        return "unknown", None
    low = title.lower()
    if "preferred" in low:
        return "preferred", title
    if re.search(r"\bnotes?\b|debentures?|\bbonds?\b", low):
        return "debt", title
    if re.search(r"shares?|stock|units?|interests?", low):
        return "common", title
    return "unknown", title


def classify(rate=4.0):
    """Classe de chaque offre utile : celles de la fenêtre, et les trois offres qui précèdent chacune
    d'elles pour les séries de F16 (SC TO-I antérieurs tirés au besoin)."""
    inv = pd.read_parquet(INV)
    offers, _ = build_offers(inv)
    k = int((_cfg().get("tenders") or {}).get("program_min_offers", 4))
    need = set()
    by = {}
    for o in offers:
        by.setdefault(o["cik"], []).append(o)
    for cik, os_ in by.items():
        os_.sort(key=lambda o: (o["offer_date"], o["offer_accession"]))
        for i, o in enumerate(os_):
            if o["in_window"]:
                need.add(o["offer_key"])
                for j in range(max(0, i - (k + 2)), i):     # marge : une offre d'une autre classe ne casse pas la série
                    need.add(os_[j]["offer_key"])
    client = _client(rate)
    states = {}
    for o in offers:
        if o["offer_key"] not in need:
            o["security_class"], o["security_title"] = None, None
            continue
        p = _doc_path(o["cik"], o["offer_accession"], o["offer_document"])
        if o["offer_document"] and not p.exists():
            url = f"https://www.sec.gov/Archives/edgar/data/{int(o['cik'])}/{o['offer_accession'].replace('-', '')}/{o['offer_document']}"
            try:
                raw, _ = client.get(url)
                cache.write(p, raw)
                states[o["offer_key"]] = "fetched"
            except net.NotCollected as exc:
                states[o["offer_key"]] = f"not_collected: {exc}"
        t = doc_text(o["cik"], o["offer_accession"], o["offer_document"])
        o["security_class"], o["security_title"] = security_class(t) if t else ("not_collected", None)
    rows = [{**{kk: v for kk, v in o.items() if kk != "amendments"}, "amendments": json.dumps(o["amendments"])}
            for o in offers]
    pd.DataFrame(rows).to_parquet(OFFERS, index=False)
    info = json.loads(INFO.read_text()) if INFO.exists() else {}
    info.update({"classify_states": states, "classify_requests": client.stats})
    INFO.write_text(json.dumps(info, default=str))
    c = pd.Series([o["security_class"] for o in offers if o["offer_key"] in need]).value_counts()
    print(c.to_dict(), ";", sum(v == "fetched" for v in states.values()), "SC TO-I antérieurs tirés")


def doc_text(cik, acc, doc):
    """Texte d'un document en cache (None s'il n'a pas été obtenu)."""
    from .discovery import plain_text
    p = _doc_path(cik, acc, doc)
    if not doc or not p.exists():
        return None
    text, _ = plain_text(cache.read(p))
    return text


RESULT_RX = re.compile(r"tender|accept|purchas|expir|pro rata|prorat|oversubscri|withdrawn|repurchas", re.I)
MAX_RX = re.compile(r"up to|not to exceed|maximum|\b5(\.0)?%|five percent", re.I)


def paragraphs(text):
    return [p for p in (re.sub(r"\s+", " ", x).strip() for x in (text or "").split("\n")) if p]


def offer_units(o):
    """Ce qui se lit pour une offre : paragraphes de résultat de chaque amendement, du dernier au
    premier, et paragraphes du SC TO-I qui donnent le maximum de l'offre."""
    out = {"amendments": [], "initial": []}
    for a in reversed(o["amendments"]):
        t = doc_text(o["cik"], a["accession"], a["document"])
        paras = paragraphs(t)
        out["amendments"].append({**a, "found": t is not None,
                                  "paragraphs": [(i, p) for i, p in enumerate(paras) if RESULT_RX.search(p)]})
    t = doc_text(o["cik"], o["offer_accession"], o["offer_document"])
    paras = paragraphs(t)
    out["initial"] = [(i, p) for i, p in enumerate(paras) if MAX_RX.search(p) and re.search(r"\d", p)][:6]
    return out


def load_offers():
    df = pd.read_parquet(OFFERS)
    out = []
    for r in df.to_dict("records"):
        r["amendments"] = json.loads(r["amendments"])
        out.append(r)
    return out


def show(start=0, count=10, width=700):
    """Unités de lecture des offres de la fenêtre, dans l'ordre véhicule puis date."""
    offers = [o for o in load_offers() if o["in_window"]]
    for n, o in enumerate(offers[start:start + count], start):
        u = offer_units(o)
        print(f"=== [{n}] {o['offer_key']} {o['entity']} SC TO-I {o['offer_date']} ; {len(o['amendments'])} amendement(s)")
        for a in u["amendments"]:
            print(f"  -- SC TO-I/A {a['accession']} {a['date']} {'' if a['found'] else '(non obtenu)'}")
            for i, p in a["paragraphs"]:
                print(f"     [{i}] {p[:width]}")
            if a["paragraphs"]:
                break      # le dernier amendement qui parle de l'offre suffit à l'affichage ; les autres sur demande
        for i, p in u["initial"]:
            print(f"  -- SC TO-I [{i}] {p[:width]}")


# -- aide à la lecture : propositions de relevés, contrôlées une à une par l'exécutant ------------

NUM = r"(\$?\s?[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|\$?\s?[0-9]+(?:\.[0-9]+)?)"
SENT_SPLIT = re.compile(r"(?<=[.;])\s+(?=[A-Z(])")
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
EXP_RX = re.compile(rf"(?:expired|terminated)\b[^.]{{0,120}}?\b((?:{MONTHS})\s+\d{{1,2}},\s+\d{{4}})", re.I)
TEND_RX = re.compile(rf"{NUM}\s*(?:of\s+(?:the\s+)?(?:Company's\s+|Fund's\s+)?)?(?:outstanding\s+)?(?:common\s+)?(?:shares|units|Shares|Units)\b"
                     r"[^.]{0,160}?(?:validly|properly)\s+tendered", re.I)
TEND2_RX = re.compile(rf"(?:validly|properly)\s+tendered[^.]{{0,60}}?(?:was|were|totaled|totalled|of|:)\s+(?:approximately\s+)?{NUM}", re.I)
ACC_RX = re.compile(rf"(?:accepted|purchased|repurchased)\s+(?:for\s+(?:purchase|payment)\s+)?(?:a\s+total\s+of\s+)?(?:approximately\s+)?{NUM}"
                    r"\s*(?:of\s+(?:the\s+)?)?(?:shares|units|Shares|Units)?", re.I)
ALL_RX = re.compile(r"accepted\s+(?:for\s+(?:purchase|payment)\s+)?all\b|all\s+(?:of\s+the\s+)?(?:shares|units)\s+(?:that\s+were\s+)?(?:validly|properly)\s+tendered[^.]{0,80}?(?:were|have\s+been)\s+accepted", re.I)
PRO_RX = re.compile(r"pro[\s-]?rata|prorat|oversubscri", re.I)
MAXQ_RX = re.compile(rf"up\s+to\s+(?:an\s+aggregate\s+of\s+)?{NUM}\s*(?:of\s+(?:its|the)\s+)?(?:issued\s+and\s+)?(?:outstanding\s+)?(?:common\s+)?(shares|units|Shares|Units)?", re.I)


def _clean_num(x):
    x = x.replace("$", "").replace(",", "").strip()
    return x


def sentences(paras):
    out = []
    for p in paras:
        out += [s.strip() for s in SENT_SPLIT.split(p) if s.strip()]
    return out


def propose(o):
    """Proposition de relevé pour une offre, à contrôler : chaque valeur avec la phrase qui la porte."""
    rec = {"offer": o["offer_key"], "read": [], "result": "no_result"}
    texts = []
    for a in reversed(o["amendments"]):
        t = doc_text(o["cik"], a["accession"], a["document"])
        if t is None:
            continue
        sents = sentences(paragraphs(t))
        hit = [s for s in sents if TEND_RX.search(s) or TEND2_RX.search(s) or ACC_RX.search(s) or ALL_RX.search(s)]
        if not hit:
            continue
        rec["read"].append(a["accession"])
        texts.append(t)
        for s in sents:
            m = EXP_RX.search(s)
            if m and "expiration" not in rec:
                rec["expiration"] = dt.datetime.strptime(re.sub(r"\s+", " ", m.group(1)), "%B %d, %Y").date().isoformat()
                rec["expiration_quote"] = s
            m = TEND_RX.search(s) or TEND2_RX.search(s)
            if m and "tendered" not in rec:
                rec["tendered"] = _clean_num(m.group(1))
                rec["tendered_unit"] = "usd" if "$" in m.group(1) else "shares"
                rec["tendered_quote"] = s
            if ALL_RX.search(s) and "accepted" not in rec:
                rec["accepted"], rec["accepted_quote"] = "all", s
            m = ACC_RX.search(s)
            if m and "accepted" not in rec and re.search(r"\d", m.group(1)):
                rec["accepted"] = _clean_num(m.group(1))
                rec["accepted_unit"] = "usd" if "$" in m.group(1) else "shares"
                rec["accepted_quote"] = s
            if PRO_RX.search(s) and "proration_quote" not in rec:
                rec["proration_quote"] = s
            m = MAXQ_RX.search(s)
            if m and "offer_max" not in rec:
                rec["offer_max"] = _clean_num(m.group(1))
                rec["offer_max_unit"] = "usd" if "$" in m.group(1) else "shares"
                rec["offer_max_quote"] = s
        rec["result"] = "read"
        break
    if "offer_max" not in rec:
        t = doc_text(o["cik"], o["offer_accession"], o["offer_document"])
        for s in sentences(paragraphs(t)):
            m = MAXQ_RX.search(s)
            if m:
                rec["offer_max"] = _clean_num(m.group(1))
                rec["offer_max_unit"] = "usd" if "$" in m.group(1) else "shares"
                rec["offer_max_quote"] = s
                rec["offer_max_source"] = o["offer_accession"]
                break
    return rec


def review(start=0, count=25, out_path=None, width=420):
    """Affiche les propositions pour contrôle ; les écrit dans un fichier JSONL de travail."""
    offers = [o for o in load_offers() if o["in_window"] and share_offer(o) and o["amendments"]]
    recs = []
    for n, o in enumerate(offers[start:start + count], start):
        r = propose(o)
        recs.append(r)
        print(f"=== [{n}] {o['entity'][:40]} | SC TO-I {o['offer_date']} | {r['result']} | "
              f"exp {r.get('expiration')} | T {r.get('tendered')} {r.get('tendered_unit', '')} | "
              f"A {r.get('accepted')} {r.get('accepted_unit', '')} | M {r.get('offer_max')} {r.get('offer_max_unit', '')}"
              f"{' | PRORATA' if r.get('proration_quote') else ''}")
        for k in ("tendered_quote", "accepted_quote", "proration_quote", "offer_max_quote"):
            q = r.get(k)
            if q and (k == "tendered_quote" or q != r.get("tendered_quote")):
                print(f"   {k[:4]}: {q[:width]}")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")


# -- relevés de lecture -------------------------------------------------------------------------

def _norm(s):
    s = (s or "").replace("’", "'").replace("“", '"').replace("”", '"').replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


def _digits(x):
    """Chiffres significatifs d'un nombre relevé, pour le retrouver dans sa citation."""
    s = str(x)
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return re.sub(r"\D", "", s)


def check_reading(rec, texts):
    """Contrôle d'un relevé d'offre : chaque citation figure mot pour mot dans un document lu, et
    chaque nombre relevé figure dans sa citation. Renvoie la liste des erreurs."""
    errs = []
    blob = " ".join(_norm(t) for t in texts if t)
    for k in ("expiration", "tendered", "accepted", "offer_max", "proration"):
        q = rec.get(f"{k}_quote")
        if q and _norm(q) not in blob:
            errs.append(f"{k}: citation introuvable")
        v = rec.get(k)
        if k in ("tendered", "accepted", "offer_max") and v not in (None, "all"):
            parts = rec.get(f"{k}_parts") or [v]
            qd = re.sub(r"\D", "", q or "")
            for x in parts:
                if _digits(x) and _digits(x) not in qd:
                    errs.append(f"{k}: {x} absent de la citation")
            if rec.get(f"{k}_parts") and abs(sum(Decimal(str(x)) for x in parts) - Decimal(str(v))) > Decimal("0.01"):
                errs.append(f"{k}: somme des parts différente")
            if rec.get(f"{k}_unit") not in ("shares", "usd"):
                errs.append(f"{k}: unité manquante")
    return errs


def readings():
    if not READINGS.exists():
        return {}
    out = {}
    for line in READINGS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["offer"]] = r
    return out


def check_file(path):
    """Contrôle des relevés d'un fichier avant de les ajouter à READINGS."""
    offers = {o["offer_key"]: o for o in load_offers()}
    ok, bad = 0, 0
    for line in pathlib_read(path):
        r = json.loads(line)
        o = offers.get(r["offer"])
        if o is None:
            print(r["offer"], "offre inconnue")
            bad += 1
            continue
        texts = [doc_text(o["cik"], a["accession"], a["document"]) for a in o["amendments"]]
        texts.append(doc_text(o["cik"], o["offer_accession"], o["offer_document"]))
        e = check_reading(r, texts)
        if e:
            print(r["offer"], e)
            bad += 1
        else:
            ok += 1
    print(ok, "relevés valides ;", bad, "rejetés")
    return bad == 0


def pathlib_read(path):
    import pathlib
    return [x for x in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


# -- cellules ------------------------------------------------------------------------------------

def balance_cells(as_of):
    """Mesures de bilan par véhicule et date, puis F14 (D-0047, points 4 et 6)."""
    from .lender_portfolio import events_cells
    cfg = _cfg()
    df = as_known(pd.read_parquet(OUT))
    out, by_vehicle = [], {}
    for r in df.sort_values(["cik", "period"]).to_dict("records"):
        cs = vehicle_cells(r, as_of, cfg)
        out += cs
        by_vehicle.setdefault(f"cik:{r['cik']}", {})[_d(r["period"])] = {c["measure"]: c for c in cs}
    out += events_cells(by_vehicle, as_of, int(cfg.get("consecutive_gap_days_max", 120)),
                        events={"F14": ("bdc_liab_asset_coverage", "down")}, decision="D-0047")
    return out


def _num(x):
    return None if x in (None, "", "all") else Decimal(str(x))


def tender_outcome(r):
    """Mesures et F15 d'une offre lue (D-0047, points 5 et 6). Renvoie un dict :
    acceptance (valeur, num, dén) ou motif, demand idem, f15 (event / no_event / motif)."""
    out = {}
    t, a, m = _num(r.get("tendered")), r.get("accepted"), _num(r.get("offer_max"))
    tu, au, mu = r.get("tendered_unit"), r.get("accepted_unit"), r.get("offer_max_unit")
    if a == "all" and t is not None:
        out["acceptance"] = (Decimal(1), t, t)
    elif a == "all":
        out["acceptance"] = "not_disclosed"
    elif t is None or _num(a) is None:
        out["acceptance"] = "not_disclosed"
    elif tu != au:
        out["acceptance"] = "precondition_not_met"
    elif t <= 0:
        out["acceptance"] = "denominator_nonpositive"
    else:
        out["acceptance"] = (_num(a) / t, _num(a), t)
    if t is None or m is None:
        out["demand"] = "not_disclosed"
    elif tu != mu:
        out["demand"] = "precondition_not_met"
    elif m <= 0:
        out["demand"] = "denominator_nonpositive"
    else:
        out["demand"] = (t / m, t, m)
    pr = r.get("proration")
    if pr is True:
        out["f15"] = "event"
    elif isinstance(out["acceptance"], tuple):
        out["f15"] = "event" if out["acceptance"][0] < 1 else "no_event"
    elif a == "all" or pr is False:
        out["f15"] = "no_event"
    else:
        out["f15"] = out["acceptance"] if isinstance(out["acceptance"], str) else "not_disclosed"
    return out


def share_offer(o):
    """Offre sur les parts ordinaires du véhicule (D-0047, point 9)."""
    return o.get("security_class") == "common"


def tender_cells(as_of):
    """Deux mesures et une cellule F15 par offre de parts de la fenêtre (D-0047, points 5, 6 et 9)."""
    from .measures import cell
    rd = readings()
    out = []
    for o in load_offers():
        if not o["in_window"] or not share_offer(o):
            continue
        subj = f"cik:{o['cik']}"
        base = {"offer": o["offer_key"], "offer_date": o["offer_date"], "vehicle": o["entity"],
                "amendments": len(o["amendments"]), "subjects": "bdc_vehicles", "decision": "D-0047"}
        r = rd.get(o["offer_key"])
        if r is None or r.get("result") != "read":
            if r is not None:
                reason = {"no_result": "not_disclosed", "not_collected": "not_collected"}.get(r.get("result"), "not_processed")
            elif not o["amendments"]:
                open_ = (dt.date.fromisoformat(as_of) - dt.date.fromisoformat(o["offer_date"])).days < OPEN_DAYS
                reason = "end_offset_exceeded" if open_ else "not_disclosed"
            else:
                reason = "not_processed"
            fl = {**base, "note": (r or {}).get("note") or {"not_disclosed": "aucun amendement ne publie le résultat",
                                                            "end_offset_exceeded": "offre peut-être encore ouverte à as_of",
                                                            "not_processed": "amendement final non lu",
                                                            "not_collected": "documents non obtenus"}[reason]}
            for m in TENDER_IDS:
                out.append(cell(m, subj, o["offer_date"], o["offer_date"], "as_known", as_of, unit="pure",
                                status="not_determinable", nd_reason=reason, flags=fl))
            out.append(cell("fragility_event", subj, o["offer_date"], o["offer_date"], "as_known", as_of, breakdown="F15",
                            status="not_determinable", nd_reason=reason, flags=fl))
            continue
        dates = {a["accession"]: a["date"] for a in o["amendments"]}
        kd = max((dates.get(x) for x in r.get("read") or [] if dates.get(x)), default=None)
        exp = r.get("expiration") or kd
        res = tender_outcome(r)
        fl = {**base, "read": r.get("read"), "expiration": r.get("expiration"),
              "tendered": r.get("tendered"), "tendered_unit": r.get("tendered_unit"),
              "accepted": r.get("accepted"), "accepted_unit": r.get("accepted_unit"),
              "offer_max": r.get("offer_max"), "offer_max_unit": r.get("offer_max_unit"),
              "proration": r.get("proration"), "note": r.get("note")}
        for m, key in (("bdc_tender_acceptance_ratio", "acceptance"), ("bdc_tender_demand_ratio", "demand")):
            v = res[key]
            if isinstance(v, tuple):
                out.append(cell(m, subj, o["offer_date"], exp, "as_known", as_of, unit="pure", value=v[0],
                                numerator=v[1], denominator=v[2], status="computed", knowledge_date=kd, flags=fl))
            else:
                out.append(cell(m, subj, o["offer_date"], exp, "as_known", as_of, unit="pure",
                                status="not_determinable", nd_reason=v, knowledge_date=kd, flags=fl))
        f = res["f15"]
        if f in ("event", "no_event"):
            out.append(cell("fragility_event", subj, o["offer_date"], exp, "as_known", as_of, breakdown="F15",
                            status="computed", value_text=f, knowledge_date=kd, flags=fl))
        else:
            out.append(cell("fragility_event", subj, o["offer_date"], exp, "as_known", as_of, breakdown="F15",
                            status="not_determinable", nd_reason=f, knowledge_date=kd, flags=fl))
    return out


def program_events(offers, inv, as_of, cfg=None):
    """F16 (D-0047, point 6) : après au moins quatre offres déposées à 120 jours au plus d'intervalle,
    aucune offre dans les 120 jours ; une inscription en bourse ou une sortie du régime dans
    l'intervalle ferme la cellule sans événement. Renvoie des dicts (une entrée par offre qui clôt
    une série), sans cellule."""
    t = (cfg or _cfg()).get("tenders") or {}
    k, gap, wait = int(t.get("program_min_offers", 4)), int(t.get("program_gap_days_max", 120)), int(t.get("interruption_days", 120))
    exits = inv[inv["form"].isin(list(t.get("listing_forms") or []) + list(t.get("exit_forms") or []))
                & (inv["filing_date"] <= as_of)]
    asof = dt.date.fromisoformat(as_of)
    out = []
    by = {}
    for o in offers:
        by.setdefault(o["cik"], []).append(o)
    for cik, os_ in sorted(by.items()):
        os_ = sorted(os_, key=lambda o: (o["offer_date"], o["offer_accession"]))
        ds = [dt.date.fromisoformat(o["offer_date"]) for o in os_]
        ex = exits[exits["cik"] == cik]
        for i, o in enumerate(os_):
            if not o["in_window"] or i < k - 1:
                continue
            run = ds[i - k + 1:i + 1]
            if any((b - a).days > gap for a, b in zip(run, run[1:])):
                continue
            end = ds[i] + dt.timedelta(days=wait)
            e = {"cik": cik, "entity": o["entity"], "offer_key": o["offer_key"], "last_offer": o["offer_date"],
                 "date": end.isoformat(), "run": [d.isoformat() for d in run]}
            if i + 1 < len(ds) and (ds[i + 1] - ds[i]).days <= wait:
                out.append({**e, "outcome": "no_event", "next_offer": ds[i + 1].isoformat(),
                            "knowledge_date": ds[i + 1].isoformat()})
                continue
            if end > asof:
                out.append({**e, "outcome": "end_offset_exceeded"})
                continue
            hit = ex[(ex["filing_date"] > o["offer_date"]) & (ex["filing_date"] <= end.isoformat())]
            if len(hit):
                h = hit.sort_values("filing_date").iloc[0]
                motive = "listing" if h["form"] in (t.get("listing_forms") or []) else "exit"
                out.append({**e, "outcome": "no_event", "motive": motive, "motive_form": h["form"],
                            "motive_accession": h["accession"], "knowledge_date": h["filing_date"]})
                continue
            out.append({**e, "outcome": "event", "knowledge_date": end.isoformat()})
    return out


def program_cells(as_of):
    from .measures import cell
    inv = pd.read_parquet(INV)
    offers = [o for o in load_offers() if share_offer(o)]
    out = []
    ann = announcements_by_cik()
    for e in program_events(offers, inv, as_of):
        fl = {k: v for k, v in e.items() if k not in ("outcome",)}
        fl.update({"subjects": "bdc_vehicles", "decision": "D-0047"})
        if e["outcome"] == "event" and ann.get(e["cik"]):
            fl["announcements"] = [a["kind"] for a in ann[e["cik"]]]
        if e["outcome"] in ("event", "no_event"):
            out.append(cell("fragility_event", f"cik:{e['cik']}", e["last_offer"], e["date"], "as_known", as_of,
                            breakdown="F16", status="computed", value_text=e["outcome"],
                            knowledge_date=e.get("knowledge_date"), flags=fl))
        else:
            out.append(cell("fragility_event", f"cik:{e['cik']}", e["last_offer"], e["date"], "as_known", as_of,
                            breakdown="F16", status="not_determinable", nd_reason=e["outcome"], flags=fl))
    return out


def announcements_by_cik():
    if not ANNOUNCEMENTS.exists():
        return {}
    out = {}
    for line in ANNOUNCEMENTS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            a = json.loads(line)
            if a.get("kind") not in (None, "none"):
                out.setdefault(a["cik"], []).append(a)
    return out


def cells(as_of):
    """Toutes les cellules du bloc."""
    return balance_cells(as_of) + tender_cells(as_of) + program_cells(as_of)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        d = extract()
        print(len(d), "dépôts ;", d["cik"].nunique(), "véhicules")
    elif cmd == "inventory":
        inventory()
    elif cmd == "fetch":
        fetch()
    elif cmd == "classify":
        classify()
    elif cmd == "review":
        review(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "show":
        show(int(sys.argv[2]) if len(sys.argv) > 2 else 0, int(sys.argv[3]) if len(sys.argv) > 3 else 10)
    elif cmd == "check":
        sys.exit(0 if check_file(sys.argv[2]) else 1)
    else:
        print(__doc__)
