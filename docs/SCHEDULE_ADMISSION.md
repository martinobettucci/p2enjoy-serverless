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
| Exclusif avec admission |0,125 CPU,128 Mio,données2Mio exclusives,concurrence1,deadline45s,file30s,idle2s,min0,max1 | HTTP Read déjà running avant W, bail réel et écriture compteur1 ; il attend jusqu'à W+10. Tir planifié lié queued sans handler, puis admis après HTTP, compteur2 sur le même volume, succeeded |
| Exclusif avec expiration | Même allocation, file2s ; HTTP actif jusqu'à W+20 | Tir lié à une vraie invocation rejetée queue_timeout, handler non démarré, firing refused_capacity avec UUID. HTTP encore actif au refus ; lecture réelle ultérieure retrouve compteur1. Aucun rejeu après libération |
| Deadline |0,125 CPU,128 Mio,timeout0,5s,idle0,min0,max1 ; handler planifié attend5s | Invocation failed/invocation_timeout, handler démarré et conteneur recyclé ; aucun marqueur de fin. Appel HTTP suivant immédiat réellement réussi |

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

Fin : attendre les appels réellement terminaux, révoquer les jetons, archiver et
purger les cinq fonctions par leurs API, supprimer les parents. Recouper code,
volumes, conteneurs, réseaux, canaux, reçus et compteurs nuls ;5982 artefacts
antérieurs conservés,34 backends et sources/images/configuration inchangés.
Un échec conserve son rapport, termine ses appels puis nettoie avant toute relance
explicite. Aucun retry automatique de la campagne ou des invocations.

Cette tranche ne qualifie pas la rétention, les états UI complémentaires ni la
régression complète ; SLS-078 reste[~] jusqu'à leurs preuves.
