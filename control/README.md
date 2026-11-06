# Plan de contrôle

Le conteneur `serverless-api` sert l’API et la console à
`https://serverless.lelabs.tech`, sur le port interne 18090.
Les [noms d’exploitation](../docs/DEPLOYMENT_NAMES.md) distinguent ce service
du runtime de référence et des conteneurs d’exécution des fonctions.

Implémentation en cours de SLS-020 et SLS-030. Contrats : [API](../docs/CONTROL.md),
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
Expiration, budget, interruption pendant nettoyage et interface de révisions
restent ouverts. L'API de publication ne fournit pas l'invocation.

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
[runtime/README.md](../runtime/README.md). Il n’est pas encore raccordé aux
routes publiques ni à la file d’admission du contrôle déployé. Les preuves de
ce composant ne ferment donc pas SLS-040.

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
code embarqué, les montages et les ressources nettoyées. Les admissions et
routes publiques d'invocation restent à réaliser.

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
Le moteur d’admission et les commandes publiques de purge restent à intégrer.
