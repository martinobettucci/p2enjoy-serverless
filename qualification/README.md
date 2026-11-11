# Application de qualification DEV

Service synthétique destiné à éprouver les développements de P2Enjoy Serverless.
Spécification : `../docs/DAT.md#qualification`, unité QLF-001.

Le conteneur permanent s’appelle `serverless-runtime-reference` : c’est
l’exécuteur Node des handlers de ce répertoire. Les commandes de test lancent
des clients éphémères séparés qui l’appellent par HTTP. Le nom de service
Compose `qualification` reste son adresse réseau interne.

L'exécuteur de référence sert uniquement au développement. Il ne remplace pas
la plateforme et ne prouve ni SSO, ACL CRUD, quotas par fonction ni autoscaling.
Son accès HTTP est limité à `127.0.0.1:18080`. Ne pas l'exposer publiquement.

Les variantes de `artifacts/` sont des modules originaux destinés au vrai
chargeur de plateforme : ESM, CommonJS, dépendance YAML et défauts d'import
intentionnels. `invoke.cjs` et `invoke.mjs` ajoutent les handlers d’invocation,
les gros corps et les pannes réellement déclenchées dans Docker.
`function-versions.cjs` sert la migration et le pilote par hash : exports primary
et secondary, marqueur de paquet, écritures données/cache, délai réel et empreinte
du secret effectif. Il est publié par les API et exécuté dans le runtime isolé.
`service-configuration.cjs` expose des valeurs publiques et une empreinte de
secret pour qualifier les valeurs communes du service et les surcharges par
la passerelle réelle ; la valeur secrète n’est pas renvoyée.
`scheduled-versions.cjs` fournit deux handlers originaux A/B qui attendent
vingt secondes : le cycle E2E des planifications change réellement la cible
pendant l'appel admis, puis vérifie son marqueur et son hash après terminaison.
`scheduled-admission.cjs` fournit les handlers originaux d'admission planifiée :
attente315s, écritures synchronisées sur le volume exclusif, attente HTTP jusqu'à
une date réelle et dépassement de deadline. La campagne correspondante vit dans
`e2e/schedule-admission.mjs` ; elle passe par la publication et la passerelle.
`scheduled-memory.cjs` expose une allocation pendant20 secondes et restitue
la mémoire déclarée au contexte ; `e2e/schedule-memory-version.mjs` recoupe son
vrai plafond Docker8192Mio après un refus RAM, et réutilise le handler exclusif
pour le changement de version avant admission.
`volume-operations.cjs` écrit, relit, supprime et sature réellement les volumes
/data et /cache ; il conserve l’errno Linux EDQUOT (-122), que Node expose
actuellement sous code UNKNOWN. Leur campagne se lance séparément selon
[runtime/README.md](../runtime/README.md). Elles ne modifient pas l'exécuteur
de référence ni son manifeste.

## Installer, lancer et vérifier

Prérequis : Docker Engine avec Compose, Bash. Aucun Node installé sur l'hôte
n'est requis. L'image Node 24 est verrouillée par digest ; la dépendance YAML
est verrouillée par `package-lock.json`. Les services externes sont inutiles.

Depuis ce répertoire, exécuter une commande à la fois :

```sh
bash dev.sh build
bash dev.sh up
bash dev.sh check
bash dev.sh test
bash dev.sh probe
bash dev.sh recreate-proof
bash dev.sh status
```

Dans le SPARK, utiliser `bash dev.sh --spark <commande>` pour chacune. Cet
argument ajoute obligatoirement les deux `env_file` du contrat de cellule.
La pile utilise exclusivement le profil `dev`. Aucun profil PREPROD/PROD.
`test` lance un conteneur client distinct qui appelle le service déjà déployé
par HTTP, sans importer ses modules ni démarrer de serveur. Aucun mock, faux
serveur, interception réseau ou substitution de dépendance. Les scénarios sont
séquentiels ; un prérequis absent fait échouer la campagne, sans test ignoré.
La matrice complète est dans `../docs/TEST_MATRIX.md`. Sur le SPARK DEV,
`bash dev.sh --spark operations` vérifie aussi confinement, logs, arrêt actif,
manifestes invalides et pannes de stockage/processus dans des conteneurs isolés
portant la même image réelle. Python 3 est requis sur la cellule pour ce pilote.
`recreate-proof` incrémente le compteur, mémorise la génération du cache,
crée un job partiel, recrée le conteneur puis vérifie les deux volumes et
reprend le calcul du job jusqu’à son résultat complet.

Logs et arrêt, avec le même argument `--spark` sur la cellule :

```sh
bash dev.sh logs
bash dev.sh stop
```

Le code peut aussi se travailler avec Node 24 : `npm ci --ignore-scripts` et
`npm run check`. Ce dernier est un contrôle statique, pas une preuve E2E du
déploiement. `npm test` s'exécute dans le conteneur client et nécessite le vrai
service Compose démarré, joignable sous son nom de service `qualification`.
`npm start` est l'entrée du conteneur et écoute sur toutes ses interfaces ;
préférer Compose pour bénéficier de la publication limitée à la boucle locale.

## Utiliser le banc

Le serveur de référence expose HTTP sur `127.0.0.1:18080` de l'hôte DEV :

```sh
curl --fail http://127.0.0.1:18080/healthz
curl --fail http://127.0.0.1:18080/catalog
curl --fail -H 'Content-Type: application/json' -d '{"message":"essai"}' http://127.0.0.1:18080/functions/echo
```

Le handler `business` exige un véritable jeton confidentiel fourni par la
cellule sous `QUALIFICATION_BUSINESS_TOKEN`, transmis en `Authorization:
Bearer <jeton>`. Sans configuration, il répond 503 et n'accorde aucun accès.
L'ancien marqueur public n'est plus une identité de démonstration acceptée.
Le serveur n'implémente aucune authentification de plateforme. Ne jamais y
injecter de code, jetons ou données de client. `serverless.yml` décrit ce banc.
`serverless.platform.yml` réutilise ses handlers avec quotas, variables et
secrets déclarés pour la plateforme. La CLI `python3 -m adapter` sait produire
son plan et ses ZIP. Les routes d'upload et de validation Node sont intégrées
au contrôle DEV ; les onze groupes de `e2e/deployments.mjs` et les sept de la
CLI passent dans la [preuve authentifiée](../docs/evidence/deployment-authenticated-dev-2026-11-06.json).
La variante originale `artifacts/deployment-delay.mjs` effectue
un véritable import asynchrone pour observer les révocations et modifications
concurrentes pendant la validation Docker.
`artifacts/storage-validation-delay.mjs` écrit un marqueur puis attend réellement
soixante secondes à l’import. La campagne
`node e2e/storage-validation-recovery.mjs`, depuis la racine après synchronisation
sur le SPARK, utilise ce module pour vérifier une purge pendant validation vivante,
le diagnostic tardif et le nettoyage après indisponibilité temporaire du socket
Docker. Ses deux groupes passent dans la
[preuve SLS-065](../docs/evidence/storage-validation-recovery-dev-2026-11-07.json).
`artifacts/log-secret-then-throw.cjs` écrit réellement le secret injecté sur
stderr puis échoue à l'import : la preuve exige le préfixe conservé et la
valeur expurgée. Le module `throws.cjs` éprouve seulement l'exception d'import.
`artifacts/publication.cjs` relit les métadonnées de sa vraie révision, les
variables, l’empreinte du secret et un compteur sur /data. Les campagnes
de publication l’invoquent pour vérifier le code actif et la conservation
de la configuration après publication et retour à une révision antérieure.

| Fonction | Contrat à qualifier |
| --- | --- |
| `echo` | HTTP, corps, query, contexte et identifiant d'invocation |
| `binary` | Réponse binaire encodée en base64 par le handler |
| `callback` | Callback et Promise : première terminaison seulement |
| `business` | Contrôle d'un vrai jeton métier configuré, sans succès simulé |
| `configuration` | Variables déclarées et présence d'un secret sans sa valeur |
| `state` | Compteur persistant, GET ou POST avec incrément de 1 à 10 |
| `cache` | Cache reconstructible, GET et invalidation par DELETE |
| `worker` | Calcul PBKDF2 sur les entrées d'un job nommé, checkpoint et reprise |
| `failure` | Exception, rejet de Promise ou sortie brutale |
| `sleep` | Attente bornée pour éprouver le timeout |
| `spin` | Boucle CPU volontairement interrompue par le superviseur |
| `relay` | Appel HTTP de pairs réels limités à echo, failure et sleep |

## Configuration

Le serveur peut démarrer sans secret, mais cela ne qualifie pas les parcours
d'authentification et d'injection de secret présent. `configuration` comprend
`QUALIFICATION_PUBLIC_LABEL` (texte public,
défaut invariant `qualification`) et `QUALIFICATION_SYNTHETIC_SECRET` (secret
de test uniquement, présence rendue sous forme booléenne). Dans le SPARK, ils
doivent venir des fichiers de cellule ; aucun `.env` n'est créé. Le jeton
`QUALIFICATION_BUSINESS_TOKEN` est un secret requis pour activer `business`.
Les tests lisent les mêmes fichiers de cellule que l'application, sans injecter
ou fabriquer de configuration. L'absence de secrets fait échouer la campagne.
Sur le SPARK DEV autorisé, les deux secrets et le label ont été posés par
l'API normale de la console, au seul niveau de ce Spark. Leurs valeurs restent
hors du dépôt et des rapports. Le cas sans configuration est également éprouvé
dans un vrai conteneur dont le manifeste ne déclare aucune variable de fonction.

L'environnement ambiant n'est pas transmis intégralement aux fonctions. Les
chemins de stockage et l'adresse du pair de `relay` sont des valeurs calculées
par l'exécuteur, pas une configuration de déploiement à recopier.

## Données de démonstration

Les données durables et le cache sont stockés dans deux volumes dédiés à ce
banc. Un arrêt ou une recréation les conserve ; aucune suppression de
volume ne fera partie des commandes normales de test ou de déploiement.

Les fonctions state, cache et worker acceptent `?key=<identifiant>` (1 à 64
caractères alphanumériques, tirets et underscores). GET lit, DELETE supprime
uniquement cette ressource ; POST incrémente le compteur ou lance/reprend un
job. Un job est créé avec `{"items":["texte", "autre texte"]}`, de 1 à 128
entrées, chacune de 128 caractères au maximum. Changer les entrées d'un job
existant est refusé avec 409. Les résultats calculés sont réellement stockés.

Chaque campagne crée des identifiants uniques et nettoie ses ressources via
HTTP. Elle ne lit ni ne modifie directement les fichiers applicatifs. Le volume
de rapports est réservé au client E2E ; il conserve les observations attendues
entre les deux étapes de la vraie recréation Docker.

## Limites explicites

Une invocation = un processus enfant frais. Le banc n'offre pas encore de
conteneur par fonction, d'instance chaude, de cron, d'autoscaling, de garantie
exactement une fois, de quota disque par fonction, de SSO ni d'ACL plateforme.
Les budgets mémoire du manifeste sont déclaratifs ; le catalogue le signale.
Le conteneur complet est limité à 384 Mio, 0,5 CPU et 96 processus. Les délais
d'invocation incluent le démarrage du processus enfant. Seul le sous-ensemble
de manifeste présent est pris en charge ; les extensions de fonction inconnues
sont refusées.

La file d'admission est limitée à seize requêtes. Un appel interne peut être
refusé si cette file est saturée ; `relay` propage alors le statut d'erreur du
pair. Aucun mécanisme de réservation de capacité interne n'est revendiqué.
Les scénarios restent séquentiels. Les scénarios de contention et de saturation
émettent plusieurs vraies requêtes comme charge d'un seul scénario, puis
attendent leur fin et nettoient leurs ressources. Le relais propage les vrais
statuts 500, 504 et 429 de ses pairs. L'admission est observée via la santé.
Aucun serveur de substitution n'est utilisé.

## Fixture originale des reprises de publication

`artifacts/publication-recovery.cjs` renvoie le marqueur du paquet, l'UUID de
requête, le libellé effectif et le SHA du secret synthétique. Un délai d'import
Node optionnel de 8 s, borné par le module, permet d'observer un vrai validateur
vivant. Le client empaquette ce module avec un marqueur différent par code et
256 Kio aléatoires pour la réception partielle. Il passe seulement par les API
et Docker. Huit invocations, les plafonds et deux reprises passent dans la
[tranche dédiée](../docs/evidence/function-version-cli-recovery-regressions-dev-2026-11-09.json),
avec dix fonctions purgées et garde indépendante après perte réelle du helper.

## Fixture de planification pendant un vidage de cache

`artifacts/scheduled-storage.cjs` écrit et synchronise les seuls records de
données/cache demandés par le POST HTTPS, puis renvoie leur contenu avec
l'UUID et les métadonnées publiques d'exécution. Le journal du tir suivant
recoupe la donnée conservée et le cache absent après sa commande réelle.
Le client `node e2e/schedule-unavailable.mjs` passe par les API de plateforme,
Docker et FUSE ; contrat : [SCHEDULE_UNAVAILABLE](../docs/SCHEDULE_UNAVAILABLE.md).

## Fixture du maximum et de la réutilisation planifiés

`artifacts/scheduled-capacity.cjs` attend au plus45s sur une date de libération
fournie au HTTP ; les tirs planifiés terminent immédiatement. Ses marqueurs
publics recoupent UUID, trigger/slot, méthode/corps et dates de début/fin dans
le runtime réel. Le client `node e2e/schedule-instance-reuse.mjs` compare les
instances/CID avant et après les frontières ; contrat :
[SCHEDULE_INSTANCE_REUSE](../docs/SCHEDULE_INSTANCE_REUSE.md).


## Fixture de capture de rétention

`artifacts/scheduled-retention.cjs` attend réellement deux secondes puis répond
avec les métadonnées du tir. Le pilote attend running/handler_started avant
d’attacher son observateur natif ; le démarrage froid reste libre. Le backup
pris après succès et avant clôture vieillit ensuite sur l’horloge réelle, selon
[SCHEDULE_RETENTION](../docs/SCHEDULE_RETENTION.md). Le client de capture est
`node e2e/schedule-retention-capture.mjs`, avec SSO réel et purge publique.
