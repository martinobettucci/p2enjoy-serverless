# Console web

Console React/Vite servie par le contrôle sur la même origine. Contrats :
[CONTROL](../docs/CONTROL.md), [design du produit](../docs/DESIGN_SYSTEM_APP.md)
et [socle visuel](../docs/DESIGN_SYSTEM.md).

Le build est inclus dans `control/Dockerfile`, lancé dans le SPARK DEV avec
`bash control/dev.sh build`. Aucun serveur de données local ni interception
API : les parcours de qualification ciblent la console réellement déployée.
La console initiale reste en cours de réalisation et de qualification.
