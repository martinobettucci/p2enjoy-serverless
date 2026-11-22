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
