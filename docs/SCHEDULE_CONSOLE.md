# Qualification des planifications dans la console

Complément de [SLS-078](BACKLOG.md#sls-078) et de la
[facette Planifications](SCHEDULES.md#facette-planifications). Décisions du
10 novembre2026, avant code ; résultats du replay en fin de page. L’unité reste ouverte.

## Parcours réel

Le navigateur entre par l'accueil HTTPS avec sa session SSO réelle. Il crée son
namespace, service et deux fonctions par les formulaires normaux. L'une reste
sans publication pour les états vides ; l'autre porte un nom de63 caractères.
La publication de ses crons passe par les API publiques de code seul : la console
ne propose pas de saisie des événements du manifeste. Le paquet est produit par
l'adaptateur réel, avec le handler original `scheduled-event.cjs` du dépôt.

Six expressions numériques distinctes, dont une longue liste, sont promues
avant une même frontière UTC de cinq minutes. Six instances minimales prêtes,
0,05CPU/128Mio chacune, permettent six handlers réels sans saturer le maximum
de fonction. Leur somme0,3CPU/768Mio reste dans les budgets officiels. Aucun
budget, route, secret ou service partagé n'est modifié. Après les six succès,
l'historique réel a deux pages de cinq et un tirs. Les lectures ne doivent pas
changer les tirs ni les invocations.

La campagne observe déclarations, prochain nominal/frontière, dernier résultat,
hash complet et lien d'invocation ; elle vérifie première/seconde page, retour
clavier, focus au titre d'historique et conservation du contexte de catalogue.
Desktop1440×1000 et vrai viewport mobile390×844 : noms et expressions complets,
absence de débordement de page, boutons accessibles aux extrémités, captures
JPEG pleine page et dans leur viewport à inspecter individuellement.

## Erreur réelle et reprise

Le protocole existant de `execution-ui.mjs` est réutilisé : sauvegarder en mémoire
les vrais cookies du navigateur, les retirer, cliquer Actualiser, constater le
GET401 du contrôle, puis remettre les mêmes cookies dans un `finally`.
Réessayer doit relire les deux endpoints200 et rétablir les mêmes données.
Il n'y a ni interception réseau, ni faux résultat, ni déconnexion serveur.
Ce scénario prouve un refus d'authentification réel, pas une panne503.

Le contrat existant retire les anciennes valeurs en chargement et en erreur,
y compris le total et le rang de pagination devenus non confirmés. Le composant
actuel semble garder ce dernier total ; la première exécution doit constater
l'état réel et échouer si une pagination périmée subsiste. L'essai et son
nettoyage restent distincts du replay d'un éventuel correctif. Masquer seulement
les cartes en conservant un ancien « Page2 sur2 » ne satisfait pas ce contrat.

## Nettoyage et preuves

Les cookies sont restitués avant toute purge. Les minima et l'idle sont ramenés
à zéro par l'API publique ; l'absence d'instances est observée avant suppression.
Les deux fonctions sont archivées puis purgées par les API normales, parents
supprimés. Le lecteur strict existant des deux fonctions recoupe SQL RO,
invocations, tirs, Docker, baux, réseaux, canaux, purges physiques et5982 artefacts
antérieurs. Identités/images/démarrages, fichiers officiels et sources embarquées
sont comparés au prérelevé. Chaque essai garde son rapport UUID et ses captures ;
aucun rejeu automatique après échec. Sources figées pendant chaque campagne.

La rétention réelle, le plafond global lié à SLS-099, le critère adaptateur.7 et
la régression complète restent des preuves distinctes dans SLS-078.

## Reproduction avant correctif

Le client2f8f989/fcfa3675 observe six succès à22:00UTC, puis les pages5+1,
clavier/focus et mobile. Le vrai401 retire les cartes mais laisse « Page2 sur2 »
sous « Historique indisponible ». La capture mobile et son SHA sont conservés
dans le rapport privé. Ce passage échoue volontairement au contrat existant ;
les deux fonctions sont purgées, six tirs et six invocations recoupés, compteurs
actifs à zéro. Les deux préparations antérieures restent distinctes.

Le correctif retire le total affiché dès le début de lecture et en erreur.
Le rang interne reste conservé afin que Réessayer relise la même page, après
restitution des cookies. Il n'ajoute ni donnée métier ni token visuel. Le manuel
décrit ce retrait et la reprise ; nouvelle image et replay réel requis avant
toute qualification du correctif.


## Résultats qualifiés

La [preuve](evidence/schedule-console-dev-2026-11-10.json) conserve19 groupes
sur326 sources figées : trois de console, huit manuel et huit publics rejoués.
Client2f8f989, correctif24d81c7, imagec59b8616 : six succès22:10UTC, deux pages5+1,
clavier/focus, vide/nom63/mobile, puis vrai401 sans ancienne pagination et reprise
200 de la même seconde page. Tirs et invocations identiques après lectures.
Deux purges physiques, six instances connues retirées, actifs nuls ; mêmes
services/configuration,34 backends et5982 artefacts pendant replay. Le déploiement
a sa sauvegarde native, conserve les neuf migrations et la référence.

31 images recoupées :17 inspectées personnellement,14 identités SHA avec des
références inspectées. Le manuel servi concorde avec16 chapitres/56 paragraphes ;
son nouveau texte est lu sur desktop/mobile. Les pleines pages et la vue après
reprise ont leurs limites de cadrage dans la preuve. Aucun défaut visuel bloquant.
Les trois essais antérieurs sont séparés, dont12 handlers et quatre purges
physiques dans les deux essais ayant atteint une frontière ; ils ne s'ajoutent
pas aux six courants. SLS-078.6 est qualifiée, les autres restes restent ouverts.
