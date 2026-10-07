"""Phase 0, suite : index des dépôts de la tranche (index.json et en-tête SGML).

Le type d'une pièce se lit dans l'en-tête SGML, jamais dans le nom de fichier ni dans
index.json, où il n'est qu'une icône (§2.3) ; index.json donne l'inventaire et les tailles.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb

from . import config
from .edgar import Edgar
from .net import NotCollected, SecClient

CLASSES = ("periodic", "8k_first_pass", "proxy", "ipo")


def run(as_of, workers=4):
    con = duckdb.connect()
    inv = con.execute(f"""SELECT group_id, filer_cik, accessionNumber, form, filingDate, reportDate,
                                 items, inv_class, primaryDocument, size, acceptanceDateTime
                          FROM '{config.DB_DIR / 'inventory.parquet'}'
                          WHERE inv_class IN {CLASSES}""").fetchall()
    client = SecClient(as_of)
    e = Edgar(client, as_of)
    out, failures = [], []

    def one(row):
        g, cik, acc, form, fdate, rdate, items, cls, prim, size, accept = row
        rec = {"group_id": g, "cik": cik, "accession": acc, "form": form, "filing_date": fdate,
               "report_date": rdate, "items": items, "inv_class": cls, "primary": prim,
               "submission_size": size, "acceptance": accept}
        try:
            idx = e.filing_index(cik, acc)
            rec["files"] = [{"name": it["name"], "size": int(it.get("size") or 0)}
                            for it in idx.get("directory", {}).get("item", [])]
        except NotCollected as exc:
            rec["files"] = None
            rec["index_error"] = str(exc)
        try:
            sg = e.sgml_documents(cik, acc)
            rec["documents"] = sg["documents"]
            rec["sgml_header"] = sg["header"]
        except NotCollected as exc:
            rec["documents"] = None
            rec["sgml_error"] = str(exc)
        return rec

    with ThreadPoolExecutor(workers) as pool:
        futs = [pool.submit(one, r) for r in inv]
        for i, f in enumerate(as_completed(futs)):
            rec = f.result()
            out.append(rec)
            if rec.get("index_error") or rec.get("sgml_error"):
                failures.append(rec)
            if (i + 1) % 100 == 0:
                print(f"{i + 1}/{len(futs)} {client.stats}", flush=True)
    (config.DB_DIR / "filing_index.json").write_text(json.dumps(out, default=str))
    print("terminé", len(out), "échecs", len(failures), client.stats)
    return out


if __name__ == "__main__":
    run(sys.argv[1])
