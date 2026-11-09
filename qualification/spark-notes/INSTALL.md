# Intégration avec P2Enjoy Serverless

Entrée HTTPS : https://serverless.lelabs.tech. La console utilise le SSO LeLabs, client confidentiel `p2enjoy-serverless-dev`, retour `/auth/retour`. Les rôles `verified` et `admin` sont exigés côté serveur. Les secrets OIDC et jetons du fournisseur restent côté serveur.

## Accès des projets

Un administrateur crée un namespace, un service puis des jetons de plateforme. Les clients utilisent `X-Serverless-Token`. Le droit Create permet une création, première publication et première promotion de ce hash ; Update permet les modifications et versions suivantes ; Delete supprime une fonction. Read permet les lectures autorisées et les invocations, quelle que soit leur méthode HTTP. Une portée par fonction interdit les opérations globales du service.

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

Le catalogue se lit sous `/api/functions/{id}/versions`, les alias historiques sous `/revisions`. Code et révisions propose publication, promotion, archivage, restauration, suppression et réimportation explicite par hash. Les réglages et secrets courants sont conservés côté serveur lors de cette publication du code. L’entrée publique est `/invoke/{function_id}` pour un alias implicite, ou `/invoke/{function_id}/{chemin}` pour un chemin déclaré. Elle exige Read dans `X-Serverless-Token` ; le cookie administrateur ne remplace pas ce jeton.

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

Supprimer une version demande confirmation. La cible courante exige remplacement disponible ou désactivation explicite. La suppression retire les nouveaux appels ; le nettoyage physique attend les consommateurs déjà admis. Relire le catalogue et son état de nettoyage avant réimportation.

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

La preuve native du Host est acquise en boucle locale. Le couple de domaines TLS, son retrait d’alias et ses détours sont vérifiés ; restent
seconde page sur six domaines et source perturbée.
Le GET CLI 401 après publication est qualifié séparément ci-dessous. Le build nominal CLI est
qualifié ; sa branche d’expiration/perte SSH reste à éprouver. SLS-066 demeure
ouverte. L’alias functions.lelabs.tech vers 18090 TLS est appliqué par la
console normale du seul SPARK ; son certificat et sa résolution native sont vérifiés. Aucun nouveau secret, variable ou schéma ; la configuration
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
functions.lelabs.tech est maintenant appliqué dans le complément distinct ci-dessous.


## Deux domaines TLS — complément SLS-066

https://functions.lelabs.tech et https://serverless.lelabs.tech visent désormais
le port 18090 du même contrôle. La console et le SSO gardent leur domaine
canonique serverless.lelabs.tech. Le DNS A exact de functions et sa route TLS
sont posés par la console normale autorisée ; les deux HTTPS sont vérifiés
sans substitution de DNS ni contournement de certificat. La projection officielle
porte les deux lignes, lisibles depuis le montage readonly du contrôle.

Les huit groupes API/CLI et six parcours UI passent sur les deux domaines :
publication, appels Docker des adresses émises, droits, chemins/méthodes,
révisions et rollback. Leurs quatre fonctions sont purgées dans deux namespaces
et recoupées nativement. Sources de preuve :
docs/evidence/invocation-domains-dev-2026-11-08.json. Ce complément ne clôture
pas SLS-066. Les cinq cycles ultérieurs qualifient retrait, détours et API locale
vide local ; le complément UI ci-dessous qualifie le parcours public vide.
Source perturbée et pages UI/CLI sur six domaines restent ouvertes.

La première déclaration est conservée comme interrompue pendant une comparaison
trop stricte de applied_at ; sa reprise en lecture seule vérifie les propriétés
matérielles inchangées et les vrais HTTPS, sans second POST. Le premier départ
API sur session expirée est également conservé, avant création de ressources ;
le replay utilise une nouvelle connexion SSO réelle. Aucun nouveau secret,
variable, schéma ou build du contrôle. Les notes sont proposées sans adoption.


## Garde vérifiée avant perturbation

Les trois déclencheurs de garde passent sur la résolution native rétablie :
restauration explicite, SIGKILL du seul pilote avec restauration indépendante,
et échéance avec pilote vivant. Chaque scénario confirme les deux HTTPS et la
fin de la garde. Les ports restent à 18090 ; aucun détour, retrait ou
rétablissement d’alias n’est qualifié par ces trois groupes.

La première échéance échouée et son diagnostic DNS restent conservés séparément.
Après expiration du cache négatif en amont, les deux domaines résolvent
nativement vers l’adresse attendue ; aucune adresse ni aucun résolveur n’est
forcé dans les tests. Preuve : docs/evidence/invocation-route-guard-dev-2026-11-08.json.
Les perturbations réelles passent les cinq cycles ci-dessous ; le parcours public vide est qualifié ci-dessous, les fautes de source restent à éprouver.
Aucune nouvelle variable, secret, route ou image applicative dans cette étape.
Ces trois notes restent proposées, sans adoption revendiquée.


## Cinq cycles réels des routes — 9 novembre

Cinq groupes sérialisés passent sur 203 sources inchangées et les mêmes images :
pages API de taille un et appels des deux domaines, détour de l’alias,
restauration indépendante après SIGKILL du pilote, retrait/rétablissement de
l’alias et détour des deux routes avec catalogue HTTP local réellement vide.
Sept appels exécutent le handler Docker depuis les URL émises. Les quatre gardes
sont terminées, la fonction est purgée dans son namespace et ses parents supprimés.
Les deux routes sont rétablies à 18090 TLS ; la recréation renouvelle l’identifiant
de l’alias. Preuve : docs/evidence/invocation-route-cycles-dev-2026-11-09.json.

Aucun build, variable ou secret ajouté ; les deux fichiers officiels et les
services sont inchangés. Le vide UI public est qualifié ci-dessous ; les fautes
de source et la seconde
page UI/CLI restent ouverts. Les quatre alias temporaires de pagination sont
une proposition locale en attente d’autorisation, sans création DNS ni route.
Ces trois notes sont proposées individuellement, sans adoption revendiquée.


## Pause et reprise natives — deux groupes qualifiés

Le vrai GET HTTPS est retenu après recvfrom puis libéré. Il survit aussi au
SIGKILL du traceur, avec confirmation de reprise par le programme indépendant. Les deux groupes passent sur 205 sources ;
la même requête termine à 200 avec deux domaines, sans mesure de sa fin par
rapport au SIGCONT de garde. Le timer déjà collecté est
reconnu uniquement par son absence/inactivité natives. L’essai initial arrêté
et le diagnostic restent distincts du replay. Deux fonctions sont purgées dans
deux namespaces ; quatre helpers et quatre paires timer/service sont terminés.
Contrôle non tracé, PID/démarrage/images et configuration officielle inchangés.
Preuve : docs/evidence/invocation-request-pause-dev-2026-11-09.json.
Aucune route, DNS, variable, secret ni build nouveau dans ce complément natif.
Le parcours public vide est qualifié ci-dessous ; fautes propres du pilote, source
et pagination UI/CLI restent ouverts.
Ces notes sont proposées, sans adoption revendiquée.


## Catalogue public vide — trois groupes qualifiés

Création/publication depuis l’accueil par les formulaires, vrai GET du bouton
Actualiser retenu pendant détour normal des deux routes vers 18091, puis réponse
200/source disponible/total zéro. Les cinq JPEG sont inspectés : aide vide utile
sans URL/copie sur desktop et mobile, retour lisible des deux domaines après
restauration 18090 TLS. L’adresse copiée invoque réellement le handler Docker.
Trois groupes passent sur 206 sources et les mêmes images. Une fonction est
purgée dans son namespace ; helper natif, timer/service et garde de routes sont
terminés. Contrôle non tracé et sans redémarrage, référence/configuration inchangées.
Preuve : docs/evidence/invocation-empty-ui-dev-2026-11-09.json.
Aucun domaine/DNS, variable, secret ni build nouveau. Les erreurs propres du
client, les fautes de source et les pages sur six domaines restent à éprouver.
Ces notes sont proposées individuellement, sans adoption revendiquée.


## Alias public et vrai SSO — trois groupes qualifiés

L’alias redirige accueil/login/console vers la canonique sans y poser de cookie ;
son API session anonyme reste à 200 sans redirection. Les contextes desktop et
mobile entrent par son accueil, se connectent au vrai SSO puis se déconnectent
par l’UI. Le même POST réel est observé par CDP durable : 200, signed_out et
sso_signed_out vrais. Trois groupes passent sur 207 sources et les mêmes images ;
six captures sont inspectées. Deux sessions/flows du replay sont fermés, plus
les deux autres des essais arrêtés conservés séparément. Aucun cookie de reprise
nominal, donnée métier, route, DNS, variable, secret ou build nouveau.
Preuve : docs/evidence/invocation-alias-entry-dev-2026-11-09.json.
Services et fichiers officiels inchangés ; fautes de source, six domaines et
pannes propres du client restent ouverts. Ces notes sont proposées sans adoption.


## Garde des permissions du relevé — trois groupes

Le seul fichier officiel de routes subit chmod 000, puis le contrôle constate
réellement errno 13. Les trois scénarios release/SIGKILL/SIGSTOP passent sur
210 sources, mêmes images. Signaux noyau observés, copies figées et reçus
immuables ; trois helpers/timers/services terminés. Nom/inode/contenu/uid/gid,
mode 0640 et mtime restitués ; ctime change comme attendu. Deux HTTPS sains et
services/démarrages inchangés. Preuve :
docs/evidence/invocation-source-guard-dev-2026-11-09.json.
Aucun workload, route/DNS, variable, secret ou build nouveau. Reçus/programmes
de preuve et verrou privés sous /run ; aucun daemon permanent. Les refus API/UI
restent à qualifier. Ces notes sont proposées, sans adoption revendiquée.


## Catalogue sous refus de lecture — quatre groupes API

Quatre groupes réels passent sur 211 sources et les mêmes images. Publication
par adaptateur, errno 13 du contrôle, diagnostic source_forbidden borné pour
Read/admin et six refus sans diagnostic. Les deux URL connues exécutent Docker
pendant la faute ; restitution explicite puis même catalogue et deux appels.
Quatre invocations et une fonction purgée sont recoupées, helper et unités finis.
Source d’origine au mode 0640, contenu/inode/mtime inchangés ; ctime changée.
Preuve : docs/evidence/invocation-source-api-dev-2026-11-09.json.
Aucun ajout de variable/secret, changement route/DNS, service ou build. Le rendu
UI et les autres fautes restent ouverts. Notes proposées sans adoption annoncée.


## Refus de lecture dans la console — trois groupes navigateur

Trois groupes réels passent sur 212 sources et les mêmes images, depuis
l’accueil/formulaires/publication jusqu’à source_forbidden puis reprise.
Alerte utile desktop/mobile, anciennes adresses/copies/succès absents ; cinq
JPEG frais. Après restitution explicite, une URL copiée invoque Docker.
Une invocation, une fonction purgée et garde finie recoupées nativement ;
parents supprimés, mode 0640 et source/configurations/services inchangés.
Preuve : docs/evidence/invocation-source-ui-dev-2026-11-09.json.
Aucune variable/secret, route/DNS ou build ajouté. Autres fautes/six domaines
restent ouverts. Notes proposées individuellement sans adoption annoncée.


## Identité canonique du paquet — composant qualifié

Bibliothèque function_code_hash.py et CLI Docker d’extraction : sept groupes
ciblés, 45 de régression et neuf invocations réelles sur 222 sources. Contextes
de build limités et prouvés, deux essais arrêtés conservés séparément. Dix-neuf
conteneurs runtime, 37 clients nommés et leurs canaux sont absents. Douze fonctions supprimées
et volumes purgés ; 33 archives de code conservées vérifiées.
Preuve : docs/evidence/function-code-hash-dev-2026-11-09.json.
Aucune variable/secret ou route/DNS ajouté. Services et configuration officiels
inchangés ; seules les images calcul/packaging sont reconstruites. L’API garde
son comportement actuel ; déduplication/promotion/appels par hash restent en cours.
Notes proposées individuellement, sans adoption revendiquée.

Sept groupes rejoués après nommage explicite ; 45 conservés aux clients inchangés,
deux époques de 222 sources et mêmes sources produit/images.


## Registre007 de l’identité du code — historique

La migration 007 et le cache code_hash sont déployés. Les alias UUID historiques
et la cible courante sont conservés ; le premier backfill reconnaît aussi les
purges 006 décidées et fortement corrélées, sans inventer de hash ni retirer les
compteurs/gardes avant leur nettoyage normal. La carte Code et révisions montre
et copie le hash complet. GET /api/functions/{id}/versions fournit une lecture
Read/admin groupée et paginée, sans code ni secrets. À ce checkpoint007, les uploads activaient encore
leur révision. Le checkpoint008 ci-dessous décrit le fonctionnement actuel.

Preuve : docs/evidence/function-version-registry-dev-2026-11-09.json. 359 groupes
sur deux époques de 233 sources aux mêmes fichiers produit et image, dont 46 ciblés
et historiques et 313 communs. 69 captures recoupées : 47 nouvelles inspections,
22 références SHA identiques. Le manuel servi correspond à 15 chapitres et
47 paragraphes. L’ancien checkpoint au repos 328 reste distinct. Le premier arrêt
WAL, son nettoyage natif et le replay 15 groupes du poller sont conservés séparément.
Les six fonctions du registre sont purgées dans six namespaces recoupés ; les
régressions ont leur propre nettoyage dans leurs rapports.

Image de ce checkpoint007 : fe75c9e7, conservée aussi sous
p2enjoy-control:purge-recovery-reference. La référence 006 est reconstruite depuis
le vrai Git f56d79e, vérifiée et conservée sous historical-schema-006. Vérifier
l’image effectivement portée après build/up ; si up garde l’ancien conteneur,
recréer explicitement le seul contrôle par Compose, avec les deux env-file
officiels, puis confirmer image/santé. Après 007 commise, le retour à une image
antérieure exige base/fichiers/volumes cohérents ; après rollback de 007 refusée,
reprendre 006 sur la même base préserve les décisions déjà prises.

Aucune variable, secret ou route ajouté. Les deux domaines TLS restent sur 18090.
Les fichiers officiels, l’agent et le runtime de référence sont conservés ; aucun
daemon permanent nouveau. Les trois notes sont proposées individuellement,
sans revendiquer leur adoption. Configuration par les deux fichiers de cellule ;
aucun .env, ENV/ARG ou environment de configuration ajouté.


## Pilote et promotion explicite

`deploy --code-only --config serverless.yml --service UUID_DU_SERVICE` publie
seulement le code de fonctions existantes, sans résoudre ni modifier le provider.
`python3 -m adapter promote --function UUID --code-hash HASH` choisit la cible
sans tag ; Read et Create première promotion, sinon Update, sont requis.
L’invocation épinglée est /invoke/UUID@HASH, suivie du chemin déclaré.
Le hash est complet,64 hexadécimaux minuscules ; inconnu/archivé/supprimé est
refusé sans repli. X-Serverless-Code-Hash indique le code réellement admis.
Le catalogue /api/functions/UUID/invocation-urls?version=HASH calcule ses URL
depuis les seules routes officielles du SPARK. Les mutations incertaines ne
se rejouent pas automatiquement ; relire candidat, catalogue et fonction.


## Versions par hash — checkpoint ciblé008

Le contrôle008 prépare une version sans la promouvoir. L’upload identique
réutilise son hash disponible et sa date ; un hash archivé se restaure
explicitement, un hash supprimé se réimporte avec son ZIP validé. Promouvoir
choisit la cible des appels sans tag ; les pilotes utilisent le hash explicite.
Le rollback de code conserve ressources, variables/secrets et volumes courants.
Les appels déjà admis terminent avec leur snapshot ; les pools des versions
partagent les budgets et limites de leur fonction.

La preuve docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json
réunit71 groupes :2 migration/reprise,12 API,5 CLI authentifiés depuis le poste,
6 UI,8 manuel et38 packaging/refus dans les images CLI. Les28 captures sont
inspectées ; manuel15 chapitres/52 paragraphes. Dix fonctions sont purgées,
les dossiers d’artefacts absents et les ressources actives à zéro. Les31 fichiers
Python/SQL backend sont identiques entre époques API/CLI/UI. Les preuves007
ci-dessus restent historiques. Le complément CLI authentifié passe désormais
cinq groupes par image, vingt commandes et douze invocations sur245 sources :
docs/evidence/function-version-cli-images-dev-2026-11-09.json. Deux nouvelles
fonctions sont purgées ; aucun client, réseau/volume ou définition Compose
résiduel. Le premier lanceur direct est remplacé par Compose DEV pour lire les
valeurs citées des deux fichiers officiels, qui ne changent pas. Les pannes du
helper et la régression complète restent ouvertes ; SLS-074 demeure en cours.

Image contrôle courante :178394abb337, référence007 retenue sous
before-function-version-promotions. Après migration008 commise, ne pas remettre
seule une ancienne image : une restauration exige base, artefacts et volumes
cohérents. La sauvegarde native privée avant008 est conservée sous
/srv/p2enjoy-serverless/qualification-history/.

Aucune variable, secret ou route ajouté ; les deux domaines TLS restent18090.
Configuration par les deux fichiers officiels de cellule, aucun .env, ENV/ARG ou
environment de configuration. Agent et runtime de référence sont conservés.
Les trois notes sont proposées individuellement ; leur adoption n’est pas revendiquée.
