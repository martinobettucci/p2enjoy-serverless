# Incohérences en cours

## SLS-078.5 — Propriétaire des JSON de première capture

Le loader 00ffa47 suppose UID1001/0600 ; le relevé natif du11novembre trouve
les deux seuls fichiers capture.json/artifacts.json root0600. Le refus a lieu
avant mutation. Issue retenue dans RETENTION_HISTORY_REPLAY : accepter cette
forme exacte à l’intérieur de la source canonique root0700, sans réécrire la
source ; vérifier reçus/empreintes puis qualifier le refus d'âge et le préflight.
Entrée ouverte jusqu'à ces contrôles réels.
