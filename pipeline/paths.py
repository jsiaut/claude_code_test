"""Bloc `paths` de §14 : cycles orientés entre groupes (`documented_path`, D-0041).

Le retour « après un ou deux intermédiaires » échappe aux mesures bilatérales. Les arêtes vont
dans le sens de la ressource (§3.1) : financeur → financé, garant → obligé, client →
fournisseur, fournisseur → client pour une contrepartie au client. Un cycle orienté de longueur
2 ou 3 entre groupes (hors intragroupe) est un chemin par lequel une ressource revient à son
point de départ ; il passe par au moins un groupe de `config.yaml`.

- `temporal` : `yes` si l'on peut choisir une arête par maillon dont les périodes sont actives
  ensemble ou à moins de quatre trimestres d'écart (trimestres civils), `no` sinon, `unknown`
  si un maillon n'a aucune arête datée ;
- pièce d'une paire d'arêtes consécutives (x → y, y → z) : ligne L1 à L5 dont les parties
  résolues comprennent y et l'un de ses deux voisins, et dont l'extrait nomme x, y et z (pour un
  cycle de longueur 2, x = z : c'est la règle des paires, D-0039) ;
- conclusion : `documented_dependency` seulement si chaque paire d'arêtes consécutives a sa
  pièce et que le cycle combine financement (ou contrepartie au client) et achats ; sinon
  `commercial_with_financing`, `reciprocal_commercial_only` ou `causality_not_established`,
  comme pour une paire (§3.4). Aucun ratio de chemin ne se publie : des montants de natures
  différentes ne se composent pas.
"""
import datetime as dt
from itertools import product

from . import circularity as C
from .graph import normalize_name
from .measures import cell

NONE = "none"
FAMILIES = ("financing", "credit_support", "commercial", "customer_consideration")
FIN = ("financing", "customer_consideration")


def _d(x):
    return C._d(x)


def admissible(l):
    """Arête du graphe des chemins : non éliminée, deux groupes connus et distincts, famille de
    §3.1, ouverture et non clôture (un remboursement suit la trésorerie, guide §3)."""
    return (l.get("elimination_status") != "eliminated" and l.get("from_group") and l.get("to_group")
            and l["from_group"] != l["to_group"] and l.get("family") in FAMILIES and C._opening(l))


def interval(l):
    """Période active d'une arête : période de la ligne, sinon sa date (§7.4)."""
    o = l["_obs"]
    a, b = _d(o.get("period_start")), _d(o.get("period_end"))
    if a and b and a <= b:
        return a, b
    d = l.get("_date")
    return (d, d) if d else None


def qidx(d):
    return d.year * 4 + (d.month - 1) // 3


def graph(edges):
    adj = {}
    for l in edges:
        if admissible(l):
            adj.setdefault(l["from_group"], {}).setdefault(l["to_group"], []).append(l)
    return adj


def cycles(adj, groups, lengths=(2, 3)):
    """Cycles orientés simples de longueur 2 ou 3 qui passent par un groupe de `config.yaml`,
    chacun une fois, écrits à partir de leur plus petit groupe de `config.yaml`."""
    out = set()
    for a in adj:
        for b in adj.get(a, {}):
            if 2 in lengths and a in adj.get(b, {}) and ({a, b} & groups):
                out.add(_canon((a, b), groups))
            if 3 in lengths:
                for c in adj.get(b, {}):
                    if c in (a, b):
                        continue
                    if a in adj.get(c, {}) and ({a, b, c} & groups):
                        out.add(_canon((a, b, c), groups))
    return sorted(out)


def _canon(nodes, groups):
    n = len(nodes)
    rots = [tuple(nodes[i:] + nodes[:i]) for i in range(n)]
    start = min(x for x in nodes if x in groups)
    return min(r for r in rots if r[0] == start)


def temporal(steps, max_q=4):
    """yes / no / unknown, et l'écart minimal en trimestres sur un choix d'une arête par maillon."""
    ivs = []
    for ls in steps:
        s = sorted({iv for iv in (interval(l) for l in ls) if iv})
        if not s:
            return "unknown", None
        ivs.append(s)
    best = None
    for combo in product(*ivs):
        gap = max(0, max(qidx(a) for a, _ in combo) - min(qidx(b) for _, b in combo))
        if best is None or gap < best:
            best = gap
            if gap == 0:
                break
    return ("yes" if best < max_q else "no"), best


def structure(steps):
    fin = [i for i, ls in enumerate(steps) if any(l["family"] in FIN for l in ls)]
    com = [i for i, ls in enumerate(steps) if any(l["family"] == "commercial" for l in ls)]
    if any(i != j for i in fin for j in com):
        return "commercial_and_financing"
    if len(com) == len(steps):
        return "reciprocal_commercial"
    if not com:
        return "financing_only"
    return "commercial_only"


def names_by_group(reg, adj):
    """Noms d'un groupe : ceux du registre, et la contrepartie nommée des lignes déposées par un
    autre groupe dont l'arête aboutit à lui ou en part (D-0039)."""
    out = {}
    for f, tos in adj.items():
        for t, ls in tos.items():
            for l in ls:
                o = l["_obs"]
                filer = o.get("group_id")
                cp = o.get("counterparty_name")
                if not cp:
                    continue
                side = t if filer == f else (f if filer == t else None)
                if side and side != filer:
                    out.setdefault(side, set()).add(cp)
    return out


def named(o, g, names):
    q = (o.get("quote") or "")
    ql = q.lower()
    if any(n and n.lower() in ql for n in names.get(g, ())):
        return True
    self_ref = ("the Company", "Company", "the Group", "The Group", "we ", "We ", "our ", "us ")
    return o.get("group_id") == g and any(x in q for x in self_ref)


def step_pieces(x, y, z, link_obs, parties_of, names):
    """Pièces de la paire d'arêtes consécutives (x → y, y → z)."""
    out = []
    need = {x, y, z}
    for o in link_obs:
        parties = parties_of[o["obs_key"]]
        if y not in parties or not ({x, z} & parties):
            continue
        if all(named(o, g, names) for g in need):
            out.append(o)
    return out


def path_measures(edges, obs, reg, groups, groups_window, as_of, text_done=frozenset(), pair_linkage=None,
                  lengths=(2, 3), max_q=4):
    """Cellules documented_path (une par cycle, vue as_known) et décompte pour E.6."""
    as_of_d = dt.date.fromisoformat(as_of)
    groups = set(groups)
    adj = graph(edges)
    found = cycles(adj, groups, lengths)
    reg_names = {g: C.names_of_group(reg, g) for g in {n for c in found for n in c}}
    extra = names_by_group(reg, adj)
    names = {g: (reg_names.get(g, set()) | extra.get(g, set())) for g in reg_names}
    link_obs = [o for o in obs if o["kind"] == "observation" and o["validation_state"] == "valid"
                and o.get("link_category") not in (None, NONE)]
    parties_of = {o["obs_key"]: C.party_groups(o, reg) for o in link_obs}
    pair_linkage = pair_linkage or {}
    cells, paths = [], []
    for nodes in found:
        n = len(nodes)
        steps = [adj[nodes[i]][nodes[(i + 1) % n]] for i in range(n)]
        temp, gap = temporal(steps, max_q)
        st = structure(steps)
        pieces = []
        for i in range(n):
            x, y, z = nodes[i - 1], nodes[i], nodes[(i + 1) % n]
            pieces.append(step_pieces(x, y, z, link_obs, parties_of, names))
        documented = all(pieces)
        # recherche complète : chaque nœud est un groupe dont le texte est lu, ou un laboratoire qui ne
        # dépose pas (§10.4), et aucune paire mesurée du cycle n'est en recherche incomplète (E.0)
        complete = all(x in text_done or str(x).startswith(("LAB:", "NF:")) for x in nodes) and all(
            pair_linkage.get((a, b)) != "search_incomplete" and pair_linkage.get((b, a)) != "search_incomplete"
            for a, b in zip(nodes, nodes[1:] + nodes[:1]))
        linkage = "documented_link" if documented else ("searched_none_found" if complete else "search_incomplete")
        if documented and st == "commercial_and_financing":
            concl = "documented_dependency"
        elif st == "commercial_and_financing":
            concl = "commercial_with_financing"
        elif st == "reciprocal_commercial":
            concl = "reciprocal_commercial_only"
        else:
            concl = "causality_not_established"
        s = nodes[0]
        win = groups_window.get(s, {}).get("window_start")
        key = ">".join(nodes)
        flags = {"length": n, "nodes": list(nodes), "temporal": temp, "gap_quarters": gap,
                 "edge_structure": st, "linkage_evidence": linkage,
                 "steps": [{"from": nodes[i], "to": nodes[(i + 1) % n],
                            "families": sorted({l["family"] for l in steps[i]}),
                            "edges": sorted(l["link_key"] for l in steps[i])} for i in range(n)],
                 "step_pieces": [sorted({o["obs_key"] for o in p}) for p in pieces],
                 "link_categories": sorted({o["link_category"] for p in pieces for o in p})}
        cells.append(cell("documented_path", s, win, as_of_d, "as_known", as_of, breakdown=key,
                          value_text=concl, status="computed", flags=flags))
        paths.append({"key": key, "nodes": nodes, "temporal": temp, "conclusion": concl, "structure": st,
                      "linkage": linkage, "gap": gap})
    return cells, paths
