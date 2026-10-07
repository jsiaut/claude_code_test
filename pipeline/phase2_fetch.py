"""Téléchargement des documents de la tranche texte (§11.1, phase 2) : document principal
des 8-K de la tranche et leurs pièces EX-10 et EX-4, DEF 14A, 424B4 des introductions."""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import config
from .edgar import Edgar
from .net import NotCollected, SecClient

EX10 = re.compile(r"^EX-10(\.\d+[A-Z]?)?$", re.I)
EX4 = re.compile(r"^EX-4(\.\d+[A-Z]?)?$", re.I)


def targets():
    recs = json.loads((config.DB_DIR / "filing_index.json").read_text())
    out = []
    for r in recs:
        cls = r["inv_class"]
        if cls == "8k_first_pass":
            out.append((r["cik"], r["accession"], r["primary"], "primary"))
            for d in r.get("documents") or []:
                t = d["TYPE"].upper().strip()
                if EX10.match(t) or EX4.match(t):
                    out.append((r["cik"], r["accession"], d["FILENAME"], t))
        elif cls == "proxy":
            out.append((r["cik"], r["accession"], r["primary"], "primary"))
        elif cls == "ipo" and r["form"] == "424B4":
            out.append((r["cik"], r["accession"], r["primary"], "primary"))
    return out


def run(as_of, workers=4):
    client = SecClient(as_of)
    e = Edgar(client, as_of)
    tg = targets()
    failures = []

    def one(t):
        cik, acc, name, kind = t
        try:
            e.archive(cik, acc, name)
            return None
        except NotCollected as exc:
            return {"cik": cik, "accession": acc, "document": name, "kind": kind, "error": str(exc)}

    with ThreadPoolExecutor(workers) as pool:
        futs = [pool.submit(one, t) for t in tg]
        for i, f in enumerate(as_completed(futs)):
            r = f.result()
            if r:
                failures.append(r)
            if (i + 1) % 100 == 0:
                print(f"{i + 1}/{len(futs)} {client.stats}", flush=True)
    (config.DB_DIR / "phase2_fetch_failures.json").write_text(json.dumps(failures, indent=1))
    print("terminé", len(tg), "documents ;", len(failures), "échecs ;", client.stats, flush=True)


if __name__ == "__main__":
    run(sys.argv[1])
