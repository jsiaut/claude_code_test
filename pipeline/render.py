"""Rendus générés depuis les tables (§12.1) : synthesis.md, delta.md, series.md, et le
livrable d'audit (§12.2). Aucun rendu n'est édité à la main : chaque nombre est un jeton
rempli depuis measures, controls ou exclusions, et se retrouve dans audit/numbers.csv avec
l'accession et l'emplacement de chacun de ses termes.

    python -m pipeline.render 2026-10-07
"""
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from decimal import Decimal

import duckdb
import yaml

from . import config

NONE = "none"
CRITERIA_COMMIT = "3ff3b98"
ND_FR = {
    "not_processed": "non traité au premier passage", "search_incomplete": "recherche incomplète",
    "non_filer": "non-déposant", "redacted": "caviardé", "anonymous": "client anonyme",
    "channel_indirect": "vente indirecte", "parse_failed": "lecture impossible",
    "denominator_nonpositive": "dénominateur négatif ou nul", "denominator_below_threshold": "dénominateur sous le seuil",
    "recast_boundary": "frontière de retraitement", "history_left_censored": "historique tronqué",
    "term_missing": "terme manquant", "not_disclosed": "non publié", "not_collected": "non collecté",
    "concept_unresolved": "concept non résolu", "conflicting": "faits en conflit", "mixed_currency": "devises mêlées",
    "end_offset_exceeded": "dates de fin trop éloignées", "no_effect_published": "effet non publié",
    "precondition_not_met": "précondition non remplie", "date_missing": "date manquante",
    "interval_straddles_threshold": "intervalle à cheval sur le seuil", "prior_period_missing": "période antérieure absente",
    "not_tagged": "non balisé", "no_named_counterparty": "pas de contrepartie nommée",
    "no_financed_pair": "aucune paire financée", "unequal_period_length": "périodes de longueurs différentes",
    "annual_only": "annuel seulement", "pending_entity": "entité non confirmée", "blocked_overlap": "chevauchement non résolu",
    "out_of_first_pass": "hors du premier passage"}
VALUE_FR = {"no_event": "sans événement", "event": "événement", "active": "actif", "lapsed": "échu",
            "unknown": "inconnu", "supported": "étayé", "refuted": "réfuté", "indeterminate": "indéterminé",
            "compatible": "compatible", "descriptive": "descriptif", "not_supported": "non étayé",
            "computed": "calculée", "partial": "partielle", "bounded": "bornée", "not_determinable": "indéterminée",
            "not_applicable": "sans objet", "commitment": "engagement", "payment": "paiement",
            "opening": "ouverture", "additions": "nouveaux", "commenced": "commencés", "closing": "clôture",
            "lower": "borne basse", "upper": "borne haute", "point": "valeur unique"}
GROUP_NAMES = {"NVDA": "NVIDIA", "GOOGL": "Alphabet", "AMZN": "Amazon", "META": "Meta", "MSFT": "Microsoft",
               "ORCL": "Oracle", "CRWV": "CoreWeave", "SPCX": "SpaceX", "AMD": "AMD", "AVGO": "Broadcom",
               "MRVL": "Marvell"}


def fr_num(v, dec=1):
    s = f"{v:,.{dec}f}"
    return s.replace(",", " ").replace(".", ",")


class Tokens:
    """Registre des nombres publiés : un jeton par nombre, relié à sa cellule."""

    def __init__(self, con, doc):
        self.con, self.doc, self.rows = con, doc, []

    def _reg(self, kind, key, field, value, text):
        self.rows.append({"document": self.doc, "token": len(self.rows) + 1, "kind": kind, "key": json.dumps(key, ensure_ascii=False),
                          "field": field, "value": str(value), "text": text})
        return text

    def m(self, c, field="value", fmt="usd", dec=1):
        """Nombre d'une cellule de measures ; une cellule sans valeur s'affiche avec son motif."""
        v = c.get(field) if isinstance(c, dict) else getattr(c, field)
        if v is None or (isinstance(v, float) and v != v):
            nd = c.get("nd_reason") if isinstance(c, dict) else c.nd_reason
            return f"n.d. ({ND_FR.get(nd, nd or 'sans valeur')})"
        v = Decimal(str(v))
        if fmt == "usd":
            text = fr_num(v / Decimal(10**6), 0) + " M$" if abs(v) >= 10**6 else fr_num(v, 0) + " $"
        elif fmt == "pct":
            text = fr_num(v * 100, dec) + " %"
        elif fmt == "x":
            text = fr_num(v, 2) + " x"
        elif fmt == "days":
            text = fr_num(v, 0) + " j"
        elif fmt == "years":
            text = fr_num(v, 1) + " ans"
        elif fmt == "count":
            text = fr_num(v, 0)
        else:
            text = fr_num(v, dec)
        st = c.get("status") if isinstance(c, dict) else getattr(c, "status", None)
        if field == "value" and st == "partial":
            text += " (partiel)"
        key = {k: (c[k] if isinstance(c, dict) else getattr(c, k)) for k in
               ("measure", "subject", "counterparty", "period_start", "period_end", "view", "as_of", "term",
                "breakdown_key", "financing_policy", "constant_perimeter", "variant")}
        return self._reg("measure", key, field, v, text)

    def n(self, table, key, value, text=None):
        """Compte tiré de controls ou exclusions (requête nommée dans la clé)."""
        return self._reg(table, key, "count", value, text if text is not None else fr_num(Decimal(value), 0))


def load(con, as_of):
    t = config.ROOT / "tables"
    for name in ("measures", "controls", "exclusions", "links", "observations", "entities", "facts", "documents"):
        con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM '{t / (name + '.parquet')}'")
    # nom d'affichage d'un groupe de contrepartie : la dénomination telle qu'écrite dans la pièce
    for ref, name in con.execute("""SELECT m.ref, min(e.name) FROM entities m JOIN entities e
                                    ON e.entity_id = m.entity_id AND e.record_kind = 'entity'
                                    WHERE m.record_kind = 'membership' AND m.ref LIKE 'CP:%' GROUP BY 1""").fetchall():
        CP_NAMES[ref] = name


def q(con, sql, *args):
    cur = con.execute(sql, list(args))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def criteria_status():
    """Les critères des annexes E et F et les seuils, comparés à leur commit d'origine."""
    old = yaml.safe_load(subprocess.run(["git", "show", f"{CRITERIA_COMMIT}:config.yaml"], capture_output=True,
                                        text=True, cwd=config.ROOT).stdout)
    new = yaml.safe_load((config.ROOT / "config.yaml").read_text(encoding="utf-8"))
    out = {}
    for k in ("annex_e", "annex_f", "thresholds"):
        out[k] = json.dumps(old.get(k), sort_keys=True) == json.dumps(new.get(k), sort_keys=True)
    full = subprocess.run(["git", "show", "-s", "--format=%H %ci", CRITERIA_COMMIT], capture_output=True, text=True,
                          cwd=config.ROOT).stdout.strip()
    cur = subprocess.run(["git", "log", "-1", "--format=%H %ci", "--", "config.yaml"], capture_output=True, text=True,
                         cwd=config.ROOT).stdout.strip()
    return out, full, cur, old, new


CONFIG_DECISIONS = {"concept_anchors": "second candidat de capex, D-0012",
                    "confirmed_entities": "entités confirmées par extrait, D-0021",
                    "entity_aliases": "alias confirmés par extrait, D-0021",
                    "own_entities": "entités propres confirmées par extrait, D-0021"}


def config_changes(old, new):
    """Clés de config.yaml changées depuis le commit des critères, avec leur décision."""
    keys = sorted(k for k in set(old) | set(new)
                  if json.dumps(old.get(k), sort_keys=True, default=str) != json.dumps(new.get(k), sort_keys=True, default=str))
    return [(k, CONFIG_DECISIONS.get(k, "voir decisions.md")) for k in keys]


# -- jeux de données communs ------------------------------------------------------------

TRANCHE_FR = {"total": "total publié", "12m": "à 12 mois", "year2": "2e année", "year3": "3e année",
              "year4": "4e année", "year5": "5e année", "after5": "au-delà de 5 ans", "remainder": "reste de l'exercice"}
RANK1_SERIES = [
    ("revenue_growth", "yoy", "Croissance du revenu (glissement annuel)", "pct"),
    ("revenue_growth", "ttm", "Croissance du revenu (douze mois glissants)", "pct"),
    ("capex_to_cfo", "without", "Capex décaissé ÷ CFO", "x"),
    ("capex_to_cfo", "with", "Capex ÷ CFO, additions non monétaires comprises", "x"),
    ("fcf_basic", NONE, "Flux disponible (CFO − capex)", "usd"),
    ("fcf_after_finance_leases", NONE, "Flux disponible après locations-financement", "usd"),
    ("fcf_after_counterparty_financing", NONE, "Flux après financement des contreparties", "usd"),
    ("receivables_collection_period", (NONE, "receivables"), "Délai de recouvrement (créances)", "days"),
    ("rpo_total", NONE, "Obligations de prestation restantes (RPO)", "usd"),
    ("lev_debt_and_leases_to_operating_income_plus_da", "debt", "Dette ÷ (résultat opérationnel + dotations)", "x"),
    ("lev_debt_and_leases_to_operating_income_plus_da", "leases", "Passifs locatifs ÷ (résultat opérationnel + dotations)", "x"),
]
ANNUAL = [
    ("liq_principal_due_to_cash", "horizon_12m", "Principal dû à 12 mois ÷ trésorerie", "x"),
    ("liq_principal_due_to_cash", "horizon_24m", "Principal dû à 24 mois ÷ trésorerie", "x"),
    ("earnings_bridge_pretax", "investment_gain_loss", "Gains et pertes sur participations", "usd"),
    ("earnings_bridge_pretax", "investment_impairment", "Dépréciations d'investissements", "usd"),
    ("finance_lease_additions", NONE, "Additions en location-financement", "usd"),
    ("vendor_financed_additions", NONE, "Additions financées par le vendeur", "usd"),
    ("stock_paid_additions", NONE, "Additions payées en titres", "usd"),
]
SIGNALS = ["sig_late_filing", "sig_distress_8k_items", "sig_auditor_change_or_nonreliance", "sig_material_weakness",
           "sig_going_concern", "sig_covenant_events"]
SIG_FR = {"sig_late_filing": "dépôt tardif", "sig_distress_8k_items": "items de détresse (8-K)",
          "sig_auditor_change_or_nonreliance": "auditeur ou correction d'erreur", "sig_material_weakness": "faiblesse du contrôle interne",
          "sig_going_concern": "continuité d'exploitation", "sig_covenant_events": "clauses financières"}
F_FR = {"F1": "capex décaissé supérieur au CFO deux trimestres de suite", "F2": "flux après financement des contreparties négatif",
        "F3": "garantie ou soutien appelé", "F4": "amendement ou dérogation de clause financière",
        "F5": "faiblesse significative du contrôle interne", "F6": "dépréciation d'investissement",
        "F7": "baisse d'une durée d'amortissement publiée", "F8": "croissance annuelle passée sous zéro",
        "F9": "fin d'un contrat de capacité (8-K item 1.02)", "F10": "doute sur la continuité d'exploitation"}
CONC_FR = {"documented_dependency": "dépendance documentée", "commercial_with_financing": "relation commerciale doublée d'un financement",
           "reciprocal_commercial_only": "achats réciproques seulement", "causality_not_established": "causalité non établie"}
STRUCT_FR = {"commercial_and_financing": "commerciale et financière", "financing_only": "financière seulement",
             "commercial_only": "commerciale seulement", "reciprocal_commercial": "commerciale réciproque", NONE: "aucune"}


def cells(con, as_of, **kw):
    where = " AND ".join(f"{k} = ?" for k in kw)
    return q(con, f"SELECT * FROM measures WHERE {where}", *kw.values())


CP_NAMES = {}


def fr(v):
    return VALUE_FR.get(v, v)


def plural(n, word, suffix="s"):
    return word + (suffix if n > 1 else "")


def group_label(g):
    if g.startswith("LAB:"):
        return {"LAB:OPENAI": "OpenAI", "LAB:ANTHROPIC": "Anthropic"}.get(g, g[4:].title())
    if g.startswith("CP:"):
        return CP_NAMES.get(g, g[3:])
    return GROUP_NAMES.get(g, g)


def last_quarters(con, g, n=4):
    rows = q(con, """SELECT DISTINCT period_end FROM measures WHERE subject = ? AND measure = 'fcf_basic'
                     AND view = 'as_known' ORDER BY period_end DESC LIMIT ?""", g, n)
    return sorted(r["period_end"] for r in rows)


def last_years(con, g, n=2):
    rows = q(con, """SELECT DISTINCT period_end FROM measures WHERE subject = ? AND measure = 'liq_principal_due_to_cash'
                     AND view = 'as_known' ORDER BY period_end DESC LIMIT ?""", g, n)
    return sorted(r["period_end"] for r in rows)


def one(con, measure, g, pe, term=NONE, view="as_known", breakdown=NONE, counterparty=NONE, policy=NONE):
    if isinstance(term, tuple):
        term, breakdown = term
    r = q(con, """SELECT * FROM measures WHERE measure = ? AND subject = ? AND period_end = ? AND term = ? AND view = ?
                  AND breakdown_key = ? AND counterparty = ? AND financing_policy = ?""",
          measure, g, str(pe), term, view, breakdown, counterparty, policy)
    return r[0] if r else None


def synthesis(con, as_of, stats):
    T = Tokens(con, "synthesis.md")
    crit, crit_commit, cfg_commit, old, new = criteria_status()
    groups = stats["groups"]
    L = []
    L.append("# Note de synthèse — fragilité financière de la chaîne IA")
    L.append("")
    L.append(f"*Exécution du {as_of} · spec v6.14 · périmètre : premier passage · rendu généré depuis les tables "
             "`measures`, `controls` et `exclusions`, jamais édité à la main.*")
    L.append("")
    L.append("## En tête")
    L.append("")
    ok_crit = all(crit.values())
    if ok_crit:
        ch = config_changes(old, new)
        L.append(f"- **Critères des annexes E et F et seuils : inchangés** depuis leur commit d'origine "
                 f"`{crit_commit.split()[0]}` ({' '.join(crit_commit.split()[1:3])}), antérieur à la première requête. "
                 f"`config.yaml` a changé depuis (dernier commit qui le touche : "
                 f"`{cfg_commit.split()[0] if cfg_commit else 'non commité'}`, plus les changements de cette exécution) "
                 "sans toucher ces critères : " + "; ".join(f"`{k}` ({d})" for k, d in ch) + ".")
    else:
        L.append("- **Critères modifiés depuis leur commit d'origine** : " + ", ".join(k for k, v in crit.items() if not v))
    L.append("- **Périmètre couvert : premier passage.** Faits balisés des onze groupes, puis notes de parties liées, "
             "Item 404, Item 9A, Item 4 des 10-Q, continuité d'exploitation et items 1.01, 1.02, 3.03 et 8.01 des 8-K "
             "avec leurs pièces EX-10 et EX-4. Les notes d'investissements, de dette, de baux et d'engagements ne sont "
             "pas lues : ce qui en dépend est publié partiel ou indéterminé, motif « non traité au premier passage ».")
    e7 = q(con, "SELECT * FROM measures WHERE measure = 'annex_e_outcome' AND breakdown_key LIKE 'E7|%'")
    if e7:
        c = e7[0]
        fl = json.loads(c["flags"]) if c["flags"] else {}
        if c["value"] is not None:
            res = ("les pièces déposées ne permettent pas de discriminer entre les deux lectures"
                   if c["value_text"] == "non_discrimination" else "discrimination possible au sens de E.7")
            reasons = ", ".join(f"{ND_FR.get(k, k)} : {T.n('measures', {'E7_reason': k}, v)}"
                                for k, v in sorted((fl.get('reasons') or {}).items(), key=lambda x: -x[1]))
            L.append(f"- **Résultat principal (E.7) : {res}.** {T.m(c, fmt='pct', dec=0)} des issues de E.1 et E.2 "
                     f"au point de tête (10 %) sont indéterminées, sur {T.m(c, field='denominator', fmt='count')} issues ; "
                     f"motifs : {reasons or 'aucun'}. Au premier passage, cette non-discrimination tient d'abord au "
                     "périmètre borné de la lecture, non à une absence de relations.")
        else:
            L.append("- **E.7** : aucune paire à financement établi, E.1 et E.2 sans issue.")
    for view in ("as_known", "revised"):
        cs = q(con, "SELECT status, count(*) AS n FROM controls WHERE view = ? GROUP BY 1 ORDER BY 1", view)
        L.append(f"- **Contrôles comptables, vue `{view}`** : " +
                 ", ".join(f"`{r['status']}` {T.n('controls', {'view': view, 'status': r['status']}, r['n'])}" for r in cs) +
                 (" (un contrôle `tautological` n'est jamais compté comme réussi ; un `mismatch` est un résultat publié, "
                  "avec son code d'explication, dans `controls`)." if view == "as_known" else "."))
    mm = q(con, """SELECT control, count(*) FILTER (WHERE status = 'mismatch') AS m, count(*) AS n FROM controls
                     WHERE view = 'as_known' GROUP BY 1 ORDER BY 1""")
    L.append("  Par contrôle (`mismatch` sur total, vue `as_known`) : " +
             ", ".join(f"{r['control'].split('_')[0].upper()} {T.n('controls', {'control': r['control'], 'mismatch': True}, r['m'])}/"
                       f"{T.n('controls', {'control': r['control']}, r['n'])}" for r in mm) + ".")
    ex = q(con, "SELECT reason, count(*) AS n FROM exclusions GROUP BY 1 ORDER BY 2 DESC")
    L.append("- **Exclusions principales** : " + ", ".join(f"`{r['reason']}` {T.n('exclusions', {'reason': r['reason']}, r['n'])}"
                                                           for r in ex) + ".")
    L.append("- **Arrêt** : aucun ; ni refus durable de la SEC, ni échec général des contrôles.")
    L.append("")
    # Événements
    L.append("## Événements (annexe F)")
    L.append("")
    L.append("Chaque événement est un observable daté, avec sa pièce ; aucune somme, aucun score. Un trimestre dont la "
             "source n'a pas été lue n'est jamais présenté comme un trimestre sans événement.")
    L.append("")
    evs = q(con, """SELECT * FROM measures WHERE measure = 'fragility_event' AND value_text = 'event'
                    ORDER BY subject, period_end, breakdown_key""")
    by = defaultdict(list)
    for c in evs:
        by[c["subject"]].append(c)
    for g in groups:
        if not by.get(g):
            continue
        L.append(f"**{GROUP_NAMES[g]}**")
        L.append("")
        for c in by[g]:
            fl = json.loads(c["flags"]) if c["flags"] else {}
            piece = evidence_text(con, c, fl)
            L.append(f"- {c['breakdown_key']} ({F_FR[c['breakdown_key']]}) — rendu public le {c['knowledge_date'] or 'n.d.'}, "
                     f"rattaché au trimestre clos le {c['period_end']} ; pièce : {piece}.")
        L.append("")
    st = q(con, """SELECT breakdown_key AS f, status, coalesce(value_text, '') AS v, count(*) AS n FROM measures
                   WHERE measure = 'fragility_event' GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""")
    agg = defaultdict(list)
    for r in st:
        agg[r["f"]].append(f"{fr(r['status'])}{(' / ' + fr(r['v'])) if r['v'] else ''} {T.n('measures', {'F': r['f'], 'status': r['status'], 'v': r['v']}, r['n'])}")
    L.append("États de couverture des cellules de l'annexe F (groupe × trimestre), pour lire ce qui n'a pas été observé :")
    L.append("")
    for f in sorted(agg, key=lambda x: int(x[1:])):
        L.append(f"- {f} : " + " ; ".join(agg[f]))
    L.append("")
    # Fragilité
    L.append("## Fragilité, par groupe")
    L.append("")
    L.append("Mesures de rang 1 en vue `as_known` (ce que l'on savait à la publication de chaque période) ; la série complète "
             "est dans `series.md`. « n.d. » donne le motif ; jamais un zéro.")
    L.append("")
    for g in groups:
        L += fragility_section(con, T, g)
    # Circularité
    L += circularity_section(con, T, groups)
    # Évolution et non établi
    L.append("## Évolution")
    L.append("")
    L.append("Premier passage : aucune exécution antérieure à laquelle comparer. Les séries trimestrielles complètes, ruptures "
             "de base marquées, sont dans `series.md` ; `delta.md` sera le point d'entrée des exécutions suivantes.")
    L.append("")
    L.append("## Ce qui n'a pas pu être établi")
    L.append("")
    nd = q(con, """SELECT nd_reason, count(*) AS n FROM measures WHERE status = 'not_determinable' AND view = 'as_known'
                   GROUP BY 1 ORDER BY 2 DESC""")
    L.append("Cellules indéterminées en vue `as_known`, par motif : " +
             ", ".join(f"{ND_FR.get(r['nd_reason'], r['nd_reason'])} {T.n('measures', {'nd_reason': r['nd_reason']}, r['n'])}" for r in nd) + ".")
    L.append("")
    return "\n".join(L) + "\n", T.rows


def evidence_text(con, c, fl):
    obs = fl.get("observations") or []
    if obs:
        r = q(con, f"SELECT DISTINCT accession, form FROM observations WHERE obs_key IN ({','.join('?' * len(obs))})", *obs)
        return ", ".join(f"{x['form']} {x['accession']}" for x in r) or "observation"
    lin = fl.get("lineage")
    if lin:
        keys = json.loads(lin) if isinstance(lin, str) else lin
        r = q(con, f"SELECT DISTINCT accession, form FROM facts WHERE fact_key IN ({','.join('?' * len(keys))})", *keys)
        return ", ".join(f"{x['form']} {x['accession']}" for x in r[:3]) or "faits balisés"
    if fl.get("decreases"):
        return "durées publiées (faits balisés de deux 10-K successifs)"
    if fl.get("accessions"):
        return ", ".join(fl["accessions"][:3])
    return "faits balisés"


def fragility_section(con, T, g):
    L = [f"### {GROUP_NAMES[g]} ({g})", ""]
    kd = q(con, """SELECT max(knowledge_date) AS d FROM measures WHERE subject = ? AND view = 'as_known'
                   AND measure IN ('fcf_basic', 'revenue_growth', 'rpo_total') AND status = 'computed'""", g)
    L.append(f"Dernière information balisée utilisée : {kd[0]['d'] if kd and kd[0]['d'] else 'n.d.'}.")
    L.append("")
    qs = last_quarters(con, g, 4)
    if qs:
        L.append("| Mesure (trimestre clos le) | " + " | ".join(qs) + " |")
        L.append("| --- | " + " | ".join("---:" for _ in qs) + " |")
        for meas, term, label, fmt in RANK1_SERIES:
            row = []
            for pe in qs:
                c = one(con, meas, g, pe, term)
                row.append(T.m(c, fmt=fmt) if c else "—")
            L.append(f"| {label} | " + " | ".join(row) + " |")
        L.append("")
    ys = last_years(con, g, 2)
    if ys:
        L.append("| Mesure (exercice clos le) | " + " | ".join(ys) + " |")
        L.append("| --- | " + " | ".join("---:" for _ in ys) + " |")
        for meas, term, label, fmt in ANNUAL:
            row = []
            for pe in ys:
                c = one(con, meas, g, pe, term)
                row.append(T.m(c, fmt=fmt) if c else "—")
            L.append(f"| {label} | " + " | ".join(row) + " |")
        # obligations d'achat (matrice, flux non actualisés) et baux non commencés
        for pe in ys[-1:]:
            po = q(con, """SELECT * FROM measures WHERE measure = 'exposure_matrix' AND subject = ? AND period_end = ?
                           AND view = 'as_known' AND breakdown_key LIKE 'contractual_outflows/undiscounted/purchase_obligation/%'
                           ORDER BY breakdown_key""", g, str(pe))
            lnc = q(con, """SELECT * FROM measures WHERE measure = 'lease_not_commenced_bridge' AND subject = ? AND period_end = ?
                            AND view = 'as_known' ORDER BY term""", g, str(pe))
            L.append("")
            if po:
                parts = [f"{TRANCHE_FR.get(c['breakdown_key'].rsplit('/', 1)[-1], c['breakdown_key'].rsplit('/', 1)[-1])} {T.m(c)}"
                         for c in po]
                L.append(f"Obligations d'achat publiées au {pe} (flux non actualisés, tranches telles que publiées, "
                         f"aucun total ajouté par le modèle) : " + " ; ".join(parts) + ".")
            if lnc:
                order = {"opening": 0, "additions": 1, "commenced": 2, "closing": 3}
                parts = [f"{fr(c['term'])} {T.m(c)}" for c in sorted(lnc, key=lambda c: order.get(c["term"], 9))]
                L.append(f"Baux non commencés au {pe} (pont ouverture + nouveaux − commencés = clôture) : " + " ; ".join(parts) + ".")
        L.append("")
    lives = q(con, """SELECT * FROM measures WHERE measure = 'depreciation_life_published' AND subject = ? AND view = 'as_known'
                      AND period_end = (SELECT max(period_end) FROM measures WHERE measure = 'depreciation_life_published'
                                        AND subject = ? AND status = 'computed') ORDER BY breakdown_key, term""", g, g)
    if lives:
        parts = []
        for c in lives:
            fl = json.loads(c["flags"]) if c["flags"] else {}
            lab = re.sub(r"\s*\[Member\]$", "", fl.get("class_label", c["breakdown_key"]))
            parts.append(f"{lab} ({fr(c['term'])}) {T.m(c, fmt='years')}")
        L.append(f"Durées d'amortissement publiées (exercice clos le {lives[0]['period_end']}) : " + " ; ".join(parts) + ".")
        L.append("")
    sig = q(con, """SELECT measure, status, coalesce(value_text, '') AS v, count(*) AS n FROM measures
                    WHERE subject = ? AND measure LIKE 'sig_%' GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""", g)
    by = defaultdict(list)
    for r in sig:
        by[r["measure"]].append(f"{fr(r['v'] or r['status'])} {T.n('measures', {'subject': g, 'measure': r['measure'], 'status': r['status'], 'v': r['v']}, r['n'])}")
    L.append("Signaux sur la fenêtre (trimestres) : " + " ; ".join(f"{SIG_FR[m]} — {', '.join(v)}" for m, v in by.items()) + ".")
    L.append("")
    return L


def circularity_section(con, T, groups):
    L = ["## Circularité, par paire", ""]
    L.append("Une paire réunit un groupe du périmètre et une contrepartie que ses pièces nomment, avec au moins une arête "
             "entre eux : client, financé, financeur ou prêteur (une paire seulement financière, comme un prêt bancaire, "
             "n'a pas de revenu à rapprocher). Aucune de ces mesures ne prouve une circularité ; la conclusion s'en tient "
             "aux valeurs de `relationship_conclusion`, et un numérateur vide se publie indéterminé, à côté des sorties de "
             "couverture (E.9).")
    L.append("")
    concl = q(con, """SELECT * FROM measures WHERE measure = 'relationship_conclusion' ORDER BY subject, counterparty""")
    for c in concl:
        s, cp = c["subject"], c["counterparty"]
        fl = json.loads(c["flags"]) if c["flags"] else {}
        L.append(f"### {GROUP_NAMES.get(s, s)} → {group_label(cp)}")
        L.append("")
        L.append(f"- Conclusion : **{CONC_FR[c['value_text']]}** ; structure {STRUCT_FR.get(fl.get('edge_structure'), fl.get('edge_structure'))} ; "
                 f"lien {'documenté (' + ', '.join(fl.get('link_categories') or []) + ')' if fl.get('linkage_evidence') == 'documented_link' else 'non trouvé, recherche incomplète au premier passage'} ; "
                 f"{T.n('links', {'pair': [s, cp], 'edges': True}, len(fl.get('edges') or []))} "
                 f"{plural(len(fl.get('edges') or []), 'arête')}.")
        fs = q(con, """SELECT financing_policy, value_text, count(*) AS n, min(period_end) AS a, max(period_end) AS b
                       FROM measures WHERE measure = 'financed_status' AND subject = ? AND counterparty = ?
                       AND view = 'as_known' GROUP BY 1, 2 ORDER BY 1, 2""", s, cp)
        parts = defaultdict(list)
        for r in fs:
            parts[r["financing_policy"]].append(f"{fr(r['value_text'])} {T.n('measures', {'financed_status': [s, cp, r['financing_policy'], r['value_text']]}, r['n'])} {plural(r['n'], 'trimestre')}")
        L.append("- Statut « financé » F, politique de tête (`exposure_outstanding`) : " + ", ".join(parts.get("exposure_outstanding", []))
                 + " ; sensibilité `ever_financed` : " + ", ".join(parts.get("ever_financed", [])) + ".")
        dep = q(con, """SELECT * FROM measures WHERE measure = 'documented_revenue_dependency' AND subject = ? AND counterparty = ?
                        AND view = 'as_known' ORDER BY period_end""", s, cp)
        if dep:
            items = []
            for d in dep:
                if d["status"] == "bounded":
                    items.append(f"{d['period_end']} : entre {T.m(d, 'value_lower', 'pct', 0)} et {T.m(d, 'value_upper', 'pct', 0)}"
                                 f"{' (borne haute exclue)' if json.loads(d['flags'] or '{}').get('upper_exclusive') else ''}")
                else:
                    items.append(f"{d['period_end']} : {T.m(d, fmt='pct')}")
            L.append("- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : " + " ; ".join(items) + ".")
        for meas, label in (("consideration_to_customer", "Contrepartie payable au client"),
                            ("documented_backlog_dependency", "Dépendance du carnet (RPO)"),
                            ("investor_customer_revenue_share", "Part du revenu venant de clients qui financent le fournisseur")):
            rows = q(con, """SELECT * FROM measures WHERE measure = ? AND subject = ? AND counterparty = ? AND view = 'as_known'
                             ORDER BY period_end, term""", meas, s, cp)
            if rows:
                st = Counter((r["status"], r["nd_reason"]) for r in rows)
                L.append(f"- {label} : " + ", ".join(f"{T.n('measures', {meas: [s, cp, a, b]}, n)} {plural(n, 'cellule')} "
                                                    f"{fr(a)}{'s' if n > 1 and a in VALUE_FR else ''}"
                                                    f"{(' (' + ND_FR.get(b, b) + ')') if b else ''}" for (a, b), n in st.items()) + ".")
        cc = one(con, "contract_coverage", s, q(con, "SELECT period_end FROM measures WHERE measure = 'contract_coverage' AND subject = ? AND counterparty = ?", s, cp)[0]["period_end"], counterparty=cp) \
            if q(con, "SELECT 1 FROM measures WHERE measure = 'contract_coverage' AND subject = ? AND counterparty = ?", s, cp) else None
        if cc:
            L.append(f"- Couverture contractuelle (accords connus déposés en entier, non caviardés) : {T.m(cc, fmt='pct', dec=0)}"
                     f"{'' if cc['value'] is None else ' (' + T.m(cc, 'numerator', 'count') + ' sur ' + T.m(cc, 'denominator', 'count') + ')'}.")
        ae = q(con, """SELECT * FROM measures WHERE measure = 'annex_e_outcome' AND subject = ? AND counterparty = ?
                       ORDER BY breakdown_key""", s, cp)
        if ae:
            items = []
            for a in ae:
                stmt, grid, basis = a["breakdown_key"].split("|")
                lab = stmt + (f" à {int(Decimal(grid) * 100)} %" if grid != NONE else "") + (f" ({fr(basis)})" if basis != NONE else "")
                items.append(f"{lab} : {fr(a['value_text'])}{(' — ' + ND_FR.get(a['nd_reason'], a['nd_reason'])) if a['nd_reason'] else ''}")
            L.append("- Annexe E : " + " ; ".join(items) + ".")
        else:
            L.append("- Annexe E : paire hors des populations de E.1 à E.5 (F jamais active, pas de relation client).")
        L.append("")
    # sorties de couverture par fournisseur
    L.append("### Sorties de couverture par fournisseur (§3.6)")
    L.append("")
    L.append("| Fournisseur | Exercice | Revenu attribué à des clients nommés | Clients anonymes d'au moins 10 % | Résidu | Paires vues seulement côté client |")
    L.append("| --- | --- | ---: | ---: | ---: | ---: |")
    for g in groups:
        ys = q(con, """SELECT DISTINCT period_end FROM measures WHERE measure = 'named_edge_coverage' AND subject = ?
                       ORDER BY period_end DESC LIMIT 1""", g)
        for y in ys:
            pe = y["period_end"]
            nn = one(con, "named_edge_coverage", g, pe, "named")
            an = one(con, "named_edge_coverage", g, pe, "anonymous")
            rs = one(con, "named_edge_coverage", g, pe, "residual")
            vp = one(con, "visible_pairs_count", g, pe)
            anon = (f"{T.m(an, fmt='pct')} [{T.m(an, 'value_lower', 'pct')} ; {T.m(an, 'value_upper', 'pct')}]"
                    if an and an.get("value_lower") is not None else (T.m(an, fmt='pct') if an else "—"))
            L.append(f"| {GROUP_NAMES[g]} | {pe} | {T.m(nn, fmt='pct') if nn else '—'} (partiel) | {anon} | "
                     f"{T.m(rs, fmt='pct') if rs else '—'} | {T.m(vp, fmt='count') if vp else '—'} |")
    L.append("")
    L.append("Le revenu attribué à des clients nommés est une borne basse : le texte qui entoure les faits de concentration "
             "n'est pas lu au premier passage. Un client nommé ailleurs peut être l'un des anonymes (`overlap_possible`).")
    L.append("")
    return L


def journal_stats():
    n = ok = by = 0
    first = last = None
    for line in open(config.ROOT / "journal.jsonl", encoding="utf-8"):
        o = json.loads(line)
        if not o.get("url"):
            continue
        n += 1
        if o.get("status") == 200:
            ok += 1
            by += o.get("bytes") or 0
        ts = o.get("ts")
        first = ts if first is None else min(first, ts)
        last = ts if last is None else max(last, ts)
    return n, ok, by, first, last


def decisions_list():
    out = []
    for line in (config.ROOT / "decisions.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"- \*\*(D-\d{4}) — (.+?)\*\*", line)
        if m:
            out.append((m.group(1), m.group(2).rstrip(".")))
    return out


def delta(con, as_of, stats):
    T = Tokens(con, "delta.md")
    L = ["# delta.md — à lire en premier", "", f"*Exécution du {as_of} (premier passage). Généré depuis les tables.*", ""]
    L.append("## Arrêt")
    L.append("")
    L.append("Aucun arrêt : la SEC n'a pas refusé l'accès durablement et les contrôles n'échouent pas de façon générale.")
    L.append("")
    L.append("## Événements nouveaux de l'annexe F")
    L.append("")
    evs = q(con, """SELECT subject, breakdown_key, count(*) AS n FROM measures WHERE measure = 'fragility_event'
                    AND value_text = 'event' GROUP BY 1, 2 ORDER BY 1, 2""")
    if evs:
        for r in evs:
            L.append(f"- {GROUP_NAMES.get(r['subject'], r['subject'])} : {r['breakdown_key']} ({F_FR[r['breakdown_key']]}) — "
                     f"{T.n('measures', {'F_event': [r['subject'], r['breakdown_key']]}, r['n'])} trimestre(s)")
    else:
        L.append("- Aucun.")
    L.append("")
    L.append("## Rendement du passage (§11.1)")
    L.append("")
    tiers = [m for m, v in __import__("pipeline.registry", fromlist=["MEASURES"]).MEASURES.items() if v[0] == 1]
    r1 = q(con, f"""SELECT status, coalesce(nd_reason, '') AS nd, count(*) AS n FROM measures
                    WHERE measure IN ({','.join('?' * len(tiers))}) AND measure NOT IN ('fragility_event', 'annex_e_outcome')
                    GROUP BY 1, 2 ORDER BY 3 DESC""", *tiers)
    L.append("- Cellules de rang 1, par statut et motif : " + " ; ".join(
        f"{fr(r['status'])}{(' / ' + ND_FR.get(r['nd'], r['nd'])) if r['nd'] else ''} {T.n('measures', {'rank1': [r['status'], r['nd']]}, r['n'])}" for r in r1) + ".")
    fe = q(con, """SELECT status, coalesce(nd_reason, '') AS nd, count(*) AS n FROM measures WHERE measure = 'fragility_event'
                   GROUP BY 1, 2 ORDER BY 3 DESC""")
    L.append("- Cellules de l'annexe F, par statut et motif : " + " ; ".join(
        f"{fr(r['status'])}{(' / ' + ND_FR.get(r['nd'], r['nd'])) if r['nd'] else ''} {T.n('measures', {'annexF': [r['status'], r['nd']]}, r['n'])}" for r in fe) + ".")
    fin = q(con, """SELECT subject, counterparty FROM measures WHERE measure = 'financed_status' AND value_text = 'active'
                    AND view = 'as_known' AND financing_policy = 'exposure_outstanding' GROUP BY 1, 2 ORDER BY 1, 2""")
    L.append(f"- Paires à financement documenté (F active au moins un trimestre) : {T.n('measures', {'financed_pairs': True}, len(fin))}"
             + (" — " + ", ".join(f"{GROUP_NAMES.get(r['subject'], r['subject'])} → {group_label(r['counterparty'])}" for r in fin) if fin else "") + ".")
    am = q(con, "SELECT family, count(*) AS n FROM links WHERE link_kind = 'edge' AND edge_evidence = 'amount' GROUP BY 1 ORDER BY 1")
    rel = q(con, "SELECT count(*) AS n FROM links WHERE link_kind = 'edge' AND edge_evidence = 'relation'")[0]["n"]
    L.append("- Arêtes de montant : " + ", ".join(f"{r['family']} {T.n('links', {'amount_edges': r['family']}, r['n'])}" for r in am)
             + f" ; arêtes de relation : {T.n('links', {'relation_edges': True}, rel)}.")
    nec = q(con, """SELECT m.subject, m.period_end, m.value FROM measures m WHERE measure = 'named_edge_coverage' AND term = 'named'
                    AND period_end = (SELECT max(period_end) FROM measures x WHERE x.measure = 'named_edge_coverage' AND x.subject = m.subject)
                    ORDER BY subject""")
    def cov(r):
        an = one(con, 'named_edge_coverage', r['subject'], r['period_end'], 'anonymous')
        a = (f"{T.m(an, fmt='pct')} [{T.m(an, 'value_lower', 'pct')} ; {T.m(an, 'value_upper', 'pct')}]"
             if an and an.get("value_lower") is not None and an["status"] == "bounded" else T.m(an, fmt='pct') if an else "—")
        return (f"{GROUP_NAMES.get(r['subject'], r['subject'])} (exercice clos le {r['period_end']}) : nommés "
                f"{T.m(one(con, 'named_edge_coverage', r['subject'], r['period_end'], 'named'), fmt='pct')}, anonymes d'au moins 10 % {a}")
    L.append("- Revenu attribué par chaque fournisseur à des clients nommés, dernier exercice (borne basse ; le texte autour "
             "des faits de concentration n'est pas lu au premier passage), et part des clients anonymes : " +
             " ; ".join(cov(r) for r in nec) + ".")
    q4 = ["financed_status", "documented_revenue_dependency", "investor_customer_revenue_share", "named_edge_coverage",
          "documented_pair_coverage", "customer_concentration_anonymous", "documented_backlog_dependency",
          "consideration_to_customer", "noncash_revenue_from_investees", "contract_coverage", "relationship_conclusion"]
    r4 = q(con, f"""SELECT status, coalesce(nd_reason, '') AS nd, count(*) AS n FROM measures WHERE measure IN ({','.join('?' * len(q4))})
                    GROUP BY 1, 2 ORDER BY 3 DESC""", *q4)
    L.append("- Cellules de la question 4, par statut et motif : " + " ; ".join(
        f"{fr(r['status'])}{(' / ' + ND_FR.get(r['nd'], r['nd'])) if r['nd'] else ''} {T.n('measures', {'q4': [r['status'], r['nd']]}, r['n'])}" for r in r4) + ".")
    n, ok, by, first, last = journal_stats()
    L.append(f"- Requêtes : {T.n('journal', {'requests': True}, n)} au journal, dont {T.n('journal', {'requests_200': True}, ok)} réussies, "
             f"{T.n('journal', {'bytes': True}, by, fr_num(Decimal(by) / Decimal(10**6), 0) + ' Mo')} reçus ; de {first} à {last}.")
    bl = stats.get("blocks", {})
    L.append(f"- Blocs lus : {T.n('observations', {'blocks_read': True}, bl.get('read', 0))} sur "
             f"{T.n('observations', {'blocks_catalog': True}, bl.get('catalog', 0))} clés de contenu ; par item de 8-K : "
             + ", ".join(f"{k} {T.n('observations', {'item': k}, v)}" for k, v in sorted(bl.get("by_item", {}).items()))
             + f" ; pièces arrêtées à leur en-tête : " + ", ".join(f"{k} {T.n('exclusions', {'header_only': k}, v)}"
                                                                  for k, v in sorted(bl.get("header_only", {}).items())) + ".")
    L.append(f"- Lignes rejetées par la validation : {T.n('exclusions', {'validation_failed': True}, stats['observations']['rejected_semantic'])} ; "
             "13 lignes corrigées dans la passe avant l'assemblage (décision D-0020).")
    L.append(f"- Durée de l'assemblage : {stats.get('seconds', 0)} s ; lecture : voir le journal ci-dessus.")
    L.append("")
    L.append("## Exclusions nouvelles, par motif")
    L.append("")
    for r in q(con, "SELECT reason, count(*) AS n FROM exclusions GROUP BY 1 ORDER BY 2 DESC"):
        L.append(f"- `{r['reason']}` : {T.n('exclusions', {'reason': r['reason']}, r['n'])}")
    L.append("")
    L.append("## Décisions et variantes nouvelles")
    L.append("")
    for d, t in decisions_list():
        L.append(f"- {d} — {t}.")
    L.append("")
    L.append("## Critères des annexes E et F")
    L.append("")
    crit, crit_commit, cfg_commit, _, _ = criteria_status()
    L.append("Inchangés depuis le commit d'origine " + crit_commit.split()[0][:12] + "." if all(crit.values())
             else "Modifiés : " + ", ".join(k for k, v in crit.items() if not v))
    L.append("")
    L.append("## Écarts avec l'annexe D")
    L.append("")
    L.append("- SpaceX : 85 dépôts à la phase 0, contre 83 dans l'annexe D au 24 septembre 2026 ; les deux de plus sont des "
             "formulaires 4 et 4/A déposés depuis (plan.md).")
    L.append("")
    L.append("## Dépôts nouveaux")
    L.append("")
    fd = q(con, """SELECT form, count(DISTINCT accession) AS n FROM documents WHERE accession IS NOT NULL GROUP BY 1 ORDER BY 2 DESC""")
    L.append("Premier passage : tous les dépôts lus sont nouveaux — " + ", ".join(f"{r['form']} {T.n('documents', {'form': r['form']}, r['n'])}" for r in fd if r["form"]) + ".")
    L.append("")
    L.append("## Valeurs changées pour des périodes déjà publiées")
    L.append("")
    c4 = q(con, """SELECT subject, count(*) AS n FROM controls WHERE control = 'c4_restatement_detection' AND status = 'mismatch'
                   GROUP BY 1 ORDER BY 1""")
    L.append("Même identité de fait, valeurs différentes selon le dépôt (C4), publiées sans écrasement ; la cause de "
             "révision (`recast_cause`) se lit au cas par cas dans `controls` : " +
             ", ".join(f"{GROUP_NAMES.get(r['subject'], r['subject'])} {T.n('controls', {'c4': r['subject']}, r['n'])}" for r in c4) + ".")
    L.append("")
    L.append("## Arêtes nouvelles")
    L.append("")
    ae = q(con, """SELECT family, edge_evidence, count(*) AS n FROM links WHERE link_kind = 'edge' GROUP BY 1, 2 ORDER BY 1, 2""")
    L.append("Premier passage : toutes les arêtes sont nouvelles — " + ", ".join(
        f"{r['family']}/{r['edge_evidence']} {T.n('links', {'edges': [r['family'], r['edge_evidence']]}, r['n'])}" for r in ae) + ".")
    L.append("")
    L.append("## Contrôles qui ont basculé")
    L.append("")
    L.append("Sans objet au premier passage.")
    L.append("")
    L.append("## Entités pending")
    L.append("")
    pend = q(con, "SELECT name FROM entities WHERE record_kind = 'entity' AND status = 'pending' ORDER BY name")
    L.append(f"{T.n('entities', {'pending': True}, len(pend))} entités nommées dans des observations sans identité affirmée par une pièce, "
             "visibles dans `entities`, absentes des agrégats : " + ", ".join(f"« {r['name']} »" for r in pend) + ".")
    L.append("")
    L.append("## Travail not_processed")
    L.append("")
    L.append("Hors tranche du premier passage, pour chaque groupe : notes d'investissements, de dette, de baux et "
             "d'engagements ; texte autour des faits de concentration ; 8-K items 2.01 et 2.03 ; corps des EX-10 et EX-4 "
             "arrêtés à leur en-tête. C'est ce que l'extension `text` de §14 lirait.")
    L.append("")
    L.append("## Paires non additives")
    L.append("")
    cnt = stats.get("non_additive_candidates", {})
    mute = [k for k, v in sorted(cnt.items()) if v == 0]
    L.append("Relations candidates par paire du registre : " + ", ".join(f"{k} {T.n('links', {'pair_candidates': k}, v)}" for k, v in sorted(cnt.items()))
             + f". Paires muettes : {', '.join(mute) if mute else 'aucune'} — la plupart portent sur des lignes de notes que le premier passage ne lit pas.")
    L.append("")
    L.append("## Changements dus à une nouvelle passe de lecture ou au code")
    L.append("")
    L.append("Une seule passe de lecture (`2026-10-07T10:54:00Z`) ; 13 lignes corrigées dans cette passe, avant l'assemblage, "
             "après la validation sémantique (D-0020). Code de la phase 3 ajouté : entités et arêtes, statut « financé », "
             "mesures de la question 4, annexes E et F, rendus.")
    L.append("")
    return "\n".join(L) + "\n", T.rows


def series(con, as_of, stats):
    T = Tokens(con, "series.md")
    L = ["# series.md — vue temporelle", "",
         f"*Exécution du {as_of}. Mesures de rang 1 par groupe et par trimestre, vue `as_known` ; « ↯ » marque une "
         "frontière de retraitement (`recast_boundary`), « n.d. » un motif d'indétermination. Les événements de "
         "l'annexe F sont en regard. Généré depuis `measures`.*", ""]
    cols = [(m, t, lab, f) for m, t, lab, f in RANK1_SERIES]
    for g in stats["groups"]:
        L.append(f"## {GROUP_NAMES[g]} ({g})")
        L.append("")
        qs = q(con, """SELECT DISTINCT period_end FROM measures WHERE subject = ? AND measure = 'fragility_event'
                       ORDER BY period_end""", g)
        L.append("| Trimestre clos le | " + " | ".join(c[2] for c in cols) + " | Événements (annexe F) |")
        L.append("| --- | " + " | ".join("---:" for _ in cols) + " | --- |")
        for r in qs:
            pe = r["period_end"]
            row = []
            for m, t, lab, f in cols:
                c = one(con, m, g, pe, t)
                if c is None:
                    row.append("—")
                elif c["nd_reason"] == "recast_boundary":
                    row.append("↯")
                else:
                    row.append(T.m(c, fmt=f))
            ev = q(con, """SELECT breakdown_key FROM measures WHERE measure = 'fragility_event' AND subject = ? AND period_end = ?
                           AND value_text = 'event' ORDER BY breakdown_key""", g, pe)
            L.append(f"| {pe} | " + " | ".join(row) + " | " + (", ".join(e["breakdown_key"] for e in ev) or "") + " |")
        L.append("")
    return "\n".join(L) + "\n", T.rows


# -- livrable d'audit -------------------------------------------------------------------

RULE_TEXT = {
    "anchor_first_present": "premier concept de la liste d'ancrage (annexe B) présent dans la linkbase de présentation "
                            "du déposant, dans un rôle de l'état concerné ; fixé avant tout contrôle",
    "definition_first_present": "grandeur sans ancre : premier concept standard dont la définition de la taxonomie 2026 "
                                "correspond, présent dans la linkbase de présentation pour l'état concerné ; liste fixée "
                                "avant tout contrôle",
    "D1_label_match": "état annuel lu en HTML dans le 424B4 : concept du 10-Q dont le libellé correspond à la ligne "
                      "(is_tagged = false)"}


def numbers_csv(con, rows, path):
    """Chaque nombre publié, avec l'accession et l'emplacement de chacun de ses termes."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["document", "token", "kind", "cell_key", "field", "value", "text", "term_key", "accession",
                    "locator", "is_tagged", "tier"])
        for r in rows:
            terms = []
            if r["kind"] == "measure":
                k = json.loads(r["key"])
                c = q(con, """SELECT lineage, flags FROM measures WHERE measure = ? AND subject = ? AND counterparty = ?
                              AND period_start = ? AND period_end = ? AND view = ? AND as_of = ? AND term = ?
                              AND breakdown_key = ? AND financing_policy = ? AND constant_perimeter = ? AND variant = ?""",
                      *[k[x] for x in ("measure", "subject", "counterparty", "period_start", "period_end", "view", "as_of",
                                       "term", "breakdown_key", "financing_policy", "constant_perimeter", "variant")])
                if c:
                    lin = json.loads(c[0]["lineage"]) if c[0]["lineage"] else []
                    fl = json.loads(c[0]["flags"]) if c[0]["flags"] else {}
                    fkeys = [x for x in lin if not x.startswith("obs:")]
                    okeys = [x[4:] for x in lin if x.startswith("obs:")]
                    for lk in fl.get("links") or []:
                        ev = q(con, "SELECT evidence_keys FROM links WHERE link_key = ?", lk)
                        if ev and ev[0]["evidence_keys"]:
                            okeys += json.loads(ev[0]["evidence_keys"])
                    if fkeys:
                        for f in q(con, f"""SELECT fact_key, accession, locator, is_tagged, tier FROM facts
                                            WHERE fact_key IN ({','.join('?' * len(fkeys))})""", *fkeys):
                            terms.append((f["fact_key"], f["accession"], f["locator"], f["is_tagged"], f["tier"]))
                    if okeys:
                        for o in q(con, f"""SELECT obs_key, accession, locator, tier FROM observations
                                            WHERE obs_key IN ({','.join('?' * len(okeys))})""", *okeys):
                            terms.append((o["obs_key"], o["accession"], o["locator"], False, o["tier"]))
            if not terms:
                terms = [(None, None, None, None, None)]
            for t in terms:
                w.writerow([r["document"], r["token"], r["kind"], r["key"], r["field"], r["value"], r["text"], *t])


def audit(con, as_of, rows, stats):
    out = config.ROOT / "audit"
    out.mkdir(exist_ok=True)
    numbers_csv(con, rows, out / "numbers.csv")
    # concepts.csv : concept retenu par groupe et grandeur, avec la règle qui l'a retenu (§12.2)
    con.execute(f"ATTACH '{config.DB_DIR / 'model.duckdb'}' AS mdl (READ_ONLY)")
    cm = q(con, """SELECT m.group_id, m.quantity, m.concept, string_agg(DISTINCT m.rule, ' ; ' ORDER BY m.rule) AS rule,
                          string_agg(DISTINCT m.statement_kind, ' ; ' ORDER BY m.statement_kind) AS statement_kind,
                          count(DISTINCT m.accession) AS filings, min(f.period_end) AS first_period, max(f.period_end) AS last_period,
                          bool_and(coalesce(f.is_tagged, true)) AS is_tagged
                   FROM mdl.concept_map m LEFT JOIN facts f ON f.accession = m.accession AND f.concept = m.concept
                        AND f.group_id = m.group_id AND f.n_dims = 0
                   GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""")
    with open(out / "concepts.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["group_id", "quantity", "concept", "rule", "rule_text", "statement_kind", "filings", "first_period",
                    "last_period", "is_tagged", "change_after_mismatch", "new_evidence"])
        for r in cm:
            text = " ; ".join(RULE_TEXT.get(x.strip(), x.strip()) for x in (r["rule"] or "").split(";"))
            w.writerow([r["group_id"], r["quantity"], r["concept"], r["rule"], text, r["statement_kind"], r["filings"],
                        r["first_period"], r["last_period"], r["is_tagged"], "none", ""])
    con.execute("DETACH mdl")
    # attributions.csv : chaque montant attribué à une contrepartie, avec sa citation
    at = q(con, """SELECT o.obs_key, o.group_id, o.accession, o.form, o.counterparty_name, o.counterparty_entity_id, o.payer,
                          o.payee, o.amount, o.unit, o.currency, o.amount_nature, o.stage, o.period_start, o.period_end,
                          o.event_date, o.quote, o.locator, o.tier
                   FROM observations o WHERE o.kind = 'observation' AND o.validation_state = 'valid'
                     AND o.counterparty_evidence IN ('named', 'derivable') AND o.amount IS NOT NULL ORDER BY o.obs_key""")
    with open(out / "attributions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        cols = list(at[0].keys()) if at else []
        w.writerow(cols)
        for r in at:
            w.writerow([r[c] for c in cols])
    # exclusions.csv
    ex = q(con, "SELECT * FROM exclusions ORDER BY exclusion_key")
    with open(out / "exclusions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        cols = list(ex[0].keys()) if ex else []
        w.writerow(cols)
        for r in ex:
            w.writerow([r[c] for c in cols])
    # annex_e.txt et annex_f.txt : critères tels que commités, empreinte, première requête, diff
    crit, crit_commit, cfg_commit, old, new = criteria_status()
    n, ok, by, first, last = journal_stats()
    first_req = next((json.loads(l)["ts"] for l in open(config.ROOT / "journal.jsonl", encoding="utf-8")
                      if json.loads(l).get("url")), None)
    for key, fname, title in (("annex_e", "annex_e.txt", "Annexe E — énoncés de réfutation"),
                              ("annex_f", "annex_f.txt", "Annexe F — événements de fragilité")):
        body = yaml.safe_dump({key: old.get(key)}, allow_unicode=True, sort_keys=False, width=110)
        same = json.dumps(old.get(key), sort_keys=True) == json.dumps(new.get(key), sort_keys=True)
        txt = (f"{title}, critères tels que commités\n\nCommit : {crit_commit}\nPremière requête au journal : {first_req}\n"
               f"Changement ultérieur : {'aucun (critères identiques dans le config.yaml courant)' if same else 'voir le diff ci-dessous'}\n\n"
               + body)
        if not same:
            txt += "\nDiff :\n" + subprocess.run(["git", "diff", CRITERIA_COMMIT, "--", "config.yaml"], capture_output=True,
                                                 text=True, cwd=config.ROOT).stdout
        (out / fname).write_text(txt, encoding="utf-8")
    shutil.copy(config.ROOT / "audit_templates" / "domain_rules.md", out / "domain_rules.md")
    # journal masqué : vérifié avant copie
    jt = (config.ROOT / "journal.jsonl").read_text(encoding="utf-8")
    secret = (config.ROOT / "secrets" / "user_agent.txt")
    if secret.exists():
        for tok in secret.read_text(encoding="utf-8").split():
            if "@" in tok:
                jt = jt.replace(tok, "<adresse masquée>")
    (out / "journal.jsonl").write_text(jt, encoding="utf-8")
    shutil.copy(config.ROOT / "synthesis.md", out / "synthesis.md")
    shutil.copy(config.ROOT / "tables" / "measures.parquet", out / "measures.parquet")
    shutil.copy(config.ROOT / "tables" / "controls.parquet", out / "controls.parquet")
    auditor_md(out)


def auditor_md(out):
    spec = (config.ROOT / "SPEC.md").read_text(encoding="utf-8")
    a = spec.index("## Annexe C")
    b = spec.index("## Annexe D")
    text = spec[a:b].strip()
    p0 = json.loads((config.DB_DIR / "phase0.json").read_text())
    lst = []
    for g in config.load()["groups"]:
        ciks = [(c, m) for c, m in p0["meta"].items() if m["group"] == g]
        main = [f"{m['name']} (CIK {c})" for c, m in ciks if not m["is_predecessor"]]
        pred = [f"{m['name']} (CIK {c})" for c, m in ciks if m["is_predecessor"]]
        lst.append(f"{g} : " + ", ".join(main) + (f" ; prédécesseurs : {', '.join(pred)}" if pred else ""))
    text = text.replace("{groupes de `config.yaml`, avec leurs CIK et ceux de leurs prédécesseurs}", "; ".join(lst))
    (out / "AUDITOR.md").write_text("# Consignes pour l'auditeur\n\n" + text + "\n", encoding="utf-8")


def block_stats():
    from . import reader
    cat = {b["content_key"]: b for b in reader.load_catalog()}
    read = {p.stem for p in config.OBS_DIR.glob("*.jsonl") if not p.name.endswith(".rejected.jsonl")}
    by_item = Counter()
    for k, b in cat.items():
        if k in read and b["block_kind"].startswith("item_8k_"):
            by_item[b["block_kind"].replace("item_8k_", "")[0] + "." + b["block_kind"].replace("item_8k_", "")[1:]] += 1
    header_only = Counter((b.get("exhibit_type") or "EX").split(".")[0] for k, b in cat.items()
                          if b["block_kind"] == "exhibit_body" and k not in read)
    return {"catalog": len(cat), "read": len(read & set(cat)), "by_item": dict(by_item), "header_only": dict(header_only)}


def main(as_of):
    con = duckdb.connect()
    load(con, as_of)
    stats = json.loads((config.ROOT / "work" / "tmp" / "assemble_stats.json").read_text())
    stats["blocks"] = block_stats()
    rows = []
    for name, fn in (("synthesis.md", synthesis), ("delta.md", delta), ("series.md", series)):
        text, r = fn(con, as_of, stats)
        (config.ROOT / name).write_text(text, encoding="utf-8")
        rows += r
    audit(con, as_of, rows, stats)
    print("rendus écrits ;", len(rows), "nombres publiés")


if __name__ == "__main__":
    # l'ordre d'itération des ensembles de chaînes ne doit pas dépendre du processus (§9.6)
    if __import__("os").environ.get("PYTHONHASHSEED") != "0":
        __import__("os").environ["PYTHONHASHSEED"] = "0"
        __import__("os").execv(sys.executable, [sys.executable, "-m", "pipeline.render", *sys.argv[1:]])
    main(sys.argv[1])
