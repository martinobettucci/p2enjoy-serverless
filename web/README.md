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
La facette **Code et révisions** est déployée en qualification : ZIP/handler,
suivi de publication, abandon, métadonnées, activation et suppression.
Son [contrat](../docs/CONSOLE_PUBLICATION.md) conserve les réglages et secrets
côté serveur. Les 14 groupes navigateur passent avec les dix groupes API et
les huit groupes du manuel : [preuve intermédiaire](../docs/evidence/publication-console-checkpoint-dev-2026-11-07.json).
Les pannes résiduelles et les régressions complètes restent à terminer.

Depuis la racine, avec la session SSO réelle :

```sh
node e2e/execution-ui.mjs
node e2e/publication-ui.mjs
python3 -B e2e/execution-suite.py --scope console
```

Ces commandes sont des campagnes distinctes ; la suite rejoue les observations
avec les parcours publics, de connexion, de gestion et du manuel. La publication
reste pour ce checkpoint une commande ciblée distincte de cette suite.

## Manuel d’usage

La navigation ouvre `/console/manual`, avec sommaire, ancres partageables et
retour au sommaire. `docs/manual.md` est la seule source à éditer ;
`vite.config.mjs` la compile en contenu HTML sans HTML brut, avec son empreinte.
Le contexte Docker inclut explicitement ce document. `markdown-it` est verrouillé
en dépendance de build et n’est pas inclus dans le navigateur. Mettre à jour le
guide avec chaque comportement utilisateur, puis reconstruire la console.

`node e2e/manual-ui.mjs` vérifie huit groupes réels. La suite de console ajoute
cette campagne aux quatre précédentes : 48 groupes, zéro échec/skip et 33 captures
relues dans la [preuve initiale](../docs/evidence/manual-console-dev-2026-11-07.json).
Le guide compte maintenant onze chapitres ; sa concordance est rejouée dans
la preuve intermédiaire de publication.
