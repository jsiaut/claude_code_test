"""Reconstruction d'un conteneur neuf en une commande (D-0091, point 5 ; RUNBOOK.md, § 6).

    make rebuild REF=<commit>                       # ou : python3 -m pipeline.rebuild <commit>
    python3 -m pipeline.rebuild <commit> --list     # les étapes, dans l'ordre, et celles déjà faites
    python3 -m pipeline.rebuild <commit> --from disc_verify
    python3 -m pipeline.rebuild <commit> --only assemble compare

Sans `db/` ni `cache/`, tout se retire de la SEC puis se recalcule sous le mode de reconstruction (D-0084), dont le
commit de référence est celui des tables à retrouver. La commande enchaîne les étapes dans l'ordre suivi à D-0088 :
une à la fois, donc une seule commande réseau à la fois ; chacune a son journal sous `work/tmp/logs/rebuild_<nom>.log`.
Elle s'arrête à la première étape qui échoue (un refus durable de la SEC arrête l'étape, D-0088, point 8) et reprend
où elle s'est arrêtée : l'avancement est dans `work/tmp/rebuild.json`.

Elle pose `PIPELINE_KEEP_ARCHIVES=1` : une archive des jeux de données se tire une fois pour tous ses lecteurs (Notes :
découverte et piste ; N-PORT : trois volets), puis s'efface après le dernier (D-0091, point 4).

Elle ne lit aucun bloc et ne commite rien. La dernière étape compare les tables à celles de la référence : chaque écart
s'explique dans la décision en cours.
"""
import datetime as dt
import json
import os
import subprocess
import sys

from . import config, montages, net, reconstruction

STATE = config.WORK / "tmp" / "rebuild.json"
LOGS = config.WORK / "tmp" / "logs"
NOTES_URL, NPORT_URL = "financial-statement-notes", "form-n-port"

# source d'un montage -> commandes qui tirent ou relèvent ses documents, avant la préparation des fenêtres
SEARCHED = {None: ("search", "fetch"), "search": ("search", "fetch"), "hits": ("replay", "fetch")}
CORPUS = {"corpus": "corpus", "lab_corpus": "lab_corpus", "backlog": "backlog_corpus", "edge_values": "values_corpus"}


def montage_steps(specs=None):
    """Étapes des montages : d'abord les recherches et leurs pièces, dans l'ordre de la configuration, puis les corpus,
    qui lisent ce qui est au cache (pièces des recherches comprises, D-0088, point 10), puis la préparation."""
    specs = montages.specs() if specs is None else specs
    out = []
    for mid, spec in specs.items():
        for cmd in SEARCHED.get(spec.get("source"), ()):
            out.append((f"mt_{cmd}_{mid}", ["montages", cmd, mid]))
    for mid, spec in specs.items():
        cmd = CORPUS.get(spec.get("source"))
        if cmd:
            out.append((f"mt_{cmd}_{mid}", ["montages", cmd, mid]))
    out.append(("mt_prepare", ["montages", "prepare"]))
    return out


def steps(ref, specs=None):
    """Étapes dans l'ordre : (nom, commande). Une commande est une liste d'arguments de `python3 -m pipeline.<module>`,
    ou une fonction sans argument pour ce qui se fait ici."""
    S = [
        ("hand", ["reconstruction", "hand"]),                    # fichiers de db/ qu'aucun programme n'écrit
        # tronc (§ 3, étape 3)
        ("phase0", ["phase0"]), ("universe", ["universe"]), ("index", ["phase0_index"]),
        ("phase1", ["phase1_run"]), ("phase2", ["phase2_fetch"]),
        ("catalog", ["catalog"]), ("text_catalog", ["text_catalog"]), ("spacex_d1", ["spacex_d1"]),
        # BDC : portefeuilles, puis passif
        ("lender_fetch", ["lender", "fetch"]), ("lender_extract", ["lender", "extract"]),
        ("lender_num", ["lender", "num"]), ("lp_extract", ["lender_portfolio", "extract"]),
        ("ll_extract", ["lender_liabilities", "extract"]), ("ll_inventory", ["lender_liabilities", "inventory"]),
        ("ll_fetch", ["lender_liabilities", "fetch"]), ("ll_classify", ["lender_liabilities", "classify"]),
        ("ll_exhibits", ["lender_liabilities", "exhibits"]), ("ll_finalize", ["lender_liabilities", "finalize"]),
        ("ll_announce", ["lender_liabilities", "announce"]),
        ("ll_check_announce", ["lender_liabilities", "check-announce"]),
        # découverte ; ses archives Notes restent gardées pour la piste
        ("disc_page", ["discovery", "page"]), ("disc_fetch", ["discovery", "fetch"]),
        ("disc_search", ["discovery", "search"]), ("disc_verify", ["discovery", "verify"]),
        ("disc_candidates", ["discovery", "candidates"]),
        ("disc_queues", ["reconstruction", "queues", "discovery_units.parquet", "discovery_candidates.parquet"]),
        ("disc_prepare", ["discovery", "prepare-history"]),
        # piste des non-déposants
        ("nf_fetch", ["nf_discovery", "fetch"]),
        ("drop_notes", lambda: print("archives Notes gardées effacées :", net.drop_kept(NOTES_URL))),
        ("nf_search", ["nf_discovery", "search"]), ("nf_verify", ["nf_discovery", "verify"]),
        ("nf_candidates", ["nf_discovery", "candidates"]), ("nf_own", ["nf_discovery", "own"]),
        ("nf_queues", ["reconstruction", "queues", "nf_discovery_units.parquet", "nf_discovery_own_units.parquet",
                       "nf_discovery_candidates.parquet"]),
        ("nf_prepare", ["nf_discovery", "prepare_history"]),
        # Form D, émetteurs étrangers et 6-K, SoftBank, participations, laboratoires
        ("formd", ["formd"]), ("foreign", ["foreign"]),
        ("sixk_fetch", ["sixk", "fetch"]), ("sixk_prepare", ["sixk", "prepare"]),
        ("sb_inventory", ["sb_own", "inventory"]), ("sb_headers", ["sb_own", "headers"]),
        ("sb_fetch", ["sb_own", "fetch"]), ("sb_prepare", ["sb_own", "prepare"]),
        ("own_fetch", ["ownership", "fetch"]), ("labs_inventory", ["labs", "inventory"]),
        # N-PORT : trois volets sur les mêmes archives
        ("nport_page", ["nport", "page"]), ("nport_fetch", ["nport", "fetch"]),
        ("nport_unlisted", ["nport", "unlisted-fetch"]),
        ("nport_unlisted_submissions", ["nport", "unlisted-submissions"]),
        ("nport_bonds", ["nport", "bonds-fetch"]),
        ("drop_nport", lambda: print("archives N-PORT gardées effacées :", net.drop_kept(NPORT_URL))),
    ]
    S += montage_steps(specs)
    S += [
        # catalogues ramenés à ceux de la référence, puis les tables
        ("restrict", ["reconstruction", "restrict"]), ("missing", ["reconstruction", "missing"]),
        ("assemble", ["assemble"]), ("compare", ["compare", ref]),
    ]
    return S


def _load(ref):
    if STATE.exists():
        st = json.loads(STATE.read_text(encoding="utf-8"))
        if st.get("ref") == ref and st.get("as_of") == config.as_of():
            return st
    return {"ref": ref, "as_of": config.as_of(), "done": [], "started": _now()}


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _journal_count():
    """Lignes du journal, requêtes et octets, pour le décompte d'une étape."""
    n = req = by = reused = 0
    if config.JOURNAL.exists():
        with open(config.JOURNAL, encoding="utf-8") as fh:
            for line in fh:
                n += 1
                o = json.loads(line)
                if o.get("url"):
                    req += 1
                    by += (o.get("bytes") or 0) if o.get("status") == 200 else 0
                elif o.get("status") == "reused":
                    reused += 1
    return {"lines": n, "requests": req, "bytes": by, "reused": reused}


def run(ref, start=None, only=None, env=None):
    """Lance les étapes restantes ; renvoie 0 si tout a réussi, 1 à la première étape qui échoue."""
    env = dict(os.environ if env is None else env)
    env[reconstruction.ENV] = ref                        # chaque étape tourne dans son processus, sous le mode
    env[net.KEEP_ENV] = "1"
    S = steps(ref)
    names = [n for n, _ in S]
    for x in ([start] if start else []) + list(only or []):
        if x not in names:
            raise SystemExit(f"étape inconnue : {x} (voir --list)")
    st = _load(ref)
    if start:
        st["done"] = [n for n in st["done"] if names.index(n) < names.index(start)] if set(st["done"]) <= set(names) else []
    LOGS.mkdir(parents=True, exist_ok=True)
    for name, cmd in S:
        if only and name not in only:
            continue
        if not only and name in st["done"]:
            continue
        t0, j0 = _now(), _journal_count()
        log = LOGS / f"rebuild_{name}.log"
        print(f"{t0[11:19]} {name} …", flush=True)
        if callable(cmd):
            try:
                cmd()
                rc = 0
            except Exception as exc:                     # une étape locale qui échoue arrête la commande comme les autres
                print(f"  {type(exc).__name__}: {exc}")
                rc = 1
        else:
            with open(log, "w", encoding="utf-8") as fh:
                rc = subprocess.run([sys.executable, "-m", f"pipeline.{cmd[0]}", *cmd[1:]], cwd=config.ROOT, env=env,
                                    stdout=fh, stderr=subprocess.STDOUT).returncode
        j1 = _journal_count()
        rec = {"name": name, "start": t0, "end": _now(), "rc": rc, "requests": j1["requests"] - j0["requests"],
               "bytes": j1["bytes"] - j0["bytes"], "reused": j1["reused"] - j0["reused"]}
        st.setdefault("steps", []).append(rec)
        if rc != 0:
            STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
            print(f"ÉCHEC de l'étape {name} (code {rc}) ; journal : {log}")
            if log.exists():
                print("".join(log.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)[-15:]))
            print(f"Reprise après correction : python3 -m pipeline.rebuild {ref} --from {name}")
            return 1
        if name not in st["done"]:
            st["done"].append(name)
        STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
        print(f"  fait : {rec['requests']} requêtes, {rec['bytes'] / 1e6:.1f} Mo" +
              (f", {rec['reused']} archives reprises" if rec["reused"] else ""), flush=True)
    summary(st)
    return 0


def summary(st):
    done = [r for r in st.get("steps", []) if r["rc"] == 0]
    print(f"reconstruction contre {st['ref']} : {len(st['done'])} étapes faites ; "
          f"{sum(r['requests'] for r in done)} requêtes, {sum(r['bytes'] for r in done) / 1e9:.1f} Go, "
          f"{sum(r['reused'] for r in done)} archives reprises ; commencée le {st['started']}")
    log = LOGS / "rebuild_compare.log"
    if "compare" in st["done"] and log.exists():
        print("".join(x for x in log.read_text(encoding="utf-8").splitlines(keepends=True) if not x.startswith("      ")))


def main(argv):
    if not argv or argv[0].startswith("-"):
        raise SystemExit("usage : python3 -m pipeline.rebuild <commit de référence> [--list] [--from ÉTAPE] [--only ÉTAPE…]")
    ref, rest = argv[0], argv[1:]
    if subprocess.run(["git", "cat-file", "-e", f"{ref}:tables/observations.parquet"], cwd=config.ROOT).returncode != 0:
        raise SystemExit(f"{ref} : commit sans tables lisibles (clone superficiel ? RUNBOOK.md, § 1)")
    if "--list" in rest:
        st = _load(ref)
        for name, cmd in steps(ref):
            what = "ici" if callable(cmd) else "python3 -m pipeline." + " ".join(cmd)
            print(("fait   " if name in st["done"] else "à faire"), f"{name:28s}", what)
        return 0
    start = rest[rest.index("--from") + 1] if "--from" in rest else None
    only = rest[rest.index("--only") + 1:] if "--only" in rest else None
    return run(ref, start=start, only=only)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
