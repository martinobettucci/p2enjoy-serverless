# Console web

Console React/Vite servie par le contrôle sur la même origine. Contrats :
[CONTROL](../docs/CONTROL.md), [design du produit](../docs/DESIGN_SYSTEM_APP.md)
et [socle visuel](../docs/DESIGN_SYSTEM.md).

Le build est inclus dans `control/Dockerfile`, lancé dans le SPARK DEV avec
`bash control/dev.sh build`. Aucun serveur de données local ni interception
API : les parcours de qualification ciblent la console réellement déployée.
Les 11 parcours de gestion de `node e2e/control-ui.mjs` passent sur le SPARK,
dont les noms longs à 390 px, les trois gestes de fermeture du menu et le
retour du focus. Sept captures ont été relues : [preuve de gestion](../docs/evidence/control-management-dev-2026-11-06.json).
Les vues de publication et d'exécution restent à réaliser.
