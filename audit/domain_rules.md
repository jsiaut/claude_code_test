# Règles du domaine appliquées

*Une page, sans aucun résultat. Elle énonce les règles que le modèle applique et leurs sources
normatives (spec v6.14, §2 à §10 et §13 ; le §14 n'est pas ouvert au premier passage).*

## Preuves (§2)

- **Filed contre furnished.** Un document filed engage l'émetteur (Exchange Act, Section 18) ; les 8-K items 2.02 et 7.01 et leurs pièces sont furnished sauf déclaration expresse (Form 8-K, General Instruction B.2), comme les 6-K (Form 6-K, General Instruction B). Un DRS est soumis, pas déposé, et n'entre dans aucune mesure.
- **Niveaux de preuve.** États et notes audités : A ; revus : B ; autres passages filed (MD&A, Item 404, sections de 8-K) : C ; contrat et ses termes (EX-10, EX-4) : D ; furnished non incorporé, soumis, correspondance, commercialisation : E ; hors EDGAR : F. Les niveaux E et F ne servent que de pointeurs et n'entrent dans aucun calcul.
- **Contrepartie.** Sans contrepartie nommée ou dérivable (parties d'un contrat annexé, libellé d'un membre de dimension, égalité exacte avec un montant nommé du même dépôt, renvoi explicite), un montant n'alimente aucune arête ; un client anonyme reste anonyme.
- **Pièges.** Un montant caviardé (Reg S-K Item 601(b)(10)(iv)) est une donnée manquante, jamais un zéro ; une conclusion fondée sur l'absence d'une clause publie la couverture contractuelle (Item 601(b)(10)(ii)) ; les lettres du personnel de la SEC orientent la lecture, jamais la source d'un montant. Aucun chiffre de seconde main ni de mémoire.

## Circularité (§3)

- Arêtes orientées de la partie qui fournit la ressource vers celle qui la reçoit : financement (financeur → financé), soutien de crédit (garant → obligé), relation commerciale (client → fournisseur), contrepartie au client (fournisseur → client). Définitions limitatives (crédit fournisseur : ASC 606-10-32-15 ou délai de plus de 12 mois ; apport non monétaire : ASC 606-10-32-21).
- Statut « financé » F(S, C, t) daté : détention d'un instrument émis par C (niveau A ou B), versement ou prêt en numéraire dans les huit trimestres précédents, ou contrepartie au client comptabilisée dans ces huit trimestres ; `unknown` tant que les pièces qui pourraient l'établir ne sont pas lues ou que l'historique est tronqué, jamais `never`.
- Dépendance de revenu : ratio des sommes sur une fenêtre déclarée, jamais une moyenne de ratios ; l'achat du client n'est pas le revenu du fournisseur sans rapprochement documenté ; l'absence d'attribution est `not_determinable`, jamais 0 %. Bornes d'ASC 280-10-50-42 (client d'au moins 10 % publié) pour les seuls exercices.
- Conclusion par paire : `documented_dependency` exige une pièce de lien L1 à L5 (clause d'emploi des fonds, tranches calées sur des livraisons, traitement comptable liant les deux — ASC 606-10-25-9, 32-25, 32-21 —, obligation d'achat finançant le fournisseur — ASC 440-10-50-2 —, déclaration explicite) dont l'extrait nomme les deux parties. Aucun seuil de ratio ne déclenche seul une conclusion.

## Santé financière, exposition, résultat (§4 à §6)

- Variations en glissement annuel ou sur douze mois glissants ; un terme manquant rend un ratio `not_determinable` et une somme `partial` ; aucun score composite.
- Exposition publiée en matrice (passifs reconnus, sorties contractuelles non actualisées, engagements conditionnels, actifs exposés), jamais en total unique ; une garantie de 100 sur une dette de 100 ne fait pas 200 ; baux non commencés (ASC 842-20-50-3(b)) suivis jusqu'à leur commencement.
- Capex décaissé, capex en droits constatés, additions en location-financement, financées par le vendeur (ASC 230-10-45-13(c)) ou payées en titres publiés séparément, jamais additionnés.
- Pont de résultat avant impôt vers les effets publiés (réévaluations, dilution, mises en équivalence, dépréciations, changements d'estimation, intérêts capitalisés) ; un effet de changement d'estimation ne vaut que pour sa période (ASC 250-10-50-4).

## Données et contrôles (§7, §8)

- Identité d'un fait : concept sans version, entité, période, unité, dimensions canoniques, cadre comptable, périmètre ; jamais `fy` ni `fp`. Vues `as_known` (connu à la date D) et `revised` (présentation révisée) ; un trimestre obtenu par différence de cumuls garde les clés de ses termes, et des termes de révisions différentes le rendent `not_determinable`.
- Une instance extraite est déjà à l'échelle ; `decimals` est une précision. `nil`, zéro explicite et absence sont trois états ; aucune somme de devises mélangées.
- Tolérance d'arrondi, et elle seule : Σ ½·10^(−decimalsᵢ) + ½·10^(−decimals_b). Contrôles C1 à C16 ; un contrôle sur les seuls totaux déposés est `tautological` ; la correspondance de concepts se fixe par règle avant les contrôles et ne change ensuite que sur une pièce nouvelle.
- Paires non additives (registre de `config.yaml`) : une somme n'existe que si une relation résolue démontre son additivité.

## Accès, périmètre, entités (§9, §10, §13)

- Un seul User-Agent déclaré, 5 requêtes par seconde au plus (plafond SEC : 10 par utilisateur), pause d'au moins 10 minutes après un 403, aucun changement d'identité.
- Une entité par personne morale, appartenances datées ; on ne fusionne que sur CIK ou identité affirmée par une pièce ; un émetteur successeur garde l'historique de son prédécesseur. Une combinaison sous contrôle commun porte deux dates (début du contrôle commun en vue `revised`, date juridique en vue `as_known`).
- Les exercices ne coïncident pas (52/53 semaines) ; les flux des 10-Q sont cumulés et le quatrième trimestre s'obtient par différence ; un amendement complète l'original sans le remplacer.
