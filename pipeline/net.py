"""Client HTTP unique vers la SEC (§9.5).

Toute requête vers www.sec.gov, data.sec.gov, efts.sec.gov ou xbrl.sec.gov passe
par ce client : un seul User-Agent, la cadence de `config.yaml` (5 requêtes par
seconde au plus, §9.5 ; 2 depuis D-0088), une pause d'au moins 10 minutes après un
refus — 403 ou 429 — pendant laquelle aucune requête ne part vers la SEC, quelques
nouvelles tentatives espacées sur 5xx et délais dépassés, et chaque requête au
journal. Le User-Agent n'est jamais envoyé à un autre hôte.

Un refus se compte par pause : celui qui arrive pendant une pause déjà ouverte
(requête partie avant elle, par un autre fil) la prolonge sans compter. Après
`max_consecutive_403_pauses` pauses sans succès entre elles, le client s'arrête
pour de bon (D-0088, point 8).
"""
import datetime as dt
import json
import os
import re
import threading
import time
import urllib.parse

import requests

from . import config


class AccessRefused(SystemExit):
    """Refus d'accès durable de la SEC malgré les pauses : arrêt (§11.4). Dérive de SystemExit pour traverser les
    enveloppes `except Exception` des commandes (« une pièce illisible ne coupe pas la vérification ») : après un
    refus durable, la commande s'arrête au lieu de passer à la pièce suivante (D-0088, point 8)."""


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
        self._consecutive_403 = 0  # pauses ouvertes depuis le dernier succès (403 et 429)
        self._refused = None       # motif de l'arrêt définitif, une fois le refus durable constaté
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

    def _refusal(self, seconds):
        """Refus de la SEC (403 ou 429) : ouvre ou prolonge la pause du client entier. Renvoie True si le refus ouvre
        une pause nouvelle, False s'il arrive pendant une pause déjà ouverte (même épisode, vu par un autre fil)."""
        with self._lock:
            now = time.monotonic()
            opened = now >= self._paused_until
            if opened:
                self._consecutive_403 += 1
            self._paused_until = max(self._paused_until, now + seconds)
            return opened

    # -- requête ---------------------------------------------------------------
    def get(self, url, timeout=120, dest=None, method="GET"):
        """Corps de la ressource, ou, avec `dest`, écrit en flux dans ce fichier (archives de
        plusieurs centaines de Mo) : le corps renvoyé est alors None et ses octets comptent au
        journal comme les autres. `method="HEAD"` ne demande que les en-têtes (date de
        publication d'une archive) : même limiteur, même journal, corps vide."""
        host = urllib.parse.urlparse(url).hostname or ""
        is_sec = host in self.sec_hosts
        headers = {"User-Agent": self.ua} if is_sec else {}
        attempt = 0
        transient = 0
        while True:
            attempt += 1
            if is_sec:
                if self._refused:                      # arrêt définitif : plus aucune requête vers la SEC
                    raise AccessRefused(self._refused)
                self._wait_slot()
            t0 = time.monotonic()
            ts_start = _utcnow().isoformat(timespec="milliseconds")
            try:
                resp = self.session.request(method, url, headers=headers, timeout=timeout, stream=dest is not None)
                if dest is not None and resp.status_code == 200:
                    n = 0
                    tmp = str(dest) + ".part"
                    with open(tmp, "wb") as fh:
                        for chunk in resp.iter_content(chunk_size=1 << 20):
                            fh.write(chunk)
                            n += len(chunk)
                    os.replace(tmp, dest)
                    resp._content = b""
                    resp._streamed_bytes = n
            except requests.exceptions.ProxyError as exc:
                self.journal(url=url, host=host, status="proxy_error", bytes=0,
                             attempt=attempt, note=str(exc)[:200])
                raise EgressBlocked(f"{host} refusé par la politique réseau de l'environnement") from exc
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError) as exc:
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
            nbytes = getattr(resp, "_streamed_bytes", len(body))
            note = None
            refusal = is_sec and status in (403, 429)
            if refusal:
                m = re.search(rb"<title>(.*?)</title>", body[:4000], re.I | re.S)
                note = re.sub(r"\s+", " ", m.group(1).decode("utf-8", "replace")).strip()[:200] if m else str(status)
            self.journal(url=url, host=host, status=status, bytes=nbytes, ts_start=ts_start,
                         elapsed_ms=int(elapsed * 1000), attempt=attempt, note=note,
                         **({"method": method} if method != "GET" else {}))
            if is_sec:
                self.stats["requests"] += 1
                self.stats["bytes"] += nbytes
                self.stats["elapsed"] += elapsed
            if status == 200:
                if is_sec and time.monotonic() >= self._paused_until:      # un succès hors pause clôt l'épisode
                    self._consecutive_403 = 0
                return (None if dest is not None else body), resp.headers
            if refusal:
                # 403 ou 429 d'un hôte de la SEC : silence du client entier, puis la même adresse (§9.5, D-0088)
                if self._refusal(self.pause_403):
                    if self._consecutive_403 > self.max_403:
                        self._refused = f"{status} persistant malgré {self.max_403} pauses : {note}"
                        self.journal(url=url, host=host, status="refused", bytes=0, note=self._refused)
                        raise AccessRefused(self._refused)
                    self.journal(url=url, host=host, status="pause", bytes=0,
                                 note=f"pause {self.pause_403} s après {status} ({note})")
                continue
            if status in (404, 410):
                raise NotCollected(url, status, "absent")
            if status == 429 or status >= 500:         # 429 d'un hôte hors SEC, ou erreur de serveur
                if transient < len(self.backoff):
                    time.sleep(self.backoff[transient])
                    transient += 1
                    continue
                raise NotCollected(url, status, "échecs répétés")
            raise NotCollected(url, status, "statut inattendu")
