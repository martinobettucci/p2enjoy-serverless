# Matrice de qualification réelle

Les [lecteurs de code concurrents](evidence/code-editor-read-concurrency-dev-2026-11-12.json) passent **34 groupes réels** :
9 ciblés puis25communs, sur414sources11b90326/imageb452ef16. Quatre vrais
workers retiennent quatre FD ; trois nouveaux threads sont rapprochés malgré
leur arrêt initial reçu avant celui du parent. Le cinquième appel donne429 en
63ms, puis les quatre réponses et la capacité reviennent. Libération, EOF,
SIGKILL, suspension/secours60s et vraiEMFILE du seul secours passent.
Sept handlers nominaux et22images communes sont recoupés ; trois fonctions/
tokens de tous les passages, six parents et16helpers sont nettoyés. Les deux
échecs restent séparés, zéro groupe ajouté. Contrôle redémarré avant campagne
avec backupf0543e39, même CID/image ; référence/configuration/5982artefacts et
manuel18/74SHA8a50ffa0 conservés.070.1–.5 restent ouverts pour les autres
preuves : droits pendant IO, purge face à lecteur vivant, reconstruction/ZIP,
focus sous attente et reprises de publication.

Le [complément console de l’éditeur](evidence/code-editor-console-focus-dev-2026-11-12.json) passe **43 groupes réels** :
18 UI puis25régressions, sur407sources6600150c et imageb452ef16. Sept versions
sur deux pages5+2, archive sélectionnable/supprimée désactivée, adoption locale
sans PUT puis sauvegarde explicite et diff paginé sont recoupés. Quatre titres
H2 et deux détails H3 reçoivent le focus en1440/390px.51images inspectées,
14handlers nominaux ; deux fonctions/tokens de tous les passages nettoyés,
quatre parents supprimés,26helpers disparus et5982artefacts conservés.
Manuel18chapitres/74paragraphes, SHA8a50ffa0 ; dix migrations inchangées.
Le premier passage échoué reste séparé, zéro groupe ajouté. SLS-070 et ses
critères070.1–.5 restent ouverts pour ZIP/concurrence, droits pendant IO et
interruptions ; les gestes de focus sous attente gardent leur preuve propre.

Le [complément de sources de l’éditeur](evidence/code-editor-source-limits-dev-2026-11-12.json)
qualifie38groupes réels :13ciblés puis25communs sur406sources59dd4591/image60938093.
Source archivée, conservation1Mio+1, chemins512/255octets, diff2000/128Kio et
JSON8Mio passent, avec cinq handlers et inventaires exacts A246→B250/C246.
22captures inspectées, deux fonctions/tokens nettoyés,5982artefacts conservés.
Le premier passage NameErrorUUID reste une preuve échouée séparée, zéro groupe
additionné. Ce complément ne ferme aucun critère de070 ; ses autres bornes,
parcours console et reprises gardent leurs preuves à produire.

Le client HTTP **Tester une fonction (SLS-071)** est livré et qualifié en DEV.
La [preuve finale du dernier critère](evidence/function-http-client-task-exception-dev-2026-11-12.json) passe **31 groupes réels** :
6 ciblés et 25 régressions sur 401 sources 67215a2b, image 60938093 inchangée ;
26 captures inspectées. Un vrai `openat` échoue avec `EMFILE` ; les limites sont
rendues avant reprise Python, qui lève un `OSError` dans le constructeur TLS.
Le même PID conserve quatre places, refuse le cinquième appel en 429 puis
réussit les appels suivants. Douze handlers nominaux et nettoyages natifs sont
recoupés ; les trois passages échoués restent séparés, sans groupe réadditionné.
Les huit critères s’appuient aussi sur leurs preuves43/46/42/32/37 distinctes.
Manuel18chapitres/74paragraphes conforme, schéma010 et5 982artefacts conservés.
Les défauts101/102 et la campagne complète095 restent ouverts. Les paragraphes
historiques ci-dessous gardent leur époque ; ils ne remplacent pas ce statut.

La [lecture réellement en attente](evidence/function-http-client-loading-dev-2026-11-12.json) est qualifiée sur l’image
60938093 : **37 groupes réels** (7 reprise, 5 chargement, 25 régressions),
397 sources d’empreinte 6b9cb2bc et 30 captures inspectées individuellement.
Le GET reste sans réponse pendant les vues desktop/mobile « Lecture en cours… ».
Après perte de l’observateur, la garde est jointe et le même PID est vivant,
sans invocation rejouée ; un nouvel appel explicite réussit. Trois fonctions
purgées, deux jetons révoqués, zéro garde/bail/réservation et 5 982 artefacts
conservés. **SLS-071.2 est qualifié**, avec les preuves antérieures des modes
serveur/CORS et du refus de source. SLS-071 reste ouvert pour 071.6 ; les
anomalies visuelles 101/102 et la campagne complète restent à traiter.
Les checkpoints historiques ci-dessous gardent leurs propres dates et groupes.

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

## Sauvegarde et copie initiales interrompues

Les [douze groupes bca96ab](evidence/schedule-retention-copy-losses-dev-2026-11-11.json)
passent sur 351 sources/images identiques : backup16/4 837 pages puis
copy2 1/5 990 fichiers, helpers réellement en T, garde80 indépendante tuant
et joignant chacun, TracerPid final0 du même contrôle sans redémarrage.
Huit groupes de panne et quatre du nominal16:50, six handlers réussis,
trois purges physiques. Partiels0+512 octets et19 824 640+4 484 octets
conservés/protégés sans manifeste final ; captures canoniques inchangées.
Six refus d'options client/helper réel sont séparés, sans groupe E2E ajouté.
Seuls deux fichiers helper/client changent depuis l'époque historique7ed2abe ;
les cinq groupes de reprise ne sont pas déclarés rejoués ici. Autres pannes
d'observation, sept jours et campagne complète restent ouverts.

## Délai natif sans événement — reproduction

Les [trois groupes c64fdd7](evidence/native-observer-deadline-reproduce-dev-2026-11-11.json)
passent sur353sources/images identiques : vrai contrôle temporaire gelé,
WNOHANG0, attente25 qui ne lève qu'à28,202s après dégel indépendant28.
Alarme35 non expirée, terminal acteur/jonction, dégel avant detach,
TracerPid0, mémoire/lecteur fermés et originaux restitués. Aucun handler.
Cette preuve confirme le défaut d'attente, sans qualifier sa correction,
les expirations35/40 de l'opérateur source ou une rétention.

Les [trois groupes bounded46e216d](evidence/native-observer-deadline-bounded-dev-2026-11-11.json)
passent ensuite sur353sources/images identiques :25,000182s avant le secours28,
masque[] restitué, handler d'alarme conservé/reste34,902→9,902s. Dégel réel
avant detach, acteur terminal/joint, TracerPid0/mémoire/lecteur fermés et
originaux restitués. Aucun handler exécuté ; seules classe partagée et deux
fichiers du probe diffèrent de la reproduction. Consommateurs et pannes35/40
ont leurs replays distincts ci-dessous ; aucune rétention ni campagne complète déduite.

## Consommateurs de l'observateur corrigé

Les [onze groupes96dcca0](evidence/native-observer-consumers-dev-2026-11-11.json)
passent sur353sources/images identiques, même époque que bounded46e216d :
trois borne des tirs (10 496→10 000, exacts496retirés,13,526s), trois source
préflight9,189s, trois terminal préflight0,005624s, deux refus source après
attache/fermeture/TracerPid0 et absence physique. Quatre campagnes sérielles,
SSO/API réels, captures canoniques conservées et restitutions jointes.
Deux nouveaux handlers running dans le seul cas de refus ; les témoins copiés
ne sont pas recomptés. Le préflight ne prouve pas sept jours. Nominal numérique
courant, detach en erreur et35/40 sont qualifiés séparément ci-dessous ;
sept jours et campagne complète restent requis.

## Bornes propres de l'opérateur source35/40

Les [six groupes e45126b](evidence/source-observer-deadlines-dev-2026-11-11.json)
passent sur354sources/images identiques :35/TimeoutError en35,683720s,
40/wrapper124 en40,009839s, puis refus sans option. Le binaire timeout réel
est recoupé par /proc/SHA ; aucun waitstatus137 du fils n'est déduit.
Trace0 avant retrait, acteurs terminaux/joints et union initiale/remplacements
(quatre CID/réseaux/consommateurs par faute) physiquement absente : neuf
contrôles historiques et sept exacts. Trois refus CLI comptent zéro groupe ;
les deux essais échoués restent exclus. Deux services sains, actifs à zéro,
5982artefacts et aucune garde finale. Detach en erreur, nominal numérique et
historique final sont qualifiés ci-dessous ; âge réel et campagne complète
restent dans078.5.

## Lecteur fermé malgré l'erreur native de detach

[Quatre groupes b5f0825](evidence/source-observer-detach-failure-dev-2026-11-11.json),
355sources/images identiques : faute19:10 et refus19:15UTC. Vraie exception de
wait5 après SIGSTOP/SIGCONT à5,255s, primaire conservée et lecteur/mémoire fermés,
masque[] restitué après SIGCHLD17 bloqué. Mort/Trace0 puis dégel sans secours,
acteur joint,9+7contrôles physiques et originaux restitués. Premier essai sans
exception exclu. Consommateurs, nominal numérique et historique final qualifiés
ci-dessous ; âge réel et campagne complète restent requis,078.5 reste ouverte.

## Consommateurs courants après la faute de detach

[Bounded courant](evidence/native-observer-detach-bounded-dev-2026-11-11.json),
trois groupes25,000300s, puis [six campagnes/quinze groupes](evidence/native-observer-detach-consumers-dev-2026-11-11.json)
au même gel355sources/images : count19:20 (157fenêtres,10 496→10 000/exacts496
retirés,12,758454s), source préflight19:25(9,476869s), terminal19:30(0,005154s),
refus19:35,35/1 à19:40 et40/124 à19:45. SSO/API, captures conservées,
acteurs/ressources joints et restitutions passent. Six handlers nouveaux
seulement, distincts des copies ; même imagec59b8616, originaux sains,5982artefacts
et aucune garde. Nominal source numérique et historique final qualifiés
ci-dessous ; sept jours et campagne complète restent requis.

## Reprise historique finale du helper courant

[Cinq groupes ef98a9f](evidence/schedule-recovery-detach-regression-dev-2026-11-11.json)
sur355sources/images identiques au bounded et aux quinze consommateurs.
Trois coupures137, trois échéances manquées et trois tirs suivants réussis sans
rejeu ; claimed sans invocation et linked interrompu avant handler. Trois
handlers réussis, quatre gardes jointes, purge physique et captures conservées.
Même worker réel terminé0, reçu terminal conservé puis unité arrêtée.
Brut682440/gzip85987. Deux services sains, actifs/baux nuls,5982artefacts et
aucune garde. Nominal numérique source courant qualifié ci-dessous ; sept jours
et campagne complète restent requis,078.5 non clôturée.

## Nominal numérique de la classe courante qualifié

La [preuve6de2a86](evidence/invocation-source-retention-detach-volume-dev-2026-11-11.json) passe trois groupes
sur355sources/images identiques au bounded et à l'historique final.10001 réponses
HTTP et un cron réels donnent10002 observations terminales,5001 par fonction.
Le tir non clos garde sa source hors comptage :10001 lignes après retrait du
plus ancien HTTP. Après clôture normale, le deuxième plus ancien HTTP disparaît :
10000 lignes et source strictement identique, désormais comptée. Les trois vecteurs
sont recoupés exactement ; observation12,410435700s sous25s.

Deux purges publiques et restitution nominale jointe ; même worker réel terminal0,
reçu conservé puis unité arrêtée. Collectes natives/captures fraîches après cette
finalisation, liées au SHA terminal :2services sains, actifs/baux nuls,5982artefacts
et aucune garde. Captures canoniques inchangées. Brut83048624octets/gzip4228693 ;
ancienne preuve348 préservée. La borne native partagée et son nominal sont
qualifiés ; âge18novembre et campagne complète restent requis,078.5 non clôturée.

## SLS-100 — Icône Serverless distincte qualifiée

[29groupes réels](evidence/application-icon-dev-2026-11-11.json) sur356sourcesb1ee473/image779aef7b :
4accueil/SSO/navigation/déconnexion desktop/mobile,8manuel,8publics,9connexion.
26captures inspectées (4par le principal,22par le vérificateur), previews16/32/64
et contraste9,03:1 ; source SVG servie recoupée par SHA/no-store. Les34backends et
les trois autres ressources web restent identiques. Le manuel sert16chapitres/
56paragraphes conformes à sa source. Configuration, référence et5982artefacts
conservés ;2services sains, actifs/baux nuls et aucune garde. SLS-100 clôturée,
la campagne complète de plateforme et l'âge réel de078 restent distincts.

## SSO : durée réelle et renouvellement, SLS-089 partielle

`node e2e/sso-session-recovery.mjs` reçoit le JSON SSO par stdin privée. Huit
groupes réels, puis8 du manuel/8 publics/9 de connexion, soit33 au gel de 359 sources, commit 1ac2523 et image
e81007c5 : [preuve partielle DEV](evidence/sso-session-recovery-dev-2026-11-11.json). Les deux JWT signés mesurent300 s ;
300,659 s d’attente et inspection, nouveau iat après expiration initiale, même
cookie/sujet/CSRF et échéance absolue, déconnexion puis ancien cookie refusé.
Les4 attentes sont des pages publiques, sans décision de rôle. 30 captures
recoupées, dont2de chapitre ajoutant0 groupe ; 16 chapitres et 57 paragraphes compilés.
Les négatifs azp/aud, les vrais profils sans droits et la rotation/pending503
restent non éprouvés ; aucune vue 503 réelle inspectée. L’unité089 reste [~],
son seul critère 089.4 passe [x].

## Testeur : source refusée et hash confirmé, complément0712

[32groupes réels](evidence/function-http-client-source-access-dev-2026-11-12.json)
sur395sources28105d2b/image60938093 :7ciblés puis8manuel/8publics/9connexion.
EACCES natif et503 sans invocation, témoins publics, URL/résultat retirés, hash
courant exact, reprise alias, absence confirmée et pilote archivé404/retour.
Six handlers succeeded,32captures inspectées dont2du nouveau paragraphe,
deux fonctions et deux jetons des deux passages nettoyés.38backend/4web recoupés,
5982artefacts et officiels conservés. Le premier échec ne compte aucun groupe ;
071.2 garde la preuve dédiée du chargement,071.6 son exception vivante,101/102
leurs défauts visuels ; la campagne complète de plateforme reste distincte.
