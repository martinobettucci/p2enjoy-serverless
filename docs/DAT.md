# Architecture technique

## Plateforme

Le [complément SSO SLS-089](SSO_SESSION_RECOVERY.md) réutilise le seul contrôle
et ses sessions chiffrées. La page publique d'attente ne monte aucun client de
session. Le renouvellement pending reste dans le cipher existant, sans nouvelle
table, variable ni service ; toute autorisation exige sa validation réelle.
Les corrections sont implémentées, leur qualification est encore ouverte.

Contrat de réalisation : [PLATFORM.md](PLATFORM.md). Le contrôle retenu est
Python avec SQLite WAL local et un seul processus de coordination ; les
transactions de réservation sont courtes et ne contiennent aucun appel Docker.
L'interface est React/Vite. Les instances Docker appartiennent au
contrôle par labels et sont réconciliées au démarrage. Le quota logique par
volume est développé dans `storage/`, avec go-fuse v2.12.1 (BSD-3-Clause,
release du 21 octobre 2026). Le proxy conserve les fichiers natifs et couvre
leurs chemins de mutation ; le contrat précis est dans PLATFORM, stockage.
Go sert uniquement à ce composant système. Son binaire statique se construit
dans Docker et s'exécute sous `spark-docker` pour fournir un montage au démon
rootless. Le montage direct sous spark-docker avec CAP_SYS_ADMIN dans la
cellule est qualifié ; les workloads Docker n'ont aucune capacité. Le helper
fusermount3 de cette cellule ne conserve pas son descripteur au passage exec.
Le composant passe 31 contrôles réels : [preuve](evidence/storage-dev-2026-11-05.json).
L’agent Python standard `storage/agent.py` supervise maintenant ce proxy, avec
registre WAL, générations, baux, sondes bornées et socket Unix authentifié par
UID. Il possède seul la capacité de montage et partage le namespace de la
cellule ; le code installé reste possédé par root. Les opérations locales et
la maintenance sont décrites dans [STORAGE_AGENT](STORAGE_AGENT.md). Son
raccordement aux instances passe quatorze groupes réels. Les mutations de
gestion, publication et admissions publiques utilisent maintenant l’agent ;
le moteur public est déployé en qualification.
L'agent prépare aussi les mutations de quotas en deux phases : l'ancienne
allocation reste réservée jusqu'à commit/abort et un reçu versionné survit aux
interruptions. Seuls les chemins nouveaux restés vides peuvent être retirés à
l'abandon. `function_operations` (migration 004 du contrôle) persiste la
décision de chaque mutation publique et sa version de stockage avant envoi.
La maintenance confirme commit/abort après interruption, sous le verrou unique
d’installation. Le protocole et ses reprises sont définis dans [ADMISSION](ADMISSION.md)
et vérifiés par la [preuve des mutations publiques](evidence/function-storage-dev-2026-11-06.json).
Les répertoires supprimés encore ouverts restent comptés jusqu'à Releasedir.
Les copies avec repli noyau passent par les écritures contrôlées du proxy.

Le contrôle et l'interface initiale sont déployés en DEV, avec 19 groupes API
administrateur et onze parcours UI qualifiés dans la [preuve de gestion](evidence/control-management-dev-2026-11-06.json).
Le banc décrit ci-dessous reste déployé à côté
du contrôle ; les montages de preuve sont nettoyés. La CLI Python de
plan/packaging passe 24 scénarios ciblés dans Docker ; le chargeur Node passe
36 scénarios réels. L'extracteur ZIP passe 112 contrôles réels, avec une
preuve indépendante des contenus et le chargement des douze fonctions.
La publication des révisions est intégrée au contrôle DEV, avec onze groupes API
et sept groupes CLI authentifiés qualifiés, puis quatre groupes de plafonds et
de reprise après interruption. Le pilote d’instances chaudes est raccordé aux admissions et à la passerelle
déployées en qualification.

La compilation du stockage utilise Go 1.27.3 dans une image épinglée. go-fuse
v2.12.1 et x/sys v0.28.0 sont verrouillés avec go.sum. L'audit govulncheck v1.9.0
relève zéro vulnérabilité atteignable et zéro paquet importé affecté. L'avis
GO-2026-5024 du module x/sys concerne uniquement Windows ; ce composant est
Linux. Résultat complet : [audit](evidence/storage-dependencies-2026-11-05.txt).

### Client de publication

Le [registre d’identité de code](FUNCTION_VERSION_REGISTRY.md) raccorde le
calculateur commun au contrôle : cache immuable dans chaque révision (migration
007), reprise des inventaires antérieurs avant admission HTTP et regroupement
des alias historiques pour la lecture Read. Le contrôle conserve un seul état
SQLite et ses UUID ; aucun service supplémentaire. Les nouvelles publications
calculent leur identité sur l’extraction et l’image réellement validées. La
console affiche et copie le hash, distinct de l’empreinte ZIP. Le pointeur actif
reste celui du comportement actuel jusqu’au checkpoint de promotion explicite.
Pour le premier passage depuis 006, la correction qualifiée reconnaît
la seule purge déjà décidée dont commande, garde, installation et versions
concordent. Son identité reste inconnue et ses compteurs sont conservés jusqu’à
la fin normale du nettoyage ; les autres inventaires absents restent refusés.
Le [banc de reprise](FUNCTION_VERSION_PURGE_UPGRADE.md) distingue le refus réel
de l’image précédente, les upgrades retenus dans volumes/artifacts et les
contre-exemples sur copies privées de la véritable base intermédiaire.
La [preuve finale](evidence/function-version-registry-dev-2026-11-09.json)
passe 359 groupes et recoupe les 69 captures, le manuel compilé et le nettoyage.
Le checkpoint au repos antérieur reste dans sa propre époque de qualification.

`adapter/deploy.py` utilise HTTPS de la bibliothèque standard avec validation
TLS et sans suivi des redirections. Le packaging et les corps JSON sont
vérifiés avant mutation ; les valeurs résolues restent en mémoire. Chaque
archive est relue sans suivre les liens puis comparée à son empreinte avant
envoi. Les fonctions sont publiées en série, les identifiants connus sont
conservés dans le rapport et les mutations ne sont jamais rejouées automatiquement.
Les refus locaux et un refus HTTPS 401 passent 14 contrôles réels ; la campagne
positive, les résultats partiels et la pagination passent sept groupes avec
la vraie session SSO : [preuve authentifiée](evidence/deployment-authenticated-dev-2026-11-06.json).

Le provider du manifeste est conservé comme configuration du service ; les
fonctions portent leurs seules surcharges. L’adaptateur applique les catégories
communes déclarées avant les publications et en indique le résultat séparément.
Le contrôle utilise une fusion unique pour la gestion, les validations et
l’admission des invocations. Il vérifie les configurations effectives dans la
transaction avant une mutation de service ou de fonction. Aucun schéma SQLite
ne change ; le remplacement du jeu de secrets réutilise son mapping chiffré.
Contrat et limites des échecs partiels :
[configuration commune](SERVICE_CONFIGURATION_URLS.md#configuration-de-service-et-surcharges).
La [preuve](evidence/service-configuration-dev-2026-11-08.json) recoupe 191 groupes,
les sources embarquées dans les deux images et 21 captures inspectées.
Le [complément natif](evidence/service-configuration-transport-dev-2026-11-08.json)
éprouve les vraies coupures avant traitement et après commit sur ce même contrôle,
sans changement du produit : cinq groupes puis treize groupes rejoués, avec
`unknown`, absence de rejeu et relances explicites publiées/invoquées dans Docker.

### Validation du code

Le pilote Python `control/app/validator.py` utilise uniquement la bibliothèque
standard pour Docker HTTP et son serveur Unix privé. Le runtime Node épinglé
reste sans dépendance ajoutée : import dynamique, hook natif de format et IPC.
Le contrôle crée le socket dans un répertoire 0700 monté readonly, puis le
superviseur Node retire sa configuration et renvoie un résultat explicite.
Les valeurs applicatives ne figurent pas dans l'environnement Docker.

Un enfant importe le code via `runtime/loader.mjs`, partagé avec le pilote
d’invocation. Les logs sont drainés, bornés, expurgés en conservant les positions
brutes avant troncature, puis convertis en UTF-8 borné. L'échéance extérieure
de quinze secondes englobe création, démarrage et import. Le pilote ferme
les connexions et supprime le conteneur avec ses descendants avant de conclure.
La preuve porte sur le chargement et ses pannes. Les droits de publication
et la réconciliation d'un contrôle interrompu disposent de campagnes API
distinctes, recensées avec leurs limites restantes dans le backlog.

### Instances d’exécution

`control/app/instances.py` utilise Docker HTTP et un canal Unix privé authentifié.
Le superviseur chaud lance un enfant neuf par appel, retire ses descendants,
puis le pilote compare les processus à l’inventaire initial. Une deadline
monotone partagée couvre l’import et l’exécution ; le contrôle refuse aussi un
résultat reçu après cette échéance. Les corps privés sont encodés en base64
pour borner l’expansion JSON. Les logs partagent l’expurgation du validateur.

Un verrou coordonne démarrage et fermeture. Les opérations système sont
rejointes malgré les annulations répétées ; la suppression Docker et réseau
est vérifiée avant retrait du canal. Un défaut de suppression garde l’état de
nettoyage dégradé et peut être repris. Un second démarrage refusé conserve
l’instance existante. Le diagnostic lit et écrit sans bloquer la boucle async.

Le contrat complet est [EXECUTION](EXECUTION.md). Les preuves du pilote portent
sur Docker réel, processus, mémoire/PIDs, réseau et courses ; elles ne qualifient
pas les admissions, générations, volumes ni routes publiques. Les
mesures proviennent de Docker stats, pas de l’allocation déclarée.

### Coordination et entrée publique

`control/app/execution.py` garde une réservation SQLite (migration 005) avant
Docker et avant acquisition de bail. Toutes ses instances, y compris en
drainage, comptent dans les budgets. Une tâche conserve chaque invocation
admise jusqu’à sa finalisation durable et sa fermeture ou remise au repos.
La notification de début du handler est persistée avant acquittement.

`invocation_routes.py` applique le jeton Read et la politique du service ;
`invocation_http.py` porte les normalisations et l’enveloppe Lambda. L’attente
ne conserve les corps qu’en mémoire, avec délai et plafonds globaux/par fonction.
La génération privée combine révision et configuration effective ; les
appels admis gardent leur instantané. Les observations paginées distinguent
réservations et mesures Docker, sans exposer cette génération ni les secrets.

Au redémarrage, le contrôle retire ses conteneurs et réseaux, libère les baux
et nettoie les canaux avant restitution des réservations. Les appels perdus
deviennent interrompus sans rejeu. Le contrat complet, dont les limites du
transport HTTP/1.1 de l’entrée DEV, est dans [ADMISSION](ADMISSION.md).

### Extraction des artefacts

`control/app/artifacts.py` lit le ZIP classique avec struct et zlib, sans
dépendance ajoutée. Le répertoire central est borné avant toute création de
fichier. Les en-têtes sont recoupés et les tailles réellement décompressées
sont comptées avant écriture. Les CRC sont vérifiés et les empreintes SHA256
calculées ; la campagne E2E les compare aux contenus attendus.
Le hash d'entrée est lui-même limité à la taille initiale acceptée.

L'extracteur travaille par descripteurs de répertoire sans suivre les liens,
applique les permissions readonly puis publie le candidat avec
renameat2(NOREPLACE). Son image Python indépendante permet la qualification
sans recréer le contrôle en service. Le même extracteur est maintenant appelé
par les routes de publication. Leurs plafonds et la reprise pendant réception
ou validation sont qualifiés ; expiration, budget et interruption du nettoyage
restent ouverts.

### Coordination des publications

Le contrôle monte le socket du démon rootless et utilise une image Node
immuable. Les candidats et révisions partagent leur UUID dans un dossier privé.
Après extraction et validation, une transaction revalide la credential exacte,
les droits et les versions de fonction/service, puis active code et configuration.
Le budget conserve les fichiers dont le nettoyage n'est pas confirmé. Un défaut
de réconciliation dégrade la santé et bloque l'admission jusqu'à reprise.
Le verrou de processus demeure détenu jusqu'à la fin des travaux de nettoyage,
y compris lorsque leur attente reçoit plusieurs annulations.

Le client E2E calcule les contenus attendus depuis les données originales de
ses ZIP synthétiques, indépendamment de l'inventaire retourné par l'extracteur.
Pour les douze ZIP issus du packager, un second lecteur ZIP recoupe cet
inventaire puis le runtime Node charge chacun des handlers extraits.

## Qualification

QLF-001 fournit l'application témoin de qualification, ses handlers et ses
données synthétiques.

### Service synthétique

Runtime Node.js 24 LTS, CommonJS, dépendance unique `yaml` pour interpréter un
véritable manifeste YAML. Le manifeste nomme handlers, événements HTTP,
échéances, budgets mémoire déclaratifs et identifiants stables de stockage.
Il utilise le fournisseur P2Enjoy proposé ; aucun plugin de déploiement
Serverless Framework n'est encore livré. La résolution `${env:...}` générale,
CloudFormation et les extensions d'autres fournisseurs ne sont pas supportées.

Les fonctions couvrent écho HTTP, réponse binaire, callback, autorisation métier
synthétique, vérification d'injection de configuration, compteur durable, cache,
worker avec checkpoint, exception, sommeil, boucle non coopérative et appel
entre fonctions. Aucune ne contacte une base client, blockchain, fournisseur
SMTP ou service externe.

### Exécuteur de référence

L'exécuteur sert `/healthz`, `/catalog` et `/functions/<nom>`. Il transforme la
requête en événement HTTP de type Lambda v1 puis invoque le handler dans un
processus enfant, avec `awsRequestId`, `functionName` et
`getRemainingTimeInMillis()`. Première terminaison gagnante pour Promise et
callback. L'échéance vient du parent, qui tue le processus après timeout.
La limite inclut ici le démarrage du processus. Chaque fonction est sérialisée
pour ses écritures ; des fonctions distinctes peuvent se relayer par HTTP.

Les deux volumes `/data` et `/cache` sont séparés et subdivisés par identifiant
stable de fonction. Les fichiers sont écrits atomiquement. Les identifiants
proviennent exclusivement du manifeste validé, jamais d'un chemin utilisateur.
Le worker conserve un checkpoint et peut reprendre une liste synthétique.

Ce serveur est un outil DEV de confiance, lié uniquement à la boucle locale
du SPARK sur le port invariant 18080. Il ne constitue pas une passerelle de
plateforme sécurisée : pas de SSO réel, de droits CRUD, de CORS/IP administrables
ou d'upload arbitraire. Pas de route publique proposée dans cette unité.
L'authentification métier du service témoin utilise un jeton confidentiel injecté
par la cellule, distinct de la future authentification de plateforme. Sans cette
configuration, le handler est indisponible ; aucun marqueur public n'est accepté
comme identité. Le jeton réel du banc DEV a été configuré via la console du
Spark ; la campagne complète exige ce prérequis.

### Configuration et secrets

Chaque service du Compose SPARK lit `/etc/spark/env` et `/run/spark/secrets` via
`env_file`. Aucun `.env`, aucune configuration injectée via `environment`,
`Dockerfile ENV` ou `ARG`. Les valeurs par défaut sont uniquement des constantes
du banc identiques partout, sans adresse distante ou identifiant de client.

Les enfants n'héritent pas de tout l'environnement du superviseur : seuls les
noms explicitement déclarés pour chaque fonction sont transmis. La fonction
configuration montre la présence d'un secret synthétique, jamais sa valeur.
Les tests n'injectent aucune configuration dans l'application. Les variables et
secrets viennent des deux fichiers réels de cellule. Le parcours de secret
présent fait échouer la campagne si la cellule n'en fournit pas. Le banc peut démarrer
sans secret, avec l'authentification métier désactivée et clairement signalée.

### Preuves et limites

La campagne complète couvre les contrats présents : nominal, refus, bornes,
authentification configurée et absente, allowlist d'environnement, saturation
réelle, logs, arrêt/reprise, persistance du worker, démarrage sur manifestes
invalides et défauts réels de stockage. Les fautes de disque et de manifeste
sont produites sur des conteneurs et volumes isolés portant la même image,
jamais sur les données du service. Les corps métier sont des objets JSON,
pas des tableaux ou scalaires. Le signal de lancement suit la résolution du
handler. La santé rend les admissions réelles pour observer la saturation.
L'arrêt ferme l'admission, tue les enfants et vide les files ; les clients
interrompus peuvent recevoir une erreur de transport.

Les tests sont exclusivement E2E et les campagnes séquentielles. Un conteneur
client séparé appelle par HTTP le service réellement déployé, sans import
applicatif, serveur privé, contexte fabriqué, mock ou interception réseau.
Les compteurs, caches et jobs acceptent un identifiant applicatif ; chaque
campagne crée et supprime ses propres ressources via les véritables routes.
Le relais appelle des pairs locaux réels limités à une liste (echo, failure,
sleep) ; la preuve d'erreur utilise une vraie exception du handler failure.
Les erreurs de saisie et les corps trop volumineux sont vérifiés par HTTP.

Une preuve distincte recrée le vrai conteneur et relit ses données par HTTP.
L'attendu est conservé dans un volume du client de test, séparé des volumes
applicatifs. Les traces ne contiennent ni jeton métier ni corps d'erreur.
Les contrôles statiques du manifeste ne sont pas des preuves fonctionnelles
E2E du déploiement de plateforme, qui exige ses propres campagnes.

Les limites Docker portent sur le banc complet, pas individuellement sur ses
fonctions. Le budget mémoire du manifeste reste un contrat à qualifier par le
moteur de plateforme ; il ne doit jamais être présenté comme un quota appliqué par
l'exécuteur de référence. Même limite pour min/max instances, cron, stockage
à quota dur et passage à zéro : non implémentés.

## Déploiement DEV

Sources : ce dépôt uniquement. Cible : cellule `infra-serverless` décrite dans
`dev-spark.md`, accessible par le rebond documenté. Répertoire dédié prévu :
`/srv/p2enjoy-serverless/qualification`. Docker est piloté par `spark-docker`.
Les notes se proposent sous `/etc/spark/notes/*.md.?`, sans modifier les notes
gérées par la console. Aucun accès d'administration à la FORGE.

## Consultation des exécutions

La fiche React de fonction possède quatre destinations : Configuration, Code
et révisions, Instances et Invocations. Les deux dernières utilisent les routes d’observation
existantes, cinq lignes par page et rafraîchissement manuel. Les détails de
journal sont natifs et rendus comme texte ; aucune mesure manquante ne devient
une allocation ou un zéro. Le [contrat](CONSOLE_EXECUTION.md) est vérifié par
la [preuve de console](evidence/console-execution-dev-2026-11-07.json), qui recoupe
le backend inchangé avec la preuve moteur, les nouvelles ressources web et
les parcours réels de session/gestion/exécution.

## Manuel d’usage embarqué

`docs/manual.md` est compilé par `web/vite.config.mjs` dans le module virtuel
`virtual:usage-manual` : titre, sommaire, HTML et SHA256 du document. La page
React `/console/manual` le présente dans la navigation existante. Le contrat
local impose la maintenance du document avec chaque évolution fonctionnelle.
La compilation standard utilise [markdown-it](https://github.com/markdown-it/markdown-it)
15.0.3 (MIT), uniquement au build, HTML brut désactivé et liens HTTPS/ancres
contrôlés. L’audit du verrou ne signale aucune vulnérabilité le 7 novembre.
Le guide est documentaire, embarqué dans les ressources publiques ; son affichage
suit la session habituelle de console. Aucune nouvelle route serveur, migration
ni variable de cellule. La [preuve](evidence/manual-console-dev-2026-11-07.json)
recoupe 101 sources, 27 fichiers embarqués et l’identité du backend avec la
preuve moteur, puis 48 groupes et 33 captures.

## Publication depuis la console

La facette **Code et révisions** utilise la préparation serveur du code, qui
capture les ressources, variables, secrets et événements courants. L’UUID connu
avant le POST corrèle suivi et upload ; la consultation au retour ne rejoue pas
le transport. La dernière lecture du candidat remplace sa ligne dans la liste.
Les révisions sont paginées localement, les candidats côté serveur. Une erreur
de mutation déclenche une relecture avant toute nouvelle action ; les succès
antérieurs disparaissent lors des consultations explicites.

Le [contrat](CONSOLE_PUBLICATION.md) conserve les refus de droits et de version
au contrôle. Aucun schéma ni dépendance supplémentaire n’est nécessaire.
La [preuve finale](evidence/publication-console-dev-2026-11-07.json) recoupe
18 campagnes et 312 groupes, 144 sources et 54 captures inspectées, avec les
mêmes sources et image avant/après chaque campagne. Le manuel à onze chapitres
est reconstruit et comparé au document source. Les trois notes maintenues dans
`qualification/spark-notes/` sont appliquées par la console SPARK puis relues.
Cette livraison ne clôt pas les preuves résiduelles et fonctionnalités du backlog.

## Effacement corrélé du stockage

SLS-064 prépare les [reçus durables](STORAGE_DISCARD.md) et le worker unique
d’effacement hors verrou de registre. Protocole déployé et vérifié : sept campagnes, 106 groupes réels, sans échec
ni skip, avec migration et nettoyages recoupés. [Preuve](evidence/storage-discard-dev-2026-11-07.json). Le raccordement public et la console appartiennent à SLS-065.

## Gestion publique du stockage

Le contrat [SLS-065](CONSOLE_STORAGE.md) est déployé et qualifié en DEV.
Les reçus publics persistants sont séparés des gardes temporaires d’admission.
Le contrôle décide après drainage et nouvelle vérification des droits, puis
reprend le protocole agent corrélé avec ses paramètres initiaux. La purge
attend aussi le nettoyage du code avant de rendre un résultat terminal.
Le catalogue traverse les parents supprimés par leurs UUID ; seule une session
administrateur y accède. Aucun service ni dépendance supplémentaire prévu.

La [preuve complète](evidence/storage-console-dev-2026-11-08.json) recoupe
29 campagnes et 397 groupes, puis neuf groupes API renforcés. Quatorze corps
invalides de purge et une version périmée sont refusés sans mutation des fichiers,
configurations ou registres. Les relevés du helper sont strictement en lecture
seule et limités aux UUID de campagne. Les 28 fonctions des huit namespaces
publics sont purgées ; les deux restaurations historiques sont séparées. Sources,
image, 25 fichiers embarqués et 72 captures sont liés à chaque phase. Aucune
nouvelle migration, dépendance ou configuration.

## Catalogue des adresses d’appel en qualification

SLS-066 suit [INVOCATION_URLS](INVOCATION_URLS.md). Le contrôle lit le répertoire
officiel de cellule par montage readonly, sans nouveau service ni variable.
Le port local ASGI du réseau hôte identifie les routes d’invocation ; le Host
client ne participe pas au calcul. Une lecture SQL joint fonction, service et
événements de sa révision active. La console et la CLI utilisent le même
catalogue Read autorisé et borné ; une erreur de lecture des adresses après
publication ne transforme pas celle-ci en échec. Aucun changement de schéma.
La projection ne garantit ni fraîcheur transactionnelle ni certificat prêt.
Le [checkpoint DEV](evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
recoupe montage readonly, 26 sources embarquées, 88 groupes et 31 captures.
Le contrôle est déployé avec ces parcours ; multi-domaines, sources perturbées
restent à qualifier ; le refus 401 après publication est qualifié séparément.

## Régression complète SLS-066

La suite définie par [INVOCATION_URLS](INVOCATION_URLS.md#suite-complète-de-preuve)
passe dans la [preuve complète](evidence/invocation-urls-regressions-dev-2026-11-08.json) :
35 campagnes / 467 groupes, six prérequis distincts non comptés, 186 sources
et images contrôle/CLI liées avant/après chaque phase. Les 32 fonctions suivies
dans dix namespaces sont purgées ; les deux restaurations historiques restent
distinctes. Les 26 fichiers embarqués et 79 captures fraîches sont recoupés,
avec 61 observations et 18 identités SHA avec une référence inspectée.
Le Host est exercé par un client réel de boucle locale du SPARK,
sans dépendance remplacée ; les alias publics restent une preuve distincte.
L’intégration de ces clients ne change ni service, schéma ni configuration.

Le [complément de transport](evidence/invocation-url-transport-dev-2026-11-08.json)
passe 16 groupes ciblés/régressions : publication conservée sous deux vrais 502
du GET facultatif, six connexions CLI sans rejeu et invocation Docker après
reprise. Ses 187 sources, image, huit fonctions purgées et six gardes terminées
sont recoupées. La preuve des 467 groupes reste distincte ; le produit est inchangé.


Le [complément de révocation](evidence/invocation-url-refusal-dev-2026-11-08.json)
qualifie le refus réel du GET après publication : CLI retenue avant sa sixième
connexion, jeton révoqué par l’API puis vrai 401, publication/UUID conservés,
six connexions sans rejeu et invocation Docker par un autre Read. Le replay
passe 17 groupes avec 188 sources/images stables, neuf fonctions purgées dans
trois namespaces, six gardes terminées et 26 fichiers embarqués recoupés.
Le premier essai incomplet reste distinct, avec deux fonctions et gardes
nettoyées ; sa barrière manquée reste de cause non prouvée. Aucun code produit,
schéma ou réglage n’est modifié ; les notes actualisées sont reproposées.
Le 403 et les pannes du pilote/diagnostic restent hors de cette preuve.

## Catalogue global qualifié

SLS-067 suit [FUNCTION_CATALOGUE](FUNCTION_CATALOGUE.md) : lecture administrateur
des métadonnées existantes, recherche Unicode avant pagination dans un snapshot
SQLite, normalisation par fonction locale à cette connexion et sélecteurs de
parents paginés. Aucune migration ni dépendance. La console utilise l’accueil
Fonctions et un retour de catalogue par query validée, sans stockage client.
La [preuve](evidence/function-catalogue-dev-2026-11-08.json) retient 37 campagnes
uniques / 489 groupes et six prérequis, avec 447 groupes conservés aux clients
inchangés puis 42 réexécutés. Les deux époques de sources sont distinctes et
les images produit/CLI restent identiques. Les 98 captures, le manuel 15/46,
les 91 fonctions suivies purgées et les ressources libérées sont recoupés.


## Identité canonique du code — composant SLS-074

`function_code_hash.py` constitue la bibliothèque commune d’identité du paquet.
Sa CLI opérateur utilise l’extracteur borné, puis l’inventaire vérifié et le
descripteur handler/runtime/architecture/image/événements. Le format v1 et la
normalisation sont dans [FUNCTION_CODE_HASH](FUNCTION_CODE_HASH.md). Le packager
conserve maintenant le mode exécutable, sans prétendre connaître hors connexion
l’image du serveur. Aucun schéma ou API de version ne change dans cette étape.
L’image serverless-code-hash ne sert aucun port, utilise les deux env_file de
cellule et un contexte limité à deux sources. Le contexte de l’adaptateur est
limité à onze feuilles. La preuve réelle réunit sept groupes du composant et
45 de régression, neuf appels Docker et 222 sources ; le contrôle reste le même.
Les étapes de registre, déduplication, promotion explicite, sélection/pools et
console restent définies dans [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md).


## Pagination des domaines — complément ciblé008

Le [plan autorisé](INVOCATION_DOMAINS_PAGINATION.md) fournit quatre routes/A
temporaires réels via la console normale, puis leur retrait borné. Le produit
ne change pas : le catalogue garde cinq domaines par page, la CLI vérifie
SHA/total/révision entre ses deux GET et conserve le succès de publication si
ce catalogue change. La [preuve](evidence/invocation-pagination-dev-2026-11-09.json)
qualifie huit groupes de cycle/UI/CLI et trois prérequis distincts, 14 appels
Docker, sept captures inspectées et deux purges physiques sur253 sources.
Les quatre routes/A sont retirés indépendamment après perte réelle du
propriétaire ; contrôle/référence, images, démarrages et configurations
permanentes sont conservés. Les autres fautes et la régression complète008
restent des unités de preuve distinctes.

## Planification du contrôle

SLS-078 intègre `app/schedules.py` au processus unique du contrôle, après la
réconciliation d'exécution. `schedule_calendar.py` fournit la grammaire et le
calcul UTC, partagés par la validation des événements et le moteur. Migration
009 et générations transactionnelles attachées au pointeur promu ; réclamation
avant l'admission interne, rétention et reprise sans envoi des fenêtres manquées.
La facette Planifications consomme les lectures Read de ce registre, jamais un
second calcul de planning côté navigateur. Voir [SCHEDULES](SCHEDULES.md).
Moteur déployé en DEV ; premier checkpoint de22 groupes réels recoupé dans
[la preuve](evidence/schedules-checkpoint-dev-2026-11-10.json). La qualification
complète des planifications et de la plateforme reste ouverte.

## Éditeur et brouillons en qualification

[CONSOLE_EDITOR](CONSOLE_EDITOR.md) spécifie SLS-070 avant code : couche de
modifications chiffrées sur une révision immuable retenue, puis reconstruction
ZIP bornée et réutilisation du vrai pipeline code-only. Une garde de lecteur
protège les entrées/sorties du nettoyage et de la purge ; aucun verrou SQLite
n'est tenu pendant la reconstruction. La copie des dépendances dans chaque
brouillon est écartée. La bibliothèque standard suffit ; aucune dépendance,
service ni variable de cellule supplémentaire. Le serveur et la première facette
console sont maintenant déployés ; leur qualification reste partielle.

Première réalisation serveur010 déployée sur7c5c6f4b et [partiellement qualifiée](evidence/code-editor-server-dev-2026-11-12.json)
le12novembre2026 local :20groupes ciblés et25régressions, données et référence
conservées. Les lecteurs réels retiennent les fichiers, les patches sont
chiffrés, l’envoi réutilise operations.responsibility et le pipeline Docker.
Les compléments de la facette Éditeur, les limites globales et les reprises
gardent leur reste à faire.

La première facette SLS-070 réutilise les API010 existantes. Une
garde client protège les départs et la déconnexion avant mutation serveur ;
le modèle texte garde ses octets/fins de ligne indépendamment de la vue DOM.
Aucune nouvelle dépendance, migration ni valeur d’environnement.

La [preuve de console](evidence/code-editor-console-dev-2026-11-12.json) passe
57 groupes réels sur a77b6b4e : 12 UI, 20 serveur et 25 régressions, avec
17 invocations natives et 41 images inspectées. Le manuel servi correspond à
17 chapitres et 67 paragraphes. Le compteur de brouillon est indépendant de la
version de fonction ; la copie relue est liée au chemin/surface/génération.
L’historique conserve des patches exacts bornés à 64 gestes et 8 Mio de fragments.
Le succès historique visible pendant une nouvelle saisie est corrigé et
qualifié dans070.8. L’unité reste ouverte pour limites, reprises et parcours complémentaires.

Le [complément070.8](evidence/code-editor-save-confirmation-dev-2026-11-12.json) passe39groupes sur371sources et6e1584f2.
Le serveur reste byte-identique au checkpoint57 ; les modifications sont dans
l’état client de confirmation et de saisie, avec le manuel associé. Une vraie
contention SQLite bornée du banc confirme le snapshot envoyé et les frappes
ultérieures sans interception ni réponse substituée. Les sorties/pertes de ce
seul helper sont recoupées ; elles ne qualifient pas un SIGKILL du contrôle.
Les données, routes et référence sont conservées ; quotas/reprises restent ouverts.

## Client HTTP intégré qualifié — SLS-071

La facette Tester compose en mémoire une requête serveur ou navigateur vers
les seules destinations calculées de l’installation. Le serveur exige admin,
un vrai Read pour la passerelle, aucune transmission du cookie de console et
aucune redirection suivie. Quatre places sont réservées avant réception JSON,
les tâches annulées/jointes avant restitution ; aucune table ou migration
supplémentaire. Le manuel et le seed original restent ceux de la plateforme.

La [preuve31](evidence/function-http-client-task-exception-dev-2026-11-12.json) recoupe la dernière
garantie sur le code déployé : OSError réelle dans le constructeur TLS après
openat/EMFILE, limites rendues avant Python, même processus, quatre sorties et
cinquième429 puis succès. Les helpers natifs appartiennent au banc de DEV,
sans capacité supplémentaire donnée aux fonctions. L’unité est livrée avec
ses autres preuves par critère ; les journaux/monitoring complets restent072/073.
