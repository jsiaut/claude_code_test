# Guide de lecture du bloc `text` (§14, §7.4)

Ce guide s'adresse à qui lit les blocs du bloc `text` : notes d'investissements, de dette, de
baux et d'engagements, paragraphes sur les clients, items 2.01 et 2.03 des 8-K, corps des
pièces EX-10 arrêtés à leur en-tête au premier passage. Il reprend les règles de §7.4 et les conventions du premier passage.
Rien d'autre que ce que dit le bloc : aucun chiffre de mémoire, aucune connaissance extérieure,
aucune arithmétique.

## 1. Procédure

Depuis `/home/user/claude_code_test`, avec la liste de blocs qui t'est confiée (`LOT`) :

```
python3 -m pipeline.reader next --list work/lists/LOT.txt
```

- Le bloc arrive avec un en-tête (clé de contenu, groupe, accession, formulaire, note, période),
  les faits candidats dont la valeur paraît dans le texte, puis le texte.
- `### SUITE` : le bloc est servi en morceaux ; relance `next --list ...` jusqu'à
  `### FIN DU BLOC` avant de rendre les lignes du bloc entier.
- Écris les lignes du bloc (une ligne JSON par observation ou abstention) dans
  `work/tmp/lines_LOT.jsonl` (écrase le fichier à chaque bloc), puis :

```
python3 -m pipeline.reader submit CLE_DE_CONTENU work/tmp/lines_LOT.jsonl --list work/lists/LOT.txt
```

- Le code renvoie les erreurs de schéma ou de sémantique (citation introuvable mot pour mot,
  contrepartie absente du bloc, montant différent du fait candidat, montant balisé déclaré
  `narrative_only`…). Corrige les lignes refusées et soumets de nouveau, une fois. S'il reste
  des erreurs, soumets avec `--final` : les lignes valides sont écrites, les autres gardées
  à part comme rejets.
- `FILE VIDE` : ton lot est fini.
- Au moins une ligne par bloc. Ne saute aucun bloc, ne relis jamais un bloc déjà soumis.

## 2. Format d'une ligne

Un objet JSON par ligne. `kind` vaut `observation` ou `abstention`. Champs permis (tout autre
champ est refusé) :

| Champ | Valeur |
| --- | --- |
| `kind` | `observation`, `abstention` |
| `abstention_reason` | `no_relevant_content`, `boilerplate_no_event`, `financial_parties_only`, `no_named_counterparty`, `no_amount`, `illegible`, `out_of_scope_content`, `duplicate_of_other_block`, `cannot_describe_in_schema` |
| `quote` | extrait copié mot pour mot du texte du bloc (obligatoire pour une observation ; une phrase ou un fragment, au plus ~400 caractères, sans ellipse ni retouche) |
| `counterparty_name` | nom de la contrepartie tel qu'écrit dans le bloc |
| `counterparty_evidence` | `named`, `derivable`, `anonymous` |
| `derivation_method` | `contract_parties`, `dimension_member_label`, `exact_amount_match`, `explicit_cross_reference` (obligatoire si `derivable`) |
| `payer`, `payee` | partie qui fournit la ressource, partie qui la reçoit (noms tels qu'écrits) |
| `amount`, `amount_lower`, `amount_upper` | nombre décimal en unités (« $2.5 billion » → `2500000000` ; « 12% » → `0.12`) |
| `unit` | `USD` (ou autre code ISO), `pure` pour un pourcentage, `shares` |
| `currency` | code ISO 4217 si monétaire (`USD`) |
| `amount_nature` | `revenue_recognized_gross`, `revenue_recognized_net`, `purchase_expensed`, `purchase_capitalized`, `purchase_unspecified`, `prepayment`, `commitment_unexecuted`, `distributor_sale`, `management_estimate`, `financing_cash`, `financing_noncash`, `investment_carrying_amount`, `fair_value`, `guarantee_amount`, `lease_payment`, `fee`, `interest`, `consideration_payable_to_customer`, `noncash_consideration_received`, `capacity_commitment`, `other` |
| `amount_origin` | `tagged_reference` (le montant est la valeur d'un fait candidat du bloc ; alors `candidate_fact_key` obligatoire) ou `narrative_only` (montant écrit seulement dans le texte) |
| `amount_qualifier` | `exact`, `approximately`, `at_least`, `more_than`, `up_to`, `at_most`, `range` (`range` exige `amount_lower` et `amount_upper`) |
| `candidate_fact_key` | clé du fait candidat (première colonne de la liste des faits) |
| `period_start`, `period_end`, `event_date` | `AAAA-MM-JJ` ; `period_label` : libellé d'origine d'une échéance (« remainder of fiscal 2026 ») |
| `stage` | `intent_non_binding`, `signed`, `available`, `drawn_or_paid`, `delivered`, `recognized`, `settled`, `terminated` |
| `event_type` | `commitment`, `signing`, `availability`, `drawdown`, `funding`, `secondary_purchase`, `delivery`, `recognition`, `repayment`, `conversion`, `amendment`, `expiry`, `guarantee_call`, `payment`, `purchase`, `commencement`, `impairment`, `observable_price_adjustment`, `measurement_change`, `disposal`, `termination`, `default`, `acceleration`, `noncash_contribution`, `warrant_vesting` |
| `instrument_key` | clé stable de l'instrument : `groupe:description_courte` en minuscules (`crwv:ddtl_3_0`, `msft:openai_investment`, `orcl:ampere_investments`) ; la même pour toutes les lignes qui décrivent le même instrument, d'un bloc à l'autre |
| `family` | `financing`, `credit_support`, `commercial`, `customer_consideration` |
| `edge_type` | voir §3 ci-dessous |
| `link_category` | `L1` à `L5` (pièce qui lie financement et achats, rare) |
| `exposure_block` | `recognized_liabilities`, `contractual_outflows`, `contingent_obligations`, `exposed_assets` |
| `category_id` | `debt`, `lease_liability`, `financing_obligation`, `supplier_finance_program`, `earnout`, `derivative_credit_support`, `debt_maturity`, `lease_operating_maturity`, `lease_finance_maturity`, `lease_not_commenced`, `purchase_obligation`, `purchase_obligation_supplier_financing`, `take_or_pay`, `uncalled_commitment`, `jv_funding_commitment`, `construction_commitment`, `power_purchase_agreement`, `guarantee`, `vie_unconsolidated`, `standby_lc`, `capacity_backstop`, `receivables_transferred`, `indemnification`, `loss_contingency`, `equity_investment`, `loan_receivable`, `other` |
| `measurement_basis` | `carrying_amount`, `principal`, `undiscounted`, `discounted`, `fair_value`, `cost`, `commitment_cap`, `maximum_exposure`, `notional`, `initial_cap`, `outstanding_balance`, `equity_method` |
| `component_kind` | `principal`, `interest`, `lease_payment`, `purchase`, `minimum_purchase`, `capacity_fee`, `termination_payment`, `guarantee_cap`, `residual_value_guarantee`, `support_commitment_contractual`, `support_noncontractual`, `interest_held`, `other` |
| `conditionality` | `firm`, `conditional`, `optional` ; toute composante conditionnelle porte `trigger_description`, `trigger_occurred` (`yes`, `no`, `unknown` ; `yes` seulement si un dépôt constate l'événement) et, s'il est nommé, `ultimate_obligor` |
| `seniority` | `senior_secured`, `senior_unsecured`, `subordinated`, `unknown` |
| `recourse` | `full_recourse`, `limited_recourse`, `non_recourse`, `unknown` |
| `is_ring_fenced`, `redacted`, `judgment_sensitive` | booléens |
| `signal` + `signal_present` | `material_weakness`, `going_concern`, `covenant_amendment`, `covenant_waiver`, `covenant_breach`, `capacity_contract_termination`, `auditor_change`, `nonreliance`, `pledged_assets`, `contract_termination_other` ; `signal_present` booléen obligatoire |
| `consolidation_treatment` | `parent`, `consolidated_subsidiary`, `vie_consolidated`, `vie_unconsolidated`, `equity_method`, `investment_only`, `undetermined` |
| `party_role` | rôle d'une partie nommée (`filer`, `filer_group`, `lender`, `administrative_agent`, `borrower`, `guarantor`, `lessor`, `customer`, `supplier`, `investee`, `holder`…) |
| `party_is_financial_institution` | booléen |
| `exhibit_title` | titre exact de la pièce tel qu'écrit dans le bloc |
| `note` | commentaire libre en français : ce que la citation ne dit pas seule (contexte, échéance, autre période) |

## 3. Orientation et familles (§3.1, D-0015)

`payer` fournit la ressource, `payee` la reçoit :

| `family` | `payer` → `payee` | `edge_type` |
| --- | --- | --- |
| `financing` | financeur → financé (investisseur → participation ; prêteur → emprunteur ; bailleur → preneur en location-financement) | `equity_primary`, `convertible_or_safe`, `loan_or_facility`, `vendor_credit`, `noncash_investment`, `lease_financing` |
| `credit_support` | garant → obligé soutenu | `guarantee`, `backstop`, `residual_value_guarantee`, `credit_enhancement` |
| `commercial` | client → fournisseur | `revenue_recognized`, `purchase`, `purchase_commitment`, `capacity_lease`, `prepayment` |
| `customer_consideration` | fournisseur → client | `equity_or_warrants_to_customer`, `credits_to_customer`, `cash_incentive_to_customer` |

- Un remboursement, un loyer ou des intérêts payés sur un instrument déjà décrit suivent le sens
  de la trésorerie, sans `family` ni `edge_type`, avec le même `instrument_key`.
- `vendor_credit` exige une créance de financement sur un client nommé, une composante de
  financement significative publiée, une location-vente ou un délai de plus de 12 mois.
- Un bail passé avec le fournisseur du service est un `capacity_lease` (famille `commercial`).
- Un contrat prouve un plafond, pas un versement : un engagement non tiré a `stage` `signed` ou
  `available` ; un versement constaté `drawn_or_paid` ; un montant au bilan `recognized`.

## 4. Contrepartie (§2.4)

- `named` : le bloc écrit le nom. `derivable` : seulement par les quatre méthodes du tableau.
  `anonymous` : « un client », « une institution financière », « certains fournisseurs ».
- Un « client A » reste anonyme, même si tu crois le reconnaître. Jamais de nom deviné.
- `counterparty_name` s'écrit comme dans le bloc (le validateur le cherche dans le texte).
- Une banque, un agent administratif, un fiduciaire ou un fonds de crédit est un établissement
  financier (`party_is_financial_institution: true`).

## 5. Montants (§7.4)

- Le montant en unités, signe positif, sans arithmétique : un total que le texte n'écrit pas ne
  se calcule pas. Un montant « in millions » d'un tableau se multiplie par l'échelle annoncée
  par le tableau ou le texte (c'est une lecture d'échelle, pas une arithmétique).
- Si un fait candidat a exactement la même valeur (en valeur absolue) et la même date (la fin de
  période de la ligne, ou sa date d'événement comprise dans la période du fait), l'origine est
  `tagged_reference` avec sa clé ; sinon `narrative_only`. Un fait d'une autre date ou d'une
  autre nature ne se cite pas parce que le nombre coïncide.
- « up to » → `up_to` ; « approximately » → `approximately` ; « at least » → `at_least`.
- Période : `period_start` / `period_end` pour un flux, `period_end` seul pour un solde à une
  date, `event_date` pour un événement daté. Mets-les dès qu'ils sont déterminables.
- Un jour que le texte n'écrit pas ne se prend pas dans un fait balisé. Un mois ou une année
  écrits (« In May 2023 », « In 2024 ») donnent une période sur ce mois ou cette année
  (`period_start` / `period_end`), pas une `event_date` ; une date seulement relative (« upon
  completion of the merger ») reste vide, avec le texte dans `note`. Un total balisé
  (remboursements de l'exercice, par exemple) ne s'attribue pas à un instrument que le texte ne
  chiffre pas, même si les valeurs coïncident.

## 6. Ce qu'on cherche, par type de bloc

**Notes d'investissements (`investment_note`).** Participations, prêts, obligations
convertibles, SAFE, bons de souscription détenus dans une entité **nommée** : une observation
`financing` par instrument et par date de bilan (investisseur → participation), avec
`amount_nature` `investment_carrying_amount` ou `fair_value`, `measurement_basis`,
`exposure_block` `exposed_assets`, `category_id` `equity_investment` ou `loan_receivable`,
`consolidation_treatment` (`equity_method`, `investment_only`…), `stage` `recognized`,
`event_type` `recognition`. Un nouvel investissement de la période : `event_type` `funding`,
`amount_nature` `financing_cash`, `stage` `drawn_or_paid`. Engagement d'investir non versé :
`stage` `signed`, `event_type` `commitment`, `exposure_block` `contractual_outflows`,
`category_id` `uncalled_commitment`. Réévaluation, dépréciation, cession, conversion :
`event_type` `measurement_change`, `impairment`, `disposal`, `conversion`. Les totaux anonymes
(« non-marketable equity securities ») sont déjà balisés : pas de ligne, sauf s'ils nomment une
entité.

**Notes de dette (`debt_note`).** Instruments nouveaux ou remboursés (`financing`,
`loan_or_facility` ou `convertible_or_safe`, prêteur → groupe ; le prêteur est souvent anonyme
ou une banque), facilités disponibles (`stage` `available`, `measurement_basis`
`commitment_cap`), financements de matériel ou de fournisseur nommés (`vendor_credit` si les
conditions de §3 sont remplies), garanties (`credit_support`), et surtout les **signaux** :
`covenant_amendment`, `covenant_waiver`, `covenant_breach` (avec `signal_present` true ou
false selon ce que dit le texte : « we were in compliance with all covenants » →
`covenant_breach` false), `pledged_assets` (actifs nantis, matériel en garantie →
true). Les échéanciers balisés ne se recopient pas.

**Notes de baux (`lease_note`).** Bailleurs ou preneurs nommés ; baux signés non commencés
(`exposure_block` `contractual_outflows`, `category_id` `lease_not_commenced`, montant non
actualisé, `period_label` des dates de commencement) ; garanties de valeur résiduelle ;
cessions-bail (`financing_obligation`, `judgment_sensitive` si le traitement dépend d'un
jugement) ; baux de capacité de centres de données avec un fournisseur nommé
(`commercial` / `capacity_lease`, client → bailleur).

**Notes d'engagements (`commitments_note`).** Obligations d'achat avec un fournisseur nommé
(`commercial` / `purchase_commitment`, client → fournisseur, `stage` `signed`,
`category_id` `purchase_obligation`, `component_kind`, `conditionality`), engagements de
capacité (`capacity_commitment`), contrats d'électricité, garanties données
(`credit_support`, `category_id` `guarantee`, plafond en `maximum_exposure`), engagements
envers des coentreprises ou des fonds (`jv_funding_commitment`, `uncalled_commitment`). Les
litiges sans montant ni contrepartie de la chaîne : abstention `out_of_scope_content` ; un
litige chiffré se note `loss_contingency` seulement s'il porte un montant.

**Paragraphes sur les clients (`concentration_text`).** C'est ici qu'un client anonyme peut être
nommé. Si le texte nomme le client qui porte une part publiée (« Microsoft accounted for 62% of
our revenue »), une observation `commercial` / `revenue_recognized`, client → groupe,
`counterparty_evidence` `named`, `amount` `0.62`, `unit` `pure`, `amount_nature`
`revenue_recognized_gross`, période de l'exercice ou du trimestre, et `tagged_reference` si la
part est un fait candidat (sinon `narrative_only`). Si le texte ne nomme personne : abstention
`no_named_counterparty`.

**Items 2.01 et 2.03 des 8-K.** 2.01 : achèvement d'une acquisition ou d'une cession — nomme
l'entité acquise ou cédée, la date, le prix ; une ligne avec `consolidation_treatment`
`consolidated_subsidiary` (acquisition achevée) et une citation qui affirme l'appartenance
(« became a wholly owned subsidiary »), `event_date` à la date d'achèvement, sans `family` ;
les montants payés à des vendeurs nommés ne sont pas des arêtes. 2.03 : obligation financière
nouvelle — `financing` / `loan_or_facility`, prêteur → groupe, montant en principal,
`stage` `drawn_or_paid` (émission) ou `available` (facilité), échéance dans `note`.

**Corps des EX-10.** Contrats entre le groupe et des établissements financiers, lus en entier,
morceau par morceau (les lignes s'ajoutent au fichier après chaque morceau). L'instrument :
`financing` / `loan_or_facility`, prêteurs → emprunteur, engagement total en `commitment_cap`,
date du contrat, échéance et marge en `note`, l'agent administratif en `payer`
(`administrative_agent`) ; les banques du syndicat ne se listent pas une à une. Une ligne par
clause financière chiffrée (niveau en `note`, sans signal ; `covenant_amendment` ou
`covenant_waiver` seulement si la pièce modifie ou lève une clause). Sûretés : `pledged_assets`
true quand le contrat crée une sûreté (actifs décrits en `note`). Garanties : `credit_support`,
garant → emprunteur, une ligne par garant nommé. Une ligne pour chaque partie qui n'est ni une
banque ni un fonds de crédit (fournisseur, client, groupe de la liste), et pour un contrat client
nommé dans les sûretés. Cas de défaut notables en `note`. Capped call ou couverture : observation
sans famille, contrepartie nommée, termes en `note`.

**Immobilisations et estimations (`lever_note`).** Leviers de §6.1 qui ne se lisent que dans
le texte. Le principal : un **changement d'estimation de durée d'utilité** (ou de valeur
résiduelle) avec son effet publié. Une observation sans `family` ni `edge_type`, `event_type`
`measurement_change`, `amount` = l'effet tel qu'écrit (positif), `unit` `USD`,
`period_start` / `period_end` = la période de l'effet que le texte nomme (trimestre ou
exercice ; sans période déterminable, pas de montant), `instrument_key` stable pour un même
changement (par exemple `msft:server_life_fy2023`). Le champ `note` commence exactement par
l'une de ces formes, choisie d'après le texte :
- `effet : + résultat opérationnel` ou `effet : − résultat opérationnel` quand le texte donne
  l'effet sur le résultat opérationnel (ou avant impôt) ;
- `effet : − dotations` ou `effet : + dotations` quand il donne l'effet sur la charge
  d'amortissement (une baisse des dotations s'écrit « − dotations ») ;
- `effet : + résultat net` ou `effet : − résultat net` quand il ne donne que l'effet net d'impôt.
Si le texte donne plusieurs effets (dotations, résultat opérationnel, résultat net), écris une
ligne par effet, avec le même `instrument_key`. Les durées d'utilité publiées par classe
d'actifs ne s'écrivent que si elles changent ; une politique inchangée → abstention
`boilerplate_no_event`.

**Notes de revenu (`revenue_note`).** Contrepartie payable à un client **nommé** (bons de
souscription, actions, crédits, incitations) : `customer_consideration` (fournisseur → client),
`edge_type` selon la forme, `amount_nature` `consideration_payable_to_customer`, `stage`
`recognized` quand le texte dit le montant porté en réduction du revenu d'une période (avec
la période), `signed` pour un engagement. Contrepartie non monétaire reçue d'un client nommé
(titres ou bons du client reçus en paiement, ASC 606-10-32-21) : `commercial` /
`revenue_recognized`, client → groupe, `amount_nature` `noncash_consideration_received`,
`stage` `recognized`, période. Revenu ou carnet (RPO) attribué à un client nommé :
`commercial` / `revenue_recognized` (montant reconnu) ou `purchase_commitment` (carnet,
`stage` `signed`, `amount_nature` `commitment_unexecuted`, `period_end` à la date du carnet).
Brut ou net (agent) : une observation sans montant seulement si le texte nomme la
contrepartie. Rien de nommé → abstention `no_named_counterparty` ; politique générale →
`boilerplate_no_event`.

## 7. Abstentions

- `no_relevant_content` : rien de ce qui précède (politique comptable générale, tableaux déjà
  balisés sans nom).
- `no_named_counterparty` : des montants, mais aucune contrepartie nommée ni dérivable.
- `boilerplate_no_event` : texte générique sans événement.
- `out_of_scope_content` : litiges, fiscalité, rémunération…
- `duplicate_of_other_block` : le bloc répète mot pour mot un bloc déjà lu (rare, la clé de
  contenu dédoublonne déjà).
- `cannot_describe_in_schema` : un fait pertinent que le schéma ne peut pas porter (explique
  dans `note`).
Une abstention peut porter une `quote` et une `note`.

## 8. Exemples (premier passage)

```
{"kind": "observation", "family": "financing", "edge_type": "equity_primary", "payer": "Oracle Corporation", "payee": "Ampere Computing Holdings LLC", "counterparty_name": "Ampere Computing Holdings LLC", "counterparty_evidence": "named", "amount": "1600000000", "unit": "USD", "currency": "USD", "amount_nature": "investment_carrying_amount", "amount_origin": "narrative_only", "amount_qualifier": "exact", "measurement_basis": "equity_method", "exposure_block": "exposed_assets", "category_id": "equity_investment", "consolidation_treatment": "equity_method", "stage": "recognized", "event_type": "recognition", "period_end": "2025-05-31", "instrument_key": "orcl:ampere_investments", "quote": "The total carrying value of our investments in Ampere, after accounting for losses under the equity method of accounting, was $1.6 billion as of May 31, 2025."}
{"kind": "observation", "family": "credit_support", "edge_type": "guarantee", "payer": "CoreWeave, Inc.", "payee": "CoreWeave Compute Acquisition Co. VII, LLC", "counterparty_name": "CCAC VII", "counterparty_evidence": "named", "category_id": "guarantee", "exposure_block": "contingent_obligations", "conditionality": "conditional", "trigger_description": "défaillance de CCAC VII au titre du DDTL 3.0", "trigger_occurred": "unknown", "recourse": "full_recourse", "stage": "signed", "event_type": "signing", "event_date": "2025-07-28", "instrument_key": "crwv:ddtl_3_0_parent_guarantee", "quote": "The obligations of CCAC VII (but not CCAC V) under the DDTL 3.0 Facility are unconditionally guaranteed by the Parent pursuant to a parent guarantee and pledge agreement"}
{"kind": "observation", "signal": "material_weakness", "signal_present": false, "quote": "Based on this evaluation, our CEO and CFO concluded that, as of February 3, 2019, our disclosure controls and procedures were effective at the reasonable assurance level."}
{"kind": "abstention", "abstention_reason": "no_named_counterparty", "note": "tableau des titres non cotés, totaux balisés, aucun émetteur nommé"}
```

## 9. Ce que tu rends à la fin

Un court compte rendu : nombre de blocs lus, d'observations et d'abstentions, et la liste des
entités nommées les plus importantes (participations, prêteurs non bancaires, clients nommés),
avec leur bloc. Pas de chiffres hors des lignes soumises.
