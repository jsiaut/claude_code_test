"""Entités et noms normalisés (§10).

Une entité par personne morale, reliée à ses groupes par des appartenances datées. On ne
fusionne que sur CIK ou identité affirmée par une pièce ; une contrepartie non confirmée
reste pending, visible dans les tables, absente des agrégats. Les arêtes se construisent dans
links.py ; l'ancien constructeur d'ici, qui n'était plus appelé, a été retiré (D-0069, point 9).
"""
import re


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

    # date de succession de chaque prédécesseur et sa pièce (§10.1) : config.yaml depuis D-0055
    succession = {str(c): (str(s["date"]), s.get("evidence")) for c, s in (cfg.get("successions") or {}).items()}
    for cik, m in p0["meta"].items():
        eid = f"cik:{cik}"
        ent(eid, m["name"], cik, True, "config_group", rule="same_cik", evidence=f"submissions {cik}")
        if m["is_predecessor"]:
            to, ev = succession.get(cik, (None, None))
            mem(eid, m["group"], "none", to, "parent", "succession", rule="succession_document", evidence=ev)
        elif (cfg.get("reverse_combinations") or {}).get(m["group"]):
            # fusion inversée (D-0043) : même CIK, mais les rapports antérieurs à la réalisation
            # présentent le déclarant légal ; ils sont hors du groupe (phase 0, pre_combination)
            rc = cfg["reverse_combinations"][m["group"]]
            mem(eid, m["group"], "none", None, "parent", "reverse_recapitalization", rule="same_cik",
                evidence=f"company_tickers.json {cik} ; réalisation le {rc['consummation']}, déclarant légal "
                         f"{rc.get('legal_registrant')}, acquéreur comptable {rc.get('accounting_acquirer')} (D-0043)")
        elif (cfg.get("history_breaks") or {}).get(m["group"]):
            # autre rupture d'historique (D-0048) : même CIK, rapports antérieurs hors du groupe
            hb = cfg["history_breaks"][m["group"]]
            mem(eid, m["group"], "none", None, "parent", rule="same_cik",
                evidence=f"company_tickers.json {cik} ; rupture d'historique le {hb['effective']} ({hb.get('kind')}) : "
                         f"avant, {hb.get('before')} (D-0048)")
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
    # autres groupes économiques non déposants (§10.4, D-0044)
    for nf in cfg.get("non_filers") or []:
        eid = f"nf:{nf['name'].lower()}"
        ent(eid, nf["name"], None, False, "non_filer", rule="config_seed",
            evidence="config.yaml non_filers (§10.4, D-0044)")
        mem(eid, nf["ref"], "none", None, "parent", rule="config_seed")
    for c in cfg.get("confirmed_entities") or []:
        eid = c.get("entity_id") or f"name:{normalize_name(c['name'])}"
        ent(eid, c["name"], c.get("cik"), bool(c.get("cik")), c.get("group_kind", "counterparty_group"),
            rule=c.get("rule", "executor_decision"), evidence=c.get("evidence"))
        mem(eid, c["group"], c.get("valid_from", "none"), c.get("valid_to"), c.get("treatment", "parent"),
            rule=c.get("rule", "executor_decision"), evidence=c.get("evidence"))
        for a in c.get("aliases") or []:
            alias(eid, a, None, None, c.get("evidence"))
    return rows
