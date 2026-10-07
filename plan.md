# Plan du premier passage — exécution du 2026-10-07

Spec v6.14. `as_of` = 2026-10-07 (date UTC du début de l'exécution). Périmètre : `first_pass` (§11.1).
Critères des annexes E et F et seuils commités avant toute requête : commit `3ff3b98`
(2026-10-07 10:54:38 UTC), empreinte envoyée à l'utilisateur à 10:54:53 UTC.

## 1. Ce qui a été mesuré (phase 0)

### Groupes et CIK

Les onze tickers de `config.yaml` sont résolus par `company_tickers.json`. Chaque CIK concorde avec
l'indication de `config.yaml`. Les prédécesseurs sont rattachés à leur groupe (§10.1).

| Groupe | CIK | Clôture lue sur les 10-K | Fenêtre (début) | Fenêtre allongée | Période de lecture du texte |
| --- | --- | --- | --- | --- | --- |
| NVDA | 0001045810 | fin janvier (52/53 sem.) | 2020-01-27 | 2019-01-28 | 2017-01-30 |
| GOOGL | 0001652044 | 31 décembre | 2021-01-01 | 2020-01-01 | 2018-01-01 |
| AMZN | 0001018724 | 31 décembre | 2021-01-01 | 2020-01-01 | 2018-01-01 |
| META | 0001326801 | 31 décembre | 2021-01-01 | 2020-01-01 | 2018-01-01 |
| MSFT | 0000789019 | 30 juin | 2020-07-01 | 2019-07-01 | 2017-07-01 |
| ORCL | 0001341439 | 31 mai | 2020-06-01 | 2019-06-01 | 2017-06-01 |
| CRWV | 0001769628 | 31 décembre | 2021-01-01 | 2020-01-01 | 2018-01-01 |
| SPCX | 0001181412 | 31 décembre | 2021-01-01 | 2020-01-01 | 2018-01-01 |
| AMD | 0000002488 | dernier samedi de décembre | 2020-12-27 | 2019-12-29 | 2017-12-31 |
| AVGO | 0001730168 (+ 0001649338, 0001441634) | dimanche proche du 31 octobre | 2020-11-02 | 2019-11-04 | 2017-10-30 |
| MRVL | 0001835632 (+ 0001058057) | samedi proche du 31 janvier | 2020-02-02 | 2019-02-03 | 2017-01-29 |

- **Successions repérées dans la structure** : 8-K12B de Broadcom Inc. le 2018-04-04 et de Marvell Technology, Inc. le 2021-04-20, conformes à l'annexe D. La période de lecture de Broadcom commence avec son exercice clos en 2018, dont le premier 10-Q a été déposé par Broadcom Ltd.
- **CoreWeave porte `history_left_censored`** : son premier dépôt date du 2019-03-11, après le début de sa période de lecture (2018-01-01), et aucun prédécesseur n'apparaît (ni 8-K12B, ni ancienne dénomination autre qu'« Atlantic Crypto Corp »).
- **SpaceX** : 85 dépôts (83 dans l'annexe D au 24 septembre ; deux formulaires 4 et 4/A depuis). Un seul rapport périodique, le 10-Q au 30 juin 2026 ; les états annuels ne sont que dans le 424B4 (D1).
- Toutes les pages de `filings.files` ont été lues pour chaque CIK ; aucun CIK incomplet.

### Inventaire de la période de lecture

| Classe | Dépôts | Taille des soumissions complètes |
| --- | --- | --- |
| Rapports périodiques (10-K 77, 10-K/A 2, 10-Q 250) | 329 | 4,1 Go |
| 8-K portant 1.01, 1.02, 3.03 ou 8.01 | 420 | 0,59 Go |
| DEF 14A | 87 | 1,3 Go |
| Introductions en bourse (S-1, S-1/A, 424B4 de CoreWeave et SpaceX) | 8 | 0,89 Go |
| Autres formulaires de la période (Form 4, 144, SC 13G…) | 13 928 | 3,0 Go |

- Items des 420 8-K de la tranche : 1.01 dans 92, 1.02 dans 11, 3.03 dans 9, 8.01 dans 350.
- Pièces de ces 8-K, typées par l'en-tête SGML : **64 EX-10** (28 Mo de HTML) et **173 EX-4** (40 Mo). Les 70 EX-4 d'Alphabet sont surtout des formes d'obligations.
- Signaux de structure dans la période : aucun NT 10-K ni NT 10-Q. Deux 8-K portent l'item 3.01, Broadcom le 2018-04-04 et Marvell le 2021-04-20, tous deux au jour de la succession.
- Les tailles de §9.1 et de l'annexe D se comptent sur la soumission complète : les documents principaux de la tranche pèsent 0,86 Go (rapports périodiques, iXBRL), 15 Mo (8-K), 134 Mo (DEF 14A) et 61 Mo (introductions).

### Réseau

1 725 requêtes SEC en phase 0, toutes en 200 : latence médiane 73 ms, p90 207 ms, 57 Mo. Le client limite les départs à 5 par seconde. Le journal, horodaté à la fin de chaque requête, montre au plus 8 fins dans une seconde glissante, sous le plafond de 10. Il porte désormais aussi l'heure de départ (`ts_start`).

### Concepts

Tous les concepts de `concept_anchors` et `concept_anchors_to_verify` figurent dans `us-gaap-2026.xsd`, dont le bloc `SubstantialDoubtAboutGoingConcernTextBlock`. La taxonomie n'a pas de concept monétaire standard pour les baux non commencés, seulement des membres de dimension (décision D-0007).

## 2. Ce qui va être fait, dans l'ordre

1. **Phase 1, l'ossature** (en cours) :
   - `companyfacts` des 14 CIK sans borne de date : 14 requêtes, 36 Mo, 234 965 faits.
   - Archives `-xbrl.zip`, instances extraites, `MetaLinks.json` et `FilingSummary.xml` des 329 rapports périodiques : environ 1 000 requêtes.
   - Instances des autres dépôts sources d'un fait de `companyfacts` de ces périodes (8-K, S-1, S-4), pour les classer.
   - États annuels du 424B4 de SpaceX lus en HTML (D1, `is_tagged = false`).
   - Puis correspondance de concepts, les deux vues, contrôles C1 à C16 et mesures de rang 1 sans texte.
2. **Phase 2, la tranche à fort signal**, lue bloc par bloc, classe (1) puis classe (2), chacune du plus récent au plus ancien (D-0008) :
   - (1) Notes de parties liées des instances et des 424B4. Item 404 : 87 DEF 14A, 424B4 de CoreWeave et de SpaceX. Item 9A d'environ 79 rapports annuels. Item 4 de 250 10-Q. Blocs de continuité d'exploitation.
   - (2) Environ 462 sections d'items de 8-K, puis la première page des 237 pièces EX-10 et EX-4. Le corps n'est lu que selon la règle de §11.1 : une partie non financière, un amendement autonome, ou un « Supplemental Indenture » sous un item 3.03.
   - Requêtes : environ 750 (documents principaux des 8-K, DEF 14A, pièces). Les documents iXBRL des rapports périodiques sont déjà dans les archives.
3. **Phase 3** : assemblage, mesures, contrôles, annexes E et F, rendus, `audit/`, commit, seconde page.

## 3. Volumes et durée (hypothèses à remplacer par les mesures)

| Étape | Volume estimé | Base |
| --- | --- | --- |
| Blocs de la classe (1) | ≈ 500 blocs, ≈ 1,4 M caractères | 9A ≈ 3 k, Item 4 ≈ 1,5 k, Item 404 ≈ 6 k, notes ≈ 4 k caractères |
| Sections de 8-K | ≈ 460 blocs, ≈ 0,9 M caractères | ≈ 2 k caractères par section |
| Premières pages des pièces | 237 blocs, ≈ 1,2 M caractères | ≈ 5 k caractères |
| Corps des pièces retenus par la règle | 20 à 40 corps, 2 à 4 M caractères | amendements et contrats avec un client |
| **Total de lecture** | **≈ 1 200 blocs, 5 à 7,5 M caractères** | lus par lots d'un bloc, morceaux de 80 000 caractères au plus |
| Réseau restant | ≈ 1 750 requêtes, une dizaine de minutes | 5 requêtes par seconde |
| Durée de lecture | plusieurs heures (de l'ordre de 7 à 14 h) | ≈ 20 à 40 s par bloc, selon sa longueur |

**Écarts avec §9.1** :
- La fourchette « 1 100 à 1 650 10-K, 10-Q et 8-K » de la spec porte sur la fenêtre du premier passage. Ici : 329 rapports périodiques et 420 8-K de la tranche, sur une période de lecture plus longue (fenêtre allongée et huit trimestres).
- `companyfacts` : 36 Mo pour 14 CIK, contre 23,9 Mo pour les 8 groupes de l'annexe D.
- La lecture, pas le réseau, borne la durée du passage.
