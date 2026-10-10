"""Pilote de la phase 1 : companyfacts, archives XBRL des rapports périodiques de la
période de lecture, instances des autres dépôts sources d'un fait de companyfacts."""
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb
import pandas as pd

from . import config, phase1
from .edgar import Edgar, cik10
from .net import NotCollected, SecClient

PERIODIC = ("10-K", "10-K/A", "10-Q", "10-Q/A", "10-KT", "10-KT/A", "10-QT", "10-QT/A")


def run(as_of, workers=4):
    cfg = config.load()
    p0 = json.loads((config.DB_DIR / "phase0.json").read_text())
    client = SecClient(as_of, cfg)
    e = Edgar(client, as_of)
    con = duckdb.connect()
    filings = con.execute(f"SELECT * FROM '{config.DB_DIR / 'filings.parquet'}'").fetchdf()
    by_acc = {r["accessionNumber"]: r for r in filings.to_dict("records")}

    # 1. companyfacts, prédécesseurs compris, sans borne de date ; les faits des rapports du déclarant
    # légal antérieurs à une fusion inversée sont hors du groupe (D-0043)
    from .phase0 import pre_combination_accessions
    pre = pre_combination_accessions(filings.to_dict("records"), cfg)
    cf_pre = {}
    cf_rows = []
    for cik, m in p0["meta"].items():
        try:
            cf = e.companyfacts(cik)
        except NotCollected as exc:
            print("companyfacts non collecté", cik, exc)
            continue
        # faits déposés après l'as_of écartés (ressource tirée plus tard pour un groupe ajouté, D-0043)
        for r in phase1.companyfacts_rows(cf, m["group"], cik, by_acc):
            if (r["filing_date"] or "") > as_of:
                continue
            if r["accession"] in pre:
                cf_pre[m["group"]] = cf_pre.get(m["group"], 0) + 1
                continue
            cf_rows.append(r)
    (config.DB_DIR / "phase1_pre_combination.json").write_text(json.dumps(
        {"facts_excluded": cf_pre, "accessions": len(pre)}, indent=1))
    print("companyfacts :", len(cf_rows), "faits", client.stats, flush=True)

    # 2. archives XBRL des rapports périodiques de la période de lecture
    inv = con.execute(f"""SELECT group_id, filer_cik, accessionNumber, form, filingDate, reportDate,
                                 acceptanceDateTime, items, isXBRL, isInlineXBRL, primaryDocument
                          FROM '{config.DB_DIR / 'inventory.parquet'}' WHERE inv_class = 'periodic'""").fetchdf()
    results, failures = [], []

    def one(r):
        filing = {"group_id": r["group_id"], "cik": r["filer_cik"], "accessionNumber": r["accessionNumber"],
                  "form": r["form"], "filingDate": r["filingDate"], "reportDate": r["reportDate"],
                  "acceptanceDateTime": r["acceptanceDateTime"]}
        try:
            d, files = phase1.fetch_xbrl(e, r["filer_cik"], r["accessionNumber"])
            if d["instance"] is None:
                return filing, None, "pas d'instance XBRL dans le dépôt"
            parsed = phase1.parse_filing(r["group_id"], filing, d, files)
            return filing, (d, parsed), None
        except NotCollected as exc:
            return filing, None, f"not_collected: {exc}"
        except Exception as exc:  # parse_failed : écarté avec son motif, l'exécution continue
            return filing, None, "parse_failed: " + "".join(traceback.format_exception_only(exc)).strip()

    with ThreadPoolExecutor(workers) as pool:
        futs = [pool.submit(one, r) for r in inv.to_dict("records")]
        for i, f in enumerate(as_completed(futs)):
            filing, res, err = f.result()
            if err:
                failures.append({"accession": filing["accessionNumber"], "group_id": filing["group_id"],
                                 "form": filing["form"], "error": err})
            else:
                results.append((filing, res))
            if (i + 1) % 25 == 0:
                print(f"{i + 1}/{len(futs)} {client.stats}", flush=True)

    # 3. écriture des tables de travail
    out = config.DB_DIR
    inst_rows = [row for _, (_, p) in results for row in p["facts"]]
    pd.DataFrame(cf_rows).to_parquet(out / "facts_companyfacts.parquet")
    pd.DataFrame(inst_rows).to_parquet(out / "facts_instances.parquet")
    for name in ("text_blocks", "pres", "calc", "tags", "labels"):
        rows = [row for _, (_, p) in results for row in p[name]]
        if rows:
            pd.DataFrame(rows).to_parquet(out / f"{name}.parquet")
    docs = []
    for filing, (d, p) in results:
        docs.append({"accession": filing["accessionNumber"], "group_id": filing["group_id"],
                     "cik": filing["cik"], "form": filing["form"], "zip": d["zip"],
                     "instance": d["instance"], "metalinks": d["metalinks"],
                     "filing_summary": d["filing_summary"], "n_facts": len(p["facts"]),
                     "n_text_blocks": len(p["text_blocks"]), "filing_summary_reports": len(p["filing_summary"])})
    pd.DataFrame(docs).to_parquet(out / "xbrl_documents.parquet")
    (out / "phase1_failures.json").write_text(json.dumps(failures, indent=1))
    print("terminé :", len(results), "dépôts lus,", len(failures), "échecs ;", client.stats, flush=True)


if __name__ == "__main__":
    run(sys.argv[1])
