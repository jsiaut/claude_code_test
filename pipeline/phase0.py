"""Phase 0 : mesurer, sans extraction (§11.1).

Résout les CIK (company_tickers.json fait foi), tire les submissions de chaque CIK,
prédécesseurs compris, toutes pages, fixe la fenêtre et inventorie les dépôts par
société, formulaire et item.
"""
import datetime as dt
import json
import re

import duckdb

from . import calendar as fcal
from . import config
from .edgar import Edgar, cik10
from .net import SecClient

FIRST_PASS_8K_ITEMS = {"1.01", "1.02", "3.03", "8.01"}
SIGNAL_8K_ITEMS = {"1.03", "2.04", "2.06", "3.01", "4.01", "4.02"}
PERIODIC = {"10-K", "10-K/A", "10-Q", "10-Q/A", "10-KT", "10-KT/A", "10-QT", "10-QT/A"}


def _items(s):
    return {x.strip() for x in (s or "").split(",") if x.strip()}


def resolve(e, cfg):
    tickers = e.tickers()
    by_ticker = {v["ticker"].upper(): v for v in tickers.values()}
    groups, excluded = {}, []
    for tk, hint in cfg["groups"].items():
        v = by_ticker.get(tk.upper())
        if v is None:
            excluded.append({"group": tk, "reason": "ticker non résolu par company_tickers.json"})
            continue
        cik = cik10(v["cik_str"])
        groups[tk] = {"cik": cik, "cik_hint": hint, "hint_matches": cik == hint, "title": v["title"],
                      "predecessors": {name: c for name, c in (cfg["predecessors"].get(tk) or {}).items()}}
    return groups, excluded


def collect(as_of, cfg=None):
    cfg = cfg or config.load()
    client = SecClient(as_of, cfg)
    e = Edgar(client, as_of)
    groups, excluded = resolve(e, cfg)
    rows = []
    meta = {}
    for tk, g in groups.items():
        ciks = [(g["cik"], False, g["title"])] + [(c, True, n) for n, c in g["predecessors"].items()]
        for cik, is_pred, label in ciks:
            main, frows, pages, complete = e.submissions(cik)
            meta[cik] = {
                "group": tk, "is_predecessor": is_pred, "name": main.get("name"),
                "sic": main.get("sic"), "sicDescription": main.get("sicDescription"),
                "stateOfIncorporation": main.get("stateOfIncorporation"),
                "fiscalYearEnd": main.get("fiscalYearEnd"), "category": main.get("category"),
                "entityType": main.get("entityType"), "tickers": main.get("tickers"),
                "exchanges": main.get("exchanges"), "formerNames": main.get("formerNames"),
                "pages": pages, "pages_complete": complete, "n_filings": len(frows),
            }
            for f in frows:
                f = dict(f)
                f["group_id"] = tk
                f["filer_cik"] = cik
                f["is_predecessor"] = is_pred
                rows.append(f)
    return client, e, groups, excluded, meta, rows


def build_calendars(groups, meta, rows, cfg, as_of):
    w = cfg["window"]
    out = {}
    for tk, g in groups.items():
        frows = [r for r in rows if r["group_id"] == tk]
        fye = meta[g["cik"]].get("fiscalYearEnd")
        years = fcal.fiscal_calendar(frows, fye, as_of)
        first_filing = min((r["filingDate"] for r in frows), default=None)
        # exercices synthétiques avant le premier rapport périodique (introduction récente)
        known_first = years[0]["fy_end"] if years and years[0].get("fy_end") else None
        synth = []
        if fye and (known_first is None or known_first.year > w["start_fiscal_year"] - 3):
            last_synth = (known_first.year - 1) if known_first else dt.date.fromisoformat(as_of).year
            synth = fcal.synthetic_years(fye, w["start_fiscal_year"] - 4, last_synth)
            if years and years[0].get("fy_start") is None and synth:
                years[0]["fy_start"] = synth[-1]["fy_end"] + dt.timedelta(days=1)
        all_years = synth + years
        win = fcal.window(all_years, w["start_fiscal_year"], w["extended_back_quarters"],
                          w["preceding_quarters"], dt.date.fromisoformat(as_of))
        own_first = min((r["filingDate"] for r in frows if not r["is_predecessor"]), default=None)
        censored = bool(win and first_filing and dt.date.fromisoformat(first_filing) > win["reading_start"])
        out[tk] = {
            "years": [{k: (v.isoformat() if isinstance(v, dt.date) else
                           [x.isoformat() for x in v] if isinstance(v, list) else v)
                       for k, v in y.items()} for y in all_years],
            "window": {k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in (win or {}).items()},
            "first_filing": first_filing, "own_first_filing": own_first,
            "history_left_censored": censored,
            "succession_filings": sorted({r["accessionNumber"] + " " + r["form"] + " " + r["filingDate"]
                                          for r in frows if r["form"].startswith("8-K12")}),
        }
    return out


def inventory(rows, cal):
    """Dépôts de la période de lecture, par société, formulaire et item."""
    inv = []
    for r in rows:
        tk = r["group_id"]
        win = cal[tk]["window"]
        if not win:
            continue
        rs = win["reading_start"]
        ref = r.get("reportDate") or r["filingDate"]
        in_reading = (ref or "") >= rs or r["filingDate"] >= rs
        items = _items(r.get("items"))
        form = r["form"]
        cls = None
        if form in PERIODIC and (r.get("reportDate") or "") >= rs:
            cls = "periodic"
        elif form in ("8-K", "8-K/A") and in_reading and items & FIRST_PASS_8K_ITEMS:
            cls = "8k_first_pass"
        elif form in ("8-K", "8-K/A") and in_reading and items & SIGNAL_8K_ITEMS:
            cls = "8k_signal_only"
        elif form in ("DEF 14A", "DEFA14A", "DEFM14A", "DEFR14A") and r["filingDate"] >= rs:
            cls = "proxy" if form == "DEF 14A" else "proxy_other"
        elif form in ("NT 10-K", "NT 10-Q", "NT 10-K/A", "NT 10-Q/A") and r["filingDate"] >= rs:
            cls = "late_filing"
        elif form in ("424B4", "S-1", "S-1/A") and r["filingDate"] >= rs:
            cls = "ipo"
        elif r["filingDate"] >= rs:
            cls = "other_in_period"
        if cls:
            inv.append({**r, "inv_class": cls})
    return inv


def run(as_of):
    cfg = config.load()
    client, e, groups, excluded, meta, rows = collect(as_of, cfg)
    cal = build_calendars(groups, meta, rows, cfg, as_of)
    inv = inventory(rows, cal)
    config.DB_DIR.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute("CREATE TABLE f AS SELECT * FROM read_json_auto(?)", [_dump(rows, "filings")])
    con.execute(f"COPY f TO '{config.DB_DIR / 'filings.parquet'}' (FORMAT parquet)")
    con.execute("CREATE TABLE i AS SELECT * FROM read_json_auto(?)", [_dump(inv, "inventory")])
    con.execute(f"COPY i TO '{config.DB_DIR / 'inventory.parquet'}' (FORMAT parquet)")
    summary = {"as_of": as_of, "groups": groups, "excluded_groups": excluded, "meta": meta,
               "calendars": cal, "network": client.stats}
    (config.DB_DIR / "phase0.json").write_text(json.dumps(summary, indent=1, default=str))
    return summary


def _dump(rows, name):
    p = config.DB_DIR / f"{name}.json"
    p.write_text(json.dumps(rows, default=str))
    return str(p)


if __name__ == "__main__":
    import sys
    as_of = sys.argv[1] if len(sys.argv) > 1 else dt.datetime.now(dt.timezone.utc).date().isoformat()
    s = run(as_of)
    print(json.dumps({k: s[k] for k in ("groups", "excluded_groups", "network")}, indent=1, default=str))
