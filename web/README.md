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
La facette **Code et révisions** est déployée et vérifiée : ZIP/handler,
suivi de publication, abandon, métadonnées, activation et suppression.
Son [contrat](../docs/CONSOLE_PUBLICATION.md) conserve les réglages et secrets
côté serveur. Ses 21 groupes navigateur passent, avec les dix groupes API et
les huit groupes du manuel, dans la [preuve finale](../docs/evidence/publication-console-dev-2026-11-07.json) :
18 campagnes en série, 312 groupes réels et 54 captures inspectées. Les deux
écarts de lecture relevés à la première revue sont corrigés et requalifiés.

Depuis la racine, avec la session SSO réelle :

```sh
node e2e/execution-ui.mjs
node e2e/publication-ui.mjs
python3 -B e2e/execution-suite.py --scope console
```

Ces commandes sont des campagnes distinctes ; la suite rejoue les observations
et la publication avec les parcours publics, de connexion, de gestion et du
manuel. `python3 -B e2e/execution-suite.py --scope publication` ajoute les
régressions du moteur dans une suite commune sans répéter les campagnes partagées.

## Manuel d’usage

La navigation ouvre `/console/manual`, avec sommaire, ancres partageables et
retour au sommaire. `docs/manual.md` est la seule source à éditer ;
`vite.config.mjs` la compile en contenu HTML sans HTML brut, avec son empreinte.
Le contexte Docker inclut explicitement ce document. `markdown-it` est verrouillé
en dépendance de build et n’est pas inclus dans le navigateur. Mettre à jour le
guide avec chaque comportement utilisateur, puis reconstruire la console.

`node e2e/manual-ui.mjs` vérifie huit groupes réels. La
[preuve initiale](../docs/evidence/manual-console-dev-2026-11-07.json) précède la
publication UI : 48 groupes, zéro échec/skip et 33 captures relues. La suite
de console comprend désormais aussi les 21 groupes de publication.
Le guide compte onze chapitres ; sa concordance est rejouée dans la preuve
finale de publication : empreinte, chapitres, 28 paragraphes, tableau et commande.
