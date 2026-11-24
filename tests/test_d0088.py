"""D-0088 (point 8) : une 429 d'un hôte de la SEC est un refus, comme un 403 — pause du client entier, refus comptés
par pause, arrêt définitif après les pauses permises — et le plafond de cadence vaut pour toute commande.
D-0088 (point 10) : la restriction d'un catalogue garde, entre plusieurs blocs de même clé, celui que la référence montre.

Lancement : python3 -m unittest tests.test_d0088 -v
"""
import json
import pathlib
import tempfile
import time
import unittest
from unittest import mock

from pipeline import config, net, reconstruction, sb_own
from tests.test_d0084 import _Mode

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


def _block(key, n, accession="a-1", document="d.htm", kind="montage_text", exhibit_type=None):
    return {"content_key": key, "n": n, "block_kind": kind, "accession": accession, "document": document,
            "exhibit_type": exhibit_type}


class RestrictByReference(unittest.TestCase):
    """Entre plusieurs blocs de même clé, celui que la référence montre ; à défaut, le dernier (point 10)."""

    def _restrict(self, rows, keys, shown):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "c.jsonl"
            p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            with _Mode(keys=keys, shown=shown):
                r = reconstruction.restrict([p])
            kept = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]
        return [(x["content_key"], x["n"]) for x in kept], r["c.jsonl"]

    def test_same_text_in_two_filings_keeps_the_filing_the_reference_shows(self):
        rows = [_block("k", 0, "recent", "q3.htm", "foreign_6k_text"), _block("k", 1, "ancien", "q2.htm", "foreign_6k_text"),
                _block("m", 2, "ancien", "x.htm", "foreign_6k_text"), _block("m", 3, "recent", "y.htm", "foreign_6k_text")]
        shown = {"k": ("foreign_6k_text", "recent", "q3.htm", None), "m": ("foreign_6k_text", "ancien", "x.htm", None)}
        kept, r = self._restrict(rows, {"k", "m"}, shown)
        self.assertEqual(kept, [("k", 0), ("m", 2)])               # ni la première ni la dernière par principe
        self.assertEqual(r, {"kept": 2, "removed": 2})

    def test_same_document_keeps_the_exhibit_type_the_reference_shows(self):
        rows = [_block("k", 0, exhibit_type=float("nan")),          # montage de corpus : pas de type de pièce
                _block("k", 1, exhibit_type="EX-99.1"),             # montage de recherche : le type du résultat
                _block("k", 2, exhibit_type=float("nan"))]
        kept, _ = self._restrict(rows, {"k"}, {"k": ("montage_text", "a-1", "d.htm", "EX-99.1")})
        self.assertEqual(kept, [("k", 1)])
        kept, _ = self._restrict(rows, {"k"}, {"k": ("montage_text", "a-1", "d.htm", None)})
        self.assertEqual(kept, [("k", 2)])                           # deux accords égaux : le dernier

    def test_right_document_without_the_exhibit_type_takes_it_from_the_reference(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "c.jsonl"
            rows = [{**_block("k", 0, exhibit_type=float("nan")), "text": "a\u2028b"}, _block("m", 1, exhibit_type="EX-10.1")]
            p.write_text("".join(json.dumps(r, ensure_ascii=False).replace("\u2028", "\\u2028") + "\n" for r in rows),
                         encoding="utf-8")
            with _Mode(keys={"k", "m"}, shown={"k": ("montage_text", "a-1", "d.htm", "EX-99.2"),
                                               "m": ("montage_text", "a-1", "d.htm", "EX-10.1")}):
                r = reconstruction.restrict([p])
            raw = p.read_text(encoding="utf-8")
            kept = [json.loads(x) for x in raw.split("\n") if x]
        self.assertEqual([(x["content_key"], x["exhibit_type"]) for x in kept], [("k", "EX-99.2"), ("m", "EX-10.1")])
        self.assertEqual(kept[0]["text"], "a\u2028b")                # le texte ne change pas
        self.assertNotIn("\u2028", raw)                              # et reste échappé dans le fichier
        self.assertEqual(r["c.jsonl"], {"kept": 2, "removed": 0, "retyped": 1})

    def test_without_agreement_the_last_one_as_the_loader(self):
        rows = [_block("k", 0, "a-2"), _block("k", 1, "a-3")]
        kept, _ = self._restrict(rows, {"k"}, {"k": ("montage_text", "a-1", "d.htm", None)})
        self.assertEqual(kept, [("k", 1)])

    def test_key_read_in_another_catalog_is_removed(self):
        rows = [_block("k", 0), _block("h", 1)]                     # « h » : arrêtée à son en-tête, sans lecture
        kept, r = self._restrict(rows, {"k", "h"}, {"k": ("item_8k_101", "a-1", "d.htm", None)})
        self.assertEqual(kept, [("h", 1)])
        self.assertEqual(r, {"kept": 1, "removed": 1, "read_elsewhere": 1})

    def test_order_is_kept_and_unkept_keys_removed(self):
        rows = [_block("b", 0), _block("x", 1), _block("a", 2), _block("b", 3, "a-9")]
        kept, _ = self._restrict(rows, {"a", "b"}, {"a": ("montage_text", "a-1", "d.htm", None),
                                                     "b": ("montage_text", "a-1", "d.htm", None)})
        self.assertEqual(kept, [("b", 0), ("a", 2)])

    def test_line_separator_inside_a_text_is_not_a_line_end(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "c.jsonl"
            p.write_text(json.dumps({**_block("k", 0), "text": "a\u2028b"}, ensure_ascii=False) + "\n", encoding="utf-8")
            with _Mode(keys={"k"}):
                reconstruction.restrict([p])
            self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["text"], "a\u2028b")


class SbEnergyNoteSets(unittest.TestCase):
    """Libellés des jeux de notes de SB Energy, par dépôt quand son ordre n'est pas celui du S-1 (point 16)."""

    def test_default_order_is_the_s1(self):
        self.assertEqual(sb_own.sbe_set_label("0001628280-26-062846", 0), "comptes annuels audités")
        self.assertEqual(sb_own.sbe_set_label("0001628280-26-062846", 1), "comptes intermédiaires non audités au 30 juin 2026")
        self.assertEqual(sb_own.sbe_set_label("0001628280-26-062846", 2), "jeu 3")

    def test_third_amendment_has_four_sets(self):
        labels = [sb_own.sbe_set_label("0001628280-26-075026", i) for i in range(5)]
        self.assertIn("31 mars 2026, retraités", labels[1])
        self.assertIn("30 juin 2026, retraités", labels[2])
        self.assertIn("30 septembre 2026", labels[3])
        self.assertEqual(labels[4], "jeu 5")


class NfQueueFile(unittest.TestCase):
    """File d'origine d'une unité de la piste des non-déposants : une valeur manquante vaut D-0044 (point 22)."""

    def test_a_missing_file_is_the_original_queue(self):
        from pipeline import nf_discovery as NF
        self.assertEqual(NF.unit_file({"file": float("nan")}), "D-0044")
        self.assertEqual(NF.unit_file({"file": None}), "D-0044")
        self.assertEqual(NF.unit_file({}), "D-0044")
        self.assertEqual(NF.unit_file({"file": ""}), "D-0044")
        self.assertEqual(NF.unit_file({"file": "D-0074"}), "D-0074")

    def test_original_queue_is_prepared_before_the_others(self):
        import pandas as pd
        from pipeline import nf_discovery as NF
        # état reconstruit puis mis à jour : les unités antérieures n'ont pas de file, les nouvelles ont la leur
        u = pd.DataFrame({"adsh": ["new1", "old2", "old1", "out"], "queue": [1, 2, 1, 3],
                          "status": ["queued", "queued", "queued", "over_cap"],
                          "file": ["D-0074", float("nan"), None, float("nan")]})
        self.assertEqual(list(NF.queue_order(u)["adsh"]), ["old1", "old2", "new1"])
        # sans la colonne : la file d'origine seule, par rang
        self.assertEqual(list(NF.queue_order(u.drop(columns=["file"]))["adsh"]), ["new1", "old1", "old2"])

    def test_the_exclusion_label_names_the_queue(self):
        import inspect
        from pipeline import assemble
        src = inspect.getsource(assemble.nf_discovery_exclusions)
        self.assertIn("NF.unit_file(u)", src)
        self.assertNotIn("u.get('file')", src)


class StopRuleRefusals(unittest.TestCase):
    """Règle d'arrêt du rendu : les 429 d'un hôte de la SEC comptent, et une dernière entrée de refus arrête (point 23)."""

    def _journal(self, rows):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / "journal.jsonl"
        p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        return p

    def test_counts_403_and_sec_429(self):
        from pipeline import render
        u = "https://www.sec.gov/x"
        p = self._journal([{"url": u, "host": "www.sec.gov", "status": 429}, {"url": u, "host": "www.sec.gov", "status": "pause"},
                           {"url": "https://xbrl.fasb.org/x", "host": "xbrl.fasb.org", "status": 429},
                           {"url": u, "host": "data.sec.gov", "status": 403}, {"url": u, "host": "www.sec.gov", "status": 200}])
        self.assertEqual(render.journal_refusals(p), (1, 1, False))

    def test_a_last_refusal_is_a_stop(self):
        from pipeline import render
        u = "https://www.sec.gov/x"
        ok = {"url": u, "host": "www.sec.gov", "status": 200}
        for last in ({"url": u, "host": "www.sec.gov", "status": 403}, {"url": u, "host": "efts.sec.gov", "status": 429},
                     {"url": u, "host": "www.sec.gov", "status": "pause"}, {"url": u, "host": "www.sec.gov", "status": "refused"}):
            self.assertTrue(render.journal_refusals(self._journal([ok, last]))[2], last)
        # une 429 d'un hôte hors SEC reste passagère, et une entrée sans adresse ne compte pas
        self.assertFalse(render.journal_refusals(self._journal([ok, {"url": "https://xbrl.fasb.org/x", "host": "xbrl.fasb.org", "status": 429}]))[2])
        self.assertFalse(render.journal_refusals(self._journal([ok, {"note": "fin de commande", "status": 403}]))[2])


if __name__ == "__main__":
    unittest.main()
