# Compatibilité du projet de référence

Contrat de l'unité [SLS-080](BACKLOG.md#sls-080), qui complète l'exigence de
[SLS-030](BACKLOG.md#sls-030) : établir la compatibilité à partir des contrats du
projet de référence, avec des fixtures originales déployées et invoquées pour de
vrai. Le projet de référence (`johndalia/jd_serverless`, déployé sur Scaleway) est
en **lecture seule** : rien n'en est copié, modifié ni déployé, aucune valeur de
configuration ou de secret n'est reproduite ici.

## Périmètre et méthode

Audit du 10 novembre 2026 : lecture du manifeste d'exemple et du manifeste réel
(structure uniquement), des points d'entrée des handlers, de leurs dépendances
déclarées et de la bibliothèque commune ; exécution de `python3 -m adapter plan`
sur les deux manifestes (analyse seule, noms de variables et de secrets
uniquement, rien d'écrit ni d'envoyé). Les conclusions de cette page sont des
constats d'audit. Elles ne prouvent pas la compatibilité : la preuve est la
campagne E2E de [Preuves attendues](#preuves-attendues).

## Constats de structure

- 13 fonctions dans le manifeste ; 14 répertoires de handlers, `addScanHistory`
  n'ayant pas d'entrée de manifeste.
- Runtime déclaré `node20`. Handlers CommonJS : `module.exports.handle = async
  (event, context, cb)`. Entrée de manifeste `dist/<nom>/index.handle`.
- Chaque fonction est livrée **empaquetée par le build du projet** : 7 à 8 fichiers,
  4 à 5 Mio. Largement sous les limites de l'adaptateur (ZIP 64 Mio, 20 000 fichiers).
- Dépendances directes en JavaScript pur (ethers, pg, md5, bcryptjs, keccak256,
  nodemailer, axios, clients SQS, form-data) : aucun addon natif détecté. Les
  dépendances transitives ne sont pas auditées.
- Bibliothèque commune importée par chemin relatif ; le build la place dans chaque
  paquet.

## Matrice du manifeste

| Élément du manifeste de référence | Traitement de l'adaptateur | Adaptation ou réserve |
| --- | --- | --- |
| `service`, `functions`, `handler` | Pris en charge | Le build du projet précède l'adaptateur, qui n'exécute ni script ni plugin |
| `plugins`, `configValidationMode`, `provider.name: scaleway` | Acceptés avec avertissement « non exécuté » | — |
| `provider.runtime: node20` | Refusé sans `--runtime node24` ; conversion explicite avec avertissement | Validation réelle du paquet sous Node 24 par import dans Docker ; versions d'ethers et de pg à éprouver |
| `provider.secret` (2 secrets) et `provider.env` | Conservés dans le **service**, surcharges seules dans les fonctions ([SLS-031](BACKLOG.md#sls-031)) | — |
| `scwToken`, `scwProject`, `scwRegion` | Ignorés avec avertissement ; jamais transmis ni stockés | — |
| `package.patterns` (exclusions) | Pris en charge (sous-ensemble glob) | — |
| `memoryLimit` 128/256 Mio, `timeout` en chaîne `120s`/`300s`/`10s` | Pris en charge | — |
| `minScale` 0 à 2, `maxScale` 1 à 5 | Pris en charge | [Capacité](#capacité) |
| `httpOption`, `privacy: public`, `custom_domains` | Exigent `--accept-provider-differences` ; ignorés | HTTPS imposé ; jeton obligatoire ; adresses issues des domaines du SPARK |
| `events: schedule` (2 fonctions) | Acceptés et enregistrés | Moteur déployé, première preuve réelle dans [SLS-078](BACKLOG.md#sls-078) ; compatibilité des expressions de la référence encore à qualifier ; voir [Planifications](#planifications) |
| `events` HTTP absents | Endpoint implicite `/invoke/{id}` | Les clients passent d'un domaine par fonction à une adresse par UUID |

## Contrat des handlers

| Contrat observé | Plateforme | Réserve |
| --- | --- | --- |
| Événement HTTP v1 (`httpMethod`, `body`, `headers`), `context.getRemainingTimeInMillis`, réponse `{statusCode, headers, body}` | Fournis par la passerelle | Casse des en-têtes à prouver (`Authorization`) |
| `JSON.parse(event.body)` sur tout appel, y compris planifié | Le corps d'un tir est toujours une chaîne JSON valide (`{}` par défaut) | Cron : [SCHEDULES](SCHEDULES.md) |
| Branche `OPTIONS` et en-têtes CORS construits dans le handler depuis une variable d'origine | La passerelle gère le préflight sans invoquer le handler et **retire** les `Access-Control-*` applicatifs ([EXECUTION](EXECUTION.md#passerelle-et-politique-réseau)) | Reporter les origines dans la politique du service ; ajouter `X-Serverless-Token` aux en-têtes envoyés par le navigateur |
| Appels entre fonctions par `fetch` sur des URL configurées par variable | Possible par la passerelle | **Le code de référence n'envoie pas `X-Serverless-Token`** : adaptation du client, hors de ce dépôt (voir [Adaptations](#adaptations-côté-client)) |
| Accès sortant : HTTPS (`fetch`), PostgreSQL (`pg`), RPC de blockchain, SMTP, webhooks, files de messages | Réseau Docker `bridge` dédié par instance | **Sortie non spécifiée ni prouvée** ; preuve et frontière à établir |
| Fichiers fournis dans le paquet, lus à l'exécution | `/code` en lecture seule | — |
| Écritures temporaires | `/tmp` de 16 Mio, noexec | Voir [parité](SCALEWAY_PARITY.md#fonction--exécution-et-limites) |
| Variables : une vingtaine par fonction | 128 clés de 16 Kio par catégorie | Suffisant ; voir [SLS-083](BACKLOG.md#sls-083) |

## Capacité

Somme des 13 fonctions : **14 instances minimum, 31 maximum** ; mémoire 2 688 Mio
au minimum et 6 144 Mio au maximum. Le CPU dépend de la règle d'allocation :

| Règle | Minimum | Maximum |
| --- | --- | --- |
| Défaut actuel de l'adaptateur, 0,25 CPU par instance | 3,50 CPU | 7,75 CPU |
| Paliers Scaleway (70 mvCPU par 128 Mio, [parité](SCALEWAY_PARITY.md)) | 1,47 CPU | 3,36 CPU |

Le budget de cellule vaut **1 CPU par défaut dans le code**
(`SERVERLESS_FUNCTION_CPU_BUDGET`) ; la valeur du SPARK DEV n'est pas supposée.
Avec le défaut de l'adaptateur, la publication complète serait refusée en 409.
Décision du 10 novembre 2026 : quand `p2enjoy.cpu` n'est pas déclaré, l'adaptateur
dérive le CPU du palier mémoire Scaleway, qui reproduit la capacité que le client
connaît ; `p2enjoy.cpu` l'emporte. Motif : même comportement pour un manifeste
Scaleway, aucune configuration obligatoire, réversible. Tenir les minima exige un
budget de cellule d'au moins 1,5 CPU et 2 Gio ; les maxima, 3,4 CPU. Ce changement
de variable de cellule est une proposition `.?` au propriétaire du SPARK, pas une
action de l'agent. La campagne de compatibilité s'exécute seule : les autres
campagnes consomment les mêmes budgets.

## Planifications

Deux fonctions de la référence sont planifiées : une chaque jour de lundi à samedi
à 21 h 00 UTC (`0 21 * * 1-6`) et une chaque heure de 7 h à 20 h UTC, de lundi à
samedi (`0 7-20 * * 1-6`). Elles tombent sur des frontières de 5 minutes : la
résolution de [SCHEDULES](SCHEDULES.md) ne les décale pas. Leurs handlers lisent
un corps JSON ; le tir envoie `{}` en `POST`. Le moteur de [SLS-078](BACKLOG.md#sls-078) a son premier checkpoint réel.
Les deux expressions de la référence et leurs fixtures originales restent à
qualifier ; ce checkpoint ne démontre pas leur compatibilité complète.

## Adaptations côté client

Non appliquées ici (le dépôt de référence est en lecture seule), à fournir dans le
guide d'intégration : adresse de base et chemin `/invoke/{UUID}` ; jeton Read dans
`X-Serverless-Token` pour le navigateur (visible du navigateur : la restriction
d'origine et d'IP atténue, elle n'identifie pas le client) et pour chaque appel
entre fonctions ; cible de build Node 24 ; origines du service alignées sur la
variable d'origine du handler ; abandon de `privacy`, `httpOption` et
`custom_domains`.

## Preuves attendues

Campagne E2E sur le SPARK DEV, exécutée seule, avec des **fixtures originales** du
dépôt (rôle de chaque fonction, mêmes clés de manifeste, mêmes contrats) :

- un service à treize fonctions reproduisant les mémoires, délais, minima et
  maxima, `provider.secret`/`env`, les trois options ignorées, le runtime
  `node20` converti, deux planifications, des handlers `(event, context, cb)`
  qui font `JSON.parse(event.body)`, construisent leurs propres en-têtes CORS,
  gèrent `OPTIONS` et s'appellent entre elles avec le jeton ;
- publication complète par `adapter deploy` avec les deux drapeaux, rapport lu ;
  mise à jour, rollback, pilote, redéploiement ; budgets CPU/RAM/instances
  constatés avant et après, y compris le refus 409 d'un budget insuffisant ;
- invocation de chaque fonction par l'adresse copiée depuis la console, jeton
  Read, origine autorisée depuis un vrai navigateur (préflight, en-têtes
  demandés, réponse sans les `Access-Control-*` du handler), refus d'une autre
  origine ou IP, `Authorization` métier reçu par le handler ;
- accès sortant réel vers des dépendances **réelles** démarrées pour l'essai sur le
  SPARK DEV (serveur HTTP, PostgreSQL, serveur de courrier) puis purgées ;
  démonstration que l'instance n'atteint ni le contrôle, ni l'agent de stockage,
  ni le socket Docker ;
- planifications : tirs réels aux frontières attendues, corps `{}`, sur la version
  promue ([SCHEDULES](SCHEDULES.md#preuves-e2e-attendues)) ;
- exécution du `plan` sur les manifestes réels de référence (lecture seule) et
  comparaison de ses fonctions, limites et événements avec ceux des fixtures, afin
  que les fixtures restent fidèles ;
- captures des écrans de console concernés (service à treize fonctions, adresses,
  planifications, erreurs de publication), inspectées sur ordinateur et mobile.
