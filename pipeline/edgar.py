"""Points d'accès EDGAR (§9.3, §9.4), tous derrière le client unique et le cache.

Découvre les ressources d'un dépôt (index.json, en-tête SGML), ne les suppose pas.
Sous /Archives/, rien ne s'invalide ; les API sont horodatées et tirées une fois par
exécution.
"""
import json
import re

from . import cache
from .net import NotCollected

WWW = "https://www.sec.gov"
DATA = "https://data.sec.gov"


def cik10(cik):
    return f"{int(cik):010d}"


def acc_nodash(accession):
    return accession.replace("-", "")


def archive_url(cik, accession, document):
    return f"{WWW}/Archives/edgar/data/{int(cik)}/{acc_nodash(accession)}/{document}"


class Edgar:
    def __init__(self, client, as_of):
        self.client = client
        self.as_of = as_of

    # -- ressources d'API horodatées -------------------------------------------
    def api(self, cik, resource, url):
        path = cache.api_path(cik, resource, self.as_of)
        if path.exists():
            return cache.read(path)
        body, _ = self.client.get(url)
        cache.write(path, body)
        return body

    def tickers(self):
        return json.loads(self.api("none", "company_tickers", f"{WWW}/files/company_tickers.json"))

    def companyfacts(self, cik):
        c = cik10(cik)
        return json.loads(self.api(c, "companyfacts", f"{DATA}/api/xbrl/companyfacts/CIK{c}.json"))

    def submissions(self, cik):
        """Toutes les pages de submissions, sans filtre de date (§9.4)."""
        c = cik10(cik)
        main = json.loads(self.api(c, "submissions", f"{DATA}/submissions/CIK{c}.json"))
        rows = _columns_to_rows(main["filings"]["recent"])
        pages = []
        for f in main["filings"].get("files", []):
            name = f["name"]
            res = "submissions-" + name.rsplit("-", 1)[-1].replace(".json", "")
            page = json.loads(self.api(c, res, f"{DATA}/submissions/{name}"))
            got = _columns_to_rows(page)
            pages.append({"name": name, "declared": f.get("filingCount"), "read": len(got),
                          "from": f.get("filingFrom"), "to": f.get("filingTo")})
            rows.extend(got)
        complete = all(p["declared"] in (None, p["read"]) for p in pages)
        return main, rows, pages, complete

    # -- archives immuables -------------------------------------------------------
    def archive(self, cik, accession, document):
        path = cache.archive_path(cik10(cik), accession, document)
        if path.exists():
            return cache.read(path)
        body, _ = self.client.get(archive_url(cik, accession, document))
        cache.write(path, body)
        return body

    def archive_cached(self, cik, accession, document):
        return cache.archive_path(cik10(cik), accession, document).exists()

    def filing_index(self, cik, accession):
        return json.loads(self.archive(cik, accession, "index.json"))

    def sgml_documents(self, cik, accession):
        """Types des pièces lus dans l'en-tête SGML, jamais dans le nom de fichier (§2.3)."""
        raw = self.archive(cik, accession, f"{accession}-index-headers.html")
        return parse_sgml_header(raw)


def _columns_to_rows(cols):
    keys = list(cols.keys())
    n = len(cols[keys[0]]) if keys else 0
    return [{k: cols[k][i] for k in keys} for i in range(n)]


_DOC_RE = re.compile(rb"<DOCUMENT>(.*?)(?=<DOCUMENT>|</SEC-HEADER>|\Z)", re.S | re.I)
_FIELD_RE = re.compile(rb"<(TYPE|SEQUENCE|FILENAME|DESCRIPTION)>([^<\r\n]*)", re.I)


def parse_sgml_header(raw):
    """Extrait la liste des documents (TYPE, SEQUENCE, FILENAME, DESCRIPTION) et
    les champs d'en-tête utiles du fichier -index-headers.html."""
    text = raw
    # le fichier est du HTML qui enveloppe l'en-tête SGML échappé
    text = text.replace(b"&lt;", b"<").replace(b"&gt;", b">").replace(b"&amp;", b"&")
    docs = []
    for m in _DOC_RE.finditer(text):
        fields = {}
        for f in _FIELD_RE.finditer(m.group(1)):
            k = f.group(1).decode().upper()
            if k not in fields:
                fields[k] = f.group(2).decode("utf-8", "replace").strip()
        if fields.get("FILENAME"):
            docs.append(fields)
    header = {}
    for key in (b"ACCEPTANCE-DATETIME", b"ITEM INFORMATION", b"CONFORMED PERIOD OF REPORT",
                b"FILED AS OF DATE", b"CONFORMED SUBMISSION TYPE", b"PUBLIC DOCUMENT COUNT"):
        vals = re.findall(rb"<?" + re.escape(key) + rb">?:?[ \t]*([^\r\n<]*)", text)
        vals = [v.decode("utf-8", "replace").strip() for v in vals if v.strip()]
        if vals:
            header[key.decode()] = vals
    return {"documents": docs, "header": header}


__all__ = ["Edgar", "NotCollected", "cik10", "acc_nodash", "archive_url", "parse_sgml_header"]
