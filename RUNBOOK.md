# Mode d'emploi de l'exploitation

Ce que fait l'exécutant, dans l'ordre, pour ouvrir une session, mettre le modèle à jour, lire, intégrer, et
reconstruire un conteneur neuf. `CLAUDE.md` porte les invariants ; `SPEC.md` et `decisions.md` l'emportent en cas
d'écart, et les règles d'une décision l'emportent sur cette page.

**État de cette page (D-0087, 2026-11-23).** Elle est tirée des décisions D-0074 à D-0086 et des docstrings des
modules, sans exécution possible ce jour-là (`db/` et `cache/` absents). La première mise à jour qui la suit
l'éprouve : un écart se corrige ici, et se consigne dans la décision en cours. Les commandes notées *(D-0087)* sont
nouvelles ; celles de la lecture et de la comparaison sont éprouvées, pas `catalog` ni `spacex_d1`.

## 1. Ouvrir une session

Une session neuve tourne sur un conteneur neuf : seul ce que Git suit s'y trouve.

- **Environnement.** Choisir l'environnement cloud `claude_code_test`. Son script de démarrage installe
  `requirements.txt`, complète le clone superficiel en clone partiel et active le crochet de commit ; sa variable
  `SEC_USER_AGENT` porte le User-Agent. Vérifier, et lancer à la main ce qui manque :

  ```
  python3 -c "import duckdb, pyarrow, zstandard; print('dépendances présentes')"   # sinon : pip install -r requirements.txt
  git rev-parse --is-shallow-repository    # false ; sinon : git fetch --unshallow --filter=blob:none origin
  git config --get core.hooksPath          # .githooks ; sinon : git config core.hooksPath .githooks
  python3 -c "from pipeline import config; config.user_agent(); print('User-Agent présent')"
  ```

  Le réseau de cet environnement se limite aux registres de paquets et aux six hôtes du journal (SEC et
  taxonomies) : un hôte de plus se demande à l'utilisateur.
  Le User-Agent ne s'affiche jamais et ne s'écrit jamais dans le dépôt. Sans variable, l'utilisateur le fournit et
  il va dans `secrets/user_agent.txt` (hors suivi, `chmod 600`). Une seule identité par exécution.
- **État hors Git.** `ls db cache` : s'ils manquent, rien ne s'assemble ni ne se rend, et toute mise à jour
  commence par la reconstruction (§ 6).
- **Où en est le travail.** `delta.md`, puis la dernière décision de `decisions.md` (`grep -n "^- \*\*D-" decisions.md | tail -3`).

## 2. Règles de toute exécution

- **Décision d'abord.** Origine, constat et règles s'écrivent dans `decisions.md` et se commitent avant tout
  tirage, toute lecture et tout changement de code ; les résultats s'y ajoutent ensuite. Une règle ajoutée en
  cours de route s'écrit avant son code ; un écart se consigne.
- **As_of.** Une seule source, la clé `as_of` de `config.yaml`. Un as_of qui tombe un samedi connaît les dépôts
  du vendredi.
- **Réseau.** Une seule commande réseau à la fois, 2 requêtes par seconde au plus (D-0088 ; plafond réglé dans
  `network` de `config.yaml`, opposable aux commandes qui règlent leur cadence), aucun changement d'identité. Chaque
  requête va à `journal.jsonl`.
  - Un refus de la SEC, 403 ou 429, met le client entier en pause dix minutes, puis la même adresse se redemande ;
    après trois pauses sans succès, la commande s'arrête (`AccessRefused`). Elle ne se relance pas à l'aveugle :
    regarder le journal (`status` 429, 403, `pause`, `refused`), attendre, consigner dans la décision.
  - Une commande arrêtée ou tuée se relance telle quelle : ce qui est au cache ne se retire pas.
  - Un document « non obtenu » après des erreurs de serveur répétées (502, 504) se voit au décompte de la
    commande (`non obtenus`, `not_collected`) : la relancer avant l'étape suivante, elle ne tire que le manquant
    (D-0088 : un relevé d'offre manquait, puis `sb_own fetch` s'arrêtait sur un en-tête non obtenu).
- **Volumes avant lecture.** Blocs et caractères à lire se consignent dans la décision avant la première lecture.
- **Lecture.** Par l'exécutant seul, un bloc à la fois ; jamais de sous-agent.
- **Deux écritures jamais ensemble.** `assemble` et `render`, ou deux `montages prepare`.
- **Commits.** `make check` avant chacun (le crochet le lance : ruff, les tests, et l'adresse de contact cherchée
  dans l'index). Ni pull request ni tâche planifiée sans demande.

## 3. Mettre le modèle à jour

Règles : D-0074 (point 3), D-0083 (points 3 et 5), D-0085 (point 3). Ordres de grandeur d'une semaine (D-0085) :
650 requêtes, 350 blocs et 2 millions de caractères à lire, 8 à 10 minutes par réassemblage.

1. **Décision et configuration**, commitées avant tout tirage :
   - `as_of` nouveau ; l'ancien s'ajoute à `as_of_previous` ; `search_overlap_from` ne change pas ;
   - les listes de lecture de l'exécution précédente se retirent (`git rm work/lists/*.txt`).
2. **Têtes non déposantes** (Nscale, CIK 2110365 ; Anthropic, CIK 2130357 ; `discovery.non_filer.own_filings`) :
   tirer leurs `submissions` et regarder les dépôts de la période nouvelle. Un amendement de S-1, un avis de prise
   d'effet, un 424B4 ou un rapport périodique demande une règle écrite avant toute lecture (D-0085, point 5).

   ```
   python3 -c "
   from pipeline import config, edgar, net
   E = edgar.Edgar(net.SecClient(config.as_of()), config.as_of())
   for cik in ('2110365', '2130357'):
       rows = E.submissions(cik)[1]
       print(cik, [(r['form'], r['filingDate']) for r in rows if r['filingDate'] > config.previous_as_of()])"
   ```
3. **Tronc**, dans cet ordre (`make help`) :

   | Commande | Réseau | Écrit |
   | --- | --- | --- |
   | `make phase0` | oui | `db/phase0.json`, inventaire, calendriers |
   | `make universe` | non | `db/expected_universe.parquet` |
   | `make index` | oui | `db/filing_index.json` (index et en-têtes SGML) |
   | `make phase1` | oui | `companyfacts`, instances XBRL, faits |
   | `make phase2` | oui | documents de la tranche texte |
   | `make catalog` *(D-0087)* | 8-K 2.01 et 2.03 absents du cache | `db/blocks.jsonl`, `db/text_blocks_ext.jsonl` |

   À consigner : dépôts nouveaux par classe, aucune clé déjà lue ne disparaît des catalogues.
4. **Lecture des groupes** (§ 4) : liste `upd_AAAAMMJJ_groups`, volume consigné, puis lecture.
5. **Blocs de §14**, dans l'ordre du § 5 ; chaque bloc consigne ses requêtes et ses volumes.
6. **Montages**, préparés après la lecture du texte des groupes (§ 5).
7. **Lecture de §14** : liste `upd_AAAAMMJJ_s14`, volume consigné, puis lecture.
8. **Contrôles avant le réassemblage** : `make read-check` *(D-0087)*. Une erreur se corrige par une passe de
   correction (§ 4) ; chaque alerte se vérifie dans le bloc, et ce qui reste se consigne.
9. **Entités par extrait** : un nom nouveau n'entre dans `config.yaml` (`confirmed_entities`, `entity_aliases`,
   `own_entities`) que sur un extrait cité mot pour mot (D-0021) ; sinon il reste en attente.
10. **Intégration** (§ 4, fin) : réassemblage, comparaison, rendus, résultats, commit, push.

## 4. Lire, puis intégrer

**Guides de lecture** : `work/guide_lecture_text.md` (format d'une ligne, orientation, montants, ce qu'on cherche
par type de bloc) et `work/guide_lecture_discovery.md` (déposants hors des groupes). À relire avant chaque lecture.

**Liste.** Une liste est un fichier de clés de contenu, une par ligne, dans l'ordre de lecture : les blocs sans
lecture tirés de dépôts de la période nouvelle, du plus récent au plus ancien. Point de départ :

```
python3 - <<'EOF'
from pipeline import config, reader
prev, a = config.previous_as_of(), config.as_of()
S14 = ("discovery_", "montage_text", "foreign_6k_text", "ownership_", "holdings_13f")
new = [b for b in reader.queue() if str(b.get("filing_date") or "")[:10] > prev]
(config.WORK / "lists").mkdir(exist_ok=True)
for name, keep in (("groups", lambda b: not b["block_kind"].startswith(S14)), ("s14", lambda b: b["block_kind"].startswith(S14))):
    bs = sorted((b for b in new if keep(b)), key=lambda b: str(b["filing_date"]), reverse=True)
    (config.WORK / "lists" / f"upd_{a.replace('-', '')}_{name}.txt").write_text("".join(b["content_key"] + "\n" for b in bs))
    print(name, len(bs), "blocs", sum(len(b["text"]) for b in bs), "caractères")
EOF
```

Le corps d'une pièce n'entre dans la file qu'après la lecture de son en-tête, et seulement si l'en-tête le
demande (§11.1) : il s'ajoute alors à la liste.

**Passe.** Elle s'ouvre une fois, avant la première soumission : `python3 -m pipeline.reader open-pass`
*(D-0087)*. Sans elle, chaque soumission prendrait l'heure du moment, et un bloc rendu en plusieurs morceaux ne
chargerait que le dernier.

**Un bloc.**

```
python3 -m pipeline.reader status --list work/lists/L.txt     # volume restant, à consigner avant de lire
python3 -m pipeline.reader next --list work/lists/L.txt       # le bloc, en morceaux s'il est long
python3 -m pipeline.reader submit CLE work/tmp/lines.jsonl --list work/lists/L.txt
```

- `lot` et `submit-lot` servent et rendent plusieurs petits blocs d'un coup ; après un refus, seuls les blocs
  refusés se soumettent de nouveau.
- Une erreur de schéma ou de sémantique se corrige une fois ; `--final` écrit ensuite les lignes valides et garde
  les autres comme rejets.
- Gardes *(D-0087)* : une ligne qui nomme une personne physique est refusée, même avec `--final` ; un montant qui
  ne se lit pas dans sa citation est une alerte, à corriger ou à confirmer par `--confirm` ; intérêts et
  commissions ne portent pas la famille `financing` ; une ligne déjà écrite dans la passe ne s'écrit pas deux fois.
- Une société prise pour une personne s'ajoute à `guards.ALLOWED`, avec une ligne dans la décision.

**Passe de correction** (aucune lecture nouvelle) : une liste `work/lists/repass_X.txt`, sa passe
(`python3 -m pipeline.reader open-pass --list work/lists/repass_X.txt --id AAAA-MM-JJTHH:MM:SSZ`), toutes les
lignes de chaque bloc soumises de nouveau, et l'identifiant inscrit dans `reading.correction_passes` de
`config.yaml` (D-0078). La passe la plus récente d'un bloc remplace l'ancienne au chargement.

**Intégrer.**

```
make read-check                 # gardes sur les lignes de l'as_of courant
make assemble                   # en arrière-plan, 8 à 15 minutes ; jamais en même temps que render
make compare                    # tables/ contre le dernier commit, clé par clé (REF=<commit> pour un autre)
make render                     # synthesis.md, series.md, delta.md, audit/
make check
```

Chaque écart de `make compare` *(D-0087)* s'explique dans la décision avant le rendu. Puis les résultats, le
commit et le push.

## 5. Blocs de §14, dans l'ordre de D-0074

Un seul processus réseau à la fois. Les colonnes disent ce qui se lance à chaque mise à jour ; le détail de
chaque étape est dans la docstring du module et dans la décision citée. Requêtes d'une semaine : D-0085, point 8.

| Bloc | Commandes, dans l'ordre | Décision | Requêtes |
| --- | --- | --- | --- |
| BDC, portefeuilles | `lender fetch`, `lender extract`, `lender num`, `lender_portfolio extract` | D-0028, D-0045 | 1 |
| BDC, passif | `lender_liabilities extract`, `inventory`, `fetch`, `exhibits`, `classify`, `announce`, puis relevés des offres (`show`, `check`), `check-announce`, `finalize` | D-0047 | 224 |
| Découverte | `discovery page`, `fetch`, `search`, `verify`, `candidates`, `prepare-frontier` ; `priority` puis `prepare-priority` pour les positions du 13F sans pièce | D-0036, D-0041, D-0086 | 79 |
| Non-déposants | `nf_discovery fetch`, `search`, `verify`, `candidates`, `prepare N`, `own`, `prepare_own` | D-0044, D-0054 | 77 |
| Form D | `formd` | D-0041 | 6 |
| Étrangers | `foreign`, puis `sixk fetch`, `sixk prepare` | D-0042, D-0048 | 17 |
| SoftBank | `sb_own inventory`, `headers`, `fetch`, `prepare` | D-0058 | 41 |
| N-PORT | `nport page`, `fetch`, `unlisted-fetch`, `unlisted-submissions`, `bonds-fetch` ; volumes par `volume`, `unlisted-volume`, `credit-volume`, `bonds-volume` | D-0058, D-0065, D-0066, D-0071 | 1 |
| Participations | `ownership plan`, `ownership fetch`, `ownership volume` | D-0071 | 7 |
| Montages | par montage, selon sa source dans `config.yaml` (ci-dessous), puis `montages prepare` | D-0046 et suivantes | 45 |

Chaque commande se lance par `python3 -m pipeline.<module> <sous-commande>`.

Unités prioritaires de la découverte (D-0086) : leur nombre (`discovery priority`) se consigne avant toute
préparation ; elles se préparent (`prepare-priority`, une requête par page R ou par pièce) et se lisent avant les
autres.

Montages, un par un dans l'ordre de `montages` de `config.yaml`, chacun selon sa source : `search` → `montages
search <id>` puis `montages fetch <id>` ; `hits` → `montages replay <id>` puis `fetch` ; `corpus` → `montages corpus
<id>` ; `lab_corpus` → `montages lab_corpus <id>` ; `backlog` → `montages backlog_corpus <id>` ; `edge_values` →
`montages values_corpus <id>` ; `tagged` → `labs inventory` ; `span` et `ppe_notes` → rien avant la préparation.
`montages prepare` écrit ensuite les fenêtres de tous les montages. L'ordre compte : un corpus lit ce qui est au
cache, pièces des recherches déjà tirées comprises (D-0088, point 10).

Ce qui ne se recalcule pas d'une exécution à l'autre (D-0074, point 3) : les catalogues préparés (montages, 6-K,
SoftBank), les files (découverte, non-déposants) et les résultats gardés des recherches plein texte gardent leurs
blocs et leurs unités ; seuls s'y ajoutent ceux de la période nouvelle. Le lexique des non-cotés de N-PORT reste
celui du dernier scan (`frozen_lexicon`).

## 6. Reconstruire un conteneur neuf

Sans `db/` ni `cache/`, tout se retire de la SEC avant la mise à jour. Mesure de D-0084, au journal : 6 h 15,
26 794 requêtes, 98 Go, dont 88 Go d'archives des jeux de données tirées plusieurs fois. **Relire D-0084
(points 3, 6 et 7) avant de s'y lancer** ; en résumé :

- la configuration reste celle du dernier commit des tables (son as_of), et
  `export PIPELINE_RECONSTRUCTION=<ce commit>` active le mode : les catalogues et les files se recalculent sur
  toute la période, puis se ramènent aux clés que ce commit charge ;
- le tronc (§ 3, étape 3), puis `python3 -m pipeline.spacex_d1` *(D-0087)* pour la série annuelle de SpaceX ;
- les blocs de §14 (§ 5), avec `discovery prepare-history` et `nf_discovery prepare_history` à la place des
  préparations ordinaires, sans oublier `lender num` ;
- deux fichiers de `db/` que nul programme n'écrit se reconstituent à la main (D-0084, point 7) :
  `exhibits_tranche.json` (types SGML des pièces, depuis la table `documents`) et `usgaap2026_balance.json`
  (soldes des concepts de `us-gaap-2026.xsd`) ;
- `python3 -m pipeline.reconstruction restrict`, puis `missing` : une clé lue qui ne revient pas est un échec
  consigné, jamais une relecture. Entre plusieurs blocs de même clé (même texte dans deux dépôts, même fenêtre
  dans deux montages), `restrict` garde celui que les tables de la référence montrent (D-0088, point 10) ;
- aucune lecture ; réassemblage, puis `make compare REF=<ce commit>` : chaque écart s'explique dans la décision.
  Les tables de la reconstruction ne se commitent pas ;
- la variable se retire, et la mise à jour (§ 3) part de cet état.

Trois chantiers allégeraient cette étape et attendent la prochaine mise à jour (D-0087, point 1) : versionner
l'état que `db/` porte seul, tirer chaque archive une seule fois, enchaîner la reconstruction en une commande.
