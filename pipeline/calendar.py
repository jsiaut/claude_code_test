"""Calendrier fiscal par groupe et fenêtre (§10.1, §11.1, §13).

La clôture se lit sur period_end (reportDate des 10-K et 10-Q), jamais sur le
fiscalYearEnd de submissions, qui ne donne que celle de l'exercice en cours.
"""
import datetime as dt

ANNUAL = {"10-K", "10-KT", "20-F", "40-F"}
QUARTERLY = {"10-Q", "10-QT"}


def d(s):
    return dt.date.fromisoformat(s[:10]) if s else None


def fiscal_calendar(filings, fiscal_year_end_mmdd=None, as_of=None):
    """filings : lignes de submissions (successeur et prédécesseurs réunis).

    Renvoie une liste d'exercices {fy_end, fy_start, quarters:[(start, end, label)]},
    triée, à partir des reportDate des rapports périodiques originaux.
    """
    fy_ends = sorted({d(f["reportDate"]) for f in filings
                      if f["form"] in ANNUAL and f.get("reportDate")})
    q_ends = sorted({d(f["reportDate"]) for f in filings
                     if f["form"] in QUARTERLY and f.get("reportDate")})
    years = []
    prev_end = None
    for fe in fy_ends:
        start = prev_end + dt.timedelta(days=1) if prev_end else None
        qs = [q for q in q_ends if (start is None or q >= start) and q < fe]
        years.append({"fy_end": fe, "fy_start": start, "q_ends": qs + [fe], "source": "filings"})
        prev_end = fe
    # exercice en cours : trimestres déposés après la dernière clôture annuelle
    last = fy_ends[-1] if fy_ends else None
    tail = [q for q in q_ends if last is None or q > last]
    if tail:
        if fiscal_year_end_mmdd and last:
            exp_end = _next_fy_end(last, fiscal_year_end_mmdd)
        elif fiscal_year_end_mmdd:
            exp_end = _fy_end_on_or_after(tail[0], fiscal_year_end_mmdd)
        else:
            exp_end = None
        years.append({"fy_end": exp_end, "fy_start": last + dt.timedelta(days=1) if last else None,
                      "q_ends": tail, "source": "filings_partial", "in_progress": True})
    return years


def _fy_end_on_or_after(day, mmdd):
    m, dd = int(mmdd[:2]), int(mmdd[2:])
    cand = dt.date(day.year, m, min(dd, 28 if m == 2 else dd))
    return cand if cand >= day else dt.date(day.year + 1, m, cand.day)


def _next_fy_end(last_end, mmdd):
    """Clôture approximative de l'exercice suivant (52/53 semaines : ±7 jours)."""
    return last_end + dt.timedelta(days=364 if _is_5253(mmdd, last_end) else 365)


def _is_5253(mmdd, last_end):
    m, dd = int(mmdd[:2]), int(mmdd[2:])
    try:
        return dt.date(last_end.year, m, dd) != last_end
    except ValueError:
        return True


def synthetic_years(fiscal_year_end_mmdd, first_year, last_year):
    """Exercices synthétiques pour les périodes sans dépôt (introduction récente)."""
    m, dd = int(fiscal_year_end_mmdd[:2]), int(fiscal_year_end_mmdd[2:])
    out = []
    for y in range(first_year, last_year + 1):
        end = dt.date(y, m, dd)
        start = dt.date(y - 1, m, dd) + dt.timedelta(days=1)
        qs = []
        for k in (3, 6, 9):
            mm = (start.month - 1 + k) % 12 + 1
            yy = start.year + (start.month - 1 + k) // 12
            qs.append(dt.date(yy, mm, 1) - dt.timedelta(days=1))
        out.append({"fy_end": end, "fy_start": start, "q_ends": qs + [end], "source": "synthetic"})
    return out


def window(years, start_fiscal_year, extended_back_quarters, preceding_quarters, as_of):
    """Fenêtre d'analyse, fenêtre allongée et période de lecture du texte (§11.1, E.0).

    Fenêtre : du premier exercice clos en start_fiscal_year jusqu'à as_of.
    Fenêtre allongée : reculée de quatre trimestres (un exercice).
    Période de lecture : fenêtre allongée et les huit trimestres qui la précèdent.
    """
    closed = [y for y in years if y.get("fy_end") and y["fy_end"].year == start_fiscal_year
              and not y.get("in_progress")]
    if not closed:
        return None
    first = closed[0]
    idx = years.index(first)
    back_years = (extended_back_quarters + preceding_quarters) // 4
    ext_years = extended_back_quarters // 4

    def start_of(i):
        if i >= 0 and years[i].get("fy_start"):
            return years[i]["fy_start"]
        # avant le premier exercice connu : approximation par années pleines
        base = first["fy_start"] or (first["fy_end"] - dt.timedelta(days=364))
        n = idx - i
        try:
            return base.replace(year=base.year - n)
        except ValueError:
            return base.replace(year=base.year - n, day=28)

    return {
        "window_start": start_of(idx),
        "window_first_fy_end": first["fy_end"],
        "extended_start": start_of(idx - ext_years),
        "reading_start": start_of(idx - back_years),
        "as_of": as_of,
    }


def quarters(years):
    """Liste plate des trimestres fiscaux (start, end, fy_end, qn)."""
    out = []
    for y in years:
        start = y.get("fy_start")
        for i, qe in enumerate(y["q_ends"]):
            out.append({"start": start, "end": qe, "fy_end": y.get("fy_end"), "q": i + 1,
                        "source": y["source"]})
            start = qe + dt.timedelta(days=1)
    return out
