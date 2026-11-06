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
Les facettes Instances et Invocations sont déployées : allocations et mesures
séparées, détails des appels et journaux expurgés, pagination et rafraîchissement
manuel. Le [contrat](../docs/CONSOLE_EXECUTION.md) et la
[preuve](../docs/evidence/console-execution-dev-2026-11-07.json) recoupent 12 groupes
propres à ces vues et 28 groupes de régression, avec 25 captures relues.
La publication et la gestion des révisions depuis l’UI restent à réaliser.

Depuis la racine, avec la session SSO réelle :

```sh
node e2e/execution-ui.mjs
python3 -B e2e/execution-suite.py --scope console
```

Ces deux commandes sont des campagnes distinctes ; la seconde rejoue aussi
la première avec les parcours publics, de connexion et de gestion.
