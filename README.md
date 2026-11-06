# P2Enjoy Serverless

Plateforme de fonctions conteneurisées, destinée à être déployée dans un SPARK
de FORGE. La console et le plan de contrôle sont en cours de qualification
dans **[control/](control/README.md)** et **[web/](web/README.md)**. Une première
application indépendante de qualification et son exécuteur de référence DEV
sont disponibles dans **[qualification/](qualification/README.md)**, avec
handlers, manifeste `serverless.yml`, Docker, tests et commandes d'exploitation.
L'[adaptateur](adapter/README.md) prépare les plans, archives ZIP et publications
HTTPS via sa commande `deploy`, dont les sept groupes authentifiés passent. La
validation Node dans Docker est disponible dans [runtime/](runtime/README.md),
avec 36 scénarios réels réussis. Les routes de publication, d'historique et de
rollback sont déployées en DEV ; onze groupes authentifiés passent :
[preuve de publication](docs/evidence/deployment-authenticated-dev-2026-11-06.json).
Les plafonds de candidats/révisions et les reprises après SIGKILL pendant
réception/validation passent quatre groupes supplémentaires :
[preuve de reprise](docs/evidence/publication-recovery-dev-2026-11-06.json).
Expiration, budget et interruption pendant nettoyage restent à éprouver.
Le pilote Docker d’instances chaudes passe 31 contrôles d’invocation et
11 de cycle de vie : [preuve DEV](docs/evidence/instances-dev-2026-11-06.json).
Le raccordement des instances aux baux de volumes passe quatorze groupes réels :
[preuve](docs/evidence/managed-storage-dev-2026-11-06.json). La passerelle et les admissions sont déployées sur DEV ; les 31 groupes HTTPS
et 221 groupes de régression passent dans la [preuve du moteur](docs/evidence/execution-dev-2026-11-06.json). Les préparations de quotas et leurs décisions
durables ont fait l’objet d’une première campagne de dix groupes réels,
avec 37 groupes de régression :
[preuve](docs/evidence/storage-preparations-dev-2026-11-06.json). Les créations, changements de quotas, suppressions et publications sont
raccordés à une décision durable du contrôle : [contrat](docs/ADMISSION.md),
[preuve des mutations publiques](docs/evidence/function-storage-dev-2026-11-06.json). L'extracteur ZIP serveur dans
[control/](control/README.md) passe 112 contrôles réels, dont les limites,
les erreurs de disque et les douze archives chargées ensuite par Node.
Le composant de [stockage à quota](storage/README.md)
est disponible et qualifié sur le SPARK DEV : 31 contrôles réels réussis,
dont saturation, concurrence et reprise après interruption. Son agent local
de volumes est installé en DEV ; les baux, budgets et reprises font l’objet
de campagnes réelles de composant. Leur raccordement aux admissions publiques
est désormais déployé et éprouvé par la campagne publique.

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

Les noms décrivent obligatoirement la fonction réelle et l’usage de chaque
élément. La [règle de nommage](CLAUDE_PROJECT.md#nommage-obligatoire) s’applique
au code, aux ressources déployées et aux libellés de la console.

Référence : [P2Enjoy Software Factory Base](https://github.com/P2Enjoy/software-factory-base).
Le module de formation, ses supports et ses exports de séminaire sont exclus.
Le socle est importé ici : `CLAUDE.md`, `AGENTS.md`, rôles `.codex/` et
`.claude/`, `.githooks/`, `scripts/git-hooks/`, `tests/git-hooks/`, contrats
d'automatisation, de design et de worker. Provenance et adaptations :
[docs/METHODE.md](docs/METHODE.md). Le worker planifié est inactif.
Validation de l'outillage : `bash tests/git-hooks/test-hooks` utilise de vrais
dépôts temporaires et un remote Git local, sans réseau ni mock.

## Exécution et validation

La console DEV est accessible sur [serverless.lelabs.tech](https://serverless.lelabs.tech).
Le conteneur `serverless-api` sert cette console et l’API. Le conteneur
`serverless-runtime-reference` exécute les handlers de qualification sur la
boucle locale ; ses clients de test sont éphémères. Les
[noms d’exploitation](docs/DEPLOYMENT_NAMES.md) précisent leurs rôles.
La gestion authentifiée passe 19 groupes API et 11 parcours de console,
avec persistance après redémarrage, droits CRUD, secrets et rendu mobile.
Les cycles de rôles, de renouvellement et de clés SSO restent à qualifier.
Les commandes du contrôle figurent dans [control/README.md](control/README.md).
Les clients de preuve de plateforme vivent dans [e2e/](e2e/README.md).
La [preuve de gestion](docs/evidence/control-management-dev-2026-11-06.json)
recoupe les sources déployées, les campagnes, les ressources web servies et
les sept captures relues. Le [manuel](docs/manual.md) décrit la console.

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
  deploy.py               Publication HTTPS en série et résultats partiels
  dev.sh                  Construction et qualification CLI dans le SPARK
control/
  app/                    API, SSO, sessions, objets et droits
  app/artifacts.py         Extraction ZIP bornée et publication readonly
  app/deployments.py       Candidats, validation Docker et publication SQLite
  app/execution.py         Admission, réservations, instances et reprise
  app/invocation_routes.py Passerelle HTTP et observations autorisées
  artifacts-dev.sh         Construction et qualification de l'extracteur
  migrations/             Schéma SQLite versionné
  compose.spark.yml       Contrôle DEV sur le port 18090
web/
  src/                    Console React, formulaires et navigation
e2e/
  artifacts.py            Preuves ZIP, disque, courses et parcours des 12 fonctions
  public.py               HTTPS public et refus OIDC réels
  login-ui.mjs            Accueil, clavier, responsive et SSO
  control-admin.mjs        Campagne API authentifiée
  control-ui.mjs           Parcours de gestion dans le navigateur
  deployments.mjs          Publication et courses par les véritables API
  adapter-deploy.mjs       Parcours de la commande deploy avec jetons réels
storage/
  agent.py                Service local, baux et registre durable des volumes
  install-dev.py          Installation du paquet protégé et maintenance
  agent-proof.py          Campagnes réelles de cycle de vie et de limites
  main.go                 Proxy de quota FUSE sur les fichiers natifs
  client.py               Client de preuve dans un conteneur Docker isolé
  prove.py                Campagne de montage, quota, crash et reprise
runtime/
  loader.mjs              Chargeur commun Node : CommonJS et ESM
  invoke-supervisor.mjs   Instances chaudes avec enfant neuf par invocation
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
