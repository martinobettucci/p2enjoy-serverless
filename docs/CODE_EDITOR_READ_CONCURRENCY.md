# Lectures vivantes et concurrence de l’éditeur

Ensemble 3 de [SLS-070](BACKLOG.md#sls-070), après les preuves de
[sources et limites](CODE_EDITOR_SOURCE_LIMITS.md) et de
[console](CODE_EDITOR_CONSOLE_EXTENSIONS.md). Décision du 12 novembre 2026,
avant le client de preuve et son observateur. Le contrat produit demeure
[CONSOLE_EDITOR](CONSOLE_EDITOR.md).

## Résultats à établir

Une lecture de source réellement engagée retient sa capacité et ses fichiers
jusqu’à jonction de son travail. Pendant cette lecture, la boucle HTTP continue
à traiter les requêtes autorisées. Quatre lectures sont admises ; une cinquième
renvoie 429 et Retry-After avant toute lecture de fichier. Après libération,
les réponses et la capacité reviennent normalement.

Une révocation commise pendant l’IO doit être relue avant la réponse : une
lecture technique déjà engagée ne donne plus le code au jeton révoqué. La purge
confirmée d’une fonction retire son accès et ses brouillons, puis attend la fin
du lecteur avant l’effacement physique de ses artefacts. Les nouvelles lectures
restent refusées. La trace native et les états API/SQLite doivent distinguer
ces étapes ; un simple délai arbitraire ne constitue pas une preuve.

La reconstruction unique du ZIP, les bornes ZIP 64 Mio / extrait 256 Mio /
20 000 entrées et répertoires, et les scénarios de publication interrompue
restent exigés par l’ensemble 3 et l’ensemble 4. La barrière décrite ici constitue
leur instrumentation réutilisable ; sa qualification seule ne les clôture pas.

## Barrière native retenue

Le client publie par les API un paquet original contenant `reader-gate.txt` et
un handler du dépôt qui en lit réellement les octets dans Docker. Le namespace
et le service portent le même UUID de campagne dans leur description ; le
nom de la fonction décrit son usage. La base, l’inventaire et le fichier sont
rapprochés avant tout attachement. Seul le SPARK DEV infra-serverless est visé.

L’observateur maintient un worker du contrôle à l’entrée du véritable syscall
`read` de ce fichier. Il vérifie TID, naissance, groupe du processus, FD,
chemin de révision exact, périphérique et inode. Il ne lit aucun buffer de code,
requête, secret ou réponse ; il ne modifie ni mémoire, ni registre, ni résultat
syscall, ni fichier applicatif. Le fichier reste régulier et immuable. Le
retour HTTP est produit par le contrôle déployé après la libération native.

Le thread principal est suivi avec PTRACE_SEIZE et TRACECLONE, en PTRACE_CONT :
les créations de nouveaux workers sont ainsi saisies avant leur exécution.
Les workers existants et nouveaux sont suivis en PTRACE_SYSCALL ; seuls ceux
arrivés sur le FD exact sont retenus. Le principal et les autres workers sont
détachés dès que le nombre attendu est atteint. Aucun arrêt de groupe ni
EXITKILL n’est utilisé. Les signaux étrangers doivent être rendus explicitement
ou provoquer une restitution vérifiée ; ils ne sont pas avalés silencieusement.

Cette décision s’appuie sur la sémantique publiée de
[ptrace](https://man7.org/linux/man-pages/man2/ptrace.2.html), notamment les
arrêts des threads hérités après SEIZE et TRACECLONE. Le
[lecteur CPython 3.14](https://raw.githubusercontent.com/python/cpython/3.14/Python/fileutils.c)
libère le GIL pendant `read` ; c’est la raison du point de maintien choisi.
La disponibilité de la boucle HTTP et l’identité du FD doivent toutefois être
prouvées à l’exécution. L’énumération périodique seule des threads est écartée :
un nouveau worker pourrait lire le petit fichier avant son attachement.

## Garde et bornes

Avant le premier SEIZE, une garde systemd indépendante est armée sur le seul
SPARK DEV. Elle possède une copie figée de son programme, vérifiée par SHA,
et une identité privée root sous `/run/serverless-restore-editor-read-<uuid>`.
L’identité lie installation, namespace, fonction, révision, image, CID,
démarrage, PID et naissance du contrôle, cgroup et helper par PID/naissance.
Les trois fichiers officiels et la référence sont recoupés sans contenu exposé.

Le maintien volontaire dure au plus 45 secondes à partir de l’armement. L’observateur a
une échéance globale de 50 secondes ; la garde indépendante part à 60 secondes,
avec exécution bornée et jonction. Un helper suspendu ne peut pas appliquer
son échéance propre ; cette branche est bornée par le départ indépendant à60s
puis sa restitution, et non par le délai volontaire45s. Une fin normale ou EOF détache tous les
tracees puis vérifie l’état sain. Une perte ou suspension du helper déclenche
sa terminaison par pidfd après vérification de son identité ; les attachements
sont ensuite tous rejoints et chaque thread doit être libre de tracer/arrêt.
La garde ne redémarre aucun conteneur et ne signale jamais un PID réutilisé.

L’unité de garde est choisie et conservée par le client avant le lancement SSH,
pour que la perte du premier message ne fasse pas perdre l’identité du secours.
Le helper exact est terminé et rejoint avant les diagnostics applicatifs de
récupération ; un refus de ces diagnostics conserve son échec sans laisser le
traceur suspendu. Les callbacks de flux du client mémorisent leurs erreurs et
laissent son finally joindre secours et transport ; ils ne lèvent pas hors du
scénario. Une jonction échouée ferme aussi le seul SSH local par TERM/KILL,
sans confondre cette fermeture avec une restitution native.

Chaque tentative terminale possède un reçu immuable distinct. Le client rejoint
la commande, les requêtes en vol, le timer et le service avant de nettoyer les
objets. Une disparition de transport ne suffit ni à déclarer un succès ni à
relancer un scénario. Les JSON privés restent incomplets jusqu’à ces jonctions.

## Qualification propre à l’instrumentation

Les mêmes véritables requêtes HTTPS éprouvent, en série :

1. maintien d’un lecteur, santé HTTP disponible, libération explicite et réponse
   exacte ;
2. EOF du propriétaire pendant un lecteur retenu ; réponse exacte et restitution ;
3. perte SIGKILL du helper après maintien, sans nouvel appel rejoué ;
4. suspension SIGSTOP du helper, secours indépendant, réponse exacte et même
   contrôle sans redémarrage ;
5. véritable échec de diagnostic du secours : après jonction du helper exact,
   seule la limite NOFILE du processus de secours est mise à zéro ; sa lecture
   de diagnostic échoue réellement avec EMFILE. Sa propre limite est restaurée
   avant publication du reçu d’échec. La vérification normale suivante doit
   confirmer helper disparu, threads détachés et contrôle sain ; aucune limite
   du contrôle ni du SPARK n’est modifiée ;
6. quatre lecteurs réellement retenus, cinquième 429 borné, puis quatre réponses
   exactes et nouvelle lecture saine après libération.

Les reçus recoupent toutes les naissances, FD et inodes réellement observés.
Les préconditions refusées n’attachent aucun thread. L’absence d’un prérequis
fait échouer le passage ; aucun mock, faux serveur, interception ou skip.
Une erreur conserve son rapport, ses ressources intentionnelles et sa restitution
avant toute correction puis nouveau gel. Les passages ne s’additionnent pas.

Après la preuve ciblée : manuel, routes publiques et connexion sont rejoués en
série ; leurs captures sont inspectées individuellement. Les sources et l’image
sont figées avant/après chaque phase, les 38 fichiers backend et quatre ressources
web servis sont recoupés, ainsi que les 5 982 artefacts initiaux et la configuration
officielle. Les fonctions/tokens de campagne sont purgés/révoqués, les parents
supprimés ; aucune activité, réservation, opération, garde ou traceur ne subsiste.

## Suite des scénarios produit

Les cas de révocation, purge et reconstruction utiliseront cette même barrière
après sa preuve propre. Les lectures maintenues du diff, la mutation/adoption/
abandon pendant attente, le choix volontaire d’un autre focus, les refus et
recalages et le focus après adoption conservent leurs critères 070.3/.4 ouverts.
Aucun nouveau comportement produit ni manuel, schéma, variable, secret ou route
n’est introduit par la seule instrumentation de lecture.

## Banc implémenté, avant premier passage

Le client, le paquet original, le lecteur natif et les deux programmes de
barrière/secours sont implémentés. Neuf groupes sont prévus, avec sept handlers
réels : préparation puis un après chacun des six scénarios. Le contrôle des
syntaxes Python/Node est un prérequis, aucune preuve fonctionnelle acquise.
La revue de sûreté précède le gel des sources et l’exécution ; les défauts de
banc trouvés avant ce passage ne sont pas présentés comme des pannes produit.
La qualification des droits pendant IO, de la purge et des bornes ZIP demeure
à produire après la qualification propre de cette instrumentation.

## Premier passage échoué et décision de jonction

Le [passage833a9c59](evidence/code-editor-reader-guard-join-failed-dev-2026-11-12.json)
au gelf17f515/414sources échoue au sixième groupe, après cinq passés. Le secours
à60s termine réellement le helper suspendu ; les threads sont détachés et le
même contrôle reste sain. La commande finish reproduit ensuite l’erreur :
`systemctl stop <unité>.timer` renvoie5 parce que le timer collecté n’existe plus.
Le client ne considère pas cette jonction comme acquise et conserve ses objets.
Ils sont ensuite purgés/révoqués par un nouveau SSO et les API normales.
Quatre handlers, quatre helpers disparus, parents supprimés, compteurs nuls,
dix migrations, ressources servies/configuration/référence et5982artefacts sont
recoupés. Zéro groupe qualifié ; EMFILE et quatre lecteurs ne sont pas exécutés.

Correction décidée avant code : la demande d’arrêt du timer n’est pas une preuve
de jonction. Comme le précédent071, attendre les états natifs du timer et du
service : chargés ou absents, tous deux inactifs, MainPID0. Une erreur de stop
ne devient pas automatiquement un succès ; l’état terminal est toujours relu
sous la borne50s, et tout état inconnu/actif échoue. Un nouveau gel et le replay
complet sont requis ; aucune image produit, manuel ou configuration ne change.

La demande stop est maintenant dissociée de son statut de sortie ; la boucle de
relecture garde exactement ses exigences et sa borne. Syntaxe contrôlée ; le
replay E2E et les campagnes communes restent à produire sur ce nouveau gel.

## Second passage et traitement des événements hérités

Le [passage7bdc6702](evidence/code-editor-reader-event-failed-dev-2026-11-12.json)
au gel032719d/414sources passe sept groupes puis échoue au huitième : le
répartiteur refuse `unexpected_tracee_event` après81événements et deux lectures
retenues. Le diagnostic n’a pas encore le TID ni le statut brut de ce wait ;
un arrêt initial d’enfant observé avant l’événement de son parent reste une
hypothèse. Le premier check de restitution échoue à joindre tous les threads ;
la fin du helper puis le secours rendent tous les threads. Six helpers sont
absents, six handlers recoupés, fonction/token/parents nettoyés et conservation
complète. Zéro groupe qualifié, aucune régression commune additionnée.

Décision avant code : conserver TID/statut brut/événement/signal du dernier wait
et la ligne de défaillance, sans buffer. Le répartiteur peut découvrir l’arrêt
initial PTRACE_EVENT_STOP/SIGTRAP d’un enfant avant GETEVENTMSG de son parent :
il enregistre alors un thread déjà tracé uniquement si TGID, cgroup et TracerPid
correspondent au contrôle/helper attendus. Il ne fait aucun nouveau SEIZE.
L’événement clone du parent rapproche ensuite ce même TID et sa naissance ;
un doublon incohérent, un autre groupe ou un arrêt différent reste refusé.
Les liens parent/enfant sont joints avant détachement du principal. Les mêmes
identités s’appliquent à tous les nouveaux threads et les listes restent bornées.

Pour éprouver réellement la création de workers, le prochain passage partira
d’un contrôle fraîchement redémarré, après backup SQLite natif et précontrôle
sans activité ni garde. Ce redémarrage DEV conserve CID/image/données et la
référence ; seul le démarrage/PID du contrôle change intentionnellement. Une
nouvelle baseline avant la campagne distingue ce changement des conservations
exigées pendant chaque épreuve. Le groupe à quatre lecteurs devra observer un
véritable événement clone ; la seule réutilisation de workers ne suffit pas.

Le répartiteur implémente maintenant ce rapprochement et conserve les métadonnées
brutes du dernier wait, les créations et les arrêts initiaux observés. Le client
exige un clone réel dans son groupe à quatre lecteurs. Les syntaxes passent ;
le correctif est qualifié par le troisième passage décrit ci-dessous. Après revue et gel du correctif ece7d09,
le redémarrage préparatoire est effectué une seule fois : backup SQLitef0543e39,
même CID/image, nouveau démarrage2026-11-12T15:57:39.012887686Z. Santé, intégrité,
FK, dix migrations, configuration, référence et5982artefacts sont conservés.
Le troisième passage part de cette nouvelle baseline.

## Résultat qualifié et portée

Le [troisième passagec07760f8](evidence/code-editor-read-concurrency-dev-2026-11-12.json)
au commit7968ab9 passe34groupes :9ciblés puis8manuel/8public/9connexion,
414sources d’index11b90326 et imageb452ef16 identiques avant/après chaque phase.
La baseline suit le redémarrage préparatoire15:57:39UTC, backupf0543e39 ;
aucun redémarrage n’a lieu pendant les quatre campagnes.38backend/quatreweb,
configuration officielle, référence et5982artefacts sont strictement conservés.
Manuel18chapitres/74paragraphes, SHA8a50ffa0 inchangé,22captures inspectées.

Quatre workers sont réellement arrêtés à read sur quatre FD distincts du même
fichier/inode. Trois créations de threads sont observées, chacune avec son
arrêt initial reçu avant l’événement du parent ; les TID/naissances sont
rapprochés avant détachement du principal. La santé/gestion HTTP répond pendant
le maintien, et la cinquième lecture reçoit429/Retry-After2 en63,238ms.
Les quatre réponses exactes, une nouvelle lecture et un nouveau handler passent
ensuite. Les autres modes prouvent release/EOF, SIGKILL9, SIGSTOP19 puis secours
indépendant60s, et EMFILE réel du seul processus de secours après jonction du
helper ; sa limite est restaurée avant le reçu d’échec, puis le finish normal
confirme la santé. Aucun buffer, registre ou retour syscall n’est substitué.

Sept invocations nominales distinctes sont jointes aux lignes succeeded,
handler_started1/HTTP200 et au hash de leur révision. La fonction/révision est
purgée physiquement, son jeton révoqué et ses deux parents supprimés. Avec les
deux passages échoués : trois fonctions/tokens, six parents et16helpers sont
nettoyés. Toutes les tentatives de restitution sont conservées, y compris les
EMFILE attendus et le premier check de threads refusé du second passage ;
les restitutions terminales réussissent toutes. Zéro activité/brouillon/
opération/réservation/bail/garde, intégritéok/FKvide et dix migrations.

Ce complément qualifie les six parcours de l’instrumentation et la capacité de
quatre lectures de source. Il ne qualifie pas encore révocation pendant IO,
purge face à lecteur vivant, reconstruction unique/limitesZIP, diff/UI maintenu
ou interruptions de publication.070.1–.5 restent ouverts ; aucun critère
supplémentaire n’est coché. Les deux échecs gardent chacun zéro groupe qualifié.


## Préparation explicite du contrôle courant — SLS-147

Le [diagnostic natif du 24 novembre](evidence/editor-reader-held-reconciliation-dev-2026-11-24.json)
retrouve les six checkpoints held du premier complément32. Le dernier contient
quatre lecteurs, quatre FD/TID distincts et aucun clone ; les quatre identités
figurent déjà dans le reçu de restitution précédent. Le client échoue avant
le cinquième GET. Le défaut de préparation de la suite est établi ; aucune
cause interne du pool ni panne produit n'est déduite.

Décision avant code : fournir `python3 -B e2e/prepare-editor-worker-control.py`
comme préparation explicite réutilisable. La suite32 l'exécute immédiatement
avant code-editor-read-concurrency, après clôture des six campagnes précédentes,
puis relève sa baseline avant le client. Le ciblé9 utilise exactement cette
même commande. L'ordre32, ses276groupes, les huit préparationsSSO et tous les
oracles restent inchangés ; cette préparation compte zéro groupe.

La commande vise uniquement infra-serverless, API f016 et CID déjà observé.
Elle exige les deux seuls conteneurs sains attendus, l'agent actif, zéro fonction
vivante/brouillon/instance/opération/appel/réservation/candidat actif/bail/
stockage en attente, onze migrations exactes, intégrités/FK, zéro garde active
et aucun thread du contrôle arrêté ou tracé. Toute précondition refusée termine
nonzéro avant la demande de redémarrage.

Avant une unique demande Docker restart de la seule API, sauvegarder les deux
bases par SQLite backup sous l'identité propriétaire1001, dans un nouveau dossier
privé qualification-history ; intégrité/FK, schéma et cardinalités des copies
recoupés et SHA conservés. Les sauvegardes ne sont jamais publiées. Conserver
les empreintes des tables de configuration/identité/code, les fichiers officiels,
les budgets et l'inventaire5982. Contrôle : security_metadata, namespaces,
services, functions, service_tokens, revisions, function_versions, code_drafts,
service_log_policies, schema_migrations ; registre : metadata, functions,
volumes, configuration_receipts et discard_receipts. Les autres tables de
maintenance et de diagnostic sont sauvegardées et dénombrées, sans prétendre
que leurs curseurs ou rétentions restent figés pendant un redémarrage normal.

Une seule demande restart, bornée35s ; si son observation expire, inspecter
la même génération jusqu'à120s, sans nouvelle demande. Un retour nonnul reste
un échec, même si le service revient sain. Avant réussite : nouvelle naissance
et StartedAt, même CID/image, référence intégralement inchangée, santéHTTP200,
repos/migrations/intégrités/FK, tables protégées, configuration, budgets et
5982originaux égaux. Le reçu privé conserve avant/après, backups parSHA,
retour réel, erreur primaire et secondaires de publication séparées. Aucune
configuration ni limite du contrôle n'est changée pour créer les threads.

Le helper de lecture exporte son recensement initial borné des TID/naissances.
Le client conserve held dans ses observations avant les assertions ; le check
à quatre lecteurs exige toujours un clone réel, et rapproche au moins un
lecteur avec un enfant cloné et au moins un avec le recensement initial.
La santéHTTP, quatre réponses exactes, cinquième429/Retry-After2 borné5s,
sept handlers et six restitutions gardent leurs exigences et leurs bornes.

Qualification : préparation réelle puis neufgroupes complets et25communs frais,
captures inspectées, purges et gardes jointes ; aucun succès déduit du code.
Le nouveau préparateur et les adaptations changent le vecteur indexé. Décision :
refaire ensuite49/543/18 depuis le début sur ce nouveau gel, sceller/committer
sa preuve, puis32/276 sur les mêmes sources. Le49cd01985/530 et le premier32
rouge restent leurs époques ; aucune équivalence de produit ne remplace ce rejeu.


## Fautes réelles du préparateur — SLS-147.3

Le nominal34 sur1006ba1/531 garde sa preuve. Avant le prochain49, exécuter
`python3 -B e2e/editor-worker-preparation-failures.py` : quatre diagnostics
réels, en série et à zéro groupe fonctionnel ajouté. Le préparateur déployé
reste exactement celui du nominal ; ni source, timeout, dépendance ni retour
ne sont substitués. Chaque diagnostic exécute une seule fois le vrai CLI,
avec zéro ressource active avant/après et référence/configuration/5982conservés.

1. Lecture refusée : après ouverture de ses flux, le seul stdout privé du
   préparateur passe temporairement de0600 à0000. Le SSH continue à écrire sur
   son FD déjà ouvert ; le vrai retour natif0 est conservé avant EACCES13.
   PermissionError reste primaire, les refus suivants restent secondaires.
2. Sauvegarde refusée : un répertoire vide possédé par le diagnostic occupe
   son seul chemin report.json avant publication. Le vrai IsADirectoryError21
   rend le CLI nonnul malgré la préparation native0 ; publication-errors.json
   conserve cette première erreur. Le répertoire exact est ensuite retiré.
3. Affichage refusé : fermer le seul lecteur du pipe stdout du CLI. Son vrai
   BrokenPipeError32 est conservé dans le reçu terminal ; le reçu report.json
   déjà écrit avant affichage est un état intermédiaire, jamais un succès final
   lorsque le CLI termine nonnul. Conserver le code réel, y compris120 si le
   flush de l'interpréteur échoue ensuite ; aucune conversion en0.
4. Transport expiré avec secondaire : identifier le seul enfantSSH du CLI par
   parent/naissance, commande et inodes de ses stdout/stderr privés, épingler
   son pidfd, puis SIGSTOP. Le préparateur conserve sa vraie attente240s,
   termine/joint son SSH et garde TimeoutExpired comme primaire, retour distant
   inconnu. Le refus temporaire de lecture de son stdout ajoute EACCES13 comme
   secondaire. Relever les octets réellement disponibles, même vides ; ne pas
   déduire qu'un restart a été demandé ou achevé d'un transport expiré.

Le contrôleur n'agit que sur ses processus et chemins privés nouvellement
créés. Il ne suspend aucun processus du contrôle, du SPARK ou de FORGE. Avant
mutation, UID/type/absence de symlink, identités/inodes et propriété sont
recoupés. Les permissions sont restaurées par le FD conservé en finally ; un
PID réutilisé n'est jamais signalé. Le CLI et son seul SSH sont joints avant
cas suivant ; un échec du contrôleur restitue ses propres fautes et garde la
première exception. Les quatre codes clients nonnuls attendus ne qualifient
le contrôleur0 qu'après validation de ces erreurs et du repos natif final.
Une faute non atteinte échoue, sans retry ni saut de scénario.

Conserver pour chaque cas : source/commit, naissances/commandes expurgées,
opérations et temps monotones, stdout/stderr réels sousSHA, reçus intermédiaire
et terminal distincts, première erreur et secondaires, restitution et état
natif final. Les sauvegardes SQLite restent privées ; aucun contenu métier
ou secret ajouté aux exports. Ces diagnostics ne remplacent ni les neufgroupes
nominalement acquis, ni25communs, ni le nouveau49/32. Le nouveau contrôleur
maintenu porte le prochain vecteur à532sources ; le gel suivant le recoupe.
