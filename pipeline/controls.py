"""Contrôles comptables C1 à C16 (§8.3).

Tolérance d'arrondi et elle seule : pour Σaᵢ = b, Σ ½·10^(−decimalsᵢ) + ½·10^(−decimals_b),
INF comptant pour zéro ; decimals se lit dans l'instance, jamais dans companyfacts.
Chaque contrôle renvoie ok, mismatch avec un explanation_code, not_testable avec son motif,
ou tautological. Un contrôle ne passe jamais ok par une variable d'ajustement.
"""
import json
from collections import defaultdict
from decimal import Decimal

import pandas as pd

NONE = "none"
HALF = Decimal("0.5")

BS_TOTALS = ["us-gaap:AssetsCurrent", "us-gaap:Assets", "us-gaap:LiabilitiesCurrent", "us-gaap:Liabilities",
             "us-gaap:StockholdersEquity",
             "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
             "us-gaap:LiabilitiesAndStockholdersEquity"]
CF_TOTALS = ["us-gaap:NetCashProvidedByUsedInOperatingActivities",
             "us-gaap:NetCashProvidedByUsedInInvestingActivities",
             "us-gaap:NetCashProvidedByUsedInFinancingActivities"]
NOTE_TOTALS = ["us-gaap:LesseeOperatingLeaseLiabilityPaymentsDue", "us-gaap:FinanceLeaseLiabilityPaymentsDue",
               "us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount",
               "us-gaap:PurchaseObligation", "us-gaap:RevenueRemainingPerformanceObligation"]


def tol_of(row):
    if row.get("decimals_inf"):
        return Decimal(0)
    d = row.get("decimals")
    if d is None or (isinstance(d, float) and pd.isna(d)):
        return None
    return HALF * Decimal(10) ** (-int(d))


def ctrl(control, subject, ps, pe, view, as_of, status, accession=None, breakdown=NONE, lhs=None, rhs=None,
         tol=None, basis="declared", explanation=None, reason=None, evidence=None, variant=NONE):
    diff = (lhs - rhs) if (lhs is not None and rhs is not None) else None
    return {"control": control, "subject": subject, "period_start": str(ps) if ps else NONE,
            "period_end": str(pe) if pe else NONE, "view": view, "as_of": as_of, "breakdown_key": breakdown,
            "mapping_variant": variant, "accession": accession, "status": status, "explanation_code": explanation,
            "not_testable_reason": reason, "lhs": lhs, "rhs": rhs, "difference": diff, "tolerance": tol,
            "tolerance_basis": basis if tol is not None else None,
            "evidence": json.dumps(evidence) if evidence else None}


class Filing:
    """Faits non dimensionnés, présentation, calcul et soldes débit/crédit d'un dépôt."""

    def __init__(self, acc, facts, pres, calc, crdr):
        self.acc = acc
        self.f = facts
        self.pres = pres
        self.calc = calc
        self.crdr = crdr
        self.values = defaultdict(list)
        self.conflicting = set()
        for r in facts.itertuples():
            if r.n_dims == 0 and r.value is not None:
                key = (r.concept, r.period_type, r.period_start, r.period_end)
                if r.conflict:
                    self.conflicting.add(key)
                    continue
                self.values[key].append({"value": Decimal(str(r.value)), "decimals": r.decimals,
                                         "decimals_inf": r.decimals_inf, "fact_key": r.fact_key})
        self.calc_parents = defaultdict(set)
        for r in calc.itertuples():
            self.calc_parents[r.parent].add(r.child)

    def get(self, concept, ptype, ps, pe):
        vs = self.values.get((concept, ptype, ps, pe))
        if not vs:
            return None
        # le plus précis
        return max(vs, key=lambda v: (99 if v["decimals_inf"] else (v["decimals"] if v["decimals"] is not None and not pd.isna(v["decimals"]) else -99)))

    def is_conflicting(self, concept, ptype, ps, pe):
        return (concept, ptype, ps, pe) in self.conflicting

    def periods(self, concept):
        return sorted({(k[1], k[2], k[3]) for k in self.values if k[0] == concept}, key=lambda x: str(x))

    def _weight(self, child, total):
        a, b = self.crdr.get(child), self.crdr.get(total)
        if a and b:
            return Decimal(1) if a == b else Decimal(-1)
        cw = self.calc[(self.calc["parent"] == total) & (self.calc["child"] == child)]
        if not cw.empty:
            return Decimal(str(cw.iloc[0]["weight"]))
        return Decimal(1)

    def siblings(self, total, kinds):
        """Composantes d'un total (§8.3) : ses enfants de calcul dans le rôle de l'état, plus
        les lignes que la présentation place sous le même parent sans les rattacher au calcul
        (ni directement ni sous un sous-total) ; le signe d'une telle ligne vient de son solde
        débit/crédit. Sans aucune relation de calcul, les enfants de présentation seuls, sous-totaux
        intermédiaires écartés. Renvoie une liste de (rôle, composantes, poids)."""
        p = self.pres[self.pres["statement_kind"].isin(kinds)]
        skip = ("Axis", "Member", "Table", "LineItems", "Domain")
        out = []
        for role, pr in p[p["child"] == total].groupby("role"):
            parent = pr.iloc[0]["parent"]
            allr = p[p["role"] == role]
            kids = list(allr[allr["parent"] == parent].sort_values("ord")["child"])
            if total not in kids:
                continue
            # les composantes précèdent leur total : on s'arrête au total
            kids = kids[:kids.index(total)]
            sibs = []
            for c in kids:
                if c.endswith(skip):
                    continue
                if c.endswith("Abstract"):
                    sub = [x for x in allr[allr["parent"] == c].sort_values("ord")["child"]
                           if not x.endswith(skip + ("Abstract",))]
                    subtot = [x for x in sub if self.calc_parents.get(x, set()) & set(sub)]
                    sibs += subtot[-1:] if subtot else sub
                else:
                    sibs.append(c)
            cr = self.calc[(self.calc["parent"] == total) & (self.calc["role"] == role)]
            if cr.empty:
                cr = self.calc[self.calc["parent"] == total]
            cr = cr.drop_duplicates("child")
            calc_kids = list(cr["child"])
            weights = {r.child: Decimal(str(r.weight)) for r in cr.itertuples()}
            # frontière : dernier sous-total précédent qui n'est pas lui-même composante du total
            last_boundary = -1
            for i, c in enumerate(sibs):
                if c not in calc_kids and (self.calc_parents.get(c, set()) & set(sibs)):
                    last_boundary = i
            sibs = sibs[last_boundary + 1:]
            if calc_kids:
                covered = set(calc_kids)
                todo = list(calc_kids)
                while todo:
                    x = todo.pop()
                    for k in self.calc_parents.get(x, ()):
                        if k not in covered:
                            covered.add(k)
                            todo.append(k)
                extra = [c for c in sibs if c not in covered and not (self.calc_parents.get(c, set()) & covered)]
                comps = calc_kids + extra
                for c in extra:
                    weights[c] = self._weight(c, total)
            else:
                comps = [c for c in sibs if not (self.calc_parents.get(c, set()) & set(sibs))]
                weights = {c: self._weight(c, total) for c in comps}
            out.append((role, comps, weights))
        return out

    def tree(self, total, kinds):
        """Descendants d'un total dans l'arbre de calcul de l'état."""
        roles = set(self.pres[self.pres["statement_kind"].isin(kinds)]["role"])
        cr = self.calc[self.calc["role"].isin(roles)]
        kids = defaultdict(set)
        for r in cr.itertuples():
            kids[r.parent].add(r.child)
        seen, todo = set(), [total]
        while todo:
            x = todo.pop()
            for k in kids.get(x, ()):
                if k not in seen:
                    seen.add(k)
                    todo.append(k)
        return seen


def sum_check(control, F, g, total, comps, weights, ptype, ps, pe, view, as_of, form):
    t = F.get(total, ptype, ps, pe)
    if t is None:
        return None
    if not comps:
        return ctrl(control, g, ps, pe, view, as_of, "not_testable", F.acc, breakdown=total,
                    reason="aucune relation de calcul publiée pour ce total")
    got, missing = [], []
    for c in comps:
        v = F.get(c, ptype, ps, pe)
        if v is None:
            if F.is_conflicting(c, ptype, ps, pe):
                return ctrl(control, g, ps, pe, view, as_of, "not_testable", F.acc, breakdown=total,
                            reason=f"composante en conflit (saut d'échelle non confirmé) : {c}")
            missing.append(c)
        else:
            got.append((c, v))
    if not got:
        return ctrl(control, g, ps, pe, view, as_of, "not_testable", F.acc, breakdown=total,
                    reason="aucune composante balisée à cette date")
    s = sum(weights.get(c, Decimal(1)) * v["value"] for c, v in got)
    tols = [tol_of(v) for _, v in got] + [tol_of(t)]
    basis = "declared"
    if any(x is None for x in tols):
        tols = [x or Decimal(0) for x in tols]
        basis = "inferred"
    tol = sum(tols)
    ok = abs(s - t["value"]) <= tol
    return ctrl(control, g, ps, pe, view, as_of, "ok" if ok else "mismatch", F.acc, breakdown=total, lhs=s,
                rhs=t["value"], tol=tol, basis=basis,
                explanation=None if ok else ("components_missing" if missing else "sum_differs"),
                evidence={"total": t["fact_key"], "components": [v["fact_key"] for _, v in got],
                          "missing": missing, "form": form})


def run(con, as_of):
    facts = con.execute("""SELECT fact_key, group_id, accession, form, concept, period_type, period_start, period_end,
                                  unit, dims, n_dims, value, decimals, decimals_inf, conflict, knowledge_date
                           FROM facts WHERE source = 'instance' AND value IS NOT NULL""").fetchdf()
    for c in ("period_start", "period_end"):
        facts[c] = pd.to_datetime(facts[c]).dt.date
    pres = con.execute("SELECT accession, role, statement_kind, parent, child, ord FROM pres").fetchdf()
    calc = con.execute("SELECT accession, role, parent, child, weight FROM calc").fetchdf()
    cmap = con.execute("SELECT accession, quantity, concept, statement_kind FROM concept_map").fetchdf()
    cmap_by = dict(tuple(cmap.groupby("accession")))
    from . import config as _cfg
    base_crdr = json.loads((_cfg.DB_DIR / "usgaap2026_balance.json").read_text())
    tags = con.execute("SELECT accession, concept, crdr FROM tags WHERE crdr IS NOT NULL").fetchdf()
    crdr_by = {a: dict(zip(t["concept"], t["crdr"])) for a, t in tags.groupby("accession")}
    pres_by = dict(tuple(pres.groupby("accession")))
    calc_by = dict(tuple(calc.groupby("accession")))
    out = []
    view = "as_known"   # un contrôle porte sur un dépôt, tel que publié (§7.3)
    for acc, fa in facts.groupby("accession"):
        g = fa["group_id"].iloc[0]
        form = fa["form"].iloc[0]
        crdr = dict(base_crdr)
        crdr.update(crdr_by.get(acc, {}))
        F = Filing(acc, fa, pres_by.get(acc, pres.iloc[0:0]), calc_by.get(acc, calc.iloc[0:0]), crdr)
        # C1 composantes du bilan
        for total in BS_TOTALS:
            for role, comps, w in F.siblings(total, {"balance_sheet"}):
                for ptype, ps, pe in F.periods(total):
                    r = sum_check("c1_balance_components", F, g, total, comps, w, ptype, ps, pe, view, as_of, form)
                    if r:
                        out.append(r)
        # C2 composantes du tableau des flux
        for total in CF_TOTALS:
            for role, comps, w in F.siblings(total, {"cash_flow"}):
                for ptype, ps, pe in F.periods(total):
                    r = sum_check("c2_cash_flow_components", F, g, total, comps, w, ptype, ps, pe, view, as_of, form)
                    if r:
                        out.append(r)
        out += mapping_check(F, g, cmap_by.get(acc), view, as_of)
        out += c3_cash(F, g, view, as_of)
        out += c6_articulation(F, g, view, as_of)
        out += c9_leases(F, g, view, as_of)
        # C10 et C13 : sommes d'échéanciers (composantes lues dans la présentation de la note)
        for total in NOTE_TOTALS:
            ctl = "c13_rpo" if total.endswith("RemainingPerformanceObligation") else "c10_maturity_sums"
            for role, comps, w in F.siblings(total, {"note_details", "note_tables", "note"}):
                # un échéancier se somme sans signe : seules les tranches de même famille comptent
                fam = [c for c in comps if _same_family(c, total)]
                for ptype, ps, pe in F.periods(total):
                    r = sum_check(ctl, F, g, total, fam, {}, ptype, ps, pe, view, as_of, form)
                    if r:
                        out.append(r)
        out += c14_eps(F, fa, g, view, as_of)
        out += c15_tax(F, g, view, as_of)
        out += c16_concentration(fa, g, acc, view, as_of)
    out += c4_restatements(con, as_of)
    out += c7_continuity(con, as_of)
    return out


def _same_family(c, total):
    """Tranche d'un échéancier : concept qui partage la racine du total (paiements de
    location, obligations d'achat, RPO), extensions comprises."""
    roots = {"us-gaap:LesseeOperatingLeaseLiabilityPaymentsDue": ("LesseeOperatingLeaseLiabilityPayments",),
             "us-gaap:FinanceLeaseLiabilityPaymentsDue": ("FinanceLeaseLiabilityPayments",),
             "us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount": ("UnrecordedUnconditionalPurchaseObligation",),
             "us-gaap:PurchaseObligation": ("PurchaseObligation",),
             "us-gaap:RevenueRemainingPerformanceObligation": ("RevenueRemainingPerformanceObligation",)}
    local = c.split(":", 1)[1]
    excluded = ("UndiscountedExcessAmount", "Percentage", "ImputedInterest", "Purchases", "Term",
                "MinimumQuantity", "MaximumQuantity")
    return any(local.startswith(r) for r in roots.get(total, ())) and not local.endswith(excluded) \
        and c != total


SUPPLEMENTAL = {"cash_and_restricted_cash_total", "unpaid_capex", "interest_paid", "rou_obtained_operating_lease",
                "rou_obtained_finance_lease", "vendor_financed_ppe_additions", "stock_paid_ppe_additions",
                "capitalized_interest", "pik_interest"}

MAP_TREES = {"balance_sheet": ["us-gaap:Assets", "us-gaap:LiabilitiesAndStockholdersEquity", "us-gaap:Liabilities"],
             "cash_flow": ["us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
                           "us-gaap:NetCashProvidedByUsedInOperatingActivities",
                           "us-gaap:NetCashProvidedByUsedInInvestingActivities",
                           "us-gaap:NetCashProvidedByUsedInFinancingActivities"]}


def mapping_check(F, g, cmap, view, as_of):
    """C1 et C2 portent sur les composantes sélectionnées (§8.3) : une grandeur rattachée
    à un concept d'un état doit appartenir à l'arbre de calcul de cet état."""
    out = []
    if cmap is None:
        return out
    for kind, roots in MAP_TREES.items():
        tree = set()
        for r in roots:
            tree |= F.tree(r, {kind})
        if not tree:
            continue
        tree |= set(roots)
        for row in cmap[cmap["statement_kind"] == kind].itertuples():
            if row.quantity in SUPPLEMENTAL:
                continue  # informations supplémentaires, hors de l'arithmétique de l'état
            ok = row.concept in tree
            out.append(ctrl("c1_balance_components" if kind == "balance_sheet" else "c2_cash_flow_components",
                            g, None, None, view, as_of, "ok" if ok else "mismatch", F.acc,
                            breakdown=f"mapping:{row.quantity}", explanation=None if ok else "mapped_concept_outside_statement_tree",
                            evidence={"concept": row.concept}))
    return out


def c3_cash(F, g, view, as_of):
    out = []
    total = "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
    for ptype, ps, pe in F.periods(total):
        if ptype != "instant":
            continue
        t = F.get(total, ptype, ps, pe)
        parts = [F.get(c, "instant", None, pe) for c in ("us-gaap:CashAndCashEquivalentsAtCarryingValue",
                                                         "us-gaap:RestrictedCashCurrent", "us-gaap:RestrictedCashNoncurrent",
                                                         "us-gaap:RestrictedCashAndCashEquivalentsAtCarryingValue")]
        cash = parts[0]
        if cash is None:
            continue
        got = [p for p in parts if p is not None]
        s = sum(p["value"] for p in got)
        tol = sum((tol_of(p) or Decimal(0)) for p in got) + (tol_of(t) or Decimal(0))
        ok = abs(s - t["value"]) <= tol
        out.append(ctrl("c3_cash_reconciliation", g, None, pe, view, as_of, "ok" if ok else "mismatch", F.acc,
                        lhs=s, rhs=t["value"], tol=tol,
                        explanation=None if ok else ("restricted_cash_not_tagged" if len(got) == 1 else "sum_differs"),
                        evidence={"total": t["fact_key"], "components": [p["fact_key"] for p in got]}))
    return out


def c6_articulation(F, g, view, as_of):
    """Résultat (part du groupe ou y compris minoritaires) = première ligne du tableau des flux."""
    out = []
    p = F.pres[F.pres["statement_kind"] == "cash_flow"]
    if p.empty:
        return out
    first = None
    for c in p.sort_values(["ord"])["child"]:
        if c in ("us-gaap:ProfitLoss", "us-gaap:NetIncomeLoss",
                 "us-gaap:IncomeLossFromContinuingOperations", "us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic"):
            first = c
            break
    if not first:
        return out
    isp = F.pres[F.pres["statement_kind"].isin({"income_statement", "comprehensive_income"})]
    if first not in set(isp["child"]):
        return out  # le compte de résultat ne présente pas ce concept : rien à comparer dans ce dépôt
    for ptype, ps, pe in F.periods(first):
        if ptype != "duration":
            continue
        v = F.get(first, ptype, ps, pe)
        out.append(ctrl("c6_income_articulation", g, ps, pe, view, as_of, "tautological", F.acc, breakdown=first,
                        lhs=v["value"], rhs=v["value"], tol=Decimal(0),
                        explanation="same_concept_in_both_statements",
                        evidence={"fact": v["fact_key"]}))
    return out


def c9_leases(F, g, view, as_of):
    out = []
    specs = [("operating", "us-gaap:LesseeOperatingLeaseLiabilityPaymentsDue",
              "us-gaap:LesseeOperatingLeaseLiabilityUndiscountedExcessAmount",
              ["us-gaap:OperatingLeaseLiability"], ["us-gaap:OperatingLeaseLiabilityCurrent", "us-gaap:OperatingLeaseLiabilityNoncurrent"]),
             ("finance", "us-gaap:FinanceLeaseLiabilityPaymentsDue",
              "us-gaap:FinanceLeaseLiabilityUndiscountedExcessAmount",
              ["us-gaap:FinanceLeaseLiability"], ["us-gaap:FinanceLeaseLiabilityCurrent", "us-gaap:FinanceLeaseLiabilityNoncurrent"])]
    for kind, pay, interest, tot, parts in specs:
        for ptype, ps, pe in F.periods(pay):
            p = F.get(pay, "instant", None, pe)
            i = F.get(interest, "instant", None, pe)
            if p is None or i is None:
                continue
            liab = F.get(tot[0], "instant", None, pe)
            terms = [liab] if liab else [F.get(c, "instant", None, pe) for c in parts]
            if not liab and any(t is None for t in terms):
                out.append(ctrl("c9_lease_liability", g, None, pe, view, as_of, "not_testable", F.acc, breakdown=kind,
                                reason="passif locatif non balisé à cette date"))
                continue
            lv = sum(t["value"] for t in terms)
            lhs = p["value"] - i["value"]
            tol = sum((tol_of(x) or Decimal(0)) for x in [p, i] + terms)
            ok = abs(lhs - lv) <= tol
            out.append(ctrl("c9_lease_liability", g, None, pe, view, as_of, "ok" if ok else "mismatch", F.acc,
                            breakdown=kind, lhs=lhs, rhs=lv, tol=tol, explanation=None if ok else "sum_differs",
                            evidence={"payments": p["fact_key"], "interest": i["fact_key"],
                                      "liability": [t["fact_key"] for t in terms]}))
    return out


def c14_eps(F, fa, g, view, as_of):
    out = []
    eps_c, sh_c = "us-gaap:EarningsPerShareDiluted", "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding"
    classes = fa[(fa["concept"] == eps_c) & (fa["n_dims"] > 0)]
    for ptype, ps, pe in F.periods(eps_c):
        e = F.get(eps_c, ptype, ps, pe)
        s = F.get(sh_c, ptype, ps, pe)
        if e is None or s is None:
            continue
        cl = classes[(classes["period_start"] == ps) & (classes["period_end"] == pe)]
        if not cl.empty and cl["value"].nunique() > 1:
            out.append(ctrl("c14_eps_scale", g, ps, pe, view, as_of, "not_testable", F.acc,
                            reason="plusieurs catégories d'actions aux BPA différents"))
            continue
        num = F.get("us-gaap:NetIncomeLossAvailableToCommonStockholdersDiluted", ptype, ps, pe)
        prod = e["value"] * s["value"]
        if num is not None:
            tol = (tol_of(e) or Decimal("0.005")) * abs(s["value"]) + (tol_of(num) or Decimal(0)) + \
                  abs(e["value"]) * (tol_of(s) or Decimal(0))
            ok = abs(num["value"] - prod) <= tol
            out.append(ctrl("c14_eps_scale", g, ps, pe, view, as_of, "ok" if ok else "mismatch", F.acc,
                            lhs=num["value"], rhs=prod, tol=tol, explanation=None if ok else "scale_or_definition",
                            evidence={"eps": e["fact_key"], "shares": s["fact_key"], "num": num["fact_key"]}))
        else:
            ni = F.get("us-gaap:NetIncomeLoss", ptype, ps, pe)
            if ni is None or ni["value"] == 0:
                continue
            rel = abs(prod - ni["value"]) / abs(ni["value"])
            ok = rel < Decimal("0.10")
            out.append(ctrl("c14_eps_scale", g, ps, pe, view, as_of, "ok" if ok else "mismatch", F.acc,
                            lhs=ni["value"], rhs=prod, tol=abs(ni["value"]) * Decimal("0.10"), basis="inferred",
                            explanation=None if ok else "relative_gap_over_10pct",
                            evidence={"eps": e["fact_key"], "shares": s["fact_key"], "net_income": ni["fact_key"]}))
    return out


def c15_tax(F, g, view, as_of):
    out = []
    for ptype, ps, pe in F.periods("us-gaap:EffectiveIncomeTaxRateContinuingOperations"):
        r = F.get("us-gaap:EffectiveIncomeTaxRateContinuingOperations", ptype, ps, pe)
        tax = F.get("us-gaap:IncomeTaxExpenseBenefit", ptype, ps, pe)
        pre = F.get("us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                    ptype, ps, pe) or F.get("us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments", ptype, ps, pe)
        if r is None or tax is None or pre is None or pre["value"] == 0:
            continue
        calc_rate = tax["value"] / pre["value"]
        tol = tol_of(r) if tol_of(r) is not None else Decimal("0.005")
        ok = abs(calc_rate - r["value"]) <= tol
        out.append(ctrl("c15_tax_rate", g, ps, pe, view, as_of, "ok" if ok else "mismatch", F.acc,
                        lhs=calc_rate.quantize(Decimal("0.000001")), rhs=r["value"], tol=tol,
                        explanation=None if ok else "rate_differs",
                        evidence={"rate": r["fact_key"], "tax": tax["fact_key"], "pretax": pre["fact_key"]}))
    return out


def c16_concentration(fa, g, acc, view, as_of):
    out = []
    c = fa[(fa["concept"] == "us-gaap:ConcentrationRiskPercentage1") & fa["value"].notna()]
    if c.empty:
        return out
    for r in c.itertuples():
        v = Decimal(str(r.value))
        if v < 0 or v > 1:
            out.append(ctrl("c16_concentration", g, r.period_start, r.period_end, view, as_of, "mismatch", acc,
                            breakdown=r.dims, lhs=v, rhs=Decimal(1), explanation="share_out_of_bounds",
                            evidence={"fact": r.fact_key}))
    # somme par repère : faits dont les dimensions ne diffèrent que par le client
    def bench(d):
        dd = json.loads(d)
        return json.dumps([x for x in dd if x[0] != "srt:MajorCustomersAxis"])
    c = c.assign(bench=c["dims"].map(bench), has_cust=c["dims"].str.contains("srt:MajorCustomersAxis"))
    for (b, ps, pe), grp in c[c["has_cust"]].groupby(["bench", "period_start", "period_end"]):
        s = sum(Decimal(str(x)) for x in grp["value"])
        ok = s <= Decimal(1)
        out.append(ctrl("c16_concentration", g, ps, pe, view, as_of, "ok" if ok else "mismatch", acc,
                        breakdown=b[:500], lhs=s, rhs=Decimal(1), explanation=None if ok else "shares_sum_over_one",
                        evidence={"facts": list(grp["fact_key"])}))
    return out


def c4_restatements(con, as_of):
    """Même identité, valeurs différentes selon le dépôt : publié avec recast_cause, jamais écrasé.
    Limité aux grandeurs du modèle (faits non dimensionnés rattachés)."""
    df = con.execute("""
      WITH o AS (
        SELECT q.group_id, q.quantity, q.period_type, q.period_start, q.period_end, q.unit, q.value, q.decimals,
               q.decimals_inf, q.accession, q.knowledge_date, q.fact_key
        FROM q_occ q WHERE q.source = 'instance')
      SELECT group_id, quantity, period_type, period_start, period_end, unit,
             arg_min(value, knowledge_date) AS first_value, arg_max(value, knowledge_date) AS last_value,
             arg_min(accession, knowledge_date) AS first_acc, arg_max(accession, knowledge_date) AS last_acc,
             min(decimals) AS dec, max(knowledge_date) AS last_kd
      FROM o GROUP BY ALL HAVING count(DISTINCT value) > 1""").fetchdf()
    flags = con.execute("""SELECT accession, value_text FROM facts
                           WHERE concept = 'dei:DocumentFinStmtErrorCorrectionFlag'""").fetchall()
    corr = {a for a, v in flags if (v or "").strip().lower() == "true"}
    out = []
    for r in df.itertuples():
        a, b = Decimal(str(r.first_value)), Decimal(str(r.last_value))
        tol = (HALF * Decimal(10) ** (-int(r.dec)) * 2) if r.dec is not None and not pd.isna(r.dec) else Decimal(0)
        if abs(a - b) <= tol:
            continue
        cause = "error_correction_restatement" if r.last_acc in corr else "unknown"
        out.append(ctrl("c4_restatement_detection", r.group_id, r.period_start, r.period_end, "revised", as_of,
                        "mismatch", r.last_acc, breakdown=f"{r.quantity}/{r.unit}", lhs=b, rhs=a, tol=tol,
                        explanation=f"recast:{cause}",
                        evidence={"first_accession": r.first_acc, "last_accession": r.last_acc}))
    return out


def c7_continuity(con, as_of):
    """Trésorerie d'ouverture de P = clôture de P−1 lue dans le dépôt de P−1."""
    rows = con.execute("""
      SELECT group_id, accession, period_end, value, decimals, decimals_inf, knowledge_date, fact_key, form
      FROM facts WHERE source = 'instance' AND n_dims = 0 AND NOT coalesce(conflict, false)
        AND concept = 'us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'
        AND period_type = 'instant'""").fetchdf()
    out = []
    for g, grp in rows.groupby("group_id"):
        # clôture publiée par chaque dépôt pour sa propre date de fin de période (la plus récente des dates qu'il porte)
        own = grp.loc[grp.groupby("accession")["period_end"].idxmax()]
        for r in grp.itertuples():
            # chaque valeur d'ouverture (date < date de clôture du dépôt) est comparée à la clôture publiée
            # par le dépôt qui porte cette date comme sa propre clôture
            prev = own[(own["period_end"] == r.period_end) & (own["accession"] != r.accession)
                       & (own["knowledge_date"] < r.knowledge_date)]
            if prev.empty:
                continue
            p = prev.sort_values("knowledge_date").iloc[-1]
            a, b = Decimal(str(r.value)), Decimal(str(p.value))
            tol = sum((tol_of({"decimals": x.decimals, "decimals_inf": x.decimals_inf}) or Decimal(0)) for x in (r, p))
            ok = abs(a - b) <= tol
            out.append(ctrl("c7_cash_continuity", g, None, r.period_end, "as_known", as_of, "ok" if ok else "mismatch",
                            r.accession, breakdown=p.accession, lhs=a, rhs=b, tol=tol,
                            explanation=None if ok else "opening_differs_from_prior_closing",
                            evidence={"opening": r.fact_key, "prior_closing": p.fact_key}))
    return out
