"""Règle de lecture du corps d'une pièce EX-10 ou EX-4 (§11.1).

L'en-tête avant le corps : la section de l'item et la première page se lisent d'abord ;
le reste de la pièce seulement si l'une de ses parties, hormis le déposant et son groupe,
n'est pas un établissement financier (EX-10), ou si son porteur n'en est pas un (EX-4).
Le corps se lit aussi, quelles que soient les parties, pour un amendement autonome :
EX-10 dont le titre contient Amendment, Waiver ou Consent en mot entier, sauf s'il commence
(ordinal mis à part) par Amended and Restated ; EX-4 « Supplemental Indenture » annexé à
un 8-K qui porte l'item 3.03.
"""
import json

from . import config, sections


def header_lines(header_ck):
    p = config.OBS_DIR / f"{header_ck}.jsonl"
    if not p.exists():
        return None
    lines = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        return []
    last = max((l.get("as_of"), l.get("pass_id")) for l in lines)
    return [l for l in lines if (l.get("as_of"), l.get("pass_id")) == last]


def decide(req):
    """Renvoie (lire_le_corps, motif) ; (None, motif) tant que l'en-tête n'est pas lu."""
    lines = header_lines(req["header_content_key"])
    if lines is None:
        return None, "en-tête non lu"
    title = next((l.get("exhibit_title") for l in lines if l.get("exhibit_title")), None)
    if sections.amendment_rule(req["exhibit_type"], title or "", set(req.get("items") or [])):
        return True, "amendement autonome (titre)"
    parties = [l for l in lines if l.get("party_role")]
    nonfin = [l for l in parties if l.get("party_is_financial_institution") is False
              and l.get("party_role") not in ("filer", "filer_group")]
    if nonfin:
        return True, "partie non financière : " + ", ".join(sorted({l.get("counterparty_name") or "?" for l in nonfin}))
    if not parties:
        return True, "parties non établies à l'en-tête : corps lu par prudence"
    return False, "établissements financiers seulement"


def body_required(req):
    want, _ = decide(req)
    return bool(want)
