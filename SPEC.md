# Spec d'exécution v6.14 — Fragilité financière de la chaîne IA dans les dépôts SEC

**Version 6.14, 25 septembre 2026.** Réécriture courte de la v5 du même jour : mêmes règles comptables, mêmes seuils (annexe E), mêmes faits vérifiés (annexe D). La fragilité financière devient l'objet du modèle et la circularité l'une de ses familles, un audit final indépendant (annexe C) remplace les mécanismes par lesquels le programme se surveillait lui-même, et le travail commence par un premier passage borné dont on mesure le rendement avant d'aller plus loin (§11.1). L'exécutant lit lui-même le texte et en tire les observations, bloc par bloc : le code sert les blocs et valide ce qu'il écrit (§7.4). AMD, Broadcom et Marvell rejoignent les huit groupes de la v5 (§10.1), et leurs faits vérifiés s'ajoutent à l'annexe D.

## 0. Mode d'emploi

**Rôles.** L'utilisateur, seul et non comptable, fournit le User-Agent, reçoit l'empreinte des critères des annexes E et F avant toute requête puis deux pages de point de contrôle (§11.3), et décide seul d'étendre le premier passage (§11.1) ; il ne tranche rien de technique. L'exécutant, Claude Opus 5.5 (« tu »), écrit le code, lit lui-même le texte et en tire les observations, sans appel à un modèle par API (§7.4), tranche les questions techniques (§11.2) et livre. Le code seul émet les requêtes et écrit tables et rendus ; ce que tu extrais n'entre dans `observations` que par un fichier que le code valide. L'auditeur, un autre agent Opus 5.5, indépendant, reçoit `audit/` et l'annexe C, rien d'autre (§12.2).

**Conventions.** Prose en français, identifiants en anglais sans accent. Un seul fichier de configuration, `config.yaml` (données de départ en annexe B) : User-Agent, groupes, entités connues, lexique initial, fenêtre, périmètre, seuils, plafond de lecture, délai de péremption du verrou de session, registre des paires non additives, critères des annexes E et F. Chaque énumération nommée dans cette spec est une contrainte de colonne du schéma (`schema.sql`, types ENUM de DuckDB) : une valeur absente du schéma n'existe pas, pour qu'une faute de frappe ne scinde pas une catégorie. Les ajouts de la v6 à la v5 sont marqués « ajout v6 ».

**Principes.** Chaque section indique entre crochets ce qui la justifie : la mission (M) ou l'un de ces principes.

- **P1 Coûts.** Réseau SEC plafonné, puis ta lecture (lente, non déterministe, faillible, bornée par ton contexte), puis parse d'arbre, puis scan et hachage : le travail va aux couches rapides quand elles suffisent. Seuls le réseau, par son cache, et ta lecture, par la clé de contenu (§9.6), sont incrémentaux ; le reste se recalcule à chaque exécution.
- **P2 Forme des données.** L'essentiel du signal est dans le XBRL, sans lecture de texte ; ta lecture attribue une contrepartie à un montant et capture ce qui n'existe qu'en texte, sans arithmétique et sans aucun chiffre que le XBRL aurait pu donner.
- **P3 Lots.** Préfère un lot à la lecture document par document quand ce qu'il apporte en masse est ce qu'on cherche : archives `-xbrl.zip` au premier passage, Notes Data Sets pour la découverte et BDC Data Sets pour le côté prêteur (§14).
- **P4 Tables plates.** Huit tables Parquet sous DuckDB ; provenance, preuve, vue et statut sont des colonnes ; une mesure est une requête SQL.
- **P5 Signal d'abord.** Parties liées et Item 404, avec l'Item 9A, l'Item 4 des 10-Q et le bloc de continuité d'exploitation, puis les items 1.01, 1.02, 3.03 et 8.01 des 8-K avec leurs EX-10 et EX-4, sur la fenêtre allongée et les huit trimestres qui la précèdent (§11.1), puis dette, baux et engagements, puis concentration client. Le premier passage s'arrête aux deux premiers ; le reste attend que leur rendement soit mesuré (§11.1, §14), et ce qui n'est pas traité reste visible dans `exclusions`.
- **P6 Mesurer.** La phase 0 mesure volumes et débits, et le premier passage mesure son rendement ; les ordres de grandeur cités sont des hypothèses, et rien ne s'ajoute avant que l'existant ait montré ce qu'il rend.
- **P7 Invariants, pas machinerie.** Une règle reste si elle protège la justesse d'un chiffre et tient dans une colonne ou un contrôle ; ce qui protège le programme contre lui-même est coupé, et l'audit en tient lieu.

**Tu écris du code ; le code lit les documents ; tu ne lis que des agrégats, des extraits ciblés et les blocs que le code te sert, jamais un dépôt entier**, car lire les dépôts un à un sature le contexte et ne laisse aucune donnée structurée à contrôler. Ce que tu extrais d'un bloc ne se rejoue pas sans toi, et c'est assumé : chaque observation porte l'exécution qui l'a produite, et les fichiers d'observations se conservent (§7.4). Des sous-agents peuvent aider ponctuellement, mais rien n'en dépend : paralléliser n'accélère pas le réseau, l'extraction est la tienne, et l'indépendance vient de l'audit.

## 1. Mission [M]

Construis et tiens à jour un modèle comptable vérifiable de la fragilité financière des groupes de `config.yaml` (§10.1), circularité des financements comprise (§3). Le modèle ne prédit rien, ne note rien et ne conclut pas : il mesure, date et publie, et l'utilisateur juge ; « fragilité » nomme ce qui se mesure, jamais un qualificatif donné à un groupe (§4.1). La note de synthèse ouvre sur les événements datés (annexe F), puis sur la fragilité de chaque groupe, la circularité venant ensuite (§12.1).

1. **Quelle est l'exposition de chaque groupe, hors bilan compris ?** En matrice, jamais en total unique (§5.4).
2. **Quelle part du résultat avant impôt tient à des effets de valorisation et d'estimation chiffrés par l'émetteur ?** Gains et pertes, en pont depuis le résultat publié (§6).
3. **Comment ces grandeurs évoluent-elles ?** En séparant ce qui change dans l'entreprise de ce qui change dans son régime de publication (§6.3), son périmètre (§10.2) ou l'étendue du graphe (§3.7).
4. **Quelle part du revenu d'un fournisseur provient de clients qu'il finance ?** Par paire et par fenêtre, avec dénominateur, bornes et part du revenu où la question est posable (§3.6) ; de même pour le client qui finance son fournisseur.

**Les dépôts SEC sont en retard sur les faits**, d'un à trois mois, et les informations annuelles jusqu'à quinze mois : l'outil mesure une fragilité accumulée, jamais une date. C'est pourquoi la vue `as_known` date chaque fait à sa publicité (`knowledge_date`, §7.3).

| Objet | Ce que les seules publications SEC permettent | Limite à rendre visible |
| --- | --- | --- |
| Exposition | une matrice de dettes, sorties contractuelles, plafonds conditionnels et actifs exposés | pas nécessairement de total additif cohérent |
| Choix comptables | un pont entre résultat publié et effets explicitement chiffrés | un résultat « réel » ne s'obtient pas par soustraction |
| Santé financière | des indicateurs tirés des faits balisés | aucun score ; un ratio dont un terme manque n'est pas calculé |
| Événements de fragilité | des observables datés, chacun avec sa pièce (annexe F) | aucun total ni score ; une source non lue n'est pas un trimestre sans événement |
| Évolution | des séries à bases comparables, ruptures identifiées | le périmètre constant peut être impossible |
| Revenu venant de clients financés | montants identifiés ou bornes, par paire et période, souvent sur une fraction du revenu | l'absence d'identification n'est pas un zéro ; l'achat d'un client n'est pas le revenu du fournisseur |

> **Clause de portée.** Le modèle mesure des relations commerciales, des financements et leurs conditions documentées. **Un rapport entre deux montants n'attribue pas causalement un revenu à un financement.** Le modèle ne conclut à une affectation ou à une interdépendance que sur des pièces qui la décrivent ; à défaut, il publie les observations, leurs limites et le statut `causality_not_established`.

Chaque nombre remonte à une accession et à un emplacement ; chaque absence est déclarée ; chaque exclusion porte son motif, car sans registre d'exclusions une omission et un oubli sont indiscernables ; relancée sur le même cache et les mêmes fichiers d'observations, une exécution redonne les mêmes chiffres.


## 2. Admissibilité des preuves [P7]

**Seuls les documents officiels déposés font foi ; les annonces ne sont pas des preuves.**

### 2.1 Filed contre furnished

Un document *filed* engage l'émetteur (Exchange Act, Section 18) et peut être incorporé dans un document d'enregistrement (Securities Act, Section 11) ; un document *furnished* non. Les 8-K items 2.02 et 7.01 et leurs pièces sont furnished (Form 8-K, General Instruction B.2), sauf déclaration expresse, comme les 6-K. Un communiqué annonçant un accord de 100 milliards n'est donc pas une preuve ; l'accord définitif en EX-10 d'un 8-K item 1.01 en est une. Un 6-K incorporé par mention expresse dans un document d'enregistrement devient admissible (`incorporated_by_reference`), puisqu'il est alors exposé à la Section 11. Un DRS est soumis, pas déposé : il n'entre dans aucune mesure (§10.3).

### 2.2 Quatre attributs de preuve, en colonnes

Un contrat prouve ses termes, pas un versement ; des états revus n'ont pas l'assurance d'états audités ; un 6-K peut porter des états audités. Une note unique mélangerait ces dimensions : chaque fait et chaque observation portent donc `filing_status` (`filed`, `furnished`, `submitted_draft`, `correspondence`, `unclassified`) ; `assurance_level`, par extrait et par période, car un S-1 mêle exercices audités et semestre non audité ; `location`, l'emplacement du passage ; `stage`, par montant (`intent_non_binding`, `signed`, `available`, `drawn_or_paid`, `delivered`, `recognized`, `settled`, `terminated`), car « facilité de 20 tirée à 5 » décrit deux montants. Une lettre d'intention non contraignante n'entre dans aucun agrégat, et l'admissibilité se juge par mesure : un contrat non financé compte dans les engagements, pas dans les flux.

Le niveau `tier` se calcule dans cet ordre : un document hors EDGAR (texte de norme, documentation) est de niveau F ; un document non classé, soumis, de correspondance, furnished non incorporé ou de commercialisation (`marketing`) est de niveau E ; des états et notes sont de niveau A s'ils sont audités, B s'ils sont revus, C sinon ; un contrat et ses termes sont de niveau D ; tout autre passage filed (MD&A, risques, Item 404, Form D) est de niveau C. E et F ne servent que de pointeurs. L'ordre n'est pas total, un contrat prouvant mieux un plafond qu'un MD&A et moins bien un versement : tout agrégat publie donc son `evidence_profile`, la part de sa valeur par niveau, car un total attesté à 40 % par le narratif n'est pas le même objet qu'un total tiré des comptes. Un fait de companyfacts prend le niveau de son formulaire (A pour 10-K, 10-KT, 20-F, 40-F ; B pour 10-Q, 10-QT) ; venu d'un autre formulaire, il attend que l'instance de son dépôt le classe.

### 2.3 Le triplet (formulaire, item, pièce)

Ni le formulaire ni le numéro de pièce ne suffisent : l'EX-99.1 d'un 8-K de Microsoft (annexe D) porte des états retraités audités, de niveau A. La précédence est : déclaration expresse du déposant, item, pièce, puis formulaire (principes en annexe A). Le type d'une pièce se lit dans l'en-tête SGML, jamais dans le nom de fichier ni dans `index.json`, où il n'est qu'une icône. Un 8-K à plusieurs items, fréquent (annexe D), se découpe par ses titres « Item x.xx », et une pièce s'y rattache par la mention légale de l'émetteur, puis l'index de l'item 9.01, puis la section qui la cite (cas limites en annexe A). Un triplet requis que l'annexe A ne couvre pas se classe sur le texte réglementaire, noté dans `decisions.md`, ou reste en quarantaine (`unclassified`) : un triplet inconnu n'arrête jamais le pipeline.

### 2.4 La contrepartie nommée

Sans contrepartie identifiée, un montant n'alimente aucune arête de montant. `counterparty_evidence` vaut `named` ; `derivable`, par l'une de ces méthodes seulement : parties d'un contrat annexé, libellé d'un membre de dimension, égalité exacte avec un montant nommé du même dépôt, renvoi explicite d'une pièce à l'autre ; ou `anonymous` (« notre plus gros client »), qui ne devient jamais une arête et va dans la concentration anonyme (§3.6). Un « client A » que chacun croit reconnaître reste anonyme : la rumeur informe le lecteur, pas le modèle.

### 2.5 Quatre pièges

- **Caviardage.** Reg S-K Item 601(b)(10)(iv) permet d'omettre d'un contrat une information non significative que l'émetteur « customarily and actually treats that information as private or confidential ». Un montant caviardé est `redacted`, une donnée manquante déclarée, jamais un zéro ; le caviardage se repère en code, par les crochets et la légende d'omission.
- **Clause absente.** L'Item 601(b)(10)(ii) dispense de dépôt les contrats du cours normal des affaires, sauf exceptions (dépendance substantielle, parties liées, acquisitions importantes, bail significatif) : une conclusion fondée sur l'absence d'une clause publie donc `contract_coverage`, la part des accords connus déposés en entier et non caviardés.
- **Incorporation par référence.** L'Item 13 du 10-K renvoie souvent au DEF 14A, dont l'Item 404(a) exige le nom de la personne liée au-delà de 120 000 $, alors que la note (ASC 850-10-50-3) ne l'exige pas toujours. Non suivi, le renvoi laisse un trou sans signal : le suivre est une obligation.
- **Lettres du personnel de la SEC** (CORRESP, UPLOAD, DRSLTR) : ni filed ni furnished, elles orientent la lecture, jamais la source d'un montant.

### 2.6 Seul EDGAR fait foi

Les niveaux E et F n'entrent jamais dans un calcul. Un montant vu seulement dans un document E, repéré par un scan lexical, sans extraction, va dans `exclusions` (`announcement_only`) et y reste visible, car c'est ce que le lecteur doit pouvoir constater. Le pipeline ne fait **aucune recherche web** : EDGAR suffit pour trouver les dépôts, et la presse n'a ainsi aucune voie d'entrée. **Aucun chiffre de seconde main ni de mémoire**, même comme ordre de grandeur : les sources secondaires présentent des annonces comme contractées, des engagements pluriannuels comme annuels, des plafonds comme tirés. Un nombre introuvable dans un dépôt n'existe pas pour ce modèle.


## 3. Circularité : le graphe et la question 4 [M, P4, P7]

### 3.1 Le graphe

Les nœuds sont des groupes économiques datés (§10.2) ; l'entité juridique reste l'unité de preuve, et le financeur est le groupe à la date de l'événement, fonds de capital-risque consolidés compris, jamais une entité mise en équivalence. Une arête est une ligne de `links`, orientée de la partie qui fournit la ressource (trésorerie, crédit, titres, garantie, avance) vers celle qui la reçoit : sans ce sens unique, un bail de capacité lu à l'envers ferait du néocloud le financeur de son client.

| `family` | Sens | `type` |
| --- | --- | --- |
| `financing` | financeur → financé | `equity_primary`, `convertible_or_safe`, `loan_or_facility`, `vendor_credit`, `noncash_investment`, `lease_financing` |
| `credit_support` | garant → obligé soutenu | `guarantee`, `backstop`, `residual_value_guarantee`, `credit_enhancement` |
| `commercial` | client → fournisseur | `revenue_recognized`, `purchase`, `purchase_commitment`, `capacity_lease`, `prepayment` |
| `customer_consideration` | fournisseur → client | `equity_or_warrants_to_customer`, `credits_to_customer`, `cash_incentive_to_customer` |

Les définitions sont limitatives, sinon tout délai de paiement deviendrait un financement : `vendor_credit` exige une créance de financement sur un client nommé, une composante de financement significative publiée (ASC 606-10-32-15), une location-vente ou un délai publié de plus de 12 mois ; un bail passé avec le fournisseur du service est un `capacity_lease` ; `noncash_investment` est un apport contre des titres (ASC 606-10-32-21). Un acompte à composante de financement publiée donne aussi une arête `financing` (drapeau `advance`), et deux arêtes commerciales opposées posent `reciprocal_purchase`. Affacturage (ASC 860) et programmes de financement de fournisseurs (ASC 405-50) restent hors du graphe, dans le hors bilan.

Seule une arête `amount` (montant admissible, contrepartie nommée ou dérivable, période) entre dans une mesure ; une arête `relation`, pièce de niveau A à D qui nomme les deux parties, rend la paire visible sans remplir la cellule. Une arête commerciale se documente par une pièce A à D : revenu attribué par le fournisseur (concentration nommée, parties liées, Reg S-X 4-08(k)), achats publiés par le client (parties liées, Item 404, ASC 275), EX-10 ou engagement ferme, bail de capacité ; une vente par intégrateur (`sales_channel`) donne une chaîne de relations, pas un revenu attribuable. Un financement ne se documente qu'au niveau A à C et au stade `drawn_or_paid` ou `recognized`, car un contrat prouve un plafond, pas un versement ; un engagement non tiré va dans les engagements, et une garantie ne rend pas « financé ».

### 3.2 Le statut « financé »

F(S, C, t) ∈ {`active`, `lapsed`, `never`, `unknown`} est une fonction pure sur `links`, à chaque fin de trimestre fiscal du fournisseur S. F vaut `active` si (a) une entité consolidée par S détient à t un instrument émis par C, acquis par une opération primaire et attesté au niveau A ou B, sans cession, conversion, remboursement ni radiation publiés depuis ; ou (b) S a versé ou prêté à C en numéraire dans les huit trimestres précédents ; ou (c) S a comptabilisé une contrepartie au client C dans ces huit trimestres. Ensuite `lapsed` ; `never` si rien n'a jamais tenu alors que toutes les pièces qui pourraient l'établir ont été lues ; `unknown` sur un historique tronqué (`history_left_censored`) ou tant que ces pièces restent `not_processed` (§11.1), jamais `never`. En vue `as_known` à la date D, un événement ne compte que s'il était connu à D. Le statut est daté pour qu'un financement ancien ne gonfle pas indéfiniment la dépendance. Seul `companyfacts`, prédécesseurs compris, se tire sans borne de date, puisque cela ne coûte rien (§9.4). Les instances des 10-K et 10-Q, qui ne servent qu'aux dimensions, aux extensions et à `decimals` des périodes analysées, se tirent sur la même période que le texte, la fenêtre allongée de l'annexe E et les huit trimestres qui la précèdent (§11.1) ; le texte ne se lit jamais sans borne : notes de parties liées, Item 404 et sections des items 1.01, 1.02, 3.03 et 8.01 des 8-K, avec les EX-10 et EX-4 annexés, se lisent sur cette période, et une détention ancienne encore en cours, condition (a), s'établit par la note d'investissements courante (bloc `text` de §14), pas par le 8-K de son acquisition. Politique de tête : `exposure_outstanding`, conditions (a) à (c) ; une seule sensibilité, `ever_financed`, où F reste `active` dès qu'une condition a tenu, borne haute jamais en tête.

### 3.3 Les mesures de dépendance

- **`documented_revenue_dependency(S, W)`** = Σ R(S, C, P) ÷ Σ R(S, P) sur une fenêtre W déclarée : un ratio des sommes, jamais une moyenne de ratios. Au numérateur, le revenu reconnu par S et venant de clients nommés ou dérivables, en canal direct, sur les trimestres où F vaut `active` ; ailleurs, `partial`, jamais proratisé. Au dénominateur, `revenue_total` sur le même repère ; si S présente des revenus hors ASC 606, locatifs par exemple, numérateur et dénominateur se prennent sur la même base et l'écart est publié.
- **Sur la même ligne de paire** : `investor_customer_revenue_share`, le miroir (clients qui financent S) ; `noncash_revenue_from_investees`, revenu contre titres reçus de clients (ASC 606-10-32-21) ; `consideration_to_customer`, contrepartie payable au client (ASC 606-10-32-25) ; `documented_backlog_dependency`, part du RPO attribuée à des clients financés, avec sa part au-delà de 12 mois (`term = total`, `beyond_12m`, §6.1).

Aucune de ces mesures ne prouve une circularité : même un cycle dans le graphe ne démontre ni revenu artificiel ni absence de demande finale.

### 3.4 La conclusion par paire

`relationship_conclusion` se dérive de `edge_structure` (`financing_only`, `commercial_only`, `commercial_and_financing`, `reciprocal_commercial`, `none`) et de `linkage_evidence` (`documented_link`, `searched_none_found`, `search_incomplete`). Pièces de lien, limitatives :

| Catégorie | Pièce |
| --- | --- |
| `L1` | clause d'emploi des fonds ou de conditionnalité liant le financement à des achats |
| `L2` | tranches de financement calées sur des livraisons du financeur |
| `L3` | traitement comptable publié qui lie les deux : contrats combinés (ASC 606-10-25-9), contrepartie payable au client (32-25), contrepartie non monétaire (32-21) |
| `L4` | obligation d'achat négociée pour financer les installations du fournisseur (ASC 440-10-50-2) |
| `L5` | déclaration explicite, dans une pièce déposée, liant nommément financement et achats |

Une dépendance commerciale, même nommée dans un facteur de risque, n'est pas une pièce de lien, et une pièce ne compte que si l'extrait cité, retrouvé mot pour mot, nomme les deux parties. `documented_dependency` exige un lien documenté ; sans lien, `commercial_with_financing` ou `reciprocal_commercial_only` décrivent la structure ; tout le reste est `causality_not_established`. `searched_none_found` exige une recherche complète au sens de E.0 ; sinon, c'est `search_incomplete`. **Aucun seuil de ratio ne déclenche seul une conclusion.**

### 3.5 Achats, revenu, absences

L'achat du client n'est pas le revenu du fournisseur : acompte, immobilisation, engagement non exécuté, vente par distributeur, reconnaissance au net ou à une autre date. `amount_nature` les sépare, et leur équivalence exige un rapprochement documenté (lien `same_measure`). Une estimation de la direction (`management_estimate`) s'affiche, jamais au numérateur. **L'absence n'est pas un zéro** : sans attribution admissible, la mesure vaut `not_determinable` avec son `nd_reason`, jamais 0 % ni une estimation, car un zéro fabriqué ferait conclure à l'absence de circularité.

### 3.6 Le résultat vide est pré-engagé

La concentration client est le plus souvent anonyme chez les fournisseurs de puces et de cloud : le numérateur sera souvent vide pour NVIDIA, Oracle ou Microsoft, moins pour un néocloud qui nomme client et investisseur dans sa note de parties liées (CoreWeave, annexe D, à lire en premier). Un fournisseur qui remet à un client des bons de souscription acquis au fil de ses achats (AMD, Marvell, annexe D) nomme ce client et peut rendre la paire financée, une fois la contrepartie comptabilisée (§3.2, condition c), sans donner pour autant le revenu qui en vient. L'arête nommée existe surtout côté client, et elle documente une relation, pas un revenu. Quatre sorties accompagnent donc chaque paire, publiées au même niveau que les mesures :

1. **`named_edge_coverage`** : revenu que S attribue lui-même, au niveau A à C, à des clients nommés ou dérivables, ÷ revenu ; à côté, la part anonyme et le résidu (`term = named`, `anonymous`, `residual`, qui font 100 %), `overlap_possible`, car un client nommé ailleurs peut être l'un des anonymes, et `visible_pairs_count`, les paires vues seulement côté client, jamais converties en revenu.
2. **`documented_pair_coverage`** : pour chaque paire à financement documenté, l'état `complete` (chaque sous-période couverte par des faits admissibles ou un zéro explicite), `partial` ou `absent` du numérateur et du dénominateur, et le compte des neuf combinaisons.
3. **`customer_concentration_anonymous`** : faits `ConcentrationRiskPercentage1` sur `CustomerConcentrationRiskMember`, repère unique, bornes d'arrondi (17,9 % publié veut dire [17,85 % ; 17,95 %[), aucune série par client anonyme sans continuité affirmée par la pièce, car un « client A » d'un exercice n'est pas forcément celui du suivant. Côté client, `supplier_concentration` (ASC 275-10-50-16).
4. **Bornes ASC 280.** Tout client externe d'au moins 10 % du revenu doit être publié, fût-il anonyme, un ensemble sous contrôle commun comptant pour un (ASC 280-10-50-42). Un client direct absent de cette publication auditée pèse donc moins de 10 %, ou est un anonyme : la cellule devient `bounded` (`bound_basis = asc280_major_customer_completeness`, sous l'hypothèse déclarée d'une publication conforme), pour les exercices seulement, puisque seuls les états annuels exigent cette publication. La publication étant déclenchée par la valeur, une série observée seulement quand elle est élevée est biaisée vers le haut : aucune interpolation ni moyenne sur les seules périodes publiées, et une tendance exige des intervalles qui ne se chevauchent pas.

Un numérateur vide est un fait sur le régime de publication, rendu selon E.9 ; il ne justifie jamais de relâcher la contrepartie nommée.

### 3.7 Garde-fous d'inférence

Aucune corrélation n'est publiée, car la demande d'IA fait monter ensemble financements et revenus. Les conclusions portent sur les groupes de `config.yaml` et les contreparties que leurs pièces nomment, jamais sur « le secteur ». Le graphe grandit d'une exécution à l'autre, par les dépôts nouveaux puis, si elle est ouverte, par la découverte (§14) : les séries se recalculent sous le graphe courant, et `delta.md` distingue une arête nouvelle sur une période déjà couverte d'une arête sur une période nouvelle. Beaucoup d'absences sont attendues sous les deux lectures (contrats non déposés, clients sous 10 %, non-déposants) : l'annexe E publie donc `indeterminate` et la non-discrimination comme des résultats.


## 4. Santé financière [M, P2, P4]

La santé financière porte l'essentiel de la fragilité que mesure le modèle (§1), avec l'exposition (§5) et la qualité du résultat (§6) ; la circularité (§3) en est une famille. La note de synthèse lui donne, pour chaque groupe, sa première partie (§12.1).

### 4.1 Règles communes

Les indicateurs se calculent par groupe et par période sur les faits balisés, sans extraction (P2) ; seuls quelques signaux (§4.5) demandent de lire du texte. Une variation se calcule en glissement annuel, contre la même période fiscale de l'exercice précédent, ou sur douze mois glissants, dans une même vue, parce que la saisonnalité et la forte croissance rendent toute autre comparaison trompeuse. Aucune croissance n'est publiée entre deux périodes de longueurs différentes sans le drapeau `unequal_period_length`. Chaque indicateur est une cellule de `measures`, avec son lignage et son statut ; un terme manquant rend un ratio `not_determinable` et une somme `partial`, avec son motif, et n'est jamais estimé. **Aucun score composite ni qualificatif** (« sain », « fragile ») : un score mélange des grandeurs sans commune mesure et cache le terme qui le fait bouger ; le modèle publie les termes, le lecteur juge.

### 4.2 Rentabilité et croissance (ajout v6)

Ces mesures, absentes de la v5, reposent sur des concepts standard `us-gaap` à vérifier en phase 0 (annexe B).

- **`revenue_growth`** : variation de `revenue_total` (`Revenues` ou `RevenueFromContractWithCustomerExcludingAssessedTax`), en glissement annuel (`term = yoy`) et sur douze mois glissants (`term = ttm`). Un changement de politique de reconnaissance ou de périmètre est une rupture (`basis_break`), pas une croissance.
- **`gross_margin`** : marge brute ÷ revenu. La marge brute est `GrossProfit` si le déposant la publie, sinon le revenu moins `CostOfRevenue` ou `CostOfGoodsAndServicesSold` quand il présente cette ligne ; s'il ne présente ni l'une ni l'autre, `not_determinable`, car reconstruire un coût des ventes à partir d'autres lignes serait une estimation.
- **`operating_margin`** : `OperatingIncomeLoss` ÷ revenu.
- **`segment_revenue`, `segment_profit`, `segment_significant_expenses`** : faits dimensionnés sur `StatementBusinessSegmentsAxis` : revenu par secteur, mesure de résultat sectoriel suivie par le principal décideur opérationnel (ASC 280) telle que le déposant la balise, et charges significatives par secteur quand elles sont publiées (ASU 2023-07, §6.3). Ces faits passent par l'instance, jamais par companyfacts, et C11 les rapproche du revenu consolidé. Chaque groupe définit sa mesure de résultat sectoriel : deux résultats sectoriels ne se comparent qu'à libellé égal, et des charges sectorielles ne forment pas un compte de résultat complet de l'activité.
- **`capex_to_revenue`** : `capex_cash` ÷ revenu de la même période ; les additions non monétaires restent à part (§5.5).
- **`working_capital`** : créances clients (`AccountsReceivableNetCurrent`), stocks (`InventoryNet`), dettes fournisseurs (`AccountsPayableCurrent`) et produits constatés d'avance (`ContractWithCustomerLiabilityCurrent`), chacun comme un terme (`receivables`, `inventories`, `payables`, `contract_liabilities`), puis leur solde net et sa variation sur la période (`net`, `change`). Une ligne que le déposant ne présente pas rend le solde `partial`, jamais complété par un zéro. C'est dans le fonds de roulement que se lisent un revenu qui ne s'encaisse pas et un financement par les fournisseurs.

### 4.3 Liquidité, levier et couverture

- **`liq_cash_to_12m_outflows`** : trésorerie et placements courants ÷ sorties contractuelles à 12 mois (principal de dette, paiements locatifs, obligations d'achat), chevauchements résolus (§8.1), sinon `blocked_overlap` ; avec et sans les facilités confirmées non tirées (`term = with`, `without`).
- **`liq_undrawn_committed_facilities`** : ces facilités, en colonne propre.
- **`liq_principal_due_to_cash`** : échéances de principal à 12 et à 24 mois ÷ trésorerie (`term = horizon_12m`, `horizon_24m`).
- **`lev_debt_and_leases_to_operating_income_plus_da`** : dette et passifs locatifs, séparément (`term = debt`, `leases`), ÷ résultat opérationnel augmenté des dotations ; jamais l'« EBITDA » de l'émetteur, dont la définition change d'un groupe à l'autre.
- **`cov_interest_coverage`** : résultat opérationnel ÷ charge d'intérêts, avec et sans réintégration des intérêts capitalisés (`term = with`, `without`), qui réduisent la charge pendant toute la construction.
- **`cov_pik_interest`** : intérêts payés en nature, s'ils sont publiés.

### 4.4 Flux disponibles

`fcf_basic` = CFO − `capex_cash` ; `fcf_after_finance_leases` retire en plus les remboursements de principal des locations-financement ; `fcf_after_counterparty_financing` retire encore les financements en numéraire accordés à des contreparties nommées, remboursements reçus déduits ; `fcf_after_sbc` retire de `fcf_basic` la rémunération en actions, libellée comme telle. `fcf_after_counterparty_financing` est le seul indicateur qui voit, sans hypothèse causale, la trésorerie sortir comme investissement pendant que le revenu entre en exploitation : il fait le pont entre la circularité (§3) et la trésorerie du groupe.

### 4.5 Signaux

Les signaux sont des types distincts, jamais additionnés ni résumés en un score : un doute sur la continuité d'exploitation et un dépôt tardif ne disent pas la même chose. Chacun est un événement daté, avec son dépôt et sa preuve, lu d'abord dans la structure (type de formulaire, items d'un 8-K), puis dans le texte.

- `sig_going_concern` : doute important sur la continuité d'exploitation (ASC 205-40) et paragraphe du rapport d'audit ;
- `sig_material_weakness` : faiblesse significative du contrôle interne ;
- `sig_auditor_change_or_nonreliance` : 8-K items 4.01 et 4.02, correction d'erreur (`dei:DocumentFinStmtErrorCorrectionFlag`) ;
- `sig_late_filing` : NT 10-K, NT 10-Q (Rule 12b-25, annexe D) ;
- `sig_distress_8k_items` : 8-K items 2.04 (obligation accélérée ou augmentée), 2.06 (dépréciation significative), 1.03 (faillite), 3.01 (radiation ou non-respect des règles de cotation) ;
- `sig_covenant_events` : manquements, dérogations et amendements de clauses financières ;
- `sig_pledged_assets` : actifs nantis et trésorerie restreinte au profit de prêteurs.

Ces formulaires et items déclenchent aussi une exécution entre deux publications périodiques (§11.5).

### 4.6 Capitaux propres et exposition par contrepartie

`eq_equity_and_accumulated_deficit` publie les capitaux propres et le déficit cumulé (`term = equity`, `accumulated_deficit`), `eq_diluted_share_count_change` la variation du nombre moyen dilué d'actions. `counterparty_exposure(S, C, t)` publie, une ligne par bloc et par base (§5.4), sans total, la participation, les prêts et créances, les garanties au profit de C, le RPO attribué à C et les engagements nommément rattachés à C. Le drapeau `wrong_way` se lève si S finance C et que C est client de S : c'est le risque « du mauvais côté », que ni la matrice d'exposition ni les mesures de la question 4 ne montrent seules.


## 5. Exposition et hors bilan : la question 1 [M, P2, P7]

C'est là que vit l'essentiel du financement des datacenters, et la partie que les analyses publiques traitent le plus mal : le modèle la couvre systématiquement, pas par anecdote.

### 5.1 Catégories

Le balisage détaillé des notes est obligatoire dès le premier fichier XBRL d'un déposant (Reg S-T Rule 405(d)) : la plupart des montants hors bilan sont des faits balisés, récupérables sans extraction. **L'extraction ne sert presque jamais à trouver le montant ; elle sert à trouver à qui il se rapporte**, car la contrepartie n'est quasiment jamais balisée. Chaque ligne porte `block` et `measurement_basis`, et `category_id` sauf pour un actif exposé hors VIE :

| Bloc | Catégories |
| --- | --- |
| `recognized_liabilities` | `debt`, `lease_liability`, `financing_obligation` (cession-bail non aboutie), `supplier_finance_program`, `earnout`, `derivative_credit_support` |
| `contractual_outflows` | échéancier de la dette, `lease_operating_maturity`, `lease_finance_maturity`, `lease_not_commenced`, `purchase_obligation`, `purchase_obligation_supplier_financing` (ASC 440-10-50-2, retenue seulement si le texte l'affirme), `take_or_pay`, `uncalled_commitment`, `jv_funding_commitment`, `construction_commitment`, `power_purchase_agreement` |
| `contingent_obligations` | `guarantee`, `vie_unconsolidated`, `standby_lc`, `capacity_backstop`, `receivables_transferred` (part avec recours), `indemnification`, `loss_contingency` |
| `exposed_assets` | `vie_unconsolidated` pour l'intérêt détenu ; hors VIE, titres, prêts et créances détenus sur une contrepartie (§4.6) |

Une catégorie à deux blocs produit deux lignes reliées (§8.1) : la dette, stock reconnu et échéancier de service ; l'intérêt dans une VIE, actif exposé à côté de l'exposition maximale ; le contrat d'achat d'électricité, engagement et, s'il est comptabilisé comme dérivé, passif reconnu. Ces montants se trouvent dans les notes de dette, de baux, d'engagements et éventualités, d'investissements, de consolidation, de créances, de regroupements et de dérivés ; take-or-pay et rachats de capacité, souvent seulement dans les notes d'engagements et les EX-10. Énumère les concepts réellement présents au lieu de coder une liste : ils varient d'un déposant à l'autre et dans le temps. Un concept peut couvrir plusieurs catégories : `UnrecordedUnconditionalPurchaseObligation*` « includes, but is not limited to, lease not yet commenced and take-or-pay and throughput contracts », d'où la paire `na06` (§8.2). Et companyfacts n'a ni extensions ni ventilations : la dernière tranche de l'échéancier d'achats de SpaceX est en extension, absente de l'API (annexe D) ; non nulle, elle amputerait le total sans aucun signal. D'où C10, et la lecture de l'instance quand il échoue sur companyfacts.

### 5.2 Ce qui compte vraiment

- **Les baux non commencés** sont probablement le plus gros poste hors bilan des hyperscalers, et le plus invisible : ni droit d'utilisation ni passif, seulement une note (ASC 842-20-50-3(b)), souvent en un total non actualisé et une plage d'années, presque jamais avec une contrepartie. À la date de commencement, le bail devient passif locatif (événement `commencement`, lien `transfers_to`) ; sans cette bascule, la série baisserait à la livraison des datacenters sans aucun désendettement. Un pont par période (`lease_not_commenced_bridge`) publie ouverture + nouveaux baux − baux commencés = clôture (`term = opening`, `additions`, `commenced`, `closing`), `not_determinable` sur les termes non publiés.
- **Les programmes de financement de fournisseurs** ne maintiennent pas mécaniquement de la dette en exploitation : ASU 2022-04 n'a ajouté que des informations à publier. Lis la classification retenue, ne reclasse pas, n'ajoute pas l'encours à une dette qui l'inclut (`na11`). Le tableau de variation est annuel. Absence de programme, non-matérialité et défaut de collecte sont trois états distincts.
- **Les VIE non consolidées**, structure de référence des coentreprises de datacenters : la perte maximale peut inclure des actifs comptabilisés, et ce n'est ni une dette ni une probabilité de perte. Garde séparément l'intérêt détenu, les actifs et passifs reconnus, les soutiens contractuel et non contractuel, le maximum et les montants déclarés non quantifiables.
- **Les créances cédées** (ASC 860-20-50) : collecte le montant décomptabilisé, le prix différé, le recours et l'implication continue ; seule la part avec recours est conditionnelle, et une créance cédée sans recours ne gonfle pas la dette.
- **Un angle mort à déclarer.** Selon une réponse du personnel de la SEC du 29 juillet 2026 (annexe D), les titres des titrisations de datacenters du type décrit dans la demande ne sont pas des « asset-backed securities ». C'est une position du personnel, sans force de loi, mais la direction est claire : ne suppose pas que la couche titrisée sera documentable à la ligne. Elle va dans `exclusions` (`not_public`), et on reconstruit ce qui peut l'être depuis le sponsor, puis, si l'extension est ouverte, depuis le prêteur (§14).

### 5.3 Montages et composantes

Quatre montages ne se classent pas sur leur forme juridique. **Le véhicule avec cession-bail** : consolidation du véhicule, qualification de vente, contrôle de l'actif, options et recours décident du traitement ; une opération qui ne remplit pas les conditions de vente est un financement, une dette juridiquement extérieure peut être garantie, et la dette du véhicule éclaire le projet sans s'ajouter à l'exposition du sponsor (colonne `vehicle_level`). **La garantie de valeur résiduelle** : les paiements probables de certaines garanties du preneur entrent dans les paiements de location (ASC 842), d'autres relèvent des garanties ou des dérivés, et certains soutiens de crédit sont des dérivés à une juste valeur distincte du notionnel ; il faut donc toujours séparer notionnel, montant comptabilisé et perte maximale. **Le rehaussement par un tiers** : le garant n'est pas la contrepartie commerciale et ne joue souvent qu'après achèvement. **Le financement d'équipement par une partie liée.** Le cas réel du corpus est dans le 10-Q de SpaceX (note 17, annexe D) : une cession-bail non aboutie avec Valor Equity Partners (`category_id = financing_obligation`), balisée sous des membres génériques, où seul le texte nomme le prêteur ; les montants se lisent dans les faits balisés, la contrepartie par extraction ciblée du bloc parties liées, avec citation vérifiée. Repère ces montages par le texte (« failed sale-leaseback ») et la note de dette, jamais par un concept d'extension ; au premier passage, seules les notes de parties liées sont lues, et la note de dette attend §14. **Enregistre la conclusion de l'émetteur, ne la refais pas** : traitement retenu avec son extrait, faits qui le fondent, drapeau `judgment_sensitive` quand la classification dépend d'un jugement ; une sensibilité ne se publie que si tous ses termes sont publiés, sous l'étiquette « scénario ».

Un engagement se décompose en composantes (`component_kind` : `principal`, `interest`, `lease_payment`, `purchase`, `minimum_purchase`, `capacity_fee`, `termination_payment`, `guarantee_cap`, `residual_value_guarantee`, `support_commitment_contractual`, `support_noncontractual`, `interest_held`, `other`), chacune avec sa `conditionality` (`firm`, `conditional`, `optional`), car c'est cette structure qui décide de ce qui s'additionne. Les échéances gardent leur libellé d'origine : « reste de l'exercice » n'est pas « année 1 ». Toute composante conditionnelle porte `trigger_description`, `trigger_occurred` (`yes` seulement si un dépôt constate l'événement) et `ultimate_obligor`, car un plafond déclenché et un plafond non déclenché ne s'additionnent pas. Non actualisé et comptabilisé vont toujours ensemble : leur écart est l'effet d'actualisation, pas une exposition supplémentaire. Recours et remboursement attendu ne se compensent que sur une base justifiée. Une garantie non comptabilisée porte son exemption (ASC 460-10-25-1), et son plafond se prend sans déduction des recours (ASC 460-10-50-4).

> **La note de parties liées et l'Item 404 du DEF 14A sont le point d'entrée le plus rentable du corpus** : la concentration client est le plus souvent anonyme, la partie liée ne l'est pas.

### 5.4 Une matrice, pas un total

Principal de dette, passifs actualisés, flux non actualisés, engagements, créances cédées et pertes maximales ne se somment pas, et leurs chevauchements sont systématiques : un crédit-bail est déjà dans la dette, une garantie couvre souvent une dette déjà comptée, l'exposition à une VIE inclut parfois une participation. L'exposition se publie donc par `exposure_matrix`, une cellule par groupe, date, bloc, base et catégorie, **jamais en total unique**. Chaque ligne porte aussi l'entité juridiquement obligée, la contrepartie, le rang (`seniority`), le recours (`recourse`), le cantonnement (`is_ring_fenced`) et `elimination_status`, parce qu'une dette cantonnée sans recours n'expose pas le groupe comme une dette garantie.

| Bloc | Base | Addition autorisée |
| --- | --- | --- |
| `recognized_liabilities` | valeur comptable à une date, principal à part | entre composantes distinctes d'une même base |
| `contractual_outflows` | flux non actualisés par horizon | dans un échéancier homogène, jamais en plus du stock qui représente les mêmes paiements |
| `contingent_obligations` | plafond, déclencheur, échéance, recours | après résolution des plafonds communs et des risques déjà comptés |
| `exposed_assets` | valeur comptable, juste valeur ou maximum | en actifs à risque, jamais assimilés à une dette |

Un sous-total n'existe que si des liens résolus démontrent son additivité (§8.1), et aucun taux de défaut n'est inventé pour obtenir un total. Trois tests : une garantie de 100 sur une dette de 100 ne fait pas 200 ; une créance vendue sans recours ne gonfle pas la dette ; un même bail ne figure pas sous deux bases dans un sous-total.

### 5.5 Deux pièges de collecte

Le tableau des obligations contractuelles a quitté le MD&A (Reg S-K Item 303, Release 33-10890 : en vigueur le 10 février 2021, obligatoire pour les exercices clos à partir du 9 août 2021), mais l'Item 303(b)(1) demande toujours d'analyser les « material cash requirements » issus des obligations connues : l'information est tantôt en tableau, tantôt dans les notes ou en narratif. Constate sa présence dépôt par dépôt (`disclosure_regime`), ne la déduis pas d'une date.

Le capex non monétaire (location-financement, dettes fournisseurs, financement par le vendeur selon ASC 230-10-45-13(c), paiement en titres) échappe au capex décaissé, et le capex impayé, payé la période suivante, y revient alors : « décaissé + impayé » compterait deux fois les mêmes serveurs. Six grandeurs se publient donc séparément, jamais additionnées : `capex_cash`, `capex_accrual` (décaissé + variation de l'impayé), `finance_lease_additions`, `vendor_financed_additions`, `stock_paid_additions` et `operating_lease_rou_additions`, qui n'est pas du capex. Les deux avant-dernières sont souvent en extension ou narratives ; sans concept résolu, elles sont `not_determinable`.


## 6. Qualité du résultat : la question 2 [M, P7]

Il s'agit de séparer ce qui relève de l'exploitation de ce qui relève d'un choix comptable. Ce sont des options normales, publiées, souvent chiffrées par l'émetteur lui-même, rarement additionnées ; elles se prennent **dans les deux sens**, un levier qui a augmenté le résultat une année pouvant le réduire la suivante. Le modèle chiffre des écarts et cite des notes ; il ne qualifie jamais un choix comptable de manipulation, l'interprétation appartient au lecteur.

### 6.1 Onze leviers

1. **Durées d'amortissement des serveurs et des équipements réseau**, le levier le plus puissant du secteur : durée publiée par classe d'actifs (souvent une plage), date et effet chiffré du changement ; comparaison entre groupes limitée aux classes de même libellé, car deux « serveurs » ne désignent pas forcément les mêmes actifs.
2. **Réévaluations de participations non cotées** lors d'un nouveau tour de table (alternative d'évaluation) : un gain sans encaissement, parfois sur les laboratoires que le groupe finance, donc une circularité comptable, distincte de celle de trésorerie. Le prix observable peut être celui que l'investisseur a contribué à fixer : `price_setting_participation` se détermine sur pièces seulement, et le pont publie à part les gains adossés à un tour auquel le groupe a participé.
3. **Gains de dilution** sur les mises en équivalence : comptables, sans encaissement.
4. **Capitalisation** (logiciels, développement, mise en service) : ce qui est capitalisé sort des charges et entre dans le capex.
5. **Capex non monétaire** (§5.5), qui fait paraître l'intensité capitalistique plus faible qu'elle n'est.
6. **Brut contre net**, déterminant dès qu'il y a revente de capacité de calcul : deux acteurs identiques peuvent afficher des revenus dans un rapport de un à dix. Ne compare jamais deux revenus sans avoir vérifié la politique des deux.
7. **Le carnet de commandes.** Le RPO est défini par ASC 606-10-50-13 ; l'hétérogénéité vient des exemptions (50-14(a) pour les contrats d'un an au plus, 50-14A pour la contrepartie variable, 50-14B interdisant d'appliquer 50-14(b) et 50-14A à la contrepartie fixe), de la durée contractuelle retenue et de la confusion avec un « backlog » hors norme, qui ne remplace jamais le RPO. Collecte le RPO avec ses exemptions, le traitement des contrats résiliables et sa part à 12 mois.
8. **Intérêts capitalisés** (ASC 835-20), qui réduisent la charge d'intérêts précisément pendant les programmes de datacenters.
9. **Contrepartie payable au client et revenu contre titres** (ASC 606-10-32-25 et 32-21), les leviers les plus directement liés à la circularité : des titres ou crédits remis au client réduisent le revenu, des titres reçus en paiement le constituent.
10. **Coûts d'obtention de contrats capitalisés** (ASC 340-40).
11. **Effets d'estimation publiés** (stocks, contrepartie variable, provisions sur impôts différés), à la hausse comme à la baisse.

### 6.2 Mesures

- `earnings_bridge_pretax` : le pont entre le résultat avant impôt des activités poursuivies et une liste fermée d'effets publiés, dans les deux sens, chaque effet étant un terme : réévaluations (`investment_gain_loss`), dilution (`dilution_gain`), quote-part des mises en équivalence (`equity_method_income`), dépréciations d'investissements (`investment_impairment`), changements d'estimation (`estimate_change_effect`), intérêts capitalisés (`capitalized_interest`), et le total (`bridge_total`). Un pont après impôt seulement si l'émetteur publie l'effet d'impôt de chaque élément.
- `earnings_bridge_share` : la part de ces effets dans le résultat avant impôt, publiée seulement si celui-ci est positif et dépasse 5 % du revenu, sinon `not_determinable` (`denominator_nonpositive` ou `denominator_below_threshold`), parce qu'une part d'un résultat proche de zéro n'a pas de sens.
- `depreciation_life_published` et `depreciation_life_change_effect` : les durées publiées par classe, et les effets publiés des changements, chacun pour sa période, sans cumul ni extrapolation.
- `implied_useful_life` : immobilisations amortissables brutes moyennes, hors terrains et en-cours, ÷ dotation ; la moyenne demande un exercice antérieur, collecté même hors fenêtre. `cip_share`, en-cours ÷ immobilisations brutes, explique une dotation qui paraît faible pendant une construction.
- `cfo_net_income_gap`, décomposé selon les lignes de rapprochement balisées ; `sbc_to_cfo` ; `receivables_collection_period`, créances et actifs de contrat rapportés au revenu, en tendance ; `customer_advances`, dont seuls les acomptes à composante de financement publiée entrent dans la mesure miroir (§3.3) ; `capitalized_interest` ; `rpo_total` et `rpo_beyond_12m` ; `capex_to_cfo`, avec et sans additions non monétaires (`term = with`, `without`).

Les libellés restent neutres : « délai de recouvrement », pas « revenu financé par le vendeur » ; « durée implicite », pas « retard d'amortissement ». Un rapport stock sur flux baisse mécaniquement en forte croissance : il se publie avec le flux et la croissance de la période.

### 6.3 Le régime de publication est une série temporelle

Ce qui se voit change indépendamment de ce qui se passe : une information qui apparaît en 2025 peut n'être qu'une norme nouvelle.

| Norme | Entrée en vigueur (exercices ouverts après) | Application | Ce qu'elle ouvre |
| --- | --- | --- | --- |
| ASU 2022-04, financement de fournisseurs | 15 décembre 2022, intermédiaires comprises ; tableau de variation : 15 décembre 2023 | rétrospective, sauf le tableau, prospectif | l'encours à chaque période, puis les flux annuels |
| ASU 2023-07, charges par secteur | annuel : 15 décembre 2023 ; intermédiaire : 15 décembre 2024 | rétrospective | les charges significatives fournies au décideur opérationnel |
| ASU 2023-09, impôts | 15 décembre 2024 | prospective, rétrospective permise | réconciliation de taux détaillée, impôts payés par juridiction |
| ASU 2024-03, clarifiée par ASU 2025-01, désagrégation des charges | annuel : 15 décembre 2026 ; intermédiaire : 15 décembre 2027 ; anticipation permise | prospective, rétrospective permise | achats, rémunérations, amortissements dans chaque poste de charges |
| ASU 2025-06, logiciels à usage interne | 15 décembre 2027, intermédiaires comprises | prospective, modifiée ou rétrospective | nouveau seuil de capitalisation (levier 4) |
| ASU 2025-07, titres reçus d'un client | 15 décembre 2026, intermédiaires comprises | voir le texte de l'ASU | ces titres relèvent d'ASC 606 (levier 9) |
| ASU 2020-06, convertibles | 15 décembre 2021, déposants SEC hors petites sociétés | rétrospective complète ou modifiée | fin de certaines séparations ; effet sur la dilution |

La méthode et la date d'adoption effectivement retenues se lisent dans la note de principes comptables (`standard_application`). Une application prospective crée une rupture ; une application rétrospective aussi, puisqu'elle ne retraite que les périodes présentées. Le drapeau `basis_break` marque les deux cas, et les réorganisations de secteurs. `first_published_period` et `first_period_available_at_the_time` distinguent la première période où la donnée existe et la première où elle existait à l'époque : une série qui commence en 2025 se lit comme telle, pas comme un zéro suivi d'un saut. Ce tableau n'est pas exhaustif : lis les notes de principes comptables de chaque groupe. La désagrégation des charges (ASU 2024-03) changera ce qui se voit quand elle entrera en vigueur : ne suppose nulle part qu'un poste de charges est atomique, sans rien construire aujourd'hui pour une norme qui n'est pas encore là.

### 6.4 Restitution

Pour chaque levier, trois cellules : publié, retraité et écart (`term = published`, `restated`, `difference`), jamais le retraité seul. Le retraité égale le publié moins l'effet publié pour la même période ; sans effet publié, il est `not_determinable`. Un effet cumulé n'existe généralement pas : ASC 250-10-50-4 ne demande l'effet d'un changement d'estimation que pour la période du changement, et additionner ou prolonger des effets serait une estimation.


## 7. Données : huit tables plates [P4, P1]

Huit tables, construites dans DuckDB en process puis exportées en Parquet : ni serveur ni migration, puisque tout se reconstruit depuis le cache et tes fichiers d'observations à chaque exécution (§9.6). Accords, instruments, événements et obligations sont des lignes ou des colonnes, pas des objets à part. Le schéma (`schema.sql`) déclare pour chaque table sa clé primaire et ses énumérations, et DuckDB les fait respecter : une contrainte vaut mieux qu'une règle qu'il faut relire. Dans une clé primaire, une composante sans objet prend la valeur `none`, une clé n'admettant pas de nul.

### 7.1 Les tables

`documents` (une ligne par ressource lue), `facts` (par nombre tiré de la structure), `observations` (par ligne validée de tes fichiers d'observations, passe la plus récente, §7.4), `entities` (par personne morale, avec appartenances et alias datés, §10.2), `links` (par arête du graphe, §3.1, ou relation entre deux montants, §8.1, avec sa clé d'instrument, `instrument_key`), `measures` (par valeur publiée ou attendue, §7.5), `controls` (par contrôle, groupe, période, vue et, s'il y a lieu, ventilation et correspondance, §8.3 ; à part, car un statut de contrôle n'est pas un statut de mesure) et `exclusions` (par élément écarté ou non traité, avec son motif). Huit tables suffisent : toute mesure est une jointure suivie d'une agrégation, et un auditeur lit une table en une requête.

Les colonnes qui portent une règle sont nommées là où la règle est écrite. Trois valent partout. **L'emplacement de chaque nombre** est une colonne, `locator` : l'`id` du fait dans l'instance, ou, pour un texte, la plage d'octets du fichier brut en cache et la citation ; compté en octets bruts, il ne bouge pas quand une bibliothèque change. Un nombre lu par un parseur HTML porte `is_tagged = false`. Un drapeau vaut vrai ou faux quand sa règle a pu s'appliquer, sinon il reste nul avec sa raison, pour que « faux » et « inconnu » ne se confondent pas.

### 7.2 Identité d'un fait et période

**Les dimensions font partie de l'identité d'un fait.** Dans le 10-Q de SpaceX, le revenu du premier semestre 2026 apparaît en 18 faits pour 16 jeux de dimensions (annexe D) : une clé (concept, dates, unité, entité) les fusionnerait, et « le plus récent gagne » ne départagerait rien, tous venant du même dépôt. L'identité sémantique est : concept sans version, entité, `period_start`, `period_end`, unité, dimensions canoniques, cadre comptable, périmètre de présentation. **La version de taxonomie est un attribut, pas une identité** : sinon un revenu et son comparatif de l'année suivante seraient deux faits, et la détection des retraitements (C4) serait aveugle là où ils se produisent. Un concept déprécié se rattache à son remplaçant par la table de dépréciation de chaque millésime. Toutes les occurrences sont gardées et se sélectionnent par vue ; la clé primaire de `facts` est l'occurrence, stable d'une exécution à l'autre : fichier du dépôt et rang du fait pour une instance ; accession (`accn`), concept, unité et période pour un fait de companyfacts, qui n'a pas de rang stable d'un tirage à l'autre.

**Jamais `fy` ni `fp` comme clé de période** : ils décrivent le dépôt contenant, sont nuls pour un 8-K, et l'actif de SpaceX au 31 décembre 2025 porte `fy = 2026`, `fp = Q2` (annexe D). La période se lit sur `period_start` et `period_end`.

### 7.3 Deux vues et normalisation

`as_known` répond à « que savait-on à la date D ? » (`knowledge_date` ≤ D, date de publicité, distincte de l'acceptation pour un DRS), `revised` à « quelle est la présentation révisée de la période ? » : se servir d'un dépôt de 2026 pour dire ce qu'on savait fin 2025 serait un biais rétrospectif, disqualifiant pour suivre une évolution. « Dernière » suit l'ordre total (`acceptance_datetime`, accession, rang du document, rang de l'occurrence), qui départage les dépôts du même jour. Les contrôles se calculent en `as_known` à `as_of` ; les séries se publient en `revised`, `as_known` à côté. Chaque révision porte `recast_cause` (`error_correction_restatement`, `error_correction_revision`, `accounting_change`, `common_control_combination`, `discontinued_operations`, `segment_change`, `presentation_reclassification`, sinon `unknown`), lue dans les axes de retraitement balisés, `dei:DocumentFinStmtErrorCorrectionFlag`, un 8-K item 4.02 ou la note ASC 250, pour que la question 3 sépare l'entreprise de sa présentation. Un trimestre obtenu par différence de cumuls, ou une somme sur douze mois glissants, est une valeur calculée qui garde les clés de ses termes ; des termes de vues ou de révisions différentes la rendent `not_determinable` (`recast_boundary`), sinon tout un retraitement tomberait sur un seul trimestre.

**Normalisation.** Une instance extraite est déjà à l'échelle : ne réapplique pas `scale` ; `decimals` est une précision, pas un multiplicateur. `nil`, zéro explicite et absence sont trois états : un tiret balisé `ixt:fixed-zero` est un zéro, un tiret nu non. Deux faits incohérents sont `conflicting`, comme un saut d'un facteur 100 d'une période à l'autre tant que `num` des Notes Data Sets ne l'a pas confirmé (§14 ; d'ici là, le fait reste hors des sommes), car une erreur d'échelle sur un poste isolé ne se voit dans aucun total. **Change** : aucune somme de devises mélangées, aucune conversion.

### 7.4 Ce que tu extrais du texte

Deux missions, pas davantage : attribuer une contrepartie nommée aux montants que donnent les faits balisés, et capturer ce qui n'existe qu'en texte. Tu fais cette extraction toi-même, et jamais sur un dépôt entier : c'est ce qui protège ton contexte. Le code sert les blocs, tu les lis dans l'ordre d'une file, le code valide ce que tu écris.

**L'unité de travail est le bloc naturel** : un bloc de texte de note (`textBlockItemType`, §9.2) et ses tableaux linéarisés, une section délimitée par son titre (Item 404, Item 9A d'un 10-K, Item 4 de la partie I d'un 10-Q, items 1.01, 1.02, 3.03 et 8.01 d'un 8-K), une pièce EX-10 ou EX-4 annexée à ces 8-K, servie d'abord par sa première page (périodes et règle de lecture en §11.1). Le code le sert avec les faits candidats qu'il contient et leurs valeurs, sous un en-tête de métadonnées (accession, déposant, formulaire, item ou pièce, note, période, emplacement, clé de contenu) ; jamais du HTML ou du XBRL brut, des états primaires ou du boilerplate, parce que c'est dans ces blocs qu'un nom se trouve à côté d'un montant. Un lot n'est qu'une file : les blocs sans fichier d'observations, dans l'ordre du signal (§11.1), jusqu'au plafond de ce que tu lis d'un coup (`max_read_chars`, §9.1). Un bloc plus long que ce plafond t'est servi en morceaux, coupés aux frontières naturelles du texte avec recouvrement, pour ne pas séparer un montant de sa contrepartie ; ces morceaux n'existent qu'au moment de la lecture et n'ont ni identité ni fichier.

Tu écris au fil de ta lecture, bloc par bloc, et non à la fin du lot : tu rends les lignes d'un bloc d'un coup, une fois le bloc lu, au moins une par bloc, observation ou abstention. Le code te renvoie aussitôt les erreurs du schéma, et tu reprends une fois les lignes refusées ; puis il écrit le fichier du bloc (§9.6) avec les lignes qui passent, même s'il n'y en a aucune, pour qu'un bloc que tu ne parviens pas à décrire dans le schéma ne revienne pas sans fin. Un bloc est déjà lu quand son fichier existe ; un bloc pour lequel tu n'as rien rendu reste dans la file. Tout l'état est sur disque : une compaction de ton contexte ou une interruption ne fait perdre qu'un bloc.

Une observation porte sa citation et son `locator`, la contrepartie et sa preuve (§2.4), payeur et receveur, montant, unité, devise et nature (§3.5), période, stade, type d'événement (`event_type` : `commitment`, `signing`, `availability`, `drawdown`, `funding`, `secondary_purchase`, `delivery`, `recognition`, `repayment`, `conversion`, `amendment`, `expiry`, `guarantee_call`, `payment`, `purchase`, `commencement`, `impairment`, `observable_price_adjustment`, `measurement_change`, `disposal`, `termination`, `default`, `acceleration`, `noncash_contribution`, `warrant_vesting`), `instrument_key`, les champs de §5.3, et l'exécution qui l'a produite (son `as_of`).

- `amount_origin = tagged_reference` exige un fait candidat de même valeur ; `narrative_only` ne vaut que pour un texte non balisé. **Aucune arithmétique en lisant, aucun chiffre que le XBRL aurait pu donner** : toute arithmétique se fait en code.
- `amount_qualifier` (`exact`, `approximately`, `at_least`, `more_than`, `up_to`, `at_most`, `range`) : « jusqu'à » ne s'additionne qu'à des plafonds, « au moins » n'est qu'une borne basse, « environ » porte sa précision.
- Période, payeur et receveur sont obligatoires s'ils sont déterminables, sinon l'orientation d'une arête se devinerait.
- **Le code valide avant de charger dans `observations`** : le schéma, puis la sémantique (citation retrouvée mot pour mot à son emplacement, contrepartie présente dans le bloc, montant, unité et devise cohérents, montant égal à celui d'un fait candidat du bloc quand l'origine est `tagged_reference`), car un JSON conforme peut être faux. Une ligne rejetée, au schéma après ta seconde tentative ou au contrôle sémantique, devient une exclusion `validation_failed`, avec la ligne brute et la clé du bloc, jamais une retouche silencieuse ; un rejet au schéma, qui n'entre pas dans le fichier du bloc, se garde à côté de lui (§9.6), pour que l'exclusion se reconstruise à chaque exécution. Aucun champ de confiance : un score non calibré n'est pas une probabilité.
- **L'abstention est un résultat**, avec son motif, et n'entre dans aucun agrégat.
- **Une observation n'est pas rejouable sans toi.** Elle porte l'exécution qui l'a produite, et les fichiers d'observations sont versionnés, puisque rien ne les reproduit (§12.1). Une nouvelle passe, pour reprendre une ligne rejetée ou parce qu'une observation doit porter un champ nouveau, relit le bloc entier et constitue un nouveau résultat : elle ajoute ses lignes au fichier du bloc sous un nouvel `as_of`, et seule la plus récente se charge, rejets compris, pourvu que la clé du bloc existe encore dans l'exécution courante ; `delta.md` signale la passe et ses écarts.

### 7.5 Mesures et couverture

**La clé primaire de `measures` réunit tout ce qui distingue deux valeurs qui ne se confondent pas** : mesure, groupe ou entité, contrepartie, période, vue, date de connaissance (`as_of`), terme (`term`), ventilation (`breakdown_key`), politique de financement (`financing_policy`), périmètre (`constant_perimeter`) et variante de décision ou de correspondance (`variant`). Deux termes, deux ventilations ou deux variantes font donc deux lignes, jamais deux valeurs d'une ligne. Les termes d'une mesure sont ceux que sa définition nomme, et le schéma les contraint mesure par mesure, car un terme n'a pas de sens hors de sa mesure. La ventilation est celle que publie la pièce (bloc, catégorie et base de la matrice, membre de dimension, énoncé de l'annexe E). `as_of` est la date de l'exécution (§7.7) ou, pour l'annexe E, la date limite de dépôt du rapport annuel évalué (E.0).

Une cellule porte sa valeur, ses bornes (`value_lower`, `value_upper`) et leur base (`bound_basis`), numérateur et dénominateur, `status`, `nd_reason`, `coverage_state`, `evidence_profile` et son lignage, les clés des faits, observations et liens qu'elle utilise. `status` vaut `computed`, `bounded`, `partial`, `not_determinable` (toujours avec `nd_reason`), `not_applicable` ou `blocked_overlap`. Les seules bornes publiées sont celles de l'arrondi et celles d'une règle de publication : aucun « intervalle d'incertitude » sans construction de ses bornes.

**L'univers attendu s'engendre par règle, sans regarder les données**, depuis les obligations de publication (ASC 842, 280, 460, 810, 405-50 et 606 pour les exercices ; Reg S-X article 10 et ASC 270 pour les périodes intermédiaires). Chaque cellule attendue a sa ligne et son `coverage_state` (`observed`, `explicit_zero`, `not_disclosed`, `not_applicable`, `redacted`, `not_collected`, `not_processed`, `parse_failed`, `conflicting`, `policy_excluded` ou `unknown`), et `not_applicable` exige une pièce : sinon un concept jamais découvert ne laisse aucune trace, et un univers tiré des données serait couvert à 100 % par construction. Collecte, extraction et mesure se lisent séparément. Aucune valeur absente ne devient zéro dans une somme : la somme est `partial`, et son statut le dit. Un échec technique, un conflit ou un triplet non classé est un état de couverture ou une quarantaine, jamais `out_of_scope` : ranger les échecs parmi les choix les ferait disparaître.

### 7.6 Invariants d'agrégat

Tout agrégat est vérifié avant publication : (a) aucun élément de niveau E ou F ; (b) aucune devise mélangée ; (c) des clés uniques, que le schéma impose ; (d) aucune somme à travers un chevauchement non résolu ; (e) pour un même nœud, aucune combinaison des perspectives `reporting_entity` et `counterparty` (§10.4) sans leur ventilation ; (f) aucune somme entre cadres comptables ; (g) aucune entité `pending` ni observation abstenue. Un agrégat qui en viole un va dans `exclusions` (`invalid_aggregate`, avec l'invariant) et l'exécution continue, le reste des chiffres n'en étant pas moins juste ; nombreuses, ces exclusions signalent un code faux, et elles ouvrent `delta.md`.

### 7.7 Mêmes chiffres

Relancée sur le même cache, avec les mêmes fichiers d'observations et le même `as_of`, une exécution redonne les mêmes chiffres ; ta lecture, elle, ne se rejoue pas (§7.4). Il suffit d'une arithmétique décimale exacte (`DECIMAL(38,6)` ou unités mineures, ratios arrondis par une règle déclarée), de tables exportées triées par leur clé primaire, et d'un `as_of` en paramètre (date UTC du début de l'exécution) qui remplace l'horloge dans tout calcul « à aujourd'hui ». L'identité octet pour octet des fichiers n'est pas un objectif.


## 8. Non-additivité et contrôles [P4, P7]

### 8.1 Relier, pas dédoublonner

Cinq sources de double comptage, par fréquence : **bilatéral** (engagement d'achat chez le client, carnet chez le fournisseur) ; **intragroupe**, aigu avec SpaceX, xAI et X ; **cycle de vie** (une facilité de 20 tirée à 5 donne un plafond de 20 et un flux de 5, jamais 25, et un garant ne produit aucun flux avant l'appel) ; **assiette** (montant initial et solde) ; **représentation** (engagement d'achat et bail, garantie et dette garantie).

Dédoublonner après coup ne marche pas, et l'unicité d'un identifiant ne prouve rien : un financement et sa garantie ont deux identifiants valides et le même principal, alors que les achats de janvier et de février d'un même contrat se somment légitimement. Le mécanisme est une relation explicite entre deux montants, une ligne de `links` avec `relation_type` (`same_measure`, `component_of`, `covers`, `overlaps`, `replaces`, `eliminated_with`, `transfers_to`) et, si elle est partielle, son allocation. Toute somme déclare sa base homogène et porte sur des faits et des arêtes, jamais sur des lignes d'`observations`, dont plusieurs peuvent décrire le même montant ; un chevauchement non résolu bloque la seule somme concernée (`blocked_overlap`), et les lignes restent consultables. **N'agrège jamais deux entités d'un même groupe sans avoir vérifié ce qui est éliminé en consolidation** (`elimination_status`, calculé depuis les appartenances datées, §10.2).

### 8.2 Paires non additives

Chaque paire du registre (dans `config.yaml`) engendre une relation `overlaps` candidate entre toutes les lignes qui s'apparient (même groupe, date ou instrument). Seule une relation résolue autorise la somme : par la règle indiquée quand sa condition se vérifie sur les colonnes et les linkbases, sinon par une pièce, sinon par toi, avec une ligne dans `decisions.md`. `delta.md` compte les candidates de chaque paire, car un registre muet laisserait passer l'invariant (d) à vide.

| Paire | Ligne a / ligne b | Résolution par défaut |
| --- | --- | --- |
| `na01` | obligation d'achat du client / RPO du fournisseur | même contrat, deux perspectives : pas de somme |
| `na02` | principal / valeur comptable de la même dette | `component_of`, le reste étant décote et frais (ASC 835-30-45-1A) |
| `na03` | engagement / tirage du même instrument | `component_of`, le reste étant le non-tiré (Reg S-X 5-02.19(b), 5-02.22(b)) |
| `na04` | plafond de garantie / dette garantie | `covers`, à hauteur du plus petit (ASC 460-10-50-4) |
| `na05` | échéancier non actualisé / passif locatif | `same_measure` si les intérêts implicites sont publiés (ASC 842-20-50-6) |
| `na06` | bail non commencé / obligation d'achat | `overlaps` tant qu'une pièce ne les dit pas disjoints |
| `na07` | même titre au coût et à la juste valeur | deux bases, jamais sommées |
| `na08` | dette intragroupe éliminée / dette consolidée | `eliminated_with` (ASC 810-10-45-1) |
| `na09` | RPO / passifs de contrat | `overlaps` : le RPO peut les inclure (ASC 606-10-50-13) |
| `na10`, `na15` | exposition à une VIE / participation, ou garantie donnée pour elle | `overlaps` : l'exposition peut les inclure |
| `na11`, `na12` | financement de fournisseurs, ou capex impayé / dettes fournisseurs | `overlaps` : ils peuvent y être logés |
| `na13` | obligation de financement / dette | `component_of` si la linkbase de présentation la place sous la dette (ASC 842-40-25-4) |
| `na14` | plafond initial / solde du même accord | `overlaps` : deux assiettes |

Le code engendre aussi deux relations hors registre : un bail non commencé `transfers_to` le passif qu'il devient (ASC 842-20-25-1), et si l'extension est ouverte, chaque dépôt d'une offre de Form D `replaces` le précédent (§14).

### 8.3 Contrôles C1 à C16

Les contrôles comptables sont les vrais tests des états financiers. Chacun est une requête SQL qui écrit une ligne de `controls` par groupe, période et vue, et, s'il y a lieu, par ventilation (accord, type de bail, échéancier) et par correspondance (§7.1).

| Contrôle | Égalité ou règle |
| --- | --- |
| C1 `c1_balance_components` | composantes = sous-totaux publiés du bilan (actif courant, actif, passif courant, passif s'il est publié, capitaux propres temporaires, capitaux propres y compris minoritaires) ; composantes = enfants du sous-total dans la linkbase de présentation |
| C2 `c2_cash_flow_components` | même principe pour les trois sections du tableau de flux, effet de change compris |
| C3 `c3_cash_reconciliation` | clôture du tableau de flux = trésorerie + trésorerie restreinte courante et non courante (ASC 230-10-50-8) |
| C4 `c4_restatement_detection` | même identité, valeurs différentes selon le dépôt : publié avec `recast_cause`, jamais écrasé |
| C5 `c5_bilateral` | écart entre les deux déclarations d'un même accord (ci-dessous) |
| C6 `c6_income_articulation` | résultat y compris minoritaires, ou part du groupe si le tableau part de celle-ci, = première ligne du tableau de flux ; résultat net = variation des résultats non distribués + dividendes déclarés + autres mouvements publiés |
| C7 `c7_cash_continuity` | trésorerie d'ouverture de P = clôture de P−1 lue dans le dépôt de P−1 |
| C8 `c8_debt_rollforward` | variation du principal de dette − (émissions − remboursements) = résidu, publié avec les éléments non monétaires |
| C9 `c9_lease_liability` | paiements non actualisés − intérêts implicites = passif locatif, par type de bail |
| C10 `c10_maturity_sums` | somme des tranches = total publié (dette, obligations d'achat, baux) |
| C11 `c11_segments` | revenus sectoriels + rapprochement = revenu consolidé |
| C12 `c12_revenue_disaggregation` | ventilation du revenu = revenu total (ASC 606-10-50-5) |
| C13 `c13_rpo` | tranches = RPO total ; parts ≤ 100 % |
| C14 `c14_eps_scale` | résultat dilué aux ordinaires ≈ BPA dilué × actions diluées ; sans numérateur publié, écart relatif sous 10 % ; `not_testable` si plusieurs catégories d'actions ont des BPA différents |
| C15 `c15_tax_rate` | taux effectif publié ≈ impôt ÷ résultat avant impôt, à la demi-unité du taux publié |
| C16 `c16_concentration` | parts ∈ [0 ; 1], somme par repère ≤ 1, montant d'un client majeur ≈ part × revenu |

Une erreur uniforme, un facteur 1 000 sur tous les postes, conserve les égalités d'identité : C14 à C16 la voient parce qu'ils mêlent des grandeurs d'échelles différentes, et C9, C10 et C13 donnent au hors bilan ses propres équations. Un mauvais concept de dette passe l'égalité actif = passif + capitaux propres : C1 et C2 portent donc sur les composantes sélectionnées, pour tester la correspondance de concepts plutôt que l'arithmétique de l'émetteur, et un contrôle sur les seuls totaux déposés est `tautological`, jamais compté comme réussi. La trésorerie du bilan exclut en général la trésorerie restreinte, et un bilan peut porter des capitaux propres temporaires (SpaceX, annexe D) : nomme les concepts et ne somme jamais un concept agrégé avec ses composantes.

**C5.** Un écart entre ce que le client dit devoir et ce que le fournisseur dit attendre est une information de premier ordre, pas une erreur à lisser : les deux montants se publient, avec bases, dates et périmètres. L'écart ne se calcule qu'à 45 jours près et sur quatre paires de bases comparables : engagement publié par le client / RPO attribué par le fournisseur au même accord ; achats du client / revenu reconnu par le fournisseur, même base brute ou nette ; acompte payé / encaissement déclaré ; financement reçu / financement accordé, même instrument. Sinon C5 est `not_testable`.

**Tolérance d'arrondi, et elle seule.** Pour Σaᵢ = b, la tolérance vaut Σ ½·10^(−decimalsᵢ) + ½·10^(−decimals_b) ; `INF` compte pour zéro, et des précisions différentes sont légitimes. `decimals` se lit dans l'instance ou dans `num.dcml` des Notes Data Sets (32767 code `INF`), jamais dans companyfacts, qui ne le fournit pas : un contrôle sur companyfacts seul est provisoire (`tolerance_basis = inferred`). Chaque contrôle renvoie `ok`, `mismatch` avec un `explanation_code` et ses preuves, `not_testable` avec son motif, ou `tautological`. Un écart de définition n'est pas un écart d'arrondi, et un contrôle ne passe jamais `ok` par une variable d'ajustement : un résidu nommé vaut mieux qu'un équilibrage silencieux. Le compte des statuts figure en tête de la note. Un `mismatch` isolé est un résultat publié ; des contrôles en échec de façon générale arrêtent l'exécution (§11.4).

**Un contrôle n'est pas une cible.** Qui choisit un concept voit aussitôt si le contrôle passe, et retenir celui qui le fait passer déplacerait la variable d'ajustement dans la correspondance. Celle-ci se fixe donc par règle, avant les contrôles : un concept n'est retenu pour une grandeur (annexe B) que s'il figure dans la linkbase de présentation du déposant pour l'état concerné, ou dans `pre` des Notes Data Sets, et si sa définition (`MetaLinks.json`, `tag.doc`) correspond ; une extension, que si elle est l'enfant d'un concept déjà rattaché et cite le même paragraphe ASC. Après un `mismatch`, la correspondance ne change que sur une pièce nouvelle (linkbase d'un dépôt postérieur, 10-K/A, lettre CORRESP), notée dans `decisions.md`, et le contrôle se publie sous les deux correspondances, l'originale en tête. Personne ne relit tes choix en cours de route : cette règle et l'audit sont les seules protections contre ce biais, et c'est pourquoi `concepts.csv` va à l'auditeur, qui commence par là (§12.2, annexe C).

Ces contrôles ne voient ni un périmètre faux mais cohérent, ni une contrepartie mal attribuée : les règles de §10.2 et la validation de §7.4 s'en chargent, et l'audit les attaque.

### 8.4 Tests unitaires

Des tests unitaires, seulement sur le code qu'aucun contrôle comptable n'atteint : `scale` (négatifs compris), `sign`, `decimals`, `ixt:fixed-zero` ; le normaliseur de texte (entités HTML, espace insécable, nom coupé par une balise, constructions iXBRL) ; unités et devises ; identité sans version et sélection de période sans `fy` ni `fp` ; blocage d'une somme par un chevauchement ; déterminisme des identifiants ; `tier` ; vérification des citations. Quelques cas suffisent, et un test ne se corrige que s'il est lui-même faux, jamais pour faire passer le code.


## 9. Réseau, entonnoir, cache : la colonne vertébrale [P1, P3, P6]

### 9.1 Coûts et volumes

| Étage | Débit effectif ou limite |
| --- | --- |
| Réseau SEC | 10 requêtes par seconde au plus, par utilisateur ; croisière du pipeline : 5 |
| Ta lecture | bornée par ton contexte, pas par un débit : au plus 80 000 caractères d'un coup, faits candidats et en-têtes compris (`max_read_chars`, environ 20 000 jetons) |
| Parse d'arbre (`lxml`, `selectolax`) | 30 à 80 Mo/s ; `BeautifulSoup`, 0,5 à 3 Mo/s, est proscrit |
| Décompression, scan multi-motifs, hachage | 0,3 à 5 Go/s |

Ta lecture ne se mesure pas en débit mais en contexte : un seul plafond borne ce que tu lis d'un coup, compté en caractères, que le code mesure sans tokeniseur ; et comme tu écris bloc par bloc, une interruption ne fait perdre qu'un bloc. Débits et volumes sont des hypothèses, les volumes étant ceux des huit groupes d'origine, extrapolés au prorata aux groupes de `config.yaml` : 1 100 à 1 650 10-K, 10-Q et 8-K sur la fenêtre du premier passage ; environ 1,4 × 10⁴ dépôts tous formulaires confondus, surtout des Form 4 et 144 ; 2 à 2,75 Go de HTML brut pour 550 Mo de texte utile. La phase 0 les remplace par des mesures en disant sur quelle base elle compte, car la somme des `size` des `submissions` mesure la soumission complète, pas le document principal (annexe D). Le plafond de lecture est lui aussi une hypothèse, modifiable à tout moment : il ne règle que ce que le code te sert d'un coup et n'entre dans aucune clé, si bien que le changer ne fait rien relire. Le corpus du premier passage tient en mémoire : aucune volumétrie ne justifie serveur, orchestrateur ou file de messages.

### 9.2 L'entonnoir

```
Premier passage (§11.1)
  XBRL des groupes de config.yaml : companyfacts sans borne,
  instances (fenetre allongee + 8 trim.)                     -> facts   sans extraction
  Parties liees, Item 404, 8-K 1.01, 1.02, 3.03 et 8.01 avec EX-10 et EX-4
  (fenetre allongee + 8 trim.),
  Item 9A, Item 4 des 10-Q, continuite d'exploitation (fenetre)
    -> parse d'arbre, normalisation versionnee
    -> blocs naturels ; ceux qui ont deja un fichier d'observations sont ecartes
    -> file dans l'ordre du signal, lue par toi, bloc par bloc :
       contrepartie des montants connus, texte seul
    -> validation par le code                                -> observations
  Liens, mesures, controles en SQL                           <- l'analyse ne lit que ca
Phase ulterieure (§14) : Notes Data Sets, Form D, recherche plein texte -> candidats
```

- **Un parseur d'arbre, pas une machine à états** : linéariser un tableau exige sa structure (`colspan`, `rowspan`, en-têtes multiples), et à 30 Mo/s les 2,75 Go de HTML des groupes de `config.yaml` passent en moins de 100 secondes.
- **Les notes se délimitent par leurs blocs de texte balisés** (type `textBlockItemType`, rattaché à un rôle de note dans `FilingSummary.xml` ou `MetaLinks.json`), jamais par le seul nom du concept : dans le 10-Q de SpaceX, 20 notes font 49 blocs, et la note 1 est balisée sans suffixe `TextBlock` (annexe D). Les Items 1A, 7, 7A, 8, 9A et 13 d'un 10-K, l'Item 4 de la partie I d'un 10-Q et la section de l'Item 404 d'un DEF 14A se délimitent par leurs titres.
- **Les pièces de la tranche se lisent en entier**, sans filtre lexical, en morceaux au-delà du plafond de lecture : elles sont peu nombreuses, et un filtre sur les noms connus manquerait les contreparties dont le nom reste à découvrir. Seule exception : le corps d'un EX-10 dont les parties autres que le déposant et son groupe sont toutes des établissements financiers, ou d'un EX-4 dont le porteur en est un (§11.1). Un amendement autonome se lit pourtant en entier, quelles que soient ses parties, car c'est l'événement F4 lui-même (annexe F) : un EX-10 dont le titre contient « Amendment », « Waiver » ou « Consent » en mot entier, sauf si, un ordinal mis à part, il commence par « Amended and Restated », ou un EX-4 « Supplemental Indenture », précédé ou non d'un ordinal, dont le 8-K porte l'item 3.03 (§11.1). Un « Amended and Restated » est un contrat d'origine : comme les autres contrats d'origine entre établissements financiers, il reste alors à l'en-tête, son événement F4 se lisant dans la section 1.01, et leurs clauses attendent le bloc `text` de §14.
- **Normalise avant de lire**, car une citation ne se retrouve pas mot pour mot, ni un paragraphe repris ne se reconnaît, quand un nom est coupé par une balise ou écrit en entités HTML : décodage (EDGAR mêle ASCII, Latin-1 et UTF-8), entités, forme Unicode, constructions iXBRL (`ix:header`, `ix:exclude` et `ix:hidden` exclus, `ix:continuation` rattaché). La version du normaliseur entre dans les clés de cache.
- **Dédupliquer le travail, pas la provenance** : un bloc repris à l'identique n'est pas relu, mais toutes ses occurrences restent listées, car deux émetteurs qui décrivent un accord dans les mêmes termes, c'est une information. Les quasi-doublons se repèrent par empreintes lexicales, pas par embeddings, puisqu'on cherche des noms et des montants.

### 9.3 Sources

**companyfacts** ne contient que les taxonomies non personnalisées, pour l'entité entière, et chaque fait n'y porte que `start`, `end`, `val`, `accn`, `fy`, `fp`, `form` et `filed` : ni `decimals`, ni dimensions, ni extensions. Les ventilations par contrepartie ou par client y manquent, mais un total ne peut pas s'y mêler à ses membres : c'est une ossature sûre et incomplète, à vérifier sur un concept ventilé avant de construire.

**L'instance du dépôt.** L'archive `{accession}-xbrl.zip` ramène en une requête le document iXBRL, le schéma, les linkbases et souvent les pièces ; l'instance extraite `*_htm.xml` (contextes, dimensions, un `id` par fait), `FilingSummary.xml`, les fichiers `R*.htm` et `MetaLinks.json` (définitions, présentation, références jusqu'au paragraphe ASC) sont générés par la SEC dans le même répertoire. **Découvre les ressources d'un dépôt, ne les suppose pas** : `index.json` pour l'inventaire, l'en-tête SGML pour les types. Un S-1/A balisé pour ses seuls droits de dépôt produit lui aussi une archive, de 3 437 octets pour SpaceX (annexe D), sans aucun état financier.

**Partage** : companyfacts pour l'ossature et les séries longues, l'instance pour les ventilations, la précision et l'ancrage d'un chiffre. **Pas de Notes Data Sets au premier passage** : leurs archives couvrent tous les déposants, et pour les quelques groupes de `config.yaml`, les instances apportent la même chose pour une fraction des octets ; un lot ne vaut que s'il donne en masse ce qu'on cherche. Notes Data Sets, recherche plein texte et BDC Data Sets servent à la phase ultérieure (§14).

### 9.4 Endpoints et pièges d'API

Vérifie chaque endpoint contre la documentation officielle avant de coder : `company_tickers.json` et `cik-lookup-data.txt`, `submissions`, `companyfacts` et `companyconcept` ; dans le répertoire d'un dépôt, `index.json`, `{accession}-index-headers.html`, `{accession}-xbrl.zip`, l'instance et ses métadonnées ; ceux des jeux de données et de la recherche plein texte ne servent qu'en §14.

- **Pagination** : `filings.recent` ne porte qu'au moins un an ou 1 000 dépôts, le plus grand des deux. Lis toutes les pages de `filings.files` **sans filtre de date**, filtre ensuite, et vérifie par CIK que toutes ont été lues, sinon des dépôts disparaissent sans signal : les 8-K et les rapports périodiques dont se lisent le texte et les instances, sur la fenêtre allongée et les huit trimestres qui la précèdent (§3.2, §11.1). Un CIK incomplet porte `history_left_censored`.
- **L'API `frames` n'est pas utilisée** : elle remappe les clôtures non calendaires et retient le dernier fait déposé, souvent un comparatif postérieur (annexe D).
- **Pas d'archives nocturnes `companyfacts.zip` ni `submissions.zip`**, plusieurs gigaoctets pour les quelques sociétés de `config.yaml` : un lot ne vaut que s'il donne en masse ce qu'on cherche.
- **Pas de scraping des pages de navigation EDGAR**, puisque les endpoints JSON existent et sont stables ; l'en-tête SGML, fichier du dépôt, n'en est pas une.
- **Les bibliothèques EDGAR servent à naviguer, jamais pour les chiffres** : leur normalisation des états applique des règles que tu n'as pas écrites et qui changent avec les versions.

### 9.5 Accès à la SEC

- **Un seul User-Agent**, fourni par l'utilisateur dans `config.yaml` au format demandé par la SEC : nom réel de l'organisation ou du projet et adresse de contact réelle et surveillée, jamais jetable (annexe D). Tu ne l'inventes pas et n'en changes pas ; il n'est envoyé qu'aux hôtes de la SEC.
- **5 requêtes par seconde**, pour un plafond SEC de 10 par utilisateur, quel que soit le nombre de machines. Un limiteur de débit dans le client HTTP suffit, à condition que toute requête vers `[www.sec.gov](https://www.sec.gov)`, `data.sec.gov`, `efts.sec.gov` ou `xbrl.sec.gov`, bibliothèques comprises, passe par ce client et qu'une seule session tourne à la fois (§11.5) : sinon un second débit ou un second User-Agent s'ajouteraient au premier.
- **Après un 403, une pause d'au moins 10 minutes, puis reprise** : la SEC limite l'adresse IP pour une courte période et ne la libère qu'après 10 minutes sous le seuil, et toute requête pendant ce délai la prolonge. Si l'accès reste refusé malgré les pauses, par exemple sur la page « Your Request Originates from an Undeclared Automated Tool », l'exécution s'arrête (§11.4), car seul l'utilisateur peut corriger le User-Agent.
- 429, 5xx et délais dépassés : quelques nouvelles tentatives espacées, puis `not_collected` pour cette exécution ; 404 et 410 : `not_collected` d'emblée.
- **Aucun changement d'identité** (User-Agent, adresse IP, mandataire) pour dépasser une limitation : ce serait contourner un plafond qui vaut par utilisateur, et une limitation de l'adresse IP ne se lèverait pas pour autant.
- **Seul le débit compte** : aucun plafond de requêtes ni d'octets par exécution. Chaque requête va au journal (`journal.jsonl` : horodatage, URL, statut, octets), preuve du respect de la politique ; l'adresse de contact est masquée dans toute copie partagée.

### 9.6 Cache et idempotence

```
cache/archives/{cik}/{accession}/{document}.zst   immuable
cache/api/{cik}/{ressource}/{date}.json.zst       horodate
cache/datasets/{nom}/{millesime}/...              millesime conserve
cache/search/{sha256_requete}/{date}.json.zst
work/observations/{content_key}.jsonl             un fichier par bloc, ecrit par toi, versionne
work/observations/{content_key}.rejected.jsonl    ses rejets au schema (§7.4), versionne
work/session.lock                                 verrou de la session en cours (§11.5)
```

Un fichier d'observations ne s'écrase jamais : une nouvelle passe y ajoute ses lignes sous un nouvel `as_of`, qui ordonne les passes (§7.4).

Un numéro d'accession est immuable : sous `/Archives/`, rien ne s'invalide et le répertoire tient lieu d'index. Les API et les jeux de données sont au contraire des agrégats vivants, corrigés après coup : chaque tirage est horodaté, une récupération nouvelle crée une version sans écraser l'ancienne, et une exécution ne tire une ressource horodatée qu'une fois.

| Étape | Clé | Invalidée par |
| --- | --- | --- |
| téléchargement | accession + document | rien |
| parse et normalisation | sha256 du document + version du normaliseur | un nouveau normaliseur |
| découpe en blocs | clé de contenu | un nouveau normaliseur ou une nouvelle délimitation |
| filtre lexical (§14) | clé de contenu + version du lexique | un lexique enrichi |
| lecture (§7.4) | clé de contenu | rien : toute clé nouvelle (normaliseur, texte du bloc, faits candidats) est un bloc à lire, et relire est une nouvelle passe |
| mesures et contrôles | aucune | recalcul intégral à chaque exécution |

La **clé de contenu** est le sha256 de la version du normaliseur, du texte normalisé du bloc et des faits candidats pris par leurs valeurs, sans identifiant d'occurrence : un bloc repris mot pour mot l'année suivante garde sa clé et n'est pas relu. Le plafond de lecture n'y entre pas. C'est le seul mécanisme d'incrémentalité côté texte : un bloc dont le fichier d'observations existe, même vide (§7.4), ne revient plus dans la file, sauf nouvelle passe.

> **Le réseau est incrémental. Le calcul est intégral.**

Il n'y a donc jamais de migration : ajouter une colonne calculée ou corriger une formule, c'est recalculer à l'exécution suivante, et les retraitements se propagent seuls. Ajouter une contrepartie, un prêteur, un alias ou un groupe est une donnée, pas du code, et le pipeline rattrape tout l'historique de la nouvelle entité, pas seulement son dernier trimestre. Tout agrégat entre groupes énonce sa composition et la date d'entrée de chaque membre, sans quoi l'ajout d'un groupe ressemblerait à une explosion de l'exposition.


## 10. Périmètre, entités, SpaceX [M, P7]

### 10.1 Les groupes de `config.yaml`

Aujourd'hui NVDA, GOOGL, AMZN, META, MSFT, ORCL, CRWV, SPCX, AMD, AVGO et MRVL (annexe B). **Aucun CIK n'est codé en dur** : `company_tickers.json` résout chaque ticker et prime sur le CIK indicatif de `config.yaml` (annexe B), et `submissions` donne clôture, SIC, État et catégorie de déposant ; un ticker non résolu écarte le groupe avec son motif. À confirmer : NVIDIA clôture fin janvier, Microsoft le 30 juin, Oracle le 31 mai, SpaceX (CIK 1181412, Nasdaq, SIC 7370, Texas, « Non-accelerated filer ») le 31 décembre, d'où un premier 10-K attendu au plus tard fin mars 2027 ; AMD le dernier samedi de décembre, Broadcom le dimanche le plus proche du 31 octobre, Marvell le samedi le plus proche du 31 janvier, en exercices de 52 ou 53 semaines dont la clôture change d'une année à l'autre : elle se lit sur `period_end` (§7.2), jamais sur le `fiscalYearEnd` de `submissions`, qui ne donne que celle de l'exercice en cours (§13, annexe D).

**Un émetteur successeur garde l'historique de son prédécesseur.** Quand une nouvelle société de tête succède à l'ancienne (changement de domicile, réorganisation), le ticker ne résout que le CIK du successeur, et les dépôts antérieurs restent sous celui du prédécesseur : sans lui, l'historique du groupe serait tronqué sans signal. Le prédécesseur entre donc dans le groupe, `parent` jusqu'à la succession que date sa pièce (8-K12B, annexe D), et ses `submissions`, son `companyfacts` et ses dépôts se traitent comme ceux du successeur. Pour l'identité d'un fait (§7.2), les deux forment une seule entité déclarante, leurs états consolidés se continuant : sinon le comparatif publié par le successeur et le chiffre publié par le prédécesseur seraient deux faits, et un retraitement entre eux échapperait à C4. Un CIK dont les dépôts commencent après le début de la fenêtre allongée et des huit trimestres qui la précèdent fait chercher un prédécesseur ; à défaut, ce CIK porte `history_left_censored` (§9.4). Marvell et Broadcom sont dans ce cas (annexe D) : le dernier 10-K de Marvell Technology Group Ltd., pour l'exercice clos le 30 janvier 2021, porte le premier exercice de la fenêtre, et la succession de Broadcom, en avril 2018, tombe dans les huit trimestres qui précèdent la fenêtre allongée, sa période de lecture commençant avec son exercice clos en 2018.

### 10.2 Entités et groupes économiques

**Une entité par personne morale**, reliée à ses groupes par des appartenances datées, qui portent `consolidation_treatment` (`parent`, `consolidated_subsidiary`, `vie_consolidated`, `vie_unconsolidated`, `equity_method`, `investment_only`, ou `undetermined`, qui la garde hors de tout agrégat) et, s'il y a eu regroupement, `combination_method`. Deux personnes morales d'un même groupe restent deux entités : c'est ce qui permet de calculer les éliminations à une date et d'évaluer `issuer_is_subject` contre tous les CIK d'un nœud et de ses filiales consolidées. Le traitement de l'entité et la base d'évaluation d'un instrument détenu sont deux attributs, car une participation change de base (à l'introduction en bourse de l'entité détenue, par exemple) sans que l'entité change de traitement. Une entité mise en équivalence est partie liée du groupe, pas le groupe : collecte sa quote-part, les pertes non reconnues (ASC 323-10-35-19 à 35-22), les profits intra-entité différés et les soutiens, car une participation ramenée à zéro n'est pas une exposition nulle.

**Résolution.** Deux mentions désignent la même entité, ou une entité appartient à un groupe à une date, par l'une de ces règles : même CIK ; inscription à l'EX-21 d'une tête de groupe (Reg S-K Item 601(b)(21)) ; même dénomination normalisée et même juridiction dans deux pièces indépendantes ; « X, anciennement Y » dans une pièce, ou `formerNames` ; présentation comme consolidée dans les notes (ASC 810-10-50). La normalisation retire casse, ponctuation, espaces multiples et « The » initial, et ramène les suffixes à `inc`, `corp`, `llc`, `lp`, `ltd`, `plc` ou `pbc`, sans troncature ni distance d'édition. Une dénomination qui en contient une autre (« X.AI Corp AGC II », véhicules nommés « … Anthropic PBC … ») ne désigne jamais la même entité sans CIK commun ou pièce qui l'affirme. Hors de ces règles, tu peux confirmer une entité sur un extrait qui établit son identité, avec une ligne dans `decisions.md` ; sinon elle reste `pending`, visible dans les tables, absente des agrégats. **On ne fusionne que sur CIK ou identité affirmée par une pièce**, jamais sur une ressemblance de nom.

**Groupes économiques.** Chaque contrepartie reçoit un groupe économique daté, fondé sur un contrôle affirmé par une pièce, sinon le sien : ASC 280-10-50-42 compte comme un seul client un ensemble sous contrôle commun, et un laboratoire opère par plusieurs entités juridiques. Une coentreprise à plusieurs sponsors forme son propre groupe. Les entités de l'EX-21 et les véhicules consolidés, fonds de capital-risque compris, sont membres de leur groupe ; un fonds géré mais non consolidé ne donne qu'une arête `relation`. Les alias et leurs dates viennent de `formerNames` ou d'une pièce, jamais d'une date arbitraire (CoreWeave s'appelait « Atlantic Crypto Corp » jusqu'au 3 octobre 2019).

> **Tout changement de périmètre fabrique une rupture de série qui ressemble à un fait économique.** Regroupement, acquisition, consolidation nouvelle, changement de segmentation, ajout d'un déposant au modèle : même mécanisme, même remède. Présentation rétrospective publiée si elle existe ; sinon, pour une acquisition ordinaire, pro forma de revenu et de résultat (ASC 805-10-50-2(h), `reporting_scope = pro_forma`) ; sinon `not_determinable` et pont partiel.

### 10.3 SpaceX

SpaceX n'est pas un déposant comme les autres, et un pipeline qui le traiterait uniformément produirait des séries fausses sans rien signaler. Les faits datés sont en annexe D ; la phase 0 les re-vérifie.

- **Pas de 10-K ni de XBRL annuel.** Les états annuels audités ne sont que dans le S-1 et le 424B4, non balisés ; le balisage commence au premier rapport périodique, le 10-Q au 30 juin 2026, qui donne des flux trimestriels et semestriels et un bilan comparatif au 31 décembre 2025. C'est le comportement normal d'une introduction en bourse.
- **Le SIC 7370 est un fait de dépôt** : la part de l'IA dans l'activité se lit dans la segmentation publiée (ASC 280), pas dans un code administratif ni dans la presse.
- **Un DRS est soumis, pas déposé** (`submitted_draft`) : EDGAR le date à sa soumission, non à sa publication, et il n'entre dans aucune mesure ; le 424B4 porte la version définitive.

**Décision D1, la série annuelle.** Lis les états annuels du 424B4 avec un parseur HTML ; chaque ligne reçoit la `model_quantity` du concept du 10-Q dont le libellé (`MetaLinks.json`) correspond, la valeur servant seulement à vérifier, jamais à apparier, sinon l'appariement confirmerait ce qu'il doit tester. **Chaque chiffre porte `is_tagged = false` jusque dans les rendus**, parce qu'un nombre lu dans du HTML n'a pas le statut d'un fait balisé et que le lecteur doit le voir. Vérifie les équations internes (C1, C2, C6) et recoupe avec le bilan comparatif du 10-Q au 31 décembre 2025, à la tolérance d'arrondi. Un écart inexpliqué écarte la série annuelle avec son motif : SpaceX n'entre alors qu'avec les périodes balisées du 10-Q, et les comparaisons pluriannuelles l'excluent explicitement. **Dès que le premier 10-K de SpaceX est déposé, ses états balisés remplacent les chiffres du 424B4.**

**Décision D2, le périmètre SpaceX, xAI, X.** Selon le 424B4, les états ont été « retrospectively recast for all periods presented » pour inclure X.AI Holdings Corp. et X Holdings Corp. « because these transactions were between entities under common control », aux valeurs comptables historiques, sans survaleur nouvelle, transactions entre entités éliminées. La série `as_if_combined` est donc la série retraitée publiée par l'émetteur (vue `revised`) ; `legacy_only`, SpaceX sans xAI ni X, n'existe qu'au niveau sectoriel, le secteur « AI » regroupant notamment xAI et X, et vaut `not_determinable` ailleurs ; en vue `as_known`, rien n'était public avant le dépôt public du S-1, le 20 mai 2026. Les deux séries se publient côte à côte.

**Entités.** X.AI Holdings Corp., X.AI Corp. (CIK 0002002695), X Holdings Corp., X Corp., X.AI LLC et CTC Property, LLC sont six entités, chacune avec ses appartenances datées. Ne fusionne pas les opérations : l'une peut relever du contrôle commun et l'autre d'une acquisition, et la conversion juridique des titres privilégiés garde sa date. **Deux dates par combinaison sous contrôle commun** : l'appartenance court depuis `common_control_start` pour toute valeur tirée d'un dépôt postérieur à la combinaison (vue `revised`), et depuis `legal_date` sinon (vue `as_known`) ; une date unique donnerait une série `revised` d'où xAI serait éliminé à tort, ou une série `as_known` qui l'inclurait rétroactivement.

### 10.4 Les non-déposants

OpenAI et Anthropic ne se voient qu'à travers leurs contreparties. `source_perspective` vaut `reporting_entity` si un CIK déposant du document appartient à la partie décrite ou à ses filiales consolidées, `counterparty` sinon, et un nœud reconstruit ne se compare jamais à un nœud déclaré sans le dire (invariant e). Une donnée manquante sur un laboratoire bloque la seule mesure qui l'exige, pas les comptes du groupe. Des règles de publication montrent les non-déposants : Reg S-X 3-09 (états séparés d'une mise en équivalence significative, en EX-99 d'un 10-K ou 10-K/A), 4-08(g) (informations résumées), 4-08(k) (parties liées au recto) et ASC 850 ; ce qu'elles donnent va sur le nœud du non-déposant, en perspective `counterparty`.


## 11. Déroulé d'une exécution [P5, P6]

### 11.1 Le premier passage

**Une page ou une livraison intermédiaire, c'est un fichier écrit et un commit, pas une fin de tour.** Le tour ne se termine que dans trois cas : la file de lecture de la phase 2 est vide et la phase 3 a livré ; un arrêt de §11.4 s'impose ; une limite dure de l'environnement est atteinte. La seule question posée à l'utilisateur, celle de l'extension (§11.3), se pose après la phase 3, jamais au milieu de la file. La tâche planifiée de §11.5 reprend une exécution interrompue par une limite, pas un tour rendu de plein gré. Sans cette règle, une page se lit comme une invitation à rendre la main, et l'exécution s'arrête après quelques blocs en attendant qu'on la relance à la main.

Le premier passage se limite à ce qui rend le plus : les faits balisés des groupes de `config.yaml`, puis leurs notes de parties liées, leur Item 404, trois blocs courts (l'Item 9A, l'Item 4 des 10-Q et la continuité d'exploitation) et les items 1.01, 1.02, 3.03 et 8.01 de leurs 8-K avec les EX-10 et EX-4 annexés, sans aucune découverte. §3.6 prévoit un numérateur souvent vide : payer la découverte avant d'avoir mesuré ce que rend la tranche la plus dense serait l'inverse de P6.

**Phase 0, mesurer**, sans extraction. **Commence par commiter `config.yaml`, critères des annexes E et F et seuils compris, et envoie aussitôt son empreinte à l'utilisateur, avant toute requête** : un critère fixé après avoir vu la couverture qu'il doit juger ne protège plus contre le biais de confirmation, et seule une empreinte reçue hors du dépôt date ce commit. Résous les CIK, prédécesseurs compris (§10.1), tire les `submissions`, toutes pages comprises, et fixe la fenêtre : du premier exercice fiscal clos en `window.start_fiscal_year` (2021, annexe B) jusqu'à `as_of`, périodes intermédiaires en cours et leurs comparatifs compris. Son début fixe garde dans la fenêtre, à mesure qu'elle s'allonge, deux exercices de référence antérieurs au boom, nécessaires pour lire une fragilité qui s'accumule ; une année de plus par an ne coûte rien après le premier passage. Inventorie les dépôts par société, formulaire et item, mesure tailles, débit et latence, lis les pièces de SpaceX (D1, D2, dates des appartenances). Écris `plan.md` (quoi, dans quel ordre, combien de requêtes, de blocs à lire et d'heures, écarts avec §9.1), engendre l'univers attendu des mesures de rang 1 (§7.5) et envoie la première page (§11.3).

**Phase 1, l'ossature**, sans extraction. Tire les `companyfacts` des groupes de `config.yaml`, prédécesseurs compris, sans borne de date (§3.2) ; lis par leur archive `-xbrl.zip` les 10-K, les 10-Q et leurs amendements de la fenêtre allongée et des huit trimestres qui la précèdent, l'instance de tout autre dépôt source d'un fait de companyfacts de ces périodes (8-K, S-1, S-4) pour le classer, et les EX-99 qui portent des états 3-09 : ces instances ne servent qu'aux dimensions, aux extensions et à `decimals` des périodes analysées. Construis la correspondance de concepts, les deux vues, les faits de parties liées, de concentration et de secteurs, les catégories hors bilan balisées, `disclosure_regime` et l'adoption des normes ; calcule les contrôles et les mesures de rang 1 qui ne demandent aucun texte. **L'essentiel de la valeur du modèle est ici, pour presque rien** : ne saute pas cette phase pour aller au texte.

**Phase 2, la tranche à fort signal**, que tu lis bloc par bloc (§7.4), pour les groupes de `config.yaml` seulement, du plus récent au plus ancien, pour que ce qui reste `not_processed` à l'arrêt soit le plus ancien : (1) les notes de parties liées (blocs de texte des instances de leurs rapports périodiques et, pour une introduction récente comme SpaceX, états annuels du 424B4) et l'Item 404, là où il se trouve (DEF 14A, partie III d'un 10-K/A, ou 424B4 faute de DEF 14A), sur la fenêtre allongée de l'annexe E et les huit trimestres qui la précèdent, pour la condition (b) du statut « financé » (§3.2), et trois blocs courts sur la fenêtre, pour que F5 et F10 (annexe F) soient calculables dès le premier passage : l'Item 9A des 10-K et 10-K/A et l'Item 4 de la partie I des 10-Q, délimités par leur titre, et le bloc balisé de doute sur la continuité d'exploitation des 10-K et 10-Q (`SubstantialDoubtAboutGoingConcernTextBlock` de `us-gaap`, à vérifier en phase 0 ; à défaut, le passage correspondant de la note 1) ; (2) les sections des items 1.01, 1.02, 3.03 et 8.01 de leurs 8-K, avec les EX-10 et EX-4 annexés, sur la fenêtre allongée et les huit trimestres qui la précèdent, comme les notes de parties liées : un fournisseur déclare aussi sous l'item 8.01 ses accords avec des clients et les bons de souscription qu'il leur remet (Broadcom, Marvell, annexe D), et on y cherche la contrepartie au client de la condition (c) de §3.2, pas des détentions anciennes ; l'item 1.02 dit la fin d'un contrat, dont celle d'un contrat de capacité, événement de l'annexe F ; l'item 3.03 annonce une modification des droits des porteurs, souvent un événement F4, et un 8-K qui ne porte que les items 3.03 et 9.01 ne doit pas échapper à la tranche. **Aucune lecture de texte n'est sans borne de date** : une détention ancienne encore en cours (condition (a) de §3.2) s'établit par la note d'investissements courante (bloc `text` de §14), pas par le 8-K de son acquisition, et seul `companyfacts` remonte sans borne (phase 1). **Pour un EX-10 ou un EX-4, l'en-tête avant le corps** : lis d'abord la section de l'item sous lequel la pièce est déposée (1.01, 1.02, 3.03 ou 8.01) et sa première page, où figurent les parties ou le porteur, puis le reste de la pièce seulement si l'une de ses parties, hormis le déposant et son groupe, n'est pas un établissement financier, ou, pour un EX-4, si son porteur n'en est pas un. Ce n'est pas un filtre lexical mais un ordre de lecture : un contrat de crédit syndiqué n'apporte rien à la question 4, alors que les conditions d'acquisition d'un bon remis à un client sont une pièce de lien (L1 ou L2, §3.4) et que §5.3 veut son déclencheur (`trigger_description`), cité mot pour mot (§7.4). Le corps se lit aussi, quelles que soient les parties, pour un amendement autonome, parce que c'est l'événement F4 lui-même (annexe F) : un EX-10 dont le titre contient « Amendment », « Waiver » ou « Consent » en mot entier, sauf si, un ordinal mis à part, il commence par « Amended and Restated », si bien que « Limited Waiver », « Omnibus Amendment » et « Amendment No. 3 to Amended and Restated Credit Agreement » se lisent ; un EX-4 « Supplemental Indenture », précédé ou non d'un ordinal, seulement si le 8-K qui l'annexe porte l'item 3.03, marque d'une modification des droits des porteurs (sans cet item, c'est une émission nouvelle, item 2.03, et la pièce reste à l'en-tête). Un « Amended and Restated » est un contrat d'origine : comme les autres contrats d'origine entre établissements financiers, il reste alors à l'en-tête, son événement F4 se lisant dans la section 1.01, et leurs clauses attendent le bloc `text` de §14. Une pièce arrêtée à son en-tête reçoit une abstention motivée, et son corps va dans `exclusions` (`financial_parties_only`), pour que ce choix reste visible, à l'audit compris. Les contreparties que nomment ces pièces sont confirmées par les règles de §10.2 ou restent `pending`, et aucune n'ouvre de lecture de ses propres dépôts. Si une interruption, arrêt de §11.4 ou limite dure de l'environnement, coupe l'exécution avant la fin de la file, le reste est exclu (`not_processed`) et ouvre l'exécution suivante.

**Phase 3, assembler, mesurer, livrer** : en SQL, entités, arêtes, relations entre montants, éliminations, statut « financé », C5, mesures de rang 1, contrôles, invariants, couverture, confrontation à l'annexe E et événements de l'annexe F ; puis rendus, livrable d'audit et commit (§12), et seconde page (§11.3).

**Ce que le premier passage ne lit pas reste `not_processed`, jamais absent**, hormis le corps des EX-10 et EX-4 arrêtés à leur en-tête, exclu avec son motif. L'Item 9A, l'Item 4 des 10-Q et le bloc de continuité d'exploitation, eux, sont lus dès le premier passage (phase 2, classe (1)), si bien que F5 et F10 (annexe F) y sont calculables, F5 à chaque trimestre. Le texte hors de la tranche (notes d'investissements, de dette, de baux et d'engagements, texte autour des faits de concentration) peut seul établir certaines arêtes : une participation qui n'est pas une partie liée, par exemple, n'apparaît pas dans la note de parties liées. Ce qui en dépend se publie `partial` sur la part lue, ou `not_determinable` s'il n'y a rien de lu, toujours avec le motif `not_processed` ; F reste `unknown` tant qu'une pièce lue ne l'établit pas (§3.2) ; la recherche n'est jamais complète au sens de E.0, si bien que `searched_none_found` et l'issue `not_supported` de E.1 n'y sont pas possibles ; et la cellule de E.6 est `not_determinable`, motif `not_processed`, jamais présentée comme un décompte nul, tant que les chemins de §14 ne sont pas calculés.

**Mesures de rang 1**, codées et regardées d'abord, parce qu'elles portent la fragilité (§1). Chacune se publie en série par trimestre, par exercice pour ce qui ne se publie qu'annuellement (§7.5), avec sa variation (§4.1) et ses ruptures de base (`basis_break`, §6.3) :

| Famille | Rang 1 |
| --- | --- |
| Investissement et flux (§4.4, §6.2) | `capex_to_cfo`, avec et sans additions non monétaires (`term = with`, `without`) ; `fcf_after_counterparty_financing` |
| Engagements (§5.1, §5.2) | `lease_not_commenced_bridge` ; l'échéancier des obligations d'achat de `exposure_matrix` (`contractual_outflows`, `purchase_obligation`) |
| Contreparties (§4.6) | `counterparty_exposure`, avec `wrong_way` |
| Revenu et résultat (§4.2, §6.1, §6.2) | `receivables_collection_period` ; `rpo_total`, publié en regard de `revenue_growth` ; `depreciation_life_published` ; `investment_gain_loss`, avec `price_setting_participation` |
| Liquidité et levier (§4.3, §4.5) | `liq_principal_due_to_cash`, `lev_debt_and_leases_to_operating_income_plus_da`, `sig_covenant_events` |
| Circularité, question 4 (§3) | `documented_revenue_dependency`, `investor_customer_revenue_share`, `named_edge_coverage`, `documented_pair_coverage`, `customer_concentration_anonymous` |

S'y ajoutent les trois signaux que donne la structure (`sig_late_filing`, `sig_distress_8k_items`, `sig_auditor_change_or_nonreliance`, §4.5), les événements de l'annexe F et les quatre mesures qu'exige l'annexe E (`documented_backlog_dependency`, `consideration_to_customer`, `noncash_revenue_from_investees`, `contract_coverage`). Les mesures de la question 4 et les sorties de couverture restent en rang 1 mais ne mènent plus la note (§12.1). Une mesure de rang 1 emporte les mesures dont elle se calcule (`fcf_basic` pour `fcf_after_counterparty_financing`, `investment_impairment` pour l'événement F6, par exemple). Les autres mesures sont de rang 2 : elles affinent, décomposent ou demandent du texte. Celles qui ne demandent que des données en cache et des observations déjà écrites se codent une fois les résultats de rang 1 relus par toi et présentés dans la seconde page, leur univers attendu engendré d'abord ; les autres attendent la décision d'étendre.

**Mesurer le rendement, puis décider.** Le passage se termine par la mesure de ce qu'il a rendu, en tête de `delta.md` : cellules de rang 1 et de l'annexe F par statut et par motif, paires à financement documenté, arêtes de montant, `named_edge_coverage` par fournisseur, cellules de la question 4 par statut et par motif, requêtes, octets, blocs lus, par item pour les 8-K (1.01, 1.02, 3.03, 8.01), EX-10 et EX-4 arrêtés à leur en-tête, lignes rejetées par la validation, durée. La ventilation des motifs d'indétermination (E.7) dit ce qu'une extension peut changer : rien là où le motif est `non_filer` ou `redacted`, car l'information n'est pas publique ; quelque chose là où il est `not_processed` ou `search_incomplete` ; et `anonymous` n'est définitif qu'une fois lu le texte qui entoure les faits de concentration. **L'extension (§14) ne s'ouvre que sur décision explicite de l'utilisateur.** Tu inscris sa réponse dans `config.yaml` (`scope` : `first_pass`, ou la liste des blocs de §14 ouverts), avec sa date et le rendement qui lui a été présenté, et tu commites ; sans décision, le pipeline s'en tient au premier passage et le tient à jour.

### 11.2 Décisions

Tu tranches seul les questions techniques (classer un triplet, établir une entité, choisir un concept, résoudre une relation entre montants, dire si un déclencheur est survenu, classer une pièce de lien, dater l'adoption d'une norme, qualifier une révision), en cherchant dans les pièces : le dépôt lui-même (instance, linkbases, `MetaLinks.json`), les autres dépôts de l'émetteur, ses lettres CORRESP comme pointeurs, les instructions des formulaires, Reg S-K, S-X et S-T, les textes des ASU. **Chaque décision non triviale va dans `decisions.md`**, en une ou deux phrases, avec sa source et un identifiant. **Si c'est vraiment ambigu**, si les pièces soutiennent deux lectures qui changent un chiffre publié, publie les deux variantes côte à côte, la plus prudente en tête : l'écart est un résultat. Ne choisis jamais une lecture d'après son effet sur une mesure. Sans règle ni pièce, prends l'option prudente : exclure plutôt qu'admettre, `not_determinable` plutôt qu'estimer.

### 11.3 Points de contrôle pour l'utilisateur

Deux pages en français simple, sans identifiant ni jargon : `user_brief_1.md` après la phase 0, `user_brief_2.md` après le premier passage. Chacune dit ce qui a été décidé, ce qui reste incertain et ce qui a été exclu, et pourquoi. La première donne aussi la durée et le volume prévus, où vivent le dépôt et le cache, et rappelle l'empreinte du commit des critères des annexes E et F, envoyée avant la première requête parce qu'un historique git peut être réécrit (§11.1). La seconde donne le rendement et dit ce qu'une extension chercherait, coûterait et pourrait changer : c'est la seule question posée à l'utilisateur, après la phase 3 (§11.1), parce qu'elle engage du temps, pas un choix technique. Tu envoies la page sans rendre la main (§11.1) et tu continues ; sans réponse, l'exécution suit les choix documentés et l'extension ne s'ouvre pas, et une réponse tardive s'applique à l'exécution suivante. L'utilisateur ne peut pas arbitrer une question technique, mais il doit savoir ce que le modèle affirme et n'affirme pas avant de s'en servir.

### 11.4 Règle d'arrêt

**Par défaut, continuer et signaler.** Une erreur locale (document illisible, ressource introuvable, ligne rejetée par la validation, concept non résolu, triplet non classé, agrégat invalide) écarte l'élément concerné avec son motif, et tout va au journal et en tête de `delta.md`, pour que la réduction du périmètre soit visible au lieu d'être silencieuse. Deux cas seulement arrêtent l'exécution :

- **la SEC refuse durablement l'accès malgré les pauses** : continuer prolongerait la limitation sans rien obtenir ;
- **les contrôles comptables échouent de façon générale**, sur la plupart des groupes et des périodes et non sur quelques cas expliqués (les contrôles provisoires, `tolerance_basis = inferred`, n'y comptent pas) : le code produit alors des chiffres faux partout, et publier serait pire que ne rien publier.

Après un arrêt, préviens l'utilisateur. Dans le second cas, corrige le code et relance : le réseau étant en cache et les blocs déjà lus gardant leurs observations, cela ne coûte presque rien, tant que la correction ne touche ni le normaliseur, ni la délimitation, ni les faits candidats d'un bloc. Les sorties publiées restent celles du dernier commit.

### 11.5 Exécution périodique

Une tâche planifiée ouvre chaque jour une de tes sessions, puisque les blocs ne se lisent pas sans toi. Chaque session tient un verrou, `work/session.lock`, écrit à l'ouverture, touché par le code à chaque bloc validé et à chaque requête SEC, effacé à la clôture. La session planifiée tient pour vivant un verrou touché depuis moins de `session_stale_minutes` (annexe B) et ne fait alors rien : deux exécutions ne doivent jamais se chevaucher, d'abord à cause du réseau, puisque deux sessions à 5 requêtes par seconde atteignent le plafond de la SEC, qui vaut par utilisateur, ensuite parce que deux lectures d'un même bloc feraient deux passes. Un verrou plus ancien est périmé, et elle le remplace par le sien. Elle relance ensuite l'exécution interrompue par une limite s'il y en a une (§11.1), ou interroge les `submissions` des groupes de `config.yaml` et lance le pipeline si un dépôt surveillé est arrivé depuis le dernier commit : 10-K, 10-Q et leurs amendements, 10-KT, 10-QT, DEF 14A ; 8-K portant l'item 1.01, 1.02, 1.03, 2.01, 2.03, 2.04, 2.06, 3.01, 3.03, 4.01, 4.02 ou 8.01 ; NT 10-K, NT 10-Q ; et, si l'extension est ouverte, les formulaires de §14. **Le pipeline est idempotent** (§7.7) : une exécution n'est acquise qu'à son commit. Elle inscrit son `as_of` en tête de ses lignes de `journal.jsonl` ; des lignes non commitées signalent une exécution interrompue, y compris par une limite d'usage de l'abonnement, qui se relance avec cet `as_of`, le cache et les fichiers d'observations évitant de refaire requêtes et lectures. Dépôt git et cache persistent d'une exécution à l'autre.

## 12. Livrables [P4]

### 12.1 Le dépôt et les rendus

Le dépôt git contient le code et le schéma, `config.yaml`, cette spec, `decisions.md`, `plan.md`, les pages pour l'utilisateur, les huit tables, tes fichiers d'observations, `journal.jsonl` et les rendus. **Un commit par exécution**, à sa fin, garde la trace du code, de la configuration et des résultats ; les critères des annexes E et F ont en plus leur propre commit, avant la première requête (§11.1). Le cache n'est pas versionné mais se conserve : seules les archives (`cache/archives/`) se retrouvent à l'identique sur EDGAR, alors que les tirages d'API ne se retrouvent pas ; `documents` garde l'empreinte de tout ce qui a été lu. Les fichiers d'observations, eux, sont versionnés, car rien ne les reproduit (§7.4). **La source de vérité, ce sont les données et le code qui les produit : les rendus sont générés, jamais édités à la main.**

- **`synthesis.md`**, la note de synthèse. En tête : tout changement des critères des annexes E et F ou des seuils depuis leur commit, avec le diff et le résultat sous les critères d'origine ; quand une version de la spec a changé `config.yaml` sans changer les critères de l'annexe E, la mention qu'ils n'ont pas changé, avec l'empreinte du commit d'origine de ces critères et celle du commit courant de `config.yaml`, pour que l'auditeur ne lise pas un changement de critères là où il n'y en a pas, et de même pour la liste de l'annexe F ; le périmètre couvert (premier passage ou blocs de §14 ouverts), et, au premier passage, le rappel qu'une non-discrimination (E.7) tient d'abord à ce périmètre borné, ventilation des motifs à l'appui ; le compte des statuts des contrôles ; les exclusions principales ; un arrêt éventuel. Puis la section **Événements** : les événements de l'annexe F, par groupe et par date, chacun avec sa pièce, sans total ni score. Puis deux parties : **Fragilité** (par groupe : les mesures de rang 1 en série, rentabilité et croissance, liquidité, levier, flux, exposition, qualité du résultat, signaux, capitaux propres, date de la dernière information), puis **Circularité** (par paire : mesures, statuts, bornes, sensibilité `ever_financed`, conclusion, sorties de couverture, confrontation à l'annexe E même quand le résultat est vide). Enfin l'évolution, et ce qui n'a pas pu être établi. Chaque nombre est un jeton rempli par le code depuis `measures`, `controls` ou `exclusions`, et un nombre sans source est retiré avec sa phrase. Une conclusion sur une paire s'en tient aux valeurs de `relationship_conclusion`, et une cellule `not_determinable` s'affiche avec son motif, jamais comme un zéro.
- **`delta.md`**, lu en premier. En tête : un arrêt éventuel, les événements nouveaux de l'annexe F, le rendement du passage (§11.1), les exclusions nouvelles par motif, les décisions et variantes nouvelles, tout changement des critères des annexes E et F, les écarts avec l'annexe D. Puis les dépôts nouveaux, les valeurs changées pour des périodes déjà publiées, par `recast_cause` (la section la plus intéressante), les arêtes nouvelles, les contrôles qui ont basculé, les entités `pending`, le travail `not_processed`, les paires non additives muettes, et les changements dus à une nouvelle passe de lecture (§7.4) ou au code.
- **`series.md`**, ou son équivalent en feuille de calcul, la vue temporelle, générée comme les autres rendus : chaque mesure de rang 1, par groupe et par trimestre, en vue `as_known`, ruptures de base marquées (`basis_break`, `recast_boundary`), et les événements de l'annexe F en regard. `delta.md` reste lu en premier.

### 12.2 Le livrable d'audit

Le répertoire `audit/` est tout ce que reçoit l'auditeur : `numbers.csv` (chaque chiffre publié, avec l'accession et l'emplacement de chacun de ses termes, et `is_tagged`) ; `concepts.csv` (pour chaque groupe et grandeur, le concept retenu, la règle qui l'a retenu et tout changement après un `mismatch`, avec sa pièce nouvelle) ; `attributions.csv` (pour chaque montant attribué, la contrepartie, la citation et son emplacement) ; `exclusions.csv` (chaque exclusion et son motif) ; `annex_e.txt` (les critères de l'annexe E tels que commités, l'empreinte et la date de leur commit, l'horodatage de la première requête, le diff de tout changement ultérieur) ; `annex_f.txt` (de même pour la liste de l'annexe F) ; `domain_rules.md` (une page qui énonce les règles du domaine appliquées, §2 à §10, §13 et, si elle est ouverte, §14, avec leurs sources normatives, sans aucun résultat) ; `journal.jsonl` (adresse de contact masquée) ; `synthesis.md`, les tables `measures` et `controls`, et `AUDITOR.md`, l'annexe C telle quelle, sa liste de groupes remplie depuis `config.yaml`. Concepts et attributions y figurent parce que ce sont les deux choses que tu tranches seul et que les contrôles ne suffisent pas à vérifier (§8.3). Ni `decisions.md`, ni le code, ni la conversation de production : l'auditeur doit juger le résultat sans hériter des choix ni des bogues du producteur.

### 12.3 Ce que « fini » veut dire

Chaque agrégat publié respecte les invariants de §7.6 ; chaque contrôle est `ok`, `not_testable` motivé, `mismatch` expliqué ou `tautological` non compté ; chaque cellule attendue a un état ; les mesures de rang 1 sont publiées, celles de la question 4 et les sorties de couverture par paire, les autres par groupe et par trimestre, la matrice sans total unique ; les événements de l'annexe F et `series.md` sont générés ; chaque nombre publié a son accession et son emplacement ; le rendement est mesuré ; `audit/` est écrit ; le commit est fait.

## 13. Pièges du corpus [P7]

- **Les exercices ne coïncident pas** et font parfois 52 ou 53 semaines : un « T2 2026 » n'est pas la même période d'un émetteur à l'autre. Normalise sur `period_start` et `period_end`, jamais sur les libellés. Une mesure entre émetteurs s'aligne par intersection des fenêtres trimestrielles et publie l'écart maximal entre dates de fin : au-delà de 45 jours, elle est `partial`, jamais proratisée.
- **Les flux des 10-Q sont cumulés**, et le 10-K ne publie pas le quatrième trimestre : il s'obtient par différence (§7.3).
- **Un amendement ne remplace pas l'original**, il le complète ou le modifie : charge les deux, reliés par `amends_accession`.
- **Les changements d'exercice** créent des périodes de transition (10-KT, 10-QT) qui invalident toute comparaison naïve.
- **Les types de formulaire changent** : depuis le 18 décembre 2024, `SCHEDULE 13G` a remplacé `SC 13G`. Un filtre écrit une fois n'est pas un filtre à jour, et la liste des formulaires surveillés (§11.5) se revoit à chaque phase 0.
- **Rapporte toujours le dénominateur**, le stade et la période ; et une co-mention n'est pas un flux : que deux sociétés apparaissent dans le même paragraphe ne prouve rien.


## 14. Phase ultérieure, si le premier passage l'a justifié [P5, P6]

Rien ici ne s'exécute sans la décision de §11.1, et le rendement se mesure de nouveau après chaque bloc. `scope` liste les blocs ouverts par leur identifiant. L'ordre recommandé est `lender`, puis `text`, puis `discovery`, les autres ensuite : `lender`, `text` et les Form D de X.AI Corp. ne dépendent que des groupes de `config.yaml` et des contreparties que nomment leurs pièces ; `paths` suppose `discovery`, et `foreign` s'ouvre avec la découverte ou avec un groupe étranger de `config.yaml`.

**Le côté prêteur** (`lender`). La dette d'un véhicule de datacenter détenu par un fonds de dette privée n'apparaît pas chez le sponsor ; elle se voit chez le prêteur quand c'est une BDC (BDC Data Sets, fichier `soi`). Les marques en juste valeur sur coût que les BDC portent sur les prêts de datacenters sont l'un des rares signaux trimestriels structurés qui bougent avant les états des sponsors : c'est pourquoi ce bloc vient en tête. L'usage des BDC Data Sets se limite aux entités des groupes, aux contreparties que nomment leurs pièces et, si `discovery` est ouvert, aux contreparties découvertes, et à trois signaux lus ensemble, `bdc_fv_to_cost` (juste valeur ÷ coût), `bdc_pik_share` (part des intérêts capitalisés) et `bdc_non_accrual_share` (part des prêts sans accumulation d'intérêts), car un rapport juste valeur sur coût n'est pas une probabilité de défaut et des intérêts capitalisés peuvent être prévus dès l'origine. `soi` exclut tags et axes personnalisés (une absence n'y prouve rien), le millésime se garde (rafraîchissements rétroactifs, annexe D), taille d'une facilité et position détenue sont deux grandeurs, et les fonds privés ne publient rien (`not_public`).

**Le reste du texte des groupes de `config.yaml`** (`text`), sur la même période que la tranche, la fenêtre allongée et les huit trimestres qui la précèdent (§11.1) : notes d'investissements (participations qui ne sont pas des parties liées), de dette, de baux et d'engagements (contreparties des montants hors bilan, montants seulement narratifs), corps des EX-10 arrêtés à leur en-tête au premier passage (clauses des contrats d'origine entre établissements financiers, §11.1), texte autour des faits de concentration, 8-K items 2.01 et 2.03, signaux et leviers qui ne se lisent que dans le texte (§4.5, §6.1). C'est ce bloc qui rend calculable l'essentiel du rang 2.

**La découverte** (`discovery`) : qui, hors des groupes de `config.yaml`, nomme un groupe. Le fichier `txt` des Notes Data Sets rattache chaque bloc de texte de tous les déposants à sa note, si bien qu'un scan du lexique dit qui nomme un groupe, et où, sans télécharger un document ; ses archives (41 à 314 Mo, annexe D) se tirent de la plus récente à la plus ancienne, une période non tirée devient une exclusion et ses paires portent `search_incomplete`, et la clé de `num` inclut `dimh`, faute de quoi un total et ses ventilations fusionnent. La recherche plein texte (`efts.sec.gov/LATEST/search-index`) ne sert qu'aux EX-10 et Form D que ces archives ne couvrent pas ; plafonnée à 10 000 résultats, une requête saturée se resserre sur une période plus courte, et chaque requête est consignée pour être reproductible. Un déposant est candidat si la mention est **dans une note, un contrat annexé, une section parties liées ou un Form D**, jamais dans un facteur de risque, car « OpenAI » apparaît dans des milliers de dépôts sans lien. Les candidats se classent par une règle fixée d'avance, pour qu'aucun choix ne favorise les grands noms : classe de mention (contrat, parties liées, note, Form D), montant documenté décroissant (tiré de `num`, du XML du Form D ou d'un fait balisé, jamais d'une observation), nombre de groupes nommés, accession. Leurs notes structurantes se lisent en entier, un filtre lexical manquant les noms encore inconnus, et le lexique ne s'enrichit que d'entités confirmées (§10.2).

**Les Form D** (`form_d`) donnent un montant levé, cumulé depuis la première vente de l'offre, jamais une valorisation ni une contrepartie : la mesure se fait par offre (`form_d_offering_amount`, clé : CIK de l'émetteur et date de première vente) sur le dernier dépôt connu, puisque sommer un D et ses D/A compterait deux fois la même levée, et un montant qui peut inclure du non monétaire n'est pas du numéraire primaire sans autre pièce. Les émetteurs se distinguent par CIK (annexe D) : les Form D de X.AI Corp. sont des faits sur cette entité (§10.3) ; ceux des véhicules tiers, dont deux portent « Anthropic PBC » dans leur nom, mesurent une demande d'exposition secondaire, et **un Form D de véhicule n'entre jamais dans une mesure de financement du nœud sous-jacent** (`issuer_is_subject` faux). Ceux des véhicules qui vendent une exposition aux non-déposants forment une série descriptive publiée, `form_d_offering_amount` par véhicule et par trimestre, sur le dernier dépôt connu à chaque fin de trimestre, toujours hors des financements du nœud sous-jacent.

**Les chemins** (`paths`). Le retour « après un ou deux intermédiaires » est invisible aux mesures bilatérales, et ses intermédiaires sont ce que la découverte trouve. `documented_path` publie les cycles orientés de longueur 2 ou 3 entre groupes, hors intragroupe, avec `temporal` (arêtes actives ensemble ou à moins de quatre trimestres d'écart) ; la conclusion n'est `documented_dependency` que si chaque paire d'arêtes consécutives a sa pièce L1 à L5, et aucun ratio de chemin ne se publie, des montants de natures différentes ne se composant pas.

**Les émetteurs étrangers** (`foreign`) déposent des 20-F, 40-F et 6-K (§2.1) : une contrepartie ou un groupe en IFRS est traité à part et jamais sommé avec du US GAAP (invariant f), les deux cadres ne définissant pas de la même façon baux, participations et entités consolidées, et la tâche planifiée surveille alors ces formulaires, comme les Form D des entités suivies (§11.5).

**L'ajout de groupes.** Un groupe s'ajoute dans `config.yaml`, jamais dans le code, et chaque ajout se date dans les agrégats entre groupes (§9.6). L'ordre recommandé suit l'endettement, parce qu'une chaîne casse au maillon le plus endetté : les hébergeurs endettés d'abord (CoreWeave est déjà là ; TeraWulf, Cipher Mining, Core Scientific ; Nebius par `foreign`, puisqu'il dépose des 20-F et des 6-K, et IREN pour ses exercices clos jusqu'au 30 juin 2024, déposés en 20-F, ses 10-K ayant commencé avec l'exercice clos le 30 juin 2025, annexe D), les fabricants ensuite.



## Annexe A — Classer une pièce : principes et cas limites

La précédence est celle de §2.3 : déclaration expresse du déposant, puis item, puis pièce, puis formulaire ; le niveau se calcule par `tier` (§2.2), et `assurance_level` s'affine par extrait et par période. Cinq principes couvrent l'essentiel :

1. **Les 8-K items 2.02 et 7.01**, et leurs pièces, sont furnished, sauf déclaration expresse « filed » de l'émetteur (Form 8-K, General Instruction B.2).
2. **Un 6-K est furnished** (Form 6-K, General Instruction B) ; il n'est admissible que s'il est incorporé par référence dans un document d'enregistrement, par une mention expresse.
3. **Un communiqué est un pointeur**, jamais une preuve, quel que soit l'item sous lequel il est déposé : il indique où chercher la pièce de niveau A à D.
4. **Un EX-10 est un contrat** (niveau D) : il prouve des termes et des plafonds, pas un versement, et un montant caviardé y est `redacted` (§2.5) ; un EX-4 porte les termes d'un titre émis, dette ou bon de souscription (annexe D).
5. **Un EX-99 accompagné d'un consentement d'auditeur (EX-23)** est audité pour les seules pièces et périodes que nomment le consentement et le rapport de l'auditeur.

Pour le reste, les états et notes d'un 10-K, 10-KT, 20-F ou 40-F sont audités, ceux d'un 10-Q ou 10-QT revus, et les autres sections sont du narratif filed ; un document qui n'entre dans aucune extraction ni mesure est inventorié sans classement.

| Cas limite | Traitement |
| --- | --- |
| 8-K à plusieurs items, pièce citée sous un item furnished et un item filed, sans déclaration expresse | furnished (repli prudent) |
| 8-K items 8.01 et 9.01, EX-99 avec EX-23 (le 8-K de Microsoft, annexe D) | filed ; audité pour les périodes nommées : niveau A |
| EX-99 sous un item filed, sans EX-23 | communiqué : pointeur ; sinon, classement par extrait |
| S-1, S-1/A, 424B4 | filed ; exercices audités, périodes intermédiaires revues ou non auditées ; le 424B4 porte la version définitive |
| FWP, 425 | commercialisation (`marketing`) : niveau E par règle de projet |
| DEF 14A | filed ; gouvernance, sujet parties liées pour l'Item 404 : niveau C |
| 10-K ou 10-K/A, EX-99 portant des états 3-09 | audité pour les périodes du rapport ; faits sur le nœud de l'entité mise en équivalence, `source_perspective = counterparty` (§10.4) |
| Form D | filed ; montant vendu par offre (§14) : niveau C |



## Annexe B — Données de départ de `config.yaml`

Des données, pas des règles : le code lit `config.yaml`, jamais cette annexe, et les énumérations vivent dans le schéma (§0). Le fichier évolue ensuite (entités confirmées, décision d'étendre) ; les critères des annexes E et F et les seuils, commités avant la première requête, ne changent pas sans que la note le signale, sinon un seuil pourrait se desserrer jusqu'à ce qu'un contrôle passe.

```yaml
user_agent: null            # fourni par l'utilisateur, jamais inventé (§9.5)
scope: first_pass           # extension seulement sur décision de l'utilisateur (§11.1)
window: {start_fiscal_year: 2021, include_interim: true, companyfacts: unbounded}
                            # début : premier exercice clos en 2021 ; fin : as_of (§11.1) ;
                            # instances et texte sur la fenêtre allongée et les huit
                            # trimestres qui la précèdent, jamais sans borne
groups:                     # CIK indicatifs ; company_tickers.json fait foi (§10.1)
  NVDA: "0001045810"
  GOOGL: "0001652044"
  AMZN: "0001018724"
  META: "0001326801"
  MSFT: "0000789019"
  ORCL: "0001341439"
  CRWV: "0001769628"
  SPCX: "0001181412"
  AMD: "0000002488"
  AVGO: "0001730168"
  MRVL: "0001835632"
predecessors:               # émetteurs prédécesseurs (§10.1) ; dates de succession
                            # lues en phase 0 (annexe D)
  AVGO: {"Broadcom Limited": "0001649338", "Avago Technologies Limited": "0001441634"}
  MRVL: {"Marvell Technology Group Ltd.": "0001058057"}
known_entities:             # appartenances et dates lues en phase 0 (§10.3)
  SPCX: ["X.AI Holdings Corp.", "X.AI Corp.", "X Holdings Corp.", "X Corp.",
         "X.AI LLC", "CTC Property, LLC"]
cik_hints: {"X.AI Corp.": "0002002695"}
labs: [OpenAI, Anthropic]   # groupes économiques non déposants (§10.4)
lexicon_seed: [NVIDIA, Alphabet, Google, Amazon, "Amazon Web Services", Meta, Microsoft,
               Oracle, CoreWeave, SpaceX, xAI, "X.AI", OpenAI, Anthropic, Stargate,
               AMD, "Advanced Micro Devices", Broadcom, Avago, Marvell]
                            # « AMD » en mot entier et en capitales : l'acronyme désigne
                            # aussi une maladie de l'œil dans les dépôts de biotechnologie
tier1: []                   # à remplir depuis le tableau de §11.1
thresholds:                 # seuils cités dans le corps
  financed_lookback_quarters: 8         # §3.2
  vendor_credit_min_months: 12          # §3.1
  c5_date_tolerance_days: 45            # §8.3
  max_end_offset_days: 45               # §13
  eps_scale_relative_tolerance: 0.10    # §8.3, C14
  denominator_min_revenue_share: 0.05   # §6.2
  scale_jump_factor: 100                # §7.3
reading:                    # plafond de lecture (§7.4, §9.1), hypothèse
  max_read_chars: 80000                 # ce que tu lis d'un coup ; n'entre dans
                                        # aucune clé, modifiable à tout moment
session_stale_minutes: 120  # verrou de session périmé au-delà (§11.5)
non_additive_pairs: []      # à écrire depuis §8.2, en sélecteurs sur les colonnes
annex_e: {}                 # à transcrire depuis l'annexe E, commité avant toute requête
annex_f: {}                 # à transcrire depuis l'annexe F, commité avec l'annexe E
concept_anchors:            # contrôle de la règle de §8.3 ; noms locaux présents
                            # dans us-gaap-2026.xsd (annexe D)
  revenue_total: [Revenues, RevenueFromContractWithCustomerExcludingAssessedTax]
  net_income: [NetIncomeLoss]
  operating_income: [OperatingIncomeLoss]
  pretax_income_continuing: [IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest]
  total_assets: [Assets]
  current_assets: [AssetsCurrent]
  total_liabilities: [Liabilities]
  current_liabilities: [LiabilitiesCurrent]
  temporary_equity: [TemporaryEquityCarryingAmountAttributableToParent]
  equity_including_nci: [StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest]
  cash_and_equivalents: [CashAndCashEquivalentsAtCarryingValue]
  restricted_cash_current: [RestrictedCashCurrent]
  restricted_cash_noncurrent: [RestrictedCashNoncurrent]
  cash_and_restricted_cash_total: [CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents]
  cfo: [NetCashProvidedByUsedInOperatingActivities]
  cfi: [NetCashProvidedByUsedInInvestingActivities]
  cff: [NetCashProvidedByUsedInFinancingActivities]
  capex_cash: [PaymentsToAcquirePropertyPlantAndEquipment]
  unpaid_capex: [CapitalExpendituresIncurredButNotYetPaid]
  eps_diluted: [EarningsPerShareDiluted]
  diluted_shares_weighted: [WeightedAverageNumberOfDilutedSharesOutstanding]
  net_income_to_common_diluted: [NetIncomeLossAvailableToCommonStockholdersDiluted]
  rpo_total: [RevenueRemainingPerformanceObligation]
  contract_liabilities: [ContractWithCustomerLiability]
  operating_lease_liability_current: [OperatingLeaseLiabilityCurrent]
  operating_lease_liability_noncurrent: [OperatingLeaseLiabilityNoncurrent]
  operating_lease_payments_undiscounted: [LesseeOperatingLeaseLiabilityPaymentsDue]
  operating_lease_imputed_interest: [LesseeOperatingLeaseLiabilityUndiscountedExcessAmount]
  finance_lease_liability_current: [FinanceLeaseLiabilityCurrent]
  finance_lease_liability_noncurrent: [FinanceLeaseLiabilityNoncurrent]
  finance_lease_payments_undiscounted: [FinanceLeaseLiabilityPaymentsDue]
  finance_lease_imputed_interest: [FinanceLeaseLiabilityUndiscountedExcessAmount]
  capitalized_interest: [InterestCostsCapitalized]
  short_term_investments: [ShortTermInvestments]
  undrawn_committed_facilities: [LineOfCreditFacilityRemainingBorrowingCapacity]
  dividends_paid: [PaymentsOfDividends, PaymentsOfDividendsCommonStock]
  dividends_declared: [Dividends, DividendsCommonStock]
  profit_including_nci: [ProfitLoss]
  vendor_financed_ppe_additions: [NoncashOrPartNoncashAcquisitionFixedAssetsAcquired1]   # sans distinction du mode de paiement
  stock_paid_ppe_additions: [StockIssued1]      # souvent en extension ou seulement narratif
  debt_proceeds: [ProceedsFromIssuanceOfLongTermDebt, ProceedsFromIssuanceOfDebt]
  debt_repayments: [RepaymentsOfLongTermDebt, RepaymentsOfDebt]
  rou_obtained_finance_lease: [RightOfUseAssetObtainedInExchangeForFinanceLeaseLiability]
  rou_obtained_operating_lease: [RightOfUseAssetObtainedInExchangeForOperatingLeaseLiability]
  finance_lease_principal_payments: [FinanceLeasePrincipalPayments]
  pik_interest: [PaidInKindInterest]
  equity_method_income: [IncomeLossFromEquityMethodInvestments]
  dilution_gain: [GainLossOnSaleOfStockInSubsidiaryOrEquityMethodInvestee]
  investment_gain_loss: [EquitySecuritiesFvNiGainLoss,
    EquitySecuritiesWithoutReadilyDeterminableFairValueUpwardPriceAdjustmentAnnualAmount,
    EquitySecuritiesWithoutReadilyDeterminableFairValueDownwardPriceAdjustmentAnnualAmount]
  investment_impairment: [EquityMethodInvestmentOtherThanTemporaryImpairment,
    EquitySecuritiesWithoutReadilyDeterminableFairValueImpairmentLossAnnualAmount]
concept_anchors_to_verify:  # ajouts v6 (§4.2), à vérifier en phase 0 dans le paquet épinglé
  gross_profit: [GrossProfit]
  cost_of_revenue: [CostOfRevenue, CostOfGoodsAndServicesSold]
  receivables: [AccountsReceivableNetCurrent]
  inventories: [InventoryNet]
  accounts_payable: [AccountsPayableCurrent]
  contract_liabilities_current: [ContractWithCustomerLiabilityCurrent]
  segment_axis: [StatementBusinessSegmentsAxis]
unanchored_quantities:      # résolues par la seule règle de §8.3
  [income_tax_expense, effective_tax_rate, retained_earnings, fx_effect_on_cash,
   depreciation_expense, gross_depreciable_ppe, land, construction_in_progress,
   debt_principal, debt_carrying_amount, rpo_within_12m, contract_assets, sbc_expense,
   interest_expense, interest_paid]
```



## Annexe C — Consignes pour l'auditeur

*À transmettre telles quelles dans `audit/AUDITOR.md`, le code y remplissant la liste des groupes depuis `config.yaml`.*

Tu audites un modèle comptable construit à partir des dépôts SEC des groupes suivants et des contreparties qu'ils nomment : {groupes de `config.yaml`, avec leurs CIK et ceux de leurs prédécesseurs}. Il mesure la fragilité financière de chaque groupe (rentabilité, liquidité, levier, flux, exposition hors bilan, qualité du résultat, signaux, événements datés), circularité des financements comprise : la part du revenu d'un fournisseur qui vient de clients qu'il finance. Il ne prédit rien et ne note rien. Tu reçois le répertoire `audit/` : la note de synthèse, les tables `measures` et `controls`, l'accession et l'emplacement de chaque chiffre publié (`numbers.csv`), la correspondance de concepts (`concepts.csv`), les attributions de contrepartie avec leurs citations (`attributions.csv`), les exclusions et leur motif, les critères de réfutation et la liste des événements de fragilité, avec l'empreinte de leur commit (`annex_e.txt`, `annex_f.txt`), le journal des requêtes du producteur (`journal.jsonl`) et une page de règles du domaine (`domain_rules.md`). Rien d'autre.

1. **Re-dérive depuis EDGAR, pas depuis les tableaux**, et seulement ce qui compte : tous les nombres de la note de synthèse, et 30 cellules de `measures` stratifiées par niveau de preuve. Pour chacun, retrouve le dépôt par son accession, lis la valeur à l'emplacement indiqué et recalcule la mesure. Un tableau du producteur n'est jamais une preuve de lui-même, mais tu n'as pas à réécrire son pipeline.
2. **Tu ne vois pas le raisonnement du producteur** : ni sa conversation, ni ses notes de décision, ni son code. Ne les demande pas. Tu juges le résultat, pas l'intention, et tu ne dois pas hériter de ses erreurs.
3. **Ta consigne est adverse**, et elle commence par les deux choses que le producteur a tranchées seul et que ses contrôles ne suffisent pas à vérifier. **La correspondance de concepts** (`concepts.csv`) : pour chaque grandeur qui alimente un chiffre de la note, le concept retenu figure-t-il dans la linkbase de présentation du déposant pour l'état concerné, sa définition correspond-elle, et tout changement après un `mismatch` s'appuie-t-il sur une pièce nouvelle ? Un concept choisi parce qu'il fait passer un contrôle est le défaut à chercher. **Les attributions** (`attributions.csv`) : la citation, lue à son emplacement, nomme-t-elle la contrepartie et le montant ? Un client anonyme présenté comme nommé, une annonce (8-K item 7.01, communiqué, document furnished) prise pour un fait, un contrat pris pour un versement sont les défauts à chercher. Ensuite : un double comptage, une borne ou un statut plus fort que les pièces, un ratio présenté comme une causalité, une rupture de périmètre ou de norme non signalée, un score, un classement ou une prédiction. Hors de l'échantillon du point 1, ne cherche pas d'erreur de calcul : le code est rejouable et redonne les mêmes chiffres, alors que concepts et contreparties sont des choix.
4. **Liste toi-même les dépôts là où une omission change une conclusion** : les notes de parties liées des 10-K et 10-Q, l'Item 404 (DEF 14A, partie III d'un 10-K/A, ou 424B4 d'une introduction récente) et les items 1.01, 1.02, 3.03 et 8.01 des 8-K avec leurs EX-10 et EX-4, sur la fenêtre allongée de l'annexe E et les huit trimestres qui la précèdent ; l'Item 9A des 10-K et 10-K/A, l'Item 4 de la partie I des 10-Q et le doute sur la continuité d'exploitation des 10-K et 10-Q (bloc balisé ou passage de la note 1), sur la fenêtre ; tous pour les groupes de la liste, prédécesseurs compris (`submissions`, toutes les pages de `filings.files`). Un 8-K plus ancien n'est pas une omission : une détention ancienne encore en cours s'établit par la note d'investissements courante, pas par le 8-K de son acquisition. Signale toute pièce de ce type qui n'est ni exploitée ni exclue, et tout amendement autonome dont le corps n'a pas été lu, puisque, quelles que soient ses parties, c'est l'événement F4 lui-même : un EX-10 dont le titre contient « Amendment », « Waiver » ou « Consent » en mot entier, sauf si, un ordinal mis à part, il commence par « Amended and Restated », ou un EX-4 « Supplemental Indenture », précédé ou non d'un ordinal, annexé à un 8-K qui porte l'item 3.03. Un contrat d'origine entre établissements financiers, « Amended and Restated » compris, peut rester à son en-tête, exclu avec son motif, comme un « Supplemental Indenture » sans item 3.03, qui est une émission nouvelle.
5. **Seul EDGAR vaut comme vérification** : ni presse, ni agrégateur, ni mémoire. Un chiffre que tu ne retrouves pas dans un dépôt est faux pour ce modèle.
6. **Mêmes limites d'accès SEC que le producteur** : un seul User-Agent déclaré (nom réel et adresse de contact surveillée), au plus 5 requêtes par seconde (le plafond de la SEC est de 10 par utilisateur, toutes machines confondues, donc n'audite pas pendant une exécution du producteur), une pause d'au moins 10 minutes après un 403, aucun changement d'identité pour contourner une limitation.

Vérifie aussi que les critères de réfutation et la liste des événements ont été commités avant la première requête (`annex_e.txt`, `annex_f.txt`, `journal.jsonl`), que tout changement ultérieur est signalé en tête de la note, et que le journal ne montre jamais plus de 10 requêtes SEC sur une seconde glissante ni de requête pendant une pause qui suit un 403. Rends une liste de constats, du plus grave au moins grave ; chaque constat donne l'accession, l'emplacement, la valeur publiée, la valeur que tu lis, et la conclusion qu'il invalide ou affaiblit.


## Annexe D — Faits vérifiés

Toutes consultées le 24 septembre 2026, sauf les cinq lignes sur AMD, Broadcom, Marvell, IREN et Nebius, consultées le 25. Ce sont des indications que le pipeline re-vérifie, jamais des données à recopier : aucune règle ne dépend de leur valeur, et un écart entre une indication et ce que le pipeline constate est signalé en tête de `delta.md`.

### D.1 Dépôts, API et jeux de données

| Objet | Fait |
| --- | --- |
| SpaceX, `submissions` | `data.sec.gov/submissions/CIK0001181412.json` : SPCX, Nasdaq, SIC 7370, clôture au 31 décembre, Texas, « Non-accelerated filer » ; 83 dépôts : un 10-Q, un 424B4, S-1 et S-1/A, 7 FWP, 15 D et 6 D/A électroniques plus 4 REGDEX et 1 REGDEX/A papier (2002-2008), 4 SCHEDULE 13G |
| SpaceX, chaîne d'enregistrement | premier DRS soumis le 30 mars 2026 (0001628280-26-021860) ; DRS/A du 7 mai 2026 (0001628279-26-000583) ; S-1 public le 20 mai 2026 ; S-1/A du 1er juin 2026 (0001628280-26-039276), sans XBRL ; S-1/A du 3 juin 2026 (0001628280-26-040364) : `-xbrl.zip` de 3 437 octets, `spcxexfilingfees_htm.xml`, R1 à R3, `FilingSummary.xml` de 2 552 octets |
| SpaceX, lettres du personnel | UPLOAD du 24 avril 2026 (0000000000-26-004247), commentaires 33, 38, 39, 43 à 45 et 55 ; le document du 29 mai 2026 est une autre lettre (UPLOAD) |
| SpaceX, 424B4 | 0001628280-26-042639, déposé le 12 juin 2026 ; `spaceexplorationtechnologi.htm`, 11 953 976 octets ; aucun XBRL ; couverture : « The initial public offering price is $135.00 per share » ; états au 31 mars 2026 ; base de présentation : retraitement rétrospectif de toutes les périodes présentées, contrôle commun ; `size` de la soumission complète : 203 Mo |
| SpaceX, 10-Q au 30 juin 2026 (10-Q de référence) | 0001628280-26-052535, déposé le 4 août 2026 ; `-xbrl.zip` de 389 718 octets, contenant les sept pièces déposées, de EX-3.1 à EX-32.2 ; `spcx-20260630_htm.xml` de 2 342 145 octets ; `spcx-20260630.htm` de 2 271 923 octets ; `FilingSummary.xml` de 51 159 octets ; 86 fichiers R ; 105 documents dans l'en-tête SGML ; `size` de la soumission complète : 13,3 Mo |
| SpaceX, contenu du 10-Q | `dei:EntityEmergingGrowthCompany = false` ; 1 647 faits portant un `id` ; 47 faits `decimals="INF"`, précisions −6, −5 et 2 à 5 ; 180 faits `ixt:fixed-zero`, dont 168 affichés en tiret cadratin ; 140 `sign="-"` ; facteurs d'échelle 6, 0, −2, −4 et 9 ; 20 notes pour 49 blocs de texte, note 10 balisée deux fois, note 1 sous `us-gaap:NatureOfOperations` ; aucun échéancier de baux balisé ; espace de noms `http://fasb.org/us-gaap/2026` ; 18 faits de revenu pour 16 jeux de dimensions au premier semestre 2026 ; `CustomerAMember` 17,9 % et `CustomerBMember` 12,2 % du revenu du semestre ; `UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount` renvoie à ASC 440-10-50-4(b) dans `MetaLinks.json` ; obligations d'achat de 27 955 M$ au 30 juin 2026, tranches standard égales à ce total, tranche « après la quatrième année » en extension (`spcx:UnrecordedUnconditionalPurchaseObligationToBePaidAfterYearFour`), nulle ; capitaux propres temporaires de 38 752 M$ au 31 décembre 2025 ; note 17, Valor : cession-bail non aboutie, obligation de financement de 2 039 M$ courante et 11 290 M$ non courante au 30 juin 2026, 455 M$ et 4 052 M$ au 31 décembre 2025, 513 M$ d'intérêts au semestre, membres `RelatedPartyMember` et `AffiliatedEntityMember` ; `spcx:NumberOfFailedSaleLeasebackTransactions` = 3 |
| SpaceX, `companyconcept` `us-gaap/Assets` | 2 faits, tous deux du 10-Q ci-dessus : 92 079 M$ au 2025-12-31 (`fy = 2026`, `fp = Q2`) et 192 770 M$ au 2026-06-30 |
| SpaceX, regroupements | 10-Q, note 1 : acquisition de X.AI Holdings Corp. le 2 février 2026 ; acquisition de X Holdings Corp. et X.AI Corp. par X.AI Holdings Corp. le 28 mars 2025 ; échanges d'actions ; note de dette : X Corp., X.AI LLC et CTC Property, LLC garants du prêt-relais |
| SpaceX, 8-K du 15 juin 2026 | items 3.02, 3.03, 5.02, 5.03, 7.01, 8.01, 9.01 |
| xAI, Form D | X.AI Corp., CIK 0002002695 : 2023-12-05, 2024-05-28, 2024-12-05, 2025-02-25 ; véhicules X.AI Corp AGC II (CIK 0002036163), AGC III (0002074953), AGC IV (0002076706) |
| Anthropic et OpenAI, Form D | recherche plein texte du 24 septembre 2026, `forms=D` : 111 résultats pour « Anthropic » (92 D, 19 D/A) et 47 pour « OpenAI » (41 D, 6 D/A), aucun des émetteurs eux-mêmes ; véhicules nommés « Anthropic PBC » : CIK 0002062711 et 0002112584 |
| CoreWeave | 10-K 2025 : CIK 0001769628, accession 0001769628-26-000104, déposé le 2 mars 2026 ; ancienne dénomination « Atlantic Crypto Corp » jusqu'au 3 octobre 2019 (`formerNames`) |
| AMD, Broadcom et Marvell, `submissions` | AMD : CIK 0000002488, Nasdaq, SIC 3674, Delaware, `fiscalYearEnd` 1226, exercice clos le dernier samedi de décembre (10-K 0000002488-26-000018, exercice clos le 27 décembre 2025) ; Broadcom Inc. : CIK 0001730168, Nasdaq, SIC 3674, `fiscalYearEnd` 1101, exercice clos le dimanche le plus proche du 31 octobre (10-K 0001730168-25-000121, clos le 2 novembre 2025) ; Marvell Technology, Inc. : CIK 0001835632, Nasdaq, SIC 3674, Delaware, `fiscalYearEnd` 0130, exercice clos le samedi le plus proche du 31 janvier (10-K 0001835632-26-000011, clos le 31 janvier 2026) |
| Broadcom et Marvell, prédécesseurs | 8-K12B de Broadcom Inc. le 4 avril 2018 (0001193125-18-107559) ; Broadcom Ltd, CIK 0001649338, aujourd'hui « Broadcom Pte. Ltd. » : 25-NSE le 4 avril 2018, 15-12B le 16 avril 2018 ; Avago Technologies Ltd, CIK 0001441634 : 15-12B le 8 février 2016 ; Marvell Technology Group Ltd, CIK 0001058057, Bermudes : dernier 10-K déposé le 16 mars 2021 (0001058057-21-000009, exercice clos le 30 janvier 2021) ; 8-K12B de Marvell Technology, Inc. le 20 avril 2021 (0001193125-21-122938), puis son premier 10-Q, déposé le 9 juin 2021 (0001835632-21-000010, trimestre clos le 1er mai 2021) |
| Bons de souscription remis à des clients | AMD, 8-K du 6 octobre 2025 (0001193125-25-230895), items 1.01, 3.02, 7.01 et 9.01 : bon à OpenAI OpCo, LLC sur 160 millions d'actions à 0,01 $, acquis par tranches selon les achats de GPU (de 1 à 6 GW) et des seuils de cours jusqu'à 600 $ ; EX-4.1 (le bon), EX-10.1 (droits d'enregistrement). AMD, 8-K du 24 février 2026 (0000002488-26-000045), mêmes items : même structure au profit de Meta Platforms, Inc. (160 millions d'actions, de 1 à 6 GW équivalents), avec un avenant au contrat-cadre d'achat du 23 mai 2023. Marvell, 8-K du 2 décembre 2025 (0001193125-25-305271), item 8.01 seul : bon au profit d'Amazon sur 1 045 171 actions à 87,0029 $, acquis selon ses achats de produits « photonic fabric » jusqu'au 31 décembre 2030. Marvell, 8-K du 19 août 2026 (0001193125-26-356217), items 1.01, 3.02 et 9.01 : contrat commercial avec Google LLC du 29 juillet 2026 et bon sur 58 970 907 actions à 206,58 $, une tranche par 500 M$ de revenu de produits sur mesure ; termes sous l'item 1.01, EX-4.1, aucun EX-10 |
| IREN et Nebius | IREN Ltd (anciennement Iris Energy), CIK 0001878848, Australie, clôture au 30 juin : 20-F jusqu'à l'exercice clos le 30 juin 2024 (0001628280-24-038677, amendé par 0001878848-25-000020), puis 10-K à partir de l'exercice clos le 30 juin 2025 (0001878848-25-000063, déposé le 28 août 2025), avec 10-Q et 8-K ; Nebius Group N.V., CIK 0001513845 : 20-F et 6-K |
| Broadcom, Google et Anthropic | 8-K du 6 avril 2026 (0001193125-26-144028), item 8.01 seul : accord de long terme avec Google LLC (TPU sur mesure jusqu'en 2031) et collaboration avec Google et Anthropic PBC (environ 3,5 GW de capacité TPU à partir de 2027) ; « OpenAI » n'apparaît dans aucun dépôt de Broadcom Inc. (recherche plein texte) |
| Microsoft, 8-K du 3 décembre 2024 | 0000950170-24-132722 ; items 8.01 et 9.01 ; `EX-23.1`, `EX-99.1` ; 118 fichiers R ; `LesseeOperatingLeaseLiabilityPaymentsDueNextTwelveMonths` = 4 124 M$ au 2024-06-30 dans `companyfacts`, avec `form = 8-K` et `fy`/`fp` nuls |
| NVIDIA, `submissions` | `filings.recent` : 1 000 dépôts (2020-09-03 → 2026-09-23) ; du 2020-08-19 au 2026-09-18, `recent` et `files` réunis : environ 1 000 dépôts, dont 556 Form 4, 246 Form 144, 62 8-K, 19 10-Q ; 13F-HR depuis le 14 février 2024 |
| Profondeur de `filings.recent` | Alphabet : jusqu'au 29 juin 2023 ; Meta : 13 juin 2024 ; CoreWeave : 19 août 2025 |
| Huit groupes d'origine, `filings.recent` depuis le 1er janvier 2021 | au moins 1 876 dépôts de formulaires absents de l'annexe A de la v4, et 41 8-K à items hors annexe ; 54 8-K (dont un 8-K/A) mêlant un item *furnished* et un item *filed* autre que 9.01 : Oracle 26, Alphabet 9, CoreWeave 9, NVIDIA 3, Microsoft 3, Amazon 2, SpaceX 2 |
| `companyfacts` des huit groupes d'origine | 23,9 Mo au total, contre 200 à 350 Mo supposés par la v4 (facteur 8 à 15) : NVDA 4,1 ; GOOGL 3,2 ; AMZN 4,5 ; META 2,7 ; MSFT 4,9 ; ORCL 4,0 ; CRWV 0,5 ; SPCX 0,1 ; taxonomies présentes au-delà de `us-gaap` et `dei` : `ecd`, `ffd`, `invest` |
| *Frame* `us-gaap/Assets/USD/CY2024Q4I` | NVIDIA au 26 janvier 2025, valeur tirée du 10-K de l'exercice 2026 (0001045810-26-000021) ; Oracle au 30 novembre 2024 ; Microsoft au 31 décembre 2024 ; plage du 22 novembre 2024 au 4 février 2025 |
| API EDGAR | `https://www.sec.gov/search-filings/edgar-application-programming-interfaces` : taxonomies non personnalisées « e.g. », entité entière ; `filings.recent` : au moins un an ou 1 000 dépôts, « whichever is more » |
| Politique d'accès | `https://www.sec.gov/about/developer-resources` ; `https://www.sec.gov/about/privacy-information` ; `https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data` ; `https://www.sec.gov/about/webmaster-frequently-asked-questions` : 10 requêtes par seconde « regardless of the number of machines used to submit requests » ; limitation de l'adresse IP « for a brief period », levée une fois le débit resté 10 minutes sous le seuil ; en-tête « Sample Company Name AdminContact@<sample company domain>.com » |
| *Financial Statement and Notes Data Sets* | `sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets` : couverture « January 2009 - August 2026 », archive la plus ancienne 2009q1 ; readme `sec.gov/files/aqfsn_1.pdf` : huit fichiers ; clé de `num` ; mensuels depuis novembre 2020, consolidation trimestrielle après un an depuis mars 2024 ; 41–314 Mo et 400–800 Mo ; archive `2026_01_notes.zip` (43 Mo) : `txt` non tronqué, 190 846 lignes, valeur la plus longue de 287 406 caractères, 1 755 valeurs au-delà de 8 180, 8 lignes sous la moitié de `txtlen`, dont 7 vides ; le readme se contredit (2 048 et 8 192) |
| *BDC Data Sets* | `sec.gov/data-research/sec-markets-data/bdc-data-sets` : « The data sets will be updated monthly », couverture « October 2022 - August 2026 » ; readme `sec.gov/files/bdc_readme.pdf` du 9 juin 2026 : huit fichiers dont `soi` ; périodes à partir du 1er août 2022 pour certains fonds et du 1er février 2023 pour les autres ; premier jeu en octobre 2022 ; rafraîchissements de juin, juillet et septembre 2026 |
| Recherche plein texte | `efts.sec.gov/LATEST/search-index` : métadonnées seulement, pages de 100, fenêtre plafonnée à 10 000 résultats ; `forms=D` inclut les D/A ; `forms=D,D/A` : erreur 500 |
| Titrisations de datacenters | réponse du personnel de l'Office of Structured Finance du 29 juillet 2026 à la demande de Latham & Watkins du 23 juillet 2026 (`sec.gov/rules-regulations/no-action-interpretive-exemptive-letters/division-corporation-finance-no-action/certain-data-center-securitizations-072926`) |

### D.2 Normes, règles et taxonomies

| Objet | Référence |
| --- | --- |
| Normes et règles | ASU 2016-18, 2020-06, 2022-04, 2023-07, 2023-09, 2024-03 et 2025-01, 2025-06, 2025-07 (textes publics du FASB) ; ASC 205-40, 230-10-45-13(c) et 50-8, 250-10-50-4, 270, 275-10-50-16, 280-10-50-42, 323-10-35, 340-40, 440-10-50-2 et 50-4, 460-10-25-1 et 50-4, 606-10-25-9, 32-15 à 32-18, 32-21, 32-25, 50-5, 50-13 à 50-14B, 55-36 à 55-40, 805-10-50-2(h), 835-20, 842-20-50-3 et 50-6, 850-10-50-3, 860-20-50 ; Reg S-K Items 303 (Release 33-10890), 404(a), 601(b)(10)(ii) et (iv) ; Reg S-T Rule 405(d) ; Reg S-X Rules 3-05, 3-09, 4-08(g), 4-08(k), article 10 ; Rules 12b-25, 13a-10, 425, 433 ; Form 8-K, General Instruction B.2 ; Form 6-K, General Instruction B ; Securities Act §6(e) ; Schedules 13D et 13G : conformité obligatoire le 18 décembre 2024 ; IFRS 9, 10, 12, 16, 18 |
| Taxonomies acceptées par EDGAR | page « Operating Companies » des taxonomies standard de la SEC (`sec.gov/data-research/standard-taxonomies/operating-companies`) : US GAAP 2026 et 2025, avec `dei` 2026 et 2025 ; IFRS 2025 (`full_ifrs-cor_2025-03-27.xsd`) et 2024 ; aucune IFRS 2026 listée |
| Paquets épinglés | `xbrl.fasb.org/us-gaap/2026/us-gaap-2026.zip` (paquet de taxonomie, `META-INF/taxonomyPackage.xml`) ; `xbrl.fasb.org/srt/2026/srt-2026.zip` ; `xbrl.sec.gov/dei/2026/dei-2026.xsd` ; `xbrl.ifrs.org/taxonomy/2025-03-27/full_ifrs/full_ifrs-cor_2025-03-27.xsd` et `full_ifrs_entry_point_2025-03-27.xsd` : tous accessibles ; les noms locaux des ancrages vérifiés de l'annexe B figurent dans `us-gaap-2026.xsd` |
| Reg S-K Item 601(b)(10)(iv) | eCFR, 17 CFR 229.601 : caviardage permis si l'émetteur « customarily and actually treats that information as private or confidential » et si l'information omise n'est pas significative |
| Domaine `bullbaby.com` | classé domaine de messagerie jetable par `check-mail.org` (§9.5) |
| Pages d'erreur de la SEC | titres « Request Rate Threshold Exceeded » (débit) et « Your Request Originates from an Undeclared Automated Tool » (en-tête non déclaré) (§9.5) |
| Rule 12b-25(b)(2)(ii) | eCFR, 17 CFR 240.12b-25 : rapport annuel (10-K, 20-F…) déposé au plus tard le quinzième jour civil suivant l'échéance, rapport trimestriel (10-Q) au plus tard le cinquième |
| IFRS 18 | `ifrs.org`, page de la norme : en vigueur pour les exercices ouverts à partir du 1er janvier 2027 |
| ASU 2020-06, 2025-06, 2025-07 | `storage.fasb.org/ASU%202020-06.pdf`, `ASU%202025-06.pdf`, `ASU%202025-07.pdf` : dates d'effet reprises en §6.3 |



## Annexe E — Énoncés de réfutation

**Statut.** Ces énoncés sont écrits avant toute exécution, parce que la tentation permanente, sur une thèse contestée, est de collecter les exemples qui illustrent la conclusion attendue. Leurs critères (issues, seuils, grille, règles d'agrégation) sont transcrits dans `config.yaml` et commités avant la première requête (§11.1) ; tout changement ultérieur est signalé en tête de la note de synthèse, avec le diff et le résultat sous les critères d'origine. Le code confronte les énoncés aux mesures à chaque exécution ; chaque issue est une cellule de `measures` (`annex_e_outcome`, l'énoncé, le point de grille et `date_basis` dans `breakdown_key`), et la note cite cette confrontation, y compris quand le résultat est vide. Identifiants : `E1` à `E6` pour les énoncés, `E7` à `E9` pour les règles.

**E.0 Conventions.**

- **Issues.** E.1 : `supported`, `not_supported` ou `indeterminate`. E.2 et E.3 : `supported`, `refuted` ou `indeterminate`. E.5 : `supported` ou `indeterminate`, jamais `refuted`. E.4 et E.6 sont descriptifs, ont leurs propres issues et n'entrent pas dans E.7. Une mesure `not_determinable` conduit toujours à `indeterminate`, avec son `nd_reason` pour motif ; les autres motifs sont `search_incomplete`, `date_missing`, `interval_straddles_threshold` (intervalle à cheval sur un seuil) et `precondition_not_met`.
- **Vue principale `as_known`** : chaque exercice est évalué avec les dépôts connus à la date limite de dépôt de son rapport annuel (10-K, 20-F ou 40-F), plafonnée à l'`as_of` de l'exécution ; l'`as_of` de la cellule porte cette date. La vue `revised` est publiée en sensibilité.
- **Unité** : la paire (groupe fournisseur, groupe économique client). Les mesures se lisent par exercice fiscal du fournisseur, et chaque énoncé rend une issue par paire, sur les exercices de la fenêtre.
- **Précondition de puissance** : une mesure `computed` ou `bounded`.
- **Grille** : E.2 et E.3 s'évaluent à chaque point de la grille, un seuil haut s ∈ {5 %, 10 %, 20 %} et un seuil bas s/2. Le point s = 10 % est le résultat de tête ; les deux autres sont publiés à côté, jamais à sa place.
- **Fenêtre allongée** : la fenêtre d'analyse (§11.1), de l'exercice `window.start_fiscal_year` à `as_of`, reculée de quatre trimestres.
- **Recherche complète** : tous les dépôts du fournisseur et, s'il dépose, du client, sur la fenêtre allongée, ont été traités ; aucun candidat pertinent n'est `not_processed` ni `parse_failed` ; aucune clause pertinente n'est `redacted` ; aucune requête ni période de données pertinente n'est exclue pour `search_incomplete` ou `not_processed`.

**E.1 Lien documenté.** Pour chaque paire où F vaut `active`, sous la politique `exposure_outstanding`, pendant au moins un trimestre de la fenêtre allongée : `supported` si au moins une pièce L1 à L5 est trouvée ; `not_supported` si la recherche est complète et n'en trouve aucune ; `indeterminate` sinon. Publication : nombre de paires par issue, avec la couverture contractuelle (`contract_coverage`, §2.5).

**E.2 Dépendance de revenu** (`documented_revenue_dependency`, politique `exposure_outstanding`). À chaque point s de la grille : `supported` si `value_lower ≥ s` sur au moins deux exercices consécutifs ; `refuted` si `value_upper < s/2` sur tous les exercices évaluables, avec au moins deux exercices évaluables ; `indeterminate` sinon. Au point de tête, 10 % est le seuil de publication d'ASC 280, et 5 % laisse une marge d'un demi-seuil.

**E.3 Dépendance du carnet** (`documented_backlog_dependency`) : mêmes règles et même grille, sur le RPO de fin d'exercice.

**E.4 Chronologie** (descriptif). Pour les paires qui ont un engagement de financement daté et au moins un engagement d'achat daté, deux lectures séparées (`date_basis`) : sur les dates d'engagement (t_f = date de l'engagement de financement ; achats = engagements d'achat) et sur les dates de versement (t_f = date du versement ou du tirage ; achats = paiements). `compatible` si un engagement d'achat, ou un paiement, du client est daté dans [t_f − 90 jours ; t_f + 365 jours] ; `indeterminate` si une date manque ; `incompatible` dans tous les autres cas. Énoncé descriptif, jamais présenté comme une preuve.

**E.5 Contrepartie au client.** `supported` si le fournisseur publie une contrepartie payable au client comptabilisée en réduction du revenu, ou un revenu contre une contrepartie non monétaire reçue de lui ; `indeterminate` sinon, y compris quand le fournisseur ne publie rien sur ce point ; jamais `refuted`. Énoncé unilatéral : l'absence de publication ne réfute rien.

**E.6 Cycles** (descriptif). Décompte des `documented_path` par valeur de `temporal` et par conclusion ; issue unique `descriptive`.

**E.7 Non-discrimination** (règle). Si plus de 70 % des issues de paire de E.1 et de E.2 réunies sont `indeterminate`, au point de tête de la grille, le résultat principal publié est : « les pièces déposées ne permettent pas de discriminer entre les deux lectures ». Il est publié avec ce taux et la ventilation de ses motifs, dont `anonymous`, `channel_indirect`, `non_filer`, `redacted`, `not_processed` et `parse_failed`. C'est un résultat, pas un échec.

**E.8 Agrégation** (règle). Aucune règle « au moins une paire » ne fonde une conclusion globale ; les résultats se publient paire par paire, avec la part des paires dans chaque issue.

**E.9 Engagements de rendu** (règle). Un numérateur vide est publié `not_determinable`, avec `named_edge_coverage`, `documented_pair_coverage` et `customer_concentration_anonymous` à côté. Les énoncés E.1 à E.3 portent leurs deux directions dans leurs issues : `supported` pour la lecture circulaire, `refuted` ou `not_supported` pour l'autre lecture ; il n'y a pas d'énoncé miroir séparé. E.5 est unilatéral ; E.4 et E.6 sont descriptifs.



## Annexe F — Événements de fragilité

**Statut.** Cette liste est écrite avant toute exécution, pour la même raison que l'annexe E : choisie après avoir vu les séries, elle retiendrait ce qui monte. Elle est transcrite dans `config.yaml` et commitée avec les critères de l'annexe E, avant la première requête (§11.1) ; tout changement ultérieur est signalé en tête de la note de synthèse, avec le diff et les événements sous la liste d'origine. La liste est fermée. Chaque événement est un observable daté, publié avec sa pièce, sans pondération ni total et jamais résumé en un score : deux événements ne pèsent pas le double d'un seul, et c'est le lecteur qui juge ce qu'ils disent ensemble.

**Publication.** Chaque événement est une cellule de `measures` (`fragility_event`, l'identifiant de l'observable dans `breakdown_key`), qui porte la période concernée et la date où sa pièce l'a rendu public (`knowledge_date`, §7.3), car c'est cet écart que rappelle §1. Comme pour les signaux (§4.5), l'univers attendu (§7.5) donne à chaque groupe, observable et trimestre une cellule dont l'état de couverture dit si la source a été lue : une source non lue ne passe jamais pour un trimestre sans événement. Aucune somme de ces cellules, ni entre observables, ni entre groupes, ni dans le temps.

| Identifiant | Observable | Source |
| --- | --- | --- |
| `F1` | capex décaissé supérieur au CFO deux trimestres de suite | termes de `capex_to_cfo`, `term = without` (§6.2) |
| `F2` | `fcf_after_counterparty_financing` négatif | §4.4 |
| `F3` | un backstop ou une garantie dont `trigger_occurred = yes` | §5.3 |
| `F4` | un amendement ou une dérogation de clause financière | `sig_covenant_events` (§4.5) |
| `F5` | une faiblesse significative du contrôle interne | `sig_material_weakness` (§4.5) |
| `F6` | une dépréciation d'investissement | `investment_impairment` (§6.2) |
| `F7` | une baisse d'une durée d'amortissement publiée | `depreciation_life_published` (§6.2) |
| `F8` | un `revenue_growth` en glissement annuel qui passe sous zéro | `revenue_growth`, `term = yoy` (§4.2) |
| `F9` | un item 1.02 de 8-K sur un contrat de capacité | section 1.02 lue en phase 2 (§11.1) |
| `F10` | un doute sur la continuité d'exploitation | `sig_going_concern` (§4.5) |