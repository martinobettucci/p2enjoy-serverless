# Intégration avec P2Enjoy Serverless

Entrée HTTPS : https://serverless.lelabs.tech. La console utilise le SSO LeLabs, client confidentiel `p2enjoy-serverless-dev`, retour `/auth/retour`. Les rôles `verified` et `admin` sont exigés côté serveur. Les secrets OIDC et jetons du fournisseur restent côté serveur.

## Accès des projets

Un administrateur crée un namespace, un service puis des jetons de plateforme. Les clients utilisent `X-Serverless-Token`. Le droit Create permet une création et première publication ; Update permet les modifications et publications suivantes ; Delete supprime une fonction. Read permet les lectures autorisées et les invocations, quelle que soit leur méthode HTTP. Une portée par fonction interdit les opérations globales du service.

L’en-tête métier `Authorization` reste réservé au handler. Les règles d’origine web et d’IP sont appliquées par la passerelle, puis relues avant admission. Une origine web n’est pas une preuve d’identité d’un client hors navigateur.

## Déployer

Le projet garde ses handlers et son `serverless.yml`. L’adaptateur lit `P2_SERVERLESS_URL` et `P2_SERVERLESS_TOKEN`, puis s’utilise ainsi :

```sh
python3 -m adapter deploy --config serverless.yml --service UUID_DU_SERVICE
```

Le service doit correspondre au manifeste. L’adaptateur prépare avant mutation, publie en série et distingue succès, refus et issue inconnue. Les valeurs secrètes ne figurent pas dans son rapport. Les API de candidat sont `POST /api/functions/{id}/deployments`, `PUT /api/deployments/{id}/artifact` et `GET /api/deployments/{id}`. L’upload est une archive ZIP ; le contrôle valide le vrai handler dans un conteneur isolé avant publication.

Les variables et secrets du provider sont enregistrés au niveau du service ;
seules les surcharges explicites sont propres à chaque fonction. Une catégorie
provider absente conserve le service, une catégorie déclarée remplace ses clés.
Une clé locale null rétablit l’héritage. Modifier une catégorie commune exige
Update non limité à des fonctions. Le rapport `service_configuration` indique
si elle est préservée, appliquée, refusée ou d’issue inconnue. Une configuration
commune appliquée reste effective si l’import d’une fonction échoue ensuite.
Après une issue inconnue de modification commune, relire la configuration du
service avant une relance explicite ; la CLI ne répète pas cette mutation et
n’entame pas les publications de fonctions. Des coupures réelles avant traitement
et après commit qualifient ce comportement sur DEV.
L’API `/api/services/{id}/configuration` accepte `replace_secrets: true` avec
un mapping `secrets` explicite ; sans ce champ, les secrets se modifient par clé.
Les lectures ne renvoient jamais leurs valeurs enregistrées.

L’historique se lit sous `/api/functions/{id}/revisions`. Le rollback rétablit une révision connue sans rétablir les anciens réglages ni les volumes. La facette Code et révisions propose la publication d’un ZIP et de son handler, le suivi, l’abandon d’une préparation, l’activation et la suppression de révisions. Les réglages et secrets courants sont conservés côté serveur lors de cette publication du code. L’entrée publique est `/invoke/{function_id}` pour un alias implicite, ou `/invoke/{function_id}/{chemin}` pour un chemin déclaré. Elle exige Read dans `X-Serverless-Token` ; le cookie administrateur ne remplace pas ce jeton.

## Quotas, décisions et erreurs

Une fonction configure séparément données permanentes et cache, avec activation et allocation en Mio. Désactiver conserve les fichiers et l’allocation. Un quota sous l’usage est refusé ; une invocation admise interdit une mutation incompatible et les instances au repos sont drainées. Supprimer archive les volumes, sans les purger ni libérer leur allocation. La purge est une commande d’administration distincte dans Archives de fonctions ; le vidage du cache est dans la facette Stockage. La qualification transversale de ces commandes est recoupée dans SLS-065 et docs/evidence/storage-console-dev-2026-11-08.json.

Les commandes publiques utilisent un UUID d’opération et la version lue :
`POST /api/functions/{id}/cache-clear`, `POST /api/archives/{id}/purge`, puis
`GET /api/storage-operations/{id}`. Le vidage requiert Update ; la purge exige
une session administrateur et la confirmation du nom exact. Consulter le reçu
avant de rejouer une requête dont la réponse a été perdue. Une purge en attente
conserve les ressources comptées jusqu’à confirmation du nettoyage.

Une réponse normale attend confirmation de l’agent. Un 503 portant `X-Serverless-Mutation-Committed: true` signifie que la modification est enregistrée et attend sa confirmation : relire la fonction ou le candidat avant toute nouvelle tentative. `X-Serverless-Operation-ID` et `X-Serverless-Function-ID` identifient cette décision ; `storage_operation` expose son résumé public, puis revient à null après confirmation. Une publication déjà décidée reste publiée malgré une confirmation perdue.

Les mutations concurrentes incompatibles donnent 409, une configuration ou réduction de quota invalide 422, un budget/marge de stockage insuffisant 507. Les mises à jour supportent `If-Match` avec la valeur `updated_at` lue. Une interruption avant décision abandonne la préparation ; après décision, elle reprend sa confirmation. Une requête retardée ne recrée pas une préparation déjà abandonnée.

Les paramètres d’exécution sont appliqués par le moteur. File pleine ou expirée : 429 ; délai d’exécution dépassé : 504. Une déconnexion après admission ne prouve pas l’absence d’effet métier : consulter l’historique par X-Serverless-Request-ID avant toute relance. Les routes `/api/functions/{id}/instances` et `/api/functions/{id}/invocations` exigent Read ou la session administrateur, avec pagination. Les logs sont expurgés ; une mesure Docker indisponible reste signalée comme telle. Les contrats détaillés sont dans docs/CONTROL.md, DEPLOYMENT.md, ADMISSION.md et le manuel du dépôt.

## Retrouver une publication et consulter le guide

La console inscrit l’UUID du candidat dans son adresse avant d’envoyer la préparation. Après interruption réseau, fermeture ou rechargement, consulter cette même adresse avant de recommencer. Une préparation en attente d’archive peut être abandonnée explicitement ; le navigateur ne renvoie pas automatiquement le ZIP.

Supprimer une révision inactive demande confirmation. Un 503 peut signifier que sa suppression logique est enregistrée mais que le nettoyage physique attend encore ; relire l’historique. La révision active reste protégée et les révisions utilisées par une instance ne peuvent pas être supprimées.

Le manuel d’usage est accessible dans la navigation, à /console/manual. Il décrit les parcours disponibles, les droits, la publication, les révisions, les limites et le diagnostic. Sa source unique est `docs/manual.md`, construite et vérifiée avec la version de la console.

Pour une nouvelle commande de purge, le corps JSON strict exige operation_id
UUID et confirm_name texte de 1 à 63 caractères, égal au nom exact. Un corps
invalide donne 422 ; une version If-Match absente donne 428, périmée 409.
Ces refus n’entament pas la purge et ne créent pas son reçu. Les fichiers,
configuration et registres ont été recoupés avant/après les refus réels.
Un UUID déjà connu suit les règles de répétition corrélée : relire son reçu,
puis réutiliser ses paramètres initiaux si une répétition explicite est nécessaire.

## Adresses d’appel en qualification

SLS-066 lit la projection officielle des routes par le montage readonly
`/etc/spark:/spark:ro`. La facette Adresses d’appel et son lien depuis le
service affichent URL, méthodes et transport déclaré. La copie native propose
un emplacement de jeton, sans valeur réelle ; les erreurs retirent les
anciennes adresses. Le résultat CLI ajoute la même information après publication.
La console et le SSO gardent leur origine canonique.

Le checkpoint `docs/evidence/invocation-urls-checkpoint-dev-2026-11-08.json`
passe 88 groupes réels : huit API/CLI, six UI, 36 régressions et 38 groupes CLI Docker. Les 31 captures
sont recoupées ; le manuel à 14 chapitres et 43 paragraphes est compilé et
vérifié. Les neuf fonctions des essais/replays sont purgées et les 26 sources
Python/SQL embarquées recoupées. Ce checkpoint ne clôture pas l’unité.

La régression complète `docs/evidence/invocation-urls-regressions-dev-2026-11-08.json`
passe ensuite 35 campagnes et 467 groupes, zéro échec/skip. Six prérequis sont
non comptés ; 186 sources et images contrôle/CLI sont identiques avant/après
chaque phase. Les 32 fonctions suivies sont purgées dans dix namespaces ; les
deux restaurations historiques restent distinctes. Les 79 captures fraîches
sont recoupées : 61 observations et 18 identités SHA avec une référence inspectée.
Le contrôle et la référence sont sains, l’agent actif, les réservations et
allocations globales à zéro. Les archives historiques étrangères restent conservées.

La preuve native du Host est acquise en boucle locale. Restent les changements
réels de routes/TLS, seconde page sur six domaines et source perturbée.
Le GET CLI 401 après publication est qualifié séparément ci-dessous. Le build nominal CLI est
qualifié ; sa branche d’expiration/perte SSH reste à éprouver. SLS-066 demeure
ouverte. L’alias functions.lelabs.tech vers 18090 TLS est proposé dans routes.? ;
il n’est pas appliqué. Aucun nouveau secret, variable ou schéma ; la configuration
reste dans les deux fichiers de cellule. Ces trois notes sont proposées,
sans revendiquer leur adoption.


## Transport du catalogue après publication

Le complément `docs/evidence/invocation-url-transport-dev-2026-11-08.json`
passe trois nouveaux groupes puis treize de régression en série, zéro échec/skip.
Les deux vrais HTTP 502 du catalogue conservent la publication et ses UUID ;
six connexions HTTPS CLI sont comptées, sans rejeu. Après reprise, catalogue
et invocation Docker fonctionnent. Les 187 sources/images sont recoupées avant
et après chaque phase, huit fonctions purgées dans trois namespaces, six gardes
terminées et 26 fichiers embarqués conformes. La référence conserve son identité,
son image et son démarrage. Aucun changement produit, build du contrôle,
migration, variable, secret ou route appliquée pour ce complément.

Le refus 401 après publication est qualifié ci-dessous ; le 403 reste distinct. Les branches d’expiration,
sortie excessive, lancement et nettoyage après réponses de création/purge perdues
du nouveau client ne sont pas déclarées acquises. Le client exige la disparition
de tout le groupe CLI avant nettoyage et reprend une purge par son UUID conservé.
La preuve complète de 467 groupes reste distincte. SLS-066 demeure ouverte.


## Révocation avant le catalogue facultatif

La preuve `docs/evidence/invocation-url-refusal-dev-2026-11-08.json` passe
quatre groupes de transport puis treize de régression, soit 17, sans échec/skip.
La CLI est retenue avant sa sixième connexion ; le jeton révoqué par l’API donne
un vrai 401 sans changer la publication réussie ni ses UUID, avec six connexions
sans rejeu. Un autre Read retrouve le catalogue et invoque Docker. Les 188 sources
et images sont recoupées, neuf fonctions purgées dans trois namespaces, six gardes
terminées et 26 fichiers embarqués conformes. Le premier essai incomplet est
conservé séparément : barrière manquée de cause inconnue, deux fonctions et deux
gardes nettoyées. Aucun changement produit, migration, build du contrôle,
variable, secret ou route appliquée. Le 403, les pannes du pilote et les branches
de confidentialité/illisibilité du diagnostic restent non éprouvés. SLS-066
reste ouverte. Les trois notes sont proposées, sans revendiquer leur adoption.


## Retrouver une fonction et ses adresses

La console s’ouvre sur le catalogue Fonctions ; Namespaces ouvre la structure
à /console/namespaces. Rechercher, choisir Namespace/Service puis Appliquer,
filtrer l’état ou le tri. La query partageable conserve ces critères et la page ;
Revenir au catalogue les retrouve depuis les six facettes d’une fonction.
Le manuel d’usage affiché décrit ces parcours depuis sa source unique du dépôt,
avec quinze chapitres et 46 paragraphes vérifiés dans l’application.

GET /api/functions et les deux sélecteurs /api/catalogue/namespaces et
/api/catalogue/services exigent une session administrateur. Un logiciel utilisant
un jeton Read conserve sa liste GET /api/services/{id}/functions et le catalogue
d’adresses GET /api/functions/{id}/invocation-urls dans sa portée. Le catalogue
global ne recherche aucune variable, secret, source ni journal. L’invocation
conserve son URL par UUID et X-Serverless-Token ; l’authentification métier
Authorization reste transmise au handler.

Preuve DEV : docs/evidence/function-catalogue-dev-2026-11-08.json, 37 campagnes
uniques/489 groupes, deux époques de clients explicitement déclarées et mêmes
images produit. 98 captures inspectées ; aucune nouvelle variable, secret,
dépendance ou migration. Les routes restent celles de /etc/spark/routes ;
functions.lelabs.tech est proposé, sans application dans cette livraison.
