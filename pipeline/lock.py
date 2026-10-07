"""Verrou de session (§11.5) : une seule session à la fois."""
import datetime as dt
import json
import os
import time

from . import config


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def acquire(as_of, stale_minutes=None, label="interactive"):
    """Prend le verrou ; refuse si un verrou vivant existe (touché il y a moins du délai)."""
    cfg = config.load()
    stale = (stale_minutes or cfg["session_stale_minutes"]) * 60
    config.LOCK.parent.mkdir(parents=True, exist_ok=True)
    if config.LOCK.exists():
        age = time.time() - config.LOCK.stat().st_mtime
        info = config.LOCK.read_text(encoding="utf-8")
        if age < stale:
            try:
                same = json.loads(info).get("label") == label
            except ValueError:
                same = False
            if not same:
                raise SystemExit(f"Verrou vivant (touché il y a {int(age)} s) : {info}")
    config.LOCK.write_text(json.dumps({"pid": os.getpid(), "as_of": as_of, "label": label,
                                       "opened": _now()}), encoding="utf-8")


def touch_lock():
    """Touché à chaque bloc validé et à chaque requête SEC."""
    try:
        if config.LOCK.exists():
            os.utime(config.LOCK, None)
    except OSError:
        pass


def release():
    try:
        config.LOCK.unlink()
    except FileNotFoundError:
        pass
