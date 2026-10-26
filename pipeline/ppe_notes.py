"""D-0076 : composition des en-cours et des actifs pas encore en service, telle que l'écrivent les notes.

Source `ppe_notes` du montage `ppe_components` (point 4) : les notes des rapports périodiques à instance XBRL (blocs de
texte sans dimension des rôles de note, normalisés comme le catalogue `text`) et celles des documents d'enregistrement
de `registration_text`. Un paragraphe qualifie s'il nomme un terme du lexique (`terms` du montage) ; un renvoi de bas
de tableau se rattache à sa ligne par sa marque ; une fenêtre prend un paragraphe de part et d'autre ; une fenêtre de
seules lignes d'en-cours nues n'est pas servie, son montant étant balisé. Faits candidats : ceux des rôles de détail et
de tableau de la note. Ligne de composante (point 5) et mesure descriptive `ppe_component_disclosed` (point 6) : aucune
arithmétique sur un chiffre lu.
"""
import io
import json
import re
import zipfile
from collections import Counter

NONE = "none"
SEP = " | "                      # séparateur des cellules d'une ligne de tableau (textnorm)
_MARK = r"\(\s*([a-z0-9]{1,2})\s*\)|(\*{1,3})|\[([a-z0-9]{1,2})\]"
ROW_MARK = re.compile(_MARK, re.I)
ONLY_MARK = re.compile(r"\s*(?:" + _MARK + r")\s*", re.I)
FOOT = re.compile(r"^\s*(?:\(\s*([a-z0-9]{1,2})\s*\)|([a-z0-9]{1,2})\)|(\*{1,3})|\[([a-z0-9]{1,2})\])\s*\S", re.I)
CIP_NAME = (r"construction[\s-]+in[\s-]+pro(?:gress|cess)|constructions?[\s-]+in[\s-]+progress|"
            r"assets?\s+under\s+construction")
BARE = re.compile(r"^\s*(?:" + CIP_NAME + r")\s*(?:,?\s*(?:net|gross))?\s*$", re.I)

# mots qu'une citation doit contenir pour une composante ou un état (point 5) ; rien pour `unspecified`
COMPONENT_WORDS = {
    "it_equipment": r"server|network|\bGPUs?\b|computer|comput|\bIT\b|information technology|hardware",
    "mining_equipment": r"\bminers?\b|mining|\bASICs?\b",
    "manufacturing_equipment": r"\btools?\b|tooling|machinery|manufactur|production|\bfabs?\b",
    "facilities": r"building|data ?cent(?:er|re)|facilit|leasehold|\bsites?\b|campus|infrastructure",
    "software": r"software",
    "land": r"\bland\b",
}
STATE_WORDS = {
    "not_in_service": r"service|\buse\b|\bin use\b|install|deploy|operation|ready",
    "under_construction": r"construct|build|develop|progress|process",
    "at_suppliers": r"supplier|vendor|manufacturer",
    "in_transit": r"transit",
    "prepaid": r"deposit|prepa|advance",
}
COMPONENT_FIELDS = ("asset_component", "asset_state", "component_of", "component_statement")


# -- renvois, fenêtres -------------------------------------------------------------------------------------------

def _first_cell(p):
    return p.split(SEP)[0]


def _mark(m):
    return next(g for g in m.groups() if g).lower()


def foot_mark(p):
    """Marque d'un renvoi : paragraphe hors tableau ouvert par « (1) », « 1) », « * » ou « [1] », ou ligne de tableau
    dont la première cellule n'est que la marque ; sinon None."""
    if SEP in p:
        m = ONLY_MARK.fullmatch(_first_cell(p))
        return _mark(m) if m else None
    m = FOOT.match(p)
    return _mark(m) if m else None


def row_marks(p):
    """Marques que porte la première cellule d'une ligne de tableau (« Equipment (1) »)."""
    if SEP not in p or foot_mark(p):
        return set()
    return {_mark(m) for m in ROW_MARK.finditer(_first_cell(p))}


def bare_row(p):
    """Ligne de tableau dont la première cellule, marques ôtées, n'est que le terme d'en-cours (« net », « gross »)."""
    return SEP in p and BARE.match(ROW_MARK.sub("", _first_cell(p))) is not None


def qualifying(paras, rx):
    """Paragraphes qualifiants (point 4) : ceux qui nomment un terme du lexique ; une ligne marquée amène le premier
    renvoi qui la suit, un renvoi la ligne marquée la plus proche avant lui (un seul pas)."""
    hits = [i for i, p in enumerate(paras) if rx.search(p)]
    q = set(hits)
    for i in hits:
        fm = foot_mark(paras[i])
        if fm:
            j = next((j for j in range(i - 1, -1, -1) if fm in row_marks(paras[j])), None)
            if j is not None:
                q.add(j)
        for m in sorted(row_marks(paras[i])):
            j = next((j for j in range(i + 1, len(paras)) if foot_mark(paras[j]) == m), None)
            if j is not None:
                q.add(j)
    return sorted(q)


def units(paras, rx, width=1):
    """Fenêtres servies [(début, fin, paragraphes qualifiants)] et nombre de fenêtres de seules lignes d'en-cours nues,
    non servies : `width` paragraphes de part et d'autre de chaque paragraphe qualifiant, fondues quand elles se
    touchent."""
    q = qualifying(paras, rx)
    spans = []
    for i in q:
        a, b = max(0, i - width), min(len(paras), i + width + 1)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    out, bare = [], 0
    for a, b in spans:
        qi = [i for i in q if a <= i < b]
        if all(bare_row(paras[i]) for i in qi):
            bare += 1
            continue
        out.append((a, b, qi))
    return out, bare


def role_title(rdef):
    """Titre d'un rôle : sa définition après « NNNN - Disclosure - », avant « (Details) », « (Tables) », « (Policies) »
    ou « - » ; en minuscules."""
    t = (rdef or "").split(" - ", 2)[-1]
    t = re.split(r"\s*\((?:details?|tables|policies|narrative)", t, flags=re.I)[0]
    return t.split(" - ")[0].strip().lower()


def lexicon(spec):
    return re.compile("|".join(t["rx"] for t in spec["terms"]), re.I)


# -- corpus ------------------------------------------------------------------------------------------------------

def periodic_notes():
    """Notes des rapports périodiques à instance XBRL, une à une : (dépôt, instance, concept, définition du rôle de la
    note, texte normalisé, emplacement, concepts des rôles de détail et de tableau de même titre)."""
    import pandas as pd
    from . import blocks, cache, config, textnorm, xbrl
    from .catalog import _cache_member, _filing
    from .edgar import cik10
    from .text_catalog import iter_periodic
    tags = pd.read_parquet(config.DB_DIR / "tags.parquet", columns=["accession", "concept", "xbrltype"])
    tb_by = {a: set(g[g["xbrltype"].fillna("").str.endswith("textBlockItemType")]["concept"])
             for a, g in tags.groupby("accession")}
    for r, d in iter_periodic():
        acc, cik = r["accessionNumber"], r["filer_cik"]
        zb = cache.read(cache.archive_path(cik10(cik), acc, d["zip"])) if d["zip"] else None
        files = {}
        if zb:
            with zipfile.ZipFile(io.BytesIO(zb)) as zf:
                files = {n: zf.read(n) for n in zf.namelist() if n.lower().endswith((".xsd", ".xml"))}
        inst = d["instance"]
        raw = _cache_member(cik, acc, inst, zb)
        if raw is None:
            yield {"accession": acc, "missing": True}
            continue
        lb = xbrl.parse_linkbases({n: b for n, b in files.items() if n not in (inst, "FilingSummary.xml")})
        kinds = {role: xbrl.statement_kind(rdef) for role, rdef in lb["roles"].items()}
        note_of = {}                         # concept de bloc de texte -> définition du rôle de note qui le porte
        for role in sorted(lb["pres"]):
            if kinds.get(role) != "note":
                continue
            for c in sorted(blocks.concepts_in_roles(lb, [role])):
                note_of.setdefault(c, lb["roles"][role])
        tb = (tb_by.get(acc) or set()) & set(note_of)
        try:
            _, tblocks, _ = xbrl.parse_instance(raw, tb or None)
        except Exception:
            yield {"accession": acc, "parse_failed": True}
            continue
        f = _filing(r)
        for t in sorted(tblocks, key=lambda t: t["occ_rank"]):
            if t["dims"] or t["concept"] not in note_of or (tb and t["concept"] not in tb):
                continue
            text = textnorm.lines_to_text(textnorm.html_fragment_lines(t["text"]))
            if not text.strip():
                continue
            rdef = note_of[t["concept"]]
            title = role_title(rdef)
            det = [role for role, k in kinds.items() if k in ("note_details", "note_tables")
                   and role_title(lb["roles"][role]) == title]
            yield {"filing": f, "instance": inst, "concept": t["concept"], "role": rdef, "text": text,
                   "byte_range": blocks._fact_byte_range(raw, t.get("fact_id")),
                   "detail_concepts": blocks.concepts_in_roles(lb, det)}


def registration_notes():
    """Notes des jeux d'états financiers des documents de `registration_text` (D-0057, point 14), toutes notes."""
    from . import cache, config, regdoc
    from .catalog import _filing
    idx = {r["accession"]: r for r in json.loads((config.DB_DIR / "filing_index.json").read_text())}
    for spec in regdoc.specs():
        r = idx[spec["accession"]]
        raw = cache.read(cache.archive_path(r["cik"], r["accession"], spec["primary"]))
        sets = regdoc.note_sets(raw)
        if len(sets) != len(spec["note_sets"]):
            raise ValueError(f"{spec['accession']} : {len(sets)} jeux de notes découpés, {len(spec['note_sets'])} fixés")
        for s, st in zip(sets, spec["note_sets"]):
            f = dict(_filing(r), period_start=st["period_start"], report_date=st["period_end"])
            for n in s["notes"]:
                yield {"filing": f, "instance": spec["primary"], "concept": None,
                       "role": f"{st['label']} — note {n['number']}. {n['title']}", "text": n["text"], "byte_range": None,
                       "detail_concepts": set(), "assurance": st["assurance"]}


def evidence(form, assurance=None):
    """Niveau de preuve d'une fenêtre : celui des notes du catalogue `text` (rapport annuel : audité, A ; trimestriel :
    revu, B) ; pour un document d'enregistrement, l'assurance de son jeu de notes (audité A, sinon C)."""
    from .catalog import is_annual
    if assurance is not None:
        return ("filed", "audited", "A") if assurance == "audited" else ("filed", "unaudited", "C")
    return ("filed", "audited", "A") if is_annual(form) else ("filed", "reviewed", "B")


def prepare_units(mid, spec, groups_by_cik):
    """Blocs du montage `ppe_components` (D-0076, point 4), des dépôts les plus anciens aux plus récents."""
    import pandas as pd
    from . import blocks, config, reader, update
    from . import montages as M
    _, docs_path, info_path = M._paths(mid)
    new = M.is_new(mid)
    rx = lexicon(spec)
    noted = M.noted_rx(spec)
    facts = pd.read_parquet(config.DB_DIR / "facts_instances.parquet",
                            columns=["fact_key", "accession", "concept", "value", "unit", "period_type", "period_start",
                                     "period_end", "dims", "decimals", "is_nil"])
    facts = facts[facts["value"].notna() & ~facts["is_nil"].fillna(False) & facts["period_type"].eq("instant")]
    facts_by = dict(tuple(facts.groupby("accession")))
    labels = pd.read_parquet(config.DB_DIR / "labels.parquet")
    labels = labels[labels["label_role"].isin(["label", "terseLabel"])]
    lab_by = {a: dict(zip(g["concept"], g["label"])) for a, g in labels.groupby("accession")}
    read_by_acc = M.read_texts(mid)
    st, units_, docs = Counter(), [], []
    for src in (periodic_notes, registration_notes):
        for n in src():
            if n.get("missing") or n.get("parse_failed"):
                st["instance_missing" if n.get("missing") else "parse_failed"] += 1
                continue
            st["notes"] += 1
            f = n["filing"]
            paras = M.paragraphs(n["text"])
            ws, bare = units(paras, rx, spec.get("window", 1))
            st["bare_windows"] += bare
            if not ws:
                if bare:                 # en-cours en ligne nue seulement : compté, pour le rendu (point 8)
                    docs.append({"adsh": f["accession"], "file": n["instance"], "form": f["form"],
                                 "file_date": f["filing_date"], "cik": f["cik"], "group_id": f["group_id"],
                                 "concept": n["concept"], "role": n["role"], "windows": 0, "bare_windows": bare})
                continue
            st["notes_named"] += 1
            acc = f["accession"]
            fa = facts_by.get(acc)
            cands = [] if fa is None or not n["detail_concepts"] else \
                [blocks._cand(x, lab_by.get(acc, {})) for x in fa[fa["concept"].isin(n["detail_concepts"])].to_dict("records")]
            texts = read_by_acc.get(acc) or []
            docs.append({"adsh": acc, "file": n["instance"], "form": f["form"], "file_date": f["filing_date"],
                         "cik": f["cik"], "group_id": f["group_id"], "concept": n["concept"], "role": n["role"],
                         "windows": len(ws), "bare_windows": bare})
            for k, (a, b, qi) in enumerate(ws):
                text = "\n".join(paras[a:b])
                reading = "complement" if texts and all(M.covered(paras[i], texts) for i in qi) else "complete"
                units_.append((f, n, k, text, cands, reading))
    pd.DataFrame(docs).to_parquet(docs_path, index=False)
    units_.sort(key=lambda u: (u[0]["filing_date"], u[0]["accession"]))     # stable : notes et fenêtres dans leur ordre
    seen, kept, dup = set(), [], []
    for u in units_:                   # un texte distinct se lit une fois (D-0049, point 11)
        tk = blocks.content_key(u[3], [])
        if tk in seen:
            dup.append({"adsh": u[0]["accession"], "file": u[1]["instance"], "window": u[2]})
            continue
        seen.add(tk)
        kept.append(u)
    known = {b["content_key"] for b in reader.load_catalog() if b.get("montage") != mid}
    # montage nouveau : préparé sur toute sa période (point 4) ; sinon, plafond d'une exécution à l'autre (D-0074)
    adm = update.Admission(spec["cap"], update.catalog_keys(M.CATALOG, where=lambda b: b.get("montage") == mid),
                           None if new else config.previous_as_of())
    out, over = [], []
    for n_, (f, n, k, text, cands, reading) in enumerate(kept):
        if blocks.content_key(text, cands) in known:     # texte déjà bloc d'un autre catalogue (D-0068, point 15)
            text = f"[D-0076, point 4 : paragraphes du bloc {blocks.content_key(text, cands)[:12]}]\n" + text
        status, assurance, tier = evidence(f["form"], n.get("assurance"))
        b = blocks._block("montage_text", f, text, cands, n["instance"], n["byte_range"],
                          note_label=(f"{n['concept']} | {n['role']}" if n["concept"] else n["role"]))
        if not adm.take(b["content_key"], f["filing_date"]):
            over.append({"adsh": f["accession"], "file": n["instance"], "window": k})
            continue
        b.update({"signal_class": 5, "sort_key": f"mt:{mid}:{n_:05d}", "group_id": f["group_id"] or groups_by_cik.get(f["cik"]),
                  "acceptance": None if f.get("acceptance") is None else str(f["acceptance"]),
                  "filing_status": status, "assurance_level": assurance, "tier": tier, "filer_name": None,
                  "exhibit_type": None, "window": k, "text_extraction": "xbrl_text_block" if n["concept"] else "html_notes",
                  "terms": sorted(set(noted.findall(text))), "queries": "", "montage": mid, "reading": reading,
                  "party": False})
        out.append(b)
    prev = json.loads(info_path.read_text()) if info_path.exists() else {}
    info = {"source": "ppe_notes", "first_as_of": prev.get("first_as_of") or config.as_of(), **dict(st),
            "windows": len(units_), "units": len(kept), "blocks": len(out), "duplicates": dup, "over_cap": over,
            "no_window": [], "excluded": [], "risk_factors": [], "already_read": [],
            "complete": sum(1 for b in out if b["reading"] == "complete"),
            "complement": sum(1 for b in out if b["reading"] == "complement")}
    info_path.write_text(json.dumps(info, ensure_ascii=False, default=str))
    print(mid, ":", st["notes"], "notes ;", st["notes_named"], "qui nomment un terme ;", len(units_), "fenêtres ;",
          len(kept), "textes distincts ;", len(out), "blocs ;", st["bare_windows"], "fenêtres de lignes nues non servies ;",
          len(over), "au-delà du plafond ; lecture complète", info["complete"], ", complémentaire", info["complement"])
    return out


def corpus_stats(catalog, mid="ppe_components"):
    """Par groupe (point 8) : notes qui nomment un terme avec une fenêtre servie, notes de seules lignes d'en-cours
    nues, blocs du montage et blocs lus."""
    import pandas as pd
    from . import config
    from . import montages as M
    p = M._paths(mid)[1]
    out = {}
    if p.exists():
        d = pd.read_parquet(p)
        for g, x in d.groupby("group_id"):
            out[g] = {"notes_named": int((x["windows"] > 0).sum()),
                      "bare_only_notes": int(((x["windows"] == 0) & (x["bare_windows"] > 0)).sum()), "blocks": 0, "read": 0}
    for b in catalog:
        if b.get("montage") != mid:
            continue
        s = out.setdefault(b["group_id"], {"notes_named": 0, "bare_only_notes": 0, "blocks": 0, "read": 0})
        s["blocks"] += 1
        s["read"] += int((config.OBS_DIR / f"{b['content_key']}.jsonl").exists())
    return out


# -- lignes de composante et mesure ------------------------------------------------------------------------------

def is_component_line(o):
    return any(o.get(k) not in (None, NONE) for k in COMPONENT_FIELDS)


def schema_errors(line):
    """Contrôles du lecteur pour une ligne de composante (point 7)."""
    if not is_component_line(line):
        return []
    errs = []
    if any(line.get(k) in (None, NONE) for k in COMPONENT_FIELDS):
        errs.append("une ligne de composante porte ses quatre champs : composante, état, poste et énoncé (D-0076, point 7)")
    if line.get("family") not in (None, NONE):
        errs.append("une ligne de composante est descriptive : sans famille (D-0076, point 5)")
    st = line.get("component_statement")
    if st == "amount" and line.get("amount") is None:
        errs.append("un énoncé `amount` porte son montant (D-0076, point 5)")
    if st in ("primarily", "includes") and line.get("amount") is not None:
        errs.append("un énoncé `primarily` ou `includes` ne porte aucun montant (D-0076, point 5)")
    if not line.get("period_end"):
        errs.append("une ligne de composante porte sa date (period_end) (D-0076, point 5)")
    return errs


def semantic_errors(line):
    """La citation nomme la composante et l'état choisis (point 5) ; rien pour `unspecified`."""
    if not is_component_line(line):
        return []
    q = line.get("quote") or ""
    errs = []
    w = COMPONENT_WORDS.get(line.get("asset_component"))
    if w and not re.search(w, q, re.I):
        errs.append(f"composante {line['asset_component']} sans mot qui la nomme dans la citation (D-0076, point 5)")
    w = STATE_WORDS.get(line.get("asset_state"))
    if w and not re.search(w, q, re.I):
        errs.append(f"état {line['asset_state']} sans mot qui le dise dans la citation (D-0076, point 5)")
    return errs


def breakdown(o):
    return "|".join(str(o.get(k)) for k in ("component_of", "asset_component", "asset_state", "component_statement"))


def cip_lookup(con):
    """En-cours balisé d'un groupe à une date, connu à une date de coupure (grandeur `construction_in_progress`) :
    (terme ou None, motif d'absence)."""
    import datetime as dt
    from . import model
    from .measures import Series
    occ, cals, series = model.occurrences_df(con), model.calendars(), {}
    cip = occ[occ["quantity"] == "construction_in_progress"]
    unit_of = dict(zip(cip["fact_key"], cip["unit"]))         # devise du fait, telle que balisée

    def at(g, pe, cutoff):
        if g not in cals:
            return None, "concept_unresolved"
        if g not in series:
            series[g] = Series(occ, g, cals[g])
        S = series[g]
        if not S.has("construction_in_progress"):
            return None, "concept_unresolved"
        t = S.instant("construction_in_progress", dt.date.fromisoformat(pe), dt.date.fromisoformat(cutoff))
        if t:
            t["unit"] = unit_of.get(t["fact_key"])
        return t, None if t else "not_disclosed"
    return at


def component_cells(obs, cip_at, as_of):
    """`ppe_component_disclosed` (point 6). Terme `component` : une cellule par groupe, date et clé, vue `as_known`
    (ligne du premier dépôt qui écrit la clé à cette date) et `revised` (celle du dernier) ; le montant écrit, jamais
    divisé ni additionné. Terme `cip_tagged` : à chaque groupe et date qui ont une ligne, l'en-cours balisé à cette
    date, connu à la date de la première ligne ou à l'as_of (`cip_at(groupe, date, coupure)`), pour l'affichage."""
    from decimal import Decimal
    from .measures import cell
    lines = [o for o in obs if o.get("kind") == "observation" and o.get("validation_state") == "valid"
             and is_component_line(o) and o.get("period_end") and (o.get("tier") or "") != "E"]
    by = {}
    for o in lines:
        by.setdefault((o["group_id"], str(o["period_end"])[:10], breakdown(o)), []).append(o)
    out, first = [], {}
    for (g, pe, bk), ls in sorted(by.items()):
        ls = sorted(ls, key=lambda o: (str(o.get("knowledge_date")), o["obs_key"]))
        k = str(ls[0].get("knowledge_date"))[:10]
        first[(g, pe)] = min(first.get((g, pe), k), k)
        for view, o in (("as_known", ls[0]), ("revised", ls[-1])):
            amt = Decimal(str(o["amount"])) if o.get("amount") is not None else None
            tagged = o.get("amount_origin") == "tagged_reference"
            terms = [{"value": amt, "fact_key": "obs:" + o["obs_key"], "knowledge_date": o.get("knowledge_date"),
                      "tier": o.get("tier"), "is_tagged": tagged}] if amt is not None else []
            flags = {"observations": [x["obs_key"] for x in ls], "quote": o.get("quote"), "accession": o.get("accession"),
                     "form": o.get("form"), "amount_origin": o.get("amount_origin"),
                     "amount_qualifier": o.get("amount_qualifier"), "is_tagged": tagged}
            c = cell("ppe_component_disclosed", g, None, pe, view, as_of, term="component", breakdown=bk, value=amt,
                     value_text=None if amt is not None else o["component_statement"],
                     unit=o.get("unit") if amt is not None else None, terms=terms,
                     knowledge_date=o.get("knowledge_date"), flags=flags)
            if amt is not None and o.get("currency"):
                c["currency"] = o["currency"]
            out.append(c)
    for (g, pe), k in sorted(first.items()):
        for view, cut in (("as_known", max(k, pe)), ("revised", as_of)):
            t, nd = cip_at(g, pe, cut)
            if t is None:
                out.append(cell("ppe_component_disclosed", g, None, pe, view, as_of, term="cip_tagged",
                                status="not_determinable", nd_reason=nd))
                continue
            c = cell("ppe_component_disclosed", g, None, pe, view, as_of, term="cip_tagged", value=t["value"],
                     unit=t.get("unit"), terms=[t], flags={"concept": t.get("concept")})
            if t.get("unit") and re.fullmatch(r"[A-Z]{3}", t["unit"]):
                c["currency"] = t["unit"]
            out.append(c)
    return out
