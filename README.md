# Fragilité financière de la chaîne de l'IA, tirée des seuls dépôts SEC

Le dépôt mesure et date, sans noter ni prédire, la fragilité financière de 32 groupes de la chaîne de l'IA
et la circularité de leurs financements, à partir des seuls dépôts EDGAR. La spécification est `SPEC.md`,
le journal des décisions `decisions.md`, et la configuration (groupes, seuils, critères des annexes E et F)
`config.yaml`.

À lire en premier : `delta.md` (ce qui a changé depuis l'exécution précédente), puis `synthesis.md` (la
note) et `series.md` (les séries trimestrielles). Le dossier `audit/` est prêt pour l'audit indépendant de
l'annexe C : il contient les consignes et les nombres publiés reliés à leurs cellules.

## Ce qu'un clone contient

- `tables/` : les huit tables Parquet (faits, mesures, contrôles, observations, liens, entités, documents,
  exclusions).
- `work/observations/` : les lectures, un fichier par bloc lu. Elles ne se rejouent pas, d'où leur
  versionnement.
- `journal.jsonl` : chaque requête réseau, sans le User-Agent.
- Les rendus : `synthesis.md`, `series.md`, `delta.md` et `audit/`.

Ce qu'un clone ne contient pas, parce que `.gitignore` l'exclut : `db/` (inventaire, faits XBRL, mémo,
environ 2,4 Go), `cache/` (copies des dépôts) et `work/tmp/`. Sans `db/`, `assemble` ne démarre pas ; sans
`work/tmp/assemble_stats.json`, `render` non plus.

## Prérequis

- Python 3.13 et `pip install -r requirements.txt` : versions exactes, dépendances transitives comprises. La
  vérification des tables à l'octet près les suppose, DuckDB 1.5.6 d'abord. `pyproject.toml` décrit le projet
  pour `uv` (`uv lock`, puis `uv sync`), hors d'une exécution du pipeline puisque `uv lock` interroge PyPI.
- Un clone complet, sans `--depth 1` : le rendu compare les critères au commit d'origine `3ff3b98`, et
  `delta.md` aux tables du commit précédent.
- Pour toute phase réseau, un User-Agent déclaré à la SEC, dans `SEC_USER_AGENT` ou dans
  `secrets/user_agent.txt`. Ce fichier n'est pas versionné, et le dépôt est public : l'adresse de contact
  ne s'y écrit jamais. Règles réseau : 5 requêtes par seconde au plus, une seule commande réseau à la fois,
  et une pause d'au moins 10 minutes après un refus 403.
- Disque : environ 41 Go pour garder les archives des Notes Data Sets et des N-PORT. Par défaut, chaque
  archive est effacée après lecture (`discovery.fetch(keep_zip=False)`) ; pour la garder, appeler
  `discovery.fetch(keep_zip=True)` depuis Python.

## Sans `db/`, depuis un clone

- Lire les tables, avec DuckDB (`SELECT * FROM 'tables/measures.parquet'`) ou avec pandas.
- Lancer les contrôles : `make check` (ruff, puis les tests ; `make test` pour les seuls tests). Le crochet
  `.githooks/pre-commit` les lance avant chaque commit une fois activé : `git config core.hooksPath .githooks`.

## Ordre d'une exécution

`make help` liste ces étapes sous forme de cibles (`make phase0`, `make assemble`, `make render`…), les cibles
réseau signalées.

1. `python3 -m pipeline.phase0 2026-10-07` : inventaire des dépôts, calendriers et fenêtres
   (`db/phase0.json`).
2. `python3 -m pipeline.phase1_run 2026-10-07` : `companyfacts` et instances XBRL des rapports
   périodiques.
3. `python3 -m pipeline.phase2_fetch 2026-10-07` : documents de la tranche texte.
4. Lecture des blocs, un à un : `python3 -m pipeline.reader status`, puis `show` et `submit`. Chaque
   bloc extensif (`discovery`, `lender`, `nport`, `montages`, `sixk`, `sb_own`…) a ses commandes dans la
   docstring de son module, et la décision qui l'ouvre dans `decisions.md`.
5. `python3 -m pipeline.assemble 2026-10-07` : les huit tables, en 14 minutes environ sans mémo, 18 si la
   recherche des citations se refait aussi (après un changement de `textnorm.py` ou de `cache.py`). Profil :
   `python3 -m pipeline.profiling work/tmp/profil.txt pipeline.assemble 2026-10-07`.
6. `python3 -m pipeline.render 2026-10-07` : les rendus, en 30 secondes environ.

Les tables et les rendus ne dépendent pas de `PYTHONHASHSEED` : sous les graines 0 et 1, deux réassemblages
à froid donnent les huit tables à l'octet près, et les rendus aussi, à la durée mesurée près (D-0072). Deux
commandes qui écrivent les mêmes fichiers ne se lancent jamais en même temps : `assemble` et `render`, ou
deux `montages prepare`.
