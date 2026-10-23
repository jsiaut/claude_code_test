"""Aperçu (D-0062) : arêtes, paires et exposition recalculées depuis les observations, comparées aux
tables du dernier réassemblage complet, sans rien écrire dans tables/.

    python -m pipeline.assemble --apercu

L'aperçu suit le même code que l'assemblage (assemble.run, apercu=True) jusqu'aux paires, à
l'exposition, au grand livre des laboratoires, aux cycles et à l'annexe E, puis applique les
invariants d'agrégat et l'univers attendu comme aux étapes 10 et 11. Il saute les mesures tirées des
faits, les signaux, les événements de l'annexe F, les contrôles et l'export. Seules les mesures qu'il
calcule entrent dans la comparaison. Le détail des écarts est écrit dans work/tmp/apercu.json ;
l'aperçu ne remplace pas le réassemblage complet, qui seul écrit les tables.
"""
import json
import time


from . import assemble, config

SHOWN = ("relationship_conclusion", "financed_status", "counterparty_exposure", "lab_ledger", "documented_path",
         "annex_e_outcome")


def _rows(con, table, rows):
    """Lignes telles que la table les écrirait : même insertion (types, doublons) que l'assemblage."""
    assemble.insert(con, table, rows)
    pk = assemble.TABLES[table]
    cols = [c[0] for c in con.execute(f"DESCRIBE {table}").fetchall()]
    out = {}
    for r in con.execute(f"SELECT * FROM {table} ORDER BY {', '.join(pk)}").fetchall():
        d = dict(zip(cols, r))
        out[tuple(d[k] for k in pk)] = d
    return out


def _table(table, where):
    pk = assemble.TABLES[table]
    con = config.duckdb_connect()
    rel = con.execute(f"SELECT * FROM '{config.ROOT / 'tables' / (table + '.parquet')}' WHERE {where} "
                      f"ORDER BY {', '.join(pk)}")
    cols = [d[0] for d in rel.description]
    out = {}
    for r in rel.fetchall():
        d = dict(zip(cols, r))
        out[tuple(d[k] for k in pk)] = d
    return out


def compare(new, old):
    """(ajoutées, retirées, modifiées) : clés, et pour une ligne modifiée les colonnes qui changent."""
    added = sorted(set(new) - set(old), key=str)
    removed = sorted(set(old) - set(new), key=str)
    changed = {k: {c: (old[k].get(c), new[k].get(c)) for c in new[k] if new[k].get(c) != old[k].get(c)}
               for k in set(new) & set(old) if new[k] != old[k]}
    return added, removed, dict(sorted(changed.items(), key=lambda kv: str(kv[0])))


def _fmt(v):
    return "∅" if v is None else str(v)


def main(as_of, use_cache=True):
    t0 = time.time()
    res = assemble.run(as_of, use_cache=use_cache, apercu=True)
    computed = sorted({c["measure"] for c in res["computed"]})
    con = config.duckdb_connect()
    con.execute((config.ROOT / "schema.sql").read_text(encoding="utf-8"))
    new_edges = _rows(con, "links", [{k: v for k, v in l.items() if not k.startswith("_")} for l in res["edges"]])
    old_edges = _table("links", "link_kind = 'edge'")
    new_cells = _rows(con, "measures", [c for c in res["cells"] if c["measure"] in set(computed)])
    old_cells = _table("measures", "measure IN (" + ", ".join(f"'{m}'" for m in computed) + ")")
    e_add, e_rem, e_chg = compare(new_edges, old_edges)
    report = {"as_of": as_of, "seconds": round(time.time() - t0), "memo": res["stats"].get("memo"),
              "edges": {"table": len(old_edges), "apercu": len(new_edges), "added": [k[0] for k in e_add],
                        "removed": [k[0] for k in e_rem],
                        "changed": {k[0]: {c: [_fmt(a), _fmt(b)] for c, (a, b) in v.items()} for k, v in e_chg.items()}},
              "measures": {}}
    print(f"aperçu au {as_of} : {report['seconds']} s ; mémo repris : {', '.join(report['memo']['hits']) or 'rien'}")
    print(f"arêtes : {len(old_edges)} dans les tables, {len(new_edges)} recalculées ; "
          f"{len(e_add)} nouvelles, {len(e_rem)} disparues, {len(e_chg)} modifiées")
    for k in (e_add[:5]):
        e = new_edges[k]
        print(f"  + {e['from_group']} → {e['to_group']} {e['family']}/{e['edge_type']} {_fmt(e['amount'])} {_fmt(e['unit'])}"
              f" ({e['stage']}) {k[0]}")
    for k in (e_rem[:5]):
        e = old_edges[k]
        print(f"  − {e['from_group']} → {e['to_group']} {e['family']}/{e['edge_type']} {_fmt(e['amount'])} {k[0]}")
    for k, v in list(e_chg.items())[:5]:
        print(f"  ~ {k[0]} : " + " ; ".join(f"{c} {_fmt(a)} → {_fmt(b)}" for c, (a, b) in v.items()))
    by_m = {}
    for key in set(new_cells) | set(old_cells):
        by_m.setdefault(key[0], set()).add(key)
    print("mesures recalculées (lignes des tables / écarts) :")
    for m in computed:
        keys = by_m.get(m, set())
        n = {k: new_cells[k] for k in keys if k in new_cells}
        o = {k: old_cells[k] for k in keys if k in old_cells}
        a, r, c = compare(n, o)
        report["measures"][m] = {"table": len(o), "apercu": len(n), "added": [list(map(str, k)) for k in a],
                                 "removed": [list(map(str, k)) for k in r],
                                 "changed": [{"key": list(map(str, k)), "columns": {col: [_fmt(x), _fmt(y)] for col, (x, y) in v.items()}}
                                             for k, v in c.items()]}
        flag = "" if not (a or r or c) else f" ; {len(a)} nouvelles, {len(r)} disparues, {len(c)} modifiées"
        print(f"  {m} : {len(o)}{flag}")
        if m in SHOWN:
            for k in a[:3]:
                x = n[k]
                print(f"    + {x['subject']} / {x['counterparty']} {_fmt(x['period_end'])} {x['status']} "
                      f"{_fmt(x['value'] if x['value'] is not None else x['value_text'])}")
            for k in r[:3]:
                x = o[k]
                print(f"    − {x['subject']} / {x['counterparty']} {_fmt(x['period_end'])} {x['status']}")
            for k, v in list(c.items())[:3]:
                cols = [f"{col} {_fmt(x)} → {_fmt(y)}" for col, (x, y) in v.items() if col not in ("flags", "lineage")]
                print(f"    ~ {k[1]} / {k[2]} {_fmt(k[4])} : " +
                      (" ; ".join(cols) if cols else "preuves seulement (" + ", ".join(v) + ")"))
    for f in ("apercu.duckdb", "apercu.duckdb.wal"):     # base de travail de l'aperçu, sans usage ensuite
        (config.DB_DIR / f).unlink(missing_ok=True)
    out = config.ROOT / "work" / "tmp" / "apercu.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    same = not (e_add or e_rem or e_chg) and all(not (v["added"] or v["removed"] or v["changed"])
                                                 for v in report["measures"].values())
    print("aucun écart avec les tables" if same else f"détail des écarts : {out.relative_to(config.ROOT)}")
    return report
