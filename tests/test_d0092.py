"""D-0092 : un texte repris dans plusieurs dépôts se rattache au premier.

Lancement : python3 -m unittest tests.test_d0092 -v
"""
import pathlib
import re
import unittest
from unittest import mock

import pandas as pd

from pipeline import config, reader, reconstruction

TABLES = config.ROOT / "tables"


def blk(key, accession, date, acceptance=None, **more):
    return {"content_key": key, "accession": accession, "knowledge_date": date, "filing_date": date,
            "acceptance": acceptance, "block_kind": "item_8k_203", "signal_class": 3, "sort_key": accession,
            "text": "The information set forth in Item 1.01 is incorporated by reference.", **more}


class FirstFiling(unittest.TestCase):
    def test_the_first_filing_wins_whatever_the_order(self):
        early, late = blk("k", "0001-25-000001", "2025-11-03"), blk("k", "0001-26-000009", "2026-11-02")
        for catalog in ([early, late], [late, early]):                    # l'ordre des lignes ne décide plus
            self.assertIs(reader.by_key(catalog)["k"], early)
        mid = blk("k", "0001-26-000002", "2026-03-01")
        self.assertIs(reader.by_key([mid, late, early])["k"], early)
        self.assertIs(reader.by_key([blk("solo", "0001-26-000003", "2026-01-01")])["solo"]["accession"], "0001-26-000003")

    def test_same_day_the_earlier_acceptance_then_the_accession(self):
        a = blk("k", "0001-21-000007", "2021-09-08", "2021-09-08 20:47:42")
        b = blk("k", "0001-21-000008", "2021-09-08", "2021-09-08 09:15:00")
        self.assertIs(reader.by_key([a, b])["k"], b)                       # même jour : la première acceptation
        self.assertIs(reader.by_key([b, a])["k"], b)
        unknown = blk("k", "0001-21-000001", "2021-09-08")
        self.assertIs(reader.by_key([unknown, a])["k"], a)                 # une acceptation inconnue vient après
        c, d = blk("k", "0001-21-000005", "2021-09-08"), blk("k", "0001-21-000004", "2021-09-08")
        self.assertIs(reader.by_key([c, d])["k"], d)                       # à égalité, le plus petit numéro d'accession
        undated = blk("k", "0001-20-000001", None)
        self.assertIs(reader.by_key([undated, a])["k"], a)                 # un bloc sans date ne passe pas devant

    def test_within_one_filing_the_last_block_stays(self):
        # un même bloc servi par deux catalogues : le dernier, comme avant, même si lui seul ignore l'acceptation
        groups = blk("k", "0001-23-000001", "2023-05-01", "2023-05-01 16:30:00", block_kind="exhibit_header")
        montage = blk("k", "0001-23-000001", "2023-05-01", None, block_kind="montage_text")
        self.assertIs(reader.by_key([groups, montage])["k"], montage)
        self.assertIs(reader.by_key([montage, groups])["k"], groups)
        # plusieurs dépôts dont le premier est servi deux fois : son dernier bloc
        late = blk("k", "0001-24-000001", "2024-05-01", "2024-05-01 16:30:00")
        self.assertIs(reader.by_key([groups, late, montage])["k"], montage)
        self.assertIs(reader.by_key([late, montage, groups])["k"], groups)

    def test_the_queue_serves_the_block_the_loader_will_keep(self):
        late = blk("k", "0001-26-000009", "2026-11-02", sort_key="1")       # premier dans l'ordre du signal
        solo = blk("solo", "0001-26-000004", "2026-06-01", sort_key="5")
        early = blk("k", "0001-25-000001", "2025-11-03", sort_key="9")
        with mock.patch.object(reader, "obs_path", lambda ck: pathlib.Path("/nulle/part") / ck), \
                mock.patch.object(reader, "LIST", None):
            q = reader.queue([late, solo, early])
        self.assertEqual([(b["content_key"], b["accession"]) for b in q],
                         [("k", "0001-25-000001"), ("solo", "0001-26-000004")])

    def test_the_rebuild_falls_back_on_the_same_choice(self):
        # reconstruction sans manifeste : la référence ne montre aucun des dépôts recalculés ; se garde le bloc que
        # le chargement retiendrait, quel que soit l'ordre des lignes
        import json
        import tempfile
        early, late = blk("k", "0001-25-000001", "2025-11-03"), blk("k", "0001-26-000009", "2026-11-02")
        shown = blk("s", "0001-26-000002", "2026-02-01", document="a.htm")
        other = blk("s", "0001-25-000002", "2025-02-01", document="a.htm")       # plus ancien, mais la référence montre l'autre
        for order in ([early, late, other, shown], [shown, other, late, early]):
            with tempfile.TemporaryDirectory() as d:
                p = pathlib.Path(d) / "foreign_6k_blocks.jsonl"
                p.write_text("".join(json.dumps(b) + "\n" for b in order), encoding="utf-8")
                ref = {"s": ("item_8k_203", "0001-26-000002", "a.htm", None), "k": ("item_8k_203", "ailleurs", "x.htm", None)}
                with mock.patch.object(reconstruction, "keys", lambda: {"k", "s"}), \
                        mock.patch.object(reconstruction, "shown", lambda: ref), \
                        mock.patch.object(reconstruction, "manifests", lambda: {}):
                    reconstruction.restrict([p])
                kept = {b["content_key"]: b["accession"] for b in map(json.loads, p.read_text(encoding="utf-8").splitlines())}
            self.assertEqual(kept, {"k": "0001-25-000001", "s": "0001-26-000002"})

    def test_one_function_everywhere(self):
        # aucun module ne se refait un dictionnaire clé -> bloc à partir d'un catalogue : `reader.by_key` seul choisit
        own = re.compile(r'\{b\["content_key"\]: b for b in (?!rows\b)')
        for p in sorted((config.ROOT / "pipeline").glob("*.py")):
            self.assertIsNone(own.search(p.read_text(encoding="utf-8")), p.name)
        for name, n in (("load.py", 1), ("montages.py", 1), ("render.py", 1), ("reader.py", 4)):
            src = (config.ROOT / "pipeline" / name).read_text(encoding="utf-8")
            self.assertGreaterEqual(len(re.findall(r"\bby_key\(", src)), n, name)


class LoadedTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obs = pd.read_parquet(TABLES / "observations.parquet",
                                  columns=["content_key", "accession", "form", "knowledge_date", "kind", "abstention_reason"])

    def _of(self, key):
        rows = self.obs[self.obs["content_key"] == key]
        self.assertEqual(len(rows), 1, key)
        r = rows.iloc[0]
        return r["accession"], r["form"], str(r["knowledge_date"])[:10]

    def test_the_cipher_exhibit_dates_from_the_8k_not_its_amendment(self):
        # la pièce figure dans le 8-K du 8 septembre 2021 et dans son 8-K/A du lendemain (D-0083, D-0085, D-0091)
        for key in ("06e115321aefb8d966f7b30bcf1069b80c8a16a19a4f9b55054ff84d982df096",
                    "bb770ba533b46df33e76363907ff431311971377654af54ee1386c5188cfba04"):
            self.assertEqual(self._of(key), ("0001193125-21-267907", "8-K", "2021-09-08"))

    def test_a_repeated_8k_item_dates_from_its_first_filing(self):
        # item 2.03 de Blackstone, mêmes mots dans dix 8-K de 2019 à 2026 ; de Dell, de 2019 à 2026
        self.assertEqual(self._of("c604acad8c7b0ee2bbd794e46abc67e9d3f1748fdeef9ed50278efec79a7e557"),
                         ("0001193125-19-242057", "8-K", "2019-09-10"))
        self.assertEqual(self._of("ae2d9ee517e0c037ab850fc93327514870c549fcdca5b0f8354ccfa67dff793e")[2], "2019-03-21")

    @unittest.skipUnless(reader.CATALOG.exists(), "db/ absent : conteneur neuf")
    def test_every_text_shared_by_several_filings_goes_to_the_first(self):
        cat = reader.load_catalog()
        filings = {}
        for b in cat:
            filings.setdefault(b["content_key"], set()).add(b["accession"])
        shown = dict(zip(self.obs["content_key"], self.obs["accession"]))
        chosen = reader.by_key(cat)
        several = [k for k, accs in filings.items() if len(accs) > 1 and k in shown]
        self.assertGreater(len(several), 50)
        for k in several:
            first = min((b for b in cat if b["content_key"] == k), key=reader.first_filed)
            self.assertEqual(chosen[k]["accession"], first["accession"], k)
            self.assertEqual(shown[k], first["accession"], k)

    @unittest.skipUnless(reader.CATALOG.exists(), "db/ absent : conteneur neuf")
    def test_the_order_of_filings_no_longer_matters(self):
        # l'ordre des dépôts dans les catalogues suit l'inventaire, qui change d'une exécution à l'autre (D-0085,
        # point 15) : le choix n'en dépend plus. L'ordre des blocs d'un même dépôt, lui, reste (tri stable).
        cat = reader.load_catalog()

        def choice(catalog):
            return {k: (b["accession"], b.get("document"), b["block_kind"]) for k, b in reader.by_key(catalog).items()}
        base = choice(cat)
        for reverse in (False, True):
            self.assertEqual(choice(sorted(cat, key=lambda b: str(b["accession"]), reverse=reverse)), base)

    @unittest.skipUnless(reader.CATALOG.exists(), "db/ absent : conteneur neuf")
    def test_a_text_shared_by_several_groups_carries_no_oriented_line(self):
        # une ligne orientée (contrepartie, payeur, receveur) se lit du point de vue d'un déposant et ne vaut pas pour un
        # autre groupe. Aujourd'hui une seule clé réunit des dépôts de plusieurs groupes, et porte une abstention. Si ce
        # test échoue : relire le bloc dans une passe de correction ; la file le sert par son premier dépôt (D-0092).
        groups = {}
        for b in reader.load_catalog():
            groups.setdefault(b["content_key"], set()).add((b["accession"], b["group_id"]))
        shared = {k for k, v in groups.items() if len({a for a, _ in v}) > 1 and len({g for _, g in v}) > 1}
        rows = self.obs[self.obs["content_key"].isin(shared)]
        self.assertEqual(sorted(set(rows["kind"])), ["abstention"] if len(rows) else [])


if __name__ == "__main__":
    unittest.main()
