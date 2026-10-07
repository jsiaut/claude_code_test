"""Client HTTP unique vers la SEC (§9.5).

Toute requête vers www.sec.gov, data.sec.gov, efts.sec.gov ou xbrl.sec.gov passe
par ce client : un seul User-Agent, 5 requêtes par seconde au plus, une pause d'au
moins 10 minutes après un 403 (aucune requête SEC pendant la pause), quelques
nouvelles tentatives espacées sur 429, 5xx et délais dépassés, et chaque requête
au journal. Le User-Agent n'est jamais envoyé à un autre hôte.
"""
import datetime as dt
import json
import re
import threading
import time
import urllib.parse

import requests

from . import config
from .lock import touch_lock


class AccessRefused(Exception):
    """Refus d'accès durable de la SEC malgré les pauses : arrêt (§11.4)."""


class EgressBlocked(Exception):
    """L'hôte est refusé par la politique réseau de l'environnement, pas par la SEC."""


class NotCollected(Exception):
    """Ressource non obtenue pour cette exécution (404, 410, échecs répétés)."""

    def __init__(self, url, status, reason):
        super().__init__(f"{status} {url} ({reason})")
        self.url, self.status, self.reason = url, status, reason


def _utcnow():
    return dt.datetime.now(dt.timezone.utc)


class SecClient:
    def __init__(self, as_of, cfg=None, journal_path=None):
        self.cfg = cfg or config.load()
        net = self.cfg["network"]
        self.ua = config.user_agent(self.cfg)
        self.sec_hosts = set(self.cfg["user_agent"]["sec_hosts"])
        self.min_interval = 1.0 / float(net["cruise_requests_per_second"])
        self.ceiling = int(net["sec_ceiling_requests_per_second"])
        self.pause_403 = int(net["pause_after_403_seconds"])
        self.max_403 = int(net["max_consecutive_403_pauses"])
        self.backoff = list(net["retry_backoff_seconds"])
        self.as_of = as_of
        self.journal_path = journal_path or config.JOURNAL
        self._lock = threading.Lock()
        self._jlock = threading.Lock()
        self._last_start = 0.0
        self._recent = []          # départs des requêtes SEC sur la dernière seconde
        self._paused_until = 0.0
        self._consecutive_403 = 0
        self.session = requests.Session()
        self.session.headers.update({"Accept-Encoding": "gzip, deflate"})
        self.stats = {"requests": 0, "bytes": 0, "elapsed": 0.0}

    # -- journal -----------------------------------------------------------
    def journal(self, **rec):
        line = {"as_of": self.as_of, "ts": _utcnow().isoformat(timespec="milliseconds")}
        line.update(rec)
        with self._jlock:
            with open(self.journal_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(line, ensure_ascii=False) + "\n")

    # -- limiteur ------------------------------------------------------------
    def _wait_slot(self):
        while True:
            with self._lock:
                now = time.monotonic()
                if now < self._paused_until:
                    wait = self._paused_until - now
                else:
                    self._recent = [t for t in self._recent if now - t < 1.0]
                    gap = now - self._last_start
                    if gap >= self.min_interval and len(self._recent) < self.ceiling:
                        self._last_start = now
                        self._recent.append(now)
                        return
                    wait = max(self.min_interval - gap, 0.01)
            time.sleep(min(wait, 5.0))

    def _pause(self, seconds):
        with self._lock:
            self._paused_until = max(self._paused_until, time.monotonic() + seconds)

    # -- requête ---------------------------------------------------------------
    def get(self, url, timeout=120):
        host = urllib.parse.urlparse(url).hostname or ""
        is_sec = host in self.sec_hosts
        headers = {"User-Agent": self.ua} if is_sec else {}
        attempt = 0
        transient = 0
        while True:
            attempt += 1
            if is_sec:
                self._wait_slot()
            t0 = time.monotonic()
            ts_start = _utcnow().isoformat(timespec="milliseconds")
            try:
                resp = self.session.get(url, headers=headers, timeout=timeout)
            except requests.exceptions.ProxyError as exc:
                self.journal(url=url, host=host, status="proxy_error", bytes=0,
                             attempt=attempt, note=str(exc)[:200])
                raise EgressBlocked(f"{host} refusé par la politique réseau de l'environnement") from exc
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                self.journal(url=url, host=host, status="network_error", bytes=0,
                             attempt=attempt, note=type(exc).__name__)
                if transient < len(self.backoff):
                    time.sleep(self.backoff[transient])
                    transient += 1
                    continue
                raise NotCollected(url, "network_error", type(exc).__name__)
            elapsed = time.monotonic() - t0
            body = resp.content
            status = resp.status_code
            note = None
            if status == 403 and is_sec:
                m = re.search(rb"<title>(.*?)</title>", body[:4000], re.I | re.S)
                note = m.group(1).decode("utf-8", "replace").strip() if m else "403"
            self.journal(url=url, host=host, status=status, bytes=len(body), ts_start=ts_start,
                         elapsed_ms=int(elapsed * 1000), attempt=attempt, note=note)
            if is_sec:
                touch_lock()
                self.stats["requests"] += 1
                self.stats["bytes"] += len(body)
                self.stats["elapsed"] += elapsed
            if status == 200:
                if is_sec:
                    self._consecutive_403 = 0
                return body, resp.headers
            if status == 403 and is_sec:
                self._consecutive_403 += 1
                if self._consecutive_403 > self.max_403:
                    raise AccessRefused(f"403 persistant malgré {self.max_403} pauses : {note}")
                self.journal(url=url, host=host, status="pause", bytes=0,
                             note=f"pause {self.pause_403} s après 403 ({note})")
                self._pause(self.pause_403)
                continue
            if status in (404, 410):
                raise NotCollected(url, status, "absent")
            if status == 429 or status >= 500:
                if transient < len(self.backoff):
                    time.sleep(self.backoff[transient])
                    transient += 1
                    continue
                raise NotCollected(url, status, "échecs répétés")
            raise NotCollected(url, status, "statut inattendu")
