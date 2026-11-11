# Mémoire et changement de version avant admission

Complément de [SLS-078](BACKLOG.md#sls-078), selon
[SCHEDULES](SCHEDULES.md#preuves-e2e-attendues). Décision opératoire du
10 novembre2026 avant code. SPARK DEV sain et au repos, budgets1CPU/8192Mio/
32instances ; aucun changement de produit, d'horloge ou de fichier officiel.

## Campagne réelle

Trois fonctions originales dans un namespace scheduled-functions-<UUID court>,
publiées par HTTPS avec l'adaptateur réel et promues explicitement :

| Fonction | Configuration | Déroulement |
| --- | --- | --- |
| Occupant de mémoire |0,05CPU,128Mio,min1,max1,idle0 ; sans cron | Instance prête avant W, réservation et plafond Docker128Mio |
| Cible mémoire |0,05CPU,8192Mio,min0,max1,idle0,deadline60s ; cron */5 | Froide à W : refused_capacity/schedule_capacity sans invocation. Après libération : tir W+300 running, plafond Docker8192Mio/CPU50m, handler20s puis succeeded |
| Version changée en file |0,05CPU,128Mio,min0,max1,concurrence1,données2Mio exclusives,idle0,deadline60s,file60s | HTTP A running avant W, libéré W+20, compteur1. Tir A queued ; promotion B sans cron pendant l'attente. Invocation rejected/schedule_changed sans handler, tir refused_changed. HTTP admis A termine ; lecture B retrouve compteur1. A promue après W+300, tir W+600 réussi compteur2 |

B est préparée avant W sans promotion ; son hash diffère par retrait du cron,
code du handler et données conservés. Promouvoir B seulement après observation
du lien tir/invocation en file et du HTTP A encore actif. Après W, passer le
minimum de l'occupant à0 par l'API, attendre retrait SQL/Docker/réseau/canal/bail.
Avant W+300 : zéro réservation. Pendant le handler mémoire20s, recouper le vrai
conteneur ; après réussite, promouvoir son hash sans cron. Ensuite seulement,
promouvoir A sur la fonction changée, pour son prochain tir W+600.

## Discriminants et nettoyage

Recouper API et SQL RO : fenêtre, génération, hashes, UUID tir/invocation, état,
erreur, handler_started, dates et instance. Avant le refus RAM : mémoire réservée
+8192 dépasse8192 ; CPU réservé+0,05 reste sous1, instances+1 sous32. Exiger aucun
lien, invocation, instance ou handler pour ce créneau. Pour schedule_changed :
UUID lié, requested_code_hash=A, resolved_code_hashNULL, aucune admission ni effet
métier. Relire les deux refus après les tirs suivants, sans replay.

Le handler de capacité attend20s pour rendre son allocation observable ; ses
journaux ne portent que métadonnées publiques. Le handler de données est celui
déjà qualifié dans scheduled-admission.cjs. Les budgets effectifs sont lus dans
le contrôle et les allocations recoupées dans Docker.

Fin : retirer les crons par promotion, révoquer le jeton, archiver/purger les trois
fonctions et supprimer parents. Recouper code/volumes/conteneurs/réseaux/canaux/
baux absents, compteurs nuls,5982 artefacts antérieurs et34 backends conservés,
services et fichiers officiels identiques. Un échec conserve son rapport,
termine ses appels et nettoie avant toute relance explicite.

Le plafond global d'instances suit séparément la correction de la garde
[SLS-099](BACKLOG.md#sls-099). Rétention et régression complète restent
ouverts ; cette campagne ne clôture pas SLS-078.

## Résultats qualifiés

La [preuve DEV du10 novembre2026](evidence/schedule-memory-version-dev-2026-11-10.json)
passe cinq groupes sur316 sources figées, client510d820 et même image b9ad872a.
Fenêtres19:40/45/50UTC. Avant W,256Mio,0,1CPU et deux instances sont réservés ;
la cible8192Mio ne tient pas en mémoire, alors que CPU et places restent disponibles.
Son tir est refused_capacity/schedule_capacity sans invocation ni instance.

Le tir A en file est observé avant promotion B. Il devient rejected/schedule_changed,
sans admission ni handler, avec tir refused_changed. Le HTTP admis A termine
après la promotion, compteur1 ; la lecture B retrouve compteur1. Minimum et
instances sont retirés, réseaux/canaux/baux absents avant W+300, y compris le canal
du minimum sans invocation. Le prochain tir RAM réussit : conteneur réellement
observé8192Mio/0,05CPU, contexte8192Mio, handler20,006s et seule réservation globale.
Après retour explicite A, son tir W+600 réussit avec compteur2. Aucun rejeu des
deux refus ni tir des planifications retirées.

Collecte indépendante : quatre tirs, cinq invocations dont quatre handlers
réussis (deux planifiés/deux HTTP), une réception rejetée sans handler, trois
purges physiques et compteurs nuls. Les34 backends,5982 artefacts antérieurs,
contrôle/référence (ID/image/démarrage) et fichiers officiels sont identiques.
Aucun build produit, budget officiel, UI/manuel ou capture modifié. Le plafond
global d'instances, rétention, adaptateur.7 et régression complète
restent ouverts ; SLS-099 porte la correction préalable de sa garde. Les autres
refus et la réutilisation sont qualifiés dans [SCHEDULE_QUEUES](SCHEDULE_QUEUES.md),
[SCHEDULE_UNAVAILABLE](SCHEDULE_UNAVAILABLE.md) et [SCHEDULE_INSTANCE_REUSE](SCHEDULE_INSTANCE_REUSE.md).

Le [complément de console](evidence/schedule-console-dev-2026-11-10.json) qualifie
les états vides/erreur, nom63, pagination et reprise401→200 sur la nouvelle image
c59b8616. Les preuves de ce document conservent leur image historique ; elles
ne sont pas présentées comme rejouées par ce complément.
