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
