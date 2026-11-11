# Admission réelle des planifications

Complément de [SLS-078](BACKLOG.md#sls-078) et du
[contrat du moteur](SCHEDULES.md#preuves-e2e-attendues). Décision opératoire du
10 novembre2026, avant code. Le contrôle DEV est sain et au repos ; budgets
effectifs relevés :1 CPU,8192 Mio,32 instances,128 attentes dont16 par fonction.
Les fichiers officiels, images et démarrages restent conservés.

## Campagne et discriminants

Créer par HTTPS cinq fonctions originales dans un namespace
`scheduled-functions-<UUID court>`, publier puis promouvoir normalement leurs
crons `*/5 * * * *`. Tous les objets sont prêts avant la fenêtre W retenue.
Une seule campagne est exécutée ; les appels simultanés ci-dessous sont ses
consommateurs réels, jamais des réponses ou réservations fabriquées.

| Fonction | Configuration et occupation réelles | Preuve attendue |
| --- | --- | --- |
| Handler long |0,125 CPU,128 Mio,deadline360s,idle0,min0,max1 ; handler planifié315s | À W+300, premier appel encore running/handler_started, même instance Docker ; second tir skipped_overlap sans invocation. Premier appel ensuite succeeded, durée du handler supérieure300s |
| Capacité CPU |1 CPU,128 Mio,min0,max1,idle0 ; aucune instance prête | À W et W+300, budget réellement occupé par les autres appels : refused_capacity/schedule_capacity, invocation_idNULL et aucune invocation de ces slots. Après libération, nouveau tir W+600 réussi, aucun retry des refus |
| Exclusif avec admission |0,125 CPU,128 Mio,données2Mio exclusives,concurrence1,deadline45s,file30s,idle10s,min0,max1 | HTTP Read déjà running avant W, bail réel et écriture compteur1 ; il attend jusqu'à W+10. Tir planifié lié queued sans handler, puis admis après HTTP, compteur2 sur le même volume, succeeded |
| Exclusif avec expiration | Même allocation, file2s,idle10s ; HTTP actif jusqu'à W+20 | Tir lié à une vraie invocation rejetée queue_timeout, handler non démarré, firing refused_capacity avec UUID. HTTP encore actif au refus ; lecture réelle ultérieure retrouve compteur1. Aucun rejeu après libération |
| Deadline |0,125 CPU,128 Mio,timeout3s,idle0,min0,max1 ; handler planifié attend5s | Invocation failed/invocation_timeout, handler démarré et conteneur recyclé ; aucun marqueur de fin. Appel HTTP suivant immédiat réellement réussi |

Le handler exclusif attend une date de libération fournie dans le payload HTTP,
sur l'horloge normale du runtime. Motif : maintenir une occupation réelle de part
et d'autre de W sans dépendre de la durée du démarrage à froid. L'horloge, le
code du contrôle, SQLite et ses dépendances ne sont jamais remplacés.

Avant W : observer les deux HTTP running/handler_started et leurs instances/baux,
la cible CPU sans instance, allocations Docker et budget consommé. À W, observer
les deux invocations planifiées queued, puis leurs issues distinctes. Un état
refused_capacity seul ne prouve pas une absence d'invocation : le lien et l'erreur
distinguent schedule_capacity de queue_timeout.

Après les issues du premier créneau, retirer les crons des deux fonctions
exclusives et de deadline par publication/promotion d'un hash sans schedule.
Après W+300, observer le handler long toujours actif, son tir skipped_overlap et
le second refus CPU. Attendre sa fin, puis retirer sa planification de même façon.
Ces mutations conservent les configurations et les données. À W+600, seule la
cible CPU demeure planifiée ; elle réussit puis sa planification est retirée.
Relire les refus et le recouvrement après ce dernier tir pour exclure un rejeu.

## Observations et nettoyage

Le client rapproche les API HTTPS et un lecteur natif RO : UUID fonction,
génération, tir, invocation, hash, nominal, états, dates, handler_started,
instance/conteneur, réservations et baux. Les journaux originaux ne contiennent
que marqueurs, compteurs et métadonnées publiques. Aucun jeton n'est conservé
dans le rapport. Mesurer l'extinction normale après idle pour les deux fonctions
exclusives, et l'absence de ressources du handler expiré avant son appel sain.
Le délai idle de10s laisse relever une instance ready et last_used_at après
terminaison malgré le coût des statistiques Docker de l'API. Ensuite, un observateur SQLite RO persistant sur le SPARK relève à50ms
les intervalles horodatés de chaque lecture jusqu'à disparition : aucune disparition
plus de0,1s avant last_used_at+10s, disparition au plus10s après cette borne.
Conserver premier/dernier relevé positif et première absence ; une simple absence
finale ne qualifie pas l'extinction temporelle. Les bornes s'appliquent aux
lectures natives, sans déduire l'instant SQL d'un retour réseau client ; le
processus de lecture est borné et rejoint avant la suite.

Fin : attendre les appels réellement terminaux, révoquer les jetons, archiver et
purger les cinq fonctions par leurs API, supprimer les parents. Recouper code,
volumes, conteneurs, réseaux, canaux, reçus et compteurs nuls ;5982 artefacts
antérieurs conservés,34 backends et sources/images/configuration inchangés.
Un échec conserve son rapport, termine ses appels puis nettoie avant toute relance
explicite. Aucun retry automatique de la campagne ou des invocations.

Cette tranche ne qualifie pas les précontrôles planifiés RAM/instances, les autres
refus avant admission, la rétention, les états UI complémentaires ni la régression
complète ; SLS-078 reste[~] jusqu'à leurs preuves.


## Premier essai et réglage de la preuve de deadline

Le premier essai au client93ec58b passe le groupe de publications/occupants puis
s'arrête sur la deadline0,5s : failed/invocation_timeout avec handler_startedNULL
et journal vide. Le démarrage n'est donc pas observé ; le cas après démarrage
exigé ne peut pas être déclaré prouvé. Le contrôle reste conforme à sa deadline,
qui inclut le lancement de l'enfant d'invocation.

Après fin réelle du handler315s, les cinq fonctions sont purgées physiquement,
sans erreur de nettoyage ;313 sources et image sont identiques avant/après.
Le rapport UUIDc9b925d3 et son relevé diagnostic restent conservés, hors total du
replay. Le délai d'essai est porté à3s pour laisser observer le vrai démarrage
sous0,125CPU ; le handler attend toujours5s et les assertions après démarrage
restent obligatoires. Aucun produit ni configuration officielle modifié.

La relance b00d6f3 est arrêtée avant sa première fenêtre après lecture de009 :
une promotion sans cron conserve une génération courante avec schedules vide.
Exiger zéro génération courante était une erreur du banc. La preuve correcte
exige cinq générations courantes au hash sans schedule promu, chacune avec
une liste vide, et zéro déclaration exposée par l'API. Le client est arrêté
par PID/naissance ; cinq fonctions purgées publiquement, aucun tir ni invocation,
compteurs nuls et physique recoupé. Rapport cff86db6 et reçu de nettoyage distincts,
zéro groupe ajouté. La campagne entière est à rejouer après correction de cette
assertion ; le schéma et le moteur ne changent pas.

## Résultats qualifiés

La [preuve DEV du10 novembre2026](evidence/schedule-admission-dev-2026-11-10.json)
passe cinq groupes sur313 sources figées, client aaf4103 et même image b9ad872a.
Fenêtres19:00,19:05 et19:10 UTC. Les deux HTTP sont observés avant W avec leurs
conteneurs0,125CPU/128Mio et leurs baux exclusifs. À W, les deux tirs sont liés
à des invocations queued sans handler. L'un attend puis réussit avec compteur2
après le HTTP compteur1, dans la même instance ; l'autre est rejected/queue_timeout,
sans handler, tandis que son HTTP reste running. La lecture ultérieure du volume
retrouve compteur1, sans effet du tir refusé.

Le tir deadline expire après démarrage réellement observé, failed/invocation_timeout
et504, sans marqueur de fin ; l'appel HTTP suivant réussit. Les extinctions idle10s
sont mesurées nativement à environ10,59 et10,54s après last_used_at. À W+300,
le handler long est toujours running dans la même instance ; le nouveau tir est
skipped_overlap sans invocation. Le premier termine après315,099s.

La cible1CPU est refused_capacity/schedule_capacity sans invocation aux deux
premières fenêtres. Après libération, son nouveau tir W+600 réussit. Les refus
et le recouvrement sont relus sans rejeu ; les cinq générations courantes suivent
les hashes promus sans cron et portent schedules vide, lectures API vides.

La collecte indépendante recoupe neuf invocations : sept handlers réussis
(trois planifiés, quatre HTTP), une expiration de file sans handler et un timeout
d'exécution. Huit tirs, deux mesures d'extinction, cinq purges publiques avec
absence physique, ressources/réservations nulles. Les34 backends,5982 artefacts
antérieurs, identités/images/démarrages et fichiers officiels sont conservés.
Les deux essais restent séparés du total : cinq fonctions initiales purgées,
puis cinq purgées avant fenêtre sans tir ni invocation. Aucun build produit,
changement UI/manuel ou capture nouvelle. Les autres critères078 restent ouverts.

La [suite RAM/version](SCHEDULE_MEMORY_VERSION.md#résultats-qualifiés) qualifie
ensuite le refus mémoire isolé et le changement de hash après réception en file.
Le plafond global d'instances dépend de SLS-099 ; les critères résiduels restent ouverts.

Le [complément de console](evidence/schedule-console-dev-2026-11-10.json) qualifie
les états vides/erreur, nom63, pagination et reprise401→200 sur la nouvelle image
c59b8616. Les preuves de ce document conservent leur image historique ; elles
ne sont pas présentées comme rejouées par ce complément.
