# Mode d'emploi exécutable (D-0072, point 3 d) : l'ordre d'une exécution, de la collecte au rendu.
# Les cibles marquées « réseau » interrogent la SEC : une seule à la fois, User-Agent requis (README).
# Les blocs extensifs (discovery, lender, nport, ownership, montages…) gardent leurs commandes dans la docstring de
# leur module et la décision qui les ouvre dans decisions.md.

# L'as_of est la clé as_of de config.yaml, seule source (D-0073) : aucune date ici. `make assemble AS_OF=AAAA-MM-JJ`
# ne fait que vérifier que la clé porte cette date.
PY ?= python3

.DEFAULT_GOAL := help
.PHONY: help phase0 phase1 phase2 read assemble assemble-cold render tables lint test check

help:  ## liste des cibles
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 16

phase0:  ## réseau : inventaire des dépôts, calendriers et fenêtres (db/phase0.json)
	$(PY) -m pipeline.phase0 $(AS_OF)

phase1:  ## réseau : companyfacts et instances XBRL des rapports périodiques
	$(PY) -m pipeline.phase1_run $(AS_OF)

phase2:  ## réseau : documents de la tranche texte
	$(PY) -m pipeline.phase2_fetch $(AS_OF)

read:  ## état de la lecture des blocs (puis show et submit, un bloc à la fois)
	$(PY) -m pipeline.reader status

assemble:  ## les huit tables, mémo repris (environ 14 minutes à froid)
	$(PY) -m pipeline.assemble $(AS_OF)

assemble-cold:  ## les huit tables, tout recalculé : mêmes tables à l'octet près
	$(PY) -m pipeline.assemble $(AS_OF) --sans-cache

render:  ## synthesis.md, series.md, delta.md et audit/
	$(PY) -m pipeline.render $(AS_OF)

tables: assemble render  ## assemblage puis rendus

lint:  ## ruff (règles F et E9, pyproject.toml)
	ruff check pipeline tests

test:  ## tests unitaires
	$(PY) -m unittest discover -s tests -t .

check: lint test  ## ruff puis les tests (le crochet .githooks/pre-commit lance cette cible)
