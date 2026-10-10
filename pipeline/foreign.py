"""Bloc `foreign` de §14 : émetteurs étrangers (20-F, 40-F, 6-K), D-0042.

- **Inventaire** : candidats de la découverte dont une mention vient d'un formulaire étranger
  (20-F, 40-F, 6-K, F-1, F-4 et leurs amendements).
- **Sélection**, fixée avant toute lecture (`config.yaml`, `foreign.selection`) : les unités de la
  file de la découverte (D-0036) tirées d'un formulaire étranger, pour les émetteurs que la spec
  nomme comme nœuds de la chaîne (IREN, Nebius) et pour les contreparties étrangères déjà présentes
  dans une paire ou un cycle. Les autres unités étrangères restent dans la file, « non traitées ».
- **Cadre comptable** d'une note : celui de ses balises dans les Notes Data Sets (colonne
  `version` : `ifrs/…` ou `us-gaap/…`). Une contrepartie en IFRS est traitée à part : aucune somme
  entre cadres (invariant f, §7.6).
- **6-K** : furnished (§2.1), niveau E, sauf mention expresse d'incorporation par référence dans un
  document d'enregistrement, lue dans le 6-K lui-même ; il devient alors admissible.
"""
import json
import re

import pandas as pd

from . import cache, config, discovery as D, edgar, net
from .graph import normalize_name

INVENTORY = config.DB_DIR / "foreign_inventory.parquet"
INCORP = re.compile(r"incorporated\s+by\s+reference\s+(?:in|into)\b[^.]{0,120}?registration\s+statements?", re.I)


def forms(cfg=None):
    cfg = cfg or config.load()
    return set((cfg.get("foreign") or {}).get("forms") or [])


def _form_of():
    m = pd.read_parquet(D.config.DB_DIR / "discovery_mentions.parquet", columns=["adsh", "form"])
    return dict(zip(m["adsh"], m["form"]))


def inventory(cfg=None):
    """Émetteurs étrangers de la file : mentions par formulaire, groupes nommés, rang."""
    cfg = cfg or config.load()
    ff = forms(cfg)
    m = pd.read_parquet(config.DB_DIR / "discovery_mentions.parquet")
    m = m[m["form"].isin(ff)]
    cand = pd.read_parquet(D.CANDIDATES)[["cik", "rank", "filer"]]
    cand["cik"] = cand["cik"].astype(str)
    g = m.groupby(m["cik"].astype(str)).agg(
        mentions=("form", "size"), forms=("form", lambda x: json.dumps({k: int(v) for k, v in x.value_counts().items()})),
        groups=("group", lambda x: ";".join(sorted(set(x)))), documents=("adsh", "nunique")).reset_index()
    g = g.merge(cand, on="cik", how="left")
    return g.sort_values(["rank", "cik"]).reset_index(drop=True)


def graph_counterparty_ciks():
    """CIK des contreparties déjà présentes dans une paire ou un cycle : groupes de contrepartie
    d'une arête dont une entité du registre porte un CIK (déposants découverts, §10.2)."""
    t = config.ROOT / "tables"
    if not (t / "links.parquet").exists():
        return set()
    l = pd.read_parquet(t / "links.parquet", columns=["link_kind", "from_group", "to_group"])
    l = l[l["link_kind"] == "edge"]
    nodes = {g for g in set(l["from_group"]) | set(l["to_group"]) if isinstance(g, str) and g.startswith("CP:")}
    e = pd.read_parquet(t / "entities.parquet")
    mem = e[(e["record_kind"] == "membership") & (e["ref"].isin(nodes))]
    ent = e[(e["record_kind"] == "entity") & e["entity_id"].isin(mem["entity_id"]) & e["cik"].notna()]
    return {str(int(c)) for c in ent["cik"] if str(c).strip().isdigit()}


def selected_units(cfg=None):
    """Unités de la file tirées d'un formulaire étranger, pour les émetteurs retenus par la règle."""
    cfg = cfg or config.load()
    f = cfg.get("foreign") or {}
    sel = set(f.get("selection") or [])
    ciks = set()
    if "named_issuers" in sel:
        ciks |= {str(int(x["cik"])) for x in f.get("named_issuers") or []}
    if "graph_counterparties" in sel:
        ciks |= graph_counterparty_ciks()
    ff = forms(cfg)
    form_of = _form_of()
    u = pd.read_parquet(D.UNITS)
    u = u[u["cik"].astype(str).isin(ciks)].copy()
    u["form"] = u["adsh"].map(form_of)
    return u[u["form"].isin(ff)].sort_values("order")


def framework(u):
    """Cadre comptable d'une note de la file : version de sa balise dans les Notes Data Sets."""
    if u["kind"] != "note":
        return None
    a = D._Archive.get(u["archive"])
    pre = a["pre"]
    v = pre[(pre["adsh"] == u["adsh"]) & (pre["tag"] == u["doc"])]["version"]
    v = {str(x).split("/")[0] for x in v}
    if "ifrs" in v:
        return "ifrs"
    if "us-gaap" in v:
        return "us_gaap"
    return None


def incorporation(ed, cik, acc):
    """Mention expresse d'incorporation par référence d'un 6-K dans un document d'enregistrement,
    lue dans son document principal (§2.1) : (vrai ou faux, extrait)."""
    idx = ed.filing_index(cik, acc)
    items = idx.get("directory", {}).get("item", [])
    docs = [i["name"] for i in items if re.search(r"\.(htm|html|txt)$", i["name"], re.I)
            and "index" not in i["name"].lower()]
    for name in docs[:3]:
        raw = ed.archive(cik, acc, name)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", D.textnorm_decode(raw)))
        m = INCORP.search(text)
        if m:
            s = text.rfind(".", 0, m.start()) + 1
            e = text.find(".", m.end())
            return True, text[s:e + 1 if e > 0 else m.end() + 200].strip()[:600], name
    return False, None, docs[0] if docs else None


def prepare(rate=4.0):
    """Construit les blocs des unités sélectionnées qui ne le sont pas encore, avec leur cadre
    comptable et, pour un 6-K, l'état d'incorporation par référence ; les inscrit au catalogue de
    la découverte (la file reste celle de D-0036, lue ici hors de son ordre au titre de foreign)."""
    cfg = config.load()
    client = net.SecClient(D.AS_OF, cfg)
    client.min_interval = 1.0 / rate
    ed = edgar.Edgar(client, D.AS_OF)
    done = D.built_units()
    todo = [u for u in selected_units(cfg).to_dict("records") if u["order"] not in done]
    nb = 0
    for u in todo:
        if u["kind"] == "exhibit_header":
            b, err = D._exhibit_block(u, client), None
        else:
            b, err = D._note_unit_block(u, client)
        if b:
            b["framework"] = framework(u)
            b["selected_by"] = "foreign"
            if str(u["form"]).startswith("6-K"):
                inc, quote, doc = incorporation(ed, u["cik"], u["adsh"])
                b["incorporated_by_reference"] = inc
                b["incorporation_quote"] = quote
                b["incorporation_document"] = doc
                if inc:
                    # admissible : exposé à la Section 11 ; états intermédiaires non audités (niveau C)
                    b["tier"], b["assurance_level"] = "C", "unaudited"
        rec = {"order": int(u["order"]), "rank": int(u["rank"]), "cik": u["cik"], "kind": u["kind"],
               "adsh": u["adsh"], "doc": u["doc"], "content_key": b["content_key"] if b else None, "error": err,
               "selected_by": "foreign"}
        if b:
            with open(D.DISC_CATALOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(b, ensure_ascii=False) + "\n")
            nb += 1
        with open(D.BUILT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    inv = inventory(cfg)
    inv["selected"] = inv["cik"].isin({str(u["cik"]) for u in selected_units(cfg).to_dict("records")})
    inv.to_parquet(INVENTORY, index=False)
    print(f"blocs préparés : {nb} sur {len(todo)} unités ; requêtes {client.stats['requests']} ; "
          f"émetteurs étrangers dans la file : {len(inv)}, retenus : {int(inv['selected'].sum())}")


def block_framework(b):
    """Cadre comptable d'un bloc : celui qu'il porte (notes de la découverte), US GAAP pour les notes
    des groupes de config.yaml (tous déposent en US GAAP), aucun pour un contrat ou un narratif."""
    if b.get("framework"):
        return b["framework"]
    if b.get("block_kind") in ("discovery_note",):
        return "us_gaap" if str(b.get("form") or "").split("/")[0] in ("10-K", "10-Q", "10-KT", "10-QT") else None
    if b.get("block_kind") in ("related_party_note", "investment_note", "debt_note", "lease_note", "commitments_note",
                               "revenue_note", "lever_note", "concentration_text", "spacex_annual_note", "going_concern",
                               "item_9a", "item_4_10q"):
        return "us_gaap"
    return None


if __name__ == "__main__":
    prepare()
