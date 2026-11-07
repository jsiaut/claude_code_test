"""Mode de reconstruction (D-0084, point 3) : `db/` et `cache/` refaits sur un conteneur neuf.

Les catalogues préparés et les files dépendent de l'historique (plafonds d'une exécution à l'autre, tranches,
fenêtres « déjà lues ») : recalculés à neuf, ils ne redonnent pas ceux du commit de référence. Le mode les recalcule
sur toute la période close à l'as_of, comme à une première exécution, puis les ramène à ce que les tables du commit
de référence en montrent : un bloc se garde si sa clé a des lectures ou une exclusion `financial_parties_only` ; une
unité de file se prépare si un bloc gardé en vient.

Le mode s'active par la variable d'environnement PIPELINE_RECONSTRUCTION, qui nomme le commit de référence ; hors de
ce mode, rien ne change.

    PIPELINE_RECONSTRUCTION=12000e6 python -m pipeline.reconstruction status     # clés, accessions, documents
    PIPELINE_RECONSTRUCTION=12000e6 python -m pipeline.reconstruction restrict   # catalogues ramenés aux clés
"""
import functools
import io
import json
import os
import subprocess
import sys

from . import config

ENV = "PIPELINE_RECONSTRUCTION"


def reference():
    """Commit de référence du mode de reconstruction, None hors de ce mode."""
    return os.environ.get(ENV) or None


@functools.lru_cache(maxsize=None)
def _table(name, ref):
    import pandas as pd
    blob = subprocess.run(["git", "show", f"{ref}:tables/{name}.parquet"], capture_output=True, check=True,
                          cwd=config.ROOT).stdout
    return pd.read_parquet(io.BytesIO(blob))


def table(name):
    """Table `name` du commit de référence (lue dans l'historique Git)."""
    return _table(name, reference())


@functools.lru_cache(maxsize=None)
def _keys(ref):
    obs, ex = _table("observations", ref), _table("exclusions", ref)
    read = set(obs["content_key"].dropna())
    hdr = set(ex.loc[(ex["item_kind"] == "block") & (ex["reason"] == "financial_parties_only"), "item_key"].dropna())
    return frozenset(read), frozenset(hdr)


def read_keys():
    """Clés des blocs dont le commit de référence charge des lectures."""
    return _keys(reference())[0]


def keys():
    """Clés gardées : blocs lus, et blocs arrêtés à leur en-tête (`financial_parties_only`)."""
    r, h = _keys(reference())
    return r | h


@functools.lru_cache(maxsize=None)
def _accessions(ref):
    obs, ex = _table("observations", ref), _table("exclusions", ref)
    blk = ex[(ex["item_kind"] == "block") & (ex["reason"] == "financial_parties_only")]
    return frozenset(set(obs["accession"].dropna()) | set(blk["accession"].dropna()))


def accessions():
    """Accessions des blocs gardés."""
    return _accessions(reference())


@functools.lru_cache(maxsize=None)
def _kind_accessions(ref, prefix):
    obs = _table("observations", ref)
    return frozenset(obs.loc[obs["block_kind"].astype(str).str.startswith(prefix), "accession"].dropna())


def accessions_of(prefix):
    """Accessions des blocs lus dont le type commence par `prefix` (par exemple « discovery_ »)."""
    return _kind_accessions(reference(), prefix)


@functools.lru_cache(maxsize=None)
def _documents(ref, kinds):
    obs = _table("observations", ref)
    if kinds:
        obs = obs[obs["block_kind"].isin(kinds)]
    out = set()
    for dk in obs["doc_key"].dropna():
        parts = str(dk).split("/")
        if len(parts) >= 3:
            out.add((parts[-2], parts[-1]))          # (accession, fichier)
    return frozenset(out)


def documents(kinds=()):
    """(accession, fichier) des blocs lus, pour les types de blocs `kinds` (tous si vide)."""
    return _documents(reference(), tuple(sorted(kinds)))


def admits(key):
    """Une unité, ou un bloc, se garde à la reconstruction si sa clé (de contenu ou d'accession) est gardée."""
    return key in keys() or key in accessions()


def catalogs():
    """Catalogues ramenés aux clés gardées : ceux qui dépendent de l'historique (D-0084, point 3)."""
    from . import reader
    return [reader.CATALOG_MT, reader.CATALOG_6K, reader.CATALOG_SB, reader.CATALOG_DISC, reader.CATALOG_NF]


def restrict(paths=None):
    """Chaque catalogue ne garde que les blocs dont la clé est gardée, dans son ordre ; renvoie, par catalogue, les
    blocs gardés et écartés. Un bloc présent deux fois ne se garde qu'une fois."""
    k = keys()
    out = {}
    for p in paths or catalogs():
        if not p.exists():
            out[p.name] = {"kept": 0, "removed": 0, "absent": True}
            continue
        kept, removed, seen = [], 0, set()
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            b = json.loads(line)
            ck = b.get("content_key")
            if ck in k and ck not in seen:
                seen.add(ck)
                kept.append(line)
            else:
                removed += 1
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text("".join(x + "\n" for x in kept), encoding="utf-8")
        tmp.replace(p)
        out[p.name] = {"kept": len(kept), "removed": removed}
    return out


def missing():
    """Clés lues du commit de référence qu'aucun catalogue ne porte : échecs de la reconstruction."""
    from . import reader
    have = {b["content_key"] for b in reader.load_catalog()}
    return sorted(read_keys() - have)


def main(argv):
    if not reference():
        raise SystemExit(f"{ENV} absent : le mode de reconstruction nomme son commit de référence (D-0084).")
    cmd = argv[0] if argv else "status"
    if cmd == "status":
        print(json.dumps({"reference": reference(), "read_keys": len(read_keys()), "kept_keys": len(keys()),
                          "accessions": len(accessions()), "documents": len(documents())}, indent=1))
    elif cmd == "restrict":
        print(json.dumps(restrict(), indent=1))
    elif cmd == "missing":
        m = missing()
        print(len(m), "clés lues sans bloc")
        for x in m[:50]:
            print(" ", x)
    else:
        raise SystemExit(f"commande inconnue : {cmd}")


if __name__ == "__main__":
    main(sys.argv[1:])
