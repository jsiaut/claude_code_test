"""Circularité (§3) : statut « financé », mesures de dépendance, conclusions par paire,
sorties de couverture (§3.6) et exposition par contrepartie (§4.6).

F(S, C, t) est une fonction pure sur les arêtes, à chaque fin de trimestre du fournisseur.
Au premier passage, les notes d'investissements ne sont pas lues : `never` est impossible et
F reste `unknown` (not_processed) tant qu'une pièce lue ne l'établit pas. L'absence n'est
jamais un zéro ; aucun seuil de ratio ne déclenche seul une conclusion.
"""
import datetime as dt
import json
from decimal import Decimal

from .graph import normalize_name
from .measures import cell

NONE = "none"
ASC280 = Decimal("0.10")
CURRENCY = "USD"
REVENUE_NATURES = {"revenue_recognized_gross", "revenue_recognized_net"}


def _d(x):
    if x in (None, "", NONE) or (isinstance(x, float) and x != x):
        return None
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])


def _kd(l):
    return _d(l["_obs"].get("knowledge_date"))


def quarter_index(quarters, d):
    for i, q in enumerate(quarters):
        if q["start"] and q["start"] <= d <= q["end"]:
            return i
    return None


class Pair:
    def __init__(self, s, c):
        self.s, self.c = s, c
        self.edges = []

    @property
    def fin(self):        # S fournit une ressource à C : financement ou contrepartie au client
        return [l for l in self.edges if l["from_group"] == self.s and l["to_group"] == self.c
                and l["family"] in ("financing", "customer_consideration")]

    @property
    def com(self):        # C achète à S
        return [l for l in self.edges if l["from_group"] == self.c and l["to_group"] == self.s
                and l["family"] == "commercial"]

    @property
    def rev_com(self):    # S achète à C
        return [l for l in self.edges if l["from_group"] == self.s and l["to_group"] == self.c
                and l["family"] == "commercial"]

    @property
    def mirror_fin(self):  # C finance S
        return [l for l in self.edges if l["from_group"] == self.c and l["to_group"] == self.s
                and l["family"] == "financing"]

    def structure(self):
        fin, com, rev = bool(self.fin), bool(self.com), bool(self.rev_com)
        if fin and com:
            return "commercial_and_financing"
        if com and rev:
            return "reciprocal_commercial"
        if fin:
            return "financing_only"
        if com or rev:
            return "commercial_only"
        return NONE


def build_pairs(edges, groups):
    """Paires (fournisseur S du périmètre, groupe client C) : C client de S, financé par S,
    ou destinataire d'une contrepartie au client ; les arêtes éliminées et les groupes
    pending (None) n'y entrent pas."""
    pairs = {}
    for l in edges:
        if l["elimination_status"] == "eliminated" or not l["from_group"] or not l["to_group"]:
            continue
        f, t = l["from_group"], l["to_group"]
        cand = []
        if l["family"] == "commercial":
            if t in groups:
                cand.append((t, f))           # f achète à t : t fournisseur
            if f in groups:
                cand.append((f, t))           # achat réciproque possible
        elif l["family"] in ("financing", "customer_consideration", "credit_support"):
            if f in groups:
                cand.append((f, t))           # S finance ou soutient C
            if t in groups and l["family"] == "financing":
                cand.append((t, f))           # miroir : C finance S
        for s, c in cand:
            if s == c:
                continue
            pairs.setdefault((s, c), Pair(s, c)).edges.append(l)
    # une paire ne vit que si C est client de S, financé par S ou reçoit une contrepartie
    keep = {}
    for k, p in pairs.items():
        if p.com or p.fin or (p.mirror_fin and p.com):
            keep[k] = p
    return keep


# -- statut « financé » --------------------------------------------------------------

def financed_events(pair):
    """Événements datés qui établissent F : (date, condition, clé, date de connaissance)."""
    ev = []
    for l in pair.fin:
        o = l["_obs"]
        d = l["_date"]
        if d is None:
            continue
        if l["family"] == "financing" and l["stage"] in ("drawn_or_paid", "recognized") \
                and l["tier"] in ("A", "B", "C") and o.get("event_type") not in ("repayment", "conversion",
                                                                                 "disposal", "termination",
                                                                                 "impairment"):
            # (b) un versement ou un prêt en numéraire, daté ; une valeur au bilan constatée à une
            # date prouve une détention (a), pas un versement des huit derniers trimestres
            holding_only = o.get("event_type") in ("recognition", "measurement_change") or \
                o.get("amount_nature") in ("investment_carrying_amount", "fair_value")
            if not holding_only:
                ev.append((d, "b", l["link_key"], _kd(l)))
            if l["tier"] in ("A", "B") and l["edge_type"] in ("equity_primary", "convertible_or_safe", "loan_or_facility",
                                                              "noncash_investment"):
                ev.append((d, "a", l["link_key"], _kd(l)))
        if l["family"] == "customer_consideration" and l["stage"] == "recognized":
            ev.append((d, "c", l["link_key"], _kd(l)))
    return sorted(ev)


def financed_status(pair, quarters, cutoff_of, lookback, censored):
    """Statut par trimestre de S : {fin de trimestre: (statut, preuves)} sous les deux politiques."""
    ev = financed_events(pair)
    ends_a = []      # fins de détention publiées (cession, conversion, remboursement, radiation)
    for l in pair.fin:
        if l["_obs"].get("event_type") in ("disposal", "conversion", "repayment", "termination") and l["_date"]:
            ends_a.append((l["_date"], l.get("instrument_key")))
    out = {"exposure_outstanding": {}, "ever_financed": {}}
    ever = False
    seen_active = False
    for i, q in enumerate(quarters):
        cut = cutoff_of(q)
        known = [e for e in ev if e[3] is None or e[3] <= cut]
        lo_i = max(0, i - lookback + 1)
        lo = quarters[lo_i]["start"] or quarters[lo_i]["end"]
        active = []
        for d, cond, key, kd in known:
            if d > q["end"]:
                continue
            if cond in ("b", "c") and d >= lo:
                active.append(key)
            if cond == "a":
                closed = any(ed <= q["end"] and ed >= d and (ed_kd is None or True) for ed, ed_kd in ends_a)
                if not closed:
                    active.append(key)
        if active:
            st = "active"
            seen_active = ever = True
        elif seen_active:
            st = "lapsed"
        else:
            st = "unknown"
        out["exposure_outstanding"][q["end"]] = (st, active)
        out["ever_financed"][q["end"]] = ("active" if ever else st, active)
    return out


def status_cell(s, c, q, view, as_of, policy, st, keys, censored):
    if st == "unknown":
        nd = "history_left_censored" if censored else "not_processed"
        return cell("financed_status", s, q["start"], q["end"], view, as_of, counterparty=c, policy=policy,
                    value_text="unknown", status="not_determinable", nd_reason=nd,
                    coverage="not_processed" if nd == "not_processed" else "unknown",
                    flags={"basis": "aucune pièce lue n'établit les conditions (a) à (c) ; notes d'investissements hors tranche"})
    return cell("financed_status", s, q["start"], q["end"], view, as_of, counterparty=c, policy=policy,
                value_text=st, status="computed", flags={"links": keys} if keys else None)


# -- mesures par paire ----------------------------------------------------------------

def names_of_group(reg, g):
    out = set()
    for r in reg.rows:
        if r["record_kind"] == "membership" and r["ref"] == g:
            e = reg.entities.get(r["entity_id"])
            if e and e.get("name"):
                out.add(e["name"])
    for r in reg.rows:
        if r["record_kind"] == "alias" and r["entity_id"] in {x["entity_id"] for x in reg.rows
                                                               if x["record_kind"] == "membership" and x["ref"] == g}:
            out.add(r["name"])
    return {n for n in out if n}


def link_pieces(pair, obs, reg, s_names, c_names):
    """Pièces L1 à L5 dont l'extrait, retrouvé mot pour mot, nomme les deux parties (§3.4).
    Le déposant se nomme lui-même par un terme défini (« the Company », « we »)."""
    out = []
    self_ref = ("the Company", "Company", "we ", "We ", "our ", "us ")
    for o in obs:
        if o["kind"] != "observation" or o["validation_state"] != "valid":
            continue
        if o.get("link_category") in (None, NONE):
            continue
        q = o.get("quote") or ""
        ql = q.lower()
        names = {normalize_name(o.get("payer") or ""), normalize_name(o.get("payee") or ""),
                 normalize_name(o.get("counterparty_name") or "")}
        s_hit = any(n.lower() in ql for n in s_names) or (o["group_id"] == pair.s and any(x in q for x in self_ref))
        c_hit = any(n.lower() in ql for n in c_names) or (o["group_id"] == pair.c and any(x in q for x in self_ref))
        involved = {normalize_name(n) for n in s_names | c_names} & names
        if s_hit and c_hit and involved:
            out.append(o)
    return out


def contract_coverage(pair, obs_by_instrument):
    known = sorted({l["instrument_key"] for l in pair.edges if l.get("instrument_key")})
    full = []
    for ik in known:
        lines = obs_by_instrument.get(ik, [])
        body = [o for o in lines if o["block_kind"] == "exhibit_body"]
        red = any(o.get("redacted") for o in lines)
        if body and not red:
            full.append(ik)
    return known, full


def revenue_attribution(pair, ps, pe, cut, active_q_ends):
    """Revenu reconnu par S venant de C (perspective du déposant S, niveau A à C), sur les
    trimestres où F est actif ; None si aucune attribution admissible."""
    vals = []
    for l in pair.com:
        o = l["_obs"]
        if o["group_id"] != pair.s or l["tier"] not in ("A", "B", "C") or l["edge_evidence"] != "amount":
            continue
        if not (o.get("amount_nature") in REVENUE_NATURES or l["edge_type"] == "revenue_recognized"):
            continue
        if l["unit"] != CURRENCY or (_kd(l) and _kd(l) > cut):
            continue
        a, b = _d(o.get("period_start")), _d(o.get("period_end"))
        if a and b and ps <= a and b <= pe and any(a <= e <= b for e in active_q_ends):
            vals.append(l)
    return vals


def anonymous_upper(conc_cells, s, fy_end):
    """Plus grande borne haute d'un client anonyme d'au moins 10 % publié pour l'exercice."""
    ups = [Decimal(str(c["value_upper"])) for c in conc_cells
           if c["subject"] == s and c["period_end"] == str(fy_end) and c.get("value_upper") is not None]
    return max(ups) if ups else None


def fiscal_years(quarters, ws, as_of_d):
    """Exercices clos de la fenêtre : (début, fin, trimestres)."""
    by = {}
    for q in quarters:
        if q["fy_end"] and q["fy_end"] <= as_of_d and q["end"] >= ws:
            by.setdefault(q["fy_end"], []).append(q)
    out = []
    for fe, qs in sorted(by.items()):
        if qs[0]["start"] is None or qs[-1]["end"] != fe:
            continue
        out.append((qs[0]["start"], fe, qs))
    return out


def pair_measures(pairs, cals, groups_window, revenue, conc_cells, named_conc, obs, reg, as_of, deadlines,
                  report_dates, lookback, censored_groups):
    """Cellules de §3 par paire, et les éléments de l'annexe E (renvoyés à part)."""
    as_of_d = dt.date.fromisoformat(as_of)
    out, ev = [], {}
    obs_by_instrument = {}
    for o in obs:
        if o.get("instrument_key") and o["validation_state"] == "valid":
            obs_by_instrument.setdefault(o["instrument_key"], []).append(o)
    for (s, c), p in sorted(pairs.items()):
        cal = cals[s]
        qs_all = [q for q in cal["quarters"] if q["end"] <= as_of_d and q["start"]]
        ext = groups_window[s]["extended_start"]
        qs = [q for q in qs_all if q["end"] >= ext - dt.timedelta(days=1)]
        censored = s in censored_groups

        def cut_known(q):
            return report_dates.get((s, q["end"])) or as_of_d
        F = {}
        for view, cutf in (("as_known", cut_known), ("revised", lambda q: as_of_d)):
            st = financed_status(p, qs_all, cutf, lookback, censored)
            F[view] = st
            for policy in ("exposure_outstanding", "ever_financed"):
                for q in qs:
                    v, keys = st[policy][q["end"]]
                    out.append(status_cell(s, c, q, view, as_of, policy, v, keys, censored))
        s_names = names_of_group(reg, s)
        c_names = names_of_group(reg, c) | {l["_obs"].get("counterparty_name") for l in p.edges
                                            if l["_obs"].get("counterparty_name")}
        pieces = link_pieces(p, obs, reg, s_names, {n for n in c_names if n})
        structure = p.structure()
        linkage = "documented_link" if pieces else "search_incomplete"
        if linkage == "documented_link" and structure == "commercial_and_financing":
            concl = "documented_dependency"
        elif structure == "commercial_and_financing":
            concl = "commercial_with_financing"
        elif structure == "reciprocal_commercial":
            concl = "reciprocal_commercial_only"
        else:
            concl = "causality_not_established"
        win_start = groups_window[s]["window_start"]
        out.append(cell("relationship_conclusion", s, win_start, as_of_d, "as_known", as_of, counterparty=c,
                        value_text=concl, status="computed",
                        flags={"edge_structure": structure, "linkage_evidence": linkage,
                               "link_pieces": sorted({o["obs_key"] for o in pieces}),
                               "link_categories": sorted({o["link_category"] for o in pieces}),
                               "edges": sorted(l["link_key"] for l in p.edges)}))
        known, full = contract_coverage(p, obs_by_instrument)
        if known:
            v = Decimal(len(full)) / Decimal(len(known))
            out.append(cell("contract_coverage", s, win_start, as_of_d, "as_known", as_of, counterparty=c,
                            value=v, numerator=len(full), denominator=len(known), unit="pure",
                            flags={"agreements": known, "filed_in_full_unredacted": full}))
        else:
            out.append(cell("contract_coverage", s, win_start, as_of_d, "as_known", as_of, counterparty=c,
                            status="not_determinable", nd_reason="not_disclosed",
                            flags={"basis": "aucun accord identifié par une clé d'instrument"}))
        ev[(s, c)] = {"pair": p, "pieces": pieces, "structure": structure, "linkage": linkage,
                      "conclusion": concl, "F": F, "years": {}, "contract": (known, full)}
        # mesures par exercice du fournisseur
        for fs, fe, fqs in fiscal_years(cal["quarters"], groups_window[s]["window_start"], as_of_d):
            for view in ("as_known", "revised"):
                cut = min(deadlines[s](fe), as_of_d) if view == "as_known" else as_of_d
                cell_as_of = cut.isoformat() if view == "as_known" else as_of
                stq = {q["end"]: F[view]["exposure_outstanding"].get(q["end"], ("unknown", []))[0] for q in fqs}
                active = [e for e, v in stq.items() if v == "active"]
                rev, rterms = revenue(s, fs, fe, cut)
                cells = dependency_cells(p, s, c, fs, fe, view, cell_as_of, cut, stq, active, rev, rterms,
                                         conc_cells, named_conc, censored)
                out += cells
                if view == "as_known":
                    ev[(s, c)]["years"][fe] = {c_["measure"]: c_ for c_ in cells}
    return out, ev


def dependency_cells(p, s, c, fs, fe, view, as_of, cut, stq, active, rev, rterms, conc_cells, named_conc,
                     censored):
    out = []
    flags_q = {"quarters": {str(k): v for k, v in sorted(stq.items())}}
    # documented_revenue_dependency (§3.3) : ratio des sommes, revenu attribué par S
    if not active:
        nd = "history_left_censored" if censored else "not_processed"
        if all(v == "lapsed" for v in stq.values()):
            nd = "not_processed"   # (a) non exclue tant que les notes d'investissements ne sont pas lues
        out.append(cell("documented_revenue_dependency", s, fs, fe, view, as_of, counterparty=c,
                        policy="exposure_outstanding", status="not_determinable", nd_reason=nd,
                        flags=dict(flags_q, basis="F jamais active sur l'exercice")))
    elif rev is None:
        out.append(cell("documented_revenue_dependency", s, fs, fe, view, as_of, counterparty=c,
                        policy="exposure_outstanding", status="not_determinable", nd_reason="term_missing",
                        flags=flags_q))
    else:
        attr = revenue_attribution(p, fs, fe, cut, active)
        named = [n for n in named_conc if n["group_id"] == s and str(n["period_end"]) == str(fe)
                 and normalize_name(c.split(":", 1)[-1]) in normalize_name(n["member"])]
        if attr:
            num = sum(Decimal(str(l["amount"])) for l in attr if not l.get("_dup_of"))
            out.append(cell("documented_revenue_dependency", s, fs, fe, view, as_of, counterparty=c,
                            policy="exposure_outstanding", value=num / rev, numerator=num, denominator=rev,
                            unit="pure", terms=rterms, status="computed" if len(active) == len(stq) else "partial",
                            nd_reason=None if len(active) == len(stq) else "not_processed",
                            flags=dict(flags_q, links=[l["link_key"] for l in attr])))
        else:
            up = anonymous_upper(conc_cells, s, fe)
            upper = max(ASC280, up) if up is not None else ASC280
            fl = dict(flags_q, upper_exclusive=(up is None or up < ASC280),
                      hypothesis="publication des clients d'au moins 10 % conforme à ASC 280-10-50-42",
                      anonymous_major_customer_upper=float(up) if up is not None else None,
                      named_concentration=[n["fact_key"] for n in named])
            out.append(cell("documented_revenue_dependency", s, fs, fe, view, as_of, counterparty=c,
                            policy="exposure_outstanding", status="bounded", lower=Decimal(0), upper=upper,
                            bound_basis="asc280_major_customer_completeness", denominator=rev, terms=rterms,
                            unit="pure", flags=fl))
    # investor_customer_revenue_share (miroir) : clients qui financent S
    if p.mirror_fin and p.com:
        out.append(cell("investor_customer_revenue_share", s, fs, fe, view, as_of, counterparty=c,
                        policy="exposure_outstanding", status="not_determinable", nd_reason="anonymous",
                        flags={"basis": "aucun revenu de ce client attribué par S au niveau A à C",
                               "mirror_links": [l["link_key"] for l in p.mirror_fin]}))
    # contrepartie au client et revenu contre titres (§3.3, E.5)
    cc = [l for l in p.fin if l["family"] == "customer_consideration"]
    if cc:
        rec = [l for l in cc if l["stage"] == "recognized" and l["unit"] == CURRENCY and l["edge_evidence"] == "amount"
               and _d(l["_obs"].get("period_end")) and fs <= _d(l["_obs"]["period_end"]) <= fe]
        if rec:
            v = sum(Decimal(str(l["amount"])) for l in rec)
            out.append(cell("consideration_to_customer", s, fs, fe, view, as_of, counterparty=c, value=v, unit="USD",
                            flags={"links": [l["link_key"] for l in rec]}))
        else:
            out.append(cell("consideration_to_customer", s, fs, fe, view, as_of, counterparty=c,
                            status="not_determinable", nd_reason="not_processed",
                            flags={"basis": "bons ou crédits remis au client publiés ; montant comptabilisé dans les notes hors tranche",
                                   "links": [l["link_key"] for l in cc]}))
    if active:
        out.append(cell("noncash_revenue_from_investees", s, fs, fe, view, as_of, counterparty=c,
                        status="not_determinable", nd_reason="not_processed",
                        flags={"basis": "revenu contre titres reçus (ASC 606-10-32-21) : notes de revenu hors tranche"}))
        for term in ("total", "beyond_12m"):
            out.append(cell("documented_backlog_dependency", s, None, fe, view, as_of, counterparty=c, term=term,
                            policy="exposure_outstanding", status="not_determinable", nd_reason="anonymous",
                            flags={"basis": "aucun RPO attribué par S à ce client au niveau A à C"}))
    return out


# -- sorties de couverture (§3.6) ------------------------------------------------------

def coverage_cells(groups, cals, groups_window, revenue, conc_cells, named_conc, pairs, edges, as_of, ev):
    as_of_d = dt.date.fromisoformat(as_of)
    out = []
    for s in groups:
        cal = cals[s]
        combos = {}
        for fs, fe, fqs in fiscal_years(cal["quarters"], groups_window[s]["window_start"], as_of_d):
            rev, rterms = revenue(s, fs, fe, as_of_d)
            named = [n for n in named_conc if n["group_id"] == s and str(n["period_end"]) == str(fe)]
            anon = [c for c in conc_cells if c["subject"] == s and c["period_end"] == str(fe)]
            # revenu attribué par S à des clients nommés (pièces lues, niveau A à C)
            attr = [l for l in edges if l["to_group"] == s and l["family"] == "commercial"
                    and l["_obs"]["group_id"] == s and l["tier"] in ("A", "B", "C") and l["edge_evidence"] == "amount"
                    and l["unit"] == CURRENCY and (l["_obs"].get("amount_nature") in REVENUE_NATURES
                                                   or l["edge_type"] == "revenue_recognized")
                    and _d(l["_obs"].get("period_end")) and fs <= _d(l["_obs"]["period_end"]) <= fe]
            if rev is None:
                for term in ("named", "anonymous", "residual"):
                    out.append(cell("named_edge_coverage", s, fs, fe, "as_known", as_of, term=term,
                                    status="not_determinable", nd_reason="term_missing"))
                continue
            n_lo = sum((Decimal(str(n["value"])) for n in named), Decimal(0))
            n_val = n_lo + sum((Decimal(str(l["amount"])) / rev for l in attr), Decimal(0))
            a_val = sum((Decimal(str(c["value"])) for c in anon), Decimal(0))
            a_lo = sum((Decimal(str(c["value_lower"])) for c in anon), Decimal(0))
            a_hi = sum((Decimal(str(c["value_upper"])) for c in anon), Decimal(0))
            fl = {"overlap_possible": True, "named_concentration": [n["fact_key"] for n in named],
                  "attributed_links": [l["link_key"] for l in attr],
                  "anonymous_cells": [c["breakdown_key"] for c in anon],
                  "basis": "texte autour des faits de concentration hors tranche (§11.1)"}
            out.append(cell("named_edge_coverage", s, fs, fe, "as_known", as_of, term="named", value=n_val,
                            status="partial", nd_reason="not_processed", unit="pure", terms=rterms, flags=fl))
            out.append(cell("named_edge_coverage", s, fs, fe, "as_known", as_of, term="anonymous", value=a_val,
                            lower=a_lo, upper=a_hi, bound_basis="rounding" if anon else None,
                            status="bounded" if anon else "computed", unit="pure", flags=fl))
            out.append(cell("named_edge_coverage", s, fs, fe, "as_known", as_of, term="residual",
                            value=Decimal(1) - n_val - a_val, lower=Decimal(1) - n_val - a_hi,
                            upper=Decimal(1) - n_val - a_lo, bound_basis="rounding" if anon else None,
                            status="partial", nd_reason="not_processed", unit="pure", flags=fl))
            # paires vues seulement côté client (jamais converties en revenu)
            vis = set()
            for (ss, c), p in pairs.items():
                if ss != s:
                    continue
                docs = {l["_obs"]["group_id"] for l in p.edges if l["_date"] and l["_date"] <= fe}
                if docs and s not in docs:
                    vis.add(c)
            out.append(cell("visible_pairs_count", s, fs, fe, "as_known", as_of, value=len(vis), unit="count",
                            flags={"pairs": sorted(vis)} if vis else None))
        # couverture des paires à financement documenté
        for (ss, c), e in ev.items():
            if ss != s:
                continue
            if not any(v[0] == "active" for v in e["F"]["as_known"]["exposure_outstanding"].values()):
                continue
            yrs = e["years"]
            num_states, den_states = [], []
            for fe, cells in yrs.items():
                d = cells.get("documented_revenue_dependency")
                if d is None:
                    continue
                if d["status"] == "computed":
                    num_states.append("complete")
                elif d["status"] == "partial":
                    num_states.append("partial")
                else:
                    num_states.append("absent")
                den_states.append("complete" if d.get("denominator") is not None else "absent")
            def agg(st):
                if not st:
                    return "absent"
                if all(x == "complete" for x in st):
                    return "complete"
                if all(x == "absent" for x in st):
                    return "absent"
                return "partial"
            ns, ds = agg(num_states), agg(den_states)
            combos[(ns, ds)] = combos.get((ns, ds), 0) + 1
            ws = groups_window[s]["window_start"]
            out.append(cell("documented_pair_coverage", s, ws, as_of_d, "as_known", as_of, counterparty=c,
                            term="numerator", value_text=ns, status="computed"))
            out.append(cell("documented_pair_coverage", s, ws, as_of_d, "as_known", as_of, counterparty=c,
                            term="denominator", value_text=ds, status="computed"))
        ws = groups_window[s]["window_start"]
        allc = {f"{a}/{b}": combos.get((a, b), 0) for a in ("complete", "partial", "absent")
                for b in ("complete", "partial", "absent")}
        out.append(cell("documented_pair_coverage", s, ws, as_of_d, "as_known", as_of, term="combinations",
                        value=sum(allc.values()), unit="count", flags={"combinations": allc}))
    return out


def counterparty_exposure(pairs, ev, cals, as_of):
    """Une ligne par bloc et par base, sans total (§4.6), avec wrong_way."""
    as_of_d = dt.date.fromisoformat(as_of)
    out = []
    for (s, c), p in sorted(pairs.items()):
        qs = [q for q in cals[s]["quarters"] if q["end"] <= as_of_d]
        t = qs[-1]["end"] if qs else as_of_d
        ever_active = any(v[0] == "active" for v in ev[(s, c)]["F"]["as_known"]["exposure_outstanding"].values())
        wrong_way = bool(ever_active and p.com)
        lines = {}
        for l in p.fin + [x for x in p.edges if x["from_group"] == s and x["to_group"] == c
                          and x["family"] == "credit_support"]:
            o = l["_obs"]
            if o.get("amount") is None or o.get("unit") != CURRENCY or l.get("_dup_of"):
                continue
            if l["_date"] and l["_date"] > t:
                continue
            if l["family"] == "financing" and l["edge_evidence"] == "amount" and o.get("event_type") not in ("repayment", "conversion"):
                key = ("exposed_assets", "cost", "equity_investment") if l["edge_type"] in ("equity_primary", "convertible_or_safe") \
                    else ("exposed_assets", "principal", "loan_receivable")
            elif l["family"] == "financing" and (o.get("amount_nature") == "commitment_unexecuted"
                                                 or o.get("measurement_basis") == "commitment_cap"):
                key = ("contractual_outflows", "commitment_cap", o.get("category_id") or "uncalled_commitment")
            elif l["family"] == "credit_support":
                key = ("contingent_obligations", o.get("measurement_basis") or "commitment_cap", o.get("category_id") or "guarantee")
            else:
                continue
            lines.setdefault(key, []).append(l)
        if not lines:
            out.append(cell("counterparty_exposure", s, None, t, "as_known", as_of, counterparty=c,
                            status="not_determinable", nd_reason="not_processed",
                            flags={"wrong_way": wrong_way, "basis": "aucun montant d'exposition lu ; notes d'investissements hors tranche"}))
            continue
        for (blk, basis, cat), ls in sorted(lines.items()):
            v = sum(Decimal(str(l["_obs"]["amount"])) for l in ls)
            tiers = {}
            for l in ls:
                tiers[l["tier"]] = tiers.get(l["tier"], Decimal(0)) + Decimal(str(l["_obs"]["amount"])) / v if v else Decimal(0)
            out.append(cell("counterparty_exposure", s, None, t, "as_known", as_of, counterparty=c,
                            breakdown=f"{blk}/{basis}/{cat}", value=v, unit="USD", status="partial",
                            nd_reason="not_processed",
                            flags={"wrong_way": wrong_way, "links": [l["link_key"] for l in ls],
                                   "evidence_profile": {k: float(round(x, 4)) for k, x in tiers.items()}}))
    return out
