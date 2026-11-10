# Objectif autonome

Le goal ci-dessous est **permanent** : il ne nomme aucune unité, aucun ordre ni
aucune échéance. Ce qui reste à faire, dans quel ordre et avec quels critères est
lu dans [le backlog](BACKLOG.md#registre-des-unités-ouvertes) au moment de la
session. Quand le backlog change, le goal n'a pas à changer.

## Texte du goal à transmettre à l'agent

```
/goal **Livrer P2Enjoy Serverless tel que le définissent le backlog et la documentation du dépôt, jusqu'à ce que toutes les unités du backlog soient `[x]`.**

Première action : lis INTÉGRALEMENT `CLAUDE.md`, `CLAUDE_PROJECT.md`, `AGENTS.md`, `README.md`, `docs/BACKLOG.md` et `docs/CloudWorker.md` (appliqué avec les adaptations de `CLAUDE_PROJECT.md#adaptation-de-cloudworker`), puis les documents de `docs/` qui portent le contrat de l'unité que tu choisis. Vérifie `git status` et `git log` ; si des commits locaux attendent d'être poussés, pousse-les d'abord.

Le backlog est la seule source de ce qu'il y a à développer, corriger ou qualifier. Prends dans son registre des unités ouvertes l'unité de plus petit ordre qui n'est ni `[x]` ni bloquée, lis son contrat, livre-la avec ses critères d'acceptation, ses tests propres et les critères communs du backlog, puis passe à la suivante. Une demande, un défaut, un écart de parité ou un reste de qualification que tu découvres devient une unité du backlog avant d'être traité. Ne déclare terminé que ce qui est prouvé sur le code réellement déployé ; une unité dont une preuve manque reste `[~]`.

Tranche seul tout choix réversible et persiste la décision avec son motif avant le code qui en dépend. Sollicite le responsable uniquement dans les cas d'arbitrage de `CLAUDE.md`, en nommant le cas et ce qui reste livrable, puis poursuis les unités indépendantes.

Termine quand le registre ne contient plus d'unité ouverte et que la campagne complète de clôture passe, ou, à défaut, avec le compte rendu factuel de `CLAUDE.md` qui nomme chaque unité restante et son blocage.
```

## Pourquoi un goal sans liste

- L'ordre et les statuts vivent à un seul endroit, le registre du backlog ; les
  recopier ici les ferait diverger.
- Les contraintes d'environnement (SPARK DEV uniquement, référence en lecture
  seule, aucun mock ni test ignoré, parcours UI depuis l'accueil, push après
  chaque commit) sont dans `CLAUDE.md` et `CLAUDE_PROJECT.md`, que le goal fait
  lire en premier.
- Les décisions et autorités en attente (courtier de messages, budget de cellule,
  comptes SSO de test, identifiants de push) sont dans la section
  [Décisions et autorités en attente](BACKLOG.md#décisions-et-autorités-en-attente)
  du backlog.
