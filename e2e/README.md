# Qualification de la plateforme

Les clients de ce répertoire visent exclusivement le déploiement DEV réel.
Ils n'importent pas les handlers, ne créent pas de serveur substitué et
n'interceptent aucune réponse réseau. Le navigateur utilise la connexion SSO
normale. Un accès absent est une erreur de prérequis, jamais un test ignoré.

## Stockage public et manuel

Après synchronisation des sources sur le SPARK, exécuter successivement depuis
la racine `node e2e/storage-console-api.mjs`, `node e2e/storage-console-ui.mjs`,
`node e2e/manual-ui.mjs`, puis `node e2e/control-ui.mjs`. Les campagnes ciblées
passent respectivement neuf, neuf, huit et onze groupes réels. La preuve reste
un [checkpoint SLS-065](../docs/evidence/storage-console-checkpoint-dev-2026-11-07.json) :
les pannes et reprises du contrôle public et les régressions élargies restent ouvertes.

Les deux campagnes stockage créent leurs ressources et les purgent par leurs
API publiques. Le rapport exige `completed`, `cleanup` et zéro test ignoré.
La campagne navigateur perd réellement une réponse, conserve l’UUID puis
reprend sa lecture sans second POST ; la pagination subit une vraie coupure
réseau du navigateur. Aucune interception de réponse n’est utilisée.

Au repos, `storage-console-inspect.py` s’exécute comme root du seul SPARK DEV,
avec un argument JSON associant chaque `namespace_id` à la liste exhaustive
de ses `function_ids` (ou `[function_id]` pour la campagne UI), lus dans les
rapports réussis. Il lit les deux bases sous leur propriétaire `spark-docker`,
recoupe reçus, budgets, artefacts, montages, canaux et ressources Docker, puis
vérifie le vide des secrets dans le conteneur sans en sortir leur valeur.
Les inventaires trash et canaux non attribuables doivent être globalement vides.
Le collecteur ne supprime rien ; toute ressource restante fait échouer la preuve.
L’appelant doit conserver les empreintes des rapports et du collecteur avec
son résultat pour rattacher les UUID aux campagnes effectivement exécutées.

Le manuel est recoupé intégralement avec `docs/manual.md` : treize chapitres,
34 paragraphes et empreinte SHA256. Ses onze captures comprennent les nouveaux
chapitres cache et archives sur ordinateur et mobile ; elles doivent être relues.

## Banc et campagnes

Installer les dépendances par `npm ci`, puis le navigateur par
`npx playwright install chromium`. Exécuter un seul scénario à la fois.
Les captures et fichiers contenant une session sont conservés uniquement
sous `.local/`, ignoré par Git. Ne jamais publier un état de navigateur.

Depuis la racine du dépôt, chaque commande attend la fin de la précédente :

```sh
python3 e2e/public.py
node e2e/login-ui.mjs
node e2e/authorize.mjs
node e2e/control-admin.mjs
node e2e/control-ui.mjs
node e2e/deployments.mjs
node e2e/adapter-deploy.mjs
node e2e/publication-recovery.mjs
node e2e/function-storage.mjs
node e2e/public-invocations.mjs
```

`python3 e2e/proxy.py --expected-proxy 10.77.0.1` s'exécute depuis le poste et
mesure les chemins réseau via HTTPS et SSH. Les pilotes `login-limits.py`,
`login-capacity.py` et `control-operations.py` s'exécutent comme `spark-docker`
dans le SPARK DEV. Les deux premiers exercent les limites SSO ; `login-limits`
redémarre aussi le contrôle. Le dernier utilise des conteneurs temporaires de son image immuable pour les
pannes de configuration, de clé et de base, le verrou exclusif d’état et la
reprise de maintenance après une contention SQLite réelle. Les fichiers `.proof-*.json`
produits sous `/srv/p2enjoy-serverless/control` contiennent les résultats
expurgés. Leurs ressources temporaires sont nettoyées après chaque campagne.
`python3 e2e/report-interruption.py`, depuis le poste après `public.py`, tue
réellement un client de preuve après son premier échange HTTP, vérifie que
l'ancien rapport réussi est invalidé, puis rejoue la campagne publique.
Les rapports ne valent que lorsque `completed` est vrai et les nettoyages
réussis ; leur initialisation précède les prérequis externes.

`python3 e2e/execution-suite.py` rejoue en série les quatorze campagnes du
moteur et de régression sur le SPARK DEV. Chaque commande attend la fin de
la précédente ; les rapports sont vérifiés comme fraîchement régénérés et
rattachés à leurs empreintes, aux sources locales et à l’image du contrôle
observée avant et après chaque campagne. Une modification pendant la suite
ou un prérequis absent provoque un échec. Le journal atomique est
`.local/e2e/execution-regressions.json` ; les 31 groupes d’invocations sont
exécutés en dernier. Les propositions de notes et la revue visuelle restent
des étapes de clôture distinctes.

`authorize.mjs` ouvre Chromium sur l'accueil de la console et laisse jusqu'à
huit heures au détenteur du compte pour démarrer la connexion SSO. Aucun flow
OAuth n'est créé avant son clic, ce qui évite une expiration pendant l'attente.
Le script ne lit aucun champ de mot de passe.
Il conserve seulement le cookie de plateforme, sous `.local/e2e/` en mode
0600, puis ferme le navigateur. Les cookies du fournisseur ne sont pas
exportés. Les campagnes de gestion et de publication exigent cette vraie session ; son
absence fait échouer leur prérequis.

`control-admin.mjs` crée ses propres objets, qualifie les droits CRUD et
redémarre le conteneur de contrôle du SPARK DEV pour éprouver la persistance.
`control-ui.mjs` crée ses objets depuis la console et augmente temporairement
la latence réelle de Chromium pour vérifier un envoi en cours ; il ne remplace
aucune réponse. Les deux nettoient uniquement les objets qu'ils ont créés.

Les scripts et preuves sont ajoutés au rythme de SLS-020 à SLS-063. Les premiers
contrôles publics, les 19 groupes API administrateur et les 11 parcours UI
ont réussi avec nettoyage confirmé. La [preuve de gestion](../docs/evidence/control-management-dev-2026-11-06.json)
recoupe l'image et les sources ; les cycles de rôles et de clés SSO ainsi que
la campagne complète de plateforme restent ouverts.
La campagne publique comporte huit groupes : découverte OIDC et clés réelles,
santé TLS, ressources de la console, refus anonymes, callbacks malformés,
flows et refus du fournisseur, bornes des corps, puis refus anonymes des routes
de publication. Un upload HTTPS utilisant Expect: 100-continue est refusé
avant l’envoi du corps de 64 Mio annoncé. La cible d'autorisation
est comparée à la découverte fraîchement lue. Les règles de client et de rôle
restent à éprouver par leurs parcours authentifiés.

`python3 e2e/adapter.py` exécute les vraies commandes plan/package sur une
copie temporaire des fichiers de qualification. Il examine les ZIP produits
et exerce les refus, les liens physiques/symboliques ainsi qu'une course
réelle sur le répertoire de sortie. Le même pilote est inclus dans l'image
E2E de l'adaptateur et lancé sur le SPARK par `bash adapter/dev.sh test`.
Sa preuve porte sur la CLI et les fichiers ; elle n'invoque aucun handler et
ne remplace pas les preuves HTTP de déploiement ou d'exécution à venir.

`runtime-validation.py`, lancé sur le SPARK par `bash runtime/dev.sh test`,
exécute le pilote Docker réel de validation. Il utilise les variantes originales
de `qualification/artifacts/`, la vraie dépendance YAML, les valeurs applicatives
de cellule et le contrôle déjà déployé pour éprouver les permissions du socket.
Il vérifie chargement, refus, limites, logs et destruction des descendants ;
son rapport est `runtime/validation-proof.json` sur le SPARK. Il ne prouve pas
encore les autorisations de publication ni l'invocation des handlers.

`artifacts.py`, lancé dans le SPARK par `bash control/artifacts-dev.sh test`,
fabrique des archives réelles et appelle la CLI d'extraction dans son image
Python. Il vérifie les fichiers produits, leurs empreintes et permissions,
les erreurs de format, les bornes, une saturation effective du disque et
des courses sur les destinations et la source. Le dernier parcours empaquette
l'application de qualification, extrait son ZIP puis charge son handler avec
le véritable runtime Node. Le rapport est `control/artifacts-proof.json`.

`deployments.mjs` empaquette les handlers originaux par la CLI réelle, puis
crée namespace, service, fonctions et jetons par les API de gestion normales.
Le chargement asynchrone de `qualification/artifacts/deployment-delay.mjs`
permet les modifications concurrentes réelles pendant la validation Docker.
Les assertions portent sur droits, candidats, import, révisions, révocation,
conflits, admission unique, rollback et suppression des révisions inactives.
Les archives conservées à la suppression d’une fonction sont recensées dans
le rapport ; ce nettoyage de gestion n’est pas une purge d’archives.
Cette campagne exige la session SSO ; ses onze groupes passent, ainsi que les
sept groupes CLI, dans la [preuve authentifiée](../docs/evidence/deployment-authenticated-dev-2026-11-06.json).
Une fixture écrit réellement un secret avant d'échouer à l'import ; le client
vérifie son expurgation et rejoint ses quatre uploads concurrents avant nettoyage.
Les limites
globales, l’expiration, la reprise après crash et les parcours CLI/UI complets
restent des preuves distinctes à compléter et exécuter.

`adapter-deploy-public.py`, exécuté sur le SPARK par `bash adapter/dev.sh
deploy-public-test`, appelle de vrais processus CLI pour les prérequis,
les bornes de configuration et le refus 401 de la véritable API HTTPS DEV.
`adapter-deploy.mjs` crée ses jetons par la session SSO puis lance la vraie
commande deploy : onze fonctions imposent une pagination, un import qui
lève réellement une erreur produit un résultat partiel, et un brouillon
refusé est repris avec Read/Create. Les révisions archivées à la suppression
sont recensées. Ses sept groupes sont réussis et le nettoyage confirmé.
Le recoupement vérifie les archives sur disque et l'absence de réservations,
de canaux et de conteneurs de validation restants. Les cas de rupture réseau,
de modification locale concurrente, de redirection et de réponse trop grande
restent ouverts.

`publication-recovery.mjs` vise les plafonds de 64 candidats globaux et de vingt
révisions, puis deux arrêts brutaux du seul `serverless-api` DEV pendant un
upload partiel et une validation Docker observée. Il redémarre le contrôle,
rejoint les requêtes interrompues et vérifie les états HTTP, SQLite en lecture
seule, fichiers et conteneurs. Il crée ses objets et conserve les archives
antérieures ; aucune base ni horloge n'est modifiée pour obtenir un résultat.
Le rapport `publication-recovery.json` exige completed et cleanup vrais.
Ses quatre groupes passent sur le SPARK DEV : [preuve de reprise](../docs/evidence/publication-recovery-dev-2026-11-06.json).
Le fragment de 192 Kio dépasse le tampon Python réel de 128 Kio ; le pilote
exige des octets présents sur disque avant de couper. Les vingt publications
du plafond utilisent des UUID distincts et le même artefact réel.

`runtime-instances.py` exerce le diagnostic réel en processus séparé : enfants
neufs dans un conteneur chaud, corps aux limites, callbacks, ESM et dépendances,
confinement, logs, mesures Docker, HTTPS sortant, descendants, mémoire/PIDs,
timeouts, signaux et imports bloquants. Une suspension SIGSTOP/SIGCONT du pilote
vérifie qu’un résultat en attente ne devient pas un succès après la deadline.
`instance-lifecycle.py` appelle les méthodes réelles du pilote avec Docker et
son canal Unix pour les courses de démarrage/fermeture, annulations répétées,
nettoyage filesystem refusé puis repris, IDs étrangers, doublons et bornes du
canal. La clé testée est celle de cette instance réelle ; aucun jeton public
ni handler de substitution n’est créé. Un second démarrage refusé doit laisser
l’instance existante utilisable. Les commandes sont `bash runtime/dev.sh
instances-test` puis `bash runtime/dev.sh lifecycle-test`, sur le SPARK.
Les rapports se trouvent dans `runtime/`. La passerelle et les admissions
restent hors de ces preuves de composants.

`managed-storage.py` s'exécute comme root dans le SPARK DEV. Un worker temporaire
est écrit dans le tmpfs du contrôle readonly, puis charge les classes de
production embarquées sous `/app`. Les quatorze groupes utilisent Docker,
l'agent installé et le handler `volume-operations.cjs` pour les quotas,
la persistance, les consommateurs partagés, les annulations et les pannes.
Le parent limite la durée totale, garde la propriété de la cible FUSE, restaure
l'agent et rejoint le worker même si une commande de panne échoue. Le rapport
et les ressources sont vérifiés avant de déclarer le succès. Cette campagne de composant n'exerce pas la passerelle publique : ses preuves
HTTPS sont portées par `public-invocations.mjs`.

`python3 -B e2e/storage-installation.py`, depuis le poste, utilise la console
SPARK sur 127.0.0.1:5175 et le rebond SSH autorisé. Il arrête l'agent au repos,
propose une autre racine par la vraie console et exige le refus de l'installateur
avant création de cette racine. Il restaure la variable officielle et l'agent,
puis vérifie son identité et le maintien du même contrôle. Son rapport est
`.local/e2e/storage-installation.json` ; ne pas lancer une autre campagne pendant
ce changement de configuration de la cellule.

`storage-preparations.py` s'exécute comme root du SPARK DEV. Il appelle les
commandes réelles du client de stockage embarqué dans le contrôle : préparation,
commit, abort et consultation du reçu. Douze groupes couvrent droits de propriétaire,
baux actifs, versions, quota réduit sous saturation, écritures et conservation,
échec sous usage réel, reprise après restart, SIGKILL pendant preparing observé,
abandon partiel devant un fichier inattendu et répertoire vide antérieur préservé.
Le nettoyage confirme la suppression Docker avant release ; une incertitude
garde le bail et bloque abort/purge de cette fonction. Son rapport
`storage/preparations-proof.json` est invalidé avant les prérequis et conserve
les erreurs de restauration. Il qualifie le protocole de l’agent. Les mutations HTTPS sont exercées
séparément par `function-storage.mjs`.


`function-storage.mjs` vérifie treize groupes autour des vraies routes de gestion
et de publication, et un groupe ciblé du pilote embarqué sous verrou SQLite : quotas, usages écrits par Docker, baux, refus et révocation,
SIGKILL avant/après décision, confirmation indisponible, contention SQLite,
publication et rollback, archive avec SHA256 des données. Un timer systemd
indépendant est armé avant chaque suspension de l’agent. La preuve du garde
exige sa trace corrélée et un processus réellement suspendu avant SIGCONT.
Le pilote redémarre explicitement le contrôle après `docker kill` et restaure
les composants avant nettoyage, même en cas d’échec. Le rapport conserve UUID,
décisions, gardes, archives et erreurs de nettoyage ; aucun jeton ni secret.

Les campagnes de gestion et publication utilisent `storage-archives.mjs`
pour une purge opérateur séparée, après leur DELETE normal. Le helper du SPARK
vérifie les UUID exacts de fonction et namespace, leur rattachement, la suppression
logique et l’absence de bail ou mutation avant d’appeler l’agent réel. Les
rapports `storage_archives` conservent l’état archivé précédant cette purge.
Les archives de **code** recensées dans `retained_archives` restent conservées.
Une erreur de purge fait échouer le nettoyage ; les fonctions indépendantes
continuent d’être traitées. Les UUID des fonctions déjà supprimées restent suivis.

## Moteur public

`public-invocations.mjs` publie les handlers originaux du dépôt, appelle HTTPS
avec les vrais jetons et recoupe les observations avec SQLite, Docker et les
baux. Il couvre les droits, enveloppes et limites HTTP, les files, générations,
allocations, modes de stockage, déconnexions et reprises du contrôle. Les
scénarios de corps incomplet distinguent HTTP/1.1 et HTTP/2 conformément au
[contrat de transport](../docs/ADMISSION.md#budgets-et-attente).

Synchroniser `execution-faults.py`, `function-storage-faults.py` et leur module
`control_database.py` dans le SPARK
avant la campagne. Le premier vérifie installation, namespace et UUID avant
les observations ou interruptions ; il ne modifie aucune ligne SQL. L’arrêt
gracieux est observé sous un vrai verrou écrivain et avec des ressources
présentes avant fermeture. Le code 143 d’Uvicorn n’est accepté qu’avec sa fin
de lifespan observée ; SIGKILL reste un scénario séparé. Les gardes indépendantes
redémarrent le contrôle en cas de perte du pilote.

`instance-limit-guard.py`, piloté par cette même campagne, applique temporairement
32 → 2 par les propositions et l’API normale de la console SPARK locale, puis
restaure 32 et recrée le contrôle. Il refuse une proposition préexistante sur
cette clé, des fonctions étrangères ou des consommateurs actifs. Garder cette
clé sans édition concurrente pendant la campagne. La console locale est donc
un prérequis de preuve ; son absence fait échouer la campagne. Les budgets CPU
et mémoire officiels et consommés sont recoupés pour isoler le plafond testé.

Le rapport `.local/e2e/public-invocations.json` conserve des checkpoints atomiques,
les identifiants créés, les archives de code retenues, les gardes et les erreurs.
Le nettoyage attend les états terminaux côté serveur, supprime les seuls objets
créés, purge leurs archives de stockage puis exige l’absence de réservations,
conteneurs, réseaux, baux et canaux résiduels. Un échec de prérequis ou de
nettoyage ne peut pas être déclaré réussi. Les 31 groupes publics et 221 régressions passent dans la
[preuve du moteur](../docs/evidence/execution-dev-2026-11-06.json).

Les gardes root ouvrent la base du contrôle sous l’identité effective du compte
`spark-docker`, puis retrouvent root pour les signaux et systemd. Lectures,
writers et fermetures suivent ce contexte ; les preuves contrôlent les UID du
WAL/SHM et la restauration de l’identité opérateur. Le registre de stockage
conserve son propriétaire root.

## Console des exécutions

`node e2e/execution-ui.mjs` part de l’accueil et crée ses objets par la console.
Le handler original `qualification/artifacts/observation.cjs` est empaqueté
par l’adaptateur, publié par l’API et invoqué avec un vrai jeton Read. Douze
groupes couvrent six instances sur deux pages, mesures rendues, extinction,
recalage et focus, journaux expurgés/tronqués/HTML texte, mobile, erreurs réseau,
absence de session, suppression, appel actif et démarrage non confirmé.
La panne de métriques tue le seul conteneur de fonction identifié par ses UUID
et labels, pendant une garde SQLite bornée ; le contrôle reprend ensuite ses
ressources. Les attentes de réponse sont jointes immédiatement aux actions UI.
Le nettoyage retrouve les créations par leurs noms exacts même si la navigation
échoue, puis confirme suppression et purge de leurs archives de stockage.

`python3 -B e2e/execution-suite.py --scope console` exécute en série `public`,
`login-ui`, `control-ui`, `execution-ui`, `publication-ui` puis `manual-ui`. Son rapport est
`.local/e2e/console-execution-regressions.json`. Il vérifie la fraîcheur et le
contenu de chaque rapport : fin, nombres de groupes, absence d’échec/skip et
nettoyage selon son schéma. La source et l’image sont recoupées avant/après.
La [preuve initiale des observations](../docs/evidence/console-execution-dev-2026-11-07.json) compte
40 groupes et 25 captures relues. Les mesures Docker partielles sont une donnée
réelle : leur absence doit rester visible, jamais devenir un zéro.

## Manuel intégré

`node e2e/manual-ui.mjs` ouvre le manuel depuis l’accueil réel et sa navigation.
Huit groupes vérifient le contenu intégral (empreinte, chapitres,
paragraphes et tableau), le clavier, le focus, les ancres rechargées, les formats
desktop/tablette/mobile, l’agrandissement mesuré du corps de texte, l’absence de
session et le retour aux namespaces. Les erreurs JavaScript sont contrôlées
après fermeture du navigateur, avant de déclarer le rapport terminé.

La [preuve initiale](../docs/evidence/manual-console-dev-2026-11-07.json) recoupe
48 groupes exécutés en série et 33 captures relues. Le tiroir mobile ouvert
dispose d’une capture visuelle complémentaire prise depuis l’accueil réel ;
elle n’ajoute pas un groupe au total. Les sources du manuel, du build Vite et
du filtre de contexte Docker font partie de l’inventaire avant/après chaque
campagne. Le parseur Markdown n’est pas utilisé par le client de preuve pour
fabriquer son attendu : paragraphes, titres et cellules sont recoupés au document.

## Publication du code dans la console

Depuis la racine, après synchronisation de `publication-state.py` et des helpers
opérateur sur le SPARK, exécuter séparément `node e2e/code-publications.mjs`,
`node e2e/publication-ui.mjs` puis `node e2e/manual-ui.mjs`. Les deux premières
campagnes utilisent `publication-fixtures.mjs` pour empaqueter les handlers
originaux par l’adaptateur ; aucun code applicatif n’est remplacé.

La campagne intermédiaire comportait dix groupes API couvrant droits, versions,
UUID, conservation effective, abandon, conflits, révocation et courses. Ses
quatorze groupes navigateur couvraient
la création depuis la console, les vrais ZIP, import et logs expurgés,
publication A/B et activation A invoquée, historique, pagination, panne réseau,
session absente, rechargement pendant l’upload et retour à une préparation
après interruption de sa réponse. Ce dernier scénario ajoute une latence
Chromium réelle, quitte le document après observation du commit par l’API,
puis retrouve le même UUID sans renvoyer le ZIP. Il ne remplace aucune réponse.

Les campagnes suppriment leurs objets, purgent leurs archives de stockage par
le helper borné et recensent séparément le code conservé. La
[preuve intermédiaire](../docs/evidence/publication-console-checkpoint-dev-2026-11-07.json)
recoupe 32 groupes, 21 captures relues et 109 sources inchangées pendant les
campagnes. La capture nommée `validating` montre encore le libellé de réception ;
la validation est observée par l’API, sans preuve visuelle de ce libellé dans
ce checkpoint. La qualification a été étendue aux scénarios ci-dessous.

Les parcours étendus passent 21 groupes ciblés : réponses perdues d’activation
et suppression, candidat d’une autre fonction, journal long/tronqué et clavier,
validation rendue, nettoyage physique refusé puis repris et confirmation de
stockage en attente. `publication-cleanup-fault.py` vérifie namespace, UUID,
inode et permissions avant son mode 000 ; sa garde indépendante est éprouvée
après SIGKILL et SIGSTOP du seul helper. Le vrai contrôle constate EACCES,
la console reçoit 503 après suppression logique, puis la maintenance reprend.
Le mode commit de `function-storage-faults.py` suspend brièvement l’agent réel
pour qualifier une publication enregistrée dont la confirmation expire ; ce
mode et son inspect exigent l’UUID exact du namespace de publication.

La commande `python3 -B e2e/execution-suite.py --scope publication` réunit les
campagnes moteur et console en série, sans répéter les campagnes communes :
dix-huit campagnes, 312 groupes réussis dans la qualification finale. Son rapport autonome est
`.local/e2e/publication-regressions.json`. Chaque rapport doit être frais,
complet et nettoyé ; sources locales/distantes et image restent identiques.
La [preuve finale](../docs/evidence/publication-console-dev-2026-11-07.json) recoupe
144 sources, l’image déployée, les ressources web servies, les archives conservées
et l’absence de ressources actives de campagne. Les 54 captures sont inspectées.
La lecture du même candidat est cohérente entre liste et suivi ; cinq gestes
constatent un succès réel puis son effacement après une seule consultation.
Les rapports et images antérieurs sont conservés comme checkpoints distincts.

## Effacements corrélés du stockage

Comme root du SPARK DEV, après installation du paquet SLS-064, exécuter
`python3 -B /srv/p2enjoy-serverless/e2e/storage-discard.py`. La campagne utilise
le client embarqué, le socket installé, Docker et les volumes FUSE : reçus,
versions, droits de propriétaire, collisions de préparation, réponse fermée
sans lecture, quotas, fichiers conservés, cache désactivé, purge et tombstone.
Elle exerce les permissions réelles, un verrou SQLite, restart et SIGKILL en
finalizing, et un arbre de 150 000 fichiers pendant l’usage d’autres baux.
Les permissions ont une garde systemd indépendante ; seuls les UUID de la
campagne sont nettoyés. Le rapport storage/discard-proof.json exige fin et
nettoyage vrais, zéro échec/skip. Les douze groupes ciblés et 94 groupes de
régression passent dans la [preuve](../docs/evidence/storage-discard-dev-2026-11-07.json).
Depuis le poste, `python3 -B e2e/execution-suite.py --scope storage` exécute les
sept campagnes en série, avec sources, image et fraîcheur des rapports vérifiées.
