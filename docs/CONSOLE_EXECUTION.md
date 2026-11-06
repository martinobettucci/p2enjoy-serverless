# Consultation des exécutions dans la console

Contrat SLS-061, tranche de SLS-060, en cours de réalisation.

## Parcours et données

La fiche `/console/functions/{id}` conserve sa configuration actuelle. Deux
facettes partageables, `/instances` et `/invocations`, présentent respectivement
les instances réservées et l’historique réel. Les liens portent Configuration,
Instances et Invocations. L’identité, l’état de publication et le fil d’Ariane
restent visibles. Chaque facette se charge indépendamment des formulaires.

Les GET existants de [ADMISSION](ADMISSION.md#observations-et-cycle-du-contrôle)
font autorité. La console emploie la session administrateur normale. Chaque
page contient cinq éléments, afin de borner le volume de journaux et le coût
des mesures Docker. Le total courant détermine Précédente/Suivante et le nombre
de pages ; l’offset ne dépasse jamais 10000. Une page devenue hors limites
après extinction revient à la dernière page existante. Un rafraîchissement
manuel remplace le relevé, sans scrutation périodique ni requêtes superposées.
La date du relevé est affichée. La pagination à offset reste un relevé vivant,
pas un instantané figé pendant les nouveaux appels.

## Présentation

Une liste d’instances montre les identifiants complets, leur révision, l’état,
les allocations CPU/Mio et les mesures séparées. Le CPU mesuré est le temps CPU
cumulé en secondes, jamais un pourcentage ; la mémoire consommée est en Mio.
Une mesure absente porte « Indisponible », avec le motif public lorsqu’il existe.
Les états ont un libellé français et une couleur secondaire ; un état inconnu
reste lisible avec un repli neutre.

La liste d’invocations présente réception, identifiant complet, état et statut
HTTP distincts. Un détail dépliable natif révèle chronologie, révision, instance,
code de diagnostic, observation du démarrage et journal. Le démarrage garde
les trois valeurs Oui, Non et Non confirmé ; il n’est pas une autorisation de
rejouer. Les journaux restent du texte échappé, multiligne, défilant localement,
avec une indication explicite lorsqu’ils sont tronqués. Un appel actif sans
journal indique que celui-ci sera disponible à sa fin ; un appel terminé sans
journal indique l’absence de collecte. Aucun corps métier n’est ajouté.

Les états chargement, vide et erreur sont explicites. Actualiser et les commandes
de page restent hors de la liste remplacée. Un changement de page place le focus
sur le titre du relevé après réception ; Actualiser garde son focus. Les détails
s’ouvrent et se ferment au clavier. À 390 px les identifiants et lignes de journal
reviennent à la ligne, sans débordement horizontal de la page.

## Preuves attendues

La campagne part de l’accueil réel avec la session SSO, crée ses objets via
la console, publie un handler original avec l’adaptateur et les API normales,
puis invoque avec un vrai jeton Read. Elle couvre listes vides et chargement,
instances réelles et allocations/mesures, appels actifs puis terminaux,
refus et erreurs, pagination réelle des deux listes, disparition des instances,
journaux vides/multilignes/longs/tronqués et expurgés, contenu HTML rendu comme
texte, clavier/focus, erreur réseau réelle et reprise, navigation partageable,
mobile et retour desktop. Les appels actifs sont rejoints avant nettoyage.
Les captures sont relues ; rapports, sources, image et ressources servies sont
recoupés. Les parcours de gestion existants et l’entrée publique sont rejoués.
