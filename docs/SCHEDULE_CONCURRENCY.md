# Concurrence des appels HTTP et planifiés

Complément de [SLS-078.4](BACKLOG.md#sls-078), selon
[SCHEDULES](SCHEDULES.md#contrat). Décision du11 novembre2026, avant code.

## Campagne réelle

Deux fonctions originales exécutent `scheduled-concurrency.handler`, avec les mêmes
ressources :0,05CPU/128Mio, maximum3, minimum0, idle60s, deadline60s, file30s,
stockage partagé et données/cache désactivés. Seule leur concurrence diffère :
1 pour `serialized-http-and-schedule`,2 pour `parallel-http-and-schedule`.
Les budgets officiels restent32 instances/1CPU/8192Mio.

Publier puis promouvoir leurs crons `*/5 * * * *` avant une même frontière W,
avec au moins80s de préparation. Vers W−20s, lancer un vrai POST HTTP par
fonction ; le handler attend réellement jusqu'à W+20s, au plus45s.
Observer avant W les deux appels running/handler_started, une instance busy
chacun et les budgets permettant encore une troisième instance.

Après W et avant la fin des HTTP, les deux tirs sont reçus :

- concurrence1 : invocation queued, sans admission ni handler, tir dispatched ;
  une seule instance alors que maximum3 et budgets libres autorisent davantage ;
- concurrence2 : invocation planifiée running sur une deuxième instance réelle,
  puis succeeded pendant le HTTP encore running. Le handler du cron attend
  réellement cinq secondes pour permettre le relevé natif pendant son exécution.

Le lecteur natif existant `schedule-instance-reuse-inspect.py` recoupe les deux
UUID du namespace propre, SQL RO sous propriétaire, configurations, Docker,
ressources et files. Une observation commune doit retrouver l'attente de la
première fonction et l'exécution de la seconde pendant les deux HTTP actifs.
Les relevés natifs sont persistés avant leurs assertions pour conserver aussi
le diagnostic d'un échec. La fin du second cron est ensuite observée avant HTTP.
Après libération, le tir en attente réussit : admitted_at après completed_at du
HTTP de sa fonction. Quatre appels réussis, exactement deux tirs ; hash,
requestId, trigger/slot et logs du handler sont corrélés, sans rejeu.

## Nettoyage et portée

Attendre les deux HTTP même en cas d'échec. PUT minimum0/idle0 et attendre la
libération avant promotion des hashes sans cron. Révoquer le jeton Read,
archiver/purger les deux fonctions et supprimer leurs parents par les API.
Le lecteur natif recoupe code/volumes/conteneurs/réseaux/baux/canaux absents,
5982 artefacts antérieurs conservés, backend embarqué conforme, services et
fichiers officiels identiques. Aucun build produit ni changement UI/manuel.

Quatre groupes : préparation et occupation ; observation discriminante à W ;
succès après libération sans rejeu ; purges publiques et absence physique.
La rétention, l'adaptateur.7, les pannes propres du banc et la régression complète
restent dans SLS-078 ; ce scénario ne les qualifie pas.

## Premier essai et fenêtre d'observation

Le clientb282bf2 échoue à03:50UTC sur le total d'instances après succès du cron
parallèle. Le lecteur a relevé son instance, mais le détail du relevé n'était
pas persisté avant l'assertion ; le nombre observé exact n'est pas reconstruit.
Les deux fonctions sont purgées et les ressources nulles. Source du moteur :
une demande en attente peut faire retirer une instance ready d'une autre
fonction, même avant idle60s (`Execution.tick`, réclamation de capacité).
Le délai idle ne garantit donc pas la conservation pour ce relevé tardif.
Observer le vrai handler pendant ses cinq secondes d'exécution, puis sa fin ;
aucune modification d'admission, de deadline ou d'horloge. Rapport et checkpoint
initiaux sont conservés, sans réussite rétroactive.

## Résultat qualifié

La [preuve08d1512](evidence/schedule-concurrency-dev-2026-11-11.json) passe quatre
groupes réels sur333sources et la même imagec59b8616, frontière03:55UTC.
Le relevé natif retrouve trois conteneurs et quatre appels non terminaux :
deux HTTP running, un cron queued sans handler, l'autre running. Celui-ci
réussit avant son HTTP ; le cron sérialisé n'est admis qu'après la fin du sien.
Quatre handlers réussis, deux tirs et aucun rejeu. Deux purges physiques,
services/configurations et5982 artefacts conservés ; aucune nouvelle image.
L'essai initial est exclu. Les pannes propres et la régression complète ne
sont pas déduites de ce nominal.
