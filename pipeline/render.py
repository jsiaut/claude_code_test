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
    "not_processed": "non traité (pièce non encore lue)", "search_incomplete": "recherche incomplète",
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
            "unknown": "inconnu", "never": "jamais documenté", "searched_none_found": "recherche complète, rien trouvé", "supported": "étayé", "refuted": "réfuté", "indeterminate": "indéterminé",
            "compatible": "compatible", "descriptive": "descriptif", "not_supported": "non étayé",
            "computed": "calculée", "partial": "partielle", "bounded": "bornée", "not_determinable": "indéterminée",
            "not_applicable": "sans objet", "commitment": "engagement", "payment": "paiement",
            "opening": "ouverture", "additions": "nouveaux", "commenced": "commencés", "closing": "clôture",
            "lower": "borne basse", "upper": "borne haute", "point": "valeur unique"}
GROUP_NAMES = {"NVDA": "NVIDIA", "GOOGL": "Alphabet", "AMZN": "Amazon", "META": "Meta", "MSFT": "Microsoft",
               "ORCL": "Oracle", "CRWV": "CoreWeave", "SPCX": "SpaceX", "AMD": "AMD", "AVGO": "Broadcom",
               "MRVL": "Marvell", "WULF": "TeraWulf", "CIFR": "Cipher", "CORZ": "Core Scientific"}
NUM_FR = {11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze", 16: "seize"}


def n_groups(cfg):
    n = len(cfg.get("groups") or {})
    return NUM_FR.get(n, str(n))


def composition_line(cfg):
    """Composition des agrégats entre groupes et date d'entrée de chaque membre (§9.6)."""
    parts = []
    for e in cfg.get("group_entry") or []:
        parts.append(", ".join(GROUP_NAMES.get(g, g) for g in e["groups"]) + f" depuis le {e['date']}")
    return "; ".join(parts)


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
    # extension `text` ouverte : ce qui manque n'est plus « non traité au premier passage » ; une fois le texte
    # lu, il ne reste de non traité que ce qui relève d'un bloc de §14 fermé (les chemins de E.6, par exemple)
    sc = config.load().get("scope")
    if isinstance(sc, list) and "text" in sc:
        ND_FR["not_processed"] = ("non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)"
                                  if "discovery" in sc else "non traité (bloc de §14 non lu ou fermé)")
    t = config.ROOT / "tables"
    for name in ("measures", "controls", "exclusions", "links", "observations", "entities", "facts", "documents"):
        con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM '{t / (name + '.parquet')}'")
    # nom d'affichage d'un groupe de contrepartie : la dénomination telle qu'écrite dans la pièce
    for ref, name in con.execute("""SELECT m.ref, min(e.name) FROM entities m JOIN entities e
                                    ON e.entity_id = m.entity_id AND e.record_kind = 'entity'
                                    WHERE m.record_kind = 'membership' AND m.ref LIKE 'CP:%' GROUP BY 1""").fetchall():
        CP_NAMES[ref] = name
    # groupe propre calculé hors de toute appartenance datée (avant une combinaison) : même nom
    for norm, name in con.execute("""SELECT normalized_name, min(name) FROM entities WHERE record_kind = 'entity'
                                     AND normalized_name IS NOT NULL GROUP BY 1""").fetchall():
        CP_NAMES.setdefault("CP:" + norm, name)


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
RANK2_SERIES = [
    ("gross_margin", NONE, "Marge brute", "pct"),
    ("operating_margin", NONE, "Marge opérationnelle", "pct"),
    ("capex_to_revenue", NONE, "Capex décaissé ÷ revenu", "x"),
    ("fcf_after_sbc", NONE, "Flux disponible après rémunération en actions", "usd"),
    ("sbc_to_cfo", NONE, "Rémunération en actions ÷ CFO", "x"),
    ("cfo_net_income_gap", NONE, "Écart CFO − résultat net", "usd"),
    ("cov_interest_coverage", "without", "Résultat opérationnel ÷ charge d'intérêts (12 mois)", "x"),
    ("working_capital", "net", "Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat)", "usd"),
    ("eq_equity_and_accumulated_deficit", "equity", "Capitaux propres", "usd"),
    ("eq_equity_and_accumulated_deficit", "accumulated_deficit", "Résultats non distribués (déficit si négatif)", "usd"),
    ("eq_diluted_share_count_change", NONE, "Variation du nombre moyen dilué d'actions (sur un an)", "pct"),
    ("cip_share", NONE, "En-cours ÷ immobilisations brutes", "pct"),
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
          "sig_going_concern": "continuité d'exploitation", "sig_covenant_events": "clauses financières",
          "sig_pledged_assets": "actifs nantis"}
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
    if g.startswith("NF:"):
        return {"NF:SOFTBANK": "SoftBank"}.get(g, g[3:].title())
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
    sc = new.get("scope")
    blocks_open = sc if isinstance(sc, list) else []
    per = "premier passage" + (f", blocs {', '.join('`' + b + '`' for b in blocks_open)} de §14" if blocks_open else "")
    L.append(f"*Exécution du {as_of} · spec v6.14 · périmètre : {per} · rendu généré depuis les tables "
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
    if not blocks_open:
        L.append(f"- **Périmètre couvert : premier passage.** Faits balisés des {n_groups(new)} groupes, puis notes de parties liées, "
                 "Item 404, Item 9A, Item 4 des 10-Q, continuité d'exploitation et items 1.01, 1.02, 3.03 et 8.01 des 8-K "
                 "avec leurs pièces EX-10 et EX-4. Les notes d'investissements, de dette, de baux et d'engagements ne sont "
                 "pas lues : ce qui en dépend est publié partiel ou indéterminé, motif « non traité au premier passage ».")
    else:
        dec = new.get("scope_decision") or {}
        L.append(f"- **Périmètre couvert : premier passage et blocs {', '.join('`' + b + '`' for b in blocks_open)} de §14**, "
                 "ouverts sur décision de l'utilisateur (" + " ; ".join(
                     f"{', '.join('`' + b + '`' for b in h.get('blocks') or [])} le {h.get('date')}"
                     for h in [dec] + list(new.get("scope_history") or []) if h.get("blocks"))
                 + ", chaque fois après le rendement présenté). "
                 f"Premier passage : faits balisés des {n_groups(new)} groupes, notes de parties liées, Item 404, Item 9A, Item 4 des "
                 "10-Q, continuité d'exploitation, items 1.01, 1.02, 3.03 et 8.01 des 8-K avec leurs pièces EX-10 et EX-4. "
                 + ("Bloc `lender` : portefeuilles publiés des BDC (BDC Data Sets). " if "lender" in blocks_open else "")
                 + ("Bloc `text` : notes d'investissements, de dette, de baux et d'engagements, texte autour des faits de "
                    "concentration, items 2.01 et 2.03 des 8-K, corps des EX-10 arrêtés à leur en-tête (les EX-4 arrêtés à leur "
                    "en-tête restent exclus, §14 ne les rouvrant pas) ; " + (
                        "tout le catalogue du bloc est lu, aucun bloc ne reste « non traité ». "
                        if not q(con, """SELECT 1 FROM exclusions WHERE reason = 'not_processed' AND item_kind = 'block'
                                         LIMIT 1""") else
                        "ce qui n'est pas encore lu reste « non traité », bloc par bloc dans `exclusions`. ")
                    if "text" in blocks_open else "")
                 + ("Bloc `discovery` : déposants hors du périmètre qui nomment un groupe (Notes Data Sets, recherche plein "
                    "texte des EX-10 et des Form D), lus dans l'ordre du classement fixé d'avance (D-0036) ; "
                    + (f"la passe A est lue jusqu'au rang {T.n('observations', {'discovery_last_rank_read': True}, discovery_ranks_read())} du classement, puis la lecture est arrêtée sur "
                       "décision de l'utilisateur (D-0041) ; le reste de la file reste « non traité ». "
                       if next((h["discovery_reading"] for h in reversed(new.get("scope_history") or [])
                                if h.get("discovery_reading")), None) == "stopped" else
                       "la lecture avance par tranches, le reste de la file est « non traité » (D-0038). ")
                    if "discovery" in blocks_open else "")
                 + ("Bloc `paths` : cycles orientés de longueur 2 ou 3 entre groupes, tirés des arêtes établies (D-0041). "
                    if "paths" in blocks_open else "")
                 + ("Bloc `form_d` : Form D des entités des groupes et des véhicules tiers nommés d'après un non-déposant "
                    "(D-0041). " if "form_d" in blocks_open else "")
                 + ("Bloc `foreign` : dépôts 20-F, 40-F et 6-K des émetteurs étrangers que la spec nomme ou qui sont déjà "
                    "dans une paire ou un cycle, cadre comptable relevé, aucune somme entre US GAAP et IFRS (D-0042). "
                    if "foreign" in blocks_open else "")
                 + (lambda closed: "" if not closed else (f"Le bloc `{closed[0]}` reste fermé." if len(closed) == 1 else
                    "Les blocs " + ", ".join(f"`{x}`" for x in closed) + " restent fermés."))(
                     [x for x in ("discovery", "form_d", "paths", "foreign") if x not in blocks_open]))
    if len(new.get("group_entry") or []) > 1:
        rcs = new.get("reverse_combinations") or {}
        L.append("- **Composition des agrégats entre groupes** (§9.6) : " + composition_line(new) + ". Tout agrégat "
                 "entre groupes (paires, cycles, issues E.6 à E.9) change de composition à la date d'entrée d'un groupe : "
                 "l'écart avec l'état publié avant tient d'abord à l'ajout, non à un fait économique."
                 + (" Fusions inversées (D-0043) : " + " ; ".join(
                     f"{GROUP_NAMES.get(g, g)}, réalisée le {r['consummation']} avec {r['legal_registrant']} comme "
                     f"déclarant légal" for g, r in rcs.items())
                    + " ; les rapports antérieurs du déclarant légal présentent une autre entité et restent hors du "
                      "groupe, dont l'historique est tronqué à gauche." if rcs else ""))
    e7 = q(con, "SELECT * FROM measures WHERE measure = 'annex_e_outcome' AND breakdown_key LIKE 'E7|%'")
    if e7:
        c = e7[0]
        fl = json.loads(c["flags"]) if c["flags"] else {}
        if c["value"] is not None:
            res = ("les pièces déposées ne permettent pas de discriminer entre les deux lectures"
                   if c["value_text"] == "non_discrimination" else "discrimination possible au sens de E.7")
            reasons = ", ".join(f"{ND_FR.get(k, k)} : {T.n('measures', {'E7_reason': k}, v)}"
                                for k, v in sorted((fl.get('reasons') or {}).items(), key=lambda x: -x[1]))
            if c["value_text"] != "non_discrimination":
                # issues déterminées, par énoncé : ce qui permet de discriminer, et ce que « non étayé » veut dire
                det = [(st, k, v) for st in ("E1", "E2") for k, v in sorted((fl.get(f"outcomes_{st}") or {}).items())
                       if k != "indeterminate"]
                caveat = ("Issues déterminées : " + ", ".join(
                    f"{st[0]}.{st[1:]} {VALUE_FR.get(k, k)} {T.n('measures', {'E7_outcomes': [st, k]}, v)}" for st, k, v in det) +
                    ". Une issue « non étayé » de E.1 dit qu'aucune pièce de lien (L1 à L5) n'est trouvée sous une recherche "
                    "complète au sens de E.0, non que le financement soit sans rapport avec les achats. "
                    + ("La découverte (§14) n'étant lue que sur les premiers rangs de son classement, les paires dont le "
                       "client a encore des dépôts à lire restent indéterminées." if "discovery" in blocks_open else ""))
            elif not blocks_open:
                caveat = ("Au premier passage, cette non-discrimination tient d'abord au périmètre borné de la lecture, "
                          "non à une absence de relations.")
            elif "discovery" in blocks_open:
                caveat = ("La découverte (§14) n'étant lue que sur les premiers rangs de son classement, la recherche reste incomplète au "
                          "sens de E.0 pour les clients dont des dépôts restent à lire : une non-discrimination tient encore "
                          "en partie au périmètre de lecture.")
            else:
                caveat = ("La découverte (§14) n'étant pas ouverte, la recherche reste incomplète au sens de E.0 : une "
                          "non-discrimination tient encore en partie au périmètre de lecture.")
            L.append(f"- **Résultat principal (E.7) : {res}.** {T.m(c, fmt='pct', dec=0)} des issues de E.1 et E.2 "
                     f"au point de tête (10 %) sont indéterminées, sur {T.m(c, field='denominator', fmt='count')} issues ; "
                     f"motifs : {reasons or 'aucun'}. " + caveat.strip())
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
    ex = q(con, "SELECT reason, count(*) AS n FROM exclusions GROUP BY 1 ORDER BY 2 DESC, 1")
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
    L += paths_section(con, T)
    L += formd_section(con, T)
    L += foreign_section(con, T)
    L += lender_section(con, T)
    # Évolution et non établi
    L.append("## Évolution")
    L.append("")
    L.append("Premier passage : aucune exécution antérieure à laquelle comparer. Les séries trimestrielles complètes, ruptures "
             "de base marquées, sont dans `series.md` ; `delta.md` sera le point d'entrée des exécutions suivantes.")
    L.append("")
    L.append("## Ce qui n'a pas pu être établi")
    L.append("")
    nd = q(con, """SELECT nd_reason, count(*) AS n FROM measures WHERE status = 'not_determinable' AND view = 'as_known'
                   GROUP BY 1 ORDER BY 2 DESC, 1""")
    L.append("Cellules indéterminées en vue `as_known`, par motif : " +
             ", ".join(f"{ND_FR.get(r['nd_reason'], r['nd_reason'])} {T.n('measures', {'nd_reason': r['nd_reason']}, r['n'])}" for r in nd) + ".")
    L.append("")
    return "\n".join(L) + "\n", T.rows


def evidence_text(con, c, fl):
    obs = fl.get("observations") or []
    if obs:
        r = q(con, f"SELECT DISTINCT accession, form FROM observations WHERE obs_key IN ({','.join('?' * len(obs))}) "
                   "ORDER BY accession", *obs)
        return ", ".join(f"{x['form']} {x['accession']}" for x in r) or "observation"
    lin = fl.get("lineage")
    if lin:
        keys = json.loads(lin) if isinstance(lin, str) else lin
        r = q(con, f"SELECT DISTINCT accession, form FROM facts WHERE fact_key IN ({','.join('?' * len(keys))}) "
                   "ORDER BY accession", *keys)
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
        if q(con, "SELECT 1 FROM measures WHERE measure = 'gross_margin' AND subject = ? LIMIT 1", g):
            L.append("| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* | " + " | ".join("" for _ in qs) + " |")
            for meas, term, label, fmt in RANK2_SERIES:
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


CLASS_FR = {"debt": "prêts et obligations", "equity": "titres de capital", "unclassified": "non classé"}


def lender_section(con, T):
    """Bloc lender de §14 : positions des BDC rattachées aux entités du registre, trois signaux
    lus ensemble, tous fonds confondus, par groupe de l'émetteur et par date de bilan."""
    rows = q(con, """SELECT * FROM measures WHERE measure IN ('bdc_fv_to_cost', 'bdc_pik_share', 'bdc_non_accrual_share')
                     AND counterparty = 'none' AND breakdown_key LIKE 'all_bdc|%' ORDER BY subject, period_end, breakdown_key""")
    if not rows:
        return []
    L = ["## Côté prêteur (BDC Data Sets)", ""]
    L.append("Positions que les sociétés de développement d'affaires (BDC) publient dans leur portefeuille, rattachées "
             "aux entités des groupes et aux contreparties que nomment leurs pièces, par dénomination légale entière ; une "
             "position dont l'identifiant nomme aussi un autre émetteur n'est rattachée à personne. Vue `as_known` : le "
             "portefeuille à la date du bilan du dépôt de chaque fonds. Les fonds privés et les banques ne publient rien "
             "(`not_public`), et une balise absente ne prouve rien : un taux d'intérêt capitalisé ou un statut de "
             "non-accumulation non balisé reste indéterminé, jamais nul. Juste valeur ÷ coût n'est pas une probabilité "
             "de défaut, et des intérêts capitalisés peuvent être prévus dès l'origine : les trois signaux se lisent ensemble.")
    L.append("")
    L.append("| Groupe de l'émetteur | Date du bilan | Instrument | Positions | Coût | Juste valeur | Juste valeur ÷ coût | Part des intérêts capitalisés | Part sans accumulation d'intérêts |")
    L.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    by = defaultdict(dict)
    for r in rows:
        by[(r["subject"], r["period_end"], r["breakdown_key"].split("|", 1)[1])][r["measure"]] = r
    for (subj, pe, cls), m in sorted(by.items()):
        fv = m.get("bdc_fv_to_cost")
        fl = json.loads(fv["flags"]) if fv and fv["flags"] else {}
        n = fl.get("holdings")
        L.append(f"| {group_label(subj)} | {pe} | {CLASS_FR.get(cls, cls)} | {T.n('measures', {'bdc_holdings': [subj, pe, cls]}, n) if n is not None else '—'} | "
                 f"{T.m(fv, 'denominator') if fv and fv.get('denominator') is not None else '—'} | "
                 f"{T.m(fv, 'numerator') if fv and fv.get('numerator') is not None else '—'} | "
                 f"{T.m(fv, fmt='x') if fv else '—'} | {T.m(m['bdc_pik_share'], fmt='pct') if m.get('bdc_pik_share') else '—'} | "
                 f"{T.m(m['bdc_non_accrual_share'], fmt='pct') if m.get('bdc_non_accrual_share') else '—'} |")
    L.append("")
    notes = []
    for subj in sorted({k[0] for k in by if k[0].startswith("CP:")}):
        m = q(con, """SELECT m.ref, min(m.common_control_start) AS cc, min(m.legal_date) AS ld FROM entities e
                      JOIN entities m ON m.entity_id = e.entity_id AND m.record_kind = 'membership'
                      WHERE e.record_kind = 'entity' AND e.normalized_name = ? AND m.ref NOT LIKE 'CP:%' GROUP BY 1""",
              subj[3:])
        for r in m:
            notes.append(f"{group_label(subj)} appartient au groupe {group_label(r['ref'])}"
                         + (f" en vue `revised` depuis le {r['cc']} (contrôle commun)" if r["cc"] else "")
                         + (f", en vue `as_known` depuis le {r['ld']}" if r["ld"] else "")
                         + " : avant cette date, la vue `as_known` le garde comme groupe propre.")
    if notes:
        L.append("Appartenances datées : " + " ".join(notes))
        L.append("")
    amb = q(con, "SELECT count(*) AS n FROM exclusions WHERE item_key LIKE 'lender:%' AND reason = 'pending_entity'")[0]["n"]
    L.append(f"Identifiants de position écartés parce qu'ils nomment deux émetteurs : "
             f"{T.n('exclusions', {'lender_ambiguous': True}, amb)}.")
    L.append("")
    return L


def LINK_FR(fl):
    """Preuve de lien d'une paire (§3.4) : documenté, recherche complète sans pièce, ou recherche incomplète et pourquoi."""
    le = fl.get("linkage_evidence")
    if le == "documented_link":
        return "documenté (" + ", ".join(fl.get("link_categories") or []) + ")"
    if le == "searched_none_found":
        return "non trouvé, recherche complète au sens de E.0"
    disc = "discovery" in (config.load().get("scope") or [])
    why = {"search_incomplete": ("le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)"
                                 if disc else "le client peut déposer hors du périmètre, découverte (§14) non ouverte"),
           "parse_failed": "une archive de la période est illisible", "redacted": "une clause de la paire est caviardée",
           "not_processed": "texte non lu"}.get(fl.get("search_reason") or "not_processed", fl.get("search_reason"))
    return f"non trouvé, recherche incomplète ({why})"


TEMP_FR = {"yes": "oui", "no": "non", "unknown": "inconnue (un maillon sans arête datée)"}


def path_link_fr(fl):
    le = fl.get("linkage_evidence")
    if le == "documented_link":
        return "documenté (" + ", ".join(fl.get("link_categories") or []) + ")"
    if le == "searched_none_found":
        return "non trouvé, recherche complète au sens de E.0"
    return "non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire)"


def paths_section(con, T):
    """Bloc paths de §14 : cycles orientés de longueur 2 ou 3 entre groupes (documented_path, E.6, D-0041)."""
    if "paths" not in (config.load().get("scope") or []):
        return []
    rows = q(con, "SELECT * FROM measures WHERE measure = 'documented_path' ORDER BY breakdown_key")
    L = ["## Cycles entre groupes (bloc paths, §14)", ""]
    L.append("Un cycle suit les arêtes dans le sens de la ressource (financeur → financé, client → fournisseur, fournisseur "
             "→ client pour une contrepartie au client, garant → obligé) et revient à son point de départ après un ou deux "
             "intermédiaires ; il passe par au moins un groupe du périmètre et jamais à l'intérieur d'un même groupe. "
             "Concomitance (`temporal`) : on peut choisir une arête par maillon dont les périodes sont actives ensemble ou à "
             "moins de quatre trimestres d'écart. La conclusion n'est « dépendance documentée » que si chaque paire d'arêtes "
             "consécutives a sa pièce L1 à L5, dont l'extrait nomme les parties de la jonction : les deux d'une paire pour un "
             "cycle de longueur 2, les trois pour un cycle de longueur 3. Aucun ratio de chemin n'est publié, des montants de "
             "natures différentes ne se composant pas, et un cycle ne prouve ni revenu artificiel ni absence de demande "
             "finale (§3.3).")
    L.append("")
    if not rows:
        L.append("Aucun cycle dans le graphe courant.")
        L.append("")
        return L
    L.append("| Cycle | Longueur | Concomitance (écart en trimestres) | Structure | Lien | Conclusion |")
    L.append("| --- | ---: | --- | --- | --- | --- |")
    for c in rows:
        fl = json.loads(c["flags"])
        nodes = " → ".join(group_label(n) for n in fl["nodes"] + fl["nodes"][:1])
        gap = fl.get("gap_quarters")
        temp = TEMP_FR.get(fl["temporal"], fl["temporal"]) + (
            f" ({T.n('measures', {'path_gap_quarters': c['breakdown_key']}, gap)})" if gap is not None else "")
        L.append(f"| {nodes} | {T.n('measures', {'path_length': c['breakdown_key']}, fl['length'])} | {temp} | "
                 f"{STRUCT_FR.get(fl['edge_structure'], fl['edge_structure'])} | {path_link_fr(fl)} | "
                 f"**{CONC_FR[c['value_text']]}** |")
    L.append("")
    e6 = q(con, """SELECT * FROM measures WHERE measure = 'annex_e_outcome' AND subject = 'ALL'
                   AND breakdown_key = 'E6|none|none'""")
    if e6:
        fl = json.loads(e6[0]["flags"]) if e6[0]["flags"] else {}
        parts = []
        for tv, cnt in sorted((fl.get("counts") or {}).items()):
            parts.append(f"concomitance {TEMP_FR.get(tv, tv).split(' (')[0]} : " + ", ".join(
                f"{CONC_FR.get(k, k)} {T.n('measures', {'E6': [tv, k]}, v)}" for k, v in sorted(cnt.items())))
        L.append(f"Décompte de E.6 (descriptif, hors de E.7) : {T.m(e6[0], fmt='count')} cycles ; " + " ; ".join(parts) + ".")
        L.append("")
    return L


def formd_section(con, T):
    """Bloc form_d de §14 : offres des émetteurs du périmètre, série des véhicules tiers (D-0041)."""
    if "form_d" not in (config.load().get("scope") or []):
        return []
    L = ["## Form D (bloc form_d, §14)", ""]
    L.append("Un Form D donne le montant vendu d'une offre, cumulé depuis sa première vente, jamais une valorisation ni une "
             "contrepartie. La mesure se fait par offre (CIK de l'émetteur et date de première vente) sur le dernier dépôt "
             "connu : un D et ses D/A ne se somment pas, chaque dépôt remplace le précédent. Le montant peut inclure du non "
             "monétaire (titres remis lors d'un regroupement d'entreprises, par exemple) : ce n'est pas du numéraire primaire "
             "sans autre pièce. Aucun total n'est fait, ni entre offres ni entre véhicules.")
    L.append("")
    subj = q(con, """SELECT * FROM measures WHERE measure = 'form_d_offering_amount'
                     AND flags LIKE '%"issuer_is_subject": true%' ORDER BY breakdown_key, view""")
    if subj:
        L.append("**Émetteurs du périmètre** (faits sur l'entité émettrice, rattachée à son groupe à la date du dépôt ; "
                 "vue `as_known`, puis `revised` quand le rattachement diffère, §10.3) :")
        L.append("")
        L.append("| Émetteur | Groupe | Première vente | Dernier dépôt | Montant vendu | Regroupement d'entreprises |")
        L.append("| --- | --- | --- | --- | ---: | --- |")
        by = defaultdict(dict)
        for c in subj:
            by[c["breakdown_key"]][c["view"]] = c
        for key, v in by.items():
            a = v.get("as_known") or v.get("revised")
            r = v.get("revised")
            fl = json.loads(a["flags"])
            grp = group_label(a["subject"]) if a["view"] == "as_known" else ""
            if r and (a["view"] != "as_known" or r["subject"] != a["subject"]):
                grp = (grp + " ; " if grp else "") + f"{group_label(r['subject'])} en vue `revised`"
            L.append(f"| {fl.get('issuer_name')} | {grp} | {a['period_start']} | {a['period_end']} | {T.m(a)} | "
                     f"{'oui' if fl.get('business_combination') else 'non'} |")
        L.append("")
    veh = q(con, """SELECT subject, count(DISTINCT counterparty) AS v, count(DISTINCT breakdown_key) AS o, count(*) AS n,
                           min(period_end) AS a, max(period_end) AS b
                    FROM measures WHERE measure = 'form_d_offering_amount' AND flags LIKE '%"issuer_is_subject": false%'
                    GROUP BY 1 ORDER BY 1""")
    if veh:
        L.append("**Véhicules tiers** (émetteurs dont la dénomination, ou la description des titres offerts, nomme un "
                 "laboratoire ou un groupe qui ne dépose encore aucun rapport périodique) : ils mesurent une demande "
                 "d'exposition secondaire et n'entrent jamais dans une mesure de financement du nœud sous-jacent. Série par "
                 "véhicule et par trimestre civil, sur le dernier dépôt connu à chaque fin de trimestre, tant que le "
                 "sous-jacent ne dépose pas ; un nom ne prouve pas la détention, et un homonyme est écarté avec son motif.")
        L.append("")
        L.append("| Sous-jacent nommé | Véhicules | Offres | Cellules (véhicule × trimestre) | Premier trimestre | Dernier trimestre |")
        L.append("| --- | ---: | ---: | ---: | --- | --- |")
        for r in veh:
            L.append(f"| {group_label(r['subject'])} | {T.n('measures', {'formd_vehicles': r['subject']}, r['v'])} | "
                     f"{T.n('measures', {'formd_vehicle_offerings': r['subject']}, r['o'])} | "
                     f"{T.n('measures', {'formd_vehicle_cells': r['subject']}, r['n'])} | {r['a']} | {r['b']} |")
        L.append("")
        for r in veh:
            top = q(con, """SELECT * FROM measures WHERE measure = 'form_d_offering_amount' AND subject = ? AND period_end = ?
                            AND flags LIKE '%"issuer_is_subject": false%' AND value IS NOT NULL
                            ORDER BY value DESC, breakdown_key LIMIT 5""", r["subject"], r["b"])
            if top:
                L.append(f"- {group_label(r['subject'])}, plus grandes offres connues au {r['b']} : " + " ; ".join(
                    f"{json.loads(c['flags']).get('vehicle')} {T.m(c)}" for c in top) + ".")
        L.append("")
    homo = q(con, """SELECT count(*) AS n FROM exclusions WHERE item_key LIKE 'formd:%' AND detail LIKE '%D-0041%'""")[0]["n"]
    oos = q(con, """SELECT count(*) AS n FROM exclusions WHERE item_key LIKE 'formd:%' AND reason = 'out_of_scope'
                    AND detail LIKE '%fenêtre allongée%'""")[0]["n"]
    L.append(f"Offres écartées : {T.n('exclusions', {'formd_homonyms': True}, homo)} dont le terme désigne autre chose qu'une "
             f"exposition à la cible (homonyme, ou promoteur du fonds ; motif lu dans le Form D, D-0041) ; offres du périmètre "
             f"antérieures à la fenêtre allongée "
             f"{T.n('exclusions', {'formd_before_window': True}, oos)}.")
    L.append("")
    return L


def foreign_section(con, T):
    """Bloc foreign de §14 : émetteurs étrangers retenus, cadre comptable, lignes et arêtes (D-0042)."""
    if "foreign" not in (config.load().get("scope") or []):
        return []
    import pandas as pd
    from . import foreign
    L = ["## Émetteurs étrangers (bloc foreign, §14)", ""]
    inv = pd.read_parquet(foreign.INVENTORY) if foreign.INVENTORY.exists() else None
    if inv is not None:
        sel = inv[inv["selected"]]
        L.append(f"La file de la découverte compte {T.n('observations', {'foreign_filers': True}, len(inv))} émetteurs "
                 f"étrangers (20-F, 40-F, 6-K, F-1, F-4). La règle fixée avant lecture retient ceux que la spec nomme comme "
                 f"nœuds de la chaîne et ceux qui sont déjà dans une paire ou un cycle : "
                 f"{T.n('observations', {'foreign_selected': True}, len(sel))} ("
                 + ", ".join(sorted(sel["filer"].fillna(sel["cik"]))) + "). Les autres restent dans la file, « non traités ». "
                 "Un 20-F ou un 40-F porte des états annuels audités ; un 6-K est furnished, admissible seulement s'il est "
                 "incorporé par référence dans un document d'enregistrement par mention expresse.")
        L.append("")
    rows = q(con, """SELECT o.group_id, o.form, o.framework, o.kind, o.family, count(*) AS n
                     FROM observations o WHERE o.validation_state = 'valid' AND o.form IN
                     ('20-F', '20-F/A', '40-F', '40-F/A', '6-K', '6-K/A') GROUP BY 1, 2, 3, 4, 5 ORDER BY 1, 2""")
    if rows:
        L.append("| Émetteur | Formulaire | Cadre comptable | Lignes | dont arêtes |")
        L.append("| --- | --- | --- | ---: | ---: |")
        agg = {}
        for r in rows:
            k = (r["group_id"], r["form"], r["framework"])
            a, e = agg.get(k, (0, 0))
            agg[k] = (a + r["n"], e + (r["n"] if r["family"] not in (None, NONE) and r["kind"] == "observation" else 0))
        fw = {"ifrs": "IFRS", "us_gaap": "US GAAP"}
        for (g, f, w), (n, e) in sorted(agg.items()):
            L.append(f"| {group_label(g)} | {f} | {fw.get(w, w or '—')} | {T.n('observations', {'foreign_lines': [g, f]}, n)} | "
                     f"{T.n('observations', {'foreign_edge_lines': [g, f]}, e)} |")
        L.append("")
    inc = q(con, """SELECT count(DISTINCT accession) AS n FROM documents WHERE form LIKE '6-K%'
                    AND incorporated_by_reference""")[0]["n"]
    mixed = q(con, """SELECT count(*) AS n FROM exclusions WHERE reason = 'invalid_aggregate'
                      AND invariant LIKE '%f%'""")[0]["n"]
    L.append(f"6-K incorporés par référence (donc admissibles) : {T.n('documents', {'foreign_6k_incorporated': True}, inc)} ; "
             f"agrégats écartés pour cadres comptables mêlés (invariant f) : "
             f"{T.n('exclusions', {'invariant_f': True}, mixed)}.")
    L.append("")
    return L


def paths_formd_yield_section(con, T):
    """Rendement des blocs paths et form_d de §14 (D-0041)."""
    sc = config.load().get("scope") or []
    L = []
    if "paths" in sc:
        L += ["## Rendement du bloc paths (§14)", ""]
        rows = q(con, "SELECT value_text, flags FROM measures WHERE measure = 'documented_path'")
        by_len = Counter(json.loads(r["flags"])["length"] for r in rows)
        by_t = Counter((json.loads(r["flags"])["temporal"], r["value_text"]) for r in rows)
        L.append(f"- Cycles orientés entre groupes : {T.n('measures', {'paths_total': True}, len(rows))}, dont "
                 + ", ".join(f"longueur {T.n('measures', {'paths_length_value': k}, k)} : {T.n('measures', {'paths_by_length': k}, v)}"
                             for k, v in sorted(by_len.items())) + ".")
        L.append("- Par concomitance et conclusion : " + " ; ".join(
            f"{TEMP_FR.get(a, a).split(' (')[0]} / {CONC_FR.get(b, b)} {T.n('measures', {'paths_by': [a, b]}, v)}"
            for (a, b), v in sorted(by_t.items())) + ".")
        L.append("- E.6 n'est plus « non traité » : chaque fournisseur porte le décompte des cycles qui passent par lui.")
        L.append("")
    if "foreign" in sc:
        L += ["## Rendement du bloc foreign (§14)", ""]
        fb = q(con, """SELECT count(DISTINCT content_key) AS b, count(*) FILTER (WHERE kind = 'observation') AS o,
                              count(*) FILTER (WHERE kind = 'abstention') AS a FROM observations
                       WHERE validation_state = 'valid' AND form IN ('20-F', '20-F/A', '40-F', '40-F/A', '6-K', '6-K/A')""")[0]
        fw = q(con, """SELECT coalesce(framework, 'aucun') AS f, count(*) AS n FROM observations WHERE validation_state = 'valid'
                       GROUP BY 1 ORDER BY 1""")
        L.append(f"- Blocs de formulaires étrangers lus : {T.n('observations', {'foreign_blocks': True}, fb['b'])} ; "
                 f"{T.n('observations', {'foreign_obs': True}, fb['o'])} {plural(fb['o'], 'observation')}, "
                 f"{T.n('observations', {'foreign_abst': True}, fb['a'])} {plural(fb['a'], 'abstention')}.")
        L.append("- Lignes par cadre comptable de leur pièce : " + ", ".join(
            f"{r['f']} {T.n('observations', {'framework': r['f']}, r['n'])}" for r in fw) + ".")
        L.append("")
    if "form_d" in sc:
        L += ["## Rendement du bloc form_d (§14)", ""]
        docs = q(con, """SELECT count(*) AS n FROM documents WHERE form IN ('D', 'D/A') AND parse_state = 'parsed'""")[0]["n"]
        st = q(con, """SELECT CASE WHEN flags LIKE '%"issuer_is_subject": true%' THEN 'subject' ELSE 'vehicle' END AS p,
                              status, count(*) AS n, count(DISTINCT breakdown_key) AS o FROM measures
                       WHERE measure = 'form_d_offering_amount' GROUP BY 1, 2 ORDER BY 1, 2""")
        ex = q(con, """SELECT reason, count(*) AS n FROM exclusions WHERE item_key LIKE 'formd:%' GROUP BY 1 ORDER BY 1""")
        rel = q(con, """SELECT count(*) AS n FROM links WHERE relation_type = 'replaces' AND a_key LIKE 'formd:%'""")[0]["n"]
        L.append(f"- Form D lus (documents analysés) : {T.n('documents', {'formd_docs': True}, docs)} ; relations « remplace » "
                 f"entre dépôts d'une même offre : {T.n('links', {'formd_replaces': True}, rel)}.")
        stfr = {"computed": "calculées", "not_determinable": "indéterminées"}
        L.append("- Cellules `form_d_offering_amount` : " + " ; ".join(
            f"{'émetteurs du périmètre' if r['p'] == 'subject' else 'véhicules'} : "
            f"{T.n('measures', {'formd_cells': [r['p'], r['status']]}, r['n'])} cellules {stfr.get(r['status'], r['status'])}, "
            f"{T.n('measures', {'formd_offerings': [r['p'], r['status']]}, r['o'])} offres" for r in st) + ".")
        L.append("- Exclusions du bloc : " + (", ".join(f"`{r['reason']}` {T.n('exclusions', {'formd_excl': r['reason']}, r['n'])}"
                                                    for r in ex) or "aucune") + ".")
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
                 f"lien {LINK_FR(fl)} ; "
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
            part = " (partiel)" if nn and nn["status"] == "partial" else ""
            L.append(f"| {GROUP_NAMES[g]} | {pe} | {T.m(nn, fmt='pct') if nn else '—'}{part} | {anon} | "
                     f"{T.m(rs, fmt='pct') if rs else '—'} | {T.m(vp, fmt='count') if vp else '—'} |")
    L.append("")
    if conc_text_read(con):
        L.append("Le texte qui entoure les faits de concentration est lu (bloc text de §14) : un client qui reste anonyme "
                 "l'est dans les pièces elles-mêmes. Un client nommé ailleurs peut être l'un des anonymes (`overlap_possible`).")
    else:
        L.append("Le revenu attribué à des clients nommés est une borne basse : le texte qui entoure les faits de concentration "
                 "n'est pas lu au premier passage. Un client nommé ailleurs peut être l'un des anonymes (`overlap_possible`).")
    L.append("")
    return L


# règles des blocs de §14, énoncées pour l'auditeur quand le bloc est ouvert (§12.2), sans aucun résultat
BLOCK_RULES = {
    "lender": "**Côté prêteur (`lender`).** Portefeuilles publiés des BDC (BDC Data Sets, fichier `soi` ; état des "
              "placements, Reg S-X 12-12), rattachés aux entités des groupes et aux contreparties nommées par dénomination "
              "légale entière. Trois signaux lus ensemble : juste valeur ÷ coût, part des intérêts capitalisés, part sans "
              "accumulation d'intérêts ; aucun n'est une probabilité de défaut. Une balise absente ne prouve rien, la taille "
              "d'une facilité n'est pas la position détenue, et les fonds privés ne publient rien.",
    "text": "**Texte des groupes (`text`).** Notes d'investissements (ASC 321, ASC 323), de dette (ASC 470), de baux "
            "(ASC 842) et d'engagements (ASC 440), texte autour des faits de concentration (ASC 280-10-50-42), items 2.01 "
            "et 2.03 des 8-K, corps des EX-10. Un contrat prouve un plafond, pas un versement.",
    "discovery": "**Découverte (`discovery`).** Un déposant hors du périmètre est candidat si la mention d'un groupe est "
                 "dans une note, un contrat annexé, une section parties liées ou un Form D, jamais dans un facteur de "
                 "risque. Les candidats se lisent dans un ordre fixé d'avance (classe de mention, montant documenté, "
                 "nombre de groupes nommés, accession) ; ce qui n'est pas lu reste « non traité », jamais absent.",
    "paths": "**Chemins (`paths`).** Cycles orientés de longueur 2 ou 3 entre groupes, hors intragroupe, dans le sens de "
             "la ressource, avec leur concomitance (arêtes actives ensemble ou à moins de quatre trimestres d'écart). "
             "« Dépendance documentée » seulement si chaque paire d'arêtes consécutives a sa pièce L1 à L5 ; aucun ratio "
             "de chemin, des montants de natures différentes ne se composant pas.",
    "form_d": "**Form D (`form_d`).** Avis de vente déposé sous la Regulation D (Rule 503) : le montant vendu (Form D, "
              "Item 13) est cumulé depuis la première vente de l'offre, jamais une valorisation ni une contrepartie. "
              "Mesure par offre (CIK de l'émetteur et date de première vente) sur le dernier dépôt connu : un D et ses D/A "
              "ne se somment pas. Un montant qui peut inclure du non monétaire n'est pas du numéraire primaire sans autre "
              "pièce. Un véhicule tiers mesure une demande d'exposition secondaire et n'entre jamais dans une mesure de "
              "financement du nœud sous-jacent.",
    "foreign": "**Émetteurs étrangers (`foreign`).** 20-F et 40-F : états annuels audités ; 6-K : furnished (Form 6-K, "
               "General Instruction B), admissible seulement s'il est incorporé par référence dans un document "
               "d'enregistrement, par mention expresse (Securities Act, Section 11). Chaque pièce porte son cadre comptable : "
               "une contrepartie ou un groupe en IFRS est traité à part et jamais sommé avec du US GAAP, les deux cadres ne "
               "définissant pas de la même façon baux, participations et entités consolidées.",
}


def domain_rules():
    """Page des règles du domaine pour l'auditeur : le modèle, puis les règles des blocs de §14 ouverts."""
    txt = (config.ROOT / "audit_templates" / "domain_rules.md").read_text(encoding="utf-8")
    sc = config.load().get("scope")
    blocks = [b for b in (sc if isinstance(sc, list) else []) if b in BLOCK_RULES]
    if not blocks:
        return txt
    txt = txt.replace("§2 à §10 et §13 ; le §14 n'est pas ouvert au premier passage).*",
                      "§2 à §10, §13 et, pour les blocs ouverts, §14).*")
    return txt.rstrip("\n") + "\n\n## Blocs ouverts de la phase ultérieure (§14)\n\n" + "".join(
        f"- {BLOCK_RULES[b]}\n" for b in blocks)


def discovery_ranks_read():
    """Dernier rang du classement dont les unités de la passe A sont lues (D-0036)."""
    from . import discovery
    built = discovery.built_units()
    return max((u.get("rank") or 0 for u in built.values() if u.get("content_key")), default=0)


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
                    GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2""", *tiers)
    L.append("- Cellules de rang 1, par statut et motif : " + " ; ".join(
        f"{fr(r['status'])}{(' / ' + ND_FR.get(r['nd'], r['nd'])) if r['nd'] else ''} {T.n('measures', {'rank1': [r['status'], r['nd']]}, r['n'])}" for r in r1) + ".")
    fe = q(con, """SELECT status, coalesce(nd_reason, '') AS nd, count(*) AS n FROM measures WHERE measure = 'fragility_event'
                   GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2""")
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
    L.append("- Revenu attribué par chaque fournisseur à des clients nommés, dernier exercice (" +
             ("le texte autour des faits de concentration est lu : l'anonymat est celui des pièces" if conc_text_read(con)
              else "borne basse ; le texte autour des faits de concentration n'est pas lu au premier passage") +
             "), et part des clients anonymes : " + " ; ".join(cov(r) for r in nec) + ".")
    q4 = ["financed_status", "documented_revenue_dependency", "investor_customer_revenue_share", "named_edge_coverage",
          "documented_pair_coverage", "customer_concentration_anonymous", "documented_backlog_dependency",
          "consideration_to_customer", "noncash_revenue_from_investees", "contract_coverage", "relationship_conclusion"]
    r4 = q(con, f"""SELECT status, coalesce(nd_reason, '') AS nd, count(*) AS n FROM measures WHERE measure IN ({','.join('?' * len(q4))})
                    GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2""", *q4)
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
    lend = q(con, """SELECT measure, status, coalesce(nd_reason, '') AS nd, count(*) AS n FROM measures
                     WHERE measure LIKE 'bdc_%' GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""")
    if lend:
        L.append("## Rendement du bloc lender (§14)")
        L.append("")
        hf = q(con, "SELECT count(*) AS n, count(DISTINCT accession) AS a, count(DISTINCT cik) AS b FROM facts WHERE source = 'bdc_num'")[0]
        L.append(f"- Faits de BDC rattachés : {T.n('facts', {'bdc_facts': True}, hf['n'])}, dans "
                 f"{T.n('facts', {'bdc_filings': True}, hf['a'])} dépôts de {T.n('facts', {'bdc_ciks': True}, hf['b'])} fonds.")
        L.append("- Cellules par mesure, statut et motif : " + " ; ".join(
            f"{r['measure']} {fr(r['status'])}{(' / ' + ND_FR.get(r['nd'], r['nd'])) if r['nd'] else ''} "
            f"{T.n('measures', {'bdc': [r['measure'], r['status'], r['nd']]}, r['n'])}" for r in lend) + ".")
        grp = q(con, """SELECT DISTINCT subject FROM measures WHERE measure = 'bdc_fv_to_cost' AND counterparty = 'none'
                        ORDER BY 1""")
        sub_n = q(con, "SELECT count(*) AS n FROM exclusions WHERE item_key LIKE 'lender:subtotal:%'")[0]["n"]
        L.append("- Groupes d'émetteurs couverts : " + ", ".join(group_label(r["subject"]) for r in grp) + ".")
        L.append("")
    L += text_yield_section(con, T, stats)
    L += discovery_yield_section(con, T, stats)
    L += paths_formd_yield_section(con, T)
    L.append("## Exclusions nouvelles, par motif")
    L.append("")
    for r in q(con, "SELECT reason, count(*) AS n FROM exclusions GROUP BY 1 ORDER BY 2 DESC, 1"):
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
    fd = q(con, """SELECT form, count(DISTINCT accession) AS n FROM documents WHERE accession IS NOT NULL GROUP BY 1 ORDER BY 2 DESC, 1""")
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
             "d'engagements ; texte autour des faits de concentration ; 8-K items 2.01 et 2.03 ; corps des EX-10 "
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
                                            WHERE fact_key IN ({','.join('?' * len(fkeys))}) ORDER BY fact_key""", *fkeys):
                            terms.append((f["fact_key"], f["accession"], f["locator"], f["is_tagged"], f["tier"]))
                    if okeys:
                        for o in q(con, f"""SELECT obs_key, accession, locator, tier FROM observations
                                            WHERE obs_key IN ({','.join('?' * len(okeys))}) ORDER BY obs_key""", *okeys):
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
    (out / "domain_rules.md").write_text(domain_rules(), encoding="utf-8")
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


def conc_text_read(con):
    """Le texte autour des faits de concentration est lu pour tous les fournisseurs : chaque cellule
    `named_edge_coverage` du terme `named` est calculée, plus aucune n'est partielle."""
    r = q(con, """SELECT count(*) AS n FROM measures WHERE measure = 'named_edge_coverage' AND term = 'named'
                  AND status = 'partial'""")
    return r[0]["n"] == 0


TEXT_KIND_FR = {"concentration_text": "paragraphes sur les clients", "investment_note": "notes d'investissements",
                "item_8k_201": "8-K item 2.01", "item_8k_203": "8-K item 2.03", "debt_note": "notes de dette",
                "lease_note": "notes de baux", "commitments_note": "notes d'engagements",
                "lever_note": "immobilisations et estimations", "revenue_note": "notes de revenu",
                "exhibit_body": "corps d'EX-10"}


def text_yield_section(con, T, stats):
    """Rendement du bloc `text` (§14) : blocs lus et restants par type, lignes rendues, et ce qui
    a changé depuis le rendement présenté à l'utilisateur avant l'ouverture."""
    cfg = config.load()
    sc = cfg.get("scope")
    if not (isinstance(sc, list) and "text" in sc):
        return []
    first = str((cfg.get("reading") or {}).get("text_block_first_pass"))
    pres = (cfg.get("scope_decision") or {}).get("yield_presented") or {}
    tb = stats.get("blocks", {}).get("text", {})
    L = ["## Rendement du bloc text (§14)", ""]
    order = [k for k in TEXT_KIND_FR if k in tb]
    tot = [sum(tb[k][i] for k in order) for i in range(4)]
    L.append(f"- Blocs lus : {T.n('observations', {'text_blocks_read': True}, tot[1])} sur "
             f"{T.n('observations', {'text_blocks_catalog': True}, tot[0])} "
             f"({fr_num(Decimal(tot[3]) / Decimal(10**6), 1)} sur {fr_num(Decimal(tot[2]) / Decimal(10**6), 1)} millions de "
             "caractères) ; par type : " + " ; ".join(
                 f"{TEXT_KIND_FR[k]} {T.n('observations', {'text_read': k}, tb[k][1])}/{T.n('observations', {'text_catalog': k}, tb[k][0])}"
                 for k in order) + (". Le reste est exclu bloc par bloc, motif « non traité » (`not_processed`), "
                                    "du plus ancien au plus récent dans chaque type, et ouvre l'exécution suivante."
                                    if tot[1] < tot[0] else ". Aucun bloc du catalogue ne reste à lire."))
    lines = q(con, f"""SELECT kind, validation_state, count(*) AS n FROM observations WHERE pass_id >= ?
                       AND CAST(block_kind AS VARCHAR) NOT LIKE 'discovery_%' GROUP BY 1, 2 ORDER BY 1, 2""", first)
    obs = sum(r["n"] for r in lines if r["kind"] == "observation" and r["validation_state"] == "valid")
    abst = sum(r["n"] for r in lines if r["kind"] == "abstention" and r["validation_state"] == "valid")
    rej = sum(r["n"] for r in lines if r["validation_state"] != "valid")
    L.append(f"- Lignes rendues dans les passes du bloc : {T.n('observations', {'text_obs': True}, obs)} observations, "
             f"{T.n('observations', {'text_abst': True}, abst)} abstentions motivées, "
             f"{T.n('observations', {'text_rejected': True}, rej)} rejetées par la validation.")
    ed = q(con, f"""SELECT l.family, l.edge_evidence, count(DISTINCT l.link_key) AS n FROM links l
                    WHERE l.link_kind = 'edge' AND EXISTS (SELECT 1 FROM observations o WHERE o.pass_id >= ?
                          AND CAST(o.block_kind AS VARCHAR) NOT LIKE 'discovery_%'
                          AND l.evidence_keys LIKE '%' || o.obs_key || '%') GROUP BY 1, 2 ORDER BY 1, 2""", first)
    if ed:
        L.append("- Arêtes établies par une ligne du bloc : " + ", ".join(
            f"{r['family']} ({'montant' if r['edge_evidence'] == 'amount' else 'relation'}) "
            f"{T.n('links', {'text_edges': [r['family'], r['edge_evidence']]}, r['n'])}" for r in ed) + ".")
    r1p = pres.get("rank1_cells") or {}
    tiers = [m for m, v in __import__("pipeline.registry", fromlist=["MEASURES"]).MEASURES.items() if v[0] == 1]
    now = {r["status"]: r["n"] for r in q(con, f"""SELECT status, count(*) AS n FROM measures
                    WHERE measure IN ({','.join('?' * len(tiers))}) AND measure NOT IN ('fragility_event', 'annex_e_outcome')
                    GROUP BY 1""", *tiers)}
    npn = q(con, f"""SELECT count(*) AS n FROM measures WHERE measure IN ({','.join('?' * len(tiers))})
                     AND measure NOT IN ('fragility_event', 'annex_e_outcome') AND nd_reason = 'not_processed'""", *tiers)[0]["n"]
    if r1p:
        L.append(f"- Cellules de rang 1, avant l'ouverture → maintenant : total {fr_num(Decimal(r1p.get('total', 0)), 0)} → "
                 f"{T.n('measures', {'rank1_now': 'total'}, sum(now.values()))} ; " + " ; ".join(
            f"{fr(st)} {fr_num(Decimal(r1p.get(st, 0)), 0)} → {T.n('measures', {'rank1_now': st}, now.get(st, 0))}"
            for st in ("computed", "bounded", "partial", "not_determinable")) +
            f" ; motif « non traité » {fr_num(Decimal(pres.get('rank1_not_processed', 0)), 0)} → "
            f"{T.n('measures', {'rank1_not_processed_now': True}, npn)}. Le total peut changer : une ligne lue ouvre parfois "
            "des cellules nouvelles (une paire, un instrument).")
    fe = q(con, "SELECT count(*) AS n FROM measures WHERE measure = 'fragility_event' AND value_text = 'event'")
    e7 = pres.get("annex_e_e7") or {}
    # E.7 au point de tête de la grille : issues de E.1 et E.2 réunies, telles que E.7 les compte
    e7r = q(con, """SELECT flags FROM measures WHERE measure = 'annex_e_outcome' AND breakdown_key LIKE 'E7|%'
                    ORDER BY breakdown_key LIMIT 1""")
    e7fl = json.loads(e7r[0]["flags"]) if e7r and e7r[0]["flags"] else {}
    e7now = {"n": sum(sum(v.values()) for k, v in e7fl.items() if k.startswith("outcomes_")),
             "i": sum(v.get("indeterminate", 0) for k, v in e7fl.items() if k.startswith("outcomes_"))}
    L.append(f"- Événements de l'annexe F : {fr_num(Decimal(pres.get('fragility_events', 0)), 0)} → "
             f"{T.n('measures', {'annexF_events_now': True}, fe[0]['n'] if fe else 0)} ; issues de paire indéterminées "
             f"(E.1 et E.2) : {e7.get('indeterminate', '—')} sur {e7.get('outcomes', '—')} → "
             f"{T.n('measures', {'e7_indeterminate_now': True}, e7now['i'])} sur {T.n('measures', {'e7_outcomes_now': True}, e7now['n'])}.")
    # statut « financé » : never devient possible une fois la recherche complète (§3.2, E.0)
    fs = q(con, """SELECT coalesce(value_text, '') AS v, coalesce(nd_reason, '') AS nd, count(*) AS n FROM measures
                   WHERE measure = 'financed_status' AND view = 'as_known' AND financing_policy = 'exposure_outstanding'
                   GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2""")
    if fs:
        L.append("- Statut « financé » (trimestres-paires, vue `as_known`, politique `exposure_outstanding`) : " + ", ".join(
            f"{VALUE_FR.get(r['v'], r['v'])}{(' / ' + ND_FR.get(r['nd'], r['nd'])) if r['nd'] else ''} "
            f"{T.n('measures', {'financed_status_now': [r['v'], r['nd']]}, r['n'])}" for r in fs) +
            ". « Jamais documenté » veut dire qu'aucune pièce lue n'établit F, sous une recherche complète au sens de E.0 : "
            "tout le texte du fournisseur et, s'il dépose, du client est lu ; un client qui peut déposer hors du périmètre "
            + ("laisse la recherche incomplète tant que ses dépôts qui nomment le fournisseur ne sont pas tous lus "
               "(découverte, §14, D-0037)." if "discovery" in (cfg.get("scope") or []) else
               "laisse la recherche incomplète tant que la découverte (§14) n'est pas ouverte."))
    # ce qu'une extension peut encore changer (§11.1, E.7) : motifs des cellules de rang 1 non calculées
    why = q(con, f"""SELECT nd_reason AS nd, count(*) AS n FROM measures WHERE measure IN ({','.join('?' * len(tiers))})
                     AND status IN ('not_determinable', 'partial') AND nd_reason IS NOT NULL
                     GROUP BY 1 ORDER BY 2 DESC, 1""", *tiers)
    if why:
        L.append("- Motifs des cellules de rang 1 indéterminées ou partielles après le bloc : " + " ; ".join(
            f"{ND_FR.get(r['nd'], r['nd'])} {T.n('measures', {'rank1_reason_now': r['nd']}, r['n'])}" for r in why) +
            ". Une extension ne change rien là où le motif est « non-déposant » ou « caviardé » ; « recherche "
            "incomplète » attend " + ("la lecture du reste de la file de la découverte (§14)" if "discovery" in
                                       (cfg.get("scope") or []) else "la découverte (§14)") +
            " ; « client anonyme » est définitif, le texte autour des faits de concentration étant lu.")
    for meas, label in (("sig_covenant_events", "Clauses financières"), ("sig_pledged_assets", "Actifs nantis")):
        rows = q(con, f"""SELECT status, coalesce(value_text, '') AS v, coalesce(nd_reason, '') AS nd, count(*) AS n
                          FROM measures WHERE measure = ? AND view = 'as_known' GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""", meas)
        if rows:
            def lab(r):
                if r["status"] == "computed":
                    return VALUE_FR.get(r["v"], fr(r["v"]))
                return fr(r["status"]) + (f" ({VALUE_FR.get(r['v'], fr(r['v']))} sur la part lue)" if r["v"] else "") + \
                    (f" / {ND_FR.get(r['nd'], r['nd'])}" if r["nd"] else "")
            L.append(f"- {label} (`{meas}`, trimestres-groupes, vue `as_known`) : " + ", ".join(
                f"{lab(r)} {T.n('measures', {'text_signal': [meas, r['status'], r['v'], r['nd']]}, r['n'])}" for r in rows) + ".")
    for meas, label in (("lease_not_commenced_bridge", "Pont des baux non commencés"),
                        ("depreciation_life_change_effect", "Effet publié d'un changement de durée d'utilité"),
                        ("lever_restatement", "Résultat opérationnel retraité de cet effet")):
        rows = q(con, "SELECT status, count(*) AS n FROM measures WHERE measure = ? GROUP BY 1 ORDER BY 1", meas)
        if rows:
            L.append(f"- {label} (`{meas}`) : " + ", ".join(
                f"{fr(r['status'])} {T.n('measures', {'text_measure': [meas, r['status']]}, r['n'])}" for r in rows) + ".")
    L.append("")
    return L


def discovery_yield_section(con, T, stats):
    """Rendement du bloc `discovery` (§14, D-0036 à D-0038) : sources tirées, candidats, file de
    lecture, lignes rendues, arêtes et pièces de lien, et ce qui a changé depuis le rendement
    présenté à l'utilisateur avant l'ouverture."""
    import pandas as pd
    from . import discovery
    cfg = config.load()
    if "discovery" not in (cfg.get("scope") or []):
        return []
    hist = [h for h in (cfg.get("scope_history") or []) if "discovery" in (h.get("blocks") or [])]
    pres = (hist[-1] if hist else {}).get("yield_presented") or {}
    L = ["## Rendement du bloc discovery (§14)", ""]
    todo = discovery.in_period(discovery.archive_list(), discovery.period_start())
    done = set(discovery.scanned_archives())
    nq = len(discovery.QUERY_LOG.read_text(encoding="utf-8").splitlines()) if discovery.QUERY_LOG.exists() else 0
    L.append(f"- Sources : {T.n('exclusions', {'discovery_archives_scanned': True}, len(done & {a['name'] for a in todo}))} "
             f"archives des Notes Data Sets scannées sur {T.n('exclusions', {'discovery_archives_period': True}, len(todo))} "
             f"de la période ; {T.n('journal', {'discovery_efts_queries': True}, nq)} requêtes de recherche plein texte "
             "consignées (EX-10 et Form D).")
    cand = pd.read_parquet(discovery.CANDIDATES) if discovery.CANDIDATES.exists() else None
    units = pd.read_parquet(discovery.UNITS) if discovery.UNITS.exists() else None
    if cand is not None:
        by = cand["best_class"].value_counts().to_dict()
        L.append(f"- Candidats (déposants qui nomment un groupe) : {T.n('observations', {'discovery_candidates': True}, len(cand))}, "
                 "par meilleure classe de mention : " + ", ".join(
                     f"{c} {T.n('observations', {'discovery_candidates_class': c}, int(by.get(c, 0)))}"
                     for c in ("contract", "related_party", "note", "form_d") if c in by) + ".")
    disc = q(con, """SELECT kind, validation_state, count(*) AS n, count(DISTINCT content_key) AS b FROM observations
                     WHERE CAST(block_kind AS VARCHAR) LIKE 'discovery_%' GROUP BY 1, 2 ORDER BY 1, 2""")
    nb = q(con, """SELECT count(DISTINCT content_key) AS b, count(DISTINCT group_id) AS g FROM observations
                   WHERE CAST(block_kind AS VARCHAR) LIKE 'discovery_%'""")[0]
    if units is not None:
        L.append(f"- File de lecture : {T.n('observations', {'discovery_units': True}, len(units))} unités (notes et en-têtes "
                 f"d'EX-10) ; lues : {T.n('observations', {'discovery_blocks_read': True}, nb['b'])} blocs de "
                 f"{T.n('observations', {'discovery_filers_read': True}, nb['g'])} déposants, ceux des premiers candidats du "
                 "classement. Le reste est exclu, motif « non traité » (`not_processed`), unité par unité dans `exclusions`.")
    obs = sum(r["n"] for r in disc if r["kind"] == "observation" and r["validation_state"] == "valid")
    abst = sum(r["n"] for r in disc if r["kind"] == "abstention" and r["validation_state"] == "valid")
    rej = sum(r["n"] for r in disc if r["validation_state"] != "valid")
    L.append(f"- Lignes rendues : {T.n('observations', {'discovery_obs': True}, obs)} observations, "
             f"{T.n('observations', {'discovery_abst': True}, abst)} abstentions motivées, "
             f"{T.n('observations', {'discovery_rejected': True}, rej)} rejetées par la validation.")
    ed = q(con, """SELECT l.family, l.edge_evidence, count(DISTINCT l.link_key) AS n FROM links l
                   WHERE l.link_kind = 'edge' AND EXISTS (SELECT 1 FROM observations o
                         WHERE CAST(o.block_kind AS VARCHAR) LIKE 'discovery_%'
                         AND l.evidence_keys LIKE '%' || o.obs_key || '%') GROUP BY 1, 2 ORDER BY 1, 2""")
    if ed:
        L.append("- Arêtes établies par une ligne de la découverte : " + ", ".join(
            f"{r['family']} ({'montant' if r['edge_evidence'] == 'amount' else 'relation'}) "
            f"{T.n('links', {'discovery_edges': [r['family'], r['edge_evidence']]}, r['n'])}" for r in ed) + ".")
    lk = q(con, """SELECT link_category AS c, count(*) AS n FROM observations WHERE CAST(block_kind AS VARCHAR) LIKE 'discovery_%'
                   AND validation_state = 'valid' AND link_category IS NOT NULL GROUP BY 1 ORDER BY 1""")
    if lk:
        # pièce d'une paire (S, C) : ses parties sont S et C et l'extrait les nomme tous deux (§3.4, D-0039)
        used = set()
        for r in q(con, "SELECT flags FROM measures WHERE measure = 'relationship_conclusion' AND view = 'as_known'"):
            used |= set((json.loads(r["flags"]) if r["flags"] else {}).get("link_pieces") or [])
        keys = [r["k"] for r in q(con, """SELECT obs_key AS k FROM observations WHERE CAST(block_kind AS VARCHAR) LIKE 'discovery_%'
                                         AND validation_state = 'valid' AND link_category IS NOT NULL""")]
        L.append("- Lignes à catégorie de lien (L1 à L5, §3.4) dans les blocs de la découverte : " + ", ".join(
            f"{r['c']} {T.n('observations', {'discovery_link': r['c']}, r['n'])}" for r in lk) +
            f". Pièces d'une paire (S, C) : {T.n('measures', {'discovery_link_pieces': True}, sum(1 for k in keys if k in used))} ; "
            "leurs parties sont le fournisseur S et le client C, et l'extrait les nomme tous deux (D-0039). "
            "Les autres lignes ne comptent pour aucune paire.")
    np_ = q(con, """SELECT count(*) AS n FROM exclusions WHERE reason = 'not_processed' AND item_key LIKE 'discovery:%'""")[0]["n"]
    L.append(f"- Unités de la file encore à lire : {T.n('exclusions', {'discovery_not_processed': True}, np_)}.")
    L += nf_discovery_lines(con, T)
    fsp = pres.get("financed_status_quarter_pairs") or {}
    if fsp:
        # clé commune aux deux relevés : la valeur, ou le motif quand la valeur est « unknown »
        canon = {"history_left_censored": "censored"}
        now = {}
        for r in q(con, """SELECT coalesce(value_text, '') AS v, coalesce(nd_reason, '') AS nd, count(*) AS n
                           FROM measures WHERE measure = 'financed_status' AND view = 'as_known'
                           AND financing_policy = 'exposure_outstanding' GROUP BY 1, 2"""):
            k = r["v"] if r["v"] not in ("", "unknown") else canon.get(r["nd"], r["nd"])
            now[k] = now.get(k, 0) + r["n"]

        def lab(k):
            return VALUE_FR.get(k) or ND_FR.get({"censored": "history_left_censored"}.get(k, k)) or k
        L.append("- Statut « financé » (trimestres-paires, vue `as_known`), avant l'ouverture → maintenant : " + " ; ".join(
            f"{lab(k)} {fr_num(Decimal(fsp.get(k, 0)), 0)} → "
            f"{T.n('measures', {'financed_status_discovery_now': k}, now.get(k, 0))}" for k in sorted(set(fsp) | set(now))) +
            ". La recherche incomplète devient « non traité » quand le client dépose et que ses unités ne sont pas toutes "
            "lues, « jamais documenté » quand son côté est complet (D-0037).")
    # paires à financement documenté et issues de l'annexe E, avant l'ouverture → maintenant (E.0, E.7)
    fin = q(con, """SELECT count(DISTINCT subject || '|' || counterparty) AS n FROM measures WHERE measure = 'financed_status'
                    AND value_text = 'active' AND view = 'as_known' AND financing_policy = 'exposure_outstanding'""")[0]["n"]
    if "pairs_financed_documented" in pres:
        L.append(f"- Paires à financement documenté (F active au moins un trimestre) : "
                 f"{fr_num(Decimal(pres['pairs_financed_documented']), 0)} → "
                 f"{T.n('measures', {'discovery_financed_pairs_now': True}, fin)}.")
    e7p = pres.get("annex_e_e7") or {}
    e7r = q(con, """SELECT value_text, flags FROM measures WHERE measure = 'annex_e_outcome' AND breakdown_key LIKE 'E7|%'
                    ORDER BY breakdown_key LIMIT 1""")
    if e7p and e7r:
        fl = json.loads(e7r[0]["flags"]) if e7r[0]["flags"] else {}
        n = sum(sum(v.values()) for k, v in fl.items() if k.startswith("outcomes_"))
        i = sum(v.get("indeterminate", 0) for k, v in fl.items() if k.startswith("outcomes_"))
        e7fr = {"non_discrimination": "non-discrimination", "discrimination_possible": "discrimination possible"}
        e1 = fl.get("outcomes_E1") or {}
        L.append(f"- Annexe E, issues de E.1 et E.2 au point de tête (10 %), avant l'ouverture → maintenant : indéterminées "
                 f"{fr_num(Decimal(e7p.get('indeterminate', 0)), 0)} sur {fr_num(Decimal(e7p.get('outcomes', 0)), 0)} → "
                 f"{T.n('measures', {'discovery_e7_indeterminate_now': True}, i)} sur "
                 f"{T.n('measures', {'discovery_e7_outcomes_now': True}, n)} ; E.7 : "
                 f"{e7fr.get(e7p.get('result'), e7p.get('result'))} → {e7fr.get(e7r[0]['value_text'], e7r[0]['value_text'])}. "
                 "Issues de E.1 (lien documenté, paires où F est active) : " + ", ".join(
                     f"{VALUE_FR.get(k, k)} {T.n('measures', {'discovery_e1_now': k}, v)}" for k, v in sorted(e1.items())) +
                 ". Une issue « non étayé » suppose la recherche complète des deux côtés (E.0) : la découverte la rend "
                 "possible quand le client ne dépose pas, n'a aucun rapport périodique dans la fenêtre allongée, ou que toutes "
                 "ses unités qui nomment le fournisseur sont lues (D-0037).")
    r1 = q(con, f"""SELECT count(*) AS n FROM measures WHERE nd_reason = 'search_incomplete' AND measure IN
                    ({','.join('?' * len([m for m, v in __import__("pipeline.registry", fromlist=["MEASURES"]).MEASURES.items() if v[0] == 1]))})""",
           *[m for m, v in __import__("pipeline.registry", fromlist=["MEASURES"]).MEASURES.items() if v[0] == 1])[0]["n"]
    if "rank1_search_incomplete" in pres:
        L.append(f"- Cellules de rang 1 au motif « recherche incomplète » : {fr_num(Decimal(pres['rank1_search_incomplete']), 0)} → "
                 f"{T.n('measures', {'rank1_search_incomplete_now': True}, r1)}.")
    L.append("")
    return L


def nf_discovery_lines(con, T):
    """Piste des non-déposants de la découverte (D-0044) : sources, candidats, unités retenues et
    lues, lignes rendues et arêtes établies."""
    import pandas as pd
    from . import discovery, nf_discovery as NF
    if not NF.UNITS.exists():
        return []
    units = pd.read_parquet(NF.UNITS)
    cand = pd.read_parquet(NF.CANDIDATES)
    ex10 = pd.read_parquet(NF.EX10) if NF.EX10.exists() else pd.DataFrame(columns=["status"])
    todo = {a["name"] for a in discovery.in_period(discovery.archive_list(), discovery.period_start())}
    done = set(NF.scanned_archives()) & todo
    keys = set()
    if NF.CATALOG.exists():
        keys = {json.loads(l)["content_key"] for l in NF.CATALOG.read_text(encoding="utf-8").splitlines() if l.strip()}
    read = {p.stem for p in config.OBS_DIR.glob("*.jsonl") if not p.name.endswith(".rejected.jsonl")} & keys
    st = units["status"].value_counts().to_dict()
    ru = units[units["status"] != "out_of_rule"]["rule"].value_counts().to_dict()
    names = ", ".join(sorted({group_label(g) for s in units["groups"] for g in s.split(";") if g}))
    L = [f"- Piste des non-déposants ({names}, D-0044) : {T.n('exclusions', {'nf_archives_scanned': True}, len(done))} "
         f"archives scannées sur {T.n('exclusions', {'nf_archives_period': True}, len(todo))} avec le lexique de la piste ; "
         f"{T.n('observations', {'nf_ex10_verified': True}, int((ex10['status'] == 'verified').sum()))} EX-10 vérifiés ; "
         f"{T.n('observations', {'nf_candidates': True}, len(cand))} candidats ; "
         f"{T.n('observations', {'nf_units': True}, len(units))} unités, dont "
         f"{T.n('observations', {'nf_units_selected': True}, int(st.get('queued', 0) + st.get('over_cap', 0)))} retenues "
         f"(co-mention R1 {T.n('observations', {'nf_units_rule': 'R1'}, int(ru.get('R1', 0)))}, "
         f"montant documenté R2 {T.n('observations', {'nf_units_rule': 'R2'}, int(ru.get('R2', 0)))}), "
         f"{T.n('observations', {'nf_blocks_read': True}, len(read))} blocs lus, "
         f"{T.n('observations', {'nf_units_over_cap': True}, int(st.get('over_cap', 0)))} au-delà du plafond, "
         f"{T.n('observations', {'nf_units_out_of_rule': True}, int(st.get('out_of_rule', 0)))} hors de la règle "
         "(exclues, motif « non traité »)."]
    if read:
        ks = ",".join("'" + k + "'" for k in sorted(read))
        r = q(con, f"""SELECT kind, count(*) AS n FROM observations WHERE validation_state = 'valid'
                       AND content_key IN ({ks}) GROUP BY 1 ORDER BY 1""")
        cnt = {x["kind"]: x["n"] for x in r}
        L.append(f"  Lignes rendues : {T.n('observations', {'nf_obs': True}, cnt.get('observation', 0))} observations, "
                 f"{T.n('observations', {'nf_abst': True}, cnt.get('abstention', 0))} abstentions motivées.")
    refs = sorted({g for s in units["groups"] for g in s.split(";") if g})
    for g in refs:
        e = q(con, """SELECT count(*) AS n, count(*) FILTER (WHERE (CASE WHEN from_group = ? THEN to_group ELSE from_group END)
                      NOT LIKE 'CP:%') AS k FROM links WHERE link_kind = 'edge' AND (from_group = ? OR to_group = ?)""", g, g, g)[0]
        L.append(f"  Arêtes de {group_label(g)} : {T.n('links', {'nf_edges': g}, e['n'])}, dont "
                 f"{T.n('links', {'nf_edges_groups': g}, e['k'])} avec un groupe ou un laboratoire ; les autres vont à des "
                 "contreparties propres (§10.2).")
    return L


def block_stats():
    from . import reader
    cat = {b["content_key"]: b for b in reader.load_catalog()}
    read = {p.stem for p in config.OBS_DIR.glob("*.jsonl") if not p.name.endswith(".rejected.jsonl")}
    by_item = Counter()
    for k, b in cat.items():
        if k in read and b["block_kind"].startswith("item_8k_"):
            by_item[b["block_kind"].replace("item_8k_", "")[0] + "." + b["block_kind"].replace("item_8k_", "")[1:]] += 1
    text_open = reader._text_scope()
    # corps arrêtés à l'en-tête et exclus : tous au premier passage ; les EX-4 seuls quand `text` rouvre les EX-10
    header_only = Counter((b.get("exhibit_type") or "EX").split(".")[0] for k, b in cat.items()
                          if b["block_kind"] == "exhibit_body" and k not in read
                          and not (text_open and reader.in_text_block(b)))
    text = {}
    if text_open:
        for k, b in cat.items():
            if not reader.in_text_block(b):
                continue
            t = text.setdefault(b["block_kind"], [0, 0, 0, 0])
            t[0] += 1
            t[2] += b["chars"]
            if k in read:
                t[1] += 1
                t[3] += b["chars"]
    return {"catalog": len(cat), "read": len(read & set(cat)), "by_item": dict(by_item), "header_only": dict(header_only),
            "text": text}


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
