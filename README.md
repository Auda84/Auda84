# Analyse_KMS_FO3

> Documentation générée automatiquement depuis `Analyse_KMS_FO3.docx`

---

KMS – ERM FO3

Analyse du Plan de Câblage Fibre Optique SM

Réf. document : C-190600009  |  Date : 29/08/2024  |  Auteur : Pierre DAISOMONT

Royal Military Academy (RMA)

# 1. Informations Générales

# 2. Architecture du Réseau

## 2.1 Structure générale

Le plan représente l'infrastructure de câblage fibre optique monomode du site KMS de la Royal Military Academy. L'architecture est organisée en blocs (bâtiments/zones) répartis sur plusieurs niveaux positifs et négatifs. Chaque bloc dispose de panneaux de brassage (Patch Panels – PP) interconnectés via des liaisons fibres codifiées par couleur.

## 2.2 Types de liaisons

## 2.3 Niveaux d'implantation

Les blocs sont implantés sur plusieurs niveaux :

- Niveaux positifs (Bloc-X0+) : niveaux 0 et supérieurs
- Niveaux négatifs (Bloc-X0-) : niveaux inférieurs au niveau 0 (sous-sols)
- Exemple : Blok K s'étend de K-2 (sous-sol -2) à K+4 (niveau +4)
# 3. Inventaire des Blocs

Le plan recense 30+ blocs distincts. Le tableau ci-dessous liste les blocs identifiés avec leurs références et niveaux d'implantation.

# 4. Panneaux de Brassage (Patch Panels)

## 4.1 Convention de nommage

- Format : PP## (ex. PP01, PP02, …, PP11)
- Chaque Patch Panel dispose de 12 ou 24 ports (selon le format)
- Ports numérotés : 1–12 (demi-panneau) ou 1–12 / 13–24 (panneau complet)
- Certains blocs secondaires utilisent un format réduit : 1–6 / 7–12 (Blok B', G') ou 1–10 / 1–13 (MUS)
## 4.2 Distribution des panneaux par bloc

# 5. Code Couleur des Fibres

Le plan applique une codification couleur normalisée pour identifier les fibres au sein de chaque câble. Les couleurs sont utilisées pour différencier les liaisons entre blocs sur le schéma.

# 6. Équipements et Points Spéciaux

# 7. Observations & Points d'Attention

- Blok L1 est le bloc le plus dense du plan avec jusqu'à 11 panneaux de brassage (PP06 à PP11) sur une seule zone.
- La couleur Rouge est omniprésente sur l'ensemble du plan, confirmant son rôle de backbone principal inter-blocs.
- Les blocs de la rangée principale (F, I, O, M, Q) suivent un schéma uniforme à 6 panneaux chacun (6 couleurs distinctes : Rouge, Vert, Bleu, Jaune, Blanc, Gris).
- La série Blok K est la plus hiérarchisée avec 6 niveaux d'implantation (K-2 à K+4) et des équipements IGN intégrés.
- Blok R constitue le point de terminaison vers la salle des serveurs IGN via le Wall Box.
- Les blocs secondaires (B', G', L1, L2) possèdent des sous-divisions avec des références de câbles spécifiques.
- Les liaisons Pied 1 et Pied 2 assurent la redondance de desserte vers les blocs terminaux.
Document généré à partir du plan RMA KMS FO3 – C-190600009 – 29/08/2024


---

*Généré automatiquement par push_readme.py*