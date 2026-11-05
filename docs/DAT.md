# Architecture technique

## Plateforme

Contrat de réalisation : [PLATFORM.md](PLATFORM.md). Le contrôle retenu est
Python avec SQLite WAL local et un seul processus de coordination ; les
transactions de réservation sont courtes et ne contiennent aucun appel Docker.
L'interface prévue est React/Vite. Les instances Docker appartiennent au
contrôle par labels et sont réconciliées au démarrage. Le quota logique par
volume est développé dans `storage/`, avec go-fuse v2.12.1 (BSD-3-Clause,
release du 21 octobre 2026). Le proxy conserve les fichiers natifs et couvre
leurs chemins de mutation ; le contrat précis est dans PLATFORM, stockage.
Go sert uniquement à ce composant système. Son binaire statique se construit
dans Docker et s'exécute sous `spark-docker` pour fournir un montage au démon
rootless. Le montage direct sous spark-docker avec CAP_SYS_ADMIN dans la
cellule est qualifié ; les workloads Docker n'ont aucune capacité. Le helper
fusermount3 de cette cellule ne conserve pas son descripteur au passage exec.
Le composant passe 31 contrôles réels : [preuve](evidence/storage-dev-2026-11-05.json).
Les répertoires supprimés encore ouverts restent comptés jusqu'à Releasedir.
Les copies avec repli noyau passent par les écritures contrôlées du proxy.

Le contrôle et l'interface initiale sont déployés en DEV, avec la qualification
administrateur encore ouverte. Le banc décrit ci-dessous reste déployé à côté
du contrôle ; les montages de preuve sont nettoyés. La CLI Python de
plan/packaging passe 24 scénarios ciblés dans Docker ; la publication des révisions et
le moteur d'invocation restent à réaliser.

La compilation utilise Go 1.27.3 dans une image épinglée. go-fuse v2.12.1 et
x/sys v0.28.0 sont verrouillés avec go.sum. L'audit govulncheck v1.9.0 relève
zéro vulnérabilité atteignable et zéro paquet importé affecté. L'avis
GO-2026-5024 du module x/sys concerne uniquement Windows ; ce composant est
Linux. Résultat complet : [audit](evidence/storage-dependencies-2026-11-05.txt).

## Qualification

QLF-001 fournit l'application témoin de qualification, ses handlers et ses
données synthétiques.

### Service synthétique

Runtime Node.js 24 LTS, CommonJS, dépendance unique `yaml` pour interpréter un
véritable manifeste YAML. Le manifeste nomme handlers, événements HTTP,
échéances, budgets mémoire déclaratifs et identifiants stables de stockage.
Il utilise le fournisseur P2Enjoy proposé ; aucun plugin de déploiement
Serverless Framework n'est encore livré. La résolution `${env:...}` générale,
CloudFormation et les extensions d'autres fournisseurs ne sont pas supportées.

Les fonctions couvrent écho HTTP, réponse binaire, callback, autorisation métier
synthétique, vérification d'injection de configuration, compteur durable, cache,
worker avec checkpoint, exception, sommeil, boucle non coopérative et appel
entre fonctions. Aucune ne contacte une base client, blockchain, fournisseur
SMTP ou service externe.

### Exécuteur de référence

L'exécuteur sert `/healthz`, `/catalog` et `/functions/<nom>`. Il transforme la
requête en événement HTTP de type Lambda v1 puis invoque le handler dans un
processus enfant, avec `awsRequestId`, `functionName` et
`getRemainingTimeInMillis()`. Première terminaison gagnante pour Promise et
callback. L'échéance vient du parent, qui tue le processus après timeout.
La limite inclut ici le démarrage du processus. Chaque fonction est sérialisée
pour ses écritures ; des fonctions distinctes peuvent se relayer par HTTP.

Les deux volumes `/data` et `/cache` sont séparés et subdivisés par identifiant
stable de fonction. Les fichiers sont écrits atomiquement. Les identifiants
proviennent exclusivement du manifeste validé, jamais d'un chemin utilisateur.
Le worker conserve un checkpoint et peut reprendre une liste synthétique.

Ce serveur est un outil DEV de confiance, lié uniquement à la boucle locale
du SPARK sur le port invariant 18080. Il ne constitue pas une passerelle de
plateforme sécurisée : pas de SSO réel, de droits CRUD, de CORS/IP administrables
ou d'upload arbitraire. Pas de route publique proposée dans cette unité.
L'authentification métier du service témoin utilise un jeton confidentiel injecté
par la cellule, distinct de la future authentification de plateforme. Sans cette
configuration, le handler est indisponible ; aucun marqueur public n'est accepté
comme identité. Le jeton réel du banc DEV a été configuré via la console du
Spark ; la campagne complète exige ce prérequis.

### Configuration et secrets

Chaque service du Compose SPARK lit `/etc/spark/env` et `/run/spark/secrets` via
`env_file`. Aucun `.env`, aucune configuration injectée via `environment`,
`Dockerfile ENV` ou `ARG`. Les valeurs par défaut sont uniquement des constantes
du banc identiques partout, sans adresse distante ou identifiant de client.

Les enfants n'héritent pas de tout l'environnement du superviseur : seuls les
noms explicitement déclarés pour chaque fonction sont transmis. La fonction
configuration montre la présence d'un secret synthétique, jamais sa valeur.
Les tests n'injectent aucune configuration dans l'application. Les variables et
secrets viennent des deux fichiers réels de cellule. Le parcours de secret
présent fait échouer la campagne si la cellule n'en fournit pas. Le banc peut démarrer
sans secret, avec l'authentification métier désactivée et clairement signalée.

### Preuves et limites

La campagne complète couvre les contrats présents : nominal, refus, bornes,
authentification configurée et absente, allowlist d'environnement, saturation
réelle, logs, arrêt/reprise, persistance du worker, démarrage sur manifestes
invalides et défauts réels de stockage. Les fautes de disque et de manifeste
sont produites sur des conteneurs et volumes isolés portant la même image,
jamais sur les données du service. Les corps métier sont des objets JSON,
pas des tableaux ou scalaires. Le signal de lancement suit la résolution du
handler. La santé rend les admissions réelles pour observer la saturation.
L'arrêt ferme l'admission, tue les enfants et vide les files ; les clients
interrompus peuvent recevoir une erreur de transport.

Les tests sont exclusivement E2E et les campagnes séquentielles. Un conteneur
client séparé appelle par HTTP le service réellement déployé, sans import
applicatif, serveur privé, contexte fabriqué, mock ou interception réseau.
Les compteurs, caches et jobs acceptent un identifiant applicatif ; chaque
campagne crée et supprime ses propres ressources via les véritables routes.
Le relais appelle des pairs locaux réels limités à une liste (echo, failure,
sleep) ; la preuve d'erreur utilise une vraie exception du handler failure.
Les erreurs de saisie et les corps trop volumineux sont vérifiés par HTTP.

Une preuve distincte recrée le vrai conteneur et relit ses données par HTTP.
L'attendu est conservé dans un volume du client de test, séparé des volumes
applicatifs. Les traces ne contiennent ni jeton métier ni corps d'erreur.
Les contrôles statiques du manifeste ne sont pas des preuves fonctionnelles
E2E d'un adaptateur de déploiement encore absent.

Les limites Docker portent sur le banc complet, pas individuellement sur ses
fonctions. Le budget mémoire du manifeste reste un contrat à qualifier par le
futur moteur ; il ne doit jamais être présenté comme un quota appliqué par
l'exécuteur de référence. Même limite pour min/max instances, cron, stockage
à quota dur et passage à zéro : non implémentés.

## Déploiement DEV

Sources : ce dépôt uniquement. Cible : cellule `infra-serverless` décrite dans
`dev-spark.md`, accessible par le rebond documenté. Répertoire dédié prévu :
`/srv/p2enjoy-serverless/qualification`. Docker est piloté par `spark-docker`.
Les notes se proposent sous `/etc/spark/notes/*.md.?`, sans modifier les notes
gérées par la console. Aucun accès d'administration à la FORGE.
