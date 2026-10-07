# Point de contrôle n° 1 — après la mesure du terrain

*7 octobre 2026. Cette page résume ce que le travail va faire, ce qui reste incertain et ce qui est
laissé de côté. Elle ne demande aucune décision.*

## Ce qui a été décidé

- **Les onze groupes** de la liste sont tous retrouvés dans le registre de la SEC : NVIDIA, Alphabet, Amazon, Meta, Microsoft, Oracle, CoreWeave, SpaceX, AMD, Broadcom et Marvell. Broadcom et Marvell ont changé de société mère en 2018 et en 2021 ; leurs anciennes sociétés mères sont rattachées à leur groupe, pour que leur historique ne s'arrête pas net.
- **La période étudiée** commence avec le premier exercice clos en 2021 et va jusqu'à aujourd'hui. Les textes sont lus depuis 2017-2018, pour pouvoir dire si un financement était encore en cours au début de la période.
- **Ce premier passage lit seulement ce qui rapporte le plus** :
  - les chiffres balisés des comptes (sans lecture de texte) ;
  - les notes sur les parties liées et la section du rapport aux actionnaires sur les transactions avec des proches ;
  - les passages sur le contrôle interne et sur la continuité d'exploitation ;
  - les annonces d'accords importants (signature, fin d'un accord, modification des droits des porteurs, autres événements), avec les contrats et titres joints.
- **Les critères qui permettront de juger les résultats** (dépendance d'un fournisseur envers des clients qu'il finance, événements de fragilité) ont été fixés et enregistrés **avant** la première requête. Leur empreinte vous a été envoyée à 10:54 UTC. Rappel : commit `3ff3b988a48a5c904f88f006d263bfa780739d39`.
- **Votre adresse de contact n'apparaît nulle part dans le dépôt**, qui est public. Elle n'est envoyée qu'à la SEC.

## Ce qui reste incertain

- **SpaceX** n'a publié qu'un seul rapport trimestriel balisé. Ses comptes annuels 2023 à 2025 ne se trouvent que dans son prospectus d'introduction en bourse, sans balises. Ils seront lus et vérifiés ; s'ils ne se recoupent pas avec le rapport trimestriel, SpaceX n'entrera qu'avec ses périodes balisées. Ses comptes incluent rétroactivement xAI et X, regroupés sous le contrôle commun d'Elon Musk : les deux présentations (avec et sans xAI et X) seront montrées côte à côte quand c'est possible.
- **CoreWeave** n'a rien déposé avant mars 2019 : son historique plus ancien est inconnu, et le modèle le dira au lieu de supposer qu'il ne s'est rien passé.
- **Beaucoup de mesures resteront « non déterminables »** à l'issue de ce passage. Les grands fournisseurs nomment rarement leurs clients, et une partie des textes n'est pas lue au premier passage. Chaque case vide portera sa raison.
- **La durée de lecture est estimée, pas mesurée** : environ 1 200 passages à lire, soit plusieurs heures. Le réseau, lui, ne prend qu'une dizaine de minutes.

## Ce qui est laissé de côté, et pourquoi

- **La recherche d'autres sociétés** qui nomment ces groupes, les jeux de données en masse de la SEC, les levées privées (Form D), les prêteurs spécialisés et les émetteurs étrangers. Ils attendent de savoir ce que rapporte ce premier passage ; vous seul déciderez de les ouvrir.
- **La presse et les communiqués** : seuls les documents officiels déposés comptent comme preuve.
- **Près de 14 000 autres dépôts** de la période (déclarations de dirigeants, détentions d'actionnaires…) : ils ne servent pas aux questions posées.

## Où vivent les choses

- **Le dépôt** : `jsiaut/claude_code_test`, branche `claude/youthful-brown-3dtor0`. Il contient le code, la configuration, les décisions, ces pages et, à la fin, les tables et les notes.
- **Le cache des téléchargements** vit dans le conteneur de cette session, qui est temporaire. Les documents officiels pourront être retéléchargés à l'identique. Les extraits d'interfaces, eux, sont datés et ne se retrouveront pas exactement : leur empreinte est gardée.
