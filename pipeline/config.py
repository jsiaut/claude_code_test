"""Chargement de config.yaml et constantes de chemin (§0, §9.6)."""
import copy
import os
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"
CACHE = ROOT / "cache"
WORK = ROOT / "work"
OBS_DIR = WORK / "observations"
TABLES = ROOT / "tables"
AUDIT = ROOT / "audit"
DB_DIR = ROOT / "db"
JOURNAL = ROOT / "journal.jsonl"
LOCK = WORK / "session.lock"

# Versions qui entrent dans les clés de cache (§9.2, §9.6).
NORMALIZER_VERSION = "n1"
DELIMITER_VERSION = "d4"


_PARSED = {}


def load():
    """config.yaml analysé une fois par version du fichier (chemin, taille, date de modification) ;
    chaque appel reçoit sa propre copie, qu'il peut modifier sans toucher aux suivants."""
    st = CONFIG_PATH.stat()
    key = (str(CONFIG_PATH), st.st_size, st.st_mtime_ns)
    if _PARSED.get("key") != key:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            _PARSED.update(key=key, cfg=yaml.safe_load(fh))
    return copy.deepcopy(_PARSED["cfg"])


def duckdb_connect(path=None):
    """Connexion DuckDB aux réglages explicites de config.yaml (D-0072, point 3 d) : nombre de fils et mémoire. L'ordre
    d'insertion reste préservé, comme par défaut : des requêtes intermédiaires sans ORDER BY en dépendent."""
    import duckdb
    con = duckdb.connect() if path is None else duckdb.connect(str(path))
    d = load().get("duckdb") or {}
    if d.get("threads"):
        con.execute(f"SET threads = {int(d['threads'])}")
    if d.get("memory_limit"):
        con.execute(f"SET memory_limit = '{d['memory_limit']}'")
    return con


def user_agent(cfg=None):
    """Valeur exacte du User-Agent fourni par l'utilisateur (§9.5), jamais inventée."""
    cfg = cfg or load()
    for src in cfg["user_agent"]["value_sources"]:
        kind, _, ref = src.partition(":")
        if kind == "env" and os.environ.get(ref):
            return os.environ[ref].strip()
        if kind == "file":
            p = ROOT / ref
            if p.exists() and p.read_text(encoding="utf-8").strip():
                return p.read_text(encoding="utf-8").strip()
    raise SystemExit("User-Agent absent : l'utilisateur doit le fournir (config.yaml, §9.5).")


def mask_contact(text, cfg=None):
    """Masque l'adresse de contact dans toute copie partagée (§9.5)."""
    try:
        ua = user_agent(cfg)
    except SystemExit:
        return text
    parts = ua.split()
    for p in parts:
        if "@" in p:
            text = text.replace(p, "<adresse masquée>")
    return text
