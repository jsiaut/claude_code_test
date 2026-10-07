"""Table links : arêtes du graphe (§3.1) et relations entre montants (§8.1, §8.2).

Une arête est orientée de la partie qui fournit la ressource vers celle qui la reçoit
(payer → payee, D-0015). Arête `amount` seulement si le montant est admissible, la
contrepartie nommée ou dérivable et la période connue ; un financement ne se documente
qu'au niveau A à C et au stade drawn_or_paid ou recognized, un contrat prouvant un plafond,
pas un versement. Les relations entre montants se posent par règle à l'intérieur d'un même
instrument ; les paires non additives du registre engendrent leurs relations candidates.
"""
import datetime as dt
import hashlib
import json
from decimal import Decimal

from . import entities as E
from .graph import normalize_name

CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CNY", "TWD", "KRW", "INR", "CAD", "AUD", "SGD", "CHF"}
FIN_STAGES = {"drawn_or_paid", "recognized"}
NONE = "none"


def _d(x):
    if x in (None, "", NONE) or (isinstance(x, float) and x != x):
        return None
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])


def _key(*parts):
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


def edge_date(o):
    return _d(o.get("event_date")) or _d(o.get("period_end")) or _d(o.get("knowledge_date"))


def counterparty_names(obs):
    """Noms à résoudre : contreparties, payeurs et receveurs des observations valides."""
    out = {}
    for o in obs:
        if o["kind"] != "observation" or o["validation_state"] != "valid":
            continue
        for k in ("counterparty_name", "payer", "payee"):
            if o.get(k):
                fin = o.get("party_is_financial_institution") if k == "counterparty_name" else None
                if o[k] not in out or (fin is not None and out[o[k]] is None):
                    out[o[k]] = fin
    return out


def build_edges(obs, reg):
    links, pend = [], set()
    for o in obs:
        if o["kind"] != "observation" or o["validation_state"] != "valid":
            continue
        if o.get("family") in (None, NONE) or o.get("edge_type") in (None, NONE):
            continue
        if o.get("counterparty_evidence") not in ("named", "derivable"):
            continue
        payer, payee = o.get("payer"), o.get("payee")
        cp = o.get("counterparty_name")
        # un côté manquant est la contrepartie nommée (D-0015)
        if not payer and payee and cp and normalize_name(cp) != normalize_name(payee):
            payer = cp
        if not payee and payer and cp and normalize_name(cp) != normalize_name(payer):
            payee = cp
        d = edge_date(o)
        fe, fg, fs = E.resolve(reg, payer, d, "as_known")
        te, tg, ts = E.resolve(reg, payee, d, "as_known")
        fg_r = E.resolve(reg, payer, d, "revised")[1]
        tg_r = E.resolve(reg, payee, d, "revised")[1]
        for e, s in ((fe, fs), (te, ts)):
            if e and s in ("pending", "unknown"):
                pend.add(e)
        amount = o.get("amount")
        unit = o.get("unit")
        tier = o.get("tier")
        admissible = (amount is not None and o.get("amount_nature") != "management_estimate"
                      and o.get("stage") not in (None, NONE, "intent_non_binding") and d is not None
                      and tier in ("A", "B", "C", "D") and o.get("amount_qualifier") != "range")
        if o["family"] == "financing":
            admissible = admissible and tier in ("A", "B", "C") and o.get("stage") in FIN_STAGES
        if fg is None or tg is None:
            elim = "unknown"
        elif fg == tg and fg_r == tg_r:
            elim = "eliminated"
        elif fg != tg and fg_r != tg_r:
            elim = "not_applicable"
        else:
            elim = "unknown"       # dépend de la vue (contrôle commun, §10.3)
        perspective = "reporting_entity" if o["group_id"] in (fg, tg, fg_r, tg_r) else "counterparty"
        links.append({
            "link_key": "edge:" + o["obs_key"], "link_kind": "edge", "family": o["family"],
            "edge_type": o["edge_type"], "edge_evidence": "amount" if admissible else "relation",
            "advance": o["edge_type"] == "prepayment", "reciprocal_purchase": None,
            "from_entity": fe, "to_entity": te, "from_group": fg, "to_group": tg,
            "amount": amount if admissible else None, "unit": unit if admissible else None,
            "currency": o.get("currency") if admissible else None,
            "amount_nature": o.get("amount_nature"), "stage": o.get("stage"),
            "period_start": o.get("period_start"), "period_end": o.get("period_end"),
            "event_date": o.get("event_date"), "relation_type": NONE, "a_key": None, "b_key": None,
            "allocation": None, "pair_id": None, "resolution": NONE, "resolution_ref": None,
            "instrument_key": o.get("instrument_key"), "evidence_keys": json.dumps([o["obs_key"]]),
            "tier": tier, "filing_status": o.get("filing_status"), "source_perspective": perspective,
            "knowledge_date": o.get("knowledge_date"), "elimination_status": elim,
            # attributs de travail, retirés à l'export
            "_obs": o, "_date": d, "_from_group_revised": fg_r, "_to_group_revised": tg_r,
        })
    # achats réciproques : deux arêtes commerciales opposées entre deux groupes (§3.1)
    pairs = {(l["from_group"], l["to_group"]) for l in links if l["family"] == "commercial"
             and l["from_group"] and l["to_group"] and l["from_group"] != l["to_group"]}
    for l in links:
        if l["family"] == "commercial" and l["from_group"] and l["to_group"]:
            l["reciprocal_purchase"] = (l["to_group"], l["from_group"]) in pairs
    return links, pend


def relation(a, b, rtype, pair_id, resolution, ref, allocation=None, instrument=None):
    return {"link_key": "rel:" + _key(a, b, rtype, pair_id), "link_kind": "relation_between_amounts",
            "family": NONE, "edge_type": NONE, "edge_evidence": NONE, "advance": None,
            "reciprocal_purchase": None, "from_entity": None, "to_entity": None, "from_group": None,
            "to_group": None, "amount": None, "unit": None, "currency": None, "amount_nature": NONE,
            "stage": NONE, "period_start": None, "period_end": None, "event_date": None,
            "relation_type": rtype, "a_key": a, "b_key": b, "allocation": allocation, "pair_id": pair_id,
            "resolution": resolution, "resolution_ref": ref, "instrument_key": instrument,
            "evidence_keys": None, "tier": None, "filing_status": None, "source_perspective": NONE,
            "knowledge_date": None, "elimination_status": "not_applicable"}


def instrument_relations(edges):
    """Relations posées par règle dans un même instrument : doublon d'un même montant au
    même stade (same_measure), tirage dans un engagement (component_of, na03)."""
    out = []
    by = {}
    for l in edges:
        if l["edge_evidence"] == "amount" and l.get("instrument_key") and l["unit"] in CURRENCIES:
            by.setdefault((l["instrument_key"], l["unit"]), []).append(l)
    for (ik, unit), ls in by.items():
        ls = sorted(ls, key=lambda x: (x["_date"], x["link_key"]))
        seen = []
        for l in ls:
            dup = next((s for s in seen if Decimal(str(s["amount"])) == Decimal(str(l["amount"]))
                        and s["stage"] == l["stage"] and abs((s["_date"] - l["_date"]).days) <= 45
                        and s["_obs"].get("event_type") == l["_obs"].get("event_type")), None)
            if dup:
                out.append(relation(dup["link_key"], l["link_key"], "same_measure", None, "resolved_rule",
                                    "même instrument, même montant, même stade et même événement à 45 jours près",
                                    instrument=ik))
                l["_dup_of"] = dup["link_key"]
            else:
                seen.append(l)
        caps = [l for l in ls if l["_obs"].get("measurement_basis") == "commitment_cap"]
        drawn = [l for l in ls if l["stage"] == "drawn_or_paid" and l["_obs"].get("measurement_basis") != "commitment_cap"]
        for c in caps:
            for d in drawn:
                out.append(relation(d["link_key"], c["link_key"], "component_of", "na03", "resolved_rule",
                                    "na03 : le reste étant le non-tiré (Reg S-X 5-02.19(b), 5-02.22(b))", instrument=ik))
    return out


def _match(sel, row):
    for k, v in sel.items():
        if k in ("side",):
            continue
        rv = row.get(k)
        if isinstance(v, list):
            if rv not in v:
                return False
        elif isinstance(v, bool):
            if rv is not v:
                return False
        elif rv != v:
            return False
    return True


def pair_candidates(pairs_cfg, amount_rows):
    """Relations candidates des paires non additives (§8.2) : toutes les lignes qui
    s'apparient (même groupe, date ou instrument). Le compte par paire va dans delta.md."""
    out, counts = [], {}
    for p in pairs_cfg:
        a_rows = [r for r in amount_rows if _match(p["a"], r)]
        b_rows = [r for r in amount_rows if _match(p["b"], r)]
        n = 0
        for a in a_rows:
            for b in b_rows:
                if a["key"] == b["key"]:
                    continue
                ok = True
                for m in p.get("match") or []:
                    if m == "same_group" and a.get("group") != b.get("group"):
                        ok = False
                    elif m == "same_date" and a.get("date") != b.get("date"):
                        ok = False
                    elif m in ("same_instrument", "same_agreement") and (not a.get("instrument_key")
                                                                       or a.get("instrument_key") != b.get("instrument_key")):
                        ok = False
                    elif m == "same_counterparty" and a.get("counterparty_group") != b.get("counterparty_group"):
                        ok = False
                    elif m == "same_lease_type" and a.get("lease_type") != b.get("lease_type"):
                        ok = False
                if not ok:
                    continue
                d = p["default"]
                rtype = d["relation_type"]
                resolved = "resolved_rule" if rtype in ("component_of", "covers", "eliminated_with", "same_measure") \
                    and not d.get("condition") else "unresolved"
                out.append(relation(a["key"], b["key"], rtype, p["id"], resolved,
                                    d.get("rule") or d.get("condition"), instrument=a.get("instrument_key")))
                n += 1
        counts[p["id"]] = n
    return out, counts
