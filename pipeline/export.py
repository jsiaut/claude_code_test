"""Export des tables en Parquet, triées par clé primaire (§7.1).

Sept tables s'écrivent par DuckDB. `facts`, la seule dont les lignes ne changent pas d'une exécution à l'autre, s'écrit
en groupes de lignes à frontières stables (D-0089, point 4) : mêmes lignes, mêmes colonnes, même ordre, mais un groupe
commence au début d'un dépôt choisi par sa seule clé, et non toutes les N lignes. Un dépôt nouveau ne réécrit alors que
le groupe où il s'insère, et Git ne garde de la version nouvelle que ce groupe (0,8 Mo par semaine au lieu de 12).
"""
import zlib

import pyarrow.parquet as pq

FACTS_EVERY = 32          # un dépôt sur 32 ouvre un groupe : une centaine de groupes pour 1,6 million de faits
FACTS_RELIEF = 4          # au-delà de FACTS_MAX_ROWS lignes, un dépôt sur 4 en ouvre un
FACTS_MAX_ROWS = 40_000
FACTS_ZSTD_LEVEL = 12
SOURCE_PREFIXES = ("cf", "bdc", "html", "nds")      # companyfacts, BDC Data Sets, états lus en HTML, Notes Data Sets


def filing_unit(fact_key):
    """Dépôt d'un fait, lu dans sa clé : `accession/...` pour un fait d'instance, `source/accession/...` sinon."""
    parts = fact_key.split("/", 2)
    return "/".join(parts[:2]) if parts[0] in SOURCE_PREFIXES and len(parts) > 1 else parts[0]


def stable_cuts(keys):
    """Rangs où commence un groupe de lignes, pour des clés triées : la première ligne d'un dépôt dont le CRC-32 est un
    multiple de FACTS_EVERY, ou de FACTS_RELIEF quand le groupe en cours a atteint FACTS_MAX_ROWS lignes. La coupe ne
    dépend que des clés voisines : insérer un dépôt ne déplace aucune autre frontière, au groupe de relève près."""
    cuts, prev, last = [0], None, 0
    for i, k in enumerate(keys):
        u = filing_unit(k)
        if u == prev:
            continue
        prev = u
        if i:
            h = zlib.crc32(u.encode("utf-8"))
            if h % FACTS_EVERY == 0 or (i - last >= FACTS_MAX_ROWS and h % FACTS_RELIEF == 0):
                cuts.append(i)
                last = i
    return cuts


def write_facts(con, path, key="fact_key", table="facts"):
    """Écrit la table des faits triée par sa clé, un groupe de lignes par intervalle de `stable_cuts`. Renvoie le nombre
    de groupes. L'écriture est déterministe : mêmes lignes, mêmes octets."""
    t = con.execute(f"SELECT * FROM {table} ORDER BY {key}").to_arrow_table()
    cuts = stable_cuts(t.column(key).to_pylist()) + [t.num_rows]
    with pq.ParquetWriter(str(path), t.schema, compression="zstd", compression_level=FACTS_ZSTD_LEVEL) as w:
        for a, b in zip(cuts, cuts[1:]):
            if b > a:
                w.write_table(t.slice(a, b - a), row_group_size=b - a)
    return len(cuts) - 1


def write_table(con, table, pk, path):
    """Une table triée par sa clé primaire, écrite par DuckDB."""
    con.execute(f"COPY (SELECT * FROM {table} ORDER BY {', '.join(pk)}) TO '{path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
