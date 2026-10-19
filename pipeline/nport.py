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
        found = set(hold.loc[hold[h["issuer_name"]].fillna("").str.contains(NAME_RX), h["issuer_lei"]].dropna()) - {"N/A", ""}
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


def fetch(only=None):
    """De la plus récente archive à la plus ancienne : tirée par le client unique, scannée dans un
    processus à part, puis effacée. Les LEI relevés s'appliquent aux archives scannées ensuite ; une
    archive scannée avant qu'un LEI ne soit relevé est signalée (`leis_missing`)."""
    from concurrent.futures import ProcessPoolExecutor
    cfg = config.load()
    n = cfg_nport(cfg)
    client = net.SecClient(cfg.get("as_of"), cfg)
    todo = in_period(archive_list(), n["period"][0], n["period"][1])
    done = manifest()
    leis = set()
    for r in done.values():
        leis |= set(r.get("leis_found") or [])
    BASE.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=1) as pp:
        for a in todo:
            if only and a["name"] not in only:
                continue
            if done.get(a["name"], {}).get("status") == "scanned" and set(done[a["name"]].get("leis_applied") or []) >= leis:
                continue
            zpath = BASE / f"{a['name']}.zip"
            try:
                raw, resp = client.get(a["url"])
            except net.NotCollected as exc:
                rec = dict(a, status="not_collected", reason=str(exc))
            else:
                zpath.write_bytes(raw)
                del raw
                meta = dict(a, retrieved=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
                rec = pp.submit(_scan_job, a["name"], zpath, sorted(leis), meta).result()
                zpath.unlink()
                leis |= set(rec["leis_found"])
            with open(MANIFEST, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(a["name"], rec.get("status"), json.dumps(rec.get("stats") or {}), flush=True)
    m = manifest()
    late = [k for k, r in m.items() if r.get("status") == "scanned" and set(r.get("leis_applied") or []) < leis]
    print("LEI relevés :", sorted(leis), "; archives à rescanner :", late)


# -- positions et mesure ---------------------------------------------------------------------------

def _dec(x):
    try:
        v = Decimal(str(x).replace(",", "").strip())
        return v if v.is_finite() else None
    except (InvalidOperation, AttributeError, TypeError):
        return None


def positions(c=None, archives=None):
    """Positions gardées de toutes les archives scannées, jointes à leur dépôt, leur série et leurs
    identifiants ; une ligne par position déclarée."""
    c = c or cols()
    rows = []
    for name, r in sorted(manifest().items()):
        if r.get("status") != "scanned" or (archives and name not in archives):
            continue
        d = BASE / name / SUBDIR
        t = {k: pd.read_parquet(d / f"{k}.parquet") for k in ("holding", "identifiers", "debt", "submission", "registrant", "fund")}
        h, s, f, g, i, b = c["holding"], c["submission"], c["fund"], c["registrant"], c["identifiers"], c["debt"]
        x = t["holding"].rename(columns={v: k for k, v in h.items()})
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
        rows.append(x)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def latest_by_series(p):
    """Au dernier dépôt de chaque série pour une date de portefeuille : un amendement remplace le
    dépôt (le plus récent par date de dépôt, puis par accession)."""
    key = ["series_id", "report_date"]
    last = (p.sort_values(["filing_date", "accession"]).groupby(key, dropna=False)["accession"].last().reset_index())
    return p.merge(last, on=key + ["accession"], how="inner")


def price_to_par(p):
    """Une ligne par (titre, date de portefeuille) : somme des valeurs dans la monnaie du titre, somme
    des nominaux (unité PA), séries distinctes ; positions en titres de dette seulement."""
    p = p[(p["unit"] == "PA") & p["asset_cat"].isin(["DBT"])].copy()
    p["security"] = p["isin"].where(p["isin"].notna() & (p["isin"] != ""), "CUSIP:" + p["cusip"].fillna(""))
    p = p[p["security"] != "CUSIP:"]
    p = latest_by_series(p)
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
                    "ratio": num / den, "n_series": g["series_id"].nunique(), "n_positions": len(vals),
                    "currency": ";".join(cur), "issuer_names": ";".join(sorted(set(g["issuer_name"].dropna()))),
                    "title": next(iter(sorted(set(g["title"].dropna()))), None),
                    "maturity": next(iter(sorted(set(g["maturity"].dropna()))), None) if "maturity" in g else None,
                    "accessions": sorted(set(g["accession"]))})
    return pd.DataFrame(out)


BASIS = ("valorisation déclarée par des fonds (Form N-PORT Data Sets), perspective counterparty : somme des valeurs "
         "dans la monnaie du titre sur la somme des nominaux, au dernier dépôt de chaque série pour la date de "
         "portefeuille ; jamais une probabilité de défaut ni un fait comptable de SoftBank, hors des mesures de "
         "financement et de l'annexe F (D-0058, point 8)")


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
        out.append(cell("nport_price_to_par", subject, x.report_date, x.report_date, "as_known", as_of,
                        breakdown=x.security, value=x.ratio, numerator=x.value_local, denominator=x.principal,
                        knowledge_date=max(str(kd.get(a) or "") for a in x.accessions)[:10] or None,
                        flags={"perspective": "counterparty", "n_series": int(x.n_series),
                               "n_positions": int(x.n_positions), "principal": str(x.principal),
                               "currency": x.currency, "title": x.title, "maturity": x.maturity,
                               "issuer_names": x.issuer_names, "accessions": list(x.accessions), "basis": BASIS}))
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
    else:
        m = manifest()
        print(len(m), "archives au manifeste ;", sum(1 for r in m.values() if r.get("status") == "scanned"), "scannées")
