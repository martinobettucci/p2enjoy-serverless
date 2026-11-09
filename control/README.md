# Plan de contrôle

Le contrôle008 est déployé en qualification DEV selon
[FUNCTION_VERSION_EXECUTION](../docs/FUNCTION_VERSION_EXECUTION.md). L’upload
prépare un hash et la promotion explicite choisit la cible sans tag ; pools et
états sont gérés par hash sous les limites communes. Le
[checkpoint ciblé](../docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json)
réunit71 groupes dont2 migration/reprise,12 API,5 CLI authentifiés depuis le poste,
6 UI et8 manuel, plus38 packaging/refus dans les images CLI. Les31 fichiers
Python/SQL embarqués sont identiques entre époques API/CLI/UI. Dix fonctions sont
purgées, sans instance ni opération active. Pannes, déclinaison CLI authentifiée
dans les images et régression complète restent ouvertes ; les preuves007 citées
ci-dessous restent historiques.

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

`node e2e/public-invocations.mjs` qualifie l’entrée réelle, les files, les
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
