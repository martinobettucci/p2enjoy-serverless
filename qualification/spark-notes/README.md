# P2Enjoy Serverless

Ce SPARK héberge la plateforme de fonctions Docker sur l’infrastructure de développement LeLabs.

## Services et accès

- https://serverless.lelabs.tech : console React et API Python, servies par `serverless-api` sur le port 18090 derrière la route TLS.
- `serverless-runtime-reference` : exécuteur des douze handlers synthétiques du dépôt, accessible sur la boucle locale du SPARK, port 18080.
- `p2enjoy-storage-dev.service` : agent de quotas et de volumes persistants par UUID de fonction, avec socket Unix privé.
- Les validateurs de code, instances de fonctions et clients de qualification sont des conteneurs distincts, identifiés par leur rôle et leur propriétaire.

## Fonctions disponibles

Le SSO LeLabs exige les rôles `verified` et `admin`. La console gère namespaces, services, fonctions, politiques d’origine/IP, variables, secrets et jetons CRUD limités au service ou à certaines fonctions.

L’adaptateur Python lit `serverless.yml`, prépare des archives et publie les fonctions par HTTPS. Le contrôle valide réellement le handler dans Node/Docker, conserve les versions par hash et fournit promotion, historique et rollback. Le rollback du code conserve les réglages applicatifs et les volumes courants.

Les créations, changements de quotas, publications et suppressions sont raccordés à l’agent réel. La décision durable du contrôle et l’objet sont commis ensemble. Avant cette décision, une interruption reprend l’abandon ; après, elle confirme la mutation. La suppression archive données et cache en conservant leur allocation. Leur purge est distincte.

## État de réalisation

Le moteur public exécute les fonctions publiées avec un jeton Read. Il réserve CPU, mémoire et place d’instance avant Docker, applique minimum/maximum/concurrence et extinction après inactivité, puis réconcilie ses ressources au redémarrage sans rejouer les appels incertains. Les générations de code et configuration conservent les appels déjà admis ; les changements de stockage drainent les instances au repos et refusent les invocations actives.

La passerelle applique les politiques d’origine/IP et CORS. Les API d’observation exposent états, allocations, mesures Docker et journaux expurgés. Les facettes Instances et Invocations montrent les allocations, mesures, états et journaux expurgés dans la fiche de fonction. La facette Code et révisions permet de publier un ZIP, suivre ou abandonner une préparation, consulter les métadonnées, activer et supprimer les révisions. Les commandes publiques de purge/cache et le catalogue d’archives sont déployés et qualifiés dans SLS-065. Le moteur de planification et sa facette sont déployés ; leur qualification complète, les cycles SSO et les pannes résiduelles sont recensés dans le backlog.

Preuve moteur : `docs/evidence/execution-dev-2026-11-06.json` dans le dépôt du projet. Elle recoupe sources, image, rapports, archives, ressources web et configuration officielle. Les campagnes sont sérielles, sans mock, doublure ou test ignoré. Les archives de code conservées sont distinguées des volumes de qualification explicitement purgés.

La publication de code conserve côté serveur les ressources, variables, secrets, volumes et routes courants. Son UUID est connu avant l’envoi ; revenir sur la même adresse permet de consulter son issue sans rejouer la publication. La console relit l’état après une erreur de mutation et distingue une publication enregistrée dont la confirmation de stockage attend encore.

La qualification `python3 -B e2e/execution-suite.py --scope publication` passe 18 campagnes en série et 312 groupes réels, sans échec ni cas ignoré. Elle réunit moteur et console sans répéter les campagnes communes. La preuve `docs/evidence/publication-console-dev-2026-11-07.json` recoupe sources, image, rapports frais, captures relues, archives et ressources nettoyées. Les pannes de nettoyage sont éprouvées sur les seules révisions de campagne, avec garde indépendante puis maintenance normale.

Le manuel d’usage se consulte dans la navigation, à /console/manual. Ses quinze chapitres et52 paragraphes viennent de l’unique source `docs/manual.md`, compilée avec chaque version de la console et mise à jour avec les comportements utilisateur. La campagne E2E compare le contenu rendu et son empreinte à ce fichier.

L’agent de stockage dispose maintenant d’effacements corrélés : reçu durable,
répétition sans second vidage et reprise après erreur physique ou interruption.
Le schéma agent est 004. Sept campagnes et 106 groupes réels passent, avec
nettoyage recoupé : docs/evidence/storage-discard-dev-2026-11-07.json.
Ces opérations sont raccordées aux commandes publiques de cache/purge
et au catalogue d’archives. La suite commune passe 29 campagnes et 397 groupes,
puis neuf groupes API renforcés : quatorze corps invalides de purge, version
périmée et relevés natifs sans mutation. Les 28 fonctions des huit namespaces
publics sont purgées, les deux restaurations historiques sont séparées et les
72 captures recoupées. Preuve : docs/evidence/storage-console-dev-2026-11-08.json. La purge conserve les artefacts
tant que sa garde existe, y compris après redémarrage si le stockage a changé.

La configuration du provider est conservée dans le service ; les fonctions
portent seulement leurs surcharges. Les jetons restent gérés au niveau service.
Treize groupes ciblés couvrent héritage, secrets, droits, limites, échec partiel
et redémarrage. Avec les régressions et les clients Docker, la preuve
`docs/evidence/service-configuration-dev-2026-11-08.json` réunit 191 groupes
en série et 21 captures inspectées. Le complément
`docs/evidence/service-configuration-transport-dev-2026-11-08.json` ajoute cinq
groupes de vraies coupures et treize groupes de configuration rejoués, sur la
même image : `unknown` sans rejeu, état durable recoupé et relances publiées puis
invoquées dans Docker. SLS-031 est qualifiée. Le catalogue des adresses d’appel est déployé ; sa qualification multi-domaines
est qualifiée dans son complément six domaines ; les autres fautes maintiennent SLS-066 ouverte.

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
les autres fautes de source. Les pages sur six domaines sont qualifiées dans leur complément ci-dessous.
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


## Catalogue des fonctions qualifié

L’accueil authentifié est Fonctions, également disponible à /console/functions.
La recherche porte sur les métadonnées des fonctions et de leurs parents ; les
filtres Namespace/Service se cherchent et se paginent, avec état et tri. L’adresse
conserve le contexte et la page lors des passages par les six facettes. Namespaces
reste l’entrée de création et d’organisation, à /console/namespaces.

La preuve docs/evidence/function-catalogue-dev-2026-11-08.json réunit
37 campagnes uniques et 489 groupes réels : 447 conservés après vérification
des mêmes sources produit/images, puis 42 réexécutés sur les clients corrigés.
Les deux époques 196/197 sources, les essais incomplets et les six prérequis
restent distincts. Les 98 captures actives sont inspectées ; le manuel servi
correspond à 15 chapitres et 46 paragraphes. Les 91 fonctions suivies sont
purgées dans 23 namespaces, quinze configurations de service effacées et les
restaurations historiques recoupées. La référence conserve identité et démarrage.

Le titre ambigu d’une fiche déjà purgée est suivi dans SLS-075. Le catalogue
est qualifié ; favoris, lots, édition, client HTTP et versions par hash restent
au backlog. SLS-066 poursuit ses preuves de domaines : autorisation de console
du seul SPARK reçue ; son alias TLS est désormais appliqué, selon le complément ci-dessous.
Les trois notes sont proposées sans revendiquer leur adoption.


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
Les pages UI/CLI sur six domaines sont qualifiées dans leur complément ; les autres fautes de source restent ouvertes.

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
services sont inchangés. Le vide UI public et les pages UI/CLI sont qualifiés
par leurs compléments distincts. Les quatre alias temporaires, expressément
autorisés, ont été créés puis retirés après leur campagne. Les autres fautes de
source restent ouvertes.
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
Le parcours public vide et la pagination UI/CLI sont qualifiés par leurs
compléments distincts ; les fautes propres du pilote et les autres fautes de
source restent ouvertes.
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
client et les autres fautes de source restent à éprouver. Les pages sur six
domaines sont qualifiées dans leur complément distinct.
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
Services et fichiers officiels inchangés ; autres fautes de source et pannes
propres du client restent ouvertes. Les six domaines ont leur preuve distincte. Ces notes sont proposées sans adoption.


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
Aucune variable/secret, route/DNS ou build ajouté dans ce complément. Les
autres fautes restent ouvertes ; les six domaines ont leur preuve distincte. Notes proposées individuellement sans adoption annoncée.


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
helper CLI conteneurisé et la régression complète restent ouvertes ; SLS-074 demeure en cours.

Image du checkpoint008 avant nommage :178394abb337, référence007 retenue sous
before-function-version-promotions. Après migration008 commise, ne pas remettre
seule une ancienne image : une restauration exige base, artefacts et volumes
cohérents. La sauvegarde native privée avant008 est conservée sous
/srv/p2enjoy-serverless/qualification-history/.

Aucune variable, secret ou route ajouté ; les deux domaines TLS restent18090.
Configuration par les deux fichiers officiels de cellule, aucun .env, ENV/ARG ou
environment de configuration. Agent et runtime de référence sont conservés.
Les trois notes sont proposées individuellement ; leur adoption n’est pas revendiquée.


## Reprise de validation sous faute — quatre groupes qualifiés

La preuve docs/evidence/function-version-validation-recovery-dev-2026-11-09.json
passe quatre groupes sur248 sources : A/B admis, refus socket puis canal isolé,
B refusé avant validation et reprise normale sans redémarrer le contrôle. Le
canal est restitué par garde indépendante après SIGKILL du helper. Les deux
fenêtres Docker ne montrent que le create de A ; cinq invocations retrouvent
stable/pilote, configuration et données/cache. Deux fonctions d’essai/replay
sont purgées et leurs artefacts absents, deux helpers/gardes du replay terminés,
réservations et ressources actives à zéro. Le socket conserve inode/UID/GID/mode
après restitution. Les31 fichiers backend, images, démarrages et fichiers
officiels restent inchangés. Aucun build, variable, secret ou route nouveau.
Les arrêts de prérequis et du premier client restent distincts. Autres pannes
et régression complète restent ouvertes ; les trois notes sont proposées,
sans adoption revendiquée.


## Pagination réelle sur six domaines — complément qualifié

Le responsable autorise quatre alias temporaires functions-pagination-1 à4,
18090TLS, et leurs A exacts, puis leur retrait. La preuve
docs/evidence/invocation-pagination-dev-2026-11-09.json passe huit groupes de
cycle/UI/CLI, trois prérequis de garde distincts,14 invocations et sept JPEG
inspectés sur253 sources figées. La console montre cinq domaines puis un,
conserve le hash mobile et invoque les copies natives. La CLI parcourt ses
deux pages ; publication conservée après vrai401 ou changement réel entre
pages, sans adresses partielles ni rejeu.

Deux fonctions sont physiquement purgées, avec volumes/artefacts/canaux et
conteneurs/réseaux absents. Après SIGKILL réel du propriétaire, la garde retire
indépendamment les quatre routes et quatre A ; deux domaines permanents, DNS
et HTTPS restent inchangés. Contrôle/référence, démarrages, images,31 fichiers
backend et deux fichiers officiels de configuration sont conservés. Aucune
variable, secret ou construction d’image ajouté. L’essai DNS interrompu et
son retrait explicite restent distincts ; état de zone en transition corrigé
dans le banc. Les autres fautes maintiennent SLS-066 ouverte.
Ces trois notes sont proposées individuellement, sans adoption revendiquée.


## Noms des validateurs — SLS-076 qualifiée

Lors de la preuve076, le contrôle008 sert19cfe884642a et nomme ses validateurs
serverless-code-validator-UUID. L’ancien p2-v est repris par labels après
interruption réelle, sans redémarrer l’ancienne image avant la nouvelle.
Preuve : docs/evidence/validator-names-dev-2026-11-09.json. Quatre groupes
ciblés et36/12/5 régressions passent, soit57. Cinq appels conservent hash,
cible, configuration et compteurs données/cache1 à5. Trois fonctions du replay
sont physiquement purgées ; l’essai initial et sa fonction restent distincts.

Les31 backends ne diffèrent que par validator ; web compilé, runtime de
référence, fichiers officiels et routes sont conservés. La garde est armée
avant SIGKILL, puis la reprise réussit explicitement et timer/service sont
inactifs. Son expiration et sa propre perte ne sont pas revendiquées testées.
Les cinq pilotes maintenus de préparation à collecte sont sous e2e, selon
docs/VALIDATOR_NAMES.md. Les autres pannes et la régression complète008
restent au backlog. Aucun secret/variable/route nouveau ; ces trois notes
sont proposées individuellement, sans adoption revendiquée.


## Reprise des paquets identiques qualifiée

La preuve docs/evidence/function-version-duplicate-recovery-dev-2026-11-09.json
passe quatre groupes et cinq appels sur le contrôle008/image19cfe884. Les
paquets dédupliqués restent réservés sous EACCES jusqu'à leur effacement confirmé.
La maintenance reprend sans redémarrage ; un second cycle après commit reprend
par garde indépendante après SIGKILL du contrôle et du helper. Même conteneur
21545c4f et configuration, nouveau démarrage attendu le2026-11-09 à16:53:43UTC.
Données/cache1–5 conservés, fonction purgée physiquement et deux gardes terminées.
SLS-074 reste en cours pour les autres fenêtres et la régression complète.


## Gardes008 et image actuelle

Le contrôle courant serverless-api est e661516b, image def45648f9e7, démarré
2026-11-09T18:52:49.904838248Z. Seul le préfixe de première transition008 change
parmi31 backends ; le web reste identique. Dix groupes sur vraies copies007
qualifient refus et coupure WAL avant commit/reprise du même conteneur. La
bascule conserve les17 tables et le schéma déjà008 ; un backup SQLite natif
privé est conservé dans `qualification-history/migration008-deployment-backup-b6c39eaeb4c447f2a7aab719902f938c`. Ne pas restaurer automatiquement cette base.

Douze groupes API puis cinq CLI passent sur l'image servie,16 appels réussissent
et un refus attendu est conservé. Deux fonctions purgées physiquement, ressources
actives nulles, garde d'image désarmée et mutateur joint. Référence et fichiers
officiels/routes restent identiques. Preuve : docs/evidence/function-version-migration008-recovery-dev-2026-11-09.json. Les pertes propres des gardes, les autres interruptions et critères
restent dans SLS-074. Ces notes sont proposées
individuellement ; leur adoption n'est pas revendiquée.


## Purges historiques008 qualifiées

Preuve : docs/evidence/function-version-purge-migration008-dev-2026-11-09.json.
Vingt-deux groupes réels passent : quatre fenêtres006/007→008, volumes/artifacts,
une restitution indépendante après perte du pilote, puis trois refus avant
interruption. CacheNULL/connu, UUID/dates, registre deleted et anciens champs
recoupés ; quatre purges terminées, cinquième installation temporaire retirée
par garde. Les17 tables, le registre et5982 artefacts originaux sont conservés.

Le contrôle e661516b garde def45648, démarrage du checkpoint précédent2026-11-09T18:52:49.904838248Z.
Cinq gardes inactives, drivers et ressources temporaires absents, actifs nuls ;
référence, configuration et routes restent identiques. La source007 est conservée
sous p2enjoy-control:historical-schema-007 avec attestation root liée à la preuve
du registre. Aucun changement produit, migration supplémentaire, variable, secret
ou route. Les autres interruptions et critères restent dans SLS-074.
Notes proposées individuellement, sans adoption revendiquée.


## Corrélations de purge007 éprouvées

La preuve docs/evidence/function-version-purge-correlation008-dev-2026-11-09.json
passe42 groupes sur283 sources :40 refus transactionnels et2 témoins migrés008
puis redémarrés dans le même conteneur, depuis les vrais backups007 volumes/
artifacts. Snapshots007 exacts après refus, anciennes colonnes des16 tables et
registre deleted/hash/dates conservés après succès. Socket absent ensuite :
preuve de démarrage/migration, sans disponibilité HTTP de la copie.

Backups, WAL vides et SHM conservés ;42 conteneurs/copies retirés. Contrôle
e661516b/def45648, démarrage18:52:49UTC, référence,17 tables vivantes et fichiers
officiels inchangés, actifs nuls. Aucun déploiement/configuration/route nouveau.
Les autres interruptions et la campagne complète restent dans SLS-074. Ces notes restent proposées, sans adoption revendiquée.


## Première identité inconnue et restitution avec handler vivant

La [première identité inconnue](docs/evidence/function-version-unknown-first-dev-2026-11-09.json) passe17 groupes sur286 sources :
un témoin entièrement issu des API006, une variante de données anciennes déclarée
qui retire seulement deux métadonnées de A déjà supprimée dans la copie privée,
puis une restitution indépendante pendant un handler008 observé actif. Les vraies
images006→007→008 conservent pointeur B, UUID/dates et marqueurs ; le premier hash
resteNULL dans la variante, sans rétablir les droits Create. C pilote reste
invocable par hash, B demeure stable jusqu'à promotion explicite. Deux purges
publiques terminent ; la troisième installation temporaire est retirée par garde.
Les23 appels réussis recoupent configuration, secret par empreinte et compteurs
données/cache. Les originaux,17 tables et5982 artefacts sont conservés ; même
contrôle def45648/e661516b, nouveau démarrage attendu 2026-11-09T20:16:45.245982432Z. La garde indépendante
retire exactement une instance, un réseau et un bail par le vrai agent ; les trois
gardes sont inactives, ressources actives nulles. Les essais antérieurs restent
séparés du replay final. Les pannes propres de garde, autres interruptions et
la régression complète008 restent dans SLS-074, toujours[~].

Notes proposées seulement, sans adoption revendiquée. Le démarrage du checkpoint précédent
du contrôle est 2026-11-09T20:16:45.245982432Z ; la référence conserve son démarrage.


## Décisions de version sous perte de réponse

Les [réponses perdues des décisions de version](docs/evidence/function-version-state-transport-dev-2026-11-09.json) passent9 groupes
sur290 sources figées : promotion par la vraie CLI, archivage et suppression
avec remplacement, chacun avant traitement puis après décision avant réponse.
Les six SIGKILL sont constatés nativement et par Docker137 ; même conteneur/image
redémarrés, référence et fichiers officiels conservés. La CLI retourne unknown
avec exactement deux connexions HTTPS, sans rejeu. Avant traitement, métier
inchangé puis relance explicite ; après commit, pointeur/état/ETag/audit persistés
ensemble sans renvoi. Le delete est observé après sa tentative de nettoyage,
sans prétendre une interruption avant effacement physique.

Seize appels réussis retrouvent les handlers A/B, configuration, secret par
empreinte et compteurs données/cache1–16 après les reprises. Les réimports B
gardent hash et date initiale ; les premiers marqueurs restent immuables.
Une perte SIGKILL de l'observateur éprouve la garde indépendante sans mutation.
Les sept gardes et helpers sont terminés ; les six arrêts ont leurs reçus root.
Une fonction est purgée publiquement, volumes/artefacts et ressources actives
absents. Les deux bootstraps arrêtés avant garde restent archivés avec leurs
purges physiques, zéro groupe ajouté. Aucun produit/UI/manuel ni configuration
modifié ; la lecture sous-propriétaire recoupe les31 backends et le web.
SLS-074 reste[~] pour les autres interruptions et la régression complète008.

Démarrage courant du contrôle : 2026-11-09T20:51:15.542532163Z. Ces notes restent
proposées sans adoption ; configuration et routes inchangées.


## Première régression courante des publications008

La [première tranche de régression008](docs/evidence/function-version-publication-regressions-dev-2026-11-09.json) passe76 groupes sur292
sources figées :55 contrôles du vrai composant Docker et21 groupes HTTPS des
publications complètes/code seul. Le prérequis SSO réel reste distinct. Les huit
migrations, intégrité, verrou et refus de configuration sont conservés ; les11
et10 groupes de publication gardent droits, propriété, conflits, révocation,
import réel, abandon, course et pagination.

Upload et promotion sont distingués, y compris première promotion Create. Une
observation native recoupe deux candidats validating/réservés et le seul validateur
vivant du premier ; le doublon réutilise le hash et la révision canonique sans
changer la cible. Rollback et pilote sont réellement invoqués. Sept appels
recoupés en base vérifient hashes demandés/résolus, handlers et configuration.
Les cinq appels de code seul vérifient l’empreinte du secret ; les deux appels
de publication complète contrôlent sa présence puis son absence. Le compteur
POST reste1 lors des GET après promotion.

Quatre fonctions sont purgées par l'API publique, code/volumes/réservations absents
et parents supprimés. Les empreintes avant purge ne prétendent pas représenter
des archives encore conservées. Les5982 artefacts antérieurs et les services,
ID/images/démarrages, fichiers officiels et backend/web embarqués restent identiques.
Les anciens rapports restent préservés par SHA. Aucun build produit ni nouveau
parcours visuel ; les autres clients et la régression complète restent dans
SLS-074, toujours[~].

Au checkpoint précédent, ces notes étaient proposées ; contrôle relevé :
2026-11-09T20:51:15.542532163Z ; référence inchangée.

## Complément CLI/reprise du contrôle008

La tranche CLI et reprise008
passe 11 groupes réels sur 296 sources figées : sept déploiement/promotion CLI et
quatre plafonds/reprises. Le prérequis SSO réel reste distinct. Les 68 appels CLI
recoupent hash, UUID et présence du secret commun ; huit appels de reprise
comparent aussi marqueur, configuration et empreinte du secret. Vingt codes
réellement distincts remplissent le plafond ; un doublon est admis sans nouvelle
version ni changement de cible, un nouveau hash est refusé puis admis après retrait.

Deux SIGKILL du contrôle sont constatés nativement et par Docker137, en réception
partielle puis avec validateur Docker vivant lié au candidat, à son installation
et à l'image runtime configurée. La seconde perte du helper déclenche réellement
la restitution indépendante. Les candidats deviennent failed/control_interrupted,
sans réservation, configuration temporaire, code, validateur ou canal restant.
La cible stable, les premiers marqueurs et la configuration privée sont conservés ;
les uploads suivants restent pilotes jusqu'à promotion explicite.

Les 22 fonctions sont purgées publiquement dans deux namespaces ; 76 invocations
réussies uniques, dont 27 épinglées, sont recoupées en base. Helpers, timers et
services des deux gardes sont terminés. Les 5 982 artefacts antérieurs et fichiers
officiels restent identiques ; contrôle de même CID/image, démarrage attendu
2026-11-09T22:00:26.747122276Z, référence inchangée. Aucun build produit, changement
d'UI/manuel ni nouvelle preuve visuelle. Les autres clients, les pannes propres
du banc et la régression complète008 restent dans SLS-074, toujours [~].

## Complément invocation/stockage008

La tranche invocation/stockage008
passe 46 groupes réels sur 298 sources figées : 15 mutations de stockage et
31 invocations publiques. Le prérequis SSO reste distinct. Sept appels Echo
recoupent A pilote/promue, doublon malgré quota modifié, B pilote/promue et
rollback A. Quota7 Mio, reçu de stockage et fichiers données/cache sont conservés.
La confirmation indisponible conserve son vrai503 et sa décision acquise.

Pendant un handler A observé actif, publier B ne déplace pas la cible. Après
promotion B, retirer A empêche ses nouvelles admissions tout en laissant finir
son instantané ; le nettoyage reste en attente puis efface A après libération.
Les31 groupes conservent ACL, HTTP/Lambda, politiques origine/IP, files, minima,
quotas, concurrence, budgets réels, contention SQLite, arrêts et réceptions bornées.
Le plafond d'instances est appliqué puis restitué par la console du seul SPARK.

La collecte recoupe 85 handlers succeeded, dont78 publics et7 Echo ; deux réponses
métier non2xx et un succès après déconnexion restent classés selon l'état durable.
Les107 réponses publiques comprennent16 UUID avant réservation. Le vrai502 du
proxy sans UUID est lié par l'identité locale de sa connexion au témoin natif
running puis au même appel interrupted ; son statut durable503 reste distinct.

Les18 fonctions finales sont purgées par les API. L'essai initial avait passé
46 groupes mais échoué à la collecte de ce502 ; il reste séparé et ne s'ajoute
pas au total. Ses18 fonctions sont également purgées : les36 sont recoupées
physiquement dans quatre namespaces. Les5 982 artefacts antérieurs, fichiers
officiels, images, backend/web et référence sont conservés. Les budgets consommés
sont rétablis à32 instances,1 CPU et8 192 Mio, sans garde active. La recréation
attendue du contrôle change son CID et son démarrage, pas son image.

Les sources exécutables du replay restent celles livrées ; seules les deux
pages de contrat reçoivent les résultats dans l'index de sources. Les opérateurs
historiques conservent leurs limites. Aucun nouveau parcours visuel ni changement
produit/UI/manuel ; console, historique et régression complète008 restent ouverts.
SLS-074 conserve [~].

Notes toujours proposées, sans adoption implicite.

## Planifications — checkpoint du 10 novembre 2026

Les crons du manifeste de la version promue sont déclenchés par fenêtres UTC
de cinq minutes, avec réclamation et historique durables, sans rejeu. La facette
Planifications affiche prochains créneaux et résultats. Le checkpoint corrigé
passe six groupes réels, plus huit du manuel et huit publics. SLS-078 reste en
qualification pour promotions, interruptions, recouvrement, saturation,
rétention et états de console complémentaires. Le manuel affiché est recoupé
à sa source : seize chapitres et 56 paragraphes.
