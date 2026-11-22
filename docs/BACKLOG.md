# Backlog

Le backlog est l'**unique source des unités à développer, corriger ou qualifier**.
Un agent qui reprend le travail part du [registre des unités ouvertes](#registre-des-unités-ouvertes),
prend l'unité de plus petit ordre non terminée, lit son contrat, puis la livre
avec les [critères communs](#critères-communs-à-toutes-les-unités). Les
documents [demandes et livraison](DEMANDES_ET_LIVRAISON.md) et
[objectif autonome](OBJECTIF_AUTONOME.md) renvoient ici ; ils ne portent aucun
ordre ni aucun statut propre.

## Alimentation du backlog

- Toute demande, tout défaut, tout écart de parité et tout reste de qualification
  devient une **unité identifiée** dès sa réception, avec sa nature, ses
  dépendances, ses critères cochables et ses tests. Une phrase « reste à
  qualifier » ou « à poursuivre » dans le récit d'une unité n'est pas un suivi :
  elle devient une unité du registre.
- Quatre natures : **Développer** (fonctionnalité absente), **Corriger** (défaut ou
  comportement non conforme au contrat), **Qualifier** (le code existe, des
  preuves contractuelles manquent), **Décision** (le dépôt ne permet pas de
  trancher, cas d'arbitrage nommé).
- Les récits de preuves (campagnes, empreintes, nettoyages) vivent dans
  `docs/evidence/` et `docs/JOURNAL.md`. L'unité garde le résultat attendu, les
  critères, les tests exigés et un lien vers la preuve la plus récente.
- Statuts : `[ ]` non commencé, `[~]` implémenté ou en cours mais insuffisamment
  vérifié, `[x]` terminé et intégralement vérifié. Un critère coché `[x]` porte sa
  preuve. Une unité passe à `[x]` quand tous ses critères le sont et que ses
  documents, seed, schéma et manuel ont suivi.
- Une unité parente restée `[~]` désigne l'unité enfant qui porte son reste à
  faire ; elle passe à `[x]` quand l'enfant l'est et que ses propres critères
  restent prouvés par la campagne de clôture ([SLS-095](#sls-095)).
- Les ancres `#sls-NNN` sont stables : le code et les tests les citent
  (`@spec`, `@verifies`). Une unité n'est ni renumérotée ni déplacée.

## Critères communs à toutes les unités

Ils complètent la Definition of Done de `CLAUDE.md` et ne sont pas répétés dans
chaque unité.

1. **Contrat d'abord.** Spécification, décisions et motifs sont écrits et commités
   avant le code qui en dépend ; chaque fichier porte `@spec` / `@verifies` vers
   l'unité et les chapitres.
2. **Cible.** SPARK DEV uniquement ; jamais PREPROD/PROD ; la référence client est
   en lecture seule ; les fixtures sont originales.
3. **Tests propres à l'unité**, sans mock ni test ignoré : un test unitaire, un test
   d'API ou d'intégration quand une API, une base, un service ou une autorisation
   est en jeu, un test E2E sur le code réellement déployé, un scénario à la fois.
4. **Autorisations** : toute règle d'accès est refusée côté serveur et prouvée par
   requête directe avec les vrais droits du profil concerné.
5. **Interface** : lecture préalable des deux design systems ; parcours depuis
   l'accueil, connecté par le vrai SSO, à la souris et au clavier ; états
   chargement, vide, erreur, données longues, mobile ; captures JPEG inspectées sur
   ordinateur et mobile ; `docs/DESIGN_SYSTEM_APP.md` à jour.
6. **Pannes et reprise** quand l'opération est durable : réponse perdue, SIGKILL du
   contrôle, redémarrage, absence de rejeu, ressources physiques restituées.
7. **Documents dans le même changement** : manuel (`docs/manual.md`, affiché par la
   console), `SCHEMA.md` et migration versionnée, seed, `DAT.md`, README,
   `CHANGELOG.md` sous « Non publié », contrat de déploiement, matrice
   [SCALEWAY_PARITY](SCALEWAY_PARITY.md), ce backlog.
8. **Preuve = code déployé** : sources et images de la preuve identiques à ce qui
   est installé sur le SPARK DEV ; nettoyage des ressources de test recoupé.

## Registre des unités ouvertes

Tri par **ordre de reprise**. Les unités terminées sont plus bas, dans leur détail.
« Dépend de » liste ce qui doit être livré avant ; une unité dont la dépendance est
bloquée est sautée et son blocage est nommé.

| Ordre | Unité | Nature | Statut | Dépend de | Contrat |
| --- | --- | --- | --- | --- | --- |
| 1 | [SLS-111](#sls-111) Reprise du banc de stockage géré après six groupes | Corriger | `[~]` | SLS-050 | [MANAGED_STORAGE_REGRESSIONS](MANAGED_STORAGE_REGRESSIONS.md) |
| 2 | [SLS-089](#sls-089) Défauts SSO : attente, azp, rotation de clé | Corriger | `[~]` | SLS-020 | [sso](sso.md), [CONTROL](CONTROL.md) |
| 3 | [SLS-072](#sls-072) Journaux recherchables et corrélation | Développer | `[~]` | SLS-061, SLS-074 | [EXECUTION_LOGS](EXECUTION_LOGS.md) |
| 3 | [SLS-120](#sls-120) Frontière réelle du buffer de journaux | Corriger | `[~]` | SLS-040, SLS-121 | cette unité |
| 3 | [SLS-121](#sls-121) Frontières natives de décision du journal | Corriger | `[~]` | SLS-040 | cette unité |
| 3 | [SLS-122](#sls-122) Clôture du client de diagnostic après refus natif | Corriger | `[~]` | SLS-040 | cette unité |
| 3 | [SLS-123](#sls-123) Armement de la coupure après compteur durable | Corriger | `[~]` | SLS-040 | cette unité |
| 3 | [SLS-124](#sls-124) Restitution du focus des commandes Journaux | Corriger | `[~]` | SLS-061 | cette unité |
| 3 | [SLS-125](#sls-125) Corrélation du hash des événements conservés | Corriger | `[~]` | SLS-040 | cette unité |
| 3 | [SLS-126](#sls-126) Acquisition des lecteurs retenus d’API12 | Corriger | `[~]` | SLS-040 | cette unité |
| 3 | [SLS-127](#sls-127) Refus SQLite après épuisement réel des descripteurs | Corriger | `[~]` | SLS-040 | cette unité |
| 3 | [SLS-128](#sls-128) Purge réelle après journal de 16Mio | Corriger | `[~]` | SLS-040 | cette unité |
| 3 | [SLS-101](#sls-101) État de fiche après publication concurrente | Corriger | `[ ]` | SLS-071 | cette unité |
| 3 | [SLS-119](#sls-119) Réponse JSON de gestion incomplète | Corriger | `[ ]` | SLS-020 | cette unité |
| 4 | [SLS-081](#sls-081) Jobs de console | Développer | `[ ]` | SLS-078, SLS-072 | [SERVERLESS_JOBS](SERVERLESS_JOBS.md) |
| 5 | [SLS-083](#sls-083) Limites et en-têtes alignés sur Scaleway | Développer | `[ ]` | SLS-040 | [SCALEWAY_PARITY](SCALEWAY_PARITY.md), [EXECUTION](EXECUTION.md) |
| 5 | [SLS-080](#sls-080) Compatibilité du projet de référence | Développer | `[~]` | SLS-078, SLS-083 | [REFERENCE_COMPATIBILITY](REFERENCE_COMPATIBILITY.md) |
| 6 | [SLS-068](#sls-068) Favoris personnels | Développer | `[ ]` | SLS-067 | [CONSOLE_USABILITY](CONSOLE_USABILITY.md#favoris-personnels) |
| 6 | [SLS-069](#sls-069) Renommage et suppression en masse | Développer | `[ ]` | SLS-067, SLS-074 | [CONSOLE_USABILITY](CONSOLE_USABILITY.md#opérations-en-masse) |
| 6 | [SLS-075](#sls-075) Titre de la fiche d'archive après purge | Corriger | `[ ]` | SLS-065 | cette unité |
| 6 | [SLS-113](#sls-113) Pagination des lectures de console pendant erreur et chargement | Corriger | `[ ]` | SLS-065 | [CONSOLE_PAGINATION_STATES](CONSOLE_PAGINATION_STATES.md) |
| 6 | [SLS-102](#sls-102) Espacement des quantités du manuel du testeur | Corriger | `[ ]` | SLS-062 | cette unité |
| 7 | [SLS-073](#sls-073) Monitoring historique et alertes | Développer | `[ ]` | SLS-072, SLS-078 | [CONSOLE_USABILITY](CONSOLE_USABILITY.md#monitoring-et-alertes) |
| 8 | [SLS-084](#sls-084) Runtimes supplémentaires | Développer | `[ ]` | SLS-083 | [SCALEWAY_PARITY](SCALEWAY_PARITY.md) |
| 8 | [SLS-086](#sls-086) Répartition du trafic entre versions | Développer | `[ ]` | SLS-074, SLS-073 | [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md) |
| 8 | [SLS-087](#sls-087) Conditions d'accès horaire et user-agent | Développer | `[ ]` | SLS-040 | [PLATFORM](PLATFORM.md) |
| 8 | [SLS-098](#sls-098) Noms de mois et jours dans les crons | Développer | `[ ]` | SLS-078 | [SCHEDULES](SCHEDULES.md), [SCALEWAY_PARITY](SCALEWAY_PARITY.md) |
| 9 | [SLS-097](#sls-097) API de gestion documentée (OpenAPI) | Développer | `[ ]` | unités 3 à 8 | [CONTROL](CONTROL.md) |
| 10 | [SLS-090](#sls-090) Pannes résiduelles de publication | Qualifier | `[ ]` | SLS-030 | [DEPLOYMENT](DEPLOYMENT.md) |
| 10 | [SLS-091](#sls-091) Rétention et nettoyage du moteur d'exécution | Qualifier | `[~]` | SLS-040 | [EXECUTION](EXECUTION.md) |
| 10 | [SLS-092](#sls-092) Stockage : acquisition partielle, marge, registre | Qualifier | `[ ]` | SLS-050 | [STORAGE_AGENT](STORAGE_AGENT.md) |
| 10 | [SLS-093](#sls-093) Fautes de source et de transport des URL d'appel | Qualifier | `[ ]` | SLS-066 | [INVOCATION_URLS](INVOCATION_URLS.md) |
| 10 | [SLS-094](#sls-094) Pannes, console et régression de SLS-074 | Qualifier | `[ ]` | SLS-074 | [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md) |
| 11 | [SLS-079](#sls-079) Guide d'exploitation rejoué | Développer | `[ ]` | unités 1 à 10 | [OPERATIONS](OPERATIONS.md) |
| 12 | [SLS-095](#sls-095) Campagne complète et clôture | Qualifier | `[ ]` | toutes | [TEST_MATRIX](TEST_MATRIX.md) |
| — | [SLS-085](#sls-085) Déclencheurs de file et NATS | Décision | `[ ]` | choix du courtier | [SCALEWAY_PARITY](SCALEWAY_PARITY.md) |
| — | [SLS-088](#sls-088) Serverless Jobs en conteneur | Décision | `[ ]` | choix des images | [SCALEWAY_PARITY](SCALEWAY_PARITY.md) |

SLS-078 est close par la [campagne complète du 22 novembre](evidence/schedules-regressions-dev-2026-11-22.json) :
49 campagnes / 543 groupes et 18 prérequis, 458 sources `9e1da70`, image `433da150`,
117 captures fraîches inspectées, 127 fonctions / 35 namespaces recoupés après
purge. Les trois preuves de rétention restent acquises sans nouveau rejeu ni
réécriture de leurs captures scellées. Les cinq anciens essais incomplets et
les campagnes des préalables restent séparés du total.

111.1/.2 restent non déterminées faute d’observation historique discriminante ;
111.3 et les régressions courantes sont qualifiées. La résolution IR-004 conserve
ce reste sans lui attribuer une cause par le succès futur. Les autres unités
indépendantes avancent ; les deux expressions exactes de référence restent 080.

Les critères089.1/.2/.3 attendent les accès/profils et rotation réels du cas4 ;
089.4 est qualifié. Les [32 groupes ZIP](evidence/code-editor-archive-boundaries-dev-2026-11-22.json)
clôturent SLS-114 et complètent les preuves de070.1. Les
[36groupes d’attentes UI](evidence/code-editor-adoption-focus-dev-2026-11-22.json)
clôturent115/116 et complètent070.4 par rapprochement des preuves de diff/recherche/
chemins. Les [29groupes de reprise](evidence/code-editor-control-interruption-dev-2026-11-22.json)
ferment070.3/.5 et118 ; les huit critères de070 sont clos, époques rapprochées
sans addition des groupes historiques.

Unités parentes encore `[~]` et unités qui portent leur reste à faire :
[SLS-001](#sls-001) → toutes ; [SLS-020](#sls-020) → SLS-089 ;
[SLS-030](#sls-030) → SLS-090 et SLS-080 ; [SLS-040](#sls-040) → SLS-091 ;
[SLS-050](#sls-050) → SLS-092 ; [SLS-060](#sls-060) → SLS-068, SLS-069, SLS-072, SLS-073,
SLS-081 et SLS-095 ; [SLS-066](#sls-066) → SLS-093 ;
[SLS-074](#sls-074) → SLS-094 ; [SLS-082](#sls-082) → SLS-083 à SLS-088 et SLS-097.

## Décisions et autorités en attente

Seuls les cas de la demande d'arbitrage figurent ici. Ce qui reste livrable sans
la réponse est livré sans attendre.

| Point | Cas | Ce qui bloque | Livrable sans la réponse |
| --- | --- | --- | --- |
| Courtier de messages pour Queue/NATS | 4 (infrastructure du SPARK) et éventuellement 2 | [SLS-085](#sls-085) | Tout le reste du registre |
| Origine des images de conteneur des Serverless Jobs | 3 (choix de produit) | [SLS-088](#sls-088) | Tout le reste du registre ; les jobs de console (SLS-081) sont distincts |
| Budget de cellule CPU/RAM pour les minima de la référence (au moins 1,5 CPU et 2 Gio) | 4 (proposition `.?` au propriétaire du SPARK) | La campagne complète de [SLS-080](#sls-080) | Adaptateur, fixtures, 12 des 13 fonctions à un budget plus bas, preuves hors budget |
| Autorité d'installation temporaire pour rejouer le guide | 4 | [SLS-079](#sls-079) | Rédaction du guide, tableau de configuration comparé au code |
| Deux profils SSO (non vérifié, verified seul), refus azp/aud sous signature réelle et rotation de clé maîtrisée | 4 | Critères 089.1/.2/.3 de [SLS-089](#sls-089) | Correctifs déployés, nominal admin/renouvellement et300 s qualifiés ; vues publiques inspectées |

## Suivi des demandes du responsable

Toute demande produit, correction ou contrainte reçue est inscrite ici dès sa
réception, dans l'unité existante correspondante ou dans une nouvelle unité
identifiée. Les corrections complètent le contrat existant ; elles ne
disparaissent pas derrière une nouvelle reformulation. Les valeurs de secrets ne
sont jamais consignées dans le backlog. L'état d'une demande se lit dans l'unité.

Les demandes confirmées sont rattachées aux unités suivantes. Leur état et
leurs preuves font autorité dans le détail de chaque unité.

| Demande confirmée | Unités et contrats concernés |
| --- | --- |
| Méthode Software Factory importée dans le dépôt, hors module de séminaire | [SLS-000](#sls-000), [METHODE](METHODE.md) |
| Plateforme Docker compatible avec l’exploitation des projets existants, handlers conservés et adaptateur `serverless.yml` | [SLS-001](#sls-001), [SLS-030](#sls-030), [DEPLOYMENT](DEPLOYMENT.md) |
| Application de qualification et sources présentes dans ce dépôt | [QLF-001](#qlf-001) |
| Toutes les fonctionnalités livrées testées E2E sur les vrais composants, sans mock ni skip | [QLF-001](#qlf-001), [SLS-001](#sls-001), critères E2E de chaque unité |
| SPARK DEV autorisé, FORGE limitée au rebond, référence client en lecture seule, aucun lancement PREPROD/PROD | [Contrat local](../CLAUDE_PROJECT.md), [QUALIFICATION_DEV](QUALIFICATION_DEV.md) ; contraintes de toutes les unités |
| Noms significatifs par fonction et usage, domaine `serverless.lelabs.tech`, route sur 18090 | [SLS-011](#sls-011), [DEPLOYMENT_NAMES](DEPLOYMENT_NAMES.md), règle de nommage du contrat local |
| Remplacer la foudre, déjà utilisée par une autre application interne, par une icône propre à Serverless | [SLS-100](#sls-100) |
| SSO réel, rôles verified/admin, namespaces, services, fonctions et gestion des jetons CRUD de service | [SLS-020](#sls-020), [SLS-060](#sls-060), [CONTROL](CONTROL.md) |
| Jeton Read pour invoquer, droits Create/Update/Delete, authentification métier indépendante | [SLS-020](#sls-020), [SLS-030](#sls-030), [SLS-040](#sls-040), [PLATFORM](PLATFORM.md) |
| Jetons, variables et secrets au niveau service, avec surcharges par fonction | [SLS-020](#sls-020), [SLS-031](#sls-031), [configuration commune](SERVICE_CONFIGURATION_URLS.md) |
| Restrictions par origine web et/ou IP, configurables au niveau service | [SLS-040](#sls-040), [PLATFORM](PLATFORM.md) |
| CPU, mémoire, concurrence, durée maximale d’exécution et délai d’arrêt après inactivité | [SLS-040](#sls-040), [SLS-060](#sls-060), [EXECUTION](EXECUTION.md) |
| Disque par identifiant stable, données permanentes et cache configurables, quotas, archive et purge | [SLS-010](#sls-010), [SLS-050](#sls-050), [SLS-064](#sls-064), [SLS-065](#sls-065) |
| Manuel d’usage maintenu et consultable dans l’application | [SLS-062](#sls-062), [SLS-096](#sls-096) (manuel déployé conforme à sa source), [CONSOLE_MANUAL](CONSOLE_MANUAL.md) ; mise à jour avec chaque livraison |
| Chemins d’appel calculés depuis les domaines réellement affectés au SPARK | [SLS-066](#sls-066) |
| Recherche, filtres et catalogue opérationnel | [SLS-067](#sls-067) |
| Favoris personnels | [SLS-068](#sls-068) |
| Suppression et renommage en masse | [SLS-069](#sls-069) |
| Édition du code et du handler sur place | [SLS-070](#sls-070) |
| Client HTTP intégré par fonction, avec réponse et diagnostic d’appel | [SLS-071](#sls-071) |
| Logging, recherche et corrélation des journaux | [SLS-072](#sls-072) |
| Monitoring historique et alertes | [SLS-073](#sls-073) |
| Version par hash du code changé, upload identique dédupliqué, invocation épinglée, rollback et pilote stable | [SLS-074](#sls-074), [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md) |
| Méthode importée fidèlement : `docs/.routine` et rôles d’origine | [SLS-000](#sls-000), [METHODE](METHODE.md) |
| Planifications (crons) du manifeste, réellement déclenchées | [SLS-078](#sls-078) pour le moteur ; [SLS-080.3, .7 et .8](#sls-080) pour les deux expressions exactes de la référence ; [SCHEDULES](SCHEDULES.md) |
| Jobs serverless : payload fixe, gabarits composés dans l’UI, expression crontab contrôlée par fenêtres de 5 minutes | [SLS-081](#sls-081), [SERVERLESS_JOBS](SERVERLESS_JOBS.md) |
| Répliquer toutes les fonctionnalités de Scaleway Serverless | [SLS-082](#sls-082) et unités 083 à 088, [SCALEWAY_PARITY](SCALEWAY_PARITY.md) |
| Compatibilité du projet de référence établie par contrats et fixtures | [SLS-080](#sls-080), [REFERENCE_COMPATIBILITY](REFERENCE_COMPATIBILITY.md) |
| Exploitation complète et reproductible, guide rejoué | [SLS-079](#sls-079), [OPERATIONS](OPERATIONS.md) |
| Écarts SSO identifiés par la revue du contrat OIDC (attente, azp, rotation de clé) | [SLS-089](#sls-089) |
| Restes de qualification : pannes de publication, moteur, stockage, URL d’appel, versions | [SLS-090](#sls-090) à [SLS-094](#sls-094) |
| API de gestion complète et documentée (parité Scaleway) | [SLS-097](#sls-097) |
| Campagne complète en série, zéro échec et zéro test ignoré, preuves = code déployé | [SLS-095](#sls-095) |

## SLS-000

Statut : [x] — socle importé, hooks standard activés, 45 contrôles Git réels
réussis. Provenance : [factory-import.json](evidence/factory-import.json).
`docs/.routine` et le rôle `factory_verifier` sont identiques à l’original (seule
l’en-tête de traçabilité est adaptée) depuis le 10 novembre 2026 ; le harnais a
été rejoué : 45 succès, zéro échec. CloudWorker s’applique avec les adaptations de
[CLAUDE_PROJECT](../CLAUDE_PROJECT.md#adaptation-de-cloudworker).

Importer le socle opérationnel de `P2Enjoy/software-factory-base` au commit
`886ba5a28a834a5f08fd1a01ec8dd78787317559`, sans formation, publication de
formation ni design system pédagogique. Conserver les contrats globaux et
documenter les contraintes locales prioritaires. Inclure hooks exécutables,
scripts, rôles des agents et preuve réelle de leur fonctionnement avec Git.
Conserver une provenance par fichier. Spécification : [Méthode](METHODE.md).

La qualification complète QLF-001 exige zéro test ignoré et la couverture des
comportements livrés : erreurs, limites, saturation, configuration, stockage
et cycle de vie. Une dépendance absente fait échouer la campagne ; elle ne
la transforme pas en succès partiel.

## QLF-001

Statut : [x] — 38 tests HTTP E2E et 28 contrôles Docker/pannes réussis,
zéro échec et zéro test ignoré. Smoke et recréation avec reprise complète du
worker réussis. Les secrets réels sont configurés. Sources locales et déployées
identiques. [Preuve complète](evidence/qualification-dev-2026-11-05-complete.json).
Les résultats 17/19 restent historiques.

Créer un service synthétique dans `qualification/`, sans dépendance au client,
avec manifeste `serverless.yml`, handlers CommonJS et exécuteur de référence
DEV. Spécification : [DAT — Qualification](DAT.md#qualification).

Critères d'acceptation :

- contrats HTTP, événement/contexte/réponse, callback et authentification métier ;
- données persistantes par identifiant stable et cache invalidable séparément ;
- worker coopératif, interruption extérieure d'une invocation non coopérative,
  erreurs maîtrisées et invocation saine après un échec ;
- scénario synthétique d'appel entre fonctions, sans accès externe ;
- parcours E2E HTTP automatisés sur la pile réelle, sans mocks, exécutés
  séquentiellement ; aucun test ignoré, tous les prérequis exigés ;
- build et exécution Docker dans le seul SPARK DEV autorisé, puis preuve de
  conservation des données après recréation du conteneur ;
- documentation d'exploitation et trois propositions de notes dans la cellule ;
- aucune modification de FORGE et aucune utilisation du client comme fixture.

Le banc n'implémente ni SSO, ni jetons CRUD de plateforme, ni ordonnanceur cron,
ni autoscaling, ni isolation Docker par fonction. Ces exigences demeurent dans
le cadrage et feront l'objet d'unités propres à la plateforme.

Les preuves initiales sont conservées comme historique. La campagne complète
suit [la matrice](TEST_MATRIX.md) et doit vérifier chaque contrat présent avec
le code réel. Le banc ne vaut pas preuve des fonctionnalités de plateforme
non encore implémentées.


## SLS-001

Statut : [~] — réalisation par les unités du [registre](#registre-des-unités-ouvertes) ;
clôturée par [SLS-095](#sls-095).

Spécifier puis livrer par unités cohérentes les fonctions confirmées du produit :
SSO admin, namespaces/services/functions, jetons CRUD et invocations avec jeton,
règles origine/IP, gestion du code/configuration/secrets, adaptateur
serverless.yml, allocation Docker, mémoire, disques durables/cache par ID,
deadline d'invocation et extinction des instances. Chaque comportement livré
exige sa preuve E2E réelle, notamment les refus et cycles de vie.
Le périmètre inclut le manuel intégré, le calcul des URL du SPARK et les
demandes d’ergonomie et d’observabilité détaillées dans SLS-062 et SLS-066 à SLS-073,
ainsi que versions par hash, invocation épinglée et pilote dans SLS-074.
Le banc QLF-001 constitue l'application indépendante pour cette qualification.
Aucun de ses résultats ne clôture ces fonctionnalités de plateforme absentes.

Spécification commune : [Contrat de plateforme](PLATFORM.md).

## SLS-010

Statut : [x] — composant de quota qualifié par 31 contrôles réels,
zéro échec/skip ; client SSO créé, authentification du client vérifiée,
variables/secret de cellule appliqués, DNS et TLS DEV opérationnels.
Preuve : [stockage DEV](evidence/storage-dev-2026-11-05.json).

Qualifier le quota dur par fonction, le montage dans Docker rootless et sa
persistance. Préparer l'intégration SSO réelle, le domaine DEV et les variables
de cellule. Preuves : écriture jusqu'au plafond, isolation entre deux volumes,
remontage, nettoyage des seules ressources de l'expérience. Un accès SSO
manquant est nommé ; aucun fournisseur d'identité de remplacement.

## SLS-011

Statut : [x] — noms et domaine appliqués, persistance et connexion SSO réelle
sur la nouvelle adresse vérifiées.

Rendre les noms Docker explicites par rôle et adopter `serverless.lelabs.tech`
dans le SPARK de développement. Contrat : [noms d’exploitation](DEPLOYMENT_NAMES.md).
Conserver les données et les identifiants Compose, qualifier la recréation
réelle, la route TLS 18090, la configuration officielle et le parcours SSO.
Le nouveau callback est accepté par le vrai fournisseur le 6 novembre ; la
route a été corrigée vers 18090 par le responsable. Les deux conteneurs sont
healthy sous leurs nouveaux noms, avec les mêmes images, volumes, objets et
identité de base. Compteur, cache et checkpoint sont retrouvés par HTTP ; le
calcul reprend jusqu’au résultat complet. 38 tests HTTP, neuf contrôles
navigateur, huit groupes publics, quatre chemins réseau et quatorze contrôles
CLI passent. La connexion personnelle sur le nouveau domaine produit une
session authentifiée et l’API administrateur des namespaces répond 200.
[Preuve de migration](evidence/deployment-names-dev-2026-11-06.json).

## SLS-020

Statut : [~] — contrôle et console initiale déployés ; qualification en cours.
Reste à faire : [SLS-089](#sls-089).

API Python/SQLite avec migrations, SSO admin réel, sessions/CSRF, CRUD des
namespaces/services/fonctions et tokens. E2E : persistance après redémarrage,
matrice de permissions, restriction interservice/fonction, expiration,
révocation, renouvellement et refus SSO. Références : PLATFORM organisation
et identité ; [schéma](SCHEMA.md) et [API du contrôle](CONTROL.md).
La tranche de console associée expose ces objets et le parcours SSO dès cette
unité ; SLS-060 complète ses facettes d'exécution et la campagne transversale.
Les parcours publics, l'accueil navigateur, la provenance réseau et les
limites de connexion sont éprouvés. La [preuve de gestion authentifiée](evidence/control-management-dev-2026-11-06.json)
recoupe 19 groupes API, 11 parcours UI et huit groupes publics sur l'image
déployée. Nettoyages confirmés, sept captures relues. Le nom maximal du fil
d’Ariane mobile revient à la ligne et les trois gestes de fermeture du menu
rendent le focus au bon contrôle, y compris après passage au desktop.
Le [checkpoint du 6 novembre](evidence/control-dev-checkpoint-2026-11-06.json)
regroupe six groupes HTTP, neuf contrôles navigateur, quatre chemins réseau,
six scénarios de limite par client, deux de capacité globale et dix-sept
de panne/reprise. Deux contrôles supplémentaires éprouvent l'interruption
du pilote de preuve. Les dépendances verrouillées sont auditées.

La revue du contrat OIDC du client créé précise les travaux SLS-020 restants :
état d'attente distinct d'une erreur technique pour verified/admin manquant,
contrôle de l'azp de l'ID token en complément de son audience, et réponse
temporaire préservant la session lorsqu'un nouveau kid arrive dans la fenêtre
anti-refresh JWKS de deux secondes. Les comptes réels et une rotation réelle
maîtrisée sont nécessaires aux preuves correspondantes ; aucune n'est déclarée
réussie. La durée de 300 secondes se mesure sur le jeton réellement émis.

## SLS-030

Statut : [~] — publication API/CLI, plafonds de candidats/révisions et deux reprises après SIGKILL qualifiés ; interface livrée par SLS-063.
Reste à faire : [SLS-090](#sls-090) (pannes de publication) et [SLS-080](#sls-080)
(compatibilité du projet de référence).

Packaging YAML, héritage, upload immuable, secrets chiffrés, validation du
handler, CJS/ESM et dépendances réelles. E2E : déployer le service témoin par
l'adaptateur, rejeter archives invalides, mettre à jour/rollback en préservant
l'identifiant. Référence : PLATFORM adaptateur et [DEPLOYMENT](DEPLOYMENT.md).
La compatibilité du projet de référence reste à établir explicitement : audit
en lecture seule du manifeste, des contrats de handlers, dépendances, événements,
variables et secrets ; matrice des comportements pris en charge, adaptations
nécessaires et écarts bloquants. Reproduire ces contrats avec des fixtures
originales du dépôt et les déployer/invoquer réellement sur la plateforme.
L’audit et la matrice sont faits (10 novembre) ; les fixtures et leurs preuves
E2E relèvent de [SLS-080](#sls-080).
La preuve identifie les adaptations nécessaires au client, dont le jeton
d’invocation ; les résultats du banc seuls ne valent pas compatibilité complète.
La déduplication des uploads, le hash public, la publication sans activation
et les résultats de version relèvent de l’extension SLS-074.
La session SSO réelle est disponible pour les preuves d'upload et de publication.
Le [checkpoint CLI](evidence/adapter-package-dev-2026-11-06.json) comporte
24 scénarios réels réussis dans Docker sur le SPARK, avec source et images
identifiées. Le [checkpoint du chargeur](evidence/runtime-validation-dev-2026-11-06.json)
ajoute 36 scénarios réels : formats CJS/ESM, dépendances, confinement, logs,
échéance extérieure, protocole Unix et destruction des descendants.
Le [checkpoint d'extraction](evidence/artifacts-dev-2026-11-06.json) ajoute
112 contrôles réels : formats et refus, limites exactes, disque saturé,
courses sur les chemins et la source, puis packaging/extraction/chargement
Node des douze fonctions. Le [checkpoint du contrôle de publication](evidence/deployment-control-dev-2026-11-06.json)
intègre les routes de préparation, upload, historique, rollback et suppression,
la migration 003, le budget et la reprise. Huit groupes publics et trente
contrôles réels de configuration/démarrage/panne passent sur l'image déployée.
La [preuve authentifiée](evidence/deployment-authenticated-dev-2026-11-06.json)
recoupe onze groupes API et sept groupes CLI : droits, refus, import et logs
expurgés, révocation/conflits pendant validation, admission unique, rollback,
suppression de révisions inactives et huit candidats par fonction. Les 35
archives conservées des campagnes sont vérifiées sur disque ; aucun objet
actif, candidat non terminal, réservation, canal ou conteneur de validation
ne subsiste à ce checkpoint. La [preuve de reprise](evidence/publication-recovery-dev-2026-11-06.json)
ajoute quatre groupes : 64 candidats globaux, vingt révisions, SIGKILL pendant
réception partielle puis pendant validation Docker vivante. Les candidats
interrompus échouent sans publication, les configurations et archives
précédentes sont intactes, les ressources sont libérées et de nouveaux uploads
réussissent. Les 53 archives antérieures et vingt nouvelles archives conservées
sont recoupées. Expiration, budget/marge disque, déconnexion concurrente et
arrêt pendant nettoyage restent à qualifier.
La commande deploy est désormais implémentée : sa [preuve ciblée](evidence/adapter-deploy-dev-2026-11-06.json)
conserve 14 contrôles de prérequis et de refus HTTPS réel, plus les 24 scénarios
plan/package rejoués. Les sept groupes CLI authentifiés réussissent onze
premières publications, la pagination, les mises à jour à UUID conservé,
les refus de droits, le résultat partiel et la reprise du même brouillon.
Rupture après envoi, modification locale concurrente, réponse trop grande et
redirection restent à éprouver. Les vues de révisions sont livrées et vérifiées par SLS-063. Le moteur est déployé ; son exécution après rollback est vérifiée dans
la [campagne publique](evidence/execution-dev-2026-11-06.json).

## SLS-040

Statut : [~] — admissions publiques et reprises éprouvées ; vues de consultation livrées par SLS-061.
Reste à faire : [SLS-091](#sls-091).

Invocation authentifiée, limites réelles, admission atomique, min/max/idle,
deadline, descendants, drainage et réconciliation. CORS/IP ET/OU côté backend.
E2E : succès/refus, saturation, mémoire/CPU/PIDs, délais, extinction/reprise,
authentification métier, chaînes proxy, crash du contrôle et absence de rejeu.
Références : PLATFORM origines et exécution, [EXECUTION](EXECUTION.md).
L’invocation d’une version par hash, ses admissions, pools et budgets partagés
avec la cible courante sont détaillés dans SLS-074.
La tranche initiale fournit le superviseur chaud, son enfant neuf et le pilote
Docker réel. Les campagnes d’invocation et de courses de cycle sont présentes,
avec régression du chargeur partagé : 31 + 11 + 36 contrôles réels réussis,
zéro échec et zéro test ignoré. La [preuve](evidence/instances-dev-2026-11-06.json)
est conservée séparément des parcours API. Le pilote est maintenant raccordé
aux baux de l’agent FUSE, avec quatorze groupes réels. Les admissions, min/max/idle, générations et invocations authentifiées sont
intégrées et déployées sur DEV. La [preuve du moteur](evidence/execution-dev-2026-11-06.json)
recoupe 31 groupes HTTPS et 221 groupes de régression, avec zéro échec/skip
dans la suite finale : budgets CPU/RAM/instances, 128 réceptions, générations,
déconnexions, contention SQLite, SIGKILL et arrêt gracieux sans rejeu.
Les scénarios échoués pendant le développement restent conservés séparément.
La rétention à sept jours/10 000 observations et les chemins résiduels de
nettoyage/reprise doivent encore recevoir leurs preuves ciblées. Les vues
d’exécution sont livrées et vérifiées par SLS-061.

## SLS-050

Statut : [~] — agent local installé en DEV ; raccordements et reprises principaux qualifiés.
Reste à faire : [SLS-092](#sls-092) (acquisition partielle, marge physique, registre).
Les crons de SLS-078 sont clos par la campagne complète du 22 novembre.

Volumes par ID, quotas et modes, archive/purge, crons UTC, logs bornés et
métriques. E2E : concurrence, saturation disque, cache, déploiement/rollback,
redémarrage, cron réellement déclenché et diagnostic autorisé/refusé.
Références : PLATFORM stockage et exploitation, [STORAGE_AGENT](STORAGE_AGENT.md).
Les futurs crons suivent uniquement la cible courante de SLS-074 ; publier
une version pilote sans l’activer ne double pas les déclenchements.
Le registre durable, les baux et la supervision FUSE sont implémentés. Quinze
groupes de cycle, huit de limites et les 31 contrôles du proxy passent, avec
nettoyage confirmé, zéro échec et zéro skip. La [preuve recoupée](evidence/storage-agent-dev-2026-11-06.json)
est complétée par quatorze groupes de raccordement au pilote d’instances :
[preuve](evidence/managed-storage-dev-2026-11-06.json). Les créations, modifications
de quotas, suppressions et publications sont raccordées à une décision SQL durable
(migration 004). Treize groupes HTTPS et une preuve ciblée du pilote couvrent les reprises avant/après commit,
la révocation, les fichiers réels, la publication et le rollback. Le protocole
de l’agent compte douze groupes avec la neutralisation d’un prepare retardé.
La [preuve du raccordement](evidence/function-storage-dev-2026-11-06.json)
recoupe aussi les régressions et la console. Les admissions et observations API sont éprouvées par les 31 groupes publics
de la [preuve du moteur](evidence/execution-dev-2026-11-06.json). Les
commandes publiques de purge/cache et leurs vues de console sont déployées
et qualifiées dans SLS-065. Les crons sont portés par [SLS-078](#sls-078) et les
jobs de console par [SLS-081](#sls-081). Le moteur est qualifié par les 543 groupes
réels de SLS-078 ; les jobs de console restent absents.
Les quotas préparés et leurs reçus sont
implémentés ; la preuve initiale de dix groupes vérifie décisions, réservations, SIGKILL pendant
préparation et reprise d'abandon partiel avec conservation des données.
La [preuve recoupée](evidence/storage-preparations-dev-2026-11-06.json) ajoute
37 groupes de régression, avec nettoyages confirmés, zéro échec et zéro skip.
L'acquisition partielle après interruption, la marge physique et les pannes de registre
restent à qualifier ; aucune clôture de SLS-050 ne repose sur ces seuls composants.

## SLS-060

Statut : [~] — gestion, exécutions, manuel, publication et purge/cache présents.
Reste à faire : [SLS-068](#sls-068) à [SLS-073](#sls-073),
[SLS-081](#sls-081) et la campagne de [SLS-095](#sls-095).

Parcours d'administration sur les API réelles : connexion, objets, jetons,
code, variables/secrets, limites, état, stockage, historique et journaux.
Lire et appliquer les deux design systems avant implémentation. Tester depuis
l'accueil, clavier/souris, états vides/erreurs/données longues et mobile ;
inspecter les captures. Exécuter la campagne complète, mettre à jour manuel,
notes SPARK, installation/reprise, preuves et backlog. Zéro échec et zéro skip.
Les demandes de recherche, favoris, actions en masse, édition du code, client
HTTP et observabilité sont spécifiées dans [CONSOLE_USABILITY](CONSOLE_USABILITY.md)
et découpées dans SLS-067 à SLS-073.
Le versionnement par hash, les appels épinglés et le pilote de versions sont
définis dans SLS-074 ; ils complètent les révisions et le rollback déjà livrés.

## SLS-061

Statut : [x] — facettes déployées ; 40 groupes réels réussis, zéro échec/skip,
25 captures relues, sources et image recoupées, nettoyages confirmés.
[Preuve](evidence/console-execution-dev-2026-11-07.json).

Tranche bornée de SLS-060 : [contrat de consultation](CONSOLE_EXECUTION.md).
Facettes de la fonction, mesures distinctes des allocations, pagination réelle,
états et journaux expurgés, focus, mobile, erreur/reprise et preuves de console.
La publication depuis l’UI, purge/cache et crons appartiennent aux autres tranches.

## SLS-062

Statut : [x] — manuel intégré et maintenu depuis sa source unique ; 48 groupes
réels réussis, zéro échec/skip, 33 captures relues.
[Preuve](evidence/manual-console-dev-2026-11-07.json).

[Contrat du manuel intégré](CONSOLE_MANUAL.md). Source éditoriale unique,
construction automatique, entrée de navigation, sommaire et ancres accessibles,
guide autonome, rendu responsive et preuve E2E de concordance avec le document.

## SLS-063

Statut : [x] — publication depuis la console déployée et vérifiée : 18 campagnes,
312 groupes réels, zéro échec/skip, 54 captures inspectées, sources et image
recoupées, nettoyages confirmés et notes SPARK appliquées.
[Preuve](evidence/publication-console-dev-2026-11-07.json).

[Publication dans la console](CONSOLE_PUBLICATION.md). ZIP et handler avec
conservation serveur de la configuration, suivi corrélé et abandon des candidats
préparés, historique, activation et suppression des révisions. Parcours UI réels,
droits et conflits, invocation après activation, réponses perdues, reprises de
nettoyage physique et de confirmation du stockage, candidat étranger et longs
journaux. Les deux incohérences de lecture découvertes à la première revue sont
corrigées puis requalifiées ; le registre est résolu. Le manuel et les notes
SPARK décrivent les parcours livrés. Les preuves résiduelles des unités parentes
restent ouvertes.
L’identification publique par hash, la déduplication et le pilote sans activation
ne font pas partie de cette preuve historique ; ils sont suivis dans SLS-074.

## SLS-064

Statut : [x] — paquet installé et migration 004 vérifiée ; sept campagnes,
106 groupes réels, zéro échec/skip, reprises et nettoyage recoupés.
[Preuve](evidence/storage-discard-dev-2026-11-07.json).

[Effacement corrélé](STORAGE_DISCARD.md) : reçus de vidage/purge, versions et
propriétaire, réponse perdue, erreur physique et interruption ; suppression
hors verrou global. Migration 004 agent, installation DEV et preuves réelles.

## SLS-065

Statut : [x] — déployé et qualifié en DEV ; replay complet, complément API,
captures, nettoyages, trois notes proposées et revue finale recoupés.

Catalogue consultable après suppression des parents, purge administrateur
confirmée, vidage sous droit Update, drainage et relecture des droits/versions
avant décision durable. API, console et manuel sont déployés avec la migration
006 et le protocole agent 004. Contrat : [CONSOLE_STORAGE](CONSOLE_STORAGE.md).

La [preuve complète](evidence/storage-console-dev-2026-11-08.json) réunit
29 campagnes et 397 groupes réels en série, sans échec/skip, puis un complément
distinct de neuf groupes API. Celui-ci couvre quatorze corps invalides de purge,
une ancienne version positive réellement lue avec UUID neuf et nom exact, les
refus du helper de lecture et l’égalité des fichiers, configurations, versions,
commandes, gardes, reçus et audit de purge avant/après. Ses assertions ne sont
pas attribuées rétroactivement aux 397 groupes.

Les 24 fonctions de six namespaces du replay et les quatre de deux namespaces
du complément sont purgées et recoupées physiquement ; ressources et allocations
globales libérées. Les deux fenêtres historiques restaurent les tables, fichiers,
identités et services originaux. La purge contradictoire de leur installation
temporaire reste volontairement en attente : elle ne devient pas une purge
métier réussie par le retrait de cette installation.

La pagination crée onze brouillons depuis l’UI, les archive et recoupe dix UUID
propres sur deux pages après coupure réseau. Le runner prépare une paire SSO au
début puis une autre juste avant la décision, sans changer les durées SSO.
Quatre prérequis restent hors du compte des groupes. Les 173 sources sont liées
avant/après chaque phase, avec deux sources E2E renforcées pour le complément ;
les 25 fichiers du contrôle embarqué et la même image sont recoupés. Les deux
mises à jour documentaires finales de statut sont distinguées des sources testées.

Les 72 captures sont recoupées : 55 nouvelles images observées et 17 images
régénérées identiques à celles déjà inspectées. Le manuel correspond à ses
treize chapitres et 39 paragraphes. Les trois notes SPARK sont proposées et
recoupées ; leur adoption n’est pas annoncée.

Checkpoints conservés : [initial](evidence/storage-console-checkpoint-dev-2026-11-07.json),
[commandes sous panne](evidence/storage-command-recovery-dev-2026-11-07.json),
[validation vivante](evidence/storage-validation-recovery-dev-2026-11-07.json),
[décisions](evidence/storage-decision-recovery-dev-2026-11-07.json),
[correctif historique](evidence/storage-legacy-recovery-dev-2026-11-07.json),
[intégration ciblée](evidence/storage-console-focused-dev-2026-11-08.json) et
[premier replay arrêté sur prérequis SSO](evidence/storage-console-incomplete-dev-2026-11-08.json).
SLS-064 seul ne qualifie aucun parcours public d’effacement.


<a id="sls-031"></a>
## SLS-031 — Préserver la configuration commune du service au déploiement

Statut : [x] — déployé et qualifié, y compris l’issue inconnue sous vraie coupure.

L’adaptateur conserve les valeurs communes du provider dans le service et
uniquement les surcharges dans les fonctions. Le rapport distingue les deux
étapes. L’API remplace explicitement un jeu de secrets et contrôle les
configurations effectives avant mutation ; la CLI borne les fusions connues,
y compris leur représentation Unicode au runtime. Contrat :
[SERVICE_CONFIGURATION_URLS](SERVICE_CONFIGURATION_URLS.md).
La [preuve](evidence/service-configuration-dev-2026-11-08.json) recoupe treize
groupes ciblés : héritage, surcharges, rotation pendant appel admis, droits,
échec partiel, reprise d’un ancien déploiement aplati, limites et redémarrage.
Les régressions portent le total à 191 groupes sur douze campagnes en série ;
24 groupes plan/package et quatorze de refus public sont rejoués dans Docker.
Zéro échec/skip, 165 sources recoupées, 25 fichiers embarqués du contrôle et cinq
de la CLI conformes. Les deux fonctions ciblées et onze répertoires d’artefacts
sont purgés, sans réservation ou conteneur résiduel. Le manuel affiche ses
39 paragraphes ; les 21 captures de gestion et de lecture sont inspectées.
Le [complément de transport](evidence/service-configuration-transport-dev-2026-11-08.json)
ajoute cinq groupes natifs : garde indépendante, coupure avant traitement et après
commit, puis deux relances explicites avec publication et invocation Docker.
La vraie CLI rend `unknown` et ne tente que les trois connexions HTTPS attendues,
sans rejeu ni fonction/candidat créé. Les treize groupes de configuration sont
ensuite rejoués. Ces dix-huit groupes passent sans échec/skip sur la même image,
avec 167 sources identiques avant/après ; aucune source produit du checkpoint
de 191 groupes n’a changé. Le recoupement physique couvre les quatre fonctions,
treize artefacts absents et les réservations à zéro ; les trois gardes sont inactives.
Les deux preuves conservent leurs index historiques distincts. Le
[banc](SERVICE_CONFIGURATION_URLS.md#preuve-de-transport) ne couvre ni une panne
de la FORGE ni les autres scénarios résiduels de SLS-030.

<a id="sls-066"></a>
## SLS-066 — Afficher les URL d’appel issues des domaines du SPARK

Statut : [~] — catalogue, console et résultat CLI déployés en DEV ; régression
complète de 35 campagnes / 467 groupes réussie, qualification multi-domaines faite.
Reste à faire : [SLS-093](#sls-093).

La source refusée suit le [contrat de permissions réelles](INVOCATION_SOURCE_PERMISSIONS.md) :
précontrôle natif positif, chmod du seul fichier officiel sans édition du
contenu, programme figé de restauration et garde systemd avant toute faute.
Trois preuves sérialisées de garde (release, SIGKILL, SIGSTOP) précèdent les refus
API/UI. Chmod modifie ctime, qui reste une observation ; aucune identité
concurrente n’est adoptée. La [garde est qualifiée](evidence/invocation-source-guard-dev-2026-11-09.json) :
trois groupes réels passent sur 210 sources, avec errno 13, signaux noyau observés,
mode/lecture/santé restitués et trois helpers/timers/services terminés. Le
[complément API](evidence/invocation-source-api-dev-2026-11-09.json) passe quatre
groupes sur 211 sources : source_forbidden pour Read/admin, six refus sans
diagnostic, quatre appels Docker dont deux pendant EACCES, catalogue initial
restitué. Fonction purgée et garde terminée recoupées nativement. Le
[parcours UI](evidence/invocation-source-ui-dev-2026-11-09.json) passe trois
groupes sur 212 sources : création/publication depuis l’accueil, refus rendu
desktop/mobile sans anciennes adresses/copies/succès, restitution et invocation
de l’URL copiée. Une fonction purgée et garde terminée recoupées nativement.
Les pages UI/CLI sur six domaines sont qualifiées par le complément ci-dessous ;
les autres fautes de source restent ouvertes.

Découvrir les routes effectivement affectées à la passerelle dans le SPARK,
calculer les adresses par fonction et événement HTTP, les afficher et les
rendre copiables dans la console ainsi que dans le résultat de déploiement.
Distinguer les domaines d’invocation du domaine SSO canonique. Contrat, limites
d’infrastructure et preuves E2E :
[SERVICE_CONFIGURATION_URLS](SERVICE_CONFIGURATION_URLS.md) et
[INVOCATION_URLS](INVOCATION_URLS.md). Le [checkpoint DEV](evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
réunit huit groupes API/CLI, six UI, 36 régressions et 38 groupes CLI Docker,
avec 31 captures recoupées.
Le manuel de ce checkpoint comporte 14 chapitres et 43 paragraphes ; le guide
courant qualifié par SLS-067 en comporte quinze et 46. Les preuves multi-domaines,
retrait et absence exigent les vraies routes et l’autorité bornée du SPARK ;
aucune substitution du registre n’est admise. Restent également les sources
perturbées. La consultation CLI refusée par révocation 401 est qualifiée
ci-dessous. Le manuel
est reconstruit et qualifié pour les parcours actuellement éprouvés.

L’autorisation bornée de gestion des routes du seul SPARK depuis sa console
normale est confirmée le 8 novembre 2026 : alias functions.lelabs.tech, deux
routes vers 18091 temporairement, garde et restauration à 18090. Le périmètre
est inscrit dans CLAUDE_PROJECT ; l’alias est appliqué et les cinq cycles réels
ci-dessous qualifient retrait, détours et restauration.

SLS-067 est clôturée. La reprise commence par le DNS exact et la route TLS de
l’alias autorisé via la console normale, puis les huit groupes API/CLI et six UI
sur les deux domaines. Le [contrat opératoire](INVOCATION_URLS.md#console-normale-et-mise-en-service-de-lalias-autorisé)
sépare cette mise en service des perturbations et de leur garde à éprouver.
Le DNS exact et l’alias sont maintenant appliqués ; les deux HTTPS et la
projection lisible depuis le contrôle sont vérifiés. Les huit groupes API/CLI
et six UI passent, avec quatre fonctions purgées dans deux namespaces.
La [preuve à deux domaines](evidence/invocation-domains-dev-2026-11-08.json)
conserve ses arrêts initiaux et la reprise sans mutation ; elle ne clôture
pas les critères résiduels de SLS-066.
Les cinq cycles suivent le [contrat de garde et cycles](INVOCATION_URLS.md#garde-de-restauration-et-cycles-autorisés) :
garde sans perturbation, mort du pilote après détour d’alias confirmé,
retrait/rétablissement puis deux ports détournés et catalogue vide local réel.
Le vide UI public exige ensuite sa propre pause/libération native, distincte
du pilote historique de destruction ; ses trois groupes UI sont qualifiés ci-dessous.

Les trois déclencheurs de garde sans perturbation sont vérifiés : restauration
explicite, SIGKILL réel du pilote avec restauration indépendante et échéance
avec pilote vivant, deux HTTPS et fin confirmée dans chaque cas. La
[preuve positive](evidence/invocation-route-guard-dev-2026-11-08.json) conserve
trois groupes sur 201 sources. Le premier
[checkpoint incomplet](evidence/invocation-route-guard-checkpoint-dev-2026-11-08.json)
garde ses deux réussites, l’arrêt HTTPS de l’échéance et le diagnostic séparément.
Le cache négatif a expiré et la résolution native s’est rétablie ; aucune adresse
ni aucun résolveur n’est forcé. Ces trois groupes précèdent les perturbations ;
les deux routes sont également revenues à 18090 après les cinq cycles suivants.
Le [contrat des cinq cycles réels](INVOCATION_ROUTE_CYCLES.md) fixe maintenant
la fixture originale, pagination API à deux domaines, détour d’alias avec reprise
explicite puis perte du pilote, retrait/rétablissement et détour des deux ports
avec catalogue vide local réel. Les cinq groupes passent ; sept appels Docker,
quatre gardes terminées et une fonction purgée dans un namespace sont recoupés.
La [preuve](evidence/invocation-route-cycles-dev-2026-11-09.json) conserve les
sources, les fichiers natifs exacts et l’arrêt initial du collecteur sur les
seuls horodatages arrondis par JavaScript. La revue finale en lecture seule
ne constate aucun défaut bloquant. Ce checkpoint est qualifié ; SLS-066 reste ouverte.

Pour les pages UI/CLI de cinq domaines, le responsable autorise explicitement
le9 novembre2026 les quatre alias temporaires functions-pagination-1 à
functions-pagination-4.lelabs.tech sur le seul infra-serverless :18090TLS,
A exacts vers51.158.54.202 TTL300, puis retrait de ces seuls objets créés.
Le [plan appliqué](INVOCATION_DOMAINS_PAGINATION.md) et CLAUDE_PROJECT portent
ce périmètre. La [preuve six domaines](evidence/invocation-pagination-dev-2026-11-09.json)
passe huit groupes : deux de cycle, trois UI et trois CLI ; trois prérequis
sans objets restent distincts. Les253 sources et images sont figées, les14
invocations et deux purges physiques recoupées, les sept captures inspectées.
Les quatre routes/A sont retirés indépendamment après SIGKILL réel du
propriétaire ; les deux configurations permanentes et leurs HTTPS restent
identiques. La CLI parcourt deux pages et conserve son succès après vrai401
ou changement réel entre pages, sans adresses partielles ni rejeu.
Le premier essai A1 s’arrête avant toute route/UI/CLI ; le principal retire ce
seul A et confirme l’absence des objets temporaires. Le relevé de transition
DNS est corrigé, sans relâcher les identités. Cet essai et les deux époques
antérieures de garde restent exclus du total. Les branches de perte de réponse,
verrou suspendu et panne durable de console ne sont pas déclarées qualifiées.
Pendant l’attente antérieure, les [preuves de pause/libération natives](INVOCATION_URLS.md#barrière-native-de-pause-et-libération)
sont préparées sur la requête canonique, sans changer de route. L’extraction de
NativeObserver est vérifiée par ses neuf régressions réelles : 201 sources,
six fonctions purgées dans deux namespaces et six gardes terminées.
[Preuve du module commun](evidence/invocation-native-observer-dev-2026-11-08.json).
La pause/libération puis le SIGKILL du traceur et la reprise indépendante de
la vraie requête passent maintenant leurs deux groupes réels, sur 205 sources.
La [preuve](evidence/invocation-request-pause-dev-2026-11-09.json) conserve le
premier essai arrêté au désarmement et son diagnostic séparé ; le replay corrige
la reconnaissance native du timer absent. Deux fonctions sont purgées dans deux
namespaces et les quatre gardes sont terminées, contrôle inchangé et non tracé.
La survie de la connexion UI pendant réapplication Caddy passe les trois groupes
suivants ; les erreurs propres du pilote restent à qualifier.
Le [parcours public suivant](INVOCATION_URLS.md#parcours-public-du-catalogue-vide-sous-vraies-routes)
fixe ses trois groupes : création/publication UI, GET retenu et vrai affichage
vide sous deux routes détournées, puis restauration/actualisation et invocation
de l’URL copiée. Les trois groupes passent sur 206 sources et les mêmes images ;
une fonction est purgée dans son namespace et les deux gardes sont terminées.
La [preuve](evidence/invocation-empty-ui-dev-2026-11-09.json) recoupe le vrai
200/total zéro, les cinq captures et la restauration, avec revue finale.
La prochaine preuve suit [l’entrée publique de l’alias](INVOCATION_URLS.md#entrée-publique-de-lalias-et-sso-réel) :
redirections HTTPS et absence de cookie sur l’alias, puis véritables connexions
et déconnexions UI desktop/mobile depuis son accueil. Trois groupes et six
captures passent maintenant sur 207 sources dans le
[replay qualifié](evidence/invocation-alias-entry-dev-2026-11-09.json), sans changement
de routes. Les six JPEG sont inspectés ; deux sessions/flows du replay et deux
autres des essais arrêtés sont recoupés fermés, distinctement.
Le premier essai atteint la console après SSO puis s’arrête à la vérification
de déconnexion desktop ; sa session et son flow sont recoupés fermés. Conserver
l’essai incomplet et préciser le diagnostic sans exposer les messages de saisie.
Le diagnostic distinct confirme HTTP 200 puis corps indisponible à la lecture
tardive après navigation. Les deux essais arrêtés sont conservés. Le même POST réel est désormais lu par
CDP durable, avec signed_out/sso_signed_out vrais et toutes les assertions de
déconnexion conservées. Les erreurs propres de ce client restent à éprouver.

La [suite `invocation-urls`](evidence/invocation-urls-regressions-dev-2026-11-08.json)
passe 35 campagnes / 467 groupes, zéro échec/skip, avec six prérequis non comptés,
186 sources et les images contrôle/CLI recoupées avant/après chaque phase.
Les 32 fonctions suivies sont purgées dans dix namespaces ; les deux restaurations
historiques sont distinctes. Les 79 captures fraîches sont recoupées : 61
observations et 18 identités SHA avec une référence inspectée. Le premier replay
des pannes est arrêté après 51 groupes à cause d’un client suivant la redirection
canonique ; sa correction et la preuve native du Host sont définies dans
INVOCATION_URLS. Le client de panne corrigé passe 55 groupes ; les huit groupes API
passent avec le vrai Host en boucle locale, puis dans la suite complète.
Les compléments qualifient les routes publiques, leur état vide UI et l’entrée
SSO depuis l’alias. Les six domaines ont leur preuve distincte ci-dessus.
Restent les autres fautes de source et la branche
d’expiration/perte SSH du build borné, dont seul le parcours nominal est qualifié.

Le [complément de transport](evidence/invocation-url-transport-dev-2026-11-08.json)
passe trois groupes de transport du catalogue, avec perte
de l’observateur, coupure du GET après réception puis avant émission, publication
durable conservée, six connexions CLI sans rejeu et invocation Docker après
reprise. Contrat : [perte native](INVOCATION_URLS.md#perte-native-du-catalogue-après-publication-cli).
Les cinq groupes de transport historique et huit API/CLI repassent ensuite :
16 groupes au total, 187 sources et images liées avant/après chaque phase,
huit fonctions purgées dans trois namespaces, six gardes terminées et 26 fichiers
embarqués recoupés. Les vrais 502 ne changent pas le succès de publication.
Le refus reste distinct de ces coupures ; le vrai 401 est qualifié ci-dessous.
Les branches
d’expiration/sortie excessive/lancement et nettoyage après réponses perdues
du nouveau client ne sont pas déclarées acquises.

Le [complément de révocation](evidence/invocation-url-refusal-dev-2026-11-08.json)
ajoute le quatrième groupe de transport :
CLI retenue nativement avant sa sixième connexion, publication durable vérifiée,
révocation API du jeton puis vrai GET 401 sans requalification ni rejeu.
Contrat : [révocation avant GET](INVOCATION_URLS.md#révocation-avant-le-get-facultatif).
Le replay passe 4 + 5 + 8 = 17 groupes, sans échec/skip, avec 188 sources/images
stables et neuf fonctions purgées dans trois namespaces ; six gardes et 26
fichiers embarqués recoupés. Le premier essai incomplet reste séparé, cause
de barrière inconnue, deux fonctions et deux gardes nettoyées. Le refus 403
et les pannes propres du pilote/diagnostic ne sont pas revendiqués.

<a id="sls-067"></a>
## SLS-067 — Catalogue de fonctions et recherche globale

Statut : [x] — API/console déployées et qualifiées ; 37 campagnes uniques /
489 groupes réussis en deux époques contrôlées, recoupements physiques,
documentation et revue finale terminés.

Catalogue global, recherche serveur, filtres namespace/service/état, tri,
pagination et contexte conservé dans l’URL. Le [contrat](FUNCTION_CATALOGUE.md)
et la [preuve](evidence/function-catalogue-dev-2026-11-08.json) couvrent les
API administrateur, le nouvel accueil et les retours depuis les six facettes.
Recherche globale, Unicode/UUID/handler, filtres combinés, homonymes et tris
stables, refus, vraie latence réseau, erreurs de saisie corrigées, historique,
rechargement, suppressions et recalage, clavier/mobile sont éprouvés.

La qualification retient 30 campagnes aux clients inchangés (447 groupes) et
sept réexécutées (42), soit 37 uniques / 489 groupes, sans échec/skip dans cet
ensemble. Six prérequis sont distincts. Les époques 196/197 et mêmes images
produit/CLI sont recoupées ; les deux arrêts précédents et l’ancien résultat
positif remplacé restent séparés, sans succès rétroactif. Le
[correctif du client privé](evidence/private-channel-lifecycle-dev-2026-11-08.json)
garde sa propre preuve de onze groupes.

Les 98 captures sont inspectées, dont les trois positions de table à 390 px et
le dialog plein viewport. Le guide compilé compte 15 chapitres et 46 paragraphes.
91 fonctions suivies purgées dans 23 namespaces, quinze jeux variables/secrets
de services vidés et restaurations historiques sont recoupés. Les 39 fonctions
des jeux écartés ont leur relevé séparé. Sources produit, référence et configuration
officielle inchangées ; 27 fichiers embarqués et quatre fichiers web HTTPS
correspondent à l’image. La remarque de titre d’archive après purge est suivie
dans SLS-075. SLS-066 conserve ses preuves indépendantes.

<a id="sls-068"></a>
## SLS-068 — Favoris personnels persistants

Statut : [ ] — contrat défini, rien d'implémenté (aucune route, table ni écran).
Nature : Développer. Dépend de : SLS-067. Ordre : 6.
Contrat : [favoris](CONSOLE_USABILITY.md#favoris-personnels).

Résultat attendu : une personne épingle et ordonne namespaces, services et fonctions ;
ses favoris la suivent entre appareils.

Critères d'acceptation :

- [ ] SLS-068.1 Table et migration versionnée : favori = identité SSO stable + type + UUID de
  l'objet + rang ; unicité par personne et objet ; suppression en cascade avec l'objet.
- [ ] SLS-068.2 API : lister, ajouter, retirer, réordonner (atomique) ; les favoris ne
  portent que des UUID, donc suivent un renommage.
- [ ] SLS-068.3 Un objet supprimé ou devenu inaccessible apparaît « indisponible » sans
  nom ni détail pour une identité qui n'y a plus droit ; la personne peut retirer la
  référence.
- [ ] SLS-068.4 Les jetons techniques de service ne lisent ni ne modifient les favoris
  d'un administrateur.
- [ ] SLS-068.5 Interface : étoile sur liste et fiche, section « Favoris » dans la navigation,
  réordonnancement au clavier et à la souris, états vide, erreur, long nom, mobile.

Tests exigés :

- Unitaires : ordre, unicité, réordonnancement, projection d'un objet indisponible.
- API / intégration : isolation entre deux comptes réels, droits par requête directe,
  concurrence de deux réordonnancements, persistance après redémarrage du contrôle.
- E2E depuis l'accueil réel : deux sessions du même compte voient les mêmes favoris,
  deux comptes ne se voient pas, renommage, suppression et retrait d'accès d'un objet
  favori, parcours clavier et mobile, captures inspectées.

À mettre à jour : `SCHEMA.md`, seed (favoris de démonstration par profil), manuel,
`DESIGN_SYSTEM_APP.md`, parité sans objet (ergonomie du produit), `CHANGELOG.md`.

<a id="sls-069"></a>
## SLS-069 — Renommage et suppression en masse

Statut : [ ] — contrat défini, actions individuelles seulement aujourd'hui.
Nature : Développer. Dépend de : SLS-067, SLS-074. Ordre : 6.
Contrat : [opérations en masse](CONSOLE_USABILITY.md#opérations-en-masse).

Résultat attendu : sélectionner explicitement des fonctions, services ou namespaces,
prévisualiser, puis renommer ou supprimer en lot avec un résultat suivi par objet.

Critères d'acceptation :

- [ ] SLS-069.1 Sélection par type d'objet, page ou éléments explicites, au plus 256 UUID
  avec leurs versions ; une nouvelle recherche n'étend jamais la sélection.
- [ ] SLS-069.2 Renommage : préfixe, suffixe, remplacement de texte, correction
  individuelle ; aperçu ancien/nouveau nom ; validation serveur des droits, des
  versions, de la grammaire et des collisions (échanges de noms compris) ; lot atomique.
- [ ] SLS-069.3 UUID, volumes, jetons, historiques et révisions conservés ; appels admis
  inchangés, appels suivants sur le nouveau nom.
- [ ] SLS-069.4 Export de manifeste après renommage avec `p2enjoy.function_id`
  (adaptateur : UUID résolu avant le nom, appartenance au service vérifiée) ; un nouveau
  déploiement du manifeste exporté conserve UUID et volumes.
- [ ] SLS-069.5 Suppression : effets présentés avant confirmation ; fonction = archivage
  (la purge reste une action administrateur distincte) ; parents occupés soumis à leurs
  règles ; état par objet (terminé, refusé, en attente, interrompu), consultable après
  rechargement.
- [ ] SLS-069.6 Reprise d'une opération corrélée après réponse perdue ou SIGKILL : aucune
  suppression appliquée deux fois, aucun objet ressuscité après échec partiel.

Tests exigés :

- Unitaires : grammaire, collisions, échanges, limite de 256, calcul d'aperçu.
- API / intégration : version obsolète (409), droits par requête directe, fonctions
  occupées, parents non vides, résultat partiel, idempotence de reprise.
- E2E depuis l'accueil réel : sélection multi-pages, collisions, résultat partiel,
  SIGKILL pendant le lot, redéploiement du manifeste exporté, état physique des
  volumes et du code, captures desktop et mobile.

À mettre à jour : `SCHEMA.md` et migration (opérations de lot), contrat de l'adaptateur
(`p2enjoy.function_id`) dans `DEPLOYMENT.md`, seed, manuel, `DESIGN_SYSTEM_APP.md`.

<a id="sls-070"></a>
## SLS-070 — Édition du code et du handler dans la console

Statut : [x] — les [29groupes de reprise](evidence/code-editor-control-interruption-dev-2026-11-22.json) clôturent070.3/.5 après
[rapprochement des critères](CONSOLE_EDITOR.md#persistance-et-publication-qualifiées-par-rapprochement),
avec26captures inspectées, six handlers, deux coupures137 et purge physique.
070.2 est clôturé par les [32 groupes des droits de source](evidence/code-editor-source-access-dev-2026-11-13.json)
et les droits pendant IO de la preuve30, sans réaddition.070.1 est clôturé après
les [32 groupes ZIP](evidence/code-editor-archive-boundaries-dev-2026-11-22.json)
et le [rapprochement des preuves de sources](CONSOLE_EDITOR.md#sources-et-limites-qualifiées--22-novembre-2026).
070.4 est clôturé par les [36groupes et leur rapprochement](CONSOLE_EDITOR.md#diff-recherche-et-attentes-qualifies).
070.3/.5 sont clôturés par le complément29 ;070.6/.7/.8 conservent leurs preuves. Contrat détaillé dans [CONSOLE_EDITOR](CONSOLE_EDITOR.md)
avant code. Serveur et migration010 déployés sur7c5c6f4b ;
[45groupes réels](evidence/code-editor-server-dev-2026-11-12.json) qualifient une première tranche serveur,
dont070.7. La première facette Éditeur est déployée sura77b6b4e et
[57groupes réels](evidence/code-editor-console-dev-2026-11-12.json) passent :12UI/20serveur/25régressions,
17invocations Docker,41captures inspectées ;manuel17chapitres/67paragraphes.
Deux époques déclarées, produit identique ; à ce checkpoint, quotas, reprises et
compléments restent ouverts. Le complément [070.8](evidence/code-editor-save-confirmation-dev-2026-11-12.json)
passe 39 groupes sur 6e1584f2 et clôture le retrait des confirmations périmées.
La [capacité des brouillons](CODE_DRAFT_CAPACITY.md) est qualifiée par
[42groupes réels](evidence/code-draft-capacity-dev-2026-11-12.json) sur375sources25a4152 :32/128brouillons,
64Mio exacts de ciphertext, refus atomiques, libération et purge. Une publication
initiale est invoquée dans Docker ;66fonctions des deux passages sont purgées.
Le préliminaire17reste exclu. Le [complément46du testeur](evidence/function-http-client-ui-admission-dev-2026-11-12.json)
qualifie ensuite070.6 ;070.1–.5restent ouverts.
La reprise des preuves suit [Sources et limites](CODE_EDITOR_SOURCE_LIMITS.md) :
bornes HTTP/source archivée, compléments console, reconstruction/concurrence,
puis persistance et interruptions. Le premier passage échoue dans le lecteur
natif, corrigé ensuite ; sa [preuve séparée](evidence/code-editor-source-limits-reader-failed-dev-2026-11-12.json)
porte zéro groupe qualifié et le nettoyage complet. Le
[replay qualifié](evidence/code-editor-source-limits-dev-2026-11-12.json) passe38groupes
réels sur406sources59dd4591/image60938093 :13ciblés/25régressions,22captures,
cinq handlers et conservation exacte246→250/246fichiers. Source archivée,
texte1Mio+1, chemins512/255octets, diff2000/128Kio et JSON8Mio sont qualifiés.
Deux fonctions/tokens des passages sont nettoyés,5982artefacts conservés.
070.1–.5 restent ouverts pour les autres bornes, console et reprises.
L’ensemble de [compléments console](CODE_EDITOR_CONSOLE_EXTENSIONS.md) est décidé
avant son client : seconde page de sources/diff, archive/supprimée et adoption
en conservant la saisie. Le focus du diff fait l’objet d’un contrôle réel avant
toute correction ; le passage initial est conservé ci-dessous.
Le [passage échoué](evidence/code-editor-console-focus-failed-dev-2026-11-12.json)
reproduit quatre focusBODY après pagination, sur407sources/image60938093.
17groupes passent mais zéro n’est qualifié ;25captures inspectées,14handlers,
une fonction/sept révisions et un jeton nettoyés,13helpers terminés et5982artefacts
conservés. Correction de focus décidée avant code dans le contrat de console.
Le correctif est implémenté, relu et déployé en qualification surb452ef16 après
backup SQLite et conservation des données. Le [replay qualifié](evidence/code-editor-console-focus-dev-2026-11-12.json)
passe43groupes réels :18UI puis25communs,407sources6600150c/imageb452ef16.
Sept versions5+2 archive/supprimée, adoption sans PUT puis sauvegarde explicite,
diff5+2 et4H2+2H3 focalisés sont recoupés ;51images inspectées,14handlers nominaux.
Deux fonctions/tokens et quatre parents des deux passages sont nettoyés,26helpers
terminés, dix migrations et5982artefacts conservés. Manuel18/74SHA8a50ffa0.
070.1–.5 restent ouverts ; aucun critère n’est clos par ce seul complément.
Les réponses de diff périmées face à une mutation restent à éprouver avec un
lecteur vivant (070.4) ; le focus après adoption locale est à mesurer (070.3).
Le [contrat des lectures vivantes](CODE_EDITOR_READ_CONCURRENCY.md) définit la
barrière native du worker avant son client : FD/inode de campagne, suivi des
nouveaux threads, garde indépendante et six parcours réels de restitution/
capacité. Elle prépare droits pendant IO, purge et reconstruction ; aucune
clôture de070.1–.5 n’est revendiquée. Le [premier passage échoué](evidence/code-editor-reader-guard-join-failed-dev-2026-11-12.json)
prouve le secours mais échoue à sa jonction sur timer déjà retiré : cinq groupes
passés, zéro qualifié. Fonction/jeton/parents nettoyés, quatre helpers disparus,
quatre handlers et conservation recoupés. Correction de jonction décidée avant
code ; nouveau gel et replay complet requis.
Le [second passage échoué](evidence/code-editor-reader-event-failed-dev-2026-11-12.json)
passe sept groupes puis refuse un événement natif après deux lectures retenues.
Six helpers/handlers et nettoyage complet sont recoupés ; zéro qualifié.
Diagnostic brut et rapprochement des enfants hérités décidés avant code,
avec nouveau passage sur workers fraîchement créés après redémarrage DEV gardé.
Le [troisième passage qualifié](evidence/code-editor-read-concurrency-dev-2026-11-12.json)
passe34groupes (9ciblés/25communs),414sources11b90326/imageb452ef16. Quatre FD/
workers, trois clones avec arrêts enfants précoces, cinquième429 en63ms puis
capacité rendue, six modes de secours et sept handlers sont recoupés ;22images
inspectées. Trois fonctions/tokens, six parents et16helpers de tous les passages
sont nettoyés ; deux échecs exclus.070.1–.5restent ouverts pour droits pendant IO,
purge face à lecteur, reconstruction/ZIP, attentes UI et interruptions.
Nature : Développer. Dépend de : SLS-063, SLS-074. Ordre : 3.
Contrat : [éditeur](CONSOLE_USABILITY.md#éditeur-de-code-et-handler) et
[CONSOLE_EDITOR](CONSOLE_EDITOR.md). Le lien vers Tester de070.6 est désormais
implémenté et qualifié avec la tranche réelle SLS-071 ; les autres preuves de
l’éditeur restent dans leurs critères propres.

Le [cycle d’accès des sources](CODE_EDITOR_SOURCE_LIFECYCLE.md) est spécifié avant
son code : révocation Update pendant IO, nouveau propriétaire sans transfert de
brouillon, purge en phase artifacts face au FD vivant, puis refus et effacement
après jonction. Le [replay qualifié](evidence/code-editor-source-lifecycle-dev-2026-11-13.json)
passe30groupes réels (5ciblés/25communs),417sourcesed0ff67a/imageb452ef16,
22captures inspectées et deux handlers. Deux gardes terminées ; deux fonctions,
cinq jetons et quatre parents de tous les passages nettoyés. Révocation pendantIO,
propriétaires distincts et purge pending/artifacts puis effacement sont prouvés.
070.1–.5 restent ouverts : Create après retrait de la cible promue, ZIP,
attentes UI et reprises restent à qualifier. Le [premier passage échoué](evidence/code-editor-source-lifecycle-error-field-failed-dev-2026-11-13.json)
attendait detail au lieu du champ error commun : un groupe SSO passé, zéro
qualifié, aucun handler/helper. Fonction/deux jetons/deux parents nettoyés et
conservation recoupée ; correction de l’assertion décidée avant code.

Le [complément des droits sans cible promue](CODE_EDITOR_SOURCE_ACCESS.md)
isole le dernier cas dynamique de070.2 et rejoue la matrice de sources sur les
six GET, les mutations refusées et les variantes CSRF. Sept groupes ciblés,
trois handlers et25communs sont qualifiés par le [replay32](evidence/code-editor-source-access-dev-2026-11-13.json).
070.2 est clôturé après rapprochement des droits pendant IO ; les échecs
préliminaires ci-dessous restent exclus de ses groupes. Le
[premier passage](evidence/code-editor-source-access-scope-failed-dev-2026-11-13.json)
est refusé422 sur la portée Create du client ; deux fonctions/parents nettoyés,
aucun jeton/handler ni groupe qualifié. Correction selon le modèle de portée
service décidée avant code. Le [second passage](evidence/code-editor-source-access-default-status-failed-dev-2026-11-13.json)
passe cinq groupes puis attend404 au lieu de409 sans cible. Un handler,
deux fonctions/cinq jetons/deux parents nettoyés, zéro groupe qualifié.
Distinction409 sans cible/404 hash archivé décidée avant correction du client.

Le [complément ZIP](CODE_EDITOR_ARCHIVE_LIMITS.md) est découpé avant code en
capacité globale de publication puis frontières du paquet reconstruit. La garde
initiale reste inchangée ; B est créée après arrêt du read de A pour éprouver
le refus inter-fonctions. Les bornes exactes seront recoupées sur le ZIP conservé,
pas seulement prédites. La [capacité globale29](evidence/code-editor-build-capacity-dev-2026-11-13.json)
passe4ciblés/25communs sur423sources0856f1be/imageb452ef16 : refus429 A/B en
118/130ms pendant le read, UUID absents/états natifs inchangés, même POST A joint
puis B explicite publiée. Trois handlers,22captures, deux fonctions/un jeton/
deux parents/helper nettoyés. Frontières64Mio/256Mio/20000 et capacité après413
restent à produire ; aucun critère supplémentaire n’est clos. Le passage
de frontières prépare cinq fonctions, sept groupes ciblés et six handlers,
avec générateur de données isolé et inspection complète des archives conservées.
Les cinq sources du banc sont implémentées et relues statiquement ; syntaxe
contrôlée, aucune génération ni campagne ZIP exécutée à ce checkpoint.

Reprise du22novembre après078 : [préconditions du banc ZIP](CODE_EDITOR_ARCHIVE_LIMITS.md#reprise-du-banc-sur-le-contrôle-courant--22-novembre-2026)
persistées avant adaptation. Image433da150 vérifiée au repos, pins périmés à
actualiser, dix noms de migration exacts et budget HTTP administrateur600s.
Le passage7+25, ses frontières et son nettoyage restent à exécuter ; aucune
nouvelle qualification de070 n’est déduite du précontrôle natif.

Le premier passage au gel `db4980e` s’arrête après le SSO dans la préparation
des paquets, puis signale une erreur de nettoyage des fixtures. Zéro fonction,
namespace ou groupe qualifié ; rapport et contrôles conservés. La reprise du
générateur et du nettoyage est portée par [SLS-114](#sls-114), avant nouveau passage.

Résultat attendu : ouvrir le code d'une fonction, modifier un fichier texte et le
handler, enregistrer un brouillon, voir le diff, publier par le pipeline réel de
révisions immuables et tester le résultat.

Critères d'acceptation :

- [x] SLS-070.1 Arborescence de la version choisie, lecture d'un fichier texte, binaires et
  dépendances identifiés comme tels, limites de taille appliquées côté serveur.
  [Composition des preuves](CONSOLE_EDITOR.md#sources-et-limites-qualifiées--22-novembre-2026) :
  serveur45, sources38, console43 et ZIP32 gardent leurs époques et leurs groupes
  distincts. Les modules de lecture/extraction sont identiques ; le composant
  console actuel est celui du passage43. Les quatre frontières ZIP et leurs
  dépassements sont réellement éprouvés, avec six invocations et dix révisions.
- [x] SLS-070.2 Accès aux sources réservé aux droits de publication (Create sur un
  brouillon initial, Update sur une fonction publiée, session administratrice) ; le
  jeton Read seul n'accède ni aux sources ni à leur téléchargement. [32 groupes](evidence/code-editor-source-access-dev-2026-11-13.json) :
  sixGET,78cas de lecture et32mutations refusées sans effet, dont12CSRF ;
  Create ancien/nouveau refusé sans cible, restauration/pilote/promotion réels.
  Trois handlers et22captures communes ; droits pendant IO/purge conservés dans
  la [preuve30](evidence/code-editor-source-lifecycle-dev-2026-11-13.json), mêmes
  modules serveur, zéro groupe ajouté. Les routes livrées n’exposent pas de ZIP
  source supplémentaire. Six fonctions/dix jetons/six parents des passages nettoyés.
- [x] SLS-070.3 Brouillon persistant côté serveur, rattaché à une révision de base ;
  conflit de version détecté ; saisies non enregistrées signalées avant de quitter.
  Le [rapprochement des preuves](CONSOLE_EDITOR.md#persistance-et-publication-qualifiées-par-rapprochement)
  conserve45/43/39 pour base/conflit/saisies/snapshot,36 pour réponses tardives
  et focus,32 pour continuité du POST, sans addition de groupes.
  [Reprise29](evidence/code-editor-control-interruption-dev-2026-11-22.json) :
  mêmes ID/version/acteur/base/handler/ciphertext après deux vrais redémarrages,
  fichiers relus API/UI1440/390. Abandon/création explicites entre les deux
  bases A et C ; aucun brouillon reconstitué automatiquement après perte.
- [x] SLS-070.4 Diff entre brouillon et code déployé ; recherche dans le fichier ; chemins
  invalides refusés.
  [Rapprochement des quatre preuves](CONSOLE_EDITOR.md#diff-recherche-et-attentes-qualifies) :
  diff Bpromue/Abase, bornes et chemins côté serveur45/sources38 ; recherche
  littérale avec sélection DOM et pagination7chemins5+2 de console43 ; puis36
  pour réponses tardives des quatre actions, refus404/429/retry, quatre recalages
  détaillés et focus volontaire/adoption. Époques conservées, aucun groupe ajouté.
  Les modules serveur sont identiques et le seul delta UI115 est qualifié dans36.
- [x] SLS-070.5 Publication par le pipeline de validation Docker existant, hash et
  déduplication de SLS-074 ; un import refusé conserve la version active et le brouillon,
  avec diagnostic consultable ; handler CJS/ESM validé avec les vrais modules.
  [Rapprochement](CONSOLE_EDITOR.md#persistance-et-publication-qualifiées-par-rapprochement) :
  serveur45/console43/sauvegarde39 pour CJS/ESM/YAML/import refusé et diagnostic,
  mêmes six modules clés ; continuité32 pour mutation/snapshot/perte de réponse/
  orphelin429, puis [reprise29](evidence/code-editor-control-interruption-dev-2026-11-22.json).
  Deux vrais SIGKILL137/HTTP502, receiving complet puis validating vivant ;
  candidatscontrol_interrupted nettoyés sans révision publiée, A/ETag/config
  préservés. Pilotes B/D explicites, C choisie comme base sans promotion,
  déduplication exacte après reprise. Six handlers, sept candidats5pub/2failed,
  quatre révisions ; premier rouge118 conservé, aucun groupe ancien ajouté.
- [x] SLS-070.6 Après publication : lien vers le test de SLS-071, promotion explicite ou
  pilote, retour à un hash précédent. Le [complément46](evidence/function-http-client-ui-admission-dev-2026-11-12.json)
  suit le lien d’une version pilote puis celui de la publication réelle de
  l’éditeur vers le hash exécuté ; archivage refuse sans repli. La [tranche43](evidence/function-http-client-dev-2026-11-12.json)
  prouve les promotions A/B et le retour A, sur le même backend38sources.
  Ces campagnes conservent leurs époques et ne sont pas additionnées.
- [x] SLS-070.7 Réception des gros enregistrements bornée avant allocation :
  quatre corps partiels, cinquième429 en107ms avec0octet de corps ; quatre408
  après30,140–30,197s, requêtes exactes recoupées dans les logs natifs. Lecture
  rétablie et purges complètes prouvent la libération. La [preuve](evidence/code-editor-server-dev-2026-11-12.json)
  conserve aussi le premier échec du client ClientRequest45s, sans le compter
  dans les45groupes réussis. Client TLS réel avec Connection:close, aucun rejeu.

- [x] SLS-070.8 Retirer le succès historique dès une nouvelle saisie/consultation.
  [39 groupes réels](evidence/code-editor-save-confirmation-dev-2026-11-12.json) : 14 UI et 25 régressions sur
  371 sources, image 6e1584f2. Snapshot sauvegardé distinct des frappes tardives,
  champ readonly pendant retrait, vrai404/retry et choix de hash éprouvés.
  Huit sorties du verrou natif, refus de signal tardif et de naissance périmée,
  zéro écriture opérateur ; 21 anciens helpers absents et trois fonctions purgées.
  Les 44 images sont inspectées ; les 17 chapitres/67 paragraphes du manuel sont
  recoupés. Le premier essai trop rapide et le nominal préliminaire restent exclus.


Tests exigés :

- Unitaires : arborescence, diff, chemins, limites, calcul du paquet reconstruit.
- API / intégration : droits par requête directe (Read refusé), conflits, contenu
  volumineux et binaire, paquet identique dédupliqué.
- E2E depuis l'accueil réel : modifier un handler CJS puis ESM, publier, invoquer en
  Docker et lire la nouvelle réponse, import réellement défaillant, rollback,
  rechargement, perte de réponse pendant la publication, captures desktop et mobile.

À mettre à jour : `SCHEMA.md` et migration (brouillons), manuel, `DESIGN_SYSTEM_APP.md`
(éditeur, diff), seed (fonction éditable), parité (onglet de code).

<a id="sls-071"></a>
## SLS-071 — Client HTTP intégré par fonction

Statut : [x] — client HTTP livré en DEV sur60938093 ; huit critères qualifiés.
La [preuve31](evidence/function-http-client-task-exception-dev-2026-11-12.json) clôt071.6 : six groupes ciblés,
25régressions sur401sources67215a2b/commit417102d,26captures inspectées.
Vraiopenat/EMFILE puis OSError dans forward/TLS ; NOFILE rendu avant Python,
même PID et quatre places/cinquième429 puis succès. Douze handlers nominaux,
nettoyages de tous les passages et5982artefacts recoupés. Les preuves43/46/42/
32/37 ci-dessous conservent leurs critères/époques, sans addition de groupes.
Les défauts101/102 et la campagne globale095 restent des unités distinctes.

Historique des compléments :
Le [complément de chargement37](evidence/function-http-client-loading-dev-2026-11-12.json) qualifie071.2 :
7reprise,5chargement,25régressions sur397sources6b9cb2bc et30captures inspectées.
Même PID vivant pendant la lecture, perte d’observateur jointe, trois fonctions
purgées, deux jetons révoqués et5982artefacts conservés. Seul071.6 reste ouvert
parmi les critères ; la campagne complète reste requise.
[Réponses perdues32groupes](evidence/function-http-client-token-loss-dev-2026-11-12.json)
sur392sourcescf5244f5 : quatre coupures avant/après commit de création/révocation,
watchdog et25régressions ;32captures inspectées.071.3/.8 sont qualifiés.
[Reprise/confidentialité42groupes](evidence/function-http-client-recovery-confidentiality-dev-2026-11-12.json) sur389sources039c4c97 :
7reprise,10confidentialité et25régressions,12handlers et27captures inspectées.
Le [complément46](evidence/function-http-client-ui-admission-dev-2026-11-12.json)
garde384sources8285798e/8c761c5e,35handlers et38captures. Les critères
071.1/.3/.4/.5/.7/.8 sont qualifiés par leurs checkpoints propres, sans réaddition.
La [première tranche43](evidence/function-http-client-dev-2026-11-12.json) garde
032ca071/382sources et son expiration réelle900s. Manuel18chapitres/74paragraphes.
Nature : Développer. Dépend de : SLS-066, SLS-074. Ordre : 3.
Contrat : [client HTTP](CONSOLE_USABILITY.md#client-http-par-fonction) et
[CONSOLE_TESTER](CONSOLE_TESTER.md). Unité d'ordre3 retenue pour fournir le parcours
de test de070.6 désormais qualifié ; les autres preuves de070 restent ouvertes.
Le [plan échéances/confidentialité/reprise](CONSOLE_TESTER_FAILURES.md) précise
les scénarios complémentaires désormais qualifiés dans42 : SIGKILL natif,
reprise unique, vrai503 avant émission, délais UI et confidentialité native avec
témoin positif. Le complément32 qualifie ensuite les mutations de jeton.
Le refus de source et le chargement sont qualifiés par leurs compléments32/37 ;
exception inattendue d’une tâche et campagne complète restent à éprouver.

Résultat attendu : une facette Tester par fonction, de type client HTTP : composer une
requête, l'envoyer par la vraie passerelle, lire la réponse et retrouver l'appel et ses
journaux.

Critères d'acceptation :

- [x] SLS-071.1 Méthode, URL calculée (cible courante ou hash disponible), paramètres, en-têtes,
  corps texte, JSON ou fichier ; réponse avec statut, en-têtes, corps, durée, hash
  effectivement appelé et identifiant de requête ; réponse volumineuse ou binaire bornée
  avec téléchargement.
- [x] SLS-071.2 Contexte **serveur** (appel émis par le serveur de console, destinations limitées
  aux adresses de cette installation et à `/invoke/UUID[@HASH]`, redirections non suivies,
  cookies de console non transmis) et contexte **navigateur** (CORS depuis la vraie origine),
  explicitement distingués. Le [complément source refusée](CONSOLE_TESTER_SOURCE.md)
  fixe avant code le vrai503 avant émission, retrait UI des anciennes URL/résultats,
  hash indisponible distinct de cible absente, CSPself et restitution. Il réutilise
  la garde de permissions qualifiée066 ; autres causes du lecteur restent093.
  Relecture du banc avant panne : témoin positif du lien de téléchargement,
  hash/UUID natifs, intégrité/FK/migrations avant/après et cleanup du namespace
  sans service sont requis ; SHA image public fourni par le relevé du lanceur.
  Le [premier passage réel](evidence/function-http-client-source-access-failed-dev-2026-11-12.json)
  reproduit « Aucune cible promue » malgré le hash courant renvoyé sous EACCES ;
  zéro groupe retenu. Correction décidée : métadonnées courantes conservées avec
  erreur de source, chargement/indisponible/absence confirmée distingués. Replay
  Le [replay corrigé](evidence/function-http-client-source-access-dev-2026-11-12.json)
  qualifie32groupes sur395sources28105d2b/image60938093 :7ciblés et25régressions,
  hash exact sous EACCES, absence confirmée, vrai404 et reprise explicite.32vues
  inspectées ; six handlers, deux fonctions et deux jetons des deux passages
  nettoyés. Le transitoire « Lecture en cours… » reste sans assertion E2E dédiée ;
  le critère reste ouvert pour cette preuve, distincte de l’exception071.6.
  Le [complément de chargement](CONSOLE_TESTER_LOADING.md) réutilise le watchdog
  natif : vrai GET en attente, retrait UI, perte du seul observateur, PID conservé
  et reprise explicite. La revue impose avant code une revalidation immédiate
  d’identité/cgroup aux deux attachements et une preuve native du PID survivant.
  Ces sept scénarios et cinq groupes dédiés passent ensuite dans la
  [preuve37](evidence/function-http-client-loading-dev-2026-11-12.json), avec25régressions communes :
  GET réellement en attente, assertions et deux vues sous233ms ; helper SIGKILL,
  garde indépendante jointe, PID1007466/naissance508864062 conservés et TracerPid0.
  La réponse GET revient après détachement natif avant la garde ; ces deux
  instants restent distincts. Un seul GET et aucune invocation rejouée ; nouvel
  appel explicite200/hash/UUID natifs. Les30vues sont inspectées ; cinq handlers
  dont un interrompu par le scénario de reprise, trois fonctions purgées,
  deux jetons révoqués et zéro activité/réservation/bail/garde. Dix migrations,
  intégrité/FK et5982artefacts recoupés. Critère qualifié avec les preuves43/46
  des contextes et32du refus de source, sans addition de leurs groupes.
- [x] SLS-071.3 Vrai jeton Read : fourni, ou jeton temporaire limité à la fonction qui expire
  après quinze minutes ; valeur en mémoire de la page, absente des exemples copiés, journaux,
  erreurs, préférences et historique. L’inspecteur de preuve ne réémet aucun
  champ de log brut non validé, même s’il contient une fuite ; UUID/statut
  validés et SHA de route seulement. Les observations de réponse interceptent
  aussi un échec de décodage asynchrone et sont jointes avant clôture.
  Le lecteur est éprouvé négativement avec les sentinelles confidentielles,
  puis positivement par une vraie trace volontaire de témoin public, retournée
  uniquement par index/SHA. Le premier9groupes reste intermédiaire ; le passage
  dd3b50db reste préliminaire ; le replay84287810 sur96e5dc4e passe10groupes
  dans le checkpoint42, avec témoin positif et valeurs protégées absentes.
  Les pertes d’émission/révocation sont qualifiées par la [preuve32](evidence/function-http-client-token-loss-dev-2026-11-12.json) :
  quatre barrières avant/après commit, un watchdog, inconnue/confirmation
  conservées, liste UI et200/401 réels, sans lecture du secret perdu.
  Expiration900s reste la preuve43 ; confidentialité native reste42.
- [x] SLS-071.4 Annulation qui distingue l'arrêt de l'attente de l'issue du handler déjà
  admis ; aucun rejeu automatique d'une invocation incertaine ; refus de la passerelle
  restitués fidèlement.
- [x] SLS-071.5 Lien de la réponse vers l'invocation et ses journaux ([SLS-072](#sls-072)) ;
  exemple cURL copiable sans secret.
- [x] SLS-071.6 En-têtes ASCII validés avant normalisation et jonction de toutes
  les tâches avant restitution de capacité, même après exception inattendue.
  Le [complément d’exception native](CONSOLE_TESTER_TASK_EXCEPTION.md) fixe avant
  code la faute réelleopenat/EMFILE, restauration NOFILE au syscall-exit, même
  PID et capacité quatre+cinquième429. Une garde spécialisée restitue avant
  terminaison pilotée du traceur ; la fenêtre après sa mort spontanée est
  explicitement bornée et ne devient aucune dépendance FORGE. Seule une lecture
  initiale du contrôle est faite ; la classe Python et les scénarios restent
  à reproduire, sans remplacement du constructeur ou certificat.
  Revue avant essai du premier opérateur : reconnaître ESRCH/pidfd lisible et
  zombie du helper sans abandonner la restitution ; revalider toute l’identité
  avant prlimit, écrire l’échec atomique avec phase/limites et traiter l’alarme
  Python. Réconcilier aussi armement à réponse perdue et unités collectées.
  Ces corrections du banc et le client/lecteur de pile précèdent toute panne ;
  syntaxe seule contrôlée, aucun scénario de ce complément n’est qualifié.
  Seconde revue : temporaires de reçus par tentative et terminaux immuables
  ordonnés nativement ; le lecteur doit exposer un échec ultérieur à un succès.
  Ce reste est corrigé avant le premier essai, sans qualification anticipée.
  Revue client/diagnostic : l’image utilise --no-access-log ; ne pas exiger
  une ligne Uvicorn500 absente. Le vrai500 vient de Playwright/POSTunique,
  recoupé par pile TLS/audit/frontière/absence d’invocation natives. Aucun
  changement de logs produit, aucun scénario encore qualifié.
  Premier05ba6e14 sur401sources : SSO puis422 de création de fonction, champ
  description non supporté ; la requête native supposait aussi cette colonne.
  Zéro groupe qualifié, aucun attachement ou prlimit, aucune fonction/jeton,
  parents supprimés et limites intactes. Décision : nonce complet des parents,
  nom de fonction significatif suffixé du nonce8, liaison UUID/noms explicite,
  sans modifier le modèle produit ; replay complet requis.
  Replay742199ee : deux groupes passent puis helperexit1 aprèsarmed/avant
  fault-entry, cause perdue derrière SHA du stderr. Aucune baisse NOFILE,
  deux handlers succeeded ; fonction purgée, jeton révoqué et helper disparu.
  Zéro groupe qualifié. Décision : échec structuré avec phase/code/errno/ligne
  et compteurs numériques, sans chemins/buffers/messages bruts ; diagnostiquer
  réellement avant de changer délai, signal ou frontière de panne.
  Relecture de l’instrumentation : E/S du diagnostic après restauration
  prioritaire de NOFILE et libération, sans masquer l’exception initiale ;
  fichier du frame réduit à ID public fixe ou SHA. Pas de nom inconnu en clair.
  Passageca4aa8b9 instrumenté : CA_open_not_observed/phase2,8154ms,6777stops,
  48openat sans CA,2232pread64, aucun signal ; limites intactes et cleanup réel,
  zéro groupe qualifié. Décision avant code : waitpid bloquant sous alarme
  locale du helper, même échéance8s et garde12s, classe partagée inchangée.
  Le coût du polling est plausible, à éprouver sans allonger les bornes.
  Le [replay4337a800](evidence/function-http-client-task-exception-dev-2026-11-12.json) passe les six groupes :
  secours réel soussoft0, restauration avantKILL du helper, puis openat-24
  nominal avec cinq TID gelés, fenêtre de limite134655ns d’après les reçus
  Python originaux, restauration avant reprise. OSError et framesforward/
  HTTPX/TLS recoupés, vrai500 UI non confirmé et aucun départ passerelle.
  Même PID1007466/naissance508864062/CID/image/StartedAt, quatre relais actifs,
  cinquième429 en22,6ms, quatre succès puis cinq nouveaux et un appel UI.
  Avec25régressions,31groupes et26images inspectées ;12handlers nominaux.
  Trois fonctions/tokens de tous les passages nettoyés, quatre helpers partis,
  zéro activité/bail/réservation/garde, dix migrations et5982artefacts. Critère
  qualifié ; les trois passages échoués restent exclus et leurs reçus conservés.
  Revue avant déploiement : `Key` pouvait devenir `key` puis échouer à l'encodage
  et empêcher le décrément du compteur. Relecture du banc de reprise avant
  exécution : StartedAt doit être revérifié avant KILL/signaux et chaque reprise
  reconnue par son propre reçu verrouillé ; le CID/image seul ne distingue pas
  un redémarrage concurrent. Vérifier les empreintes opérateur/observateur,
  borner la mémoire/jonction du SSH et écrire le reçu natif avant déverrouillage.
  Premier reçu3360afcd : watchdog restauré mais assertion SSH137 trop stricte
  (255 réel) puis MainPID absent du timer. Reprendre le précédent137/255 avec
  événement SIGKILL et reçu indépendant ; timer inactif/service PID0, et
  conserver les événements d’opérateur même après échec. Aucun KILL produit
  ni groupe de récupération qualifié dans ce passage.
  Les vrais arrêts et la capacité sont ensuite recoupés dans42 ; une exception
  Python inattendue d’une tâche dans un contrôle restant vivant demeure une
  garantie relue, pas encore un scénario exécuté.
  Relecture du nouvel opérateur de jetons avant exécution : exiger intégrité/FK
  des deux bases et réservations nulles, puis revérifier CID/image/StartedAt,
  naissance/cgroup immédiatement avant tout attachement, watchdog inclus.
  Premier3c50e181 : coupures de création natives franchies mais liste UI
  comptée avant rendu Resource. Attendre panneau/lignes exactes avant assertions ;
  fonction purgée, jeton perdu révoqué par UUID, parents/gardes nettoyés.
  Reçu préliminaire exclu ; les quatre cas passent ensuite dans32.
  Refus422 répétés puis cinq appels sains
  passent dans la tranche43 ; à ce checkpoint, saturation et interruption
  restaient à prouver, avant les compléments46 et42.
  Appliquer aussi avant fetch navigateur les mêmes bornes query/en-têtes et
  interdictions que dans le mode serveur ; préserver les refus HTTP du testeur.
  Le client de preuve réconcilie aussi une création à réponse5xx inconnue,
  sans rejouer le POST, et termine ses fermetures indépendamment des erreurs.
  Premier passage réel047e33 :13groupes serveur réussis, timeout au premier
  parcours UI ; deux fonctions purgées, aucun groupe ajouté à une preuve finale.
  Étapes/capture d’échec instrumentées et URL du catalogue corrigée avant replay.
  Passage4824d4a2 :18groupes ciblés puis25régressions passent ; deux fonctions
  nominales et deux préliminaires purgées, huit jetons révoqués. Les13groupes
  préliminaires restent exclus des43.

- [x] SLS-071.7 Retirer les erreurs et confirmations de composition dès que leur
  saisie change. Revue du passage UI f4908538 : après refus d’un fichier>1Mio,
  le choix JSON laissait « Le fichier dépasse1Mio » à côté du nouveau corps et
  du cURL. Effacer ces messages sur changement des champs de composition,
  conserver les nouvelles erreurs jusqu’à correction ou nouvel envoi et ne pas
  prétendre modifier l’issue de l’appel précédent. Tester le vrai refus fichier,
  passage JSON, correction de JSON invalide et modification après copie cURL.
  La même revue relève «1octets» : afficher le singulier pour un seul octet
  et vérifier ce compteur avec le vrai corps JSON invalide d’un octet.
  Le [complément46](evidence/function-http-client-ui-admission-dev-2026-11-12.json)
  sur8c761c5e prouve retrait après fichier/JSON, correction de JSON invalide et
  modification après copie ; nouveau refus conservé et singulier vérifié.
  38captures sont inspectées ; le passage21antérieur reste exclu.

- [x] SLS-071.8 Distinguer le refus confirmé du contrôle et le502 du proxy
  après admission. Reçu80eca655 sur8c761c5e : SIGKILL natif/Docker137, reprise
  unique `control_interrupted`, mais UI affiche un refus certain502. Marquer
  les réponses API réelles du contrôle et vérifier la forme de l’erreur avant
  ce classement ; une réponse sans provenance reste inconnue, sans rejeu.
  Appliquer aussi aux mutations du jeton temporaire. Rejouer coupure, vrai503
  avant émission sous verrou SQLite sans écriture, capacité, manuel et
  régressions sur la nouvelle image. Dans42, coupure puis vrai503 sont
  qualifiés sur96e5dc4e ; la [matrice dédiée](CONSOLE_TESTER_TOKEN_LOSS.md)
  passe ensuite dans32 sur la même image : mutations avant/après commit,
  unique POST, message non confirmé et métadonnées retrouvées,32captures
  inspectées.071.8 est qualifié par42 et32, sans addition de leurs groupes. Contrat : [provenance](CONSOLE_TESTER_FAILURES.md#défaut-reproduit-après-admission--correction0718).

Les critères071.1/.5 reposent sur43 et46 (corps, limites, versions, cURL et
corrélation) ;071.4 reçoit en plus42 (deux délais UI et vraie coupure sans rejeu).
Chaque preuve garde sa source/image, ses groupes et son périmètre. Aucune
somme des checkpoints n’est annoncée comme campagne complète.

Tests exigés :

- Unitaires : construction de requête, bornes de réponse, expurgation, validation de destination.
- API / intégration : destinations interdites, redirections, expiration et révocation du jeton,
  droits par requête directe, politiques origine/IP évaluées sur l'IP réelle de l'appel.
- E2E depuis l'accueil réel : appels réels texte, JSON, binaire, CORS réussi et refusé, timeout,
  annulation, corrélation avec l'invocation, hash demandé indisponible sans repli, captures
  desktop et mobile.

À mettre à jour : manuel, `DESIGN_SYSTEM_APP.md`, parité (onglet Test), seed.

<a id="sls-072"></a>
## SLS-072 — Journaux recherchables et corrélation d'exploitation

Statut : [~] — registre011, API, vues, recherche, suivi et export implémentés et
déployés en DEV sur1aa70214 ; qualification fonctionnelle, visuelle et
régressions encore à produire. La bascule gardée nominale est recoupée,
sans groupe fonctionnel ajouté et sans clôture d'un critère ci-dessous.
Le premier passage API s'arrête sur la frontière du buffer ; [SLS-120](#sls-120)
porte son diagnostic et sa correction avant reprise de072.4.
Nature : Développer. Dépend de : SLS-061, SLS-074. Ordre : 3.
Contrat : [EXECUTION_LOGS](EXECUTION_LOGS.md), complétant
[journaux](CONSOLE_USABILITY.md#journaux-et-corrélation).

Résultat attendu : retrouver et suivre les journaux d'une fonction ou d'un service sur une
période, et passer d'une ligne à l'appel, à la version et à l'instance concernés.

Critères d'acceptation :

- [ ] SLS-072.1 Vues fonction et service : période, sévérité lorsqu'elle est connue (sinon non
  renseignée), état, identifiant d'appel, recherche texte ; pagination.
- [ ] SLS-072.2 Suivi des nouveaux événements activable et pausable, repris après coupure.
- [ ] SLS-072.3 Corrélation fonction, service, version et hash exécuté, instance, requête,
  chronologie ; événements de plateforme (publication, démarrage, extinction, délai
  dépassé, opération de stockage) retrouvables ; erreurs de code distinguées des refus
  d'admission et des défaillances d'infrastructure.
- [ ] SLS-072.4 Collecte, taille, rétention, historique interrogé et exports bornés ; troncature,
  rétention expirée et collecte indisponible signalées ; secrets expurgés ; valeurs
  d'authentification et corps métier non journalisés.
- [ ] SLS-072.5 Export respectant les droits ; texte échappé, clavier et mobile.
- [ ] SLS-072.6 Migration011 additive et [déploiement gardé](EXECUTION_LOG_DEPLOYMENT.md) : intégrité/FK,
  conservation des données et des sources réelles, puis régression du socle
  49 campagnes / 543 groupes sur011 et des consommateurs ajoutés depuis,
  inventoriés séparément avant adaptation. Les préconditions des clients courants
  sont actualisées avant exécution ; les branches historiques et captures
  scellées restent intactes. Les groupes communs ne sont comptés qu'une fois.

Tests exigés :

- Unitaires : analyse texte/JSON, expurgation, bornes, pagination.
- API / intégration : droits par requête directe, secrets absents, rétention, redémarrage.
- E2E depuis l'accueil réel : logs réels texte et JSON d'un handler Docker, erreur de code,
  refus d'admission, troncature, suivi interrompu puis repris, export, diagnostic depuis
  un appel déclenché dans la console, captures desktop et mobile.

À mettre à jour : `SCHEMA.md` et migration, manuel, `DESIGN_SYSTEM_APP.md`, parité
(journaux), seed.

<a id="sls-073"></a>
## SLS-073 — Monitoring historique et alertes dans la console

Statut : [ ] — relevés Docker ponctuels présents ; séries, tableaux de bord et alertes absents.
Nature : Développer. Dépend de : SLS-072, SLS-078. Ordre : 7.
Contrat : [monitoring](CONSOLE_USABILITY.md#monitoring-et-alertes).

Résultat attendu : voir l'évolution de l'activité et des ressources par plateforme,
namespace, service et fonction, et être alerté quand un seuil est franchi.

Critères d'acceptation :

- [ ] SLS-073.1 Séries historiques : appels, erreurs, refus, délais dépassés, latence et
  percentiles avec taille d'échantillon, attente, démarrages à froid, instances, CPU,
  mémoire, stockage ; unité, période, source ; allocation, plafond et consommation
  distingués ; donnée manquante ou échantillon insuffisant indiqués.
- [ ] SLS-073.2 Santé du contrôle, du moteur Docker, de l'agent de stockage et des nettoyages en
  attente ; tirs de planification et jobs ([SLS-078](#sls-078)) visibles.
- [ ] SLS-073.3 Seuils configurables, alertes avec état, début, fin, lien vers objets et journaux ;
  déduplication ; retour à la normale visible.
- [ ] SLS-073.4 Collecte et agrégation sur mesures réelles, rétention et budget bornés, coût
  mesuré sur le SPARK ; intervalle et lacunes affichés ; rafraîchissement suspendable ;
  vues partageables par URL.
- [ ] SLS-073.5 Droits côté serveur par périmètre.

Tests exigés :

- Unitaires : agrégation, percentiles, rétention, déduplication d'alerte.
- API / intégration : valeurs recoupées aux appels et aux mesures, droits par requête
  directe, redémarrage du collecteur.
- E2E depuis l'accueil réel : charge réelle et panne provoquées, franchissement et retour
  sous seuil, collecte indisponible, graphes inspectés sur ordinateur et mobile, coût de
  collecte mesuré.

À mettre à jour : `SCHEMA.md` et migration, manuel, `DESIGN_SYSTEM_APP.md` (graphes,
alertes), parité (métriques, alertes), seed.

<a id="sls-074"></a>
## SLS-074 — Versions par hash, appels épinglés et pilote de code

Statut : [~] — publication, promotion et invocation par hash déployées en DEV ; checkpoint ciblé008 qualifié.
Reste à faire : [SLS-094](#sls-094) (pannes, console, régression complète).

Checkpoint livré et qualifié : [registre persistant](FUNCTION_VERSION_REGISTRY.md),
migration additive des identités, conservation des alias et lecture/copie du hash.
Ce checkpoint007 est historique. Le contrôle008 sépare désormais publication
et promotion, déduplique et admet les appels épinglés ; sa qualification complète
reste dans cette même unité.

La [preuve du registre](evidence/function-version-registry-dev-2026-11-09.json)
passe 359 groupes : 46 ciblés/historiques et 313 dans 18 campagnes communes, sur deux
époques de 233 sources aux mêmes fichiers produit et image. Les 69 captures
recoupées comprennent 47 nouvelles inspections et 22 références SHA identiques.
Manuel 15 chapitres/47 paragraphes, six fonctions du registre purgées dans six
namespaces recoupés, 29 fichiers Python/SQL embarqués et deux assets HTTPS conformes.
L’upgrade au repos conserve sa preuve antérieure 328 groupes, sans addition comme
groupes uniques au total 359. La [reprise des purges 006](FUNCTION_VERSION_PURGE_UPGRADE.md)
passe 31 groupes ciblés sur l’image finale ; le banc 003→007 passe 5 groupes.
Le premier arrêt SQLITE_BUSY_RECOVERY reste conservé avec son nettoyage natif ;
le poller RO persistant passe 15 groupes ciblés puis la suite complète. Les deux
entrées du registre d’incohérences sont retirées après leurs preuves ; le
versionnement complet reste en cours pour les étapes suivantes.
La prochaine livraison suit [FUNCTION_VERSION_EXECUTION](FUNCTION_VERSION_EXECUTION.md) :
autorité d’état par hash, première promotion durable, déduplication avec nettoyage,
admission/pools et raccordements CLI/UI livrés ensemble. Les nouveaux critères
incluent le droit Create après désactivation, les handlers A/B et le cas
minimum=maximum=1 ; les exigences existantes ne sont pas réduites.
Le [checkpoint ciblé008](evidence/function-version-execution-checkpoint-dev-2026-11-09.json)
réunit71 groupes :2 migration/reprise,12 API,5 CLI authentifiés depuis le poste,
6 UI,8 manuel et38 packaging/refus dans les images CLI. Les époques239/242/244
sources sont explicites ; les31 sources backend sont identiques entre API/CLI/UI.
Les28 captures sont inspectées ; le manuel correspond à15 chapitres/52 paragraphes.
Dix fonctions, dont celles des essais interrompus, sont purgées ; instances,
appels, opérations, réservations et montages actifs sont à zéro. Préparation007
et nettoyage migration sont des prérequis non additionnés. Les essais UI
interrompus et les premiers replays verts restent distincts, sans gonfler71.

Les cinq groupes CLI passent depuis Python sur le poste, avec six invocations
des URL des deux domaines. Leur déclinaison authentifiée dans les deux images
passe désormais cinq groupes par image, détaillés ci-dessous. La convergence API est recoupée physiquement avant purge :
révision canonique conservée, paquet réutilisé effacé, réservations à zéro.
Le catalogue UI est lu après le candidat ; le suivi termine avec le nouveau hash
sans mutation d’ETag parent. Les vrais refus409/404 conservent confirmation,
saisie et focus après réactivation. Le dialog conserve son contexte quand sa
carte quitte la page pendant une publication réelle. Les messages de publication
sont recoupés au PUT réel, au GET durable et au rendu ; aucun corps PUT navigateur
n’est déclaré observé. Les pannes et la régression complète restent ouvertes.
Le [complément CLI Docker](evidence/function-version-cli-images-dev-2026-11-09.json)
passe cinq groupes par image sur245 sources figées : vingt conteneurs CLI,
douze invocations réelles et deux fonctions supplémentaires purgées. Les six
modules embarqués, trois fichiers de projet, images et nettoyages sont recoupés.
Le contrôle, la référence, les images et la configuration officielle sont
inchangés. Aucun client, réseau/volume Compose ou définition temporaire ne reste.
Les douze fonctions des campagnes008 sont purgées, l’essai initial n’en a créé
aucune et ses parents sont supprimés. Le premier lanceur direct échoue sur la
lecture littérale de l’origine citée ; le replay passe par Compose DEV sans
changer la cellule. Le rapport incomplet reste séparé. Les dix exécutions
complètent cinq comportements dans deux images et ne sont pas revendiquées
comme dix comportements nouveaux. Les pannes du helper, ses délais indépendants,
les fautes de publication/migration et la suite complète restent nécessaires.
La [preuve de nettoyage avec attente](evidence/function-version-validation-recovery-dev-2026-11-09.json)
passe quatre groupes sur248 sources figées, avec cinq invocations. A/B sont
réellement admis avant la faute ; B reçoit le503 précis avant validation,
request_rejected et validation NULL. Le refus global du socket laisse le
conteneur présent ; l’exception du canal isolé le retire et laisse Docker
accessible. Le journal de chaque fenêtre ne porte que le create de A. Le
pipeline reprend par maintenance normale, sans redémarrage, après restitution
explicite puis indépendante après SIGKILL du helper. Le pilote est publié puis
réutilisé, avec stable et données/cache préservés.
Deux fonctions (essai interrompu et replay) sont purgées ;13 candidats et trois
révisions n’ont plus d’artefact, les parents sont supprimés, les jetons révoqués.
Les deux helpers et gardes du replay sont terminés ; compteurs actifs à zéro.
Les31 fichiers backend, images et configuration officielle sont inchangés. Les
arrêts sur SSO puis champ de diagnostic erroné restent séparés, sans groupe vert.
La revue a fermé la fenêtre lstat/chmod du helper par descripteur épinglé avant
la faute. La vérification physique de la garde de validation est donc acquise ;
les autres pannes, migrations perturbées et la régression complète restent
obligatoires avant clôture074.

La [capacité des uploads](FUNCTION_VERSION_UPLOAD_CAPACITY.md) est maintenant
[qualifiée](evidence/function-version-upload-capacity-dev-2026-11-09.json) :
quatre groupes sur267 sources figées et la même19cfe884. Quatre admissions
réservent1 997 570 048 octets ; le cinquième429 conserve prepared/réservation0,
sans artefact. Un vrai candidat attend encore lors d'un relevé commencé après
31,43s. Quatre create/destroy natifs confirment un seul validateur à la fois ;
A expire normalement et B/C/D convergent vers un hash/UUID, avec un seul créateur.
La relance explicite du même cinquième candidat réutilise ce hash après validation.
Quatre appels conservent cible, ETag, configuration chiffrée et compteurs data/cache1–4.
La fonction finale et les deux fonctions des essais précédents sont physiquement
purgées ; compteurs actifs/réservations nuls,31 fichiers backend et services conservés.
L'essai de collecte interrompu et le replay intermédiaire restent distincts,
sans addition de groupes. Les pertes de réponses de création du banc et l'instant
du callback de maintenance ne sont pas qualifiés par cette preuve.

La [reprise des paquets dédupliqués](FUNCTION_VERSION_DUPLICATE_RECOVERY.md) est
[qualifiée](evidence/function-version-duplicate-recovery-dev-2026-11-09.json) :
quatre groupes sur 271 sources figées, cinq appels et compteurs données/cache1–5.
Deux commits200 identiques conservent chacun 499 392 512 octets réservés sous
EACCES du seul répertoire candidat. La première restitution reprend par maintenance
sans redémarrage. Après le second commit, SIGKILL du contrôle (137), signal9 du
helper recoupé par waitpid, puis garde indépendante qui restitue et démarre le
même ID/image/configuration. Le candidat reste published, ses octets sont retirés
et une nouvelle déduplication réussit. La fonction est purgée physiquement,
les unités/helpers sont terminés et les compteurs actifs/réservations nuls.
Les fichiers officiels,31 backends et référence sont conservés. Le journal natif
recoupe l'exécution indépendante ; aucune coupure pendant unlink, perte SSH ou
panne propre de la garde n'est déduite de cette preuve. Ces fenêtres, les autres
pannes, migrations perturbées et la régression complète restent ouvertes.

Le [complément008](FUNCTION_VERSION_MIGRATION_008_RECOVERY.md) reproduit le
refus manquant sur19cfe884 puis corrige la première transition. Le premier
checkpoint neuf reste historique ; la [preuve de reprise](evidence/function-version-migration008-recovery-dev-2026-11-09.json)
retient dix groupes sur276 sources : six refus transactionnels, témoin007,
verrou/reprise, contraintes et coupure WAL/reprise. Les anciennes colonnes des16
tables,863 groupes/219 doublons,261 tombstones inconnus et141 alias supprimés au
hash connu sont conservés ;2882 publications/4418 invocations sont recoupées.
Le SIGKILL suit une écriture WAL réelle non commise :007 reste exact puis le
même conteneur applique008. Copies retirées, sauvegarde originale inchangée.

La bascule def45648f9e7 est qualifiée avec backup natif privé et garde d'image :
17 tables et schéma déjà008 strictement identiques après remplacement. Sur277
sources figées,12 groupes API et5 CLI passent, avec16 invocations réussies et
un refus attendu. Deux fonctions sont purgées physiquement ;31 backends et4
fichiers HTTPS recoupés, référence/configuration/routes conservées, actifs nuls.
Les trois essais WAL et l'essai de bascule arrêté avant garde sont séparés du
total. Les gardes nominales sont désarmées ; leur déclenchement autonome et leurs
pannes propres ne sont pas qualifiés par ce parcours. Le jeu de ce checkpoint ne contient pas premier hash inconnu puis connu ;
le complément dédié ci-dessous le qualifie. Les autres pannes et la régression complète restent nécessaires. Statut conservé[~].

Le [replay de purges historiques008](FUNCTION_VERSION_PURGE_MIGRATION_008.md)
est qualifié par22 groupes : quatre fenêtres006/007→008 en volumes/artifacts,
une restitution indépendante007/artifacts après perte du pilote, puis trois
refus source/cible avant armement/arrêt/déplacement. Les19 groupes de fenêtres portent280
sources ; les3 refus281 sources, avec mêmes exécutables communs. L'attestation007
recoupe29 backends historiques, image et tag conservés. Les identitésNULL ne sont
pas inventées ; les hashes connus, UUID/dates et registre deleted sont conservés.
Les anciens champs des tables restent identiques sauf phase/erreur de la purge
exactement corrélée. Les quatre purges normales terminent et persistent après
restart ; la cinquième installation temporaire est retirée par garde.

Le recoupement retrouve les17 tables, le registre de stockage et5982 artefacts
originaux identiques après les cinq restitutions, gardes inactives et ressources
actives nulles. Le contrôle e661516b conserve def45648 ; démarrage de ce checkpoint
2026-11-09T18:52:49.904838248Z attendu après restitution. Référence/configuration/
routes inchangées, nouvelle construction produit inutile, manuel/web inchangés.
L'essai d'attestation interrompu est séparé, sans groupe ajouté. Les autres pannes restent nécessaires ; statut[~]. Preuve : [purges008](evidence/function-version-purge-migration008-dev-2026-11-09.json).

La matrice de [corrélations007](FUNCTION_VERSION_PURGE_MIGRATION_008.md#refus-de-corrélation-sur-copies007)
est qualifiée :42 groupes sur283 sources,40 refus et2 témoins depuis les backups
007 volumes/artifacts réels. Trente-huit refus UDF et deux CHECK actifs conservent
exactement snapshots logiques/schéma/tables007 ; les contraintes restent actives.
Les témoins conservent les anciennes colonnes des16 tables, le hash connu, version
deleted, dates et backfills puis redémarrent le même conteneur sans changement008.
La panne attendue de socket vient ensuite, sans disponibilité HTTP revendiquée.

Archives principales, WAL0 et SHM32768 conservés par SHA/identité/mode ;42
conteneurs et copies retirés. Les17 tables du contrôle servi, ID/image/démarrage,
référence et fichiers officiels restent strictement identiques, actifs nuls.
L'essai initial arrêté avant copie est séparé, zéro groupe ajouté. Le banc
historique006 et les22 groupes de reprise publique restent dans leurs époques ;
aucune addition rétroactive. Les autres interruptions et la campagne complète restent nécessaires ; SLS-074 conserve[~].
Preuve : [corrélations007](evidence/function-version-purge-correlation008-dev-2026-11-09.json).

La [première identité inconnue](evidence/function-version-unknown-first-dev-2026-11-09.json) passe17 groupes sur286 sources :
un témoin entièrement issu des API006, une variante de données anciennes déclarée
qui retire seulement deux métadonnées de A déjà supprimée dans la copie privée,
puis une restitution indépendante pendant un handler008 observé actif. Les vraies
images006→007→008 conservent pointeur B, UUID/dates et marqueurs ; le premier hash
resteNULL dans la variante, sans rétablir les droits Create. C pilote reste
invocable par hash, B demeure stable jusqu'à promotion explicite. Deux purges
publiques terminent ; la troisième installation temporaire est retirée par garde.
Les23 appels réussis recoupent configuration, secret par empreinte et compteurs
données/cache. Les originaux,17 tables et5982 artefacts sont conservés ; même
contrôle def45648/e661516b, nouveau démarrage attendu 2026-11-09T20:16:45.245982432Z. La garde indépendante
retire exactement une instance, un réseau et un bail par le vrai agent ; les trois
gardes sont inactives, ressources actives nulles. Les essais antérieurs restent
séparés du replay final. Les pannes propres de garde, autres interruptions et
la régression complète008 restent dans SLS-074, toujours[~].

Le témoin API006 conserve l'inventaire de A supprimée : cette API ne produit pas
à elle seule A inconnue/B connue. Le backup API et la variante préparée restent
séparés, avec comparaison de toutes les anciennes colonnes. La préparation
n'est jamais attribuée à une capacité publique historique. Les17 groupes finaux
excluent la première matrice interrompue, le ciblé vert3 et la matrice verte avant
le dernier durcissement des diagnostics. La lecture du corps interrompue reste
une branche distincte non provoquée par le nominal502 à corps vide.

Les [réponses perdues des décisions de version](evidence/function-version-state-transport-dev-2026-11-09.json) passent9 groupes
sur290 sources figées : promotion par la vraie CLI, archivage et suppression
avec remplacement, chacun avant traitement puis après décision avant réponse.
Les six SIGKILL sont constatés nativement et par Docker137 ; même conteneur/image
redémarrés, référence et fichiers officiels conservés. La CLI retourne unknown
avec exactement deux connexions HTTPS, sans rejeu. Avant traitement, métier
inchangé puis relance explicite ; après commit, pointeur/état/ETag/audit persistés
ensemble sans renvoi. Le delete est observé après sa tentative de nettoyage,
sans prétendre une interruption avant effacement physique.

Seize appels réussis retrouvent les handlers A/B, configuration, secret par
empreinte et compteurs données/cache1–16 après les reprises. Les réimports B
gardent hash et date initiale ; les premiers marqueurs restent immuables.
Une perte SIGKILL de l'observateur éprouve la garde indépendante sans mutation.
Les sept gardes et helpers sont terminés ; les six arrêts ont leurs reçus root.
Une fonction est purgée publiquement, volumes/artefacts et ressources actives
absents. Les deux bootstraps arrêtés avant garde restent archivés avec leurs
purges physiques, zéro groupe ajouté. Aucun produit/UI/manuel ni configuration
modifié ; la lecture sous-propriétaire recoupe les31 backends et le web.
SLS-074 reste[~] pour les autres interruptions et la régression complète008.

La prochaine étape est l'adaptation fidèle de la régression courante008.
L'exploration source du scope publication constate18 campagnes/313 groupes
historiques, sans inclusion automatique des nouveaux clients SLS-074. Les attentes
à adapter sont identifiées dans control-operations, deployments, code-publications,
adapter-deploy, publication-recovery, function-storage, public-invocations,
execution-ui et publication-ui. Conserver tous leurs contrôles de droits, pannes,
quota, consommateurs, persistance, parcours et rendu ; aucun scénario n'est retiré
pour obtenir du vert. Les sources006/007 des bancs historiques restent inchangées.
L'upgrade de storage-legacy-recovery doit seulement nommer sa cible008 explicitement.

Ordre décidé : adapter d'abord migrations/fixtures/publications API/CLI et leurs
refus, puis stockage/invocations et reprise, puis les parcours de console ;
rejouer chaque campagne modifiée avant le gel et la suite complète en série.
La matrice finale doit inventorier les clients SLS-074, distinguer prérequis,
époques et captures, et compter les groupes réellement retenus sans figer le
total à313. Les21 anciens groupes de publication UI ne sont pas remplacés par
les six nouveaux parcours ciblés. Sources et discriminants de l'exploration
sont consignés au journal du9novembre ; aucun résultat de cette adaptation
n'est encore acquis. Le statut reste[~].

La [première tranche de régression008](evidence/function-version-publication-regressions-dev-2026-11-09.json) passe76 groupes sur292
sources figées :55 contrôles du vrai composant Docker et21 groupes HTTPS des
publications complètes/code seul. Le prérequis SSO réel reste distinct. Les huit
migrations, intégrité, verrou et refus de configuration sont conservés ; les11
et10 groupes de publication gardent droits, propriété, conflits, révocation,
import réel, abandon, course et pagination.

Upload et promotion sont distingués, y compris première promotion Create. Une
observation native recoupe deux candidats validating/réservés et le seul validateur
vivant du premier ; le doublon réutilise le hash et la révision canonique sans
changer la cible. Rollback et pilote sont réellement invoqués. Sept appels
recoupés en base vérifient hashes demandés/résolus, handlers et configuration.
Les cinq appels de code seul vérifient l’empreinte du secret ; les deux appels
de publication complète contrôlent sa présence puis son absence. Le compteur
POST reste1 lors des GET après promotion.

Quatre fonctions sont purgées par l'API publique, code/volumes/réservations absents
et parents supprimés. Les empreintes avant purge ne prétendent pas représenter
des archives encore conservées. Les5982 artefacts antérieurs et les services,
ID/images/démarrages, fichiers officiels et backend/web embarqués restent identiques.
Les anciens rapports restent préservés par SHA. Aucun build produit ni nouveau
parcours visuel ; les autres clients et la régression complète restent dans
SLS-074, toujours[~].

La [tranche CLI et reprise008](evidence/function-version-cli-recovery-regressions-dev-2026-11-09.json)
passe 11 groupes réels sur 296 sources figées : sept déploiement/promotion CLI et
quatre plafonds/reprises. Le prérequis SSO réel reste distinct. Les 68 appels CLI
recoupent hash, UUID et présence du secret commun ; huit appels de reprise
comparent aussi marqueur, configuration et empreinte du secret. Vingt codes
réellement distincts remplissent le plafond ; un doublon est admis sans nouvelle
version ni changement de cible, un nouveau hash est refusé puis admis après retrait.

Deux SIGKILL du contrôle sont constatés nativement et par Docker137, en réception
partielle puis avec validateur Docker vivant lié au candidat, à son installation
et à l'image runtime configurée. La seconde perte du helper déclenche réellement
la restitution indépendante. Les candidats deviennent failed/control_interrupted,
sans réservation, configuration temporaire, code, validateur ou canal restant.
La cible stable, les premiers marqueurs et la configuration privée sont conservés ;
les uploads suivants restent pilotes jusqu'à promotion explicite.

Les 22 fonctions sont purgées publiquement dans deux namespaces ; 76 invocations
réussies uniques, dont 27 épinglées, sont recoupées en base. Helpers, timers et
services des deux gardes sont terminés. Les 5 982 artefacts antérieurs et fichiers
officiels restent identiques ; contrôle de même CID/image, démarrage attendu
2026-11-09T22:00:26.747122276Z, référence inchangée. Aucun build produit, changement
d'UI/manuel ni nouvelle preuve visuelle. Les autres clients, les pannes propres
du banc et la régression complète008 restent dans SLS-074, toujours [~].


La [tranche invocation/stockage008](evidence/function-version-invocation-storage-regressions-dev-2026-11-10.json)
passe 46 groupes réels sur 298 sources figées : 15 mutations de stockage et
31 invocations publiques. Le prérequis SSO reste distinct. Sept appels Echo
recoupent A pilote/promue, doublon malgré quota modifié, B pilote/promue et
rollback A. Quota7 Mio, reçu de stockage et fichiers données/cache sont conservés.
La confirmation indisponible conserve son vrai503 et sa décision acquise.

Pendant un handler A observé actif, publier B ne déplace pas la cible. Après
promotion B, retirer A empêche ses nouvelles admissions tout en laissant finir
son instantané ; le nettoyage reste en attente puis efface A après libération.
Les31 groupes conservent ACL, HTTP/Lambda, politiques origine/IP, files, minima,
quotas, concurrence, budgets réels, contention SQLite, arrêts et réceptions bornées.
Le plafond d'instances est appliqué puis restitué par la console du seul SPARK.

La collecte recoupe 85 handlers succeeded, dont78 publics et7 Echo ; deux réponses
métier non2xx et un succès après déconnexion restent classés selon l'état durable.
Les107 réponses publiques comprennent16 UUID avant réservation. Le vrai502 du
proxy sans UUID est lié par l'identité locale de sa connexion au témoin natif
running puis au même appel interrupted ; son statut durable503 reste distinct.

Les18 fonctions finales sont purgées par les API. L'essai initial avait passé
46 groupes mais échoué à la collecte de ce502 ; il reste séparé et ne s'ajoute
pas au total. Ses18 fonctions sont également purgées : les36 sont recoupées
physiquement dans quatre namespaces. Les5 982 artefacts antérieurs, fichiers
officiels, images, backend/web et référence sont conservés. Les budgets consommés
sont rétablis à32 instances,1 CPU et8 192 Mio, sans garde active. La recréation
attendue du contrôle change son CID et son démarrage, pas son image.

Les sources exécutables du replay restent celles livrées ; seules les deux
pages de contrat reçoivent les résultats dans l'index de sources. Les opérateurs
historiques conservent leurs limites. Aucun nouveau parcours visuel ni changement
produit/UI/manuel ; console, historique et régression complète008 restent ouverts.
SLS-074 conserve [~].


Ordre de réalisation persisté dans [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md#ordre-de-réalisation).
Premier checkpoint : [format et preuve du hash](FUNCTION_CODE_HASH.md), via le
vrai packager, extracteur et runtime Docker. Il laisse l’API en service inchangée ;
les trois étapes suivantes et tous les critères ci-dessous restent nécessaires.
La [preuve du composant](evidence/function-code-hash-dev-2026-11-09.json) passe
sept groupes rejoués et 45 de régression conservés sur deux époques de 222 sources,
produit/images identiques, avec neuf invocations
Docker. Deux essais arrêtés sont conservés séparément. Les contextes de build
sont bornés et prouvés ; douze fonctions supprimées/volumes purgés, 33 archives
de code conservées vérifiées. L’API et ses pointeurs actifs restent inchangés.

Contrat : [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md). Une nouvelle version n’est
créée que si le paquet exécutable a changé ; son tag public est son hash SHA256
canonique, vérifié côté serveur. Un upload identique réutilise la version, sans
doublon durable ni activation inutile. Les métadonnées sans effet du ZIP sont
exclues ; fichiers, dépendances et descripteur d’exécution sont pris en compte.
Un renommage conserve le hash ; un doublon reste admis au plafond de versions.

Sans tag, appeler la dernière version promue, mise à jour uniquement par
promotion/rollback explicite. L’upload prépare une version sans déplacer cette
cible, y compris au premier upload. Avec un hash, appeler exactement cette version
disponible, sans aucun repli si elle est archivée ou supprimée. Conserver les
droits Read, politiques origine/IP et authentification métier. Les URL
versionnées sont calculées avec SLS-066 et proposées dans SLS-071.
Create couvre la première publication et sa première promotion ; Update les suivantes et le cycle des
versions, y compris leur suppression individuelle. Delete reste la suppression
de la fonction. Le handler/runtime/image/événements viennent du hash sélectionné,
les ressources et configurations applicatives restent courantes.

Séparer publication et promotion pour un pilote, puis promouvoir ou revenir
à un ancien hash depuis la fiche de fonction. La CLI propose le même parcours
de code seul, sans mutation implicite des variables/secrets communs. Les clients
épinglés au hash stable continuent à l’appeler pendant le pilote. Configurations
et volumes restent attachés à la fonction ; le rollback concerne son code.

Prévoir archivage/restauration/suppression par version, protection de la cible
courante, consommateurs vivants et rétention explicite. Compter les ressources
et limites de toutes les versions ensemble ; isoler leurs pools d’exécution et
corréler le hash réellement exécuté dans logs et monitoring. Migrer les révisions
actuelles sans perte de pointeur, références ou données.

E2E : upload identique et ZIP différent de même contenu, modifications réelles,
renommage sans nouveau hash, doublon au plafond, handlers A/B distincts,
concurrence et déduplication, stable/pilote simultanés, appel sans tag, activation,
rollback sous appel vivant, droits/refus et aucune substitution de version,
archive/restauration/suppression, saturation entre versions, migration, réponse
perdue/SIGKILL et nettoyage physique. Parcours UI complets, captures et manuel
compilé requis. Dépendances : SLS-030/040/063 ; raccordements SLS-066/070 à SLS-073.

<a id="sls-075"></a>
## SLS-075 — Nommer la fiche d'archive sans ambiguïté après purge

Statut : [ ] — défaut mineur issu de la revue SLS-067, aucune défaillance de purge.
Nature : Corriger. Dépend de : SLS-065. Ordre : 6, avec la prochaine livraison de console.

Constat : le titre « Archives conservées » apparaît aussi au-dessus de l'état Purgée,
de zéro révision et zéro Mio. Source : `web/src/storage.jsx:96` ; capture contrôlée
`storage-ui-purged-mobile.jpg`, empreinte
`ae744c550e6e636e91163047b3768840f310d943d728a621102bee6121fa2285`. Le badge et le
reçu sont corrects.
Reconfirmation au gel9e1da70/image433da150 pendant le sixième078 : capture
storage-ui-purged-mobile.jpg SHA7c91c06207213fa4c8d830d83bf29b9a001f8c103f535a1adbc14c987af33a93.
Ce constat reste075 ; la pagination périmée distincte porte113, sans duplication.
Le titre neutre et le badge seul restent le choix prescrit, sans titre dynamique.


Critères d'acceptation :

- [ ] SLS-075.1 Titre neutre qui décrit la fiche (« Archive de la fonction ») ; états
  Conservée, Purge en cours et Purgée portés par le badge seul.
- [ ] SLS-075.2 Aucun changement de rétention, de commande ou d'allocation.

Tests exigés :

- Unitaire : rendu du titre pour les trois états.
- E2E depuis l'accueil réel : ouvrir une vraie archive après suppression de ses parents,
  lire titre et badge en état conservé, effectuer la purge réelle, relire titre, badge,
  volumes, code et reçu ; captures desktop et mobile, noms complets, focus.

À mettre à jour : manuel si le libellé y figure, `DESIGN_SYSTEM_APP.md` si le libellé y
est référencé. Nécessite une nouvelle image de console : preuve séparée des preuves
produit figées.

<a id="sls-076"></a>
## SLS-076 — Nom explicite des conteneurs de validation du code

Statut : [x] — nom explicite déployé en DEV sur19cfe884642a,57 groupes réels
réussis, trois fonctions du replay physiquement purgées et garde terminée.
Le premier essai échoué et son nettoyage restent distincts.

Le pilote `control/app/validator.py` emploie maintenant
`serverless-code-validator-<uuid>`. L’ancien p2-v ne décrivait pas sa
responsabilité pour un exploitant. Le changement porte uniquement sur le nom ;
le protocole, les labels, l’isolation et les délais restent identiques.

Employer `serverless-code-validator-<uuid>`, qui désigne le rôle et l’usage,
sans changer le label d’installation, le kind validation, l’unicité ni la
suppression de secours par nom. La réconciliation par labels doit continuer
à retirer les validateurs encore nommés p2-v après interruption. Le runtime,
les instances de fonctions, leurs noms et le calcul du hash de code ne changent
pas de responsabilité. Contrat : [Noms d’exploitation](DEPLOYMENT_NAMES.md#conteneurs-de-validation).

Cette correction reconstruit l’image du contrôle ; elle est séparée des preuves
074 dont le produit était figé. E2E réel : inspecter le nom/rôle d’un validateur
vivant issu d’un upload HTTPS, import réussi, import refusé et expiration,
puis absence du conteneur et de son canal ; éprouver une reprise d’un ancien
validateur p2-v réel après interruption. Recouper images, aliases/hashes,
pointeurs, données/cache et configuration conservés. Rejouer les campagnes
connexes et maintenir les notes du SPARK ; aucun changement de route ni secret.
Le [plan séquentiel](VALIDATOR_NAMES.md#plan-séquentiel-avant-code) est persisté
avant code : construction à contrôle actif, stable/données/cache, ancien
validateur produit par upload réellement interrompu, bascule gardée vers la
nouvelle image, trois issues d’import observées puis régressions36/12/5.
La garde utilise exclusivement Compose DEV et les deux fichiers officiels.
Le [premier essai](VALIDATOR_NAMES.md#premier-essai-et-correction-du-répertoire-de-travail)
produit bien un ancien validateur mais échoue à la remise en service du banc.
Sa fonction est purgée et son arrêt reste exclu. Le
[replay qualifié](evidence/validator-names-dev-2026-11-09.json) passe quatre
groupes ciblés et36/12/5 régressions, sur258 sources figées. Les imports
succès/refus/timeout portent le nouveau nom et sont supprimés ; l’ancien
validateur est repris par la nouvelle image après vrai SIGKILL. Cinq appels
conservent hash, cible, configuration et compteurs données/cache1 à5. Trois
fonctions du replay sont purgées, plus celle de l’arrêt recoupée séparément.
Les31 fichiers backend ne diffèrent que par validator ; assets web, fichiers
officiels et runtime de référence sont conservés. La garde est armée puis
libérée explicitement ; ses propres pannes/échéance ne sont pas revendiquées.
Les cinq pilotes maintenus et documents de résultat ont un relevé de livraison
distinct du gel258 des clients, avec provenance des corps réellement exécutés.
SLS-074 et la régression complète008 restent en cours.

## SLS-077 — Audit des secrets avant publication publique

Statut : [x] Audit initial effectué le 10 novembre 2026.

Demande : vérifier si des secrets empêchent une publication publique sur GitHub.
[Résultat et périmètre](PUBLICATION_SECURITY.md) : 475 fichiers de travail et
1 969 blobs historiques accessibles contrôlés ; aucun secret exploitable détecté,
valeurs connues absentes et aucun candidat correspondant aux quatre variables
confidentielles actives du SPARK. Les sessions restent dans .local ignoré.
Les coordonnées d'exploitation DEV sont suivies et restent à arbitrer avant
une éventuelle préparation publique. L'audit n'engage aucune publication ni
réécriture d'historique. Les limites de détection restent explicites.

### SLS-077 — Retirer le briefing privé avant publication

Statut : [x] Réalisé et vérifié le10 novembre2026.

Exclure docs/dev-spark.md par .gitignore, conserver sa copie locale et retirer
son chemin de tout l'historique et de toutes les références Git locales.
[Contrat](GIT_HISTORY_REWRITE.md) : sauvegarde privée, remappage des trois
lectures Git historiques, preuves datées conservées, comparaison des arbres,
absence du blob, collecte des objets inaccessibles et archive publique contrôlée.

Retrait vérifié sur263 commits et deux instantanés internes de type tree :
autres entrées et métadonnées conservées, briefing local intact et ignoré,
blob absent après collecte, trois sélecteurs historiques remappés et101fichiers
relus avec Git. [Preuve](evidence/git-history-private-briefing-removed-2026-11-10.json).


<a id="sls-078"></a>
## SLS-078 — Moteur de planification des crons

Statut : [x] — [campagne complète du 22 novembre](evidence/schedules-regressions-dev-2026-11-22.json),
49 campagnes / 543 groupes et 18 prérequis frais, sans cumul des essais antérieurs.
Gel `9e1da70`, 458 sources, image `433da150` : 117 captures ouvertes individuellement,
127 fonctions dans 35 namespaces recoupées après purge, dont 36 fonctions cron / 12 namespaces.
Worker terminé puis unité arrêtée et client joint ; quatre gardes de reprise,
trois coupures137 et 38 backend / quatre ressources HTTPS recoupés. Dix migrations,
intégrités/FK, configuration, référence et 5 982 originaux conservés ; manuel 18/74.
Rétention rapprochée sur trois manifestes/gzip/modules, sans rejeu ni nouveau
hash des captures scellées. Le détail daté ci-dessous conserve les étapes antérieures.
Les défauts 075/113, l’ancienne cause 111.1/.2, les expressions 080 et les
limites 091.2 / campagne globale 095 restent ouverts dans leurs unités.

Historique de reprise du21novembre : préalables103/104 livrés. Le
[contrat de campagne complète](SCHEDULE_REGRESSIONS.md) fixe49campagnes/543groupes
attendus,18prérequis et les recoupements des36fonctions cron supplémentaires.
Le lanceur est implémenté et relu ; qualification complète à produire.
Deux essais antérieurs restent exclus : premier refus avant SSO sur deux
contrats décalés, zéro groupe ; second15campagnes/272groupes puis préparation
execution-ui en échec. Les préalables107/106/105 sont maintenant livrés par
46/79/37groupes, chacun dans son époque. Nouveau worker et replay entier49/543,
18prérequis,450sources et état natif au repos ; aucun résultat complet revendiqué.

Dernier complément : [preuve de rétention à sept jours](evidence/schedule-retention-age-dev-2026-11-21.json) passe31groupes sur428sources41574c45,
image capturéec59 puis originauxb452restaurés. Source protégée puis retirée,
tir terminal/générations99/100 effacés, zéro nouvelle invocation ; six ciblés
et25communs,22captures inspectées.078.5 reste ouvert pour la campagne complète.

Premier checkpoint du 10 novembre — moteur, migration 009, lectures API et facette déployés en DEV ;
[premier checkpoint réel](evidence/schedules-checkpoint-dev-2026-11-10.json) : six groupes ciblés,
huit du manuel et huit publics. Le manuel conforme SLS-096 est clos ; les critères
restants de cette unité demeurent ouverts. Le [cycle des versions planifiées](evidence/schedule-versions-dev-2026-11-10.json)
qualifie séparément cinq groupes : pilote, promotion, retour de hash, retrait,
désactivation et suppression ; les appels admis conservent leur code.
La [grammaire numérique](evidence/schedule-calendar-dev-2026-11-10.json) est
qualifiée par cinq autres groupes sur le client final : huit tirs de la fenêtre,
douze refus et prévisions calendaires, trois fonctions purgées.
Nature : Développer. Dépend de : SLS-040 (admission), SLS-074 (cible promue).
Débloque : SLS-080, SLS-081, SLS-073. Ordre : 1.
Décision de reprise après112/IR-004 : sixième passage entier49/543+18 à préparer
sur l’image433da150 et le gel courant458sources ; cinq essais incomplets exclus.
Au point de décision, aucun résultat du sixième passage n’était encore acquis.
Contrat : [SCHEDULES](SCHEDULES.md).
Les [coupures et reprises réelles](evidence/schedule-recovery-dev-2026-11-10.json)
passent cinq groupes sur310 sources : garde indépendante, trois SIGKILL aux
frontières SQL, trois fenêtres manquées sans rattrapage, trois tirs suivants
réussis. Une fonction purgée physiquement ; quatre gardes terminées. Le
[plan et les résultats](SCHEDULE_RECOVERY.md) gardent les autres preuves ouvertes.
L'[admission réelle](evidence/schedule-admission-dev-2026-11-10.json) passe cinq
groupes sur313 sources : deux refus CPU sans invocation, deux files exclusives,
deadline après démarrage, recouvrement315s, deux extinctions mesurées et prochain
tir sans rejeu. Sept handlers réussis, cinq fonctions purgées ; les deux essais
antérieurs et leurs dix purges restent séparés. [Plan et résultats](SCHEDULE_ADMISSION.md).
La [suite RAM/version](evidence/schedule-memory-version-dev-2026-11-10.json)
passe cinq groupes sur316 sources : refus RAM sans invocation, changement A→B
après réception en file sans handler, allocation réelle8192Mio puis retour A,
compteur conservé et aucun rejeu. Quatre handlers réussis, trois fonctions purgées.
[Plan et résultats](SCHEDULE_MEMORY_VERSION.md).
SLS-078.4 est qualifiée par le recoupement ci-dessous ;.5 reste ouverte pour
la rétention réelle. Les preuves du plafond global sont liées ci-dessous.
Aucun changement produit, budget officiel ni nouvelle capture.
Les [files pleines](evidence/schedule-queues-dev-2026-11-10.json) passent quatre
groupes sur319 sources : plafonds réels16/128, deux tirs queue_full sans invocation,
144 réceptions déconnectées avant handler, deux succès HTTP puis deux planifiés.
Neuf fonctions purgées physiquement ; aucun budget modifié. [Plan et résultats](SCHEDULE_QUEUES.md).
Le [refus sous commande de cache](evidence/schedule-unavailable-dev-2026-11-10.json)
passe quatre groupes sur322 sources : garde commit/pending sous storage_io_error,
tir refused_unavailable sans invocation, même reçu terminé après restitution,
prochain tir et données conservés. Trois handlers réussis, une fonction purgée
et garde terminée. [Plan et résultats](SCHEDULE_UNAVAILABLE.md).
Le [maximum et la réutilisation](evidence/schedule-instance-reuse-dev-2026-11-10.json)
passent quatre groupes sur325 sources : HTTP non exclusif au maximum1, budgets
globaux libres et refus sans invocation ; minimum préchauffé puis deux mêmes
instances/CID à W+300, générations/configurations identiques. Quatre handlers
réussis, deux purges physiques. [Plan et résultats](SCHEDULE_INSTANCE_REUSE.md).
Restent rétention réelle et régression complète dans078.5 ; les critères.4/.7
sont qualifiés par leurs preuves rapprochées ci-dessous.
La [capture de rétention authentique](SCHEDULE_RETENTION.md) prépare le
vieillissement réel : invocation terminale liée à un tir non clos et témoin
HTTP antérieur, sauvegarde native privée ; aucune preuve des sept jours encore.
Premier essai de capture03:20UTC échoué avant handler sous traceur ; originaux
restitués et fixture purgée. Le correctif d’attachement après démarrage réel
est qualifié par la capture suivante.
La [capture5056167](evidence/schedule-retention-capture-dev-2026-11-11.json) passe
quatre groupes sur331sources : sauvegarde authentique, même contrôle repris,
fixture purgée. Épreuve d’âge au plus tôt le18 novembre2026 à03:30:26.355818UTC.
Les [pertes avant capture](evidence/schedule-retention-gate-losses-dev-2026-11-11.json)
passent huit groupes sur 351 sources, puis le
[nominal rejoué](evidence/schedule-retention-capture-regression-dev-2026-11-11.json)
quatre groupes sur le même client 20ffc09. Interruptions backup/copie et
régressions historiques du helper ont leurs preuves distinctes ci-dessous.
La [capture de témoins terminaux/retirés](SCHEDULE_RETENTION.md#capture-des-tirs-terminaux-et-générations-retirées)
réutilise les objets purgés de la vraie campagne CLI04:05UTC, sans mutation ni
nouveau service. [Capture39862b9](evidence/schedule-terminal-history-capture-dev-2026-11-11.json)
qualifiée par trois groupes réels sur335sources ; tir et générations99/100
conservés en privé avec5982 artefacts et images vérifiées. Borne commune d'âge :
18 novembre2026 à04:05:13.358459UTC ; vieillissement et replay restent à qualifier.
La [borne globale des invocations](INVOCATION_RETENTION_VOLUME.md) est spécifiée :
deux fonctions/5008 appels réels chacune,9984 observations avant borne puis10000
sur10016, installation isolée existante et garde1800s explicite. La
[preuve228a99c](evidence/invocation-retention-volume-dev-2026-11-11.json) passe
trois groupes réels sur337sources :10016 handlers, exacts10000 survivants,
deux purges et restitution complète. Rapport intégral compressé conservé.
Les [quatorze groupes de garde](evidence/invocation-retention-guard-regressions-dev-2026-11-11.json)
passent : onze restitutions120/partial et trois options/défaut900. La source de tir
non clos sous borne numérique a sa preuve distincte ci-dessous ; sept jours encore
ouverts et borne des tirs qualifiée ci-dessous.
La [préparation de la borne des tirs](SCHEDULE_FIRING_VOLUME.md) est spécifiée :
16 fonctions/16 déclarations chacune dans l'installation isolée existante,
256 premiers tirs authentiques puis sauvegarde native de générations actives.
Le futur replay après39 fenêtres réellement écoulées devra franchir10000 sans
injection SQL ni horloge remplacée. Client et lecteur natif avec jonction par
verrou hérité, régressions, replay numérique et interruption du lecteur qualifiés ci-dessous.
Premier [essai27221ea](evidence/schedule-firing-volume-capture-failed-dev-2026-11-11.json)
à06:00UTC échoué :2 succès/172 refus/82 failed sous
OperationalError, originaux restitués, aucune capture validée dans cet essai.
Observateur RO durable existant appliqué au poller ; cause exacte non établie.
Le [replay31b9102](evidence/schedule-firing-volume-capture-dev-2026-11-11.json)
passe quatre groupes sur340sources :256 tirs à06:15UTC,2 handlers/254 refus,
sauvegarde privée vérifiée,16 purges et restitution. Première éligibilité du
replay numérique le11 novembre09:30UTC. Les
[vingt groupes de restitution/options/sûreté](evidence/schedule-firing-volume-guard-regressions-dev-2026-11-11.json)
passent ensuite sur les mêmes340sources :11 reprises,3 options/défaut900 et6
avec consommateur/diagnostic indisponible/namespace étranger. Copie native sous
panne et replay sont qualifiés séparément ci-dessous ; aucune rétention déduite de la préparation.
Le [chargement/replay gardé](SCHEDULE_FIRING_VOLUME.md#chargement-gardé-de-la-copie)
est spécifié avant code : source scellée vérifiée avant arrêt, copie atomique
CONTROL en dernier, observation native de deux états au même curseur. Préflight,
refus avant mutation/éligibilité, pertes pendant copie/observation et replay
numérique implémentés ; qualification sous borne et pertes ci-dessous, mode
count qualifié séparément ci-dessous ; interruption du copieur initial également.
Premier essai0e29293 : huit refus et refus avant éligibilité passent, préflight
échoué avant publication CONTROL sur TypeError dans l'écriture du reçu ;
originaux restitués. Appel Path.open/opener corrigé dans le replay qualifié ci-dessous.
Essai7757065 : copie achevée, observation expirée sur le PID init Docker ;
3840 tirs réels et deux invocations initiales constatés avant restitution.
Sélection du processus Python unique, même cgroup que init, alignée sur
l'opérateur historique dans le replay qualifié ci-dessous. Cet essai reste échoué.
Essai dad8031 : contrôleur Python identifié, expiration25s après4 fenêtres
récupérées sur15. Attente waitpid bloquante et lectures RO réduites implémentées,
délais25/35/40 inchangés ; cet essai reste échoué et distinct du replay ci-dessous.
Le [replaye53b0d9](evidence/schedule-firing-replay-preflight-dev-2026-11-11.json)
passe neuf groupes sur342sources : refus avant mutation/éligibilité,4864 tirs
issus de18 fenêtres manquées, SSO/64 pages API, pertes copie/observateur et
restitutions indépendantes. Aucun handler nouveau ; source identique. Les trois
essais échoués restent séparés. Les
[vingt régressions historiques](evidence/schedule-firing-replay-guard-regressions-dev-2026-11-11.json)
passent ensuite sur les mêmes342sources ; count qualifié séparément ci-dessous, aucune rétention déduite du préflight.
La frontière de capture initiale est qualifiée séparément ci-dessous.
Le [préflight sur deux lots](evidence/schedule-firing-replay-two-batches-dev-2026-11-11.json)
passe trois groupes sur342sources e23e820 à09:15UTC :36 fenêtres manquées,
9472 tirs, deux invocations initiales seules,96 pages API et restitution jointe.
Observation9,94s sous25s, source inchangée ; aucune borne numérique qualifiée.
L'[interruption du copieur de capture](SCHEDULE_CAPTURE_INTERRUPTION.md) est
qualifiée par [cinq groupes](evidence/schedule-capture-interruption-dev-2026-11-11.json)
sur342sources dbb840b : nominal08:50UTC, perte du pilote pendant backup SQLite,
garde bloquée2,043s, SIGKILL du copieur à5,07s/40 puis jonctions et restitution
indépendante. Le premier essai c5fcb1d échoué reste séparé ; son groupe timeout
orphelin recevait SIGHUP, reproduit nativement et corrigé par foreground limité
au copieur. Les deux captures et la sortie partielle sont recoupées ; aucune
purge métier après perte. Les [vingt régressions](evidence/schedule-capture-guard-regressions-dev-2026-11-11.json) passent sur les mêmes342sources.
Le [mode count ef8cb3f](evidence/schedule-firing-retention-count-dev-2026-11-11.json)
passe trois groupes sur342sources inchangées :39 fenêtres réellement manquées,
10240→10000 tirs au même curseur09:30UTC, exacts240 plus anciens retirés,
640 tirs par fonction avant borne. Observation10,82s,112 pages API après SSO,
deux invocations initiales seules, source intacte et restitution nominale jointe.
La borne globale des tirs est qualifiée. La source protégée sous borne est qualifiée
ci-dessous ; sept jours et campagne complète restent requis,078.5 reste ouvert.
Le [discriminant des sources sous borne](INVOCATION_SOURCE_RETENTION_VOLUME.md)
est décidé avant code :10001 HTTP+source non close →10000 HTTP+source, puis
9999 HTTP+source après clôture. Les retraits des deux plus anciens ordinaires
prouvent les deux comptages. Installation isolée à2, garde2700 explicite pour
la charge/attente réelles, deux fonctions et aucune date/ligne fabriquée.
Client, handler original et observateur natif sont implémentés ; syntaxe contrôlée.
Nominal qualifié séparément ci-dessous ; pannes résiduelles et régressions restent requises, aucun succès déduit du seul code.
Les [cinq groupes de garde2700](evidence/source-retention-guard-options-dev-2026-11-11.json)
passent sur346sources : quatre refus avant mutation et programmation/restitution
réelles. Collecte initiale en échec de glob, rapport E2E terminé0 recoupé sans
rejeu ; aucune preuve de rétention ni d'expiration2700 déduite.
L'[essai source028d134d](evidence/invocation-source-retention-interrupted-dev-2026-11-11.json) est interrompu :
9730 réponses locales,9883 succès natifs avant retrait et aucun tir ; zéro groupe
retenu. Même346sources/images et originaux restitués, cause non établie.
Le [pilote durable](INVOCATION_SOURCE_RETENTION_VOLUME.md#essai-interrompu-et-pilote-durable)
est décidé avant code : tâche utilisateur locale transitoire, identifiants SSO
en mémoire par socket authentifié, mêmes clients et dépendances réels, relevés
avant/après et vérification indépendante du processus. Lanceur oneshot et finalisation durable implémentés, syntaxe contrôlée ; preuve
d'indépendance et nominal qualifiés ci-dessous. Aucun rejeu automatique de l'essai.
Le client de perte du worker est implémenté : SSO/appels réels, SIGKILL ciblé,
finalisation de l'échec et restauration recoupée en trois groupes. Ce scénario
et le nominal sont qualifiés ci-dessous ; les cinq groupes de garde existants
gardent leur époque346 distincte.
L'[essai worker200ea30](evidence/source-retention-worker-loss-failed-dev-2026-11-11.json) reste échoué :
511 réponses, indépendance et signal9 acquis, mais assertion exigeant deux
retraits Docker par la garde alors qu'elle trouve déjà zéro conteneur. Deux
réseaux/baux retirés, originaux et348sources conservés ; zéro groupe compté.
Correction spécifiée : inventaire réel avant faute, absence de tous les UUID
après restitution, retraits par acteur conservés séparément ; nouveau cas qualifié ci-dessous.
Le [nouveau cas de perte bbe9d0e](evidence/source-retention-worker-loss-dev-2026-11-11.json)
passe trois groupes sur348sources :512 réponses, indépendance réelle et SIGKILL9
finalisé comme échec, deux conteneurs/réseaux/baux observés puis absents, restitution
indépendante et sources/images identiques. Premier essai exclu. Le
[nominal d860cc5](evidence/invocation-source-retention-volume-dev-2026-11-11.json) passe trois autres groupes
sur les mêmes348sources :10001 HTTP et un cron,10002→10001 avec tir strictement
non clos puis10000 après clôture. Deux plus anciens HTTP exactement retirés,
source inchangée,5001 observations par fonction avant borne, observation12,34s.
Deux purges publiques et restitution nominale jointe ; worker success/Code1/Status0
réel conservé puis arrêté. La source protégée sous borne est qualifiée ; âge,
pannes propres résiduelles et campagne complète restent ouverts,078.5 non clôturée.
Le [replay d'âge](RETENTION_HISTORY_REPLAY.md) a son contrat explicite : les deux
captures canoniques sont clonées uniquement dans une fenêtre exclusive, image
capturée, garde120, observation avant santé et contrôles stricts d'identité à
chaque démarrage/restitution. Les
[treize groupes](evidence/retention-history-replay-preflight-dev-2026-11-11.json)
passent sur351sources identiques : huit refus d'options et deux refus d'âge en trois groupes,
les deux préflights en six groupes avec vrai SSO/API et restitutions nominales.
Source9,859s/149251 stops/sept frontières fdatasync ; deux témoins conservés et même
tir clos sans nouveau handler. Tir terminal et générations retirées conservés
dans l'autre copie. [Quatre essais échoués](evidence/retention-history-replay-failed-dev-2026-11-11.json)
exclus ; métadonnées historiques et filtre des lectures corrigés et vérifiés.
Les deux pertes avant CONTROL et après attache passent quatre groupes
supplémentaires au client3125ad1, sur les mêmes351sources ; gardes120 réellement
indépendantes et originaux/captures conservés. Les [dates natives](evidence/retention-history-loss-timings-dev-2026-11-11.json)
confirment les absences sousD+240 et restitutions sousD+270, sans groupe ajouté.
Le [refus du contexte cloné](evidence/retention-history-namespace-scope-dev-2026-11-11.json)
passe quatre groupes au client9f3e7da, dont deux préflights rejoués : namespace
supplémentaire présent après refus, même conteneur temporaire conservé et original
arrêté, retrait API de la seule fixture puis restitution explicite.351sources
avant/après, deux clients seuls changés par rapport aux treize groupes ; helper
et images inchangés. Réconciliation nominale réellement exercée, perte de
réponse HTTP non provoquée. Les
[vingt-cinq régressions finales](evidence/retention-history-guard-regressions-dev-2026-11-11.json)
passent sur 351 sources au client f908640 : 11 groupes de fenêtre/partiel, 3 options
et défaut 900, 5 options 2700, 6 consommateur/diagnostic indisponible/namespace.
Originaux/images conservés, gardes/pilotes joints ; contrôles finaux : 2 services sains,
actifs à zéro et 5 982 artefacts. Les trois essais interrompu/échoués restent
[eux](evidence/retention-history-guard-interrupted-dev-2026-11-11.json)
[aussi](evidence/retention-history-guard-failed-dev-2026-11-11.json)
[exclus](evidence/retention-history-sigkill-confirmation-failed-dev-2026-11-11.json).
Confirmation pidfd puis /proc renforcée, reçu conservé ; les deux groupes du
[ciblé](evidence/retention-history-sigkill-confirmation-dev-2026-11-11.json)
ne sont pas recomptés avec le SIGKILL de la matrice. Aucun âge réel avant
le 18 novembre ; 078.5 reste ouverte.

Restes ciblés de 078.5, avant clôture et campagne complète :

- [x] Capture initiale `schedule-recovery-operator.py` : pannes propres et
  régressions de ce helper distinct, non couvertes par la matrice de
  `storage-legacy-environment.py`.
  [EOF et SIGKILL après gated](evidence/schedule-retention-gate-losses-dev-2026-11-11.json)
  qualifiés par huit groupes au client 20ffc09 : même contrôle sans redémarrage,
  TracerPid réel puis zéro, garde indépendante 80 s, mêmes UUID/dates et deux
  purges physiques. Le [nominal](evidence/schedule-retention-capture-regression-dev-2026-11-11.json)
  passe quatre groupes sur les mêmes 351 sources/images ; trois refus CLI
  précoces sont vérifiés séparément. Les captures canoniques restent conservées.
  Les [cinq régressions historiques](evidence/schedule-recovery-regression-dev-2026-11-11.json)
  passent sur 351 sources 7ed2abe : trois coupures 137, trois tirs suivants,
  quatre gardes jointes et une purge physique. Worker systemd terminé 0,
  son lanceur expiré à 20 s conservé séparément, aucun rejeu. Les quatre
  handlers réussis incluent un témoin initial ; un appel lié est interrompu
  avant démarrage. Les interruptions backup/copie sont qualifiées ci-dessous.
  [Interruptions de copie](SCHEDULE_RETENTION.md#interruptions-pendant-sauvegarde-et-copie)
  spécifiées : callback SQLite réel ou copy2 réel, SIGSTOP puis garde 80 s,
  reçu par FD préouvert sous root et dossier partiel conservé. Les
  [douze groupes bca96ab](evidence/schedule-retention-copy-losses-dev-2026-11-11.json)
  passent sur 351 sources/images identiques : backup16/4 837 pages,
  copy2 1/5 990 fichiers, deux helpers arrêtés puis tués/joints par gardes80,
  TracerPid0 et même contrôle sans redémarrage. Huit groupes de panne puis
  quatre du nominal, six handlers réussis et trois purges physiques. Six refus
  CLI séparés, dossiers partiels protégés et captures canoniques inchangées.
  Les cinq historiques7ed2abe conservent leur époque ; le rejeu sur le helper
  final est qualifié ci-dessous. La campagne complète reste requise pour078.5.
  Rejeu historique préparé avec le même client, dans un oneshot utilisateur
  local indépendant du terminal ; [contrat de suivi](SCHEDULE_RECOVERY.md#exécution-indépendante-du-terminal).
  Le [rejeu historique final](evidence/schedule-recovery-detach-regression-dev-2026-11-11.json)
  passe cinq groupes au gel355 ef98a9f, identique au bounded et aux quinze
  consommateurs : trois coupures137, trois échéances manquées sans invocation,
  tir claimed sans invocation et tir linked interrompu avant handler, puis trois
  tirs suivants réussis sans rejeu. Quatre gardes terminées et une purge physique.
  Lancement --no-block accepté, même worker3016607/naissance64482164 confirmé
  vivant puis réellement terminal0, reçu conservé avant arrêt. Deux services
  sains, actifs/baux nuls,5982artefacts et captures canoniques inchangées.
- [x] Observateur source sous borne : [refus réel après attachement](evidence/invocation-source-observer-refusal-dev-2026-11-11.json)
  qualifié par deux groupes au commit 956498a, sur 351 sources figées. Deux
  handlers HTTP/cron running, tir et UUID recoupés ; TracerPid 471960 puis zéro
  du même contrôle 470002/naissance, mémoire et lecteur fermés. Helper terminé
  1 après son refus naturel, restitution nominale jointe et absence physique
  des deux conteneurs/réseaux/baux. Aucun succès de rétention numérique ajouté.
- [x] Fermeture du lecteur lorsque detach lui-même échoue : finally renforcé,
  preuve native [décidée avant code](INVOCATION_SOURCE_RETENTION_VOLUME.md#fermeture-du-lecteur-malgré-une-erreur-native-de-detach).
  [Premier essai34b8815 échoué](evidence/source-observer-detach-failed-dev-2026-11-11.json) :
  Docker pause seul laisse detach réussir, aucune exception observée. Zéro groupe
  qualifié ; originaux restitués. Décision révisée : vrai SIGSTOP au point
  optionnel d’entrée dans wait5, reçu d’échéance réel, SIGCONT indépendant après
  échéance+.25 ; erreur réelle de wait, lecteur fermé, mort/Trace0 puis dégel.
  [Quatre groupes b5f0825](evidence/source-observer-detach-failure-dev-2026-11-11.json)
  qualifiés sur355sources : vraie erreur detach5,255021s, erreur primaire
  conservée, mémoire/lecteur fermés, masque[] restitué après SIGCHLD17 bloqué.
  Acteur reprend après échéance+.25, constate mort/Trace0 puis dégèle sans
  secours ; neuf contrôles physiques et sept exacts passent, refus sans option
  rejoué, originaux restitués. Les quinze groupes consommateurs courants
  et le nominal numérique complet sont qualifiés ci-dessous.
- [x] Observateur source : expiration de l'alarme de 35 s et coupure extérieure à 40 s
  avec processus/verrou joints et ressources physiques restituées.
  [Contrat décidé avant code](INVOCATION_SOURCE_RETENTION_VOLUME.md#pannes-propres-de-lalarme35-et-de-la-commande40) :
  deux vrais handlers, SIGSTOP après attache/reçu et avant assertion10002 ;
  acteur indépendant SIGCONT après vraie alarme35+.5 ou suspension jusqu'au
  vrai timeout40. Statuts opérateur/wrapper/helper distincts, TracerPid0 mesuré
  avant retrait du contrôle, nettoyages et ressources recoupés. Code implémenté :
  portes SIGSTOP, acteur indépendant, reçu de commande et deux options du client ;
  [Six groupes e45126b](evidence/source-observer-deadlines-dev-2026-11-11.json)
  qualifiés sur354sources/images identiques :35,683720s avec TimeoutError et
  lecteur fermé ;40,009839s avec vrai wrapper124, KILL rapporté, opérateur
  absent et TracerPid0 avant retrait. Acteurs joints, union initiale/tardive
  physiquement absente (neuf contrôles existants et sept contrôles exacts),
  puis refus sans option rejoué. Trois refus CLI séparés, zéro groupe ajouté.
  Les valeurs35/40 restent inchangées ; aucun waitstatus137 du fils déduit.
  [Premier essai ad70d47 échoué](evidence/source-observer-deadline-failed-dev-2026-11-11.json),
  zéro groupe qualifié : alarme35,719s et restitution acquises, mais assertion
  d'inventaire rejetant les remplacements légitimes du minimum1. Correction
  décidée dans le contrat : identités natives initiales et tardives corrélées
  aux mêmes fonctions/révisions, puis absence physique de leur union. Code
  corrigé et qualifié par le replay ci-dessus. Les neuf contrôles
  physiques ne sont pas atteints dans l'essai échoué.
  [Matrice f22d217 arrêtée](evidence/source-observer-timeout-status-failed-dev-2026-11-11.json) :
  35 passe,40 retourne réellement124 après40,014s mais le client attend137.
  Zéro groupe qualifié dans ce bilan ; statut wrapper distinct de celui du fils,
  identité du binaire conservée et même commande rejouée dans la preuve finale.
- [x] Attente native partagée de 25 s : défaut reproduit puis borne corrigée
  qualifiée sur un vrai contrôle temporaire gelé, avec dégel indépendant confirmé
  avant detach. Le waitpid bloquant dépassait sa borne ; la correction attend
  de vrais SIGCHLD avec sigtimedwait. Une preuve de ce composant
  ne vaut pas preuve de toute la boucle de rétention.
  [Banc décidé avant code](INVOCATION_SOURCE_RETENTION_VOLUME.md#mesure-de-lattente-native-sans-événement) :
  contrôle temporaire vide réel, Docker pause après attache, WNOHANG sans statut,
  vraie attente25s et dégel indépendant28s confirmé avant detach, alarme35 et
  commande40 inchangées. Reproduction et correction sont qualifiées ci-dessous.
  Banc implémenté (client `native-observer-deadline.mjs` modes reproduce/bounded,
  opérateur dédié et commande strictement limitée au helper instance-limit120).
  Syntaxes contrôlées ; reproduction réelle et borne isolée qualifiées ci-dessous.
  [Reproduction c64fdd7](evidence/native-observer-deadline-reproduce-dev-2026-11-11.json)
  trois groupes sur353sources : vrai délai25 dépassé à28,202s après dégel,
  alarme35 non expirée. Nettoyage/acteur joints et originaux restitués. Décision
  de correction bornée par vrais SIGCHLD/sigtimedwait, sans changer l'alarme35 ;
  correction implémentée avec masque restauré dans finally. Les
  [trois groupes bounded46e216d](evidence/native-observer-deadline-bounded-dev-2026-11-11.json)
  passent sur353sources/images identiques :25,000182s, masque[] identique,
  handler35 inchangé/reste34,902→9,902s, acteur joint et originaux restitués.
  Les [onze groupes consommateurs96dcca0](evidence/native-observer-consumers-dev-2026-11-11.json)
  passent ensuite sur les mêmes353sources/images : borne des tirs10 496→10 000
  en13,526s/exacts496retirés, préflights source9,189s et terminal0,005624s,
  refus après attache avec lecteur fermé/TracerPid0 et deux consommateurs
  physiquement retirés. SSO/API et quatre restitutions joints ; les deux
  captures canoniques sont conservées. Le nominal numérique complet de la
  classe courante a sa preuve355 distincte ci-dessous ; l'époque353 reste conservée.
  Après le point de faute detach, [bounded courant](evidence/native-observer-detach-bounded-dev-2026-11-11.json)
  repasse trois groupes sur355sources :25,000300s, masque/alarme conservés,
  dégel avant detach et restitution. Les [quinze groupes courants](evidence/native-observer-detach-consumers-dev-2026-11-11.json)
  passent au même gel355 : six campagnes count/préflights/refus/35/40,
  10 496→10 000/exacts496 retirés en12,758s, témoins conservés,35,679s/1 et
  40,010s/124 avec nettoyages joints. Six nouveaux handlers distincts des copies.
  Historique final qualifié ci-dessus. Le [nominal courant](evidence/invocation-source-retention-detach-volume-dev-2026-11-11.json)
  passe trois groupes6de2a86, mêmes355sources/images que bounded et historique :
  10001 HTTP et un cron,5001 observations par fonction,10002→10001 tant que le
  tir reste non clos puis10000 après clôture. Exacts deux plus anciens HTTP
  retirés, source strictement conservée ; observation12,410436s. Deux purges
  publiques et restitution nominale jointe. Même worker3440900/naissance64743860
  réellement terminal0 puis arrêté ; collectes natives et captures fraîches
  après finalisation,2services sains, actifs/baux nuls,5982artefacts et aucune garde.
  Les anciens essais restent distincts ; ce résultat ne qualifie pas sept jours.
- [x] Âge réel des deux sources : [replay du21novembre](evidence/schedule-retention-age-dev-2026-11-21.json),
  six groupes ciblés à10:50/10:55UTC, plus25communs. Deux gardes/pilotes joints,
  sources scellées inchangées, source protégée puis supprimée après clôture,
  tir terminal et générations99/100 supprimés ; aucun nouveau handler.
- [x] Campagne complète de non-régression raccordée et exécutée sur010 :
  [49 campagnes / 543 groupes + 18 prérequis](evidence/schedules-regressions-dev-2026-11-22.json),
  nouveaux clients de planification et bancs historiques préservés ; 117 captures
  inspectées, clôture native et purges recoupées sur le même worker terminé.

Le recoupement078.4 avait identifié une preuve non discriminante : concurrence
planifiée isolée du maximum individuel et du stockage exclusif. Le scénario
qualifié ci-dessous résout ce manque avant clôture du critère.4.
Le [scénario discriminant](SCHEDULE_CONCURRENCY.md) compare concurrence1/2 à
maximum3, stockage partagé et budgets libres, pendant deux vrais HTTP à W.
Client `e2e/schedule-concurrency.mjs` implémenté ; contrôle de syntaxe réussi,
premier essai03:50UTC échoué sur l'observation après fin du handler, deux purges
physiques réussies. Observer désormais le handler cron pendant cinq secondes
et conserver les relevés avant assertion : [replay08d1512](evidence/schedule-concurrency-dev-2026-11-11.json)
qualifié par quatre groupes sur333sources à03:55UTC, quatre handlers et deux purges.
Le [raccordement CLI](SCHEDULE_ADAPTER.md) de.7 est implémenté dans
`e2e/adapter-schedules.mjs` et [qualifié](evidence/adapter-schedules-dev-2026-11-11.json) :
quatre groupes sur334sources, plan/deploy/deux promotions et un vrai tir04:05UTC ;
déclaration désactivée sans appel, deux purges physiques. Critères.4 et.7 qualifiés
après recoupement ci-dessous ; rétention et régression complète restent ouvertes.
La [console des planifications](evidence/schedule-console-dev-2026-11-10.json)
passe19 groupes sur326 sources : trois ciblés, huit du manuel et huit publics
rejoués. Six handlers réels22:10UTC, pages5+1, vide, nom63, clavier/focus et mobile.
Le vrai401 retire cartes et pagination ; Réessayer retrouve la même seconde page.
Le [plan et la reproduction](SCHEDULE_CONSOLE.md) conservent le défaut sous401
sur l'imageb9 et les essais du banc, hors total courant. Correctif24d81c7, image
c59b8616 et manuel conforme16 chapitres/56 paragraphes.31 captures recoupées :
17 inspections personnelles et14 références SHA. Deux fonctions purgées ;34
backends,5982 artefacts, services et fichiers officiels conservés pendant replay.
SLS-078.6 est qualifiée ; rétention et régression complète
gardent l’unité ouverte.

Le [plafond global en installation isolée](evidence/instance-limit-admission-dev-2026-11-11.json)
est maintenant qualifié séparément : quatre groupes, tir refusé01:35UTC sans
invocation puis succès01:40UTC sans rejeu. Son [raccordement final](evidence/instance-limit-public-integration-dev-2026-11-11.json)
réussit à02:40/02:45UTC, avec restitutions et régression historique ; SLS-099
est close. Les critères.4/.5 ne sont pas clôturés sur ce seul complément.

Résultat attendu : les planifications du manifeste s'exécutent réellement, par fenêtres
de 5 minutes, sur la version promue ; un moteur unique servira aussi les jobs de console.

Critères d'acceptation :

- [x] SLS-078.1 Preuve : [checkpoint réel](evidence/schedules-checkpoint-dev-2026-11-10.json). Réveil aux frontières UTC de 5 minutes ; un créneau nominal de la fenêtre
  écoulée est lancé à la frontière suivante ; jamais en avance ; retard consigné.
- [x] SLS-078.2 Preuve : [calendrier numérique](evidence/schedule-calendar-dev-2026-11-10.json). Plusieurs créneaux d'une même fenêtre fusionnés en un tir (`coalesced`) ;
  syntaxe cinq champs (listes, plages, pas, `*`, dimanche 0 ou 7) ; jour du mois OU jour de
  la semaine quand les deux sont restreints.
- [x] SLS-078.3 Preuve : [cycle réel des versions](evidence/schedule-versions-dev-2026-11-10.json). Cible = version promue (pilote jamais déclenché) ; promotion, retour à un hash
  ou retrait de la planification remplace l'ensemble à l'instant de la décision ;
  `enabled: false` sans tir ; fonction désactivée, supprimée ou archivée sans tir.
- [x] SLS-078.4 Preuves rapprochées : [admission commune](SCHEDULES.md#admission-commune-qualifiée), dernier discriminant [concurrence](evidence/schedule-concurrency-dev-2026-11-11.json). Événement HTTP v1 synthétique `POST /`, corps `{}`, en-têtes
  `x-p2enjoy-trigger` et `x-p2enjoy-schedule-slot`, sans jeton ni politique origine/IP,
  par la même admission que les appels HTTP (budgets, file, concurrence, verrou de
  stockage, deadline, extinction).
- [x] SLS-078.5 [Campagne complète et rétention rapprochée](evidence/schedules-regressions-dev-2026-11-22.json). Enregistrement durable de chaque tir (états `claimed`, `dispatched`,
  `succeeded`, `failed`, `skipped_downtime`, `skipped_overlap`, `refused_*`) ; réclamation
  avant envoi ; aucun rejeu ni rattrapage ; recouvrement évité ; refus de capacité consigné
  sans retry.
- [x] SLS-078.6 Preuve : [console et reprise401→200](evidence/schedule-console-dev-2026-11-10.json), lectures Read du checkpoint initial. L'invocation porte `trigger: schedule`, l'origine, l'expression et le créneau ;
  la fiche de fonction affiche les planifications actives (prochain tir, dernier résultat,
  état) en lecture avec le droit Read.
- [x] SLS-078.7 Preuve : [CLI et tir réel](evidence/adapter-schedules-dev-2026-11-11.json). Adaptateur : `plan` et `deploy` avertissent par fonction planifiée tant que le
  moteur n'est pas déployé ; l'avertissement et la phrase du manuel disparaissent avec le
  déploiement du moteur, dans le même changement.

Tests exigés :

- Unitaires : calcul des créneaux, fenêtres, fusion, grammaire, OU jour/semaine.
- API / intégration : table des tirs, droits par requête directe, migration, reprise
  après redémarrage.
- E2E du moteur sur l'horloge réelle (détail dans
  [SCHEDULES](SCHEDULES.md#preuves-e2e-attendues)) : `*/5`, `* * * * *`, instant précis,
  pilote/promotion/retour de hash, désactivation et suppression, SIGKILL du contrôle autour de
  la réclamation, arrêt sur plusieurs fenêtres, recouvrement, saturation, stockage exclusif
  occupé, parcours UI et captures. Tous les objets d'un scénario sont créés avant la
  frontière suivante.
- La qualification des expressions exactes `0 21 * * 1-6` et `0 7-20 * * 1-6`
  dans les fixtures des treize fonctions relève de
  [SLS-080.3, .7 et .8](#sls-080), après SLS-078 et SLS-083. Cette exigence
  reste ouverte ; les preuves et la clôture du moteur ne la déclarent pas
  satisfaite.

À mettre à jour : `SCHEMA.md` et migration, seed (fonctions planifiées), manuel (retrait de la
limite), `DESIGN_SYSTEM_APP.md`, `DEPLOYMENT.md`, parité (CRON), README.

<a id="sls-079"></a>
## SLS-079 — Exploitation complète et reproductible

Statut : [ ] — contrat défini ([OPERATIONS](OPERATIONS.md)) ; informations dispersées dans les
comptes rendus de campagne, guide absent.
Nature : Développer (documentation rejouée). Dépend de : unités 1 à 10, pour rejouer l'état
stable le plus tardif. Ordre : 11.

Résultat attendu : un seul guide pour une personne qui n'a pas suivi le développement.

Critères d'acceptation :

- [ ] SLS-079.1 Les onze chapitres de [OPERATIONS](OPERATIONS.md#contenu-exigé-du-guide) rédigés :
  prérequis, configuration, installation, mise à jour, reprise, sauvegarde, secrets,
  persistance, intégration au SPARK, diagnostic, purge.
- [ ] SLS-079.2 Tableau de **toutes** les variables et secrets (rôle, format, obligatoire, défaut,
  exemple) comparé mécaniquement au code qui les lit.
- [ ] SLS-079.3 README ramené à une porte d'entrée ; notes de la cellule du SPARK réduites à leur
  usage ; récits de campagne déplacés au journal, jamais supprimés.
  Relevé du12novembre : notes actives encore au schéma005/manuel11chapitres,
  propositions du dépôt au schéma009/manuel15chapitres et anciens contrôles.
  Actualisation minimale des trois propositions après071 (010,18/74, image96e5
  et testeur) ; adoption non revendiquée. La réduction des récits reste à faire.
  Actualisation minimale112 : image433da150 déployée, qualification82acquise,22captures inspectées ;
  schéma010 et manuel18/74inchangés, propositions seules sans adoption active.
  Relevé du22novembre pendant la livraison115 : neuf liens relatifs préexistants sont
  cassés dans les trois sources `qualification/spark-notes/{README,INSTALL,CONTRIBUTORS}.md`.
  Chacune vise `docs/evidence/function-version-unknown-first-dev-2026-11-09.json`,
  `docs/evidence/function-version-state-transport-dev-2026-11-09.json` et
  `docs/evidence/function-version-publication-regressions-dev-2026-11-09.json` depuis
  le répertoire des notes. Corriger leur destination dans la restructuration des notes,
  puis vérifier les liens dans leur contexte de consultation réel sur le SPARK.
- [ ] SLS-079.4 Guide rejoué sur une installation temporaire distincte : installation depuis
  zéro, mise à jour, redémarrage forcé, sauvegarde, destruction partielle, restauration,
  purge ; au moins cinq symptômes du tableau de diagnostic provoqués pour de vrai.
- [ ] SLS-079.5 Un relecteur qui n'a pas suivi le développement exécute les chapitres 3 à 6 sans aide.

Tests exigés : le rejeu est la preuve ; chaque commande est exécutée ou, si destructive,
exécutée dans l'installation temporaire ; un test automatique compare le tableau de
configuration au code ; aucune preuve par relecture. Si l'autorité du SPARK ne permet pas
l'installation temporaire, le blocage est nommé ici ([Décisions](#décisions-et-autorités-en-attente)),
sans preuve partielle.

À mettre à jour : README, `DEPLOYMENT.md`, `PLATFORM_DEV.md`, notes SPARK, `DAT.md`, manuel si
l'exploitant y renvoie.

<a id="sls-080"></a>
## SLS-080 — Compatibilité du projet de référence

Statut : [~] — audit et matrice faits le 10 novembre 2026
([REFERENCE_COMPATIBILITY](REFERENCE_COMPATIBILITY.md)) ; adaptations, fixtures et preuves
E2E à réaliser.
Nature : Développer. Dépend de : SLS-078, SLS-083. Ordre : 5. Portée du reste de SLS-030.

Résultat attendu : prouver, avec des fixtures originales déployées et invoquées, qu'un
projet de la forme de la référence se publie et s'exécute sur la plateforme.

Critères d'acceptation :

- [ ] SLS-080.1 CPU dérivé du palier mémoire Scaleway (70 mvCPU par 128 Mio) quand `p2enjoy.cpu`
  est absent ; `p2enjoy.cpu` l'emporte.
- [ ] SLS-080.2 Avertissements de l'adaptateur : options ignorées, conversion Node 20 vers 24,
  planifications ; guide d'intégration client (adresse de base, `/invoke/{UUID}`,
  `X-Serverless-Token`, build Node 24, origines, abandon de `privacy`/`httpOption`/
  `custom_domains`).
- [ ] SLS-080.3 Fixtures originales à treize fonctions fidèles aux contrats (mémoires, délais,
  minima et maxima, `provider.secret`/`env`, trois options ignorées, `node20` converti,
  les deux planifications exactes `0 21 * * 1-6` et `0 7-20 * * 1-6`, handlers `(event, context, cb)` avec `JSON.parse(event.body)`, CORS
  construit par le handler, `OPTIONS`, appels entre fonctions avec jeton). Jamais de copie
  du client.
- [ ] SLS-080.4 Publication complète par `adapter deploy` avec les deux drapeaux, rapport lu ;
  mise à jour, rollback, pilote, redéploiement ; budgets CPU/RAM/instances constatés avant
  et après, y compris le refus 409 d'un budget insuffisant.
- [ ] SLS-080.5 Invocation de chaque fonction par l'adresse copiée de la console, jeton Read,
  origine autorisée depuis un vrai navigateur (préflight sans `Access-Control-*` du handler),
  autre origine ou IP refusée, `Authorization` métier reçu par le handler.
- [ ] SLS-080.6 Accès sortant réel vers des dépendances réelles démarrées pour l'essai (HTTP,
  PostgreSQL, courrier) puis purgées ; l'instance n'atteint ni le contrôle, ni l'agent de
  stockage, ni le socket Docker.
- [ ] SLS-080.7 Les deux planifications exactes `0 21 * * 1-6` et
  `0 7-20 * * 1-6` tirent réellement aux frontières UTC attendues sur la
  version promue de leurs fixtures originales, avec `POST` et corps `{}`.
  Les expressions enregistrées, créneaux, tirs et invocations des handlers
  sont recoupés ; aucune expression accélérée ni horloge modifiée ne les
  remplace.
- [ ] SLS-080.8 `plan` exécuté en lecture seule sur les manifestes réels de la référence et
  comparé aux fixtures, y compris les deux expressions de planification
  exactes, pour que celles-ci restent fidèles.

Tests exigés : campagne E2E exécutée **seule** (budgets partagés), captures des écrans
concernés sur ordinateur et mobile. Un budget de cellule insuffisant est une proposition
`.?` au propriétaire du SPARK, nommée si elle bloque.

À mettre à jour : `REFERENCE_COMPATIBILITY.md`, manuel (adaptateur), parité, `DEPLOYMENT.md`.

<a id="sls-081"></a>
## SLS-081 — Jobs serverless de la console

Statut : [ ] — contrat défini ([SERVERLESS_JOBS](SERVERLESS_JOBS.md)), rien d'implémenté.
Nature : Développer. Dépend de : SLS-078, SLS-072. Ordre : 4.

Demande du responsable : exécuter une fonction avec un payload fixe et quelques gabarits
composés dans l'UI, selon une expression crontab contrôlée par fenêtres de 5 minutes. À ne
pas confondre avec les Serverless Jobs en conteneur ([SLS-088](#sls-088)).

Critères d'acceptation :

- [ ] SLS-081.1 Définition par fonction : nom unique, description, activation, expression UTC,
  endpoint POST de la version promue (défaut `/`), payload JSON de 64 Kio au plus ;
  16 jobs par fonction, 512 par installation ; `updated_at` en `If-Match`.
- [ ] SLS-081.2 Gabarits : liste fermée, remplacés dans les valeurs texte, valeur exacte typée,
  `{{{{` littéral, gabarit inconnu refusé à l'enregistrement, aucun secret ni expression.
- [ ] SLS-081.3 Onglet Jobs : modèles d'expression, phrase en français, cinq prochains tirs
  (nominal et effectif), éditeur JSON validé en direct avec compteur, palette de gabarits
  insérable souris et clavier, aperçu du corps exact, choix de l'endpoint ; erreurs serveur
  près du champ sans perte de saisie.
- [ ] SLS-081.4 Liste par fonction et par service : nom, phrase, état, prochain tir, dernier
  résultat ; états vide, erreur, chargement, longs noms, mobile.
- [ ] SLS-081.5 Historique des tirs au vocabulaire Scaleway (`succeeded`, `failed` avec raison,
  `quota_exceeded`, `skipped_*`) avec lien vers l'invocation et ses journaux ;
  `refused_endpoint` et job « à corriger » si une promotion retire l'endpoint.
- [ ] SLS-081.6 « Exécuter maintenant » : tir `manual` sous les mêmes admissions, 409 pendant un
  tir du même job, droit Update.
- [ ] SLS-081.7 API (liste, création, lecture, modification, suppression, exécution, historique,
  prévisualisation sans enregistrement) ; droits Read/Update côté serveur ; mutations
  auditées.

Tests exigés :

- Unitaires : gabarits, typage, grammaire, aperçu des tirs.
- API / intégration : refus (JSON invalide, gabarit inconnu, 64 Kio + 1, 17e job, cron hors
  grammaire, 409 de version, doublon), droits par requête directe (Read, jeton d'une autre
  fonction, session non administratrice), aucun secret dans les réponses ni journaux.
- E2E depuis l'accueil réel (liste complète dans
  [SERVERLESS_JOBS](SERVERLESS_JOBS.md#preuves-e2e-attendues)) : création par l'UI, corps exact
  reçu au tir, aucun tir en avance, fusion, modification et suppression prises en compte,
  promotion et retour de hash, SIGKILL, saturation, captures desktop et mobile.

À mettre à jour : `SCHEMA.md` et migration, seed (jobs de démonstration), manuel,
`DESIGN_SYSTEM_APP.md` (éditeur, palette, liste de tirs), `DEPLOYMENT.md`, parité.

<a id="sls-082"></a>
## SLS-082 — Parité fonctionnelle avec Scaleway Serverless

Statut : [~] — matrice sourcée relevée le 10 novembre 2026
([SCALEWAY_PARITY](SCALEWAY_PARITY.md)) ; écarts portés par les unités ci-dessous.
Nature : Qualifier (suivi). Ordre : suit les unités qu'elle référence.

Demande du responsable : répliquer toutes les fonctionnalités de Scaleway Serverless.

Critères d'acceptation :

- [ ] SLS-082.1 Chaque ligne de la matrice est Livré, Sans objet ou Écart assumé avec preuve E2E,
  ou portée par une unité ouverte dont le blocage externe est nommé.
- [ ] SLS-082.2 La matrice est mise à jour dans le même changement que chaque livraison.
- [ ] SLS-082.3 La documentation de Scaleway est revérifiée à chaque revue de la matrice.

Unités qui portent les écarts : SLS-070 à 073 (code, test, journaux, métriques), 078 et 081
(déclencheurs), 083 (limites, en-têtes), 084 (runtimes), 085 (messages), 086 (trafic),
087 (conditions d'accès), 088 (jobs en conteneur), 097 (API documentée).

<a id="sls-083"></a>
## SLS-083 — Aligner les limites et les en-têtes sur Scaleway

Statut : [ ] — écarts relevés ; contrat à compléter dans [EXECUTION](EXECUTION.md) avant le code.
Nature : Développer. Dépend de : SLS-040. Débloque : SLS-080, SLS-084. Ordre : 5.

Critères d'acceptation :

- [ ] SLS-083.1 Corps de requête entrant de 6 Mio (1 Mio aujourd'hui).
- [ ] SLS-083.2 Archive ZIP de 100 Mio et code de 500 Mio (64 et 256 Mio aujourd'hui).
- [ ] SLS-083.3 200 variables et 200 secrets de 64 Kio par catégorie (128 clés de 16 Kio).
- [ ] SLS-083.4 Disque temporaire de 1 Gio par instance (`/tmp` tmpfs de 16 Mio).
- [ ] SLS-083.5 Jusqu'à 50 instances par fonction, sous réserve du budget de cellule.
- [ ] SLS-083.6 En-têtes `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Real-IP` (écrasé par la
  passerelle, valeurs usurpées ignorées) et `X-Request-ID` injectés au handler.
- [ ] SLS-083.7 Chaque relèvement mesure son coût mémoire, disque et temps, respecte budgets et
  marge disque, garde sa validation côté serveur ; modèle, schéma, manuel et parité à jour.

Tests exigés :

- Unitaires : bornes de chaque grandeur, calcul des en-têtes.
- API / intégration : valeur limite exacte acceptée et suivante refusée pour chaque grandeur.
- E2E : en-têtes reçus par un vrai handler, valeurs usurpées écrasées, saturation et
  restitution des ressources, publication et invocation aux nouvelles limites.

À mettre à jour : `EXECUTION.md`, `SCHEMA.md` si le modèle change, manuel, parité, seed.

<a id="sls-084"></a>
## SLS-084 — Runtimes supplémentaires

Statut : [ ] — contrat à écrire dans [SCALEWAY_PARITY](SCALEWAY_PARITY.md) et
[EXECUTION](EXECUTION.md) avant le code (ordre : écrire, persister, puis réaliser).
Nature : Développer. Dépend de : SLS-083. Ordre : 8.

Résultat attendu : les runtimes de Scaleway, dans l'ordre Node 22 et 26, Python, puis Go,
PHP et Rust.

Critères d'acceptation, **par runtime** :

- [ ] SLS-084.1 Image, protocole du superviseur dans le langage, validation d'import, calcul du
  hash de code et mêmes limites que Node.
- [ ] SLS-084.2 Adaptateur : sélection du runtime sans conversion implicite ; Node 20 et 22
  restent une conversion explicite tant qu'ils ne sont pas natifs.

Tests exigés : par runtime, publication, invocation, erreurs, délai, mémoire, stockage, journaux
et hash stable en E2E ; unitaires du protocole ; budget d'images mesuré.

À mettre à jour : `EXECUTION.md`, manuel, parité, `DAT.md`, seed.

<a id="sls-085"></a>
## SLS-085 — Déclencheurs de file de messages et NATS

Statut : [ ] — **décision d'infrastructure requise** ([cas 4](#décisions-et-autorités-en-attente)) ;
contrat à écrire après la décision.
Nature : Décision. Hors ordre.

Un appel par message d'une file ou d'un sujet NATS, pression arrière, 10 messages en vol,
relance jusqu'à 3 fois sur statut ≥ 300. Aucun service de messagerie n'existe dans le SPARK
DEV : quel courtier fournir relève du responsable du SPARK.

Critères d'acceptation après décision : à écrire avec le contrat (livraison, ordre, relance,
mise en file morte, droits, quotas), preuves sur un vrai courtier démarré sur le SPARK DEV.

<a id="sls-086"></a>
## SLS-086 — Répartition du trafic entre versions

Statut : [ ] — contrat à écrire dans [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md) avant le code.
Nature : Développer. Dépend de : SLS-074, SLS-073. Ordre : 8.

Résultat attendu : répartir un pourcentage des appels sans tag entre la cible promue et un
pilote, comme la mise à jour progressive de Scaleway.

Critères d'acceptation :

- [ ] SLS-086.1 Pourcentage explicite, défini et modifié par un droit Update, jamais implicite.
- [ ] SLS-086.2 Hash exécuté corrélé dans les invocations, journaux et monitoring.
- [ ] SLS-086.3 Retour arrière immédiat ; appels épinglés par hash inchangés.
- [ ] SLS-086.4 Répartition conforme au pourcentage sur un échantillon mesuré, bornes 0 et 100.

Tests exigés : unitaires du tirage, API avec droits par requête directe, E2E sur deux handlers
distincts avec comptage des hash exécutés, captures.

À mettre à jour : `FUNCTION_VERSIONS.md`, `SCHEMA.md`, manuel, parité, seed.

<a id="sls-087"></a>
## SLS-087 — Conditions d'accès supplémentaires

Statut : [ ] — contrat à écrire dans [PLATFORM](PLATFORM.md) avant le code.
Nature : Développer. Dépend de : SLS-040. Ordre : 8.

Résultat attendu : compléter les politiques origine/IP par une plage horaire et un
user-agent, comme les conditions IAM de Scaleway.

Critères d'acceptation :

- [ ] SLS-087.1 Combinaison explicite avec origine/IP (ET/OU), évaluée côté passerelle.
- [ ] SLS-087.2 Plage horaire en UTC ; user-agent par motif ; refus consigné.
- [ ] SLS-087.3 Préflight cohérent avec les conditions ; le manuel rappelle que l'user-agent
  n'atteste aucune identité.

Tests exigés : unitaires de la combinaison, E2E par requêtes directes avec vraies horloge et
en-têtes, préflight navigateur, captures de l'éditeur de politique.

À mettre à jour : `PLATFORM.md`, `SCHEMA.md`, manuel, `DESIGN_SYSTEM_APP.md`, parité, seed.

<a id="sls-088"></a>
## SLS-088 — Serverless Jobs en conteneur

Statut : [ ] — **choix de produit** ([cas 3](#décisions-et-autorités-en-attente)) ; contrat à écrire
après la décision.
Nature : Décision. Hors ordre.

Lots en conteneur jusqu'à 24 heures : image, commande et arguments, relances jusqu'à cinq
fois, stockage éphémère, secrets externes, fuseau d'horaire, lancement et arrêt manuels,
statuts et raisons. Exige un registre d'images et un runtime conteneur généraliste que la
plateforme n'a pas. À distinguer des jobs de console ([SLS-081](#sls-081)).

Critères d'acceptation après décision : à écrire avec le contrat, preuves sur un vrai
conteneur de lot sur le SPARK DEV.

<a id="sls-089"></a>
## SLS-089 — Défauts SSO : attente, azp, rotation de clé

Statut : [~] — corrections déployées en DEV sur e81007c5 ;
[preuve partielle DEV](evidence/sso-session-recovery-dev-2026-11-11.json) : 33 groupes sur 359 sources, 30 captures recoupées.
089.4 est qualifié ; 089.1/.2/.3 restent ouverts. Les vrais profils sans droits,
les refus azp/aud sous signature réelle et la rotation/pending503 restent à
éprouver ; les accès externes indispensables relèvent du cas 4.
Nature : Corriger. Dépend de : SLS-020. Ordre : 2. Reste à faire de SLS-020.
Contrat : [sso](sso.md), [CONTROL](CONTROL.md), [PLATFORM](PLATFORM.md),
[SSO_SESSION_RECOVERY](SSO_SESSION_RECOVERY.md).

Critères d'acceptation :

- [ ] SLS-089.1 Un compte sans rôle `verified`/`admin` voit un **état d'attente** distinct d'une
  erreur technique, avec la conduite à tenir.
- [ ] SLS-089.2 L'`azp` de l'ID token est contrôlé en complément de l'audience.
- [ ] SLS-089.3 Un nouveau `kid` qui arrive dans la fenêtre anti-refresh JWKS de deux secondes
  donne une réponse temporaire qui préserve la session au lieu de la fermer.
- [x] SLS-089.4 La durée de 300 secondes se mesure sur le jeton réellement émis.
  [preuve partielle DEV](evidence/sso-session-recovery-dev-2026-11-11.json) : deux JWT RS256 vérifiés, exp − iat = 300, nouveau iat après
  l’expiration du premier ; 300,659 s mesurées, cookie/sujet/CSRF et échéance
  absolue conservés, puis ancien cookie refusé après déconnexion.

Tests exigés :

- Unitaires : décision d'état d'attente, validation `azp`, gestion du `kid` inconnu.
- API / intégration : jetons forgés avec mauvais `azp`, mauvaise audience, `kid` inconnu.
- E2E depuis l'accueil réel avec vrais comptes (non vérifié, vérifié, admin) et rotation de
  clé réelle maîtrisée ; captures desktop et mobile de l'état d'attente. Si les comptes ou la
  rotation ne sont pas fournis, nommer le blocage ([cas 4](#décisions-et-autorités-en-attente)),
  livrer correctifs et tests de composants, ne rien déclarer prouvé.

À mettre à jour : `sso.md`, `CONTROL.md`, manuel, `DESIGN_SYSTEM_APP.md`, seed.

<a id="sls-090"></a>
## SLS-090 — Pannes résiduelles de publication

Statut : [ ] — scénarios nommés dans SLS-030, jamais éprouvés.
Nature : Qualifier. Dépend de : SLS-030. Ordre : 10. Reste à faire de SLS-030.

Critères d'acceptation, un groupe E2E réel par ligne, sur l'image déployée :

- [ ] SLS-090.1 Expiration d'un candidat.
- [ ] SLS-090.2 Budget et marge disque.
- [ ] SLS-090.3 Déconnexion concurrente du client.
- [ ] SLS-090.4 Arrêt pendant le nettoyage.
- [ ] SLS-090.5 Rupture après envoi de la CLI.
- [ ] SLS-090.6 Modification locale concurrente pendant `deploy`.
- [ ] SLS-090.7 Réponse trop grande.
- [ ] SLS-090.8 Redirection.
- [ ] SLS-090.9 Panne de la FORGE (rebond) pendant une publication, sans écriture sur la FORGE.

Un défaut révélé est corrigé avec un test qui échoue avant correction. Tests exigés :
unitaires des garde-fous touchés, E2E réels, ressources restituées recoupées.

À mettre à jour : `DEPLOYMENT.md`, manuel si un message change.

<a id="sls-091"></a>
## SLS-091 — Rétention et nettoyage du moteur d'exécution

Statut : [~] —091.1 est qualifié : bornes numériques et âge réel rapprochés ;
le nettoyage résiduel091.2 et la nouvelle continuité011 de091.3 restent ouverts.
Nature : Qualifier. Dépend de : SLS-040. Ordre : 10. Reste à faire de SLS-040.

Critères d'acceptation :

- [x] SLS-091.1 Rétention à sept jours et 10 000 observations prouvée par franchissement réel des
  deux bornes. [Âge31](evidence/schedule-retention-age-dev-2026-11-21.json) : HTTP ancien
  retiré, source identique protégée tant que le tir est ouvert puis supprimée.

  La [borne numérique HTTP ordinaire](evidence/invocation-retention-volume-dev-2026-11-11.json)
  est qualifiée par10016 appels/5008 par fonction dans SLS-078. La
  [source protégée sous borne](evidence/invocation-source-retention-volume-dev-2026-11-11.json) est aussi
  qualifiée :10002→10001 non clos→10000 clos. La preuve des sept jours reste
  requise avant de cocher ce critère.
- [ ] SLS-091.2 Chemins résiduels de nettoyage et de reprise après interruption prouvés (SIGKILL
  pendant nettoyage, reprise sans doublon ni perte).
  Les pannes propres du gardien112 et du rattrapage de son parent restent à
  provoquer : perte avant/après armement, gardien perdu pendant STOP, CONT avant
  TERM, reçu ou jointure indisponible et identité conservée sans signal étranger.
  Le cas nominal de suspension ne les qualifie pas par lui-même.
- [ ] SLS-091.3 Continuité de rétention après l'instrumentation SLS-072 et
  la migration011 : `execution.py` change, donc l'égalité de sources exigée
  par `retained_retention_proofs()` n'est plus acquise. Les trois manifestes
  scellés et leurs captures restent inchangés et qualifiés à leur époque.
  Avant adaptation de cette garde, écrire le contrat de preuve courante et
  conserver la distinction historique/courant. Un rapprochement de code ou
  une durée d'une minute ne prouve pas sept jours réellement écoulés sur011.
  Aucune régression complète courante n'est revendiquée tant que cette
  précondition du socle49/543 n'est pas satisfaite.

Tests exigés : unitaires de la rétention, E2E sur horloge et volume réels, ressources
restituées recoupées.

À mettre à jour : `EXECUTION.md`.

<a id="sls-092"></a>
## SLS-092 — Stockage : acquisition partielle, marge physique, panne du registre

Statut : [ ] — scénarios nommés dans SLS-050, jamais éprouvés.
Nature : Qualifier. Dépend de : SLS-050. Ordre : 10. Reste à faire de SLS-050 (avec les
crons de SLS-078).

Critères d'acceptation :

- [ ] SLS-092.1 Acquisition partielle après interruption : reprise sans perte, sans doublon.
- [ ] SLS-092.2 Marge physique de disque : refus propre, aucune corruption, ressources restituées.
- [ ] SLS-092.3 Pannes du registre durable : décisions cohérentes après reprise.

Tests exigés : E2E réels sur l'agent de stockage et le contrôle, unitaires des protocoles
touchés, recoupement physique des volumes. Aucune clôture de SLS-050 ne repose sur les seuls
composants.

À mettre à jour : `STORAGE_AGENT.md`, `DEPLOYMENT.md`.

<a id="sls-093"></a>
## SLS-093 — Fautes de source et de transport des URL d'appel

Statut : [ ] — branches nommées dans SLS-066, non qualifiées.
Nature : Qualifier. Dépend de : SLS-066. Ordre : 10. Reste à faire de SLS-066.

Critères d'acceptation :

- [ ] SLS-093.1 Fautes de source restantes (perte de réponse, verrou suspendu, panne durable de la
  console) : le catalogue reste cohérent, aucune adresse partielle, aucun rejeu.
- [ ] SLS-093.2 Expiration et perte SSH du build borné.
- [ ] SLS-093.3 Erreurs propres du pilote de preuve et du client de diagnostic.
- [ ] SLS-093.4 Refus 403 distinct des coupures ; nettoyage après réponses perdues du nouveau
  client ; sortie excessive et lancement.

Tests exigés : E2E réels sous les routes autorisées du seul SPARK, gardes de restauration
vérifiées, captures des états d'erreur.

À mettre à jour : `INVOCATION_URLS.md`, manuel si un message change.

<a id="sls-094"></a>
## SLS-094 — Pannes, console et régression de SLS-074

Statut : [ ] — l'unité parente SLS-074 reste `[~]` pour ces reliquats.
Nature : Qualifier. Dépend de : SLS-074. Ordre : 10. Reste à faire de SLS-074.

Critères d'acceptation :

- [ ] SLS-094.1 Parcours UI complets de versions (publication, pilote, promotion, retour à un
  hash, archivage, restauration, suppression) depuis l'accueil, captures et manuel compilé.
- [ ] SLS-094.2 Pannes propres du banc et autres interruptions encore nommées dans SLS-074.
- [ ] SLS-094.3 Régression complète de la migration 008 sur le code final, sans échec ni test
  ignoré.
- [ ] SLS-094.4 Historique des versions affiché et cohérent avec le registre.

Tests exigés : E2E réels, recoupement physique du code et des volumes, sources et images
identiques à l'installation.

À mettre à jour : `FUNCTION_VERSIONS.md`, manuel, `DESIGN_SYSTEM_APP.md`.

<a id="sls-095"></a>
## SLS-095 — Campagne complète et clôture

Statut : [ ] — dernière unité ; aucune campagne complète ne vaut tant que les autres sont ouvertes.
Nature : Qualifier. Dépend de : toutes. Ordre : 12. Clôture SLS-001 et SLS-060.

Critères d'acceptation :

- [ ] SLS-095.1 Toutes les autres unités sont `[x]`, ou une décision/autorité nommée dans le
  registre explique celles qui restent.
- [ ] SLS-095.2 Campagne complète exécutée **en série** sur le code déployé : zéro échec, zéro
  test ignoré, sources et images recoupées avec l'installation.
- [ ] SLS-095.3 Toutes les captures de la campagne inspectées ; manuel affiché conforme à
  `docs/manual.md`.
- [ ] SLS-095.4 Matrice [SCALEWAY_PARITY](SCALEWAY_PARITY.md) : chaque ligne Livré, Sans objet ou
  Écart assumé prouvé.
- [ ] SLS-095.5 Documents relus : plus aucune mention de blocage levé, d'incohérence résolue, de
  limite disparue ni de statut périmé ; `CHANGELOG.md`, contrat de déploiement et seed à jour.

À mettre à jour : `TEST_MATRIX.md`, README, journal, compte rendu final de `CLAUDE.md` §25.

<a id="sls-096"></a>
## SLS-096 — Manuel déployé conforme à sa source

Statut : [x] — console reconstruite et déployée avec la source courante ; huit
parcours réels du manuel passent, seize chapitres et 56 paragraphes concordent,
seize captures du guide inspectées. [Preuve](evidence/schedules-checkpoint-dev-2026-11-10.json).
Nature : Corriger. Dépend de : — (même build que SLS-078). Ordre : 1.
Contrat : [CONSOLE_MANUAL](CONSOLE_MANUAL.md).

Critères d'acceptation :

- [x] SLS-096.1 La console est reconstruite et déployée avec le manuel courant.
- [x] SLS-096.2 Le test de concordance entre le guide affiché et `docs/manual.md` passe sur
  l'image déployée.
- [x] SLS-096.3 Règle de maintien : chaque unité qui modifie `docs/manual.md` redéploie la
  console dans la même livraison (critère commun 7).

Tests exigés : concordance des chapitres et paragraphes, E2E depuis l'accueil réel qui ouvre
le manuel, captures desktop et mobile.

<a id="sls-097"></a>
## SLS-097 — API de gestion documentée (OpenAPI)

Statut : [ ] — routes décrites dans [CONTROL](CONTROL.md) ; schéma OpenAPI désactivé.
Nature : Développer. Dépend de : unités 3 à 8 (pour documenter les routes finales). Ordre : 9.

Résultat attendu : la parité « API complète et documentée » de la matrice.

Critères d'acceptation :

- [ ] SLS-097.1 Schéma OpenAPI généré, exposé aux seuls administrateurs authentifiés, complet
  pour toutes les routes de gestion et de jetons.
- [ ] SLS-097.2 Exemples de requêtes et de réponses sans secret ; codes d'erreur documentés.
- [ ] SLS-097.3 Un test compare le schéma aux routes réellement montées (aucune route absente
  ni inventée).

Tests exigés : unitaire de génération, intégration de comparaison routes/schéma, accès direct
refusé sans droit, E2E de lecture du schéma depuis une session administrateur.

À mettre à jour : `CONTROL.md`, manuel, parité, `SCHEMA.md` si besoin.

<a id="sls-098"></a>
## SLS-098 — Noms de mois et de jours des expressions cron

Statut : [ ] — écart découvert lors de la revue de parité SLS-078 du 10 novembre 2026.
Nature : Développer. Dépend de : SLS-078. Ordre : 8.
Contrat à compléter avant code dans [SCHEDULES](SCHEDULES.md).

Constat : la [référence Scaleway des crons](https://www.scaleway.com/en/docs/serverless-jobs/reference-content/cron-schedules/)
accepte les noms de mois et de jours (`DEC`, `MON-FRI`, `WED`). Le contrat
numérique actuel de la plateforme les refuse. Cet écart est distinct de la
résolution de cinq minutes explicitement choisie.

Critères d'acceptation :

- [ ] SLS-098.1 Même grammaire de noms dans l'adaptateur, le contrôle, le moteur et
  les aperçus ; listes, plages, pas et règle jour/semaine cohérents.
- [ ] SLS-098.2 Refus explicite des noms inconnus et combinaisons invalides ;
  déclarations numériques historiques conservées.
- [ ] SLS-098.3 Équivalence des aperçus numériques/nommés et tir réel du jour et
  du mois courants sur les handlers Docker, avec publication/promotion normale.

Tests exigés : validation par les API réelles, déploiement de manifeste avec
noms, prévisions comparées et invocation planifiée sur l'horloge réelle, sans
substitution ; manuel et matrice de parité mis à jour avec la livraison.


<a id="sls-099"></a>
## SLS-099 — Qualification isolée du plafond d’instances

Statut : [x] — même image en installation isolée ; admissions HTTP/cron, sûreté
consommateur et raccordement public qualifiés. Régressions du helper final et
reprise historique réussies sur329sources. Nature : Corriger. Dépend de :
SLS-040. Ordre :1, préalable à la preuve du plafond global de SLS-078.
Contrat : [INSTANCE_LIMIT_RESTORATION](INSTANCE_LIMIT_RESTORATION.md).

Constat : le test abaissait32→2 puis réécrivait32, avec un risque d’écrasement
concurrent et sans restitution indépendante. Le refus préventif est
[vérifié historiquement](evidence/instance-limit-safety-dev-2026-11-10.json).
La correction retenue élimine cette mutation : même image réelle, installation
DEV temporaire à plafond2 dès son démarrage, données originales mises à l’abri,
SSO/API/Docker/agent réels. Aucun besoin d’évolution de FORGE.

Critères d’acceptation :

- [x] SLS-099.1 Décision et périmètre persistés avant le code ; ancienne demande
  externe retirée. La preuve historique des deux refus reste distincte.
- [x] SLS-099.2 [Dix groupes réels](evidence/instance-limit-environment-dev-2026-11-11.json),327sources. Déploiement isolé à plafond2, même image que le contrôle habituel,
  CPU/RAM inchangés ; zéro écriture de variable/proposition officielle.
- [x] SLS-099.3 [Six groupes réels](evidence/instance-limit-consumer-restoration-dev-2026-11-11.json),328sources : consommateur, pause et refus étranger. Restitution indépendante des répertoires et services après perte
  réelle du pilote, même avec un consommateur Docker ; processus/gardes terminés,
  originaux conservés, aucun retrait d’une ressource étrangère.
- [x] SLS-099.4 [Quatre groupes réels](evidence/instance-limit-admission-dev-2026-11-11.json),328sources, six handlers réussis ; cinq restitutions dans la preuve327. Deux instances réelles puis refus HTTP de la troisième, minimum3
  refusé sans mutation, prochain appel sain ; refus planifié sans invocation,
  prochain tir sain sans rejeu. Nominal, EOF, SIGTERM et SIGKILL éprouvés.
- [x] SLS-099.5 [Preuve finale](evidence/instance-limit-public-integration-dev-2026-11-11.json) :31 groupes publics (détail plafond4), dix groupes de garde et un historique. Campagne raccordée à la suite publique et à la matrice,
  toutes les assertions précédentes conservées, dont le retrait natif après
  le troisième appel avant toute promotion et le nettoyage différé dans un
  budget couvrant la maintenance normale ; régressions connexes réussies.

Les anciens succès32→2→32 et le refus préventif ne qualifient pas ces nouveaux
critères. L’unité est clôturée par les preuves sur le vrai déploiement.

Le raccordement passe dans le scope canonique de la suite générale, sur
329sources et imagec59b8616. HTTP30 et ses treize purges précèdent plafond4
et trois purges ; rapport31 parents, sans double comptage. Les cinq modes
finaux repassent dix groupes, puis --partial historique un groupe. Tous les
originaux et fichiers officiels sont conservés, gardes/helpers terminés.
L’échec initial après17 groupes HTTP reste exclu ; le budget de polling
d’effacement couvre maintenant les deux périodes normales de maintenance.
Aucun produit/UI/schéma/manuel modifié ; SLS-078 et la campagne globale restent
ouverts.

<a id="sls-100"></a>
## SLS-100 — Identité visuelle distincte pour Serverless

Statut : [x] — déployée en DEV sur779aef7b et vérifiée :29groupes réels,26captures inspectées.
Nature : Corriger. Dépend de : SLS-020. Ordre :2.
Contrat : cette unité et
[identité du produit](DESIGN_SYSTEM_APP.md#serverless-identity).

Constat initial : l'ancienne foudre de `web/public/favicon.svg`, également
affichée dans la marque de la console par `web/src/main.jsx`, était déjà utilisée
par une autre application interne. Le remplacement livre une identité distincte.

Résultat attendu : un pictogramme vectoriel propre à Serverless, lié à son usage
de fonctions conteneurisées, cohérent avec la charte P2Enjoy et reconnaissable
aux petites dimensions.

Décision du11 novembre2026, avant code : trois blocs reliés par deux branches,
en blanc sur la pastille bleue P2Enjoy existante. Les blocs évoquent les fonctions
et leurs relations ; la silhouette se distingue de la foudre et reste simple à
16px. Un SVG autonome partagé par le favicon et la marque suffit : aucune police,
dépendance, animation ou copie de dessin dans un composant. Le texte P2Enjoy
Serverless reste le libellé accessible ; le SVG de marque est décoratif à côté.
Ce choix est réversible. Un dessin isométrique détaillé est écarté parce qu'il
ajouterait des traits difficiles à lire en favicon.

Preuve commune aux quatre critères : [qualification DEV](evidence/application-icon-dev-2026-11-11.json).

Critères d'acceptation :

- [x] SLS-100.1 Remplacer la foudre dans toutes les utilisations de la marque
  applicative courante, notamment le favicon, l'accueil de connexion et la
  console. Conserver une seule source SVG pour ces représentations.
- [x] SLS-100.2 Vérifier la lisibilité du motif à 16 et32px, son contraste,
  l'absence de débordement sur ordinateur/mobile et le libellé accessible de la
  marque ; les images décoratives restent ignorées des lecteurs d'écran.
- [x] SLS-100.3 Construire et déployer sur le SPARK DEV, puis parcourir l'accueil,
  la connexion SSO réelle et la console à la souris et au clavier. Recouper le
  favicon effectivement servi avec la source et inspecter les captures JPEG
  fraîches de l'accueil et de la console sur ordinateur/mobile.
- [x] SLS-100.4 Mettre à jour le design du produit, le changelog, les preuves et
  références visuelles concernées ; conserver la traçabilité des captures
  historiques et vérifier les parcours connexes sur la nouvelle image.

Tests exigés : E2E sur l'application réellement déployée, sans substitution de
ressource ni interception ; contrôles du fichier servi distincts de l'inspection
visuelle. Une campagne active doit finir et être restituée avant toute
modification de ses sources gelées, construction ou redéploiement. Le nominal
caf8c362 est maintenant terminé, finalisé et restitué ; ce gel est levé.

La nouvelle image conserve les34 fichiers backend et les trois autres ressources
web ; seul favicon.svg change. Contraste blanc/bleu9,03:1, SVG servi recoupé par
SHA,26 captures inspectées (quatre dédiées par le principal,22 de régression par
le vérificateur), previews16/32/64 distinctes des captures applicatives. Les
29groupes comprennent4 ciblés,8manuel,8publics,9connexion ; aucun mock ni skip.
Les5982artefacts et fichiers officiels sont inchangés ;2services sains, actifs/
baux nuls, référence inchangée et aucune garde. Le manuel conserve ses16chapitres
et56paragraphes, recoupés avec sa source inchangée.

<a id="sls-101"></a>
## SLS-101 — État de fiche après publication concurrente

Statut : [ ]. Nature : Corriger. Ordre :3. Dépend de : SLS-071.

Constat réel pendant le replay071.2 : la fonction est ouverte sans code, puis
publiée/promue par l’API normale tandis que Tester reste monté. Actualiser les
adresses affiche le hash courant et les appels200 réels, mais le badge de fiche
reste « Brouillon ». Le catalogue courant confirme function_state:published.
Captures source-forbidden et selected-version-404 du passage2f044b71, référencées
dans la preuve071.2 ; défaut visuel distinct de la correction de hash et non
masqué par le succès des assertions du banc.

Résultat attendu : la fiche ne conserve pas un état de publication contredit
par une relecture explicite de sa fonction, tout en conservant la composition
et les valeurs éphémères du testeur monté.

- [ ] SLS-101.1 Spécifier la source autoritative et le moment de mise à jour du
  badge parent ; ne pas déduire l’état d’une réussite HTTP ni d’un hash seul.
- [ ] SLS-101.2 Publication/promotion concurrentes puis rafraîchissement réel :
  badge cohérent avec les métadonnées courantes, sans rechargement du workspace,
  perte de jeton ou de saisie, ni réémission d’une requête.
- [ ] SLS-101.3 Éprouver E2E le défaut avant correction, le retour corrigé, les
  refus de lecture et les autres facettes affectées ; captures desktop/mobile
  inspectées, manuel/design et régressions communs actualisés.

<a id="sls-102"></a>
## SLS-102 — Espacement des quantités du manuel du testeur

Statut : [ ]. Nature : Corriger. Ordre :6. Dépend de : SLS-062.

Constat visuel du complément071.2 : les cadrages du manuel rendent « de1Mio »,
« à128couples », « et8Kio », « à64 et16Kio » et « de1 à900secondes ». Les mesures
restent compréhensibles, mais l’absence d’espaces dégrade la lecture.

- [ ] SLS-102.1 Corriger ces espacements dans la source canonique du manuel,
  sans changer les bornes fonctionnelles ; examiner les quantités du même chapitre.
- [ ] SLS-102.2 Reconstruire/déployer en DEV et recouper le manuel servi avec sa
  source ; parcours du guide et captures desktop/mobile du chapitre inspectées,
  régressions communes réelles.


<a id="sls-103"></a>
## SLS-103 — Préconditions des preuves sur le schéma010

Statut : [x] — [qualification109](evidence/schema010-proof-prerequisites-dev-2026-11-21.json) passe sur428sourcesfd9c995f,
imageb452 :84ciblés puis25communs,22captures inspectées,12fenêtres restituées.
Nature : Corriger. Ordre :1, préalable désormais livré de la campagne078.
Deux refus préalables reproduits sont exclus, zéro groupe qualifié.

Contrat : [SCHEMA_010_PROOF_PREREQUISITES](SCHEMA_010_PROOF_PREREQUISITES.md).

Constats de revue du21novembre : control-operations.py141 exige008 alors que
l’image courante applique010 ; storage-legacy-environment.py1135 exige009
dans le parcours099 ordinaire. Ces refus précoces empêchent les campagnes
complètes de mesurer le code actuel. Aucun échec fonctionnel produit déduit.

- [x] SLS-103.1 Précontrôle et assertions des migrations courantes exactement
  001→010 ; les bancs006/007/008 historiques et leurs refus restent inchangés.
- [x] SLS-103.2 Fenêtre099 sur l’image courante et son schéma010 : garde figée,
  même autorité/identités, refus des états inconnus et restitution physique,
  sans modification des captures ou configuration officielle.
- [x] SLS-103.3 Tests propres réels : contrôle55, gardes/restitutions et admission099
  avec véritable refus puis succès cron ; schéma, intégrité et originaux recoupés.
- [x] SLS-103.4 Matrice/README/contrat et preuves mis à jour, sans présenter
  ces prérequis comme la campagne complète078 ou095.

Le raccordement des clients schedule-* dans la campagne complète reste porté
par078.5 ; le choix de son assemblage est persisté avant le code correspondant.

Preuve103 :55contrôle,10restitutions,8options,6sûreté consommateur/propriété,
4admission et1déplacement partiel, puis25communs. Onze fenêtres099 utilisent
010→010 ; le déplacement interrompu garde ses métadonnées historiques006→007,
sans démarrer de contrôle historique. Refus cron11:35UTC puis succès11:40,
aucun rejeu ; six handlers réussis sur sept appels du nominal. Douze pilotes
disparus et gardes inactives, zéro activité/bail/réservation, dix migrations,
intégrité/FK,38backend/quatreweb et5982artefacts recoupés. Manuel18/74 conforme.
Aucun changement produit, UI, migration ou configuration officielle ;078 et095
conservent leurs propres campagnes.


<a id="sls-104"></a>
## SLS-104 — Préparation du contrôle historique vers010

Statut : [x] — [qualification104](evidence/legacy-schema010-dev-2026-11-21.json) :30groupes réels sur428sources8b1a9f33,
image couranteb452 et historique5ff7 ;22captures inspectées, deux fenêtres restituées.
Nature : Corriger. Ordre :1, préalable livré de la campagne078.
Contrat : [STORAGE_LEGACY_PROOF](STORAGE_LEGACY_PROOF.md#compatibilité-courante-et-preuves104).

ConstatsGit du21novembre : storage-legacy-build.py exige auth.py identique,
mais les correctifs089 le changent ; la comparaison du validateur omet le
nommage076 et son commentaire. storage-legacy-recovery.mjs attend encore007
à l’upgrade alors que le helper lance l’image courante010. Le socle37 refuse
ainsi avant de prouver sa migration réelle ; aucun défaut produit déduit.

- [x] SLS-104.1 Ancien arbre003 inchangé, provenance Git remappée ; dépendances
  et deux modules runtime identiques. Authentifications ancienne/courante
  distinctes et attestées, aucune injection du code courant dans l’ancien.
- [x] SLS-104.2 Différences du validateur bornées aux changements déjà livrés :
  max_bytes optionnel, nom de conteneur076, commentaire de traçabilité. Toute
  autre différence reste refusée ; tag courant conservé pendant le vrai build.
- [x] SLS-104.3 Rejeu réel003→010 : SSO depuis accueil historique, deux archives
  produites par ses API et imports Docker, session/UUID/code conservés après
  upgrade, dix migrations exactes, purge absente et contradiction réelles
  conservées après redémarrage ; restitution complète des originaux.
- [x] SLS-104.4 Déplacement partiel rejoué et25communs, images/captures/sources
  recoupées. Préconditions historiques périmées reproduites puis exclues,
  contrats actuels/historiques clairement distingués.

Le build est un prérequis, pas un groupe fonctionnel inventé. Les modes
spécifiques006/007/008 et les captures de rétention009 restent inchangés.
La campagne complète078 reste à assembler après ce préalable.

<a id="sls-105"></a>
## SLS-105 — Préparation des instances dans la preuve console

Statut : [x] — [37groupes réels](evidence/execution-console-warmup-dev-2026-11-21.json) au gel93bc53d,
450sources6f09e175 et34captures inspectées, six UUID ready réellement observés.
Nature : Corriger. Ordre :1, préalable à078, après106 pour sa propreté native.
Contrat : [EXECUTION_CONSOLE_WARMUP](EXECUTION_CONSOLE_WARMUP.md).

- [x] SLS-105.1 Refus des six instances conservé, provenance/UUID/configuration
  et publication/promotion recoupées sans déduire une cause non observée.
- [x] SLS-105.2 Préparation respectant upload pilote puis promotion explicite ;
  six vraies instances mesurées, pagination5+1 et douze scénarios conservés.
- [x] SLS-105.3 Douze groupes UI et25communs passent ; captures fraîches relues,
  services/données/artéfacts antérieurs et ressources propres recoupés.

Le pilote est observé sans cible/instance, puis une promotion unique choisit
son hash/alias. Six UUID ready,0,05CPU/128Mio chacun, trois mesures mémoire
positives au relevé initial et pagination5+1 sont recoupés. Dix invocations
terminales, jeton révoqué et purge native complète ;5982originaux/configuration
et services inchangés. L’échec d’origine et les diagnostics de collecte restent
hors des37groupes. La campagne543 de078 reste exigée.

<a id="sls-106"></a>
## SLS-106 — Conservation des artefacts en régression

Statut : [x] — [79groupes réels](evidence/regression-artifact-cleanup-dev-2026-11-21.json) au gel72059cb,
450sourcesaaf0784a et51captures inspectées ; neuf fonctions purgées nativement.
Nature : Corriger. Ordre :1, préalable opérationnel à105/078.
Contrat : [REGRESSION_ARTIFACT_CLEANUP](REGRESSION_ARTIFACT_CLEANUP.md).

- [x] SLS-106.1 Inventaires original/courant comparés intégralement, différences
  attribuées aux UUID de campagne ou protégées si leur appartenance est inconnue.
- [x] SLS-106.2 Cause et décision persistées avant correction ; nettoyage par
  les vraies API limité aux fixtures prouvées, aucun original effacé ou fabriqué.
- [x] SLS-106.3 Helper partagé éprouvé par3groupes dédiés,19control-admin,
  11control-ui et21publication-ui, puis25communs ;5982artefacts et ressources
  recoupés, rapports/captures inspectés. Les douze execution-ui restent à105.

La remise en état de l’ancien UUID est distincte et compte0groupe. Neuf
fonctions de la nouvelle campagne sont purgées, dix observations du helper
conservent une seule commande par fonction. Les deux records données/cache
sont réellement écrits, conservés au SHA attendu après archive puis retirés
par purge.5982originaux, fichiers officiels, référence et images préservés.
Le contrôle redémarre normalement dans le scénario control-admin. Deux essais
incomplets restent exclus ;105/078/095 gardent leurs preuves propres.

<a id="sls-107"></a>
## SLS-107 — Raccordement de la preuve de publication console

Statut : [x] — [qualification de 46 groupes](evidence/publication-console-hash-regressions-dev-2026-11-21.json) au gel659e852,
450sources7b67df18, imageb452 et44captures inspectées.
Nature : Corriger. Ordre :1, préalable à106/078.
Contrat : [PUBLICATION_CONSOLE_REGRESSIONS](PUBLICATION_CONSOLE_REGRESSIONS.md).

- [x] SLS-107.1 Échec initial conservé ; correspondance complète des21groupes
  avec les contrats et les widgets servis, sans cause produit présumée.
- [x] SLS-107.2 Attentes/gestes du client alignés aux versions par hash et au
  pilote/promotion, sans groupe retiré ni mutation UI contournée.
- [x] SLS-107.3 Vingt-et-un groupes et25communs passent, captures inspectées,
  manuel/source/rendu et nettoyage natif recoupés ;5982artefacts conservés.

La preuve conserve21groupes publication,8manuel,8public et9connexion. Treize
invocations réussies et deux refus recoupent pilote, promotion et disponibilité.
Deux fonctions sont purgées par les API avec contrôle physique du code, des
volumes et des secrets ;5982originaux/configuration/référence sont préservés.
Les deux essais incomplets restent exclus.106 et105 ont leurs preuves propres ;
078 reste ouverte pour son assemblage complet.

<a id="sls-108"></a>
## SLS-108 — Raccordement de la preuve de transport des services

Statut : [x] — [30 groupes réels et 22 captures inspectées](evidence/service-transport-promotion-regressions-dev-2026-11-21.json), gel 3f6974a / 451 sources.
Nature : Corriger. Ordre :1, préalable à078.
Contrat : [SERVICE_TRANSPORT_REGRESSIONS](SERVICE_TRANSPORT_REGRESSIONS.md).

- [x] SLS-108.1 Échec et worker finalisé conservés ; cause et cinq groupes
  rapprochés des contrats/identités actuels avant décision.
- [x] SLS-108.2 Client raccordé sans supprimer faute, observateur, garde,
  transport CLI ou vérification réelle ; décision persistée avant code.
- [x] SLS-108.3 Cinq groupes puis25communs passent ; captures/manuel et
  nettoyage natif recoupés,5982originaux préservés.

Les deux commandes coupées conservent trois connexions HTTPS et une seule
tentative de mutation chacune. Trois gardes restaurent le contrôle ; les
relances publient un pilote, constatent son refus sans cible, puis le
promeuvent par la CLI avant deux invocations Docker réussies. Deux fonctions
sont purgées physiquement et quatre jetons révoqués ; configuration, référence
et 5982 artefacts conservés. SLS-109 et la campagne entière SLS-078 restent ouvertes.

<a id="sls-109"></a>
## SLS-109 — Préparation des dix clients modernes du socle

Statut : [x] — [106 groupes réels et 59 captures inspectées](evidence/modern-client-promotion-regressions-dev-2026-11-21.json), gel 0dfd953 / 453 sources.
Nature : Corriger. Ordre :1, après108 et avant le prochain078.
Contrat : [MODERN_CLIENT_PROMOTION_REGRESSIONS](MODERN_CLIENT_PROMOTION_REGRESSIONS.md).

- [x] SLS-109.1 Dix clients/groupes rapprochés des contrats actuels ; décisions
  explicites de cible, hash/alias, ETag et parcours persistées avant code.
- [x] SLS-109.2 Dix montages raccordés sans retirer leurs81groupes, leurs
  fautes, refus, gestes UI et consommateurs réels ; historique003 intact.
- [x] SLS-109.3 Les81groupes puis25communs passent ; captures/manuels,
  gardes/restaurations, purges et5982originaux recoupés sur le code déployé.

Les dix campagnes passent leurs 81 groupes puis les 25 communs, sans saut.
Dix-neuf promotions API de préparation et une confirmation UI sont recoupées
par vingt audits ; le parcours UI des adresses conserve son pilote sans défaut.
Quatre-vingt-neuf fonctions sont purgées physiquement, 22 namespaces et 26
services supprimés logiquement, 30 jetons révoqués et 83 invocations réussies.
La purge efface les secrets propres des fonctions ; les configurations communes
des parents restent hors de sa portée conformément à CONSOLE_STORAGE. Quinze
services catalogue ont été explicitement vidés ; deux autres services conservent
leurs secrets communs chiffrés dans leurs lignes supprimées. Ce constat ne clôt ni SLS-074,
ni SLS-066, ni la campagne entière SLS-078.

<a id="sls-110"></a>
## SLS-110 — Restitution indépendante des publications pendant validation

Statut : [x] — 29 groupes réels et 22 captures inspectées au gel965185f, le21 novembre2026.
Nature : Corriger. Ordre :1, préalable au nouveau078.
Contrat : [PUBLICATION_RECOVERY_GUARD_REGRESSIONS](PUBLICATION_RECOVERY_GUARD_REGRESSIONS.md).

- [x] SLS-110.1 Échec scellé et état natif recoupés ; reçus, échéances et cause
  instruits avant décision, sans assimiler timeout client et panne de garde.
- [x] SLS-110.2 Décision persistée puis correction bornée sans retirer aucun
  des quatre groupes, coupe, helper perdu, garde ou contrôle physique.
- [x] SLS-110.3 Quatre groupes et25communs passent sur code déployé ; captures,
  manuel, reçus/restaurations et dix purges physiques recoupés,5982originaux conservés.

Preuve : [confirmation indépendante réelle](evidence/publication-restoration-confirmation-dev-2026-11-21.json),
454sources / imageb452 ; quatre ciblés puis25communs, sans réutiliser les groupes
du worker incomplet. Deux coupures137 et gardes natives, huit invocations Docker
réussies, dix purges physiques et un jeton révoqué. Le reçu indépendant est lu
après84sondes et49,343131s monotones, dans l’enveloppe235s ; ce nouveau passage
ne dépasse pas50s. L’ancien délai natif50,495795658s reste une preuve distincte.
Manuel18/74,38backend/quatreweb, mêmes services/images, configuration, référence
et5982originaux conservés. Les branches de secours et d’expiration235s non
provoquées restent hors de cette preuve et des critères résiduels074/091.2.
IR-003 et la campagne entière078 restent ouverts.

<a id="sls-111"></a>
## SLS-111 — Reprise du banc de stockage géré après six groupes

Statut : [~] —39régressions qualifiées dans la preuve112 ; assertion historique
du cinquième passage078 au gel f7b1d2a toujours indéterminée, critères111.1/.2 ouverts.
Nature : Corriger. Ordre :1. Diagnostic borné et régression actuelle39 acquis avant
reprise078 ; investigation historique111.1/.2 ouverte, sans dépendance absolue de078.
Contrat : [MANAGED_STORAGE_REGRESSIONS](MANAGED_STORAGE_REGRESSIONS.md).

- [ ] SLS-111.1 Échec scellé, assertion et état natif instruits, cause et décision
  persistées avant code ; aucun timeout ou silence assimilé à une panne produit.
- [ ] SLS-111.2 Correction bornée du défaut établi, sans retirer de groupe, de faute
  réelle, de concurrence ou de contrôle de nettoyage ; tout défaut distinct inscrit.
- [x] SLS-111.3 Les14groupes ciblés puis25communs passent sur le code déployé ;
  captures ouvertes individuellement, manuel, ressources et reçus recoupés, helpers
  réellement terminés, services/référence/configuration et5982originaux conservés.

<a id="sls-112"></a>
## SLS-112 — Issue d’invocation pendant libération volontaire du bail

Statut : [x] —82groupes réels qualifiés au gel36763c9/458sources/image433da150,
22captures inspectées. Ancienne assertion111 non attribuée.
Nature : Corriger. Ordre :1. Contrat : [MANAGED_INVOCATION_WATCH](MANAGED_INVOCATION_WATCH.md).

- [x] SLS-112.1 Discriminant réel entre résultat de l’invocation interne,
  exception du watcher et résultat final, même UUID/fermeture/bail ; cause et
  décision persistées avant correction du produit, sans faux événement ou mock.
- [x] SLS-112.2 Une fermeture initiée par l’invocation ou le drainage ne devient
  pas une fausse panne de stockage à cause de son propre bail libéré ; les pertes
  réelles de FUSE/agent continuent de retirer le consommateur avec leur erreur.
- [x] SLS-112.3 Douze groupes discriminants,14groupes gérés,31publics et25communs
  (82uniques) passent
  sur code déployé ; captures/manuel, pannes et nettoyages natifs recoupés, même
  référence/configuration et5982originaux conservés. Aucune cause111 inventée.

Preuve112 : [82groupes réels](evidence/managed-invocation-watch-dev-2026-11-21.json),
12ciblés/14gérés/31publics/25communs ;22captures inspectées et0saut. Cas natif :
LeaseMissingDuringClose pendant fermeture, STOP/CONT0,759268909s, timeout interne
et final identiques et données relues.17purges physiques et trois fonctions
isolées purgées puis absentes après restauration,38backend/quatreweb, manuel18/74,
référence/configuration/5982originaux conservés. Les39gérés/communs satisfont
111.3 sans double comptage. Ancienne assertion111 et fautes propres091.2 non
attribuées/non qualifiées ; la campagne entière078 reste due.

<a id="sls-113"></a>
## SLS-113 — Pagination des lectures de console pendant erreur et chargement

Statut : [ ] — pagination périmée constatée visuellement sur 433da150 pendant
le sixième passage 078 au gel 9e1da70 ; aucun correctif ni nouveau test appliqué.
Nature : Corriger. Ordre : 6, avec la prochaine livraison de console.
Dépend de : SLS-065. Contrat : [CONSOLE_PAGINATION_STATES](CONSOLE_PAGINATION_STATES.md).

- [ ] SLS-113.1 Navigation chiffrée des archives et des observations Instances/
  Invocations retirée hors lecture réussie, comme dans le catalogue global ; aucune ancienne page ni faux total à zéro
  présentés en cours
  de lecture ou d’erreur. Erreur et relecture restent lisibles.
- [ ] SLS-113.2 Filtre et page demandée conservés pour la reprise ; résultat,
  total et recalage relus depuis la vraie réponse, focus sur un élément monté,
  desktop/mobile et retour après panne sans données périmées présentées à jour.
- [ ] SLS-113.3 Cause/décision persistées avant code ; mode hors connexion natif
  navigateur, requête réellement refusée puis reprise online, sans interception
  ni serveur de substitution. Les 10 groupes storage-console-ui,12 execution-ui enrichis et 25 communs
  (47 uniques) passent sur code déployé ; captures fraîches inspectées, manuel et ressources/
  nettoyages/configuration/référence/originaux recoupés, aucune faute retirée.

Constat : storage-ui-pagination-error.jpg
SHA569351743565ed9243f8ce4b3822ad3b6f8fbe63b76e5f9921e69eeaf01ec7c3
montre « Page 1 sur 161 » pendant l’erreur, sans cartes ni total, commandes grisées.
Rapport storage-console-ui3f346779432b5dd2cd3e17a135ab44a4d27dd5ecb1e65777df381bfe816f37d3,
10 groupes passés et 14 captures fraîches. La fiche titrée « Archives conservées »
après purge était déjà suivie dans 075 et y reste attribuée. Le même état est observé dans execution-ui-network-error.jpg
SHA7a7ea8d638e499db76a41877d6fff251d041a1d8ac30e4bd858f9342d7321d85 :
Instances sans cartes en erreur, « Page 2 sur 2 », Précédente active. Le composant
ExecutionObservations est partagé avec Invocations ; les deux variantes doivent
être éprouvées. Aucun défaut backend n’est inféré des seules images ; aucune
correction de 075/113 n’est encore qualifiée.

<a id="sls-114"></a>
## SLS-114 — Génération et nettoyage des archives de qualification

Statut : [x] — [32 groupes réels](evidence/code-editor-archive-boundaries-dev-2026-11-22.json)
au gel0168ae2/459sources, image433da150 ;22captures fraîches inspectées.
Le premier passage échoué reste conservé, zéro groupe ajouté.
Nature : Corriger. Ordre :3, préalable au passage ZIP de070. Dépend de : SLS-063.
Contrat : [CODE_EDITOR_ARCHIVE_RECOVERY](CODE_EDITOR_ARCHIVE_RECOVERY.md).

- [x] SLS-114.1 [Premier échec et diagnostic natif](evidence/code-editor-archive-preparation-failed-dev-2026-11-22.json). Premier échec scellé, état natif du générateur, reçus, identités et
  propriété des sorties instruits ; cause et décision persistées avant correction.
- [x] SLS-114.2 Correction bornée conservant image, identités, limites, calibration,
  refus et contrôles de nettoyage ; restitution ou retrait des seules ressources
  possédées après diagnostic connu, sans masquer l’état natif ni relance automatique.
  Le prérequis natif positif intégré à la preuve32 confirme cleanup sortie0,
  already_absent/output_removed/container_gone et absence avant/après de l’ancien
  UUID ; il ajoute zéro groupe. Le nouveau générateur et son nettoyage passent.
- [x] SLS-114.3 Sept groupes ZIP et25communs passent au nouveau gel sur code réel ;
  six handlers, cinq fonctions, dix révisions et nettoyage physique complet recoupés,
  captures/manuel/backend/web/configuration/référence et5982originaux conservés.
  Le premier essai reste séparé et n’ajoute aucun groupe au total qualifié.

Diagnostic114 : Docker dit `error: no such object` en minuscules ; le helper
rejette ce message réel par comparaison sensible à la casse, avant création et
au nettoyage. Cleanup original reproduit sortie1 sur des ressources absentes
avant/après ; aucun nettoyage forcé nécessaire. Décision avant code : normaliser
la casse des seuls messages connus sous code1 et compléter les postconditions
du retour already_absent après vérification native. Prérequis positif
sur l’ancien UUID puis nouveau7+25 réalisés ; aucune garde ni limite retirée.

<a id="sls-115"></a>
## SLS-115 — Retour du focus après adoption du brouillon

Statut : [x] — [36groupes réels](evidence/code-editor-adoption-focus-dev-2026-11-22.json)
au gelce8540a/463sources/image04604089,62captures inspectées. Le défaut initial
sur433 reste conservé, zéro groupe ajouté. Nature : Corriger. Ordre :3, préalable à la
qualification résiduelle070.3/.4. Dépend de : SLS-063 ; s’appuie sur la tranche
déjà déployée de SLS-070.
Contrat : [CODE_EDITOR_ADOPTION_FOCUS](CODE_EDITOR_ADOPTION_FOCUS.md).

- [x] SLS-115.1 [Échec et cause circonscrite](evidence/code-editor-adoption-focus-failed-dev-2026-11-22.json)
  conservés : neuf groupes passés mais zéro qualifié,18gardes/24lecteurs
  restaurés, huit invocations et purge complète,32captures inspectées. L’adoption
  retire sa confirmation avant son retour de focus ; aucun relais parent.
- [x] SLS-115.2 Rendre après adoption réussie le focus au textarea courant en
  édition, sinon au titre stable du fichier ; garder/remplacer restent des
  actions locales sans PUT. Annuler/refuser ne déclenche aucun retour tardif.
  Les huit mesures des quatre adoptions sont TEXTAREA/on_fieldtrue ; huit
  variantes de lecture/existence/absence gardent le titre attendu, texte/SHA,
  lecture seule et version UI/serveur recoupés. La preuve36 conserve leurs données.
- [x] SLS-115.3 Nouveau gel construit/déployé : onze groupes ciblés puis25communs
  frais, quatre adoptions retenues et huit variantes hors saisie/fichier absent,
  neuf invocations,18gardes/24lecteurs joints et purge physique recoupés.
  Captures/manuel/backend/web/notes/configuration/référence/5982originaux conservés.
  Le premier échec reste exclu. Les critères070.3/.4/.5 gardent leurs autres preuves.

<a id="sls-116"></a>
## SLS-116 — Image de retour disponible avant bascule

Statut : [x] — image de retouraa214179 reconstruite et comparée au live,
bascule046 réussie puis [36groupes qualifiés](evidence/code-editor-adoption-focus-dev-2026-11-22.json).
Le premier arrêt avant Compose et son diagnostic restent conservés, zéro groupe ajouté.
Nature : Corriger. Ordre :3, préalable à115. Dépend de : SLS-063.
Contrat : [CODE_EDITOR_DEPLOYMENT_RECOVERY](CODE_EDITOR_DEPLOYMENT_RECOVERY.md).

- [x] SLS-116.1 [Arrêt et diagnostic natif](evidence/editor-adoption-image-preparation-failed-dev-2026-11-22.json).
  Conserver le premier transport/programme/intention et relever
  l’état réel du magasin d’images, du contrôle/référence et des sauvegardes
  possédées. Déterminer la cause sans déduire l’existence d’une image de son
  empreinte dans l’inspection d’un conteneur ; aucune relance automatique.
  L’image433 est actuellement absente du magasin, contrôle sain inchangé ;
  la garde de préparation ne vérifiait pas cette disponibilité. Le stderr
  interne du premier tag et la raison de disparition Docker restent inconnus,
  sans être inventés ; le diagnostic actuel et ses limites sont conservés.
- [x] SLS-116.2 Disposer avant bascule d’une image de retour validée contre les
  vrais octets backend/web servis et la configuration d’image attendue, sans
  secret embarqué. Toute reconstruction est décidée avant son code et conserve
  les sources, images et services de départ ; premier échec exclu.
  Prérequis de la preuve36 :63entrées dont deux copies Git4d,38backend/quatreweb
  exactement égaux au live433 ; six attributs d’image comparés sans valeurs,
  conteneur d’inspection retiré, candidate046/services conservés. Zéro groupe ajouté.
- [x] SLS-116.3 Nouveau précontrôle, nouveaux UUID et bascule DEV puis36groupes
  réels de115 :9handlers,18gardes/24lecteurs joints, captures inspectées et purge
  physique complète ; backend/web/manuel/notes/configuration/référence/originaux
  recoupés. Pas de fermeture de115 ni de070 sur la seule construction d’image.
  La preuve36 lie build, retour et déploiement exacts ; bascule5c106957, nouveau
  CIDe219 et sauvegardes des deux bases. Aucun retour de déploiement n’a été
  exécuté ou qualifié par ce nominal ; les fautes de garde acquises restent à leur époque.

<a id="sls-117"></a>
## SLS-117 — Observation de la requête après départ du document

Statut : [x] — [32groupes réels](evidence/code-editor-publication-continuity-dev-2026-11-22.json)
au gel9b14b0d/469sources/API046,32captures inspectées, neuf handlers et purge
physique recoupés. Les deux rouges et le diagnostic restent séparés, zéro groupe ajouté.
Nature : Corriger (banc de preuve). Ordre :3, préalable à070.3/.5.
Dépend de : SLS-063. Contrat : [CODE_EDITOR_NAVIGATION_OBSERVATION](CODE_EDITOR_NAVIGATION_OBSERVATION.md).

- [x] SLS-117.1 Conserver le premier rouge, le rapport et les programmes figés,
  pilote89379 sortie1/joint, deux captures desktop ouvertes individuellement,
  quatre invocations, une garde restituée et purge physique de la fonction.
  L’UUID UI est plus tard publié mais aucun événement terminal réseau n’est
  conservé ; cette inconnue n’est pas reconstruite.38backend/quatreweb, notes,
 010/manual18/74, référence/configuration/budgets et5982originaux préservés.
- [x] SLS-117.2 Conserver le diagnostic réel de navigation et sa limite de
  visibilité réseau, puis éprouver la fermeture réelle de la Page cliente :
  Close/close achevé et Target.targetDestroyed de son identifiant natif, inventaire absent,
  nouvelle Page au même candidat par GET sans POST. La fin HTTP reste distincte.
  Diagnostic borné et séparé à zéro groupe qualifié avant correction/replay.
  Revue du diagnostic avant exécution : l’expiration20s quittait l’attente sans
  fin/dernière sonde ni GET indépendant du candidat. Conserver échéance, fin,
  résultat absent ou reçu et lecture GET avant de réémettre ce rouge, sans
  prolongation de fenêtre ni conversion en réussite.
  Le [diagnostic20s](evidence/code-editor-navigation-diagnostic-failed-dev-2026-11-22.json)
  fe02296/468 échoue : deux étapes passent, troisième native_network_terminal_missing,
  zéro qualifié, un handler et deux captures ;390sondes, nouveau loader/init et
  GET publié sans terminal réseau observé. Purge physique et conservations recoupées.
  La décision de fermeture Page/target est persistée au contrat avant son client ;
  aucun nouvel allongement de fenêtre ni acquittement rétroactif du rouge.
  Revue du client de fermeture avant exécution : relier frame/loader du POST
  au document initial, et borner le refus de réponse à la fermeture confirmée ;
  conserver les événements ultérieurs sans leur attribuer une remise antérieure.
  [Diagnostic de fermeture acquis](evidence/code-editor-page-closure-diagnostic-dev-2026-11-22.json)
  au gel1749ffe/469 : trois étapes, zéro groupe qualifié. Close/retourclose/
  targetDestroyed exacts en3,144ms puis targetabsente ; nouvellePage/GETmêmeUUID,
  Bparhash/Apar défaut, trois handlers et trois captures, purge physique et
  conservations recoupées. HTTPoriginal resteinconnu. À ce checkpoint diagnostique,117attendait son replay32.
- [x] SLS-117.3 Persister le résultat et la décision avant correction du client ;
  nouveau gel et nouveau7+25sans cumul, neuf handlers, une garde, quatre vrais
  uploads partiels, dix captures ciblées et22communes inspectées, purge physique.
 À ce checkpoint117,070.3/.5 restaient ouverts ; le complément29 les clôture
 après rapprochement des critères.

Résultat117.3 : sept ciblés puis25communs frais, deux fermetures Page/target et
reprises par GET, observateurs détachés avant le POST suivant ; neuf handlers,
une garde/un lecteur, quatre uploads receiving puis orphanprepared429/abandon.
Neuf candidats4publiés/5échoués et quatre révisions recoupés. Les32captures sont
inspectées ;38backend/quatreweb,010/manuel/notes/configuration/budgets/référence/
5982originaux conservés. Les fins HTTP inconnues restent inconnues ; aucune
coupure du contrôle ni persistance après restart acquise par cette campagne.

<a id="sls-118"></a>
## SLS-118 — Acquisition de la validation du banc éditeur

Statut : [x] — [29groupes réels](evidence/code-editor-control-interruption-dev-2026-11-22.json) au gelef71eb7/474sources/API046,
26captures inspectées, six handlers, deux coupures137 et purge physique. Nature : Corriger (banc de preuve). Ordre :3, préalable à
070.3/.5. Dépend de : SLS-063. Contrat :
[CODE_EDITOR_CONTROL_WINDOW](CODE_EDITOR_CONTROL_WINDOW.md).

- [x] SLS-118.1 Conserver le [premier échec](evidence/code-editor-control-interruption-window-failed-dev-2026-11-22.json),
  gel4a5d67d/473sources/API046, pilote11034 sortie1/joint : deux groupes passent
  puis acquisition validating expirée20,007976929s/1535sondes, état receiving0444
  encore observé. Une seule vraie coupure receiving137/HTTP502, deux gardes
  terminées, trois handlers, deux JPEG desktop inspectés et purge physique ;
  seconde requête ensuite200/publiée, aucune coupure validating ni vue mobile.
  Zéro qualifié, aucun commun. Produit/notes/config/référence/5982originaux
  conservés ; durée précise d’extraction et cause système non reconstruites.
- [x] SLS-118.2 Après persistance de la décision, garder le grand ZIP pour
  receiving, publier un pilote C compact de deux vrais fichiers, abandonner
  explicitement le brouillon déjà éprouvé et créer une nouvelle base C pour
  validating. Même fonction/cible A/ETag, fenêtres20s/timer45s/protocole235s
  et gardes à l’octet. Aucun produit ni dépendance substituée.
  Implémentation préparée après9a35d3d : modes explicites, nouvelle base C et
  contrôles par phase ; syntaxes JS/Python contrôlées,474sources. Ces gestes
  passent dans29 : C non promue, nouveau brouillon réellement sur sa révision.
- [x] SLS-118.3 Nouveau gel et nouveau4+25réels : deux coupures137, seconde
  restitution indépendante, API/UI du brouillon conservé dans les deux phases,
  six handlers, sept candidats5pub/2failed, quatre révisions, déduplication,
  quatre JPEG ciblés et22communs inspectés, purge physique/repos/conservations.
  Le premier rouge reste exclu ;070.3/.5 exigent aussi le rapprochement avec
  leurs preuves historiques, sans cumul de groupes.

Résultat118 : quatre ciblés puis25communs frais, pilote47037 sortie0/joint.
Deux gardes terminées, seconde restitution indépendante50,289497s/83sondes,
aucun secours ; six handlers et26captures inspectées. Sept candidats5pub/2failed,
quatre révisions, deux créations/deux sauvegardes/un abandon de brouillon.
Purge physique, compteurs0,38backend/quatreweb/010/manuel/notes/config/budgets/
référence/5982originaux recoupés. Le premier rouge ajoute0groupe. Les sources
serveur inchangées et les preuves historiques rapprochées ferment070.3/.5 ;
les autres unités et la clôture globale095 restent ouvertes.

<a id="sls-119"></a>
## SLS-119 — Refuser une réponse JSON de gestion incomplète

Statut : [ ] — constat statique découvert pendant SLS-072 ; aucune reproduction
réelle ni correction du client commun encore acquise.
Nature : Corriger. Dépend de : SLS-020. Ordre : 3.

Constat : [web/src/api.js](../web/src/api.js) remplace toute erreur de lecture
JSON par `{}` avant de vérifier le statut HTTP. Un corps incomplet sous statut
2xx peut ainsi être rendu au consommateur comme une réussite. La cause est
localisée ; l'effet réel sur les parcours existants reste à reproduire. Le
comportement commun reste inchangé pendant la préparation de SLS-072.

Résultat attendu : une réponse JSON non lisible ne confirme pas une opération
et ne transforme pas une lecture incomplète en données par défaut.

- [ ] SLS-119.1 Reproduire sur une vraie réponse de contrôle : en-têtes2xx et
  corps incomplet observés, défaut natif possédé avec garde de restitution,
  test échoué conservé avant correction. Aucun serveur ou flux substitué.
- [ ] SLS-119.2 Rejeter cette réponse dans le client commun ; conserver les
  refus HTTP réels, distinguer protocole incomplet et refus métier, et garder
  une mutation non acquittée sans rejeu automatique.
- [ ] SLS-119.3 Prouver les lectures et écritures concernées dans la vraie UI :
  erreur lisible, aucun faux message de réussite ni ancien contenu présenté
  comme nouveau résultat, relecture explicite et ressource native recoupée.
  Rejouer les consommateurs touchés et les critères communs, captures ouvertes.

À mettre à jour lors de la réalisation : contrat du client de gestion dans
`CONTROL.md`, manuel, `DESIGN_SYSTEM_APP.md`, preuve et inventaire de régression.

<a id="sls-120"></a>
## SLS-120 — Réconcilier la frontière réelle du buffer de journaux

Statut : [~] — premier passage072 arrêté sur une assertion de frontière dans
API04, après trois groupes passés ; zéro qualifié. Le nettoyage physique et
les5982artefacts antérieurs sont recoupés. La cause est à établir par un témoin
d'octets conservé ; ne pas attribuer l'échec au runtime sur cette seule assertion.
Nature : Corriger. Dépend de : SLS-040. Ordre : 3.

Résultat attendu : distinguer la borne brute du runtime et le buffer expurgé
exposé par l'API, puis avoir un contrat et un client qui éprouvent exactement
leurs limites sans affaiblir la protection des secrets ou masquer une perte.

- [x] SLS-120.1 Sceller le premier rouge sur1aa70214/498sources, son nettoyage
  et sa conservation ; garder ses trois groupes partiels hors du total qualifié.
- [x] SLS-120.2 Diagnostic réel aux bornes65535/65536/65537 octets, avec et
  sans secrets effectifs : conserver UUID, octets observés, empreinte et drapeaux
  avant toute assertion. Éprouver aussi un secret traversant la frontière.
  Aucune horloge, dépendance, réponse ou donnée SQL substituée.
- [x] SLS-120.3 Décision et motif persistés avant correction du contrat,
  client ou produit concerné ; limites et expurgation restent contrôlées.
  Le test échoué précède toute correction de comportement produit.
- [ ] SLS-120.4 Rejouer API04 dans les douze groupes réels puis25communs frais,
  avec sources/image recoupées, purge physique et captures communes inspectées.
  Les dixUI et la régression complète de072 restent des preuves distinctes ;
  aucun cumul de l'ancien échec et aucun critère072 validé par le seul diagnostic.

Premier rouge scellé : [preuve](evidence/execution-journal-buffer-first-failed-dev-2026-11-22.json),
brutSHA `63a18943…`, trois groupes partiels et zéro qualifié. Les498sources et
le programme privé sont conservés séparément ; le client de diagnostic est un
nouveau fichier et ne réécrit pas le premier passage.

Diagnostic : [huit mesures réelles](evidence/execution-journal-buffer-diagnostic-dev-2026-11-22.json),
499sources/1aa70214, brutSHA `0564ea54…`, zéro groupe qualifié. Sans secret,
65536 est conservé ; avec secret maximal61octets,65537 devient65476 avec
troncature et sans préfixe divulgué. Nettoyage physique et5982originaux recoupés.
Décision avant correction : conserver le produit ; le client éprouvera la borne
brute dans un service sans secrets et le retrait de protection séparément dans
le service à secrets. Manuel inchangé : il décrit une limite et l'expurgation,
sans promettre une taille égale à64Kio après celle-ci. Le replay complet reste dû. Le second passage passe API04 et07 mais échoue
au verrou natif d’API08 ;120.4 attend maintenant [SLS-121](#sls-121).

À mettre à jour : contrat de collecte dans `EXECUTION_LOGS.md`/`EXECUTION.md`,
preuve et clients ; manuel s'il décrit incorrectement le buffer expurgé.

<a id="sls-121"></a>

## SLS-121 — Éprouver les frontières natives de décision du journal

Statut : [~] — API08 du second passage072 échoue avant acquisition de la
barrière finale :40s,66178tours de boucle, zéro thread retenu. Les cinq groupes
précédents restent partiels, zéro qualifié. Nature : Corriger. Dépend de :
SLS-040. Ordre : 3. Contrat de frontière :
[EXECUTION_LOGS](EXECUTION_LOGS.md#instrumentation-native-des-lectures).

Résultat attendu : éprouver les changements acceptés avant et après la
décision de lecture, et la réponse perdue après commit de politique, par de
vraies frontières natives de worker et les résultats HTTP/versions/audits.
Le banc respecte les délais du produit et restitue ses threads ; il n'exige
pas d'errno noyau pour un conflit que SQLite peut traiter en interne. Ne pas
changer de produit pour satisfaire une hypothèse du banc.

- [x] SLS-121.1 Sceller le rouge499sources/1aa70214, ses programmes et reçus,
  cinq groupes partiels hors qualification ; nettoyage physique et5982originaux.
- [x] SLS-121.2 Diagnostic réel des syscalls de la lecture finale : thread,
  commande/fd/verrou/résultat et chemin effectifs, résultat HTTP et chronologie.
  Garder les bornes40/45/50/60s et les2s du produit ; aucun syscall remplacé,
  registre modifié, résultat injecté ni écriture de données SQL.
- [x] SLS-121.3 Décision/motif persistés avant correction du seul élément en
  cause ; le rouge précède toute correction de comportement produit. Les
  conditions natives et l’observation du writer restent strictes.
- [ ] SLS-121.4 Rejouer API08 dans les12API réels puis25communs frais,
  sources/image recoupées, gardes/threads/consommateurs joints, purge physique
  et captures communes inspectées.120.4 et072 gardent leurs critères propres.

Diagnostic retenu avant code : ajouter aux seuls reçus du banc un relevé borné
des noms de workers et numéros de syscalls rencontrés, les128premiers fcntl des
workers du journal (fd, identité du fichier, type/portée du verrou et résultat),
leur première/dernière observation et les compteurs de dépassement. Ne lire ni
en-têtes, ni corps, ni buffers applicatifs ; la mémoire lue se limite au struct
flock déjà requis pour observer SQLite. Conserver le statut/délai/code public
de la vraie requête même si la barrière échoue. Reproduire le préfixe réel des
cinq groupes pour garder le même corpus de lecture ; ce diagnostic compte zéro
groupe qualifié. Les ralentissements de ptrace ne valent pas performance normale.
Le champ historique `events` compte les tours de boucle avant waitpid, y compris
les polls sans statut, pas des événements natifs effectifs. Le diagnostic les
sépare : tours, polls vides, statuts waitpid et stops de syscall. La preuve brute
échouée est inchangée ; aucun coût de traçage n'est déduit du seul nombre66178.

La revue du diagnostic préparé relève deux écarts à résoudre dans121.2 avant
première exécution : écritures concurrentes possibles du même fichier pending,
et résultat HTTP perdu avant observation si statut/décodage/transport échoue.
Décision avant correction du banc : sérialiser les sauvegardes par campagne ;
observer la réponse HTTP brute et ses erreurs expurgées dans finally, puis
maintenir200 comme unique réussite. Aucun changement de contrat produit.

Premier rouge : [preuve](evidence/execution-journal-final-lock-first-failed-dev-2026-11-22.json),
brutSHA `43182a4a…`, archive des499sources `09804d14…`. Le contrôle/référence,
leur démarrage, configuration et originaux sont conservés. Cause non établie ;
le premier rouge de buffer et son diagnostic restent des époques distinctes.

Diagnostic500sources/1aa70214 : [preuve](evidence/execution-journal-final-lock-diagnostic-dev-2026-11-22.json),
brutSHA `437fcbfa…`, zéro groupe qualifié et nettoyage physique acquis. GET503
log_read_unavailable à2074ms ; workers subject puis read, aucune entrée verify.
66184tours =64398polls vides+1786statuts waitpid, tous stops syscall sur ce passage.
72fcntl conservés sans dépassement. Le chemin shm exact est bien rencontré dans
les workers antérieurs ; aucun verrou final n'est atteint sur cette mesure.

Décision réversible avant code : remplacer le sommeil fixe0,5ms après chaque
poll vide du seul observateur par un réveil SIGCHLD sur pipe non bloquant,
`signal.set_wakeup_fd` et select borné à la même échéance. Les statuts se lisent
toujours par waitpid, jamais par le nombre d'octets du pipe ; vider le pipe,
préserver/restaurer handler et wakeupfd, fermer ses deux FD dans finally.
Conserver les mêmes sélecteurs, vérifications d'identité, plafonds et40/45/50/60s,
sans relâcher les2s du produit. Écarter l'allongement de budget et la suppression
des contrôles d'identité : ils changeraient ce que la preuve est censée éprouver.
Ajouter au prochain diagnostic un GET sans trace avant le même GET tracé sur le
même corpus ; comparer statut/délai et entrée effective dans journal-verify.
Ce correctif du banc reste à éprouver ; la seule hypothèse de son efficacité
ne clôture ni121.4, ni120.4, ni072.

## SLS-122 — Fermer le diagnostic après une restitution refusée

Statut : [~] — le replay de réveil121 acquiert le verrou final mais échoue
avant writer-blocked ; les premières vérifications de santé de restitution
échouent. La garde indépendante60s rétablit les threads et confirme ensuite
la santé. Le client quitte son finally avant fermeture navigateur/purge,
laissant son Node en attente et ses quatre fonctions possédées. Nature :
Corriger. Dépend de : SLS-040. Ordre : 3.

Résultat attendu : un échec natif conserve son rouge, joint ses processus et
ferme toujours les ressources locales. Une restitution non prouvée interdit la
purge jusqu'à sa confirmation ; une fois la garde terminée et le contrôle sain,
les seuls UUID possédés sont nettoyés avec un reçu distinct. Ne pas réécrire le
rapport échoué en succès ni faire d'une reprise opérateur une preuve nominale.

- [x] SLS-122.1 Sceller le replay échoué500sources, les reçus natifs et la garde
  indépendante ; arrêter/joindre seulement le Node et ses enfants identifiés,
  recouper le contrôle sain et purger les seules fixtures par API réelles.
- [x] SLS-122.2 Décision et motif avant correction du flux finally ; ressources
  navigateur/API/work toujours fermées, échecs primaires conservés, nettoyage
  conditionné à la restitution réellement acquise. Aucun rejeu du scénario.
- [ ] SLS-122.3 Éprouver le refus et sa clôture sur le vrai code déployé avec
  faute réelle et gardes jointes, puis replay121/12API/25communs frais ;
  aucune simulation, substitution de réponse, skip ou succès conditionnel.
  Le champ `independent` du reçu vaut le mode rescue : il ne prouve pas seul
  une expiration du timer. Une preuve attribuée à la garde60 recoupe son
  attempt_id exact avec la sortie journalisée par l'unité systemd possédée ;
  une restitution manuelle reste nommée manuelle. Ce recoupement est requis
  avant de qualifier le chemin de garde, même si la purge physique a réussi.

- [x] SLS-122.4 Éprouver le mode existant recover-low-fds sur la copie figée
  d'une garde terminée : vraie limite de descripteurs du seul restorer à zéro,
  errno24 et limite propre restaurée, unique JSON stdout, source/identités
  recoupées. Le contrôle/référence restent sains et inchangés, aucun consommateur
  recréé ; le reçu diagnostique failed ne devient pas un reçu de restitution.
  [Preuve réelle](evidence/execution-journal-restorer-low-fds-dev-2026-11-22.json) :
  errno24, limite propre restaurée, un JSON ; huitcompteurs0 et5982originaux.

Le rouge primaire reste celui de121 ; cette unité porte la clôture du banc,
pas la reconnaissance du writer ni un changement du budget produit.

Décision122 avant code : séparer une fermeture locale idempotente de la purge
métier ; l'appeler dans un finally externe, même si jonction ou sauvegarde
échoue. Conserver le premier échec dans failure/observations et le code1.
Après échec d'une tentative de restitution, observer le reçu de la garde déjà
armée, sans rejouer le scénario ni désarmer son timer. Le budget d'observation
client est125s depuis le lancement du helper :60s de déclenchement+55s de garde
existants+10s de jonction ; aucune borne native40/45/50/60 ni2s produit augmentée.
Une garde réellement terminée avec santé, identités et threads libérés permet
alors finish et la purge habituelle. Sans ce reçu, pas de purge : fermeture
locale quand même, rapport rouge et UUID laissés pour récupération explicite.
Les tentatives échouées demeurent dans les observations ; le reçu final ne les
réécrit pas. Le prochain replay conserve le défaut writer121 pour éprouver
cette clôture sur son échec réel, avec zéro groupe fonctionnel qualifié.

Preuve initiale et reprise : [replay/recovery](evidence/execution-journal-wakeup-writer-failed-dev-2026-11-22.json).
Brut primaire `cfbe96b3…`, archive500sources `146c4b4e…`. Le réveil acquiert
réellement verify/F_SETLK0 ; writer-blocked reste absent. GETsans trace200 en72ms,
GETtracé503 après44,8s. Garde indépendante60s puis confirmation explicite des
deux gardes ; Node ciblé par pidfd/SIGTERM, wrapper sort1/joint. Une nouvelle
session SSO vérifie les UUID/noms/descriptions puis purge les quatre fonctions,
révoque les13jetons et supprime leurs quatre services/namespace. Huitcompteurs0,
5982originaux, mêmes services/démarrages/configuration ; wrapper/Node/driver absents.
Le primaire reste cleanup=false ; la reprise opérateur reste une preuve distincte.

Le [replay de fermeture locale](evidence/execution-journal-local-closure-health-failed-dev-2026-11-22.json)
500sources est conservé : Node finit1 sans signal opérateur et paquet temporaire
absent, premier échec inchangé ; la purge reste refusée après125s car la garde
termine checking_health/failed. Une nouvelle récupération opérateur purge quatre
fonctions/13jetons/quatre services/namespace ; huitcompteurs0 et5982originaux.
Aucune de ces reprises ne constitue une réussite de clôture automatique.

Décision avant la suite du code122 : le contrôle de santé du restorer attend
HTTP200 et l'état Docker healthy à l'intérieur de son alarme55s EXISTANTE,
au lieu de conclure sur une seule photographie. Garder toutes ses observations
bornées et son dernier état ; ne jamais modifier/recréer le conteneur. Le reçu
porte PID/naissance/cgroup du restorer et origine réelle (unité systemd exacte
ou opérateur). Une ligne JSON d'ID de reçu est journalisée aussi en échec,
pour permettre le recoupement exact de l'origine ; le primaire reste échoué.

Isoler la preuve122 du discriminant writer121 : nouveau client original
`execution-journal-guard-closure.mjs`, un namespace/service/fonction/jeton, vrai
handler Docker puis vraie lecture finale retenue. Suspendre réellement le seul
helper identifié après held par son actionnative existante, et émettre le PUT
réel ; laisser la garde60s le tuer/restituer. Le client observe exclusivement
cette garde pour ce cas, sous125s, sans secours actif anticipé. Exiger helper
SIGSTOP attesté, reçu d'origine systemd réelle et journal corrélé, réponse de
lecture503 conservée en échec/code1, PUT réel abouti, purge physique et cinq
fermetures locales acquises. Zéro groupe qualifié ajouté ; les12API/25communs
restent dus après résolution121. Ce cas n'exige pas le EAGAIN noyau contesté.

Premier client isolé501sources : primaire503/code1 conservé, PUT200, garde
système confirmée par son cgroup, purge physique et cinq fermetures locales
réussies. Le contrôle indépendant du journal échoue dans l'orchestrateur privé ;
le passage reste donc à zéro groupe qualifié,122 non clôturée. Conserver ses
sources/rapports et déterminer ce refus de collecte avant toute correction.

Cause du refus de collecte501 : journalctl JSON sans `--all` remplace MESSAGE
par null au-delà4096octets ; le reçu fait7860octets. Décision avant nouveau
collecteur : relecture RO `--all` du même reçu déjà exécuté, typage MESSAGE et
recoupement exact attempt_id/PID/unité/naissance. Conserver l'orchestrateur
échoué et son brut ; aucune relance du SIGSTOP ou du handler n'est nécessaire
pour lire cette preuve existante. Cet addendum ne compte aucun groupe de plus.

Clôture de faute isolée attestée : [preuve501sources](evidence/execution-journal-independent-guard-closure-dev-2026-11-22.json).
SIGSTOP helper757199 puis SIGKILL par la garde ; GET503 à60,070s et PUT200 à58,947s.
La santé passe unhealthy→healthy dans55s, les threads sont libérés et la vraie
origine systemd (PID758216, attemptad7bfba1…) est recoupée avec MESSAGE7860octets,
SHA8f153bf7. Purge physique d'une fonction/jeton/service/namespace, cinqfermetures,
dixprocessus recensés absents et paquet temporaire retiré. Le primaire reste
completed=false/code1, cleanup=true ; zéro groupe qualifié. Le collecteur initial
échoué est conservé ; son addendum RO n'ajoute aucun handler ou faute.122 reste
[~] pour l'intégration12API/25communs, actuellement dépendante du défaut121.

Décision121 avant correction du banc, après la preuve de clôture122 : remplacer
l'attente EAGAIN par les phases de restauration du nom de worker existantes.
read-result retient après le résultat principal mais avant vérification finale
(PUT accepté→GET410) ; read-decision retient après final_check et son commit
(PUT accepté avant réponse→GET200 puis snapshot410) ; policy-commit retient
après write_policy (version/audit committés→vraie perte de réponse sans rejeu).
Pour les deux derniers, recouper acquisition/libération WAL du même TID/inode
avant son prctl de fin et exiger les succès HTTP/états qui discriminent le retour
normal du finally d'erreur. Aucune pile/registre/buffer n'est substitué ; aucun
symbole ou layout interne SQLite, single-step ou changement produit nécessaire.
L'arrêt dans SQLite est renommé sqlite-reservation et réservé à la faute122.
Les modes sont à implémenter puis prouver, toujours sous2s produit/40/45/50/60.


<a id="sls-123"></a>
## SLS-123 — Armer la coupure après le vrai compteur durable

Statut : [~] — le replay501sources/1aa70214 passe sept groupes dont API08,
puis le helper API10 sort1 après armed, avant cut ; stderr930octets non retenu.
Le contrôle ne redémarre pas, le handler finit normalement200, sa seule invocation
est retrouvée puis purgée. Nature : Corriger. Dépend de : SLS-040. Ordre : 3.
Contrat : [instrumentation native](EXECUTION_LOGS.md#instrumentation-native-des-lectures).

Résultat attendu : identifier l'échec d'armement sans l'attribuer au produit par
hypothèse, couper le contrôle seulement après le reçu fsync du vrai handler,
puis prouver interruption, reprise du suivi et compteur1 sans rejeu.

- [x] SLS-123.1 Sceller le rouge501sources, sept groupes partiels/zéro qualifié,
  les programmes et les preuves de restitution/purge de cinq fonctions et parents.
- [x] SLS-123.2 Diagnostic borné du helper réel : phase, type/errno, code public
  d'assertion et lignes de traceback, sans buffers applicatifs ni stderr brut.
  Rejouer le seul scénario compteur sur une fixture originale fraîche ; aucune
  donnéeSQL écrite, limite élargie ni signal avant acquittement durable.
- [x] SLS-123.3 Cause établie, décision/motif persistés avant correction du
  composant en cause ; conserver l'original rouge et ses sources figées.
- [ ] SLS-123.4 Replay API10 dans les12API puis25communs frais, code déployé et
  sources recoupés, gardes/processus joints, purge physique et captures inspectées.

Décision avant instrumentation : conserver un diagnostic structuré dans le seul
répertoire /run possédé et l'émettre en JSON avec unit. Nommer la phase et les
fichiers/lignes du helper ; ne conserver un message d'assertion que s'il appartient
à un vocabulaire statique du banc, sinon seulement son SHA. Le client conserve cet
événement avant de traiter la sortie. Ne pas réexécuter la fixture purgée ni déduire
une cause des seuls930octets ; une nouvelle exécution reste une époque distincte.

Preuve initiale : [rouge API10](evidence/execution-journal-control-arm-first-failed-dev-2026-11-22.json),
brut6947603a, archive501sources b39638e8. API08 passe partiellement ;121.4,
120.4 et122.3 attendent le replay complet après123.


Diagnostic123 : [preuve réelle](evidence/execution-journal-control-start-race-diagnostic-dev-2026-11-22.json).
Les trois chemins attendus appartiennent à1001 ; reçu synthétique valide,
compteur1. La ligneSQL de la même invocation est running/non terminée mais
handler_started=null lors de l'assertion ; elle finit ensuite normalement avec
handler_started=1. Ceci établit une course du banc sur ce passage, sans attribuer
rétroactivement une cause au premier rouge dépourvu de ce tuple.

Décision avant correction : l'état running/handler_started=null est une attente
transitoire, seulement si fonction/UUID et unique invocation active concordent,
avec reçu déjà validé. Continuer les sondes dans les30s EXISTANTES ; n'envoyer le
signal qu'après handler_started=1, sans accepter0, une autre fonction, un appel
terminé ni une activité étrangère. Conserver le premier tuple null et l'acquittement
suivant dans le reçu cut. Ne pas changer le runtime asynchrone ni retirer la
condition de démarrage pour satisfaire le banc.


Le [replay suivant](evidence/execution-journal-counter-pending-not-observed-dev-2026-11-22.json)
coupe réellement9/137 après acquittement1, mais échoue parce que sa première
sonde ne rencontre pas null. La récupération de nettoyage redémarre le mêmeCID
sur1aa ; purge physique acquise, sept groupes partiels/zéro qualifié.

Décision avant instrumentation complémentaire : préparer une instance chaude
sans appel préalable, tracer uniquement le principal jusqu'à la réception
réelle de `POST /started HTTP/1.1` sur son socketUNIX propre. Lire seulement la
ligne attendue, jamais les en-têtes/clé/corps, avec inode et chemin du canal liés
à l'instanceUUID et à la génération possédée. Retenir ce retour recv au plus1s,
à l'intérieur des30s existantes, observer le reçu fsync et le tuple null, puis
détacher immédiatement ; attendre ensuite1 avec les égalités déjà imposées.
Le handler poursuit réellement son travail pendant cette retenue du contrôle.
Aucun résultat de syscall remplacé, changement de runtime ni faux message.
Le signal reste interdit avant1. Après restitution, remettre le minimum0 de la
seule fixture pour éprouver son extinction. Ce placement natif rend la branche
à prouver observable ; il ne transforme pas l'ancien passage en réussite.


Premier [essai de réception](evidence/execution-journal-started-receive-first-failed-dev-2026-11-22.json) :
borne30s atteinte avant /started, invocation réelle503/storage_unavailable,
handler_started0. Les trois fonctions sont purgées ; zéro groupe qualifié.
La nouvelle barrière n'est pas acquise. L'observateur partagé utilise encore un
poll waitpid suivi de1ms de sommeil ; le défaut de coût similaire de121 rend
cette piste plausible, sans prouver la cause de ce503 particulier.

Décision avant diagnostic complémentaire : mesurer en nombres et temps les
stops/syscalls effectivement rencontrés, les retours read/recvfrom et un relevé
borné de32inodes/cheminsUNIX rencontrés, avec compteur de dépassement et booléen
instance correspondante. N'enregistrer que les chemins /state/execution ; pour
les autres, uniquement SHA. Ne lire aucun contenu supplémentaire. Conserver les
mêmes bornes et le même poll pour cette mesure avant correction de l'attente.


Les [mesures du poll](evidence/execution-journal-started-receive-poll-metrics-dev-2026-11-22.json)
conservent26249stops,24740polls vides et26974ms réellement passées en sommeil
sur la fenêtre30s. Quatre socketsUNIX sans nom, aucun canal instance reconnu.
Le coût propre du poll est établi ; aucune cause précise de stockage n'est
attribuée par le seul code public storage_unavailable.

Décision avant correction du banc : extraire sans modification NativeWakeup
actuel de l'opérateurSQL vers un moduleE2E commun, et l'utiliser aussi pour le
wait du seul CounterObserver. Attente SIGCHLD sur pipe non bloquant/CLOEXEC,
waitpid reste seul arbitre ; handlers/wakeupfd/FD toujours restaurés en finally.
Épingler le module dans les identités de programmes des deux opérateurs.
Ne changer ni matcher de socket, ni budgets, ni runtime ; conserver les mesures
pour le prochain diagnostic avant le full12. Cette extraction n'est pas une
nouvelle preuve des groupes121 : ils restent à rejouer avec le vecteur commun.


Le [replay SIGCHLD](evidence/execution-journal-started-receive-sigchld-scope-failed-dev-2026-11-22.json)
supprime le sommeil artificiel mais atteint100000stops en12,26s sans reconnaître
le canal. Le vrai compteur finit200/started1 ;67lectures sockets, seulement63
inodesUNIX retrouvés dans le netns du contrôle, tous anonymes. Zéro qualification.

Décision avant correction du sélecteur : épingler le seul conteneur runtime de
l'instance chaude, par labelsfonction/instance/révision, CID/image/PID/naissance,
cgroup et inode du netns. Recouper son unique montage /protocol avec le chemin
state/execution de l'instance ; exiger lecture seule et canalexact control.sock.
Rechercher l'inode du FD du contrôle dans les tablesUNIX du contrôle ET de ce
seul runtime, avec identité/propriété du runtime recontrôlées. Ne reconnaître la
ligne /started qu'après concordance inode+chemin+instance et consigner le netns
qui la fournit. Aucun autre conteneur, namespace ou buffer n'est inspecté.
La sourceLinux explique l'allocation du nouveau socket dans le netns du client ;
ce comportement reste à recouper sur la vraie cible, pas présumé comme preuve.
Ne modifier ni plafond100000, ni30s, ni retenue1s, ni runtime/protocole.


Le [diagnostic corrigé](evidence/execution-journal-counter-start-and-guard-diagnostic-dev-2026-11-22.json)
503sources/1aa acquiert réellement /started dans le netns du runtime, inode
absent du netns contrôle ; retenue6,514ms, mêmeUUID/reçu null→1. Cut9/137,
helper tué/joint par pidfd, garde45 attribuée à son unique reçu journalisé,
redémarrage du mêmeCID1aa, reprise du suivi et compteur toujours1. Trois fonctions
purgées, huitcompteurs0,5982originaux et configuration/référence conservés.
Diagnostic seul : zéro groupe qualifié ;123.4 et les12API/25communs restent ouverts.


<a id="sls-124"></a>
## SLS-124 — Restituer le focus des commandes Journaux

Statut : [~] — deux focusBODY reproduits sur512sources/bf9b61a6 ; trois
capturesdesktop inspectées, purge physique et compteurs0. Nature : Corriger. Dépend de : SLS-061. Ordre : 3. Contrats :
[console](EXECUTION_LOGS.md#console-et-manuel), [design local](DESIGN_SYSTEM_APP.md).

Résultat attendu : à la fermeture de Conservation et lors d'un refus invalidant
le suivi, le focus reste sur une commande active ou rejoint le titre ; aucune
commande focalisée ne devient désactivée sans relais.

- [x] SLS-124.1 Reproduire depuis l'accueil, SSO réel, clavier : ouvrir
  Conservation puis Échap sans changement ; relever le focus pendant/après le
  GET politique de fermeture. Garder l'état réellement observé, même s'il réfute
  le risque statique resource.reload→loading→déclencheur désactivé.
- [x] SLS-124.2 Reproduire avec le focus sur Pause et une vraie invalidation de
  politique ou droits : refus, lignes retirées, commande désactivée et relais
  effectif observés. Aucune interception ni réponse substituée.
- [ ] SLS-124.3 Si défaut confirmé, décision/motif avant correction ; conserver
  les rouges et rejouer les dix UI et25communs frais sur le code déployé, captures
  ouvertes individuellement, contextes/gardes joints et purge physique.

Décision de diagnostic124 avant client : éprouver les deux risques sur le web
inchangé de l'imagebf9b61a6, après reprise128, avant la campagne finale. Partir
de l'accueil avec une fonction originale et un SSO réel, commandes clavier,
GET de politique réel et PUT de version réel provoquant410 du suivi. Conserver
les événementsfocus natifs pendant Échap/relecture, le focusfinal et trois
captures, ainsi que les erreursPage. Les deux observations précèdent leur
assertion commune pour conserver un éventuel succès et l'autre défaut. Aucun
focus forcé au résultat, réponse substituée, interception, mock ou succès
conditionnel. Ce préparatoire compte zéro groupe qualifié ; les parcours
UI06/UI09 et la campagne10UI/25communs gardent leurs preuves propres.

Ces vérifications complètent UI06/UI09 déjà prévus ; elles ne créent pas deux
groupes supplémentaires. Le risque statique seul ne vaut pas preuve d'un défaut
ni autorisation de masquer un échec du banc.


<a id="sls-125"></a>
## SLS-125 — Recouper le hash des événements conservés après purge du frère

Statut : [~] — replay503sources/1aa passe huit groupes puis échoue API11 ligne397,
après purge du frère, sur items nonvides et tous code_hash identiques au hash
publié. La réponse de ce GET n'a pas été conservée avant assertion. Nature :
Corriger. Dépend de : SLS-040. Ordre : 3. Contrat :
[modèle/corrélation](EXECUTION_LOGS.md#modèle-et-migration-011).

Résultat attendu : conserver les événements de la fonction sœur encore visible,
avec leur corrélation honnête aux étapes d'exécution ; refuser toute attribution
inventée d'un hash à un événement où il n'était pas connu. Départager le défaut
produit du mauvais oracle sur des champs réellement retournés.

- [x] SLS-125.1 Sceller le rouge503sources, huit groupes partiels/zéro qualifié,
  ses programmes, gardes et purge physique. [Preuve](evidence/execution-journal-correlation-hash-first-failed-dev-2026-11-22.json).
- [x] SLS-125.2 Reproduire API11 isolément avec les mêmes vrais appels/purge ;
  conserver avant assertion total/items et leurs id/kind/state/function_id/
  invocation_id/code_hash, hash attendu et hash résolu de l'invocation native.
  Pas de messages, secrets, donnéesSQL écrites ni réponse substituée.
- [x] SLS-125.3 Cause recoupée contre le contrat, décision/motif commités avant
  correction de l'élément en cause ; rouge et source initiale inchangés.
- [ ] SLS-125.4 Replay dans12API puis25communs frais, sources et image du code
  déployé recoupées, gardes/consommateurs joints, purge physique et captures
  communes inspectées. Les autres critères072 gardent leurs preuves propres.

Décision avant diagnostic : ne changer ni l'oracle ni le produit ; sauvegarder
les champs bornés ci-dessus avant l'assertion et exécuter seulement la préparation
originale et correlations(), avec ses fautes réelles et sa purge du frère.
Si le préfixe complet est nécessaire à la reproduction, le nommer et le rejouer
ensuite, sans considérer un diagnostic nonreproducteur comme une réussite.


Diagnostic125 : [cinq événements réellement conservés](evidence/execution-journal-correlation-hash-diagnostic-dev-2026-11-22.json).
received/queued portent null, admitted/dispatched/completed portent le hash résolu
450d33a8…, identique au hash publié. Le producteur capture la ligne d'invocation
lors de chaque transition ; resolved_code_hash n'est affecté qu'à l'admission.
La lecture n'enrichit pas rétroactivement l'événement avec une cible plus récente.

Décision avant correction : corriger le seul oracle API11. Exiger les cinq étapes
avec leurs vrais sujets ; comparer les DTO complets avant/après purge du frère.
Hash/révision/instance restent null pour reçu/enfile ; à partir de l'admission,
ils correspondent à la révision/instance et au hash réellement résolus. Une
absence d'événement, une modification ou une autre référence échoue. Ne remplir
aucun hash rétroactivement et ne modifier ni schéma ni produit pour le banc.

Avant le prochain full12, éprouver séparément les trois groupes encore jamais
atteints (lecteurs API12 et budgets API05/06), avec les mêmes helpers et de vrais
corpus. Ce client préparatoire ajoute zéro groupe qualifié ; il ne remplace pas
le full12/25communs et ne saute aucun scénario de la campagne finale. Son rôle
est de départager les échecs nouveaux avant de refaire le préfixe déjà observé.


<a id="sls-126"></a>
## SLS-126 — Acquérir les lecteurs retenus d'API12

Statut : [~] — préparatoire505sources/1aa échoue dans l'attente d'une barrière
API12, client source_line62 ; trois propriétaires natifs sont relevés, nettoyage
physique acquis, API05/06 non exécutés. Nature : Corriger. Dépend de : SLS-040.
Ordre : 3. Contrat : [instrumentation native](EXECUTION_LOGS.md#instrumentation-native-des-lectures).

Résultat attendu : éprouver les deux vrais lecteurs retenus,429,deadline/jonction,
EOF/perte de helper et EMFILE réel avec leurs gardes, sans confondre un refus du
banc avec celui du produit ni relâcher les délais.

- [x] SLS-126.1 Sceller le préparatoire échoué505sources, ses programmes/reçus,
  zéro groupe qualifié et purge physique ; situer précisément le mode/phase.
- [x] SLS-126.2 Reproduire et départager le défaut à partir des reçus natifs,
  des vrais résultatsHTTP et d'un diagnostic borné si nécessaire. Aucun résultat
  injecté, thread supposé acquis, registre modifié ni étatSQL fabriqué.
- [x] SLS-126.3 Cause recoupée et décision/motif commités avant correction du
  composant en cause ; conserver les sources et le rouge originaux.
- [ ] SLS-126.4 Rejouer API12 puis API05/06 et12API/25communs frais sur le code
  déployé, gardes/processus joints, purge physique, captures communes inspectées.
- [x] SLS-126.5 Éclairer le GET503 inattendu du replay512/a7d, vagueEOF :
  conserver rouge/retours natifs, identifier le chemin, le refus et sa phase
  avant toute correction. Une finSSH pendant le secours n'est pas attribuée
  d'office à l'échec primaire ; reçus et ordre doivent la départager.



Premierrouge : [preuve](evidence/execution-journal-readers-acquisition-first-failed-dev-2026-11-22.json).
Release et EOF acquièrent2, la troisième vague prévuekill ne retient qu'un
worker openatDB. Un autre journal-read passe en journal-verify et finit son
travail avant0,9s. Le matcher d'ouverture n'a donc pas retenu tous les lecteurs ;
leurs réponsesHTTP ne sont pas encore conservées. SQLite peut réutiliser un FD
de base existant, ce qui rend plausible une lecture sans nouvelle ouverture,
sans attribuer encore cette cause à l'exécution observée.

Décision avant diagnostic : garder l'oracle et le matcher, enregistrer chaque
vague/mode, statut/code public/durée/fin des deux GET avant assertions. Ajouter
aux reçus natifs au plus64openat des seuls workersjournal-read : typeDB/WAL/SHM
ou SHA d'autre chemin borné, retour, TID et instant. Aucun autre contenu mémoire,
en-tête/corps, FD remplacé, valeurSQL écrite ou budget élargi. Rejouer les trois
vagues puis la vraie faute comme dans API12, zéro groupe qualifié pour ce relevé.


Diagnostic126 : [deux GET200 sans ouverture DBprincipale](evidence/execution-journal-readers-openat-diagnostic-dev-2026-11-22.json).
Deux workers lisent correctement, trois openat WAL/SHM et zéro DBprincipale,
sans dépassement du relevé. Le matcher manque donc des lectures valides. Le
réemploiFD décrit parSQLite explique une possibilité, sans identification de
sa fonction interne dans cette exécution ; cette identification n'est pas
nécessaire pour écarter la précondition erronée du banc.

Décision avant correction : ajouter le mode explicite reader-start et l'utiliser
pour les trois vagues API12 seulement. Reconnaître l'entrée prctl157/commande15
avec argument exact journal-read, puis sa sortie0 sur le mêmeTID/naissance et
comm journal-read ; distinguer cette affectation initiale de sa restauration.
Deux TID distincts sont retenus avant le callbackSQL, sans mutexSQLite ni
hypothèse d'ouverture de FD ; vérifier429/santé puis, après2,1s réelles, exiger
503/log_read_timeout à la jonction. Restituer via release/EOF/SIGKILL et recouper
la capacité revenue. Les40/45/50/60s natifs et2s produit restent inchangés.
Le modefault conserve une vraie entréeopenatDB et son résultat noyauEMFILE,
limite restaurée avantPython ; un prctl ou un autre503 ne vaut pas cette preuve.
Le mode read historique et les autres frontières restent inchangés. Aucun
hook produit, nouvelle réouverture forcée, faux résultat ou écritureSQL.


<a id="sls-127"></a>
## SLS-127 — Recouper le refus SQLite après épuisement de descripteurs

Statut : [~] — replay506sources/1aa passe les trois vagues reader-start,
constate réellement native-fault/syscall_result=-24 et limite restaurée, puis
échoue dans l'oracleHTTP attendu503 (harness124). Le statut réel de cette dernière
réponse n'est pas conservé avant assertion. Nature : Corriger. Dépend de :
SLS-040. Ordre : 3. Contrat : [défaut natif](EXECUTION_LOGS.md#instrumentation-native-des-lectures).

Résultat attendu : distinguer un errno noyau récupéré parSQLite d'une lecture
réellement refusée ; si le banc prétend éprouver503, conserver un refus réel
jusqu'à sa propagation et restaurer les limites/threads sans forger de résultat.

- [x] SLS-127.1 Sceller le replay201ade72, trois vagues acquises partiellement,
  faute native, sources/programmes, purge physique et zéro groupe qualifié.
- [x] SLS-127.2 Diagnostic du vrai statut/code/délaiHTTP et des ouverturesSQLite
  de cette faute, phases/flags/retours et restauration, avant toute correction.
  Aucune valeur injectée, erreur supposée terminale ni étatSQL fabriqué.
- [x] SLS-127.3 Cause recoupée, décision/motif persistés avant correction du
  seul élément en cause ; rouge et sources initiales conservés.
- [ ] SLS-127.4 Éprouver le défaut réel corrigé puis les trois vagues et budgets,
 12API/25communs frais, mêmes sources/image déployées, gardes/jonctions/purge
  physiques et captures communes inspectées.126 garde ses critères propres.


Premier rouge127 : [trois vagues puis HTTP200 après EMFILE](evidence/execution-journal-emfile-first-failed-dev-2026-11-22.json).
Le SHA exact de unexpected_http_status:GET:200 recoupe le statut ; le corps et
le délai de cette réponse ne sont pas capturés. Les quatre gardes sont jointes,
limites restaurées, purge physique acquise, zéro groupe qualifié.

Décision avant diagnostic127 : conserver la faute (limite0 puis restauration
immédiate après le premier errno24) et son oracle503. Capturer statut/code/délai
avant assertion et les flags d'ouverture. Après restauration, observer au plus64
arrêts et2s du seul TID jusqu'au retour d'une éventuelle nouvelle ouverture du
même fichier ; autres threads toujours acquis et restitution dans finally.
Aucun registre, résultat, buffer applicatif ou SQL modifié. Un client préparatoire
limité à cette faute réutilise le même cas queAPI12 ; zéro groupe qualifié.
SQLite unixOpen prévoit une tentative read-only après l'échec read-write
([source officielle](https://raw.githubusercontent.com/sqlite/sqlite/master/src/os_unix.c),
branche Failed to open the file for read/write access). Cela motive le relevé,
sans prouver encore que cette branche s'exécute dans notre binaire.


Diagnostic127 : [deux ouvertures réelles, récupération confirmée](evidence/execution-journal-emfile-recovery-diagnostic-dev-2026-11-22.json).
Flags655426/access_mode2 → errno24 ; après restauration, flags655360/mode0 →
FD11, puisHTTP200 en168,47ms. Même fichier/TID/naissance, deux arrêts après
restauration, aucun registre ou résultat modifié, garde et purge jointes.
Cela recoupe la reprise read-only prévue parunixOpen ; aucun défaut produit
n'est établi et le scénario n'obtient aucun groupe qualifié.

Décision avant correction127 : maintenir la limite0 pendant les deux tentatives
réelles RW puisRO du même fichier/TID, exiger les deux retours noyauEMFILE,
puis restaurer la limite à la sortie de la seconde ouverture, avantPython.
Garder2s/64arrêts, acquisition de tous les autres threads, garde indépendante,
restaurationfinally, propriétaires et programmes attestés. Exiger dans le client
503/log_read_unavailable puis une lecture réussie après jonction. Si la
seconde ouverture n'est pas observée ou réussit, le banc échoue sans prétendre
avoir prouvé le refus. Aucune modification du produit ni fauxerrno ; restaurer
après le premier échec est écarté car cette faute est réellement récupérée.


Replay127 isolé : [deuxEMFILE,503 et reprise](evidence/execution-journal-emfile-both-opens-replay-dev-2026-11-22.json).
Les deux openat renvoient réellement-24 sous limite0 ; restauration à la seconde
sortie, HTTP503/log_read_unavailable en198,22ms, puis lecture réussie. Garde
jointe, purge physique, huit compteurs0, même1aa/référence/config/5982artefacts.
Revue RO du helper/oracle : aucunP1/P2 trouvé ; elle reste distincte de la preuve.
507sources gelées ; préparatoire zéro groupe qualifié,127.4 reste ouvert.


<a id="sls-128"></a>
## SLS-128 — Rétablir la purge après le corpus réel de16Mio

Statut : [~] — préparatoire507sources/1aa09e9ab57 : API12 etAPI05 passent,
le corpus exactAPI06 atteint16777216octets/5169événements, puis POST503 à la
retraite du corpus et de nouveau pendant son nettoyage. Cinq ressources locales
fermées maiscleanupfalse ; le second corpus+1 n'est pas exécuté.
Nature : Corriger. Dépend de : SLS-040. Ordre : 3.
Contrats : [budget](EXECUTION_LOGS.md#conservation-par-service-et-budget),
[purge](CONSOLE_STORAGE.md).

Résultat attendu : purger par les véritables API le corpus possédé après la
borne16Mio, comprendre le refus503 sans supposer sa cause, finir le second
corpus+1 puis les campagnes propres et communes, sans étatSQL fabriqué.

- [x] SLS-128.1 Conserver rouge, programmes, résultat exact16Mio, références
  possédées et erreurs primaires/nettoyage ; relever l'état natif actuel.
- [x] SLS-128.2 Recouper le chemin/code public du503, propriétaires, opérations,
  délais et erreurs réelles. Décider et écrire la cause/issue avant correction.
  Reprendre le nettoyage uniquement sur les ressources possédées, via les API,
  en conservant le premier rouge ; aucune suppression SQL ni faux succès.
- [ ] SLS-128.3 Corriger le seul composant en cause, puis prouver sa reprise,
  purge physique et compteurs vides ; corpus16Mio puis+1 et12API/25communs sur
  les sources déployées, captures inspectées et gardes/consommateurs joints.


Premierrouge128 : [corpus exact puis refus de purge](evidence/execution-journal-byte-purge-first-failed-dev-2026-11-22.json).
Le SHA du harnais recoupe POST503. Le relevéRO conserve5169événements/
16777089octets après les tentatives, zéro fonction active/instance/opération,
mais archive389b71c3 nonpurgée et service/namespace encore présents. Cinq
ressources locales closes, aucun succès de nettoyage physique annoncé.

Décision avant diagnostic128 : relever enRO les commandes de stockage et leur
error_code, l'état du registre et des propriétaires, sans messages/secrets.
Faire une seule nouvelle intention de purge sur cette archive possédée, via
SSO/APIréels, avec UUID persisté avantPOST, If-Match et nom courant exact ;
conserver chemin, statut, code public et durée avantassertion. Si une commande
est déjà active, la joindre au lieu d'en créer une. Un503 garde son intention
et reste rouge ; pas de répétition automatique aveugle. La reprise éventuelle
du nettoyage réutilise uniquement les UUID de ce rapport et prouve ensuite
l'absence physique et les parents supprimés, sans réécrire le rapport initial.


Diagnostic128 : [tmpfs rempli par le journalSQLite temporaire](evidence/execution-journal-byte-purge-temp-full-diagnostic-dev-2026-11-22.json).
L'unique intention conservée reçoit503 en521,64ms. Même request_id dans
SQLITE_FULL/purge_function224 ; /proc du PID/naissance/CID1aa épinglés montre
un FD etilqs déjà délié de16777216octets, /tmp libre0 puis16777216 après fermeture.
La base dispose de100Go et de nombreuses pages libres. SQLite3.46.1 actif,
aucun trigger surinvocations, seules FKfunction_id/service_id, inchangées par
cet effacement.248logs occupent16067621octets ; leurs pages avant modification
font déborder le sous-journal d'instruction dans /tmp16Mio. Aucun contenu lu.

Décision avant correction128 : les deux effacements de logs par fonction/service
utilisent UPDATE OR ROLLBACK dans leur transaction existante. SQLite documente
l'absence de statementjournal pour cette clause ; notre Database.transaction
annule déjà toute la transaction si une exception est propagée et vérifie
in_transaction avantROLLBACK. Même effacement atomique, sans nouveau budgetRAM,
montage, pragma global, dépendance ou changement de rétention. Augmenter/tmp
repousserait la panne sans corriger cette sauvegarde d'instruction inutile ;
forcer temp_store en mémoire déplacerait le problème vers les512Mio du contrôle.

Après construction et mise à jour gardée011→011, reprendre une seule intention
sur l'archive possédée et prouver son succès, l'absence de saturationtmp, la
purge physique et le retrait des parents. Les deux corpusAPI06 gardent leurs
bornesexactes ; après+1, archiver la fonction puis supprimer son service avant
purge physique éprouve aussi l'effacement bulk parservice. Chaque refus avant
cette décision reste rouge ;12API/10UI/25communs frais restent requis.
Sources : [journaux d'instructionSQLite](https://www.sqlite.org/tempfiles.html#statement_journal_files),
[ROLLBACK](https://www.sqlite.org/lang_conflict.html). La mise à jour conserve
la base011 et ne remet jamais046 ni une ancienne sauvegarde ; son contrat
spécifique doit précéder son pilote.


Complément de décision128 avant pilote : la voie prepare-update et sa garde
sont spécifiées dans [mise à jour compatible011](EXECUTION_LOG_DEPLOYMENT.md#mise-à-jour-de-code-compatible011--sls-128).
Elle garde la baseline1aa et une candidate011 distincte, les onze migrations,
le schémaSQL, toutes les tables et la collection nonvide exacts ; seule l'image
et sa génération changent. Même supervision et jonction140/200/180s, label/nonce
propre, sauvegardes natives avant/aprèsarrêt, reprise enavant après intention,
aucun046 ni restauration deDB. L'archive retenue constitue la donnée protégée
de cette mise à jour, pas une précondition à masquer en la supprimant.


128 — correctif et prérequis préparés : les deux clausesSQL sont écrites,
revueRO sansP1/P2 restant sur leur sémantique ; imagebf9b61a6 construite/inspectée,
42backend/quatreweb, seul execution_logs.py différent de1aa. Contrôleactif et
référence inchangés. Le pilote prepare-update compare la baseline embarquée,
schéma/table/collection complets et distingue le résultat réel de l'unité des
seuls fichiers de reçu. Trois écarts de revue (schema_migrations dispensée,
préflightmanifeste absent, failed assimiléàinactive) sont corrigés avant exécution.
Compilation/diff passent ; la miseàjour et la reprise API ne sont pas encore
éprouvées.128.3 reste ouvert.


128 — [miseàjour et reprise physique acquises](evidence/execution-journal-purge-recovery-dev-2026-11-22.json).
L'unité20da0f11 termineinactive/Resultsuccess, MainPID/ControlPID0/cgroupvide ;
les clientsDocker sont joints. CID7574a50f/imagebf9b61a6 remplace1aa, tables/schema/
collection nonvide égaux au backupfinal, onze migrations, configuration/référence
conservées, aucune restaurationDB. Le POST de reprise donne202 en1129,77ms puis
completed ; /tmp garde16777216octets libres sur5067mesures et aucunFDtemporaire
observé. Trois fonctions, trois services et le namespace antérieurs sont retirés,
huit compteurs0 et5982originaux recoupés.511sources ; zéro groupe complet qualifié.
Le premier rouge reste inchangé.128.3 reste ouvert pour la secondevoie service,
les corpus et campagnes complètes.124 peut maintenant éprouver ses deux risques
sur les mêmes ressourcesweb inchangées avant la prochaine campagne finale.


124 — [deux pertes de focus réelles](evidence/execution-journal-focus-first-failed-dev-2026-11-22.json).
Échap : INPUT→BUTTON actif→BUTTON désactivé→BODY durant relectureGET200.
Suivi : Pause focalisée avantPUTpolitique1→2 ; après refus, lignes0, Reprendre
indisponible et focusBODY. TroisJPEG ouverts individuellement, aucun autre
défaut visuel bloquant ; Pageerrors0, purge et huit compteurs0. Le statut exact
du GETinvalidé n'est pas conservé par ce premier client ; le replay le relèvera.
Zéro groupe qualifié.

Décision avant correction124 : conserver la relecture après fermeture et porter
dans le parent une intention de focus. Un effet après démontage et restitution
passive du dialog rejoint le titre stable Conservation si le focus reste sur
le déclencheur ouBODY ; un autre contrôle choisi entretemps est respecté. Cela
évite le déclencheur transitoirement désactivé sans temporisation ni changement
du dialog partagé. Relais ponctuel, annulé à l'ouverture suivante. Une ref sur
Pause/Reprendre permet de focaliser le titreJournaux avant désactivation lors
d'un refus invalidant ; les autres contrôles conservent le focus. Aucun nouveau
style/token. Manuel et design local nomment ces replis. Rejouer les deux vrais
parcours avec statutHTTP410, captures desktop/mobile, puis10UI/25communs frais.
Les premiers rouge et sources restent conservés.


124 — décision avant extension du pilote : profil journal-focus, baselinebf9
et backend42 strictement identique, CSS/favicon conservés ; JavaScript et
index.html recompilés avec le manuel seulement. Contrat de [mise à jour du focus](EXECUTION_LOG_DEPLOYMENT.md#mise-à-jour-du-focus--sls-124).
Le profilpurge-rollback128 n'est pas assoupli ; le nouveaupréflight recoupe le
manifeste de la baseline embarquée. Même garde011→011/possession/reprise, aucune
restaurationDB. La relecture du correctif et sa qualification restent ouvertes.


124 — correctif écrit/relu : intention ponctuelle du parentConservation après
cleanup passif, ref de la commande de suivi et relais avant désactivation.
Aucun P1/P2 statique restant ; les deux designsystems ont été lus entièrement.
Build local puis imagea7d7491a inspectée :42backend identiques àbf, CSS/favicon
conservés, JS/HTML seuls changés. Le profiljournal-focus est relu, les deux voies
SQL/UI restent strictes. Le client préparatoire attend maintenant le vrai410
et mesure les titres en1440/390px avec six vues. Bascule et replay restent à faire,
10UI/25communs nonqualifiés ;124.3 reste ouvert.


126 — nouveau reste de qualification : replay02ce7249/512sources/a7d passe la
vague release, puis échoue sur unexpected_http_status:GET:503 pendantEOF.
Deuxworkers étaient acquis ; les deuxGET détenus finissent200 en~1s après
restitution. La finSSH255 et le reçu de restauration sont observés pendant le
secours ; ils ne prouvent pas une panne primaire du transport. Kill/fault et
les budgets ne sont pas atteints. Nettoyage physique acquis, huitcompteurs0,
512sources/image stables. Ce résultat appartient à126.4/.5 toujours ouverts.

Décision avant diagnostic126.5 : conserver les appels et leurs statuts attendus.
Avant toute assertionHTTP inattendue du harness, relever méthode, route fixée
ou son SHA (jamais query/corps/en-têtesconfidentiels), statutsattendus/réel,
durée et SHA/taille du corps. Pour un JSONd'erreur auplus16Kio, conserver le
SHA du champ error et uniquement un code log_ appartenant à la liste constante
du contrôle. Aucun contenu libre du corps n'est publié. Ce relevé ne change
aucune réponse, deadline ou attente. Rejouer seulement readers() avec son client
préparatoire existant, zéro groupequalifié ; recouper les reçus de secours et
les traces natives si nécessaire. Cause et issue restent à établir avantfix.


126.5 — [rouge scellé du GET503](evidence/execution-journal-reader-wave-http-first-failed-dev-2026-11-22.json).
Le finally du client appelle recover pour une barrière nonclose : son arrêt du
helper peut expliquerSSH255 et les retours200 avantdeadline. Cette fin n'est
donc pas qualifiée de panne primaire du transport. L'objet à identifier reste
le GET503 avant l'actionEOF. Les programmes et premiers reçus sont conservés.


126.5 — relevéRO des logs : dans la fenêtreEOF,429/logs précède503/healthz ;
deux execution.maintenance_failed/OperationalError sont relevés avant les deux
reader-held. Aucune database.unavailable dans ce relevé. Le contrôle conserve
l'erreur de maintenance jusqu'au succès d'un prochain tick ; le codeSQLite et
le détailHTTP du premier503 ne sont pas reconstructibles à partir de ce log.
Un premier replay du même cas avec relevéHTTP a passé troisvagues+EMFILE,
sans503inattendu : il ne prouve pas la cause du premier. Avant toute correction,
le préparatoire peut répéterreaders() auplus3fois, s'arrêtant au premier échec,
statuts/deadlines inchangés, zéro groupequalifié et purge unique à la fin.


126.5 — [replaydiagnostic sans reproduction et logs du premier rouge](evidence/execution-journal-reader-health-diagnostic-dev-2026-11-22.json).
Les troisvagues et les deux vraisEMFILE passent, restitution/purge et huitcompteurs0.
Zéro groupecompletqualifié et aucune cause attribuée au premier503. Le harness
conserve désormais tout refus inattendu avant assertion sous forme expurgée ;
la reproduction limitéeàtrois itérations s'arrête au premier échec.126.5 resteouvert.


124 — [replay préparatoire positif et six captures inspectées](evidence/execution-journal-focus-replay-dev-2026-11-22.json).
Bascule9a4eb277 inactive/Resultsuccess,16clientsDockerjoints, toutes tables,
schéma et collection égaux au backupfinal, backend42/CSS/favicon conservés.
Imagea7d7491a/CID218c13d1. Quatre focusH2 en1440/390, deux vrais410/
log_policy_changed aprèsPUTversion, Pageerrors0 ; fonction/jeton/parents purgés,
huitcompteurs0 et5982originaux.512sources identiques au commit6f6fefc.
Zéro groupecompletqualifié ;124.3 reste ouvert pour intentionssuccessives,
respect d'un autrecontrôle et10UI/25communs. Les images mobiles ne cadrent pas
le refus souslepli : sa preuve estDOM/HTTP, pas visuelle.


126.5 — [reproduction bornée rouge](evidence/execution-journal-reader-health-repeated-failed-dev-2026-11-22.json) :
les deux premières itérations passent, la troisième échoue pendant release.
Le GET/healthz503 conserve le SHA exact de « Les planifications doivent être
réconciliées. » ; les logs recoupent schedules.maintenance_failed/OperationalError
avant les deuxworkersheld. Le codeSQLite précis reste inconnu. Restitution/purge,
huitcompteurs0 et5982originaux acquis ; zéro groupequalifié. Aucune attente assouplie.

128 — décision avant préparatoire indépendant : exécuter les seules fonctions
eventBudget puisbyteBudget existantes, avec leurs deuxcorpus16Mio/+1, purgefonction
et effacementservice réels. Pas de préfixereaders susceptible de masquer cette
preuve indépendante, aucun oracle changé, zéro groupecompletqualifié. Le client
reste possesseur de toutes ses ressources et les purge en finally. Le full12
reste requis ensuite sur la même source déployée.

128 — [budgets et purges ciblés acquis](evidence/execution-journal-budgets-purge-replay-dev-2026-11-22.json) :
89e99d13/514sources/imagea7d :10000/+1,16777216exact puis16777217avantéviction ;
ce dernier conserve16777154octets/5168événements. La suppression du service
vide248anciens buffers (expired/0octet) et le registre avant purge physique.
Trois fonctions et leurs parents retirés, huitcompteurs0/5982originaux conservés.
Zéro groupecompletqualifié ;128.3 reste ouvert pour les campagnes complètes.

126.5 — décision avant instrumentation du contrôle : enrichir exclusivement les
logs maintenance_failed des deux moteurs, avec codeSQLite étendu et site/phase,
sans texte d'exception ni SQL ; préserver flags santé/cadences et mêmes refus.
Le contrat EXECUTION_LOGS et le profil maintenance-diagnostics011→011 partant
d'a7d figent cette modification avant code. La prochaine reproduction doit
établir le code exact avant toute correction ; aucun retry santé ajouté.

126.5 — revue avant bascule : recover intercepte ses propres exceptions ; son
événement execution.recovery_failed reçoit aussi code/site/phase expurgés au
point de capture, sans relance et sans changer l'état. Ce complément contractuel
précède son code ; le profil conserve les deux seuls fichiers backend autorisés.

126.5 — [diagnosticSQLite exact acquis](evidence/execution-journal-maintenance-code-diagnostic-dev-2026-11-22.json).
Bascule0c195234 terminéeinactive/Resultsuccess/cgroupvide/16clientsjoints ;
CID88201d21/imagef73efa6e, backenddeuxdiffs/webidentique, schema/tables/collection
égaux au backupfinal, configurations/référence conservées. Rouge13fab054/514sources :
EOFhealth503 après SQLITE_BUSY_RECOVERY261 des planifications etBUSY5 du moteur,
db.transaction41/BEGINIMMEDIATE, avantheld44.582/44.589s. Le flagplanning posé
à44.531s est relu parhealth44.724s avant sa prochaine maintenance0,5s.
La préparationptrace arrête aussi les workersjournal-subject avant détachement ;
aucune erreur SQLite n'est attribuée aux deuxlecteurs qui restent avantSQL.
Restitution/purge acquises, huitcompteurs0/5982originaux ; zéro groupequalifié.

126.5 — décision avant correction du banc : la santé200 préalable à chaque
armement reste stricte. Aprèsheld/détachement seulement, une préparationnommée
bornée1000ms/21sondes, comprise dans45s moins5s réservées, observe la reprise
réelle des maintenances. Tous refus/probes sont conservés ; codes5/261 auBEGIN
à recouper enRO avantqualification, autres anomalies refusées. Aucun réarmement,
rejeuGET, changementflag/délai2s. Ensuite429→health200→2,1s→429 et les actions/
jonctions restent exécutés unefois ; tout échec qualifié échoue immédiatement.
Contrat complet EXECUTION_LOGS, anciensrougesinchangés. Le détenteur exact du
verrou resteinconnu ; la preuve ne promet pas santé200 pendantacquisitionptrace.

126.5 — [replay préparatoire positif](evidence/execution-journal-reader-preparation-replay-dev-2026-11-22.json) :
f0d9fd63/514sources efba3fe/f73, troisitérations/neufvagues/troisEMFILE. Deux
préparations observent11health503, toutes stabilisées enmoins390,06ms et recoupées
automatiquement au boncomposant/codes5/261/siteBEGIN ; tousautresdéfautspropriétaires
oumaintenance sont refusés. Ensuite neuf429→health200→délai→429 et jonctions
503timeout passent. Aucunprimitifréarmé, mêmesdeadlines ; huitcompteurs0/5982originaux.
126.5 éclairci avec limite explicite : codeSQL/corps du toutpremier512 nonconservés,
aucune rétroattribution.126.4/ensemble restent ouverts pour12API/25communs frais.

072/124 — le client e2e/execution-journal-ui.mjs porte maintenant les dixgroupes
du contrat, avec vrai SSO/API/handlers, captures, jonctions et purge. La revue a
corrigé ses locators/états/insertions avant exécution ; aucun P1/P2 restant
statiquement. Il utilise le vrai modehorsligne et la latence du navigateur,
avec restaurationfinally, jamais des routes ou réponses fabriquées. La perte
d'un PUT est retenue après son commit natif, puis relue sans rejeu. Syntaxe seule
vérifiée, aucune preuvefonctionnelle UI acquise ; premièrecampagne à exécuter.
