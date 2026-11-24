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


@functools.lru_cache(maxsize=None)
def _shown(ref):
    obs = _table("observations", ref)
    out = {}
    for ck, kind, acc, dk, ex in zip(obs["content_key"], obs["block_kind"], obs["accession"], obs["doc_key"],
                                     obs["exhibit_type"]):
        out[ck] = (kind, acc, str(dk).split("/", 2)[-1], ex if isinstance(ex, str) else None)
    return out


def shown():
    """Par clé lue, ce que la table des observations du commit de référence montre de son bloc : type de bloc, dépôt,
    document, type de pièce (D-0088, point 10)."""
    return _shown(reference())


def _agreement(b, ref):
    """Accord d'un bloc avec ce que la référence montre de sa clé : 0 si le dépôt ou le document diffère, 1 s'ils sont
    les mêmes, 2 si le type de pièce l'est aussi."""
    if ref is None or b.get("accession") != ref[1] or b.get("document") != ref[2]:
        return 0
    ex = b.get("exhibit_type")
    return 2 if (ex if isinstance(ex, str) else None) == ref[3] else 1


def restrict(paths=None):
    """Chaque catalogue ne garde que les blocs dont la clé est gardée, dans son ordre ; renvoie, par catalogue, les
    blocs gardés et écartés.

    Un catalogue recalculé d'un bloc porte parfois plusieurs blocs de même clé : le même texte dans deux dépôts, ou la
    même fenêtre servie par deux montages. La référence dit de quel bloc viennent ses lectures (D-0088, point 10) :
    - un bloc dont elle montre la clé sous un autre type de bloc est écarté (elle la lit dans un autre catalogue) ;
    - entre plusieurs blocs de même clé, se garde celui du dépôt et du document qu'elle montre, de même type de pièce
      s'il y en a plusieurs ; à défaut d'accord, le dernier, celui que le chargement retient (D-0083, point 12) ;
    - un bloc gardé du bon document, dont aucune occurrence ne porte le type de pièce que la référence montre, le
      reprend d'elle : le recalcul le tire parfois du registre des documents, qui ne type pas les pièces des montages."""
    k, ref = keys(), shown()
    out = {}
    for p in paths or catalogs():
        if not p.exists():
            out[p.name] = {"kept": 0, "removed": 0, "absent": True}
            continue
        with open(p, encoding="utf-8") as fh:            # ligne à ligne : un U+2028 dans un texte n'est pas une fin de ligne
            lines = [x.rstrip("\n") for x in fh if x.strip()]
        best, elsewhere = {}, 0
        for i, line in enumerate(lines):
            b = json.loads(line)
            ck = b.get("content_key")
            if ck not in k:
                continue
            r = ref.get(ck)
            if r is not None and b.get("block_kind") != r[0]:
                elsewhere += 1
                continue
            rank = (_agreement(b, r), i)                 # à accord égal, la dernière occurrence
            if ck not in best or rank > best[ck]:
                best[ck] = rank
        keep = {i: ck for ck, (_, i) in best.items()}
        retyped = 0
        for ck, (agreement, i) in best.items():
            if agreement == 1:                           # bon document, type de pièce absent ou autre
                b = json.loads(lines[i])
                b["exhibit_type"] = ref[ck][3]
                lines[i] = _line(b)
                retyped += 1
        kept = [line for i, line in enumerate(lines) if i in keep]
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text("".join(x + "\n" for x in kept), encoding="utf-8")
        tmp.replace(p)
        out[p.name] = {"kept": len(kept), "removed": len(lines) - len(kept),
                       **({"read_elsewhere": elsewhere} if elsewhere else {}),
                       **({"retyped": retyped} if retyped else {})}
    return out


def _line(b):
    """Ligne d'un bloc réécrit : comme les catalogues, U+2028 et U+2029 échappés (D-0085, point 13)."""
    return json.dumps(b, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


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
        from . import montages
        out = restrict()
        # les listes « au-delà du plafond » des montages suivent leur catalogue (D-0088, point 25)
        out["montages_info"] = {"over_cap": montages.restrict_info()}
        print(json.dumps(out, indent=1))
    elif cmd == "missing":
        m = missing()
        print(len(m), "clés lues sans bloc")
        for x in m[:50]:
            print(" ", x)
    else:
        raise SystemExit(f"commande inconnue : {cmd}")


if __name__ == "__main__":
    main(sys.argv[1:])
