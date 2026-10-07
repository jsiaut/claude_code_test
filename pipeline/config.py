"""Chargement de config.yaml et constantes de chemin (§0, §9.6)."""
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
DELIMITER_VERSION = "d2"


def load():
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


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
