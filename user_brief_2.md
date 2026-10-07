# Point de contrôle n° 2 — après le premier passage

*7 octobre 2026. Cette page résume ce que le premier passage a produit, ce que le modèle affirme et
n'affirme pas, ce qui a été laissé de côté, et pose la seule question de l'exécution : faut-il aller
plus loin ?*

## Ce qui a été fait

- **843 dépôts officiels** des onze groupes ont été lus : les chiffres balisés de leurs comptes, puis
  1 133 passages de texte (transactions avec des proches, contrôle interne, continuité d'exploitation,
  annonces d'accords importants et contrats joints). Ils ont donné 1 550 constats, chacun avec sa
  citation mot pour mot, et 274 abstentions motivées.
- **Tout a été recalculé deux fois** à partir des mêmes documents : les tables obtenues sont identiques.
- **Plus de 15 000 vérifications comptables** ont été faites sur les comptes tels que publiés (sommes
  des bilans, des flux de trésorerie, des secteurs, des échéanciers…). 13 615 passent ; 603 montrent un
  écart, publié tel quel avec sa cause probable ; les autres ne sont pas testables ou ne prouvent rien.

## Ce que le modèle affirme

- **Huit groupes ont au moins un événement de fragilité daté**, avec sa pièce :
  - Oracle a investi plus que la trésorerie dégagée par son activité, deux trimestres de suite, à cinq
    reprises depuis l'été 2025 ; Amazon à quatre reprises (2021, 2022 et 2026) ; CoreWeave à cinq.
  - CoreWeave déclare une faiblesse de son contrôle interne sur six trimestres d'affilée ; elle a
    obtenu une dérogation aux clauses financières d'un prêt et modifié ces clauses deux fois.
  - Marvell a aussi modifié des clauses de prêt (deux fois) ; NVIDIA, Meta, AMD et Marvell ont connu un
    recul de leur chiffre d'affaires sur un an ; NVIDIA et Microsoft ont abaissé une durée
    d'amortissement publiée ; AMD a déprécié un investissement.
- **Quatre relations mêlent, pièces à l'appui, un financement et des achats** reliés par un document :
  NVIDIA et CoreWeave, NVIDIA et OpenAI, AMD et OpenAI, Amazon et OpenAI. Quatre autres réunissent un
  financement et une relation commerciale sans lien documenté entre les deux (AMD et Meta, Marvell et
  Alphabet, Oracle et deux sociétés Ampere).
- **Six relations ont un financement établi** à au moins une date, dont NVIDIA dans CoreWeave depuis
  janvier 2026, et CoreWeave dans un fonds géré par Magnetar, lui-même financeur de CoreWeave.

## Ce que le modèle n'affirme pas, et ce qui reste incertain

- **Il ne mesure aucune dépendance de chiffre d'affaires.** Pour aucune des relations ci-dessus on ne
  sait quelle part des ventes du fournisseur vient de clients qu'il finance : les grands clients sont
  presque toujours anonymes (« client A : 67 % du chiffre d'affaires de CoreWeave en 2025 »), et le
  texte qui permettrait de les nommer n'est pas lu au premier passage. Là où une borne existe, elle se
  limite à « moins de 10 % » (28 cas).
- **Le test principal ne tranche pas.** Sur 12 confrontations aux critères fixés avant la première
  requête, 11 restent indéterminées : les documents lus ne permettent ni de confirmer ni d'écarter
  l'idée que le financement des clients fabrique une partie du chiffre d'affaires. C'est d'abord une
  conséquence du périmètre de lecture, pas la preuve qu'il n'y a rien.
- **Plus de la moitié des cases du tableau de bord restent vides** (8 489 sur 15 766), chacune avec sa
  raison : 3 394 parce que le texte qui les remplirait n'est pas encore lu, 786 parce que les documents
  de CoreWeave ne remontent pas assez loin, les autres surtout parce que l'information n'est pas publiée
  ou pas balisée.
- **SpaceX** n'a qu'un trimestre publié en bourse ; ses comptes annuels viennent de son prospectus.

## Ce qui a été laissé de côté, et pourquoi

- **217 contrats et actes d'emprunt** dont les seules autres parties sont des banques ont été arrêtés à
  leur première page : ils n'apprennent rien sur les relations entre ces groupes.
- **377 chiffres** contradictoires (deux valeurs pour le même chiffre dans un même dépôt, ou un saut
  d'échelle d'un facteur 100 entre deux périodes) sont écartés plutôt que devinés.
- **48 noms** cités dans les documents n'ont pas pu être identifiés avec certitude : ils restent
  visibles mais hors des totaux, pour ne jamais fusionner deux sociétés sur une ressemblance de nom.
- **8 projets de prospectus** non déposés officiellement ne comptent pas comme preuve.

## Rendement du passage

- Réseau : 3 741 requêtes, presque toutes à la SEC, 1,5 Go reçus, en une heure environ.
- Lecture : environ deux heures et quart pour 1 133 passages.
- Résultat : 6 322 cases calculées, 955 bornées ou partielles, 33 événements de fragilité datés,
  36 relations entre groupes et contreparties, dont 8 où financement et commerce se croisent.

## La question : faut-il aller plus loin ?

Rien de ce qui suit ne s'ouvre sans votre accord. Sans réponse, le modèle reste au premier passage et
se tient à jour. Le cahier des charges recommande l'ordre : prêteurs, puis texte, puis découverte.

1. **Le côté prêteur.** Ce qu'il cherche : dans les données publiées par la SEC sur les fonds de prêt
   cotés, les prêts accordés aux sociétés citées par les onze groupes (valeur du prêt rapportée à son
   coût, intérêts payés en nouveaux titres, prêts sans intérêts versés). Ce qu'il coûte : quelques
   dizaines de fichiers mensuels, sans lecture de texte, quelques heures. Ce qu'il peut changer : des
   signaux trimestriels précoces sur la dette des centres de données détenus par des fonds privés ;
   rendement incertain, ces fonds prêtant rarement aux grands groupes eux-mêmes.
2. **Le reste du texte.** Ce qu'il cherche : les notes sur les participations, la dette, les baux et
   les engagements, les 217 contrats bancaires, le texte autour des parts de clients. Ce qu'il coûte :
   quinze à vingt fois le texte lu jusqu'ici, soit plusieurs dizaines d'heures de lecture en plusieurs
   séances (estimation, pas une mesure), sans nouveau téléchargement. Ce qu'il peut changer : c'est lui
   qui remplit le plus de cases vides (les 3 394 « pas encore lu » et 794 partielles), qui peut nommer
   des clients anonymes, dater les participations plus anciennes (NVIDIA dans CoreWeave avant 2026, par
   exemple) et rendre le test principal décisif.
3. **La découverte.** Ce qu'elle cherche : qui, en dehors des onze groupes, les nomme dans ses notes,
   ses contrats ou ses levées de fonds privées (hébergeurs, fonds, véhicules). Ce qu'elle coûte :
   plusieurs gigaoctets d'archives de la SEC, puis la lecture des notes des sociétés trouvées ; plusieurs
   jours. Ce qu'elle peut changer : trouver les intermédiaires, condition pour suivre un financement qui
   revient par deux ou trois étapes ; c'est la seule façon de clore la recherche.
4. **Plus petits ou plus tard :** les levées privées de xAI avant sa fusion (quatre déclarations, coût
   faible, des montants levés mais jamais une valorisation) ; les circuits à plusieurs étapes (après la
   découverte) ; d'autres groupes, en commençant par les hébergeurs endettés (TeraWulf, Cipher Mining,
   Core Scientific, Nebius, IREN), chacun au prix d'un premier passage.

**Mon avis, chiffres à l'appui :** le reste du texte est ce qui change le plus de résultats pour son
coût ; le côté prêteur est rapide mais de rendement incertain ; la découverte est la plus chère.
Dites simplement lesquels ouvrir (par exemple « texte », ou « prêteurs et texte »), ou « rien ».
