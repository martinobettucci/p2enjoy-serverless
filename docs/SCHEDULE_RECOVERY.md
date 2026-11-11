# Reprise réelle des tirs planifiés

Preuves de [SLS-078](BACKLOG.md#sls-078), selon le contrat
[SCHEDULES](SCHEDULES.md#réalisation-du-moteur-et-migration-009). Décisions
opératoires du10 novembre2026, avant le code du pilote. Aucun changement du
moteur, de son horloge, de ses dépendances ou de ses réponses.

## Périmètre et frontières

Le contrôle DEV est le seul processus applicatif arrêté. Une fonction originale,
créée/publiée/promue par HTTPS dans un namespace `scheduled-functions-<UUID court>`,
porte `*/5 * * * *`. Installation au repos avant armement : cette seule fonction
vivante, aucun upload en cours, appel actif, instance, bail ou réservation.
Le runtime de référence, les fichiers officiels et les autres archives sont
conservés. Un backup SQLite natif privé est créé avant la première faute.

Le pilote reconnaît ces frontières par la vraie base, jamais par un délai seul :

- **Avant réclamation** : processus suspendu avant la frontière UTC visée,
  curseur antérieur, aucun tir ni invocation de cette fenêtre. Après SIGKILL,
  relire ces mêmes absences avant toute reprise ; ne pas revendiquer une
  interruption au milieu du COMMIT.
- **Réclamation acquise** : curseur à la frontière, tir exact `claimed`,
  `invocation_id=NULL`, aucune invocation liée. Arrêt à un syscall natif entre
  commit de réclamation et réception ; après mort, les mêmes identifiants et
  états doivent être récupérables. Reprise : `failed/control_interrupted`,
  jamais de nouvelle invocation pour ce tir.
- **Invocation liée** : curseur à la frontière, tir `dispatched` et invocation
  exacte persistés ensemble, avant démarrage du handler. Reprise : invocation
  interrompue et tir réconcilié terminal, sans nouvel envoi.

Les deux dernières frontières sont observées par `NativeObserver` et une
connexion SQLite RO persistante `ControlObserver`, sans transaction retenue.
Les métadonnées des syscalls de fichiers suffisent à choisir des arrêts
candidats ; le snapshot SQL exact décide si la frontière est acquise. Aucun
registre, tampon, retour système, résultat SQL ou code applicatif n'est remplacé.
Motif : le chemin claim→receive est synchrone et possède deux commits distincts ;
un endpoint artificiel n'éprouverait pas cette fenêtre réelle.

## Garde et restitution

Avant suspension, créer une garde systemd indépendante, dossier root0700 et
identité figée : SPARK, UUID fonction/namespace, CID/image du contrôle,
PID/naissance/cgroup, référence, empreintes des fichiers officiels et programmes
d'arrêt/restitution. Nom : `serverless-restore-schedule-<UUID>`.

Les programmes d'arrêt/restitution déjà utilisés pour les décisions de versions
sont extraits comme chaînes littérales par AST ; seul leur préfixe de dossier
est adapté. Aucun import opérationnel du pilote historique. Leurs verrous de
mutation, pidfd, reçus atomiques, attente de fin du client Docker et refus d'une
issue d'arrêt inconnue sont conservés. Le programme de restitution vérifie les
identités avant de démarrer le même CID et attend sa santé ainsi que celle de
la référence ; il ne restaure ni ne réécrit la base.

Pour le prérequis de perte d'observateur sans faute : garde12s.
Pour un arrêt court : garde80s, observation native bornée45s, commande de coupe
attendue8s. Pour l'arrêt couvrant trois frontières : garde680s et attente
bornée du client jusqu'à la troisième frontière passée ; état arrêté constaté
durant l'attente. La restitution explicite attend la fin de l'observateur et
désarme timer/service. Une perte réelle de l'observateur avant faute éprouve
d'abord la restitution indépendante. En cas d'échec, conserver l'état inconnu
et le reçu, puis résoudre avant toute autre faute.

## Campagne séquentielle

1. Garde sans arrêt du contrôle : observateur suspendu, SIGKILL de l'observateur,
   restitution indépendante et identité/démarrage du contrôle conservés.
2. Arrêt avant réclamation couvrant trois frontières réelles : contrôle arrêté
   à chacune ; reprise avec exactement un `skipped_downtime` par fenêtre, sans
   invocation ; frontière suivante réellement exécutée.
3. Arrêt après réclamation durable : absence d'invocation avant/après mort,
   état terminal après reprise, puis prochain tir normal avec le même code.
4. Arrêt après lien durable : invocation interrompue et tir réconcilié,
   aucune substitution/reprise du handler, puis prochain tir normal.
5. Purge par les API publiques, recoupement natif des tirs/invocations, générations,
   artefacts et ressources ; toutes les gardes/helpers terminés. Sources et
   image identiques avant/après, nouveaux démarrages attendus du seul contrôle.

Les états attendus après coupure ne sont pas des tests ignorés. Les branches
propres du pilote ne sont qualifiées que si réellement provoquées. Cette
campagne ne clôture pas les critères de saturation, recouvrement, exclusif,
rétention et régression complète de SLS-078.


## Résultats réels du10 novembre2026

La [preuve DEV](evidence/schedule-recovery-dev-2026-11-10.json) passe cinq groupes
sur310 sources figées, client e2ced96 et même image b9ad872a. La garde indépendante
restitue la santé après SIGKILL réel de l'observateur, sans redémarrer le contrôle.
Les trois coupes du contrôle sont confirmées par waitpid et Docker137 ; mêmes
CID/image, nouveaux démarrages attendus. La référence et les fichiers officiels
restent identiques.

- Avant réclamation à17:40 UTC : curseur17:35, aucun tir ni invocation avant et
  après mort. Le contrôle reste arrêté aux frontières17:40,17:45 et17:50 ; après
  reprise, trois skipped_downtime sans invocation. Le handler de17:55 réussit ;
  les trois fenêtres restent ignorées après ce prochain réveil.
- Réclamation acquise à18:00 : tir claimed et curseur persistés, aucun lien ni
  invocation avant/après mort. À la reprise : failed/control_interrupted ; le
  handler de18:05 réussit, aucun envoi tardif du tir réclamé.
- Lien acquis à18:10 : tir dispatched et invocation receiving, sans date de fin
  ni démarrage du handler. Après mort, mêmes UUID/états ; à la reprise, invocation
  interrupted/control_interrupted et tir failed. Le handler de18:15 réussit ;
  une seule invocation demeure pour le créneau interrompu, aucun rejeu.

Les trois handlers réussis et l'unique invocation interrompue avant handler sont
recoupés dans la base native. La fonction est purgée par HTTPS ; code, volumes,
conteneurs, réseaux, canaux et réservations sont absents. Les quatre sauvegardes
SQLite restent intègres et inchangées depuis leur création ; les quatre
helpers/timers/services sont
terminés. Les5982 artefacts antérieurs et34 fichiers backend sont conservés.

Aucun build produit, changement d'interface/manuel ni nouvelle capture. Les
checkpoints précédents ne sont pas ajoutés à ce total ni prétendus rejoués.
Les autres branches de secours du banc ne sont pas qualifiées par ce passage.
Recouvrement, CPU, stockage exclusif/file/deadline/extinction sont ensuite
qualifiés dans [SCHEDULE_ADMISSION](SCHEDULE_ADMISSION.md#résultats-qualifiés).
RAM et changement de version avant admission sont qualifiés ensuite dans
[SCHEDULE_MEMORY_VERSION](SCHEDULE_MEMORY_VERSION.md#résultats-qualifiés).
Files pleines, commande de stockage et maximum/réutilisation sont ensuite
qualifiés dans [SCHEDULE_QUEUES](SCHEDULE_QUEUES.md),
[SCHEDULE_UNAVAILABLE](SCHEDULE_UNAVAILABLE.md) et [SCHEDULE_INSTANCE_REUSE](SCHEDULE_INSTANCE_REUSE.md).
Plafond global (SLS-099), rétention, adaptateur.7 et régression restent
ouverts : SLS-078[~].

Le [complément de console](evidence/schedule-console-dev-2026-11-10.json) qualifie
les états vides/erreur, nom63, pagination et reprise401→200 sur la nouvelle image
c59b8616. Les preuves de ce document conservent leur image historique ; elles
ne sont pas présentées comme rejouées par ce complément.
