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
    PIPELINE_RECONSTRUCTION=12000e6 python -m pipeline.reconstruction hand       # fichiers de db/ faits à la main
    PIPELINE_RECONSTRUCTION=12000e6 python -m pipeline.reconstruction queues     # files et candidats d'origine

État versionné (D-0091, point 3) : quand le commit de référence porte `state/`, le mode s'en sert. Les clés gardées
comprennent celles des manifestes (un bloc préparé mais non lu revient aussi) ; la restriction suit le manifeste de
chaque catalogue (mêmes clés, même dépôt et même document, même ordre) ; les listes des montages, les files et les
candidats reviennent tels qu'à l'exécution d'origine. Sans `state/`, le mode se comporte comme avant.
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
def commit(ref):
    """Empreinte du commit que `ref` désigne ; `ref` tel quel si Git ne le connaît pas. `HEAD` ou une branche peuvent
    bouger : ce qui se garde d'une commande à l'autre se range sous l'empreinte (D-0091, point 12)."""
    r = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], capture_output=True, text=True,
                       cwd=config.ROOT)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else str(ref)


@functools.lru_cache(maxsize=None)
def _state_dir(ref):
    """`state/` du commit de référence, extrait une fois sous work/tmp/ref_state/ ; None si le commit n'en a pas."""
    import tarfile
    out = config.WORK / "tmp" / "ref_state" / commit(ref)
    if (out / "state" / "STATE.json").exists():
        return out / "state"
    r = subprocess.run(["git", "archive", "--format=tar", str(ref), "state"], capture_output=True, cwd=config.ROOT)
    if r.returncode != 0 or not r.stdout:
        return None
    out.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tf:
        tf.extractall(out, filter="data")
    return out / "state" if (out / "state" / "STATE.json").exists() else None


def state_dir():
    """État versionné du commit de référence (D-0091), None s'il n'en porte pas."""
    return _state_dir(reference())


@functools.lru_cache(maxsize=None)
def _manifests(ref):
    from . import state
    d = _state_dir(ref)
    return state.manifests(d) if d else {}


def manifests():
    """Manifestes des catalogues préparés au commit de référence : nom du catalogue -> blocs, dans l'ordre."""
    return _manifests(reference())


def manifest_fields():
    """Champs que portent les manifestes du commit de référence ; vide sans état versionné."""
    from . import state
    d = state_dir()
    return state.manifest_fields(d) if d else ()


def _missing(v):
    return v is None or (isinstance(v, float) and v != v)


def realign(b, row, fields):
    """Rend au bloc `b` les champs que la ligne `row` de son manifeste porte : le manifeste dit l'attribution, le
    recalcul rend le texte (D-0091, point 12). Un champ du manifeste absent de la ligne était vide à l'origine. Renvoie
    (changé, autre dépôt ou autre document)."""
    moved = b.get("accession") != row.get("accession") or b.get("document") != row.get("document")
    changed = False
    for f in fields:
        if f in ("content_key", "chars"):
            continue
        mv, bv = row.get(f), b.get(f)
        if f == "locator":
            if isinstance(mv, dict):
                loc = dict(bv) if isinstance(bv, dict) else {}
                if any(k not in loc or loc[k] != v for k, v in mv.items()):
                    loc.update(mv)
                    b[f] = loc
                    changed = True
            continue
        if _missing(mv) and _missing(bv):
            continue
        if mv != bv:
            b[f] = mv
            changed = True
    return changed, moved


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
    """Clés gardées : blocs lus, blocs arrêtés à leur en-tête (`financial_parties_only`), et blocs des manifestes de
    l'état versionné, lus ou non (D-0091)."""
    r, h = _keys(reference())
    return r | h | frozenset(b["content_key"] for rows in manifests().values() for b in rows)


@functools.lru_cache(maxsize=None)
def _accessions(ref):
    obs, ex = _table("observations", ref), _table("exclusions", ref)
    blk = ex[(ex["item_kind"] == "block") & (ex["reason"] == "financial_parties_only")]
    man = {b["accession"] for rows in _manifests(ref).values() for b in rows if b.get("accession")}
    return frozenset(set(obs["accession"].dropna()) | set(blk["accession"].dropna()) | man)


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
    for rows in _manifests(ref).values():            # blocs préparés de l'état versionné, lus ou non (D-0091)
        for b in rows:
            if b.get("accession") and b.get("document") and (not kinds or b.get("block_kind") in kinds):
                out.add((b["accession"], b["document"]))
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
      s'il y en a plusieurs ; à défaut d'accord, celui que le chargement retient : le dernier bloc du premier dépôt
      (D-0092) ;
    - un bloc gardé du bon document, dont aucune occurrence ne porte le type de pièce que la référence montre, le
      reprend d'elle : le recalcul le tire parfois du registre des documents, qui ne type pas les pièces des montages."""
    from . import reader
    k, ref, man = keys(), shown(), manifests()
    fields = manifest_fields() if man else ()
    attributed = "knowledge_date" in fields              # manifeste qui porte l'attribution des blocs (D-0091, point 12)
    out = {}
    for p in paths or catalogs():
        if not p.exists():
            out[p.name] = {"kept": 0, "removed": 0, "absent": True}
            continue
        with open(p, encoding="utf-8") as fh:            # ligne à ligne : un U+2028 dans un texte n'est pas une fin de ligne
            lines = [x.rstrip("\n") for x in fh if x.strip()]
        # état versionné (D-0091) : le manifeste du catalogue dit ses clés, le bloc de chacune et leur ordre
        rows = man.get(p.name)
        place = {b["content_key"]: i for i, b in enumerate(rows)} if rows is not None else None
        told = ({b["content_key"]: (b.get("block_kind"), b.get("accession"), b.get("document"), b.get("exhibit_type"))
                 for b in rows} if rows is not None else ref)
        cands, elsewhere = {}, 0
        for i, line in enumerate(lines):
            b = json.loads(line)
            ck = b.get("content_key")
            if ck not in (place if place is not None else k):
                continue
            r = told.get(ck)
            if r is not None and b.get("block_kind") != r[0]:
                elsewhere += 1
                continue
            cands.setdefault(ck, []).append((_agreement(b, r), i, reader.first_filed(b), b.get("accession")))
        best = {}
        for ck, c in cands.items():
            top = max(x[0] for x in c)
            c = [x for x in c if x[0] == top]
            acc = min(c, key=lambda x: x[2])[3]          # à accord égal, le premier dépôt (D-0092)…
            best[ck] = (top, max(x[1] for x in c if x[3] == acc))     # … et son dernier bloc
        keep = {i: ck for ck, (_, i) in best.items()}
        retyped = realigned = moved = 0
        row_of = {b["content_key"]: b for b in rows} if rows is not None else {}
        for ck, (agreement, i) in best.items():
            if rows is not None and attributed:          # le manifeste dit l'attribution du bloc
                b = json.loads(lines[i])
                changed, other = realign(b, row_of[ck], fields)
                if changed:
                    lines[i] = _line(b)
                    realigned += 1
                    moved += bool(other)
            elif agreement == 1:                         # bon document, type de pièce absent ou autre
                b = json.loads(lines[i])
                b["exhibit_type"] = told[ck][3]
                lines[i] = _line(b)
                retyped += 1
        order = sorted(keep, key=lambda i: place[keep[i]]) if place is not None else sorted(keep)
        kept = [lines[i] for i in order]
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text("".join(x + "\n" for x in kept), encoding="utf-8")
        tmp.replace(p)
        out[p.name] = {"kept": len(kept), "removed": len(lines) - len(kept),
                       **({"read_elsewhere": elsewhere} if elsewhere else {}),
                       **({"retyped": retyped} if retyped else {}),
                       **({"realigned": realigned, "from_another_filing": moved} if realigned else {}),
                       **({"manifest": len(place), "missing_from_manifest": len(set(place) - set(best))}
                          if place is not None else {})}
    return out


def unmanifested():
    """Catalogues recalculés des documents, sans manifeste : celui des groupes et celui du bloc `text`."""
    from . import reader
    return [reader.CATALOG, reader.CATALOG_EXT]


def prefer_shown(paths=None):
    """Catalogues sans manifeste : entre plusieurs blocs de même clé, range en dernier celui du dépôt et du document que
    la référence montre (D-0091, point 12). L'ordre de ces blocs suit l'index des dépôts, qui dépend de l'exécution
    (D-0085, point 15). Depuis D-0092, le chargement retient le premier dépôt quel que soit l'ordre : ce rangement ne
    joue plus qu'entre blocs d'un même dépôt, dont le chargement garde le dernier. Rien d'autre ne bouge. Renvoie, par
    catalogue, les clés en double et celles réordonnées."""
    ref = shown()
    out = {}
    for p in paths or unmanifested():
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as fh:            # ligne à ligne, comme `restrict`
            lines = [x.rstrip("\n") for x in fh if x.strip()]
        where = {}
        for i, line in enumerate(lines):
            b = json.loads(line)
            where.setdefault(b.get("content_key"), []).append((i, b.get("accession"), b.get("document")))
        swapped = 0
        for ck, occ in where.items():
            r = ref.get(ck)
            if len(occ) < 2 or r is None:
                continue
            good = [i for i, acc, doc in occ if acc == r[1] and doc == r[2]]
            last = occ[-1][0]
            if good and good[-1] != last:
                i = good[-1]
                lines[i], lines[last] = lines[last], lines[i]
                swapped += 1
        if swapped:
            tmp = p.with_suffix(p.suffix + ".tmp")
            tmp.write_text("".join(x + "\n" for x in lines), encoding="utf-8")
            tmp.replace(p)
        out[p.name] = {"duplicated_keys": sum(1 for o in where.values() if len(o) > 1), "reordered": swapped}
    return out


def restore_queues(only=()):
    """Files et candidats de la découverte et de la piste remis tels qu'à l'exécution d'origine (D-0091) : le recalcul
    d'une reconstruction leur donnait d'autres rangs. Renvoie, par fichier, les lignes d'avant et d'après et combien
    différaient ; rien sans état versionné. `only` : noms de fichiers à remettre (tous par défaut)."""
    import pandas as pd
    from . import state
    d = state_dir()
    out = {}
    if d is None:
        return out
    for name in state.QUEUES:
        if only and name not in only:
            continue
        p = config.DB_DIR / name
        before = pd.read_parquet(p) if p.exists() else None
        if not state.restore_queue(name, state=d):
            continue
        after = pd.read_parquet(p)
        same = before is not None and list(before.columns) == list(after.columns) and before.equals(after)
        out[name] = {"recalculated": None if before is None else len(before), "restored": len(after), "identical": bool(same)}
    return out


def _line(b):
    """Ligne d'un bloc réécrit : comme les catalogues, U+2028 et U+2029 échappés (D-0085, point 13)."""
    return json.dumps(b, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def missing_keys(have=None):
    """Échecs de la reconstruction : (clés lues du commit de référence, clés de ses manifestes) qu'aucun catalogue ne
    porte. Les secondes comptent aussi les blocs préparés que la référence n'a pas lus (D-0091, point 9)."""
    if have is None:
        from . import reader
        have = {b["content_key"] for b in reader.load_catalog()}
    man = {b["content_key"] for rows in manifests().values() for b in rows}
    return sorted(read_keys() - have), sorted(man - have)


def missing():
    """Clés lues du commit de référence qu'aucun catalogue ne porte."""
    return missing_keys()[0]


def main(argv):
    if not reference():
        raise SystemExit(f"{ENV} absent : le mode de reconstruction nomme son commit de référence (D-0084).")
    cmd = argv[0] if argv else "status"
    if cmd == "status":
        print(json.dumps({"reference": reference(), "read_keys": len(read_keys()), "kept_keys": len(keys()),
                          "accessions": len(accessions()), "documents": len(documents())}, indent=1))
    elif cmd == "restrict":
        from . import montages, state
        out = restrict()
        if state_dir() is not None:
            # état versionné (D-0091) : les listes des montages et les registres des unités préparées sont ceux de
            # l'exécution d'origine
            out["montages_info"] = {"restored": state.restore_lists(state=state_dir())}
            out["built"] = {"restored": state.restore_built(state=state_dir())}
        else:
            # sans état : les listes « au-delà du plafond » suivent leur catalogue (D-0088, point 25)
            out["montages_info"] = {"over_cap": montages.restrict_info()}
        out["without_manifest"] = prefer_shown()
        print(json.dumps(out, indent=1))
    elif cmd == "hand":
        from . import state
        d = state_dir()
        print("fichiers faits à la main remis dans db/ :", ", ".join(state.restore_hand(state=d)) if d else
              "aucun (le commit de référence n'a pas d'état versionné : D-0084, point 7)")
    elif cmd == "queues":
        print(json.dumps(restore_queues(argv[1:]), indent=1, ensure_ascii=False))
    elif cmd == "missing":
        read, man = missing_keys()
        print(len(read), "clés lues sans bloc ;", len(man), "blocs des manifestes absents des catalogues")
        was_read = set(read)
        for x in sorted(was_read | set(man))[:50]:
            print(" ", x, "lue" if x in was_read else "préparée, non lue")
        if read or man:
            # D-0091, point 9 : on n'assemble pas des tables qu'on sait incomplètes sans l'avoir décidé
            raise SystemExit("reconstruction incomplète : chercher la cause avant d'assembler. Pour assembler quand même, "
                             f"`python3 -m pipeline.rebuild {reference()} --from assemble`, et expliquer l'écart dans la "
                             "décision en cours.")
    else:
        raise SystemExit(f"commande inconnue : {cmd}")


if __name__ == "__main__":
    main(sys.argv[1:])
