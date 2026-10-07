"""Entités, appartenances datées et alias ; résolution des contreparties (§10.2).

Sources, dans cet ordre : têtes de groupe et prédécesseurs (même CIK, formerNames), entités
de SpaceX et laboratoires (graines), appartenances et alias établis par un extrait cité mot
pour mot (config : confirmed_entities, entity_aliases, own_entities ; décision D-0021), puis
la règle D-0022 : une contrepartie nommée par sa dénomination légale complète (suffixe de
forme juridique) est une entité et un groupe économique propres, sans fusion avec aucune
autre dénomination. Toute autre mention reste pending : visible dans les tables, absente
des agrégats. On ne fusionne jamais sur une ressemblance de nom.
"""
import copy
import datetime as dt
import re

from . import graph
from .graph import normalize_name

LEGAL_SUFFIX = re.compile(r"\b(inc|corp|llc|lp|ltd|plc|pbc|co|n a|ag|gmbh|s a|sa|b v|bv|n v|nv|pte|llp|lllp|"
                          r"sarl|s a r l|kk|spa|s p a|se|limited|l l c)$")
FILER_WORDS = {"we", "us", "the company", "our company"}


def _d(x):
    if x in (None, "", "none"):
        return None
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])


def _cp_group(norm):
    return "CP:" + norm


class Registry:
    """Entités et appartenances ; group_at() lit l'appartenance valide à une date, avec
    les deux dates d'une combinaison sous contrôle commun (§10.3) selon la vue."""

    def __init__(self, rows):
        self.rows = rows
        self.names = {}       # nom normalisé -> entity_id (entités et alias confirmés)
        self.members = {}     # entity_id -> [membership rows]
        self.entities = {}
        for r in rows:
            if r["record_kind"] == "entity":
                self.entities[r["entity_id"]] = r
            elif r["record_kind"] == "membership":
                self.members.setdefault(r["entity_id"], []).append(r)
        for r in rows:
            if r["record_kind"] in ("entity", "alias") and r.get("status") != "pending" and r.get("normalized_name"):
                self.names.setdefault(r["normalized_name"], r["entity_id"])

    def group_at(self, eid, date, view="as_known"):
        ms = self.members.get(eid) or []
        d = _d(date)
        hit = None
        for m in ms:
            if m.get("status") == "pending":
                continue
            frm = m.get("valid_from")
            if view == "as_known" and m.get("legal_date"):
                frm = str(m["legal_date"])
            elif view == "revised" and m.get("common_control_start"):
                frm = str(m["common_control_start"])
            lo, hi = _d(frm), _d(m.get("valid_to"))
            if d is None:
                ok = hi is None
            else:
                ok = (lo is None or lo <= d) and (hi is None or d <= hi)
            if ok:
                hit = m
        if hit:
            return hit["ref"]
        e = self.entities.get(eid)
        if e and e.get("status") != "pending" and e.get("normalized_name") and ms:
            # hors de toute appartenance datée (avant la date légale d'une combinaison, après une
            # cession) : l'entité forme son propre groupe, jamais fusionnée par défaut (§10.2)
            return _cp_group(e["normalized_name"])
        return None

    def treatment_at(self, eid, date, view="as_known"):
        g = self.group_at(eid, date, view)
        for m in self.members.get(eid) or []:
            if m["ref"] == g:
                return m.get("consolidation_treatment")
        return None


def build(p0, cfg, counterparty_names):
    """Lignes de la table entities (entités, appartenances, alias) et le registre."""
    base = copy.deepcopy(cfg)
    base["confirmed_entities"] = []          # traitées ici, avec leur extrait
    rows = graph.seed_entities(p0, base)
    by_norm = {r["normalized_name"]: r["entity_id"] for r in rows
               if r["record_kind"] in ("entity", "alias") and r.get("normalized_name")}

    def ent(eid, name, rule, evidence, kind="counterparty_group", status="confirmed", cik=None, fin=None):
        rows.append({"entity_id": eid, "record_kind": "entity", "ref": "none", "valid_from": "none",
                     "valid_to": None, "name": name, "normalized_name": normalize_name(name), "cik": cik,
                     "jurisdiction": None, "is_filer": bool(cik), "is_financial_institution": fin,
                     "status": status, "group_kind": kind, "consolidation_treatment": None,
                     "combination_method": None, "common_control_start": None, "legal_date": None,
                     "resolution_rule": rule, "evidence": evidence})
        by_norm.setdefault(normalize_name(name), eid)

    def mem(eid, group, frm="none", to=None, treat="parent", rule="executor_decision", evidence=None,
            method=None):
        rows.append({"entity_id": eid, "record_kind": "membership", "ref": group, "valid_from": frm or "none",
                     "valid_to": to, "name": None, "normalized_name": None, "cik": None, "jurisdiction": None,
                     "is_filer": None, "is_financial_institution": None, "status": "confirmed",
                     "group_kind": None, "consolidation_treatment": treat, "combination_method": method,
                     "common_control_start": None, "legal_date": None, "resolution_rule": rule,
                     "evidence": evidence})

    def alias(eid, name, evidence):
        rows.append({"entity_id": eid, "record_kind": "alias", "ref": name, "valid_from": "none",
                     "valid_to": None, "name": name, "normalized_name": normalize_name(name), "cik": None,
                     "jurisdiction": None, "is_filer": None, "is_financial_institution": None,
                     "status": "confirmed", "group_kind": None, "consolidation_treatment": None,
                     "combination_method": None, "common_control_start": None, "legal_date": None,
                     "resolution_rule": "executor_decision", "evidence": evidence})
        by_norm.setdefault(normalize_name(name), eid)

    def ev(c):
        return f"{c.get('decision')} ; {c.get('accession')} ; bloc {c.get('block')} ; « {c.get('quote')} »"

    # appartenances établies par un extrait (D-0021)
    for c in cfg.get("confirmed_entities") or []:
        n = normalize_name(c["name"])
        eid = by_norm.get(n) or f"name:{n}"
        if eid not in {r["entity_id"] for r in rows if r["record_kind"] == "entity"}:
            kind = "lab" if str(c["group"]).startswith("LAB:") else "config_group"
            ent(eid, c["name"], "executor_decision", ev(c), kind=kind)
        frm = c.get("valid_from") or "none"
        if frm != "none":
            # avant l'entrée dans le groupe, l'entité forme son propre groupe
            prev = (_d(frm) - dt.timedelta(days=1)).isoformat()
            mem(eid, _cp_group(n), "none", prev, "parent", evidence=ev(c) + " (avant l'entrée dans le groupe)")
        mem(eid, c["group"], frm, c.get("valid_to"), c.get("treatment", "consolidated_subsidiary"),
            evidence=ev(c) + (f" ; {c['membership_note']}" if c.get("membership_note") else ""))
    # entités propres sans suffixe juridique, identité établie par l'extrait (D-0021)
    for c in cfg.get("own_entities") or []:
        n = normalize_name(c["name"])
        eid = f"name:{n}"
        ent(eid, c["name"], "executor_decision", ev(c))
        if c.get("group"):
            prev = (_d(c["valid_from"]) - dt.timedelta(days=1)).isoformat()
            mem(eid, _cp_group(n), "none", prev, "parent", evidence=ev(c))
            mem(eid, c["group"], c["valid_from"], None, c.get("treatment", "consolidated_subsidiary"),
                evidence=ev(c) + (f" ; {c['membership_note']}" if c.get("membership_note") else ""))
        else:
            mem(eid, _cp_group(n), "none", None, "parent", evidence=ev(c))
    # alias établis par un extrait (D-0021)
    for a in cfg.get("entity_aliases") or []:
        target = a["of"]
        if target.startswith("LAB:"):
            eid = f"lab:{target.split(':', 1)[1].lower()}"
        else:
            eid = by_norm.get(normalize_name(target))
            if eid is None:      # cible nommée par sa dénomination légale complète (D-0022)
                eid = f"name:{normalize_name(target)}"
                ent(eid, target, "executor_decision", "D-0022 : dénomination légale complète, cible d'un alias")
                mem(eid, _cp_group(normalize_name(target)), evidence="D-0022")
        alias(eid, a["alias"], ev(a))

    reg = Registry(rows)
    # contreparties nommées : dénomination légale complète (D-0022), sinon pending
    known = set(reg.names)
    for name, fin in sorted(counterparty_names.items()):
        n = normalize_name(name)
        # « we » ou l'identifiant d'un groupe écrit par le lecteur pour le déclarant : pas une contrepartie
        if not n or n in known or n in FILER_WORDS or name.strip().upper() in (cfg.get("groups") or {}):
            continue
        known.add(n)
        if LEGAL_SUFFIX.search(n):
            eid = f"name:{n}"
            ent(eid, name, "executor_decision",
                "D-0022 : dénomination légale complète dans une pièce déposée ; entité et groupe propres", fin=fin)
            mem(eid, _cp_group(n), evidence="D-0022")
        else:
            ent(f"name:{n}", name, None,
                "nommée dans une observation, identité non affirmée par une pièce (§10.2)", status="pending", fin=fin)
    return rows, Registry(rows)


def resolve(reg, name, date, view="as_known"):
    """(entity_id, groupe, statut) d'un nom à une date ; groupe None si pending ou inconnu."""
    if not name:
        return None, None, None
    n = normalize_name(name)
    eid = reg.names.get(n)
    if eid is None:
        e = reg.entities.get(f"name:{n}")
        if e is None:
            return f"name:{n}", None, "unknown"
        return e["entity_id"], (reg.group_at(e["entity_id"], date, view) if e["status"] == "confirmed" else None), \
            e["status"]
    return eid, reg.group_at(eid, date, view), "confirmed"
