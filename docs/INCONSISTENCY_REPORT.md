# Incohérences en cours

## SLS-078.5 — Propriétaire des JSON de première capture

Le loader 00ffa47 suppose UID1001/0600 ; le relevé natif du11novembre trouve
les deux seuls fichiers capture.json/artifacts.json root0600. Le refus a lieu
avant mutation. Issue retenue dans RETENTION_HISTORY_REPLAY : accepter cette
forme exacte à l’intérieur de la source canonique root0700, sans réécrire la
source ; vérifier reçus/empreintes puis qualifier le refus d'âge et le préflight.
Entrée ouverte jusqu'à ces contrôles réels.

## SLS-078.5 — Délai d’observation au premier démarrage

Le premier préflight source échoue sur native_stop_not_observed ; restitution
nominale et contrôle natif final réussis. Le lecteur interrogeait les témoins
sur toutes les fermetures de fichiers, y compris les imports de démarrage.
Limiter ces lectures aux descripteurs SQLite réels et conserver des compteurs
et le diagnostic terminal. Le second essai mesure41424 stops et5842 frontières SQLite avant expiration.
Limiter les lectures à fdatasync, sans augmenter25s ; un nouveau préflight
reste requis. Le rôle précis de chaque coût ne se déduit pas des compteurs.
