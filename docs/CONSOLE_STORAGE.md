# Gestion du stockage et des archives

Contrat SLS-065, décidé avant implémentation. Le protocole agent de
[SLS-064](STORAGE_DISCARD.md) est déployé ; les routes et écrans décrits ici
restent à implémenter et qualifier. Le manuel change avec leur livraison.

## Portée et droits

Une fonction active expose son stockage avec Read ou une session administrateur.
Vider son cache exige Update, y compris pour un cache désactivé mais conservé.
Le drainage refuse les invocations admises/en cours et ferme les instances au
repos. Données, quotas, code et configuration sont conservés. Un cache absent
produit une opération terminée sans contenu supprimé.

Catalogue et purge exigent une session administrateur, avec CSRF en mutation.
Aucun jeton de service n’y donne accès. Les lignes supprimées de fonction,
service et namespace restent identifiables par UUID ; leurs noms peuvent être
réutilisés. La consultation ne dépend pas de parents actifs.

Une purge concerne une seule fonction déjà supprimée. Elle efface définitivement
ses volumes données/cache, ZIP et code extrait, variables et secrets propres,
configuration de fonction, inventaires de fichiers, événements de déploiement
et résultats de validation. DELETE conserve ces éléments jusqu’à cette décision.
Le code fait déjà partie du périmètre prescrit par DEPLOYMENT, section rétention.

Identifiants, noms, dates, empreintes et métadonnées de révision, reçus et audit
restent conservés. Les invocations suivent leur rétention ordinaire de sept
jours/10 000. La purge ne modifie aucune configuration ou secret des parents,
aucune autre fonction, ni les sauvegardes gérées par le SPARK. Elle ne propose
pas de restauration.

## API et représentations

- `GET /api/functions/{UUID}/storage` : fonction active, Read ; identité,
  version publique, observation stockage, garde active et dernière commande.
- `POST /api/functions/{UUID}/cache-clear` : Update, JSON strict
  `{operation_id: UUID}` et If-Match obligatoire.
- `GET /api/archives` : administrateur ; state retained/purged/all (retained
  par défaut), limit 1–100, offset 0–2147483647, service_id UUID facultatif.
  retained inclut archivage/purge en attente. Réponse items, total, limit,
  offset ; tri deleted_at décroissant puis id. Une lecture SQL cohérente
  détermine total/page ; aucune requête agent par ligne.
- `GET /api/archives/{UUID}` : administrateur ; détail accessible après
  suppression des parents et après purge.
- `POST /api/archives/{UUID}/purge` : administrateur ; JSON strict
  `{operation_id: UUID, confirm_name: nom exact}` et If-Match obligatoire.
- `GET /api/storage-operations/{UUID}` : résultat sans mutation ; administrateur
  pour purge, Update de la fonction active ou administrateur pour clear-cache.
  L’administrateur conserve cet accès après suppression des parents.

Le catalogue rend UUID et noms de fonction/service/namespace, created_at,
deleted_at, updated_at, purged_at, nombre de révisions conservées et octets
d’artefacts encore réservés/stockés. Aucune variable, secret, configuration
applicative, chemin hôte, inventaire ou contenu de code n’est exposé.

Le détail lit une observation expurgée de l’agent : state, version, pending,
leases et, par volume, enabled, quota_bytes, phase, last_measured_used_bytes,
error. La dernière mesure n’est pas instantanée et ne mesure pas les blocs
physiques. Une panne donne une observation indisponible, jamais des zéros ;
une fonction inconnue de l’agent est distinguée de cette panne. Catalogue et
reçus du contrôle restent lisibles sans agent.

Une commande rend id, function_id, kind clear-cache/purge, state
preparing/pending/completed/aborted, phase draining/volumes/artifacts ou null,
created_at, completed_at, expected_function_version, result_version et
error_code fixe ou null. Aucun identifiant de session ni chemin privé.
POST rend 202 en preparing/pending, 200 pour un résultat terminal ; avant
décision, les refus 401/403/404/409/422/428/503 gardent leur sens. Une erreur
agent après commit laisse pending avec diagnostic. Location désigne le reçu.

## Décision durable et répétition

Le client génère un UUID neuf avant l’envoi et le conserve dans l’URL de suivi.
Le contrôle conserve chaque commande et son résultat, comme trace durable
comparable à l’audit, séparée de la garde. Ces petits reçus ne sont pas purgés
automatiquement dans cette version. Même UUID, fonction, type et If-Match
initial retrouvent le résultat avant vérification de la version courante,
sans second effet. Une réutilisation connue avec d’autres paramètres est
refusée. Les droits actuels sont vérifiés avant toute lecture ou répétition.

Une nouvelle commande exige une version courante et aucune autre garde.
Enregistrement preparing et garde function_operations sont atomiques. Après
drainage, le contrôle lit l’agent et persiste sa version initiale sans envoyer
start-discard. Droits et versions fonction/service sont relus après attente et
vérifiés dans la transaction de décision. Celle-ci avance updated_at, marque
commande pending et garde commit, et écrit l’audit ensemble. Une purge marque
aussi les révisions supprimées et efface les configurations décrites plus haut.
Aucune opération physique n’est effectuée dans une transaction du contrôle.

Avant décision, erreur, annulation ou restart abandonnent sans effacement.
Après décision, la reprise envoie le même start-discard avec UUID, installation,
type et version agent enregistrés. Tous les champs et la version du reçu sont
vérifiés ; un reçu inconnu n’autorise jamais une nouvelle version initiale.
Une révocation ultérieure ne défait pas la décision. La garde bloque admissions
et mutations incompatibles jusqu’à terminaison confirmée.

Si l’agent répondait function_unknown lors de la préparation, cette absence
de ligne est persistée et revérifiée à la reprise ; une apparition inattendue
reste une erreur. Un registre connu avec volumes vides n’est pas absent :
il possède une version et exige le reçu normal. Un cache absent ou une archive purgée par le protocole opérateur peut
être confirmé par le reçu normal. Une archive déjà purgée par le contrôle
refuse une nouvelle commande ; répéter le même UUID reste possible.

La phase artifacts attend l’absence de validation/upload actif avant de
retirer les seuls fichiers de la fonction. Elle vérifie les références
d’instances, utilise le nettoyage protégé et synchronise le parent même si
le répertoire a disparu. Les compteurs ne tombent à zéro qu’après confirmation
physique. Cette synchronisation s’applique aussi au nettoyage général des
révisions et candidats, qui peut confirmer des fichiers de cette purge. Le
verrou d’activité commun empêche deux nettoyeurs ou une validation d’agir
simultanément. Une erreur conserve réservations, garde et diagnostic ; la
maintenance reprend. Un vidage de cache ne passe pas par cette phase.

Un upload invalidé par DELETE peut encore terminer son diagnostic. Après son
arrêt effectif et avant le reçu completed, la transaction terminale efface
à nouveau les résultats de validation/configurations de candidats. Aucun
propriétaire d’upload ne peut alors les réintroduire. La preuve maintient une
vraie validation active pendant DELETE/purge puis vérifie cet état terminal.

Reçu terminal, purged_at éventuel et retrait de garde sont atomiques. completed
exige les deux volets confirmés. Une réponse perdue se résout par GET, jamais
par un nouvel UUID automatique. Au démarrage, les conteneurs sont réconciliés
avant la reprise des effacements.

## Console et manuel

La fiche de fonction ajoute une facette Stockage, distincte de l’édition des
quotas dans Configuration : allocations, dernières mesures, état, baux, suivi
et Actualiser. Vider le cache demande une confirmation dans le flux nommant
la fonction et la conservation des données ; aucune ressaisie du nom.

La navigation ajoute Archives de fonctions. Liste de cinq éléments, filtre
conservées/purgées/toutes, détail `/console/archives/{UUID}` indépendant des
parents supprimés. Noms et UUID des parents restent visibles, sans liens vers
des fiches inaccessibles. La purge demande le nom exact dans une confirmation
dans le flux, avec portée volumes/code/configuration et caractère définitif.
Validation visible mais désactivée jusqu’à concordance ; instruction associée
au champ, sans faux message d’erreur avant envoi.

Le suivi utilise `?operation=UUID` avant POST, comme la publication. Reload ne
fait que lire. Introuvable, abandon, attente et terminaison sont distingués.
Une réponse incertaine demande une consultation ; aucune mutation sur lecture
obsolète/en erreur. Nouvelle action explicite = nouvel UUID après relecture.
Aucun code, secret ou résultat dans localStorage/sessionStorage.

Page/filtre/Actualiser retirent les anciens succès et conservent les diagnostics
en attente. Pagination basée sur total, page vide recalée. Focus sur Actualiser
ou titre après changement de page/disparition de carte. Noms/UUID complets avec
retour à la ligne, clavier et mobile 390 px. Le manuel explique suppression,
allocation conservée, purge, cache et réponse incertaine.

## Preuves attendues

SPARK DEV uniquement, vrais HTTPS/SSO/jetons, Docker, FUSE et code original de
qualification. Backup natif avant migration, recoupement anciennes lignes et
archives. Rapports invalidés avant prérequis, UUID propres recensés ; aucun
effacement global d’archives historiques, aucun mock/skip.

API : CRUD/scopes/CSRF ; schémas stricts ; versions absentes/périmées et mauvais
noms ; garde/drainage/admissions ; révocation avant décision ; cache effacé avec
données/code conservés ; cache absent/désactivé ; réponse perdue puis même UUID
après reconstruction ; conflits UUID/type/cible ; parents supprimés et noms
réutilisés ; purge code/config/secrets/volumes et budgets ; fonction voisine
préservée ; 202 et pannes réelles agent/artefacts ; reprises avant/après commit
et interruption pendant nettoyage, réservations conservées et aucun second effet.

UI : accueil, créations/publication réelles, vrais fichiers, navigation,
confirmations annulées/validées, suivi rechargé, filtre/pagination recoupés à
l’API, erreurs réseau/session/version, attentes, focus/noms longs desktop/mobile.
Concordance manuel source/rendu et captures inspectées. Régressions sérielles :
mutations stockage, publication, invocations et console complète ; les preuves
de l’agent ne remplacent pas celles des parcours publics.
