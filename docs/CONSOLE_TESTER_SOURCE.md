# Testeur HTTP : source des domaines indisponible

Complément de [SLS-071.2](BACKLOG.md#sls-071) après les preuves43/46/42/32.
Les checkpoints restent distincts. Décision avant code : utiliser la garde
existante de [refus réel de lecture](INVOCATION_SOURCE_PERMISSIONS.md), sans
modifier son programme qualifié ni remplacer la projection par une copie.

## Panne réelle et invariants

Le client original `e2e/function-http-client-source-access.mjs` crée sa seule
fonction dans `source-access-XXXXXXXX`, avec nonce UUID complet dans les
descriptions du namespace et du service `source-access-fixture`. Ce scope est
celui exigé par le helper existant `invocation-source-permissions.py`.
Publication normale, handler original du dépôt et vrai jeton Read temporaire ;
SSO depuis l'accueil et parcours UI vers Tester. Aucune référence client utilisée.

Au repos, armer le superviseur existant avec l'image courante et délai120s,
attendre guard-armed puis fault-active et nouvel open réel errno13. Le helper
fchmod(000) du seul fichier officiel `/etc/spark/routes`, sans changer contenu,
nom, inode, uid/gid ou mtime. Le contrôle continue de lire sa vraie projection
readonly. Ctime change nécessairement et n'est jamais déclaré restauré.
Fichiers de variables/secrets, routes/DNS enregistrés et FORGE sont inchangés.

La garde indépendante et son programme figé sont ceux déjà qualifiés par066.
Le client vérifie PID/superviseur, fin native du helper, reçu de restauration,
retour du mode initial et nouvel open réussi, santé et identités des deux
services. Une restitution inconnue interdit le nettoyage métier ; le client
rejoint le seul SSH local avec échéance et préserve son diagnostic. Aucun
programme de restauration, source ou réponse n'est simulé.

## Matrice fonctionnelle

1. Avant faute, lire le catalogue réel et composer/envoyer depuis Tester. La
   réponse200, son hash promu et son UUID d'invocation doivent être présents.
   Attendre l'extinction réelle de l'instance avant d'armer la faute.
2. Sous EACCES, appeler le véritable POST `/test-invocation` avec la destination
   connue avant la faute :503 marqué du contrôle, message de catalogue
   indisponible sans chemin interne ni valeur de jeton, aucune nouvelle
   invocation. La faute de découverte ne retire pas les routes actives : les
   deux URL HTTPS connues restent invoquées réellement comme témoins positifs.
3. Depuis la page déjà ouverte, Actualiser les adresses relit source_forbidden.
   Plus de sélection/URL, cURL, réponse ni téléchargement périmé ; envoi désactivé.
   Les saisies éphémères sont conservées. Le hash courant indisponible ne doit
   pas être présenté comme une absence de cible promue, puisque cette cible
   existe toujours. Focus après lecture et absence de débordement sont vérifiés,
   avec captures desktop/mobile. Un GET HTML réel recoupe `connect-src 'self'`
   uniquement, sans wildcard ni ancienne origine d'alias.
4. Libération explicite puis fin du helper/timer/service. Actualiser retrouve
   domaines, endpoints et hash identiques. Choisir l'alias officiel puis envoyer
   de nouveau : réponse200 Docker réelle, hash/UUID exacts et capacité réutilisée.

Le relevé natif `e2e/function-http-client-source-inspect.py` accepte seulement le
namespace et son nonce, vérifie les descriptions et retourne les métadonnées
nécessaires, jamais code, secret ou ciphertext. Les fonctions, jetons et parents
sont nettoyés par les API normales après restitution confirmée ; absence physique,
intégrité/FK, migrations, réservations/baux/gardes et artefacts sont recoupés.
Les attentes asynchrones sont protégées dès création puis jointes ; la rétention
stdout/stderr de l'opérateur est bornée. Les erreurs restent des reçus incomplets.

## Attribution et limites

Ce complément éprouve la branche commune d'indisponibilité du testeur par une
véritable source refusée, avec UI et CSP. Il ne revendique pas une nouvelle
preuve de source physiquement manquante, format invalide ou changement pendant
lecture : ces causes du lecteur commun restent dans [SLS-093](BACKLOG.md#sls-093).
Aucun statut ne doit les présenter comme exécutées par le refus EACCES.
L'exception inattendue d'une tâche du relais relève séparément de071.6.
Les régressions communes et captures inspectées précèdent toute qualification.
Statut : spécifié, client non implémenté/non exécuté.
