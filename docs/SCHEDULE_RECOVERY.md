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
Rétention et régression restent ouvertes : SLS-078[~]. Plafond099 et
adaptateur.7 sont qualifiés séparément.

Le [complément de console](evidence/schedule-console-dev-2026-11-10.json) qualifie
les états vides/erreur, nom63, pagination et reprise401→200 sur la nouvelle image
c59b8616. Les preuves de ce document conservent leur image historique ; elles
ne sont pas présentées comme rejouées par ce complément.

## Exécution indépendante du terminal

Décision du 11 novembre 2026 avant le lanceur du rejeu courant : cette campagne
d'environ quarante minutes s'exécute dans une tâche systemd utilisateur locale
transitoire `serverless-schedule-recovery-proof-UUID`. Le terminal qui la lance
peut terminer ; seule l'observation réelle du processus ou de son résultat
systemd décide si le travail continue ou est terminé. Aucun service applicatif
local, dépendance de remplacement ou nouvelle récurrence n'est installé.

Préparer les deux sessions privées par le parcours SSO existant avant lancement,
puis exécuter le même `node e2e/schedule-recovery.mjs` avec ses fichiers de session
habituels. Mot de passe en mémoire seulement, jamais argument, environnement,
fichier, journal ni reçu. Les sorties et checkpoints sont privés. Sources et
images sont figées et recoupées avant/après ; les originaux et captures de
vieillissement restent conservés.

Type=oneshot, TimeoutStartSec=3700 s et RemainAfterExit=yes ; client borné à
3300 s, gardes distantes 12/80/680 s inchangées. Conserver PID/naissance/cgroup
vivants, puis MainPID=0, Result, ExecMainCode et ExecMainStatus terminaux avec le
SHA du checkpoint avant d'arrêter cette seule unité. Un checkpoint completed
ne suffit pas si le worker échoue. Une perte reste un échec conservé, sans
relance automatique ; recouper d'abord les restaurations réelles. Ce lanceur
ne change aucun scénario ni aucun critère et n'ajoute pas de groupe E2E.

### Observation du lancement et résultat courant

Le premier lancement du 11 novembre a bien créé son worker ; le client de
lancement a ensuite expiré après 20 s parce que systemd-run attendait la fin
du oneshot. L'unité, son MainPID 510223/naissance 63038117 et son cgroup sont
recoupés vivants après la fin de ce client ; aucun rejeu n'est lancé. Décision :
le prochain lancement doit employer `systemd-run --no-block` pour rendre
l'acceptation immédiatement, puis observer l'unité. Le code figé du worker
courant reste inchangé jusqu'à son résultat terminal. La récupération de
l'observation est conservée séparément de l'échec du client de lancement.

Le [rejeu courant](evidence/schedule-recovery-regression-dev-2026-11-11.json)
termine ses cinq groupes sur les 351 sources du commit 7ed2abe, identiques
avant/après, et les mêmes images applicatives. Trois coupures Docker 137,
trois fenêtres manquées sans invocation, reprises claimed/linked sans rejeu
et trois tirs suivants réussis. Quatre handlers réussissent au total, dont
un témoin initial ; l'invocation liée est interrompue avant handler_started.
Les quatre gardes sont jointes et la fonction est purgée physiquement.

Le même worker 510223 termine avec Result=success, ExecMainCode=1 et
ExecMainStatus=0 ; son résultat et le SHA du checkpoint sont conservés avant
l'arrêt de l'unité. Le timeout du client de lancement reste un échec distinct,
sans relance du worker ; le nominal du futur lancement --no-block n'est pas
qualifié par cette campagne. Les captures canoniques sont inchangées,
les deux services sont sains, actifs à zéro, 5 982 artefacts et aucune garde.
Les interruptions de backup/copie sont qualifiées ensuite dans
[leur preuve distincte](evidence/schedule-retention-copy-losses-dev-2026-11-11.json).
Les cinq groupes ci-dessus conservent leur époque7ed2abe, avant les changements
du helper/client bca96ab. L'âge réel et la campagne complète restent ouverts ;
aucune modification produit ou UI dans cette étape.

### Lancement courant avec --no-block

Le lancement du11novembre à19:50UTC emploie maintenant --no-block et son client
termine0. Le même worker3016607/naissance64482164 est observé vivant après la
sortie du lanceur, dans l'unité transitoire serverless-schedule-recovery-proof-ee45e27fdc8344c1b5e6c22a6959291f.
Le [rejeu final](evidence/schedule-recovery-detach-regression-dev-2026-11-11.json)
passe cinq groupes au gel355sources ef98a9f, identique au bounded et aux quinze
consommateurs courants. Trois coupures Docker137 : échéances19:55/20:00/20:05UTC
manquées sans invocation, tir claimed20:15 sans invocation, tir linked20:25
interrompu avant handler. Les trois tirs suivants20:10/20:20/20:30 réussissent,
sans rejeu. Trois handlers réussis au total, un appel lié interrompu avant
démarrage, quatre gardes jointes et une fonction purgée physiquement.

Le même worker3016607 termine réellement avec MainPID0, Result=success,
ExecMainCode=1 et ExecMainStatus=0. Le reçu et le SHA du checkpoint sont conservés
avant arrêt de la seule unité. Checkpoint privé :
.local/e2e/schedule-recovery-current-ee45e27fdc8344c1b5e6c22a6959291f/checkpoint.json.
Brut682440octets/gzip85987 ; images,355sources et captures canoniques inchangées.
Deux services sains, actifs/baux nuls,5982artefacts et aucune garde. Le nominal
numérique courant est qualifié séparément ci-dessous ; âge et campagne complète
restent requis.

## Nominal numérique de la classe courante qualifié

La [preuve6de2a86](evidence/invocation-source-retention-detach-volume-dev-2026-11-11.json) passe trois groupes
sur355sources/images identiques au bounded et à l'historique final.10001 réponses
HTTP et un cron réels donnent10002 observations terminales,5001 par fonction.
Le tir non clos garde sa source hors comptage :10001 lignes après retrait du
plus ancien HTTP. Après clôture normale, le deuxième plus ancien HTTP disparaît :
10000 lignes et source strictement identique, désormais comptée. Les trois vecteurs
sont recoupés exactement ; observation12,410435700s sous25s.

Deux purges publiques et restitution nominale jointe ; même worker réel terminal0,
reçu conservé puis unité arrêtée. Collectes natives/captures fraîches après cette
finalisation, liées au SHA terminal :2services sains, actifs/baux nuls,5982artefacts
et aucune garde. Captures canoniques inchangées. Brut83048624octets/gzip4228693 ;
ancienne preuve348 préservée. La borne native partagée et son nominal sont
qualifiés ; âge18novembre et campagne complète restent requis,078.5 non clôturée.

## Diagnostic de la barrière non reçue — SLS-145

Décision du23novembre2026 avant code, après le
[premier échec scellé](evidence/schedules-recovery-gated-first-failed-dev-2026-11-23.json).
L’erreur primaire est l’expiration cliente `native_event_missing_gated`, et
non la finSSH255. Le site natif n’est pas établi. La décision porte sur la
conservation d’observations nouvelles ; aucun correctif de cause n’est déduit
du seul rouge. Les cinq groupes nominaux restent exigés intégralement.

### Périmètre de l’instrumentation

Instrumenter seulement le parcours de reprise et ses quatre gardes. Conserver
la classe partagée `NativeObserver`, `ControlObserver`, les programmes historiques
d’arrêt/restitution et les requêtes/prédicats d’acquisition. Le mode
`terminal-capture` des rétentions garde son chemin non instrumenté. Aucun
registre, tampon, résultat SQL, horloge ou réponse n’est remplacé. Aucun
nouveau service, paquet tiers ou réglage d’infrastructure n’est nécessaire.

Le helper crée dans son dossier de garde root0700 des fichiers diagnostiques
root0600. Un petit état binaire versionné, mappé par la bibliothèque standard
Python, conserve phase et compteurs sans écriture de fichier ni émission
stdout à chaque syscall. Les mises à jour de la page mémoire partagée restent
visibles après SIGKILL du helper sur le même démarragehôte ; aucune garantie de
persistance après redémarrage n’est revendiquée. Cette observation a un coût,
nommé dans la preuve ; elle n’est pas assimilée à une exécution non instrumentée.

Le protocole publie sa version, ses champs/types et ses phases dans un manifeste
figé sousSHA, avec identité helper/contrôle, naissances, namespacePID et boot.
Un compteur de séquence encadre chaque mise à jour ; le lecteur borne ses essais
et annonce un état incomplet si la mort interrompt l’écriture. Il ne reconstruit
pas une valeur partielle. Les diagnostics ne contiennent ni environnement,
secrets, arguments applicatifs, en-têtes, corpsHTTP ni mémoire utilisateur.

Bornes de réalisation : page d’état fixe de4096octets ; manifeste de16Kio au
plus ; derniercheckpointJSON de64Kio au plus ; primaire et incidents de
finalisation de16Kio chacun,16cadres source au plus. Les dépassements sont
nommés avec taille/SHA et observation incomplète, jamais convertis en un état
complet. Le lecteur fait au plus trois essais de séquence espacés au plus
d’1ms, dans la borne globale3s. Une erreur de conservation diagnostique ne
remplace ni la primaire ni ses métadonnées déjà reçues ; elle constitue un
incident séparé et empêche de qualifier une observation manquante.

### Observations conservées

- instants réels d’armement, attenteUTC, début/fin d’attache, début d’acquisition
  et échéance45s ; domaines tempsmur/monotone explicitement séparés ;
- phase avant les appels susceptibles de bloquer : `attach`, `wait`, `info`,
  chacune des trois lectures du checkpoint, `predicate`, `durable`, `emit`,
  `detach`, `restore`, `reader_close` et fin ;
- nombre d’appels/retours de l’API `NativeObserver.wait`, dernier signal réellement
  retourné, métadonnée du dernier syscall observé et nombre de candidats.
  Ces compteurs ne prétendent pas exposer les appels internes vides de waitpid
  ni leur statutbrut, que la classe partagée ne publie pas ;
- durées et compteurs séparés des trois lecturesSQLite et de `durable()` ;
  dernier checkpoint réellement obtenu, sous révision/SHA et capacité bornée,
  distinct du seul fait d’avoir commencé une lecture. Tout dépassement ou
  désaccord de révision reste une observation indisponible explicite ;
- exception primaire enregistrée atomiquement avant le `finally` : type,
  errno applicable, SHA du message et cadres source sans variables ; incidents
  de finalisation conservés séparément, sans les substituer à la primaire.

Une lecture diagnostique dédiée est strictementRO : dossier/identités/SHA
vérifiés, page mémoire et checkpoint recoupés, puis métadonnées bornées de
`/proc` du helper encore identifié (état, syscall, attente noyau, tempsCPU,
identités). Le lecteur ne lit ni environ ni tampon pointé. Il distingue processus
vivant, naissance terminée, permission refusée et fichier absent ; le namespace
et boot épinglés précèdent toute conclusion d’absence.

Le client enregistre l’expiration primaire et la photographieRO avant d’engager
son secours. Cette photographie est bornée à3s, sans retry ; son échec conserve
la primaire au lieu de la remplacer. Les limites45/70/80s restent inchangées,
avec leurs origines distinctes. La commande de secours choisie, l’étatSSH
observé et les instants d’envoi/retour sont retenus ; `independent:true` n’est
jamais présenté comme une preuve du déclencheur timer. Une course non distinguée
par les reçus/journaux reste nommée inconnue. Après réussite aussi, lire les
fichiers diagnostiques figés avant de commencer la garde suivante.

### Diagnostic d’acquisition séparé du nominal

Un mode explicite `--diagnose-claimed` du client peut préparer une fonction
originale par les API réelles, puis éprouver la seule acquisitionclaimed à la
prochaine frontièreUTC. Il utilise le même helper, observateur, SQL, prédicat
et bornes que le nominal. Après barrière réellement acquise, une commande
explicite `release`, autorisée seulement avec l’option native d’observation,
détache et restitue sans envoyer de commande de coupure. Le vrai handler peut
alors poursuivre normalement ; le nettoyage public et physique reste exigé.
Un échec reste conservé avec son vrai retour et sa photographie.

Ce mode produit un rapport distinct identifié acquisitiondiagnostique et compte
zérogroupefonctionnel. Il ne saute aucun groupe du nominal et ne remplace ni
les trois coupures137, ni les trois fenêtres manquées, ni claimed/linked
interrompus, ni leurs tirs normaux. Pas de relance automatique : résultat,
programmes, diagnostics, identités, gardes et purge sont recoupés avant toute
nouvelle expérience. Le nominal cinqgroupes puis25communs,49/543/18 depuisle
début et complément32/276 restent nécessaires à145.4.
