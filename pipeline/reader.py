"""File de lecture et validation des observations (§7.4).

Le code sert les blocs naturels dans l'ordre du signal, jusqu'au plafond de lecture ;
l'exécutant rend les lignes d'un bloc d'un coup, une fois le bloc lu, au moins une par
bloc (observation ou abstention). Le code renvoie aussitôt les erreurs de schéma ;
l'exécutant reprend une fois ; puis le code écrit le fichier du bloc avec les lignes qui
passent, même s'il n'y en a aucune. Les rejets au schéma se gardent à côté.
La validation sémantique se fait au chargement dans `observations` (load.py).

Usage :
  python -m pipeline.reader status
  python -m pipeline.reader next [--max-chars N]
  python -m pipeline.reader submit CONTENT_KEY FICHIER.jsonl [--final] [--next]
  python -m pipeline.reader show CONTENT_KEY
"""
import argparse
import datetime as dt
import json
import re
import sys
from decimal import Decimal, InvalidOperation

from . import config
from .lock import touch_lock
from .registry import ENUMS

CATALOG = config.DB_DIR / "blocks.jsonl"          # recalculé à chaque exécution
CATALOG_EXT = config.DB_DIR / "text_blocks_ext.jsonl"   # bloc `text` de §14, s'il est ouvert
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
    return out


def obs_path(content_key):
    return config.OBS_DIR / f"{content_key}.jsonl"


def rejected_path(content_key):
    return config.OBS_DIR / f"{content_key}.rejected.jsonl"


LIST = None        # fichier de clés de contenu : file de lecture restreinte, dans son ordre


def _state_path():
    if LIST:
        return STATE.parent / f"reading_state_{__import__('pathlib').Path(LIST).stem}.json"
    return STATE


def _run_path():
    """Une liste de relecture a sa propre passe (work/tmp/run_<liste>.json) : ses blocs se
    relisent même s'ils ont déjà des lignes, et la passe la plus récente remplace l'ancienne
    au chargement (§7.4)."""
    if LIST:
        p = RUN.parent / f"run_{__import__('pathlib').Path(LIST).stem}.json"
        if p.exists():
            return p
    return RUN


def _read_in_pass(ck, pass_id):
    """Le bloc a reçu des lignes (valides ou rejetées) dans cette passe."""
    for p in (obs_path(ck), rejected_path(ck)):
        if p.exists() and any(json.loads(l).get("pass_id") == pass_id
                              for l in p.read_text(encoding="utf-8").splitlines() if l.strip()):
            return True
    return False


def queue(catalog=None):
    """Blocs sans fichier d'observations, dans l'ordre du signal (§11.1) ; avec une liste,
    seulement ses blocs, dans l'ordre de la liste."""
    catalog = catalog if catalog is not None else load_catalog()
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
        if b.get("requires") and not _requirement_met(b["requires"]):
            continue
        seen.add(ck)
        out.append(b)
    return out


def _text_scope():
    sc = config.load().get("scope")
    return isinstance(sc, list) and "text" in sc


def _requirement_met(req):
    """Un corps de pièce n'entre dans la file qu'après lecture de son en-tête (§11.1) ; arrêté
    à l'en-tête au premier passage (établissements financiers seulement), il y entre quand le
    bloc `text` de §14 est ouvert, après les notes et les items de 8-K."""
    from .exhibits import decide
    want, _ = decide(req)
    if want is None:
        return False
    return bool(want) or _text_scope()


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
                                  "note_label", "period_start", "period_end", "knowledge_date")}
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


def cmd_submit_lot(path, final=False):
    """Lignes de plusieurs blocs : champ `block` = clé de contenu ; écrites bloc par bloc."""
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
    tmp = STATE.parent / "lot_part.jsonl"
    for ck in order:
        tmp.write_text("\n".join(groups[ck]) + "\n", encoding="utf-8")
        r = cmd_submit(ck, str(tmp), final)
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
    if _run_path().exists():
        return json.loads(_run_path().read_text())
    now = dt.datetime.now(dt.timezone.utc)
    return {"as_of": now.date().isoformat(), "pass_id": now.isoformat(timespec="seconds")}


def cmd_submit(content_key, path, final=False):
    lines = []
    raw_lines = open(path, encoding="utf-8").read().splitlines() if path != "-" else sys.stdin.read().splitlines()
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
    catalog = {b["content_key"]: b for b in load_catalog()}
    if content_key not in catalog:
        print(f"REFUS : clé de contenu inconnue {content_key}")
        return 2
    errs = []
    from .load import semantic_errors
    for i, (raw, obj) in enumerate(lines):
        e = [obj["__json_error__"]] if "__json_error__" in obj else schema_errors(obj)
        if not e and not final:
            e = ["sémantique : " + x for x in semantic_errors(obj, catalog[content_key])[0]]
        if e:
            errs.append((i, raw, e))
    if errs and not final:
        print("ERREURS DE SCHÉMA OU DE SÉMANTIQUE (reprendre une fois les lignes refusées, puis --final) :")
        for i, _, e in errs:
            print(f"  ligne {i + 1}: " + " ; ".join(e))
        return 1
    run = _run_info()
    good = [obj for i, (raw, obj) in enumerate(lines) if i not in {x[0] for x in errs}]
    p = obs_path(content_key)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        for obj in good:
            obj = dict(obj)
            fh.write(json.dumps({"as_of": run["as_of"], "pass_id": run["pass_id"], **obj},
                                ensure_ascii=False, sort_keys=True) + "\n")
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
    touch_lock()
    print(f"ÉCRIT : {len(good)} ligne(s) valides, {len(errs)} rejetée(s) — {p.name}")
    return 0


def cmd_status():
    cat = load_catalog()
    q = queue(cat)
    done = sum(1 for b in {b["content_key"]: b for b in cat}.values() if obs_path(b["content_key"]).exists())
    by = {}
    for b in q:
        by.setdefault(b["block_kind"], [0, 0])
        by[b["block_kind"]][0] += 1
        by[b["block_kind"]][1] += len(b["text"])
    print(f"catalogue : {len(cat)} blocs ; lus : {done} ; file : {len(q)}")
    for k, (n, c) in sorted(by.items()):
        print(f"  {k:22s} {n:5d} blocs  {c:>10,d} caractères")


def cmd_show(content_key):
    cat = {b["content_key"]: b for b in load_catalog()}
    b = cat[content_key]
    header, facts, chunks = render_block(b, 10**9)
    print(header)
    print(facts)
    print(chunks[0])


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
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
    for sp_ in (n, s, lt, sl):
        sp_.add_argument("--list")
    st_ = sub.choices["status"]
    st_.add_argument("--list")
    a = ap.parse_args(argv)
    global LIST
    LIST = getattr(a, "list", None)
    if a.cmd == "status":
        return cmd_status()
    if a.cmd == "next":
        return cmd_next(a.max_chars)
    if a.cmd == "submit":
        rc = cmd_submit(a.content_key, a.path, a.final)
        if rc == 0 and a.next:
            cmd_next(None)
        return rc
    if a.cmd == "show":
        return cmd_show(a.content_key)
    if a.cmd == "lot":
        return cmd_lot(a.small, a.total)
    if a.cmd == "submit-lot":
        rc = cmd_submit_lot(a.path, a.final)
        if rc == 0 and a.then == "lot":
            cmd_lot(a.small, a.total)
        elif rc == 0 and a.then == "next":
            cmd_next(None)
        elif rc == 0 and a.then == "auto":
            cmd_auto(a.small, a.total)
        return rc


if __name__ == "__main__":
    sys.exit(main() or 0)
