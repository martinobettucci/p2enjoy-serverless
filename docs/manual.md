# Utiliser la console DEV

La console initiale est déployée sur
[serverless.lelabs.tech](https://serverless.lelabs.tech).
Les parcours de gestion passent leurs preuves API et UI ; les cycles SSO
restants figurent dans [BACKLOG.md](BACKLOG.md). Les paramètres d'exécution sont actuellement
enregistrés : leur application aux fonctions appartient au moteur en développement.

## Se connecter

Ouvrir la console puis choisir **Se connecter**. La connexion se déroule sur
le SSO lelabs ; le compte doit posséder les rôles `verified` et `admin`.
Un refus de connexion revient à l'accueil avec son motif. La session de console
expire au plus tard après huit heures ; la déconnexion la ferme immédiatement.

## Organiser les fonctions

Depuis **Namespaces**, créer un namespace puis ouvrir sa fiche. Créer un service
dans ce namespace, puis une fonction dans le service. Les noms de namespaces
et services sont en minuscules ; ceux des fonctions conservent leur casse.
Une fonction créée sans révision de code est un brouillon.

Les fiches permettent de modifier l'identité, les variables et les secrets.
La fiche de fonction expose aussi mémoire, CPU, durées, concurrence, instances
et stockage. Les erreurs de validation restent dans le formulaire. Si un
autre onglet a modifié l'objet entre-temps, l'enregistrement est refusé pour
préserver la version récente ; annuler puis rouvrir le formulaire pour la relire.

Une variable est visible en lecture. Un secret montre uniquement son nom et
sa présence ; sa valeur enregistrée n'est pas réaffichée. Les secrets et les
variables de service servent de configuration commune aux fonctions. Une
surcharge de fonction doit être explicite.

## Donner un accès à un service

Dans la fiche du service, créer un jeton, choisir ses droits CRUD, sa portée
et éventuellement son expiration. Une portée limitée à des fonctions exclut
le droit Create. La confirmation rappelle les droits accordés.

La valeur complète n'est affichée qu'à la création ou au renouvellement.
La copier avant de fermer son affichage. Chaque valeur nouvellement créée
reste visible indépendamment des autres jusqu'à sa fermeture. Révoquer un
jeton interdit ses nouvelles requêtes ; renouveler révoque l'ancien et fournit
une nouvelle valeur.

| Droit | Usage |
| --- | --- |
| Create | Créer une fonction et sa première révision |
| Read | Lire les objets autorisés et invoquer les fonctions |
| Update | Modifier configuration, secrets et révisions |
| Delete | Supprimer les fonctions autorisées |

Les appels portent `X-Serverless-Token`. L'en-tête `Authorization` reste
disponible pour l'authentification métier du handler. Les routes de révision
et la commande CLI `deploy` sont implémentées en DEV et restent à qualifier
avec une session administrateur. Le moteur d’invocation est en développement.

La [CLI](../adapter/README.md) lit `P2_SERVERLESS_URL` et `P2_SERVERLESS_TOKEN`
dans son environnement. Depuis le projet de fonctions, lancer
`python3 -m adapter deploy --config serverless.yml --service UUID_DU_SERVICE`.
Le nom du service doit correspondre au manifeste. Le jeton requiert Read et
Create pour une première publication, Read et Update pour une mise à jour.
Le rapport distingue les fonctions publiées, refusées et celles dont l’issue
est inconnue après une rupture réseau. Dans ce dernier cas, consulter le
candidat indiqué avant de relancer. Les valeurs de configuration restent
absentes des sorties et des descripteurs locaux.

## Définir les restrictions d'appel

La politique du service accepte des origines exactes, par exemple
`https://app.johndalia.com`, et des adresses IP ou CIDR. Choisir ET pour
exiger les deux critères actifs, OU pour accepter l'un des deux. Une liste
vide désactive son critère ; deux listes vides laissent le jeton comme
condition d'accès. La sauvegarde de cette politique est disponible ; son
application publique sera qualifiée avec la passerelle d'invocation.

## Consulter les changements et supprimer

L'activité du service présente les mutations et refus attribuables à une
identité connue. Les listes sont paginées.
La suppression demande confirmation. Un service doit être vide de fonctions
actives ; un namespace doit être vide de services actifs. L'archivage des
données de fonctions exécutables sera intégré avec leur stockage.
