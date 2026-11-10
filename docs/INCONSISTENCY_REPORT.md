# Registre d'incohérences

## Ouverts

### Restitution du plafond d'instances sans contrôle de la valeur courante

Constat source : e2e/instance-limit-guard.py applique32 dans finally sans vérifier
la valeur officielle courante. Le SHA protège la proposition, pas une édition
concurrente du plafond actif. Les180s du helper ne constituent pas une restitution
indépendante après son SIGKILL.

Mesure : lecture de apply/finally ; aucun écrasement réellement provoqué ni
nouvelle baisse du plafond. La console normale5175 répond200. Correction et
preuves portées par [SLS-099](BACKLOG.md#sls-099). RAM et changement de version
restent livrables sans cette garde. L'entrée reçoit son issue à la boucle après
leurs preuves ciblées.
