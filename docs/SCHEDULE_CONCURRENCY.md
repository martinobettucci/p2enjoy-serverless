# Concurrence des appels HTTP et planifiés

Complément de [SLS-078.4](BACKLOG.md#sls-078), selon
[SCHEDULES](SCHEDULES.md#contrat). Décision du11 novembre2026, avant code.

## Campagne réelle

Deux fonctions originales exécutent `scheduled-capacity.handler`, avec les mêmes
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
- concurrence2 : invocation planifiée succeeded pendant le HTTP encore running,
  sur une deuxième instance réelle. Son CID reste observable grâce à idle60s.

Le lecteur natif existant `schedule-instance-reuse-inspect.py` recoupe les deux
UUID du namespace propre, SQL RO sous propriétaire, configurations, Docker,
ressources et files. Une observation commune doit retrouver l'attente de la
première fonction et le succès de la seconde pendant les deux HTTP actifs.
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
