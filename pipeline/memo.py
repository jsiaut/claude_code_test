"""Mémo des étapes du réassemblage qui ne lisent pas les observations (D-0062).

Une étape mémorisée se reprend telle quelle quand rien de ce qu'elle peut lire n'a changé depuis
qu'elle a été calculée. L'empreinte des entrées couvre le code (pipeline/, sauf le rendu, et
schema.sql), les versions de Python et des bibliothèques, config.yaml, les fichiers de db/ (hors
la base de l'exécution et ce mémo), ceux de work/ hors observations et fichiers temporaires, et
l'arbre du cache. Seules les observations peuvent donc changer entre deux exécutions qui reprennent
une étape ; tout autre changement la recalcule. Une étape qui lit des faits ajoutés en cours
d'exécution (positions des BDC, Notes Data Sets des laboratoires) porte aussi leur empreinte.

Le mémo est un cache de calculs (§9.6) : le supprimer, ou lancer l'assemblage avec --sans-cache,
recalcule tout et donne les mêmes tables, à l'octet près.
"""
import hashlib
import json
import os
import pickle
import shutil
import sys

from . import config

MEMO = config.DB_DIR / "memo"
KEEP = 2                                   # entrées gardées par étape (la plus récente d'abord)
_SKIP_DB = {"model.duckdb", "model.duckdb.wal", "apercu.duckdb", "apercu.duckdb.wal", "memo"}
_SKIP_WORK = {"observations", "tmp"}       # et les fichiers posés à la racine de work/ (journaux, verrou)


def _tree(h, root, skip=frozenset(), top_files=True):
    """Chemin, taille et date de modification de chaque fichier sous root, dans un ordre fixe."""
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        if rel == ".":
            dirnames[:] = [d for d in dirnames if d not in skip]
            if not top_files:
                filenames = []
        dirnames.sort()
        for f in sorted(filenames):
            if rel == "." and f in skip:
                continue
            st = os.stat(os.path.join(dirpath, f))
            h.update(f"{os.path.join(rel, f)}\0{st.st_size}\0{st.st_mtime_ns}\n".encode("utf-8"))


def inputs_fingerprint():
    """Empreinte de tout ce qu'une étape mémorisée peut lire, observations exceptées."""
    h = hashlib.sha256()
    h.update(sys.version.encode("utf-8"))
    for mod in ("duckdb", "lxml", "numpy", "pandas", "pyarrow", "yaml", "zstandard"):
        try:
            h.update(f"{mod}={__import__(mod).__version__}\n".encode("utf-8"))
        except (ImportError, AttributeError):
            h.update(f"{mod}=absent\n".encode("utf-8"))
    for p in sorted((config.ROOT / "pipeline").glob("*.py")):
        if p.name != "render.py":
            h.update(p.name.encode("utf-8") + b"\0" + p.read_bytes())
    h.update((config.ROOT / "schema.sql").read_bytes())
    h.update(config.CONFIG_PATH.read_bytes())
    for name, root, skip, top in (("db", config.DB_DIR, _SKIP_DB, True), ("work", config.WORK, _SKIP_WORK, False),
                                  ("cache", config.CACHE, frozenset(), True)):
        h.update(f"[{name}]\n".encode("utf-8"))
        _tree(h, root, skip, top)
    return h.hexdigest()


def digest(obj):
    """Empreinte stable d'une valeur Python (listes de lignes, ensembles triés au préalable)."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()


class Memo:
    """Valeurs des étapes d'une exécution. use=False recalcule tout (les entrées sont réécrites)."""

    def __init__(self, fingerprint, use=True):
        self.fp, self.use = fingerprint, use
        self.hits, self.misses = [], []
        MEMO.mkdir(parents=True, exist_ok=True)

    def _path(self, name, key, ext):
        k = hashlib.sha256(f"{name}|{self.fp}|{key}".encode("utf-8")).hexdigest()[:32]
        return MEMO / f"{name}-{k}{ext}"

    def _prune(self, name, ext, keep_path):
        olds = sorted((p for p in MEMO.glob(f"{name}-*{ext}") if p != keep_path), key=lambda p: p.stat().st_mtime,
                      reverse=True)
        for p in olds[KEEP - 1:]:
            p.unlink(missing_ok=True)

    def value(self, name, compute, key=""):
        """Valeur de compute(), reprise du mémo quand l'étape y est déjà pour ces entrées."""
        p = self._path(name, key, ".pkl")
        if self.use and p.exists():
            try:
                with open(p, "rb") as fh:
                    v = pickle.load(fh)
                self.hits.append(name)
                return v
            except (OSError, EOFError, pickle.UnpicklingError):
                pass
        v = compute()
        tmp = p.with_name(p.name + ".tmp")
        with open(tmp, "wb") as fh:
            pickle.dump(v, fh, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(p)
        self._prune(name, ".pkl", p)
        self.misses.append(name)
        return v

    def database(self, name, db_path, build, key=""):
        """Base DuckDB construite par build() (qui renvoie (connexion, info)), reprise d'une copie du
        fichier quand l'étape est déjà dans le mémo pour ces entrées."""
        import duckdb
        p, info_p = self._path(name, key, ".duckdb"), self._path(name, key, ".json")
        if self.use and p.exists() and info_p.exists():
            for f in (db_path, db_path.with_name(db_path.name + ".wal")):
                f.unlink(missing_ok=True)
            shutil.copyfile(p, db_path)
            self.hits.append(name)
            return duckdb.connect(str(db_path)), json.loads(info_p.read_text(encoding="utf-8"))
        con, info = build()
        con.execute("CHECKPOINT")
        con.close()
        tmp = p.with_name(p.name + ".tmp")
        shutil.copyfile(db_path, tmp)
        tmp.replace(p)
        info_p.write_text(json.dumps(info, default=str), encoding="utf-8")
        for ext in (".duckdb", ".json"):
            self._prune(name, ext, p if ext == ".duckdb" else info_p)
        self.misses.append(name)
        return duckdb.connect(str(db_path)), info
