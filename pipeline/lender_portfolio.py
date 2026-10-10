"""Bloc `lender_portfolio` (D-0045) : le portefeuille entier de chaque BDC des archives en cache.

Cinq mesures par véhicule (un déclarant BDC) et date de bilan, vue as_known : juste valeur ÷ coût
des prêts, part des intérêts capitalisés et part des prêts sans accumulation d'intérêts (bornes
basses), engagements non tirés ÷ portefeuille (borne basse), part logiciel. Puis les événements
F11 à F13 de l'annexe F, une cellule par véhicule, événement et date de bilan, jamais de somme
entre véhicules. Les règles sont celles de D-0045, fixées avant tout calcul.

    python -m pipeline.lender_portfolio extract   # archives en cache -> db/bdc_portfolio.parquet
"""
import datetime as dt
import io
import json
import sys
import zipfile
from decimal import Decimal

import pandas as pd

from . import cache, config, lender

OUT = config.DB_DIR / "bdc_portfolio.parquet"
INFO = config.DB_DIR / "bdc_portfolio.json"
PERF_AXIS = lender.PERF_AXIS
NONPERF = lender.NONPERF
EVENTS = {"F11": ("bdc_portfolio_fv_to_cost", "down"), "F12": ("bdc_portfolio_pik_share", "up"),
          "F13": ("bdc_portfolio_non_accrual_share", "up")}
MEASURE_IDS = ("bdc_portfolio_fv_to_cost", "bdc_portfolio_pik_share", "bdc_portfolio_non_accrual_share",
               "bdc_portfolio_unfunded_ratio", "bdc_portfolio_software_share")


def _f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def holdings_of(lines, period, head):
    """Positions d'un dépôt à partir de ses lignes de num : une position par identifiant et autres
    axes, hors statut de performance et secteur ; le premier fait d'un concept l'emporte."""
    hold = {}
    for f in lines:
        d = dict(zip(head, f))
        if d["ddate"] != period:
            continue
        segs = lender.parse_segments(d["segments"])
        ident = next((m for a, m in segs if a == lender.AXIS), "")
        perf = [m for a, m in segs if a == PERF_AXIS]
        ind = [m for a, m in segs if "industry" in a.lower()]
        other = ";".join(f"{a}={m}" for a, m in segs
                         if a != lender.AXIS and a != PERF_AXIS and "industry" not in a.lower())
        k = ident + "|" + other
        h = hold.setdefault(k, {"identifier": ident, "other_axes": other, "has_perf": False, "nonperforming": False,
                                "industry": None, "principal_usd": None})
        if perf:
            h["has_perf"] = True
            h["nonperforming"] = h["nonperforming"] or any(NONPERF.search(m) for m in perf)
        if ind and not h["industry"]:
            h["industry"] = ind[0]
        col = lender.TAGS[d["tag"]]
        if col in h:
            continue
        h[col] = _f(d["value"])
        if col == "principal":
            h["principal_usd"] = d["uom"] == "USD"
    return hold


def extract():
    """Relit num.tsv de chaque archive sans préfiltre de noms (D-0045, point 4)."""
    tags = {t.encode() for t in lender.TAGS}
    frames, info = [], {"lines_malformed": {}, "subtotals": {}, "archives": []}
    for p in lender.archives():
        raw = cache.read(p)
        sha = cache.sha256(raw)
        zf = zipfile.ZipFile(io.BytesIO(raw))
        with zf.open("datasets/sub.tsv") as fh:
            sub = pd.read_csv(fh, sep="\t", dtype=str, keep_default_na=False, quoting=3)
        sub = sub.drop_duplicates("adsh").set_index("adsh")
        by_adsh, bad = {}, 0
        with zf.open("datasets/num.tsv") as fh:
            head = fh.readline().decode().rstrip("\n").split("\t")
            for line in fh:
                if b"InvestmentIdentifierAxis" not in line:
                    continue
                if line.split(b"\t", 2)[1] not in tags:
                    continue
                f = line.decode("utf-8", "replace").rstrip("\n").split("\t")
                if len(f) != len(head):
                    bad += 1
                    continue
                by_adsh.setdefault(f[0], []).append(f)
        rows, subtot = [], 0
        for adsh, lines in by_adsh.items():
            if adsh not in sub.index:
                continue
            s = sub.loc[adsh]
            period = str(s["period"])[:8]
            for k, h in holdings_of(lines, period, head).items():
                if lender.TOTAL_RX.search(h["identifier"]):
                    subtot += 1
                    continue
                rows.append({"archive": p.name[:-4], "archive_sha256": sha, "adsh": adsh,
                             "cik": str(s["cik"]).zfill(10), "name": s["name"], "former": s.get("former", ""),
                             "form": s["form"], "period": period, "filed": str(s["filed"]),
                             "instrument_class": lender.instrument_class(h["identifier"]), **h})
        info["lines_malformed"][p.name[:-4]] = bad
        info["subtotals"][p.name[:-4]] = subtot
        info["archives"].append({"archive": p.name[:-4], "sha256": sha, "positions": len(rows)})
        frames.append(pd.DataFrame(rows))
        print(p.name, len(rows), "positions", flush=True)
    df = pd.concat(frames, ignore_index=True)
    # une même accession dans deux archives : la première archive l'emporte
    df = df.drop_duplicates(["adsh", "identifier", "other_axes"], keep="first")
    df.to_parquet(OUT, index=False)
    INFO.write_text(json.dumps(info))
    return df


# -- mesures et événements ------------------------------------------------------------------

def _d(x):
    return f"{x[:4]}-{x[4:6]}-{x[6:8]}"


def as_known(df):
    """Premier dépôt d'un véhicule pour une date de bilan (vue as_known)."""
    first = df.groupby(["cik", "period"])["filed"].transform("min")
    df = df[df["filed"] == first]
    keep = df.groupby(["cik", "period"])["adsh"].transform("min")
    return df[df["adsh"] == keep]


def _dec(v):
    return Decimal(str(v)) if v is not None and v == v else None



SCALE = 500     # coût ou juste valeur à 500 fois le principal au moins, ou coût à 1/500 au plus : erreur d'échelle


def loans_of(g):
    """Prêts d'un portefeuille (D-0045, point 8) : position que son libellé ne classe pas en capital, que
    son libellé classe en dette ou qui porte un principal, et qui est financée (coût, juste valeur ou
    principal) ; une ligne qui ne porte qu'un engagement non tiré n'est pas un prêt du portefeuille.
    Renvoie les prêts et le masque des erreurs d'échelle (principal en dollars comme référence)."""
    funded = g["cost"].notna() | g["fair_value"].notna() | g["principal"].notna()
    loans = g[(g["instrument_class"] != "equity") & ((g["instrument_class"] == "debt") | g["principal"].notna()) & funded]

    def scale(r):
        p = r["principal"]
        if p is None or p != p or p <= 0 or r["principal_usd"] != True:  # noqa: E712 (booléen numpy ou NaN)
            return False
        c, f = r["cost"], r["fair_value"]
        hi = any(v is not None and v == v and v > 0 and v / p >= SCALE for v in (c, f))
        lo = c is not None and c == c and c > 0 and c / p <= 1 / SCALE
        return bool(hi or lo)
    bad = loans.apply(scale, axis=1) if len(loans) else pd.Series(dtype=bool)
    return loans, bad.astype(bool)

def vehicle_cells(g, cik, date, as_of, cfg):
    """Les cinq mesures d'un véhicule à une date de bilan (D-0045, point 5)."""
    from .measures import cell
    subj = f"cik:{cik}"
    r0 = g.iloc[0]
    kd = _d(r0["filed"])
    base = {"accession": r0["adsh"], "archive": r0["archive"], "archive_sha256": r0["archive_sha256"],
            "form": r0["form"], "vehicle": r0["name"], "positions": int(len(g))}
    out = []
    cov_min = Decimal(str(cfg.get("software_coverage_min", 0.9)))
    loans, bad = loans_of(g)

    def put(measure, **kw):
        out.append(cell(measure, subj, None, date, "as_known", as_of, unit="pure", knowledge_date=kd, **kw))
    base["scale_errors_excluded"] = int(bad.sum())
    debt = loans[~bad.reindex(loans.index, fill_value=False)]
    # juste valeur ÷ coût des prêts, si au moins 90 % de leur juste valeur porte un coût (D-0045, point 8)
    fvl = debt[debt["fair_value"].notna()]
    both = fvl[fvl["cost"].notna()]
    tot_fv = sum((_dec(x) for x in fvl["fair_value"]), Decimal(0))
    cov = (sum((_dec(x) for x in both["fair_value"]), Decimal(0)) / tot_fv) if tot_fv > 0 else Decimal(0)
    fl = {**base, "loans": int(len(debt)), "loans_with_cost_and_fv": int(len(both)), "coverage_fv": str(round(cov, 4))}
    if len(both) and cov >= cov_min:
        c, f = sum(_dec(x) for x in both["cost"]), sum(_dec(x) for x in both["fair_value"])
        st = ("computed" if len(both) == len(fvl) else "partial") if c > 0 else "not_determinable"
        put("bdc_portfolio_fv_to_cost", value=(f / c) if c > 0 else None, numerator=f, denominator=c, status=st,
            nd_reason=None if c > 0 else "denominator_nonpositive", flags=fl)
    else:
        put("bdc_portfolio_fv_to_cost", status="not_determinable", nd_reason="not_tagged",
            flags={**fl, "note": "coût balisé sur moins de 90 % de la juste valeur des prêts"})
    # intérêts capitalisés : borne basse, un prêt sans taux PIK balisé compte sans PIK ; taux total balisé
    # sur au moins 90 % du principal en dollars (D-0045, point 8)
    pl = debt[debt["principal"].notna() & (debt["principal_usd"] == True)]  # noqa: E712
    rated = pl[pl["rate"].notna()]
    tot_p = sum((_dec(x) for x in pl["principal"]), Decimal(0))
    pcov = (sum((_dec(x) for x in rated["principal"]), Decimal(0)) / tot_p) if tot_p > 0 else Decimal(0)
    pfl = {**base, "loans_rated": int(len(rated)), "loans_with_pik_rate": int(rated["rate_pik"].notna().sum()),
           "loans_non_usd_principal": int((debt["principal_usd"] == False).sum()),  # noqa: E712
           "coverage_principal": str(round(pcov, 4))}
    den = sum((_dec(p) * _dec(r) for p, r in zip(rated["principal"], rated["rate"])), Decimal(0))
    if len(rated) and pcov >= cov_min and den > 0:
        num = sum((_dec(p) * _dec(r) for p, r in zip(rated["principal"], rated["rate_pik"]) if r == r and r is not None),
                  Decimal(0))
        put("bdc_portfolio_pik_share", lower=num / den, upper=Decimal(1), numerator=num, denominator=den,
            status="bounded", bound_basis="untagged_counted_as_absent", flags=pfl)
    else:
        put("bdc_portfolio_pik_share", status="not_determinable",
            nd_reason="denominator_nonpositive" if len(rated) and pcov >= cov_min else "not_tagged",
            flags={**pfl, "note": "taux total balisé sur moins de 90 % du principal en dollars des prêts"})
    # prêts sans accumulation d'intérêts : borne basse, si le dépôt balise un statut de performance
    dc = debt[debt["cost"].notna()]
    if not bool(debt["has_perf"].any()):
        put("bdc_portfolio_non_accrual_share", status="not_determinable", nd_reason="not_tagged",
            flags={**base, "note": "aucun statut de performance balisé : une absence ne prouve pas une accumulation"})
    else:
        den = sum(_dec(x) for x in dc["cost"]) if len(dc) else Decimal(0)
        num = sum(_dec(x) for x, n in zip(dc["cost"], dc["nonperforming"]) if n) if len(dc) else Decimal(0)
        num = num or Decimal(0)
        if den > 0:
            put("bdc_portfolio_non_accrual_share", lower=num / den, upper=Decimal(1), numerator=num, denominator=den,
                status="bounded", bound_basis="untagged_counted_as_absent",
                flags={**base, "loans_with_cost": int(len(dc)), "loans_nonperforming": int(dc["nonperforming"].sum()),
                       "loans_with_status": int(dc["has_perf"].sum())})
        else:
            put("bdc_portfolio_non_accrual_share", status="not_determinable", nd_reason="denominator_nonpositive",
                flags=base)
    # engagements non tirés ÷ portefeuille : borne basse
    fv_all = g[g["fair_value"].notna()]
    unf = g[g["unfunded_commitment"].notna()] if "unfunded_commitment" in g else g.iloc[0:0]
    den = sum(_dec(x) for x in fv_all["fair_value"]) if len(fv_all) else Decimal(0)
    if len(unf) and den > 0:
        big = unf["unfunded_commitment"].map(lambda x: _dec(x) > den)
        num = sum((_dec(x) for x in unf.loc[~big, "unfunded_commitment"]), Decimal(0))
        put("bdc_portfolio_unfunded_ratio", lower=num / den, numerator=num, denominator=den, status="bounded",
            bound_basis="untagged_counted_as_absent",
            flags={**base, "commitments_tagged": int(len(unf)), "commitments_over_portfolio_excluded": int(big.sum())})
    else:
        put("bdc_portfolio_unfunded_ratio", status="not_determinable",
            nd_reason="not_tagged" if not len(unf) else "denominator_nonpositive", flags=base)
    # part logiciel, si au moins 90 % de la juste valeur porte un secteur
    sec = fv_all[fv_all["industry"].notna()]
    if len(sec) and den > 0:
        cov = sum(_dec(x) for x in sec["fair_value"]) / den
        sden = sum(_dec(x) for x in sec["fair_value"])
        snum = sum(_dec(x) for x, i in zip(sec["fair_value"], sec["industry"]) if "software" in str(i).lower())
        snum = snum or Decimal(0)
        st = "computed" if cov >= Decimal(str(cfg.get("software_coverage_min", 0.9))) else "partial"
        put("bdc_portfolio_software_share", value=(snum / sden) if sden > 0 else None, numerator=snum,
            denominator=sden, status=st if sden > 0 else "not_determinable",
            nd_reason=None if sden > 0 else "denominator_nonpositive",
            flags={**base, "industry_coverage_fv": str(round(cov, 4))})
    else:
        put("bdc_portfolio_software_share", status="not_determinable", nd_reason="not_tagged",
            flags={**base, "note": "aucun secteur balisé dans num pour ce dépôt"})
    return out


def _point(c):
    """Valeur comparée par un événement : la valeur, ou la borne basse d'une cellule bornée."""
    if c is None or c["status"] in ("not_determinable",):
        return None
    v = c["value"] if c["status"] != "bounded" else c["value_lower"]
    return None if v is None else Decimal(str(v))


def events_cells(cells_by_vehicle, as_of, gap_days, events=None, decision="D-0045"):
    """F11 à F13 (et F14, D-0047) : trois dates de bilan successives du même véhicule, 120 jours au
    plus entre deux."""
    from .measures import cell
    out = []
    for subj, by_date in cells_by_vehicle.items():
        dates = sorted(by_date)
        for i, date in enumerate(dates):
            ps = dates[i - 1] if i else None
            for fid, (measure, way) in (events or EVENTS).items():
                trio = dates[i - 2:i + 1] if i >= 2 else None
                if trio is None:
                    out.append(cell("fragility_event", subj, ps, date, "as_known", as_of, breakdown=fid,
                                    status="not_determinable", nd_reason="prior_period_missing",
                                    flags={"subjects": "bdc_vehicles", "decision": decision}))
                    continue
                ds = [dt.date.fromisoformat(x) for x in trio]
                if any((b - a).days > gap_days for a, b in zip(ds, ds[1:])):
                    out.append(cell("fragility_event", subj, ps, date, "as_known", as_of, breakdown=fid,
                                    status="not_determinable", nd_reason="prior_period_missing",
                                    flags={"subjects": "bdc_vehicles", "decision": decision, "dates": trio,
                                           "note": f"écart de plus de {gap_days} jours entre deux dates de bilan"}))
                    continue
                vals = [_point(by_date[x].get(measure)) for x in trio]
                c = by_date[date].get(measure)
                if any(v is None for v in vals):
                    out.append(cell("fragility_event", subj, ps, date, "as_known", as_of, breakdown=fid,
                                    status="not_determinable", nd_reason="not_tagged",
                                    flags={"subjects": "bdc_vehicles", "decision": decision, "dates": trio}))
                    continue
                a, b, cur = vals
                hit = (cur < b < a) if way == "down" else (cur > b > a)
                out.append(cell("fragility_event", subj, ps, date, "as_known", as_of, breakdown=fid, status="computed",
                                value_text="event" if hit else "no_event", knowledge_date=c["knowledge_date"],
                                flags={"subjects": "bdc_vehicles", "decision": decision, "dates": trio,
                                       "values": [str(v) for v in vals], "measure": measure}))
    return out


def platform_ciks(df, cfg):
    """Véhicules d'une plateforme par la marque du gestionnaire dans la dénomination EDGAR,
    actuelle ou ancienne (D-0045, point 3) : un regroupement de présentation, sans somme."""
    out = {}
    for plat, spec in (cfg.get("platforms") or {}).items():
        terms = [t.lower() for t in spec.get("name_terms") or []]
        names = df[["cik", "name", "former"]].drop_duplicates()
        hit = names[[any(t in f"{n} {fo}".lower() for t in terms) for n, fo in zip(names["name"], names["former"])]]
        out[plat] = sorted(hit["cik"].unique())
    return out


def cells(as_of):
    """Toutes les cellules du bloc : mesures par véhicule et date, puis événements."""
    cfg = config.load().get("lender_portfolio") or {}
    df = as_known(pd.read_parquet(OUT))
    out, by_vehicle = [], {}
    for (cik, period), g in df.groupby(["cik", "period"], sort=True):
        date = _d(period)
        cs = vehicle_cells(g, cik, date, as_of, cfg)
        out += cs
        by_vehicle.setdefault(f"cik:{cik}", {})[date] = {c["measure"]: c for c in cs}
    out += events_cells(by_vehicle, as_of, int(cfg.get("consecutive_gap_days_max", 120)))
    return out


def exclusions(as_of):
    """Ce que le bloc écarte, par archive : lignes « Total » et lignes de num illisibles."""
    info = json.loads(INFO.read_text())
    out = []
    for arch, n in sorted(info.get("subtotals", {}).items()):
        if n:
            out.append({"exclusion_key": f"invalid_aggregate:lender_portfolio:{arch}", "item_kind": "aggregate",
                        "item_key": f"lender_portfolio:{arch}", "reason": "invalid_aggregate",
                        "detail": f"{n} ligne(s) « Total » de portefeuilles de BDC, sous-totaux des positions déjà comptées (D-0045)",
                        "group_id": None, "accession": None, "content_key": None, "as_of": as_of})
    for arch, n in sorted(info.get("lines_malformed", {}).items()):
        if n:
            out.append({"exclusion_key": f"parse_failed:lender_portfolio:{arch}", "item_kind": "document",
                        "item_key": f"lender_portfolio:{arch}:num.tsv", "reason": "parse_failed",
                        "detail": f"{n} ligne(s) de num au nombre de champs inattendu, écartées (D-0045)",
                        "group_id": None, "accession": None, "content_key": None, "as_of": as_of})
    return out


if __name__ == "__main__":
    if sys.argv[1:] and sys.argv[1] == "extract":
        d = extract()
        print(len(d), "positions ;", d["cik"].nunique(), "BDC ;", d["adsh"].nunique(), "dépôts")
    else:
        print(__doc__)
