# Régressions courantes après migration011

Contrat de SLS-072.6 et SLS-132.5, complément de EXECUTION_LOGS et
SCHEDULE_REGRESSIONS. Inventaire avant adaptation : les options --target-schema011 des trois wrappers
sont implémentées, mais leur qualification courante reste à exécuter. Les anciens résultats
restent leurs époques et aucune réussite n'est déduite de cette liste.

## Périmètre décidé

Exécuter les49campagnes/543groupes/18prérequis du scope schedules, puis32commandes
courantes supplémentaires/276groupes propres. Les25communs sont inclus dans543 ;
les12API/10UI du journal sont22autres groupes. Ce passage de régression ne
recompte ni les préparations, ni les répétitions diagnostiques, ni les anciennes
preuves de rétention. Les nouveaux replays de rétention132 gardent leur bilan
propre, dont aucun groupe n'est ajouté au socle par son simple rattachement.

P = SSO username/password sur stdin privée puis mémoire seulement. S = nouvelle
préparation réelle dev-sso-sessions avant chaque commande, fichiers privés des
seuls cookies plateforme ; reçu SSO archivé, jamais cookies/CSRF dans le bilan.
N = commande native sur le seulSPARKDEV. Les deux variantes Docker deCLI
constituent chacune une commande5, distincte des24/14du socleadaptateurDocker.

| Client ou commande | Groupes | Auth |
| --- | ---: | --- |
| code-draft-capacity.mjs |17|P|
| code-editor.mjs |20|P|
| code-editor-ui.mjs |18|P|
| code-editor-source-limits.mjs |13|P|
| code-editor-source-access.mjs |7|P|
| code-editor-source-lifecycle.mjs |5|P|
| code-editor-read-concurrency.mjs |9|P|
| code-editor-build-capacity.mjs |4|P|
| code-editor-ui-concurrency.mjs |11|P|
| code-editor-publication-continuity.mjs |7|P|
| code-editor-control-interruption.mjs |4|P|
| code-editor-archive-boundaries.mjs |7|P|
| function-http-client.mjs |18|P|
| function-http-client-ui.mjs |16|P|
| function-http-client-admission.mjs |5|P|
| function-http-client-confidentiality.mjs |10|P|
| function-http-client-loading.mjs IMAGE_COURANTE |5|P|
| function-http-client-recovery.mjs |7|P|
| function-http-client-source-access.mjs IMAGE_COURANTE |7|P|
| function-http-client-task-exception.mjs IMAGE_COURANTE |6|P|
| function-http-client-token-loss.mjs |7|P|
| control/code-hash-dev.sh test |7|N|
| function-version-state-transport-run.py --target-schema011 |9|P|
| function-version-validation.mjs |4|S|
| function-version-upload-capacity-run.py --target-schema011 |4|S|
| function-version-duplicate-recovery-run.py --target-schema011 |4|S|
| function-versions-api.mjs |12|S|
| function-versions-ui.mjs |6|S|
| function-versions-cli.mjs |5|S|
| function-versions-cli.mjs --docker cli |5|S|
| function-versions-cli.mjs --docker qualification |5|S|
| managed-invocation-watch.py |12|N|

Sommes : éditeur12/122, testeur9/81, hash/versions10/61, surveillance1/12,
soit32/276 (22P,8S,2N). Chaque groupe doit passer, sansskip, toutes assertions
positives/refus/limites/nettoyage conservées. Les900s du jeton testeur et les
coupures/réservations réelles ne sont ni accélérées ni remplacées.

## Préconditions et historique

Les clients de contrôle courant exigent exactement001→011, jamais une simple
longueur, >=010 ou une liste permissive. Les pins d'image courante sont fournis
ou recoupés contre l'image réellement servie, y compris opérateurs figés,
restaurateurs, programmes d'arrêt et générateur des ZIP. Une seule assertion
cliente actualisée ne suffit pas. Le code produit et les anciens manifestes
ne sont pas modifiés pour faire accepter ces préconditions.

Les sources historiques003/006/007/008/009 restent exactes. Le modehistorical
courant (miseàniveau003 vers imageactuelle) vérifie sa nouvelle cible011 sans
changer sa source003. Les voies de migration versions006→007,007→008 et purge
006/007→008 gardent leurs options, images, oracles et rapports historiques.

Ne pas exécuter comme commandes courantes : function-version-registry (006→007),
registry-ui (oracle007 de doublon et appel nonpromu), unknown-first (006→007→008),
function-versions-upgrade (007→008), purge-upgrade/migration008. Les parcours
actuels de registry-ui ont leurs descendants dans versions-ui ; ils ne sont
pas simplement supprimés. Les trois wrappers de régression publication/CLI/
invocation-stockage recouvrent respectivement76/11/46groupes du socle et ne
s'ajoutent pas une secondefois. Navigation-observation et page-closure restent
diagnostics0, sans faux groupes de réussite.

Les trois wrappers versions ci-dessus reçoivent une **branche explicite011** ;
absence d'argument conserve008 et ses anciens recoupements. La branchecourante
exige onze migrations nommées, codeembarqué réel égal aux sources et baseline
courante gelée, mêmeCID/image et référence/config conservées. State-transport
ne compare plus le passage011 au CID/image/web de la preuve008 ; il conserve
les7gardes,6coupures137,16invocations, reçus et détails d'absence de rejeu.
Upload/duplicate conservent leurs recoupements actuels de ce passage,4/5appels,
1purge chacun, et les2gardes propres au doublon.

## Exécution, preuves et clôture

Un seulcas à lafois, sur sources committées/synchronisées et image immuable
identifiée. Archive exacte des rapports antérieurs **avant** tout remplacement ;
les wrappers exigeant rapport/checkpoint absents utilisent ensuite un espace
neuf explicitement préparé, sans effacer une preuve. Les trois checkpoints
natifs restent liés à leurs rapportsNode ; aucun des deux ne remplace l'autre.
RapportsUUID découverts par différence exacte avant/après sur le préfixe de
leur seulclient, exactement un nouveau fichier. Code nonnul demeure rouge
même si JSONcompleted ; champs d'erreur et captures sont traités selon leur
schéma réel explicite, jamais par omission tolérante.

Avant/après chaquecas : repos natif, onze migrations/intégrité/FK, configuration,
budgets, référence et5982artefacts originaux. Recouper tousUUIDpossédés et leur
purgephysique ; les installations isolées restent identifiées séparément et
leurs originaux/gardes/consommateurs joints. Les redémarrages prévus changent
StartedAt, jamaisCID/image ; référence entièrement inchangée. ChaqueJPEG/PNG
fresh est conservée avecSHA puis ouverte individuellement avant qualification.
Aucune imagehistorique substituée à un nouveau parcours ; limites visuelles
nommées séparément des assertions DOM/HTTP/natives.

Le lancement long reste oneshot et sansrejeu automatique, avec credentials en
mémoire, fenêtre locale bornée et finalisation seulement après résultat terminal
systemd, MainPID0 et jonction réelle du client. Une preuve manquante laisse072
et132ouverts. Toute divergence nouvelle devient unité avant correction.


## Formats explicites des rapports supplémentaires

21rapportsUUID canonique36 : les12éditeurs et9testeurs ;11rapportsfixes pour
les10commandes hash/versions et lewatch. Tous portent checks{name,status},
skipped0. Parmi les21UUID, seulcode-editor-ui a cleanup ; les20autres n'ont
volontairement pas cechamp. Exiger pour chacun son schéma réel, completed et
cleanup_errors[], puis le recoupementphysique, sans inventer cleanup=true.
Les4éditeursvisuels exigent aussi faults[]. Les21 portent failure:null et
namespace_id/function_ids, jamais namespace_ids.

Les9testeurs publient captures[clé_logique]={path_absolu,sha256,bytes,viewport}.
L'archive valide le chemin réel sous .local/e2e, sonbasename/type/absence de
symlink, taille etSHA ; la clélogique ne devient pas unnom de fichier. Les
4éditeursvisuels etversions-ui utilisent basename→{sha256,viewport,full_page}.
Versions-ui réutilise ses nomsJPEG fixes : archive avant le prochainpassage.
LesUUID ne nécessitent aucuncheckpoint supplémentaire au nomdeviné.

Lesversions ont cleanup et cleanup_errors ; validation/upload/duplicate ont
aussi request_join_errors[] etversions-ui faults[]. State-transport n'a pas
de failure au premierniveau : refuser ses groupeséchoués et son entrée
campaign-error dans evidence. State/versions-ui ont function_id singulier,
lesautresversions function_ids. LaCLIhôte peut omettre imageCLI ; l'image du
contrôle est liée par les snapshots. Ses troisvariants exigent execution égal
àhost-python/docker-cli/docker-qualification respectivement.

Code-hash n'a aucunUUID API fonction/namespace : conserver installation et
son propre nettoyageDocker/canaux/répertoire. Managed-watch porte installation_id
et functions, sansnamespace ; conserver son résultatparent, workerjoint,
scriptretiré et transportsstdout/stderr souschemins privés avec SHA/octets.
Ces deuxcas gardent leurs nettoyagesnatifs ; ne pas fabriquer de mapping API.
Le repos global original est ensuite exigé pourtous. Les troiswrappers versions
gardent checkpoints/logs/recoupements propres en plus du rapportNode, avec
assertions de fraîcheur pour les deuxniveaux et archive préalable des anciens.


## Propriété courante et lancement dédié

Les30commandes API possèdent30namespaces et74fonctions nominales distinctes :
51éditeur,14testeur et9versions. Le manifeste partagé
`e2e/additional_regressions_contract.py` décrit les formats et cardinalités exacts
lus dans les clients. Pour27commandes, reconstruire le nom depuiscampaign UUID36
ou prefix complet ; les suffixes16 sont des UUIDtronqués avec tirets, jamais
16hex. Les cinq éditeurs réutilisant code-editor-read-concurrency conservent
ce nom réel. Les troisCLI sauvegardent désormais namespace_name de la vraie
réponsePOST, lié à namespace_id, pour permettre la comparaison indépendante.

L'inspecteur natif reçoit son mappingUUID habituel puis l'option explicite
`--additional-client CLIENT --namespace-name NOM`. Un seul namespace est accepté,
avec format et cardinalité du client, nom natif strictement égal et inventaire
complet identique. Toutes les assertions de purge/secrets/reçus/consommateurs
restent exigées. Sans ces options, la garde historique reste inchangée.
Aucun nom libre, booléen de propriété ou simple total74 ne remplace ce lien.

`python3 -B e2e/additional-regressions-suite.py` exécute le manifeste complet
32/276, huitprérequisSSO, sans sélectionpartielle ni rejeuautomatique. Pour une
exécution durable : `python3 -B e2e/additional-regressions-worker.py start`, puis
`status NOM` et `finish NOM`. Le worker reprend les bornesoneshot21600s/60s,
credentials surstdin puismémoire, résultatterminal et vraiejonction du client.
La présence de ces commandes ne constitue pas leur qualification : aucunbilan
complet ne passe avant les32résultats réellement acquis et captures inspectées.

Les anciens rapports/checkpoints/logs, y compris les couplespartiels, sont
archivés puis seuls les cheminsconnus recoupés sont déplacés. Les images de
résultat portent unmtime entre lancement et terminaison de leur cas ; leur SHA
et taille applicable sont vérifiés. Tous les testeurs déclarent captures, mais
admission n'exige pas d'imagepositive : ses images sont seulement diagnostiques
lors d'une panne. Aucun fichierhistorique ne remplace une capture fraîche.


L’exécuteur courant après optimisation133 est strictement f016a1b7 (SHAcomplet
dans RETENTION_SCHEMA_011, section Exécuteur courant après optimisation133).
Les huit pins d’éditeur/fixtures suivent cette image réellement construite et
déployée. Les baselines des profils de bascule et des diagnostics historiques
ne changent pas. La garde courante lie les trois nouvelles preuves nommées et
les quatre modules de rétention ; une preuve manquante reste un refus.

## Finalisations des collectes courantes

Les programmes auxiliaires gardent la première exception jusqu’à la fin de
leurs tentatives de restitution, jointure, conservation des flux et sauvegarde.
Une erreur de finalisation ne remplace pas cette primaire ; ses métadonnées
expurgées sont conservées séparément. Sans primaire, la première erreur de
finalisation entraîne une sortie en échec. Un retour nonnul du client observé
reste nonnul. Le moniteur143 ne soumet aucune requête métier et compte zéro groupe.

Le scellement49 exige les six essais courants incomplets distincts, y compris
celui de146, exclus du total. Le lancement32 épingle réellement espacePID du
lecteur et du worker vivant, boot et identités ; une absence ultérieure n’est
interprétée que dans ce contexte vérifié. Manifeste et gzip49 sont déjà dans le
commit de lancement32 ; tous les SHA du vecteur de sources restent strictement
identiques entre ces deux passages, avec sa cardinalité explicite au gel.


## Préparation des workers — SLS-147

Le premier32 sur530sources échoue faute de clone observé, après80groupes.
Le contrat de préparation est dans CODE_EDITOR_READ_CONCURRENCY, section
Préparation explicite du contrôle courant. La préparation réelle est placée
immédiatement avant code-editor-read-concurrency, après repos vérifié des six
précédents, puis une nouvelle baseline lie la génération de contrôle à ce client.
Son reçu est archivé séparément des32commandes et des huitprérequisSSO ; il
ne produit aucun groupe. MêmeCID/image, référence/configuration/budgets/données
conservés, arrêt/naissance nouveaux explicites. Aucun retry du scénario.

Le préparateur maintenu portait l'index à531sources pour le ciblé nominal.
Son contrôleur de fautes maintenu porte le prochain gel à532sources. Le contrat et les clients modifiés ne sont pas attribués au
49cd01985/530. Après le ciblé9 et ses25communs frais, un nouveau49complet sur
le nouveau gel précède le prochain32 ; mêmes sources entre ces deux passages,
preuve49 committée avant lancement32. Les anciensmanifestes restent inchangés.

## Négatifs des finalisations du moniteur — SLS-143.5

Décision après147.3, avant code : éprouver les deux vrais programmes de
moniteur/contrôleur sur trois passages ciblés réels, puis leur nominal dans
le prochain49. Les copies privées530 déjà exécutées restent immuables. Les
nouvelles copies décrivent leur responsabilité, leur source et leurs paramètres ;
elles sont conservées exactement avec les preuves, comme les programmes de
collecte actuels. Aucun faux worker, rapport, run_id, acquisition ou retour.

Le worker maintenu accepte `start --scope storage-console-focused`, en plus
de `start` qui conserve schedules. Le ciblé emploie les sept commandes déjà
existantes, leurs37groupes, les quatre prérequis réels (SSO, build historique,
SSO décision et inspection physique) et tous leurs oracles. La suite produit
ses propres archives, run_id, source_commit, baseline et dates de cas, comme
le scope schedules. La sélection49/543/18 et ses exigences restent inchangées.
Chaque passage ciblé reste distinct du49 et du32, sans addition aux819 uniques.

Le lancement ciblé porte un dossier `storage-console-worker-<uuid>` et une
unité `serverless-storage-console-regressions-<uuid>`. Scope et chemin de
rapport viennent d'une table fermée, sont inscrits au vrai launch puis relus
par status/finish ; aucun chemin libre ni autre profil. Les anciens dossiers
schedules-worker restent lisibles avec leur scope schedules historique. Les
bornes21600/60, identités/cgroups, résultat terminal et jonction restent exigés.
Le ciblé ne devient pascompleted sur la seule fin d'un processus auxiliaire.

La nouvelle copie du moniteur lie scope/rapport, vecteur exact et cardinalité
du lancement, namespacePID/boot, naissance du worker et cgroup du vrai Node.
Pour schedules, l'admission reste pendant storage-preparations. Pour focused,
elle accepte le vrai état avant storage-console-api ou ce cas encore vivant ;
un cas déjà terminé reste refusé. Commande canonique, image f016, fenêtre900s
d'attente, trace90s, réponse80s et SQL/consumer corrélés restent inchangés.

Le rapport initial est ouvert une seule fois et sa fraîcheur est vérifiée par
fstat sur ce même FD : mtime au moins égal à la création du lancement, octets
et SHA conservés avec run_id. Un ancien focused au même commit ne peut servir
de contexte au nouveau worker, même avec commands vide. Les lectures suivantes
conservent cette borne et ce run_id ; une absence ou une divergence reste refusée.

La portée ciblée est retenue plutôt que six replays49 : elle exerce les mêmes
parcours avec de vrais marqueurs, et laisse finir chaque campagne et son cleanup.

Pour les fautes avant armement, une barrière locale épingle uniquement son
propre moniteur par UID/parent/naissance/namespace/pidfd. Après le premier
affichage initial réellement réussi, elle observe l'entrée du premier read
du rapport de suite dans current(), donc à l'intérieur du try protégé et
avant traitement du marqueur. Les métadonnées du syscall et du FD sont lues,
jamais les buffers/mémoires/registres modifiés. Le FD régulier doit désigner
le chemin de rapport exact, éventuellement remplacé atomiquement ; la lecture
bornée du fichier réellement ouvert recoupe run_id/source/scope du vraiworker.
Un autre inode/rapport ou une observation manquante échoue. Cette barrière
ne suspend ni worker de suite, ni Node, ni contrôle/agent du SPARK.

Six diagnostics réels, en série dans leurs passages possédés :

1. Moniteur avec primaire : après son affichage initial et à ce read protégé,
   occuper son seul checkpoint.pending par un répertoire vide possédé, fermer
   le lecteur de stdout, puis livrer son vrai SIGTERM. InterruptedError reste
   primaire ; save/IsADirectoryError21 puis print/BrokenPipeError32 restent
   secondaires exactes. Aucun appel natif n'a encore été armé.
2. Contrôleur avec primaire : son moniteur est retenu au même read ; son seul
   observer.stdout passe0600→0000 par FD conservé et son result.pending est
   occupé par un répertoire possédé. Fermer le lecteur stdout du contrôleur
   après son affichage initial, puis SIGINT du contrôleur. KeyboardInterrupt
   reste primaire ; terminate/join réels du fils, retain_stdout/PermissionError13,
   save/IsADirectoryError21 et print/BrokenPipeError32 restent secondaires.
   Livrer le SIGTERM réel du parent au moniteur retenu, sans le remplacer.
3. Contrôleur sans primaire propre : même EACCES sur observer.stdout, puis
   SIGTERM réel du seul moniteur, sans signaler le contrôleur. Le retour nonnul
   du fils est conservé et retain_stdout/PermissionError13 est la première
   erreur du contrôleur. Ne pas confondre l'absence de primaire du parent et
   l'InterruptedError attendu du fils.
4. Contrôleur avec restitution longue : arrêter son moniteur au read protégé,
   livrer SIGSTOP et détacher en exigeant T/TracerPid0 ; SIGINT du contrôleur.
   Son terminate laisse le fils arrêté ; attendre les110s réelles avant kill,
   puis jointure bornée10s. KeyboardInterrupt et vrai retour du fils restent
   conservés. Ce timeout de secours n'est pas une secondaire du programme.
5. Moniteur avec finish refusé : dans un passage canonique distinct, après
   armement natif confirmé, créer seulement la collision privée
   native-agent-trace-finish-transport.json, puis SIGTERM du moniteur. Son
   vrai finish arrête d'abord la trace distante et échoue sur son assertion
   de non-écrasement locale ; InterruptedError reste primaire et
   native_trace_finish/AssertionError la secondaire. Le fichier collision
   est retiré après jointure, sans écraser un reçu. Lire indépendamment
   finished.json/unité/naissance/cgroup/agent identique et TracerPid0.
6. Moniteur sans primaire : dans un autre passage canonique distinct, fermer
   son lecteur stdout après l'affichage initial et laisser l'observation
   complète finir normalement. print/BrokenPipeError32 est sa première
   secondaire, le retour final reste nonnul même si checkpointcompletedtrue.

Les diagnostics1–4 utilisent un premier passage ciblé ; le long reste dernier.
Les diagnostics5 et6 utilisent chacun leur propre passage ciblé complet.
Une observation non atteinte reste un refus, sans relance automatique. Les
programmes finissent et leurs ressources sont recoupées avant passage suivant.
Une sortie120 de flush Python est conservée telle quelle, sans conversion
en0 ni assimilation à une autre primaire. Les stderr diagnostiques terminaux
et les reçus intermédiaires sont distingués. Les erreurs de rétention éprouvent
la vraie lecture préalable au SHA, sans prétendre altérer SHA256 lui-même.

Chaque lancement est lié au code committé, aux sources réellement livrées et
à ses programmes figés. Propriété/inodes/naissances sont vérifiés avant faute ;
SIGSTOP se livre au signal-delivery-stop avant detach, les autres signaux
sont préservés. Sur erreur, restituer d'abord toute trace locale, puis joindre
les processus possédés, restaurer les permissions via FD et retirer seulement
les répertoires/fichiers collisions exacts. Conserver première exception et
chaque secondaire ; aucune restitution de secours ne devient une jointure
réussie du programme testé. Ne pas réécrire un programme déjà exécuté.

La preuve retient les six codes nonnuls attendus, leurs primaires/secondaires,
flux réels sous taille/SHA, délais et identités, contrôle natif repos/config/
référence/5982, purges physiques des vrais sept cas et tous les originaux UI
de chaque passage, inspectés individuellement. Les diagnostics ajoutent0groupe.
Les trois ciblés complets gardent leurs propres37groupes chacun ; aucune
préparation ni répétition n'est ajoutée au543. Nouveau49 nominal puis32 sur
le même vecteur restent requis ; aucune réussite déduite de cette spécification.
