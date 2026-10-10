"""Construction du modèle : base, correspondance de concepts, séries par vue (§7, §8.3).

Le réseau est incrémental, le calcul est intégral (§9.6) : tout se recalcule à chaque
exécution depuis le cache et les fichiers d'observations.
"""
import datetime as dt
import json
from decimal import Decimal

import duckdb
import pandas as pd

from . import config, load, quantities

AUX = ("pres", "calc", "tags", "labels", "text_blocks")


def build_base(as_of):
    cfg = config.load()
    con = load.connect(fresh=True)
    n = load.load_facts(con)
    for name in AUX:
        p = config.DB_DIR / f"{name}.parquet"
        if p.exists():
            con.execute(f"CREATE TABLE {name} AS SELECT * FROM '{p}'")
    # la classification des rôles se recalcule à chaque exécution (§9.6)
    from . import xbrl
    defs = [r[0] for r in con.execute("SELECT DISTINCT role_definition FROM pres").fetchall()]
    con.execute("CREATE TEMP TABLE role_kind (role_definition VARCHAR, statement_kind VARCHAR)")
    con.executemany("INSERT INTO role_kind VALUES (?, ?)", [(d, xbrl.statement_kind(d)) for d in defs])
    con.execute("""UPDATE pres SET statement_kind = rk.statement_kind FROM role_kind rk
                   WHERE pres.role_definition IS NOT DISTINCT FROM rk.role_definition""")
    nconf = load.mark_conflicts(con, cfg["thresholds"]["scale_jump_factor"])
    nmap = quantities.map_concepts(con, cfg)
    # D1 : les lignes du 424B4 de SpaceX prennent la correspondance du 10-Q (§10.3)
    con.execute("""INSERT INTO concept_map
        SELECT DISTINCT m.group_id, m.quantity, f.accession, f.concept, 'D1_label_match', m.statement_kind
        FROM facts f JOIN concept_map m ON m.concept = f.concept AND m.group_id = f.group_id
        WHERE f.source = 'html_parse' AND m.accession = '0001628280-26-052535'""")
    # un concept peut servir deux grandeurs (créances nettes, résultats non distribués) : la
    # colonne en garde une, de façon déterministe ; concept_map garde la correspondance entière
    con.execute("""UPDATE facts SET model_quantity = m.quantity
                   FROM (SELECT accession, concept, group_id, min(quantity) AS quantity FROM concept_map
                         GROUP BY 1, 2, 3) m
                   WHERE facts.accession = m.accession AND facts.concept = m.concept
                     AND facts.group_id = m.group_id AND facts.n_dims = 0""")
    quantities.occurrences(con)
    return con, {"facts": n, "conflicts": nconf, "concept_map_rows": nmap}


def calendars():
    p0 = json.loads((config.DB_DIR / "phase0.json").read_text())
    out = {}
    for g, cal in p0["calendars"].items():
        qs = []
        prev = None
        for y in cal["years"]:
            start = dt.date.fromisoformat(y["fy_start"]) if y.get("fy_start") else None
            fe = dt.date.fromisoformat(y["fy_end"]) if y.get("fy_end") else None
            ends = [(dt.date.fromisoformat(q), y["source"]) for q in y["q_ends"]]
            ends = _fill_quarter_gaps(ends, start, prev)
            for i, (qe, src) in enumerate(ends):
                qs.append({"start": start, "end": qe, "fy_end": fe, "q": i + 1, "source": src,
                           "in_progress": bool(y.get("in_progress"))})
                start = qe + dt.timedelta(days=1)
            prev = y
        out[g] = {"quarters": qs, "window": cal["window"]}
    return out


def _fill_quarter_gaps(ends, fy_start, prev):
    """Un exercice en cours ne liste que les trimestres déposés : un premier rapport qui
    couvre six mois (SpaceX, introduite en juin 2026) ferait sinon d'un semestre un
    trimestre. Les fins de trimestre manquantes avant la dernière déposée se déduisent de
    l'exercice précédent, même décalage depuis le début d'exercice (source synthetic)."""
    if not ends or fy_start is None or not prev or len(prev.get("q_ends", [])) < 4 or not prev.get("fy_start"):
        return ends
    p_start = dt.date.fromisoformat(prev["fy_start"])
    have = [e for e, _ in ends]
    out = list(ends)
    for q in prev["q_ends"][:3]:
        cand = fy_start + (dt.date.fromisoformat(q) - p_start)
        if cand < have[-1] and not any(abs((cand - e).days) <= 10 for e in have):
            out.append((cand, "synthetic"))
    return sorted(out)


def original_report_dates(con):
    """Date de publicité du rapport qui porte chaque période comme période courante :
    sert de date de coupure de la vue as_known (§7.3)."""
    # rapports du déclarant légal antérieurs à une fusion inversée : autre entité (D-0043)
    from .phase0 import pre_combination_accessions
    fil = pd.read_parquet(config.DB_DIR / "filings.parquet")
    pre = sorted(pre_combination_accessions(fil.to_dict("records"), config.load())) or ["none"]
    rows = con.execute(f"""SELECT group_id, reportDate, min(filingDate) AS d
                           FROM '{config.DB_DIR / 'filings.parquet'}'
                           WHERE form IN ('10-K','10-Q','10-KT','10-QT') AND reportDate IS NOT NULL
                             AND accessionNumber NOT IN (SELECT unnest(?::VARCHAR[]))
                           GROUP BY 1, 2""", [pre]).fetchall()
    return {(g, r if isinstance(r, dt.date) else dt.date.fromisoformat(str(r))): d for g, r, d in rows}


def occurrences_df(con):
    df = con.execute("SELECT * FROM q_occ WHERE NOT coalesce(conflict, false)").fetchdf()
    for c in ("period_start", "period_end", "knowledge_date"):
        df[c] = pd.to_datetime(df[c]).dt.date
    prec = df["decimals"].fillna(-99).astype(int).where(~df["decimals_inf"].fillna(False).astype(bool), 99)
    df["order_key"] = list(zip(df["acceptance_datetime"].astype(str), df["accession"],
                               (df["source"] == "instance").astype(int), prec,
                               df["occ_rank"].fillna(0).astype(int)))
    return df


def pick(occ, cutoff):
    """Dernière occurrence connue à la date de coupure, par l'ordre total (§7.3)."""
    sub = occ[occ["knowledge_date"] <= cutoff]
    if sub.empty:
        return None
    return sub.loc[sub["order_key"].idxmax()]


def _match(occ, start, end, instant, tol=3):
    def close(a, b):
        # un instant n'a pas de début : NaT ne se compare à rien
        if a is None or b is None or a != a or b != b:
            return False
        return abs((a - b).days) <= tol
    if instant:
        m = occ[occ["period_end"].map(lambda x: close(x, end)) & (occ["period_type"] == "instant")]
    else:
        m = occ[occ["period_end"].map(lambda x: close(x, end)) &
                occ["period_start"].map(lambda x: close(x, start)) & (occ["period_type"] == "duration")]
    return m


def term_value(occ_q, start, end, instant, cutoff):
    """Une valeur de grandeur pour une période exacte, connue à la date de coupure."""
    m = _match(occ_q, start, end, instant)
    if m.empty:
        return None
    r = pick(m, cutoff)
    if r is None:
        return None
    revised_before = m[(m["knowledge_date"] <= cutoff)]["value"].nunique() > 1
    return {"value": Decimal(str(r["value"])), "fact_key": r["fact_key"], "accession": r["accession"],
            "concept": r["concept"],
            "knowledge_date": r["knowledge_date"], "tier": r["tier"], "decimals": r["decimals"],
            "decimals_inf": r["decimals_inf"], "precision_known": r["precision_known"],
            "is_tagged": bool(r["is_tagged"]), "revised": revised_before}


def quarter_series(occ, group, quantity, cal, instant, view, as_of, report_dates):
    """Série trimestrielle d'une grandeur pour un groupe et une vue.

    Flux : valeur directe du trimestre, sinon différence de cumuls (T4 = exercice − 9 mois) ;
    des termes de révisions différentes rendent le trimestre not_determinable (recast_boundary)."""
    occ_q = occ[(occ["group_id"] == group) & (occ["quantity"] == quantity)]
    out = []
    qs = cal["quarters"]
    by_fy = {}
    for q in qs:
        by_fy.setdefault(q["fy_end"], []).append(q)
    for fy_end, fqs in by_fy.items():
        fy_start = fqs[0]["start"]
        for i, q in enumerate(fqs):
            if view == "revised":
                cutoff = as_of
            else:
                cutoff = report_dates.get((group, q["end"])) or as_of
            rec = {"group_id": group, "quantity": quantity, "view": view, "start": q["start"],
                   "end": q["end"], "fy_end": fy_end, "q": q["q"], "cutoff": cutoff}
            if occ_q.empty:
                rec.update(status="not_determinable", nd_reason="concept_unresolved", value=None, terms=[])
                out.append(rec)
                continue
            if instant:
                t = term_value(occ_q, None, q["end"], True, cutoff)
                rec.update(_from_terms([t], t["value"] if t else None, "direct"))
                out.append(rec)
                continue
            t = term_value(occ_q, q["start"], q["end"], False, cutoff) if q["start"] else None
            if t:
                rec.update(_from_terms([t], t["value"], "direct"))
            elif i > 0 and fy_start:
                cur = term_value(occ_q, fy_start, q["end"], False, cutoff)
                prev = term_value(occ_q, fy_start, fqs[i - 1]["end"], False, cutoff)
                if cur and prev:
                    if cur["revised"] != prev["revised"]:
                        rec.update(status="not_determinable", nd_reason="recast_boundary", value=None,
                                   terms=[cur, prev], method="ytd_difference")
                    else:
                        rec.update(_from_terms([cur, prev], cur["value"] - prev["value"], "ytd_difference"))
                else:
                    rec.update(status="not_determinable", nd_reason="term_missing", value=None,
                               terms=[x for x in (cur, prev) if x])
            else:
                rec.update(status="not_determinable", nd_reason="not_disclosed", value=None, terms=[])
            out.append(rec)
    return out


def _from_terms(terms, value, method):
    if value is None or not terms or terms[0] is None:
        return {"status": "not_determinable", "nd_reason": "not_disclosed", "value": None, "terms": [],
                "method": method}
    return {"status": "computed", "nd_reason": None, "value": value, "terms": terms, "method": method}


def annual_value(occ, group, quantity, fy_start, fy_end, instant, cutoff):
    occ_q = occ[(occ["group_id"] == group) & (occ["quantity"] == quantity)]
    if occ_q.empty:
        return None
    return term_value(occ_q, fy_start, fy_end, instant, cutoff)
