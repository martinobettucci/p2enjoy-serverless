# P2Enjoy Serverless

Plateforme de fonctions conteneurisées, destinée à être déployée dans un SPARK
de FORGE. La console et le plan de contrôle sont en cours de qualification
dans **[control/](control/README.md)** et **[web/](web/README.md)**. Une première
application indépendante de qualification et son exécuteur de référence DEV
sont disponibles dans **[qualification/](qualification/README.md)**, avec
handlers, manifeste `serverless.yml`, Docker, tests et commandes d'exploitation.
L'[adaptateur](adapter/README.md) prépare les plans et archives ZIP ; la
validation Node dans Docker est disponible dans [runtime/](runtime/README.md),
avec 36 scénarios réels réussis. La publication des révisions et le moteur
d'invocation restent à implémenter. Le composant de [stockage à quota](storage/README.md)
est disponible et qualifié sur le SPARK DEV : 31 contrôles réels réussis,
dont saturation, concurrence et reprise après interruption.

## Objectif

Exploiter et déployer les projets P2Enjoy avec une compatibilité Lambda ciblée,
sans rechercher une reproduction complète des API AWS. Docker constitue le
socle d'exécution. Une interface permettra de gérer namespaces, fonctions,
allocations, mémoire, stockage permanent par identifiant de fonction et durées
du cycle d'exécution.

Le stockage propose des modes configurables par fonction pour les données
métier et le cache reconstructible. Le [contrat de plateforme](docs/PLATFORM.md)
définit concurrence, rétention, quotas et suppression ; son implémentation suit
les unités du [backlog](docs/BACKLOG.md).

Le premier projet de référence est `johndalia/jd_serverless`, actuellement
déployé sur Scaleway. La décision confirmée est de conserver ses handlers et
de réutiliser `serverless.yml` avec un adaptateur P2Enjoy.

## Accès confirmé

- La console d'administration utilise le SSO du domaine avec le rôle `admin`.
- Les administrateurs créent des jetons propres à la plateforme, limités à un
  service, avec des droits CRUD.
- `Create` et `Update` permettent la création ou modification des fonctions,
  du code, des variables, des secrets et des configurations, suivant le droit.
- `Delete` supprime une fonction en archivant ses données persistantes ; la
  purge des archives constitue une opération administrateur distincte.
- `Read` autorise l'invocation. Une invocation peut avoir des effets métier en
  écriture ; ce droit ne signifie pas que le handler est sans effet de bord.
- L'authentification métier reste indépendante et peut être implémentée dans
  chaque fonction. John Dalia devra transmettre le jeton de la plateforme en
  plus de son authentification existante.
- Chaque service doit permettre de limiter les appels aux fonctions à des
  origines web autorisées (par exemple `https://app.johndalia.com`) et/ou à
  des adresses IP autorisées, en complément du jeton. L'origine web n'est pas
  une preuve d'identité pour les clients hors navigateur. Le détail proposé
  de la combinaison des règles est consigné dans le journal.

Le contrat d'intégration fourni est [docs/sso.md](docs/sso.md).
Les décisions, preuves de lecture et questions sont dans
[docs/JOURNAL.md](docs/JOURNAL.md).

## Méthode

Référence : [P2Enjoy Software Factory Base](https://github.com/P2Enjoy/software-factory-base).
Le module de formation, ses supports et ses exports de séminaire sont exclus.
Le socle est importé ici : `CLAUDE.md`, `AGENTS.md`, rôles `.codex/` et
`.claude/`, `.githooks/`, `scripts/git-hooks/`, `tests/git-hooks/`, contrats
d'automatisation, de design et de worker. Provenance et adaptations :
[docs/METHODE.md](docs/METHODE.md). Le worker planifié est inactif.
Validation de l'outillage : `bash tests/git-hooks/test-hooks` utilise de vrais
dépôts temporaires et un remote Git local, sans réseau ni mock.

## Exécution et validation

La console DEV est accessible sur [serverless-dev.lelabs.tech](https://serverless-dev.lelabs.tech).
Son accueil et l'entrée vers le vrai SSO sont déployés ; la qualification
administrateur des objets, droits et cycles de session reste en cours.
Les commandes du contrôle figurent dans [control/README.md](control/README.md).
Les clients de preuve de plateforme vivent dans [e2e/](e2e/README.md).
Le [checkpoint DEV](docs/evidence/control-dev-checkpoint-2026-11-06.json)
conserve les sources déployées, les campagnes terminées et les parcours
administrateur encore à qualifier. Le [manuel](docs/manual.md) décrit la console.

**Il est interdit de lancer l'application avec un profil PREPROD ou PROD,
quelles que soient les circonstances.**

Prérequis pour le banc : Docker Engine avec Compose et Bash. Aucun runtime
Node ni service externe requis sur l'hôte. Depuis ce dépôt, exécuter chaque
commande après la fin de la précédente :

```sh
cd qualification
bash dev.sh build
bash dev.sh up
bash dev.sh check
bash dev.sh test
bash dev.sh probe
bash dev.sh recreate-proof
bash dev.sh status
```

Arrêt : `bash dev.sh stop`. Les volumes sont conservés. Les tests utilisent des
ressources nommées créées puis supprimées par leurs vraies API. **Aucun mock :
toute fonctionnalité testée est vérifiée E2E contre le code réellement déployé.**
Un conteneur client distinct appelle la pile en fonctionnement. Les pannes
de configuration, de stockage et de processus sont exercées dans de vrais
conteneurs isolés de la même image. Un prérequis absent fait échouer la
qualification ; aucun test n'est ignoré.
Sur le SPARK autorisé, chaque commande prend `--spark` avant l'action et lit
les deux fichiers de configuration de la cellule. Aucun `.env` n'est utilisé.

Le code source est **ici dans `qualification/`**, puis copié pour exécution dans
`/srv/p2enjoy-serverless/qualification` du seul SPARK DEV autorisé. Voir
[le guide de qualification](qualification/README.md) et
[le déploiement DEV](docs/QUALIFICATION_DEV.md). L'accès HTTP est local au SPARK,
sans route publique. La FORGE sert uniquement de rebond SSH ; aucune opération
d'administration n'y est autorisée.

## Structure

```text
adapter/
  manifest.py             Lecture sûre du manifeste et correspondances
  archive.py              Packaging ZIP et inventaire SHA256
  dev.sh                  Construction et qualification CLI dans le SPARK
control/
  app/                    API, SSO, sessions, objets et droits
  migrations/             Schéma SQLite versionné
  compose.spark.yml       Contrôle DEV sur le port 18090
web/
  src/                    Console React, formulaires et navigation
e2e/
  public.py               HTTPS public et refus OIDC réels
  login-ui.mjs            Accueil, clavier, responsive et SSO
  control-admin.mjs        Campagne API authentifiée
  control-ui.mjs           Parcours de gestion dans le navigateur
storage/
  main.go                 Proxy de quota FUSE sur les fichiers natifs
  client.py               Client de preuve dans un conteneur Docker isolé
  prove.py                Campagne de montage, quota, crash et reprise
runtime/
  loader.mjs              Chargeur commun Node : CommonJS et ESM
  validate-supervisor.mjs Supervision d'import et protocole Unix privé
  dev.sh                  Construction et qualification sur le SPARK
qualification/
  serverless.yml          Manifeste du service synthétique
  serverless.platform.yml Manifeste de packaging pour la plateforme
  src/handlers.cjs         Les douze fonctions originales
  runner/                 Exécuteur de référence, sans SSO ni ACL plateforme
  tests/                  Client E2E HTTP et preuve de recréation Docker
  compose.dev.yml          Pile DEV, ports uniquement sur boucle locale
  compose.spark.yml        Injection des deux fichiers de cellule
  dev.sh                  Commandes reproductibles
docs/
  DAT.md                  Architecture et limites des preuves
  BACKLOG.md              Unités de travail
  JOURNAL.md              Décisions et constats
  dev-spark.md             Dossier du SPARK fourni par le responsable
  sso.md                   Contrat d'intégration SSO
```
