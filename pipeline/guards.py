"""Gardes de lecture (D-0087) : ce qu'une ligne ne doit pas porter, contrôlé à sa soumission.

Trois règles de lecture que le schéma ne voyait pas, et que l'exécutant contrôlait à la main après coup :

- G1, erreur : une ligne de famille `financing` de nature `interest` ou `fee`. Intérêts et commissions sont le prix d'un
  financement : ils suivent la trésorerie, sans `family` ni `edge_type`, sous le même `instrument_key` (guide de
  lecture, §3 ; D-0015 ; D-0086, point 11). Un remboursement garde sa famille : le code le lit comme une clôture
  (D-0069, point 5).
- G2, erreur : une personne physique nommée dans un champ de texte ou dans la clé d'instrument (D-0078). La fonction
  remplace le nom, et une citation se réduit à un passage sans nom. Une société prise pour une personne s'ajoute à
  ALLOWED, avec une ligne dans la décision en cours.
- G3, alerte : un montant qui ne vient pas d'un fait balisé et ne se lit pas dans sa citation (D-0084, point 14 ;
  D-0085, point 3). L'exécutant corrige la ligne, ou confirme l'alerte (`reader submit --confirm`).

Les gardes s'appliquent à la soumission (`reader submit`) et au contrôle d'avant réassemblage (`reader check`), jamais
au chargement : une ligne déjà écrite garde son état. La garde de D-0078 sur la table assemblée (`tests/test_d0078.py`)
lit le même relevé.
"""
import re
from decimal import Decimal, InvalidOperation

# -- G1 : prix d'un financement ---------------------------------------------------------------------------------------

PRICE_NATURES = ("interest", "fee")


def flow_errors(line):
    """Erreur d'une ligne de famille `financing` dont la nature est le prix du financement (intérêts, commissions)."""
    if line.get("kind") == "observation" and line.get("family") == "financing" and line.get("amount_nature") in PRICE_NATURES:
        return [f"ligne `financing` de nature `{line['amount_nature']}` : le prix d'un financement suit la trésorerie, "
                "sans family ni edge_type, sous le même instrument_key (guide de lecture, §3 ; D-0087)"]
    return []


# -- G2 : aucune ligne ne nomme une personne physique (D-0078, points 3 et 6) ------------------------------------------

FIELDS = ("quote", "note", "counterparty_name", "payer", "payee", "period_label", "trigger_description", "exhibit_title",
          "ultimate_obligor", "party_role")
FIRST = """Aaron Adam Alan Albert Alex Alexander Alice Amanda Amit Amy Andrea Andrew Andy Angela Ann Anna Anne Anthony
Antonio Arthur Barbara Ben Benjamin Bill Bob Brad Bradley Brian Bruce Carl Carlos Carol Catherine Charles Charlie Chris
Christine Christopher Colin Craig Dan Daniel Dave David Dean Deborah Dennis Diana Diane Donald Doug Douglas Edward
Elizabeth Elon Emily Eric Erik Frank Fred Gary George Glenn Gordon Grace Greg Gregory Gwynne Harold Harry Heather Helen
Henry Hock Howard Ian Ira Jack Jacob James Jamie Jane Janet Jason Jay Jeff Jeffrey Jennifer Jensen Jeremy Jerry Jessica
Jim Joan Joe Joel John Jon Jonathan Jordan Jose Joseph Josh Joshua Juan Judith Julia Julie Justin Karen Kate Katherine
Keith Kelly Ken Kenneth Kevin Kim Kimbal Larry Laura Lauren Lawrence Lee Leon Linda Lisa Lori Louis Marc Margaret Maria
Marie Mark Martin Mary Masayoshi Matt Matthew Michael Michelle Mike Nancy Nathan Nazar Neil Nicholas Nick Nicole Pamela
Patricia Patrick Paul Peter Philip Rachel Rajeev Ralph Ray Raymond Rebecca Reid Richard Rick Robert Robin Roger Ronald
Rose Russell Ryan Safra Sam Samuel Sandra Sara Sarah Satya Scott Sean Sergey Sharon Stephen Steve Steven Sundar Susan
Syed Ted Thomas Tim Timothy Todd Tom Tony Victor Walter Wayne Wes William""".split()
SURNAMES = """Altman Amodei Ballmer Bartz Belardi Benioff Bezos Birchall Brin Catz Denholm Ellison Feldman Gracias Hoffman Huang
Intrator Jassy Masaitis McCabe Moussouris Musk Nadella Novak Pichai Prager Schmidt Shotwell Suleyman Sutardja Varjabedian
Yaccarino Zuckerberg""".split()
PATTERNS = [
    re.compile(r"\b(?:" + "|".join(FIRST) + r")\s+(?:[A-Z]\.\s+)?[A-Z][a-zA-Z'\-]+"),
    re.compile(r"\b(?:" + "|".join(SURNAMES) + r")\b"),
    re.compile(r"\b(?:Mr|Ms|Mrs|Dr|Messrs)\.\s+[A-Z][a-z]+|\bM\.\s+[A-Z][a-z]+|\bMme\s+[A-Z]|\bJudge\s+[A-Z]"),
    re.compile(r"\b[A-Z][a-z]{2,} [A-Z]\. [A-Z][a-z]{2,}\b"),
    re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)? (?:v\.|c\.) [A-Z]"),
    re.compile(r"(?:Family|Revocable|Living|Irrevocable) Trust"),
]
KEY_SURNAMES = re.compile(r"(?:^|[:_\-])(" + "|".join(s.lower() for s in SURNAMES) + r")(?:[_\-]|$)")
# noms de sociétés, de fondations, de lieux, de projets et tournures admis (D-0078, point 6), retirés avant le relevé
ALLOWED = sorted("""Carl Zeiss|Ben Milam|Frank Funds|BCH San Jose LLC|Jane Street|Jordan HPC|Sharon AI|John Wiley|Apollo Rose
|Lawrence Investments|Grace Blackwell|Louis Energy|USMIO Charlie LLC|Angela Bridge|Martin Merger Sub|Raymond James|Ernst & Young LLP
|Raymond Chabot|James River|George Town|Howard Street|Dave Inc|Grace Period|Saint Lawrence|Bradley Woods|Trade Mark Licence
|B. Riley|Term Loan A. The|Company A. Intel|Texas v. Meta|Brandt Dr. S.|Green Earth Liang's Inc.|Green Earth Liang
|The Jen-Hsun and Lori Huang Foundation|Huang Foundation|McCabe Petroleum|Ellison Institute|Ellison Medical|Musk Industries
|Harbor Gates|Kohlberg Kravis Roberts|Kravis Roberts|Hong Kong|Kleiner Perkins|Janus Henderson|The Washington Post
|Charles Schwab & Co., Inc.""".replace("\n", "").split("|"),
                 key=len, reverse=True)




def person_mentions(line):
    """Mentions d'une personne physique dans une ligne : [(champ, mention)]. Les noms admis (sociétés, fondations,
    lieux, tournures) sont retirés avant le relevé ; la clé d'instrument se lit sur les noms de famille."""
    out = []
    for f in FIELDS:
        t = line.get(f)
        if not isinstance(t, str) or not t:
            continue
        for a in ALLOWED:
            t = t.replace(a, " ")
        out += [(f, m.group(0)) for rx in PATTERNS for m in rx.finditer(t)]
    ik = line.get("instrument_key")
    if isinstance(ik, str) and KEY_SURNAMES.search(ik.lower()):
        out.append(("instrument_key", ik))
    return out


# -- G3 : montant contre citation -------------------------------------------------------------------------------------

_SCALES = {"thousand": 3, "million": 6, "billion": 9, "trillion": 12, "k": 3, "m": 6, "mm": 6, "mn": 6, "b": 9, "bn": 9}
# un nombre, puis son échelle ou son signe de pourcentage s'il en porte ; une lettre peut le précéder (« W8,837,748 »)
_NUM = re.compile(r"(?<![\d.,])(\d[\d,]*(?:\.\d+)?)"
                  r"(?:\s*-?\s*(%|percent|thousand|million|billion|trillion|bn|mm|mn|k|m|b)(?![a-z]))?", re.I)
_BARE = (0, 3, 6, 9, 12)        # un nombre nu vaut à l'unité ou à l'échelle d'un tableau, écrite hors de la citation
AMOUNT_FIELDS = ("amount", "amount_lower", "amount_upper")


def quote_values(quote):
    """Valeurs qu'une citation permet de lire : nombre fois son échelle écrite, pourcentage divisé par cent, nombre nu
    à l'unité et aux échelles de mille en mille."""
    vals = set()
    for m in _NUM.finditer(quote or ""):
        try:
            n = Decimal(m.group(1).replace(",", ""))
        except InvalidOperation:
            continue
        unit = (m.group(2) or "").lower()
        if unit in ("%", "percent"):
            vals.add(n / 100)
        elif unit in _SCALES:
            vals.add(n * Decimal(10) ** _SCALES[unit])
        else:
            vals.update(n * Decimal(10) ** k for k in _BARE)
    return vals


def amount_alerts(line):
    """Alertes d'une observation dont un montant, hors fait balisé et hors zéro, ne se lit pas dans sa citation."""
    if line.get("kind") != "observation" or line.get("amount_origin") == "tagged_reference":
        return []
    out, vals = [], None
    for f in AMOUNT_FIELDS:
        v = line.get(f)
        if v is None:
            continue
        try:
            d = abs(Decimal(str(v)))
        except InvalidOperation:
            continue
        if d == 0:
            continue
        if vals is None:
            vals = quote_values(line.get("quote"))
        if d not in vals:
            out.append(f"{f} {v} ne se lit pas dans la citation : citer le passage qui porte le montant, ou confirmer "
                       "(--confirm) une somme de montants publiés ou un montant écrit en lettres")
    return out
