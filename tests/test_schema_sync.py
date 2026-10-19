"""schema.sql s'engendre depuis le registre (python -m pipeline.schema_gen) : une mesure ajoutée au registre
sans régénérer le schéma fait échouer l'insertion au réassemblage (D-0058, intégration).

Lancement : python3 -m unittest discover -s tests -t .
"""
import unittest

from pipeline import config, schema_gen


class SchemaSync(unittest.TestCase):
    def test_schema_sql_is_the_rendering_of_the_registry(self):
        self.assertEqual((config.ROOT / "schema.sql").read_text(encoding="utf-8"), schema_gen.render(),
                         "schema.sql n'est pas à jour : lancer python -m pipeline.schema_gen")


if __name__ == "__main__":
    unittest.main()
