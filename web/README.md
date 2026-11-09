# Console web

La suite SLS-074 est déployée pour qualification en DEV : versions groupées par hash,
publication/promotion séparées, archive/restore/delete, réimportation explicite
et adresses épinglées. Le manuel source accompagne ces changements. Le build
Vite local et Docker passent ; six groupes navigateur et huit du manuel passent
dans le [checkpoint008](../docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json),
avec28 captures inspectées. Les vrais409/404 conservent confirmation, saisie et
focus ; un dialog reste ouvert lorsque sa carte quitte la page pendant une
publication externe. Pannes et régression complète restent à éprouver.
Le checkpoint007 ci-dessous reste historique.

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
Le guide courant compte quinze chapitres, dont Retrouver une fonction, le
vidage du cache, la purge et les adresses d’appel. La campagne SLS-067 recoupe
son empreinte, ses quinze chapitres, 46 paragraphes, le tableau et la commande.
Quatorze captures du guide sont inspectées, dont trois vues du nouveau chapitre ;
le chapitre Adresses d’appel possède aussi son viewport mobile dédié. La [qualification complète du stockage public](../docs/evidence/storage-console-dev-2026-11-08.json)
recoupe ces huit groupes, dix parcours UI stockage, les régressions et leurs captures.
La [preuve du correctif de purge](../docs/evidence/storage-legacy-recovery-dev-2026-11-07.json)
rejoue ces huit groupes et ajoute une capture de lecture mobile du nouveau
paragraphe sur une purge en attente après changement du stockage. Les douze
captures sont inspectées ; le document affiché correspond à sa source.

La [preuve de configuration commune](../docs/evidence/service-configuration-dev-2026-11-08.json)
rejoue les onze groupes de gestion et les huit du manuel, puis complète la lecture
des niveaux service/fonction et du déploiement. Ses 21 captures sont inspectées,
dont les sept vues de gestion, onze du guide et trois lectures complémentaires.

## Adresses d’appel en qualification

La fiche de fonction présente la facette **Adresses d’appel**, également liée
depuis sa ligne du service. Le catalogue officiel fournit méthodes, URL et
transport déclaré. Les copies natives ont leurs confirmations et refus ; une
erreur de consultation retire les anciennes adresses. Le manuel contient le
chapitre correspondant. Le [checkpoint SLS-066](../docs/evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
passe six groupes propres au parcours navigateur et ses régressions, avec
sept captures inspectées. Les pages suivantes et les changements réels de
routes restent à qualifier ; aucune preuve simulée ne les remplace.
La [régression complète](../docs/evidence/invocation-urls-regressions-dev-2026-11-08.json)
recoupe 79 captures fraîches de l’ensemble des parcours : 61 observations
visuelles et 18 identités SHA avec les références inspectées, sans défaut
bloquant constaté. Le manuel servi correspond aux 14 chapitres et 43 paragraphes
de sa source. Les limites d’observation sont précisées dans le design du produit.


## Catalogue global qualifié

L’accueil Fonctions et /console/functions présentent la table globale ;
Namespaces possède sa destination /console/namespaces. Recherche temporisée,
filtres recherchés/paginés, tri, état et page sont partageables dans la query.
Le retour depuis une fiche traverse ses six facettes et se recale après une
suppression. Les erreurs retirent les anciennes lignes ; une session admin
reste obligatoire pour les trois lectures de catalogue.

La [preuve SLS-067](../docs/evidence/function-catalogue-dev-2026-11-08.json)
retient 37 campagnes uniques / 489 groupes réels et six prérequis : 447 groupes
aux clients inchangés puis 42 réexécutés sur les mêmes sources produit/images.
Deux époques de clients restent déclarées. Les 98 images sont inspectées, dont
seize du catalogue avec les trois positions de table mobile et le dialog en
viewport. Les noms complets restent lisibles sans élargir le document.
La remarque mineure de titre d’archive après purge est suivie dans SLS-075.


## Hash du code dans les révisions

La carte montre le hash64 complet, distinct du SHA des octets ZIP, et sa copie
native avec confirmation/refus utiles. Le résultat disparaît à la prochaine
observation. Le manuel canonique est compilé avec la console :15 chapitres et
47 paragraphes recoupés. La [preuve](../docs/evidence/function-version-registry-dev-2026-11-09.json)
qualifie trois groupes ciblés et les régressions ; six nouvelles captures hash,
dont deux viewports réels. Avec les campagnes communes :69 captures recoupées,
47 nouvelles inspections et 22 références SHA strictes. L’upload garde son activation
actuelle ; la promotion distincte et les appels par hash restent en cours.
