"""Volet F de D-0058 : signal de crédit sur les obligations de SoftBank, lu dans les Form N-PORT Data Sets.

Source EDGAR publiée par la SEC : archives trimestrielles des positions déclarées par les fonds (formulaire
NPORT-P). Chaque archive est tirée par le client unique (§9.5), scannée dans un processus à part, puis effacée ;
seules restent, sous `cache/datasets/nport/{archive}/softbank/`, les positions dont l'émetteur est une entité de
SoftBank (nom d'émetteur qui contient « SOFTBANK », ou LEI relevé avec un tel nom dans les archives, jamais
supposé), avec leurs identifiants, leurs caractéristiques de titre de dette, et le dépôt et la série de chaque
fonds. Les colonnes se lisent dans la description publiée avec les archives (`nport.columns` de config.yaml),
vérifiée avant tout calcul.

Mesure `nport_price_to_par`, par titre (ISIN, à défaut CUSIP) et par date de portefeuille déclarée : somme des
valeurs déclarées, dans la monnaie du titre, divisée par la somme des nominaux (unité « PA »), sur les positions
en titres de dette des séries de fonds distinctes, au dernier dépôt de chaque série pour cette date (un
amendement remplace le dépôt). Le nombre de séries et le nominal détenu se publient avec. C'est une valorisation
déclarée par des tiers (perspective `counterparty`), jamais une probabilité de défaut ni un fait comptable de
SoftBank : elle n'entre dans aucune mesure de financement ni dans l'annexe F.

    python -m pipeline.nport page       # page des jeux de données et description, tirées une fois
    python -m pipeline.nport fetch      # archives tirées, scannées, effacées (de la plus récente à la plus ancienne)
    python -m pipeline.nport stamp      # date de publication (HEAD) des archives scannées sans elle
    python -m pipeline.nport volume     # décompte des extraits et de la sélection, sans valeur de la mesure
    python -m pipeline.nport status
"""
import csv
import datetime as dt
import io
import json
import re
import sys
import zipfile
from decimal import Decimal, InvalidOperation

import pandas as pd

from . import cache, config, net

SEC = "https://www.sec.gov"
PAGE = ("datasets", "nport", "form-n-port-data-sets.html")
PAGE_URL = SEC + "/data-research/sec-markets-data/form-n-port-data-sets"
BASE = config.CACHE / "datasets" / "nport"
MANIFEST = BASE / "manifest.jsonl"
SUBDIR = "softbank"
NONE = "none"
NAME_RX = re.compile(r"SOFTBANK", re.I)


def cfg_nport(cfg=None):
    return (cfg or config.load()).get("nport") or {}


def cols(cfg=None):
    """Noms des colonnes, tels que la description publiée les donne (vérifiés avant tout calcul)."""
    c = cfg_nport(cfg).get("columns")
    if not c:
        raise SystemExit("nport.columns absent de config.yaml : la description n'est pas encore vérifiée")
    return c


# -- page et archives -------------------------------------------------------------------------------

def page(client=None):
    """La page des jeux de données, tirée une fois et gardée en cache (comme en D-0036)."""
    p = cache.other_path(*PAGE)
    if p.exists():
        return cache.read(p).decode("utf-8", "replace")
    client = client or net.SecClient(config.load().get("as_of"), config.load())
    raw, _ = client.get(PAGE_URL)
    cache.write(p, raw)
    return raw.decode("utf-8", "replace")


def archive_list(html=None):
    """Archives trimestrielles publiées : nom, adresse, trimestre de dépôt couvert."""
    html = html or page()
    out, seen = [], set()
    for u in re.findall(r'href="([^"]*?/(\d{4}q[1-4])_nport\.zip)"', html):
        url, name = u
        if name in seen:
            continue
        seen.add(name)
        y, q = int(name[:4]), int(name[5])
        start = dt.date(y, 3 * q - 2, 1)
        end = dt.date(y + (q == 4), (3 * q) % 12 + 1, 1) - dt.timedelta(days=1)
        out.append({"name": name, "url": url if url.startswith("http") else SEC + url,
                    "filed_from": start.isoformat(), "filed_to": end.isoformat()})
    return sorted(out, key=lambda a: a["name"], reverse=True)


def readme_links(html=None):
    html = html or page()
    return sorted(set(re.findall(r'href="([^"]*form-n-port-data-sets[^"]*\.(?:pdf|htm|html|txt))"', html, re.I)))


def in_period(archives, start, as_of):
    return [a for a in archives if a["filed_to"] >= start and a["filed_from"] <= as_of]


def manifest():
    if not MANIFEST.exists():
        return {}
    return {r["name"]: r for r in (json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l)}


# -- scan d'une archive ------------------------------------------------------------------------------

def _member(z, stem):
    names = [n for n in z.namelist() if n.rsplit("/", 1)[-1].upper().startswith(stem.upper() + ".")]
    return names[0] if names else None


def _read(z, stem, usecols=None, keep=None, key=None, chunk=500_000):
    """Lecture par morceaux d'une table TSV de l'archive ; `keep(df)` filtre chaque morceau, ou
    `key` (colonne, ensemble) garde les lignes dont la colonne est dans l'ensemble."""
    m = _member(z, stem)
    if m is None:
        return pd.DataFrame(columns=usecols or [])
    out = []
    with z.open(m) as fh:
        for df in pd.read_csv(io.TextIOWrapper(fh, encoding="utf-8", errors="replace"), sep="\t", dtype=str,
                              usecols=usecols, chunksize=chunk, quoting=csv.QUOTE_NONE, keep_default_na=False,
                              na_values=[""], on_bad_lines="warn"):
            if keep is not None:
                df = df[keep(df)]
            elif key is not None:
                df = df[df[key[0]].isin(key[1])]
            if len(df):
                out.append(df)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=usecols or [])


def scan_archive(zpath, leis=(), c=None):
    """Positions de SoftBank d'une archive et leurs tables liées. `leis` : LEI déjà relevés avec un nom
    qui contient « SOFTBANK ». Retourne (tables, statistiques, LEI relevés dans cette archive)."""
    c = c or cols()
    h = c["holding"]
    leis = set(leis)
    with zipfile.ZipFile(zpath) as z:
        def keep(df):
            name = df[h["issuer_name"]].fillna("")
            lei = df[h["issuer_lei"]].fillna("")
            return name.str.contains(NAME_RX) | lei.isin(leis)
        hold = _read(z, c["tables"]["holding"], keep=keep)
        found = set(hold.loc[hold[h["issuer_name"]].fillna("").str.contains(NAME_RX), h["issuer_lei"]].dropna()) - NOT_LEI
        if found - leis:                 # LEI relevé dans cette archive même : second passage, une fois
            leis |= found
            hold = _read(z, c["tables"]["holding"], keep=keep)
        ids = set(hold[h["holding_id"]])
        acc = set(hold[h["accession"]])
        out = {"holding": hold}
        for t in ("identifiers", "debt"):
            out[t] = _read(z, c["tables"][t], key=(c[t]["holding_id"], ids))
        for t in ("submission", "registrant", "fund"):
            out[t] = _read(z, c["tables"][t], key=(c[t]["accession"], acc))
    stats = {k: len(v) for k, v in out.items()}
    stats["by_name"] = int(hold[h["issuer_name"]].fillna("").str.contains(NAME_RX).sum())
    stats["by_lei_only"] = int(len(hold) - stats["by_name"])
    return out, stats, sorted(found)


def _scan_job(name, zpath, leis, meta):
    out, stats, found = scan_archive(zpath, leis)
    d = BASE / name / SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    for k, df in out.items():
        df.to_parquet(d / f"{k}.parquet", index=False, compression="zstd")
    return dict(meta, status="scanned", bytes=zpath.stat().st_size, stats=stats, leis_found=found,
                leis_applied=sorted(leis))


NOT_LEI = {"", "N/A"}


def lei_evidence(hold, c=None):
    """Par LEI relevé (porté par une position dont le nom d'émetteur contient « SOFTBANK ») : positions
    gardées qui le portent et, parmi elles, celles dont le nom contient « SOFTBANK »."""
    h = (c or cols())["holding"]
    lei = hold[h["issuer_lei"]].fillna("").astype(str).str.strip()
    named = hold[h["issuer_name"]].fillna("").str.contains(NAME_RX)
    return {l: {"positions": int((lei == l).sum()), "named": int(((lei == l) & named).sum())}
            for l in sorted(set(lei[named]) - NOT_LEI)}


def accepted(evidence):
    """Un LEI relevé est un LEI de SoftBank si la majorité des positions gardées qui le portent, toutes
    archives scannées confondues, ont un nom qui contient « SOFTBANK » (D-0058, point 28)."""
    return {l for l, e in evidence.items() if 2 * e["named"] > e["positions"]}


def _holdings(m, c=None):
    h = (c or cols())["holding"]
    use = [h["issuer_name"], h["issuer_lei"]]
    out = [pd.read_parquet(BASE / k / SUBDIR / "holding.parquet", columns=use) for k, r in sorted(m.items())
           if r.get("status") == "scanned" and (BASE / k / SUBDIR / "holding.parquet").exists()]
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=use)


def softbank_leis(m=None):
    """LEI de SoftBank, tirés des extraits des archives scannées (une archive publiée après l'as_of n'en
    apporte aucun)."""
    m = manifest() if m is None else m
    return accepted(lei_evidence(_holdings(m)))


def applied(r):
    """LEI appliqués au scan d'une archive : ceux qu'il a reçus et ceux qu'il a relevés (second passage)."""
    return set(r.get("leis_applied") or []) | set(r.get("leis_found") or [])


def _published(headers):
    lm = headers.get("Last-Modified") if headers is not None else None
    return lm, _http_date(lm)


def _drop_extracts(name):
    """Extraits d'une archive publiée après l'as_of : ni gardés ni lus (point 27)."""
    d = BASE / name / SUBDIR
    for f in (sorted(d.glob("*.parquet")) if d.exists() else []):
        f.unlink()


def _append(rec):
    with open(MANIFEST, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def fetch(only=None):
    """De la plus récente archive à la plus ancienne : tirée par le client unique, scannée dans un
    processus à part, puis effacée. Une archive publiée après l'as_of (en-tête Last-Modified) n'est ni
    gardée ni scannée. Les LEI relevés et acceptés (point 28) s'appliquent aux archives scannées ensuite ;
    une archive scannée avant qu'un LEI ne soit accepté est signalée, et un nouvel appel la rescanne."""
    from concurrent.futures import ProcessPoolExecutor
    from .discovery import AS_OF
    cfg = config.load()
    n = cfg_nport(cfg)
    client = net.SecClient(AS_OF, cfg)
    todo = in_period(archive_list(), n["period"][0], n["period"][1])
    done = manifest()
    leis = softbank_leis(done)
    BASE.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=1) as pp:
        for a in todo:
            if only and a["name"] not in only:
                continue
            prev = done.get(a["name"], {})
            if prev.get("status") == "after_as_of":
                continue
            if prev.get("status") == "scanned" and applied(prev) >= leis:
                continue
            zpath = BASE / f"{a['name']}.zip"
            t0 = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            try:
                _, headers = client.get(a["url"], timeout=900, dest=zpath)
            except net.NotCollected as exc:
                rec = dict(a, status="not_collected", reason=str(exc))
            else:
                lm, published = _published(headers)
                meta = dict(a, retrieved=t0, last_modified=lm)
                if published and published > AS_OF:
                    zpath.unlink()     # publiée après l'as_of : connaissance postérieure, ni gardée ni scannée
                    _drop_extracts(a["name"])
                    rec = dict(meta, status="after_as_of")
                else:
                    rec = pp.submit(_scan_job, a["name"], zpath, sorted(leis), meta).result()
                    zpath.unlink()
            _append(rec)
            if rec.get("status") == "scanned":
                leis = softbank_leis()      # un LEI relevé ne vaut pour les archives suivantes que s'il est accepté
            print(a["name"], rec.get("status"), json.dumps(rec.get("stats") or {}), flush=True)
    m = manifest()
    late = [k for k, r in sorted(m.items(), reverse=True) if r.get("status") == "scanned" and applied(r) < leis]
    print("LEI de SoftBank :", sorted(leis), "; archives à rescanner :", late)


def stamp():
    """Date de publication (en-tête Last-Modified, requête HEAD) des archives scannées sans elle ; une
    archive publiée après l'as_of perd ses extraits et passe à l'état `after_as_of` (point 27)."""
    from .discovery import AS_OF
    cfg = config.load()
    client = net.SecClient(AS_OF, cfg)
    for name, r in sorted(manifest().items(), reverse=True):
        if r.get("status") != "scanned" or r.get("last_modified"):
            continue
        try:
            _, headers = client.get(r["url"], method="HEAD")
        except net.NotCollected as exc:
            print(name, "en-tête non obtenu :", exc, flush=True)
            continue
        lm, published = _published(headers)
        t = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        if published and published > AS_OF:
            _drop_extracts(name)
            rec = {k: r.get(k) for k in ("name", "url", "filed_from", "filed_to", "retrieved", "bytes")}
            rec.update(last_modified=lm, stamped=t, status="after_as_of",
                       note="scannée avant que l'en-tête ne soit lu ; extraits effacés, non lus")
        else:
            rec = dict(r, last_modified=lm, stamped=t)
        _append(rec)
        print(name, rec["status"], lm, flush=True)


def _http_date(v):
    """Date AAAA-MM-JJ d'un en-tête HTTP Last-Modified, ou None."""
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(v).date().isoformat() if v else None
    except (TypeError, ValueError):
        return None


def _iso(v):
    """Date des tables (« 30-SEP-25 », « 2025-09-30 »…) en AAAA-MM-JJ, ou None."""
    if v is None or v != v or str(v).strip() == "":
        return None
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d-%b-%y", "%d-%b-%Y", "%m/%d/%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s[:11] if fmt != "%Y-%m-%d" else s[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


# -- positions et mesure ---------------------------------------------------------------------------

def _dec(x):
    try:
        v = Decimal(str(x).replace(",", "").strip())
        return v if v.is_finite() else None
    except (InvalidOperation, AttributeError, TypeError):
        return None


def positions(c=None, archives=None):
    """Positions de SoftBank de toutes les archives scannées (nom qui contient « SOFTBANK », ou LEI de
    SoftBank accepté), jointes à leur dépôt, leur série et leurs identifiants ; une ligne par position
    déclarée."""
    c = c or cols()
    m = manifest()
    leis = softbank_leis(m)
    rows = []
    for name, r in sorted(m.items()):
        if r.get("status") != "scanned" or (archives and name not in archives):
            continue
        d = BASE / name / SUBDIR
        t = {k: pd.read_parquet(d / f"{k}.parquet") for k in ("holding", "identifiers", "debt", "submission", "registrant", "fund")}
        h, s, f, g, i, b = c["holding"], c["submission"], c["fund"], c["registrant"], c["identifiers"], c["debt"]
        x = t["holding"].rename(columns={v: k for k, v in h.items()})
        lei = x["issuer_lei"].fillna("").astype(str).str.strip()
        x = x[x["issuer_name"].fillna("").str.contains(NAME_RX) | lei.isin(leis)]
        x = x.merge(t["submission"].rename(columns={v: k for k, v in s.items()}), on="accession", how="left")
        x = x.merge(t["fund"].rename(columns={v: k for k, v in f.items()}), on="accession", how="left", suffixes=("", "_fund"))
        x = x.merge(t["registrant"].rename(columns={v: k for k, v in g.items()}), on="accession", how="left", suffixes=("", "_reg"))
        ids = t["identifiers"].rename(columns={v: k for k, v in i.items()})
        if len(ids):
            ids = ids.groupby("holding_id", as_index=False).agg({"isin": lambda v: next((y for y in v if isinstance(y, str) and y), None)})
            x = x.merge(ids, on="holding_id", how="left")
        else:
            x["isin"] = None
        debt = t["debt"].rename(columns={v: k for k, v in b.items()})
        x = x.merge(debt, on="holding_id", how="left", suffixes=("", "_debt"))
        x["archive"] = name
        for col in ("filing_date", "report_date", "maturity"):
            if col in x:
                x[col] = [_iso(v) for v in x[col]]
        conv = cfg_nport().get("exchange_rate_convention", "currency_per_usd")
        x["value_local"] = [_local_value(v, r, cur, conv) for v, r, cur in zip(x["value_usd"], x["exchange_rate"], x["currency"])]
        rows.append(x)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _local_value(value_usd, rate, currency, conv="currency_per_usd"):
    """Valeur dans la monnaie du titre : la valeur déclarée est en dollars (rubrique C.2.c du formulaire),
    le taux de change est celui qui a servi à la calculer, en unités de la monnaie du titre pour un dollar
    (`nport.exchange_rate_convention`, vérifiée sur les positions avant tout calcul)."""
    v = _dec(value_usd)
    if v is None:
        return None
    if not currency or str(currency).upper() == "USD":
        return v
    r = _dec(rate)
    if r is None or r == 0:
        return None
    return v * r if conv == "currency_per_usd" else v / r


ISIN_RX = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
CUSIP_RX = re.compile(r"^[A-Z0-9*@#]{8}[0-9]$")


def _ident(v, rx):
    s = v.strip().upper() if isinstance(v, str) else ""
    return s if rx.match(s) and set(s) != {"0"} else None


def security_keys(p):
    """Titre de chaque position : son ISIN ; à défaut l'ISIN que d'autres positions donnent au même CUSIP,
    s'il est unique ; à défaut « CUSIP:… ». « N/A », « 000000000 » et tout code mal formé ne sont pas des
    identifiants (D-0058, point 28)."""
    isin = [_ident(v, ISIN_RX) for v in p["isin"]]
    cusip = [_ident(v, CUSIP_RX) for v in p["cusip"]]
    by_cusip = {}
    for i, c in zip(isin, cusip):
        if i and c:
            by_cusip.setdefault(c, set()).add(i)
    return [i or (next(iter(by_cusip[c])) if len(by_cusip.get(c) or ()) == 1 else ("CUSIP:" + c if c else None))
            for i, c in zip(isin, cusip)]


def fund_key(p):
    """Série du fonds ; un fonds sans série (fonds fermé) est son déclarant (CIK)."""
    cik = p["cik"] if "cik" in p else pd.Series([None] * len(p), index=p.index)
    return [s if isinstance(s, str) and s else (f"CIK:{k}" if isinstance(k, str) and k else None)
            for s, k in zip(p["series_id"], cik)]


def selection(p):
    """Positions de la mesure et nombre de positions écartées à chaque étape (D-0058, points 8 et 28) :
    titres de dette en nominal (catégorie DBT, unité PA), positions longues, titre identifié, émetteur de
    SoftBank (la majorité des positions du titre sous un nom qui contient « SOFTBANK », et l'une au moins
    sous un intitulé de titre qui le contient)."""
    steps = {}

    def keep(q, step, mask):
        steps[step] = int((~mask).sum())
        return q[mask].copy()
    p = keep(p, "not_debt_in_principal", (p["unit"] == "PA") & (p["asset_cat"] == "DBT"))
    p = keep(p, "not_long", p["payoff"] == "Long")
    p["security"] = security_keys(p)
    p = keep(p, "no_identifier", p["security"].notna())
    g = pd.DataFrame({"security": p["security"], "named": p["issuer_name"].fillna("").str.contains(NAME_RX),
                      "titled": p["title"].fillna("").str.contains(NAME_RX)}).groupby("security").agg(
        n=("named", "size"), named=("named", "sum"), titled=("titled", "sum"))
    ok = set(g.index[(2 * g["named"] > g["n"]) & (g["titled"] > 0)])
    p = keep(p, "not_softbank_issuer", p["security"].isin(ok))
    steps["securities_kept"], steps["securities_out"] = sorted(ok), sorted(set(g.index) - ok)
    return p, steps


def latest_by_fund(p):
    """Au dernier dépôt de chaque série (ou fonds sans série) pour une date de portefeuille : un
    amendement remplace le dépôt (le plus récent par date de dépôt, puis par accession)."""
    p = p.assign(fund=fund_key(p))
    key = ["fund", "report_date"]
    last = (p.sort_values(["filing_date", "accession"]).groupby(key, dropna=False)["accession"].last().reset_index())
    return p.merge(last, on=key + ["accession"], how="inner")


def price_to_par(p):
    """Une ligne par (titre, date de portefeuille) : somme des valeurs dans la monnaie du titre, somme
    des nominaux (unité PA), séries distinctes ; positions retenues par `selection`."""
    p, _ = selection(p)
    p = latest_by_fund(p)
    out = []
    for (sec, d), g in p.groupby(["security", "report_date"]):
        vals = [(_dec(r.value_local), _dec(r.balance)) for r in g.itertuples(index=False)]
        vals = [(v, n) for v, n in vals if v is not None and n is not None and n != 0]
        if not vals:
            continue
        num = sum(v for v, _ in vals)
        den = sum(n for _, n in vals)
        cur = sorted(set(g["currency"].dropna()))
        out.append({"security": sec, "report_date": d, "value_local": num, "principal": den,
                    "ratio": num / den, "n_series": g["fund"].nunique(), "n_positions": len(vals),
                    "currency": ";".join(cur), "issuer_names": ";".join(sorted(set(g["issuer_name"].dropna()))),
                    "title": next(iter(sorted(set(g["title"].dropna()))), None),
                    "maturity": next(iter(sorted(set(g["maturity"].dropna()))), None) if "maturity" in g else None,
                    "accessions": sorted(set(g["accession"]))})
    return pd.DataFrame(out)


BASIS = ("valorisation déclarée par des fonds (Form N-PORT Data Sets), perspective counterparty : somme des valeurs "
         "dans la monnaie du titre sur la somme des nominaux, au dernier dépôt de chaque série (un fonds fermé sans "
         "série compte pour une) pour la date de portefeuille ; jamais une probabilité de défaut ni un fait comptable "
         "de SoftBank, hors des mesures de financement et de l'annexe F (D-0058, points 8 et 28)")


def cells(as_of, subject="NF:SOFTBANK"):
    """Cellules nport_price_to_par : une par titre et par date de portefeuille, série descriptive du nœud."""
    from .measures import cell
    if not manifest():
        return []
    p = positions()
    if p.empty:
        return []
    r = price_to_par(p)
    kd = p.groupby("accession")["filing_date"].max().to_dict()
    out = []
    for x in r.itertuples(index=False):
        out.append(cell("nport_price_to_par", subject, None, x.report_date, "as_known", as_of,
                        breakdown=x.security, value=x.ratio, numerator=x.value_local, denominator=x.principal, unit="pure",
                        knowledge_date=max(str(kd.get(a) or "") for a in x.accessions)[:10] or None,
                        flags={"perspective": "counterparty", "n_series": int(x.n_series),
                               "n_positions": int(x.n_positions), "principal": str(x.principal),
                               "currency": x.currency, "title": x.title, "maturity": x.maturity,
                               "issuer_names": x.issuer_names, "accessions": list(x.accessions), "basis": BASIS}))
    return out


def volume():
    """Décompte des extraits et de la sélection, sans aucune valeur de la mesure (consigné avant calcul)."""
    c = cols()
    m = manifest()
    raw = _holdings(m, c)
    ev = lei_evidence(raw, c)
    ok = accepted(ev)
    p = positions(c)
    named = p["issuer_name"].fillna("").str.contains(NAME_RX)
    kept, steps = selection(p)
    last = latest_by_fund(kept)
    return {"archives_scanned": sum(1 for r in m.values() if r.get("status") == "scanned"),
            "archives_after_as_of": sum(1 for r in m.values() if r.get("status") == "after_as_of"),
            "bytes": sum(int(r.get("bytes") or 0) for r in m.values() if r.get("status") == "scanned"),
            "extract_rows": len(raw), "lei_evidence": ev, "leis_accepted": sorted(ok),
            "positions": len(p), "by_name": int(named.sum()), "by_lei_only": int((~named).sum()),
            "asset_unit": {f"{a}/{u}": int(n) for (a, u), n in p.groupby(["asset_cat", "unit"]).size().items()},
            "steps": {k: v for k, v in steps.items() if not k.startswith("securities")},
            "securities_kept": len(steps["securities_kept"]), "securities_out": steps["securities_out"],
            "selected": len(kept), "after_latest_filing": len(last), "funds": last["fund"].nunique(),
            "report_dates": last["report_date"].nunique(),
            "first_last_date": [last["report_date"].min(), last["report_date"].max()] if len(last) else None,
            "security_dates": int(last.groupby(["security", "report_date"]).ngroups)}


def exclusions(as_of):
    """Archives de la période non tirées ou non scannées, et archives scannées avant qu'un LEI ne soit
    relevé (positions possiblement manquées) : visibles dans les exclusions (§11)."""
    cfg = config.load()
    n = cfg_nport(cfg)
    if not n or not cache.other_path(*PAGE).exists():
        return []
    m = manifest()
    leis = softbank_leis(m)
    out = []

    def ex(key, reason, detail):
        out.append({"exclusion_key": f"{reason}:nport:{key}", "item_kind": "period", "item_key": f"nport:{key}",
                    "reason": reason, "detail": detail, "group_id": "NF:SOFTBANK", "accession": None,
                    "content_key": None, "as_of": as_of})
    for a in in_period(archive_list(), n["period"][0], n["period"][1]):
        r = m.get(a["name"])
        if r is None:
            ex(a["name"], "not_processed", f"archive des Form N-PORT Data Sets non tirée ({a['filed_from']} au {a['filed_to']})")
        elif r.get("status") == "not_collected":
            ex(a["name"], "not_collected", f"archive des Form N-PORT Data Sets non tirée : {r.get('reason')}")
        elif r.get("status") == "after_as_of":
            ex(a["name"], "not_public", f"archive des Form N-PORT Data Sets publiée après l'as_of (Last-Modified "
               f"{r.get('last_modified')}) : connaissance postérieure, ni gardée ni lue (D-0058, point 27)")
        elif applied(r) < leis:
            ex(a["name"], "not_processed", "archive scannée avant que tous les LEI de SoftBank ne soient acceptés : "
               "positions sous un autre nom possiblement manquées")
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "page":
        html = page()
        a = archive_list(html)
        print(len(a), "archives :", a[-1]["name"] if a else None, "à", a[0]["name"] if a else None)
        print("description :", readme_links(html))
    elif cmd == "fetch":
        fetch(only=set(sys.argv[2:]) or None)
    elif cmd == "stamp":
        stamp()
    elif cmd == "volume":
        print(json.dumps(volume(), ensure_ascii=False, indent=1, default=str))
    else:
        m = manifest()
        leis = softbank_leis(m)
        print("LEI de SoftBank :", sorted(leis))
        print(len(m), "archives au manifeste ;", sum(1 for r in m.values() if r.get("status") == "scanned"), "scannées ;",
              sum(1 for r in m.values() if r.get("status") == "after_as_of"), "publiées après l'as_of ; à rescanner :",
              [k for k, r in sorted(m.items(), reverse=True) if r.get("status") == "scanned" and applied(r) < leis])
