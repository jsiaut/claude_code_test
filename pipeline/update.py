"""Files plafonnées d'une exécution à l'autre (D-0074, point 3).

La règle de D-0058 (point 24) pour un lexique enrichi s'étend à une période nouvelle : une unité tirée d'un dépôt daté
au plus de l'as_of précédent garde son état, admise si elle était au catalogue de l'exécution précédente, au-delà du
plafond sinon ; les unités de la période nouvelle forment une file à part, dans l'ordre où elles sont présentées, avec
le même plafond. Sans as_of précédent, c'est le plafond simple : les `cap` premières unités de chaque groupe.

Un catalogue préparé (montages, 6-K, SoftBank) ne se recalcule pas sur la période ancienne : son recalcul dépend de ce
qui a été lu depuis (une fenêtre déjà lue devient « déjà lue »), si bien qu'un recalcul complet au même as_of fait sortir
du catalogue des blocs lus. Une exécution nouvelle garde donc les blocs de l'exécution précédente tels quels, copiés une
fois avant leur première réécriture, et n'y ajoute que ceux des dépôts de la période nouvelle (D-0074, point 3).
"""
import json
import shutil
from collections import Counter

from . import config


class Admission:
    def __init__(self, cap, admitted=(), since=None):
        self.cap, self.admitted, self.since = int(cap), set(admitted), since
        self.taken = Counter()

    def take(self, key, date, group=None):
        """Vrai si l'unité `key` (dépôt daté `date`) est admise dans la file de son groupe."""
        if self.since is not None and str(date or "")[:10] <= self.since:
            return key in self.admitted
        if self.taken[group] >= self.cap:
            return False
        self.taken[group] += 1
        return True


def admission(cap, admitted=()):
    """Admission à l'as_of de l'exécution : sa période nouvelle commence après l'as_of précédent (config.yaml)."""
    return Admission(cap, admitted, config.previous_as_of())


def catalog_keys(path, field="content_key", where=lambda b: True):
    """Clés des blocs d'un catalogue JSONL (celui de l'exécution précédente, avant sa réécriture)."""
    if not path.exists():
        return set()
    out = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                b = json.loads(line)
                if where(b):
                    out.add(b.get(field))
    return out


def previous_state(path, since):
    """Fichier de l'exécution précédente (catalogue, état d'une file), copié une fois, avant sa première réécriture par
    l'exécution nouvelle, sous {nom}.{as_of précédent}{suffixe}."""
    snap = path.with_name(f"{path.stem}.{since}{path.suffix}")
    if not snap.exists() and path.exists():
        shutil.copy2(path, snap)
    return snap


def read_jsonl(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def carry_over(previous, recomputed, since, key="content_key"):
    """Catalogue d'une exécution nouvelle : les blocs de l'exécution précédente tels quels, dans leur ordre, puis ceux du
    recalcul tirés de dépôts de la période nouvelle dont la clé n'y est pas déjà (un texte identique se lit une fois)."""
    if since is None:
        return list(recomputed)
    keys = {b.get(key) for b in previous}
    return list(previous) + [b for b in recomputed
                             if str(b.get("filing_date") or "")[:10] > since and b.get(key) not in keys]
