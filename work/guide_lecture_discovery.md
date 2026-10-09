# Guide de lecture du bloc `discovery` (§14, §7.4, D-0036)

Ce guide complète `work/guide_lecture_text.md`, dont le format des lignes, l'orientation des
arêtes, la contrepartie et les montants valent ici aussi. Rien d'autre que ce que dit le bloc :
aucun chiffre de mémoire, aucune connaissance extérieure, aucune arithmétique.

## 1. Ce qui change

- **Le déclarant n'est pas un groupe de `config.yaml`.** C'est un déposant qui nomme un groupe
  (son nom est dans l'en-tête, champ `filer_name`). Ses noms dans le texte (« we », « the
  Company », sa dénomination) se rattachent à lui : écris `payer` ou `payee` tels que le texte
  les écrit, « we » compris.
- **Ce qu'on cherche d'abord** : les relations entre le déclarant et les groupes nommés
  (`groups_named` dans l'en-tête), et les contreparties de ces relations.
  - Un groupe finance le déclarant : participation, prêt, bon de souscription détenu,
    préfinancement, garantie ou soutien de crédit (« backstop »).
    - Famille `financing` ou `credit_support`, groupe → déclarant.
    - Stade `drawn_or_paid` ou `recognized` seulement si le texte constate le versement ou la
      comptabilisation.
  - Le déclarant achète à un groupe : achats, engagements d'achat, bail de capacité pris chez
    un groupe.
    - Famille `commercial`, déclarant → groupe.
  - Un groupe est client du déclarant : revenu reconnu, bail de capacité consenti à un groupe,
    contrat d'hébergement.
    - Famille `commercial`, groupe → déclarant, `revenue_recognized` ou `capacity_lease`.
  - Le déclarant remet des titres, des bons ou des crédits à un groupe client.
    - Famille `customer_consideration`, déclarant → groupe.
  - Tout intermédiaire nommé dans ces relations (fonds, véhicule, coentreprise, laboratoire) :
    une ligne pour chacun.
    - Ce sont les maillons que la découverte doit trouver (§14, chemins).
- **Pièce de lien (L1 à L5)** : seulement si l'extrait nomme les deux parties et lie
  financement et achats (§3.4). Elle est rare : jamais sur une simple co-mention.
- **Ce qui n'est pas une relation** : un groupe cité comme concurrent, comme plateforme de
  vente ou de publicité générique, comme fournisseur de logiciels courants sans montant, ou
  dans un exemple.
  - Abstention `out_of_scope_content` si le bloc ne contient rien d'autre.
  - Une mention de vente par une plateforme d'un groupe (« sold through Amazon.com ») avec une
    part ou un montant attribué au groupe est une relation commerciale : une ligne.
- **Les relations du déclarant avec des tiers hors groupes** ne se notent que si elles
  touchent une relation avec un groupe : par exemple un financement levé pour un contrat
  conclu avec un groupe, ou une garantie au profit d'un groupe.

## 2. Pièces EX-10 (en-têtes)

L'en-tête montre les parties. Une ligne par partie qui est un groupe ou un laboratoire, avec
`party_role`, et sans montant si le texte n'en donne pas. Si aucun groupe n'est partie (le
groupe n'est que cité), abstention `out_of_scope_content` avec une `note` qui le dit.

## 3. `instrument_key`

Préfixe : le nom court du déclarant, en minuscules sans espace (`apollo:broadcom_capital_solution`,
`applieddigital:coreweave_lease_ellendale`). La même clé pour toutes les lignes du même
instrument, d'un bloc à l'autre.

## 4. Désignation des parties (D-0038)

- Le déclarant et ses filiales consolidées s'écrivent `the Company` dans `payer` et `payee`, quelle que soit la forme du texte (« we », nom court, « the Group », nom d'une filiale consolidée). La citation reste celle du texte.
- Un terme défini du bloc (« Borrower », « Lender », « Holder », « Customer », « Partner ») s'écrit sous le nom qu'il désigne dans le même bloc.
- Une même valeur ne se relève qu'une fois : un montant par segment qui compose un total déjà relevé ne fait pas de ligne (abstention `duplicate_of_other_block`).
