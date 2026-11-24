# Mode d'emploi exécutable (D-0072, point 3 d) : le tronc d'une exécution, de la collecte au rendu, dans l'ordre.
# Les cibles marquées « réseau » interrogent la SEC : une seule à la fois, User-Agent requis (README).
# Les blocs de §14 (discovery, lender, nport, ownership, montages…) et la lecture sont dans RUNBOOK.md, avec leurs
# commandes dans l'ordre (D-0087).

# L'as_of est la clé as_of de config.yaml, seule source (D-0073) : aucune date ici. `make assemble AS_OF=AAAA-MM-JJ`
# ne fait que vérifier que la clé porte cette date.
PY ?= python3

.DEFAULT_GOAL := help
.PHONY: help phase0 universe index phase1 phase2 catalog read read-check assemble assemble-cold compare render tables \
	lint test check state rebuild

help:  ## liste des cibles
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 16

phase0:  ## réseau : inventaire des dépôts, calendriers et fenêtres (db/phase0.json)
	$(PY) -m pipeline.phase0 $(AS_OF)

universe:  ## univers attendu des cellules de rang 1 (db/expected_universe.parquet)
	$(PY) -m pipeline.universe $(AS_OF)

index:  ## réseau : index et en-têtes SGML des dépôts de la tranche (db/filing_index.json)
	$(PY) -m pipeline.phase0_index $(AS_OF)

phase1:  ## réseau : companyfacts et instances XBRL des rapports périodiques
	$(PY) -m pipeline.phase1_run $(AS_OF)

phase2:  ## réseau : documents de la tranche texte
	$(PY) -m pipeline.phase2_fetch $(AS_OF)

catalog:  ## catalogues de la tranche et du bloc text ; réseau pour les seuls 8-K 2.01 et 2.03 absents du cache
	$(PY) -m pipeline.catalog $(AS_OF)
	$(PY) -m pipeline.text_catalog $(AS_OF)

read:  ## état de la lecture des blocs (puis show et submit, un bloc à la fois)
	$(PY) -m pipeline.reader status

read-check:  ## gardes de lecture sur les lignes de l'as_of courant, avant le réassemblage (D-0087)
	$(PY) -m pipeline.reader check

assemble:  ## les huit tables, mémo repris (environ 14 minutes à froid)
	$(PY) -m pipeline.assemble $(AS_OF)

assemble-cold:  ## les huit tables, tout recalculé : mêmes tables à l'octet près
	$(PY) -m pipeline.assemble $(AS_OF) --sans-cache

compare:  ## tables/ contre celles d'un commit, clé par clé (REF=HEAD par défaut), entre assemble et render
	$(PY) -m pipeline.compare $(REF)

state:  ## state/ écrit depuis db/ après un assemblage : files, manifestes et listes, sans texte de dépôt (D-0091)
	$(PY) -m pipeline.state save

rebuild:  ## réseau : reconstruction d'un conteneur neuf en une commande, REF=<commit des tables> (RUNBOOK.md, § 6)
	$(PY) -m pipeline.rebuild $(REF)

render:  ## synthesis.md, series.md, delta.md et audit/
	$(PY) -m pipeline.render $(AS_OF)

tables: assemble render  ## assemblage puis rendus

lint:  ## ruff (règles F et E9, pyproject.toml ; version de requirements.txt)
	$(PY) -m ruff check pipeline tests

test:  ## tests unitaires
	$(PY) -m unittest discover -s tests -t .

check: lint test  ## ruff puis les tests (le crochet .githooks/pre-commit lance cette cible)
