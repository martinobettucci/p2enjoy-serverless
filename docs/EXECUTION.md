# Moteur d’invocation

Contrat SLS-040 en cours de réalisation, complété par SLS-050 pour le stockage
et l’exploitation. Il précise [PLATFORM](PLATFORM.md) sans remplacer ses exigences.
Le runtime de validation est déjà qualifié ; les instances chaudes, la passerelle
et leurs preuves réelles restent à construire. Les campagnes de composants
ne prouvent ni les autorisations publiques ni les parcours de console.

## Instance et processus

Une instance est un conteneur Docker rootless portant les labels installation,
kind=instance, fonction, révision et identifiant d’instance. Son image est celle
de la révision validée. Un superviseur Node reste prêt entre les appels ; il
crée un enfant neuf pour chaque invocation. Ce dernier utilise le même
`runtime/loader.mjs` que la validation. Les variables globales applicatives ne
survivent pas d’un appel au suivant.

L’image et `/code` sont readonly ; aucun socket Docker ou fichier du contrôle
n’est monté dans la fonction. Le conteneur n’a aucune capability, utilise
no-new-privileges, un init pour récolter les orphelins, 64 PIDs et un tmpfs
`/tmp` de 16 Mio noexec/nosuid. Mémoire, swap limité à cette même mémoire et
CPU viennent de la configuration de fonction. Le superviseur et l’enfant
comptent ensemble dans ces limites. Docker ne redémarre pas seul une instance.

Les appels extérieurs utilisent un réseau Docker dédié à l’instance, sans
port publié. Son réseau et son conteneur portent les mêmes labels de propriété.
Un réseau explicitement `none` est admis par l’outil de diagnostic pour les
preuves sans appel sortant ; il ne devient pas silencieusement le réseau d’une
fonction de plateforme qui doit pouvoir contacter ses dépendances.

## Canal privé et terminaison

Le contrôle crée un socket Unix dans un répertoire privé par instance, monté
readonly sous `/protocol`. Le superviseur retire une fois son identité de
canal avant de charger du code applicatif. Les échanges suivants portent cette
clé en en-tête et l’identifiant de l’invocation. La clé reste dans le superviseur,
absente de l’environnement Docker, de l’environnement métier et du message
envoyé à l’enfant. Les corps du protocole sont bornés à 10 Mio, les en-têtes à
8 Kio et les connexions simultanées à quatre par instance.

Le corps de réponse est toujours encodé en base64 dans ce canal uniquement :
les 6 Mio décodés occupent au plus 8 Mio, même avec des caractères JSON échappés.
Le contrôle restitue le texte UTF-8 lorsque le handler a rendu du texte.
L’enveloppe d’événement est bornée à 8 Mio de JSON UTF-8 ; elle peut ainsi
transporter un corps HTTP de 1 Mio entièrement échappé sans réduire sa limite.

Le superviseur demande le prochain travail ; une attente sans travail est
bornée. Un seul travail peut être retiré à la fois. Les résultats tardifs,
doublons et identifiants étrangers sont refusés. Une sortie de processus ou
un log ne remplace jamais un résultat explicite. Le canal privé ne constitue
pas une attestation contre le code applicatif du même conteneur : le contrôle
vérifie également le cycle Docker avant réutilisation.

Le délai de démarrage d’une instance est distinct, plafonné à quinze secondes.
L’échéance d’invocation commence au dispatch vers l’instance prête et inclut
l’import applicatif. Elle utilise l’horloge monotone Linux partagée avec les
conteneurs ; le démarrage contrôle la cohérence de cette horloge. Le contexte
calcule son temps restant sur cette même échéance. Le superviseur garde une
échéance locale, et le contrôle impose indépendamment l’échéance extérieure.

Callback, Promise et retour synchrone sont acceptés : la première terminaison
gagne. Une exception, un rejet, une sortie sans résultat, une réponse invalide
et un timeout restent des issues distinctes. Après terminaison, le superviseur
tue et récolte les processus applicatifs, y compris leurs descendants détachés.
Il ne réutilise pas un enfant. Le contrôle compare ensuite les processus Docker
à ceux observés avant tout appel. Un processus résiduel provoque le recyclage
du conteneur ; il n’est pas accepté comme état prêt.

Un timeout, un défaut de protocole ou une disparition du superviseur recycle
le conteneur entier. La suppression est confirmée avant restitution du budget,
libération des références de révision et nettoyage du canal. Une destruction
non confirmée conserve ces ressources et dégrade la santé. Les tâches système
en cours sont rejointes avant la libération du verrou du contrôle, y compris
après annulation. Une invocation n’est jamais rejouée automatiquement.

Une notification indépendante signale le début du handler. L’observation
`handler_started` vaut true lorsqu’il a été signalé, false lorsqu’un résultat
exclut ce début, et null si le travail a été retiré puis perdu sans observation
suffisante. Un import peut lui-même produire des effets avant le handler ;
aucune de ces observations n’autorise un rejeu automatique. Le diagnostic
rejoint le nettoyage sur SIGTERM et SIGINT, y compris au repos avec stdin ouvert.

## Événement, réponse et journaux

La passerelle fournit un événement Lambda HTTP v1 : httpMethod, path, headers,
multiValueHeaders, queryStringParameters, multiValueQueryStringParameters,
body, isBase64Encoded et requestContext avec sourceIp et requestId. Le contexte
comprend awsRequestId, functionName, functionVersion, memoryLimitInMB et
getRemainingTimeInMillis. Les IDs proviennent du contrôle, pas du client.

Le corps HTTP entrant est borné à 1 Mio après autorisation. Les contenus textuels
UTF-8 sont transmis comme chaînes ; les autres sont encodés en base64. Les
types textuels comprennent text/*, JSON, XML, leurs suffixes +json/+xml et
application/x-www-form-urlencoded. Un texte non décodable reste binaire.
Les en-têtes multiples et paramètres répétés sont conservés. Le jeton plateforme,
les cookies de contrôle et son en-tête CSRF sont retirés ; Authorization et les
cookies métier restent transmis. sourceIp vient du résolveur de proxy approuvé.

La réponse exige statusCode entier 200..599 et body chaîne. Le corps décodé
est borné à 6 Mio ; le base64 doit être canonique. headers et multiValueHeaders
portent uniquement des noms HTTP valides et des valeurs sans caractères de
contrôle. Leur ensemble est borné à 32 Kio et 128 valeurs ; les valeurs multiples
prennent la priorité pour un même nom. Les en-têtes hop-by-hop, y compris ceux
nommés par Connection, Content-Length
et Access-Control-* applicatifs ne sont pas émis. La passerelle calcule ses
propres longueurs et sa politique CORS. HEAD ne transmet pas de corps.

stdout et stderr sont drainés par invocation, bornés à 64 Kio et expurgés des
secrets effectifs avant stockage ou exposition. Les buffers sont remis à zéro
entre appels. L’algorithme conserve les protections de chevauchement, troncature
et UTF-8 déjà qualifiées pour la validation. Les réponses métier ne sont pas
réécrites par l’expurgation des logs : le handler est responsable de leur contenu.

## Admission et générations

La file est bornée globalement et par fonction. L’attente possède sa propre
échéance queue_timeout_seconds, distincte de l’exécution. Un appel en attente
n’est pas encore admis : lors de l’admission, le contrôle relit le jeton,
la politique, la fonction, le service et la révision active, puis réserve
atomiquement son instance et ses ressources. Une révocation empêche donc un
appel encore en file de commencer ; elle ne rejoue ni ne tue un appel admis.

Les plafonds globaux excluent le contrôle, le stockage et les validations.
Une réservation comprend CPU, mémoire et place d’instance ; elle persiste
pendant le démarrage, l’exécution, l’inactivité et le drainage. Les limites de
fonction comprennent ses anciennes générations encore vivantes. Un timeout
de file retourne 429 sans exécution ; l’absence de ressources n’entraîne pas
de surallocation. Les minima sont servis dans ces mêmes budgets et leur somme
est contrôlée lors des changements de configuration.

Une génération combine révision, ressources et configuration effective de
service/fonction. Après publication, rollback ou modification de configuration,
les nouvelles admissions utilisent la génération courante. Les appels admis
terminent avec leur instantané et leur deadline ; les instances anciennes
prêtes sont retirées. La sérialisation des données exclusives porte sur l’UUID
de fonction et inclut toutes ses générations. Une révision utilisée par une
instance démarrant, prête ou occupée ne peut pas être supprimée physiquement.

Une suppression de fonction ferme les admissions et lance le drainage, tout
en conservant l’état d’exploitation jusqu’à disparition des instances. Un
changement de quota exige un drainage préalable et une vérification de l’usage.
Une mutation nécessitant un drainage long refuse à 409 tant que des invocations
sont actives ; elle ne prétend pas avoir appliqué le nouveau quota. Toute attente
système avant commit impose une nouvelle vérification des droits et versions.

## Stockage associé

Un agent local du SPARK supervise les processus FUSE qualifiés sous l’UID du
compte Docker, avec la seule capability nécessaire au montage. Son canal Unix
vérifie le pair local. Il accepte des UUID de fonction et les types data/cache,
jamais une commande, un backing ou un chemin client arbitraire. Il dérive les
chemins depuis les racines configurées dans la cellule et conserve un registre
durable des volumes, quotas, générations et états de montage.

Le contrôle lui réserve un bail avant création Docker. Le démontage est interdit
tant que des consommateurs conservent ce bail. L’agent vérifie le mountinfo hôte
et une opération réussie sur le montage, avec délai borné. Le runtime confirme
le type FUSE après montage ; un répertoire ordinaire n’est jamais un fallback.
Le contrôle ne suppose pas qu’un nouveau sous-montage apparaît dans son bind
déjà ouvert. Les chemins transmis à Docker sont ceux vus par le démon hôte.

Les montages sont `/data` et `/cache` lorsqu’ils sont activés ; le manifeste
peut y faire pointer ses variables applicatives. Le backing reste privé et
n’est jamais monté dans une fonction. Le quota actuel se change par drainage,
démontage, relance et rescan ; une réduction sous l’usage est refusée. Un crash
FUSE impose le remplacement de ses consommateurs avant remontage, sans prétendre
réparer leurs anciens bind mounts. Les données sont conservées pendant toute
reprise ; archive et purge sont des opérations distinctes.

## Passerelle et politique réseau

L’entrée stable est `/invoke/{function_id}/{path}`. Le chemin relatif correspond
à un événement HTTP de la révision ; `/invoke/{function_id}` désigne son endpoint
implicite lorsqu’il existe. Une méthode non déclarée est refusée. Le jeton
X-Serverless-Token avec Read est obligatoire ; une session admin ne le remplace pas.

Chaque requête effective vérifie la politique courante origine/IP. Les origines
sont normalisées par schéma, hôte et port explicite non nul ; le port par défaut
est canonisé. Une origine absente ou null ne satisfait pas une restriction
d’origine active. Les CIDR IPv4-mapped sont canonisés comme les IP clientes.
Le test de vérité sur le port ne doit pas assimiler zéro à une origine valide.

Un OPTIONS portant Access-Control-Request-Method est un préflight : origine,
IP, route, méthode et noms d’en-têtes sont vérifiés sans invocation ni jeton.
Les noms demandés sont bornés et validés ; le navigateur reçoit une origine
explicite conforme à la décision ET/OU, jamais un joker imposé par le handler.
Les réponses CORS ne permettent pas les credentials du navigateur. Les requêtes
OPTIONS ordinaires restent des invocations authentifiées lorsqu’elles sont
déclarées. Les en-têtes Vary conservent les dimensions de cette décision.

## Réalisation et preuves

La première tranche construit le superviseur, l’enfant et le pilote réel
d’instance, réutilisés ensuite par l’admission du contrôle. Leur outil de
diagnostic exige l’accès administratif au démon Docker et possède uniquement
ses ressources étiquetées ; il n’ajoute aucune identité d’invocation publique.
Les campagnes exécutent ce vrai pilote avec les sources de qualification,
le chargeur et Docker réels, puis vérifient processus, limites et nettoyage.

Les tranches suivantes raccordent l’agent de stockage, les admissions, les
transitions et la passerelle. Leurs preuves complètes passent par les véritables
routes avec des jetons créés après connexion SSO. La matrice couvre chaud/froid,
callback/Promise, binaire, erreurs, logs, CPU/RAM/PIDs, saturation, file, min/max/idle,
descendants, origines/IP, volumes, redéploiement, rollback, suppression et crash.
La console ajoute les opérations et observations réelles ; aucune métrique
calculée d’après une allocation n’est présentée comme une consommation mesurée.
