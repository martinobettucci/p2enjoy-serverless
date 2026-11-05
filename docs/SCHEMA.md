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

Les révisions, invocations, instances, réservations et schedules recevront
leurs migrations dans SLS-030 à SLS-050. Leur absence n'est pas simulée par
des lignes de démonstration.
