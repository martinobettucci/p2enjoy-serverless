# Déploiement DEV de la plateforme

## Noms et entrée courants

L’entrée est `https://serverless.lelabs.tech` vers le port HTTP 18090 du SPARK.
Le conteneur `serverless-api` sert la console et l’API ;
`serverless-runtime-reference` exécute les fonctions du banc sur la boucle locale
18080. Les noms Compose internes conservent l’identité des ressources et volumes.
Le client OIDC reste `p2enjoy-serverless-dev`, avec les nouvelles URL de la
[déclaration](OIDC_DEV.txt). Le [contrat OIDC courant](OIDC_DEV.llms.txt)
est le bloc fourni par le responsable pour le client daté du 6 novembre 2026
à 15:44:32 ; il confirme aussi l’origine web et l’accueil sur ce domaine.
Le détail de migration est dans
[DEPLOYMENT_NAMES](DEPLOYMENT_NAMES.md). Les constats datés ci-dessous décrivent
les étapes antérieures, dont l’ancien domaine.

La [preuve du 6 novembre](evidence/deployment-names-dev-2026-11-06.json) recoupe
les deux services healthy, la conservation avant/après recréation, dix-sept
sources déployées et les campagnes publiques sur cette adresse. La route
courante a été corrigée vers 18090 par le responsable ; SERVERLESS_PUBLIC_URL
a été appliquée par la proposition officielle. Les trois notes ont été
appliquées et relues. La connexion personnelle sur le nouveau domaine a
réussi : session authentifiée et accès administrateur aux namespaces HTTP 200.

La [preuve de gestion](evidence/control-management-dev-2026-11-06.json) ajoute
19 groupes API administrateur, 11 parcours UI et huit groupes publics sur
l'image corrigée de navigation mobile. La [preuve de publication](evidence/deployment-authenticated-dev-2026-11-06.json)
ajoute onze groupes API et sept groupes CLI authentifiés sur cette même image.
Les trois notes sont appliquées et relues, les fichiers officiels concordent.
Les constats d'absence de session ci-dessous décrivent leurs checkpoints
historiques ; la session réelle est maintenant disponible. Les cycles SSO,
limites et interruptions résiduelles de publication et vues de révisions restent
ouverts. Le moteur raccordé est décrit dans la section de déploiement courante
ci-dessous. La [preuve de reprise](evidence/publication-recovery-dev-2026-11-06.json)
qualifie ensuite quatre groupes de plafonds et de reprise après SIGKILL pendant
réception et validation. Le contrôle est redémarré et healthy ; ses images,
la configuration officielle et la route sont conservées. Les trois notes
décrivent les commandes et limites restantes : expiration, budget, déconnexion
concurrente et interruption pendant nettoyage.

## Baseline

Le banc de qualification est déployé selon `QUALIFICATION_DEV.md`. Le composant
de quota est construit dans `storage/`, testé par 31 contrôles puis laissé
sans montage permanent après ses preuves. L’agent local est maintenant installé
en service DEV, avec état durable et socket privé. Le contrôle et la console initiale sont déployés en
DEV ; les parcours de gestion administrateur sont désormais qualifiés.
La cible est le SPARK `infra-serverless`
et le répertoire `/srv/p2enjoy-serverless`, administré par `spark-docker` pour
Docker. Le dossier de cellule fourni reste la référence `dev-spark.md`.

## Instances chaudes qualifiées

Le pilote opérateur et le superviseur sont construits sur le SPARK DEV, avec
31 contrôles d’invocation, 11 de courses et 36 régressions du chargeur réussis.
La [preuve](evidence/instances-dev-2026-11-06.json) conserve les empreintes des
sources et images, les rapports et les limites d’intégration. Les commandes
sont `bash runtime/dev.sh instances-test`, `lifecycle-test` et `test`, en série.

L’empreinte `SERVERLESS_RUNTIME_IMAGE` est proposée puis appliquée par la console
SPARK après qualification, et le contrôle est recréé pour la lire. Son image
applicative reste celle du checkpoint de publication ; les futures révisions
utiliseront le nouveau runtime validé, qui contient aussi le superviseur
d’invocation. Aucun nouveau secret, route, port ou schéma SQLite.
Le pilote d’instance n’est pas encore relié aux routes publiques. Il nécessite
le véritable accès opérateur au démon ; aucun accès d’invocation public n’est
créé par ce diagnostic. La réconciliation des instances après SIGKILL sera
raccordée avec le moteur. Les trois notes de cellule décrivent ce checkpoint.
Un retour à l’ancienne empreinte reste possible depuis la console, en tenant
compte des révisions qui auront été publiées ensuite ; les images sont conservées.

## Ordre de réalisation

La migration 003 et les routes de publication sont intégrées au contrôle DEV.
Les trois paramètres `SERVERLESS_STATE_HOST_PATH`, `SERVERLESS_DOCKER_SOCKET_HOST`
et `SERVERLESS_RUNTIME_IMAGE` ont été proposés puis appliqués par la console
de cellule. Le contrôle monte son état durable et le socket Docker rootless ;
le runtime est désigné par son empreinte immuable. Le budget d’artefacts garde
sa valeur par défaut de 4096 Mio. Aucun nouveau secret ni route n’est requis.

Avant la première migration, la sauvegarde SQLite native
`/srv/p2enjoy-serverless/state/backups/before-003-20261106T005940Z-5d7534.sqlite3`
a été créée et vérifiée : intégrité correcte, versions 001/002, fichier 0600
et dossier 0700. La base active porte les versions 001/002/003 et un UUID
d’installation durable. Les anciennes images sont conservées ; un retour
à une version antérieure de schéma exige l’arrêt du contrôle et une restauration
explicite de sa sauvegarde, avec prise en compte des écritures postérieures.

Huit groupes HTTPS publics et trente contrôles de démarrage/panne passent sur
l’image déployée. La [preuve](evidence/deployment-control-dev-2026-11-06.json)
recoupe 21 sources avec le SPARK et 14 fichiers embarqués, la configuration
active, la sauvegarde et les deux services sains. Le client de publication
s’arrête sur le prérequis absent de session SSO réelle. La console de révisions
et les preuves authentifiées restent à poursuivre.

La commande deploy de l’adaptateur est construite dans ses images DEV. Après
`bash adapter/dev.sh build`, la campagne `test` repasse ses 24 contrôles et
`deploy-public-test` passe 14 contrôles de prérequis, configuration et refus
HTTPS réel. Sources et images sont recoupées dans la
[preuve CLI](evidence/adapter-deploy-dev-2026-11-06.json). Le contrôle permanent
n’est pas recréé pour cette tranche ; aucun paramètre de cellule supplémentaire.
Les jetons de déploiement sont ceux créés par un administrateur pour un service.
La campagne `node e2e/adapter-deploy.mjs` exige la session SSO réelle, absente
au checkpoint ; aucun déploiement positif n’est déclaré qualifié.

L'extraction serveur est construite depuis `control/Dockerfile.artifacts`
et qualifiée par `e2e/artifacts.py` : 112 contrôles réels réussis le 6 novembre,
zéro échec et zéro test ignoré. Image, empreintes et périmètre figurent dans
[la preuve](evidence/artifacts-dev-2026-11-06.json). Depuis `control/`, lancer
`bash artifacts-dev.sh build` puis `bash artifacts-dev.sh test`, en série.
Ces commandes restent séparées du contrôle permanent et ne déclenchent aucune
migration. Leurs résultats précèdent l’intégration HTTP décrite ci-dessus.
Les notes README, CONTRIBUTORS et INSTALL de la cellule sont reproposées,
appliquées par la console SPARK puis relues : elles décrivent ce composant,
ses commandes et ses limites. Aucune variable, secret ou route supplémentaire.

L'image `runtime/` de validation Node et ses variantes originales sont construites
sur le SPARK. Le pilote Docker passe 36 scénarios réels ; ses ressources de
qualification sont nettoyées. Cette étape ne change pas le contrôle déployé.
Le socket Docker et le chemin hôte des artefacts sont maintenant intégrés
au contrôle avec les API de révision et leur migration. Les répertoires
`adapter/`, `runtime/`, `e2e/` et `qualification/artifacts/` sont présents sous
`/srv/p2enjoy-serverless`. Les commandes d'exploitation figurent dans leurs README.

1. Proposer les paramètres supplémentaires du contrôle dans les fichiers `.?` de la cellule,
   puis les appliquer par sa console. Aucun secret n'est conservé au dépôt.
2. Construire et déployer le contrôle et le runtime, appliquer les migrations
   SQLite versionnées, puis déployer l'application témoin via l'adaptateur.
3. Exécuter les campagnes ciblées puis complète et mettre à jour les notes.

## Intégration initiale des 5 et 6 novembre

Client OIDC créé : `p2enjoy-serverless-dev`, application serveur confidentielle,
PKCE S256, callback `/auth/retour`, déconnexion `/`, rôles `verified` et `admin`.
Déclaration prête à importer dans l'interface SSO, onglet Intégrations :
[OIDC_DEV.txt](OIDC_DEV.txt). Domaine retenu pour DEV :
`serverless-dev.lelabs.tech`, résolu vers l'entrée de la cellule et déclaré
sur le port HTTP 18090 avec TLS public. Le secret `OIDC_CLIENT_SECRET` est
appliqué dans le SPARK, avec `OIDC_CLIENT_ID` et `SERVERLESS_PUBLIC_URL`.

État vérifié le 5 novembre 2026 : découverte SSO accessible ; callback accepté
par le client, PKCE exigé ; l'authentification du client au token endpoint est
acceptée (code d'autorisation invalide volontairement, erreur invalid_grant).
La route DNS et HTTPS répond et le contrôle écoute sur 18090. Les trois notes
de cellule décrivent le banc, le stockage et le contrôle déployé. La console
locale est accessible sur 5175. Le parcours utilisateur SSO reste à vérifier
avec le contrôle, dans SLS-020 et SLS-060.

Revalidation du 6 novembre 2026 à 00:09 UTC après confirmation du responsable :
la route officielle est `serverless-dev.lelabs.tech 18090 tls`. Le certificat
Let’s Encrypt YE1 couvre le domaine et passe la validation TLS normale ; il
est valable du 5 novembre 2026 au 3 février 2027. `/healthz` répond 200 et le
contrôle est healthy. Les cinq paramètres requis et le proxy approuvé du
conteneur correspondent aux fichiers de cellule, comparaison des secrets
effectuée uniquement en mémoire. Aucune recréation n'est nécessaire. Les sept
groupes de contrôles publics repassent. Les trois notes officielles restent
justes pour cette confirmation ; aucune route ni variable supplémentaire.

## Conservation de l'adresse cliente

La mesure sur le contrôle DEV constate que le proxy TLS et l'accès direct
depuis le SPARK arrivent tous deux avec le pair `172.19.0.1` tant que le proxy
utilisateur Docker est actif. Caddy reconstruit X-Forwarded-For sur l'entrée
TLS, mais un accès direct peut le fournir lui-même. Ce pair commun ne doit
donc pas entrer dans SERVERLESS_TRUSTED_PROXIES.

La désactivation de userland-proxy est écartée : Docker refuse de démarrer
sans `/proc/sys/net/bridge/bridge-nf-call-iptables`, absent de cette cellule.
La configuration initiale du démon est restaurée. Les réseaux Compose,
devenus incohérents au redémarrage refusé, ont été recréés sans retirer les
volumes ; les deux piles DEV sont revenues saines.

Le choix retenu est `network_mode: host` pour le seul contrôle. Docker 29.9.3
permet ici de partager le réseau réel du SPARK : la preuve utilise le vrai
contrôle, un état SQLite temporaire et les deux env_file officiels lus par
Compose. Le pair loopback reste 127.0.0.1 et l'inode de namespace réseau du
conteneur correspond à celui du SPARK. Les fonctions gardent un réseau Docker
isolé ; leur commande d'exécution passera par l'API locale Docker.

Le contrôle écoute directement sur 18090, sans publication de port Docker.
Les chemins TLS et directs sont mesurés : le pair TLS est `10.77.0.1`, le
loopback `127.0.0.1`, et un client Docker bridge arrive depuis `10.77.0.24`.
Caddy remplace X-Forwarded-For même lorsque le client le falsifie. La proposition
`SERVERLESS_TRUSTED_PROXIES=10.77.0.1/32` est appliquée par la console SPARK,
puis le contrôle est recréé. La campagne réelle des limites de connexion
vérifie ensuite les refus et la persistance des compteurs au redémarrage. Aucun
paramètre de FORGE ni garde de filtrage noyau n'est modifié. Les expériences
de conteneurs temporaires sont supprimées après chaque mesure.

## Reprise et retour arrière

Le binaire de montage s'exécute comme `spark-docker`. Le helper fusermount3
installé perd son descripteur de communication au passage exec dans cette
cellule (trace réelle : dup3 réussi, puis fd 3 absent au démarrage du helper).
Le mode direct est qualifié avec CAP_SYS_ADMIN attribuée exclusivement
au processus de montage dans le SPARK, sous ce même UID. Les workloads et la
construction restent dans Docker. Le montage reste accessible au seul UID
propriétaire, qui correspond au root interne des conteneurs rootless ; les
capacités des workloads sont retirées. Le montage n'expose aucune API réseau.

L'expérience de quota ne remplace aucun volume existant. Son nettoyage suit
l'ordre arrêt des conteneurs, démontage FUSE, suppression des fichiers propres
à l'expérience. Un échec de montage arrête cette expérience sans modifier les
volumes du banc. L’installation de l’agent DEV et ses limites sont décrites ci-dessous.


## Agent de volumes installé

Les cinq variables SERVERLESS_STORAGE_ROOT_HOST,
SERVERLESS_STORAGE_SOCKET_DIR_HOST, SERVERLESS_STORAGE_BUDGET_MIB,
SERVERLESS_STORAGE_RESERVE_MIB et SERVERLESS_STORAGE_MAX_MOUNTS ont été
proposées puis appliquées par la console. Racines DEV :
`/srv/p2enjoy-serverless/storage-state` et `/srv/p2enjoy-serverless/storage-channel`.
Le canal a été migré par proposition officielle : le /run du démon Docker
rootless est distinct de celui de l’agent et ne rendait pas son socket visible.
Budget 32768 Mio, marge 8192 Mio, limite 64 montages. Aucun secret ni route
supplémentaire. Le service lit directement les deux fichiers officiels.

Le paquet versionné par empreinte est installé sous `/usr/local/lib` avec
propriétaire root. Le service conserve UID/GID spark-docker, CAP_SYS_ADMIN
seule, le namespace de montage de la cellule et un socket 0600 sous dossier
0700. Les vrais binds Docker valident la visibilité des montages. La base
séparée porte les migrations 001/002/003, avec intention de sonde avant lancement
et reçus durables de configuration.
Le contrôle est recréé avec le répertoire du canal monté readonly sous
/storage-agent ; ses valeurs sont relues dans les deux fichiers officiels.
L’installateur conserve le répertoire 0700 aux arrêts et l’agent recrée seulement
son socket. Le même contrôle retrouve ce socket après stop/start de l’agent.

Construire avec `bash storage/dev.sh build` comme spark-docker ; installer
avec `bash storage/dev.sh install` comme root. Puis exécuter en série
`agent-test` et `limits-test` comme root. La [preuve de composant](evidence/storage-agent-dev-2026-11-06.json)
recoupe sources, paquet installé, binaire, rapports, configuration et nettoyage.
Le raccordement au pilote passe quatorze groupes réels, dont annulation, quotas,
panne FUSE et arrêt/reprise de l’agent. [Preuve](evidence/managed-storage-dev-2026-11-06.json).
Les parcours publics restent ouverts dans SLS-050.

Une mise à jour exige l’absence de baux et d’opérations en attente. Le protocole
quiesce empêche un acquire entre cette vérification et le restart. Les anciens
paquets restent conservés. Revenir à un code de schéma antérieur exige un plan
de restauration de sa base ; ne pas pointer l’unité vers l’ancien paquet en
supposant une migration descendante. Les backups de la cellule restent gérés
par son mécanisme existant. Un restart forcé invalide les anciens binds et
exige la réconciliation des consommateurs avant libération des baux.

## Préparation des mutations de stockage

Le paquet installé le 6 novembre porte l'empreinte
`4ba9e4bf5626d221596725566102d919047d19c43a944bfa20cd1a12bd8a3d34`.
L'installateur l'a préparé au repos, a fermé les mutations par quiesce puis a
redémarré l'agent, qui a appliqué sa migration 003. L'image et le schéma du
contrôle ne changent pas dans cette étape. Les paramètres, secrets et la route
restent fournis par les fichiers officiels de la cellule.

Les préparations réservent les augmentations sans libérer l'ancien quota. Les
reçus distinguent prepared, committed et aborted ; un redémarrage ne choisit
pas à la place du contrôle. L'abandon retire uniquement les répertoires nouveaux
restés vides et conserve une version monotone même pour une création abandonnée.
La campagne `python3 -B e2e/storage-preparations.py`, exécutée comme root dans
le SPARK, qualifie dix groupes avec SIGKILL, reprise partielle et vrais fichiers.
Le rapport reste sous storage/preparations-proof.json. Les commandes de
régression agent-test, limits-test et e2e/managed-storage.py s'exécutent en série.
Les 47 groupes passent avec nettoyage confirmé ; la [preuve recoupée](evidence/storage-preparations-dev-2026-11-06.json)
vérifie 62 sources locales/distantes, 21 fichiers embarqués, le paquet protégé,
la configuration officielle et les 73 archives de publication conservées.
Les trois notes de cellule sont appliquées par sa console puis relues.
Le raccordement des mutations de gestion et publication est décrit dans la
baseline suivante. Les admissions et invocations sont décrites dans la
baseline du moteur ci-dessous.

La migration est additive, mais l'ancien agent n'accepte pas la version 003.
Un retour à son paquet exige une restauration explicite et cohérente du
registre après drainage, en tenant compte des écritures postérieures.
Les mécanismes de sauvegarde du SPARK restent l'autorité d'exploitation.


## Baseline des mutations publiques de stockage

Le contrôle déployé porte l’image
`sha256:922b2be19b240df60ed4dec7397b4f87c5902a7a97d9d23592ef825bf57e8cb2`
et les migrations 001 à 004. La migration 004 ajoute les intentions de fonction.
La sauvegarde native préalable est
`/srv/p2enjoy-serverless/state/backups/before-004-20261106T190408Z-793ab4.sqlite3` :
intégrité vérifiée, migrations 001 à 003, mode 0600 et 73 archives de code recensées.
La migration est additive ; revenir à un ancien contrôle ne doit pas laisser
une intention non résolue. Une restauration de base doit tenir compte des
publications et écritures postérieures ; aucune restauration n’est implicite.

L’agent porte le paquet protégé
`e116f761cadf8a04a59d1f45d729ef29edcb7b1e41e3a81afab43eda4422b255`,
avec le schéma 003 et l’abandon d’une préparation encore inconnue par sa
configuration et sa version initiales. Aucune nouvelle variable ni route :
les deux fichiers officiels et `serverless.lelabs.tech` vers 18090 restent
l’autorité de configuration. Le canal privé conserve son montage readonly.

Les créations, modifications de quotas, suppressions et publications passent
par l’intention durable du contrôle. Une suppression conserve une archive
allouée ; seule une purge opérateur distincte la libère. Après confirmation
perdue, relire la fonction et le candidat : une décision commit se confirme,
elle ne se compense pas par l’ancienne configuration. Les intentions et codes
fixes de reprise sont consultables sans exposer leurs paramètres privés.

Les commandes de cette qualification figurent dans [e2e](../e2e/README.md).
La [preuve recoupée](evidence/function-storage-dev-2026-11-06.json) distingue les
parcours HTTPS, la preuve ciblée du pilote sous contention, les composants de
stockage et les régressions. Les 161 groupes passent, dont 149 rejoués en série
sur le contrôle final et douze préparations sur le même paquet d’agent.
Les 82 sources locales/distantes, 23 fichiers embarqués et 136 archives de code
sont vérifiés. Les sept captures JPEG sont relues ; les trois notes de cellule
sont appliquées par sa console puis relues. Aucun bail, montage, allocation,
intention, conteneur d’instance/validation ni espace de test ne subsiste.
Ce checkpoint précède le raccordement du moteur décrit ci-dessous. Les
commandes de purge/cache restent à réaliser ; les vues d’observation sont
livrées dans la baseline de console ci-dessous.

## Déploiement du moteur en qualification

Les cinq budgets SERVERLESS_FUNCTION_CPU_BUDGET=1,
SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB=8192, SERVERLESS_FUNCTION_INSTANCE_LIMIT=32,
SERVERLESS_WAITING_CALL_LIMIT=128 et SERVERLESS_FUNCTION_WAITING_CALL_LIMIT=16
sont proposés puis appliqués par la console et relus dans /etc/spark/env.
La route, les secrets et le runtime Node ne changent pas.

La sauvegarde native préalable est
`/state/backups/before-005-20261106T203759Z-a85aa7.sqlite3` dans le contrôle,
soit le même suffixe sous /srv/p2enjoy-serverless/state. Elle est intègre,
en mode 0600, porte les migrations 001 à 004 et les 136 archives conservées.
La migration 005 ajoute les réservations et invocations, ainsi que les gardes
de révision utilisée. Elle est appliquée ; le moteur est déployé avec l’image
`sha256:d7621027bf550ea1e199aa81cb87d89b6628c93ff75b258a84cc18a64a4edb43`.
La [preuve courante](evidence/execution-dev-2026-11-06.json) recoupe 252 groupes
réussis, zéro échec et zéro test ignoré dans les treize campagnes finales.
Elle vérifie 93 sources locales/distantes, 27 fichiers embarqués,
280 archives de code retenues, les ressources web servies et les valeurs de cellule.
Les sept captures de console sont relues ; les trois notes sont appliquées
par la console SPARK puis relues. Les ressources actives, baux, montages,
réservations et espaces de campagne sont libérés. Les archives de code et
l’historique restent conservés selon leur contrat.

Le banc corrige une course de création WAL/SHM pendant ses lectures root :
les accès SQLite des gardes emploient l’identité effective du contrôle et
restaurent root avant les actions système. La preuve conserve les échecs
initiaux et les diagnostics séparément du bilan de la campagne finale.
Les vues de révisions, les commandes de purge/cache, les crons et
les preuves résiduelles restent ouverts dans le backlog.

Un retour à une ancienne image exige d'abord un drainage confirmé et l'absence
de réservation ou invocation active. Une restauration de base ne rejoue jamais
les appels interrompus et doit tenir compte des écritures métier postérieures.
Le répertoire privé /state/execution est possédé par l'installation et est
réconcilié avec ses labels Docker et baux avant réouverture des admissions.

## Baseline de consultation des exécutions

Le 7 novembre, l’image du contrôle devient `sha256:ff953f8e39871c060618482f6ecb4a88fc8026d2da93f80efe1565f83be30b21`. Les fichiers Python/SQL
embarqués sont identiques à ceux de la preuve moteur ; les ressources web
ajoutent les facettes Instances et Invocations. Le schéma reste 005 et les
valeurs officielles consommées sont recoupées avec la cellule.

La [preuve courante](evidence/console-execution-dev-2026-11-07.json) passe 40 groupes
dans quatre campagnes sérielles : 8 publics, 9 de connexion, 11 de gestion et
12 propres aux observations. Elle recoupe 96 sources locales/distantes, 27
fichiers embarqués, 286 archives de code conservées et 25 captures relues.
Les trois notes sont appliquées puis relues par la console SPARK. Les fonctions
de campagne, instances, réseaux, baux, montages et espaces temporaires sont
libérés ; les archives de code et l’historique suivent leur rétention normale.

La publication depuis l’UI, les commandes de purge/cache, les crons et les
preuves résiduelles du backlog restent ouverts. La commande de qualification
de cette tranche est `python3 -B e2e/execution-suite.py --scope console`.

## Baseline du manuel intégré

L’image courante devient
`sha256:c2dd1e3a3849558fe6202538c21591f8c534bd6c963ecaec1dbe20f5e629904d`.
Le manuel est généré depuis `docs/manual.md` à la construction et affiché dans
la navigation de console. Le backend Python/SQL reste identique à la preuve
moteur ; schéma, configuration de cellule et agent de stockage sont inchangés.

La [preuve du manuel](evidence/manual-console-dev-2026-11-07.json) recoupe 101
sources locales/distantes, 27 fichiers embarqués, 287 archives conservées et les
ressources effectivement servies. Les cinq campagnes sérielles passent 48
groupes : 8 publics, 9 connexion, 11 gestion, 12 exécution et 8 manuel.
Les 33 captures sont relues : huit du manuel/tiroir par le principal et 25 de
régression par les vérificateurs. Le SHA256 documentaire affiché correspond
au fichier du dépôt ; titres, paragraphes et tableau sont aussi vérifiés.
Les trois notes sont appliquées puis relues par la console SPARK. Aucune
ressource active de campagne ni opération en attente ne subsiste.

La commande reste `python3 -B e2e/execution-suite.py --scope console` et inclut
désormais `manual-ui`. SLS-062 est clos ; les autres unités du backlog et
l’objectif global restent ouverts.

## Baseline des reçus d’effacement

Le paquet `8bf1292fb61b28d1644d7488351b527ed9429e06c1f247685514ce52710d1dc4` est installé le 7 novembre.
La migration 004 du registre agent est appliquée après sauvegarde native
`/srv/p2enjoy-serverless/storage-state/backups/before-004-20261107T030639Z.sqlite3`, intègre et en mode 0600.
Les lignes préexistantes de fonctions, reçus de configuration et métadonnées
sont recoupées avec cette sauvegarde ; l’identité de stockage est conservée.
Aucune nouvelle variable ni migration du contrôle. Son image reste celle de
SLS-063. L’ancien paquet refuse 004 : revenir exige une restauration cohérente
explicitement préparée.

La [preuve](evidence/storage-discard-dev-2026-11-07.json) recoupe sept campagnes en série et
106 groupes réels, sans échec/skip, le paquet protégé, les sources, les archives
de code et les ressources libérées. La commande est `python3 -B
e2e/execution-suite.py --scope storage`. Les commandes publiques et la console
restent dans SLS-065. [Contrat](STORAGE_DISCARD.md).

## Déploiement initial et checkpoints de SLS-065

Le [contrat public](CONSOLE_STORAGE.md) est déployé avec la migration 006 du
contrôle : reçus durables, extension des gardes et date de purge. Le déploiement
du 7 novembre suit le contrôle d’absence d’invocations, de validations,
de fonctions actives, d’instances et d’intentions. La sauvegarde SQLite native
`state/backups/before-006-20261107T041204Z.sqlite3` conserve les permissions 0600 ;
son SHA256 est `d5bd52c12099df2be17330476facf7d8c8d53cd748515523f7d3c14189972a05`.
Les anciennes lignes et les 2 705 fichiers d’archives sont recoupés après migration,
avec contrôles d’intégrité et de clés étrangères réussis.

L’image du contrôle est
`sha256:fb01050c7c1055fde4b295c228d24d6086715218872756859d8bbccb2bdbd6cf`.
L’agent 004 reste inchangé. Aucun secret, variable, route ou service de cellule
supplémentaire. Les campagnes ciblées API, console de stockage et manuel passent
26 groupes réels ; les campagnes créatrices nettoient leurs propres objets.
Ces campagnes initiales sont complétées par la qualification finale ci-dessous.

Un retour à l’ancien contrôle exige d’abord zéro commande en cours et une
restauration cohérente base/fichiers/volumes ; une purge effective ne s’annule
pas en restaurant seulement SQLite. Aucune migration descendante automatique.
Les preuves utilisent uniquement leurs propres fonctions et archives, jamais
une purge globale des archives conservées des campagnes précédentes.

Le [checkpoint de reprise](evidence/storage-command-recovery-dev-2026-11-07.json)
conserve sept groupes publics sous panne : garde indépendante de l’agent,
indisponibilité avant décision, révocation Update, collision avec une garde de
configuration, SIGKILL avant décision, puis erreurs cache/artefacts après décision
et reprise. Le même UUID termine sans second effacement après reconstruction.
Quinze groupes de mutations et huit du manuel passent aussi, avec onze captures
relues. L’image du contrôle reste identique ; ses 25 fichiers Python/migrations
sont recoupés. Les trois fonctions de reprise sont purgées, leurs trois répertoires
de code absents, les canaux et réservations globaux vides au repos.
Le helper de mutation ferme désormais son writer sous propriétaire même lors
d’un SIGTERM ; la preuve ciblée rejoue cette transition après la dernière
correction de son assertion d’identité. Les nettoyages de l’ancienne campagne
de mutation conservent leurs archives de code selon son contrat.
La preuve nomme les cas restant à qualifier et la mise à jour finale des notes
SPARK ; aucune nouvelle migration ni modification de configuration de cellule.

Le [checkpoint de validation vivante](evidence/storage-validation-recovery-dev-2026-11-07.json)
ajoute deux groupes de panne du socket Docker et neuf groupes API renforcés.
Le contrôle constate réellement EACCES pendant l’import. La purge conserve ses
réservations et fichiers tant que le validateur n’est pas nettoyé ; le diagnostic
tardif est effacé après reprise. La garde indépendante rétablit aussi le socket
après SIGKILL du helper. Le socket observé appartient à UID 1001/GID 1987, mode
01660 : son groupe n’est pas déduit de celui de SQLite, et son mode est restauré
exactement. Les deux campagnes gardent l’image ci-dessus, sans configuration
supplémentaire. Le collecteur confirme huit fonctions purgées et neuf répertoires
de code absents, avec réservations et allocations globales à zéro au repos.
Ce total inclut les deux fonctions de l’essai initial refusé avant perturbation,
les deux fonctions de validation et les quatre fonctions des deux namespaces API.

Le [checkpoint des décisions](evidence/storage-decision-recovery-dev-2026-11-07.json)
recoupe quatre nouveaux groupes et les sept groupes de reprise rejoués. Une
seconde vraie session SSO est fermée pendant la préparation de purge ; l’abandon
conserve version, fichiers, révisions et configuration. Après commit, les refus
de transport et du writer SQLite conservent le reçu jusqu’à confirmation. Les
gardes indépendantes libèrent le writer et redémarrent le contrôle ; ce dernier
attend la fin de son mutateur Docker par un verrou natif avant de redémarrer.
Le nettoyage physique des six fonctions, l’absence des six répertoires de code,
les budgets à zéro, l’accès aux deux sockets depuis le contrôle et les six timers
corrélés inactifs sont vérifiés au repos. Aucun verrou de redémarrage ne reste.
L’image et les 160 sources couvertes restent identiques entre les deux campagnes.
Aucune nouvelle variable, route, migration ou modification du paquet agent.

### Correction de la purge des archives historiques

Image du contrôle après correction :
`sha256:9110295b4652e011b97bc6edfdb3d368b581a19fb73e5af1d1d2a9e5b8e8d40d`.
L’[image historique](STORAGE_LEGACY_PROOF.md) reconstruite depuis `93f88e5` est
`sha256:6b579d7eaa001d14834d34162e02fff9ef7c955ae5f301f13c7aa76378aeaedb`.
Elle s’exécute uniquement dans la fenêtre temporaire de qualification ; le
contrôle courant et ses trois répertoires sont conservés puis rétablis.

La [preuve](evidence/storage-legacy-recovery-dev-2026-11-07.json) recoupe
22 groupes sans échec/skip sur la nouvelle image, avec 163 sources identiques
entre les cinq campagnes et les 25 fichiers Python/migrations embarqués.
Une [preuve en échec](evidence/storage-legacy-cleanup-defect-dev-2026-11-07.json)
conserve le défaut observé avant correction. Le nettoyage général respecte
maintenant la garde de purge, ce qui préserve le code et son budget quand le
stockage a changé de manière inattendue. Le manuel explique cette attente.

Les deux fenêtres finales ont rétabli les identités des répertoires et du
conteneur original, les bases et artefacts, l’agent et l’API sains ; l’exécuteur
de référence reste intact. Leurs timers/services de garde sont inactifs et
leurs ressources temporaires absentes. Les journaux privés et backups natifs
restent dans `qualification-history/storage-absence-<UUID>` pour la traçabilité.
Le contrôle partiel prouve la restauration après mort du pilote au premier
renommage ; il ne constitue pas une preuve de redémarrage complet de la cellule.
Les cinq fonctions des régressions sont purgées, sept répertoires de code absents
et les budgets globaux à zéro. Les douze captures du manuel ont été relues.

Aucune migration, variable, secret ou route n’est ajouté. Les deux fichiers
officiels de configuration sont inchangés. La suite commune élargie est recoupée
dans la qualification finale ci-dessous. Les notes sont aussi proposées dans le déploiement
de configuration commune du 8 novembre décrit ci-dessous.

### Configuration commune des services — 8 novembre 2026

Image du contrôle :
`sha256:62ad2b7f13f0e274b7365daa39c1b5f3fcf524a32e82fa27d4acf582e7187900`.
Image CLI :
`sha256:3304f057c81d7dd5169752f8cef7d15c6b9f5788b30d513dbdcd05f11b91277c`.

Le provider est enregistré dans le service, les fonctions conservent seulement
leurs surcharges. Le contrôle vérifie les configurations effectives dans les
transactions de gestion ; l’adaptateur borne les fusions connues avant mutation.
Les valeurs communes modifiées s’appliquent aux appels suivants, sans altérer
les instantanés déjà admis. Aucun schéma, variable de cellule, secret ou route
n’est ajouté pour ce changement.

La [preuve](evidence/service-configuration-dev-2026-11-08.json) réunit 191 groupes
sur douze campagnes : 153 sur le poste, puis 24 de plan/package et quatorze de
refus public rejoués dans Docker. Les 165 sources sont identiques avant/après
chaque campagne ; 25 fichiers Python/migrations du contrôle et cinq modules
CLI embarqués correspondent aux sources. Les deux fonctions ciblées et onze
répertoires d’artefacts sont purgés ; réservations et allocations sont à zéro,
aucun conteneur de l’installation ne reste, contrôle/agent/référence sont sains.
Les 21 captures de gestion et de lecture du manuel sont inspectées ; le guide
affiché comporte ses treize chapitres et 39 paragraphes conformes à sa source.

Les trois notes sont mises à jour dans `qualification/spark-notes/` et déposées
dans `/etc/spark/notes/{README,CONTRIBUTORS,INSTALL}.md.?`. Leurs empreintes
correspondent aux sources locales ; les notes actives restent celles du registre
tant que ces propositions ne sont pas adoptées. Le dépôt a vérifié qu’aucune
autre proposition n’était en attente avant écriture. Aucune proposition de
variable, secret ou route n’a été nécessaire. Les deux env_file officiels restent
la seule source de configuration des services.

## Qualification finale du stockage public — 8 novembre 2026

La [preuve](evidence/storage-console-dev-2026-11-08.json) recoupe 29 campagnes,
397 groupes et 72 captures, puis un complément distinct de neuf groupes API.
Les quatorze refus de corps de purge et la version périmée conservent les fichiers,
configurations, versions, commandes, gardes et audit. Les 24 fonctions du replay
et les quatre du complément sont purgées dans huit namespaces ; les deux fenêtres
historiques restaurent les originaux et restent distinctes de ces purges publiques.
Les tables restaurées sont comparées logiquement et les fichiers par empreinte,
sans prétendre à une identité octet par octet des fichiers SQLite redémarrés.

Les 173 sources sont identiques avant/après chaque phase ; deux sources E2E sont
renforcées entre replay et complément, puis deux documents reçoivent leur statut
final. Ces écarts sont explicites dans la preuve. Les 25 fichiers Python/migrations
embarqués et l’image `sha256:62ad2b7f13f0e274b7365daa39c1b5f3fcf524a32e82fa27d4acf582e7187900`
restent identiques. Aucun nouveau build applicatif, migration, variable, secret
ou route. Configuration exclusivement par les deux fichiers officiels de cellule.
Les trois notes actualisées sont proposées et recoupées ; leur adoption n’est
pas revendiquée. Les autres unités du backlog restent indépendantes.

## Adresses d’appel SLS-066 en qualification

Le [contrat](INVOCATION_URLS.md) utilise un montage readonly du répertoire
`/etc/spark` dans le contrôle, sans nouvelle variable, secret, migration ou
service. L’image du contrôle utilisée par ce checkpoint initial est
`sha256:1ef637d7b9f111f5a7324c99c99ff365e9e043ff3c28fed16d8f5946c045dd4a`.
Le [checkpoint](evidence/invocation-urls-checkpoint-dev-2026-11-08.json) recoupe
88 groupes, les sources embarquées et les nettoyages ; les preuves résiduelles
ne sont pas annoncées comme acquises.
Le fichier routes est actuellement 0640 root:1001 ; lecture réelle et refus
d’écriture vérifiés dans un conteneur rootless supprimé après relevé. Une
projection future en 0600 sera signalée indisponible, sans modification de ses
permissions par l’application.

L’alias `functions.lelabs.tech` vers 18090 TLS est désormais appliqué depuis
la console normale, avec l’autorisation explicite du seul SPARK. Son DNS A
exact, sa résolution native et les deux HTTPS sont vérifiés. Le contrôle lit
les deux lignes dans la projection officielle. Le reçu distinct conserve la
déclaration initiale interrompue pendant sa vérification, puis sa reprise en
lecture seule ; aucun POST n’est rejoué. Les huit groupes API/CLI et six UI
passent et leurs quatre fonctions sont purgées dans deux namespaces.
La FORGE et les autres SPARK restent hors du périmètre d’administration.
Retrait/détours avec garde, source perturbée et pages sur six domaines restent
à qualifier dans SLS-066.

Le [replay complet](evidence/invocation-urls-regressions-dev-2026-11-08.json)
passe ensuite 35 campagnes et 467 groupes, zéro échec/skip. Six prérequis restent
non comptés ; 186 sources et images sont recoupées avant/après chaque phase.
L’image du contrôle reste identique ; les deux images CLI sont reconstruites
puis figées. Les 32 fonctions suivies dans dix namespaces sont purgées, les
deux restaurations historiques séparées et les 26 fichiers embarqués recoupés.
Les 79 captures fraîches sont recoupées : 61 observations et 18 identités avec
une référence inspectée. Le manuel servi correspond à 14 chapitres/43 paragraphes.
Le Host réel est qualifié en boucle locale ; routes publiques, sources perturbées,
pagination multi-domaines restent ouverts ; le GET CLI 401 est qualifié séparément.

Ce replay ne demande aucun build du contrôle, migration, variable ou secret.
Les trois notes de cellule sont actualisées et proposées par leurs voisins
`.?`, avec empreintes recoupées ; leur adoption n’est pas revendiquée.

Le [complément de transport du catalogue](evidence/invocation-url-transport-dev-2026-11-08.json)
passe ensuite trois groupes propres et treize de régression, sans changement
applicatif. Les 187 sources et images restent identiques avant/après chaque
phase. Les deux vrais HTTP 502 préservent la publication ; six connexions CLI
sans rejeu sont comptées et les fonctions invoquées après reprise. Huit fonctions
sont purgées dans trois namespaces, six gardes terminées et les 26 fichiers
embarqués recoupés. La référence conserve son identité/image/démarrage. Les
trois notes sont actualisées et reproposées, sans application de route, variable,
secret ou migration. Les branches d’erreur du nouveau client restent explicites.


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

## Catalogue global SLS-067 en qualification

Le nouveau build du contrôle et de sa console est déployé ; réseau, routes,
deux env_file et montages conservés. Aucun nouveau schéma, secret ou variable.
L’accueil authentifié devient Fonctions, Namespaces gardant une destination
latérale explicite. La configuration et les volumes restent gérés par leurs
commandes actuelles. L’image est
`sha256:7b52f630b7f071a9fc7659298039b7bfcfe3579ed6fb962ebf0a63db8259f490`.
Les deux services sont sains ; les 27 fichiers embarqués correspondent aux
sources et la référence conserve son identité/image/démarrage. Sauvegarde
SQLite native avant mise en service :
`/srv/p2enjoy-serverless/state/backups/before-function-catalogue-1794163923159023391.sqlite3`,
intégrité vérifiée, migrations 001 à 006.
La [qualification](evidence/function-catalogue-dev-2026-11-08.json) retient
37 campagnes uniques / 489 groupes et six prérequis, en deux époques de clients
sur les mêmes sources produit/images. Les 98 captures sont inspectées ;
91 fonctions suivies purgées dans 23 namespaces et quinze jeux de variables/
secrets de services vidés. Les deux restaurations historiques et le nettoyage
des 39 fonctions des jeux écartés sont séparés. Les deux services sont sains,
la référence conserve son identité/démarrage et les quatre fichiers web servis
en HTTPS correspondent à l’image. Le manuel affiché compte 15 chapitres et
46 paragraphes, avec son empreinte compilée recoupée. Les trois notes actualisées
sont proposées sans adoption ; env, secrets et routes officiels restent identiques.

## Garde des routes : checkpoint sans perturbation

Le contrôle et ses deux routes 18090 restent inchangés. Deux scopes du nouveau
client de garde passent : restauration explicite et perte SIGKILL du pilote
avec restauration indépendante, HTTPS vérifiés et processus terminés. Le scope
d’échéance reste incomplet après URLError sur le HTTPS de l’alias. Le diagnostic
ultérieur observe un ancien cache négatif natif alors que les deux autoritaires
servent le bon A. Aucune modification de résolveur, route, secret, variable ou
image applicative n’est appliquée dans cette étape. La lecture native confirme
services/images/démarrages, agent actif, configuration officielle inchangée et
deux lignes lisibles depuis le contrôle. La qualification de garde et SLS-066
restent ouvertes ; la [preuve](evidence/invocation-route-guard-checkpoint-dev-2026-11-08.json)
conserve l’essai arrêté et son diagnostic. Les trois notes sont reproposées.

## Module de preuve natif partagé qualifié

NativeObserver est déplacé sans changement de son corps vers
e2e/native_control_observer.py, importé par le pilote historique. Synchroniser
le module dans le même répertoire E2E avant son consommateur. Aucun nouveau
build applicatif : neuf groupes de transport passent sur 201 sources, puis
six fonctions sont recoupées purgées dans deux namespaces, six gardes terminées
et les observateurs absents. Les 27 fichiers du contrôle restent identiques.
Les pannes exercent des redémarrages du contrôle ; la référence conserve son
identité, son image et son démarrage. Les deux routes et les fichiers officiels
restent inchangés. Les trois notes restent justes, avec leurs empreintes actives
et proposées inchangées. [Preuve](evidence/invocation-native-observer-dev-2026-11-08.json).
L’extraction seule ne qualifie pas la pause/libération : ses deux preuves
ultérieures sont décrites plus bas. L’échéance de garde est également vérifiée
sur la résolution native rétablie dans le complément ci-dessous.

## Trois déclencheurs de garde vérifiés sans perturbation

Après expiration du cache DNS négatif en amont, les deux noms résolvent
nativement vers l’IP attendue et leurs HTTPS sont vérifiés. Le replay passe
trois groupes sur 201 sources : explicite, mort SIGKILL du pilote et échéance
avec propriétaire vivant. Les ports restent à 18090 ; services, démarrages et
configuration sont inchangés depuis les régressions du traceur commun.
La [preuve](evidence/invocation-route-guard-dev-2026-11-08.json) garde le premier
arrêt séparé. Les trois notes sont actualisées et reproposées ; aucune variable,
secret, route ou image applicative nouvelle. Les cycles effectifs restent à
qualifier à ce checkpoint ; ils sont désormais recoupés dans le complément suivant.

## Cinq cycles réels des routes qualifiés

Le client des cycles passe cinq groupes et sept invocations des URL émises,
sur 203 sources et les mêmes images. Les quatre gardes sont terminées et la
fonction originale est purgée dans son namespace. Les deux routes finales
visent 18090 TLS ; l’alias a un nouvel identifiant après son retrait/recréation,
la canonique conserve le sien. Les services et leurs démarrages, l’agent et
les deux fichiers officiels restent inchangés. Aucun build applicatif ni DNS
supplémentaire n’est appliqué. La [preuve](evidence/invocation-route-cycles-dev-2026-11-09.json)
conserve les données natives exactes, ainsi que le premier arrêt de collecte
sur les seuls horodatages arrondis pendant le passage JSON JavaScript.
Les trois notes sont reproposées. Le vide UI public est qualifié par le complément ultérieur ; les sources perturbées
et les pages suivantes UI/CLI restent ouverts dans SLS-066.


## Pause/reprise native du 9 novembre

Deux groupes réels qualifient libération du GET HTTPS retenu et SIGKILL du
traceur avec reprise indépendante, sur 205 sources et les mêmes images.
La [preuve](evidence/invocation-request-pause-dev-2026-11-09.json) distingue
l’essai initial arrêté sur le timer déjà collecté, sa récupération et le
diagnostic du replay positif. Deux fonctions sont purgées dans deux namespaces,
quatre gardes finies ; contrôle non tracé et sans redémarrage, référence inchangée.
Variables : aucun ajout. Secrets : aucun ajout. Routes : aucun changement,
les deux domaines à 18090 TLS. Notes : README, CONTRIBUTORS et INSTALL actualisées
comme propositions. Configuration : seuls les deux fichiers officiels existants,
aucun nouvel env/ARG ni build. Les deux groupes seuls ne qualifient pas le vide UI
public, qui passe le complément suivant.


## Parcours public du catalogue vide — 9 novembre

Trois groupes réels passent sur 206 sources et les mêmes images. Le GET du vrai
bouton Actualiser survit au détour normal des deux routes vers 18091, termine
à 200/total zéro et rend l’aide vide sur desktop/mobile. Après restauration
18090 TLS, l’UI retrouve les deux domaines et l’URL copiée invoque Docker.
Une fonction est purgée dans son namespace ; helper, timer/service et garde
de routes sont finis. Contrôle non tracé et sans redémarrage, référence inchangée.
[Preuve](evidence/invocation-empty-ui-dev-2026-11-09.json).
Variables : aucun ajout. Secrets : aucun ajout. Routes : deux détours temporaires
restaurés, aucun domaine/DNS nouveau. Notes : README, CONTRIBUTORS, INSTALL
proposés individuellement. Configuration : deux fichiers officiels inchangés,
aucun nouvel env/ARG ni build. Source perturbée et six domaines restent ouverts.


## Alias public et SSO — 9 novembre

Trois groupes passent sur 207 sources et les mêmes images : redirections réelles
de functions.lelabs.tech vers la canonique, API session anonyme sans redirection,
puis connexion et déconnexion UI desktop/mobile via le vrai fournisseur.
Le POST réel de déconnexion est observé par CDP durable ; ses deux indicateurs
sont vrais malgré la navigation. Six captures sont inspectées. Deux sessions
et flows du replay sont absents nativement, ainsi que les deux autres des
essais arrêtés, conservés séparément.
[Preuve](evidence/invocation-alias-entry-dev-2026-11-09.json).
Variables : aucun ajout. Secrets : aucun ajout. Routes/DNS : aucun changement.
Notes : README, CONTRIBUTORS, INSTALL proposés individuellement. Configuration :
deux fichiers officiels et services inchangés, aucun env/ARG ni build nouveau.
Aucune donnée métier créée. Source perturbée et six domaines restent ouverts.


## Garde de permissions du relevé — 9 novembre

Trois groupes réels passent sur 210 sources et les mêmes images. Chmod 000 du
seul fichier officiel /etc/spark/routes, nouvel open du contrôle à errno 13,
release/SIGKILL/SIGSTOP du helper et restitution indépendante sont éprouvés.
Les signaux sont observés par waitpid ; trois helpers/timers/services terminés
et reçus immuables sont recoupés. Le fichier garde nom, inode, contenu, uid/gid,
mtime et mode 0640 ; ctime change. Contrôle/référence et démarrages inchangés.
[Preuve](evidence/invocation-source-guard-dev-2026-11-09.json).
Variables : aucun ajout. Secrets : aucun ajout. Routes/DNS : aucun changement.
Notes : README, CONTRIBUTORS, INSTALL proposés. Configuration : env/secrets
officiels inchangés, aucun build. Programmes/reçus et verrou de preuve sous /run,
aucun daemon permanent. Les refus API/UI sont la prochaine étape non qualifiée.


## Catalogue sous EACCES réel — 9 novembre

Quatre groupes API passent sur 211 sources et les mêmes images : publication
originale via adaptateur, source_forbidden borné pour Read/admin, six refus
sans diagnostic, appels HTTPS des deux domaines pendant EACCES et catalogue
identique après restitution explicite. Quatre invocations réussies, une fonction
purgée et un helper/timer/service terminés sont recoupés nativement.
[Preuve](evidence/invocation-source-api-dev-2026-11-09.json).
Variables : aucun ajout. Secrets : aucun ajout. Routes/DNS : aucun changement.
Notes : README, CONTRIBUTORS, INSTALL proposés individuellement. Configuration :
env/secrets, images, services et démarrages inchangés ; aucun build. Seul le mode
du relevé est temporairement retiré puis restitué à 0640, contenu/inode/mtime
inchangés et ctime modifiée. Rendu UI et autres fautes de source encore ouverts.


## Refus réel dans la console — 9 novembre

Trois groupes navigateur passent sur 212 sources et les mêmes images, depuis
l’accueil/formulaires/publication jusqu’au refus réel et à la reprise. L’alerte
source_forbidden s’affiche en desktop/mobile sans anciennes adresses/copies/
succès. Après restitution, l’URL copiée appelle réellement Docker. Une fonction
purgée, parents supprimés, invocation et garde terminée recoupés nativement.
[Preuve](evidence/invocation-source-ui-dev-2026-11-09.json), cinq JPEG frais.
Variables : aucun ajout. Secrets : aucun ajout. Routes/DNS : aucun changement.
Notes : README, CONTRIBUTORS, INSTALL proposés individuellement. Configuration :
fichiers officiels, services, images et démarrages inchangés ; aucun build. Mode
du relevé retiré puis restitué à 0640, contenu/inode/mtime identiques, ctime changée.
Autres fautes de source et pages UI/CLI sur six domaines restent à qualifier.
