# Schéma du contrôle

Spécification SLS-020. Le schéma SQLite est appliqué par migrations numérotées,
avec table `schema_migrations`. WAL, clés étrangères activées, transactions
explicites courtes ; un unique contrôle coordonne le cycle des instances.
Tous les identifiants d'objets sont des UUID, les dates des secondes UTC.
`security_metadata` conserve un témoin chiffré de la clé maîtresse ; son
contrôle au démarrage refuse une clé différente avant d'exposer le service.

## Objets

- `namespaces` : id, name, description, created_at, updated_at, deleted_at.
- `services` : id, namespace_id, name, description, policy_json,
  environment_json, secrets_cipher, created_at, updated_at, deleted_at.
- `functions` : id, service_id, name, config_json, environment_json,
  secrets_cipher, active_revision_id nullable, created_at, updated_at,
  deleted_at. Une fonction créée sans code est un brouillon.

Les noms sont uniques parmi les objets actifs de leur parent (index partiels).
Une suppression renseigne deleted_at ; les données archivées restent
adressables par ID. Un namespace doit être vide de services actifs avant sa
suppression ; un service doit être vide de fonctions actives. Une suppression
de fonction sera associée au drainage du runtime lors de son intégration.

`config_json` stocke le contrat validé de runtime : handler, runtime, CPU,
mémoire, deadline, idle, instances min/max, concurrence, attente et stockage.
Les secrets sont des mappings chiffrés avec Fernet et la clé maîtresse de
cellule. Seuls les noms sortent dans les lectures de gestion.

Le service conserve la configuration commune, la fonction ses surcharges.
Le remplacement du jeu de secrets de service réutilise `secrets_cipher` et
ne change pas le schéma. Les configurations effectives sont validées dans la
transaction avant mutation, selon
[SLS-031](SERVICE_CONFIGURATION_URLS.md#configuration-de-service-et-surcharges).

## Identités

- `service_tokens` : id, service_id, name, digest unique, prefix, rights_json,
  function_ids_json nullable, expires_at nullable, revoked_at nullable,
  created_at, last_used_at. Le jeton complet n'est jamais enregistré.
- `login_flows` : state_digest, verifier_cipher, nonce, expires_at. Le state
  est aussi lié au navigateur par un cookie HttpOnly à durée courte. Le flow
  est consommé une seule fois au callback.
  La migration 002 ajoute client_address pour borner les flows par client.
- `login_rate` : client_address, window_start, attempts. Fenêtre fixe d'une
  minute ; compteur des flows ouverts, nettoyé à expiration.
- `sessions` : digest, subject, display_name, csrf_digest, tokens_cipher,
  access_expires_at, created_at, expires_at. Les jetons OAuth restent côté
  serveur, chiffrés ; l'expiration absolue est bornée à huit heures. Le payload
  chiffré conserve aussi la valeur CSRF, stable pendant la session et partagée
  entre ses onglets ; csrf_digest permet de vérifier les mutations sans la
  régénérer lors des lectures.

Un jeton restreint à des fonctions ne peut porter Create ni modifier les
variables globales du service. Une liste vide est invalide ; null désigne
toutes les fonctions du seul service. La rotation révoque l'ancien et crée le
nouveau dans une même transaction.

## Audit

`audit_events` : id, actor_kind, actor_id, service_id nullable, action,
object_id nullable, created_at, detail_json expurgé. Les mutations et refus
exploitables sont corrélés à leurs objets ; aucun corps utilisateur, secret,
en-tête d'authentification ou jeton n'est journalisé.
Un refus associé à une identité connue conserve l'acteur et le service de
cette identité, le statut et le patron de route. Les requêtes anonymes
malformées sont consignées dans les journaux bornés plutôt qu'en base pour
éviter une croissance du registre sous trafic anonyme.

## Déploiements et révisions

Contrat SLS-030 : [DEPLOYMENT](DEPLOYMENT.md). La migration suivante ajoute :

- `deployments` : id, function_id, service_id, actor_kind, actor_id,
  expected_function_version, expected_service_version, configuration_cipher,
  events_json, required_right, state, error_code nullable, validation_json
  nullable, reserved_bytes, created_at, expires_at, completed_at nullable,
  revision_id nullable. configuration_cipher devient NULL à la fin du candidat.
- `revisions` : id, function_id, handler, runtime, architecture, image_id,
  archive_sha256, inventory_json, events_json, stored_bytes, created_at,
  deleted_at nullable. Les fichiers résident sous artifacts/{revision_id}.

Le candidat et sa future révision partagent le même UUID. Son dossier privé
`artifacts/{id}` contient `archive.zip` et `code/` dès la réception ; seule la
transaction créant la ligne de révision et son pointeur actif le rend utilisable.
Cette disposition évite une pseudo-transaction entre renommage et SQLite.
Une réservation reste comptée tant qu'un nettoyage échoué n'est pas repris.
Une révision supprimée conserve stored_bytes jusqu'à la suppression physique
confirmée ; son tombstone reste en base avec stored_bytes=0 ensuite.
Un trigger interdit un pointeur actif vers une révision absente, supprimée
ou appartenant à une autre fonction.

États de candidat : prepared, receiving, validating, published, failed,
expired. Les états receiving/validating trouvés au redémarrage sont échoués
et nettoyés, sans publication automatique. Les réservations servent au budget
global avant extraction ; leur somme et les révisions conservées sont comptées
dans les transactions d'admission. Un UUID d'installation dans security_metadata
sert à reconnaître les seuls conteneurs Docker appartenant à ce contrôle.

Le pointeur active_revision_id de functions ne change qu'après validation et
relecture des versions attendues. Le rollback ne déchiffre ni ne restaure
d'ancienne configuration : il restaure le code, le handler et les événements
de la révision choisie, avec les ressources et secrets courants.

Les invocations, instances et exécutions planifiées recevront leurs migrations
dans SLS-040/050.

## Identité du code des révisions

La migration 007 ajoute `revisions.code_hash`, SHA256 canonique nullable pour
les tombstones historiques déjà purgés sans inventaire et les purges 006
engagées dont la décision est fortement corrélée. Le calcul commun
est enregistré sur la connexion de migration avant son script transactionnel.
Un inventaire invalide ou absent pour un code conservé/actif annule la migration.
La reconnaissance d’une purge en attente exige fonction supprimée sans pointeur,
inventaire/événements effacés, commande et garde de même UUID, fonction et service,
décision commit, état pending dans volumes/artifacts, installation et versions
concordantes. Elle conserve les octets et la garde jusqu’au nettoyage normal,
selon [le contrat de reprise](FUNCTION_VERSION_PURGE_UPGRADE.md).
Les inserts futurs exigent un hash complet valide ; un hash connu est immuable.
L’index `(function_id,code_hash,created_at,id)` conserve les doublons UUID
historiques, leurs références et le pointeur actif. L’API `/versions` regroupe
ces alias dans un même snapshot autorisé sans exposer leur code.
Le [contrat de reprise](FUNCTION_VERSION_REGISTRY.md) fixe sélection, pagination,
sauvegarde, retour arrière et preuves. Cette migration ne change encore ni
l’activation à l’upload ni l’admission d’invocations.

## Autorité des versions et promotions

La migration 008 de SLS-074 ajoute `function_versions`, clé primaire
`(function_id, code_hash)` : `revision_id` canonique référencé, `created_at`
initial, `state` available/archived/deleted et `updated_at`. L’alias canonique
doit appartenir à la même fonction et porter le même hash. Les UUID historiques
et la cible active ne sont pas fusionnés ni remplacés pendant la migration.
Les règles de sélection et de conservation sont définies dans
[FUNCTION_VERSION_EXECUTION](FUNCTION_VERSION_EXECUTION.md#autorité-persistante-et-migration).

La première transition008 vérifie son entrée007 dans la même transaction,
avant transformation : cible active conservée et appartenant à une fonction
vivante, références étrangères et cache canonique. Le recalcul reprend la
reconnaissance stricte de purge007 ; un tombstone légitime conserve son cache
connu ou inconnu. Une incohérence annule la transition sans réparation implicite.
Les installations déjà008 ne la rejouent pas. Les [refus et interruptions](FUNCTION_VERSION_MIGRATION_008_RECOVERY.md)
passent dix groupes sur copies historiques, dont interruption WAL puis reprise
du même conteneur. L'image def45648f9e7 est servie en DEV ; la bascule conserve
exactement les17 tables et le schéma déjà008, puis12 groupes API et5 CLI passent.
Les historiques de purge engagée, le premier hash inconnu suivi d'un connu et
les pannes propres de garde restent ouverts ; SLS-074 reste en cours.

`functions` reçoit `first_published_code_hash` et `first_promoted_at`, nullable
avant le premier succès correspondant et immuable une fois renseigné. L’historique
antérieur établit une promotion passée dès qu’une révision existe, même si son
hash a été perdu après purge. Désactiver une cible ne rétablit donc jamais le
droit de première promotion Create.

`deployments` reçoit `code_hash`, `code_changed`, `version_restored`,
`result_function_version`, `default_code_hash_at_publication`, `restore_code_hash`
et `code_only`. Les résultats décrivent la décision de publication, pas la cible
présente. Une réservation de candidat published réutilisé reste comptée jusqu’au
nettoyage confirmé. `invocations` reçoit `requested_code_hash` et
`resolved_code_hash` ; le résolu historique est repris depuis sa révision connue.
Les instances conservent leur UUID d’alias physique ; leur hash est lu dans la
révision immuable, sans nouveau champ positionnel. Les insertions concernées
nomment explicitement leurs colonnes.

Cette migration est installée en qualification DEV avec publication sans
activation, promotion et admission par hash. Deux groupes réels recoupent
alias/cible et données/cache après migration puis redémarrage ; douze groupes API
complètent ce premier checkpoint. Le
[checkpoint ciblé008](evidence/function-version-execution-checkpoint-dev-2026-11-09.json)
ajoute5 groupes CLI authentifiés depuis le poste,6 UI,8 manuel et38 packaging/refus
CLI Docker. Le [complément CLI](evidence/function-version-cli-images-dev-2026-11-09.json)
qualifie ensuite cinq groupes authentifiés par image, sans changement de schéma
ni produit. Les preuves007 restent historiques. Les refus/reprises de008 et la
régression complète restent requis.

## Registre local de stockage

SLS-050 utilise une base distincte, possédée exclusivement par l’agent de
montage : `storage/migrations/001.sql`. Elle ne porte aucune identité publique.
`functions` conserve l’UUID, l’état active/archived/purging/purged, la version,
la configuration publiée et l’intention de mutation. `volumes` conserve le type,
le quota alloué, l’activation, la génération, la phase de montage, l’identité
complète du démon, la dernière mesure et un code d’erreur fixe. Une intention
configure réserve les augmentations jusqu’au commit ou à la compensation.
`leases` associe consommateur, installation du contrôle, fonction, configuration
et montages acquis. Une ligne sans résultat de montage complet représente une
acquisition interrompue : elle exige une réconciliation, pas une santé positive.
`probes` contient au plus une sonde dont la terminaison reste à confirmer.
La migration 002 permet un PID et une naissance absents : la commande unique
et le boot sont inscrits avant lancement pour retrouver un enfant orphelin.
`metadata` conserve l’identité de cette installation de stockage. WAL,
synchronous FULL et verrou de propriétaire protègent les transitions décrites
dans [STORAGE_AGENT](STORAGE_AGENT.md).

## Préparation des quotas par le contrôle

La migration 003 du registre de stockage ajoute configuration_receipts :
function_id unique, operation_id unique, installation_id propriétaire,
configuration_json cible, expected_version de départ, decision committed/aborted
et version résultante. L'intention pending_json de la fonction porte les mêmes
identifiants pendant preparing/prepared/aborting, ainsi que la provenance des
nouvelles lignes et des répertoires, et la réservation supplémentaire.

Commit et abort incrémentent la version de fonction ; elle ne revient jamais à
sa valeur antérieure. Après abandon d'une création, l'agent conserve un état vide
versionné et son reçu, sans allocation ni visibilité dans les objets du contrôle.
Un nouvel identifiant d'opération exige la version courante ; rejouer une demande
ancienne ne recrée donc pas une préparation après remplacement de son reçu.
Les anciennes intentions configure sans provenance conservent leur traitement
de reprise historique ; les nouvelles enregistrent explicitement leurs créations.

Le contrôle utilisera son UUID durable comme installation_id. Les commandes
prepare-configuration exigent function_id, operation_id, installation_id,
configuration et expected_version ; commit-configuration, abort-configuration et
configuration-operation exigent les trois identifiants. La consultation permet
de distinguer la préparation de la décision sans rejouer une mutation.

Un abort portant aussi configuration et expected_version peut écrire un reçu
aborted pour une opération encore inconnue, sans allocation. Ce reçu interdit
à un prepare retardé du même UUID de recréer une préparation après abandon.
La version et les conflits de propriétaire/mutation/bail restent vérifiés.

## Intentions des mutations publiques

La migration 004 du contrôle ajoute function_operations : id UUID primaire,
function_id unique sans clé étrangère (création encore invisible), service_id
référencé, kind configuration/archive, decision undecided/commit/abort,
configuration_json des seuls quotas nullable, storage_version nullable,
expected_function_version nullable, expected_service_version, created_at et
error_code nullable. Les secrets et la configuration applicative ne sont pas
copiés dans cette table. Une intention bloque les mutations incompatibles du
service et de la fonction. Le pointeur de décision commit est modifié dans la
même transaction que l'objet public ou sa suppression logique.

storage_version est écrit avant tout envoi de prepare ; son absence permet de
prouver qu'aucune préparation n'a été envoyée. Une version présente impose une
résolution agent, y compris pour une opération encore inconnue. Après décision
et confirmation, la ligne est retirée ; l'audit métier et le reçu de l'agent
restent les traces durables. Le démarrage résout les seules intentions de ce
contrôle avant leur réouverture. Les tables d'instances et d'invocations seront
ajoutées avec leur moteur ; leur absence n'autorise aucune invocation publique.

## Réservations et invocations

La migration 005 ajoute execution_instances : id, function_id, revision_id,
generation privée, cpu_nanos, memory_mib, state, snapshot_cipher, created_at,
ready_at, last_used_at et error_code. L'instantané contient le nom, la révision,
l'image, les paramètres et la configuration effective chiffrée. La réservation
précède toute acquisition de bail ou création de canal Docker. Une référence
d'instance interdit la suppression logique et physique de sa révision.

invocations conserve id, actor_kind/id, service_id, function_id, revision_id,
instance_id, state, created_at, queued_at, admitted_at, dispatched_at,
completed_at, handler_started nullable, error_code, http_status, logs et
logs_truncated. Les références historiques d'instance/révision restent des UUID
de diagnostic et ne retiennent pas indéfiniment leurs ressources. Les états
actifs sont receiving, queued, admitted et running ; les états terminaux sont
succeeded, failed, rejected, disconnected et interrupted. Aucun corps métier,
réponse, en-tête ni jeton brut n'est enregistré dans ces deux tables.

Le canal de chaque instance appartient à /state/execution/<UUID>, dérivé de sa
réservation. La reprise inventorie les conteneurs et les réseaux séparément,
avec tous leurs labels de propriété ; elle libère aussi les baux incomplets
de cette installation. La réservation ne disparaît qu'après confirmation de
la disparition de Docker, de son réseau, du bail et du répertoire de canal.

## Reçus d’effacement

SLS-064, installée et qualifiée en DEV : migration 004 du registre agent avec
discard_receipts (function_id unique référencé, operation_id unique,
installation_id, kind, expected_version, version). Le reçu et la terminaison
sont atomiques ; pending_json porte identifiants/phase/error_code pendant
nettoyage. [Contrat](STORAGE_DISCARD.md#migration-et-installation).

## Commandes publiques de stockage

Migration 006 du contrôle appliquée en DEV le 7 novembre 2026 pour
[SLS-065](CONSOLE_STORAGE.md), après sauvegarde SQLite native et recoupement
des lignes et fichiers antérieurs :
functions reçoit purged_at nullable. function_operations est recréée avec ses
colonnes et lignes conservées, en autorisant clear-cache/purge sans configuration,
en plus de configuration/archive. Index service et unicité fonction conservés.
storage_commands conserve id UUID primaire, function_id/service_id référencés,
installation_id, kind clear-cache/purge, state preparing/pending/completed/aborted,
phase nullable, storage_absent booléen, expected_function_version, result_version nullable, created_at,
completed_at et error_code nullable. Un index function_id/created_at sert la
dernière commande. Les résultats terminaux restent consultables ; la garde
active reste exclusivement dans function_operations. Aucun secret n’est copié.
