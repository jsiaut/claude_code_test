"""Table documents : une ligne par ressource lue, avec son empreinte (§7.1, §12.1).

Le cache n'est pas versionné ; documents garde l'empreinte (sha256 du contenu décompressé)
et l'emplacement de tout ce qui a été lu. Classement par le triplet (formulaire, item,
pièce), le type de pièce venant de l'en-tête SGML (§2.3).
"""
import json

import pandas as pd

from . import cache, config

PERIODIC_A = {"10-K", "10-K/A", "10-KT", "10-KT/A"}
PERIODIC_B = {"10-Q", "10-Q/A", "10-QT", "10-QT/A"}


def _kind(name, sgml_type):
    if name.endswith("-index-headers.html"):
        return "sgml_header"
    if name == "index.json":
        return "filing_index"
    if name == "MetaLinks.json":
        return "metalinks"
    if name == "FilingSummary.xml":
        return "filing_summary"
    if name.endswith("-xbrl.zip"):
        return "xbrl_zip"
    if name.endswith(".xml"):
        return "instance"
    if name.endswith(".xsd"):
        return "schema"
    if sgml_type and sgml_type.upper().startswith("EX-"):
        return "exhibit"
    return "primary_document"


def _classify(kind, form, sgml_type, items):
    """filing_status, doc_class, assurance_level, tier d'un document (§2.2, annexe A)."""
    form = form or ""
    st = (sgml_type or "").upper()
    if form.startswith("DRS"):
        return "submitted_draft", "narrative", "unaudited", "E"
    if kind in ("sgml_header", "filing_index", "filing_summary", "metalinks"):
        return "filed", "inventory", "not_applicable", None
    if kind in ("xbrl_zip", "instance"):
        if form in PERIODIC_A:
            return "filed", "financial_statements", "audited", "A"
        if form in PERIODIC_B:
            return "filed", "financial_statements", "reviewed", "B"
        return "filed", "financial_statements", "unaudited", "C"
    if kind == "exhibit":
        if st.startswith("EX-10") or st.startswith("EX-4") or st.startswith("EX-2"):
            return "filed", "contract", "not_applicable", "D"
        if st.startswith("EX-99"):
            return "furnished", "pointer", "unaudited", "E"
        return "filed", "narrative", "unaudited", "C"
    # document principal
    it = {x.strip() for x in (items or "").split(",") if x.strip()}
    if form in ("8-K", "8-K/A") and it and it <= {"2.02", "7.01", "9.01"}:
        return "furnished", "pointer", "unaudited", "E"
    if form in PERIODIC_A:
        return "filed", "financial_statements", "audited", "A"
    if form in PERIODIC_B:
        return "filed", "financial_statements", "reviewed", "B"
    if form.startswith("DEF 14A"):
        return "filed", "governance", "not_applicable", "C"
    return "filed", "narrative", "unaudited", "C"


def build(as_of, used_accessions=None, failed=None):
    filings = pd.read_parquet(config.DB_DIR / "filings.parquet")
    meta = {r["accessionNumber"]: r for r in filings.to_dict("records")}
    ex = json.loads((config.DB_DIR / "exhibits_tranche.json").read_text())
    sgml = {}
    for e in ex if isinstance(ex, list) else ex.get("exhibits", []):
        if isinstance(e, dict) and e.get("accession") and e.get("filename"):
            sgml[(e["accession"], e["filename"])] = (e.get("type"), e.get("description"))
    failed = failed or set()
    rows = []
    root = config.CACHE
    disc = _discovery_meta()
    for p in sorted((root / "archives").rglob("*.zst")):
        rel = p.relative_to(root)
        cik, acc = rel.parts[1], rel.parts[2]
        name = "/".join(rel.parts[3:])[:-4]
        m = meta.get(acc) or disc.get(acc, {})
        st, desc = sgml.get((acc, name), (None, None))
        kind = _kind(name, st)
        fs, dc, al, tier = _classify(kind, m.get("form"), st, m.get("items"))
        data = cache.read(p)
        fd = m.get("filingDate")
        rows.append({
            "doc_key": f"{cik}/{acc}/{name}", "resource_kind": kind,
            "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{name}",
            "cik": cik, "group_id": m.get("group_id"), "accession": acc, "document": name,
            "sgml_type": st, "sgml_description": desc, "form": m.get("form"), "items": m.get("items"),
            "filing_date": fd, "acceptance_datetime": m.get("acceptanceDateTime"), "report_date": m.get("reportDate"),
            "knowledge_date": fd, "filing_status": fs, "incorporated_by_reference": None, "doc_class": dc,
            "assurance_level": al, "tier": tier, "sha256": cache.sha256(data), "size_bytes": len(data),
            "cache_path": str(rel), "fetched_as_of": as_of, "amends_accession": None,
            "parse_state": "parse_failed" if acc in failed else
            ("parsed" if (used_accessions is None or acc in used_accessions) else "not_parsed"),
            "normalizer_version": "textnorm-1", "classification_note": None})
    for p in sorted((root / "api").rglob("*.zst")):
        rel = p.relative_to(root)
        cik, res = rel.parts[1], rel.parts[2]
        kind = "api_companyfacts" if res == "companyfacts" else ("api_submissions" if res.startswith("submissions")
                                                                 else "api_tickers")
        data = cache.read(p)
        rows.append({"doc_key": "api/" + "/".join(rel.parts[1:])[:-4], "resource_kind": kind,
                     "url": None, "cik": cik, "group_id": None, "accession": None, "document": res,
                     "sgml_type": None, "sgml_description": None, "form": None, "items": None,
                     "filing_date": None, "acceptance_datetime": None, "report_date": None,
                     "knowledge_date": rel.parts[-1][:10], "filing_status": "filed", "incorporated_by_reference": None,
                     "doc_class": "inventory", "assurance_level": "not_applicable", "tier": None,
                     "sha256": cache.sha256(data), "size_bytes": len(data), "cache_path": str(rel),
                     "fetched_as_of": as_of, "amends_accession": None, "parse_state": "parsed",
                     "normalizer_version": None, "classification_note": None})
    # jeux de données de la SEC (bloc lender de §14) : page, readme et archives mensuelles
    for p in sorted((root / "other" / "bdc").rglob("*.zst")):
        rel = p.relative_to(root)
        data = cache.read(p)
        name = rel.name[:-4]
        if rel.parts[-2] == "archives":
            kind, url = "dataset_archive", ("https://www.sec.gov/files/datastandardsinnovation/data/"
                                            "business-development-company-bdc-data-sets/" + name)
        elif name.endswith(".pdf"):
            kind, url = "web_page", "https://www.sec.gov/files/bdc_readme.pdf"
        else:
            kind, url = "web_page", "https://www.sec.gov/data-research/sec-markets-data/bdc-data-sets"
        rows.append({"doc_key": "other/" + "/".join(rel.parts[1:])[:-4], "resource_kind": kind, "url": url,
                     "cik": None, "group_id": None, "accession": None, "document": name, "sgml_type": None,
                     "sgml_description": None, "form": None, "items": None, "filing_date": None,
                     "acceptance_datetime": None, "report_date": None, "knowledge_date": None,
                     "filing_status": "filed" if kind == "dataset_archive" else None, "incorporated_by_reference": None,
                     "doc_class": "financial_statements" if kind == "dataset_archive" else "inventory",
                     "assurance_level": "not_applicable", "tier": None, "sha256": cache.sha256(data),
                     "size_bytes": len(data), "cache_path": str(rel), "fetched_as_of": as_of,
                     "amends_accession": None, "parse_state": "parsed", "normalizer_version": None,
                     "classification_note": "BDC Data Sets, millésime gardé (rafraîchissement de septembre 2026)"
                     if kind == "dataset_archive" else None})
    rows += _discovery_rows(root, as_of)
    for p in sorted((root / "taxonomies").rglob("*.zst")):
        rel = p.relative_to(root)
        data = cache.read(p)
        rows.append({"doc_key": "taxonomy/" + rel.name[:-4], "resource_kind": "schema", "url": "https://xbrl.fasb.org/",
                     "cik": None, "group_id": None, "accession": None, "document": rel.name[:-4], "sgml_type": None,
                     "sgml_description": None, "form": None, "items": None, "filing_date": None,
                     "acceptance_datetime": None, "report_date": None, "knowledge_date": None, "filing_status": None,
                     "incorporated_by_reference": None, "doc_class": "non_edgar", "assurance_level": "not_applicable",
                     "tier": "F", "sha256": cache.sha256(data), "size_bytes": len(data), "cache_path": str(rel),
                     "fetched_as_of": as_of, "amends_accession": None, "parse_state": "parsed",
                     "normalizer_version": None, "classification_note": "taxonomie épinglée (annexe D)"})
    return rows


def _discovery_meta():
    """Formulaire et date des dépôts tirés par la découverte (pages R, EX-10, Form D)."""
    out = {}
    for name in ("discovery_mentions.parquet", "discovery_ex10.parquet", "discovery_formd.parquet"):
        p = config.DB_DIR / name
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        for r in df.to_dict("records"):
            acc = r.get("adsh")
            if not acc or acc in out:
                continue
            fd = str(r.get("date") or r.get("file_date") or "").replace("-", "")
            out[acc] = {"form": r.get("form"), "filingDate": f"{fd[:4]}-{fd[4:6]}-{fd[6:8]}" if len(fd) == 8 else None,
                        "group_id": None}
    return out


def _discovery_rows(root, as_of):
    """Bloc `discovery` (§14) : archives des Notes Data Sets (empreinte et extraits, l'archive
    entière n'étant pas gardée, D-0036), page et notice des jeux de données, liste des noms
    d'EDGAR, pages de la recherche plein texte."""
    rows = []
    man = root / "datasets" / "notes" / "manifest.jsonl"
    seen = {}
    if man.exists():
        for l in man.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            seen[r["name"]] = r
    for name, r in sorted(seen.items()):
        if r.get("status") != "scanned":
            continue
        rows.append({"doc_key": f"datasets/notes/{name}", "resource_kind": "dataset_archive", "url": r["url"],
                     "cik": None, "group_id": None, "accession": None, "document": name + ".zip", "sgml_type": None,
                     "sgml_description": None, "form": None, "items": None, "filing_date": None,
                     "acceptance_datetime": None, "report_date": None, "knowledge_date": r.get("retrieved", "")[:10] or None,
                     "filing_status": "filed", "incorporated_by_reference": None, "doc_class": "financial_statements",
                     "assurance_level": "not_applicable", "tier": None, "sha256": r.get("sha256"),
                     "size_bytes": r.get("bytes"), "cache_path": f"datasets/notes/{name}/", "fetched_as_of": as_of,
                     "amends_accession": None, "parse_state": "parsed", "normalizer_version": None,
                     "classification_note": (f"Notes Data Sets, dépôts du {r.get('filed_from')} au {r.get('filed_to')} ; "
                                             f"archive non gardée entière (extraits sous cache_path), lexique "
                                             f"{r.get('lexicon_version')}, Last-Modified {r.get('last_modified')}")})
    for sub, url_of, kind, note in (
            ("notes", lambda n: "https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets"
             if n.endswith(".html") else "https://www.sec.gov/files/aqfsn_1.pdf", "web_page", "Notes Data Sets : page et notice"),
            ("edgar", lambda n: "https://www.sec.gov/Archives/edgar/cik-lookup-data.txt", "web_page",
             "liste des noms et CIK d'EDGAR (§9.4)")):
        d = root / "other" / sub
        if not d.exists():
            continue
        for p in sorted(d.glob("*.zst")):
            data = cache.read(p)
            name = p.name[:-4]
            rows.append({"doc_key": f"other/{sub}/{name}", "resource_kind": kind, "url": url_of(name), "cik": None,
                         "group_id": None, "accession": None, "document": name, "sgml_type": None,
                         "sgml_description": None, "form": None, "items": None, "filing_date": None,
                         "acceptance_datetime": None, "report_date": None, "knowledge_date": None,
                         "filing_status": None, "incorporated_by_reference": None, "doc_class": "inventory",
                         "assurance_level": "not_applicable", "tier": None, "sha256": cache.sha256(data),
                         "size_bytes": len(data), "cache_path": str(p.relative_to(root)), "fetched_as_of": as_of,
                         "amends_accession": None, "parse_state": "parsed", "normalizer_version": None,
                         "classification_note": note})
    sdir = root / "search"
    if sdir.exists():
        for p in sorted(sdir.rglob("*.json.zst")):
            data = cache.read(p)
            rows.append({"doc_key": "search/" + "/".join(p.relative_to(sdir).parts)[:-4], "resource_kind": "web_page",
                         "url": None, "cik": None, "group_id": None, "accession": None,
                         "document": p.parent.name, "sgml_type": None, "sgml_description": None, "form": None,
                         "items": None, "filing_date": None, "acceptance_datetime": None, "report_date": None,
                         "knowledge_date": p.name[:10], "filing_status": None, "incorporated_by_reference": None,
                         "doc_class": "inventory", "assurance_level": "not_applicable", "tier": None,
                         "sha256": cache.sha256(data), "size_bytes": len(data),
                         "cache_path": str(p.relative_to(root)), "fetched_as_of": as_of, "amends_accession": None,
                         "parse_state": "parsed", "normalizer_version": None,
                         "classification_note": "page de la recherche plein texte (efts.sec.gov), requête consignée "
                                                "dans work/discovery/efts_queries.jsonl"})
    return rows
