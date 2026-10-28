"""Bloc `labs` (D-0060) : OpenAI et Anthropic vus par les déposants, sans requête.

Volet 3 : faits balisés dont un membre de dimension nomme un laboratoire, dans les instances des groupes et dans
les extraits des Notes Data Sets déjà en cache (mesure `lab_tagged_value`). Le point de vue est celui du déposant
(actionnaire, fournisseur, bailleur, prêteur) : jamais un fait comptable du laboratoire, jamais une valorisation.
Les paragraphes qui portent ces faits se servent à la lecture (montage `labs_tagged`, source `tagged`), avec leurs
faits candidats et les libellés de leurs membres : une contrepartie que le texte tait et qu'un libellé nomme y
devient dérivable (§2.4).

Volet 4 : grand livre par laboratoire (mesure `lab_ledger`). Pour chaque partenaire, ses arêtes avec le laboratoire,
par instrument et par sens des ressources (§3.1), au dernier montant admissible connu. Un flux reste le dernier flux
publié, jamais une somme ; aucun total.

    python -m pipeline.labs inventory                  # faits retenus et comptés (D-0060, point 2)
    python -m pipeline.montages prepare labs_tagged    # unités du volet 3 (D-0060, point 4)
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal

import pandas as pd

from . import config
from .measures import NONE, cell

LABS = {"OpenAI": "LAB:OPENAI", "OPENAI": "LAB:OPENAI", "Anthropic": "LAB:ANTHROPIC", "ANTHROPIC": "LAB:ANTHROPIC"}
# mot de la casse en chameau : suivi d'une majuscule (« Member » compris), d'un chiffre ou de la fin du nom
LAB_WORD = re.compile(r"(OpenAI|OPENAI|Anthropic|ANTHROPIC)(?=[A-Z0-9_]|$)")
COMPLEMENT = re.compile(r"(OtherThan|Excluding|Except)(?=[A-Z]|$)")
LAB_NAME = re.compile(r"(?i)\b(?:open ?ai|anthropic)\b")      # citation ou contrepartie qui nomme un laboratoire
STANDARD = ("us-gaap", "srt", "dei", "ifrs-full", "ecd", "country", "currency", "exch", "invest")
INSTANCES = config.DB_DIR / "facts_instances.parquet"
NOTES = config.CACHE / "datasets" / "notes"
LABELS = config.DB_DIR / "labels.parquet"
CAPACITY_UNITS = {"MW": "MW", "MWh": "MW", "megawatt": "MW", "GW": "GW", "gigawatt": "GW"}
MARK = "@@F[{}]@@"
MARK_RX = re.compile(r"@@F\[([^\]]+)\]@@")


def member_lab(local):
    """(laboratoire, complément) d'un nom local de membre ou de concept : `LAB:...` si un mot de la casse en
    chameau nomme un laboratoire ; complément vrai si « OtherThan », « Excluding » ou « Except » le précède,
    le laboratoire n'étant alors pas nommé (D-0060, point 3)."""
    m = LAB_WORD.search(local or "")
    if not m:
        return None, False
    if COMPLEMENT.search(local[:m.start()]):
        return None, True
    return LABS[m.group(1)], False


def fact_lab(concept, dims):
    """(laboratoire, membre, complément) d'un fait : premier membre de dimension qui nomme un laboratoire,
    à défaut un concept d'extension qui le nomme. `dims` : [[axe, membre], ...], préfixes compris ou non."""
    compl = False
    for _, mem in dims:
        if str(mem).startswith("typed:"):
            continue
        lab, c = member_lab(str(mem).split(":")[-1])
        if lab:
            return lab, mem, False
        compl = compl or c
    pre, _, local = (concept or "").rpartition(":")
    if pre not in STANDARD:
        lab, c = member_lab(local)
        if lab:
            return lab, None, False
        compl = compl or c
    return None, None, compl


def segments_dims(seg):
    """Segments des Notes Data Sets (« Axe=Membre;Axe=Membre; ») en [[axe, membre], ...]."""
    return [list(x.split("=", 1)) for x in (seg or "").split(";") if "=" in x]


def _nds_concept(tag, version):
    pre = str(version or "").split("/")[0]
    return f"{pre if pre in STANDARD else 'ext'}:{tag}"


def _date8(x):
    s = str(x or "").split(".")[0]
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) >= 8 and s[:8].isdigit() else None


def _dec(v):
    if v is None or (isinstance(v, float) and v != v):
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def instance_facts(path=INSTANCES):
    """Faits des instances en cache dont un membre (ou un concept d'extension) nomme un laboratoire."""
    import duckdb
    df = duckdb.connect().execute(f"""
        SELECT fact_key, group_id, cik, accession, form, filing_date, concept, dims, period_type, period_start, period_end,
               unit, value, value_text, decimals, fact_id, locator, tier, knowledge_date
        FROM '{path}' WHERE regexp_matches(dims, '(OpenAI|OPENAI|Anthropic|ANTHROPIC)')
                         OR regexp_matches(concept, '(OpenAI|OPENAI|Anthropic|ANTHROPIC)')
        ORDER BY accession, fact_key""").fetchdf()
    out = []
    for r in df.to_dict("records"):
        dims = json.loads(r["dims"] or "[]")
        lab, mem, compl = fact_lab(r["concept"], dims)
        out.append({**r, "source": "instance", "dims_list": dims, "lab": lab, "member": mem, "complement": compl,
                    "filer_name": None, "qtrs": None,
                    "filing_date": str(r["filing_date"])[:10] if r["filing_date"] is not None else None,
                    "knowledge_date": str(r["knowledge_date"])[:10] if r["knowledge_date"] is not None else None})
    return out


def nds_facts(root=NOTES):
    """Faits des extraits des Notes Data Sets en cache dont un segment nomme un laboratoire, une fois chacun
    (un même fait peut figurer dans deux archives)."""
    import duckdb
    con = duckdb.connect()
    rows, seen = [], set()
    for base in sorted(glob.glob(str(root / "*_notes"))):
        sub = f"{base}/sub.parquet"
        for part in ("", "nf/"):
            dp, npth = f"{base}/{part}dim.parquet", f"{base}/{part}num.parquet"
            if not (os.path.exists(dp) and os.path.exists(npth)):
                continue
            join_sub = f"LEFT JOIN '{sub}' s ON s.adsh = n.adsh" if os.path.exists(sub) else ""
            cols = "s.cik, s.name, s.form, s.filed" if join_sub else "NULL cik, NULL name, NULL form, NULL filed"
            df = con.execute(f"""
                SELECT n.adsh, {cols}, n.tag, n.version, n.ddate, n.qtrs, n.uom, n.iprx, n.value, n.dimh, d.segments
                FROM '{npth}' n JOIN '{dp}' d ON n.dimh = d.dimhash {join_sub}
                WHERE regexp_matches(d.segments, '(OpenAI|OPENAI|Anthropic|ANTHROPIC)')""").fetchdf()
            arch = os.path.basename(base) + ("/nf" if part else "")
            for r in df.to_dict("records"):
                fk = f"nds/{r['adsh']}/{r['tag']}/{r['version']}/{r['ddate']}/{r['qtrs']}/{r['uom']}/{r['dimh']}/{r['iprx']}"
                # même fait affiché deux fois (iprx) avec la même valeur : une fois
                same = (r["adsh"], r["tag"], r["version"], r["ddate"], r["qtrs"], r["uom"], r["dimh"], str(r["value"]))
                if fk in seen or same in seen:
                    continue
                seen.update((fk, same))
                dims = segments_dims(r["segments"])
                concept = _nds_concept(r["tag"], r["version"])
                lab, mem, compl = fact_lab(concept, dims)
                try:
                    q = int(float(r["qtrs"]))
                except (TypeError, ValueError):
                    q = None
                form = r["form"] or ""
                tier = "A" if form.startswith(("10-K", "20-F", "N-CSR")) else "B"
                kd = _date8(r["filed"])
                cik = r["cik"]
                cik = str(int(cik)).zfill(10) if cik is not None and cik == cik else None
                rows.append({"fact_key": fk, "group_id": None, "cik": cik,
                             "accession": r["adsh"], "form": form, "filing_date": kd, "concept": concept,
                             "dims": json.dumps(dims, separators=(",", ":")), "dims_list": dims,
                             "period_type": "instant" if q == 0 else "duration", "period_start": None,
                             "period_end": _date8(r["ddate"]), "unit": r["uom"], "value": r["value"], "value_text": None,
                             "decimals": None, "fact_id": None, "locator": f"{arch}:num.tsv", "tier": tier,
                             "knowledge_date": kd, "source": "nds", "lab": lab, "member": mem, "complement": compl,
                             "filer_name": r["name"], "qtrs": q, "archive": arch, "version": r["version"]})
    return rows


def retained(inst=None, nds=None):
    """(faits retenus, comptes) : un fait des Notes Data Sets d'un dépôt dont l'instance est en cache s'efface
    devant elle (D-0060, point 3) ; un membre de complément est compté, non retenu."""
    import duckdb
    inst = instance_facts() if inst is None else inst
    nds = nds_facts() if nds is None else nds
    inst_acc = {a for (a,) in duckdb.connect().execute(f"SELECT DISTINCT accession FROM '{INSTANCES}'").fetchall()} \
        if INSTANCES.exists() else {f["accession"] for f in inst}
    n_inst_dup = sum(1 for f in nds if f["accession"] in inst_acc)
    nds_kept = [f for f in nds if f["accession"] not in inst_acc]
    allf = inst + nds_kept
    kept = [f for f in allf if f["lab"]]
    stats = {"instance_facts": sum(1 for f in inst if f["lab"]), "instance_accessions": len({f["accession"] for f in inst if f["lab"]}),
             "nds_facts": len(nds), "nds_accessions": len({f["accession"] for f in nds}),
             "nds_in_instance": n_inst_dup, "nds_kept": sum(1 for f in nds_kept if f["lab"]),
             "complement": sum(1 for f in allf if f["complement"] and not f["lab"]),
             "by_filer": dict(Counter((f["group_id"] or f["filer_name"] or f["cik"]) for f in kept))}
    return kept, stats


def nds_fact_rows(facts):
    """Lignes de la table facts pour les faits retenus des Notes Data Sets (source `nds_num`), avec leur
    accession et leur emplacement dans l'archive, comme les faits des BDC (source `bdc_num`)."""
    out = []
    for f in facts:
        if f["source"] != "nds":
            continue
        v = _dec(f["value"])
        pre = f["concept"].split(":")[0]
        out.append({"fact_key": f["fact_key"], "source": "nds_num", "cik": f["cik"],
                    "entity_id": f"cik:{f['cik']}" if f["cik"] else None, "group_id": None, "accession": f["accession"],
                    "form": f["form"], "filing_date": f["filing_date"], "concept": f["concept"], "concept_ns": pre,
                    "taxonomy_version": f.get("version"), "period_type": f["period_type"], "period_start": None,
                    "period_end": f["period_end"], "unit": f["unit"], "currency": "USD" if f["unit"] == "USD" else None,
                    "dims": f["dims"], "n_dims": len(f["dims_list"]), "framework": "us_gaap", "reporting_scope": "as_reported",
                    "value": v, "value_text": None if v is not None else (str(f["value"]) if f["value"] is not None else None),
                    "decimals": None, "decimals_inf": None, "precision_known": False, "is_nil": False, "is_fixed_zero": False,
                    "locator": f["locator"], "is_tagged": True, "tier": f["tier"], "filing_status": "filed",
                    "assurance_level": "audited" if f["tier"] == "A" else "reviewed", "knowledge_date": f["knowledge_date"],
                    "fy": None, "fp": None})
    return out


def _labels():
    """Libellés de chaque membre par dépôt : rôles standard, court et documentation, réunis."""
    if not LABELS.exists():
        return {}
    lb = pd.read_parquet(LABELS)
    lb = lb[lb["label_role"].isin(["label", "terseLabel", "documentation"])]
    out = defaultdict(list)
    for a, c, t in zip(lb["accession"], lb["concept"], lb["label"]):
        if t and t not in out[(a, c)]:
            out[(a, c)].append(t)
    return {k: " | ".join(v) for k, v in out.items()}


def _subject(f, groups_by_cik, cik_group):
    """Groupe du déposant (config.yaml, puis découverte), sinon son CIK (tiers hors du graphe)."""
    if f.get("group_id"):
        return f["group_id"]
    c = f.get("cik")
    if c and groups_by_cik.get(c):
        return groups_by_cik[c]
    if c and cik_group:
        g = cik_group(c, f.get("period_end"))
        if g:
            return g
    return f"cik:{c}" if c else None


def registry_cik_group(reg):
    """Groupe d'un CIK par le registre des entités (déposants de la découverte), à une date."""
    by_cik = {}
    for eid, e in reg.entities.items():
        c = e.get("cik")
        if c is None or (isinstance(c, float) and c != c):
            continue
        s = str(c).split(".")[0]
        if s.isdigit():
            by_cik.setdefault(s.zfill(10), eid)

    def f(cik, date):
        eid = by_cik.get(str(cik).zfill(10))
        return reg.group_at(eid, date, "as_known") if eid else None
    return f


def _conflicts(f, obs_by_acc):
    """Lignes valides du même dépôt, même montant, citation qui nomme un laboratoire, contrepartie qui n'en est
    pas un (D-0060, point 3)."""
    v = _dec(f["value"])
    if v is None or f["unit"] != "USD" or v == 0:
        return []
    out = set()
    for o in obs_by_acc.get(f["accession"]) or []:
        a = _dec(o.get("amount"))
        if a is None or abs(a) != abs(v):
            continue
        if not LAB_NAME.search(o.get("quote") or "") or LAB_NAME.search(o.get("counterparty_name") or ""):
            continue
        out.add(o.get("counterparty_name"))
    return sorted(x for x in out if x)


def breakdown(f):
    dims = ";".join(f"{a}={m}" for a, m in f["dims_list"])
    q = f"|qtrs={f['qtrs']}" if f["source"] == "nds" and f["qtrs"] not in (None, 0) else ""
    return f"{f['concept']}|{dims}{q}"


def tagged_value_cells(facts, reg, obs, as_of, groups_by_cik=None):
    """lab_tagged_value : une cellule par fait retenu, valeur et unité telles que balisées (D-0060, point 3)."""
    groups_by_cik = groups_by_cik or {}
    cik_group = registry_cik_group(reg) if reg is not None else None
    labels = _labels()
    obs_by_acc = defaultdict(list)
    for o in obs:
        if o.get("kind") == "observation" and o.get("validation_state") == "valid" and o.get("amount") is not None:
            obs_by_acc[o["accession"]].append(o)
    out, seen = [], {}
    for f in sorted(facts, key=lambda x: (x["accession"], x["fact_key"])):
        subj = _subject(f, groups_by_cik, cik_group)
        if not subj:
            continue
        v = _dec(f["value"])
        bk = breakdown(f)
        ps = f["period_start"] if f["period_type"] == "duration" else None
        key = (subj, f["lab"], str(ps), str(f["period_end"]), bk)
        if key in seen:
            if seen[key] == str(v):     # même fait publié deux fois dans le même dépôt (identifiants distincts)
                continue
            # même contexte, autre valeur : les deux se publient, la seconde distinguée par sa valeur
            bk, key = f"{bk}|value={v}", (*key[:4], f"{bk}|value={v}")
        seen[key] = str(v)
        fl = {"accession": f["accession"], "form": f["form"], "source": f["source"], "member": f["member"],
              "member_label": labels.get((f["accession"], f["member"])) if f["member"] else None,
              "filer_name": f["filer_name"], "qtrs": f["qtrs"], "period_type": f["period_type"],
              "outside_graph": subj.startswith("cik:")}
        cf = _conflicts(f, obs_by_acc)
        if cf:
            fl["conflict"] = cf
        term = {"fact_key": f["fact_key"], "value": str(v) if v is not None else "0", "tier": f["tier"],
                "knowledge_date": f["knowledge_date"], "is_tagged": True}
        out.append(cell("lab_tagged_value", subj, ps, f["period_end"], "as_known", as_of, breakdown=bk, value=v,
                        unit=f["unit"], counterparty=f["lab"], terms=[term], knowledge_date=f["knowledge_date"],
                        value_text=None if v is not None else (f.get("value_text") or None),
                        flags={k: x for k, x in fl.items() if x not in (None, False)}))
    return out


# --- volet 3 : unités du montage `labs_tagged` -------------------------------------------------------------------

def _primary_docs(accessions):
    d = pd.read_parquet(config.TABLES / "documents.parquet",
                        columns=["cik", "group_id", "accession", "document", "form", "filing_date", "resource_kind"])
    d = d[d["accession"].isin(accessions) & (d["resource_kind"] == "primary_document")]
    return {a: r for a, r in zip(d["accession"], d.to_dict("records"))}


def mark_facts(raw, fact_ids):
    """Le HTML avec un marqueur juste après la balise ouvrante de chaque fait : le linéariseur le garde dans le
    paragraphe qui porte le fait ; un fait masqué (`ix:hidden`) n'en a pas (D-0060, point 4)."""
    want = set(fact_ids)

    def rep(m):
        fid = m.group(2).decode()
        return m.group(0) + MARK.format(fid).encode() if fid in want else m.group(0)
    return re.sub(rb'<ix:(nonFraction|nonNumeric)\b[^>]*?\bid="([^"]+)"[^>]*>', rep, raw)


def _cand(f, labels, acc):
    dl = [[a, m, labels.get((acc, m))] for a, m in json.loads(f["dims"] or "[]")]
    return {"fact_key": f["fact_key"], "concept": f["concept"], "value": str(f["value"]), "unit": f.get("unit"),
            "period_start": str(f.get("period_start") or ""), "period_end": str(f.get("period_end") or ""),
            "dims": json.dumps(dl) if dl else "[]", "decimals": f.get("decimals")}


def prepare_units(mid, spec, groups_by_cik):
    """Blocs du montage `labs_tagged` : fenêtres de deux paragraphes autour de chaque paragraphe qui porte un fait
    retenu, du dépôt le plus récent au plus ancien ; faits candidats : ceux balisés dans la fenêtre, avec les
    libellés de leurs membres (D-0060, point 4)."""
    import duckdb
    from . import blocks, cache
    from . import discovery as D
    from . import montages as M
    _, docs_path, info_path = M._paths(mid)
    facts, st = retained()
    inst = [f for f in facts if f["source"] == "instance"]
    lab_ids = defaultdict(set)
    for f in inst:
        lab_ids[f["accession"]].add(f["fact_id"])
    docs = _primary_docs(set(lab_ids))
    labels = _labels()
    con = duckdb.connect()
    read_by_acc = M.read_texts(mid) if spec.get("skip_read") else {}
    units, hidden, risk, already, no_doc = [], [], [], [], []
    meta = json.loads((config.DB_DIR / "phase0.json").read_text())["meta"]
    rows_docs = []
    for acc in sorted(lab_ids):
        d = docs.get(acc)
        if d is None:
            no_doc.append(acc)
            continue
        path = cache.archive_path(d["cik"], acc, d["document"])
        if not path.exists():
            no_doc.append(acc)
            continue
        allf = con.execute(f"""SELECT fact_key, fact_id, concept, value, unit, period_start, period_end, dims, decimals
                               FROM '{INSTANCES}' WHERE accession = ? AND fact_id IS NOT NULL
                                 AND concept NOT LIKE '%TextBlock'""", [acc]).fetchdf().to_dict("records")
        by_id = {}
        for f in allf:
            by_id.setdefault(f["fact_id"], []).append(f)
        raw = mark_facts(cache.read(path), by_id.keys())
        text, how = D.plain_text(raw)
        paras_m = M.paragraphs(text)
        paras = [MARK_RX.sub("", p).strip() for p in paras_m]
        ids_in = [set(MARK_RX.findall(p)) for p in paras_m]
        carriers = [i for i, ids in enumerate(ids_in) if ids & lab_ids[acc]]
        seen_ids = set().union(*ids_in) if ids_in else set()
        hidden += [{"adsh": acc, "fact_id": x} for x in sorted(lab_ids[acc] - seen_ids)]
        filer = (meta.get(d["cik"]) or {}).get("name") or d["group_id"]
        fd = str(d["filing_date"])[:10]
        rows_docs.append({"adsh": acc, "file": d["document"], "form": d["form"], "file_type": d["form"], "file_date": fd,
                          "cik": d["cik"], "filer": filer, "source": "tagged", "queries": "", "state": "cached"})
        spans = []
        for i in carriers:
            a, b = max(0, i - M.WINDOW), min(len(paras), i + M.WINDOW + 1)
            if spans and a <= spans[-1][1]:
                spans[-1][1] = max(spans[-1][1], b)
            else:
                spans.append([a, b])
        rf = M.risk_factor_span(paras) if spec.get("skip_risk_factors") else None
        texts = read_by_acc.get(acc) or []
        for k, (a, b) in enumerate(spans):
            hits = [i for i in carriers if a <= i < b]
            ref = {"adsh": acc, "file": d["document"], "form": d["form"], "filer": filer, "window": k}
            if rf and all(rf[0] <= i < rf[1] for i in hits):
                risk.append(ref)
                continue
            if texts and all(M.covered(paras[i], texts) for i in hits):
                already.append(ref)
                continue
            ids = set().union(*ids_in[a:b])
            cands = [_cand(f, labels, acc) for fid in sorted(ids) for f in by_id.get(fid, [])]
            dd = {**rows_docs[-1]}
            units.append((dd, k, "\n".join(p for p in paras[a:b] if p), how, cands,
                          sorted(set().union(*(ids_in[i] for i in hits)) & lab_ids[acc])))
    pd.DataFrame(rows_docs).to_parquet(docs_path, index=False)
    units.sort(key=lambda u: M._order_key(u[0], u[1], spec))
    seen, kept, dup = set(), [], []
    for u in units:
        ck = blocks.content_key(u[2], [])
        if spec.get("dedupe") and ck in seen:
            dup.append({"adsh": u[0]["adsh"], "file": u[0]["file"], "window": u[1]})
            continue
        seen.add(ck)
        kept.append(u)
    noted = M.noted_rx(spec)
    from . import update
    # plafond d'une exécution à l'autre (D-0074, point 3) : les fenêtres déjà au catalogue y restent
    adm = update.admission(spec["cap"], update.catalog_keys(M.CATALOG, where=lambda b: b.get("montage") == mid))
    out, over = [], []
    for n, (d, k, text, how, cands, lab_fids) in enumerate(kept):
        ck = blocks.content_key(text, cands)
        if not adm.take(ck, d["file_date"]):
            over.append({"adsh": d["adsh"], "file": d["file"], "window": k})
            continue
        grp = groups_by_cik.get(d["cik"]) or d["filer"]
        tier, assurance, status = M.evidence(d, spec)          # triplet pour une pièce de 8-K (D-0066, point 5)
        fd = d["file_date"]
        out.append({"content_key": ck, "block_kind": "montage_text", "signal_class": 5,
                    "sort_key": f"mt:{mid}:{n:05d}", "group_id": grp, "cik": d["cik"], "accession": d["adsh"],
                    "form": d["form"], "filing_date": fd, "acceptance": None, "knowledge_date": fd,
                    "period_start": None, "period_end": fd, "document": d["file"],
                    "locator": {"file": d["file"], "accession": d["adsh"], "cik": d["cik"], "byte_range": None},
                    "text": text, "candidate_facts": cands, "chars": len(text),
                    "normalizer_version": config.NORMALIZER_VERSION, "delimiter_version": config.DELIMITER_VERSION,
                    "filing_status": status, "assurance_level": assurance, "tier": tier, "filer_name": d["filer"],
                    "exhibit_type": d["file_type"], "window": k, "text_extraction": how,
                    "terms": sorted(set(noted.findall(text))), "queries": "", "montage": mid,
                    "lab_fact_ids": lab_fids})
    info = {"source": "tagged", "facts": st, "accessions": len(lab_ids), "documents": len(rows_docs),
            "no_document": no_doc, "hidden_facts": hidden, "windows": len(units) + len(already) + len(risk),
            "units": len(units),
            "duplicates": dup, "risk_factors": risk, "already_read": already, "over_cap": over, "no_window": [],
            "excluded": []}
    info_path.write_text(json.dumps(info, ensure_ascii=False, default=str))
    print(mid, ":", len(lab_ids), "dépôts ;", len(units) + len(already) + len(risk), "fenêtres ;", len(kept), "textes distincts ;",
          len(out), "blocs ;", len(already), "déjà lues ;", len(risk), "dans un facteur de risque ;", len(hidden),
          "faits masqués ;", len(over), "au-delà du plafond")
    return out


# --- volet 4 : grand livre -----------------------------------------------------------------------------------------

def is_lab(g):
    return str(g or "").startswith("LAB:")


def ledger_cells(edges, as_of):
    """lab_ledger : pour chaque partenaire d'un laboratoire, une cellule par instrument, sens, famille, type,
    nature de montant, base et unité, au dernier montant admissible connu, avec sa pièce (D-0060, point 6)."""
    groups = defaultdict(list)
    for e in edges:
        if e.get("link_kind", "edge") != "edge" or e.get("elimination_status") == "eliminated":
            continue
        fg, tg = e.get("from_group"), e.get("to_group")
        if is_lab(fg) == is_lab(tg) or fg is None or tg is None:
            continue
        lab, partner, direction = (tg, fg, "to_lab") if is_lab(tg) else (fg, tg, "from_lab")
        if e.get("amount") is None or e.get("_date") is None:
            continue
        o = e.get("_obs") or {}
        inst = e.get("instrument_key") or f"edge:{e['link_key']}"
        key = (partner, lab, direction, e.get("family"), e.get("edge_type"), inst, e.get("amount_nature") or NONE,
               o.get("measurement_basis") or NONE, e.get("unit") or NONE)
        groups[key].append(e)
    out = []
    for key, es in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        partner, lab, direction, fam, et, inst, nat, basis, unit = key
        # à date égale, une arête close ne passe pas pour le dernier montant d'une arête en vigueur (bons déchus le
        # jour où le bon refondu est remis ; D-0067, point 17)
        es = sorted(es, key=lambda e: (str(e["_date"]), str(e.get("knowledge_date") or ""), e.get("stage") != "terminated",
                                       e["link_key"]))
        last = es[-1]
        o = last.get("_obs") or {}
        same_day = [e for e in es if str(e["_date"]) == str(last["_date"])
                    and str(e.get("knowledge_date") or "") == str(last.get("knowledge_date") or "")]
        amt = _dec(last["amount"])
        pe = str(last["_date"])[:10]
        ps = o.get("period_start") if o.get("period_end") and str(o.get("period_end"))[:10] == pe else None
        bk = "|".join(str(x) for x in (direction, fam, et, inst, nat, basis, unit))
        fl = {"direction": direction, "family": fam, "edge_type": et, "instrument_key": None if inst.startswith("edge:") else inst,
              "amount_nature": nat, "measurement_basis": basis, "accession": o.get("accession"), "form": o.get("form"),
              "stage": last.get("stage"), "event_type": o.get("event_type"), "n_amounts": len(es),
              "distinct_amounts": len({str(_dec(e["amount"])) for e in es}), "first_date": str(es[0]["_date"])[:10],
              "link_key": last["link_key"], "source_perspective": last.get("source_perspective"),
              "filer": o.get("group_id"), "same_date_other_amounts": len({str(_dec(e["amount"])) for e in same_day}) - 1}
        term = {"fact_key": "obs:" + o["obs_key"] if o.get("obs_key") else last["link_key"], "value": str(amt),
                "tier": last.get("tier"), "knowledge_date": last.get("knowledge_date"), "is_tagged": False}
        out.append(cell("lab_ledger", partner, ps, pe, "as_known", as_of, breakdown=bk, value=amt, unit=unit,
                        counterparty=lab, terms=[term], knowledge_date=last.get("knowledge_date"),
                        flags={k: x for k, x in fl.items() if x not in (None, "")}))
    return out


def inventory():
    facts, st = retained()
    print(json.dumps(st, ensure_ascii=False, indent=1))
    print(Counter((f["source"], f["lab"]) for f in facts))


if __name__ == "__main__":
    if (sys.argv[1] if len(sys.argv) > 1 else "") == "inventory":
        inventory()
    else:
        print(__doc__)
