"""Mesures lues sur des faits dimensionnés de l'instance (§4.2, §5.2, §6.2, §3.6) :
durées d'amortissement par classe, baux non commencés, concentration client."""
import json
import re
from decimal import Decimal

import pandas as pd

from .measures import cell

DUR = re.compile(r"^P(?:(\d+(?:\.\d+)?)Y)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)D)?$")
SEGMENT_LIKE = re.compile(r"(DataCenter|Consumer|Automotive|Industrial|Enterprise|Carrier|Networking|Cloud|EndCustomers|"
                          r"Distributors?|OEM|Government|Gaming|Embedded|Storage|Infrastructure|Market|Segment|Region|"
                          r"UnitedStates|Europe|Asia|China|Taiwan)", re.I)
ANON = re.compile(r"Customer\s*\d|RevenueCustomer|CustomerNumber|"
                  r"(^|:)(Customer|Client)s?([A-Z0-9]|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\w*Member$|"
                  r"(^|:)(Largest|Second|Third|Major|Significant|Direct|Indirect|Top|One|Two|Three)\w*Customers?\w*Member$|"
                  r"(^|:)\w*(Distributor|Reseller|Hyperscale|Partner)\w*Member$")
REVENUE_BENCH = ("RevenueFromContractWithCustomerProductAndServiceBenchmarkMember", "SalesRevenueNetMember",
                 "RevenueBenchmarkMember", "RevenueFromContractWithCustomerMember", "SalesRevenueGoodsNetMember")


def years(v):
    m = DUR.match((v or "").strip())
    if not m:
        return None
    y, mo, d = (Decimal(x) if x else Decimal(0) for x in m.groups())
    return (y + mo / 12 + d / 365).quantize(Decimal("0.0001"))


def _dims(s):
    return {a: m for a, m in json.loads(s or "[]")}


def useful_lives(con, groups, fiscal_years, as_of):
    """depreciation_life_published : durées publiées par classe (bornes basse, haute ou
    ponctuelle), dans les 10-K ; F7 compare à la publication précédente de même libellé."""
    df = con.execute("""SELECT fact_key, group_id, accession, form, period_end, dims, value_text, knowledge_date
                        FROM facts WHERE source = 'instance' AND concept = 'us-gaap:PropertyPlantAndEquipmentUsefulLife'
                          AND form LIKE '10-K%'""").fetchdf()
    labels = dict(con.execute("SELECT concept, any_value(label) FROM labels WHERE label_role = 'label' GROUP BY 1").fetchall())
    out = []
    prev = {}
    for r in df.sort_values(["group_id", "period_end"]).itertuples():
        d = _dims(r.dims)
        cls = d.get("us-gaap:PropertyPlantAndEquipmentByTypeAxis")
        rng = d.get("srt:RangeAxis")
        if not cls or len(d) > (2 if rng else 1):
            continue
        term = {"srt:MinimumMember": "lower", "srt:MaximumMember": "upper"}.get(rng, "point")
        y = years(r.value_text)
        if y is None:
            continue
        label = labels.get(cls, cls)
        key = (r.group_id, cls, term)
        flags = {"class_label": label}
        p = prev.get(key)
        if p is not None and p[1] < str(r.period_end) and y < p[0]:
            flags["decrease"] = {"class": label, "term": term, "from": float(p[0]), "to": float(y)}
        prev[key] = (y, str(r.period_end))
        fs = str(r.period_end)
        out.append(cell("depreciation_life_published", r.group_id, None, r.period_end, "as_known", as_of,
                        term=term, breakdown=cls, value=y, unit="years", flags=flags,
                        terms=[{"value": y, "fact_key": r.fact_key, "knowledge_date": str(r.knowledge_date),
                                "tier": "A", "is_tagged": True}]))
    # une même publication peut porter plusieurs dates (comparatifs) : clé unique par cellule
    seen, uniq = set(), []
    for c in out:
        k = (c["measure"], c["subject"], c["period_end"], c["term"], c["breakdown_key"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    return uniq


def leases_not_commenced(con, groups, years_by_group, as_of):
    """lease_not_commenced_bridge : ouverture et clôture sur les faits portant un membre
    standard « NotYetCommenced » ; ajouts et baux commencés non publiés (§5.2)."""
    totals = ("us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount", "us-gaap:OtherCommitment",
              "us-gaap:LesseeOperatingLeaseLiabilityPaymentsDue", "us-gaap:PurchaseObligation",
              "us-gaap:ContractualObligation")
    df = con.execute(f"""SELECT fact_key, group_id, concept, period_end, dims, value, knowledge_date, tier
                        FROM facts WHERE source = 'instance' AND value IS NOT NULL AND unit = 'USD'
                          AND (dims LIKE '%LeaseNotYetCommencedMember%') AND period_type = 'instant'
                          AND concept IN {totals}""").fetchdf()
    out = []
    for g in groups:
        sub = df[df["group_id"] == g]
        for fs, fe in years_by_group.get(g, []):
            def at(day):
                m = sub[sub["period_end"].astype(str) == str(day)]
                if m.empty:
                    return None
                r = m.sort_values("knowledge_date").iloc[-1]
                return {"value": Decimal(str(r["value"])), "fact_key": r["fact_key"],
                        "knowledge_date": str(r["knowledge_date"]), "tier": r["tier"], "is_tagged": True}
            close = at(fe)
            opening = at(pd.Timestamp(fs) - pd.Timedelta(days=1)) if fs else None
            for term, t in (("opening", opening), ("closing", close)):
                out.append(cell("lease_not_commenced_bridge", g, fs, fe, "as_known", as_of, term=term,
                                value=t["value"] if t else None, unit="USD", terms=[t] if t else [],
                                status="computed" if t else "not_determinable",
                                nd_reason=None if t else ("not_disclosed" if not sub.empty else "concept_unresolved")))
            for term in ("additions", "commenced"):
                out.append(cell("lease_not_commenced_bridge", g, fs, fe, "as_known", as_of, term=term,
                                status="not_determinable", nd_reason="not_disclosed"))
    return out


def concentration(con, groups, as_of):
    """customer_concentration_anonymous : parts publiées sur le revenu, par client anonyme,
    avec les bornes d'arrondi ; parts nommées pour named_edge_coverage."""
    df = con.execute("""SELECT fact_key, group_id, accession, form, period_start, period_end, dims, value, decimals,
                               decimals_inf, knowledge_date, tier
                        FROM facts WHERE source = 'instance' AND concept = 'us-gaap:ConcentrationRiskPercentage1'
                          AND value IS NOT NULL""").fetchdf()
    out, named = [], []
    for r in df.itertuples():
        d = _dims(r.dims)
        bench = d.get("us-gaap:ConcentrationRiskByBenchmarkAxis", "")
        typ = d.get("us-gaap:ConcentrationRiskByTypeAxis", "")
        cust = d.get("srt:MajorCustomersAxis")
        if not cust or not any(bench.endswith(b) for b in REVENUE_BENCH) or "Customer" not in typ:
            continue
        v = Decimal(str(r.value))
        if r.decimals_inf or r.decimals is None or pd.isna(r.decimals):
            lo = hi = v
            basis = None
        else:
            half = Decimal("0.5") * Decimal(10) ** (-int(r.decimals))
            lo, hi = v - half, v + half
            basis = "rounding"
        term = {"value": v, "fact_key": r.fact_key, "knowledge_date": str(r.knowledge_date), "tier": r.tier,
                "is_tagged": True}
        local = cust.split(":", 1)[-1]
        if SEGMENT_LIKE.search(local) and not ANON.search(local):
            continue  # marché ou catégorie de clients, pas un client
        if ANON.search(local):
            out.append(cell("customer_concentration_anonymous", r.group_id, r.period_start, r.period_end, "as_known",
                            as_of, breakdown=cust, value=v, lower=lo, upper=hi, bound_basis=basis,
                            status="bounded" if basis else "computed", unit="pure", terms=[term],
                            flags={"benchmark": bench, "form": r.form}))
        else:
            named.append({"group_id": r.group_id, "member": cust, "value": v, "period_start": r.period_start,
                          "period_end": r.period_end, "fact_key": r.fact_key, "form": r.form})
    seen, uniq = set(), []
    for c in out:
        k = (c["subject"], c["period_start"], c["period_end"], c["breakdown_key"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    return uniq, named
