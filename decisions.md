# Décisions techniques

Chaque décision non triviale, en une ou deux phrases, avec sa source et un identifiant (§11.2).
Ce fichier ne va pas à l'auditeur (§12.2).

## Exécution du 2026-10-07 (as_of 2026-10-07)

- **D-0001 — User-Agent masqué dans le dépôt.** L'utilisateur a fourni le User-Agent le 2026-10-07. Le dépôt `jsiaut/claude_code_test` étant public, `config.yaml` porte le nom (`SEC_rapport_test`) et une adresse masquée ; la valeur exacte vit dans `secrets/user_agent.txt` (non versionné) ou `SEC_USER_AGENT`. Source : §9.5 (« l'adresse de contact est masquée dans toute copie partagée »).
- **D-0002 — Réseau refusé par l'environnement.** La première requête (company_tickers.json, 10:56:41 UTC) a été refusée au CONNECT par le proxy de l'environnement, ainsi que trois tests de joignabilité (curl -I, sans User-Agent) vers `xbrl.fasb.org`, `data.sec.gov` et `xbrl.sec.gov` : aucune n'a atteint un hôte de la SEC. Les quatre lignes sont au journal (`proxy_error`, `proxy_connect_rejected`). L'utilisateur a ouvert l'accès dans les réglages de l'environnement ; la première requête aboutie est company_tickers.json à 11:11:00 UTC.
- **D-0003 — Verrou de session.** Le verrou `work/session.lock` porte l'identifiant de la session, pas celui d'un processus : les commandes successives d'une même session le partagent ; une autre session le trouve vivant tant qu'il a été touché depuis moins de `session_stale_minutes`. Source : §11.5.
- **D-0004 — Annexe F, lecture de F7 et F8.** « Passe sous zéro » (F8) est lu comme une transition : valeur en glissement annuel < 0 alors que celle de la période précédente est ≥ 0. « Baisse d'une durée » (F7) : une borne publiée de la durée d'une classe de même libellé inférieure à celle de la publication précédente. Ces lectures sont transcrites dans `config.yaml` avant toute requête (commit 3ff3b98).
- **D-0005 — Candidats des grandeurs non ancrées.** Pour les grandeurs de `unanchored_quantities` et quelques grandeurs auxiliaires (échéancier des obligations d'achat, durées d'utilité, concentration), la liste des concepts standard dont la définition correspond est fixée dans `pipeline/quantities.py` avant tout contrôle, vérifiée contre `us-gaap-2026.xsd` (17 182 éléments) ; six candidats initiaux absents de la taxonomie 2026 ont été remplacés par leurs équivalents présents (ex. `PurchaseObligationDueInNextTwelveMonths`), et les variantes « rolling » des obligations d'achat ajoutées. Source : §8.3, annexe B.
- **D-0006 — Ancres vérifiées.** Tous les noms locaux de `concept_anchors` et `concept_anchors_to_verify` figurent dans `us-gaap-2026.xsd` (tiré de `xbrl.fasb.org` le 2026-10-07), dont `SubstantialDoubtAboutGoingConcernTextBlock` (type `textBlockItemType`) ; `NatureOfOperations` est aussi un `textBlockItemType`, ce qui confirme qu'un bloc de note se reconnaît par son type et son rôle, pas par le suffixe `TextBlock` (§9.2, annexe D).
- **D-0007 — Baux non commencés.** La taxonomie 2026 n'a pas de concept monétaire standard pour le montant des baux non commencés ; elle offre les membres `OperatingLeaseLeaseNotYetCommencedMember` et `FinancingLeaseLeaseNotYetCommencedMember`. Le pont `lease_not_commenced_bridge` se lit donc sur des faits dimensionnés par ces membres, ou sur une extension rattachée par la règle de §8.3 ; à défaut, `not_determinable` (`concept_unresolved`).
- **D-0008 — Ordre de la file de lecture.** Classe (1) de §11.1 (parties liées, Item 404, Item 9A, Item 4, continuité d'exploitation) avant la classe (2) (8-K et pièces), chacune du plus récent au plus ancien. Source : §11.1 (numérotation des classes et « du plus récent au plus ancien »).
- **D-0009 — Doublons cohérents.** Deux faits d'une même identité dans un même dépôt ne sont `conflicting` que si leur écart dépasse la somme des tolérances d'arrondi de leurs précisions (ex. 4 784 M$ à `decimals=-6` et « 4,8 milliards » à `decimals=-8` sont cohérents) ; la vue retient alors le plus précis. Le saut d'un facteur 100 ne se compare qu'entre périodes successives de même longueur. Source : §7.3, §8.3 (tolérance d'arrondi).
- **D-0010 — D1 retenue.** Les états annuels du 424B4 de SpaceX (0001628280-26-042639, tableaux 58, 59, 62) sont lus en HTML ; chaque ligne prend le concept du 10-Q (0001628280-26-052535) dont le libellé correspond, la valeur ne servant qu'à vérifier. Deux règles d'appariement : « income (loss) » équivaut à « loss » (le 10-Q, en perte, libelle « Loss from operations ») ; un concept présenté avec un libellé `negated` dans l'état du 10-Q prend le signe opposé à celui affiché. Vérifications : 28 lignes du bilan au 2025-12-31 identiques au comparatif du 10-Q, C1 (actif courant, actif) et C6 (résultat net = première ligne du tableau des flux) sans écart sur 2023-2025. Aucun écart inexpliqué : la série annuelle est retenue, `is_tagged = false` jusque dans les rendus ; elle sera remplacée par le premier 10-K balisé. Knowledge date : dépôt du 424B4 (2026-06-12), prudente par rapport au S-1 public du 2026-05-20.
- **D-0011 — Appartenances SpaceX (D2).** Sources : 424B4, note 1, et 10-Q, note 1. `legal_date` : X.AI Holdings Corp. entre dans le groupe SpaceX le 2026-02-02 ; X Holdings Corp. et X.AI Corp. entrent dans xAI le 2025-03-28, donc dans le groupe SpaceX le 2026-02-02 ; X Corp. et X.AI LLC suivent leurs sociétés mères. `common_control_start` : 2023-01-01, début de la première période présentée, les états étant « retrospectively recast for all periods presented » et M. Musk contrôlant les trois entités « during the periods presented ». CTC Property, LLC : filiale consolidée attestée par la note de dette du 10-Q (garant du prêt-relais) au 2026-06-30, date d'entrée non établie.
- **D-0012 — Second candidat de `capex_cash`.** NVIDIA (depuis fin 2020) et Amazon présentent leurs investissements sous `us-gaap:PaymentsToAcquireProductiveAssets` (« purchases of and capital improvements on property, plant and equipment (capital expenditures), software, and other intangible assets »), absent des ancres : la grandeur était `concept_unresolved` pour deux groupes majeurs. Ce concept est la ligne de capex de leur tableau des flux et sa définition correspond, en plus large ; il est ajouté en second candidat dans `config.yaml` (le premier reste prioritaire), avant tout calcul de contrôle, et chaque cellule qui l'utilise porte `capex_definition = productive_assets_incl_intangibles`. Changement de configuration hors critères des annexes E et F et hors seuils.
- **D-0013 — Rôles « - Unaudited ».** Un rôle « Condensed Consolidated Statements of Cash Flows - Unaudited » n'était pas reconnu comme tableau des flux (le titre était lu sur le dernier segment). Le titre se lit désormais sur tous les segments qui suivent la catégorie. Correction de code, sans effet sur une règle.
- **D-0014 — Lots de petits blocs.** Un bloc de plus de 4 000 caractères est servi seul (en morceaux de 80 000 caractères au plus) et ses lignes sont rendues avant le bloc suivant. Les blocs plus courts (Item 4 d'un 10-Q, Item 9A, 8-K « 8.01 » de dividende…) peuvent être servis par lot de 20 000 caractères au plus ; les lignes de chaque bloc sont validées et écrites dans le fichier du bloc, bloc par bloc dans l'ordre de lecture, au sein d'un même appel. La perte maximale sur interruption reste de l'ordre d'un bloc moyen ; le gain est d'éviter plusieurs centaines d'allers-retours pour des blocs de quelques lignes. Source : §7.4 (un lot est une file de blocs jusqu'au plafond de lecture ; un fichier par bloc).
- **D-0015 — Payeur et receveur d'une ligne.** `payer` est la partie qui fournit la ressource et `payee` celle qui la reçoit, au sens de l'orientation des arêtes de §3.1 : client → fournisseur pour un achat, financeur → financé pour un financement (bailleur → preneur pour une `lease_financing`), garant → obligé pour un soutien de crédit, fournisseur → client pour une contrepartie au client. Un paiement en sens inverse sur un instrument déjà décrit (loyer, remboursement, intérêts) suit le sens de la trésorerie et ne porte ni `family` ni `edge_type`, donc n'ouvre pas d'arête ; il garde `instrument_key`. Source : §3.1, §7.4 (« sinon l'orientation d'une arête se devinerait »).
- **D-0016 — Délimitation `d3` de l'Item 404.** Trois défauts de `d2`, vus en lecture : une entrée de sommaire (titre suivi de son numéro de page) ouvrait la section (Marvell 2022-2026, Amazon 2020-2021, Broadcom 2026, Alphabet 2020) ; une puce qui commence par « Director compensation. » la fermait ; une mise en page où chaque page est une seule ligne (Alphabet 2020) n'avait aucun titre court. `d3` écarte les entrées de sommaire, n'accepte comme titre de fin qu'une ligne marquée titre ou sans phrase, ferme sur « Additional Meeting Information », et, faute de titre court, ouvre et ferme sur les lignes qui commencent par un titre. La clé de contenu ne dépend que du texte : seuls les blocs dont le texte change reçoivent une clé nouvelle et reviennent dans la file ; aucun bloc déjà lu n'est touché. Source : §7.4, §11.4.
- **D-0017 — Affichage des faits candidats.** Le lecteur n'affiche que les faits candidats dont la valeur paraît dans le texte du bloc (à son échelle : unités, milliers, millions, milliards, pourcentages), avec le compte des faits masqués, et les membres de dimension par leur libellé. Le catalogue, la clé de contenu et la validation sémantique gardent tous les faits : un montant lu dans le texte ne peut égaler qu'un fait dont la valeur y paraît, si bien que le filtre ne cache aucun rapprochement possible ; il retire de la lecture des dizaines de faits de dette sans rapport avec le texte (notes de CoreWeave). Source : §7.4 (le bloc est servi avec les faits candidats qu'il contient), P6.
- **D-0018 — Dates d'appartenance de CTC Property, LLC à SpaceX.** Le 424B4 de SpaceX (note 9) dit « CTC » filiale à 100 % et présente des états annuels audités recomposés sous contrôle commun. L'appartenance de CTC Property, LLC au groupe SPCX porte donc deux dates : la date juridique de la combinaison (2 février 2026) en vue `as_known`, et le début du contrôle commun (1er janvier 2023, premier exercice des états recomposés) en vue `revised`. Avant la date juridique, une arête entre CTC et un tiers reste externe en vue `as_known` ; en vue `revised`, elle est intragroupe dès le 1er janvier 2023. Source : §10 (« une combinaison sous contrôle commun porte deux dates »), §7.2.
- **D-0019 — Le fonds MAIV est consolidé par CoreWeave.** Le 10-K 2025 de CoreWeave dit consolider le fonds géré par Magnetar (« The Company consolidated the fund », modèle des droits de vote). MAIV devient une filiale consolidée du groupe CRWV : ses arêtes avec CoreWeave sont intragroupe et éliminées, et seuls les apports de Magnetar et des autres investisseurs au fonds sont des financements externes du groupe. Source : §10 (périmètre par consolidation publiée), §3.1 (éliminations intragroupe).
- **D-0020 — Corrections dans la passe, avant l'assemblage.** La validation sémantique de `load.py` (citation mot pour mot, contrepartie présente dans le bloc, montant balisé) a été appliquée aux 1 824 lignes à la fin de la lecture ; 13 lignes de la passe `2026-10-07T10:54:00Z` ont été corrigées en place, la passe n'étant pas close : contrepartie « Tesla, Inc. » ramenée à « Tesla » comme écrit dans le 424B4 de SpaceX (7 lignes) ; total des achats des sociétés liées à M. Ellison (DEF 14A 2025 d'Oracle) passé en contrepartie anonyme, les lignes par société portant les arêtes ; titre de pièce inventé retiré d'une lettre d'administratrice d'Alphabet ; quatre ventes de Broadcom à des entités liées (2018) passées en `tagged_reference` sur leur fait `RevenueFromRelatedParties`. La relecture AMD (100 M$) était déjà conforme. File de lecture vide : 1 133 blocs lus sur 1 350 clés de contenu ; les 217 corps de pièces restants n'ont que des établissements financiers pour parties non déposantes (exclusion `financial_parties_only`). Source : §7.4, §11.1.
- **D-0021 — Entités confirmées par un extrait.** Une filiale, une entité propre ou un alias n'entre dans le registre que sur un extrait cité mot pour mot qui affirme l'identité ou l'appartenance (« wholly-owned subsidiary », « merged with and into the Company », « the Company consolidated the fund ») ; chaque entrée de `config.yaml` (`confirmed_entities`, `entity_aliases`, `own_entities`) porte la décision, l'accession, le bloc et la citation, et la table `entities` les reprend en preuve. Avant la date d'entrée publiée (Xilinx le 14 février 2022, Inphi le 20 avril 2021, MAIV le 31 décembre 2025), l'entité forme son propre groupe ; hors de toute appartenance datée, de même. Aucune fusion sur une ressemblance de nom. Source : §10.2.
- **D-0022 — Dénomination légale complète.** Une contrepartie nommée dans une pièce déposée par sa dénomination légale complète (suffixe de forme juridique : Inc., LLC, Ltd., PBC…) est une entité et un groupe économique propres (`CP:<nom normalisé>`), sans fusion avec aucune autre dénomination tant qu'aucun extrait ne l'affirme ; toute autre mention (nom commercial, abréviation) reste `pending` : visible dans les tables, absente des agrégats, comptée dans les exclusions (`pending_entity`). Source : §10.2 (« on ne fusionne que sur un CIK ou une identité affirmée par un document »).
- **D-0023 — Contrôles par vue.** Un contrôle se calcule dans chaque dépôt qui publie la période (le comparatif d'un 10-K repasse le contrôle de l'exercice précédent). Il s'écrit une fois par vue : `as_known` lit le premier dépôt qui a publié la période, `revised` le dernier connu à la date `as_of` ; les statuts obtenus dans les autres dépôts restent dans les preuves (`filings_tested`), si bien qu'un écart vu dans un comparatif n'est pas effacé. Les contrôles de correspondance de C1 et C2 portent la date de fin de la période du dépôt. Correction de code : un instant portait une date de début `NaT` au lieu de `none`, ce qui privait C3 et C9 de toute valeur ; corrigé avant tout rendu. Source : §8.3, §7.3.
- **D-0024 — C8, C11 et C12.** C8 compare la variation de la valeur comptable de la dette rattachée (annexe B) aux émissions moins remboursements du même exercice dans chaque 10-K ; le résidu se publie en `mismatch` nommé (`residual_noncash_or_untagged_flows` : décotes, frais d'émission, change, acquisitions, conversions, billets de trésorerie nets), jamais équilibré. C11 et C12 lisent les membres d'un axe dans la linkbase de présentation du dépôt, rôle par rôle : seuls les membres de premier niveau d'un tableau se somment (un membre imbriqué est une composante de son parent, et deux tableaux sur un même axe sont deux ventilations). Les clients majeurs ne sont pas une ventilation du revenu. Source : §8.3.
- **D-0025 — Concentration : un seul dépôt par période.** Les libellés des clients anonymes sont propres à un dépôt : le « Customer A » du 10-K de l'exercice 2025 de NVIDIA devient « Customer One » dans le comparatif du 10-K suivant. Les parts de clients anonymes d'une période se lisent donc dans le seul premier dépôt qui l'a publiée (vue `as_known`), jamais en mêlant deux dépôts, ce qui comptait deux fois les mêmes clients. Source : §3.6, §7.3.
- **D-0026 — Trimestres d'un exercice en cours et dates des clés.** Un exercice en cours ne liste que les trimestres déposés : le premier 10-Q de SpaceX couvre six mois, et le trimestre clos le 30 juin 2026 commençait le 1er janvier. Les fins de trimestre manquantes avant la dernière déposée se déduisent de l'exercice précédent (même décalage depuis le début d'exercice) ; le trimestre déduit est `synthetic` et ses valeurs restent indéterminées faute de pièce. Correction de code : les dates des clés de `measures` et de `controls` s'écrivent toujours `AAAA-MM-JJ` (une heure accolée empêchait de rapprocher les parts de clients du revenu et les durées d'amortissement d'un exercice à l'autre). Source : §7.3, §7.5.

## Extension (§14), décidée le 2026-10-07

- **D-0027 — Blocs ouverts : `lender` et `text`.** Réponse de l'utilisateur à la seconde page (« prêteurs et texte »), le 2026-10-07, après le rendement présenté dans `user_brief_2.md` et `delta.md` (commit 9210738) : `scope: [lender, text]` dans `config.yaml`, avec la date, la décision et le rendement présenté. Ordre d'exécution : `lender` puis `text`, comme le recommande §14 ; le rendement se mesure de nouveau après chaque bloc. `discovery`, `form_d`, `paths`, `foreign` et l'ajout de groupes restent fermés. Source : §11.1, §14.
- **D-0028 — Bloc `lender` : sources et règles.** Les 21 archives des BDC Data Sets publiées au 2026-10-07 (2022 T4 à 2025 T4 par trimestre, puis mensuelles de janvier à août 2026, toutes dans leur rafraîchissement de septembre 2026 ; 514 Mo) sont en cache avec leur empreinte. Les colonnes du fichier `soi` suivent les libellés de la table `tag`, qui changent avec la version de la taxonomie (us-gaap/2026 libelle `InvestmentOwnedAtCost` « Adjusted cost basis ») : coût et juste valeur d'un même fonds y tombent sous deux colonnes. Les positions se lisent donc dans `num` (nom du concept, segment `InvestmentIdentifierAxis`), de la même archive. Rattachement : une position appartient à une entité du registre seulement si son identifiant contient la dénomination légale entière de l'entité (suffixe de forme juridique, D-0022) et qu'aucune autre dénomination légale ne la suit avant la description de l'instrument (« Oracle Corp Yucca Growth Infrastructure, LLC » désigne Yucca) ; sinon `pending_entity`. Les lignes « Total » des portefeuilles sont des sous-totaux, écartés (`invalid_aggregate`). Vue `as_known` : les faits à la date du bilan du dépôt, le premier dépôt d'un fonds pour une date l'emportant. Un instrument se classe prêt, titre de capital ou non classé d'après son libellé : juste valeur ÷ coût d'une action n'est pas un signal de crédit. Taux PIK et statut de performance ne sont jamais déduits d'une absence (`not_tagged`). Trois véhicules de CoreWeave (CCAC V, CoreWeave Financing DDTL V et DDTL V-V) sont confirmés filiales par leurs 8-K (D-0021) ; VMware reste un groupe propre tant que l'achèvement de son acquisition par Broadcom (8-K item 2.01, bloc `text`) n'est pas lu. Source : §14, annexe D, §10.2.
- **D-0029 — Lecture du bloc `text`.** Catalogue recalculé depuis le cache (`pipeline/text_catalog.py`) : notes d'investissements, de dette, de baux et d'engagements des rapports périodiques, repérées par la définition de leur rôle (§9.2) ; paragraphes des notes qui portent les faits de concentration et parlent de clients ; sections des items 2.01 et 2.03 des 8-K (11 documents principaux tirés, au journal) ; notes des immobilisations et paragraphes des estimations, repérés par leur concept standard (leviers de §6.1) ; corps des EX-10 et EX-4 arrêtés à leur en-tête au premier passage. Ordre : paragraphes des clients, notes d'investissements, items de 8-K, dette, baux, engagements, leviers, puis corps de pièces ; dans chaque classe, du plus récent au plus ancien, si bien qu'à l'arrêt ce qui reste `not_processed` est le plus ancien. Passe `2026-10-07T16:30:00Z`. La file est découpée en lots disjoints (`work/lists/`), lus en parallèle par des sous-agents de l'exécutant selon un même guide (`work/guide_lecture_text.md`), avec le même lecteur et les mêmes validations de schéma et de sémantique, désormais appliquées dès la remise (une reprise, puis `--final`). Source : §7.4, §11.1, §14.
- **D-0030 — Bloc `text` : corrections du validateur, relecture ciblée, VMware.** Quatre corrections faites pendant la lecture, sur des difficultés que les lecteurs ont rapportées. (1) Les montants se comparent aux faits candidats en valeur absolue : une perte balisée en négatif reste le même fait, et le lecteur écrit le montant positif. Dix lignes `narrative_only` de la première passe (cinq notes d'investissements de MSFT et NVDA) égalent désormais un fait candidat. Elles sont relues dans une passe propre, `2026-10-07T17:00:00Z` (liste `repass_01`, fichier de passe par liste), qui remplace la précédente pour ces blocs. (2) L'affichage des faits candidats tient compte de l'échelle d'un tableau (« in millions ») : un nombre nu y vaut aussi à l'échelle déclarée. Avant cette correction, le validateur exigeait la clé d'un fait qui n'était pas affiché. (3) Une contrepartie tirée d'un libellé de membre se compare en texte normalisé, apostrophes typographiques comprises. (4) L'identifiant de groupe que le lecteur écrit pour le déclarant (« META », « AMD ») se rattache au groupe déclarant, comme « we », et n'est jamais une contrepartie. Par ailleurs, VMware, Inc. est filiale d'AVGO à compter du 22 novembre 2023, d'après l'item 2.01 du 8-K d'achèvement lu dans ce bloc (extrait cité dans `config.yaml`, D-0021). Avant cette date, VMware forme son propre groupe. Source : §7.4, §10.2.
- **D-0031 — Bloc `text` : corps de pièces, leviers et notes de revenu.** §14 rouvre les corps des EX-10 arrêtés à leur en-tête au premier passage, c'est-à-dire les clauses des contrats d'origine entre établissements financiers. Il ne rouvre pas les corps des EX-4. D-0029 avait mis les deux dans le catalogue : c'est corrigé avant toute lecture de pièce. Les 165 corps d'EX-4 arrêtés à leur en-tête (actes d'émission dont le fiduciaire est le seul porteur non déposant) restent exclus avec leur motif, `financial_parties_only`. Les 52 corps d'EX-10 (12,1 millions de caractères) forment 38 lots, du plus récent au plus ancien (`work/lists/x10_*`). Le guide fixe la forme des lignes de levier : un changement de durée d'utilité s'écrit `measurement_change`, l'effet publié en montant positif, et sa note commence par « effet : ± résultat opérationnel », « effet : ± dotations » ou « effet : ± résultat net ». Seuls les deux premiers retraitent le résultat opérationnel de la même période (§6.4). Un effet net d'impôt est gardé mais jamais retraité. Il fixe aussi la forme des lignes des notes de revenu : contrepartie payable à un client nommé (`consideration_payable_to_customer`) et contrepartie non monétaire reçue d'un client nommé (`noncash_consideration_received`). Source : §14, §11.1, §6.1, §6.4, §3.3.
- **D-0032 — Bloc `text` : corrections nées de la lecture, corps d'EX-10, Maui HoldCo.** Les points qui suivent ont été réglés pendant la lecture, sur des difficultés rapportées par les lecteurs ou vues au réassemblage. (1) Validateur : une ligne `narrative_only` n'est refusée que si un fait balisé candidat a la même valeur à la même date (même fin de période ; pour un événement, une date comprise dans la période du fait ou égale à sa fin). La même valeur à une autre date est un autre fait : la ligne reste narrative. (2) Leviers de durée d'utilité : par groupe, période et instrument, l'effet sur le résultat opérationnel l'emporte. À défaut, les effets sur les dotations sont additionnés par parts distinctes (coût des ventes, charges opérationnelles), chacune comptée une fois : le même effet relu dans un dépôt ultérieur ne compte pas deux fois. Les clés d'instrument écrites par des lots différents ne sont pas toujours les mêmes pour un même changement (MSFT, exercice 2021 : `msft:server_life_fy2021` dans les 10-Q d'octobre 2020 et janvier 2021, `msft:server_life_2020` ensuite). Chaque période n'a qu'une clé, donc aucun effet n'est compté deux fois ; seule l'étiquette de ventilation change d'une période à l'autre. (3) Sûretés : une sûreté qui ne joue que sur un déclencheur non survenu (dépôt en espèces exigé seulement si un prêteur fait défaut, ou après un cas de défaut) n'entre pas dans `sig_pledged_assets`. (4) Contrepartie payable à un client : seuls les flux (une période avec un début, une base autre que la valeur au bilan) entrent dans la mesure ; un solde de réduction du revenu à une date n'est pas un flux. (5) Entités : un nom qui commence par un article ou un déterminant (« an affiliate of OpenAI Group PBC ») ou qui contient « affiliate of », « subsidiary of », « on behalf of » reste pending même s'il finit par un suffixe de forme juridique ; D-0022 ne s'applique qu'à une dénomination. (6) Baux signés non commencés : seules les lignes à date écrite comptent. Deux lignes à la même date ne s'additionnent que si elles sont complémentaires (financement et exploitation, long et court terme) ; sinon la cellule reste partielle. (7) Corps d'EX-10 : une clause financière s'écrit en observation sans montant ni signal, son niveau dans `note` (le schéma n'a pas de champ de ratio) ; une partie non bancaire sans engagement chiffré (vendeur d'actifs, véhicule de fusion, prestataire) s'écrit sans famille et ne fait donc pas d'arête ; une garantie ou une sûreté conditionnelle le dit dans `conditionality`. Une lettre d'engagement et le contrat définitif qui la suit gardent chacun leur ligne d'instrument : aucune mesure n'additionne les plafonds d'engagement d'établissements financiers, qui ne font qu'augmenter le décompte des arêtes. (8) « Maui HoldCo, Inc. » est un alias de Marvell Technology, Inc. (cik 0001835632), d'après l'EX-4.1 du 8-K 0001193125-21-123305 : « Marvell Technology, Inc. (f/k/a Maui HoldCo, Inc.), a Delaware corporation ("Marvell Technology") » (extrait cité dans `config.yaml`, D-0021). Les contrats de 2020 où il est emprunteur se rattachent donc à MRVL. (9) Deux interruptions pour limite d'usage ont coupé des lecteurs au milieu d'un contrat. Leur reprise part de l'état du lecteur (morceau suivant à servir), du fichier de lignes déjà écrit et des morceaux enregistrés ; rien n'est soumis avant la lecture du dernier morceau. Au début de la lecture, des lecteurs simultanés ont enregistré des morceaux sous les mêmes noms génériques. Les citations sont vérifiées contre le bloc soumis, et aucun rejet n'est enregistré : aucune ligne tirée d'un autre bloc n'est entrée. Une omission dans un bloc touché ne se détecte pas, en revanche. Depuis, les fichiers de travail sont nommés par lot. Source : §7.4, §10.2, §14, §6.4, §11.1.
- **D-0033 — Bloc `text` lu en entier : motifs de couverture, statut `never`, exposition par contrepartie.** Le texte d'un groupe est lu en entier quand le bloc `text` est ouvert et qu'aucun bloc du catalogue de ce groupe n'attend de lecture ; les corps exclus avec leur motif (EX-4, `financial_parties_only`) ne comptent pas. Pour un tel groupe, `not_processed` ne se publie plus : chaque cellule dit ce qui manque vraiment, pour que la ventilation des motifs dise ce qu'une extension peut encore changer (§11.1, E.7). (1) Statut « financé » (§3.2, E.0) : F vaut `never` là où rien n'a jamais tenu et où la recherche est complète. La recherche est complète quand tout le texte du fournisseur est lu, que le client est un groupe du périmètre au texte lu ou un laboratoire non déposant (§10.4), qu'aucune archive de la fenêtre de rétrospection n'est illisible et qu'aucune clause d'un contrat de la paire n'est caviardée. Sinon F reste `unknown`, avec son motif : `search_incomplete` pour un client qui peut déposer hors du périmètre, tant que la découverte (§14) n'est pas ouverte ; `parse_failed` (le 10-K/A 2018 d'Alphabet, sans instance, jusqu'à huit trimestres après sa période) ; `redacted`. L'historique tronqué de CoreWeave est inchangé. Le rendu dit « jamais documenté » : `never` est un constat sur les pièces lues, pas sur les faits. (2) Un exercice sans trimestre actif après une recherche complète laisse `documented_revenue_dependency` indéterminée, motif `precondition_not_met`, jamais 0 % (§3.5) : E.2 y reste `indeterminate`. Une paire sans pièce L1 à L5 a pour lien `searched_none_found` si la recherche est complète, et E.1 y vaut alors `not_supported`. Sinon le lien reste `search_incomplete`, avec son motif. (3) Signaux lus dans la note de dette : un trimestre sans rapport périodique (CoreWeave et SpaceX avant leur introduction en bourse) ou dont le rapport n'a pas de note de dette (des 10-Q d'Oracle, Meta avant sa première émission de 2022) est `not_disclosed`. Il n'est plus « pas encore lu ». F3 est calculé une fois les notes d'engagements lues. F2 suit le flux après financement des contreparties, calculé une fois le texte lu ; sa date de connaissance est celle du flux libre dont il se calcule, ou celle du dernier financement retenu si elle est postérieure. `named_edge_coverage` est calculée : le texte de concentration est lu, et tous ses clients y sont anonymes. E.5 prend le motif `not_disclosed`. (4) `counterparty_exposure` : au coût, seuls les apports s'additionnent, jamais un gain ou une perte de mise en équivalence ni une valeur au bilan. Un plafond d'engagement, une valeur au bilan ou une garantie est un état : la dernière valeur connue à la date, par instrument, la plus précise à date égale. Sans ligne retenue, la cellule dit qu'aucun montant n'a été relevé dans les dépôts lus, ce qui n'affirme pas que rien n'est publié. Cela corrige deux sommes. Les gains et pertes trimestriels de Microsoft sur OpenAI étaient additionnés comme une exposition. L'engagement d'Amazon envers OpenAI était compté deux fois : 35,0 Md$ à l'item 1.01 et 34 999 999 447,98 $ dans la pièce sont le même engagement. (5) Une clôture (remboursement, résiliation, conversion, cession, stade réglé ou résilié) suit le sens de la trésorerie (guide, §3) et ne fait plus naître seule une paire. Les paires où un groupe « finançait » sa banque ou son bailleur disparaissent : Broadcom → Bank of America, NVIDIA → Goldman Sachs, NVIDIA → Wachovia (§3.1). Source : §3.1, §3.2, §3.4, §3.5, §4.6, §10.4, §11.1, annexe E.
- **D-0034 — Audit de la lecture du bloc `text` après les interruptions.** La lecture a été faite par des lecteurs parallèles, coupés quatre fois par des limites d'usage, et ceux du début ont partagé des fichiers de travail aux mêmes noms. L'audit relit les journaux des 102 lecteurs et régénère chaque morceau tel qu'il a été servi. (1) Chaque ligne de texte des 1 781 blocs a été affichée à un lecteur de son lot, début et fin de ligne compris, à quatorze lignes près. Les 32 vues partielles de l'outil de lecture ont toutes été complétées. Douze lignes non vues sont une table des matières (EX-10, lot `x10_27`) et une un pied de page (`x10_12`). Les deux dernières sont un paragraphe sur le segment logiciel de Broadcom, qui ne nomme aucun client, et une ligne tronquée dont la phrase utile est citée (`conc_01`) : l'abstention de ce bloc reste juste. (2) Deux collisions réelles de fichiers ont eu lieu, et les deux lecteurs s'en sont aperçus. Dans `x10_10`, le morceau 4 du contrat CCAC VIII de CoreWeave a été écrasé ; ce morceau ne contient ni montant, ni ratio, ni contrepartie autre que l'emprunteur (cascade de trésorerie, déclarations, conditions préalables). Dans `debt_01`, le lecteur a relu son bloc dans un répertoire propre. (3) Les blocs coupés en cours de lecture ont été relus en entier à la reprise, sauf trois contrats EX-10 (`x10_31`, `x10_34`, `x10_37`). Pour ceux-là, les morceaux antérieurs ont été traités par le premier lecteur, et le lecteur de reprise a vérifié le dernier morceau et lu la suite. (4) La soumission en mode lot passait par un fichier temporaire commun à tous les lecteurs. Les lignes vérifiées correspondent toutes à leur bloc, mais le contrôle ne couvre que les lignes écrites hors script. Ce fichier est désormais propre à chaque liste. L'audit établit que le texte a été vu, pas que chaque ligne utile en a été extraite : cela reste la qualité ordinaire de la lecture. Aucune relecture ni aucun réassemblage n'en découle. Source : §7.4, §11.1, §11.4.
- **D-0035 — Tests unitaires de §8.4 et trois mesures de rang 2.** (1) `tests/test_spec_8_4.py` couvre les points de §8.4 en 35 cas : échelle (négatifs compris), signe, `decimals`, zéro fixe et valeur nulle ; normaliseur de texte (entités, espace insécable, nom coupé par une balise, constructions iXBRL, décodage) ; unités et devises ; identité sans version et trimestres choisis par dates, sans `fy` ni `fp` ; blocage d'une somme par un chevauchement ou par des devises mêlées ; déterminisme des identifiants ; `tier` ; vérification des citations. Lancement : `python3 -m unittest discover -s tests -t .`. Deux tests ont d'abord échoué, et c'est le code qui a été corrigé. (a) Dans les états HTML du 424B4 de SpaceX (D1, D-0010), un tiret était lu comme une absence ; c'est un zéro publié, l'équivalent de `ixt:fixed-zero`. L'extraction relancée depuis le cache donne 13 faits nouveaux, tous nuls et marqués `is_fixed_zero` (par exemple les remboursements de location-financement de 2023) ; aucune valeur existante ne change, et les 36 vérifications de D1 restent justes. (b) Une somme d'arêtes en devises mêlées recevait le motif « entité non confirmée ». Chaque invariant violé a maintenant son motif : `blocked_overlap` (d), `mixed_currency` (b), `pending_entity` (g), `precondition_not_met` (a, pièce de niveau E ou F). (2) `liq_cash_to_12m_outflows` (§4.3), en fin d'exercice. Numérateur : trésorerie et placements courants, soit le total balisé, soit la trésorerie plus la ligne de placements courants ; un groupe qui ne présente cette ligne dans aucun de ses bilans n'en a pas, et la trésorerie seule est complète. Avec (`with`) ou sans (`without`) les facilités confirmées non tirées. Dénominateur : principal de dette, loyers de location simple et de location-financement, obligations d'achat, tous à 12 mois ; aucune paire non additive du registre (§8.2) ne relie ces quatre termes. Un terme de sortie non balisé rend le ratio indéterminé, jamais complété par un zéro : des obligations d'achat publiées en texte seulement peuvent être très grandes. Deux grandeurs non ancrées sont ajoutées : `operating_lease_payments_12m` et `finance_lease_payments_12m`. Résultat : le ratio est calculé pour neuf exercices (Amazon 2021 à 2023, Broadcom 2021 à 2024, Oracle 2025 et 2026), sans les facilités seulement, aucun de ces groupes ne balisant le non-tiré sans dimension en fin d'exercice ; ailleurs un terme de sortie manque, le plus souvent les obligations d'achat ou les loyers de location-financement. (3) `segment_significant_expenses` (§4.2, ASU 2023-07) : chaque charge balisée sur `StatementBusinessSegmentsAxis` est une cellule par secteur, concept et période, jamais sommée ; les autres éléments sectoriels gardent leur concept. Les montants de restructuration cumulés ou attendus sont écartés, parce que ce ne sont pas des charges de la période. Un exercice ouvert après le 15 décembre 2023 sans charge sectorielle balisée vaut `not_tagged` : CoreWeave, secteur unique sans axe, et les comptes annuels de SpaceX, lus en HTML. Résultat : 2 200 cellules pour dix groupes, et quatre exercices `not_tagged`. (4) `supplier_concentration` : aucun des onze groupes ne balise de concentration de fournisseurs. Chaque exercice vaut `not_tagged` ; cela n'exclut pas un fournisseur nommé en texte seulement. (5) Déterminisme des rendus (§7.7) : des requêtes triées par effectif seul rangeaient les ex aequo au hasard (formulaires, pièces d'un événement de l'annexe F, termes d'un nombre dans `numbers.csv`). Elles sont départagées par leurs clés, et deux rendus successifs sont désormais identiques à l'octet près. Source : §3.6, §4.2, §4.3, §7.3, §7.6, §7.7, §8.4.

- **D-0036 — Bloc `discovery` : ouverture, sources, lexique, candidats, classement et file de lecture, fixés avant de voir les candidats.** (1) Réponse de l'utilisateur le 2026-10-09 (« On lance la partie découverte, sans sous-agent »), après le rendement de `delta.md` (commit 63323c4) : `scope: [lender, text, discovery]`, la décision et le rendement présenté dans `scope_history`. La lecture est séquentielle, par l'exécutant seul. (2) Notes Data Sets : les 47 archives qui couvrent les dépôts du 2017-01-01 au 2026-09-30, puisque la période de lecture la plus ancienne des groupes commence le 2017-01-29 (§11.1). Ce sont les archives trimestrielles 2017 T1 à 2025 T3 et les mensuelles d'octobre 2025 à septembre 2026. Elles sont tirées de la plus récente à la plus ancienne par le client unique. L'empreinte, la taille, la date `Last-Modified`, l'URL et l'heure de tirage de chaque archive vont dans `cache/datasets/notes/manifest.jsonl`. Faute de place (17,5 Go), une archive n'est pas gardée entière. Le scan en garde `sub` entier, les lignes de `txt` qui nomment un terme, puis `num`, `dim`, `pre`, `ren` et les balises propres des dépôts retenus. Il garde aussi la liste des valeurs de `txt` plus courtes que 90 % de `txtlen`, pour juger de la complétude du scan par déposant. Un lexique enrichi fait retirer les archives. (3) Lexique : le lexique initial de `config.yaml`, chaque terme avec sa cible et sa règle de casse. Meta, Amazon, Oracle, Alphabet, Anthropic, Stargate, xAI, X.AI et AMD sont sensibles à la casse, les autres non, et tous se prennent en mots entiers. Il ne s'enrichit que d'entités des groupes confirmées par le registre (§10.2), avec leurs dates : Facebook jusqu'au 2021-10-27, Xilinx depuis le 2022-02-14, VMware depuis le 2023-11-22, Inphi depuis le 2021-04-20, MAIV, CTC Property, X Corp, X Holdings Corp, Atlantic Crypto jusqu'au 2019-10-03 et Maui HoldCo. Version `lx-8d4520d34ab5`. (4) Mention : une ligne de `txt` d'une taxonomie de notes. Sont exclus les faits de couverture (`dei`), les informations sur les initiés (`ecd`), les droits de dépôt (`ffd`), la cybersécurité de l'Item 1C (`cyd`), les prospectus et facteurs de risque des fonds (`cef`, `oef`, `rr`, `vip`) et les listes de référence (§14 : jamais dans un facteur de risque). Les dépôts des groupes eux-mêmes sont exclus : leurs CIK, ceux de leurs prédécesseurs et des entités du registre qui leur appartiennent. Une occurrence qui fait partie de la dénomination du déposant, actuelle ou ancienne, n'est pas une mention : « Karbon-X Corp. » ne nomme pas X Corp. Un terme daté ne nomme le groupe que si la période du dépôt recoupe sa validité. Les EX-10 trouvés par la recherche plein texte sont tirés, et le code y applique les mêmes règles. Les Form D aussi, nom de l'émetteur compris : un véhicule nommé d'après un laboratoire est la mention que décrit §14. (5) Recherche plein texte : la phrase de chaque terme, du 2017-01-01 à `as_of`, sur les formulaires racines qui portent des EX-10 déposés (8-K, 10-K, 10-Q, S-1, S-4, S-11, F-1, F-4, 10-12B, 10-12G, 20-F, 40-F). Le 6-K est exclu, car furnished (§2.1). Puis `forms=D`. Une requête saturée se coupe en deux périodes jusqu'à passer sous 10 000 résultats. Chaque page est en cache sous `cache/search/{sha256}/` et chaque requête est consignée dans `work/discovery/efts_queries.jsonl`. (6) Candidat et classement (§14) : le candidat est le déposant (CIK). Clés de tri, dans l'ordre :
  - **classe de mention** : contrat (EX-10), puis parties liées (note dont la balise nomme des parties liées), puis note, puis Form D ;
  - **montant documenté**, décroissant : le plus grand montant en USD d'un fait de `num` des dépôts du candidat dont un membre de dimension nomme le groupe, hors de son propre nom, ou, pour un Form D, `totalAmountSold` du XML ; jamais une observation. Les candidats sans montant viennent après ;
  - **nombre de groupes nommés**, décroissant ;
  - **accession** de sa première mention de la meilleure classe, croissante.

  (7) Unité de lecture : les « notes structurantes » d'un candidat sont les notes qui nomment un groupe. Elles se lisent en entier, pas seulement autour du terme, car le filtre lexical manque les noms encore inconnus. La source est la page R du dépôt (note rendue par la SEC), mise en cache comme toute pièce d'archive et linéarisée par le normaliseur des autres blocs. Les faits candidats sont les faits de `num` présentés dans les pages de cette note (la note, ses tableaux, ses détails) dont la valeur paraît dans le texte. Un texte identique ne se lit qu'une fois (clé de contenu). Un EX-10 se lit par son en-tête (première page), comme au premier passage (§11.1) ; son corps seulement si un groupe en est partie, après toutes les notes. Un Form D ne se lit pas : son XML est structuré, son montant se lit par code, et il ne nomme jamais de contrepartie. (8) Ordre de la file :
  - (A) pour chaque candidat dans l'ordre du classement, ses en-têtes d'EX-10 et les notes de son dépôt le plus récent qui nomment un groupe ;
  - (B) puis, dans le même ordre, ses autres notes, du plus récent au plus ancien ;
  - (C) enfin, les corps d'EX-10 dont l'en-tête montre un groupe partie.

  L'étendue passe avant la profondeur : sous une limite, chaque candidat classé reçoit sa lecture la plus récente avant toute lecture plus ancienne. (9) Ce qui n'est pas lu est exclu (`not_processed`), et une paire dont le client a des blocs non lus garde `search_incomplete`. (10) Un déposant découvert est l'entité dont la dénomination légale normalisée égale sa dénomination EDGAR, actuelle ou ancienne (convention de D-0022), avec son CIK. Source : §2.1, §2.4, §9.6, §10.2, §11.1, §14, annexe D.
- **D-0037 — Recherche complète côté client (E.0) une fois la découverte ouverte.** E.0 demande que tous les dépôts du fournisseur et, s'il dépose, du client soient traités. Pour un client hors du périmètre, la découverte dit s'il dépose et ce qui reste à lire. (1) Un client est cherché par sa dénomination légale normalisée : d'abord parmi les déposants trouvés par la découverte, sinon dans la liste des noms d'EDGAR (`cik-lookup-data.txt`, tirée le 2026-10-09, §9.4). Sans CIK sous cette dénomination, il ne dépose pas : la recherche est complète de son côté, comme pour un laboratoire (§10.4). (2) Un CIK sans rapport périodique (10-K, 10-Q, 20-F, 40-F, leurs amendements et rapports de transition) depuis le début de la fenêtre allongée n'a pas de note à lire. Ses autres dépôts, Form D ou déclarations de détention, ne nomment pas les financeurs d'un émetteur ; la recherche est complète de son côté. (3) Un client qui dépose des rapports périodiques n'est complet que si toutes ses unités de lecture qui nomment le fournisseur sont lues : notes et en-têtes d'EX-10 de la file de D-0036. Sinon le motif est `not_processed`. (4) Tant qu'une archive des Notes Data Sets de la période n'est pas scannée, la recherche reste incomplète pour tout client hors périmètre (`search_incomplete`, §14). (5) Le statut F d'une paire peut alors valoir `never` (« jamais documenté ») sous une recherche complète, comme pour les paires entre groupes (D-0033). Source : §3.2, §10.4, §14, annexe E (E.0).
- **D-0038 — Première tranche de la découverte lue : alias de marque, désignation du déclarant, doubles comptes.** (1) Sur la décision de l'utilisateur « On lance la partie découverte, sans sous-agent », la file de D-0036 est lue dans son ordre, sans sous-agent, sur les 25 premiers candidats du classement : 190 blocs (191 unités, dont une note de Cipher présente deux fois sous la même clé de contenu), soit 177 observations et 97 abstentions. Le reste de la file (environ 19 000 unités) reste `not_processed`, et les clients concernés qui déposent des rapports périodiques gardent ce motif (D-0037, point 3). Les corps d'EX-10 (passe C) ne sont pas lus. (2) Alias de marque établis par un extrait cité mot pour mot (convention de D-0021) : Amazon → Amazon.com, Inc. ; Google → Google LLC ; Microsoft → Microsoft Corporation ; Facebook → Facebook, Inc. ; Broadcom → Broadcom Inc. ; Oracle → Oracle Corporation ; Marvell → Marvell Technology Group Ltd. ; SpaceX → Space Exploration Technologies Corp. Amazon Logistics, Inc. entre dans le groupe AMZN : le bloc la dit affiliée d'Amazon.com, Inc. Aucun extrait lu ne rattache « Google Inc. » à Alphabet, et EDGAR lui donne un autre CIK que Google LLC (0001288776 contre 0001824723). Elle reste donc un groupe propre (D-0022), comme « Amazon.com Services, LLC », prêteur de 1Life, faute d'extrait qui la rattache à Amazon.com, Inc. Les relations écrites sous ces deux dénominations sont donc sous-comptées pour GOOGL et AMZN. « Google Cloud » et « Fluidstack » restent `pending`. (3) Désignation du déclarant dans un bloc de découverte : « we » et « the Company » étaient comparés aux mots du déclarant sans normalisation, alors que la forme normalisée de « the Company » est « co ». Ils ne se rattachaient donc pas au déposant découvert. La comparaison se fait désormais sur la forme normalisée (`FILER_NORM`). Les lignes qui désignaient le déclarant par un nom court ou par une filiale consolidée (Mattel, Intel, Startek, AOI, « the Group », Cruise Holdings, Wulf Compute), ou une partie par un terme défini du bloc (Borrower, Lender, Holder, Customer, Partner), sont réécrites. Le déclarant et ses filiales consolidées deviennent « the Company », et un terme défini devient le nom qu'il désigne dans le même bloc. Les citations ne changent pas. Les 23 remplacements sont consignés dans `work/discovery/payer_payee_normalization.jsonl`, et le guide de lecture est complété. (4) Pas de double compte : chez IAC, le revenu tiré de Google par segment est une composante du revenu consolidé tiré de Google, relevé avec ses faits balisés. Les lignes par segment sont retirées au profit d'une abstention `duplicate_of_other_block`. (5) Pièces de lien relevées :
  - AAOI–Amazon : L1 (bons acquis selon les achats d'Amazon, seuil de 4 Md$) et L3 (contrepartie payable au client) ;
  - Rivian–Amazon : L5 (lettre commerciale conclue en contrepartie de la souscription de série A, qui engage à négocier l'accord sur les véhicules de livraison), `judgment_sensitive` ;
  - Cerebras–OpenAI : L1 (prêt de fonds de roulement lié au MRA et affecté à l'infrastructure qui sert OpenAI ; bons acquis selon le versement du prêt et la livraison de capacité), L3 (prêt et contrat évalués ensemble) et L5 (bon présenté comme une incitation aux achats), ce dernier `judgment_sensitive` ;
  - Cerebras–AWS : L1 (bons acquis selon les paiements d'AWS) ;
  - IREN–NVIDIA : L1 (droits d'investissement acquis selon les volumes de GPU livrés) et L3 (juste valeur incorporée au coût des GPU), `judgment_sensitive` ;
  - Startek–Amazon : L1 (bon acquis selon les paiements d'Amazon).

  (6) Limite : la date de début affichée pour un fait candidat se déduit de `qtrs` et `durp`, dont le sens exact n'est pas établi. Elle peut précéder de quelques jours le début réel de la période. Seule la date de fin sert à la règle de date du guide (§5), et elle se lit sans ambiguïté (`ddate` moins `datp`). Source : §2.4, §3.4, §7.4, §10.2, §14, annexe E.
- **D-0039 — Pièces de lien d'une paire : les parties de la ligne sont S et C ; alias « AMD » ; « the Group ».** (1) Défaut corrigé dans `link_pieces` (§3.4). Les noms de C recevaient la contrepartie nommée de toutes les arêtes de la paire, y compris celles que C dépose, qui nomment S. Toute ligne à catégorie de lien qui nommait S passait donc les deux tests de nom, quel que soit son déposant. Exemples :
  - la ligne d'IREN sur les droits accordés à NVIDIA et celle de NVIDIA sur le site de Portsmouth loué à OpenAI comptaient pour NVIDIA–CoreWeave ;
  - la ligne de Marvell sur le bon remis à Google comptait pour Alphabet–SpaceX, Alphabet–Cipher, Alphabet–Equifax, Alphabet–Snap et Alphabet–TeraWulf ;
  - les bons d'Applied Optoelectronics, de Startek et de Cerebras comptaient pour Amazon–Rivian, Amazon–1Life et Amazon–Snap.

  Le défaut précède la découverte : l'issue « étayé » de E.1 publiée pour NVIDIA–CoreWeave reposait sur la ligne de Portsmouth, qui ne nomme pas CoreWeave. (2) Règle : une ligne L1 à L5 est une pièce de la paire (S, C) à deux conditions. Ses parties (payeur, bénéficiaire, contrepartie nommée) comprennent S et C : elles sont résolues à la date de la ligne, dans l'une des deux vues, et « we » ou « the Company » désigne le déposant de la ligne. L'extrait nomme aussi les deux parties. Les noms de C pris aux arêtes viennent des seules lignes déposées par S, ceux de S des seules lignes déposées par C. Un test unitaire couvre ces cas (`tests/test_link_pieces.py`). (3) J'ai relu les lignes dont les parties sont exactement S et C mais dont l'extrait échouait au test de nom ; deux nomment bien les deux parties.
  - La ligne d'AMD « AMD issued to Meta a performance-based warrant… » nomme AMD par son nom court, absent du registre. L'alias « AMD » est établi par l'extrait « Advanced Micro Devices, Inc. ("AMD") » (8-K du 2026-02-23, item 1.01 ; convention de D-0021). Il rattache aussi au groupe AMD deux lignes d'AMD écrites « AMD ».
  - La ligne L3 d'IREN nomme le déclarant « the Group », désignation déjà relevée en D-0038. Elle compte désormais comme désignation du déposant.

  Les autres lignes nomment l'une des parties seulement par un terme défini du contrat (« Warrantholder », « the Customer », « the Holder »), ou pas du tout. Elles restent hors des pièces, puisque l'extrait doit nommer les deux parties. (4) Effets sur les paires :
  - AMD–Meta passe de « commercial avec financement » à « dépendance documentée » (L2 : bon de souscription acquis selon les achats de GPU, engagement d'achat de Meta) ;
  - NVIDIA–CoreWeave passe à « commercial avec financement » : la recherche est complète et ne trouve aucune pièce, et E.1 y devient « non étayé » ;
  - Alphabet–SpaceX, Alphabet–Cipher, Alphabet–Equifax, Alphabet–Snap, Alphabet–TeraWulf, Amazon–1Life et Amazon–Snap perdent des pièces qui n'étaient pas les leurs ;
  - NVIDIA–IREN garde L1 et L3, et Amazon–Rivian garde L5.
  - Des pièces relevées en D-0038 (point 5), seules celles de NVIDIA–IREN et d'Amazon–Rivian comptent pour une paire (S, C). Les autres lient Amazon à un fournisseur qui lui remet des bons (Applied Optoelectronics, Startek, Cerebras), sens qui ne forme pas de paire (§3.1), ou OpenAI à Cerebras, tous deux hors du périmètre.

  (5) E.1 n'a plus aucune paire « étayé » : 9 sont « non étayé » et 2 indéterminées. Pour Alphabet–SpaceX, une archive XBRL de la fenêtre est illisible (`parse_failed`). Pour Microsoft–General Motors, des unités de General Motors restent à lire (`not_processed`). Avec les 11 issues indéterminées de E.2, 13 issues sur 22 sont indéterminées (59 %). C'est sous le seuil de 70 % de E.7, d'où « discrimination possible ». Avant l'ouverture de la découverte, 15 issues sur 18 l'étaient (83 %). Le changement tient à D-0037 et non à la correction : six clients financés (Silicon Manufacturing Partners, MAIV, Jio Platforms, Ampere Computing LLC et Ampere Computing Holdings, Screening Room Media) n'ont pas de CIK sous leur dénomination. Ils ne déposent pas, leur côté de la recherche est complet (D-0037, point 1), et E.1 y passe d'« indéterminé » à « non étayé ». Les pièces fausses corrigées ici rendaient au contraire deux paires « étayé ». Source : §3.4, §10.2, annexe E (E.0, E.1, E.7).
- **D-0040 — Deuxième tranche de la découverte lue (rangs 26 à 50) : bons passés en charges, mentions fausses, litiges, filiale d'Amazon.** (1) Sur la réponse de l'utilisateur « oui continue », la file de D-0036 est lue dans son ordre, sans sous-agent : passe A, rangs 26 à 50, unités d'ordre 192 à 395. Elles forment 204 unités et 201 blocs distincts (64 notes, 137 en-têtes d'EX-10), sans erreur de construction ni bloc déjà lu en première tranche. Lecture : 263 lignes valides, aucune rejetée. 129 observations dans 67 blocs : 32 `commercial`, 32 `customer_consideration`, 8 `financing`, 57 sans famille (parties d'en-tête, fusions, cessions). 134 abstentions : 113 hors périmètre, 18 doubles, 2 sans contenu pertinent, 1 illisible (pièce EX-10.1 de Squarespace, sans texte). (2) Cas tranchés, consignés au guide (`work/guide_lecture_discovery.md`, §5) :
  - Affirm remet des bons à des filiales d'Amazon.com, Inc. au titre d'accords commerciaux. Il les porte en charges commerciales et de marketing, ou en actif de l'accord amorti en charges. Ce sont des coûts d'achat : `commercial`, Affirm → Amazon, `judgment_sensitive` (5 lignes). La famille `customer_consideration` reste réservée aux bons portés en réduction du revenu (Clean Energy, Ranpak, ATSG).
  - PLAYSTUDIOS publie la part de ses créances due par chaque plateforme de distribution. Google Play encaisse les achats des joueurs : une ligne `commercial`, `judgment_sensitive` (règle du guide, §1).
  - Mentions fausses du lexique, en abstention `out_of_scope_content` : « Meta » pour Meta Materials (et Torchlight Energy Resources, son ancien nom), le navire « the Amazon » (McDermott), le projet éolien « Amazon Wind » (Pattern Energy), « AMD » dans les pièces d'Installed Building Products, « Microsoft Word » dans les titres de fichiers (JBG SMITH).
  - Litiges et transactions avec un groupe, hors périmètre : accord transactionnel du 7 juillet 2025 entre Rimini Street et Oracle, actions sur la fusion résiliée d'iRobot avec Amazon, action Horn contre Amazon (PLAYSTUDIOS), actions contre la fusion de Cavium avec Marvell.
  - L'état des placements du plan 11-K de Boeing (601 287 caractères) a été parcouru en entier par recherche des noms de groupes. Les 35 lignes trouvées sont des placements du plan : abstention.

  (3) Rattachement : Amazon.com Services LLC entre dans le groupe AMZN (`confirmed_entities`). Extrait : « Amazon.com Services LLC, a direct or indirect subsidiary of Amazon » (8-K/A d'ATSG du 2024-05-10, EX-10.2), où le même bloc définit « Amazon » comme Amazon.com, Inc. Jusqu'ici, l'entité formait son propre groupe sous la dénomination « AMAZON.COM SERVICES, LLC », prêteur de 1Life Healthcare dans un en-tête d'EX-10 (D-0022). « Google Cloud » (Ginkgo Bioworks, Snap) reste en attente : aucun extrait lu ne la rattache à Google LLC (convention de D-0021). (4) Pièces de lien relevées (8 lignes) :
  - ATSG–Amazon : L1 (trois lignes : bons émis ou acquis selon les avions pris à bail par Amazon et les prolongations de baux), L2 (bons de 14,8 millions d'actions remis avec l'engagement de louer dix Boeing 767-300 de plus et la prolongation de l'ATSA), L5 (bons présentés comme une incitation à prendre des avions à bail et à confier leur exploitation) ;
  - Clean Energy–Amazon : L1 (tranches du bon acquises selon les achats de carburant d'Amazon et les redevances, jusqu'à 500,0 M$) ;
  - ADT–Google : L2 (crédits, remises et incitations de Google pour Google Cloud Platform, accordés avec l'engagement d'achat d'ADT), L5 (avenant au pacte de l'investisseur Google lié au « Cloud Addendum »), ce dernier `judgment_sensitive`.

  (5) Effets, au réassemblage :
  - cinq paires nouvelles. Alphabet–ADT devient « dépendance documentée » : structure commerciale et financière, pièces L2 et L5 d'ADT. Alphabet–Planet Labs est une « relation commerciale doublée d'un financement », recherche incomplète. Amazon–Affirm, Alphabet–PLAYSTUDIOS et Oracle–Paramount Skydance n'ont qu'une structure commerciale : causalité non établie, recherche incomplète ;
  - pour Alphabet–ADT et Alphabet–Planet Labs, F reste « non traité » dans la vue `as_known` : aucune pièce lue n'en établit les conditions (a) à (c), et des unités de ces clients qui nomment Google restent à lire. Ces paires n'entrent donc pas encore dans E.1 ;
  - le rattachement d'Amazon.com Services LLC fait entrer dans la paire Amazon–1Life les deux lignes du prêt qu'elle consent à 1Life Healthcare (arêtes : 3 → 5). La conclusion ne change pas : financement seul, recherche incomplète ;
  - Ginkgo Bioworks ne forme pas de paire : ses lignes nomment « Google Cloud », entité en attente ;
  - pièces d'une paire relevées dans la découverte : 3 → 5 (les deux d'ADT). Les pièces d'ATSG et de Clean Energy lient Amazon à un fournisseur qui lui remet des bons : comme en D-0039, ce sens ne forme pas de paire (§3.1) ;
  - inchangés : 11 paires à financement documenté (F active au moins un trimestre, vue `as_known`) ; E.1 à 9 « non étayé » et 2 indéterminées ; E.7 à 13 issues indéterminées sur 22 (59 %), « discrimination possible » ;
  - unités de la file encore à lire : 19 003 → 18 799. Source : §2.4, §3.1, §3.4, §7.4, §10.2, §14, annexe E.
- **D-0041 — Lecture de la découverte arrêtée ; blocs `paths` et `form_d` ouverts.** (1) Après un point d'étape, l'utilisateur a répondu le 2026-10-10 « ok fais ça, toujours sans sous-agent » à la proposition d'arrêter la lecture de la découverte et d'ouvrir `paths` et `form_d`. La décision est consignée dans `config.yaml` (`scope`, `scope_history`), avec l'état publié avant l'ouverture (commit ccb65e5). La passe A reste lue jusqu'au rang 50 ; les 18 799 unités restantes de la file restent « non traitées », une par une dans `exclusions`. Le bloc `foreign` reste fermé, et la tâche planifiée de §11.5 n'est pas créée. (2) Bloc `paths` (`pipeline/paths.py`) :
  - les arêtes vont dans le sens de la ressource (§3.1). Un maillon est une arête non éliminée entre deux groupes connus et distincts, des quatre familles, qui ouvre une relation : une ligne de remboursement, de résiliation, de conversion ou de cession, ou au stade `settled` ou `terminated`, suit la trésorerie et n'en fait pas un. Sans cette règle, les remboursements de Broadcom à Bank of America formaient un faux cycle ;
  - un cycle orienté de longueur 2 ou 3 passe par au moins un groupe de `config.yaml` et s'écrit à partir du plus petit d'entre eux ;
  - `temporal` vaut `yes` si l'on peut choisir une arête par maillon dont les périodes sont actives ensemble ou à moins de quatre trimestres civils d'écart, `no` sinon, `unknown` si un maillon n'a aucune arête datée ;
  - pièce d'une jonction (x → y, y → z) : la règle de D-0039, étendue. Une ligne L1 à L5 compte si ses parties résolues comprennent y et l'un de ses voisins, et si son extrait nomme x, y et z (pour un cycle de longueur 2, x = z : c'est exactement la règle des paires). Une ligne n'a que deux parties : une pièce de jonction d'un cycle de longueur 3 doit nommer la troisième dans son extrait, ce qui est rare par construction ;
  - conclusion comme pour une paire (§3.4) : `documented_dependency` seulement si chaque jonction a sa pièce et que le cycle combine financement (ou contrepartie au client) et achats. Le lien est `searched_none_found` si chaque nœud est un groupe dont le texte est lu ou un laboratoire, et qu'aucune paire mesurée du cycle n'est en recherche incomplète ; sinon `search_incomplete` ;
  - E.6 n'est plus « non traité » : une cellule par fournisseur avec le décompte des cycles qui passent par lui, par `temporal` et par conclusion, et une cellule d'ensemble où chaque cycle compte une fois.

  (3) Bloc `form_d` (`pipeline/formd.py`) :
  - émetteurs du périmètre (`issuer_is_subject` vrai) : Form D déposés par un CIK des groupes (têtes, prédécesseurs, entités du registre : X.AI Corp., Inphi, VMware), ou par une entité du registre reconnue à sa dénomination légale, comme toute contrepartie (§10.2). C'est le cas de X.AI Holdings Corp. (CIK 2079267), dont le 10-Q de SpaceX constate l'acquisition. Chaque offre est rattachée au groupe de l'émetteur à la date du dernier dépôt, dans chaque vue : X.AI Corp. et X.AI Holdings Corp. forment leur propre groupe en vue `as_known` avant le 2026-02-02, et appartiennent à SpaceX en vue `revised` (§10.3). Les offres dont le dernier dépôt précède la fenêtre allongée sont exclues (`out_of_scope`) ;
  - véhicules tiers (`issuer_is_subject` faux) : Form D trouvés par la recherche plein texte de la découverte, déjà en cache. Leur dénomination, ou la description des titres offerts (séries de Linqto), nomme un laboratoire ou un groupe qui ne dépose encore aucun rapport périodique, selon les termes et les règles de casse du lexique. Le sous-jacent est un non-déposant à une fin de trimestre si c'est un laboratoire, ou si son premier 10-K ou 10-Q est déposé après cette date (SpaceX le 2026-08-04, CoreWeave le 2025-05-15). La complétude est celle de la recherche plein texte consignée ; « XAI » en capitales ne répond pas au terme « xAI », sensible à la casse ;
  - émetteurs écartés, motif lu dans le Form D lui-même (`config.yaml`, `form_d.excluded_issuers`) : Anthropic Capital Fund, LP (fonds de type « Hedge Fund » dont le commandité et le gérant portent le nom Anthropic Capital), Karbon-X Corp. (« X Corp » n'y est que la fin d'une autre dénomination), et les huit fonds « OpenAI Startup Fund » (I, II, SPV I à VI), dont la dénomination nomme le promoteur d'un fonds de démarrage, pas une exposition à OpenAI ;
  - mesure `form_d_offering_amount` : par offre (CIK de l'émetteur et date de première vente ; un D/A sans date reprend celle du dépôt qu'il amende), sur le dernier dépôt connu ; chaque dépôt `replaces` le précédent (§8.2). Pour un véhicule, une cellule par trimestre civil, sur le dernier dépôt connu à la fin du trimestre, tant que le sous-jacent ne dépose pas. Aucun total, ni entre offres ni entre véhicules ; le montant peut inclure du non monétaire (regroupements d'entreprises signalés) ;
  - collecte : 43 requêtes (submissions de trois CIK du registre et XML des Form D des groupes), toutes au journal.

  (4) Corrections liées. Un Form D est classé « filed », niveau C (annexe A), et non plus comme une instance XBRL. `audit/domain_rules.md` énonce désormais les règles des blocs ouverts de §14 ; la page disait encore « le §14 n'est pas ouvert » depuis l'ouverture de `lender` et de `text`. (5) Effets, au réassemblage :
  - 23 cycles, dont 20 de longueur 2 et 3 de longueur 3. Concomitants : 10 « dépendance documentée », 11 « relation commerciale doublée d'un financement », 1 « achats réciproques seulement » ; non concomitant : 1 « relation commerciale doublée d'un financement » ;
  - les cycles documentés sont de longueur 2 : ceux des paires documentées (AMD–OpenAI, AMD–Meta, Amazon–Rivian, Amazon–OpenAI, Alphabet–ADT, Marvell–Alphabet, NVIDIA–IREN, NVIDIA–OpenAI), plus Amazon–ATSG et Amazon–Applied Optoelectronics. Dans ces deux derniers, le fournisseur qui remet des bons à Amazon est hors du périmètre : ce sens ne forme pas de paire (§3.1), mais il forme un cycle ;
  - cycles de longueur 3 : CoreWeave → NVIDIA → OpenAI → CoreWeave (concomitant, écart de 2 trimestres, recherche complète, aucune pièce de jonction) ; CoreWeave → OpenAI → NVIDIA → CoreWeave (écart de 4 trimestres, non concomitant) ; Amazon → OpenAI → Cerebras → Amazon (concomitant, recherche incomplète). Aucun n'est documenté ;
  - E.1 et E.7 inchangés : 13 issues indéterminées sur 22 (59 %), « discrimination possible ». E.6 est descriptif, hors de E.7 ;
  - Form D, émetteurs du périmètre : 20 offres dans la fenêtre allongée (SpaceX 7, CoreWeave 4, X.AI Corp. 4, X.AI Holdings Corp. 2, Marvell 2, Microsoft 1), 40 cellules (deux vues) ; 13 offres antérieures exclues ;
  - Form D, véhicules : 303 émetteurs, 2 275 cellules trimestrielles. Par sous-jacent : SpaceX 194 véhicules, Anthropic 61, OpenAI 32, CoreWeave 13. Les 10 émetteurs écartés portent 12 offres. 883 Form D sont au registre `documents` (niveau C), et 293 relations `replaces` relient les dépôts d'une même offre. Source : §3.1, §3.4, §8.2, §10.2, §10.3, §10.4, §12.2, §14, annexes A, D et E (E.6).
- **D-0042 — Bloc `foreign` ouvert : émetteurs étrangers, cadre comptable et invariant (f).** (1) L'utilisateur a demandé le 2026-10-10 : « Poursuis sur le bloc foreign, toujours sans sous-agent ». La décision est consignée dans `config.yaml` (`scope`, `scope_history`, section `foreign`), avec l'état publié avant l'ouverture (commit 94b7a1e). Aucun groupe de `config.yaml` n'est étranger : le bloc s'ouvre avec la découverte (§14). (2) Inventaire et sélection, fixés avant toute lecture :
  - la file de la découverte compte 263 déposants dont une mention vient d'un formulaire étranger (20-F, 40-F, 6-K, F-1, F-4 et leurs amendements), pour 1 962 mentions (`db/foreign_inventory.parquet`) ;
  - la règle retient les unités de ces formulaires pour deux sortes d'émetteurs : ceux que la spec nomme comme nœuds de la chaîne (IREN, 20-F jusqu'à l'exercice clos le 30 juin 2024 ; Nebius, 20-F et 6-K ; §14 et annexe D), et les contreparties étrangères déjà présentes dans une paire ou un cycle (IREN). Six unités en résultent : trois notes du 20-F 2025 de Nebius, et les notes « événements postérieurs » d'un 20-F, d'un 20-F/A et d'un 6-K d'IREN ;
  - ces unités sont lues hors de l'ordre de D-0036, au titre de ce bloc. Les autres unités étrangères restent dans la file, « non traitées ».

  (3) Règles mises en œuvre (`pipeline/foreign.py`) :
  - cadre comptable d'une note : celui de sa balise dans les Notes Data Sets (colonne `version`). Nebius dépose son 20-F en US GAAP, IREN ses 20-F et 6-K en IFRS. La colonne `framework` des observations le porte : `us_gaap` pour les notes des groupes, aucun cadre pour un contrat ou un narratif ;
  - invariant (f) : un agrégat qui mêle des arêtes de cadres différents est écarté (`invalid_aggregate`, motif `mixed_framework`, nouvelle valeur de l'énumération des motifs) ;
  - un 6-K est furnished, niveau E, sauf mention expresse d'incorporation par référence lue dans le 6-K lui-même. Le 6-K d'IREN du 15 février 2024 la porte (« shall be deemed to be incorporated by reference into the registration statements on Form S-8 ») : admissible, niveau C, `incorporated_by_reference` vrai. Les 20-F et 40-F sont des états annuels audités (niveau A, annexe A), y compris dans la table `documents`, qui les tenait jusqu'ici pour non audités ;
  - les formulaires étrangers et les Form D entrent dans `watched_forms` (§11.5) ; la tâche planifiée n'est pas créée.

  (4) Lecture, sans sous-agent : 6 blocs, 8 observations, 1 abstention, aucune ligne rejetée.
  - Nebius (20-F 2025, US GAAP) :
    - contrat avec Microsoft du 8 septembre 2025 : capacité GPU dédiée sur cinq ans, frais « up to $17,392.9 » dont des avances « approximately $6,958.1 » ;
    - contrat avec Meta du 1er novembre 2025 : « approximately $2,880.7 ». Le bloc n'annonce pas l'échelle de ces trois montants, qui restent non convertis (guide, §5) : arêtes de relation ;
    - après la clôture : bon de souscription préfinancé vendu à NVIDIA le 11 mars 2026, environ 2,0 Md$ (fait balisé), arête de financement NVIDIA → Nebius ;
    - contrat d'approvisionnement avec Meta du 16 mars 2026, environ 12 Md$ (fait balisé), et engagement de Meta d'acheter jusqu'à 15 Md$ de capacité invendue (soutien de capacité, même convention que les accords de NVIDIA) ;
    - la note des méthodes comptables (version « Policies ») reprend mot pour mot les contrats de 2025 : doublon.
  - IREN (IFRS) : achats de GPU NVIDIA annoncés le 29 août 2023 (248 H100, environ 10 M$), le 14 février 2024 (568 H100, environ 22 M$) et le 16 septembre 2024 (1 080 H200, environ 43 M$). Le texte nomme le fabricant des GPU, pas le vendeur : lignes sans famille, aucune arête vers NVIDIA ;
  - la mention « Commercial Partnership with NVIDIA » de Nebius et la plateforme « NVIDIA Vera Rubin » du contrat avec Meta ne décrivent aucun achat à NVIDIA : aucune arête commerciale Nebius → NVIDIA, aucune pièce de lien.

  (5) Effets, au réassemblage :
  - une paire nouvelle, NVIDIA → Nebius : financement seul, recherche complète (les unités de Nebius qui nomment NVIDIA sont toutes lues), aucune pièce de lien, donc causalité non établie. F y est actif sur deux trimestres de NVIDIA (clos le 2026-04-26 et le 2026-07-26) : 12 paires à financement documenté au lieu de 11 ;
  - E.1 compte 10 issues « non étayé » (dont NVIDIA–Nebius) et 2 indéterminées ; E.2, 12 indéterminées. E.7 : 14 issues indéterminées sur 24 (58 %), toujours « discrimination possible » ;
  - les arêtes Microsoft → Nebius et Meta → Nebius ne forment ni paire (Nebius est hors du périmètre et Microsoft et Meta y sont clients) ni cycle (aucune arête documentée ne revient de Nebius vers ces groupes ou vers NVIDIA) : les 23 cycles sont inchangés ;
  - pour NVIDIA, le flux après financement des contreparties du trimestre clos le 2026-04-26 intègre le versement de 2,0 Md$ à Nebius (48 587 M$ → 46 587 M$), seul chiffre de `series.md` qui change ;
  - lignes par cadre comptable : 5 765 en US GAAP, 3 en IFRS (IREN), 2 076 sans cadre (contrats, narratifs) ; aucun agrégat ne mêle les cadres (invariant f : aucune exclusion).

  (6) Correction liée : un même CIK est une même entité (§10.2). La découverte rattachait chaque bloc au groupe de la dénomination portée par le dépôt : les dépôts d'IREN de 2023 et 2024, au nom d'Iris Energy, formaient ainsi un groupe distinct. Douze CIK lus étaient dans ce cas. Les observations d'un déposant découvert prennent désormais le groupe de sa dénomination la plus récente, et onze anciennes dénominations deviennent des alias (règle `same_cik`) : Iris Energy (IREN), Cipher Mining (Cipher Digital), dMY Technology Group IV (Planet Labs), Acies Acquisition Corp. (PLAYSTUDIOS), Soaring Eagle Acquisition Corp. (Ginkgo Bioworks), NortonLifeLock (Gen Digital), GP Investments Acquisition Corp. (Rimini Street), Torchlight Energy Resources (Meta Materials), Meta Financial Group (Pathward), Oak Street Net Lease Trust (Blue Owl Real Estate Net Lease Trust), IAC Inc. (People Inc.). « IAC/InterActiveCorp », porté par deux CIK (Match Group et People Inc.), reste sans alias. Aucune conclusion de paire ni aucun cycle n'en change. Source : §2.1, §2.2, §7.6 (invariant f), §10.2, §11.5, §14, annexes A et D.

- **D-0043 — Ajout de groupes : TeraWulf (WULF), Cipher (CIFR) et Core Scientific (CORZ).** Décision de l'utilisateur, le 2026-10-10 : « On continue sur l'ajout de nouveaux groupes, toujours sans sous-agent ». Elle fait suite au rapport de livraison du bloc `foreign` (commit 2364e9c). Les trois groupes sont pris dans l'ordre de §14, les hébergeurs endettés d'abord ; Nebius et IREN restent traités par le bloc `foreign`. Lecture séquentielle par l'exécutant, sans sous-agent.

  (1) Configuration :
  - les trois groupes entrent dans `config.yaml`, jamais dans le code (§14). `company_tickers.json` résout les tickers vers les CIK 1083301, 1819989 et 1839341, conformes aux CIK indicatifs ;
  - `group_entry` date l'entrée de chaque groupe dans le modèle : les onze groupes de l'annexe B le 2026-10-07, les trois nouveaux le 2026-10-10 ;
  - les cellules entre groupes de l'annexe E (E.6 à E.9) portent cette composition et ces dates, et `synthesis.md` les énonce (§9.6).

  (2) Date de connaissance :
  - l'exécution garde l'as_of du 2026-10-07. Les submissions et les companyfacts des trois CIK, tirés le 2026-10-10, sont rangés sous cet as_of ;
  - les dépôts postérieurs à l'as_of (quatre pour Cipher) et les faits déposés après lui sont écartés en phases 0 et 1 ;
  - le journal garde l'heure réelle de chaque requête.

  (3) Fusions inversées. Chacun des trois CIK a d'abord été celui d'une autre entité, le déclarant légal :
  - IKONICS Corporation pour TeraWulf : TeraWulf en est le successeur au sens de la Rule 12g-3(c), à la fusion du 2021-12-13 (8-K12B 0000950142-21-003986). Le 10-K 2021 dit : « For financial accounting purposes, the business combination was treated as a reverse merger whereby the accounting acquirer was TeraCub » ;
  - Good Works Acquisition Corp. pour Cipher : recapitalisation inversée du 2021-08-27. Le 10-Q du T3 2021 dit : « The Merger was accounted for as a reverse recapitalization in accordance with U.S. GAAP » ;
  - Power & Digital Infrastructure Acquisition Corp. pour Core Scientific : recapitalisation inversée du 2022-01-19. Le 10-Q du T1 2022 dit : « The Merger is accounted for as a reverse recapitalization with the Company being the accounting acquirer ».

  La règle des prédécesseurs (§10.1) suppose des états consolidés qui se continuent. Ici ils ne se continuent pas : l'historique du groupe est celui de l'acquéreur comptable, publié par les rapports postérieurs à la réalisation. D'où la règle, écrite dans `config.yaml` (`reverse_combinations`) :
  - hors du groupe : les rapports périodiques du CIK dont la période se clôt avant la réalisation, et ses autres dépôts antérieurs à la réalisation. Ils forment la classe d'inventaire `pre_combination`, hors des séries et du texte ;
  - leurs faits de companyfacts sont écartés : 8 516 pour TeraWulf, 874 pour Cipher, 384 pour Core Scientific ;
  - le 10-K 2021 de Core Scientific, déposé après la réalisation, présente encore la SPAC (actif de 346 368 517 $) : il est écarté ;
  - le 8-K (item 4.02) de Cipher du 23 décembre 2021 ne porte que sur les états de la SPAC : « Therefore, the errors relate to the pre-business combination SPAC and its financial statements ». Il est écarté de même ;
  - les trois groupes portent `history_left_censored`. Leurs trimestres attendus commencent au premier 10-Q de l'acquéreur comptable (`reporting_start`) ;
  - l'appartenance du CIK à son groupe porte `combination_method` `reverse_recapitalization`, valeur ajoutée à l'énumération.

  (4) Du code vers la configuration :
  - les débuts d'obligation de publier de SpaceX et de CoreWeave passent du code (`universe.py`) à `config.yaml` (`reporting_start`). L'univers attendu des onze groupes est inchangé (vérifié ligne à ligne) ;
  - `history_left_censored` se lit dans la phase 0 au lieu d'une liste codée, avec le même résultat pour les onze groupes. Son exclusion est publiée pour chaque groupe concerné.

  (5) Alias : « Core Scientific, Inc. » est un alias de « Core Scientific, Inc./tx ». Le « /tx » est un suffixe de désambiguïsation d'EDGAR, pas la dénomination légale. La pièce : « Core Scientific, Inc., a Delaware corporation (the "Company") » (0001193125-22-199189).

  (6) Découverte :
  - les lignes déjà lues dans la découverte pour TeraWulf (8 blocs) et Cipher (9 blocs) vont désormais à leur groupe. Les en-têtes de pièces de même clé de contenu ne se relisent pas ;
  - les unités de ces déposants encore dans la file en sortent (`out_of_scope`) : leurs dépôts se lisent par le catalogue du groupe ;
  - côté client, la recherche reste incomplète pour un fournisseur que le lexique de la découverte ne nommait pas, c'est-à-dire pour les trois nouveaux groupes : le scan des Notes Data Sets n'a jamais cherché leurs noms (`search_incomplete`).

  (7) Un 10-K/A ou un 10-Q/A sans instance XBRL ne contient aucun état financier :
  - TeraWulf, 2025 : « Because no financial statements have been included in this Amendment » ;
  - Alphabet, 2019 : amendement « for the sole purpose of updating the consent in Exhibit 23.01 ».

  Ce n'est donc plus un échec de parse : ni recherche incomplète, ni exclusion `parse_failed`. L'exclusion d'Alphabet de 2019 disparaît.

  (8) Correction liée : l'en-tête de `synthesis.md` lisait l'état de la lecture de la découverte dans la dernière décision de `scope_history`. Depuis D-0042, il affichait à tort une lecture « par tranches ». Il lit désormais la dernière décision qui fixe cet état (arrêt, D-0041).

  (9) Lecture, sans sous-agent, groupe après groupe, un commit par groupe (903d52c, c2018c5, 9913545) :
  - TeraWulf : 315 blocs au catalogue, 310 lus, 498 lignes (361 observations, 137 abstentions) ; 174 blocs portent au moins une observation ;
  - Cipher : 266 blocs, 259 lus, 398 lignes (335 observations, 63 abstentions) ; 196 blocs avec observation ;
  - Core Scientific : 286 blocs, 278 lus, 1 112 lignes (1 019 observations, 93 abstentions) ; 185 blocs avec observation ;
  - les blocs non lus sont des corps d'EX-4 dont l'en-tête ne nomme que des établissements financiers (`financial_parties_only`, §11.1) : 5 pour TeraWulf, 7 pour Cipher, 8 pour Core Scientific. Aucune ligne rejetée.

  Relations avec des groupes déjà présents :
  - Google et les hébergeurs : Google garantit certaines obligations de Fluidstack, locataire de TeraWulf et de Cipher (« Google has agreed to backstop (the "Google BackStop") certain obligations of Fluidstack »), contre des bons de souscription à 0,01 $ : 41 011 803 actions TeraWulf (13 août 2025), 32 568 197 (17 août 2025), 24 178 576 actions Cipher (24 septembre 2025, contrat refondu le 20 novembre 2025). Google nantit ces bons au profit des prêteurs des chantiers. La garantie du centre de données d'Abernathy, coentreprise de TeraWulf, « totals $1.3 billion » ;
  - Amazon : bail de 15 ans d'octobre 2025 entre Cipher et Amazon Data Services, Inc., environ 300 MW bruts à Black Pearl, montant non publié ;
  - Anthropic : bail de 20 ans du 6 juillet 2026 entre Raylan Data LLC, filiale de TeraWulf, et Anthropic PBC, environ 401 MW à Hawesville (Kentucky), montant non publié ;
  - CoreWeave : accord de fusion du 7 juillet 2025 avec Core Scientific, résilié le 30 octobre 2025 après le rejet des actionnaires de Core Scientific ; indemnité de résiliation de 270 M$ due dans des cas déterminés. Lignes sans famille : ni financement ni achat. Les contrats d'hébergement viennent des lignes de CoreWeave, qui nomment Core Scientific.

  Corrections faites en lecture :
  - TeraWulf : dans le 10-Q du T1 2024, la part du prêt à terme détenue par des parties liées (6,7 M$ au 31 mars 2024, 12,9 M$ au 31 décembre 2023) est balisée avec le membre « NovaWolf Digital Master Fund & NovaWulf digital Private Fund ». Le 10-K 2023 dit qu'en octobre 2023 les créances de NovaWulf ont été distribuées à des entités contrôlées par des dirigeants et un administrateur : détenteurs non attribués, lignes anonymes, sans famille ;
  - Cipher : les 10-Q de 2026 datent du 31 décembre 2025 un encours de 25,0 M$ envers Coinbase. Le 10-K 2025 et les flux de trésorerie (25,0 M$ remboursés en 2025) le situent au 31 décembre 2024 : lignes sans famille ;
  - Core Scientific : l'item 1.01 du 8-K d'août 2022 attribue le billet relais de 60 M$ à B. Riley Commercial Capital et celui de 15 M$ à un affilié. Les pièces 10.1 et 10.2 disent l'inverse (15 M$ pour B. Riley Commercial Capital, 60 M$ pour BRF Finance Co., LLC). Chaque ligne suit son bloc, et la note signale l'écart ;
  - Core Scientific : l'état de la dette existante au 30 novembre 2022, annexé au crédit DIP de remplacement (annexe 10.2.1), nomme chaque créancier : obligations convertibles, prêts, financements d'équipement. Il donne 118 lignes nommées. Les créances des personnes physiques et des fiducies familiales ne sont pas reprises, puisqu'un nom de particulier n'a pas sa place dans les tables ; leurs montants restent compris dans les soldes des notes de dette. Pour la même raison, le prêteur d'équipement qui est une personne physique (annexe J du plan) reste anonyme.

  (10) Délimitation `d4` de l'Item 9A. Le 10-K/A 2024 de Core Scientific (0001628280-26-013232) énumère dans sa note explicative les items qu'il modifie (« •Item 9A - Controls and Procedures; and »). Il ne porte ni Item 9B, 9C ou 10, ni partie III : la section retenue allait de cette puce à la fin du document (566 076 caractères, le rapport retraité entier). `d4` ferme l'Item 9A au titre d'item suivant, quel qu'il soit (ici l'Item 15), à « Part III », « Part IV » ou « Signatures ». La puce n'ouvre plus qu'une section de moins de 200 caractères, écartée. Sur les 92 Items 9A du catalogue, seul ce bloc change (16 038 caractères) : il reçoit une clé nouvelle et revient dans la file. Les autres blocs ne sont pas touchés, puisque la clé de contenu ne dépend que du texte (D-0016). L'ancien fichier d'observations est conservé, non chargé.

  (11) Correction liée : un bloc reste rattaché à chacun de ses dépôts. Un même texte peut revenir à l'identique dans plusieurs dépôts : il a une seule clé de contenu et ne se lit qu'une fois. L'assemblage ne le rattachait qu'à un seul dépôt, et les trimestres des autres perdaient leur bloc. Ainsi l'Item 4 d'Amazon, identique d'un 10-Q à l'autre (24 dépôts pour 3 textes), laissait 14 trimestres d'Amazon et 2 d'Oracle en « section non délimitée » (`parse_failed`) pour la faiblesse du contrôle interne. De même, le doute sur la continuité d'exploitation de Core Scientific au T2 2023, même passage qu'au T1 (« substantial doubt exists regarding our ability to continue as a going concern »), passait pour un trimestre sans événement. Chaque dépôt garde désormais son bloc.

  (12) Correction liée : date de publicité d'un signal (§7.3). Pour les trimestres clos du 31 décembre 2024 au 30 septembre 2025, Core Scientific n'a publié sa faiblesse de contrôle interne que par les 10-K/A et 10-Q/A du 2 mars 2026 : les rapports d'origine jugeaient le contrôle efficace. L'événement F5 prenait pourtant la date du rapport d'origine (2025), ce qui revient à se servir d'un dépôt de 2026 pour dire ce qu'on savait en 2025. Un signal présent prend désormais la date du premier rapport du trimestre qui le porte ; un trimestre sans signal garde celle de son premier rapport. Même règle pour F9 (item 1.02).

  (13) Entité : Amazon Data Services, Inc. était une contrepartie propre (D-0022). Une pièce déposée par Cipher affirme le contrôle (EX-4.1 du 8-K du 11 février 2026, 0000950103-26-001966) : « "Amazon Parent" means Amazon.com, Inc. "Amazon Tenant" means Amazon Data Services, Inc. », avec la « limited parent guarantee dated as of November 21, 2025 » de la société mère sur les loyers. L'entité devient filiale consolidée d'Amazon (`confirmed_entities`). Le corps de cette pièce reste à son en-tête (`financial_parties_only`) : il n'est cité que pour l'identité. La paire Cipher → Amazon en résulte.

  (14) Bloc `lender` : l'extraction des BDC Data Sets (`lender num`) est refaite après un premier réassemblage, puisque son registre de dénominations se lit dans les observations. Elle datait du 7 octobre : le registre comprend désormais aussi les contreparties nommées depuis (découverte, `form_d`, `foreign`) et les trois groupes. Les positions de BDC sur Core Scientific, publiées jusque-là sous une contrepartie propre, vont à son groupe : prêts et obligations de 30 M$ au coût en 2022, puis de 87 M$ en 2023. Au 31 décembre 2022, dix jours après la demande de protection du 21 décembre 2022, leur juste valeur tombe à 0,38 x le coût.

  (15) Effets, au réassemblage (14 groupes) :
  - événements de l'annexe F : 69 → 169, tous chez les trois groupes ajoutés (TeraWulf 27, Cipher 30, Core Scientific 43) ; ceux des onze autres groupes sont inchangés. Doute sur la continuité d'exploitation : Core Scientific du T3 2022 au T3 2023 (5 trimestres ; demande de protection le 21 décembre 2022), TeraWulf du T4 2021 au T3 2022 (4), Cipher au T3 2021 (1). Faiblesse du contrôle interne : Core Scientific 18 trimestres, dont 4 (T4 2024 à T3 2025) rendus publics le 2 mars 2026 seulement, Cipher 12, TeraWulf 2 ;
  - faiblesse du contrôle interne, toutes cellules : 14 trimestres d'Amazon et 2 d'Oracle passent de « section non délimitée » à « sans événement » (point 11) ; les cellules indéterminées de F5 tombent de 53 à 46, dont 9 trimestres sans rapport chez les nouveaux groupes ;
  - paires : 54 → 61. Nouvelles : Cipher → Amazon, Core Scientific → CoreWeave, TeraWulf → Anthropic et TeraWulf → Fluidstack USA I Inc. (structure commerciale seulement, recherche complète) ; Core Scientific → Bitmain Technologies Delaware Limited et TeraWulf → Heorot Power Holdings LLC (achats réciproques seulement) ; Core Scientific → Sphere 3D Corp. (recherche incomplète, Sphere 3D dépose hors du périmètre) Alphabet → Cipher et Alphabet → TeraWulf remplacent les contreparties « CIPHER DIGITAL INC. » et « TERAWULF INC. » de la découverte : structure financière seulement (garanties et bons de souscription), causalité non établie. Aucune nouvelle paire n'a de financement documenté (F) : elles restent 12 ;
  - E.1 et E.2 : 24 issues. E.1 compte 11 issues « non étayé » au lieu de 10 : Alphabet–SpaceX était indéterminée parce que l'archive d'Alphabet de 2019 passait pour illisible ; le point 7 la tranche. E.7 : 13 issues indéterminées sur 24 (54 %), toujours « discrimination possible » ;
  - cycles : 23 → 25. Core Scientific → Bitmain → Core Scientific, concomitant : Core Scientific achète des mineurs à Bitmain, qui reçoit en paiement des actions Core Scientific (53,9 M$, janvier 2024) et lui achète de l'hébergement ; « relation commerciale doublée d'un financement », recherche incomplète, Bitmain ne déposant pas. TeraWulf → Heorot Power Holdings → TeraWulf, non concomitant (16 trimestres d'écart) : achats réciproques seulement ;
  - bloc `lender` : cellules des BDC 831 → 1 251 (point 14) ;
  - exclusions : `conflicting` +178 (faits des trois groupes : TeraWulf 38, Cipher 62, Core Scientific 78), `financial_parties_only` +20, `out_of_scope` +6 (unités de la découverte et dépôts antérieurs aux fusions inversées, deux lignes par groupe), `history_left_censored` +3, `pending_entity` +91 (85 dénominations sans pièce d'identité, 6 positions de BDC qui nomment deux émetteurs), `not_processed` −44 (unités de la découverte des trois déposants). `parse_failed` passe de 3 à 16 : l'archive d'Alphabet de 2019 en sort (point 7), et les archives de BDC dont des lignes de `num` ont un nombre de champs inattendu passent de 2 à 16 avec la nouvelle extraction ;
  - tests unitaires : 60 (délimitation `d4`, date de publicité d'un signal). Source : §2.1, §3.1, §7.3, §9.2, §9.6, §10.1, §10.2, §11.1, §14, annexes A, E et F.
- **D-0044 — SoftBank, groupe économique non déposant (§10.4) : entités confirmées et découverte dédiée, règles fixées avant de voir les candidats.** (1) Décision de l'utilisateur, le 2026-10-10 : « Ok fais les niveaux 1 et 2, toujours sans sous-agent ». Elle suit une réflexion sur l'intégration de SoftBank, sur l'état publié au commit 05e85c0. Le niveau 1 réunit les entités de SoftBank en un groupe économique, par des extraits de pièces (§10.2). Le niveau 2 traite SoftBank comme un non-déposant, à la manière d'OpenAI et d'Anthropic, et cherche qui le nomme dans EDGAR. Le niveau 3, des comptes propres tirés de sources hors SEC, n'est pas retenu. Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Non-déposant. SoftBank Group Corp. est coté à Tokyo et ne dépose ni 10-K ni 20-F. Ses dépôts EDGAR éventuels, sans rapport périodique, ne nomment pas les financeurs d'un émetteur : la recherche est complète de son côté (D-0037, point 2), ce que l'intégration vérifie dans la liste des noms d'EDGAR. Son groupe s'écrit `NF:SOFTBANK` (`config.yaml`, `non_filers`), et non `LAB:` :
  - ce n'est pas un laboratoire ;
  - un Form D dont la dénomination nomme SoftBank est une offre d'une entité de SoftBank, pas un véhicule d'exposition : le bloc `form_d` ne prend pas SoftBank pour sous-jacent.

  Comme pour un laboratoire, la recherche est complète du côté de SoftBank pour une paire (E.0) et pour un cycle (bloc `paths`). Une filiale qui dépose elle-même ne fait pas de SoftBank un déposant ; ses dépôts restent des dépôts de découverte.

  (3) Niveau 1, entités confirmées dès maintenant (8-K de Cipher du 30 janvier 2025) :
  - SoftBank Group Corp. est la tête du groupe ;
  - Star Beacon LLC en est une filiale à 100 % : « Star Beacon LLC, a wholly owned subsidiary of SoftBank Group Corp. ("SoftBank") » ;
  - « SoftBank » est un alias du groupe.

  N'entrent dans le groupe que sur un extrait qui l'affirme, avec sa date : SoftBank Group Capital Limited et SVF Holdco (UK) Limited, vendeurs d'Arm dans le 8-K de NVIDIA du 14 septembre 2020 ; Arm Limited ; Ampere. Aucun bloc lu ne le fait aujourd'hui :
  - le 8-K de NVIDIA ne dit pas qui contrôle les vendeurs ;
  - la DEF 14A d'Oracle de 2025 ne donne que l'accord du 19 mars 2025 sur Ampere (« When the Ampere Acquisition closes, we will cease to be an investor in Ampere »), pas sa réalisation.

  (4) Niveau 2, sources et lexique :
  - lexique de la piste : « SoftBank », insensible à la casse, en mot entier, cible `NF:SOFTBANK`. Ni « Vision Fund », ni « SVF », ni « Arm », ni « Ampere », ni « SB Energy » : ce sont des termes ambigus (une unité électrique, un mot courant) ou des entités non confirmées (D-0036, point 3) ;
  - Notes Data Sets : les 47 archives de D-0036, retirées et scannées avec le lexique d'ensemble (groupes, laboratoires, Stargate, SoftBank). Ne sont gardées que les lignes de `txt` qui nomment SoftBank, avec les autres cibles nommées dans la même valeur, ainsi que `num`, `dim`, `tag`, `pre` et `ren` de leurs dépôts. Exclusions de D-0036 (dépôts des groupes, taxonomies qui ne sont pas des notes, nom propre du déposant). Extraits sous `cache/datasets/notes/{archive}/nf/`, manifeste `manifest_nf.jsonl` ;
  - recherche plein texte : la phrase « SoftBank » sur les formulaires racines des EX-10 (D-0036, point 5). Pas de Form D : un Form D ne se lit jamais, et SoftBank n'est pas un sous-jacent du bloc `form_d` ;
  - la découverte d'origine ne change pas : mêmes extraits, même version de lexique, même classement, même file, même état de lecture. L'arrêt de D-0041 tient.

  (5) Candidats, classement et règle de lecture :
  - candidat : le déposant (CIK). Classement de D-0036 : classe de mention, puis montant documenté, puis nombre de cibles nommées, puis accession. Le montant documenté est celui d'un fait de `num` dont un membre de dimension nomme SoftBank ;
  - unités lues :
    - (R1) une note ou un EX-10 qui nomme SoftBank et, dans la même unité, un groupe, un laboratoire ou Stargate : toutes ces unités, de la plus récente à la plus ancienne ;
    - (R2) pour un candidat qui a un montant documenté, les notes de son dépôt le plus récent qui nomment SoftBank ;
  - le reste est exclu, motif `not_processed`, la règle dans le détail ;
  - ordre : R1 puis R2, chacun dans l'ordre du classement. Un texte identique n'est qu'une unité, et un bloc déjà lu par la découverte d'origine (même clé de contenu) ne se relit pas. Un EX-10 se lit par son en-tête ; son corps seulement si l'en-tête montre un groupe partie, après les notes ;
  - plafond : au-delà de 300 unités retenues, la lecture s'arrête à la 300e. Le reste est `not_processed`, et le rendement est présenté avant d'aller plus loin ;
  - l'état d'une unité préparée se garde sous sa clé (accession, document), non sous son rang dans la file, pour qu'un lexique enrichi ne décale rien.

  (6) Lecture, sans sous-agent :
  - 89 candidats et 1 221 unités. 78 unités retenues chez 26 candidats : 40 par R1, 38 par R2 ; 57 notes et 21 en-têtes d'EX-10. Les 1 143 autres sont hors règle, exclues avec le motif `not_processed` et la règle dans le détail. Le plafond n'est pas atteint ;
  - 75 blocs lus, les 3 autres unités l'ayant déjà été par la découverte d'origine. Puis 2 corps d'EX-10 dont l'en-tête montre NVIDIA partie : la convention de droits d'enregistrement et le contrat à terme prépayé de SB Energy (S-1 et S-1/A de 2026). Aucun autre en-tête ne montre un groupe partie ; ces corps ne se lisent pas ;
  - 126 lignes : 96 observations, 30 abstentions, aucune rejetée ;
  - Arm Holdings plc (rang 51) est hors règle : ni co-mention dans une unité, ni montant documenté. Il n'est pas lu, la règle étant fixée ;
  - incident : un lot soumis deux fois a dupliqué des lignes dans 7 fichiers d'observations. Les doublons ont été retirés avant l'assemblage (8 lignes ramenées à 4 dans un fichier, 2 à 1 dans les autres).

  (7) Niveau 1, entités confirmées pendant la lecture (`config.yaml`, `confirmed_entities` et `entity_aliases`). Traitement de consolidation `undetermined` sauf mention contraire.
  - Règle A, l'extrait affirme le lien :
    - alias « SBG » : note 1 du 10-Q de WeWork du 8 août 2023, « All references to "SBG" are references to SoftBank Group Corp. or a controlled affiliate or subsidiary thereof ». L'alias est global ; seules des lignes de WeWork le portent ;
    - Brightstar US, Inc., filiale (`consolidated_subsidiary`) : 10-Q de Sprint de janvier 2020, « As Brightstar is a subsidiary of SoftBank ». Sa sortie du groupe n'est pas documentée ;
    - SoftBank Latin America (« an affiliate of SBG », WeWork) et SB Northstar LP (« an affiliate of SoftBank Group Corp. », Better Home & Finance) ;
    - SB Energy HoldCo, LLC et SVF II Energy (DE) LLC : le corps de la convention de droits d'enregistrement de SB Energy définit « SoftBank » comme SoftBank Group Corp., et les « SoftBank Holders » du préambule comme incluant « any other Affiliate of SoftBank ».
  - Règle B, désignation : SoftBank Group Capital Limited (8-K de NVIDIA de septembre 2020, aussi Moatable), SoftBank Vision Fund (AIV M2) L.P. (10-K 2024 de GM), SVF Yellow (USA) Corporation (Uber), Stellar Beacon LLC (Twenty One Capital) et SoftBank Corp. (AeroVironment, Bloom Energy). Le déposant désigne chacune par le terme défini « SoftBank », qui est l'alias déjà confirmé du groupe :
    - une ligne qui aurait gardé ce terme serait rattachée au groupe, et la convention de lecture impose d'écrire le nom désigné ;
    - sans cette règle, une même contrepartie changerait de groupe d'un bloc à l'autre : chez GM, « SoftBank » en 2021 et 2022, le nom du fonds en 2024 ;
    - cette règle assouplit le point (3), qui écartait SoftBank Group Capital Limited faute d'extrait sur le contrôle. C'est une décision de l'exécutant, soumise à l'utilisateur ; la retirer revient à supprimer ces cinq entrées de `config.yaml`.
  - Alias sans appartenance : « SVF II » désigne SoftBank Vision Fund II-2 L.P. (même note de WeWork). Ce fonds n'entre pas dans le groupe : WeWork l'exclut expressément de « SBG », et aucun extrait n'affirme son contrôle. Même chose pour SoftBank Vision Fund (AIV M1) L.P. et SVF Endurance (Cayman) Limited.
  - Restent hors du groupe, faute d'extrait :
    - « SoftBank Group » chez Intel (2 lignes, dont le placement de 2,0 Md$ de septembre 2025) : aucun bloc ne définit ce terme ;
    - Softbank Vision fund (Getaround), Softbank Robotics Singapore Pte Ltd (Concorde) ;
    - HAPSMobile Inc., détenue à 100 % par SoftBank depuis mars 2022 : aucune ligne n'est postérieure ;
    - SB Energy, Inc. (contrôle non affirmé), OpenAI Infra Holdings, LLC, Arm, Ampere, SVF Holdco (UK) Limited ;
    - Sprint et Fortress, contrôlées par SoftBank à l'époque, restent des contreparties propres : aucun bloc lu n'affirme ce contrôle. Les flux entre Sprint et Brightstar ne s'éliminent donc pas.

  (8) Relations principales relevées :
  - WeWork :
    - échange en mai 2023 des 1,65 Md$ d'obligations série I détenues par des entités de SBG, contre 458 M$ d'obligations échangeables et environ 1,1 milliard d'actions (494 M$) ;
    - billets garantis de SVF II : 300 M$ émis puis rachetés, engagement de 500 M$ résilié, 300 M$ de billets de premier rang à tirage différé ;
    - JapanCo (500 M$, plus 31 M$ en 2022) et LatamCo (80 M$ de SoftBank Latin America, options pour 60 M$) ;
    - revenus d'adhésions tirés de SBG ;
  - GM : rachat des actions privilégiées de Cruise détenues par SoftBank, 2,1 Md$ en mars 2022 ;
  - Uber : 333 M$ de parts privilégiées d'Apparate en 2019, réglées à la cession d'ATG en janvier 2021 (356 M$) ;
  - Intel : 2,0 Md$ d'actions vendues à « SoftBank Group » en septembre 2025, 5,0 Md$ à NVIDIA en décembre 2025 ;
  - SB Energy : placement privé d'actions de classe N et contrat prépayé de 1,5 Md$ de NVIDIA ; bons d'OpenAI Infra Holdings ; actionnaires SoftBank ;
  - autres :
    - Guardant Health : coentreprise (41 M$), rachat 177,8 M$ ;
    - Sprint : bon exercé (287 M$) ; Brightstar (ligne de crédit de 700 M$, ventes d'appareils, commissions) ; 154 M$ dus à un affilié de SoftBank ;
    - DiDi (Voyager, 325 M$) ; AeroVironment (HAPSMobile, commande de 51,2 M$, 43,3 M$ de revenus) ; Moatable (rachats de 7,1 M$ et 2,5 M$) ;
    - Concorde (billet convertible de 1 M$), Getaround (prêt-relais de 5 M$), Tempus (coentreprise), Fortress (garantie limitée), Better (billet convertible de SB Northstar) ;
    - Twenty One Capital (actionnaire par achat à Tether, sortie en mai 2026), Alibaba, UTStarcom (40 % du chiffre d'affaires 2017), Bloom Energy (coentreprise rachetée 2,0 M$).

  (9) Non-déposant vérifié : ni SoftBank Group Corp. (CIK 1065521) ni SoftBank Corp. (CIK 1794354) n'a de rapport périodique dans les 47 archives des Notes Data Sets. La recherche reste complète du côté de SoftBank.

  (10) Effets au réassemblage, de l'état publié au commit 05e85c0 à maintenant :
  - paires : 60 → 64. Les 4 nouvelles sont en « causalité non établie » : Amazon → DISH (cloud 5G), NVIDIA → Energy Global, LP (contrat prépayé), NVIDIA → SB Energy (placement de classe N), NVIDIA → Intel (5,0 Md$). Aucune conclusion existante ne change ;
  - Microsoft → General Motors reste une relation commerciale doublée d'un financement, mais passe de 2 à 18 arêtes et de 11 à 21 trimestres « financé » actifs (actions de classe G de Cruise, cloud) ;
  - paires à financement documenté : 12 → 13 (NVIDIA → Intel) ;
  - cycles documentés : 25, inchangés ; aucun ne passe par SoftBank ;
  - annexe E : 13 issues indéterminées sur 24 → 15 sur 26. E.7 reste « discrimination possible » ;
  - SoftBank porte 47 arêtes. 3 vont à un groupe ou un laboratoire : 2 à Cipher (placement de 50 M$ de Star Beacon LLC en janvier 2025, et une arête de relation), 1 à OpenAI (investisseur, pièce d'Amazon). Les autres vont à des contreparties propres (WeWork, GM, Sprint, Uber, DiDi, Guardant Health, AeroVironment…). SoftBank n'est le client d'aucun groupe : il n'entre dans aucune paire (S, C) ;
  - les lignes d'Arm entre NVIDIA et SoftBank Group Capital Limited n'ont pas de famille : la règle B ne crée aucune arête entre groupes ;
  - flux de NVIDIA après financement des contreparties, trimestre clos le 25 janvier 2026 : 32 904 → 27 904 M$, soit les 5,0 Md$ placés chez Intel ;
  - exclusions `not_processed` : 18 749 → 19 892, dont 1 143 unités hors règle de la piste.

- **D-0045 — Fragilité du financement : Blue Owl, niveau 1. Signaux de portefeuille de toutes les BDC et événements F11 à F13 de l'annexe F, règles fixées avant tout calcul.** (1) Décision de l'utilisateur, le 2026-10-10 : « Fais le niveau 1, toujours sans sous-agent ». Elle suit « Pour Blue Owl ce qui m'intéresse c'est la fragilité du financement ». Le niveau 1 calcule, depuis les archives BDC déjà en cache et sans requête, des signaux de portefeuille par véhicule et par date de bilan, avec des événements de fragilité définis ici avant de voir une seule valeur. Les niveaux 2 (passif : levier, couverture, rachats) et 3 (nommer Blue Owl sur la coentreprise de Meta en Louisiane) ne sont pas ouverts. Lecture et calcul par l'exécutant, sans sous-agent.

  (2) Périmètre. Le bloc `lender` limite l'usage des BDC Data Sets aux positions sur les entités des groupes et sur leurs contreparties (§14). Cette décision l'étend au portefeuille entier de chaque BDC, pour les cinq mesures du point 5 seulement : bloc `lender_portfolio` dans `scope`. La fragilité d'un financeur se lit dans tout son portefeuille, pas dans ses seules positions sur nos groupes : les 60 cellules du bloc `lender` qui portent sur les BDC de Blue Owl visent des emprunteurs sans rapport avec la question.

  (3) Univers, sans sélection :
  - toutes les BDC des 21 archives en cache (2022 T4 à août 2026), soit environ 188 véhicules et 2 066 dépôts. Un véhicule est un déclarant (CIK). Aucune somme entre véhicules ;
  - véhicules Blue Owl : les déclarants dont la dénomination EDGAR, actuelle ou ancienne, contient « Blue Owl » ou « Owl Rock ». Ce sont Blue Owl Capital Corp, Blue Owl Capital Corp II, Blue Owl Capital Corp III, Blue Owl Technology Finance Corp., Blue Owl Technology Finance Corp. II, Blue Owl Credit Income Corp. et Blue Owl Technology Income Corp. C'est un regroupement de présentation par la marque du gestionnaire : ces fonds ne sont pas consolidés par Blue Owl Capital Inc., et aucun groupe économique n'est affirmé ;
  - repères nommés d'avance, pour la lecture : Ares Capital Corp, Blackstone Secured Lending Fund, Blackstone Private Credit Fund, Golub Capital BDC, FS KKR Capital Corp, HPS Corporate Lending Fund ;
  - repères de distribution : à chaque date de bilan, les quartiles de chaque mesure sur les véhicules où elle est calculée. Ce sont des repères, jamais des totaux. Les événements ne se comptent pas entre véhicules.

  (4) Source et millésime :
  - les faits de `num.tsv` des archives, relus sans le préfiltre de noms du bloc `lender`. Le fichier `soi` ne sert pas : son coût et sa juste valeur suivent des libellés qui changent d'une taxonomie à l'autre ;
  - concepts : coût, juste valeur, principal, taux d'intérêt, taux capitalisé (PIK), engagement non tiré envers l'émetteur, et les axes de statut de performance et de secteur ;
  - une position : dépôt, identifiant, et autres axes hors statut de performance et secteur ; les lignes « Total » sont écartées ; classe d'instrument par le libellé, comme le bloc `lender` (prêt, capital, non classé) ;
  - faits à la date du bilan du dépôt. Vue `as_known` : le premier dépôt d'un véhicule pour une date l'emporte, un amendement ne la remplace pas.

  (5) Mesures, par véhicule et date de bilan :
  - `bdc_portfolio_fv_to_cost` : somme des justes valeurs ÷ somme des coûts des prêts dont les deux sont balisés ; `partial` si des prêts n'ont pas les deux ;
  - `bdc_portfolio_pik_share` : somme de (principal × taux capitalisé) ÷ somme de (principal × taux total), sur les prêts dont le principal et le taux total sont balisés. Un prêt sans taux capitalisé balisé compte sans intérêts capitalisés : la valeur est une borne basse (`bounded`, base `untagged_counted_as_absent`) ;
  - `bdc_portfolio_non_accrual_share` : somme des coûts des prêts dont le statut de performance balisé dit non productif ou sans accumulation d'intérêts ÷ somme des coûts des prêts. Un dépôt qui ne balise aucun statut n'est pas déterminable (`not_tagged`). Sinon, un prêt sans statut compte comme productif : borne basse ;
  - `bdc_portfolio_unfunded_ratio` : somme des engagements non tirés balisés ÷ somme des justes valeurs de toutes les positions. Aucun engagement balisé : non déterminable ; sinon, borne basse ;
  - `bdc_portfolio_software_share` : somme des justes valeurs des positions dont le membre de l'axe de secteur contient « software » ÷ somme des justes valeurs des positions qui portent un secteur. Calculée si au moins 90 % de la juste valeur porte un secteur, `partial` en dessous, non déterminable sans aucun secteur balisé. Un premier relevé de structure, fait avant tout calcul de valeur, montre que l'axe de secteur est rare dans `num` : cette mesure sera le plus souvent non déterminable.

  (6) Annexe F : trois événements ajoutés à la liste fermée, pour les véhicules de l'univers seulement. Les groupes ne sont pas concernés et F1 à F10 ne changent pas. Seuils de signe et de durée, sans calibrage sur les données :
  - F11 : `bdc_portfolio_fv_to_cost` en baisse deux trimestres de suite ;
  - F12 : `bdc_portfolio_pik_share` (borne basse) en hausse deux trimestres de suite ;
  - F13 : `bdc_portfolio_non_accrual_share` (borne basse) en hausse deux trimestres de suite.

  Chaque événement porte sur trois dates de bilan successives du même véhicule, distantes de 120 jours au plus, et se date à la dernière, comme F1. Si une des trois valeurs manque ou si l'écart dépasse 120 jours, la cellule est non déterminable, jamais « sans événement ». Une cellule par véhicule, événement et date de bilan. Comme le veut l'annexe F, le changement de la liste est signalé en tête de la note de synthèse, avec le diff.

  (7) Limites connues avant calcul :
  - les bornes basses suivent les pratiques de balisage : un changement de balisage peut produire une hausse ;
  - les marques en juste valeur sont lissées, et seulement trimestrielles ;
  - les fonds de data centers de Blue Owl ne publient pas de portefeuille (`not_public`) : le niveau 1 ne voit pas la coentreprise de Meta en Louisiane ;
  - le passif (levier, couverture, rachats demandés et acceptés) n'est pas couvert.

  (8) Corrections de validité, après un premier calcul et avant toute publication. Elles visent des défauts de données vus en contrôlant la couverture. Les événements, leurs seuils de signe et de durée et la vue ne changent pas :
  - prêt : une position que son libellé ne classe pas en capital, que son libellé classe en dette ou qui porte un principal, et qui est financée (coût, juste valeur ou principal). Le libellé seul ne suffisait pas : chez Blackstone Secured Lending, les identifiants ne nomment que l'emprunteur (« ACI Group Holdings, Inc. 1 »), et un seul prêt sur 568 positions était reconnu au 31 mars 2024. Une ligne qui ne porte qu'un engagement non tiré n'est pas un prêt du portefeuille ;
  - couverture : juste valeur ÷ coût exige un coût balisé sur au moins 90 % de la juste valeur des prêts ; les intérêts capitalisés exigent un taux total balisé sur au moins 90 % du principal en dollars. C'est le seuil de 90 % que le point 5 fixait déjà pour la part logiciel ; en dessous, la cellule est non déterminable (`not_tagged`), avec sa couverture dans les drapeaux. Un ratio calculé sur une petite part du portefeuille n'en dit rien ;
  - erreurs d'échelle : un prêt dont le coût ou la juste valeur vaut au moins 500 fois son principal en dollars, ou dont le coût en vaut au plus le 1/500e, est écarté et compté (`scale_errors_excluded`). Une juste valeur très basse reste : un prêt déprécié peut valoir presque rien. Un engagement non tiré supérieur à toute la juste valeur du portefeuille est écarté de même. Exemples : chez Blue Owl Capital Corp au 30 septembre 2023, des engagements balisés mille fois trop haut portaient le ratio à 523 % ; chez HPS Corporate Lending Fund, 15 à 18 prêts par dépôt en 2025.

  (9) Résultats au réassemblage, vue `as_known`, dernier bilan au 30 juin 2026 pour la plupart des véhicules :
  - univers : 198 véhicules et 2 088 couples véhicule × date de bilan. Sont déterminés : juste valeur ÷ coût 1 904 fois, intérêts capitalisés 1 078, engagements non tirés 847, part logiciel 3, prêts sans accumulation d'intérêts jamais. Le statut de performance n'est pas balisé dans `num`, si bien que F13 est non déterminable partout ;
  - repères de l'univers pour juste valeur ÷ coût : la médiane passe de 99,58 % au 31 décembre 2025 à 98,64 % au 31 mars 2026 et 98,72 % au 30 juin 2026 ; le premier quartile, de 97,47 % à 96,66 %. La médiane des intérêts capitalisés (bornes basses) passe de 1,83 % au 30 septembre 2025 à 3,18 % au 30 juin 2026 ;
  - Blue Owl, juste valeur ÷ coût au 30 juin 2026, avec la valeur un an plus tôt :
    - Blue Owl Capital Corp II : 88,56 % (96,94 %) ;
    - Blue Owl Technology Income Corp. : 96,06 % (100,02 %) ;
    - Blue Owl Capital Corp : 96,30 % (98,63 %) ;
    - Blue Owl Technology Finance Corp. : 97,61 % (99,90 %) ;
    - Blue Owl Credit Income Corp. : 98,17 % (99,50 %) ;
  - trois de ces cinq véhicules sont sous le premier quartile de l'univers au 30 juin 2026, Blue Owl Capital Corp II très en dessous. F11 tombe au 30 juin 2026 chez Blue Owl Capital Corp II, Blue Owl Technology Finance Corp., Blue Owl Credit Income Corp. et Blue Owl Technology Income Corp. ;
  - Blue Owl Capital Corp III et Blue Owl Technology Finance Corp. II n'ont plus de bilan dans les archives après le 30 septembre et le 31 décembre 2024 ;
  - les intérêts capitalisés de Blue Owl ne sont pas déterminables : ses véhicules ne balisent pas le taux total. Ses engagements non tirés valent au moins 7,1 % à 12,0 % du portefeuille selon le véhicule ;
  - repères nommés, au 30 juin 2026 : FS KKR Capital Corp 91,01 %, Blackstone Secured Lending Fund 96,34 %, Blackstone Private Credit Fund 96,64 %, Ares Capital Corp 96,66 %, Golub Capital BDC 98,25 %, HPS Corporate Lending Fund 99,08 % ;
  - F11 est fréquent : deux baisses consécutives suffisent. Il ne distingue pas un véhicule à lui seul ; le niveau et l'ampleur de la baisse se lisent à côté.

- **D-0046 — Blue Owl, niveau 3 : nommer le financeur de la coentreprise de Meta en Louisiane, règles fixées avant la recherche.** (1) Décision de l'utilisateur, le 2026-10-10 : « Fais le niveau 3, toujours sans sous-agent ». Le niveau 3 nomme Blue Owl sur le montage de Meta à partir des pièces qui le décrivent, et le relie à ce que les notes de Meta en publient déjà. Meta n'appelle ce montage que « the Venture » : 20 % pour Meta, garanties de valeur résiduelle d'environ 28 Md$, loyers de 12,31 Md$ à partir de 2029 (blocs 3e5dc9af3bd4 et 07588365270c, deux abstentions `no_named_counterparty`). Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Pourquoi la découverte ne l'a pas vu. Les Notes Data Sets ne portent que les notes des états financiers. Un gestionnaire comme Blue Owl Capital Inc. décrit ce genre d'opération dans son rapport de gestion ou dans ses communiqués, hors des notes. Blue Owl Capital Inc. n'est donc pas un candidat de D-0036. Ses véhicules le sont (Blue Owl Real Estate Net Lease Trust au rang 21 ; véhicules « Blue Owl GP Stakes Stargate » par leurs Form D).

  (3) Sources. Recherche plein texte d'EDGAR, du 2025-10-01 au 2026-10-07, tous formulaires :
  - « "Beignet Investor" » ;
  - « "Blue Owl" Hyperion » ;
  - « "Blue Owl" "Richland Parish" » ;
  - « "Blue Owl" "Meta Platforms" » ;
  - « "Blue Owl" », limitée aux dépôts de Meta (CIK 1326801).

  S'y ajoutent les rapports périodiques de Blue Owl Capital Inc. de la période : 10-Q du troisième trimestre 2025, 10-K 2025, 10-Q des deux premiers trimestres 2026. Chaque pièce se tire une fois, en cache, sous les règles réseau habituelles (journal, cinq requêtes par seconde au plus, pause après un refus).

  (4) Unités de lecture. Dans chaque pièce retenue (document principal ou annexe), les paragraphes qui nomment un terme du lexique (« Beignet », « Hyperion », « Richland Parish », « Meta » en mot entier et avec sa majuscule), avec les deux paragraphes qui précèdent et les deux qui suivent ; les fenêtres qui se chevauchent se fondent. C'est la règle du texte autour des faits du bloc `text` (D-0029). Plafond : 40 unités, dans l'ordre des dates de dépôt ; au-delà, `not_processed`. Une pièce où « Meta » n'a aucun rapport avec Meta Platforms se ferme par une abstention motivée.

  (5) Lignes. Conventions de lecture habituelles : citation mot pour mot, contrepartie nommée dans le bloc, la société déclarante écrite « the Company ». Dans une pièce de Blue Owl Capital Inc., « the Company » est le gestionnaire ; les fonds qu'il gère et les véhicules du montage s'écrivent comme le bloc les nomme. Un montant égal à un fait balisé du bloc renvoie à ce fait.

  (6) Identification de « the Venture ». La coentreprise des notes de Meta n'est identifiée à un montage décrit ailleurs que si un extrait cité en confirme au moins trois traits : la Louisiane (ou Richland Parish) ; une formation ou une annonce en octobre 2025 ; 20 % pour Meta, ou 80 % pour l'autre membre ; Meta nommée comme membre ou comme locataire. L'identification se consigne dans `config.yaml` (`identified_ventures`), avec les extraits des deux côtés. Les abstentions de Meta restent : ses notes ne nomment personne. Les arêtes ne naissent que des lignes de blocs qui nomment leurs parties.

  (7) Rattachements. Les fonds gérés par Blue Owl ne forment pas un groupe économique (D-0045, point 3). Un véhicule dont la dénomination ne porte pas « Blue Owl » (Beignet Investor LLC, par exemple) n'entre dans le regroupement de présentation de la plateforme que sur un extrait qui le dit détenu ou géré par des fonds de Blue Owl.

  (8) Amendement après les comptes de la recherche, avant toute lecture. Il ne se fonde que sur les formulaires et les nombres de résultats. Les requêtes rendent 3 538, 790, 1, plus de 10 000 et 2 résultats. Ce sont pour l'essentiel des relevés de portefeuille : NPORT-P, N-CSR et N-CSRS, N-MFP3, 13F-HR, N-PX, 486BPOS, POS EX, et les 11-K des plans d'épargne, où les obligations de Beignet Investor LLC et les actions de Meta figurent en lignes de titres. Deux règles s'ajoutent :
  - ces relevés ne décrivent pas de montage et ne se lisent pas : motif `out_of_scope`, compté par formulaire ;
  - « Hyperion » seul ne qualifie pas une fenêtre, car il désigne aussi Hyperion Refinance S.à r.l. (Howden), emprunteur des BDC de Blue Owl. Une fenêtre ne se lit que si elle nomme « Beignet », « Richland Parish » ou « Meta ».

  Restent 37 pièces de formulaires narratifs (10-Q, 10-K, 8-K et annexes, 424B3, N-14 8C, DEF 14A), plus les rapports périodiques de Blue Owl Capital Inc. Elles se tirent toutes, et la règle des fenêtres s'y applique mécaniquement.

  (9) Second amendement, après le premier décompte des fenêtres et avant toute lecture. Dans ses propres dépôts, Meta se nomme « Meta » à chaque paragraphe : son 10-Q du troisième trimestre 2025 et sa DEF 14A de 2026 donnaient 63 fenêtres, dont 24 au-delà du plafond. Le nom du déposant ne qualifie donc pas une fenêtre dans ses propres pièces, et « Blue Owl » s'ajoute aux termes qualifiants hors des pièces de Blue Owl :
  - dans une pièce de Meta, une fenêtre se lit si elle nomme « Blue Owl », « Beignet » ou « Richland Parish » ;
  - dans une pièce d'un déposant « Blue Owl », si elle nomme « Meta », « Beignet » ou « Richland Parish » ;
  - ailleurs, si elle nomme l'un de ces cinq termes.

  Les rapports périodiques de Blue Owl Capital Inc. de la période ne nomment ni Meta, ni Beignet, ni Richland Parish : aucune fenêtre.

  (10) Résultats de la lecture et de l'intégration :
  - 40 pièces narratives tirées ; 2 fenêtres seulement (aucune dans les rapports de Blue Owl Capital Inc. ni dans les BDC de Blue Owl, que « Hyperion » rattachait à Hyperion Refinance) ; 7 lignes, aucune rejetée. 52 exclusions `out_of_scope` : relevés de portefeuille par formulaire, pièces sans fenêtre ;
  - la note 13 du 10-Q de Meta du troisième trimestre 2025 nomme le financeur : « an affiliate of funds managed by Blue Owl Capital, Inc. (the Investor) », 80 %, 7,0 Md$ en numéraire ; Meta apporte 4,3 Md$ d'actifs, reçoit une distribution unique de 2,6 Md$ et garde 20 % ; baux à partir de 2029 (environ 12,3 Md$ sur quatre ans, jusqu'à 20 ans) ; garantie de valeur résiduelle sur seize ans, seuil de départ 28 Md$. Les notes suivantes de Meta n'écrivent plus que « the Venture » ;
  - le 10-Q de Blue Owl Real Estate Net Lease Trust du troisième trimestre 2025 nomme le montage : Project Beignet Holdings (« Beignet JV »), détenu à 80,0 % par Beignet Investor LLC, elle-même détenue à 63,0 % indirectement par ce fonds, qui s'engage pour 1,53 Md$ de fonds propres ; Beignet Investor LLC a émis 27,29 Md$ d'obligations garanties à 6,581 %, échéance 30 mai 2049 ;
  - identification consignée (`identified_ventures`) : la Louisiane, octobre 2025, la répartition 20/80 et Meta locataire concordent. Project Beignet Holdings entre au registre par extrait (`own_entities`) ; Beignet Investor LLC, détenue par un fonds de Blue Owl, rejoint le regroupement de présentation de la plateforme ;
  - effets : un cycle documenté de plus, 25 → 26 : Meta → Blue Owl Capital, Inc. par les baux et la garantie, Blue Owl Capital, Inc. → Meta par la distribution, concomitants, en « relation commerciale doublée d'un financement ». Pour Meta, l'issue E.6 compte deux cycles au lieu d'un. Paires (64), paires à financement documenté (13) et événements des groupes (169) ne changent pas ;
  - à lire ensemble, sans les additionner : les obligations (27,29 Md$, échéance 2049) et le seuil de départ de la garantie de Meta (28 Md$) sont du même ordre, alors que le premier bail ne court que quatre ans.

- **D-0047 — Blue Owl, niveau 2 : le passif des BDC (couverture, levier, rachats demandés et acceptés, interruptions), règles fixées avant tout calcul et toute lecture.** (1) Décision de l'utilisateur, le 2026-10-10 : « Fais le niveau 2, toujours sans sous-agent ». Le niveau 1 (D-0045) lisait l'actif des BDC. Le niveau 2 lit leur passif : ce que les véhicules doivent, et ce que leurs porteurs demandent à récupérer. Lecture et calcul par l'exécutant, sans sous-agent.

  (2) Périmètre : bloc `lender_liabilities` dans `scope`. Univers, vue, plateforme et repères de D-0045 (point 3), inchangés :
  - toutes les BDC des 21 archives en cache, soit 209 véhicules et 2 395 dépôts ; un véhicule est un déclarant ;
  - aucune somme entre véhicules ; à chaque date, les quartiles d'une mesure se prennent sur les véhicules où elle est calculée.

  (3) Relevé de structure, fait avant ces règles et sans calculer de valeur (présence des concepts, ordre de grandeur) :
  - concepts non dimensionnels à la date du bilan : `Liabilities` dans 2 381 dépôts, l'actif net (`AssetsNet` ou `StockholdersEquity`) dans 2 310 ;
  - le ratio de couverture standard (`InvestmentCompanySeniorSecurityIndebtednessAssetCoverageRatio`) dans 940 dépôts, chez 98 véhicules sur 209. Tous les véhicules de Blue Owl et les six repères le publient à chaque date, sauf un dépôt d'Ares Capital ;
  - la dette n'a pas de concept total commun : `LongTermDebt` (1 322 dépôts), `LineOfCredit` (913), `DebtInstrumentCarryingAmount` (855) et une dizaine d'autres, souvent pour une partie de la dette seulement. Le levier ne se reconstruit donc pas ligne à ligne ;
  - ordre de grandeur du ratio balisé : 930 valeurs entre 1 et 10, 3 entre 10 et 100, 1 entre 100 et 1 000, 2 entre 1 000 et 10 000, 4 sous 1.

  (4) Mesures de bilan, depuis `num.tsv`, sans requête. Par véhicule et date de bilan, vue `as_known`, faits non dimensionnels à la date du bilan du dépôt :
  - `bdc_liab_asset_coverage` : le ratio de couverture des titres de créance de premier rang publié par le véhicule (loi de 1940, articles 18 et 61). Seul le concept standard sert, pas les concepts propres aux déclarants. Il s'écrit en ratio : 2,0 pour 200 %. Règle d'échelle : de 100 à moins de 1 000, c'est un pourcentage écrit en nombre (÷ 100) ; de 1 000 à moins de 10 000, un montant par tranche de 1 000 $ de dette (÷ 1 000). Sous 1, ou à 10 000 et plus, la cellule est non déterminable ;
  - `bdc_liab_debt_to_net_assets` : dette de premier rang ÷ actif net, déduite du ratio : 1 ÷ (couverture − 1). La couverture vaut (actif net + dette de premier rang) ÷ dette de premier rang ; c'est donc le levier au sens de la loi. Non déterminable si la couverture l'est, ou si elle vaut 1 ou moins ;
  - `bdc_liab_liabilities_to_net_assets` : passif total ÷ actif net (`AssetsNet`, à défaut `StockholdersEquity`). Il majore le levier, car le passif comprend aussi les intérêts courus, les frais dus au gestionnaire, les achats de titres non réglés et les distributions à payer. Non déterminable si l'actif net manque ou n'est pas positif.

  (5) Offres de rachat. Une BDC non cotée rachète ses parts par des offres publiques, en général trimestrielles et plafonnées à 5 % des parts. Chaque offre se dépose sous Schedule TO (SC TO-I), et un amendement final en publie le résultat (règle 13e-4(c)(4)) :
  - inventaire : la liste des dépôts EDGAR de chaque véhicule de l'univers (`submissions`), une requête par véhicule, plus les pages anciennes si la liste récente ne remonte pas au 1er octobre 2022 ;
  - une offre : un SC TO-I et les SC TO-I/A qui le suivent jusqu'au SC TO-I suivant du même véhicule. Fenêtre : SC TO-I déposés du 2022-10-01 au 2026-10-07 ;
  - lecture : le document principal du dernier SC TO-I/A de chaque offre ; s'il ne donne pas le résultat, l'amendement qui le précède. Sans résultat, les mesures et F15 sont non déterminables, jamais « sans événement ». Si l'amendement lu ne donne pas le maximum de l'offre, le document principal du SC TO-I ;
  - relevés, chacun avec sa citation mot pour mot : parts (ou montant) valablement apportées et non retirées, parts (ou montant) acceptées, maximum de l'offre, date d'expiration. Un rapport ne se calcule qu'entre deux grandeurs de même unité, parts ou dollars. Les classes de parts s'additionnent quand le document ne donne que leur détail ;
  - mesures par offre, datées à l'expiration et connues au dépôt de l'amendement lu : `bdc_tender_acceptance_ratio` (acceptées ÷ apportées) et `bdc_tender_demand_ratio` (apportées ÷ maximum de l'offre).

  (6) Annexe F : trois événements ajoutés à la liste fermée, pour les véhicules de l'univers seulement. Seuils de signe et de durée, sans calibrage :
  - F14 : `bdc_liab_asset_coverage` en baisse deux trimestres de suite, avec les règles de dates de F11 (trois dates de bilan successives, 120 jours au plus entre deux) ;
  - F15 : une offre dont les parts acceptées sont inférieures aux parts apportées, ou dont l'amendement annonce une réduction au prorata. Une cellule par offre ;
  - F16 : l'interruption d'un programme régulier d'offres. Il faut au moins quatre offres successives, chacune déposée 120 jours au plus après la précédente, puis aucune nouvelle offre dans les 120 jours qui suivent la dernière. Une cellule par offre qui clôt une série d'au moins quatre, datée au dépôt de cette offre plus 120 jours ; non déterminable si ces 120 jours ne sont pas écoulés à `as_of`. Une inscription en bourse (8-A12B) ou une sortie du régime (N-54C, ou formulaire 15) déposée dans l'intervalle ferme la cellule « sans événement », avec son motif : le programme s'arrête alors parce que le véhicule cote ou disparaît, pas parce qu'il retient ses porteurs.

  F16 se lit dans l'inventaire seul, sans texte. Comme le veut l'annexe F, le changement de la liste est signalé en tête de la note de synthèse, avec le diff.

  (7) Annonces. Des 8-K se lisent pour nommer la cause d'une interruption, et les fusions ou suspensions annoncées : document principal et annexes 99, si le 8-K porte l'un des items 1.01, 1.02, 2.01, 3.03, 7.01 ou 8.01.
  - quels 8-K : ceux d'un véhicule où F16 tombe, déposés entre sa dernière offre et la date de l'événement plus 30 jours ; ceux des véhicules de Blue Owl, sur toute la fenêtre ;
  - unités : les paragraphes qui nomment « tender offer », « repurchase », « redemption », « merger » ou « suspend », avec deux paragraphes de part et d'autre, fondus quand ils se chevauchent (règle de D-0046, point 4). Plafond de 40 unités : d'abord les véhicules où F16 tombe, puis ceux de Blue Owl, du plus récent au plus ancien ; au-delà, `not_processed` ;
  - relevés : ce qui est annoncé (suspension ou fin des rachats, accord de fusion, abandon de fusion, fusion réalisée, inscription en bourse, remboursement par distributions, autre), la date et la citation mot pour mot. Ces relevés ne créent ni arête ni mesure : ils motivent les cellules F16 et s'affichent dans la synthèse.

  (8) Limites connues avant calcul :
  - le ratio de couverture n'est publié que par 98 véhicules sur 209 : ses quartiles portent sur ces véhicules, qui ne sont pas tirés au hasard ;
  - le passif total majore le levier ;
  - les offres ne concernent que les véhicules non cotés qui en font : une BDC cotée rachète en bourse, sans demandes à mesurer ;
  - les rapports entre demandes et rachats sont trimestriels et ne disent pas qui demande ;
  - la lecture des 8-K est plafonnée, et ne couvre les véhicules hors Blue Owl que là où F16 tombe.

  (9) Corrections et précisions, après un premier calcul des mesures de bilan et l'inventaire des offres, avant toute lecture d'un résultat d'offre et avant toute publication. Les événements, leurs seuils et la vue ne changent pas :
  - actif net : six véhicules balisent `AssetsNet` avec le signe contraire, sur 55 dates de bilan (Hercules Capital et Sixth Street Specialty Lending notamment). Un actif net négatif dont la valeur absolue égale actif total − passif total, à 1 % près, est une erreur de signe : sa valeur absolue sert. `Assets` s'ajoute aux concepts relevés pour ce contrôle ;
  - couverture : la dette de premier rang ne dépasse pas le passif total, si bien que la couverture vaut au moins 1 + actif net ÷ passif total. Un ratio publié sous ce plancher, à 2 % près (la loi compte la dette au principal, le bilan à sa valeur comptable), n'est pas le ratio du véhicule : la cellule est non déterminable (`conflicting`). C'est le cas de 43 valeurs, dont 37 égales au seuil légal (1,5 ou 2,0) balisé à la place du ratio, chez Kayne Anderson BDC, PhenixFin, Silver Point Specialty Lending Fund, Lafayette Square et First Eagle Private Credit Fund notamment. Sept valeurs rondes (2,0 six fois, 1,5 une fois) passent le contrôle et restent, faute de preuve contraire ;
  - offres : le SC TO-I sert aussi aux offres sur des obligations (New Mountain Finance, deux offres) et sur des actions de préférence (Prospect Capital, une offre). Seules comptent les offres sur les parts du véhicule (actions ordinaires, parts de toutes classes). La classe se lit sur la page de garde du SC TO-I (« Title of Class of Securities ») ou, à défaut, à son item 2(b). Les trois autres offres sont écartées (`out_of_scope`) et ne comptent pas dans les séries de F16. Pour ces séries, 79 SC TO-I antérieurs à la fenêtre ont été tirés, pour lire leur classe ;
  - dates : aucun dépôt postérieur à `as_of` ne compte, ni pour les offres ni pour les motifs de F16. Une offre sans amendement dont le SC TO-I a moins de 60 jours à `as_of` est réputée encore ouverte (`end_offset_exceeded`) ; plus ancienne, son résultat n'est pas publié (`not_disclosed`) ;
  - volumes : l'inventaire compte 64 244 dépôts pour les 209 véhicules (209 requêtes). La fenêtre compte 625 offres chez 70 véhicules, dont 622 sur des parts chez 68 véhicules ; 570 ont au moins un amendement. 1 357 documents tirés (SC TO-I et amendements), sans échec ;
  - méthode de lecture : pour chaque offre, des motifs fixés proposent un relevé (phrases qui portent « tendered », « accepted », « purchased », « pro rata », « up to », « expired »). L'exécutant contrôle chaque proposition sur les phrases citées et la corrige au besoin ; chaque citation est vérifiée mot pour mot dans le document.

  (10) Précisions de lecture, prises pendant la lecture des amendements. Elles portent sur l'endroit et la forme où le résultat est publié, jamais sur sa valeur, et s'appliquent à toutes les offres. Les événements et leurs seuils ne changent pas :
  - rattachement : un amendement revient à l'offre dont il désigne la date de dépôt (« Schedule TO filed ... on May 1, 2024 »), à trois jours près, et non plus à l'offre ouverte juste avant lui. Plusieurs fonds (HPS Corporate Lending Fund, Star Mountain, Bain Capital) déposent le résultat d'une offre après l'ouverture de la suivante : le rattachement par l'ordre des dépôts donnait des expirations antérieures à l'offre. 39 amendements changent d'offre ; 169 n'ont pas de date lisible et gardent le rattachement par l'ordre des dépôts ;
  - communiqués : quand le document principal renvoie le résultat à un communiqué déposé en annexe, l'annexe se lit aussi (23 amendements, 29 annexes, 14 requêtes) ;
  - unités : un plafond exprimé en pourcentage des parts en circulation se compare aux parts apportées exprimées dans le même pourcentage, à la même date de référence. Un taux d'acceptation publié tel quel (« proration factor of approximately 69.3% », « accepted ... approximately 44.3% of the Shares ») sert de rapport acceptées ÷ apportées quand les parts apportées ne sont pas chiffrées ;
  - formes : « No Shares were validly tendered » vaut zéro part apportée (pas de rapport, pas de réduction : F15 sans événement). Le paiement des parts apportées (« payment of the purchase price of the Shares tendered was made », « the net asset value ... of the total amount of the Shares tendered ») vaut acceptation de toutes les parts apportées : les mêmes modèles annoncent la réduction au prorata quand elle a lieu (Onex Direct Lending, Carlyle Credit Solutions). Une estimation publiée avant le décompte final se relève comme telle, sans acceptation ;
  - contrôle : chaque ligne de relevé a été relue ; les citations complètes l'ont été pour la première offre de chaque véhicule et pour toute offre dont le relevé était incomplet, réduit au prorata ou hors calendrier. 98 relevés sur 590 portent une correction de l'exécutant, dont la décision explicite sur chaque phrase de réduction au prorata. Toutes les citations sont vérifiées mot pour mot (`python -m pipeline.lender_liabilities finalize`).

  (11) Résultats au réassemblage, vue `as_known` :
  - bilans : 209 véhicules, 2 380 couples véhicule × date. Couverture retenue 889 fois ; non balisée 1 444 ; contraire à l'identité du bilan 43 ; hors échelle 4. Passif ÷ actif net calculé 2 271 fois, dont 55 après correction du signe ;
  - quartiles de dette ÷ actif net au 30 juin 2026, sur les 73 véhicules qui publient leur couverture : 0,86 / 1,03 / 1,22. Passif ÷ actif net sur 171 véhicules : 0,77 / 1,08 / 1,31 ;
  - Blue Owl, dette ÷ actif net au 30 juin 2026 (un an plus tôt) : Blue Owl Capital Corp 1,15 (1,23) ; Blue Owl Technology Finance Corp. 0,97 (0,61) ; Blue Owl Credit Income Corp. 0,93 (0,87) ; Blue Owl Technology Income Corp. 0,87 (0,79) ; Blue Owl Capital Corp II 0,27 (0,70). Repères : Ares Capital 1,16 (1,01), Blackstone Secured Lending 1,28 (1,13), Blackstone Private Credit 0,82 (0,68), Golub Capital BDC 1,24 (1,30), FS KKR 1,27 (1,30), HPS Corporate Lending 1,02 (0,94). F14 tombe 182 fois dans l'univers, dont au 30 juin 2026 chez Blue Owl Credit Income, Blue Owl Technology Income et Blue Owl Technology Finance ;
  - offres : 622 offres de parts chez 68 véhicules ; 590 ont un amendement, 579 un résultat lu. F15 : 84 offres réduites au prorata, 478 servies en entier, 23 encore ouvertes à `as_of`, 37 sans résultat publié ou complet (parts acceptées non chiffrées chez NexPoint Capital, par exemple). Par trimestre d'expiration, les offres réduites passent de 3 à 5 par trimestre en 2023-2025 à 11 au premier trimestre 2026 et 18 au deuxième ; la demande médiane rapportée au plafond passe de 0,10-0,32 en 2025 à 0,58 puis 0,64 ;
  - Blue Owl Credit Income Corp. : 21,9 % des parts demandées au premier trimestre 2026 (4,38 fois le plafond de 5 %), 22,8 % des parts apportées rachetées ; 18,8 % au deuxième (3,76 fois), 26,6 % rachetées. Blue Owl Technology Income Corp. : 40,4 % demandées (8,08 fois), 14,4 % rachetées ; puis 38,1 % (7,62 fois), 13,1 %. Jusqu'à l'offre close le 31 décembre 2025 (le 8 janvier 2026 pour Technology Income), les deux fonds avaient racheté toutes les parts apportées ;
  - repères non cotés : Blackstone Private Credit Fund, 1,39 fois le plafond au premier trimestre 2026, tout racheté, puis 2,06 fois, 48,5 % rachetées ; HPS Corporate Lending Fund, 1,85 fois (54,0 %), puis 2,66 fois (37,6 %) ;
  - F16 : 6 interruptions sur 473 cellules (423 sans événement, 44 dont les 120 jours ne sont pas écoulés). Blue Owl Capital Corp II : dernière offre en août 2025 (1,19 fois le plafond, tout racheté grâce à la marge de 2 % de la règle 13e-4(f)(1)(ii)), puis accord de fusion avec Blue Owl Capital Corporation le 5 novembre 2025, sans nouvelle offre avant la fusion, et fusion abandonnée le 18 novembre ; MSC Income Fund (rachats suspendus en vue d'une cotation) ; Steele Creek Capital (plan de désendettement en vue d'une liquidation probable) ; Hancock Park Corporate Income et Audax Credit BDC (aucune cause lue) ; Stellus Private Credit BDC (offre suivante 133 jours après la précédente) ;
  - 8-K : 40 unités lues (14 pour les interruptions, 26 pour Blue Owl), 305 8-K ou fenêtres au-delà du plafond (`not_processed`). Les lettres de Blue Owl aux porteurs, hors SC TO-I, annoncent pour le troisième trimestre 2026 une demande estimée de 16,8 % des parts chez Blue Owl Credit Income (environ 30 % servis) et de 39,0 % chez Blue Owl Technology Income (environ 13 % servis). Le gestionnaire attribue la demande de Blue Owl Technology Income à une base de porteurs concentrée et aux craintes sur les éditeurs de logiciels face à l'IA ;
  - requêtes : 209 listes de dépôts, 1 357 documents d'offres, 14 annexes, 123 pour les 8-K. Exclusions : `out_of_scope` 3 (offres sur obligations ou actions de préférence), `not_processed` 305 (8-K au-delà du plafond).

- **D-0048 — Ajout de groupes : Nebius (NBIS) et IREN (IREN), règles fixées avant tout calcul.** (1) Décision de l'utilisateur, le 2026-10-11 : « Ok on continue avec Nebius et IREN ». Ils suivent TeraWulf, Cipher et Core Scientific dans l'ordre de §14 (hébergeurs endettés). Jusqu'ici, le bloc `foreign` ne les lisait qu'au titre de nœuds de la chaîne (D-0042 : six unités, aucune mesure propre, aucune paire avec leurs clients). Lecture séquentielle par l'exécutant, sans sous-agent, un commit par groupe.

  (2) Configuration et date de connaissance :
  - `company_tickers.json` (2026-10-07) résout NBIS vers le CIK 1513845 (Nebius Group N.V.) et IREN vers le CIK 1878848 (IREN Ltd). Les deux groupes entrent dans `config.yaml`, avec `group_entry` au 2026-10-11 ;
  - l'exécution garde l'as_of du 2026-10-07. Ce qui est tiré le 2026-10-11 se range sous cet as_of ; les dépôts postérieurs sont écartés ; le journal garde l'heure réelle des requêtes.

  (3) Nebius, rupture de périmètre. Le CIK 1513845 est celui de Yandex N.V. jusqu'à la cession de ses activités russes, achevée le 12 juillet 2024 (20-F 2024, 0001558370-25-005991 : « July 12, 2024, at which the Company sold its remaining stake in the Divested Businesses »). Les rapports antérieurs présentent une autre entité économique. Même règle que les fusions inversées (D-0043, point 3), écrite dans `config.yaml` (`history_breaks`) :
  - hors du groupe : les rapports périodiques dont la période se clôt avant le 12 juillet 2024 et les autres dépôts antérieurs à cette date (classe d'inventaire `pre_combination`, hors des séries et du texte) ;
  - l'exercice 2024 reste, puisqu'il se clôt après la cession ; ses états présentent les activités cédées en activités abandonnées jusqu'au 12 juillet ;
  - le groupe porte `history_left_censored`.

  (4) IREN, changement de référentiel. IREN publiait en IFRS (20-F des exercices clos les 30 juin 2022 à 2024, et 6-K), puis en US GAAP à partir de l'exercice clos le 30 juin 2025 (10-K 0001878848-25-000063 : « Effective this fiscal year, we have transitioned from International Financial Reporting Standards [...] to GAAP »). L'invariant (f) interdit de mêler les deux cadres :
  - hors des séries : les rapports dont la période se clôt avant le 1er juillet 2024 et les dépôts antérieurs à cette date (`history_breaks`, même règle). Leurs notes en IFRS restent lues par le bloc `foreign` (D-0042) ;
  - le groupe porte `history_left_censored` ; ses séries commencent avec l'exercice 2025.

  (5) Rapports annuels sans rapports trimestriels :
  - Nebius est un émetteur privé étranger : un 20-F par an, aucun rapport trimestriel déposé (la règle 13a-13 ne s'applique pas ; les 6-K sont furnished, sans états balisés). IREN n'a déposé de 10-Q qu'à partir du trimestre clos le 30 septembre 2025 ;
  - le 20-F entre dans les rapports périodiques du pipeline (inventaire, archives XBRL, dates de publicité de la vue `as_known`, signaux) ;
  - un exercice qui n'a qu'un rapport annuel se découpe en quatre trimestres de trois mois, comme les exercices synthétiques. Sinon l'exercice entier passerait pour un trimestre, et des montants annuels pour des montants trimestriels. Aucun groupe présent n'a un tel exercice dans la fenêtre (vérifié : seul AMD en 1993) ;
  - `reporting_start` : les trimestres de Nebius sont `not_applicable`, avec la règle 13a-13 pour pièce ; ceux d'IREN commencent au 1er juillet 2025 (premier 10-Q, 0001878848-25-000081) ;
  - les signaux du rapport annuel (faiblesse du contrôle interne, continuité d'exploitation) se lisent au trimestre de clôture de l'exercice, comme pour un 10-K.

  (6) Textes lus :
  - 20-F de Nebius (exercices 2024 et 2025, et l'amendement de 2026) : notes par rôles XBRL, comme les 10-K. Item 15 (Controls and Procedures) en bloc `item_9a` ; Item 7.B (Related Party Transactions) en bloc `item_404`, l'Item 404 de Reg S-K ne s'appliquant pas aux émetteurs étrangers ; Item 10.C (Material Contracts) en bloc `item_8k_101`. Mêmes contenus, mêmes règles de lecture. Les états d'un 20-F sont audités (niveau A) ;
  - IREN, à partir de son 10-K de l'exercice 2025 : 10-K, 10-Q, 8-K et DEF 14A, règles des groupes présents ;
  - 6-K (Nebius après le 12 juillet 2024 ; IREN du 1er juillet 2024 à son dernier 6-K) : un 6-K n'a pas d'items. Unités : les paragraphes du document principal et des annexes 99 qui nomment un terme du lexique fixé ici, avec deux paragraphes de part et d'autre, fondus quand ils se chevauchent (règle de D-0046) ; bloc `foreign_6k_text`. Lexique : « agreement », « contract », « financing », « convertible », « notes due », « credit facility », « loan », « warrant », « offering », « lease », et les noms des groupes et des laboratoires de `config.yaml`. Plafond : 80 unités par groupe, du plus récent au plus ancien ; au-delà, `not_processed`. Un 6-K est furnished (niveau E), sauf incorporation par référence lue dans le 6-K (D-0042).

  (7) Découverte et `foreign` : comme en D-0043, point 6. Les lignes déjà lues pour ces déposants vont à leur groupe ; leurs unités encore dans la file en sortent (`out_of_scope`) ; côté client, la recherche reste incomplète, puisque le scan des Notes Data Sets n'a jamais cherché leurs noms (`search_incomplete`).

  (8) Limites connues avant calcul :
  - Nebius n'a pas de séries trimestrielles, et deux exercices seulement dans son périmètre actuel (2024, dont la première moitié avec les activités cédées, et 2025) ;
  - les séries d'IREN commencent avec l'exercice 2025 ;
  - l'Item 15 du 20-F 2024 de Nebius dit déjà une difficulté de contrôle (« we were unable to complete the implementation of all necessary controls for our newly constituted group during 2024 ») : vu en relevant la date de la cession, avant toute règle de lecture. La lecture de l'Item 15 dira s'il s'agit d'une faiblesse significative.

  (9) Précisions d'application, écrites avant de construire les unités et les blocs (aucun bloc ni aucune unité vus) :
  - délimitation du 20-F : l'Item 15 court jusqu'au premier titre d'Item 16 (16, 16A à 16K) ; l'Item 7.B et l'Item 10.C se cherchent à l'intérieur de leur item, de leur titre au titre suivant de même rang (« C. Interests of Experts and Counsel » ; « Exchange Controls », « Taxation » et suivants), lettrés ou non. Le 20-F de Nebius ne les lettre pas : « Related Party Transactions », « Material Contracts » ;
  - lexique des 6-K : mots entiers, casse indifférente, singulier et pluriel écrits dans `config.yaml` (`foreign_6k`), au lieu d'une règle de pluriel dans le code ;
  - un nom de groupe ne qualifie pas un paragraphe du groupe qui dépose : jamais le nom du déposant lui-même (même règle que D-0046, point 9). Sinon chaque paragraphe d'un communiqué de Nebius ou d'IREN ferait une unité. « Iris Energy », dénomination d'IREN jusqu'au 29 novembre 2024 (submissions, `formerNames`), est un nom d'IREN ;
  - noms des groupes : ceux du lexique de la découverte (onze groupes de l'annexe B, laboratoires, Stargate, avec leur casse) et ceux des groupes ajoutés depuis (TeraWulf, Cipher, Core Scientific, Nebius, IREN) ;
  - pièces lues : le document principal et les annexes dont l'en-tête SGML donne un type EX-99, au format texte (htm, html, txt). Une image ou un PDF n'est pas lu : exclusion `out_of_scope`, comptée ;
  - un 6-K sans aucun paragraphe qualifiant sort avec `out_of_scope` ; les unités entrent dans la classe 3 (texte du groupe), du 6-K le plus récent au plus ancien, et le plafond de 80 compte dans cet ordre.

  (10) Lecture, sans sous-agent, un commit par groupe (5f0268d, 2052e8f) :
  - Nebius : 100 blocs (22 de rapports et de pièces, 78 unités 6-K), tous lus, 166 lignes retenues (111 observations, 55 abstentions) ; 45 blocs portent au moins une observation ;
  - IREN : 149 blocs (71 de rapports et de pièces, 78 unités 6-K), 145 lus, 227 lignes (149 observations, 78 abstentions) ; 67 blocs avec observation. Les 4 blocs non lus sont des corps d'actes de fiducie (pièces 4 des obligations 2031, 2032 et 2033) dont l'en-tête ne nomme que le déposant et le fiduciaire (`financial_parties_only`, §11.1). Aucune ligne rejetée dans les deux groupes ;
  - 6-K : 761 unités qualifiantes (Nebius 490, IREN 271) ; 160 sous le plafond, 80 par groupe (Nebius : 6-K du 20 mai au 1er octobre 2026 ; IREN : du 20 mars au 30 juin 2025), 601 au-delà (`not_processed`) ; 7 6-K de Nebius sans paragraphe qualifiant (`out_of_scope`). 149 unités viennent de 6-K incorporés par référence dans des enregistrements S-8 ou F-3 (niveau C), 11 sont furnished (niveau E).

  Relations avec des groupes déjà présents :
  - Microsoft : contrat de cinq ans de Nebius (effet au 7 septembre 2025, centre de Vineland), « up to $17,392.9 » millions de frais estimés, tranches livrées en novembre 2025 et février 2026 ; contrat d'IREN du 2 novembre 2025 (GPU dédiés à Childress, 9,7 Md$, cinq ans en moyenne), exécuté par une filiale (IE US Hardware 3 Inc.) et adossé au financement de ses GPU ;
  - Meta : contrat de Nebius du 1er novembre 2025 (capacité dédiée de cinq ans, environ 2,9 Md$, deux tranches livrées) et contrat du 13 mars 2026 (12 Md$ de capacité dédiée, plus un engagement de Meta d'acheter jusqu'à 15 Md$ de capacité invendue) ;
  - NVIDIA : bon de souscription préfinancé de 2,0 Md$ émis par Nebius le 11 mars 2026 (21 065 936 actions de classe A). Les achats de GPU d'IREN nomment la marque, pas le vendeur : lignes sans famille, comme en D-0042 ;
  - côté fournisseurs hors groupes présents : Dell (Dell Marketing L.P. et Dell Canada Inc.) pour IREN, 5,8 Md$ en novembre 2025, 3,5 Md$ en mars 2026 et 1,6 Md$ en mai 2026 ; Bitmain pour IREN, contrats de machines de 2023 à 2025 (19,6 M$ à 411,35 M$ par contrat ou levée d'option).

  Signaux d'IREN antérieurs à ses séries (point 4) : incertitude significative sur la continuité d'exploitation dans les comptes IFRS aux 31 décembre 2024 (6-K/A retraité) et 31 mars 2025 ; retraitement des comptes des exercices 2022 à 2024 annoncé le 20 mars 2025 (reclassement des ventes de bitcoins minés) ; défaut des financements d'équipement à recours limité de deux filiales (séquestre nommé le 3 février 2023) et demande pour abus de NYDIG encore pendante au 31 mars 2025. Ils sont lus et publiés en observations. La continuité d'exploitation ne fait pas d'événement F10 : le signal se lit dans les rapports périodiques (10-K, 10-Q, 20-F), et les comptes intermédiaires en IFRS de ces trimestres ne sont publiés que par 6-K. Le retraitement est repris par le signal de correction d'erreur (point 12).

  (11) Corrections faites en lecture :
  - clé du bon préfinancé de NVIDIA : deux blocs de Nebius portaient la clé `nbis:prefunded_warrants_2026` alors que D-0042 avait relevé le même instrument sous `nebius:nvidia_prefunded_warrant`. La déduplication d'une même mesure exige la même clé (même montant, même stade, à 45 jours près) : sans correction, les 2,0 Md$ comptaient deux fois sur la relation Nebius–NVIDIA. Les deux blocs sont repassés (passe du 2026-10-11T09:00:00Z) avec la clé de D-0042 et la date du 11 mars 2026 ; le chargement ne garde que la passe la plus récente ;
  - un lot d'IREN (8 blocs) a été soumis deux fois. Les lignes en double, identiques à la ligne près, sont retirées ; aucun contenu ne change ;
  - une contrepartie dérivable par renvoi explicite doit figurer dans le bloc qui la porte. Deux lignes d'IREN restent donc anonymes : les acomptes de matériel de minage du rapport de gestion au 31 mars 2025 (583,6 M$ sur neuf mois, renvoi à la section « Hardware Purchases ») et le défaut des financements à recours limité (prêteur non nommé dans le bloc). Bitmain et NYDIG sont nommés dans leurs propres blocs ;
  - IREN, 6-K de juin 2025 : la clôture des convertibles 2029 (550 M$) porte le montant ; le lancement (10 juin) et la fixation du prix (11 juin) sont des lignes sans montant, comme pour les convertibles 2031 (D-0042).

  (12) Correction, après un premier réassemblage et avant toute publication : signaux tirés des items de 8-K sous le régime des émetteurs privés étrangers. Les items de détresse (1.03, 2.04, 2.06, 3.01), le changement d'auditeur ou la correction d'erreur (4.01, 4.02) et F9 (1.02) se lisent dans les 8-K. Un trimestre où le groupe ne dépose que des 6-K n'en a aucun : un 6-K n'a pas d'items (point 6), et les 6-K ne sont lus que par unités plafonnées. Le premier réassemblage y écrivait pourtant « sans événement », comme dans un trimestre de 8-K sans l'item. Or le 6-K d'IREN du 20 mars 2025 annonce un retraitement des comptes (« should be amended and restated ») : la cellule du trimestre le contredisait. Règle, appliquée au trimestre qui porte au moins un 6-K et aucun 8-K :
  - items de détresse et F9 : non établis (`not_collected`), avec les 6-K du trimestre pour pièce ;
  - changement d'auditeur ou correction d'erreur : événement si le drapeau de correction balisé (`dei:DocumentFinStmtErrorCorrectionFlag`) ou un signal `nonreliance` lu dans un 6-K l'établit, daté du dépôt qui le porte ; sinon non établi ;
  - dépôt tardif : le formulaire NT 20-F (et son amendement) s'ajoute aux formulaires NT. Il signale un 20-F tardif ;
  - un trimestre de 8-K garde la règle commune ; un trimestre sans aucun dépôt aussi (convention déjà appliquée avant toute première cotation et avant une fusion inversée).
  Code : `events.regime_6k`, `structural_signals` et F9 de `fsignals.fragility_events` ; deux tests unitaires (97 au total).

  (13) Correction, après le second réassemblage et avant toute publication : issue E.5 (contrepartie au client). Le code tenait pour `supported` toute pièce L3 publiée par le fournisseur. Or L3 couvre tout traitement comptable publié qui lie financement et relation commerciale (contrats combinés, contrepartie payable au client, contrepartie non monétaire), et E.5 n'en retient que deux : une contrepartie payable au client, comptabilisée en réduction du revenu (ASC 606-10-32-25), et un revenu contre une contrepartie non monétaire reçue de lui (32-21). La première issue `supported` de l'étude venait d'une autre pièce : IREN accorde à NVIDIA, son fournisseur de GPU, des droits d'acquérir jusqu'à 30 millions d'actions à 70 $ (« Investment Rights », 7 mai 2026), dont la juste valeur de 793,4 M$ est incorporée au coût des GPU achetés. NVIDIA est aussi cliente du cloud d'IREN, mais le 10-K dit que ces droits « are accounted for separately from the Company's cloud services agreement with NVIDIA ». La pièce reste L3 pour E.1 à E.3 (documented_link) ; elle ne vaut plus pour E.5, qui exige désormais une pièce de la famille `customer_consideration`, ou une arête ou une nature de montant de contrepartie au client (`annex_e.customer_consideration`). Avant ce réassemblage, aucune issue E.5 n'était `supported` : la correction ne touche que la paire IREN–NVIDIA. Un test unitaire (98 au total).

  (14) Effets, au réassemblage (16 groupes, vue `as_known`) :
  - événements de l'annexe F (F1 à F10) : 169 → 183, tous chez les deux groupes ajoutés ; ceux des quatorze autres groupes sont inchangés. IREN 10 : F2 six fois (de l'exercice 2025 à mars 2026, par les comparatifs en US GAAP des 10-Q), F1 trois fois, F8 au trimestre clos le 31 mars 2026 (croissance annuelle passée sous zéro). Nebius 4 : F5 aux exercices 2024 et 2025 (faiblesses significatives de l'Item 15 : réponse au point 8), F6 en 2022 et 2023 (dépréciations de mises en équivalence de 2,5 M$ et 10,9 M$, rendues publiques le 30 avril 2025 et le 30 avril 2026) ;
  - la limite du point 8 (« deux exercices seulement ») était trop étroite. Les 20-F postérieurs à la cession présentent trois exercices, retraités des activités cédées. Par la règle du point 3 (celle des fusions inversées : l'historique du groupe est celui que publient les rapports postérieurs), ces comparatifs entrent dans les séries ;
  - signaux de structure (point 12) : IREN porte un changement d'auditeur ou une correction d'erreur aux trimestres clos les 31 mars 2025 (retraitement annoncé par 6-K), 30 septembre 2025 (drapeau de correction du 10-K de l'exercice 2025) et 31 décembre 2025 (8-K item 4.01 du 28 novembre 2025). Sous le régime 6-K, les items de détresse ne sont pas établis sur 6 trimestres de Nebius et 4 d'IREN ;
  - paires (conclusions de relation) : 64 → 69. Nouvelles : IREN → Microsoft, Nebius → Meta, Nebius → Microsoft et Nebius → ClickHouse (causalité non établie : structure commerciale ou financière seulement) ; IREN → NVIDIA (achats réciproques seulement). NVIDIA → IREN (dépendance documentée) et NVIDIA → Nebius (relation commerciale doublée d'un financement) remplacent les contreparties « IREN LTD » et « NEBIUS GROUP N.V. » de D-0042. Les dépendances documentées restent 8 ;
  - cycles : 26 → 27. IREN → NVIDIA → IREN, concomitant, dépendance documentée, remplace le cycle de NVIDIA par la contrepartie « IREN LTD » : NVIDIA fournit les GPU et achète du cloud à IREN, qui lui accorde les droits d'investissement du point 13. Nouveau : Nebius → NVIDIA → Nebius, concomitant, commercial et financier, aucun lien documenté (achats de matériel NVIDIA ; bon préfinancé de 2,0 Md$) ;
  - E.1 et E.2 : 26 issues, dont 15 indéterminées (58 %), « discrimination possible » ; inchangé, les issues de NVIDIA–Nebius passent de la contrepartie au groupe avec les mêmes valeurs. E.5 : 69 issues, toutes indéterminées (point 13). E.6 : 17 cycles décrits ;
  - bloc `lender` : l'extraction des BDC Data Sets est refaite avec le registre enrichi (D-0043, point 14). Une position nouvelle : Crescent Private Credit Income Corp sur Banco Santander, S.A. (8,5 M$ de principal, juste valeur sur coût 0,98 au 30 juin 2026), nommée comme contrepartie des options plafonnées d'IREN. Aucune BDC ne détient de position sur Nebius ou IREN ;
  - exclusions : `not_processed` +595 (601 unités 6-K au-delà du plafond, moins 6 unités de la découverte d'IREN), `conflicting` +43 (faits : IREN 26, Nebius 17), `pending_entity` +29 (dénominations sans pièce d'identité), `out_of_scope` +10 (7 6-K de Nebius sans paragraphe qualifiant, dépôts antérieurs aux ruptures d'historique), `financial_parties_only` +4, `history_left_censored` +2 ;
  - limites relevées : les unités 6-K n'ont pas de cadre comptable (narratif, comme en D-0042). Deux lignes d'IREN portent des valeurs comptables en IFRS (dette hôte des convertibles 2030 aux 31 décembre 2024 et 31 mars 2025) : leur note le dit, et elles n'entrent dans aucune somme (cellules d'exposition ligne à ligne, aucun total ajouté). Le libellé « the Group », employé par le lecteur dans 9 blocs d'IREN pour IREN lui-même, figure parmi les dénominations en attente ; il ne fait aucune arête (lignes anonymes) et sera remplacé à la prochaine passe ;
  - correction de rendu : la section `foreign` triait ses lignes par cadre comptable, absent pour les unités 6-K ; le tri place désormais la clé vide en dernier ;
  - tests unitaires : 98. Source : §2.1, §3.6, §4.5, §7.5, §9.6, §10.2, §11.1, §14, annexes E et F.
- **D-0049 — Trois ajouts : le montage Apollo–Athene–Broadcom (WHCO), le groupe Applied Digital (APLD) et une lecture ciblée de Galaxy Digital (Helios). Règles fixées avant toute recherche et toute lecture.** (1) Décision de l'utilisateur, le 2026-10-11 : « Ok on part là-dessus, toujours sans sous-agent ». Elle répond au remue-méninges du même jour, qui proposait cet ordre : Athene/WHCO en montage, Applied Digital en groupe complet, Galaxy (Helios) en lecture ciblée. Great Elm Capital et MSD Investment Corp. sont déjà suivies comme BDC (blocs `lender`, `lender_portfolio`, `lender_liabilities`), Cipher Mining est un groupe depuis D-0043 : rien de plus pour elles. Backblaze reste en file. Lecture séquentielle par l'exécutant, sans sous-agent, un commit par partie. L'exécution garde l'as_of du 2026-10-07 (D-0048, point 2).

  (2) Montage Apollo–Athene–Broadcom (bloc `montages`, second montage). Ce qui est déjà lu : la note d'engagements du 10-Q d'Apollo Global Management du deuxième trimestre 2026 (bloc 29f74ba9f6b1, rang 1 de la découverte). Des fonds gérés par Apollo et des affiliés, dont Athene, ont conclu avec Broadcom Inc. un « capital solution agreement » de 35 Md$, qui « facilitates Anthropic, PBC's compute infrastructure expansion beginning in mid-2026 ». WarehouseCo Intermediate Holdings LP (« WHCO »), fonds géré par Apollo, porte l'obligation d'achat de l'infrastructure produite. Athene Holding Ltd. (« AHL ») garantit 15 % de l'obligation restante ; un tiers non nommé lui en rembourse 35 %. Objet : nommer les parties et les montants de la structure (qui achète, qui finance, qui garantit, pour quel client final) et la relier à Broadcom (groupe AVGO) et à Anthropic (laboratoire). Règles :
  - sources : recherche plein texte d'EDGAR du 2026-01-01 au 2026-10-07, tous formulaires : « "WarehouseCo Intermediate Holdings" » ; « "WarehouseCo" » ; « "capital solution" "Broadcom" » ; « "Apollo" » et « "Athene" », limitées aux dépôts de Broadcom (CIK 1730168) ; « "Broadcom" », limitée aux dépôts d'Athene (CIK 1527469) puis à ceux d'Apollo (CIK 1858681). S'y ajoutent les rapports périodiques (10-Q, 10-K) d'Athene et d'Apollo déposés dans la période. Chaque pièce se tire une fois, en cache, sous les règles réseau habituelles ;
  - relevés de portefeuille (mêmes formulaires que D-0046, point 8) : comptés, non lus, motif `out_of_scope` ;
  - unités : les paragraphes qui nomment un terme qualifiant, avec deux paragraphes avant et deux après, fondus quand ils se chevauchent (règle de D-0046). Termes qualifiants : « WarehouseCo », « WHCO », « capital solution », « Broadcom », « Anthropic », « Apollo », « Athene ». Jamais le nom du déposant dans ses propres pièces (D-0046, point 9) : « Broadcom » ne qualifie pas une pièce de Broadcom ; ni « Apollo » ni « Athene » ne qualifient une pièce d'Apollo ou d'Athene, l'un nommant l'autre à chaque page (Athene est la branche retraite d'Apollo) ;
  - plafond : 40 unités, dans l'ordre des dates de dépôt ; au-delà, `not_processed` ;
  - lignes : conventions de D-0046, point 5. Dans une pièce d'Apollo ou d'Athene, « the Company » est le déposant ; les fonds et les véhicules s'écrivent comme le bloc les nomme ;
  - identification : si les notes de Broadcom décrivent l'accord sans nommer la contrepartie, cette contrepartie n'est identifiée à WHCO ou aux fonds d'Apollo que si un extrait cité en confirme au moins trois traits : un montant de 35 Md$ (ou égal à celui d'Apollo) ; une conclusion au deuxième trimestre 2026 ; Anthropic comme utilisateur final ; une obligation d'achat de l'infrastructure de calcul produite. L'identification se consigne dans `config.yaml` (`identified_ventures`), avec les extraits des deux côtés ;
  - rattachements : les fonds gérés par Apollo (dont WHCO) ne forment pas un groupe économique avec Apollo (même règle que D-0045, point 3). Athene Holding Ltd. ne rejoint Apollo Global Management que sur un extrait qui la dit filiale consolidée d'Apollo. Ni Apollo ni Athene ne deviennent des groupes : ce sont des contreparties (§10.4).

  (3) Applied Digital (APLD), groupe complet. Hébergeur endetté dont CoreWeave serait le locataire principal, de même profil que TeraWulf et Cipher (D-0043). Règles :
  - `company_tickers.json` (2026-10-07) résout APLD vers le CIK 1144879 (Applied Digital Corp.). Le groupe entre dans `config.yaml` avec `group_entry` au 2026-10-11 ;
  - mêmes phases et mêmes règles de lecture que les groupes présents (D-0043, D-0048) : inventaire, archives XBRL, catalogue des notes, items et pièces, lecture du texte complète ;
  - exercice clos fin mai : le calendrier le traite comme les exercices décalés déjà présents ;
  - rupture d'historique : seulement si l'inventaire montre une fusion inversée, une reprise de coquille ou une cession de périmètre, constatée par un extrait (D-0043, point 3 ; D-0048, point 3). Un changement de dénomination seul n'en est pas une ;
  - découverte : les lignes déjà lues pour ce déposant (aucune) iraient au groupe ; ses 27 unités encore en file en sortent (`out_of_scope`), puisque ses dépôts se lisent par le catalogue du groupe (D-0043, point 6).

  (4) Galaxy Digital (Helios), lecture ciblée (bloc `montages`, troisième montage). Galaxy Digital Inc. (CIK 1859392) n'entre pas comme groupe : son bilan est dominé par les actifs numériques et le négoce, et il ne dépose comme société américaine que depuis 2025. Objet : nommer les parties et les montants du campus Helios (bail ou location à CoreWeave, financement du projet) et les relier à CoreWeave (groupe CRWV). Règles :
  - sources : recherche plein texte d'EDGAR du 2025-01-01 au 2026-10-07, tous formulaires : « "Helios" "CoreWeave" » ; « "Galaxy Digital" », limitée aux dépôts de CoreWeave (CIK 1769628) ; « "CoreWeave" », limitée aux dépôts de Galaxy Digital Inc. S'y ajoutent les rapports périodiques (10-Q, 10-K) de Galaxy Digital Inc. déposés dans la période ;
  - relevés de portefeuille : comptés, non lus (`out_of_scope`) ;
  - unités : même règle de fenêtres ; termes qualifiants : « Helios », « CoreWeave », « Galaxy ». Jamais le nom du déposant dans ses propres pièces : « Galaxy » ne qualifie pas une pièce de Galaxy, « CoreWeave » pas une pièce de CoreWeave. « Helios » seul ne qualifie que dans les pièces de Galaxy ou de CoreWeave, puisqu'il nomme aussi d'autres sociétés ;
  - plafond : 40 unités, dans l'ordre des dates de dépôt ; au-delà, `not_processed` ;
  - lignes : conventions de D-0046, point 5 ; les lignes d'une pièce de Galaxy vont à la contrepartie Galaxy Digital Inc. ; les arêtes ne naissent que des lignes qui nomment leurs parties.

  (5) Code : le bloc `montages` se généralise. Chaque montage est décrit dans `config.yaml` (`montages`) : période, requêtes, déposants dont les rapports périodiques se tirent, termes qualifiants et noms propres de chaque déposant, plafond. Le montage de D-0046 s'y écrit tel quel ; ses blocs doivent garder leurs clés de contenu, ce qui se vérifie avant toute nouvelle lecture.

  (6) Ordre et commits : la décision ; le montage Athene/WHCO (code, recherche, unités, lecture) ; Applied Digital (phases, catalogue, lecture) ; Galaxy (recherche, unités, lecture) ; puis l'intégration : extraction refaite des BDC Data Sets (D-0043, point 14), réassemblage, rendus, résultats ici.

  (7) Amendement, après le premier décompte des fenêtres du montage Athene/WHCO et avant toute lecture. Il ne se fonde que sur les comptes et les termes relevés. Les requêtes rendent 1, 4, 4, 1, 0, 1 et 1 résultats : 9 pièces, dont 3 relevés 13F-HR écartés, plus les rapports périodiques d'Athene et d'Apollo (10-K 2025, 10-Q des deux premiers trimestres 2026). Premier décompte : 76 fenêtres, dont 36 au-delà du plafond. « Capital solution » est aussi le nom d'un métier d'Apollo (« Apollo Capital Solutions ») : les 10-K et les 10-Q du premier trimestre d'Apollo et d'Athene en donnaient 30 fenêtres. Le plafond en était rempli, et les 10-Q du deuxième trimestre, seuls à nommer WHCO, Broadcom et Anthropic, passaient au-delà. Règle ajoutée : « capital solution » ne qualifie pas une pièce d'Apollo ou d'Athene, comme leurs propres noms ; il qualifie ailleurs. Second décompte : 33 fenêtres, toutes sous le plafond. Ce sont les 10-Q d'Athene et d'Apollo du deuxième trimestre 2026 (une fenêtre chacun), le 10-Q de Broadcom clos le 3 mai 2026 (une fenêtre, « Apollo »), et 30 fenêtres de deux annexes 99.3 de 6-K de Brookfield du 5 juin 2026, qui nomment « WarehouseCo » (14 textes distincts, présents dans les deux annexes, et 2 autres). Les quatre autres rapports d'Apollo et d'Athene n'ont plus de fenêtre (`out_of_scope`).

  (8) Lecture du montage Athene/WHCO, sans sous-agent : 19 blocs distincts (33 fenêtres, les annexes des deux 6-K de Brookfield se répétant), 19 lus, 2 observations et 17 abstentions, aucune ligne rejetée.
  - Les 16 fenêtres de Brookfield nomment ses propres « WarehouseCo » (BN-ESP Warehouse Holdings Ltd., BNT ESP Warehousing Ltd.), sociétés de son plan d'actions entiercées, sans rapport avec WHCO, ou ses « capital solutions » : abstentions motivées.
  - Les notes d'Athene et d'Apollo du deuxième trimestre 2026 répètent la note d'Apollo déjà lue dans la découverte (bloc 29f74ba9f6b1) : abstentions `duplicate_of_other_block`.
  - Fait nouveau, dans la rubrique « Other Information » du 10-Q de Broadcom clos le 3 mai 2026 (déposé le 9 juin 2026) : « On June 8, 2026, we arranged for Apollo ("investor partner") to take on certain agreements to purchase AI racks based on custom AI accelerators designed by us and the related lease agreements with a customer ». Broadcom garantit à Apollo les loyers de ce client sur cinq ans, « with a maximum exposure of $29 billion ». Deux lignes du groupe Broadcom : une garantie (famille `credit_support`, arête `backstop`, 29 Md$ d'exposition maximale, déclencheur : défaut du client) et la reprise des contrats d'achat par Apollo (famille commerciale, sans montant).
  - Identification non faite (point 2) : le trimestre et l'objet concordent avec l'accord de 35 Md$ décrit par Apollo, mais Broadcom ne donne ni ce montant (il écrit 29 Md$ d'exposition maximale) ni le nom du client. Deux traits sur quatre : le client de Broadcom reste anonyme, et les lignes de Broadcom gardent une clé distincte de celle d'Apollo.

  (9) Applied Digital, constats de la phase 0 et règle existante appliquée (avant toute lecture). Les submissions montrent des 10-Q de 2008 et 2009 d'une ancienne société coquille, puis aucun rapport périodique jusqu'en 2022 : ils précèdent la période de lecture (début au 1er juin 2017) et ne changent rien. L'introduction en bourse date d'avril 2022 (EFFECT du 12 avril, 424B4 0001104659-22-045562 du 13 avril) ; le premier 10-Q couvre le trimestre clos le 28 février 2022 (0001628280-22-014389). Comme pour CoreWeave et SpaceX (§7.5), `reporting_start` fixe le début des trimestres au 1er décembre 2021 : avant, la cellule trimestrielle attendue est `not_applicable`, avec cette pièce. Exercice clos le 31 mai ; fenêtre du groupe : à partir du 1er juin 2020. Aucune rupture d'historique : pas de fusion inversée ni de cession dans la période.

  (10) Lecture d'Applied Digital, sans sous-agent : 452 blocs en file (6,9 M de caractères lus, dont 5,65 M de corps de pièces). 442 lus ; les 10 autres sont des corps d'EX-4 (actes de fiducie des obligations, formes de billets et de bons) dont l'en-tête ne montre que des établissements financiers, exclus par la règle (`financial_parties_only`, §14 ne les rouvrant pas). 894 lignes : 710 observations (177 lignes d'en-têtes de pièces, 304 de financement, 149 commerciales, 42 de soutien de crédit, 3 de contrepartie payable à un client, 35 sans famille) et 184 abstentions (74 `duplicate_of_other_block`, 40 `no_named_counterparty`, 25 `boilerplate_no_event`, 24 `no_relevant_content`, 15 `out_of_scope_content`, 4 `illegible`, 2 `financial_parties_only`). Aucune ligne rejetée au final : les refus du validateur (montant balisé à citer en `tagged_reference`, valeur hors énumération) ont été corrigés avant écriture, et une note d'abstention inexacte a été réécrite. 68 contreparties nommées hors en-têtes.
  - Méthode : les corps d'EX-10 longs (contrats de crédit, baux, actes de garantie) ont été parcourus par recherche des montants, des parties et des clauses financières, comme le billet de NYDIG (D-0048) et le 11-K de Boeing (D-0038) ; tous leurs morceaux ont été servis avant soumission. Limite : une clause sans montant ni nom de partie peut avoir échappé à la recherche.
  - Clients : CoreWeave, Inc. (baux des bâtiments 2, 3 et 4 de Polaris Forge 1, 400 MW, environ 3, 4 et 4 Md$ ; garanties de la société au profit de CoreWeave ; bons de 13 062 521 et 8 393 611 actions remis au client ; le 30 mars 2026, bail de deux halls avec CoreWeave Compute Acquisition Co. VIII, LLC, garanties « springing » et lettre de crédit de 50 M$ de CoreWeave, cession du bail du bâtiment 3 à cette société). Oracle (Polaris Forge 2) n'est nommé que dans certains blocs ; les notes l'appellent « hyperscaler » américain de bonne qualité de crédit (200 MW, 20 octobre 2025). Un second hyperscaler non nommé loue Delta Forge 1 (300 MW, avril 2026), Polaris Forge 3 (300 MW, mai 2026) et Delta Forge 2 (210 MW, 5 juin 2026, environ 5,2 Md$) : lignes anonymes. Avant 2024 : Marathon Digital Holdings, Inc. (hébergement de 200 MW en 2022 ; achat du site de Garden City par sa filiale Mara Garden City LLC pour 87 328 675 $ le 1er avril 2024), JointHash Holding Limited (filiale de GMR), Bitmain Technologies Limited, F2Pool Mining, Inc. et Hashing LLC (premier site de Jamestown, 2022) ; deux clients du nuage IA non nommés (jusqu'à 180 M$ et 460 M$, 2023).
  - Financements : Macquarie (MIP HPC Holdings, LLC : quatre clôtures du contrat de parts de TopCo 2 entre octobre 2025 et mai 2026, 112,5 + 450 + 337,5 + 925 M$, environ 1,8 Md$ ; bons de 2,4 millions d'actions ; Macquarie Equipment Capital, Inc. : billets de 150 M$ en 2024, de FAR-01 et de DevCo en 2025, tous remboursés) ; Sumitomo Mitsui Banking Corporation (375 M$, février 2025, remboursé en novembre 2025) ; Goldman Sachs Bank USA (crédit relais de 300 M$ d'APLD ComputeCo 3 LLC, 1er mai 2026, avec garantie de la société mère à recours intégral, remboursé en juin 2026) ; First National Bank of Omaha (crédit de 65 M$ de 2025, puis crédit renouvelable de 350 M$ porté à 430 M$, 82,4 M$ tirés et 241 M$ de lettres de crédit au 31 août 2026) ; Texas Capital Bank (58,5 M$, 30 juin 2026) ; obligations de premier rang des trois ComputeCo (2,35, 2,15 et 1,59 Md$) et convertibles de 450 M$, porteurs anonymes ; B. Riley (prêt de 50 M$ de 2023, contrat d'achat d'actions de préférence de 150 M$ porté à 2 Md$) ; YA II PN, LTD. (avances prépayées de 92,1 M$ en 2024, dont 71,3 M$ convertis et 4,8 M$ remboursés ; actions de préférence de série F de 50 M$) ; AI Bridge Funding LLC (20 M$, 2024) ; CIM APLD Lender Holdings, LLC (125 M$, 2024) ; prêts bancaires régionaux : Starion Bank (15 M$ en 2022, 20 M$ en 2023), Vantage Bank Texas (7,5 M$ et 15 M$ en 2022, 3,7 M$ en 2024), Cornerstone Bank (16 M$ en 2024, garanti par Bank of North Dakota), Jamestown Stutsman Development Corporation (aide de taux).
  - Parties liées : Base Electron (entité à intérêts variables non consolidée ; garantie de la société au profit de The Babcock & Wilcox Company, exposition implicite d'environ 2,4 Md$, résiliée le 29 mai 2026 contre 37 M$ ; billet à vue de 58,6 M$ puis 59,3 M$ ; participation de 2,0 M$), Ekso Bionics Holdings, Inc. devenue ChronoScale (filiale), GMR Limited et GOI (anciens détenteurs de plus de 5 %).
  - Lignes sans nom : quand un bloc donne l'encours d'un prêt sans nommer le prêteur (« Starion Term Loan », « SMBC Loan », « 2026 Revolving Credit Facility »), la ligne est `derivable` (`explicit_cross_reference`) sans `counterparty_name`, sous la clé d'instrument des lignes nommées ; le validateur exige que le nom figure dans le bloc.
  - À régler à l'intégration (entités et clés) : « CoreWeave Parent » (8-K/A du 1er avril 2026) vers CoreWeave, Inc., sur un extrait cité ; variantes de Base Electron (Corporation, Corp., Inc. et nom court), de YA II PN, LTD., d'AI Bridge Funding LLC et de GOI ; « Vantage Bank » (prêt de 2024) et « Vantage Bank Texas » ; « CORNERSOTNE BANK », coquille du texte ; ancien nom « Applied Blockchain, Inc. » (déposant) ; clé d'instrument `apld:computeco2_notes_2026` écrite une fois pour `apld:computeco2_notes_2031`.

  (11) Amendement du montage Galaxy (Helios), après le premier décompte des fenêtres et avant toute lecture. Il ne se fonde que sur les comptes, les formulaires et les noms de fichiers. Les requêtes rendent 6 202, 6 et 46 résultats ; 6 142 sont des relevés de portefeuille de fonds qui détiennent à la fois des titres de CoreWeave et d'Helios Technologies (NPORT-P 4 645, 13F-HR 708, N-PX 304, N-CSRS 189, N-CSR 149, autres 147), comptés et non lus. 66 pièces tirées, plus les rapports périodiques de Galaxy. Premier décompte : 811 fenêtres (469 textes distincts), dont 771 au-delà du plafond de 40. Galaxy en fournit 787, car « Helios », nom de son campus, figure dans presque tous ses paragraphes d'activité ; 579 viennent de ses prospectus et déclarations d'enregistrement (S-4/A, S-1, S-1/A, DRS, 424B4 et 424B3, dont les suppléments qui reprennent ses 10-Q et son 10-K). Dans l'ordre des dates, le plafond était rempli par le S-4/A de mars 2025 et le premier 424B3, avant tout rapport périodique et avant les contrats de financement de 2025 et 2026. Règles ajoutées :
  - un texte de fenêtre identique se lit une fois (le premier dans l'ordre ci-dessous) ;
  - les prospectus et déclarations d'enregistrement de Galaxy, et ses communiqués et présentations trimestriels de résultats (pièces 99.1 « press release » et 99.2 des 8-K de résultats), sont comptés, non lus (`out_of_scope`) : ils reprennent les rapports périodiques ;
  - ordre de lecture : les fenêtres des autres déposants, puis celles des 8-K de Galaxy (contrats et communiqués propres à Helios ou à son financement), puis ses rapports périodiques, chaque classe du plus récent au plus ancien, puis le reste ;
  - plafond porté à 71 textes distincts : les autres déposants (18), les 8-K de Galaxy (32) et le dernier rapport périodique (10-Q du deuxième trimestre 2026, 21). Second décompte : 178 fenêtres, 169 textes distincts ; les rapports périodiques antérieurs et la circulaire de procuration (98 textes) passent au-delà du plafond (`not_processed`). Les clés des blocs des deux autres montages ne changent pas (vérifié).

  (12) Lecture du montage Galaxy (Helios), sans sous-agent : 71 blocs distincts (177 000 caractères), tous lus. 84 lignes : 34 observations (18 de financement, 12 commerciales, 1 de soutien de crédit, 3 sans famille) et 50 abstentions (18 `boilerplate_no_event`, 11 `duplicate_of_other_block`, 9 `no_relevant_content`, 7 `no_named_counterparty`, 2 `out_of_scope_content`, 2 `financial_parties_only`, 1 `no_amount`). Aucune ligne rejetée. Une ligne a été corrigée en place avant l'intégration : la nature du montant du bail de la phase II, alignée sur les baux d'Applied Digital (`commitment_unexecuted`).
  - Bail : CoreWeave loue tout Helios.
    - Phase I : accord de 15 ans de mars 2025 (avril 2025 selon le 10-Q du deuxième trimestre 2026), 133 MW de capacité informatique critique (environ 200 MW bruts), environ 4,5 Md$ de loyers attendus sur la durée initiale. Livrée au premier semestre 2026 ; premiers revenus au deuxième trimestre 2026 : 18,9 M$ de loyers et 5,8 M$ de refacturation des coûts d'exploitation.
    - Phase II : bail du 8 août 2025 entre Galaxy Power LLC et CoreWeave, Inc. (avenants des 21 janvier et 3 juin 2026, bail cédé à Galaxy Helios II LLC), 260 MW critiques (400 MW bruts). Paiements minimaux restants d'environ 10,4 Md$ sur 15 ans, loyers à partir du deuxième trimestre 2027 ; un paiement d'options de 100 M$ a déjà été reçu de CoreWeave.
    - Phase III : 133 MW critiques (200 MW bruts), en 2028.
    - Au total, 526 MW critiques et 800 MW bruts loués à CoreWeave ; plus de 1 Md$ de loyers annuels moyens attendus (journée analystes de décembre 2025) ; contrat initial expirant en 2040.
  - Financement :
    - Deutsche Bank AG : prêt à terme garanti de 1,4 Md$ à Galaxy Helios I LLC (15 août 2025, SOFR + 4,75 %, échéance 15 août 2028) ; 434 M$ tirés au 30 septembre 2025, environ 1,3 Md$ au 30 juin 2026.
    - Ares Core Infrastructure Fund (BDC) détient un prêt à tirage différé de 100 M$ à « Galaxy Helios LLC », de même marge et de même échéance (principal de 62,7 M$ au 31 décembre 2025, de 90,6 M$ au 30 juin 2026). C'est vraisemblablement une part du prêt de Deutsche Bank, mais aucun bloc ne le dit : les deux restent des instruments distincts.
    - Obligations garanties de premier rang de Galaxy Helios Data Centers II LLC pour la phase II : 3,507 Md$ à 9,875 %, échéance 2031, émises le 28 juillet 2026 (Morgan Stanley & Co. LLC représentant des acheteurs initiaux, The Bank of New York Mellon fiduciaire). Galaxy Digital Holdings LP en garantit l'achèvement, sans plafond.
  - Électricité et site : contrat de service avec AEP Texas Inc. pour 830 MW de plus (janvier 2026) ; interconnexion par Wind Energy Transmission Texas, LLC (sans contrat écrit) ; site acheté à Argo Blockchain en décembre 2022.
  - Autres déposants :
    - MSD Investment Corp. (BDC déjà suivie) détient deux tranches d'un prêt à tirage différé de CoreWeave, sans rapport avec Helios. Ses lignes vont de MSD à CoreWeave, aux montants du bloc `lender_portfolio`.
    - Ares Core Infrastructure Fund s'est aussi engagée envers Coreweave Financing DDTL V, LLC (15,0 M$, dont 9,7 M$ non tirés).
    - Galaxy Digital Partners LLC a souscrit 93 750 actions de l'introduction en bourse de CoreWeave (mars 2025).
    - Une présentation de Big Digital Energy, Inc. cite de seconde main « Galaxy Digital/CoreWeave (800 MW Helios, $1B+ avg. annual revenue, 15 - yr) » : abstention.
  - À régler à l'intégration (entités) :
    - rattachements à Galaxy Digital Inc. permis par un extrait cité : Galaxy Digital Holdings LP (« Galaxy Digital Inc. (Pubco) serves as the general partner and consolidates GDH LP for financial reporting »), Galaxy Helios I LLC (« a wholly owned subsidiary of GDH LP »), Galaxy Helios Data Centers II LLC (« an indirect wholly owned subsidiary of Galaxy Digital Inc. ») et Galaxy Helios II LLC (« a wholly owned direct subsidiary of the Issuer ») ;
    - sans extrait d'appartenance dans les blocs lus, Galaxy Power LLC, Galaxy Helios LLC (nom écrit par Ares) et Galaxy Digital Partners LLC restent des contreparties propres ;
    - « Coreweave Financing DDTL V, LLC » et « CoreWeave Compute Acquisition Co., IV, LLC » ne rejoignent CoreWeave que sur extrait ; « CoreWeave » et « CoreWeave, Inc. » désignent CoreWeave, Inc. ;
    - Galaxy Digital Inc. reste une contrepartie (point 4).

  (13) Intégration (17 groupes, vue `as_known`), dans l'ordre de D-0048 : premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus. Le second réassemblage a été relancé une fois, pour y inclure les rattachements des véhicules de Galaxy décrits plus bas.
  - Corrections dans la passe, avant l'assemblage (la passe n'est pas close, comme en D-0020) :
    - une clé d'instrument d'Applied Digital, `apld:computeco2_notes_2026`, devient `apld:computeco2_notes_2031` (1 ligne) ;
    - dans les pièces de Galaxy, les véhicules écrits en payeur ou en receveur (Galaxy Power LLC, Galaxy Helios I LLC et « Galaxy Helios I », Galaxy Helios Data Centers II LLC, Galaxy Digital Holdings LP) deviennent « the Company » (7 lignes), en application du point 4 ; leurs noms restent dans les notes.
  - Entités, sur extraits cités (D-0021) :
    - alias : « CoreWeave » → CoreWeave, Inc. (10-Q de Galaxy du deuxième trimestre 2026 : « CoreWeave, Inc. ("CoreWeave") ») ; « Ekso » → Ekso Bionics Holdings, Inc. (10-K 2026 d'Applied Digital) ; « Sai Computing » → Sai Computing, LLC (8-K d'Applied Digital de 2023). L'alias « CoreWeave » rattache aussi à CoreWeave une ligne de NVIDIA jusque-là en attente ;
    - rattachements au groupe économique de la contrepartie Galaxy Digital Inc. (`confirmed_entities`, groupe `CP:galaxy digital inc`), avec les extraits du point 12 : Galaxy Digital Holdings LP, Galaxy Helios I LLC, Galaxy Helios Data Centers II LLC et Galaxy Helios II LLC. Ce sont les premières filiales d'une contrepartie au registre : leur type devient `counterparty_group` (correction de code, test unitaire). Galaxy Digital Inc. reste une contrepartie (point 4) ;
    - « Applied Blockchain, Inc. », ancienne dénomination du CIK d'Applied Digital, se rattache par ses formerNames ;
    - restent en attente, faute d'extrait qui les définisse :
      - « CoreWeave Parent » : le 8-K/A du 1er avril 2026 l'emploie sans la définir ;
      - « GOI » : aucun bloc lu ne le définit comme Global Operating Infrastructure LLC ;
      - « Base Electron » : Base Electron Corp. (ou Corporation) et Base Electron, Inc. restent deux entités, aucun extrait ne les reliant ;
      - les banques sans suffixe juridique, comme dans les groupes précédents : Starion Bank, Cornerstone Bank et sa coquille, Vantage Bank, Vantage Bank Texas, First National Bank of Omaha, Goldman Sachs Bank USA, Texas Capital Bank, Frost Bank, Bank of North Dakota ;
      - « Deutsche Bank » (journée analystes de Galaxy), « Argo Blockchain » et « Apollo » (10-Q de Broadcom, point 8).
  - Effets :
    - événements de l'annexe F : 183 → 220, tous chez Applied Digital (F1 6 fois, F2 17 fois, F5 14 trimestres, de février 2022 à mai 2025) ; ceux des seize autres groupes sont inchangés ;
    - paires (conclusions de relation) : 69 → 83, toutes nouvelles avec Applied Digital. Treize en causalité non établie : CoreWeave, Oracle, AI Bridge Funding LLC, B. Riley Commercial Capital, LLC, B. Riley Financial, Inc., Base Electron (deux dénominations), CIM APLD Lender Holdings, LLC, Ekso Bionics Holdings, Inc., Global Operating Infrastructure LLC, Macquarie Equipment Capital, Inc., MIP HPC Holdings, LLC et MIP VI HPC Holdings, LLC. Une en achats réciproques seulement : GMR Limited. Les dépendances documentées restent 8 ;
    - cycles : 27 → 30. Les trois nouveaux sont des boucles de financement seul (prêt reçu ; intérêts, commission ou bons rendus au prêteur) entre Applied Digital et AI Bridge Funding LLC, B. Riley Commercial Capital, LLC et B. Riley Financial, Inc., en causalité non établie ;
    - paires à financement documenté : 13 → 16 (Applied Digital avec AI Bridge Funding LLC et avec les deux dénominations de Base Electron). E.1 et E.2 : 26 issues dont 15 indéterminées → 32 dont 18, avec trois issues E.1 nouvelles « non étayé » ; E.7 reste « discrimination possible ». E.5 : 83 issues, toutes indéterminées. E.6 : 18 cycles décrits ;
    - Galaxy : arêtes CoreWeave → Galaxy Digital Inc. (baux, paiement d'options de 100 M$, revenus du deuxième trimestre 2026), Morgan Stanley & Co. LLC → Galaxy Digital Inc. (obligations de 3,507 Md$) et Deutsche Bank AG → Galaxy Digital Inc. (contrat de crédit). Aucune paire nouvelle : Galaxy n'est pas un groupe, et aucun financement de CoreWeave par Galaxy Digital Inc. n'est écrit (la souscription de Galaxy Digital Partners LLC à l'introduction en bourse de CoreWeave va à cette contrepartie propre) ;
    - bloc `lender` : extraction refaite (2 098 dépôts). Positions nouvelles :
      - Trinity Capital Inc. et Eagle Point Trinity Senior Secured Lending Co sur Applied Digital Corp (financement d'équipement de mars 2024, dont une tranche à 19 % ; juste valeur sur coût entre 1,00 et 1,03, de mars 2024 à mars 2026) ;
      - Crestline Lending Solutions, LLC sur Galaxy Helios I LLC (12,75 M$ de principal au 30 juin 2026, juste valeur sur coût 1,00), rattachée à Galaxy Digital Inc. par les rattachements ci-dessus ;
      - Ares Core Infrastructure Fund sur Galaxy Helios LLC (90,6 M$), contrepartie propre ;
      - les lignes « Total » du portefeuille de Trinity sont écartées (`invalid_aggregate`, 5) ;
    - exclusions :
      - `not_processed` +71 : 98 textes du montage Galaxy au-delà du plafond, moins 27 unités de la découverte tirées des dépôts d'Applied Digital, désormais une seule exclusion `out_of_scope` du groupe ;
      - `conflicting` +81 (faits d'Applied Digital) ;
      - `out_of_scope` +55 : 54 pour les montages (pièces écartées par la règle du point 11, pièces sans fenêtre, relevés de portefeuille) et 1 pour Applied Digital ;
      - `pending_entity` +22, `financial_parties_only` +10 (corps d'EX-4 d'Applied Digital), `invalid_aggregate` +5.
  - Limite relevée : les véhicules d'un hébergeur (« APLD ELN-02 LLC », « APLD HPC TopCo 2 LLC », etc.) restent des contreparties propres faute de rattachement par extrait, comme ceux de TeraWulf, Cipher, Core Scientific, Nebius et IREN. 113 arêtes d'Applied Digital passent par eux, dont 15 avec CoreWeave (baux, garanties) et 34 avec MIP HPC Holdings, LLC et Macquarie Equipment Capital, Inc. Les extraits existent (« APLD ELN-02 LLC, a subsidiary of the Company »). Rattacher par extrait les véhicules des six hébergeurs est la prochaine correction utile : elle changerait leurs paires et leurs expositions.
  - Tests unitaires : 104 (98 à D-0048), dont le rattachement d'une filiale à une contrepartie. Source : §2.1, §3.6, §10.2, §14, annexes E et F.
- **D-0050 — Filiales des hébergeurs : véhicules rattachés à leur groupe par extrait. Règles fixées avant tout inventaire.** (1) Décision de l'utilisateur, le 2026-10-12 : « ok on continue avec les filiales hébergeurs ». Elle répond au point d'étape du même jour, qui proposait cette correction (D-0049, point 13, limite relevée). Les véhicules d'un hébergeur (« APLD ELN-02 LLC », « Stingray Compute LLC », « Lake Mariner Data LLC »…) se résolvent aujourd'hui en contreparties propres (D-0022) : les arêtes qui les nomment en payeur ou en receveur ne touchent pas leur groupe. Vérification des extraits par l'exécutant, sans sous-agent.

  (2) Périmètre : les six groupes d'hébergeurs, TeraWulf (WULF), Cipher (CIFR), Core Scientific (CORZ), Nebius (NBIS), IREN (IREN) et Applied Digital (APLD). Les autres groupes ne changent pas.

  (3) Candidats (inventaire mécanique) : les dénominations nommées dans une ligne valide (contrepartie, payeur ou receveur) qui portent un suffixe juridique, se résolvent aujourd'hui en contrepartie propre et figurent dans au moins un bloc lu de l'un des six groupes. La ressemblance de nom (« APLD », « Cipher », « IE ») ne sert qu'à ordonner l'inventaire, jamais à rattacher.

  (4) Extrait admis : une phrase d'un bloc déjà lu (fichier d'observations présent), citée mot pour mot, qui nomme l'entité par sa dénomination et la dit filiale du groupe : filiale (« subsidiary »), filiale à 100 %, directe ou indirecte (« wholly owned », « wholly-owned », « indirect »), filiale consolidée, ou entité à intérêts variables consolidée (« primary beneficiary »). La société mère nommée doit être le déclarant du groupe (« the Company », « we », « our », sa dénomination, « the Group » chez IREN) ou une entité déjà rattachée au groupe par un extrait (chaîne d'extraits, chacun cité). Ne suffisent pas : un rôle écrit par le lecteur (`filer_group`), une partie à un contrat avec le groupe, un garant, un co-emprunteur, un « affiliate », une coentreprise mise en équivalence, une entité à intérêts variables non consolidée, une liste de noms sans lien dit.

  (5) Dates : une filiale constituée par le groupe entre sans date (`valid_from: none`), comme les entités déjà confirmées. Une entité acquise n'entre qu'à la date de réalisation de l'acquisition, citée par un extrait ; sans date établie, elle reste contrepartie propre. Une filiale cédée ou déconsolidée sort à la date citée (`valid_to`). Avant l'entrée et après la sortie, l'entité forme son propre groupe (mécanisme de D-0021).

  (6) Traitement : `consolidated_subsidiary`, ou `vie_consolidated` pour une entité à intérêts variables consolidée. Les arêtes entre le groupe et ses filiales deviennent internes (élimination, §10.3) ; celles des autres groupes vers une filiale vont au groupe.

  (7) Écritures : `config.yaml`, `confirmed_entities`, un enregistrement par entité (décision D-0050, bloc, accession, extrait ; note d'appartenance pour une chaîne, une date ou un traitement d'entité à intérêts variables). Les entités vues sans extrait restent des contreparties propres et sont comptées par groupe.

  (8) Ordre et commits : la décision ; l'inventaire et les extraits (un commit) ; le réassemblage (l'extraction des BDC Data Sets n'est refaite que si une dénomination nouvelle entre au registre, D-0043, point 14) ; les rendus ; les résultats ici ; tests, commit, push, rapport.

  (9) Inventaire et extraits, avant tout réassemblage.
  - Candidats (point 3) : WULF 50 entités, CIFR 33, CORZ 100, NBIS 9, IREN 16, APLD 62, surtout des tiers (banques, fournisseurs, clients). Les phrases qui les nomment avec un terme de filiale ont été cherchées mécaniquement dans 554 blocs lus, puis chaque phrase a été relue par l'exécutant. Un premier découpage en phrases coupait après « Inc. » ou « Ltd. » et cachait des extraits (IREN, Nebius) ; il a été corrigé avant la relecture.
  - Retenus : 52 rattachements (`confirmed_entities`, D-0050) et un alias, chaque extrait vérifié mot pour mot dans son bloc, avec son accession :
    - Applied Digital (25) : APLD - Rattlesnake Den I, LLC ; APLD ChronoScale HoldCo LLC ; APLD ComputeCo LLC, 2 et 3 ; APLD DevCo LLC ; APLD ELN-01, ELN-02, ELN-02 C et ELN-03 LLC ; APLD-ELN-02 LLC (graphie à trait d'union, rattachée sans fusion) ; APLD ELN-02 Holdings LLC et APLD HPC Holdings LLC (ancienne et nouvelle dénomination) ; APLD FAR-01 LLC ; APLD GPU-01, LLC ; APLD Holdings 2 LLC ; APLD Hosting, LLC ; APLD HPC TopCo LLC et TopCo 2 LLC ; APLD Intermediate HoldCo LLC ; Applied Digital Cloud Corporation ; Applied Hosting, LLC ; Sai Computing LLC et Sai Computing Holdings LLC ; Ekso Bionics Holdings, Inc., à partir du 5 mai 2026 (acquise par regroupement d'entreprises), avec l'alias ChronoScale Corporation (« Ekso will change its name to ChronoScale Corporation ») ;
    - TeraWulf (11) : Lake Mariner Data LLC, TeraWulf Brookings LLC, WULF Compute LLC, Lake Hawkeye LLC, Big Country Wulf LLC, Raylan Data LLC, DB Long Hunts Data LLC, TeraLease LLC, TeraCub Inc., TeraWulf (Thales) LLC, Akela Data LLC ;
    - Cipher (7) : Cipher Mining Technologies Inc., Cipher Mining Infrastructure LLC, Cipher Compute LLC, Cipher Barber Lake LLC, Cipher Black Pearl LLC, Black Pearl Compute LLC, Stingray Compute LLC ;
    - Core Scientific (2) : Core Scientific Finance I LLC ; Polaris DS LLC, à partir du 13 août 2026 (acquisition réalisée) ;
    - Nebius (3) : Nebius, Inc. ; Nebius Compute II, LLC ; AlphaAI Technologies, Inc. (Tavily), à partir du 19 février 2026 ;
    - IREN (4) : IE US Hardware 3 LLC, IE US Hardware 3 Inc., IE US Hardware 4 Inc., IE CA Leasing Ltd.
  - Restent des contreparties propres, faute d'extrait :
    - APLD FAR Holdings LLC et APLD HPC Holdings 2 LLC, dites seulement « parent » d'un émetteur ;
    - les coentreprises de TeraWulf avec Fluidstack : FS CS I LLC (détenue à 50,1 %), Flash Compute LLC et FS AB LLC, qu'aucun extrait ne dit consolidées ; Allin WULF LLC ;
    - les coentreprises mises en équivalence (Nautilus Cryptomine LLC chez TeraWulf, Alborz LLC chez Cipher), les apparentés (Beowulf, Bitfury) et tous les tiers.
  - Aucune dénomination nouvelle n'entre au registre : l'extraction des BDC Data Sets n'est pas refaite (point 8).

  (10) Effets, au réassemblage (17 groupes, vue `as_known`) :
  - arêtes : 203 arêtes allaient à une contrepartie propre portant le nom d'un véhicule retenu ; elles vont désormais à son groupe (les six hébergeurs passent de 1 050 à 1 278 arêtes). 7 deviennent internes et s'éliminent (132 → 139). Avec les grands groupes : CoreWeave → Applied Digital 0 → 15 arêtes (baux des bâtiments 2 à 4 de Polaris Forge 1, environ 3, 4 et 4 Md$ ; lettre de crédit de 50 M$ ; garanties), Meta → Nebius 4 → 8, Microsoft → Nebius 2 → 4, Microsoft → IREN 2 → 4, Alphabet → Cipher 12 → 13, Alphabet → TeraWulf 8 → 9 ;
  - paires (conclusions de relation) : 83 → 85. Nouvelles, en causalité non établie : Cipher → Fluidstack USA II Inc. (bail de Barber Lake) et TeraWulf → Nautilus Cryptomine LLC (coentreprise mise en équivalence). Applied Digital → CoreWeave passe de « causalité non établie » à « relation commerciale doublée d'un financement » : baux, lettre de crédit et garanties de CoreWeave d'un côté, bons de souscription et garanties d'Applied Digital de l'autre ; recherche complète, aucune pièce de lien (E.0). Les dépendances documentées restent 8 ;
  - cycles : 30 → 38 :
    - Applied Digital → CoreWeave → Applied Digital, concomitant, commercial et financier ;
    - Cipher avec Bitfury Top HoldCo B.V. (concomitant) et avec Luminant ET Services Company LLC (non concomitant), commerciaux et financiers ;
    - cinq boucles de financement seul d'Applied Digital, en causalité non établie : CIM APLD Lender Holdings, LLC, Macquarie Equipment Capital, Inc., MIP HPC Holdings, LLC, MIP VI HPC Holdings, LLC et Sumitomo Mitsui Banking Corporation ;
  - inchangés : événements de l'annexe F (220), paires à financement documenté (16), E.1 et E.2 (32 issues, dont 18 indéterminées ; E.7 « discrimination possible »), E.6 (18 cycles décrits). E.5 : 85 issues, toutes indéterminées ;
  - limite : les véhicules sans extrait (point 9) restent des contreparties propres. Si un extrait disait consolidée la coentreprise de TeraWulf avec Fluidstack (50,1 %), ses arêtes iraient à TeraWulf ;
  - tests unitaires : 104. Source : §3.6, §10.2, §10.3, annexe E.
- **D-0051 — Noms de personnes déjà présents dans les lignes : conservés.** Décision de l'utilisateur, le 2026-10-16 : « Non on les garde, c'est de l'information ». Elle répond au contrôle signalé à la fin de D-0050 : environ 80 mentions de personnes physiques (dirigeants et actionnaires de contrôle nommés par les dépôts) dans les citations, les notes et les rendus de lignes antérieures, dont une ligne hors graphe qui nomme une personne comme contrepartie. Elles restent telles quelles ; aucune correction rétroactive.
- **D-0052 — Ajout de groupes : Dell Technologies (DELL) et Super Micro Computer (SMCI). Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-16 : « Ok ajoute Dell et SMCI au modèle ». Elle suit le point d'étape du même jour sur les entités du modèle. Deux fournisseurs de serveurs d'IA, liés aux groupes présents (NVIDIA, CoreWeave, SpaceX et xAI, IREN, Core Scientific). Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Configuration et date de connaissance : `company_tickers.json` doit résoudre DELL et SMCI ; les CIK attendus sont 1571996 (Dell Technologies Inc.) et 1375365 (Super Micro Computer, Inc.), à vérifier en phase 0. Les deux groupes entrent dans `config.yaml`, avec `group_entry` au 2026-10-16. L'exécution garde l'as_of du 2026-10-07 (D-0048, point 2) : ce qui est tiré maintenant se range sous cet as_of, les dépôts postérieurs sont écartés, le journal garde l'heure réelle des requêtes.

  (3) Mêmes phases et mêmes règles de lecture que les groupes présents (D-0043, D-0048, D-0049) : inventaire, archives XBRL, catalogue des notes, des items et des pièces, lecture complète du texte.

  (4) Calendriers : Dell clôt un exercice de 52 ou 53 semaines fin janvier ou début février, SMCI le 30 juin. Le calendrier les traite comme les exercices décalés déjà présents (clôtures lues sur `period_end`).

  (5) Ruptures d'historique : seulement une fusion inversée, une reprise de coquille ou une cession de l'essentiel de l'activité après laquelle les rapports présentent une autre entité économique (D-0043, point 3 ; D-0048, point 3). N'en sont pas : chez Dell, l'échange des actions de classe V (décembre 2018) et la scission de VMware (1er novembre 2021), présentée ensuite en activités abandonnées, Dell restant la même entité économique ; un retard de dépôt, même de plusieurs exercices, qui relève des signaux de structure (dépôt tardif, changement d'auditeur), comptés comme pour les autres groupes.

  (6) Filiales : la règle de D-0050 (points 3 à 7) s'applique aux véhicules des deux groupes nommés dans les lignes, y compris dans celles des autres groupes (par exemple Dell Marketing L.P., Dell Canada Inc. ou Dell Financial Services L.L.C.). Elle s'applique à l'intégration, après la lecture.

  (7) Découverte (D-0043, point 6) : les lignes déjà lues pour ces déposants vont à leur groupe ; leurs unités encore en file en sortent (`out_of_scope`) ; côté client, la recherche reste incomplète pour un fournisseur que le lexique de la découverte ne nommait pas.

  (8) Les lexiques déjà fixés (unités 6-K de D-0048, point 9 ; termes des montages) ne changent pas.

  (9) Ordre et commits :
  - la décision ;
  - la configuration, la phase 0 et l'univers attendu ;
  - l'index, les archives XBRL et les pièces (phases 0, 1 et 2, réseau en série) ;
  - le catalogue et les listes de lecture, avec leur volume consigné ici avant toute lecture ;
  - la lecture de Dell, puis celle de SMCI, un commit par partie ;
  - l'intégration : filiales par extrait, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (10) Phases 0 à 2 et catalogue, avant toute lecture :
  - CIK confirmés par `company_tickers.json` : 1571996 (Dell Technologies Inc., anciennement Denali Holding Inc.) et 1375365 (Super Micro Computer, Inc.). Exercices clos fin janvier ou début février pour Dell, le 30 juin pour SMCI. Aucune rupture d'historique (point 5) ;
  - inventaire : Dell 38 rapports périodiques, 67 8-K de la tranche, 10 circulaires ; SMCI 39 rapports périodiques, 70 8-K de la tranche, 15 8-K à items de signal, 13 avis de retard (NT 10-K et NT 10-Q), 8 circulaires. Chez SMCI, les rapports des exercices 2017 à 2019 ont été déposés en mai et décembre 2019, et le 10-K 2024 en février 2025 : ce sont des signaux de dépôt tardif (point 5) ;
  - univers attendu : 1 640 cellules pour les deux groupes ;
  - index : 1 467 dépôts, aucun échec. Archives XBRL : 499 dépôts lus ; les 3 échecs sont les amendements sans instance déjà connus (D-0043, point 7). Pièces : 1 485 documents, aucun échec ;
  - catalogue : aucune clé de bloc existante ne change. Dell : 484 blocs à lire, 8,45 M de caractères. SMCI : 450 blocs, 7,72 M de caractères. Les deux fichiers de catalogue s'allongent de 525 blocs pour la tranche et de 409 pour le bloc `text` ;
  - découverte : aucune ligne déjà lue pour ces déposants ; leurs 85 unités encore en file en sortent au réassemblage (point 7).

  (11) Lecture de Dell (2026-10-16), séquentielle, sans sous-agent :
  - 445 blocs lus sur 484 ; les 39 autres sont des corps d'EX-4 (actes de fiducie) arrêtés à leur en-tête, qui ne nomme que des établissements financiers (même règle que pour les groupes présents) ;
  - 1 480 lignes : 1 262 observations et 218 abstentions (133 sans contenu pertinent, 51 hors champ, 33 clauses types sans événement, une concentration de clientèle sans nom : un client à 12 % du chiffre d'affaires de l'exercice 2026). Familles : financement 548, commercial 278, contrepartie versée au client 3, soutien de crédit 1. Signaux : respect des clauses financières 37, faiblesse de contrôle 33 (aucune présente), résiliations 3 ;
  - 176 contreparties nommées. VMware, Inc. porte 261 lignes (notes de parties liées, contrats de 2021 et scission) ; suivent les émetteurs Dell International L.L.C. et EMC Corporation, le fiduciaire The Bank of New York Mellon Trust Company, N.A., les agents et prêteurs des crédits de 2016, 2018, 2019, 2021 et 2026 (annexes de prêteurs lues), les placeurs des émissions, Silver Lake et MSD Capital, L.P. (parties liées des circulaires) ;
  - une correction pendant la lecture : la résiliation du contrat-cadre commercial avec VMware (2021) était portée deux fois, par le 8-K et par la circulaire de 2024 ; la ligne de la circulaire (bloc `ed3b63b7…`) perd son signal et garde l'instrument, le signal reste sur le 8-K (un événement, une ligne de signal) ;
  - trois citations nomment M. Dell, actionnaire de contrôle, dans des lignes dont la contrepartie est une entité (MSD Capital, L.P.) : elles restent (D-0051) ; aucune personne physique n'est contrepartie ;
  - pour l'intégration (point 9) : VMware, Inc. rattaché à DELL par appartenance datée jusqu'à la scission (extrait « a majority-owned subsidiary of Diamond » de l'EX-10.6 du 8-K/A du 2018-11-15), puis à son groupe propre jusqu'à l'entrée dans AVGO ; alias « VMware » vers VMware, Inc. et « MSD Capital, L.P. » vers DFO Management LLC (extrait de la circulaire de 2024) ; véhicules Dell International L.L.C., EMC Corporation, Denali Intermediate Inc. et Dell Inc. par extrait (D-0050).
  (12) Lecture de SMCI (2026-10-16), séquentielle, sans sous-agent :
  - 444 blocs lus sur 450 ; les 6 autres sont des corps d'EX-4 (actes de fiducie des obligations convertibles 2028, 2029 et 2030, titres de 2026) arrêtés à leur en-tête, qui ne nomme que des établissements financiers ;
  - 2 943 lignes : 2 772 observations et 171 abstentions (106 sans contenu pertinent, 21 doublons d'un autre bloc, 19 pièces illisibles (images), 16 hors champ, 5 clients ou fournisseurs désignés par lettre, 4 confirmations d'options plafonnées entre établissements financiers). Familles : commercial 1 589, financement 466, soutien de crédit 5. Signaux : nantissements 31 ; clauses respectées 24 et une rupture (clause de communication financière des obligations 2029 : 10-K 2024 déposé en retard, intérêts spéciaux courus) ; avenants de clauses 17 ; dispenses 3 ; faiblesses de contrôle 28 (16 présentes) ; résiliations 7 ;
  - 84 noms de contreparties, variantes comprises : les parties liées Ablecom et Compuware (plus de 1 700 lignes à elles deux, notes de parties liées et circulaires), Leadtek, Monolithic Power Systems, Green Earth Liang's Inc., Aeon Lighting et Ampera ; les banques de la filiale taïwanaise (CTBC, E.SUN, Chang Hwa, Mega, First Bank, HSBC Taïwan, Yuanta, succursale de Taipei de Bank of America) et celles de SMCI (Bank of America et les prêteurs de 2018, Cathay Bank, JPMorgan et son syndicat de 2025, MUFG) ; 4701 Santa Fe, LLC (bail de Vernon), Lambda, Inc. (sous-licence et participation), Caracol Property Owner LLC, Build Group Inc. (paiement transactionnel de 2,0 M$ sur un contrat de construction), les placeurs et les fiduciaires ;
  - notes sur la dette, les engagements, les baux et les participations saisies par des fonctions de lecture (encours par prêteur pris au tableau, colonne de la date de clôture ; valeur comptable des convertibles ; obligations d'achat ; passif locatif, tranches et revenus de sous-licence de Vernon), chaque phrase nouvelle étant lue ; un registre d'événements fait relever une seule fois chaque signature, avenant, renouvellement, échéance ou résiliation, au bloc le plus récent qui le décrit ; les événements datés au mois seulement portent une période d'un mois, sans date d'événement ;
  - corrections pendant la lecture : la participation dans Ampera perd sa base de mesure (méthode non précisée dans le bloc) ; le bloc `39d8593f…` est dédoublonné (10 lignes ramenées à 5) ; 22 et 24 lignes manquantes sont ajoutées aux notes `a436b113…` et `1129f213…` (faits `smci:` d'abord non repris) ; deux citations de Green Earth sont raccourcies ; cinq lignes sont ajoutées à la note des baux `f7e1bf8b…` (première soumission incomplète après l'échec d'un script) ; les encours Bank of America antérieurs à avril 2018 sont rattachés au crédit de 2016 et non à celui de 2018 (corrigé avant soumission) ;
  - écarts entre sources, laissés tels quels : la date de la revente d'Ablecom au Japon diffère entre la circulaire et la note des parties liées ; le remboursement du prêt HSBC du 9 septembre 2024 vaut 30,0 M$ au 10-K 2025 et 50 M$ dans les 10-Q de l'exercice 2025 (une seule ligne d'événement, celle du 10-K) ;
  - données personnelles : le numéro d'identité de M. Liang (pièce Mega de 2022) et une adresse électronique (pages de signature du contrat de 2018) ne sont pas recopiés ; les noms déjà présents restent (D-0051) ; aucune personne physique n'est contrepartie ;
  - pour l'intégration (point 9) : alias des variantes (Ablecom vers Ablecom Technology Inc. ; Compuware vers Compuware Technology Inc. ; CTBC et CTBC Bank vers CTBC Bank Co., Ltd. ; Chang Hwa Bank vers Chang Hwa Commercial Bank, Ltd. ; Mega Bank vers Mega International Commercial Bank ; E.SUN Bank et E.Sun Commercial Bank, Ltd. en une entité ; First Bank vers First Commercial Bank Co., Ltd. ; Yuanta Bank vers Yuanta Commercial Bank Co., Ltd. ; Bank of America et Bank of America N.A. vers Bank of America, N.A. ; HSBC Bank des lignes taïwanaises vers HSBC Bank (Taiwan) Limited) ; le sous-licencié de Vernon identifié à Lambda, Inc. ; véhicules Super Micro Computer, Inc. Taiwan et Super Micro Computer B.V. par extrait (D-0050).

  (13) Intégration (2026-10-16), dix-neuf groupes, vue `as_known` :
  - rattachements par extrait (point 6 ; D-0050, points 4 et 5), chacun vérifié mot pour mot dans un bloc lu, dans `config.yaml` : Dell Inc., Denali Intermediate Inc. et Dell International L.L.C. ; EMC Corporation et EMC Equity Assets LLC à partir du 2016-09-07 (clôture de la fusion avec EMC, extrait « "EMC Closing" means the closing of the EMC Merger on September 7, 2016 ») ; VMware, Inc. dans DELL du 2016-09-07 au 2021-10-31 (« a majority-owned subsidiary of Diamond », Diamond étant Dell Technologies Inc. ; scission du 1er novembre 2021), groupe propre ensuite, puis AVGO à partir du 2023-11-22 ; Super Micro Computer, Inc. Taiwan. Quinze alias (D-0021) : VMware ; MSD Capital, L.P. vers DFO Management LLC ; Ablecom ; Compuware ; Monolithic Power Systems ; CTBC et CTBC Bank ; Chang Hwa Bank et Chang Hwa Commercial Bank ; First Bank ; Bank of America ; Mega International Commercial Bank et Mega Bank vers Mega International Commercial Bank Co., Ltd. (pièce et 8-K de la même accession) ; HSBC Bank vers HSBC Bank (Taiwan) Limited (même accord) ; Yuanta Bank vers Yuanta Commercial Bank Co., Ltd. (paragraphe du 10-K 2025 placé sous l'intitulé « Yuanta Bank Credit Lines »). Deux entités sans suffixe juridique, identité établie par l'extrait : E.SUN Bank et Cathay Bank ;
  - restent des contreparties propres, faute d'extrait qui les dise filiales : Dell Marketing L.P. (et « Dell Marketing, L.P. »), Dell Canada Inc. et Dell Financial Services L.L.C., nommées par IREN, CoreWeave et Core Scientific (les achats de GPU d'IREN ne vont donc pas à DELL) ; Super Micro Management Consulting Inc. et Super Micro Asia Science and Technology Park, Inc., détenues à 50 %. Trois intentions du point 12 ne se réalisent pas : « E.SUN Bank » et « E.Sun Commercial Bank, Ltd. » restent deux entités, aucun extrait ne les identifiant l'une à l'autre ; les lignes anonymes du sous-licencié de Vernon restent anonymes, le modèle ne rattachant une ligne anonyme par renvoi que pour un montage identifié (D-0046), et les lignes qui nomment Lambda, Inc. (sous-licence, participations) portent déjà l'arête ; Super Micro Computer B.V. n'est nommée dans aucune ligne ;
  - premier réassemblage : observations 11 375 → 15 798, entités 1 440 → 1 702, arêtes 3 772 → 6 271. DELL : 456 arêtes avec des contreparties, dont 145 avec VMware, Inc. après la scission et 165 avec des noms restés en attente (établissements financiers sans suffixe juridique, « Silver Lake » au sens des entités affiliées, actionnaires) ; 31 arêtes avec VMware antérieures à la scission deviennent internes et s'éliminent. SMCI : 1 863 arêtes, dont Compuware 681, Ablecom 677, CTBC 119, E.SUN Bank 63, Bank of America 59, Leadtek 51, Monolithic Power Systems 34, Mega 33, Chang Hwa 29 ; 33 vers des noms en attente. Entre groupes suivis : DELL et AVGO 4 arêtes (VMware après le 2023-11-22), SMCI → APLD 2 (actions et SAFE d'Applied Digital, annexe 6.18 du crédit JPMorgan) ;
  - BDC Data Sets : extraction refaite (D-0043, point 14), archives de 2022 T4 à août 2026 : 2 657 028 lignes de positions, 2 100 dépôts. Second réassemblage : 8 faits et 12 mesures de plus ;
  - correction après le second réassemblage, avant tout commit des rendus : période des archives de la découverte. `period_start()` (`pipeline/discovery.py`) prenait le début de lecture le plus ancien de tous les groupes. Celui de SMCI (2016-07-01) faisait entrer les archives 2016 T3 et 2016 T4 dans la période ; elles n'ont jamais été scannées, et toute recherche côté client devenait `search_incomplete` (D-0037, point 4). E.7 passait ainsi à « les pièces déposées ne permettent pas de discriminer » (85 % d'issues indéterminées, dont 13 pour recherche incomplète), sans aucune pièce nouvelle. Or la période de D-0036 (point 2) est celle des groupes que cherche la découverte, et les groupes ajoutés après le scan (APLD, CIFR, CORZ, DELL, IREN, NBIS, SMCI, WULF) ne sont pas cherchés côté client (D-0043 ; points 7 et 8). Règle : la période se calcule sur les groupes que nomme le lexique. Elle revient au 2017-01-29 et aux 47 archives de D-0036, toutes scannées. Tirer les deux archives de 2016 n'aurait rien apporté : SMCI n'est pas dans le lexique, et aucun groupe du lexique ne lit de période antérieure au 2017-01-29. La piste SoftBank, qui reprend la période de D-0036, suit la même règle. L'alias Yuanta, prévu au point 12 et omis de la configuration, entre au même réassemblage ;
  - troisième réassemblage et rendus : documents 17 915, faits 909 522, observations 15 798, entités 1 702, arêtes 6 271, mesures 105 653, exclusions 22 504. Annexe F : 265 événements (220 avant l'ajout). Paires : 103 (85) ; conclusions : causalité non établie 69 (61), achats réciproques seulement 15 (8), relation commerciale doublée d'un financement 11 (8), dépendance documentée 8 (8). Dix-huit paires nouvelles, aucune disparue : Broadcom → Dell ; Dell → Broadcom, BlackRock, Inc., DFO Management LLC, GIC Private Limited, Temasek Holdings (Private) Limited et VMware, Inc. ; Supermicro → Ablecom Technology Inc, Aeon Lighting Technology Inc., Ampera Inc., Applied Digital, Compuware Technology Inc, Green Earth Liang's Inc., Lambda, Inc., Leadtek Research Inc., Memverge, Inc, Super Micro Asia Science and Technology Park, Inc. et Super Micro Management Consulting Inc. Cycles (E.6) : 46 (38) ; huit nouveaux, aucun disparu : Broadcom → Dell → Broadcom ; Dell → VMware, Inc. → Dell ; Supermicro avec Ablecom, Compuware, CTBC Bank Co., Ltd., Green Earth Liang's Inc., Lambda, Inc. et Leadtek Research Inc. E.7 : discrimination possible, 56 % d'issues indéterminées sur 34 (56 % sur 32 avant l'ajout). Les deux issues nouvelles viennent de la paire Supermicro → Ampera Inc. : E.1 non étayé (Ampera ne dépose pas, la recherche est complète) et E.2 au point de tête indéterminé (précondition non remplie). Les dix-sept autres paires nouvelles ne portent que E.5, non publié ;
  - tests unitaires : 104, tous passés.
- **D-0053 — Ajout de groupes : Hut 8 (HUT) et Galaxy Digital (GLXY). Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-16 : « Ajoute Hut 8 et Galaxy Digital ». Elle suit le rapport d'intégration de Dell et SMCI (D-0052, commit 401fcf1). Deux mineurs devenus hébergeurs et promoteurs de centres de données : Hut 8, et Galaxy Digital, dont le campus Helios est loué à CoreWeave (D-0049, point 12). Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Configuration et date de connaissance : `company_tickers.json` (2026-10-07) résout HUT vers le CIK 1964789 (Hut 8 Corp.) et GLXY vers le CIK 1859392 (Galaxy Digital Inc., anciennement Galaxy Digital Pubco Inc.), à vérifier en phase 0. Les deux groupes entrent dans `config.yaml`, avec `group_entry` au 2026-10-16. L'exécution garde l'as_of du 2026-10-07 (D-0048, point 2) : ce qui est tiré maintenant se range sous cet as_of, les dépôts postérieurs sont écartés, le journal garde l'heure réelle des requêtes.

  (3) Mêmes phases et mêmes règles de lecture que les groupes présents (D-0043, D-0048, D-0049, D-0052) : inventaire, archives XBRL, catalogue des notes, des items et des pièces, lecture complète du texte.

  (4) Hut 8, historique. Hut 8 Corp. est la société de tête créée pour le regroupement de Hut 8 Mining Corp. (CIK 1731805, émetteur privé étranger qui déposait des 40-F et des 6-K en IFRS) et de U.S. Data Mining Group, Inc. (US Bitcoin, CIK 1880323), réalisé fin novembre 2023. La date de réalisation et l'acquéreur comptable s'établissent en phase 0 par un extrait cité du premier rapport postérieur. Règle (§10.1 ; D-0043, point 3) :
  - si l'acquéreur comptable est US Bitcoin, l'historique du groupe est le sien, publié par les rapports de Hut 8 Corp. Hut 8 Mining Corp. n'est pas un prédécesseur, puisque ses états ne se continuent pas dans ceux du groupe : ses dépôts restent hors du groupe et ne se lisent pas. Elle entre dans le groupe comme entité à la date de réalisation, par extrait (D-0050) ;
  - si l'acquéreur comptable est Hut 8 Mining Corp., elle devient prédécesseur, mais ses rapports en IFRS restent hors des séries (invariant (f) ; D-0048, point 4) et ne se lisent pas ;
  - dans les deux cas, le groupe porte `history_left_censored` ; les rapports du CIK pour des périodes closes avant la réalisation et ses autres dépôts antérieurs, s'il y en a, sont hors du groupe (classe `pre_combination`).

  (5) Hut 8, calendrier. US Bitcoin clôturait au 30 juin ; la date de clôture du groupe et une éventuelle période de transition se lisent en phase 0. Un rapport de transition forme un exercice de la durée qu'il couvre, lue dans le rapport (extrait cité), découpé en trimestres de trois mois à partir de son début ; il ne passe jamais pour un exercice de douze mois. La période se consigne dans `config.yaml` (`transition_periods`), jamais dans le code.

  (6) American Bitcoin Corp. (CIK 1755953, anciennement Akerna Corp. puis Gryphon Digital Mining, Inc.) entre dans le groupe HUT comme entité, à la date que donne un extrait qui la dit filiale consolidée (D-0050). Ses propres dépôts ne se lisent pas : une filiale qui dépose seule se lit par les rapports de sa société de tête, comme VMware pour Dell (D-0052, point 11). Ses quatre unités de la découverte, antérieures à son entrée, restent en file.

  (7) Galaxy Digital. Le point 4 de D-0049 est levé sur décision de l'utilisateur : Galaxy Digital Inc. devient un groupe complet. Règles :
  - réorganisation de 2025 (Galaxy Digital Holdings Ltd., société des îles Caïmans cotée à Toronto, remplacée en tête par Galaxy Digital Inc., société du Delaware) : pas de rupture d'historique si les rapports de Galaxy Digital Inc. continuent les états consolidés de Galaxy Digital Holdings LP, ce qu'un extrait établit en phase 0 (D-0052, point 5) ;
  - `reporting_start` : trimestres à partir du premier 10-Q, exercices présentés par le document d'enregistrement (Reg S-X 3-01, 3-02), comme pour CoreWeave et SpaceX ;
  - le bilan, dominé par les actifs numériques et le négoce (raison de D-0049, point 4), se mesure avec les mêmes règles que les autres groupes. Aucune mesure propre n'est ajoutée ;
  - les lignes déjà lues dans les dépôts de Galaxy pour le montage Helios (D-0049, point 12) vont au groupe, comme celles de la découverte (D-0043, point 6). Les quatre véhicules rattachés à la contrepartie Galaxy Digital Inc. (D-0049, point 13) deviennent des filiales du groupe ;
  - la lecture du catalogue ne relève pas une seconde fois un événement ou un encours déjà relevé par ces lignes. Elle reprend leurs clés d'instrument, et un même encours à la même date ne fait qu'une mesure ;
  - les fenêtres du montage tirées des dépôts de Galaxy au-delà du plafond sortent du montage (`out_of_scope`) : ces dépôts se lisent par le catalogue du groupe.

  (8) Filiales : la règle de D-0050 (points 3 à 7) s'applique aux véhicules des deux groupes nommés dans les lignes, y compris dans celles des autres groupes et dans les positions des BDC (par exemple Galaxy Digital LP, Galaxy Digital Partners LLC, Galaxy Helios LLC, Hut 8 Mining Corp.). Elle s'applique à l'intégration, après la lecture.

  (9) Découverte (D-0043, point 6) : aucune ligne déjà lue pour ces déposants ; leurs unités encore en file (5 pour Hut 8 Corp., 4 pour Galaxy Digital Inc.) en sortent (`out_of_scope`) ; côté client, la recherche reste incomplète pour ces deux fournisseurs, que le lexique ne nommait pas.

  (10) Les lexiques déjà fixés (unités 6-K de D-0048, point 9 ; termes des montages) ne changent pas.

  (11) Ordre et commits :
  - la décision ;
  - la configuration, la phase 0 et l'univers attendu ;
  - l'index, les archives XBRL et les pièces (phases 0, 1 et 2, réseau en série) ;
  - le catalogue et les listes de lecture, avec leur volume consigné ici avant toute lecture ;
  - la lecture de Hut 8, puis celle de Galaxy, un commit par partie ;
  - l'intégration : filiales par extrait, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (12) Phases 0 à 2 et catalogue, avant toute lecture :
  - CIK confirmés par `company_tickers.json` : 1964789 (Hut 8 Corp.) et 1859392 (Galaxy Digital Inc.). Exercices clos le 31 décembre ;
  - Hut 8, historique (point 4, premier cas). Le 10-KT 0001558370-24-004176 dit : « The transaction ("Business Combination") was accounted for under the acquisition method with USBTC identified as the accounting acquirer », réalisation du 30 novembre 2023. Le 10-Q du trimestre clos le 30 septembre 2023 (0001104659-23-127101, déposé le 19 décembre 2023, après la réalisation) présente US Bitcoin : « U.S. Data Mining Group, Inc. (d/b/a "US BITCOIN") and Subsidiaries (collectively, the "Company" or "USBTC") ». Il appartient donc à l'historique du groupe. Correction du dernier tiret du point 4 : la règle de D-0043 écarte les rapports qui présentent une autre entité que l'acquéreur comptable, non ceux d'une période close avant la réalisation qui présentent l'acquéreur comptable lui-même. Hut 8 n'en a aucun : pas d'entrée `reverse_combinations`. Le groupe porte `history_left_censored` (premier dépôt du CIK le 2023-02-07) ;
  - Hut 8, calendrier (point 5). Le 10-KT dit : « presented in this Annual Report are for the six months ended December 31, 2023, whereas its fiscal year 2023, 2022, and 2021 are for the twelve months ended June 30 ». La période du 1er juillet au 31 décembre 2023 forme un exercice de deux trimestres, et les exercices synthétiques antérieurs se closent le 30 juin (`transition_periods`). Code : `calendar.apply_transition`, appelé par la phase 0, et deux tests unitaires. Sans cette entrée, le calendrier faisait de 2023 un exercice de douze mois ouvert le 1er janvier. Trimestres attendus à partir du 1er juillet 2023 (`reporting_start`, premier 10-Q) ;
  - Galaxy, historique (point 7). Le 10-Q du deuxième trimestre 2025 (0001859392-25-000030) dit : « On May 13, 2025, the Company (as defined below), GDH Ltd. and GDH LP consummated a series of transactions resulting in the reorganization of the Company's corporate structure » et « The Reorganization Transactions were accounted for as a reverse recapitalization with the Company consolidating GDH LP, which was the accounting acquirer and the predecessor entity ». L'historique est celui de GDH LP, comme le prévoyait le point 7. Mais le 10-Q du premier trimestre 2025 (0001859392-25-000005) ne présente que la société de tête, sans filiale (« the Corporation did not have any subsidiaries and as such the numbers presented [...] are on a stand-alone basis »). C'est le cas de D-0043, point 3 : entrée `reverse_combinations` (réalisation le 2025-05-13), 84 dépôts antérieurs hors du groupe (`pre_combination`), trimestres attendus à partir du 1er avril 2025 (premier 10-Q de l'acquéreur comptable), `history_left_censored` ;
  - inventaire : Hut 8 12 rapports périodiques (dont le 10-KT), 23 8-K de la tranche, 1 8-K à item de signal, 3 circulaires ; Galaxy 5 rapports périodiques, 13 8-K de la tranche, 1 circulaire, 5 documents d'enregistrement de l'offre de mai 2025 ;
  - univers attendu : 1 508 cellules pour les deux groupes (792 pour Hut 8, dont 336 `not_applicable` ; 716 pour Galaxy, dont 476) ;
  - index : 1 530 dépôts (63 nouveaux), aucun échec. Archives XBRL : 516 dépôts lus (17 nouveaux, le 10-Q de Galaxy du premier trimestre 2025 étant hors du groupe) ; les 3 échecs sont ceux déjà connus. Pièces : 1 546 documents (61 nouveaux), aucun échec ;
  - catalogue : aucune clé de bloc déjà lue ne change (la seule clé absente, un bloc de Core Scientific, manquait déjà au dernier assemblage). Le catalogue principal s'allonge de 117 blocs, celui du bloc `text` de 140. Hut 8 : 149 blocs à lire, 4,16 M de caractères, dont 12 corps de pièces pour 3,54 M. Galaxy : 91 blocs, 2,25 M de caractères, dont 8 corps de pièces pour 1,92 M. Les 53 blocs du montage Helios tirés des dépôts de Galaxy, déjà lus (60 lignes), ne sont pas dans la liste (point 7) ;
  - découverte : aucune ligne déjà lue pour ces déposants ; leurs 9 unités encore en file en sortent au réassemblage (point 9).

  (13) Lecture, sans sous-agent (2026-10-16) :
  - Hut 8 : 147 blocs lus sur les 149 clés de la liste ; les deux corps d'EX-4 restants (actes de fiducie des obligations de River Bend et de Beacon Point, Wilmington Trust seul établissement nommé) restent exclus (`financial_parties_only`). 331 lignes : 236 observations (118 de financement, 20 commerciales, 2 de soutien de crédit, 96 sans famille, dont les parties des en-têtes de pièces) et 95 abstentions (24 `no_named_counterparty`, 22 `duplicate_of_other_block`, 15 `boilerplate_no_event`, 14 `out_of_scope_content`, 12 `no_amount`, 8 `no_relevant_content`), aucune rejetée. Commit f9214fe ;
  - Hut 8, contenu : crédits de Coinbase Credit, Inc. (contrat du 26 juin 2023, refontes de janvier 2024, juin 2024, juin et décembre 2025, remboursement de mai 2026) ; prêts d'équipement d'Anchorage Lending CA, LLC (contrats des 31 mars et 26 avril 2022, restructuration du 3 février 2023, remboursement en actions de septembre 2024) ; billet garanti et coentreprise TZRC LLC (50 %, contrat de gestion) ; obligation convertible de Coatue (juin 2024) ; crédits de Two Prime Lending Limited (août 2025) et de FalconX Charlie, Inc. (mai 2026) ; crédit syndiqué de 2026 (JPMorgan Chase Bank, N.A. et onze autres banques) ; obligations de River Bend et de Beacon Point (2042, porteurs non nommés, acheteurs initiaux et fiduciaire en lignes de parties) ; bail de River Bend à Fluidstack USA IV Inc., avec le soutien financier de Google LLC ; programmes d'émission au fil du marché ; regroupement avec Hut 8 Mining Corp. (accord du 6 février 2023, réalisation le 30 novembre 2023, ligne sans famille) ; fusion d'American Bitcoin avec Gryphon Digital Mining, Inc. (mai et septembre 2025) ; crédit renouvelable de Galaxy Digital LLC (22 février 2022, résilié le 17 juin 2024) ; actifs de Validus Power Corp. (opération Far North) et cession-bail avec Macquarie. Le locataire de Beacon Point reste anonyme ;
  - Hut 8, méthode : fonctions de lecture pour les tableaux de dette (colonne de la date de clôture, tableau à trois colonnes du 10-KT) et pour les notes de TZRC (valeur de la participation, coûts refacturés) ; registre des phrases déjà lues ; boucle d'office sur les notes de baux, d'engagements et de méthodes sans phrase nouvelle portant un événement, arrêtée aussi, après correction, sur toute phrase d'événement déjà vue ailleurs. Corrections en place pendant la lecture : six abstentions de notes d'immobilisations (10-Q de 2024 et 2025) passent de `boilerplate_no_event` à `duplicate_of_other_block`, leurs achats (poste électrique de Salt Creek, terrains de Louisiane) étant relevés sur les notes des 10-K 2024 et 2025, vendeurs non nommés ; les liens de faits de deux encours du 10-K 2025 (#1241, #1255), d'abord pris sans période ; trois lignes de disponibilité du crédit de Galaxy, lues dans les déclarations des contrats de Coinbase, deviennent des abstentions une fois sa résiliation du 17 juin 2024 lue ;
  - Galaxy : 89 blocs lus sur les 91 clés ; les deux corps d'EX-4 restants (actes de fiducie des obligations échangeables de 2031 et des obligations d'Helios II, The Bank of New York Mellon seul établissement nommé) restent exclus. 133 lignes : 69 observations (30 de financement, 15 commerciales, 3 de soutien de crédit, 21 sans famille) et 64 abstentions (28 `no_named_counterparty`, 14 `out_of_scope_content`, 12 `duplicate_of_other_block`, 8 `no_relevant_content`, 2 `boilerplate_no_event`), aucune rejetée. Commit d3a27e8 ;
  - Galaxy, contenu : obligations échangeables de 2026, 2029 et 2031 (émissions, principal restant par l'échéancier) ; emprunts de négoce (prêteurs non nommés) ; encours du prêt de Deutsche Bank AG à Galaxy Helios I LLC aux dates que le montage n'a pas (2025-12-31, 2026-03-31) ; contrat de construction de la phase I avec Clayco, Inc. (3 avril 2025, ordre de modification du 13 août 2025) et contrat de commission de Newmark & Company Real Estate Inc. (6 novembre 2024), lus dans le corps du contrat de crédit ; garanties d'achèvement et de recours limité de Galaxy Digital Holdings LP pour Helios I ; GLAS USA LLC, Goldman Sachs & Co. LLC, Morgan Stanley & Co. LLC et The Bank of New York Mellon en lignes de parties ; programme au fil du marché de mai 2026 (Jefferies LLC, BNY Mellon Capital Markets, LLC, UBS Securities LLC) ; placement privé d'octobre 2025 (investisseurs non nommés) ; indemnisation des cautionnements par Galaxy Group Investments LLC et ses commissions ; participation dans Candy Digital, Inc. ; honoraires de sous-conseil de CI Investments Inc. (2022 au premier trimestre 2025, client que les rapports postérieurs ne nomment plus) ; sous-location de Galaxy Investment Partners LLC ; engagements de construction d'Helios, loyers minimaux futurs (4,75 Md$), loyers payés d'avance (150 M$) et avances de clients, preneurs et clients non nommés dans ces blocs ;
  - Galaxy, méthode : les événements et encours déjà relevés par les lignes du montage ne le sont pas une seconde fois, et leurs clés d'instrument sont reprises (point 7) ; l'émission des obligations de 2031 est relevée sur le 8-K de clôture, lu le premier. Correction en place : les loyers payés d'avance de 150 M$, d'abord relevés sur le 10-Q du 2026-06-30 avec la période de leur fait balisé (premier semestre 2025), contredite par le 10-Q du troisième trimestre 2025 (133,3 M$ sur neuf mois) et par le 10-K 2025 (150 M$ sur l'exercice), passent sur le bloc du 10-K 2025, période annuelle et fait annuel ;
  - données personnelles : noms des dirigeants, administrateurs et consultants (personnes physiques) non recopiés, y compris ceux des sociétés qu'ils contrôlent quand le texte les nomme ; aucune personne physique n'est contrepartie.

  (14) Intégration (2026-10-16), vingt et un groupes, vue `as_known` :
  - rattachements par extrait (point 8 ; D-0050), chacun vérifié mot pour mot dans un bloc lu, dans `config.yaml` : pour HUT, Hut 8 Mining Corp. et Hut 8 Holdings Inc. à partir du 2023-11-30 (« As a result of the Business Combination, both Hut 8 and USBTC became wholly-owned subsidiaries of New Hut »), US Data Guardian LLC, Hut 8 DC LLC, Beacon Point DC LLC, Hut 8 MB One LLC, Hut 8 Mining Holding Corp., American Bitcoin Corp. à partir du 2025-03-31 (« a majority-owned subsidiary of the Company ») ; pour GLXY, les quatre véhicules de D-0049 (point 13), Galaxy Digital Holdings LP, Galaxy Helios I LLC, Galaxy Helios Data Centers II LLC et Galaxy Helios II LLC, passent de la contrepartie Galaxy Digital Inc. au groupe (point 7). Deux alias : TZRC vers TZRC LLC, Anchorage vers Anchorage Lending CA, LLC. Une entité par extrait : Two Prime Lending Limited, dénomination complète dont le premier mot (« Two ») se lit comme un quantificateur par la règle des descriptions ;
  - restent des contreparties propres, faute d'extrait qui les dise filiales de Galaxy : Galaxy Digital LLC (crédit de 2022 à Hut 8), Galaxy Digital LP (porteur d'obligations convertibles de Core Scientific), Galaxy Digital Partners LLC (souscripteur de l'introduction en Bourse de CoreWeave) et Galaxy Helios LLC (emprunteur du fonds d'Ares). Restent en attente, faute d'extrait qui les définisse : « Legacy Hut », « Galaxy Digital » (la résiliation du crédit de 2022 ne fait donc pas d'arête entre HUT et GLXY), « Macquarie », « NOGRA » et les banques dont la dénomination n'a pas de suffixe juridique reconnu. Gryphon Digital Mining, Inc. reste une entité propre, distincte d'American Bitcoin Corp. ;
  - code : `load.line_group` fait passer au groupe les lignes du montage lues dans les dépôts d'un déposant devenu groupe suivi (60 lignes de Galaxy, toutes postérieures au 2025-05-13) ; `montages.exclusions` classe `out_of_scope` les 98 fenêtres du montage au-delà du plafond tirées des dépôts de Galaxy, que le catalogue du groupe lit (point 7). Deux tests unitaires ;
  - premier réassemblage : observations 15 798 → 16 262, entités 1 702 → 1 829, arêtes 6 271 → 6 392. HUT : 93 arêtes, dont Coinbase Credit, Inc. 21, Anchorage Lending CA, LLC 18, TZRC LLC 13, Coatue 12, 8 vers des noms en attente, 1 vers GOOGL (soutien financier du bail de River Bend). GLXY : 27 arêtes, dont CRWV 12 (baux d'Helios), CI Investments Inc. 4, Deutsche Bank AG 3, Clayco, Inc. 2. Une abstention de la lecture de TeraWulf, portée par une phrase de renvoi identique à celle d'un 8-K de Hut 8 (même clé de contenu), est comptée dans HUT : le chargeur garde le dernier bloc d'une clé partagée ;
  - BDC Data Sets : extraction refaite (D-0043, point 14), 2 678 553 lignes de positions, 2 100 dépôts. Second réassemblage : aucun fait ni aucune mesure de plus ;
  - rendus : documents 18 185, faits 945 600, observations 16 262, entités 1 829, arêtes 6 392, mesures 112 624, exclusions 22 571. Annexe F : 277 événements (265 avant l'ajout) : Hut 8, F5 sur quatre trimestres (faiblesse significative du contrôle interne, du troisième trimestre 2023 au deuxième trimestre 2025) ; Galaxy, F2 sur cinq trimestres, F6 sur deux, F8 sur un. Paires : 108 (103) ; cinq nouvelles, aucune disparue, toutes en causalité non établie : Galaxy → CoreWeave, Galaxy → CI Investments Inc., Galaxy → Candy Digital Inc., Hut 8 → TZRC LLC, Hut 8 → Fluidstack USA IV Inc. ; conclusions : causalité non établie 74, achats réciproques seulement 15, relation commerciale doublée d'un financement 11, dépendance documentée 8. Cycles (E.6) : 46, inchangés. E.7 : discrimination possible, 56 % d'issues indéterminées sur 36 (56 % sur 34 avant l'ajout) ; les deux issues nouvelles viennent de la paire Galaxy → Candy Digital Inc. : E.1 non étayé (Candy Digital ne dépose pas, recherche complète) et E.2 au point de tête indéterminé (historique tronqué) ;
  - tests unitaires : 108, tous passés.
- **D-0054 — Ajout de groupes : Akamai (AKAM), Backblaze (BLZE) et Riot Platforms (RIOT) ; Lambda et Nscale, groupes économiques non déposants (§10.4). Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-16 : « Ajoute Akamai, Backblaze, Riot Platforms, Nscale et Lambda ». Elle suit le rapport d'intégration de Hut 8 et Galaxy (D-0053, commit 233b31f). Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Statut lu avant tout tirage, dans `company_tickers.json` du 2026-10-07 déjà en cache (aucune requête) :
  - AKAM résout le CIK 1086222 (Akamai Technologies Inc.), BLZE le 1462056 (Backblaze, Inc.), RIOT le 1167419 (Riot Platforms, Inc.). Ces trois sociétés entrent comme groupes complets (`groups`, `group_entry` au 2026-10-16). L'exécution garde l'as_of du 2026-10-07 (D-0048, point 2) : ce qui est tiré maintenant se range sous cet as_of, les dépôts postérieurs sont écartés, le journal garde l'heure réelle des requêtes ;
  - ni Nscale ni Lambda n'y figurent : aucune n'a de titre coté à l'as_of. Elles entrent comme groupes économiques non déposants, sur le modèle de SoftBank (D-0044) : `NF:NSCALE` et `NF:LAMBDA` dans `non_filers`. Ce ne sont pas des laboratoires. Le statut se vérifie à l'intégration, comme au point 9 de D-0044 : aucun rapport périodique de leurs entités dans les archives des Notes Data Sets ni dans les submissions des CIK que la recherche fait apparaître. Si l'une a déposé un rapport périodique avant l'as_of, la règle est revue et consignée ici avant toute lecture de ses rapports. Comme pour un laboratoire, la recherche est alors complète de leur côté pour une paire (E.0) et pour un cycle (bloc `paths`).

  (3) Akamai, Backblaze et Riot : mêmes phases et mêmes règles de lecture que les groupes présents (D-0043, D-0048, D-0052, D-0053) : inventaire, archives XBRL, catalogue des notes, des items et des pièces, lecture complète du texte. Les clôtures se lisent en phase 0 sur `period_end`. Backblaze, introduite en Bourse en novembre 2021, reçoit un `reporting_start` (trimestres à partir du premier 10-Q, exercices présentés par le document d'enregistrement, Reg S-X 3-01 et 3-02, comme CoreWeave et SpaceX) et `history_left_censored` si son premier dépôt suit le début de lecture.

  (4) Ruptures d'historique : règle de D-0052, point 5 (fusion inversée, reprise de coquille, cession de l'essentiel de l'activité après laquelle les rapports présentent une autre entité économique). N'en sont pas : chez Riot, les changements de dénomination (Bioptix, Riot Blockchain, Riot Platforms) et les acquisitions (Whinstone et ESS Metron en 2021, Block Mining en 2024) ; chez Akamai, les acquisitions (Linode en 2022 notamment). La phase 0 le vérifie sur la liste des dépôts (8-K12, dénominations antérieures) et, en cas de doute, par un extrait cité.

  (5) Filiales : la règle de D-0050 (points 3 à 7) s'applique aux véhicules des trois groupes nommés dans les lignes, y compris dans celles des autres groupes et dans les positions des BDC. Elle s'applique à l'intégration, après la lecture.

  (6) Découverte d'origine (D-0043, point 6) : les lignes déjà lues pour ces trois déposants vont à leur groupe ; leurs unités encore en file en sortent (`out_of_scope`) ; côté client, la recherche reste incomplète pour un fournisseur que le lexique de la découverte ne nommait pas. Le lexique, le classement, la file et l'état de lecture de la découverte d'origine ne changent pas (D-0036).

  (7) Lambda et Nscale, niveau 1 : entités réunies par extraits (§10.2, D-0021), comme pour SoftBank (D-0044, points 3 et 7) : la tête de chaque groupe et ses filiales n'y entrent que sur un extrait qui l'affirme, avec sa date. Les lignes déjà lues qui nomment ces entités (par exemple Lambda, Inc. chez Supermicro) vont au groupe par ces extraits, à l'intégration.

  (8) Lambda et Nscale, niveau 2 : la piste des non-déposants (D-0044, points 4 et 5) reçoit leurs termes, sans autre changement :
  - lexique de la piste : « Nscale », en mot entier, insensible à la casse, cible `NF:NSCALE` ; « Lambda, Inc. », « Lambda Inc. » et « Lambda Labs », en mots entiers, sensibles à la casse, cible `NF:LAMBDA`. Jamais « Lambda » seul : le mot désigne aussi le service AWS Lambda d'Amazon, une lettre grecque, des paramètres de modèles et d'autres sociétés (D-0036, point 3) ;
  - Notes Data Sets : les 47 archives de la piste, retirées et scannées avec le lexique d'ensemble enrichi ; recherche plein texte de chaque terme sur les formulaires racines des EX-10. Pas de Form D : le bloc `form_d` ne prend ni Lambda ni Nscale pour sous-jacent ;
  - candidats, classement, règle de lecture (R1, R2) et plafond de 300 unités : ceux de D-0044, point 5, sur l'ensemble de la piste. Les co-mentions restent celles du lexique d'ensemble (groupes du lexique de la découverte, laboratoires, Stargate, non-déposants) ;
  - l'état des unités de SoftBank se garde sous leur clé (accession, document) : rien ne se relit, et une unité déjà lue par la découverte d'origine ou par la piste (même clé de contenu) ne se relit pas ;
  - au-delà du plafond, la lecture s'arrête et le rendement est présenté avant d'aller plus loin.

  (9) Les lexiques déjà fixés (unités 6-K de D-0048, point 9 ; termes des montages ; lexique de la découverte d'origine) ne changent pas.

  (10) Ordre et commits :
  - la décision ;
  - la configuration, la phase 0 et l'univers attendu ;
  - l'index, les archives XBRL et les pièces (phases 0, 1 et 2, réseau en série) ;
  - le catalogue et les listes de lecture, avec leur volume consigné ici avant toute lecture ;
  - la piste des non-déposants (archives, recherche plein texte, pièces, candidats, unités retenues), avec son volume consigné ici avant toute lecture ;
  - la lecture d'Akamai, de Backblaze et de Riot, puis celle des unités de Lambda et Nscale, un commit par partie ;
  - l'intégration : entités et filiales par extrait, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (11) Amendement après la phase 0, avant tout autre tirage : premier exercice d'un nouveau déclarant. Le calendrier tirait l'exercice 2021 de Backblaze des rapports déposés : un seul 10-Q (trimestre clos le 30 septembre 2021, 0001628280-21-025028, déposé après l'introduction en Bourse de novembre) et le 10-K. Il en faisait deux « trimestres », du 1er janvier au 30 septembre puis d'octobre à décembre : la cellule du troisième trimestre aurait couvert neuf mois, et celles des deux premiers manquaient. Règle : un exercice de douze mois dont les premiers trimestres précèdent le premier 10-Q reçoit des trimestres de trois mois depuis son début aux places qu'aucun rapport ne couvre ; les fins de trimestre déposées restent. C'est le cas du point 11 de D-0048 (« premier exercice d'un nouveau déclarant ») quand un rapport trimestriel est déposé. L'exercice se consigne dans `config.yaml` (`first_year_quarters`), jamais dans le code ; code : `calendar.fill_first_year`, appelé par la phase 0, et un test unitaire. Backblaze reçoit aussi `reporting_start` : trimestres à partir du 1er juillet 2021 (EFFECT 9999999995-21-004291 du 2021-11-10, 424B4 0001193125-21-327209, premier 10-Q). Le même défaut touche l'exercice 2020 de Cipher, avant sa recapitalisation inversée : ses cellules sont sans objet (`not_applicable`), il n'est pas corrigé, et aucun autre groupe n'en dépend.

  (12) Phases 0 à 2 et catalogue, avant toute lecture :
  - CIK confirmés par `company_tickers.json` : 1086222 (Akamai Technologies, Inc.), 1462056 (Backblaze, Inc.) et 1167419 (Riot Platforms, Inc.). Exercices clos le 31 décembre ;
  - historique (point 4) : aucune rupture. Les dénominations antérieures de Riot (`formerNames` : Riot Blockchain du 2017-10-04 au 2022-12-19, Bioptix, Venaxis, AspenBio) sont des changements de nom du même déclarant ; ni 8-K12 ni recapitalisation inversée dans la liste des dépôts. Akamai n'a pas de dénomination antérieure. Le premier dépôt de Backblaze (Form D du 2009-04-15) précède le début de lecture : pas de `history_left_censored` ; ses cellules antérieures au 1er juillet 2021 sont sans objet (`reporting_start`, point 11) ;
  - inventaire : Akamai 34 rapports périodiques (26 10-Q, 8 10-K), 23 8-K de la tranche, 9 circulaires ; Backblaze 21 rapports périodiques (15 10-Q, 5 10-K, 1 10-K/A), 14 8-K de la tranche, 1 8-K à item de signal, 5 circulaires, 5 documents d'enregistrement de l'introduction ; Riot 41 rapports périodiques (26 10-Q, 8 10-K, 5 10-K/A, 2 10-Q/A), 85 8-K de la tranche, 3 8-K à item de signal, 9 avis de retard (NT), 13 circulaires ;
  - univers attendu : 2 148 cellules pour les trois groupes (716 chacun ; 56 `not_applicable` pour Backblaze) ;
  - index : 1 779 dépôts (249 nouveaux), aucun échec. Archives XBRL : 608 dépôts lus (92 nouveaux) ; 7 sans instance XBRL, les 3 déjà connus et 4 amendements de Riot (10-K/A 0001079973-19-000239 et 0001079973-20-000321, 10-Q/A 0001079973-19-000014 et 0001079973-19-000116) ; un rapport périodique sans XBRL n'a pas de bloc au catalogue, comme le 10-K/A d'Alphabet. Pièces : 1 797 documents (251 nouveaux), aucun échec ;
  - amendement, documents principaux des rapports antérieurs à l'iXBRL. Le catalogue comptait 31 documents principaux absents (`primary_missing`) : 5 d'Akamai (2018 et premier trimestre 2019), 9 de Riot (2018 au premier trimestre 2020), et 17 de Dell et Supermicro depuis D-0052 (Dell, exercices 2018 et 2019 ; Supermicro, 2016 à 2019, dont les 10-Q/A retraités). Avant l'iXBRL, le document principal n'est pas dans l'archive XBRL. L'exécution d'origine avait tiré ceux des neuf groupes de départ (journal du 2026-10-07, vers 11 h 54), mais aucune phase ne le faisait pour les groupes ajoutés : l'Item 9A et l'Item 4 de ces trimestres manquaient sans motif consigné chez Dell et Supermicro. Règle : un rapport périodique balisé en XBRL mais pas en iXBRL a son document principal parmi les cibles de la phase 2 (`phase2_fetch.pre_ixbrl`, un test unitaire). 31 requêtes, 58,5 Mo, aucun échec, 5 requêtes par seconde au plus ; la phase 2 relancée compte 1 886 cibles, toutes en cache (aucune requête). Les 89 rapports concernés ont désormais leur document principal ;
  - catalogue : aucune clé de bloc déjà lue ne change (la seule clé absente, le bloc de Core Scientific, manquait déjà). Le catalogue principal passe de 2 927 à 3 431 blocs (473 pour les trois groupes avant l'amendement, 31 par l'amendement, dont 14 d'Akamai et de Riot), celui du bloc `text` gagne 505 blocs ;
  - à lire, dans l'ordre de la file (les corps de pièces n'entrent qu'après lecture de leur en-tête) : Akamai 222 blocs, 1,01 M de caractères, plus 26 corps de pièces pour 3,87 M ; Backblaze 195 blocs, 0,68 M, plus 13 corps pour 1,75 M ; Riot 462 blocs, 1,98 M, plus 61 corps pour 3,47 M. Par l'amendement : Dell 6 blocs (5 Item 4, 1 Item 9A ; 17 k caractères) et Supermicro 11 (9 Item 4, 2 Item 9A ; 171 k), lus après Riot, avec leur commit (`grp_dell_d54`, `grp_smci_d54` ; les listes de D-0052 restent) ;
  - découverte d'origine (point 6) : aucune ligne déjà lue pour ces déposants ; leurs 18 unités encore en file (Akamai 2, Backblaze 5, Riot 11) en sortent au réassemblage.

  (13) Piste des non-déposants, avant toute lecture :
  - archives : les 47 archives des Notes Data Sets retirées et scannées sous le lexique d'ensemble lx-a5f53dcc9640 (18,56 Go, effacées après le scan) ; 1 140 lignes de notes nomment un non-déposant ;
  - recherche plein texte des EX-10 : 6 requêtes. « Nscale » donne 25 pièces ; « Lambda, Inc. » et « Lambda Inc. » donnent les mêmes 4 pièces, toutes de 8-K de Supermicro (juin 2024 et janvier 2026), groupe de la liste, donc hors de la piste ; « Lambda Labs » n'en donne aucune. SoftBank est inchangé (296 pièces, en cache). Vérification : 295 pièces nomment un non-déposant, 23 n'en nomment aucun ;
  - statut (point 2), vérifié sur les submissions des CIK que font apparaître la recherche et la liste des noms d'EDGAR déjà en cache (7 requêtes) :
    - NSCALE Ltd (CIK 2110365, dénommée DSNS Holdings Ltd à sa création) : quatre projets confidentiels (DRS et DRS/A, de février à août 2026), puis un S-1 public le 2026-09-18 (0001193125-26-395475). Ni prise d'effet, ni 424B4, ni rapport périodique, ni titre coté : Nscale reste non déposante au sens du point 2. NSCALE LP et NSCALE II LP (Delaware) n'ont chacune déposé qu'un Form D ;
    - Lambda, Inc./DE (CIK 1954966, San Francisco) : deux Form D (2022 et 2024), rien d'autre. Lambda reste non déposante. Le CIK 1821413, dénommé « Lambda Inc. » avant de devenir BloomTech Inc. (l'ancienne Lambda School), n'a aucun lien établi avec Lambda. Une mention de « Lambda Inc. » porte donc ce risque d'homonymie ; la lecture le tranche sur le texte ;
  - candidats et file, règle de D-0044 (point 5) sans changement : 1 435 mentions (SoftBank 1 422, Lambda 8, Nscale 5), 94 candidats, 1 231 unités, dont 78 retenues (R1 40, R2 38). Toutes sont déjà préparées et lues pour SoftBank. Aucune unité de Lambda ni de Nscale n'est retenue. Dix unités les nomment : les notes d'Edge Data Solutions et d'Elastic N.V. pour « Lambda Labs », celles de KinRG pour Nscale, et les pièces EX-10 d'Ionic Digital et de WhiteFiber pour Nscale. Aucune ne nomme une autre cible du lexique d'ensemble (R1), et aucune n'a de montant documenté (R2) : elles restent `out_of_rule`, comptées. Les lignes déjà lues qui nomment Lambda, Inc. vont au groupe par extrait à l'intégration (point 7) : chez Supermicro, la sous-licence de Vernon, la garantie de fait et la participation ; ailleurs, une note d'emprunteur de la découverte d'origine ;
  - amendement, avant toute lecture : le S-1 de Nscale. La règle du nom propre (D-0036) retire d'un document les occurrences du nom de son déclarant. Elle écarte donc les pièces EX-10 du S-1 de NSCALE Ltd : les 23 que la recherche trouve (sur 24) sont les 23 pièces « sans mention » de la vérification. La piste cherchait des tiers qui nomment un non-déposant ; D-0044 n'avait pas prévu qu'un non-déposant dépose lui-même un document d'enregistrement. Or ce S-1 est la seule source publique des contrats de Nscale. Sans lui, « la recherche est complète du côté » de Nscale (point 2) serait faux. Règle : le document d'enregistrement public de la tête d'un groupe non déposant, déposé avant l'as_of, entre dans la piste comme texte propre de ce groupe. Il se lit en entier, comme le texte d'un groupe de la liste (D-0033), et non par la règle R1. Une première version de cet amendement retenait R1 ; elle est écartée avant toute lecture. La validation du découpage a montré, dans les titres du document, un « Dell Vendor Financing ». Or le lexique d'ensemble ne nomme pas les groupes ajoutés depuis D-0043 (Dell, Supermicro, les hébergeurs) : R1 aurait laissé de côté des liens avec des groupes de la liste. Unités :
    - chacune des 24 pièces EX-10 du S-1 : l'en-tête, puis le corps si l'en-tête montre pour partie un groupe de la liste, un laboratoire, Stargate ou un autre non-déposant (règle des corps de D-0044, point 5) ;
    - dans le document principal, l'Item 404 (« Certain Relationships and Related Party Transactions »), borné au titre suivant du sommaire du document. `sections.item_404`, écrit pour les circulaires, débordait sur la description de l'endettement ;
    - chaque note des états financiers annuels audités et intermédiaires, découpée à ses titres (21 et 18 notes) ;
    - niveau 1 : la liste des filiales (EX-21.1). Une entité nommée dans une ligne et inscrite sur la liste entre au groupe par cet extrait, à la date du dépôt (2026-09-18) ;
    - ces unités ne comptent pas dans le plafond de 300, qui borne la file des tiers. Elles se lisent après celles de la piste ;
    - code : `nf_discovery.own_filing_units` et `prepare_own`, configuration `discovery.non_filer.own_filings`, un test unitaire. Au chargement, un bloc de ce dépôt rattache ses lignes au groupe non déposant, et non à un groupe de contrepartie `CP:`.
    - volume, avant lecture : 65 blocs, 286 249 caractères. 24 en-têtes de pièces EX-10 (75 k ; corps possibles ensuite, 7,16 M de caractères au total des 24 pièces), l'Item 404 (26 k), 39 notes (178 k), la liste des filiales (7 k). Liste de lecture `nf_nscale_s1` : l'Item 404, les notes intermédiaires puis annuelles, les en-têtes, la liste des filiales. Requêtes de l'amendement : 3 documents (le document principal, l'EX-10.20 que la recherche ne trouvait pas, l'EX-21.1) et l'index du dépôt.

  (14) Lecture, sans sous-agent (2026-10-16 et 2026-10-17) :
  - Akamai : 240 blocs lus sur 248 de la liste ; les 8 autres sont des corps d'EX-4 (contrats d'émission avec le fiduciaire seul), que §14 ne rouvre pas. 223 observations et 133 abstentions. Lignes principales :
    - Anthropic, PBC : contrat-cadre du 5 mai 2026 (capacité de calcul en nuage dédiée) ; plans de projet 2 et 3 du 18 septembre 2026, environ 11,6 Md$ d'engagement sur sept ans ; bon de souscription remis au client (jusqu'à 387 051 actions de série B, acquis par tranches selon les paiements puis des extensions de 3,0, 6,0 et 9,0 Md$) ;
    - fournisseurs nommés : Lenovo (contrat-cadre du 23 septembre 2026, sans montant) et Jabil (commande d'environ 1,7 Md$ de composants mémoire du 24 septembre 2026) ;
    - financement : six séries d'obligations convertibles de 2018 à 2026 (acheteurs initiaux, fiduciaires, couvertures, encours trimestriels) ; crédits renouvelables de 2018 et 2022 (agent JPMorgan Chase Bank), avenants dont le levier maximal porté à 4,75 pour deux trimestres de 2026 et un nouveau cas de défaut à défaut d'avenant au 31 décembre 2026 (sûretés et garanties possibles) ; crédit non confirmé de 150 M$ de janvier 2025, garanti par des titres ;
    - bail d'un centre de données en Virginie (environ 750 M$ sur douze ans) et sa sous-location à l'affilié d'un grand client de réseau social, non nommé ;
    - signaux : faiblesse significative du contrôle interne (impôts) au 31 décembre 2022 et aux trois premiers trimestres 2023, remédiée au 31 décembre 2023 ; durée d'utilité des serveurs portée de quatre à cinq ans en 2019 et de cinq à six ans en 2023, avec leurs effets ;
  - corrections pendant la lecture d'Akamai : deux encours omis par le premier découpage des notes de dette (obligations 2027 au premier trimestre 2023, obligations 2025 au 31 décembre 2020) sont ajoutés à leur bloc ; l'abstention de la note des immobilisations du 10-K 2019 est remplacée par les effets du changement de durée d'utilité (le registre des phrases déjà vues, qui neutralise les chiffres, l'avait masqué ; une garde sur ces phrases est ajoutée à la boucle) ; le remboursement des obligations 2019, d'abord relevé sans date sur la note du deuxième trimestre 2023, est porté sur le 10-K 2021, qui le date du 15 février 2019.
  - Backblaze : 207 blocs lus sur 208 de la liste ; le dernier est le corps de l'acte d'émission des obligations convertibles 2031 (EX-4.1, fiduciaire seul), que §14 ne rouvre pas. 183 observations et 124 abstentions. Lignes principales :
    - CoreWeave, Inc. : contrat-cadre stratégique du 16 juin 2026 (stockage objet, environ 335 M$ sur les bons de commande initiaux de cinq et sept ans) ; bons de souscription remis au client (3 053 314 et 1 141 562 actions à 7,60 $), dont la juste valeur d'environ 21,7 M$ est déduite de la valeur du contrat ;
    - financement : crédit renouvelable garanti de Citizens Bank, N.A. (20 M$ le 4 juin 2025, cinq avenants jusqu'à 50 M$ et l'échéance du 30 avril 2030 ; encours de 2,5 M$ au 30 septembre 2025, remboursé en octobre) ; crédit de City National Bank (octobre 2021 ; 9,5, puis 30, puis 20 M$ ; encours garantis par une trésorerie nantie de 2022 à 2024 ; résilié le 10 décembre 2024) ; crédit de 2017 de HomeStreet Bank, résilié en octobre 2021 ; financements de primes d'assurance par AFCO Premium Credit LLC (2022 et 2023) ; SAFE de 10,0 M$ d'août 2021 (dont 2,0 M$ de TMT Investments PLC), converti en 722 860 actions à l'introduction en Bourse puis réglé en février 2023 ; obligations convertibles 2031 de 201,25 M$ et options plafonnées ; offre d'actions de novembre 2024 (Oppenheimer & Co. Inc. et Needham & Company, LLC) et introduction en Bourse de novembre 2021 (115,0 M$ bruts) ; prêt PPP de 2020, remis en 2021 ; cessions-bails de 2021 et 2023 avec des fournisseurs non nommés ;
    - baux de centres de données non commencés (2022, 2024, 2025 et 2026), bailleurs non nommés ; paiements à Meaningful Works, partie liée (2023 et 2024) ;
    - signaux : faiblesses significatives de 2021 au troisième trimestre 2024, remédiées au 31 décembre 2024 ; actifs nantis à chaque trimestre où un crédit garanti était en place ; clauses respectées à chaque clôture où le texte le dit ; durée d'utilité des équipements portée à six ans au 1er avril 2025, avec ses effets trimestriels et annuels ;
  - corrections pendant la lecture de Backblaze : le balisage automatique prenait le premier fait candidat de même valeur et de même date de fin ; il préfère désormais le fait de même début, puis le concept qui répond à la nature de la ligne, et deux lignes mal balisées (intérêts du troisième trimestre 2024, effets du premier semestre 2025) sont repassées ; une citation coupée à la virgule décimale (bail non commencé au 30 juin 2025) est corrigée ; les lignes d'actifs nantis des 10-Q de 2026, omises d'abord (le signal se lit trimestre par trimestre), sont ajoutées à leur bloc, ainsi que les intérêts AFCO du premier trimestre 2023, écrits seulement en comparatif au 10-Q du premier trimestre 2024.
  - Riot : 522 blocs lus sur 523 de la liste ; le dernier est le corps de l'acte d'émission des obligations convertibles 2030 (EX-4.1, fiduciaire seul), que §14 ne rouvre pas. 648 observations et 285 abstentions. Lignes principales :
    - fournisseurs de mineurs : MicroBT (contrat-cadre du 23 juin 2023 et bons de commande ; acomptes cumulés, engagement restant et valeur cumulée des commandes à chaque trimestre) ; Bitmain (contrats de 2019 à 2021, puis engagements restants et soldes d'acomptes des tableaux trimestriels de 2020 à 2022, sous une clé commune aux contrats de ces tableaux) ; Midas (refroidissement par immersion, acomptes et engagements de 2023 et 2024) ;
    - financement : crédit de Coinbase Credit, Inc. (2025), crédits renouvelables de 50 M$ et de 20 M$ (2024), obligations convertibles 0,75 % 2030, billet à payer repris avec Block Mining, contrat de crédit et de sûreté d'ESS Metron (encours, tirages, actifs nantis, manquements aux clauses levés par avenants en 2024), billets convertibles garantis de janvier 2019 (trois investisseurs nommés au 8-K), programmes de vente d'actions au marché (agents nommés) ;
    - placements : Bitfarms Ltd. (juste valeur et part détenue par trimestre), billet convertible d'un émetteur non nommé, Coinsquare Ltd. (investissements de 2017 et 2018, dépréciation de 2020, cessions à Mogo en 2021), actions de Mogo Inc. (juste valeur à la réception, perte latente de 2021, vente en 2022), Tess (prise de contrôle de 2017, déconsolidation de 2019, juste valeur résiduelle) et Verady (billet de 2017 converti en 2019) ;
    - acquisitions et compléments de prix : Whinstone (Northern Data AG, 2021 ; complément de prix lié aux crédits d'électricité de la tempête de février 2021), ESS Metron (Ferrie Franzmann Industries, LLC, 2021), Block Mining et E4A Solutions (2024, justes valeurs des compléments de prix), actifs de Prive Technologies LLC et de Blockchain Mining Supply & Services Ltd. (2018) ;
    - litiges, une fois, au bloc le plus récent qui les cite : Northern Data (prix d'achat de Whinstone, demandes de 2022 de plus de 100 M$ et d'environ 40 M$), Rhodium, SBI, GMO (demande initiale de plus de 50 M$, puis de plus de 150 M$), brevets (Malikie, GRC), Kashwise, GRQ Consultants, Inc. ; les actions d'actionnaires, menées par des personnes physiques et sans montant, ne donnent pas de ligne ;
    - engagements et contrats : réservation d'eau de Rockdale (paiement annuel à chaque période, avenant de 2022), bail foncier de Rockdale (avenant de 2022, achat du terrain en 2025), infrastructure d'eau de Corsicana, équipements électriques, baux d'Oklahoma City (7725 Reno #1, LLC ; renouvellements de 2019, fin au 30 juin 2020) et de Fort Lauderdale (résilié en mai 2020), contrat d'hébergement de Coinmint (non renouvelé, fin au 8 juillet 2022), ventes d'électricité à l'ERCOT (2021) ;
    - signaux : actifs nantis et clauses de crédit à chaque clôture où le texte les donne ; durée d'utilité des mineurs portée de deux à trois ans au 1er janvier 2024, avec ses effets.
  - corrections pendant la lecture de Riot : « Northern Data AG », absent du bloc de l'item 1.01, y est remplacé par « Northern Data » ; la ligne de l'item 1.01 du quatrième avenant au bail de Kairos, sans loyer, est remplacée par une abstention, l'avenant étant porté par l'en-tête de la pièce (190 000 $ par mois) ; l'abstention de la note des baux du 10-K 2025 est remplacée par la fin du bail foncier de Rockdale (11,2 M$) ; le balisage automatique, qui choisissait des faits de capacité pour des encours et rattachait l'amortissement du crédit de Coinbase à des faits d'intérêts du crédit de 50 M$, préfère désormais le fait dont la dimension nomme l'instrument (lignes repassées, dont un encours d'ESS Metron rattaché à la valeur nominale au lieu du fait de dette) ; le stade « repaid », hors énumération, devient « settled » ; l'engagement restant envers MicroBT au 30 septembre 2025, écrit « $105.4 » sans unité, est relevé à 105,4 M$ avec une note ; trois événements omis sont portés sur le dernier bloc qui les cite : la demande de Whinstone contre Rhodium (plus de 26,0 M$, 10-K 2023, dont la ligne des demandes reconventionnelles rappelle désormais la demande initiale de 7,0 à 10,0 M$), la juste valeur des actions de Mogo reçues en 2021 (24,8 M$) et la perte latente de 2021 (13,7 M$), ainsi que la demande initiale de GMO (10-Q de mars 2023) ; les valeurs de Tess et de Verady au 31 mars 2020, omises d'abord, sont ajoutées à leur bloc. La boucle de lecture s'arrête sur les notes à mesure par période (motifs fixés), sauf sur les phrases génériques déjà écartées.
  - Dell et Supermicro, blocs de l'amendement du point 12 : Dell, 6 blocs (Item 4 des 10-Q des exercices 2018 et 2019, Item 9A du 10-K de l'exercice 2018), contrôles efficaces à chaque date, 6 signaux `material_weakness` absents. Supermicro, 11 blocs, 11 signaux présents ou absents selon le document : faiblesses significatives au 30 juin 2017 et au 30 juin 2019 (Item 9A) et aux trois premiers trimestres de l'exercice 2019 ; les trois 10-Q de l'exercice 2017 concluaient à l'efficacité (signal absent, date de connaissance du dépôt d'origine), leurs 10-Q/A de mai 2019 révisent la conclusion (signal présent, à la date de l'amendement).
  - Nscale, unités du S-1 (point 13) : 68 blocs lus sur 68 de la liste `nf_nscale_s1` (539 742 caractères) : l'Item 404, les 39 notes (18 intermédiaires, 21 annuelles), les en-têtes des 24 pièces EX-10, la liste des filiales et les corps des 3 pièces dont l'en-tête montre un groupe de la liste ou un laboratoire (bon de travail de Microsoft, EX-10.19 ; contrat-cadre de Dell Financial Services, EX-10.20 ; commande de services de GPU d'Anthropic, EX-10.25), ajoutés au catalogue et à la liste après lecture de leur en-tête (`nf_discovery body`, sans requête, 253 493 caractères). 229 observations et 32 abstentions. Lignes principales :
    - clients : Microsoft Ireland Operations Limited (bon de travail de Kvandal North, à Narvik : GPU NVIDIA VR200 en trois tranches sur six ans, colocation de 6 MW, avances du client ; montants caviardés ; garantie de Microsoft Corporation seulement en cas de cession à une filiale) ; Anthropic PBC (une tranche sur quatre d'un site caviardé, systèmes NVIDIA Vera Rubin NVL72, sous condition d'un financement qualifiant avant une date butoir) ; NVIDIA Corporation (contrat-cadre de services en nuage de juillet 2025, 1,2 Md$ de bons de commande) ; contrats de grappes de GPU de clients non nommés (62,9 Md$ depuis le 31 décembre 2025) ;
    - parties liées : Arkon Energy (ancienne société mère : apport de Nscale Holdings B.V. en 2024, prêts échangés contre des actions en mai 2025, achats de deux sociétés de terrains, réorganisation de mai 2026 avec séquestre et engagement de payer environ 5,0 M$ de frais) ; Aker ASA (coentreprise de Stargate Norvège, série B) ; NVIDIA (garantie du bail du comté de Ward, SAFE antérieur à la série C, souscription de 1,0 Md$ du 15 septembre 2026) ; Sandton (prêts à terme, bons sur Nscale AS, obligations de série A) ; OpenAI (Stargate UK, ligne sans famille, retrait en avril 2026) ;
    - financement : obligations convertibles de série A (155,0 M$, dont 50 M$ vendus à AF Realizations S.à r.l. selon le préambule du sixième avenant de Sandton, sans période pour ne pas les additionner), séries B et C, SAFE, obligations convertibles 2028 ; crédits de Macquarie (crédit senior de juin 2025, modifié et refondu le 22 septembre 2025 ; crédit islandais de 331 893 517 $) ; crédit des GPU du 11 février 2026 (1,4 Md$, agents GLAS, trois amendements) ; crédit renouvelable du 8 mai 2026 (770,0 puis 900,0 M$, agent JPMorgan Chase Bank, N.A.) ; crédits de Kvandal South (agent DNB Bank ASA), du comté de Ward (1,85 Md$) et de Caroline du Nord (1,2 Md$), agent U.S. Bank Trust Company, National Association ; les en-têtes nomment les arrangeurs, inconnus des notes ; contrat-cadre de financement de location de Dell Financial Services (formulaire, sûreté sur les produits) ;
    - acquisitions : Future Tech S.C.I. Limited (2025), campus Monarch (2026, dont American Intelligence & Power Corporation), site SIN02 (2026) et Anyscale (accord de juillet 2026) ;
    - signaux : doute sur la continuité d'exploitation, levé (signal absent) ; manquements au contrat de crédit et de sûreté de Sandton, dont l'EBITDA glissant minimal, levés par le sixième avenant du 12 mai 2025 ; dérogation n° 1 du 29 avril 2026 à l'acte de sûreté du crédit des GPU (notifications et accusés de réception d'Alpha Bank non obtenus dans le délai) ; amendement n° 2 de ce crédit (assurance cyber) noté sans signal, faute de clause financière ; actifs nantis ;
    - liste des filiales : 138 lignes (137 noms, « Nscale GPU Holdings Limited » deux fois). Seules les 25 filiales nommées dans des lignes y sont relevées, avec la tête, Nscale Limited (future Nscale plc) ; elles entrent au groupe à l'intégration (point 7) ;
  - corrections pendant la lecture de Nscale : trois sociétés d'Arkon Energy, d'abord notées sociétés du groupe à l'en-tête du sixième avenant de Sandton, ne figurent pas sur la liste des filiales du 18 septembre 2026 ; leurs lignes prennent le rôle du contrat (emprunteur, partie, garant), sans rattachement. Nscale Portugal, Unipessoal, LDA, absente de la liste sous ce nom, porte la même réserve. Les noms des personnes physiques des contrats de travail, des lettres d'offre et des blocs de signature ne sont pas repris (D-0051).
  - Lambda : aucune unité propre (deux Form D seulement, point 13) ; ses lignes viennent des blocs de Supermicro déjà lus et vont au groupe par extrait à l'intégration.

  (15) Intégration (2026-10-17), vingt-quatre groupes et trois non-déposants, vue `as_known` :
  - statut des non-déposants (point 2) : ni NSCALE Ltd (CIK 2110365) ni Lambda, Inc. (CIK 1954966), ni l'homonyme devenu BloomTech Inc. (CIK 1821413), n'a de soumission dans les 47 archives des Notes Data Sets (708 495 soumissions) ; le seul nom approchant, ColAmbda Technologies, Inc. (CIK 1104462), est sans lien. La recherche reste complète de leur côté ;
  - rattachements par extrait (points 5 et 7 ; D-0050), chacun vérifié mot pour mot dans un bloc lu, dans `config.yaml` :
    - Nscale (`NF:NSCALE`) : la tête, Nscale Limited (future Nscale plc), et les 25 filiales de la liste (pièce 21.1) nommées dans des lignes, entrées à la date du dépôt (2026-09-18), sauf deux que les notes annuelles datent plus tôt et qui entrent sans date : Nscale Global Holdings Limited, société de tête avant la réorganisation du 4 mai 2026 (« The share-for-share exchange is regarded as a transaction under common ownership » ; comparatifs présentés depuis le 1er janvier 2024), et Nscale Services UK Ltd (« through our wholly-owned subsidiary, Nscale Services UK Limited ("NS UK") »). Arkon Energy Pty Ltd, détenue par Nscale Limited depuis la réorganisation (« As a result, Nscale Limited is the ultimate holding company of Arkon Energy and, directly and indirectly, NGHL »), entre le 4 mai 2026, bien qu'absente de la liste ;
    - Lambda (`NF:LAMBDA`) : la tête, Lambda, Inc. (« LAMBDA, INC., a Delaware corporation ("Sublicensee") », sous-licence de Vernon, 8-K de Supermicro du 21 juin 2024) ;
    - Riot : Whinstone US, Inc. à partir du 2021-05-26 et Ferrie Franzmann Industries, LLC (ESS Metron) à partir du 2021-12-01 (« its wholly-owned subsidiaries, Whinstone US, Inc. and Ferrie Franzmann Industries, LLC (d/b/a ESS Metron) », dates du 10-Q et du 8-K de réalisation) ; Kairos Global Technology, Inc. et sa graphie Kairos Global Technologies, Inc., puis Riot DC Logistics, LLC, sans date. Akamai et Backblaze : aucun véhicule nommé dans une ligne ;
    - dix alias (D-0021) : Whinstone ; ESS Metron ; MicroBT et Super Acme Technology (Hong Kong) Ltd. vers SuperAcme Technology (Hong Kong) Limited ; Midas et Midas Immersion Cooling, LLC vers Midas Green Technologies, LLC ; Coinmint ; Mogo ; Arkon Energy ; Aker vers Aker ASA. Une entité par extrait : City National Bank ;
  - restent des contreparties propres, faute d'extrait : Microsoft Ireland Operations Limited, cocontractante du bon de travail de Kvandal North (aucun bloc lu ne la dit filiale de Microsoft : ses arêtes ne vont pas à MSFT) ; Nscale GPU MCC B1.1 LLC, fournisseur de la commande d'Anthropic (« Controlled Affiliate of Parent », « Parent » non défini dans le texte non caviardé : la commande ne touche pas `NF:NSCALE`) ; Block Mining, Inc. (« we acquired 100% of the equity interests », sans terme de filiale) ; Logical Brokerage Corp. (réalisation non datée) ; Riot Corsicana, LLC (« an affiliate of Riot Platforms, Inc. ») ; RiotX Holdings, Inc. Restent en attente : Dell Financial Services (aucune arête vers DELL), « Bitmain » et « Rhodium » (chacun défini pour deux entités selon le document), Tess, HomeStreet Bank, J.P. Morgan Securities, Sandton, Macquarie, PEGA, Aker Nscale JV ;
  - corrections avant les rendus, chacune avec son test :
    - suffixes juridiques (`entities.LEGAL_SUFFIX`) : la normalisation retire les points avant de ramener les suffixes, si bien que « L.P. », « p.l.c. » et « S.à r.l. » n'étaient jamais reconnus ; les formes AS, ASA, AB, Abp NUF, Oy, ehf, DA, GK et Lda manquaient. 33 dénominations deviennent des entités propres (D-0022), dont 22 déjà nommées avant l'ajout (20 en « L.P. ») ; 49 arêtes les touchent (16 à montant), dont 27 dans des groupes déjà suivis (CORZ 9, WULF 5, APLD 4, IREN 3, AVGO 3, AMD 2, GOOGL 1). Trois paires en naissent : Alphabet → Technology Impact Growth Fund II, L.P. ; Applied Digital → MIP VI DC REIT AIV, L.P. et MIP VI REIT AIV, L.P. Limite non corrigée : « L.L.C. » et « LLC » donnent deux normalisations distinctes (« 7725 RENO #1, L.L.C. » et « 7725 Reno #1, LLC », deux entités pour un même bailleur de Riot) ; la correction changerait les identifiants de toutes les entités ;
    - énumération `block_kind` : `discovery_item_404` et `discovery_entity_list` manquaient, le chargement des observations échouait (`schema.sql` régénéré depuis le registre) ;
    - « the Company » du S-1 de Nscale (`links.build_edges`) : le déposant d'un bloc ne se rattachait qu'à la tête d'un groupe de `config.yaml` ; 67 des 70 arêtes de Nscale restaient sans groupe au premier réassemblage. La tête d'un groupe non déposant, confirmée par extrait, la désigne désormais ;
  - premier réassemblage : observations 16 262 → 18 136, entités 1 829 → 2 186, liens 6 392 → 6 976. Arêtes : AKAM 15 (Anthropic 3, JPMorgan Chase Bank, N.A. et J.P. Morgan Securities LLC, Citigroup Global Markets Inc., Lenovo, Jabil) ; BLZE 59 (City National Bank 28, AFCO Premium Credit LLC 14, Citizens Bank, N.A. 5, CoreWeave 5) ; RIOT 192 (SuperAcme 32, « Bitmain » 27 en attente, Coinbase Credit, Inc. 23, Bitfarms Ltd. 15, Midas 10, AMD 2 ; 35 vers des noms en attente) ; `NF:NSCALE` 67 (NVIDIA 10, deux fonds de Sandton 11, Macquarie Bank Limited 6, Arkon Energy 6 dont 2 internes après le 4 mai 2026, Aker ASA 5, Microsoft Ireland Operations Limited 2 ; 16 vers des noms en attente) ; `NF:LAMBDA` 4 (Supermicro). Entre groupes suivis : Anthropic → Akamai (environ 11,6 Md$ d'engagement) et le bon de souscription en retour ; CoreWeave → Backblaze (environ 335 M$) et les bons en retour (21,7 M$ de juste valeur) ; AMD → Riot (bail de Rockdale, 311 M$ de loyers) ; NVIDIA → Nscale (contrat-cadre de services en nuage de 1,2 Md$, séries B et C, SAFE, souscription de 1,0 Md$ de septembre 2026) et Nscale → NVIDIA (bons et séquestre en contrepartie de la garantie du bail du comté de Ward) ; Supermicro → Lambda (participations de séries C à E, sous-licence de Vernon) ;
  - BDC Data Sets : extraction refaite (D-0043, point 14), 2 906 656 lignes de positions (2 678 553 avant), 2 100 dépôts. Cinq BDC de Blue Owl (Blue Owl Capital Corp, Blue Owl Capital Corp II, Blue Owl Credit Income Corp., Blue Owl Technology Finance Corp., Blue Owl Technology Income Corp.) détiennent des actions de préférence de série B de Nscale Global Holdings Limited puis de Nscale Limited (coût de 50 M$ ; juste valeur de 91 M$ au 31 mars 2026, 1,83 x, et de 87 M$ au 30 juin 2026), et des parts du prêt à tirages différés de Nscale Services UK Ltd (crédit des GPU, 11 M$ au 31 mars 2026) : les prêteurs que les notes de Nscale ne nomment pas. Trinity Capital Inc. a prêté à Backblaze de 2022 à 2024 (10 M$ au 31 mars 2023). Second réassemblage : 264 faits et 96 mesures de plus ; un troisième, après l'entrée sans date de NGHL et de Nscale Services UK Ltd, place ces positions sous `NF:NSCALE` (96 cellules) ;
  - rendus : documents 19 439, faits 1 083 356, observations 18 136, entités 2 185, liens 6 976, mesures 124 024, exclusions 22 789 ; 8 432 nombres publiés. Annexe F : 344 événements (277 avant l'ajout) : Akamai 5 (F5 du quatrième trimestre 2022 au troisième trimestre 2023, F4 une fois), Backblaze 27 (F5 13, F2 10, F4 3, F1 1), Riot 35 (F2 21, F5 8, F4 3, F8 2, F1 1) ; les non-déposants n'ont pas de rapport périodique, donc aucune cellule. Paires : 129 (108) ; 22 nouvelles, une renommée (Supermicro → Lambda, Inc. devient Supermicro → Lambda) ; conclusions : causalité non établie 92 (74), achats réciproques seulement 16 (15), relation commerciale doublée d'un financement 13 (11 ; nouvelles : Akamai → Anthropic et Backblaze → CoreWeave), dépendance documentée 8 (8). Paires à financement documenté : 29 (18). Cycles (E.6) : 52 (46) ; nouveaux : Akamai ↔ Anthropic et Backblaze ↔ CoreWeave (commerciaux et financiers, recherche complète), NVIDIA ↔ Nscale (recherche complète), Backblaze ↔ AFCO Premium Credit LLC, Backblaze ↔ City National Bank, Riot ↔ Coinbase Credit, Inc. ; Supermicro ↔ Lambda remplace Supermicro ↔ Lambda, Inc., désormais en recherche complète. E.7 : discrimination possible, 57 % d'issues indéterminées sur 56 (56 % sur 36 avant l'ajout) ; E.1 non étayé 24 (16) ;
  - tests unitaires : 118, tous passés.
- **D-0055 — Ajout de groupes : Blue Owl (OWL), Apollo (APO) et Blackstone (BX), gestionnaires d'actifs. Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-17 : « Ajoute Blue Owl, Apollo et Blackstone ». Elle suit le rapport d'intégration d'Akamai, Backblaze, Riot, Nscale et Lambda (D-0054, commit 892da92). Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Statut lu avant tout tirage, dans `company_tickers.json` du 2026-10-07 déjà en cache (aucune requête) : OWL résout le CIK 1823945 (BLUE OWL CAPITAL INC.), APO le 1858681 (Apollo Global Management, Inc.), BX le 1393818 (Blackstone Inc.). Les trois sociétés entrent comme groupes complets (`groups`, `group_entry` au 2026-10-17). L'exécution garde l'as_of du 2026-10-07 (D-0048, point 2) : ce qui est tiré maintenant se range sous cet as_of, les dépôts postérieurs sont écartés, le journal garde l'heure réelle des requêtes.

  (3) Mêmes phases et mêmes règles de lecture que les groupes présents (D-0043, D-0048, D-0052 à D-0054) : inventaire, archives XBRL, catalogue des notes, des items et des pièces, lecture complète du texte. Les clôtures se lisent en phase 0 sur `period_end`.

  (4) Successions et ruptures d'historique, vérifiées en phase 0 sur la liste des dépôts (8-K12, `formerNames`, items 2.01 et 3.03) et par un extrait cité :
  - Blue Owl : le CIK 1823945 a d'abord été celui de la SPAC Altimar Acquisition Corporation ; le regroupement avec Owl Rock Capital Group et Dyal Capital Partners a été réalisé en mai 2021. Si un extrait dit que l'acquéreur comptable n'est pas la SPAC, la règle `reverse_combinations` de D-0043 (point 3) s'applique : les rapports du CIK pour les périodes closes avant la réalisation et ses autres dépôts antérieurs sont hors du groupe (`pre_combination`), le groupe porte `history_left_censored`, et `reporting_start` fait commencer les trimestres au premier 10-Q de l'acquéreur comptable. Les états antérieurs de l'acquéreur comptable publiés seulement dans la circulaire ou le document d'enregistrement de la SPAC ne se lisent pas, comme pour TeraWulf, Cipher et Core Scientific ;
  - Apollo : le CIK 1858681 (d'abord Tango Holdings, Inc.) est devenu la tête du groupe le 1er janvier 2022, par les fusions avec Apollo Asset Management, Inc. (anciennement Apollo Global Management, Inc., CIK 1411494) et avec Athene Holding Ltd. (CIK 1527469). Règle des prédécesseurs (§10.1), comme pour Broadcom et Marvell : si une pièce citée (8-K12B ou rapport) établit qu'AGM succède à AAM comme émetteur et que ses états consolidés continuent ceux d'AAM, le CIK 1411494 entre dans `predecessors`, tête du groupe jusqu'à la succession que date sa pièce. Si la phase 0 montre autre chose, la règle est revue et consignée ici avant toute lecture ;
  - un seul rapport par période et par groupe. Pour une période close avant la succession, le rapport du prédécesseur ; un rapport du successeur pour une telle période qui ne présente que la nouvelle société de tête, sans filiale, reste hors du groupe (comme le 10-Q de Galaxy Digital Inc. du premier trimestre 2025, D-0053). Pour une période close après la succession, les rapports du successeur seuls ; ceux que le prédécesseur déposerait encore comme filiale sont des rapports de filiale, hors des séries et du texte du groupe (`out_of_scope`, comptés). Les dates de succession des prédécesseurs, aujourd'hui écrites dans `graph.py` pour Broadcom, Avago et Marvell, passent dans `config.yaml` avec leur pièce ; l'univers et les tables des groupes présents ne doivent pas changer (vérifié avant tout tirage) ;
  - ne sont pas des ruptures : chez Blackstone, la conversion de The Blackstone Group L.P. en société par actions (1er juillet 2019) et ses changements de dénomination (The Blackstone Group Inc., puis Blackstone Inc.) ; chez Apollo, la conversion d'Apollo Global Management, LLC en société par actions (2019), puis la fusion avec Athene, si l'acquéreur comptable continue l'historique : c'est un changement de périmètre (§10.2), traité comme toute acquisition ; chez les trois, leurs acquisitions (Oak Street, IPI Partners, Kuvare ou Atalaya chez Blue Owl ; Griffin ou Bridge chez Apollo, par exemple).

  (5) Gestionnaires et fonds. Règle de §10.2 : « Les entités de l'EX-21 et les véhicules consolidés, fonds de capital-risque compris, sont membres de leur groupe ; un fonds géré mais non consolidé ne donne qu'une arête `relation` ».
  - Membres : la tête, ses filiales, et les fonds et véhicules qu'elle consolide (fonds consolidés, CLO, entités à intérêts variables dont elle est le principal bénéficiaire), rattachés par extrait selon D-0050 (points 3 à 7), avec le traitement `consolidated_subsidiary` ou `vie_consolidated`.
  - Ne sont pas membres : les fonds gérés mais non consolidés et leurs véhicules, même quand leur nom porte la marque du gestionnaire (BDC, fonds immobiliers, fonds privés, véhicules détenus par des fonds : Blue Owl Real Estate Net Lease Trust, Beignet Investor LLC, WarehouseCo Intermediate Holdings LP, Blackstone Private Credit Fund…). Chacun reste une entité et un groupe propres (D-0022). Ses liens avec le gestionnaire viennent des lignes qui les décrivent : commissions, engagements, garanties.
  - Athene Holding Ltd. entre dans APO à la date de réalisation de la fusion, sur un extrait qui la dit filiale (D-0050, point 5) ; avant, elle forme son propre groupe. Même règle pour toute entité acquise par l'un des trois groupes.
  - Une partie qu'un bloc ne désigne que comme des fonds gérés par le gestionnaire (« funds managed by X », « X-managed funds », « an affiliate of funds managed by X ») est une description (D-0022) : elle reste en attente et ne va pas au groupe du gestionnaire.
  - Correction dans la passe (D-0020), lignes déjà lues. Trois lignes de Meta (D-0046, bloc 4495846547b3) portent la contrepartie « Blue Owl Capital, Inc. ». Or le bloc désigne l'investisseur comme « an affiliate of funds managed by Blue Owl Capital, Inc. (the Investor) », et le bailleur et le bénéficiaire de la garantie comme « the Venture ». Une fois Blue Owl devenu groupe, ces lignes mettraient sur Blue Owl Capital Inc. des baux d'environ 12,3 Md$, une garantie de 28 Md$ et une distribution de 2,6 Md$ qui reviennent à la coentreprise et à l'affilié des fonds. Leur contrepartie devient la désignation du bloc, « an affiliate of funds managed by Blue Owl Capital, Inc. » : les lignes restent visibles, en attente, hors des agrégats. Conséquence connue d'avance : le cycle Meta → Blue Owl Capital, Inc. → Meta (D-0046, point 10) sort de E.6. L'identification de la coentreprise (`identified_ventures`) et les lignes de Blue Owl Real Estate Net Lease Trust ne changent pas. Toute autre ligne dans le même cas, relevée à l'intégration, reçoit le même traitement et se liste ici.
  - Noms courts : « Apollo », « Blackstone », « Blue Owl » et « Owl Rock » ne deviennent pas des alias d'une tête de groupe (D-0021). Dans les documents des tiers, le nom court d'un gestionnaire désigne souvent ses fonds : le 10-Q de Broadcom écrit « we arranged for Apollo ("investor partner") » (D-0049), et cette ligne reste en attente. Un alias valant pour toutes les lignes, un bloc qui définit le nom court comme la tête fait corriger ses lignes dans la passe, vers la dénomination définie ; il ne crée pas d'alias.

  (6) Montages : les deux montages existants (`meta_hyperion`, `athene_whco`) ne changent pas (requêtes, termes, blocs, clés de contenu). Un bloc du catalogue d'un groupe qui a la clé de contenu d'un bloc de montage déjà lu ne se relit pas. Leurs lignes vont aux groupes par les règles du point 5.

  (7) BDC :
  - bloc `lender` : les positions des BDC sur les entités des trois groupes viennent de l'extraction refaite après le premier réassemblage (D-0043, point 14) ;
  - blocs `lender_portfolio` et `lender_liabilities` : les plateformes de présentation (D-0045, point 3) reçoivent Apollo et Blackstone, par la même règle : la dénomination EDGAR, actuelle ou ancienne, porte « Apollo » ou « Blackstone ». Relevé des dénominations, fait sans aucune valeur : Apollo, cinq véhicules (MidCap Financial Investment Corp, anciennement Apollo Investment Corp ; Apollo Debt Solutions BDC ; MidCap Apollo Institutional Private Lending, anciennement Middle Market Apollo Institutional Private Lending ; Apollo Origination II (UL) Capital Trust ; Apollo Origination II (Levered) Capital Trust) ; Blackstone, trois (Blackstone Secured Lending Fund, anciennement Blackstone / GSO Secured Lending Fund ; Blackstone Private Credit Fund ; Blackstone Private Real Estate Credit & Income Fund). C'est un regroupement de présentation, pas un groupe économique : ces fonds ne sont pas consolidés par leur gestionnaire (point 5), et rien ne s'additionne entre véhicules. Les repères nommés de D-0045 ne changent pas ; les deux repères de Blackstone figurent aussi dans sa plateforme. La lecture des 8-K de D-0047 (point 7) reste limitée aux véhicules de Blue Owl et à ceux où F16 tombe. C'est un choix de l'exécutant, soumis à l'utilisateur : le retirer revient à supprimer les deux entrées de `platforms`.

  (8) Découverte d'origine (D-0043, point 6) : les lignes déjà lues pour ces trois déposants vont à leur groupe (chez Apollo, la note d'engagements du 10-Q du deuxième trimestre 2026, bloc 29f74ba9f6b1, rang 1 de la découverte) ; leurs unités encore en file en sortent (`out_of_scope`) ; côté client, la recherche reste incomplète pour un fournisseur que le lexique de la découverte ne nommait pas. Les lignes des blocs déposés par une entité qui entre dans un groupe par extrait (Athene Holding Ltd.) vont à ce groupe aux dates de l'appartenance. Le lexique, le classement, la file et l'état de lecture de la découverte d'origine ne changent pas (D-0036).

  (9) Les lexiques déjà fixés (unités 6-K de D-0048, point 9 ; termes des montages ; lexique de la découverte d'origine ; piste des non-déposants) ne changent pas.

  (10) Données personnelles : les dépôts de ces gestionnaires nomment beaucoup de personnes physiques (fondateurs, dirigeants, associés) dans les circulaires, les notes de parties liées et les pièces. Aucune personne physique n'est contrepartie, et les noms des contrats de travail, des lettres d'offre et des blocs de signature ne sont pas repris (D-0051).

  (11) Ordre et commits :
  - la décision ;
  - la configuration (successions déplacées du code, test unitaire), la phase 0 et l'univers attendu ;
  - l'index, les archives XBRL et les pièces (phases 0, 1 et 2, réseau en série) ;
  - le catalogue et les listes de lecture, avec leur volume consigné ici avant toute lecture ;
  - la lecture de Blue Owl, puis celle d'Apollo, puis celle de Blackstone, un commit par groupe ;
  - l'intégration : entités et filiales par extrait, corrections du point 5, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (12) Phases 0 à 2 et catalogue, avant toute lecture :
  - CIK confirmés par `company_tickers.json` : 1823945 (Blue Owl Capital Inc., anciennement Altimar Acquisition Corp.), 1858681 (Apollo Global Management, Inc., anciennement Tango Holdings, Inc.) et 1393818 (Blackstone Inc.). Exercices clos le 31 décembre ;
  - successions et ruptures (point 4), chaque extrait consigné dans `config.yaml` :
    - Blue Owl : regroupement réalisé le 19 mai 2021 (8-K 0001193125-21-169371, items 2.01 et 3.03 : « On May 19, 2021 (the “Closing Date”), Altimar Acquisition Corporation [...] changed its names to Blue Owl Capital Inc. »). L'acquéreur comptable est Owl Rock (10-Q 0001823945-21-000007 : « for both the ALT merger and the Dyal Acquisition, Owl Rock was deemed to be the acquirer for accounting purposes »). La règle `reverse_combinations` s'applique : 83 dépôts de la SPAC dans la période de lecture, dont 4 rapports périodiques (10-Q du troisième trimestre 2020, 10-K 2020 et son amendement, 10-Q du premier trimestre 2021), sont hors du groupe, avec 188 faits de companyfacts ; le groupe porte `history_left_censored` ; ses trimestres commencent le 1er avril 2021 (`reporting_start`) ;
    - Apollo : le 8-K12B 0001193125-22-000274 du 3 janvier 2022 « establishes AGM as the successor issuer to AAM and AHL pursuant to Rule 12g-3(c) ». Le 10-Q du premier trimestre 2022 (0001858681-22-000029) dit : « Apollo was deemed to be the accounting acquirer and Athene the accounting acquiree, which, for financial reporting purposes, results in Apollo’s historical financial information prior to the Mergers becoming that of the Company ». AAM (CIK 1411494) entre donc dans `predecessors`, tête du groupe jusqu'au 1er janvier 2022 (`successions`). Athene n'est pas un prédécesseur malgré le 8-K12B : ses états ne continuent pas ceux du groupe, et elle n'y entre que comme filiale (point 5). AAM a continué de déposer comme filiale : ses 10-Q des trois premiers trimestres 2022, son 10-K 2022 et ses 10-Q des deux premiers trimestres 2023 sont des rapports de filiale, hors du groupe (`post_succession`, 6 rapports, 2 345 faits de companyfacts). Son 10-K 2021, déposé le 25 février 2022 pour un exercice clos avant la succession, est le rapport du groupe pour 2021. AGM n'a déposé aucun rapport périodique avant celui du premier trimestre 2022 ;
    - Blackstone : même CIK depuis 2007 ; `formerNames` donne The Blackstone Group L.P. jusqu'au 28 juin 2019, puis Blackstone Group Inc, puis Blackstone Inc. Aucun 8-K12, aucune rupture ;
  - les inventaires des groupes présents sont inchangés (vérifiés par groupe et par classe : Akamai, Backblaze et Riot redonnent les chiffres de D-0054) ;
  - inventaire : Blue Owl 21 rapports périodiques (16 10-Q, 5 10-K), 55 8-K de la tranche, 5 circulaires ; Apollo 35 rapports périodiques (17 d'AAM de 2018 à 2021, 18 d'AGM depuis 2022), 58 8-K de la tranche, 1 8-K à item de signal, 7 circulaires ; Blackstone 34 rapports périodiques (26 10-Q, 8 10-K), 38 8-K de la tranche, aucune circulaire ;
  - univers attendu : 2 148 cellules pour les trois groupes (716 chacun ; 28 sans objet pour Blue Owl) ;
  - index : 2 036 dépôts (257 nouveaux), aucun échec. Archives XBRL : 698 dépôts lus (90 nouveaux) ; les 7 échecs sont ceux déjà connus. Pièces : 2 145 documents (259 nouveaux), aucun échec. Requêtes du jour : 1 126, toutes en 200, 801,6 Mo, vers les seuls hôtes de la SEC (phase 0 6, pièces des successions 4, index 514, archives 344, pièces 258) ;
  - amendement, avant toute lecture : l'Item 404 de Blackstone. Blackstone ne dépose aucune circulaire dans la période, ni DEF 14A ni DEF 14C. Ses transactions avec des proches figurent dans la partie III de ses 10-K, à l'Item 13 (« Certain Relationships and Related Transactions, and Director Independence »), que la règle de l'Item 404 ne voyait pas, puisqu'elle ne lit que les circulaires. Règle : pour un groupe qui ne dépose aucune circulaire dans la période, l'Item 404 se lit dans l'Item 13 de chacun de ses 10-K, de son titre au titre d'item suivant, s'il y est rédigé (un renvoi de quelques lignes à une circulaire ne compte pas). Seul Blackstone est dans ce cas (Nebius dépose des 20-F, dont l'Item 7.B est déjà lu) : 8 blocs, de 23 700 à 34 600 caractères. Code : `sections.item_13_10k`, `catalog.build`, un test unitaire ;
  - catalogue : aucune clé de bloc déjà lue ne change. Le catalogue principal passe de 3 431 à 3 988 blocs, celui du bloc `text` de 3 528 à 4 045 ;
  - à lire, dans l'ordre de la file (les corps de pièces n'entrent qu'après lecture de leur en-tête) : Blue Owl 281 blocs, 1,17 M de caractères, plus 41 corps de pièces pour 4,71 M ; Apollo 361 blocs, 3,43 M, plus 23 corps pour 4,22 M ; Blackstone 310 blocs, 1,64 M, plus 22 corps pour 3,39 M. Listes `grp_owl`, `grp_apo` et `grp_bx` ;
  - découverte d'origine (point 8) : deux blocs déjà lus pour Apollo (la note d'engagements du 10-Q du deuxième trimestre 2026 et l'en-tête d'un contrat de travail d'Athene déposé par AGM, abstention), qui vont au groupe ; une unité d'AAM encore en file (rang 1 549) en sort au réassemblage. Les cinq unités d'Athene (rang 138) restent dans la file, non traitées : Athene n'est pas un des trois déposants.

  (13) Lecture, sans sous-agent (2026-10-17), un commit par groupe (d1d99a0, 5bd06d0, cbce006) :
  - Blue Owl : 309 blocs lus sur 322 de la liste `grp_owl` ; les 13 autres sont des corps d'EX-4 (actes d'émission entre l'émetteur du groupe et le fiduciaire), que §14 ne rouvre pas. 439 observations et 118 abstentions. Lignes principales :
    - financement : obligations de Blue Owl Finance LLC (séries 2028, 2031, 2032, 2034, 2036 et 2051 : émissions, garants du groupe, fiduciaire Wilmington Trust, National Association, encours trimestriels) ; crédits renouvelables d'avril 2021 et de 2022 (agent MUFG Bank, Ltd., avenants jusqu'en 2025) ; billets à ordre envers des produits gérés (15, 50 et 250 M$) ; prêteurs d'Owl Rock antérieurs au regroupement, nommés par les statuts : East West Bank (contrats de prêt et de sûreté des conseillers) et Diamond Finance Investors (US Unlevered) LP (contrat de crédit et de garantie du 25 octobre 2019) ;
    - acquisitions : Oak Street (décembre 2021, 1,0 Md$ à la clôture), IPI Partners (janvier 2025), Atalaya ; compléments de prix et prix d'achat différé de 2024 ; rachat de 2021 des parts de commissions des investisseurs des fonds Dyal ; services de transition de Neuberger Berman ;
    - engagements envers les produits gérés (engagements non tirés, soutien des frais) ; baux non commencés ; conventions de conseil des BDC (OBDC, OTF) et actions de l'article 36(b) de 2026, sans montant ;
  - Apollo : 370 blocs lus sur 384 de la liste `grp_apo` ; les 14 autres sont des corps d'EX-4, que §14 ne rouvre pas. 2 146 observations et 76 abstentions. Lignes principales :
    - parties liées d'AGM et d'AAM : Athene avant et après la fusion (commissions, apports, contrats de financement, ADIP), Athora, Atlas, Venerable et VA Capital, Catalina, Wheels, PK AirFinance, placements d'Athene dans des véhicules affiliés (AMAPS, AP Grange, AP Tundra, Fox Hedge...) ;
    - financement : obligations d'AGM, d'AMH et d'AHL (tableaux et émissions), crédits renouvelables (Citibank, N.A. ; Wells Fargo Bank, National Association ; Sumitomo Mitsui Banking Corporation pour ACMP ; JPMorgan Chase Bank, N.A. pour les crédits de 2013) ; contrats de financement d'Athene (FHLB, FABN, FABR) ;
    - engagements envers les fonds gérés, compléments de prix (Stone Tower, Griffin Capital), garanties, pénalité civile versée à la SEC en janvier 2025 ; réalisation des fusions le 1er janvier 2022 (item 2.01 : Athene Holding Ltd. filiale directe d'AGM) ;
  - corrections pendant la lecture d'Apollo (D-0020) : renvois de notes « 1,2 » qui masquaient les lignes d'AGM du tableau de dette (10-K 2025 refait) ; émissions de même clé de phrase ; engagements envers Athora et lignes d'ACRA 1 et d'ADIP sur dix notes de parties liées ; doublons FHLB et FABN du 10-Q du premier trimestre 2024 ; citation de l'action dérivée de 2023 ramenée à un fragment sans noms sur onze notes d'engagements ;
  - Blackstone : 315 blocs lus sur 332 de la liste `grp_bx` ; les 17 autres sont des corps d'EX-4 (émetteurs du groupe et fiduciaires), que §14 ne rouvre pas ; les cinq corps du contrat de crédit refondu (2018, 2020, 2022, 2023, 2025) sont lus. 1 446 observations et 102 abstentions. Lignes principales :
    - financement : obligations de Blackstone Holdings Finance Co. L.L.C. et de Blackstone Reg Finance Co. L.L.C. (tableaux, émissions, fiduciaire et agent payeur, offre de rachat et remboursement de 2019), crédit renouvelable (agent Citibank, N.A. ; engagements de l'annexe 2.01 de 2018, prêteurs des pages de signature, plafonds de lettres de crédit), facilités des fonds, CLO et emprunts garantis ;
    - engagements : envers les fonds, garanties des fonds immobiliers et des prêts aux salariés, restitutions de commissions de performance ; sûretés données aux Regents of the University of California (UC Investments) pour les coentreprises stratégiques de décembre 2022 et janvier 2023 ; règlements avec KRS ; pénalité civile de la SEC (janvier 2025) ;
    - placements : 9,9 % de SAFG Retirement Services, Inc. achetés en 2021 pour 2,2 Md$, puis actions de Corebridge Financial, Inc. ; Pátria (mise en équivalence, ventes de 2021) ; Item 13 des 10-K : relation de Tsinghua University Education Foundation (commission de gestion levée) ;
  - données personnelles (point 10) : aucune personne physique n'est contrepartie ; aucune citation ni note ne reprend un nom de personne physique ; Blackstone Group Management L.L.C. et Blackstone Partners L.L.C. ne sont ni membres ni contreparties. Contrôle de cohérence de Blackstone : les lignes soumises redonnent celles des extracteurs sur les 315 blocs.

  (14) Intégration (2026-10-17), vingt-sept groupes et trois non-déposants, vue `as_known` :
  - inventaire de D-0050 (point 3), après la lecture : noms à forme juridique des lignes valides, présents dans un bloc lu du groupe et non confirmés : Blue Owl 78 (30 avec une phrase à terme de filiale), Apollo 116 (47), Blackstone 61 (13) ; chaque phrase relue par l'exécutant ;
  - rattachements par extrait (point 5 ; D-0050, points 4 à 7), 48, chacun vérifié mot pour mot dans un bloc lu et sans nom de personne physique, dans `config.yaml` :
    - Blue Owl (10) : Blue Owl Finance LLC (« an indirect subsidiary of Blue Owl Capital Inc. ») ; six des onze garantes des obligations 2036 nommées dans des lignes (Blue Owl Capital GP LLC, Blue Owl Capital Holdings LP, Blue Owl Capital Carry LP, Blue Owl Real Estate Holdings LP, Blue Owl Real Estate GP Holdings LLC, Blue Owl Capital Holdings LLC : « each a direct or indirect subsidiary of the Company », 8-K du 18 août 2026), sans date ; Dyal Capital Holdings LLC au 19 mai 2021 (activité de Dyal acquise au regroupement) ; Blue Owl Credit Advisors LLC et Blue Owl Technology Credit Advisors LLC (« an indirect subsidiary of the Company ») ;
    - Apollo (31) : Athene Holding Ltd. et Apollo Asset Management, Inc. au 1er janvier 2022 (« As a result of the Mergers, AAM and AHL became direct subsidiaries of AGM. », item 2.01) ; à la même date, les filiales d'Athene nommées comme telles : Athene Annuity and Life Company, Athene Life Re Ltd., PK Air Holdings, LP (entité à intérêts variables consolidée par Athene), AP Violet ATH Holdings, L.P ; sans date : Apollo Management Holdings, L.P., Apollo Management International LLP, APH Finance 1, LLC, Apollo Investment Management, L.P., Apollo Investment Consulting LLC, Apollo Insurance Solutions Group LP, Athene Asset Management, ACMP Holdings LLC et APO Corp. (filiales d'AAM), Apollo Capital Markets Partnership (« a consolidated VIE »), les douze Apollo Principal Holdings et AMH Holdings (Cayman), L.P. (« its indirect subsidiaries », 8-K du 12 mars 2018), Blue Merger Sub, Ltd. et Green Merger Sub, Inc. (filiales de HoldCo, constituées pour les fusions). Le message du commit a88afbc compte 30 rattachements pour Apollo : ils sont 31 ;
    - Blackstone (7) : Blackstone Holdings Finance Co. L.L.C., les cinq Blackstone Holdings L.P. (« each indirect subsidiaries of the Corporation ») et Blackstone Reg Finance Co. L.L.C. ;
    - treize alias (D-0021) : Owl Rock Capital Holdings LLC vers Blue Owl Capital Holdings LLC (« f/k/a ») ; Athene et AHL vers Athene Holding Ltd. ; ALRe vers Athene Life Re Ltd. ; FHLB ; les graphies longues d'AMAPS 1 et 2 ; VIAC (Venerable Insurance and Annuity Company) ; Venerable (Venerable Holdings, Inc.) ; Atlas (Atlas Securitized Products Holdings L.P.) ; Wheels (Wheels Inc.) ; Catalina (Catalina Holdings (Bermuda) Ltd.) ; PK Air (PK AirFinance). Cinq entités propres par extrait : East West Bank, Federal Home Loan Bank of Des Moines, Regents of the University of California, PK AirFinance, Athene Global Funding (« a special purpose, unaffiliated statutory trust »). « VA Capital Company, LLC » et « VA Capital Company LLC » ont la même forme normalisée : aucun alias ;
  - restent des contreparties propres, faute d'extrait qui les dise filiales : les commandités des Blackstone Holdings (« its general partner », pages de signature) ; Blackstone ISG-I Advisors L.L.C. et Argon Holdco LLC (« an entity affiliated with Blackstone ») ; SAFG Retirement Services, Inc. et Corebridge Financial, Inc. (aucun bloc lu ne dit le changement de dénomination) ; Opal Capital Holdings LLC (emprunteuse du contrat du 25 octobre 2019 dans les statuts de mai 2021, sans extrait d'identité avec Owl Rock Capital Holdings LLC) ; Catalina, Skylign, AP Grange Holdings, LLC (coentreprise d'Intel) et les véhicules d'Athene (placements, non consolidés) ; Oak Street, IPI Partners, Kuvare et Atalaya (acquises, sans terme de filiale) ; Athene USA Corporation (co-emprunteuse, sans ligne d'arête) ; SVF II Finco Cayman L.P. (aucun extrait ne la rattache à SoftBank). Augustus, LLC, détenue par une personne physique, n'est pas rattachée (point 10). Restent en attente : « AAA » (deux entités selon le document : AP Alternative Assets, L.P. jusqu'en 2019, Apollo Aligned Alternatives, L.P. ensuite), « Athene Holding » (écrit sans définition), « Pátria » (les deux sociétés ensemble), Athora, ADIP, AINV, MidCap Financial, Fund VIII et Fund IX, KRS, Neuberger, les fonds gérés (point 5) ;
  - corrections dans la passe (D-0020) : les trois lignes de Meta du bloc 4495846547b3 prennent la désignation du bloc, « an affiliate of funds managed by Blue Owl Capital, Inc. » (point 5) ; aucune autre ligne d'un groupe suivi ne nommait la tête de l'un des trois groupes. Neuf noms des tableaux de concentration d'Athene (trois blocs) perdent le renvoi de note collé (« AP Grange Holdings, LLC1 », « Fox Hedge L.P.1 »...), et « Investment-grade debt issued by Blackstone Private Credit Fund3 » devient l'émetteur, « Blackstone Private Credit Fund » ;
  - corrections du code, chacune avec son test :
    - prédécesseurs : AAM, tête du groupe jusqu'au 1er janvier 2022 par `successions`, puis filiale par extrait, ne reçoit plus de groupe propre avant son rattachement (`entities.build`) ; `Registry.treatment_at` lit l'appartenance valide à la date ;
    - formes juridiques : « Ltda » (Pátria Investimentos Ltda) et « National Association », forme développée de « N.A. ». Douze dénominations en « National Association » deviennent des entités propres (D-0022), dont Wells Fargo Bank, National Association, Bremer Bank, National Association, U.S. Bank National Association et Wilmington Trust, National Association ; 157 arêtes les touchent, dont 96 dans des groupes déjà suivis (CORZ 42, dont 27 à montant, prêts de Bremer Bank ; AMD 25, dont 9 ; DELL 14 ; SMCI 7 ; CRWV 4 ; MRVL 2 ; CIFR 1 ; APLD 1). Ce sont des prêteurs des groupes : aucune paire n'en naît. Limite non corrigée : « N.A. » et « National Association » donnent deux normalisations distinctes (Wells Fargo Bank, N.A. et Wells Fargo Bank, National Association, deux entités), comme « L.L.C. » et « LLC » (D-0054) ;
    - dépôts d'un déposant rattaché par extrait (point 8) : `load.line_group` envoie à APO les lignes des blocs déposés par Athene Holding Ltd. après le 1er janvier 2022 (champ `cik` de son rattachement) ; une ligne, une abstention du montage `athene_whco` ;
    - bloc `lender`, émetteur d'une position (`lender.issuer_unambiguous`) : une forme juridique dans les quatre mots qui suivent la dénomination trouvée l'emporte sur un mot d'instrument. « Blue Owl Capital Corporation Senior Loan Fund LLC », coentreprise d'OBDC, n'est plus rattachée à OBDC (6 identifiants, 21 faits) ; aucun autre rattachement ne change ;
    - rendu : noms des trois groupes ; plateformes de présentation Apollo et Blackstone (point 7) dans les blocs `lender_portfolio` et `lender_liabilities`, l'annexe F et les séries par véhicule. La marque se lit aussi dans l'ancienne dénomination EDGAR (champ `former` de sub.tsv) : MidCap Financial Investment Corp (anciennement Apollo Investment Corp) entre dans la plateforme Apollo. Plateformes : Blue Owl 7 véhicules, Apollo 5, Blackstone 3 ;
  - premier réassemblage : observations 18 136 → 22 463, entités 2 185 → 2 550, liens 6 976 → 8 756. Les 4 333 lignes des trois groupes sont valides (dont les 6 des deux blocs de la découverte d'origine, point 8). Aucune arête ne relie les trois groupes aux groupes déjà suivis : les fonds gérés restent hors des gestionnaires (point 5), les lignes de Meta sont en attente, et « Apollo » du 10-Q de Broadcom reste une description ;
  - arêtes au dernier réassemblage : Blue Owl 31 (4 à montant ; East West Bank 8, MUFG Bank, Ltd. 7, Diamond Finance Investors (US Unlevered) LP 2 ; les obligations de Blue Owl Finance LLC n'ont pas de porteur nommé) ; Apollo 720 (387 à montant ; Citibank, N.A. 76, Wells Fargo Bank, National Association 50, Atlas 38, Athene Holding Ltd. 34, avant la fusion, Catalina 30, VA Capital Company LLC 24, Venerable Holdings, Inc. 21, VIAC 20, Sumitomo Mitsui Banking Corporation 19, Wheels Inc. 18, Athene Global Funding 17, Federal Home Loan Bank of Des Moines 17 ; 266 vers des noms en attente, dont Athora 76, ADIP 36, « Athene Holding » 26, AINV 25) ; Blackstone 233 (36 à montant ; Regents of the University of California 33, Citibank, N.A. 32, les deux sociétés Pátria 34, Corebridge Financial, Inc. 6, prêteurs du crédit renouvelable ; 70 vers des noms en attente, surtout des banques sans forme juridique ou des succursales, « … New York Branch ») ;
  - BDC Data Sets : extraction refaite après le premier réassemblage (D-0043, point 14), puis après les derniers alias, qui font entrer des dénominations au registre : 3 032 517 lignes de positions (2 906 656 avant), 2 100 dépôts. Faits de BDC rattachés : 2 154 (2 134), dans 258 dépôts de 47 fonds (256, 46). Nouveaux émetteurs : Blackstone, par deux prêts à terme de premier rang d'AB Private Lending Fund dont l'identifiant porte « BLACKSTONE INC » et le secteur « Electrical Equipment » (992 500 $ de principal, juste valeur ÷ coût de 1,0001 au 31 mars 2026), rattachés par la règle de la dénomination entière : l'émetteur réel est probablement une société du portefeuille, à vérifier dans le dépôt ; U.S. Bank National Association (dépôts monétaires de deux BDC) ; Blue Owl Capital Corporation et Blue Owl Technology Finance Corp., entités propres hors du groupe ; aucun émetteur d'Apollo. Second et troisième réassemblages : faits 1 379 840 → 1 379 849 → 1 379 828, entités 2 562 puis 2 570, mesures 140 753 puis 141 451 ;
  - rendus : documents 20 646, faits 1 379 828, observations 22 463, entités 2 570, liens 8 756, mesures 141 451, exclusions 23 131 ; 9 818 nombres publiés (8 432). Annexe F : 359 événements des groupes (344) : Blue Owl 2 (F4 aux 30 septembre 2024 et 2025), Apollo 7 (F2 deux fois en 2021 ; F8 cinq fois, du 31 décembre 2021 au 31 mars 2026), Blackstone 6 (F2 au 31 décembre 2021 ; F8 cinq fois, du 31 mars 2022 au 30 septembre 2025). Paires : 160 (129) ; 31 nouvelles (Apollo 24, surtout les placements d'Athene dans des véhicules affiliés ; Blackstone 4 ; Blue Owl 3), aucune paire existante modifiée ; conclusions : causalité non établie 122 (92), achats réciproques seulement 16 (16), relation commerciale doublée d'un financement 14 (13 ; nouvelle : Apollo → Athene Holding Ltd., avant la fusion), dépendance documentée 8 (8). Paires à financement documenté : 57 (29). Cycles (E.6) : 53 (52) ; Meta ↔ Blue Owl Capital, Inc. en sort, comme prévu au point 5 ; Apollo ↔ Athene Holding Ltd. (avant la fusion) et Apollo ↔ Bank of America, N.A. y entrent. E.7 : discrimination possible, 58 % d'issues indéterminées sur 112 (57 % sur 56 avant l'ajout) ; E.1 non étayé 47 (24) ;
  - tests unitaires : 126, tous passés.
- **D-0056 — Ajout de groupes : Intel (INTC), Micron (MU) et TSMC (TSM), fabricants. Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-18 : « Ajoute Intel, Micron et TSMC ». Elle suit le rapport d'intégration de Blue Owl, Apollo et Blackstone (D-0055, commit 06528ef). §14 met les fabricants après les hébergeurs endettés. Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Statut lu avant tout tirage, dans `company_tickers.json` du 2026-10-07 déjà en cache (aucune requête) : INTC résout le CIK 50863 (INTEL CORP), MU le 723125 (MICRON TECHNOLOGY INC), TSM le 1046179 (TAIWAN SEMICONDUCTOR MANUFACTURING CO LTD, aussi coté sous TSMWF). Les trois sociétés entrent comme groupes complets (`groups`, `group_entry` au 2026-10-18). L'exécution garde l'as_of du 2026-10-07 (D-0048, point 2) : ce qui est tiré maintenant se range sous cet as_of, les dépôts postérieurs sont écartés, le journal garde l'heure réelle des requêtes.

  (3) Mêmes phases et mêmes règles de lecture que les groupes présents (D-0043, D-0048, D-0052 à D-0055) : inventaire, archives XBRL, catalogue des notes, des items et des pièces, lecture complète du texte. Les clôtures se lisent en phase 0 sur `period_end` (exercices de 52 ou 53 semaines d'Intel et de Micron compris).

  (4) Successions et ruptures d'historique, vérifiées en phase 0 sur la liste des dépôts (8-K12, `formerNames`, items 2.01 et 3.03) et par un extrait cité. Aucune n'est attendue : les trois CIK portent le même déclarant sur toute la période. Ne sont pas des ruptures, mais des changements de périmètre (§10.2), traités comme toute acquisition ou cession : chez Intel, la cession de l'activité de mémoire NAND à SK hynix (deux réalisations, fin 2021 et 2025), l'introduction en Bourse de Mobileye (2022), la cession de 51 % d'Altera (2025), les participations minoritaires vendues dans ses usines (Brookfield en Arizona, Apollo en Irlande) ; chez Micron et TSMC, leurs acquisitions et cessions. Si la phase 0 montre autre chose, la règle est revue et consignée ici avant toute lecture.

  (5) TSMC, émetteur privé étranger en IFRS :
  - un 20-F par an et des 6-K, aucun rapport trimestriel (règle 13a-13 non applicable) : mêmes règles que Nebius (D-0048, points 5 et 6). Le 20-F entre dans les rapports périodiques ; un exercice qui n'a qu'un rapport annuel se découpe en quatre trimestres de trois mois ; `reporting_start` met les trimestres de TSMC à `not_applicable`, avec la règle 13a-13 pour pièce ; les signaux du 20-F se lisent au trimestre de clôture ;
  - cadre comptable : les états du 20-F sont établis selon les IFRS publiées par l'IASB, sur toute la période. Aucune rupture d'historique (le cadre ne change pas, contrairement à IREN, D-0048, point 4). Invariant (f) : les faits, les notes et les cellules de TSMC portent le cadre `ifrs`, et aucun agrégat ne les somme avec du US GAAP (exclusion `invalid_aggregate`, motif `mixed_framework`, D-0042). Le cadre d'un groupe s'écrit dans `config.yaml` (`group_frameworks`) : les notes d'un groupe en IFRS ne portent plus le cadre US GAAP que `foreign.block_framework` donnait à toutes les notes des groupes ;
  - correspondance des concepts (§8.3) : la liste des candidats d'une grandeur est fixée d'avance d'après les définitions us-gaap ; pour un groupe en IFRS, elle l'est d'après les définitions ifrs-full, ici, avant de voir les faits (`concept_anchors_ifrs` de `config.yaml`, noms locaux vérifiés en phase 0 dans `full_ifrs-cor_2025-03-27.xsd`, paquet épinglé de l'annexe D ; un nom absent du paquet sort de la liste, consigné ici). Un candidat ifrs-full ne peut jamais être retenu pour un déposant en US GAAP : la règle exige qu'il figure dans la linkbase de présentation du déposant. Les grandeurs sans équivalent en IFRS restent sans candidat, et leurs cellules de TSMC « concept non résolu » : capitaux propres temporaires, trésorerie soumise à restrictions, ventilation des baux entre location simple et location-financement (IFRS 16 n'a qu'un modèle de preneur), acquisitions d'immobilisations non payées, financées par le fournisseur ou payées en actions, intérêts capitalisés en principal (PIK), échéanciers des obligations d'achat et des dettes, gains de dilution, gains et dépréciations des titres de participation ;
  - contrôles (§8.3) : les contrôles d'additivité des totaux du bilan et des flux (C1 et C2) reçoivent les totaux ifrs-full correspondants ; les autres contrôles, écrits sur des concepts us-gaap (trésorerie, articulation, baux, résultat par action, impôt), restent `not_testable` pour TSMC, avec leur motif ;
  - textes lus : notes du 20-F par rôles XBRL, comme les 10-K ; Item 15 (Controls and Procedures) en bloc `item_9a`, Item 7.B (Related Party Transactions) en bloc `item_404`, Item 10.C (Material Contracts) en bloc `item_8k_101` ; délimitation de D-0048, point 9. Les états d'un 20-F sont audités (niveau A) ;
  - 6-K : unités de D-0048 (points 6 et 9), même lexique de termes ; les noms de groupes et de laboratoires qualifiants sont ceux du lexique de la découverte et tous ceux des groupes de `config.yaml` à cette date, jamais TSMC lui-même (« TSMC », « Taiwan Semiconductor »). Cette liste s'écrit pour TSMC seul (`foreign_6k.group_names_by_group`) : les unités de Nebius et d'IREN ne changent pas (D-0055, point 9). Plafond de 80 unités, du 6-K le plus récent au plus ancien ; au-delà, `not_processed`. Un 6-K est furnished (niveau E), sauf incorporation par référence lue dans le 6-K (niveau C, D-0042) ;
  - monnaie : TSMC publie en nouveaux dollars de Taïwan (TWD). Aucun agrégat ne mêle les monnaies (invariant b) ; les ratios d'un même groupe ne sont pas touchés.

  (6) Filiales et entités : règle de D-0050 (points 3 à 7), appliquée à l'intégration, après la lecture, aux dénominations nommées dans les lignes, y compris celles des autres groupes et les positions des BDC. Une coentreprise consolidée (les usines d'Intel en Arizona et en Irlande, les filiales de TSMC au Japon et en Allemagne) entre au groupe par un extrait qui la dit consolidée ; le véhicule de l'associé minoritaire (Brookfield, Apollo, partenaires japonais et allemands) reste une entité propre, et, s'il est un véhicule de fonds gérés, il ne va pas au groupe du gestionnaire (D-0055, point 5). Une filiale cédée ou déconsolidée sort à la date citée (Altera). Mobileye Global Inc. dépose ses propres rapports : ce sont des rapports d'une filiale, hors des séries et du texte du groupe (`out_of_scope`, comptés), et l'entité entre au groupe par un extrait d'Intel.

  (7) Lignes déjà lues qui nomment ces sociétés, relevées avant tout tirage : deux lignes de NVIDIA nomment « Intel Corporation » (investissement de 2025, avec montant), deux de Broadcom nomment « Taiwan Semiconductor Manufacturing Company » (fonderie, sans montant) ; les lignes d'Apollo nomment « AP Grange Holdings, LLC », véhicule de l'associé de l'usine irlandaise d'Intel (D-0055) ; neuf lignes de la découverte d'origine viennent des dépôts d'Intel (rang 22 : six observations, trois abstentions). Elles vont aux groupes par les règles ordinaires : la dénomination légale entière se résout en la tête (même CIK) ou en une entité par extrait ; un nom court (« Intel », « Micron », « TSMC ») ne devient un alias qu'avec un extrait qui le définit (D-0021). Aucune correction n'est faite d'avance.

  (8) Découverte d'origine (D-0043, point 6) : les lignes déjà lues pour Intel vont à son groupe ; ses unités encore en file (rang 22, passe B) en sortent (`out_of_scope`) ; côté client, la recherche reste incomplète pour un fournisseur que le lexique de la découverte ne nommait pas. Micron et TSMC n'y ont aucun candidat. Le lexique, le classement, la file et l'état de lecture de la découverte ne changent pas (D-0036).

  (9) Montages : `meta_hyperion` et `athene_whco` ne changent pas (requêtes, termes, blocs, clés de contenu). Un bloc du catalogue d'un groupe qui a la clé de contenu d'un bloc de montage ou de la découverte déjà lu ne se relit pas. BDC : les positions sur les entités des trois groupes viennent de l'extraction refaite après le premier réassemblage (D-0043, point 14) ; les plateformes de présentation ne changent pas (aucune BDC ne porte la marque d'un fabricant).

  (10) Les lexiques déjà fixés (unités 6-K de Nebius et d'IREN, termes des montages, lexique de la découverte, piste des non-déposants) ne changent pas.

  (11) Données personnelles (D-0051 ; D-0055, point 10) : aucune personne physique n'est contrepartie, et les noms des contrats de travail, des lettres d'offre, des blocs de signature et des circulaires (rémunérations, transactions avec des proches) ne sont pas repris.

  (12) Limites connues avant calcul : TSMC n'a pas de série trimestrielle (cellules « annuel seulement ») ; ses contrôles autres que C1 et C2 restent non testables ; ses grandeurs sans équivalent IFRS restent non résolues ; ses montants en TWD ne se comparent aux autres groupes que par des ratios.

  (13) Ordre et commits :
  - la décision ;
  - la configuration et le code (cadre des groupes, candidats ifrs-full, totaux IFRS de C1 et C2, noms des 6-K de TSMC), avec leurs tests, la phase 0 et l'univers attendu ;
  - l'index, les archives XBRL, le paquet IFRS et les pièces (phases 0, 1 et 2, réseau en série) ;
  - le catalogue et les listes de lecture, avec leur volume consigné ici avant toute lecture ;
  - la lecture d'Intel, puis celle de Micron, puis celle de TSMC, un commit par groupe ;
  - l'intégration : entités et filiales par extrait, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (14) Phases 0 à 2 et catalogue, avant toute lecture (2026-10-18) :
  - CIK confirmés par `company_tickers.json` : 50863 (Intel Corporation), 723125 (Micron Technology, Inc.) et 1046179 (Taiwan Semiconductor Manufacturing Company Limited). `formerNames` est vide pour les trois. Exercices : Intel, de 52 ou 53 semaines, clos le dernier samedi de décembre (27 décembre 2025) ; Micron, de 52 ou 53 semaines, clos le jeudi le plus proche du 31 août (28 août 2025) ; TSMC, le 31 décembre ;
  - successions et ruptures (point 4) : aucun 8-K12B ni 8-K12G3 (les 8-A12B de Micron enregistrent des titres). Les trois items 2.01 de la période sont chez Intel : la réalisation de la coentreprise Arizona Fab LLC avec Brookfield (8-K du 22 novembre 2022), la seconde réalisation de la cession de l'activité NAND à SK hynix (8-K du 28 mars 2025) et la cession de la majorité d'Altera à un affilié de Silver Lake (8-K du 15 septembre 2025). Ce sont des changements de périmètre, lus au bloc `text`. Le seul item 3.03 de la période (Micron, 19 juillet 2019) est l'expiration de son plan de droits (« The Section 382 Rights Agreement [...] expired by their respective terms on the close of business on July 19, 2019 »). Aucune rupture : la règle du point 4 tient ;
  - les inventaires et l'univers attendu des groupes présents sont inchangés (vérifiés par groupe, dépôt et classe) ;
  - inventaire : Intel 34 rapports périodiques (26 10-Q, 8 10-K), 30 8-K de la tranche, 9 circulaires ; Micron 35 rapports périodiques (27 10-Q, 8 10-K), 47 8-K de la tranche, 9 circulaires ; TSMC 8 20-F (exercices 2018 à 2025 ; le 20-F de 2017 est hors de la période), 463 6-K (dont 3 6-K/A), aucune circulaire ;
  - univers attendu : 2 120 cellules pour les trois groupes (Intel 716, Micron 744, TSMC 660, dont 560 cellules trimestrielles sans objet, comme Nebius) ;
  - index : 2 208 dépôts (172 nouveaux), aucun échec. Archives XBRL : 775 dépôts lus (77 nouveaux) ; les 7 échecs sont ceux déjà connus (amendements de GOOGL, WULF et RIOT sans instance). Pièces : 2 320 documents (175 nouveaux), aucun échec. 6-K de TSMC : 463 en-têtes et 555 documents (document principal et annexes 99). Paquet épinglé de l'annexe D : `full_ifrs-cor_2025-03-27.xsd`, 1 requête vers xbrl.ifrs.org, sans User-Agent. Requêtes du jour : 1 827, toutes en 200, 861,7 Mo (phase 0 7, index 344, companyfacts 3, archives 278, pièces 172, paquet IFRS 1, 6-K 1 018, documents principaux des items 2.01 et 2.03 4), toutes vers les hôtes de la SEC sauf celle du paquet IFRS ;
  - candidats ifrs-full (point 5), vérifiés dans le paquet avant toute correspondance : 53 grandeurs. Deux noms ne s'y trouvaient pas. `ProfitLossAttributableToOrdinaryEquityHoldersOfParentEntityIncludingDilutiveEffect` était mal écrit : il cède la place au nom du paquet (`...DilutiveEffects`), même élément. `NoncurrentPortionOfNoncurrentBorrowings` est absent et sort de la liste ; la dette non courante garde `LongtermBorrowings` ;
  - amendements, avant toute lecture :
    - Item 9A et Item 4 d'Intel : Intel ne numérote ses items que dans l'index de correspondance qui clôt chaque rapport (« Form 10-K Cross-Reference Index », « Form 10-Q Cross-Reference Index ») ; sa section des contrôles porte le seul titre « Controls and Procedures ». Les délimiteurs de l'Item 9A et de l'Item 4 ne trouvaient rien dans ses 34 rapports. Règle : dans un 10-K ou un 10-Q qui a un tel index, l'Item 9A ou l'Item 4 est la section titrée « Controls and Procedures », jusqu'au premier titre qui n'est pas une de ses sous-sections ; les pieds de page et les renvois au sommaire la coupent sans la fermer. Seul Intel est dans ce cas : les autres rapports où ni l'Item 9A ni l'Item 4 ne se trouvent sont des amendements sans index. 34 blocs, de 2 200 à 4 250 caractères. Code : `sections.controls_xref`, `catalog.build`, deux tests unitaires ;
    - notes de TSMC (point 5, « comme les 10-K ») : les titres de ses notes de dette (« Bonds Payable », « Long-term Bank Loans », « Short-term Loans ») échappaient au motif des notes de dette ; ses 20-F de 2018 à 2024 balisent ces notes en blocs de texte dimensionnés (un membre par note sur l'axe `BorrowingsByNameAxis`), que le catalogue ne prenait pas ; les notes de leviers et de revenu, comme le texte autour des faits de concentration, se choisissaient par concept us-gaap. Règle : le motif des notes de dette reçoit ces titres ; un concept de note qui n'a de bloc de texte que dimensionné donne un bloc par membre ; les notes de leviers et de revenu reçoivent leurs équivalents ifrs-full (immobilisations corporelles, jugements et estimations, méthode comptable des immobilisations, changements d'estimation ; revenu des contrats avec les clients), avec leurs faits candidats ; le texte de concentration reçoit `ifrs-full:PercentageOfEntitysRevenue` (part des clients importants, IFRS 8.34), dont le rôle de détail porte un sous-titre (« Operating Segments Information - Major Customers [...] (Detail) ») : sa note parente est le titre avant le tiret. Noms vérifiés dans le paquet. Aucun rôle, bloc ou concept d'un autre groupe ne répond aux ajouts. Les rôles « (Detail) » de TSMC restent classés en notes, comme ceux des autres groupes : ses notes de dette des 20-F de 2018 à 2024 n'ont pas de faits candidats, et leurs montants seront narratifs. Blocs ajoutés : 17 notes de dette, 24 notes de leviers, 8 notes de revenu, 8 textes de concentration (clients A, B et C, sans nom). Code : `text_catalog`, quatre tests unitaires ;
  - catalogue : aucune clé de bloc déjà lue ne change, et les blocs des groupes présents sont identiques (catalogue principal, bloc `text`, unités 6-K). Le catalogue principal passe de 3 988 à 4 333 blocs, celui du bloc `text` de 4 045 à 4 574, celui des unités 6-K de 160 à 240 ;
  - 6-K de TSMC (point 5) : 3 445 fenêtres. Les 80 plus récentes, prises dans les 6-K du 15 mai au 10 septembre 2026 (77 clés de contenu, 45 600 caractères), sont des blocs, toutes de niveau E (aucune incorporation par référence). 3 365 fenêtres de 187 6-K sont au-delà du plafond (`not_processed`) ; 269 6-K n'ont aucune fenêtre (`out_of_scope`) ;
  - à lire, dans l'ordre de la file (les corps de pièces n'entrent qu'après lecture de leur en-tête) :
    - Intel : 257 blocs, 1,33 M de caractères, plus 53 corps de pièces pour 2,57 M ;
    - Micron : 401 blocs, 1,30 M, plus 12 corps pour 1,32 M ;
    - TSMC : 196 blocs, 0,54 M, dont les 77 unités 6-K ;
    - listes `grp_intc`, `grp_mu` et `grp_tsm` ;
  - découverte d'origine (point 8) : quatre blocs déjà lus viennent des dépôts d'Intel et vont au groupe. Ce sont la note d'engagements du 10-Q du deuxième trimestre 2026 et trois en-têtes de pièces : contrat de société d'Arizona Fab LLC (2022, modèle et version refondue) et de Grange Newco LLC (2024). Deux de ces en-têtes figurent au catalogue d'Intel et ne se relisent pas (point 9). Ses 40 unités de la passe B, encore en file, en sortent au réassemblage ;
  - limites ajoutées : la note des intérêts minoritaires d'Intel (Arizona Fab LLC, coentreprise irlandaise avec Apollo, Mobileye, IMS) n'est pas une note du bloc `text` (placements, dette, baux, engagements) ; les accords de co-investissement se lisent dans les 8-K de la tranche, leurs pièces et les autres notes.

  (15) Lecture, sans sous-agent (2026-10-18), un commit par groupe (8468c77, 3c43ba5, 4b4e63a) :
  - Intel : 267 blocs lus sur 310 de la liste `grp_intc` (257 blocs et 10 corps de pièces) ; les 43 autres corps restent fermés à l'en-tête (établissements financiers seuls ou émission nouvelle). 1 585 observations et 37 abstentions. Lignes principales :
    - financement : séries d'obligations et papier commercial, débentures convertibles, obligations municipales de l'Arizona et de l'Oregon (autorités émettrices de Chandler et de l'Oregon), crédits renouvelables, prêt à terme de 2026 et prêt-relais d'avril 2026 (rachat des 49 % d'Apollo dans la coentreprise irlandaise) ; accord de financement de capacité avec Brookfield (Arizona Fab LLC, réalisé le 22 novembre 2022) et coentreprise irlandaise avec AP Grange Holdings, LLC (Grange Newco LLC, réalisée le 12 juin 2024) ; CHIPS Act (accord de financement direct de novembre 2024, puis actions ordinaires et bons de souscription acquis par le Département du Commerce le 27 août 2025) ; SoftBank Group Corp. (actions nouvelles d'août 2025) ;
    - cessions et participations : activité NAND à SK hynix Inc. (deux réalisations), 51 % d'Altera à SLP VII Gryphon Aggregator, L.P., affilié de Silver Lake (12 septembre 2025, participation de 49 % mise en équivalence ensuite), McAfee, Unisoc, IMFT (participation minoritaire vendue à Micron le 31 octobre 2019), ASML, Cloudera ;
    - litiges : VLSI Technology LLC, Commission européenne, R2 Semiconductor, Inc., IMECAS, MCP (brevets de Philips), EireOg Innovations Ltd. ; indemnités envers les clients poursuivis ; accords d'approvisionnement prépayés (clients anonymes) ;
  - Micron : 402 blocs lus sur 413 de la liste `grp_mu` (401 blocs et un corps de pièce, le plan d'actions de 2025, en abstention) ; les 11 autres corps restent fermés à l'en-tête. 1 304 observations et 142 abstentions. Lignes principales :
    - financement : séries d'obligations, prêts à terme et crédit renouvelable rattachés à leur accord par la date (accords de 2018, 2021, 2022 et 2025, tranches incrémentales), convertibles (avis, conversions, règlements), dette des membres d'IMFT envers Intel, prises fermes, remboursements anticipés et offres de rachat de 2026 ; CHIPS Act (Idaho et New York en décembre 2024, avenants et Virginie en juin 2025) ;
    - IMFT et Intel (rachat de la participation d'Intel le 31 octobre 2019, approvisionnement d'Intel), Inotera, Tera Probe, Powertech Technology Inc. Xi'an, entités ad hoc des locations d'équipements ; accords stratégiques avec des clients (obligations de prestation restantes d'environ 5 Md$ au 28 mai 2026), prépaiements et contreparties dues aux clients ; usine de Tongluo achetée à Powerchip Semiconductor Manufacturing Corporation (mars 2026) ;
    - litiges : Netlist, Inc., United Microelectronics Corporation, Fujian Jinhua Integrated Circuit Co., Ltd., Qimonda, President and Fellows of Harvard University, Bell Semiconductor, LLC, Innovative Memory Solutions, Inc. et Vervain, LLC, Allied Telesis K.K. ;
  - corrections pendant la lecture de Micron (D-0020), chacune vérifiée à blanc sur toute la liste avant la reprise : séparateur manquant après le motif des formules types (six motifs inopérants) ; crédit renouvelable et prêts à terme rattachés à leur accord par la date, non par le premier exercice du paragraphe ; doublons d'un tableau et de la phrase qui le commente écartés à 1 % près ; agrégat CHIPS de 2025 (6,1 Md$) porté par sa propre clé ; phrases coupées sur deux lignes recousues sans coller un titre à la phrase suivante, et demandeur d'un litige lu dans la dernière mention qui précède la phrase ; demandes chinoises réglées sorties après la date du règlement ;
  - TSMC : 196 blocs lus sur 196 de la liste `grp_tsm` (dont 77 unités 6-K). 358 observations et 114 abstentions. Lignes principales :
    - sociétés associées (GUC, VIS, SSMC, Xintec, Mutual-Pak) : créances et dettes des notes de parties liées, achats et ventes de l'Item 7.B, valeurs comptables des participations ; souscription à VIS en 2024 ; cession de 8,1 % de VIS le 15 mai 2026 (6-K) ;
    - financement : obligations émises à Taïwan et à l'étranger (encours et tranches de l'exercice, obligations vertes), prêts bancaires à long terme (NT$, JPY) et à court terme ; lettres de crédit inutilisées, garanties de bonne exécution données par des établissements financiers (non nommés) ;
    - engagements : droit de capacité de l'ITRI, engagement d'achat de capacité de SSMC et pacte d'actionnaires avec NXP B.V., dépôts de garantie de clients ; fins de litige avec Innovative Foundry Technologies LLC (octobre 2019) et Daedalus Prime LLC (septembre 2023) ; financement de la R&D d'ASML (276 M EUR, 2013 à 2017, Item 10.C du 20-F de 2018) ; coentreprise Advanced Vision Semiconductor Manufacturing Corporation avec Sony Semiconductor Solutions Corporation (accord préliminaire du 8 mai 2026, accord définitif du 11 août 2026, environ 282 Md JPY d'apports de TSMC) ; passifs sur contrats, encaissements provisoires de clients et passifs de remboursement ; passifs locatifs ;
  - TSMC, première passe refaite (D-0020) : la première passe, non committée, laissait en abstention les notes d'engagements et de baux des 20-F de 2018 à 2024. Leurs items à repère mis en cellule (« a. | Under a technical cooperation agreement… ») sortaient du découpage en phrases ; des coupures du texte source (« bond s », « guarante e ») et des libellés sur deux lignes (« Receivables from related » puis « parties ») cachaient des montants ; les tableaux d'une seule colonne (premier exercice d'IFRS 16, encaissements provisoires de 2021) n'étaient pas pris. Un contrôle de couverture (phrases et repères à montant qu'aucune ligne ne cite) les a relevés. Les 196 fichiers ont été retirés, les extracteurs corrigés et vérifiés à blanc, puis la liste relue entièrement : 301 observations, puis 358 ; les lignes écrites redonnent celles de la répétition à blanc. Les phrases à montant qui restent sans ligne sont des agrégats sans contrepartie (dépréciations d'équipements, plafonds des investisseurs QDII, ventilations du revenu) ;
  - limite relevée : le découpage en phrases du lecteur ne prend pas les lignes à cellules, donc ni les renvois de tableau (« (1) | … ») ni les puces mises en cellule. Contrôle sur les trois groupes : chez Micron, huit notes de dette des exercices 2018 et 2019 détaillent en renvoi des conversions et règlements de convertibles et le remboursement des obligations garanties 2023 (13 et 16 novembre 2017) dont les tableaux portent les totaux ; chez Intel, trois renvois de swaps de devises (notionnel, contrepartie non nommée) et des critères de la politique des transactions avec des proches. Aucune dénomination à forme juridique n'y manque aux lignes ;
  - limite relevée : les lignes des 8-K de l'accord de crédit de Micron de 2018 portent la clé `micron:credit_2018`, celles des notes les clés du crédit renouvelable et du prêt à terme qu'il ouvre ; elles ne se rapprochent pas par la clé ;
  - données personnelles (point 11) : aucune personne physique n'est contrepartie ; aucune citation ni note ne reprend un nom de personne physique (contrôle par motif sur les 865 fichiers des trois groupes). Personnes rencontrées et écartées : chez Micron, l'administrateur judiciaire de Qimonda et des dirigeants nommés dans les pièces ; chez TSMC, un demandeur personne physique.

  (16) Intégration (2026-10-18), trente groupes et trois non-déposants, vue `as_known` :
  - inventaire de D-0050 (point 6), après la lecture de chaque groupe : noms à forme juridique des lignes valides, présents dans un bloc lu du groupe et non confirmés : Intel 53 (12 avec une phrase à terme de filiale), Micron 45 (5), TSMC 9 (2) ; chaque phrase relue par l'exécutant ;
  - rattachements par extrait (point 6 ; D-0050, points 4 à 7), 10, chacun vérifié mot pour mot dans un bloc lu et sans nom de personne physique, dans `config.yaml` :
    - Intel (5) : Intel Ireland Limited, Arizona Fab HoldCo Inc. et Intel Americas, Inc. (« a wholly owned subsidiary of Intel ») ; Altera Corporation, sortie à la cession de 51 % réalisée le 12 septembre 2025 (`valid_to` au 11 septembre ; la participation conservée est mise en équivalence, l'entité forme ensuite son propre groupe) ; Arizona Fab LLC, coentreprise de l'usine d'Arizona (« which we will fully consolidate into our consolidated financial statements », 10-Q du troisième trimestre 2022), entrée à la réalisation du 22 novembre 2022 (item 2.01) ;
    - Micron (5) : Micron Idaho Semiconductor Manufacturing (Triton) LLC, Micron New York Semiconductor Manufacturing LLC et Micron Virginia Semiconductor Manufacturing LLC (parties des accords du CHIPS Act), Micron Semiconductor Products, Inc. (« the only guarantor subsidiary ») ; IM Flash Technologies, LLC, entité à intérêts variables consolidée (« We consolidate IMFT… », chaîne avec la définition de l'IMFT du 8-K du 1er novembre 2019), filiale à 100 % après le rachat de la participation d'Intel le 31 octobre 2019 : les lignes d'Intel sur l'IMFT vont à Micron ;
    - TSMC : aucune filiale nommée dans ses lignes ; ses sociétés associées (GUC, VIS, SSMC, Xintec, Mutual-Pak), mises en équivalence, restent des entités propres ;
    - vingt et un alias (D-0021), chacun défini par un extrait : IMFT, Micron, Altera, McAfee, VLSI, Unisoc, ASML, Cloudera, JD (Beijing Jingdong Century Information Technology, Ltd.), Cisco, IBM, HPI (HP, Inc.) et DOC dans les blocs d'Intel ; Intel dans un 8-K de Micron ; VIS, SSMC, Xintec, GUC, Mutual-Pak et TSMC dans les blocs de TSMC ; « Taiwan Semiconductor Manufacturing Company », graphie du 8-K de Broadcom du 5 mai 2020, par la définition de « TSMC » commune à ce 8-K et au 6-K de TSMC du 11 août 2026. Trois entités propres par extrait : United States Department of Commerce (accords du CHIPS Act d'Intel et de Micron, actions d'Intel achetées en août 2025), Industrial Development Authority of the City of Chandler, Arizona et State of Oregon Business Development Commission (émettrices des obligations municipales prêtées à Intel par contrat de prêt) ;
  - restent des contreparties propres, faute d'extrait qui les dise consolidées : Grange Newco LLC (coentreprise irlandaise, 51 % Intel Ireland ; aucune phrase des blocs lus ne la dit consolidée, et la note des intérêts minoritaires n'est pas lue, point 14), Foundry JV Holdco LLC et AP Grange Holdings, LLC (véhicules des associés, point 6 ; AP Grange n'est pas rattachée à Apollo, D-0055, point 5), SLP VII Gryphon Aggregator, L.P. (affilié de Silver Lake), les sociétés associées de TSMC. Mobileye Global Inc. : aucune ligne ne la nomme comme contrepartie (une abstention seulement) et aucun bloc lu ne la dit filiale ; ses rapports ne sont pas au corpus (CIK hors des groupes, aucune unité de la découverte) : rien à rattacher ni à exclure. Restent en attente : « Brookfield » (deux entités selon le document : Foundry JV Holdco LLC dans les 8-K, Brookfield Asset Management dans la note de 2022), « Dell » (Dell Technologies, Inc. dans le 10-Q de novembre 2025, Dell China, Ltd. dans ceux de 2021 et 2022, sans définition ailleurs), « SoftBank Group » (placement de 2,0 Md$ d'août 2025, deux notes de la piste des non-déposants tirées des dépôts d'Intel ; la pièce du 25 août 2025 nomme SoftBank Group Corp. et relie Intel à SoftBank), « Oregon Business Development Commission » (sans « State of »), HPE, HP, Lenovo, Acer, Fujitsu, Silver Lake ; chez Micron, Powertech Technology Inc. Xi'an, Tera Probe, Inotera, Tektronix, Qimonda et des succursales de banques ; chez TSMC, « Vanguard International Semiconductor » et « Sony Semiconductor Solutions », écrites sans forme juridique dans un 6-K ;
  - corrections dans la passe (D-0020) : deux lignes d'Intel du bloc 196fbd477e55 (clients poursuivis par Philips, puis MCP) prennent la désignation du bloc, « Dell Technologies, Inc. (Dell) » et « Lenovo Group Ltd. (Lenovo) » ;
  - code : noms des trois groupes au rendu, nombre de groupes en lettres jusqu'à trente ; un test (`tests/test_fabricants.py`, six cas : sortie d'Altera, entrée d'Arizona Fab LLC, IMFT consolidée par Micron, noms courts, sociétés associées de TSMC, véhicules des associés) ;
  - découverte d'origine (point 8) : les 40 unités d'Intel de la passe B sortent de la file (`INTC:discovery_units`, `out_of_scope`) ; les lignes de ses quatre blocs déjà lus et des deux notes de la piste des non-déposants tirées de ses dépôts vont au groupe. La piste des non-déposants garde son unité tirée d'une pièce d'Intel (8-K du 25 août 2025), hors de sa règle de lecture (D-0044), comme celles d'Apollo ; ce document est lu par le catalogue d'Intel ;
  - premier réassemblage : observations 22 463 → 26 003 (les 3 540 lignes des trois groupes sont valides), entités 2 570 → 2 753, liens 8 756 → 9 549, faits 1 379 828 → 1 549 482 ;
  - arêtes au dernier réassemblage : Intel 423 (124 à montant ; 12 internes ; 50 vers des noms en attente) ; Micron 202 (90 ; 1 interne ; 28) ; TSMC 138 (125 ; aucune vers un nom en attente). Entre groupes suivis : Intel → Micron 79 (58 à montant : achats à l'IMFT, dette des membres, apports, engagements) et Micron → Intel 30 ; Dell → Intel 4 (relation de client) et Intel → Dell 1, Intel → Amazon 7 et Intel → Oracle 5 (indemnités envers des clients poursuivis), NVIDIA → Intel 2 (investissement de 2025, une à montant), SoftBank → Intel 1, Broadcom → TSMC 1 (achats de plaquettes) ;
  - BDC Data Sets : extraction refaite après le premier réassemblage (D-0043, point 14) : 3 054 099 lignes de positions (3 032 517 avant), 2 100 dépôts. Faits de BDC rattachés : 3 238 (2 154), dans 419 dépôts de 59 fonds (258, 47). Nouveaux émetteurs, tous nommés par des lignes d'Intel : Cloudera, Inc. (556 faits, 105 dépôts, 9 fonds) et McAfee Corp. (434, 102, 13), prêts de premier et de second rang ; Lenovo Group Ltd. (90 faits, mezzanine structurée d'un fonds) ; Altera Corporation, un prêt à terme de premier rang d'un fonds au 30 juin 2025 (1,9 M$ de principal, échéance du 21 juin 2032, juste valeur ÷ coût de 1,006), rattaché à Intel par la règle de la dénomination entière et la date (la cession n'est réalisée que le 12 septembre) : il finance probablement le rachat par l'affilié de Silver Lake, à vérifier dans le dépôt. Aucune position sur Intel, Micron, TSMC ni leurs autres filiales. Second réassemblage : faits 1 549 934, entités 2 755, mesures 157 624 ;
  - rendus : documents 22 550, faits 1 549 934, observations 26 003, entités 2 755, liens 9 549, mesures 157 624, exclusions 26 921 ; 10 931 nombres publiés (9 818). Annexe F : 398 événements des groupes (359) : Intel 22 (F1 5, F2 13, F4 1, F8 3), Micron 17 (F1 5, F2 8, F6 3, F8 1), TSMC aucun (cellules annuelles seulement, point 12). Paires : 186 (160) ; 27 nouvelles, dont NVIDIA → Intel, qui remplace NVIDIA → INTEL CORP (même paire, désormais nommée par son groupe) ; conclusions : causalité non établie 141 (122), relation commerciale doublée d'un financement 20 (14 ; nouvelles : Intel → Altera Corporation, Micron → Intel, TSMC → GUC, SSMC, VIS et Xintec), achats réciproques seulement 17 (16 ; nouvelle : Micron → Nanya Technology Corporation), dépendance documentée 8 (8). Paires à financement documenté : 69 (57). Cycles (E.6) : 69 (53), dont Intel ↔ Micron, Intel → Micron → United States Department of Commerce → Intel, Dell ↔ Intel, Intel ↔ Altera Corporation, Intel ↔ les véhicules des associés de ses usines, TSMC ↔ quatre de ses sociétés associées. E.7 : discrimination possible, 57 % d'issues indéterminées sur 136 (58 % sur 112 avant l'ajout) ; E.1 non étayé 58 (47) ;
  - tests unitaires : 143, tous passés.
- **D-0057 — Ajout de groupes : ASML (ASML) et SK hynix (SKHY), émetteurs privés étrangers ; Samsung, groupe économique non déposant (§10.4). Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-18 : « Ajoute SK Hynix, Samsung et ASML ». Elle suit le rapport d'intégration d'Intel, de Micron et de TSMC (D-0056, commit 936611a). Ce sont un fabricant d'équipements et deux fabricants de mémoire, après les fabricants de D-0056 (§14). Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Statut lu avant tout tirage, sans aucune requête, dans `company_tickers.json` du 2026-10-07 et la liste des noms d'EDGAR du 2026-10-09, déjà en cache :
  - ASML résout le CIK 937966 (ASML HOLDING NV, aussi coté sous ASMLF) : groupe complet, émetteur privé étranger (20-F et 6-K) ;
  - SK hynix résout le CIK 2120882 (SK hynix Inc., cotations SKHY et HXSCL). Ce CIK est plus récent que celui de NSCALE Ltd (2110365, créé en 2026, D-0054, point 13) : SK hynix est un déclarant de 2026. Il entre comme groupe complet `SKHY`, avec `history_left_censored` si son premier dépôt suit le début de lecture. La phase 0 lit ses dépôts. Si aucun rapport périodique (20-F) n'est déposé avant l'as_of, les exercices présentés par son document d'enregistrement en tiennent lieu, comme les 424B4 de SpaceX et de CoreWeave (`reporting_start`). Les règles de lecture de ce document se consignent alors ici avant toute lecture ;
  - Samsung : aucune entrée dans `company_tickers.json`, donc aucun titre coté à l'as_of. La liste des noms d'EDGAR donne des CIK sans cotation : SAMSUNG ELECTRONICS CO LTD /FI (879316), SAMSUNG DISPLAY CO., LTD. (1843625), et d'autres sociétés du nom (Samsung C&T Corp, Samsung Corp, filiales financières américaines). Samsung entre comme groupe économique non déposant `NF:SAMSUNG`, sur le modèle de SoftBank (D-0044) et de Lambda et Nscale (D-0054) : Samsung Electronics Co., Ltd. et ses filiales consolidées. Les autres sociétés du nom (Samsung C&T, Samsung SDI, Samsung Biologics, Samsung Life, Samsung Securities, Samsung Heavy Industries…) ne sont pas consolidées par Samsung Electronics et n'entrent pas au groupe. Ses sociétés mises en équivalence n'y entrent pas non plus (D-0050, point 4). Le statut se vérifie en phase 0 sur les submissions de Samsung Electronics et de Samsung Display : aucun rapport périodique depuis le début de lecture. Si l'une en a déposé, la règle est revue ici avant toute lecture. Comme pour un laboratoire, la recherche est complète du côté de Samsung pour une paire (E.0) et pour un cycle (bloc `paths`) ;
  - l'exécution garde l'as_of du 2026-10-07 (D-0048, point 2). ASML et SKHY entrent dans `groups` et `group_entry` au 2026-10-18.

  (3) ASML et SK hynix, émetteurs privés étrangers : mêmes phases et mêmes règles que TSMC et Nebius (D-0056, point 5 ; D-0048, points 5, 6 et 9) :
  - 20-F dans les rapports périodiques ; un exercice qui n'a qu'un rapport annuel se découpe en quatre trimestres de trois mois ; `reporting_start` met leurs trimestres à `not_applicable`, avec la règle 13a-13 pour pièce ; signaux du 20-F au trimestre de clôture ;
  - textes lus : notes du 20-F par rôles XBRL, Item 15 en bloc `item_9a`, Item 7.B en `item_404`, Item 10.C en `item_8k_101` ; délimitation de D-0048, point 9 ;
  - 6-K : unités de D-0048 (points 6 et 9), même lexique de termes, plafond de 80 unités par groupe, du plus récent au plus ancien. Les noms qualifiants sont ceux du lexique de la découverte et de tous les groupes et non-déposants de `config.yaml` à cette date, jamais le groupe lui-même (`foreign_6k.group_names_by_group`). Les unités de Nebius, d'IREN et de TSMC ne changent pas. Un 6-K est furnished (niveau E), sauf incorporation par référence lue dans le 6-K (niveau C, D-0042) ;
  - cadre comptable, lu en phase 0 dans les instances XBRL (espace de noms des faits) et dans la base de préparation des états. Pour ASML, le US GAAP est attendu : pas d'entrée `group_frameworks`. Pour SK hynix, les IFRS publiées par l'IASB sont attendues : `group_frameworks` (`SKHY: ifrs`), candidats `concept_anchors_ifrs`, totaux IFRS de C1 et C2, invariant (f), comme TSMC. Si les états suivent un autre référentiel, la règle est revue ici avant toute lecture. C'est le cas d'IFRS adoptées par la Corée sans déclaration de conformité à celles de l'IASB, ou d'états sans XBRL ;
  - monnaies : euros (ASML), wons (SK hynix) ; aucun agrégat ne mêle les monnaies (invariant b).

  (4) Successions et ruptures d'historique : règle de D-0052, point 5, vérifiée en phase 0 sur la liste des dépôts (8-K12, `formerNames`, items 2.01 et 3.03 ; pour un émetteur étranger, 6-K de réalisation) et par un extrait cité. Aucune n'est attendue : chacun des deux CIK porte le même déclarant sur toute la période. Les acquisitions d'ASML (Berliner Glas en 2020) et sa participation dans Carl Zeiss SMT Holding sont des changements de périmètre (§10.2). Si la phase 0 montre autre chose, la règle est revue ici avant toute lecture.

  (5) Filiales et entités : règle de D-0050 (points 3 à 7), appliquée à l'intégration, après la lecture, aux dénominations nommées dans les lignes, y compris celles des autres groupes et les positions des BDC. Une filiale entre au groupe par un extrait qui la dit filiale ou consolidée (Solidigm, la filiale de SK hynix issue de l'activité NAND d'Intel, ne s'y rattache que sur un tel extrait). Une société mise en équivalence reste une entité propre.

  (6) Samsung, niveau 1 : entités réunies par extraits (§10.2, D-0021), comme pour SoftBank (D-0044, points 3 et 7) : la tête du groupe (Samsung Electronics Co., Ltd.) et ses filiales n'y entrent que sur un extrait qui l'affirme, avec sa date. Règles A (lien affirmé) et B (désignation par un alias confirmé du groupe) de D-0044, point 7.

  (7) Samsung, niveau 2 : la piste des non-déposants (D-0044, points 4 et 5) reçoit son terme, sans autre changement :
  - lexique de la piste : « Samsung », en mot entier, insensible à la casse, cible `NF:SAMSUNG`. Les mentions des sociétés du nom non consolidées par Samsung Electronics deviennent des candidats comme les autres : la lecture écrit le nom de l'entité nommée, et le rattachement au groupe ne se fait que par extrait (point 6) ;
  - Notes Data Sets : les 47 archives de la piste, retirées et scannées avec le lexique d'ensemble enrichi ; recherche plein texte du terme sur les formulaires racines des EX-10. Pas de Form D : le bloc `form_d` ne prend pas Samsung pour sous-jacent ;
  - candidats, classement, règle de lecture (R1, R2) et plafond de 300 unités : ceux de D-0044, point 5, sur l'ensemble de la piste. Les co-mentions restent celles du lexique d'ensemble (groupes du lexique de la découverte, laboratoires, Stargate, non-déposants) ;
  - l'état des unités de SoftBank, de Lambda et de Nscale se garde sous leur clé (accession, document). Rien ne se relit, et une unité déjà lue par la découverte d'origine ou par la piste (même clé de contenu) ne se relit pas ;
  - au-delà du plafond, la lecture s'arrête à la 300e unité et le rendement est présenté avant d'aller plus loin ;
  - SK hynix, déclarant (point 2), n'entre pas dans la piste.

  (8) Lignes déjà lues qui nomment ces sociétés, relevées avant tout tirage : seize lignes d'Intel nomment « SK hynix Inc. » (cession de l'activité NAND). Onze lignes d'Intel nomment « ASML Holding N.V. » et sept « ASML » (participation vendue en 2019 ; alias de D-0056). Deux lignes de TSMC nomment « ASML Holding N.V. » (financement de la R&D de 2013 à 2017). Aucune ligne ni citation ne nomme Samsung. Ces lignes vont aux groupes par les règles ordinaires : la dénomination légale entière se résout en la tête (même CIK) ou en une entité par extrait (D-0021 ; D-0056, point 7). Aucune correction n'est faite d'avance.

  (9) Découverte d'origine (D-0043, point 6) : aucune unité, aucun candidat et aucun bloc déjà lu ne vient des dépôts d'ASML, de SK hynix ou de Samsung (CIK 937966, 2120882, 879316, 1843625). La piste des non-déposants n'en a pas non plus. Côté client, la recherche reste incomplète pour un fournisseur que le lexique de la découverte ne nommait pas. Le lexique, le classement, la file et l'état de lecture de la découverte ne changent pas (D-0036).

  (10) Montages : `meta_hyperion` et `athene_whco` ne changent pas. BDC : les positions sur les entités des nouveaux groupes viennent de l'extraction refaite après le premier réassemblage (D-0043, point 14). Aucune ligne des BDC Data Sets extraites en D-0056 ne nomme SK hynix ni ASML, déjà au registre par les lignes d'Intel ; Samsung n'y était pas. Les lexiques déjà fixés ne changent pas, hors le terme de Samsung (point 7) : unités 6-K de Nebius, d'IREN et de TSMC, termes des montages, lexique de la découverte.

  (11) Données personnelles (D-0051 ; D-0056, point 11) : aucune personne physique n'est contrepartie. Les noms des contrats de travail, des lettres d'offre, des blocs de signature et des circulaires (rémunérations, transactions avec des proches) ne sont pas repris.

  (12) Limites connues avant calcul :
  - ASML et SK hynix n'ont pas de série trimestrielle (cellules « annuel seulement ») ;
  - SK hynix n'a, au plus, que les exercices de son document d'enregistrement et ses 6-K. Si son cadre est IFRS, ses grandeurs sans équivalent IFRS restent non résolues et ses contrôles autres que C1 et C2 non testables ;
  - Samsung n'a pas de comptes au modèle : seuls les dépôts des autres le nomment ;
  - les montants en euros et en wons ne se comparent aux autres groupes que par des ratios.

  (13) Ordre et commits :
  - la décision ;
  - la configuration et le code (groupes, entrée, noms des 6-K, non-déposant et terme de la piste, noms au rendu), avec leurs tests, la phase 0 et l'univers attendu ;
  - l'index, les archives XBRL, les pièces et les 6-K (phases 0, 1 et 2, réseau en série) ;
  - le catalogue et les listes de lecture, avec leur volume consigné ici avant toute lecture ;
  - la piste des non-déposants (archives, recherche plein texte, pièces, candidats, unités retenues), avec son volume consigné ici avant toute lecture ;
  - la lecture d'ASML, puis celle de SK hynix, puis celle des unités de Samsung, un commit par partie ;
  - l'intégration : entités et filiales par extrait, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (14) Constats de la phase 0 et règles du document d'enregistrement de SK hynix, fixés avant tout catalogue et toute lecture (points 2 et 3) :
  - ASML : 127 dépôts dans la période, dont huit 20-F (exercices 2018 à 2025) balisés en US GAAP (faits `us-gaap` et extension `asml`), donc pas d'entrée `group_frameworks`, et 78 6-K. L'ancienne dénomination ASM LITHOGRAPHY HOLDING NV a pris fin en 2001, avant le début de lecture : aucune rupture d'historique ;
  - SK hynix : premier dépôt le 2026-03-24, un DRS soumis et non déposé (§2.1), d'où `history_left_censored`. Suivent trois DRS/A, le F-1 0001193125-26-280172 et deux F-1/A, le F-6, le 8-A12B, deux EFFECT (2026-07-09), le 424B4 0001193125-26-299963 du 2026-07-10 et 21 6-K du 2026-07-15 au 2026-09-18. Aucun 20-F avant l'as_of : le premier, pour l'exercice 2026, est attendu en 2027 ;
  - companyfacts de SK hynix : dix faits `dei`, ceux des pages de couverture du F-1 et du F-1/A. Aucune instance XBRL financière : les états du 424B4 n'existent qu'en HTML. Ce sont les états consolidés audités des exercices 2023 à 2025, en IFRS publiées par l'IASB (déclaration de conformité de la note 2, opinion d'un cabinet inscrit au PCAOB), en millions de wons, et les états intermédiaires résumés du premier trimestre 2026 (IAS 34), non audités ;
  - Samsung : submissions lues le 2026-10-18, en deux requêtes journalisées. Samsung Electronics Co., Ltd. (879316) a 251 dépôts, le dernier du 2015-01-20 (SUPPL, ARS, déclarations d'offre publique et de participation), et aucun rapport périodique. Samsung Display Co., Ltd. (1843625) n'a que neuf déclarations de participation (13D, 13G, formulaires 3 et 4) de 2021 à 2025, et aucun rapport périodique. Le point 2 s'applique sans révision : `NF:SAMSUNG` est un groupe non déposant.

  Le cadre de SK hynix suit les IFRS de l'IASB, mais ses états n'ont pas de XBRL. La règle du point 3 est donc revue ici, et le document d'enregistrement tient lieu de rapports périodiques (point 2) :
  - `reporting_start` : exercices à partir du 2023-01-01, pièce du 424B4 (exercices 2023 à 2025 présentés). Les exercices 2021 et 2022 de la fenêtre sont `not_applicable` ; les trimestres le restent (règle 13a-13) ;
  - `group_frameworks` : `SKHY: ifrs`, comme TSMC. Les notes lues portent ce cadre (invariant f) ;
  - grandeurs : sans instance, aucune cellule annuelle ne se calcule. SpaceX avait un rapport balisé postérieur dont les concepts appariaient les lignes de ses états HTML (D-0010) ; SK hynix n'en a aucun. Ses états ne se lisent donc pas en tableaux. Les cellules de ses exercices 2023 à 2025 restent indéterminées, et C1 et C2 ne sont pas testables, ce qui étend la limite du point 12 ;
  - texte : le 424B4 se lit comme un 20-F (point 3), les titres des notes tenant lieu de rôles XBRL (`config.yaml`, `registration_text` ; `pipeline/regdoc.py`) ;
  - découpage : les deux jeux de notes se découpent en HTML. Un jeu s'ouvre au titre courant « Notes to the … Financial Statement(s) » suivi de la note 1. Une note va de son titre « N. Titre » au titre suivant, et le jeu se ferme au titre d'un état financier ou après le dernier pied de page. Pieds de page « F-n », titres courants et titres « Continued » sont retirés. Résultat : 35 notes annuelles et 32 notes intermédiaires ;
  - familles lues, reconnues au titre de la note :
    - celles des rôles (`NOTE_SPECS` : participations, dette, baux, engagements) ;
    - la note de parties liées et la note de revenu ;
    - les notes des leviers : immobilisations corporelles, estimations et jugements, et paragraphe « Property, plant and equipment » de la note des principes comptables ;
    - les paragraphes des clients de la note sectorielle.

    Les autres notes ne se lisent pas, comme les rôles d'un 20-F hors de ces familles : information générale et filiales, instruments financiers et risques, impôts, résultat par action, flux de trésorerie, paiements en actions, événements postérieurs ;
  - niveaux : jeu annuel audité (A) ; jeu intermédiaire non audité (C, `unaudited`) ;
  - la section « Certain Relationships and Related Party Transactions » du prospectus se lit en `item_404`, comme dans les 424B4 de CoreWeave et de SpaceX (catalogue, étape 3). Le reste du prospectus (activité, rapport de gestion, facteurs de risque) ne se lit pas, comme le corps d'un 20-F hors des items de D-0048, point 9. Les pièces du F-1 ne se lisent pas, comme celles des S-1 de CoreWeave et de SpaceX. Les unités 6-K suivent le point 3 ;
  - volume obtenu : 21 blocs de notes, soit 86 143 caractères de notes entières, plus le paragraphe des immobilisations et les paragraphes des clients, et la section des parties liées (8 219 caractères). Un test couvre le découpage : deux jeux, numérotation suivie, bruit de page retiré, familles par titre, niveaux.

  (15) Phases 0 à 2, catalogue et listes de lecture, avant toute lecture (2026-10-18) :
  - réseau, en série : 464 requêtes, toutes en 200, 395,7 Mo, toutes vers les hôtes de la SEC (www.sec.gov 458, data.sec.gov 6). Ce sont 4 submissions (dont les deux de Samsung, point 14), 2 companyfacts, 117 en-têtes et index, 8 archives XBRL et 333 documents : le rapport intégré de 2018 d'ASML, antérieur à l'iXBRL, le 424B4 de SK hynix, et les documents principaux et annexes 99 des 6-K (309 pièces). Aucun 403 ;
  - inventaire : ASML a 8 20-F (exercices 2018 à 2025) et 78 6-K, sans 8-K ni circulaire ; SK hynix a le 424B4 (classe `ipo`) et 21 6-K, sans rapport périodique. Les inventaires et l'univers attendu des groupes présents sont inchangés : vérifiés par groupe, dépôt et classe, Intel, Micron et TSMC aux effectifs de D-0056, point 14 ;
  - index : 2 217 dépôts (9 nouveaux), aucun échec. Archives XBRL : 783 dépôts lus (8 nouveaux), et les 7 échecs déjà connus. Pièces : 2 322 documents (2 nouveaux), aucun échec ;
  - univers attendu : 23 652 cellules, dont 1 404 pour les deux groupes. ASML en a 660, dont 560 trimestrielles sans objet. SK hynix en a 744 : 644 trimestrielles sans objet, 40 annuelles sans objet (exercices 2021 et 2022) et 60 annuelles attendues (exercices 2023 à 2025) ;
  - amendement, avant toute lecture : les 20-F d'ASML sont des rapports annuels intégrés. Ils ne numérotent leurs items que dans leur table de correspondance (« Reference table 20-F »), et les délimiteurs des Items 15, 7.B et 10.C ne trouvaient rien dans aucun des huit. Règle, sur le modèle de l'index d'Intel (D-0056, point 14) : dans un 20-F à table de correspondance, l'item est la section que la table désigne.
    - Une annexe (« Appendix - Controls and procedures », « Appendix - Material contracts ») va de son titre au titre d'annexe suivant, sans les lignes de mise en page.
    - Si ce texte ne porte pas le contenu de l'item (« disclosure controls » pour l'Item 15, un contrat ou un accord pour l'Item 10.C), le titre est celui de la page qu'il clôt, et l'annexe est le texte qui le précède. C'est la mise en page du 20-F de l'exercice 2023.
    - Un renvoi à une note des états ne donne pas de bloc, la note étant déjà au catalogue par son rôle XBRL : note des parties liées, note 30 sur le programme de co-investissement des clients (CCIP) en 2018. « None » ne donne rien.

    Résultat : 8 Items 15, de 2 850 à 2 950 caractères. L'Item 10.C donne 5 blocs pour les exercices 2018 à 2022 (accords avec Carl Zeiss SMT), « None » pour 2023 et 2024, et un renvoi à la note 26 pour 2025. Les 8 Items 7.B renvoient aux notes des parties liées. Aucun 20-F de Nebius ni de TSMC n'a une telle table : leurs blocs sont inchangés. Code : `sections.xref_20f`, `catalog.build`, trois tests unitaires ;
  - catalogue : aucune clé de bloc déjà lue ne change, et les blocs des groupes présents sont identiques (catalogue principal, bloc `text`, unités 6-K). Le catalogue principal passe de 4 333 à 4 355 blocs, celui du bloc `text` de 4 574 à 4 679, celui des unités 6-K de 240 à 400 ;
  - 6-K d'ASML (point 3) : 995 fenêtres. Les 80 plus récentes sont prises dans les 12 6-K du 15 octobre 2024 au 15 juillet 2026 (80 clés de contenu, 2 634 818 caractères) :
    - 45 viennent des 6-K qui déclarent leurs annexes incorporées par référence dans les enregistrements sur Form S-8 : niveau C (D-0042) ;
    - 35 viennent des deux 6-K des rapports annuels statutaires de 2024 et de 2025, établis en IFRS adoptées par l'Union européenne pour les besoins du droit néerlandais (« Annual Report based on IFRS », annexes 99.1, 1,11 M et 1,16 M de caractères en 18 et 17 fenêtres, la plus grande de 281 630 caractères) : niveau E. Un narratif ne porte pas de cadre comptable (`foreign.block_framework`) ; un montant qui double une ligne du 20-F est une abstention `duplicate_of_other_block` (D-0038, point 4). La règle des fenêtres (D-0048, points 6 et 9) ne borne pas leur taille et s'applique sans changement ;
    - 915 fenêtres de 58 6-K sont au-delà du plafond (`not_processed`) ; 9 6-K n'ont aucune fenêtre (`out_of_scope`) ; une présentation en PDF n'est pas lue (`out_of_scope`) ;
  - 6-K de SK hynix : 114 fenêtres. Les 80 plus récentes (78 clés, 64 638 caractères) viennent de deux 6-K : 79 de celui du 18 août 2026 et une du 19 août. Toutes sont de niveau E, sans incorporation par référence. 34 fenêtres de 3 6-K sont au-delà du plafond ; 17 6-K n'ont aucune fenêtre ;
  - à lire, dans l'ordre de la file :
    - ASML : 183 blocs, 3,17 M de caractères. Ce sont 103 blocs des 20-F (0,53 M : notes par rôles, Items 15 et 10.C, notes des parties liées) et les 80 unités 6-K (2,63 M) ;
    - SK hynix : 100 blocs, 0,16 M de caractères. Ce sont les 21 blocs de notes du 424B4 (0,09 M), sa section des parties liées (8 219 caractères) et les 78 unités 6-K (0,06 M) ;
    - listes `grp_asml` et `grp_skhy`.

  (16) Piste des non-déposants (point 7), avant toute lecture (2026-10-18) :
  - Notes Data Sets : les 47 archives de la piste, retirées de nouveau (47 requêtes, toutes en 200, 18,56 Go) et scannées avec le lexique d'ensemble enrichi (`lx-32cb5adcf3c6`), chacune effacée après son scan ;
  - recherche plein texte des EX-10 : 125 requêtes pour « Samsung » (124 en 200, une erreur 500 du serveur reprise par le client). La requête dépasse 10 000 résultats et se coupe en deux périodes : 5 006 résultats du 2017-01-01 au 2021-11-19, 7 141 du 2021-11-20 à l'as_of. Sur ces résultats, 276 sont des pièces EX-10, dans 201 dépôts. SoftBank, Nscale et Lambda sont inchangés (en cache, aucune requête) ;
  - vérification : 576 pièces (199 requêtes, toutes en 200). 552 nomment un non-déposant (Samsung 261, SoftBank 292, Nscale 2), 24 aucun. Trois pièces de SoftBank nomment aussi Samsung. Une pièce de SoftBank sort : l'EX-10.1 d'Intel du 22 août 2025, qu'Intel dépose et qui se lit comme texte d'Intel depuis D-0056 (règle de D-0043, point 6) ;
  - candidats et file, règle de D-0044 (point 5) sans changement : 4 114 mentions (Samsung 2 698, SoftBank 1 403, Lambda 8, Nscale 5), 363 candidats (dont 279 nomment Samsung) et 3 717 unités :
    - 300 retenues : R1, 81 en-têtes de pièces et 219 notes ;
    - 116 au-delà du plafond (R1 19, R2 97), qui restent `not_processed` ;
    - 3 301 hors de la règle ;
  - unités déjà lues : des 78 unités de SoftBank retenues en D-0054, toutes lues, 38 restent dans les 300 premières. 38 passent au-delà du plafond, les unités R1 de Samsung les précédant dans l'ordre de la file. Deux sortent de la file : les notes du résultat par action d'Intel (10-Q du troisième trimestre 2025, 10-K 2025), Intel étant un groupe depuis D-0056. Leur état se garde sous leur clé : rien ne se relit, et l'assemblage ne compte pas en exclusion une unité dont le bloc est lu ;
  - Samsung : 266 unités retenues le nomment (262 nouvelles et 4 déjà lues pour SoftBank). Leurs 262 blocs ont été préparés en 181 requêtes, toutes en 200. Ils donnent 244 clés de contenu nouvelles, dont 4 déjà lues ailleurs ;
  - à lire : 240 blocs, 6,00 M de caractères, soit 181 notes (5,82 M) et 59 en-têtes de pièces EX-10 (0,18 M). Un corps de pièce n'entre qu'après lecture de son en-tête, s'il montre pour partie un groupe de la liste, un laboratoire, Stargate ou un autre non-déposant (D-0044, point 5). Liste `nf_samsung`, dans l'ordre de la file ;
  - déposants : 67, dont Netlist (22 blocs), QVC (19), Network-1 Technologies (23 sous deux dénominations), CuriosityStream (17), InterDigital (14), Kartoon Studios (13), Shinhan Financial Group (12), Qualcomm (12), Rambus (9) et VoIP-Pal (9). Ce sont surtout des licences et des litiges de brevets, des contrats de distribution et de fourniture. Co-mentions des blocs : Amazon 115, Alphabet 101, Microsoft 45, Meta 37, NVIDIA 32, Broadcom 23, Oracle 11, SpaceX 11, AMD 6, Marvell 6, CoreWeave 2 ;
  - la lecture s'arrête à la 300e unité de la file ; le rendement est présenté avant d'aller plus loin (point 7).

  (17) Lecture, sans sous-agent (2026-10-18 et 2026-10-19), un commit par partie (06bab69, 4ef977c, 9d37e21 et 032fe29 ; correction 1fb0b26) :
  - ASML : 183 blocs lus sur 183 de la liste `grp_asml` (103 blocs des 20-F et 80 unités 6-K). 486 observations et 115 abstentions. Lignes principales :
    - Carl Zeiss SMT : participation de 24,9 % dans Carl Zeiss SMT Holding GmbH & Co. KG (mise en équivalence : valeur, résultat, dividendes) et intérêt variable dans cette entité non consolidée (exposition maximale par accord : EUV, DUV, High NA, participation) ; achats, dettes, créances et charges à payer de la note des parties liées ; avances sur livraisons de colonnes optiques et soutien de l'accord High-NA de 2016 (760 M€ estimés d'abord, financements additionnels de 2017 et de 2018) ; accord-cadre de 2021 : prêts de septembre 2021 et de septembre 2024 (jusqu'à 1 Md€ chacun), prêts sans intérêts de 2025, plancher de flux de trésorerie, financement de la R&D High NA ; garantie de ces prêts par Carl Zeiss AG ;
    - financement : euro-obligations (séries de 2013 à 2023, valeurs comptables par exercice), facilité confirmée de 1,5 Md€ non tirée, lignes non confirmées (3 Md€), programme de papier commercial européen (ouvert en 2024), dette reprise de Berliner Glas (prêt hypothécaire, facilités renouvelables, location-financement), facilité non confirmée de la filiale chinoise (130 M€), facilités de garantie et leur utilisation (EUR, JPY, TWD), garantie de la société mère pour le bail de San Jose (92,4 M€) ;
    - engagements et revenu : obligations d'achat, passifs nets sur contrats, obligations de prestation restantes (46,5 Md€ au 2025-12-31), commandes non comptabilisées de 2018 (6,2 Md€ de systèmes, 0,8 Md€ de services), passifs locatifs, indemnisation des clients en matière de brevets ;
    - autres : règlement avec Nikon (protocole du 23 janvier 2019, accords du 18 février 2019 : 150 M€ versés à Nikon par ASML et Carl Zeiss SMT, dont 131,0 M€ pour ASML, licence croisée de dix ans) ; Mistral AI (participation à la juste valeur, montant propre non publié) ; Koppelenweg I B.V. (entité à intérêts variables propriétaire du siège de Veldhoven jusqu'à l'option d'achat du 28 juin 2018, 24,5 M€ ; prêt subordonné de 5,4 M€ à la société mère du bailleur, remboursé le 4 juillet 2018) ; Intel et TSMC, clients nommés sans montant dans les rapports statutaires et une présentation de 2026. Aucun bloc d'ASML ne nomme Samsung ;
  - corrections pendant la lecture d'ASML (D-0020) : le contrôle de couverture (phrases à montant qu'aucune ligne ne cite) a relevé des faits perdus par les tournures des exercices anciens, le marquage en bloc et la clé de nouveauté, qui tient pour vue une phrase reprise d'un exercice à l'autre. Les extracteurs ont été généralisés et 17 blocs relus : facilités de crédit et de garantie, obligations d'achat, passifs sur contrats et carnet de 2018 à 2023, tableau de l'intérêt variable de 2019 et de 2020. Après coup, la ligne de l'Item 15 de 2025, écrite avant que l'extracteur ne retienne d'abord la conclusion sur le contrôle interne de l'information financière, est relue : elle cite la même phrase que les sept autres exercices (1fb0b26). À l'intégration, la ligne de Koppelenweg I B.V. du 20-F de 2018 perd le traitement `vie_consolidated`, que le texte n'affirme pas (« a "variable interest entity" », sans dire qui la consolide) : `undetermined`, et les prêts bancaires de 47,1 M€ sont rendus à la société mère du bailleur ;
  - SK hynix : 100 blocs lus sur 100 de la liste `grp_skhy` (21 blocs de notes du 424B4, sa section des parties liées et 78 unités 6-K). 713 observations et 80 abstentions. Lignes principales :
    - parties liées et sociétés du groupe SK (note 31, Item 404) : ventes, achats, acquisitions d'actifs, créances, dettes, dividendes reçus et versés, emprunts, ligne à ligne pour chaque exercice et période présentés, en wons. 70 contreparties nommées, dont SK Holdings (redevance de la marque SK comprise), SK Square (dividendes versés), SK Telecom, SK Ecoplant (acquisitions d'actifs), ESSENCORE (ventes), HITECH Semiconductor (Wuxi) (services de back-end, marge garantie), SK Siltron et SK Airplus. Les sociétés du même groupe d'entreprises au sens de la loi coréenne sur la concurrence, qui ne sont pas des parties liées selon IAS 24, sont écrites comme telles. S'y ajoutent les bailleurs parties liées (HITECH, Hystars, SK Airplus, SK Broadband, SK Aircore) et la cession-bail de septembre 2023 à Clean Industrial REIT ;
    - participations : coentreprises et sociétés associées mises en équivalence (HITECH 45 %, SK hynix system ic (Wuxi) 49,79 %, SK China Company 11,87 %, SK South East Asia Investment 20 %, Wuxi Xinfa IC industry park 30 %, SiFive 6,84 %, fonds), avec la cession de 2024 et les dépréciations ; intérêt indirect dans KIOXIA Holdings par les véhicules BCPE Pangea ; Key Foundry, acquise en août 2022 (filiale) ;
    - financement : papier commercial (Shinhan Bank), emprunts dont le premier prêteur est nommé (Nonghyup Bank, MUFG, The Export-Import Bank of Korea), obligations en wons et internationales par série, obligations échangeables de 2030 (échangées au premier semestre 2026), lignes de crédit (Hana Bank, Agricultural Bank of China, Citibank), accords de financement des fournisseurs (736 236 M₩ au 30 juin 2026), swaps (Korea Development Bank, Shinhan Bank, Woori Bank), clause financière des obligations en wons (endettement d'au plus 500 %), actifs nantis, émission d'ADS du 14 juillet 2026 (26 507,1 M$) ;
    - garanties et engagements : Hystars Semiconductor (Wuxi) (701 M de yuans garantis envers Wuxi Xinfa Group au 2025-12-31, 566 M au 30 juin 2026 ; emprunts de 163 897 M₩ envers elle au 2024-12-31) ; Département du Commerce des États-Unis (accord de financement direct de West Lafayette, garantie de 1 028 M$) ; dépôts de garantie locatifs (71 M$, 12 M PLN) ; engagements d'investissement ; seconde réalisation de l'achat de l'activité NAND d'Intel (mars 2025, 3 079 783 M₩) ; licence croisée avec Rambus (2013 à 2034) ;
  - Samsung, piste des non-déposants : 246 blocs lus sur 246 de la liste `nf_samsung`. Ce sont 181 notes, 59 en-têtes de pièces EX-10 et les corps de 6 pièces, ajoutés au catalogue et à la liste après lecture de leur en-tête (`nf_discovery body`, sans requête, 296 100 caractères) : les accords transactionnels de Rambus de 2013 avec SK hynix et avec Micron, chacun dans trois dépôts. 58 observations dans 30 blocs et 216 abstentions (198 hors champ, 18 doublons). Lignes principales :
    - licences : Netlist (licence croisée et accord transactionnel d'août 2026 avec Samsung Electronics Co., Ltd. ; JDLA de 2015, avec l'obligation d'approvisionnement de Samsung) ; Immersion (redevances de 2012 à 2016 ; sentence de 7 841 324 165 ₩ payée le 22 avril 2019 et remboursement de 6 088 855 388 ₩ en mars 2022, lignes sans famille) ; InterDigital (licence de 2023) ; Network-1 (licence de 2015) ; Rambus (parties des accords de 2010 avec Samsung et de 2013 avec SK hynix et Micron, et redevances de 240 M$ sur cinq ans dues par SK hynix, section 2.1 du corps) ; TiVo (Samsung Electronics à 10 % du revenu de 2016) ;
    - fourniture : engagements d'achat de DISH envers Samsung ; GCL Global (NVIDIA et Samsung fournisseurs) ;
    - financement : prêts de Samsung Life Insurance à KEPCO (actifs nantis) ; valeurs comptables de deux fonds au nom de Samsung chez Shinhan Financial Group, dont le rattachement se décide à l'intégration, par extrait (point 6) : Samsung SRA Real Estate Professional Private 45 (de 2020 à 2025) et Samsung-dunamu Innovative IT Technology Investment Trust No. 1 (de 2023 à 2025) ;
    - abstentions : litiges de brevets, verdicts sans flux constaté (Netlist, Qualcomm, Network-1, VoIP-Pal, Straight Path, Patriot Scientific, Pendrell, InterDigital de 2016 à 2019) ; Samsung cité comme plateforme, marque ou appareil (QVC, CuriosityStream, Kartoon Studios, Genius Brands, FreeCast, Socket Mobile, Barnes & Noble, EchoStar) ; états des placements des plans 11-K ; en-têtes sans Samsung ni groupe de la liste parmi les parties. Le corps de l'accord de Rambus avec Micron renvoie le paiement au contrat de licence, incorporé par renvoi au 10-K de 2013 : aucun montant, abstention ;
  - corrections pendant la lecture de Samsung (D-0020), chacune vérifiée à blanc sur toute la liste avant la reprise :
    - sociétés associées de Shinhan : chaque note porte trois tableaux de sept cellules par fonds (variation, données financières résumées, rapprochement). La première version, qui comptait les rangées, ne donnait rien pour cinq 20-F et datait de 2019, dans le sixième, la rangée de rapprochement de 2020. La valeur se lit désormais sur le tableau de variation, repéré par sa ligne d'année et son en-tête ; une rangée n'est retenue que si solde d'ouverture et mouvements donnent le solde de clôture. Six blocs relus ;
    - notes des abstentions : la note se choisit phrase par phrase (Samsung partie à un litige, ou cité comme plateforme ou appareil), non plus par déclarant. 14 blocs relus, le code d'abstention ne changeant pas : InterDigital de 2016 à 2019, Headwater et Morris Routing chez EchoStar et DISH ;
    - corps de pièces : la règle de D-0044 (point 5 ; point 16 ci-dessus) ouvre les corps des deux accords transactionnels de Rambus dont l'en-tête montre SK hynix et Micron pour parties. Ils sont lus après les 240 blocs (032fe29). Les versions de 2021 sont identiques à celles du 10-K de 2024, aux renvois, tirets et séparateurs de cellules près : abstentions `duplicate_of_other_block` ;
  - incident relevé : l'état de lecture d'une liste (`reading_state_<liste>.json`) garde le dernier morceau servi d'un bloc long. Après une passe à blanc ou une boucle interrompue, `next` reprend à ce morceau, et la couture du bloc n'en garde que celui-là. Deux blocs de Shinhan ont ainsi d'abord été écrits en abstention, puis relus après remise à zéro de l'état. Règle de conduite : remettre l'état à zéro après toute passe à blanc ou interruption, avant de servir de nouveau ;
  - contrôle de lecture, après coup, sur les trois listes : extraction à blanc sur chaque bloc entier rendu par le lecteur (sans morceaux ni couture), comparée aux lignes écrites :
    - Samsung : 246 blocs (25 en plusieurs morceaux), aucun écart ;
    - SK hynix : 100 blocs, aucun écart ;
    - ASML : 183 blocs (10 en plusieurs morceaux), deux écarts, tous deux venus d'un extracteur modifié en cours de lecture, sur des blocs d'un seul morceau. L'un est l'Item 15 de 2025, relu. L'autre est le tableau de l'intérêt variable au 2018-12-31 de la note des participations du 20-F de 2018 : l'extracteur actuel le répéterait, alors qu'un autre bloc de la même pièce (0000937966-19-000007) l'a déjà écrit. Il est laissé sans doublon ;
  - données personnelles (point 11) : aucune personne physique n'est contrepartie ; aucune citation ni note ne reprend un nom de personne physique (contrôle par motif sur les 529 fichiers des trois listes). Les signataires et les avocats des accords de Rambus (blocs de signature, formulaires de désistement) sont écartés.

  (18) Intégration (2026-10-19), trente-deux groupes et quatre non-déposants, vue `as_known` :
  - inventaire de D-0050 (point 6), après la lecture de chaque groupe : noms à forme juridique des lignes valides, présents dans un bloc lu du groupe et non confirmés : ASML 11 (2 avec une phrase à terme de filiale), SK hynix 56 (11). Chaque phrase a été relue par l'exécutant. Restent des entités propres :
    - les sociétés du groupe SK (SK Holdings, SK Square, SK Telecom…), parties liées de SK hynix sans en être des filiales ;
    - ses coentreprises : HITECH Semiconductor (Wuxi), SK hynix system ic (Wuxi) et Hystars, filiale de cette dernière ;
    - Carl Zeiss SMT Holding GmbH & Co. KG, mise en équivalence (« we are not the primary beneficiary of the VIE ») ;
  - rattachements par extrait (`config.yaml`), chacun vérifié mot pour mot dans un bloc lu et sans nom de personne physique :
    - SK hynix : SK hynix America Inc. (« SK hynix America Inc. and other sales subsidiaries », rapport semestriel au 30 juin 2026, 6-K). Restent des entités propres :
      - Key Foundry Co., Ltd. : son acquisition à 100 % n'est datée qu'au mois (« August 2022 »), et une entité acquise n'entre qu'à une date de réalisation établie (D-0050, point 5) ;
      - les autres entités de l'en-tête de l'accord avec Rambus (Hynix Semiconductor Manufacturing America Inc., SK hynix U.K. Ltd., SK hynix Deutschland, GmbH) et celles de Micron dans l'accord de 2013 : une liste de noms sans lien dit ne suffit pas (D-0050, point 4) ;
    - Samsung (règles A et B de D-0044, point 7 ; point 6) :
      - Samsung Electronics Co., Ltd., tête du groupe (`parent`) ;
      - l'alias « Samsung » du groupe (« Samsung Electronics Co., Ltd. ("Samsung") » chez Netlist, Straight Path et Network-1) ;
      - Samsung Electronics America, Inc., Samsung Semiconductor, Inc. et Samsung Austin Semiconductor, L.P., désignées avec la tête par le terme défini « Samsung » (accord de Rambus de 2010, Netlist), en `undetermined` ;
      - la graphie « Samsung Electronics Co. » d'Immersion, en alias de la tête.

      Restent hors du groupe : Samsung Life Insurance, société du nom non consolidée par Samsung Electronics (point 2), et les deux fonds au nom de Samsung de Shinhan Financial Group, qu'aucun extrait ne rattache ;
    - alias (D-0021) :
      - « Nikon » (glossaire du rapport statutaire d'ASML de 2025) ;
      - « U.S. Department of Commerce » (8-K d'Intel du 25 novembre 2024 ; « DOC » est déjà l'alias de United States Department of Commerce) ;
      - « ASML Holding N.V. », graphie de la tête « ASML HOLDING NV » d'EDGAR (rapport statutaire d'ASML, 6-K du 25 février 2026 ; le message du commit 0557be7 le date à tort du 11 février). L'alias « ASML » de D-0056 est ramené à cette tête ;
    - entités propres sans forme juridique (18), chacune avec son extrait :
      - neuf établissements financiers de SK hynix : Hana Bank, Agricultural Bank of China, Citibank, Shinhan Bank, Nonghyup Bank, MUFG, The Export-Import Bank of Korea, Korea Development Bank et Woori Bank ;
      - deux fonds mis en équivalence par SK hynix, TCL Fund, SystemIC Solution et Wuxi Taiji Industry ;
      - Mistral AI (Mistral AI SAS selon le glossaire d'ASML) ;
      - Samsung Life Insurance et les deux fonds au nom de Samsung ;
    - reste en attente « HITECH Semiconductor », nom court de l'Item 404, faute d'une définition qui le relie à HITECH Semiconductor (Wuxi) Co., Ltd. Une ligne est concernée ; elle porte la même clé d'instrument que la participation ;
  - code, avec six tests (`test_entities_suffix`, `test_lender_measures`, `test_fsignals`) :
    - formes juridiques allemandes « KG » et « KGaA » (`entities.LEGAL_SUFFIX`). Carl Zeiss SMT Holding GmbH & Co. KG (113 lignes d'ASML) n'était qu'un nom en attente ; c'est le seul nom du corpus de cette forme ;
    - mesures des BDC : une valeur vide ou illisible du coût, de la juste valeur, du principal ou d'un taux compte comme non balisée. Le premier réassemblage s'arrêtait sur quatre positions de Carlyle Secured Lending sur Barnes & Noble, Inc., au taux capitalisé vide ;
    - signaux d'un groupe sans aucun rapport périodique (SK hynix) : le masque des rapports du trimestre est forcé en booléen (`fsignals.reports_by_quarter`) ;
  - premier réassemblage : observations 26 003 → 27 671 (les 1 668 lignes des trois listes sont valides), entités 2 755 → 3 048, liens 9 549 → 10 623, faits 1 549 934 → 1 580 920. Il a montré que « ASML Holding N.V. » (normalisé « asml holding n v ») ne rejoignait pas la tête « ASML HOLDING NV » : les lignes d'Intel et de TSMC qui nomment ASML restaient hors du groupe. L'alias ci-dessus l'a corrigé avant l'extraction des BDC et le second réassemblage ;
  - arêtes au dernier réassemblage :
    - ASML 250 (201 à montant ; aucune interne ni vers un nom en attente) ; SK hynix 630 (562 ; 2 vers un nom en attente) ; Samsung 21 (1) ;
    - entre groupes suivis : Intel et ASML 5 (participation vendue en 2019), TSMC et ASML 1 (financement de la R&D d'ASML de 2013 à 2017), Intel et SK hynix 8 (cession de l'activité NAND) ;
    - vers Samsung : Rambus, Netlist, Immersion, InterDigital, Network-1, TiVo, DISH et GCL Global ;
    - autres liens de la piste : Rambus et SK hynix (redevances de 240 M$ de l'accord de 2013), Rambus et Micron (accord de 2013), NVIDIA et GCL Global (fournisseur nommé) ;
  - BDC Data Sets : extraction refaite après le premier réassemblage (D-0043, point 14), 3 057 432 lignes de positions (3 054 099 avant) dans 2 100 dépôts. Faits de BDC rattachés : 3 405 (3 238), dans 435 dépôts de 60 fonds (419, 59). Les nouveaux émetteurs sont Barnes & Noble Inc, JPMorgan Chase & Co, Rackspace Technology, Inc., Snowflake Inc. et XPLR Infrastructure, LP, déposants de blocs lus de la piste de Samsung (entités de leur dénomination EDGAR, D-0036, point 10). Aucune position ne porte sur ASML, SK hynix ou Samsung ;
  - rendus : documents 23 526 (22 550), faits 1 580 920 (1 549 934), observations 27 671 (26 003), entités 3 047 (2 755), liens 10 623 (9 549), mesures 169 094 (157 624), contrôles 69 943, exclusions 30 126 (26 921) ; 11 527 nombres publiés (10 931). Exclusions :
    - `not_processed` 27 154 (23 979) : 949 fenêtres 6-K au-delà du plafond (ASML 915, SK hynix 34) et 2 243 unités de la piste de Samsung (2 165 hors de la règle de lecture, 78 au-delà du plafond) ; 17 unités de SoftBank en sortent ;
    - `submitted_draft` 19 (15) : les quatre DRS de SK hynix ;
    - `history_left_censored` 10 (9) : SK hynix ;
  - annexe F : 398 événements des groupes, inchangés. ASML et SK hynix n'ont que des cellules annuelles (point 12) ;
  - paires : 233 (186), dont 47 d'ASML et de SK hynix. Parmi elles, Intel → ASML et Intel → SK hynix remplacent les paires d'Intel vers « ASML Holding N.V. » et « SK hynix Inc. ». Deux autres viennent de la piste de Samsung :
    - NVIDIA → GCL Global Holdings Ltd ;
    - Apollo → Morgan Stanley : « Morgan Stanley », en attente jusque-là dans les lignes d'Apollo, se résout désormais en le déposant MORGAN STANLEY, dont le 11-K a été lu.

    Conclusions : causalité non établie 155 (141), achats réciproques seulement 44 (17), relation commerciale doublée d'un financement 26 (20), dépendance documentée 8 (8). Paires à financement documenté : 83 (69). Les quatorze nouvelles sont ASML → Carl Zeiss SMT GmbH, → Carl Zeiss SMT Holding GmbH & Co. KG et → Mistral AI, dix paires de SK hynix (HITECH, SK hynix system ic (Wuxi), SK China Company, sociétés associées et fonds, véhicules BCPE Pangea) et Apollo → Morgan Stanley. Intel → ASML, déjà financée sous « ASML Holding N.V. » (27 trimestres), n'est que renommée ;
  - cycles (E.6) : 102 (69), dont 97 de longueur 2. Les nouveaux :
    - ASML avec Carl Zeiss SMT GmbH et avec Carl Zeiss SMT Holding GmbH & Co. KG (relation commerciale doublée d'un financement) ;
    - SK hynix avec 26 sociétés du groupe SK et parties liées (achats réciproques seulement) ;
    - quatre relations commerciales doublées d'un financement : HITECH, Hystars, SK China Company, SK hynix system ic (Wuxi) ;
    - Intel → SK hynix → United States Department of Commerce → Intel (longueur 3, causalité non établie).

    Intel ↔ SK hynix remplace Intel ↔ « SK hynix Inc. » ;
  - E.7 : 164 issues (136), dont 57 % indéterminées au point de tête ;
  - contrôles, vue `as_known` : `mismatch` 1 833 (1 826), `not_testable` 1 333 (1 265), `ok` 29 886 (29 579), `tautological` 1 393 (1 383) ;
  - tests unitaires : 162, tous passés.

- **D-0058 — SoftBank approfondi : six volets, tous sur EDGAR. Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-19 : « Je veux tout creuser ». Elle répond au remue-méninges demandé le même jour (« Tu penses qu'il y a moyen de récupérer beaucoup plus d'informations intéressantes sur Softbank en étant astucieux et malin étant donné que ça a l'air d'être un acteur majeur de notre modèle ? Reste en mode brainstorming »). Ce remue-méninges proposait sept volets. Avant toute requête, l'utilisateur a tranché deux questions :
  - EDINET et TDnet, où SoftBank Group Corp. dépose ses comptes au Japon : « Rester sur EDGAR ». Ce volet est écarté. §2.6 (« Seul EDGAR fait foi ») et §9.5 (User-Agent envoyé aux seuls hôtes de la SEC) ne changent pas ;
  - Arm Holdings plc : « Filiale de SoftBank ». Arm entre au groupe `NF:SOFTBANK` par un extrait de ses propres dépôts. Ses notes et sa section des parties liées se lisent comme texte de ce groupe. Ses comptes n'entrent pas au modèle : ni faits, ni séries, ni signaux.

  Lecture séquentielle par l'exécutant, sans sous-agent. L'as_of reste le 2026-10-07 (D-0048, point 2).

  (2) État de départ, relevé sans aucune requête dans les tables du commit 9b5625e et dans le cache :
  - `NF:SOFTBANK` compte 13 entités et 48 arêtes, dont 21 à montant. Quatre seulement vont à un groupe ou à un laboratoire : Cipher 2, Intel 1, OpenAI 1. Les autres vont à des contreparties propres : WeWork 14, GM 9, Sprint 6, Guardant Health 3, AeroVironment 3, Moatable, Uber… ;
  - 160 lignes lues nomment SoftBank, l'un de ses véhicules ou l'une de ses sociétés, dont 130 observations. Restent hors du groupe, faute d'extrait :
    - « SoftBank Group » chez Intel (2,0 Md$ d'actions, accord du 18 août 2025) ;
    - Ampere Computing LLC et Ampere Computing Holdings LLC chez Oracle (24 observations, circulaires de 2018 à 2025) ;
    - « SoftBank Vision Fund II » et SVF II Finco Cayman L.P. chez Apollo (titres adossés d'investment grade : 2 116 M$ au 31 mars 2026) ;
    - SB Energy, Inc., SoftBank Vision Fund (AIV M1) L.P., « SVF II », « Softbank Vision fund », Softbank Robotics Singapore Pte Ltd ;
  - piste des non-déposants (D-0044, D-0054, D-0057) : 3 717 unités, dont 76 de SoftBank, toutes déjà lues ; 1 126 unités qui nomment SoftBank sont hors de la règle de lecture ;
  - liste des noms d'EDGAR du 2026-10-09, déjà en cache. Elle donne les CIK suivants :
    - SoftBank Group Corp. (1065521), SoftBank Corp. (1794354), SoftBank Group Capital Ltd (1755163) ;
    - cinq fonds : SoftBank Vision Fund L.P. (1699940), (AIV M1) L.P. (1755143), (AIV M2) L.P. (1805808), (AIV S1) L.P. (1776222), SoftBank Vision Fund II-2 L.P. (1787613) ;
    - leurs gérants, SB Investment Advisers (UK, US et Japon) et SB Global Advisers ; SB Management Ltd et SB Northstar GP ;
    - SB Energy, Inc. (2133037), Arm Holdings plc (1973239) et DigitalBridge Group, Inc. (1679688). L'ancienne Arm Holdings plc (1057997) a cessé de déposer avant le début de lecture.

    Aucune de leurs submissions n'est en cache ;
  - vérification faite avant d'écrire cette décision, dans les dépôts d'Oracle déjà en cache : le 10-Q du 11 mars 2026 écrit « On November 25, 2025, SoftBank Group Corp. acquired all of the equity interests of Ampere ». Ce paragraphe n'appartient à aucun bloc lu, et le catalogue du groupe n'a retenu de ce 10-Q que quatre notes. Il ne vaut pas extrait tant qu'il n'est pas lu (volet A) ;
  - volume compté sans lecture : 600 documents en cache nomment un terme de la famille SoftBank. « SoftBank » seul apparaît dans 3 409 paragraphes, dont 98 dans un bloc lu. Dans les documents des groupes de `config.yaml`, environ 330 paragraphes, chez Cipher, NVIDIA, Oracle, Marvell, AMD, Intel, Apollo, TSMC, ASML et quelques autres. Le reste vient des pièces de tiers tirées par la piste (WeWork, GM, T-Mobile, Sprint, SB Energy…), dont les corps suivent la règle de D-0044, point 5.

  (3) Volet A, le corpus des groupes déjà en cache. Aucune requête.
  - Documents : documents principaux et pièces, en HTML ou en texte, déposés par un groupe de `config.yaml` du 2017-01-29 (début du texte, `discovery.period_start`) à l'as_of.
  - Termes qualifiants, en mots entiers :
    - « SoftBank », en toutes casses ;
    - les noms des entités confirmées du groupe : « Star Beacon », « Stellar Beacon », « SB Northstar », « SVF Yellow », « SVF II Energy », « SB Energy », « Brightstar US » ;
    - les noms de sociétés et de véhicules que des lignes lues nomment sans rattachement : « SVF II », « SVF Holdco », « SVF Endurance », « HAPSMobile », « Ampere Computing », « Graphcore », « Arm Holdings », « Arm Limited », « Arm Ltd ». Casse exacte, ou capitales pour Arm (« ARM Holdings ») ;
    - « Stargate », en casse exacte.

    Sont seulement comptés, sans qualifier : « Arm » seul (l'architecture), « Ampere » seul (l'architecture de processeurs graphiques de NVIDIA), « SVF » seul (Apollo SVF Management, sans lien), « SBG » et « Vision Fund ». Un terme ne qualifie jamais un document dont il est le nom du déposant (D-0046, point 9).
  - Unités : les fenêtres du bloc `montages` (D-0046, points 4, 8 et 9) : le paragraphe qualifiant, les deux qui le précèdent et les deux qui le suivent, fondues quand elles se chevauchent. Une unité par fenêtre.
  - Ne sont pas lues, et sont comptées :
    - une fenêtre dont chaque paragraphe qualifiant figure déjà, mot pour mot aux blancs près, dans un bloc lu du même dépôt ;
    - une fenêtre dont chaque paragraphe qualifiant se trouve dans la section des facteurs de risque (`out_of_scope` ; §14 : jamais dans un facteur de risque). La section va du titre « Risk Factors » (Item 1A, ou titre du prospectus) au titre majeur suivant ; la plus longue est retenue, ce qui écarte la table des matières ;
    - un texte identique à une unité déjà retenue.
  - Ordre : du dépôt le plus récent au plus ancien. Plafond de 300 unités ; au-delà, `not_processed`, et le rendement est présenté avant d'aller plus loin.
  - Une unité appartient au groupe du déposant (perspective `reporting_entity`), comme tout bloc de ce groupe.
  - Code : le bloc `montages` reçoit un montage de corpus, `softbank_corpus`, sans recherche ni tirage. Les documents viennent de la table `documents`, et trois options s'ajoutent : `skip_read`, `skip_risk_factors` et l'ordre `recent_first`. Les montages existants ne changent pas.

  (4) Volet B, les dépôts EDGAR des entités de SoftBank.
  - CIK : ceux dont la dénomination EDGAR contient « SoftBank » (hors eSoftBank.com, sans lien), ceux des véhicules et des gérants du point 2, et les déclarants conjoints que les dépôts lus nomment comme personnes déclarantes d'une 13D ou d'une 13G.
  - Phase 0 : submissions complètes, toutes les pages de `filings.files` lues sans filtre de date (§9.4). Les formulaires se comptent ici avant toute lecture.
  - Unités, dans la période du volet A :
    - Schedules 13D et leurs amendements : le document principal, Items 2 à 7, coupé avant les annexes qui listent les administrateurs et les dirigeants, et avant les signatures. Les pièces EX-99 se lisent par leur en-tête, et le corps selon la règle de D-0044, point 5 ;
    - Schedules 13G et leurs amendements : Items 1 à 4 et notes, mêmes coupes ;
    - formulaires 3, 4 et 5 : seulement si l'émetteur est un groupe de `config.yaml`, un laboratoire ou une entité de SoftBank (Arm, SB Energy). On lit la table des transactions et les notes ; les autres sont comptés `out_of_scope` ;
    - 13F-HR : par dépôt, la page de garde et les lignes de la table d'information dont l'émetteur est un groupe de `config.yaml` ou une entité de SoftBank ; les autres lignes sont comptées ;
    - Form D : par le bloc `form_d`, en émetteur du périmètre (`issuer_is_subject` vrai), si l'émetteur est une entité du groupe au registre. Aucun nom de personne liée n'est lu ;
    - autres formulaires (425, SC TO, 144, F-6, CORRESP…) : comptés, non lus.
  - Ordre : émetteurs du modèle d'abord (groupes, laboratoires, entités de SoftBank), puis les autres ; du plus récent au plus ancien dans chaque classe. Un texte identique se lit une fois. Plafond de 200 unités.

  (5) Volet C, les déposants contrôlés par SoftBank, lus comme texte du groupe.
  - SB Energy, Inc. (2133037). Son dernier document d'enregistrement avant l'as_of (le 424B4 s'il existe, sinon le dernier S-1/A) entre dans `discovery.non_filer.own_filings`, avec les unités du S-1 de Nscale (D-0054, point 13) :
    - en-têtes des EX-10, corps selon la règle ;
    - Item 404 ;
    - notes des états annuels audités et des états intermédiaires ;
    - liste des filiales.

    Ses rapports périodiques déposés avant l'as_of, s'il y en a, se lisent par leurs notes. Les corps déjà lus en D-0044 ne se relisent pas. Le document est celui d'une filiale, non de la tête : SB Energy, Inc. n'entre au groupe que par un extrait (point 8).
  - Arm Holdings plc (1973239). Rapports périodiques déposés depuis son introduction en bourse jusqu'à l'as_of : 10-K et 10-Q, ou 20-F et 6-K, selon la phase 0. Unités :
    - toutes les notes du dernier rapport annuel et des rapports trimestriels qui le suivent ;
    - dans les rapports antérieurs, les notes des parties liées, des participations, des engagements, de la dette, des baux, du revenu et des secteurs ;
    - la section des parties liées (Item 13 ou Item 7.B) et la liste des filiales (EX-21) du dernier rapport annuel ;
    - 8-K items 1.01, 2.01, 2.03 et 8.01. Si Arm dépose des 6-K, ce sont les unités de D-0048 (lexique d'ensemble, plafond de 80).

    Les comptes d'Arm restent hors du modèle (point 1).
  - DigitalBridge Group, Inc. (1679688). Si la phase 0 montre l'acquisition par SoftBank réalisée avant l'as_of (8-K item 2.01, 3.01 ou 5.01, Form 25), on lit les items du 8-K de réalisation et l'en-tête de la convention de fusion. DigitalBridge entre alors au groupe à la date citée (D-0050, point 5). Sinon rien ne se lit : un accord non réalisé est une annonce.
  - Si un autre déposant de SoftBank a des rapports périodiques, il se lit comme Arm ; la règle est revue ici avant toute lecture.

  (6) Volet D, la piste des non-déposants élargie. Il vient après l'intégration des entités des volets A à C et E.
  - Termes : les noms distinctifs des entités rattachées à `NF:SOFTBANK` à cette date, en mots entiers et en casse exacte, avec leurs dates d'entrée et de sortie, comme dans `discovery.lexicon.confirmed`. Jamais un mot générique : « Arm », « Ampere », « SVF », « Vision Fund », « SBG ». Le lexique ne s'enrichit que d'entités confirmées (§14).
  - Sources : les 47 archives des Notes Data Sets, retirées et scannées avec le lexique d'ensemble enrichi ; recherche plein texte de chaque nouveau terme sur les formulaires racines des EX-10 (D-0044, point 4).
  - Candidats, classement et règle de lecture (R1, R2) : ceux de D-0044, point 5. Les unités nouvelles, que nul terme antérieur ne faisait naître, forment une file propre, plafonnée à 300 unités. L'état des unités existantes se garde sous leur clé, et rien ne se relit.

  (7) Volet E, le montage Stargate (bloc `montages`, `stargate`).
  - Période : du 2025-01-01 à l'as_of.
  - Requêtes de la recherche plein texte, tous formulaires : « "Stargate" "OpenAI" », « "Stargate" "SoftBank" », « "Stargate" "Oracle" », « "Stargate" "data center" ».
  - Terme qualifiant : « Stargate », en casse exacte. Les relevés de portefeuille sont comptés, non lus (D-0046, point 8). Les Form D sont écartés : ils relèvent du bloc `form_d`.
  - Plafond de 60 fenêtres ; un texte distinct se lit une fois ; du plus récent au plus ancien.
  - Les dix-sept Form D vérifiés de véhicules au nom de Stargate (Blue Owl GP Stakes Stargate, Stargate Crypto Capital Fund, séries de Wefunds) ne changent pas. Stargate n'est ni un laboratoire ni un groupe non déposant : aucun de ces Form D ne mesure une exposition (D-0041).

  (8) Volet F, un signal de crédit sur les obligations de SoftBank (Form N-PORT Data Sets).
  - Statut : la source est EDGAR, publiée par la SEC. La mesure est d'une sorte nouvelle : une valorisation de marché déclarée par des fonds, hors du cadre comptable et hors des blocs que §14 énumère. C'est une décision de l'exécutant, prise dans le mandat de l'utilisateur ; le remue-méninges la présentait comme une mesure à décider. Le retrait revient à supprimer la mesure et ses extraits.
  - Archives : archives trimestrielles des Form N-PORT Data Sets, de la première de la période à la dernière avant l'as_of, listées par la page des jeux de données, tirée une fois et gardée en cache (comme en D-0036). Chacune est tirée par le client unique, scannée dans un processus à part, puis effacée.
  - Lignes gardées : positions dont l'émetteur est une entité de SoftBank, c'est-à-dire un nom d'émetteur qui contient « SOFTBANK », ou un LEI relevé avec un tel nom dans les archives (jamais supposé). On garde aussi leurs identifiants, leurs caractéristiques de titre de dette, et le dépôt et la série de chaque fonds. Le tout va sous `cache/datasets/nport/{archive}/softbank/`. Les colonnes se lisent dans la description publiée avec les archives, vérifiée avant tout calcul.
  - Mesure `nport_price_to_par`, par titre (ISIN, à défaut CUSIP) et par fin de trimestre déclarée : somme des valeurs déclarées, dans la monnaie du titre, divisée par la somme des nominaux (unité « PA »). Elle porte sur les positions en titres de dette des séries de fonds distinctes, au dernier dépôt de chaque série pour cette date ; un amendement remplace le dépôt. On publie aussi le nombre de séries et le nominal détenu.
  - C'est une valorisation déclarée par des tiers (perspective `counterparty`), jamais une probabilité de défaut ni un fait comptable de SoftBank. Elle n'entre dans aucune mesure de financement ni dans l'annexe F ; c'est une série descriptive du nœud `NF:SOFTBANK`.

  (9) Entités, à l'intégration et après la lecture :
  - appartenance au groupe par les règles A (lien affirmé) et B (désignation par un alias confirmé du groupe) de D-0044, point 7 ;
  - traitement `consolidated_subsidiary` seulement sur les mots de D-0050, point 4 (filiale, filiale à 100 %, consolidée). Sinon `undetermined` ;
  - une entité acquise entre à la date de réalisation citée par un extrait (D-0050, point 5) : Ampere, Graphcore, DigitalBridge. Une entité cédée sort à la date citée ;
  - Sprint (de 2013 à 2020) et Fortress (de 2017 à 2024) entrent au groupe avec leurs dates si un bloc lu affirme le contrôle de SoftBank. Sinon elles restent des contreparties propres (D-0044, point 7) ;
  - un alias (« SoftBank Group ») ne naît que d'un extrait qui le définit (D-0021).

  (10) Données personnelles (D-0051 ; D-0057, point 11) : aucune personne physique n'est contrepartie. Ne sont jamais repris :
  - les annexes des 13D et 13G qui listent administrateurs et dirigeants, et les signatures ;
  - les personnes liées des Form D ;
  - les noms des contrats de travail et des circulaires.

  Une personne physique déclarante d'une 13D ou d'une 13G n'est jamais ni contrepartie ni citée. C'est le cas du fondateur de SoftBank.

  (11) Réseau (§9.5) : un seul client et un seul User-Agent, envoyé aux seuls hôtes de la SEC ; 5 requêtes par seconde au plus ; jamais deux processus réseau à la fois ; pause d'au moins dix minutes après un 403 ; chaque requête au journal.

  (12) Ordre et commits :
  - la décision ;
  - la configuration et le code (montage de corpus et montage Stargate, unités des 13D, 13G, formulaires 3 à 5 et 13F, dépôts propres de SB Energy et d'Arm, bloc N-PORT), avec leurs tests ;
  - volet A : unités préparées, volume consigné ici avant toute lecture, lecture, commit ;
  - volets B et C : phase 0 (submissions), constats consignés ici et règles revues s'il le faut, pièces, unités, volume consigné, lecture, un commit par volet ;
  - volet E : recherche, pièces, unités, volume consigné, lecture, commit ;
  - premières entités par extrait (un commit), puis volet D : archives, recherche plein texte, unités, volume consigné, lecture, commit ;
  - volet F : archives, extraits, mesure et tests, commit ;
  - intégration : entités par extrait, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (13) Limites connues avant calcul :
  - SoftBank n'a pas de comptes au modèle. Le volet F est un signal de marché déclaré par des tiers ;
  - le volet A ne voit que le corpus déjà tiré : un document de groupe absent du cache n'est pas scanné ;
  - un paragraphe qui ne nomme Arm que par « Arm », ou Ampere que par « Ampere », n'est pas servi (point 3) ;
  - les volets B et C dépendent des constats de la phase 0, consignés ici avant toute lecture.

  (14) Volet A, volume avant lecture :
  - 4 218 documents des groupes dans la période, tous en cache. Le pré-filtre en retient 130 qui nomment un terme ;
  - 221 fenêtres : 34 dans la section des facteurs de risque (`out_of_scope`), 37 déjà dans un bloc lu du même dépôt, 150 à lire. Ces 150 fenêtres donnent 143 textes distincts, soit 377 713 caractères, sous le plafond de 300 ;
  - par groupe : NVIDIA 40, Oracle 35, AMD 14, TSMC 14, Intel 12, Marvell 10, Cipher 7, ASML 7, Core Scientific 2, IREN 2. Par formulaire : 10-K 43, 10-Q 38, DEF 14A 33, 6-K 22, 8-K 6, 20-F 1. Dépôts du 2017-05-03 au 2026-08-26 ;
  - les blocs des trois autres montages sont inchangés (mêmes clés de contenu) ;
  - code : `montages.corpus`, `risk_factor_span`, `read_texts` et `covered`, options du point 3, exclusions du montage de corpus. Cinq tests (`test_montages`). Liste de lecture `sb_corpus`, du dépôt le plus récent au plus ancien.

  (15) Volet A, lecture : 143 blocs lus, 159 lignes (48 observations, 111 abstentions), aucune rejetée. Faits nouveaux :
  - Ampere : SoftBank Group Corp. a acquis toutes les parts d'Ampere le 25 novembre 2025 (10-Q d'Oracle de décembre 2025 et de mars 2026, 10-K de 2026). Oracle a reçu 4,3 Md$ pour ses participations, sa dette et ses options d'achat. S'y ajoutent les valeurs comptables trimestrielles de 2024 et 2025, 90 M$ de dette convertible au premier trimestre de l'exercice 2026 et l'avenant du 5 mars 2024 ;
  - « SoftBank Group » : le glossaire du 10-Q d'Intel du troisième trimestre 2025 le définit comme SoftBank Group Corp. ;
  - SB Energy Corp. : contractant nommé des garanties de NVIDIA (105 Md$, PORTS Technology Campus, Ohio) ;
  - Arm :
    - TSMC : 1 961 milliers d'actions achetées 100 M$ en 2023, après une résolution du conseil (au plus 100 M$ au prix de l'introduction en bourse) ; 850 milliers revendues 101,5 M$ au premier trimestre 2024 ; juste valeur trimestrielle ;
    - Intel : investissement dans l'introduction en bourse, sans montant ;
    - NVIDIA : paiements d'avance de licences et de redevances d'Arm, 0,17 et 0,47 Md$ sur 20 ans, à la signature de l'accord de 2020 ; charge de résiliation de 1,35 Md$ ;
    - Marvell : bon de souscription de 9 millions d'actions au profit d'Arm Limited, règlement plafonné à 210 M$, accords de collaboration de 2018 et 2019 ;
    - AMD : licencié d'ARM Holdings ;
  - Cipher : exclusivité de SoftBank sur le site de Barber Lake jusqu'au 28 février 2025 ;
  - hors SoftBank, dans les mêmes fenêtres : achat par TSMC de 10 % d'IMS Nanofabrication à Intel (au plus 432,8 M$, résolution du conseil du 12 septembre 2023) ; participation de 15 % d'Oracle dans TikTok USDS Joint Venture LLC.

  Extraits pour l'intégration : la réalisation du rachat d'Ampere (10-K et 10-Q d'Oracle) ; l'alias « SoftBank Group » (glossaire d'Intel) ; « ARM Holdings plc, a publicly-traded semiconductor IP and software design company, now a wholly-owned subsidiary of the Softbank Group » (circulaires de Marvell de 2017 à 2023). Cette dernière phrase parle de la société ; le nom de la personne décrite n'est pas repris.

  Deux corrections pendant la lecture :
  - la charge de résiliation de NVIDIA, d'abord reprise à 1,4 Md$ (arrondi du 10-K de l'exercice 2025), ne l'est plus qu'une fois, à 1,35 Md$ (10-K de l'exercice 2023). La ligne arrondie devient une abstention ;
  - les montants cumulés depuis le début de l'exercice, déjà compris dans un total annuel lu (dette convertible d'Oracle dans Ampere, cession d'actions Arm par TSMC), ne sont pas repris, pour ne pas compter deux fois.

  (16) Volets B et C, constats de la phase 0 et règles précisées avant toute lecture :
  - submissions de 41 CIK lues le 2026-10-19 (41 requêtes), toutes complètes. 37 CIK propres, dont seize anciens véhicules de SoftBank Capital, de SoftBank Technology Ventures, de SoftBank America et de SoftBank Holdings, sans dépôt dans la période. Deux CIK ont aujourd'hui une autre dénomination EDGAR : MOBIUS TECHNOLOGY VENTURES VI LP (ex-SoftBank Technology Ventures VI) et SOFTBANK U S VENTURES VI L P, avec dix formulaires 3 et 4 jusqu'en février 2019 ;
  - 606 dépôts propres distincts dans la période, souvent conjoints à plusieurs entités :
    - 191 Schedules 13D et 13G, du 2017-02-14 au 2026-05-29 ;
    - 226 formulaires 3 et 4 ;
    - 112 13F-HR (SoftBank Group Corp. 57, SB Investment Advisers (UK) 40, SB Management 8, SB Global Advisers 7) ;
    - 43 13F-NT, 10 N-PX, 17 F-6, 2 CORRESP, un 424B3, un 144 ;
    - trois Form D de SoftBank Vision Fund L.P. ;
  - émetteurs visés, lus dans les en-têtes SGML (530 requêtes) : un seul 13G (Arm Holdings plc) et un seul formulaire 3 ou 4 (Arm) portent sur un émetteur du modèle. Les autres portent sur le portefeuille de SoftBank : T-Mobile 19, WeWork 12, Alibaba 11, Full Truck Alliance 8, Guardant Health 8, SoFi 7, Coupang, Compass, Roivant, Sprint, DoorDash, Uber… Les 225 autres formulaires 3 et 4 sont comptés `out_of_scope` (point 4). Les 191 13D et 13G tiennent sous le plafond de 200 ; Arm vient en tête, puis les autres du plus récent au plus ancien ;
  - SB Energy, Inc. : DRS du 2026-05-22 et deux DRS/A (soumis, non déposés, §2.1), S-1 du 2026-09-01, S-1/A du 2026-09-04 (pièces seulement) et S-1/A du 2026-09-21. Aucun 424B4 avant l'as_of. Le document d'enregistrement est donc le S-1 et ses deux amendements. On lit le prospectus du dernier S-1/A (Item 404 et notes), et les EX-10 et EX-21 des trois dépôts (texte identique lu une fois) ;
  - Arm Holdings plc : émetteur privé étranger. 20-F des exercices clos le 31 mars 2024, 2025 et 2026 (déposés le 2024-05-29, le 2025-05-28 et le 2026-05-26), 34 6-K du 2023-11-08 au 2026-09-18, 424B4 du 2023-09-14. Le point 5 s'applique dans sa branche 20-F et 6-K. Liste des filiales : pièce 8.1 du dernier 20-F. Amendement avant toute lecture : la section « Certain Relationships and Related Party Transactions » du 424B4 se lit aussi. Le premier 20-F ne couvre que l'exercice 2024, et le 424B4 est le seul document qui décrive les relations antérieures entre Arm et SoftBank (même règle que le S-1 de Nscale, D-0054, point 13) ;
  - DigitalBridge Group, Inc. : rachat réalisé avant l'as_of (Form 25 du 2026-09-22 ; 8-K du 2026-09-30, items 2.01, 3.01, 3.03, 5.01, 5.02 et 5.03 ; 15-12G du 2026-10-13, après l'as_of). Le point 5 s'applique : items du 8-K du 2026-09-30 et en-tête de la convention de fusion (pièce 2.1 du 8-K du 2025-12-30, item 1.01) ;
  - groupe des blocs des volets B et C :
    - un bloc des dépôts propres de SoftBank (13D, 13G, formulaires 3 et 4, 13F) appartient à `NF:SOFTBANK` (perspective `reporting_entity`) ;
    - un bloc de SB Energy, d'Arm ou de DigitalBridge appartient d'abord à son propre groupe de contrepartie (`CP:`). Ses lignes ne passent à `NF:SOFTBANK` qu'après le rattachement du déposant par extrait, avec son CIK et sa date d'entrée, par le mécanisme d'Athene Holding (D-0055, point 8). Ce n'est pas celui d'une tête de non-déposant (Nscale, D-0054, point 13).

  (17) Volets B et C, unités et volume, consignés avant toute lecture :
  - précisions de code, arrêtées avant toute lecture :
    - 13D : Items 2 à 7, de la première rubrique de ces items à la première annexe des administrateurs et des dirigeants ou aux signatures. La page de garde n'est pas lue. 13G : Items 1 à 4, coupés à l'Item 5. Ses notes sont les notes de bas de page de la page de garde, hors mentions types. Au format XML de 2025 : les éléments des mêmes items ; pour un 13G, les commentaires des personnes déclarantes, qui tiennent lieu de notes ; jamais les personnes autorisées ni les signatures. Le texte des 13D et des 13G passe ainsi de 2,2 à 1,0 million de caractères ;
    - le plafond de 200 compte toutes les unités du volet B, non les seuls 13D et 13G comme l'écrivait le point 16. Une unité est un dépôt : 13D ou 13G avec ses pièces EX-99, formulaire 3 ou 4, 13F. Un 13F réduit aux lignes d'émetteurs du modèle est de la première classe ;
    - première classe de l'ordre : groupes, laboratoires, Arm, SB Energy, DigitalBridge, et les deux entités de SoftBank que le point 9 nomme, Sprint et Fortress. Elles n'entrent pas au groupe pour autant (point 9). Les formulaires 3 et 4 s'en tiennent aux émetteurs que le point 4 énumère : les 23 formulaires sur Sprint restent `out_of_scope` ;
    - notes de SB Energy et d'Arm, découpées selon leurs propres titres (« Note N. » ; « N - Titre »). Un jeu se ferme aussi à l'item suivant d'un rapport annuel (Item 8.B, Item 9) et à la quatrième de couverture du prospectus. Les titres courants sont retirés. SB Energy : deux jeux de 21 notes, comptes annuels audités et comptes intermédiaires au 30 juin 2026. Arm : les 22 notes du 20-F de 2026, et six notes de chacun des deux 20-F antérieurs (revenu, baux, participations, engagements, parties liées, secteurs ; aucune note de dette) ;
    - section des parties liées du prospectus de SB Energy : du titre en capitales au titre suivant, hors table des matières (63 043 caractères) ;
    - DigitalBridge : la note introductive et les items du 8-K de réalisation, hors 9.01. Du 8-K de l'accord, seul l'en-tête de la convention de fusion (pièce 2.1) se lit ;
  - volet B, `NF:SOFTBANK` : 200 unités, 268 blocs, 961 280 caractères :
    - 148 13D et 13G (735 330 caractères), du 2017-02-17 au 2026-05-29, et 68 en-têtes de pièces EX-99 (198 798). Première classe : Arm 1, Sprint 5, Fortress 2 ;
    - un formulaire 4 sur Arm (2 956) ;
    - 51 13F (24 196), du 2018-02-15 au 2026-08-14 : 94 lignes d'émetteurs du modèle sur 1 453. NVIDIA 38, TSMC 10, Sprint 9, Amazon 5, Alphabet, Intel et Microsoft 4 chacun, Meta 3, Cipher et Oracle 2 chacun ;
    - non lus : 43 13D et 13G au-delà du plafond (`not_processed`), du 2017-02-14 au 2021-09-16 (T-Mobile 9, Guardant Health 8, Alibaba 5…) ; 225 formulaires 3 et 4 (Vir Biotechnology 59, Sprint 23, Lemonade 12…) et 61 13F sans ligne du modèle (`out_of_scope`) ; 74 autres formulaires comptés (13F-NT 43, F-6EF 12, N-PX 10, F-6 POS 5, CORRESP 2, un 424B3, un 144) ;
  - volet C, groupes de contrepartie des déposants : 209 blocs, 1 512 046 caractères :
    - SB Energy, 82 blocs (434 744) : 36 en-têtes d'EX-10, 3 listes de filiales, la section des parties liées, 42 notes ;
    - Arm, 119 blocs (1 050 610) : 34 notes, 4 sections des parties liées (Item 7.B des trois 20-F, 424B4), la pièce 8.1 et 80 fenêtres 6-K (691 531). Les 6-K donnent 539 fenêtres : 54 doublons, 405 au-delà du plafond (`not_processed`). Les 33 autres notes des 20-F antérieurs sont `out_of_scope` ;
    - DigitalBridge, 8 blocs (26 692) ;
  - en tout 477 blocs et 2 473 326 caractères. Lecture dans l'ordre du point 12 : volet B, puis volet C, un commit par volet. Code : `pipeline/sb_own.py` (`prepare`, `exclusions`), dix tests (`test_sb_own`).

  (18) Volet B, lecture, sans sous-agent (2026-10-19) :
  - deux corrections du catalogue, faites avant la lecture des blocs touchés :
    - une pièce EX-99 hors texte (PDF, image) ne forme plus de bloc. Les six pièces en cause sont les annexes des dirigeants de 13D/A de 2025 (point 10). Elles sont comptées `out_of_scope` (`exhibits_not_text`). Le volet B passe à 262 blocs ;
    - la coupe d'un 13D ne joue plus qu'après le dernier intitulé d'Item du périmètre. Une phrase de l'Item 2 qui renvoie à l'annexe (« Schedule A attached hereto sets forth… ») coupait le 13D d'EQRx du 2021-12-27 avant ses Items 3 à 7. C'est le seul bloc touché, et il n'était pas encore lu (2 265 puis 9 267 caractères). Un test de plus (`test_sb_own`, onze tests) ;
    - les volets B et C font désormais 471 blocs et 2 407 647 caractères, dont 895 601 pour le volet B ;
  - règles de codage, appliquées à tout le volet :
    - 13F : une ligne par ligne d'émetteur du modèle. La valeur est en milliers de dollars avant le 2023-01-03, en dollars ensuite ; elle est omise quand le nombre de titres déclaré est nul. Une arête de financement seulement si le nombre de titres est celui d'une opération primaire attestée ailleurs : Intel (86 956 522 actions, placement privé du 26 septembre 2025) et Cipher (10 438 413 actions, placement privé du 30 janvier 2025). Les autres positions (NVIDIA, TSMC, Oracle, Amazon, Alphabet, Microsoft, Meta, Sprint) n'ont pas d'origine écrite : lignes descriptives, sans arête (SPEC §3.1 et §3.2 (a)) ;
    - détentions, achats et ventes secondaires, échanges de titres lors d'un rapprochement, ventes à terme et options face à des contreparties non nommées : lignes descriptives, sans arête ;
    - opérations primaires (souscriptions, placements privés), obligations, convertibles et prêts : arêtes de financement. Indemnités et soutiens de crédit : `credit_support`. Bons de souscription remis à un client : `customer_consideration`. Aucun montant ne se calcule à partir d'un nombre d'actions et d'un prix (guide, §5) ;
    - extraits d'appartenance : rôle `filer_group`. Le traitement `consolidated_subsidiary` suit les mots de D-0050, point 4, et seulement si la chaîne remonte à SoftBank ou à une entité du groupe de D-0044. « Sole member », « sole owner », « sole shareholder », « general partner », « wholly owned by », « 100% equity interest », un gérant ou un AIFM donnent `undetermined`. Une entité n'est relevée qu'une fois ; un extrait plus fort, lu plus tard, s'ajoute (12 entités ont les deux) ;
    - accords de dépôt conjoint : abstention `boilerplate_no_event` ;
    - corps des pièces EX-99 : aucun n'est lu. Aucun des 62 en-têtes ne nomme un groupe du modèle, un laboratoire ou Stargate (D-0044, point 5) ; le contrôle est refait à la fin de la lecture ;
    - aucune personne physique n'est citée : administrateurs, dirigeants, comité d'investissement, fiducies de fondateurs, listes d'actionnaires bloqués ;
  - rendement : 262 blocs lus (148 13D et 13G, 62 en-têtes d'EX-99, 51 13F, un formulaire 4), 459 lignes (399 observations, 60 abstentions), aucune rejetée :
    - 46 arêtes : 37 de financement (16 en actions, 14 prêts et obligations, 7 convertibles), 7 de soutien de crédit, un engagement d'achat, une contrepartie remise à un client. 28 portent un montant ;
    - 112 extraits d'appartenance pour 96 entités : 40 `consolidated_subsidiary`, 72 `undetermined` ;
    - 241 lignes descriptives ;
  - faits principaux :
    - Sprint : contrôle de SoftBank entre 83,80 % et 84,85 % ; Starburst I et Galaxy Investment Holdings sont des filiales à 100 %. Bon de souscription exercé le 2018-07-10. Indemnité consentie à T-Mobile en 2020 ;
    - Fortress : filiale à 100 % de SB Foundation Holdings LP à partir du 2017-12-27 ;
    - WeWork :
      - soutien de crédit de SoftBank à une ligne de lettres de crédit de 1,75 Md$, pris en octobre 2019 et repris par SVF II (accord du 2019-12-27). Appel en garantie et lettre de règlement le 2023-10-30, fin le 2024-06-11 ;
      - échange de mai 2023 : obligations non garanties de 250 M$, 359,5 M$ et 1,04 Md$ ; nouvelles obligations de 187,5 M$ et 269,625 M$ ; tranche de premier rang à tirage différé jusqu'à 300 M$. Défaut des obligations PIK le 2023-10-02 ;
      - Junior TLC de 441,6 M$ le 2024-06-11 ; Secured NPA de 500 M$ en 2021 ;
    - Better : obligations relais de 650 M$ (2021-12-02), converties le 2023-08-22. Obligations convertibles de 528,6 M$. Échange du 2025-04-28 : 110 M$ en numéraire et 155 M$ d'obligations garanties de premier rang ;
    - Symbotic et GreenBox, le 2023-07-23 : contrat-cadre d'au moins 7,5 Md$ ; bon de 11 434 360 actions remis à Sunlight Investment Corp. ; souscription de 100 M$ ; engagements en capital de 3,2 Md$ et de 1,7 Md$ ;
    - Berkshire Grey : obligations de 60 M$ (2023-03-24) et de 12 M$ (2023-06-26) ; filiale à 100 % à partir du 2023-07-20 ;
    - SB Northstar : placement privé d'EQRx (41 250 000 actions à 10,00 $, le 2021-12-17) ; unités de Learn CW (100 M$, le 2021-10-13) et d'Aurora Acquisition Corp. (le 2021-03-08). SVF II : souscription de série D1 et placement privé d'Exscientia (2021) ;
    - T-Mobile : ventes à terme prépayées et prêt sur titres de Project 6 LLC (2022) ; options de Deutsche Telekom, réglées en actions DT en 2021 puis en numéraire en 2022 ; cessions de blocs en 2025. Toutes ces lignes sont descriptives ;
    - entités nouvelles : Skywalk Finance GK (filiale, 6,3 % d'Alibaba au 2021-12-31), Tsubasa Corporation (filiale à 100 %), SB WW Holdings (Cayman) Limited, et des véhicules du SoftBank Vision Fund (AIV S1, AIV M1, SVF GP (Jersey), XKI Subco, Oyster, Buzzard…).
  (19) Volet C, lecture, sans sous-agent (2026-10-19) :
  - ajouts et corrections, faits avant la lecture des blocs touchés :
    - deux corps d'EX-10 de SB Energy entrent au catalogue, juste après leur en-tête, car l'en-tête lu montre NVIDIA partie (D-0044, point 5) : l'accord d'achat d'actions de classe N du 2026-08-17 (pièce 10.28 du S-1, 44 627 caractères) et le modèle de garantie de valeur résiduelle (pièce 10.31 du S-1/A, 43 751 caractères). Volume consigné avant lecture : 88 378 caractères. Code : `sb_own.exhibit_body` et la constante `SBE_BODIES`, un test de plus (`test_sb_own`, douze tests). Les 471 autres blocs gardent leur clé. La liste du volet C passe à 211 blocs, dont six en-têtes d'EX-10 de SB Energy déjà lus en D-0044 ; volets B et C : 473 blocs, 2 496 025 caractères ;
    - la ligne de D-0044 sur les bons d'OpenAI (`sbenergy:openai_warrants`, bloc 3b1ce41b…, `financing` / `equity_primary`) devient descriptive. Selon la section des parties liées du S-1/A, ces bons sont une contrepartie remise au client (incitation, en réduction du revenu locatif) ; ils sont relevés en `customer_consideration` ;
    - une note sans appui est rendue neutre. La part du revenu d'Arm liée à Arm China en 2021 (424B4) disait « Arm China alors consolidée jusqu'au 28 mars 2022 ». Le prospectus est ambigu sur ce point ;
  - règles de codage, appliquées à tout le volet :
    - une citation ne traverse jamais des points de conduite de tableau. Une suite de quatre signes de ponctuation identiques ou plus fait boucler la recherche de la citation dans le fichier brut ; on cite donc après les points. L'aide de lecture le vérifie ; `textnorm` est inchangé ;
    - Arm : aucun signal tiré de ses comptes (point 1). La seule ligne de signal des blocs d'Arm (`pledged_assets`, 769 029 000 actions d'Arm nanties, soit 72,0 % au 2026-05-21) porte sur le crédit de SoftBank Group (`sbg:arm_share_backed_facility_2023`), pas sur les comptes d'Arm. Elle est gardée ;
    - les relations avec les actionnaires du groupe sont relevées et notées « interne au groupe » : contrat de conseil avec SoftBank, Acetone Limited, Kigen, Ampere après novembre 2025, apports de SBE Global ;
    - doublons : une valeur arrondie d'une section narrative (Item 7.B, rapport britannique en IFRS) et la valeur exacte d'une note ne fusionnent pas, car `same_measure` exige le même montant. Une seule ligne est gardée ; l'autre bloc reçoit une abstention `duplicate_of_other_block` ;
    - acquisitions : les achats de projets de SB Energy (acquisitions d'actifs, paiements à jalons) sont des arêtes commerciales. Les acquisitions d'entreprises (DreamBig par Arm, DigitalBridge par SoftBank) n'ont pas de famille : le prix payé aux vendeurs n'est pas une arête (guide, Items 2.01). La réalisation porte la ligne d'appartenance, datée ;
    - listes de filiales (pièce 21.1 de SB Energy ; pièce 8.1, note 41 et filiales dispensées d'audit du rapport britannique d'Arm) : seules les entités nommées dans une ligne lue entrent au groupe (D-0054, point 13). Arm, Inc., Apical Limited, Arm UK Holdings Limited et les autres ne sont pas rattachées ;
    - fenêtres des 6-K d'Arm : les annonces de tiers et les relations sans contrat ni montant ne sont pas reprises. Trois relations propres d'Arm, nommées, deviennent des lignes descriptives : Meta, partenaire principal et co-développeur de l'Arm AGI CPU ; TSMC, son fabricant ; OpenAI, client annoncé ;
    - aucune personne physique n'est citée : biographies, rémunérations, notifications et signatures sont écartées ;
  - rendement : 205 blocs lus (SB Energy 78, Arm 119, DigitalBridge 8 ; les six en-têtes lus en D-0044 ne sont pas relus), 550 lignes (390 observations, 160 abstentions), aucune rejetée :
    - 217 arêtes : 121 de financement, 61 commerciales, 31 de soutien de crédit, 4 contreparties remises à un client. 204 portent un montant ;
    - 84 extraits d'appartenance pour 82 dénominations, comptées par déposant (SB Energy 70, Arm 8, DigitalBridge 4 ; « the Company » une fois par déposant) : 63 `consolidated_subsidiary`, 8 `vie_consolidated`, 13 `undetermined` ;
    - 89 lignes descriptives, dont 3 signaux (deux sur la dette de SB Energy, un sur le crédit de SoftBank adossé aux actions d'Arm) ;
  - faits principaux :
    - SB Energy : apports de SoftBank de 3,2 Md$ à Energy Global ; billets intragroupe de SBE Global (709,5 M$ au 2026-06-30) ; bail Cosmos à un affilié de SoftBank (2,5 Md$) et garantie de SoftBank Group Capital Limited (2,905 Md$) ; actions privilégiées d'un affilié d'OpenAI dans Energy Global (500 M$, 2026-01-09) ; bons d'OpenAI (3,646 Md$ à l'émission, 5,5 Md$ au 2026-06-30) ; garantie de valeur résiduelle de NVIDIA (plafond de 105 Md$, 4,25 GW) avec exclusivité de l'architecture de NVIDIA pendant au moins 20 ans ; placement de classe N de NVIDIA (1,5 Md$, accord du 2026-08-17, caduc au 2027-05-15 sans introduction en bourse) et vente à terme prépayée (1,5 Md$ reçus le 2026-08-17) ; dette de projet et lignes de lettres de crédit, agents et arrangeurs bancaires nommés ;
    - Arm : filiale consolidée de SoftBank Group (environ 87 % indirects au 2026-03-31), mère directe Kronos II LLC. Crédit de 2022 de Kronos I (UK) Limited (8,5 Md$, agent J.P. Morgan SE), remboursé en septembre 2023 ; crédit de 2023 (8,5 Md$). Contrat de conseil avec SoftBank : 704,4 M$ de revenu sur l'exercice 2026 et 192,9 M$ au premier trimestre de l'exercice 2027 ; paiement fixe de 300 M$ en 2027. Revenu IPLA d'Arm China : de 474,2 M$ (exercice 2022) à 790,6 M$ (exercice 2026). Ampere : rachetée en totalité par SoftBank en novembre 2025, par une option d'achat sur la part d'Arm (143,4 M$) ; billet convertible de 29,0 M$ réglé 39,3 M$. DreamBig : accord d'octobre 2025 (environ 265,0 M$), réalisé le 2026-07-01. Cession secondaire de SoftBank lors de l'introduction en bourse (102 500 000 ADS à 51 $, le 2023-09-18) ;
    - DigitalBridge : fusion réalisée le 2026-09-30, avant l'as_of. DigitalBridge devient filiale à 100 % de Duncan Holdco III LLC, et filiale indirecte de Duncan Holdco II LLC et de Duncan Holdco LLC, détenue à 100 % par SoftBank Group Overseas GK. La contrepartie de 16,00 $ par action est financée par un engagement en fonds propres de SoftBank Group Overseas GK et par la trésorerie de DigitalBridge ;
    - entités nouvelles : Ampere (novembre 2025, `undetermined`), DreamBig Semiconductor, Inc. (2026-07-01, `undetermined`), DigitalBridge Group, Inc. et ses holdings Duncan (2026-09-30), Arm Limited, Arm France SAS, Arm Technology Israel Ltd., Acetone Limited, Kigen (UK) Limited, les filiales et entités à intérêts variables de SB Energy.
  (20) Volet E, précisions avant tout tirage (2026-10-19). Elles appliquent §14 et le point 7, sans en changer le périmètre :
  - le terme qualifiant « Stargate » (casse exacte) ne qualifie jamais une pièce d'un déposant dont le nom le porte (D-0046, point 9) : les véhicules au nom de Stargate sont des Form D, qui relèvent du bloc `form_d` ;
  - les Form D et Form D/A de la recherche sont comptés, non tirés (`count_only_forms`), et sortent en `out_of_scope`. Les relevés de portefeuille restent comptés, non lus (D-0046, point 8) ;
  - une fenêtre dont chaque paragraphe qualifiant est dans la section des facteurs de risque n'est pas servie (§14 : une mention n'y fait jamais une unité) ; elle sort en `out_of_scope`. Une fenêtre dont chaque paragraphe qualifiant figure déjà, mot pour mot, dans un bloc lu du même dépôt n'est pas servie non plus (un texte se lit une fois). Ce sont les options `skip_risk_factors` et `skip_read` du montage de corpus (point 3) ;
  - ordre : du dépôt le plus récent au plus ancien, plafond de 60 fenêtres distinctes. Au-delà, une fenêtre d'un dépôt d'un groupe suivi se lit par le catalogue du groupe (D-0053, point 7) ; les autres sortent en `not_processed` ;
  - code : `montages.prepare <montage>` prépare un seul montage, sans toucher aux blocs des autres (déjà lus) ; `count_only_forms` dans `fetch`. Deux tests de plus (`test_montages`).
  (21) Volet E, amendement et volume, après le premier décompte et avant toute lecture (2026-10-19) :
  - recherche (2025-01-01 à l'as_of) : 52, 26, 49 et 105 résultats pour les quatre requêtes, soit 232 résultats et 112 pièces distinctes. Aucun Form D. 17 résultats sont des relevés de portefeuille (N-CSRS 11, N-CSR 6), comptés et non lus ; 104 pièces sont tirées (96 requêtes, 8 pièces déjà en cache) ;
  - premier décompte : 112 fenêtres, 77 textes distincts, 60 blocs au plafond, 17 au-delà. Quinze fenêtres venaient de projets DRS et DRS/A (Nscale, DSNS Holdings, AI Infrastructure Acquisition Corp., Roth CH Holdings) ;
  - amendement, fondé sur les seuls formulaires : un DRS est soumis, pas déposé, et n'entre dans aucune mesure (SPEC §2.1, `submitted_draft`). Les neuf pièces DRS et DRS/A sont écartées (`exclude`) et sortent en `out_of_scope` ; la version publique déposée (S-1, F-1, 424B4) se lit. C'est la règle déjà suivie pour les DRS de SB Energy (point 5) ;
  - volume, avant lecture : 89 fenêtres dans 86 pièces, 58 textes distincts (31 doublons), 58 blocs issus de 50 pièces, aucun au-delà du plafond de 60 ; 161 472 caractères. Écartées ou non servies : 9 pièces sans fenêtre qualifiante, 9 pièces DRS, 3 fenêtres dans une section des facteurs de risque, 7 déjà lues dans un bloc du même dépôt. Les blocs vont du 2026-09-22 au 2025-01-27 : 27 de 8-K, 5 de 485APOS, 5 de 6-K, puis S-1, F-1, 424B3, 424B4, 425, 10-K, 10-Q, 20-F, DEFM14A et DFAN14A. Liste de lecture `stargate`, dans l'ordre du montage.
  (22) Volet E, lecture, sans sous-agent (2026-10-19) :
  - règles de codage, appliquées à tout le volet :
    - une mention générale de Stargate (contexte du marché, titres de presse, chronologies, déclarations de personnes) reçoit `no_relevant_content`. Une diapositive ou un paragraphe repris d'un dépôt à l'autre reçoit `duplicate_of_other_block`, car un texte se lit une fois : six fenêtres de WEC Energy Group sur le campus de Port Washington, trois de Genneia, quatre des prospectus de GraniteShares sur Crusoe, chacune reprise d'un bloc relevé ;
    - une relation de Stargate nommée, sans contrat ni montant propres au déclarant, devient une ligne descriptive, même rapportée par un tiers, quand la pièce nomme les parties. La note donne la pièce et la date du dépôt ;
    - un prêt, une commande ou un partenariat sans société nommée en face reçoit `no_named_counterparty` : prêt de construction de 7,1 Md$ conseillé par Newmark, grues de Manitowoc pour Stargate UAE, NVIDIA « key technology partner » du projet (le projet n'est pas une personne morale), premier contrat Stargate attendu par Oracle ;
    - les relations des entités du modèle trouvées dans un bloc servi sont relevées, même hors de Stargate : SK Telecom avec Lambda et Amazon Web Services, accords de nuage d'Oracle. Celles de tiers hors du modèle reçoivent `out_of_scope_content` : Sharon AI et New Era Helium, Mawson, KULR, Penguin Solutions ;
    - un titre d'article cité comme source par le déclarant ne fait qu'une ligne descriptive : le prêt de JPMorgan pour le campus d'Abilene, par une note du communiqué de Newmark ;
    - aucune personne physique n'est citée : déclarations de dirigeants, équipes de direction et transcriptions sont écartées. Le contrôle des noms, refait à la fin de la lecture, ne trouve aucun nom dans les lignes ;
  - rendement : 58 blocs lus, 82 lignes (24 observations, 58 abstentions), aucune rejetée :
    - une arête, de financement : l'investissement en actions de SK Telecom dans Lambda, Inc. (20 M$, février 2024) ;
    - 23 lignes descriptives ; aucun signal, aucun extrait d'appartenance ;
    - abstentions : 22 `no_relevant_content`, 17 `duplicate_of_other_block`, 11 `out_of_scope_content`, 7 `no_named_counterparty`, 1 `boilerplate_no_event` ;
  - faits principaux :
    - sites : Abilene (Texas), campus de 1,2 GW de Crusoe, coentreprise de 15 Md$ de Primary Digital Infrastructure, Crusoe et Blue Owl, prêt de JPMorgan de 2,3 Md$ (titre de presse cité par Newmark) ; Port Washington (Wisconsin), campus de Vantage Data Centers pour OpenAI et Oracle (plus de 15 Md$, jusqu'à 3,5 GW), avec les garanties financières d'Oracle exigées par la commission du Wisconsin ; Frontier (Texas) et Lighthouse (Wisconsin) de Vantage, 40 Md$ en construction ; Stargate UAE (G42, OpenAI, Oracle, SoftBank Group, Cisco) ; Stargate Korea (lettre d'intention et protocole d'accord de SK Telecom avec OpenAI, octobre 2025) ; Stargate Argentina (protocole d'accord de Genneia avec Sur Energy, octobre 2025) ; Stargate Norway (Nscale et Aker, déjà lu en D-0054). Vantage est une société du portefeuille des fonds de DigitalBridge, non une filiale ;
    - partenaires : Arm rejoint le projet en janvier 2025, partenaire technologique clé aux côtés de Microsoft, NVIDIA, Oracle et OpenAI ; partenariat « Cristal intelligence » d'Arm avec OpenAI et SoftBank Group (interne au groupe SoftBank) ; accord de confidentialité de DigitalBridge avec SoftBank Group du 7 mars 2024 ;
    - Oracle, au 2025-03-10 : accords de nuage signés avec OpenAI, xAI, Meta, NVIDIA et AMD ; revenu Database MultiCloud tiré de Microsoft, Google et Amazon (+92 % en trois mois) ; premier contrat Stargate attendu, non signé.
  (23) Premières entités par extrait, avant le volet D (2026-10-19) :
  - source : les 196 extraits d'appartenance des volets B et C (112 et 84), pour 176 dénominations. Le volet E n'en a aucun. Règles : D-0044, point 7 (A et B), D-0050, points 4 et 5, et point 18. Chaque citation est vérifiée mot pour mot dans son bloc lu (espaces normalisés) ;
  - chaîne : une entité n'entre que si la chaîne d'extraits remonte, lien après lien, à SoftBank Group Corp. ou à une entité déjà au groupe. Le traitement `consolidated_subsidiary` suit les mots de D-0050, point 4 ; sinon `undetermined` ;
  - rendement :
    - 148 entités nouvelles au groupe `NF:SOFTBANK` : 94 `consolidated_subsidiary`, 46 `undetermined`, 8 `vie_consolidated`. Volet B 69 (34 et 35) ; volet C 79 (SB Energy 67, Arm 7, DigitalBridge 5) ;
    - 18 entrent à une date, les autres sans date (filiales constituées par le groupe) ;
    - trois entrées de D-0044 ont leur traitement précisé : SoftBank Corp., SB Northstar LP et SoftBank Group Capital Limited passent à `consolidated_subsidiary`, avec l'extrait nouveau. Le groupe compte 160 entrées ;
  - déposants rattachés par leur CIK (mécanisme d'Athene Holding, D-0055, point 8) : SB Energy, Inc. (2133037) et Arm Holdings plc (1973239), sans date ; DigitalBridge Group, Inc. (1679688) au 2026-09-30. Leurs blocs lus passent à `NF:SOFTBANK` à ces dates, au réassemblage ;
  - alias nés d'un extrait qui les définit (D-0021) : « SoftBank Group » (SoftBank Group Corp., 20-F de 2026 d'Arm), « SBGC », « SBGA », « SBIA US », « SBE Global », « Energy Global » et « Ampere » (Ampere Computing Holdings LLC). « SoftBank Group » est global : les deux lignes d'Intel que D-0044 laissait hors du groupe, dont le placement de 2,0 Md$ de septembre 2025, y passent ;
  - dates d'entrée, à la réalisation citée : Berkshire Grey (2023-07-20), Studio 151 (2025-11-24), Ampere (novembre 2025, jour non écrit : dernier jour du mois, 2025-11-30), DreamBig (2026-07-01), DigitalBridge et sa filiale (2026-09-30). Les douze filiales de la pièce 21.1 du S-1 de SB Energy entrent à la date du dépôt (2026-09-01), comme celles de Nscale (D-0054) ;
  - deux exclusions de D-0044, point 7, levées par un extrait nouveau :
    - SoftBank Vision Fund II-2 L.P. : « certain affiliates of SoftBank, including SoftBank Vision Fund II-2, L.P. » (13D/A du 2023-04-11 sur WeWork). Ses décisions d'investissement reviennent à SB Global Advisers Limited, dont SoftBank est l'actionnaire unique. Ses véhicules entrent avec lui ;
    - SVF Endurance (Cayman) Limited : désignée « SoftBank » par l'accord d'adhésion du 20 mars 2023 (règle B) ;
  - restent hors du groupe, 26 dénominations :
    - Sprint : aucun bloc lu n'affirme le contrôle (une majorité des voix, de 83,80 % à 84,85 %, sans le mot) ni ne cite ses dates. Le 13D/A du 2020-02-21 dit seulement « as early as April 1, 2020 ». Contrepartie propre (point 9). Starburst I, Inc. et Galaxy Investment Holdings, Inc., filiales à 100 %, entrent ;
    - Fortress Investment Group LLC : entrée citée (2017-12-27), sortie de 2024 non citée. Un rattachement sans fin ferait de Fortress une entité de SoftBank après sa cession ;
    - le SoftBank Vision Fund L.P. et ses véhicules, 17 dénominations (AIV M1, AIV S1, SVF Holdings (UK) LLP, SVF GP (Jersey) Limited…) : leur gérant, SB Investment Advisers (UK) Limited, n'est relié à SoftBank par aucun bloc lu. Kigen (UK) Limited aussi : « SoftBank Vision Fund indirectly owned 85% », fonds non rattaché ;
    - GreenBox Systems LLC : coentreprise (65 % pour Sunlight, 35 % pour Symbotic, trois gérants), contrôle non affirmé ;
    - SVF II GP (Jersey) Limited (commandité du fonds, propre lien non écrit), SVF Sponsor II (DE) LLC (lien non écrit), Backgammon Acquisition Corp. (« Merger Sub », dénomination non liée dans le bloc) et SB Energy Private Limited (sortie à la cession de 2021, non datée) ;
  - corrections, faites avant l'écriture des entrées : deux extraits lus portaient `consolidated_subsidiary` sans le mot filiale. SBLA Holdings (Cayman) L.P. (« controlled and wholly owned by ») et Studio 151, LLC (« 100% of the membership interests ») passent à `undetermined`, dans les fichiers d'observations comme dans les entrées ;
  - SB Management Limited : le 13D/A de 2023 sur Symbotic la dit ancienne dénomination de SB Northstar LP, ce que contredit le 13D/A de 2022 (gérante de SB Northstar LP jusqu'au 31 mars 2022). Elle reste une entité propre du groupe, sans alias ;
  - note de lecture devenue inexacte : les relations d'Arm avec Kigen, notées « interne au groupe » au volet C, ne le sont pas dans le modèle, puisque Kigen reste hors du groupe ;
  - code et tests : `config.yaml` seul (148 entrées, trois entrées précisées, sept alias) ; deux tests de plus (`test_sb_own`, quatorze tests) ; résolution vérifiée sur la configuration réelle.
  (24) Volet D, règles fixées avant tout tirage (2026-10-19). Elles appliquent le point 6 aux entités du point 23 :
  - lexique : 60 termes nouveaux de la piste, cible `NF:SOFTBANK`, en casse exacte et en mots entiers (version lx-a0784a3638fc avec les six termes antérieurs). Ce sont les noms distinctifs des entités rattachées :
    - véhicules et gérants : « SVF II » (alias confirmé du fonds, préfixe de ses véhicules), « SVF Endurance », « SVF Excalibur », « SVF Fast », « SVF Swift », « SVF Yellow », « SVF Sponsor III », « SVF Sponsor LLC », « SB Northstar », « SB Global Advisers », « SB Investment Advisers (US) », « Silver Brick Management », « Star Beacon », « Stellar Beacon », « Brightstar US », « Starburst I », « Galaxy Investment Holdings », « Kronos I (UK) », « Kronos II », « Kronos Holdco », « SB Foundation Holdings », « LDH Sponsor », « Latin America Digital Holdings », « SBLA Latin America Fund », « SBLA Holdings », « SBLA Investments », « SLA Investments IV », « Phoenix SPAC Holdco », « Skywalk Finance », « Tsubasa Corporation », « Backgammon Investment », « SB Management Limited », « Sunlight Investment Corp », « SB WW Holdings », « StarBright WW », « SB Group US », « LY Corporation », « PayPay », « Berkshire Grey » (à partir du 2023-07-20) ;
    - SB Energy : « SB Energy », « SBE Global », « Milam County DC », « Pelicans Jaw », « Aratina », « IP Backlog Land Holdings », et, à partir du 2026-09-01 (pièce 21.1), « Holville Solar », « Paris Farm Solar », « Angiola East », « Ben Milam Solar ». D-0044 écartait « SB Energy », entité alors non confirmée ; elle l'est (point 23) ;
    - Arm : « Arm Holdings », « ARM Holdings », « Arm Limited », « ARM Limited », « Arm Technology Israel », « Arm France », « Acetone Limited », « Ampere Computing » (à partir du 2025-11-30), « DreamBig » (à partir du 2026-07-01) ;
    - DigitalBridge : « DigitalBridge » (à partir du 2026-09-30), « Duncan Holdco » ;
  - écartés comme génériques : « Arm », « Ampere », « SVF », « Vision Fund », « SBG », « SBLA », « Energy Global », « B Holdings », les « Project 4 LLC » à « Project 10 LLC » et les « Delaware Project », « Venus Buyer », les « SE … » de SB Energy (Titan, Athos, Juno, Cosmos, DC Holdco…), les « Orion », « Big Five », « Libra » et « Eiffel », « Studio 151 », « Foundation (GP) Holdings ». « SoftBank » couvre déjà les dénominations qui le portent ;
  - sources : les 47 archives des Notes Data Sets, retirées et scannées sous le nouveau lexique d'ensemble, puis effacées ; recherche plein texte des seuls termes nouveaux sur les formulaires racines des EX-10 (`search new`), les résultats des six termes antérieurs étant gardés ; vérification de chaque pièce sous le lexique d'ensemble ;
  - file propre : l'état des unités d'avant l'enrichissement est gardé une fois (`snapshot`, `nf_discovery_units_before_d0058.parquet`). Une unité connue garde sa règle, son rang et son état. Les unités que nul terme antérieur ne faisait naître forment une file à part, R1 puis R2 (D-0044, point 5), plafonnée à 300 ;
  - une unité nouvelle tirée d'un dépôt propre du groupe ne se lit pas (état `own_group`, exclusion `out_of_scope`) : dépôts d'Arm et de SB Energy, de DigitalBridge à partir du 2026-09-30, et des CIK propres de SoftBank (point 4). Ces textes ont été lus aux volets B et C ; leurs mentions de leurs propres entités sont internes au groupe ;
  - code : `nf_discovery.snapshot`, `select_with_prior`, `own_group_ciks`, `search(new_only)` ; deux tests de plus (`test_nf_discovery`). Le volume se consigne ici avant toute lecture.
  (25) Volet D, volume consigné avant toute lecture (2026-10-19) :
  - archives : les 47 archives des Notes Data Sets, retirées et scannées sous le lexique lx-a0784a3638fc (18,56 Go, effacées après le scan). 3 943 lignes de notes nomment un terme de la piste ;
  - recherche plein texte des 60 termes nouveaux : 52 requêtes, 533 résultats ; 21 termes sans résultat (Acetone Limited, Ampere Computing, Aratina, Arm France, Arm Technology Israel, DreamBig, Holville Solar, Kronos Holdco, Kronos I (UK), Latin America Digital Holdings, Milam County DC, les quatre termes SBLA et SLA, SVF Fast, SVF Swift, SVF Yellow, Skywalk Finance, Tsubasa Corporation). Le premier passage s'est arrêté sur une réponse d'erreur du service de recherche (« ConnectionError »), gardée en cache. Elle est écartée, et une réponse sans résultats n'est plus jamais gardée : elle se redemande après une pause (`discovery._efts`, un test de plus dans `test_nf_discovery`) ;
  - vérification : 846 pièces EX-10 de déposants hors des groupes, 711 qui nomment un non-déposant, 135 aucun ; 243 requêtes ;
  - candidats : 4 501 mentions, 382 candidats, 4 073 unités. Les 3 717 unités d'avant gardent leur état sous leur clé ;
  - file propre : 356 unités nouvelles. 12 sont retenues chez 7 candidats : 7 en-têtes d'EX-10 par R1 (Adobe 3, Kulicke & Soffa 2, Symbotic 2) et 5 notes par R2 (WeWork, Better 2, WEBTOON Entertainment, Illumina). 297 sont hors de la règle ; 47 viennent de dépôts propres du groupe (`own_group` : Arm 36, SB Energy 10, DigitalBridge 1). Le plafond de 300 n'est pas atteint. Les termes qui font naître le plus d'unités nouvelles sont « SB Northstar » (66), « SVF II » (50), « SVF Sponsor III » (40), « Acetone Limited » (34, dépôts d'Arm), « LDH Sponsor » (27) et « LY Corporation » (25) ;
  - volume, avant lecture : 12 blocs, 67 824 caractères (5 requêtes). Liste de lecture `nf_d58`, dans l'ordre de la file.
  (26) Volet D, lecture, sans sous-agent (2026-10-19) :
  - règles de codage, appliquées à tout le volet :
    - un en-tête d'EX-10 qui ne montre aucun groupe partie ne fait pas lire le corps (D-0044, point 5). C'est le cas des plans de rémunération d'Adobe et de Kulicke & Soffa (les sociétés du modèle n'y sont nommées que comme comparables) et des deux conventions de GreenBox Systems LLC, dont l'en-tête ne nomme aucune partie ;
    - le coût d'un soutien de crédit payé par le bénéficiaire (commissions, bon de souscription) est une ligne sans famille, comme le soutien de Google payé en bons (D-0050). Le soutien lui-même est `credit_support` ;
    - une relation entre deux tiers rapportée par un déclarant qui n'y est pas partie est une ligne descriptive, sans arête pour lui : l'accord de PacBio avec SB Northstar LP, lu chez Illumina ;
    - des montants de parties liées donnés ensemble pour plusieurs contreparties, sans part de l'entité de SoftBank, ne font pas d'arête : ceux de NAVER et de LY Corporation chez WEBTOON Entertainment ;
    - aucune personne physique n'est citée, y compris le fondateur de Better et ses sociétés ;
  - rendement : 12 blocs lus, 29 lignes (17 observations, 12 abstentions), aucune rejetée :
    - 5 arêtes, toutes avec montant : 2 de soutien de crédit (WeWork) et 3 de financement (Better) ;
    - 7 lignes sans famille avec montant, 5 lignes descriptives ;
    - abstentions : 5 `no_relevant_content`, 4 `out_of_scope_content`, 2 `no_named_counterparty`, 1 `duplicate_of_other_block` ;
  - faits principaux :
    - WeWork (note 18 du 10-Q de 2023-08-08) : SVF II, obligé de la tranche de premier rang depuis le cinquième avenant de décembre 2022, avec 1,0 Md$ de lettres de crédit en cours au 30 juin 2023 ; tranche junior de 470 M$, dont SVF II reprend le rôle de SBG en février 2023 ; commissions de l'accord de remboursement avec SBG (16 M$ par trimestre, 32 M$ au premier semestre 2023) ; bon de souscription remis à SBG, de 284 M$ à l'émission ; lettre de soutien de crédit du 25 mars 2021 ;
    - Better (notes 10 et 11 du 10-Q de 2026-08-11) : échange du 28 avril 2025 avec SB Northstar LP, soit 532,5 M$ d'obligations convertibles éteintes contre 155,0 M$ d'obligations garanties de premier rang et 110,0 M$ en numéraire ; gain de restructuration de 210,0 M$ porté en capitaux propres ; valeur comptable des obligations de 198,8 M$ au 30 juin 2026, intérêts payés en nature depuis le 18 juillet 2025 ;
    - WEBTOON Entertainment : LY Corporation, avec NAVER, est l'un des principaux actionnaires ; services de publicité fournis à LY et services d'usage de marque et de sous-traitance reçus d'elle ;
    - PacBio : accord d'investissement de février 2021 avec SB Northstar LP pour 900 M$ d'obligations convertibles (rapporté par Illumina).
  (27) Volet F, sources et colonnes vérifiées avant tout tirage d'archive (2026-10-19) :
  - page des Form N-PORT Data Sets tirée une fois et gardée en cache : 28 archives trimestrielles, de 2019q4 (données déposées depuis octobre 2019) à 2026q3 (440,95 Mo pour la dernière). Une archive dont l'en-tête Last-Modified est postérieur à l'as_of est une connaissance postérieure : ni gardée ni scannée (état `after_as_of`), et comptée dans les exclusions ;
  - description publiée tirée une fois (`nport_readme.pdf`, Last-Modified du 26 juillet 2024) et lue avant tout calcul. Tables et colonnes retenues (sections 5.1 à 5.3 et 5.10 à 5.12) : SUBMISSION (FILING_DATE, SUB_TYPE, REPORT_DATE, « date as of which information is reported »), REGISTRANT (CIK, REGISTRANT_NAME, LEI), FUND_REPORTED_INFO (SERIES_ID, SERIES_NAME, SERIES_LEI), FUND_REPORTED_HOLDING (ISSUER_NAME, ISSUER_LEI, ISSUER_TITLE, ISSUER_CUSIP, BALANCE, UNIT, CURRENCY_CODE, CURRENCY_VALUE, EXCHANGE_RATE, ASSET_CAT…), IDENTIFIERS (IDENTIFIER_ISIN), DEBT_SECURITY (MATURITY_DATE, COUPON_TYPE, ANNUALIZED_RATE, IS_DEFAULT, ARE_ANY_INTEREST_PAYMENT, IS_ANY_PORTION_INTEREST_PAID). Fichiers TSV en UTF-8. Les noms sont dans `nport.columns` ;
  - unité de la valeur : la description dit seulement « Value » (rubrique C.2.c). Le formulaire N-PORT (`formn-port.pdf`, tiré une fois, Last-Modified du 3 décembre 2024) précise : « Report values in U.S. dollars. If currency of investment is not denominated in U.S. dollars, provide the exchange rate used to calculate value. » La valeur dans la monnaie du titre est donc la valeur en dollars convertie par ce taux. Le sens du taux n'est écrit nulle part : il se vérifie sur les positions scannées avant tout calcul (titres en yens et en euros), et se fixe dans `nport.exchange_rate_convention` ;
  - mesure : nominal pris sur les positions dont l'unité est `PA` (« principal amount ») et la catégorie d'actif `DBT` ; titre identifié par son ISIN, à défaut par son CUSIP ; dernier dépôt de chaque série par date de portefeuille, par date de dépôt puis par accession (un NPORT-P/A remplace le dépôt) ;
  - LEI : un LEI relevé avec un nom qui contient « SOFTBANK » s'applique à l'archive où il est relevé (second passage de la table des positions) et à celles qui sont scannées ensuite, de la plus récente à la plus ancienne. Une archive scannée avant qu'un LEI ne soit relevé est signalée, puis rescannée ;
  - code : `pipeline/nport.py` (`page`, `fetch`, `scan_archive`, `positions`, `price_to_par`, `cells`, `exclusions`), bloc branché sous la portée `nport` ; trois tests (`test_nport`).

  (28) Volet F, volume et corrections fixées avant tout calcul de la mesure (2026-10-19) :
  - volume : 28 archives tirées, scannées et effacées, de 2019q4 à 2026q3 (11,94 Go). 31 746 lignes de positions sont gardées sous `cache/datasets/nport/` (8,3 Mo) ;
  - date de publication : le tirage cherchait l'en-tête Last-Modified dans un `dict`, alors que le client rend les en-têtes de `requests` : aucune date n'a été lue. C'est corrigé et testé. Les dates sont relevées après coup par une requête HEAD par archive (28 requêtes, `python -m pipeline.nport stamp`, par le client unique, avec journal ; option `method` du client). L'archive 2026q3 est publiée le 7 octobre 2026 à 16 h 13 GMT, le jour de l'as_of : elle est gardée, la règle du point 27 n'écartant qu'une archive publiée après l'as_of. Les 27 autres sont publiées entre le 25 juillet 2024 (les archives de 2019q4 à 2024q2 ont été republiées en juillet 2024) et le 9 juillet 2026 ;
  - sens du taux, vérifié sur les positions avant tout calcul : EXCHANGE_RATE est en unités de la monnaie du titre pour un dollar (0,852915 pour l'euro et 105,465 pour le yen au 30 septembre 2020). Une obligation de SoftBank Group en euros, de nominal 100 000, déclarée 117 203,24 dollars, vaut 99 964 euros, soit 99,96 % du pair ; l'autre sens donnerait 137 %. `nport.exchange_rate_convention` reste `currency_per_usd` ;
  - LEI : la règle mécanique du point 27 a relevé 7 LEI, dont 5 appartiennent à d'autres émetteurs : Sprint Corp (549300ZTTY7CXOLJ6539), Sprint Communications (549300JKU50UT08ZWD77), Sprint Capital (549300L17W0GQBR1PO80), SB Technology (529900I4GPREMKBTJL62, déclarée 30 fois sur 562 sous son ancien nom « SoftBank Technology », des actions) et Goldman Sachs International (N9FYJ29MC81JI74MJE92). Il y a deux causes. Une famille de fonds (Thrivent) déclare comme nom d'émetteur la société mère ultime, « SoftBank Group Corp. », pour des titres de Sprint et de Drawbridge Special Opportunities Fund, avec le LEI de l'émetteur réel ou « N/A ». Un fonds (GuideStone) déclare un CDS sur SoftBank Group sous le LEI de sa contrepartie. Appliquée telle quelle, la règle faisait entrer toutes les positions de Sprint (de 1 578 à 2 669 lignes par archive de 2019q4 à 2020q3) et demandait le rescan de 27 archives ;
  - correction du LEI, fixée sur ces faits d'identité et avant tout calcul : un LEI relevé n'est un LEI de SoftBank que si la majorité des positions gardées qui le portent, toutes archives confondues, ont un nom qui contient « SOFTBANK ». Sont acceptés SoftBank Group (5493003BZYYYCDIO0R13, 13 480 positions sur 13 692) et SoftBank Corp. (353800M1YCTS9JRBJ535, 8 626 sur 8 633). Les cinq autres n'atteignent pas 10 % : SB Technology 30 sur 562 ; Sprint 22 sur 2 212, 3 sur 718 et 86 sur 5 500 ; Goldman Sachs 1 sur 10. Les deux LEI acceptés sont relevés dans la première archive scannée (2026q3) et appliqués à toutes les autres : aucun rescan n'est nécessaire. Le tirage recalcule les LEI acceptés après chaque archive. Une position qui ne porte qu'un LEI refusé sort des positions lues (8 860 lignes) ; il en reste 22 886, dont 22 667 par le nom et 219 par un LEI accepté seul ;
  - correction du titre : un titre n'entre dans la mesure que si la majorité de ses positions retenues portent un nom qui contient « SOFTBANK », et l'une au moins un intitulé de titre qui le contient. Sortent 12 titres d'autres émetteurs, déclarés sous le nom ou le LEI de SoftBank Group (Sprint, Sprint Spectrum, Sprint Capital, Nationstar Mortgage, Drawbridge), soit 319 positions. Sprint et Fortress ne sont pas des entités confirmées du groupe (point 23). Restent 50 titres de SoftBank Group et de SoftBank Corp. ;
  - identifiants : un ISIN a 12 caractères (2 lettres, 9 lettres ou chiffres, 1 chiffre), un CUSIP en a 9 ; « N/A » et « 000000000 » ne sont pas des identifiants. Une position sans ISIN prend l'ISIN que d'autres positions donnent au même CUSIP, s'il est unique. 4 positions sans identifiant sortent ;
  - positions vendeuses : 15 positions déclarées « Short » sortent, car la valeur d'une position vendeuse n'est pas celle d'un titre détenu ;
  - fonds sans série : un fonds fermé n'a pas d'identifiant de série, et son dernier dépôt se cherche par déclarant (CIK). Le code confondait ces fonds en un seul pour chaque date ; le défaut est corrigé et testé avant tout calcul ;
  - volume de la mesure : 4 624 positions retenues, dont 4 491 au dernier dépôt de chaque série ; 261 séries ou fonds ; 97 dates de portefeuille, du 30 septembre 2019 au 31 juillet 2026 ; 1 092 cellules (titre, date) ;
  - hors mesure, et comptés : 5 positions d'un CDS sur SoftBank Group (GuideStone, du 31 mars 2025 au 31 mars 2026), 4 dérivés sur actions, 168 prêts en nominal (LON), 129 titres de dette déclarés en nombre (DBT/NS), 17 610 positions en actions ;
  - limite déclarée : un amendement qui ne porte plus aucune position de SoftBank n'est pas vu, puisque les extraits ne gardent que les dépôts qui en portent une. Le dépôt antérieur reste alors retenu ;
  - code : `pipeline/nport.py` (`lei_evidence`, `accepted`, `softbank_leis`, `security_keys`, `fund_key`, `selection`, `latest_by_fund`, `stamp`, `volume`), `pipeline/net.py` (option `method`) ; neuf tests (`test_nport`).

  (29) Intégration et résultats (2026-10-19) :
  - entités par extrait, après le premier réassemblage. 71 des 883 lignes d'observation des listes de D-0058 nommaient 22 noms en attente. 16 sont rattachés par un extrait vérifié mot pour mot :
    - 5 alias : « Arm China » (Arm Technology (China) Co. Limited, 26 lignes d'Arm) ; « Cadence » (Cadence Design Systems, Inc., extrait de la note de cession de l'activité Artisan, non de la biographie d'un administrateur) ; « OAI » (OpenAI Infra Holdings, LLC) ; « Sprint » (Sprint Corporation, hors du groupe, point 23) ; « NVIDIA COR » (nom tronqué de la table d'informations d'un 13F, qui porte aussi « NVIDIA CORPORATION » sous le même CUSIP 67066G104). Les 14 lignes de détention de SoftBank rejoignent ainsi NVIDIA ;
    - 2 entités membres, au traitement indéterminé (règle A, sans les mots de D-0050, point 4) : OpenAI Infra Holdings, LLC au laboratoire OpenAI (« an affiliate of OpenAI, Inc. ») ; Treasure Data au groupe SoftBank, composante de l'activité IoT d'Arm distribuée en juin 2021 aux actionnaires d'Arm, « subsidiaries of SoftBank Group ». Le prêt de 50 M$ d'un membre du groupe à Treasure Data devient interne ;
    - 10 entités propres : cinq établissements financiers des crédits de SB Energy (Deutsche Bank Trust Company Americas, Deutsche Bank AG New York Branch, Banco Santander S.A. New York Branch, Truist Bank, CoBank ACB) ; VTEX (dénomination EDGAR lue dans l'en-tête SGML) ; SVF Investment Corp. 2 et 3, LDH Growth Corp I (émetteurs des 13G, sans lien de contrôle affirmé) ; Vantage Data Centers (société du portefeuille de DigitalBridge) ;
    - 6 noms restent en attente, faute d'un extrait qui les identifie (7 lignes) : « ARM Holdings » (10-K d'AMD de 2020, circulaire d'Intel de 2024 ; la dénomination légale change avec la date, Arm Limited puis Arm Holdings plc, et aucun extrait ne la donne), « Ares », « JPMorgan », « Primary Digital Infrastructure », « Vantage » et « xAI » ;
  - code :
    - `schema.sql` régénéré pour `nport_price_to_par`. Le premier réassemblage échouait à l'insertion des cellules : la mesure était au registre, pas dans les contraintes du schéma. Un test vérifie désormais que le schéma est le rendu du registre (`test_schema_sync`) ;
    - rendu de la série N-PORT : une section dans `synthesis.md` (titres détenus à la dernière date, plus bas, première date) et une table par titre dans `series.md` ;
    - trois tests (`test_schema_sync`, `test_sb_own`, `test_nport`) ;
  - premier réassemblage : observations 27 671 → 28 950, toutes valides ; entités 3 047 → 3 554 ; liens 10 623 → 10 869 ; faits 1 580 920 → 1 580 956 ;
  - BDC Data Sets : extraction refaite après les rattachements (D-0043, point 14), soit 3 465 167 lignes de positions (3 057 432) dans 2 100 dépôts. Faits de BDC rattachés : 3 536 (3 405), dans 456 dépôts de 62 fonds (435, 60). Nouveaux émetteurs :
    - SoftBank. Apollo Debt Solutions BDC détient 25 M$ de nominal d'un prêt de premier rang, « Softbank ARM Loan », accordé à Kronos I (UK) Limited, filiale à 100 % de SoftBank Group Capital. Il s'agit d'un tirage différé et d'un prêt à terme à SOFR + 225 ou 250 points de base, d'échéances août et septembre 2027. Juste valeur ÷ coût : de 1,001 à 1,003, du 31 décembre 2025 au 30 juin 2026 ;
    - DigitalBridge Group, Inc. : actions de préférence des séries H, I et J, avant l'acquisition ;
    - DoorDash, Inc. et Pear Therapeutics, Inc., nommées par des lignes de D-0058 ;
    - DISH DBS Corp, DISH Network Corp et Match Group, Inc., déjà au registre comme déposants découverts, dont les positions entrent avec cette extraction.

    Second réassemblage : faits 1 581 051, entités 3 569, mesures 171 024 ;
  - SoftBank :
    - 162 entités au groupe (13 avant D-0058) : 99 filiales consolidées, 53 au traitement indéterminé, 8 entités à intérêt variable consolidées, 2 têtes ;
    - 238 arêtes (48 avant D-0058), dont 136 à montant et 15 internes au groupe ;
    - arêtes vers les groupes et les laboratoires : NVIDIA 16, TSMC 10, Intel 9, OpenAI 8, Cipher 6, Oracle 3, Marvell 1 ;
    - principales contreparties propres : WeWork 36, Arm China 26, Better Home & Finance 10, General Motors 9, Sprint 7, Ampere 7 (avant son entrée au groupe le 30 novembre 2025), Kigen 6 (hors du groupe, point 23), Balanced Rock Power 6, Arevia Power 5 ;
    - lignes de D-0058 par liste : `sb_own_b` 399 observations et 60 abstentions (262 blocs) ; `sb_own_c` 395 et 164 (211) ; `sb_corpus` 48 et 110 (142) ; `stargate` 24 et 58 (58) ; `nf_d58` 17 et 12 (12) ; `sb_fix` 0 et 1 ;
  - N-PORT : 1 092 cellules sur 50 titres (45 de SoftBank Group, 5 de SoftBank Corp.), du 30 septembre 2019 au 31 juillet 2026. 37 titres sont détenus dans les trois mois qui précèdent la dernière date, 13 ne le sont plus. C'est une valorisation déclarée, rapportée sans interprétation de crédit :
    - les plus bas tombent en mars 2020 (6,875 % 2027 en dollars : 76,0 %) et de juin à octobre 2022 (3,875 % 2032 en euros : 68,0 % ; 3,375 % 2029 : 68,6 % ; 4 % 2029 : 70,8 %) ;
    - au 31 juillet 2026, les titres longs restent sous le pair : 3,875 % 2032 en euros 88,5 %, hybride 2062 en euros 88,9 %, 5,25 % 2031 en dollars 92,5 % ;
    - les émissions de juillet 2025 cotent de 95,0 à 98,9 %, après un plus bas en mars 2026 (hybrides 2061 et 2065 à 89,8 % et 89,7 %) ;
    - les émissions d'avril 2026 sont au pair (100,4 à 100,9 %) ;
  - rendus : documents 25 104 (23 526), faits 1 581 051 (1 580 920), observations 28 950 (27 671), entités 3 569 (3 047), liens 10 869 (10 623), mesures 171 024 (169 094), contrôles 69 946 (69 943), exclusions 31 402 (30 126). 14 035 nombres publiés (11 527), dont 2 372 pour la série N-PORT. Exclusions :
    - `not_processed` 27 899 (27 154) : 405 fenêtres 6-K d'Arm au-delà du plafond de 80 unités (point 5) et 340 unités de la piste élargie, hors de la règle de lecture ou au-delà du plafond ;
    - `out_of_scope` 1 069 (569) : unités tirées des dépôts propres du groupe (état `own_group`), formulaires 4 de SB Investment Advisers (UK) sur Vir Biotechnology, fenêtres dans les facteurs de risque ;
    - `pending_entity` 587 (556) ;
    - bloc `nport` : aucune exclusion. Les 28 archives sont scannées, publiées au plus tard le jour de l'as_of, et aucun LEI n'est accepté en retard ;
  - annexe F : événements des groupes inchangés. SoftBank n'a pas de comptes au modèle ;
  - paires : 236 (233).
    - Nouvelles : NVIDIA → SoftBank, Marvell → SoftBank et TSMC → SoftBank. NVIDIA → SB Energy et NVIDIA → Energy Global, deux paires de D-0057, se fondent dans NVIDIA → SoftBank, ces entités étant au groupe depuis le point 23 ;
    - nouvelles aussi, par des lignes du volet A : Oracle → TikTok USDS Joint Venture LLC (participation de 15 % mise en équivalence) et TSMC → Intel ;
    - conclusions : causalité non établie 158 (155), achats réciproques seulement 44, relation commerciale doublée d'un financement 26, dépendance documentée 8 ;
    - paires à financement documenté : 84 (83). La nouvelle est Oracle → TikTok USDS Joint Venture LLC ;
  - cycles (E.6) : 103 (102). Le nouveau est NVIDIA → SoftBank → OpenAI → NVIDIA (longueur 3, relation commerciale doublée d'un financement) ;
  - E.7 : 166 issues (164), dont 57 % indéterminées au point de tête ; discrimination possible ;
  - contrôles, vue `as_known` : `mismatch` 1 833, `not_testable` 1 336 (1 333), `ok` 29 886, `tautological` 1 393 ;
  - lacunes déclarées :
    - Kigen (UK) Limited reste hors du groupe : ses relations avec Arm ne sont pas internes ;
    - les véhicules du SoftBank Vision Fund L.P. restent hors du groupe, faute d'un bloc lu qui relie leur gérant à SoftBank ;
    - Sprint (de 2013 à 2020) et Fortress (de 2017 à 2024) restent des contreparties propres ;
    - six noms en attente (ci-dessus) ;
    - N-PORT : un amendement sans position de SoftBank n'est pas vu ; prêts, CDS et dérivés restent hors de la mesure ;
  - tests unitaires : 198, tous passés.

- **D-0059 — OpenAI et Anthropic : montage de corpus et entités par extrait (volets 1 et 2). Règles fixées avant tout traitement.** (1) Décision de l'utilisateur, le 2026-10-19 : « On commence par les volets 1 et 2 ». Elle répond au remue-méninges demandé le même jour (« Dans le même genre, tu penses qu'il y a moyen de récupérer beaucoup plus d'informations intéressantes sur Anthropic et OpenAI en étant astucieux et malin étant donné que ça a l'air d'être parmi les acteurs principaux de notre modèle ? Reste en mode brainstorming »). Ce remue-méninges proposait neuf volets. Seuls le volet 1 (montage de corpus « laboratoires ») et le volet 2 (entités des laboratoires par extrait) sont ouverts ; les autres restent des propositions. L'as_of reste le 2026-10-07. Aucune requête réseau.

  (2) Constat, compté sans lecture, après l'intégration de D-0058 :
  - OpenAI : 4 entités, 82 arêtes, dont 46 à montant. Contreparties : CoreWeave 19, Cerebras 19, Microsoft 18, Amazon 10, SoftBank 8, AMD 5, NVIDIA 3. Aucune arête avec Oracle, qui ne nomme OpenAI que dans un document ;
  - Anthropic : 2 entités, 8 arêtes, dont 2 à montant : TeraWulf 3, Akamai 3, Broadcom 1, Nscale 1. Aucune avec Amazon ni Alphabet ;
  - documents des groupes en cache (4 223 documents principaux et pièces de la période, en HTML ou en texte), comptage en mots entiers et en casse exacte sur le texte :
    - « OpenAI » : 70 documents et 756 occurrences (CoreWeave 405, Microsoft 202, AMD 51, Amazon 49, NVIDIA 28…), dont 11 circulaires de procuration ;
    - « Anthropic » : 37 documents et 233 occurrences (Amazon 101 dans 13 documents, Akamai 59, TeraWulf 33, SpaceX 8, Meta 6, Broadcom 6, Hut 8 6, NVIDIA 4…), dont 5 circulaires. Alphabet ne le nomme que deux fois, Microsoft une fois ;
    - correction avant toute lecture : le comptage du remue-méninges, insensible à la casse et sans mots entiers, donnait 156 documents et 450 occurrences pour Anthropic. Il comptait « philanthropic », présent dans 122 documents (183 occurrences, surtout des circulaires) ;
  - blocs lus qui nomment un laboratoire : 88 pour OpenAI, 19 pour Anthropic, aucun d'Amazon ni d'Alphabet pour Anthropic ;
  - les véhicules des Form D sont déjà couverts (D-0041) : 531 cellules pour Anthropic et 218 pour OpenAI.

  (3) Volet 1, montage de corpus `labs_corpus`, sur les règles du volet A de D-0058 (point 3) :
  - documents : documents principaux et pièces, en HTML ou en texte, déposés par un groupe de `config.yaml` du 2017-01-29 (début du texte) à l'as_of, déjà en cache ;
  - termes qualifiants, en mots entiers et en casse exacte :
    - « OpenAI » et « OPENAI ». Ils couvrent ses entités : OpenAI OpCo, OpenAI Global, OpenAI Group PBC, OpenAI Infra Holdings, OpenAI Foundation ;
    - « Anthropic » et « ANTHROPIC », sauf suivis de « Capital », qui désigne un gérant homonyme (D-0041).

    Sont seulement comptés, sans qualifier : « Open AI » (aussi une expression générique), « ChatGPT », « Claude » (aussi un prénom ; jamais une personne), « Stargate » (déjà servi aux volets A et E de D-0058) ;
  - unités : les fenêtres du bloc `montages`, soit le paragraphe qualifiant, les deux qui le précèdent et les deux qui le suivent, fondues quand elles se chevauchent ;
  - ne sont pas lues, et sont comptées :
    - une fenêtre dont chaque paragraphe qualifiant figure déjà, mot pour mot aux blancs près, dans un bloc lu du même dépôt ;
    - une fenêtre dont chaque paragraphe qualifiant se trouve dans la section des facteurs de risque (`out_of_scope`) ;
    - un texte identique à une unité déjà retenue ;
  - ordre : du dépôt le plus récent au plus ancien. Plafond de 300 unités ; au-delà, `not_processed`, et le rendement est présenté avant d'aller plus loin ;
  - une unité appartient au groupe du déposant (perspective `reporting_entity`).

  (4) Lecture, sans sous-agent, par l'exécutant :
  - lignes codées sur les conventions de D-0058. Une relation entre tiers rapportée par un déposant qui n'y est pas partie est une ligne descriptive. Le coût d'un soutien de crédit payé par son bénéficiaire est une ligne sans famille. Un total entre parties liées qui ne nomme pas la contrepartie n'est pas une arête ;
  - un client, un fournisseur ou un investisseur anonyme reste anonyme : aucun « laboratoire » n'est déduit d'une description, d'une presse ou d'un montant ;
  - une valorisation, un gain ou une perte de réévaluation qu'un actionnaire publie sur ses titres d'un laboratoire est une ligne du point de vue de l'actionnaire. Ce n'est jamais un fait comptable du laboratoire ;
  - données personnelles (D-0051 ; D-0058, point 10) : aucune personne physique n'est contrepartie. Une fenêtre de circulaire qui n'est qu'une biographie d'administrateur ou de dirigeant est une abstention ; aucun nom de personne n'est cité, même dans une transaction entre parties liées.

  (5) Volet 2, entités des laboratoires, à l'intégration et après la lecture :
  - appartenance à `LAB:OPENAI` ou à `LAB:ANTHROPIC` par les règles A (lien affirmé par un extrait : filiale, affilié, contrôlé par) et B (désignation par un alias confirmé du laboratoire, « OpenAI » ou « Anthropic ») de D-0044, point 7 ;
  - traitement `consolidated_subsidiary` seulement sur les mots de D-0050, point 4 (filiale, filiale à 100 %, consolidée), sinon `undetermined`. Les têtes déjà confirmées (OpenAI OpCo, LLC, OpenAI Group PBC, Anthropic PBC) restent `parent` ;
  - une entité entre à la date de réalisation citée par un extrait ; une réorganisation, comme la recapitalisation d'OpenAI, ne change une tête qu'à la date citée. Sans date, l'appartenance vaut sans borne (`none`) ;
  - une participation n'est pas une appartenance. Une coentreprise ou un véhicule où un laboratoire détient un intérêt (Stargate LLC par exemple) reste une entité propre, sauf extrait qui affirme le contrôle du laboratoire ;
  - un alias ne naît que d'un extrait qui le définit (D-0021) ;
  - les noms des lignes encore en attente après le premier réassemblage se rattachent par extrait, comme au point 29 de D-0058.

  (6) Ordre et commits :
  - la décision et la configuration (montage `labs_corpus`), avec un test des termes ;
  - volet 1 : pièces du corpus, unités préparées, liste de lecture, volume consigné ici avant toute lecture, commit ;
  - lecture séquentielle, commits par lot, rendement consigné ;
  - volet 2 : entités par extrait, un commit ;
  - intégration : noms en attente par extrait, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (7) Limites connues avant calcul :
  - les laboratoires n'ont pas de comptes au modèle ; tout ce qui s'en lit vient de leurs contreparties ;
  - le volet 1 ne voit que le corpus déjà tiré des groupes : un document d'un autre déposant n'est pas scanné ;
  - un paragraphe qui ne nomme un laboratoire que par un produit (« ChatGPT », « Claude ») ou par un pronom n'est pas servi ;
  - les engagements d'un fournisseur envers un client qu'il ne nomme pas (Oracle, les clients anonymes de Broadcom) restent hors des laboratoires.

  (8) Volet 1, volume consigné avant toute lecture (2026-10-19) :
  - corpus : 4 223 documents des groupes dans la période, tous en cache ; 99 nomment un terme au pré-filtre (insensible à la casse, sur les octets). 3 n'ont aucune fenêtre, le terme n'y étant pas en casse exacte ;
  - fenêtres : 275. Sont écartées 29 fenêtres dans un facteur de risque, 62 déjà lues dans un bloc du même dépôt et 39 doublons de texte. Restent 236 unités, sous le plafond de 300 ; aucune pièce écartée ;
  - lecture : 236 blocs, 636 824 caractères, du 2026-09-24 au 2022-10-27 ;
  - par groupe du déposant : Microsoft 77, CoreWeave 62, Amazon 53, AMD 13, SpaceX 5, Nebius 5, TeraWulf 4, NVIDIA 4, Hut 8 4, Meta 3, Akamai 2, Alphabet 2, Apollo 1, Intel 1 ;
  - par formulaire : 10-Q 105, 10-K 31, DEF 14A 30, 424B4 28, S-1/A 19, 8-K 18, 6-K 4, 20-F 1 ;
  - par laboratoire nommé : OpenAI seul 163, Anthropic seul 58, les deux 15. Termes seulement comptés : « ChatGPT » dans 3 blocs, « Claude » dans 1 ;
  - les blocs des autres montages ne changent pas (mêmes clés de contenu), et aucune clé n'est déjà lue ailleurs ;
  - liste de lecture `labs_corpus`, du dépôt le plus récent au plus ancien.

  (9) Volet 1, lecture faite le 2026-10-19, sans sous-agent, en 29 lots :
  - 236 blocs lus et 335 lignes. 157 observations dans 58 blocs : 92 avec famille, 87 avec montant (79 en dollars, 6 en actions, 2 en parts) et 65 lignes descriptives ;
  - 178 abstentions :
    - 112 doublons d'un autre bloc : reprises du rapport de gestion, index de pièces, versions préliminaires du prospectus de CoreWeave ;
    - 34 sans contenu utile : concurrence, produits, propositions d'actionnaires ;
    - 27 hors champ, dont 19 facteurs de risque que le découpage n'a pas repérés et 7 passages de rémunération de circulaires ;
    - 4 clauses types et 1 contrepartie non nommée ;
  - par groupe :
    - Amazon : 95 observations, dont 58 à montant, pour 53 blocs ;
    - Microsoft : 23 observations, dont 12 à montant, pour 77 blocs ;
    - CoreWeave : 17 observations, dont 8 à montant, pour 62 blocs ;
    - AMD 11 (7 à montant), Hut 8 5 (2), Nebius 4, NVIDIA et SpaceX 1 chacun ;
    - aucune observation pour TeraWulf, Meta, Akamai, Alphabet, Apollo ni Intel ;
  - 145 observations nomment un laboratoire en contrepartie (Anthropic 88, OpenAI 57), dont 76 avec famille et montant. 32 clés d'instrument, dont 17 nouvelles ;
  - principaux faits nouveaux, Amazon et Anthropic (aucune arête avant) :
    - obligations convertibles : 8,0 Md$ du T3 2023 au T4 2025, en cinq souscriptions trimestrielles qui portent le montant (point 11) ;
    - conversions et gains reclassés, réévaluations sur prix observables ;
    - actions de préférence au bilan : 14,8 Md$ au 31 décembre 2025, 92,5 Md$ au 30 juin 2026 ;
    - séries G et H de 5,0 Md$ chacune, facilité d'au plus 20,0 Md$ ;
    - engagement d'Anthropic envers AWS de plus de 100,0 Md$ sur 10 ans (T2 2026), intérêts variables non consolidés ;
  - Amazon et OpenAI :
    - série C de 15,0 Md$ et engagement de 35,0 Md$, dont 13,7 Md$ versés au T2 2026 et 21,3 Md$ en juillet 2026 ;
    - engagements envers AWS : 38,0 Md$, plus une extension de 100,0 Md$ sur 8 ans ;
  - Microsoft et OpenAI :
    - achat supplémentaire de 250 Md$ de services Azure par l'accord du 28 octobre 2025, absent jusque-là ;
    - engagements de 13 Md$, dont 11,6 à 11,9 Md$ versés selon le trimestre ;
    - revenu de 24,1 Md$ tiré d'OpenAI sur l'exercice 2026, créance de 6,0 Md$ ;
    - participation d'environ 27 %, puis 25 % ;
  - CoreWeave et OpenAI :
    - accord de mai 2025 jusqu'à 4,0 Md$, absent jusque-là ;
    - engagement de 11,9 Md$ du prospectus, sous condition d'un véhicule dédié ;
    - panier de dette « contrat OpenAI » de 7,0 Md$ dans quatre actes de fiducie ;
    - accord d'émission d'actions du 7 mars 2025 ;
    - revenus tirés de Microsoft : 81 M$ et 1,2 Md$, soit 35 % et 62 % du revenu de 2023 et de 2024 ;
  - autres groupes :
    - Hut 8 : valeur de 7,0 Md$ du bail de River Bend avec Fluidstack, montant absent jusque-là ; partenariat avec Anthropic et Fluidstack jusqu'à 2 295 MW ;
    - SpaceX : accord de services en nuage avec Anthropic PBC (mai 2026) ;
    - AMD : bons de souscription et contrats d'approvisionnement d'OpenAI et de Meta, à chaque clôture ;
    - NVIDIA : accord d'investissement et de partenariat avec OpenAI en cours de finalisation (10-K de l'exercice 2026) ;
  - corrections faites pendant la lecture :
    - le lot 13, refusé en partie, a été resoumis en entier : les lignes déjà écrites de 13 blocs l'ont été deux fois (24 lignes identiques). Ces doublons exacts sont retirés. Désormais, un lot refusé en partie n'est resoumis qu'après effacement des fichiers de ses blocs ;
    - le même contrôle sur tous les fichiers de lignes trouve 21 lignes identiques en double dans 15 fichiers de passes antérieures (D-0054, D-0056, D-0058). Elles sont traitées à l'intégration ;
    - le revenu futur de 11,55 Md$ du prospectus de CoreWeave passe en nature `other`. Le montant revient à l'engagement de paiement de 11,9 Md$ du même prospectus ;
  - limites constatées : les désignations « an affiliate of OpenAI » et voisines restent en attente, hors des agrégats (D-0032, point 5 ; détail au point 11).

  (10) Volet 2, entités des laboratoires par extrait :
  - noms de laboratoire déjà confirmés dans les lignes du volet 1 : « OpenAI » et « Anthropic » (alias), OpenAI OpCo, LLC (graphie sans virgule comprise), OpenAI Group PBC, Anthropic PBC (« Anthropic, PBC » a la même forme normalisée) ;
  - une entité nouvelle, OpenAI Global, LLC, désignée « OpenAI » par le 10-Q de Microsoft du 29 octobre 2025 (règle B). Traitement indéterminé, sans borne ;
  - OpenAI, Inc. n'est nommée que dans une clause type du contrat de placement de CoreWeave, sans ligne : pas d'entrée ;
  - aucune entité ni aucun alias nouveaux pour Anthropic. Le test `test_lab_entities` vérifie ces rattachements.

  (11) Intégration et résultats (2026-10-19) :
  - corrections faites à l'intégration :
    - 21 doublons exacts retirés de 15 fichiers de passes antérieures (D-0054, D-0056, D-0058). La citation de chacun ne figure qu'une fois dans son bloc ;
    - catégories de lien posées sur deux lignes déjà lues (D-0020). L2 pour la facilité d'Amazon : ses montants deviennent disponibles à mesure qu'AWS livre la capacité de calcul (10-Q du T1 2026). L5 pour les 350,0 M$ d'actions que CoreWeave remet à OpenAI au titre du contrat-cadre (prospectus du 31 mars 2025) ;
    - versements cumulés de Microsoft à OpenAI (11,6 à 11,9 Md$, selon le trimestre) : ils passent en état au coût (base `cost`, nature `other`). La mesure les additionnait comme quatre apports, soit 47,0 Md$ d'exposition au lieu de 11,9 Md$. F2 les retirait aussi à chaque trimestre, d'où un faux événement F2 de Microsoft au 31 décembre 2025 ;
    - chez Amazon, les cinq souscriptions trimestrielles d'obligations d'Anthropic (1,25, 2,75, 1,3, 1,3 et 1,4 Md$) deviennent des flux : 19 lignes, aux mêmes montants et mêmes dates d'un dépôt à l'autre. Deviennent descriptives les deux lignes du cumul de 8,0 Md$, ainsi que la série G annoncée après la clôture du T1 2026, sinon comptée deux fois ;
    - réévaluations d'Amazon sur prix observables (5 lignes) : elles passent en nature `other`, sans base de juste valeur. La plus récente tenait lieu de juste valeur des actions de préférence, ce qui ajoutait 50,5 Md$ à l'exposition. Les gains de conversion (10 lignes) perdent aussi leur base de juste valeur ;
    - code (`counterparty_exposure`) : une réévaluation sur prix observables devient un flux du résultat, comme un gain de mise en équivalence (`FLOW_ONLY`) ; un cumul versé publié au coût est un état, la dernière valeur connue. Les réévaluations de ClickHouse chez Nebius (nature `other`), additionnées jusque-là comme des apports, sortent aussi de l'exposition. Test `test_exposure_labs` ;
  - noms rattachés par extrait après le premier réassemblage : « Fluidstack », alias de Fluidstack Ltd. (10-K de Hut 8), et « Sanmina », alias de Sanmina Corporation (10-K d'AMD). « Uber » reste en attente, faute d'extrait qui le définit ;
  - extraction refaite des BDC Data Sets (D-0043, point 14) : 2 100 dépôts, aucun changement (3 536 faits, 1 031 positions, 61 BDC). Troisième réassemblage après les corrections ;
  - OpenAI : 5 entités et 115 arêtes (82 avant D-0059), dont 69 à montant (46). Contreparties : Microsoft 29, CoreWeave 24, Amazon 21, Cerebras 19, AMD 11, SoftBank 8, NVIDIA 3 ;
  - Anthropic : 2 entités et 73 arêtes (8), dont 56 à montant (2). Contreparties : Amazon 64, TeraWulf 3, Akamai 3, Broadcom 1, Nscale 1, SpaceX 1 ;
  - expositions au 30 juin 2026, du point de vue du fournisseur (jamais un fait comptable du laboratoire) :
    - Amazon sur Anthropic : 18,0 Md$ versés au coût, 92,5 Md$ d'actions de préférence au bilan, 97,9 Md$ de juste valeur des obligations et 16,4 Md$ d'engagements (facilité restante de 15,0 Md$, plus l'engagement de 1,4 Md$ de 2025, déjà versé) ;
    - Amazon sur OpenAI : 28,7 Md$ versés et au bilan, et 50,0 Md$ d'engagements au plafond (15,0 et 35,0 Md$ de série C). Au 30 juin, 28,7 Md$ en sont déjà versés ; le solde de 21,3 Md$ l'est en juillet 2026 ;
    - Microsoft sur OpenAI : 11,9 Md$ versés et 13 Md$ d'engagements ;
  - dépendance de revenu documentée de Microsoft envers OpenAI : 7,3 % du revenu de l'exercice 2026 (24,1 Md$) ;
  - paires : 240 (236).
    - Nouvelles : Amazon → Anthropic, SpaceX → Anthropic, ainsi que Hut 8 → Fluidstack Ltd. et Cipher → Fluidstack Ltd. par l'alias ;
    - conclusions : causalité non établie 160 (158), achats réciproques seulement 44, relation commerciale doublée d'un financement 26, dépendance documentée 10 (8) ;
    - Amazon → Anthropic (L2) et CoreWeave → OpenAI (L5) passent en dépendance documentée. Microsoft → OpenAI reste une relation commerciale doublée d'un financement, sans pièce de lien ;
  - paires à financement documenté : 86 (84). S'y ajoutent Amazon → Anthropic et Amazon → OpenAI ;
  - cycles (E.6) : 106 (103). Trois nouveaux :
    - Amazon → Anthropic → Amazon (longueur 2, dépendance documentée) ;
    - Microsoft → OpenAI → Microsoft (longueur 2, relation commerciale doublée d'un financement) ;
    - CoreWeave → OpenAI → Microsoft → CoreWeave (longueur 3, relation commerciale doublée d'un financement) ;
  - annexe E : premières issues « étayé » de E.1, pour Amazon → Anthropic, Amazon → OpenAI et CoreWeave → OpenAI. Sur chacune de ces paires, F est actif au moins un trimestre et une pièce de lien (L2 ou L5) est trouvée. Issues de E.1 : étayé 3 (0), non étayé 71 (72), indéterminé 11 (11). E.2 à 20 % est réfuté pour Amazon → Anthropic (31 issues réfutées à ce point, 30 avant) : le revenu tiré d'Anthropic reste sous 10 % du revenu d'Amazon de 2023 à 2025 ;
  - E.7 : 170 issues (166), dont 56 % indéterminées au point de tête (57 %). Discrimination possible ;
  - annexe F : un événement nouveau, F2 d'Amazon au 30 juin 2025. Le flux après financement des contreparties devient négatif avec la souscription de 1,3 Md$ d'obligations d'Anthropic ;
  - rendus :
    - tables : documents 25 104 (25 104), faits 1 581 051 (1 581 051), observations 29 264 (28 950), entités 3 576 (3 569), liens 10 984 (10 869), mesures 171 569 (171 024), contrôles 69 950 (69 946), exclusions 31 430 (31 402) ;
    - 14 077 nombres publiés (14 035) ;
    - exclusions : `not_processed` 27 899 (27 899), `out_of_scope` 1 098 (1 069), `pending_entity` 586 (587) ;
  - contrôles, vue `as_known` : `mismatch` 1 833, `not_testable` 1 340 (1 336), `ok` 29 886, `tautological` 1 393 ;
  - lacunes déclarées :
    - les désignations « an affiliate of OpenAI » et voisines restent en attente (D-0032, point 5). Les baux de SB Energy avec des affiliés d'OpenAI (campus PORTS du comté de Pike, garantie du preneur de Milam) restent donc hors des agrégats d'OpenAI. La garantie de NVIDIA, plafonnée à 105 Md$, y entre par le 8-K de NVIDIA du 17 août 2026, qui nomme OpenAI ; ses reprises du 10-Q de NVIDIA et du S-1/A de SB Energy, qui ne désignent qu'un affilié, restent en attente ;
    - « Uber » reste en attente ;
    - un plafond d'engagement reste un état tant qu'aucune ligne plus récente de l'instrument ne le remplace. Les engagements déjà versés d'Amazon restent donc comptés dans les sorties contractuelles ;
    - Microsoft ne publie que des cumuls : le versement de chaque trimestre n'est pas connu, et F2 ne retire rien pour OpenAI ;
  - tests unitaires : 204, tous passés.
- **D-0060 — OpenAI et Anthropic : faits balisés qui nomment un laboratoire (volet 3) et grand livre par laboratoire (volet 4). Règles fixées avant tout traitement.** (1) Décision de l'utilisateur, le 2026-10-20 : « continue avec les volets 3 et 4 ». Ce sont les volets 3 et 4 du remue-méninges de D-0059 (point 1) : « le laboratoire vu par ses actionnaires », sur les données XBRL déjà en cache, et « un grand livre par laboratoire », du code et un rendu. Lecture séquentielle par l'exécutant, sans sous-agent. Aucune requête réseau ; l'as_of reste le 2026-10-07.

  (2) Constat, fait sur le cache avant ces règles. C'est un inventaire (faits, déposants, concepts, membres) ; aucune mesure n'est calculée :
  - instances des groupes en cache : 72 faits dont un membre de dimension nomme un laboratoire, dans 17 dépôts de 7 groupes. Microsoft 33, Amazon 13, CoreWeave 12, Riot 7, TeraWulf 5, NVIDIA 1, Apollo 1 ; 9 membres distincts. Aucun concept, d'instance ou de `companyfacts`, ne nomme un laboratoire, et aucun libellé ne nomme un laboratoire sous un membre dont le nom ne le nomme pas ;
  - extraits des Notes Data Sets en cache (D-0036, D-0044, D-0058) : 75 faits dans 11 dépôts :
    - 7 faits de 3 dépôts déjà en instance (Apollo, Riot, TeraWulf) ;
    - Cerebras, déposant de la découverte : 47 faits dans 2 dépôts ;
    - quatre déposants hors du graphe : Eightco Holdings (13 faits), Salesforce (4), Zoom Communications (3), Destiny Tech100 (1). Un fait de Zoom porte un membre de complément (« ...OtherThanAnthropic ») ;
  - Riot, 10-Q du 10 août 2026 : le texte ne nomme pas le locataire du bail de Rockdale (« a leading frontier AI lab, (the "Tenant") »). Ses faits balisés le nomment : membre « Lease Agreement With Anthropic Pbc », dont la documentation dit « Represents the information pertaining to Anthropic PBC ». Aucun bloc lu ne porte ce bail ;
  - NVIDIA, 10-Q du 19 novembre 2025 : la ligne de l'engagement d'investir jusqu'à 10 Md$ dans Anthropic a une famille mais pas de type d'arête. Elle n'ouvre donc aucune arête, l'assemblage ignorant une telle ligne. Les lignes valides dans ce cas sont 281 :
    - 157 anonymes, qui n'ouvriraient aucune arête de toute façon ;
    - 124 qui nomment leur contrepartie : Apollo 87 (engagements d'Athene envers Athora et d'autres véhicules surtout), Intel 15 et Micron 11 (Department of Commerce), ASML 5, NVIDIA 4, SK hynix 2. Trois de ces lignes nomment un laboratoire, toutes de NVIDIA ;
  - Apollo, 10-Q du T2 2026 : le fait balisé de 35 Md$ (accord de « capital solution ») porte le membre « Anthropic » sur l'axe des contreparties. Le texte lu nomme Broadcom comme partie à l'accord (« with Broadcom Inc., which facilitates Anthropic, PBC's compute infrastructure expansion »).

  (3) Volet 3, faits balisés qui nomment un laboratoire :
  - faits retenus : ceux des instances des groupes et des extraits des Notes Data Sets en cache dont un membre de dimension nomme un laboratoire. Le nom local du membre, ou la valeur du segment dans les Notes Data Sets, contient « OpenAI », « OPENAI », « Anthropic » ou « ANTHROPIC » comme mot de la casse en chameau : suivi d'une majuscule, d'un chiffre, de « Member » ou de la fin du nom. Même règle pour un concept d'extension (aucun aujourd'hui) ;
  - un membre de complément (« OtherThan », « Excluding », « Except » avant le nom du laboratoire) ne nomme pas le laboratoire : son fait est compté, non retenu ;
  - un fait présent dans l'instance et dans les Notes Data Sets (même dépôt) ne compte qu'une fois, et l'instance l'emporte. Un dépôt des Notes Data Sets sans instance en cache garde ses faits ;
  - laboratoire, par son alias confirmé (règle B de D-0044, point 7) : « OpenAI » désigne `LAB:OPENAI`, « Anthropic » `LAB:ANTHROPIC` ;
  - déposant : son groupe, de `config.yaml` ou de la découverte. Un déposant hors du graphe garde son CIK (`cik:` suivi du CIK) : il n'entre dans aucune paire, arête ni agrégat, et s'affiche à part, comme tiers hors du graphe ;
  - mesure `lab_tagged_value` (rang 2) : une cellule par fait retenu. Valeur et unité telles que balisées, signe compris ; période du fait ; vue `as_known`, date de connaissance égale à la date de dépôt. Ventilation : le concept et les membres de tous les axes ;
  - point de vue du déposant (actionnaire, fournisseur, bailleur, prêteur) : jamais un fait comptable du laboratoire, jamais une valorisation. Aucun ratio, aucune division par un taux de détention, aucun trimestre déduit d'un cumul ;
  - conflit : une ligne valide du même dépôt porte le même montant, sa citation nomme le laboratoire, mais sa contrepartie n'est pas un laboratoire (Apollo et Broadcom). Le fait est alors publié avec la mention du conflit et n'ouvre rien. Deux événements distincts de même montant, chacun avec son laboratoire (les deux extensions de 100 Md$ chez Amazon), ne sont pas un conflit.

  (4) Volet 3, contreparties dérivables par le libellé d'un membre (§2.4) :
  - unités : les paragraphes du document principal qui portent un fait retenu (l'élément balisé de son identifiant), avec deux paragraphes avant et deux après, fondus quand ils se chevauchent (fenêtres de D-0046). Faits candidats : les faits de l'instance balisés dans la fenêtre, avec leurs membres et leurs libellés ;
  - ne sont pas servies, et sont comptées :
    - une fenêtre dont chaque paragraphe porteur figure déjà, mot pour mot aux blancs près, dans un bloc lu du même dépôt ;
    - une fenêtre dont chaque paragraphe porteur est dans la section des facteurs de risque ;
    - un texte identique à une unité déjà retenue ;
    - un fait masqué (`ix:hidden`), sans paragraphe ;
  - montage `labs_tagged`, au catalogue des montages ; ordre du dépôt le plus récent au plus ancien ; plafond de 100 unités. Le volume est consigné ici avant toute lecture ;
  - lecture séquentielle par l'exécutant, sur les conventions de D-0058 et de D-0059. Une contrepartie que le texte ne nomme pas, mais qu'un libellé de membre des faits candidats nomme, est `derivable` (`dimension_member_label`), sous le nom que le libellé écrit (« Anthropic PBC ») ;
  - un bail de capacité porte sa valeur sur la durée initiale en `commitment_unexecuted`, `undiscounted`, au stade `signed`, comme les baux de Hut 8 et de Galaxy. La puissance (MW) va dans la note.

  (5) Lignes de financement sans type d'arête :
  - règle : une ligne de financement qui dit « invest in » (investir dans) une société, sans écrire la forme de l'instrument, prend `equity_primary`. La forme non écrite reste dans la note. Un engagement reste au stade `signed` : aucun versement n'est déduit, et l'arête ne rend pas F active (§3.1) ;
  - elle s'applique aux trois lignes de laboratoire du point 2 : l'engagement de NVIDIA envers Anthropic (stade `signed`) et les deux lettres d'intention de NVIDIA envers OpenAI (stade `intent_non_binding`, arêtes de relation seulement) ;
  - les 278 autres lignes sans type d'arête ne changent pas ici. Elles ouvriraient de nouvelles arêtes chez Apollo, Intel, Micron, ASML et SK hynix : leur traitement relève d'une décision propre de l'utilisateur.

  (6) Volet 4, grand livre par laboratoire :
  - pour chaque laboratoire et chaque groupe qui a une arête avec lui : toutes leurs arêtes non éliminées, regroupées par instrument (`instrument_key`, à défaut l'arête seule), en deux sens, celui des ressources (§3.1) :
    - du partenaire vers le laboratoire : financements, contreparties remises au client, soutiens de crédit, achats du partenaire au laboratoire ;
    - du laboratoire vers le partenaire : achats et engagements d'achat, baux de capacité, financements du partenaire par le laboratoire ;
  - mesure `lab_ledger` (rang 2) : une cellule par instrument, sens, nature de montant et unité. Elle porte le dernier montant admissible connu : date de l'arête (événement, puis fin de période, puis date de connaissance), puis dépôt le plus récent. Avec lui, sa période, sa pièce (accession et formulaire) et le nombre de montants de l'instrument ;
  - un flux reste le « dernier flux publié », jamais une somme. Les états de la paire (au coût, au bilan, à la juste valeur, plafonds d'engagement) viennent de `counterparty_exposure`, quand elle en a ;
  - capacités (MW, GW) : seulement celles des faits balisés retenus au volet 3, en colonne à part. Elles ne s'additionnent ni aux dollars, ni entre elles ;
  - aucun total, ni par partenaire, ni par laboratoire, ni par sens ;
  - une arête sans montant (de relation) s'affiche avec son stade et sa pièce, sans nombre ;
  - point de vue : celui du déposant de chaque pièce. Le grand livre ne dit rien des comptes des laboratoires.

  (7) Ordre et commits :
  - la décision, la configuration (montage `labs_tagged`, mesures), le code et ses tests, un commit ;
  - volet 3 : unités, volume consigné, lecture, lignes de NVIDIA, commit ;
  - volet 4 : grand livre et rendu, commit ;
  - intégration : réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (8) Limites connues avant calcul :
  - seuls les instances et les extraits déjà en cache sont lus. Un dépôt hors de la période des instances, ou des Notes Data Sets sans note qui nomme une cible du lexique d'ensemble, échappe au volet 3 ;
  - un déposant ne balise un laboratoire que sur certains trimestres : une série balisée n'est pas complète, et un trimestre absent n'est pas un zéro ;
  - les capacités écrites seulement dans le texte (les 6 GW d'AMD, par exemple) ne sont pas chiffrées ;
  - le grand livre ne nette pas les engagements déjà versés (D-0059, point 11).

  (9) Volet 3, volume consigné avant toute lecture (2026-10-20) :
  - faits retenus : 139, dont 72 des instances (17 dépôts de 7 groupes) et 67 des Notes Data Sets (8 dépôts sans instance en cache : Cerebras 47, Eightco Holdings 13, Salesforce 4, Zoom Communications 2, Destiny Tech100 1). Le fait de complément de Zoom est compté, non retenu ; les 7 faits des Notes Data Sets déjà en instance s'effacent devant elle ;
  - unités du montage `labs_tagged`, dans les 17 dépôts à instance : 25 fenêtres. 20 sont déjà lues dans un bloc du même dépôt (Microsoft 10, Amazon 4, CoreWeave 3, NVIDIA, TeraWulf et Apollo 1 chacun), et 2 sont des doublons de texte (paragraphe des engagements de Microsoft, identique d'un 10-Q à l'autre). Aucune n'est dans un facteur de risque, et aucun fait n'est masqué ;
  - restent 3 blocs à lire : deux du 10-Q de Riot du 10 août 2026 (bail de Rockdale) et un du 10-Q de Microsoft du 30 avril 2025 (note des placements) ;
  - liste de lecture `labs_tagged`, du dépôt le plus récent au plus ancien.

  (10) Intégration et résultats (2026-10-20) :
  - volet 3, lecture : 3 blocs lus, 5 lignes valides, aucune rejetée :
    - Riot : bail de Rockdale avec Anthropic PBC, contrepartie dérivée du libellé du membre (le texte écrit « a leading frontier AI lab »). 191 MW de charge informatique critique, dont 96 MW à livrer en décembre 2027 ; durée initiale de 20 ans à compter de la livraison complète prévue en juin 2028, deux prolongations de cinq ans ; environ 9,1 Md$ de loyer de base sur la durée initiale ;
    - Riot encore : avenant du bail d'AMD (50 MW, jusqu'à 200 MW), et facilité intermédiaire de 573,0 M$ (Morgan Stanley Senior Funding, agent) qui finance les équipements du bail avec Anthropic ;
    - Microsoft : engagements de 13 Md$ envers OpenAI Global, LLC au 31 mars 2025, le seul trimestre qui manquait ;
  - lignes de NVIDIA (point 5) : trois lignes typées `equity_primary`. La paire NVIDIA → Anthropic apparaît, avec un engagement de 10,0 Md$ au 26 juillet 2026 dans `counterparty_exposure` ;
  - `lab_tagged_value` : 127 cellules (OpenAI 102, Anthropic 25) chez 12 déposants. Sur les 139 faits retenus, 12 reprennent à l'identique (même contexte, même valeur) le fait d'un dépôt antérieur et ne comptent qu'une fois. Un conflit, celui d'Apollo (35 Md$, Broadcom dans le texte) :
    - Microsoft, autres produits et charges balisés sur OpenAI : −1,5 Md$ sur l'exercice 2024 ; −4,8 Md$ sur l'exercice 2025, dont −688 M$, −1,2 Md$ et −768 M$ aux trois premiers trimestres ; −4,1 Md$ au T1 de l'exercice 2026, +10,0 Md$ au T2 (recapitalisation d'OpenAI), −19 M$ au T3, +6,5 Md$ sur l'exercice. S'y ajoutent les versements cumulés (11,6 à 11,9 Md$), les engagements de 13 Md$ sur huit trimestres, la participation (27 %, puis 25 % au 30 juin 2026), la créance de 6,0 Md$ et le revenu de 24,1 Md$ ;
    - Amazon : carnet (RPO) de 38 Md$ d'OpenAI au 31 mars 2026 ; hausse du carnet de 100 Md$ pour OpenAI (T1 2026) et pour Anthropic (T2 2026), écoulée sur environ 10 ans pour Anthropic ; facilité d'Anthropic d'au plus 20 Md$, dont 15 Md$ encore disponibles, expirant 30 mois après un événement de liquidité ;
    - CoreWeave : actif sur contrat de 11,9 Md$ avec OpenAI OpCo, LLC ; 8,75 millions d'actions émises au titre des incitations du contrat ; montants associés, de 350 M$ au total à chaque clôture ;
    - Riot et TeraWulf : baux avec Anthropic (191 MW et 401 MW, 20 ans, deux options de cinq ans) ;
    - NVIDIA : engagement de 10 Md$ envers Anthropic, PBC ;
    - Cerebras : bons d'OpenAI sur 33,4 millions d'actions, dont 5,6 millions acquis au 30 juin 2026 ; prêt de fonds de roulement d'OpenAI de 1,0 Md$ à 6 % (918 M$ au bilan) ; capacité engagée de 750 MW, jusqu'à 2 GW, option sur 1,25 GW ; revenu tiré d'OpenAI de 16,9 M$ au T1 2026 et de 56,8 M$ au T2 ;
    - tiers hors du graphe : Salesforce (Anthropic pèse 22 %, puis 45 %, de ses placements stratégiques ; réévaluations à la hausse de 2,7 Md$ au trimestre et de 3,0 Md$ au semestre clos le 31 juillet 2026), Zoom Communications (titres d'Anthropic de 1 267 M$ au 30 avril 2026), Eightco Holdings (placements liés à OpenAI de 92,6 M$), Destiny Tech100 (un fait de participation) ;
  - `lab_ledger` : 36 cellules pour 10 partenaires à montant ; 15 partenaires en tout (Anthropic 8, OpenAI 7). Les engagements de financement signés, sans montant admissible d'arête, figurent par l'état de la paire (`counterparty_exposure`) ;
  - OpenAI : 118 arêtes (115), dont 69 à montant (69). Anthropic : 76 arêtes (73), dont 57 à montant (56), avec Riot et NVIDIA pour contreparties nouvelles ;
  - paires : 242 (240). Nouvelles : NVIDIA → Anthropic (financement seul) et Riot → Anthropic (structure commerciale seule), toutes deux « causalité non établie ». Conclusions : causalité non établie 162 (160), achats réciproques seulement 44, relation commerciale doublée d'un financement 26, dépendance documentée 10 ;
  - cycles (E.6) : 106 (106). Annexe F : 399 événements, aucun nouveau, aucun disparu. E.7 : 170 issues, 56 % indéterminées, discrimination possible ; E.1 : étayé 3, non étayé 71, indéterminé 11, tous inchangés ;
  - rendus :
    - tables : documents 25 104 (25 104), faits 1 581 118 (1 581 051, dont 67 faits `nds_num`), observations 29 269 (29 264), entités 3 576 (3 576), liens 10 992 (10 984), mesures 171 994 (171 569), contrôles 69 952 (69 950), exclusions 31 430 (31 430) ;
    - 14 519 nombres publiés (14 077) ;
    - exclusions inchangées, motif par motif ;
  - contrôles, vue `as_known` : `mismatch` 1 833, `not_testable` 1 342 (1 340), `ok` 29 886, `tautological` 1 393 ;
  - lacunes déclarées :
    - les 278 autres lignes de financement sans type d'arête (point 5) n'ouvrent toujours aucune arête. Leur traitement attend une décision ;
    - Riot balise sa puissance en MWh et TeraWulf un nombre d'options en dollars : les valeurs se publient telles que balisées, avec l'unité signalée. Un fait sans valeur d'Eightco s'affiche « n.d. » ;
    - Microsoft ne balise OpenAI qu'à partir de ses dépôts de l'exercice 2025 (comparatif de 2024 compris). Alphabet, AMD et Oracle ne balisent aucun laboratoire dans les instances en cache ;
    - les extraits des Notes Data Sets ne gardent que les dépôts dont une note nomme une cible du lexique : les séries des tiers sont partielles ;
    - l'engagement de 50 Md$ d'Amazon envers OpenAI compte encore les montants déjà versés (D-0059, point 11) ;
  - tests unitaires : 218, tous passés.
- **D-0061 — Lignes de financement sans type d'arête : la règle de D-0060 (point 5) appliquée aux 278 autres lignes. Règles fixées avant tout traitement.** (1) Décision de l'utilisateur, le 2026-10-20 : « Oui applique la même règle ». Elle répond à la question posée avec le rapport de D-0060 : appliquer la règle du point 5 aux 278 lignes valides qui ont une famille mais pas de type d'arête, ou les laisser telles quelles. Aucune requête réseau ; l'as_of reste le 2026-10-07.

  (2) Constat, sur les 278 lignes (D-0060, point 2) :
  - 121 nomment leur contrepartie : Apollo 87, Intel 15, Micron 11, ASML 5, SK hynix 2, NVIDIA 1 ;
  - 157 sont anonymes : Blackstone 68, Apollo 52, Blue Owl 21, ASML 8, SK hynix 3, Applied Digital 2, Broadcom 2, Riot 1 ;
  - par catégorie de la matrice d'exposition : 224 engagements non appelés, 8 indemnisations, 5 intérêts dans une entité à intérêts variables, 3 programmes de financement fournisseur, 1 autre, 37 sans catégorie.

  (3) Règles :
  - une ligne prend le type que son texte écrit : actions, bons, apports en capital, participation : `equity_primary` ; dette, billets, prêt : `loan_or_facility` ; billets convertibles : `convertible_or_safe` ; indemnisation (ASC 460) : `guarantee` ;
  - une ligne qui dit « invest in », « investments in », « capital commitments », « capital funding commitments » ou « capital contributions », sans écrire la forme de l'instrument, prend `equity_primary` (D-0060, point 5). La forme non écrite reste dans la note ; pour PK AirFinance, Athene détient par ailleurs des obligations senior, ce que la note rappelle ;
  - une ligne d'entité à intérêts variables qui décrit une participation détenue (Carl Zeiss SMT Holding chez ASML, 24,9 %) prend `equity_primary`, avec le déposant pour payeur et l'entité pour receveur (D-0015) ;
  - une ligne qu'aucun type de §3.1 ne décrit, la liste étant limitative, n'ouvre pas d'arête et reste telle quelle :
    - subventions et aides du CHIPS Act et leurs clauses (Intel, Micron, SK hynix) ;
    - partage des flux d'une subvention ;
    - accords de développement conjoint et contrat d'exploitation (Intel et Tsinghua Unigroup, Micron et Intel) ;
    - licence croisée de brevets (SK hynix et Rambus) ;
    - programmes de financement fournisseur, hors du graphe par §3.1 (SK hynix) ;
    - dérivés sur actions achetés à des banques (options plafonnées et rachat à terme prépayé d'Applied Digital) ;
  - une ligne anonyme prend aussi son type, par cohérence ; elle n'ouvre aucune arête (§2.4) ;
  - le stade ne change pas : un engagement reste `signed`, aucun versement n'est déduit, et il ne rend pas F active (§3.1) ;
  - chaque ligne modifiée garde ses autres champs ; sa note reçoit la mention du type et de la règle (« D-0061 »).

  (4) Ordre : la décision ; les lignes modifiées ; un réassemblage ; les rendus ; les résultats ici ; tests, commit, push, rapport.

  (5) Correction liée, constatée au premier réassemblage. Les engagements trimestriels d'un même engagement (Athene envers un véhicule, AAM envers Athora) n'avaient pas de clé d'instrument : `counterparty_exposure` additionnait donc chaque trimestre comme un engagement distinct (Atlas : 16,2 Md$, somme de huit trimestres, au lieu de 1,3 Md$ au 31 mars 2026). Un engagement est un état : seule compte sa dernière valeur connue. Chaque série reçoit donc une clé commune, par porteur et par contrepartie :
  - `apo:athene_commitment_<véhicule>` pour les engagements d'Athene (ADIP, Athora, Atlas, PK AirFinance, Skylign, Venerable, Wheels) ;
  - `apo:aam_equity_commitment_athora` pour les engagements de souscription d'AAM envers Athora, expiration du 1er avril 2025 comprise ;
  - les engagements conditionnels du 3 juillet 2025 gardent leur clé.

  (6) Résultats (2026-10-20) :
  - 245 lignes typées :
    - `equity_primary` 234 : Apollo 139, Blackstone 68, Blue Owl 21, ASML 5, NVIDIA 1 ;
    - `guarantee` 8 (ASML), `loan_or_facility` 2 (Broadcom), `convertible_or_safe` 1 (Riot) ;
  - 33 lignes restent sans type, aucun type de §3.1 ne les décrivant : Intel 15, Micron 11, SK hynix 5, Applied Digital 2 ;
  - 83 lignes d'Apollo reçoivent une clé d'instrument (point 5) ;
  - arêtes : 11 085 (10 992), soit 93 de plus. Les 152 lignes anonymes typées n'en ouvrent aucune :
    - 39 vont vers des contreparties résolues : d'Apollo vers Atlas Securitized Products Holdings (8), PK AirFinance (9), Skylign Aviation Holdings (4), Venerable Holdings (1) et Wheels (11) ; d'ASML vers Carl Zeiss SMT Holding (5) ; de NVIDIA vers Intel (1) ;
    - 54 vont vers des noms en attente : Athora 46, ADIP 7, Wheels Donlen 1. Aucun bloc lu ne définit « Athora » par extrait ; « ADIP » désigne une série de fonds, « Wheels Donlen » deux sociétés réunies. Ces noms restent en attente (D-0021) ;
  - paires : 242 (242), aucune nouvelle. Les 7 paires touchées gagnent des arêtes, mais gardent leur structure et leur conclusion :
    - Apollo et ses cinq véhicules : financement seul, causalité non établie ;
    - ASML → Carl Zeiss SMT Holding : relation commerciale doublée d'un financement ;
    - NVIDIA → Intel : financement seul, causalité non établie ;
  - `counterparty_exposure` : 6 états nouveaux d'engagements non appelés, chacun à sa dernière valeur :
    - Apollo envers Atlas, 1,3 Md$ (31 mars 2026) ; Skylign, 159 M$ (30 septembre 2025) ; Venerable, 169 M$ (30 juin 2025) ; Wheels, 56 M$ (30 juin 2026) ; PK AirFinance, 40 M$ (30 septembre 2024, dernière valeur publiée) ;
    - NVIDIA envers Intel, 5,0 Md$ ;
    - avant la correction du point 5, les mêmes cellules additionnaient les trimestres : Atlas 16,2 Md$, PK AirFinance 9,4 Md$, Wheels 687 M$, Skylign 280 M$ ;
  - statut F, annexe F (399 événements), cycles (106), contrôles et exclusions : inchangés, un engagement signé ne rendant pas F active. E.7 : 170 issues, 56 % indéterminées, discrimination possible ; E.1 inchangé (étayé 3, non étayé 71, indéterminé 11) ;
  - rendus :
    - tables : liens 11 085 (10 992), mesures 172 000 (171 994) ; les autres tables sont inchangées ;
    - 14 531 nombres publiés (14 519) ;
  - lacunes déclarées :
    - les 33 lignes sans type (point 3) n'ouvrent toujours aucune arête ;
    - Athora, ADIP et Wheels Donlen restent en attente : les 54 arêtes qui les visent n'entrent dans aucune paire ;
    - le type `equity_primary` par défaut ne dit pas la forme réelle d'un engagement d'investir ;
    - un engagement sans valeur récente garde sa dernière valeur publiée (PK AirFinance ; D-0059, point 11) ;
  - tests unitaires : 218, tous passés.
- **D-0062 — Réassemblage plus rapide, mêmes tables à l'octet près : travail répété supprimé, mémo des citations, mémo des étapes qui ne lisent pas les observations, mode aperçu.** (1) Décision de l'utilisateur, le 2026-10-20 : « Fais les pistes 1, 2, 3 et 4 ». Elle répond au remue-méninges demandé le même jour (« il y a pas moyen de faire le réassemblage de manière plus intelligentes et astucieuse pour éviter les 40 min à chaque fois ? Reste en mode brainstorming »), fondé sur un profil par échantillonnage d'un réassemblage complet : 33 min 52 s, et des tables identiques à l'octet près à celles du dépôt, ce qui établit que le calcul est déterministe. Aucune règle de mesure ne change, aucune requête réseau ; l'as_of reste le 2026-10-07.

  (2) Constat du profil (2 031 s) : huit endroits où le code refaisait le même travail font les trois quarts du temps :
  - relocaliser les citations à la validation, 603 s : chaque ligne décompressait son document et y cherchait sa citation dans le HTML brut (25 438 lignes, 3 893 documents) ;
  - valeurs trimestrielles, 248 s : chaque valeur demandée filtrait toute la série en Python, et les mêmes valeurs revenaient ;
  - tableaux par axe des contrôles C11 et C12, 241 s : la présentation d'un dépôt était triée de nouveau pour chaque axe ;
  - état de la recherche des paires, 175 s : la file de la découverte était filtrée à chaque trimestre, alors que la réponse ne dépend que du couple fournisseur et contrepartie ;
  - positions des BDC, 86 s : chaque identifiant comparé à tous les noms du registre ;
  - texte des blocs, 64 s : normalisé une fois par ligne ;
  - insertions dans DuckDB ligne à ligne, 58 s ; config.yaml relu à chaque appel, 29 s.

  (3) Exception à P1, décidée par l'utilisateur. P1 veut que seuls le réseau et la lecture soient incrémentaux, le reste recalculé à chaque exécution. Les pistes 2 et 3 gardent d'une exécution à l'autre des résultats de calcul. La garantie reste celle de §9.6 : le mémo est un cache de calculs déterministes, sa clé porte toutes leurs entrées, et `--sans-cache` recalcule tout et donne les mêmes tables.

  (4) Piste 1, même calcul sans le travail répété. Chaque correction a été comparée à l'ancien calcul sur les données réelles :
  - citations cherchées document par document, chacune dans un document décompressé et décodé une fois : 29 269 lignes identiques, plages comprises ;
  - texte du bloc normalisé une fois par bloc, et non une fois par ligne ;
  - valeurs trimestrielles mémorisées pour la vie de la série et cherchées par positions, sans extraire de sous-table : 80 906 cellules identiques, 282 s → 48 s ;
  - présentation d'un dépôt triée une fois pour tous les axes : 4 418 contrôles identiques, 299 s → 55 s ;
  - état de la recherche calculé une fois par couple ;
  - positions des BDC : seuls les noms dont le premier mot figure dans l'identifiant se testent : 301 260 identifiants, mêmes rattachements, 88 s → 2 s ;
  - insertions d'un bloc dans DuckDB ; config.yaml lu une fois par version du fichier, chaque appel recevant sa copie ;
  - noms d'un groupe pour les paires sans recherche quadratique.
  Constat lié : l'ordre physique de `concept_map` variait déjà d'une exécution à l'autre (UNION de DuckDB sans ordre) ; le contenu est le même, et les tables n'en dépendent pas.

  (5) Piste 2, mémo des plages de citations (`db/memo/quote_ranges.json`, hors suivi). Une plage ne dépend que du document en cache, du début du bloc, de la citation et du code qui la cherche. La clé porte la taille et la date de modification du document ; le mémo porte l'empreinte de `textnorm.py`, de `cache.py` et de la classe `QuoteRanges`. Un document ou un code modifié se recherche. Le mémo ne garde que les clés de la dernière exécution. Validation des observations : 563 s sans mémo, 20 s avec.

  (6) Piste 3, mémo des étapes qui ne lisent pas les observations (`pipeline/memo.py`, `db/memo`) :
  - étapes : base XBRL (copie du fichier DuckDB), mesures tirées des faits, rattachement des positions des BDC (clé : lignes du registre), contrôles (clé : faits ajoutés en cours d'exécution, positions des BDC et Notes Data Sets des laboratoires), blocs `lender_portfolio`, `lender_liabilities` et `nport`, documents (clé : accessions utilisées), dénominations d'EDGAR ;
  - empreinte des entrées : code de `pipeline/` hors rendu et aperçu, `schema.sql`, versions de Python et des bibliothèques, `config.yaml`, fichiers de `db/` hors bases et mémo, de `work/` hors observations et fichiers temporaires, arbre du cache. Seules les observations peuvent donc changer pour qu'une étape soit reprise ; tout autre changement la recalcule ;
  - deux entrées gardées par étape ; `python -m pipeline.assemble 2026-10-07 --sans-cache` recalcule tout et réécrit le mémo.

  (7) Piste 4, aperçu : `python -m pipeline.assemble 2026-10-07 --apercu`. Le même code que l'assemblage jusqu'aux paires, à l'exposition, au grand livre des laboratoires, aux cycles et à l'annexe E, puis les invariants d'agrégat et l'univers attendu. Il reprend du mémo les mesures tirées des faits sans les comparer, une mesure comparée pouvant en avoir (`exposure_matrix`), et saute les signaux, l'annexe F, les contrôles et l'export. Il travaille sur sa propre base (`db/apercu.duckdb`, effacée ensuite) et n'écrit rien dans `tables/`. Il compare les arêtes et les mesures qu'il calcule aux tables, à l'octet près des types, et écrit le détail dans `work/tmp/apercu.json`. Il ne remplace pas le réassemblage complet, seul à écrire les tables.

  (8) Vérifications, toutes à l'octet près sur les huit tables :
  - trois réassemblages complets à mémo des étapes vide : tables identiques à celles du dépôt ;
  - réassemblage repris du mémo, les dix étapes reprises : identiques ;
  - observations remises à leur état d'avant D-0061 (065e155), mémo calculé sur les observations courantes : tables identiques à celles du dépôt à 065e155, calculées par l'ancien code sur les mêmes observations ; observations rétablies ensuite ;
  - réassemblage `--sans-cache`, rien repris, toutes les citations recherchées : identiques ;
  - aperçu : aucun écart sur l'état courant (8 326 arêtes, 21 mesures) ; sur les observations d'avant D-0061, il retrouve les changements de D-0061 : 93 arêtes en moins, 6 états de `counterparty_exposure` en moins, 7 paires dont seules les preuves changent ;
  - l'ordre de deux listes intermédiaires variait déjà d'une exécution à l'autre (`concept_map`, issue d'une UNION de DuckDB ; dépôts annuels de C8, issus d'un SELECT DISTINCT) : le contenu est le même, et l'export trie chaque table par sa clé.

  (9) Durées (réassemblage complet, 2026-10-20) :
  - avant : 33 min 52 s (2 031 s) ;
  - mémo des étapes vide, plages des citations en mémo : 9 min 15 s à 10 min 49 s, contre 33 min 52 s ;
  - mémo plein, seules les observations ayant pu changer : 2 min 10 s, et 2 min 20 s avec les observations d'avant D-0061 ;
  - `--sans-cache` : 18 min 9 s, dont 9 min 23 s pour rechercher toutes les citations ;
  - aperçu : 61 à 63 s.

  (10) Limites :
  - un changement de `config.yaml` ou du code de `pipeline/` (hors rendu et aperçu) recalcule toutes les étapes du mémo : environ 10 min ;
  - la première exécution sans mémo des citations les recherche toutes : environ 9 min de plus ;
  - le rendu (11 min) n'est pas touché ;
  - tests unitaires : 231, tous passés.
- **D-0063 — Rendu plus rapide, mêmes fichiers : tables lues en mémoire, requêtes répétées regroupées, ordre fixé de deux requêtes qui n'en avaient pas.** (1) Décision de l'utilisateur, le 2026-10-20 : « Oui occupe-toi aussi du rendu ». Elle répond au rapport de D-0062, qui proposait la même méthode pour le rendu (11 min). Aucune règle de rendu ne change, aucune requête réseau ; l'as_of reste le 2026-10-07.

  (2) Constat du profil (667 s, soit 11 min 11 s) : 596 s dans les requêtes DuckDB. Les huit tables étaient des vues sur les fichiers Parquet, et chaque requête relisait et décompressait le fichier : 22 ms pour une requête ponctuelle sur `measures`. Les postes :
  - `audit/numbers.csv`, 304 s : quatre requêtes par nombre publié (14 531) ;
  - `series.md`, 137 s, et la section des fragilités, 56 s : une requête `one()` par case de tableau, environ 15 000 ;
  - rendement du bloc text, 65 s : une requête comparait chaque arête à chaque ligne par `LIKE '%…%'`, environ 240 millions de comparaisons ;
  - statistiques du catalogue, 40 s : le catalogue entier relu.

  (3) Corrections, même résultat :
  - les tables sont chargées en mémoire une fois, dans l'ordre du fichier : 22 ms → 2,6 ms par requête ponctuelle ;
  - `one()` lit un index construit au chargement : la première ligne de la table pour sa clé, comme la requête, et chaque appel reçoit sa copie ;
  - `numbers_csv` lit les cellules, les preuves des liens, les faits et les observations d'un bloc, une requête par table ; l'ordre des termes ne change pas ;
  - arêtes citées par le bloc text : les clés des lignes se cherchent par leur préfixe commun, avec la sémantique de sous-chaîne du `LIKE` ; si une clé contient un caractère spécial de `LIKE`, la requête d'avant s'applique ;
  - statistiques du catalogue reprises du mémo de D-0062 tant que le catalogue, la configuration, le code et la liste des fichiers d'observations ne changent pas.

  (4) Ordre fixé, constat lié. Deux requêtes sans `ORDER BY` rendaient leurs lignes dans l'ordre de DuckDB, qui varie d'une exécution à l'autre :
  - les groupes d'une même entité dans « Appartenances datées » (VMware, Inc., groupes Broadcom et Dell) : le rendu de l'ancien code, profilé le 2026-10-20, les a sortis dans l'ordre inverse de celui du dépôt ;
  - les arêtes du grand livre des laboratoires, dont la dernière de chaque instrument s'affiche.
  Elles prennent l'ordre de la clé du groupe et de celle du lien, qui est aussi celui du dernier rendu du dépôt.

  (5) Vérifications, sur les mêmes tables :
  - `synthesis.md`, `delta.md`, `series.md` et les fichiers de `audit/` sont identiques à l'octet près à ceux de l'ancien code, hormis la ligne de VMware (point 4) ;
  - ils sont identiques à ceux du dépôt, hormis `delta.md`, qui prend les décisions D-0062 et D-0063 et la durée du dernier assemblage ;
  - deux rendus successifs donnent les mêmes fichiers ;
  - 4 tests d'équivalence (`tests/test_render_speed.py`) : l'index de `one()` contre la requête, `numbers_csv` contre son ancienne version, les arêtes citées contre la requête `LIKE`, une clé contenue dans une autre comprise ; 235 tests passés.

  (6) Durées :
  - rendu : 11 min 11 s → 36 s à mémo du catalogue vide, 24 à 30 s ensuite ;
  - cycle après une lecture : réassemblage 2 min 15 s et rendu 30 s, contre 33 min 52 s et 11 min 11 s ;
  - après un redémarrage de la machine, le premier réassemblage prend 4 min, le cache disque étant vide.
- **D-0064 — OpenAI et Anthropic : la chaîne de calcul d'Anthropic dans les 8-K (volet 7) et les lettres de commentaires de la SEC (volet 6). Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-20 : « Ok, on repart sur Anthropic et OpenAI. Fais les volets 7 et 6 ». Ce sont deux volets du remue-méninges de D-0059 (point 1) :
  - volet 7, montage « chaîne d'Anthropic », « l'équivalent de Stargate ». Fluidstack au centre (sites de TeraWulf et de Cipher garantis par Google, piste Hut 8, autres hébergeurs), puis les TPU de Google, l'infrastructure d'Amazon et Azure, par une recherche plein texte « Fluidstack » et « Anthropic » dans les 8-K et leurs pièces ;
  - volet 6, lettres de commentaires de la SEC (CORRESP et UPLOAD) : le personnel y demande à un déposant comment il comptabilise son lien avec un laboratoire.

  Le volet 7 passe d'abord, puis le 6. Lecture séquentielle par l'exécutant, sans sous-agent. Réseau : le client SEC unique et journalisé, au plus 4 requêtes par seconde, jamais deux processus réseau en parallèle, une pause d'au moins 10 minutes après un 403. L'as_of reste le 2026-10-07 : la recherche s'arrête à cette date, et aucun document déposé après n'est lu.

  (2) Constat, compté sans lecture sur les tables de D-0063 :
  - Anthropic : 76 arêtes, dont 57 à montant. Amazon 64, Akamai 3, TeraWulf 3, Riot 2, puis NVIDIA, SpaceX, Broadcom et Nscale, 1 chacun. Aucune avec Alphabet ni Microsoft. La première est du 2023-09-30 ;
  - Fluidstack : 36 lignes valides (TeraWulf 16, Cipher 15, Hut 8 5) et 30 arêtes, dont 4 à montant. Elles se répartissent sur six dénominations tenues pour des contreparties distinctes, qu'aucun extrait ne relie encore : Fluidstack Ltd et cinq sociétés américaines (Fluidstack USA I à IV, Fluidstack CS I). 13 sont des garanties d'Alphabet (`credit_support`, `backstop`), les autres des baux de capacité des hébergeurs. La première est du 2025-08-13 ;
  - aucune arête ne relie Fluidstack à Anthropic. Deux lignes descriptives de Hut 8 nomment ensemble les deux sociétés (partenariat de décembre 2025).

  (3) Volet 7, montage `anthropic_chain`, tiré de la recherche plein texte sur les règles du montage Stargate (D-0058, points 7 et 20) :
  - période : du 2023-01-01, neuf mois avant la première arête d'Anthropic, à l'as_of ;
  - requêtes, sur les formulaires racines 8-K et 8-K/A, pièces comprises (paramètre `forms`) : « "Fluidstack" », puis « "Anthropic" » croisé avec « "data center" », « "compute" », « "megawatts" », « "gigawatt" », « "TPU" », « "Trainium" », « "Azure" », « "Google Cloud" » et « "Amazon Web Services" » ;
  - termes qualifiants, en mots entiers. « Fluidstack », dans les casses « Fluidstack », « FluidStack », « fluidstack » et « FLUIDSTACK », jamais dans une pièce d'un déposant à son nom. « Anthropic » et « ANTHROPIC », sauf suivis de « Capital » (D-0041). Sont seulement comptés : Google, Alphabet, Amazon, AWS, Microsoft, Azure, NVIDIA, TPU, Trainium, Project Rainier et OpenAI ;
  - unités : les fenêtres du bloc `montages`, soit le paragraphe qualifiant, les deux qui le précèdent et les deux qui le suivent, fondues quand elles se chevauchent ;
  - ne sont pas servies, et sont comptées :
    - une fenêtre dont chaque paragraphe qualifiant figure déjà, mot pour mot, dans un bloc lu du même dépôt ;
    - une fenêtre dont chaque paragraphe qualifiant est dans la section des facteurs de risque (`out_of_scope`) ;
    - un texte identique à une unité retenue ;
  - ordre, par classes, chacune du plus récent au plus ancien :
    - d'abord les fenêtres qui nomment Fluidstack ;
    - puis celles qui nomment l'infrastructure : centre de données, MW, GW, TPU, Trainium, calcul, capacité, colocation, hébergement, nuage, bail ;
    - puis les autres ;
  - plafond de 80 fenêtres distinctes. Au-delà, une fenêtre d'un dépôt d'un groupe suivi se lit par le catalogue du groupe (D-0053, point 7). Les autres sortent en `not_processed`, et le rendement est présenté avant d'aller plus loin ;
  - niveau de preuve, par le triplet (§2.1, §2.3), comme dans le registre des documents. Le type de pièce et les items viennent de la recherche :
    - un contrat (EX-10, EX-4, EX-2) est de niveau D ;
    - une pièce EX-99 est furnished, de niveau E ;
    - un document principal dont les items sont tous 2.02, 7.01 ou 9.01 est furnished, de niveau E ;
    - le reste est filed, de niveau C.

    Un communiqué n'est donc pas la preuve d'un montant : sa ligne garde le montant, et son arête n'est qu'une relation.

  (4) Volet 6, montage `sec_letters` :
  - période : du 2019-01-01 à l'as_of ;
  - requêtes « "OpenAI" » et « "Anthropic" », sur les formulaires CORRESP et UPLOAD ;
  - termes qualifiants : « OpenAI » et « OPENAI », puis « Anthropic » et « ANTHROPIC », sauf suivis de « Capital » ;
  - une lettre en PDF (UPLOAD) se lit par son texte extrait (pypdf, mode « layout »), en paragraphes. Une ligne vide, une fin de page ou un commentaire numéroté (« 1. ») ouvre un paragraphe. Un PDF illisible ou sans texte (image numérisée) sort en `out_of_scope`, avec son motif ;
  - niveau E, `correspondence` : une lettre n'est ni filed ni furnished. Elle oriente la lecture et n'est jamais la source d'un montant (§2.1) ;
  - plafond de 60 fenêtres distinctes, du plus récent au plus ancien. Fenêtres et exclusions comme au point 3 ;
  - si la recherche ne rend aucune lettre, ce point le dit et le volet s'arrête.

  (5) Lecture, sans sous-agent, sur les conventions de D-0058 (point 22) et de D-0059 (point 4) :
  - pas d'inférence : un client, un locataire ou un garant anonyme reste anonyme, même si la presse le nomme. Un projet ou un site n'est pas une personne morale ;
  - une relation entre tiers rapportée par un déposant qui n'y est pas partie est une ligne descriptive. Une annonce, une lettre d'intention ou un protocole d'accord non contraignant porte `intent_non_binding` ;
  - les relations des entités du modèle trouvées dans un bloc servi sont relevées, même hors d'Anthropic. Celles de tiers hors du modèle reçoivent `out_of_scope_content` ;
  - une lettre (volet 6) ne donne que des lignes descriptives, sans famille ni montant, donc aucune arête :
    - la note dit qui écrit (le personnel ou la société), la date, le dépôt visé et la question comptable : mise en équivalence, entité à intérêts variables, consolidation, juste valeur, concentration, comptabilisation du revenu ;
    - une lettre qui renvoie à un dépôt (« see Note 5 », « we will revise our disclosure in future filings ») le dit dans la note. Ce dépôt n'est pas tiré dans ce volet ;
  - données personnelles (D-0051 ; D-0058, point 10) : aucune personne physique n'est contrepartie ni citée. Les lettres portent les noms du personnel de la SEC, des dirigeants et des conseils, qui ne sont jamais cités. Une fenêtre qui n'est qu'adresse, signature ou contact reçoit une abstention.

  (6) Entités, à l'intégration et après la lecture : par extrait seulement (D-0044, point 7, règles A et B ; D-0050, points 4 et 5) :
  - une société de Fluidstack (Fluidstack USA I à IV, Fluidstack CS I) ne rejoint Fluidstack Ltd que par un extrait qui affirme le lien. Sans extrait, elle reste une contrepartie propre ;
  - un alias ne naît que d'un extrait qui le définit (D-0021) ;
  - une participation n'est pas une appartenance.

  (7) Code, avant tout tirage :
  - `montages` :
    - formulaires racines par requête (`forms`), consignés au journal des requêtes ;
    - classes de lecture (`priority`) ;
    - niveau par le triplet (`evidence: triplet`), avec les items et le type de pièce gardés depuis la recherche ;
    - texte des PDF (`pdf_text`), pour le seul montage `sec_letters` ;
    - libellé d'un terme dans les exclusions (`label`) ;
  - `discovery.form_evidence` : CORRESP, UPLOAD et DRSLTR au niveau E, `correspondence` ;
  - correction de l'export. D-0058 (point 20) veut qu'une fenêtre d'un montage tiré de la recherche, écartée comme facteur de risque, sorte en `out_of_scope`. L'export ne le faisait que pour les montages de corpus : les 3 fenêtres de Stargate y entrent au prochain réassemblage ;
  - écart connu, laissé en l'état. Les blocs des montages d'avant ne sont pas préparés de nouveau et gardent le niveau de leur formulaire. Ainsi 39 pièces EX-99 de 8-K (Stargate 28, Galaxy Helios 11) restent de niveau C, quand le registre les classe furnished, de niveau E. Quatre arêtes à montant de Galaxy Helios en viennent : trois baux de CoreWeave (4,5 Md$, 10,4 Md$, 100 M$) et un financement de 434 M$. L'écart est présenté à l'utilisateur ;
  - tests : 8 de plus (`test_montages`).

  (8) Ordre et commits :
  - la décision, la configuration et le code, avec les tests ;
  - volet 7 : recherche, tirage, unités, liste de lecture, volume consigné ici avant toute lecture, commit. Puis lecture, commits par lot, rendement consigné ;
  - volet 6, de même ;
  - intégration : entités par extrait, réassemblage (sans mémo des étapes, le code ayant changé), rendus, résultats ici, tests, commit, push, rapport.

  (9) Limites connues avant calcul :
  - Anthropic ne dépose rien : tout ce qui s'en lit vient de ses contreparties ;
  - le volet 7 ne lit que les 8-K et leurs pièces. Un 10-Q ou un 10-K d'un déposant hors des groupes n'est pas cherché ;
  - la recherche plein texte ne trouve que le texte qu'EDGAR indexe : une lettre numérisée sans texte n'est pas trouvée ;
  - une lettre décrit une question et une réponse, pas un fait comptable. Elle ne change aucune mesure.

  (10) Volet 7, amendement et volume, après le premier décompte et avant toute lecture (2026-10-20) :
  - amendement de la requête. Le service de recherche applique « 8-K/A » au formulaire du dépôt et « 8-K » à sa forme racine, puis combine les deux filtres par un ET. La première recherche, avec « 8-K,8-K/A », ne visait donc que les 8-K/A : 0 résultat pour les dix requêtes, consignées au journal. La forme racine « 8-K » couvre les 8-K et leurs amendements : les dix requêtes portent `forms=8-K`. Le périmètre du point 3 ne change pas ;
  - recherche : 71, 43, 62, 2, 5, 1, 12, 12, 19 et 15 résultats pour les dix requêtes, soit 242 résultats, 164 pièces distinctes dans 133 dépôts, du 2023-03-10 au 2026-10-05, aucun 8-K/A. 135 pièces sont tirées et 29 étaient déjà en cache. Les 135 requêtes ont toutes le statut 200, avec au plus 5 départs par seconde glissante ;
  - volume, avant lecture : 277 fenêtres. 49 sont déjà dans un bloc lu du même dépôt, aucune n'est dans un facteur de risque. Restent 228 fenêtres et 225 textes distincts (3 doublons). Une pièce n'a aucune fenêtre (rapport annuel intégré de Leonardo DRS). Par classe : 120 textes nomment Fluidstack, 61 l'infrastructure, 44 aucune des deux ;
  - les 80 blocs servis, au plafond, nomment tous Fluidstack. Ils font 253 598 caractères et vont du 2026-09-25 au 2025-11-10 :
    - déposants : TeraWulf 34, Cipher 28 (sous ses deux dénominations, Cipher Mining et Cipher Digital), Hut 8 13, Willow Lane Acquisition 2, AIB Data Centers, IREN et Blue Acquisition 1 chacun ;
    - trois actes d'émission (EX-4.1) en donnent 35 : TeraWulf du 2025-12-29 (19), Cipher Mining du 2025-11-13 (13), Hut 8 du 2026-05-01 (3) ;
    - niveaux : 40 E (communiqués et présentations furnished), 35 D (les actes d'émission), 5 C (documents principaux de 8-K) ;
  - au-delà du plafond, 145 fenêtres : 40 nomment Fluidstack (du 2025-01-08 au 2025-11-10 ; TeraWulf 27, Cipher 11, IREN et Soluna 1 chacun), 61 l'infrastructure, 44 aucune des deux. 78 viennent de dépôts de groupes suivis (TeraWulf 29, Amazon 22, Cipher 12, AMD 5, Akamai, CoreWeave, Microsoft et NVIDIA 2 chacun, IREN et Dell 1 chacun) et sortent comme lues par le catalogue du groupe (D-0053, point 7) ; 67 sortent en `not_processed`. Le rendement des 80 blocs est présenté avant d'aller plus loin (point 3) ;
  - liste de lecture `anthropic_chain`, dans l'ordre du montage.

  (11) Volet 7, lecture, sans sous-agent (2026-10-20) :
  - règles de codage, en plus du point 5 :
    - un communiqué ou une présentation qui reprend un fait déjà codé depuis un dépôt du même déclarant reçoit `duplicate_of_other_block`, même quand son texte diffère. Seul un fait ou un montant absent des lignes déjà lues fait une ligne ;
    - un acte d'émission ne donne une ligne que pour une définition ou une clause qui porte un fait nouveau (date, partie, mécanisme). Ses tables, renvois et clauses types sont des abstentions ;
    - un alias défini dans un acte ne vaut que dans ce document : « Fluidstack » désigne Fluidstack Ltd. dans l'acte de Flash Compute (TeraWulf) et Fluidstack USA II Inc. dans celui de Cipher Compute ;
    - le client aval en colocation de Fluidstack, que les actes d'émission nomment « Downstream Customer », reste anonyme ;
    - aucune personne physique n'est citée : déclarations de dirigeants, coordonnées et transcriptions sont écartées. Le contrôle des noms, refait à la fin de la lecture, n'en trouve aucun dans les lignes ;
  - rendement : 80 blocs, 90 lignes (38 observations, 52 abstentions), aucune rejetée :
    - 16 lignes à famille : 7 baux de capacité, 4 garanties de Google sur des obligations de Fluidstack, 2 garanties d'Amazon.com, Inc. pour Cipher, un apport de TeraWulf à la coentreprise d'Abernathy, les bons de Fluidstack remis à Google et un contrat de services d'exploitation prévu à River Bend. 12 portent un montant. Leurs pièces sont pour la plupart furnished (niveau E) : les montants restent dans les lignes, et leurs arêtes ne sont que des relations ;
    - 22 lignes descriptives, dont un extrait d'appartenance ;
    - abstentions : 28 `duplicate_of_other_block`, 17 `boilerplate_no_event`, 5 `no_relevant_content`, 1 `out_of_scope_content`, 1 `no_named_counterparty` ;
  - faits principaux :
    - Anthropic : bail de 20 ans de TeraWulf à Justified (Hawesville, Kentucky), environ 401 MW et environ 19 Md$ sur la durée initiale (communiqués du 2026-07-06 et du 2026-08-05). Les lignes du 8-K et du 10-Q déjà lus n'avaient pas de montant ;
    - Fluidstack, baux des hébergeurs : Lake Mariner environ 6,7 Md$ (trois baux de dix ans, août 2025) ; Barber Lake environ 3,8 Md$, dont environ 830 M$ pour l'extension de novembre 2025 ;
    - Fluidstack, autres relations : Fluidstack Ltd. a émis le 26 septembre 2025, au profit de Google, des bons sur jusqu'à 7 786 250 de ses actions, liés au projet d'Abernathy (acte de Flash Compute, contrat déposé). Fluidstack achète pour 127 M$ de calcul sur deux ans à Boost Run (décembre 2025) et est client d'IREN (juillet 2026) ;
    - Google : garanties chiffrées de 3,2 Md$ à Lake Mariner (600 M$ devenus effectifs à la livraison de CB-3, en juillet 2026) et de 1,73 Md$ à Barber Lake. Google doit reprendre le bail d'Abernathy si Fluidstack devient insolvable ou fait défaut de paiement, sauf après six ans. À River Bend, Hut 8 n'émet ni actions ni bons en contrepartie de la garantie ;
    - montage commun à Abernathy et à Barber Lake : un client aval en colocation de Fluidstack, non nommé, verse les loyers sur un compte séquestre nanti au profit des porteurs des obligations ;
    - Amazon : chez Cipher, bail de Black Pearl d'environ 5,5 Md$ et bail de Stingray d'environ 2,0 Md$, loyers garantis par Amazon.com, Inc. ;
    - entités : Fluidstack CS I Inc. est une filiale indirecte à 100 % de Fluidstack Ltd. (8-K de TeraWulf du 2025-12-18), extrait retenu pour le point 6 ;
  - écart relevé : le communiqué et la présentation de Hut 8 du 2025-12-17 sont expressément incorporés par référence dans un item 8.01, et le niveau par le triplet (point 3) les classe pourtant furnished. Laissé en l'état, comme l'écart du point 7 ;
  - au-delà du plafond restent 145 fenêtres : 40 nomment Fluidstack, 61 l'infrastructure (dont 22 d'Amazon), 44 aucune des deux. Le rendement est présenté à l'utilisateur avant d'aller plus loin.

  (12) Volet 6, amendement et volume, après le tirage et avant toute lecture (2026-10-20) :
  - recherche : 15 résultats pour « "OpenAI" » et 7 pour « "Anthropic" », soit 22 résultats, 21 pièces dans 15 dépôts, du 2024-01-12 au 2026-06-01 : 12 pièces UPLOAD et 9 CORRESP. Déposants : SpaceX 6, Destiny Tech100 4, CoreWeave 3, Scepter Holdings 3, Rubrik 3, DHC Acquisition et Klarna 1 chacun. Aucune lettre de Microsoft, d'Amazon, d'AMD ni d'Oracle ne nomme un laboratoire : l'attente du remue-méninges n'était pas fondée sur un dépôt. Les 21 pièces sont tirées (21 requêtes) ;
  - amendement, fondé sur les seuls types de pièce : chacun des six dépôts UPLOAD porte la lettre en PDF (type LETTER) et son texte extrait par EDGAR (type TEXT-EXTRACT). Le normaliseur fait de ce texte un seul paragraphe (jusqu'à 28 517 caractères), quand le texte du PDF garde 14 à 132 paragraphes par lettre. La lettre se lit donc par son PDF (point 4), et les six textes extraits sont écartés (`exclude`) avec leur motif ;
  - volume, avant lecture : 21 fenêtres, 21 textes distincts, 21 blocs, aucun au-delà du plafond de 60 ; 35 011 caractères. 13 viennent des réponses des sociétés (CORRESP) et 8 des lettres du personnel (UPLOAD), toutes au niveau E, `correspondence`. Déposants : Destiny Tech100 7, SpaceX 6, CoreWeave, Scepter Holdings et Rubrik 2 chacun, Klarna et DHC Acquisition 1 chacun. Les blocs vont du 2026-06-01 au 2024-01-12. Liste de lecture `sec_letters`, dans l'ordre du montage.

  (13) Volet 6, lecture, sans sous-agent (2026-10-20) :
  - rendement : 21 blocs, 21 lignes (13 observations, toutes descriptives, sans famille ni montant ; 8 abstentions), aucune rejetée. Abstentions : 4 `out_of_scope_content` (simple usage d'outils ou de services d'IA par Scepter Holdings et Rubrik), 3 `duplicate_of_other_block` (lettre du personnel reprise mot pour mot dans la réponse de la société), 1 `no_relevant_content` (contexte du marché, de seconde main, chez DHC Acquisition) ;
  - noms : les lettres portent ceux du personnel de la SEC, des destinataires et de dirigeants ; le contrôle refait à la fin n'en trouve aucun dans les lignes. Les propos de presse cités par le personnel ne sont pas repris comme faits ;
  - ce que les lettres orientent :
    - SpaceX (mai et juin 2026) : le S-1 décrivait d'abord en page F-62 un accord de services en nuage du 3 mai 2026 avec un tiers non nommé. À la demande du personnel, le prospectus révisé indique qu'Anthropic paiera 1,25 Md$ par mois pour la capacité de COLOSSUS et COLOSSUS II. Le personnel demande pourquoi l'accord n'est pas déposé (Item 601(b)(10)) ; SpaceX répond qu'il relève du cours normal des affaires et chiffre la capacité aux pages 13 et 147 de l'amendement n° 1. Les lignes du 424B4 déjà lues disent « montant non publié » : l'écart est à vérifier dans le prospectus, non tiré dans ce volet ;
    - CoreWeave (mars 2025) : la part de Microsoft dans le revenu futur engagé (15,1 Md$ de RPO au 31 décembre 2024, plus jusqu'à 11,55 Md$ du contrat-cadre avec OpenAI OpCo, LLC) est caviardée dans la réponse ;
    - Destiny Tech100 (2024 et 2025) : le fonds détient OpenAI par un véhicule (DXYZ OAI I LLC) qui n'avait que de la trésorerie au 31 décembre 2023 et a investi le 22 janvier 2024. Le personnel conteste que le N-PORT au 31 décembre 2023 présente OpenAI comme un placement ; le fonds refuse de le modifier en 2024 et s'y engage en 2025. Les véhicules ne sont pas consolidés ;
    - Klarna (juillet 2025) : partenariat avec OpenAI annoncé en 2023, assistant de service client fondé sur OpenAI depuis février 2024 ;
  - attendu du remue-méninges non vérifié : aucune lettre de Microsoft, d'Amazon, d'AMD ni d'Oracle ne nomme un laboratoire dans la recherche plein texte.

  (14) Intégration et résultats (2026-10-20) :
  - entités par extrait (point 6) :
    - Fluidstack CS I Inc. rejoint le groupe de Fluidstack Ltd. (`consolidated_subsidiary`) sur l'extrait « Fluidstack CS I Inc., a wholly-owned indirect subsidiary of Fluidstack Ltd. » (8-K de TeraWulf du 2025-12-18 ; même phrase dans deux autres 8-K déjà lus). Fluidstack USA I à IV restent des contreparties propres : aucun bloc lu ne nomme leur lien, le 8-K de Hut 8 du 2025-12-17 ne parlant que d'« a subsidiary of Fluidstack Ltd. » sans la nommer ;
    - deux alias nés d'un extrait qui les définit (D-0021) : « Abernathy Joint Venture » pour FS CS I LLC (10-Q de TeraWulf du 2026-08-05) et « Fluidstack USA III » pour Fluidstack USA III Inc. (acte de Flash Compute) ;
  - correction de lecture avant le second réassemblage : quatre lignes du volet 7 portaient un preneur non résolu (« Cipher », « La Lupa Data LLC », filiale de TeraWulf), qui laissait trois arêtes sans groupe d'arrivée ou rattachait le bail de Core42 à une contrepartie propre. Le preneur devient « the Company », le déclarant (règle des blocs de montage) ;
  - correction du rendu : un groupe de contrepartie affichait le plus petit nom de ses membres. Fluidstack CS I Inc. donnait donc son nom au groupe de Fluidstack Ltd. Le nom de la tête (même nom normalisé que la clé du groupe) passe désormais d'abord. Aucun des 1 070 autres groupes de contrepartie à appartenance ne change de nom ; un test de plus ;
  - réassemblages : le premier, sans mémo des étapes (le code ayant changé), en 13 min ; le second, après la correction des preneurs, en 2 min 44 s ; rendu en 26 s ;
  - tables, contre le dépôt d'avant D-0064 :
    - observations 29 269 → 29 380 (111 lignes : 90 du volet 7, 21 du volet 6) ;
    - arêtes 8 326 → 8 342, dont 5 212 à montant avant comme après : les 16 arêtes nouvelles sont des relations, leurs pièces étant furnished (niveau E) ou des contrats de financement de niveau D ;
    - entités 3 576 → 3 579 ;
    - exclusions 31 430 → 31 587 : 146 du volet 7 (67 `not_processed` et 78 `out_of_scope` au-delà du plafond, ces dernières venant de dépôts de groupes suivis ; une pièce sans fenêtre), 6 textes extraits par EDGAR du volet 6, les 3 fenêtres de Stargate dans les facteurs de risque (point 7), un nom en attente (« Dell Technologies », ligne descriptive) et un agrégat invalide ;
  - agrégat invalide : l'exposition d'Alphabet envers Fluidstack Ltd. au 2026-06-30 (obligations conditionnelles, plafond d'engagement, garantie) devient `not_determinable` (invariant (a) de §7.6). Ses garanties ne sont chiffrées que dans des pièces furnished. La cellule n'existait pas avant ;
  - arêtes d'Anthropic 76 → 77 : le bail de Justified chez TeraWulf est une relation, sans montant admissible, et son montant d'environ 19 Md$ reste dans la ligne. Arêtes de Fluidstack (toutes dénominations) 30 → 38, dont 4 à montant avant comme après ;
  - paires nouvelles : Alphabet → Fluidstack Ltd. (6 arêtes, structure financière), TeraWulf → Fluidstack Ltd. et TeraWulf → FS CS I LLC (une arête chacune). Toutes sont `causalité non établie`, avec un contrôle bilatéral C5 non testable ; Cipher → Amazon passe de 1 à 3 arêtes et Hut 8 → Fluidstack Ltd. de 2 à 3 ;
  - cellules de rang 1 : 39 684 → 39 798 calculées ; motifs `historique tronqué` 8 153 → 8 389 ;
  - tests : 245, tous passés.
- **D-0065 — Volet 5 : marques de tiers des non-cotés du modèle dans les Form N-PORT Data Sets (parts d'OpenAI, d'Anthropic et des autres, en un seul passage). Règles fixées avant tout tirage.** (1) Décision de l'utilisateur, le 2026-10-20 : « Fais plutôt le volet 5 et profites-en pour scanner en un seul passage tous les non-côtés du modèle ». C'est le volet 5 du remue-méninges de D-0059 (point 1) : « Quelques fonds enregistrés (fonds à intervalle de capital-risque, fonds fermés, grands fonds actions) détiennent des actions non cotées d'OpenAI et d'Anthropic. On obtiendrait une valeur déclarée par action, par fonds et par mois : une marque de tiers, comme la série obligataire de SoftBank. […] Astuce : scanner en un seul passage tous les non-cotés du modèle (xAI, Cerebras, Crusoe, Lambda, Nscale…) ». Il passe avant les trois propositions du rapport de D-0064, qui restent des propositions. Aucun bloc n'est lu : le volet est fait de code, d'un tirage et de deux mesures. Réseau : les 28 archives de D-0058 sont tirées de nouveau (11,94 Go en D-0058), par le client SEC unique et journalisé. L'as_of reste le 2026-10-07.

  (2) Constat, sans requête, sur les tables du commit 5c05d30 et sur le cache :
  - les extraits de D-0058 (point 8) ne gardent que les positions de SoftBank, soit 31 746 lignes. Aucune autre ligne des archives n'est en cache : il faut les tirer de nouveau ;
  - registre : 1 943 entités, 161 alias et 1 475 appartenances. 1 392 dénominations légales servent déjà à rattacher les positions des BDC (D-0022, D-0045) : nom normalisé, mot de forme juridique final, au moins deux mots ;
  - non-cotés que nomme le registre, entre autres :
    - laboratoires : OpenAI (OpenAI, OpenAI Global, LLC, OpenAI Group PBC, OpenAI OpCo, LLC, OpenAI Infra Holdings, LLC) et Anthropic (Anthropic, Anthropic PBC) ;
    - groupes non déposants : Lambda (Lambda, Inc.) et Nscale (28 entités ; Nscale Limited a déposé un S-1 et n'a pas de symbole au 2026-10-07) ;
    - groupe SpaceX : X.AI Holdings Corp., X.AI Corp., X.AI LLC, X Corp. et X Holdings Corp. ;
    - contreparties : Crusoe Energy Systems, Inc., Fluidstack Ltd. et cinq sociétés de Fluidstack, Cohere, Inc., Hugging Face, Inc., Inflection AI, Inc., ANYSPHERE, INC. D'autres n'y figurent que sous un nom sans forme juridique (« Scale AI », « Mistral AI », « Vantage Data Centers », « Crusoe », « xAI »), qui ne rattache rien (D-0022) ;
  - cotation, d'après la liste des symboles d'EDGAR du 2026-10-07 (`company_tickers.json`, en cache) : 125 entités du registre ont un symbole. Parmi elles :
    - Cerebras Systems Inc. (CBRS), dont aucune submission n'est en cache ;
    - SpaceX, dont le premier 424B4 est du 2026-06-12, et CoreWeave, du 2025-03-31.

    Leurs positions d'avant ces dates sont celles d'un non-coté ;
  - codes des tables, vérifiés sur les extraits de SoftBank : ASSET_CAT (EC, DBT, LON, DCR, DE, SN, ABS-MBS, OTHER), UNIT (NS, PA, NC, OU), FAIR_VALUE_LEVEL (1, 2, 3, N/A), ISSUER_TYPE (CORP, OTHER, NUSS). Le formulaire (Items C.4 et C.8) nomme les autres catégories, dont « equity-preferred » et « private fund ». Il précise que « N/A » s'emploie quand la valeur liquidative sert d'expédient pratique.

  (3) Sources et tirage :
  - les 28 archives trimestrielles de la page en cache (D-0058, point 27), du 2019-10-01 à l'as_of. Une archive dont l'en-tête Last-Modified est postérieur à l'as_of n'est ni gardée ni scannée (`not_public`) ;
  - chacune est tirée par le client unique, scannée dans un processus à part, puis effacée, de la plus récente à la plus ancienne. L'archive suivante se tire pendant le scan de la précédente. Il n'y a donc jamais qu'un processus réseau, et au plus deux archives sur le disque ;
  - extraits sous `cache/datasets/nport/{archive}/unlisted/`. Le manifeste `cache/datasets/nport/unlisted_manifest.jsonl` garde, pour chaque archive, l'en-tête Last-Modified et celui de D-0058, la taille, l'empreinte, la version du lexique et les décomptes ;
  - les extraits de SoftBank, leur manifeste et la mesure `nport_price_to_par` ne changent pas.

  (4) Lexique, tiré du registre du commit 5c05d30 et de `config.yaml`, figé avant le premier tirage. Sa version est consignée au manifeste. Il comprend :
  - (a) les dénominations légales des entités et alias confirmés, selon la règle des BDC ;
  - (b) leurs bases, c'est-à-dire la dénomination sans sa forme juridique finale, quand il reste au moins deux mots (« crusoe energy systems ») ;
  - (c) les termes des lexiques de la configuration : laboratoires, découverte (`seed`, `confirmed`) et piste des non-déposants. Ce sont les seuls noms courts ;
  - (d) les noms d'entités confirmées sans forme juridique, quand ils ont au moins deux mots (« scale ai », « vantage data centers »). Une description (« a syndicate of banks ») ou une suite de parties jointes par « and » n'en est pas une.

  Chaque chaîne vaut aussi sous sa variante de ponctuation, le point retiré plutôt que remplacé par une espace (« X.AI » et « XAI »). La comparaison se fait sur les noms normalisés (§10.2), en mots entiers, sans casse. Un alias court (« OAI », « Meta ») n'est pas un terme : il ne vaut que dans le document qui le définit (D-0021).

  (5) Lignes gardées : une position dont le nom d'émetteur (ISSUER_NAME) ou l'intitulé (ISSUER_TITLE) contient une chaîne du lexique, et qui n'est évaluée ni au niveau 1 ni au niveau 2 de la hiérarchie de juste valeur (Item C.8). Le niveau est donc 3, « N/A » ou vide : ce sont les positions que le fonds évalue lui-même. Une position des niveaux 1 et 2 est comptée, par entité ou chaîne, par niveau et par catégorie, mais elle n'est pas gardée. Sont gardés aussi les identifiants, les caractéristiques de dette, le dépôt, le déclarant et la série des positions gardées.

  (6) Rattachement, à l'assemblage. C'est la règle des BDC (D-0022, D-0045), appliquée au seul nom d'émetteur :
  - le nom doit commencer par une dénomination légale (a), au besoin sous la variante de ponctuation. La plus longue l'emporte ;
  - un autre mot de forme juridique dans les quatre mots qui suivent, avant tout mot d'instrument, laisse le nom sans rattachement ;
  - le groupe est celui de l'entité à la date de portefeuille (`group_at`, vue `as_known`) ;
  - l'intitulé ne rattache jamais rien. Un véhicule qui détient un laboratoire n'est pas le laboratoire ;
  - un nom gardé par (b), (c) ou (d) seulement est un nom voisin. Il n'est jamais rattaché sans un extrait (D-0021, D-0022). Il sort en `pending_entity`, avec le nombre de positions et de séries et la valeur déclarée à sa dernière date ;
  - un véhicule nommé d'après un laboratoire est la mention que décrit D-0036 (point 4). Il est compté comme un nom voisin, jamais comme une part du laboratoire.

  (7) Cotation :
  - une entité dont le CIK porte un symbole dans la liste du 2026-10-07 est cotée à partir du dépôt de son premier prospectus 424B4 ou 424B1, lu dans ses submissions EDGAR. Sans un tel prospectus, elle est cotée sur toute la période ;
  - ses positions n'entrent dans la mesure que si leur date de portefeuille précède cette date ;
  - les submissions se lisent dans le cache. Elles se tirent une fois, après le scan, pour les seules entités cotées qui portent des positions de la mesure ;
  - une entité sans symbole est non cotée aux États-Unis. Le niveau 3 dit alors à lui seul que le fonds n'a pas de prix observable.

  (8) Mesures. Ce sont deux séries descriptives par nœud, des marques déclarées par des tiers (perspective `counterparty`). Ce n'est jamais une valorisation du nœud, ni un fait comptable, ni une probabilité de défaut. Elles n'entrent dans aucune mesure de financement, ni dans l'exposition, les paires, les cycles ou l'annexe F, ni dans aucun agrégat entre nœuds.
  - `nport_equity_mark`, par nœud, fonds (la série, à défaut le déclarant), titre et date de portefeuille : la valeur déclarée par action, dans la monnaie du titre. C'est la valeur en dollars convertie par le taux déclaré (D-0058, point 28). Positions retenues :
    - rattachées (point 6) et non cotées à leur date (point 7) ;
    - en actions ordinaires ou de préférence (EC, EP), en nombre d'actions (NS), longues, de solde positif ;
    - au niveau 3 ;
    - au dernier dépôt de chaque série pour cette date : un amendement remplace le dépôt (D-0058, points 8 et 28).

    Le titre est l'ISIN, à défaut le CUSIP, à défaut l'intitulé normalisé, précédé de la catégorie. Les positions d'un même titre dans un même dépôt s'additionnent. Sont publiés avec la valeur : le nombre d'actions, la valeur en dollars, la catégorie, l'intitulé, le titre restreint (Item C.6), les noms de la série et du déclarant, et l'accession ;
  - `nport_equity_held`, par nœud et par trimestre civil : la somme des valeurs en dollars des positions de la mesure précédente, au dernier rapport de chaque série dans le trimestre. Sont publiés avec la somme : le nombre de séries et de positions, et les dates de portefeuille. C'est ce que les fonds enregistrés déclarent détenir, jamais une valeur du nœud ;
  - le registre des mesures et `schema.sql` sont mis à jour (test `test_schema_sync`).

  (9) Hors des mesures, et comptés :
  - les positions des niveaux 1 et 2 (cotées, ou évaluées sur des données observables) ;
  - les positions rattachées hors actions (dette, prêts, dérivés, autres) et les actions en autres unités (OU) ;
  - les positions d'une entité cotée à leur date ;
  - les noms voisins et les véhicules (point 6) ;
  - les positions vendeuses.

  (10) Données personnelles (D-0051 ; D-0058, point 10) : les tables lues nomment des fonds et des émetteurs, jamais des signataires. Aucune personne physique n'est un nœud. Un nom d'émetteur qui serait celui d'une personne n'est ni rattaché ni cité.

  (11) Réseau (§9.5) : un seul client et un seul User-Agent, envoyé aux seuls hôtes de la SEC ; au plus 5 requêtes par seconde ; jamais deux processus réseau à la fois ; une pause d'au moins dix minutes après un 403 ; chaque requête au journal.

  (12) Code, avant tout tirage :
  - `pipeline/nport.py` : lexique, scan, tirage avec recouvrement, positions, rattachement, cotation, mesures, exclusions et volume ;
  - registre des mesures et `schema.sql` ;
  - `assemble` : cellules et exclusions du scan ;
  - rendus : `synthesis.md` et `series.md` ;
  - tests (`test_nport`).

  (13) Ordre et commits :
  - la décision, la configuration et le code, avec leurs tests, poussés avant toute requête ;
  - tirage et scan des 28 archives. Le volume est consigné ici avant tout calcul, en décomptes seulement, avec les constats d'identité ; toute correction est fixée avant le calcul. Commit ;
  - submissions des entités cotées concernées (point 7) ;
  - réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (14) Limites connues avant calcul :
  - un non-coté sans dénomination légale au registre n'est pas rattaché ; seuls ses noms voisins sont comptés ;
  - une variante de forme juridique (« LLC » pour « Inc. ») ne rattache pas ;
  - une position privée déclarée au niveau 2 n'entre pas ;
  - deux fonds peuvent détenir deux catégories d'actions différentes, dont les valeurs par action ne se comparent pas sans le titre ;
  - les noms ajoutés au registre après le scan ne sont pas scannés. Une archive scannée avec un lexique antérieur est signalée (`not_processed`).

  (15) Volume et constats d'identité, consignés avant tout calcul de la mesure (2026-10-20), en décomptes seulement :
  - tirage : les 28 archives, de 2026q3 à 2019q4, tirées, scannées et effacées en 56 minutes (11,94 Go). Le journal compte 42 requêtes, toutes réussies : les 28 archives et 14 pages de submissions (point 7). L'en-tête Last-Modified de chaque archive est celui de D-0058 : les extraits de SoftBank restent ceux d'archives identiques. Extraits gardés : 26,3 Mo ;
  - lexique `lx-cd6e02bb8912` : 1 527 dénominations légales et leurs variantes sans points (a), 1 201 bases (b), 44 termes de la configuration (c) et 60 noms sans forme juridique (d). Une chaîne déjà présente garde sa première partie ;
  - positions qui contiennent une chaîne du lexique : 7 579 884. Celles des niveaux 1 (2 208 278) et 2 (4 976 508) sont comptées et non gardées. Sont gardées 395 098 positions : 314 503 au niveau 3, 76 529 sans niveau, 4 066 en « N/A ». Ce sont surtout des prêts (292 793) et des dérivés (80 377) ; les actions en font 11 159 (EC 6 603, EP 4 556) ;
  - rattachement : 354 379 positions rattachées, à 201 nœuds. Les noms voisins sont 1 361 noms et 40 719 positions (`pending_entity` ou `conflicting`) ;
  - sélection de la mesure (point 8). Sont écartées : 346 477 positions hors actions, 10 en autres unités, 8 vendeuses, 462 hors du niveau 3, 1 791 d'entités cotées à leur date, et 255 par la correction ci-dessous. Restent 5 376 positions, dont 5 338 au dernier dépôt de chaque série : 217 séries, 37 nœuds, dates de portefeuille du 2019-09-30 au 2026-07-31 ;
  - par nœud, positions au dernier dépôt, séries et dates de portefeuille :
    - SpaceX : 2 059 positions, 58 séries, 86 dates, du 2019-09-30 au 2026-05-31. Elles sont toutes antérieures au 424B4 du 2026-06-12 ; y entrent les positions de X.AI Holdings Corp. et de X.AI Corp. datées après leur entrée au groupe ;
    - Waymo LLC : 1 076 positions, 59 séries, du 2020-05-31 au 2026-07-31 ;
    - Anthropic : 606 positions, 113 séries, 32 dates, du 2024-03-31 au 2026-07-31 ;
    - OpenAI : 318 positions, 58 séries, 25 dates, du 2024-04-30 au 2026-07-31 (OpenAI Global, LLC puis OpenAI Group PBC) ;
    - xAI avant son entrée au groupe SpaceX : X.AI Holdings Corp. 211 positions (45 séries), X.AI Corp. 114 (40 séries) ; X Holdings Corp. 155 (19 séries) ;
    - CoreWeave avant son 424B4 du 2025-03-31 : 185 positions, 26 séries, du 2023-11-30 au 2025-02-28 ;
    - Cerebras avant son 424B4 du 2026-05-14 : 82 positions, 29 séries, du 2022-06-30 au 2026-04-30 ;
    - Nscale : 31 positions, 9 séries ; Lambda : 11 positions, une série ; Fluidstack : 6 positions, 3 séries ; SiFive : 31 positions, 8 séries ;
    - 24 autres nœuds, 453 positions. Ce sont pour la plupart des sociétés avant leur introduction en bourse ou après leur radiation (Compass, DoorDash, Snowflake, Coinbase, Aurora, WeWork, McDermott…) ;
  - cotation (point 7) : les submissions de 10 entités cotées, absentes du cache, ont été tirées. Leur premier 424B4 ou 424B1 : Cerebras 2026-05-14, Tempus AI 2024-06-17, DiDi 2021-06-30, Symbotic 2021-03-10, Ginkgo 2021-02-25, Snowflake 2020-09-16, CuriosityStream 2019-11-21, Triller 2019-05-15, Uber 2019-05-13, General Motors 2010-11-18. Nebius, cotée depuis 2011 sous le nom de Yandex, porte 1 493 positions de niveau 3, hors de la mesure ;
  - correction fixée avant le calcul, la cotation des entités sans symbole. Le point 7 tenait pour non cotée toute entité sans symbole dans la liste du 2026-10-07. Or le registre contient des sociétés cotées sans CIK au registre (American International Group, Banco Santander, ABN AMRO, SK Telecom) et des sociétés radiées depuis (VMware, Mellanox, EQRx, Meta Materials). Leurs rares positions de niveau 3 seraient entrées dans la mesure. Règle, sur la règle de majorité de D-0058 (point 28) : une entité sans symbole est tenue pour cotée dans une archive où la majorité de ses positions en actions, toutes séries confondues, sont évaluées aux niveaux 1 ou 2. Ses positions de niveau 3 de cette archive sortent alors (`quoted_in_archive`). 5 301 couples (entité, archive) sont ainsi cotés, pour 268 entités, et 255 positions sortent : EQRx 56, Meta Materials 46, AIG 41, SK Telecom 32, McDermott 29, et d'autres. Anthropic ne l'est jamais : 1 position au niveau 1 et 4 au niveau 2, contre 612 au niveau 3. La majorité se compte par archive, et non par date de portefeuille, car les extraits ne gardent pas les positions des niveaux 1 et 2. Une introduction en bourse au milieu d'une archive peut donc écarter quelques positions antérieures d'une entité sans symbole (Squarespace, 1 position) ;
  - correction fixée avant le calcul, un véhicule rattaché à tort. La revue des 175 noms rattachés trouve un seul nom qui n'est pas l'émetteur : « BMO BANK NA PRIVATE EQUITY (SPV RAVINE MASTER AGGR » (2 positions), un véhicule. Règle : un mot de véhicule après la dénomination (« SPV », « feeder », « aggregator », « co-invest ») laisse le nom sans rattachement. Les 174 autres noms désignent l'émetteur lui-même, au besoin avec la catégorie du titre (« Anthropic PBC SER H-1 CVT PFD PP », « WAYMO LLC SER A-2 CVT PFD UNITS PP ») ou un ancien nom défini par un extrait (« Ikonics Corporation », « Soaring Eagle Acquisition Corp. », « TORCHLIGHT ENERGY RESOURCES INC ») ;
  - noms voisins des laboratoires et des nœuds, laissés sans rattachement par la règle du point 6 et comptés :
    - OpenAI : 136 positions (34 séries, 17 noms). Ce sont « OpenAI Group PCB… », où PCB est une faute pour PBC (67), « OPENAI LLC CVT INT RIGHTS PP » (12), « DXYZ OAI I LLC (economic exposure to OpenAI Global LLC…) » (10), « OPENAI SERIES C » (9), « OpenAI » (6), « OpenAI Foundation » (6), « OpenAI, Inc. » (4) ;
    - Anthropic : 45 positions (14 séries, 9 noms) : « Anthropic, Inc. » (14), « ANTHROPIC SERIES G » (9), « ANTHROPIC » (8), « ANTHROPIC SERIES H » (4), et un véhicule (« Magnitude ANC III, LLC »). D'autres positions n'ont qu'un nom d'émetteur « N/A » ;
    - SpaceX : 562 positions (45 séries) : « Space Exploration Technologies » sans forme juridique (378), « X HOLDINGS I, INC. » (49), « x.AI, Inc. » (19), et des véhicules (Atreides, MWAM VC SpaceX-II, Celadon, DXYZ SpaceX I) ;
    - CoreWeave : 302 positions, presque toutes des prêts de ses sociétés de financement (« COREWEAVE COMPUTE AC », « CoreWeave CAC IV, LLC ») ; Nscale : 19 prêts, sous le seul nom « Nscale » ;
  - une extension du rattachement, au nom d'un laboratoire suivi des seuls mots de la catégorie du titre (« ANTHROPIC SERIES G », « OPENAI SERIES C »), est laissée à la décision de l'utilisateur. Les positions sont gardées : elle ne demanderait aucun nouveau tirage ;
  - code : `quoted_archives`, étape `quoted_in_archive` de la sélection, mots de véhicule du rattachement, `fetch_listing_submissions` ; deux tests de plus (`test_nport`).

  (16) Intégration et résultats (2026-10-20) :
  - deux corrections de l'export, fixées avant le rendu :
    - un nom voisin sans forme juridique sortait en `conflicting`, une valeur manquante de pandas étant prise pour une forme trouvée. Il sort désormais en `pending_entity` ;
    - les entités cotées sans date d'introduction connue sortaient en `not_processed` même sans position de la mesure (Adobe, Boeing…). Seules comptent les entités qui en portent (point 7), et toutes ont désormais leur date ;
  - trimestres partiels. Un N-PORT se dépose dans les 60 jours qui suivent la fin du trimestre du fonds. Le trimestre civil en cours à la dernière archive (T3 2026, rapports de juillet seulement) et le premier de la période (T3 2019) ne sont donc couverts qu'en partie. Leur valeur détenue porte le statut `partial` (10 cellules), et le rendu prend le dernier trimestre complet ;
  - réassemblages complets, le code ayant changé : 10 min 36 s, puis 9 min 58 s ; rendu en 26 s ;
  - tables, contre le dépôt d'avant D-0065 :
    - mesures 172 366 → 177 892 : 5 275 cellules `nport_equity_mark` et 251 `nport_equity_held`, dont 10 partielles. Aucune cellule d'avant ne change ;
    - exclusions 31 587 → 32 948 : 1 356 noms voisins en `pending_entity` et 5 en `conflicting`. Aucune exclusion d'avant ne change ;
    - documents 25 282 → 25 296 : les 14 pages de submissions tirées (point 7) ;
    - faits, observations, entités, liens et contrôles identiques à l'octet près ;
  - nombres publiés : 14 552 → 18 833 ;
  - résultats, au dernier trimestre complet (2026-06-30, sauf mention). Ce sont des valeurs déclarées par des fonds, jamais des valorisations :
    - Anthropic : 15 233 M$ détenus par 106 séries. C'était 2 M$ au 2024-03-31 (une série), 184 M$ au 2025-06-30 (17), 2 129 M$ au 2025-12-31 (54) et 5 273 M$ au 2026-03-31 (65). Valeur par action médiane : 259,14 $ au 2026-03-31, puis 589,01 $ du 2026-05-31 au 2026-07-31, la plus haute à 622,94 $ ;
    - OpenAI : 4 345 M$ détenus par 58 séries. C'était 276 M$ au 2024-12-31 (4 séries) et 1 577 M$ au 2025-12-31 (32). Valeur par action médiane : 693,90 $ au 2026-02-28, puis 687,69 $ du 2026-03-31 au 2026-07-31 ;
    - SpaceX avant son introduction : 23 667 M$ au 2026-03-31, détenus par 51 séries. C'était 737 M$ au 2019-12-31 (14 séries), 3 327 M$ au 2022-12-31 (29) et 13 719 M$ au 2025-12-31 (38). Au 2026-06-30, seuls entrent les rapports d'avril et de mai, avant le 424B4 : 11 727 M$ (24 séries). La valeur médiane passe de 526,59 $ à 105,32 $ au 2026-05-31, soit un rapport de 5. Quelques fonds déclarent encore 5 265,90 $ : les valeurs par action ne se comparent pas d'un fonds à l'autre à une division d'actions près. Le nœud réunit aussi les actions de X.AI Holdings Corp. datées après son entrée au groupe ;
    - xAI avant son entrée au groupe SpaceX (X.AI Holdings Corp.) : 2 456 M$ au 2025-12-31, détenus par 42 séries. Valeur par action : 36,56 $ en septembre et octobre 2025, 65,19 $ en novembre, puis 75,46 $ ;
    - Waymo LLC : 2 366 M$ détenus par 54 séries, contre 490 M$ au 2020-06-30. Valeur par action de 164,32 à 214,12 $ en 2026 ;
    - Cerebras avant son introduction : 1 282 M$ au 2026-03-31, détenus par 27 séries, contre 7 M$ en 2022 (une série). Valeur par action : 36,23 $ fin 2025, 89,02 $ au premier trimestre 2026, puis 100,26 $ au 2026-04-30 ;
    - CoreWeave avant son introduction : 808 M$ au 2024-12-31, détenus par 26 séries. Valeur médiane de 847 à 1 005 $ par action environ, de septembre 2024 à février 2025, avant sa division ; quelques fonds déclarent 1,2 à 1,8 $ ;
    - Fluidstack : 109 M$ détenus par 3 séries, 144,11 à 162,22 $ par action, contre 74,09 $ au 2026-03-31 ;
    - Nscale : 47 M$ détenus par 9 séries. La valeur par action passe de 1 223,53 $ en avril 2026 à 20,39 $ en mai, autre changement d'unité ;
    - Lambda : 12 M$, une seule série. Sa valeur par action va de 20,94 à 38,00 $ (2025-07-31 et 2026-07-31) ;
  - limites :
    - les noms voisins (point 15) ne sont pas rattachés. Ce sont, sur toute la période, 136 positions d'OpenAI, 45 d'Anthropic et 562 de SpaceX. Les valeurs détenues en sont sous-estimées d'autant ;
    - une division d'actions ou une autre unité rend les valeurs par action de deux fonds incomparables. La mesure les publie telles que déclarées, avec le nombre d'actions ;
    - les positions des niveaux 1 et 2 ne sont pas gardées. La règle de majorité se compte donc par archive (point 15) ;
    - les prêts et la dette des non-cotés évalués au niveau 3 sont gardés (292 793 positions de prêts, dont CoreWeave et Nscale), mais ne sont pas mesurés ;
  - tests unitaires : 258, tous passés.
- **D-0066 — Rattachement étendu des positions N-PORT, marques de crédit des prêts et de la dette, et les trois propositions de D-0064 (chaîne d'Anthropic au-delà du plafond, niveau des pièces des montages d'avant, montant d'Anthropic dans le 424B4 de SpaceX). Règles fixées avant tout traitement.** (1) Décision de l'utilisateur, le 2026-10-21 : « Fais les propositions 1, 2 et 3 ». Ce sont les trois propositions du rapport de D-0065 :
  - « Rattacher aussi les noms formés du nom d'un laboratoire suivi de la seule catégorie du titre (« ANTHROPIC SERIES G »). Les positions sont déjà gardées » ;
  - « Mesurer les marques de crédit des prêts aux non-cotés, évalués par les fonds : 292 793 positions de prêts gardées, dont CoreWeave et Nscale » ;
  - « Reprendre les trois propositions du rapport de D-0064, toujours en attente » : continuer la chaîne d'Anthropic au-delà du plafond (145 fenêtres), reclasser les pièces EX-99 des montages d'avant, vérifier le montant d'Anthropic dans le 424B4 de SpaceX.

  Lecture séquentielle par l'exécutant, sans sous-agent. Aucune requête n'est prévue : pièces et extraits sont en cache. L'as_of reste le 2026-10-07.

  (2) Constat, sans lecture et sans aucune valeur, sur les tables du commit a485fcd :
  - rattachement étendu. Sur les 93 termes des lexiques de la configuration, 34 désignent une seule entité confirmée du registre, par son nom normalisé ou un alias. Les autres n'en désignent aucune (« xAI », « X.AI », « Alphabet », « Stargate », « Lambda Labs »…). La règle du point 3 rattacherait 143 positions, sous 16 noms déclarés :
    - OpenAI 24 (« OPENAI SERIES C », « OpenAI », « OpenAI Private Placement »…) et Anthropic 24 (« ANTHROPIC SERIES G », « ANTHROPIC », « ANTHROPIC SERIES H »…) ;
    - SpaceX 22 (« SPACEX SERIES K CVT PFD STOCK PP », « SPACEX COMMON SHARES ») ;
    - CoreWeave 54 : des actions de préférence convertibles (31) et des prêts (« COREWEAVE SENIOR » 13, « COREWEAVE 2ND ABL:TL » 10) ;
    - Nscale 19 prêts, déclarés sous le seul nom « Nscale ».

    Une première version, qui admettait un code de catégorie isolé, rattachait aussi « META CW GPU » à Meta. Le code n'est donc admis qu'après un mot de catégorie ;
  - prêts et dette. 289 834 positions rattachées sont des prêts (288 956) ou des titres de dette (878), toutes au niveau 3 sauf 12. 287 614 portent un seul nom, « Block, Inc. ». Ce sont des prêts de la plateforme Square, un par commerçant, détenus par cinq fonds Franklin : jusqu'à 7 279 positions dans un même dépôt, quand aucune autre entité n'en a plus de 19 (une société de financement de CoreWeave). Le déclarant y nomme l'intermédiaire, non l'emprunteur. 14 autres sont des « Marketplace Loan » de Prosper. Restent 2 176 positions, 2 132 au dernier dépôt de chaque série, de 69 nœuds et 319 séries, sur 94 dates du 2019-09-30 au 2026-07-31. Parmi elles :
    - CoreWeave, 453 : les prêts à tirage différé de CoreWeave Compute Acquisition Co. II et IV ;
    - SVF II Finco Cayman, 243 : les prêts à terme de SoftBank Vision Fund II ;
    - Beignet Investor LLC, 94 : l'obligation garantie « Project Beignet », de la coentreprise de Meta ;
    - Nscale, 38 : son prêt à tirage différé ;
    - Cloudera, AP Grange, General Motors, Broadcom, T-Mobile, Amazon (obligations « CTL Logistics »), et des titres structurés de banques ;
  - montages d'avant. 71 blocs de 8-K y gardent le niveau de leur formulaire, au lieu du triplet du registre des documents (D-0064, point 3) :
    - pièces EX-99 (Stargate 28, Galaxy Helios 11) : C au lieu de E ;
    - contrats EX-4 et EX-10 (Galaxy Helios 19, `labs_corpus` 13) : C au lieu de D.

    Ils portent 91 lignes, dont 31 observations, et 9 arêtes, dont 4 à montant. Ces quatre arêtes viennent de pièces EX-99 de Galaxy Helios : trois baux de CoreWeave (4,5 Md$, 10,4 Md$ et 100 M$) et un financement de 434 M$ ;
  - chaîne d'Anthropic. Au-delà du plafond de 80 restent 145 textes distincts, soit 411 832 caractères : 40 de la classe Fluidstack, 61 de l'infrastructure, 44 autres. Il y a 127 pièces EX-99 (niveau E), 13 contrats (D) et 5 documents principaux de 8-K, déposés du 2023-04-27 au 2026-10-05. Les déposants : TeraWulf 29, Amazon 22, Cipher 12, Box 8, AMD 5, puis d'autres ;
  - 424B4 de SpaceX (0001628280-26-042639). La phrase « the customer has agreed to pay us $1.25 billion per month through May 2029 » y figure deux fois : au résumé du prospectus et dans la description de l'activité. Les paragraphes de ce document sont des lignes d'environ 110 caractères. Les fenêtres de `labs_corpus`, de deux paragraphes de part et d'autre, s'arrêtent donc avant le montant. La note lue (événements postérieurs) ne dit que « a monthly fee ». Les deux fenêtres sont des abstentions `duplicate_of_other_block`, la ligne gardée étant celle de la note.

  (3) Rattachement étendu (proposition 1). Il s'applique aux positions N-PORT, après la règle des dénominations légales (D-0065, point 6) :
  - un nom d'émetteur formé d'un terme de la configuration est rattaché à l'entité que ce terme désigne, s'il n'est suivi que de mots de catégorie ou d'instrument. Les termes sont ceux des laboratoires, de la découverte (`seed`, `confirmed`) et de la piste des non-déposants. Le terme doit désigner une seule entité confirmée du registre, par son nom normalisé ou un alias ;
  - mots de catégorie : series, class, preferred, common, stock, shares, units, ordinary, convertible, private placement, restricted, et leurs abréviations (ser, cl, pfd, pref, cvt, pp…). Mots d'instrument : term loan, delayed draw, revolver, ABL, first ou second lien, senior, secured, notes, bonds, tranche, unfunded, et leurs abréviations (tl, ddtl, 1st, 2nd…). Un code (« G », « H-1 », « A-3 », un taux, une date) n'est admis qu'après un tel mot ;
  - une forme juridique (« Inc. », « LLC ») ou un mot de véhicule (« SPV », « fund ») après le terme laisse le nom sans rattachement (« Anthropic, Inc. », « x.AI, Inc. ») ;
  - la règle vaut pour les laboratoires, comme proposé, et pour les autres termes (SpaceX, CoreWeave, Nscale…), car le prêt de Nscale n'est déclaré que sous « Nscale ». Le terme est celui que le modèle a déjà retenu pour ce nœud, et l'entité celle que le registre confirme ;
  - restent des noms voisins : les fautes (« OpenAI Group PCB »), les noms sans forme juridique (« Space Exploration Technologies ») et les autres formes juridiques (« Crusoe Energy Systems LLC »). §10.2 exclut la troncature et la distance d'édition.

  (4) Marques de crédit (proposition 2). Nouvelle mesure `nport_credit_mark`, par nœud, catégorie (prêt LON ou titre de dette DBT), monnaie et date de portefeuille :
  - valeur : somme des valeurs dans la monnaie du titre sur somme des nominaux (unité PA), comme `nport_price_to_par` (D-0058, points 8 et 28) ;
  - positions retenues : rattachées (D-0065, point 6, et point 3), prêts ou titres de dette, en nominal, longues, de nominal positif, au niveau 3, au dernier dépôt de chaque série pour la date ;
  - publiés avec la valeur : le nominal, le nombre de positions, de séries et de titres, les échéances et les coupons extrêmes, les intitulés les plus fréquents, et la part du nominal déclarée en défaut, en arriéré d'intérêts ou en intérêts capitalisés (Item C.9) ;
  - un prêt n'est pas coté : la cotation des actions de l'emprunteur ne joue pas, et le niveau 3 dit que le fonds l'évalue lui-même ;
  - sont exclus et comptés les prêts de plateforme. Un fonds qui déclare plus de 100 positions d'un même émetteur dans un dépôt nomme la plateforme qui les a consentis, non l'emprunteur (Square, sous « Block, Inc. »). Un intitulé « Marketplace Loan » est traité de même (Prosper). Leurs débiteurs peuvent être des personnes physiques, qui ne sont jamais des nœuds ;
  - perspective `counterparty` : jamais une probabilité de défaut ni un fait comptable de l'emprunteur. La mesure n'entre dans aucune mesure de financement, ni dans l'exposition, les paires, les cycles ou l'annexe F.

  (5) Niveau des pièces des montages d'avant (proposition 3, deuxième volet) :
  - le niveau par le triplet (D-0064, point 3) s'applique aux pièces de 8-K et de 8-K/A de tous les montages, comme dans le registre des documents. Un contrat EX-10, EX-4 ou EX-2 est de niveau D. Une pièce EX-99 est furnished, de niveau E. Un document principal dont les items sont tous 2.02, 7.01 ou 9.01 est de niveau E. Le reste est de niveau C. Les items viennent des documents du montage, à défaut des dépôts de la phase 0 ;
  - les blocs ne sont pas préparés de nouveau : seul leur niveau change, et leurs textes, leurs clés et leurs lignes restent les mêmes. L'option `evidence: triplet` est posée sur ces montages, pour qu'une préparation nouvelle donne les mêmes niveaux ;
  - une ligne d'un bloc de niveau E n'est jamais la source d'un montant : son arête devient une relation. Une ligne de financement d'un contrat (D) n'est pas non plus un financement à montant (§2.6).

  (6) Chaîne d'Anthropic au-delà du plafond (proposition 3, premier volet) :
  - le plafond du montage `anthropic_chain` passe de 80 à 225 textes distincts, soit tous. Les 80 premiers blocs gardent leurs clés ;
  - les 145 autres se lisent dans l'ordre du montage (classes, puis du plus récent au plus ancien), sur les conventions de D-0064 (points 5 et 6) : pas d'inférence, lignes descriptives pour les relations entre tiers, pièces furnished de niveau E, données personnelles ;
  - une fenêtre d'un dépôt d'un groupe suivi se lit ici : le catalogue du groupe ne lit pas ces pièces. L'exclusion `out_of_scope` de D-0064 pour ces 78 fenêtres tombe.

  (7) Montant d'Anthropic dans le 424B4 de SpaceX (proposition 3, troisième volet) :
  - une unité de lecture est ajoutée, par un nouveau montage `spacex_anthropic` (source `span`). C'est le passage du résumé du prospectus qui va de « For example, in May 2026, we entered into Cloud Services Agreements with Anthropic » à la fin de la phrase sur la résiliation (« upon 90 days' notice »), lignes du document jointes. La description de l'activité le répète mot pour mot et n'est pas reprise. Niveau C (424B4, filed) ;
  - la ligne prend le montant tel qu'écrit : 1,25 Md$ par mois jusqu'en mai 2029, montée en capacité en mai et juin 2026 à tarif réduit, résiliable par chaque partie après les trois premiers mois sur préavis de 90 jours. Aucun total n'est calculé ;
  - le jour de la signature n'y est pas écrit (« in May 2026 ») : la ligne ne porte pas de date d'événement, comme les lignes « jour non écrit » d'avant ; son arête prend la date du dépôt ;
  - la ligne de la note (fenêtre 5 de `labs_corpus`) devient une abstention `duplicate_of_other_block` ;
  - les lettres CORRESP restent des pointeurs, de niveau E.

  (8) Données personnelles (D-0051 ; D-0058, point 10) : aucune personne physique n'est un nœud ni n'est citée. Les débiteurs des prêts de plateforme ne sont pas lus.

  (9) Réseau : aucune requête prévue. Si une pièce manquait, ce seraient les règles du client unique (§9.5), au journal.

  (10) Code, avant tout traitement :
  - `pipeline/nport.py` : termes désignant une entité, rattachement étendu, sélection et cellules de `nport_credit_mark`, prêts de plateforme, caractéristiques de dette jointes aux positions, exclusions, rendus ;
  - `pipeline/montages.py` : niveau par le triplet pour tous les montages, reclassement des blocs en place, source `span`, plafond du montage ;
  - registre des mesures, `schema.sql`, configuration ; tests.

  (11) Ordre et commits :
  - la décision, la configuration et le code, avec leurs tests ;
  - l'unité du 424B4, puis sa lecture ; commit ;
  - le reclassement des montages d'avant ; commit ;
  - les 145 blocs de la chaîne d'Anthropic, leur volume consigné ici avant lecture, la lecture ; commit ;
  - l'intégration : entités par extrait, réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (12) Limites connues avant calcul :
  - une marque de crédit par nœud mêle des tranches de rang différent. Les intitulés et les échéances sont publiés avec ;
  - une partie des prêts de CoreWeave est déclarée sous des abréviations (« CoreWeave CAC IV, LLC », « COREWEAVE COMPUTE AC »). Ces noms restent voisins, comme les prêts de Crusoe (« LLC » pour « Inc. ») ;
  - les titres structurés de banques déclarés en prêts se mesurent comme une dette de leur émetteur ;
  - les pièces EX-99 de la chaîne d'Anthropic ne donnent aucune arête à montant ;
  - la règle de majorité de la cotation (D-0065, point 15) reste comptée sur les seuls noms rattachés par une dénomination légale. Le scan n'a gardé que les positions hors des niveaux 1 et 2, et n'a compté les autres que sous la chaîne trouvée (« anthropic »), qui ne distingue pas « ANTHROPIC SERIES G » de « Anthropic, Inc. ».

  (13) Décomptes de la sélection codée, sans aucune valeur (`python -m pipeline.nport credit-volume`) :
  - la règle du terme rattache 143 positions sous 16 noms, comme au constat : CoreWeave 54, Anthropic 24, OpenAI 24, SpaceX 22, Nscale 19 ;
  - marques de crédit : 2 171 positions retenues, 2 127 au dernier dépôt de chaque série, de 69 nœuds et 318 séries, sur 94 dates du 2019-09-30 au 2026-07-31, soit 522 cellules. Le constat en comptait 2 176 : 8 positions de nominal nul ou négatif en sortent, dont 3 de Block, Inc. ;
  - prêts de plateforme écartés : 287 611 positions de Block, Inc. (72 dépôts) et 14 de Prosper Marketplace, Inc. (12 dépôts) ;
  - reclassement, à blanc : 85 blocs de 8-K changent de triplet. 71 changent de niveau, comme au constat. Les 14 autres sont des documents principaux de 8-K (Galaxy Helios 3, `labs_corpus` 5, `softbank_corpus` 6) : ils gardent le niveau C et passent de l'assurance `not_applicable` à `unaudited`, comme dans le registre des documents.

  (14) Traitement, 2026-10-21 :
  - 424B4 de SpaceX : unité préparée (paragraphes 1083 à 1089 du document, 713 caractères, niveau C), lue ; une ligne à montant (1,25 Md$ par mois, `fee`, `optional`, comme les commandes résiliables d'avant), et la ligne de la note devenue abstention `duplicate_of_other_block` (commit e73de1e) ;
  - reclassement en place (`python -m pipeline.montages retier`) : les 85 blocs du décompte à blanc, seuls le niveau, l'assurance et le statut de dépôt changés, textes et clés identiques. Le catalogue des montages est local (`db/`, hors suivi) : l'effet se lit dans les tables à l'intégration ;
  - chaîne d'Anthropic, préparée avec le plafond de 225 : 228 fenêtres, 225 textes distincts, tous en blocs ; les 80 premiers identiques champ pour champ à ceux de D-0064, les autres montages inchangés. Volume des 145 blocs, consigné avant lecture (liste `work/lists/anthropic_chain_2.txt`) : 411 832 caractères, 104 dépôts du 2023-04-27 au 2026-10-05 ; classes Fluidstack 40, infrastructure 61, autres 44 ; niveaux E 128 (127 pièces EX-99 et un document principal), D 13 (11 actes EX-4, 2 contrats EX-10), C 4 ; 78 fenêtres de groupes suivis (TeraWulf 29, Amazon 22, Cipher 12, AMD 5, Akamai, CoreWeave, Microsoft et NVIDIA 2 chacun, IREN et Dell 1), 67 d'autres déposants (Box 8, Wiley 4, ERock, GitLab et MongoDB 3, puis d'autres) ; le plus long fait 38 657 caractères.

  (15) Rendement de lecture des 145 blocs de la chaîne d'Anthropic, 2026-10-21, sans sous-agent :
  - 163 lignes : 57 observations, 106 abstentions, aucun rejet. Abstentions : `no_relevant_content` 62 (intégrations de produits et disponibilité des modèles), `duplicate_of_other_block` 31, `boilerplate_no_event` 9, `no_named_counterparty` 2, `out_of_scope_content` 2 ;
  - 16 observations portent une famille, toutes de blocs de niveau E (pièces EX-99) : `commercial` 11, `credit_support` 4, `financing` 1. Les 41 autres sont des lignes descriptives, sans famille ni montant ;
  - 10 lignes à montant, tel qu'écrit : Cipher, 5,5 Md$ d'AWS et 3,0 Md$ de Fluidstack (deux pièces), garantie de Google sur Fluidstack de 1,4 Md$ (deux pièces) ; TeraWulf, 3,7 et 6,7 Md$ de Fluidstack, garanties de Google de 1,8 et 3,2 Md$ ; Microsoft, gain de 3,2 Md$ sur Anthropic. Leurs blocs étant de niveau E, aucune ne donne d'arête à montant : leurs arêtes sont des relations (point 5) ;
  - relations sans montant : signées, la commande de 470 MW d'Anthropic chez ERock, l'accord pluriannuel d'Anthropic avec CoreWeave et celui de Meta avec Amazon (Graviton) ; `intent_non_binding`, la lettre d'intention de Fluidstack avec Soluna et les annonces d'AMD avec Anthropic (2 GW) et Microsoft (Azure) ;
  - aucun nom de personne physique n'est cité (contrôle sur les citations, notes et contreparties des 163 lignes).

  (16) Intégration et résultats (2026-10-21) :
  - entités par extrait, après le premier réassemblage. Deux noms nouveaux restaient en attente, sur des lignes descriptives de la chaîne ; chacun devient un alias né d'un extrait qui le définit (D-0021) :
    - « AWS », pour Amazon Web Services, Inc. : « Amazon Web Services ("AWS") cloud services to OpenAI » (8-K d'Amazon du 2026-02-27, déjà source de l'alias « Amazon Web Services ») ;
    - « Cerebras », pour Cerebras Systems Inc. : « the provision of the Services by Cerebras Systems Inc. ("Cerebras") to OpenAI OpCo, LLC ("OpenAI") » (S-1 de Cerebras, pièce EX-10.11, bloc lu). L'entité prend la dénomination de l'extrait et garde son CIK, comme Sprint Corporation (D-0022) ;
  - ligne du 424B4, avant le second réassemblage : elle porte son libellé de période tel qu'écrit, « per month through May 2029 ». Le grand livre affiche désormais ce libellé à côté du dernier montant, pour cette ligne et pour les trois qui en avaient déjà un (« through October 2030 » pour CoreWeave et OpenAI, « 2028 » pour SB Energy et OpenAI, « semestre clos le 30 juin 2026 » pour Amazon et Anthropic). La nature `fee` s'y lit « redevance » ;
  - réassemblages : le premier, à froid, en 1 193 s ; le second en 953 s, le mémo ne reprenant rien, la configuration ayant changé ; rendu en 42 s ;
  - tables, contre le dépôt d'avant D-0066 (commit a485fcd) :
    - observations 29 380 → 29 544 : 163 lignes de la chaîne et celle du 424B4 ; la ligne de la note devient une abstention. 91 lignes changent de niveau (C → E 57, C → D 34), 16 d'assurance seulement ;
    - arêtes 8 342 → 8 358, dont à montant 5 212 → 5 209. 17 arêtes nouvelles : les 16 de la chaîne, toutes des relations (niveau E), et celle du 424B4, à montant (niveau C) ; la relation de la note disparaît ;
    - quatre arêtes de Galaxy Helios perdent leur montant et deviennent des relations, leurs pièces étant des EX-99 (point 5) : les baux de CoreWeave de Helios I (4,5 Md$) et de Helios II (10,4 Md$ et 100 M$), et le prêt à terme de Helios I auprès de Deutsche Bank (434 M$). Leurs montants restent dans les lignes ;
    - entités 3 579 → 3 581 ;
    - exclusions 32 948 → 32 789 : `not_processed` − 67 et `out_of_scope` − 78, les fenêtres au-delà du plafond étant lues ; `pending_entity` − 16, les noms N-PORT rattachés par la règle du terme ; deux `out_of_scope` de prêts de plateforme (Block, Inc. : 287 611 positions dans 72 dépôts ; Prosper : 14) ;
    - mesures 177 892 → 179 108 ; contrôles 69 955 → 69 960 (C5 245 → 250) ;
  - grand livre d'Anthropic : SpaceX, redevance de 1 250 M$ (per month through May 2029), engagement d'achat, 424B4 du 2026-06-12. Aucun total n'est calculé ;
  - paires nouvelles, toutes `causalité non établie` : AMD → Anthropic, AMD → Microsoft, Amazon → Meta, CoreWeave → Anthropic, Microsoft → Anthropic (une arête chacune). Arêtes en plus : Alphabet → Fluidstack Ltd. 6 → 10, Cipher → Fluidstack Ltd. 3 → 5, Cipher → Amazon 3 → 4, TeraWulf → Fluidstack Ltd. 1 → 3 ; SpaceX → Anthropic reste à une arête, désormais à montant ;
  - cycles de E.6 : 106 → 108. AMD → OpenAI → Microsoft → AMD et CoreWeave → NVIDIA → Anthropic → CoreWeave, tous deux « relation commerciale doublée d'un financement », à titre descriptif ;
  - cellules de rang 1 : calculées 39 798 → 40 248 ; motifs `historique tronqué` 8 389 → 8 507 ;
  - N-PORT, rattachement étendu :
    - 71 cellules `nport_equity_mark` de plus (OpenAI 23, SpaceX 22, Anthropic 14, CoreWeave 12), aucune existante ne change ;
    - 23 cellules `nport_equity_held` augmentent. Anthropic au 2026-06-30 : 15 233 → 15 353 M$, sur 106 → 109 séries. OpenAI : 4 345 → 4 507 M$, sur 58 → 69 séries. CoreWeave au 2025-03-31 : 508 → 520 M$ ;
  - N-PORT, marques de crédit : 522 cellules sur 69 nœuds, du 2019-09-30 au 2026-07-31, comme au décompte (point 13). Seize couples nœud et catégorie ont une position dans les trois mois avant le 2026-07-31. Dernières marques :
    - Nscale, prêts, 100,0 % de 334,1 M$ sur 19 séries (2026-06-30) ;
    - CoreWeave, prêts, 99,8 % de 49,3 M$ (2026-07-31 ; plus bas 98,4 % au 2023-10-31) ;
    - SoftBank, prêt de premier rang de Kronos I (UK), 100,0 % de 35,0 M$ ;
    - SVF II Finco Cayman, 100,3 % de 16,9 M$ (plus bas 93,5 % au 2023-09-30) ;
    - Cloudera, 60,0 % ;
    - Beignet Investor LLC : 6 919 M$ au pair, à la seule date du 2025-09-30 (94 séries).

    Aucune des seize lignes ne porte de part en défaut, en arriéré d'intérêts ou en PIK. Sur l'ensemble, 70 cellules en portent une, sur huit couples nœud et catégorie :
    - General Motors (en euros et en dollars) : défaut jusqu'à 100 % ;
    - JPMorgan Chase & Co : défaut et PIK ;
    - T-Mobile : défaut 57 % ;
    - Nielsen : arriéré ;
    - AP Grange : arriéré jusqu'à 36 %, PIK jusqu'à 90 % ;
    - Core Scientific et iRobot : PIK 100 % ;
  - tests : 267, tous passés.

  (17) Limites constatées après calcul, sans changer la sélection fixée d'avance :
  - 54 cellules de marque de crédit dépassent 1,5. 52 sont des titres de dette de banques : des titres structurés, dont le nominal déclaré n'est pas celui d'une dette ordinaire. Le plus haut est à 25 750 fois le nominal (JPMorgan Chase Bank, N.A., 2025-12-31). Les deux autres sont Berkshire Hathaway (2,7, 2021-09-30) et Micron (8,5, 2021-06-30) ;
  - 75 cellules sont sous 0,5 : General Motors 32 et T-Mobile 9, proches de zéro ; JPMorgan Chase & Co 14 ; WeWork 9 ; Core Scientific 5 (25 à 30 %, d'octobre 2022 à octobre 2023) ; AP Grange 2 ; JPMorgan Chase Bank en livres turques 2 ; iRobot (46,9 %) et QVC (44,5 %), une chacune ;
  - ces cellules sont publiées telles que déclarées, et aucune n'est dans le tableau des trois derniers mois de la synthèse. Écarter les titres structurés des banques serait une décision nouvelle.

- **D-0067 — OpenAI et Anthropic : contrats déposés et calendrier des capacités (volet 8), événements propres aux laboratoires (volet 9). Règles fixées avant tout traitement.** (1) Décision de l'utilisateur, le 2026-10-21 : « Fais plutôt les volets 8 et 9 pour Anthropic et OpenAI ». Elle passe avant les deux propositions du rapport de D-0066 (titres structurés des banques, niveau 2), qui restent des propositions. Les deux volets viennent du remue-méninges de D-0059 (point 1) :
  - volet 8, « Contrats déposés et calendrier des capacités » : « Les pièces EX-10 et EX-4 des contreparties (bons AMD, contrats CoreWeave et Cerebras) donnent les tranches d'acquisition, les échéances et les clauses de sortie. Les GW annoncés pour chaque laboratoire, mis face aux GW que les hébergeurs déclarent avoir contractés » ;
  - volet 9, « Événements propres aux laboratoires, faute de comptes » : « un engagement réduit ; la fin d'une exclusivité ; une marque en baisse chez un actionnaire ; une garantie appelée ; un site retardé. Les règles seraient fixées avant toute lecture ».

  Lecture séquentielle par l'exécutant, sans sous-agent. L'as_of reste le 2026-10-07.

  (2) Constat, compté sans lecture et sans aucune valeur, sur les tables du commit 2abc3b1 et le cache :
  - contrats. Les pages de la recherche plein texte de la découverte (D-0036) sont en cache pour « OpenAI » (1 198 résultats) et « Anthropic » (463). Elles couvrent les formulaires racines 8-K, 10-K, 10-Q, S-1, S-4, S-11, F-1, F-4, 10-12B, 10-12G, 20-F et 40-F, du 2017-01-01 à l'as_of. La découverte n'en gardait que les EX-10. Relues depuis le cache, sans requête, elles donnent 47 pièces contractuelles distinctes (EX-10, EX-4, EX-2) qui nomment un laboratoire, déposées de 2024 à 2026 :
    - 12 où le laboratoire est partie, nommé dans les 3 000 premiers caractères :
      - OpenAI : le contrat-cadre de CoreWeave avec OpenAI OpCo (2025-09-25), le bon de souscription d'AMD et son accord de droits d'enregistrement (2025-10-06), la lettre d'OpenAI Group PBC à Amazon (2026-02-27), quatre pièces du S-1 de Cerebras (contrat-cadre, billet garanti, bon de souscription, accord de droits d'enregistrement ; 2026-04-17) et le contrat-cadre repris au S-1/A, l'accord de droits d'enregistrement de SB Energy, qui lie OpenAI Infra Holdings et NVIDIA (2026-09-21) ;
      - Anthropic : une pièce du S-1 de Nscale (2026-09-18) et le bon d'Akamai au profit d'Anthropic, PBC (2026-09-24).

      Sept de ces pièces ont été lues en entier, en phase 2 ou par la découverte. Les cinq de Cerebras ne l'ont été que par leur en-tête ;
    - 21 autres en cache, qui ne nomment le laboratoire qu'ensuite : actes et contrats de crédit de CoreWeave, contrats de déposants hors du modèle (fusions, licences) ;
    - 14 hors du cache, dont quatre de CoreWeave (S-1/A du 2025-03-12, EX-10.24 et EX-10.25 ; S-4/A, EX-10.32 ; 10-Q du 2025-11-13, EX-10.7 ; 10-K du 2026-03-02, EX-10.31) et l'EX-4.1 du S-1 de SB Energy ;
  - lignes des laboratoires. 305 observations nomment un laboratoire, et aucune ne porte de capacité structurée : MW et GW ne sont que dans les notes. Leurs citations nomment un MW ou un GW 17 fois, une exclusivité 5, une réduction ou une résiliation 9, un appel ou un défaut 4, un retard aucune. Aucun signal n'est propre aux laboratoires. Des 11 lignes du modèle à `trigger_occurred = yes`, aucune ne concerne un laboratoire ;
  - cache. Hors facteurs de risque, des paragraphes nomment un laboratoire et, dans le même paragraphe :
    - une capacité : 58 dans les pièces des montages, 2 dans les blocs de la découverte ;
    - un terme d'événement : retard 13, exclusivité 14, réduction ou résiliation 61 dans les pièces des montages, et 19 dans les blocs de la découverte.

    Presque tous ont déjà été lus, par `labs_corpus`, la chaîne d'Anthropic et Stargate, qui n'ont aucune fenêtre au-delà de leur plafond ;
  - marques : `nport_equity_mark` compte 330 cellules pour OpenAI (140 couples fonds et titre, dont 106 à au moins deux dates) et 620 pour Anthropic (246, dont 142), du 2024-03-31 au 2026-07-31 ;
  - l'annexe F est une liste fermée (« La liste est fermée ») : les événements du volet 9 ne s'y ajoutent pas.

  (3) Volet 8, contrats : montage `labs_contracts` :
  - pièces : les 47 pièces du constat, tirées des pages en cache de la découverte, sans recherche nouvelle (même période, mêmes formulaires racines). Les 14 absentes se tirent par le client SEC (point 9). Le type de pièce commence par EX-10, EX-4 ou EX-2 : contrats et instruments, de niveau D (§2.3) ;
  - pièce dont le laboratoire est partie : l'un de ses noms (« OpenAI », « Anthropic », jamais « Anthropic Capital ») figure dans les 3 000 premiers caractères du texte, préambule et parties compris. Dans ces pièces, un paragraphe qualifie s'il nomme un laboratoire ou une clause :
    - acquisition : vest, tranche, milestone, exercisable ;
    - durée : term of this agreement, initial term, renewal term, expiration ;
    - échéance : maturity date ;
    - sortie : terminate, termination, for convenience, change of control ;
    - capacité : MW, GW, megawatt, gigawatt ;
    - livraison : delivery date, delivery schedule, commencement date, ready for service ;
    - engagement minimal : minimum commitment, minimum purchase, take-or-pay ;
    - exclusivité : exclusive, first refusal.

    Dans les autres pièces, seul un paragraphe qui nomme un laboratoire qualifie ;
  - fenêtres : un paragraphe de part et d'autre, fondues quand elles se chevauchent. Un texte distinct se lit une fois. Aucun plafond. Les pièces dont le laboratoire est partie passent d'abord, puis du plus récent au plus ancien ;
  - fenêtre déjà lue (chaque paragraphe qualifiant figure dans un bloc lu du même dépôt) : dans une pièce dont le laboratoire est partie, elle se lit en lecture complémentaire (point 6) ; dans une autre, elle n'est pas servie.

  (4) Volets 8 et 9, corpus : montage `labs_events` :
  - documents, de 2017-01-29 à l'as_of, s'ils nomment un laboratoire :
    - les documents des groupes en cache (registre des documents) ;
    - les pièces des autres montages, hors celles de `labs_contracts` ;
    - les notes lues de la découverte (blocs des Notes Data Sets, sans document HTML), dont le texte du bloc tient lieu de document ;
  - un paragraphe qualifie s'il nomme un laboratoire et, dans le même paragraphe, une capacité (MW, GW, megawatt, gigawatt) ou un terme d'événement :
    - retard : delay, postpone, pushed back, behind schedule, later than expected ;
    - exclusivité : exclusiv-, first refusal ;
    - réduction ou fin : reduced, reduction, terminated, cancelled, not to renew, scaled back, wound down ;
    - appel de garantie : called, drew on, draw down, demanded payment, payment under a guarantee or backstop ;
    - baisse de valeur : impairment, unrealized loss, decrease in fair value or carrying value, downward revaluation.

    Un paragraphe de la section des facteurs de risque ne qualifie jamais (§14) ;
  - fenêtres comme au point 3. Une fenêtre déjà lue se lit en lecture complémentaire, une fenêtre jamais lue en lecture complète.

  (5) Champs nouveaux des lignes (registre, lecteur, chargement, `schema.sql`) :
  - `clause_kind` :
    - `vesting_tranche` : tranche d'acquisition ou d'exercice ;
    - `term` : durée, fin, renouvellement ;
    - `maturity` : échéance d'un prêt ou d'un billet ;
    - `termination_right` : clause de sortie ;
    - `exclusivity` : exclusivité, premier refus ;
    - `minimum_commitment` : engagement minimal, take-or-pay ;
    - `delivery_schedule` : livraison, mise en service ;
    - `none` ;
  - capacité :
    - `capacity_value` et `capacity_unit` (`MW` ou `GW`, tels qu'écrits, jamais convertis) ;
    - `capacity_kind` : `compute` (puces, serveurs, nuage), `hosting` (centre de données, charge IT), `power` (alimentation électrique), `unspecified` ;
    - `capacity_qualifier`, sur l'énumération des qualificatifs de montant ;
  - signaux nouveaux, avec `signal_present` : `commitment_reduction`, `exclusivity_end`, `guarantee_call`, `site_delay`, `mark_down`.

  Le chargement vérifie que la capacité figure dans la citation avec son unité, en chiffres ou en lettres jusqu'à vingt.

  (6) Conventions de lecture des deux montages, en plus de celles de D-0058 (point 22), D-0059 (point 4) et D-0064 (points 5 et 6) :
  - lecture complète : comme d'habitude (familles, montants, arêtes), plus les lignes de clause, de capacité et d'événement ;
  - lecture complémentaire : seules s'écrivent des lignes de clause, de capacité ou d'événement, toutes descriptives (sans famille). Le reste est déjà codé dans le bloc qui l'a lu, ce que la note dit. Sans rien de cela, c'est une abstention `duplicate_of_other_block` ;
  - ligne de clause :
    - `clause_kind`, la citation de la clause et sa date telle qu'écrite (`event_date`, `period_start`, `period_end`, ou `period_label` pour un délai relatif) ;
    - `conditionality` : `conditional` pour une tranche ou une sortie soumise à condition, `optional` pour une sortie de convenance ;
    - `trigger_description` ; `redacted` quand la clause est caviardée ; l'`instrument_key` du contrat ;
    - une quantité écrite (actions d'une tranche, minimum en dollars) va dans le montant, sans famille ;
  - ligne de capacité :
    - la capacité telle qu'écrite, son unité, son genre, `stage` (`signed`, `intent_non_binding`, `delivered`), le calendrier tel qu'écrit et la contrepartie ;
    - jamais d'addition, jamais de conversion entre MW et GW ;
    - une capacité en GPU ou en puces, sans MW ni GW, reste dans la note ;
  - ligne d'événement : le signal, `signal_present` et la date telle qu'écrite ; un jour non écrit laisse `event_date` vide. Elle dit ce que le texte écrit, sans inférence :
    - un retard est un « delay » écrit, ou un report par rapport à une date écrite plus tôt ;
    - une exclusivité finie est écrite comme finie ou restreinte ;
    - un engagement réduit l'est par le texte, jamais par la baisse d'un solde restant ;
    - un appel de garantie est un paiement ou une demande au titre d'une garantie ou d'un backstop ;
    - une marque en baisse est une perte de valeur, une dépréciation ou une baisse de juste valeur qu'un actionnaire comptabilise sur ses titres d'un laboratoire ;
  - données personnelles : aucun nom de personne physique n'est cité, ni signataire, ni destinataire d'une notification, ni dirigeant.

  (7) Mesures nouvelles (rang 2, §14), sans total ni score. Une ligne concerne un laboratoire si sa contrepartie, son payeur ou son bénéficiaire se résout en laboratoire, ou si sa citation le nomme :
  - `lab_contract_clause` : une cellule par ligne de clause qui concerne un laboratoire. Valeur : la quantité écrite s'il y en a une (montant, ou capacité), sinon le genre de clause. Drapeaux : dates, condition, caviardage, pièce ;
  - `lab_capacity` : une cellule par ligne de capacité qui concerne un laboratoire, valeur et unité telles qu'écrites. Jamais additionnées, ni entre elles, ni aux dollars ;
  - `lab_event` : par laboratoire, événement et trimestre civil, de 2021 T1 à 2026 T3 (fenêtre du modèle) :
    - L1, engagement réduit : signal `commitment_reduction` ;
    - L2, fin d'une exclusivité : `exclusivity_end` ;
    - L3, marque en baisse chez un actionnaire : une valeur par action `nport_equity_mark` inférieure à celle de la date précédente du même fonds et du même titre, ou une ligne `mark_down` ;
    - L4, garantie appelée : `guarantee_call`, ou une ligne de soutien de crédit qui concerne le laboratoire, à `trigger_occurred = yes` ;
    - L5, site retardé : `site_delay`.

    Une cellule porte `event` quand un tel fait est daté dans le trimestre (date d'événement, sinon fin de période, sinon date de la pièce, notée), avec ses pièces. L3 porte `no_event` quand au moins une marque du trimestre a une date précédente et qu'aucune ne baisse, et sinon `not_determinable` (`prior_period_missing` ou `not_disclosed`). L1, L2, L4 et L5, sans fait daté dans le trimestre, portent `not_determinable` (`not_processed`) : seules les pièces en cache sont lues, et une source non lue ne passe jamais pour un trimestre sans événement ;
  - ces cellules n'entrent ni dans l'annexe F, ni dans les mesures de financement, l'exposition, les paires, les cycles ou les conclusions.

  (8) Rendus, dans la synthèse après le grand livre ; le détail par ligne va dans `series.md` :
  - « Contrats des laboratoires » : par laboratoire et par contrat, les tranches, échéances, sorties, exclusivités et minimums, avec leurs dates et leurs pièces ;
  - « Calendrier des capacités » : par laboratoire, les capacités de calcul (`compute`) face aux capacités d'hébergement et d'électricité (`hosting`, `power`), chacune telle qu'écrite, avec son statut, son calendrier et sa pièce. Jamais de total ;
  - « Événements propres aux laboratoires » : les cellules `event`, le compte des cellules par statut, et la mention que cette liste n'est pas l'annexe F.

  (9) Réseau : seules les 14 pièces absentes se tirent, par le client SEC unique et journalisé : au plus 4 requêtes par seconde, jamais deux processus réseau en parallèle, une pause d'au moins 10 minutes après tout 403. Aucune recherche plein texte nouvelle.

  (10) Données personnelles (D-0051 ; D-0058, point 10) : aucune personne physique n'est un nœud ni n'est citée.

  (11) Code, avant tout traitement :
  - `pipeline/montages.py` :
    - source `hits` : pages de recherche en cache, sans requête, filtrées par type de pièce ;
    - test de partie, termes de clause, `window`, `require`, lecture complémentaire ;
    - corpus élargi (`source: lab_corpus`), où les notes de la découverte comptent par le texte de leur bloc ;
  - registre, lecteur et chargement : champs et signaux nouveaux, vérification de la capacité dans la citation ; `schema.sql` ;
  - `pipeline/lab_terms.py` : cellules `lab_contract_clause`, `lab_capacity` et `lab_event` ; assemblage ; rendus ; tests.

  (12) Ordre et commits :
  - la décision, la configuration et le code, avec leurs tests ; commit ;
  - le tirage des pièces absentes et la préparation des deux montages, leur volume consigné ici avant lecture ; commit ;
  - la lecture de `labs_contracts`, puis de `labs_events`, avec des commits par lot et le rendement consigné ;
  - l'intégration : entités par extrait, réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (13) Limites connues avant lecture :
  - les contrats non déposés n'ont aucune pièce : Microsoft, Google et Amazon avec Anthropic ; Oracle, Broadcom et NVIDIA avec OpenAI. Leurs clauses ne se lisent que dans les résumés des déposants ;
  - les calendriers caviardés restent caviardés (bon d'AMD : pièces E et F) ;
  - la recherche de la découverte s'arrête à ses formulaires racines : un contrat déposé avec un 6-K, un 424B ou un N-2 n'y figure pas ;
  - une capacité écrite sans le laboratoire n'est pas une capacité du laboratoire, par exemple le bail d'un hébergeur avec Fluidstack sans « Anthropic » dans le texte ;
  - L1, L2, L4 et L5 ne voient que les pièces en cache.

  (14) Traitement, 2026-10-21, et corrections avant toute lecture :
  - pièces des contrats : relues depuis les pages en cache, sans requête, 49 résultats et 47 pièces (EX-10 32, EX-4 10, EX-2 7), comme au constat. Les 14 absentes sont tirées par le client SEC : 14 requêtes, aucun refus. Dans deux pièces, aucun paragraphe ne qualifie : un 20-F de BHP Group, une pièce d'iSpecimen ;
  - corrections du corpus de `labs_events`, avant lecture :
    - un document n'y entre qu'en texte (`.htm`, `.html`, `.txt`). Un PDF lu comme texte brut, le rapport annuel de Chatham Lodging Trust venu du montage Stargate, donnait une fenêtre de 11 millions de caractères ;
    - une pièce que la règle d'un autre montage écarte reste écartée : le texte extrait par EDGAR d'une lettre déjà lue en PDF (D-0064, point 12) ;
    - un déposant hors des groupes (Cerebras, SB Energy, Nscale, Athene, SK Telecom) prend le nom que portent ses blocs déjà au catalogue ;
  - le test de couverture reste celui du point 3 : un paragraphe déjà lu figure, aux blancs près, dans un bloc lu du même dépôt. Les 17 fenêtres de lecture complète du corpus sont pour l'essentiel des paragraphes que les blocs lus n'avaient pas couverts (S-1 de SB Energy et de Nscale hors des sections lues, communiqués de tiers). D'autres sont des notes de Cerebras déjà lues dans leur version des Notes Data Sets, découpée autrement : la lecture y vérifie les lignes du même dépôt avant de coder ;
  - volume, consigné avant lecture :
    - `labs_contracts` : 224 fenêtres, 206 textes distincts, tous en blocs (liste `work/lists/labs_contracts.txt`), 438 163 caractères, 26 dépôts du 2024-02-22 au 2026-09-24, tous de niveau D. Contrats dont un laboratoire est partie : 67 blocs en lecture complète (Cerebras 41, CoreWeave 15, SB Energy 11) et 117 en lecture complémentaire (Nscale 47, Akamai 18, AMD 17, SB Energy 17, Amazon 14, Cerebras 3, CoreWeave 1). Autres pièces : 22 blocs en lecture complète (CoreWeave 9, SB Energy 1, douze déposants hors du modèle un chacun). 30 fenêtres de pièces sans laboratoire partie, déjà lues, ne sont pas servies ;
    - `labs_events` : 233 documents nomment un laboratoire (135 du registre des documents, 98 des autres montages ; les 27 blocs lus de la découverte qui en nomment un y sont déjà par leur document). 146 fenêtres, 130 textes distincts, tous en blocs (liste `work/lists/labs_events.txt`), 327 166 caractères, 75 dépôts du 2023-04-25 au 2026-09-24 : 113 en lecture complémentaire, 17 en lecture complète ; 58 blocs nomment une capacité. Niveaux : B 42, C 39, E 37, A 12. 14 fenêtres d'un facteur de risque ne qualifient pas. Principaux déclarants : Microsoft 25, Amazon 18, TeraWulf 13, SB Energy 10, AMD 10 ;
    - en tout, 336 blocs et 765 329 caractères. Les autres montages restent identiques bloc pour bloc.

  (15) Correction avant lecture, avant toute ligne soumise. Une fenêtre de contrat ne nomme souvent pas le laboratoire : la clause dit « the Warrantholder » ou « the Investor », le préambule seul le nomme. Le bloc d'une pièce dont le laboratoire est partie porte donc les noms lus dans ses 3 000 premiers caractères (`party_terms`), et une ligne de ce bloc concerne ce laboratoire (point 7). La contrepartie de la ligne reste vide si la fenêtre ne la nomme pas : la validation exige qu'un nom de contrepartie figure dans le bloc. Les blocs préparés restent les mêmes, textes et clés compris ; seul ce champ s'ajoute.

  (16) Lecture, 2026-10-21, sans sous-agent, lot par lot dans l'ordre servi, `labs_contracts` puis `labs_events` :
  - `labs_contracts` : 206 blocs, dont 48 avec des lignes. 80 lignes :
    - 67 lignes de clause : sortie 20, durée 15, tranche 12, exclusivité 6, calendrier de livraison 5, échéance 5, minimum 4. Deux portent aussi une capacité signée : les baux de 800 MW-IT d'Orion (ligne 1 de l'annexe E du bon refondu de SB Energy) et 250 MW de Cerebras d'ici la fin de 2026 ;
    - 6 lignes de famille (4 bons remis au client, un engagement d'achat, un prêt) et 7 lignes descriptives ;
    - 158 abstentions : 90 doublons, 68 sans contenu utile (en-têtes, définitions, signatures, clauses types) ;
  - `labs_events` : 130 blocs, dont 27 avec des lignes. 48 lignes :
    - 22 lignes de clause : durée 6, sortie 4, calendrier de livraison 4, tranche 3, exclusivité 3, minimum 2 ;
    - 25 lignes de capacité, dont 2 sont aussi des clauses, 16 pour OpenAI et 9 pour Anthropic : 11 signées, 11 intentions non contraignantes, 3 sans statut écrit (`stage` à `none` : Frontier, 1,4 GW, et Lighthouse, environ 1,0 GW, chez DigitalBridge ; Abilene, 1,2 GW, dans un prospectus de fonds de GraniteShares) ;
    - une ligne d'événement : le 10-Q de Microsoft du 29 octobre 2025 écrit « Microsoft will no longer have a right of first refusal to be OpenAI's compute provider » (`exclusivity_end`, 2025-10-28) ;
    - une ligne de famille, la garantie de valeur résiduelle de 105 Md$ de NVIDIA au S-1 de SB Energy, et une ligne descriptive ;
    - 103 abstentions : 69 doublons, 34 sans contenu utile ;
  - doublons, convention tenue pendant la lecture : un fait d'un déclarant n'a qu'une ligne de clause ou de capacité. Une reprise est une abstention `duplicate_of_other_block`, dont la note nomme le bloc qui porte la ligne. Un chiffre ou un statut qui change fait une ligne nouvelle : 4,25 GW-IT au S-1 de SB Energy, 3,78 GW-IT restants au S-1/A ; 250 MW au contrat de Cerebras, 750 MW engagés et une option de 1,25 GW à son 10-Q :
    - `labs_events`, servi du plus récent au plus ancien : la ligne va au bloc le plus ancien du même déclarant. Les renvois tenus pendant la lecture sont tous soldés ;
    - `labs_contracts` : un contrat déposé deux fois porte ses clauses sur la version servie la première. Le contrat-cadre de Cerebras avec OpenAI, déposé avec le S-1 du 17 avril 2026 puis avec le S-1/A du 4 mai, est codé sur le S-1/A : ses clauses sont connues au 4 mai, 17 jours après le premier dépôt. Le contrat « bare metal » de CoreWeave est codé sur la pièce 10.32 du S-4/A, déposée le même jour que la pièce 10.1 du 8-K, lue plus tôt (bloc 6eb5ce02) ;
  - corrections pendant la lecture, sans changer les règles :
    - contrôle de capacité (`load.capacity_in_quote`), plus étroit que la règle du point 5 (la capacité figure dans la citation). Un qualificatif d'une liste fermée (additional, more, new, incremental, further, total, aggregate) peut séparer le nombre de l'unité : « approximately 3.8 additional gigawatts », 10-Q de NVIDIA. Un nombre en lettres suivi du même nombre entre parenthèses vaut ce nombre : « one (1) gigawatt », « six (6) gigawatts », 8-K d'AMD. Restent refusés deux qualificatifs, un multiplicateur (« 3.8 billion gigawatts ») et une discordance (« six (5) »). Tests ajoutés ; les lignes refusées l'avaient été avant tout écrit ;
    - deux clés d'instrument alignées sur celles déjà au registre : `stargate:crusoe_abilene` (bloc a4ec6722) et `nvda:anthropic_compute_1gw` (bloc be8ff4b9) ;
    - lignes en double : `submit` ajoute au fichier du bloc, il ne le remplace pas. Les trois blocs resoumis gardaient leurs lignes d'avant dans la même passe : 8473dfde, resoumis avec une septième ligne sur l'incitation que fut le bon d'origine, puis a4ec6722 et be8ff4b9, pour leurs clés. Ces 9 lignes périmées sont retirées avant le réassemblage. Contrôle : chacun des 336 fichiers est identique à la dernière soumission de son bloc, et aucun autre fichier du corpus n'a de ligne en double dans sa dernière passe ;
  - entités par extrait :
    - alias « SE Global Holdings, Inc. » de SB Energy, Inc. : « SB Energy, Inc. (formerly SE Global Holdings, Inc.) », note 1 des états du S-1/A (bloc d093b87e). C'est le payeur des 3 lignes de famille du bon refondu (bloc 8473dfde) ;
    - OpenAI, Inc. : pas de rattachement au laboratoire. Aucun extrait n'affirme son lien avec lui ni ne la désigne par « OpenAI ». La seule ligne qui la nomme (bloc 258bccc7, investisseurs permis du crédit renouvelable de SB Energy) est descriptive. Le nom prend son entité et son groupe propres (règle de D-0022), sans arête ; les effets sont au point 17 ;
  - limites constatées à la lecture, en plus de celles du point 13 :
    - L3 : les pertes de Microsoft sur ses placements mis en équivalence, OpenAI compris, sont une quote-part de résultat, ni dépréciation ni baisse de juste valeur (point 6) : aucune ligne `mark_down`. Exemple : 4,1 Md$ au trimestre clos le 30 septembre 2025, ligne déjà au corpus. Cinq rapports de Microsoft lus en complément le notent ;
    - L1 : la facilité d'au plus 20,0 Md$ d'Amazon envers Anthropic, ramenée à 15,0 Md$ disponibles par la souscription de la série H, est la baisse d'un solde, pas un engagement réduit (point 6) ;
    - L1 : le retrait d'OpenAI de Stargate UK en avril 2026 (S-1 de Nscale) est une ligne descriptive d'une lecture antérieure (bloc 96831d93), sans signal. Le corpus de `labs_events` ne l'a pas servi : « withdrew » n'est pas un terme du point 4. L1 d'OpenAI pour 2026 T2 reste `not_determinable` ;
    - L2 : entre le 10-K de Microsoft de 2023 (« As OpenAI's exclusive cloud provider », bloc e0769154) et celui de juillet 2025 (API exclusive à Azure et droit de premier refus, bloc 99b35d57), aucune fenêtre servie n'écrit la fin de l'exclusivité de nuage. Ces deux extraits sont des lignes de clause, sans événement. Le seul événement L2 est la fin du droit de premier refus, en 2025 T4 ;
    - calendriers : l'annexe E du bon refondu de SB Energy n'est servie que jusqu'à sa ligne 3, réservée ; les lignes 4 à 8 manquent. L'annexe A du bon de Cerebras ne montre que sa première tranche, sans la colonne de MW cumulés des suivantes. Le calendrier de livraison du contrat de Cerebras (annexe A) et celui du bon d'AMD (annexe E) sont caviardés en entier.

  (17) Intégration et résultats (2026-10-21) :
  - entités : l'alias de SB Energy (point 16) rattache au groupe SoftBank le payeur des lignes du bon refondu. OpenAI, Inc. prend son entité et son groupe propres (D-0022) :
    - les 4 positions N-PORT d'un fonds déclarées sous « OpenAI, Inc. » (2023-12-31 au 2024-09-30), en attente jusque-là, s'y rattachent. Elles sont hors du laboratoire : 4 cellules `nport_equity_held` et 4 `nport_equity_mark` vont à ce groupe propre. Leurs titres sont « openai inc » puis « empros technologies », publiés tels que déclarés ;
    - les 28 archives N-PORT des non-cotés (2019 T4 à 2026 T3) passent `not_processed` : scannées avec le lexique d'avant, elles n'ont pas cherché les deux dénominations légales nouvelles (D-0065, point 14). Pour OpenAI, Inc., le terme « OpenAI » gardait déjà ses positions ; pour SE Global Holdings, aucun terme ne la gardait. Lever ces marques demande de retirer et de rescanner les 28 archives, ce qui n'est pas fait ;
  - corrections après le premier réassemblage, avant le second :
    - grand livre (D-0060, point 6) : à date égale, la clé de l'arête départageait les montants. Les 4 562 791 bons déchus le jour de la remise du bon refondu passaient pour le dernier montant du bon de SB Energy envers OpenAI. Une arête close (`terminated`) ne l'emporte plus sur une arête en vigueur de même date : la cellule porte les 3 991 809 bons du bon refondu. Une clôture datée plus tard reste le dernier état connu. C'est la seule cellule touchée ; test ajouté ;
    - rendus des volets 8 et 9. Un déclarant hors des groupes, sans entité au registre, porte le nom de son dépôt (WEC Energy Group, GraniteShares ETF Trust, ERock) au lieu de la clé de son groupe. Une pièce ne répète plus son type quand il vaut le formulaire. Une baisse de marque s'affiche avec les décimales qui la montrent (30,0045 puis 30,0000, et non 30,00 et 30,00). La synthèse donne les trois plus fortes baisses de chaque trimestre et leurs pièces ; toutes vont dans `series.md`. Tests ajoutés ;
  - réassemblages : le premier, à froid, en 1 287 s, après un lancement arrêté pour retirer les lignes périmées ; le second en 1 004 s, le mémo ne reprenant rien, le code ayant changé ; rendu en 42 s ;
  - tables, contre le dépôt d'avant D-0067 (commit 2abc3b1) :
    - documents 25 296 → 25 310 : les 14 pièces tirées ;
    - observations 29 544 → 29 933 : 128 lignes et 261 abstentions ;
    - arêtes 8 358 → 8 365. Les 7 arêtes nouvelles viennent des lignes de famille :
      - les trois arêtes du bon de SB Energy envers OpenAI Infra Holdings : 3 991 809 actions, 4 562 791 actions déchues, le bon d'origine ;
      - la garantie de valeur résiduelle de 105 Md$ de NVIDIA au S-1 de SB Energy ;
      - les actions remises par CoreWeave en contrepartie au client ;
      - l'engagement d'achat et le prêt de fonds de roulement d'OpenAI envers Cerebras ;
    - entités 3 581 → 3 584 : l'alias et OpenAI, Inc. (entité et appartenance) ;
    - exclusions 32 789 → 32 832. `out_of_scope` + 16 : les deux pièces sans paragraphe qualifiant et 14 fenêtres de facteurs de risque. `not_processed` + 28 : les archives N-PORT. `pending_entity` − 1 : OpenAI, Inc. ;
    - mesures 179 108 → 179 464 : `lab_event` 230, `lab_contract_clause` 89, `lab_capacity` 27, `lab_ledger` 2, `nport_equity_held` et `nport_equity_mark` 4 chacune ; contrôles 69 960, inchangés ;
  - cellules existantes qui changent : 352, toutes par la règle de §3.2 qu'applique `circularity` : une clause caviardée d'un contrat de la paire empêche d'établir « jamais ». Les lignes de clause caviardées touchent quatre instruments déjà liés aux paires : le bon d'AMD (annexe E, calendrier d'acquisition), le bon d'Akamai (délai de régularisation), l'engagement d'Amazon envers OpenAI (date butoir), et les deux contrats-cadres de CoreWeave avec OpenAI :
    - `financed_status` : 316 cellules passent de « jamais » à « non déterminé (caviardé) » : Akamai → Anthropic 108, AMD → OpenAI 108, Amazon → OpenAI 100. D'où les cellules de rang 1 calculées 48 643 → 48 327 ;
    - `documented_revenue_dependency` : 30 cellules, motif « précondition non remplie » → « caviardé » ; annexe E, E2 d'Amazon et OpenAI aux trois seuils : même changement de motif. Le résultat de E.7 reste à 56 % d'issues indéterminées sur 170 ; une issue change de motif ;
    - `contract_coverage` : AMD et OpenAI 50 % → 0 %, Amazon et OpenAI 80 % → 60 %, CoreWeave et OpenAI 60 % → 20 % ;
    - les conclusions des paires ne changent pas ; Akamai et Anthropic passent en recherche incomplète (« une clause de la paire est caviardée »), et le cycle Akamai → Anthropic → Akamai de même ;
  - clauses : 89 cellules, OpenAI 59 sur 19 contrats ou instruments, Anthropic 30 sur 6. 15 portent une quantité écrite (actions 5, pourcentages 4, dollars 3, GW 2, MW 1) ; les autres le genre de clause. 82 sont datées par leur pièce, faute de date écrite ;
  - capacités : 27 cellules, OpenAI 18 et Anthropic 9, jamais additionnées. Calcul : OpenAI 8, Anthropic 4. Hébergement : 8 et 4. Électricité : 2 et 1. Statuts : signées 13, intentions 11, statut non écrit 3 (OpenAI) ;
  - événements : 230 cellules :
    - L2 d'OpenAI en 2025 T4 : fin du droit de premier refus de Microsoft, 10-Q du 29 octobre 2025 ;
    - L3 : Anthropic 4 trimestres (2024 T2, 2024 T3, 2025 T2, 2025 T4), OpenAI 3 (2026 T1, T2 et T3). Six trimestres sans baisse pour chacun. Les autres sont non déterminés : 13 et 14, dont un `prior_period_missing` chacun ;
    - L1, L4 et L5 : aucun fait daté ; 23 trimestres non déterminés par laboratoire ;
  - tests : 279, tous passés.

  (18) Limites constatées après calcul, sans changer les règles fixées d'avance :
  - L3 compte toute baisse, même d'un cent :
    - Anthropic, 2024 T2 et 2024 T3 : 30,0045 → 30,0000. En 2025 T4, la plupart des baisses vont de 140,97 à 140,96 ; les plus fortes vont de 147,49 à 140,97 et de 154,15 à 148,29 ;
    - les baisses nettes sont les suivantes. Anthropic 2025 T2 : 56,09 → 50,53 et 58,50 → 52,74. OpenAI 2026 T1 : 651,79 → 483,12, un fonds, titre « openai global llc ». Ensuite 693,90 → 687,69 (2026 T2) et 687,69 → 678,11 (2026 T3) ;
    - un seuil de baisse serait une décision nouvelle ;
  - les effets de §3.2 ci-dessus suivent la règle existante. Garder les lignes des volets 8 et 9 hors des mesures des paires serait une décision nouvelle : la caviardure d'une clause de ces contrats est un fait de leurs pièces ;
  - « OpenAI, Inc. » chez un fonds, au titre « empros technologies », reste rattachée à son groupe propre : rien n'établit qu'il s'agit du laboratoire.

- **D-0068 — Carnet de commandes : RPO total dérivé de l'axe d'horizon, dépendance du carnet (E.3) calculée selon §3.3, carnet contracté par client nommé (rang 2, §14). Règles fixées avant tout calcul et toute lecture.**
  (1) Décision de l'utilisateur, le 2026-10-22 : « Fais 1, 2 et 3 », après le constat demandé la veille (« Ok investigue en profondeur la piste 1 »). Les trois volets :
  - volet 1 : rétablir `rpo_total` quand le seul RPO balisé est celui « à partir du lendemain de la clôture » ;
  - volet 2 : remplacer la cellule fixe de `documented_backlog_dependency` (toujours « anonyme », sans recherche) par la règle de §3.3, avec ses cellules de fin de trimestre ;
  - volet 3 : mesure nouvelle, la part du carnet contracté d'un vendeur attribuée par lui à un client nommé, financé ou non.

  (2) Constat, compté sans aucune valeur, sur les tables du commit 5ddb6af. Deux paragraphes de CoreWeave ont été vus, chiffres masqués, pour en connaître la forme :
  - univers de E.3 : 75 paires financées sur 19 fournisseurs, 231 exercices. Dans 18 paires le client achète au fournisseur (arête commerciale du client vers le fournisseur), dont 8 où le fournisseur publie un RPO ; dans 3 le fournisseur achète au client ; 54 sont de pur financement, sans arête commerciale. 62 des 231 exercices ont un `rpo_total` à la même date ;
  - attributions nommées de RPO par le fournisseur lui-même :
    - Amazon balise `RevenueRemainingPerformanceObligation` sur `srt:MajorCustomersAxis` : un solde au membre OpenAI au 2026-03-31, et pour Anthropic une hausse sur le trimestre clos le 2026-06-30, pas un solde ;
    - Microsoft ne balise son RPO que pour les « commercial customers », une catégorie de clients (37 faits) ;
    - aucun autre groupe ne balise un RPO par client ; aucun `ConcentrationRiskPercentage1` ne porte sur un repère de carnet ;
  - textes : dans les rapports des fournisseurs des paires de E.3, seuls deux paragraphes nomment un client avec du vocabulaire de RPO, aux 10-Q de CoreWeave du 2025-03-31 (le RPO exclut le contrat avec OpenAI) et du 2025-06-30 (il l'inclut, sans montant). Les paragraphes de Microsoft qui nomment OpenAI ne parlent jamais de RPO ; ceux d'Amazon parlent d'engagements. Aucune attribution n'existe à une fin d'exercice ;
  - `rpo_total` : 24 trimestres n'ont pour RPO balisé qu'un fait unique sur `RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis`, au membre du lendemain de la clôture (Amazon 21 depuis le 2020-09-30, Applied Digital 2, Micron 1). Ailleurs, aucun fait de RPO (Cipher, Hut 8, TeraWulf, Marvell : leurs contrats d'IA sont des baux) ou des ventilations par produit (Core Scientific, Riot) ;
  - loyers futurs à recevoir d'un bailleur (`LessorOperatingLeasePaymentsToBeReceived`, location-financement) : balisés chez Applied Digital (7 dates), Core Scientific (9), TeraWulf (4), Galaxy (1), IREN (1), Riot (2), Supermicro (9), Dell (30), Akamai (6), Marvell (7) ; ASML par échéance seulement ; ni Cipher ni Hut 8. Aucune grandeur du modèle ne les reprend ;
  - valeurs de contrats attribuées à un client nommé, déjà en tables et admissibles (niveaux A à D) : 44 arêtes, 22 paires, 14 vendeurs. Les grands baux des hébergeurs (TeraWulf et Fluidstack, Cipher avec AWS et Fluidstack, Galaxy et CoreWeave) n'ont leurs montants que dans des communiqués EX-99, de niveau E : ce sont des relations sans montant ;
  - volume des paragraphes candidats (dépôts des vendeurs, niveaux A à D, hors facteurs de risque, qui nomment un client du vendeur et parlent de carnet, de valeur de contrat ou de loyers) : 118 paragraphes, dont 76 déjà dans un bloc lu et 42 non (191 538 caractères), chez 12 vendeurs et pour 19 paires.

  (3) Volet 1, `rpo_total` (§6.2). Un dépôt (instance) sans fait non dimensionné de `RevenueRemainingPerformanceObligation` à une date t peut porter un seul fait de ce concept dont l'unique axe est l'axe d'horizon, au membre t + 1 jour, sans autre fait de ce concept sur ce seul axe à t (aucune autre tranche) :
  - ce fait est le RPO total à t : un carnet dont la satisfaction commence le lendemain de la clôture, sans autre tranche, est le carnet entier. Il entre dans `rpo_total` comme une occurrence du dépôt, avec le drapeau `derived_from: timing_axis_next_day` ;
  - un fait à plusieurs axes (client et horizon) n'est ni le total ni une tranche : il n'empêche ni ne fait la règle ;
  - aucune autre dérivation : ni somme de tranches, ni tranche par produit ou par segment, ni membre de client. `rpo_within_12m` et `rpo_beyond_12m` ne changent pas ; une durée d'horizon (`Period1`) ne se convertit jamais en tranche à douze mois ;
  - C13 lit les dépôts eux-mêmes et ne change pas.

  (4) Volet 2, `documented_backlog_dependency` (§3.3, E.3) :
  - cellules :
    - à chaque fin d'exercice du fournisseur dans la fenêtre, pour les paires financées, comme avant (exercice où F est active au moins un trimestre) : seules celles-ci entrent dans E.3 ;
    - à chaque autre fin de trimestre du fournisseur où F (`exposure_outstanding`) est active : série publiée, jamais dans E.3 ;
    - deux vues, `as_known` et `revised`, aux dates de coupure de la dépendance de revenu (exercices) et du statut financé (trimestres) ; termes `total` et `beyond_12m` ;
  - dénominateur : `rpo_total` du fournisseur à la date (volet 1 compris) ; `rpo_beyond_12m` pour le second terme ;
  - numérateur, attribué par le fournisseur lui-même, niveau A à C, connu à la coupure :
    - un fait balisé de RPO à la date sur `srt:MajorCustomersAxis`, dont le membre nomme le client (nom du registre contenu dans le nom local du membre, le plus long l'emporte), sans autre axe que celui d'horizon au lendemain de la date. Une catégorie de clients, un segment ou un marché (« commercial customers ») ne compte jamais ;
    - une ligne de carnet (point 7) de base `rpo`, d'énoncé `remaining`, datée de la date (`period_end`), pour ce client ;
    - une ligne d'énoncé `excluded` à la date : le RPO exclut le contrat du client. Le numérateur vaut alors zéro, pourvu qu'aucun autre contrat entre eux, signé à la date au plus tard, ne figure dans les lignes de carnet ; sinon la cellule reste non déterminée ;
    - `beyond_12m` : seulement si la part du client au-delà de douze mois est elle-même écrite ou balisée ;
  - jamais au numérateur : une hausse ou une baisse (`change`), une valeur de contrat, l'engagement du client (na01), une estimation de la direction (§3.5) ;
  - statuts et motifs :
    - le fournisseur ne publie aucun RPO à la date : `not_determinable`, avec le motif de `rpo_total` (`not_disclosed`, `concept_unresolved`) ;
    - numérateur trouvé : `computed`, valeur = numérateur ÷ dénominateur ;
    - le client achète au fournisseur, sans attribution : `not_determinable`, `anonymous`, comme avant. Les drapeaux disent ce qui existe sans entrer dans la valeur : inclusion sans montant, hausses, valeurs de contrats ;
    - le client n'achète pas au fournisseur (aucune arête commerciale du client vers lui) : `not_determinable`, `precondition_not_met`, drapeau « aucune vente du fournisseur au client documentée » ;
    - aucune borne : rien n'oblige à publier le RPO par client, à la différence d'ASC 280-10-50-42 pour le revenu ;
  - E.3 se calcule comme avant, sur les seules cellules de fin d'exercice, terme `total` (le RPO de fin d'exercice). La table des exercices gardait jusqu'ici la dernière des deux cellules, `beyond_12m`, sans effet tant qu'elles étaient identiques ; précision consignée en codant, avant tout calcul. E.7 ne change pas (E.1 et E.2).

  (5) Volet 3, mesures nouvelles (rang 2, §14), hors de l'annexe E :
  - `lessor_lease_receipts` : loyers futurs non actualisés à recevoir d'un bailleur à une date, tels que publiés (`LessorOperatingLeasePaymentsToBeReceived` et, s'il est publié, `SalesTypeAndDirectFinancingLeasesLeaseReceivablePaymentsToBeReceived`, faits non dimensionnés). Une cellule seulement aux dates où l'un est publié ; la somme des deux est la seule addition, notée ;
  - `contracted_backlog_share` (vendeur S, client nommé C, date t, terme) : part du carnet contracté de S que S attribue lui-même à C :
    - paires : tout groupe S du modèle et tout client C qu'une ligne de carnet de S nomme, ou qu'un fait balisé de RPO de S nomme ; aucune condition de financement ;
    - termes, jamais mêlés ni additionnés : `rpo` (contrats de services, ASC 606), sur `rpo_total` ; `lease` (S bailleur, ASC 842), sur `lessor_lease_receipts`. Le terme d'un contrat est la base de ses lignes de carnet ; un contrat de base `unspecified` n'entre dans aucun terme et reste en drapeau ;
    - dates : chaque fin de trimestre ou d'exercice de S, de la première date d'une ligne sur C à l'as_of, où le dénominateur du terme existe (publié) ; s'y ajoutent les dates d'un reste ou d'une exclusion écrits, où le dénominateur peut manquer (`not_determinable`, son motif). Vue `as_known` à l'as_of. Précision consignée en codant, avant tout calcul : sans elle, le motif « dénominateur absent » ne pouvait naître ;
    - `computed` : S écrit le reste dû par C à t (ligne `remaining` datée de t, ou fait balisé de RPO par client à t), ou l'exclusion de ses contrats (zéro, aux conditions du point 4) ;
    - `bounded`, borne basse 0 : borne haute = valeur publiée ÷ dénominateur, plafonnée à 1, avec `bound_basis = published_contract_value`. La valeur publiée est la dernière ligne `total_contract_value` de C datée au plus tard de t. À défaut, c'est la somme, sur les contrats de S avec C signés au plus tard à t, de la dernière valeur de chaque contrat et des hausses (`change`) qui la suivent. Cette somme n'est admise que si chaque contrat de S avec C dans les lignes de carnet a une valeur. Hypothèse déclarée en drapeau : S publie chacun de ses contrats importants avec C (Item 1.01 du 8-K), et la valeur d'un contrat, totale ou maximale (« up to »), majore ce qu'il en reste ;
    - `not_determinable` : dénominateur absent (son motif) ; aucune valeur ni aucun reste (`not_disclosed`) ; devises différentes (`mixed_currency`) ;
    - jamais : une somme entre clients, un total entre vendeurs, une conversion entre termes, une part au-delà de 1, une pièce EX-99 (niveau E) ;
  - ces cellules n'entrent ni dans l'annexe E ni dans l'annexe F, ni dans les mesures de financement, l'exposition, les paires, les cycles ou les conclusions.

  (6) Montage `backlog` (lecture du volet 3, et des deux paragraphes du volet 2) :
  - corpus : documents en cache (registre des documents) des vendeurs, c'est-à-dire des groupes du modèle vers lesquels va au moins une arête commerciale d'un client nommé. Formulaires 10-K (10-KT compris), 10-Q, 8-K, S-1, 424B3, 424B4, 20-F, 40-F et leurs amendements, du 2019-01-01 à l'as_of ; pièces EX-99 écartées (furnished, niveau E). Niveau de preuve de chaque bloc comme le registre des documents (`evidence: registry`) ; noms des clients tels qu'écrits, casse comprise, et termes de carnet sans égard à la casse, comme au constat du point 2 ;
  - un paragraphe qualifie s'il nomme un client du vendeur (noms et alias du registre, termes du lexique) et un terme de carnet : RPO, remaining ou unsatisfied performance obligations, contract value, contracted revenue, total contract, aggregate value, future, minimum ou remaining lease payments, lease payments to be received, backlog. Un paragraphe de la section des facteurs de risque ne qualifie jamais ;
  - fenêtres d'un paragraphe de part et d'autre, fondues ; servies des plus anciennes aux plus récentes ; un texte distinct se lit une fois ;
  - régimes : lecture complète d'une fenêtre jamais lue (codage habituel, plus les lignes de carnet) ; lecture complémentaire d'une fenêtre déjà dans un bloc lu du même dépôt (seules s'écrivent des lignes de carnet ; sinon `duplicate_of_other_block`).

  (7) Ligne de carnet, descriptive (sans famille ni arête, aucune autre mesure), note finie par « ligne de carnet (D-0068) » :
  - `backlog_basis` : `rpo` (contrat de services), `lease` (S bailleur), `unspecified` si le texte ne le dit pas ;
  - `backlog_statement` :
    - `remaining` : reste dû par C à une date (RPO attribué, loyers restant à recevoir de C, valeur restante de ses contrats) ;
    - `contract_value` : valeur d'un contrat sur sa durée, à sa signature ou à un avenant ;
    - `total_contract_value` : valeur de tous les contrats de S avec C ;
    - `change` : hausse de la valeur d'un contrat, ou du RPO de C, sur une période ;
    - `excluded` : le RPO ou le carnet de S exclut le contrat de C ;
    - `included_no_amount` : il l'inclut, sans montant ;
  - champs de montant habituels (montant, unité, devise, qualificatif, origine) pour `remaining`, `contract_value`, `total_contract_value` et `change` ; aucun pour `excluded` et `included_no_amount` ;
  - `period_end` : date du reste ou de l'énoncé (exigée pour `remaining`, `excluded`, `included_no_amount`) ; `event_date` : signature du contrat ; `period_label` : durée telle qu'écrite ;
  - `counterparty_name` : le client tel qu'écrit, présent dans le bloc ; `instrument_key` : le contrat, une clé par contrat, la même dans toutes les lignes ;
  - doublons : une ligne par fait du vendeur, sur le premier dépôt qui l'écrit ; une reprise est une abstention `duplicate_of_other_block` ; un chiffre ou une date qui change fait une ligne nouvelle ;
  - données personnelles : aucun nom de personne physique.

  (8) Champs et registre : `backlog_basis` et `backlog_statement` (registre, lecteur, chargement, `schema.sql`) ; `bound_basis` gagne `published_contract_value` ; mesures `lessor_lease_receipts` et `contracted_backlog_share` (rang 2, §14). Les loyers à recevoir se lisent directement dans les faits non dimensionnés, comme `rpo_beyond_12m`, sans grandeur ni ancre nouvelle : une ancre ajouterait des contrôles de correspondance sans rien apporter. Contrôles du lecteur : une ligne de carnet est descriptive ; l'énoncé exige la base et réciproquement ; un montant pour les énoncés chiffrés, aucun pour les autres ; la date du point 7.

  (9) Rendus : dans la section des paires, les cellules calculées de la dépendance du carnet avec leur valeur. Section nouvelle « Carnet contracté par client (D-0068) » après le calendrier des capacités :
  - par vendeur, son RPO et ses loyers à recevoir à la dernière date ;
  - par client, la dernière cellule (part, ou intervalle [0 ; borne haute]) avec sa base et ses pièces ;
  - jamais de total. Le détail par date va dans `series.md`.

  (10) Réseau : aucun, tout est en cache. Données personnelles : aucune personne physique n'est citée.

  (11) Code avant tout traitement : règle du lendemain (occurrences des grandeurs), règle de §3.3 et cellules de trimestre (`circularity`), module `backlog` (mesures du volet 3, source du montage), champs et contrôles, rendus, tests.

  (12) Ordre et commits : règles, configuration, code et tests ; montage préparé et volume consigné avant lecture ; lecture lot par lot, sans sous-agent ; intégration (réassemblage, rendus, résultats, tests), commit, push, rapport.

  (13) Limites connues avant lecture :
  - une valeur de contrat n'est pas un carnet : elle ne donne qu'une borne haute, sous l'hypothèse du point 5 ; un contrat non publié la rend fausse, et une hausse sans base (« incremental ») n'en donne aucune ;
  - le RPO exclut les contrats d'un an au plus, la contrepartie variable et les contrats résiliables sans pénalité (ASC 606-10-50-14 à 14B) ; les loyers à recevoir excluent les loyers variables ;
  - l'échéancier des loyers à recevoir est souvent annuel : beaucoup de trimestres n'auront pas de dénominateur ;
  - les grands baux dont la valeur n'est écrite qu'en EX-99 restent sans montant ;
  - Microsoft n'attribue aucun RPO à OpenAI dans ses dépôts ; Amazon ne balise son RPO par client que depuis 2026. Aucune paire de E.3 n'a d'attribution de fin d'exercice : E.3 restera indéterminé.

  (14) Volume du montage `backlog`, consigné le 2026-10-22 avant toute lecture :
  - corpus : 30 vendeurs ; 2 558 documents dans la période, tous en cache ; 1 812 nomment un terme de carnet (pré-filtre sur les octets) ;
  - fenêtres : 103, dont 83 textes distincts (20 doublons, 9 d'entre eux déjà blocs d'un autre catalogue) ; 1 737 pièces sans fenêtre ; 3 fenêtres dans un facteur de risque ; aucune au-delà du plafond ;
  - 83 blocs, 307 790 caractères : lecture complète 33 (134 130 caractères), complémentaire 50 (173 660) ;
  - par niveau : A 20, B 18, C 29, D 6, E 10. Les dix blocs de niveau E sont des 8-K dont tous les items sont furnished (2.02, 7.01, 9.01) : ils se lisent, leurs lignes n'entrent dans aucune mesure (points 4 et 5) ;
  - par vendeur (complète / complémentaire) : Akamai 0/1, Applied Digital 2/3, Apollo 9/0, Broadcom 0/4, Backblaze 1/2, Cipher 0/10, CoreWeave 2/14, Galaxy 6/1, Hut 8 0/3, IREN 6/1, Nebius 2/3, TeraWulf 5/8 ; douze vendeurs, comme au constat ;
  - file de lecture : `work/lists/backlog.txt`, des plus anciens aux plus récents ; lecture par lots, sans sous-agent.

  (15) Amendement consigné le 2026-10-22 pendant la lecture, après 28 blocs lus et avant toute lecture de ce qu'il ajoute ; aucun calcul fait :
  - constat de lecture : un paragraphe qui chiffre un contrat ne nomme pas toujours le client (Applied Digital, 8-K du 2 juin 2025 : la valeur des baux des bâtiments 2 et 3 suit le paragraphe qui nomme CoreWeave), et les valeurs des 8-K (Item 1.01) s'écrivent sans terme de carnet (« has committed to pay »). La règle du point 6 ne les sert pas : la somme du point 5 ne compterait qu'une partie des contrats d'une paire et sa borne haute serait fausse ;
  - montage `backlog_values` (source `edge_values`) : les blocs déjà lus qui portent une arête de valeur, c'est-à-dire une arête commerciale du client vers le vendeur (engagement d'achat ou bail de capacité), montant en USD, niveau A à D, au stade `signed` ou `available`, tirée d'une ligne déposée par le vendeur lui-même. Un paragraphe qualifie s'il contient la citation d'une de ces lignes ; fenêtre d'un paragraphe de part et d'autre, dans le texte du bloc lu ; lecture complémentaire (lignes de carnet seulement, sinon `duplicate_of_other_block`) ; une fenêtre qui reprend tout son bloc reçoit en tête une ligne qui la nomme, pour avoir sa propre clé ;
  - garde du point 5 : un contrat d'une paire que les tables connaissent par une telle arête, daté au plus tard de t, sans aucune ligne de carnet (par sa clé de contrat), interdit la somme : `not_disclosed`, avec les arêtes en drapeau (`uncovered_edges`). Une valeur totale ne s'admet que si aucun contrat connu (lignes ou arêtes) n'est daté après elle et au plus tard de t. Ces contrats comptent aussi parmi les « autres contrats » qui empêchent le zéro d'une exclusion (points 4 et 5) ;
  - pièces EX-99 sans type au registre : treize blocs du montage `backlog` sont des pièces EX-99 que le registre des documents ne type pas (nom de fichier en « ex99 », type absent). Elles sont hors du corpus du point 6 : le corpus les écarte désormais par leur nom de fichier, et le montage `backlog` se prépare de nouveau ; les blocs déjà lus gardent leur clé.

  (16) Volumes après l'amendement, consignés avant la suite de la lecture :
  - montage `backlog` préparé de nouveau : 2 503 documents dans la période, 1 779 nomment un terme de carnet ; 90 fenêtres, 70 textes distincts, 70 blocs (226 388 caractères), lecture complète 31 (112 336 caractères), complémentaire 39 (114 052) ; par niveau A 20, B 18, C 20, D 6, E 6. Les treize blocs EX-99 sortent, aucun n'avait été lu ; les 28 blocs lus gardent leur clé, et aucun autre bloc ne change ;
  - montage `backlog_values` : 38 arêtes de valeur, dont 32 tirées d'une ligne du vendeur, dans 24 blocs lus ; 25 fenêtres, 25 blocs (38 834 caractères), tous en lecture complémentaire, dont 14 avec la ligne de tête ; par niveau A 3, B 8, C 14 ; par vendeur : CoreWeave 9, Nebius 3, Applied Digital 2, Hut 8 2, Riot 2, Amazon 2, Microsoft 1, IREN 1, SpaceX 1, Backblaze 1, Akamai 1 ;
  - files : `work/lists/backlog.txt` (70 blocs, dont 28 lus) puis `work/lists/backlog_values.txt` (25 blocs).

  (17) Résultats, réassemblage du 2026-10-22 (831 s, mémo non repris), comparés aux tables d'avant :
  - lecture : 95 blocs, sans sous-agent (70 du montage `backlog`, 25 de `backlog_values`) ; 101 lignes, 34 observations et 67 abstentions. 28 lignes de carnet, toutes valides : 15 valeurs de contrat (RPO), 5 valeurs de bail, 5 hausses, 1 exclusion, 2 inclusions sans montant ; niveaux A 5, B 12, C 11. 6 lignes du codage habituel dans les fenêtres jamais lues ;
  - tables : observations 29 933 → 30 034 ; liens 11 124 → 11 132 (6 arêtes commerciales, 2 relations `same_measure`) ; exclusions 32 832 → 32 835 (les 3 fenêtres de facteurs de risque) ; mesures 179 464 → 182 649 ; documents, faits, entités et nombre de contrôles inchangés. Parmi les cellules communes, seules changent : `documented_backlog_dependency` 822 (statut ou motif), `annex_e_outcome` 198 (motif de E.3), `rpo_total` 50 (calculé) ; 6 contrôles `c5_bilateral` ne changent que leur compte d'arêtes ;
  - volet 1 : `rpo_total` calculé 540 → 590 cellules, toutes marquées `derived_from: timing_axis_next_day` : Amazon 22 trimestres (2021-03-31 à 2026-06-30), Applied Digital 2, Micron 1, dans les deux vues ;
  - volet 2 : 3 940 cellules de `documented_backlog_dependency` (938 de fin d'exercice, 3 002 de fin de trimestre). Quatre calculées, toutes de fin de trimestre, donc hors E.3 : Amazon → OpenAI au 2026-03-31, 10,4 % (RPO balisé du membre OpenAI, 38,0 Md$, sur 364 Md$), et CoreWeave → OpenAI au 2025-03-31, 0 % (le RPO exclut le Commercial Agreement), chacune dans les deux vues. Les autres : `concept_unresolved` 2 164, `not_disclosed` 1 161, `anonymous` 337, `precondition_not_met` 274. E.3 : 225 issues, toutes indéterminées comme prévu (point 13), avec un motif plus juste qu'avant (`anonymous` 27, `concept_unresolved` 126, `not_disclosed` 33, `precondition_not_met` 39) ; E.7 inchangé ;
  - volet 3 : `lessor_lease_receipts` 152 cellules pour 10 groupes (Dell seul publie les deux concepts) ; `contracted_backlog_share` 31 cellules, 12 paires, 8 vendeurs : 2 calculées, 25 bornées, 4 non déterminées. Dernière cellule de chaque paire : Amazon → OpenAI [0 ; 27,8 %] au 2026-06-30 (10,4 % exact au 2026-03-31) ; CoreWeave → OpenAI [0 ; 21,6 %] et CoreWeave → Meta [0 ; 33,9 %] au 2026-06-30 ; Applied Digital → CoreWeave [0 ; 30,8 %] des loyers au 2026-08-31 ; Backblaze → CoreWeave [0 ; 84,6 %] ; Nebius → Microsoft [0 ; 81,6 %] et Nebius → Meta [0 ; 13,6 %] au 2025-12-31 ; Riot → AMD [0 ; 49,1 %] des loyers ; IREN → NVIDIA [0 ; 66,7 %] ; IREN → Microsoft plafonnée à 100 % ; Microsoft → OpenAI et Amazon → Anthropic non déterminées (hausses sans base publiée). Sans aucune cellule : Akamai → Anthropic (contrat de septembre 2026, après le dernier trimestre publié) et Hut 8 → Fluidstack (loyers à recevoir non publiés).

  (18) Limites constatées :
  - une borne haute n'est qu'une borne : elle tient sous l'hypothèse du point 5 et compte la valeur entière d'un contrat (« up to »), sans rien retrancher de ce qui a déjà été facturé ; la borne basse reste zéro, même quand le vendeur dit que son RPO inclut le contrat (CoreWeave au 2025-06-30, Backblaze au 2026-06-30 : drapeau `included_no_amount`) ;
  - IREN publie des loyers à recevoir (11,4 Md$ au 2026-06-30) au-dessus de son RPO (5,1 Md$) : ses contrats avec Microsoft et NVIDIA, que leurs textes disent de services, sont codés `rpo`, et la borne de Microsoft, plafonnée, ne dit rien. Si IREN les comptait en baux, le terme `lease` serait le bon ; aucun texte lu ne le dit ;
  - deux valeurs d'un même contrat : la dernière par date de contrat l'emporte (Backblaze : 335 M$ du 8-K, daté de sa pièce, plutôt que 335,1 M$ du 10-Q, daté de la signature) ;
  - les valeurs écrites seulement dans des pièces EX-99 (TeraWulf, Cipher, Galaxy, les communiqués de Hut 8) restent hors mesure ; le locataire du bail de Riot d'août 2026 n'est pas nommé dans la fenêtre lue, et le contrat de SpaceX avec Anthropic n'a qu'un tarif mensuel : ces paires n'ont aucune ligne de carnet ;
  - Amazon est le seul vendeur qui balise son RPO par client ; aucune paire de E.3 n'a d'attribution de fin d'exercice.
- **D-0069 — Audit du dépôt du 22 octobre 2026 : chaque constat revérifié, six défauts de calcul corrigés, garde-fous des rendus calculés. Règles fixées avant tout recalcul.**
  (1) Origine : un audit du dépôt au commit eadc0f4, remis par l'utilisateur le 2026-10-22 (« Voilà un audit que j'ai fait faire sur le repo à prendre en compte »). Chaque constat est revérifié sur le code et sur les tables versionnées avant toute modification. Les verdicts et les règles corrigées ci-dessous sont fixés avant le réassemblage, et les résultats vont au point 12. Rien n'est relu ni retéléchargé, et aucune requête réseau n'est faite.

  (2) F1 (annexe F) — confirmé.
  - Défaut : `fsignals.py` ne comparait capex et CFO que si `capex_to_cfo` était `computed`, ce qui exige un CFO strictement positif. Un trimestre à CFO négatif sortait donc `not_determinable` (`denominator_nonpositive`), et le trimestre suivant perdait son prédécesseur. Or l'annexe F pose la condition sur les termes (`capex_cash > cfo`), pas sur le ratio.
  - Règle : la condition se lit sur les deux termes de `capex_to_cfo` (`term = without`) dès qu'ils sont connus, quels que soient le signe du CFO et le statut du ratio. Sans l'un d'eux, la cellule reste `not_determinable` avec le motif du ratio, comme avant.
  - Effet attendu, recalculé sur les tables en vue `as_known` : 121 événements au lieu de 43, dans 13 groupes. Riot passe de 1 à 19, TeraWulf de 3 à 15, Cipher de 0 à 11, Applied Digital de 6 à 13, Backblaze de 1 à 8, Supermicro de 0 à 7, Core Scientific, CoreWeave et Intel à 8, Galaxy de 0 à 3 ; Amazon, Dell et IREN gagnent un événement.

  (3) Variation du nombre moyen dilué d'actions (`eq_diluted_share_count_change`, §4.6) — confirmé, avec un second défaut trouvé pendant la vérification.
  - Premier défaut : un trimestre sans fait direct se calculait comme un flux (exercice moins neuf mois), ce qui n'a pas de sens pour une moyenne pondérée. Cela touche 67 cellules de la vue `revised` et 71 de la vue `as_known`. 52 d'entre elles dépassent 50 %, dont Intel à +638,5 % dans `synthesis.md`. 28 autres sortent `denominator_nonpositive`, motif impossible pour un nombre d'actions.
  - Second défaut : en vue `revised`, un fractionnement mêle deux bases. Le trimestre vient du dépôt de l'année suivante, retraité ; son comparatif vient d'un dépôt antérieur au fractionnement, non retraité. Exemples : Amazon en 2021-2022, vers +1 900 % ; Broadcom, NVIDIA et Supermicro, de +306 % à +1 024 %.
  - Règle : la variation compare deux faits directs de trois mois, le trimestre et le même trimestre de l'exercice précédent, pris dans un même dépôt. C'est le dernier dépôt connu à la date de coupure qui publie les deux, car un dépôt présente un trimestre et son comparatif sur la même base. Jamais de différence de cumuls. Sans fait direct pour l'un des deux trimestres, le motif est `not_disclosed`. Si les deux faits directs existent mais qu'aucun dépôt ne les publie ensemble, le motif est `recast_boundary`.

  (4) Dette du levier (`lev_debt_and_leases_to_operating_income_plus_da`, `term = debt`) — confirmé et élargi.
  - Défaut : les emprunts à court terme (`ShortTermBorrowings`, `CommercialPaper`) s'ajoutaient à toute dette courante. Or `DebtCurrent` les contient déjà (Intel, NVIDIA : 11 cellules), de même que `DebtLongtermAndShorttermCombinedAmount` (Broadcom : 7 cellules, trouvées pendant la vérification).
  - Règle : ils ne s'ajoutent qu'à une dette qui les exclut par définition : `LongTermDebtCurrent`, ou `CurrentPortionOfLongtermBorrowings` en IFRS, pour la part courante, et `LongTermDebt` pour le total. Ils ne s'ajoutent jamais à `DebtCurrent`, `DebtLongtermAndShorttermCombinedAmount`, `CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings` ni `Borrowings`.
  - Effet : Intel au 2024-06-30 passe de 56 229 à 53 029 M$, et son levier de 6,98 à 6,58.

  (5) Statut « financé », condition (a) de §3.2 — confirmé.
  - Défaut : la liste des fins de détention rangeait (date, clé d'instrument), mais la boucle la lisait comme (date, date de connaissance), avec un test toujours vrai. La clôture de n'importe quel instrument fermait donc toutes les détentions de la paire, et comptait avant d'être publique.
  - Second défaut : seules les clôtures du sens fournisseur → client étaient lues. Or une clôture suit le sens de la trésorerie : la cession de la part d'Intel dans IMFT à Micron va de Micron à Intel.
  - Relevé : 509 détentions (a) dans 80 paires. 29 clôtures vont du fournisseur S au client C, et 38 vont de C à S, jamais lues. L'instrument est confondu dans 4 paires : Amazon → Anthropic, ASML → Carl Zeiss SMT, Backblaze → AFCO et Intel → Micron.
  - Troisième constat, fait en vérifiant la règle : 12 instruments ont leur clôture enregistrée hors de la paire. C'est le cas de la cession à un tiers (Coinsquare, payée par Mogo), de l'acheteur non résolu (McAfee) et de l'arête d'Intel vers Intel pour sa part dans ASML.
  - Règle : une détention (a) datée d est close à la fin du trimestre q par une cession, une conversion, un remboursement ou une résiliation qui remplit quatre conditions : portant la même clé d'instrument, sur n'importe quelle arête, dans la paire ou non ; datée entre d et la fin de q ; connue à la date de coupure de q ; et à un stade accompli (ni `intent_non_binding`, ni `signed`, ni `available`).
  - Une détention sans clé se ferme par une clôture de la paire, dans l'un ou l'autre sens, du même type d'arête. Il y en a 191 sur 509, et toutes sont dans des paires sans clôture, sauf Apollo → AP Grange : ses soldes trimestriels et son remboursement anticipé portent sur la même dette ABS.

  (6) Sauts d'un facteur 100 (§7.3) — confirmé en partie.
  - Défaut : §7.3 rend un saut `conflicting` tant que `num` des Notes Data Sets ne l'a pas confirmé. Le code ne cherchait aucune confirmation et ne marquait que les faits d'instance, si bien que le fait `companyfacts` du même dépôt revenait dans les sommes.
  - Relevé : 1 377 faits sont marqués, tous par cette règle. 1 125 ont ce doublon, égal à la tolérance d'arrondi près : 1 120 exactement, 5 à l'arrondi près (une même valeur présentée en millions et en milliers). Les 225 faits qui alimentent une mesure reviennent tous ainsi. Les 252 sans doublon n'alimentent aucune mesure.
  - Règle : `companyfacts` est l'extraction par la SEC du même dépôt, le rôle que §7.3 donne à `num`, que le pipeline ne conserve pas pour ces dépôts. Un saut est confirmé, et n'est pas `conflicting`, quand le fait `companyfacts` du même dépôt lui est égal à la tolérance d'arrondi de leurs deux précisions près : même concept, mêmes bornes de période, même unité, sans dimension. Un saut non confirmé reste `conflicting`, et son doublon `companyfacts` éventuel aussi, pour que le fait reste hors des sommes quelle que soit sa source.
  - Non retenu : ne garder qu'un saut qui s'inverse à la période suivante, comme le propose l'audit. Ce critère changerait la règle de détection de §7.3, et une fois la confirmation faite il ne toucherait plus aucun fait d'une mesure.

  (7) Délai du rapport annuel (E.0) — confirmé.
  - Défaut : `deadline_fn` appliquait 60, 75 ou 90 jours selon la catégorie du déposant. Or E.0 évalue chaque exercice « à la date limite de dépôt de son rapport annuel (10-K, 20-F ou 40-F) », et un 20-F dispose de quatre mois.
  - Règle : la date limite suit le formulaire du rapport annuel original de l'exercice, lu dans l'inventaire des dépôts ; pour un exercice sans rapport, c'est le dernier formulaire annuel antérieur. Pour un 20-F, c'est la fin d'exercice plus quatre mois ; pour un 10-K, la catégorie, comme avant.
  - Concernés : TSMC, ASML et Nebius, ainsi qu'IREN jusqu'à l'exercice clos le 2024-06-30.

  (8) Garde-fous des rendus, calculés au lieu d'être écrits :
  - Règle d'arrêt (§11.4) : la ligne « Arrêt » de `synthesis.md` et la section de `delta.md` se déduisent du journal et des contrôles.
    - Refus durable de la SEC : la dernière requête du journal est un refus 403, malgré les pauses.
    - Échec général des contrôles : on retient les contrôles non provisoires (`tolerance_basis = declared`) de la vue `as_known`. Une période est en échec quand ses `mismatch` dépassent ses `ok`. L'échec est général quand plus de la moitié des groupes ont plus de la moitié de leurs périodes testées en échec : c'est la lecture retenue de « la plupart des groupes et des périodes ».
  - `delta.md` devient un différentiel. L'assemblage note le commit dont il remplace les tables, et le rendu compare les tables courantes à celles de ce commit. Il liste les événements de l'annexe F apparus et disparus, les exclusions nouvelles par motif, les dépôts nouveaux, les valeurs changées pour des périodes déjà publiées, les arêtes nouvelles, les contrôles qui ont basculé et les décisions nouvelles. Les lignes écrites en dur (« premier passage », les 13 lignes corrigées de D-0020) disparaissent.
  - E.7 : la ligne de tête dit aussi la part d'issues indéterminées de E.2 seule.
  - « Recherche complète » (E.0) : la note précise qu'elle porte sur les blocs du catalogue (notes, items de 8-K, pièces annexées), non sur le rapport de gestion ni sur les autres sections. Une pièce L5 qui ne se trouverait que là échapperait donc à la recherche.

  (9) Hygiène :
  - Les huit tables s'exportent en Parquet compressé ZSTD, sans changement de contenu. `facts.parquet` pèse 95,4 Mio pour une limite GitHub de 100 Mio, et doit descendre vers 48 Mio.
  - `assemble.insert` compte les doublons de clé primaire par table, identiques ou en collision, dans les statistiques d'assemblage, et la note publie ce compte. En cas de collision, la dernière ligne est toujours gardée.
  - `requirements.txt` épingle les versions de cet environnement. Un `README.md` court donne les prérequis, l'ordre des commandes et ce qui fonctionne sans `db/`.
  - `user_brief_2.md` reçoit un erratum : depuis D-0039, NVIDIA et CoreWeave ne sont plus reliés par un document.
  - Code mort retiré : `events.fragility_events` (l'ancienne règle F1), `events.observed_signal`, ainsi que `graph.edges_from_observations` et ses deux auxiliaires.

  (10) Laissé à la décision de l'utilisateur, sans changement ici :
  - L'audit indépendant de l'annexe C, par un tiers, en commençant par les dix « dépendances documentées » et les 71 issues « non étayé ». Les trois pièces de lien que l'audit juge fragiles (NVIDIA → OpenAI, L5 ; AMD → Meta, L2 ; NVIDIA → IREN, L1 et L3) relèvent de ce jugement : le lecteur qui les a classées ne les reclasse pas.
  - Un seuil de matérialité pour F11 à F16, à fixer avant tout recalcul.
  - La seconde moitié de C6, la cause des retraitements de C4, les membres qui se recoupent dans C12 et la trésorerie restreinte de C3.
  - La forme de `decisions.md`, et une page courte à jour.
  - Restent en l'état :
    - le verrou de session, qui sert la session planifiée de §11.5, laquelle n'existe pas ;
    - `keep_zip`, faux par défaut à cause du disque de l'environnement ; le README dit comment garder les archives ;
    - `PYTHONHASHSEED` ;
    - les plages d'octets des citations dans le HTML échappé ;
    - les nombres des notes du lecteur.

  (11) Tests de régression, un par défaut :
  - F1 avec un CFO négatif deux trimestres de suite ;
  - actions diluées sans fait direct au quatrième trimestre, et à travers un fractionnement ;
  - `DebtCurrent` accompagné de `CommercialPaper` ;
  - paire à deux instruments dont un seul est cédé, avec une clôture dans le sens client → fournisseur, une clôture connue après la coupure et une vente à un tiers ;
  - saut ×100 confirmé par son doublon `companyfacts`, et saut non confirmé ;
  - date limite d'un 20-F.

  (12) Résultats, après réassemblage (1 055 s), comparés aux tables d'eadc0f4. Un second assemblage, qui n'ajoute que le relevé complet des collisions, redonne `measures` à l'octet près.
  - F1 : 121 événements au lieu de 43, groupe par groupe comme prévu au point 2.
  - Actions diluées :
    - vue `revised` : 389 cellules calculées au lieu de 456, dont 41 au-delà de 50 % au lieu de 107 ; plus aucune `denominator_nonpositive` (il y en avait 28) ;
    - les deux vues donnent désormais les mêmes valeurs ;
    - Intel au 2025-12-27 passe de +638,5 % à « non publié » : le 10-K ne donne pas le quatrième trimestre ;
    - les fractionnements ne faussent plus rien : Amazon en 2021-2022 donne de −0,8 % à +1,0 % ; Broadcom, NVIDIA et Supermicro de −0,7 % à +12,4 % ;
    - les 41 variations restantes viennent d'émetteurs qui ont fortement émis des actions : Riot 7, TeraWulf 6, Blue Owl 5, Core Scientific 4, puis Backblaze, Apollo, Applied Digital, CoreWeave, Hut 8, IREN, Galaxy et SpaceX. Elles vont de −65,8 % à +317,1 %.
  - Levier : 12 cellules changent, toutes chez Intel et Broadcom, là où les emprunts à court terme ne sont pas nuls ; le papier commercial de NVIDIA est nul. Intel au 2024-06-29 passe de 6,98 à 6,58, Broadcom au 2025-02-02 de 3,99 à 3,77.
  - Statut « financé » : 313 cellules changent dans 12 paires. En vue `as_known`, politique `exposure_outstanding` :
    - ASML → Carl Zeiss SMT redevient active au 2024-09-30 (c'est le cas de l'audit), et Backblaze → AFCO sur quatre trimestres ;
    - les clôtures hors paire, désormais lues, closent des détentions restées actives :
      - Intel → ASML, Unisoc et McAfee passent à `lapsed` (27, 27 et 17 trimestres), et Intel → Cloudera à `unknown` (23 trimestres) ;
      - Riot → Coinsquare et Mogo passent à `lapsed` (10 et 7 trimestres) ;
      - SK hynix → ses deux fonds coréens passent à `lapsed` (4 trimestres chacun) ;
    - Applied Digital → AI Bridge Funding devient `never` (10 trimestres) et Backblaze → City National Bank `lapsed` (4 trimestres). Ces deux paires ne tenaient qu'à des charges d'intérêts du fournisseur, enregistrées du fournisseur vers son prêteur : elles s'éteignent au remboursement ou à la résiliation du prêt. La question de leur sens reste à l'audit de l'annexe C ;
    - paires à financement établi au moins un trimestre : 82 au lieu de 86.
  - E.7 : le résultat ne change pas (« discrimination possible »).
    - 162 issues au lieu de 170, dont 91 indéterminées au lieu de 96, soit 56,2 % au lieu de 56,5 %.
    - E.1 compte 81 issues : 68 « non étayé » au lieu de 71, 3 « étayé », 10 indéterminées. E.2 compte 81 issues, toutes indéterminées.
    - Les conclusions de paire ne changent pas : 10 dépendances documentées, 26 relations commerciales doublées d'un financement, 44 achats réciproques seuls et 170 causalités non établies.
  - Sauts ×100 : 252 conflits au lieu de 1 377, aucun dans une mesure ; les exclusions `conflicting` diminuent de 1 125.
    - Une seule valeur change : le capex de Core Scientific au deuxième trimestre 2023, en vue `as_known`, passe de 261 000 à 235 000 $. Le fait précis (1 774 000 $ sur six mois) était marqué, et l'arrondi de 1,8 M$ servait à sa place.
    - 335 contrôles basculent, presque tous de `not_testable` vers `ok` (C1 63, C2 234, C10 16) ou vers `mismatch` (C1 1, C2 10, C10 2). C3 compte 6 `mismatch` → `ok`, C2 1 `ok` → `mismatch` et 2 `ok` → `not_testable`.
  - Date limite des 20-F : les cellules de l'annexe E de TSMC, d'ASML, de Nebius et d'IREN (exercices jusqu'à 2024) sont redatées, car l'`as_of` fait partie de la clé : 48 apparaissent, 76 disparaissent. Il en va de même pour `documented_revenue_dependency` (86), `investor_customer_revenue_share` (8), `noncash_revenue_from_investees` (37 apparues, 84 disparues) et `documented_backlog_dependency` (84 apparues, 536 disparues, dont les fins de trimestre des paires qui ne sont plus financées).
  - Doublons de clé primaire :
    - `measures` : 668 lignes écartées, dont 229 clés en collision, toutes de `lease_not_commenced_bridge`. Deux producteurs écrivent la même cellule indéterminée avec des motifs différents (`annual_measures` et `leases_not_commenced`), et la ligne gardée est celle de `leases_not_commenced`, la plus précise. Aucune valeur calculée n'est perdue : c'est vérifié, et le remplacement de rang 2 s'applique aux deux copies.
    - `entities` : 1, l'appartenance de VMware. `exclusions` : 2 doublons identiques.
  - Règle d'arrêt : aucun refus 403 au journal. Apollo est le seul groupe dont plus de la moitié des périodes testées sont en échec, avec 22 périodes en échec sur 904 au total ; il n'y a donc pas d'arrêt.
  - Taille : les huit tables passent de 123,3 à 62,6 Mo, dont `facts.parquet` de 100,0 à 50,7 Mo.
  - Tests : 321, tous réussis.
- **D-0070 — Ajout de groupes : Cerebras Systems (CBRS) ; Fluidstack, groupe économique non déposant (§10.4). Règles fixées avant tout tirage.**
  (1) Décision de l'utilisateur, le 2026-10-22 : « On verra plus tard, pour l'instant ajoute Cerebras et Fluidstack au modèle ». Elle suit le rapport de D-0069 (commit 9747107) ; les décisions que D-0069 (point 10) laisse à l'utilisateur restent en attente. Lecture séquentielle par l'exécutant, sans sous-agent.

  (2) Statut lu avant tout tirage, sans aucune requête, dans `company_tickers.json` du 2026-10-07 et dans la liste des noms d'EDGAR du 2026-10-09, déjà en cache :
  - Cerebras : CBRS résout le CIK 2021728 (Cerebras Systems Inc.). Cerebras entre comme groupe complet (`groups`, `group_entry` au 2026-10-22).
    - La découverte (§14) connaît déjà ses dépôts : le S-1 du 2024-09-30 (0001628280-24-041596, première tentative), le S-1 du 2026-04-17 (0001628280-26-025762), le S-1/A du 2026-05-04 (0001628280-26-029503) et deux 10-Q, déposés le 2026-06-24 (0001628280-26-044981) et le 2026-08-12 (0001628280-26-056357).
    - La phase 0 lit tous ses dépôts. La prise d'effet, le 424B4, le premier 10-Q et les exercices présentés par le document d'enregistrement fixent `reporting_start` (Reg S-X 3-01 et 3-02), comme pour CoreWeave et SpaceX. Cerebras reçoit `history_left_censored` si son premier dépôt suit le début de lecture.
    - L'exécution garde l'as_of du 2026-10-07 (D-0048, point 2).
  - Fluidstack n'a aucune entrée dans `company_tickers.json`, donc aucun titre coté à l'as_of. La liste des noms d'EDGAR donne FLUIDSTACK LTD (CIK 2104151), un CIK de 2026 comme celui de NSCALE Ltd (2110365).
    - Fluidstack entre comme groupe économique non déposant `NF:FLUIDSTACK` (§10.4), sur le modèle de Lambda et de Nscale (D-0054) : Fluidstack Ltd et ses filiales consolidées. Ce n'est pas un laboratoire.
    - Le statut se vérifie sur les submissions de FLUIDSTACK LTD et des CIK que la recherche fait apparaître. Un document d'enregistrement public déposé avant l'as_of entre dans la piste comme texte propre du groupe et se lit en entier (D-0054, point 13). Un rapport périodique déposé avant l'as_of fait revoir la règle ici, avant toute lecture.
    - Comme pour un laboratoire, la recherche est alors complète du côté de Fluidstack, pour une paire (E.0) comme pour un cycle (bloc `paths`).
  - La liste des noms donne aussi une trentaine de véhicules de fonds qui portent le nom de l'une des deux sociétés : séries « Hiive Cerebras » et « HII Cerebras », séries de CGF2021 LLC (dont « Thesiger Fluidstack Fund » 1 et 2), « Fluidstack SPV Jan 2026 II » de SC2025 AI LLC, « ZDN VC LLC - Series Fluidstack », « 7GC & Co. Opportunity Partners, Fluidstack LLC », et d'autres. Ce sont des actionnaires, pas des entités des groupes : ils n'y entrent pas. Leurs Form D ne se lisent pas, car le bloc `form_d` ne prend ni Cerebras ni Fluidstack pour sous-jacent (D-0054, point 8).

  (3) Cerebras : mêmes phases et mêmes règles de lecture que les groupes présents (D-0043, D-0048, D-0052 à D-0057).
  - Inventaire, archives XBRL, catalogue des notes, des items et des pièces, puis lecture complète du texte. Les clôtures se lisent en phase 0 sur `period_end`.
  - Introduction récente : les états annuels et l'Item 404 se lisent dans le 424B4 (phase 2), comme pour SpaceX et CoreWeave.
  - Les pièces d'un document d'enregistrement ne sont pas au catalogue d'un groupe ; les en-têtes d'EX-10 des S-1 que la découverte a déjà lus restent tels quels. Le catalogue prend les pièces des 8-K, comme pour tout groupe.

  (4) Ruptures d'historique : règle de D-0052, point 5, vérifiée en phase 0 sur la liste des dépôts et, en cas de doute, par un extrait cité. Aucune n'est attendue : le CIK porte le même déclarant depuis 2024.

  (5) Filiales : la règle de D-0050 (points 3 à 7) s'applique aux véhicules des deux groupes nommés dans les lignes, y compris dans celles des autres groupes et dans les positions des BDC. Elle s'applique à l'intégration, après la lecture.

  (6) Découverte d'origine (D-0043, point 6) :
  - les lignes déjà lues pour Cerebras vont à son groupe. Ce sont celles de la découverte (notes du 10-Q du 2026-08-12, en-têtes d'EX-10 du S-1 de 2024 et des S-1 et S-1/A de 2026) et celles du montage des laboratoires (D-0059 : paragraphes du S-1, du S-1/A et du 10-Q). Les en-têtes de pièces de même clé de contenu ne se relisent pas ;
  - ses 19 unités encore en file en sortent (`out_of_scope`), car ses dépôts se lisent par le catalogue du groupe ;
  - côté client, la recherche reste incomplète pour un fournisseur que le lexique de la découverte ne nommait pas (`search_incomplete`). Le lexique, le classement, la file et l'état de lecture de la découverte d'origine ne changent pas (D-0036).

  (7) Fluidstack, niveau 1 : entités réunies par extraits (§10.2, D-0021), comme pour SoftBank (D-0044, points 3 et 7).
  - La tête du groupe (Fluidstack Ltd) et ses filiales n'y entrent que sur un extrait qui l'affirme, avec sa date (règles A et B de D-0044, point 7).
  - Les lignes déjà lues qui nomment ces entités vont au groupe par ces extraits, à l'intégration. Il y en a chez TeraWulf (34), Cipher (24), Hut 8 (7) et IREN (2), et chez deux déposants de la découverte (Soluna Holdings, Willow Lane Acquisition Corp.).
  - D'ici là, les entités déjà confirmées (Fluidstack Ltd., Fluidstack USA I à IV Inc., Fluidstack CS I Inc.) restent des contreparties propres.

  (8) Fluidstack, niveau 2 : la piste des non-déposants (D-0044, points 4 et 5 ; D-0058, point 24) reçoit son terme, sans autre changement.
  - Lexique de la piste : « Fluidstack », en mot entier, insensible à la casse (il prend aussi « FluidStack »), cible `NF:FLUIDSTACK`. Jamais « FS », ni « FS AB LLC » ou « FS CS I LLC » : ces sigles n'entrent au groupe que par extrait (point 7).
  - Sources : les 47 archives des Notes Data Sets, retirées, scannées sous le lexique d'ensemble enrichi, puis effacées ; recherche plein texte du seul terme nouveau sur les formulaires racines des EX-10 (`search new`) ; vérification de chaque pièce sous le lexique d'ensemble. Pas de Form D.
  - Candidats, classement et règle de lecture (R1, R2) : ceux de D-0044, point 5. Comme au point 24 de D-0058 :
    - l'état des unités d'avant l'enrichissement est gardé une fois (`snapshot`) ; une unité connue garde sa règle, son rang et son état ;
    - les unités que nul terme antérieur ne faisait naître forment une file à part, R1 puis R2, plafonnée à 300 ;
    - une unité tirée d'un dépôt propre du groupe ne se lit pas (état `own_group`).
  - Co-mentions : celles du lexique d'ensemble (groupes du lexique de la découverte, laboratoires, Stargate, non-déposants). Cerebras n'y figure pas (point 6).
  - Au-delà du plafond, la lecture s'arrête à la 300e unité, et le rendement est présenté avant d'aller plus loin.

  (9) Les lexiques déjà fixés ne changent pas : unités 6-K de D-0048 (point 9) et noms qualifiants de D-0057 (point 3), termes des montages, lexique de la découverte d'origine.

  (10) Ordre et commits :
  - la décision ;
  - la configuration, la phase 0 et l'univers attendu ;
  - l'index, les archives XBRL et les pièces (phases 0, 1 et 2, réseau en série) ;
  - le catalogue et les listes de lecture, avec leur volume consigné ici avant toute lecture ;
  - la piste des non-déposants (archives, recherche plein texte, pièces, statut de FLUIDSTACK LTD, candidats, unités retenues), avec son volume consigné ici avant toute lecture ;
  - la lecture de Cerebras, puis celle des unités de Fluidstack, un commit par partie ;
  - l'intégration : entités et filiales par extrait, noms au rendu, premier réassemblage, extraction refaite des BDC Data Sets (D-0043, point 14), second réassemblage, rendus, résultats ici, tests, commit, push, rapport.

  (11) Phases 0 à 2 et catalogue, avant toute lecture (2026-10-22) :
  - CIK confirmé par `company_tickers.json` : 2021728 (Cerebras Systems Inc., Nasdaq, CBRS). Exercice clos le 31 décembre ; déclarant non accéléré et émetteur émergent.
  - Historique (point 4) : aucune rupture, ni 8-K12 ni dénomination antérieure.
    - Le premier dépôt est un projet confidentiel (DRS) du 2024-06-17, postérieur au début de lecture : Cerebras reçoit `history_left_censored`.
    - Première tentative : DRS et DRS/A (juin à août 2024), puis S-1 du 2024-09-30, retiré le 2025-10-03 (RW).
    - Seconde tentative : DRS du 2025-12-22, DRS/A du 2026-03-31, S-1 du 2026-04-17, S-1/A des 2026-05-04 et 2026-05-11, prise d'effet le 2026-05-13 (EFFECT 9999999995-26-001616), 424B4 du 2026-05-14 (0001628280-26-035214) et 8-K de clôture du 2026-05-15 (items 5.03, 8.01 et 9.01).
  - `reporting_start` :
    - trimestres à partir du 2026-01-01 : le premier 10-Q porte sur le trimestre clos le 2026-03-31 et a été déposé le 2026-06-24 ;
    - exercices 2024 et 2025, présentés par le 424B4 (émetteur émergent, Reg S-X 3-02). Chacun est audité par son propre cabinet : le rapport sur 2024 et celui sur 2025 sont distincts.
  - Inventaire : 125 dépôts.
    - 2 rapports périodiques (10-Q des trimestres clos les 2026-03-31 et 2026-06-30), 1 8-K de la tranche (item 8.01), 2 8-K de résultats (item 2.02, hors tranche), 1 424B4, aucune circulaire.
    - Le reste : formulaires 3, 4 et 144, déclarations 13D et 13G, S-8.
  - Univers attendu : 716 cellules, dont 620 `not_applicable` ; 24 368 au total.
  - Réseau : 27 requêtes, 5 par seconde au plus, aucun échec.
    - Index : 2 225 dépôts, 16 requêtes.
    - Archives XBRL : 785 dépôts lus, 9 requêtes ; les 7 échecs sont ceux déjà connus (amendements sans instance).
    - Pièces : 2 324 documents, 2 requêtes (le 8-K de clôture et le 424B4, 8,5 Mo).
  - Catalogue : aucune clé déjà lue ne change.
    - Catalogue principal : 4 355 → 4 359 blocs (Item 404 du 424B4, Item 4 des deux 10-Q, item 8.01 du 8-K de clôture).
    - Le 424B4 n'a pas de note de parties liées distincte : G42 et MBZUAI y sont des clients « related parties with respect to each other », dans la note de concentration. Les instances des 10-Q n'ont pas non plus de bloc de parties liées.
    - Bloc `text` : 13 blocs (notes d'investissements, de dette, de baux, d'engagements, de revenus, et estimations).
  - Amendement avant lecture (point 6) : trois notes du 10-Q du 2026-08-12 (dette, autres produits, revenus) ont déjà été lues en entier par la découverte, depuis le même élément de bloc de texte. Les textes sont identiques à un rapport de similarité de 0,988 à 0,999. Ces notes ne se relisent pas, et leurs lignes vont au groupe.
    - Règle : un bloc du catalogue d'un groupe ajouté dont la note (même dépôt, même élément) a déjà été lue par la découverte ne se relit pas.
  - À lire : 14 blocs, 45 933 caractères, liste `grp_cbrs`. Ce sont l'Item 4 des deux 10-Q, l'item 8.01 du 8-K de clôture et l'Item 404 du 424B4, puis 10 notes : 4 du 10-Q du 2026-08-12 et 6 de celui du 2026-06-24.
  - Découverte d'origine (point 6) : 59 blocs déjà lus, 13 par la découverte et 46 par le montage des laboratoires. Les 19 unités encore en file en sortent au réassemblage.

  (12) Localisation des citations, amendement pendant la lecture (2026-10-22) :
  - L'Item 404 du 424B4 donne les achats des actionnaires de plus de 5 % en lignes de tableau, le libellé suivi de points de conduite (« Entities affiliated with Fidelity(4) ...... | 19,319,724 | $699,999,968 »). Le motif de localisation (`textnorm._word_pattern`) faisait un groupe par signe : sur une suite de 68 points, le retour arrière explosait et le dépôt des lignes du bloc ne finissait pas.
  - Règle : une suite d'au moins cinq fois le même signe de ponctuation se cherche d'un seul groupe ; les autres mots gardent leur motif.
  - Vérifié avant tout dépôt : le motif est identique pour les 25 741 citations déjà lues. Huit portent des suites de « _ », caractère de mot que la classe de ponctuation ne reconnaît pas : elles gardent leur motif. Test : `tests/test_d0070.py`.
  - Les citations restent mot pour mot, points compris : l'audit (annexe C) veut une citation qui nomme la contrepartie et le montant, et une ligne de tableau ne relie les deux que par ses points.

  (13) Piste des non-déposants pour Fluidstack, avant toute lecture (2026-10-22) :
  - Archives : les 47 archives des Notes Data Sets, retirées sous le lexique d'ensemble lx-71f9d8460b25, scannées puis effacées. 47 requêtes, 18,56 Go, toutes réussies, en 45 minutes. Hors des groupes, deux lignes de notes nomment Fluidstack, toutes deux chez Boost Run Inc. (CIK 2090646) : la note des événements postérieurs de deux dépôts de janvier et février 2026 (exercice clos le 30 septembre 2025).
  - Recherche plein texte du seul terme nouveau sur les formulaires racines des EX-10 : 1 requête, 4 pièces, toutes de TeraWulf et de Cipher, groupes déjà présents. La vérification les écarte, sans requête.
  - Statut (point 2) : FLUIDSTACK LTD (CIK 2104151, Royaume-Uni) n'a déposé que trois Form D (2026-01-23, D/A du 2026-05-12, 2026-06-30). Ni document d'enregistrement, ni rapport périodique, ni titre coté : Fluidstack reste non déposant et n'a pas d'unités de dépôts propres (D-0054, point 13), comme Lambda. 1 requête (submissions). La recherche ne fait apparaître aucun autre CIK d'une entité de Fluidstack ; les véhicules de fonds restent hors du groupe (point 2).
  - Candidats et file (point 8) : 4 075 unités, contre 4 073 avant. Les 2 unités nouvelles sont celles de Boost Run. La plus récente (0001493152-26-006791, du 2026-02-13) entre dans la file de D-0070 par la règle R2 ; l'autre reste hors règle, R2 ne prenant que les notes du dépôt le plus récent. Aucune unité existante ne change d'état ; pas de co-mention (R1).
  - À lire : 1 unité, 2 784 caractères.
  - Réseau de la piste : 49 requêtes en tout.
  - Bloc préparé (1 requête, la page R17 du S-4/A) : 14 966 caractères et non 2 784. La page R réunit les notes des événements postérieurs des quatre jeux d'états du S-4/A ; la valeur du Notes Data Set ne portait que celle de Boost Run Holdings. Le bloc est lu en entier. Réseau de la piste : 50 requêtes.
  - Lecture (sans sous-agent) : 1 observation, 1 abstention. Contrat du 6 novembre 2025 : Boost Run fournit à Fluidstack Infrastructure 1 Ltd. (« Fluidstack ») 1 152 GPU B300 pour deux ans (`commercial`, `purchase_commitment`, Fluidstack cliente). Le montant n'est pas repris : le bloc n'annonce pas d'échelle ; « $63,577 » se lit en milliers comme le reste de la note, mais les mensualités sont écrites « $2,649 million » et balisées 2 649 000 000 $.

  (14) Intégration et résultats (2026-10-22), sans sous-agent :
  - Entités par extrait (point 7), groupe `NF:FLUIDSTACK` :
    - Fluidstack Ltd., tête du groupe (10-K de Hut 8, « Fluidstack Ltd. ("Fluidstack") ») ;
    - Fluidstack CS I Inc., filiale indirecte à 100 % (entrée de D-0064), rattachée avec sa société mère ;
    - Fluidstack USA I, II et IV Inc. et Fluidstack Infrastructure 1 Ltd. par la règle B : chaque déposant les désigne par le terme défini « Fluidstack » (TeraWulf, Cipher, Hut 8, Boost Run) ; Fluidstack USA III Inc. par les règles A et B (« an affiliate of the Fluidstack Member », TeraWulf) ;
    - alias « Fluidstack USA II » (10-Q de Cipher, même bail de Barber Lake que le 8-K qui nomme Fluidstack USA II Inc.) ;
    - les véhicules de fonds au nom de Fluidstack restent hors du groupe (point 2), et la coentreprise d'Abernathy (FS CS I LLC) reste une contrepartie propre.
  - Cerebras : « Cerebras » (alias de D-0066) et « Cerebras Systems Inc. » vont au groupe par son CIK ; aucune filiale n'est nommée dans les lignes (D-0050). Les investisseurs que l'Item 404 nomme sans forme juridique (Alpha Wave, Benchmark, Fidelity, Eclipse, Foundation Capital) restent en attente, comme « DFJ Growth » chez SpaceX : 8 arêtes visibles, hors des agrégats. Alpha Wave Ventures II, LP est une contrepartie propre.
  - Découverte d'origine (point 6) : sur les 19 unités de Cerebras, 13 étaient lues ; les 6 autres (notes du 10-Q du 2026-06-24) sortent de la file (`out_of_scope`, une exclusion).
  - Amendement du point 11, appliqué : les trois notes du 10-Q du 2026-08-12 reçoivent chacune une abstention `duplicate_of_other_block` qui nomme le bloc de la découverte porteur des lignes. Sans elles, ces notes comptaient comme non lues (4 587 blocs lus sur 4 590 au premier rendu, 123 cellules de Cerebras au motif « non traité »).
  - Constat, sans suite dans cette décision : la note du prêt de fonds de roulement du 10-Q du 2026-06-24 (élément `DebtDisclosureTextBlock`) n'est pas au catalogue, car son rôle s'intitule « Working Capital Loan » et l'expression des notes de dette (`text_catalog.NOTE_SPECS`) ne le prend pas. Mesuré sur tous les groupes, 83 dépôts portent un élément standard de note sans bloc correspondant : investissements 68 (AMD 33, TeraWulf 20, Akamai 15), dette 10 (Riot 8, Supermicro 1, Cerebras 1), baux 5 (Backblaze 4, Akamai 1). C'est un défaut antérieur du catalogue, hors du périmètre de cette décision ; il est soumis à l'utilisateur. Pour Cerebras, la note reste non lue : ses montants sont balisés, et la note du trimestre suivant, lue, couvre le même prêt.
  - Réassemblages : un premier (1 493 s) ; l'extraction des BDC Data Sets refaite (`lender num`, 3 465 406 lignes, 2 100 dépôts) ; un second (717 s), aux mêmes effectifs ; un troisième après les abstentions de reprise (757 s). Faits de BDC rattachés : 3 536, inchangés : aucune position de BDC ne nomme Cerebras ni Fluidstack.
  - Résultats, comparés aux tables de 9747107 :
    - Cerebras : 2 725 cellules, dont 485 calculées, 62 partielles et 14 bornées. Événements de l'annexe F : F1 sur 2 trimestres, F2 sur 4 et F5 sur 2 (faiblesse significative du contrôle interne aux 31 mars et 30 juin 2026), soit 485 événements au lieu de 477. Paires : Cerebras → OpenAI, dépendance documentée (30 arêtes, lien L1 : prêt d'OpenAI remboursable en services, bon acquis au versement du prêt et aux livraisons) ; Cerebras → Amazon, causalité non établie (financière seulement, bon de souscription remis à AWS).
    - Fluidstack : 49 arêtes, dont 44 avec un groupe ou un laboratoire. Les 7 paires qui allaient à des entités de Fluidstack (contreparties propres) deviennent 4 paires avec `NF:FLUIDSTACK` : Alphabet (22 arêtes, soutien de crédit des baux, financière seulement), Cipher (11), TeraWulf (7) et Hut 8 (4), commerciales seulement. Toutes concluent « causalité non établie », lien non trouvé, recherche complète au sens de E.0.
    - Paires : 249 au lieu de 250 (7 paires fondues en 4, 2 nouvelles). Conclusions : 11 dépendances documentées (10), 26 relations commerciales doublées d'un financement, 44 achats réciproques seuls, 168 causalités non établies (170).
    - Paires à financement établi au moins un trimestre : 84 au lieu de 82 (Cerebras → Amazon, Cerebras → OpenAI).
    - Cycles : 109 au lieu de 108. Le cycle Cerebras → OpenAI → Cerebras (dépendance documentée, L1) est nouveau ; le cycle Amazon → OpenAI → Cerebras → Amazon existait déjà, avec Cerebras comme contrepartie propre, et passe au groupe.
    - E.7 : « discrimination possible », inchangé ; 166 issues au lieu de 162, dont 93 indéterminées (91), soit 56,0 %. E.1 : 5 « étayé » (3), 68 « non étayé », 10 indéterminées.
  - Contrôles : règle d'arrêt non atteinte (Apollo seul, 22 périodes en échec sur 909) ; doublons de clé primaire de `measures` : 688 lignes écartées (668), dont 239 clés en collision (229), toutes de `lease_not_commenced_bridge`, comme au point 12 de D-0069. Taille des huit tables : 62,6 Mo.
  - Tests : 324, tous réussis, dont `tests/test_d0070.py` (points de conduite, entités de Fluidstack) ; deux tests de D-0059 et de D-0064 suivent le rattachement des entités de Fluidstack.

- **D-0071 — Deux pistes : déclarations de détention (13F, 13D, 13G) et prix des obligations tirés de N-PORT (Oracle, CoreWeave, Beignet). Règles fixées avant tout tirage.**
  (1) Proposition de l'utilisateur, le 2026-10-22 : « Deux pistes qui coûtent peu, restent dans les dépôts SEC et comblent un vrai manque ». Première piste, les déclarations de détention d'actions (13F, 13D, 13G) : « Elles diraient quand un groupe entre dans le capital d'une société cotée et quand il en sort, donc quand le statut « financé » se ferme. » Elles ne couvrent rien avant l'introduction en bourse : pour NVIDIA → CoreWeave, « il faudrait lire le tableau des principaux actionnaires dans le prospectus de CoreWeave ». Seconde piste, le prix des obligations tiré de N-PORT, étendu « avec le code existant, aux obligations d'Oracle, de CoreWeave et du véhicule qui finance le centre de données Hyperion de Meta (Beignet) ». Le constat qui suit est fait sans calcul, sur les tables de 1d248f6 et le cache. Les décisions laissées en attente par D-0069 et D-0070 (dont les 83 notes hors du catalogue) le restent.

  (2) Constat :
  - Aucune déclaration 13F, 13D ou 13G n'est lue. Les submissions en cache en portent :
    - 13F-HR : NVIDIA 11 (depuis le 2024-02-14), Alphabet 51 (depuis le 2022-11-15), Amazon 23 (depuis le 2021-02-11), AMD 3, Galaxy 2, Blackstone 75 et Intel 113, plus des amendements ;
    - 13D et 13G : chez tous les groupes, qu'ils les déposent ou qu'elles portent sur eux, sans que les submissions disent lequel.
  - NVIDIA → CoreWeave vaut `never` à chaque trimestre jusqu'au 2025-01-26, puis `active`.
    - Le tableau des principaux actionnaires du 424B4 de CoreWeave (2025-03-31) donne à NVIDIA 17 932 460 actions de classe A au 15 mars 2025, soit 5,96 % du capital. Le tableau de la série B de l'Item 404 ne nomme que Magnetar, et aucune pièce en cache ne date l'entrée d'avril 2023.
    - Le 15 mars 2025 tombe dans le trimestre de NVIDIA clos le 2025-04-27, déjà `active` : lire ce tableau ne change aucun trimestre.
    - Pour les deux autres introductions récentes, le tableau de SpaceX (au 1er mai 2026) ne nomme pas Alphabet, et Alphabet → SpaceX reste `never` jusqu'au 2026-03-31. Celui de Cerebras (au 31 mars 2026) ne nomme aucun groupe.
    - Ces tableaux ne sont donc pas lus.
  - La condition (a) de §3.2 veut un instrument « acquis par une opération primaire ». Une position de 13F, un 13D ou un 13G, ou une ligne de tableau d'actionnaires, prouvent une détention à une date, pas son origine.
  - Prix au nominal : `nport_price_to_par` compte 1 092 cellules, toutes de SoftBank. `nport_credit_mark` (D-0066) ne prend que le niveau 3 : 29 cellules de CoreWeave (prêts des véhicules CCAC, notes privées de 2023-2024) et 1 de Beignet. Les extraits de D-0065 portent 94 positions en titres de dette de Beignet Investor LLC, aucune obligation d'Oracle ni de CoreWeave, Inc.

  (3) Volet A, déclarations de détention, sans lecture de texte :
  - Paires : celles du statut « financé » dont S est un groupe et C un déclarant (un groupe, ou une contrepartie qui porte un CIK), hors intragroupe, avec au moins une arête de financement en titres (`equity_primary`, `convertible_or_safe`, `noncash_investment`). Il y en a 18 :
    - Amazon → Rivian ; Alphabet → Cipher, ADT, Planet Labs, SpaceX et TeraWulf ;
    - Intel → ASML et Micron ; Microsoft → General Motors ; Micron → Intel ;
    - NVIDIA → CoreWeave, Intel, IREN et Nebius ;
    - Blue Owl → Blue Owl Real Estate Net Lease Trust ; Supermicro → Applied Digital ; TSMC → Intel et SoftBank (Arm Holdings plc).
  - 13F : les 13F-HR et 13F-HR/A des financeurs qui en déposent (Amazon, Alphabet, Intel, NVIDIA), déposés du 2019-01-01 à l'as_of. Pour chacun, l'index, la page de couverture et la table d'information XML.
    - Une ligne de C : l'émetteur commence par une dénomination légale d'une entité de C (règle des BDC, D-0022), puis toute ligne au même préfixe CUSIP de six caractères, si ce préfixe ne désigne que C. Options exclues, actions seulement (`SH`).
    - Valeurs en dollars, en milliers avant le 2023-01-03 (règle de la SEC). Un amendement `RESTATEMENT` remplace le dépôt ; un amendement `NEW HOLDINGS` ajoute ses lignes.
  - 13D et 13G : les formulaires SC 13D, SC 13G, SCHEDULE 13D et SCHEDULE 13G, amendements compris, dont l'accession figure à la fois dans les submissions de S (déclarant) et de C (émetteur).
    - Submissions en cache à l'as_of pour les groupes ; tirées une fois pour les six contreparties.
    - Se lisent sur la page de couverture : les actions détenues, la part de la catégorie et la date de l'événement. La forme XML (depuis le 2024-12-18) se lit par ses champs, la forme HTML antérieure par le gabarit de la page de couverture. Ce qui ne se lit pas est exclu et compté.
  - Mesures, descriptives, à la perspective du déclarant :
    - `ownership_position` : actions de C que S déclare au 13F, par date de portefeuille, avec la valeur déclarée ;
    - `ownership_stake` : part de la catégorie et actions déclarées au 13D ou au 13G, à la date de l'événement.
    - Ni l'une ni l'autre n'entre dans le revenu, l'exposition, les paires ni l'annexe F.
  - Effet sur le statut « financé » :
    - une position ne fait jamais naître la condition (a), faute d'opération primaire attestée (§3.2) ;
    - une sortie publiée la clôt. Une sortie, c'est un 13F de S sans ligne de C après un 13F qui en portait, aucun des deux ne déclarant de traitement confidentiel et aucun amendement ne rétablissant la ligne ; ou un 13D ou un 13G de S sur C à zéro action.
    - La sortie ferme les détentions en actions de la paire (`equity_primary`), à la date de portefeuille du 13F ou à la date de l'événement, connue à la date de dépôt. Les obligations convertibles, les bons et les prêts n'en sont pas fermés : un 13F ne porte que des titres cotés.

  (4) Volet B, prix des obligations, sans changement de définition (D-0058, points 8 et 28) :
  - Nœuds : Oracle (`ORCL`), CoreWeave (`CRWV`) et Beignet Investor LLC (`CP:beignet investor llc`).
  - Émetteur : la forme normalisée du nom commence par « oracle corp », « coreweave » ou « beignet investor ». À défaut, un LEI relevé avec un tel nom et accepté par la majorité, comme pour SoftBank. Par titre, la majorité des positions porte un tel nom et une au moins un intitulé qui contient « ORACLE », « COREWEAVE » ou « BEIGNET ».
    - Cette règle écarte « VANTAGE ORACLE TX » et « ORACLE VISION HOLDCO ». Elle garde les titres des filiales de CoreWeave (CCAC IV et suivantes), qui sont des dettes de son groupe.
  - Positions : titres de dette en nominal (DBT, PA), longues, identifiées par ISIN ou CUSIP, au dernier dépôt de chaque série pour la date, tous niveaux de juste valeur confondus. La mesure de niveau 3 de D-0066 reste telle quelle.
  - Source : les 28 archives des Form N-PORT Data Sets (2019q4 à 2026q3, 11,9 Go), tirées une troisième fois, scannées pour ces trois émetteurs (extraits sous `bonds/`), puis effacées. Une archive publiée après l'as_of est écartée.
  - Publié avec chaque valeur : le nominal, le nombre de séries, la monnaie, l'intitulé, l'échéance et le coupon. Perspective `counterparty` : une tension de marché déclarée par des tiers, jamais une probabilité de défaut, hors du financement, de l'exposition, des paires, des cycles et de l'annexe F.
  - Le code de SoftBank ne change pas : ses 1 092 cellules doivent ressortir à l'octet près.

  (5) Ordre et commits :
  - la décision ;
  - le code et les tests des deux volets ;
  - le tirage de N-PORT, puis son volume consigné ici avant calcul ;
  - les tirages du volet A (submissions, 13F, 13D et 13G), puis leur volume consigné ici avant calcul ;
  - l'intégration : réassemblage, rendus, résultats, tests, commit, push, rapport.
  - Réseau : un seul processus à la fois, environ 28 archives et quelques centaines de requêtes.

  (6) Tirage de N-PORT et volume du volet B, consignés avant tout calcul de la mesure :
  - Le tirage a commencé après le commit du code du volet B (9966307), pendant l'écriture du code du volet A, qui ne tire rien. Aucune donnée du volet A n'est tirée avant son code (9fec093).
  - 28 archives tirées une troisième fois (11,94 Go, 28 requêtes), toutes scannées, aucune publiée après l'as_of. Chacune a la même empreinte SHA-256 qu'en D-0065. Extraits gardés sous `bonds/` : 160 682 positions ; archives effacées.
  - LEI : cinq acceptés à la majorité, aucune archive à rescanner.
    - Deux d'Oracle : 137 828 et 6 083 positions, dont 137 805 et 6 070 sous un nom d'Oracle.
    - Trois de CoreWeave : 4 553, 48 et 27 positions.
    - Trois refusés : un LEI porté par 8 623 positions dont 2 sous le nom d'Oracle, et deux autres de 157 et 99 positions.
  - Positions retenues par le nom ou par un LEI accepté : 151 809. Oracle 144 508 par le nom, CoreWeave 6 202, Beignet 1 059, et 40 par le seul LEI.
  - Étapes de la sélection :
    - 45 533 hors titres de dette en nominal, dont 41 182 actions ;
    - 38 courtes, 101 sans identifiant ;
    - 4 hors émetteur : trois titres Reg S de CoreWeave dont l'intitulé (« CRWV 9 02/01/31 ») ne contient pas « COREWEAVE ».
  - Retenues : 106 133 positions, 104 524 au dernier dépôt de chaque série.
    - Oracle : 96 titres, 1 771 séries, 108 dates de portefeuille du 2019-09-30 au 2026-07-31, 3 944 cellules. Niveaux 2 (99 856 positions) et 1 (10) ; 115 positions en euros.
    - CoreWeave : 8 titres dont 2 convertibles, 623 séries, 21 dates du 2025-05-30 au 2026-07-31, 66 cellules. Niveau 2 ; 52 positions en euros.
    - Beignet : 2 titres, 390 séries, 14 dates du 2025-09-30 au 2026-07-31, 14 cellules. Niveaux 2 (957) et 3 (94).
    - En tout, 4 024 cellules attendues.
  - Noms du préfiltre que la règle écarte : 2 231 positions.
    - Oracle Financial Services Software, société indienne, au moins 1 822 positions sous huit graphies ; des contrats sur écart (« CFD ») ; des produits structurés d'autres émetteurs (« UBS AG into Oracle Corp. ») ; « Oracle » seul (52) ; « Vantage Oracle TX » (24) et « Oracle Vision Holdco » (23).
    - Le nom abrégé écarte aussi 82 positions de l'obligation de Beignet : « BEIGNET INV LLC » (32), « BEIGNET INVEST 6.581% 05/30/49 » (17), « Beignet Investments, LLC » (14), « BEIGNET INVSTR. LL 6.581% » (11), « Beignet » (8). La règle reste telle que fixée au point 4 ; ce manque se publie avec la mesure.
  - Précisions du code, fixées avant le tirage :
    - le début de nom s'arrête à une fin de mot : « oracle corp/de » oui, « oracle corporate » non ;
    - l'intitulé doit contenir le mot du nœud du titre ;
    - un titre est dit convertible si une position remplit l'Item C.9.f (rubriques IS_CONVTIBLE_MANDATORY et IS_CONVTIBLE_CONTINGENT, section 5.12 de la description) ;
    - une cellule garde au plus 20 accessions, avec leur nombre.

  (7) Tirages et volume du volet A, consignés avant tout calcul :
  - Les submissions de General Motors et d'Arm étaient déjà en cache. Ont été tirées celles des quatre autres contreparties (Rivian, ADT, Planet Labs, Blue Owl Real Estate Net Lease Trust), 5 requêtes avec une page de plus pour ADT. Puis 125 dépôts complets ; 130 requêtes en tout, toutes en 200, en 32 secondes.
  - 13F : 120 dépôts, tous lus par leurs champs (116 initiaux et 4 amendements RESTATEMENT, tous des rapports complets, aucun traitement confidentiel).
    - Amazon 23 dates de portefeuille (2020-12-31 au 2026-06-30), Alphabet 51 (2013-12-31 au 2026-06-30, dont 36 déposés en novembre 2022 pour des périodes passées), Intel 34 (2018-03-31 au 2026-06-30), NVIDIA 11 (2023-12-31 au 2026-06-30).
    - Lignes rattachées à une paire, toutes en actions (SH), aucune option : Amazon → Rivian 19 ; Alphabet → Planet Labs 19, dont une par le préfixe CUSIP (« Planet Labs Inc. ») ; NVIDIA → CoreWeave 6, → Intel 3, → Nebius 7. Aucune ligne d'ADT, de Cipher, de TeraWulf ni d'IREN ; aucune d'ASML ni de Micron chez Intel.
    - Ligne non rattachée : « SPACE EXPLORATION TECHN CORP », nom abrégé du 13F (Alphabet, 2026-06-30 ; aussi chez NVIDIA, hors paire). Il ne commence pas par la dénomination légale « space exploration technologies corp », et son préfixe CUSIP n'est porté par aucune ligne rattachée. La règle reste telle que fixée.
  - 13D et 13G : 5 annexes de la période dont l'en-tête fait de S le déclarant et de C la société visée, toutes lues (3 en XML, 2 sur le gabarit de la page de couverture) : Amazon → Rivian 1, Intel → ASML 1, NVIDIA → CoreWeave 2, NVIDIA → Nebius 1. Aucune à zéro action.
  - Limite : seules se cherchent les annexes présentes dans les submissions du CIK du groupe. Une annexe déposée par une filiale sous son propre CIK (par exemple Google LLC pour ADT ou Planet Labs) n'est pas vue.
  - Précisions du code, fixées avant ces tirages (9fec093) :
    - Les annexes 13D et 13G suivent la même période que les 13F (dépôts du 2019-01-01 à l'as_of). Celles d'avant ne se lisent pas : Intel → ASML 4 (2012 à 2018) ; Intel et Micron 7 (1998 à 2010).
    - Le sens d'une annexe se lit dans l'en-tête SGML : société visée et déposant, par leur CIK.
    - Une sortie compare deux 13F consécutifs de S. Le second doit être un rapport complet (13F HOLDINGS REPORT) : un rapport combiné laisse des lignes à un autre gestionnaire et ne prouve aucune absence.
    - Les dénominations légales valent aussi sans le suffixe d'État du nom conforme d'EDGAR (« rivian automotive inc / de »). Cela ajoute quatre formes : dave inc, jefferson capital inc, qualcomm inc, rivian automotive inc.

  (8) Intégration et résultats :
  - Réassemblage (830 s) :
    - `measures` gagne 4 083 cellules : 4 024 `nport_price_to_par` pour les trois nœuds, 54 `ownership_position` et 5 `ownership_stake` ;
    - `documents` gagne 130 lignes, les ressources tirées ;
    - aucune autre ligne des huit tables ne change ;
    - les 1 092 cellules de SoftBank ressortent à l'octet près (même empreinte de leur export).
  - Volet B, à la dernière date de portefeuille (2026-07-31) :
    - Oracle : 3 944 cellules sur 96 titres depuis le 2019-09-30. 58 titres sont détenus dans les trois derniers mois, de 56,1 % (3,85 % 2060) à 101,2 % (6,15 % 2029).
      - Les six émissions de septembre 2025, entre 99,7 % et 100,6 % au 2025-09-30, valent 94,4 % (2030), 92,1 % (2032), 89,8 % (2035), 82,1 % (2045), 79,5 % (2055) et 78,6 % (2065), chacune à son plus bas.
      - Celles de février 2026 sont passées de 95,9 %–100,4 % à 88,0 %–97,5 %.
    - CoreWeave : 66 cellules sur 8 titres depuis le 2025-05-30.
      - Valeurs de 88,2 % (convertible 1,75 % 2032, à 120,5 % à sa première date, le 2026-04-30) à 94,2 % (convertible 1,75 % 2031).
      - Les obligations à haut rendement, entre 89,5 % et 93,6 %, sont toutes à leur plus bas, sauf celle de 2030 (92,3 % au 2025-11-30).
    - Beignet : 14 cellules. L'obligation 6,581 % 2049, à 106,7 % au 2025-10-31, vaut 96,9 %, son plus bas, chez 76 séries.
    - Une obligation à coupon fixe perd de sa valeur quand les taux montent comme quand l'écart de crédit s'élargit, et la mesure ne sépare pas les deux. Les titres de 2020-2021, à coupon bas, sont sous le pair par le seul effet des taux.
    - Rendu : un taux annuel déclaré en fraction (sous 0,25) s'affiche en pourcentage, signalé. C'est le cas d'un titre à taux variable d'Oracle (2029).
  - Volet A :
    - 54 positions au 13F :
      - Amazon → Rivian 19 et Alphabet → Planet Labs 19, du 2021-12-31 au 2026-06-30 ;
      - NVIDIA → CoreWeave 6 : 24 182 460 actions au 2025-03-31, 47 213 353 depuis le 2026-03-31 ;
      - NVIDIA → Intel 3 : 214 776 632 actions depuis le 2025-12-31 ;
      - NVIDIA → Nebius 7 : 1 190 476 actions depuis le 2024-12-31.
    - 5 parts aux annexes :
      - Amazon → Rivian 18,1 % au 2021-12-31 ;
      - Intel → ASML 1,6 % au 2018-12-31 ;
      - NVIDIA → CoreWeave 7,0 % au 2025-03-31 et 11,5 % au 2026-01-23, avec les mêmes nombres d'actions qu'au 13F ;
      - NVIDIA → Nebius 9,3 % au 2026-07-13 (22 256 412 actions, après le dernier 13F).
    - Aucune sortie. La série de 13F de chaque paire est continue de sa première ligne au 2026-06-30, et aucune annexe n'est à zéro action. Les 27 744 cellules du statut « financé » sont inchangées.
    - Intel ne déclare aucune ligne d'ASML à ses 13F de la période : rien à comparer, donc aucune sortie, et la paire est déjà `lapsed`.
    - NVIDIA → CoreWeave : les déclarations datent la détention du 2025-03-31 au plus tôt, dans un trimestre déjà `active`. Elles ne changent rien, comme prévu au point 2.
  - Bug n° 4 de l'audit : ces déclarations ne ferment un statut que si le financeur sort. Aucun des dix-huit ne l'a fait dans la période. Le bug reste ouvert pour les participations non cotées et pour les sorties d'avant 2019.
  - Question laissée à l'utilisateur. NVIDIA → CoreWeave vaut `never` jusqu'au 2025-01-26 alors que NVIDIA détenait des actions avant l'introduction. Aucune pièce en cache ne date son entrée. Faut-il qu'une détention documentée plus tard, d'origine inconnue, fasse passer les trimestres antérieurs de `never` à `unknown` ?

- **D-0072 — Observations d'architecture de l'audit : ce qui est déjà fait, ce qui se fait, ce qui ne se fait pas. Règles fixées avant tout changement.**
  (1) Origine : observations remises par l'utilisateur le 2026-10-22 (« Voilà d'autres observations de l'audit à éventuellement considérer si c'est pertinent (ne refais pas ce qui est déjà fait) »). Chaque observation est vérifiée sur le code, sur `SPEC.md` et sur les tables de 580e8e9 avant toute modification. Aucune règle de mesure ne change, aucune requête réseau n'est faite, l'as_of reste le 2026-10-07.

  (2) Déjà fait :
  - Export des huit tables en Parquet ZSTD (D-0069, point 9) : `facts.parquet` pèse 48,3 Mio, contre 95,4 Mio avant.
  - Versions épinglées dans `requirements.txt`, ordre des commandes dans `README.md` (D-0069, point 9).
  - Mémo propre aux plages de citations (D-0062, point 5). La recherche d'environ 9 minutes ne se refait que si un document, `textnorm.py`, `cache.py` ou la classe `QuoteRanges` change, et non à chaque changement de code.
  - Tables committées aux étapes clés : elles ne le sont qu'à l'intégration d'une décision.

  (3) Ce qui se fait :
  - a. Emplacement des faits.
    - Constat. Dans `facts`, `locator` est un texte JSON qui répète des colonnes :
      - pour les 1 077 903 faits d'instance, l'accession, `fact_id` et `occ_rank` sont égaux aux colonnes, et le fichier est dans `fact_key` ;
      - pour les 501 772 faits `companyfacts`, le CIK, l'accession, le concept, l'unité et la période sont dans la clé et les colonnes.
      - Aucune accession n'a deux fichiers d'instance, et aucun `id` n'y revient deux fois. `locator` fait 41,9 % du fichier, `fact_id` 27,5 %.
    - Règle, conforme à §7 (« l'emplacement de chaque nombre est une colonne, `locator` : l'`id` du fait dans l'instance… ») :
      - pour un fait d'instance, `locator` vaut l'`id` du fait, ou `#` suivi du rang d'occurrence pour les 51 816 faits qui n'en ont pas ;
      - la colonne `fact_id`, désormais en double, quitte le schéma ;
      - pour un fait `companyfacts`, `locator` nomme la ressource de l'API (`companyfacts/CIK…`) ; le concept, l'unité et la période restent dans la clé et les colonnes ;
      - les autres sources ne changent pas (plage d'octets et citation pour un texte).
    - La transformation se fait au chargement des faits dans la base ; les fichiers de `db/` ne changent pas. L'ordre physique actuel, par dépôt, est gardé.
    - Effet mesuré sur une copie : 48,3 → 28,2 Mio, autant que sans la colonne. Seules changent les colonnes `locator` et `fact_id` de `facts`, et, dans `audit/numbers.csv`, la colonne `locator` des termes de ces deux sources.
  - b. Recherche des citations en parallèle. Au-delà de huit documents à chercher, les documents se répartissent sur un pool de processus (démarrage `spawn`, un par cœur). Chaque document reste cherché d'un bloc, et les plages se rangent par clé, comme avant. Elles doivent ressortir identiques : `observations` à l'octet près.
  - c. Profil. Un échantillonneur (100 Hz, `pipeline/profiling.py`) profile le réassemblage à froid avant toute autre optimisation. Ses postes sont consignés aux résultats ; aucune optimisation ne suit dans cette décision.
  - d. Outils :
    - `pyproject.toml` : métadonnées, Python 3.13, dépendances épinglées, réglages de ruff et de pytest. `requirements.txt` épingle aussi les dépendances transitives de l'environnement.
    - Le fichier `uv.lock` n'est pas produit : `uv lock` interroge l'index PyPI, hors du client unique et du journal. Il se produit hors de cette exécution.
    - `Makefile` : mode d'emploi exécutable (`make help`), de la collecte au rendu, avec les cibles réseau signalées. `make check` lance ruff, puis les tests.
    - ruff, règles F (pyflakes) et E9 : 51 constats, tous corrigés. Ce sont 24 imports inutilisés, 9 f-strings sans champ et 18 variables jamais lues. Toutes ces variables sont des restes (comptes jamais affichés, requête morte, dictionnaire inutilisé) ; aucun nom n'est indéfini, aucun calcul n'est oublié.
    - Crochet `.githooks/pre-commit` (`make check`), fourni mais non activé ici. Il s'active par `git config core.hooksPath .githooks`.
    - DuckDB : `threads` et `memory_limit` explicites dans `config.yaml`, appliqués aux connexions de l'assemblage, du mémo, du rendu et de l'aperçu. Les valeurs sont celles du défaut de cet environnement pour les cœurs (4), et 10 Go de mémoire.
  - e. Déterminisme. Un second réassemblage à froid (`--sans-cache`), lancé sous `PYTHONHASHSEED=1` sans relance, puis son rendu, doivent redonner les huit tables et les rendus à l'octet près. Si c'est le cas, la relance par `PYTHONHASHSEED=0` est retirée d'`assemble` et de `render`. Sinon, chaque écart est tracé jusqu'à l'ensemble non trié qui le cause.

  (4) Ce qui ne se fait pas, et pourquoi :
  - JSON de `flags`, `lineage` et `evidence` en vraies colonnes. Les tables sont petites (`measures` 2,9 Mo, `controls` 1,4 Mo). Les drapeaux varient d'une mesure à l'autre et n'ont pas de schéma commun. Le changement toucherait le schéma de §7 et la plupart des lecteurs, pour un gain que le profil doit d'abord montrer.
  - Dates de `measures` en DATE. §7 donne `none` aux composantes sans objet d'une clé primaire ; une colonne DATE ne peut ni le porter ni être nulle dans une clé.
  - Mémo par étape. Plusieurs étapes lisent la base DuckDB construite pendant l'exécution, et des valeurs calculées en amont qui ne sont pas dans leur clé. Une clé par étape qui ne les verrait pas rendrait des tables périmées sans le dire. La version sûre doit hacher toutes les entrées de chaque étape. Son gain porte sur les itérations de développement, et le poste le plus lourd, les citations, a déjà son mémo fin. Laissé à la décision de l'utilisateur, profil à l'appui.
  - Conversion des archives en Parquet complet. Il faudrait environ 40 Go, pour 19 Go libres dans cet environnement, et le cache, non versionné, ne survit pas à l'environnement. `keep_zip` reste faux (D-0069).
  - Réécriture en SQL des calculs des défauts. Ils sont corrigés depuis D-0069, avec un test chacun ; les réécrire ne corrige plus rien et risque de changer des valeurs.
  - `preserve_insertion_order=false`. Des requêtes intermédiaires sans ORDER BY alimentent des « premier trouvé » ; l'ordre deviendrait variable d'une exécution à l'autre.
  - `audit/` généré à la demande. §12.2 en fait le livrable de l'auditeur, écrit et commité. Ses copies (`measures.parquet`, `controls.parquet`, `synthesis.md`) sont les mêmes objets git que les originaux et ne coûtent rien en stockage.

  (5) Ordre :
  - la décision ;
  - le code et les tests ;
  - un réassemblage à froid profilé, et la comparaison de ses tables avec celles de 580e8e9 ;
  - le réassemblage sous `PYTHONHASHSEED=1` et les rendus des deux ;
  - les résultats ; commit, push, rapport.

  (6) Résultats :
  - Réassemblage à froid profilé, graine 0 : 1 078 s. Rien n'est repris du mémo, et les plages de citations se recherchent de nouveau, leur code ayant changé. Comparé aux tables de 580e8e9 :
    - `measures`, `controls`, `exclusions`, `links`, `observations`, `entities` et `documents` sont identiques à l'octet près. `observations` établit que la recherche répartie donne les mêmes plages ;
    - `facts` : `fact_id` est retirée, `locator` suit la règle du point 3 a sur chaque ligne, et aucune autre valeur ne change. Le fichier passe de 48,3 à 28,2 Mio ;
    - rendus : `synthesis.md` et `series.md` sont identiques. `delta.md` ne change que par sa base (580e8e9), sa durée et la décision nouvelle. Hors `delta.md`, `audit/numbers.csv` ne change que dans la colonne `locator` (21 756 lignes ; 24,7 → 22,2 Mo).
  - Recherche des citations : 218 s sur quatre processus, contre 563 s en série (D-0062, point 5).
  - Sonde de déterminisme : un réassemblage `--sans-cache` sous `PYTHONHASHSEED=1`, sans relance, prend 1 058 s.
    - Les huit tables sont identiques à l'octet près à celles de la graine 0, et les statistiques ne diffèrent que par la durée.
    - Les rendus sous la même graine sont identiques, à la ligne de durée de `delta.md` près.
    - La relance est donc retirée d'`assemble` et de `render`, comme prévu au point 3 e.
  - Profil (1 080 s échantillonnées), postes principaux :
    - filtres par masque booléen sur les colonnes texte Arrow de pandas 3 : 233 s de temps propre dans `pyarrow.take`. Ils sont appelés en boucle par `controls.siblings` (86 s inclusifs), `controls_more.role_children` (60 s), `nport.unlisted` (93 s) et `nport.bond_cells` (75 s, dont 58 s pour `par_rows`) ;
    - recherche des citations : 218 s, seulement quand son mémo est vide ;
    - base XBRL (`model.build_base`) : 65 s, dont 56 s de chargement des faits ;
    - empreintes SHA-256 des documents (`cache.sha256`) : 36 s.
    - Piste pour une décision suivante : regrouper une fois au lieu de filtrer à chaque tour de boucle, ou confier ces filtres à DuckDB. Rien n'en est fait ici.
  - Outils : `make check` passe (ruff sans constat, 346 tests).

- **D-0073 — Une seule source pour l'as_of : la clé `as_of` de `config.yaml`. Règles fixées avant tout changement.**
  (1) Origine : remarque R3 de l'audit, remise par l'utilisateur le 2026-10-23 (« R3 — as_of écrit en dur : une mise à jour exige de modifier le code »), à considérer « éventuellement ». Elle est vérifiée sur le code de 98a0bc3. L'as_of de l'exécution reste le 2026-10-07, et aucune requête réseau n'est faite.

  (2) Constat, vérifié :
  - Trois constantes `AS_OF = "2026-10-07"` : `discovery.py:29`, `lender_liabilities.py:36` et `sb_own.py:22`. Sept modules importent celle de `discovery` : `foreign`, `formd`, `montages`, `nf_discovery`, `nport`, `ownership` et `sixk`.
  - `text_catalog.py` écrit la date en dur (lignes 189 et 277), et le `Makefile` la met par défaut.
  - `nport.py:67` lit `config.load().get("as_of")`, une clé qui n'existe pas. La requête de la page des Form N-PORT Data Sets du 2026-10-19 (ligne 25 055 du journal) porte donc `as_of: null`. C'est la seule des 25 582 lignes du journal dont l'as_of n'est pas le 2026-10-07.
  - Trouvé en plus pendant la vérification :
    - faute d'argument, `phase0.py` prend la date du jour ; le lecteur (`reader._run_info`) aussi, faute de `work/tmp/run.json` ;
    - 19 bornes de `config.yaml` finissent en dur le 2026-10-07 : périodes des montages et de `softbank_deep`, de N-PORT et du volet A de D-0071, fenêtre des offres de rachat, rejeu des contrats des laboratoires, date de la liste des symboles d'EDGAR. Une mise à jour devrait aussi les changer une à une ;
    - l'assemblage ne vérifie pas que l'inventaire et les fenêtres (`db/phase0.json`) sont au même as_of que lui.
  - Ce qui n'est pas un défaut. Les lignes d'observations et du journal portent toutes l'as_of du 2026-10-07 malgré quinze jours de travail. L'as_of est la date de connaissance de l'exécution, non la date du travail :
    - ce qui est publié après est écarté par règle (archives N-PORT publiées après, dépôts déposés après) ;
    - le journal donne dans `ts` la date réelle de chaque requête ;
    - §9.6 fait de « le même `as_of` » une condition de la reproductibilité ;
    - le README ne contient pas la phrase citée ; l'allongement annuel de la fenêtre est dans §11 (phase 0).
  - Dates qui ne sont pas des as_of, et qui restent :
    - la date de la décision du périmètre et l'entrée des groupes dans les agrégats ;
    - la première passe du bloc `text` ;
    - le nom daté d'une réponse du service de recherche en cache (`discovery.py:395`), version d'une ressource vivante (« chaque tirage est horodaté »).

  (3) Règles :
  - Source unique : la clé `as_of` de `config.yaml`, lue par `config.as_of()`. Versionnée, elle se tient à côté des critères et des tables qu'elle date. Ni variable d'environnement, invisible dans le dépôt, ni date du jour.
  - Les commandes qui prenaient un as_of en argument (`assemble`, `render`, `phase0`, `phase1_run`, `phase2_fetch`, `universe`, `formd`) le prennent de la configuration. Un argument reste accepté, mais il doit être égal à la clé ; sinon la commande s'arrête et dit pourquoi.
  - Les trois constantes disparaissent. Les sept modules, `text_catalog` et `nport.py:67` lisent `config.as_of()`.
  - Une borne de `config.yaml` qui finit à l'as_of s'écrit `as_of`, et `config.load()` la remplace par la date. Les 19 bornes ci-dessus passent à `as_of`.
  - Gardes :
    - l'assemblage s'arrête si `db/phase0.json` porte un autre as_of (« relancer la phase 0 ») ;
    - le lecteur s'arrête si la passe en cours (`work/tmp/run*.json`) porte un autre as_of (« ouvrir une passe nouvelle ») ; faute de fichier, il prend l'as_of de la configuration, non la date du jour.
  - Le `Makefile` ne fixe plus de date.
  - La ligne 25 055 du journal reste telle quelle : le journal ne se réécrit pas.
  - Effet attendu : aucun, puisque l'as_of reste le 2026-10-07. Les huit tables et les rendus doivent ressortir à l'octet près, sauf `delta.md` (base et durée) et `audit/annex_e.txt` et `annex_f.txt`, qui portent le diff de `config.yaml`.

  (4) Mettre le modèle à jour devient : changer `as_of` dans `config.yaml`, puis relancer les phases dans l'ordre du README. Les gardes arrêtent toute commande qui mêlerait deux as_of.

  (5) Résultats :
  - Code (078a179) :
    - la clé `as_of` est en tête de `config.yaml`, et les 19 bornes s'écrivent `as_of` ;
    - `config.as_of()` lit la clé ; `config.check_as_of()` arrête une commande devant une étape d'un autre as_of ;
    - les trois constantes sont retirées. Les sept modules, `text_catalog` et `nport.page` (l'ancienne ligne 67) lisent `config.as_of()`. La date de la liste des symboles vient de la borne `tickers` (`nport.tickers_day`), et le message d'exclusion qui la cite reste le même ;
    - les commandes du point 3 se lancent sans date. Un argument daté est vérifié ;
    - gardes : celles du point 3, et trois du même ordre (point 4). La phase 1 et l'univers s'arrêtent devant un autre `db/phase0.json`, le rendu devant d'autres tables (`work/tmp/assemble_stats.json`, « relancer l'assemblage ») ;
    - le `Makefile` ne fixe plus de date, et le README décrit la source unique et la mise à jour.
  - Tests : 13 nouveaux (`tests/test_d0073.py`). Le test de `config.load` (D-0062) reçoit une clé `as_of`, devenue obligatoire. `make check` passe : ruff sans constat, 359 tests.
  - Réassemblage sans argument daté : 1 207 s.
    - Rien n'est repris du mémo des étapes, car le code et `config.yaml` ont changé. Les plages de citations sont reprises du leur : `textnorm.py`, `cache.py` et `load.py` sont inchangés.
    - La base XBRL seule prend 105 s, contre 67 s en D-0072, sans changement de son code.
    - Les huit tables sont identiques à l'octet près à celles de 98a0bc3.
  - Rendu sans argument daté :
    - `synthesis.md`, `series.md`, `audit/numbers.csv` et `audit/annex_e.txt` sont identiques. Les critères de l'annexe E n'ont pas changé, et son diff reste vide ;
    - `delta.md` ne change que par la durée et par la ligne de la décision nouvelle ; sa base est la même, les tables n'ayant pas changé ;
    - `audit/annex_f.txt` ne change que par le diff de `config.yaml` : la clé `as_of` et les 19 bornes.
  - Aucune requête réseau. Le journal reste à 25 583 lignes.
  - Erratum du point 2 : le journal compte 25 583 lignes, dont 25 582 au 2026-10-07 ; la ligne 25 055 est la seule à `as_of: null`.

- **D-0074 — Mise à jour du modèle à l'as_of du 2026-10-24. Règles fixées avant tout tirage.**
  (1) Origine : demande de l'utilisateur, le 2026-10-24 : « Fais une update du modèle à la date du jour ». C'est une exécution nouvelle (§11.5), la première après celle du 2026-10-07, et la première mise à jour selon D-0073 (point 4). Le 2026-10-24 est un samedi : la connaissance porte sur les dépôts dont la date de dépôt est au plus le vendredi 2026-10-23. Ni groupe, ni bloc de §14, ni critère des annexes E et F, ni seuil, ni lexique, ni règle de lecture ne change.

  (2) Constat, sur le code de 8a17254, avant tout tirage :
  - Changer la clé `as_of` suffit pour les phases 0 à 2 et pour les ressources de l'API (`cache/api/{cik}/{ressource}/{as_of}`), qui se tirent une fois à l'as_of nouvel. `phase0_index` prend encore l'as_of en argument, sans le vérifier : un oubli de D-0073.
  - Ressources vivantes hors de l'API, tirées une fois sous un nom fixe :
    - la page des Notes Data Sets (`financial-statement-notes-data-sets_2026-10-09`) et la liste des noms d'EDGAR (`cik-lookup-data_2026-10-09`) ;
    - la page des Form N-PORT Data Sets, sans date ;
    - la page des BDC Data Sets (`bdc-data-sets_2026-10-07`), tirée hors du code, comme ses archives ;
    - les submissions des véhicules des BDC (`lender_liabilities`) et des déposants suivis par les montages (`montages.periodic`), en cache sans date.
    Une mise à jour les relirait telles quelles.
  - Recherches plein texte : chaque requête porte sa période entière, de son début à l'as_of. Avec l'as_of nouvel, l'adresse change et tout se retirerait : environ 2 600 pages pour la découverte et la piste des non-déposants (209 fenêtres consignées).
  - Les catalogues préparés ne se recalculent pas à l'identique. Vérification sans réseau, à l'as_of du 2026-10-07, sur le code de la mise à jour :
    - la recherche de la découverte, rejouée du cache, redonne ses 9 390 résultats à l'octet près ;
    - le catalogue de la tranche et celui du bloc `text` se reconstruisent à l'identique (4 359 et 4 692 blocs), comme ceux des 6-K, du volet B et C de SoftBank et des annonces des BDC ;
    - mais une préparation complète des montages ramène leur catalogue de 1 224 à 1 135 blocs : 91 blocs, tous lus, en sortent. La préparation dépend de ce qui a été lu depuis (une fenêtre déjà couverte par un bloc lu du même dépôt n'est plus servie), et le catalogue s'est construit montage par montage. Les lectures de ces blocs ne se chargeraient plus (`load_observations` ne charge que les blocs du catalogue) ;
    - le rejeu complet des recherches de trois montages (`athene_whco`, `galaxy_helios`, `stargate`) ne redonne pas leurs résultats gardés, et celui de `meta_hyperion` demande des pages absentes du cache.
  - Files plafonnées, la plupart triées du plus récent au plus ancien : montages (plafond par montage), 6-K (80 fenêtres par groupe), volet B de SoftBank (200 unités) et 6-K d'Arm (80), annonces des BDC (40), piste des non-déposants (300). Recalculées telles quelles, les unités nouvelles pousseraient au-delà du plafond des blocs déjà lus. Au plafond ou près de lui : les montages `anthropic_chain`, `labs_corpus` et `galaxy_helios`, les 6-K d'ASML, de SK hynix et d'Arm.
  - File de la découverte : figée depuis le 2026-10-09, lue jusqu'au rang 50 de la passe A (395 unités, toutes préparées, D-0041). Ses unités préparées s'y rattachent par leur numéro d'ordre. Un recalcul de la file renumérote, si bien que ces rattachements, ses exclusions et la recherche complète côté client (E.0) se décaleraient.
  - Piste des non-déposants : ses unités préparées s'y rattachent par leur pièce, mais un recalcul change le rang affiché des unités non lues.

  (3) Règles :
  - As_of : le 2026-10-24, dans `config.yaml`. La clé `as_of_previous` garde, dans l'ordre, les as_of des exécutions précédentes : `["2026-10-07"]`.
  - Ressources vivantes : chacune se tire une fois, à l'as_of nouvel, et se garde datée de lui, sans écraser l'ancienne (§9.6). Ce sont les submissions, `companyfacts`, `company_tickers.json`, les pages des trois jeux de données, la liste des noms d'EDGAR, et les submissions des véhicules et des déposants des montages, désormais datées sous `cache/api`. Une archive déjà tirée ne se retire pas.
  - Jeux de données : une archive nouvelle de la page (BDC, Notes, N-PORT), publiée à l'as_of au plus selon son en-tête Last-Modified, se tire et se traite comme les autres. Aucun traitement ne change.
  - Recherches plein texte : une requête se coupe aux as_of précédents. Les résultats gardés restent tels quels, dans leur ordre. Une requête qui y figure ne se cherche que sur la fenêtre nouvelle, du 2026-10-08 au 2026-10-24, et ses résultats nouveaux s'ajoutent à la suite. Une requête jamais cherchée l'est sur toutes ses fenêtres. Le rejeu des laboratoires suit les fenêtres de la découverte. Une fenêtre déjà consignée ne se consigne pas une seconde fois.
  - Reprise de l'exécution précédente : un catalogue préparé (montages, 6-K, SoftBank) et une file (découverte, piste des non-déposants) gardent leurs blocs et leurs unités tels quels, dans leur ordre, numéros d'ordre compris. Ils sont copiés une fois avant leur première réécriture, sous `{nom}.2026-10-07`. Seuls s'y ajoutent les blocs et les unités tirés de dépôts de la période nouvelle, dont la clé n'y est pas déjà. Les décomptes des montages (pièces sans fenêtre, au-delà du plafond, facteurs de risque, déjà lues) gardent de même leurs entrées anciennes.
  - Files plafonnées (règle de D-0058, point 24, pour un lexique enrichi, étendue à une période nouvelle) : les unités de la période nouvelle forment une file à part, dans l'ordre de la file, avec le même plafond. Les unités anciennes gardent leur état. Sans as_of précédent, c'est le plafond simple, comme avant.
  - Découverte (D-0041) :
    - la frontière de lecture s'applique aux unités nouvelles : une unité nouvelle de la passe A d'un candidat classé au plus au rang 50 par l'exécution précédente se lit ;
    - les autres restent non traitées, sauf celles que d'autres blocs sélectionnent déjà (`foreign`, `form_d`).
  - Ordre :
    - verrou de session (§11.5) ;
    - phases 0, univers attendu, index, phases 1 et 2, catalogues de la tranche et du bloc `text`, puis leur lecture ;
    - blocs de §14 : `lender` et `lender_portfolio` (BDC Data Sets), `lender_liabilities`, `discovery` (Notes, recherche, pièces, Form D, file), piste des non-déposants, `form_d`, `foreign` et 6-K, `sb_own`, `nport`, `ownership`, puis les montages, préparés après la lecture du texte des groupes comme aux exécutions précédentes ;
    - un seul processus réseau à la fois, 5 requêtes par seconde au plus, pause de 10 minutes après un refus 403, chaque requête au journal.
  - Volumes consignés ici avant toute lecture, catalogue par catalogue : dépôts nouveaux par classe, blocs à lire, caractères.
  - Lecture : sans sous-agent, du plus récent au plus ancien, règles et guides inchangés. Un bloc dont la clé a déjà des observations ne se relit pas (§9.6).
  - Réassemblage et rendus à l'as_of nouvel. `delta.md` se compare aux tables de 580e8e9, dernier commit qui les porte.
  - Effets attendus : des cellules nouvelles pour les périodes closes depuis, et des valeurs changées pour des périodes déjà publiées (`companyfacts` révisés, retraitements), que `delta.md` montre par `recast_cause`.
  - Non fait : aucun bloc nouveau, aucune relecture ; la tâche planifiée de §11.5 n'est pas créée.

  (4) Code, avant tout tirage :
  - `config.previous_as_of()` et `config.search_windows(début, fin)` : la clé `as_of_previous`, vérifiée (dates croissantes, antérieures à l'as_of), et les fenêtres d'une recherche coupées à ces dates ;
  - `phase0_index` : as_of de la configuration, argument vérifié (D-0073) ;
  - ressources vivantes datées :
    - `cache.dated` sert à l'as_of la version la plus récente au plus de lui, sinon l'ancien nom fixe, sinon la plus ancienne ; `edgar.dated_resource` la tire une fois par exécution ;
    - `discovery page` (page des Notes et liste des noms), `nport page`, `lender fetch` (page et archives des BDC Data Sets, tirées par le code, manifeste des tirages) ;
  - submissions de `lender_liabilities` et de `montages.periodic` datées sous `cache/api`, comme celles d'`edgar.Edgar` ;
  - recherches par fenêtres, résultats ajoutés à la suite des anciens : `discovery.search`, `nf_discovery.search`, `montages.search` ; `montages.replay` rejoue toutes les fenêtres ; une fenêtre déjà consignée ne se consigne plus (`discovery._log_query`) ;
  - `update` :
    - `Admission`, la file à part de la période nouvelle, dans les montages, les 6-K, le volet B et les 6-K d'Arm de SoftBank et les annonces des BDC ;
    - `previous_state` et `carry_over`, la reprise de l'exécution précédente, dans `montages.prepare` (décomptes compris), `sixk.prepare` et `sb_own.prepare` ;
  - files : `discovery.extend_units` et `nf_discovery.extend_with_prior` (unités anciennes telles quelles, nouvelles à la suite) ; `discovery prepare-frontier` prépare les unités nouvelles de la frontière ;
  - les étapes des montages qui écrivent leurs décomptes (`fetch`, `corpus`, `lab_corpus`, `backlog_corpus`, `values_corpus`) n'effacent plus ceux de la préparation (`_write_info`).

  (5) Phases 0 à 2 et catalogues des groupes, avant toute lecture (2026-10-24) :
  - Réseau : 153 requêtes, toutes en 200, aucun refus 403. Phase 0 : 62 (`company_tickers.json` et 61 listes de submissions). Index : 26. Phase 1 : 49 (`companyfacts` et archives XBRL). Phase 2 : 16.
  - Inventaire : 30 568 → 30 746 dépôts. Les 178 nouveaux sont déposés du 2026-10-08 au 2026-10-23 ; aucun ne sort, aucun ne change de classe.
    - Tranche : 8 8-K à items de la tranche (Cipher 3, Riot, Blue Owl, Meta, TeraWulf, Marvell), 3 rapports périodiques (10-K de Micron, 10-Q de Meta et de SpaceX), 2 DEF 14A (IREN, Microsoft) et leurs 2 DEFA14A.
    - Le reste : formulaires 3 et 4 (116) et 144 (20), 7 6-K (TSMC 3, SK hynix 2, ASML, Nebius), 8 8-K hors tranche, 3 13F-HR/A, 4 13G, 2 ARS, et 3 autres.
  - Fenêtres : seule leur fin change, à l'as_of. Univers attendu : 24 472 cellules.
  - Phase 1 : 788 dépôts lus ; les 7 échecs sont ceux déjà connus (amendements sans instance). Phase 2 : 2 340 documents, aucun échec.
  - Catalogues : aucune clé déjà lue ne disparaît ni ne change.
    - Tranche : 4 359 → 4 386 blocs. 26 clés nouvelles, 1 291 065 caractères. Six corps de pièces (Blue Owl, Cipher 3, Meta, Marvell), 1 193 931 caractères, ne se lisent que si leur en-tête le demande (§11.1) ; il reste 97 134 caractères d'items, d'en-têtes, d'Items 404, 4 et 9A et de la note de parties liées de SpaceX.
    - Bloc `text` : 4 692 → 4 718 blocs. 24 clés nouvelles, 135 531 caractères : notes du 10-K de Micron (9), des 10-Q de SpaceX (7) et de Meta (6), item 2.03 de Blue Owl et de TeraWulf.
  - À lire : 50 blocs, liste `upd_20261024_groups`, du plus récent au plus ancien.

  (6) Blocs de §14, avant toute lecture (2026-10-24) :
  - Réseau : 611 requêtes, aucun refus 403. Une réponse 500 de la recherche plein texte a été relancée une fois, avec succès. Par bloc : BDC Data Sets et `lender_liabilities` 225, découverte 79, piste des non-déposants 69, `form_d` 85, `foreign` 18, 6-K 20, `sb_own` 64, N-PORT 9, `ownership` 7, montages 35. Avec les phases 0 à 2, cela fait 764 requêtes à cet as_of, et le journal compte 26 347 lignes.
  - `lender` et `lender_portfolio` : la page des BDC Data Sets compte 22 archives, dont une nouvelle, `2026_09`, publiée le 2026-10-08 selon son en-tête Last-Modified. Volumes :
    - dépôts : 2 395 → 2 397 ;
    - lignes NUM : 3 465 406 → 3 466 288 ;
    - lignes SOI : 1 031 750 → 1 031 997 ;
    - positions : 746 458 → 746 616.
  - `lender_liabilities` :
    - inventaire des véhicules : 64 244 → 64 416 dépôts, aucun véhicule sans liste. 7 documents tirés sur 1 364.
    - offres de rachat : 942 → 943. Il y a 594 lectures, dont 98 corrigées.
      - Quatre sont nouvelles : Carlyle, 1 781 444 parts acceptées ; Eagle Point Trinity et Crestline, aucune part apportée ; Onex, sans résultat.
      - BIP Ventures, sans résultat jusque-là, se lit à 105 319 parts apportées et acceptées.
      - Barings se lit sur l'amendement final du 22 octobre 2026. Sa correction garde les parts apportées non chiffrées : la réduction au prorata est publiée (environ 46,84 % des parts apportées), et les 7 080 516 parts de cet amendement sont les parts acceptées.
    - annonces : 40 → 42 unités. Les deux nouvelles, les 8-K d'OTIC et d'OCIC du 2026-10-23, ne portent aucune annonce.
  - Découverte :
    - la page des Notes Data Sets, tirée à cet as_of, ne porte aucune archive nouvelle : 76 archives, dont la dernière, `2026_09`, est déjà traitée ;
    - la recherche plein texte (60 requêtes) passe de 9 390 à 9 414 résultats. Les candidats ne changent pas (3 074) ;
    - la file passe de 19 194 à 19 201 unités. Les 7 nouvelles sont des en-têtes de pièces de la passe A, de candidats classés aux rangs 123 à 2 013 : aucune n'est dans la frontière (rang 50), et elles restent non traitées. Aucun bloc nouveau.
  - Piste des non-déposants : 1 142 → 1 143 résultats (68 requêtes) ; une unité nouvelle, l'en-tête d'une pièce du 2026-10-13 qui nomme Nscale, hors règle. Aucun bloc nouveau.
  - `form_d` : 883 → 965 Form D.
    - 2 sont de la période nouvelle, parmi les véhicules candidats.
    - 80 sont anciens et portent sur des groupes ajoutés après D-0041 : Apollo 55 (deux CIK), Applied Digital 7, Dell 6, Riot 5, Blue Owl 2, Intel 2, Backblaze, Core Scientific et IREN 1 chacun. La population des groupes passe ainsi de 38 à 118 dépôts. La collecte n'avait pas été relancée à leur ajout ; elle se refait ici sur la configuration du jour.
    - Une collecte de données structurées se refait entière, comme les phases 0 à 2. Seuls les catalogues de lecture et les files gardent leur état (point 3). Les cellules que ces Form D produisent sont relevées à l'intégration.
  - `foreign` : aucune unité nouvelle.
    - Shinhan Financial Group, GCL Global Holdings et Korea Electric Power sont entrés depuis dans une paire ou un cycle ; ils ont 52 unités, toutes antérieures à l'as_of précédent.
    - Une première préparation en a construit les blocs (18 requêtes). Ces blocs ont été retirés du catalogue de la découverte, qui revient à 401 blocs. Les unités gardent leur état, « non traitées » : c'est la garde `new_period`.
    - L'inventaire retient 2 émetteurs (IREN, Nebius) et en garde 3 (`retention`), ce que la synthèse dit.
  - 6-K : 7 6-K nouveaux (TSMC 3, SK hynix 2, ASML, Nebius) et 13 pièces tirées (20 requêtes).
    - Quatre portent des fenêtres, soit 12 blocs et 43 329 caractères : TSMC 5, Nebius 3, ASML 3, SK hynix 1. Les trois autres n'en ont pas.
    - Aucune fenêtre nouvelle n'est au-delà du plafond. Le catalogue passe de 400 à 412 blocs, et les 400 anciens sont identiques.
  - `sb_own` : inventaire des déposants et 23 pièces tirées (64 requêtes en tout) ; 570 pièces et 529 en-têtes en cache. Le catalogue ne change pas : 473 blocs, identiques, aucun bloc nouveau.
  - N-PORT :
    - la page ne porte aucune archive nouvelle : 28 archives, de 2019q4 à 2026q3 ;
    - aucune archive n'est à rescanner pour SoftBank ni pour les obligations (Oracle, CoreWeave) ;
    - pour les non-cotés, le lexique se recalculait sur les entités du jour. Sa version changeait (`lx-e8610930b682` au lieu de `lx-cd6e02bb8912`), si bien que les 28 archives auraient été retirées et rescannées. Cinq ont été tirées avant l'arrêt, et les scans de trois d'entre elles (2026q1 à 2026q3) réécrits. Ces trois-là ont été retirées et rescannées sous le lexique de l'exécution précédente : empreintes et décomptes identiques. Le correctif est `frozen_lexicon`. En tout : 9 requêtes, 3,62 Go.
  - `ownership` : 125 dépôts au plan (120 13F-HR, 5 13D ou 13G), 7 requêtes.
  - Montages :
    - recherches sur la fenêtre nouvelle (32 requêtes) : `meta_hyperion` passe de 2 793 à 2 991 résultats, `galaxy_helios` de 6 254 à 6 298, `anthropic_chain` de 242 à 244. `athene_whco`, `stargate` et `sec_letters` n'en ont pas de nouveaux. Ceux de `meta_hyperion` et de `galaxy_helios` sont des relevés de portefeuille (N-PORT, 13F, N-CSR), écartés comme avant ;
    - tirages : 2 pièces (3 requêtes), deux EX-99.1 de 8-K de `anthropic_chain` (Kinetic Seas, Data443) ;
    - préparation : les 1 224 blocs anciens sont identiques, et 2 blocs s'ajoutent, ceux de ces pièces (3 230 caractères). Dans `labs_events`, ces deux pièces sont sans fenêtre ;
    - corpus, sans requête : aucun document de la période nouvelle ne nomme un terme. Le recalcul nomme des documents anciens de plus : `labs_corpus` 56, `softbank_corpus` 28, `backlog` 15, `backlog_values` 5, `labs_events` 3. Ce sont surtout des documents mis en cache depuis la préparation de ces montages, et ceux de Cerebras, ajouté depuis. Tous sont antérieurs au 2026-10-08 et restent hors du catalogue (point 3) ;
    - `labs inventory`, sans requête : 130 faits des instances (OpenAI 109, Anthropic 21) et 20 des Notes Data Sets (14 et 6). Aucun ne vient d'un dépôt de la période nouvelle.
  - Code, avant toute lecture, et 3 tests de plus (20 dans `test_d0074`) :
    - `foreign.new_period` : une unité ancienne garde son état, même si son émetteur est entré depuis dans le graphe ;
    - `foreign.retention` : un émetteur est retenu si une de ses unités sélectionnées est préparée. Il est gardé si la règle le retient sans unité préparée ;
    - `nport.frozen_lexicon` : à une exécution nouvelle, le lexique des non-cotés est celui du dernier scan de l'exécution précédente ;
    - `sb_own._header_party` : l'analyseur des en-têtes SGML s'appelait `_block`, et la fonction de même nom qui construit les blocs le masquait depuis D-0058 (3a6d650). `sb_own headers` échouait donc. Il est renommé, et sa sortie est identique.
  - À lire : 14 blocs, 46 559 caractères (12 6-K, 2 montages), liste `upd_20261024_s14`, du plus récent au plus ancien.

  (7) Lecture des blocs de §14, intégration et résultats (2026-10-24), sans sous-agent :
  - Lecture, liste `upd_20261024_s14` : 14 blocs et 16 lignes, soit 5 observations et 11 abstentions.
    - Nebius : facilité relais garantie de 3,5 Md$ signée le 17 octobre 2026 avec Citibank, N.A., avec une clause de liquidité minimale et des sûretés sur la quasi-totalité des actifs des emprunteurs (6-K du 22 octobre). Le communiqué joint la redit sans montant, pour ne pas compter deux fois la facilité. Le 6-K est furnished : l'arête est une relation.
    - ASML : initiative avec TSMC pour des photomasques de 12 pouces (High NA EUV), relation sans montant. Les états du T3 2026 sont en agrégat.
    - SK hynix : Solidigm renonce à sa levée avant introduction en bourse, sans contrepartie. TSMC : relevés de dérivés en agrégat.
    - Chaîne d'Anthropic : une compilation d'un tiers (Data443, hors champ) et un programme de partenaires (Kinetic Seas), sans arête.
    - Aucune des 161 lignes nouvelles de la mise à jour ne nomme une personne physique (citations, notes, contreparties).
  - Entités par extrait, après le premier réassemblage. Trois noms nouveaux restaient en attente :
    - « TBC » devient un alias de The Boring Company, d'après l'extrait qui le définit dans la note des participations du 10-Q de SpaceX du 2026-10-22 : « TBC - The Boring Company ("TBC") » (D-0021) ;
    - « District of Columbia Attorney General » et « participating states » (litiges de Meta) restent en attente : aucune pièce n'en affirme l'identité ;
    - « Citi », dans le communiqué de Nebius, l'était déjà ; aucune position de BDC ne nomme TBC ni The Boring Company, et l'extraction des BDC Data Sets ne se refait pas.
  - Réassemblages : le premier en 1 048 s, le second en 894 s (le mémo ne reprend rien, la configuration ayant changé).
  - Constat et correctif du rendu :
    - `delta.md` rapprochait les cellules et les contrôles des deux exécutions sur leur clé, as_of compris. À un as_of nouveau, aucune cellule ne se rapprochait : presque toutes apparaissaient et disparaissaient, et aucune valeur changée ne se lisait.
    - `_same_run` lit comme un seul « run » l'as_of de chaque exécution, et une fin de période qui lui est égale (fenêtres jusqu'à la date de coupure). Les millésimes datés de la vue `as_known` (environ 3 500 cellules) gardent leur date dans la clé.
    - Un test de plus : 21 dans `test_d0074`, 380 en tout, et ruff passe.
  - Tables, contre celles de 580e8e9 :
    - documents : 25 472 → 26 227 ; faits : 1 583 436 → 1 588 706 ;
    - observations : 30 073 → 30 234. Ce sont 161 lignes dans 62 blocs, 145 des groupes et 16 de §14 ; aucune ne disparaît ;
    - entités : 3 597 → 3 606 ;
    - liens : 11 155 → 11 195, dont 22 arêtes nouvelles et aucune disparue (commercial à montant 4, soutien de crédit 5, financement à montant 2 et en relation 11). Entre autres : achats de SpaceX à Tesla (151, 480 et 506 M$), participation de SpaceX dans The Boring Company (gain latent de 561 M$), achat de Micron à Powerchip (1,8 Md$), facilités de MUFG (Blue Owl), de Citibank (Nebius), de Bank of America (Marvell) et de Morgan Stanley Senior Funding (TeraWulf) ;
    - mesures : 188 379 → 189 234 ; contrôles : 70 269 → 70 578 ;
    - exclusions : 31 716 → 31 860.
      - `out_of_scope` + 128 : 124 Form D anciens, antérieurs à la fenêtre (le bloc `form_d` passe de 38 à 162), 3 6-K sans fenêtre et 1 de `sb_own`.
      - `not_processed` + 35 et − 24. Les entrées : les 7 unités de la découverte, hors frontière, et celle de la piste des non-déposants, hors règle ; puis 27 8-K anciens de véhicules de BDC (Blue Owl 18, MSC Income Fund 6, trois autres 1 chacun). Ces 8-K sont entrés dans la file des annonces, qui ne s'était pas recalculée depuis le 2026-10-10 ; antérieurs à l'as_of précédent, ils restent au-delà du plafond (point 3). Les sorties : 24 fenêtres de 6-K au-delà du plafond, dont le texte est celui d'un bloc déjà lu, que la clé de contenu admet (vérifié fenêtre par fenêtre).
      - `pending_entity` + 2, `financial_parties_only` + 2 (corps EX-4 de Cipher), `conflicting` + 1 (SpaceX).
  - `delta.md` :
    - événements nouveaux de l'annexe F : Meta F2 sur un trimestre ; SpaceX F1 sur un trimestre, F2 sur trois et F4 sur un. Aucun ne disparaît ;
    - valeurs changées pour des périodes déjà publiées : 130 cellules de même clé. Ce sont surtout les trimestres de 2025 de SpaceX, calculés pour la première fois grâce aux comparatifs de son 10-Q du T3 2026 (« terme manquant » → calculée). S'y ajoutent les ratios des offres de rachat de quatre véhicules de BDC et l'issue E.7 (0,5602 → 0,5595) ;
    - cellules apparues : celles des périodes closes depuis (T3 2026 de Meta et de SpaceX, exercice 2026 de Micron, clos le 3 septembre). On y trouve 148 cellules de `financed_status`, 188 de `segment_significant_expenses` et 20 de `form_d_offering_amount` : 30 offres des émetteurs du périmètre au lieu de 20 ;
    - contrôles basculés : C1 3, vers `not_testable` ; C2 1, vers `ok`.
  - Faits de la période, dans les lignes lues :
    - Meta : pénalité civile de 25 Md$ prononcée le 21 octobre 2026 dans l'affaire du procureur général du Nouveau-Mexique ; accord d'août 2026 avec 52 procureurs généraux, jusqu'à environ 18,59 Md$ ;
    - Cipher : obligations convertibles à 0,00 % de 850 M$, échéance 2032 ;
    - Blue Owl : avenant n° 4 du crédit renouvelable, porté à 3,225 Md$ ;
    - Micron : environ 134 Md$ d'obligations de prestation restantes au 3 septembre 2026 ;
    - Nebius : facilité relais de 3,5 Md$.
  - Constat, sans suite dans cette décision (aucune relecture, point 3) : neuf lignes de passes antérieures (2026-10-07), dans six blocs de Microsoft et de SpaceX, nomment une personne physique. Quatre le font dans une note, quatre dans une citation, une comme contrepartie. La règle les exclut. Leur correction est proposée à l'utilisateur. « Harbor Gates Capital, LLC » et « Musk Industries LLC » sont des sociétés.
  - Verrou de session levé en fin d'exécution. La tâche planifiée de §11.5 n'est pas créée.

- **D-0075 — En-cours publiés sous dimension et deux indicateurs des en-cours. Règles fixées avant tout changement.**
  (1) Origine : demande de l'utilisateur, le 2026-10-26, à la suite d'un échange sur les GPU achetés et pas encore en service : « Oui fais les pistes 1 et 2 ». La piste 1 consiste à lire les en-cours publiés sous dimension, la piste 2 à ajouter deux indicateurs tirés du XBRL seul. L'as_of reste le 2026-10-24. Il n'y a ni requête réseau ni lecture.

  (2) Constat, sur les tables de dca257c, avant tout changement :
  - `cip_share` (§6.2, en-cours ÷ immobilisations brutes) : 752 cellules, dont 41 calculées, pour AMD, ASML et Oracle seulement. Les 711 autres sont indéterminées, 623 au motif « concept non résolu » et 88 « non publié ». La grandeur `construction_in_progress` ne lit que l'élément `ConstructionInProgressGross`, ou `ConstructionInProgress` en IFRS, et les occurrences n'admettent que des faits sans dimension (sauf le RPO, D-0068, volet 1).
  - Les en-cours de 20 groupes sont pourtant dans `facts`. Ils y sont publiés comme membre de l'axe `us-gaap:PropertyPlantAndEquipmentByTypeAxis` d'un poste d'immobilisations brutes :
    - membres : `us-gaap:ConstructionInProgressMember` (19 groupes) ; `us-gaap:AssetUnderConstructionMember` (Alphabet, depuis 2025) ; `smci:BuildingsUnderConstructionMember` (Supermicro, libellé court « Construction in progress ») ; `nbis:AssetsNotInUseMember` (Nebius, libellé « Assets not yet in use », documenté comme « computer equipment and other assets, which are under installation ») ;
    - montants récents : Alphabet 122,8 Md$ (30 juin 2026), Meta 89,5 Md$ (30 septembre 2026), Amazon 71,7 Md$ (31 décembre 2025), SpaceX 23,7 Md$ (30 septembre 2026), CoreWeave 11,9 Md$ (30 juin 2026), Micron 11,4 Md$ (3 septembre 2026), IREN et Applied Digital 3,7 Md$ chacun, Nebius 2,4 Md$ (31 décembre 2025) ;
    - postes porteurs : le plus souvent `PropertyPlantAndEquipmentGross` ; chez Micron, Cipher, Intel et Alphabet, `PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetBeforeAccumulatedDepreciationAndAmortization`. Aucun dépôt ne publie, à une même date, deux membres admis ni un même membre sur deux postes ;
    - total du tableau : chez Meta, Hut 8, IREN, Backblaze et Amazon, les classes sont balisées sur `PropertyPlantAndEquipmentGross`, et le total sur le poste qui comprend les droits d'utilisation des locations-financement.
  - Effet sur `implied_useful_life` : la durée retire les en-cours de la base, mais seulement s'ils sont balisés sans dimension. Sinon, des actifs non amortis y restent (drapeau `land_or_cip_untagged`). Recalcul hors code sur l'exercice 2025 :
    - CoreWeave : 9,54 ans publiés, 6,98 ans sans les en-cours ;
    - Nebius : 8,85 ans publiés, environ 5,6 ans sans les actifs pas encore en service.
  - Hors de la règle, consignés sans suite :
    - les acomptes sur équipements (Applied Digital, Cipher, TeraWulf) : ce sont des avances aux fournisseurs, pas des en-cours ;
    - le matériel « not placed into service » de Micron (6,12 Md$ au 3 septembre 2026), compris dans la ligne « Equipment » et publié en note de bas de tableau ;
    - les en-cours portés par un poste net ou d'extension (Core Scientific ; Alphabet en 2019 et 2020) ;
    - Microsoft, qui ne publie aucun en-cours en XBRL ;
    - les terrains, eux aussi souvent publiés sous dimension, que la durée implicite ne retire donc pas toujours.

  (3) Règles :
  - En-cours sous dimension, grandeur `construction_in_progress`. Un fait est admis s'il remplit toutes ces conditions :
    - fait d'instance à une seule dimension, sur l'axe `us-gaap:PropertyPlantAndEquipmentByTypeAxis` ;
    - membre de la liste fermée ci-dessus (quatre membres), sur l'un des deux postes bruts (`PropertyPlantAndEquipmentGross`, ou `PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetBeforeAccumulatedDepreciationAndAmortization`) ;
    - périmètre publié et valeur présente ;
    - poste présent dans la linkbase de présentation du dépôt, pour une note ou le bilan (§8.3).

    Un dépôt qui balise `ConstructionInProgressGross` sans dimension à la même date garde ce fait. Les listes des membres et des postes sont dans `config.yaml` (`cip_dimensional`). Un membre ne s'y ajoute que par décision, sur son libellé ou sa documentation.
  - Une seule valeur par période, choisie par l'ordre total (§7.3) comme pour les autres grandeurs : la valeur d'un membre, jamais une somme de membres.
  - Dénominateur de `cip_share` : le total sans dimension, à la même date, du poste qui porte l'en-cours.
    - Pour `PropertyPlantAndEquipmentGross`, c'est `gross_depreciable_ppe`. À défaut, c'est le total du tableau, droits d'utilisation des locations-financement compris : grandeur nouvelle `ppe_and_finance_rou_gross`, élément `PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetBeforeAccumulatedDepreciationAndAmortization`, en note ou au bilan.
    - Pour un en-cours porté par ce second poste, c'est ce seul total.
    - Un en-cours sans dimension garde `gross_depreciable_ppe`, avec le même repli.
    - Le drapeau de la cellule dit le poste de l'en-cours et le total retenu.
  - `implied_useful_life` : les en-cours admis, avec ou sans dimension, se retirent du brut amortissable, comme le prévoit §6.2. Un en-cours est compris dans les immobilisations brutes quel que soit le tableau qui le porte. Le drapeau `land_or_cip_untagged` garde son sens.
  - Deux indicateurs de rang 2, trimestriels (§6.2), aux libellés neutres :
    - `cip_change_to_capex` : (en-cours en fin de trimestre − en-cours en fin du trimestre précédent) ÷ capex décaissé du trimestre. Le rapport est négatif quand les mises en service dépassent les entrées. La variation comprend aussi les acquisitions, cessions, dépréciations et reclassements, que la mesure ne sépare pas. Le drapeau dit si les deux en-cours viennent de postes différents ;
    - `capitalized_interest_to_cip` : intérêts capitalisés du trimestre ÷ moyenne des en-cours de début et de fin de trimestre. C'est un taux du trimestre, non annualisé ;
    - chacune se publie avec ses termes (numérateur et dénominateur), comme tout rapport de flux sur stock (§6.2) ;
    - motifs d'indétermination : « concept non résolu » ou « non publié » faute de terme, « période antérieure absente » faute d'en-cours au trimestre précédent, « dénominateur négatif ou nul » pour un capex ou des en-cours nuls.
  - Ni événement de l'annexe F, ni critère, ni seuil ne change, et il n'y a ni lecture ni requête. Le réassemblage et les rendus se font à l'as_of du 2026-10-24, et `delta.md` se compare aux tables de dca257c.

  (4) Code, avant tout recalcul (8b77edc) :
  - `config.yaml`, section `cip_dimensional` : l'axe, les quatre membres et les deux postes ;
  - `quantities` :
    - `cip_dimensional` remplit la table `cip_dim` avec les faits admis ;
    - `occurrences` les ajoute sous `construction_in_progress`, avec le concept du poste ;
    - grandeur nouvelle `ppe_and_finance_rou_gross` ;
  - `rank2` :
    - `cip_share_cell` : dénominateur du même poste, repli sur le total du tableau, drapeau ;
    - `cip_flows` : les deux mesures ;
    - la durée implicite garde son code et retire désormais les en-cours qu'elle reçoit ;
  - registre (deux mesures), rendu (deux lignes des tableaux trimestriels), `schema.sql` régénéré ;
  - 13 tests (`test_d0075`), 393 en tout ; ruff passe.

  (5) Réassemblage et résultats (2026-10-26) :
  - Réassemblage en 1 642 s, le mémo ne reprenant rien puisque la configuration a changé. L'étape de base y a pris 194 s. Mesurée à part, elle prend 103 s, la requête d'admission 0,1 s et la lecture des occurrences 2,1 s. L'écart avec les 894 s de D-0074 tient à la machine, comme en D-0070.
  - Faits admis : 591, de 20 groupes. La correspondance des concepts passe de 36 011 à 36 138 lignes, celles de la grandeur nouvelle.
  - `cip_share`, vue `as_known` : de 41 à 283 cellules calculées, et de 3 à 23 groupes.
    - Dernières valeurs : Cipher 70,8 %, TeraWulf 63,2 %, Applied Digital 57,0 %, Cerebras 56,0 %, Hut 8 52,7 %, IREN 47,7 %, Nebius 39,1 % (fin 2025), Oracle 31,6 %, Meta 27,4 %, CoreWeave 22,6 %, Galaxy 21,8 %, SpaceX 21,6 %, Amazon 13,4 % (fin 2025), Micron 8,5 %, NVIDIA 4,0 %.
    - Alphabet : l'en-cours est admis, mais son tableau ne publie aucun total brut qui le contienne, puisque ses actifs pas encore en service s'ajoutent après les amortissements. La part reste « non publié » depuis le 30 juin 2025.
  - `implied_useful_life`, vue `as_known` : 32 des 64 cellules calculées changent. Entre autres :
    - exercice 2025 : CoreWeave 9,54 → 6,98 ans, Nebius 8,85 → 5,71, Amazon 7,06 → 6,16, TeraWulf 11,95 → 5,31, Galaxy 27,70 → 7,45 ;
    - autres exercices : IREN 7,32 → 6,38 (clos en juin 2025), NVIDIA 4,86 → 4,65 (clos en janvier 2026), Applied Digital 18,29 → 9,72 (clos en mai 2023).
  - `cip_change_to_capex` : 226 cellules calculées, pour 17 groupes. Au dernier trimestre publié :
    - Cipher 205 %, IREN 118 %, Core Scientific 86 % (T3 2025), TeraWulf 84 %, Cerebras 74 %, AMD 62 %, SpaceX 57 %, Applied Digital 43 %, CoreWeave 36 %, Alphabet 32 %, Oracle 30 %, Meta 27 %, Micron 4 % ;
    - valeurs négatives quand les mises en service dépassent les entrées : Galaxy −298 %, Riot −41 %, Supermicro −11 %.
  - `capitalized_interest_to_cip` : 46 cellules, pour 6 groupes. Au dernier trimestre, de 0,31 % (Alphabet) à 1,63 % (TeraWulf), avec CoreWeave à 0,73 % et SpaceX à 0,66 %.
  - Contrôles : 70 578 → 70 585. Les sept nouveaux sont des C4 en `mismatch` : en-cours révisés d'un dépôt à l'autre chez Applied Digital (3), Alphabet et TeraWulf, total du tableau chez Cipher et Core Scientific. Aucun contrôle ne bascule.
  - Tables, contre celles de dca257c :
    - documents, observations, entités, liens et exclusions sont identiques ;
    - les faits aussi, sauf la colonne `model_quantity` de 452 faits, ceux de la grandeur nouvelle ;
    - mesures : 189 234 → 192 242, soit les deux mesures nouvelles, 1 504 cellules chacune.
  - `delta.md` :
    - valeurs changées pour `cip_share` (485 valeurs, 905 statuts ou motifs, sur les deux vues) et pour `implied_useful_life` (66 valeurs) ;
    - aucun événement de l'annexe F n'apparaît ni ne disparaît, et aucune arête ne change.
- **D-0076 — Composition des en-cours et des actifs pas encore en service, telle que l'écrivent les notes (piste 4). Règles fixées avant toute lecture.**
  (1) Origine : demande de l'utilisateur, le 2026-10-26 : « Oui, prépare la piste 4 ». C'est la quatrième piste de l'échange sur les GPU achetés et pas encore en service (D-0075, point 1) : lire dans le texte des notes ce que les tableaux balisés ne disent pas, c'est-à-dire quelle part des en-cours, ou des actifs pas encore en service, est du matériel informatique (serveurs, GPU) plutôt que des bâtiments. Elle vise aussi Microsoft, qui ne publie aucun en-cours en XBRL (D-0075, point 2), et la composition des en-cours d'Alphabet. L'as_of reste le 2026-10-24. Il n'y a aucune requête réseau.

  (2) Constat, compté sans aucune valeur et sans lecture, sur le cache et les tables de 52a0873 :
  - les blocs `lever_note` déjà lus (notes d'immobilisations et d'estimations) ne suffisent pas. Alphabet, NVIDIA et Intel publient leur tableau d'immobilisations dans une note de compléments du bilan (« Supplemental Financial Statement Information », « Balance Sheet Components », « Other Financial Statement Details »), que le catalogue ne sert pas. Le corpus est donc fait de toutes les notes des rapports périodiques ;
  - corpus : 788 instances de rapports périodiques (10-K, 10-KT, 10-Q, 20-F et leurs amendements), 12 642 notes (blocs de texte des rôles de note, sans dimension). 532 notes, de 27 groupes, nomment un terme du lexique (point 4) ;
  - Microsoft et Dell : aucun terme du lexique dans aucune note. Hors des notes, sur les octets des documents principaux de leurs 76 rapports périodiques, Dell n'en a aucun et Microsoft le seul « not deployed », une fois par rapport (36), hors de toute note. Microsoft ne publie donc ni en-cours ni actifs pas encore en service dans ses états, ni en XBRL ni en texte. AMD, Marvell, Cerebras et TeraWulf ne nomment leurs en-cours que comme ligne nue d'un tableau, déjà balisée ;
  - fenêtres selon les règles du point 4 : 432, dont 397 textes distincts (290 502 caractères). 286 sont déjà dans un bloc lu du même dépôt (213 519 caractères), 111 jamais lues (76 983). Par groupe (textes distincts, caractères, déjà lus) : Akamai 20, 35 918, 0 ; Amazon 6, 6 724, 4 ; Applied Digital 9, 7 530, 8 ; ASML 21, 8 855, 8 ; Broadcom 8, 24 257, 8 ; Backblaze 6, 3 890, 6 ; Cipher 29, 36 029, 29 ; Core Scientific 23, 11 887, 20 ; CoreWeave 1, 1 181, 1 ; Galaxy 16, 10 686, 16 ; Alphabet 15, 10 943, 8 ; Hut 8 9, 11 218, 8 ; Intel 9, 15 808, 1 ; IREN 8, 4 245, 5 ; Meta 44, 39 721, 43 ; Micron 64, 19 850, 64 ; Nebius 10, 2 800, 8 ; NVIDIA 9, 3 925, 0 ; Oracle 1, 1 162, 1 ; Riot 28, 21 460, 23 ; Supermicro 47, 7 117, 11 ; SpaceX 2, 1 906, 2 ; TSMC 12, 3 390, 12 ;
  - écartées par ces règles : les fenêtres faites de seules lignes d'en-cours nues (leur montant est balisé) ; les 52 fenêtres que seul « under construction » qualifiait (78 001 caractères), presque toutes dans les notes d'engagements, de baux ou de présentation (projets et sites loués en construction, qui ne sont pas des actifs au bilan) : le terme sort du lexique, sauf dans « assets under construction » ;
  - variantes relevées avant de fixer le lexique : « construction in process » (NVIDIA, TeraWulf, Backblaze), « not ready for … use » (Alphabet), « pending deployment » et « undeployed » (Core Scientific, Backblaze) ;
  - hors corpus : les 6-K des émetteurs étrangers. Ce sont des communiqués et des rapports sans notes balisées, aux paragraphes sans structure (ASML 20 fenêtres de 208 431 caractères, IREN 22 de 147 935, Nebius 13 de 5 582, TSMC 88 de 26 287). Leurs rapports annuels (20-F) sont dans le corpus. Sont aussi hors corpus le texte des rapports périodiques hors des notes (rapport de gestion) et les pièces EX-99.

  (3) Règles générales :
  - lignes descriptives, sans famille ni arête ;
  - aucune arithmétique sur un chiffre lu dans le texte : ni somme, ni part, ni conversion. Un montant écrit se publie tel quel, à côté de l'en-cours balisé à la même date, jamais divisé par lui ;
  - rien de ce qui est lu n'entre dans `cip_share`, `implied_useful_life` ou les indicateurs de D-0075, ni dans les annexes E et F, les mesures de financement, l'exposition, les paires, les cycles ou les conclusions.

  (4) Montage `ppe_components`, source `ppe_notes` :
  - corpus :
    - les notes des rapports périodiques à instance XBRL (10-K, 10-KT, 10-Q, 20-F et amendements) des groupes de `config.yaml`, telles que le catalogue `text` les normalise : blocs de texte sans dimension des rôles de note ;
    - les notes des jeux d'états financiers des documents d'enregistrement qui tiennent lieu de rapports périodiques (`registration_text`, D-0057, point 14), toutes notes comprises ;
  - lexique, sans égard à la casse :
    - en-cours : « construction in progress » ou « construction in process » (tirets admis), « constructions in progress », « assets under construction » ;
    - pas en service : « not (yet) (been) placed / put in / into service, use ou operation », « not (yet) in / into service ou use », « not (yet) available / ready for (its / their) (intended) use » ;
    - installation : « under installation », « pending installation », « awaiting installation », « not yet installed », « yet to be installed » ;
    - déploiement : « pending / awaiting / prior to / before (its / their) deployment », « not (yet) (been) deployed », « undeployed » ;
    - fournisseurs : « stored / held / located / warehoused by / at / with (our / its / the) (third-party) suppliers, vendors ou manufacturers » ;
    - en transit : « machinery / equipment / miner(s) / server(s) in transit » ;
  - paragraphe qualifiant : il nomme un terme du lexique. Renvois :
    - une ligne de tableau qualifiante dont la première cellule porte une marque (« (1) », « (a) », « * », « [1] ») amène le premier renvoi qui la suit sous la même marque : un paragraphe hors tableau ouvert par elle, ou une ligne dont la première cellule n'est qu'elle ;
    - un paragraphe qualifiant ouvert par une marque amène la ligne de tableau la plus proche avant lui dont la première cellule la porte ;
    - le paragraphe amené qualifie à son tour ;
  - fenêtre : un paragraphe de part et d'autre de chaque paragraphe qualifiant, fondues quand elles se touchent ;
  - non servie : une fenêtre dont tous les paragraphes qualifiants sont des lignes de tableau dont la première cellule, marques ôtées, n'est que le terme d'en-cours (suivi au plus de « net » ou « gross ») : le montant est balisé et la ligne ne décrit rien. Elle est comptée dans les décomptes du montage, sans ligne d'exclusion ;
  - faits candidats : les faits d'instance du dépôt, numériques, non nuls, à une date (instant), dont le concept figure dans un rôle de détail ou de tableau de la note (même titre que le rôle de la note, avant « (Details) », « (Tables) » ou « - »). Le lecteur voit ceux dont la valeur paraît dans le texte (D-0017) ;
  - un texte distinct se lit une fois. Un texte qui est déjà un bloc d'un autre catalogue ou montage reçoit en tête une ligne qui le nomme, pour avoir sa propre clé (D-0068, point 15) ;
  - ordre : des dépôts les plus anciens aux plus récents ;
  - régimes :
    - lecture complète d'une fenêtre jamais lue : codage habituel, plus les lignes de composante ;
    - lecture complémentaire d'une fenêtre dont chaque paragraphe qualifiant est dans un bloc lu du même dépôt : seules s'écrivent des lignes de composante, sinon une abstention `duplicate_of_other_block` ;
  - plafond : 2 000 unités, au-dessus du volume : tout se lit ;
  - niveau de preuve : celui des notes du catalogue `text` (10-K, 10-KT et 20-F : `filed`, `audited`, A ; 10-Q : `filed`, `reviewed`, B) ; pour un document d'enregistrement, l'assurance de son jeu de notes ;
  - date du bloc (`period_end`) : la date de fin de période du rapport ;
  - montage nouveau : il se prépare sur toute sa période, y compris dans une exécution nouvelle. La règle de D-0074 (point 3 : les blocs de l'exécution précédente restent tels quels et seuls s'ajoutent ceux des dépôts de la période nouvelle) ne vaut que pour un montage qui figurait au catalogue de l'exécution précédente. Précision consignée avant de coder : sans elle, un montage nouveau ne recevrait que les dépôts postérieurs au 2026-10-07.

  (5) Ligne de composante, descriptive, note finie par « ligne de composante (D-0076) » :
  - `asset_component`, ce que le texte nomme, jamais déduit :
    - `it_equipment` : serveurs, équipements de réseau, GPU, matériel informatique ;
    - `mining_equipment` : machines de minage ;
    - `manufacturing_equipment` : outils et machines de production ;
    - `facilities` : bâtiments, centres de données, installations, aménagements ;
    - `software` : logiciels ;
    - `land` : terrains ;
    - `unspecified` : le texte ne dit pas la nature (« equipment », « assets », « AI infrastructure », « data center equipment », « network infrastructure ») ;
  - `asset_state`, ce qui le tient hors service, tel qu'écrit :
    - `not_in_service` : pas encore mis en service, pas en usage, en installation ou en attente d'installation, pas déployé ;
    - `under_construction` : en construction ou en développement, en-cours ;
    - `at_suppliers` : stocké ou détenu chez des fournisseurs ;
    - `in_transit` : en transit ;
    - `prepaid` : acompte, paiement d'avance ou avance pour un actif pas encore reçu ;
    - `unspecified` ;
  - `component_of`, le poste qui le porte, tel qu'écrit :
    - `construction_in_progress` : en-cours, ou son équivalent dans le tableau (« assets under construction », « assets not yet in use » de Nebius, « equipment under installation and construction in progress » de TSMC) ;
    - `ppe_class` : une autre classe du tableau d'immobilisations (« Equipment », « Servers »…) ;
    - `property_and_equipment` : les immobilisations entières, brutes ou nettes ;
    - `other_assets` : un autre poste du bilan (acomptes, autres actifs) ;
    - `unspecified` ;
  - `component_statement` :
    - `amount` : le montant de la composante à une date ;
    - `primarily` : le poste se compose surtout de la composante, une ligne par composante nommée ;
    - `includes` : le poste la comprend, sans montant ni prépondérance ;
  - montant : champs habituels (montant, unité, devise, qualificatif, origine) pour `amount`, `tagged_reference` quand un fait candidat a cette valeur à cette date ; aucun montant pour `primarily` et `includes` ;
  - `period_end` : la date de l'énoncé, telle qu'écrite, sinon la date de fin de période du bloc ; exigée. Un énoncé à deux dates fait deux lignes ;
  - chaque fenêtre se lit seule, comparatifs compris : le code ne garde qu'une ligne par clé (point 6) ;
  - contrôles au chargement : la citation contient un mot de la composante (`it_equipment` : server, network, GPU, computer, compute, IT, information technology, hardware ; `mining_equipment` : miner, mining, ASIC ; `manufacturing_equipment` : tool, machinery, manufacturing, production, fab ; `facilities` : building, data center, datacenter, facility, facilities, leasehold, site, campus, infrastructure ; `software` : software ; `land` : land) et un mot de l'état (`not_in_service` : service, use, install, deploy, operation, ready ; `under_construction` : construct, build, develop, progress, process ; `at_suppliers` : supplier, vendor, manufacturer ; `in_transit` : transit ; `prepaid` : deposit, prepa, advance) ; rien pour `unspecified` ;
  - données personnelles : aucun nom de personne physique.

  (6) Mesure `ppe_component_disclosed` (rang 2, §6.2, à une date), descriptive, deux termes :
  - terme `component` : une cellule par groupe, date et clé (poste, composante, état et énoncé, `breakdown_key`), de deux vues : `as_known`, la ligne du premier dépôt qui écrit la clé à cette date ; `revised`, celle du dernier. Valeur : le montant écrit pour `amount`, avec son unité, sa devise et son origine ; pour `primarily` et `includes`, aucune valeur et l'énoncé en texte. Drapeaux : la citation et les observations ;
  - terme `cip_tagged` : à chaque groupe et date qui ont une ligne, l'en-cours balisé à cette date (grandeur `construction_in_progress`), connu à la date de la première ligne (`as_known`) ou à l'as_of (`revised`), son fait en lignée ; sinon indéterminé, avec son motif. Il ne sert qu'à l'affichage, à côté des composantes. Précision consignée en codant, avant toute lecture : en drapeau, ce nombre aurait été publié sans cellule ni lignée ;
  - aucune somme, aucune part, aucune conversion entre devises ; une ligne de niveau E n'entre pas.

  (7) Champs et registre : `asset_component`, `asset_state`, `component_of` et `component_statement` (registre, lecteur, chargement, `schema.sql`) ; la mesure `ppe_component_disclosed`. Contrôles du lecteur : une ligne de composante porte ses quatre champs (`unspecified` admis) et sa date ; elle est descriptive (sans famille) ; un montant pour `amount`, aucun pour les autres énoncés.

  (8) Rendus : dans la synthèse, section nouvelle « Composition des en-cours, telle qu'écrite (D-0076) », après le carnet contracté. Pour chaque groupe qui a des lignes, à sa dernière date : l'en-cours balisé, puis chaque composante (poste, état, énoncé, montant écrit, pièce). Ensuite, les groupes sans aucune ligne, avec leur motif : aucun terme dans les notes (Microsoft, Dell…), en-cours en ligne nue seulement (AMD…), ou fenêtres lues sans composante écrite. Le détail par date va dans `series.md`.

  (9) Réseau : aucun, tout est en cache. Données personnelles : aucune personne physique n'est citée.

  (10) Code avant tout traitement : source `ppe_notes` (corpus, renvois, fenêtres, faits candidats), montage dans `config.yaml`, préparation d'un montage nouveau, champs et contrôles, mesure, rendus, tests.

  (11) Ordre et commits : règles, configuration, code et tests ; montage préparé et volume consigné avant lecture ; lecture par lots, sans sous-agent ; intégration (réassemblage, rendus, résultats, tests), commit, push, rapport.

  (12) Limites connues avant lecture :
  - Microsoft et Dell n'écrivent rien : leur composition reste inconnue ;
  - beaucoup d'émetteurs ne publient que le total des en-cours : le texte ne dit la composition que si l'émetteur choisit de l'écrire ;
  - un énoncé « surtout » ou « comprend » ne pèse rien, et un montant écrit n'est jamais rapporté à un total ;
  - une fenêtre d'un paragraphe de part et d'autre peut manquer un énoncé plus éloigné ; les renvois ne se rattachent que par leur marque ;
  - les 6-K ne sont pas lus : la composition trimestrielle des émetteurs étrangers n'est connue que par leurs rapports annuels.

  (13) Code, consigné avant la préparation du montage et toute lecture :
  - module `ppe_notes` : corpus (notes des instances XBRL et de `registration_text`), renvois, fenêtres, lignes d'en-cours nues, faits candidats, niveau de preuve (celui du registre des documents pour un rapport périodique, celui du jeu de notes pour un document d'enregistrement), contrôles des lignes de composante, mesure ;
  - `montages` : source `ppe_notes`. Un montage nouveau se prépare sur toute sa période, sans état copié ni report de ses décomptes. Il est nouveau s'il n'a aucun bloc au catalogue de l'exécution précédente et que ses décomptes manquent, ou portent l'as_of courant comme première préparation (`first_as_of`) ;
  - champs et registre, `schema.sql` régénéré ; mesure dans l'assemblage, décomptes par groupe dans les statistiques de l'assemblage (point 8) ; rendus de la synthèse et de `series.md` ;
  - configuration : montage `ppe_components` (lexique, fenêtre, plafond, niveau `registry`) ;
  - 21 tests (`test_d0076`), 414 en tout ; ruff passe.

  (14) Volume du montage `ppe_components`, consigné le 2026-10-26 avant toute lecture :
  - corpus : 12 911 notes, dont 342 avec au moins une fenêtre servie ; 288 fenêtres de seules lignes d'en-cours nues, non servies ;
  - fenêtres : 448, dont 413 textes distincts (35 doublons) ; aucune au-delà du plafond, aucune ligne de tête (point 4) ;
  - 413 blocs, 294 502 caractères : lecture complète 112 (78 103 caractères), complémentaire 301 (216 399) ;
  - par niveau : A 182 (10-K, 10-KT, 20-F, notes auditées du 424B4 de SK hynix), B 231 (10-Q) ; dépôts du 2016-11-07 au 2026-10-22 ;
  - par groupe (blocs, caractères, en lecture complémentaire) : Akamai 20, 35 918, 0 ; Amazon 10, 7 765, 8 ; Applied Digital 9, 7 530, 8 ; ASML 21, 8 855, 8 ; Broadcom 8, 24 257, 8 ; Backblaze 6, 3 890, 6 ; Cipher 29, 36 029, 29 ; Core Scientific 23, 11 887, 20 ; CoreWeave 1, 1 181, 1 ; Galaxy 16, 10 686, 16 ; Alphabet 15, 10 943, 8 ; Hut 8 9, 11 218, 8 ; Intel 9, 15 808, 1 ; IREN 8, 4 245, 5 ; Meta 44, 39 721, 43 ; Micron 72, 21 056, 72 ; Nebius 10, 2 800, 8 ; NVIDIA 9, 3 925, 0 ; Oracle 1, 1 162, 1 ; Riot 28, 21 460, 23 ; SK hynix 4, 1 753, 3 ; Supermicro 47, 7 117, 11 ; SpaceX 2, 1 906, 2 ; TSMC 12, 3 390, 12. L'écart avec le constat (397 textes, point 2) tient aux rôles de note lus dans les linkbases au lieu de la table `pres`, et aux notes du 424B4 de SK hynix ;
  - file de lecture : `work/lists/ppe_components.txt`, des plus anciens aux plus récents ; passe `2026-10-26T16:00:00Z` à l'as_of du 2026-10-24 ; lecture par lots, sans sous-agent.

  (15) Amendement consigné le 2026-10-26 pendant la lecture, après 37 blocs lus et avant tout calcul :
  - constat de lecture : une note peut écrire plusieurs montants d'une même composante à la même date, un par classe du tableau. Ainsi ASML (20-F de 2018) écrit les actifs en construction de « land and buildings » et de « leasehold improvements », deux classes de bâtiments et installations. Avec la clé du point 6, la seconde ligne effacerait la première ;
  - règle : chaque ligne porte alors la classe telle qu'écrite (`instrument_key`), qui entre dans la clé de la cellule (`breakdown_key`). Elle s'écrit en minuscules, sous le libellé du premier dépôt qui l'écrit, pour qu'une variante de rédaction d'un exercice à l'autre (« Furniture, fixtures and other » pour « furniture, fixtures and other equipment ») ne coupe pas la série ; la variante va dans la note de la ligne. Les montants ne s'additionnent jamais. Sans classe écrite, la clé ne change pas.

  (16) Second amendement, consigné le 2026-10-26 pendant la lecture, après 270 blocs lus et avant tout calcul :
  - constat de lecture : Backblaze écrit, dans le renvoi de sa ligne d'en-cours, « hard drives not yet deployed » (10-K de 2024), puis « primarily comprised of hard drives that are not yet deployed » (10-Q de 2025). Ce sont des disques de stockage, du matériel informatique au sens du point 5, mais la liste des mots du contrôle n'en contient aucun ;
  - règle : les mots de `it_equipment` s'étendent à « hard drive » et « disk drive », au singulier comme au pluriel. Rien d'autre ne change. Aucune ligne déjà lue n'est touchée : aucune n'a été refusée ni codée autrement pour ce motif.
  - ajout consigné après 312 blocs lus, avant de l'appliquer : un montant d'en-cours écrit pour une seule entité consolidée (Intel : « construction in progress assets » d'Arizona SCIP, entité à intérêt variable) porte le nom de l'entité tel qu'écrit dans `instrument_key`, comme une classe du point 15. Sans cela, la cellule se lirait comme l'en-cours du groupe entier.
