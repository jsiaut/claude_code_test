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
    if not CATALOG.exists():
        return []
    with open(CATALOG, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def obs_path(content_key):
    return config.OBS_DIR / f"{content_key}.jsonl"


def rejected_path(content_key):
    return config.OBS_DIR / f"{content_key}.rejected.jsonl"


def queue(catalog=None):
    """Blocs sans fichier d'observations, dans l'ordre du signal (§11.1)."""
    catalog = catalog if catalog is not None else load_catalog()
    seen, out = set(), []
    for b in sorted(catalog, key=lambda b: (b["signal_class"], b["sort_key"])):
        ck = b["content_key"]
        if ck in seen or obs_path(ck).exists():
            continue
        if b.get("requires") and not _requirement_met(b["requires"]):
            continue
        seen.add(ck)
        out.append(b)
    return out


def _requirement_met(req):
    """Un corps de pièce n'entre dans la file qu'après lecture de son en-tête (§11.1)."""
    from .exhibits import body_required
    return body_required(req)


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


def render_block(b, cap):
    head = {k: b.get(k) for k in ("content_key", "block_kind", "group_id", "cik", "accession",
                                  "form", "filing_date", "item", "exhibit_type", "document",
                                  "note_label", "period_start", "period_end", "knowledge_date")}
    cands = b.get("candidate_facts") or []
    cand_lines = [f"  {c['fact_key']} | {c['concept']} | {c['value']} {c.get('unit') or ''} | "
                  f"{c.get('period_start') or ''}..{c.get('period_end')} | {c.get('dims') or '[]'}"
                  for c in cands]
    header = "### BLOC " + json.dumps(head, ensure_ascii=False)
    facts = "### FAITS CANDIDATS (" + str(len(cands)) + ")\n" + "\n".join(cand_lines)
    budget = max(cap - len(header) - len(facts) - 200, 4000)
    return header, facts, _chunks(b["text"], budget)


def cmd_next(max_chars):
    cap = max_chars or config.load()["reading"]["max_read_chars"]
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
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
    STATE.write_text(json.dumps(state))


def _run_info():
    if RUN.exists():
        return json.loads(RUN.read_text())
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
    for i, (raw, obj) in enumerate(lines):
        e = [obj["__json_error__"]] if "__json_error__" in obj else schema_errors(obj)
        if e:
            errs.append((i, raw, e))
    if errs and not final:
        print("ERREURS DE SCHÉMA (reprendre une fois les lignes refusées, puis --final) :")
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
    if STATE.exists():
        st = json.loads(STATE.read_text())
        if st.get("content_key") == content_key:
            STATE.unlink()
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
    a = ap.parse_args(argv)
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


if __name__ == "__main__":
    sys.exit(main() or 0)
