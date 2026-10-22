"""D-0068 : carnet de commandes attribué par le vendeur à un client nommé.

- volet 2 : `documented_backlog_dependency` (§3.3, E.3), part du RPO du fournisseur que le fournisseur attribue
  lui-même à un client financé ; jamais bornée (rien n'oblige à publier le RPO par client) ;
- volet 3 : `contracted_backlog_share` (rang 2, §14), part du carnet contracté d'un vendeur (RPO ou loyers à recevoir,
  jamais mêlés) que le vendeur attribue à un client nommé, financé ou non ; exacte quand le reste est écrit, sinon
  majorée par la valeur publiée des contrats, sous une hypothèse déclarée ;
- montage `backlog` : paragraphes des dépôts d'un vendeur qui nomment l'un de ses clients et parlent de carnet.

Aucune somme entre clients ni entre vendeurs ; les cellules du volet 3 n'entrent ni dans l'annexe E ni dans l'annexe F,
ni dans les mesures de financement, l'exposition, les paires, les cycles ou les conclusions (E.3 ne lit que les cellules
de fin d'exercice du volet 2).
"""
import datetime as dt
import json
import re
from collections import defaultdict
from decimal import Decimal

from .measures import cell, ds

NONE = "none"
RPO = "us-gaap:RevenueRemainingPerformanceObligation"
TIMING = "us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis"
CUSTOMER_AXIS = "srt:MajorCustomersAxis"
CHANGE_CONCEPT = re.compile(r"RemainingPerformanceObligation\w*(?:IncreaseDecrease|Increase)$")
CATEGORY = re.compile(r"Customers?$|Clients?$|Segment|Market", re.I)    # « CommercialCustomers » : une catégorie
HYPOTHESIS = ("S publie chacun de ses contrats importants avec C (Item 1.01 du 8-K) ; la valeur d'un contrat, "
              "totale ou maximale (« up to »), majore ce qu'il en reste")
CONTRACT_STATEMENTS = ("contract_value", "change", "remaining", "included_no_amount", "excluded")


def _d(x):
    if x in (None, "", NONE) or (isinstance(x, float) and x != x):
        return None
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def _key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def next_day(t):
    return "typed:" + (_d(t) + dt.timedelta(days=1)).isoformat()


# -- faits balisés par client (point 4) -------------------------------------------------------------------------

def member_group(member, candidates):
    """Groupe que nomme un membre de client : le nom le plus long (registre, lexique), d'au moins quatre caractères,
    contenu dans le nom local du membre, parmi les groupes candidats ; None si aucun, si deux groupes se partagent le
    plus long, ou si le membre est une catégorie de clients, un segment ou un marché (« commercial customers »)."""
    local = member.split(":", 1)[-1]
    local = local[:-6] if local.endswith("Member") else local
    if CATEGORY.search(local):
        return None
    mk = _key(local)
    best, who = 0, set()
    for g, names in candidates.items():
        for n in names:
            k = _key(n)
            if len(k) < 4 or k not in mk:
                continue
            if len(k) > best:
                best, who = len(k), {g}
            elif len(k) == best:
                who.add(g)
    return next(iter(who)) if len(who) == 1 else None


def tagged_customer_rpo(rows, candidates_of):
    """Faits balisés de RPO par client : un solde (le concept RPO, à une date) ou une variation (concept d'extension en
    IncreaseDecrease, sur une période), sur srt:MajorCustomersAxis, sans autre axe que l'horizon au lendemain de la
    date. `rows` : faits (dictionnaires) ; `candidates_of(S)` : {groupe: noms} des clients possibles de S."""
    out = []
    for r in rows:
        d = {a: m for a, m in json.loads(r["dims"] or "[]")}
        m = d.get(CUSTOMER_AXIS)
        pe = ds(r["period_end"])
        if not m or pe == NONE:
            continue
        other = {a: v for a, v in d.items() if a != CUSTOMER_AXIS}
        if other and other != {TIMING: next_day(pe)}:
            continue
        if r["concept"] == RPO and r.get("period_type") in (None, "instant"):
            kind = "balance"
        elif CHANGE_CONCEPT.search(r["concept"]):
            kind = "change"
        else:
            continue
        if r.get("value") is None:
            continue
        g = member_group(m, candidates_of(r["group_id"]))
        if g is None or g == r["group_id"]:
            continue
        out.append({"fact_key": r["fact_key"], "group_id": r["group_id"], "counterparty": g, "member": m, "kind": kind,
                    "period_end": pe, "period_start": ds(r.get("period_start")), "value": Decimal(str(r["value"])),
                    "unit": r.get("unit"), "accession": r.get("accession"), "form": r.get("form"),
                    "knowledge_date": ds(r.get("knowledge_date")), "tier": r.get("tier"), "is_tagged": True})
    return out


# -- lignes de carnet (point 7) ---------------------------------------------------------------------------------

def line_date(o):
    """Date d'une ligne de carnet : celle du reste ou de l'énoncé (`period_end`), sinon la signature
    (`event_date`), sinon la date de la pièce."""
    return _d(o.get("period_end")) or _d(o.get("event_date")) or _d(o.get("knowledge_date"))


def contract_date(o):
    """Date d'un contrat dans une ligne : sa signature, sinon la date de l'énoncé, sinon celle de la pièce."""
    return _d(o.get("event_date")) or _d(o.get("period_end")) or _d(o.get("knowledge_date"))


def carnet_lines(obs, resolve):
    """Lignes de carnet valides, rattachées au client par la dénomination écrite (`resolve(nom, date)` -> groupe)."""
    out = []
    for o in obs:
        if o.get("kind") != "observation" or o.get("validation_state") != "valid":
            continue
        if o.get("backlog_basis") in (None, NONE) or o.get("backlog_statement") in (None, NONE):
            continue
        c = resolve(o.get("counterparty_name"), line_date(o))
        if not c or c == o.get("group_id"):
            continue
        out.append(dict(o, _client=c))
    return out


def known_values(edges):
    """Contrats qu'une arête de valeur fait connaître (point 15) : arête commerciale du client vers le vendeur,
    engagement d'achat ou bail de capacité, montant en USD, niveau A à D, au stade `signed` ou `available`, tirée d'une
    ligne déposée par le vendeur lui-même. Renvoie des dictionnaires (vendeur, client, clé de contrat, date, arête) ;
    une arête sans clé de contrat garde la sienne (`link:`), qu'aucune ligne de carnet ne peut couvrir."""
    out = []
    for l in edges:
        o = l.get("_obs") or {}
        if l.get("family") != "commercial" or l.get("edge_type") not in ("purchase_commitment", "capacity_lease"):
            continue
        if l.get("amount") is None or l.get("unit") != "USD" or l.get("tier") not in ("A", "B", "C", "D"):
            continue
        if l.get("stage") not in ("signed", "available") or l.get("elimination_status") == "eliminated":
            continue
        if not l.get("to_group") or o.get("group_id") != l["to_group"] or l.get("from_group") in (None, l["to_group"]):
            continue
        out.append({"group_id": l["to_group"], "counterparty": l["from_group"],
                    "instrument_key": l.get("instrument_key") or "link:" + l["link_key"],
                    "date": contract_date(o), "link_key": l["link_key"], "knowledge_date": o.get("knowledge_date")})
    return out


class Inputs:
    """Faits balisés, lignes de carnet et contrats connus par une arête de valeur, par (vendeur, client) ;
    dénominateurs publiés, par (groupe, date, vue)."""

    def __init__(self, tagged=(), lines=(), rpo_cells=(), rpo12_cells=(), lease_cells=(), known=()):
        self.tagged, self.lines, self.known = defaultdict(list), defaultdict(list), defaultdict(list)
        for f in tagged:
            self.tagged[(f["group_id"], f["counterparty"])].append(f)
        for o in lines:
            self.lines[(o["group_id"], o["_client"])].append(o)
        for k in known:
            self.known[(k["group_id"], k["counterparty"])].append(k)

        def by(cs):
            return {(c["subject"], c["period_end"], c["view"]): c for c in cs}
        self.rpo, self.rpo12, self.lease = by(rpo_cells), by(rpo12_cells), by(lease_cells)

    def pairs(self):
        return sorted(set(self.tagged) | set(self.lines))


def _pick(rows, view):
    """as_known : la première publication ; revised : la dernière."""
    rows = sorted(rows, key=lambda r: (str(r.get("knowledge_date") or ""), str(r.get("accession") or ""),
                                       str(r.get("fact_key") or r.get("obs_key") or "")))
    return (rows[0] if view == "as_known" else rows[-1]) if rows else None


def _known(rows, cut):
    return [r for r in rows if _d(r.get("knowledge_date")) is None or _d(r.get("knowledge_date")) <= cut]


def _usd(o):
    return (o.get("currency") or o.get("unit")) in ("USD", None)


def _computed(c):
    return c is not None and c.get("status") == "computed" and c.get("value") is not None


def other_contracts(lines, t, excluded, known=()):
    """Contrats de S avec C, signés à t au plus tard, que les lignes de carnet ou les arêtes de valeur (point 15) font
    paraître, hors de ceux que les exclusions visent (par leur clé de contrat). Une valeur de contrat, une hausse ou une
    inclusion sans clé compte pour un contrat ; un reste sans clé ne nomme aucun contrat."""
    keys = {o.get("instrument_key") for o in excluded if o.get("instrument_key")}
    out = set()
    for o in lines:
        st, k = o["backlog_statement"], o.get("instrument_key")
        if st not in ("contract_value", "change", "remaining", "included_no_amount") or (st == "remaining" and not k):
            continue
        if (contract_date(o) or t) > t or (k and k in keys):
            continue
        out.add(k or "obs:" + o["obs_key"])
    out |= {k["instrument_key"] for k in known if (k["date"] or t) <= t and k["instrument_key"] not in keys}
    return out


def uncovered(lines, known, t):
    """Arêtes de valeur datées de t au plus tard dont le contrat n'a aucune ligne de carnet (point 15)."""
    keys = {o.get("instrument_key") for o in lines if o.get("instrument_key")}
    return sorted({k["link_key"] for k in known if (k["date"] or t) <= t and k["instrument_key"] not in keys})


def _term(o, value):
    return {"fact_key": o.get("fact_key") or ("obs:" + o["obs_key"]), "value": abs(Decimal(str(value))),
            "tier": o.get("tier"), "knowledge_date": o.get("knowledge_date"), "is_tagged": bool(o.get("is_tagged"))}


# -- volet 2 : documented_backlog_dependency (point 4) ----------------------------------------------------------

def dependency_cells(I, s, c, t, view, as_of, cut, buys, at="fiscal_year_end"):
    """Les deux cellules (total, beyond_12m) de la dépendance du carnet du fournisseur s au client c à la date t, avec
    ce que le fournisseur publie à la coupure `cut` ; `buys` : une arête commerciale va du client au fournisseur ; `at` :
    fin d'exercice (E.3) ou autre fin de trimestre (série publiée seulement)."""
    t, cut = _d(t), _d(cut)
    pe = t.isoformat()
    tagged = _known(I.tagged.get((s, c), []), cut)
    lines = [o for o in _known(I.lines.get((s, c), []), cut) if o.get("tier") in ("A", "B", "C")]
    bal = _pick([f for f in tagged if f["kind"] == "balance" and f["period_end"] == pe and _usd(f)], view)
    rem = _pick([o for o in lines if o["backlog_basis"] == "rpo" and o["backlog_statement"] == "remaining"
                 and ds(o.get("period_end")) == pe and _usd(o)], view)
    exc = [o for o in lines if o["backlog_basis"] == "rpo" and o["backlog_statement"] == "excluded"
           and ds(o.get("period_end")) == pe]
    # ce qui existe sans entrer dans la valeur : inclusion sans montant, hausses, valeurs de contrats
    ctx = {"included_no_amount": sorted("obs:" + o["obs_key"] for o in lines
                                        if o["backlog_statement"] == "included_no_amount" and ds(o.get("period_end")) == pe),
           "changes": sorted({f["fact_key"] for f in tagged if f["kind"] == "change" and _d(f["period_end"]) <= t} |
                             {"obs:" + o["obs_key"] for o in lines if o["backlog_statement"] == "change"
                              and (line_date(o) or t) <= t}),
           "contract_values": sorted("obs:" + o["obs_key"] for o in lines
                                     if o["backlog_statement"] in ("contract_value", "total_contract_value")
                                     and (contract_date(o) or t) <= t)}
    flags = dict({k: v for k, v in ctx.items() if v}, date_kind=at)
    num = term = src = None
    if bal is not None:
        num, term, src = bal["value"], _term(bal, bal["value"]), "tagged_customer_rpo"
    elif rem is not None:
        num, term, src = Decimal(str(rem["amount"])), _term(rem, rem["amount"]), "line_remaining"
    elif exc and not other_contracts(lines, t, exc, _known(I.known.get((s, c), []), cut)):
        num, term, src = Decimal(0), _term(exc[0], 0), "line_excluded"
    den_total = I.rpo.get((s, pe, view))
    out = []
    for tm, den in (("total", den_total), ("beyond_12m", I.rpo12.get((s, pe, view)))):
        def nd(reason, basis):
            return cell("documented_backlog_dependency", s, None, t, view, as_of, counterparty=c, term=tm,
                        policy="exposure_outstanding", status="not_determinable", nd_reason=reason,
                        flags=dict(flags, basis=basis))
        if not _computed(den_total):
            out.append(nd((den_total or {}).get("nd_reason") or "not_disclosed",
                          "le fournisseur ne publie aucun RPO à cette date"))
        elif not _computed(den):
            out.append(nd((den or {}).get("nd_reason") or "not_disclosed",
                          "part du RPO du fournisseur au-delà de douze mois non publiée"))
        elif num is not None and (tm == "total" or src == "line_excluded") and Decimal(str(den["value"])) > 0:
            dv = Decimal(str(den["value"]))
            out.append(cell("documented_backlog_dependency", s, None, t, view, as_of, counterparty=c, term=tm,
                            policy="exposure_outstanding", value=num / dv, numerator=num, denominator=dv, unit="pure",
                            terms=[term], flags=dict(flags, source=src)))
        elif num is not None:
            out.append(nd("not_disclosed", "part du client au-delà de douze mois non écrite"))
        elif buys:
            out.append(nd("anonymous", "aucun RPO attribué par le fournisseur à ce client au niveau A à C"))
        else:
            out.append(nd("precondition_not_met", "aucune vente du fournisseur au client documentée"))
    return out


# -- volet 3 : contracted_backlog_share (point 5) ---------------------------------------------------------------

def upper_value(lines, t, known=()):
    """Valeur publiée qui majore ce que C doit encore à S à t (point 5) : la dernière valeur totale des contrats de S
    avec C datée de t au plus tard, si aucun contrat connu (lignes ou arêtes de valeur, point 15) n'est daté après elle ;
    à défaut, la somme, sur les contrats signés à t au plus tard, de la dernière valeur de chaque contrat et des hausses
    qui la suivent, si chaque contrat que les lignes font paraître à t a une valeur. Une hausse sans clé de contrat ne
    s'attache à aucune valeur et ne majore rien. Renvoie (valeur, lignes) ou None."""
    tot = [o for o in lines if o["backlog_statement"] == "total_contract_value" and (line_date(o) or t) <= t]
    if tot:
        o = max(tot, key=lambda o: (line_date(o) or t, str(o.get("knowledge_date")), o["obs_key"]))
        td = line_date(o) or t
        dates = [contract_date(x) for x in lines if x["backlog_statement"] in ("contract_value", "change")] + \
                [k["date"] for k in known]
        if not any(d and td < d <= t for d in dates):
            return Decimal(str(o["amount"])), [o]
    by = defaultdict(list)
    for o in lines:
        k = o.get("instrument_key")
        if o["backlog_statement"] == "contract_value":
            by[k or "obs:" + o["obs_key"]].append(o)
        elif k and o["backlog_statement"] in CONTRACT_STATEMENTS:
            by[k].append(o)
    total, used = Decimal(0), []
    for k, os_ in sorted(by.items()):
        vals = [o for o in os_ if o["backlog_statement"] == "contract_value"]
        signed = [o for o in vals if (contract_date(o) or t) <= t]
        if not signed:
            if not vals and min(contract_date(o) or t for o in os_) <= t:
                return None              # un contrat qui paraît à t sans valeur publiée : la somme ne majore rien
            continue
        last = max(signed, key=lambda o: (contract_date(o) or t, str(o.get("knowledge_date")), o["obs_key"]))
        ups = [o for o in os_ if o["backlog_statement"] == "change"
               and (contract_date(last) or t) < (line_date(o) or t) <= t]
        total += Decimal(str(last["amount"])) + sum((Decimal(str(o["amount"])) for o in ups), Decimal(0))
        used += [last] + ups
    return (total, used) if used else None


TERM_FR = {"rpo": "RPO (ASC 606)", "lease": "loyers à recevoir (ASC 842, bailleur)"}


def share_cells(I, quarter_ends, as_of):
    """contracted_backlog_share : une cellule par vendeur, client, terme et date, vue as_known à l'as_of. Dates : les
    fins de trimestre de S, de la première date d'une ligne ou d'un fait sur C à l'as_of, où le dénominateur du terme
    est publié ; et les dates d'un reste ou d'une exclusion écrits, où il peut manquer (son motif)."""
    as_of_d = _d(as_of)
    out = []
    for s, c in I.pairs():
        lines = [o for o in I.lines.get((s, c), []) if o.get("tier") != "E"]        # jamais une pièce EX-99 (niveau E)
        balances = [f for f in I.tagged.get((s, c), []) if f["kind"] == "balance"]
        unspecified = sorted("obs:" + o["obs_key"] for o in lines if o["backlog_basis"] == "unspecified")
        for tm, dens in (("rpo", I.rpo), ("lease", I.lease)):
            ls = [o for o in lines if o["backlog_basis"] == tm]
            tg = balances if tm == "rpo" else []
            if not ls and not tg:
                continue
            first = min([line_date(o) for o in ls if line_date(o)] + [_d(f["period_end"]) for f in tg])
            exact = {_d(o.get("period_end")) for o in ls if o["backlog_statement"] in ("remaining", "excluded")} | \
                    {_d(f["period_end"]) for f in tg}
            dates = sorted({q for q in quarter_ends.get(s, []) if first <= q <= as_of_d
                            and _computed(dens.get((s, q.isoformat(), "as_known")))} |
                           {x for x in exact if x and x <= as_of_d})
            base = {"term_basis": TERM_FR[tm], **({"unspecified_lines": unspecified} if unspecified else {})}
            for t in dates:
                pe = t.isoformat()
                inc = sorted("obs:" + o["obs_key"] for o in ls
                             if o["backlog_statement"] == "included_no_amount" and ds(o.get("period_end")) == pe)
                fl = dict(base, **({"included_no_amount": inc} if inc else {}))

                def nd(reason, basis=None, **extra):
                    return cell("contracted_backlog_share", s, None, t, "as_known", as_of, counterparty=c, term=tm,
                                status="not_determinable", nd_reason=reason,
                                flags=dict(fl, **({"basis": basis} if basis else {}), **extra))
                den = dens.get((s, pe, "as_known"))
                if not _computed(den) or Decimal(str(den["value"])) <= 0:
                    out.append(nd((den or {}).get("nd_reason") or "not_disclosed", "dénominateur non publié à cette date"))
                    continue
                dv = Decimal(str(den["value"]))
                bal = _pick([f for f in tg if f["period_end"] == pe], "as_known")
                rem = _pick([o for o in ls if o["backlog_statement"] == "remaining" and ds(o.get("period_end")) == pe],
                            "as_known")
                exc = [o for o in ls if o["backlog_statement"] == "excluded" and ds(o.get("period_end")) == pe]
                if bal is not None or rem is not None:
                    src = bal if bal is not None else rem
                    num = bal["value"] if bal is not None else Decimal(str(rem["amount"]))
                    if not _usd(src):
                        out.append(nd("mixed_currency"))
                        continue
                    out.append(cell("contracted_backlog_share", s, None, t, "as_known", as_of, counterparty=c, term=tm,
                                    value=num / dv, numerator=num, denominator=dv, unit="pure", terms=[_term(src, num)],
                                    flags=dict(fl, source="tagged_customer_rpo" if bal is not None else "line_remaining")))
                    continue
                known = I.known.get((s, c), [])
                if exc and not other_contracts(ls, t, exc, known):
                    out.append(cell("contracted_backlog_share", s, None, t, "as_known", as_of, counterparty=c, term=tm,
                                    value=Decimal(0), numerator=Decimal(0), denominator=dv, unit="pure",
                                    terms=[_term(exc[0], 0)], flags=dict(fl, source="line_excluded")))
                    continue
                # garde du point 15 : un contrat connu par une arête de valeur, sans ligne de carnet, interdit la somme
                miss = uncovered(lines, known, t)
                if miss:
                    out.append(nd("not_disclosed", "contrat connu par une arête de valeur, sans ligne de carnet",
                                  uncovered_edges=miss))
                    continue
                ub = upper_value(ls, t, known)
                if ub is None:
                    out.append(nd("not_disclosed", "aucun reste ni aucune valeur de contrat qui le majore"))
                    continue
                v, used = ub
                if not all(_usd(o) for o in used):
                    out.append(nd("mixed_currency"))
                    continue
                out.append(cell("contracted_backlog_share", s, None, t, "as_known", as_of, counterparty=c, term=tm,
                                status="bounded", lower=Decimal(0), upper=min(Decimal(1), v / dv), numerator=v,
                                denominator=dv, unit="pure", bound_basis="published_contract_value",
                                terms=[_term(o, o["amount"]) for o in used],
                                flags=dict(fl, hypothesis=HYPOTHESIS, capped=v > dv,
                                           value_lines=["obs:" + o["obs_key"] for o in used])))
    return out


# -- montage `backlog` (point 6) --------------------------------------------------------------------------------

VOCAB = (r"remaining performance obligations?|\bRPOs?\b|unsatisfied performance obligations?|contract(?:ed|ual)? "
         r"(?:revenue|value)|total contract|aggregate (?:contract )?value|(?:future|minimum|remaining) (?:minimum )?"
         r"(?:lease|rental) (?:payments|receipts)|lease payments to be received|\bbacklog\b|revenue backlog")
PREFILTER = rb"(?i)performance obligation|\bRPO|contract(?:ed|ual)? (?:revenue|value)|total contract|aggregate|lease payments|backlog"
FORMS = ("10-K", "10-K/A", "10-KT", "10-KT/A", "10-Q", "10-Q/A", "8-K", "8-K/A", "S-1", "S-1/A", "424B3", "424B4",
         "20-F", "20-F/A", "40-F", "40-F/A")
EX99_FILE = r"ex-?99|exhibit-?99"      # pièce EX-99 sans type au registre des documents (point 15)


def sellers(links, groups):
    """{vendeur: clients} : groupes du modèle vers lesquels va une arête commerciale d'un client nommé
    (`links` : (de, vers, famille, élimination))."""
    out = defaultdict(set)
    for f, t, fam, el in links:
        if fam == "commercial" and el != "eliminated" and t in groups and isinstance(f, str) and f and f != t:
            out[t].add(f)
    return dict(out)


def names_rx(names):
    """Noms d'un ou de plusieurs clients, tels qu'écrits (casse comprise), entre deux bornes de mot."""
    alts = sorted({re.escape(n) for n in names if n and len(n) >= 3}, key=len, reverse=True)
    return re.compile(r"(?<![\w])(?:" + "|".join(alts) + r")(?![\w])") if alts else None


def qualifier(names, vocab=VOCAB):
    """Un paragraphe qualifie s'il nomme l'un des clients du vendeur et un terme de carnet (point 6)."""
    nrx, voc = names_rx(names), re.compile(vocab, re.I)
    if nrx is None:
        return None
    return lambda p: bool(voc.search(p)) and bool(nrx.search(p))
