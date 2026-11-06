# Incohérences à résoudre

## Attente de l’upload dans le client de preuve SLS-030

Constat : `e2e/deployments.mjs`, fonction `finishUpload`, appelle récursivement
`finishUpload(pending)` au lieu d’attendre la promesse passée en argument.
La lecture de cette ligne établit une récursion sans condition de sortie.
Elle empêche la preuve et l’attente du nettoyage des vrais uploads concurrents.
Résolution à traiter après la correction UI SLS-020 et avant cette campagne :
attendre la promesse existante et qualifier les scénarios HTTP de publication.
