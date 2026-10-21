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
    ident = {sec: {"issuer": _mode(re.sub(r"[\s.,]+$", "", str(n).upper().strip()) for n in g["issuer_name"].dropna()),
                   "coupon": _mode(g["coupon"].dropna()) if "coupon" in g else None,
                   "maturity": _mode(g["maturity"].dropna()) if "maturity" in g else None}
             for sec, g in p.groupby("security")}
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
                    "title": next(iter(sorted(set(g["title"].dropna()))), None), **ident[sec],
                    "accessions": sorted(set(g["accession"]))})
    return pd.DataFrame(out)


def _mode(values):
    """Valeur la plus fréquente ; à égalité, la première dans l'ordre (déterministe)."""
    c = pd.Series(list(values), dtype=object).value_counts()
    return min(c.index[c == c.max()]) if len(c) else None


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
                               "issuer": x.issuer, "coupon": x.coupon,
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


# -- D-0065 : non-cotés du modèle, en un seul passage (volet 5 de D-0059) -------------------------------
#
# Lexique tiré du registre et de la configuration, figé au premier tirage ; positions gardées hors des niveaux 1
# et 2 de la hiérarchie de juste valeur ; rattachement par le seul nom d'émetteur, qui commence par une
# dénomination légale (règle des BDC) ; mesures nport_equity_mark (valeur par action, par fonds et par date) et
# nport_equity_held (valeur détenue par les fonds, par trimestre civil), marques déclarées par des tiers.

U_SUBDIR = "unlisted"
U_MANIFEST = BASE / "unlisted_manifest.jsonl"
U_TABLES = ("holding", "identifiers", "debt", "submission", "registrant", "fund")
INNER_DOT = re.compile(r"(?<=\w)\.(?=\w)")
PARTY_LIST = re.compile(r"^(a|an) | and ")


def cfg_unlisted(cfg=None):
    return cfg_nport(cfg).get("unlisted") or {}


def dotless(name):
    """Variante de ponctuation : le point retiré plutôt que remplacé par une espace (« X.AI » donne « xai »)."""
    from .graph import normalize_name
    return normalize_name(INNER_DOT.sub("", name or ""))


def forms(name):
    """Formes comparées d'un nom : normalisé (§10.2), puis sans ses points s'il en diffère."""
    from .graph import normalize_name
    a, b = normalize_name(name or ""), dotless(name)
    return (a,) if b == a else (a, b)


def _base(n):
    """Dénomination normalisée sans sa ou ses formes juridiques finales (« samsung electronics co ltd »)."""
    from .entities import LEGAL_SUFFIX
    s = n
    while True:
        m = LEGAL_SUFFIX.search(s)
        if not m or m.start() == 0:
            return s.strip()
        s = s[:m.start()].strip()


def _entity_rows():
    df = pd.read_parquet(config.ROOT / "tables" / "entities.parquet")
    return df.astype(object).where(df.notna(), None).to_dict("records")


def config_terms(cfg):
    """Termes des lexiques de la configuration (D-0065, point 4, c) : laboratoires, découverte, non-déposants."""
    d = cfg.get("discovery") or {}
    out = list(cfg.get("labs") or [])
    out += [x["term"] for k in ("seed", "confirmed") for x in ((d.get("lexicon") or {}).get(k) or [])]
    out += [x["term"] for x in ((d.get("non_filer") or {}).get("lexicon") or [])]
    return out


def legal_forms(ent_rows):
    """Dénominations légales de la règle des BDC (D-0022, D-0045) et variante sans points de chacune, prise
    sur le nom d'origine : forme -> entity_id."""
    from . import lender
    legal = lender.legal_names(ent_rows)
    out = dict(legal)
    for r in ent_rows:
        if (r["record_kind"] in ("entity", "alias") and r.get("status") != "pending"
                and r.get("normalized_name") in legal):
            out.setdefault(dotless(r.get("name")), legal[r["normalized_name"]])
    return out


def lexicon(ent_rows=None, cfg=None):
    """Lexique du scan (D-0065, point 4) : {"legal": {forme: entity_id}, "keep": {chaîne: partie}, "version"}.
    (a) dénominations légales ; (b) leurs bases d'au moins deux mots ; (c) termes de la configuration ; (d) noms
    d'entités confirmées sans forme juridique, d'au moins deux mots, hors descriptions et listes de parties.
    Chaque chaîne vaut aussi sans ses points."""
    from .entities import LEGAL_SUFFIX
    cfg = cfg or config.load()
    ent_rows = _entity_rows() if ent_rows is None else ent_rows
    legal = legal_forms(ent_rows)
    keep = {}

    def add(s, part):
        s = (s or "").strip()
        if s:
            keep.setdefault(s, part)
    for f in legal:
        add(f, "a")
    for f in legal:
        b = _base(f)
        if len(b.split()) >= 2:
            add(b, "b")
    for t in config_terms(cfg):
        for f in forms(t):
            add(f, "c")
    for r in ent_rows:
        if r["record_kind"] != "entity" or r.get("status") == "pending":
            continue
        for f in forms(r.get("name")):
            if f and f not in legal and not LEGAL_SUFFIX.search(f) and len(f.split()) >= 2 and not PARTY_LIST.search(f):
                add(f, "d")
    blob = json.dumps({"legal": sorted(legal.items()), "keep": sorted(keep.items())}, ensure_ascii=False)
    return {"legal": legal, "keep": keep, "version": "lx-" + cache.sha256(blob.encode())[:12],
            "parts": {p: sum(1 for v in keep.values() if v == p) for p in "abcd"}}


def finder(keys):
    """Plus longue chaîne de `keys` contenue mot pour mot dans l'une des formes d'un texte, ou None (préfiltre
    des BDC : seules les chaînes dont le premier mot figure dans le texte se testent)."""
    from .lender import name_finder
    find = name_finder(sorted(keys, key=lambda k: (-len(k), k)))

    def hit(text):
        for f in forms(text):
            k = find(" " + f + " ")
            if k:
                return k
        return None
    return hit


VEHICLE_WORDS = {"spv", "feeder", "aggregator", "aggr", "co-invest", "coinvest"}


def attribute(name, legal):
    """Entité d'un nom d'émetteur (D-0065, point 6) : le nom commence par une dénomination légale, la plus
    longue l'emporte, et aucune autre forme juridique ne la suit avant un mot d'instrument (règle des BDC). Un mot
    de véhicule après la dénomination (« SPV ») la laisse sans rattachement (point 15). Renvoie (entity_id, forme),
    (None, forme) si la forme trouvée n'est pas l'émetteur, (None, None) sinon."""
    from .lender import issuer_unambiguous
    found = None
    for f in forms(name):
        toks = f.split()
        for i in range(len(toks), 0, -1):
            k = " ".join(toks[:i])
            if k in legal:
                if issuer_unambiguous(" " + f + " ", k) and not VEHICLE_WORDS & set(toks[i:]):
                    return legal[k], k
                found = found or k
                break
    return None, found


# D-0066, point 3 : après un terme de la configuration, seuls des mots de catégorie ou d'instrument ; un code (« G »,
# « H-1 », un taux, une date) n'est admis qu'après un tel mot ; une forme juridique ou un mot de véhicule bloque
CLASS_WORDS = set("series ser class cl preferred pref pfd prf common com stock stk shares share shs units unit ordinary ord "
                  "convertible cvt conv pp private placement restricted".split())
DEBT_WORDS = set("term loan loans tl tla tlb tlc ddtl delayed draw ddl revolver revolving rcf rc abl facility first 1st "
                 "second 2nd lien senior sr secured sec unsecured notes note nts bond bonds debt incremental initial tranche "
                 "unfunded funded sub subordinated junior mezzanine pik fixed floating frn".split())
CODE_RX = re.compile(r"^(?:[a-z0-9]{1,3}(?:-[a-z0-9]{1,3})?|\d+(?:\.\d+)?%?|\d{1,2}/\d{1,2}/\d{2,4})$")
SEPARATOR_RX = re.compile(r"^[/&-]+$")
FORM_WORDS = {"inc", "corp", "llc", "lp", "ltd", "plc", "pbc", "co", "sa", "ag", "nv", "bv", "gmbh", "pte", "llp", "lllp",
              "as", "asa", "ab", "oy", "kk", "kg", "se", "spa", "sarl", "limited", "company", "corporation", "incorporated"}
TERM_BLOCK_WORDS = FORM_WORDS | VEHICLE_WORDS | {"fund", "funds"}


def term_forms(ent_rows, cfg=None):
    """Termes de la configuration (`config_terms`) qui désignent une seule entité confirmée du registre, par son nom
    normalisé ou un alias (D-0066, point 3) : forme -> entity_id. Chaque terme vaut aussi sans ses points."""
    names = {}
    for r in ent_rows:
        if r["record_kind"] in ("entity", "alias") and r.get("status") != "pending" and r.get("normalized_name"):
            names.setdefault(r["normalized_name"], set()).add(r["entity_id"])
    out = {}
    for t in config_terms(cfg or config.load()):
        for f in forms(t):
            if len(names.get(f) or ()) == 1:
                out[f] = next(iter(names[f]))
    return out


def class_words_only(rest):
    """Les mots qui suivent le terme ne sont que des mots de catégorie ou d'instrument, et des codes qui suivent l'un
    d'eux ; une forme juridique ou un mot de véhicule laisse le nom sans rattachement (D-0066, point 3)."""
    if TERM_BLOCK_WORDS & set(rest):
        return False
    after_word = False
    for w in rest:
        if w in CLASS_WORDS or w in DEBT_WORDS:
            after_word = True
        elif SEPARATOR_RX.match(w):
            continue
        elif not (after_word and CODE_RX.match(w)):
            return False
    return True


def term_attribute(name, terms):
    """Rattachement étendu (D-0066, point 3) : le nom commence par un terme qui désigne une seule entité (le plus long
    l'emporte), suivi seulement de mots de catégorie ou d'instrument (« ANTHROPIC SERIES G », « Nscale »). Renvoie
    (entity_id, terme), (None, terme) si un autre mot suit le terme, (None, None) sinon."""
    found = None
    for f in forms(name):
        toks = f.split()
        for i in range(len(toks), 0, -1):
            k = " ".join(toks[:i])
            if k in terms:
                if class_words_only(toks[i:]):
                    return terms[k], k
                found = found or k
                break
    return None, found


def scan_unlisted(zpath, lex, c=None, chunk=500_000):
    """Positions gardées d'une archive (D-0065, point 5) et leurs tables liées, avec les décomptes de toutes les
    positions qui contiennent une chaîne du lexique, par entité rattachée (nom d'émetteur) ou à défaut par
    chaîne, par niveau de juste valeur et par catégorie. Retourne (tables, statistiques, décomptes)."""
    c = c or cols()
    h = c["holding"]
    quoted = set(cfg_unlisted().get("quoted_levels") or ["1", "2"])
    hit = finder(lex["keep"])
    memo_hit, memo_att = {}, {}

    def lookup(values, memo, fn):
        for v in values:
            if v not in memo:
                memo[v] = fn(v) if v else None
        return memo
    kept, counts, columns = [], [], None
    with zipfile.ZipFile(zpath) as z:
        m = _member(z, c["tables"]["holding"])
        with z.open(m) as fh:
            for df in pd.read_csv(io.TextIOWrapper(fh, encoding="utf-8", errors="replace"), sep="\t", dtype=str,
                                  chunksize=chunk, quoting=csv.QUOTE_NONE, keep_default_na=False, na_values=[""],
                                  on_bad_lines="warn"):
                columns = columns or list(df.columns)
                name = df[h["issuer_name"]].fillna("")
                title = df[h["title"]].fillna("")
                nh = name.map(lookup(name.unique(), memo_hit, hit))
                th = title.map(lookup(title.unique(), memo_hit, hit))
                matched = nh.notna() | th.notna()
                if not matched.any():
                    continue
                x = df[matched]
                nm = name[matched]
                ent = nm.map(lookup(nm.unique(), memo_att, lambda v: attribute(v, lex["legal"])[0]))
                key = ent.where(ent.notna(), nh[matched].where(nh[matched].notna(), th[matched]))
                level = x[h["fair_value_level"]].fillna("").str.strip()
                counts.append(pd.DataFrame({"kind": ent.notna().map({True: "entity", False: "string"}).values,
                                            "key": key.values, "level": level.values,
                                            "asset_cat": x[h["asset_cat"]].fillna("").values}))
                k = x[~level.isin(quoted)]
                if len(k):
                    kept.append(k)
        hold = pd.concat(kept, ignore_index=True) if kept else pd.DataFrame(columns=columns or [])
        ids = set(hold[h["holding_id"]]) if len(hold) else set()
        acc = set(hold[h["accession"]]) if len(hold) else set()
        out = {"holding": hold}
        for t in ("identifiers", "debt"):
            out[t] = _read(z, c["tables"][t], key=(c[t]["holding_id"], ids))
        for t in ("submission", "registrant", "fund"):
            out[t] = _read(z, c["tables"][t], key=(c[t]["accession"], acc))
    cnt = (pd.concat(counts, ignore_index=True).groupby(["kind", "key", "level", "asset_cat"], dropna=False).size()
           .reset_index(name="n") if counts else pd.DataFrame(columns=["kind", "key", "level", "asset_cat", "n"]))
    stats = {k: len(v) for k, v in out.items()}
    stats["matched"] = int(cnt["n"].sum()) if len(cnt) else 0
    stats["matched_by_level"] = ({str(k): int(v) for k, v in cnt.groupby("level")["n"].sum().items()} if len(cnt) else {})
    return out, stats, cnt


def _scan_unlisted_job(name, zpath, lex, meta):
    import hashlib
    sha = hashlib.sha256()
    with open(zpath, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            sha.update(b)
    out, stats, cnt = scan_unlisted(zpath, lex)
    d = BASE / name / U_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    for k, df in out.items():
        df.to_parquet(d / f"{k}.parquet", index=False, compression="zstd")
    cnt.to_parquet(d / "counts.parquet", index=False, compression="zstd")
    return dict(meta, status="scanned", bytes=zpath.stat().st_size, sha256=sha.hexdigest(), stats=stats)


def u_manifest():
    if not U_MANIFEST.exists():
        return {}
    return {r["name"]: r for r in (json.loads(l) for l in U_MANIFEST.read_text(encoding="utf-8").splitlines() if l)}


def _u_append(rec):
    with open(U_MANIFEST, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def lexicon_path(version):
    return BASE / f"unlisted_lexicon_{version}.json"


def save_lexicon(lex):
    """Lexique figé du scan, gardé sous sa version (D-0065, point 4)."""
    p = lexicon_path(lex["version"])
    if not p.exists():
        BASE.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({k: lex[k] for k in ("version", "parts", "legal", "keep")}, ensure_ascii=False,
                                sort_keys=True, indent=0), encoding="utf-8")
    return p


def fetch_unlisted(only=None):
    """De la plus récente archive à la plus ancienne : tirée par le client unique pendant que la précédente se
    scanne dans un processus à part, puis effacée (D-0065, point 3). Une archive publiée après l'as_of n'est ni
    gardée ni scannée ; une archive déjà scannée avec la même version du lexique ne se tire pas."""
    from concurrent.futures import ProcessPoolExecutor
    from .discovery import AS_OF
    cfg = config.load()
    n = cfg_nport(cfg)
    lex = lexicon(cfg=cfg)
    save_lexicon(lex)
    client = net.SecClient(AS_OF, cfg)
    done, d58 = u_manifest(), manifest()

    def todo_(a):
        r = done.get(a["name"]) or {}
        return (not only or a["name"] in only) and not (
            r.get("status") == "after_as_of" or (r.get("status") == "scanned" and r.get("lexicon") == lex["version"]))
    todo = [a for a in in_period(archive_list(), n["period"][0], n["period"][1]) if todo_(a)]
    BASE.mkdir(parents=True, exist_ok=True)
    print("lexique", lex["version"], json.dumps(lex["parts"]), "; archives à tirer :", len(todo), flush=True)

    def finish(p):
        if p is None:
            return
        a, zpath, fut = p
        try:
            rec = fut.result()
        except Exception as exc:          # scan échoué : l'archive reste à reprendre
            rec = dict(a, status="parse_failed", reason=repr(exc)[:300], lexicon=lex["version"])
        if zpath.exists():
            zpath.unlink()
        _u_append(rec)
        print(a["name"], rec.get("status"), json.dumps(rec.get("stats") or {}), flush=True)
    pending = None
    with ProcessPoolExecutor(max_workers=1) as pp:
        try:
            for a in todo:
                zpath = BASE / f"{a['name']}.zip"
                t0 = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
                try:
                    _, headers = client.get(a["url"], timeout=900, dest=zpath)
                except net.NotCollected as exc:
                    finish(pending)
                    pending = None
                    _u_append(dict(a, status="not_collected", reason=str(exc), lexicon=lex["version"]))
                    print(a["name"], "not_collected", exc, flush=True)
                    continue
                lm, published = _published(headers)
                meta = dict(a, retrieved=t0, last_modified=lm, lexicon=lex["version"],
                            last_modified_d58=(d58.get(a["name"]) or {}).get("last_modified"))
                finish(pending)           # le scan précédent a tourné pendant ce tirage
                pending = None
                if published and published > AS_OF:
                    zpath.unlink()        # connaissance postérieure, ni gardée ni scannée
                    _u_append(dict(meta, status="after_as_of"))
                    print(a["name"], "after_as_of", lm, flush=True)
                    continue
                pending = (a, zpath, pp.submit(_scan_unlisted_job, a["name"], zpath, lex, meta))
        finally:
            finish(pending)


# -- positions, rattachement, cotation --------------------------------------------------------------

def u_positions(c=None, archives=None):
    """Positions gardées des archives scannées (D-0065), jointes à leur dépôt, leur série, leur déclarant, leur
    ISIN et leurs caractéristiques de dette (Item C.9, D-0066) ; une ligne par position déclarée."""
    c = c or cols()
    m = u_manifest()
    h, s, f, g, i, b = (c[k] for k in ("holding", "submission", "fund", "registrant", "identifiers", "debt"))
    conv = cfg_nport().get("exchange_rate_convention", "currency_per_usd")
    rows = []
    for name, r in sorted(m.items()):
        if r.get("status") != "scanned" or (archives and name not in archives):
            continue
        d = BASE / name / U_SUBDIR
        t = {k: pd.read_parquet(d / f"{k}.parquet") for k in U_TABLES}
        x = t["holding"].rename(columns={v: k for k, v in h.items()})
        if x.empty:
            continue
        x = x.merge(t["submission"].rename(columns={v: k for k, v in s.items()}), on="accession", how="left")
        x = x.merge(t["fund"].rename(columns={v: k for k, v in f.items()}), on="accession", how="left", suffixes=("", "_fund"))
        x = x.merge(t["registrant"].rename(columns={v: k for k, v in g.items()}), on="accession", how="left", suffixes=("", "_reg"))
        ids = t["identifiers"].rename(columns={v: k for k, v in i.items()})
        if len(ids):
            ids = ids.groupby("holding_id", as_index=False).agg({"isin": lambda v: next((y for y in v if isinstance(y, str) and y), None)})
            x = x.merge(ids, on="holding_id", how="left")
        else:
            x["isin"] = None
        debt = t["debt"].rename(columns={v: k for k, v in b.items()}).reindex(columns=list(b))   # Item C.9 (D-0066)
        x = x.merge(debt.drop_duplicates("holding_id"), on="holding_id", how="left", suffixes=("", "_debt"))
        x["archive"] = name
        for col in ("filing_date", "report_date", "maturity"):
            x[col] = [_iso(v) for v in x[col]]
        x["value_local"] = [_local_value(v, rr, cur, conv) for v, rr, cur in zip(x["value_usd"], x["exchange_rate"], x["currency"])]
        rows.append(x)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def attributed(p, ent_rows=None, reg=None, cfg=None):
    """Rattachement des positions sur le registre courant : dénomination légale en tête du nom (D-0065, point 6),
    à défaut terme de la configuration suivi de mots de catégorie ou d'instrument (D-0066, point 3). Entité, forme
    légale trouvée, règle qui rattache, et groupe de l'entité à la date de portefeuille (vue as_known)."""
    from .entities import Registry
    ent_rows = _entity_rows() if ent_rows is None else ent_rows
    reg = reg or Registry(ent_rows)
    legal = legal_forms(ent_rows)
    terms = term_forms(ent_rows, cfg)
    names = p["issuer_name"].fillna("")
    memo = {}
    for nm in names.unique():
        e, k = attribute(nm, legal) if nm else (None, None)
        t = term_attribute(nm, terms)[0] if nm and e is None else None
        memo[nm] = (e or t, k, "legal_name" if e else ("config_term" if t else None))
    p = p.copy()
    p["entity_id"] = [memo[nm][0] for nm in names]
    p["legal_form"] = [memo[nm][1] for nm in names]
    p["attribution"] = [memo[nm][2] for nm in names]
    p["node"] = [reg.group_at(e, d, "as_known") if e else None for e, d in zip(p["entity_id"], p["report_date"])]
    return p


def tickers(cfg=None):
    """CIK (dix chiffres) -> symboles, d'après la liste d'EDGAR en cache (D-0065, point 7)."""
    day = cfg_unlisted(cfg).get("tickers") or "2026-10-07"
    d = json.loads(cache.read(cache.api_path("none", "company_tickers", day)))
    out = {}
    for v in d.values():
        out.setdefault(str(v["cik_str"]).zfill(10), []).append(v["ticker"])
    return out


def listing_date(cik, as_of, forms_=("424B4", "424B1")):
    """Dépôt du premier prospectus d'introduction (424B4 ou 424B1, à l'as_of au plus) dans les submissions en
    cache ; "" si elles n'en montrent aucun (cotée sur toute la période) ; None si elles ne sont pas en cache,
    ou pas toutes leurs pages (D-0065, point 7)."""
    c = str(cik).zfill(10)
    main = cache.latest_api(c, "submissions")
    if main is None:
        return None
    j = json.loads(cache.read(main))
    pages = [j["filings"]["recent"]]
    for fdesc in j["filings"].get("files") or []:
        q = cache.latest_api(c, "submissions-" + fdesc["name"].rsplit("-", 1)[-1].replace(".json", ""))
        if q is None:
            return None
        pages.append(json.loads(cache.read(q)))
    dates = [d for pg in pages for fm, d in zip(pg.get("form", []), pg.get("filingDate", []))
             if fm in forms_ and d <= as_of]
    return min(dates) if dates else ""


def listing(ent_rows, as_of, tick=None, forms_=None):
    """Par entité dont le CIK porte un symbole : sa date de cotation ("" sur toute la période, None si inconnue)."""
    tick = tickers() if tick is None else tick
    forms_ = tuple(forms_ or cfg_unlisted().get("listing_forms") or ("424B4", "424B1"))
    out = {}
    for r in ent_rows:
        if r["record_kind"] == "entity" and r.get("cik") and str(r["cik"]).zfill(10) in tick:
            out[r["entity_id"]] = listing_date(r["cik"], as_of, forms_)
    return out


def fetch_listing_submissions(as_of=None):
    """Submissions des entités cotées sans date de cotation connue qui portent des positions de la mesure
    (D-0065, point 7) : tirées une fois par le client unique, toutes leurs pages, après le scan."""
    from .discovery import AS_OF
    from .edgar import Edgar
    as_of = as_of or AS_OF
    ent_rows = _entity_rows()
    listed = listing(ent_rows, as_of)
    sel, _ = mark_selection(attributed(u_positions(), ent_rows), as_of, {})
    need = sorted({e for e in sel["entity_id"] if e in listed and listed[e] is None})
    ciks = {r["entity_id"]: r["cik"] for r in ent_rows if r["record_kind"] == "entity" and r["entity_id"] in need}
    ed = Edgar(net.SecClient(as_of, config.load()), as_of)
    for e, cik in sorted(ciks.items()):
        try:
            _, rows, pages, complete = ed.submissions(cik)
        except net.NotCollected as exc:
            print(e, cik, "non tirées :", exc, flush=True)
            continue
        print(e, cik, len(rows), "dépôts", "complet" if complete else "incomplet", "; cotation :",
              listing_date(cik, as_of) or "toute la période", flush=True)


def quoted_archives(m=None, cats=None):
    """(entité, archive) où la majorité des positions en actions de l'entité, toutes séries confondues, sont évaluées
    aux niveaux 1 ou 2 : l'entité y est cotée (D-0065, point 15, sur la règle de majorité de D-0058, point 28)."""
    m = u_manifest() if m is None else m
    cats = cats or (cfg_unlisted().get("mark") or {}).get("asset_cats") or ["EC", "EP"]
    quoted = set(cfg_unlisted().get("quoted_levels") or ["1", "2"])
    out = set()
    for name, r in sorted(m.items()):
        f = BASE / name / U_SUBDIR / "counts.parquet"
        if r.get("status") != "scanned" or not f.exists():
            continue
        c = pd.read_parquet(f)
        c = c[(c["kind"] == "entity") & c["asset_cat"].isin(cats)]
        for e, g in c.groupby("key"):
            if 2 * int(g.loc[g["level"].isin(quoted), "n"].sum()) > int(g["n"].sum()):
                out.add((e, name))
    return out


def mark_selection(p, as_of, listed, quoted=None):
    """Positions de nport_equity_mark (D-0065, points 8 et 15), avant le dernier dépôt de chaque série, et décompte
    des positions écartées à chaque étape. `listed` : entité à symbole -> date de cotation ("" toujours, None
    inconnue) ; `quoted` : (entité sans symbole, archive) où l'entité est cotée (`quoted_archives`)."""
    mk = cfg_unlisted().get("mark") or {}
    quoted = quoted or set()
    steps = {}

    def keep(q, step, mask):
        mask = pd.Series(list(mask), index=q.index, dtype=bool)
        steps[step] = int((~mask).sum())
        return q[mask].copy()
    p = keep(p, "not_attributed", p["entity_id"].notna() & p["node"].notna())
    p = keep(p, "not_equity", p["asset_cat"].isin(mk.get("asset_cats") or ["EC", "EP"]))
    p = keep(p, "not_shares", p["unit"] == (mk.get("unit") or "NS"))
    p = keep(p, "not_long", p["payoff"] == (mk.get("payoff") or "Long"))
    p = keep(p, "not_positive", [(_dec(v) or 0) > 0 for v in p["balance"]])
    p = keep(p, "not_level_3", p["fair_value_level"].fillna("").str.strip() == str(mk.get("level") or "3"))
    p = keep(p, "listing_unknown", [not (e in listed and listed[e] is None) for e in p["entity_id"]])
    p = keep(p, "listed_at_date", [e not in listed or (listed[e] != "" and str(d) < listed[e])
                                   for e, d in zip(p["entity_id"], p["report_date"])])
    arch = p["archive"] if "archive" in p else [None] * len(p)
    p = keep(p, "quoted_in_archive", [e in listed or (e, a) not in quoted for e, a in zip(p["entity_id"], arch)])
    return p, steps


def equity_key(asset_cat, isin, cusip, title):
    """Titre d'une position en actions : catégorie, puis ISIN, à défaut CUSIP, à défaut intitulé normalisé."""
    from .graph import normalize_name
    i, cu = _ident(isin, ISIN_RX), _ident(cusip, CUSIP_RX)
    return f"{asset_cat}|" + (i or (f"CUSIP:{cu}" if cu else "TITLE:" + normalize_name(title or "")))


def fund_ref(series_id, cik):
    """Contrepartie d'une cellule : la série du fonds, à défaut son déclarant (fonds fermé)."""
    if isinstance(series_id, str) and series_id:
        return f"series:{series_id}"
    return f"cik:{str(cik).zfill(10)}" if isinstance(cik, str) and cik else "none"


MARK_BASIS = ("valeur déclarée par action par un fonds enregistré (Form N-PORT Data Sets), perspective counterparty : "
              "valeur dans la monnaie du titre sur le nombre d'actions, positions en actions évaluées au niveau 3, au dernier "
              "dépôt de la série pour la date de portefeuille ; jamais une valorisation du nœud ni un fait comptable, hors des "
              "mesures de financement, de l'exposition, des paires, des cycles et de l'annexe F (D-0065, point 8)")
HELD_BASIS = ("somme des valeurs en dollars que les fonds enregistrés déclarent pour leurs positions en actions du nœud évaluées "
              "au niveau 3, au dernier rapport de chaque série dans le trimestre civil (Form N-PORT Data Sets), perspective "
              "counterparty ; jamais une valeur du nœud, hors des mesures de financement, de l'exposition, des paires, des "
              "cycles et de l'annexe F (D-0065, point 8)")


def quarter_end(d):
    y, m = int(d[:4]), int(d[5:7])
    q = (m - 1) // 3 + 1
    return (dt.date(y + (q == 4), (3 * q) % 12 + 1, 1) - dt.timedelta(days=1)).isoformat()


FILING_DAYS = 60     # un N-PORT se dépose dans les 60 jours qui suivent la fin du trimestre du fonds (formulaire, Instruction générale A)


def quarter_complete(qe, m=None):
    """Un trimestre civil est complet si les archives scannées couvrent tous les dépôts de ses rapports : du début du
    trimestre à 60 jours après sa fin. Sinon sa valeur détenue est partielle (D-0065, point 16)."""
    m = u_manifest() if m is None else m
    sc = [r for r in m.values() if r.get("status") == "scanned"]
    if not sc:
        return False
    lo, hi = min(r["filed_from"] for r in sc), max(r["filed_to"] for r in sc)
    end = dt.date.fromisoformat(qe)
    start = dt.date(end.year, end.month - 2, 1).isoformat()
    return start >= lo and (end + dt.timedelta(days=FILING_DAYS)).isoformat() <= hi


def u_attributed(ent_rows=None, reg=None):
    """Positions gardées, rattachées sur le registre courant (un seul chargement pour les mesures et les exclusions)."""
    p = u_positions()
    return p if p.empty else attributed(p, _entity_rows() if ent_rows is None else ent_rows, reg)


def u_selected(as_of, ent_rows=None, reg=None, tick=None, p=None):
    """Positions de la mesure, au dernier dépôt de chaque série par date, avec leur titre ; et les étapes."""
    ent_rows = _entity_rows() if ent_rows is None else ent_rows
    p = u_attributed(ent_rows, reg) if p is None else p
    if p.empty:
        return p, {}
    sel, steps = mark_selection(p, as_of, listing(ent_rows, as_of, tick), quoted_archives())
    sel = latest_by_fund(sel)
    if len(sel):
        sel["security"] = [equity_key(a, i, cu, t) for a, i, cu, t in zip(sel["asset_cat"], sel["isin"], sel["cusip"], sel["title"])]
        sel["fund_ref"] = [fund_ref(s, k) for s, k in zip(sel["series_id"], sel["cik"])]
    return sel, steps


def u_cells(as_of, ent_rows=None, reg=None, tick=None, p=None):
    """Cellules nport_equity_mark (nœud, fonds, titre, date) et nport_equity_held (nœud, trimestre civil)."""
    from .measures import cell
    if not u_manifest():
        return []
    sel, _ = u_selected(as_of, ent_rows, reg, tick, p)
    if sel.empty:
        return []
    kd = sel.groupby("accession")["filing_date"].max().to_dict()
    out = []
    for (node, fref, sec, d), g in sel.groupby(["node", "fund_ref", "security", "report_date"], sort=True):
        shares = sum(_dec(v) for v in g["balance"])
        vloc = [_dec(v) for v in g["value_local"]]
        usd = sum(_dec(v) or 0 for v in g["value_usd"])
        cur = sorted(set(g["currency"].dropna()))
        fl = {"perspective": "counterparty", "shares": str(shares), "value_usd": str(usd), "currency": ";".join(cur),
              "positions": int(len(g)), "asset_cat": sec.split("|", 1)[0],
              "title": next(iter(sorted(set(g["title"].dropna()))), None),
              "issuer_names": sorted(set(g["issuer_name"].dropna())), "entities": sorted(set(g["entity_id"])),
              "restricted": sorted(set(g["restricted"].dropna())) if "restricted" in g else [],
              "series_name": next(iter(sorted(set(g["series_name"].dropna()))), None),
              "registrant_name": next(iter(sorted(set(g["registrant_name"].dropna()))), None),
              "accessions": sorted(set(g["accession"])), "basis": MARK_BASIS}
        k = max(str(kd.get(a) or "") for a in g["accession"])[:10] or None
        if len(cur) > 1:
            out.append(cell("nport_equity_mark", node, None, d, "as_known", as_of, counterparty=fref, breakdown=sec,
                            status="not_determinable", nd_reason="mixed_currency", knowledge_date=k, flags=fl))
        elif any(v is None for v in vloc):
            out.append(cell("nport_equity_mark", node, None, d, "as_known", as_of, counterparty=fref, breakdown=sec,
                            status="not_determinable", nd_reason="not_disclosed", knowledge_date=k,
                            flags=dict(fl, note="taux de change non déclaré : valeur dans la monnaie du titre inconnue")))
        else:
            num = sum(vloc)
            out.append(cell("nport_equity_mark", node, None, d, "as_known", as_of, counterparty=fref, breakdown=sec,
                            value=num / shares, numerator=num, denominator=shares, unit=cur[0] if cur else None,
                            knowledge_date=k, flags=fl))
    sel = sel.assign(quarter=[quarter_end(d) for d in sel["report_date"]])
    last = sel.groupby(["node", "quarter", "fund"])["report_date"].transform("max")
    q = sel[sel["report_date"] == last]
    man = u_manifest()
    complete = {qe: quarter_complete(qe, man) for qe in set(q["quarter"])}
    for (node, qe), g in q.groupby(["node", "quarter"], sort=True):
        usd = sum(_dec(v) or 0 for v in g["value_usd"])
        fl = {"perspective": "counterparty", "series": int(g["fund"].nunique()), "positions": int(len(g)),
              "report_dates": [min(g["report_date"]), max(g["report_date"])],
              "entities": sorted(set(g["entity_id"])), "accessions": sorted(set(g["accession"]))[:20], "basis": HELD_BASIS}
        if not complete[qe]:
            fl["coverage"] = ("trimestre partiel : les archives scannées ne couvrent pas tous les dépôts de ses rapports, "
                              "du début du trimestre à 60 jours après sa fin")
        out.append(cell("nport_equity_held", node, None, qe, "as_known", as_of, value=usd, unit="USD",
                        status="computed" if complete[qe] else "partial",
                        knowledge_date=max(str(kd.get(a) or "") for a in g["accession"])[:10] or None, flags=fl))
    return out


def neighbors(p):
    """Noms d'émetteur gardés et non rattachés (D-0065, point 6) : par nom déclaré, la chaîne qui l'a gardé, le
    nombre de positions et de séries, et la valeur déclarée en dollars à sa dernière date."""
    p = p[p["entity_id"].isna()]
    if p.empty:
        return []
    out = []
    for nm, g in p.groupby(p["issuer_name"].fillna(""), sort=True):
        d = max(x for x in g["report_date"] if x) if g["report_date"].notna().any() else None
        at = g[g["report_date"] == d] if d else g
        out.append({"name": nm, "legal_form": next((x for x in g["legal_form"] if isinstance(x, str) and x), None),
                    "positions": int(len(g)), "series": int(pd.Series(fund_key(g)).nunique()),
                    "last_date": d, "value_usd_last": str(sum(_dec(v) or 0 for v in at["value_usd"])),
                    "asset_cats": sorted(set(g["asset_cat"].dropna()))})
    return out


def u_exclusions(as_of, ent_rows=None, reg=None, tick=None, p=None):
    """Archives de la période non tirées, non scannées, publiées après l'as_of ou scannées avec un lexique
    antérieur ; noms voisins non rattachés ; entités cotées sans date de cotation connue ; prêts de plateforme (§11)."""
    cfg = config.load()
    n = cfg_nport(cfg)
    m = u_manifest()
    if not n or not m:
        return []
    ent_rows = _entity_rows() if ent_rows is None else ent_rows
    legal = set(legal_forms(ent_rows))
    terms = set(term_forms(ent_rows, cfg))
    out = []

    def ex(kind, key, reason, detail, group=None):
        out.append({"exclusion_key": f"{reason}:nport_unlisted:{key}", "item_kind": kind,
                    "item_key": f"nport_unlisted:{key}", "reason": reason, "detail": detail, "group_id": group,
                    "accession": None, "content_key": None, "as_of": as_of})
    scanned_with = {}
    for a in in_period(archive_list(), n["period"][0], n["period"][1]):
        r = m.get(a["name"])
        if r is None:
            ex("period", a["name"], "not_processed", f"archive des Form N-PORT Data Sets non tirée pour les non-cotés "
               f"({a['filed_from']} au {a['filed_to']}, D-0065)")
        elif r.get("status") == "not_collected":
            ex("period", a["name"], "not_collected", f"archive des Form N-PORT Data Sets non tirée : {r.get('reason')}")
        elif r.get("status") == "parse_failed":
            ex("period", a["name"], "parse_failed", f"archive des Form N-PORT Data Sets non scannée : {r.get('reason')}")
        elif r.get("status") == "after_as_of":
            ex("period", a["name"], "not_public", f"archive des Form N-PORT Data Sets publiée après l'as_of (Last-Modified "
               f"{r.get('last_modified')}) : connaissance postérieure, ni gardée ni lue (D-0065, point 3)")
        else:
            scanned_with.setdefault(r.get("lexicon"), []).append(a["name"])
    for v, names in sorted(scanned_with.items(), key=lambda kv: str(kv[0])):
        lp = lexicon_path(v)
        lx = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else None
        new = sorted(legal - set(lx["legal"])) if lx else None
        new_terms = sorted(terms - set(lx["keep"])) if lx else []          # D-0066 : terme qui rattache, non gardé
        if lx is None:
            why = f"lexique {v} introuvable"
        elif new_terms:
            why = f"{len(new)} dénominations légales et {len(new_terms)} termes ajoutés depuis, non scannés"
        else:
            why = f"{len(new)} dénominations légales ajoutées depuis, non scannées"
        if new is None or new or new_terms:
            for nm in names:
                ex("period", nm, "not_processed", f"archive scannée avec un lexique antérieur : {why} (D-0065, point 14)")
    p = u_attributed(ent_rows, reg) if p is None else p
    if p.empty:
        return out
    for r in neighbors(p):
        reason = "conflicting" if r["legal_form"] else "pending_entity"
        why = (f"commence par « {r['legal_form']} », suivie d'une autre forme juridique" if r["legal_form"]
               else "aucune dénomination légale du registre en tête du nom")
        usd = f"{round(float(r['value_usd_last'])):,}".replace(",", " ")
        ex("entity", r["name"], reason, f"nom d'émetteur déclaré par des fonds, gardé par le lexique et non rattaché ({why}) : "
           f"{r['positions']} positions, {r['series']} séries, {usd} $ déclarés au {r['last_date']} "
           f"({', '.join(r['asset_cats'])}) ; jamais rattaché sans extrait (D-0065, point 6)")
    listed = listing(ent_rows, as_of, tick)
    reach, _ = mark_selection(p, as_of, {})       # positions qui atteignent l'étape de la cotation (point 7)
    unknown = sorted({e for e in reach["entity_id"] if e in listed and listed[e] is None})
    for e in unknown:
        ex("entity", e, "not_processed", "entité cotée (symbole au 2026-10-07) sans submissions complètes en cache : "
           "date de cotation inconnue, positions hors de la mesure (D-0065, point 7)")
    plat = []
    credit_selection(p, out=plat)
    for r in platforms(plat):
        ex("entity", f"platform:{r['entity_id']}", "out_of_scope",
           f"prêts de plateforme déclarés sous « {r['name']} » ({r['rule']}) : {r['positions']} positions, {r['filings']} "
           f"dépôts, {r['series']} séries, du {r['first']} au {r['last']} ; le déclarant nomme la plateforme qui les a "
           "consentis, non l'emprunteur, et leurs débiteurs ne sont jamais lus : hors de nport_credit_mark (D-0066, point 4)",
           group=r["node"])
    return out


# -- D-0066, point 4 : marques de crédit des prêts et de la dette des nœuds, évalués par les fonds ---------------

CREDIT_BASIS = ("valorisation déclarée par des fonds enregistrés (Form N-PORT Data Sets), perspective counterparty : somme des "
                "valeurs dans la monnaie du titre sur la somme des nominaux, prêts ou titres de dette du nœud évalués au "
                "niveau 3, au dernier dépôt de chaque série pour la date de portefeuille ; jamais une probabilité de défaut ni "
                "un fait comptable de l'emprunteur, hors des mesures de financement, de l'exposition, des paires, des cycles et "
                "de l'annexe F (D-0066, point 4)")
PLATFORM_RULES = {"pool": "plus de 100 positions d'un même émetteur dans un dépôt", "title": "intitulé « Marketplace Loan »"}


def cfg_credit(cfg=None):
    return cfg_unlisted(cfg).get("credit") or {}


def credit_selection(p, out=None):
    """Positions de nport_credit_mark (D-0066, point 4), avant le dernier dépôt de chaque série, et décompte des
    positions écartées à chaque étape : rattachées, prêts ou titres de dette, en nominal, longues, de nominal positif,
    au niveau 3, puis hors prêts de plateforme (plus de 100 positions d'un même émetteur dans un dépôt, ou intitulé
    « Marketplace Loan »). Les prêts de plateforme écartés s'ajoutent à `out` (colonne `platform`)."""
    cr = cfg_credit()
    steps = {}

    def keep(q, step, mask, rule=None):
        mask = pd.Series(list(mask), index=q.index, dtype=bool)
        steps[step] = int((~mask).sum())
        if rule and out is not None and (~mask).any():
            out.append(q[~mask].assign(platform=rule))
        return q[mask].copy()
    if p.empty:
        return p, steps
    p = keep(p, "not_attributed", p["entity_id"].notna() & p["node"].notna())
    p = keep(p, "not_credit", p["asset_cat"].isin(cr.get("asset_cats") or ["LON", "DBT"]))
    p = keep(p, "not_principal", p["unit"] == (cr.get("unit") or "PA"))
    p = keep(p, "not_long", p["payoff"] == (cr.get("payoff") or "Long"))
    p = keep(p, "not_positive", [(_dec(v) or 0) > 0 for v in p["balance"]])
    p = keep(p, "not_level_3", p["fair_value_level"].fillna("").str.strip() == str(cr.get("level") or "3"))
    n = p.groupby(["entity_id", "accession"])["balance"].transform("size") if len(p) else []
    p = keep(p, "platform_pool", [k <= int(cr.get("pool_max_positions") or 100) for k in n], "pool")
    rx = re.compile(cr.get("platform_title_rx") or r"\bmarketplace loans?\b", re.I)
    p = keep(p, "platform_title", [not (isinstance(t, str) and rx.search(t)) for t in p["title"]], "title")
    return p, steps


def platforms(frames):
    """Par entité : prêts de plateforme écartés, comptés (positions, dépôts, séries, dates), sans aucune valeur."""
    if not frames:
        return []
    x = pd.concat(frames, ignore_index=True)
    out = []
    for e, g in x.groupby("entity_id", sort=True):
        out.append({"entity_id": e, "node": next(iter(sorted(set(g["node"].dropna()))), None),
                    "name": _mode(g["issuer_name"].dropna()), "positions": int(len(g)),
                    "rule": " ; ".join(PLATFORM_RULES[k] for k in sorted(set(g["platform"]))),
                    "filings": int(g["accession"].nunique()), "series": int(pd.Series(fund_key(g)).nunique()),
                    "first": min(g["report_date"].dropna(), default=None), "last": max(g["report_date"].dropna(), default=None)})
    return out


def c_selected(as_of, ent_rows=None, reg=None, p=None):
    """Positions de nport_credit_mark, au dernier dépôt de chaque série par date, avec leur titre ; et les étapes."""
    p = u_attributed(ent_rows, reg) if p is None else p
    if p.empty:
        return p, {}
    sel, steps = credit_selection(p)
    sel = latest_by_fund(sel)
    if len(sel):
        sel["security"] = [equity_key(a, i, cu, t) for a, i, cu, t in zip(sel["asset_cat"], sel["isin"], sel["cusip"], sel["title"])]
    return sel, steps


def _share(g, col, den):
    """Part du nominal dont la rubrique `col` de l'Item C.9 vaut « Y »."""
    if col not in g:
        return None
    num = sum((_dec(b) or 0) for b, v in zip(g["balance"], g[col]) if isinstance(v, str) and v.strip().upper() == "Y")
    return str((num / den).quantize(Decimal("0.000001")))


def _extremes(values):
    v = sorted(x for x in values if x is not None)
    return [str(v[0]), str(v[-1])] if v else None


def c_cells(as_of, ent_rows=None, reg=None, p=None):
    """Cellules nport_credit_mark : une par nœud, catégorie (LON ou DBT), monnaie et date de portefeuille (D-0066)."""
    from .measures import cell
    from collections import Counter
    if not u_manifest():
        return []
    sel, _ = c_selected(as_of, ent_rows, reg, p)
    if sel.empty:
        return []
    kd = sel.groupby("accession")["filing_date"].max().to_dict()
    sel = sel.assign(cur=sel["currency"].fillna("").str.strip().str.upper())
    out = []
    for (node, cat, cur, d), g in sel.groupby(["node", "asset_cat", "cur", "report_date"], sort=True):
        den = sum(_dec(v) for v in g["balance"])
        vloc = [_dec(v) for v in g["value_local"]]
        tt = Counter(t.strip() for t in g["title"].dropna() if t.strip())
        fl = {"perspective": "counterparty", "principal": str(den), "value_usd": str(sum(_dec(v) or 0 for v in g["value_usd"])),
              "currency": cur or None, "asset_cat": cat, "positions": int(len(g)), "series": int(g["fund"].nunique()),
              "titles": int(g["security"].nunique()),
              "maturity": _extremes(g["maturity"]) if "maturity" in g else None,
              "coupon": _extremes(_dec(v) for v in g["coupon"]) if "coupon" in g else None,
              "top_titles": [[t, n] for t, n in sorted(tt.items(), key=lambda kv: (-kv[1], kv[0]))[:3]],
              "default_share": _share(g, "is_default", den), "arrears_share": _share(g, "arrears", den),
              "pik_share": _share(g, "pik", den),
              "c9_share": str((sum(_dec(b) or 0 for b, v in zip(g["balance"], g["is_default"]) if isinstance(v, str))
                               / den).quantize(Decimal("0.000001"))) if "is_default" in g else None,
              "issuer_names": sorted(set(g["issuer_name"].dropna()))[:10], "entities": sorted(set(g["entity_id"])),
              "attribution": sorted(set(g["attribution"].dropna())) if "attribution" in g else [],
              "accessions": sorted(set(g["accession"]))[:20], "basis": CREDIT_BASIS}
        k = max(str(kd.get(a) or "") for a in g["accession"])[:10] or None
        bk = f"{cat}|{cur or 'none'}"
        if any(v is None for v in vloc):
            out.append(cell("nport_credit_mark", node, None, d, "as_known", as_of, breakdown=bk, status="not_determinable",
                            nd_reason="not_disclosed", knowledge_date=k,
                            flags=dict(fl, note="taux de change non déclaré : valeur dans la monnaie du titre inconnue")))
        else:
            num = sum(vloc)
            out.append(cell("nport_credit_mark", node, None, d, "as_known", as_of, breakdown=bk, value=num / den,
                            numerator=num, denominator=den, unit="pure", knowledge_date=k, flags=fl))
    return out


def unlisted(as_of, ent_rows=None, reg=None, tick=None):
    """Cellules et exclusions de D-0065 et D-0066, sur un seul chargement des positions rattachées."""
    ent_rows = _entity_rows() if ent_rows is None else ent_rows
    if not u_manifest():
        return [], u_exclusions(as_of, ent_rows, reg, tick)
    p = u_attributed(ent_rows, reg)
    return (u_cells(as_of, ent_rows, reg, tick, p) + c_cells(as_of, ent_rows, reg, p),
            u_exclusions(as_of, ent_rows, reg, tick, p))


def c_volume(as_of=None):
    """Décomptes de la sélection des marques de crédit, sans aucune valeur (D-0066, point 11)."""
    from .discovery import AS_OF
    from collections import Counter
    as_of = as_of or AS_OF
    ent_rows = _entity_rows()
    p = u_attributed(ent_rows)
    by_rule = Counter(zip(p["attribution"].fillna("none"), p["asset_cat"].fillna("")))
    term = p[p["attribution"] == "config_term"]
    plat = []
    sel, steps = credit_selection(p, out=plat)
    last = latest_by_fund(sel)
    return {"positions": int(len(p)), "by_rule_and_category": {f"{r}/{a}": int(n) for (r, a), n in sorted(by_rule.items())},
            "term_names": int(term["issuer_name"].nunique()),
            "term_by_node": dict(Counter(term["node"].fillna("none")).most_common()),
            "steps": steps, "platforms": platforms(plat), "selected": int(len(sel)), "after_latest_filing": int(len(last)),
            "nodes": int(last["node"].nunique()), "series": int(last["fund"].nunique()),
            "report_dates": int(last["report_date"].nunique()),
            "first_last": [min(last["report_date"]), max(last["report_date"])] if len(last) else None,
            "by_node": dict(Counter(last["node"]).most_common()),
            "cells": int(last.groupby(["node", "asset_cat", last["currency"].fillna(""), "report_date"]).ngroups) if len(last) else 0}


def u_volume(as_of=None):
    """Décomptes du scan et de la sélection, sans aucune valeur de la mesure (consignés avant calcul)."""
    from .discovery import AS_OF
    as_of = as_of or AS_OF
    m = u_manifest()
    cnt = []
    for name, r in sorted(m.items()):
        f = BASE / name / U_SUBDIR / "counts.parquet"
        if r.get("status") == "scanned" and f.exists():
            cnt.append(pd.read_parquet(f).assign(archive=name))
    cnt = pd.concat(cnt, ignore_index=True) if cnt else pd.DataFrame(columns=["kind", "key", "level", "asset_cat", "n"])
    ent_rows = _entity_rows()
    from .entities import Registry
    reg = Registry(ent_rows)
    p = attributed(u_positions(), ent_rows, reg)
    listed = listing(ent_rows, as_of)
    sel, steps = mark_selection(p, as_of, listed, quoted_archives(m))
    last = latest_by_fund(sel)
    node_of = {e: reg.group_at(e, as_of, "as_known") for e in set(p["entity_id"].dropna())}
    by_node = {}
    for node, g in last.groupby("node"):
        by_node[node] = {"positions": int(len(g)), "series": int(g["fund"].nunique()), "entities": sorted(set(g["entity_id"])),
                         "report_dates": int(g["report_date"].nunique()),
                         "first_last": [min(g["report_date"]), max(g["report_date"])]}
    ents = cnt[cnt["kind"] == "entity"]
    lvl = {}
    for (e, lv), n_ in ents.groupby(["key", "level"])["n"].sum().items():
        nk = node_of.get(e) or reg.group_at(e, as_of, "as_known") or e
        k = lv or "vide"
        lvl.setdefault(nk, {})[k] = lvl.setdefault(nk, {}).get(k, 0) + int(n_)
    nb = neighbors(p)
    return {"archives": {s: sum(1 for r in m.values() if r.get("status") == s) for s in sorted({r.get("status") for r in m.values()})},
            "bytes": sum(int(r.get("bytes") or 0) for r in m.values() if r.get("status") == "scanned"),
            "lexicon": sorted({r.get("lexicon") for r in m.values() if r.get("lexicon")}),
            "matched": int(cnt["n"].sum()) if len(cnt) else 0,
            "matched_by_level": {str(k): int(v) for k, v in cnt.groupby("level")["n"].sum().items()} if len(cnt) else {},
            "kept_positions": int(len(p)), "attributed": int(p["entity_id"].notna().sum()),
            "neighbors": len(nb), "neighbor_positions": sum(r["positions"] for r in nb),
            "listed_entities_attributed": sorted({e for e in p["entity_id"].dropna() if e in listed}),
            "listing": {e: listed[e] for e in sorted({e for e in p["entity_id"].dropna() if e in listed})},
            "steps": steps, "selected": int(len(sel)), "after_latest_filing": int(len(last)),
            "by_node": by_node, "matched_levels_by_node": lvl}


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
    elif cmd == "unlisted-lexicon":
        lx = lexicon()
        print(lx["version"], json.dumps(lx["parts"]), save_lexicon(lx))
    elif cmd == "unlisted-fetch":
        fetch_unlisted(only=set(sys.argv[2:]) or None)
    elif cmd == "unlisted-submissions":
        fetch_listing_submissions()
    elif cmd == "unlisted-volume":
        print(json.dumps(u_volume(), ensure_ascii=False, indent=1, default=str))
    elif cmd == "credit-volume":
        print(json.dumps(c_volume(), ensure_ascii=False, indent=1, default=str))
    elif cmd == "unlisted-status":
        um = u_manifest()
        print(len(um), "archives au manifeste des non-cotés ;",
              {s: sum(1 for r in um.values() if r.get("status") == s) for s in sorted({r.get("status") for r in um.values()})})
    else:
        m = manifest()
        leis = softbank_leis(m)
        print("LEI de SoftBank :", sorted(leis))
        print(len(m), "archives au manifeste ;", sum(1 for r in m.values() if r.get("status") == "scanned"), "scannées ;",
              sum(1 for r in m.values() if r.get("status") == "after_as_of"), "publiées après l'as_of ; à rescanner :",
              [k for k, r in sorted(m.items(), reverse=True) if r.get("status") == "scanned" and applied(r) < leis])
