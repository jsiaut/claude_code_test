"""D-0086, volet B : typologie du Bulletin BRI n° 137 (« Circular relationships among AI firms », 1er octobre 2026),
appliquée aux arêtes du modèle (point 4).

Une relation d'investissement I -> T entre deux nœuds du périmètre (une arête `financing` de I vers T, de tout type et
à tout stade) est circulaire si une relation commerciale lie aussi I et T dans la fenêtre. Une arête commerciale va du
payeur au fournisseur : I fournit T (type 1, `supplier_investor`), I achète à T (type 2, `customer_investor`), ou les
deux (type 3, `reciprocal`) ; sinon `financing_only`. Les titres ou crédits remis à un client se comptent à part.
Descriptive (rang 2) : hors du revenu, de l'exposition, des paires, des cycles et des annexes E et F.
"""
import datetime as dt
from collections import Counter

from . import config
from .measures import NONE, cell

TYPES = ("supplier_investor", "customer_investor", "reciprocal", "financing_only")
BIS_TYPE = {"supplier_investor": 1, "customer_investor": 2, "reciprocal": 3, "financing_only": None}
ADVANCE = ("intent_non_binding", "signed", "available", "drawn_or_paid", "delivered", "recognized", "settled")
BASIS = ("relation d'investissement I -> T entre nœuds du périmètre (arête de financement de tout type et de tout stade), "
         "typée selon le Bulletin BRI n° 137 par les arêtes commerciales de la même fenêtre : I fournit T (type 1), "
         "I achète à T (type 2), les deux (type 3) ; descriptive : hors du revenu, de l'exposition, des paires, des "
         "cycles et des annexes E et F (D-0086, point 4)")


def perimeter(cfg):
    """Nœuds du périmètre (D-0086, point 4) : groupes hors gestionnaires d'actifs exclus, laboratoires, non-déposants."""
    t = cfg.get("bis_typology") or {}
    out = {g for g in (cfg.get("groups") or {}) if g not in set(t.get("excluded_groups") or [])}
    out |= {f"LAB:{x.upper()}" for x in cfg.get("labs") or []}
    out |= {x["ref"] if isinstance(x, dict) else x for x in cfg.get("non_filers") or []}
    return out


def _d(v):
    if v is None or (isinstance(v, float) and v != v) or str(v) in ("", NONE, "NaT"):
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _stage(es):
    """Stade le plus avancé d'un ensemble d'arêtes ; `terminated` seulement si toutes le sont."""
    st = [e.get("stage") for e in es]
    adv = [s for s in st if s in ADVANCE]
    if adv:
        return max(adv, key=ADVANCE.index)
    return "terminated" if "terminated" in st else None


def classify(edges, nodes, start=None, end=None):
    """Relations d'investissement de la fenêtre [start, end] typées, {(I, T): {...}}, et contreparties au client
    [(fournisseur, client)]. Une arête compte si sa date tombe dans la fenêtre ; sans date, seulement sans borne de
    début. Hors intragroupe ; arêtes éliminées exclues."""
    fin, com, cc = {}, {}, set()
    for e in edges:
        if e.get("link_kind", "edge") != "edge" or e.get("elimination_status") == "eliminated":
            continue
        a, b = e.get("from_group"), e.get("to_group")
        if a not in nodes or b not in nodes or a == b:
            continue
        d = _d(e.get("_date"))
        if d is None:
            if start is not None:
                continue
        elif (start is not None and d < start) or (end is not None and d > end):
            continue
        fam = e.get("family")
        if fam == "financing":
            fin.setdefault((a, b), []).append(e)
        elif fam == "commercial":
            com.setdefault((a, b), []).append(e["link_key"])
        elif fam == "customer_consideration":
            cc.add((a, b))
    out = {}
    for (i, t), es in fin.items():
        sup, cus = (t, i) in com, (i, t) in com
        typ = "reciprocal" if sup and cus else "supplier_investor" if sup else "customer_investor" if cus else "financing_only"
        out[(i, t)] = {"type": typ, "financing": sorted(e["link_key"] for e in es),
                       "commercial_target_pays_investor": sorted(com.get((t, i), [])),
                       "commercial_investor_pays_target": sorted(com.get((i, t), [])), "stage": _stage(es)}
    return out, sorted(cc)


def cells(edges, as_of, cfg=None):
    """Cellules investment_relationship_type par fenêtre de la configuration, et décomptes (D-0086, points 4 et 7). Une
    fenêtre sans fin prend toutes les arêtes connues à l'as_of, quelle que soit leur date."""
    cfg = cfg or config.load()
    t = cfg.get("bis_typology")
    if not t:
        return [], {}
    nodes = perimeter(cfg)
    out, stats = [], {}
    for ws, we in t.get("windows") or []:
        s, e = _d(ws), _d(we)
        rel, cc = classify(edges, nodes, s, e)
        for (i, tg), r in sorted(rel.items()):
            # fenêtre ouverte : toutes les arêtes connues à l'as_of, cellule datée de l'as_of (D-0086, point 7)
            out.append(cell("investment_relationship_type", i, s, e or as_of, "as_known", as_of, counterparty=tg,
                            value_text=r["type"],
                            flags={"bis_type": BIS_TYPE[r["type"]], "stage": r["stage"], "financing": r["financing"],
                                   "commercial_target_pays_investor": r["commercial_target_pays_investor"],
                                   "commercial_investor_pays_target": r["commercial_investor_pays_target"],
                                   "nodes": len(nodes), "basis": BASIS}))
        stats[f"{ws or NONE}..{we or as_of}"] = dict(Counter(r["type"] for r in rel.values()), relations=len(rel),
                                            customer_consideration=len(cc))
    return out, stats
