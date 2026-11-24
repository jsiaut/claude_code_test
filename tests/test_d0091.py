"""D-0091 : état versionné sans texte de dépôt, archives des jeux de données tirées une fois, reconstruction en une
commande.

Lancement : python3 -m unittest tests.test_d0091 -v
"""
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import pandas as pd

from pipeline import config, net, rebuild, reconstruction, state


# -- archives gardées (point 4) ---------------------------------------------------------------------------------------

class _Stream:
    def __init__(self, body, headers):
        self.status_code, self.headers, self._body, self.content = 200, headers, body, b""

    def iter_content(self, chunk_size=1):
        yield self._body


class _Session:
    def __init__(self):
        self.calls = []

    def request(self, method, url, headers=None, timeout=None, stream=False):
        self.calls.append(url)
        return _Stream(b"PK-archive-" + url.encode()[-12:], {"Last-Modified": "Wed, 07 Oct 2026 15:16:19 GMT"})


def _client(directory, keep):
    cfg = {"network": {"cruise_requests_per_second": 200, "sec_ceiling_requests_per_second": 200,
                       "pause_after_403_seconds": 600, "max_consecutive_403_pauses": 3, "retry_backoff_seconds": [0]},
           "user_agent": {"sec_hosts": ["www.sec.gov"]}}
    with mock.patch.object(config, "user_agent", lambda cfg=None: "essai"):
        c = net.SecClient("2026-11-23", cfg, journal_path=pathlib.Path(directory) / "journal.jsonl")
    c.keep_dir = pathlib.Path(directory) / "kept" if keep else None
    c.session = _Session()
    return c


class KeptArchives(unittest.TestCase):
    URL = "https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2026_09_notes.zip"

    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.dir = pathlib.Path(d.name)

    def test_a_kept_archive_is_served_again_without_a_request(self):
        c = _client(self.dir, keep=True)
        a, b = self.dir / "a.zip", self.dir / "b.zip"
        _, h1 = c.get(self.URL, dest=a)
        a.unlink()                                                    # le premier lecteur efface son archive
        _, h2 = c.get(self.URL, dest=b)
        self.assertEqual(len(c.session.calls), 1)                     # une seule requête pour deux lecteurs
        self.assertEqual(b.read_bytes(), b"PK-archive-" + self.URL.encode()[-12:])
        self.assertEqual(h2.get("Last-Modified"), h1.get("Last-Modified"))
        self.assertEqual(h2.get("last-modified"), "Wed, 07 Oct 2026 15:16:19 GMT")
        rows = [json.loads(x) for x in (self.dir / "journal.jsonl").read_text().splitlines()]
        self.assertEqual([r.get("status") for r in rows], [200, "reused"])
        self.assertNotIn("url", rows[1])                              # une reprise n'est pas une requête
        self.assertEqual(rows[1]["resource"], self.URL)

    def test_nothing_is_kept_outside_the_rebuild(self):
        c = _client(self.dir, keep=False)
        c.get(self.URL, dest=self.dir / "a.zip")
        c.get(self.URL, dest=self.dir / "b.zip")
        self.assertEqual(len(c.session.calls), 2)
        self.assertFalse((self.dir / "kept").exists())

    def test_the_environment_variable_turns_it_on(self):
        with mock.patch.object(config, "user_agent", lambda cfg=None: "essai"):
            with mock.patch.dict("os.environ", {net.KEEP_ENV: "1"}):
                self.assertEqual(net.SecClient("2026-11-23").keep_dir, net.KEEP_DIR)
            with mock.patch.dict("os.environ", {}, clear=False) as env:
                env.pop(net.KEEP_ENV, None)
                self.assertIsNone(net.SecClient("2026-11-23").keep_dir)

    def test_a_family_is_dropped_after_its_last_reader(self):
        c = _client(self.dir, keep=True)
        other = "https://www.sec.gov/files/dera/data/form-n-port-data-sets/2026q2_nport.zip"
        c.get(self.URL, dest=self.dir / "a.zip")
        c.get(other, dest=self.dir / "b.zip")
        kept = self.dir / "kept"
        self.assertEqual(sorted(u for u, _, _ in net.kept_archives(kept)), sorted([self.URL, other]))
        self.assertEqual(net.drop_kept(rebuild.NOTES_URL, kept), 1)
        self.assertEqual([u for u, _, _ in net.kept_archives(kept)], [other])
        self.assertEqual(net.drop_kept(rebuild.NPORT_URL, kept), 1)
        self.assertEqual(list(kept.iterdir()), [])


# -- état versionné (point 3) -----------------------------------------------------------------------------------------

def _block(key, **more):
    return {"content_key": key, "block_kind": "montage_text", "accession": "0000000001-26-000001", "document": "a.htm",
            "text": "Texte du dépôt, M. Untel compris.", "note_label": "Titre de note", "filer_name": "SOCIETE X",
            "chars": 33, "sort_key": "mt00000", **more}


class VersionedState(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.db, self.state = pathlib.Path(d.name) / "db", pathlib.Path(d.name) / "state"
        self.db.mkdir()
        (self.db / "exhibits_tranche.json").write_text('{"a": "EX-10.1"}', encoding="utf-8")
        (self.db / "usgaap2026_balance.json").write_text('{"Assets": "debit"}', encoding="utf-8")
        (self.db / "montages_blocks.jsonl").write_text(
            "".join(json.dumps(b) + "\n" for b in (_block("k1", exhibit_type=float("nan")), _block("k2", window=3))),
            encoding="utf-8")
        (self.db / "montages_info_x.json").write_text('{"over_cap": [{"adsh": "a", "file": "f", "window": 1}]}', encoding="utf-8")
        (self.db / "montages_info_x.2026-11-14.json").write_text("{}", encoding="utf-8")      # copie datée : hors état
        pd.DataFrame({"order": [1, 2], "rank": [1, 7], "cik": ["12", "34"], "queue": [float("nan"), 2.5],
                      "latest": [True, False], "file": [None, "D-0074"]}).to_parquet(self.db / "discovery_units.parquet")

    def test_save_check_and_no_filing_text(self):
        self.assertEqual(sorted(state.check(self.db, self.state))[:1], ["STATE.json"])     # rien de sauvé
        state.save(self.db, self.state)
        self.assertEqual(state.check(self.db, self.state), [])
        self.assertEqual(sorted(p.relative_to(self.state).as_posix() for p in self.state.rglob("*") if p.is_file()),
                         ["STATE.json", "catalogs/montages.jsonl", "hand/exhibits_tranche.json",
                          "hand/usgaap2026_balance.json", "lists/montages_info_x.json", "queues/discovery_units.jsonl"])
        rows = [json.loads(x) for x in (self.state / "catalogs" / "montages.jsonl").read_text().splitlines()]
        self.assertEqual([r["content_key"] for r in rows], ["k1", "k2"])                   # ordre du catalogue
        for r in rows:
            self.assertLessEqual(set(r), set(state.MANIFEST_FIELDS))                       # liste fermée de champs
        self.assertNotIn("exhibit_type", rows[0])                                          # type de pièce absent : pas de NaN
        blob = (self.state / "catalogs" / "montages.jsonl").read_text()
        for leaked in ("Untel", "Titre de note", "SOCIETE X"):
            self.assertNotIn(leaked, blob)
        # un changement de db/ se voit ; une nouvelle sauvegarde ne réécrit que lui
        (self.db / "montages_info_x.json").write_text('{"over_cap": []}', encoding="utf-8")
        self.assertEqual(state.check(self.db, self.state), ["lists/montages_info_x.json"])
        self.assertEqual(state.save(self.db, self.state), ["lists/montages_info_x.json"])

    def test_the_manifest_fields_carry_no_text(self):
        for f in ("text", "candidate_facts", "note_label", "filer_name", "terms", "queries", "locator", "sgml_description",
                  "incorporation_quote", "issuer_name", "party_terms"):
            self.assertNotIn(f, state.MANIFEST_FIELDS)

    def test_a_queue_comes_back_without_loss(self):
        state.save(self.db, self.state)
        out = self.db.parent / "db2"
        out.mkdir()
        self.assertTrue(state.restore_queue("discovery_units.parquet", db=out, state=self.state))
        a, b = pd.read_parquet(self.db / "discovery_units.parquet"), pd.read_parquet(out / "discovery_units.parquet")
        self.assertTrue(a.equals(b))
        self.assertEqual(list(a.dtypes), list(b.dtypes))
        self.assertFalse(state.restore_queue("nf_discovery_units.parquet", db=out, state=self.state))   # absente de l'état

    def test_hand_files_and_lists_come_back(self):
        state.save(self.db, self.state)
        out = self.db.parent / "db3"
        self.assertEqual(state.restore_hand(db=out, state=self.state), list(state.HAND))
        self.assertEqual(json.loads((out / "usgaap2026_balance.json").read_text()), {"Assets": "debit"})
        self.assertEqual(state.restore_lists(db=out, state=self.state), ["montages_info_x.json"])

    def test_the_committed_state_describes_the_committed_tables(self):
        # l'état versionné du dépôt : présent, à l'as_of de la configuration, sans champ hors de la liste fermée
        self.assertTrue(state.present())
        head = json.loads((state.STATE / "STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(head["as_of"], config.as_of())
        for name, rows in state.manifests().items():
            self.assertTrue(rows, name)
            self.assertLessEqual({k for r in rows for k in r}, set(state.MANIFEST_FIELDS), name)
        self.assertEqual(sorted(p.name for p in (state.STATE / "hand").iterdir()), sorted(state.HAND))


# -- la reconstruction s'en sert (point 3) ----------------------------------------------------------------------------

class RestrictFollowsTheManifest(unittest.TestCase):
    def test_keys_documents_and_order(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "montages_blocks.jsonl"
            cat = [_block("read", document="b.htm", accession="acc-B"),         # lu, mais d'un autre dépôt que le manifeste
                   _block("unread"),                                            # préparé, jamais lu
                   _block("read", document="a.htm", accession="acc-A"),         # le dépôt que le manifeste nomme
                   _block("drift"),                                             # fenêtre recalculée, absente du manifeste
                   _block("first")]
            p.write_text("".join(json.dumps(b) + "\n" for b in cat), encoding="utf-8")
            man = {"montages_blocks.jsonl": [
                {"content_key": "first", "block_kind": "montage_text", "accession": "0000000001-26-000001", "document": "a.htm"},
                {"content_key": "read", "block_kind": "montage_text", "accession": "acc-A", "document": "a.htm"},
                {"content_key": "unread", "block_kind": "montage_text", "accession": "0000000001-26-000001", "document": "a.htm"},
                {"content_key": "gone", "block_kind": "montage_text", "accession": "x", "document": "x.htm"}]}
            with mock.patch.object(reconstruction, "keys", lambda: {"read"}), \
                    mock.patch.object(reconstruction, "shown", lambda: {}), \
                    mock.patch.object(reconstruction, "manifests", lambda: man):
                out = reconstruction.restrict([p])
            kept = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(b["content_key"], b["accession"]) for b in kept],
                         [("first", "0000000001-26-000001"), ("read", "acc-A"), ("unread", "0000000001-26-000001")])
        self.assertEqual(out[p.name], {"kept": 3, "removed": 2, "manifest": 4, "missing_from_manifest": 1})

    def test_without_state_the_reference_decides(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "montages_blocks.jsonl"
            p.write_text("".join(json.dumps(b) + "\n" for b in (_block("read"), _block("unread"))), encoding="utf-8")
            with mock.patch.object(reconstruction, "keys", lambda: {"read"}), \
                    mock.patch.object(reconstruction, "shown", lambda: {}), \
                    mock.patch.object(reconstruction, "manifests", lambda: {}):
                out = reconstruction.restrict([p])
            kept = [json.loads(x)["content_key"] for x in p.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(kept, ["read"])
        self.assertEqual(out[p.name], {"kept": 1, "removed": 1})


# -- une commande (point 5) -------------------------------------------------------------------------------------------

class OneCommand(unittest.TestCase):
    def test_every_montage_has_its_steps_searches_before_corpora(self):
        specs = {"s1": {"source": None}, "c1": {"source": "corpus"}, "h1": {"source": "hits"}, "t1": {"source": "tagged"},
                 "l1": {"source": "lab_corpus"}, "b1": {"source": "backlog"}, "v1": {"source": "edge_values"},
                 "p1": {"source": "ppe_notes"}, "sp": {"source": "span"}}
        names = [n for n, _ in rebuild.montage_steps(specs)]
        self.assertEqual(names, ["mt_search_s1", "mt_fetch_s1", "mt_replay_h1", "mt_fetch_h1", "mt_corpus_c1",
                                 "mt_lab_corpus_l1", "mt_backlog_corpus_b1", "mt_values_corpus_v1", "mt_prepare"])

    def test_the_sources_of_the_configuration_are_all_known(self):
        known = set(rebuild.SEARCHED) | set(rebuild.CORPUS) | {"tagged", "span", "ppe_notes"}
        self.assertLessEqual({s.get("source") for s in config.load()["montages"].values()}, known)

    def test_order_of_the_whole(self):
        names = [n for n, _ in rebuild.steps("abc1234")]
        self.assertEqual(len(names), len(set(names)))
        pos = names.index
        self.assertEqual(names[0], "hand")
        self.assertEqual(names[-4:], ["restrict", "missing", "assemble", "compare"])
        # tronc avant les blocs ; files remises après leur recalcul et avant la préparation des blocs
        self.assertLess(pos("phase0"), pos("catalog"))
        self.assertLess(pos("disc_candidates"), pos("disc_queues"))
        self.assertLess(pos("disc_queues"), pos("disc_prepare"))
        self.assertLess(pos("nf_own"), pos("nf_queues"))
        self.assertLess(pos("nf_queues"), pos("nf_prepare"))
        # une archive s'efface après son dernier lecteur
        self.assertLess(pos("disc_fetch"), pos("nf_fetch"))
        self.assertEqual(pos("drop_notes"), pos("nf_fetch") + 1)
        self.assertEqual(pos("drop_nport"), pos("nport_bonds") + 1)
        self.assertLess(pos("nport_fetch"), pos("nport_bonds"))
        self.assertLess(pos("mt_prepare"), pos("restrict"))

    def test_a_failed_step_stops_and_resumes(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            calls = []

            def fake_run(cmd, **kw):
                calls.append(cmd[2].split(".", 1)[1] + (" " + " ".join(cmd[3:]) if cmd[3:] else ""))
                return mock.Mock(returncode=1 if calls[-1] == "universe" and calls.count("universe") == 1 else 0)
            few = [("hand", ["reconstruction", "hand"]), ("phase0", ["phase0"]), ("universe", ["universe"]),
                   ("index", ["phase0_index"])]
            with mock.patch.object(rebuild, "STATE", d / "rebuild.json"), mock.patch.object(rebuild, "LOGS", d / "logs"), \
                    mock.patch.object(rebuild, "steps", lambda ref, specs=None: few), \
                    mock.patch.object(rebuild.subprocess, "run", fake_run), mock.patch("builtins.print"):
                self.assertEqual(rebuild.run("abc1234", env={}), 1)
                self.assertEqual(calls, ["reconstruction hand", "phase0", "universe"])
                self.assertEqual(json.loads((d / "rebuild.json").read_text())["done"], ["hand", "phase0"])
                self.assertEqual(rebuild.run("abc1234", env={}), 0)                       # reprend à l'étape en échec
                self.assertEqual(calls[3:], ["universe", "phase0_index"])


if __name__ == "__main__":
    unittest.main()
