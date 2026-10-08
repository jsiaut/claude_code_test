# Note de synthèse — fragilité financière de la chaîne IA

*Exécution du 2026-10-07 · spec v6.14 · périmètre : premier passage, blocs `lender`, `text` de §14 · rendu généré depuis les tables `measures`, `controls` et `exclusions`, jamais édité à la main.*

## En tête

- **Critères des annexes E et F et seuils : inchangés** depuis leur commit d'origine `3ff3b988a48a5c904f88f006d263bfa780739d39` (2026-10-07 10:54:38), antérieur à la première requête. `config.yaml` a changé depuis (dernier commit qui le touche : `b6364a7771f7e68270c704dbf6b72fe10dec499f`, plus les changements de cette exécution) sans toucher ces critères : `concept_anchors` (second candidat de capex, D-0012); `confirmed_entities` (entités confirmées par extrait, D-0021); `entity_aliases` (alias confirmés par extrait, D-0021); `own_entities` (entités propres confirmées par extrait, D-0021); `reading` (voir decisions.md); `scope` (voir decisions.md); `scope_decision` (voir decisions.md).
- **Périmètre couvert : premier passage et blocs `lender`, `text` de §14**, ouverts par l'utilisateur le 2026-10-07 après le rendement présenté dans la seconde page. Premier passage : faits balisés des onze groupes, notes de parties liées, Item 404, Item 9A, Item 4 des 10-Q, continuité d'exploitation, items 1.01, 1.02, 3.03 et 8.01 des 8-K avec leurs pièces EX-10 et EX-4. Bloc `lender` : portefeuilles publiés des BDC (BDC Data Sets). Bloc `text` : notes d'investissements, de dette, de baux et d'engagements, texte autour des faits de concentration, items 2.01 et 2.03 des 8-K, corps des EX-10 arrêtés à leur en-tête (les EX-4 arrêtés à leur en-tête restent exclus, §14 ne les rouvrant pas) ; tout le catalogue du bloc est lu, aucun bloc ne reste « non traité ». Les blocs `discovery`, `form_d`, `paths` et `foreign` restent fermés.
- **Résultat principal (E.7) : les pièces déposées ne permettent pas de discriminer entre les deux lectures.** 83 % des issues de E.1 et E.2 au point de tête (10 %) sont indéterminées, sur 18 issues ; motifs : recherche incomplète : 7, intervalle à cheval sur le seuil : 4, précondition non remplie : 4. La découverte (§14) n'étant pas ouverte, la recherche reste incomplète au sens de E.0 : une non-discrimination tient encore en partie au périmètre de lecture.
- **Contrôles comptables, vue `as_known`** : `mismatch` 603, `not_testable` 506, `ok` 13 615, `tautological` 613 (un contrôle `tautological` n'est jamais compté comme réussi ; un `mismatch` est un résultat publié, avec son code d'explication, dans `controls`).
- **Contrôles comptables, vue `revised`** : `mismatch` 775, `not_testable` 720, `ok` 13 425, `tautological` 613.
  Par contrôle (`mismatch` sur total, vue `as_known`) : C10 78/445, C11 48/462, C12 206/1 153, C13 0/199, C14 9/499, C15 61/273, C16 0/192, C1 79/6 754, C2 29/3 868, C3 54/261, C5 0/35, C6 0/613, C7 1/212, C8 38/78, C9 0/293.
- **Exclusions principales** : `conflicting` 377, `pending_entity` 223, `financial_parties_only` 165, `invalid_aggregate` 8, `submitted_draft` 8, `parse_failed` 3, `not_public` 2, `history_left_censored` 1.
- **Arrêt** : aucun ; ni refus durable de la SEC, ni échec général des contrôles.

## Événements (annexe F)

Chaque événement est un observable daté, avec sa pièce ; aucune somme, aucun score. Un trimestre dont la source n'a pas été lue n'est jamais présenté comme un trimestre sans événement.

**NVIDIA**

- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-11-18, rattaché au trimestre clos le 2022-10-30 ; pièce : faits balisés.
- F7 (baisse d'une durée d'amortissement publiée) — rendu public le 2025-02-26, rattaché au trimestre clos le 2025-01-26 ; pièce : durées publiées (faits balisés de deux 10-K successifs).

**Alphabet**

- F2 (flux après financement des contreparties négatif) — rendu public le 2026-07-23, rattaché au trimestre clos le 2026-06-30 ; pièce : faits balisés.

**Amazon**

- F2 (flux après financement des contreparties négatif) — rendu public le 2021-04-30, rattaché au trimestre clos le 2021-03-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2021-07-30, rattaché au trimestre clos le 2021-06-30 ; pièce : 10-Q 0001018724-21-000020.
- F2 (flux après financement des contreparties négatif) — rendu public le 2021-07-30, rattaché au trimestre clos le 2021-06-30 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2021-10-29, rattaché au trimestre clos le 2021-09-30 ; pièce : 10-Q 0001018724-21-000028.
- F2 (flux après financement des contreparties négatif) — rendu public le 2021-10-29, rattaché au trimestre clos le 2021-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-04-29, rattaché au trimestre clos le 2022-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-07-29, rattaché au trimestre clos le 2022-06-30 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2022-10-28, rattaché au trimestre clos le 2022-09-30 ; pièce : 10-Q 0001018724-22-000023.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-10-28, rattaché au trimestre clos le 2022-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-04-28, rattaché au trimestre clos le 2023-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-05-02, rattaché au trimestre clos le 2025-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-04-30, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-07-31, rattaché au trimestre clos le 2026-06-30 ; pièce : 10-Q 0001018724-26-000026.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-07-31, rattaché au trimestre clos le 2026-06-30 ; pièce : faits balisés.

**Meta**

- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-07-28, rattaché au trimestre clos le 2022-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-07-31, rattaché au trimestre clos le 2025-06-30 ; pièce : faits balisés.

**Microsoft**

- F7 (baisse d'une durée d'amortissement publiée) — rendu public le 2025-07-30, rattaché au trimestre clos le 2025-06-30 ; pièce : durées publiées (faits balisés de deux 10-K successifs).

**Oracle**

- F2 (flux après financement des contreparties négatif) — rendu public le 2021-12-10, rattaché au trimestre clos le 2021-11-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-12-13, rattaché au trimestre clos le 2022-11-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-12-12, rattaché au trimestre clos le 2023-11-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-12-10, rattaché au trimestre clos le 2024-11-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-09-26, rattaché au trimestre clos le 2025-05-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-09-10, rattaché au trimestre clos le 2025-08-31 ; pièce : 10-Q 0001193125-25-200095.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-09-10, rattaché au trimestre clos le 2025-08-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-12-11, rattaché au trimestre clos le 2025-11-30 ; pièce : 10-Q 0001193125-25-200095, 10-Q 0001193125-25-315925.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-12-11, rattaché au trimestre clos le 2025-11-30 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-03-11, rattaché au trimestre clos le 2026-02-28 ; pièce : 10-Q 0001193125-26-101045, 10-Q 0001193125-25-315925.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-03-11, rattaché au trimestre clos le 2026-02-28 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-06-22, rattaché au trimestre clos le 2026-05-31 ; pièce : 10-K 0001193125-26-277521, 10-Q 0001193125-26-101045.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-06-22, rattaché au trimestre clos le 2026-05-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-09-11, rattaché au trimestre clos le 2026-08-31 ; pièce : 10-Q 0001193125-26-389274.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-09-11, rattaché au trimestre clos le 2026-08-31 ; pièce : faits balisés.

**CoreWeave**

- F2 (flux après financement des contreparties négatif) — rendu public le 2025-08-13, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-11-13, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-03-02, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-Q 0001769628-25-000062, 10-K 0001769628-26-000104.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-03-02, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-10-02, rattaché au trimestre clos le 2024-12-31 ; pièce : 8-K 0001193125-25-227562.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-05-15, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q 0001769628-25-000014.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-05-15, rattaché au trimestre clos le 2025-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-05-15, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q 0001769628-25-000014.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-08-13, rattaché au trimestre clos le 2025-06-30 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-05-15, rattaché au trimestre clos le 2025-06-30 ; pièce : 10-Q 0001769628-25-000014.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-08-13, rattaché au trimestre clos le 2025-06-30 ; pièce : 10-Q 0001769628-25-000041.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-11-13, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-08-13, rattaché au trimestre clos le 2025-09-30 ; pièce : 8-K 0001193125-25-227562, 10-Q 0001769628-25-000041.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-11-13, rattaché au trimestre clos le 2025-09-30 ; pièce : 10-Q 0001769628-25-000062.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-K 0001769628-26-000104, 10-Q 0001769628-25-000062.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-11-13, rattaché au trimestre clos le 2025-12-31 ; pièce : 8-K 0001769628-26-000003, 10-Q 0001769628-25-000062.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-K 0001769628-26-000104.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-Q 0001769628-26-000222.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2026-03-02, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-K 0001769628-26-000104.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-Q 0001769628-26-000222.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-08-12, rattaché au trimestre clos le 2026-06-30 ; pièce : 10-Q 0001769628-26-000222, 10-Q 0001769628-26-000366.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-08-12, rattaché au trimestre clos le 2026-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-08-12, rattaché au trimestre clos le 2026-06-30 ; pièce : 10-Q 0001769628-26-000366.

**SpaceX**

- F4 (amendement ou dérogation de clause financière) — rendu public le 2026-08-04, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-Q 0001628280-26-052535.

**AMD**

- F8 (croissance annuelle passée sous zéro) — rendu public le 2023-05-03, rattaché au trimestre clos le 2023-04-01 ; pièce : faits balisés.
- F6 (dépréciation d'investissement) — rendu public le 2026-02-04, rattaché au trimestre clos le 2025-12-27 ; pièce : 10-K 0000002488-26-000018.

**Marvell**

- F4 (amendement ou dérogation de clause financière) — rendu public le 2020-12-08, rattaché au trimestre clos le 2021-01-30 ; pièce : 8-K 0001193125-20-312706.
- F2 (flux après financement des contreparties négatif) — rendu public le 2021-06-09, rattaché au trimestre clos le 2021-05-01 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2021-04-21, rattaché au trimestre clos le 2021-05-01 ; pièce : 8-K 0001193125-21-123305.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2023-04-17, rattaché au trimestre clos le 2023-04-29 ; pièce : 10-Q 0001835632-23-000046, 10-K 0001835632-25-000057, 10-Q 0001835632-24-000200, 10-Q 0001835632-23-000029, 10-Q 0001835632-24-000142, 10-K 0001835632-24-000009, 8-K 0001193125-23-103639, 10-Q 0001835632-23-000038, 10-Q 0001835632-24-000063.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2023-05-26, rattaché au trimestre clos le 2023-04-29 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-05-31, rattaché au trimestre clos le 2024-05-04 ; pièce : faits balisés.

États de couverture des cellules de l'annexe F (groupe × trimestre), pour lire ce qui n'a pas été observé :

- F1 : calculée / événement 14 ; calculée / sans événement 177 ; indéterminée 65
- F2 : calculée / événement 32 ; calculée / sans événement 181 ; indéterminée 43
- F3 : calculée / sans événement 219 ; partielle / sans événement 37
- F4 : calculée / événement 9 ; calculée / sans événement 194 ; partielle / sans événement 53
- F5 : calculée / événement 6 ; calculée / sans événement 197 ; indéterminée 53
- F6 : calculée / événement 1 ; indéterminée 255
- F7 : calculée / événement 2 ; calculée / sans événement 44 ; indéterminée 210
- F8 : calculée / événement 5 ; calculée / sans événement 203 ; indéterminée 48
- F9 : calculée / sans événement 256
- F10 : calculée / sans événement 219 ; indéterminée 37

## Fragilité, par groupe

Mesures de rang 1 en vue `as_known` (ce que l'on savait à la publication de chaque période) ; la série complète est dans `series.md`. « n.d. » donne le motif ; jamais un zéro.

### NVIDIA (NVDA)

Dernière information balisée utilisée : 2026-08-26.

| Mesure (trimestre clos le) | 2025-10-26 | 2026-01-25 | 2026-04-26 | 2026-07-26 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 62,5 % | 73,2 % | 85,2 % | 105,9 % |
| Croissance du revenu (douze mois glissants) | 65,2 % | 65,5 % | 70,7 % | 83,4 % |
| Capex décaissé ÷ CFO | 0,07 x | 0,04 x | 0,03 x | 0,11 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 22 115 M$ | 34 904 M$ | 48 587 M$ | 21 400 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 22 115 M$ | 32 904 M$ | 48 587 M$ | 21 400 M$ |
| Délai de recouvrement (créances) | 53 j | 51 j | 45 j | 60 j |
| Obligations de prestation restantes (RPO) | 2 500 M$ | 2 300 M$ | 2 600 M$ | 3 200 M$ |
| Dette ÷ (résultat opérationnel + dotations) | 0,08 x | 0,06 x | 0,05 x | 0,17 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,02 x | 0,02 x | 0,03 x | 0,03 x |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 73,4 % | 75,0 % | 74,9 % | 75,0 % |
| Marge opérationnelle | 63,2 % | 65,0 % | 65,6 % | 66,2 % |
| Capex décaissé ÷ revenu | 0,03 x | 0,02 x | 0,02 x | 0,03 x |
| Flux disponible après rémunération en actions | 20 461 M$ | 33 271 M$ | 46 659 M$ | 19 374 M$ |
| Rémunération en actions ÷ CFO | 0,07 x | 0,05 x | 0,04 x | 0,08 x |
| Écart CFO − résultat net | -8 159 M$ | -6 772 M$ | -7 977 M$ | -35 611 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 445,84 x | 503,42 x | 544,58 x | 426,74 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 43 303 M$ | 48 678 M$ | 51 696 M$ | 74 959 M$ |
| Capitaux propres | 118 897 M$ | 157 293 M$ | 195 474 M$ | 228 984 M$ |
| Résultats non distribués (déficit si négatif) | 107 908 M$ | 146 973 M$ | 185 038 M$ | 219 157 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -1,2 % | n.d. (dénominateur négatif ou nul) | -0,9 % | -1,0 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2025-01-26 | 2026-01-25 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | 816 M$ | 2 369 M$ |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-01-25 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié 22 700 M$.
Baux non commencés au 2026-01-25 (pont ouverture + nouveaux − commencés = clôture) : ouverture 7 600 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 22 700 M$.

Durées d'amortissement publiées (exercice clos le 2026-01-25) : Equipment, Compute Hardware, And Software (borne basse) 2,0 ans ; Equipment, Compute Hardware, And Software (borne haute) 7,0 ans ; Building (valeur unique) 30,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 26 ; clauses financières — sans événement 26 ; items de détresse (8-K) — sans événement 26 ; continuité d'exploitation — sans événement 26 ; dépôt tardif — sans événement 26 ; faiblesse du contrôle interne — sans événement 26 ; actifs nantis — sans événement 26.

### Alphabet (GOOGL)

Dernière information balisée utilisée : 2026-07-23.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 15,9 % | 18,0 % | 21,8 % | 24,2 % |
| Croissance du revenu (douze mois glissants) | 13,4 % | 15,1 % | 17,5 % | 20,1 % |
| Capex décaissé ÷ CFO | 0,49 x | 0,53 x | 0,78 x | 1,15 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 24 461 M$ | 24 551 M$ | 10 116 M$ | -5 855 M$ |
| Flux disponible après locations-financement | 24 369 M$ | 22 957 M$ | 9 594 M$ | -6 173 M$ |
| Flux après financement des contreparties | 24 461 M$ | 24 551 M$ | 10 116 M$ | -5 855 M$ |
| Délai de recouvrement (créances) | 51 j | 51 j | 52 j | 53 j |
| Obligations de prestation restantes (RPO) | 157 700 M$ | 242 800 M$ | 467 600 M$ | 519 500 M$ |
| Dette ÷ (résultat opérationnel + dotations) | 0,19 x | 0,32 x | 0,49 x | 0,58 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,12 x | 0,12 x | 0,11 x | 0,12 x |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 59,6 % | 59,8 % | 62,4 % | 61,6 % |
| Marge opérationnelle | 30,5 % | 31,6 % | 36,1 % | 34,0 % |
| Capex décaissé ÷ revenu | 0,23 x | 0,24 x | 0,32 x | 0,38 x |
| Flux disponible après rémunération en actions | 18 093 M$ | 17 480 M$ | 3 365 M$ | -13 812 M$ |
| Rémunération en actions ÷ CFO | 0,13 x | 0,13 x | 0,15 x | 0,20 x |
| Écart CFO − résultat net | 13 435 M$ | 17 947 M$ | -16 788 M$ | -73 124 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 252,70 x | 175,32 x | 111,85 x | 65,55 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 41 060 M$ (partiel) | 44 108 M$ (partiel) | 38 985 M$ (partiel) | 51 754 M$ |
| Capitaux propres | 386 867 M$ | 415 265 M$ | 478 746 M$ | 640 480 M$ |
| Résultats non distribués (déficit si négatif) | 297 226 M$ | 324 055 M$ | 384 024 M$ | 493 371 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -1,7 % | n.d. (dénominateur négatif ou nul) | -0,4 % | 0,9 % |
| En-cours ÷ immobilisations brutes | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,04 x | 0,07 x |
| Principal dû à 24 mois ÷ trésorerie | 0,13 x | 0,10 x |
| Gains et pertes sur participations | 3 714 M$ | 24 080 M$ |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 313 M$ | 1 606 M$ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture 7 273 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 59 600 M$ (partiel).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Corporate And Other Assets (borne basse) 2,0 ans ; Corporate And Other Assets (borne haute) 25,0 ans ; Data Center and Office Buildings (borne basse) 7,0 ans ; Data Center and Office Buildings (borne haute) 40,0 ans ; Servers and Network Equipment (valeur unique) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22 ; actifs nantis — sans événement 22.

### Amazon (AMZN)

Dernière information balisée utilisée : 2026-07-31.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 13,4 % | 13,6 % | 16,6 % | 19,6 % |
| Croissance du revenu (douze mois glissants) | 11,5 % | 12,4 % | 14,2 % | 15,8 % |
| Capex décaissé ÷ CFO | 0,99 x | 0,73 x | 1,70 x | 1,19 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 430 M$ | 14 937 M$ | -18 171 M$ | -8 821 M$ |
| Flux disponible après locations-financement | 79 M$ | 14 552 M$ | -18 639 M$ | -9 216 M$ |
| Flux après financement des contreparties | 430 M$ | 14 937 M$ | -18 171 M$ | -8 821 M$ |
| Délai de recouvrement (créances) | 31 j | 29 j | 37 j | 40 j |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Dette ÷ (résultat opérationnel + dotations) | 0,40 x | 0,47 x | 0,78 x | 0,78 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,71 x | 0,70 x | 0,67 x | 0,65 x |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 50,8 % | 48,5 % | 51,8 % | 52,3 % |
| Marge opérationnelle | 9,7 % | 11,7 % | 13,1 % | 13,7 % |
| Capex décaissé ÷ revenu | 0,19 x | 0,19 x | 0,24 x | 0,27 x |
| Flux disponible après rémunération en actions | -4 417 M$ | 10 540 M$ | -22 203 M$ | -14 859 M$ |
| Rémunération en actions ÷ CFO | 0,14 x | 0,08 x | 0,15 x | 0,13 x |
| Écart CFO − résultat net | 14 338 M$ | 33 267 M$ | -4 223 M$ | -17 260 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 35,20 x | 35,17 x | 33,72 x | 28,13 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -24 476 M$ | -36 431 M$ | -33 570 M$ | -41 592 M$ |
| Capitaux propres | 369 631 M$ | 411 065 M$ | 441 914 M$ | 551 620 M$ |
| Résultats non distribués (déficit si négatif) | 229 344 M$ | 250 536 M$ | 280 791 M$ | 343 438 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 1,0 % | -25,0 % | 0,8 % | 0,9 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,06 x | 0,03 x |
| Principal dû à 24 mois ÷ trésorerie | 0,10 x | 0,13 x |
| Gains et pertes sur participations | 49 M$ | 1 200 M$ |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 854 M$ | 2 911 M$ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture 61 627 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 96 373 M$.

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Building (valeur unique) 40,0 ans ; Computer Equipment (borne basse) 5,0 ans ; Computer Equipment (borne haute) 6,0 ans ; Machinery And Equipment (borne basse) 10,0 ans ; Machinery And Equipment (borne haute) 13,0 ans ; Other Machinery and Equipment (borne basse) 3,0 ans ; Other Machinery and Equipment (borne haute) 10,0 ans ; Technology Equipment (borne basse) 5,0 ans ; Technology Equipment (borne haute) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 8, indéterminée 14 ; actifs nantis — événement 14, sans événement 8.

### Meta (META)

Dernière information balisée utilisée : 2026-07-30.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 26,2 % | 23,8 % | 33,1 % | 28,0 % |
| Croissance du revenu (douze mois glissants) | 21,3 % | 22,2 % | 26,2 % | 27,7 % |
| Capex décaissé ÷ CFO | 0,63 x | 0,59 x | 0,59 x | 0,95 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 11 170 M$ | 14 831 M$ | 13 229 M$ | 1 746 M$ |
| Flux disponible après locations-financement | 10 625 M$ | 14 077 M$ | 12 386 M$ | 784 M$ |
| Flux après financement des contreparties | 11 170 M$ | n.d. (entité non confirmée) | 13 229 M$ | 1 746 M$ |
| Délai de recouvrement (créances) | 31 j | 30 j | 28 j | 33 j |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | 0,58 x | n.d. (terme manquant) | 0,76 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | 0,26 x | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 82,0 % | 81,8 % | 81,9 % | 81,4 % |
| Marge opérationnelle | 40,1 % | 41,3 % | 40,6 % | 30,9 % |
| Capex décaissé ÷ revenu | 0,37 x | 0,36 x | 0,34 x | 0,50 x |
| Flux disponible après rémunération en actions | 5 614 M$ | 8 941 M$ | 7 197 M$ | -5 912 M$ |
| Rémunération en actions ÷ CFO | 0,19 x | 0,16 x | 0,19 x | 0,24 x |
| Écart CFO − résultat net | 27 290 M$ | 13 446 M$ | 5 453 M$ | 16 014 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (non publié) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 17 297 M$ (partiel) | 19 769 M$ (partiel) | 17 470 M$ (partiel) | 5 863 M$ (partiel) |
| Capitaux propres | 194 066 M$ | 217 243 M$ | 243 681 M$ | 261 221 M$ |
| Résultats non distribués (déficit si négatif) | 101 577 M$ | 121 179 M$ | 144 647 M$ | 157 843 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -1,1 % | n.d. (dénominateur négatif ou nul) | -1,0 % | -0,2 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | 0,00 x |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | 0,08 x |
| Gains et pertes sur participations | n.d. (non publié) | n.d. (non publié) |
| Dépréciations d'investissements | n.d. (non publié) | n.d. (non publié) |
| Additions en location-financement | 181 M$ | 613 M$ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié 103 770 M$.
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture 34 120 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 103 770 M$.

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Equipment And Other (borne basse) 1,0 ans ; Equipment And Other (borne haute) 25,0 ans ; Finance Lease, Right-Of-Use Asset (borne basse) 5,0 ans ; Finance Lease, Right-Of-Use Asset (borne haute) 20,0 ans ; Servers and Network Assets Components Stored By Suppliers (borne basse) 5,0 ans ; Servers and Network Assets Components Stored By Suppliers (borne haute) 5,5 ans ; Building (borne basse) 25,0 ans ; Building (borne haute) 30,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 16, sans événement 6 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22 ; actifs nantis — événement 2, sans événement 14, indéterminée 6.

### Microsoft (MSFT)

Dernière information balisée utilisée : 2026-07-29.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 18,4 % | 16,7 % | 18,3 % | 17,7 % |
| Croissance du revenu (douze mois glissants) | 15,6 % | 16,7 % | 17,9 % | 17,8 % |
| Capex décaissé ÷ CFO | 0,43 x | 0,84 x | 0,66 x | 0,65 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 25 663 M$ | 5 882 M$ | 15 803 M$ | 19 639 M$ |
| Flux disponible après locations-financement | 25 024 M$ | 5 181 M$ | 14 964 M$ | 18 717 M$ |
| Flux après financement des contreparties | 25 663 M$ | 5 882 M$ | 15 803 M$ | 19 639 M$ |
| Délai de recouvrement (créances) | 63 j | 64 j | 65 j | 82 j |
| Obligations de prestation restantes (RPO) | 398 000 M$ | 631 000 M$ | 633 000 M$ | 684 000 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 69,0 % | 68,0 % | 67,6 % | 67,2 % |
| Marge opérationnelle | 48,9 % | 47,1 % | 46,3 % | 45,1 % |
| Capex décaissé ÷ revenu | 0,25 x | 0,37 x | 0,37 x | 0,40 x |
| Flux disponible après rémunération en actions | 22 680 M$ | 2 663 M$ | 12 722 M$ | 16 517 M$ |
| Rémunération en actions ÷ CFO | 0,07 x | 0,09 x | 0,07 x | 0,06 x |
| Écart CFO − résultat net | 17 310 M$ | -2 700 M$ | 14 901 M$ | 19 675 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 54,35 x | 53,94 x | 52,69 x | 50,88 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -37 543 M$ | -31 110 M$ | -27 177 M$ | -33 108 M$ |
| Capitaux propres | 363 076 M$ | 390 875 M$ | 414 367 M$ | 442 387 M$ |
| Résultats non distribués (déficit si négatif) | 254 873 M$ | 280 789 M$ | 302 526 M$ | 328 265 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -0,1 % | -0,1 % | -0,2 % | n.d. (dénominateur négatif ou nul) |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2025-06-30 | 2026-06-30 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,10 x | 0,44 x |
| Principal dû à 24 mois ÷ trésorerie | 0,41 x | 0,44 x |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 20 511 M$ | 24 608 M$ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-06-30 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (concept non résolu).
Baux non commencés au 2026-06-30 (pont ouverture + nouveaux − commencés = clôture) : ouverture 92 700 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 329 100 M$.

Durées d'amortissement publiées (exercice clos le 2026-06-30) : Building And Building Improvements (borne basse) 5,0 ans ; Building And Building Improvements (borne haute) 15,0 ans ; Computer Equipment (borne basse) 2,0 ans ; Computer Equipment (borne haute) 6,0 ans ; Furniture And Fixtures (borne basse) 1,0 ans ; Furniture And Fixtures (borne haute) 10,0 ans ; Leasehold Improvements (borne basse) 3,0 ans ; Leasehold Improvements (borne haute) 15,0 ans ; Software And Software Development Costs (valeur unique) 3,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 24 ; clauses financières — sans événement 24 ; items de détresse (8-K) — sans événement 24 ; continuité d'exploitation — sans événement 24 ; dépôt tardif — sans événement 24 ; faiblesse du contrôle interne — sans événement 24 ; actifs nantis — sans événement 24.

### Oracle (ORCL)

Dernière information balisée utilisée : 2026-09-11.

| Mesure (trimestre clos le) | 2025-11-30 | 2026-02-28 | 2026-05-31 | 2026-08-31 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 14,2 % | 21,7 % | 20,6 % | 29,6 % |
| Croissance du revenu (douze mois glissants) | 11,1 % | 14,9 % | 17,4 % | 21,6 % |
| Capex décaissé ÷ CFO | 5,82 x | 2,61 x | 1,13 x | 1,23 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -9 967 M$ | -11 484 M$ | -1 873 M$ | -5 396 M$ |
| Flux disponible après locations-financement | -10 080 M$ | -11 571 M$ | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux après financement des contreparties | -9 967 M$ | -11 484 M$ | -1 873 M$ | -5 396 M$ |
| Délai de recouvrement (créances) | 53 j | 56 j | 50 j | 54 j |
| Obligations de prestation restantes (RPO) | 523 300 M$ | 552 600 M$ | 638 000 M$ | 664 000 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 1,00 x | 1,06 x | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Marge opérationnelle | 29,5 % | 31,8 % | 32,0 % | 34,8 % |
| Capex décaissé ÷ revenu | 0,75 x | 1,08 x | 0,86 x | 1,47 x |
| Flux disponible après rémunération en actions | -11 123 M$ | -12 812 M$ | -3 076 M$ | -6 523 M$ |
| Rémunération en actions ÷ CFO | 0,56 x | 0,19 x | 0,08 x | 0,05 x |
| Écart CFO − résultat net | -4 069 M$ | 3 430 M$ | 10 316 M$ | 18 343 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 4,80 x | 4,73 x | 4,48 x | 4,52 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -10 640 M$ (partiel) | -8 636 M$ (partiel) | -10 508 M$ (partiel) | -14 355 M$ (partiel) |
| Capitaux propres | 29 951 M$ | 38 495 M$ | 42 508 M$ | 66 772 M$ |
| Résultats non distribués (déficit si négatif) | -9 355 M$ | -7 092 M$ | -4 309 M$ | -1 114 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 1,8 % | 1,3 % | -100,0 % | 3,1 % |
| En-cours ÷ immobilisations brutes | n.d. (non publié) | n.d. (non publié) | 32,6 % | 31,6 % |

| Mesure (exercice clos le) | 2025-05-31 | 2026-05-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,68 x | 0,23 x |
| Principal dû à 24 mois ÷ trésorerie | 1,21 x | 0,55 x |
| Gains et pertes sur participations | n.d. (non publié) | n.d. (non publié) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 2 900 M$ | 4 946 M$ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-05-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : after_year_5 7 533 M$ ; total publié 13 309 M$ ; within_12m 1 841 M$ ; year_2 1 034 M$ ; year_3 1 053 M$ ; year_4 952 M$ ; year_5 896 M$.
Baux non commencés au 2026-05-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture 43 400 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 260 000 M$.

Durées d'amortissement publiées (exercice clos le 2026-05-31) : Servers and Networking Equipment (valeur unique) 6,0 ans ; Building And Building Improvements (borne basse) 1,0 ans ; Building And Building Improvements (borne haute) 40,0 ans ; Furniture And Fixtures (borne basse) 5,0 ans ; Furniture And Fixtures (borne haute) 15,0 ans ; Machinery And Equipment (borne basse) 1,0 ans ; Machinery And Equipment (borne haute) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 25 ; clauses financières — sans événement 13, sans événement 12 ; items de détresse (8-K) — sans événement 25 ; continuité d'exploitation — sans événement 25 ; dépôt tardif — sans événement 25 ; faiblesse du contrôle interne — sans événement 23, indéterminée 2 ; actifs nantis — sans événement 13, indéterminée 12.

### CoreWeave (CRWV)

Dernière information balisée utilisée : 2026-08-12.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 133,7 % | 110,4 % | 111,6 % | 112,5 % |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | 167,9 % | 129,9 % | 115,3 % |
| Capex décaissé ÷ CFO | 1,41 x | 2,60 x | 2,58 x | 9,46 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -700 M$ | -2 501 M$ | -4 711 M$ | -5 743 M$ |
| Flux disponible après locations-financement | n.d. (terme manquant) | n.d. (terme manquant) | -4 726 M$ | -5 761 M$ |
| Flux après financement des contreparties | -700 M$ | -2 501 M$ | -4 711 M$ | -5 743 M$ |
| Délai de recouvrement (créances) | 112 j | 185 j | 92 j | 90 j |
| Obligations de prestation restantes (RPO) | 50 000 M$ | 60 700 M$ | 98 800 M$ | 103 700 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | 8,88 x | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | 3,51 x | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 73,0 % | 67,6 % | 65,5 % | 65,9 % |
| Marge opérationnelle | 3,8 % | -5,7 % | -6,9 % | -1,9 % |
| Capex décaissé ÷ revenu | 1,75 x | 2,58 x | 3,70 x | 2,49 x |
| Flux disponible après rémunération en actions | -844 M$ | -2 657 M$ | -4 864 M$ | -5 908 M$ |
| Rémunération en actions ÷ CFO | 0,09 x | 0,10 x | 0,05 x | 0,24 x |
| Écart CFO − résultat net | 1 799 M$ | 2 011 M$ | 3 724 M$ | 1 305 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (terme manquant) | -0,04 x | -0,12 x | -0,14 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -605 M$ (partiel) | -163 M$ (partiel) | -3 381 M$ (partiel) | -3 778 M$ (partiel) |
| Capitaux propres | 3 878 M$ | 3 335 M$ | 4 759 M$ | 5 024 M$ |
| Résultats non distribués (déficit si négatif) | -2 192 M$ | -2 643 M$ | -3 383 M$ | -4 009 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 132,9 % | 235,0 % | 111,6 % | 13,1 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | 2,15 x |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | 3,52 x |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 142 M$ | 343 M$ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | 0 $ | 350 M$ |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (concept non résolu).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 38 500 M$.

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Data Center Equipment And Leasehold Improvements (valeur unique) 12,0 ans ; Furniture, Fixtures, and Other Assets (borne basse) 3,0 ans ; Furniture, Fixtures, and Other Assets (borne haute) 5,0 ans ; Software (borne basse) 3,0 ans ; Software (borne haute) 6,0 ans ; Technology Equipment (valeur unique) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — événement 5, sans événement 2, sans événement 15 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 6, indéterminée 16 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — événement 6, indéterminée 16 ; actifs nantis — événement 7, indéterminée 15.

### SpaceX (SPCX)

Dernière information balisée utilisée : 2026-08-04.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | 91,9 % |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex décaissé ÷ CFO | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible après locations-financement | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux après financement des contreparties | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Délai de recouvrement (créances) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | 42 j |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 47 461 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | 55,3 % |
| Marge opérationnelle | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | -1,8 % |
| Capex décaissé ÷ revenu | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible après rémunération en actions | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Rémunération en actions ÷ CFO | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Écart CFO − résultat net | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | n.d. (terme manquant) | -13 908 M$ | n.d. (terme manquant) | -9 906 M$ |
| Capitaux propres | n.d. (non publié) | 2 573 M$ | 34 533 M$ | 127 224 M$ |
| Résultats non distribués (déficit si négatif) | n.d. (non publié) | -37 035 M$ | n.d. (non publié) | -41 852 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | 100,2 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Gains et pertes sur participations | n.d. (non publié) | n.d. (non publié) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — événement 1, sans événement 1, sans événement 20 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 1, indéterminée 21 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 1, indéterminée 21 ; actifs nantis — événement 2, indéterminée 20.

### AMD (AMD)

Dernière information balisée utilisée : 2026-08-05.

| Mesure (trimestre clos le) | 2025-09-27 | 2025-12-27 | 2026-03-28 | 2026-06-27 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 35,6 % | 34,1 % | 37,8 % | 50,1 % |
| Croissance du revenu (douze mois glissants) | 31,8 % | 34,3 % | 35,0 % | 39,5 % |
| Capex décaissé ÷ CFO | 0,12 x | 0,09 x | 0,13 x | 0,34 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 1 901 M$ | 2 378 M$ | 2 566 M$ | 1 558 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 1 901 M$ | 2 378 M$ | 2 566 M$ | 1 558 M$ |
| Délai de recouvrement (créances) | 61 j | 56 j | 54 j | 57 j |
| Obligations de prestation restantes (RPO) | 279 M$ | 315 M$ | 264 M$ | 222 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 51,7 % | 54,3 % | 52,8 % | 53,8 % |
| Marge opérationnelle | 13,7 % | 17,1 % | 14,4 % | 17,3 % |
| Capex décaissé ÷ revenu | 0,03 x | 0,02 x | 0,04 x | 0,07 x |
| Flux disponible après rémunération en actions | 1 482 M$ | 1 892 M$ | 2 079 M$ | 1 055 M$ |
| Rémunération en actions ÷ CFO | 0,19 x | 0,19 x | 0,16 x | 0,21 x |
| Écart CFO − résultat net | 916 M$ | 1 089 M$ | 1 572 M$ | 69 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 24,68 x | 28,20 x | 29,49 x | 44,14 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 10 031 M$ (partiel) | 11 306 M$ (partiel) | 11 083 M$ (partiel) | 10 390 M$ (partiel) |
| Capitaux propres | 60 790 M$ | 62 999 M$ | 64 462 M$ | 67 224 M$ |
| Résultats non distribués (déficit si négatif) | 5 188 M$ | 6 699 M$ | 8 082 M$ | 5 909 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 0,3 % | n.d. (dénominateur négatif ou nul) | 1,5 % | 1,8 % |
| En-cours ÷ immobilisations brutes | 12,5 % | 10,3 % | 11,8 % | 18,1 % |

| Mesure (exercice clos le) | 2024-12-28 | 2025-12-27 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | 0,16 x |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Gains et pertes sur participations | n.d. (non publié) | n.d. (non publié) |
| Dépréciations d'investissements | n.d. (non publié) | 53 M$ |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (non publié) | n.d. (non publié) |
| Additions payées en titres | 0 $ | n.d. (non publié) |

Obligations d'achat publiées au 2025-12-27 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : after_year_5 0 $ ; total publié 12 166 M$ ; within_12m 8 498 M$ ; year_2 1 099 M$ ; year_3 1 216 M$ ; year_4 1 197 M$ ; year_5 156 M$.
Baux non commencés au 2025-12-27 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 1 300 M$.

Durées d'amortissement publiées (exercice clos le 2021-12-25) : Equipment (borne basse) 2,0 ans ; Equipment (borne haute) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22 ; actifs nantis — événement 2, sans événement 20.

### Broadcom (AVGO)

Dernière information balisée utilisée : 2026-09-10.

| Mesure (trimestre clos le) | 2025-11-02 | 2026-02-01 | 2026-05-03 | 2026-08-02 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 28,2 % | 29,5 % | 47,9 % | 85,5 % |
| Croissance du revenu (douze mois glissants) | 23,9 % | 25,2 % | 32,3 % | 48,7 % |
| Capex décaissé ÷ CFO | 0,03 x | 0,03 x | 0,02 x | 0,04 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 7 466 M$ | 8 010 M$ | 10 262 M$ | 13 665 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 7 466 M$ | 8 010 M$ | 10 262 M$ | 13 665 M$ |
| Délai de recouvrement (créances) | 36 j | 40 j | 44 j | 42 j |
| Obligations de prestation restantes (RPO) | 33 300 M$ | 45 000 M$ | 164 600 M$ | 179 200 M$ |
| Dette ÷ (résultat opérationnel + dotations) | 2,58 x | 2,33 x | 1,95 x | 1,37 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 68,0 % | 68,1 % | 69,5 % | 69,1 % |
| Marge opérationnelle | 41,7 % | 44,3 % | 48,6 % | 53,9 % |
| Capex décaissé ÷ revenu | 0,01 x | 0,01 x | 0,01 x | 0,02 x |
| Flux disponible après rémunération en actions | 5 271 M$ | 5 834 M$ | 8 170 M$ | 11 646 M$ |
| Rémunération en actions ÷ CFO | 0,28 x | 0,26 x | 0,20 x | 0,14 x |
| Écart CFO − résultat net | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 7,94 x | 8,86 x | 10,41 x | 13,74 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -1 614 M$ | 122 M$ | 2 783 M$ | 4 729 M$ |
| Capitaux propres | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Résultats non distribués (déficit si négatif) | 9 761 M$ | 6 520 M$ | 12 166 M$ | 22 151 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -25,0 % | 1,1 % | 1,0 % | 0,6 % |
| En-cours ÷ immobilisations brutes | 1,1 % | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |

| Mesure (exercice clos le) | 2024-11-03 | 2025-11-02 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,13 x | 0,19 x |
| Principal dû à 24 mois ÷ trésorerie | 0,47 x | 0,35 x |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 49 M$ | n.d. (non publié) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-11-02 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : after_year_5 0 $ ; total publié 132 M$ ; within_12m 106 M$ ; year_2 12 M$ ; year_3 10 M$ ; year_4 4 M$ ; year_5 0 $.
Baux non commencés au 2025-11-02 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-11-02) : Buildings and Leasehold Improvements (borne basse) 15,0 ans ; Buildings and Leasehold Improvements (borne haute) 40,0 ans ; Machinery And Equipment (borne basse) 3,0 ans ; Machinery And Equipment (borne haute) 10,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 23 ; clauses financières — sans événement 23 ; items de détresse (8-K) — sans événement 23 ; continuité d'exploitation — sans événement 23 ; dépôt tardif — sans événement 23 ; faiblesse du contrôle interne — sans événement 23 ; actifs nantis — sans événement 23.

### Marvell (MRVL)

Dernière information balisée utilisée : 2026-08-28.

| Mesure (trimestre clos le) | 2025-11-01 | 2026-01-31 | 2026-05-02 | 2026-08-01 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 36,8 % | 22,1 % | 27,6 % | 36,5 % |
| Croissance du revenu (douze mois glissants) | 45,0 % | 42,1 % | 34,1 % | 30,6 % |
| Capex décaissé ÷ CFO | 0,13 x | 0,31 x | 0,24 x | 0,21 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 509 M$ | 259 M$ | 483 M$ | 479 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 509 M$ | 259 M$ | 483 M$ | 479 M$ |
| Délai de recouvrement (créances) | 68 j | 90 j | 70 j | 74 j |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 51,6 % | 51,7 % | 52,1 % | 53,1 % |
| Marge opérationnelle | 17,2 % | 18,2 % | 14,0 % | 16,8 % |
| Capex décaissé ÷ revenu | 0,04 x | 0,05 x | 0,06 x | 0,05 x |
| Flux disponible après rémunération en actions | 357 M$ | 116 M$ | 276 M$ | 153 M$ |
| Rémunération en actions ÷ CFO | 0,26 x | 0,38 x | 0,32 x | 0,54 x |
| Écart CFO − résultat net | -1 319 M$ | -22 M$ | 604 M$ | 298 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 5,86 x | 6,53 x | 6,73 x | 7,21 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 1 927 M$ (partiel) | 2 501 M$ (partiel) | 2 563 M$ (partiel) | 2 781 M$ (partiel) |
| Capitaux propres | 14 057 M$ | 14 308 M$ | 18 216 M$ | 18 532 M$ |
| Résultats non distribués (déficit si négatif) | 1 010 M$ | 1 356 M$ | 1 336 M$ | 1 591 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -0,2 % | n.d. (non publié) | 2,0 % | 5,8 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2025-02-01 | 2026-01-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,14 x | 0,19 x |
| Principal dû à 24 mois ÷ trésorerie | 1,15 x | 0,19 x |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-01-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2026-01-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2026-01-31) : Building Improvements (valeur unique) 15,0 ans ; Building (valeur unique) 30,0 ans ; Furniture And Fixtures (borne basse) 3,0 ans ; Furniture And Fixtures (borne haute) 4,0 ans ; Machinery And Equipment (borne basse) 2,0 ans ; Machinery And Equipment (borne haute) 7,0 ans ; Software And Software Development Costs (borne basse) 3,0 ans ; Software And Software Development Costs (borne haute) 4,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 26 ; clauses financières — événement 3, sans événement 23 ; items de détresse (8-K) — événement 1, sans événement 25 ; continuité d'exploitation — sans événement 26 ; dépôt tardif — sans événement 26 ; faiblesse du contrôle interne — sans événement 26 ; actifs nantis — sans événement 26.

## Circularité, par paire

Une paire réunit un groupe du périmètre et une contrepartie que ses pièces nomment, avec au moins une arête entre eux : client, financé, financeur ou prêteur (une paire seulement financière, comme un prêt bancaire, n'a pas de revenu à rapprocher). Aucune de ces mesures ne prouve une circularité ; la conclusion s'en tient aux valeurs de `relationship_conclusion`, et un numérateur vide se publie indéterminé, à côté des sorties de couverture (E.9).

### AMD → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L2, L5) ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E4 (engagement) : compatible ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### AMD → Meta

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E4 (engagement) : compatible ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Amazon → Apple Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-31 : n.d. (recherche incomplète) ; 2024-12-31 : n.d. (recherche incomplète) ; 2025-12-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Amazon → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (4 sur 4).
- Annexe E : E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Broadcom → Apple Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (recherche incomplète) ; 2022-10-30 : n.d. (recherche incomplète) ; 2023-10-29 : n.d. (recherche incomplète) ; 2024-11-03 : n.d. (recherche incomplète) ; 2025-11-02 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Broadcom → Silicon Manufacturing Partners Pte. Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 28 trimestres ; sensibilité `ever_financed` : actif 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : entre 0 % et 18 % ; 2022-10-30 : entre 0 % et 20 % ; 2023-10-29 : entre 0 % et 22 % ; 2024-11-03 : entre 0 % et 28 % ; 2025-11-02 : entre 0 % et 32 %.
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Broadcom → Alphabet

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (une archive de la période est illisible) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 23 trimestres, inconnu 5 trimestres ; sensibilité `ever_financed` : jamais documenté 23 trimestres, inconnu 5 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (précondition non remplie) ; 2022-10-30 : n.d. (précondition non remplie) ; 2023-10-29 : n.d. (précondition non remplie) ; 2024-11-03 : n.d. (précondition non remplie) ; 2025-11-02 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Broadcom → Anthropic

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (précondition non remplie) ; 2022-10-30 : n.d. (précondition non remplie) ; 2023-10-29 : n.d. (précondition non remplie) ; 2024-11-03 : n.d. (précondition non remplie) ; 2025-11-02 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Broadcom → Meta

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (précondition non remplie) ; 2022-10-30 : n.d. (précondition non remplie) ; 2023-10-29 : n.d. (précondition non remplie) ; 2024-11-03 : n.d. (précondition non remplie) ; 2025-11-02 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → Jane Street Group, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → MagAI Ventures

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 17 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → MAIV

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, échu 1 trimestre, inconnu 18 trimestres ; sensibilité `ever_financed` : actif 9 trimestres, inconnu 18 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : entre 0 % et 68 %.
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### CoreWeave → OpenAI

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 19 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 6 trimestres, inconnu 21 trimestres ; sensibilité `ever_financed` : actif 6 trimestres, inconnu 21 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : entre 0 % et 68 %.
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 60 % (3 sur 5).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### CoreWeave → Meta

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → Microsoft

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → NVIDIA

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → Kitty Hawk Corporation

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-31 : n.d. (recherche incomplète) ; 2024-12-31 : n.d. (recherche incomplète) ; 2025-12-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → LTA Research & Exploration LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-31 : n.d. (recherche incomplète) ; 2024-12-31 : n.d. (recherche incomplète) ; 2025-12-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Meta → Jio Platforms Limited

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 24 trimestres, inconnu 3 trimestres ; sensibilité `ever_financed` : actif 24 trimestres, inconnu 3 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Marvell → Amazon

- Conclusion : **causalité non établie** ; structure financière seulement ; lien documenté (L2) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-30 : n.d. (précondition non remplie) ; 2022-01-29 : n.d. (précondition non remplie) ; 2023-01-28 : n.d. (précondition non remplie) ; 2024-02-03 : n.d. (précondition non remplie) ; 2025-02-01 : n.d. (précondition non remplie) ; 2026-01-31 : n.d. (précondition non remplie).
- Contrepartie payable au client : 6 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Marvell → Alphabet

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète (une archive de la période est illisible) ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 23 trimestres, inconnu 8 trimestres ; sensibilité `ever_financed` : jamais documenté 23 trimestres, inconnu 8 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-30 : n.d. (lecture impossible) ; 2022-01-29 : n.d. (précondition non remplie) ; 2023-01-28 : n.d. (précondition non remplie) ; 2024-02-03 : n.d. (précondition non remplie) ; 2025-02-01 : n.d. (précondition non remplie) ; 2026-01-31 : n.d. (précondition non remplie).
- Contrepartie payable au client : 6 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Microsoft → OpenAI

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 18 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, jamais documenté 21 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, jamais documenté 21 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : entre 0 % et 10 % (borne haute exclue) ; 2026-06-30 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### NVIDIA → CoreWeave

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 6 trimestres, jamais documenté 25 trimestres ; sensibilité `ever_financed` : actif 6 trimestres, jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : entre 0 % et 22 %.
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E1 : étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### NVIDIA → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Oracle → Ampere Computing Holdings LLC

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 4 trimestres, inconnu 26 trimestres ; sensibilité `ever_financed` : actif 4 trimestres, inconnu 26 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Oracle → Ampere Computing LLC

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 22 trimestres, échu 8 trimestres ; sensibilité `ever_financed` : actif 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2026-05-31 : n.d. (recherche incomplète).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Oracle → Autonomous Medical Devices, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Desert Champions LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Eau Palm Beach Resort & Spa

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Ellison Institute, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Lanai Resorts, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Lawrence Investments, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Screening Room Media, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, échu 28 trimestres ; sensibilité `ever_financed` : actif 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — recherche incomplète ; E2 à 10 % : indéterminé — recherche incomplète ; E2 à 20 % : indéterminé — recherche incomplète ; E5 : indéterminé — non publié.

### Oracle → Sensei AG Holdings, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### SpaceX → Tesla, Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète (le client peut déposer hors du périmètre, découverte (§14) non ouverte) ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-31 : n.d. (recherche incomplète) ; 2024-12-31 : n.d. (recherche incomplète) ; 2025-12-31 : n.d. (recherche incomplète).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Sorties de couverture par fournisseur (§3.6)

| Fournisseur | Exercice | Revenu attribué à des clients nommés | Clients anonymes d'au moins 10 % | Résidu | Paires vues seulement côté client |
| --- | --- | ---: | ---: | ---: | ---: |
| NVIDIA | 2026-01-25 | 0,0 % | 36,0 % [35,0 % ; 37,0 %] | 64,0 % | 0 |
| Alphabet | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Amazon | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Meta | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Microsoft | 2026-06-30 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Oracle | 2026-05-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| CoreWeave | 2025-12-31 | 0,0 % | 67,0 % [66,5 % ; 67,5 %] | 33,0 % | 0 |
| SpaceX | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| AMD | 2025-12-27 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Broadcom | 2025-11-02 | 0,0 % | 32,0 % [31,5 % ; 32,5 %] | 68,0 % | 1 |
| Marvell | 2026-01-31 | 0,0 % | 51,0 % [50,0 % ; 52,0 %] | 49,0 % | 0 |

Le texte qui entoure les faits de concentration est lu (bloc text de §14) : un client qui reste anonyme l'est dans les pièces elles-mêmes. Un client nommé ailleurs peut être l'un des anonymes (`overlap_possible`).

## Côté prêteur (BDC Data Sets)

Positions que les sociétés de développement d'affaires (BDC) publient dans leur portefeuille, rattachées aux entités des groupes et aux contreparties que nomment leurs pièces, par dénomination légale entière ; une position dont l'identifiant nomme aussi un autre émetteur n'est rattachée à personne. Vue `as_known` : le portefeuille à la date du bilan du dépôt de chaque fonds. Les fonds privés et les banques ne publient rien (`not_public`), et une balise absente ne prouve rien : un taux d'intérêt capitalisé ou un statut de non-accumulation non balisé reste indéterminé, jamais nul. Juste valeur ÷ coût n'est pas une probabilité de défaut, et des intérêts capitalisés peuvent être prévus dès l'origine : les trois signaux se lisent ensemble.

| Groupe de l'émetteur | Date du bilan | Instrument | Positions | Coût | Juste valeur | Juste valeur ÷ coût | Part des intérêts capitalisés | Part sans accumulation d'intérêts |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Broadcom | 2022-12-31 | non classé | 1 | 5 M$ | 5 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2026-06-30 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2022-09-30 | prêts et obligations | 1 | 30 M$ | 30 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2022-09-30 | titres de capital | 1 | 296 000 $ | 119 000 $ | 0,40 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2022-12-31 | prêts et obligations | 1 | 30 M$ | 11 M$ | 0,38 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2022-12-31 | titres de capital | 1 | 296 000 $ | 7 000 $ | 0,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2023-03-31 | prêts et obligations | 7 | 87 M$ | 46 M$ | 0,53 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2023-03-31 | titres de capital | 4 | 638 000 $ | 60 000 $ | 0,09 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2023-06-30 | prêts et obligations | 9 | 87 M$ | 51 M$ | 0,59 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2023-06-30 | titres de capital | 4 | 638 000 $ | 168 000 $ | 0,26 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2023-09-30 | prêts et obligations | 9 | 87 M$ | 66 M$ | 0,76 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2023-09-30 | titres de capital | 4 | 638 000 $ | 141 000 $ | 0,22 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2023-12-31 | prêts et obligations | 7 | 87 M$ | 75 M$ | 0,86 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2023-12-31 | titres de capital | 3 | 638 000 $ | 286 000 $ | 0,45 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific, Inc. | 2024-03-31 | titres de capital | 10 | 53 M$ | 49 M$ | 0,92 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2022-12-31 | non classé | 1 | 5 M$ | 4 M$ | 0,89 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2023-03-31 | non classé | 1 | 5 M$ | 4 M$ | 0,92 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2023-06-30 | non classé | 1 | 7 M$ | 6 M$ | 0,91 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2023-09-30 | non classé | 1 | 7 M$ | 6 M$ | 0,90 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2024-03-31 | non classé | 2 | 11 M$ | 11 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2024-06-30 | prêts et obligations | 1 | 6 M$ | 6 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2024-06-30 | non classé | 1 | 7 M$ | 7 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2024-09-30 | prêts et obligations | 1 | 6 M$ | 6 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2024-09-30 | non classé | 1 | 7 M$ | 7 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2024-12-31 | non classé | 2 | 13 M$ | 13 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2025-03-31 | non classé | 1 | 6 M$ | 6 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2025-06-30 | prêts et obligations | 3 | 25 M$ | 25 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2025-06-30 | non classé | 2 | 7 M$ | 7 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2025-09-30 | prêts et obligations | 3 | 76 M$ | 76 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2025-09-30 | non classé | 2 | 11 M$ | 11 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2025-11-30 | prêts et obligations | 1 | 4 M$ | 4 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2025-12-31 | prêts et obligations | 3 | 75 M$ | 76 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2025-12-31 | non classé | 2 | 9 M$ | 9 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2026-03-31 | prêts et obligations | 3 | 25 M$ | 25 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2026-03-31 | non classé | 2 | 9 M$ | 9 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2026-06-30 | prêts et obligations | 1 | 24 M$ | 24 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Jane Street Group, LLC | 2026-06-30 | non classé | 2 | 9 M$ | 9 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| VMware, Inc. | 2022-12-31 | non classé | 1 | 3 M$ | 3 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| X Corp. | 2025-03-31 | non classé | 1 | 10 M$ | 10 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| X Corp. | 2025-06-30 | prêts et obligations | 4 | 124 M$ | 125 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| X Corp. | 2025-06-30 | non classé | 2 | 12 M$ | 12 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| X Corp. | 2025-09-30 | prêts et obligations | 5 | 123 M$ | 126 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| X Corp. | 2025-09-30 | non classé | 2 | 17 M$ | 17 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| X Corp. | 2025-12-31 | prêts et obligations | 4 | 98 M$ | 100 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| X Corp. | 2025-12-31 | non classé | 2 | 12 M$ | 12 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| X Holdings Corp. | 2025-03-31 | prêts et obligations | 3 | 35 M$ | 36 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| X Holdings Corp. | 2025-06-30 | prêts et obligations | 2 | 30 M$ | 29 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| X Holdings Corp. | 2025-09-30 | prêts et obligations | 6 | 48 M$ | 48 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| X Holdings Corp. | 2025-12-31 | prêts et obligations | 6 | 56 M$ | 56 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2023-09-30 | prêts et obligations | 8 | 687 000 $ | 685 000 $ | 1,00 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2023-12-31 | prêts et obligations | 8 | 10 M$ | 10 M$ | 1,00 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2024-03-31 | prêts et obligations | 5 | 17 M$ | 18 M$ | 1,02 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2024-06-30 | prêts et obligations | 13 | 19 M$ | 19 M$ | 1,02 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2024-09-30 | prêts et obligations | 14 | 32 M$ | 33 M$ | 1,01 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2024-12-31 | prêts et obligations | 11 | 53 M$ | 54 M$ | 1,01 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2025-03-31 | prêts et obligations | 9 | 64 M$ | 64 M$ | 1,01 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2025-06-30 | prêts et obligations | 10 | 69 M$ | 69 M$ | 1,01 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2025-06-30 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2025-09-30 | prêts et obligations | 8 | 69 M$ | 69 M$ | 1,01 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2025-12-31 | prêts et obligations | 8 | 68 M$ | 68 M$ | 1,01 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2026-03-31 | prêts et obligations | 7 | 60 M$ | 61 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| CoreWeave | 2026-06-30 | prêts et obligations | 20 | 60 M$ | 61 M$ | 1,02 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Oracle | 2022-12-31 | non classé | 1 | 1 M$ | 1 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2022-09-30 | titres de capital | 2 | 3 M$ | 4 M$ | 1,30 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2022-12-31 | titres de capital | 2 | 3 M$ | 4 M$ | 1,40 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2023-03-31 | titres de capital | 4 | 30 M$ | 43 M$ | 1,43 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2023-06-30 | titres de capital | 4 | 30 M$ | 43 M$ | 1,43 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2023-09-30 | titres de capital | 4 | 30 M$ | 45 M$ | 1,51 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2023-12-31 | titres de capital | 4 | 30 M$ | 51 M$ | 1,71 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2024-03-31 | titres de capital | 4 | 30 M$ | 54 M$ | 1,80 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2024-06-30 | titres de capital | 4 | 30 M$ | 60 M$ | 2,00 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2024-09-30 | titres de capital | 4 | 30 M$ | 63 M$ | 2,09 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2024-12-31 | titres de capital | 4 | 30 M$ | 100 M$ | 3,33 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2025-03-31 | titres de capital | 4 | 30 M$ | 105 M$ | 3,51 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2025-06-30 | titres de capital | 4 | 30 M$ | 105 M$ | 3,51 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2025-09-30 | titres de capital | 4 | 30 M$ | 120 M$ | 4,01 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2025-12-31 | titres de capital | 4 | 30 M$ | 217 M$ | 7,22 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2026-03-31 | titres de capital | 4 | 13 M$ | 147 M$ | 10,94 x | n.d. (non balisé) | n.d. (non balisé) |
| SpaceX | 2026-06-30 | titres de capital | 2 | 13 M$ | 239 M$ | 17,75 x | n.d. (non balisé) | n.d. (non balisé) |

Appartenances datées : VMware, Inc. appartient au groupe Broadcom : avant cette date, la vue `as_known` le garde comme groupe propre. X Corp. appartient au groupe SpaceX en vue `revised` depuis le 2023-01-01 (contrôle commun), en vue `as_known` depuis le 2026-02-02 : avant cette date, la vue `as_known` le garde comme groupe propre. X Holdings Corp. appartient au groupe SpaceX en vue `revised` depuis le 2023-01-01 (contrôle commun), en vue `as_known` depuis le 2026-02-02 : avant cette date, la vue `as_known` le garde comme groupe propre.

Identifiants de position écartés parce qu'ils nomment deux émetteurs : 11.

## Évolution

Premier passage : aucune exécution antérieure à laquelle comparer. Les séries trimestrielles complètes, ruptures de base marquées, sont dans `series.md` ; `delta.md` sera le point d'entrée des exécutions suivantes.

## Ce qui n'a pas pu être établi

Cellules indéterminées en vue `as_known`, par motif : concept non résolu 1 719, terme manquant 1 655, non publié 1 548, recherche incomplète 838, non balisé 552, annuel seulement 394, historique tronqué 380, client anonyme 83, précondition non remplie 68, lecture impossible 59, période antérieure absente 45, dénominateur négatif ou nul 41, frontière de retraitement 21, non traité (bloc de §14 non lu ou fermé) 11, intervalle à cheval sur le seuil 9, date manquante 8, entité non confirmée 3, dénominateur sous le seuil 2.

