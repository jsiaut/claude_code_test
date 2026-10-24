"""Cache disque (§9.6). Archives immuables ; ressources d'API horodatées par as_of."""
import hashlib
import pathlib

import threading

import zstandard as zstd

from . import config

# Les objets zstd ne sont pas sûrs entre fils d'exécution : un par fil.
_tls = threading.local()


def _c():
    if not hasattr(_tls, "c"):
        _tls.c = zstd.ZstdCompressor(level=10)
    return _tls.c


def _d():
    if not hasattr(_tls, "d"):
        _tls.d = zstd.ZstdDecompressor()
    return _tls.d


def archive_path(cik, accession, document):
    return config.CACHE / "archives" / cik / accession / (document + ".zst")


def api_path(cik, resource, date):
    return config.CACHE / "api" / cik / resource / f"{date}.json.zst"


def other_path(*parts):
    return config.CACHE.joinpath(*parts)


def write(path: pathlib.Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{threading.get_ident()}.tmp")
    tmp.write_bytes(_c().compress(data))
    tmp.replace(path)


def read(path: pathlib.Path) -> bytes:
    return _d().decompress(path.read_bytes(), max_output_size=2**31)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dated_path(parts, stem, ext, date):
    """Version d'une ressource vivante hors de l'API (page d'un jeu de données, liste des noms d'EDGAR), datée de
    l'as_of de l'exécution qui l'a tirée : {stem}_{date}{ext}.zst (D-0074)."""
    return config.CACHE.joinpath(*parts) / f"{stem}_{date}{ext}.zst"


def dated(parts, stem, ext, date, legacy=None):
    """Version servie à l'as_of `date` : la plus récente des versions datées au plus de lui ; à défaut, `legacy` (ancien
    nom fixe) s'il existe, puis la plus ancienne version datée, tirée après coup pour la première exécution ; None
    sinon (D-0074)."""
    d = config.CACHE.joinpath(*parts)
    files = sorted(d.glob(f"{stem}_????-??-??{ext}.zst")) if d.exists() else []
    n = len(stem) + 1
    upto = [f for f in files if f.name[n:n + 10] <= str(date)]
    if upto:
        return upto[-1]
    if legacy is not None and legacy.exists():
        return legacy
    return files[0] if files else None


def latest_api(cik, resource):
    """Dernier tirage horodaté d'une ressource d'API (nom de fichier = date)."""
    d = config.CACHE / "api" / cik / resource
    if not d.exists():
        return None
    files = sorted(d.glob("*.json.zst"))
    return files[-1] if files else None
