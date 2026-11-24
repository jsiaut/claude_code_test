# Fragilité financière de la chaîne de l'IA, tirée des seuls dépôts SEC

Le dépôt mesure et date, sans noter ni prédire, la fragilité financière de 34 groupes de la chaîne de l'IA
et la circularité de leurs financements, à partir des seuls dépôts EDGAR. La spécification est `SPEC.md`,
le journal des décisions `decisions.md`, et la configuration (groupes, seuils, critères des annexes E et F)
`config.yaml`.

À lire en premier : `delta.md` (ce qui a changé depuis l'exécution précédente), puis `synthesis.md` (la
note) et `series.md` (les séries trimestrielles). Le dossier `audit/` est prêt pour l'audit indépendant de
l'annexe C : il contient les consignes et les nombres publiés reliés à leurs cellules.

Une session Claude Code lit d'abord `CLAUDE.md` (les invariants d'exploitation, en une page), puis `RUNBOOK.md`
(le mode d'emploi).

## Ce qu'un clone contient

- `tables/` : les huit tables Parquet (faits, mesures, contrôles, observations, liens, entités, documents,
  exclusions).
- `work/observations/` : les lectures, un fichier par bloc lu. Elles ne se rejouent pas, d'où leur
  versionnement.
- `journal.jsonl` : chaque requête réseau, sans le User-Agent.
- `state/` : ce qui dépend de l'historique d'exécution et ne se recalcule pas à l'identique (files de la
  découverte, manifestes des catalogues préparés, listes des montages), sans aucun texte de dépôt (D-0091 ;
  environ 12 Mo).
- Les rendus : `synthesis.md`, `series.md`, `delta.md` et `audit/`.

Ce qu'un clone ne contient pas, parce que `.gitignore` l'exclut : `db/` (inventaire, faits XBRL, mémo,
environ 2,4 Go), `cache/` (copies des dépôts) et `work/tmp/`. Sans `db/`, `assemble` ne démarre pas ; sans
`work/tmp/assemble_stats.json`, `render` non plus.

## Prérequis

- Python 3.13 et `pip install -r requirements.txt` : versions exactes, dépendances transitives et ruff compris.
  C'est la seule liste de versions (D-0087), et la vérification des tables à l'octet près les suppose, DuckDB 1.5.6
  d'abord. `pyproject.toml` ne porte que les réglages de ruff.
- L'historique des commits, pas forcément celui des fichiers : `git clone --filter=blob:none <url>` suffit (un
  `.git` d'environ 55 Mo, contre plus de 700 Mo pour un clone complet, D-0079), jamais `--depth 1`. Le rendu
  relit deux commits anciens : les critères du commit d'origine `3ff3b98` et, pour `delta.md`, les tables du
  commit précédent. Un clone partiel en tire les fichiers à la demande depuis `origin`, qui doit alors être
  joignable.
- Pour toute phase réseau, un User-Agent déclaré à la SEC, dans `SEC_USER_AGENT` ou dans
  `secrets/user_agent.txt`. Ce fichier n'est pas versionné, et le dépôt est public : l'adresse de contact
  ne s'y écrit jamais. Règles réseau : 2 requêtes par seconde au plus (D-0088 ; §9.5 en permet 5), une seule
  commande réseau à la fois, et une pause d'au moins 10 minutes après un refus, 403 ou 429.
- En session cloud, l'environnement `claude_code_test` installe ces prérequis à l'ouverture et porte le User-Agent
  (`RUNBOOK.md`, § 1).
- Disque : `db/` et `cache/` pèsent 5 Go. La reconstruction garde chaque archive des Notes Data Sets et des
  N-PORT jusqu'à son dernier lecteur, 19 Go au plus fort, si le disque a 30 Go libres ; sinon chaque lecteur
  retire la sienne (D-0091). Hors reconstruction, une archive s'efface dès sa lecture.

## Sans `db/`, depuis un clone

- Lire les tables, avec DuckDB (`SELECT * FROM 'tables/measures.parquet'`) ou avec pandas.
- Reconstruire `db/` et `cache/` : `make rebuild REF=<commit des tables>`, en une commande (D-0091 ; `RUNBOOK.md`,
  § 6). Tout se retire de la SEC : environ 27 000 requêtes, six heures, sans intervention sauf refus de la SEC.
- Lancer les contrôles : `make check` (ruff, puis les tests ; `make test` pour les seuls tests). Le crochet
  `.githooks/pre-commit` les lance avant chaque commit une fois activé : `git config core.hooksPath .githooks`.

## Ordre d'une exécution

L'as_of, date de connaissance de l'exécution, a une seule source : la clé `as_of` de `config.yaml`
(D-0073). Aucune commande ne la prend ailleurs, ni de la date du jour ; une date passée en argument doit
lui être égale. Les bornes de `config.yaml` qui finissent à l'as_of s'écrivent `as_of`.

`RUNBOOK.md` est le mode d'emploi complet (D-0087) : session neuve, mise à jour pas à pas, lecture et ses
gardes, blocs de §14 dans leur ordre, intégration, reconstruction d'un conteneur neuf. `make help` liste le
tronc sous forme de cibles, les cibles réseau signalées :

1. `make phase0` : inventaire des dépôts, calendriers et fenêtres (`db/phase0.json`) ; puis `make universe`
   (univers attendu) et `make index` (index et en-têtes SGML des dépôts de la tranche).
2. `make phase1` : `companyfacts` et instances XBRL des rapports périodiques.
3. `make phase2` : documents de la tranche texte ; puis `make catalog` (catalogues de la tranche et du bloc
   `text`).
4. Lecture des blocs, un à un : `python3 -m pipeline.reader open-pass`, puis `status`, `next` et `submit`,
   d'après les guides `work/guide_lecture_*.md`. Les blocs de §14 (`discovery`, `lender`, `nport`, `montages`,
   `sixk`, `sb_own`…) ont leurs commandes, dans l'ordre, au § 5 de `RUNBOOK.md`.
5. `make read-check`, puis `make assemble` : les huit tables, en 8 à 15 minutes selon ce que le mémo reprend
   (davantage si la recherche des citations se refait, après un changement de `textnorm.py` ou de `cache.py`).
   Profil : `python3 -m pipeline.profiling work/tmp/profil.txt pipeline.assemble`.
6. `make compare` : les tables contre celles du dernier commit, clé par clé ; chaque écart s'explique dans la
   décision. Puis `make render` : les rendus, en 30 secondes environ.

Mettre le modèle à jour : changer `as_of` dans `config.yaml` et ajouter l'ancien à `as_of_previous`, puis suivre
le § 3 de `RUNBOOK.md`. Une commande s'arrête si l'étape précédente porte un autre as_of : l'assemblage et la
phase 1 devant `db/phase0.json` (« relancer la phase 0 »), le rendu devant les tables (« relancer
l'assemblage »), le lecteur devant une passe ouverte (« ouvrir une passe nouvelle » : `reader open-pass`). Une
recherche plein texte ne se tire que sur la fenêtre nouvelle ; les catalogues préparés et les files gardent tels
quels les blocs et les unités de l'exécution précédente, et n'y ajoutent que ceux de la période nouvelle (D-0074).

Les tables et les rendus ne dépendent pas de `PYTHONHASHSEED` : sous les graines 0 et 1, deux réassemblages
à froid donnent les huit tables à l'octet près, et les rendus aussi, à la durée mesurée près (D-0072). Deux
commandes qui écrivent les mêmes fichiers ne se lancent jamais en même temps : `assemble` et `render`, ou
deux `montages prepare`.
