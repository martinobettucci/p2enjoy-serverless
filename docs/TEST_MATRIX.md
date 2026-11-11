# Matrice de qualification réelle

## Application témoin QLF-001

Chaque ligne doit être exercée contre le vrai service. `tests/e2e.test.cjs`
désigne le client HTTP dans un conteneur séparé ; `tests/operations.py` pilote
Docker et HTTP sur le SPARK DEV. Aucun test ignoré n'est accepté.

| Contrat livré | Preuve E2E |
| --- | --- |
| Catalogue, douze handlers, IDs, mémoire déclarée, stockage | Catalogue complet comparé au contrat |
| Événement HTTP, query répétée/vide/Unicode, corps, contexte | Appels echo depuis le réseau Docker réel |
| Entrée et sortie binaires, HEAD sans corps | Octets exacts, en-têtes et statut |
| Callback, Promise, retour synchrone, callback tardif et erreur | Modes du vrai handler callback ; première réponse gagnante |
| Auth métier configurée, absente, invalide, même longueur | Vrais secrets de cellule ; conteneur sans déclaration d'environnement |
| Configuration et allowlist des secrets | Valeur publique réelle, présence bornée, absence chez echo, logs |
| Compteur CRUD, validation, deux écritures, clés séparées | API réelle et observation des valeurs persistées |
| Cache hit, invalidation, indépendance, reconstruction | API réelle et changement de génération |
| Worker, bornes d'entrées, conflit, checkpoints et tous résultats | Calcul PBKDF2 réel ; 1, 64 et 128 entrées ; reprise HTTP |
| Worker, compteur et cache après recréation | probe avant/après, observations dans volume client uniquement |
| Erreur synchrone, rejet, exit, réponse invalide | Vrais handlers ; invocation suivante saine |
| Deadline sur sommeil et boucle CPU | Exécution réelle, SIGKILL du processus, reaping vérifié |
| Relais nominal, payload, erreurs 500/504/429 | Appels aux vrais pairs, aucune doublure réseau |
| Saturation d'admission et retour au service | Seize vraies requêtes incomplètes ; dix-septième refusée |
| Délai après passage en file, déconnexion client | Charge d'un seul scénario, santé observée, aucun délai arbitraire |
| Routes, méthodes, taille exacte et flux fragmenté | 404/405/413 exacts ; 262144 octets acceptés, 262145 refusés |
| Arrêt actif et en file, redémarrage | SIGTERM réel du conteneur puis HTTP sain |
| Logs, confidentialité et fin des enfants | Docker logs/top réels corrélés aux réponses |
| Confinement Docker et écoute locale | Cgroups réels, écriture EROFS et connexions réseau effectives |
| Refus de manifestes invalides | Démarrages de la même image avec vraies configurations erronées |
| Stockage corrompu, illisible, non inscriptible, compteur maximal | Fichiers réels d'un volume isolé, résultat observé par HTTP |
| Épuisement des processus | Vrai plafond cgroup abaissé dans le seul conteneur isolé, puis restauré |

La matrice qualifie les comportements de l'application témoin et de son
exécuteur de référence. Elle ne mesure pas une couverture de lignes et ne
prouve pas les fonctionnalités propres à la plateforme : SSO, ACL CRUD, UI,
adaptateur de déploiement, règles origine/IP, quotas individuels, instances
chaudes et extinction automatique. Ces fonctionnalités ont leurs campagnes
distinctes, preuves datées et limites suivies au backlog.

## Méthode SLS-000

`tests/git-hooks/test-hooks` exerce les vrais scripts, index Git, commits,
hooks installés, pushes vers un dépôt bare local et garde de fin de session.
Les dépôts sont temporaires ; aucun dépôt client ni remote public n'est modifié.
La présence et l'activation locale des hooks sont vérifiées séparément.

Les résultats datés et les empreintes sont dans `docs/evidence/` ; les résultats
des campagnes antérieures restent historiques et ne qualifient pas un code
modifié depuis leur exécution.

### Instances et baux de stockage — SLS-040/050

Le client `e2e/managed-storage.py` vérifie quatorze groupes réels dans l'image
active du contrôle : acquisition/binds, persistance chaud/froid, quotas data
et cache, partage/isolation/refus de mutation, invocation concurrente et double
démarrage, échec Docker, deadline, annulation pendant acquire, annulation
pendant check, SIGKILL FUSE, arrêt/reprise agent avec nettoyage différé,
volumes désactivés, pagination de 51 baux, diagnostic CLI/EOF. Les ressources appartiennent à une
installation de preuve distincte ; le contrôle conserve son ID durant les pannes.
La simultanéité exacte du résultat métier et de l'échec du watcher est couverte
par revue structurelle ; aucune synchronisation factice n'est présentée comme
une reproduction E2E de cette course.

`e2e/storage-installation.py` vérifie la garde de racine avec agent réellement
arrêté, refus avant création, restauration via propositions de cellule et
identité de registre conservée. Les démarrages invalides associés au nouveau
canal sont vérifiés par les conteneurs isolés de `control-operations.py`.

### Décisions de quotas — SLS-040/050

`e2e/storage-preparations.py` exerce les vrais RPC, montages et écritures Docker.
La réservation de l'ancien quota reste comptée lors d'une baisse, y compris
avec le budget global saturé. Les refus portent sur les mutations concurrentes,
le propriétaire, les baux actifs, la version et la taille réellement occupée.
Commit/abort sont rejoués et une décision opposée est refusée. Le scénario
SIGKILL vérifie preparing après SIGSTOP avant de tuer l'agent ; une préparation
déjà achevée ferait échouer ce contrôle. Le restart après préparation conserve
la décision en attente. L'abandon partiel retire d'abord un cache vide, puis
rencontre une donnée inattendue : le restart doit préserver cette donnée et
l'allocation, avant résolution explicite. Un répertoire antérieur vide est
conservé. Les régressions agent, limites et instances gérées sont exécutées
séparément, en série ; ces preuves ne remplacent pas celles de l'API publique.

### Console de publication et manuel — SLS-062/063

| Contrat livré | Preuve E2E réelle |
| --- | --- |
| Préparation du code, conservation serveur, droits et versions | Dix groupes de `e2e/code-publications.mjs` |
| ZIP depuis la console, suivi, abandon, activation et suppression | 21 groupes de `e2e/publication-ui.mjs`, invocations Docker après activation |
| Réponses perdues après commit, retour sans rejeu | Transport réel, sortie de page puis retour et état serveur recoupé |
| Nettoyage physique refusé, garde et reprise | EACCES Docker réel, 503 après suppression logique, SIGKILL/SIGSTOP du helper et maintenance normale |
| Publication enregistrée avec confirmation de stockage retardée | Suspension bornée de l’agent, 503 réel, décision conservée puis quota confirmé |
| Liste/suivi cohérents et succès antérieur retiré | Observation DOM atomique et cinq gestes indépendants après succès réel |
| Manuel au checkpoint SLS-063 du7 novembre | Huit groupes de `e2e/manual-ui.mjs`, SHA256, onze chapitres, 28 paragraphes, tableau, clavier et formats d’écran |
| Régression commune | `python3 -B e2e/execution-suite.py --scope publication` : 18 campagnes, 312 groupes, zéro échec/skip |

La [preuve finale](evidence/publication-console-dev-2026-11-07.json) recoupe les
rapports frais avec les sources et l’image, les 54 captures inspectées, les
archives conservées, le nettoyage et les notes appliquées au SPARK.

## Planifications et concordance du manuel — SLS-078/096

Checkpoint courant : [preuve009](evidence/schedules-checkpoint-dev-2026-11-10.json).
Exécuter en série, après connexion SSO réelle :

1. `node e2e/schedules.mjs` : six groupes, deux frontières UTC réelles, cron
   Unicode, prévision nominal passé/frontière future, fusion, droits, pilote,
   état désactivé, handler Docker et console depuis l'accueil.
2. `node e2e/manual-ui.mjs` : huit groupes ; concordance du SHA,16 chapitres et
   56 paragraphes, tableau, focus, ancres, formats et session.
3. `python3 -B e2e/public.py` : huit groupes publics.

Vingt-deux groupes courants uniques ; cinq groupes d'une première image restent
distincts, ainsi que le refus Unicode reproduit avant correction. Les neuf
fonctions de tous les essais sont recoupées purgées. Vingt et une captures
courantes sont inspectées ; SLS-096 est clos. Grammaire, coupures, recouvrement,
saturation, exclusif et états UI ont leurs preuves distinctes dans
[SCHEDULES](SCHEDULES.md). Rétention et régression complète restent ouvertes.
Cette tranche ne
remplace aucune campagne de régression de la plateforme. La campagne complète
SLS-095 doit inclure ces nouveaux clients et cibler les migrations réellement
installées, en conservant les bancs historiques008 dans leur périmètre propre.

Complément indépendant : `node e2e/schedule-versions.mjs`, cinq groupes sur307
sources figées, quatre frontières réelles, cinq handlers et trois fonctions
physiquement purgées. Pilote, promotion, retour par archivage avec remplacement,
retrait, désactivation et suppression sont recoupés ; les appels déjà admis
terminent avec leur hash initial. L'inspection native vérifie l'absence de tirs
après suppression au-delà du404 public. [Preuve](evidence/schedule-versions-dev-2026-11-10.json).
Même image, ID et démarrages,34 backends, configuration officielle et5982
artefacts conservés ; aucune nouvelle preuve visuelle. Les22 groupes précédents
ne sont pas rejoués ni ajoutés à ces cinq groupes. SLS-078.3 est qualifiée.

Grammaire numérique : `node e2e/schedule-calendar.mjs`, cinq groupes du client
final7b2c99e sur308 sources figées. À17:15 UTC, huit tirs et leurs fusions
recoupent listes/plages/pas, OU jour/semaine, heure/mois ; les déclarations
exclues n'ont aucun tir. Douze422 réels et les prévisions dimanche0/7,
31février impossible et prochain29février complètent cette
[preuve](evidence/schedule-calendar-dev-2026-11-10.json). Les dates futures
sont des aperçus API, sans handler prétendu ces jours-là. Quinze handlers du
replay, dont sept préparatoires ; trois fonctions purgées. Le premier passage
vert, puis renforcé sur sa borne d'aperçu, conserve15 autres handlers et trois
purges, sans addition de groupes. Même image/ID/démarrages,34 backends et5982
artefacts conservés ; aucune nouvelle capture. SLS-078.2 est qualifiée.


## Concurrence et adaptateur des crons — SLS-078.4/.7

Commandes en série après le prérequis SSO réel :

| Client | Preuve distincte du11 novembre2026 |
| --- | --- |
| `node e2e/schedule-concurrency.mjs` | [Quatre groupes](evidence/schedule-concurrency-dev-2026-11-11.json),333sources, quatre handlers, deux purges ; observation simultanée HTTP/cron à03:55UTC |
| `node e2e/adapter-schedules.mjs` | [Quatre groupes](evidence/adapter-schedules-dev-2026-11-11.json),334sources, plan/deploy/deux promote, un handler à04:05UTC, deux purges |

Les sources produit et images sont conservées entre les deux époques ; les
index de clients diffèrent. L'essai initial échoué de concurrence et ses deux
purges restent exclus. Aucun replay global ou parcours visuel nouveau prétendu.
Le [rapprochement d'admission](SCHEDULES.md#admission-commune-qualifiée) coche078.4
sans recomptage des groupes historiques ; la CLI qualifie078.7. La capture de
rétention5056167 reste éligible au replay d'âge le18 novembre03:30:26UTC seulement.

`python3 -B e2e/schedule-terminal-history-capture.py` complète cette préparation :
[trois groupes réels](evidence/schedule-terminal-history-capture-dev-2026-11-11.json),
335sources, tir terminal et générations99/100 retirées conservés, dont une sans
tir. Ce sont les témoins authentiques de la campagne CLI précédente, sans nouvel
appel ou fonction créé. SQLite natives intègres,5982 artefacts, images exportées
et services recoupés ; borne commune d'âge18 novembre04:05:13.358459UTC.
L'âge, l'effacement, les pannes propres et les bornes10000 restent à éprouver.

## Borne globale des invocations — SLS-078.5/091.1

`node e2e/invocation-retention-volume.mjs` passe
[trois groupes réels](evidence/invocation-retention-volume-dev-2026-11-11.json)
sur337sources :10016 handlers HTTP réussis,5008 par fonction, puis exactement
les10000 observations les plus récentes conservées et les16 plus anciennes
supprimées. Les deux fonctions sont purgées et les originaux restitués. Les
relevés complets restent dans le rapport brut compressé lié par cette preuve.

Les [régressions des gardes](evidence/invocation-retention-guard-regressions-dev-2026-11-11.json)
passent14 groupes distincts : cinq modes de
`node e2e/instance-limit-environment.mjs` (release, eof, sigterm, sigkill,
deadline), puis `node e2e/storage-legacy-recovery.mjs --partial` et
`python3 -B e2e/instance-limit-guard-options.py`. Onze groupes à337sources,
trois à338 ; toutes les sources communes et les images sont identiques.
Les refus de paramètres précèdent toute fenêtre ; la garde par défaut900s
est réellement programmée puis restituée, sans prétendre son expiration.
L'expiration réelle est couverte séparément à120s et la reprise partielle à60s.

Soit17 groupes pour cette étape, sans recomptage des assertions internes.
La borne des tirs et la source protégée sous borne numérique ont leurs preuves distinctes ci-dessous. Les sept jours,
les pannes propres des nouveaux clients et la campagne complète restent ouverts.

## Préparation de la borne des tirs — SLS-078.5

`node e2e/schedule-firing-volume-capture.mjs`, seul sur le SPARK DEV au repos,
avec identifiants SSO sur stdin privée, passe
[quatre groupes](evidence/schedule-firing-volume-capture-dev-2026-11-11.json)
sur340sources31b9102 :256 tirs réels à06:15UTC, deux handlers/254 refus sans
invocation, copie native protégée,16 purges et restitution jointe. Le premier
essai27221ea échoué reste distinct. Éligibilité après39 fenêtres :09:30UTC le
11 novembre. Cette préparation ne prouve ni10000 ni sept jours ; replay numérique qualifié ci-dessous.
La frontière de copie interrompue est qualifiée séparément ci-dessous.

Les [régressions355453b](evidence/schedule-firing-volume-guard-regressions-dev-2026-11-11.json)
passent20 groupes sur les mêmes340sources : cinq modes de
`instance-limit-environment.mjs` puis `storage-legacy-recovery.mjs --partial`
(11 groupes), `instance-limit-guard-options.py` (3), et trois modes de
`instance-limit-admission.mjs` (`--consumer-loss`, `--observer-unavailable`,
`--foreign-namespace`,6 groupes). Chaque commande est terminée avant la suivante.
Total de l'étape24, sans réattribuer les anciennes preuves ni compter l'essai échoué.

Le pilote `node e2e/schedule-firing-volume-replay.mjs MODE` passe
[neuf groupes propres](evidence/schedule-firing-replay-preflight-dev-2026-11-11.json)
sur342sources e53b0d9 : invalid1 (huit refus), not-eligible1, preflight3,
seed-loss2 et observer-loss2.4864 tirs et64 pages API, zéro nouveau handler,
sources scellées conservées, restitutions jointes. Les trois essais échoués
restent exclus. Les
[vingt régressions du helper courant](evidence/schedule-firing-replay-guard-regressions-dev-2026-11-11.json)
passent sur les mêmes342sources :11 restitutions,3 options et6 sûreté/consommateur.
Étape29 groupes (9+20). Count après39 fenêtres qualifié séparément ci-dessous ; aucun résultat numérique ou d'âge déduit du préflight.

Le [complément e23e820 sur deux lots](evidence/schedule-firing-replay-two-batches-dev-2026-11-11.json)
passe trois groupes sur342sources courantes :36 fenêtres manquées/9472 tirs,
observation9,94s, nouveau SSO/96 pages API, restitution/source inchangée. Ce
complément ne qualifie ni10000 ni sept jours ; les trois groupes ne remplacent
pas les neuf contrôles propres et les20 régressions historiques.

## Interruption du copieur initial — SLS-078.5

`node e2e/schedule-firing-volume-capture.mjs --copy-loss` passe
[cinq groupes](evidence/schedule-capture-interruption-dev-2026-11-11.json) sur342sources
dbb840b : nominal complet, puis interruption au premier pas1/140 du vrai backup,
perte du pilote, garde bloquée2,043s, SIGKILL à5,07s/40s et jonctions, restitution
indépendante. Captures scellées identiques avant/après ; partiel protégé mais
sans intégrité revendiquée. L'essai c5fcb1d échoué reste exclu. Les [vingt régressions](evidence/schedule-capture-guard-regressions-dev-2026-11-11.json) passent sur les mêmes342sources ; borne10000 et sept jours non qualifiés par ces groupes.

## Plafond global isolé — SLS-099

Commande publique canonique : `python3 -B e2e/public-invocations-suite.py`,
identifiants SSO sur stdin privée. Le lanceur prépare des sessions réelles,
exécute les trente groupes HTTP et leur nettoyage, puis les quatre groupes
isolés. Le rapport public conserve31 groupes :30 HTTP et le groupe parent du
plafond, dont quatre détails sont conservés sans double comptage.
`node e2e/public-invocations.mjs` seul produit le rapport HTTP de trente groupes ;
il ne constitue plus la campagne publique complète.

Preuves ciblées distinctes : cinq modes de `instance-limit-environment.mjs`
(dix groupes), `instance-limit-admission.mjs` (quatre groupes), puis ses modes
`--consumer-loss`, `--observer-unavailable`, `--foreign-namespace` (six groupes).
Mêmes image réelle, moteur, agent, Docker et SSO ; aucune mutation des variables
officielles. Les époques et les essais arrêtés restent séparés dans leurs preuves.
Le [rejeu final](evidence/instance-limit-public-integration-dev-2026-11-11.json)
passe sur329sources et imagec59b8616 :31 groupes publics via le scope canonique
`public-invocations` de la suite générale, dix groupes du helper final et un
groupe historique --partial. Treize fonctions HTTP et trois isolées purgées,
originaux restitués, zéro écriture officielle. Le parent plafond conserve ses
quatre détails ;42 groupes parents ou45 feuilles, sans addition des deux.
La campagne complète de plateforme reste requise pour sa clôture globale.

## Borne globale des tirs — SLS-078.5

Le mode `node e2e/schedule-firing-volume-replay.mjs count` passe
[trois groupes réels](evidence/schedule-firing-retention-count-dev-2026-11-11.json)
sur342sources ef8cb3f :39 fenêtres réellement manquées,10240→10000 tirs au même
curseur09:30UTC,240 plus anciens exactement retirés. Chaque fonction avait640
tirs avant borne ;112 pages API après SSO concordent avec les survivants natifs.
Observation10,82s, deux invocations initiales seules, restitution jointe et source
scellée inchangée. Source protégée sous borne, sept jours et campagne complète
restent ouverts ;078.5 reste non clôturée.

## Source protégée sous borne — SLS-078.5

Le [contrat discriminant](INVOCATION_SOURCE_RETENTION_VOLUME.md) exige trois
ensembles natifs10002→10001→10000 et les deux plus anciens HTTP exactement
retirés. Clients : `node e2e/invocation-source-retention-volume.mjs` (SSO privé),
puis gardes `python3 -B e2e/source-retention-guard-options.py`, en série. Même
image réelle,10000 HTTP initiaux sur deux fonctions et rendez-vous cron/HTTP.
Le nominal de trois groupes est qualifié séparément ci-dessous ; pannes
propres encore requises et régressions de la fenêtre commune qualifiées par 25 groupes.

### Garde2700 et refus qualifiés

La [preuve f59a8d3](evidence/source-retention-guard-options-dev-2026-11-11.json)
passe cinq groupes sur346sources inchangées : quatre refus avant mutation,
puis programmation2700s et restitution nominale jointe. Même contrôle/image,
configuration et référence conservés, pilote et garde terminés. L'expiration2700
n'est pas revendiquée. Le collecteur initial a échoué sur un glob incluant son
checkpoint ; le rapport E2E terminé0 est conservé et recoupé avant/après sans
rejouer les tests. Charge10000 et frontières sont qualifiées séparément ci-dessous ;
pannes propres encore requises et régressions communes qualifiées séparément.
Ces cinq groupes seuls ne prouvent
pas la rétention.

## Pilote durable du volume source — SLS-078.5

`python3 -B e2e/source-retention-worker-loss.py` : vrai SSO et appels sous
worker utilisateur indépendant, SIGKILL MainPID et résultat signal9 finalisé
comme échec, puis retrait de deux consommateurs et restitution native. Trois
groupes requis, pas de mock ni rétention déduite. Ensuite le nominal utilise
`invocation-source-retention-worker.py start`, contrôlé par `status UUID` et
`finish UUID` après fin réelle. Checkpoint, code Node, état système et sources/
images avant/après doivent concorder. Perte et nominal qualifiés séparément ci-dessous.
Le premier essai200ea30 reste échoué et exclu ; le contrôle corrigé relève les
identifiants Docker réels avant faute puis leur absence et celle des baux après
restitution, en distinguant les retraits explicites de la garde.

### Perte du pilote durable qualifiée

La [preuve bbe9d0e](evidence/source-retention-worker-loss-dev-2026-11-11.json) passe trois groupes
sur348sources figées :512 réponses HTTP réelles, contrôleur initial terminé et
worker indépendant recoupé, SIGKILL MainPID avec résultat signal/Code2/Status9
conservé comme échec. Deux conteneurs/réseaux et consommateurs sont inventoriés
avant faute puis réellement absents après restitution ; les deux retraits de
chaque classe sont aussi enregistrés par la garde dans ce cas. Restitution
indépendante terminée, mêmes données/configuration/images et référence, garde
et unité locale jointes. Le premier essai échoué reste exclu. Ces trois groupes
qualifient la perte et sa restitution ; nominal numérique qualifié séparément ci-dessous, sept jours encore requis.

### Qualification distincte de la source

Le [nominal de source protégée](evidence/invocation-source-retention-volume-dev-2026-11-11.json) passe trois
groupes sur348sources d860cc5 :10001 HTTP et un cron,10002→10001 avec tir non
clos puis10000 après clôture. Exacts deux plus anciens HTTP retirés, source
inchangée,5001 lignes par fonction avant borne, observation12,34s, deux purges
publiques et restitution nominale jointe. Sept jours et campagne complète restent
ouverts ; cette preuve ne clôture pas078.5.

## Replay des témoins encore jeunes — SLS-078.5

[Treize groupes](evidence/retention-history-replay-preflight-dev-2026-11-11.json)
sur351sources : trois groupes de refus (huit options et deux âges prématurés),
six groupes pour les deux préflights avec vrai SSO/API et restitutions nominales.
La source non close conserve ses deux appels, son instance est récupérée et
son tir se clôt normalement, sans nouveau handler. Observation9,859s sous25s.
La seconde source conserve tir terminal et générations ; aucun DELETE d'âge
n'est revendiqué. Captures/images/originaux inchangés, copie retirée et garde jointe.
Quatre essais échoués sont exclus et conservés en preuve distincte. Les deux
pertes sur la source vivante ajoutent quatre groupes, avec gardes indépendantes120,
source intacte et pilotes joints. Les bornes natives sont recoupées séparément,
zéro groupe ajouté. Le contexte cloné sous namespace supplémentaire est
qualifié séparément ci-dessous ; régressions et âge encore ouverts.

### Refus du périmètre cloné

[Quatre groupes9f3e7da](evidence/retention-history-namespace-scope-dev-2026-11-11.json),
dont deux préflights rejoués, passent sur351sources. Objet API et même temporaire
conservés au refus, original arrêté ; retrait de la seule fixture puis restitution
explicite avant expiration du timer. Sources/captures/configuration/originaux
conservés et gardes jointes. Deux clients seuls diffèrent de la preuve précédente.
Perte HTTP non provoquée ; régressions communes qualifiées ci-dessous, âge ouvert.

## Régressions finales des fenêtres de restitution

La [preuve au commit f908640](evidence/retention-history-guard-regressions-dev-2026-11-11.json)
passe 25 groupes sur 351 sources identiques avant/après : onze fenêtres/partiel,
trois options/défaut 900, cinq options 2700 et six consommateur vivant/pause/
namespace. Onze campagnes distinctes, images conservées. Les confirmations
SIGTERM (15) et SIGKILL (9) ont pidfd lisible puis pilote absent de /proc, mesurées
10,765 ms et 28,345 ms ; gardes de 120 s et restitutions attendues jointes. Les
options 900/2700 s sont programmées puis restituées, pas laissées expirer.

Les trois essais antérieurs sont exclus ; le ciblé SIGKILL de deux groupes n'est pas ajouté
au même cas de cette matrice. Le contrôle final garde le même conteneur 68a8 et image c59,
redémarrage à 14:26:18 UTC, référence inchangée, deux services sains, actifs à zéro, 5 982 artefacts
et aucune garde. Cette preuve qualifie les fenêtres communes ; pannes
propres de capture et d'observateur source, âge et campagne complète restent
ouverts dans 078.5. Les preuves antérieures conservent leurs époques distinctes.

## Refus après attachement qualifié

La [preuve 956498a](evidence/invocation-source-observer-refusal-dev-2026-11-11.json)
passe deux groupes sur 351 sources identiques avant/après. Le scénario du
créneau réel 15:00 UTC ne produit aucun HTTP ordinaire : un vrai HTTP et un
vrai cron sont running, leur tir/UUID/fonction recoupés. L'opérateur constate
l'historique insuffisant après attache : TracerPid 471960 sur le contrôle
470002/naissance 502682872, puis zéro après detach ; mémoire et lecteur fermés.
Son reçu garde completed=false et AssertionError/retention_history_incomplete.
Le code retour individuel de l'opérateur n'est pas enregistré ; celui du
helper est bien 1, avec l'assertion exacte conservée en privé et son SHA.

Le client de qualification termine 0 après ce refus attendu et la restitution
nominale jointe, sans ajouter de succès de rétention ni de purge métier. Deux
conteneurs, deux réseaux et deux baux sont corrélés puis retirés, canaux et
artefacts absents. Contrôle final : même conteneur/image, redémarrage attendu
15:00:08 UTC, référence inchangée, deux services sains, actifs à zéro, 5 982
artefacts et aucune garde active. Seuls les deux fichiers de cet observateur/
client diffèrent des 25 régressions précédentes ; helper et images inchangés.

Ce refus qualifie une panne après attache et son nettoyage normal. Il ne
qualifie pas une erreur de detach, l'alarme 35 s, la coupure 40 s, l'attente
native 25 s sans événement ni l'âge de sept jours. Le nominal numérique garde
sa preuve distincte au commit d860cc5 ; la campagne complète reste requise.

## Pertes avant la capture initiale et non-régression nominale

[Huit groupes de panne](evidence/schedule-retention-gate-losses-dev-2026-11-11.json),
puis [quatre nominaux](evidence/schedule-retention-capture-regression-dev-2026-11-11.json)
passent sur 351 sources au client 20ffc09, mêmes images. EOF 1, SIGKILL pidfd/SSH
255, TracerPid réel puis zéro, garde indépendante 80 s, mêmes UUID/dates et
captures canoniques conservées ; trois purges physiques. Les trois refus CLI
précoces restent un contrôle local distinct, non ajouté aux douze groupes E2E.
Backup/copie interrompus, historique du helper et âge réel non qualifiés ici.

Le [rejeu historique courant](evidence/schedule-recovery-regression-dev-2026-11-11.json)
qualifie ensuite cinq groupes sur les mêmes 351 sources 7ed2abe et images :
trois coupures 137, trois tirs suivants, absence de rejeu, quatre gardes jointes
et une purge physique. Quatre handlers réussis dont un initial, une invocation
liée interrompue avant démarrage. Worker terminé systemd Code1/Status0/success,
malgré timeout distinct 20 s de son lanceur ; aucun redémarrage du worker.
Captures canoniques inchangées, deux services sains, actifs à zéro et 5 982
artefacts. Pas de résultat backup/copie, sept jours ou campagne complète ajouté.
