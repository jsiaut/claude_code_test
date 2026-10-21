"""Volets 8 et 9 de D-0067 : clauses des contrats, capacités et événements propres aux laboratoires.

Trois mesures de rang 2 (§14), sans total ni score :
- lab_contract_clause : une cellule par ligne de clause qui concerne un laboratoire ;
- lab_capacity : une cellule par ligne de capacité qui concerne un laboratoire, valeur et unité telles qu'écrites,
  jamais additionnées ni converties ;
- lab_event : par laboratoire, événement (L1 à L5) et trimestre civil, de 2021 T1 au dernier trimestre clos avant
  l'as_of. Ce n'est pas l'annexe F, liste fermée : ces cellules n'entrent dans aucune autre mesure.

Une ligne concerne un laboratoire si sa contrepartie, son payeur ou son bénéficiaire se résout en laboratoire, ou si sa
citation le nomme (D-0067, point 7). La cellule va du déclarant (sujet) au laboratoire (contrepartie), comme le grand
livre (D-0060, point 6).
"""
import datetime as dt
import re
from collections import defaultdict
from decimal import Decimal

from . import entities as E
from .measures import cell
from .registry import NONE

LAB_RX = {"LAB:OPENAI": re.compile(r"\bOpenAI\b|\bOPENAI\b"),
          "LAB:ANTHROPIC": re.compile(r"\bAnthropic\b(?! Capital)|\bANTHROPIC\b(?! CAPITAL)")}
LABS = tuple(LAB_RX)
START = dt.date(2021, 1, 1)                 # fenêtre du modèle : premier exercice clos en 2021 (D-0067, point 7)
EVENTS = {"L1": "commitment_reduction", "L2": "exclusivity_end", "L5": "site_delay"}
FIELDS = ("clause_kind", "instrument_key", "conditionality", "trigger_description", "trigger_occurred", "redacted",
          "event_type", "stage", "event_date", "period_start", "period_end", "period_label", "accession", "form",
          "exhibit_type", "capacity_kind", "capacity_qualifier", "amount_qualifier", "counterparty_name", "signal",
          "signal_present", "note")


def _d(x):
    if x in (None, "", NONE) or (isinstance(x, float) and x != x):
        return None
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def _txt(x):
    return None if x in (None, "", NONE) or (isinstance(x, float) and x != x) else x


def line_date(o):
    """Date d'une ligne et sa base : date d'événement, sinon fin de période, sinon date de la pièce."""
    for k, basis in (("event_date", "event"), ("period_end", "period"), ("knowledge_date", "knowledge")):
        if _d(o.get(k)):
            return _d(o.get(k)), basis
    return None, None


def labs_of(o, reg):
    """Laboratoires que concerne une ligne : contrepartie, payeur ou bénéficiaire résolus en laboratoire, ou nommés
    par la citation (D-0067, point 7)."""
    d, _ = line_date(o)
    out = set()
    for k in ("counterparty_name", "payer", "payee"):
        g = E.resolve(reg, _txt(o.get(k)), d)[1] if _txt(o.get(k)) else None
        if g in LABS:
            out.add(g)
    q = o.get("quote") or ""
    out |= {lab for lab, rx in LAB_RX.items() if rx.search(q)}
    return sorted(out)


def _term(o, value):
    return {"fact_key": "obs:" + o["obs_key"], "value": str(abs(Decimal(str(value)))) if value is not None else "1",
            "tier": o.get("tier"), "knowledge_date": o.get("knowledge_date"), "is_tagged": False}


def _flags(o, date_basis):
    fl = {k: _txt(o.get(k)) for k in FIELDS}
    fl["date_basis"] = date_basis
    fl["filer"] = o.get("group_id")
    return {k: (str(v) if isinstance(v, (dt.date, Decimal)) else v) for k, v in fl.items() if v not in (None, "")}


def clause_cells(obs, reg, as_of):
    """lab_contract_clause : une cellule par ligne de clause qui concerne un laboratoire ; valeur : le montant écrit,
    sinon la capacité écrite, sinon aucune (le genre de clause en texte)."""
    out = []
    for o in obs:
        ck = _txt(o.get("clause_kind"))
        if o.get("kind") != "observation" or ck is None:
            continue
        d, basis = line_date(o)
        for lab in labs_of(o, reg):
            if o.get("amount") is not None:
                value, unit = Decimal(str(o["amount"])), o.get("unit")
            elif o.get("capacity_value") is not None:
                value, unit = Decimal(str(o["capacity_value"])), o.get("capacity_unit")
            else:
                value, unit = None, None
            bk = "|".join((ck, _txt(o.get("instrument_key")) or NONE, o["obs_key"]))
            out.append(cell("lab_contract_clause", o.get("group_id") or NONE, _d(o.get("period_start")), d, "as_known",
                            as_of, breakdown=bk, value=value, unit=unit, value_text=None if value is not None else ck,
                            counterparty=lab, terms=[_term(o, value)], knowledge_date=o.get("knowledge_date"),
                            flags=_flags(o, basis)))
    return out


def capacity_cells(obs, reg, as_of):
    """lab_capacity : une cellule par ligne de capacité qui concerne un laboratoire, telle qu'écrite."""
    out = []
    for o in obs:
        if o.get("kind") != "observation" or o.get("capacity_value") is None:
            continue
        d, basis = line_date(o)
        for lab in labs_of(o, reg):
            v = Decimal(str(o["capacity_value"]))
            bk = "|".join((_txt(o.get("capacity_kind")) or NONE, _txt(o.get("instrument_key")) or NONE, o["obs_key"]))
            out.append(cell("lab_capacity", o.get("group_id") or NONE, _d(o.get("period_start")), d, "as_known", as_of,
                            breakdown=bk, value=v, unit=o.get("capacity_unit"), counterparty=lab, terms=[_term(o, v)],
                            knowledge_date=o.get("knowledge_date"), flags=_flags(o, basis)))
    return out


def quarters(as_of):
    """Trimestres civils de 2021 T1 au dernier trimestre clos à l'as_of."""
    out, y, q = [], START.year, 1
    while True:
        s = dt.date(y, 3 * q - 2, 1)
        e = (dt.date(y + (q == 4), 1 if q == 4 else 3 * q + 1, 1) - dt.timedelta(days=1))
        if e > as_of:
            return out
        out.append((s, e))
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)


def mark_decreases(marks):
    """Baisses de marque (L3) : pour chaque laboratoire, fonds et titre, une valeur par action inférieure à celle de la
    date précédente de la même série ; avec chaque marque qui a une date précédente."""
    series = defaultdict(list)
    for c in marks:
        if c.get("measure") != "nport_equity_mark" or c.get("view") != "as_known" or c.get("subject") not in LABS \
                or c.get("value") is None:
            continue
        series[(c["subject"], c["counterparty"], c["breakdown_key"])].append(c)
    compared, down = [], []
    for k, cs in series.items():
        cs = sorted(cs, key=lambda c: str(c["period_end"]))
        for prev, cur in zip(cs, cs[1:]):
            rec = {"lab": k[0], "fund": k[1], "title": k[2], "date": str(cur["period_end"])[:10],
                   "previous_date": str(prev["period_end"])[:10], "value": str(cur["value"]),
                   "previous": str(prev["value"]), "knowledge_date": str(cur.get("knowledge_date") or "")[:10] or None}
            compared.append(rec)
            if Decimal(str(cur["value"])) < Decimal(str(prev["value"])):
                down.append(rec)
    first = {(k[0], str(c["period_end"])[:10]) for k, cs in series.items() for c in cs}
    return compared, down, first


def event_lines(obs, reg):
    """Lignes d'événement par laboratoire et par identifiant (L1, L2, L3, L4, L5), avec leur date."""
    out = defaultdict(list)
    for o in obs:
        if o.get("kind") != "observation":
            continue
        sig, present = _txt(o.get("signal")), o.get("signal_present")
        ids = []
        for lid, s in EVENTS.items():
            if sig == s and present is True:
                ids.append(lid)
        if sig == "mark_down" and present is True:
            ids.append("L3")
        if (sig == "guarantee_call" and present is True) or (o.get("family") == "credit_support"
                                                              and o.get("trigger_occurred") == "yes"):
            ids.append("L4")
        if not ids:
            continue
        d, basis = line_date(o)
        for lab in labs_of(o, reg):
            for lid in ids:
                out[(lab, lid)].append((d, basis, o))
    return out


def event_cells(obs, reg, marks, as_of):
    """lab_event : une cellule par laboratoire, événement et trimestre (D-0067, point 7)."""
    as_of_d = _d(as_of)
    lines = event_lines(obs, reg)
    compared, down, first = mark_decreases(marks)
    out = []
    for lab in LABS:
        for lid in ("L1", "L2", "L3", "L4", "L5"):
            for s, e in quarters(as_of_d):
                hits = [(d, b, o) for d, b, o in lines.get((lab, lid), []) if d is not None and s <= d <= e]
                obs_keys = sorted(o["obs_key"] for _, _, o in hits)
                terms = [_term(o, None) for _, _, o in hits]
                flags = {"observations": obs_keys} if obs_keys else {}
                if hits:
                    flags["date_basis"] = sorted({b for _, b, _ in hits})
                    flags["accessions"] = sorted({o.get("accession") for _, _, o in hits if o.get("accession")})
                kd = min((str(o.get("knowledge_date")) for _, _, o in hits if o.get("knowledge_date")), default=None)
                if lid == "L3":
                    cmp_q = [r for r in compared if r["lab"] == lab and s <= _d(r["date"]) <= e]
                    dn = [r for r in down if r["lab"] == lab and s <= _d(r["date"]) <= e]
                    if dn:
                        flags["marks"] = dn
                        kd = min([kd] + [r["knowledge_date"] for r in dn if r["knowledge_date"]], key=lambda x: x or "9")
                    if hits or dn:
                        out.append(cell("lab_event", lab, s, e, "as_known", as_of, breakdown=lid, value_text="event",
                                        terms=terms, knowledge_date=kd, flags=flags))
                    elif cmp_q:
                        out.append(cell("lab_event", lab, s, e, "as_known", as_of, breakdown=lid, value_text="no_event",
                                        flags={"marks_compared": len(cmp_q)}))
                    else:
                        any_mark = any(l == lab and s <= _d(p) <= e for l, p in first)
                        nd = "prior_period_missing" if any_mark else "not_disclosed"
                        out.append(cell("lab_event", lab, s, e, "as_known", as_of, breakdown=lid, status="not_determinable",
                                        nd_reason=nd, coverage="not_disclosed" if nd == "not_disclosed" else "observed"))
                    continue
                if hits:
                    out.append(cell("lab_event", lab, s, e, "as_known", as_of, breakdown=lid, value_text="event",
                                    terms=terms, knowledge_date=kd, flags=flags))
                else:
                    out.append(cell("lab_event", lab, s, e, "as_known", as_of, breakdown=lid, status="not_determinable",
                                    nd_reason="not_processed", coverage="not_processed"))
    return out


def cells(obs, reg, marks, as_of):
    """Les trois mesures de D-0067 (volets 8 et 9)."""
    return clause_cells(obs, reg, as_of) + capacity_cells(obs, reg, as_of) + event_cells(obs, reg, marks, as_of)
