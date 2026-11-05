# Automatisation de la méthode d'ingénierie

Ce document définit les garde-fous exécutables et l'orchestration des
sous-agents qui complètent `CLAUDE.md` et `docs/CloudWorker.md`.

Les documents conservent les règles qui demandent du jugement. Les scripts et
les hooks appliquent uniquement les invariants déterministes. Un contrôle local
ne remplace jamais une preuve fonctionnelle ni un contrôle distant de CI.

## 1. Propriété du travail

Une session traite une seule unité cohérente. L'agent principal est l'unique
éditeur des fichiers suivis, le seul autorisé à modifier l'état Git et le responsable des
décisions, de la documentation et de la Definition of Done.

Un sous-agent reçoit une mission indépendante et bornée d'exploration,
d'analyse, de revue, de vérification ou d'instruction d'une entrée du registre
d'incohérences. Il restitue des constats sourcés et ses
incertitudes. Il ne décide pas, ne clôture pas une unité et n'exécute aucune
opération Git modificatrice. Les consultations Git en lecture seule sont permises.

<a id="hook-installation"></a>

## 2. Activation des hooks

Les hooks sont versionnés sous `.githooks/`. Git ne les active pas lors d'un
clone ; leur installation est donc explicite et idempotente :

```bash
scripts/git-hooks/install
```

Le worker planifié active en plus les contraintes propres à son checkout
éphémère et à la branche `main` :

```bash
scripts/git-hooks/install --worker
```

L'installation configure `core.hooksPath`, `factory.hooks.mode` et, lors de sa
première exécution, le commit courant comme baseline locale. Cette baseline
évite de rejuger tout l'historique antérieur lors du premier push vers une
nouvelle destination ; chaque commit créé après l'activation reste contrôlé.
L'installation ne modifie jamais l'identité Git.
Elle refuse de remplacer un autre `core.hooksPath` déjà configuré : intégrer
explicitement les hooks existants avant de choisir le chemin du socle.

<a id="local-guards"></a>

## 3. Contrôles locaux

<a id="pre-commit-hook"></a>

### 3.1 `pre-commit`

Le hook :

- exécute `git diff --cached --check` ;
- exige `user.name` et `user.email` dans la configuration locale du dépôt, puis
  vérifie que les identités effectives de l'auteur et du committer valent
  exactement cette identité locale ; le socle n'épingle aucune valeur, il impose
  que celle du responsable soit déclarée dans le dépôt et jamais surchargée ;
- examine les blobs indexés, jamais une version non indexée du fichier ;
- exige un marqueur `@spec` dans les fichiers de code reconnus ;
- exige aussi `@verifies` dans les fichiers de test reconnus ;
- refuse les fichiers `.env` non modèles, les clés privées et quelques formats
  de secrets à forte confiance ;
- impose `main` lorsque `factory.hooks.mode=worker`.

Quand `docs/BACKLOG.md` existe, le marqueur de portée utilise une référence
parseable vers une unité stable :

```text
@spec docs/BACKLOG.md#identifiant | docs/DAT.md#section
@verifies docs/BACKLOG.md#identifiant | docs/DAT.md#section
```

Dans un dépôt de socle sans backlog produit, le marqueur cite directement le
contrat normatif stable, par exemple :

```text
@spec docs/AUTOMATION.md#pre-commit-hook
```

Le contrat cité n'est pas restreint au dossier `docs/` : tout document Markdown
versionné du dépôt convient, dès lors qu'il est stable et porte une ancre.

Lors de l'adoption dans un dépôt applicatif, rattacher également les scripts
importés à l'unité de backlog qui introduit l'outillage. Le contrôle ne valide
que la forme du marqueur dans les 60 premières lignes, pas l'existence ni la
pertinence de l'ancre.

La détection intégrée de secrets constitue un filet minimal. Un scanner dédié
maintenu reste nécessaire dans la CI des projets qui manipulent des secrets.

<a id="commit-message-hook"></a>

### 3.2 `commit-msg`

Le hook refuse les trailers de co-auteur et les signatures indiquant une
génération par un assistant. Il ne prétend pas reconnaître automatiquement la
langue française, qui reste une règle soumise au jugement.

<a id="pre-push-hook"></a>

### 3.3 `pre-push`

Le hook contrôle l'identité et les messages des seuls commits sortants ; un
commit sortant doit porter, en auteur comme en committer, l'identité locale du
dépôt. En mode
worker, il refuse :

- un remote différent de `origin` ;
- une source ou une destination différente de `refs/heads/main` ;
- un tag ou une suppression ;
- une mise à jour non fast-forward.

Il ne lance aucune campagne de tests longue et ne modifie jamais le dépôt ou le
remote.

<a id="session-guard"></a>

## 4. Garde de fin de session

La fin d'une session n'est pas un événement Git ; elle reste donc une commande
explicite :

```bash
scripts/git-hooks/check-session
```

Après le `git fetch origin main` prescrit par le worker, cette commande exige :

- les hooks activés avec `factory.hooks.mode=worker` ;
- `HEAD` attaché à `main` ;
- aucune opération Git inachevée ;
- aucun changement suivi ou non suivi ;
- `HEAD` strictement égal à `origin/main`, sans avance, retard ni divergence ;
- aucune sauvegarde temporaire `sauvegarde-etat-initial-worker` oubliée.

Cette commande est en lecture seule. Elle échoue avec une explication et laisse
à l'agent principal la correction de l'état.

## 5. Extension et CI

Un projet peut fournir un exécutable `scripts/project-pre-commit` pour ses
contrôles rapides propres à la pile. Le socle l'exécute après ses contrôles
génériques. Ce point d'extension ne lance ni campagne E2E ni opération réseau.

Les hooks peuvent être contournés localement avec `--no-verify`. Ce socle ne
fournit pas de workflow CI distant. Chaque projet doit configurer ses contrôles
de référence et ses protections de branche dans sa CI. Les scripts sont
réutilisables en respectant leurs entrées : index préparé pour `check-staged`,
fichier de message pour `check-message`, références et objets Git disponibles
pour `check-push`. Un checkout CI à index vide ne vérifie pas le code avec
`check-staged`. Les commandes de lint, de build et de tests restent celles
documentées par chaque projet ; le socle ne les devine pas.

<a id="subagents"></a>

## 6. Sous-agents

Les mêmes quatre rôles sont définis, avec le même contrat, pour les deux
outillages :

- Codex lit `AGENTS.md` puis les définitions de `.codex/agents/*.toml` ;
  `.codex/config.toml` borne leur concurrence ;
- Claude Code lit `CLAUDE.md` nativement et découvre les définitions de
  `.claude/agents/*.md` : le frontmatter restreint les outils du rôle et le
  corps du fichier est son prompt. Ces définitions nomment les rôles avec des
  tirets, `factory-explorer` pour `factory_explorer`.

Les rôles :

- `factory_explorer` cartographie le dépôt en lecture seule ;
- `factory_reviewer` relit un changement stabilisé en lecture seule ;
- `factory_verifier` exécute ou analyse une preuve ciblée sans modifier les
  sources, la documentation ou Git ;
- `factory_resolver` instruit en lecture seule une entrée du registre
  d'incohérences pour la boucle de résolution de `CLAUDE.md` §5 : il relit le
  constat, cherche les précédents du produit et de ses contrats, puis propose
  une issue avec son critère décisif, ses sources et sa preuve minimale ;
  l'agent principal vérifie, décide, applique et retire l'entrée.

Les sous-agents sont un accélérateur facultatif. Leur indisponibilité ne bloque
jamais une session. Ils ne sont utilisés que lorsque le travail peut être
réellement isolé et que le gain compense leur coût de coordination.

Le vérificateur dispose d'un accès d'écriture au workspace uniquement parce que
les outils de test peuvent produire des caches, builds, captures ou rapports.
Il relève `git status --short` avant et après la commande, ne nettoie rien et
signale toute modification suivie ou tout artefact inattendu.

## 7. Limites des garde-fous

Les scripts vérifient une forme, jamais le sens. Ils ne peuvent pas établir :

- la pertinence d'une référence de spécification ;
- la cohérence fonctionnelle d'un commit ;
- la qualité d'une décision ;
- l'observation réelle d'une capture ;
- le respect mental de l'ordre de travail.

Ces responsabilités restent portées par l'agent principal, la revue et les
preuves décrites dans `CLAUDE.md`.
