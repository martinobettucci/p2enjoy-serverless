# Testeur HTTP : exception native d’une tâche avec processus conservé

Complément du dernier critère ouvert [SLS-071.6](BACKLOG.md#sls-071), après la
[qualification37 du chargement](CONSOLE_TESTER_LOADING.md). Le comportement
produit attendu est inchangé : les tâches sont annulées puis jointes avant de
rendre la capacité, y compris lorsqu’une tâche sortante lève une exception qui
n’est pas une erreur de transport prévue. Un redémarrage ne prouve pas cette
restitution : il réinitialiserait le compteur.

## Décision avant code

Employer une vraie faute de ressource du noyau sur le seul contrôle DEV,
exclusif et au repos, au moment de l’ouverture publique de son certificat CA.
L’inspection en lecture seule du12novembre relève Python3.14.10, HTTPX0.28.1,
`trust_env=False` et le constructeur `ssl.create_default_context(cafile=certifi.where())`.
Le fichier réel est `/usr/local/lib/python3.14/site-packages/certifi/cacert.pem`.
Le PID courant1007466 porte la naissance508864062 ; ses limites NOFILE sont
1048576/1048576. Ces valeurs sont des observations initiales, à relire avant
chaque attachement et mutation, jamais des autorisations pour un autre PID.

Un opérateur spécialisé compose les observateurs mono-TID existants sans
modifier leur classe partagée. À l’entrée du vrai `openat` du CA, il garde le
TID principal arrêté, inventorie et arrête les autres TID jusqu’à un ensemble
stable confirmé. Il abaisse seulement la limite soft NOFILE à0, hard conservée,
puis ne relance que le syscall cible. Le retour doit être le vrai `-EMFILE`
produit par le noyau. À l’arrêt de sortie, il restaure et relit les limites
originales **avant toute continuation Python et tout détachement**.

Aucun registre, résultat de syscall, buffer, certificat, code applicatif,
dépendance, couche Docker ou fichier officiel n’est modifié. La panne ne
remplace aucun composant : le constructeur TLS traite réellement l’échec de
son ouverture. La classe d’exception Python reste à observer ; une erreur
capturée par le chemin normal `httpx.HTTPError` ne satisfait pas cette preuve.

## Garde et bornes

Armer et constater une garde indépendante avant l’attachement. Elle porte une
copie figée du restaurateur, les SHA des programmes/fichiers officiels, CID,
image, StartedAt, PID/naissance/cgroup, identité du helper et limites originales.
Les modes de contrôle ne prennent que les UUID de la fixture et l’unité native.
Le namespace original est `function-http-client-task-exception-XXXXXXXX` ;
service et fonction portent le nonce de campagne. Hors scope ou consommation
concurrente, aucun attachement et aucune mutation ne sont permis.

Au secours piloté, la garde empêche d’abord le helper de poursuivre une mutation
avec un SIGSTOP par pidfd et vérifie cet arrêt ; elle revalide le propriétaire,
restaure et relit les limites, puis termine et joint le helper. Le détachement
noyau libère ensuite les TID avec leurs ressources normales. Elle n’attend pas
un verrou détenu par un helper figé pour restaurer la ressource. La preuve
nominale et le secours possèdent leurs reçus séparés, écrits atomiquement.
Aucun restart n’est une restitution acceptable pour ce critère.

Une mort spontanée du traceur peut détacher les TID avant le passage de la
garde. Il existe donc une fenêtre locale de ressource dégradée, bornée par la
garde, sans garantie d’atomicité entre disparition et restauration. Cette
limite du banc DEV est explicite ; elle ne crée aucune dépendance FORGE.
La garde restaure le PID original s’il existe encore. Si ce PID/génération est
perdu, le résultat reste non qualifié, avec diagnostic et fixture conservés
jusqu’à restitution connue. Aucun nouveau contrôle n’est adopté comme preuve.

Bornes : au plus64TID, convergence de census et arrêts sous2s ; recherche de
l’ouverture sous8s ; garde12s ; une seule faute par opérateur. Toute divergence
d’identité, traceur concurrent, limite inattendue, TID non arrêtable ou dépassement
abandonne avant abaissement, ou rejoint la restitution déjà armée. Le chemin
public est comparé octet par octet, borné à512octets, et seule sa concordance
est rapportée ; aucun buffer de requête, TLS ou secret n’est lu.

## Matrice de qualification

1. Connexion réelle depuis l’accueil et SSO ; préflight des deux bases,
   exclusivité, Docker et limites. Créer/publier/promouvoir une fonction
   originale du dépôt, Read temporaire par API normale. Appel sain200 avec
   hash/UUID et trace native, puis repos complet.
2. Éprouver le secours après abaissement, avant exécution du syscall cible :
   tous les TID sont arrêtés et soft0 constatée ; demander le secours, sans
   SIGKILL spontané du helper. Constater restauration avant sa terminaison,
   détachement de tous les TID, même PID/CID/image/StartedAt et appel réel200.
   Ce scénario de secours ne compte pas comme exception inattendue.
3. Provoquer nominalement la seule ouverture CA fautée. L’audit `function.test`
   de cette fonction doit être commis avant la frontière, sans invocation
   passerelle nouvelle. Constater `openat`, `-EMFILE`, limites originales
   relues au syscall-exit puis libération. Observer le500 réel et le traitement
   UI d’issue non confirmée, sans rejeu ; desktop/mobile et saisies conservées.
4. Lire les vrais logs du contrôle depuis un relevé avant campagne, avec borne
   d’octets et deadline. Rapporter seulement classe d’exception, frames
   publiques fichier/ligne/fonction et SHA du bloc ; jamais les logs bruts.
   Exiger une pile passant par `forward`, le constructeur HTTPX et TLS, hors du
   chemin de transport prévu. Corréler fenêtre et unique audit de campagne ;
   un500 sans pile native ni frontière noyau n’est pas une preuve suffisante.
5. Avec le **même processus**, lancer quatre vrais relais lents et attendre
   quatre invocations actives ; cinquième429 avant émission. Joindre les quatre
   succès puis réussir cinq nouveaux appels explicites. Un seul200 serait
   insuffisant pour exclure la fuite d’une des quatre places. Ne pas rejouer
   automatiquement la requête dont l’issue est inconnue.
6. Purger la fonction, révoquer les jetons, supprimer les parents par API après
   restitution connue. Recouper deux bases, migrations, réservations, instances,
   baux, limites exactes, tous les TID sans traceur/arrêt, gardes jointes, même
   contrôle/référence et5 982artefacts. Régressions communes sérialisées et
   inspection de chaque capture avant qualification ; aucun groupe antérieur
   réadditionné et aucun test ignoré.

## Relecture du premier opérateur avant exécution

La revue du code préparatoire relève cinq frontières à corriger avant tout
prlimit modificatif : disparition du helper entre ouverture du pidfd et STOP,
zombie pendant l’attente, identité complète trop ancienne avant abaissement,
absence de reçu d’échec de restitution, et état systemd collecté interprété
comme échec de commande. STOP/KILL/jonction doivent reconnaître un pidfd lisible
ou ESRCH comme une sortie, puis poursuivre la restauration du PID original.
CID/image/StartedAt et référence sont relus immédiatement avant abaissement.

Le restaurateur écrit aussi un reçu atomique incomplet avec phase, limites
connues et état du helper si sa restitution échoue ; aucune santé ou libération
n’y est présumée. Son alarme devient une exception traitée pour traverser cette
finalisation, sans prétendre couvrir SIGKILL. L’unité préparée est exposée avant
systemd-run et la tentative retenue avant sa commande pour pouvoir réconcilier
une réponse perdue. Les unités absentes/collectées sont reconnues par leurs
propriétés natives, même si systemctl retourne un code non nul. Aucun de ces
constats ne provient d’une exécution de panne ; client/pile restent à écrire.

La seconde revue relève le temporaire commun à deux restaurateurs et la priorité
inconditionnelle d’un ancien succès sur un échec plus récent. Conserver des
reçus terminaux immuables par tentative, avec temporaire unique, UUID, début/fin
et ordre monotone local. Le lecteur choisit le dernier reçu terminal de cette
unité, succès ou échec, et ne transforme jamais le succès historique en état
courant. Aucun changement de compteur ou d’infrastructure externe n’est requis.

## Corrélation du500 sans access log

La revue du client/lecteur relève une hypothèse à retirer avant essai :
`control/Dockerfile` désactive explicitement les access logs Uvicorn. Le500
est donc prouvé par la vraie réponse Playwright et l’unique POST UI, jamais
par une ligne d’accès supposée présente. Le lecteur natif recoupe séparément
la pile TLS inattendue, l’audit supplémentaire unique, la frontière EMFILE et
l’absence d’invocation passerelle. La journalisation de l’application reste
inchangée. Six groupes et douze handlers sont les comptes attendus, sans
préjuger de leur réussite ni de la classe Python réellement observée.

## Premier passage : refus du modèle pendant préparation

Le [passage05ba6e14](evidence/function-http-client-task-preparation-failed-dev-2026-11-12.json)
sur401sources/commit1a41b44 s’arrête au422 de création : FunctionCreate ne porte
pas de description. La table functions n’a pas cette colonne non plus ; la
requête de propriété du helper aurait donc aussi échoué. Aucun attachement,
prlimit modificatif, fonction, jeton ou capture n’est produit. Namespace/service
supprimés, intégritéok et limites1048576/1048576 recoupées sur le même PID.
Zéro groupe retenu pour la qualification, y compris le SSO préliminaire.

Décision avant correction : garder le nonce complet dans les descriptions du
namespace/service, et le suffixe de huit caractères dans le nom significatif de
la fonction. Le helper lie nom exact, UUID de fonction/service/namespace et
nonce parent ; il ne suppose aucun champ absent et ne modifie pas le modèle
produit pour les besoins du banc. Rejouer le client complet après correction.

## Replay : sortie de l’observateur sans cause structurée

Le [passage742199ee](evidence/function-http-client-task-observation-failed-dev-2026-11-12.json)
sur401sources/commitb5c1907 passe SSO et préparation, puis le helper termine1
après armed, avant tout fichier fault-entry. Deux handlers réussissent après
libération ; une fonction est purgée, un jeton révoqué, parents supprimés et
helper disparu. Même PID, limites originales et TID sans traceur recoupés,
38backend/4web et5982artefacts conservés ; deux captures inspectées. Zéro
groupe ajouté à une qualification, et aucune baisse NOFILE n’est exécutée.

La cause exacte manque : le client conserve seulement taille431/SHA du stderr
et constate native_operator_ended. Ce reçu ne prouve ni timeout, ni signal, ni
mauvais chemin. Décision avant correction : persister/émettre un échec structuré
avec phase, code fixe/errno/ligne, durée et compteurs numériques de stops,
syscalls, ouvertures, correspondances CA et TID, ainsi que limites connues.
Aucun message brut, chemin inconnu, pointeur ou buffer n’est rapporté. Conserver
les événements dans le client avant toute levée, puis rejouer le parcours réel.
Ne pas modifier les bornes, la gestion des signaux ou la frontière de panne
sur une hypothèse non vérifiée par ce reçu.

Relecture de cette instrumentation avant exécution : capturer l’échec en
mémoire, mais remettre/relire prioritairement NOFILE puis libérer les TID et
joindre la garde avant les E/S du diagnostic. Un stdout bloqué ne doit pas
prolonger la fenêtre de limite dégradée ; une erreur du diagnostic ne masque
pas l’exception initiale. Le fichier du frame est un identifiant public fixe
ou une empreinte, jamais un basename inconnu en clair. Ces corrections sont
requises avant le nouveau passage ; aucune panne n’est encore qualifiée.

## Attente native : borne atteinte après6777arrêts

Le [passageca4aa8b9](evidence/function-http-client-task-wait-failed-dev-2026-11-12.json)
sur401sources/commit9e73901 établit phase2/CA_open_not_observed après8154,437ms :
6777stops,3389entrées,3388sorties,48openat sans CA,2232pread64 et aucun signal.
Aucune baisse NOFILE ni nouveau TID attaché hors main ; restitution connue,
TIDlibérés, même PID et limites. Deux handlers réussissent après libération,
fonction purgée, jeton révoqué, parents/helper nettoyés ; deux vues inspectées,
38backend/4web et5982artefacts conservés. Zéro groupe qualifié.

Le polling1ms par stop peut coûter plusieurs secondes sur ce volume ; il est
une explication plausible, pas une mesure isolée de toutes les8154ms. Décision
avant code : composer un observateur local dont wait utilise waitpid bloquant
avec alarme POSIX sur la même échéance absolue. L’alarme est propre au helper,
annulée à chaque sortie d’attente et l’ancien handler restauré au détachement.
Aucun timer antérieur n’est adopté. Conserver8s de recherche,2s de gel et la
garde indépendante12s ; aucun allongement de borne, aucun changement de la
classe NativeObserver partagée ni de la gestion des signaux du contrôle. Le
nouvel essai devra prouver l’arrivée au CA et toutes les frontières de panne.

## Qualification finale de071.6

La [preuve31](evidence/function-http-client-task-exception-dev-2026-11-12.json) porte401sources67215a2b,
commit417102d et image60938093 inchangée. Le replay4337a800 passe six groupes,
puis8manuel/8public/9connexion sur les mêmes sources. Quatre JPEG ciblés sont
inspectés par le principal et22originaux communs par le vérificateur RO.
Les trois passages échoués précédents gardent zéro groupe qualifié.

Le secours soussoft0 remet NOFILE1048576/1048576 avant le SIGKILL du seul
helper, le joint et libère le même PID. L’appel en attente réussit une seule
fois. La faute nominale observe le vraiopenat du CA, cinq TID arrêtés et le
retour noyau-24. Les reçus Python originaux donnent134655ns de ressource
dégradée, restituée à l’arrêt syscall-exit avant Python. Les nombres muraux ns
des événements JS peuvent être arrondis ; les originaux collectés séparément
servent à cette mesure et à l’ordre natif. Aucun registre/résultat/buffer n’est
modifié. Le500 est reçu par Playwright sur un seul POST UI ; la pile native
porte OSError, forward, constructeurHTTPX et create_default_context. Un audit
supplémentaire unique, aucune invocation nouvelle. Les9336octets de logs restent
privés ; seuls classe, sept frames publiques, taille/SHA sont rapportés.

Le même PID1007466/naissance508864062 et le même CID/image/StartedAt restent
vivants. Quatre vrais relais lents sont actifs, le cinquième reçoit429 en22,6ms ;
les quatre terminent200, cinq appels suivants et un dernier UI200 réussissent.
Douze handlers succeeded sont corrélés. Une fonction/jeton nominaux sont
purgés/révoqués ; avec les passages préliminaires, trois fonctions et trois
jetons, quatre namespaces/services supprimés et quatre helpers terminés.
Toutes les limites et tous les TID sont recoupés, sans traceur/arrêt restant,
gardes et ressources nulles. Dix migrations, intégritéok/FKvide,38backend/4web,
manuel18chapitres/74paragraphes et5982artefacts sont conservés.

Statut :071.6 et SLS-071 qualifiés avec les références antérieures de chaque
critère. La campagne complète de plateforme095 et les défauts101/102 restent
ouverts ; aucune autre unité n’est close par ce complément.
