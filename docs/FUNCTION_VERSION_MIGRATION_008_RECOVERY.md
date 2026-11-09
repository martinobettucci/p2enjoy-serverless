# Refus et interruption de la migration008 — SLS-074

## Source historique et confinement

Le banc utilise une copie SQLite native de la véritable sauvegarde007 créée
avant la première migration008 :
`qualification-history/function-versions-before008-1794211976610764464`.
La fonction d5486e9a-28f9-4b04-9fb8-974230194f48 a de vrais alias A/A/B,
rollback, invocations et données/cache, créés par les API historiques. Le reçu
du checkpoint008 fournit son image et les empreintes de toutes les tables.
La sauvegarde et ses artefacts/backings restent inchangés et ne sont jamais
publiés. Aucun rollback ni arrêt du contrôle servi n'est nécessaire à ces copies.

Chaque scénario emploie une copie privée distincte, un conteneur éphémère de
l'image réelle du contrôle, les deux env_file officiels, réseau none, aucun port,
racine readonly, limites CPU/RAM/PID, et le seul bind de sa copie sous /state.
Il ne monte ni socket Docker, ni agent, ni volume métier vivant. Les fichiers
historiques privés restent en0600 dans un répertoire0700. Le vrai uvicorn est
lancé : un échec postérieur faute de socket n'est jamais pris pour un refus de
migration. La preuve positive de démarrage exploitable reste celle du véritable
upgrade public007→008 ; ce banc qualifie la transaction de migration isolée.

## Invariants et matrice négative

Avant de transformer007, refuser une cible active dont la fonction est supprimée,
dont la révision appartient à une autre fonction, est supprimée, sans hash ou
sans octets conservés. Refuser les références étrangères orphelines. Recalculer
l'identité des codes conservés et vérifier leur cache007, en réutilisant le
calcul canonique et la reconnaissance stricte des purges engagées de007. Un
tombstone purgé légitime ne retrouve pas artificiellement un inventaire ou hash.
Les pointeurs, alias, dates et compteurs ne sont jamais corrigés silencieusement.

Six copies fautées constituent la matrice initiale : fonction supprimée avec
cible, alias actif réaffecté à une autre fonction existante, octets de l'alias
actif ramenés à zéro, inventaire retenu vide, inventaire valide dont le digest
ne correspond plus au cache, et jeton référençant un service inexistant.
Ce sont des altérations réelles des entrées historiques privées ; les dépendances
et les résultats de l'application ne sont pas remplacés.

Chaque refus exige sortie non nulle du vrai démarrage, diagnostic de migration,
absence du marqueur008, de function_versions et des nouvelles colonnes, schéma
et contenu logique strictement identiques à l'entrée fautée. L'intégrité et les
références sont relevées séparément ; le scénario orphelin conserve volontairement
son défaut d'entrée. Le premier test doit d'abord reproduire l'absence de refus
sur l'image19cfe884, avant toute correction. Son échec reste séparé du replay.

## Correction de la première transition

Si le défaut est reproduit, ajouter les gardes au début du script008, dans sa
transaction existante, avant les ALTER/INSERT. Une table temporaire à CHECK
nommés et le calculateur déjà enregistré suffisent ; aucun nouveau format ni
migration009 n'est introduit. Une migration suivante seule ne peut annuler un
commit008 déjà réalisé. Le précédent007 suit cette même correction de première
transition. Les installations déjà marquées008 sautent le script et conservent
leurs données ; les preuves distinguent l'ancienne et la nouvelle image.

## Verrou et interruption native

Une vraie transaction BEGIN IMMEDIATE ouverte sur une autre copie doit faire
échouer le démarrage au délai SQLite, sans changement logique. Après libération,
une nouvelle tentative explicite doit appliquer008 normalement.

Pour l'interruption avant commit, un wrapper natif s'arrête par SIGSTOP puis
exec le véritable uvicorn de l'image. Un traceur lit les métadonnées du premier
pwrite64 de sa WAL privée : FD/inode exact, en-tête de frame24 octets, numéro de
page positif et taille de commit nulle. Il laisse ce syscall s'exécuter, constate
sa sortie réelle, puis interrompt ce seul conteneur par SIGKILL avant la suite.
Il ne lit pas les pages métier, ne modifie ni registres, buffers ni résultats.
Le statut de mort natif et l'ExitCode137 Docker sont recoupés. La base doit
rester exactement007, puis une relance explicite du même conteneur doit appliquer
008 sur la même copie. Aucun callback de progression SQLite n'est injecté.

Une garde indépendante est armée avant attachement et ne peut arrêter/retirer
que le conteneur privé exact, identifié par son nom, ID, image et montage.
Une perte du traceur ne laisse pas de processus suspendu indéfiniment. Les
scénarios de perte propre de cette garde restent distincts du nominal.

## Résultats et régression

Le témoin007 non fauté applique008 par le vrai démarrage avant l'échec attendu
sur son socket absent. Il conserve les anciennes tables, identités, cache,
alias, cible et dates ; les champs historiques sont vérifiés contre les lignes
réelles. Les contraintes nouvelles sont éprouvées dans l'image réelle sur une
copie migrée, sans publier ces données. Ces preuves de composant ne prétendent
pas invoquer les handlers dans les conteneurs isolés.

Après correction et gel des sources : matrice négative, verrou/reprise,
interruption/reprise, contraintes puis régressions liées en série. Construire
et recouper la nouvelle image avant toute bascule du seul contrôle DEV ; sauvegarder
l'état courant et vérifier l'absence d'effets de migration sur la base008 déjà
servie. Les campagnes publiques de versions et CLI doivent passer sur cette image.
Les pannes de publication, purges historiques engagées et la campagne complète
restent nécessaires dans SLS-074. Aucun nouveau parcours UI n'est attendu.
