"""État versionné (D-0091, point 3) : ce qui dépend de l'historique d'exécution sans porter de texte de dépôt.

Un conteneur neuf n'a ni `db/` ni `cache/`. La reconstruction retire les documents de la SEC et recalcule les catalogues,
mais quatre choses ne se recalculent pas à l'identique, ou ne se recalculent pas du tout :

- deux fichiers de `db/` qu'aucun programme n'écrit (`HAND`) ;
- l'ordre et le choix des blocs des catalogues préparés, qui dépendent de ce qui était lu à chaque exécution : un
  manifeste par catalogue, sans texte (`MANIFEST_FIELDS`) ;
- les listes des montages (pièces sans fenêtre, fenêtres au-delà du plafond, déjà lues…) ;
- les files et les candidats de la découverte et de la piste, avec leurs rangs et leurs états, et le registre de
  leurs unités préparées (`BUILT`).

Le manifeste porte l'attribution d'un bloc, le recalcul en rend le texte (point 12) : un texte que le recalcul ne rend
que d'un autre dépôt reprend du manifeste son dépôt, son document et ses dates.

    python3 -m pipeline.state save      # db/ -> state/, après un assemblage ; se commite avec les tables
    python3 -m pipeline.state check     # state/ décrit-il db/ ? (code de retour 1 sinon)
    python3 -m pipeline.state restore   # state/ -> db/ : les deux fichiers faits à la main
    python3 -m pipeline.state status

`state/` ne porte ni texte de bloc ni titre de note ou de pièce : les catalogues gardent le texte des dépôts tel quel,
noms de personnes compris, que le dépôt tient hors de ses lignes (D-0078). Le texte se recalcule des documents.
"""
import base64
import json
import sys

import pyarrow as pa
import pyarrow.parquet as pq

from . import config

STATE = config.ROOT / "state"
HAND = ("exhibits_tranche.json", "usgaap2026_balance.json")
CATALOGS = {"montages": "montages_blocks.jsonl", "foreign_6k": "foreign_6k_blocks.jsonl", "sb": "sb_blocks.jsonl",
            "discovery": "discovery_blocks.jsonl", "nf_discovery": "nf_discovery_blocks.jsonl"}
# champs d'un manifeste : de quoi retrouver le bloc, sa place et son attribution, rien de son texte. Les onze premiers
# sont ceux du premier état commité ; les suivants tiennent au dépôt du bloc et à sa file (point 12)
MANIFEST_FIELDS_V1 = ("content_key", "block_kind", "accession", "document", "exhibit_type", "montage", "window", "sort_key",
                      "chars", "filing_date", "group_id")
MANIFEST_FIELDS = MANIFEST_FIELDS_V1 + ("cik", "form", "acceptance", "knowledge_date", "period_start", "period_end",
                                        "filing_status", "assurance_level", "tier", "locator", "unit_order", "nf_queue")
LOCATOR_FIELDS = ("file", "accession", "cik", "byte_range")      # pas `section`, un titre du dépôt
QUEUES = ("discovery_units.parquet", "discovery_candidates.parquet", "nf_discovery_units.parquet",
          "nf_discovery_own_units.parquet", "nf_discovery_candidates.parquet")
LISTS_GLOB = "montages_info*.json"
# registres des unités préparées de la découverte et de la piste, et leurs champs : aucun ne porte de texte de dépôt
BUILT = ("discovery_built.jsonl", "nf_discovery_built.jsonl")
BUILT_FIELDS = ("order", "rank", "cik", "kind", "adsh", "doc", "content_key", "error", "selected_by", "queue", "rule",
                "own_filing")


def _clean(v):
    """Valeur d'un champ de manifeste : un flottant manquant (NaN d'un type de pièce absent) s'écrit null."""
    return None if isinstance(v, float) and v != v else v


def _field(b, k):
    """Champ `k` du bloc pour son manifeste ; d'une localisation ne se gardent que LOCATOR_FIELDS."""
    v = _clean(b.get(k))
    if k == "locator" and isinstance(v, dict):
        return {f: _clean(v.get(f)) for f in LOCATOR_FIELDS if f in v}
    return v


def manifest_rows(path):
    """Manifeste d'un catalogue : une ligne par bloc, dans l'ordre du catalogue, limitée à MANIFEST_FIELDS."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                b = json.loads(line)
                out.append({k: v for k, v in ((k, _field(b, k)) for k in MANIFEST_FIELDS) if v is not None})
    return out


def built_text(path):
    """Registre des unités préparées, ligne à ligne, dans son ordre. Un champ hors de la liste fermée arrête
    l'écriture : il s'ajoute à BUILT_FIELDS une fois vérifié qu'il ne porte pas de texte de dépôt."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                unknown = sorted(set(r) - set(BUILT_FIELDS))
                if unknown:
                    raise ValueError(f"{path.name} : champ hors de la liste fermée de l'état : {', '.join(unknown)}")
                out.append(json.dumps(r, ensure_ascii=False) + "\n")
    return "".join(out)


def _dump_rows(rows):
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)


def table_text(path):
    """Table Parquet en texte, sans perte : le schéma Arrow (avec les types de pandas) en première ligne, puis une
    ligne JSON par ligne de la table. Git ne garde alors d'une version à l'autre que les lignes changées."""
    t = pq.read_table(path)
    head = {"arrow_schema": base64.b64encode(t.schema.serialize().to_pybytes()).decode("ascii"),
            "columns": t.schema.names, "rows": t.num_rows}
    return json.dumps(head) + "\n" + "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in t.to_pylist())


def text_table(text):
    """Table Arrow d'un texte écrit par `table_text` : mêmes colonnes, mêmes types, mêmes valeurs, même ordre."""
    lines = text.split("\n")
    head = json.loads(lines[0])
    schema = pa.ipc.read_schema(pa.py_buffer(base64.b64decode(head["arrow_schema"])))
    rows = [json.loads(x) for x in lines[1:] if x]
    if len(rows) != head["rows"]:
        raise ValueError(f"table tronquée : {len(rows)} lignes pour {head['rows']} annoncées")
    return pa.Table.from_pylist(rows, schema=schema)


def lists_paths(db=None):
    """Listes des montages de l'exécution courante (pas les copies datées de l'exécution précédente)."""
    db = db or config.DB_DIR
    return [p for p in sorted(db.glob(LISTS_GLOB)) if len(p.name.split(".")) == 2]


def files(db=None):
    """Contenu attendu de state/ pour ce db/ : chemin relatif -> texte."""
    db = db or config.DB_DIR
    out = {}
    for name in HAND:
        if (db / name).exists():
            out[f"hand/{name}"] = (db / name).read_text(encoding="utf-8")
    for key, name in CATALOGS.items():
        if (db / name).exists():
            out[f"catalogs/{key}.jsonl"] = _dump_rows(manifest_rows(db / name))
    for p in lists_paths(db):
        out[f"lists/{p.name}"] = p.read_text(encoding="utf-8")
    for name in QUEUES:
        if (db / name).exists():
            out[f"queues/{name[:-len('.parquet')]}.jsonl"] = table_text(db / name)
    for name in BUILT:
        if (db / name).exists():
            out[f"built/{name}"] = built_text(db / name)
    out["STATE.json"] = json.dumps({"as_of": config.as_of(), "files": sorted(out), "manifest_fields": list(MANIFEST_FIELDS)},
                                   ensure_ascii=False, indent=1) + "\n"
    return out


def save(db=None, state=None):
    """Écrit state/ depuis db/ ; retire ce qui n'en fait plus partie. Renvoie les chemins écrits ou retirés."""
    state = state or STATE
    want = files(db)
    changed = []
    for rel, text in want.items():
        p = state / rel
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            changed.append(rel)
    for p in sorted(state.rglob("*")) if state.exists() else []:
        if p.is_file() and p.relative_to(state).as_posix() not in want:
            p.unlink()
            changed.append("-" + p.relative_to(state).as_posix())
    return changed


def check(db=None, state=None):
    """Écarts entre state/ et ce que db/ donnerait : chemins absents, en trop ou différents."""
    state = state or STATE
    want = files(db)
    have = {p.relative_to(state).as_posix() for p in state.rglob("*") if p.is_file()} if state.exists() else set()
    diff = sorted(set(want) - have) + sorted("-" + x for x in have - set(want))
    diff += sorted(rel for rel in set(want) & have if (state / rel).read_text(encoding="utf-8") != want[rel])
    return diff


def present(state=None):
    return ((state or STATE) / "STATE.json").exists()


def restore_hand(db=None, state=None):
    """Remet dans db/ les fichiers qu'aucun programme n'écrit. Renvoie leurs noms."""
    db, state = db or config.DB_DIR, state or STATE
    db.mkdir(parents=True, exist_ok=True)
    done = []
    for name in HAND:
        src = state / "hand" / name
        if src.exists():
            (db / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            done.append(name)
    return done


def restore_queue(name, db=None, state=None):
    """Remet une file ou une liste de candidats (rangs et états de l'exécution d'origine). Faux si l'état ne l'a pas."""
    db, state = db or config.DB_DIR, state or STATE
    src = state / "queues" / (name[:-len(".parquet")] + ".jsonl")
    if not src.exists():
        return False
    pq.write_table(text_table(src.read_text(encoding="utf-8")), db / name)
    return True


def restore_lists(db=None, state=None):
    """Remet les listes des montages. Renvoie leurs noms."""
    db, state = db or config.DB_DIR, state or STATE
    done = []
    for src in sorted((state / "lists").glob(LISTS_GLOB)) if (state / "lists").exists() else []:
        (db / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        done.append(src.name)
    return done


def restore_built(db=None, state=None):
    """Remet les registres des unités préparées, tels qu'à l'exécution d'origine. Renvoie leurs noms."""
    db, state = db or config.DB_DIR, state or STATE
    done = []
    for name in BUILT:
        src = state / "built" / name
        if src.exists():
            (db / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            done.append(name)
    return done


def manifest_fields(state=None):
    """Champs que les manifestes de cet état portent : un champ absent d'une ligne y était vide à l'origine. Le premier
    état commité ne les nommait pas : ce sont alors les onze premiers."""
    head = json.loads(((state or STATE) / "STATE.json").read_text(encoding="utf-8"))
    return tuple(head.get("manifest_fields") or MANIFEST_FIELDS_V1)


def manifests(state=None):
    """Manifestes versionnés : nom du fichier de catalogue de db/ -> lignes, dans l'ordre. Vide sans état."""
    state = state or STATE
    out = {}
    for key, name in CATALOGS.items():
        p = state / "catalogs" / f"{key}.jsonl"
        if p.exists():
            out[name] = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return out


def main(argv):
    cmd = argv[0] if argv else "status"
    if cmd == "save":
        ch = save()
        print(f"state/ : {len(ch)} fichier(s) écrit(s) ou retiré(s)" + (" : " + ", ".join(ch) if ch else ""))
    elif cmd == "check":
        d = check()
        print("state/ à jour" if not d else "state/ ne décrit pas db/ : " + ", ".join(d))
        return 1 if d else 0
    elif cmd == "restore":
        print("remis dans db/ :", ", ".join(restore_hand()) or "rien")
    elif cmd == "status":
        if not present():
            print("state/ absent")
            return 0
        head = json.loads((STATE / "STATE.json").read_text(encoding="utf-8"))
        size = sum(p.stat().st_size for p in STATE.rglob("*") if p.is_file())
        print(f"state/ : as_of {head['as_of']}, {len(head['files'])} fichiers, {size // 1024} Ko")
        for name, rows in manifests().items():
            print(f"  {name} : {len(rows)} blocs")
    else:
        raise SystemExit(f"commande inconnue : {cmd}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
