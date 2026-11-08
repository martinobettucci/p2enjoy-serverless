# Gestion du stockage et des archives

Contrat SLS-065, décidé avant implémentation. Les routes, les écrans et leur
manuel sont déployés sur le SPARK DEV avec le protocole agent de
[SLS-064](STORAGE_DISCARD.md). Les neuf groupes API, neuf parcours navigateur
et huit groupes du manuel passent en qualification ciblée. La qualification
complète reste ouverte : pannes et reprises du contrôle public et régressions
élargies. Le [checkpoint](evidence/storage-console-checkpoint-dev-2026-11-07.json)
inclut aussi onze groupes de gestion et le recoupement physique des nettoyages.

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

Une seule résolution par UUID peut s’exécuter à la fois, y compris entre
maintenance des opérations et reprise du moteur. Les appels concurrents
constatent l’attente ; ils ne réécrivent pas la phase d’un reçu terminé.
Un UUID déjà pris par une autre garde est refusé avant d’en prendre la
responsabilité, pour ne jamais abandonner l’opération d’un autre propriétaire.

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
physique. Tant qu’une garde de purge existe pour la fonction, le nettoyage
général des révisions et candidats lui laisse l’effacement de ses artefacts.
Il ne peut ni retirer ces fichiers ni libérer leurs compteurs, y compris au
démarrage : cela contournerait la relecture de l’absence/version du stockage.
Une garde abandonnée ou terminée libère le nettoyage ordinaire. Le
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

La preuve de validation encore vivante emploie un module original dont l’import
attend réellement soixante secondes et écrit un marqueur dans son `/tmp`.
Le délai produit de quinze secondes reste inchangé. Le conteneur est rattaché
au candidat par le montage `/code`, ses labels d’installation et son marqueur.
Une garde systemd indépendante est armée avant de retirer temporairement les
permissions du seul socket Docker rootless de ce SPARK. Le contrôle doit subir
un vrai refus EACCES ; root conserve l’accès opérateur à ce même daemon.

DELETE puis purge interviennent pendant l’import. La preuve exige ensuite
l’échec réel de l’upload avec nettoyage non confirmé, une purge encore en attente,
les fichiers et compteurs retenus. Après restauration exacte du socket, le
produit doit retirer le validateur et son canal, effacer les seuls artefacts de
la fonction, vider les diagnostics tardifs et terminer le même reçu. Le banc
ne retire pas lui-même le conteneur avant ces assertions. La restauration du
socket après perte du helper est aussi exercée réellement. La fenêtre exige
une cellule au repos, sans fonction étrangère active ; aucune opération sur
la FORGE ni arrêt du daemon Docker.

La preuve des décisions utilise deux sessions administrateur issues de connexions
SSO distinctes. Pendant une préparation de purge retenue par l’agent suspendu,
la session demandeuse est fermée par `/auth/logout`. La session de contrôle
observe l’abandon, l’absence de reçu d’effacement agent et la conservation des
fichiers, de la configuration et de la version ; elle assure aussi le nettoyage.
Une copie du même cookie ne constitue pas une seconde session.

Après une décision réelle retenue par une erreur physique de cache, le banc
peut retirer les permissions du socket agent ou acquérir un vrai writer SQLite
du contrôle avec `BEGIN IMMEDIATE`, sans changer aucune ligne. Le socket et
son montage doivent être ceux des fichiers officiels de cellule. Le writer est
ouvert, lu, rollbacké et fermé sous l’identité propriétaire de la base, avec
signaux différés pendant ouverture/fermeture. Une garde indépendante précède
chaque perturbation et contrôle l’identité de la ressource restaurée.

La panne de transport exige le diagnostic `storage_transport` sur le reçu commis.
Le worker agent reste libre de finir son effacement : la preuve ne confond pas
l’absence de communication avec un arrêt du worker. La contention exige un reçu
agent terminé et le reçu public encore en attente, puis le diagnostic corrélé
`control_database_unavailable` dans le journal réel. Après restauration, le même
UUID/version doit terminer ; un rejeu après reconstruction conserve le cache.
La garde du writer est exercée par SIGKILL de son helper. Une campagne distincte
laisse la garde de redémarrage relancer effectivement le contrôle arrêté, avec
preuve de son état antérieur et de son redémarrage. Toutes les fonctions de ces
campagnes sont créées, publiées, invoquées, archivées et purgées par les API.
Le secours de redémarrage attend un verrou natif conservé par le helper et son
processus d’arrêt Docker, lui-même borné indépendamment du helper. Il ne peut
ainsi redémarrer avant un arrêt tardif. Le fichier de garde est privé, rattaché
à son unité et retiré après restauration ; l’observation attend ensuite le
retour réel de l’API avant de relire le reçu.

Le cas `storage_absent` est produit par une véritable version historique puis
migré vers le contrôle actuel, dans une installation temporaire dont les données
sont retirées après preuve de la contradiction attendue. Le
[contrat de qualification des archives anciennes](STORAGE_LEGACY_PROOF.md)
définit les versions, la fenêtre DEV, la garde et la conservation de l’installation
habituelle. Aucun enregistrement absent n’est fabriqué par SQL.

### Suite commune et pagination autonome

La clôture SLS-065 ajoute deux sélections explicites à `execution-suite.py` :
`--scope storage-console-focused` rejoue les sept campagnes publiques et
historiques de stockage ; `--scope storage-console` les complète par l’union
des régressions publication/console et stockage agent, sans doublon de campagne.
La sélection ciblée n’est pas une preuve de campagne transversale complète.

Le runner reçoit une ligne JSON `username`/`password` sur stdin privée, sans
écho sur un terminal, sans valeur dans les arguments, l’environnement, les
rapports ou fichiers. Un client SSO de qualification ouvre l’accueil puis la
connexion normale dans deux contextes neufs : session de contrôle et session
de purge distinctes. Seuls les cookies de plateforme nécessaires sont conservés
dans les fichiers privés autorisés ; les erreurs de navigateur sont expurgées.
La paire est créée au début de la suite, puis recréée immédiatement avant la
campagne de décision : une session inutilisée pendant les longues régressions
peut ne plus être renouvelable au SSO, même si son cookie reste valide.
Ces deux préparations ont des rapports frais distincts et ne comptent aucun
groupe fonctionnel. Une connexion refusée arrête la suite ; aucun rejeu implicite
du scénario ni allongement du délai de session ne compense ce refus.
La session de purge est consommée par la vraie déconnexion de cette campagne.
Les mêmes identifiants sont transmis en mémoire à la campagne historique complète.

Le build historique est un prérequis contrôlé par fraîcheur et empreintes, sans
groupe artificiellement compté. Son rapport est invalidé avant toute opération.
Chaque campagne est liée aux sources locales/distantes, aux dépendances du
client E2E, à l’image et à son rapport frais avant/après. La suite s’arrête sur
échec, nettoyage incomplet ou restauration historique non confirmée.

La campagne navigateur prépare onze fonctions brouillon supplémentaires depuis
les parcours UI ordinaires et les archive avant de tester la pagination. Ses
deux premières pages conservées doivent montrer dix de ces UUID, sans doublon,
y compris après la vraie panne réseau. Le rapport recense toutes les fonctions
du namespace, même si une création ou une suppression échoue. Le nettoyage
purge ses archives et parents par API, sans retirer les archives des autres
campagnes. Ce groupe de préparation porte la campagne UI à dix groupes.

Le recoupement final utilise `campaigns` lorsqu’il existe, sinon le namespace et
la liste exhaustive de fonctions du rapport. Il associe cinq campagnes publiques
à six namespaces et vingt-quatre fonctions, puis exige le nettoyage physique et
les réservations libérées. Les deux campagnes historiques sont vérifiées par
leur preuve de restauration, sans envoyer leurs UUID temporaires au collecteur
de l’installation habituelle. Le rapport historique complet conserve le reçu
volontairement bloqué comme un résultat de panne, sans le présenter comme une
purge métier réussie. Les captures fraîches de stockage, publication, gestion
et manuel restent à inspecter avant clôture.
