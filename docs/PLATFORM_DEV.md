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
limites et interruptions de publication, vues de révisions et raccordement
du moteur restent ouverts. La [preuve de reprise](evidence/publication-recovery-dev-2026-11-06.json)
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
baseline suivante. L’admission et l’invocation publiques restent à réaliser.

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
Le moteur d’admission et l’invocation publique,
les commandes de purge/cache de la console et l’observabilité restent à terminer.
