# Plan de contrôle

La tranche serveur [SLS-070](../docs/CONSOLE_EDITOR.md) ajoute les sources,
brouillons chiffrés et publication du code enregistré par le pipeline Docker
courant. Migration010 implémentée, déploiement et E2E à exécuter. La facette
Éditeur de la console reste à réaliser ; aucune clôture de critère revendiquée.

SLS-089 est déployée sur e81007c5, après sauvegarde native SQLite et sans
changement de schéma ou configuration de cellule. La [preuve partielle](../docs/evidence/sso-session-recovery-dev-2026-11-11.json) passe 33 groupes
sur 359 sources : 8 ciblés SSO, 8 du manuel, 8 publics, 9 de connexion. 30 captures sont recoupées,
manuel : 16 chapitres et 57 paragraphes. Seul 089.4 est qualifié : durée réelle 300 s et
renouvellement après expiration. Les profils sans droits, négatifs azp/aud et
rotation/pending503 restent ouverts. Les checkpoints ci-dessous gardent leur
image et leur époque historiques.

Le contrôle008 est déployé en qualification DEV selon
[FUNCTION_VERSION_EXECUTION](../docs/FUNCTION_VERSION_EXECUTION.md). L’upload
prépare un hash et la promotion explicite choisit la cible sans tag ; pools et
états sont gérés par hash sous les limites communes. Le
[checkpoint ciblé](../docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json)
réunit71 groupes dont2 migration/reprise,12 API,5 CLI authentifiés depuis le poste,
6 UI et8 manuel, plus38 packaging/refus dans les images CLI. Les31 fichiers
Python/SQL embarqués sont identiques entre époques API/CLI/UI. Dix fonctions sont
purgées, sans instance ni opération active. Le
[complément CLI Docker](../docs/evidence/function-version-cli-images-dev-2026-11-09.json)
passe cinq groupes par image, avec vingt clients disparus, douze invocations et
deux fonctions supplémentaires purgées. Produit, images et fichiers officiels
restent identiques. Le [complément de validation](../docs/evidence/function-version-validation-recovery-dev-2026-11-09.json)
passe quatre groupes sous refus socket/canal et reprise avec garde indépendante,
plus cinq invocations. Les deux fonctions des essais/replay sont purgées ; le
contrôle ne redémarre pas. Les autres pannes et la régression complète restent
ouvertes ; les preuves007 citées ci-dessous restent historiques.

Le conteneur `serverless-api` sert l’API et la console à
`https://serverless.lelabs.tech`, sur le port interne 18090.
Les [noms d’exploitation](../docs/DEPLOYMENT_NAMES.md) distinguent ce service
du runtime de référence et des conteneurs d’exécution des fonctions.

Implémentation en cours de SLS-020, SLS-030 et SLS-040. Contrats : [API](../docs/CONTROL.md),
[schéma](../docs/SCHEMA.md), [SSO](../docs/sso.md), [publication](../docs/DEPLOYMENT.md).

Python 3.14, FastAPI, SQLite WAL et authentification OIDC confidentielle.
Les identités et les objets de gestion persistent sous `/state`. La clé
maîtresse et le secret client proviennent de la cellule, avec les autres
paramètres documentés dans CONTROL. Aucun profil PREPROD/PROD.

Depuis `/srv/p2enjoy-serverless/control` dans le SPARK DEV, comme spark-docker,
exécuter séquentiellement :

```sh
bash dev.sh build
bash dev.sh up
bash dev.sh status
```

`bash dev.sh logs` affiche les logs bornés ; `bash dev.sh stop` arrête le
contrôle en conservant la base. Le build utilise les sources voisines `web/`
et ses dépendances verrouillées. L'image sert la console et l'API sur 18090,
dans le réseau hôte du SPARK ; `/state` monte le répertoire durable de métadonnées.
Les deux env_file officiels de la cellule fournissent la configuration et
l'interpolation Compose. `SERVERLESS_STATE_HOST_PATH` désigne le montage durable,
`SERVERLESS_DOCKER_SOCKET_HOST` le socket rootless monté sous `/docker.sock`,
et `SERVERLESS_RUNTIME_IMAGE` une empreinte locale `sha256:…` du runtime qualifié.
`SERVERLESS_ARTIFACT_BUDGET_MIB` vaut 4096 par défaut. Les paramètres sont
appliqués depuis les propositions de cellule avant le démarrage.

Les contrôles publics, de l'accueil, du réseau et des limites SSO ont réussi
sur DEV. Trente-huit scénarios de panne/démarrage passent, dont le verrou exclusif et la
reprise automatique de maintenance. Huit groupes publics passent sur cette
image : [preuve du contrôle de publication](../docs/evidence/deployment-control-dev-2026-11-06.json).
La [preuve de gestion authentifiée](../docs/evidence/control-management-dev-2026-11-06.json)
ajoute 19 groupes API et 11 parcours UI, ainsi que huit groupes publics rejoués
sur l'image corrigée. Objets, droits, secrets, concurrence et persistance après
redémarrage sont éprouvés avec la vraie session SSO. Les cycles de rôles,
de renouvellement et de clés du fournisseur restent ouverts dans SLS-020.

La configuration commune de service est déployée dans SLS-031 : catégories
provider conservées à ce niveau, surcharges de fonction et remplacement explicite
du jeu de secrets. Les mutations de gestion partagent le contrôle de configuration
effective avec la publication et le moteur. La
[preuve](../docs/evidence/service-configuration-dev-2026-11-08.json) recoupe 191
groupes, les 25 sources Python/migrations embarquées et le nettoyage physique.
L’API conserve les schémas de données existants ; aucune migration ni nouvelle
variable de cellule n’est nécessaire. `replace_secrets` est un champ applicatif
de `/api/services/{id}/configuration`, documenté dans [CONTROL](../docs/CONTROL.md).
La [preuve complémentaire](../docs/evidence/service-configuration-transport-dev-2026-11-08.json)
qualifie la perte réelle d’une réponse de modification commune avant traitement
et après commit, avec garde indépendante, relance explicite et invocation Docker.
Cinq groupes natifs puis treize groupes de configuration passent sur la même
image du contrôle, sans modification de ses sources ; SLS-031 est clôturée.

`app/validator.py` fournit le pilote de chargement Node de SLS-030. Sa CLI
est qualifiée sur le SPARK avec le runtime isolé, selon
[runtime/README.md](../runtime/README.md). Elle est désormais incluse dans le
contrôle et appelée par `app/deployments.py` après extraction de l'archive.
La migration 003 ajoute candidats et révisions. Un verrou exclusif protège
l'état ; le démarrage reprend les seules validations de cette installation.
L'activation de la révision et de sa configuration est une transaction SQLite.
Une révision active ne peut pas être supprimée ; le rollback conserve les
ressources et la configuration applicative courantes.

`node e2e/deployments.mjs`, depuis la racine du dépôt, exige une session SSO
réelle enregistrée par `e2e/authorize.mjs`. Le pilote empaquette les sources
de qualification, crée ses objets et jetons par les API puis exerce publication,
refus, révocation pendant validation, conflits et rollback. Ses onze groupes
passent ; sept groupes CLI passent ensuite sur le même contrôle :
[preuve authentifiée](../docs/evidence/deployment-authenticated-dev-2026-11-06.json).
Les archives conservées sont vérifiées sur disque, les validations Docker
supprimées et les réservations libérées. Quatre groupes supplémentaires
qualifient les plafonds globaux/de révisions et la reprise après SIGKILL
pendant réception ou validation : [preuve de reprise](../docs/evidence/publication-recovery-dev-2026-11-06.json).
Expiration, budget et interruption du contrôle pendant nettoyage restent à
qualifier. La console Code et révisions est livrée par SLS-063. L’API de
publication et la passerelle d’invocation ont des responsabilités distinctes.

`app/artifacts.py` fournit l'extraction bornée des ZIP classiques. Sa CLI
vérifie les en-têtes, les tailles réelles, les CRC et les chemins, écrit dans
un candidat privé puis publie un répertoire readonly sans écraser une
destination existante. L'image dédiée ne remplace pas le contrôle en service.
Depuis ce répertoire dans le SPARK DEV, construire puis qualifier en série :

```sh
bash artifacts-dev.sh build
bash artifacts-dev.sh test
```

La campagne appelle l'image immuable, le packager existant et le validateur
Node ; 112 contrôles réussissent, zéro échec et zéro test ignoré sur le SPARK
le 6 novembre 2026. La [preuve conservée](../docs/evidence/artifacts-dev-2026-11-06.json)
recoupe les sources locales/distantes et le code embarqué.
Son rapport `artifacts-proof.json` n'est valide que si `completed` et
`cleanup` valent true. Cette preuve indépendante de l'extracteur ne qualifie
pas les routes authentifiées qui l'appellent.

`app/instances.py` fournit le pilote réel d’instances chaudes, avec diagnostic
opérateur, limites Docker, canal privé, deadline et fermeture confirmée.
Ses campagnes passent par Docker et les handlers de qualification, selon
[runtime/README.md](../runtime/README.md). Il est raccordé aux routes publiques et à la file d’admission du contrôle
déployé. Les preuves propres à ces admissions restent distinctes de celles du
pilote ; leurs 31 groupes HTTPS passent dans la
[preuve du moteur](../docs/evidence/execution-dev-2026-11-06.json).

## Instances avec stockage géré

`app/storage_client.py` dialogue avec le véritable agent local, via le répertoire
privé monté readonly sous `/storage-agent`. `app/managed_instances.py` acquiert
un bail avant de créer Docker et le libère après destruction confirmée du
conteneur, de son réseau et de son canal. Une panne de stockage retire le
consommateur ; un nettoyage encore impossible reste signalé comme tel et se
reprend après retour de l'agent.

Quatorze groupes réels passent dans l'image du contrôle, avec les handlers
`qualification/artifacts/volume-operations.cjs` : persistance, quotas, partage,
isolation, refus, courses, interruptions et diagnostic CLI. La [preuve de
raccordement](../docs/evidence/managed-storage-dev-2026-11-06.json) recoupe le
code embarqué, les montages et les ressources nettoyées. Les admissions et routes publiques sont déployées en qualification.

## Mutations de stockage des fonctions

La migration 004 et `app/function_operations.py` raccordent les créations,
changements de quotas, suppressions et publications à l’agent réel. La décision
SQL et l’objet métier sont commis ensemble, puis le stockage est confirmé.
Avant décision, une interruption reprend l’abandon ; après décision, elle reprend
la confirmation. Une erreur d’audit SQLite ne masque pas le statut ni les
identifiants d’une modification déjà enregistrée.

`node e2e/function-storage.mjs` utilise la session SSO, HTTPS, les vrais volumes,
Docker et des interruptions du seul contrôle DEV. Treize groupes HTTPS et une preuve ciblée du pilote couvrent aussi
révocation, nom concurrent, bail actif, conservation des fichiers, publication
avec confirmation perdue et rollback. Le helper distant doit être synchronisé
avant la campagne. Les gardes indépendantes rétablissent un agent suspendu même
si le processus de preuve meurt ; le contrôle est explicitement redémarré après
un arrêt demandé à Docker. [Preuve recoupée](../docs/evidence/function-storage-dev-2026-11-06.json).

Les lectures ajoutent `storage_operation`. Un 503 avec
`X-Serverless-Mutation-Committed: true` signifie que la modification est
persistée et attend la confirmation du stockage : relire la fonction ou le
candidat avant de réessayer. Les mutations incompatibles restent refusées.
La suppression archive les volumes ; elle ne libère pas leur allocation.
Le moteur d’admission est intégré ; les commandes publiques de purge restent
qualifiées dans SLS-065. La migration 006, les reçus publics, le vidage du
cache, le catalogue d’archives et la purge sont déployés ; leurs pannes et reprises
sont suivies dans la [preuve ciblée](../docs/evidence/storage-command-recovery-dev-2026-11-07.json).
La campagne courante de mutation comporte quinze groupes, dont la fermeture
du writer de qualification sous SIGTERM réel ; la preuve historique ci-dessus
précède cet ajout. La qualification complète de SLS-065 est recoupée dans la preuve finale ci-dessous.
La [preuve de validation vivante](../docs/evidence/storage-validation-recovery-dev-2026-11-07.json)
ajoute deux groupes sous panne réelle du socket Docker et neuf groupes API
renforcés : diagnostic tardif effacé après nettoyage, UUID lié au type de commande
et archives distinctes malgré la réutilisation des noms. Le contrôle et son image
restent inchangés ; ces campagnes étendent la qualification du comportement livré.
La [preuve des décisions](../docs/evidence/storage-decision-recovery-dev-2026-11-07.json)
qualifie ensuite quatre groupes sur la session administrateur et les pannes après
commit, avec sept groupes de reprise rejoués. La décision est abandonnée si la
session est fermée avant commit ; une décision déjà enregistrée termine après
restauration du transport ou du writer, avec le même reçu. Le redémarrage effectif
par la garde indépendante est aussi recoupé. Les régressions élargies sont incluses dans la preuve finale ci-dessous.

Le [banc historique](../docs/STORAGE_LEGACY_PROOF.md) produit de vraies archives
avec l’API antérieure au registre, puis applique les migrations actuelles.
Il a reproduit un contournement de purge : le nettoyage général retirait le
code malgré une apparition inattendue du stockage. Tant qu’une garde de purge
existe, le nettoyage des révisions/candidats laisse maintenant ses artefacts au
résolveur de purge. La [preuve corrigée](../docs/evidence/storage-legacy-recovery-dev-2026-11-07.json)
passe 22 groupes ciblés et recoupe les 25 sources Python/migrations embarquées,
la restauration des originaux, cinq fonctions de régression nettoyées et douze
captures du manuel. Ce checkpoint historique est complété par la preuve finale ci-dessous.

## Invocations publiques et admissions

La migration 005 conserve réservations et observations d’invocation.
`app/execution.py` réserve CPU, mémoire et place avant Docker, garde les
responsabilités malgré les déconnexions, applique minimum, maximum et extinction
après inactivité, puis réconcilie ses ressources au redémarrage sans rejeu.
`app/invocation_routes.py` exige Read dans X-Serverless-Token, applique origine/IP
et traduit l’événement/réponse Lambda HTTP. Les observations d’instances et
d’invocations exigent Read ou la session administrateur.

Les cinq budgets de cellule et leurs bornes figurent dans
[ADMISSION](../docs/ADMISSION.md). Les minima doivent tenir simultanément dans
ces budgets. Les réservations ne sont restituées qu’après destruction et
libération confirmées, y compris pour les anciennes générations. La santé
est dégradée si cette réconciliation ne peut pas finir.

`python3 -B e2e/public-invocations-suite.py` qualifie l’entrée réelle, les files, les
générations, les budgets, le stockage et les reprises. Ses 31 groupes passent,
avec 221 groupes de régression, dans la [preuve du moteur](../docs/evidence/execution-dev-2026-11-06.json).
Les 55 groupes de configuration/panne, les 14 de stockage, les composants
Docker et les parcours API/UI sont rejoués par `python3 e2e/execution-suite.py`.
Les rapports frais sont liés à l’image et aux sources locales/distantes avant
et après chaque commande. Les prérequis et fautes ciblées sont décrits dans
[e2e](../e2e/README.md). La limite HTTP/1.1 du proxy est explicitée dans
[ADMISSION](../docs/ADMISSION.md#budgets-et-attente).

## Consultation des exécutions

La console présente les facettes Instances et Invocations dans la fiche de
fonction. Les deux API d’observation sont consommées avec la session admin ;
les journaux se déplient dans le flux. La [preuve de console](../docs/evidence/console-execution-dev-2026-11-07.json)
passe 40 groupes réels et vérifie l’identité du backend avec celui de la preuve
moteur. Commande depuis le poste : `python3 -B e2e/execution-suite.py --scope console`.

Le build embarque aussi le manuel d’usage, généré depuis `docs/manual.md` et
accessible dans la navigation de console. Aucune route API ni migration ajoutée.
La [preuve du manuel](../docs/evidence/manual-console-dev-2026-11-07.json) rejoue
les parcours de console et ajoute huit groupes : 48 réussites au total.

La publication UI ajoute la préparation du code conservant la configuration,
la liste administrateur des candidats et l’abandon des seuls candidats préparés.
Le schéma reste inchangé. La [preuve finale de SLS-063](../docs/evidence/publication-console-dev-2026-11-07.json)
réunit 18 campagnes et 312 groupes réels, dont dix API de publication du code,
21 de console de publication et huit du manuel. Les réponses perdues, le vrai
503 de nettoyage et la confirmation de stockage en attente sont éprouvés.
Les 54 captures ont été inspectées ; sources, image et nettoyage sont recoupés.

La [preuve finale du stockage public](../docs/evidence/storage-console-dev-2026-11-08.json)
passe 29 campagnes et 397 groupes, puis neuf groupes API renforcés. Les refus
directs de purge couvrent quatorze corps invalides et une version périmée avec
UUID frais ; les snapshots natifs sont identiques avant/après. Le contrôle et
son image restent identiques. Les 28 fonctions des huit namespaces SLS-065 sont
purgées et les ressources globales libérées ; les deux restaurations historiques
sont vérifiées séparément.

## Catalogue des adresses d’appel

SLS-066 ajoute `GET /api/functions/{id}/invocation-urls`, autorisé par session
admin ou Read, et le montage readonly `/etc/spark:/spark:ro`. La révision active
fournit chemins et méthodes ; le port ASGI réel filtre les routes officielles.
Source indisponible et absence de domaine sont distinctes ; la santé du moteur
n’est pas affectée par cette consultation. Aucun nouveau secret, réglage ou
schéma. [Contrat](../docs/INVOCATION_URLS.md) et
[checkpoint DEV](../docs/evidence/invocation-urls-checkpoint-dev-2026-11-08.json).
Les changements de routes et la qualification résiduelle restent ouverts.
La [régression complète](../docs/evidence/invocation-urls-regressions-dev-2026-11-08.json)
passe 35 campagnes / 467 groupes sans échec/skip, avec six prérequis distincts,
186 sources avant/après chaque phase et les 26 fichiers embarqués recoupés.
La preuve native du Host est acquise sur la boucle locale ; elle ne qualifie
pas un alias public. Aucun nouveau déploiement applicatif pour ce replay.

## Catalogue global qualifié

SLS-067 ajoute les lectures administrateur `/api/functions`,
`/api/catalogue/namespaces` et `/api/catalogue/services` : recherche avant
pagination dans les métadonnées publiques, filtres croisés et tris stables.
Le [contrat](../docs/FUNCTION_CATALOGUE.md) précise les bornes et l’authentification.
Aucune migration, variable ou dépendance nouvelle. L’image est construite et
déployée sur DEV, avec 27 fichiers Python/migrations embarqués recoupés.
Les huit groupes API et quatorze navigateur passent dans la
[preuve SLS-067](../docs/evidence/function-catalogue-dev-2026-11-08.json), avec
les régressions : 37 campagnes uniques / 489 groupes et six prérequis distincts.
Les 447 groupes aux clients inchangés sont conservés avec leurs rapports et
empreintes ; 42 sont réexécutés après correction des seuls clients de preuve.
Les sources produit et images restent identiques dans les deux époques.
Le recoupement lie les 27 fichiers embarqués, quatre fichiers web HTTPS,
91 fonctions purgées et les variables/secrets de quinze services effacés.


## Calcul canonique des paquets — première étape SLS-074

La bibliothèque racine `function_code_hash.py` et sa CLI calculent l’identité
SHA256 à partir du vrai ZIP extrait et d’un descripteur d’exécution public.
Le [format v1](../docs/FUNCTION_CODE_HASH.md) distingue contenu exécutable et
métadonnées de transport. Depuis control sur DEV, comme spark-docker, exécuter
en série `bash code-hash-dev.sh build` puis `bash code-hash-dev.sh test`.
Le rapport natif est `control/function-code-hash-proof.json`. Le calculateur
ne sert aucun port et ne modifie pas le contrôle en service.
La [preuve](../docs/evidence/function-code-hash-dev-2026-11-09.json) passe
52 groupes dont sept ciblés, neuf invocations Docker et 222 sources. La future
déduplication/promotion/sélection par hash reste dans SLS-074 ; aucune migration
ni modification du pointeur actif n’est livrée par ce composant.


## Registre persistant du code — checkpoint SLS-074

La migration 007 conserve les UUID et remplit code_hash depuis l’inventaire et
le descripteur réels ; les tombstones et les purges 006 corrélées restent inconnus.
GET /api/functions/{id}/versions groupe les alias, avec Read/admin, pagination
bornée et snapshot autorisé. La console copie le hash complet. L’upload active
encore la révision ; déduplication/promotion et invocation par hash suivent.
[Contrat](../docs/FUNCTION_VERSION_REGISTRY.md) et
[preuve](../docs/evidence/function-version-registry-dev-2026-11-09.json) :359 groupes,
69 captures, deux époques de clients et même image finale. Le premier passage au
repos conserve ses 328 groupes et son backup natif distincts. Les commandes DEV
restent build puis up ; vérifier l’image portée réellement après la bascule.
Les références006 et courante sont conservées sous des tags de responsabilité.


## Noms des validateurs qualifiés

Lors de la preuve076, le contrôle sert19cfe884642a, schéma008 inchangé. Ses validateurs
portent `serverless-code-validator-<uuid>` ; les labels reprennent aussi les
anciens noms après interruption. La [preuve076](../docs/evidence/validator-names-dev-2026-11-09.json)
passe57 groupes : ancien orphelin réel, trois imports observés, puis36/12/5
régressions. Les31 fichiers backend ne diffèrent que par validator ; les assets
web restent identiques. Les trois fonctions du replay sont physiquement purgées,
plus la fonction de l’arrêt initial recoupée séparément. Les cinq pilotes de
préparation à collecte sont dans e2e, selon le [contrat](../docs/VALIDATOR_NAMES.md).
L’expiration propre de la garde et les autres pannes008 restent distinctes.

## Capacité des uploads qualifiée sur la même image

Le [complément074](../docs/evidence/function-version-upload-capacity-dev-2026-11-09.json)
passe quatre groupes sur267 sources et19cfe884 conservée : quatre admissions,
cinquième429 avant réception, attente supérieure30s, validations sérialisées,
convergence par hash et relance explicite. Quatre appels préservent stable,
configuration et données/cache ; les trois fonctions des essais sont purgées.
Aucune migration, nouvelle variable, modification de service ou reconstruction
d'image. Commande et limites dans [e2e](../e2e/README.md#capacité-des-uploads--complément-sls-074).

## Reprise des doublons qualifiée

La [preuve074](../docs/evidence/function-version-duplicate-recovery-dev-2026-11-09.json)
passe quatre groupes sur271 sources, avec cinq appels et données/cache1–5.
Un paquet réutilisé reste réservé après commit200 si son ouverture est refusée
pendant le nettoyage. La maintenance reprend après restitution. Le second cycle
coupe le contrôle après commit ; la garde indépendante restitue puis démarre
le même conteneur, qui conserve published et termine le nettoyage. Le helper
SIGKILL est recoupé par waitpid, la garde dans son journal systemd. Une fonction
purgée physiquement, deux gardes terminées ; même19cfe884/configuration et
référence, nouveau démarrage du contrôle attendu. Aucune migration ni variable
ajoutée. Commande et limites dans [e2e](../e2e/README.md#reprise-des-paquets-dédupliqués--complément-sls-074).

## Gardes de migration008 déployées en DEV

La [preuve de reprise](../docs/evidence/function-version-migration008-recovery-dev-2026-11-09.json)
réunit dix groupes de composant sur276 sources et17 groupes publics sur277
sources : six refus, témoin, verrou/reprise, contraintes, interruption WAL puis
12 API et5 CLI. Le SIGKILL est observé après une vraie écriture de frame non
commise ; rollback007 exact et relance du même conteneur appliquent008.
Les2882 publications et4418 invocations historiques sont recoupées. Les replays
ne s'ajoutent pas aux anciens checkpoints comme comportements nouveaux.

La bascule vers def45648f9e7 crée le conteneur e661516b le
2026-11-09T18:25:10.056771655Z. Le seul delta parmi31 backends est le préfixe008,
le web reste identique. La base déjà008 n'a pas rejoué ce script ; ses17 tables
et son schéma sont strictement identiques avant/après remplacement. Le backup
natif privé est conservé dans `qualification-history/migration008-deployment-backup-b6c39eaeb4c447f2a7aab719902f938c`. Aucune restauration DB automatique.

Les deux fonctions publiques sont purgées,16 appels réussissent et un refus
attendu est conservé. Gardes désarmées, référence et fichiers officiels inchangés,
ressources actives nulles. L'essai arrêté avant garde sur une erreur du pilote
est conservé séparément. Les pertes propres des gardes et autres pannes restent à éprouver selon [le contrat](../docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md).


## Purges historiques reprises jusqu'à008

La [preuve](../docs/evidence/function-version-purge-migration008-dev-2026-11-09.json)
passe22 groupes : quatre fenêtres006/007→008 en volumes/artifacts, une fenêtre
007/artifacts avec restitution indépendante après perte du pilote, puis trois
refus de paramètres avant garde/arrêt/déplacement. Les identités inconnues
restentNULL ; les hashes connus restent attachés aux mêmes révisions et dates
dans une version deleted. Les anciens champs sont conservés ; seules phase et
erreur de l'opération exacte peuvent progresser vers artifacts sous EACCES.

Les quatre fenêtres normales terminent leur purge et persistent après restart.
La cinquième conserve la purge pendant migration puis retire l'installation
temporaire par la garde. Les cinq restitutions retrouvent exactement les17 tables,
le registre de stockage et5982 fichiers d'artefacts originaux ; les cinq unités
sont inactives. Le contrôle original e661516b conserve def45648, avec démarrage de ce checkpoint
2026-11-09T18:52:49.904838248Z. Référence, configuration et routes inchangées,
ressources actives nulles, aucune nouvelle image produit ni migration. Les autres pannes restent nécessaires dans SLS-074 ; les corrélations007 sont
qualifiées dans le complément ci-dessous.


## Refus des corrélations de purge007

La [preuve](../docs/evidence/function-version-purge-correlation008-dev-2026-11-09.json)
retient42 groupes sur283 sources :20 copies fautées et1 témoin par phase, depuis
les deux backups007 réellement créés par les fenêtres volumes/artifacts. Chaque
refus garde exactement schéma, tables et marqueurs007 ;38 diagnostics UDF et2
CHECK historical_active_version_required sont recoupés. Les deux témoins appliquent008 puis le même
conteneur redémarre avec un état008 strictement identique. L'échec attendu sur
le socket absent survient après migration et ne vaut pas succès HTTP.

Les anciennes colonnes des16 tables et le registre deleted/hash connu sont
recoupés. Les archives principales, WAL vides et SHM sont conservés par SHA,
taille, identité et droits ; aucun checkpoint ou retrait de sidecar. Les42
conteneurs de copie sont retirés, aucune ressource de copie ni bail/montage.
Le contrôle e661516b/def45648 et son démarrage18:52:49UTC, la référence, les17
tables vivantes et fichiers officiels restent identiques. Aucun déploiement
produit. Un essai arrêté avant copie sur l'absence supposée de sidecars reste
archivé séparément. Les autres interruptions et la campagne complète restent ouvertes dans SLS-074.


## Première identité inconnue : migrations et appels réels

La [première identité inconnue](../docs/evidence/function-version-unknown-first-dev-2026-11-09.json) passe17 groupes sur286 sources :
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


## Décisions de version et réponse perdue

Les [réponses perdues des décisions de version](../docs/evidence/function-version-state-transport-dev-2026-11-09.json) passent9 groupes
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


## Première régression des publications008

La [première tranche de régression008](../docs/evidence/function-version-publication-regressions-dev-2026-11-09.json) passe76 groupes sur292
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


## Console des planifications qualifiée le10 novembre2026

Le contrôle sert désormaisc59b8616, migration009, après sauvegarde SQLite native.
Le [complément de console](../docs/evidence/schedule-console-dev-2026-11-10.json)
passe19 groupes réels : trois ciblés, huit manuel et huit publics ; six handlers
22:10UTC, vide/nom63, pages5+1, clavier/mobile et vrai401→Réessayer200. Pagination
périmée corrigée et manuel servi conforme16 chapitres/56 paragraphes.31 captures
recoupées,17 inspectées personnellement et14 références SHA ; deux fonctions
purgées,34 backends et5982 artefacts conservés. L'unité078 reste ouverte pour
rétention, adaptateur.7 et régression complète. Le [plafond global099](../docs/evidence/instance-limit-public-integration-dev-2026-11-11.json)
est qualifié sur la même image, par installation isolée sans écriture officielle. Les checkpoints
cités plus haut conservent leur image et leur époque historique.

## Identité visuelle déployée le11novembre2026

L'image779aef7b remplacec59b8616 pour la seule modification de favicon.svg.
Les34fichiers backend et les trois autres ressources web sont identiques ; les
neuf migrations restent inchangées. [SLS-100](../docs/evidence/application-icon-dev-2026-11-11.json)
passe29groupes réels et26captures inspectées. Le contrôle est recréé après backup
SQLite natif ; la référence, les5982artefacts et fichiers officiels sont conservés.
