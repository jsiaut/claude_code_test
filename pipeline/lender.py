"""Bloc `lender` de §14 : le côté prêteur, par les BDC Data Sets (fichier `soi`).

La dette d'un véhicule détenu par un fonds de dette privée n'apparaît pas chez le sponsor ;
elle se voit chez le prêteur quand c'est une BDC. L'usage des archives se limite aux entités
des groupes et aux contreparties que nomment leurs pièces, et à trois signaux lus ensemble :
juste valeur ÷ coût, part des intérêts capitalisés, part des prêts sans accumulation
d'intérêts. `soi` exclut tags et axes personnalisés, si bien qu'une absence n'y prouve rien ;
le millésime de chaque archive se garde (rafraîchissements rétroactifs, annexe D).

    python -m pipeline.lender extract     # archives en cache -> db/bdc_soi.parquet
"""
import io
import json
import re
import sys
import zipfile

import pandas as pd

from . import cache, config

ARCH = ("other", "bdc", "archives")
KEEP = {
    "adsh": "adsh", "cik": "bdc_cik", "name": "bdc_name", "ddate": "ddate", "qtrs": "qtrs", "form": "form",
    "filed": "filed", "period": "period", "cstm": "cstm",
    "Investment, Identifier Axis": "identifier",
    "Investment, Issuer Name Axis": "issuer_axis",
    "Investment, Issuer Name [Extensible Enumeration]": "issuer_enum",
    "Investment, Name Axis": "name_axis",
    "Investment Type Axis": "inv_type",
    "Investment, Type [Extensible Enumeration]": "inv_type_enum",
    "Investment, Issuer Affiliation Axis": "affiliation",
    "Industry Sector Axis": "industry",
    "Lien Category Axis": "lien",
    "Investment Interest Rate": "rate",
    "Investment, Interest Rate, Paid in Kind": "rate_pik",
    "Investment, Interest Rate, Paid in Cash": "rate_cash",
    "Investment Owned, Balance, Principal Amount": "principal",
    "Investment Owned, Cost": "cost",
    "Investment Owned, Fair Value": "fair_value",
    "Investment, Non-income Producing [true false]": "non_income_producing",
    "Financial Instrument Performance Status Axis": "performance_axis",
    "InvestmentPerformanceStatus": "performance_custom",
    "Investment Maturity Date": "maturity",
    "Investment, Acquisition Date": "acquired",
}
NUMERIC = ("rate", "rate_pik", "rate_cash", "principal", "cost", "fair_value")


def archives():
    d = config.CACHE.joinpath(*ARCH)
    return sorted(d.glob("*_bdc.zip.zst"))


def extract():
    """Une ligne par position (coût ou juste valeur publié), colonnes utiles, avec le millésime
    (nom de l'archive, empreinte de son contenu)."""
    frames = []
    for p in archives():
        raw = cache.read(p)
        zf = zipfile.ZipFile(io.BytesIO(raw))
        info = zf.getinfo("soi.tsv")
        if info.file_size == 0:
            continue
        with zf.open("soi.tsv") as fh:
            df = pd.read_csv(fh, sep="\t", dtype=str, keep_default_na=False, quoting=3, on_bad_lines="warn")
        cols = [c for c in KEEP if c in df.columns]
        df = df[cols].rename(columns=KEEP)
        for c in KEEP.values():
            if c not in df.columns:
                df[c] = ""
        df = df[(df["cost"] != "") | (df["fair_value"] != "") | (df["principal"] != "")]
        df["archive"] = p.name[:-4]
        df["archive_sha256"] = cache.sha256(raw)
        frames.append(df)
        print(p.name, len(df), flush=True)
    out = pd.concat(frames, ignore_index=True)
    for c in NUMERIC:
        out[c] = pd.to_numeric(out[c].str.replace(",", ""), errors="coerce")
    out = out[list(KEEP.values()) + ["archive", "archive_sha256"]]
    out.to_parquet(config.DB_DIR / "bdc_soi.parquet", index=False)
    return out



# -- rattachement des positions aux entités (§10.2) ---------------------------------------

def legal_names(ent_rows):
    """Dénominations légales complètes (suffixe de forme juridique) des entités et alias
    confirmés : seule une égalité de dénomination légale rattache une position (D-0022) ;
    un nom court ou commercial (« Meta ») ne rattache jamais rien."""
    from .entities import LEGAL_SUFFIX
    out = {}
    for r in ent_rows:
        if r["record_kind"] not in ("entity", "alias") or r.get("status") == "pending":
            continue
        n = (r.get("normalized_name") or "").strip()
        if not n or not LEGAL_SUFFIX.search(n) or len(n.split()) < 2:
            continue
        out.setdefault(n, r["entity_id"])
    return out


def match_rows(soi, names):
    """Positions dont un champ d'identification contient, mot pour mot, une dénomination
    légale du registre ; la plus longue l'emporte (« x ai holdings corp » avant « x ai corp »)."""
    from .graph import normalize_name
    fields = ["identifier", "issuer_enum", "issuer_axis", "name_axis"]
    keys = sorted(names, key=len, reverse=True)
    cache_norm = {}

    def norm(s):
        if s not in cache_norm:
            cache_norm[s] = " " + normalize_name(s) + " " if s else ""
        return cache_norm[s]

    hits = []
    for i, r in enumerate(soi[fields].itertuples(index=False)):
        best = None
        for f, v in zip(fields, r):
            t = norm(v)
            if not t:
                continue
            for k in keys:
                if " " + k + " " in t:
                    if best is None or len(k) > len(best[1]):
                        best = (f, k)
                    break
        if best:
            hits.append((i, best[0], best[1], names[best[1]]))
    return hits


# -- faits de num : la source des positions rattachées --------------------------------------
# Les colonnes de soi suivent les libellés de la table tag, qui varient d'une version de la
# taxonomie à l'autre dans les archives (us-gaap/2026 : InvestmentOwnedAtCost libellé
# « Adjusted cost basis ») : coût et juste valeur d'un même fonds tombent sous deux colonnes.
# Les faits de num portent le nom du concept : on lit les positions rattachées là.

TAGS = {"InvestmentOwnedAtCost": "cost", "InvestmentOwnedAtFairValue": "fair_value",
        "InvestmentOwnedBalancePrincipalAmount": "principal", "InvestmentInterestRate": "rate",
        "InvestmentInterestRatePaidInKind": "rate_pik", "InvestmentInterestRatePaidInCash": "rate_cash",
        "InvestmentNonIncomeProducing": "non_income_producing",
        "InvestmentCompanyFinancialCommitmentToInvesteeFutureAmount": "unfunded_commitment"}
AXIS = "InvestmentIdentifierAxis"


SEG_RX = re.compile(r"([A-Za-z0-9_\-]+)\(([^()]*)\)=(.*?)\(([^()]*)\);(?=[A-Za-z0-9_\-]+\([^()]*\)=|$)", re.S)


def parse_segments(segments):
    """Segments de num : « Axe(version)=Membre(version); » répétés. Un libellé de membre peut
    contenir un point-virgule : on coupe seulement devant l'axe suivant."""
    return [(m.group(1), m.group(3).strip()) for m in SEG_RX.finditer(segments or "")]


ISSUER_SUFFIX = {"inc", "corp", "corporation", "llc", "lp", "ltd", "plc", "pbc", "limited", "llp", "gmbh",
                 "ag", "sa", "nv", "bv", "pte", "lllp", "l l c"}
INSTRUMENT_WORDS = {"investment", "investments", "first", "1st", "second", "2nd", "senior", "term", "loan", "loans",
                    "delayed", "revolver", "revolving", "notes", "note", "bond", "bonds", "common", "preferred", "class",
                    "warrant", "warrants", "units", "equity", "secured", "unsecured", "industry", "instrument",
                    "type", "interest", "maturity", "debt", "initial", "incremental", "ddtl", "security"}


def issuer_unambiguous(t, k):
    """La dénomination trouvée est l'émetteur si aucune autre dénomination légale (mot de forme
    juridique) ne la suit avant la description de l'instrument : « Oracle Corp Yucca Growth
    Infrastructure, LLC Investment Type ... » désigne Yucca, pas Oracle."""
    rest = t.split(" " + k + " ", 1)[1].split()
    for w in rest:
        if w in INSTRUMENT_WORDS:
            return True
        if w in ISSUER_SUFFIX:
            return False
    return True


def _keywords(names):
    """Premier mot distinctif de chaque dénomination : préfiltre de lignes, jamais une règle de
    rattachement (le rattachement exige la dénomination entière)."""
    kw = set()
    for n in names:
        toks = n.split()
        kw.add(" ".join(toks[:2]) if len(toks[0]) < 4 else toks[0])
    return sorted(kw)


def extract_num(names):
    """Faits de num des positions dont l'identifiant contient un mot de préfiltre ; une ligne
    par fait, avec l'archive, son empreinte, et le déposant (sub)."""
    from .graph import normalize_name
    kws = [k.encode() for k in _keywords(names)]
    tags = {t.encode() for t in TAGS}
    rows, subs, skipped = [], [], {}
    for p in archives():
        raw = cache.read(p)
        sha = cache.sha256(raw)
        zf = zipfile.ZipFile(io.BytesIO(raw))
        with zf.open("datasets/sub.tsv") as fh:
            sub = pd.read_csv(fh, sep="\t", dtype=str, keep_default_na=False, quoting=3)
        sub["archive"] = p.name[:-4]
        subs.append(sub)
        n_bad = 0
        with zf.open("datasets/num.tsv") as fh:
            head = fh.readline().decode().rstrip("\n").split("\t")
            for line in fh:
                if b"InvestmentIdentifierAxis" not in line:
                    continue
                tag = line.split(b"\t", 2)[1]
                if tag not in tags:
                    continue
                low = line.lower()
                if not any(k in low for k in kws):
                    continue
                f = line.decode("utf-8", "replace").rstrip("\n").split("\t")
                if len(f) != len(head):
                    n_bad += 1
                    continue
                d = dict(zip(head, f))
                segs = parse_segments(d["segments"])
                ident = next((m for a, m in segs if a == AXIS), "")
                other = ";".join(f"{a}={m}" for a, m in segs if a != AXIS)
                rows.append({"archive": p.name[:-4], "archive_sha256": sha, "adsh": d["adsh"], "tag": d["tag"],
                             "version": d["version"], "ddate": d["ddate"], "qtrs": d["qtrs"], "uom": d["uom"],
                             "segments": d["segments"], "identifier": ident, "identifier_norm": normalize_name(ident),
                             "other_axes": other, "value": d["value"]})
        skipped[p.name[:-4]] = n_bad
        print(p.name, len(rows), flush=True)
    df = pd.DataFrame(rows)
    sub = pd.concat(subs, ignore_index=True)
    df.to_parquet(config.DB_DIR / "bdc_num.parquet", index=False)
    sub.to_parquet(config.DB_DIR / "bdc_sub.parquet", index=False)
    (config.DB_DIR / "bdc_extract.json").write_text(__import__("json").dumps({"num_lines_malformed": skipped}))
    return df, sub


def registry(obs_rows=None):
    """Registre des entités tel que l'assemblage le construit : graines, extraits confirmés et
    contreparties nommées par les observations validées (D-0021, D-0022)."""
    from . import entities, links
    p0 = __import__("json").loads((config.DB_DIR / "phase0.json").read_text())
    cfg = config.load()
    if obs_rows is None:
        df = pd.read_parquet(config.ROOT / "tables" / "observations.parquet")
        obs_rows = df.astype(object).where(df.notna(), None).to_dict("records")
    return entities.build(p0, cfg, links.counterparty_names(obs_rows))


def _universe_names():
    rows, _ = registry()
    return legal_names(rows)



# -- positions rattachées et mesures (§14) ---------------------------------------------------

EQUITY_RX = re.compile(r"\b(common stock|common units?|common shares|preferred (stock|units?|equity|shares)|"
                       r"class [a-z0-9]+ (common|units?|shares|interests?)|warrants?|equity interests?|"
                       r"membership interests?|ordinary shares|lp interests?|partnership interests?)\b", re.I)
DEBT_RX = re.compile(r"\b(loans?|revolv\w*|delayed draw|ddtl|notes?|bonds?|debentures?|first lien|second lien|"
                     r"1st lien|2nd lien|secured|unsecured|debt|equipment financing|senior)\b", re.I)
TOTAL_RX = re.compile(r"\btotal\b", re.I)


def instrument_class(identifier):
    """Prêt ou titre de capital, d'après le libellé de la position : la juste valeur d'une action
    sur son coût n'est pas un signal de crédit ; une position non classée reste à part."""
    d, e = bool(DEBT_RX.search(identifier)), bool(EQUITY_RX.search(identifier))
    if e and not d:
        return "equity"
    if d and not e:
        return "debt"
    if d and e:
        return "debt" if re.search(r"\b(loan|notes?|bonds?|lien|ddtl|delayed draw)\b", identifier, re.I) else "unclassified"
    return "unclassified"


PERF_AXIS = "FinancialInstrumentPerformanceStatusAxis"
AMBIGUOUS = {}      # identifiants qui nomment une entité du registre et un autre émetteur
SUBTOTALS = []      # lignes « Total » des portefeuilles, écartées
NONPERF = re.compile(r"nonperform|non-perform|nonaccrual|non-accrual", re.I)


def matched_holdings(names, ent_rows):
    """Faits de num rattachés à une entité du registre par sa dénomination légale entière,
    vue as_known : seuls les faits à la date du bilan du dépôt (période de sub), le premier
    dépôt d'un même fonds pour une même date l'emportant. Renvoie (positions, faits)."""
    from .entities import Registry
    num = pd.read_parquet(config.DB_DIR / "bdc_num.parquet")
    sub = pd.read_parquet(config.DB_DIR / "bdc_sub.parquet")
    sub = sub.drop_duplicates("adsh")
    num = num.drop_duplicates(["adsh", "tag", "ddate", "qtrs", "identifier", "other_axes", "value"])
    keys = sorted(names, key=len, reverse=True)
    ent_of, ambiguous = {}, {}
    for ident in num["identifier_norm"].unique():
        t = " " + ident + " "
        hit = next((k for k in keys if " " + k + " " in t), None)
        if hit:
            if issuer_unambiguous(t, hit):
                ent_of[ident] = names[hit]
            else:
                ambiguous[ident] = names[hit]
    AMBIGUOUS.clear()
    AMBIGUOUS.update(ambiguous)
    SUBTOTALS.clear()
    num = num[num["identifier_norm"].isin(ent_of)].copy()
    num["entity_id"] = num["identifier_norm"].map(ent_of)
    num = num.merge(sub[["adsh", "cik", "name", "form", "period", "filed", "fy", "fp"]], on="adsh", how="left")
    num["period"] = num["period"].str[:8]
    num = num[num["ddate"] == num["period"]]
    # premier dépôt d'un fonds pour une date de bilan (un 10-K/A ne remplace pas la vue as_known)
    first = num.groupby(["cik", "ddate"])["filed"].transform("min")
    num = num[num["filed"] == first]
    reg = Registry(ent_rows)

    def d8(x):
        return f"{x[:4]}-{x[4:6]}-{x[6:8]}"
    num["date"] = num["ddate"].map(d8)
    num["group"] = [reg.group_at(e, d, "as_known") for e, d in zip(num["entity_id"], num["date"])]
    num["value_dec"] = num["value"]
    num["nonperforming"] = num["other_axes"].str.contains(PERF_AXIS) & num["other_axes"].map(
        lambda a: bool(NONPERF.search(a.split(PERF_AXIS, 1)[-1][:120])) if PERF_AXIS in a else False)
    num["has_perf"] = num["other_axes"].str.contains(PERF_AXIS)
    # une position : dépôt, identifiant, autres axes hors statut de performance
    num["holding"] = num["adsh"] + "|" + num["identifier"] + "|" + num["other_axes"].map(
        lambda a: ";".join(x for x in a.split(";") if x and not x.startswith(PERF_AXIS)))
    rows = []
    for h, g in num.groupby("holding", sort=True):
        r = g.iloc[0]
        vals = {}
        for t, col in TAGS.items():
            x = g[g["tag"] == t]
            if len(x):
                vals[col] = x["value"].iloc[0]
        if TOTAL_RX.search(r["identifier"]):
            SUBTOTALS.append(h)
            continue      # sous-total du portefeuille : il recompterait les positions qu'il somme
        rows.append({"holding": h, "adsh": r["adsh"], "bdc_cik": str(r["cik"]).zfill(10), "bdc_name": r["name"],
                     "instrument_class": instrument_class(r["identifier"]),
                     "form": r["form"], "filed": r["filed"], "date": r["date"], "entity_id": r["entity_id"],
                     "group": r["group"], "identifier": r["identifier"], "archive": r["archive"],
                     "archive_sha256": r["archive_sha256"],
                     "has_perf": bool(g["has_perf"].any()), "nonperforming": bool(g["nonperforming"].any()),
                     "fact_keys": {t: f"bdc/{r['adsh']}/{__import__('hashlib').sha1(h.encode()).hexdigest()[:12]}/{t}"
                                   for t in g["tag"].unique()},
                     **vals})
    return pd.DataFrame(rows), num


def _dec(x):
    from decimal import Decimal
    try:
        return Decimal(str(x)) if x not in (None, "") and x == x else None
    except Exception:
        return None


def _num_or_none(v):
    try:
        float(v)
        return v
    except (TypeError, ValueError):
        return None


def bdc_facts(num):
    """Lignes de la table facts pour les faits rattachés (source bdc_num) : nombre tiré de la
    structure du dépôt de la BDC, avec son accession et son emplacement dans l'archive."""
    import hashlib
    out = []
    for r in num.itertuples():
        hold = r.holding
        fk = f"bdc/{r.adsh}/{hashlib.sha1(hold.encode()).hexdigest()[:12]}/{r.tag}"
        dims = [["us-gaap:InvestmentIdentifierAxis", r.identifier]] + \
            [[x.split("=", 1)[0].split("(")[0], x.split("=", 1)[1]] for x in r.other_axes.split(";") if "=" in x]
        tier = "A" if str(r.form).startswith("10-K") else "B"
        out.append({"fact_key": fk, "source": "bdc_num", "cik": str(r.cik).zfill(10), "entity_id": f"cik:{str(r.cik).zfill(10)}",
                    "group_id": None, "accession": r.adsh, "form": r.form, "filing_date": f"{r.filed[:4]}-{r.filed[4:6]}-{r.filed[6:8]}",
                    "concept": "us-gaap:" + r.tag, "concept_ns": "us-gaap", "taxonomy_version": r.version,
                    "period_type": "instant" if str(r.qtrs) == "0" else "duration", "period_start": None,
                    "period_end": r.date, "unit": r.uom, "currency": "USD" if r.uom == "USD" else None,
                    "dims": json.dumps(dims, separators=(",", ":")), "n_dims": len(dims), "framework": "us_gaap",
                    "reporting_scope": "as_reported", "value": _num_or_none(r.value),
                    "value_text": None if _num_or_none(r.value) is not None else (r.value or None),
                    "decimals": None, "decimals_inf": None, "precision_known": False, "is_nil": False,
                    "is_fixed_zero": False, "fact_id": None, "locator": f"{r.archive}:datasets/num.tsv",
                    "is_tagged": True, "tier": tier, "filing_status": "filed",
                    "assurance_level": "audited" if tier == "A" else "reviewed",
                    "knowledge_date": f"{r.filed[:4]}-{r.filed[4:6]}-{r.filed[6:8]}", "fy": None, "fp": None})
    return out


def measures_cells(hold, as_of):
    """bdc_fv_to_cost, bdc_pik_share, bdc_non_accrual_share par (groupe de l'émetteur, BDC,
    date) et tous fonds confondus. Une absence de balise n'est jamais un zéro (§14)."""
    from decimal import Decimal
    from .measures import cell
    out = []
    if hold.empty:
        return out
    hold = hold[hold["group"].notna()]
    for scope_cols in (["group", "bdc_cik", "date", "instrument_class"], ["group", "date", "instrument_class"]):
        for key, g in hold.groupby(scope_cols, sort=True):
            subj, date, cls = key[0], key[-2], key[-1]
            cp = f"cik:{key[1]}" if len(key) == 4 else "none"
            bk = cls if len(key) == 4 else f"all_bdc|{cls}"
            kd = min(f"{x[:4]}-{x[4:6]}-{x[6:8]}" for x in g["filed"])
            fl_base = {"holdings": len(g), "instrument_class": cls, "entities": sorted(g["entity_id"].unique()),
                       "bdc": sorted(g["bdc_name"].unique())[:20], "archives": sorted(g["archive"].unique()),
                       "accessions": sorted(g["adsh"].unique())[:20]}
            # juste valeur ÷ coût
            both = g[g["cost"].notna() & g["fair_value"].notna()] if "cost" in g and "fair_value" in g else g.iloc[0:0]
            terms = []
            for r in both.itertuples():
                for t in ("InvestmentOwnedAtCost", "InvestmentOwnedAtFairValue"):
                    terms.append({"fact_key": r.fact_keys[t], "value": _dec(r.cost if t.endswith("Cost") else r.fair_value),
                                  "knowledge_date": f"{r.filed[:4]}-{r.filed[4:6]}-{r.filed[6:8]}",
                                  "tier": "A" if str(r.form).startswith("10-K") else "B"})
            if len(both):
                c = sum(_dec(x) for x in both["cost"])
                f = sum(_dec(x) for x in both["fair_value"])
                st = "computed" if len(both) == len(g) else "partial"
                out.append(cell("bdc_fv_to_cost", subj, None, date, "as_known", as_of, counterparty=cp, breakdown=bk,
                                value=(f / c) if c else None, numerator=f, denominator=c, unit="pure",
                                status=st if c else "not_determinable", nd_reason=None if c else "denominator_nonpositive",
                                terms=terms, knowledge_date=kd,
                                flags={**fl_base, "principal": str(sum((_dec(x) or Decimal(0)) for x in g.get("principal", []))),
                                       "unfunded_commitment": str(sum((_dec(x) or Decimal(0)) for x in g.get("unfunded_commitment", []) if x == x)),
                                       "holdings_without_cost_or_fv": int(len(g) - len(both))}))
            else:
                out.append(cell("bdc_fv_to_cost", subj, None, date, "as_known", as_of, counterparty=cp, breakdown=bk,
                                status="not_determinable", nd_reason="not_tagged", knowledge_date=kd,
                                flags={**fl_base, "note": "coût ou juste valeur non balisés en us-gaap pour ces positions"}))
            # part des intérêts capitalisés : taux PIK ÷ taux total, pondérés par le principal
            if "rate_pik" in g:
                pk = g[g["rate_pik"].notna() & g["rate"].notna() & g["principal"].notna()]
            else:
                pk = g.iloc[0:0]
            if len(pk):
                num_ = sum(_dec(r.principal) * _dec(r.rate_pik) for r in pk.itertuples())
                den_ = sum(_dec(r.principal) * _dec(r.rate) for r in pk.itertuples())
                out.append(cell("bdc_pik_share", subj, None, date, "as_known", as_of, counterparty=cp, breakdown=bk,
                                value=(num_ / den_) if den_ else None, numerator=num_, denominator=den_, unit="pure",
                                status=("computed" if len(pk) == len(g) else "partial") if den_ else "not_determinable",
                                nd_reason=None if den_ else "denominator_nonpositive", knowledge_date=kd,
                                flags={**fl_base, "holdings_with_pik_rate": int(len(pk))}))
            else:
                out.append(cell("bdc_pik_share", subj, None, date, "as_known", as_of, counterparty=cp, breakdown=bk,
                                status="not_determinable", nd_reason="not_tagged", knowledge_date=kd,
                                flags={**fl_base, "note": "taux PIK non balisé : une absence ne prouve pas un taux nul"}))
            # part des prêts sans accumulation d'intérêts : statut de performance balisé
            pf = g[g["has_perf"]]
            if len(pf) and "cost" in g:
                pf = pf[pf["cost"].notna()]
            if len(pf):
                den_ = sum(_dec(x) for x in pf["cost"])
                num_ = sum(_dec(x) for x, n in zip(pf["cost"], pf["nonperforming"]) if n)
                out.append(cell("bdc_non_accrual_share", subj, None, date, "as_known", as_of, counterparty=cp,
                                breakdown=bk, value=(num_ / den_) if den_ else None, numerator=num_, denominator=den_,
                                unit="pure", status=("computed" if len(pf) == len(g) else "partial") if den_ else "not_determinable",
                                nd_reason=None if den_ else "denominator_nonpositive", knowledge_date=kd, flags=fl_base))
            else:
                out.append(cell("bdc_non_accrual_share", subj, None, date, "as_known", as_of, counterparty=cp,
                                breakdown=bk, status="not_determinable", nd_reason="not_tagged", knowledge_date=kd,
                                flags={**fl_base, "note": "statut de performance non balisé : une absence ne prouve pas une accumulation d'intérêts"}))
    return out



def exclusions(as_of):
    """Ce que le bloc lender écarte, avec son motif : positions non publiques, identifiants qui
    nomment deux émetteurs, lignes de num illisibles."""
    import hashlib
    out = []

    def ex(kind, key, reason, detail):
        out.append({"exclusion_key": f"{reason}:{key}", "item_kind": kind, "item_key": key, "reason": reason,
                    "detail": detail, "group_id": None, "accession": None, "content_key": None, "as_of": as_of})
    ex("aggregate", "lender:private_credit_funds", "not_public",
       "positions des fonds de dette privée qui ne sont pas des BDC, et des banques : aucune publication de "
       "portefeuille ; seules les BDC publient le leur (§14)")
    for ident, eid in sorted(AMBIGUOUS.items()):
        ex("fact", "lender:" + hashlib.sha1(ident.encode()).hexdigest()[:16], "pending_entity",
           f"position de BDC « {ident[:240]} » : nomme {eid} et un autre émetteur ; non rattachée (§10.2)")
    for h in sorted(SUBTOTALS):
        ex("fact", "lender:subtotal:" + hashlib.sha1(h.encode()).hexdigest()[:16], "invalid_aggregate",
           f"ligne « Total » d'un portefeuille de BDC ({h.split('|')[0]}) : sous-total des positions déjà comptées")
    info = __import__("json").loads((config.DB_DIR / "bdc_extract.json").read_text())
    for arch, n in sorted(info.get("num_lines_malformed", {}).items()):
        if n:
            ex("document", f"lender:{arch}:num.tsv", "parse_failed",
               f"{n} ligne(s) de num au nombre de champs inattendu, écartées")
    return out


if __name__ == "__main__":
    if sys.argv[1] == "extract":
        df = extract()
        print(len(df), df["bdc_cik"].nunique(), "BDC")
    elif sys.argv[1] == "num":
        names = _universe_names()
        df, sub = extract_num(names)
        print(len(df), df["adsh"].nunique(), "dépôts")
