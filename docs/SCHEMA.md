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
