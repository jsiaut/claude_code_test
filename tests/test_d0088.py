"""D-0088 (point 8) : une 429 d'un hôte de la SEC est un refus, comme un 403 — pause du client entier, refus comptés
par pause, arrêt définitif après les pauses permises — et le plafond de cadence vaut pour toute commande.

Lancement : python3 -m unittest tests.test_d0088 -v
"""
import json
import pathlib
import tempfile
import time
import unittest
from unittest import mock

from pipeline import config, net

REFUSAL = b"<html><head><title>SEC.gov | Request Rate\n Threshold Exceeded</title></head><body></body></html>"


class _Response:
    def __init__(self, status, content=b"ok"):
        self.status_code, self.content, self.headers = status, content, {}


class _Session:
    """Session factice : rend les statuts dans l'ordre (le dernier se répète) et note l'heure de chaque requête."""

    def __init__(self, statuses):
        self.statuses, self.calls = list(statuses), []

    def request(self, method, url, headers=None, timeout=None, stream=False):
        self.calls.append(time.monotonic())
        status = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
        return _Response(status, b"ok" if status == 200 else REFUSAL)


def _client(directory, statuses, pause=0.2, max_pauses=3, cruise=200, ceiling=200):
    cfg = {"network": {"cruise_requests_per_second": cruise, "sec_ceiling_requests_per_second": ceiling,
                       "pause_after_403_seconds": 600, "max_consecutive_403_pauses": max_pauses,
                       "retry_backoff_seconds": [0, 0, 0]},
           "user_agent": {"sec_hosts": ["www.sec.gov"]}}
    with mock.patch.object(config, "user_agent", lambda cfg=None: "essai"):
        c = net.SecClient("2026-11-14", cfg, journal_path=pathlib.Path(directory) / "journal.jsonl")
    c.pause_403 = pause          # la configuration ne porte que des secondes entières
    c.session = _Session(statuses)
    return c


def _journal(client):
    return [json.loads(x) for x in pathlib.Path(client.journal_path).read_text(encoding="utf-8").splitlines()]


class Refusal429(unittest.TestCase):
    def test_429_from_sec_pauses_the_client_then_asks_the_same_url(self):
        with tempfile.TemporaryDirectory() as d:
            c = _client(d, [429, 200])
            body, _ = c.get("https://www.sec.gov/a")
            rows = _journal(c)
        self.assertEqual(body, b"ok")
        self.assertEqual(len(c.session.calls), 2)
        self.assertGreaterEqual(c.session.calls[1] - c.session.calls[0], 0.2)       # silence pendant la pause
        self.assertEqual([r["status"] for r in rows], [429, "pause", 200])
        self.assertEqual({r["url"] for r in rows}, {"https://www.sec.gov/a"})
        self.assertEqual(rows[0]["note"], "SEC.gov | Request Rate Threshold Exceeded")  # titre de la page de refus
        self.assertIn("après 429", rows[1]["note"])

    def test_403_still_pauses(self):
        with tempfile.TemporaryDirectory() as d:
            c = _client(d, [403, 200])
            c.get("https://www.sec.gov/a")
            self.assertEqual([r["status"] for r in _journal(c)], [403, "pause", 200])

    def test_refusals_count_by_pause_not_by_response(self):
        with tempfile.TemporaryDirectory() as d:
            c = _client(d, [200])
            self.assertTrue(c._refusal(0.3))             # ouvre la pause
            self.assertFalse(c._refusal(0.3))            # même épisode, vu par un autre fil : prolonge sans compter
            self.assertEqual(c._consecutive_403, 1)

    def test_success_between_two_refusals_resets_the_count(self):
        with tempfile.TemporaryDirectory() as d:
            c = _client(d, [429, 200, 429, 200], pause=0.05, max_pauses=1)
            c.get("https://www.sec.gov/a")
            c.get("https://www.sec.gov/b")               # une seconde pause de suite arrêterait le client
            self.assertEqual(len(c.session.calls), 4)

    def test_durable_refusal_stops_for_good(self):
        with tempfile.TemporaryDirectory() as d:
            c = _client(d, [429], pause=0.05, max_pauses=2)
            with self.assertRaises(net.AccessRefused):
                c.get("https://www.sec.gov/a")
            self.assertEqual(len(c.session.calls), 3)    # deux pauses, puis le refus de trop
            with self.assertRaises(net.AccessRefused):
                c.get("https://www.sec.gov/b")
            self.assertEqual(len(c.session.calls), 3)    # plus aucune requête ne part
            self.assertEqual([r["status"] for r in _journal(c)], [429, "pause", 429, "pause", 429, "refused"])

    def test_access_refused_passes_through_generic_handlers(self):
        def piece():
            try:
                raise net.AccessRefused("refus durable")
            except Exception:                            # « une pièce illisible ne coupe pas la vérification »
                return "avalé"
        with self.assertRaises(net.AccessRefused):
            piece()

    def test_429_from_another_host_stays_transient(self):
        with tempfile.TemporaryDirectory() as d:
            c = _client(d, [429])
            with self.assertRaises(net.NotCollected):
                c.get("https://xbrl.fasb.org/a")
            self.assertEqual(len(c.session.calls), 4)    # trois reprises, sans pause du client
            self.assertEqual([r["status"] for r in _journal(c)], [429] * 4)


class Cadence(unittest.TestCase):
    def test_ceiling_binds_a_command_that_sets_its_own_rate(self):
        with tempfile.TemporaryDirectory() as d:
            c = _client(d, [200], cruise=2, ceiling=2)
            c.min_interval = 0.01                        # une commande qui règle sa cadence (rate=4.0, par exemple)
            t = []
            for _ in range(3):
                c._wait_slot()
                t.append(time.monotonic())
        self.assertGreaterEqual(t[2] - t[0], 0.95)       # jamais plus de deux départs par seconde glissante

    def test_configured_cadence(self):
        n = config.load()["network"]
        self.assertLessEqual(n["sec_ceiling_requests_per_second"], 2)         # D-0088, jusqu'à nouvel ordre
        self.assertLessEqual(n["cruise_requests_per_second"], n["sec_ceiling_requests_per_second"])
        self.assertGreaterEqual(n["pause_after_403_seconds"], 600)            # §9.5 : dix minutes au moins


if __name__ == "__main__":
    unittest.main()
