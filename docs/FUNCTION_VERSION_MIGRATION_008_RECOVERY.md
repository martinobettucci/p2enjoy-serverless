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

Le défaut est reproduit sur19cfe884 : un alias actif sans octets déclarés est
migré, puis le démarrage isolé échoue plus tard sur son socket absent. Les gardes
sont ajoutées au début du script008, dans sa transaction existante, avant les
ALTER/INSERT. Une table temporaire à CHECK nommés et le calculateur déjà enregistré
sont utilisés ; aucun nouveau format ni migration009 n'est introduit. Une migration suivante seule ne peut annuler un
commit008 déjà réalisé. Le précédent007 suit cette même correction de première
transition. Les installations déjà marquées008 sautent le script et conservent
leurs données ; les preuves distinguent l'ancienne et la nouvelle image.

## Verrou et interruption native

Une vraie transaction BEGIN IMMEDIATE ouverte sur une autre copie doit faire
échouer le démarrage au délai SQLite, sans changement logique. Après libération,
une nouvelle tentative explicite doit appliquer008 normalement.

Pour l'interruption avant commit, un wrapper natif PID1 crée un enfant unique
puis attend sa terminaison. Cet enfant s'arrête réellement par SIGSTOP avant
d'exécuter le véritable uvicorn de l'image. Le traceur identifie ce seul enfant
depuis le PID initial Docker, sa parenté, sa naissance et son cgroup ; le PID1
superviseur n'est pas supposé être l'écrivain SQLite. Un traceur lit les métadonnées du premier
pwrite64 de sa WAL privée : FD/inode exact, en-tête de frame24 octets, numéro de
page positif et taille de commit nulle. Cette frontière précède le marqueur de
commit WAL ; l'instruction SQL COMMIT peut déjà être en cours. Le thread écrivain
doit être unique dans cette phase. Il laisse ce syscall s'exécuter, constate
sa sortie réelle, puis interrompt ce seul conteneur par SIGKILL avant la suite.
Il ne lit pas les pages métier, ne modifie ni registres, buffers ni résultats.
Le statut de mort natif et l'ExitCode137 Docker sont recoupés. La base doit
rester exactement007, puis une relance explicite du même conteneur doit appliquer
008 sur la même copie. Aucun callback de progression SQLite n'est injecté.

Une garde indépendante est armée avant attachement et ne peut arrêter/retirer
que le conteneur privé exact, identifié par son nom, ID, image et montage.
Une perte du traceur ne laisse pas de processus suspendu indéfiniment. Les
scénarios de perte propre de cette garde restent distincts du nominal.

Le module natif prend en charge le conteneur depuis son wrapper arrêté jusqu'à
sa suppression confirmée après relance. Il garde le timer armé pendant le retour
à007, le redémarrage du même ID et la vérification008. Sa restitution normale
retire le seul conteneur privé sous verrou, inscrit un reçu terminal puis désarme.
Une garde déjà déclenchée relit ce reçu après acquisition du même verrou et ne
signale plus le parent. Sinon elle vérifie ID/image/labels/bind avant de joindre
le traceur exact par pidfd/naissance/empreinte d'arguments, puis retire cette
copie. Une disparition native déjà confirmée reste distincte d'une suppression.
Le contrôle servi et la référence ne sont jamais des cibles admissibles.

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

## Checkpoint de refus et contrôles positifs

Le [checkpoint](evidence/function-version-migration008-checkpoint-dev-2026-11-09.json)
passe neuf groupes, sans échec ni skip, sur275 sources figées : six refus,
témoin007 réel, verrou/reprise et contraintes. Les quatorze refus SQL et trois
contrôles internes du dernier groupe ne sont pas ajoutés au total neuf.
Le témoin conserve les anciennes colonnes des seize tables,863 groupes dont219
groupes d'alias,261 tombstones inconnus et141 alias supprimés au cache connu.
Les backfills de2882 publications et4418 invocations sont recoupés, ainsi que
les cibles, premiers hash/dates, états et révisions canoniques. Cet historique
ne contient aucun premier hash inconnu suivi d'un hash connu : cette variante
positive reste à éprouver sur un historique réel approprié.

La candidate def45648f9e7 ne diffère du contrôle servi19cfe884 que par le script008,
parmi31 fichiers backend recoupés ; le web compilé est identique. Les images,
ID, démarrages, environnements, fichiers officiels et compteurs actifs du contrôle
et de la référence restent identiques. La sauvegarde originale est inchangée,
les conteneurs/copies sont retirés. La reproduction rouge et le premier replay
de six refus sont séparés, sans gonfler le total.

Commandes depuis la racine synchronisée, avec SSH vers le seul SPARK DEV :

```sh
python3 -B e2e/function-version-migration008-build.py
python3 -B e2e/function-version-migration008-run.py rejections-and-controls sha256:def45648f9e74490a18c5d05f79681d838fbd10fdb519bc8942f9fffe4decbe4
```

La seconde commande rejoue l'image conservée de ce checkpoint ; après une autre
construction, passer l'empreinte retournée par son build. Les pilotes refusent
d'écraser leurs rapports : conserver l'essai précédent local et distant avant
relance. Le rapport natif est control/function-version-migration008.json ; le
checkpoint et le build sont dans .local/e2e. Les bases privées ne sont pas publiées.

La candidate n'est pas servie. L'interruption WAL, ses reprises et sa garde ne
sont pas encore implémentées dans ce banc. Elles précèdent la bascule DEV, les
régressions publiques et la clôture de ce complément. Les purges engagées et
autres critères de SLS-074 restent ouverts. Les résultats ajoutés ici sont
postérieurs au gel275 et ne modifient aucun code exécutable qualifié.
