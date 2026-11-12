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

## État

Décision et matrice persistées avant code. Seule l’inspection préalable en
lecture seule a été exécutée. Aucun prlimit modificatif, nouvel attachement ou
scénario de ce complément n’est encore exécuté ;071.6 et SLS-071 restent ouverts.
