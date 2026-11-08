# Incohérences hors de l’unité en cours

## INC-001 — Introduction du contrat API périmée sur SLS-065

Constat du 8 novembre 2026 : `docs/CONTROL.md` introduction annonce encore que
les commandes de purge/cache ne sont pas livrées. Les routes existent dans
`control/app/storage_management.py` et les preuves SLS-065 puis la régression
de 467 groupes recoupent leur déploiement/qualification. La phrase contredit
le README et les preuves. Corriger ce statut documentaire dans la boucle de
résolution après les preuves ciblées de l’unité, sans changer ces routes.
