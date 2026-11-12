# Parité fonctionnelle avec Scaleway Serverless

Contrat de l'unité [SLS-082](BACKLOG.md#sls-082). Demande du responsable, 10 novembre
2026 : **répliquer toutes les fonctionnalités de Scaleway Serverless**, dont les
projets de référence sont aujourd'hui clients. Cette matrice est la liste de
travail ; chaque ligne a un état réel et, quand elle n'est pas livrée, une unité
du backlog. Une ligne « Sans objet » porte son motif.

## Source et méthode

Relevé du 10 novembre 2026 sur la documentation publiée par Scaleway
(`github.com/scaleway/docs-content`, branche `main`, pages `serverless-functions/`
et `serverless-jobs/` : concepts, limitations, runtimes, paliers mémoire/CPU,
en-têtes de requête, déclencheurs, sécurité, gestion, test, jobs). Le site
`scaleway.com` avait refusé ce relevé automatisé (HTTP403), d’où les sources
open source ; le complément ciblé du12novembre ci-dessous consulte directement
les pages publiées accessibles du testeur. Les valeurs de Scaleway peuvent évoluer ; la
matrice se revérifie à chaque revue de parité. Les états de la plateforme
viennent du code et des contrats du dépôt, pas de la mémoire de l'agent.

États : **Livré**, **Partiel** (la fonctionnalité existe, avec un écart nommé),
**À livrer** (unité ouverte), **Sans objet** (motif), **Écart assumé** (décision
déjà prise et documentée, avec motif).

## Correspondance de vocabulaire

| Scaleway | P2Enjoy Serverless |
| --- | --- |
| Namespace (fonctions, variables, secrets et jetons partagés) | **Service** (un `serverless.yml`). Le champ `service:` du manifeste est le nom du namespace Scaleway |
| Fonction | Fonction (UUID stable, révisions, versions par hash) |
| Variables/secrets de namespace surchargés par la fonction | Variables/secrets du service surchargés par la fonction ([SLS-031](BACKLOG.md#sls-031)) |
| Jeton de namespace / de fonction (`X-Auth-Token`) | Jeton du service, restreignable à des fonctions, en-tête `X-Serverless-Token` |
| Déclencheur CRON avec arguments JSON | **Job** ([SLS-081](BACKLOG.md#sls-081)) sur le moteur de [planification](SCHEDULES.md) |
| Serverless Jobs (lots en conteneur) | Hors périmètre actuel ([SLS-088](BACKLOG.md#sls-088)) |
| Namespace P2Enjoy | Regroupement supplémentaire au-dessus des services, sans équivalent Scaleway |

## Matrice

### Fonction : exécution et limites

| Fonctionnalité Scaleway | Limite ou valeur Scaleway | État de la plateforme | Unité ou décision |
| --- | --- | --- | --- |
| Runtimes | Node 22/24/26, Python 3.9 à 3.14, Go 1.25/1.26, PHP 8.4/8.5, Rust ; anciens runtimes « fin de support » | **Partiel** : Node 24 ; Node 20/22 par conversion explicite | [SLS-084](BACKLOG.md#sls-084) |
| Handler | Fonction ou méthode traitant un événement | **Livré** : `module.export`, signature `(event, context, callback)`, événement HTTP v1 | — |
| Mémoire et CPU | Paliers 128 Mo/70 mvCPU, 256/140, 512/280, 1024/560, 2048/1120, 3072/1680, 4096/2240 | **Livré**, surensemble : mémoire 128 à 8192 Mio et CPU 0,05 à 1 indépendants | Dérivation du CPU depuis le palier Scaleway quand `cpu` est absent : [SLS-080](BACKLOG.md#sls-080) |
| Échelle | min/max d'instances, max 50 ; réduction après 30 s ; extinction à zéro après 15 min | **Partiel** : min/max jusqu'à 32, `idle_seconds` configurable | Plafond 50 sous réserve du budget de cellule : [SLS-083](BACKLOG.md#sls-083) |
| Concurrence | 1 requête par instance | **Livré** : une invocation active par instance | — |
| Durée d'une requête | 10 s à 60 min | **Livré**, surensemble : 0,1 s à 24 h (`max_execution_seconds`) | — |
| Disque temporaire | 1 024 Mio par instance | **Partiel** : `/tmp` tmpfs de 16 Mio noexec ; volumes données/cache en plus | [SLS-083](BACKLOG.md#sls-083) |
| Corps de requête | 6 Mio | **Partiel** : 1 Mio entrant, 6 Mio en réponse | [SLS-083](BACKLOG.md#sls-083) |
| Variables d'environnement | 200 variables de 65 536 caractères (fonction + namespace) | **Partiel** : 128 clés de 16 384 octets par catégorie | [SLS-083](BACKLOG.md#sls-083) |
| Secrets | 200 secrets de 65 536 octets ; masqués après saisie ; surcharge fonction sur namespace | **Partiel** : masqués, chiffrés, surchargés ; 128 clés de 16 384 octets | [SLS-083](BACKLOG.md#sls-083) |
| Archive | ZIP 100 Mio, code 500 Mio | **Partiel** : ZIP 64 Mio, 256 Mio décompressés, 20 000 fichiers | [SLS-083](BACKLOG.md#sls-083) |
| En-têtes ajoutés | `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Real-IP` (écrasé par Scaleway), `X-Request-ID` | **Partiel** : `requestContext.identity.sourceIp` et `requestId` ; ces en-têtes ne sont pas injectés, `X-Request-ID` est même retiré | [SLS-083](BACKLOG.md#sls-083) |
| État de la fonction | Ready, Pending, Error | **Livré** : états de candidat, de révision et d'instance | — |
| Étape de build, Container Registry | Image construite au déploiement | **Sans objet** : l'archive est validée par un import réel dans le runtime Docker commun | — |
| Sandbox v1/v2 | Isolation de la fonction | **Sans objet** : conteneur Docker rootless, capabilities retirées, `no-new-privileges` | — |
| Réseaux privés | 1 par fonction | **Sans objet** : réseau Docker dédié par instance ; sortie vers Internet à prouver | Preuve de sortie : [SLS-080](BACKLOG.md#sls-080) |
| Facturation GB-s, vCPU-s | Mesure de consommation | **Sans objet** pour la facturation ; consommation affichée par [SLS-061](BACKLOG.md#sls-061) | — |

### Fonction : déploiement et versions

| Fonctionnalité Scaleway | État de la plateforme | Unité ou décision |
| --- | --- | --- |
| Déploiement par Serverless Framework | **Livré** : adaptateur lisant `serverless.yml` sans exécuter de plugin | [SLS-030](BACKLOG.md#sls-030), [SLS-080](BACKLOG.md#sls-080) |
| Éditeur de code en ligne et import ZIP | ZIP et première facette Éditeur **déployés** ;checkpoint57 et complément39 réels ; bornes/reprises et compléments UI **ouverts** | [SLS-070](BACKLOG.md#sls-070) |
| Mise à jour progressive sans interruption | **Livré** : promotion atomique, appels admis terminés, instance précédente drainée | [SLS-074](BACKLOG.md#sls-074) |
| Répartition du trafic entre versions | **Partiel** : appel épinglé par hash et pilote, sans pourcentage | [SLS-086](BACKLOG.md#sls-086) |
| Terraform / OpenTofu | **Sans objet** : l'API REST du contrôle suffit à l'automatisation | — |
| API complète et documentée | **Partiel** : routes dans [CONTROL](CONTROL.md) ; schéma OpenAPI non exposé | [SLS-082](BACKLOG.md#sls-082) |
| Test local (`serveHandler`) | **Sans objet** : handlers CommonJS standard | — |
| Migration vers conteneurs | **Sans objet** | — |

### Accès et sécurité

| Fonctionnalité Scaleway | État de la plateforme | Unité ou décision |
| --- | --- | --- |
| Fonction publique (accès anonyme) | **Écart assumé** : le jeton Read est toujours obligatoire ; l'origine et l'IP le complètent | [PLATFORM](PLATFORM.md#identité-et-autorisations), README ; le client transmet le jeton |
| Fonction privée par jeton `X-Auth-Token` | **Livré**, surensemble : droits CRUD, portée par fonction, expiration, révocation, renouvellement | [SLS-020](BACKLOG.md#sls-020) |
| IAM et conditions CEL (IP, plage horaire, user-agent) | **Partiel** : origines et IP/CIDR avec ET/OU ; ni horaire ni user-agent | [SLS-087](BACKLOG.md#sls-087) |
| JWT | **Sans objet** : obsolète chez Scaleway | — |
| HTTPS seul (`httpOption: redirected`) | **Livré** : HTTPS imposé par la route du SPARK ; l'option du manifeste est ignorée avec avertissement | [SLS-080](BACKLOG.md#sls-080) |
| Domaines personnalisés | **Écart assumé** : domaines du SPARK et adresses calculées `/invoke/{id}` ; pas de domaine par fonction | [SLS-066](BACKLOG.md#sls-066) |
| CORS | **Livré**, surensemble : produit par la passerelle depuis la politique du service ; les en-têtes CORS du handler sont retirés | [SLS-080](BACKLOG.md#sls-080) |

### Déclencheurs

| Fonctionnalité Scaleway | État de la plateforme | Unité ou décision |
| --- | --- | --- |
| CRON : UTC, au plus une fois par minute, arguments JSON envoyés en `POST` sur `/` | **Partiel, en qualification** : moteur de manifeste déployé, [grammaire numérique qualifiée](evidence/schedule-calendar-dev-2026-11-10.json), résolution de **5 minutes** voulue par le responsable ; arguments de jobs et noms de mois/jours à livrer | [SLS-078](BACKLOG.md#sls-078), [SLS-081](BACKLOG.md#sls-081), [SLS-098](BACKLOG.md#sls-098) |
| Queue (Scaleway Queues) : retry jusqu'à 3 fois si statut ≥ 300, 10 messages en vol | **À livrer** plus tard ; aucun service de messagerie dans le SPARK DEV | [SLS-085](BACKLOG.md#sls-085) |
| NATS : un appel par message du sujet | **À livrer** plus tard, même dépendance | [SLS-085](BACKLOG.md#sls-085) |

La [référence des crons](https://www.scaleway.com/en/docs/serverless-jobs/reference-content/cron-schedules/)
est revérifiée le10 novembre2026 avec le complément numérique : les exemples
nommés `WED`, `MON-FRI` et `DEC` maintiennent l'écart SLS-098 ouvert.

### Exploitation

| Fonctionnalité Scaleway | État de la plateforme | Unité ou décision |
| --- | --- | --- |
| Journaux (Cockpit, 30 000 par minute et par projet) | **Partiel** : journaux expurgés par invocation | [SLS-072](BACKLOG.md#sls-072) |
| Métriques | **Partiel** : relevés Docker ponctuels | [SLS-073](BACKLOG.md#sls-073) |
| Alertes | **À livrer** | [SLS-073](BACKLOG.md#sls-073) |
| Onglet Test (commande `curl` générée) | **Partiel** : client HTTP déployé ; UI/CORS/IP/annulation/saturation46, reprise42 et jetons32 qualifiés ; [source/hash32](evidence/function-http-client-source-access-dev-2026-11-12.json) qualifié ; chargement dédié et exception071.6 ouverts | [SLS-071](BACKLOG.md#sls-071) |

### Serverless Jobs

| Fonctionnalité Scaleway | État de la plateforme | Unité ou décision |
| --- | --- | --- |
| Déclencheur planifié avec nom, expression, arguments | **À livrer** pour les fonctions sous le nom de job de la console | [SLS-081](BACKLOG.md#sls-081) |
| Historique des exécutions : statuts `succeeded`, `failed`, `interrupted`, raisons (`timeout`, `memory_usage_exceeded`, `exited_with_error`, `quota_exceeded`…) | **À livrer** : l'historique des tirs reprend ce vocabulaire | [SLS-081](BACKLOG.md#sls-081) |
| Lancement manuel et arrêt d'une exécution | **À livrer** : « Exécuter maintenant » | [SLS-081](BACKLOG.md#sls-081) |
| Lots en conteneur jusqu'à 24 h, image, commande, relances jusqu'à 5, stockage éphémère, secrets externes, fuseau | **À livrer** plus tard : exige un registre d'images et un runtime conteneur | [SLS-088](BACKLOG.md#sls-088) |

## Écarts de précision voulus par le responsable

La résolution des planifications est de 5 minutes là où Scaleway évalue chaque
minute : un tir peut partir avec jusqu'à 5 minutes de retard, jamais en avance.
Le manuel et l'interface le disent. Toute autre divergence de cette matrice est un
écart à résorber par son unité, pas une décision.

## Revue de parité

Cette matrice est mise à jour avec chaque unité qu'elle cite. Sa clôture exige
que toute ligne soit **Livré**, **Sans objet** ou **Écart assumé** avec preuve
E2E sur le SPARK DEV, ou qu'une ligne restante soit portée par une unité ouverte
dont le blocage externe est nommé.

Revue ciblée du 10 novembre 2026 (SLS-078) : [déclencheurs de fonctions](https://www.scaleway.com/en/docs/serverless-functions/how-to/add-trigger-to-a-function/)
et [référence des crons](https://www.scaleway.com/en/docs/serverless-jobs/reference-content/cron-schedules/)
consultées à nouveau. UTC et POST sur `/` confirmés ; l'écart des noms de
mois/jours devient SLS-098. Cette revue ciblée ne renouvelle pas la preuve des
autres lignes de la matrice.

## Relecture ciblée du testeur —12novembre2026

La page officielle [How to test a function](https://www.scaleway.com/en/docs/serverless-functions/how-to/test-a-function/)
décrit méthode, chemin, en-têtes/paramètres et copie de commande, avec jeton pour
une fonction privée. Le [quickstart](https://www.scaleway.com/en/docs/serverless-functions/quickstart/)
présente aussi un bouton Run et une section Output : ces deux parcours publiés
restent cités séparément. La ligne Test reste Partiel tant que071.2/.6 et la
clôture ne sont pas prouvés ; les autres lignes ne sont pas déclarées revérifiées
par cette consultation ciblée.
