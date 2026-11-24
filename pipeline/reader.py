"""File de lecture et validation des observations (§7.4).

Le code sert les blocs naturels dans l'ordre du signal, jusqu'au plafond de lecture ;
l'exécutant rend les lignes d'un bloc d'un coup, une fois le bloc lu, au moins une par
bloc (observation ou abstention). Le code renvoie aussitôt les erreurs de schéma ;
l'exécutant reprend une fois ; puis le code écrit le fichier du bloc avec les lignes qui
passent, même s'il n'y en a aucune. Les rejets au schéma se gardent à côté.
La validation sémantique se fait au chargement dans `observations` (load.py).

Gardes de lecture (guards.py, D-0087), à la soumission seulement : une ligne qui nomme une personne physique ne
s'écrit nulle part, même avec --final ; un montant qui ne se lit pas dans sa citation est une alerte, que l'exécutant
corrige ou confirme (--confirm) ; une ligne déjà écrite dans la même passe ne s'écrit pas deux fois.

Usage :
  python -m pipeline.reader open-pass [--list L] [--id AAAA-MM-JJTHH:MM:SSZ]
  python -m pipeline.reader status
  python -m pipeline.reader next [--max-chars N]
  python -m pipeline.reader submit CONTENT_KEY FICHIER.jsonl [--confirm] [--final] [--next]
  python -m pipeline.reader show CONTENT_KEY
  python -m pipeline.reader check [--list L]      # gardes sur les lignes de l'as_of courant, avant le réassemblage
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from decimal import Decimal, InvalidOperation

from . import config, guards
from .registry import ENUMS

CATALOG = config.DB_DIR / "blocks.jsonl"          # recalculé à chaque exécution
CATALOG_EXT = config.DB_DIR / "text_blocks_ext.jsonl"   # bloc `text` de §14, s'il est ouvert
CATALOG_DISC = config.DB_DIR / "discovery_blocks.jsonl"  # bloc `discovery` de §14, s'il est ouvert
CATALOG_NF = config.DB_DIR / "nf_discovery_blocks.jsonl"   # piste des non-déposants de la découverte (D-0044)
CATALOG_MT = config.DB_DIR / "montages_blocks.jsonl"       # bloc montages : financeur d'un montage nommé ailleurs (D-0046)
CATALOG_6K = config.DB_DIR / "foreign_6k_blocks.jsonl"     # paragraphes des 6-K des groupes émetteurs étrangers (D-0048)
CATALOG_SB = config.DB_DIR / "sb_blocks.jsonl"             # dépôts propres de SoftBank et déposants contrôlés (D-0058, volets B et C)
STATE = config.WORK / "tmp" / "reading_state.json"
RUN = config.WORK / "tmp" / "run.json"              # as_of et pass_id de l'exécution

# Champs qu'une ligne peut porter : nom -> type ("enum:<nom>", "str", "decimal", "date", "bool")
LINE_FIELDS = {
    "kind": "enum:obs_kind",
    "abstention_reason": "enum:abstention_reason",
    "quote": "str",
    "counterparty_name": "str",
    "counterparty_evidence": "enum:counterparty_evidence",
    "derivation_method": "enum:derivation_method",
    "payer": "str", "payee": "str",
    "amount": "decimal", "amount_lower": "decimal", "amount_upper": "decimal",
    "unit": "str", "currency": "str",
    "amount_nature": "enum:amount_nature",
    "amount_origin": "enum:amount_origin",
    "amount_qualifier": "enum:amount_qualifier",
    "candidate_fact_key": "str",
    "period_start": "date", "period_end": "date", "period_label": "str",
    "stage": "enum:stage",
    "event_type": "enum:event_type",
    "event_date": "date",
    "instrument_key": "str",
    "family": "enum:family",
    "edge_type": "enum:edge_type",
    "link_category": "enum:link_category",
    "exposure_block": "enum:exposure_block",
    "category_id": "enum:category_id",
    "measurement_basis": "enum:measurement_basis",
    "component_kind": "enum:component_kind",
    "conditionality": "enum:conditionality",
    "trigger_description": "str",
    "trigger_occurred": "enum:trigger_occurred",
    "ultimate_obligor": "str",
    "seniority": "enum:seniority",
    "recourse": "enum:recourse",
    "is_ring_fenced": "bool",
    "signal": "enum:signal",
    "signal_present": "bool",
    "redacted": "bool",
    "judgment_sensitive": "bool",
    "price_setting_participation": "enum:price_setting_participation",
    "consolidation_treatment": "enum:consolidation_treatment",
    "party_role": "str",
    "party_is_financial_institution": "bool",
    "exhibit_title": "str",
    "note": "str",
    # D-0067 : clause d'un contrat et capacité telles qu'écrites
    "clause_kind": "enum:clause_kind",
    "capacity_value": "decimal", "capacity_unit": "enum:capacity_unit", "capacity_kind": "enum:capacity_kind",
    "capacity_qualifier": "enum:amount_qualifier",
    # D-0068 : ligne de carnet, telle qu'écrite par le vendeur
    "backlog_basis": "enum:backlog_basis", "backlog_statement": "enum:backlog_statement",
    # D-0076 : ligne de composante des en-cours, telle qu'écrite
    "asset_component": "enum:asset_component", "asset_state": "enum:asset_state",
    "component_of": "enum:component_of", "component_statement": "enum:component_statement",
}
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_CCY = re.compile(r"^[A-Z]{3}$")


def schema_errors(line):
    """Erreurs de schéma d'une ligne (liste vide si conforme)."""
    errs = []
    if not isinstance(line, dict):
        return ["la ligne n'est pas un objet JSON"]
    for k in line:
        if k not in LINE_FIELDS:
            errs.append(f"champ inconnu : {k}")
    kind = line.get("kind")
    if kind not in ENUMS["obs_kind"]:
        errs.append("kind doit valoir observation ou abstention")
    for k, v in line.items():
        t = LINE_FIELDS.get(k)
        if t is None or v is None:
            continue
        if t.startswith("enum:"):
            if v not in ENUMS[t[5:]]:
                errs.append(f"{k} = {v!r} hors énumération {t[5:]}")
        elif t == "decimal":
            try:
                Decimal(str(v))
            except InvalidOperation:
                errs.append(f"{k} n'est pas un nombre décimal : {v!r}")
        elif t == "date":
            if not (isinstance(v, str) and _DATE.match(v)):
                errs.append(f"{k} doit être une date AAAA-MM-JJ : {v!r}")
        elif t == "bool":
            if not isinstance(v, bool):
                errs.append(f"{k} doit être un booléen")
        elif t == "str":
            if not isinstance(v, str) or not v.strip():
                errs.append(f"{k} doit être une chaîne non vide")
    if kind == "abstention":
        if not line.get("abstention_reason"):
            errs.append("une abstention porte son motif (abstention_reason)")
    if kind == "observation":
        if not line.get("quote"):
            errs.append("une observation porte sa citation (quote)")
        if line.get("amount") is not None:
            if not line.get("unit"):
                errs.append("un montant porte son unité")
            if not line.get("amount_origin") or line.get("amount_origin") == "none":
                errs.append("un montant porte son origine (tagged_reference ou narrative_only)")
            if not line.get("amount_qualifier") or line.get("amount_qualifier") == "none":
                errs.append("un montant porte son qualificatif (exact, approximately, ...)")
            if line.get("currency") and not _ISO_CCY.match(line["currency"]):
                errs.append("currency : code ISO 4217 attendu")
        if line.get("amount_origin") == "tagged_reference" and not line.get("candidate_fact_key"):
            errs.append("tagged_reference exige candidate_fact_key")
        if line.get("amount_qualifier") == "range" and (line.get("amount_lower") is None
                                                         or line.get("amount_upper") is None):
            errs.append("range exige amount_lower et amount_upper")
        if line.get("counterparty_evidence") == "derivable" and \
                line.get("derivation_method") in (None, "none"):
            errs.append("derivable exige derivation_method (§2.4)")
        if line.get("signal") not in (None, "none") and line.get("signal_present") is None:
            errs.append("un signal porte signal_present")
        if line.get("capacity_value") is not None:
            if line.get("capacity_unit") in (None, "none"):
                errs.append("une capacité porte son unité (MW ou GW, telle qu'écrite)")
            if line.get("capacity_kind") in (None, "none"):
                errs.append("une capacité porte son genre (compute, hosting, power, unspecified)")
            if line.get("capacity_qualifier") in (None, "none"):
                errs.append("une capacité porte son qualificatif (exact, approximately, ...)")
            if line.get("family") not in (None, "none"):
                errs.append("une ligne de capacité est descriptive : sans famille (D-0067, point 6)")
        elif line.get("capacity_unit") not in (None, "none") or line.get("capacity_kind") not in (None, "none"):
            errs.append("unité ou genre de capacité sans capacity_value")
        bb, bs = line.get("backlog_basis"), line.get("backlog_statement")
        if bb not in (None, "none") or bs not in (None, "none"):          # ligne de carnet (D-0068, point 7)
            if bb in (None, "none") or bs in (None, "none"):
                errs.append("une ligne de carnet porte sa base et son énoncé (D-0068, point 7)")
            if line.get("family") not in (None, "none"):
                errs.append("une ligne de carnet est descriptive : sans famille (D-0068, point 7)")
            if bs in ("remaining", "contract_value", "total_contract_value", "change") and line.get("amount") is None:
                errs.append("un énoncé chiffré de carnet porte son montant")
            if bs in ("excluded", "included_no_amount") and line.get("amount") is not None:
                errs.append("une exclusion ou une inclusion sans montant ne porte aucun montant")
            if bs in ("remaining", "excluded", "included_no_amount") and not line.get("period_end"):
                errs.append("un reste, une exclusion ou une inclusion porte sa date (period_end)")
            if not line.get("counterparty_name") or line.get("counterparty_evidence") != "named":
                errs.append("une ligne de carnet nomme le client (counterparty_name, counterparty_evidence named)")
        from .ppe_notes import schema_errors as component_errors     # ligne de composante (D-0076, point 7)
        errs += component_errors(line)
        errs += guards.flow_errors(line)                              # prix d'un financement (D-0087, G1)
    return errs


# -- catalogue et file ---------------------------------------------------------------

def load_catalog():
    out = []
    if CATALOG.exists():
        with open(CATALOG, encoding="utf-8") as fh:
            out = [json.loads(l) for l in fh if l.strip()]
    scope = config.load().get("scope")
    if isinstance(scope, list) and "text" in scope and CATALOG_EXT.exists():
        with open(CATALOG_EXT, encoding="utf-8") as fh:
            out += [json.loads(l) for l in fh if l.strip()]
    # bloc `discovery` de §14 : blocs préparés par tranches, dans l'ordre de la file (D-0036)
    if isinstance(scope, list) and "discovery" in scope and CATALOG_DISC.exists():
        with open(CATALOG_DISC, encoding="utf-8") as fh:
            out += [json.loads(l) for l in fh if l.strip()]
    if isinstance(scope, list) and "discovery" in scope and CATALOG_NF.exists():
        with open(CATALOG_NF, encoding="utf-8") as fh:
            out += [json.loads(l) for l in fh if l.strip()]
    if isinstance(scope, list) and "montages" in scope and CATALOG_MT.exists():
        with open(CATALOG_MT, encoding="utf-8") as fh:
            out += [json.loads(l) for l in fh if l.strip()]
    if CATALOG_6K.exists():
        with open(CATALOG_6K, encoding="utf-8") as fh:
            out += [json.loads(l) for l in fh if l.strip()]
    if CATALOG_SB.exists():
        with open(CATALOG_SB, encoding="utf-8") as fh:
            out += [json.loads(l) for l in fh if l.strip()]
    return out


def first_filed(b):
    """Rang du dépôt d'un bloc parmi ceux de même texte (D-0092) : la date de connaissance, puis l'acceptation, une
    acceptation inconnue venant après, puis le numéro d'accession."""
    return (str(b.get("knowledge_date") or "")[:10] or "9999-99-99", str(b.get("acceptance") or "9999"),
            str(b.get("accession") or ""))


def by_key(catalog=None):
    """Clé de contenu -> bloc qui la représente (D-0092). Entre des blocs de plusieurs dépôts, celui du premier dépôt :
    un texte repris mot pour mot était connu dès sa première publication (§7.3). Entre blocs d'un même dépôt, le dernier
    dans l'ordre des catalogues, comme avant. L'ordre des lignes ne décide donc plus entre deux dépôts."""
    catalog = load_catalog() if catalog is None else catalog
    per = {}                                             # clé -> {accession: [rang du dépôt, dernier bloc]}
    for b in catalog:
        d = per.setdefault(b["content_key"], {})
        acc, rank = b.get("accession"), first_filed(b)
        if acc in d:
            d[acc][0] = min(d[acc][0], rank)
            d[acc][1] = b
        else:
            d[acc] = [rank, b]
    return {k: min(d.values(), key=lambda x: x[0])[1] for k, d in per.items()}


def obs_path(content_key):
    return config.OBS_DIR / f"{content_key}.jsonl"


def rejected_path(content_key):
    return config.OBS_DIR / f"{content_key}.rejected.jsonl"


LIST = None        # fichier de clés de contenu : file de lecture restreinte, dans son ordre


def _state_path():
    if LIST:
        return STATE.parent / f"reading_state_{pathlib.Path(LIST).stem}.json"
    return STATE


def _run_path():
    """Une liste de relecture a sa propre passe (work/tmp/run_<liste>.json) : ses blocs se
    relisent même s'ils ont déjà des lignes, et la passe la plus récente remplace l'ancienne
    au chargement (§7.4)."""
    if LIST:
        p = _list_run_path()
        if p.exists():
            return p
    return RUN


def _list_run_path():
    return RUN.parent / f"run_{pathlib.Path(LIST).stem}.json"


def _read_in_pass(ck, pass_id):
    """Le bloc a reçu des lignes (valides ou rejetées) dans cette passe."""
    for p in (obs_path(ck), rejected_path(ck)):
        if p.exists() and any(json.loads(l).get("pass_id") == pass_id
                              for l in p.read_text(encoding="utf-8").splitlines() if l.strip()):
            return True
    return False


def queue(catalog=None):
    """Blocs sans fichier d'observations, dans l'ordre du signal (§11.1) ; avec une liste,
    seulement ses blocs, dans l'ordre de la liste. Une clé portée par plusieurs blocs se sert une fois, à la place du
    premier dans cet ordre, par le bloc qui la représente (`by_key`, D-0092) : celui que le chargement retiendra."""
    catalog = catalog if catalog is not None else load_catalog()
    chosen = by_key(catalog)
    seen, out = set(), []
    order = None
    if LIST:
        keys = [l.strip() for l in open(LIST, encoding="utf-8") if l.strip()]
        order = {k: i for i, k in enumerate(keys)}
        catalog = [b for b in catalog if b["content_key"] in order]
    repass = _run_path() != RUN
    repass_id = json.loads(_run_path().read_text())["pass_id"] if repass else None
    for b in sorted(catalog, key=(lambda b: order[b["content_key"]]) if order else
                    (lambda b: (_effective_class(b), b["sort_key"]))):
        ck = b["content_key"]
        if ck in seen:
            continue
        if obs_path(ck).exists() and (not repass or _read_in_pass(ck, repass_id)):
            continue
        if b.get("requires") and not _requirement_met(b["requires"], b):
            continue
        seen.add(ck)
        out.append(chosen[ck])
    return out


def _text_scope():
    sc = config.load().get("scope")
    return isinstance(sc, list) and "text" in sc


def text_body(b):
    """Corps de pièce que le bloc `text` de §14 rouvre : les EX-10 arrêtés à leur en-tête
    (clauses des contrats d'origine entre établissements financiers) ; un EX-4 arrêté à son
    en-tête reste exclu (`financial_parties_only`), §14 ne le rouvrant pas."""
    return b.get("block_kind") == "exhibit_body" and (b.get("exhibit_type") or "").upper().startswith("EX-10")


def in_text_block(b):
    """Bloc du bloc `text` de §14 : catalogue étendu (classe 3), ou corps d'EX-10 arrêté à son
    en-tête au premier passage."""
    if b.get("signal_class") == 3:
        return True
    if text_body(b) and b.get("requires"):
        from .exhibits import decide
        return decide(b["requires"])[0] is False
    return False


def _requirement_met(req, b=None):
    """Un corps de pièce n'entre dans la file qu'après lecture de son en-tête (§11.1) ; arrêté
    à l'en-tête au premier passage (établissements financiers seulement), il y entre quand le
    bloc `text` de §14 est ouvert, après les notes et les items de 8-K, s'il s'agit d'un EX-10."""
    from .exhibits import decide
    want, _ = decide(req)
    if want is None:
        return False
    return bool(want) or (_text_scope() and (b is None or text_body(b)))


def _effective_class(b):
    if b["block_kind"] == "exhibit_body" and b.get("requires"):
        from .exhibits import decide
        want, _ = decide(b["requires"])
        if want is False:
            return 4
    return b["signal_class"]


def _chunks(text, cap, overlap=1500):
    """Coupe aux frontières naturelles (lignes), avec recouvrement (§7.4)."""
    if len(text) <= cap:
        return [text]
    lines = text.split("\n")
    chunks, cur, size = [], [], 0
    for ln in lines:
        if size + len(ln) + 1 > cap and cur:
            chunks.append("\n".join(cur))
            # recouvrement : dernières lignes du morceau précédent
            back, bsize = [], 0
            for l2 in reversed(cur):
                if bsize + len(l2) > overlap:
                    break
                back.insert(0, l2)
                bsize += len(l2) + 1
            cur, size = back, bsize
        cur.append(ln)
        size += len(ln) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks


_NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(%|percent|thousand|million|billion|trillion)?", re.I)
_SCALE = {"thousand": Decimal(10) ** 3, "million": Decimal(10) ** 6, "billion": Decimal(10) ** 9,
          "trillion": Decimal(10) ** 12}


_TABLE_SCALE = re.compile(r"\bin\s+(thousand|million|billion)s?\b", re.I)


def text_values(text):
    """Valeurs numériques que le texte affiche, à leur échelle et brutes (pour l'affichage).
    Un tableau « in millions » (ou thousands, billions) affiche des nombres nus : ils valent
    aussi à l'échelle déclarée par le bloc."""
    vals = set()
    table_scales = {_SCALE[m.group(1).lower()] for m in _TABLE_SCALE.finditer(text)}
    for m in _NUM.finditer(text):
        try:
            v = Decimal(m.group(1).replace(",", ""))
        except InvalidOperation:
            continue
        vals.add(v)
        unit = (m.group(2) or "").lower()
        if unit in _SCALE:
            vals.add(v * _SCALE[unit])
        elif unit in ("%", "percent"):
            vals.add(v / 100)
        else:
            for sc in table_scales:
                vals.add(v * sc)
    return vals


def visible_candidates(b):
    """Faits candidats dont la valeur paraît dans le texte du bloc. Le catalogue, la clé de
    contenu et la validation gardent tous les faits ; seul l'affichage est réduit, car un
    montant lu dans le texte ne peut égaler qu'un fait dont la valeur y paraît (D-0017)."""
    cands = b.get("candidate_facts") or []
    vals = text_values(b["text"])
    out = []
    for c in cands:
        try:
            v = Decimal(str(c["value"]))
        except (InvalidOperation, TypeError):
            out.append(c)
            continue
        if v in vals or -v in vals:
            out.append(c)
    return out, len(cands)


def _dims_short(dims):
    """Membres de dimension par leur libellé (le membre lui-même à défaut)."""
    try:
        d = json.loads(dims) if isinstance(dims, str) else (dims or [])
    except ValueError:
        return str(dims)
    return "[" + " ; ".join((x[2] if len(x) > 2 and x[2] else x[1]) for x in d) + "]"


def render_block(b, cap):
    head = {k: b.get(k) for k in ("content_key", "block_kind", "group_id", "cik", "accession",
                                  "form", "filing_date", "item", "exhibit_type", "document",
                                  "note_label", "period_start", "period_end", "knowledge_date",
                                  "filer_name", "groups_named", "terms", "montage", "reading", "party")
            if k in b or k in (
                                      "content_key", "block_kind", "group_id", "cik", "accession", "form")}
    cands, n_all = visible_candidates(b)
    cand_lines = [f"  {c['fact_key']} | {c['concept']} | {c['value']} {c.get('unit') or ''} | "
                  f"{c.get('period_start') or ''}..{c.get('period_end')} | {_dims_short(c.get('dims'))}"
                  for c in cands]
    header = "### BLOC " + json.dumps(head, ensure_ascii=False)
    facts = (f"### FAITS CANDIDATS ({len(cands)} affichés sur {n_all} : valeur présente dans le texte)\n"
             + "\n".join(cand_lines))
    budget = max(cap - len(header) - len(facts) - 200, 4000)
    return header, facts, _chunks(b["text"], budget)


def cmd_lot(small=4000, total=20000):
    """Lot de petits blocs (§7.4) : les blocs suivants de la file tant que chacun fait moins
    de `small` caractères et que le lot ne dépasse pas `total` ; un bloc plus long est servi
    seul par `next`. Chaque bloc garde son fichier et sa validation (submit-lot)."""
    q = queue()
    lot, size = [], 0
    for b in q:
        header, facts, chunks = render_block(b, 10**9)
        n = len(header) + len(facts) + len(chunks[0])   # faits candidats et en-têtes compris (§7.4)
        if n > small:
            break
        if size + n > total and lot:
            break
        lot.append(b)
        size += n
    if not lot:
        print("PAS DE PETIT BLOC EN TÊTE DE FILE : utiliser `next`")
        return
    for b in lot:
        header, facts, chunks = render_block(b, 10**9)
        print(header)
        print(facts)
        print("### TEXTE")
        print(chunks[0])
        print()
    print(f"### LOT : {len(lot)} blocs, {size} caractères ; file restante : {len(q)} blocs")


def cmd_submit_lot(path, final=False, confirm=False):
    """Lignes de plusieurs blocs : champ `block` = clé de contenu ; écrites bloc par bloc. Un bloc refusé (erreur ou
    alerte) n'est pas écrit, les autres le sont : seuls les blocs refusés se soumettent de nouveau."""
    groups = {}
    order = []
    src = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    for raw in src.splitlines():
        if not raw.strip():
            continue
        obj = json.loads(raw)
        ck = obj.pop("block")
        if ck not in groups:
            order.append(ck)
            groups[ck] = []
        groups[ck].append(json.dumps(obj, ensure_ascii=False))
    rc = 0
    # un fichier par liste : deux lecteurs simultanés ne doivent jamais s'échanger leurs lignes (D-0034)
    tmp = STATE.parent / (f"lot_part_{pathlib.Path(LIST).stem}.jsonl" if LIST else "lot_part.jsonl")
    for ck in order:
        tmp.write_text("\n".join(groups[ck]) + "\n", encoding="utf-8")
        r = cmd_submit(ck, str(tmp), final, confirm)
        rc = max(rc, r or 0)
    return rc


def cmd_auto(small=5000, total=22000):
    """Sert un lot si la tête de file est petite, sinon le bloc suivant (en morceaux)."""
    STATE.parent.mkdir(parents=True, exist_ok=True)
    sp = _state_path()
    state = json.loads(sp.read_text()) if sp.exists() else {}
    if state.get("content_key"):
        return cmd_next(None)
    q = queue()
    if not q:
        print("FILE VIDE")
        return
    header, facts, chunks = render_block(q[0], 10**9)
    if len(header) + len(facts) + len(chunks[0]) <= small:
        return cmd_lot(small, total)
    return cmd_next(None)


def cmd_next(max_chars):
    cap = max_chars or config.load()["reading"]["max_read_chars"]
    STATE.parent.mkdir(parents=True, exist_ok=True)
    sp = _state_path()
    state = json.loads(sp.read_text()) if sp.exists() else {}
    q = queue()
    if not q:
        print("FILE VIDE")
        return
    cur = None
    if state.get("content_key"):
        cur = next((b for b in q if b["content_key"] == state["content_key"]), None)
    if cur is None:
        cur, state = q[0], {"content_key": q[0]["content_key"], "chunk": 0}
    header, facts, chunks = render_block(cur, cap)
    i = min(state.get("chunk", 0), len(chunks) - 1)
    print(header)
    print(f"### MORCEAU {i + 1}/{len(chunks)} — file restante : {len(q)} blocs")
    print(facts)
    print("### TEXTE")
    print(chunks[i])
    if i + 1 < len(chunks):
        state["chunk"] = i + 1
        print(f"### SUITE : relancer `next` pour le morceau {i + 2}/{len(chunks)} avant de rendre les lignes")
    else:
        state["chunk"] = len(chunks) - 1
        state["complete"] = True
        print("### FIN DU BLOC : rendre les lignes avec `submit`")
    sp.write_text(json.dumps(state))


def _run_info():
    """As_of et pass_id de la passe en cours. Une passe ouverte à un autre as_of que config.yaml arrête la commande ;
    faute de fichier, l'as_of est celui de la configuration, jamais la date du jour (D-0073)."""
    p = _run_path()
    if p.exists():
        run = json.loads(p.read_text())
        config.check_as_of(run.get("as_of"), f"work/tmp/{p.name}", "ouvrir une passe nouvelle")
        return run
    now = dt.datetime.now(dt.timezone.utc)
    return {"as_of": config.as_of(), "pass_id": now.isoformat(timespec="seconds")}


def _stored(run, obj):
    """Ligne telle qu'elle s'écrit dans le fichier du bloc : la passe en tête, clés triées."""
    return json.dumps({"as_of": run["as_of"], "pass_id": run["pass_id"], **obj}, ensure_ascii=False, sort_keys=True)


def cmd_submit(content_key, path, final=False, confirm=False):
    lines = []
    raw_lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines() if path != "-" else sys.stdin.read().splitlines()
    for i, raw in enumerate(raw_lines):
        if not raw.strip():
            continue
        try:
            lines.append((raw, json.loads(raw)))
        except json.JSONDecodeError as exc:
            lines.append((raw, {"__json_error__": str(exc)}))
    if not lines:
        print("REFUS : au moins une ligne par bloc (observation ou abstention)")
        return 2
    catalog = by_key()
    if content_key not in catalog:
        print(f"REFUS : clé de contenu inconnue {content_key}")
        return 2
    # G2 (D-0078, D-0087) : une ligne qui nomme une personne physique ne s'écrit nulle part, pas même parmi les rejets,
    # dont la ligne brute va aux exclusions ; --final n'y change rien
    persons = [(i, guards.person_mentions(obj)) for i, (_, obj) in enumerate(lines) if isinstance(obj, dict)]
    persons = [(i, m) for i, m in persons if m]
    if persons:
        print("REFUS : personne physique nommée (D-0078) — écrire la fonction, réduire la citation à un passage sans nom ; "
              "une société prise à tort s'ajoute à guards.ALLOWED. Rien n'est écrit, même avec --final :")
        for i, m in persons:
            print(f"  ligne {i + 1}: " + " ; ".join(f"{f} « {x} »" for f, x in m))
        return 2
    errs, alerts = [], []
    from .load import semantic_errors
    for i, (raw, obj) in enumerate(lines):
        e = [obj["__json_error__"]] if "__json_error__" in obj else schema_errors(obj)
        if not e and not final:
            e = ["sémantique : " + x for x in semantic_errors(obj, catalog[content_key])[0]]
        if e:
            errs.append((i, raw, e))
        elif not final and not confirm:
            a = guards.amount_alerts(obj)              # G3 : montant contre citation
            if a:
                alerts.append((i, a))
    if (errs or alerts) and not final:
        if errs:
            print("ERREURS DE SCHÉMA OU DE SÉMANTIQUE (reprendre une fois les lignes refusées, puis --final) :")
            for i, _, e in errs:
                print(f"  ligne {i + 1}: " + " ; ".join(e))
        if alerts:
            print("ALERTES DE LECTURE (corriger la ligne, ou confirmer par --confirm) :")
            for i, a in alerts:
                print(f"  ligne {i + 1}: " + " ; ".join(a))
        return 1
    run = _run_info()
    good = [obj for i, (raw, obj) in enumerate(lines) if i not in {x[0] for x in errs}]
    p = obs_path(content_key)
    p.parent.mkdir(parents=True, exist_ok=True)
    # G4 : une ligne déjà écrite dans cette passe, ou répétée dans la soumission, ne s'écrit pas deux fois
    seen = set()
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                if (d.get("as_of"), d.get("pass_id")) == (run["as_of"], run["pass_id"]):
                    seen.add(json.dumps(d, ensure_ascii=False, sort_keys=True))
    new = []
    for obj in good:
        s = _stored(run, dict(obj))
        if s not in seen:
            seen.add(s)
            new.append(s)
    with open(p, "a", encoding="utf-8") as fh:
        for s in new:
            fh.write(s + "\n")
    if errs:
        with open(rejected_path(content_key), "a", encoding="utf-8") as fh:
            for i, raw, e in errs:
                fh.write(json.dumps({"as_of": run["as_of"], "pass_id": run["pass_id"],
                                     "raw": raw, "errors": e}, ensure_ascii=False) + "\n")
    if not good:
        p.touch()
    sp = _state_path()
    if sp.exists():
        st = json.loads(sp.read_text())
        if st.get("content_key") == content_key:
            sp.unlink()
    dup = len(good) - len(new)
    print(f"ÉCRIT : {len(new)} ligne(s) valides, {len(errs)} rejetée(s) — {p.name}"
          + (f" ; {dup} ligne(s) déjà écrite(s) dans cette passe, ignorée(s)" if dup else ""))
    return 0


def cmd_check():
    """Gardes de lecture sur les lignes de l'as_of courant (D-0087), avant le réassemblage : passe chargée de chaque
    bloc, ou des seuls blocs d'une liste. Erreurs : prix d'un financement sous la famille `financing` (G1), personne
    physique nommée (G2), ligne en double dans la passe (G4). Alertes : montant qui ne se lit pas dans sa citation
    (G3). Sans catalogue : seuls les fichiers d'observations sont lus. Renvoie 1 s'il reste une erreur."""
    as_of = config.as_of()
    if LIST:
        paths = [obs_path(k.strip()) for k in pathlib.Path(LIST).read_text(encoding="utf-8").splitlines() if k.strip()]
    else:
        paths = sorted(p for p in config.OBS_DIR.glob("*.jsonl") if not p.name.endswith(".rejected.jsonl"))
    blocks = n = n_err = n_alert = 0
    for p in paths:
        if not p.exists():
            continue
        lines = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not lines:
            continue
        last = max((l.get("as_of"), l.get("pass_id")) for l in lines)
        if last[0] != as_of:
            continue
        blocks += 1
        seen = set()
        for i, l in enumerate(x for x in lines if (x.get("as_of"), x.get("pass_id")) == last):
            n += 1
            errs = guards.flow_errors(l) + [f"{f} nomme une personne physique (« {x} », D-0078)"
                                            for f, x in guards.person_mentions(l)]
            s = json.dumps(l, ensure_ascii=False, sort_keys=True)
            if s in seen:
                errs.append("ligne en double dans la passe")
            seen.add(s)
            alerts = guards.amount_alerts(l)
            for kind, msgs in (("ERREUR", errs), ("ALERTE", alerts)):
                for m in msgs:
                    print(f"{kind} {p.stem[:12]} ligne {i + 1} : {m}")
            n_err += len(errs)
            n_alert += len(alerts)
    print(f"contrôlé : {n} ligne(s) de l'as_of {as_of} dans {blocks} bloc(s) ; {n_err} erreur(s), {n_alert} alerte(s)")
    return 1 if n_err else 0


_PASS_ID = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def cmd_open_pass(pass_id=None):
    """Ouvre la passe de lecture de l'exécution (work/tmp/run.json) ou, avec --list, celle d'une liste de relecture
    (work/tmp/run_<liste>.json) : l'as_of de config.yaml et un identifiant AAAA-MM-JJTHH:MM:SSZ, l'heure UTC par
    défaut. Sans passe ouverte, chaque soumission prendrait l'heure du moment, et un bloc rendu en plusieurs morceaux
    ne chargerait que le dernier. Une passe ouverte au même as_of se garde ; celle d'un autre as_of est remplacée
    (D-0087). Une passe de correction s'inscrit aussi dans reading.correction_passes de config.yaml (D-0078)."""
    if pass_id is not None and not _PASS_ID.match(pass_id):
        print(f"REFUS : identifiant de passe attendu sous la forme AAAA-MM-JJTHH:MM:SSZ, pas {pass_id!r}")
        return 2
    as_of = config.as_of()
    p = _list_run_path() if LIST else RUN
    if p.exists():
        cur = json.loads(p.read_text())
        if cur.get("as_of") == as_of:
            if pass_id in (None, cur.get("pass_id")):
                print(f"passe déjà ouverte : {cur.get('pass_id')} (as_of {as_of}) — work/tmp/{p.name}")
                return 0
            print(f"REFUS : la passe {cur.get('pass_id')} est ouverte au même as_of ({as_of}) dans work/tmp/{p.name} ; "
                  "retirer ce fichier pour en ouvrir une autre")
            return 2
    pid = pass_id or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"as_of": as_of, "pass_id": pid}), encoding="utf-8")
    print(f"passe ouverte : {pid} (as_of {as_of}) — work/tmp/{p.name}")
    return 0


def cmd_status():
    cat = load_catalog()
    q = queue(cat)
    done = sum(1 for k in by_key(cat) if obs_path(k).exists())
    by = {}
    for b in q:
        by.setdefault(b["block_kind"], [0, 0])
        by[b["block_kind"]][0] += 1
        by[b["block_kind"]][1] += len(b["text"])
    print(f"catalogue : {len(cat)} blocs ; lus : {done} ; file : {len(q)}")
    for k, (n, c) in sorted(by.items()):
        print(f"  {k:22s} {n:5d} blocs  {c:>10,d} caractères")


def cmd_show(content_key):
    cat = by_key()
    b = cat[content_key]
    header, facts, chunks = render_block(b, 10**9)
    print(header)
    print(facts)
    print(chunks[0])


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    st_ = sub.add_parser("status")
    n = sub.add_parser("next")
    n.add_argument("--max-chars", type=int)
    s = sub.add_parser("submit")
    s.add_argument("content_key")
    s.add_argument("path")
    s.add_argument("--final", action="store_true")
    s.add_argument("--next", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("content_key")
    lt = sub.add_parser("lot")
    lt.add_argument("--small", type=int, default=4000)
    lt.add_argument("--total", type=int, default=20000)
    sl = sub.add_parser("submit-lot")
    sl.add_argument("path")
    sl.add_argument("--final", action="store_true")
    sl.add_argument("--then", choices=["lot", "next", "auto"])
    sl.add_argument("--small", type=int, default=5000)
    sl.add_argument("--total", type=int, default=22000)
    ck = sub.add_parser("check")
    op = sub.add_parser("open-pass")
    op.add_argument("--id", dest="pass_id")
    for sp_ in (s, sl):
        sp_.add_argument("--confirm", action="store_true")      # alertes de lecture vues et confirmées (D-0087)
    for sp_ in (st_, n, s, lt, sl, ck, op):
        sp_.add_argument("--list")
    a = ap.parse_args(argv)
    global LIST
    LIST = getattr(a, "list", None)
    if a.cmd == "status":
        return cmd_status()
    if a.cmd == "next":
        return cmd_next(a.max_chars)
    if a.cmd == "submit":
        rc = cmd_submit(a.content_key, a.path, a.final, a.confirm)
        if rc == 0 and a.next:
            cmd_next(None)
        return rc
    if a.cmd == "show":
        return cmd_show(a.content_key)
    if a.cmd == "lot":
        return cmd_lot(a.small, a.total)
    if a.cmd == "submit-lot":
        rc = cmd_submit_lot(a.path, a.final, a.confirm)
        if rc == 0 and a.then == "lot":
            cmd_lot(a.small, a.total)
        elif rc == 0 and a.then == "next":
            cmd_next(None)
        elif rc == 0 and a.then == "auto":
            cmd_auto(a.small, a.total)
        return rc
    if a.cmd == "check":
        return cmd_check()
    if a.cmd == "open-pass":
        return cmd_open_pass(a.pass_id)


if __name__ == "__main__":
    sys.exit(main() or 0)
