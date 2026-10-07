# Note de synthèse — fragilité financière de la chaîne IA

*Exécution du 2026-10-07 · spec v6.14 · périmètre : premier passage · rendu généré depuis les tables `measures`, `controls` et `exclusions`, jamais édité à la main.*

## En tête

- **Critères des annexes E et F et seuils : inchangés** depuis leur commit d'origine `3ff3b988a48a5c904f88f006d263bfa780739d39` (2026-10-07 10:54:38), antérieur à la première requête. `config.yaml` a changé depuis (dernier commit qui le touche : `852264fe8bf42fd3264fcd421b8cb2711ccf9c9e`, plus les changements de cette exécution) sans toucher ces critères : `concept_anchors` (second candidat de capex, D-0012); `confirmed_entities` (entités confirmées par extrait, D-0021); `entity_aliases` (alias confirmés par extrait, D-0021); `own_entities` (entités propres confirmées par extrait, D-0021).
- **Périmètre couvert : premier passage.** Faits balisés des onze groupes, puis notes de parties liées, Item 404, Item 9A, Item 4 des 10-Q, continuité d'exploitation et items 1.01, 1.02, 3.03 et 8.01 des 8-K avec leurs pièces EX-10 et EX-4. Les notes d'investissements, de dette, de baux et d'engagements ne sont pas lues : ce qui en dépend est publié partiel ou indéterminé, motif « non traité au premier passage ».
- **Résultat principal (E.7) : les pièces déposées ne permettent pas de discriminer entre les deux lectures.** 92 % des issues de E.1 et E.2 au point de tête (10 %) sont indéterminées, sur 12 issues ; motifs : recherche incomplète : 5, précondition non remplie : 3, intervalle à cheval sur le seuil : 2, non traité au premier passage : 1. Au premier passage, cette non-discrimination tient d'abord au périmètre borné de la lecture, non à une absence de relations.
- **Contrôles comptables, vue `as_known`** : `mismatch` 603, `not_testable` 507, `ok` 13 615, `tautological` 613 (un contrôle `tautological` n'est jamais compté comme réussi ; un `mismatch` est un résultat publié, avec son code d'explication, dans `controls`).
- **Contrôles comptables, vue `revised`** : `mismatch` 775, `not_testable` 720, `ok` 13 425, `tautological` 613.
  Par contrôle (`mismatch` sur total, vue `as_known`) : C10 78/445, C11 48/462, C12 206/1 153, C13 0/199, C14 9/499, C15 61/273, C16 0/192, C1 79/6 754, C2 29/3 868, C3 54/261, C5 0/36, C6 0/613, C7 1/212, C8 38/78, C9 0/293.
- **Exclusions principales** : `conflicting` 377, `financial_parties_only` 217, `pending_entity` 48, `not_processed` 11, `submitted_draft` 8, `parse_failed` 1, `not_public` 1, `history_left_censored` 1, `invalid_aggregate` 1.
- **Arrêt** : aucun ; ni refus durable de la SEC, ni échec général des contrôles.

## Événements (annexe F)

Chaque événement est un observable daté, avec sa pièce ; aucune somme, aucun score. Un trimestre dont la source n'a pas été lue n'est jamais présenté comme un trimestre sans événement.

**NVIDIA**

- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-11-18, rattaché au trimestre clos le 2022-10-30 ; pièce : faits balisés.
- F7 (baisse d'une durée d'amortissement publiée) — rendu public le 2025-02-26, rattaché au trimestre clos le 2025-01-26 ; pièce : durées publiées (faits balisés de deux 10-K successifs).

**Amazon**

- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2021-07-30, rattaché au trimestre clos le 2021-06-30 ; pièce : 10-Q 0001018724-21-000020.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2021-10-29, rattaché au trimestre clos le 2021-09-30 ; pièce : 10-Q 0001018724-21-000028.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2022-10-28, rattaché au trimestre clos le 2022-09-30 ; pièce : 10-Q 0001018724-22-000023.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-07-31, rattaché au trimestre clos le 2026-06-30 ; pièce : 10-Q 0001018724-26-000026.

**Meta**

- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-07-28, rattaché au trimestre clos le 2022-06-30 ; pièce : faits balisés.

**Microsoft**

- F7 (baisse d'une durée d'amortissement publiée) — rendu public le 2025-07-30, rattaché au trimestre clos le 2025-06-30 ; pièce : durées publiées (faits balisés de deux 10-K successifs).

**Oracle**

- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-09-10, rattaché au trimestre clos le 2025-08-31 ; pièce : 10-Q 0001193125-25-200095.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-12-11, rattaché au trimestre clos le 2025-11-30 ; pièce : 10-Q 0001193125-25-200095, 10-Q 0001193125-25-315925.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-03-11, rattaché au trimestre clos le 2026-02-28 ; pièce : 10-Q 0001193125-25-315925, 10-Q 0001193125-26-101045.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-06-22, rattaché au trimestre clos le 2026-05-31 ; pièce : 10-K 0001193125-26-277521, 10-Q 0001193125-26-101045.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-09-11, rattaché au trimestre clos le 2026-08-31 ; pièce : 10-Q 0001193125-26-389274.

**CoreWeave**

- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-03-02, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-Q 0001769628-25-000062, 10-K 0001769628-26-000104.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-10-02, rattaché au trimestre clos le 2024-12-31 ; pièce : 8-K 0001193125-25-227562.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-05-15, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q 0001769628-25-000014.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-05-15, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q 0001769628-25-000014.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-08-13, rattaché au trimestre clos le 2025-06-30 ; pièce : 10-Q 0001769628-25-000041.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-10-02, rattaché au trimestre clos le 2025-09-30 ; pièce : 8-K 0001193125-25-227562.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-11-13, rattaché au trimestre clos le 2025-09-30 ; pièce : 10-Q 0001769628-25-000062.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-Q 0001769628-25-000062, 10-K 0001769628-26-000104.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2026-01-02, rattaché au trimestre clos le 2025-12-31 ; pièce : 8-K 0001769628-26-000003.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-K 0001769628-26-000104.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-Q 0001769628-26-000222.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-Q 0001769628-26-000222.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-08-12, rattaché au trimestre clos le 2026-06-30 ; pièce : 10-Q 0001769628-26-000366, 10-Q 0001769628-26-000222.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-08-12, rattaché au trimestre clos le 2026-06-30 ; pièce : 10-Q 0001769628-26-000366.

**AMD**

- F8 (croissance annuelle passée sous zéro) — rendu public le 2023-05-03, rattaché au trimestre clos le 2023-04-01 ; pièce : faits balisés.
- F6 (dépréciation d'investissement) — rendu public le 2026-02-04, rattaché au trimestre clos le 2025-12-27 ; pièce : 10-K 0000002488-26-000018.

**Marvell**

- F4 (amendement ou dérogation de clause financière) — rendu public le 2020-12-08, rattaché au trimestre clos le 2021-01-30 ; pièce : 8-K 0001193125-20-312706.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2023-04-17, rattaché au trimestre clos le 2023-04-29 ; pièce : 8-K 0001193125-23-103639.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2023-05-26, rattaché au trimestre clos le 2023-04-29 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-05-31, rattaché au trimestre clos le 2024-05-04 ; pièce : faits balisés.

États de couverture des cellules de l'annexe F (groupe × trimestre), pour lire ce qui n'a pas été observé :

- F1 : calculée / événement 14 ; calculée / sans événement 177 ; indéterminée 65
- F2 : indéterminée 256
- F3 : partielle / sans événement 256
- F4 : calculée / événement 5 ; partielle / sans événement 251
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
| Flux après financement des contreparties | 22 115 M$ (partiel) | 32 904 M$ (partiel) | 48 587 M$ (partiel) | 21 400 M$ (partiel) |
| Délai de recouvrement (créances) | 53 j | 51 j | 45 j | 60 j |
| Obligations de prestation restantes (RPO) | 2 500 M$ | 2 300 M$ | 2 600 M$ | 3 200 M$ |
| Dette ÷ (résultat opérationnel + dotations) | 0,08 x | 0,06 x | 0,05 x | 0,17 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,02 x | 0,02 x | 0,03 x | 0,03 x |

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
Baux non commencés au 2026-01-25 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (non publié) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (non publié).

Durées d'amortissement publiées (exercice clos le 2026-01-25) : Equipment, Compute Hardware, And Software (borne basse) 2,0 ans ; Equipment, Compute Hardware, And Software (borne haute) 7,0 ans ; Building (valeur unique) 30,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 26 ; clauses financières — sans événement 26 ; items de détresse (8-K) — sans événement 26 ; continuité d'exploitation — sans événement 26 ; dépôt tardif — sans événement 26 ; faiblesse du contrôle interne — sans événement 26.

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
| Flux après financement des contreparties | 24 461 M$ (partiel) | 24 551 M$ (partiel) | 10 116 M$ (partiel) | -5 855 M$ (partiel) |
| Délai de recouvrement (créances) | 51 j | 51 j | 52 j | 53 j |
| Obligations de prestation restantes (RPO) | 157 700 M$ | 242 800 M$ | 467 600 M$ | 519 500 M$ |
| Dette ÷ (résultat opérationnel + dotations) | 0,19 x | 0,32 x | 0,49 x | 0,58 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,12 x | 0,12 x | 0,11 x | 0,12 x |

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
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (non publié) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (non publié).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Corporate And Other Assets (borne basse) 2,0 ans ; Corporate And Other Assets (borne haute) 25,0 ans ; Data Center and Office Buildings (borne basse) 7,0 ans ; Data Center and Office Buildings (borne haute) 40,0 ans ; Servers and Network Equipment (valeur unique) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22.

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
| Flux après financement des contreparties | 430 M$ (partiel) | 14 937 M$ (partiel) | -18 171 M$ (partiel) | -8 821 M$ (partiel) |
| Délai de recouvrement (créances) | 31 j | 29 j | 37 j | 40 j |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Dette ÷ (résultat opérationnel + dotations) | 0,40 x | 0,47 x | 0,78 x | 0,78 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,71 x | 0,70 x | 0,67 x | 0,65 x |

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
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (non publié) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 96 373 M$.

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Building (valeur unique) 40,0 ans ; Computer Equipment (borne basse) 5,0 ans ; Computer Equipment (borne haute) 6,0 ans ; Machinery And Equipment (borne basse) 10,0 ans ; Machinery And Equipment (borne haute) 13,0 ans ; Other Machinery and Equipment (borne basse) 3,0 ans ; Other Machinery and Equipment (borne haute) 10,0 ans ; Technology Equipment (borne basse) 5,0 ans ; Technology Equipment (borne haute) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 8, indéterminée 14.

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
| Flux après financement des contreparties | 11 170 M$ (partiel) | 14 831 M$ (partiel) | 13 229 M$ (partiel) | 1 746 M$ (partiel) |
| Délai de recouvrement (créances) | 31 j | 30 j | 28 j | 33 j |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | 0,58 x | n.d. (terme manquant) | 0,76 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | 0,26 x | n.d. (terme manquant) | n.d. (terme manquant) |

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
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (non publié) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (non publié).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Equipment And Other (borne basse) 1,0 ans ; Equipment And Other (borne haute) 25,0 ans ; Finance Lease, Right-Of-Use Asset (borne basse) 5,0 ans ; Finance Lease, Right-Of-Use Asset (borne haute) 20,0 ans ; Servers and Network Assets Components Stored By Suppliers (borne basse) 5,0 ans ; Servers and Network Assets Components Stored By Suppliers (borne haute) 5,5 ans ; Building (borne basse) 25,0 ans ; Building (borne haute) 30,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22.

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
| Flux après financement des contreparties | 25 663 M$ (partiel) | 5 882 M$ (partiel) | 15 803 M$ (partiel) | 19 639 M$ (partiel) |
| Délai de recouvrement (créances) | 63 j | 64 j | 65 j | 82 j |
| Obligations de prestation restantes (RPO) | 398 000 M$ | 631 000 M$ | 633 000 M$ | 684 000 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

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
Baux non commencés au 2026-06-30 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2026-06-30) : Building And Building Improvements (borne basse) 5,0 ans ; Building And Building Improvements (borne haute) 15,0 ans ; Computer Equipment (borne basse) 2,0 ans ; Computer Equipment (borne haute) 6,0 ans ; Furniture And Fixtures (borne basse) 1,0 ans ; Furniture And Fixtures (borne haute) 10,0 ans ; Leasehold Improvements (borne basse) 3,0 ans ; Leasehold Improvements (borne haute) 15,0 ans ; Software And Software Development Costs (valeur unique) 3,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 24 ; clauses financières — sans événement 24 ; items de détresse (8-K) — sans événement 24 ; continuité d'exploitation — sans événement 24 ; dépôt tardif — sans événement 24 ; faiblesse du contrôle interne — sans événement 24.

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
| Flux après financement des contreparties | -9 967 M$ (partiel) | -11 484 M$ (partiel) | -1 873 M$ (partiel) | -5 396 M$ (partiel) |
| Délai de recouvrement (créances) | 53 j | 56 j | 50 j | 54 j |
| Obligations de prestation restantes (RPO) | 523 300 M$ | 552 600 M$ | 638 000 M$ | 664 000 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 1,00 x | 1,06 x | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |

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
Baux non commencés au 2026-05-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2026-05-31) : Servers and Networking Equipment (valeur unique) 6,0 ans ; Building And Building Improvements (borne basse) 1,0 ans ; Building And Building Improvements (borne haute) 40,0 ans ; Furniture And Fixtures (borne basse) 5,0 ans ; Furniture And Fixtures (borne haute) 15,0 ans ; Machinery And Equipment (borne basse) 1,0 ans ; Machinery And Equipment (borne haute) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 25 ; clauses financières — sans événement 25 ; items de détresse (8-K) — sans événement 25 ; continuité d'exploitation — sans événement 25 ; dépôt tardif — sans événement 25 ; faiblesse du contrôle interne — sans événement 23, indéterminée 2.

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
| Flux après financement des contreparties | -700 M$ (partiel) | -2 501 M$ (partiel) | -4 711 M$ (partiel) | -5 743 M$ (partiel) |
| Délai de recouvrement (créances) | 112 j | 185 j | 92 j | 90 j |
| Obligations de prestation restantes (RPO) | 50 000 M$ | 60 700 M$ | 98 800 M$ | 103 700 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | 8,88 x | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | 3,51 x | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |

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
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Data Center Equipment And Leasehold Improvements (valeur unique) 12,0 ans ; Furniture, Fixtures, and Other Assets (borne basse) 3,0 ans ; Furniture, Fixtures, and Other Assets (borne haute) 5,0 ans ; Software (borne basse) 3,0 ans ; Software (borne haute) 6,0 ans ; Technology Equipment (valeur unique) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — événement 3, sans événement 19 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 6, indéterminée 16 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — événement 6, indéterminée 16.

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

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 1, indéterminée 21 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 1, indéterminée 21.

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
| Flux après financement des contreparties | 1 901 M$ (partiel) | 2 378 M$ (partiel) | 2 566 M$ (partiel) | 1 558 M$ (partiel) |
| Délai de recouvrement (créances) | 61 j | 56 j | 54 j | 57 j |
| Obligations de prestation restantes (RPO) | 279 M$ | 315 M$ | 264 M$ | 222 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |

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
Baux non commencés au 2025-12-27 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2021-12-25) : Equipment (borne basse) 2,0 ans ; Equipment (borne haute) 6,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22.

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
| Flux après financement des contreparties | 7 466 M$ (partiel) | 8 010 M$ (partiel) | 10 262 M$ (partiel) | 13 665 M$ (partiel) |
| Délai de recouvrement (créances) | 36 j | 40 j | 44 j | 42 j |
| Obligations de prestation restantes (RPO) | 33 300 M$ | 45 000 M$ | 164 600 M$ | 179 200 M$ |
| Dette ÷ (résultat opérationnel + dotations) | 2,58 x | 2,33 x | 1,95 x | 1,37 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |

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

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 23 ; clauses financières — sans événement 23 ; items de détresse (8-K) — sans événement 23 ; continuité d'exploitation — sans événement 23 ; dépôt tardif — sans événement 23 ; faiblesse du contrôle interne — sans événement 23.

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
| Flux après financement des contreparties | 509 M$ (partiel) | 259 M$ (partiel) | 483 M$ (partiel) | 479 M$ (partiel) |
| Délai de recouvrement (créances) | 68 j | 90 j | 70 j | 74 j |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |

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

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 26 ; clauses financières — événement 2, sans événement 24 ; items de détresse (8-K) — événement 1, sans événement 25 ; continuité d'exploitation — sans événement 26 ; dépôt tardif — sans événement 26 ; faiblesse du contrôle interne — sans événement 26.

## Circularité, par paire

Une paire réunit un groupe du périmètre et une contrepartie que ses pièces nomment, avec au moins une arête entre eux : client, financé, financeur ou prêteur (une paire seulement financière, comme un prêt bancaire, n'a pas de revenu à rapprocher). Aucune de ces mesures ne prouve une circularité ; la conclusion s'en tient aux valeurs de `relationship_conclusion`, et un numérateur vide se publie indéterminé, à côté des sorties de couverture (E.9).

### AMD → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L2, L5) ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (non traité au premier passage) ; 2022-12-31 : n.d. (non traité au premier passage) ; 2023-12-30 : n.d. (non traité au premier passage) ; 2024-12-28 : n.d. (non traité au premier passage) ; 2025-12-27 : n.d. (non traité au premier passage).
- Contrepartie payable au client : 5 cellules indéterminées (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E4 (engagement) : compatible ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non traité au premier passage.

### AMD → Meta

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète au premier passage ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (non traité au premier passage) ; 2022-12-31 : n.d. (non traité au premier passage) ; 2023-12-30 : n.d. (non traité au premier passage) ; 2024-12-28 : n.d. (non traité au premier passage) ; 2025-12-27 : n.d. (non traité au premier passage).
- Contrepartie payable au client : 5 cellules indéterminées (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E4 (engagement) : compatible ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non traité au premier passage.

### Amazon → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité au premier passage) ; 2022-12-31 : n.d. (non traité au premier passage) ; 2023-12-31 : n.d. (non traité au premier passage) ; 2024-12-31 : n.d. (non traité au premier passage) ; 2025-12-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (4 sur 4).
- Annexe E : E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non traité au premier passage.

### Broadcom → Apple Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (non traité au premier passage) ; 2022-10-30 : n.d. (non traité au premier passage) ; 2023-10-29 : n.d. (non traité au premier passage) ; 2024-11-03 : n.d. (non traité au premier passage) ; 2025-11-02 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Broadcom → BANK OF AMERICA, N.A.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète au premier passage ; 16 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (non traité au premier passage) ; 2022-10-30 : n.d. (non traité au premier passage) ; 2023-10-29 : n.d. (non traité au premier passage) ; 2024-11-03 : n.d. (non traité au premier passage) ; 2025-11-02 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 8).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Broadcom → Silicon Manufacturing Partners Pte. Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète au premier passage ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 28 trimestres ; sensibilité `ever_financed` : actif 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : entre 0 % et 18 % ; 2022-10-30 : entre 0 % et 20 % ; 2023-10-29 : entre 0 % et 22 % ; 2024-11-03 : entre 0 % et 28 % ; 2025-11-02 : entre 0 % et 32 %.
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non traité au premier passage.

### Broadcom → Alphabet

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (non traité au premier passage) ; 2022-10-30 : n.d. (non traité au premier passage) ; 2023-10-29 : n.d. (non traité au premier passage) ; 2024-11-03 : n.d. (non traité au premier passage) ; 2025-11-02 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Broadcom → Anthropic

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (non traité au premier passage) ; 2022-10-30 : n.d. (non traité au premier passage) ; 2023-10-29 : n.d. (non traité au premier passage) ; 2024-11-03 : n.d. (non traité au premier passage) ; 2025-11-02 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Broadcom → Meta

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (non traité au premier passage) ; 2022-10-30 : n.d. (non traité au premier passage) ; 2023-10-29 : n.d. (non traité au premier passage) ; 2024-11-03 : n.d. (non traité au premier passage) ; 2025-11-02 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### CoreWeave → Jane Street Group, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### CoreWeave → MagAI Ventures

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 8 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### CoreWeave → MAIV

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète au premier passage ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, échu 1 trimestre, inconnu 18 trimestres ; sensibilité `ever_financed` : actif 9 trimestres, inconnu 18 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : entre 0 % et 68 %.
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non traité au premier passage.

### CoreWeave → OpenAI

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### CoreWeave → Meta

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### CoreWeave → Microsoft

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### CoreWeave → NVIDIA

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète au premier passage ; 8 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Alphabet → Kitty Hawk Corporation

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité au premier passage) ; 2022-12-31 : n.d. (non traité au premier passage) ; 2023-12-31 : n.d. (non traité au premier passage) ; 2024-12-31 : n.d. (non traité au premier passage) ; 2025-12-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Alphabet → LTA Research & Exploration LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité au premier passage) ; 2022-12-31 : n.d. (non traité au premier passage) ; 2023-12-31 : n.d. (non traité au premier passage) ; 2024-12-31 : n.d. (non traité au premier passage) ; 2025-12-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Marvell → Amazon

- Conclusion : **causalité non établie** ; structure financière seulement ; lien documenté (L2) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 31 trimestres ; sensibilité `ever_financed` : inconnu 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-30 : n.d. (non traité au premier passage) ; 2022-01-29 : n.d. (non traité au premier passage) ; 2023-01-28 : n.d. (non traité au premier passage) ; 2024-02-03 : n.d. (non traité au premier passage) ; 2025-02-01 : n.d. (non traité au premier passage) ; 2026-01-31 : n.d. (non traité au premier passage).
- Contrepartie payable au client : 6 cellules indéterminées (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Marvell → Alphabet

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète au premier passage ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 31 trimestres ; sensibilité `ever_financed` : inconnu 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-30 : n.d. (non traité au premier passage) ; 2022-01-29 : n.d. (non traité au premier passage) ; 2023-01-28 : n.d. (non traité au premier passage) ; 2024-02-03 : n.d. (non traité au premier passage) ; 2025-02-01 : n.d. (non traité au premier passage) ; 2026-01-31 : n.d. (non traité au premier passage).
- Contrepartie payable au client : 6 cellules indéterminées (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Microsoft → OpenAI

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 29 trimestres ; sensibilité `ever_financed` : inconnu 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (non traité au premier passage) ; 2022-06-30 : n.d. (non traité au premier passage) ; 2023-06-30 : n.d. (non traité au premier passage) ; 2024-06-30 : n.d. (non traité au premier passage) ; 2025-06-30 : n.d. (non traité au premier passage) ; 2026-06-30 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### NVIDIA → Goldman Sachs & Co. LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 31 trimestres ; sensibilité `ever_financed` : inconnu 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (non traité au premier passage) ; 2022-01-30 : n.d. (non traité au premier passage) ; 2023-01-29 : n.d. (non traité au premier passage) ; 2024-01-28 : n.d. (non traité au premier passage) ; 2025-01-26 : n.d. (non traité au premier passage) ; 2026-01-25 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### NVIDIA → Wachovia Service Corporation

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 31 trimestres ; sensibilité `ever_financed` : inconnu 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (non traité au premier passage) ; 2022-01-30 : n.d. (non traité au premier passage) ; 2023-01-29 : n.d. (non traité au premier passage) ; 2024-01-28 : n.d. (non traité au premier passage) ; 2025-01-26 : n.d. (non traité au premier passage) ; 2026-01-25 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### NVIDIA → CoreWeave

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 4 trimestres, inconnu 27 trimestres ; sensibilité `ever_financed` : actif 4 trimestres, inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (non traité au premier passage) ; 2022-01-30 : n.d. (non traité au premier passage) ; 2023-01-29 : n.d. (non traité au premier passage) ; 2024-01-28 : n.d. (non traité au premier passage) ; 2025-01-26 : n.d. (non traité au premier passage) ; 2026-01-25 : entre 0 % et 22 %.
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E1 : étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non traité au premier passage.

### NVIDIA → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 31 trimestres ; sensibilité `ever_financed` : inconnu 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (non traité au premier passage) ; 2022-01-30 : n.d. (non traité au premier passage) ; 2023-01-29 : n.d. (non traité au premier passage) ; 2024-01-28 : n.d. (non traité au premier passage) ; 2025-01-26 : n.d. (non traité au premier passage) ; 2026-01-25 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non traité au premier passage.

### Oracle → Ampere Computing Holdings LLC

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète au premier passage ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 4 trimestres, inconnu 26 trimestres ; sensibilité `ever_financed` : actif 4 trimestres, inconnu 26 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non traité au premier passage.

### Oracle → Ampere Computing LLC

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète au premier passage ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 22 trimestres, échu 8 trimestres ; sensibilité `ever_financed` : actif 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2026-05-31 : n.d. (non traité au premier passage).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non traité au premier passage.

### Oracle → Autonomous Medical Devices, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Oracle → Desert Champions LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Oracle → Eau Palm Beach Resort & Spa

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète au premier passage ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Oracle → Ellison Institute, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Oracle → Lanai Resorts, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Oracle → Lawrence Investments, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Oracle → Screening Room Media, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète au premier passage ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, échu 28 trimestres ; sensibilité `ever_financed` : actif 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — non traité au premier passage ; E2 à 10 % : indéterminé — non traité au premier passage ; E2 à 20 % : indéterminé — non traité au premier passage ; E5 : indéterminé — non traité au premier passage.

### Oracle → Sensei AG Holdings, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète au premier passage ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité au premier passage) ; 2022-05-31 : n.d. (non traité au premier passage) ; 2023-05-31 : n.d. (non traité au premier passage) ; 2024-05-31 : n.d. (non traité au premier passage) ; 2025-05-31 : n.d. (non traité au premier passage) ; 2026-05-31 : n.d. (non traité au premier passage).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### SpaceX → Tesla, Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète au premier passage ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité au premier passage) ; 2022-12-31 : n.d. (non traité au premier passage) ; 2023-12-31 : n.d. (non traité au premier passage) ; 2024-12-31 : n.d. (non traité au premier passage) ; 2025-12-31 : n.d. (non traité au premier passage).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non traité au premier passage.

### Sorties de couverture par fournisseur (§3.6)

| Fournisseur | Exercice | Revenu attribué à des clients nommés | Clients anonymes d'au moins 10 % | Résidu | Paires vues seulement côté client |
| --- | --- | ---: | ---: | ---: | ---: |
| NVIDIA | 2026-01-25 | 0,0 % (partiel) (partiel) | 36,0 % [35,0 % ; 37,0 %] | 64,0 % (partiel) | 1 |
| Alphabet | 2025-12-31 | 0,0 % (partiel) (partiel) | 0,0 % [0,0 % ; 0,0 %] | 100,0 % (partiel) | 0 |
| Amazon | 2025-12-31 | 0,0 % (partiel) (partiel) | 0,0 % [0,0 % ; 0,0 %] | 100,0 % (partiel) | 0 |
| Meta | 2025-12-31 | 0,0 % (partiel) (partiel) | 0,0 % [0,0 % ; 0,0 %] | 100,0 % (partiel) | 0 |
| Microsoft | 2026-06-30 | 0,0 % (partiel) (partiel) | 0,0 % [0,0 % ; 0,0 %] | 100,0 % (partiel) | 1 |
| Oracle | 2026-05-31 | 0,0 % (partiel) (partiel) | 0,0 % [0,0 % ; 0,0 %] | 100,0 % (partiel) | 0 |
| CoreWeave | 2025-12-31 | 0,0 % (partiel) (partiel) | 67,0 % [66,5 % ; 67,5 %] | 33,0 % (partiel) | 0 |
| SpaceX | 2025-12-31 | 0,0 % (partiel) (partiel) | 0,0 % [0,0 % ; 0,0 %] | 100,0 % (partiel) | 0 |
| AMD | 2025-12-27 | 0,0 % (partiel) (partiel) | 0,0 % [0,0 % ; 0,0 %] | 100,0 % (partiel) | 0 |
| Broadcom | 2025-11-02 | 0,0 % (partiel) (partiel) | 32,0 % [31,5 % ; 32,5 %] | 68,0 % (partiel) | 1 |
| Marvell | 2026-01-31 | 0,0 % (partiel) (partiel) | 51,0 % [50,0 % ; 52,0 %] | 49,0 % (partiel) | 0 |

Le revenu attribué à des clients nommés est une borne basse : le texte qui entoure les faits de concentration n'est pas lu au premier passage. Un client nommé ailleurs peut être l'un des anonymes (`overlap_possible`).

## Évolution

Premier passage : aucune exécution antérieure à laquelle comparer. Les séries trimestrielles complètes, ruptures de base marquées, sont dans `series.md` ; `delta.md` sera le point d'entrée des exécutions suivantes.

## Ce qui n'a pas pu être établi

Cellules indéterminées en vue `as_known`, par motif : non traité au premier passage 2 019, terme manquant 1 113, non publié 628, concept non résolu 623, annuel seulement 394, historique tronqué 393, client anonyme 58, lecture impossible 32, période antérieure absente 28, frontière de retraitement 13, dénominateur négatif ou nul 10, précondition non remplie 9, date manquante 6, recherche incomplète 5, intervalle à cheval sur le seuil 5, entité non confirmée 1.

