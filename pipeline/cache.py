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


def latest_api(cik, resource):
    """Dernier tirage horodaté d'une ressource d'API (nom de fichier = date)."""
    d = config.CACHE / "api" / cik / resource
    if not d.exists():
        return None
    files = sorted(d.glob("*.json.zst"))
    return files[-1] if files else None
