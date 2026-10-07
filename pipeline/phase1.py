"""Phase 1 : l'ossature, sans extraction (§11.1).

companyfacts sans borne de date (prédécesseurs compris) ; archives -xbrl.zip des 10-K,
10-Q et amendements de la période de lecture (fenêtre allongée et huit trimestres qui
la précèdent) ; instance de tout autre dépôt source d'un fait de companyfacts de ces
périodes, pour le classer. Les instances ne servent qu'aux dimensions, aux extensions
et à decimals des périodes analysées.
"""
import io
import json
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor

from . import cache, config
from .edgar import Edgar, archive_url, cik10
from .net import NotCollected
from . import xbrl

ANNUAL_TIER_A = {"10-K", "10-K/A", "10-KT", "10-KT/A", "20-F", "20-F/A", "40-F", "40-F/A"}
QUARTER_TIER_B = {"10-Q", "10-Q/A", "10-QT", "10-QT/A"}
FURNISHED_8K_ITEMS = {"2.02", "7.01"}


def tier_for_form(form):
    if form in ANNUAL_TIER_A:
        return "A", "audited", "filed"
    if form in QUARTER_TIER_B:
        return "B", "reviewed", "filed"
    return None, None, None


def companyfacts_rows(cf, group_id, filer_cik, filings_by_acc):
    """Faits de companyfacts : ossature sûre et incomplète (§9.3). Ni decimals, ni
    dimensions, ni extensions ; clé : accession, concept, unité, période (§7.2)."""
    rows = []
    seen = {}
    for taxonomy, concepts in (cf.get("facts") or {}).items():
        fw = xbrl.framework_of(taxonomy)
        for local, c in concepts.items():
            for unit, arr in (c.get("units") or {}).items():
                for f in arr:
                    accn = f.get("accn")
                    concept = f"{taxonomy}:{local}"
                    base = f"cf/{accn}/{concept}/{unit}/{f.get('start') or ''}/{f['end']}"
                    n = seen.get(base, 0)
                    seen[base] = n + 1
                    key = base if n == 0 else f"{base}#{n}"
                    form = f.get("form")
                    fil = filings_by_acc.get(accn, {})
                    tier, assurance, status = tier_for_form(form)
                    if form in ("8-K", "8-K/A"):
                        items = {x.strip() for x in (fil.get("items") or "").split(",") if x.strip()}
                        status = "furnished" if items and items <= (FURNISHED_8K_ITEMS | {"9.01"}) else "filed"
                    try:
                        val = xbrl.Decimal(str(f["val"]))
                    except Exception:
                        val = None
                    rows.append({
                        "fact_key": key, "source": "companyfacts", "cik": filer_cik,
                        "entity_id": f"group:{group_id}", "group_id": group_id,
                        "accession": accn, "form": form, "filing_date": f.get("filed"),
                        "acceptance_datetime": fil.get("acceptanceDateTime"),
                        "doc_rank": None, "occ_rank": None,
                        "concept": concept, "concept_ns": None, "taxonomy_version": None,
                        "period_type": "duration" if f.get("start") else "instant",
                        "period_start": f.get("start"), "period_end": f["end"],
                        "unit": unit, "currency": unit if re.fullmatch(r"[A-Z]{3}", unit) else None,
                        "dims": "[]", "n_dims": 0, "framework": fw, "reporting_scope": "as_reported",
                        "value": str(val) if val is not None else None, "value_text": None,
                        "decimals": None, "decimals_inf": None, "precision_known": False,
                        "is_nil": False, "is_fixed_zero": None, "fact_id": None,
                        "locator": json.dumps({"api": "companyfacts", "cik": filer_cik, "accn": accn,
                                               "concept": concept, "unit": unit,
                                               "start": f.get("start"), "end": f["end"]}),
                        "is_tagged": True, "tier": tier, "filing_status": status,
                        "assurance_level": assurance, "knowledge_date": f.get("filed"),
                        "fy": f.get("fy"), "fp": f.get("fp"), "frame": f.get("frame"),
                    })
    return rows


# -- archives XBRL d'un dépôt ------------------------------------------------------

LINKBASE_RX = re.compile(r"_(cal|def|lab|pre)\.xml$", re.I)


def discover(e: Edgar, cik, accession):
    """Inventaire du répertoire du dépôt (index.json) : ressources XBRL présentes."""
    idx = e.filing_index(cik, accession)
    items = idx.get("directory", {}).get("item", [])
    names = {it["name"]: it for it in items}
    zipname = f"{accession}-xbrl.zip"
    inst = [n for n in names if n.endswith("_htm.xml")]
    if not inst:
        inst = [n for n in names if n.endswith(".xml") and not LINKBASE_RX.search(n)
                and n not in ("FilingSummary.xml",) and not n.startswith("R")
                and not n.endswith("_ref.xml")]
    return {
        "zip": zipname if zipname in names else None,
        "instance": inst[0] if inst else None,
        "metalinks": "MetaLinks.json" if "MetaLinks.json" in names else None,
        "filing_summary": "FilingSummary.xml" if "FilingSummary.xml" in names else None,
        "names": names,
    }


def fetch_xbrl(e: Edgar, cik, accession):
    """Ramène archive, instance, MetaLinks et FilingSummary ; renvoie un dict de bytes."""
    d = discover(e, cik, accession)
    files = {}
    if d["zip"]:
        z = e.archive(cik, accession, d["zip"])
        with zipfile.ZipFile(io.BytesIO(z)) as zf:
            for n in zf.namelist():
                files[n] = zf.read(n)
    for key in ("instance", "metalinks", "filing_summary"):
        n = d[key]
        if n and n not in files:
            files[n] = e.archive(cik, accession, n)
    return d, files


def parse_filing(group_id, filing, d, files):
    """Faits, blocs de texte, linkbases et métadonnées d'un dépôt."""
    accession = filing["accessionNumber"]
    ml = xbrl.parse_metalinks(files[d["metalinks"]]) if d["metalinks"] in files else None
    tb = xbrl.text_block_concepts_from_metalinks(ml) if ml else None
    inst_name = d["instance"]
    if inst_name is None or inst_name not in files:
        return None
    facts, blocks, meta = xbrl.parse_instance(files[inst_name], tb)
    lb = xbrl.parse_linkbases({n: b for n, b in files.items()
                               if n.lower().endswith((".xsd", ".xml")) and n != inst_name
                               and n != "FilingSummary.xml"})
    fs = xbrl.parse_filing_summary(files[d["filing_summary"]]) if d["filing_summary"] in files else []
    tier, assurance, status = tier_for_form(filing["form"])
    rows = []
    for f in facts:
        dims = f["dims"]
        scope = "legal_entity" if any(a in ("dei:LegalEntityAxis", "srt:ConsolidatedEntitiesAxis")
                                      for a, _ in dims) else "as_reported"
        val = f.get("value")
        rows.append({
            "fact_key": f"{accession}/{inst_name}#{f['occ_rank']}", "source": "instance",
            "cik": f.get("cik"), "entity_id": f"group:{group_id}", "group_id": group_id,
            "accession": accession, "form": filing["form"], "filing_date": filing["filingDate"],
            "acceptance_datetime": filing.get("acceptanceDateTime"), "doc_rank": 0,
            "occ_rank": f["occ_rank"], "concept": f["concept"], "concept_ns": f["concept_ns"],
            "taxonomy_version": f["taxonomy_version"], "period_type": f["period_type"],
            "period_start": f["period_start"], "period_end": f["period_end"],
            "unit": f.get("unit"), "currency": f.get("currency"),
            "dims": xbrl.canonical_dims(dims), "n_dims": len(dims), "framework": f["framework"],
            "reporting_scope": scope, "value": str(val) if val is not None else None,
            "value_text": f.get("value_text"), "decimals": f.get("decimals"),
            "decimals_inf": f.get("decimals_inf"), "precision_known": True,
            "is_nil": f["is_nil"], "is_fixed_zero": None, "fact_id": f.get("fact_id"),
            "locator": json.dumps({"file": inst_name, "accession": accession, "fact_id": f.get("fact_id"),
                                   "occ_rank": f["occ_rank"]}),
            "is_tagged": True, "tier": tier, "filing_status": status, "assurance_level": assurance,
            "knowledge_date": filing["filingDate"], "fy": None, "fp": None, "frame": None,
        })
    tblocks = [{"accession": accession, "group_id": group_id, "concept": b["concept"],
                "fact_id": b.get("fact_id"), "occ_rank": b["occ_rank"],
                "period_start": b["period_start"], "period_end": b["period_end"],
                "dims": xbrl.canonical_dims(b["dims"]), "chars": len(b["text"])}
               for b in blocks]
    pres = []
    for role, arcs in lb["pres"].items():
        rdef = lb["roles"].get(role, "")
        kind = xbrl.statement_kind(rdef)
        for frm, to, order, pl in arcs:
            pres.append({"accession": accession, "group_id": group_id, "role": role,
                         "role_definition": rdef, "statement_kind": kind, "parent": frm,
                         "child": to, "ord": order, "preferred_label": pl})
    calc = []
    for role, arcs in lb["calc"].items():
        for frm, to, order, w in arcs:
            calc.append({"accession": accession, "group_id": group_id, "role": role,
                         "parent": frm, "child": to, "ord": order, "weight": w})
    tags = []
    if ml:
        for c, t in ml["tags"].items():
            refs = []
            for r in t.get("auth_ref", []):
                sr = ml["std_ref"].get(r, {})
                if sr.get("Topic"):
                    refs.append("ASC " + "-".join(x for x in (sr.get("Topic"), sr.get("SubTopic"),
                                                            sr.get("Section"), sr.get("Paragraph")) if x))
            tags.append({"accession": accession, "group_id": group_id, "concept": c,
                         "xbrltype": t.get("xbrltype"), "crdr": t.get("crdr"), "label": t.get("label"),
                         "documentation": (t.get("documentation") or "")[:2000],
                         "asc_refs": json.dumps(sorted(set(refs)))})
    labels = [{"accession": accession, "group_id": group_id, "concept": c, "label_role": r, "label": l}
              for c, rl in lb["labels"].items() for r, l in rl.items()]
    return {"facts": rows, "text_blocks": tblocks, "pres": pres, "calc": calc, "tags": tags,
            "labels": labels, "filing_summary": fs, "meta": meta}
