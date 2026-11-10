# Objectif autonome de reprise

Plan de découpage persisté le 10 novembre 2026, après la revue des écarts et les
demandes du responsable : parité avec Scaleway Serverless, jobs de console,
crons, exploitation reproductible. Il remplace l'objectif initial pour la suite
du travail ; l'état réel de chaque unité reste dans [le backlog](BACKLOG.md) et
[le suivi des demandes](DEMANDES_ET_LIVRAISON.md).

## Texte du goal à transmettre à l'agent

```
/goal **Terminer dans `/home/p2enjoy/Documents/VSCodeProjects/p2enjoy-serverless` la plateforme P2Enjoy Serverless : répliquer les fonctionnalités de Scaleway Serverless sur le SPARK DEV, avec une console web complète, et clore chaque unité du backlog par des preuves E2E réelles.**

Première action : lis INTÉGRALEMENT `CLAUDE.md`, `CLAUDE_PROJECT.md`, `AGENTS.md`, `README.md`, `docs/BACKLOG.md`, `docs/DEMANDES_ET_LIVRAISON.md`, `docs/OBJECTIF_AUTONOME.md` et `docs/CloudWorker.md` (appliqué avec les adaptations de `CLAUDE_PROJECT.md#adaptation-de-cloudworker`). Vérifie `git status` et `git log` ; des commits locaux peuvent attendre un push : pousse-les d'abord avec tes identifiants. Les documents de méthode (`CLAUDE.md`, `docs/CloudWorker.md`, `docs/.routine`, `docs/AUTOMATION.md`, `docs/DESIGN_SYSTEM.md`) ne sont modifiés que sur instruction explicite.

Le périmètre est le backlog : tout ce qui n'est pas `[x]` y est obligatoire. Contrats déjà persistés et à respecter : `docs/SCHEDULES.md` (SLS-078), `docs/SERVERLESS_JOBS.md` (SLS-081), `docs/SCALEWAY_PARITY.md` (SLS-082 à 088), `docs/REFERENCE_COMPATIBILITY.md` (SLS-080), `docs/OPERATIONS.md` (SLS-079), `docs/CONSOLE_USABILITY.md` (SLS-068 à 073). Ordre de travail, une unité à la fois : 1) SLS-078 moteur de planification (fenêtres de 5 minutes), avertissements de l'adaptateur et reconstruction/déploiement de la console pour que le manuel affiché soit `docs/manual.md` ; 2) SLS-070 éditeur, SLS-071 client HTTP, SLS-072 journaux ; 3) SLS-081 jobs de console : payload fixe, gabarits composés dans l'UI, expression crontab ; 4) SLS-083 limites et en-têtes alignés sur Scaleway, puis SLS-080 compatibilité du projet de référence par fixtures originales ; 5) SLS-068 favoris, SLS-069 renommage et suppression en masse, SLS-075 ; 6) SLS-073 monitoring et alertes ; 7) SLS-079 guide d'exploitation rejoué sur une installation temporaire ; 8) clôture de SLS-074 (régression complète 008), SLS-066, SLS-020 (écarts SSO), SLS-030, SLS-040, SLS-050, SLS-060 ; 9) SLS-084, 086, 087 : écrire le contrat, le persister, puis réaliser ; SLS-085 et SLS-088 exigent d'abord une décision (courtier de messages, origine des images) : pose la question au responsable et continue le reste.

Contraintes non négociables : SPARK DEV uniquement, jamais PREPROD/PROD ; John Dalia (`johndalia/`) est une référence en lecture seule, ses fixtures sont originales ; aucun mock, stub, faux serveur ni test ignoré, tout est prouvé E2E sur le code réellement déployé, un scénario à la fois ; les parcours UI partent de l'accueil, connectés par le vrai SSO, à la souris et au clavier, avec captures JPEG inspectées sur ordinateur et mobile après lecture des deux design systems ; l'autorisation est toujours prouvée côté serveur par requête directe ; noms descriptifs de la fonction réelle ; chaque décision et son motif sont persistés et commités AVANT le code qui en dépend ; la matrice `docs/SCALEWAY_PARITY.md`, le manuel (`docs/manual.md`, affiché par la console), le backlog, le CHANGELOG, le seed, le schéma et le contrat de déploiement évoluent dans le même commit que le code ; commits en français, au nom du responsable, sans co-signature, poussés après chaque chunk cohérent.

Tranche seul les choix réversibles. Sollicite le responsable uniquement pour : un accès ou un secret indispensable absent (identifiants de push, autorité sur le SPARK), un budget de cellule insuffisant (propose-le en `.?`, ne le modifie pas), une dépense, un choix de produit non déductible du dépôt. Poursuis alors les travaux indépendants.

Critère de clôture : toutes les unités sont `[x]` avec leur Definition of Done, chaque ligne de `docs/SCALEWAY_PARITY.md` est Livré, Sans objet ou Écart assumé prouvé, ou portée par une unité dont le blocage externe est nommé ; la campagne complète passe en série avec zéro échec et zéro test ignoré ; les preuves, sources et images correspondent au code déployé. Ne déclare jamais fini ce qui ne l'est pas, ne réduis aucune exigence pour obtenir du vert, et termine par le compte rendu factuel de `CLAUDE.md` §25.
```

## Ordre de travail et dépendances

| Étape | Unités | Pourquoi dans cet ordre |
| --- | --- | --- |
| 1 | SLS-078 | Moteur partagé par les crons du manifeste et les jobs ; lève l'écart bloquant de la référence et le silence de l'adaptateur ; redéploie le manuel qui dit déjà la limite |
| 2 | SLS-070, 071, 072 | Parcours éditer, publier, tester, diagnostiquer ; les journaux alimentent le client HTTP et les jobs |
| 3 | SLS-081 | Demande explicite du responsable ; repose sur 078 et profite des journaux |
| 4 | SLS-083, 080 | Les limites doivent être alignées avant de prouver la compatibilité de la référence |
| 5 | SLS-068, 069, 075 | Ergonomie demandée, indépendante du moteur |
| 6 | SLS-073 | Le monitoring consomme tirs, invocations et journaux déjà livrés |
| 7 | SLS-079 | Le guide est rejoué sur l'état stable le plus tardif possible |
| 8 | Clôtures 074, 066, 020, 030, 040, 050, 060 | Preuves résiduelles et régression complète sur le code final |
| 9 | SLS-084, 086, 087 ; 085, 088 sous décision | Reste de la parité Scaleway |

## Points d'autorité connus

- **Push** : l'agent qui a préparé ce plan n'a pas d'identifiants GitHub ; des
  commits locaux peuvent précéder `origin/main`.
- **Budget CPU de cellule** : la compatibilité complète de la référence demande au
  moins 1,5 CPU et 2 Gio de budget d'exécution. La valeur du SPARK DEV est à lire ;
  toute hausse est une proposition `.?`, pas une action de l'agent.
- **SLS-085** : aucun courtier de messages dans le SPARK DEV.
- **SLS-088** : origine des images de conteneur non déductible du dépôt.
- **Installation temporaire de SLS-079** : si l'autorité du SPARK ne l'autorise pas,
  nommer le blocage.
