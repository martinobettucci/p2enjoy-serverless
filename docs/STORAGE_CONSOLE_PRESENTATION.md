# États d’archives cohérents dans la console de stockage

Contrat de [SLS-113](BACKLOG.md#sls-113), découvert pendant la lecture visuelle
du sixième passage complet078. L’unité porte deux présentations contradictoires,
aucune attribution de perte de données ou de défaut d’ACL sur une capture seule.

## Constats conservés

Image433da150, gel9e1da704c230dcd05c414c4e1013fa882c8fda44,
run833b57eff42c4b429d06a86161e5fc5b, phase storage-console-ui :10groupes réussis,
14JPEG déclarés et ouverts individuellement. Rapport SHA
3f346779432b5dd2cd3e17a135ab44a4d27dd5ecb1e65777df381bfe816f37d3.
Images sous072-storage-console-ui-result :

- storage-ui-purged-mobile.jpg,390×1730,
  SHA7c91c06207213fa4c8d830d83bf29b9a001f8c103f535a1adbc14c987af33a93 :
  titre « Archives conservées », badge « Purgée », zéro révision/espace code,
  aucun volume et purge datée. Le titre contredit l’état détaillé.
- storage-ui-pagination-error.jpg,1440×1000,
  SHA569351743565ed9243f8ce4b3822ad3b6f8fbe63b76e5f9921e69eeaf01ec7c3 :
  cartes et total retirés pendant l’erreur ; « Page1sur161 » reste affiché,
  sans indication de fraîcheur, bien que les commandes soient grisées.

Les dates source sont dans la phase1795299314559953009→1795299424106362162.
Ce constat ne modifie pas le code ni les assertions du passage078 en cours.
Il est enregistré dans un checkout documentaire séparé pour garder le gel.

## Instruction avant correction

Lire les README racine/web/e2e, les deux design systems, CONSOLE_STORAGE,
manual et les composants/clients qui produisent ces vues. Rechercher les
précédents de titre selon état et de pagination pendant erreur/chargement.
Identifier les causes exactes puis persister le choix réversible et son motif
avant le code. Ne pas changer les états API ou les droits pour résoudre un libellé.

## Résultat attendu

La fiche distingue conservation et purge sans promesse contradictoire ; les
métadonnées historiques et le reçu restent consultables. La pagination en erreur
n’affirme pas un nombre de pages courant non obtenu. Conserver le filtre, la
possibilité de relire et le contexte utile ; ne pas remplacer l’inconnu par un
faux zéro. Reprendre ensuite avec la pagination réellement renvoyée par le serveur.
Appliquer le même sens desktop/mobile, avec titres et focus cohérents.

## Preuves requises

Depuis l’accueil, SSO réel puis navigation souris/clavier, créer des fixtures
originales par les API, supprimer/purger réellement et provoquer la vraie panne
de consultation selon le mécanisme natif du client existant. Ajouter des
assertions qui discriminent chacun des deux défauts, sans retirer un des10groupes
ni modifier leurs fautes, volumes ou nettoyages. Aucune interception réseau,
substitution, mock, horloge fausse ou succès conditionnel.

Passage entier storage-console-ui10 puis25communs, sur sources/image synchronisées
et gelées ; tous les JPEG frais ouverts individuellement, dont les deux états
corrigés desktop/mobile. Recouper les purges, baux/chemins/processus, reçus,
manuel canonique affiché, backend/web servis, configuration/référence et5982
originaux. Le compte reste35groupes si les discriminants enrichissent les groupes
existants ; tout nouveau groupe distinct est annoncé avant son exécution.
Une preuve manquante garde113ouverte. Le passage078 actuel conserve son époque ;
il ne qualifie ni ces changements absents ni la campagne globale095.
