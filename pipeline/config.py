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
AS_OF_TOKEN = "as_of"        # borne de config.yaml qui finit à l'as_of de l'exécution (D-0073)


def _checked_as_of(v):
    """La clé as_of de config.yaml : une date AAAA-MM-JJ, seule source de l'as_of (D-0073)."""
    import datetime as dt
    if isinstance(v, dt.date):
        v = v.isoformat()
    try:
        dt.date.fromisoformat(v)
    except (TypeError, ValueError):
        raise SystemExit(f"config.yaml : la clé as_of doit être une date AAAA-MM-JJ, pas {v!r} (D-0073)") from None
    return v


def resolve_as_of(node, as_of):
    """Remplace par la date chaque valeur égale à « as_of » : une borne qui finit à l'as_of de l'exécution (D-0073).
    Les clés ne changent pas."""
    if isinstance(node, dict):
        return {k: resolve_as_of(v, as_of) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve_as_of(v, as_of) for v in node]
    return as_of if node == AS_OF_TOKEN else node


def _parsed():
    st = CONFIG_PATH.stat()
    key = (str(CONFIG_PATH), st.st_size, st.st_mtime_ns)
    if _PARSED.get("key") != key:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        a = _checked_as_of(raw.get("as_of"))
        prev = _checked_previous(raw.get("as_of_previous"), a)
        _PARSED.update(key=key, cfg=resolve_as_of(dict(raw, as_of=a, as_of_previous=prev), a))
    return _PARSED["cfg"]


def _checked_previous(v, a):
    """La clé as_of_previous : les as_of des exécutions précédentes, dates croissantes antérieures à l'as_of (D-0074)."""
    out = [_checked_as_of(x) for x in (v or [])]
    if out != sorted(set(out)) or (out and out[-1] >= a):
        raise SystemExit(f"config.yaml : as_of_previous doit lister des dates croissantes antérieures à l'as_of {a}, "
                         f"pas {v!r} (D-0074)")
    return out


def load():
    """config.yaml analysé une fois par version du fichier (chemin, taille, date de modification), bornes « as_of »
    remplacées par la date ; chaque appel reçoit sa propre copie, qu'il peut modifier sans toucher aux suivants."""
    return copy.deepcopy(_parsed())


def as_of(cli=None):
    """As_of de l'exécution : la clé as_of de config.yaml, seule source (D-0073). Un argument de ligne de commande est
    accepté s'il lui est égal ; sinon la commande s'arrête, plutôt que de mêler deux dates de coupure."""
    v = _parsed()["as_of"]
    if cli is not None and str(cli) != v:
        raise SystemExit(f"as_of {cli} en argument, {v} dans config.yaml : l'as_of n'a qu'une source, la clé as_of de "
                         "config.yaml (D-0073). Changer la clé, ou retirer l'argument.")
    return v


def previous_as_of():
    """As_of de l'exécution précédente (le dernier de as_of_previous), None à la première exécution (D-0074)."""
    prev = _parsed()["as_of_previous"]
    return prev[-1] if prev else None


def search_windows(start, end=None):
    """Fenêtres d'une recherche plein texte de `start` à `end` (l'as_of par défaut), coupées aux as_of des exécutions
    précédentes : chaque fenêtre se tire une fois, à l'exécution qui la clôt, puis se rejoue du cache (D-0074)."""
    import datetime as dt
    end = end or as_of()
    out, a = [], str(start)
    for c in _parsed()["as_of_previous"]:
        if a <= c < end:
            out.append((a, c))
            a = (dt.date.fromisoformat(c) + dt.timedelta(days=1)).isoformat()
    if a <= end:
        out.append((a, end))
    return out


def check_as_of(found, where, remedy):
    """Arrête la commande si `where` (un fichier d'une étape antérieure) porte un autre as_of que config.yaml : une
    exécution n'en mêle jamais deux (D-0073, point 4)."""
    v = as_of()
    if found != v:
        raise SystemExit(f"{where} porte l'as_of {found}, config.yaml {v} : {remedy} (D-0073).")
    return v


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
