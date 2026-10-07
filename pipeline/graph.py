"""Entités, arêtes et statut « financé » (§3, §10).

Une entité par personne morale, reliée à ses groupes par des appartenances datées. On ne
fusionne que sur CIK ou identité affirmée par une pièce ; une contrepartie non confirmée
reste pending, visible dans les tables, absente des agrégats. Une arête est orientée de
la partie qui fournit la ressource vers celle qui la reçoit.
"""
import datetime as dt
import json
import re

import pandas as pd

from . import config

SUFFIX = [(r"\bincorporated\b|\binc\b", "inc"), (r"\bcorporation\b|\bcorp\b", "corp"),
          (r"\blimited liability company\b|\bl\.?l\.?c\b", "llc"), (r"\blimited partnership\b|\bl\.?p\b", "lp"),
          (r"\blimited\b|\bltd\b", "ltd"), (r"\bpublic limited company\b|\bplc\b", "plc"),
          (r"\bpublic benefit corporation\b|\bpbc\b", "pbc"), (r"\bcompany\b|\bco\b", "co")]


def normalize_name(name):
    """Casse, ponctuation, espaces multiples et « The » initial retirés ; suffixes ramenés
    à inc, corp, llc, lp, ltd, plc ou pbc ; ni troncature ni distance d'édition (§10.2)."""
    s = (name or "").lower()
    s = re.sub(r"[.,;:'\"()\[\]]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^the\s+", "", s)
    for pat, rep in SUFFIX:
        s = re.sub(pat, rep, s)
    return re.sub(r"\s+", " ", s).strip()


def seed_entities(p0, cfg):
    """Entités de départ : têtes de groupe, prédécesseurs, entités connues de SpaceX, laboratoires."""
    rows = []

    def ent(eid, name, cik=None, is_filer=False, kind="config_group", status="confirmed", rule="config_seed",
            evidence=None):
        rows.append({"entity_id": eid, "record_kind": "entity", "ref": "none", "valid_from": "none",
                     "valid_to": None, "name": name, "normalized_name": normalize_name(name), "cik": cik,
                     "jurisdiction": None, "is_filer": is_filer, "is_financial_institution": False,
                     "status": status, "group_kind": kind, "consolidation_treatment": None,
                     "combination_method": None, "common_control_start": None, "legal_date": None,
                     "resolution_rule": rule, "evidence": evidence})

    def mem(eid, group, frm, to=None, treat="parent", method=None, ccs=None, legal=None, rule="config_seed",
            evidence=None):
        rows.append({"entity_id": eid, "record_kind": "membership", "ref": group, "valid_from": frm or "none",
                     "valid_to": to, "name": None, "normalized_name": None, "cik": None, "jurisdiction": None,
                     "is_filer": None, "is_financial_institution": None, "status": "confirmed",
                     "group_kind": None, "consolidation_treatment": treat, "combination_method": method,
                     "common_control_start": ccs, "legal_date": legal, "resolution_rule": rule,
                     "evidence": evidence})

    def alias(eid, name, frm, to, evidence):
        rows.append({"entity_id": eid, "record_kind": "alias", "ref": name, "valid_from": frm or "none",
                     "valid_to": to, "name": name, "normalized_name": normalize_name(name), "cik": None,
                     "jurisdiction": None, "is_filer": None, "is_financial_institution": None,
                     "status": "confirmed", "group_kind": None, "consolidation_treatment": None,
                     "combination_method": None, "common_control_start": None, "legal_date": None,
                     "resolution_rule": "formerly_known_as", "evidence": evidence})

    succession = {"0001649338": ("2018-04-04", "8-K12B 0001193125-18-107559"),
                  "0001441634": ("2016-02-01", "8-K12B 0001193125-16-446865"),
                  "0001058057": ("2021-04-20", "8-K12B 0001193125-21-122938")}
    for cik, m in p0["meta"].items():
        eid = f"cik:{cik}"
        ent(eid, m["name"], cik, True, "config_group", rule="same_cik", evidence=f"submissions {cik}")
        if m["is_predecessor"]:
            to, ev = succession.get(cik, (None, None))
            mem(eid, m["group"], "none", to, "parent", "succession", rule="succession_document", evidence=ev)
        else:
            mem(eid, m["group"], "none", None, "parent", rule="same_cik", evidence=f"company_tickers.json {cik}")
        for fn in m.get("formerNames") or []:
            alias(eid, fn["name"], fn.get("from", "")[:10] or None, fn.get("to", "")[:10] or None,
                  f"formerNames {cik}")
    # SpaceX : D2 et D-0011
    spx = {"X.AI Holdings Corp.": ("2026-02-02", None), "X.AI Corp.": ("2026-02-02", "0002002695"),
           "X Holdings Corp.": ("2026-02-02", None), "X Corp.": ("2026-02-02", None),
           "X.AI LLC": ("2026-02-02", None)}
    for name, (legal, cik) in spx.items():
        eid = f"cik:{cik}" if cik else f"name:{normalize_name(name)}"
        ent(eid, name, cik, bool(cik), "config_group", rule="notes_consolidated",
            evidence="424B4 0001628280-26-042639, note 1 ; 10-Q 0001628280-26-052535, note 1 (D-0011)")
        mem(eid, "SPCX", "2023-01-01", None, "consolidated_subsidiary", "common_control", "2023-01-01", legal,
            rule="notes_consolidated", evidence="D-0011")
    eid = f"name:{normalize_name('CTC Property, LLC')}"
    ent(eid, "CTC Property, LLC", None, False, "config_group", rule="notes_consolidated",
        evidence="10-Q 0001628280-26-052535, note de dette (garant du prêt-relais), D-0011")
    mem(eid, "SPCX", "2026-06-30", None, "consolidated_subsidiary", None, None, None, rule="notes_consolidated",
        evidence="D-0011 : date d'entrée non établie, attestée au 2026-06-30")
    for lab in cfg["labs"]:
        ent(f"lab:{lab.lower()}", lab, None, False, "lab", rule="config_seed",
            evidence="config.yaml labs (§10.4)")
        mem(f"lab:{lab.lower()}", f"LAB:{lab.upper()}", "none", None, "parent", rule="config_seed")
    for c in cfg.get("confirmed_entities") or []:
        eid = c.get("entity_id") or f"name:{normalize_name(c['name'])}"
        ent(eid, c["name"], c.get("cik"), bool(c.get("cik")), c.get("group_kind", "counterparty_group"),
            rule=c.get("rule", "executor_decision"), evidence=c.get("evidence"))
        mem(eid, c["group"], c.get("valid_from", "none"), c.get("valid_to"), c.get("treatment", "parent"),
            rule=c.get("rule", "executor_decision"), evidence=c.get("evidence"))
        for a in c.get("aliases") or []:
            alias(eid, a, None, None, c.get("evidence"))
    return rows


def resolver(entity_rows):
    """Nom normalisé -> (entity_id, groupe) pour les entités confirmées et leurs alias."""
    names = {}
    groups = {}
    for r in entity_rows:
        if r["record_kind"] == "membership" and r["status"] == "confirmed":
            groups.setdefault(r["entity_id"], r["ref"])
    for r in entity_rows:
        if r["record_kind"] in ("entity", "alias") and r["status"] == "confirmed":
            names[r["normalized_name"]] = r["entity_id"]
    return names, groups


def group_of_name(name, names, groups, filer_group=None):
    if not name:
        return None, None
    n = normalize_name(name)
    eid = names.get(n)
    if eid:
        return eid, groups.get(eid)
    return f"name:{n}", None


def edges_from_observations(obs, entity_rows):
    """Arêtes du graphe : une observation valide avec famille, type et contrepartie nommée
    ou dérivable. Arête `amount` si un montant admissible et une période ; sinon `relation`.
    Les contreparties non confirmées restent pending et hors des agrégats."""
    names, groups = resolver(entity_rows)
    pend = {}
    links = []
    for o in obs:
        if o["kind"] != "observation" or o["validation_state"] != "valid":
            continue
        if not o.get("family") or o.get("family") == "none" or not o.get("edge_type") or o.get("edge_type") == "none":
            continue
        if o.get("counterparty_evidence") not in ("named", "derivable"):
            continue
        filer_group = o["group_id"]
        payer_e, payer_g = group_of_name(o.get("payer"), names, groups)
        payee_e, payee_g = group_of_name(o.get("payee"), names, groups)
        # le déposant est l'une des parties : ses noms se rattachent à son groupe
        for side in ("payer", "payee"):
            nm = o.get(side)
            if nm and normalize_name(nm) in ("we", "us", "the company", "our company"):
                if side == "payer":
                    payer_e, payer_g = f"group:{filer_group}", filer_group
                else:
                    payee_e, payee_g = f"group:{filer_group}", filer_group
        for e, g, nm in ((payer_e, payer_g, o.get("payer")), (payee_e, payee_g, o.get("payee"))):
            if e and g is None and nm:
                pend[e] = nm
        amount_ok = o.get("amount") is not None and o.get("amount_nature") != "management_estimate" \
            and o.get("stage") not in (None, "none", "intent_non_binding") and o.get("period_end")
        links.append({
            "link_key": "obs:" + o["obs_key"], "link_kind": "edge", "family": o["family"],
            "edge_type": o["edge_type"], "edge_evidence": "amount" if amount_ok else "relation",
            "advance": o.get("edge_type") == "prepayment", "reciprocal_purchase": None,
            "from_entity": payer_e, "to_entity": payee_e, "from_group": payer_g, "to_group": payee_g,
            "amount": o.get("amount") if amount_ok else None, "unit": o.get("unit"), "currency": o.get("currency"),
            "amount_nature": o.get("amount_nature"), "stage": o.get("stage"),
            "period_start": o.get("period_start"), "period_end": o.get("period_end"),
            "event_date": o.get("event_date"), "relation_type": None, "a_key": None, "b_key": None,
            "allocation": None, "pair_id": None, "resolution": None, "resolution_ref": None,
            "instrument_key": o.get("instrument_key"), "evidence_keys": json.dumps([o["obs_key"]]),
            "tier": o.get("tier"), "filing_status": o.get("filing_status"),
            "source_perspective": "reporting_entity", "knowledge_date": o.get("knowledge_date"),
            "elimination_status": "not_applicable" if payer_g != payee_g else "eliminated",
        })
    pending = [{"entity_id": e, "record_kind": "entity", "ref": "none", "valid_from": "none", "valid_to": None,
                "name": n, "normalized_name": normalize_name(n), "cik": None, "jurisdiction": None,
                "is_filer": False, "is_financial_institution": None, "status": "pending",
                "group_kind": "counterparty_group", "consolidation_treatment": None, "combination_method": None,
                "common_control_start": None, "legal_date": None, "resolution_rule": None,
                "evidence": "nommée dans une observation, identité non affirmée par une pièce"}
               for e, n in pend.items()]
    return links, pending
