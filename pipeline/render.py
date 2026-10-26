"""Rendus générés depuis les tables (§12.1) : synthesis.md, delta.md, series.md, et le
livrable d'audit (§12.2). Aucun rendu n'est édité à la main : chaque nombre est un jeton
rempli depuis measures, controls ou exclusions, et se retrouve dans audit/numbers.csv avec
l'accession et l'emplacement de chacun de ses termes.

    python -m pipeline.render          # à l'as_of de config.yaml (D-0073)
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
    "end_offset_exceeded": "période non écoulée à la date de coupure", "no_effect_published": "effet non publié",
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
               "MRVL": "Marvell", "WULF": "TeraWulf", "CIFR": "Cipher", "CORZ": "Core Scientific",
               "NBIS": "Nebius", "IREN": "IREN", "APLD": "Applied Digital", "DELL": "Dell", "SMCI": "Supermicro",
               "HUT": "Hut 8", "GLXY": "Galaxy", "AKAM": "Akamai", "BLZE": "Backblaze", "RIOT": "Riot",
               "OWL": "Blue Owl", "APO": "Apollo", "BX": "Blackstone", "INTC": "Intel", "MU": "Micron", "TSM": "TSMC",
               "ASML": "ASML", "SKHY": "SK hynix", "CBRS": "Cerebras"}
NUM_FR = {11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze", 16: "seize", 17: "dix-sept", 18: "dix-huit",
          19: "dix-neuf", 20: "vingt", 21: "vingt et un", 22: "vingt-deux", 23: "vingt-trois", 24: "vingt-quatre",
          25: "vingt-cinq", 26: "vingt-six", 27: "vingt-sept", 28: "vingt-huit", 29: "vingt-neuf", 30: "trente",
          31: "trente et un", 32: "trente-deux", 33: "trente-trois"}


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
        elif fmt == "mn":
            text = fr_num(v / Decimal(10**6), 1) + " M"
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
    # tables chargées en mémoire une fois, dans l'ordre du fichier : une vue relisait et décompressait le
    # Parquet à chaque requête (des milliers de requêtes ponctuelles)
    for name in ("measures", "controls", "exclusions", "links", "observations", "entities", "facts", "documents"):
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM '{t / (name + '.parquet')}'")
    _ONE.clear()
    _ONE["con"] = con
    for r in q(con, "SELECT * FROM measures"):
        _ONE.setdefault((r["measure"], r["subject"], r["period_end"], r["term"], r["view"], r["breakdown_key"],
                         r["counterparty"], r["financing_policy"]), r)
    CP_NAMES.update(cp_names(con))


def cp_names(con):
    """Nom d'affichage d'un groupe de contrepartie : la dénomination telle qu'écrite dans la pièce. Celle de la tête
    (même nom normalisé que la clé du groupe) passe d'abord : une filiale rattachée par extrait ne lui donne pas son
    nom (D-0064, Fluidstack CS I Inc. sous Fluidstack Ltd.). Un groupe propre calculé hors de toute appartenance datée
    (avant une combinaison) garde le même nom."""
    heads = dict(con.execute("""SELECT 'CP:' || normalized_name, min(name) FROM entities WHERE record_kind = 'entity'
                                AND normalized_name IS NOT NULL GROUP BY 1""").fetchall())
    out = {}
    for ref, name in con.execute("""SELECT m.ref, min(e.name) FROM entities m JOIN entities e
                                    ON e.entity_id = m.entity_id AND e.record_kind = 'entity'
                                    WHERE m.record_kind = 'membership' AND m.ref LIKE 'CP:%' GROUP BY 1""").fetchall():
        out[ref] = heads.get(ref, name)
    for ref, name in heads.items():
        out.setdefault(ref, name)
    return out


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



def criteria_diff(old, new):
    """Diff des critères des annexes E et F et des seuils par rapport à leur commit d'origine :
    événements ajoutés, retirés ou modifiés, clés changées (annexe F, statut)."""
    out = []
    oe = ((old.get("annex_f") or {}).get("events") or {})
    ne = ((new.get("annex_f") or {}).get("events") or {})
    add = [k for k in ne if k not in oe]
    rem = [k for k in oe if k not in ne]
    chg = [k for k in ne if k in oe and json.dumps(ne[k], sort_keys=True) != json.dumps(oe[k], sort_keys=True)]
    for k in add:
        e = ne[k]
        out.append(f"annexe F, ajout de {k} ({e.get('added_by', 'décision non citée')}) : « {e.get('observable')} » ; "
                   f"règle {json.dumps(e.get('rule'), ensure_ascii=False)} ; sujets : {e.get('subjects', 'groupes')}")
    for k in rem:
        out.append(f"annexe F, retrait de {k} : « {oe[k].get('observable')} »")
    for k in chg:
        out.append(f"annexe F, {k} modifié : {json.dumps(oe[k], ensure_ascii=False)} → {json.dumps(ne[k], ensure_ascii=False)}")
    same = [k for k in oe if k in ne and k not in chg]
    if same:
        out.append("annexe F, inchangés : " + ", ".join(same) + " (mêmes observables, mêmes règles)")
    rest = {k: v for k, v in (new.get("annex_f") or {}).items() if k != "events"}
    orest = {k: v for k, v in (old.get("annex_f") or {}).items() if k != "events"}
    for k in sorted(set(rest) | set(orest)):
        if json.dumps(rest.get(k), sort_keys=True) != json.dumps(orest.get(k), sort_keys=True):
            out.append(f"annexe F, `{k}` : {json.dumps(orest.get(k), ensure_ascii=False)} → {json.dumps(rest.get(k), ensure_ascii=False)}")
    for blk in ("annex_e", "thresholds"):
        o, n = old.get(blk) or {}, new.get(blk) or {}
        ks = sorted(k for k in set(o) | set(n) if json.dumps(o.get(k), sort_keys=True) != json.dumps(n.get(k), sort_keys=True))
        if ks:
            out.append(f"`{blk}`, clés modifiées : " + ", ".join(f"`{k}`" for k in ks))
    return out

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
    ("cip_change_to_capex", NONE, "Variation des en-cours ÷ capex décaissé", "pct"),
    ("capitalized_interest_to_cip", NONE, "Intérêts capitalisés ÷ en-cours moyen (trimestre, non annualisé)", "pct"),
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
        "F9": "fin d'un contrat de capacité (8-K item 1.02)", "F10": "doute sur la continuité d'exploitation",
        "F11": "juste valeur ÷ coût du portefeuille de prêts d'une BDC en baisse deux trimestres de suite",
        "F12": "intérêts capitalisés d'une BDC (borne basse) en hausse deux trimestres de suite",
        "F13": "prêts sans accumulation d'intérêts d'une BDC (borne basse) en hausse deux trimestres de suite",
        "F14": "ratio de couverture des dettes d'une BDC en baisse deux trimestres de suite",
        "F15": "offre de rachat d'une BDC réduite au prorata (parts acceptées inférieures aux parts apportées)",
        "F16": "interruption d'un programme régulier d'offres de rachat d'une BDC"}
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
        return {"NF:SOFTBANK": "SoftBank", "NF:NSCALE": "Nscale", "NF:LAMBDA": "Lambda", "NF:SAMSUNG": "Samsung",
                "NF:FLUIDSTACK": "Fluidstack"}.get(g, g[3:].title())
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


_ONE = {}      # première ligne de measures par clé de one(), dans l'ordre de la table (voir load)


def one(con, measure, g, pe, term=NONE, view="as_known", breakdown=NONE, counterparty=NONE, policy=NONE):
    if isinstance(term, tuple):
        term, breakdown = term
    key = (measure, g, str(pe), term, view, breakdown, counterparty, policy)
    if _ONE.get("con") is con and all(isinstance(x, str) for x in key):
        r = _ONE.get(key)                        # même ligne que la requête, sans relire la table
        return dict(r) if r is not None else None
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
        L.append(f"- **Critères modifiés depuis leur commit d'origine** `{crit_commit.split()[0]}` "
                 f"({' '.join(crit_commit.split()[1:3])}) : " + ", ".join(f"`{k}`" for k, v in crit.items() if not v)
                 + ". Diff, et ce qui ne change pas :")
        for line in criteria_diff(old, new):
            L.append("  - " + line)
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
                      "groupe, dont l'historique est tronqué à gauche." if rcs else "")
                 + (" Autres ruptures d'historique (D-0048) : " + " ; ".join(
                     f"{GROUP_NAMES.get(g, g)} au {h['effective']} ({h.get('before')})"
                     for g, h in (new.get("history_breaks") or {}).items())
                    + " ; les dépôts antérieurs restent hors du groupe." if new.get("history_breaks") else ""))
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
                e2 = fl.get("outcomes_E2") or {}
                caveat = ("Issues déterminées : " + ", ".join(
                    f"{st[0]}.{st[1:]} {VALUE_FR.get(k, k)} {T.n('measures', {'E7_outcomes': [st, k]}, v)}" for st, k, v in det) +
                    (f". E.2 seule (dépendance de revenu) : {T.n('measures', {'E7_outcomes': ['E2', 'indeterminate']}, e2.get('indeterminate', 0))} "
                     f"issues indéterminées sur {T.n('measures', {'E7_outcomes_total': 'E2'}, sum(e2.values()))}" if e2 else "") +
                    ". Une issue « non étayé » de E.1 dit qu'aucune pièce de lien (L1 à L5) n'est trouvée sous une recherche "
                    "complète au sens de E.0, non que le financement soit sans rapport avec les achats. Complète veut dire que "
                    "tous les blocs du catalogue de lecture des dépôts de la paire sont lus (notes, items de 8-K, pièces annexées, "
                    "Items 404, 9A et 4) ; le rapport de gestion et la description de l'activité n'en font pas partie, si bien "
                    "qu'une pièce L5 qui ne serait que là échapperait à la recherche (D-0069, point 8). "
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
    dup = {t: v for t, v in (stats.get("pk_duplicates") or {}).items() if v.get("dropped")}
    L.append("- **Doublons de clé primaire écartés à l'assemblage** (une ligne gardée par clé, la dernière ; D-0069, point 9) : "
             + (", ".join(f"`{t}` {T.n(t, {'pk_duplicates': t}, v['dropped'])}, dont "
                          f"{T.n(t, {'pk_collisions': t}, v['collision_keys'])} clé(s) en collision" for t, v in sorted(dup.items()))
                if dup else "aucun") + ".")
    stopped, sec, ctl = stop_text(con, T)
    L.append(f"- **Arrêt (§11.4)** : {'oui' if stopped else 'aucun'} ; {sec} ; {ctl}.")
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
    L.append("États de couverture des cellules de l'annexe F (groupe × trimestre ; F11 à F14 : véhicule BDC × date de bilan, "
             "D-0045 et D-0047 ; F15 : véhicule × offre de rachat ; F16 : véhicule × offre qui clôt une série), pour lire ce "
             "qui n'a pas été observé :")
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
    L += lender_portfolio_section(con, T)
    L += lender_liabilities_section(con, T)
    L += montages_section(con, T)
    L += ownership_section(con, T)
    L += nport_section(con, T)
    L += bonds_section(con, T)
    L += unlisted_section(con, T)
    L += credit_section(con, T)
    L += labs_tagged_section(con, T)
    L += labs_ledger_section(con, T)
    L += lab_clauses_section(con, T)
    L += lab_capacity_section(con, T)
    L += backlog_section(con, T)
    L += ppe_components_section(con, T, stats)
    L += lab_events_section(con, T)
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
                      WHERE e.record_kind = 'entity' AND e.normalized_name = ? AND m.ref NOT LIKE 'CP:%' GROUP BY 1
                      ORDER BY 1""",
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



LP_MEAS = ("bdc_portfolio_fv_to_cost", "bdc_portfolio_pik_share", "bdc_portfolio_non_accrual_share",
           "bdc_portfolio_unfunded_ratio", "bdc_portfolio_software_share")


def lp_data(con):
    """Cellules du bloc lender_portfolio par véhicule et date, noms des véhicules, événements F11 à F13."""
    rows = q(con, """SELECT * FROM measures WHERE measure LIKE 'bdc_portfolio_%' AND view = 'as_known'
                     ORDER BY subject, period_end, measure""")
    by = defaultdict(lambda: defaultdict(dict))
    names = defaultdict(dict)
    for r in rows:
        by[r["subject"]][r["period_end"]][r["measure"]] = r
        fl = json.loads(r["flags"]) if r["flags"] else {}
        if fl.get("vehicle"):
            names[r["subject"]][r["period_end"]] = fl["vehicle"]
    evd = defaultdict(lambda: defaultdict(list))
    for e in q(con, """SELECT subject, period_end, breakdown_key FROM measures WHERE measure = 'fragility_event'
                       AND subject LIKE 'cik:%' AND value_text = 'event' ORDER BY period_end"""):
        evd[e["subject"]][e["breakdown_key"]].append(e["period_end"])
    return by, names, evd


def lp_platform(names, terms):
    """Véhicules dont une dénomination, actuelle ou ancienne, porte la marque (D-0045, point 3)."""
    t = [x.lower() for x in terms]
    return sorted(s for s, d in names.items() if any(x in v.lower() for v in d.values() for x in t))


def lp_former_names():
    """Anciennes dénominations EDGAR des véhicules (champ `former` de sub.tsv), par sujet : la marque d'une
    plateforme se lit dans la dénomination actuelle ou ancienne (D-0045, point 3 ; D-0055, point 7)."""
    from . import lender_portfolio as LPM
    out = defaultdict(set)
    if LPM.OUT.exists():
        import pandas as pd
        df = pd.read_parquet(LPM.OUT, columns=["cik", "former"]).drop_duplicates()
        for c, f in zip(df["cik"], df["former"]):
            if f:
                out[f"cik:{str(c).zfill(10)}"].add(str(f))
    return out


def lp_platforms(names, lp):
    """Plateformes de présentation, dans l'ordre de config.yaml : [(marque, véhicules)] (D-0045, point 3 ;
    Apollo et Blackstone depuis D-0055, point 7). Les anciennes dénominations comptent pour la marque,
    sans servir à l'affichage."""
    pl = lp.get("platforms") or {"Blue Owl": {"name_terms": ["Blue Owl", "Owl Rock"]}}
    former = lp_former_names()
    allnames = {s: {**d, **{f"former:{f}": f for f in former.get(s, ())}} for s, d in names.items()}
    return [(b, lp_platform(allnames, p.get("name_terms") or [b])) for b, p in pl.items()]


def lp_platform_text(lp):
    """Phrase de présentation des plateformes (marques et termes de dénomination)."""
    pl = lp.get("platforms") or {"Blue Owl": {"name_terms": ["Blue Owl", "Owl Rock"]}}
    parts = [f"{b} (« " + " » ou « ".join(p.get("name_terms") or [b]) + " »)" for b, p in pl.items()]
    return ("Les plateformes " + ", ".join(parts[:-1]) + " et " + parts[-1] if len(parts) > 1 else "La plateforme " + parts[0]) + \
        (" réunissent" if len(parts) > 1 else " réunit") + " les véhicules dont la dénomination EDGAR, actuelle ou ancienne, " \
        "porte la marque : " + ("des regroupements de présentation, pas des groupes économiques." if len(parts) > 1 else
                                "un regroupement de présentation, pas un groupe économique.")


def lp_cell_txt(T, c):
    if c is None:
        return "—"
    if c["status"] == "bounded":
        return "≥ " + T.m(c, field="value_lower", fmt="pct", dec=2)
    return T.m(c, fmt="pct", dec=2)


def lp_year_before(dates, d):
    """Date de bilan du même véhicule environ un an plus tôt (330 à 400 jours)."""
    d0 = dt.date.fromisoformat(d)
    cand = [x for x in dates if 330 <= (d0 - dt.date.fromisoformat(x)).days <= 400]
    return min(cand, key=lambda x: abs((d0 - dt.date.fromisoformat(x)).days - 365)) if cand else None


def lp_rows(T, by, names, evd, subjects):
    L = ["| Véhicule | Dernier bilan | Juste valeur ÷ coût | — un an plus tôt | Intérêts capitalisés | — un an plus tôt | "
         "Engagements non tirés ÷ portefeuille | F11 (dates) | F12 (dates) |",
         "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
    for s in subjects:
        dates = sorted(by.get(s) or {})
        if not dates:
            continue
        d = dates[-1]
        y = lp_year_before(dates, d)
        m, my = by[s][d], (by[s][y] if y else {})
        L.append(f"| {names[s].get(d) or s} | {d} | {lp_cell_txt(T, m.get('bdc_portfolio_fv_to_cost'))} | "
                 f"{lp_cell_txt(T, my.get('bdc_portfolio_fv_to_cost')) if y else '—'} | "
                 f"{lp_cell_txt(T, m.get('bdc_portfolio_pik_share'))} | "
                 f"{lp_cell_txt(T, my.get('bdc_portfolio_pik_share')) if y else '—'} | "
                 f"{lp_cell_txt(T, m.get('bdc_portfolio_unfunded_ratio'))} | "
                 f"{', '.join(evd[s].get('F11', [])) or 'aucune'} | {', '.join(evd[s].get('F12', [])) or 'aucune'} |")
    return L


def lender_portfolio_section(con, T):
    """Bloc lender_portfolio (D-0045) : portefeuille entier des BDC, par véhicule ; plateformes de présentation
    et repères nommés d'avance, quartiles de l'univers par date de bilan ; événements F11 à F13."""
    import statistics
    cfg = config.load()
    if "lender_portfolio" not in (cfg.get("scope") or []):
        return []
    lp = cfg.get("lender_portfolio") or {}
    by, names, evd = lp_data(con)
    if not by:
        return []
    L = ["## Fragilité du financement : portefeuilles entiers des BDC (bloc `lender_portfolio`, D-0045)", ""]
    L.append("Toutes les BDC des archives en cache, sans sélection ; un véhicule est un déclarant, et rien ne s'additionne "
             "entre véhicules. Vue `as_known` : le premier dépôt d'un véhicule pour une date de bilan. Juste valeur ÷ coût "
             "porte sur les prêts. Les intérêts capitalisés (taux PIK pondéré par le principal, sur le taux total) et les "
             "engagements non tirés sont des bornes basses : une position sans balise compte sans PIK ou sans engagement. "
             "Les événements F11 (juste valeur ÷ coût en baisse deux trimestres de suite) et F12 (intérêts capitalisés en "
             "hausse deux trimestres de suite) ont été fixés avant le calcul (D-0045). " + lp_platform_text(lp))
    L.append("")
    nveh = len(by)
    ndates = sum(len(v) for v in by.values())
    det = {m: sum(1 for v in by.values() for c in v.values() if c.get(m) and c[m]["status"] != "not_determinable")
           for m in LP_MEAS}
    lab = {"bdc_portfolio_fv_to_cost": "juste valeur ÷ coût", "bdc_portfolio_pik_share": "intérêts capitalisés",
           "bdc_portfolio_non_accrual_share": "prêts sans accumulation d'intérêts",
           "bdc_portfolio_unfunded_ratio": "engagements non tirés", "bdc_portfolio_software_share": "part logiciel"}
    L.append(f"- Univers : {T.n('measures', {'lp_vehicles': True}, nveh)} véhicules, "
             f"{T.n('measures', {'lp_vehicle_dates': True}, ndates)} couples véhicule × date de bilan. Mesures déterminées : "
             + ", ".join(f"{lab[m]} {T.n('measures', {'lp_determined': m}, det[m])}" for m in LP_MEAS) + ".")
    L.append("- Les prêts sans accumulation d'intérêts ne sont pas balisés dans `num` (ni axe de statut ni membre) : la mesure "
             "et F13 restent non déterminables. Le secteur n'est presque jamais balisé : la part logiciel aussi. Il faudrait "
             "lire les notes des portefeuilles (niveau 2).")
    L.append("")
    for b, vs in lp_platforms(names, lp):
        L += [f"**Véhicules {b}**", ""] + lp_rows(T, by, names, evd, vs) + [""]
    peers = [f"cik:{p['cik']}" for p in lp.get("peers") or []]
    L += ["**Repères nommés d'avance**", ""] + lp_rows(T, by, names, evd, [p for p in peers if p in by]) + [""]
    # quartiles de l'univers aux dernières dates de bilan communes (au moins 20 véhicules)
    per_date = defaultdict(lambda: defaultdict(list))
    for s, v in by.items():
        for d, m in v.items():
            for k in ("bdc_portfolio_fv_to_cost", "bdc_portfolio_pik_share"):
                c = m.get(k)
                if c and c["status"] != "not_determinable":
                    x = c["value_lower"] if c["status"] == "bounded" else c["value"]
                    if x is not None:
                        per_date[d][k].append(Decimal(str(x)))
    dates = [d for d in sorted(per_date) if len(per_date[d]["bdc_portfolio_fv_to_cost"]) >= 20][-8:]
    if dates:
        L.append("Quartiles de l'univers par date de bilan (premier quartile / médiane / troisième quartile ; des repères, "
                 "jamais des totaux) :")
        L.append("")
        L.append("| Date du bilan | Véhicules | Juste valeur ÷ coût | Intérêts capitalisés (bornes basses) |")
        L.append("| --- | ---: | --- | --- |")

        def qt(meas, d):
            xs = sorted(per_date[d][meas])
            if len(xs) < 4:
                return "—"
            q1, q2, q3 = statistics.quantiles(xs, n=4, method="inclusive")
            return " / ".join(T.n("measures", {"lp_quartile": [meas, d, i]}, v, fr_num(v * 100, 2) + " %")
                              for i, v in ((1, q1), (2, q2), (3, q3)))
        for d in dates:
            L.append(f"| {d} | {T.n('measures', {'lp_vehicles_at': d}, len(per_date[d]['bdc_portfolio_fv_to_cost']))} | "
                     f"{qt('bdc_portfolio_fv_to_cost', d)} | {qt('bdc_portfolio_pik_share', d)} |")
        L.append("")
    ex = q(con, """SELECT reason, count(*) AS n FROM exclusions WHERE item_key LIKE 'lender_portfolio:%' GROUP BY 1 ORDER BY 1""")
    if ex:
        L.append("Exclusions du bloc : " + ", ".join(f"`{r['reason']}` {T.n('exclusions', {'lp_excl': r['reason']}, r['n'])}"
                                                    for r in ex) + " (lignes « Total » de portefeuilles et lignes illisibles, "
                 "par archive).")
        L.append("")
    return L


def f15_txt(f):
    f = f or {}
    if f.get("value_text") == "event":
        return "réduite"
    if f.get("value_text") == "no_event":
        return "servie en entier"
    return "n.d. (" + {"end_offset_exceeded": "offre encore ouverte", "not_disclosed": "résultat non publié",
                       "not_processed": "non lu", "not_collected": "non obtenu"}.get(f.get("nd_reason"), f.get("nd_reason") or "") + ")"


LL_KIND_FR = {"suspension": "suspension des rachats", "termination": "fin des rachats", "merger_agreement": "accord de fusion",
              "merger_termination": "fusion abandonnée", "merger_completion": "fusion réalisée", "listing": "cotation",
              "return_of_capital": "remboursement par distributions", "other": "autre annonce"}


def ll_data(con):
    """Cellules du bloc lender_liabilities : bilan par véhicule et date, offres par véhicule, événements F14 à F16."""
    by = defaultdict(dict)
    names = {}
    for r in q(con, """SELECT * FROM measures WHERE measure LIKE 'bdc_liab_%' AND view = 'as_known'
                       ORDER BY subject, period_end, measure"""):
        by[(r["subject"], r["period_end"])][r["measure"]] = r
        fl = json.loads(r["flags"]) if r["flags"] else {}
        if fl.get("vehicle"):
            names[r["subject"]] = fl["vehicle"]
    offers = defaultdict(dict)
    for r in q(con, """SELECT * FROM measures WHERE (measure LIKE 'bdc_tender_%' OR (measure = 'fragility_event'
                       AND breakdown_key = 'F15')) AND subject LIKE 'cik:%' ORDER BY subject, period_end"""):
        fl = json.loads(r["flags"]) if r["flags"] else {}
        o = offers[fl.get("offer")]
        o.update({"subject": r["subject"], "vehicle": fl.get("vehicle"), "offer_date": fl.get("offer_date"),
                  "end": r["period_end"]})
        o["F15" if r["measure"] == "fragility_event" else r["measure"]] = r
    f16 = [dict(r, fl=json.loads(r["flags"]) if r["flags"] else {}) for r in q(con, """SELECT * FROM measures
           WHERE measure = 'fragility_event' AND breakdown_key = 'F16' ORDER BY period_end, subject""")]
    return by, names, offers, f16


def lender_liabilities_section(con, T):
    """Bloc lender_liabilities (D-0047) : couverture et levier des BDC, offres de rachat (demandes et
    acceptations), événements F14 à F16, annonces lues dans les 8-K."""
    import statistics
    from . import lender_liabilities as LL
    cfg = config.load()
    if "lender_liabilities" not in (cfg.get("scope") or []):
        return []
    lp = cfg.get("lender_portfolio") or {}
    by, names, offers, f16 = ll_data(con)
    if not by:
        return []
    L = ["## Fragilité du financement : passif des BDC et rachats (bloc `lender_liabilities`, D-0047)", ""]
    L.append("Mêmes véhicules que le bloc `lender_portfolio`, sans sélection ni somme entre véhicules. Le ratio de couverture "
             "est celui que publie le véhicule (loi de 1940 : actif net plus dette de premier rang, sur cette dette) ; dette "
             "÷ actif net s'en déduit, et passif total ÷ actif net le majore. Les offres de rachat sont les SC TO-I des "
             "véhicules non cotés : parts apportées, parts acceptées et plafond de l'offre se lisent dans l'amendement final. "
             "Événements fixés avant tout calcul : F14 (couverture en baisse deux trimestres de suite), F15 (offre réduite au "
             "prorata), F16 (interruption d'un programme régulier d'offres). Les demandes ne disent pas qui demande.")
    L.append("")
    cov = Counter((m.get("bdc_liab_asset_coverage") or {}).get("status") for m in by.values())
    nd = Counter((m.get("bdc_liab_asset_coverage") or {}).get("nd_reason") for m in by.values())
    lna = Counter((m.get("bdc_liab_liabilities_to_net_assets") or {}).get("status") for m in by.values())
    L.append(f"- Bilans : {T.n('measures', {'ll_vehicles': True}, len(names))} véhicules, "
             f"{T.n('measures', {'ll_vehicle_dates': True}, len(by))} couples véhicule × date. Couverture publiée et retenue "
             f"{T.n('measures', {'ll_cov': 'computed'}, cov['computed'])} fois ; non balisée "
             f"{T.n('measures', {'ll_cov_nd': 'not_tagged'}, nd['not_tagged'])} ; contraire à l'identité du bilan, souvent le "
             f"seuil légal balisé à la place du ratio, {T.n('measures', {'ll_cov_nd': 'conflicting'}, nd['conflicting'])} ; "
             f"hors échelle {T.n('measures', {'ll_cov_nd': 'parse_failed'}, nd['parse_failed'])}. Passif ÷ actif net "
             f"calculé {T.n('measures', {'ll_lna': 'computed'}, lna['computed'])} fois.")
    res = Counter()
    for o in offers.values():
        f = o.get("F15") or {}
        res[f.get("value_text") or f.get("nd_reason")] += 1
    L.append(f"- Offres de rachat de parts dans la fenêtre : {T.n('measures', {'ll_offers': True}, len(offers))}, chez "
             f"{T.n('measures', {'ll_offer_vehicles': True}, len({o['subject'] for o in offers.values()}))} véhicules. "
             f"F15 tranché : {T.n('measures', {'ll_f15': 'read'}, res['event'] + res['no_event'])} ; réduites au prorata "
             f"{T.n('measures', {'ll_f15': 'event'}, res['event'])} ; encore ouvertes à `as_of` "
             f"{T.n('measures', {'ll_f15': 'end_offset_exceeded'}, res['end_offset_exceeded'])} ; résultat non publié "
             f"{T.n('measures', {'ll_f15': 'not_disclosed'}, res['not_disclosed'])} (dont les parts acceptées non chiffrées).")
    L.append("")

    def val(c):
        if not c or c["status"] == "not_determinable" or c["value"] is None:
            return None
        return Decimal(str(c["value"]))

    def cell_txt(c, fmt):
        if c is None:
            return "—"
        if fmt == "x":
            return T.m(c, fmt="x") if c["value"] is not None else T.m(c)
        return T.m(c, fmt="pct", dec=0)
    plats = lp_platforms({s: {"_": n} for s, n in names.items()}, lp)
    peers = [f"cik:{p['cik']}" for p in lp.get("peers") or [] if f"cik:{p['cik']}" in names]
    ev14 = defaultdict(list)
    for r in q(con, """SELECT subject, period_end FROM measures WHERE measure = 'fragility_event' AND breakdown_key = 'F14'
                       AND value_text = 'event' ORDER BY period_end"""):
        ev14[r["subject"]].append(r["period_end"])

    def lev_rows(subjects):
        out = ["| Véhicule | Dernier bilan | Couverture | Dette ÷ actif net | — un an plus tôt | Passif ÷ actif net | F14 (dernières dates) |",
               "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
        for s in subjects:
            ds = sorted(d for (ss, d) in by if ss == s)
            if not ds:
                continue
            d = ds[-1]
            y = lp_year_before(ds, d)
            m, my = by[(s, d)], (by[(s, y)] if y else {})
            out.append(f"| {names[s]} | {d} | {cell_txt(m.get('bdc_liab_asset_coverage'), 'pct')} | "
                       f"{cell_txt(m.get('bdc_liab_debt_to_net_assets'), 'x')} | "
                       f"{cell_txt(my.get('bdc_liab_debt_to_net_assets'), 'x') if y else '—'} | "
                       f"{cell_txt(m.get('bdc_liab_liabilities_to_net_assets'), 'x')} | "
                       f"{', '.join(ev14[s][-3:]) or 'aucune'} |")
        return out
    for b, vs in plats:
        L += [f"**Levier des véhicules {b}**", ""] + lev_rows(vs) + [""]
    L += ["**Levier des repères nommés d'avance**", ""] + lev_rows(peers) + [""]
    per = defaultdict(lambda: defaultdict(list))
    for (s, d), m in by.items():
        for k in ("bdc_liab_debt_to_net_assets", "bdc_liab_liabilities_to_net_assets"):
            x = val(m.get(k))
            if x is not None:
                per[d][k].append(x)
    dates = [d for d in sorted(per) if len(per[d]["bdc_liab_debt_to_net_assets"]) >= 20][-6:]
    if dates:
        L.append("Quartiles de l'univers par date de bilan (premier quartile / médiane / troisième quartile ; des repères, "
                 "jamais des totaux). Dette ÷ actif net sur les seuls véhicules qui publient leur couverture :")
        L.append("")
        L.append("| Date du bilan | Véhicules (couverture) | Dette ÷ actif net | Véhicules (passif) | Passif ÷ actif net |")
        L.append("| --- | ---: | --- | ---: | --- |")

        def qt(meas, d):
            xs = sorted(per[d][meas])
            if len(xs) < 4:
                return "—"
            q1, q2, q3 = statistics.quantiles(xs, n=4, method="inclusive")
            return " / ".join(T.n("measures", {"ll_quartile": [meas, d, i]}, v, fr_num(v, 2) + " x")
                              for i, v in ((1, q1), (2, q2), (3, q3)))
        for d in dates:
            L.append(f"| {d} | {T.n('measures', {'ll_n_at': ['de', d]}, len(per[d]['bdc_liab_debt_to_net_assets']))} | "
                     f"{qt('bdc_liab_debt_to_net_assets', d)} | "
                     f"{T.n('measures', {'ll_n_at': ['lna', d]}, len(per[d]['bdc_liab_liabilities_to_net_assets']))} | "
                     f"{qt('bdc_liab_liabilities_to_net_assets', d)} |")
        L.append("")
    # rachats : trimestre d'expiration, toute l'univers
    tq = defaultdict(lambda: {"n": 0, "read": 0, "ev": 0, "dem": []})
    for o in offers.values():
        e = o["end"] or o["offer_date"]
        k = f"{e[:4]} T{(int(e[5:7]) - 1) // 3 + 1}"
        f = o.get("F15") or {}
        tq[k]["n"] += 1
        tq[k]["read"] += f.get("value_text") in ("event", "no_event")
        tq[k]["ev"] += f.get("value_text") == "event"
        x = val(o.get("bdc_tender_demand_ratio"))
        if x is not None:
            tq[k]["dem"].append(x)
    L.append("**Rachats, par trimestre d'expiration des offres (tous les véhicules qui en font)**")
    L.append("")
    L.append("| Trimestre | Offres | F15 tranché | Réduites au prorata (F15) | Demande médiane ÷ plafond | Offres au-delà du plafond |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for k in sorted(tq):
        t = tq[k]
        med = statistics.median(t["dem"]) if t["dem"] else None
        L.append(f"| {k} | {T.n('measures', {'ll_q_offers': k}, t['n'])} | {T.n('measures', {'ll_q_read': k}, t['read'])} | "
                 f"{T.n('measures', {'ll_q_f15': k}, t['ev'])} | "
                 f"{T.n('measures', {'ll_q_dem_med': k}, med, fr_num(med, 2)) if med is not None else '—'} "
                 f"({T.n('measures', {'ll_q_dem_n': k}, len(t['dem']))} offres) | "
                 f"{T.n('measures', {'ll_q_dem_over': k}, sum(1 for x in t['dem'] if x > 1))} |")
    L.append("")
    L.append("La demande rapporte les parts apportées au plafond de l'offre (en général 5 % des parts) ; elle n'est calculée "
             "que si l'amendement ou l'offre donne ce plafond dans la même unité.")
    L.append("")

    def offer_rows(subjects, n_last=6):
        out = ["| Véhicule | Expiration | Demande ÷ plafond | Acceptées ÷ apportées | F15 |", "| --- | --- | ---: | ---: | --- |"]
        for s in subjects:
            os_ = sorted((o for o in offers.values() if o["subject"] == s), key=lambda o: o["end"] or "")
            for o in os_[-n_last:]:
                out.append(f"| {o['vehicle']} | {o['end']} | {cell_txt(o.get('bdc_tender_demand_ratio'), 'x')} | "
                           f"{cell_txt(o.get('bdc_tender_acceptance_ratio'), 'pct')} | {f15_txt(o.get('F15'))} |")
        return out
    peer_t = [s for s in peers if any(o["subject"] == s for o in offers.values())]
    for b, vs in plats:
        pl_t = [s for s in vs if any(o["subject"] == s for o in offers.values())]
        if pl_t:
            L += [f"**Rachats des véhicules {b} (six dernières offres)**", ""] + offer_rows(pl_t) + [""]
    L += ["**Rachats des repères non cotés (six dernières offres)**", ""] + offer_rows(peer_t) + [""]
    ann = LL.announcements_by_cik()
    L.append("**F16, interruptions d'un programme régulier d'offres**")
    L.append("")
    evs = [r for r in f16 if r["value_text"] == "event"]
    st = Counter(r["value_text"] or r["nd_reason"] for r in f16)
    L.append(f"- Cellules : {T.n('measures', {'ll_f16': 'event'}, st['event'])} événements, "
             f"{T.n('measures', {'ll_f16': 'no_event'}, st['no_event'])} sans événement, "
             f"{T.n('measures', {'ll_f16': 'open'}, st['end_offset_exceeded'])} dont les 120 jours ne sont pas écoulés.")
    for r in evs:
        fl = r["fl"]
        cik = r["subject"].split(":", 1)[1]
        why = [f"{LL_KIND_FR.get(a['kind'], a['kind'])} ({a['date']} : {a.get('note')})" for a in ann.get(cik, [])
               if a.get("reason") == "f16"]
        L.append(f"- {fl.get('entity')} : dernière offre le {fl.get('last_offer')}, aucune dans les 120 jours (événement daté "
                 f"du {r['period_end']}). " + (("8-K lus : " + " ; ".join(why) + ".") if why else "Aucun 8-K lu n'en donne la cause."))
    L.append("")
    owl_ann = [a for c_, xs in ann.items() for a in xs if a.get("reason") == "blue_owl"]
    if owl_ann:
        L.append("**Annonces des véhicules Blue Owl lues dans leurs 8-K (les plus récentes d'abord, plafond de 40 unités)**")
        L.append("")
        for a in sorted(owl_ann, key=lambda a: a["date"], reverse=True):
            L.append(f"- {a['date']}, {a['entity']} — {LL_KIND_FR.get(a['kind'], a['kind'])} : {a.get('note')}. "
                     f"« {a['quote'][:220]}{'…' if len(a['quote']) > 220 else ''} »")
        L.append("")
    ex = q(con, """SELECT reason, count(*) AS n FROM exclusions WHERE item_key LIKE 'lender_liabilities:%' GROUP BY 1 ORDER BY 1""")
    if ex:
        L.append("Exclusions du bloc : " + ", ".join(f"`{r['reason']}` {T.n('exclusions', {'ll_excl': r['reason']}, r['n'])}"
                                                    for r in ex) + " (offres sur des obligations ou des actions de préférence ; "
                 "8-K au-delà du plafond de lecture).")
        L.append("")
    return L


def montages_section(con, T):
    """Bloc montages (D-0046) : montages que les notes d'un groupe décrivent sans les nommer,
    identifiés par des extraits des deux côtés ; montants tirés des lignes validées."""
    cfg = config.load()
    if "montages" not in (cfg.get("scope") or []) or not cfg.get("identified_ventures"):
        return []
    L = ["## Montages identifiés (bloc `montages`, D-0046)", ""]
    L.append("Un montage que les notes d'un groupe décrivent sans nommer son financeur, identifié par des extraits "
             "cités des deux côtés (au moins trois traits concordants). Les montants viennent des lignes validées des "
             "deux côtés ; ils ne s'additionnent pas.")
    L.append("")
    for v in cfg["identified_ventures"]:
        cks = [e["block"] for e in (v.get("group_blocks") or []) + (v.get("financier_blocks") or [])]
        rows = q(con, f"""SELECT obs_key, content_key, group_id, form, knowledge_date, counterparty_name, family, edge_type,
                             amount, amount_qualifier, measurement_basis, instrument_key FROM observations
                          WHERE validation_state = 'valid' AND kind = 'observation' AND amount IS NOT NULL
                          AND CAST(block_kind AS VARCHAR) = 'montage_text'
                          AND content_key IN ({','.join('?' * len(cks))}) ORDER BY knowledge_date, obs_key""", *cks)
        L.append(f"**{v['name']}** — « {v.get('group_term')} » dans les notes de {GROUP_NAMES.get(v['group'], v['group'])}")
        L.append("")
        L.append("- Membres : " + " ; ".join(f"{m['name']} {m['interest']}" for m in v.get("members") or []) + ".")
        L.append("- Traits concordants : " + " ; ".join(f"{t}" for t in (v.get("traits") or {}).values()) + ".")
        lab = {"lease_financing": "distribution reçue par Meta à la formation",
               "capacity_lease": "baux d'exploitation (engagement initial, à partir de 2029)",
               "residual_value_guarantee": "garantie de valeur résiduelle de Meta (seuil de départ)",
               "equity_primary": "engagement de fonds propres de Blue Owl Real Estate Net Lease Trust",
               "loan_or_facility": "obligations garanties de Beignet Investor LLC (6,581 %, 2049)"}
        for r in rows:
            amt = Decimal(str(r["amount"]))
            L.append(f"- {lab.get(r['edge_type'], r['edge_type'])} : "
                     f"{T.n('observations', {'montage_amount': r['obs_key']}, amt, fr_num(amt / Decimal(10**9), 2) + ' Md$')}"
                     f"{' (environ)' if r['amount_qualifier'] == 'approximately' else ''}"
                     f"{' (au plus)' if r['amount_qualifier'] == 'up_to' else ''} — {group_label(r['group_id'])}, {r['form']} rendu public le {r['knowledge_date']}.")
        L.append("- Les notes suivantes de Meta (10-K 2025, 10-Q de 2026) ne nomment plus que « the Venture » : leurs lignes "
                 "restent des abstentions (`no_named_counterparty`), et l'identification se lit ici.")
        L.append("")
    ex = q(con, """SELECT reason, count(*) AS n FROM exclusions WHERE item_key LIKE 'montages:%' GROUP BY 1 ORDER BY 1""")
    if ex:
        L.append("Exclusions du bloc : " + ", ".join(f"`{r['reason']}` {T.n('exclusions', {'mt_excl': r['reason']}, r['n'])}"
                                                    for r in ex) + " (relevés de portefeuille non lus, pièces écartées "
                 "par la règle d'un montage ou sans paragraphe qualifiant, textes au-delà du plafond ; D-0046, D-0049).")
        L.append("")
    return L

def nport_cells(con, subject="NF:SOFTBANK"):
    """Cellules nport_price_to_par d'un nœud (D-0058, volet F ; D-0071, volet B), par titre, dans l'ordre des dates de
    portefeuille."""
    by = defaultdict(list)
    for r in q(con, """SELECT * FROM measures WHERE measure = 'nport_price_to_par' AND view = 'as_known' AND subject = ?
                       ORDER BY breakdown_key, period_end""", subject):
        r["fl"] = json.loads(r["flags"]) if r["flags"] else {}
        by[r["breakdown_key"]].append(r)
    return by


def nport_title(sec, fl):
    """Émetteur, coupon, échéance et monnaie d'un titre, tels que les fonds les déclarent le plus souvent."""
    iss = (fl.get("issuer") or "").upper()
    name = "SoftBank Group" if "GROUP" in iss else ("SoftBank Corp." if "SOFTBANK CORP" in iss else (fl.get("issuer") or "?"))
    cp = fl.get("coupon")
    cp = fr_num(Decimal(str(cp)), 3).rstrip("0").rstrip(",") + " %" if cp not in (None, "") else "coupon n.d."
    return f"{name} {cp}, échéance {fl.get('maturity') or 'n.d.'} ({fl.get('currency')}, {sec})"


def nport_section(con, T):
    """Volet F de D-0058 : obligations de SoftBank valorisées par les fonds (Form N-PORT Data Sets)."""
    by = nport_cells(con)
    if not by:
        return []
    last_date = max(r["period_end"] for rs in by.values() for r in rs)
    recent = (dt.date.fromisoformat(last_date) - dt.timedelta(days=92)).isoformat()
    L = ["## Obligations de SoftBank valorisées par les fonds (Form N-PORT)", ""]
    L.append("Valeur que les fonds déclarent pour les obligations de SoftBank Group et de SoftBank Corp. qu'ils détiennent, "
             "rapportée au nominal, dans la monnaie du titre (Form N-PORT Data Sets ; D-0058, points 8, 27 et 28). Une cellule "
             "par titre (ISIN) et par date de portefeuille, au dernier dépôt de chaque série ; chaque fonds déclare à la fin de "
             "son propre trimestre. C'est une valorisation déclarée par des tiers, jamais une probabilité de défaut ni un fait "
             "comptable de SoftBank : elle n'entre dans aucune mesure de financement ni dans l'annexe F. Les positions d'autres "
             "émetteurs déclarées sous le nom ou le LEI de SoftBank Group (Sprint, Fortress) en sont écartées. La série complète "
             "est dans `series.md`.")
    L.append("")
    n = sum(len(v) for v in by.values())
    L.append(f"Cellules : {T.n('measures', {'measure': 'nport_price_to_par', 'subject': 'NF:SOFTBANK'}, n)}, sur "
             f"{T.n('measures', {'measure': 'nport_price_to_par', 'subject': 'NF:SOFTBANK', 'securities': True}, len(by))} titres, du "
             f"{min(r['period_end'] for rs in by.values() for r in rs)} au {last_date}.")
    L.append("")
    L.append(f"Titres détenus par au moins un fonds dans les trois mois qui précèdent la dernière date de portefeuille ({last_date}) :")
    L.append("")
    L.append("| Titre | Dernière date | Valeur ÷ nominal | Séries | Nominal détenu | Plus bas (date) | Première date (valeur ÷ nominal) |")
    L.append("| --- | --- | ---: | ---: | ---: | --- | --- |")
    gone = []
    for sec, rs in sorted(by.items(), key=lambda kv: (kv[1][-1]["fl"].get("maturity") or "", kv[0])):
        last = rs[-1]
        if last["period_end"] < recent:
            gone.append(sec)
            continue
        lo = min(rs, key=lambda r: (Decimal(str(r["value"])), r["period_end"]))
        fl = last["fl"]
        L.append(f"| {nport_title(sec, fl)} | {last['period_end']} | {T.m(last, fmt='pct')} | "
                 f"{T.n('measures', {'nport_series': [sec, last['period_end']]}, fl.get('n_series'))} | "
                 f"{T.m(last, 'denominator', fmt='mn')} {fl.get('currency')} | {T.m(lo, fmt='pct')} ({lo['period_end']}) | "
                 f"{rs[0]['period_end']} ({T.m(rs[0], fmt='pct')}) |")
    L.append("")
    L.append(f"Titres sans position déclarée dans ces trois mois (remboursés, rachetés ou cédés par les fonds) : "
             f"{T.n('measures', {'measure': 'nport_price_to_par', 'subject': 'NF:SOFTBANK', 'securities_without_recent_position': True}, len(gone))}.")
    L.append("")
    return L


def bond_nodes():
    """Nœuds du volet B de D-0071, dans l'ordre de la configuration."""
    return [i["node"] for i in ((config.load().get("nport") or {}).get("bonds") or {}).get("issuers") or []]


def bond_title(sec, fl):
    """Émetteur, coupon, échéance et monnaie d'un titre du volet B de D-0071, tels que les fonds les déclarent le plus
    souvent ; « convertible » si une position au moins remplit l'Item C.9.f. Un taux annuel déclaré en fraction (sous
    0,25, « 0,047 » pour 4,7 %) s'affiche en pourcentage, signalé."""
    cp = fl.get("coupon")
    if cp in (None, ""):
        cp = "coupon n.d."
    else:
        c = Decimal(str(cp))
        frac = 0 < c < Decimal("0.25")
        cp = fr_num(c * 100 if frac else c, 3).rstrip("0").rstrip(",") + " %" + (" (déclaré en fraction)" if frac else "")
    conv = ", convertible" if fl.get("convertible") else ""
    return f"{fl.get('issuer') or '?'} {cp}{conv}, échéance {fl.get('maturity') or 'n.d.'} ({fl.get('currency')}, {sec})"


def bonds_section(con, T):
    """Volet B de D-0071 : obligations d'Oracle, de CoreWeave et de Beignet valorisées par les fonds (Form N-PORT)."""
    nodes = [(g, nport_cells(con, g)) for g in bond_nodes()]
    nodes = [(g, by) for g, by in nodes if by]
    if not nodes:
        return []
    L = ["## Obligations d'Oracle, de CoreWeave et de Beignet valorisées par les fonds (Form N-PORT)", ""]
    L.append("Valeur que les fonds déclarent pour les obligations qu'ils détiennent, rapportée au nominal, dans la monnaie du "
             "titre : la mesure des obligations de SoftBank, sur trois autres nœuds (Form N-PORT Data Sets ; D-0058, points 8 "
             "et 28 ; D-0071, point 4). Une cellule par titre (ISIN) et par date de portefeuille, au dernier dépôt de chaque "
             "série, tous niveaux de juste valeur confondus ; chaque fonds déclare à la fin de son propre trimestre. L'émetteur "
             "se reconnaît au début de son nom (« Oracle Corp », « CoreWeave », « Beignet Investor ») : les titres des filiales "
             "de CoreWeave qui portent son nom en sont, ceux de « Vantage Oracle TX » ou d'« Oracle Vision Holdco » non. C'est "
             "une tension de marché déclarée par des tiers (perspective `counterparty`), jamais une probabilité de défaut ni un "
             "fait comptable de l'émetteur : elle n'entre ni dans le financement, ni dans l'exposition, les paires, les cycles "
             "ou l'annexe F. La série complète est dans `series.md`.")
    L.append("")
    for g, by in nodes:
        last_date = max(r["period_end"] for rs in by.values() for r in rs)
        recent = (dt.date.fromisoformat(last_date) - dt.timedelta(days=92)).isoformat()
        n = sum(len(v) for v in by.values())
        L.append(f"**{group_label(g)} ({g})** : {T.n('measures', {'measure': 'nport_price_to_par', 'subject': g}, n)} cellules, "
                 f"sur {T.n('measures', {'measure': 'nport_price_to_par', 'subject': g, 'securities': True}, len(by))} titres, "
                 f"du {min(r['period_end'] for rs in by.values() for r in rs)} au {last_date}. Titres détenus par au moins un "
                 f"fonds dans les trois mois qui précèdent la dernière date de portefeuille :")
        L.append("")
        L.append("| Titre | Dernière date | Valeur ÷ nominal | Séries | Nominal détenu | Plus bas (date) | Première date (valeur ÷ nominal) |")
        L.append("| --- | --- | ---: | ---: | ---: | --- | --- |")
        gone = []
        for sec, rs in sorted(by.items(), key=lambda kv: (kv[1][-1]["fl"].get("maturity") or "", kv[0])):
            last = rs[-1]
            if last["period_end"] < recent:
                gone.append(sec)
                continue
            lo = min(rs, key=lambda r: (Decimal(str(r["value"])), r["period_end"]))
            fl = last["fl"]
            L.append(f"| {bond_title(sec, fl)} | {last['period_end']} | {T.m(last, fmt='pct')} | "
                     f"{T.n('measures', {'nport_series': [g, sec, last['period_end']]}, fl.get('n_series'))} | "
                     f"{T.m(last, 'denominator', fmt='mn')} {fl.get('currency')} | {T.m(lo, fmt='pct')} ({lo['period_end']}) | "
                     f"{rs[0]['period_end']} ({T.m(rs[0], fmt='pct')}) |")
        L.append("")
        L.append(f"Titres sans position déclarée dans ces trois mois (échus, remboursés, rachetés ou cédés par les fonds) : "
                 f"{T.n('measures', {'measure': 'nport_price_to_par', 'subject': g, 'securities_without_recent_position': True}, len(gone))}.")
        L.append("")
    return L


def bonds_series(con, T):
    """Volet B de D-0071 : série complète, une table par titre et par nœud."""
    L = []
    for g in bond_nodes():
        by = nport_cells(con, g)
        if not by:
            continue
        L.append(f"## {group_label(g)} ({g}) : obligations valorisées par les fonds (Form N-PORT)")
        L.append("")
        L.append("Valeur déclarée ÷ nominal, dans la monnaie du titre, au dernier dépôt de chaque série pour la date de "
                 "portefeuille, tous niveaux de juste valeur ; nombre de séries (un fonds fermé sans série compte pour une). "
                 "Perspective `counterparty` : une tension de marché déclarée par des tiers, jamais une probabilité de défaut "
                 "ni un fait comptable de l'émetteur (D-0071, point 4).")
        L.append("")
        for sec, rs in sorted(by.items(), key=lambda kv: (kv[1][-1]["fl"].get("maturity") or "", kv[0])):
            L.append(f"**{bond_title(sec, rs[-1]['fl'])}**")
            L.append("")
            L.append("| Date de portefeuille | Valeur ÷ nominal | Séries |")
            L.append("| --- | ---: | ---: |")
            for r in rs:
                L.append(f"| {r['period_end']} | {T.m(r, fmt='pct')} | "
                         f"{T.n('measures', {'nport_series': [g, sec, r['period_end']]}, r['fl'].get('n_series'))} |")
            L.append("")
    return L


def ownership_cells(con):
    """Cellules de D-0071, volet A, par paire (financeur, société) : positions au 13F et parts aux annexes 13D et 13G."""
    pos, stake = defaultdict(list), defaultdict(list)
    for r in q(con, """SELECT * FROM measures WHERE measure IN ('ownership_position', 'ownership_stake') AND view = 'as_known'
                       ORDER BY subject, counterparty, period_end, breakdown_key"""):
        r["fl"] = json.loads(r["flags"]) if r["flags"] else {}
        (pos if r["measure"] == "ownership_position" else stake)[(r["subject"], r["counterparty"])].append(r)
    return pos, stake


def ownership_exits(pos, stake):
    """Sorties publiées d'une paire : date de portefeuille du 13F sans ligne, ou date de l'événement d'une annexe à
    zéro action."""
    out = [r["fl"]["exit_next"]["date"] for r in pos if r["fl"].get("exit_next")]
    out += [r["period_end"] for r in stake if r["value"] is not None and Decimal(str(r["value"])) == 0]
    return sorted(set(out))


def ownership_section(con, T):
    """D-0071, volet A : déclarations de détention des paires du statut « financé » (13F, 13D, 13G)."""
    pos, stake = ownership_cells(con)
    if not pos and not stake:
        return []
    L = ["## Déclarations de détention (13F, 13D, 13G)", ""]
    L.append("Actions qu'un financeur déclare détenir dans une société de ses paires : au 13F (table d'information, par "
             "date de portefeuille) et aux annexes 13D et 13G (page de couverture, à la date de l'événement), lues par "
             "leurs champs, sans lecture de texte (D-0071, point 3). Ces déclarations prouvent une détention à une date, "
             "jamais son origine : elles n'ouvrent jamais la condition (a) du statut « financé », faute d'opération "
             "primaire attestée (§3.2). Une sortie publiée la ferme : un 13F complet sans ligne de la société après un 13F "
             "qui en portait, aucun des deux ne déclarant de traitement confidentiel, ou une annexe à zéro action. Elle ne "
             "ferme que les détentions en actions (`equity_primary`) de la paire ; obligations convertibles, bons et prêts "
             "restent ouverts. Les valeurs sont celles que le financeur déclare (en milliers de dollars avant 2023, "
             "converties). Ni position ni part n'entre dans le revenu, l'exposition, les paires ou l'annexe F ; la série "
             "complète est dans `series.md`.")
    L.append("")
    L.append(f"Cellules : {T.n('measures', {'measure': 'ownership_position'}, sum(len(v) for v in pos.values()))} positions "
             f"au 13F et {T.n('measures', {'measure': 'ownership_stake'}, sum(len(v) for v in stake.values()))} parts aux "
             "annexes 13D et 13G.")
    L.append("")
    L.append("| Paire | Positions au 13F | Dernière position (date de portefeuille) | Valeur déclarée | Dernière annexe "
             "(date de l'événement) | Sorties publiées | Statut « financé » au dernier trimestre |")
    L.append("| --- | ---: | --- | ---: | --- | --- | --- |")
    for k in sorted(set(pos) | set(stake), key=lambda k: (group_label(k[0]), group_label(k[1]))):
        ps, ss = pos.get(k, []), stake.get(k, [])
        last, ls = (ps[-1] if ps else None), (ss[-1] if ss else None)
        v = Decimal(last["fl"]["value_usd"]) if last else None
        st = q(con, """SELECT value_text, period_end FROM measures WHERE measure = 'financed_status' AND subject = ?
                       AND counterparty = ? AND view = 'as_known' AND financing_policy = 'exposure_outstanding'
                       ORDER BY period_end DESC LIMIT 1""", k[0], k[1])
        ex = ownership_exits(ps, ss)
        L.append(f"| {group_label(k[0])} → {group_label(k[1])} | "
                 f"{T.n('measures', {'measure': 'ownership_position', 'pair': list(k)}, len(ps))} | "
                 + (f"{T.m(last, fmt='count')} actions ({last['period_end']})" if last else "—") + " | "
                 + (T.n('measures', {'ownership_value_usd': [k[0], k[1], last['period_end']]}, v,
                        text=fr_num(v / Decimal(10**6), 0) + " M$") if last else "—") + " | "
                 + (f"{T.m(ls, fmt='pct')} ({ls['period_end']}, {ls['fl'].get('form')})" if ls else "—") + " | "
                 + (", ".join(ex) or "aucune") + " | "
                 + (f"{st[0]['value_text']} ({st[0]['period_end']})" if st else "—") + " |")
    L.append("")
    return L


def ownership_series(con, T):
    """D-0071, volet A : par paire, chaque position au 13F et chaque annexe 13D ou 13G."""
    pos, stake = ownership_cells(con)
    L = []
    for k in sorted(set(pos) | set(stake), key=lambda k: (group_label(k[0]), group_label(k[1]))):
        L.append(f"## {group_label(k[0])} ({k[0]}) → {group_label(k[1])} ({k[1]}) : déclarations de détention")
        L.append("")
        L.append("Actions déclarées par le financeur au 13F (date de portefeuille) ou à une annexe 13D ou 13G (date de "
                 "l'événement) ; perspective du déclarant, descriptive (D-0071, point 3).")
        L.append("")
        L.append("| Date | Déclaration | Actions | Valeur déclarée | Part de la catégorie | Sortie publiée ensuite |")
        L.append("| --- | --- | ---: | ---: | ---: | --- |")
        rows = [("13F", r) for r in pos.get(k, [])] + [(r["fl"].get("form") or "13D/G", r) for r in stake.get(k, [])]
        for src, r in sorted(rows, key=lambda x: (x[1]["period_end"], x[0], x[1]["breakdown_key"])):
            fl = r["fl"]
            if src == "13F":
                v = Decimal(fl["value_usd"])
                L.append(f"| {r['period_end']} | 13F | {T.m(r, fmt='count')} | "
                         f"{T.n('measures', {'ownership_value_usd': [k[0], k[1], r['period_end']]}, v, text=fr_num(v / Decimal(10**6), 1) + ' M$')}"
                         f" | — | {(fl.get('exit_next') or {}).get('date') or ''} |")
            else:
                sh = Decimal(fl.get("shares") or 0)
                L.append(f"| {r['period_end']} | {src} | "
                         f"{T.n('measures', {'ownership_stake_shares': [k[0], k[1], r['breakdown_key']]}, sh)} | — | "
                         f"{T.m(r, fmt='pct')} | {'zéro action : sortie' if r['value'] is not None and Decimal(str(r['value'])) == 0 else ''} |")
        L.append("")
    return L


def unlisted_cells(con):
    """Cellules de D-0065, par nœud : valeurs par action (nport_equity_mark) et valeurs détenues (nport_equity_held)."""
    marks, held = defaultdict(list), defaultdict(list)
    for r in q(con, """SELECT * FROM measures WHERE measure IN ('nport_equity_mark', 'nport_equity_held') AND view = 'as_known'
                       ORDER BY subject, period_end, counterparty, breakdown_key"""):
        r["fl"] = json.loads(r["flags"]) if r["flags"] else {}
        (marks if r["measure"] == "nport_equity_mark" else held)[r["subject"]].append(r)
    return marks, held


def per_share(T, r):
    return T.m(r, fmt="num", dec=2) + (f" {r['unit']}" if r.get("unit") and r.get("value") is not None else "")


def unlisted_section(con, T):
    """D-0065 : marques de tiers des non-cotés du modèle, déclarées par les fonds enregistrés (Form N-PORT)."""
    marks, held = unlisted_cells(con)
    if not marks and not held:
        return []
    L = ["## Non-cotés du modèle valorisés par les fonds (Form N-PORT)", ""]
    L.append("Valeur par action que des fonds enregistrés déclarent pour les actions d'un nœud du modèle qu'ils évaluent "
             "eux-mêmes (niveau 3 de la hiérarchie de juste valeur), au dernier dépôt de chaque série pour la date de "
             "portefeuille, et somme de ces valeurs par trimestre civil (Form N-PORT Data Sets ; D-0065). Une position n'est "
             "rattachée que si le nom d'émetteur déclaré commence par une dénomination légale du registre, ou n'est formé que "
             "d'un terme de la configuration qui désigne une seule entité, suivi de mots de catégorie ou d'instrument "
             "(« ANTHROPIC SERIES G » ; D-0066, point 3), et une entité cotée n'y entre qu'avant son introduction en bourse. "
             "Ce sont des marques déclarées par des tiers (perspective "
             "`counterparty`) : jamais une valorisation du nœud ni un fait comptable, hors des mesures de financement, de "
             "l'exposition, des paires et de l'annexe F. Deux fonds peuvent détenir deux catégories d'actions différentes : "
             "leurs valeurs par action ne se comparent qu'à titre égal. Le détail par fonds et par titre est dans `series.md`.")
    L.append("")
    L.append("Le dernier trimestre est le dernier trimestre civil complet : un N-PORT se dépose dans les 60 jours qui suivent la "
             "fin du trimestre du fonds, si bien que le trimestre en cours à la dernière archive n'est couvert qu'en partie, comme "
             "le premier de la période ; ces trimestres sont marqués « partiel ».")
    L.append("")
    L.append("| Nœud | Dernier trimestre | Valeur détenue déclarée | Séries | Valeur par action à la dernière date (plus basse – plus haute) | Premier trimestre (valeur détenue) |")
    L.append("| --- | --- | ---: | ---: | --- | --- |")
    def last_full(hs):
        full = [h for h in hs if h["status"] == "computed"]
        return full[-1] if full else hs[-1]
    order = sorted(held, key=lambda s: (-(Decimal(str(last_full(held[s])["value"])) if last_full(held[s])["value"] is not None
                                          else 0), s))
    for s in order:
        hs, ms = held[s], [m for m in marks.get(s, []) if m["value"] is not None]
        h = last_full(hs)
        last = max((m["period_end"] for m in ms), default=None)
        at = [m for m in ms if m["period_end"] == last]
        lo = min(at, key=lambda m: (Decimal(str(m["value"])), m["counterparty"], m["breakdown_key"])) if at else None
        hi = max(at, key=lambda m: (Decimal(str(m["value"])), m["counterparty"], m["breakdown_key"])) if at else None
        rng = (f"{per_share(T, lo)} – {per_share(T, hi)} ({last})" if lo is not None and lo is not hi
               else (f"{per_share(T, lo)} ({last})" if lo is not None else "—"))
        L.append(f"| {group_label(s)} | {h['period_end']} | {T.m(h)} | "
                 f"{T.n('measures', {'nport_unlisted_series': [s, h['period_end']]}, h['fl'].get('series'))} | {rng} | "
                 f"{hs[0]['period_end']} ({T.m(hs[0])}) |")
    L.append("")
    ex = q(con, """SELECT reason, count(*) AS n FROM exclusions WHERE item_key LIKE 'nport_unlisted:%' GROUP BY 1 ORDER BY 1""")
    if ex:
        L.append("Exclusions du scan : " + ", ".join(f"`{r['reason']}` {T.n('exclusions', {'nport_unlisted': r['reason']}, r['n'])}"
                                                   for r in ex) + ". Un nom d'émetteur gardé par le lexique sans commencer par "
                 "une dénomination légale ni être formé d'un terme suivi de mots de catégorie (véhicule nommé d'après un nœud, "
                 "autre forme juridique, nom commercial) est compté en `pending_entity`, jamais rattaché sans extrait (D-0065, "
                 "point 6 ; D-0066, point 3) ; les prêts de plateforme sont comptés en `out_of_scope` (D-0066, point 4).")
        L.append("")
    return L


def unlisted_series(con, T):
    """D-0065 : par nœud, valeur détenue par trimestre, puis chaque fonds et titre de sa première à sa dernière date."""
    marks, held = unlisted_cells(con)
    L = []
    for s in sorted(set(held) | set(marks), key=lambda x: group_label(x)):
        L.append(f"## {group_label(s)} ({s}) : actions valorisées par les fonds (Form N-PORT)")
        L.append("")
        L.append("Valeur que les fonds enregistrés déclarent pour leurs actions du nœud évaluées au niveau 3, au dernier "
                 "rapport de chaque série dans le trimestre civil ; perspective `counterparty`, jamais une valeur du nœud "
                 "(D-0065, point 8).")
        L.append("")
        if held.get(s):
            L.append("| Trimestre | Valeur détenue déclarée | Séries | Positions |")
            L.append("| --- | ---: | ---: | ---: |")
            for h in held[s]:
                L.append(f"| {h['period_end']} | {T.m(h)} | "
                         f"{T.n('measures', {'nport_unlisted_series': [s, h['period_end']]}, h['fl'].get('series'))} | "
                         f"{T.n('measures', {'nport_unlisted_positions': [s, h['period_end']]}, h['fl'].get('positions'))} |")
            L.append("")
        by = defaultdict(list)
        for m in marks.get(s, []):
            by[(m["counterparty"], m["breakdown_key"])].append(m)
        if by:
            L.append("| Fonds (série) | Titre | Première date (valeur par action) | Dernière date (valeur par action) | Dates |")
            L.append("| --- | --- | --- | --- | ---: |")
            for (cp, bk), rs in sorted(by.items(), key=lambda kv: ((kv[1][-1]["fl"].get("series_name") or kv[0][0]), kv[0])):
                f0, f1 = rs[0], rs[-1]
                L.append(f"| {f1['fl'].get('series_name') or f1['fl'].get('registrant_name') or cp} | "
                         f"{f1['fl'].get('title') or bk.split('|', 1)[-1]} ({bk.split('|', 1)[0]}) | {f0['period_end']} ({per_share(T, f0)}) | "
                         f"{f1['period_end']} ({per_share(T, f1)}) | {T.n('measures', {'nport_unlisted_dates': [s, cp, bk]}, len(rs))} |")
            L.append("")
    return L


def credit_cells(con):
    """Cellules nport_credit_mark (D-0066), par nœud et par catégorie et monnaie, dans l'ordre des dates."""
    by = defaultdict(list)
    for r in q(con, """SELECT * FROM measures WHERE measure = 'nport_credit_mark' AND view = 'as_known'
                       ORDER BY subject, breakdown_key, period_end"""):
        r["fl"] = json.loads(r["flags"]) if r["flags"] else {}
        by[(r["subject"], r["breakdown_key"])].append(r)
    return by


CREDIT_CAT = {"LON": "prêts", "DBT": "titres de dette"}


def credit_cat(bk):
    cat, cur = (bk.split("|", 1) + [""])[:2]
    return f"{CREDIT_CAT.get(cat, cat)} ({cur})"


def credit_flags(T, r):
    """Parts du nominal déclarées en défaut, en arriéré d'intérêts ou en intérêts capitalisés (Item C.9), si non nulles."""
    out = []
    for k, lab in (("default_share", "défaut"), ("arrears_share", "arriéré"), ("pik_share", "PIK")):
        v = r["fl"].get(k)
        if v not in (None, "") and Decimal(str(v)) > 0:
            out.append(T.n("measures", {"nport_credit_share": [r["subject"], r["breakdown_key"], r["period_end"], k]}, v,
                           text=f"{lab} {fr_num(Decimal(str(v)) * 100, 1)} %"))
    return ", ".join(out) or "—"


def credit_section(con, T):
    """D-0066, point 4 : prêts et titres de dette des nœuds évalués par les fonds (Form N-PORT), valeur ÷ nominal."""
    by = credit_cells(con)
    if not by:
        return []
    last_date = max(r["period_end"] for rs in by.values() for r in rs)
    recent = (dt.date.fromisoformat(last_date) - dt.timedelta(days=92)).isoformat()
    L = ["## Prêts et dette des nœuds valorisés par les fonds (Form N-PORT)", ""]
    L.append("Valeur que les fonds enregistrés déclarent pour les prêts (LON) et les titres de dette (DBT) d'un nœud du modèle "
             "qu'ils évaluent eux-mêmes (niveau 3), rapportée au nominal, dans la monnaie du titre, au dernier dépôt de chaque "
             "série pour la date de portefeuille (Form N-PORT Data Sets ; D-0066, point 4). Une cellule par nœud, catégorie, "
             "monnaie et date : elle mêle les tranches et les rangs que les fonds détiennent, dont les intitulés et les "
             "échéances sont dans `series.md`. C'est une marque déclarée par des tiers (perspective `counterparty`), jamais une "
             "probabilité de défaut ni un fait comptable de l'emprunteur : elle n'entre dans aucune mesure de financement, ni "
             "dans l'exposition, les paires, les cycles ou l'annexe F. Les parts en défaut, en arriéré d'intérêts ou en intérêts "
             "capitalisés (PIK) sont celles du nominal que les fonds déclarent ainsi (Item C.9).")
    L.append("")
    n = sum(len(v) for v in by.values())
    L.append(f"Cellules : {T.n('measures', {'measure': 'nport_credit_mark'}, n)}, sur "
             f"{T.n('measures', {'measure': 'nport_credit_mark', 'nodes': True}, len({s for s, _ in by}))} nœuds, du "
             f"{min(r['period_end'] for rs in by.values() for r in rs)} au {last_date}.")
    L.append("")
    L.append(f"Nœuds dont au moins un fonds déclare un prêt ou un titre de dette dans les trois mois qui précèdent la dernière "
             f"date de portefeuille ({last_date}), par valeur déclarée en dollars à leur dernière date :")
    L.append("")
    L.append("| Nœud | Catégorie | Dernière date | Valeur ÷ nominal | Nominal détenu | Séries | Défaut, arriéré, PIK | "
             "Plus bas (date) | Première date (valeur ÷ nominal) |")
    L.append("| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |")
    rows, gone = [], 0
    for (s, bk), rs in by.items():
        if rs[-1]["period_end"] < recent:
            gone += 1
            continue
        rows.append((s, bk, rs))
    rows.sort(key=lambda x: (-Decimal(str(x[2][-1]["fl"].get("value_usd") or 0)), x[0], x[1]))
    for s, bk, rs in rows:
        last = rs[-1]
        vals = [r for r in rs if r["value"] is not None]
        lo = min(vals, key=lambda r: (Decimal(str(r["value"])), r["period_end"])) if vals else None
        cur = bk.split("|", 1)[-1]
        L.append(f"| {group_label(s)} | {credit_cat(bk)} | {last['period_end']} | {T.m(last, fmt='pct')} | "
                 f"{T.m(last, 'denominator', fmt='mn')} {cur} | "
                 f"{T.n('measures', {'nport_credit_series': [s, bk, last['period_end']]}, last['fl'].get('series'))} | "
                 f"{credit_flags(T, last)} | " + (f"{T.m(lo, fmt='pct')} ({lo['period_end']})" if lo else "—") +
                 f" | {rs[0]['period_end']} ({T.m(rs[0], fmt='pct')}) |")
    L.append("")
    L.append(f"Nœuds et catégories sans position déclarée dans ces trois mois : "
             f"{T.n('measures', {'measure': 'nport_credit_mark', 'without_recent_position': True}, gone)}.")
    L.append("")
    ex = q(con, """SELECT count(*) AS n FROM exclusions WHERE item_key LIKE 'nport_unlisted:platform:%'""")
    if ex and ex[0]["n"]:
        L.append(f"Prêts de plateforme écartés et comptés, par émetteur déclaré : "
                 f"{T.n('exclusions', {'nport_credit_platforms': True}, ex[0]['n'])} (`out_of_scope`) ; le fonds y nomme la "
                 "plateforme qui les a consentis, non l'emprunteur, et leurs débiteurs ne sont jamais lus (D-0066, point 4).")
        L.append("")
    return L


def credit_series(con, T):
    """D-0066 : par nœud et par catégorie et monnaie, chaque date de portefeuille avec ses caractéristiques déclarées."""
    by = credit_cells(con)
    L = []
    nodes = defaultdict(list)
    for (s, bk), rs in by.items():
        nodes[s].append((bk, rs))
    for s in sorted(nodes, key=lambda x: (group_label(x), x)):
        L.append(f"## {group_label(s)} ({s}) : prêts et dette valorisés par les fonds (Form N-PORT)")
        L.append("")
        L.append("Valeur déclarée ÷ nominal, dans la monnaie du titre, des positions évaluées au niveau 3, au dernier dépôt de "
                 "chaque série pour la date de portefeuille ; échéances et coupons extrêmes tels que déclarés (un coupon se "
                 "déclare en taux annuel, en fraction ou en pourcentage selon le fonds). Perspective `counterparty` : jamais une "
                 "probabilité de défaut ni un fait comptable de l'emprunteur (D-0066, point 4).")
        L.append("")
        for bk, rs in sorted(nodes[s]):
            L.append(f"**{credit_cat(bk)}**")
            L.append("")
            L.append("| Date | Valeur ÷ nominal | Nominal | Séries | Positions | Titres | Échéances | Coupons | "
                     "Défaut, arriéré, PIK | Intitulé le plus fréquent |")
            L.append("| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |")
            cur = bk.split("|", 1)[-1]
            for r in rs:
                fl = r["fl"]
                mt, cp = fl.get("maturity"), fl.get("coupon")
                tt = (fl.get("top_titles") or [[None]])[0][0]
                L.append(f"| {r['period_end']} | {T.m(r, fmt='pct')} | {T.m(r, 'denominator', fmt='mn')} {cur} | "
                         f"{T.n('measures', {'nport_credit_series': [s, bk, r['period_end']]}, fl.get('series'))} | "
                         f"{T.n('measures', {'nport_credit_positions': [s, bk, r['period_end']]}, fl.get('positions'))} | "
                         f"{T.n('measures', {'nport_credit_titles': [s, bk, r['period_end']]}, fl.get('titles'))} | "
                         + (f"{mt[0]} – {mt[1]}" if mt and mt[0] != mt[1] else (mt[0] if mt else "n.d.")) + " | "
                         + (f"{cp[0].replace('.', ',')} – {cp[1].replace('.', ',')}" if cp and cp[0] != cp[1]
                            else (cp[0].replace('.', ',') if cp else "n.d.")) +
                         f" | {credit_flags(T, r)} | {(tt or '—').replace('|', '/')} |")
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
        held = inv[inv["held"]] if "held" in inv.columns else inv.iloc[0:0]
        if len(held):
            L.append("")
            L.append(f"Entrés depuis dans une paire ou un cycle, {T.n('observations', {'foreign_held': True}, len(held))} "
                     "émetteurs (" + ", ".join(sorted(held["filer"].fillna(held["cik"]))) + ") n'ont dans la file que des "
                     "unités antérieures à l'as_of précédent : elles gardent leur état, « non traitées » (D-0074, point 3).")
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
        # une unité 6-K narrative n'a pas de cadre comptable (D-0042, D-0048) : clé vide en dernier
        for (g, f, w), (n, e) in sorted(agg.items(), key=lambda kv: tuple(x or "" for x in kv[0])):
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


# --- D-0060 : OpenAI et Anthropic vus par les déposants ---------------------------------------------------------

LAB_LABEL = {"LAB:OPENAI": "OpenAI", "LAB:ANTHROPIC": "Anthropic"}
LAB_DIR_FR = {"to_lab": "partenaire → laboratoire", "from_lab": "laboratoire → partenaire"}
LAB_EDGE_FR = {"equity_primary": "fonds propres", "convertible_or_safe": "obligations convertibles", "loan_or_facility": "prêt ou facilité",
               "vendor_credit": "crédit fournisseur", "noncash_investment": "apport en nature", "lease_financing": "location-financement",
               "guarantee": "garantie", "backstop": "garantie de bonne fin", "residual_value_guarantee": "garantie de valeur résiduelle",
               "credit_enhancement": "rehaussement de crédit", "revenue_recognized": "revenu comptabilisé", "purchase": "achat",
               "purchase_commitment": "engagement d'achat", "capacity_lease": "bail de capacité", "prepayment": "paiement d'avance",
               "equity_or_warrants_to_customer": "titres ou bons remis au client", "credits_to_customer": "crédits au client",
               "cash_incentive_to_customer": "incitation en numéraire"}
LAB_NAT_FR = {"financing_cash": "versement", "investment_carrying_amount": "valeur au bilan", "fair_value": "juste valeur",
              "commitment_unexecuted": "engagement non exécuté", "capacity_commitment": "engagement de capacité",
              "consideration_payable_to_customer": "contrepartie payable au client", "revenue_recognized_gross": "revenu (brut)",
              "revenue_recognized_net": "revenu (net)", "guarantee_amount": "montant garanti", "lease_payment": "loyers",
              "prepayment": "avance", "fee": "redevance", "other": "autre", "none": "sans nature"}
LAB_BASIS_FR = {"fair_value": "juste valeur", "carrying_amount": "valeur au bilan", "cost": "coût", "equity_method": "mise en équivalence",
                "undiscounted": "non actualisé", "discounted": "actualisé", "commitment_cap": "plafond", "outstanding_balance": "encours",
                "maximum_exposure": "exposition maximale"}
LAB_QUAL_FR = {"at_most": "au plus ", "approximately": "environ ", "up_to": "jusqu'à ", "more_than": "plus de ", "at_least": "au moins "}
LAB_EVENT_FR = {"funding": "versement", "recognition": "comptabilisation", "measurement_change": "variation de valeur",
                "observable_price_adjustment": "réévaluation sur prix observables", "conversion": "conversion", "commitment": "engagement",
                "signing": "signature", "amendment": "avenant", "repayment": "remboursement", "payment": "paiement",
                "impairment": "dépréciation", "termination": "résiliation"}
LAB_STAGE_FR = {"signed": "signé", "drawn_or_paid": "versé ou tiré", "recognized": "comptabilisé", "settled": "réglé",
                "intent_non_binding": "intention sans engagement", "announced": "annoncé"}


def duration_fr(v):
    m = re.fullmatch(r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?", (v or "").strip())
    if not m or not any(m.groups()):
        return v
    y, mo, d = m.groups()
    return " ".join(x for x in ((f"{y} ans" if y else ""), (f"{mo} mois" if mo else ""), (f"{d} jours" if d else "")) if x)


def lab_value(T, c):
    """Valeur d'une cellule du bloc labs dans son unité ; une durée balisée s'affiche en clair, jamais convertie."""
    if c["value"] is None and c.get("value_text"):
        key = {k: c[k] for k in ("measure", "subject", "counterparty", "period_start", "period_end", "view", "as_of", "term",
                                 "breakdown_key", "financing_policy", "constant_perimeter", "variant")}
        return T._reg("measure", key, "value_text", c["value_text"], duration_fr(c["value_text"]))
    u = c.get("unit") or ""
    concept = (c.get("breakdown_key") or "").split("|")[0].split(":")[-1]
    v = Decimal(str(c["value"])) if c["value"] is not None else None
    dec = 0 if v is None or v == v.to_integral_value() else 2
    if u == "USD" and "NumberOf" in concept:          # nombre balisé en dollars par le déposant
        return T.m(c, fmt="n", dec=dec) + " (unité balisée : USD)"
    if u == "USD":
        return T.m(c)
    if u == "pure":
        return T.m(c, fmt="pct", dec=1)
    txt = T.m(c, fmt="n", dec=dec)
    if u in ("item", "items", "segment"):
        return txt
    if u == "shares":
        return txt + " actions"
    if u in ("MWh", "megawatt"):
        return txt + f" MW (unité balisée : {u})"
    return txt + (f" {u}" if u else "")


def lab_period(c):
    ps, pe = c["period_start"], c["period_end"]
    return f"{ps} → {pe}" if ps not in (None, NONE) else f"au {pe}"


def lab_member(fl):
    lb = [x.strip() for x in (fl.get("member_label") or "").split("|") if x.strip() and not x.strip().endswith("[Member]")]
    lb = [x for x in lb if not x.startswith(("Represents", "It Represent"))] or lb
    return min(lb, key=len) if lb else str(fl.get("member") or "").split(":")[-1]


def lab_subject_label(s, fl):
    if s.startswith("cik:"):
        return f"{fl.get('filer_name') or s} ({s}, hors du graphe)"
    return group_label(s)


def labs_tagged_cells(con):
    out = []
    for r in q(con, """SELECT * FROM measures WHERE measure = 'lab_tagged_value' AND view = 'as_known'
                       ORDER BY counterparty, subject, breakdown_key, period_end, period_start"""):
        r["fl"] = json.loads(r["flags"]) if r["flags"] else {}
        out.append(r)
    return out


def labs_tagged_section(con, T):
    """Volet 3 de D-0060 : faits balisés dont un membre nomme un laboratoire, au dernier fait de chaque série."""
    rows = labs_tagged_cells(con)
    if not rows:
        return []
    L = ["## OpenAI et Anthropic vus par les déposants : faits balisés (D-0060, volet 3)", ""]
    L.append("Faits des instances XBRL des groupes et des extraits des Notes Data Sets déjà en cache dont un membre de dimension "
             "nomme un laboratoire (`lab_tagged_value`). Valeur et unité telles que balisées, du point de vue du déposant "
             "(actionnaire, fournisseur, bailleur, prêteur) : jamais un fait comptable du laboratoire, jamais une valorisation, "
             "aucun ratio. Un trimestre sans fait balisé n'est pas un zéro. Un déposant hors du graphe n'entre dans aucune paire "
             "ni aucun agrégat. Une ligne par série (fait et membres), au dernier fait connu ; la série complète est dans "
             "`series.md`.")
    L.append("")
    cnt = Counter(r["counterparty"] for r in rows)
    subj = Counter((r["counterparty"], r["subject"]) for r in rows)
    L.append("Cellules : " + ", ".join(
        f"{LAB_LABEL.get(l, l)} {T.n('measures', {'measure': 'lab_tagged_value', 'counterparty': l}, n)} "
        f"({T.n('measures', {'measure': 'lab_tagged_value', 'counterparty': l, 'filers': True}, len([1 for (a, _) in subj if a == l]))} déposants)"
        for l, n in sorted(cnt.items())) + ".")
    L.append("")
    for lab in sorted(cnt):
        L.append(f"### {LAB_LABEL.get(lab, lab)}")
        L.append("")
        by = defaultdict(lambda: defaultdict(list))
        for r in rows:
            if r["counterparty"] == lab:
                by[r["subject"]][r["breakdown_key"]].append(r)
        for s in sorted(by, key=lambda x: (x.startswith("cik:"), lab_subject_label(x, {}))):
            series = by[s]
            allr = [r for rs in series.values() for r in rs]
            L.append(f"**{lab_subject_label(s, allr[0]['fl'])}** : {T.n('measures', {'lab_tagged_value': [s, lab]}, len(allr))} "
                     f"{plural(len(allr), 'fait')} balisé{'s' if len(allr) > 1 else ''}, du "
                     f"{min(r['period_end'] for r in allr)} au {max(r['period_end'] for r in allr)}.")
            L.append("")
            L.append("| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |")
            L.append("| --- | --- | --- | ---: | --- | ---: |")
            for bk, rs in sorted(series.items(), key=lambda kv: kv[0]):
                last = max(rs, key=lambda r: (r["period_end"], r["period_start"] or "", r["knowledge_date"] or ""))
                fl = last["fl"]
                concept = bk.split("|")[0].split(":")[-1]
                extra = ""
                if fl.get("conflict"):
                    extra = f" (conflit : le texte lu nomme {', '.join(fl['conflict'])} pour ce montant)"
                L.append(f"| `{concept}` | {lab_member(fl)} | {lab_period(last)} | {lab_value(T, last)}{extra} | "
                         f"{fl.get('form')} {fl.get('accession')} | {T.n('measures', {'lab_tagged_series': [s, lab, bk]}, len(rs))} |")
            L.append("")
    return L


def labs_tagged_series(con, T):
    rows = labs_tagged_cells(con)
    if not rows:
        return []
    L = ["## OpenAI et Anthropic : faits balisés par les déposants (D-0060, volet 3)", ""]
    L.append("Série complète de `lab_tagged_value`, vue `as_known`, par laboratoire et par déposant. Point de vue du déposant, "
             "jamais une valorisation du laboratoire ; un trimestre absent n'est pas un zéro.")
    L.append("")
    for lab in sorted({r["counterparty"] for r in rows}):
        for s in sorted({r["subject"] for r in rows if r["counterparty"] == lab}, key=lambda x: (x.startswith("cik:"), x)):
            rs = [r for r in rows if r["counterparty"] == lab and r["subject"] == s]
            L.append(f"**{LAB_LABEL.get(lab, lab)} — {lab_subject_label(s, rs[0]['fl'])}**")
            L.append("")
            L.append("| Fait balisé | Membre | Période | Valeur | Pièce |")
            L.append("| --- | --- | --- | ---: | --- |")
            for r in sorted(rs, key=lambda r: (r["breakdown_key"], r["period_end"], r["period_start"] or "")):
                L.append(f"| `{r['breakdown_key'].split('|')[0].split(':')[-1]}` | {lab_member(r['fl'])} | {lab_period(r)} | "
                         f"{lab_value(T, r)} | {r['fl'].get('form')} {r['fl'].get('accession')} |")
            L.append("")
    return L


def labs_ledger_section(con, T):
    """Volet 4 de D-0060 : grand livre par laboratoire, au dernier montant connu de chaque instrument, sans total."""
    cells = q(con, "SELECT * FROM measures WHERE measure = 'lab_ledger' AND view = 'as_known' ORDER BY counterparty, subject, breakdown_key")
    if not cells:
        return []
    edges = q(con, """SELECT l.*, o.accession, o.form FROM links l LEFT JOIN observations o
                      ON o.obs_key = json_extract_string(l.evidence_keys, '$[0]')
                      WHERE l.link_kind = 'edge' AND coalesce(l.elimination_status, '') <> 'eliminated'
                        AND ((l.from_group LIKE 'LAB:%' AND l.to_group NOT LIKE 'LAB:%') OR (l.to_group LIKE 'LAB:%' AND l.from_group NOT LIKE 'LAB:%'))
                      ORDER BY l.link_key""")
    tagged = labs_tagged_cells(con)
    L = ["## Grand livre des laboratoires (D-0060, volet 4)", ""]
    L.append("Pour chaque laboratoire et chaque groupe qui a une arête avec lui : les instruments qui les lient, dans le sens des "
             "ressources (§3.1), au dernier montant admissible connu (`lab_ledger`), avec sa pièce. Un flux est le dernier flux "
             "publié, jamais une somme ; aucun total, ni par partenaire, ni par sens. Les états de la paire (au coût, au bilan, à "
             "la juste valeur, plafonds d'engagement) viennent de `counterparty_exposure` et ne nettent pas les engagements déjà "
             "versés. Les capacités balisées (MW, GW) restent à part, jamais additionnées aux dollars. Chaque montant est vu par "
             "le déposant de sa pièce : le grand livre ne dit rien des comptes des laboratoires.")
    L.append("")
    by_pair = defaultdict(list)
    for c in cells:
        c["fl"] = json.loads(c["flags"]) if c["flags"] else {}
        by_pair[(c["counterparty"], c["subject"])].append(c)
    e_pair = defaultdict(list)
    for e in edges:
        lab, partner = (e["to_group"], e["from_group"]) if str(e["to_group"]).startswith("LAB:") else (e["from_group"], e["to_group"])
        if partner is None or lab is None:
            continue
        e_pair[(lab, partner)].append(e)
    for lab in sorted({k[0] for k in e_pair}):
        partners = sorted({p for (l, p) in e_pair if l == lab}, key=lambda p: (-len(e_pair[(lab, p)]), group_label(p)))
        L.append(f"### {LAB_LABEL.get(lab, lab)}")
        L.append("")
        L.append(f"Partenaires : {T.n('links', {'lab_partners': lab}, len(partners))} ; arêtes : "
                 f"{T.n('links', {'lab_edges': lab}, sum(len(e_pair[(lab, p)]) for p in partners))}.")
        L.append("")
        for p in partners:
            es = e_pair[(lab, p)]
            n_amt = sum(1 for e in es if e["amount"] is not None)
            L.append(f"#### {group_label(p)}")
            L.append("")
            L.append(f"{T.n('links', {'lab_pair_edges': [lab, p]}, len(es))} {plural(len(es), 'arête')}, dont "
                     f"{T.n('links', {'lab_pair_edges_amount': [lab, p]}, n_amt)} à montant.")
            ex = q(con, """SELECT * FROM measures WHERE measure = 'counterparty_exposure' AND view = 'as_known' AND subject = ?
                           AND counterparty = ? AND value IS NOT NULL ORDER BY period_end DESC, breakdown_key""", p, lab)
            if ex:
                pe = ex[0]["period_end"]
                parts = [f"{LAB_EXPO_FR.get(x['breakdown_key'], x['breakdown_key'])} {T.m(x)}" for x in ex if x["period_end"] == pe]
                L.append(f"- Exposition du partenaire au {pe} (`counterparty_exposure`) : " + " ; ".join(parts) + ".")
            caps = [t for t in tagged if t["subject"] == p and t["counterparty"] == lab and (t["unit"] or "") in ("MW", "GW", "MWh", "megawatt", "gigawatt")]
            if caps:
                L.append("- Capacités balisées (jamais additionnées) : " + " ; ".join(
                    f"{lab_value(T, t)}, `{t['breakdown_key'].split('|')[0].split(':')[-1]}` ({lab_period(t)})" for t in caps) + ".")
            pc = by_pair.get((lab, p)) or []
            if pc:
                L.append("")
                L.append("| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |")
                L.append("| --- | --- | --- | --- | ---: | --- | --- | ---: |")
                for c in sorted(pc, key=lambda c: (c["fl"].get("direction"), c["fl"].get("family"), c["breakdown_key"])):
                    fl = c["fl"]
                    src = q(con, """SELECT o.amount_qualifier, o.event_type, o.period_label FROM links l JOIN observations o
                                     ON o.obs_key = json_extract_string(l.evidence_keys, '$[0]') WHERE l.link_key = ?""",
                            fl.get("link_key"))
                    qual, evt, plab = ((src[0]["amount_qualifier"], src[0]["event_type"], src[0]["period_label"])
                                       if src else (None, None, None))
                    nat = LAB_NAT_FR.get(fl.get("amount_nature"), fl.get("amount_nature"))
                    basis = LAB_BASIS_FR.get(fl.get("measurement_basis"), fl.get("measurement_basis"))
                    if basis not in (None, NONE) and basis not in nat:
                        nat += f", {basis}"
                    if fl.get("amount_nature") == "other" and LAB_EVENT_FR.get(evt):
                        nat += f" ({LAB_EVENT_FR[evt]})"
                    val = LAB_QUAL_FR.get(qual, "") + lab_value(T, c) + (f" ({plab})" if plab else "")
                    ik = fl.get("instrument_key") or "arête sans clé d'instrument"
                    L.append(f"| {LAB_DIR_FR.get(fl.get('direction'), fl.get('direction'))} | {ik} | "
                             f"{LAB_EDGE_FR.get(fl.get('edge_type'), fl.get('edge_type'))} | {nat} | {val} | {c['period_end']} | "
                             f"{fl.get('form')} {fl.get('accession')} | {T.n('links', {'lab_ledger_amounts': c['breakdown_key'], 'pair': [lab, p]}, fl.get('n_amounts'))} |")
            with_cell = {c["fl"].get("instrument_key") for c in pc}
            rel = defaultdict(list)
            for e in es:
                if e["amount"] is None and (e["instrument_key"] or None) not in with_cell:
                    rel[e["instrument_key"] or "arête sans clé d'instrument"].append(e)
            if rel:
                L.append("")
                L.append("Sans montant admissible : " + " ; ".join(
                    f"{ik} ({LAB_EDGE_FR.get(v[-1]['edge_type'], v[-1]['edge_type'])}, {LAB_STAGE_FR.get(v[-1]['stage'], v[-1]['stage'])}, "
                    f"{v[-1]['form'] or '?'} {v[-1]['accession'] or '?'})" for ik, v in sorted(rel.items(), key=lambda kv: str(kv[0]))) + ".")
            L.append("")
    return L


# D-0067 : clauses des contrats, capacités et événements propres aux laboratoires
CLAUSE_FR = {"vesting_tranche": "tranche d'acquisition", "term": "durée", "maturity": "échéance",
             "termination_right": "clause de sortie", "exclusivity": "exclusivité", "minimum_commitment": "engagement minimal",
             "delivery_schedule": "calendrier de livraison"}
CAPKIND_FR = {"compute": "calcul", "hosting": "hébergement", "power": "électricité", "unspecified": "non précisé"}
COND_FR = {"conditional": "sous condition", "optional": "au choix d'une partie", "firm": "ferme"}
LAB_EVENT_ID_FR = {"L1": "engagement réduit", "L2": "fin d'une exclusivité", "L3": "marque en baisse chez un actionnaire",
                   "L4": "garantie appelée", "L5": "site retardé"}
LAB_NAMES = (("LAB:OPENAI", "OpenAI"), ("LAB:ANTHROPIC", "Anthropic"))


def _cell_rows(con, measure):
    rows = q(con, f"SELECT * FROM measures WHERE measure = '{measure}' AND view = 'as_known' "
                  "ORDER BY counterparty, subject, breakdown_key, period_end")
    for r in rows:
        r["fl"] = json.loads(r["flags"]) if r["flags"] else {}
    return rows


def _clean(x, n=None):
    s = re.sub(r"\s+", " ", str(x or "")).strip().replace("|", "/")
    return (s[:n - 1] + "…") if n and len(s) > n else s


def lab_quantity(T, c):
    """Quantité écrite d'une clause ou d'une capacité, dans son unité, jamais convertie."""
    if c["value"] is None:
        return "—"
    v = Decimal(str(c["value"]))
    dec = 0 if v == v.to_integral_value() else 2
    u = c.get("unit") or ""
    if u == "USD":
        return T.m(c)
    if u == "pure":                     # part écrite (« 40 % of the Warrant Shares »)
        return T.m(c, fmt="pct", dec=0 if (v * 100) == (v * 100).to_integral_value() else 1)
    txt = T.m(c, fmt="n", dec=dec)
    return txt + (" actions" if u == "shares" else f" {u}" if u else "")


def lab_when(c):
    """Date d'une clause ou d'une capacité telle qu'écrite : la date retenue et sa base, le délai écrit."""
    fl = c["fl"]
    base = {"event": "", "period": " (fin de période)", "knowledge": " (date de la pièce)"}.get(fl.get("date_basis"), "")
    span = f"{c['period_start']} → {c['period_end']}" if c["period_start"] not in (None, NONE) else str(c["period_end"])
    return span + base + (f" ; « {_clean(fl['period_label'], 80)} »" if fl.get("period_label") else "")


def lab_piece(fl):
    ex = fl.get("exhibit_type") if fl.get("exhibit_type") not in (None, fl.get("form")) else None
    return f"{fl.get('form') or '?'}{' ' + ex if ex else ''} {fl.get('accession') or '?'}"


def lab_declarant(r):
    """Déclarant d'une cellule de D-0067 ; un déposant hors des groupes, sans entité au registre, prend le nom que porte
    son dépôt (drapeau `filer_name`), jamais la clé normalisée de son groupe."""
    s = r["subject"]
    if s.startswith("CP:") and s not in CP_NAMES and r["fl"].get("filer_name"):
        return r["fl"]["filer_name"]
    return group_label(s)


def visible_dec(a, b, dec=2, most=6):
    """Décimales qu'il faut pour que deux valeurs arrondies diffèrent, de `dec` à `most` (30,0045 puis 30,0000)."""
    a, b = Decimal(str(a)), Decimal(str(b))
    while dec < most and round(a, dec) == round(b, dec):
        dec += 1
    return dec


def lab_mark_facts(con, T, marks):
    """Baisses de marque d'une cellule L3, de la plus forte à la plus faible en part de la valeur précédente, chacune
    avec autant de décimales qu'il en faut pour que la baisse se voie, et ses pièces."""
    out = []
    for m in marks:
        sel = """SELECT * FROM measures WHERE measure = 'nport_equity_mark' AND view = 'as_known' AND subject = ?
                 AND counterparty = ? AND breakdown_key = ? AND period_end = ?"""
        cur, prv = q(con, sel, m["lab"], m["fund"], m["title"], m["date"]), q(con, sel, m["lab"], m["fund"], m["title"], m["previous_date"])
        if not (cur and prv):
            continue
        a, b = Decimal(str(prv[0]["value"])), Decimal(str(cur[0]["value"]))
        dec = visible_dec(a, b)
        title = m["title"].split("TITLE:", 1)[-1]
        text = (f"{m['fund']}, « {title} » : {T.m(prv[0], fmt='n', dec=dec)} au {m['previous_date']}, "
                f"{T.m(cur[0], fmt='n', dec=dec)} au {m['date']} (valeur par action, USD)")
        acc = (json.loads(cur[0]["flags"]) if cur[0]["flags"] else {}).get("accessions") or []
        out.append(((b - a) / a if a else Decimal(0), text, acc))
    return [(t, acc) for _, t, acc in sorted(out, key=lambda x: (x[0], x[1]))]


def lab_clauses_section(con, T):
    """D-0067, volet 8 : clauses des contrats qui concernent un laboratoire, une ligne par clause, sans total."""
    rows = _cell_rows(con, "lab_contract_clause")
    if not rows:
        return []
    L = ["## Contrats des laboratoires : tranches, échéances, sorties (D-0067, volet 8)", ""]
    L.append("Clauses lues dans les pièces contractuelles déposées (EX-10, EX-4, EX-2) et dans les résumés des déposants, "
             "telles qu'écrites : tranches d'acquisition, durées et échéances, clauses de sortie, exclusivités, engagements "
             "minimaux et calendriers de livraison (`lab_contract_clause`). Une clause caviardée le reste ; une quantité est "
             "celle du texte, jamais un total. Le déclarant est le déposant de la pièce.")
    L.append("")
    for lab, name in LAB_NAMES:
        rs = [r for r in rows if r["counterparty"] == lab]
        if not rs:
            continue
        L.append(f"### {name}")
        L.append("")
        L.append(f"Clauses : {T.n('measures', {'measure': 'lab_contract_clause', 'counterparty': lab}, len(rs))}, de "
                 f"{T.n('measures', {'measure': 'lab_contract_clause', 'counterparty': lab, 'instruments': True}, len({(r['subject'], r['fl'].get('instrument_key') or r['breakdown_key']) for r in rs}))} contrats ou instruments.")
        L.append("")
        L.append("| Déclarant | Contrat | Clause | Date | Quantité | Condition | Pièce |")
        L.append("| --- | --- | --- | --- | ---: | --- | --- |")
        for r in sorted(rs, key=lambda r: (lab_declarant(r), r["fl"].get("instrument_key") or "", str(r["period_end"]),
                                           r["breakdown_key"])):
            fl = r["fl"]
            cond = " ; ".join(x for x in (COND_FR.get(fl.get("conditionality")), _clean(fl.get("trigger_description"), 140),
                                          "caviardée" if fl.get("redacted") else None) if x) or "—"
            L.append(f"| {lab_declarant(r)} | {fl.get('instrument_key') or '—'} | "
                     f"{CLAUSE_FR.get(fl.get('clause_kind'), fl.get('clause_kind'))} | {lab_when(r)} | {lab_quantity(T, r)} | "
                     f"{cond} | {lab_piece(fl)} |")
        L.append("")
    return L


def lab_capacity_section(con, T):
    """D-0067, volet 8 : capacités écrites pour chaque laboratoire, calcul face à hébergement et électricité."""
    rows = _cell_rows(con, "lab_capacity")
    if not rows:
        return []
    L = ["## Calendrier des capacités des laboratoires (D-0067, volet 8)", ""]
    L.append("Capacités en MW ou en GW écrites dans les pièces pour un laboratoire nommé (`lab_capacity`), telles qu'écrites : "
             "jamais additionnées, ni entre elles, ni aux dollars, jamais converties de MW en GW. Les capacités de calcul "
             "(puces, serveurs, nuage) sont mises face aux capacités d'hébergement (centres de données, charge IT) et "
             "d'électricité que les déclarants disent avoir contractées ; une capacité écrite sans le laboratoire n'y figure pas.")
    L.append("")
    for lab, name in LAB_NAMES:
        rs = [r for r in rows if r["counterparty"] == lab]
        if not rs:
            continue
        L.append(f"### {name}")
        L.append("")
        for title, kinds in (("Calcul", ("compute",)), ("Hébergement, électricité et non précisé", ("hosting", "power", "unspecified"))):
            ks = [r for r in rs if r["fl"].get("capacity_kind") in kinds]
            if not ks:
                continue
            L.append(f"**{title}** : {T.n('measures', {'measure': 'lab_capacity', 'counterparty': lab, 'kinds': list(kinds)}, len(ks))} lignes.")
            L.append("")
            L.append("| Déclarant | Contrepartie écrite | Genre | Capacité | Statut | Calendrier | Pièce |")
            L.append("| --- | --- | --- | ---: | --- | --- | --- |")
            for r in sorted(ks, key=lambda r: (str(r["period_end"]), lab_declarant(r), r["breakdown_key"])):
                fl = r["fl"]
                L.append(f"| {lab_declarant(r)} | {_clean(fl.get('counterparty_name'), 60) or '—'} | "
                         f"{CAPKIND_FR.get(fl.get('capacity_kind'), fl.get('capacity_kind'))} | "
                         f"{LAB_QUAL_FR.get(fl.get('capacity_qualifier'), '')}{lab_quantity(T, r)} | "
                         f"{LAB_STAGE_FR.get(fl.get('stage'), fl.get('stage') or '—')} | {lab_when(r)} | {lab_piece(fl)} |")
            L.append("")
    return L


# D-0068 : carnet attribué par le vendeur à un client nommé
BACKLOG_AT_FR = {"fiscal_year_end": "fin d'exercice, E.3", "quarter_end": "fin de trimestre, hors E.3"}
BACKLOG_SRC_FR = {"tagged_customer_rpo": "RPO balisé par client", "line_remaining": "reste écrit par le vendeur",
                  "line_excluded": "contrat exclu du RPO par le vendeur (zéro)"}
BACKLOG_TERM_FR = {"rpo": "RPO", "lease": "loyers à recevoir"}


def backlog_pieces(con, c):
    """Pièces d'une cellule de D-0068 : formulaire et accession des faits et des lignes qui la font."""
    out = []
    for k in json.loads(c["lineage"]) if c.get("lineage") else []:
        r = (q(con, "SELECT form, accession FROM observations WHERE obs_key = ?", k[4:]) if k.startswith("obs:") else
             q(con, "SELECT form, accession FROM facts WHERE fact_key = ?", k))
        if r:
            out.append(f"{r[0]['form']} {r[0]['accession']}")
    return ", ".join(dict.fromkeys(out)) or "—"


def backlog_value(T, c):
    """Part exacte, ou intervalle [0 ; borne haute] sous l'hypothèse déclarée, ou motif."""
    if c["status"] == "bounded":
        return f"[0 ; {T.m(c, 'value_upper', 'pct')}]" + (" (plafonnée)" if c["fl"].get("capped") else "")
    return T.m(c, fmt="pct")


def backlog_basis(c):
    fl = c["fl"]
    if c["status"] == "computed":
        return BACKLOG_SRC_FR.get(fl.get("source"), fl.get("source") or "—")
    if c["status"] == "bounded":
        return "valeur publiée des contrats ÷ carnet du vendeur (hypothèse déclarée)"
    return fl.get("basis") or ND_FR.get(c["nd_reason"], c["nd_reason"] or "—")


def backlog_section(con, T):
    """D-0068, volet 3 : part du carnet contracté de chaque vendeur que le vendeur attribue à un client nommé, la
    dernière cellule de chaque client, jamais de total."""
    rows = _cell_rows(con, "contracted_backlog_share")
    if not rows:
        return []
    L = ["## Carnet contracté par client (D-0068)", ""]
    L.append("Part du carnet contracté d'un vendeur que le vendeur attribue lui-même à un client nommé, financé ou non "
             "(`contracted_backlog_share`) : sur son RPO (contrats de services, ASC 606) ou sur ses loyers à recevoir de "
             "bailleur (ASC 842), jamais mêlés. La part est exacte quand le vendeur écrit ce que le client lui doit encore, "
             "ou balise son RPO par client ; sinon elle est majorée par la valeur publiée des contrats, plafonnée à 100 %, "
             "sous une hypothèse déclarée : le vendeur publie chacun de ses contrats importants avec ce client (Item 1.01 du "
             "8-K), et la valeur d'un contrat, totale ou maximale, majore ce qu'il en reste. Aucune somme entre clients ni "
             "entre vendeurs, aucune pièce EX-99 ; ces cellules n'entrent ni dans l'annexe E ni dans l'annexe F. Le détail "
             "par date est dans `series.md`.")
    L.append("")
    sellers = sorted({r["subject"] for r in rows}, key=group_label)
    L.append("| Vendeur | RPO, dernière date publiée | Loyers à recevoir, dernière date publiée |")
    L.append("| --- | ---: | ---: |")
    for g in sellers:
        last = {}
        for m in ("rpo_total", "lessor_lease_receipts"):
            r = q(con, f"""SELECT * FROM measures WHERE measure = '{m}' AND subject = ? AND view = 'as_known'
                            AND status = 'computed' ORDER BY period_end DESC LIMIT 1""", g)
            last[m] = f"{T.m(r[0])} au {r[0]['period_end']}" if r else "—"
        L.append(f"| {group_label(g)} | {last['rpo_total']} | {last['lessor_lease_receipts']} |")
    L.append("")
    L.append("| Vendeur | Client | Terme | Date | Part du carnet | Base | Pièces | Cellules |")
    L.append("| --- | --- | --- | --- | ---: | --- | --- | ---: |")
    by = defaultdict(list)
    for r in rows:
        by[(r["subject"], r["counterparty"], r["term"])].append(r)
    for (g, cp, tm), rs in sorted(by.items(), key=lambda kv: (group_label(kv[0][0]), group_label(kv[0][1]), kv[0][2])):
        rs = sorted(rs, key=lambda r: str(r["period_end"]))
        shown = [r for r in rs if r["status"] in ("computed", "bounded")]
        r = (shown or rs)[-1]
        L.append(f"| {group_label(g)} | {group_label(cp)} | {BACKLOG_TERM_FR.get(tm, tm)} | {r['period_end']} | "
                 f"{backlog_value(T, r)} | {_clean(backlog_basis(r), 120)} | {backlog_pieces(con, r)} | "
                 f"{T.n('measures', {'contracted_backlog_share': [g, cp, tm]}, len(rs))} |")
    L.append("")
    # lignes de carnet d'un vendeur sans aucune date où son carnet du même terme est publié : aucune cellule
    seen = {(g, cp, tm) for g, cp, tm in by}
    lone = defaultdict(int)
    for o in q(con, """SELECT o.group_id, o.backlog_basis, m.ref FROM observations o JOIN entities m
                         ON m.entity_id = o.counterparty_entity_id AND m.record_kind = 'membership'
                         WHERE o.backlog_basis IN ('rpo', 'lease') AND o.validation_state = 'valid'
                         AND o.kind = 'observation' AND coalesce(o.tier, '') <> 'E'"""):
        if (o["group_id"], o["ref"], o["backlog_basis"]) not in seen and o["ref"] != o["group_id"]:
            lone[(o["group_id"], o["ref"], o["backlog_basis"])] += 1
    if lone:
        L.append("Lignes de carnet sans aucune date où le carnet du vendeur, du même terme, est publié (aucune cellule) : "
                 + " ; ".join(f"{group_label(g)} → {group_label(cp)}, {BACKLOG_TERM_FR.get(tm, tm)} "
                              f"({T.n('observations', {'backlog_lines_without_cell': [g, cp, tm]}, n)} "
                              f"{plural(n, 'ligne')})" for (g, cp, tm), n in sorted(lone.items())) + ".")
        L.append("")
    un = q(con, """SELECT group_id, counterparty_name, count(*) AS n FROM observations WHERE backlog_basis = 'unspecified'
                    AND validation_state = 'valid' GROUP BY 1, 2 ORDER BY 1, 2""")
    if un:
        L.append("Lignes de carnet sans base écrite (ni RPO ni loyers), hors des deux termes : " + " ; ".join(
            f"{group_label(u['group_id'])} → {_clean(u['counterparty_name'], 60)} "
            f"({T.n('observations', {'backlog_basis': 'unspecified', 'group': u['group_id'], 'client': u['counterparty_name']}, u['n'])})"
            for u in un) + ".")
        L.append("")
    return L


def backlog_series(con, T):
    """D-0068 : carnet contracté par client, toutes les dates, avec les deux termes du rapport."""
    rows = _cell_rows(con, "contracted_backlog_share")
    by = defaultdict(list)
    for r in rows:
        by[(r["subject"], r["counterparty"], r["term"])].append(r)
    L = []
    for (g, cp, tm), rs in sorted(by.items(), key=lambda kv: (group_label(kv[0][0]), group_label(kv[0][1]), kv[0][2])):
        L.append(f"## {group_label(g)} → {group_label(cp)} : carnet contracté, {BACKLOG_TERM_FR.get(tm, tm)} (D-0068)")
        L.append("")
        L.append("| Date | Part du carnet | Numérateur | Carnet du vendeur | Base | Pièces |")
        L.append("| --- | ---: | ---: | ---: | --- | --- |")
        for r in sorted(rs, key=lambda r: str(r["period_end"])):
            num = T.m(r, "numerator") if r.get("numerator") is not None else "—"
            den = T.m(r, "denominator") if r.get("denominator") is not None else "—"
            L.append(f"| {r['period_end']} | {backlog_value(T, r)} | {num} | {den} | {_clean(backlog_basis(r), 120)} | "
                     f"{backlog_pieces(con, r)} |")
        L.append("")
    return L


COMPONENT_FR = {"it_equipment": "matériel informatique", "mining_equipment": "machines de minage",
                "manufacturing_equipment": "outils et machines de production", "facilities": "bâtiments et installations",
                "software": "logiciels", "land": "terrains", "unspecified": "nature non écrite"}
ASSET_STATE_FR = {"not_in_service": "pas encore en service", "under_construction": "en construction",
                  "at_suppliers": "chez les fournisseurs", "in_transit": "en transit", "prepaid": "payé d'avance",
                  "unspecified": "état non écrit"}
COMPONENT_OF_FR = {"construction_in_progress": "en-cours", "ppe_class": "classe du tableau",
                   "property_and_equipment": "immobilisations", "other_assets": "autre poste", "unspecified": "poste non écrit"}
COMPONENT_STATEMENT_FR = {"amount": "montant", "primarily": "surtout", "includes": "comprend"}


def ppe_amount(T, c):
    """Montant d'une cellule de `ppe_component_disclosed`, dans sa devise, jamais converti (D-0076)."""
    if c.get("value") is None:
        return T.m(c) if c.get("status") == "not_determinable" else "—"
    u = c.get("unit") or ""
    return T.m(c) if u == "USD" else T.m(c, fmt="mn") + f" {u}"


def ppe_rows(con, view="as_known"):
    """Cellules de `ppe_component_disclosed` : composantes par groupe, en-cours balisé par (groupe, date)."""
    rows = q(con, """SELECT * FROM measures WHERE measure = 'ppe_component_disclosed' AND view = ?
                     ORDER BY subject, period_end, breakdown_key""", view)
    comp, cip = defaultdict(list), {}
    for r in rows:
        r["fl"] = json.loads(r["flags"]) if r["flags"] else {}
        if r["term"] == "component":
            comp[r["subject"]].append(r)
        else:
            cip[(r["subject"], str(r["period_end"]))] = r
    return comp, cip


def ppe_line(T, r, cip_cell, first):
    parent, comp, state, stmt = r["breakdown_key"].split("|")
    return (f"| {str(r['period_end']) if first else ''} | {ppe_amount(T, cip_cell) if first and cip_cell else ('' if not first else '—')} | "
            f"{COMPONENT_FR.get(comp, comp)} | {ASSET_STATE_FR.get(state, state)} | {COMPONENT_OF_FR.get(parent, parent)} | "
            f"{COMPONENT_STATEMENT_FR.get(stmt, stmt)} | {ppe_amount(T, r) if stmt == 'amount' else '—'} | "
            f"{r['fl'].get('form')} {r['fl'].get('accession')} |")


def ppe_components_section(con, T, stats):
    """D-0076 : composition des en-cours et des actifs pas encore en service, telle que l'écrivent les notes ; la
    dernière date de chaque groupe, jamais divisée ni additionnée."""
    comp, cip = ppe_rows(con)
    st = stats.get("ppe_components")
    if not comp and not st:
        return []
    L = ["## Composition des en-cours, telle qu'écrite (D-0076)", ""]
    L.append("Ce que les notes des rapports périodiques écrivent des en-cours et des actifs pas encore en service : la "
             "composante (matériel informatique, bâtiments…), ce qui la tient hors service (pas encore mise en service, "
             "chez les fournisseurs…), le poste qui la porte et, quand il est écrit, son montant (`ppe_component_disclosed`). "
             "Une composante n'est jamais déduite d'un mot vague (« equipment », « AI infrastructure ») ; un montant écrit "
             "n'est ni additionné ni rapporté à un total. L'en-cours balisé à la même date n'est qu'un repère. Le détail "
             "par date est dans `series.md`.")
    L.append("")
    if comp:
        L.append("| Groupe | Date | En-cours balisé | Composante | État | Poste | Énoncé | Montant écrit | Pièce |")
        L.append("| --- | --- | ---: | --- | --- | --- | --- | ---: | --- |")
        for g in sorted(comp, key=group_label):
            last = max(str(r["period_end"]) for r in comp[g])
            rs = [r for r in comp[g] if str(r["period_end"]) == last]
            for i, r in enumerate(rs):
                L.append(f"| {group_label(g) if i == 0 else ''} " + ppe_line(T, r, cip.get((g, last)), i == 0))
        L.append("")
    if st is not None:
        none_term = [g for g in stats.get("groups") or [] if g not in comp and g not in st]
        bare = [g for g in stats.get("groups") or [] if g not in comp and g in st and not st[g].get("blocks")]
        silent = [g for g in stats.get("groups") or [] if g not in comp and st.get(g, {}).get("blocks")]
        if none_term:
            L.append("Aucun terme d'en-cours ni d'actif pas encore en service dans les notes : "
                     + ", ".join(group_label(g) for g in sorted(none_term, key=group_label)) + ".")
        if bare:
            L.append("En-cours nommé seulement comme ligne nue d'un tableau, déjà balisée : "
                     + ", ".join(group_label(g) for g in sorted(bare, key=group_label)) + ".")
        if silent:
            L.append("Fenêtres lues sans composante écrite : " + " ; ".join(
                f"{group_label(g)} ({T.n('observations', {'ppe_read_blocks': g}, st[g]['read'])} "
                f"{plural(st[g]['read'], 'bloc')} lus sur {T.n('observations', {'ppe_blocks': g}, st[g]['blocks'])})"
                for g in sorted(silent, key=group_label)) + ".")
        L.append("")
    return L


def ppe_components_series(con, T):
    """D-0076 : composition des en-cours telle qu'écrite, toutes les dates, vue `as_known`."""
    comp, cip = ppe_rows(con)
    L = []
    for g in sorted(comp, key=group_label):
        L.append(f"## {group_label(g)} : composition des en-cours, telle qu'écrite (D-0076)")
        L.append("")
        L.append("| Date | En-cours balisé | Composante | État | Poste | Énoncé | Montant écrit | Pièce |")
        L.append("| --- | ---: | --- | --- | --- | --- | ---: | --- |")
        prev = None
        for r in sorted(comp[g], key=lambda r: (str(r["period_end"]), r["breakdown_key"])):
            pe = str(r["period_end"])
            L.append(ppe_line(T, r, cip.get((g, pe)), pe != prev))
            prev = pe
        L.append("")
    return L


def lab_events_section(con, T):
    """D-0067, volet 9 : événements propres aux laboratoires, par trimestre, hors annexe F (liste fermée)."""
    rows = _cell_rows(con, "lab_event")
    if not rows:
        return []
    L = ["## Événements propres aux laboratoires (D-0067, volet 9 ; hors annexe F)", ""]
    L.append("Cinq observables datés, fixés avant toute lecture (D-0067, point 7), par laboratoire et trimestre civil, de "
             "2021 T1 au dernier trimestre clos : L1 engagement réduit, L2 fin d'une exclusivité, L3 marque en baisse chez un "
             "actionnaire (valeur par action déclarée par un fonds, sous celle de sa date précédente pour le même titre, ou "
             "perte de valeur écrite), L4 garantie appelée, L5 site retardé. Ce n'est pas l'annexe F, liste fermée ; aucune "
             "somme, aucun score. L1, L2, L4 et L5 ne voient que les pièces en cache : un trimestre sans fait lu est "
             "« non déterminé », jamais « sans événement ».")
    L.append("")
    L.append("| Laboratoire | Événement | Événement daté | Sans événement | Non déterminé |")
    L.append("| --- | --- | ---: | ---: | ---: |")
    for lab, name in LAB_NAMES:
        for lid, lab_fr in LAB_EVENT_ID_FR.items():
            rs = [r for r in rows if r["subject"] == lab and r["breakdown_key"] == lid]
            n_ev = sum(1 for r in rs if r["value_text"] == "event")
            n_no = sum(1 for r in rs if r["value_text"] == "no_event")
            n_nd = sum(1 for r in rs if r["status"] == "not_determinable")
            k = {"measure": "lab_event", "subject": lab, "breakdown_key": lid}
            L.append(f"| {name} | {lid} {lab_fr} | {T.n('measures', {**k, 'value_text': 'event'}, n_ev)} | "
                     f"{T.n('measures', {**k, 'value_text': 'no_event'}, n_no)} | {T.n('measures', {**k, 'status': 'not_determinable'}, n_nd)} |")
    L.append("")
    ev = [r for r in rows if r["value_text"] == "event"]
    if ev:
        L.append("Trimestres à événement :")
        L.append("")
        L.append("| Laboratoire | Événement | Trimestre | Fait | Pièces |")
        L.append("| --- | --- | --- | --- | --- |")
        for r in sorted(ev, key=lambda r: (r["subject"], r["breakdown_key"], str(r["period_end"]))):
            fl = r["fl"]
            marks = lab_mark_facts(con, T, fl.get("marks") or [])
            facts = [t for t, _ in marks[:3]]       # les trois plus fortes baisses ; toutes dans series.md
            if len(marks) > 3:
                facts.append(f"{T.n('measures', {'lab_event_marks': [r['subject'], r['breakdown_key'], str(r['period_end'])]}, len(marks) - 3)} "
                             f"autres baisses (détail dans `series.md`)")
            for ok in fl.get("observations") or []:
                o = q(con, "SELECT note, accession, form FROM observations WHERE obs_key = ?", ok)
                if o:
                    facts.append(_clean(o[0]["note"], 220))
            accs = list(dict.fromkeys((fl.get("accessions") or []) + [a for _, acc in marks[:3] for a in acc]))
            L.append(f"| {dict(LAB_NAMES).get(r['subject'], r['subject'])} | {r['breakdown_key']} "
                     f"{LAB_EVENT_ID_FR.get(r['breakdown_key'])} | {r['period_start']} → {r['period_end']} | "
                     f"{' ; '.join(facts) or '—'} | {', '.join(accs) or '—'} |")
        L.append("")
    return L


def lab_terms_series(con, T):
    """D-0067 : détail par ligne des clauses et des capacités, avec la note de lecture."""
    L = []
    for measure, title in (("lab_contract_clause", "clauses des contrats"), ("lab_capacity", "capacités écrites")):
        rows = _cell_rows(con, measure)
        for lab, name in LAB_NAMES:
            rs = [r for r in rows if r["counterparty"] == lab]
            if not rs:
                continue
            L.append(f"## {name} : {title} (D-0067, volet 8)")
            L.append("")
            for r in sorted(rs, key=lambda r: (lab_declarant(r), r["fl"].get("instrument_key") or "", str(r["period_end"]))):
                fl = r["fl"]
                kind = (CLAUSE_FR.get(fl.get("clause_kind"), fl.get("clause_kind")) if measure == "lab_contract_clause"
                        else CAPKIND_FR.get(fl.get("capacity_kind"), fl.get("capacity_kind")))
                L.append(f"- {lab_declarant(r)}, {fl.get('instrument_key') or 'sans clé'} — {kind}, {lab_when(r)}, "
                         f"{lab_quantity(T, r)} ({lab_piece(fl)}) : {_clean(fl.get('note'), 400) or '—'}")
            L.append("")
    ev = [r for r in _cell_rows(con, "lab_event") if r["value_text"] == "event" and r["fl"].get("marks")]
    for lab, name in LAB_NAMES:
        rs = sorted((r for r in ev if r["subject"] == lab), key=lambda r: str(r["period_end"]))
        if not rs:
            continue
        L.append(f"## {name} : marques en baisse chez un actionnaire, L3 (D-0067, volet 9)")
        L.append("")
        for r in rs:
            L.append(f"**{r['period_start']} → {r['period_end']}**")
            L.append("")
            for t, acc in lab_mark_facts(con, T, r["fl"]["marks"]):
                L.append(f"- {t} ({', '.join(acc) or 'pièce non notée'})")
            L.append("")
    return L


LAB_EXPO_FR = {"exposed_assets/cost/equity_investment": "au coût (participation)", "exposed_assets/cost/loan_receivable": "au coût (prêt)",
               "exposed_assets/carrying_amount/equity_investment": "au bilan (participation)",
               "exposed_assets/carrying_amount/loan_receivable": "au bilan (prêt)",
               "exposed_assets/fair_value/equity_investment": "à la juste valeur (participation)",
               "exposed_assets/fair_value/loan_receivable": "à la juste valeur (prêt)",
               "contractual_outflows/commitment_cap/uncalled_commitment": "engagements non appelés (plafond)"}


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
                done = [r for r in rows if meas == "documented_backlog_dependency" and r["status"] == "computed"]
                if done:            # D-0068, point 9 : les cellules calculées, avec leur valeur
                    L.append("  - Calculées : " + " ; ".join(
                        f"{r['period_end']} ({BACKLOG_AT_FR.get(json.loads(r['flags'] or '{}').get('date_kind'), '?')}, "
                        f"{'RPO total' if r['term'] == 'total' else 'au-delà de douze mois'}) : {T.m(r, fmt='pct')}, "
                        f"{BACKLOG_SRC_FR.get(json.loads(r['flags'] or '{}').get('source'), '?')}" for r in done) + ".")
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


def stop_rule(con):
    """Règle d'arrêt de §11.4, calculée (D-0069, point 8). Refus durable de la SEC : la dernière requête du
    journal est un refus 403. Échec général des contrôles : sur les contrôles non provisoires
    (`tolerance_basis = declared`) de la vue as_known, plus de la moitié des groupes ont plus de la moitié de
    leurs périodes testées en échec, une période l'étant quand ses mismatch dépassent ses ok."""
    n403, last = 0, None
    for line in open(config.ROOT / "journal.jsonl", encoding="utf-8"):
        o = json.loads(line)
        if o.get("url"):
            n403 += o.get("status") == 403
            last = o
    groups = set(config.load()["groups"])
    per = {}
    for r in q(con, """SELECT subject, period_end, count(*) FILTER (WHERE status = 'mismatch') AS m,
                              count(*) FILTER (WHERE status = 'ok') AS ok FROM controls
                       WHERE view = 'as_known' AND tolerance_basis = 'declared' AND status IN ('ok', 'mismatch')
                       GROUP BY 1, 2"""):
        if r["subject"] in groups:
            t = per.setdefault(r["subject"], [0, 0])
            t[0] += 1
            t[1] += r["m"] > r["ok"]
    failing = sorted(g for g, (n, f) in per.items() if 2 * f > n)
    return {"n403": n403, "refused": bool(last and last.get("status") == 403), "groups": len(per), "failing": failing,
            "general": 2 * len(failing) > len(per), "periods": sum(n for n, _ in per.values()),
            "failing_periods": sum(f for _, f in per.values())}


def stop_text(con, T):
    """(arrêt, phrase sur la SEC, phrase sur les contrôles), nombres en jetons."""
    s = stop_rule(con)
    sec = (f"refus 403 de la SEC au journal : {T.n('journal', {'http_403': True}, s['n403'])}, et la dernière requête "
           + ("est un refus" if s["refused"] else "a abouti"))
    ctl = ("groupes dont plus de la moitié des périodes testées sont en échec (contrôles non provisoires, vue `as_known`, "
           f"`mismatch` plus nombreux que `ok`) : {T.n('controls', {'stop_failing_groups': True}, len(s['failing']))} sur "
           f"{T.n('controls', {'stop_groups': True}, s['groups'])}"
           + (f" ({', '.join(GROUP_NAMES.get(g, g) for g in s['failing'])})" if s["failing"] else "")
           + f" ; périodes en échec : {T.n('controls', {'stop_failing_periods': True}, s['failing_periods'])} sur "
             f"{T.n('controls', {'stop_periods': True}, s['periods'])}")
    return s["refused"] or s["general"], sec, ctl


PREVIOUS = ("measures", "exclusions", "links", "controls", "documents", "observations")


def previous_run(con, stats):
    """Tables de l'exécution précédente, celles du commit que l'assemblage a remplacées (D-0069, point 8),
    en vues prev_<table>, et les décisions de ce commit. Sans commit lisible, les vues sont vides et tout
    est nouveau."""
    prev = stats.get("previous_tables") or {}
    d = config.ROOT / "work" / "tmp" / "previous_tables"
    ok = bool(prev)
    if ok:
        d.mkdir(parents=True, exist_ok=True)
        for t in PREVIOUS:
            r = subprocess.run(["git", "show", f"{prev['commit']}:tables/{t}.parquet"], capture_output=True, cwd=config.ROOT)
            if r.returncode != 0:
                ok = False
                break
            (d / f"{t}.parquet").write_bytes(r.stdout)
    for t in PREVIOUS:
        src = f"'{(d / (t + '.parquet')).as_posix()}'" if ok else f"(SELECT * FROM {t} WHERE false)"
        con.execute(f"CREATE OR REPLACE VIEW prev_{t} AS SELECT * FROM {src}")
    dec = set()
    if ok:
        r = subprocess.run(["git", "show", f"{prev['commit']}:decisions.md"], capture_output=True, text=True, cwd=config.ROOT)
        dec = set(re.findall(r"^- \*\*(D-\d{4}) — ", r.stdout, re.M))
    return dict(prev, decisions=dec) if ok else None


def _same_run(cols, a_run, b_run, a="c", b="p"):
    """Rapprochement d'une exécution à l'autre (D-0074) : l'as_of de chaque exécution (`a_run` pour `a`, `b_run` pour
    `b`), et une fin de période qui lui est égale (fenêtre jusqu'à la date de coupure), se lisent comme un seul « run » ;
    les autres as_of, millésimes datés de la vue `as_known`, restent dans la clé tels quels."""
    def col(t, k, run):
        return f"(CASE WHEN {t}.{k} = '{run}' THEN 'run' ELSE {t}.{k} END)" if k in ("as_of", "period_end") else f"{t}.{k}"
    return " AND ".join(f"{col(a, k, a_run)} IS NOT DISTINCT FROM {col(b, k, b_run)}" for k in cols)


def decisions_list():
    out = []
    for line in (config.ROOT / "decisions.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"- \*\*(D-\d{4}) — (.+?)\*\*", line)
        if m:
            out.append((m.group(1), m.group(2).rstrip(".")))
    return out


def delta(con, as_of, stats):
    T = Tokens(con, "delta.md")
    P = previous_run(con, stats)
    # as_of de l'exécution précédente : celui de ses contrôles, tous à la date de coupure (D-0074)
    pr = q(con, "SELECT as_of FROM prev_controls GROUP BY 1 ORDER BY count(*) DESC LIMIT 1")
    prev_as_of = pr[0]["as_of"] if pr else as_of
    since = (f"comparée à l'exécution précédente, dont les tables sont celles du commit {P['commit'][:12]} ({P['date'][:10]})"
             if P else "sans exécution précédente lisible : tout y est nouveau")
    L = ["# delta.md — à lire en premier", "", f"*Exécution du {as_of}, {since}. Généré depuis les tables (D-0069, point 8).*", ""]
    L.append("## Arrêt")
    L.append("")
    stopped, sec, ctl = stop_text(con, T)
    L.append(("Arrêt (§11.4) : " if stopped else "Aucun arrêt (§11.4) : ") + sec + " ; " + ctl + ".")
    L.append("")
    L.append("## Événements nouveaux de l'annexe F")
    L.append("")
    ev_key = ("subject", "period_start", "period_end", "view", "breakdown_key")

    def runs(cur):
        return (as_of, prev_as_of) if cur == "measures" else (prev_as_of, as_of)

    def ev_diff(cur, prev, vehicles):
        return q(con, f"""SELECT c.subject, c.breakdown_key, count(*) AS n FROM {cur} c
                          WHERE c.measure = 'fragility_event' AND c.value_text = 'event'
                            AND c.subject {'' if vehicles else 'NOT '}LIKE 'cik:%'
                            AND NOT EXISTS (SELECT 1 FROM {prev} p WHERE p.measure = 'fragility_event'
                                            AND p.value_text = 'event'
                                            AND {_same_run(ev_key, *runs(cur))})
                          GROUP BY 1, 2 ORDER BY 1, 2""")
    for title, rows, key in (("Apparus", ev_diff("measures", "prev_measures", False), "F_new"),
                             ("Disparus", ev_diff("prev_measures", "measures", False), "F_gone")):
        L.append(f"**{title}** (trimestres des groupes) :" if rows else f"**{title}** : aucun.")
        for r in rows:
            L.append(f"- {GROUP_NAMES.get(r['subject'], r['subject'])} : {r['breakdown_key']} ({F_FR[r['breakdown_key']]}) — "
                     f"{T.n('measures', {key: [r['subject'], r['breakdown_key']]}, r['n'])} trimestre(s)")
        L.append("")
    vn, vg = Counter(), Counter()
    for c_, rows in ((vn, ev_diff("measures", "prev_measures", True)), (vg, ev_diff("prev_measures", "measures", True))):
        for r in rows:
            c_[r["breakdown_key"]] += r["n"]
    if vn or vg:
        L.append("Véhicules BDC de l'univers (D-0045, D-0047), événements apparus et disparus : " + " ; ".join(
            f"{f} +{T.n('measures', {'F_vehicle_new': f}, vn[f])} / −{T.n('measures', {'F_vehicle_gone': f}, vg[f])}"
            for f in sorted(set(vn) | set(vg))) + ".")
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
                   AND subject NOT LIKE 'cik:%' GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2""")
    L.append("- Cellules de l'annexe F des groupes, par statut et motif : " + " ; ".join(
        f"{fr(r['status'])}{(' / ' + ND_FR.get(r['nd'], r['nd'])) if r['nd'] else ''} {T.n('measures', {'annexF': [r['status'], r['nd']]}, r['n'])}" for r in fe) + ".")
    fv = q(con, """SELECT status, coalesce(nd_reason, '') AS nd, count(*) AS n FROM measures WHERE measure = 'fragility_event'
                   AND subject LIKE 'cik:%' GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2""")
    if fv:
        L.append("- Cellules de F11 à F16 des véhicules BDC (D-0045, D-0047), par statut et motif : " + " ; ".join(
            f"{fr(r['status'])}{(' / ' + ND_FR.get(r['nd'], r['nd'])) if r['nd'] else ''} {T.n('measures', {'annexF_vehicles': [r['status'], r['nd']]}, r['n'])}" for r in fv) + ".")
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
             + " ; pièces arrêtées à leur en-tête : " + ", ".join(f"{k} {T.n('exclusions', {'header_only': k}, v)}"
                                                                  for k, v in sorted(bl.get("header_only", {}).items())) + ".")
    L.append(f"- Lignes rejetées par la validation : {T.n('exclusions', {'validation_failed': True}, stats['observations']['rejected_semantic'])}.")
    dup = {t: v for t, v in (stats.get("pk_duplicates") or {}).items() if v.get("dropped")}
    L.append("- Doublons de clé primaire écartés à l'assemblage : " + (", ".join(
        f"`{t}` {T.n(t, {'pk_duplicates': t}, v['dropped'])} (collisions : {T.n(t, {'pk_collisions': t}, v['collision_keys'])})"
        for t, v in sorted(dup.items())) if dup else "aucun") + ".")
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
        L.append("- Groupes d'émetteurs couverts : " + ", ".join(group_label(r["subject"]) for r in grp) + ".")
        L.append("")
    L += text_yield_section(con, T, stats)
    L += discovery_yield_section(con, T, stats)
    L += paths_formd_yield_section(con, T)
    L.append("## Exclusions nouvelles, par motif")
    L.append("")
    ex_new = {r["reason"]: r["n"] for r in q(con, """SELECT reason, count(*) AS n FROM exclusions c WHERE NOT EXISTS
                                                     (SELECT 1 FROM prev_exclusions p WHERE p.exclusion_key = c.exclusion_key)
                                                     GROUP BY 1""")}
    ex_gone = {r["reason"]: r["n"] for r in q(con, """SELECT reason, count(*) AS n FROM prev_exclusions c WHERE NOT EXISTS
                                                      (SELECT 1 FROM exclusions p WHERE p.exclusion_key = c.exclusion_key)
                                                      GROUP BY 1""")}
    for r in sorted(set(ex_new) | set(ex_gone), key=lambda k: (-ex_new.get(k, 0), k)):
        L.append(f"- `{r}` : +{T.n('exclusions', {'reason_new': r}, ex_new.get(r, 0))}, "
                 f"−{T.n('exclusions', {'reason_gone': r}, ex_gone.get(r, 0))}")
    if not ex_new and not ex_gone:
        L.append("- Aucune.")
    L.append("")
    L.append("## Décisions et variantes nouvelles")
    L.append("")
    new_dec = [(d, t) for d, t in decisions_list() if not P or d not in P["decisions"]]
    for d, t in new_dec:
        L.append(f"- {d} — {t}.")
    if not new_dec:
        L.append("- Aucune.")
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
    fd = q(con, """SELECT form, count(DISTINCT accession) AS n FROM documents WHERE accession IS NOT NULL AND accession NOT IN
                   (SELECT accession FROM prev_documents WHERE accession IS NOT NULL) GROUP BY 1 ORDER BY 2 DESC, 1""")
    L.append(("Dépôts lus pour la première fois : " + ", ".join(f"{r['form']} {T.n('documents', {'form_new': r['form']}, r['n'])}"
                                                              for r in fd if r["form"]) + ".") if fd else "Aucun.")
    L.append("")
    L.append("## Valeurs changées pour des périodes déjà publiées")
    L.append("")
    pk = ("measure", "subject", "counterparty", "period_start", "period_end", "view", "as_of", "term", "breakdown_key",
          "financing_policy", "constant_perimeter", "variant")
    ch = q(con, f"""SELECT c.measure, count(*) FILTER (WHERE c.value IS DISTINCT FROM p.value
                                                   OR c.value_text IS DISTINCT FROM p.value_text) AS v,
                           count(*) FILTER (WHERE c.status IS DISTINCT FROM p.status
                                                   OR c.nd_reason IS DISTINCT FROM p.nd_reason) AS s
                    FROM measures c JOIN prev_measures p ON {_same_run(pk, as_of, prev_as_of)} GROUP BY 1 HAVING v > 0 OR s > 0
                    ORDER BY 2 DESC, 1""")
    nw = {r["measure"]: r["n"] for r in q(con, f"""SELECT measure, count(*) AS n FROM measures c WHERE NOT EXISTS
                                                    (SELECT 1 FROM prev_measures p WHERE {_same_run(pk, as_of, prev_as_of)})
                                                    GROUP BY 1""")}
    gn = {r["measure"]: r["n"] for r in q(con, f"""SELECT measure, count(*) AS n FROM prev_measures c WHERE NOT EXISTS
                                                    (SELECT 1 FROM measures p WHERE {_same_run(pk, prev_as_of, as_of)})
                                                    GROUP BY 1""")}
    if ch or nw or gn:
        L.append("Cellules de même clé dont la valeur, le statut ou le motif a changé, puis cellules apparues et disparues, "
                 "par mesure :")
        L.append("")
        L.append("| Mesure | Valeur changée | Statut ou motif changé | Apparues | Disparues |")
        L.append("| --- | ---: | ---: | ---: | ---: |")
        chd = {r["measure"]: r for r in ch}
        for m in sorted(set(chd) | set(nw) | set(gn), key=lambda m: (-(chd[m]["v"] if m in chd else 0), m)):
            r = chd.get(m, {"v": 0, "s": 0})
            L.append(f"| `{m}` | {T.n('measures', {'changed_value': m}, r['v'])} | {T.n('measures', {'changed_status': m}, r['s'])} | "
                     f"{T.n('measures', {'cells_new': m}, nw.get(m, 0))} | {T.n('measures', {'cells_gone': m}, gn.get(m, 0))} |")
        L.append("")
    else:
        L.append("Aucune cellule changée, apparue ni disparue.")
        L.append("")
    c4 = q(con, """SELECT subject, count(*) AS n FROM controls WHERE control = 'c4_restatement_detection' AND status = 'mismatch'
                   GROUP BY 1 ORDER BY 1""")
    L.append("Même identité de fait, valeurs différentes selon le dépôt (C4), publiées sans écrasement ; la cause de "
             "révision (`recast_cause`) se lit au cas par cas dans `controls` : " +
             ", ".join(f"{GROUP_NAMES.get(r['subject'], r['subject'])} {T.n('controls', {'c4': r['subject']}, r['n'])}" for r in c4) + ".")
    L.append("")
    L.append("## Arêtes nouvelles")
    L.append("")
    def edge_diff(cur, prev):
        return q(con, f"""SELECT family, edge_evidence, count(*) AS n FROM {cur} c WHERE link_kind = 'edge' AND NOT EXISTS
                          (SELECT 1 FROM {prev} p WHERE p.link_kind = 'edge' AND p.link_key = c.link_key)
                          GROUP BY 1, 2 ORDER BY 1, 2""")
    for title, rows, key in (("Apparues", edge_diff("links", "prev_links"), "edges_new"),
                             ("Disparues", edge_diff("prev_links", "links"), "edges_gone")):
        L.append(f"- {title} : " + (", ".join(f"{r['family']}/{r['edge_evidence']} {T.n('links', {key: [r['family'], r['edge_evidence']]}, r['n'])}"
                                              for r in rows) if rows else "aucune") + ".")
    L.append("")
    L.append("## Contrôles qui ont basculé")
    L.append("")
    cpk = ("control", "subject", "period_start", "period_end", "view", "as_of", "breakdown_key", "mapping_variant")
    fl = q(con, f"""SELECT c.control, p.status AS before, c.status AS after, count(*) AS n FROM controls c
                    JOIN prev_controls p ON {_same_run(cpk, as_of, prev_as_of)} WHERE c.status IS DISTINCT FROM p.status
                    GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""")
    for r in fl:
        L.append(f"- {r['control'].split('_')[0].upper()} : `{r['before']}` → `{r['after']}` "
                 f"{T.n('controls', {'flipped': [r['control'], r['before'], r['after']]}, r['n'])}")
    if not fl:
        L.append("- Aucun.")
    L.append("")
    L.append("## Entités pending")
    L.append("")
    pend = q(con, "SELECT name FROM entities WHERE record_kind = 'entity' AND status = 'pending' ORDER BY name")
    L.append(f"{T.n('entities', {'pending': True}, len(pend))} entités nommées dans des observations sans identité affirmée par une pièce, "
             "visibles dans `entities`, absentes des agrégats : " + ", ".join(f"« {r['name']} »" for r in pend) + ".")
    L.append("")
    L.append("## Travail not_processed")
    L.append("")
    npr = q(con, "SELECT item_kind, count(*) AS n FROM exclusions WHERE reason = 'not_processed' GROUP BY 1 ORDER BY 2 DESC, 1")
    L.append("Exclusions `not_processed`, par nature d'élément : " + (", ".join(
        f"{r['item_kind']} {T.n('exclusions', {'not_processed': r['item_kind']}, r['n'])}" for r in npr) if npr else "aucune") + ".")
    L.append("")
    L.append("## Paires non additives")
    L.append("")
    cnt = stats.get("non_additive_candidates", {})
    mute = [k for k, v in sorted(cnt.items()) if v == 0]
    L.append("Relations candidates par paire du registre : " + ", ".join(f"{k} {T.n('links', {'pair_candidates': k}, v)}" for k, v in sorted(cnt.items()))
             + f". Paires muettes : {', '.join(mute) if mute else 'aucune'}.")
    L.append("")
    L.append("## Changements dus à une nouvelle passe de lecture ou au code")
    L.append("")
    ob = q(con, """SELECT (SELECT count(*) FROM observations c WHERE NOT EXISTS
                            (SELECT 1 FROM prev_observations p WHERE p.obs_key = c.obs_key)) AS new_rows,
                          (SELECT count(DISTINCT content_key) FROM observations c WHERE NOT EXISTS
                            (SELECT 1 FROM prev_observations p WHERE p.obs_key = c.obs_key)) AS new_blocks,
                          (SELECT count(*) FROM prev_observations c WHERE NOT EXISTS
                            (SELECT 1 FROM observations p WHERE p.obs_key = c.obs_key)) AS gone_rows""")[0]
    L.append(f"Lecture : {T.n('observations', {'obs_new': True}, ob['new_rows'])} lignes d'observation nouvelles, dans "
             f"{T.n('observations', {'obs_new_blocks': True}, ob['new_blocks'])} blocs, et "
             f"{T.n('observations', {'obs_gone': True}, ob['gone_rows'])} disparues. Code : les décisions nouvelles ci-dessus "
             "disent ce qui a changé.")
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
    by = nport_cells(con) if "nport" in (config.load().get("scope") or []) else {}
    if by:
        # volet F de D-0058 : série complète, une table par titre
        L.append("## SoftBank (NF:SOFTBANK) : obligations valorisées par les fonds (Form N-PORT)")
        L.append("")
        L.append("Valeur déclarée ÷ nominal, dans la monnaie du titre, au dernier dépôt de chaque série pour la date de "
                 "portefeuille ; nombre de séries (un fonds fermé sans série compte pour une). Perspective `counterparty` : "
                 "jamais une probabilité de défaut ni un fait comptable de SoftBank (D-0058, points 8 et 28).")
        L.append("")
        for sec, rs in sorted(by.items(), key=lambda kv: (kv[1][-1]["fl"].get("maturity") or "", kv[0])):
            L.append(f"**{nport_title(sec, rs[-1]['fl'])}**")
            L.append("")
            L.append("| Date de portefeuille | Valeur ÷ nominal | Séries |")
            L.append("| --- | ---: | ---: |")
            for r in rs:
                L.append(f"| {r['period_end']} | {T.m(r, fmt='pct')} | "
                         f"{T.n('measures', {'nport_series': [sec, r['period_end']]}, r['fl'].get('n_series'))} |")
            L.append("")
    if "ownership" in (config.load().get("scope") or []):
        L += ownership_series(con, T)
    if "nport" in (config.load().get("scope") or []):
        L += bonds_series(con, T)
        L += unlisted_series(con, T)
        L += credit_series(con, T)
    if "labs" in (config.load().get("scope") or []):
        L += labs_tagged_series(con, T)
        L += lab_terms_series(con, T)
    L += backlog_series(con, T)
    L += ppe_components_series(con, T)
    if "lender_portfolio" in (config.load().get("scope") or []):
        # véhicules BDC des plateformes de présentation (D-0045 ; D-0055, point 7) : série complète, vue as_known
        lp = config.load().get("lender_portfolio") or {}
        by, names, evd = lp_data(con)
        for sj in dict.fromkeys(s for _, vs in lp_platforms(names, lp) for s in vs):
            last = sorted(names[sj])[-1]
            L.append(f"## {names[sj][last]} (véhicule BDC, {sj})")
            L.append("")
            L.append("| Date du bilan | Juste valeur ÷ coût | Intérêts capitalisés | Engagements non tirés ÷ portefeuille | Événements (F11 à F13) |")
            L.append("| --- | ---: | ---: | ---: | --- |")
            for d in sorted(by[sj]):
                m = by[sj][d]
                evs = [f for f, ds in sorted(evd[sj].items()) if d in ds]
                L.append(f"| {d} | {lp_cell_txt(T, m.get('bdc_portfolio_fv_to_cost'))} | {lp_cell_txt(T, m.get('bdc_portfolio_pik_share'))} | "
                         f"{lp_cell_txt(T, m.get('bdc_portfolio_unfunded_ratio'))} | {', '.join(evs)} |")
            L.append("")
            if "lender_liabilities" in (config.load().get("scope") or []):
                L += series_liabilities(con, T, sj)
    return "\n".join(L) + "\n", T.rows


def series_liabilities(con, T, sj):
    """Passif et offres de rachat d'un véhicule BDC (D-0047), série complète, vue as_known."""
    rows = q(con, """SELECT * FROM measures WHERE subject = ? AND (measure LIKE 'bdc_liab_%' OR (measure = 'fragility_event'
                     AND breakdown_key = 'F14' AND value_text = 'event')) AND view = 'as_known' ORDER BY period_end, measure""", sj)
    by = defaultdict(dict)
    for r in rows:
        by[r["period_end"]][r["measure"] if r["measure"] != "fragility_event" else "F14"] = r
    L = []
    if by:
        L.append("Passif (D-0047) :")
        L.append("")
        L.append("| Date du bilan | Couverture | Dette ÷ actif net | Passif ÷ actif net | F14 |")
        L.append("| --- | ---: | ---: | ---: | --- |")
        for d in sorted(by):
            m = by[d]
            if not any(k.startswith("bdc_liab_") for k in m):
                continue
            c, de, ln = m.get("bdc_liab_asset_coverage"), m.get("bdc_liab_debt_to_net_assets"), m.get("bdc_liab_liabilities_to_net_assets")
            L.append(f"| {d} | {T.m(c, fmt='pct', dec=0) if c else '—'} | {T.m(de, fmt='x') if de and de['value'] is not None else (T.m(de) if de else '—')} | "
                     f"{T.m(ln, fmt='x') if ln and ln['value'] is not None else (T.m(ln) if ln else '—')} | {'oui' if 'F14' in m else ''} |")
        L.append("")
    offs = defaultdict(dict)
    for r in q(con, """SELECT * FROM measures WHERE subject = ? AND (measure LIKE 'bdc_tender_%' OR (measure = 'fragility_event'
                       AND breakdown_key = 'F15')) ORDER BY period_end""", sj):
        fl = json.loads(r["flags"]) if r["flags"] else {}
        o = offs[fl.get("offer")]
        o["offer_date"], o["end"] = fl.get("offer_date"), r["period_end"]
        o["F15" if r["measure"] == "fragility_event" else r["measure"]] = r
    if offs:
        L.append("Offres de rachat (D-0047) :")
        L.append("")
        L.append("| SC TO-I | Expiration | Demande ÷ plafond | Acceptées ÷ apportées | F15 |")
        L.append("| --- | --- | ---: | ---: | --- |")
        for o in sorted(offs.values(), key=lambda o: o["offer_date"] or ""):
            dm, ac = o.get("bdc_tender_demand_ratio"), o.get("bdc_tender_acceptance_ratio")
            L.append(f"| {o['offer_date']} | {o['end']} | {T.m(dm, fmt='x') if dm and dm['value'] is not None else (T.m(dm) if dm else '—')} | "
                     f"{T.m(ac, fmt='pct', dec=1) if ac else '—'} | {f15_txt(o.get('F15'))} |")
        L.append("")
    return L


# -- livrable d'audit -------------------------------------------------------------------

RULE_TEXT = {
    "anchor_first_present": "premier concept de la liste d'ancrage (annexe B) présent dans la linkbase de présentation "
                            "du déposant, dans un rôle de l'état concerné ; fixé avant tout contrôle",
    "definition_first_present": "grandeur sans ancre : premier concept standard dont la définition de la taxonomie 2026 "
                                "correspond, présent dans la linkbase de présentation pour l'état concerné ; liste fixée "
                                "avant tout contrôle",
    "D1_label_match": "état annuel lu en HTML dans le 424B4 : concept du 10-Q dont le libellé correspond à la ligne "
                      "(is_tagged = false)"}


MEASURE_PK = ("measure", "subject", "counterparty", "period_start", "period_end", "view", "as_of", "term",
              "breakdown_key", "financing_policy", "constant_perimeter", "variant")


def _by_key(con, table, key_col, cols, keys):
    """Lignes d'une table pour une liste de clés uniques, en une requête : {clé: ligne}."""
    if not keys:
        return {}
    rows = con.execute(f"SELECT {', '.join(cols)} FROM {table} WHERE {key_col} IN (SELECT unnest(?::VARCHAR[]))",
                       [sorted(keys)]).fetchall()
    return {r[0]: r for r in rows}


def numbers_csv(con, rows, path):
    """Chaque nombre publié, avec l'accession et l'emplacement de chacun de ses termes. Les cellules, les
    preuves des liens et les termes se lisent d'un bloc (une requête par table, et non quatre par nombre) ;
    l'ordre des termes reste celui des requêtes d'avant (clé du fait, puis clé de l'observation)."""
    cell = {tuple(r[:12]): (r[12], r[13]) for r in
            con.execute(f"SELECT {', '.join(MEASURE_PK)}, lineage, flags FROM measures").fetchall()}
    evidence = dict(con.execute("SELECT link_key, evidence_keys FROM links").fetchall())
    plan = []
    for r in rows:
        fkeys, okeys, found = [], [], False
        if r["kind"] == "measure":
            k = json.loads(r["key"])
            key = tuple(k[x] for x in MEASURE_PK)
            c = cell.get(key) if all(isinstance(x, str) for x in key) else _cell_by_query(con, key)
            if c:
                found = True
                lin = json.loads(c[0]) if c[0] else []
                fl = json.loads(c[1]) if c[1] else {}
                fkeys = [x for x in lin if not x.startswith("obs:")]
                okeys = [x[4:] for x in lin if x.startswith("obs:")]
                for lk in fl.get("links") or []:
                    ev = evidence.get(lk) if isinstance(lk, str) else _evidence_by_query(con, lk)
                    if ev:
                        okeys += json.loads(ev)
        plan.append((r, found, fkeys, okeys))
    facts = _by_key(con, "facts", "fact_key", ("fact_key", "accession", "locator", "is_tagged", "tier"),
                    {f for _, ok, fk, _ in plan if ok for f in fk})
    obs = _by_key(con, "observations", "obs_key", ("obs_key", "accession", "locator", "tier"),
                  {o for _, ok, _, ks in plan if ok for o in ks})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["document", "token", "kind", "cell_key", "field", "value", "text", "term_key", "accession",
                    "locator", "is_tagged", "tier"])
        for r, found, fkeys, okeys in plan:
            terms = []
            if found:
                terms += [facts[f] for f in sorted(set(fkeys)) if f in facts]
                terms += [(o[0], o[1], o[2], False, o[3]) for o in (obs[x] for x in sorted(set(okeys)) if x in obs)]
            if not terms:
                terms = [(None, None, None, None, None)]
            for t in terms:
                w.writerow([r["document"], r["token"], r["kind"], r["key"], r["field"], r["value"], r["text"], *t])


def _cell_by_query(con, key):
    """Repli de numbers_csv quand une clé n'est pas faite de chaînes : la requête d'avant."""
    c = q(con, """SELECT lineage, flags FROM measures WHERE measure = ? AND subject = ? AND counterparty = ?
                  AND period_start = ? AND period_end = ? AND view = ? AND as_of = ? AND term = ?
                  AND breakdown_key = ? AND financing_policy = ? AND constant_perimeter = ? AND variant = ?""", *key)
    return (c[0]["lineage"], c[0]["flags"]) if c else None


def _evidence_by_query(con, lk):
    ev = q(con, "SELECT evidence_keys FROM links WHERE link_key = ?", lk)
    return ev[0]["evidence_keys"] if ev else None


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


def edges_citing(con, first):
    """Arêtes dont la liste des preuves contient, comme sous-chaîne, la clé d'une ligne des passes du bloc
    text : ce que testait `evidence_keys LIKE '%' || obs_key || '%'` pour chaque arête et chaque ligne. Les
    clés se cherchent par leur préfixe commun, position par position. None si une clé est vide ou contient
    un caractère spécial de LIKE : la requête d'avant s'applique alors."""
    keys = [k for (k,) in con.execute("""SELECT obs_key FROM observations WHERE pass_id >= ?
                                         AND CAST(block_kind AS VARCHAR) NOT LIKE 'discovery_%'""", [first]).fetchall()]
    if any(k is None or k == "" or "%" in k or "_" in k or "\\" in k for k in keys):
        return None
    if not keys:
        return []
    m = min(len(k) for k in keys)
    by_prefix = {}
    for k in keys:
        by_prefix.setdefault(k[:m], []).append(k)
    hit = []
    for lk, ev in con.execute("SELECT link_key, evidence_keys FROM links WHERE link_kind = 'edge'").fetchall():
        if ev is not None and any(ev.startswith(k, i) for i in range(len(ev) - m + 1)
                                  for k in by_prefix.get(ev[i:i + m], ())):
            hit.append(lk)
    return hit


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
    lines = q(con, """SELECT kind, validation_state, count(*) AS n FROM observations WHERE pass_id >= ?
                       AND CAST(block_kind AS VARCHAR) NOT LIKE 'discovery_%' GROUP BY 1, 2 ORDER BY 1, 2""", first)
    obs = sum(r["n"] for r in lines if r["kind"] == "observation" and r["validation_state"] == "valid")
    abst = sum(r["n"] for r in lines if r["kind"] == "abstention" and r["validation_state"] == "valid")
    rej = sum(r["n"] for r in lines if r["validation_state"] != "valid")
    L.append(f"- Lignes rendues dans les passes du bloc : {T.n('observations', {'text_obs': True}, obs)} observations, "
             f"{T.n('observations', {'text_abst': True}, abst)} abstentions motivées, "
             f"{T.n('observations', {'text_rejected': True}, rej)} rejetées par la validation.")
    hit = edges_citing(con, first)
    if hit is None:
        ed = q(con, """SELECT l.family, l.edge_evidence, count(DISTINCT l.link_key) AS n FROM links l
                        WHERE l.link_kind = 'edge' AND EXISTS (SELECT 1 FROM observations o WHERE o.pass_id >= ?
                              AND CAST(o.block_kind AS VARCHAR) NOT LIKE 'discovery_%'
                              AND l.evidence_keys LIKE '%' || o.obs_key || '%') GROUP BY 1, 2 ORDER BY 1, 2""", first)
    else:
        ed = q(con, """SELECT family, edge_evidence, count(DISTINCT link_key) AS n FROM links
                       WHERE link_kind = 'edge' AND link_key IN (SELECT unnest(?::VARCHAR[])) GROUP BY 1, 2 ORDER BY 1, 2""",
               hit)
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
    fe = q(con, "SELECT count(*) AS n FROM measures WHERE measure = 'fragility_event' AND value_text = 'event' AND subject NOT LIKE 'cik:%'")
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
        rows = q(con, """SELECT status, coalesce(value_text, '') AS v, coalesce(nd_reason, '') AS nd, count(*) AS n
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
    """Blocs du catalogue et blocs lus. Ne dépend que du catalogue, de la configuration, du code et des
    fichiers d'observations présents (non de leur contenu) : repris du mémo (D-0062) tant que rien de cela
    ne change, la lecture du catalogue entier coûtant à elle seule plusieurs secondes."""
    import inspect
    from . import memo
    read = {p.stem for p in config.OBS_DIR.glob("*.jsonl") if not p.name.endswith(".rejected.jsonl")}
    key = memo.digest([inspect.getsource(_block_stats), sorted(read)])
    return memo.Memo(memo.inputs_fingerprint()).value("render_block_stats", lambda: _block_stats(read), key=key)


def _block_stats(read):
    from . import reader
    cat = {b["content_key"]: b for b in reader.load_catalog()}
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


def main(as_of=None):
    as_of = config.as_of(as_of)
    stats = json.loads((config.ROOT / "work" / "tmp" / "assemble_stats.json").read_text())
    config.check_as_of(stats["as_of"], "work/tmp/assemble_stats.json", "relancer l'assemblage")     # tables au même as_of
    con = config.duckdb_connect()
    load(con, as_of)
    stats["blocks"] = block_stats()
    rows = []
    for name, fn in (("synthesis.md", synthesis), ("delta.md", delta), ("series.md", series)):
        text, r = fn(con, as_of, stats)
        (config.ROOT / name).write_text(text, encoding="utf-8")
        rows += r
    audit(con, as_of, rows, stats)
    print("rendus écrits ;", len(rows), "nombres publiés")


if __name__ == "__main__":
    # mêmes rendus sous PYTHONHASHSEED=0 et 1, à la durée mesurée de l'assemblage près (D-0072, point 3 e)
    main(*sys.argv[1:2])
