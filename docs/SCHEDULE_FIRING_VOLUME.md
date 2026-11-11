# Borne globale des tirs planifiés

Contrat de preuve de [SLS-078.5](BACKLOG.md#sls-078), selon
[SCHEDULE_RETENTION](SCHEDULE_RETENTION.md#autres-preuves-requises).
Décision du11 novembre2026 avant code. DEV uniquement, campagnes en série,
horloge réelle, aucune date ni ligne métier fabriquée.

## Préparation authentique et conservation

Préparer une sauvegarde d'installation réellement active, puis laisser passer
les fenêtres nécessaires avant son replay. La reprise normale de l'ordonnanceur
consigne les fenêtres manquées en skipped_downtime sans exécuter leurs handlers.
Ces tirs terminaux participent à la même borne10000 que les succès et refus.
Cette voie éprouve la rétention des tirs ; elle ne prétend pas10000 exécutions.

Réutiliser sans changement le mode instance-limit de storage-legacy-environment.py,
garde900s, image immuable du contrôle servi et installation neuve. Les originaux
restent conservés, leur contrôle arrêté, configuration officielle inchangée.
Ce choix évite un arrêt de plusieurs heures de la console habituelle et toute
modification de FORGE. Aucun second contrôle ne consomme le registre original.

Le client `e2e/schedule-firing-volume-capture.mjs` reçoit les identifiants sur
stdin privée et passe par l'accueil SSO, les API publiques HTTPS, la publication
et la promotion réelles. Namespace exact instance-limit-<UUID court>, service
scheduled-firing-history-limit, fonctions firing-retention-01 à16. Chacune porte
16 déclarations activées */5 * * * *, timezone UTC. Les indices distincts des
déclarations sont conservés ; aucune déclaration supplémentaire hors contrat.
Configuration CPU0,05/mémoire128Mio/min0/max1/concurrence1/idle0/deadline60s,
stockage partagé, données/cache désactivés. Réutiliser le handler original
scheduled-capacity.handler, sans nouveau code métier.

Publier tous les pilotes sans les promouvoir, choisir une frontière W avec
au moins90s de marge, puis promouvoir les16 avant W. Une installation neuve
ne doit contenir aucun tir antérieur. À W :256 tirs, dont deux vrais handlers
réussis et254 refused_capacity/schedule_capacity sans invocation ; aucun autre
état accepté. Les refus viennent du plafond2 et des maxima individuels1, pendant
le dispatch synchrone de cette fenêtre. Recouper indices0..15, génération active,
hash, créneau, UUID des deux appels et logs du handler ; attendre zéro instance,
conteneur et bail avant copie. Chaque fonction porte16 tirs, sous la borne.

`e2e/schedule-firing-volume-snapshot.py`, exécuté sur le seul SPARK DEV, est un
lecteur/copieur natif borné. Il vérifie le journal de fenêtre, les identités des
répertoires temporaires, le contrôle original arrêté et la santé de la référence.
Il exige les16 fonctions exactes, générations actives,256 tirs terminaux à W,
deux succès réels, aucun consommateur ni opération en cours. Il sauvegarde
SQLite depuis mode=ro, vérifie l'intégrité et les mêmes témoins dans la copie,
copie les artefacts avec inventaires SHA/taille/mode égaux, sauvegarde le registre
sans bail. Les images contrôle/runtime sont recoupées avec les exports privés
déjà conservés par la capture5056167, sans les modifier ni les réexporter.

Un dossier neuf qualification-history/schedule-firing-volume-<UUID> conserve
ces copies : racine root0700, SQLite et reçus root0400, aucun secret publié.
Écrire le reçu terminé en dernier, vérifier de nouveau les services, fichiers
officiels et témoins. Une interruption laisse un dossier incomplet, sans changer
les sources ; elle ne constitue pas une capture réussie. Pas de reprise automatique.
Ce lecteur ne modifie ni donnée active ni service. Il est lancé par la seule
opération capture-firing-history du pilote existant, qui lui transmet son verrou
hérité, comme aux autres commandes bornées. La garde attend donc sa jonction
avant tout renommage de restitution, même si le pilote meurt pendant la copie.
Alarme native30s, commande timeout40s et lecture client bornée ; aucun lecteur
externe ne poursuit sa copie pendant la restitution. Les options de garde ne
changent pas ; les restitutions historiques font partie de la qualification
de ce raccordement.

Après capture, archiver/purger les16 fonctions par les API, supprimer les parents,
recouper l'absence physique du code, volumes, canaux et consommateurs, puis
restituer les originaux et joindre pilote/gardes. Les copies privées actives
gardent leurs générations non retirées ; la purge réelle ne les réécrit pas.

Quatre groupes distincts : SSO/publications avant W ;256 tirs et deux handlers
authentiques ; sauvegarde native vérifiée/protégée ;16 purges et restitution.
Le rapport conserve les sources/images avant/après, dates et empreintes. Cette
préparation seule ne qualifie ni la borne10000, ni l'âge, ni les pannes du client.

## Premier essai et observation durable

L'[essai27221ea](evidence/schedule-firing-volume-capture-failed-dev-2026-11-11.json)
à06:00UTC a produit deux handlers réussis,172 refus de capacité
et82 tirs failed/execution_unavailable. Les journaux signalent OperationalError
dans les maintenances planification/exécution ; SQLite est intègre et les
fichiers appartiennent au bon propriétaire. L'errno et le site exact ne sont
pas capturés : ne pas attribuer rétrospectivement l'échec à une cause certaine.
Aucune sauvegarde validée ni purge métier n'est retenue. La restitution de
secours conserve registres, artefacts, configuration et référence d'origine.

Le poller capacity ouvrait/fermait des connexions RO successives autour du
dispatch de256 tirs. Appliquer au seul mode instance-limit l'observateur durable
déjà défini par [ADMISSION](ADMISSION.md#observation-durable-des-intentions-par-les-gardes) :
ouvrir après démarrage une connexion CONTROL sous propriétaire, en autocommit,
sans transaction retenue ; réutiliser ses lectures puis la fermer dans finally
avant toute restitution. La garde indépendante n'en dépend pas. Motif : réduire
les courses de fin de connexion pendant l'observation, sans délai SQL modifié,
sans réécriture de registre et sans changer l'admission applicative. Cela reste
un correctif du banc à éprouver, pas une preuve de cause ni une correction SQLite.
Le client doit aussi échouer immédiatement sur un état terminal inattendu en
conservant le relevé, au lieu d'attendre la fin du délai d'observation.

## Capture qualifiée le11 novembre2026

Le [replay31b9102](evidence/schedule-firing-volume-capture-dev-2026-11-11.json)
passe quatre groupes sur340sources figées, même imagec59b8616. À06:15UTC :
256 tirs, deux handlers succeeded et254 refus schedule_capacity sans invocation.
Les256 lignes natives,16 générations actives, deux appels et logs sont recoupés
dans la sauvegarde intègre ; artefacts et exports immuables vérifiés. Le lecteur
confirme son verrou hérité et ses copies protégées. Aucun échec de maintenance
dans le relevé de journal de cette fenêtre ; la cause de l'essai précédent
reste inconnue. Rapport brut intégral conservé en gzip, hors secrets.

Capture privée schedule-firing-volume-5d3595f228964f4e848a8974004e8c0f.
Curseur C=06:15UTC,256 déclarations par fenêtre : éligibilité au premier replay
numérique le11 novembre2026 à09:30UTC, après39 fenêtres réellement écoulées.
Les16 fonctions sont purgées par API, code/volumes/canaux/consommateurs absents,
originaux restitués et pilote/gardes terminés. L'essai27221ea reste échoué et
hors total. Les régressions du helper sont qualifiées ci-dessous ; l’interruption
pendant backup CONTROL est qualifiée dans SCHEDULE_CAPTURE_INTERRUPTION.
La capture ne qualifie pas la rétention,
le futur replay ni les sept jours.

## Restitutions et sûreté qualifiées

La [preuve du helper355453b](evidence/schedule-firing-volume-guard-regressions-dev-2026-11-11.json)
passe20 groupes sur les mêmes340sources que la capture31b9102, sans nouvelle
image :11 pour release/EOF/SIGTERM/SIGKILL/échéance120s et reprise partielle60s,
trois pour les refus de paramètres et le défaut900 réellement programmé/restitué,
six pour perte avec consommateur actif, diagnostic Docker indisponible et refus
du namespace étranger. Les trois derniers cas passent aussi par un vrai SSO.
Le journal natif partiel confirme60s et le même SHA de helper figé.

Les connexions d'observation ne retiennent aucune transaction ; les pilotes et
gardes sont joints, les originaux restitués à chaque fenêtre. Le retrait des
consommateurs après perte ne vaut pas purge métier. Les quatre groupes de
capture gardent leurs16 purges publiques distinctes :24 groupes de cette étape,
sans addition des sous-assertions ni de l'essai initial échoué. Le replay
numérique est qualifié séparément ci-dessous ; les sept jours restent ouverts. La copie interrompue est
qualifiée séparément ci-dessous. Aucune campagne complète de plateforme revendiquée.

## Éligibilité et protocole de replay

Relever dans la sauvegarde le curseur réel C=W et le nombre initial T0=256.
Avec256 déclarations actives par fenêtre, calculer
N=floor((10000-T0)/256)+1=39. Le premier redémarrage utile doit avoir sa frontière
réelle D>=C+39*300, soit3h15 après C. Ce délai est mesuré sur l'horloge du SPARK,
jamais remplacé par une date injectée. Les témoins restent âgés de moins de sept
jours pour isoler la borne numérique. Chaque fonction reste sous10000 tirs.

Le pilote de replay décrit ci-dessous doit être qualifié avant son usage :
fenêtre gardée exclusive, données/registre/artefacts copiés avant démarrage de
l'image capturée, originaux conservés et aucun consommateur original partagé.
Ne pas réutiliser une seconde base avec le registre actif de la plateforme.

La preuve devra observer toutes les lignes d'un lot de récupération terminé
avant sa suppression numérique, puis exactement les10000 plus récentes par
completed_at DESC,id DESC au même curseur. L'ordonnanceur traite au plus20
fenêtres par passage ; un relevé au milieu d'un lot ne suffit pas. Recouper
fenêtres, générations/indices, absence de nouvelles invocations, dates authentiques,
portée globale et absence de rejeu. Le mécanisme d'observation natif et ses pannes
restent à qualifier ; aucun succès n'est déduit de ce plan ou de la capture.

## Chargement gardé de la copie

Décision du11 novembre2026 avant code. Étendre uniquement le mode instance-limit
avec la paire explicite --firing-history=schedule-firing-volume-<32hex> et
--firing-observation=preflight|count|seed-loss|observer-loss. Refuser toute option
isolée, ambiguë, inconnue, hors mode ou identifiant non canonique avant création
de fenêtre. Tous les modes de replay exigent la garde120 explicite.
Le client est e2e/schedule-firing-volume-replay.mjs ; le module opérateur natif
est e2e/schedule_firing_volume_replay.py. Ce sont des outils DEV, sans réglage
supplémentaire du moteur applicatif, du runtime, du SSO ou de FORGE.

Avant tout arrêt, vérifier le reçu public de capture, sa copie privée terminée,
les propriétaires/modes root0700/root0400, chemins canoniques et absence de liens,
SHA/intégrité des deux SQLite fermées, témoins256/16/2 exacts, inventaire des
artefacts et exports d'images immuables. Les bases scellées sont ouvertes RO
immutable, sans créer de sidecar ; aucun fichier source n'est modifié. Vérifier
registre sans bail, probe, volume monté ou intention pendante. L'image contrôle
doit être celle capturée et celle servie ; le runtime doit correspondre au reçu.
Un prérequis absent échoue ; aucune substitution d'image ni capture fabriquée.

Le journal de la nouvelle fenêtre lie namespace_name et temporary_installation
aux témoins capturés, différents de l'installation originale, avant toute copie.
Après renommage des trois originaux et installation des trois remplacements
déjà journalisés, copier les artefacts puis le registre puis CONTROL. Les deux
SQLite passent par fichier temporaire, fsync et rename atomique ; CONTROL est
publié en dernier, complet et sous propriétaire spark-docker0600. Les sources
restent scellées. Aucune donnée métier, date, génération ou UUID n'est réécrit.
Les commandes de copie héritent du verrou et sont bornées40s.

Motif de cet ordre : avant publication CONTROL, la restitution existante peut
lire le registre sans références sous le propriétaire de original-state ; après
publication, la base entière permet le contrôle d'appartenance. Aucun remplacement
inutilisé n'est peuplé et aucune base tronquée n'est exposée. Ouvrir la connexion
RO durable après copie complète, avant démarrage de l'agent et du contrôle ; la
fermer/détacher avant restitution comme pour les fenêtres déjà qualifiées.

## Observation du replay et preuves propres

D est la frontière réelle du démarrage. Armer entre D+10 et D+120 ; la garde120
indépendante retire ainsi la copie avant D+300 même si le client reste bloqué
pendant SSO ou les lectures. Le défaut900 des autres usages reste inchangé.
Motif : empêcher les générations actives de lancer le créneau suivant pendant
un pilote bloqué ; une simple vérification d'horloge dans le client ne suffit pas.
Après armement, relever ActiveEnterTimestampMonotonic du timer et le recouper
avec les horloges monotone/réelle du SPARK. Persister l'instant d'activation et
sa frontière dans le journal. Refuser tout démarrage si l'activation est hors
D+10..D+120, si la frontière a changé ou si la marge D+150 est dépassée. Ces
contrôles se font dans le try/finally de restitution, après les précontrôles,
avant l'arrêt des originaux ; un contrôle tardif n'autorise aucune copie servie.
Démarrer dans cette première partie de fenêtre, garder une marge avant D+300
et échouer si le créneau suivant est atteint :
aucun nouveau handler ne doit être lancé. La préflight exige1 à38 fenêtres manquées
et un total encore inférieur à10000 ; count exige au moins39 fenêtres manquées.
Les témoins doivent rester plus jeunes que sept jours. Un refus d'éligibilité
est vérifié séparément avant cette date ; il ne devient pas un succès numérique.

Armer NativeObserver sur le Python uvicorn unique descendant du PID init Docker,
même cgroup, avec sa naissance vérifiée, avant l'attente
healthy. Une attache tardive ne donne aucun succès : elle fait échouer le cas.
Le traceur ne change aucun registre, tampon ou retour système. Limiter les
lectures SQL aux frontières natives utiles, avec connexion RO/autocommit ; les
syscalls ne valent jamais preuve seuls, seuls les prédicats SQL observés décident.
Le pilote attend les stops avec waitpid bloquant réel, sans pause ajoutée par
syscall ; la bibliothèque partagée n'est pas modifiée. Délais d'observation25s,
alarme native35s et commande40s conservés. Avant la fin du lot, éviter les
lectures SQL sur chaque fermeture de fichier de l'import Python ; consulter les
sync, puis les fermetures proches du curseur attendu. Aucun résultat système
n'est substitué et aucun état SQL n'est fabriqué.
Après le lot critique complet, observer les lignes encore visibles en lecture
commise avant la suppression commise, puis les10000 UUID exacts au même curseur.
Les fdatasync et fermetures de descripteurs servent de points d'observation ;
si la frontière n'est pas observable, conserver l'échec sans relance automatique.

Pour count, le premier lot qui franchit la borne finit après
min(D-C,40*300) secondes de curseur. Vérifier toutes ses fenêtres,256 déclarations
par fenêtre, les256 témoins initiaux inchangés, tous les nouveaux tirs en
skipped_downtime et exactement les deux invocations initiales. Recalculer les
survivants depuis completed_at DESC,id DESC et comparer aux UUID réellement
relus après commit. Chaque fonction reste individuellement sous10000. Conserver
les vecteurs complets et leur rapport brut compressé, pas seulement des compteurs.

Après détachement, attendre santé et fin de récupération au curseur D ; nouvelle
connexion SSO depuis l'accueil, lectures API paginées des16 fonctions recoupées
avec le relevé natif. Puis restitution des originaux, jonction des processus/
gardes et nouvelle vérification des sources scellées. Trois groupes nominaux :
chargement/observation native ; SSO/lectures réelles sans handler nouveau ;
restitution/source inchangée. Le préflight ne qualifie pas la borne numérique.

Qualifier séparément les refus d'options/source avant mutation, le refus count
avant39 fenêtres, la perte après publication du registre mais avant CONTROL et
la perte après attache réelle de l'observateur. Ces deux pertes tuent réellement
le pilote et le mutateur, gardent un reçu privé du point atteint, puis exigent
la restitution indépendante120s et la source inchangée ; elles ne sont ni
purges métier ni succès de handler. Timeout40s et verrou hérité imposent la
jonction du mutateur avant restauration. Les nouveaux cas et les régressions
historiques doivent passer avant de qualifier le pilote ; SLS-078 reste ouverte.

## Chargement et pertes qualifiés

Le [replaye53b0d9](evidence/schedule-firing-replay-preflight-dev-2026-11-11.json)
passe neuf groupes sur342sources figées, mêmes imagesc59b8616/1e64b4af : huit
refus de paramètres/source, refus count avant éligibilité, préflight nominal et
deux pertes réelles. Les refus ne créent aucune fenêtre. À07:45UTC,18 fenêtres
réellement manquées donnent4864 tirs ; observation4,46s sous la borne25s,
deux invocations initiales seules. Nouveau SSO puis64 pages API exhaustives
recoupées ; source scellée identique après restitution.

Les pertes après registre/avant CONTROL et après attache au Python tuent
réellement pilote et mutateur ; garde120 indépendante, sources conservées,
originaux restitués, processus et unités joints. Aucune nouvelle fonction,
invocation ou purge métier revendiquée dans ce replay. Le rapport brut complet
est lié en gzip ; trois essais échoués sont conservés et exclus des neuf groupes.

Le mode count et ses deux frontières au-delà10000 sont qualifiés séparément ci-dessous.
Les neuf groupes ne prouvent pas la rétention numérique ; les
régressions historiques du helper courant sont qualifiées séparément ci-dessous.

## Régressions historiques du pilote qualifiées

La [preuve342sources](evidence/schedule-firing-replay-guard-regressions-dev-2026-11-11.json)
passe20 groupes distincts :11 reprises release/EOF/SIGTERM/SIGKILL/échéance120s
et partielle60s, trois options/refus/défaut900 et six consommateur actif/diagnostic
indisponible/namespace étranger. Le helper figé et les342sources sont identiques
à l'époque des neuf groupes propres ; images conservées et originaux restitués
à chaque fenêtre, pilotes et gardes joints. Le reçu natif partiel confirme60s.

Soit29 groupes de l'étape, sans recomptage des assertions ou des essais échoués.
Le mode count après39 fenêtres est qualifié ci-dessous ; les sept jours restent ouverts ;
l’interruption du copieur initial est qualifiée séparément ci-dessous.
Aucune campagne complète de plateforme revendiquée.


## Interruption de la capture initiale qualifiée

La [preuve propre](evidence/schedule-capture-interruption-dev-2026-11-11.json)
passe cinq groupes sur342sources dbb840b : vraie fenêtre08:50UTC, capture normale,
perte pendant backup natif puis garde bloquée2,043s et restitution indépendante
après SIGKILL/jonction. Le [contrat détaillé](SCHEDULE_CAPTURE_INTERRUPTION.md#frontière-de-copie-qualifiée)
distingue la correction du groupe timeout orphelin et l'essai c5fcb1d échoué.
Captures canonique et nominale conservées, sortie partielle protégée ; aucun
nouveau résultat de rétention. Les [vingt régressions](evidence/schedule-capture-guard-regressions-dev-2026-11-11.json) passent sur les mêmes342sources.


## Rejeu sous borne sur deux lots qualifié

La [preuve e23e820](evidence/schedule-firing-replay-two-batches-dev-2026-11-11.json)
passe trois groupes sur342sources et les mêmes images :36 fenêtres manquées
au démarrage09:15UTC,9472 tirs au curseur final et toujours les deux invocations
initiales. La limite20 fenêtres par passage impose ici deux lots de récupération.
L'observation native termine en9,938675s sous25s ;37 fenêtres complètes de256 tirs,
592 par fonction. Nouveau SSO,96 pages API exhaustives et restitution nominale
jointe ; source scellée et fichiers officiels inchangés. Ce complément exerce
la récupération au-delà d'un lot, sans résultat de rétention numérique. Le
franchissement est qualifié ci-dessous ; les preuves d'âge restent ouvertes.

## Franchissement réel de la borne qualifié

La [preuve ef8cb3f](evidence/schedule-firing-retention-count-dev-2026-11-11.json)
passe trois groupes sur342sources identiques avant/après, mêmes images :39 fenêtres
réellement manquées entre C06:15UTC et D09:30UTC. Le relevé commis avant rétention
contient10240 tirs/40 fenêtres de256 ; le suivant, au même curseur, conserve
exactement les10000 UUID les plus récents selon completed_at DESC,id DESC.
Les240 plus anciens sont exactement retirés. Chacune des16 fonctions avait640
tirs avant rétention ; aucune n'atteint individuellement10000.

Les9984 skipped_downtime restent ; les254 refus initiaux deviennent14, les deux
succès initiaux restent. Les deux invocations et leurs générations sont inchangées,
aucun nouveau handler n'est exécuté. L'observation native dure10,822922s sous25s.
Après nouveau SSO depuis l'accueil,112 pages API concordent intégralement avec
les10000 lignes natives. Restitution nominale jointe, originaux et source scellée
conservés ; vecteurs complets dans le brut compressé lié à la preuve. Les captures,
préflights et essais échoués gardent leurs époques et leur comptage distincts.

Cette preuve qualifie la borne globale des tirs. Elle ne qualifie pas la source
d'invocation protégée sous borne, les sept jours ni la campagne complète ;
SLS-078.5 et SLS-078 restent ouverts.
