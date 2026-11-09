# P2Enjoy Serverless

Ce SPARK héberge la plateforme de fonctions Docker sur l’infrastructure de développement LeLabs.

## Services et accès

- https://serverless.lelabs.tech : console React et API Python, servies par `serverless-api` sur le port 18090 derrière la route TLS.
- `serverless-runtime-reference` : exécuteur des douze handlers synthétiques du dépôt, accessible sur la boucle locale du SPARK, port 18080.
- `p2enjoy-storage-dev.service` : agent de quotas et de volumes persistants par UUID de fonction, avec socket Unix privé.
- Les validateurs de code, instances de fonctions et clients de qualification sont des conteneurs distincts, identifiés par leur rôle et leur propriétaire.

## Fonctions disponibles

Le SSO LeLabs exige les rôles `verified` et `admin`. La console gère namespaces, services, fonctions, politiques d’origine/IP, variables, secrets et jetons CRUD limités au service ou à certaines fonctions.

L’adaptateur Python lit `serverless.yml`, prépare des archives et publie les fonctions par HTTPS. Le contrôle valide réellement le handler dans Node/Docker, conserve les révisions et fournit historique et rollback. Le rollback du code conserve les réglages applicatifs et les volumes courants.

Les créations, changements de quotas, publications et suppressions sont raccordés à l’agent réel. La décision durable du contrôle et l’objet sont commis ensemble. Avant cette décision, une interruption reprend l’abandon ; après, elle confirme la mutation. La suppression archive données et cache en conservant leur allocation. Leur purge est distincte.

## État de réalisation

Le moteur public exécute les fonctions publiées avec un jeton Read. Il réserve CPU, mémoire et place d’instance avant Docker, applique minimum/maximum/concurrence et extinction après inactivité, puis réconcilie ses ressources au redémarrage sans rejouer les appels incertains. Les générations de code et configuration conservent les appels déjà admis ; les changements de stockage drainent les instances au repos et refusent les invocations actives.

La passerelle applique les politiques d’origine/IP et CORS. Les API d’observation exposent états, allocations, mesures Docker et journaux expurgés. Les facettes Instances et Invocations montrent les allocations, mesures, états et journaux expurgés dans la fiche de fonction. La facette Code et révisions permet de publier un ZIP, suivre ou abandonner une préparation, consulter les métadonnées, activer et supprimer les révisions. Les commandes publiques de purge/cache et le catalogue d’archives sont déployés et qualifiés dans SLS-065. Les crons, cycles SSO et pannes résiduelles sont recensés dans le backlog.

Preuve moteur : `docs/evidence/execution-dev-2026-11-06.json` dans le dépôt du projet. Elle recoupe sources, image, rapports, archives, ressources web et configuration officielle. Les campagnes sont sérielles, sans mock, doublure ou test ignoré. Les archives de code conservées sont distinguées des volumes de qualification explicitement purgés.

La publication de code conserve côté serveur les ressources, variables, secrets, volumes et routes courants. Son UUID est connu avant l’envoi ; revenir sur la même adresse permet de consulter son issue sans rejouer la publication. La console relit l’état après une erreur de mutation et distingue une publication enregistrée dont la confirmation de stockage attend encore.

La qualification `python3 -B e2e/execution-suite.py --scope publication` passe 18 campagnes en série et 312 groupes réels, sans échec ni cas ignoré. Elle réunit moteur et console sans répéter les campagnes communes. La preuve `docs/evidence/publication-console-dev-2026-11-07.json` recoupe sources, image, rapports frais, captures relues, archives et ressources nettoyées. Les pannes de nettoyage sont éprouvées sur les seules révisions de campagne, avec garde indépendante puis maintenance normale.

Le manuel d’usage se consulte dans la navigation, à /console/manual. Ses quinze chapitres et 46 paragraphes viennent de l’unique source `docs/manual.md`, compilée avec chaque version de la console et mise à jour avec les comportements utilisateur. La campagne E2E compare le contenu rendu et son empreinte à ce fichier.

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
reste ouverte dans SLS-066.

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
