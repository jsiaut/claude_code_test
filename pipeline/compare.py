"""Comparaison des tables d'un réassemblage à celles d'un commit (D-0087, point 9).

Après un réassemblage, les huit tables se comparent à celles du commit précédent, clé par clé, et chaque écart
s'explique dans la décision (CLAUDE.md). Par table : les lignes du commit de référence et celles de tables/, les clés
apparues, les clés disparues et les lignes changées à clé égale ; pour `measures`, le détail par mesure.

    python -m pipeline.compare            # tables/ contre le dernier commit (HEAD)
    python -m pipeline.compare 587dbbc    # contre un autre commit

Lecture seule, sans db/ : les tables du commit se lisent dans l'historique Git.
"""
import pathlib
import subprocess
import sys
import tempfile

import duckdb

from . import config
from .assemble import TABLES


def _columns(con, path):
    return [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{path}'").fetchall()]


def diff_tables(old_dir, new_dir, tables=None):
    """Écarts de `new_dir` par rapport à `old_dir`, par table : lignes de part et d'autre, clés apparues et disparues,
    lignes changées à clé égale (sur les colonnes communes), colonnes ajoutées ou retirées ; pour `measures`, les
    mêmes comptes par mesure, sans les mesures inchangées."""
    con = duckdb.connect()
    out = {}
    for t, pk in (tables or TABLES).items():
        old, new = pathlib.Path(old_dir) / f"{t}.parquet", pathlib.Path(new_dir) / f"{t}.parquet"
        oc, nc = _columns(con, old), _columns(con, new)
        k, cols = ", ".join(pk), ", ".join(c for c in nc if c in oc)

        def by(sql, group):
            g = f"{group}, " if group else ""
            rows = con.execute(f"SELECT {g}count(*) FROM ({sql}){' GROUP BY 1' if group else ''}").fetchall()
            return {r[0]: r[1] for r in rows} if group else rows[0][0]

        def counts(group=None):
            added = by(f"SELECT {k} FROM '{new}' EXCEPT SELECT {k} FROM '{old}'", group)
            removed = by(f"SELECT {k} FROM '{old}' EXCEPT SELECT {k} FROM '{new}'", group)
            differ = by(f"SELECT {cols} FROM '{new}' EXCEPT SELECT {cols} FROM '{old}'", group)
            return added, removed, differ

        added, removed, differ = counts()
        r = {"old": by(f"SELECT * FROM '{old}'", None), "new": by(f"SELECT * FROM '{new}'", None), "added": added,
             "removed": removed, "changed": differ - added,
             "columns_added": [c for c in nc if c not in oc], "columns_removed": [c for c in oc if c not in nc]}
        if t == "measures":
            a, d, x = counts("measure")
            r["by_measure"] = {m: {"added": a.get(m, 0), "removed": d.get(m, 0), "changed": x.get(m, 0) - a.get(m, 0)}
                               for m in sorted(set(a) | set(d) | set(x))}
        out[t] = r
    return out


def tables_of(ref, directory):
    """Les huit tables du commit `ref`, écrites dans `directory`."""
    for t in TABLES:
        r = subprocess.run(["git", "show", f"{ref}:tables/{t}.parquet"], capture_output=True, cwd=config.ROOT)
        if r.returncode != 0:
            raise SystemExit(f"tables/{t}.parquet illisible au commit {ref} : {r.stderr.decode('utf-8', 'replace').strip()}")
        (pathlib.Path(directory) / f"{t}.parquet").write_bytes(r.stdout)


def _fr(n, width=0):
    return f"{n:,d}".replace(",", " ").rjust(width)


def report(diff, ref):
    lines = [f"tables/ contre le commit {ref} :"]
    for t, r in diff.items():
        s = (f"  {t:13s} {_fr(r['old'], 9)} -> {_fr(r['new'], 9)} lignes ; clés apparues {_fr(r['added'])}, disparues "
             f"{_fr(r['removed'])} ; lignes changées à clé égale {_fr(r['changed'])}")
        if r["columns_added"] or r["columns_removed"]:
            s += f" ; colonnes ajoutées {r['columns_added']}, retirées {r['columns_removed']}"
        lines.append(s)
        for m, c in (r.get("by_measure") or {}).items():
            lines.append(f"      {m} : +{c['added']}, −{c['removed']}, changées {c['changed']}")
    return "\n".join(lines)


if __name__ == "__main__":
    ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    with tempfile.TemporaryDirectory() as d:
        tables_of(ref, d)
        print(report(diff_tables(d, config.TABLES), ref))
