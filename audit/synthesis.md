# Note de synthèse — fragilité financière de la chaîne IA

*Exécution du 2026-10-07 · spec v6.14 · périmètre : premier passage, blocs `lender`, `text`, `discovery`, `paths`, `form_d`, `foreign`, `lender_portfolio`, `montages`, `lender_liabilities`, `nport`, `labs` de §14 · rendu généré depuis les tables `measures`, `controls` et `exclusions`, jamais édité à la main.*

## En tête

- **Critères modifiés depuis leur commit d'origine** `3ff3b988a48a5c904f88f006d263bfa780739d39` (2026-10-07 10:54:38) : `annex_f`. Diff, et ce qui ne change pas :
  - annexe F, ajout de F11 (D-0045) : « juste valeur ÷ coût du portefeuille de prêts d'une BDC en baisse deux trimestres de suite » ; règle {"measure": "bdc_portfolio_fv_to_cost", "condition": "valeur(t) < valeur(t-1) < valeur(t-2)", "consecutive_quarters": 2, "dated_at": "fin du second trimestre"} ; sujets : bdc_vehicles
  - annexe F, ajout de F12 (D-0045) : « part des intérêts capitalisés du portefeuille d'une BDC (borne basse) en hausse deux trimestres de suite » ; règle {"measure": "bdc_portfolio_pik_share", "condition": "borne(t) > borne(t-1) > borne(t-2)", "consecutive_quarters": 2, "dated_at": "fin du second trimestre"} ; sujets : bdc_vehicles
  - annexe F, ajout de F13 (D-0045) : « part des prêts sans accumulation d'intérêts d'une BDC (borne basse) en hausse deux trimestres de suite » ; règle {"measure": "bdc_portfolio_non_accrual_share", "condition": "borne(t) > borne(t-1) > borne(t-2)", "consecutive_quarters": 2, "dated_at": "fin du second trimestre"} ; sujets : bdc_vehicles
  - annexe F, ajout de F14 (D-0047) : « ratio de couverture des titres de créance d'une BDC en baisse deux trimestres de suite » ; règle {"measure": "bdc_liab_asset_coverage", "condition": "valeur(t) < valeur(t-1) < valeur(t-2)", "consecutive_quarters": 2, "dated_at": "fin du second trimestre"} ; sujets : bdc_vehicles
  - annexe F, ajout de F15 (D-0047) : « offre de rachat d'une BDC dont les parts acceptées sont inférieures aux parts apportées (réduction au prorata) » ; règle {"measure": "bdc_tender_acceptance_ratio", "condition": "acceptées < apportées, ou réduction au prorata annoncée", "dated_at": "expiration de l'offre"} ; sujets : bdc_vehicles
  - annexe F, ajout de F16 (D-0047) : « interruption d'un programme régulier d'offres de rachat d'une BDC » ; règle {"condition": "au moins quatre offres déposées à 120 jours au plus d'intervalle, puis aucune offre dans les 120 jours ; ni 8-A12B ni N-54C ou formulaire 15 dans l'intervalle", "dated_at": "dépôt de la dernière offre + 120 jours"} ; sujets : bdc_vehicles
  - annexe F, inchangés : F1, F2, F3, F4, F5, F6, F7, F8, F9, F10 (mêmes observables, mêmes règles)
- **Périmètre couvert : premier passage et blocs `lender`, `text`, `discovery`, `paths`, `form_d`, `foreign`, `lender_portfolio`, `montages`, `lender_liabilities`, `nport`, `labs` de §14**, ouverts sur décision de l'utilisateur (`lender`, `text` le 2026-10-07 ; `discovery` le 2026-10-09 ; `paths`, `form_d` le 2026-10-10 ; `foreign` le 2026-10-10 ; `discovery` le 2026-10-10 ; `lender_portfolio` le 2026-10-10 ; `montages` le 2026-10-10 ; `lender_liabilities` le 2026-10-10 ; `nport` le 2026-10-19 ; `labs` le 2026-10-20, chaque fois après le rendement présenté). Premier passage : faits balisés des trente-deux groupes, notes de parties liées, Item 404, Item 9A, Item 4 des 10-Q, continuité d'exploitation, items 1.01, 1.02, 3.03 et 8.01 des 8-K avec leurs pièces EX-10 et EX-4. Bloc `lender` : portefeuilles publiés des BDC (BDC Data Sets). Bloc `text` : notes d'investissements, de dette, de baux et d'engagements, texte autour des faits de concentration, items 2.01 et 2.03 des 8-K, corps des EX-10 arrêtés à leur en-tête (les EX-4 arrêtés à leur en-tête restent exclus, §14 ne les rouvrant pas) ; tout le catalogue du bloc est lu, aucun bloc ne reste « non traité ». Bloc `discovery` : déposants hors du périmètre qui nomment un groupe (Notes Data Sets, recherche plein texte des EX-10 et des Form D), lus dans l'ordre du classement fixé d'avance (D-0036) ; la passe A est lue jusqu'au rang 2 077 du classement, puis la lecture est arrêtée sur décision de l'utilisateur (D-0041) ; le reste de la file reste « non traité ». Bloc `paths` : cycles orientés de longueur 2 ou 3 entre groupes, tirés des arêtes établies (D-0041). Bloc `form_d` : Form D des entités des groupes et des véhicules tiers nommés d'après un non-déposant (D-0041). Bloc `foreign` : dépôts 20-F, 40-F et 6-K des émetteurs étrangers que la spec nomme ou qui sont déjà dans une paire ou un cycle, cadre comptable relevé, aucune somme entre US GAAP et IFRS (D-0042). 
- **Composition des agrégats entre groupes** (§9.6) : NVIDIA, Alphabet, Amazon, Meta, Microsoft, Oracle, CoreWeave, SpaceX, AMD, Broadcom, Marvell depuis le 2026-10-07; TeraWulf, Cipher, Core Scientific depuis le 2026-10-10; Nebius, IREN depuis le 2026-10-11; Applied Digital depuis le 2026-10-11; Dell, Supermicro depuis le 2026-10-16; Hut 8, Galaxy depuis le 2026-10-16; Akamai, Backblaze, Riot depuis le 2026-10-16; Blue Owl, Apollo, Blackstone depuis le 2026-10-17; Intel, Micron, TSMC depuis le 2026-10-18; ASML, SK hynix depuis le 2026-10-18. Tout agrégat entre groupes (paires, cycles, issues E.6 à E.9) change de composition à la date d'entrée d'un groupe : l'écart avec l'état publié avant tient d'abord à l'ajout, non à un fait économique. Fusions inversées (D-0043) : TeraWulf, réalisée le 2021-12-13 avec IKONICS Corporation comme déclarant légal ; Cipher, réalisée le 2021-08-27 avec Good Works Acquisition Corp. comme déclarant légal ; Core Scientific, réalisée le 2022-01-19 avec Power & Digital Infrastructure Acquisition Corp. comme déclarant légal ; Galaxy, réalisée le 2025-05-13 avec Galaxy Digital Inc. (anciennement Galaxy Digital Pubco Inc.), sans filiale avant la réorganisation comme déclarant légal ; Blue Owl, réalisée le 2021-05-19 avec Altimar Acquisition Corporation (SPAC) comme déclarant légal ; les rapports antérieurs du déclarant légal présentent une autre entité et restent hors du groupe, dont l'historique est tronqué à gauche. Autres ruptures d'historique (D-0048) : Nebius au 2024-07-12 (Yandex N.V. (activités russes cédées)) ; IREN au 2024-07-01 (rapports en IFRS (20-F, 6-K)) ; les dépôts antérieurs restent hors du groupe.
- **Résultat principal (E.7) : discrimination possible au sens de E.7.** 56 % des issues de E.1 et E.2 au point de tête (10 %) sont indéterminées, sur 170 issues ; motifs : intervalle à cheval sur le seuil : 40, précondition non remplie : 28, historique tronqué : 11, recherche incomplète : 10, terme manquant : 5, non traité (unité de la découverte non encore lue, ou bloc de §14 fermé) : 1, caviardé : 1. Issues déterminées : E.1 non étayé 71, E.1 étayé 3. Une issue « non étayé » de E.1 dit qu'aucune pièce de lien (L1 à L5) n'est trouvée sous une recherche complète au sens de E.0, non que le financement soit sans rapport avec les achats. La découverte (§14) n'étant lue que sur les premiers rangs de son classement, les paires dont le client a encore des dépôts à lire restent indéterminées.
- **Contrôles comptables, vue `as_known`** : `mismatch` 1 833, `not_testable` 1 350, `ok` 29 886, `tautological` 1 393 (un contrôle `tautological` n'est jamais compté comme réussi ; un `mismatch` est un résultat publié, avec son code d'explication, dans `controls`).
- **Contrôles comptables, vue `revised`** : `mismatch` 3 011, `not_testable` 1 611, `ok` 29 483, `tautological` 1 393.
  Par contrôle (`mismatch` sur total, vue `as_known`) : C10 192/869, C11 99/835, C12 425/2 026, C13 0/357, C14 85/1 182, C15 133/834, C16 2/496, C1 422/15 283, C2 169/8 969, C3 215/636, C5 0/250, C6 0/1 393, C7 9/529, C8 76/208, C9 6/595.
- **Exclusions principales** : `not_processed` 27 927, `pending_entity` 1 926, `conflicting` 1 382, `out_of_scope` 1 126, `financial_parties_only` 356, `invalid_aggregate` 52, `parse_failed` 32, `submitted_draft` 19, `history_left_censored` 10, `not_public` 2.
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
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-08-01, rattaché au trimestre clos le 2025-06-30 ; pièce : faits balisés.
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
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-03-11, rattaché au trimestre clos le 2026-02-28 ; pièce : 10-Q 0001193125-25-315925, 10-Q 0001193125-26-101045.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-03-11, rattaché au trimestre clos le 2026-02-28 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-06-22, rattaché au trimestre clos le 2026-05-31 ; pièce : 10-Q 0001193125-26-101045, 10-K 0001193125-26-277521.
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
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-Q 0001769628-25-000062, 10-K 0001769628-26-000104.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-11-13, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-Q 0001769628-25-000062, 8-K 0001769628-26-000003.
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
- F4 (amendement ou dérogation de clause financière) — rendu public le 2023-04-17, rattaché au trimestre clos le 2023-04-29 ; pièce : 8-K 0001193125-23-103639, 10-Q 0001835632-23-000029, 10-Q 0001835632-23-000038, 10-Q 0001835632-23-000046, 10-K 0001835632-24-000009, 10-Q 0001835632-24-000063, 10-Q 0001835632-24-000142, 10-Q 0001835632-24-000200, 10-K 0001835632-25-000057.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2023-05-26, rattaché au trimestre clos le 2023-04-29 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-05-31, rattaché au trimestre clos le 2024-05-04 ; pièce : faits balisés.

**TeraWulf**

- F10 (doute sur la continuité d'exploitation) — rendu public le 2022-03-31, rattaché au trimestre clos le 2021-12-31 ; pièce : 10-K 0001104659-22-041168.
- F10 (doute sur la continuité d'exploitation) — rendu public le 2022-05-16, rattaché au trimestre clos le 2022-03-31 ; pièce : 10-Q 0001558370-22-008985.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-05-16, rattaché au trimestre clos le 2022-03-31 ; pièce : faits balisés.
- F10 (doute sur la continuité d'exploitation) — rendu public le 2022-08-15, rattaché au trimestre clos le 2022-06-30 ; pièce : 10-Q 0001083301-22-000023.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-08-15, rattaché au trimestre clos le 2022-06-30 ; pièce : faits balisés.
- F10 (doute sur la continuité d'exploitation) — rendu public le 2022-11-14, rattaché au trimestre clos le 2022-09-30 ; pièce : 10-Q 0001083301-22-000048.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-11-14, rattaché au trimestre clos le 2022-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-03-31, rattaché au trimestre clos le 2022-12-31 ; pièce : 10-K 0001558370-23-005301.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-05-15, rattaché au trimestre clos le 2023-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-08-14, rattaché au trimestre clos le 2023-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-11-13, rattaché au trimestre clos le 2023-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-11-22, rattaché au trimestre clos le 2023-09-30 ; pièce : 10-Q/A 0001083301-23-000060.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-03-20, rattaché au trimestre clos le 2023-12-31 ; pièce : 10-Q/A 0001083301-23-000060, 10-K 0001083301-24-000072.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-03-20, rattaché au trimestre clos le 2023-12-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-05-13, rattaché au trimestre clos le 2024-03-31 ; pièce : 10-Q 0001083301-24-000103.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-05-13, rattaché au trimestre clos le 2024-03-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-08-13, rattaché au trimestre clos le 2024-06-30 ; pièce : 10-Q 0001083301-24-000103, 10-Q 0001083301-24-000124.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-08-13, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-11-12, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-03-03, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-05-09, rattaché au trimestre clos le 2025-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-08-08, rattaché au trimestre clos le 2025-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-11-10, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-02-27, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-08-05, rattaché au trimestre clos le 2026-06-30 ; pièce : faits balisés.

**Cipher**

- F10 (doute sur la continuité d'exploitation) — rendu public le 2021-11-12, rattaché au trimestre clos le 2021-09-30 ; pièce : 10-Q 0000950170-21-004222.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-05-10, rattaché au trimestre clos le 2022-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-08-09, rattaché au trimestre clos le 2022-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-11-14, rattaché au trimestre clos le 2022-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-03-14, rattaché au trimestre clos le 2022-12-31 ; pièce : 10-K 0000950170-23-007793.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-05-09, rattaché au trimestre clos le 2023-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-05-09, rattaché au trimestre clos le 2023-03-31 ; pièce : 10-Q 0000950170-23-019186.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-08-08, rattaché au trimestre clos le 2023-06-30 ; pièce : 10-Q 0000950170-23-039416.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-11-08, rattaché au trimestre clos le 2023-09-30 ; pièce : 10-Q 0000950170-23-060724.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-03-05, rattaché au trimestre clos le 2023-12-31 ; pièce : 10-K 0000950170-24-025442.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-05-07, rattaché au trimestre clos le 2024-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-05-07, rattaché au trimestre clos le 2024-03-31 ; pièce : 10-Q 0000950170-24-054002.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-08-13, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-08-13, rattaché au trimestre clos le 2024-06-30 ; pièce : 10-Q 0000950170-24-095795.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-10-31, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-10-31, rattaché au trimestre clos le 2024-09-30 ; pièce : 10-Q 0001819989-24-000028.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-10-31, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-02-25, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-02-25, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-K 0001819989-25-000005.
- F7 (baisse d'une durée d'amortissement publiée) — rendu public le 2025-02-25, rattaché au trimestre clos le 2024-12-31 ; pièce : durées publiées (faits balisés de deux 10-K successifs).
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-05-06, rattaché au trimestre clos le 2025-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-05-06, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q 0001819989-25-000037.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-08-07, rattaché au trimestre clos le 2025-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-08-07, rattaché au trimestre clos le 2025-06-30 ; pièce : 10-Q 0001819989-25-000081.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-11-03, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-11-03, rattaché au trimestre clos le 2025-09-30 ; pièce : 10-Q 0001819989-25-000112.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-02-24, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-05-05, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2026-05-05, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-08-04, rattaché au trimestre clos le 2026-06-30 ; pièce : faits balisés.

**Core Scientific**

- F2 (flux après financement des contreparties négatif) — rendu public le 2022-08-22, rattaché au trimestre clos le 2021-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-11-22, rattaché au trimestre clos le 2021-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-05-13, rattaché au trimestre clos le 2022-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-05-13, rattaché au trimestre clos le 2022-03-31 ; pièce : 10-Q 0001628280-22-014350.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-08-22, rattaché au trimestre clos le 2022-06-30 ; pièce : 10-Q 0001628280-22-023382.
- F10 (doute sur la continuité d'exploitation) — rendu public le 2022-11-22, rattaché au trimestre clos le 2022-09-30 ; pièce : 10-Q 0001628280-22-030600.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-11-22, rattaché au trimestre clos le 2022-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-11-22, rattaché au trimestre clos le 2022-09-30 ; pièce : 10-Q 0001628280-22-030600.
- F10 (doute sur la continuité d'exploitation) — rendu public le 2023-04-04, rattaché au trimestre clos le 2022-12-31 ; pièce : 10-K 0001628280-23-010454.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-04-04, rattaché au trimestre clos le 2022-12-31 ; pièce : 10-K 0001628280-23-010454.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2023-04-04, rattaché au trimestre clos le 2022-12-31 ; pièce : faits balisés.
- F10 (doute sur la continuité d'exploitation) — rendu public le 2023-05-15, rattaché au trimestre clos le 2023-03-31 ; pièce : 10-Q 0001628280-23-017974.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-05-15, rattaché au trimestre clos le 2023-03-31 ; pièce : 10-Q 0001628280-23-017974.
- F10 (doute sur la continuité d'exploitation) — rendu public le 2023-08-04, rattaché au trimestre clos le 2023-06-30 ; pièce : 10-Q 0001628280-23-017974.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-08-04, rattaché au trimestre clos le 2023-06-30 ; pièce : 10-Q 0001628280-23-027559.
- F10 (doute sur la continuité d'exploitation) — rendu public le 2023-11-06, rattaché au trimestre clos le 2023-09-30 ; pièce : 10-Q 0001628280-23-036849.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-11-06, rattaché au trimestre clos le 2023-09-30 ; pièce : 10-Q 0001628280-23-036849.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-03-13, rattaché au trimestre clos le 2023-12-31 ; pièce : 10-K 0001628280-24-010682.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-05-09, rattaché au trimestre clos le 2024-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-05-09, rattaché au trimestre clos le 2024-03-31 ; pièce : 10-Q 0001628280-24-021848.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-08-07, rattaché au trimestre clos le 2024-06-30 ; pièce : 10-Q 0001628280-24-021848, 10-Q 0001628280-24-035714.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-08-07, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-08-07, rattaché au trimestre clos le 2024-06-30 ; pièce : 10-Q 0001628280-24-035714.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-11-06, rattaché au trimestre clos le 2024-09-30 ; pièce : 10-Q 0001628280-24-035714, 10-Q 0001628280-24-045811.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-11-06, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-11-06, rattaché au trimestre clos le 2024-09-30 ; pièce : 10-Q 0001628280-24-045811.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-11-06, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-02-27, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-Q 0001628280-24-045811, 10-K 0001628280-25-008302.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-02-27, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-03-02, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-K/A 0001628280-26-013232.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-05-07, rattaché au trimestre clos le 2025-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q/A 0001628280-26-013286.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-08-08, rattaché au trimestre clos le 2025-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-06-30 ; pièce : 10-Q/A 0001628280-26-013294.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-10-24, rattaché au trimestre clos le 2025-09-30 ; pièce : 10-Q 0001628280-25-039284, 10-Q 0001628280-25-046272.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-10-24, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-09-30 ; pièce : 10-Q/A 0001628280-26-013301.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-K 0001628280-26-013305.
- F7 (baisse d'une durée d'amortissement publiée) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : durées publiées (faits balisés de deux 10-K successifs).
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-05-06, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-05-06, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-Q 0001628280-26-031396.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-07-28, rattaché au trimestre clos le 2026-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-07-28, rattaché au trimestre clos le 2026-06-30 ; pièce : 10-Q 0001839341-26-000014.

**Nebius**

- F6 (dépréciation d'investissement) — rendu public le 2025-04-30, rattaché au trimestre clos le 2022-12-31 ; pièce : 20-F 0001558370-25-005991.
- F6 (dépréciation d'investissement) — rendu public le 2026-04-30, rattaché au trimestre clos le 2023-12-31 ; pièce : 20-F 0001104659-26-052948.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-04-30, rattaché au trimestre clos le 2024-12-31 ; pièce : 20-F 0001558370-25-005991.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-04-30, rattaché au trimestre clos le 2025-12-31 ; pièce : 20-F 0001104659-26-052948.

**IREN**

- F2 (flux après financement des contreparties négatif) — rendu public le 2025-11-06, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-02-05, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-05-08, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q 0001878848-26-000015, 10-Q 0001878848-26-000026.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-05-08, rattaché au trimestre clos le 2025-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-11-06, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-02-05, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-Q 0001878848-25-000081, 10-Q 0001878848-26-000015.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-02-05, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-Q 0001878848-26-000015, 10-Q 0001878848-26-000026.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.

**Applied Digital**

- F2 (flux après financement des contreparties négatif) — rendu public le 2023-01-10, rattaché au trimestre clos le 2021-11-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-05-13, rattaché au trimestre clos le 2022-02-28 ; pièce : 10-Q 0001628280-22-014389.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-08-29, rattaché au trimestre clos le 2022-05-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-08-29, rattaché au trimestre clos le 2022-05-31 ; pièce : 10-K 0001628280-22-023816.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-10-12, rattaché au trimestre clos le 2022-08-31 ; pièce : 10-Q 0001144879-22-000052.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-01-10, rattaché au trimestre clos le 2022-11-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-01-10, rattaché au trimestre clos le 2022-11-30 ; pièce : 10-Q 0001144879-23-000028.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-04-06, rattaché au trimestre clos le 2023-02-28 ; pièce : 10-Q 0001144879-23-000101.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-08-02, rattaché au trimestre clos le 2023-05-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-08-02, rattaché au trimestre clos le 2023-05-31 ; pièce : 10-K 0001144879-23-000176.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2023-10-10, rattaché au trimestre clos le 2023-08-31 ; pièce : 10-Q 0001898844-23-000006.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-10-10, rattaché au trimestre clos le 2023-08-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-10-10, rattaché au trimestre clos le 2023-08-31 ; pièce : 10-Q 0001898844-23-000006.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-01-16, rattaché au trimestre clos le 2023-11-30 ; pièce : 10-Q 0001144879-24-000010, 10-Q 0001898844-23-000006.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-01-16, rattaché au trimestre clos le 2023-11-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-01-16, rattaché au trimestre clos le 2023-11-30 ; pièce : 10-Q 0001144879-24-000010.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-04-11, rattaché au trimestre clos le 2024-02-29 ; pièce : 10-Q 0001144879-24-000010, 10-Q 0001144879-24-000078.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-04-11, rattaché au trimestre clos le 2024-02-29 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-04-11, rattaché au trimestre clos le 2024-02-29 ; pièce : 10-Q 0001144879-24-000078.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-08-30, rattaché au trimestre clos le 2024-05-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-08-30, rattaché au trimestre clos le 2024-05-31 ; pièce : 10-K 0001144879-24-000216.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-10-09, rattaché au trimestre clos le 2024-08-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-10-09, rattaché au trimestre clos le 2024-08-31 ; pièce : 10-Q 0001144879-24-000253.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-01-14, rattaché au trimestre clos le 2024-11-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-01-14, rattaché au trimestre clos le 2024-11-30 ; pièce : 10-Q 0001144879-25-000006.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-04-14, rattaché au trimestre clos le 2025-02-28 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-04-14, rattaché au trimestre clos le 2025-02-28 ; pièce : 10-Q 0001628280-25-017684.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-07-30, rattaché au trimestre clos le 2025-05-31 ; pièce : 10-K 0001144879-25-000021, 10-Q 0001628280-25-017684.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-07-30, rattaché au trimestre clos le 2025-05-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-07-30, rattaché au trimestre clos le 2025-05-31 ; pièce : 10-K 0001144879-25-000021.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-10-09, rattaché au trimestre clos le 2025-08-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-01-08, rattaché au trimestre clos le 2025-11-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-04-08, rattaché au trimestre clos le 2026-02-28 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-07-29, rattaché au trimestre clos le 2026-05-31 ; pièce : 10-Q 0001144879-26-000030, 10-K 0001144879-26-000048.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-07-29, rattaché au trimestre clos le 2026-05-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2026-10-07, rattaché au trimestre clos le 2026-08-31 ; pièce : 10-Q 0001144879-26-000059.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-10-07, rattaché au trimestre clos le 2026-08-31 ; pièce : faits balisés.

**Dell**

- F2 (flux après financement des contreparties négatif) — rendu public le 2020-06-08, rattaché au trimestre clos le 2020-05-01 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-06-06, rattaché au trimestre clos le 2022-04-29 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-09-01, rattaché au trimestre clos le 2022-07-29 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2022-12-05, rattaché au trimestre clos le 2022-10-28 ; pièce : 10-Q 0001571996-22-000031, 10-Q 0001571996-22-000044.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-12-05, rattaché au trimestre clos le 2022-10-28 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-12-05, rattaché au trimestre clos le 2022-10-28 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-03-25, rattaché au trimestre clos le 2025-01-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-03-25, rattaché au trimestre clos le 2025-01-31 ; pièce : 10-K 0001571996-25-000034.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-06-10, rattaché au trimestre clos le 2025-05-02 ; pièce : 10-Q 0001571996-25-000063.

**Supermicro**

- F5 (faiblesse significative du contrôle interne) — rendu public le 2020-11-06, rattaché au trimestre clos le 2020-09-30 ; pièce : 10-Q 0001375365-20-000074.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2021-02-05, rattaché au trimestre clos le 2020-12-31 ; pièce : 10-Q 0001375365-21-000011.
- F2 (flux après financement des contreparties négatif) — rendu public le 2021-05-07, rattaché au trimestre clos le 2021-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2021-05-07, rattaché au trimestre clos le 2021-03-31 ; pièce : 10-Q 0001375365-21-000034.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2021-06-29, rattaché au trimestre clos le 2021-06-30 ; pièce : 8-K 0001375365-21-000047.
- F2 (flux après financement des contreparties négatif) — rendu public le 2021-11-05, rattaché au trimestre clos le 2021-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-02-04, rattaché au trimestre clos le 2021-12-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-05-06, rattaché au trimestre clos le 2022-03-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2022-03-04, rattaché au trimestre clos le 2022-03-31 ; pièce : 8-K 0001375365-22-000021.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-08-29, rattaché au trimestre clos le 2022-06-30 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2023-05-05, rattaché au trimestre clos le 2023-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-08-28, rattaché au trimestre clos le 2023-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-02-02, rattaché au trimestre clos le 2023-12-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-05-06, rattaché au trimestre clos le 2024-03-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2024-02-22, rattaché au trimestre clos le 2024-03-31 ; pièce : 8-K 0001375365-24-000015.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-02-25, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-02-25, rattaché au trimestre clos le 2024-06-30 ; pièce : 10-K 0001375365-25-000004.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2024-07-22, rattaché au trimestre clos le 2024-09-30 ; pièce : 8-K 0001375365-24-000027, 8-K 0001375365-24-000035.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-02-25, rattaché au trimestre clos le 2024-09-30 ; pièce : 10-Q 0001375365-25-000005.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-02-25, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2024-11-01, rattaché au trimestre clos le 2024-12-31 ; pièce : 8-K 0001375365-24-000037, 8-K 0001375365-24-000042.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-02-25, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-Q 0001375365-25-000006.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-02-21, rattaché au trimestre clos le 2025-03-31 ; pièce : 8-K 0001375365-25-000003, 10-Q 0001375365-25-000006.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-05-12, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q 0001375365-25-000014.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2026-08-31, rattaché au trimestre clos le 2025-06-30 ; pièce : 10-K 0001375365-26-000022.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-08-28, rattaché au trimestre clos le 2025-06-30 ; pièce : 10-K 0001375365-25-000027.
- F7 (baisse d'une durée d'amortissement publiée) — rendu public le 2025-08-28, rattaché au trimestre clos le 2025-06-30 ; pièce : durées publiées (faits balisés de deux 10-K successifs).
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-11-07, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-11-07, rattaché au trimestre clos le 2025-09-30 ; pièce : 10-Q 0001375365-25-000030.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2025-11-07, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-02-06, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-02-06, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-Q 0001375365-26-000007.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-05-11, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-05-11, rattaché au trimestre clos le 2026-03-31 ; pièce : 10-Q 0001375365-26-000014.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2026-06-12, rattaché au trimestre clos le 2026-06-30 ; pièce : 8-K 0001193125-26-269703, 10-K 0001375365-26-000022.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2026-08-31, rattaché au trimestre clos le 2026-06-30 ; pièce : 10-K 0001375365-26-000022.

**Hut 8**

- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-12-19, rattaché au trimestre clos le 2023-09-30 ; pièce : 10-Q 0001104659-23-127101.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-03-03, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-K 0001558370-25-001996.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-05-08, rattaché au trimestre clos le 2025-03-31 ; pièce : 10-Q 0001558370-25-006845.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2025-08-07, rattaché au trimestre clos le 2025-06-30 ; pièce : 10-Q 0001558370-25-010631.

**Galaxy**

- F2 (flux après financement des contreparties négatif) — rendu public le 2025-11-10, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-02-26, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F6 (dépréciation d'investissement) — rendu public le 2026-02-26, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-K 0001859392-26-000016.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-02-26, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F6 (dépréciation d'investissement) — rendu public le 2026-02-26, rattaché au trimestre clos le 2025-12-31 ; pièce : 10-K 0001859392-26-000016.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2026-02-26, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-05-08, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-08-10, rattaché au trimestre clos le 2026-06-30 ; pièce : faits balisés.

**Akamai**

- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-02-28, rattaché au trimestre clos le 2022-12-31 ; pièce : 10-K 0001086222-23-000078.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-05-09, rattaché au trimestre clos le 2023-03-31 ; pièce : 10-Q 0001086222-23-000187.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-08-08, rattaché au trimestre clos le 2023-06-30 ; pièce : 10-Q 0001086222-23-000248.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-11-08, rattaché au trimestre clos le 2023-09-30 ; pièce : 10-Q 0001086222-23-000285.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2026-05-18, rattaché au trimestre clos le 2026-06-30 ; pièce : 8-K 0001193125-26-228949.

**Backblaze**

- F2 (flux après financement des contreparties négatif) — rendu public le 2022-05-10, rattaché au trimestre clos le 2021-03-31 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2022-08-12, rattaché au trimestre clos le 2021-06-30 ; pièce : 10-Q 0001462056-22-000006, 10-Q 0001628280-22-013608.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-08-12, rattaché au trimestre clos le 2021-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2021-12-14, rattaché au trimestre clos le 2021-09-30 ; pièce : 10-Q 0001628280-21-025028.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-03-28, rattaché au trimestre clos le 2021-12-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2023-03-31, rattaché au trimestre clos le 2021-12-31 ; pièce : 10-K 0001462056-23-000119.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-03-28, rattaché au trimestre clos le 2021-12-31 ; pièce : 10-K 0001628280-22-007434.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-05-10, rattaché au trimestre clos le 2022-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-05-10, rattaché au trimestre clos le 2022-03-31 ; pièce : 10-Q 0001628280-22-013608.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-08-12, rattaché au trimestre clos le 2022-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-08-12, rattaché au trimestre clos le 2022-06-30 ; pièce : 10-Q 0001462056-22-000006.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-11-10, rattaché au trimestre clos le 2022-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-11-10, rattaché au trimestre clos le 2022-09-30 ; pièce : 10-Q 0001462056-22-000031.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-03-31, rattaché au trimestre clos le 2022-12-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-03-31, rattaché au trimestre clos le 2022-12-31 ; pièce : 10-K 0001462056-23-000119.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-05-12, rattaché au trimestre clos le 2023-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-05-12, rattaché au trimestre clos le 2023-03-31 ; pièce : 10-Q 0001462056-23-000142.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-08-14, rattaché au trimestre clos le 2023-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-08-14, rattaché au trimestre clos le 2023-06-30 ; pièce : 10-Q 0001462056-23-000190.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-11-14, rattaché au trimestre clos le 2023-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-11-14, rattaché au trimestre clos le 2023-09-30 ; pièce : 10-Q 0001462056-23-000207.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-04-01, rattaché au trimestre clos le 2023-12-31 ; pièce : 10-K 0001462056-24-000033.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-05-08, rattaché au trimestre clos le 2024-03-31 ; pièce : 10-Q 0001462056-24-000041.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-08-08, rattaché au trimestre clos le 2024-06-30 ; pièce : 10-Q 0001628280-24-036136.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2024-11-07, rattaché au trimestre clos le 2024-09-30 ; pièce : 10-Q 0001462056-24-000053.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-08-07, rattaché au trimestre clos le 2025-09-30 ; pièce : 8-K 0001628280-25-038582.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2026-07-02, rattaché au trimestre clos le 2026-06-30 ; pièce : 8-K 0001628280-26-046865, 10-Q 0001628280-26-051818.

**Riot**

- F2 (flux après financement des contreparties négatif) — rendu public le 2021-05-17, rattaché au trimestre clos le 2021-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2021-05-17, rattaché au trimestre clos le 2021-03-31 ; pièce : 10-Q 0001079973-21-000383.
- F2 (flux après financement des contreparties négatif) — rendu public le 2021-08-23, rattaché au trimestre clos le 2021-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2021-08-23, rattaché au trimestre clos le 2021-06-30 ; pièce : 10-Q 0001079973-21-000828.
- F2 (flux après financement des contreparties négatif) — rendu public le 2021-11-15, rattaché au trimestre clos le 2021-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2021-11-15, rattaché au trimestre clos le 2021-09-30 ; pièce : 10-Q 0001079973-21-001156.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-03-16, rattaché au trimestre clos le 2021-12-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-03-16, rattaché au trimestre clos le 2021-12-31 ; pièce : 10-K 0001079973-22-000280, 10-K/A 0001553350-22-000961.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-05-10, rattaché au trimestre clos le 2022-03-31 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-05-10, rattaché au trimestre clos le 2022-03-31 ; pièce : 10-Q 0001079973-22-000557.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-08-15, rattaché au trimestre clos le 2022-06-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-08-15, rattaché au trimestre clos le 2022-06-30 ; pièce : 10-Q 0001553350-22-000687.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2022-11-07, rattaché au trimestre clos le 2022-09-30 ; pièce : 10-Q 0001079973-22-001403, 10-Q 0001553350-22-000687.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-11-07, rattaché au trimestre clos le 2022-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2022-11-07, rattaché au trimestre clos le 2022-09-30 ; pièce : 10-Q 0001079973-22-001403.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-11-07, rattaché au trimestre clos le 2022-09-30 ; pièce : faits balisés.
- F5 (faiblesse significative du contrôle interne) — rendu public le 2023-03-02, rattaché au trimestre clos le 2022-12-31 ; pièce : 10-K 0001558370-23-002704.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-05-10, rattaché au trimestre clos le 2023-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-08-09, rattaché au trimestre clos le 2023-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-11-08, rattaché au trimestre clos le 2023-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-02-23, rattaché au trimestre clos le 2023-12-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-05-01, rattaché au trimestre clos le 2024-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-07-31, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2024-05-01, rattaché au trimestre clos le 2024-06-30 ; pièce : 10-Q 0001558370-24-006400.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-07-31, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-11-04, rattaché au trimestre clos le 2024-09-30 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2024-07-31, rattaché au trimestre clos le 2024-09-30 ; pièce : 10-Q 0001558370-24-010495.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-02-28, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2024-11-04, rattaché au trimestre clos le 2024-12-31 ; pièce : 10-Q 0001558370-24-014179.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-05-01, rattaché au trimestre clos le 2025-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-07-31, rattaché au trimestre clos le 2025-06-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-10-30, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-03-02, rattaché au trimestre clos le 2025-12-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-04-30, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-08-10, rattaché au trimestre clos le 2026-06-30 ; pièce : faits balisés.

**Blue Owl**

- F4 (amendement ou dérogation de clause financière) — rendu public le 2024-07-23, rattaché au trimestre clos le 2024-09-30 ; pièce : 8-K 0001193125-24-182973.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-08-08, rattaché au trimestre clos le 2025-09-30 ; pièce : 8-K 0001193125-25-177104.

**Apollo**

- F2 (flux après financement des contreparties négatif) — rendu public le 2021-05-10, rattaché au trimestre clos le 2021-03-31 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-02-25, rattaché au trimestre clos le 2021-12-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-02-25, rattaché au trimestre clos le 2021-12-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2023-11-07, rattaché au trimestre clos le 2023-09-30 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-08-08, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2025-02-24, rattaché au trimestre clos le 2024-12-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2026-05-07, rattaché au trimestre clos le 2026-03-31 ; pièce : faits balisés.

**Blackstone**

- F2 (flux après financement des contreparties négatif) — rendu public le 2022-02-25, rattaché au trimestre clos le 2021-12-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-05-05, rattaché au trimestre clos le 2022-03-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-02-23, rattaché au trimestre clos le 2023-12-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-08-02, rattaché au trimestre clos le 2024-06-30 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2025-05-02, rattaché au trimestre clos le 2025-03-31 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2025-11-07, rattaché au trimestre clos le 2025-09-30 ; pièce : faits balisés.

**Intel**

- F2 (flux après financement des contreparties négatif) — rendu public le 2022-01-27, rattaché au trimestre clos le 2021-12-25 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-04-29, rattaché au trimestre clos le 2022-04-02 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-07-29, rattaché au trimestre clos le 2022-07-02 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2022-10-28, rattaché au trimestre clos le 2022-10-01 ; pièce : 10-Q 0000050863-22-000030, 10-Q 0000050863-22-000038.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-10-28, rattaché au trimestre clos le 2022-10-01 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-04-28, rattaché au trimestre clos le 2023-04-01 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-07-28, rattaché au trimestre clos le 2023-07-01 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-01-26, rattaché au trimestre clos le 2023-12-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-04-26, rattaché au trimestre clos le 2024-03-30 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-08-02, rattaché au trimestre clos le 2024-06-29 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2024-08-02, rattaché au trimestre clos le 2024-06-29 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-11-01, rattaché au trimestre clos le 2024-09-28 ; pièce : 10-Q 0000050863-24-000124, 10-Q 0000050863-24-000149.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-11-01, rattaché au trimestre clos le 2024-09-28 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-01-31, rattaché au trimestre clos le 2024-12-28 ; pièce : 10-Q 0000050863-24-000149, 10-K 0000050863-25-000009.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-01-31, rattaché au trimestre clos le 2024-12-28 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-04-25, rattaché au trimestre clos le 2025-03-29 ; pièce : 10-Q 0000050863-25-000074.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-04-25, rattaché au trimestre clos le 2025-03-29 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2025-07-24, rattaché au trimestre clos le 2025-06-28 ; pièce : 10-Q 0000050863-25-000074, 10-Q 0000050863-25-000109.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-07-24, rattaché au trimestre clos le 2025-06-28 ; pièce : faits balisés.
- F4 (amendement ou dérogation de clause financière) — rendu public le 2025-08-29, rattaché au trimestre clos le 2025-09-27 ; pièce : 8-K 0000050863-25-000135.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2026-01-23, rattaché au trimestre clos le 2025-12-27 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2026-04-24, rattaché au trimestre clos le 2026-03-28 ; pièce : faits balisés.

**Micron**

- F2 (flux après financement des contreparties négatif) — rendu public le 2021-01-08, rattaché au trimestre clos le 2020-12-03 ; pièce : faits balisés.
- F8 (croissance annuelle passée sous zéro) — rendu public le 2022-10-07, rattaché au trimestre clos le 2022-09-01 ; pièce : faits balisés.
- F2 (flux après financement des contreparties négatif) — rendu public le 2022-12-22, rattaché au trimestre clos le 2022-12-01 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2023-03-29, rattaché au trimestre clos le 2023-03-02 ; pièce : 10-Q 0000723125-22-000072, 10-Q 0000723125-23-000022.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-03-29, rattaché au trimestre clos le 2023-03-02 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2023-06-29, rattaché au trimestre clos le 2023-06-01 ; pièce : 10-Q 0000723125-23-000022, 10-Q 0000723125-23-000041.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-06-29, rattaché au trimestre clos le 2023-06-01 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2023-10-06, rattaché au trimestre clos le 2023-08-31 ; pièce : 10-Q 0000723125-23-000041, 10-K 0000723125-23-000054.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-10-06, rattaché au trimestre clos le 2023-08-31 ; pièce : faits balisés.
- F6 (dépréciation d'investissement) — rendu public le 2023-10-06, rattaché au trimestre clos le 2023-08-31 ; pièce : 10-K 0000723125-23-000054.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2023-12-21, rattaché au trimestre clos le 2023-11-30 ; pièce : 10-Q 0000723125-23-000077.
- F2 (flux après financement des contreparties négatif) — rendu public le 2023-12-21, rattaché au trimestre clos le 2023-11-30 ; pièce : faits balisés.
- F1 (capex décaissé supérieur au CFO deux trimestres de suite) — rendu public le 2024-03-21, rattaché au trimestre clos le 2024-02-29 ; pièce : 10-Q 0000723125-23-000077, 10-Q 0000723125-24-000007.
- F2 (flux après financement des contreparties négatif) — rendu public le 2024-03-21, rattaché au trimestre clos le 2024-02-29 ; pièce : faits balisés.
- F6 (dépréciation d'investissement) — rendu public le 2024-10-04, rattaché au trimestre clos le 2024-08-29 ; pièce : 10-K 0000723125-24-000027.
- F2 (flux après financement des contreparties négatif) — rendu public le 2025-03-21, rattaché au trimestre clos le 2025-02-27 ; pièce : faits balisés.
- F6 (dépréciation d'investissement) — rendu public le 2025-10-03, rattaché au trimestre clos le 2025-08-28 ; pièce : 10-K 0000723125-25-000028.

États de couverture des cellules de l'annexe F (groupe × trimestre ; F11 à F14 : véhicule BDC × date de bilan, D-0045 et D-0047 ; F15 : véhicule × offre de rachat ; F16 : véhicule × offre qui clôt une série), pour lire ce qui n'a pas été observé :

- F1 : calculée / événement 43 ; calculée / sans événement 307 ; indéterminée 377
- F2 : calculée / événement 178 ; calculée / sans événement 324 ; indéterminée 225
- F3 : calculée / sans événement 553 ; partielle / sans événement 174
- F4 : calculée / événement 27 ; calculée / sans événement 490 ; partielle / sans événement 210
- F5 : calculée / événement 97 ; calculée / sans événement 456 ; indéterminée 174
- F6 : calculée / événement 8 ; indéterminée 719
- F7 : calculée / événement 5 ; calculée / sans événement 104 ; indéterminée 618
- F8 : calculée / événement 31 ; calculée / sans événement 411 ; indéterminée 285
- F9 : calculée / sans événement 676 ; indéterminée 51
- F10 : calculée / événement 10 ; calculée / sans événement 543 ; indéterminée 174
- F11 : calculée / événement 500 ; calculée / sans événement 1 009 ; indéterminée 579
- F12 : calculée / événement 222 ; calculée / sans événement 562 ; indéterminée 1 304
- F13 : indéterminée 2 088
- F14 : calculée / événement 182 ; calculée / sans événement 521 ; indéterminée 1 677
- F15 : calculée / événement 84 ; calculée / sans événement 478 ; indéterminée 60
- F16 : calculée / événement 6 ; calculée / sans événement 423 ; indéterminée 44

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
| Flux après financement des contreparties | 21 715 M$ | 27 904 M$ | 46 110 M$ | 21 400 M$ |
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
| Flux après financement des contreparties | 430 M$ | 13 537 M$ | -33 171 M$ | -32 521 M$ |
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

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22 ; actifs nantis — événement 14, sans événement 8.

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

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 25 ; clauses financières — sans événement 13, sans événement 12 ; items de détresse (8-K) — sans événement 25 ; continuité d'exploitation — sans événement 25 ; dépôt tardif — sans événement 25 ; faiblesse du contrôle interne — sans événement 25 ; actifs nantis — sans événement 13, indéterminée 12.

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

### TeraWulf (WULF)

Dernière information balisée utilisée : 2026-08-05.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 86,9 % | 2,4 % | -1,1 % | -6,0 % |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | 14,6 % |
| Capex décaissé ÷ CFO | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -268 M$ | -703 M$ | -541 M$ | -992 M$ |
| Flux disponible après locations-financement | -277 M$ | -703 M$ | -541 M$ | -992 M$ |
| Flux après financement des contreparties | -268 M$ | -703 M$ | -541 M$ | -992 M$ |
| Délai de recouvrement (créances) | 6 j | 3 j | 15 j | 27 j |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 66,1 % | 47,3 % | 93,1 % | 72,3 % |
| Marge opérationnelle | -48,8 % | -240,9 % | -476,7 % | -313,7 % |
| Capex décaissé ÷ revenu | 4,58 x | 17,16 x | 15,38 x | 19,11 x |
| Flux disponible après rémunération en actions | -273 M$ | -710 M$ | -642 M$ | -1 076 M$ |
| Rémunération en actions ÷ CFO | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| Écart CFO − résultat net | 418 M$ | 38 M$ | 410 M$ | 803 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | -7,24 x | -2,32 x | -2,02 x | -2,11 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -59 M$ (partiel) | -64 M$ (partiel) | -222 M$ (partiel) | -185 M$ (partiel) |
| Capitaux propres | 247 M$ | 140 M$ | -79 M$ | 147 M$ |
| Résultats non distribués (déficit si négatif) | -867 M$ | -994 M$ | -1 421 M$ | -2 361 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 5,1 % | -47,4 % | 10,4 % | 25,5 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Gains et pertes sur participations | 23 M$ | 0 $ |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (non publié) | n.d. (non publié) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié 90 M$.
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Equipment (valeur unique) 5,0 ans ; Leasehold Improvements And Electrical Equipment (valeur unique) 25,0 ans ; Miners (valeur unique) 4,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 2, sans événement 20 ; clauses financières — sans événement 19, sans événement 3 ; items de détresse (8-K) — événement 1, sans événement 21 ; continuité d'exploitation — événement 4, sans événement 15, indéterminée 3 ; dépôt tardif — événement 1, sans événement 21 ; faiblesse du contrôle interne — événement 2, sans événement 17, indéterminée 3 ; actifs nantis — événement 2, sans événement 17, indéterminée 3.

### Cipher (CIFR)

Dernière information balisée utilisée : 2026-08-04.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 197,5 % | 41,4 % | -28,8 % | -43,0 % |
| Croissance du revenu (douze mois glissants) | 35,4 % | 48,0 % | 38,0 % | 20,3 % |
| Capex décaissé ÷ CFO | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | 6,05 x | n.d. (dénominateur négatif ou nul) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -256 M$ | -280 M$ | -462 M$ | -654 M$ |
| Flux disponible après locations-financement | -257 M$ | -282 M$ | -464 M$ | -655 M$ |
| Flux après financement des contreparties | -256 M$ | -280 M$ | -462 M$ | -654 M$ |
| Délai de recouvrement (créances) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | 12,99 x | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,27 x | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 62,7 % | 59,4 % | 49,2 % | 39,4 % |
| Marge opérationnelle | -52,5 % | -503,4 % | -328,9 % | -316,2 % |
| Capex décaissé ÷ revenu | 2,88 x | 3,78 x | 15,90 x | 16,52 x |
| Flux disponible après rémunération en actions | -264 M$ | -305 M$ | -490 M$ | -684 M$ |
| Rémunération en actions ÷ CFO | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | 0,30 x | n.d. (dénominateur négatif ou nul) |
| Écart CFO − résultat net | -47 M$ | 680 M$ | 206 M$ | 24 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | -27,41 x | -11,53 x | -5,25 x | -3,31 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -12 M$ (partiel) | -40 M$ (partiel) | -198 M$ (partiel) | -289 M$ (partiel) |
| Capitaux propres | 783 M$ | 806 M$ | 714 M$ | 562 M$ |
| Résultats non distribués (déficit si négatif) | -269 M$ | -1 004 M$ | -1 118 M$ | -1 386 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 18,2 % | -36,9 % | 12,4 % | 9,2 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 0 $ | 0 $ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Infrastructure Assets (borne basse) 10,0 ans ; Infrastructure Assets (borne haute) 20,0 ans ; Miners and Mining Equipment (valeur unique) 3,0 ans ; Leasehold Improvements (borne basse) 5,0 ans ; Leasehold Improvements (borne haute) 20,0 ans ; Property, Plant and Equipment, Other Types (borne basse) 3,0 ans ; Property, Plant and Equipment, Other Types (borne haute) 7,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 1, sans événement 21 ; clauses financières — sans événement 7, sans événement 15 ; items de détresse (8-K) — événement 1, sans événement 21 ; continuité d'exploitation — événement 1, sans événement 19, indéterminée 2 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — événement 12, sans événement 8, indéterminée 2 ; actifs nantis — sans événement 7, indéterminée 15.

### Core Scientific (CORZ)

Dernière information balisée utilisée : 2026-07-28.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | -14,9 % | -16,0 % | 44,9 % | 108,8 % |
| Croissance du revenu (douze mois glissants) | -40,1 % | -37,5 % | -13,7 % | 26,4 % |
| Capex décaissé ÷ CFO | 1,86 x | n.d. (frontière de retraitement) | 1,56 x | n.d. (dénominateur négatif ou nul) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -113 M$ | n.d. (frontière de retraitement) | -139 M$ | -584 M$ |
| Flux disponible après locations-financement | -113 M$ | n.d. (frontière de retraitement) | -140 M$ | -584 M$ |
| Flux après financement des contreparties | -113 M$ | n.d. (frontière de retraitement) | -139 M$ | -584 M$ |
| Délai de recouvrement (créances) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 4,8 % | 26,0 % | 26,1 % | 42,7 % |
| Marge opérationnelle | -70,8 % | n.d. (frontière de retraitement) | -269,4 % | -47,8 % |
| Capex décaissé ÷ revenu | 3,01 x | n.d. (frontière de retraitement) | 3,38 x | 3,44 x |
| Flux disponible après rémunération en actions | -143 M$ | n.d. (frontière de retraitement) | -157 M$ | -602 M$ |
| Rémunération en actions ÷ CFO | 0,23 x | n.d. (frontière de retraitement) | 0,07 x | n.d. (dénominateur négatif ou nul) |
| Écart CFO − résultat net | 278 M$ | n.d. (frontière de retraitement) | 597 M$ | 1 136 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (terme manquant) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -212 M$ (partiel) | -126 M$ (partiel) | -219 M$ (partiel) | -112 M$ (partiel) |
| Capitaux propres | -1 128 M$ | -963 M$ | -1 306 M$ | -2 419 M$ |
| Résultats non distribués (déficit si négatif) | -4 238 M$ | -4 147 M$ | -4 494 M$ | -5 649 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 8,9 % | -74,6 % | -11,1 % | 2,3 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (non publié) | 2 M$ |
| Additions financées par le vendeur | n.d. (non publié) | n.d. (non publié) |
| Additions payées en titres | n.d. (non publié) | n.d. (non publié) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié 8 170 M$.
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Electrical Equipment (valeur unique) 15,0 ans ; Building And Building Improvements (borne basse) 10,0 ans ; Building And Building Improvements (borne haute) 39,0 ans ; Land and Land Improvements (valeur unique) 20,0 ans ; Property, Plant and Equipment, Other Types (borne basse) 5,0 ans ; Property, Plant and Equipment, Other Types (borne haute) 7,0 ans ; Technology Equipment (borne basse) 3,0 ans ; Technology Equipment (borne haute) 10,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 4, sans événement 18 ; clauses financières — sans événement 18, sans événement 4 ; items de détresse (8-K) — événement 3, sans événement 19 ; continuité d'exploitation — événement 5, sans événement 13, indéterminée 4 ; dépôt tardif — événement 4, sans événement 18 ; faiblesse du contrôle interne — événement 18, indéterminée 4 ; actifs nantis — sans événement 18, indéterminée 4.

### Nebius (NBIS)

Dernière information balisée utilisée : 2026-04-30.

| Mesure (trimestre clos le) | 2025-03-31 | 2025-06-30 | 2025-09-30 | 2025-12-31 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Capex décaissé ÷ CFO | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible après locations-financement | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux après financement des contreparties | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Délai de recouvrement (créances) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 21 333 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Marge opérationnelle | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex décaissé ÷ revenu | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible après rémunération en actions | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Rémunération en actions ÷ CFO | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Écart CFO − résultat net | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | 720 M$ (partiel) |
| Capitaux propres | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 4 594 M$ |
| Résultats non distribués (déficit si négatif) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 3 300 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (non publié) | n.d. (non publié) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (non publié) | 19 M$ |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (concept non résolu).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture 168 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 9 760 M$.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 14, indéterminée 6 ; clauses financières — sans événement 2, sans événement 18 ; items de détresse (8-K) — sans événement 14, indéterminée 6 ; continuité d'exploitation — sans événement 2, indéterminée 18 ; dépôt tardif — sans événement 20 ; faiblesse du contrôle interne — événement 2, indéterminée 18 ; actifs nantis — sans événement 2, indéterminée 18.

### IREN (IREN)

Dernière information balisée utilisée : 2026-08-27.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 355,4 % | 59,0 % | -0,0 % | -26,7 % |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | 41,1 % |
| Capex décaissé ÷ CFO | 1,27 x | 7,53 x | 12,60 x | n.d. (frontière de retraitement) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -38 M$ | -468 M$ | -874 M$ | n.d. (frontière de retraitement) |
| Flux disponible après locations-financement | n.d. (terme manquant) | n.d. (terme manquant) | -881 M$ | n.d. (frontière de retraitement) |
| Flux après financement des contreparties | -38 M$ | -468 M$ | -874 M$ | n.d. (frontière de retraitement) |
| Délai de recouvrement (créances) | 9 j | 5 j | 43 j | 14 j |
| Obligations de prestation restantes (RPO) | 195 M$ | 289 M$ | 710 M$ | 5 100 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (dénominateur négatif ou nul) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 66,4 % | 64,4 % | 72,4 % | 75,7 % |
| Marge opérationnelle | -31,8 % | -63,0 % | -161,3 % | -452,1 % |
| Capex décaissé ÷ revenu | 0,75 x | 2,92 x | 6,56 x | 9,68 x |
| Flux disponible après rémunération en actions | -110 M$ | -526 M$ | -905 M$ | n.d. (frontière de retraitement) |
| Rémunération en actions ÷ CFO | 0,51 x | 0,81 x | 0,42 x | n.d. (frontière de retraitement) |
| Écart CFO − résultat net | -242 M$ | 227 M$ | 323 M$ | n.d. (frontière de retraitement) |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (terme manquant) | n.d. (terme manquant) | -10,22 x | -17,67 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 23 M$ (partiel) | 3 M$ (partiel) | 47 M$ (partiel) | -25 M$ (partiel) |
| Capitaux propres | 2 876 M$ | 2 511 M$ | 2 665 M$ | 4 186 M$ |
| Résultats non distribués (déficit si négatif) | -212 M$ | -367 M$ | -615 M$ | -1 299 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 91,1 % | 41,6 % | 52,6 % | -8,4 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2025-06-30 | 2026-06-30 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | 0,03 x |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | 0,08 x |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (non publié) | n.d. (non publié) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-06-30 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2026-06-30 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2026-06-30) : GPU Hardware (valeur unique) 5,0 ans ; HPC Hardware (valeur unique) 5,0 ans ; Mining Hardware (valeur unique) 4,0 ans ; Building (valeur unique) 20,0 ans ; Other Capitalized Property Plant and Equipment (borne basse) 3,0 ans ; Other Capitalized Property Plant and Equipment (borne haute) 10,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 3, sans événement 18, indéterminée 3 ; clauses financières — sans événement 5, sans événement 19 ; items de détresse (8-K) — sans événement 20, indéterminée 4 ; continuité d'exploitation — sans événement 5, indéterminée 19 ; dépôt tardif — sans événement 24 ; faiblesse du contrôle interne — sans événement 5, indéterminée 19 ; actifs nantis — événement 1, sans événement 4, indéterminée 19.

### Applied Digital (APLD)

Dernière information balisée utilisée : 2026-10-07.

| Mesure (trimestre clos le) | 2025-11-30 | 2026-02-28 | 2026-05-31 | 2026-08-31 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 250,1 % | 139,3 % | n.d. (frontière de retraitement) | 322,4 % |
| Croissance du revenu (douze mois glissants) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) | n.d. (frontière de retraitement) |
| Capex décaissé ÷ CFO | n.d. (dénominateur négatif ou nul) | 14,09 x | 9,73 x | 32,46 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -568 M$ | -720 M$ | -1 157 M$ | -2 011 M$ |
| Flux disponible après locations-financement | -608 M$ | -745 M$ | -1 162 M$ | -2 025 M$ |
| Flux après financement des contreparties | -568 M$ | -720 M$ | -1 252 M$ | -2 069 M$ |
| Délai de recouvrement (créances) | 10 j | 15 j | 20 j | 31 j |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 20,6 % | 42,5 % | 37,6 % | 28,1 % |
| Marge opérationnelle | -24,5 % | -67,6 % | -48,2 % | -18,2 % |
| Capex décaissé ÷ revenu | 4,36 x | 6,12 x | 4,98 x | 6,07 x |
| Flux disponible après rémunération en actions | -597 M$ | -770 M$ | -1 282 M$ | -2 077 M$ |
| Rémunération en actions ÷ CFO | n.d. (dénominateur négatif ou nul) | 0,91 x | 0,95 x | 1,04 x |
| Écart CFO − résultat net | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | 248 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | -3,96 x | -31,18 x | -11,14 x | -3,13 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -109 M$ (partiel) | -369 M$ (partiel) | -344 M$ (partiel) | -262 M$ (partiel) |
| Capitaux propres | 1 450 M$ | 1 581 M$ | 1 717 M$ | 1 602 M$ |
| Résultats non distribués (déficit si négatif) | -512 M$ | -583 M$ | -662 M$ | -838 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 32,4 % | 26,8 % | -54,8 % | 13,9 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2025-05-31 | 2026-05-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 114 M$ | 25 M$ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-05-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2026-05-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2026-05-31) : Electric Generation and Transformers (borne basse) 15,0 ans ; Electric Generation and Transformers (borne haute) 30,0 ans ; Electrical Infrastructure (valeur unique) 15,0 ans ; Mechanical Infrastructure (valeur unique) 20,0 ans ; Building Improvements (borne basse) 15,0 ans ; Building Improvements (borne haute) 25,0 ans ; Building (valeur unique) 39,0 ans ; Furniture And Fixtures (borne basse) 5,0 ans ; Furniture And Fixtures (borne haute) 10,0 ans ; Land Improvements (valeur unique) 15,0 ans ; Leasehold Improvements (borne basse) 3,0 ans ; Leasehold Improvements (borne haute) 7,0 ans ; Software And Software Development Costs (borne basse) 3,0 ans ; Software And Software Development Costs (borne haute) 5,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 1, sans événement 24 ; clauses financières — sans événement 19, sans événement 6 ; items de détresse (8-K) — sans événement 25 ; continuité d'exploitation — sans événement 19, indéterminée 6 ; dépôt tardif — événement 1, sans événement 24 ; faiblesse du contrôle interne — événement 14, sans événement 5, indéterminée 6 ; actifs nantis — sans événement 19, indéterminée 6.

### Dell (DELL)

Dernière information balisée utilisée : 2026-09-08.

| Mesure (trimestre clos le) | 2025-10-31 | 2026-01-30 | 2026-05-01 | 2026-07-31 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 10,8 % | 39,5 % | 87,5 % | 57,7 % |
| Croissance du revenu (douze mois glissants) | 10,8 % | 18,8 % | 38,6 % | 49,0 % |
| Capex décaissé ÷ CFO | 0,57 x | 0,15 x | 0,24 x | 0,56 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 503 M$ | 3 953 M$ | 3 118 M$ | 986 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 503 M$ | 3 953 M$ | 3 118 M$ | 986 M$ |
| Délai de recouvrement (créances) | 39 j | 48 j | 54 j | 44 j |
| Obligations de prestation restantes (RPO) | 51 000 M$ | 82 000 M$ | 97 000 M$ | 132 000 M$ |
| Dette ÷ (résultat opérationnel + dotations) | 3,05 x | 2,82 x | 2,28 x | 1,99 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,07 x | 0,07 x | 0,05 x | 0,05 x |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 20,7 % | 20,2 % | 17,8 % | 20,9 % |
| Marge opérationnelle | 7,8 % | 9,3 % | 8,3 % | 11,5 % |
| Capex décaissé ÷ revenu | 0,02 x | 0,02 x | 0,02 x | 0,03 x |
| Flux disponible après rémunération en actions | 338 M$ | 3 764 M$ | 2 929 M$ | 802 M$ |
| Rémunération en actions ÷ CFO | 0,14 x | 0,04 x | 0,05 x | 0,08 x |
| Écart CFO − résultat net | -376 M$ | 2 415 M$ | 643 M$ | -1 908 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 4,84 x | 5,22 x | 6,66 x | 8,92 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -17 773 M$ | -18 942 M$ | -17 548 M$ | -20 276 M$ |
| Capitaux propres | -2 620 M$ | -2 470 M$ | -1 404 M$ | -1 427 M$ |
| Résultats non distribués (déficit si négatif) | 1 420 M$ | 3 325 M$ | 6 343 M$ | 10 065 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -5,2 % | n.d. (dénominateur négatif ou nul) | -6,6 % | -5,0 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2025-01-31 | 2026-01-30 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 1,43 x | 0,69 x |
| Principal dû à 24 mois ÷ trésorerie | 3,19 x | 0,95 x |
| Gains et pertes sur participations | n.d. (non publié) | n.d. (non publié) |
| Dépréciations d'investissements | n.d. (non publié) | n.d. (non publié) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-01-30 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (concept non résolu) ; within_12m 16 800 M$ ; year_2 600 M$ ; year_3 700 M$ ; year_4 300 M$.
Baux non commencés au 2026-01-30 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2026-01-30) : Internal Use Software (valeur unique) 5,0 ans ; Building And Building Improvements (borne basse) 10,0 ans ; Building And Building Improvements (borne haute) 30,0 ans ; Computer Equipment (borne basse) 3,0 ans ; Computer Equipment (borne haute) 5,0 ans ; Leasehold Improvements (valeur unique) 5,0 ans ; Software Development (valeur unique) 2,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 1, sans événement 25 ; clauses financières — sans événement 26 ; items de détresse (8-K) — sans événement 26 ; continuité d'exploitation — sans événement 26 ; dépôt tardif — sans événement 26 ; faiblesse du contrôle interne — événement 2, sans événement 24 ; actifs nantis — sans événement 26.

### Supermicro (SMCI)

Dernière information balisée utilisée : 2026-08-31.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | -15,5 % | 123,4 % | 122,7 % | 93,2 % |
| Croissance du revenu (douze mois glissants) | 11,9 % | 34,8 % | 56,2 % | 77,8 % |
| Capex décaissé ÷ CFO | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | 0,04 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -950 M$ | -45 M$ | -6 696 M$ | 719 M$ |
| Flux disponible après locations-financement | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux après financement des contreparties | -950 M$ | -45 M$ | -6 696 M$ | 714 M$ |
| Délai de recouvrement (créances) | 46 j | 80 j | 74 j | 50 j |
| Obligations de prestation restantes (RPO) | 1 028 M$ | 1 303 M$ | 2 136 M$ | 2 612 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 9,3 % | 6,3 % | 9,9 % | 17,5 % |
| Marge opérationnelle | 3,6 % | 3,7 % | 6,1 % | 13,4 % |
| Capex décaissé ÷ revenu | 0,01 x | 0,00 x | 0,01 x | 0,00 x |
| Flux disponible après rémunération en actions | -1 039 M$ | -136 M$ | -6 822 M$ | 612 M$ |
| Rémunération en actions ÷ CFO | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | 0,14 x |
| Écart CFO − résultat net | -1 086 M$ | -424 M$ | -7 099 M$ | -431 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 13,79 x | 12,00 x | 11,02 x | 14,24 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 6 378 M$ | 7 072 M$ | 14 358 M$ | 15 196 M$ |
| Capitaux propres | 6 523 M$ | 6 992 M$ | 7 575 M$ | 14 479 M$ |
| Résultats non distribués (déficit si négatif) | 3 603 M$ | 4 003 M$ | 4 487 M$ | 5 652 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 3,8 % | 9,1 % | 11,3 % | 658,8 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2025-06-30 | 2026-06-30 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,01 x | 0,27 x |
| Principal dû à 24 mois ÷ trésorerie | 0,02 x | 0,27 x |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (non publié) | n.d. (non publié) |
| Additions en location-financement | n.d. (non publié) | n.d. (non publié) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-06-30 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié 34 200 M$.
Baux non commencés au 2026-06-30 (pont ouverture + nouveaux − commencés = clôture) : ouverture 118 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2026-06-30) : Building Improvements (valeur unique) 20,0 ans ; Building (valeur unique) 39,0 ans ; Furniture And Fixtures (valeur unique) 5,0 ans ; Land Improvements (valeur unique) 15,0 ans ; Machinery And Equipment (borne basse) 3,0 ans ; Machinery And Equipment (borne haute) 7,0 ans ; Software And Software Development Costs (valeur unique) 3,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 2, sans événement 22 ; clauses financières — événement 8, sans événement 16 ; items de détresse (8-K) — événement 4, sans événement 20 ; continuité d'exploitation — sans événement 24 ; dépôt tardif — événement 3, sans événement 21 ; faiblesse du contrôle interne — événement 12, sans événement 12 ; actifs nantis — événement 17, sans événement 7.

### Hut 8 (HUT)

Dernière information balisée utilisée : 2024-11-13.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex décaissé ÷ CFO | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Délai de recouvrement (créances) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,09 x | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Marge opérationnelle | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Capex décaissé ÷ revenu | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux disponible après rémunération en actions | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Rémunération en actions ÷ CFO | 8,21 x | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| Écart CFO − résultat net | -49 M$ | 222 M$ | 193 M$ | 145 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 11,60 x | -10,71 x | -17,10 x | -12,58 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 5 M$ (partiel) | 30 M$ (partiel) | 5 M$ (partiel) | 9 M$ (partiel) |
| Capitaux propres | 1 442 M$ | 1 422 M$ | 1 380 M$ | 1 443 M$ |
| Résultats non distribués (déficit si négatif) | 285 M$ | 5 M$ | -214 M$ | -365 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 26,3 % | -254,9 % | 8,0 % | -0,4 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,76 x | 4,45 x |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | 5,56 x |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 26 M$ | n.d. (non publié) |
| Additions financées par le vendeur | n.d. (non publié) | n.d. (non publié) |
| Additions payées en titres | n.d. (non publié) | n.d. (non publié) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Artificial Intelligence Graphic Processing Units (valeur unique) 5,0 ans ; Data Center Infrastructure (borne basse) 5,0 ans ; Data Center Infrastructure (borne haute) 8,0 ans ; Mining Infrastructure (borne basse) 5,0 ans ; Mining Infrastructure (borne haute) 10,0 ans ; Power plant assets (valeur unique) 10,0 ans ; Land Improvements (valeur unique) 15,0 ans ; Mining Properties and Mineral Rights (borne basse) 2,0 ans ; Mining Properties and Mineral Rights (borne haute) 4,0 ans ; Technology Equipment (valeur unique) 3,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 2, sans événement 22 ; clauses financières — sans événement 12, sans événement 12 ; items de détresse (8-K) — événement 1, sans événement 23 ; continuité d'exploitation — sans événement 12, indéterminée 12 ; dépôt tardif — sans événement 24 ; faiblesse du contrôle interne — événement 4, sans événement 8, indéterminée 12 ; actifs nantis — événement 6, sans événement 6, indéterminée 12.

### Galaxy (GLXY)

Dernière information balisée utilisée : 2026-08-10.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 231,4 % | -34,4 % | -22,6 % | -1,2 % |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (non publié) | 24,3 % | 24,7 % |
| Capex décaissé ÷ CFO | 0,56 x | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | 1,07 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 190 M$ | -1 632 M$ | -421 M$ | -27 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 190 M$ | -1 632 M$ | -421 M$ | -27 M$ |
| Délai de recouvrement (créances) | 0 j | 0 j | 1 j | 1 j |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (concept non résolu) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Marge opérationnelle | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Capex décaissé ÷ revenu | 0,01 x | 0,05 x | 0,03 x | 0,05 x |
| Flux disponible après rémunération en actions | 179 M$ | -1 647 M$ | -440 M$ | -43 M$ |
| Rémunération en actions ÷ CFO | 0,03 x | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | 0,04 x |
| Écart CFO − résultat net | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 72 M$ (partiel) | 34 M$ (partiel) | 103 M$ (partiel) | 86 M$ (partiel) |
| Capitaux propres | 1 762 M$ | 1 956 M$ | 1 812 M$ | 1 823 M$ |
| Résultats non distribués (déficit si négatif) | 541 M$ | 343 M$ | 251 M$ | 233 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -35,1 % | -104,2 % | 205,4 % | -48,1 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | 2 M$ | 19 M$ |
| Dépréciations d'investissements | 7 M$ | 19 M$ |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (concept non résolu).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Corporate Assets Other Than Leasehold Improvements (borne basse) 3,0 ans ; Corporate Assets Other Than Leasehold Improvements (borne haute) 10,0 ans ; Data Center Infrastructure (borne basse) 15,0 ans ; Data Center Infrastructure (borne haute) 25,0 ans ; Mining Equipment (borne basse) 3,0 ans ; Mining Equipment (borne haute) 5,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 5, sans événement 17 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 5, indéterminée 17 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 5, indéterminée 17 ; actifs nantis — sans événement 5, indéterminée 17.

### Akamai (AKAM)

Dernière information balisée utilisée : 2026-08-07.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex décaissé ÷ CFO | 0,26 x | 0,36 x | 0,33 x | 0,44 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 329 M$ | 235 M$ | 211 M$ | 181 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 329 M$ | 235 M$ | 211 M$ | 181 M$ |
| Délai de recouvrement (créances) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | 4 800 M$ | 5 200 M$ | 5 500 M$ | 7 600 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,86 x | 1,23 x | 1,41 x | 1,50 x |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Marge opérationnelle | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Capex décaissé ÷ revenu | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible après rémunération en actions | 214 M$ | 116 M$ | 82 M$ | 35 M$ |
| Rémunération en actions ÷ CFO | 0,26 x | 0,33 x | 0,41 x | 0,45 x |
| Écart CFO − résultat net | 302 M$ | 282 M$ | 206 M$ | 247 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 20,95 x | 18,43 x | 16,33 x | 13,75 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 413 M$ (partiel) | 517 M$ (partiel) | 526 M$ (partiel) | 480 M$ (partiel) |
| Capitaux propres | 4 732 M$ | 4 977 M$ | 4 909 M$ | 4 749 M$ |
| Résultats non distribués (déficit si négatif) | 3 340 M$ | 3 425 M$ | 3 531 M$ | 3 611 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -5,5 % | n.d. (dénominateur négatif ou nul) | -0,7 % | 5,8 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | n.d. (non publié) | 9 M$ |
| Dépréciations d'investissements | n.d. (non publié) | n.d. (non publié) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture 947 M$ (partiel) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 465 M$ (partiel).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Internal-Use Software (borne basse) 2,0 ans ; Internal-Use Software (borne haute) 10,0 ans ; Computer Equipment (borne basse) 3,0 ans ; Computer Equipment (borne haute) 7,0 ans ; Furniture And Fixtures (borne basse) 1,0 ans ; Furniture And Fixtures (borne haute) 7,0 ans ; Leasehold Improvements (borne basse) 1,0 ans ; Leasehold Improvements (borne haute) 15,0 ans ; Office Equipment (borne basse) 3,0 ans ; Office Equipment (borne haute) 5,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — événement 1, sans événement 21 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — événement 4, sans événement 18 ; actifs nantis — sans événement 22.

### Backblaze (BLZE)

Dernière information balisée utilisée : 2026-08-03.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 14,0 % | 11,8 % | 11,7 % | 17,7 % |
| Croissance du revenu (douze mois glissants) | 15,7 % | 14,3 % | 13,3 % | 13,9 % |
| Capex décaissé ÷ CFO | 0,55 x | 0,03 x | 0,19 x | 0,08 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 3 M$ | 9 M$ | 3 M$ | 10 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 3 M$ | 9 M$ | 3 M$ | 10 M$ |
| Délai de recouvrement (créances) | 8 j | 8 j | 10 j | 11 j |
| Obligations de prestation restantes (RPO) | 46 M$ | 66 M$ | 76 M$ | 396 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (dénominateur négatif ou nul) | 12,92 x | 5,22 x | 4,16 x |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 62,1 % | 62,0 % | 60,9 % | 62,8 % |
| Marge opérationnelle | -8,9 % | -12,4 % | -13,8 % | -9,8 % |
| Capex décaissé ÷ revenu | 0,08 x | 0,01 x | 0,02 x | 0,02 x |
| Flux disponible après rémunération en actions | -3 M$ | 3 M$ | -4 M$ | 469 000 $ |
| Rémunération en actions ÷ CFO | 0,95 x | 0,68 x | 2,05 x | 0,88 x |
| Écart CFO − résultat net | 10 M$ | 15 M$ | 10 M$ | 16 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | -9,00 x | -6,11 x | -4,75 x | -3,80 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -27 M$ (partiel) | -29 M$ (partiel) | -27 M$ (partiel) | -25 M$ (partiel) |
| Capitaux propres | 83 M$ | 83 M$ | 85 M$ | 89 M$ |
| Résultats non distribués (déficit si négatif) | -216 M$ | -222 M$ | -228 M$ | -233 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 30,9 % | -58,4 % | 9,7 % | 9,3 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | 17 M$ | 25 M$ |
| Additions financées par le vendeur | n.d. (non publié) | n.d. (non publié) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié) ; within_12m 2 M$ ; year_2 2 M$ ; year_3 800 000 $.
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 18 M$.

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Data Center Equipment (valeur unique) 6,0 ans ; Computer Equipment (borne basse) 3,0 ans ; Computer Equipment (borne haute) 5,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 1, sans événement 21 ; clauses financières — événement 3, sans événement 17, sans événement 2 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 20, indéterminée 2 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — événement 13, sans événement 7, indéterminée 2 ; actifs nantis — événement 15, sans événement 5, indéterminée 2.

### Riot (RIOT)

Dernière information balisée utilisée : 2026-08-10.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 112,6 % | 7,2 % | 3,6 % | 13,9 % |
| Croissance du revenu (douze mois glissants) | 103,6 % | 71,9 % | 42,4 % | 24,5 % |
| Capex décaissé ÷ CFO | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | -140 M$ | -188 M$ | -298 M$ | -151 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | -140 M$ | -188 M$ | -298 M$ | -151 M$ |
| Délai de recouvrement (créances) | 14 j | 18 j | 36 j | 22 j |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Dette ÷ (résultat opérationnel + dotations) | 1,46 x | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,06 x | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Marge opérationnelle | 44,4 % | -447,9 % | -298,9 % | -137,4 % |
| Capex décaissé ÷ revenu | 0,14 x | 0,54 x | 0,69 x | 0,35 x |
| Flux disponible après rémunération en actions | -173 M$ | -221 M$ | -337 M$ | -186 M$ |
| Rémunération en actions ÷ CFO | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) | n.d. (dénominateur négatif ou nul) |
| Écart CFO − résultat net | -218 M$ | 585 M$ | 318 M$ | 147 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | -4 M$ (partiel) | -31 M$ (partiel) | -9 M$ (partiel) | -41 M$ (partiel) |
| Capitaux propres | 3 505 M$ | 2 858 M$ | 2 395 M$ | 2 193 M$ |
| Résultats non distribués (déficit si négatif) | -663 M$ | -1 354 M$ | -1 854 M$ | -2 091 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 40,9 % | -184,9 % | 5,5 % | -9,1 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,00 x | n.d. (terme manquant) |
| Principal dû à 24 mois ÷ trésorerie | 0,00 x | n.d. (terme manquant) |
| Gains et pertes sur participations | n.d. (non publié) | -28 M$ |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (non publié) | 4 M$ |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (non publié) | n.d. (non publié) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : 1 29 M$ ; 2 7 M$ ; total publié n.d. (concept non résolu).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Machinery And Facility Equipment Member (borne basse) 5,0 ans ; Machinery And Facility Equipment Member (borne haute) 10,0 ans ; Miners And Mining Equipment Member (valeur unique) 3,0 ans ; Building Improvements (borne basse) 10,0 ans ; Building Improvements (borne haute) 25,0 ans ; Computer Equipment (valeur unique) 3,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 2, sans événement 20 ; clauses financières — événement 3, sans événement 12, sans événement 7 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — événement 4, sans événement 18 ; faiblesse du contrôle interne — événement 8, sans événement 14 ; actifs nantis — événement 15, indéterminée 7.

### Blue Owl (OWL)

Dernière information balisée utilisée : 2026-07-31.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 21,2 % | 19,7 % | 10,3 % | 7,1 % |
| Croissance du revenu (douze mois glissants) | 27,2 % | 25,0 % | 19,3 % | 14,2 % |
| Capex décaissé ÷ CFO | 0,02 x | 0,06 x | 0,13 x | 0,02 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 422 M$ | 359 M$ | 89 M$ | 453 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 422 M$ | 359 M$ | 89 M$ | 453 M$ |
| Délai de recouvrement (créances) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Marge opérationnelle | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Capex décaissé ÷ revenu | 0,01 x | 0,03 x | 0,02 x | 0,01 x |
| Flux disponible après rémunération en actions | 249 M$ | 197 M$ | -107 M$ | 267 M$ |
| Rémunération en actions ÷ CFO | 0,40 x | 0,42 x | 1,90 x | 0,40 x |
| Écart CFO − résultat net | 427 M$ | 335 M$ | 87 M$ | 450 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capitaux propres | 2 296 M$ | 2 205 M$ | 2 100 M$ | 1 997 M$ |
| Résultats non distribués (déficit si négatif) | -1 508 M$ | -1 609 M$ | -1 744 M$ | -1 888 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -54,8 % | -65,3 % | 6,7 % | 4,9 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié 17 M$.
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture 256 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture 17 M$.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — événement 1, sans événement 21 ; clauses financières — événement 2, sans événement 19, sans événement 1 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 21, indéterminée 1 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 21, indéterminée 1 ; actifs nantis — sans événement 21, indéterminée 1.

### Apollo (APO)

Dernière information balisée utilisée : 2026-08-10.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 26,4 % | 86,7 % | -8,8 % | 63,7 % |
| Croissance du revenu (douze mois glissants) | -13,8 % | 22,7 % | 28,2 % | 41,2 % |
| Capex décaissé ÷ CFO | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible après locations-financement | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux après financement des contreparties | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Délai de recouvrement (créances) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Marge opérationnelle | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Capex décaissé ÷ revenu | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Flux disponible après rémunération en actions | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) | n.d. (terme manquant) |
| Rémunération en actions ÷ CFO | 0,69 x | 0,06 x | 0,14 x | 0,09 x |
| Écart CFO − résultat net | -1 433 M$ | 3 985 M$ | 3 526 M$ | 1 520 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capitaux propres | 23 137 M$ | 23 341 M$ | 19 951 M$ | 21 006 M$ |
| Résultats non distribués (déficit si négatif) | 7 306 M$ | 7 634 M$ | 5 157 M$ | 6 149 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 3,3 % | -89,8 % | 0,3 % | 3,4 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (concept non résolu).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — événement 2, sans événement 20 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22 ; actifs nantis — sans événement 22.

### Blackstone (BX)

Dernière information balisée utilisée : 2026-08-07.

| Mesure (trimestre clos le) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | -15,7 % | 41,4 % | 10,0 % | 35,9 % |
| Croissance du revenu (douze mois glissants) | 15,2 % | 9,2 % | 15,2 % | 17,2 % |
| Capex décaissé ÷ CFO | 0,01 x | 0,02 x | 0,03 x | 0,02 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 1 574 M$ | 1 045 M$ | 958 M$ | 1 909 M$ |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | 1 574 M$ | 1 045 M$ | 958 M$ | 1 909 M$ |
| Délai de recouvrement (créances) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Marge opérationnelle | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Capex décaissé ÷ revenu | 0,01 x | 0,01 x | 0,01 x | 0,01 x |
| Flux disponible après rémunération en actions | 1 270 M$ | 687 M$ | 397 M$ | 1 555 M$ |
| Rémunération en actions ÷ CFO | 0,19 x | 0,34 x | 0,57 x | 0,18 x |
| Écart CFO − résultat net | 973 M$ | 53 M$ | 341 M$ | 712 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capitaux propres | 8 393 M$ | 8 666 M$ | 8 371 M$ | 9 015 M$ |
| Résultats non distribués (déficit si négatif) | 184 M$ | 192 M$ | -324 M$ | -19 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 1,9 % | 40,8 % | 1,8 % | 2,2 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,16 x | 0,27 x |
| Principal dû à 24 mois ÷ trésorerie | 0,48 x | 0,61 x |
| Gains et pertes sur participations | 8 M$ | 9 M$ |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (non publié) | n.d. (non publié) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-31) : Furniture Fittings And Other Assets (borne basse) 3,0 ans ; Furniture Fittings And Other Assets (borne haute) 5,0 ans ; Leasehold Improvements (valeur unique) 7,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — sans événement 22 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22 ; actifs nantis — sans événement 22.

### Intel (INTC)

Dernière information balisée utilisée : 2026-07-24.

| Mesure (trimestre clos le) | 2025-09-27 | 2025-12-27 | 2026-03-28 | 2026-06-27 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 2,8 % | -4,1 % | 7,2 % | 25,4 % |
| Croissance du revenu (douze mois glissants) | -1,5 % | -0,5 % | 1,4 % | 7,5 % |
| Capex décaissé ÷ CFO | 0,95 x | 0,81 x | 3,32 x | 0,36 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 121 M$ | 800 M$ | -2 540 M$ | 4 450 M$ |
| Flux disponible après locations-financement | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux après financement des contreparties | 121 M$ | 800 M$ | -2 540 M$ | 4 450 M$ |
| Délai de recouvrement (créances) | 21 j | 26 j | 27 j | 23 j |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) |
| Dette ÷ (résultat opérationnel + dotations) | 5,90 x | 5,45 x | 7,28 x | 4,45 x |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 38,2 % | 36,1 % | 39,4 % | 40,4 % |
| Marge opérationnelle | 5,0 % | 4,2 % | -23,1 % | 11,1 % |
| Capex décaissé ÷ revenu | 0,18 x | 0,26 x | 0,27 x | 0,16 x |
| Flux disponible après rémunération en actions | -427 M$ | n.d. (frontière de retraitement) | -3 161 M$ | 3 764 M$ |
| Rémunération en actions ÷ CFO | 0,22 x | n.d. (frontière de retraitement) | 0,57 x | 0,10 x |
| Écart CFO − résultat net | -1 517 M$ | 4 879 M$ | 4 824 M$ | 18 039 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | -2,29 x | -2,03 x | -4,78 x | -0,07 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 4 423 M$ (partiel) | 5 575 M$ (partiel) | 9 333 M$ (partiel) | 7 769 M$ (partiel) |
| Capitaux propres | 106 376 M$ | 114 281 M$ | 111 394 M$ | 87 542 M$ |
| Résultats non distribués (déficit si négatif) | 49 602 M$ | 48 983 M$ | 45 179 M$ | 33 842 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | 5,6 % | 638,5 % | 17,0 % | 16,8 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-28 | 2025-12-27 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | 0,18 x |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | 0,44 x |
| Gains et pertes sur participations | n.d. (non publié) | n.d. (non publié) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-27 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié 6 700 M$.
Baux non commencés au 2025-12-27 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-12-27) : Building (borne basse) 10,0 ans ; Building (borne haute) 25,0 ans ; Machinery And Equipment (borne basse) 3,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22 ; clauses financières — événement 1, sans événement 21 ; items de détresse (8-K) — sans événement 22 ; continuité d'exploitation — sans événement 22 ; dépôt tardif — sans événement 22 ; faiblesse du contrôle interne — sans événement 22 ; actifs nantis — sans événement 22.

### Micron (MU)

Dernière information balisée utilisée : 2026-06-25.

| Mesure (trimestre clos le) | 2025-08-28 | 2025-11-27 | 2026-02-26 | 2026-05-28 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | 46,0 % | 56,7 % | 196,3 % | 345,7 % |
| Croissance du revenu (douze mois glissants) | 48,9 % | 45,4 % | 85,5 % | 167,0 % |
| Capex décaissé ÷ CFO | 0,99 x | 0,64 x | 0,54 x | 0,31 x |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | 72 M$ | 3 022 M$ | 5 516 M$ | 17 562 M$ |
| Flux disponible après locations-financement | -33 M$ | 2 899 M$ | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux après financement des contreparties | 72 M$ | 3 022 M$ | 5 516 M$ | 17 562 M$ |
| Délai de recouvrement (créances) | 75 j | 68 j | 66 j | 68 j |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 5 000 M$ |
| Dette ÷ (résultat opérationnel + dotations) | 0,64 x | 0,40 x | n.d. (terme manquant) | n.d. (terme manquant) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | 0,21 x | 0,16 x | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | 44,7 % | 56,0 % | 74,4 % | 84,6 % |
| Marge opérationnelle | 32,3 % | 45,0 % | 67,6 % | 80,4 % |
| Capex décaissé ÷ revenu | 0,50 x | 0,40 x | 0,27 x | 0,19 x |
| Flux disponible après rémunération en actions | -178 M$ | 2 732 M$ | 5 207 M$ | 17 207 M$ |
| Rémunération en actions ÷ CFO | 0,04 x | 0,03 x | 0,03 x | 0,01 x |
| Écart CFO − résultat net | 2 529 M$ | 3 171 M$ | -1 882 M$ | -2 855 M$ |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | 20,48 x | 31,71 x | 79,59 x | 257,58 x |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | 17 594 M$ (partiel) | 18 389 M$ (partiel) | 25 581 M$ (partiel) | 39 592 M$ (partiel) |
| Capitaux propres | 54 165 M$ | 58 806 M$ | 72 459 M$ | 100 724 M$ |
| Résultats non distribués (déficit si négatif) | 48 583 M$ | 53 344 M$ | 66 824 M$ | 94 682 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | -85,7 % | 1,4 % | 1,7 % | 1,8 % |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2025-08-28 | 2026-08-27 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | 0,00 x | n.d. (terme manquant) |
| Principal dû à 24 mois ÷ trésorerie | 0,00 x | n.d. (terme manquant) |
| Gains et pertes sur participations | n.d. (non publié) | n.d. (non publié) |
| Dépréciations d'investissements | 10 M$ | n.d. (non publié) |
| Additions en location-financement | 1 298 M$ | n.d. (non publié) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2026-08-27 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (non publié).
Baux non commencés au 2026-08-27 (pont ouverture + nouveaux − commencés = clôture) : ouverture 1 160 M$ ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Durées d'amortissement publiées (exercice clos le 2025-08-28) : Building And Building Improvements (borne basse) 10,0 ans ; Building And Building Improvements (borne haute) 30,0 ans ; Equipment (valeur unique) 7,0 ans ; Other Machinery and Equipment (borne haute) 7,0 ans ; Software And Software Development Costs (borne basse) 3,0 ans ; Software And Software Development Costs (borne haute) 5,0 ans.

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 23 ; clauses financières — sans événement 23 ; items de détresse (8-K) — sans événement 23 ; continuité d'exploitation — sans événement 23 ; dépôt tardif — sans événement 23 ; faiblesse du contrôle interne — sans événement 23 ; actifs nantis — sans événement 23.

### TSMC (TSM)

Dernière information balisée utilisée : n.d..

| Mesure (trimestre clos le) | 2025-03-31 | 2025-06-30 | 2025-09-30 | 2025-12-31 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Capex décaissé ÷ CFO | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible après locations-financement | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux après financement des contreparties | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Délai de recouvrement (créances) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Marge opérationnelle | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex décaissé ÷ revenu | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible après rémunération en actions | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Rémunération en actions ÷ CFO | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Écart CFO − résultat net | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | 514 575 M$ |
| Capitaux propres | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 170 706 M$ |
| Résultats non distribués (déficit si négatif) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 160 629 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (concept non résolu).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — indéterminée 20 ; clauses financières — sans événement 5, sans événement 15 ; items de détresse (8-K) — indéterminée 20 ; continuité d'exploitation — sans événement 5, indéterminée 15 ; dépôt tardif — sans événement 20 ; faiblesse du contrôle interne — sans événement 5, indéterminée 15 ; actifs nantis — sans événement 5, indéterminée 15.

### ASML (ASML)

Dernière information balisée utilisée : 2026-02-25.

| Mesure (trimestre clos le) | 2025-03-31 | 2025-06-30 | 2025-09-30 | 2025-12-31 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Croissance du revenu (douze mois glissants) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Capex décaissé ÷ CFO | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible après locations-financement | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux après financement des contreparties | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Délai de recouvrement (créances) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Obligations de prestation restantes (RPO) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 46 500 M$ |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Marge opérationnelle | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capex décaissé ÷ revenu | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible après rémunération en actions | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Rémunération en actions ÷ CFO | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Écart CFO − résultat net | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | -5 076 M$ |
| Capitaux propres | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 19 612 M$ |
| Résultats non distribués (déficit si négatif) | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 17 587 M$ |
| Variation du nombre moyen dilué d'actions (sur un an) | n.d. (non publié) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| En-cours ÷ immobilisations brutes | n.d. (non publié) | n.d. (non publié) | n.d. (non publié) | 13,8 % |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (terme manquant) | n.d. (terme manquant) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : 0 13 M$ ; total publié n.d. (concept non résolu).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — indéterminée 20 ; clauses financières — sans événement 5, sans événement 15 ; items de détresse (8-K) — indéterminée 20 ; continuité d'exploitation — sans événement 5, indéterminée 15 ; dépôt tardif — sans événement 20 ; faiblesse du contrôle interne — sans événement 5, indéterminée 15 ; actifs nantis — sans événement 5, indéterminée 15.

### SK hynix (SKHY)

Dernière information balisée utilisée : n.d..

| Mesure (trimestre clos le) | 2025-12-31 | 2026-03-31 | 2026-06-30 | 2026-09-30 |
| --- | ---: | ---: | ---: | ---: |
| Croissance du revenu (glissement annuel) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Croissance du revenu (douze mois glissants) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Capex décaissé ÷ CFO | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Capex ÷ CFO, additions non monétaires comprises | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Flux disponible (CFO − capex) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux disponible après locations-financement | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux après financement des contreparties | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Délai de recouvrement (créances) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Obligations de prestation restantes (RPO) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dette ÷ (résultat opérationnel + dotations) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Passifs locatifs ÷ (résultat opérationnel + dotations) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| *Rang 2 : rentabilité, fonds de roulement, capitaux propres* |  |  |  |  |
| Marge brute | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Marge opérationnelle | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Capex décaissé ÷ revenu | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Flux disponible après rémunération en actions | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Rémunération en actions ÷ CFO | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Écart CFO − résultat net | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Résultat opérationnel ÷ charge d'intérêts (12 mois) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Fonds de roulement (créances + stocks − fournisseurs − passifs de contrat) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) |
| Capitaux propres | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Résultats non distribués (déficit si négatif) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Variation du nombre moyen dilué d'actions (sur un an) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |
| En-cours ÷ immobilisations brutes | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) | n.d. (concept non résolu) |

| Mesure (exercice clos le) | 2024-12-31 | 2025-12-31 |
| --- | ---: | ---: |
| Principal dû à 12 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Principal dû à 24 mois ÷ trésorerie | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Gains et pertes sur participations | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Dépréciations d'investissements | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions en location-financement | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions financées par le vendeur | n.d. (concept non résolu) | n.d. (concept non résolu) |
| Additions payées en titres | n.d. (concept non résolu) | n.d. (concept non résolu) |

Obligations d'achat publiées au 2025-12-31 (flux non actualisés, tranches telles que publiées, aucun total ajouté par le modèle) : total publié n.d. (concept non résolu).
Baux non commencés au 2025-12-31 (pont ouverture + nouveaux − commencés = clôture) : ouverture n.d. (concept non résolu) ; nouveaux n.d. (non publié) ; commencés n.d. (non publié) ; clôture n.d. (concept non résolu).

Signaux sur la fenêtre (trimestres) : auditeur ou correction d'erreur — sans événement 22, indéterminée 1 ; clauses financières — sans événement 23 ; items de détresse (8-K) — sans événement 22, indéterminée 1 ; continuité d'exploitation — indéterminée 23 ; dépôt tardif — sans événement 23 ; faiblesse du contrôle interne — indéterminée 23 ; actifs nantis — événement 2, indéterminée 21.

## Circularité, par paire

Une paire réunit un groupe du périmètre et une contrepartie que ses pièces nomment, avec au moins une arête entre eux : client, financé, financeur ou prêteur (une paire seulement financière, comme un prêt bancaire, n'a pas de revenu à rapprocher). Aucune de ces mesures ne prouve une circularité ; la conclusion s'en tient aux valeurs de `relationship_conclusion`, et un numérateur vide se publie indéterminé, à côté des sorties de couverture (E.9).

### Akamai → Anthropic

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète (une clause de la paire est caviardée) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (caviardé) ; 2022-12-31 : n.d. (caviardé) ; 2023-12-31 : n.d. (caviardé) ; 2024-12-31 : n.d. (caviardé) ; 2025-12-31 : n.d. (caviardé).
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E4 (engagement) : compatible ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### AMD → Anthropic

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### AMD → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L2, L5) ; 11 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (caviardé) ; 2022-12-31 : n.d. (caviardé) ; 2023-12-30 : n.d. (caviardé) ; 2024-12-28 : n.d. (caviardé) ; 2025-12-27 : n.d. (caviardé).
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E4 (engagement) : compatible ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### AMD → Meta

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L2) ; 7 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 33 % (1 sur 3).
- Annexe E : E4 (engagement) : compatible ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### AMD → Microsoft

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Amazon → 1Life Healthcare Inc

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Amazon → AFFIRM HOLDINGS, INC.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Amazon → Apple Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Amazon → DISH NETWORK CORP

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Amazon → RIVIAN AUTOMOTIVE, INC. / DE

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 13 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### Amazon → SNAP INC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Amazon → Anthropic

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L2) ; 64 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 12 trimestres, jamais documenté 15 trimestres ; sensibilité `ever_financed` : actif 12 trimestres, jamais documenté 15 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 6).
- Annexe E : E1 : étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Amazon → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 21 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, inconnu 25 trimestres ; sensibilité `ever_financed` : actif 2 trimestres, inconnu 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (caviardé) ; 2022-12-31 : n.d. (caviardé) ; 2023-12-31 : n.d. (caviardé) ; 2024-12-31 : n.d. (caviardé) ; 2025-12-31 : n.d. (caviardé).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 60 % (3 sur 5).
- Annexe E : E1 : étayé ; E2 à 5 % : indéterminé — caviardé ; E2 à 10 % : indéterminé — caviardé ; E2 à 20 % : indéterminé — caviardé ; E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Amazon → Meta

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → AI Bridge Funding LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 20 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 10 trimestres, jamais documenté 20 trimestres ; sensibilité `ever_financed` : actif 10 trimestres, jamais documenté 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (terme manquant) ; 2025-05-31 : entre 0 % et 94 % ; 2026-05-31 : entre 0 % et 60 %.
- Dépendance du carnet (RPO) : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Applied Digital → B. RILEY COMMERCIAL CAPITAL, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 21 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → B. Riley Financial, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → Base Electron Corp.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, jamais documenté 28 trimestres ; sensibilité `ever_financed` : actif 2 trimestres, jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : entre 0 % et 60 %.
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Applied Digital → Base Electron, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 3 trimestres, jamais documenté 27 trimestres ; sensibilité `ever_financed` : actif 3 trimestres, jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : entre 0 % et 60 %.
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Applied Digital → CIM APLD LENDER HOLDINGS, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 15 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 33 % (1 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → Ekso Bionics Holdings, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (recherche incomplète) ; 2022-05-31 : n.d. (recherche incomplète) ; 2023-05-31 : n.d. (recherche incomplète) ; 2024-05-31 : n.d. (recherche incomplète) ; 2025-05-31 : n.d. (recherche incomplète) ; 2026-05-31 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → Global Operating Infrastructure LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → GMR Limited

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 7 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → Macquarie Equipment Capital, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 19 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 33 % (2 sur 6).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → MIP HPC HOLDINGS, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 20 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → MIP VI DC REIT AIV, L.P.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → MIP VI HPC HOLDINGS, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → MIP VI REIT AIV, L.P.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → CoreWeave

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 18 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Contrepartie payable au client : 6 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 44 % (4 sur 9).
- Annexe E : E5 : indéterminé — non publié.

### Applied Digital → Oracle

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Apollo → AMAPS 1, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 4 trimestres, jamais documenté 23 trimestres ; sensibilité `ever_financed` : actif 4 trimestres, jamais documenté 23 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → AMAPS 2, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 3 trimestres, jamais documenté 24 trimestres ; sensibilité `ever_financed` : actif 3 trimestres, jamais documenté 24 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → AMAPS 3, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, jamais documenté 25 trimestres ; sensibilité `ever_financed` : actif 2 trimestres, jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E5 : indéterminé — non publié.

### Apollo → AMAPS 4, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 1 trimestre, jamais documenté 26 trimestres ; sensibilité `ever_financed` : actif 1 trimestre, jamais documenté 26 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E5 : indéterminé — non publié.

### Apollo → AMAPS 5, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 1 trimestre, jamais documenté 26 trimestres ; sensibilité `ever_financed` : actif 1 trimestre, jamais documenté 26 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E5 : indéterminé — non publié.

### Apollo → AP Alkaios (Luxembourg) S.à.r.l.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 3 trimestres, jamais documenté 24 trimestres ; sensibilité `ever_financed` : actif 3 trimestres, jamais documenté 24 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → AP Aristotle Holdings LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 18 trimestres, jamais documenté 9 trimestres ; sensibilité `ever_financed` : actif 18 trimestres, jamais documenté 9 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → AP Grange Holdings, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 9 trimestres, jamais documenté 18 trimestres ; sensibilité `ever_financed` : actif 9 trimestres, jamais documenté 18 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → AP Tundra Holdings LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 18 trimestres, jamais documenté 9 trimestres ; sensibilité `ever_financed` : actif 18 trimestres, jamais documenté 9 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Apollo Rose II (B), L.P.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 17 trimestres, jamais documenté 10 trimestres ; sensibilité `ever_financed` : actif 17 trimestres, jamais documenté 10 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → AT&T Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 13 trimestres, inconnu 14 trimestres ; sensibilité `ever_financed` : actif 13 trimestres, inconnu 14 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Athene Holding Ltd.

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 34 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, échu 18 trimestres, inconnu 1 trimestre ; sensibilité `ever_financed` : actif 26 trimestres, inconnu 1 trimestre.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-31 : n.d. (recherche incomplète) ; 2024-12-31 : n.d. (recherche incomplète) ; 2025-12-31 : n.d. (recherche incomplète).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Atlas Securitized Products Holdings L.P.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 46 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 14 trimestres, jamais documenté 13 trimestres ; sensibilité `ever_financed` : actif 14 trimestres, jamais documenté 13 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Bank of America, N.A.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 17 trimestres, jamais documenté 10 trimestres ; sensibilité `ever_financed` : actif 17 trimestres, jamais documenté 10 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Catalina Holdings (Bermuda) Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 30 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 6 trimestres, jamais documenté 21 trimestres ; sensibilité `ever_financed` : actif 6 trimestres, jamais documenté 21 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Fox Hedge L.P.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 8 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, jamais documenté 19 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, jamais documenté 19 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → LeasePlan USA, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 14 trimestres, jamais documenté 13 trimestres ; sensibilité `ever_financed` : actif 14 trimestres, jamais documenté 13 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → MORGAN STANLEY

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 17 trimestres, inconnu 10 trimestres ; sensibilité `ever_financed` : actif 17 trimestres, inconnu 10 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → PK AirFinance

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 17 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 18 trimestres, jamais documenté 9 trimestres ; sensibilité `ever_financed` : actif 18 trimestres, jamais documenté 9 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Skylign Aviation Holdings, LP

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 11 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 7 trimestres, jamais documenté 20 trimestres ; sensibilité `ever_financed` : actif 7 trimestres, jamais documenté 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → SVF II Finco Cayman L.P.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, jamais documenté 25 trimestres ; sensibilité `ever_financed` : actif 2 trimestres, jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E5 : indéterminé — non publié.

### Apollo → VA Capital Company LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 24 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 22 trimestres, jamais documenté 5 trimestres ; sensibilité `ever_financed` : actif 22 trimestres, jamais documenté 5 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Venerable Holdings, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 22 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 18 trimestres, jamais documenté 9 trimestres ; sensibilité `ever_financed` : actif 18 trimestres, jamais documenté 9 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Apollo → Venerable Insurance and Annuity Company

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 20 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Apollo → Wheels Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 29 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 18 trimestres, jamais documenté 9 trimestres ; sensibilité `ever_financed` : actif 18 trimestres, jamais documenté 9 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### ASML → Carl Zeiss SMT GmbH

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 134 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 24 trimestres, échu 1 trimestre ; sensibilité `ever_financed` : actif 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 67 % ; 2022-12-31 : entre 0 % et 56 % ; 2023-12-31 : entre 0 % et 54 % ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 25).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### ASML → Carl Zeiss SMT Holding GmbH & Co. KG

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 101 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 25 trimestres ; sensibilité `ever_financed` : actif 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 67 % ; 2022-12-31 : entre 0 % et 56 % ; 2023-12-31 : entre 0 % et 54 % ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 7).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### ASML → Mistral AI

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, jamais documenté 23 trimestres ; sensibilité `ever_financed` : actif 2 trimestres, jamais documenté 23 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### ASML → TSMC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 25 trimestres ; sensibilité `ever_financed` : jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Broadcom → Apple Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (précondition non remplie) ; 2022-10-30 : n.d. (précondition non remplie) ; 2023-10-29 : n.d. (précondition non remplie) ; 2024-11-03 : n.d. (précondition non remplie) ; 2025-11-02 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Broadcom → Silicon Manufacturing Partners Pte. Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 28 trimestres ; sensibilité `ever_financed` : actif 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : entre 0 % et 18 % ; 2022-10-30 : entre 0 % et 20 % ; 2023-10-29 : entre 0 % et 22 % ; 2024-11-03 : entre 0 % et 28 % ; 2025-11-02 : entre 0 % et 32 %.
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Broadcom → WarehouseCo Intermediate Holdings LP

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (précondition non remplie) ; 2022-10-30 : n.d. (précondition non remplie) ; 2023-10-29 : n.d. (précondition non remplie) ; 2024-11-03 : n.d. (précondition non remplie) ; 2025-11-02 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Broadcom → Dell

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-10-31 : n.d. (précondition non remplie) ; 2022-10-30 : n.d. (précondition non remplie) ; 2023-10-29 : n.d. (précondition non remplie) ; 2024-11-03 : n.d. (précondition non remplie) ; 2025-11-02 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Broadcom → Alphabet

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
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

### Backblaze → AFCO Premium Credit LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 3 trimestres, échu 7 trimestres, jamais documenté 17 trimestres ; sensibilité `ever_financed` : actif 10 trimestres, jamais documenté 17 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : n.d. (précondition non remplie).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Backblaze → City National Bank

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 28 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 14 trimestres, jamais documenté 13 trimestres ; sensibilité `ever_financed` : actif 14 trimestres, jamais documenté 13 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (terme manquant) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Backblaze → CoreWeave

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 1 trimestre, jamais documenté 26 trimestres ; sensibilité `ever_financed` : actif 1 trimestre, jamais documenté 26 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 25 % (1 sur 4).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E4 (engagement) : compatible ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Blackstone → American International Group, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 19 trimestres, inconnu 8 trimestres ; sensibilité `ever_financed` : actif 19 trimestres, inconnu 8 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Blackstone → Corebridge Financial, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 16 trimestres, inconnu 11 trimestres ; sensibilité `ever_financed` : actif 16 trimestres, inconnu 11 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 8 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Blackstone → Pátria Investimentos Ltda

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 17 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 27 trimestres ; sensibilité `ever_financed` : actif 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Blackstone → Pátria Investments Limited

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 17 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 27 trimestres ; sensibilité `ever_financed` : actif 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Cipher → Amazon

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Cipher → Fluidstack Ltd.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Cipher → Fluidstack USA II Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Core Scientific → BITMAIN TECHNOLOGIES DELAWARE LIMITED

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Core Scientific → Sphere 3D Corp.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Core Scientific → CoreWeave

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → Jane Street Group, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → MagAI Ventures

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 17 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → MAIV

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, échu 1 trimestre, inconnu 18 trimestres ; sensibilité `ever_financed` : actif 9 trimestres, inconnu 18 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : entre 0 % et 68 %.
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### CoreWeave → Anthropic

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 25 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 6 trimestres, inconnu 21 trimestres ; sensibilité `ever_financed` : actif 6 trimestres, inconnu 21 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : entre 0 % et 68 %.
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 20 % (1 sur 5).
- Annexe E : E1 : étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### CoreWeave → Meta

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → Microsoft

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### CoreWeave → NVIDIA

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### Dell → Broadcom

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-29 : n.d. (précondition non remplie) ; 2022-01-28 : n.d. (précondition non remplie) ; 2023-02-03 : n.d. (précondition non remplie) ; 2024-02-02 : n.d. (précondition non remplie) ; 2025-01-31 : n.d. (précondition non remplie) ; 2026-01-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Dell → BlackRock, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 31 trimestres ; sensibilité `ever_financed` : inconnu 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-29 : n.d. (recherche incomplète) ; 2022-01-28 : n.d. (recherche incomplète) ; 2023-02-03 : n.d. (recherche incomplète) ; 2024-02-02 : n.d. (recherche incomplète) ; 2025-01-31 : n.d. (recherche incomplète) ; 2026-01-30 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Dell → DFO Management LLC

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-29 : n.d. (précondition non remplie) ; 2022-01-28 : n.d. (précondition non remplie) ; 2023-02-03 : n.d. (précondition non remplie) ; 2024-02-02 : n.d. (précondition non remplie) ; 2025-01-31 : n.d. (précondition non remplie) ; 2026-01-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Dell → GIC Private Limited

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-29 : n.d. (précondition non remplie) ; 2022-01-28 : n.d. (précondition non remplie) ; 2023-02-03 : n.d. (précondition non remplie) ; 2024-02-02 : n.d. (précondition non remplie) ; 2025-01-31 : n.d. (précondition non remplie) ; 2026-01-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Dell → Temasek Holdings (Private) Limited

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-29 : n.d. (précondition non remplie) ; 2022-01-28 : n.d. (précondition non remplie) ; 2023-02-03 : n.d. (précondition non remplie) ; 2024-02-02 : n.d. (précondition non remplie) ; 2025-01-31 : n.d. (précondition non remplie) ; 2026-01-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Dell → VMware, Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 144 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 31 trimestres ; sensibilité `ever_financed` : inconnu 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-29 : n.d. (recherche incomplète) ; 2022-01-28 : n.d. (recherche incomplète) ; 2023-02-03 : n.d. (recherche incomplète) ; 2024-02-02 : n.d. (recherche incomplète) ; 2025-01-31 : n.d. (recherche incomplète) ; 2026-01-30 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Galaxy → Candy Digital Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, échu 14 trimestres, inconnu 5 trimestres ; sensibilité `ever_financed` : actif 22 trimestres, inconnu 5 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Galaxy → CI Investments Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Galaxy → CoreWeave

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 12 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → Cipher

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 13 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → ADT INC.

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L2, L5) ; 12 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Contrepartie payable au client : 5 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Alphabet → EQUIFAX INC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → Fluidstack Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 67 % (2 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → Kitty Hawk Corporation

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → LTA Research & Exploration LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → PLANET LABS PBC

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète (texte non lu) ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Alphabet → PLAYSTUDIOS, INC.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → SNAP INC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → Technology Impact Growth Fund II, L.P.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Alphabet → SpaceX

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 1 trimestre, jamais documenté 26 trimestres ; sensibilité `ever_financed` : actif 1 trimestre, jamais documenté 26 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E5 : indéterminé — non publié.

### Alphabet → TeraWulf

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 75 % (3 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### Hut 8 → Fluidstack Ltd.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 29 trimestres ; sensibilité `ever_financed` : inconnu 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (historique tronqué) ; 2022-06-30 : n.d. (historique tronqué) ; 2023-06-30 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Hut 8 → Fluidstack USA IV Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 29 trimestres ; sensibilité `ever_financed` : inconnu 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (historique tronqué) ; 2022-06-30 : n.d. (historique tronqué) ; 2023-06-30 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Hut 8 → TZRC LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 13 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 29 trimestres ; sensibilité `ever_financed` : inconnu 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (historique tronqué) ; 2022-06-30 : n.d. (historique tronqué) ; 2023-06-30 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Intel → ASML

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 27 trimestres ; sensibilité `ever_financed` : actif 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : entre 0 % et 44 % ; 2022-12-31 : entre 0 % et 42 % ; 2023-12-30 : entre 0 % et 40 % ; 2024-12-28 : entre 0 % et 46 % ; 2025-12-27 : entre 0 % et 44 %.
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Intel → Altera Corporation

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 4 trimestres, jamais documenté 23 trimestres ; sensibilité `ever_financed` : actif 4 trimestres, jamais documenté 23 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : entre 0 % et 44 %.
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Intel → AP Grange Holdings, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 8 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (5 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### Intel → Beijing Unisoc Technology Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 21 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 22 trimestres, jamais documenté 5 trimestres ; sensibilité `ever_financed` : actif 22 trimestres, jamais documenté 5 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : entre 0 % et 44 % ; 2022-12-31 : entre 0 % et 42 % ; 2023-12-30 : entre 0 % et 40 % ; 2024-12-28 : entre 0 % et 46 % ; 2025-12-27 : entre 0 % et 44 %.
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Intel → Beijing UniSpreadtrum Technology Ltd

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 11 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 27 trimestres ; sensibilité `ever_financed` : actif 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : entre 0 % et 44 % ; 2022-12-31 : entre 0 % et 42 % ; 2023-12-30 : entre 0 % et 40 % ; 2024-12-28 : entre 0 % et 46 % ; 2025-12-27 : entre 0 % et 44 %.
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Intel → Cloudera, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 23 trimestres, inconnu 4 trimestres ; sensibilité `ever_financed` : actif 23 trimestres, inconnu 4 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : entre 0 % et 44 % ; 2022-12-31 : entre 0 % et 42 % ; 2023-12-30 : entre 0 % et 40 % ; 2024-12-28 : entre 0 % et 46 % ; 2025-12-27 : entre 0 % et 44 %.
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Intel → Foundry JV Holdco LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (3 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### Intel → Grange Newco LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (2 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Intel → HP, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 7 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (recherche incomplète) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-30 : n.d. (recherche incomplète) ; 2024-12-28 : n.d. (recherche incomplète) ; 2025-12-27 : n.d. (recherche incomplète).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Intel → Lenovo Group Ltd.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Intel → McAfee Corp.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 20 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 23 trimestres, inconnu 4 trimestres ; sensibilité `ever_financed` : actif 23 trimestres, inconnu 4 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : entre 0 % et 44 % ; 2022-12-31 : entre 0 % et 42 % ; 2023-12-30 : entre 0 % et 40 % ; 2024-12-28 : entre 0 % et 46 % ; 2025-12-27 : entre 0 % et 44 %.
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : indéterminé — intervalle à cheval sur le seuil ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Intel → Dell

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Intel → Micron

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 109 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 3 trimestres, échu 24 trimestres ; sensibilité `ever_financed` : actif 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 10).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E5 : indéterminé — non publié.

### Intel → SK hynix

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 7 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-25 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-30 : n.d. (précondition non remplie) ; 2024-12-28 : n.d. (précondition non remplie) ; 2025-12-27 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### IREN → Microsoft

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (une clause de la paire est caviardée) ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 29 trimestres ; sensibilité `ever_financed` : inconnu 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (historique tronqué) ; 2022-06-30 : n.d. (historique tronqué) ; 2023-06-30 : n.d. (historique tronqué) ; 2024-06-30 : n.d. (historique tronqué) ; 2025-06-30 : n.d. (historique tronqué) ; 2026-06-30 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### IREN → NVIDIA

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien documenté (L1, L3) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 29 trimestres ; sensibilité `ever_financed` : inconnu 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (historique tronqué) ; 2022-06-30 : n.d. (historique tronqué) ; 2023-06-30 : n.d. (historique tronqué) ; 2024-06-30 : n.d. (historique tronqué) ; 2025-06-30 : n.d. (historique tronqué) ; 2026-06-30 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### Meta → Jio Platforms Limited

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 24 trimestres, jamais documenté 3 trimestres ; sensibilité `ever_financed` : actif 24 trimestres, jamais documenté 3 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Marvell → Amazon

- Conclusion : **causalité non établie** ; structure financière seulement ; lien documenté (L2) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-30 : n.d. (précondition non remplie) ; 2022-01-29 : n.d. (précondition non remplie) ; 2023-01-28 : n.d. (précondition non remplie) ; 2024-02-03 : n.d. (précondition non remplie) ; 2025-02-01 : n.d. (précondition non remplie) ; 2026-01-31 : n.d. (précondition non remplie).
- Contrepartie payable au client : 6 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Marvell → Alphabet

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L2) ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-30 : n.d. (précondition non remplie) ; 2022-01-29 : n.d. (précondition non remplie) ; 2023-01-28 : n.d. (précondition non remplie) ; 2024-02-03 : n.d. (précondition non remplie) ; 2025-02-01 : n.d. (précondition non remplie) ; 2026-01-31 : n.d. (précondition non remplie).
- Contrepartie payable au client : 6 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Marvell → SoftBank

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-30 : n.d. (précondition non remplie) ; 2022-01-29 : n.d. (précondition non remplie) ; 2023-01-28 : n.d. (précondition non remplie) ; 2024-02-03 : n.d. (précondition non remplie) ; 2025-02-01 : n.d. (précondition non remplie) ; 2026-01-31 : n.d. (précondition non remplie).
- Contrepartie payable au client : 6 cellules indéterminées (non publié).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Microsoft → GENERAL MOTORS CO

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche incomplète (texte non lu) ; 18 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 21 trimestres, inconnu 8 trimestres ; sensibilité `ever_financed` : actif 21 trimestres, inconnu 8 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : entre 0 % et 10 % (borne haute exclue) ; 2022-06-30 : entre 0 % et 10 % (borne haute exclue) ; 2023-06-30 : entre 0 % et 10 % (borne haute exclue) ; 2024-06-30 : entre 0 % et 10 % (borne haute exclue) ; 2025-06-30 : entre 0 % et 10 % (borne haute exclue) ; 2026-06-30 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 12 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E1 : indéterminé — non traité (unité de la découverte non encore lue, ou bloc de §14 fermé) ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Microsoft → Anthropic

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Microsoft → OpenAI

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 30 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, jamais documenté 21 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, jamais documenté 21 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : entre 0 % et 10 % (borne haute exclue) ; 2026-06-30 : 7,3 %.
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Micron → Huawei Technologies Co. Ltd.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-09-02 : n.d. (précondition non remplie) ; 2022-09-01 : n.d. (précondition non remplie) ; 2023-08-31 : n.d. (précondition non remplie) ; 2024-08-29 : n.d. (précondition non remplie) ; 2025-08-28 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Micron → Kingston Technology Company, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 7 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-09-02 : n.d. (précondition non remplie) ; 2022-09-01 : n.d. (précondition non remplie) ; 2023-08-31 : n.d. (précondition non remplie) ; 2024-08-29 : n.d. (précondition non remplie) ; 2025-08-28 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Micron → Nanya Technology Corporation

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-09-02 : n.d. (précondition non remplie) ; 2022-09-01 : n.d. (précondition non remplie) ; 2023-08-31 : n.d. (précondition non remplie) ; 2024-08-29 : n.d. (précondition non remplie) ; 2025-08-28 : n.d. (précondition non remplie).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### Micron → WPG Holdings Limited

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-09-02 : n.d. (précondition non remplie) ; 2022-09-01 : n.d. (précondition non remplie) ; 2023-08-31 : n.d. (précondition non remplie) ; 2024-08-29 : n.d. (précondition non remplie) ; 2025-08-28 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Micron → Intel

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 109 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 28 trimestres ; sensibilité `ever_financed` : jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-09-02 : n.d. (précondition non remplie) ; 2022-09-01 : n.d. (précondition non remplie) ; 2023-08-31 : n.d. (précondition non remplie) ; 2024-08-29 : n.d. (précondition non remplie) ; 2025-08-28 : n.d. (précondition non remplie).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 10).
- Annexe E : E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### Nebius → ClickHouse Inc

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 25 trimestres ; sensibilité `ever_financed` : inconnu 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Nebius → Meta

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 8 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 25 trimestres ; sensibilité `ever_financed` : inconnu 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Nebius → Microsoft

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 25 trimestres ; sensibilité `ever_financed` : inconnu 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### NVIDIA → GCL GLOBAL HOLDINGS LTD

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 31 trimestres ; sensibilité `ever_financed` : inconnu 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-01-30 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-01-29 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-01-28 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-01-26 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2026-01-25 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### NVIDIA → CoreWeave

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 11 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 6 trimestres, jamais documenté 25 trimestres ; sensibilité `ever_financed` : actif 6 trimestres, jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : entre 0 % et 22 %.
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### NVIDIA → Intel

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 3 trimestres, jamais documenté 28 trimestres ; sensibilité `ever_financed` : actif 3 trimestres, jamais documenté 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : entre 0 % et 22 %.
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### NVIDIA → IREN

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L1, L3) ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### NVIDIA → Anthropic

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### NVIDIA → OpenAI

- Conclusion : **dépendance documentée** ; structure commerciale et financière ; lien documenté (L5) ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E4 (engagement) : indéterminé — date manquante ; E4 (paiement) : indéterminé — date manquante ; E5 : indéterminé — non publié.

### NVIDIA → Nebius

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 7 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, jamais documenté 29 trimestres ; sensibilité `ever_financed` : actif 2 trimestres, jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E5 : indéterminé — non publié.

### NVIDIA → Nscale

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### NVIDIA → SoftBank

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 16 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 31 trimestres ; sensibilité `ever_financed` : jamais documenté 31 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-01-31 : n.d. (précondition non remplie) ; 2022-01-30 : n.d. (précondition non remplie) ; 2023-01-29 : n.d. (précondition non remplie) ; 2024-01-28 : n.d. (précondition non remplie) ; 2025-01-26 : n.d. (précondition non remplie) ; 2026-01-25 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Ampere Computing Holdings LLC

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 11 trimestres, jamais documenté 19 trimestres ; sensibilité `ever_financed` : actif 11 trimestres, jamais documenté 19 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2026-05-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Oracle → Ampere Computing LLC

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 22 trimestres, échu 8 trimestres ; sensibilité `ever_financed` : actif 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2022-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2023-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-05-31 : entre 0 % et 10 % (borne haute exclue) ; 2026-05-31 : n.d. (précondition non remplie).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Oracle → Autonomous Medical Devices, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Desert Champions LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Eau Palm Beach Resort & Spa

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Ellison Institute, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Lanai Resorts, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Lawrence Investments, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → PARAMOUNT SKYDANCE CORP

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (texte non lu) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 30 trimestres ; sensibilité `ever_financed` : inconnu 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-05-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-05-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-05-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-05-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2026-05-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → Screening Room Media, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 2 trimestres, échu 28 trimestres ; sensibilité `ever_financed` : actif 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E5 : indéterminé — non publié.

### Oracle → Sensei AG Holdings, Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 30 trimestres ; sensibilité `ever_financed` : jamais documenté 30 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Oracle → TikTok USDS Joint Venture LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 3 trimestres, jamais documenté 27 trimestres ; sensibilité `ever_financed` : actif 3 trimestres, jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-05-31 : n.d. (précondition non remplie) ; 2022-05-31 : n.d. (précondition non remplie) ; 2023-05-31 : n.d. (précondition non remplie) ; 2024-05-31 : n.d. (précondition non remplie) ; 2025-05-31 : n.d. (précondition non remplie) ; 2026-05-31 : entre 0 % et 10 % (borne haute exclue).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Blue Owl → Blue Owl Capital Corporation

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Blue Owl → Blue Owl Real Estate Net Lease Trust

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 4 trimestres, échu 6 trimestres, inconnu 17 trimestres ; sensibilité `ever_financed` : actif 10 trimestres, inconnu 17 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : n.d. (historique tronqué).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Blue Owl → Blue Owl Technology Finance Corp.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Riot → AMD

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Riot → 7725 RENO #1, LLC

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Riot → Air HPC LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Riot → Bitfarms Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 15 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 9 trimestres, inconnu 18 trimestres ; sensibilité `ever_financed` : actif 9 trimestres, inconnu 18 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-31 : n.d. (recherche incomplète) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Riot → COINBASE CREDIT, INC.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 23 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 5 trimestres, jamais documenté 22 trimestres ; sensibilité `ever_financed` : actif 5 trimestres, jamais documenté 22 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Riot → Coinsquare Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 26 trimestres, jamais documenté 1 trimestre ; sensibilité `ever_financed` : actif 26 trimestres, jamais documenté 1 trimestre.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Riot → goNumerical Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 1 trimestre, échu 26 trimestres ; sensibilité `ever_financed` : actif 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Riot → Mogo Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 11 trimestres, inconnu 16 trimestres ; sensibilité `ever_financed` : actif 11 trimestres, inconnu 16 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (recherche incomplète) ; 2022-12-31 : n.d. (recherche incomplète) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 6 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E1 : indéterminé — recherche incomplète ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Riot → Rhodium Encore LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Riot → Rhodium JV, LLC

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Riot → TessPay Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 26 trimestres, jamais documenté 1 trimestre ; sensibilité `ever_financed` : actif 26 trimestres, jamais documenté 1 trimestre.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Riot → Verady, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 26 trimestres, jamais documenté 1 trimestre ; sensibilité `ever_financed` : actif 26 trimestres, jamais documenté 1 trimestre.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Riot → Verady, LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 23 trimestres, jamais documenté 4 trimestres ; sensibilité `ever_financed` : actif 23 trimestres, jamais documenté 4 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2024-12-31 : entre 0 % et 10 % (borne haute exclue) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 10 % : indéterminé — intervalle à cheval sur le seuil ; E2 à 20 % : réfuté ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Riot → Anthropic

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → BCPE Pangea Cayman2 Limited

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 4 trimestres, inconnu 24 trimestres ; sensibilité `ever_financed` : actif 4 trimestres, inconnu 24 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → BCPE Pangea Intermediate Holdings Cayman, L.P.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 4 trimestres, inconnu 24 trimestres ; sensibilité `ever_financed` : actif 4 trimestres, inconnu 24 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 2 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → Chungcheong energy service Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 21 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → Clean Industrial REIT Co., Ltd

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → ESSENCORE Limited

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → FSK L&S Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 23 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → HITECH Semiconductor (Wuxi) Co., Ltd.

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 33 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, inconnu 20 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, inconnu 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 9).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → Hystars Semiconductor (Wuxi) Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 18 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 9).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → Korea Nexlene Company

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 9 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SiFive, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, inconnu 20 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, inconnu 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → SK Aircore Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Airplus Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 22 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 6).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Bioscience Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 12 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Chemicals Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK China Company Limited

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 20 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, inconnu 20 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, inconnu 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → SK E&S Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Ecoplant Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 21 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Energy Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 19 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK enpulse Co., Ltd

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Holdings Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 23 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK hynix system ic (Wuxi) Co., Ltd.

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 14 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, inconnu 20 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, inconnu 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → SK hynix system ic Wuxi solutions Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Innovation Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 21 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Japan Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 13 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Networks Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 22 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK REIT Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 15 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Shieldus Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 23 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Siltron Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 18 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK South East Asia Investment Pte. Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, inconnu 20 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, inconnu 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → SK Specialty Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Square Co., Ltd.

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 13 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Telecom Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète (le client dépose hors du périmètre et ses dépôts ne sont pas tous lus (découverte, §14)) ; 22 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SK Tri Chem Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 18 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SM Core Co., Ltd.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → SMCore. Inc

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 19 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → Specialized Investment-type Private Equity Investment Trust For Growth Of Semiconductor

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 8 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, inconnu 20 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, inconnu 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → Specialized Investment-type Private Equity Investment Trust For Win-win System Semiconductor

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 5 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, inconnu 20 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, inconnu 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### SK hynix → SystemIC Solution

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → TCL Fund

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → UNA Digital Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 6 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 28 trimestres ; sensibilité `ever_financed` : inconnu 28 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E5 : indéterminé — non publié.

### SK hynix → Wuxi xinfa IC industry park., Ltd

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 7 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 8 trimestres, inconnu 20 trimestres ; sensibilité `ever_financed` : actif 8 trimestres, inconnu 20 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — historique tronqué ; E2 à 10 % : indéterminé — historique tronqué ; E2 à 20 % : indéterminé — historique tronqué ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Supermicro → Applied Digital

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 2 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Ablecom Technology Inc

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 677 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Aeon Lighting Technology Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Ampera Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 5 trimestres, jamais documenté 24 trimestres ; sensibilité `ever_financed` : actif 5 trimestres, jamais documenté 24 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : entre 0 % et 21 % ; 2026-06-30 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 4 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — précondition non remplie ; E2 à 10 % : indéterminé — précondition non remplie ; E2 à 20 % : indéterminé — précondition non remplie ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### Supermicro → Compuware Technology Inc

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 681 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Green Earth Liang's Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 8 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Leadtek Research Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 51 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Memverge, Inc

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Super Micro Asia Science and Technology Park, Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Super Micro Management Consulting Inc.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### Supermicro → Lambda

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 29 trimestres ; sensibilité `ever_financed` : jamais documenté 29 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-06-30 : n.d. (précondition non remplie) ; 2022-06-30 : n.d. (précondition non remplie) ; 2023-06-30 : n.d. (précondition non remplie) ; 2024-06-30 : n.d. (précondition non remplie) ; 2025-06-30 : n.d. (précondition non remplie) ; 2026-06-30 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 75 % (3 sur 4).
- Annexe E : E5 : indéterminé — non publié.

### SpaceX → ECHOSTAR CORP

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète (texte non lu) ; 7 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E5 : indéterminé — non publié.

### SpaceX → Tesla, Inc.

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche incomplète (texte non lu) ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2022-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2023-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2024-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)) ; 2025-12-31 : n.d. (non traité (unité de la découverte non encore lue, ou bloc de §14 fermé)).
- Part du revenu venant de clients qui financent le fournisseur : 5 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### SpaceX → Anthropic

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 27 trimestres ; sensibilité `ever_financed` : jamais documenté 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### TSMC → Broadcom

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 25 trimestres ; sensibilité `ever_financed` : jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : n.d. (non publié).
- Annexe E : E5 : indéterminé — non publié.

### TSMC → Advanced Vision Semiconductor Manufacturing Corporation

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 25 trimestres ; sensibilité `ever_financed` : jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### TSMC → Global Unichip Corporation

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 24 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 25 trimestres ; sensibilité `ever_financed` : actif 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : n.d. (terme manquant) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 3).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — terme manquant ; E2 à 10 % : indéterminé — terme manquant ; E2 à 20 % : indéterminé — terme manquant ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### TSMC → Mutual-Pak Technology Co., Ltd.

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 8 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 25 trimestres ; sensibilité `ever_financed` : actif 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : n.d. (terme manquant) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — terme manquant ; E2 à 10 % : indéterminé — terme manquant ; E2 à 20 % : indéterminé — terme manquant ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### TSMC → Systems on Silicon Manufacturing Company Pte Ltd.

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 41 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 25 trimestres ; sensibilité `ever_financed` : actif 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : n.d. (terme manquant) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — terme manquant ; E2 à 10 % : indéterminé — terme manquant ; E2 à 20 % : indéterminé — terme manquant ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### TSMC → Vanguard International Semiconductor Corporation

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 32 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 25 trimestres ; sensibilité `ever_financed` : actif 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : n.d. (terme manquant) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 5).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — terme manquant ; E2 à 10 % : indéterminé — terme manquant ; E2 à 20 % : indéterminé — terme manquant ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### TSMC → Xintec Inc.

- Conclusion : **relation commerciale doublée d'un financement** ; structure commerciale et financière ; lien non trouvé, recherche complète au sens de E.0 ; 30 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : actif 25 trimestres ; sensibilité `ever_financed` : actif 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (terme manquant) ; 2022-12-31 : n.d. (terme manquant) ; 2023-12-31 : n.d. (terme manquant) ; 2024-12-31 : n.d. (terme manquant) ; 2025-12-31 : n.d. (terme manquant).
- Dépendance du carnet (RPO) : 10 cellules indéterminées (client anonyme).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 4).
- Annexe E : E1 : non étayé ; E2 à 5 % : indéterminé — terme manquant ; E2 à 10 % : indéterminé — terme manquant ; E2 à 20 % : indéterminé — terme manquant ; E3 à 5 % : indéterminé — client anonyme ; E3 à 10 % : indéterminé — client anonyme ; E3 à 20 % : indéterminé — client anonyme ; E5 : indéterminé — non publié.

### TSMC → Intel

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 25 trimestres ; sensibilité `ever_financed` : jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### TSMC → SoftBank

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 10 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : jamais documenté 25 trimestres ; sensibilité `ever_financed` : jamais documenté 25 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (précondition non remplie) ; 2022-12-31 : n.d. (précondition non remplie) ; 2023-12-31 : n.d. (précondition non remplie) ; 2024-12-31 : n.d. (précondition non remplie) ; 2025-12-31 : n.d. (précondition non remplie).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### TeraWulf → Fluidstack Ltd.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 3 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### TeraWulf → Fluidstack USA I Inc.

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### TeraWulf → FS CS I LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### TeraWulf → Heorot Power Holdings LLC

- Conclusion : **achats réciproques seulement** ; structure commerciale réciproque ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 50 % (1 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### TeraWulf → NAUTILUS CRYPTOMINE LLC

- Conclusion : **causalité non établie** ; structure financière seulement ; lien non trouvé, recherche complète au sens de E.0 ; 1 arête.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 100 % (1 sur 1).
- Annexe E : E5 : indéterminé — non publié.

### TeraWulf → Anthropic

- Conclusion : **causalité non établie** ; structure commerciale seulement ; lien non trouvé, recherche complète au sens de E.0 ; 4 arêtes.
- Statut « financé » F, politique de tête (`exposure_outstanding`) : inconnu 27 trimestres ; sensibilité `ever_financed` : inconnu 27 trimestres.
- Dépendance de revenu documentée (`documented_revenue_dependency`, par exercice du fournisseur) : 2021-12-31 : n.d. (historique tronqué) ; 2022-12-31 : n.d. (historique tronqué) ; 2023-12-31 : n.d. (historique tronqué) ; 2024-12-31 : n.d. (historique tronqué) ; 2025-12-31 : n.d. (historique tronqué).
- Couverture contractuelle (accords connus déposés en entier, non caviardés) : 0 % (0 sur 2).
- Annexe E : E5 : indéterminé — non publié.

### Sorties de couverture par fournisseur (§3.6)

| Fournisseur | Exercice | Revenu attribué à des clients nommés | Clients anonymes d'au moins 10 % | Résidu | Paires vues seulement côté client |
| --- | --- | ---: | ---: | ---: | ---: |
| NVIDIA | 2026-01-25 | 0,0 % | 36,0 % [35,0 % ; 37,0 %] | 64,0 % | 1 |
| Alphabet | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 6 |
| Amazon | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 5 |
| Meta | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Microsoft | 2026-06-30 | 7,3 % | 0,0 % [0,0 % ; 0,0 %] | 92,7 % | 1 |
| Oracle | 2026-05-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 1 |
| CoreWeave | 2025-12-31 | 0,0 % | 67,0 % [66,5 % ; 67,5 %] | 33,0 % | 0 |
| SpaceX | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 1 |
| AMD | 2025-12-27 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Broadcom | 2025-11-02 | 0,0 % | 32,0 % [31,5 % ; 32,5 %] | 68,0 % | 2 |
| Marvell | 2026-01-31 | 0,0 % | 51,0 % [50,0 % ; 52,0 %] | 49,0 % | 0 |
| TeraWulf | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Cipher | 2025-12-31 | 70,0 % | 0,0 % [0,0 % ; 0,0 %] | 30,0 % | 0 |
| Core Scientific | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 1 |
| Nebius | 2025-12-31 | 40,0 % | 0,0 % [0,0 % ; 0,0 %] | 60,0 % | 0 |
| IREN | 2026-06-30 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Applied Digital | 2026-05-31 | 0,0 % | 96,0 % [94,0 % ; 98,0 %] | 4,0 % | 0 |
| Dell | 2026-01-30 | 0,0 % | 12,0 % [11,5 % ; 12,5 %] | 88,0 % | 0 |
| Supermicro | 2026-06-30 | 0,2 % | 28,1 % [28,0 % ; 28,2 %] | 71,7 % | 0 |
| Hut 8 | 2025-12-31 | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Galaxy | 2025-12-31 | 38,0 % | 0,0 % [0,0 % ; 0,0 %] | 62,0 % | 0 |
| Akamai | 2025-12-31 | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |
| Backblaze | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Riot | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Blue Owl | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Apollo | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Blackstone | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 0 |
| Intel | 2025-12-27 | 43,0 % | 43,0 % [42,5 % ; 43,5 %] | 14,0 % | 0 |
| Micron | 2025-08-28 | 17,0 % | 0,0 % [0,0 % ; 0,0 %] | 83,0 % | 0 |
| TSMC | 2025-12-31 | 0,0 % | 0,0 % [0,0 % ; 0,0 %] | 100,0 % | 1 |
| ASML | 2025-12-31 | 61,2 % | 0,0 % [0,0 % ; 0,0 %] | 38,8 % | 1 |
| SK hynix | 2025-12-31 | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (terme manquant) | n.d. (non publié) |

Le texte qui entoure les faits de concentration est lu (bloc text de §14) : un client qui reste anonyme l'est dans les pièces elles-mêmes. Un client nommé ailleurs peut être l'un des anonymes (`overlap_possible`).

## Cycles entre groupes (bloc paths, §14)

Un cycle suit les arêtes dans le sens de la ressource (financeur → financé, client → fournisseur, fournisseur → client pour une contrepartie au client, garant → obligé) et revient à son point de départ après un ou deux intermédiaires ; il passe par au moins un groupe du périmètre et jamais à l'intérieur d'un même groupe. Concomitance (`temporal`) : on peut choisir une arête par maillon dont les périodes sont actives ensemble ou à moins de quatre trimestres d'écart. La conclusion n'est « dépendance documentée » que si chaque paire d'arêtes consécutives a sa pièce L1 à L5, dont l'extrait nomme les parties de la jonction : les deux d'une paire pour un cycle de longueur 2, les trois pour un cycle de longueur 3. Aucun ratio de chemin n'est publié, des montants de natures différentes ne se composant pas, et un cycle ne prouve ni revenu artificiel ni absence de demande finale (§3.3).

| Cycle | Longueur | Concomitance (écart en trimestres) | Structure | Lien | Conclusion |
| --- | ---: | --- | --- | --- | --- |
| Akamai → Anthropic → Akamai | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| AMD → OpenAI → AMD | 2 | oui (0) | commerciale et financière | documenté (L2, L5) | **dépendance documentée** |
| AMD → OpenAI → Microsoft → AMD | 3 | oui (1) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| AMD → Meta → AMD | 2 | oui (0) | commerciale et financière | documenté (L2) | **dépendance documentée** |
| Amazon → AIR TRANSPORT SERVICES GROUP, INC. → Amazon | 2 | oui (0) | commerciale et financière | documenté (L1, L5) | **dépendance documentée** |
| Amazon → APPLIED OPTOELECTRONICS, INC. → Amazon | 2 | oui (0) | commerciale et financière | documenté (L1, L3) | **dépendance documentée** |
| Amazon → CLEAN ENERGY FUELS CORP. → Amazon | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Amazon → RIVIAN AUTOMOTIVE, INC. / DE → Amazon | 2 | oui (0) | commerciale et financière | documenté (L5) | **dépendance documentée** |
| Amazon → Anthropic → Amazon | 2 | oui (0) | commerciale et financière | documenté (L2) | **dépendance documentée** |
| Amazon → OpenAI → Amazon | 2 | oui (0) | commerciale et financière | documenté (L5) | **dépendance documentée** |
| Amazon → OpenAI → Cerebras Systems Inc. → Amazon | 3 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Applied Digital → AI Bridge Funding LLC → Applied Digital | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Applied Digital → B. RILEY COMMERCIAL CAPITAL, LLC → Applied Digital | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Applied Digital → B. Riley Financial, Inc. → Applied Digital | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Applied Digital → CIM APLD LENDER HOLDINGS, LLC → Applied Digital | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Applied Digital → Macquarie Equipment Capital, Inc. → Applied Digital | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Applied Digital → MIP HPC HOLDINGS, LLC → Applied Digital | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Applied Digital → MIP VI HPC HOLDINGS, LLC → Applied Digital | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Applied Digital → SUMITOMO MITSUI BANKING CORPORATION → Applied Digital | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Applied Digital → CoreWeave → Applied Digital | 2 | oui (0) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| Apollo → Athene Holding Ltd. → Apollo | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Apollo → Bank of America, N.A. → Apollo | 2 | oui (2) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| ASML → Carl Zeiss SMT GmbH → ASML | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| ASML → Carl Zeiss SMT Holding GmbH & Co. KG → ASML | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Broadcom → Dell → Broadcom | 2 | oui (0) | commerciale réciproque | non trouvé, recherche complète au sens de E.0 | **achats réciproques seulement** |
| Backblaze → AFCO Premium Credit LLC → Backblaze | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Backblaze → City National Bank → Backblaze | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Backblaze → CoreWeave → Backblaze | 2 | oui (0) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| Cipher → BITFURY TOP HOLDCO B.V. → Cipher | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Cipher → LUMINANT ET SERVICES COMPANY LLC → Cipher | 2 | non (4) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Core Scientific → BITMAIN TECHNOLOGIES DELAWARE LIMITED → Core Scientific | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| CoreWeave → OpenAI → CoreWeave | 2 | oui (0) | commerciale et financière | documenté (L5) | **dépendance documentée** |
| CoreWeave → OpenAI → Microsoft → CoreWeave | 3 | oui (0) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| CoreWeave → OpenAI → NVIDIA → CoreWeave | 3 | non (4) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| CoreWeave → NVIDIA → CoreWeave | 2 | oui (0) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| CoreWeave → NVIDIA → Anthropic → CoreWeave | 3 | oui (2) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| CoreWeave → NVIDIA → OpenAI → CoreWeave | 3 | oui (1) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| Dell → VMware, Inc. → Dell | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Dell → Intel → Dell | 2 | oui (0) | commerciale seulement | non trouvé, recherche complète au sens de E.0 | **causalité non établie** |
| Alphabet → ADT INC. → Alphabet | 2 | oui (0) | commerciale et financière | documenté (L2, L5) | **dépendance documentée** |
| Alphabet → PLANET LABS PBC → Alphabet | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Alphabet → Marvell → Alphabet | 2 | oui (0) | commerciale et financière | documenté (L2) | **dépendance documentée** |
| Intel → Altera Corporation → Intel | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Intel → AP Grange Holdings, LLC → Intel | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Intel → Foundry JV Holdco LLC → Intel | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Intel → HP, Inc. → Intel | 2 | oui (0) | commerciale seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Intel → Lenovo Group Ltd. → Intel | 2 | oui (0) | commerciale seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Intel → SLP VII Gryphon Aggregator, L.P. → Intel | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Intel → United States Department of Commerce → Intel | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Intel → Micron → Intel | 2 | oui (0) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| Intel → Micron → United States Department of Commerce → Intel | 3 | non (19) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Intel → SK hynix → Intel | 2 | oui (0) | commerciale seulement | non trouvé, recherche complète au sens de E.0 | **causalité non établie** |
| Intel → SK hynix → United States Department of Commerce → Intel | 3 | non (22) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| IREN → NVIDIA → IREN | 2 | oui (0) | commerciale et financière | documenté (L1, L3) | **dépendance documentée** |
| Microsoft → GENERAL MOTORS CO → Microsoft | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Microsoft → OpenAI → Microsoft | 2 | oui (0) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| Micron → Nanya Technology Corporation → Micron | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Nebius → NVIDIA → Nebius | 2 | oui (0) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| NVIDIA → OpenAI → NVIDIA | 2 | oui (0) | commerciale et financière | documenté (L5) | **dépendance documentée** |
| NVIDIA → Nscale → NVIDIA | 2 | oui (0) | commerciale seulement | non trouvé, recherche complète au sens de E.0 | **causalité non établie** |
| NVIDIA → SoftBank → OpenAI → NVIDIA | 3 | oui (0) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| Oracle → Ampere Computing Holdings LLC → Oracle | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Oracle → Ampere Computing LLC → Oracle | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Oracle → Eau Palm Beach Resort & Spa → Oracle | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| Riot → COINBASE CREDIT, INC. → Riot | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| SK hynix → Chungcheong energy service Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → Clean Industrial REIT Co., Ltd → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → FSK L&S Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → HITECH Semiconductor (Wuxi) Co., Ltd. → SK hynix | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| SK hynix → Hystars Semiconductor (Wuxi) Co., Ltd. → SK hynix | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| SK hynix → SK Aircore Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Airplus Inc. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Bioscience Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Chemicals Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK China Company Limited → SK hynix | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| SK hynix → SK E&S Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Ecoplant Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Energy Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK enpulse Co., Ltd → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Holdings Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK hynix system ic (Wuxi) Co., Ltd. → SK hynix | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| SK hynix → SK hynix system ic Wuxi solutions Inc. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Innovation Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Japan Inc. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Networks Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK REIT Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Shieldus Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Siltron Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Specialty Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Telecom Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SK Tri Chem Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SM Core Co., Ltd. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SMCore. Inc → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → SystemIC Solution → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| SK hynix → UNA Digital Inc. → SK hynix | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| Supermicro → Ablecom Technology Inc → Supermicro | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Supermicro → Compuware Technology Inc → Supermicro | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| Supermicro → CTBC Bank Co., Ltd. → Supermicro | 2 | oui (0) | financière seulement | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **causalité non établie** |
| Supermicro → Green Earth Liang's Inc. → Supermicro | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| Supermicro → Leadtek Research Inc. → Supermicro | 2 | oui (0) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |
| Supermicro → Lambda → Supermicro | 2 | oui (2) | commerciale et financière | non trouvé, recherche complète au sens de E.0 | **relation commerciale doublée d'un financement** |
| SpaceX → ECHOSTAR CORP → SpaceX | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| SpaceX → Tesla, Inc. → SpaceX | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| TSMC → Global Unichip Corporation → TSMC | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| TSMC → Systems on Silicon Manufacturing Company Pte Ltd. → TSMC | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| TSMC → Vanguard International Semiconductor Corporation → TSMC | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| TSMC → Xintec Inc. → TSMC | 2 | oui (0) | commerciale et financière | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **relation commerciale doublée d'un financement** |
| TeraWulf → Heorot Power Holdings LLC → TeraWulf | 2 | non (16) | commerciale réciproque | non trouvé, recherche incomplète (un nœud dépose hors du périmètre ou une paire du cycle reste à lire) | **achats réciproques seulement** |

Décompte de E.6 (descriptif, hors de E.7) : 108 cycles ; concomitance non : causalité non établie 1, relation commerciale doublée d'un financement 3, achats réciproques seulement 1 ; concomitance oui : causalité non établie 22, relation commerciale doublée d'un financement 39, dépendance documentée 12, achats réciproques seulement 30.

## Form D (bloc form_d, §14)

Un Form D donne le montant vendu d'une offre, cumulé depuis sa première vente, jamais une valorisation ni une contrepartie. La mesure se fait par offre (CIK de l'émetteur et date de première vente) sur le dernier dépôt connu : un D et ses D/A ne se somment pas, chaque dépôt remplace le précédent. Le montant peut inclure du non monétaire (titres remis lors d'un regroupement d'entreprises, par exemple) : ce n'est pas du numéraire primaire sans autre pièce. Aucun total n'est fait, ni entre offres ni entre véhicules.

**Émetteurs du périmètre** (faits sur l'entité émettrice, rattachée à son groupe à la date du dépôt ; vue `as_known`, puis `revised` quand le rattachement diffère, §10.3) :

| Émetteur | Groupe | Première vente | Dernier dépôt | Montant vendu | Regroupement d'entreprises |
| --- | --- | --- | --- | ---: | --- |
| SPACE EXPLORATION TECHNOLOGIES CORP | SpaceX | 2020-02-28 | 2020-05-26 | 346 M$ | non |
| SPACE EXPLORATION TECHNOLOGIES CORP | SpaceX | 2020-08-04 | 2020-08-18 | 1 901 M$ | non |
| SPACE EXPLORATION TECHNOLOGIES CORP | SpaceX | 2021-02-16 | 2021-04-14 | 1 164 M$ | non |
| SPACE EXPLORATION TECHNOLOGIES CORP | SpaceX | 2021-11-01 | 2021-11-15 | 345 M$ | oui |
| SPACE EXPLORATION TECHNOLOGIES CORP | SpaceX | 2021-12-14 | 2021-12-29 | 337 M$ | non |
| SPACE EXPLORATION TECHNOLOGIES CORP | SpaceX | 2022-05-27 | 2022-06-30 | 1 725 M$ | non |
| SPACE EXPLORATION TECHNOLOGIES CORP | SpaceX | 2022-07-20 | 2022-08-05 | 250 M$ | non |
| CoreWeave, Inc. | CoreWeave | 2019-09-25 | 2020-02-14 | 1 M$ | non |
| CoreWeave, Inc. | CoreWeave | 2020-12-14 | 2021-03-03 | 4 M$ | non |
| CoreWeave, Inc. | CoreWeave | 2021-04-30 | 2021-05-07 | 4 M$ | non |
| CoreWeave, Inc. | CoreWeave | 2024-05-16 | 2024-05-30 | 1 150 M$ | non |
| Marvell Technology, Inc. | Marvell | 2026-02-02 | 2026-02-17 | 2 031 M$ | oui |
| Marvell Technology, Inc. | Marvell | 2026-02-10 | 2026-02-25 | 200 M$ | oui |
| X.AI CORP. | X.AI Corp. ; SpaceX en vue `revised` | 2023-11-29 | 2023-12-05 | 135 M$ | non |
| X.AI CORP. | X.AI Corp. ; SpaceX en vue `revised` | 2024-05-10 | 2024-05-28 | 5 024 M$ | non |
| X.AI CORP. | X.AI Corp. ; SpaceX en vue `revised` | 2024-11-22 | 2024-12-05 | 6 000 M$ | non |
| X.AI CORP. | X.AI Corp. ; SpaceX en vue `revised` | 2025-02-10 | 2025-02-25 | 28 M$ | oui |
| X.AI Holdings Corp. | X.AI Holdings Corp. ; SpaceX en vue `revised` | 2025-06-18 | 2025-08-06 | 5 319 M$ | non |
| X.AI Holdings Corp. | X.AI Holdings Corp. ; SpaceX en vue `revised` | 2025-12-19 | 2026-01-06 | 16 600 M$ | non |
| MICROSOFT CORP | Microsoft | 2020-07-14 | 2020-07-24 | 270 M$ | oui |

**Véhicules tiers** (émetteurs dont la dénomination, ou la description des titres offerts, nomme un laboratoire ou un groupe qui ne dépose encore aucun rapport périodique) : ils mesurent une demande d'exposition secondaire et n'entrent jamais dans une mesure de financement du nœud sous-jacent. Série par véhicule et par trimestre civil, sur le dernier dépôt connu à chaque fin de trimestre, tant que le sous-jacent ne dépose pas ; un nom ne prouve pas la détention, et un homonyme est écarté avec son motif.

| Sous-jacent nommé | Véhicules | Offres | Cellules (véhicule × trimestre) | Premier trimestre | Dernier trimestre |
| --- | ---: | ---: | ---: | --- | --- |
| CoreWeave | 13 | 13 | 30 | 2023-12-31 | 2025-03-31 |
| Anthropic | 61 | 77 | 531 | 2023-06-30 | 2026-09-30 |
| OpenAI | 32 | 33 | 218 | 2023-03-31 | 2026-09-30 |
| SpaceX | 194 | 207 | 1 496 | 2019-06-30 | 2026-06-30 |

- CoreWeave, plus grandes offres connues au 2025-03-31 : Lumida 2024 A CoreWeave SPV Sep 24 a Series of CGF2021 LLC 11 M$ ; AUGUREY VENTURES I, LLC - COREWEAVE A 3 M$ ; DiversiFi Ventures CoreWeave SPV I a Series of CGF2021 LLC 2 M$ ; AUGUREY VENTURES III, LLC - SERIES COREWEAVE B 1 M$ ; CoreWeave a Series of Anchor Capital GP II LLC 1 M$.
- Anthropic, plus grandes offres connues au 2026-09-30 : MW LSVC Anthropic, LLC 18 M$ ; HII Anthropic-01, a Series of HII Anthropic, LLC 17 M$ ; Anthropic Magnitude Jan 2026 a Series of CGF2021 LLC 14 M$ ; HII Anthropic Series-02, a Series of HII Anthropic, LLC 12 M$ ; Hiive Anthropic Series II a Series of Hiive Anthropic LLC 9 M$.
- OpenAI, plus grandes offres connues au 2026-09-30 : Starbridge OpenAI 1 Jul 2025 a Series of CGF2021 LLC 9 M$ ; OpenAI-01, a Series of OpenAI Opp Fund LLC 8 M$ ; OpenAI Sep 2024 a Series of CGF2021 LLC 5 M$ ; DiversiFi Ventures OpenAI SPVI a Series of CGF2021 LLC 4 M$ ; OpenAI 1, a Series of Venelite Venture Funds, LP 3 M$.
- SpaceX, plus grandes offres connues au 2026-06-30 : American Ventures QP Opportunity Fund LLC, Series IV SpaceX 202 M$ ; MCF SpaceX LLC 31 M$ ; MCF SpaceX-I LLC 29 M$ ; Vise SpaceX SPV I, LLC 26 M$ ; SpaceX Partners 1 LLC 21 M$.

Offres écartées : 12 dont le terme désigne autre chose qu'une exposition à la cible (homonyme, ou promoteur du fonds ; motif lu dans le Form D, D-0041) ; offres du périmètre antérieures à la fenêtre allongée 26.

## Émetteurs étrangers (bloc foreign, §14)

La file de la découverte compte 263 émetteurs étrangers (20-F, 40-F, 6-K, F-1, F-4). La règle fixée avant lecture retient ceux que la spec nomme comme nœuds de la chaîne et ceux qui sont déjà dans une paire ou un cycle : 2 (IREN Ltd, NEBIUS GROUP N.V.). Les autres restent dans la file, « non traités ». Un 20-F ou un 40-F porte des états annuels audités ; un 6-K est furnished, admissible seulement s'il est incorporé par référence dans un document d'enregistrement par mention expresse.

| Émetteur | Formulaire | Cadre comptable | Lignes | dont arêtes |
| --- | --- | --- | ---: | ---: |
| ASML | 20-F | — | 6 | 5 |
| ASML | 20-F | US GAAP | 515 | 455 |
| ASML | 6-K | — | 87 | 2 |
| ALIBABA GROUP HOLDING LTD | 20-F | — | 1 | 1 |
| brookfield wealth solutions ltd | 6-K | — | 16 | 0 |
| CONCORDE INTERNATIONAL GROUP LTD. | 20-F | — | 3 | 2 |
| DIDI GLOBAL INC. | 20-F | — | 2 | 1 |
| gambling com group ltd | 20-F | — | 1 | 0 |
| GCL GLOBAL HOLDINGS LTD | 20-F | — | 2 | 2 |
| hive digital technologies ltd | 6-K | — | 2 | 0 |
| KOREA ELECTRIC POWER CORP | 20-F | — | 3 | 3 |
| poet technologies inc | 6-K | — | 1 | 0 |
| SHINHAN FINANCIAL GROUP CO LTD | 20-F | — | 22 | 16 |
| Siyata Mobile Inc. | 20-F | — | 2 | 0 |
| Siyata Mobile Inc. | 20-F/A | — | 1 | 0 |
| SK Telecom Co., Ltd. | 20-F | — | 5 | 1 |
| UTSTARCOM HOLDINGS CORP. | 20-F | — | 2 | 1 |
| IREN | 20-F | IFRS | 1 | 0 |
| IREN | 20-F/A | IFRS | 1 | 0 |
| IREN | 6-K | — | 87 | 25 |
| IREN | 6-K | IFRS | 1 | 0 |
| IREN | 6-K/A | — | 10 | 1 |
| Nebius | 20-F | — | 16 | 8 |
| Nebius | 20-F | US GAAP | 35 | 18 |
| Nebius | 6-K | — | 117 | 44 |
| Nebius | 6-K/A | — | 10 | 4 |
| SoftBank | 20-F | — | 110 | 44 |
| SoftBank | 6-K | — | 100 | 12 |
| SK hynix | 6-K | — | 96 | 21 |
| TSMC | 20-F | — | 40 | 33 |
| TSMC | 20-F | IFRS | 349 | 286 |
| TSMC | 6-K | — | 99 | 20 |

6-K incorporés par référence (donc admissibles) : 24 ; agrégats écartés pour cadres comptables mêlés (invariant f) : 0.

## Côté prêteur (BDC Data Sets)

Positions que les sociétés de développement d'affaires (BDC) publient dans leur portefeuille, rattachées aux entités des groupes et aux contreparties que nomment leurs pièces, par dénomination légale entière ; une position dont l'identifiant nomme aussi un autre émetteur n'est rattachée à personne. Vue `as_known` : le portefeuille à la date du bilan du dépôt de chaque fonds. Les fonds privés et les banques ne publient rien (`not_public`), et une balise absente ne prouve rien : un taux d'intérêt capitalisé ou un statut de non-accumulation non balisé reste indéterminé, jamais nul. Juste valeur ÷ coût n'est pas une probabilité de défaut, et des intérêts capitalisés peuvent être prévus dès l'origine : les trois signaux se lisent ensemble.

| Groupe de l'émetteur | Date du bilan | Instrument | Positions | Coût | Juste valeur | Juste valeur ÷ coût | Part des intérêts capitalisés | Part sans accumulation d'intérêts |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Applied Digital | 2024-03-31 | prêts et obligations | 2 | 34 M$ | 34 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Applied Digital | 2024-06-30 | prêts et obligations | 5 | 36 M$ | 36 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Applied Digital | 2024-09-30 | prêts et obligations | 5 | 28 M$ | 29 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Applied Digital | 2024-12-31 | prêts et obligations | 5 | 23 M$ | 23 M$ | 1,03 x | n.d. (non balisé) | n.d. (non balisé) |
| Applied Digital | 2025-03-31 | prêts et obligations | 1 | 3 M$ | 3 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Applied Digital | 2025-06-30 | prêts et obligations | 5 | 14 M$ | 14 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Applied Digital | 2025-09-30 | prêts et obligations | 8 | 10 M$ | 11 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Applied Digital | 2025-12-31 | prêts et obligations | 7 | 6 M$ | 6 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Applied Digital | 2026-03-31 | prêts et obligations | 5 | 1 M$ | 1 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Broadcom | 2022-12-31 | non classé | 1 | 5 M$ | 5 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Backblaze | 2023-03-31 | prêts et obligations | 15 | 10 M$ | 10 M$ | 0,97 x | n.d. (non balisé) | n.d. (non balisé) |
| Backblaze | 2023-06-30 | prêts et obligations | 14 | 8 M$ | 8 M$ | 0,97 x | n.d. (non balisé) | n.d. (non balisé) |
| Backblaze | 2023-09-30 | prêts et obligations | 11 | 7 M$ | 7 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Backblaze | 2023-12-31 | prêts et obligations | 8 | 5 M$ | 5 M$ | 0,97 x | n.d. (non balisé) | n.d. (non balisé) |
| Backblaze | 2024-03-31 | prêts et obligations | 4 | 2 M$ | 2 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Backblaze | 2024-06-30 | prêts et obligations | 3 | 1 M$ | 1 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Backblaze | 2024-09-30 | prêts et obligations | 1 | 708 000 $ | 693 000 $ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Backblaze | 2024-12-31 | prêts et obligations | 2 | 3 M$ | 3 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Blackstone | 2026-03-31 | prêts et obligations | 2 | 990 266 $ | 990 332 $ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2022-09-30 | prêts et obligations | 1 | 30 M$ | 30 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2022-09-30 | titres de capital | 1 | 296 000 $ | 119 000 $ | 0,40 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2022-12-31 | prêts et obligations | 1 | 30 M$ | 11 M$ | 0,38 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2022-12-31 | titres de capital | 1 | 296 000 $ | 7 000 $ | 0,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2023-03-31 | prêts et obligations | 7 | 87 M$ | 46 M$ | 0,53 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2023-03-31 | titres de capital | 4 | 638 000 $ | 60 000 $ | 0,09 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2023-06-30 | prêts et obligations | 9 | 87 M$ | 51 M$ | 0,59 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2023-06-30 | titres de capital | 4 | 638 000 $ | 168 000 $ | 0,26 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2023-09-30 | prêts et obligations | 9 | 87 M$ | 66 M$ | 0,76 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2023-09-30 | titres de capital | 4 | 638 000 $ | 141 000 $ | 0,22 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2023-12-31 | prêts et obligations | 7 | 87 M$ | 75 M$ | 0,86 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2023-12-31 | titres de capital | 3 | 638 000 $ | 286 000 $ | 0,45 x | n.d. (non balisé) | n.d. (non balisé) |
| Core Scientific | 2024-03-31 | titres de capital | 10 | 53 M$ | 49 M$ | 0,92 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2024-09-30 | non classé | 1 | 1 M$ | 1 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2024-12-31 | non classé | 1 | 1 M$ | 1 M$ | 0,97 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2025-03-31 | non classé | 1 | 1 M$ | 1 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2025-06-30 | non classé | 1 | 1 M$ | 1 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2025-09-30 | non classé | 1 | 1 M$ | 1 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2025-12-31 | non classé | 1 | 1 M$ | 1 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2026-03-31 | non classé | 1 | 1 M$ | 1 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| AbbVie Inc. | 2026-06-30 | non classé | 1 | 1 M$ | 1 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| B. Riley Financial, Inc. | 2022-12-31 | prêts et obligations | 2 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| B. Riley Financial, Inc. | 2023-03-31 | prêts et obligations | 2 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| Banco Santander, S.A. | 2026-06-30 | prêts et obligations | 1 | 10 M$ | 10 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Barings BDC, Inc. | 2023-03-31 | non classé | 1 | 333 352 $ | 313 600 $ | 0,94 x | n.d. (non balisé) | n.d. (non balisé) |
| Barings BDC, Inc. | 2023-06-30 | non classé | 1 | 333 352 $ | 314 000 $ | 0,94 x | n.d. (non balisé) | n.d. (non balisé) |
| Barings BDC, Inc. | 2023-09-30 | non classé | 1 | 333 352 $ | 356 400 $ | 1,07 x | n.d. (non balisé) | n.d. (non balisé) |
| Barings BDC, Inc. | 2023-12-31 | non classé | 1 | 333 352 $ | 343 200 $ | 1,03 x | n.d. (non balisé) | n.d. (non balisé) |
| Barings BDC, Inc. | 2024-03-31 | non classé | 1 | 333 352 $ | 372 000 $ | 1,12 x | n.d. (non balisé) | n.d. (non balisé) |
| Barings BDC, Inc. | 2024-06-30 | non classé | 1 | 333 352 $ | 389 200 $ | 1,17 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2022-09-30 | prêts et obligations | 1 | 27 M$ | 27 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2022-12-31 | prêts et obligations | 1 | 27 M$ | 27 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2023-03-31 | prêts et obligations | 2 | 54 M$ | 54 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2023-06-30 | prêts et obligations | 2 | 53 M$ | 53 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2023-09-30 | prêts et obligations | 2 | 52 M$ | 53 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2023-12-31 | prêts et obligations | 2 | 52 M$ | 53 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2024-03-31 | prêts et obligations | 2 | 42 M$ | 42 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2024-06-30 | prêts et obligations | 2 | 41 M$ | 42 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2024-09-30 | prêts et obligations | 2 | 40 M$ | 40 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2024-12-31 | prêts et obligations | 2 | 40 M$ | 40 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2025-03-31 | prêts et obligations | 2 | 39 M$ | 39 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2025-06-30 | prêts et obligations | 2 | 33 M$ | 33 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2025-09-30 | prêts et obligations | 2 | 33 M$ | 33 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2025-12-31 | prêts et obligations | 2 | 32 M$ | 32 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2026-03-31 | prêts et obligations | 2 | 31 M$ | 31 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| BARNES & NOBLE INC | 2026-06-30 | prêts et obligations | 2 | 31 M$ | 31 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Blue Owl Capital Corporation | 2024-09-30 | non classé | 3 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| Blue Owl Technology Finance Corp. | 2024-09-30 | non classé | 2 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2022-09-30 | non classé | 2 | 74 M$ | 61 M$ | 0,82 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2022-12-31 | non classé | 4 | 134 M$ | 121 M$ | 0,91 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2023-03-31 | prêts et obligations | 3 | 13 M$ | 13 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2023-03-31 | non classé | 5 | 117 M$ | 108 M$ | 0,93 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2023-06-30 | prêts et obligations | 3 | 13 M$ | 13 M$ | 1,03 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2023-06-30 | non classé | 3 | 105 M$ | 99 M$ | 0,94 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2023-09-30 | prêts et obligations | 3 | 13 M$ | 14 M$ | 1,08 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2023-09-30 | non classé | 3 | 105 M$ | 102 M$ | 0,97 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2023-12-31 | prêts et obligations | 4 | 17 M$ | 18 M$ | 1,07 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2023-12-31 | non classé | 3 | 105 M$ | 103 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2024-03-31 | prêts et obligations | 5 | 27 M$ | 28 M$ | 1,06 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2024-03-31 | non classé | 3 | 105 M$ | 105 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2024-06-30 | prêts et obligations | 6 | 32 M$ | 33 M$ | 1,06 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2024-06-30 | non classé | 3 | 104 M$ | 104 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2024-09-30 | prêts et obligations | 6 | 39 M$ | 40 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2024-09-30 | non classé | 3 | 104 M$ | 100 M$ | 0,96 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2024-12-31 | prêts et obligations | 6 | 39 M$ | 41 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2024-12-31 | non classé | 3 | 107 M$ | 106 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2025-03-31 | prêts et obligations | 6 | 39 M$ | 40 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2025-03-31 | non classé | 3 | 108 M$ | 106 M$ | 0,97 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2025-06-30 | prêts et obligations | 6 | 39 M$ | 39 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2025-06-30 | non classé | 3 | 108 M$ | 101 M$ | 0,94 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2025-09-30 | prêts et obligations | 7 | 49 M$ | 49 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2025-09-30 | non classé | 3 | 107 M$ | 101 M$ | 0,95 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2025-12-31 | prêts et obligations | 7 | 49 M$ | 47 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2025-12-31 | non classé | 3 | 107 M$ | 97 M$ | 0,91 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2026-03-31 | prêts et obligations | 7 | 46 M$ | 41 M$ | 0,89 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2026-03-31 | non classé | 3 | 94 M$ | 76 M$ | 0,82 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2026-06-30 | prêts et obligations | 6 | 44 M$ | 34 M$ | 0,77 x | n.d. (non balisé) | n.d. (non balisé) |
| Cloudera, Inc. | 2026-06-30 | non classé | 3 | 94 M$ | 67 M$ | 0,72 x | n.d. (non balisé) | n.d. (non balisé) |
| DigitalBridge Group, Inc. | 2026-03-31 | titres de capital | 3 | 10 M$ | 8 M$ | 0,83 x | n.d. (non balisé) | n.d. (non balisé) |
| DigitalBridge Group, Inc. | 2026-06-30 | titres de capital | 3 | 10 M$ | 7 M$ | 0,72 x | n.d. (non balisé) | n.d. (non balisé) |
| DISH DBS CORP | 2022-12-31 | non classé | 2 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| DISH DBS CORP | 2023-03-31 | non classé | 3 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| DISH DBS CORP | 2023-06-30 | non classé | 3 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| DISH DBS CORP | 2023-09-30 | non classé | 2 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| DISH NETWORK CORP | 2024-06-30 | prêts et obligations | 2 | 140 000 $ | 137 000 $ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| DISH NETWORK CORP | 2024-09-30 | prêts et obligations | 2 | 147 000 $ | 168 000 $ | 1,14 x | n.d. (non balisé) | n.d. (non balisé) |
| DoorDash, Inc. | 2023-03-31 | titres de capital | 1 | 945 000 $ | 5 M$ | 5,51 x | n.d. (non balisé) | n.d. (non balisé) |
| DoorDash, Inc. | 2023-06-30 | titres de capital | 1 | 946 000 $ | 6 M$ | 6,62 x | n.d. (non balisé) | n.d. (non balisé) |
| DoorDash, Inc. | 2023-09-30 | titres de capital | 1 | 945 000 $ | 7 M$ | 6,90 x | n.d. (non balisé) | n.d. (non balisé) |
| DoorDash, Inc. | 2023-12-31 | titres de capital | 1 | 657 000 $ | 6 M$ | 8,58 x | n.d. (non balisé) | n.d. (non balisé) |
| DoorDash, Inc. | 2024-03-31 | titres de capital | 1 | 196 000 $ | 2 M$ | 11,94 x | n.d. (non balisé) | n.d. (non balisé) |
| ECHOSTAR CORP | 2024-12-31 | non classé | 1 | 73 M$ | 78 M$ | 1,07 x | n.d. (non balisé) | n.d. (non balisé) |
| ECHOSTAR CORP | 2025-06-30 | prêts et obligations | 3 | 67 M$ | 67 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| ECHOSTAR CORP | 2025-09-30 | prêts et obligations | 3 | 117 M$ | 124 M$ | 1,05 x | n.d. (non balisé) | n.d. (non balisé) |
| ECHOSTAR CORP | 2025-12-31 | prêts et obligations | 2 | 112 M$ | 136 M$ | 1,21 x | n.d. (non balisé) | n.d. (non balisé) |
| Galaxy Helios LLC | 2025-12-31 | prêts et obligations | 2 | 59 M$ | 59 M$ | 1,00 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Galaxy Helios LLC | 2026-03-31 | prêts et obligations | 2 | 73 M$ | 76 M$ | 1,05 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Galaxy Helios LLC | 2026-06-30 | prêts et obligations | 2 | 87 M$ | 88 M$ | 1,01 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2022-09-30 | non classé | 2 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2022-12-31 | non classé | 3 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2023-03-31 | prêts et obligations | 2 | 2 M$ | 2 M$ | 1,00 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2023-03-31 | non classé | 3 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2023-06-30 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2023-06-30 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2023-09-30 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2023-09-30 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2023-12-31 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2023-12-31 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2024-03-31 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2024-06-30 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2024-09-30 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2024-11-30 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2024-12-31 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-03-31 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-05-31 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-06-30 | prêts et obligations | 1 | 995 000 $ | 1 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-06-30 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-08-31 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-09-30 | prêts et obligations | 1 | 993 000 $ | 995 000 $ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-09-30 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-12-31 | prêts et obligations | 1 | 990 000 $ | 997 000 $ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2025-12-31 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2026-02-28 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2026-03-31 | prêts et obligations | 1 | 988 000 $ | 979 000 $ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2026-03-31 | non classé | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2026-05-31 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2026-06-30 | prêts et obligations | 1 | 986 000 $ | 979 000 $ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| GEN DIGITAL INC. | 2026-06-30 | non classé | 1 | 3 M$ | 3 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Hut 8 Holdings Inc. | 2023-03-31 | prêts et obligations | 2 | 19 M$ | 19 M$ | 0,98 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Hut 8 Holdings Inc. | 2023-06-30 | prêts et obligations | 2 | 17 M$ | 16 M$ | 0,98 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Hut 8 Holdings Inc. | 2023-09-30 | prêts et obligations | 2 | 14 M$ | 14 M$ | 0,99 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| IROBOT CORP | 2023-09-30 | prêts et obligations | 3 | 15 M$ | 16 M$ | 1,07 x | 17,3 % | n.d. (non balisé) |
| IROBOT CORP | 2023-12-31 | prêts et obligations | 3 | 15 M$ | 15 M$ | 1,04 x | 17,3 % | n.d. (non balisé) |
| IROBOT CORP | 2024-03-31 | prêts et obligations | 3 | 13 M$ | 13 M$ | 0,97 x | 17,3 % | n.d. (non balisé) |
| IROBOT CORP | 2024-06-30 | prêts et obligations | 3 | 13 M$ | 12 M$ | 0,96 x | 17,3 % | n.d. (non balisé) |
| IROBOT CORP | 2024-09-30 | prêts et obligations | 3 | 13 M$ | 13 M$ | 0,97 x | 17,3 % | n.d. (non balisé) |
| IROBOT CORP | 2024-12-31 | prêts et obligations | 2 | 9 M$ | 9 M$ | 0,97 x | 18,3 % | n.d. (non balisé) |
| IROBOT CORP | 2025-03-31 | prêts et obligations | 2 | 13 M$ | 12 M$ | 0,95 x | 18,8 % | n.d. (non balisé) |
| IROBOT CORP | 2025-03-31 | non classé | 2 | 0 $ | 0 $ | n.d. (dénominateur négatif ou nul) | n.d. (non balisé) | n.d. (non balisé) |
| IROBOT CORP | 2025-06-30 | prêts et obligations | 2 | 13 M$ | 7 M$ | 0,55 x | 18,8 % | n.d. (non balisé) |
| IROBOT CORP | 2025-06-30 | non classé | 2 | 0 $ | 87 000 $ | n.d. (dénominateur négatif ou nul) | n.d. (non balisé) | n.d. (non balisé) |
| IROBOT CORP | 2025-09-30 | prêts et obligations | 2 | 13 M$ | 6 M$ | 0,49 x | 19,3 % | n.d. (non balisé) |
| IROBOT CORP | 2025-09-30 | non classé | 2 | 0 $ | 45 000 $ | n.d. (dénominateur négatif ou nul) | n.d. (non balisé) | n.d. (non balisé) |
| Jabil Inc. | 2022-12-31 | non classé | 1 | 5 M$ | 5 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
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
| JPMORGAN CHASE & CO | 2024-06-30 | non classé | 1 | 10 M$ | 10 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| JPMORGAN CHASE & CO | 2024-09-30 | non classé | 1 | 10 M$ | 10 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| JPMORGAN CHASE & CO | 2024-12-31 | non classé | 1 | 10 M$ | 10 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| JPMORGAN CHASE & CO | 2025-03-31 | non classé | 1 | 10 M$ | 10 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| JPMORGAN CHASE & CO | 2025-06-30 | non classé | 1 | 11 M$ | 11 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| JPMORGAN CHASE & CO | 2025-09-30 | non classé | 1 | 11 M$ | 11 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| JPMORGAN CHASE & CO | 2025-12-31 | non classé | 1 | 11 M$ | 11 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| JPMORGAN CHASE & CO | 2026-03-31 | non classé | 1 | 11 M$ | 11 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| JPMORGAN CHASE & CO | 2026-06-30 | non classé | 1 | 11 M$ | 11 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Lenovo Group Ltd. | 2022-09-30 | non classé | 6 | 22 M$ | 22 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Lenovo Group Ltd. | 2022-12-31 | non classé | 6 | 22 M$ | 23 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| Lenovo Group Ltd. | 2023-03-31 | non classé | 6 | 22 M$ | 23 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| Lenovo Group Ltd. | 2023-06-30 | non classé | 6 | 22 M$ | 23 M$ | 1,05 x | n.d. (non balisé) | n.d. (non balisé) |
| Lenovo Group Ltd. | 2023-09-30 | non classé | 6 | 22 M$ | 23 M$ | 1,03 x | n.d. (non balisé) | n.d. (non balisé) |
| Match Group, Inc. | 2024-11-30 | prêts et obligations | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2022-12-31 | prêts et obligations | 1 | 2 M$ | 2 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2023-03-31 | prêts et obligations | 3 | 16 M$ | 16 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2023-03-31 | non classé | 1 | 8 M$ | 7 M$ | 0,95 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2023-06-30 | prêts et obligations | 3 | 21 M$ | 21 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2023-06-30 | non classé | 1 | 8 M$ | 8 M$ | 0,96 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2023-09-30 | prêts et obligations | 3 | 29 M$ | 30 M$ | 1,03 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2023-09-30 | non classé | 2 | 11 M$ | 11 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2023-12-31 | prêts et obligations | 3 | 31 M$ | 32 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2023-12-31 | non classé | 2 | 14 M$ | 14 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2024-03-31 | prêts et obligations | 3 | 26 M$ | 27 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2024-03-31 | non classé | 2 | 14 M$ | 14 M$ | 1,02 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2024-06-30 | prêts et obligations | 6 | 30 M$ | 30 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2024-06-30 | non classé | 2 | 38 M$ | 38 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2024-09-30 | prêts et obligations | 6 | 36 M$ | 36 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2024-09-30 | non classé | 2 | 37 M$ | 37 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2024-12-31 | prêts et obligations | 6 | 50 M$ | 50 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2024-12-31 | non classé | 2 | 38 M$ | 38 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2025-03-31 | prêts et obligations | 8 | 76 M$ | 74 M$ | 0,97 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2025-03-31 | non classé | 2 | 37 M$ | 35 M$ | 0,96 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2025-06-30 | prêts et obligations | 9 | 79 M$ | 78 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2025-06-30 | non classé | 3 | 41 M$ | 40 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2025-09-30 | prêts et obligations | 9 | 86 M$ | 84 M$ | 0,98 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2025-09-30 | non classé | 3 | 40 M$ | 39 M$ | 0,96 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2025-12-31 | prêts et obligations | 8 | 89 M$ | 85 M$ | 0,95 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2025-12-31 | non classé | 3 | 40 M$ | 38 M$ | 0,93 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2026-03-31 | prêts et obligations | 7 | 82 M$ | 75 M$ | 0,92 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2026-03-31 | non classé | 2 | 9 M$ | 8 M$ | 0,91 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2026-06-30 | prêts et obligations | 8 | 60 M$ | 55 M$ | 0,91 x | n.d. (non balisé) | n.d. (non balisé) |
| McAfee Corp. | 2026-06-30 | non classé | 2 | 6 M$ | 6 M$ | 0,90 x | n.d. (non balisé) | n.d. (non balisé) |
| MSD INVESTMENT CORP. | 2024-12-31 | prêts et obligations | 1 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| MSD INVESTMENT CORP. | 2025-03-31 | prêts et obligations | 1 | 25 M$ | 25 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| MSD INVESTMENT CORP. | 2025-06-30 | prêts et obligations | 1 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| MSD INVESTMENT CORP. | 2025-09-30 | prêts et obligations | 1 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| MSD INVESTMENT CORP. | 2025-12-31 | prêts et obligations | 1 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| MSD INVESTMENT CORP. | 2026-03-31 | prêts et obligations | 1 | 25 M$ | 25 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| MSD INVESTMENT CORP. | 2026-06-30 | prêts et obligations | 1 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Pear Therapeutics, Inc. | 2023-03-31 | titres de capital | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| Pear Therapeutics, Inc. | 2023-06-30 | titres de capital | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| Pear Therapeutics, Inc. | 2023-09-30 | titres de capital | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2023-09-30 | titres de capital | 1 | 220 610 $ | 401 539 $ | 1,82 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2023-12-31 | titres de capital | 1 | 220 610 $ | 395 180 $ | 1,79 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2024-03-31 | titres de capital | 1 | 220 610 $ | 416 522 $ | 1,89 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2024-06-30 | titres de capital | 1 | 220 610 $ | 430 511 $ | 1,95 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2024-09-30 | titres de capital | 1 | 220 610 $ | 462 566 $ | 2,10 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2024-12-31 | titres de capital | 1 | 220 610 $ | 528 568 $ | 2,40 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2025-03-31 | titres de capital | 1 | 220 610 $ | 528 639 $ | 2,40 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2025-06-30 | titres de capital | 1 | 220 610 $ | 598 491 $ | 2,71 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2025-09-30 | titres de capital | 1 | 220 610 $ | 627 068 $ | 2,84 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2025-12-31 | titres de capital | 1 | 220 610 $ | 631 399 $ | 2,86 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2026-03-31 | titres de capital | 1 | 220 610 $ | 605 560 $ | 2,74 x | n.d. (non balisé) | n.d. (non balisé) |
| PEOPLE INC | 2026-06-30 | titres de capital | 1 | 220 610 $ | 584 365 $ | 2,65 x | n.d. (non balisé) | n.d. (non balisé) |
| PLANET LABS PBC | 2023-03-31 | titres de capital | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| PLANET LABS PBC | 2023-06-30 | titres de capital | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| PLANET LABS PBC | 2023-09-30 | titres de capital | 1 | — | — | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) |
| PLANET LABS PBC | 2026-03-31 | titres de capital | 1 | 2 M$ | 2 M$ | 1,11 x | n.d. (non balisé) | n.d. (non balisé) |
| PLANET LABS PBC | 2026-06-30 | titres de capital | 1 | 2 M$ | 2 M$ | 1,31 x | n.d. (non balisé) | n.d. (non balisé) |
| Rackspace Technology, Inc. | 2026-03-31 | prêts et obligations | 1 | 492 494 $ | 493 586 $ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Snowflake Inc. | 2026-03-31 | titres de capital | 2 | 470 000 $ | 270 000 $ | 0,57 x | n.d. (non balisé) | n.d. (non balisé) |
| Snowflake Inc. | 2026-06-30 | titres de capital | 2 | 470 000 $ | 455 000 $ | 0,97 x | n.d. (non balisé) | n.d. (non balisé) |
| Synapse Financial Technologies, Inc. | 2025-06-30 | titres de capital | 1 | 23 000 $ | 0 $ | 0,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Synapse Financial Technologies, Inc. | 2025-06-30 | non classé | 1 | 727 000 $ | 56 000 $ | 0,08 x | n.d. (non balisé) | n.d. (non balisé) |
| Tempus AI, Inc. | 2024-03-31 | prêts et obligations | 3 | 104 M$ | 104 M$ | 1,00 x | 23,9 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2024-03-31 | titres de capital | 1 | 2 M$ | 2 M$ | 1,06 x | n.d. (non balisé) | n.d. (non balisé) |
| Tempus AI, Inc. | 2024-06-30 | prêts et obligations | 3 | 104 M$ | 104 M$ | 1,00 x | 24,0 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2024-09-30 | prêts et obligations | 3 | 105 M$ | 105 M$ | 1,00 x | 23,9 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2024-12-31 | prêts et obligations | 3 | 106 M$ | 106 M$ | 1,00 x | 25,3 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2025-03-31 | prêts et obligations | 4 | 138 M$ | 137 M$ | 0,99 x | 25,9 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2025-06-30 | prêts et obligations | 4 | 139 M$ | 142 M$ | 1,02 x | 25,9 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2025-09-30 | prêts et obligations | 1 | 32 M$ | 32 M$ | 1,00 x | 26,5 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2025-12-31 | prêts et obligations | 1 | 32 M$ | 32 M$ | 1,00 x | 27,3 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2026-03-31 | prêts et obligations | 1 | 32 M$ | 32 M$ | 1,00 x | 27,2 % | n.d. (non balisé) |
| Tempus AI, Inc. | 2026-06-30 | titres de capital | 1 | 2 M$ | 4 M$ | 1,84 x | n.d. (non balisé) | n.d. (non balisé) |
| Trinity Capital Inc. | 2024-12-31 | prêts et obligations | 1 | 30 M$ | 29 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| Trinity Capital Inc. | 2025-03-31 | prêts et obligations | 1 | 30 M$ | 30 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Trinity Capital Inc. | 2025-06-30 | prêts et obligations | 1 | 30 M$ | 30 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Trinity Capital Inc. | 2025-09-30 | prêts et obligations | 1 | 30 M$ | 30 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Trinity Capital Inc. | 2025-12-31 | prêts et obligations | 1 | 30 M$ | 30 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Trinity Capital Inc. | 2026-03-31 | prêts et obligations | 1 | 30 M$ | 30 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Trinity Capital Inc. | 2026-06-30 | prêts et obligations | 1 | 30 M$ | 30 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Twitter, Inc. | 2025-03-31 | prêts et obligations | 2 | 113 M$ | 119 M$ | 1,06 x | n.d. (non balisé) | n.d. (non balisé) |
| Twitter, Inc. | 2025-06-30 | prêts et obligations | 1 | 91 M$ | 94 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| Twitter, Inc. | 2025-09-30 | prêts et obligations | 1 | 91 M$ | 95 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| Twitter, Inc. | 2025-12-31 | prêts et obligations | 1 | 91 M$ | 95 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| U.S. BANK NATIONAL ASSOCIATION | 2023-12-31 | non classé | 3 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| UBER TECHNOLOGIES, INC | 2023-03-31 | prêts et obligations | 2 | 5 M$ | 5 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| UBER TECHNOLOGIES, INC | 2023-03-31 | non classé | 1 | 2 M$ | 2 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| UBER TECHNOLOGIES, INC | 2023-06-30 | prêts et obligations | 1 | 4 M$ | 4 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| UBER TECHNOLOGIES, INC | 2023-09-30 | non classé | 2 | 5 M$ | 5 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| UBER TECHNOLOGIES, INC | 2023-12-31 | non classé | 2 | 4 M$ | 4 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| UBER TECHNOLOGIES, INC | 2024-03-31 | non classé | 2 | 3 M$ | 3 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| UBER TECHNOLOGIES, INC | 2024-06-30 | prêts et obligations | 1 | 2 M$ | 2 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| UBER TECHNOLOGIES, INC | 2024-06-30 | non classé | 1 | 2 M$ | 2 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| VMware, Inc. | 2022-12-31 | non classé | 1 | 3 M$ | 3 M$ | 0,99 x | n.d. (non balisé) | n.d. (non balisé) |
| X.AI Corp. | 2025-09-30 | prêts et obligations | 1 | 71 M$ | 72 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| X.AI Corp. | 2025-12-31 | prêts et obligations | 1 | 71 M$ | 73 M$ | 1,03 x | n.d. (non balisé) | n.d. (non balisé) |
| X.AI LLC | 2025-06-30 | prêts et obligations | 3 | 111 M$ | 111 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| X.AI LLC | 2025-09-30 | prêts et obligations | 4 | 54 M$ | 56 M$ | 1,04 x | n.d. (non balisé) | n.d. (non balisé) |
| X.AI LLC | 2025-12-31 | prêts et obligations | 4 | 33 M$ | 35 M$ | 1,05 x | n.d. (non balisé) | n.d. (non balisé) |
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
| XPLR Infrastructure, LP | 2025-06-30 | non classé | 1 | 88 000 $ | 82 000 $ | 0,93 x | n.d. (non balisé) | n.d. (non balisé) |
| XPLR Infrastructure, LP | 2025-09-30 | non classé | 1 | 87 000 $ | 102 000 $ | 1,17 x | n.d. (non balisé) | n.d. (non balisé) |
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
| Galaxy | 2025-09-30 | prêts et obligations | 2 | 4 M$ | 4 M$ | 1,00 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Galaxy | 2025-12-31 | prêts et obligations | 2 | 9 M$ | 9 M$ | 1,02 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Galaxy | 2026-03-31 | prêts et obligations | 2 | 11 M$ | 11 M$ | 1,01 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Galaxy | 2026-06-30 | prêts et obligations | 2 | 13 M$ | 13 M$ | 1,00 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Intel | 2025-06-30 | prêts et obligations | 1 | 2 M$ | 2 M$ | 1,01 x | n.d. (non balisé) | n.d. (non balisé) |
| Nscale | 2025-09-30 | titres de capital | 10 | 50 M$ | 50 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Nscale | 2025-12-31 | titres de capital | 10 | 50 M$ | 50 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| Nscale | 2026-03-31 | prêts et obligations | 5 | 11 M$ | 11 M$ | 1,00 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Nscale | 2026-03-31 | titres de capital | 10 | 50 M$ | 91 M$ | 1,83 x | n.d. (non balisé) | n.d. (non balisé) |
| Nscale | 2026-06-30 | prêts et obligations | 6 | 8 M$ | 9 M$ | 1,10 x (partiel) | n.d. (non balisé) | n.d. (non balisé) |
| Nscale | 2026-06-30 | titres de capital | 10 | 50 M$ | 87 M$ | 1,74 x | n.d. (non balisé) | n.d. (non balisé) |
| SoftBank | 2025-12-31 | prêts et obligations | 2 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| SoftBank | 2026-03-31 | prêts et obligations | 2 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
| SoftBank | 2026-06-30 | prêts et obligations | 2 | 25 M$ | 25 M$ | 1,00 x | n.d. (non balisé) | n.d. (non balisé) |
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

Appartenances datées : DigitalBridge Group, Inc. appartient au groupe SoftBank : avant cette date, la vue `as_known` le garde comme groupe propre. Hut 8 Holdings Inc. appartient au groupe Hut 8 : avant cette date, la vue `as_known` le garde comme groupe propre. VMware, Inc. appartient au groupe Broadcom : avant cette date, la vue `as_known` le garde comme groupe propre. VMware, Inc. appartient au groupe Dell : avant cette date, la vue `as_known` le garde comme groupe propre. X.AI Corp. appartient au groupe SpaceX en vue `revised` depuis le 2023-01-01 (contrôle commun), en vue `as_known` depuis le 2026-02-02 : avant cette date, la vue `as_known` le garde comme groupe propre. X.AI LLC appartient au groupe SpaceX en vue `revised` depuis le 2023-01-01 (contrôle commun), en vue `as_known` depuis le 2026-02-02 : avant cette date, la vue `as_known` le garde comme groupe propre. X Corp. appartient au groupe SpaceX en vue `revised` depuis le 2023-01-01 (contrôle commun), en vue `as_known` depuis le 2026-02-02 : avant cette date, la vue `as_known` le garde comme groupe propre. X Holdings Corp. appartient au groupe SpaceX en vue `revised` depuis le 2023-01-01 (contrôle commun), en vue `as_known` depuis le 2026-02-02 : avant cette date, la vue `as_known` le garde comme groupe propre.

Identifiants de position écartés parce qu'ils nomment deux émetteurs : 54.

## Fragilité du financement : portefeuilles entiers des BDC (bloc `lender_portfolio`, D-0045)

Toutes les BDC des archives en cache, sans sélection ; un véhicule est un déclarant, et rien ne s'additionne entre véhicules. Vue `as_known` : le premier dépôt d'un véhicule pour une date de bilan. Juste valeur ÷ coût porte sur les prêts. Les intérêts capitalisés (taux PIK pondéré par le principal, sur le taux total) et les engagements non tirés sont des bornes basses : une position sans balise compte sans PIK ou sans engagement. Les événements F11 (juste valeur ÷ coût en baisse deux trimestres de suite) et F12 (intérêts capitalisés en hausse deux trimestres de suite) ont été fixés avant le calcul (D-0045). Les plateformes Blue Owl (« Blue Owl » ou « Owl Rock »), Apollo (« Apollo ») et Blackstone (« Blackstone ») réunissent les véhicules dont la dénomination EDGAR, actuelle ou ancienne, porte la marque : des regroupements de présentation, pas des groupes économiques.

- Univers : 198 véhicules, 2 088 couples véhicule × date de bilan. Mesures déterminées : juste valeur ÷ coût 1 904, intérêts capitalisés 1 078, prêts sans accumulation d'intérêts 0, engagements non tirés 847, part logiciel 3.
- Les prêts sans accumulation d'intérêts ne sont pas balisés dans `num` (ni axe de statut ni membre) : la mesure et F13 restent non déterminables. Le secteur n'est presque jamais balisé : la part logiciel aussi. Il faudrait lire les notes des portefeuilles (niveau 2).

**Véhicules Blue Owl**

| Véhicule | Dernier bilan | Juste valeur ÷ coût | — un an plus tôt | Intérêts capitalisés | — un an plus tôt | Engagements non tirés ÷ portefeuille | F11 (dates) | F12 (dates) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| BLUE OWL CAPITAL CORP II | 2026-06-30 | 88,56 % | 96,94 % | n.d. (non balisé) | n.d. (non balisé) | ≥ 7,09 % | 2024-03-31, 2024-06-30, 2025-09-30, 2026-06-30 | aucune |
| BLUE OWL CAPITAL CORP | 2026-06-30 | 96,30 % (partiel) | 98,63 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | ≥ 7,69 % | 2024-06-30, 2024-09-30, 2024-12-31, 2025-09-30 | aucune |
| BLUE OWL TECHNOLOGY FINANCE CORP. | 2026-06-30 | 97,61 % (partiel) | 99,90 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | ≥ 11,94 % | 2024-06-30, 2025-12-31, 2026-03-31, 2026-06-30 | aucune |
| BLUE OWL CAPITAL CORP III | 2024-09-30 | 99,80 % | 99,77 % | n.d. (non balisé) | n.d. (non balisé) | ≥ 12,98 % | 2024-09-30 | aucune |
| BLUE OWL CREDIT INCOME CORP. | 2026-06-30 | 98,17 % (partiel) | 99,50 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | ≥ 12,01 % | 2024-06-30, 2024-09-30, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30, 2026-06-30 | aucune |
| BLUE OWL TECHNOLOGY INCOME CORP. | 2026-06-30 | 96,06 % (partiel) | 100,02 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | ≥ 9,62 % | 2025-03-31, 2025-12-31, 2026-03-31, 2026-06-30 | aucune |
| BLUE OWL TECHNOLOGY FINANCE CORP. II | 2024-12-31 | 100,21 % (partiel) | 100,66 % | n.d. (non balisé) | n.d. (non balisé) | ≥ 12,01 % | aucune | aucune |

**Véhicules Apollo**

| Véhicule | Dernier bilan | Juste valeur ÷ coût | — un an plus tôt | Intérêts capitalisés | — un an plus tôt | Engagements non tirés ÷ portefeuille | F11 (dates) | F12 (dates) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| MIDCAP FINANCIAL INVESTMENT CORP | 2026-06-30 | 94,81 % (partiel) | 98,57 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) | 2024-09-30, 2024-12-31, 2025-12-31, 2026-03-31, 2026-06-30 | aucune |
| APOLLO DEBT SOLUTIONS BDC | 2026-06-30 | 98,98 % (partiel) | 101,15 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) | 2025-12-31, 2026-03-31 | aucune |
| MIDCAP APOLLO INSTITUTIONAL PRIVATE LENDING | 2026-06-30 | 96,90 % (partiel) | 99,03 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | ≥ 6,41 % | 2024-12-31, 2025-09-30, 2025-12-31, 2026-03-31, 2026-06-30 | aucune |
| APOLLO ORIGINATION II (LEVERED) CAPITAL TRUST | 2026-06-30 | 99,22 % | 99,98 % | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) | 2026-03-31 | aucune |
| APOLLO ORIGINATION II (UL) CAPITAL TRUST | 2026-06-30 | 99,23 % | 99,98 % | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) | 2026-03-31 | aucune |

**Véhicules Blackstone**

| Véhicule | Dernier bilan | Juste valeur ÷ coût | — un an plus tôt | Intérêts capitalisés | — un an plus tôt | Engagements non tirés ÷ portefeuille | F11 (dates) | F12 (dates) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| BLACKSTONE SECURED LENDING FUND | 2026-06-30 | 96,34 % | 100,27 % | ≥ 5,33 % | ≥ 5,41 % | ≥ 10,38 % | 2023-03-31, 2023-06-30, 2025-09-30, 2025-12-31, 2026-03-31, 2026-06-30 | 2023-03-31, 2024-06-30, 2024-09-30, 2024-12-31, 2025-03-31 |
| BLACKSTONE PRIVATE CREDIT FUND | 2026-06-30 | 96,64 % | 99,48 % | ≥ 4,79 % | ≥ 5,14 % | ≥ 22,70 % | 2026-06-30 | 2023-03-31, 2023-12-31, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30 |
| BLACKSTONE PRIVATE REAL ESTATE CREDIT & INCOME FUND | 2026-06-30 | 100,38 % | 100,50 % | ≥ 0,00 % | ≥ 0,00 % | n.d. (non balisé) | 2026-03-31, 2026-06-30 | aucune |

**Repères nommés d'avance**

| Véhicule | Dernier bilan | Juste valeur ÷ coût | — un an plus tôt | Intérêts capitalisés | — un an plus tôt | Engagements non tirés ÷ portefeuille | F11 (dates) | F12 (dates) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| ARES CAPITAL CORP | 2026-06-30 | 96,66 % (partiel) | 97,89 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | ≥ 14,47 % | 2023-03-31, 2025-03-31, 2026-06-30 | aucune |
| BLACKSTONE SECURED LENDING FUND | 2026-06-30 | 96,34 % | 100,27 % | ≥ 5,33 % | ≥ 5,41 % | ≥ 10,38 % | 2023-03-31, 2023-06-30, 2025-09-30, 2025-12-31, 2026-03-31, 2026-06-30 | 2023-03-31, 2024-06-30, 2024-09-30, 2024-12-31, 2025-03-31 |
| BLACKSTONE PRIVATE CREDIT FUND | 2026-06-30 | 96,64 % | 99,48 % | ≥ 4,79 % | ≥ 5,14 % | ≥ 22,70 % | 2026-06-30 | 2023-03-31, 2023-12-31, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30 |
| GOLUB CAPITAL BDC, INC. | 2026-06-30 | 98,25 % | 99,56 % | ≥ 6,32 % | ≥ 4,72 % | n.d. (non balisé) | 2026-03-31 | 2023-03-31, 2024-03-31, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30, 2025-12-31, 2026-03-31, 2026-06-30 |
| FS KKR CAPITAL CORP | 2026-06-30 | 91,01 % (partiel) | 95,58 % (partiel) | n.d. (non balisé) | n.d. (non balisé) | ≥ 6,50 % | 2023-03-31, 2026-03-31, 2026-06-30 | aucune |
| HPS CORPORATE LENDING FUND | 2026-06-30 | 99,08 % | 101,38 % | ≥ 4,98 % | n.d. (non balisé) | ≥ 10,97 % | 2025-12-31 | 2023-09-30, 2023-12-31, 2024-03-31 |

Quartiles de l'univers par date de bilan (premier quartile / médiane / troisième quartile ; des repères, jamais des totaux) :

| Date du bilan | Véhicules | Juste valeur ÷ coût | Intérêts capitalisés (bornes basses) |
| --- | ---: | --- | --- |
| 2024-09-30 | 131 | 97,56 % / 99,42 % / 100,42 % | 0,23 % / 2,27 % / 3,60 % |
| 2024-12-31 | 133 | 97,38 % / 99,34 % / 100,21 % | 0,43 % / 2,21 % / 3,30 % |
| 2025-03-31 | 134 | 97,44 % / 99,47 % / 100,09 % | 0,00 % / 1,53 % / 4,08 % |
| 2025-06-30 | 145 | 97,59 % / 99,67 % / 100,33 % | 0,14 % / 1,74 % / 3,84 % |
| 2025-09-30 | 148 | 97,58 % / 99,55 % / 100,34 % | 0,17 % / 1,83 % / 4,17 % |
| 2025-12-31 | 155 | 97,47 % / 99,58 % / 100,25 % | 0,25 % / 2,64 % / 4,93 % |
| 2026-03-31 | 155 | 96,64 % / 98,64 % / 99,51 % | 0,79 % / 2,94 % / 5,22 % |
| 2026-06-30 | 157 | 96,66 % / 98,72 % / 99,43 % | 0,65 % / 3,18 % / 5,33 % |

Exclusions du bloc : `invalid_aggregate` 20, `parse_failed` 16 (lignes « Total » de portefeuilles et lignes illisibles, par archive).

## Fragilité du financement : passif des BDC et rachats (bloc `lender_liabilities`, D-0047)

Mêmes véhicules que le bloc `lender_portfolio`, sans sélection ni somme entre véhicules. Le ratio de couverture est celui que publie le véhicule (loi de 1940 : actif net plus dette de premier rang, sur cette dette) ; dette ÷ actif net s'en déduit, et passif total ÷ actif net le majore. Les offres de rachat sont les SC TO-I des véhicules non cotés : parts apportées, parts acceptées et plafond de l'offre se lisent dans l'amendement final. Événements fixés avant tout calcul : F14 (couverture en baisse deux trimestres de suite), F15 (offre réduite au prorata), F16 (interruption d'un programme régulier d'offres). Les demandes ne disent pas qui demande.

- Bilans : 209 véhicules, 2 380 couples véhicule × date. Couverture publiée et retenue 889 fois ; non balisée 1 444 ; contraire à l'identité du bilan, souvent le seuil légal balisé à la place du ratio, 43 ; hors échelle 4. Passif ÷ actif net calculé 2 271 fois.
- Offres de rachat de parts dans la fenêtre : 622, chez 68 véhicules. F15 tranché : 562 ; réduites au prorata 84 ; encore ouvertes à `as_of` 23 ; résultat non publié 37 (dont les parts acceptées non chiffrées).

**Levier des véhicules Blue Owl**

| Véhicule | Dernier bilan | Couverture | Dette ÷ actif net | — un an plus tôt | Passif ÷ actif net | F14 (dernières dates) |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| BLUE OWL CAPITAL CORP II | 2026-06-30 | 473 % | 0,27 x | 0,70 x | 0,30 x | 2024-06-30, 2024-09-30 |
| BLUE OWL CAPITAL CORP | 2026-06-30 | 187 % | 1,15 x | 1,23 x | 1,18 x | 2023-03-31, 2024-09-30 |
| BLUE OWL TECHNOLOGY FINANCE CORP. | 2026-06-30 | 203 % | 0,97 x | 0,61 x | 1,00 x | 2025-12-31, 2026-03-31, 2026-06-30 |
| BLUE OWL CAPITAL CORP III | 2024-09-30 | 176 % | 1,32 x | 0,92 x | 1,34 x | 2024-03-31, 2024-06-30 |
| BLUE OWL CREDIT INCOME CORP. | 2026-06-30 | 207 % | 0,93 x | 0,87 x | 0,99 x | 2026-03-31, 2026-06-30 |
| BLUE OWL TECHNOLOGY INCOME CORP. | 2026-06-30 | 215 % | 0,87 x | 0,79 x | 0,93 x | 2024-12-31, 2025-09-30, 2026-06-30 |
| BLUE OWL TECHNOLOGY FINANCE CORP. II | 2024-12-31 | 214 % | 0,88 x | 1,14 x | 0,91 x | aucune |

**Levier des véhicules Apollo**

| Véhicule | Dernier bilan | Couverture | Dette ÷ actif net | — un an plus tôt | Passif ÷ actif net | F14 (dernières dates) |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| MIDCAP FINANCIAL INVESTMENT CORP | 2026-06-30 | 163 % | 1,59 x | 1,52 x | 1,60 x | 2025-06-30, 2026-03-31 |
| APOLLO DEBT SOLUTIONS BDC | 2026-06-30 | 214 % | 0,88 x | 0,54 x | 0,99 x | 2025-12-31, 2026-03-31, 2026-06-30 |
| MIDCAP APOLLO INSTITUTIONAL PRIVATE LENDING | 2026-06-30 | 165 % | 1,54 x | 1,47 x | 1,57 x | 2024-12-31, 2026-03-31, 2026-06-30 |
| APOLLO ORIGINATION II (LEVERED) CAPITAL TRUST | 2026-06-30 | 202 % | 0,98 x | 1,05 x | 0,99 x | 2025-09-30, 2025-12-31 |
| APOLLO ORIGINATION II (UL) CAPITAL TRUST | 2026-06-30 | n.d. (non balisé) | n.d. (non balisé) | n.d. (non balisé) | 0,01 x | aucune |

**Levier des véhicules Blackstone**

| Véhicule | Dernier bilan | Couverture | Dette ÷ actif net | — un an plus tôt | Passif ÷ actif net | F14 (dernières dates) |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| BLACKSTONE SECURED LENDING FUND | 2026-06-30 | 178 % | 1,28 x | 1,13 x | 1,32 x | 2025-03-31, 2025-12-31, 2026-03-31 |
| BLACKSTONE PRIVATE CREDIT FUND | 2026-06-30 | 221 % | 0,82 x | 0,68 x | 0,90 x | 2024-12-31, 2026-03-31, 2026-06-30 |
| BLACKSTONE PRIVATE REAL ESTATE CREDIT & INCOME FUND | 2026-06-30 | 193 % | 1,07 x | 1,23 x | 1,08 x | 2026-03-31 |

**Levier des repères nommés d'avance**

| Véhicule | Dernier bilan | Couverture | Dette ÷ actif net | — un an plus tôt | Passif ÷ actif net | F14 (dernières dates) |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| ARES CAPITAL CORP | 2026-06-30 | 186 % | 1,16 x | 1,01 x | 1,20 x | 2025-12-31, 2026-03-31, 2026-06-30 |
| BLACKSTONE SECURED LENDING FUND | 2026-06-30 | 178 % | 1,28 x | 1,13 x | 1,32 x | 2025-03-31, 2025-12-31, 2026-03-31 |
| BLACKSTONE PRIVATE CREDIT FUND | 2026-06-30 | 221 % | 0,82 x | 0,68 x | 0,90 x | 2024-12-31, 2026-03-31, 2026-06-30 |
| GOLUB CAPITAL BDC, INC. | 2026-06-30 | 180 % | 1,24 x | 1,30 x | 1,25 x | 2023-06-30, 2024-12-31, 2026-03-31 |
| FS KKR CAPITAL CORP | 2026-06-30 | 179 % | 1,27 x | 1,30 x | 1,31 x | 2024-09-30, 2025-06-30, 2026-03-31 |
| HPS CORPORATE LENDING FUND | 2026-06-30 | 198 % | 1,02 x | 0,94 x | 1,09 x | 2025-06-30, 2025-09-30, 2025-12-31 |

Quartiles de l'univers par date de bilan (premier quartile / médiane / troisième quartile ; des repères, jamais des totaux). Dette ÷ actif net sur les seuls véhicules qui publient leur couverture :

| Date du bilan | Véhicules (couverture) | Dette ÷ actif net | Véhicules (passif) | Passif ÷ actif net |
| --- | ---: | --- | ---: | --- |
| 2025-03-31 | 64 | 0,71 x / 0,98 x / 1,14 x | 162 | 0,67 x / 0,99 x / 1,27 x |
| 2025-06-30 | 66 | 0,71 x / 0,98 x / 1,21 x | 162 | 0,62 x / 1,01 x / 1,30 x |
| 2025-09-30 | 70 | 0,79 x / 1,02 x / 1,19 x | 166 | 0,67 x / 1,05 x / 1,32 x |
| 2025-12-31 | 73 | 0,82 x / 1,06 x / 1,26 x | 173 | 0,79 x / 1,11 x / 1,35 x |
| 2026-03-31 | 74 | 0,85 x / 1,02 x / 1,20 x | 173 | 0,74 x / 1,09 x / 1,32 x |
| 2026-06-30 | 73 | 0,86 x / 1,03 x / 1,22 x | 171 | 0,77 x / 1,08 x / 1,31 x |

**Rachats, par trimestre d'expiration des offres (tous les véhicules qui en font)**

| Trimestre | Offres | F15 tranché | Réduites au prorata (F15) | Demande médiane ÷ plafond | Offres au-delà du plafond |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 T4 | 15 | 14 | 1 | 0,35 (11 offres) | 2 |
| 2023 T1 | 21 | 20 | 4 | 0,67 (15 offres) | 3 |
| 2023 T2 | 23 | 21 | 4 | 0,45 (15 offres) | 2 |
| 2023 T3 | 26 | 24 | 4 | 0,17 (17 offres) | 1 |
| 2023 T4 | 30 | 28 | 4 | 0,14 (21 offres) | 1 |
| 2024 T1 | 34 | 32 | 4 | 0,11 (25 offres) | 3 |
| 2024 T2 | 35 | 33 | 5 | 0,15 (26 offres) | 3 |
| 2024 T3 | 39 | 38 | 5 | 0,16 (31 offres) | 1 |
| 2024 T4 | 41 | 40 | 4 | 0,13 (33 offres) | 1 |
| 2025 T1 | 44 | 42 | 3 | 0,10 (34 offres) | 2 |
| 2025 T2 | 44 | 42 | 4 | 0,14 (36 offres) | 3 |
| 2025 T3 | 48 | 47 | 3 | 0,20 (41 offres) | 3 |
| 2025 T4 | 49 | 48 | 3 | 0,32 (41 offres) | 3 |
| 2026 T1 | 51 | 50 | 11 | 0,58 (39 offres) | 8 |
| 2026 T2 | 51 | 50 | 18 | 0,64 (36 offres) | 13 |
| 2026 T3 | 70 | 33 | 7 | 0,22 (21 offres) | 2 |
| 2026 T4 | 1 | 0 | 0 | — (0 offres) | 0 |

La demande rapporte les parts apportées au plafond de l'offre (en général 5 % des parts) ; elle n'est calculée que si l'amendement ou l'offre donne ce plafond dans la même unité.

**Rachats des véhicules Blue Owl (six dernières offres)**

| Véhicule | Expiration | Demande ÷ plafond | Acceptées ÷ apportées | F15 |
| --- | --- | ---: | ---: | --- |
| Blue Owl Capital Corp II | 2024-06-24 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Capital Corp II | 2024-09-23 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Capital Corp II | 2024-12-23 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Capital Corp II | 2025-03-24 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Capital Corp II | 2025-06-23 | 1,08 x | 100 % | servie en entier |
| Blue Owl Capital Corp II | 2025-09-22 | 1,19 x | 100 % | servie en entier |
| Blue Owl Credit Income Corp. | 2025-06-30 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Credit Income Corp. | 2025-09-30 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Credit Income Corp. | 2025-12-31 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Credit Income Corp. | 2026-03-31 | 4,38 x | 23 % | réduite |
| Blue Owl Credit Income Corp. | 2026-06-30 | 3,76 x | 27 % | réduite |
| Blue Owl Credit Income Corp. | 2026-08-26 | n.d. (période non écoulée à la date de coupure) | n.d. (période non écoulée à la date de coupure) | n.d. (offre encore ouverte) |
| Blue Owl Technology Income Corp. | 2025-06-30 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Technology Income Corp. | 2025-09-30 | n.d. (non publié) | 100 % | servie en entier |
| Blue Owl Technology Income Corp. | 2026-01-08 | 0,77 x | 100 % | servie en entier |
| Blue Owl Technology Income Corp. | 2026-03-31 | 8,08 x | 14 % | réduite |
| Blue Owl Technology Income Corp. | 2026-06-30 | 7,62 x | 13 % | réduite |
| Blue Owl Technology Income Corp. | 2026-08-26 | n.d. (période non écoulée à la date de coupure) | n.d. (période non écoulée à la date de coupure) | n.d. (offre encore ouverte) |

**Rachats des véhicules Apollo (six dernières offres)**

| Véhicule | Expiration | Demande ÷ plafond | Acceptées ÷ apportées | F15 |
| --- | --- | ---: | ---: | --- |
| Apollo Debt Solutions BDC | 2025-06-16 | 0,37 x | 100 % | servie en entier |
| Apollo Debt Solutions BDC | 2025-09-15 | 0,61 x | 100 % | servie en entier |
| Apollo Debt Solutions BDC | 2025-12-15 | 0,97 x | 100 % | servie en entier |
| Apollo Debt Solutions BDC | 2026-03-16 | 2,21 x | 45 % | réduite |
| Apollo Debt Solutions BDC | 2026-06-15 | 3,36 x | 30 % | réduite |
| Apollo Debt Solutions BDC | 2026-08-14 | n.d. (période non écoulée à la date de coupure) | n.d. (période non écoulée à la date de coupure) | n.d. (offre encore ouverte) |

**Rachats des véhicules Blackstone (six dernières offres)**

| Véhicule | Expiration | Demande ÷ plafond | Acceptées ÷ apportées | F15 |
| --- | --- | ---: | ---: | --- |
| Blackstone Private Credit Fund | 2025-05-30 | 0,53 x | 100 % | servie en entier |
| Blackstone Private Credit Fund | 2025-08-29 | 0,36 x | 100 % | servie en entier |
| Blackstone Private Credit Fund | 2025-12-02 | 0,91 x | 100 % | servie en entier |
| Blackstone Private Credit Fund | 2026-03-02 | 1,39 x | 100 % | servie en entier |
| Blackstone Private Credit Fund | 2026-05-29 | 2,06 x | 49 % | réduite |
| Blackstone Private Credit Fund | 2026-08-04 | n.d. (non publié) | n.d. (non publié) | n.d. (résultat non publié) |

**Rachats des repères non cotés (six dernières offres)**

| Véhicule | Expiration | Demande ÷ plafond | Acceptées ÷ apportées | F15 |
| --- | --- | ---: | ---: | --- |
| Blackstone Private Credit Fund | 2025-05-30 | 0,53 x | 100 % | servie en entier |
| Blackstone Private Credit Fund | 2025-08-29 | 0,36 x | 100 % | servie en entier |
| Blackstone Private Credit Fund | 2025-12-02 | 0,91 x | 100 % | servie en entier |
| Blackstone Private Credit Fund | 2026-03-02 | 1,39 x | 100 % | servie en entier |
| Blackstone Private Credit Fund | 2026-05-29 | 2,06 x | 49 % | réduite |
| Blackstone Private Credit Fund | 2026-08-04 | n.d. (non publié) | n.d. (non publié) | n.d. (résultat non publié) |
| HPS Corporate Lending Fund | 2025-05-30 | 0,39 x | 100 % | servie en entier |
| HPS Corporate Lending Fund | 2025-08-29 | 0,33 x | 100 % | servie en entier |
| HPS Corporate Lending Fund | 2025-12-02 | 0,82 x | 100 % | servie en entier |
| HPS Corporate Lending Fund | 2026-03-04 | 1,85 x | 54 % | réduite |
| HPS Corporate Lending Fund | 2026-06-08 | 2,66 x | 38 % | réduite |
| HPS Corporate Lending Fund | 2026-08-10 | n.d. (période non écoulée à la date de coupure) | n.d. (période non écoulée à la date de coupure) | n.d. (offre encore ouverte) |

**F16, interruptions d'un programme régulier d'offres**

- Cellules : 6 événements, 423 sans événement, 44 dont les 120 jours ne sont pas écoulés.
- Audax Credit BDC Inc. : dernière offre le 2023-07-12, aucune dans les 120 jours (événement daté du 2023-11-09). Aucun 8-K lu n'en donne la cause.
- MSC INCOME FUND, INC. : dernière offre le 2024-09-26, aucune dans les 120 jours (événement daté du 2025-01-24). 8-K lus : suspension des rachats (2024-11-14 : suspension des rachats en vue d'une cotation).
- Blue Owl Capital Corp II : dernière offre le 2025-08-18, aucune dans les 120 jours (événement daté du 2025-12-16). 8-K lus : fusion abandonnée (2025-11-19 : fusion avec Blue Owl Capital Corporation abandonnée le 18 novembre 2025) ; accord de fusion (2025-11-05 : accord de fusion avec Blue Owl Capital Corporation (cotée), 5 novembre 2025) ; accord de fusion (2025-11-05 : communiqué de l'accord de fusion) ; suspension des rachats (2025-11-05 : plus d'offre de rachat avant la fusion).
- Stellus Private Credit BDC : dernière offre le 2026-03-23, aucune dans les 120 jours (événement daté du 2026-07-21). Aucun 8-K lu n'en donne la cause.
- Hancock Park Corporate Income, Inc. : dernière offre le 2026-05-22, aucune dans les 120 jours (événement daté du 2026-09-19). 8-K lus : autre annonce (2026-06-30 : fin d'une ligne de crédit bancaire peu utilisée ; aucune mention des offres de rachat).
- Steele Creek Capital Corp : dernière offre le 2026-05-29, aucune dans les 120 jours (événement daté du 2026-09-26). 8-K lus : autre annonce (2026-08-25 : cession de 75,8 % du portefeuille pour rembourser la ligne de crédit) ; autre annonce (2026-08-25 : plan de désendettement en vue d'une liquidation probable).

**Annonces des véhicules Blue Owl lues dans leurs 8-K (les plus récentes d'abord, plafond de 40 unités)**

- 2026-10-02, Blue Owl Credit Income Corp. — autre annonce : demande estimée du troisième trimestre 2026 (16,8 % des parts), servie au prorata à environ 30 % ; publiée hors SC TO-I. « the Fund received an estimated third-quarter total repurchase request of $3.1 billion, or 16.8% »
- 2026-10-02, Blue Owl Credit Income Corp. — autre annonce : même annonce, FAQ. « All repurchase requests will be satisfied on a pro rata basis, representing approximately 30% of total shares tendered »
- 2026-10-02, Blue Owl Technology Income Corp. — autre annonce : demande estimée du troisième trimestre 2026 (39,0 % des parts), servie au prorata à environ 13 % ; publiée hors SC TO-I. « OTIC received an estimated total repurchase request of 39.0% »
- 2026-07-02, Blue Owl Credit Income Corp. — autre annonce : demande estimée du deuxième trimestre 2026 (18,8 %), servie au prorata à environ 27 %. « OCIC received an estimated total repurchase request of 18.8% »
- 2026-07-02, Blue Owl Technology Income Corp. — autre annonce : demande estimée du deuxième trimestre 2026 (38,1 %), servie au prorata à environ 13 %. « OTIC received an estimated total repurchase request of 38.1% »
- 2026-04-23, Blue Owl Credit Income Corp. — autre annonce : levier net après règlement de l'offre du premier trimestre 2026. « Pro-forma for the settlement of our most recent tender offer the net debt-to-equity leverage was 0.88x as of March 31, 2026. »
- 2026-04-23, Blue Owl Technology Income Corp. — autre annonce : levier net après règlement de l'offre du premier trimestre 2026. « Pro-forma for the settlement of our most recent tender offer, the net debt-to-equity leverage ratio was 0.85x as of March 31, 2026. »
- 2026-04-02, Blue Owl Credit Income Corp. — autre annonce : le gestionnaire décrit une vague de demandes de rachat dans toutes les BDC non cotées. « Tender activity was elevated across the non-traded BDC industry in the first quarter of 2026 »
- 2026-04-02, Blue Owl Credit Income Corp. — autre annonce : premier trimestre 2026 : 21,9 % demandés, environ 23 % servis. « All repurchase requests will be satisfied on a pro rata basis, representing approximately 23% of total shares tendered »
- 2026-04-02, Blue Owl Technology Income Corp. — autre annonce : le gestionnaire attribue la demande d'OTIC à une base de porteurs concentrée et aux craintes sur le logiciel face à l'IA. « For OTIC, this dynamic was amplified by the fund's more concentrated shareholder base »

Exclusions du bloc : `not_processed` 305, `out_of_scope` 3 (offres sur des obligations ou des actions de préférence ; 8-K au-delà du plafond de lecture).

## Montages identifiés (bloc `montages`, D-0046)

Un montage que les notes d'un groupe décrivent sans nommer son financeur, identifié par des extraits cités des deux côtés (au moins trois traits concordants). Les montants viennent des lignes validées des deux côtés ; ils ne s'additionnent pas.

**Project Beignet Holdings** — « the Venture » dans les notes de Meta

- Membres : Meta Platforms, Inc. 20 % ; Beignet Investor LLC 80 %.
- Traits concordants : Richland Parish, Louisiana (10-Q de Meta, note 13) ; In October 2025 (Meta) ; On October 21, 2025 (Blue Owl Real Estate Net Lease Trust) ; 20 % pour Meta, 80 % pour l'investisseur (Meta) ; 80,0 % de Project Beignet Holdings à Beignet Investor LLC (Blue Owl Real Estate Net Lease Trust) ; Meta Platforms, Inc., locataire et exploitante du campus (Blue Owl Real Estate Net Lease Trust).
- distribution reçue par Meta à la formation : 2,60 Md$ — Meta, 10-Q rendu public le 2025-10-30.
- baux d'exploitation (engagement initial, à partir de 2029) : 12,30 Md$ (environ) — Meta, 10-Q rendu public le 2025-10-30.
- garantie de valeur résiduelle de Meta (seuil de départ) : 28,00 Md$ (au plus) — Meta, 10-Q rendu public le 2025-10-30.
- engagement de fonds propres de Blue Owl Real Estate Net Lease Trust : 1,53 Md$ — Blue Owl Real Estate Net Lease Trust, 10-Q rendu public le 2025-11-07.
- obligations garanties de Beignet Investor LLC (6,581 %, 2049) : 27,29 Md$ — Blue Owl Real Estate Net Lease Trust, 10-Q rendu public le 2025-11-07.
- Les notes suivantes de Meta (10-K 2025, 10-Q de 2026) ne nomment plus que « the Venture » : leurs lignes restent des abstentions (`no_named_counterparty`), et l'identification se lit ici.

Exclusions du bloc : `out_of_scope` 313 (relevés de portefeuille non lus, pièces écartées par la règle d'un montage ou sans paragraphe qualifiant, textes au-delà du plafond ; D-0046, D-0049).

## Obligations de SoftBank valorisées par les fonds (Form N-PORT)

Valeur que les fonds déclarent pour les obligations de SoftBank Group et de SoftBank Corp. qu'ils détiennent, rapportée au nominal, dans la monnaie du titre (Form N-PORT Data Sets ; D-0058, points 8, 27 et 28). Une cellule par titre (ISIN) et par date de portefeuille, au dernier dépôt de chaque série ; chaque fonds déclare à la fin de son propre trimestre. C'est une valorisation déclarée par des tiers, jamais une probabilité de défaut ni un fait comptable de SoftBank : elle n'entre dans aucune mesure de financement ni dans l'annexe F. Les positions d'autres émetteurs déclarées sous le nom ou le LEI de SoftBank Group (Sprint, Fortress) en sont écartées. La série complète est dans `series.md`.

Cellules : 1 092, sur 50 titres, du 2019-09-30 au 2026-07-31.

Titres détenus par au moins un fonds dans les trois mois qui précèdent la dernière date de portefeuille (2026-07-31) :

| Titre | Dernière date | Valeur ÷ nominal | Séries | Nominal détenu | Plus bas (date) | Première date (valeur ÷ nominal) |
| --- | --- | ---: | ---: | ---: | --- | --- |
| SoftBank Group 4 %, échéance 2026-07-06 (USD, XS2361252971) | 2026-04-30 | 99,8 % | 1 | 0,3 M USD | 83,0 % (2022-06-30) | 2021-09-30 (98,5 %) |
| SoftBank Group 2,875 %, échéance 2027-01-06 (EUR, XS2361254597) | 2026-06-30 | 99,6 % | 1 | 0,2 M EUR | 76,3 % (2022-09-30) | 2021-07-31 (104,9 %) |
| SoftBank Group 6,875 %, échéance 2027-07-19 (USD, XS1642686676) | 2026-07-31 | 99,4 % | 3 | 3,5 M USD | 76,0 % (2020-03-31) | 2019-09-30 (93,5 %) |
| SoftBank Group 5,25 %, échéance 2027-07-30 (EUR, XS1266661013) | 2026-07-31 | 100,9 % | 1 | 0,2 M EUR | 100,9 % (2026-04-30) | 2026-01-31 (102,6 %) |
| SoftBank Group 5,125 %, échéance 2027-09-19 (USD, XS1684384867) | 2026-07-31 | 98,9 % | 4 | 4,1 M USD | 81,7 % (2022-06-30) | 2019-09-30 (102,6 %) |
| SoftBank Group 6,25 %, échéance 2028-04-15 (USD, XS1793255198) | 2026-07-31 | 100,0 % | 1 | 0,2 M USD | 95,4 % (2022-04-30) | 2019-10-31 (109,5 %) |
| SoftBank Group 5 %, échéance 2028-04-15 (EUR, XS1793255941) | 2026-07-31 | 100,7 % | 3 | 1,7 M EUR | 78,8 % (2022-09-30) | 2019-09-30 (110,9 %) |
| SoftBank Group 4,625 %, échéance 2028-07-06 (USD, XS2361253433) | 2026-07-31 | 96,6 % | 1 | 0,4 M USD | 77,5 % (2022-06-30) | 2021-07-31 (99,2 %) |
| SoftBank Group 5,375 %, échéance 2029-01-08 (EUR, XS2854423386) | 2026-07-31 | 100,7 % | 7 | 7,2 M EUR | 99,6 % (2024-07-31) | 2024-06-30 (100,0 %) |
| SoftBank Group 6,5 %, échéance 2029-04-10 (USD, XS3109833817) | 2026-07-31 | 98,0 % | 1 | 0,2 M USD | 98,0 % (2026-07-31) | 2025-09-30 (102,0 %) |
| SoftBank Group 3,38 %, échéance 2029-07-06 (EUR, XS2361255057) | 2026-07-31 | 95,3 % | 6 | 3,5 M EUR | 68,6 % (2022-06-30) | 2021-07-31 (97,8 %) |
| SoftBank Group 6,75 %, échéance 2029-07-08 (USD, XS2854422578) | 2026-07-31 | 98,8 % | 2 | 1,2 M USD | 98,8 % (2026-07-31) | 2024-06-30 (99,5 %) |
| SoftBank Group 4 %, échéance 2029-09-19 (EUR, XS1684385591) | 2026-07-31 | 96,4 % | 3 | 0,6 M EUR | 70,8 % (2022-09-30) | 2019-09-30 (103,0 %) |
| SoftBank Group 5,25 %, échéance 2029-10-10 (EUR, XS3109834898) | 2026-07-31 | 99,3 % | 9 | 15,9 M EUR | 98,4 % (2026-03-31) | 2025-07-31 (101,7 %) |
| SoftBank Group 7,625 %, échéance 2029-10-22 (USD, XS3344488948) | 2026-07-31 | 100,4 % | 2 | 1,7 M USD | 100,4 % (2026-07-31) | 2026-04-30 (100,7 %) |
| SoftBank Group 6,375 %, échéance 2030-04-22 (EUR, XS3344489326) | 2026-07-31 | 100,6 % | 10 | 15,5 M EUR | 100,6 % (2026-07-31) | 2026-04-30 (100,9 %) |
| SoftBank Corp. 4,699 %, échéance 2030-07-09 (USD, US83405KAA07) | 2026-07-31 | 97,9 % | 7 | 13,9 M USD | 97,9 % (2026-07-31) | 2025-07-31 (99,7 %) |
| SoftBank Group 6,875 %, échéance 2031-01-10 (USD, XS3109834112) | 2026-07-31 | 97,1 % | 1 | 0,2 M USD | 96,5 % (2026-03-31) | 2025-09-30 (102,0 %) |
| SoftBank Group 5,25 %, échéance 2031-07-06 (USD, XS2361253607) | 2026-07-31 | 92,5 % | 2 | 1,4 M USD | 73,7 % (2022-06-30) | 2021-07-31 (101,4 %) |
| SoftBank Group 7 %, échéance 2031-07-08 (USD, XS2854422818) | 2026-07-31 | 97,8 % | 2 | 2,5 M USD | 97,8 % (2026-07-31) | 2024-06-30 (99,2 %) |
| SoftBank Group 5,875 %, échéance 2031-07-10 (EUR, XS3109835192) | 2026-07-31 | 98,9 % | 13 | 42,9 M EUR | 97,4 % (2026-03-31) | 2025-07-31 (103,5 %) |
| SoftBank Group 8,25 %, échéance 2031-10-22 (USD, XS3344488864) | 2026-07-31 | 100,8 % | 6 | 4,6 M USD | 100,8 % (2026-07-31) | 2026-04-30 (101,0 %) |
| SoftBank Group 7 %, échéance 2032-04-22 (EUR, XS3344489599) | 2026-07-31 | 100,8 % | 7 | 7,4 M EUR | 100,8 % (2026-07-31) | 2026-04-30 (101,2 %) |
| SoftBank Corp. 3,94 %, échéance 2032-06-30 (EUR, XS3317460619) | 2026-07-31 | 99,4 % | 4 | 0,7 M EUR | 99,4 % (2026-07-31) | 2026-04-30 (100,2 %) |
| SoftBank Group 3,875 %, échéance 2032-07-06 (EUR, XS2362416617) | 2026-07-31 | 88,5 % | 5 | 0,8 M EUR | 68,0 % (2022-10-31) | 2021-07-31 (97,6 %) |
| SoftBank Group 5,75 %, échéance 2032-07-08 (EUR, XS2854423469) | 2026-07-31 | 95,6 % | 14 | 22,9 M EUR | 94,9 % (2026-03-31) | 2024-06-30 (99,9 %) |
| SoftBank Group 7,25 %, échéance 2032-07-10 (USD, XS3112542272) | 2026-07-31 | 95,0 % | 3 | 6,1 M USD | 95,0 % (2026-07-31) | 2025-09-30 (103,0 %) |
| SoftBank Group 6,375 %, échéance 2033-07-10 (EUR, XS3112543080) | 2026-07-31 | 97,6 % | 11 | 21,6 M EUR | 95,9 % (2026-03-31) | 2025-07-31 (103,7 %) |
| SoftBank Group 7,375 %, échéance 2034-04-22 (EUR, XS3344489672) | 2026-07-31 | 100,9 % | 7 | 10,7 M EUR | 100,9 % (2026-07-31) | 2026-04-30 (100,9 %) |
| SoftBank Corp. 5,332 %, échéance 2035-07-09 (USD, US83405KAB89) | 2026-07-31 | 96,6 % | 7 | 16,2 M USD | 96,6 % (2026-07-31) | 2025-06-30 (100,0 %) |
| SoftBank Corp. 5,33 %, échéance 2035-07-09 (USD, USJ75963DC97) | 2026-07-31 | 96,6 % | 1 | 5,0 M USD | 96,6 % (2026-07-31) | 2025-10-31 (101,0 %) |
| SoftBank Group 7,5 %, échéance 2035-07-10 (USD, XS3112542355) | 2026-07-31 | 97,3 % | 1 | 0,2 M USD | 97,3 % (2026-07-31) | 2025-10-31 (106,0 %) |
| SoftBank Group 8,5 %, échéance 2036-04-22 (USD, XS3344489169) | 2026-07-31 | 100,6 % | 2 | 0,6 M USD | 100,6 % (2026-07-31) | 2026-04-30 (102,0 %) |
| SoftBank Corp. 4,47 %, échéance 2036-06-30 (EUR, XS3317460700) | 2026-07-31 | 99,4 % | 1 | 0,3 M EUR | 99,4 % (2026-07-31) | 2026-04-30 (100,2 %) |
| SoftBank Group 7,625 %, échéance 2061-04-29 (USD, XS3203997005) | 2026-07-31 | 94,5 % | 4 | 6,6 M USD | 89,8 % (2026-03-31) | 2025-10-31 (99,5 %) |
| SoftBank Group 6,5 %, échéance 2062-10-29 (EUR, XS3203998078) | 2026-07-31 | 88,9 % | 7 | 4,8 M EUR | 85,7 % (2026-03-31) | 2025-12-31 (97,7 %) |
| SoftBank Group 8,25 %, échéance 2065-10-29 (USD, XS3203997427) | 2026-07-31 | 96,8 % | 4 | 6,4 M USD | 89,7 % (2026-03-31) | 2025-12-31 (93,7 %) |

Titres sans position déclarée dans ces trois mois (remboursés, rachetés ou cédés par les fonds) : 13.

## Non-cotés du modèle valorisés par les fonds (Form N-PORT)

Valeur par action que des fonds enregistrés déclarent pour les actions d'un nœud du modèle qu'ils évaluent eux-mêmes (niveau 3 de la hiérarchie de juste valeur), au dernier dépôt de chaque série pour la date de portefeuille, et somme de ces valeurs par trimestre civil (Form N-PORT Data Sets ; D-0065). Une position n'est rattachée que si le nom d'émetteur déclaré commence par une dénomination légale du registre, ou n'est formé que d'un terme de la configuration qui désigne une seule entité, suivi de mots de catégorie ou d'instrument (« ANTHROPIC SERIES G » ; D-0066, point 3), et une entité cotée n'y entre qu'avant son introduction en bourse. Ce sont des marques déclarées par des tiers (perspective `counterparty`) : jamais une valorisation du nœud ni un fait comptable, hors des mesures de financement, de l'exposition, des paires et de l'annexe F. Deux fonds peuvent détenir deux catégories d'actions différentes : leurs valeurs par action ne se comparent qu'à titre égal. Le détail par fonds et par titre est dans `series.md`.

Le dernier trimestre est le dernier trimestre civil complet : un N-PORT se dépose dans les 60 jours qui suivent la fin du trimestre du fonds, si bien que le trimestre en cours à la dernière archive n'est couvert qu'en partie, comme le premier de la période ; ces trimestres sont marqués « partiel ».

| Nœud | Dernier trimestre | Valeur détenue déclarée | Séries | Valeur par action à la dernière date (plus basse – plus haute) | Premier trimestre (valeur détenue) |
| --- | --- | ---: | ---: | --- | --- |
| Anthropic | 2026-06-30 | 15 353 M$ | 109 | 589,00 USD – 622,94 USD (2026-07-31) | 2024-03-31 (2 M$) |
| SpaceX | 2026-06-30 | 11 727 M$ | 24 | 105,32 USD – 5 265,90 USD (2026-05-31) | 2019-09-30 (320 M$ (partiel)) |
| OpenAI | 2026-06-30 | 4 507 M$ | 69 | 678,11 USD – 687,69 USD (2026-07-31) | 2024-06-30 (2 M$) |
| Waymo LLC | 2026-06-30 | 2 366 M$ | 54 | 164,32 USD – 197,80 USD (2026-07-31) | 2020-06-30 (490 M$) |
| X.AI Holdings Corp. | 2026-03-31 | 751 M$ | 7 | 75,46 USD – 75,46 USD (2026-01-31) | 2025-03-31 (29 M$) |
| CoreWeave | 2025-03-31 | 520 M$ | 14 | 939,94 USD – 1 062,92 USD (2025-02-28) | 2023-12-31 (162 M$) |
| X Holdings Corp. | 2025-03-31 | 209 M$ | 19 | 101,50 USD – 101,50 USD (2025-03-31) | 2023-03-31 (32 M$) |
| Cerebras Systems Inc. | 2026-06-30 | 168 M$ | 5 | 100,26 USD – 100,26 USD (2026-04-30) | 2022-06-30 (7 M$) |
| SiFive, Inc. | 2026-06-30 | 132 M$ | 8 | 9,51 USD – 11,22 USD (2026-06-30) | 2022-03-31 (25 M$) |
| Fluidstack Ltd. | 2026-06-30 | 109 M$ | 3 | 144,11 USD – 162,22 USD (2026-06-30) | 2026-03-31 (54 M$) |
| Coinbase, Inc. | 2021-03-31 | 90 M$ | 15 | 373,00 USD – 373,00 USD (2021-03-31) | 2021-03-31 (90 M$) |
| Compass, Inc. | 2021-03-31 | 85 M$ | 7 | 178,61 USD – 182,90 USD (2021-01-31) | 2019-12-31 (74 M$) |
| DoorDash, Inc. | 2020-09-30 | 67 M$ | 14 | 229,53 USD – 229,53 USD (2020-09-30) | 2020-06-30 (67 M$) |
| Nscale | 2026-06-30 | 47 M$ | 9 | 20,94 USD – 20,94 USD (2026-07-31) | 2025-09-30 (151 952 $) |
| WEWORK INC. | 2025-03-31 | 46 M$ | 10 | 15,68 USD – 16,00 USD (2025-03-31) | 2019-09-30 (3 M$ (partiel)) |
| Aurora Innovation, Inc. | 2021-06-30 | 45 M$ | 4 | 19,66 USD – 19,66 USD (2021-06-30) | 2019-09-30 (21 M$ (partiel)) |
| Innovium, Inc. | 2021-09-30 | 38 M$ | 3 | 8,48 USD – 10,08 USD (2021-09-30) | 2020-06-30 (10 M$) |
| EQRx, Inc. | 2021-06-30 | 37 M$ | 4 | 3,32 USD – 3,32 USD (2021-05-31) | 2020-12-31 (31 M$) |
| Barings Capital Investment Corporation | 2021-06-30 | 25 M$ | 1 | 21,63 USD (2021-06-30) | 2021-03-31 (15 M$) |
| Seer, Inc. | 2020-09-30 | 22 M$ | 5 | 0,15 USD – 3,75 USD (2020-08-31) | 2019-12-31 (463 720 $) |
| SQUARESPACE, INC. | 2021-06-30 | 22 M$ | 3 | 68,42 USD – 68,42 USD (2021-04-30) | 2021-03-31 (1 M$) |
| Santander Bank, N.A. | 2026-06-30 | 18 M$ | 1 | 0,95 USD (2026-06-30) | 2025-12-31 (25 M$) |
| Zymergen Inc. | 2020-12-31 | 14 M$ | 3 | 8,21 USD – 8,21 USD (2020-12-31) | 2020-09-30 (11 M$) |
| Lambda | 2026-06-30 | 12 M$ | 1 | 38,00 USD (2026-07-31) | 2025-03-31 (5 M$) |
| Snowflake Inc. | 2020-09-30 | 12 M$ | 2 | 38,77 USD – 38,77 USD (2020-08-31) | 2020-03-31 (9 M$) |
| CURIOSITYSTREAM INC. | 2019-09-30 | 9 M$ (partiel) | 1 | 10,00 USD (2019-09-30) | 2019-09-30 (9 M$ (partiel)) |
| X.AI Corp. | 2026-03-31 | 7 M$ | 1 | 75,46 USD (2026-01-31) | 2024-06-30 (129 M$) |
| 1Life Healthcare Inc | 2019-12-31 | 6 M$ | 1 | 13,26 USD – 13,26 USD (2019-10-31) | 2019-09-30 (8 M$ (partiel)) |
| MELLANOX TECHNOLOGIES, LTD. | 2020-06-30 | 5 M$ | 1 | 125,00 USD (2020-05-29) | 2020-06-30 (5 M$) |
| MCDERMOTT INTERNATIONAL INC | 2024-12-31 | 3 M$ | 5 | 0,14 USD – 250,00 USD (2024-11-30) | 2022-12-31 (8 M$) |
| OpenAI, Inc. | 2024-09-30 | 3 M$ | 1 | 262,00 USD (2024-09-30) | 2023-12-31 (2 M$) |
| PENDRELL CORP | 2022-06-30 | 2 M$ | 1 | 215 088,56 USD (2022-06-30) | 2021-12-31 (2 M$) |
| MGM Holdings Inc. | 2022-03-31 | 2 M$ | 6 | 3,80 USD – 142,69 USD (2022-03-31) | 2021-09-30 (21 M$) |
| Silver Lake Partners V, L.P. | 2026-06-30 | 626 394 $ | 1 | 1,35 USD (2026-06-30) | 2024-12-31 (602 637 $) |
| PROSPER MARKETPLACE, INC | 2026-03-31 | 92 769 $ | 1 | 0,38 USD (2026-03-31) | 2022-06-30 (320 877 $) |
| Broadcom | 2026-06-30 | 78 $ | 1 | 0,01 USD (2026-04-30) | 2026-03-31 (78 $) |
| META MATERIALS INC. | 2026-06-30 | 28 $ | 4 | 0,00 USD – 0,00 USD (2026-06-30) | 2024-09-30 (28 $) |
| Goldman Sachs & Co. LLC | 2020-06-30 | 11 $ | 4 | 0,00 AUD – 0,00 AUD (2020-04-30) | 2020-06-30 (11 $) |

Exclusions du scan : `conflicting` 5, `not_processed` 28, `out_of_scope` 2, `pending_entity` 1 339. Un nom d'émetteur gardé par le lexique sans commencer par une dénomination légale ni être formé d'un terme suivi de mots de catégorie (véhicule nommé d'après un nœud, autre forme juridique, nom commercial) est compté en `pending_entity`, jamais rattaché sans extrait (D-0065, point 6 ; D-0066, point 3) ; les prêts de plateforme sont comptés en `out_of_scope` (D-0066, point 4).

## Prêts et dette des nœuds valorisés par les fonds (Form N-PORT)

Valeur que les fonds enregistrés déclarent pour les prêts (LON) et les titres de dette (DBT) d'un nœud du modèle qu'ils évaluent eux-mêmes (niveau 3), rapportée au nominal, dans la monnaie du titre, au dernier dépôt de chaque série pour la date de portefeuille (Form N-PORT Data Sets ; D-0066, point 4). Une cellule par nœud, catégorie, monnaie et date : elle mêle les tranches et les rangs que les fonds détiennent, dont les intitulés et les échéances sont dans `series.md`. C'est une marque déclarée par des tiers (perspective `counterparty`), jamais une probabilité de défaut ni un fait comptable de l'emprunteur : elle n'entre dans aucune mesure de financement, ni dans l'exposition, les paires, les cycles ou l'annexe F. Les parts en défaut, en arriéré d'intérêts ou en intérêts capitalisés (PIK) sont celles du nominal que les fonds déclarent ainsi (Item C.9).

Cellules : 522, sur 69 nœuds, du 2019-09-30 au 2026-07-31.

Nœuds dont au moins un fonds déclare un prêt ou un titre de dette dans les trois mois qui précèdent la dernière date de portefeuille (2026-07-31), par valeur déclarée en dollars à leur dernière date :

| Nœud | Catégorie | Dernière date | Valeur ÷ nominal | Nominal détenu | Séries | Défaut, arriéré, PIK | Plus bas (date) | Première date (valeur ÷ nominal) |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| Nscale | prêts (USD) | 2026-06-30 | 100,0 % | 334,1 M USD | 19 | — | 100,0 % (2026-03-31) | 2026-03-31 (100,0 %) |
| CoreWeave | prêts (USD) | 2026-07-31 | 99,8 % | 49,3 M USD | 6 | — | 98,4 % (2023-10-31) | 2023-09-30 (99,2 %) |
| Deutsche Bank AG | titres de dette (USD) | 2026-06-30 | 99,9 % | 39,5 M USD | 2 | — | 99,9 % (2025-12-31) | 2025-06-30 (100,0 %) |
| SoftBank | prêts (USD) | 2026-06-30 | 100,0 % | 35,0 M USD | 1 | — | 100,0 % (2026-03-31) | 2026-03-31 (100,0 %) |
| Deutsche Bank AG | titres de dette (INR) | 2026-06-30 | 97,9 % | 2 025,0 M INR | 2 | — | 97,9 % (2026-06-30) | 2026-06-30 (97,9 %) |
| Trinity Capital Inc. | titres de dette (USD) | 2026-06-30 | 100,3 % | 20,3 M USD | 1 | — | 99,2 % (2024-12-31) | 2024-12-31 (99,2 %) |
| SVF II Finco Cayman L.P. | prêts (USD) | 2026-06-30 | 100,3 % | 16,9 M USD | 2 | — | 93,5 % (2023-09-30) | 2022-04-30 (100,0 %) |
| IREN | titres de dette (USD) | 2026-06-30 | 100,0 % | 10,0 M USD | 1 | — | 100,0 % (2026-06-30) | 2026-06-30 (100,0 %) |
| Sanmina Corporation | prêts (USD) | 2026-06-30 | 100,2 % | 5,2 M USD | 11 | — | 99,9 % (2025-09-30) | 2025-08-31 (100,0 %) |
| Wingspire Equipment Finance LLC | titres de dette (USD) | 2026-06-30 | 100,0 % | 4,6 M USD | 1 | — | 100,0 % (2024-12-31) | 2024-12-31 (100,0 %) |
| BARCLAYS BANK PLC | titres de dette (USD) | 2026-06-30 | 100,0 % | 3,4 M USD | 2 | — | 96,4 % (2025-02-28) | 2022-06-30 (104,7 %) |
| BARNES & NOBLE INC | prêts (USD) | 2026-06-30 | 97,5 % | 1,6 M USD | 1 | — | 89,8 % (2020-03-31) | 2020-03-31 (89,8 %) |
| CITIGROUP INC | titres de dette (USD) | 2026-07-31 | 100,0 % | 0,3 M USD | 1 | — | 94,9 % (2026-06-30) | 2025-12-31 (100,0 %) |
| Cloudera, Inc. | prêts (USD) | 2026-06-30 | 60,0 % | 0,3 M USD | 1 | — | 60,0 % (2026-06-30) | 2020-12-31 (99,9 %) |
| Tempus AI, Inc. | prêts (USD) | 2026-06-30 | 100,0 % | 0,0 M USD | 1 | — | 96,7 % (2025-03-31) | 2025-03-31 (96,7 %) |
| Jane Street Group, LLC | prêts (USD) | 2026-06-30 | 100,0 % | 0,0 M USD | 1 | — | 99,3 % (2026-03-31) | 2019-09-30 (100,0 %) |

Nœuds et catégories sans position déclarée dans ces trois mois : 75.

Prêts de plateforme écartés et comptés, par émetteur déclaré : 2 (`out_of_scope`) ; le fonds y nomme la plateforme qui les a consentis, non l'emprunteur, et leurs débiteurs ne sont jamais lus (D-0066, point 4).

## OpenAI et Anthropic vus par les déposants : faits balisés (D-0060, volet 3)

Faits des instances XBRL des groupes et des extraits des Notes Data Sets déjà en cache dont un membre de dimension nomme un laboratoire (`lab_tagged_value`). Valeur et unité telles que balisées, du point de vue du déposant (actionnaire, fournisseur, bailleur, prêteur) : jamais un fait comptable du laboratoire, jamais une valorisation, aucun ratio. Un trimestre sans fait balisé n'est pas un zéro. Un déposant hors du graphe n'entre dans aucune paire ni aucun agrégat. Une ligne par série (fait et membres), au dernier fait connu ; la série complète est dans `series.md`.

Cellules : Anthropic 25 (7 déposants), OpenAI 102 (6 déposants).

### Anthropic

**Amazon** : 7 faits balisés, du 2026-04-29 au 2026-06-30.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `RevenueRemainingPerformanceObligationAmountPeriodIncreaseDecrease` | Anthropic | 2026-04-01 → 2026-06-30 | 100 000 M$ | 10-Q 0001018724-26-000026 | 1 |
| `LineOfCreditFacilityCurrentBorrowingCapacity` | Anthropic | au 2026-06-30 | 15 000 M$ | 10-Q 0001018724-26-000026 | 1 |
| `LineOfCreditFacilityExpirationPeriod` | Anthropic | 2026-01-01 → 2026-06-30 | 30 mois | 10-Q 0001018724-26-000026 | 1 |
| `LineOfCreditFacilityExpirationPeriod` | Anthropic | 2026-04-01 → 2026-04-29 | 30 mois | 10-Q 0001018724-26-000014 | 1 |
| `LineOfCreditFacilityMaximumBorrowingCapacity` | Anthropic | au 2026-06-30 | 20 000 M$ | 10-Q 0001018724-26-000026 | 1 |
| `LineOfCreditFacilityMaximumBorrowingCapacity` | Anthropic | au 2026-04-29 | 20 000 M$ | 10-Q 0001018724-26-000014 | 1 |
| `RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionPeriod1` | Anthropic | au 2026-06-30 | 10 ans | 10-Q 0001018724-26-000026 | 1 |

**Apollo** : 1 fait balisé, du 2026-06-30 au 2026-06-30.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `CapitalSolutionAgreementAmount` | Anthropic | 2026-04-01 → 2026-06-30 | 35 000 M$ (conflit : le texte lu nomme Broadcom Inc. pour ce montant) | 10-Q 0001858681-26-000040 | 1 |

**NVIDIA** : 1 fait balisé, du 2025-11-19 au 2025-11-19.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `OtherCommitment` | Anthropic, PBC | au 2025-11-19 | 10 000 M$ | 10-Q 0001045810-25-000230 | 1 |

**Riot** : 6 faits balisés, du 2026-08-31 au 2026-08-31.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `ExpectedDataCenterRevenueDuringInitialTerm` | Anthropic Lease | 2026-08-01 → 2026-08-31 | 9 100 M$ | 10-Q 0001104659-26-093448 | 1 |
| `InitialMegawattsOfPowerDeployment` | Anthropic Lease | 2026-08-01 → 2026-08-31 | 96 MW (unité balisée : MWh) | 10-Q 0001104659-26-093448 | 1 |
| `InitialMegawattsOfPowerDeployment` | Anthropic Lease | 2026-08-01 → 2026-08-31 | 191 MW (unité balisée : MWh) | 10-Q 0001104659-26-093448 | 1 |
| `OperatingLeaseOptionToExtendTermOfLeaseNumberOfSuccessiveExtension` | Anthropic Lease | 2026-08-01 → 2026-08-31 | 2 | 10-Q 0001104659-26-093448 | 1 |
| `LesseeOperatingLeaseRenewalTerm` | Anthropic Lease | au 2026-08-31 | 5 ans | 10-Q 0001104659-26-093448 | 1 |
| `LesseeOperatingLeaseTermOfContract` | Anthropic Lease | au 2026-08-31 | 20 ans | 10-Q 0001104659-26-093448 | 1 |

**TeraWulf** : 4 faits balisés, du 2026-07-06 au 2026-07-06.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `LessorOperatingLeaseLeaseNotYetCommencedRenewalTerm1` | Anthropic HPC Lease | au 2026-07-06 | 5 ans | 10-Q 0001083301-26-000166 | 1 |
| `LessorOperatingLeaseLeaseNotYetCommencedTermOfContract1` | Anthropic HPC Lease | au 2026-07-06 | 20 ans | 10-Q 0001083301-26-000166 | 1 |
| `LessorOperatingLeaseLeaseNotYetCommencedMegawattsOfCriticalITLoad` | Anthropic HPC Lease | au 2026-07-06 | 401 MW | 10-Q 0001083301-26-000166 | 1 |
| `LessorOperatingLeaseLeaseNotYetCommencedNumberOfRenewalOptions` | Anthropic HPC Lease | au 2026-07-06 | 2 (unité balisée : USD) | 10-Q 0001083301-26-000166 | 1 |

**SALESFORCE, INC. (cik:0001108524, hors du graphe)** : 4 faits balisés, du 2026-01-31 au 2026-07-31.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `ConcentrationRiskPercentage1` | AnthropicPBC | au 2026-07-31 | 45,0 % | 10-Q 0001108524-26-000190 | 1 |
| `ConcentrationRiskPercentage1` | AnthropicPBC | au 2026-01-31 | 22,0 % | 10-Q 0001108524-26-000190 | 1 |
| `EquitySecuritiesWithoutReadilyDeterminableFairValueUpwardPriceAdjustmentAnnualAmount` | AnthropicPBC | au 2026-07-31 | 2 700 M$ | 10-Q 0001108524-26-000190 | 1 |
| `EquitySecuritiesWithoutReadilyDeterminableFairValueUpwardPriceAdjustmentAnnualAmount` | AnthropicPBC | au 2026-07-31 | 3 000 M$ | 10-Q 0001108524-26-000190 | 1 |

**ZOOM COMMUNICATIONS, INC. (cik:0001585521, hors du graphe)** : 2 faits balisés, du 2026-04-30 au 2026-04-30.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `EquitySecuritiesWithoutReadilyDeterminableFairValueAmount` | EquitySecuritiesWithoutReadilyDeterminableFairValueAnthropic | au 2026-04-30 | 1 267 M$ | 10-Q 0001585521-26-000071 | 1 |
| `PaymentsToAcquireLongtermInvestments` | EquitySecuritiesWithoutReadilyDeterminableFairValueAnthropic | au 2026-04-30 | 46 M$ | 10-Q 0001585521-26-000071 | 1 |

### OpenAI

**Amazon** : 6 faits balisés, du 2026-03-31 au 2026-03-31.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `RevenueRemainingPerformanceObligationAmountPeriodIncreaseDecrease` | Open AI | 2026-01-01 → 2026-03-31 | 100 000 M$ | 10-Q 0001018724-26-000014 | 1 |
| `RevenueRemainingPerformanceObligationAmountPeriodIncreaseDecrease` | Open AI | 2026-01-01 → 2026-03-31 | 100 000 M$ | 10-Q 0001018724-26-000026 | 1 |
| `RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionPeriod1` | Open AI | au 2026-03-31 | 8 ans | 10-Q 0001018724-26-000014 | 1 |
| `RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionPeriod1` | Open AI | au 2026-03-31 | 8 ans | 10-Q 0001018724-26-000026 | 1 |
| `RevenueRemainingPerformanceObligation` | Open AI | au 2026-03-31 | 38 000 M$ | 10-Q 0001018724-26-000014 | 1 |
| `RevenueRemainingPerformanceObligation` | Open AI | au 2026-03-31 | 38 000 M$ | 10-Q 0001018724-26-000026 | 1 |

**Cerebras Systems Inc.** : 41 faits balisés, du 2025-12-31 au 2026-07-31.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `ClassOfWarrantOrRightGrantDateFairValuePerShare` | OpenAIWarrant | au 2026-06-30 | 82 $ | 10-Q 0001628280-26-056357 | 2 |
| `ClassOfWarrantOrRightVestedAndExercisable` | OpenAIWarrant | au 2026-06-30 | 5 574 171 actions | 10-Q 0001628280-26-056357 | 3 |
| `CommittedComputeCapacityIncludedInRemainingPerformanceObligations` | OpenAI | au 2026-03-31 | 250 MW (unité balisée : megawatt) | 10-Q 0001628280-26-044981 | 1 |
| `CommittedComputeCapacityUnderMasterRelationshipAgreement` | OpenAI | au 2025-12-31 | 750 MW (unité balisée : megawatt) | 10-Q 0001628280-26-044981 | 1 |
| `CustomerWarrantAssetAmortizationReductionOfRevenue` | OpenAI | au 2026-06-30 | 2 M$ | 10-Q 0001628280-26-056357 | 2 |
| `CustomerWarrantAssetAmortizationReductionOfRevenue` | OpenAI | au 2026-06-30 | 3 M$ | 10-Q 0001628280-26-056357 | 1 |
| `LongTermDebtOffsettingAmount` | OpenAI | au 2026-03-31 | 22 M$ | 10-Q 0001628280-26-044981 | 1 |
| `LongTermDebtOffsettingAmount` | OpenAI | au 2026-06-30 | -86 M$ | 10-Q 0001628280-26-056357 | 1 |
| `MaximumTotalComputeCapacityUnderMasterRelationshipAgreement` | OpenAI | au 2025-12-31 | 2 GW | 10-Q 0001628280-26-044981 | 1 |
| `NoncashInterestExpense` | OpenAI | au 2026-06-30 | 20 M$ | 10-Q 0001628280-26-056357 | 2 |
| `NoncashInterestExpense` | OpenAI | au 2026-06-30 | 39 M$ | 10-Q 0001628280-26-056357 | 1 |
| `NoncashRepaymentOfDebt` | OpenAI | au 2026-03-31 | 22 M$ | 10-Q 0001628280-26-044981 | 1 |
| `NoncashRepaymentOfDebt` | OpenAI | au 2026-06-30 | 86 M$ | 10-Q 0001628280-26-056357 | 1 |
| `OptionToPurchaseAdditionalComputeCapacity` | OpenAI | au 2025-12-31 | 1,25 GW | 10-Q 0001628280-26-044981 | 1 |
| `ClassOfWarrantOrRightExercisePriceOfWarrantsOrRights1` | OpenAIWarrant | au 2026-06-30 | 0 $ | 10-Q 0001628280-26-056357 | 2 |
| `ClassOfWarrantOrRightNumberOfSecuritiesCalledByWarrantsOrRights` | OpenAIWarrant | au 2026-06-30 | 33 445 026 actions | 10-Q 0001628280-26-056357 | 2 |
| `ClassOfWarrantOrRightNumberOfSecuritiesCalledByWarrantsOrRights` | OpenAIWarrant | au 2026-07-31 | 10 033 508 actions | 10-Q 0001628280-26-056357 | 1 |
| `DebtInstrumentCarryingAmount` | OpenAI | au 2026-06-30 | 918 M$ | 10-Q 0001628280-26-056357 | 2 |
| `DebtInstrumentFaceAmount` | OpenAI | au 2025-12-31 | 1 000 M$ | 10-Q 0001628280-26-044981 | 1 |
| `DebtInstrumentInterestRateStatedPercentage` | OpenAI | au 2026-06-30 | 6,0 % | 10-Q 0001628280-26-056357 | 2 |
| `LongTermDebtCurrent` | OpenAI | au 2026-06-30 | 736 M$ | 10-Q 0001628280-26-056357 | 2 |
| `LongTermDebtNoncurrent` | OpenAI | au 2026-06-30 | 182 M$ | 10-Q 0001628280-26-056357 | 2 |
| `ProceedsFromIssuanceOfLongTermDebt` | OpenAI | au 2026-01-31 | 1 000 M$ | 10-Q 0001628280-26-044981 | 1 |
| `ProceedsFromIssuanceOfLongTermDebt` | OpenAI | au 2026-03-31 | 1 005 M$ | 10-Q 0001628280-26-044981 | 1 |
| `ProceedsFromIssuanceOfLongTermDebt` | OpenAI | au 2026-06-30 | 1 005 M$ | 10-Q 0001628280-26-056357 | 1 |
| `RepaymentsOfLongTermDebt` | OpenAI | au 2026-03-31 | 0 $ | 10-Q 0001628280-26-044981 | 1 |
| `RepaymentsOfLongTermDebt` | OpenAI | au 2026-06-30 | 0 $ | 10-Q 0001628280-26-056357 | 1 |
| `RevenueFromContractWithCustomerExcludingAssessedTax` | OpenAI | au 2026-06-30 | 57 M$ | 10-Q 0001628280-26-056357 | 2 |
| `RevenueFromContractWithCustomerExcludingAssessedTax` | OpenAI | au 2026-06-30 | 74 M$ | 10-Q 0001628280-26-056357 | 1 |

**CoreWeave** : 10 faits balisés, du 2025-03-31 au 2025-09-30.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `StockIssuedDuringPeriodSharesIssuedForContractIncentives` | OpenAI OpCo, LLC | 2025-03-01 → 2025-03-31 | 8 750 000 actions | 10-Q 0001769628-25-000041 | 1 |
| `ContractWithCustomerAssetGross` | OpenAI OpCo, LLC | au 2025-06-30 | 11 900 M$ | 10-Q 0001769628-25-000041 | 2 |
| `ContractWithCustomerLiabilityCurrent` | OpenAI OpCo, LLC | au 2025-09-30 | 52 M$ | 10-Q 0001769628-25-000062 | 3 |
| `ContractWithCustomerLiabilityNoncurrent` | OpenAI OpCo, LLC | au 2025-09-30 | 298 M$ | 10-Q 0001769628-25-000062 | 3 |
| `ContractWithCustomerLiability` | OpenAI OpCo, LLC | au 2025-03-31 | 450 M$ | 10-Q 0001769628-25-000014 | 1 |

**Microsoft** : 32 faits balisés, du 2024-06-30 au 2026-06-30.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `EquityMethodInvestmentsFunded` | OpenAI Global, LLC | au 2026-06-30 | 11 900 M$ | 10-K 0001193125-26-323660 | 4 |
| `EquityMethodInvestmentsTotalFundingCommitments` | OpenAI Global, LLC | au 2026-06-30 | 13 000 M$ | 10-K 0001193125-26-323660 | 8 |
| `InvestmentOwnershipPercentage` | OpenAI Global, LLC | au 2025-10-28 | 27,0 % | 10-Q 0001193125-25-256321 | 1 |
| `PurchaseCommitmentIncrementalAmountCommitted` | OpenAI Global, LLC | 2025-10-28 → 2025-10-28 | 250 000 M$ | 10-Q 0001193125-25-256321 | 1 |
| `AccountsReceivableNet` | OpenAI Global, LLC | au 2026-06-30 | 6 000 M$ | 10-K 0001193125-26-323660 | 1 |
| `EquityMethodInvestmentOwnershipPercentage` | OpenAI Global, LLC | au 2026-06-30 | 25,0 % | 10-K 0001193125-26-323660 | 3 |
| `NonoperatingIncomeExpense` | OpenAI Global, LLC | 2025-07-01 → 2026-06-30 | 6 500 M$ | 10-K 0001193125-26-323660 | 13 |
| `RevenueFromContractWithCustomerExcludingAssessedTax` | OpenAI Global, LLC | 2025-07-01 → 2026-06-30 | 24 100 M$ | 10-K 0001193125-26-323660 | 1 |

**DESTINY TECH100 INC. (cik:0001843974, hors du graphe)** : 1 fait balisé, du 2024-01-31 au 2024-01-31.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `MinorityInterestOwnershipPercentageByNoncontrollingOwners` | OpenAIInc | au 2024-01-31 | 100,0 % | N-CSR/A 0001398344-25-009943 | 1 |

**EIGHTCO HOLDINGS INC. (cik:0001892492, hors du graphe)** : 12 faits balisés, du 2025-12-31 au 2026-06-30.

| Fait balisé | Membre | Dernière période | Valeur | Pièce | Faits de la série |
| --- | --- | --- | ---: | --- | ---: |
| `TreasuryPositionPercentage` | OpenAI | au 2026-03-31 | 30,0 % | 10-K 0001493152-26-016664 | 1 |
| `BusinessCombinationConsiderationTransferred1` | OpenAI | au 2026-03-31 | 93 M$ | 10-Q 0001493152-26-023890 | 1 |
| `BusinessCombinationConsiderationTransferred1` | OpenAI | au 2026-06-30 | 93 M$ | 10-Q 0001493152-26-036637 | 1 |
| `Investments` | OpenAI | au 2026-03-31 | 90 M$ | 10-K 0001493152-26-016664 | 1 |
| `OtherInvestments` | OpenAI | au 2026-06-30 | 93 M$ | 10-Q 0001493152-26-036637 | 2 |
| `OtherInvestments` | OpenAI | au 2026-06-30 | 93 M$ | 10-Q 0001493152-26-036637 | 3 |
| `PaymentsToAcquireInterestInSubsidiariesAndAffiliates` | OpenAI | au 2026-02-28 | 125 M$ | 10-K 0001493152-26-016664 | 1 |
| `PaymentsToAcquireInvestments` | OpenAI | au 2026-03-31 | 40 M$ | 10-K 0001493152-26-016664 | 2 |

## Grand livre des laboratoires (D-0060, volet 4)

Pour chaque laboratoire et chaque groupe qui a une arête avec lui : les instruments qui les lient, dans le sens des ressources (§3.1), au dernier montant admissible connu (`lab_ledger`), avec sa pièce. Un flux est le dernier flux publié, jamais une somme ; aucun total, ni par partenaire, ni par sens. Les états de la paire (au coût, au bilan, à la juste valeur, plafonds d'engagement) viennent de `counterparty_exposure` et ne nettent pas les engagements déjà versés. Les capacités balisées (MW, GW) restent à part, jamais additionnées aux dollars. Chaque montant est vu par le déposant de sa pièce : le grand livre ne dit rien des comptes des laboratoires.

### Anthropic

Partenaires : 12 ; arêtes : 81.

#### Amazon

64 arêtes, dont 54 à montant.
- Exposition du partenaire au 2026-06-30 (`counterparty_exposure`) : engagements non appelés (plafond) 16 400 M$ ; au bilan (participation) 92 500 M$ ; au coût (participation) 18 000 M$ ; à la juste valeur (participation) 97 900 M$.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| laboratoire → partenaire | amzn:anthropic_aws_commitment | engagement d'achat | engagement de capacité | plus de 100 000 M$ | 2026-06-30 | 10-Q 0001018724-26-000026 | 1 |
| partenaire → laboratoire | amzn:anthropic_convertible_notes | obligations convertibles | juste valeur | environ 97 900 M$ | 2026-06-30 | 10-Q 0001018724-26-000026 | 11 |
| partenaire → laboratoire | amzn:anthropic_convertible_notes | obligations convertibles | versement | 1 400 M$ | 2025-12-31 | 10-K 0001018724-26-000004 | 19 |
| partenaire → laboratoire | amzn:anthropic_convertible_notes | obligations convertibles | autre (conversion) | au plus 4 500 M$ | 2026-06-30 | 10-Q 0001018724-26-000026 | 10 |
| partenaire → laboratoire | amzn:anthropic_nonvoting_preferred | fonds propres | valeur au bilan | environ 92 500 M$ | 2026-06-30 | 10-Q 0001018724-26-000026 | 6 |
| partenaire → laboratoire | amzn:anthropic_nonvoting_preferred | fonds propres | autre (réévaluation sur prix observables) | au plus 62 800 M$ (semestre clos le 30 juin 2026) | 2026-06-30 | 10-Q 0001018724-26-000026 | 5 |
| partenaire → laboratoire | amzn:anthropic_series_g | fonds propres | versement | 5 000 M$ | 2026-06-30 | 10-Q 0001018724-26-000026 | 1 |
| partenaire → laboratoire | amzn:anthropic_series_h | fonds propres | versement | 5 000 M$ | 2026-06-30 | 10-Q 0001018724-26-000026 | 1 |

Sans montant admissible : amzn:anthropic_financing_facility (obligations convertibles, signé, 10-Q 0001018724-26-000026).

#### TeraWulf

4 arêtes, dont 0 à montant.
- Capacités balisées (jamais additionnées) : 401 MW, `LessorOperatingLeaseLeaseNotYetCommencedMegawattsOfCriticalITLoad` (au 2026-07-06).

Sans montant admissible : terawulf:anthropic_hawesville_lease (bail de capacité, signé, 10-Q 0001083301-26-000166) ; wulf:justified_anthropic_lease (bail de capacité, signé, 8-K 0001104659-26-080583).

#### Akamai

3 arêtes, dont 2 à montant.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| laboratoire → partenaire | akam:anthropic_msa | engagement d'achat | engagement de capacité | environ 11 600 M$ | 2026-09-18 | 8-K 0001193125-26-401048 | 1 |
| partenaire → laboratoire | akam:anthropic_warrant | titres ou bons remis au client | contrepartie payable au client | jusqu'à 387 051 actions | 2026-09-18 | 8-K 0001193125-26-401048 | 1 |

#### Riot

2 arêtes, dont 1 à montant.
- Capacités balisées (jamais additionnées) : 96 MW (unité balisée : MWh), `InitialMegawattsOfPowerDeployment` (2026-08-01 → 2026-08-31) ; 191 MW (unité balisée : MWh), `InitialMegawattsOfPowerDeployment` (2026-08-01 → 2026-08-31).

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| laboratoire → partenaire | riot:anthropic_rockdale_lease_2026 | bail de capacité | engagement non exécuté, non actualisé | environ 9 100 M$ | 2026-08-31 | 10-Q 0001104659-26-093448 | 1 |

#### AMD

1 arête, dont 0 à montant.

Sans montant admissible : amd:anthropic_helios_2gw (engagement d'achat, intention sans engagement, 8-K 0000002488-26-000121).

#### Broadcom

1 arête, dont 0 à montant.

Sans montant admissible : avgo:anthropic_tpu_capacity_2027 (engagement d'achat, signé, 8-K 0001193125-26-144028).

#### CoreWeave

1 arête, dont 0 à montant.

Sans montant admissible : crwv:anthropic_partnership (engagement d'achat, signé, 8-K 0001769628-26-000220).

#### Microsoft

1 arête, dont 0 à montant.

Sans montant admissible : msft:anthropic_investment (fonds propres, comptabilisé, 8-K 0001193125-26-323632).

#### NVIDIA

1 arête, dont 0 à montant.
- Exposition du partenaire au 2026-07-26 (`counterparty_exposure`) : engagements non appelés (plafond) 10 000 M$.

Sans montant admissible : nvda:anthropic_investment (fonds propres, signé, 10-Q 0001045810-25-000230).

#### Nscale GPU MCC B1.1 LLC

1 arête, dont 0 à montant.

Sans montant admissible : nscale:anthropic_gpu_services_order (engagement d'achat, signé, S-1 0001193125-26-395475).

#### SpaceX

1 arête, dont 1 à montant.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| laboratoire → partenaire | spcx:anthropic_cloud_services | engagement d'achat | redevance | 1 250 M$ (per month through May 2029) | 2026-06-12 | 424B4 0001628280-26-042639 | 1 |

#### erock inc

1 arête, dont 0 à montant.

Sans montant admissible : erock:anthropic_power_order (engagement d'achat, signé, 8-K 0001193125-26-344714).

### OpenAI

Partenaires : 7 ; arêtes : 125.

#### Microsoft

30 arêtes, dont 19 à montant.
- Exposition du partenaire au 2026-06-30 (`counterparty_exposure`) : engagements non appelés (plafond) 13 000 M$ ; au coût (participation) 11 900 M$.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| laboratoire → partenaire | msft:openai_azure_2025 | engagement d'achat | engagement de capacité | 250 000 M$ | 2025-10-28 | 10-Q 0001193125-25-256321 | 1 |
| laboratoire → partenaire | msft:openai_commercial | revenu comptabilisé | revenu (brut) | 24 100 M$ | 2026-06-30 | 10-K 0001193125-26-323660 | 1 |
| partenaire → laboratoire | msft:openai_investment | fonds propres | autre, coût (versement) | 11 900 M$ | 2026-06-30 | 10-K 0001193125-26-323660 | 4 |
| partenaire → laboratoire | msft:openai_investment | fonds propres | autre, mise en équivalence (variation de valeur) | 6 500 M$ | 2026-06-30 | 10-K 0001193125-26-323660 | 13 |

Sans montant admissible : arête sans clé d'instrument (fonds propres, versé ou tiré, 8-K 0001104659-26-021050).

#### CoreWeave

25 arêtes, dont 18 à montant.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| laboratoire → partenaire | crwv:openai_commercial_agreement | paiement d'avance | avance, valeur au bilan | 450 M$ | 2025-03-31 | 10-Q 0001769628-25-000014 | 1 |
| laboratoire → partenaire | crwv:openai_commercial_agreement | engagement d'achat | engagement non exécuté | jusqu'à 11 900 M$ (through October 2030) | 2025-06-30 | 10-Q 0001769628-25-000041 | 4 |
| laboratoire → partenaire | crwv:openai_commercial_agreement | engagement d'achat | autre (engagement) | jusqu'à 11 550 M$ | 2025-03-31 | 424B4 0001193125-25-067651 | 1 |
| laboratoire → partenaire | crwv:openai_msa_2025 | engagement d'achat | engagement de capacité | jusqu'à 6 500 M$ | 2025-09-23 | 8-K 0001193125-25-216497 | 2 |
| partenaire → laboratoire | crwv:openai_ipo_shares_contra_revenue | titres ou bons remis au client | contrepartie payable au client, valeur au bilan | 298 M$ | 2025-09-30 | 10-Q 0001769628-25-000062 | 6 |
| partenaire → laboratoire | crwv:openai_ipo_shares_contra_revenue | titres ou bons remis au client | contrepartie payable au client | 350 M$ | 2025-03-31 | 10-Q 0001769628-25-000062 | 4 |

Sans montant admissible : crwv:openai_msa (engagement d'achat, signé, 8-K 0001769628-25-000033) ; crwv:openai_of2_2025 (engagement d'achat, signé, 8-K 0001193125-25-227562).

#### Amazon

21 arêtes, dont 9 à montant.
- Exposition du partenaire au 2026-06-30 (`counterparty_exposure`) : engagements non appelés (plafond) 50 000 M$ ; au bilan (participation) 28 700 M$ ; au coût (participation) 28 700 M$.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| laboratoire → partenaire | amzn:openai_aws_2025 | engagement d'achat | engagement de capacité | 38 000 M$ | 2026-06-30 | 10-Q 0001018724-26-000026 | 2 |
| laboratoire → partenaire | amzn:openai_aws_2026 | engagement d'achat | engagement de capacité | 100 000 M$ | 2026-03-31 | 10-Q 0001018724-26-000026 | 2 |
| partenaire → laboratoire | amzn:openai_series_c_2026 | fonds propres | versement | 15 000 M$ | 2026-03-31 | 10-Q 0001018724-26-000026 | 2 |
| partenaire → laboratoire | amzn:openai_series_c_2026 | fonds propres | valeur au bilan | 28 700 M$ | 2026-06-30 | 10-Q 0001018724-26-000026 | 1 |
| partenaire → laboratoire | amzn:openai_series_c_commitment_2026 | fonds propres | versement | 21 300 M$ | 2026-07-31 | 10-Q 0001018724-26-000026 | 2 |

Sans montant admissible : amzn:openai_collaboration_2026 (achat, signé, 8-K 0001104659-26-021050).

#### Cerebras Systems Inc.

21 arêtes, dont 11 à montant.
- Capacités balisées (jamais additionnées) : 250 MW (unité balisée : megawatt), `CommittedComputeCapacityIncludedInRemainingPerformanceObligations` (au 2026-03-31) ; 750 MW (unité balisée : megawatt), `CommittedComputeCapacityUnderMasterRelationshipAgreement` (au 2025-12-31) ; 2 GW, `MaximumTotalComputeCapacityUnderMasterRelationshipAgreement` (au 2025-12-31) ; 1,25 GW, `OptionToPurchaseAdditionalComputeCapacity` (au 2025-12-31).

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| laboratoire → partenaire | cerebras:openai_mra | revenu comptabilisé | revenu (net) | 74 M$ | 2026-06-30 | 10-Q 0001628280-26-056357 | 2 |
| laboratoire → partenaire | cerebras:openai_working_capital_loan | prêt ou facilité | versement | environ 1 000 M$ | 2026-01-31 | 10-Q 0001628280-26-056357 | 1 |
| laboratoire → partenaire | cerebras:openai_working_capital_loan | prêt ou facilité | versement, encours | 918 M$ | 2026-06-30 | 10-Q 0001628280-26-056357 | 1 |
| partenaire → laboratoire | cerebras:openai_class_n_warrant | titres ou bons remis au client | contrepartie payable au client | 3 M$ | 2026-06-30 | 10-Q 0001628280-26-056357 | 2 |
| partenaire → laboratoire | cerebras:openai_class_n_warrant | titres ou bons remis au client | contrepartie payable au client | jusqu'à 33 445 026 actions | 2026-08-12 | 10-Q 0001628280-26-056357 | 5 |

#### AMD

11 arêtes, dont 5 à montant.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| partenaire → laboratoire | amd:openai_warrant_2025 | titres ou bons remis au client | contrepartie payable au client | jusqu'à 160 000 000 actions | 2026-06-27 | 10-Q 0000002488-26-000123 | 5 |

Sans montant admissible : amd:openai_supply_2025 (engagement d'achat, signé, 10-Q 0000002488-26-000123).

#### SoftBank

11 arêtes, dont 8 à montant.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| partenaire → laboratoire | sbenergy:openai_software_minimums | engagement d'achat | engagement non exécuté, non actualisé | 25 M$ (2028) | 2028-12-31 | S-1/A 0001628280-26-062846 | 3 |
| partenaire → laboratoire | sbenergy:openai_warrants | titres ou bons remis au client | contrepartie payable au client, juste valeur | 733 M$ | 2026-06-30 | S-1/A 0001628280-26-062846 | 2 |
| partenaire → laboratoire | sbenergy:openai_warrants | titres ou bons remis au client | contrepartie payable au client | jusqu'à 3 991 809 actions | 2026-09-01 | S-1 0001628280-26-059639 | 2 |
| partenaire → laboratoire | sbenergy:openai_warrants | titres ou bons remis au client | juste valeur | environ 5 500 M$ | 2026-06-30 | S-1/A 0001628280-26-062846 | 1 |

Sans montant admissible : arête sans clé d'instrument (fonds propres, versé ou tiré, 8-K 0001104659-26-021050).

#### NVIDIA

6 arêtes, dont 2 à montant.

| Sens | Instrument | Type | Nature | Dernier montant | Date | Pièce | Montants publiés |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| partenaire → laboratoire | nvda:portsmouth_rvg_2026 | garantie de valeur résiduelle | montant garanti, plafond | au plus 105 000 M$ | 2026-08-17 | 8-K 0001045810-26-000069 | 1 |
| partenaire → laboratoire | nvda:portsmouth_rvg_2026 | garantie de valeur résiduelle | montant garanti | au plus 105 000 M$ | 2026-09-01 | S-1 0001628280-26-059639 | 1 |

Sans montant admissible : arête sans clé d'instrument (fonds propres, versé ou tiré, 8-K 0001104659-26-021050) ; nvda:openai_investment (fonds propres, intention sans engagement, 10-Q 0001045810-25-000230).

## Contrats des laboratoires : tranches, échéances, sorties (D-0067, volet 8)

Clauses lues dans les pièces contractuelles déposées (EX-10, EX-4, EX-2) et dans les résumés des déposants, telles qu'écrites : tranches d'acquisition, durées et échéances, clauses de sortie, exclusivités, engagements minimaux et calendriers de livraison (`lab_contract_clause`). Une clause caviardée le reste ; une quantité est celle du texte, jamais un total. Le déclarant est le déposant de la pièce.

### OpenAI

Clauses : 59, de 19 contrats ou instruments.

| Déclarant | Contrat | Clause | Date | Quantité | Condition | Pièce |
| --- | --- | --- | --- | ---: | --- | --- |
| AMD | amd:openai_registration_rights | durée | 2033-10-05 (fin de période) | — | — | 8-K EX-10.1 0001193125-25-230895 |
| AMD | amd:openai_supply_2025 | engagement minimal | 2025-10-06 (date de la pièce) | 1 GW | ferme | 8-K 0001193125-25-230895 |
| AMD | amd:openai_warrant_2025 | clause de sortie | 2025-10-06 (date de la pièce) | — | sous condition ; résiliation anticipée pour faute du contrat d'approvisionnement par AMD : annulation des parts non acquises ou non exerçables | 8-K EX-4.1 0001193125-25-230895 |
| AMD | amd:openai_warrant_2025 | tranche d'acquisition | 2025-10-06 (date de la pièce) | — | sous condition ; livraison du premier gigawatt de GPU MI450, sous réserve des cours cibles de l'action et de conditions techniques et commerciales avant exe… | 8-K 0001193125-25-230895 |
| AMD | amd:openai_warrant_2025 | tranche d'acquisition | 2025-10-06 (date de la pièce) | 160 000 000 actions | sous condition ; achat de six gigawatts de GPU Instinct par OpenAI, ses affiliés ou des acheteurs autorisés, et cours de l'action AMD croissant jusqu'à 600 … | 8-K 0001193125-25-230895 |
| AMD | amd:openai_warrant_2025 | tranche d'acquisition | 2025-10-06 (date de la pièce) | — | caviardée | 8-K EX-4.1 0001193125-25-230895 |
| AMD | amd:openai_warrant_2025 | durée | 2030-10-05 (fin de période) | — | — | 8-K EX-4.1 0001193125-25-230895 |
| Amazon | amzn:openai_commitment_guarantee_2026 | durée | 2026-02-27 (date de la pièce) ; « Outside Date » | — | — | 8-K EX-10.1 0001104659-26-021050 |
| Amazon | amzn:openai_series_c_commitment_2026 | engagement minimal | 2026-04-30 (date de la pièce) | — | sous condition ; jalons précisés atteints par OpenAI, ou introduction en bourse ou cotation directe d'OpenAI aux États-Unis ; achats au choix d'Amazon avant… | 10-Q 0001018724-26-000014 |
| Amazon | amzn:openai_series_c_commitment_2026 | durée | 2028-12-31 (fin de période) ; « December 31, 2028 (such earliest date, the "Outside Date") » | — | sous condition ; fin de l'engagement à la première de ces dates : financement complet, résiliation valable de l'accord de collaboration conjointe, douze moi… ; caviardée | 8-K EX-10.1 0001104659-26-021050 |
| Cerebras Systems Inc. | cerebras:openai_class_n_warrant | durée | 2026-04-17 (date de la pièce) ; « ten (10) year anniversary of the Issue Date » | — | sous condition ; expiration anticipée cinq jours ouvrés après la première date sans engagement ferme d'achat de capacité ni paiement dû au titre du MRA | S-1 EX-10.13 0001628280-26-025762 |
| Cerebras Systems Inc. | cerebras:openai_class_n_warrant | tranche d'acquisition | 2026-04-17 (date de la pièce) | 4 459 337 actions | sous condition ; dépôt du prêt de fonds de roulement d'OpenAI sur le compte séquestre ; caviardée | S-1 EX-10.13 0001628280-26-025762 |
| Cerebras Systems Inc. | cerebras:openai_mra | engagement minimal | 2026-02-15 (fin de période) ; « by February 15, 2026 » | — | sous condition ; contrat d'achat de matériel Cerebras à négocier d'ici le 15 février 2026, en plus ou à la place des services | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | calendrier de livraison | 2026-05-04 (date de la pièce) ; « by [***] 2029 ; by [***] 2030 » | — | au choix d'une partie ; option d'OpenAI sur une capacité additionnelle, en MW caviardés, livrable en 2029 puis en 2030, exerçable sur préavis caviardé ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | calendrier de livraison | 2026-05-04 (date de la pièce) | — | caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | exclusivité | 2026-05-04 (date de la pièce) | — | sous condition ; tant que Cerebras n'est pas en manquement grave, jusqu'à une date caviardée ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | exclusivité | 2026-05-04 (date de la pièce) | — | sous condition ; tant qu'OpenAI n'est pas en manquement grave, pendant la période d'exclusivité ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | engagement minimal | 2026-05-04 (date de la pièce) | — | ferme ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | clause de sortie | 2026-05-04 (date de la pièce) | — | sous condition ; manquement grave d'OpenAI, défaut de paiement compris, non réparé dans un délai caviardé après escalade ; cessation d'activité sans success… ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | clause de sortie | 2026-05-04 (date de la pièce) | — | sous condition ; manquement grave de Cerebras non réparé dans un délai caviardé après escalade ; cessation d'activité sans successeur ; procédure collective… ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | clause de sortie | 2026-05-04 (date de la pièce) | — | sous condition ; segment de capacité non livré à la date engagée de l'annexe A, retard prolongé au-delà d'un délai caviardé ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | clause de sortie | 2026-05-04 (date de la pièce) | — | sous condition ; changement de contrôle de Cerebras au profit d'un acquéreur d'une catégorie caviardée : avenant à signer avec OpenAI, contenu caviardé ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | clause de sortie | 2026-05-04 (date de la pièce) | — | sous condition ; cession du contrat à un concurrent nommé de l'autre partie, ou acquisition par un tel concurrent, pendant la période d'exclusivité | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | durée | 2026-05-04 (date de la pièce) ; « 3 years thereafter ; four years thereafter » | — | caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | durée | 2026-05-04 (date de la pièce) ; « maximum 5 year term » | — | au choix d'une partie ; renouvellement d'un an, deux fois pour les segments de trois ans, une fois pour ceux de quatre ans, sur avis écrit à Cerebras dans un délai… | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_mra | calendrier de livraison | 2026-12-31 (fin de période) ; « by the end of calendar year 2026 » | 250 MW | ferme ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_registration_rights | durée | 2026-04-17 (date de la pièce) ; « the later of (x) the three-year anniversary of expiration of the Warrant and (y… » | — | — | S-1 EX-10.14 0001628280-26-025762 |
| Cerebras Systems Inc. | cerebras:openai_working_capital_loan | échéance | 2026-04-17 (date de la pièce) | — | sous condition ; cas de défaut : défaut de paiement en numéraire, manquement à des engagements non régularisé en trente jours, liquidation ou insolvabilité,… ; caviardée | S-1 EX-10.12 0001628280-26-025762 |
| Cerebras Systems Inc. | cerebras:openai_working_capital_loan | échéance | 2026-04-17 (date de la pièce) | — | sous condition ; résiliation du MRA pour une autre raison qu'un manquement grave non réparé d'OpenAI, ou cas caviardé ; caviardée | S-1 EX-10.12 0001628280-26-025762 |
| Cerebras Systems Inc. | cerebras:openai_working_capital_loan | échéance | 2026-04-17 (date de la pièce) | — | caviardée | S-1 EX-10.12 0001628280-26-025762 |
| Cerebras Systems Inc. | cerebras:openai_working_capital_loan | échéance | 2026-05-04 (date de la pièce) | — | sous condition ; résiliation du MRA pour une autre raison qu'un manquement grave non réparé d'OpenAI (ou un cas caviardé) : au choix d'OpenAI, remboursement… ; caviardée | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | cerebras:openai_working_capital_loan | échéance | 2032-12-31 (fin de période) | 1 005 M$ | — | S-1 EX-10.12 0001628280-26-025762 |
| CoreWeave | crwv:openai_commercial_agreement | durée | 2025-03-12 (date de la pièce) ; « through October 2030 » | 11 900 M$ | sous condition ; sous réserve des cas de résiliation et du respect des exigences de livraison et de disponibilité du service ; obligations d'OpenAI subordon… | S-1/A 0001193125-25-052207 |
| CoreWeave | crwv:openai_msa | engagement minimal | 2025-03-12 (date de la pièce) | — | sous condition ; résiliation par CoreWeave pour faute du client, dont le non-paiement : montant caviardé dû par le client, diminué du produit de la revente … ; caviardée | S-1/A EX-10.24 0001193125-25-052207 |
| CoreWeave | crwv:openai_msa | clause de sortie | 2025-03-12 (date de la pièce) ; « thirty (30) consecutive days or longer » | — | sous condition ; force majeure prolongée trente jours consécutifs ou plus : résiliation du bon touché par le client et remboursement des avances non consomm… | S-1/A EX-10.24 0001193125-25-052207 |
| CoreWeave | crwv:openai_msa | clause de sortie | 2025-03-12 (date de la pièce) | — | sous condition ; manquement grave non réparé dans un délai caviardé (délai propre, non prolongeable, pour le non-paiement), ou procédure collective de l'aut… ; caviardée | S-1/A EX-10.24 0001193125-25-052207 |
| CoreWeave | crwv:openai_msa | clause de sortie | 2025-03-12 (date de la pièce) | — | au choix d'une partie ; résiliation par le client pour procédure collective de CoreWeave : option du client d'exiger la cession du bon, du contrat et du contrat de… | S-1/A EX-10.24 0001193125-25-052207 |
| CoreWeave | crwv:openai_msa | durée | 2025-03-12 (date de la pièce) | — | — | S-1/A EX-10.24 0001193125-25-052207 |
| CoreWeave | crwv:openai_msa_2025 | exclusivité | 2025-09-25 (date de la pièce) | — | — | S-4/A EX-10.32 0001140361-25-036118 |
| CoreWeave | crwv:openai_msa_2025 | engagement minimal | 2025-09-25 (date de la pièce) | — | sous condition ; résiliation par CoreWeave pour faute du client, dont le non-paiement : montant caviardé dû par le client, diminué du produit de la revente … ; caviardée | S-4/A EX-10.32 0001140361-25-036118 |
| CoreWeave | crwv:openai_msa_2025 | clause de sortie | 2025-09-25 (date de la pièce) | — | sous condition ; manquement grave non réparé dans un délai caviardé (délai propre, caviardé et non prolongeable, pour le non-paiement), ou procédure collect… ; caviardée | S-4/A EX-10.32 0001140361-25-036118 |
| CoreWeave | crwv:openai_msa_2025 | clause de sortie | 2025-09-25 (date de la pièce) ; « thirty (30) consecutive days or longer » | — | sous condition ; force majeure prolongée trente jours consécutifs ou plus : résiliation du bon touché par le client et remboursement des avances non consomm… | S-4/A EX-10.32 0001140361-25-036118 |
| CoreWeave | crwv:openai_msa_2025 | durée | 2025-09-25 (date de la pièce) | — | — | S-4/A EX-10.32 0001140361-25-036118 |
| DigitalBridge Group, Inc. | stargate:vantage_frontier_lighthouse | calendrier de livraison | 2025-10-30 (date de la pièce) ; « first delivery in H2 2026 with phased completion by 2028 » | — | — | 8-K EX-99.1 0001679688-25-000096 |
| Microsoft | msft:openai_partnership | exclusivité | 2023-07-27 (date de la pièce) | — | — | 10-K 0000950170-23-035122 |
| Microsoft | msft:openai_partnership | exclusivité | 2025-07-30 (date de la pièce) | — | — | 10-K 0000950170-25-100235 |
| NVIDIA | nvda:portsmouth_rvg_2026 | exclusivité | 2026-08-17 (date de la pièce) | 4,25 GW | — | 8-K 0001045810-26-000069 |
| NVIDIA | nvda:portsmouth_rvg_2026 | durée | 2026-08-17 (date de la pièce) ; « the 20th anniversary of the commencement of the applicable lease » | — | sous condition ; fin anticipée sur résiliation du bail par OpenAI selon ses termes, note de crédit satisfaisante d'OpenAI, ou autres cas usuels | 8-K 0001045810-26-000069 |
| NVIDIA | nvda:sb_energy_openai_guarantees | calendrier de livraison | 2026-08-26 (date de la pièce) ; « the first of which is expected in fiscal year 2029 » | — | — | 10-Q 0001045810-26-000075 |
| SoftBank | nvda:portsmouth_rvg_2026 | durée | 2026-09-01 (date de la pièce) | — | sous condition ; note de crédit désignée atteinte par OpenAI Group PBC, ou garanties ou baux de remplacement fournis | S-1 0001628280-26-059639 |
| SoftBank | sbenergy:openai_registration_rights | durée | 2026-09-21 (date de la pièce) | — | sous condition ; l'accord prend fin quand aucun porteur ne détient d'actions ; les droits d'un porteur tombent sous 1 % du capital s'il peut tout vendre sou… | S-1/A EX-10.37 0001628280-26-062846 |
| SoftBank | sbenergy:openai_warrants | tranche d'acquisition | 2026-09-01 (date de la pièce) | 868 934 actions | sous condition ; signature de baux NNN pour 800 MW de charge IT au projet d'Orion, acquisition au prorata en deçà | S-1 EX-4.1 0001628280-26-059639 |
| SoftBank | sbenergy:openai_warrants | tranche d'acquisition | 2026-09-01 (date de la pièce) | 408 942 actions | sous condition ; bouclage financier (Financial Close) d'au moins 753 MW de charge IT au projet d'Orion, acquisition au prorata en deçà | S-1 EX-4.1 0001628280-26-059639 |
| SoftBank | sbenergy:openai_warrants | tranche d'acquisition | 2026-09-01 (date de la pièce) ; « six (6) years from the date hereof » | — | sous condition ; changement de contrôle de la société (fusion, cession de l'essentiel des actifs ou du capital, liquidation, procédure collective) : acquisi… | S-1 EX-4.1 0001628280-26-059639 |
| SoftBank | sbenergy:openai_warrants | tranche d'acquisition | 2026-09-01 (date de la pièce) | — | sous condition ; résiliation anticipée de l'accord-cadre par OpenAI (section 4.1(a)(ii)) : toute la part non acquise s'acquiert | S-1 EX-4.1 0001628280-26-059639 |
| SoftBank | sbenergy:openai_warrants | tranche d'acquisition | 2026-09-01 (date de la pièce) | — | sous condition ; manquement grave du groupe SBE à l'obligation d'obtenir l'accord écrit d'OpenAI, ou trois manquements graves sur un même projet (délai de r… | S-1 EX-4.1 0001628280-26-059639 |
| SoftBank | sbenergy:openai_warrants | tranche d'acquisition | 2026-09-01 (date de la pièce) | — | sous condition ; perte par OpenAI de ses droits sur un projet (section 4.3 de l'accord-cadre) : annulation de la part non acquise liée au projet | S-1 EX-4.1 0001628280-26-059639 |
| SoftBank | sbenergy:openai_warrants | tranche d'acquisition | 2026-09-21 (date de la pièce) | 868 933 actions | sous condition ; suite de la phrase hors de la fenêtre servie ; le même dépôt lie cette tranche à la fixation du prix d'une introduction en bourse qualifiée… | S-1/A 0001628280-26-062846 |
| SoftBank | sbenergy:openai_warrants | durée | 2036-01-09 (fin de période) | — | — | S-1 EX-4.1 0001628280-26-059639 |

### Anthropic

Clauses : 30, de 6 contrats ou instruments.

| Déclarant | Contrat | Clause | Date | Quantité | Condition | Pièce |
| --- | --- | --- | --- | ---: | --- | --- |
| Akamai | akam:anthropic_msa | clause de sortie | 2026-09-24 (date de la pièce) | — | sous condition ; manquement grave non réparé d'Akamai, ou changement de contrôle d'Akamai au profit d'un concurrent direct d'Anthropic | 8-K 0001193125-26-401048 |
| Akamai | akam:anthropic_msa | clause de sortie | 2026-09-24 (date de la pièce) | — | sous condition ; manquement non réparé d'Anthropic ; la résiliation d'un plan de projet pour manquement d'Anthropic ne vise que ce plan, les autres continue… | 8-K 0001193125-26-401048 |
| Akamai | akam:anthropic_msa | clause de sortie | 2026-09-24 (date de la pièce) | — | sous condition ; panne importante notifiée, sous conditions non décrites | 8-K 0001193125-26-401048 |
| Akamai | akam:anthropic_msa | durée | 2026-09-24 (date de la pièce) ; « initial seven-year term commencing on their respective service start dates » | — | — | 8-K 0001193125-26-401048 |
| Akamai | akam:anthropic_warrant | clause de sortie | 2026-09-24 (date de la pièce) | — | sous condition ; expiration ou résiliation du contrat-cadre, d'un plan de projet ou d'un accord d'extension avant la condition d'acquisition | 8-K EX-4.1 0001193125-26-401048 |
| Akamai | akam:anthropic_warrant | clause de sortie | 2026-09-24 (date de la pièce) | — | sous condition ; défaut de paiement de la valeur contractuelle due par Anthropic, non régularisé dans un délai caviardé après notification ; suspendu pendan… ; caviardée | 8-K EX-4.1 0001193125-26-401048 |
| Akamai | akam:anthropic_warrant | durée | 2026-09-24 (date de la pièce) ; « seventh anniversary of the Issue Date » | — | — | 8-K EX-4.1 0001193125-26-401048 |
| Akamai | akam:anthropic_warrant | tranche d'acquisition | 2026-09-24 (date de la pièce) | 40 % | sous condition ; premier paiement d'Anthropic (ou de ses affiliés) à Akamai au titre du plan de projet 3 | 8-K EX-4.1 0001193125-26-401048 |
| Akamai | akam:anthropic_warrant | tranche d'acquisition | 2026-09-24 (date de la pièce) | 60 % | sous condition ; accords d'extension portant la valeur contractuelle totale d'au moins 3,0 Md$, avant la fin des sept ans du plan de projet 3 | 8-K EX-4.1 0001193125-26-401048 |
| Akamai | akam:anthropic_warrant | tranche d'acquisition | 2026-09-24 (date de la pièce) | 80 % | sous condition ; accords d'extension portant la hausse cumulée de valeur contractuelle à au moins 6,0 Md$, avant la fin des sept ans du plan de projet 3 | 8-K EX-4.1 0001193125-26-401048 |
| Akamai | akam:anthropic_warrant | tranche d'acquisition | 2026-09-24 (date de la pièce) | 100 % | sous condition ; hausse cumulée de valeur contractuelle d'au moins 9,0 Md$ ; les tranches 2 à 4 doivent être atteintes avant la fin des sept ans du plan de … | 8-K EX-4.1 0001193125-26-401048 |
| Amazon | amzn:anthropic_financing_facility | durée | 2026-04-30 (date de la pièce) ; « 30 months after a liquidity event » | 20 000 M$ | sous condition ; montants rendus disponibles à mesure qu'Amazon atteint des jalons de livraison de capacité de calcul au titre de l'accord commercial modifi… | 10-Q 0001018724-26-000014 |
| Apollo | apollo:broadcom_capital_solution | calendrier de livraison | 2026-08-10 (date de la pièce) ; « beginning in mid-2026 » | — | — | 10-Q 0001858681-26-000040 |
| Nscale | nscale:anthropic_gpu_services_order | calendrier de livraison | 2026-09-18 (date de la pièce) | — | caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | calendrier de livraison | 2026-09-18 (date de la pièce) | — | sous condition ; retard du début de service au-delà de la période de grâce caviardée ; caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | exclusivité | 2026-09-18 (date de la pièce) | — | — | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | exclusivité | 2026-09-18 (date de la pièce) | — | — | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | exclusivité | 2026-09-18 (date de la pièce) | — | caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | clause de sortie | 2026-09-18 (date de la pièce) | — | sous condition ; manquement grave non réparé dans un délai caviardé, procédure d'insolvabilité, sortie du fournisseur du contrôle de la société mère, ou cha… ; caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | clause de sortie | 2026-09-18 (date de la pièce) | — | sous condition ; force majeure prolongée au-delà d'un délai caviardé qui empêche matériellement les services ; caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | clause de sortie | 2026-09-18 (date de la pièce) | — | sous condition ; le fournisseur cesse d'être une société affiliée contrôlée par la société mère (hors cession permise) | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | clause de sortie | 2026-09-18 (date de la pièce) | — | sous condition ; disponibilité mensuelle sous des seuils non publiés pendant des périodes prolongées | S-1 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | clause de sortie | 2026-09-18 (date de la pièce) | — | sous condition ; début de service d'une tranche retardé au-delà d'un délai caviardé après la date de livraison attendue ; caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | clause de sortie | 2026-09-18 (date de la pièce) | — | sous condition ; réclamation de contrefaçon visant les services non résolue par le fournisseur dans un délai caviardé ; caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | clause de sortie | 2026-09-18 (date de la pièce) | — | sous condition ; l'autre partie manque à ses obligations de contrôle des échanges ou devient une partie visée par des sanctions | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | clause de sortie | 2026-09-18 (date de la pièce) | — | sous condition ; financement des GPU et du centre de données non obtenu par le fournisseur à la date butoir (délai caviardé) ; caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | durée | 2026-09-18 (date de la pièce) | — | sous condition ; durée de chaque tranche à compter de sa réception, en mois caviardés ; réduite au choix d'Anthropic d'un retard au-delà d'un seuil caviardé ; caviardée | S-1 EX-10.25 0001193125-26-395475 |
| Nscale | nscale:anthropic_gpu_services_order | durée | 2026-09-18 (date de la pièce) | — | au choix d'une partie ; prolongation de la durée d'une tranche au choix d'Anthropic, sur préavis caviardé, aux mêmes conditions sauf ajustement caviardé du prix ; caviardée | S-1 EX-10.25 0001193125-26-395475 |
| TeraWulf | wulf:justified_anthropic_lease | calendrier de livraison | 2026-07-06 (date de la pièce) ; « in phases beginning in late 2027 and concluding in early 2028 » | — | — | 8-K 0001104659-26-080583 |
| TeraWulf | wulf:justified_anthropic_lease | durée | 2026-07-06 (date de la pièce) ; « a term of 20 years thereafter ; two successive five-year renewal options » | — | au choix d'une partie | 8-K 0001104659-26-080583 |

## Calendrier des capacités des laboratoires (D-0067, volet 8)

Capacités en MW ou en GW écrites dans les pièces pour un laboratoire nommé (`lab_capacity`), telles qu'écrites : jamais additionnées, ni entre elles, ni aux dollars, jamais converties de MW en GW. Les capacités de calcul (puces, serveurs, nuage) sont mises face aux capacités d'hébergement (centres de données, charge IT) et d'électricité que les déclarants disent avoir contractées ; une capacité écrite sans le laboratoire n'y figure pas.

### OpenAI

**Calcul** : 8 lignes.

| Déclarant | Contrepartie écrite | Genre | Capacité | Statut | Calendrier | Pièce |
| --- | --- | --- | ---: | --- | --- | --- |
| AMD | OpenAI OpCo, LLC | calcul | 1 GW | signé | 2025-10-06 (date de la pièce) | 8-K 0001193125-25-230895 |
| AMD | OpenAI OpCo, LLC | calcul | 6 GW | intention sans engagement | 2025-10-06 (date de la pièce) | 8-K 0001193125-25-230895 |
| NVIDIA | OpenAI | calcul | au moins 10 GW | intention sans engagement | 2025-11-19 (date de la pièce) | 8-K 0001045810-25-000228 |
| Amazon | OpenAI | calcul | environ 2 GW | signé | 2026-04-29 (date de la pièce) ; « begins ramping in 2027 » | 8-K 0001018724-26-000012 |
| Cerebras Systems Inc. | OpenAI OpCo, LLC | calcul | 750 MW | signé | 2026-08-12 (date de la pièce) ; « multi-year term » | 10-Q 0001628280-26-056357 |
| Cerebras Systems Inc. | OpenAI | calcul | 250 MW | signé | 2026-12-31 (fin de période) ; « by the end of calendar year 2026 » | S-1/A EX-10.11 0001628280-26-029503 |
| Cerebras Systems Inc. | OpenAI OpCo, LLC | calcul | 1,25 GW | intention sans engagement | 2030-12-31 (fin de période) ; « by the end of 2030 » | 10-Q 0001628280-26-056357 |
| Cerebras Systems Inc. | OpenAI OpCo, LLC | calcul | jusqu'à 2 GW | intention sans engagement | 2030-12-31 (fin de période) ; « by the end of 2030 » | 10-Q 0001628280-26-056357 |

**Hébergement, électricité et non précisé** : 10 lignes.

| Déclarant | Contrepartie écrite | Genre | Capacité | Statut | Calendrier | Pièce |
| --- | --- | --- | ---: | --- | --- | --- |
| DigitalBridge Group, Inc. | OpenAI | hébergement | 1,40 GW | — | 2025-10-30 (date de la pièce) | 8-K EX-99.1 0001679688-25-000096 |
| DigitalBridge Group, Inc. | OpenAI | hébergement | environ 1 GW | — | 2025-10-30 (date de la pièce) | 8-K EX-99.1 0001679688-25-000096 |
| WEC ENERGY GROUP, INC. | OpenAI | électricité | 1,30 GW | intention sans engagement | 2025-12-05 (date de la pièce) ; « through 2030 » | 8-K EX-99.1 0000783325-25-000068 |
| WEC ENERGY GROUP, INC. | OpenAI | électricité | jusqu'à 3,50 GW | intention sans engagement | 2025-12-05 (date de la pièce) ; « over time » | 8-K EX-99.1 0000783325-25-000068 |
| GraniteShares ETF Trust | OpenAI | hébergement | 1,20 GW | — | 2026-05-18 (date de la pièce) | 485APOS 0001493152-26-024144 |
| NVIDIA | OpenAI | hébergement | environ 4,25 GW | signé | 2026-08-17 (date de la pièce) | 8-K 0001045810-26-000069 |
| NVIDIA | OpenAI | hébergement | environ 3,80 GW | intention sans engagement | 2026-08-26 (date de la pièce) | 10-Q 0001045810-26-000075 |
| SoftBank | — | hébergement | 800 MW | signé | 2026-09-01 (date de la pièce) | S-1 EX-4.1 0001628280-26-059639 |
| SoftBank | OpenAI Group PBC | hébergement | 4,25 GW | signé | 2026-09-01 (date de la pièce) | S-1 0001628280-26-059639 |
| SoftBank | OpenAI | hébergement | environ 3,78 GW | signé | 2026-09-21 (date de la pièce) | S-1/A 0001628280-26-062846 |

### Anthropic

**Calcul** : 4 lignes.

| Déclarant | Contrepartie écrite | Genre | Capacité | Statut | Calendrier | Pièce |
| --- | --- | --- | ---: | --- | --- | --- |
| NVIDIA | Anthropic | calcul | 1 GW | intention sans engagement | 2025-11-19 (date de la pièce) ; « initially » | 8-K 0001045810-25-000228 |
| Broadcom | Anthropic | calcul | environ 3,50 GW | signé | 2026-04-06 (date de la pièce) ; « beginning in 2027 » | 8-K 0001193125-26-144028 |
| Amazon | Anthropic | calcul | jusqu'à 5 GW | signé | 2026-04-29 (date de la pièce) | 8-K 0001018724-26-000012 |
| AMD | Anthropic | calcul | jusqu'à 2 GW | intention sans engagement | 2026-08-04 (date de la pièce) | 8-K 0000002488-26-000121 |

**Hébergement, électricité et non précisé** : 5 lignes.

| Déclarant | Contrepartie écrite | Genre | Capacité | Statut | Calendrier | Pièce |
| --- | --- | --- | ---: | --- | --- | --- |
| Hut 8 | Anthropic | hébergement | jusqu'à 2 295 MW | intention sans engagement | 2026-02-25 (date de la pièce) | 10-K 0001104659-26-019392 |
| Hut 8 | Anthropic | hébergement | jusqu'à 1 050 MW | intention sans engagement | 2026-02-25 (date de la pièce) | 10-K 0001104659-26-019392 |
| Hut 8 | Anthropic | hébergement | au moins 245 MW | signé | 2026-02-25 (date de la pièce) | 8-K 0001104659-26-019393 |
| TeraWulf | Anthropic | hébergement | environ 401 MW | signé | 2026-07-06 (date de la pièce) | 8-K 0001104659-26-080583 |
| ERock, Inc. | Anthropic | électricité | 470 MW | signé | 2026-08-11 (date de la pièce) ; « extending production commitments into 2028 » | 8-K EX-99.1 0001193125-26-344714 |

## Événements propres aux laboratoires (D-0067, volet 9 ; hors annexe F)

Cinq observables datés, fixés avant toute lecture (D-0067, point 7), par laboratoire et trimestre civil, de 2021 T1 au dernier trimestre clos : L1 engagement réduit, L2 fin d'une exclusivité, L3 marque en baisse chez un actionnaire (valeur par action déclarée par un fonds, sous celle de sa date précédente pour le même titre, ou perte de valeur écrite), L4 garantie appelée, L5 site retardé. Ce n'est pas l'annexe F, liste fermée ; aucune somme, aucun score. L1, L2, L4 et L5 ne voient que les pièces en cache : un trimestre sans fait lu est « non déterminé », jamais « sans événement ».

| Laboratoire | Événement | Événement daté | Sans événement | Non déterminé |
| --- | --- | ---: | ---: | ---: |
| OpenAI | L1 engagement réduit | 0 | 0 | 23 |
| OpenAI | L2 fin d'une exclusivité | 1 | 0 | 22 |
| OpenAI | L3 marque en baisse chez un actionnaire | 3 | 6 | 14 |
| OpenAI | L4 garantie appelée | 0 | 0 | 23 |
| OpenAI | L5 site retardé | 0 | 0 | 23 |
| Anthropic | L1 engagement réduit | 0 | 0 | 23 |
| Anthropic | L2 fin d'une exclusivité | 0 | 0 | 23 |
| Anthropic | L3 marque en baisse chez un actionnaire | 4 | 6 | 13 |
| Anthropic | L4 garantie appelée | 0 | 0 | 23 |
| Anthropic | L5 site retardé | 0 | 0 | 23 |

Trimestres à événement :

| Laboratoire | Événement | Trimestre | Fait | Pièces |
| --- | --- | --- | --- | --- |
| Anthropic | L3 marque en baisse chez un actionnaire | 2024-04-01 → 2024-06-30 | series:S000007755, « anthropic pbc ser b pc pp » : 30,004 au 2024-03-31, 30,000 au 2024-06-30 (valeur par action, USD) | 0001752724-24-194634 |
| Anthropic | L3 marque en baisse chez un actionnaire | 2024-07-01 → 2024-09-30 | series:S000005322, « anthropic pbc ser b pc pp » : 30,004 au 2024-04-30, 30,000 au 2024-07-31 (valeur par action, USD) | 0001752724-24-217980 |
| Anthropic | L3 marque en baisse chez un actionnaire | 2025-04-01 → 2025-06-30 | series:S000005322, « anthropic pbc ser b pc pp » : 56,09 au 2025-01-31, 50,53 au 2025-04-30 (valeur par action, USD) ; series:S000005322, « anthropic pbc series d pc pp » : 58,50 au 2025-01-31, 52,74 au 2025-04-30 (valeur par action, USD) ; series:S000007195, « anthropic pbc series d pc pp » : 58,50 au 2025-01-31, 52,74 au 2025-04-30 (valeur par action, USD) ; 2 autres baisses (détail dans `series.md`) | 0001752724-25-159817, 0001752724-25-159875 |
| Anthropic | L3 marque en baisse chez un actionnaire | 2025-10-01 → 2025-12-31 | series:S000005322, « anthropic pbc ser b pc pp » : 147,49 au 2025-07-31, 140,97 au 2025-10-31 (valeur par action, USD) ; series:S000007195, « anthropic pbc series e pc pp » : 147,49 au 2025-07-31, 140,97 au 2025-10-31 (valeur par action, USD) ; series:S000042624, « anthropic pbc series e pc pp » : 147,49 au 2025-07-31, 140,97 au 2025-10-31 (valeur par action, USD) ; 45 autres baisses (détail dans `series.md`) | 0000035402-25-002863, 0000035402-25-002869, 0000035402-25-003008 |
| OpenAI | L2 fin d'une exclusivité | 2025-10-01 → 2025-12-31 | 10-Q de Microsoft du 29 octobre 2025, événement postérieur : nouvel accord définitif du 28 octobre 2025 avec OpenAI ; Microsoft perd son droit de premier refus comme fournisseur de calcul d'OpenAI, qui s'engage à achete… | 0001193125-25-256321 |
| OpenAI | L3 marque en baisse chez un actionnaire | 2026-01-01 → 2026-03-31 | cik:0001905088, « openai global llc » : 651,79 au 2025-10-31, 483,12 au 2026-01-30 (valeur par action, USD) | 0000940400-26-012609 |
| OpenAI | L3 marque en baisse chez un actionnaire | 2026-04-01 → 2026-06-30 | series:S000005111, « openai group pbc a pp » : 693,90 au 2026-02-28, 687,69 au 2026-05-31 (valeur par action, USD) ; series:S000005111, « openai group pbc a-2 pc pp » : 693,90 au 2026-02-28, 687,69 au 2026-05-31 (valeur par action, USD) ; series:S000005111, « openai group pbc a-3 pc pp » : 693,90 au 2026-02-28, 687,69 au 2026-05-31 (valeur par action, USD) ; 20 autres baisses (détail dans `series.md`) | 0000035402-26-004618 |
| OpenAI | L3 marque en baisse chez un actionnaire | 2026-07-01 → 2026-09-30 | cik:0001905088, « openai group pbc » : 687,69 au 2026-04-30, 678,11 au 2026-07-31 (valeur par action, USD) ; cik:0001905088, « openai group pbc series c » : 687,69 au 2026-04-30, 678,11 au 2026-07-31 (valeur par action, USD) ; series:S000042977, « openai group pbc series c » : 687,69 au 2026-04-30, 678,11 au 2026-07-31 (valeur par action, USD) ; 2 autres baisses (détail dans `series.md`) | 0000940400-26-036464, 0000940400-26-037955 |

## Évolution

Premier passage : aucune exécution antérieure à laquelle comparer. Les séries trimestrielles complètes, ruptures de base marquées, sont dans `series.md` ; `delta.md` sera le point d'entrée des exécutions suivantes.

## Ce qui n'a pas pu être établi

Cellules indéterminées en vue `as_known`, par motif : non balisé 15 920, concept non résolu 7 175, terme manquant 6 395, non publié 5 819, historique tronqué 4 291, période antérieure absente 1 740, annuel seulement 1 116, non traité (unité de la découverte non encore lue, ou bloc de §14 fermé) 1 042, client anonyme 748, précondition non remplie 742, dénominateur négatif ou nul 565, recherche incomplète 522, frontière de retraitement 195, caviardé 176, non collecté 152, période non écoulée à la date de coupure 113, intervalle à cheval sur le seuil 89, faits en conflit 86, date manquante 20, dénominateur sous le seuil 10, lecture impossible 8, entité non confirmée 2.

