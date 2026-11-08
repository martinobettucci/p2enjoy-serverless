# Contrat de la plateforme

Ce document spécifie la version en développement. L'état de réalisation et les
preuves sont portés par [le backlog](BACKLOG.md). Le banc de qualification
constitue une charge indépendante ; sa validation ne clôture pas la plateforme.

## Organisation

Un namespace contient des services. Un service correspond à un déploiement
`serverless.yml` et contient des fonctions. Chaque objet possède un UUID stable
et un nom unique dans son parent. Une fonction garde son UUID, ses données et
son historique lors d'un changement de code. Les révisions sont immuables.

La console et l'API de gestion partagent les mêmes règles d'autorisation.
Les namespaces et services sont administrés par le SSO ; leurs fonctions
peuvent également être gérées par un jeton du service. Les lectures présentent
les noms de secrets et leur présence, jamais leurs valeurs enregistrées.

Les variables et secrets communs appartiennent au service ; les fonctions
portent leurs surcharges explicites. L’adaptateur doit préserver cette séparation.
Les adresses d’appel sont calculées depuis les domaines du SPARK qui ciblent
la passerelle et les événements HTTP de la fonction. Le
[contrat de configuration et d’adresses](SERVICE_CONFIGURATION_URLS.md)
précise les écarts actuels et les preuves requises dans SLS-031 et SLS-066.

## Identité et autorisations

Connexion au SSO réel selon `sso.md` : Authorization Code, PKCE S256, state,
nonce, signature JWKS, issuer exact, expiration et `azp` du jeton d'accès.
La console exige `verified` et `admin`. Le cookie de session serveur est
HttpOnly, Secure, SameSite=Lax ; les mutations de session exigent une preuve
CSRF et une origine conforme. La déconnexion invalide la session serveur.

Un administrateur crée des jetons opaques, montrés une seule fois, dont seule
l'empreinte est conservée. Chaque jeton appartient à un service, possède une
expiration facultative, une liste CRUD et éventuellement une liste de fonctions
autorisées. Une restriction à des fonctions exclut Create. La révocation prend
effet pour les nouvelles requêtes ; renouveler révoque l'ancien jeton.

- Create : création d'une fonction et de sa première révision.
- Read : consultation des ressources du service, configurations expurgées,
  journaux et invocation ; une invocation peut produire des écritures métier.
- Update : configuration, secrets, nouvelle révision, rollback et cache.
- Delete : désactivation et suppression des fonctions, avec archivage durable.

L'en-tête `X-Serverless-Token` porte cette identité ; la passerelle le consomme
avant le handler. `Authorization` reste l'identité métier de l'application.
Les cookies d'administration ne servent pas de jeton d'invocation public.

## Origines et réseau

Le service configure des origines exactes (schéma, hôte, port), des IP ou CIDR
IPv4/IPv6 et une combinaison ET/OU. Listes vides : critère désactivé. Deux
critères actifs : ET par défaut. Aucun critère actif : jeton seul. Une origine
absente ou `null` ne satisfait jamais un critère origine actif. Une origine
n'atteste pas l'identité d'un client non navigateur.

Le préflight vérifie origine, IP, méthode et en-têtes sans exiger un jeton que
le navigateur n'envoie pas dans OPTIONS. Il n'exécute pas le handler. Chaque
requête effective revérifie identité et politique. CORS est produit par la
passerelle, qui ne laisse pas le handler élargir la politique du service.
La source IP vient du pair TCP ; une chaîne Forwarded/X-Forwarded-For n'est
utilisée que depuis un proxy explicitement approuvé par la configuration.

## Adaptateur

L'adaptateur lit le YAML sans exécuter ses plugins. Il conserve les handlers
`module.export`, les noms, l'héritage provider/fonction et les exclusions de
packaging. Il accepte `environment`/`env`, `secret`, `memorySize`/`memoryLimit`,
`timeout` numérique ou en secondes, `minScale`/`maxScale`, les endpoints HTTP
implicites et les schedules cron à cinq champs. Les mappings locaux vides ou
null conservent l'héritage. Les options non prises en charge sont signalées
avant upload, sans prétendre qu'elles ont été appliquées.

Les artefacts contiennent le code réellement exécutable et ses dépendances.
Le runtime cible et l'architecture font partie du contrat de build ; un addon
natif compilé pour une autre ABI n'est pas réputé portable. Node 24 est la
cible initiale. Un manifeste Node 20 demande une conversion explicite et une
qualification de l'artefact, jamais un alias silencieux.

Le code uploadé est extrait dans une nouvelle révision : chemins relatifs
validés, limites d'archive et de nombre de fichiers, rejet des liens et des
doublons ambigus, présence de l'export vérifiée par le vrai runtime. Une erreur
de déploiement conserve la révision active. Les secrets sont chiffrés au repos.

## Exécution

Une instance est un conteneur Docker isolé, avec une seule invocation active.
Un nouveau processus applicatif est créé pour chaque invocation ; le conteneur
peut rester prêt, mais les variables globales du handler ne sont pas conservées.
Le contexte expose un temps restant qui correspond à la deadline du moteur.
Promise et callback : la première terminaison gagne. La passerelle fournit un
événement HTTP Lambda v1, un corps chaîne et le support des réponses binaires.

Les limites CPU, RAM, processus, concurrence, instances min/max, file d'attente,
durée d'invocation et durée d'inactivité sont distinctes. L'admission réserve
atomiquement les ressources avant démarrage. La marge du contrôle est exclue
du budget des fonctions. Un timeout recycle le conteneur entier pour terminer
les descendants. Docker ne redémarre pas seul une instance retirée du moteur.

Un redéploiement laisse finir les appels déjà admis sur l'ancienne révision
dans leur deadline ; les suivants utilisent la nouvelle. Un crash du contrôle
entraîne une réconciliation des seuls conteneurs étiquetés comme lui appartenant.
Une invocation interrompue n'est jamais rejouée automatiquement : ses effets
métier peuvent avoir eu lieu. Les crons utilisent UTC par défaut, un événement
HTTP synthétique avec corps JSON et aucune récupération en rafale après arrêt.

## Stockage

Chaque fonction configure séparément un volume données et un volume cache,
chacun avec un plafond. Le mode données sérialise par défaut les invocations
de la fonction, y compris entre révisions. Un mode partagé explicite permet
la concurrence lorsque le code assure sa cohérence. Les volumes restent liés
à l'UUID lors d'une extinction, d'un redéploiement ou d'un rollback de code.

La suppression désactive la fonction et archive ses données. La purge des
données archivées est une opération distincte réservée à l'administrateur.
Le cache peut être vidé explicitement après drainage des instances ; aucune
purge automatique des données métier. Une réduction sous l'usage est refusée.

Le plafond disque doit être imposé au chemin d'écriture, avec une erreur
observable par le handler. Une simple mesure périodique ne suffit pas.
L'unité SLS-010 qualifie un proxy FUSE sur les fichiers natifs du SPARK. La
comptabilité porte sur la taille logique arrondie à 4 Kio, plus 4 Kio par
entrée. Elle borne aussi les fichiers vides et répertoires ; ce compteur
n'est pas une mesure des blocs physiques ZFS. Le budget global garde une marge
pour les métadonnées, images, journaux et sauvegardes du SPARK.

Un processus possède exclusivement chaque volume avec un verrou système. Il
sérialise les mutations et compte les inodes supprimés encore ouverts jusqu'au
dernier close, y compris pour les répertoires supprimés. Les extensions sont
réservées avant écriture/truncate ; les
écritures partielles sont recomptées. Les liens, fichiers spéciaux, xattrs,
préallocation et ioctl sont refusés ; l'accélération de copie côté filesystem
est désactivée. Les copies ordinaires et le repli read/write du noyau pour
copy_file_range restent soumis au quota. Le passthrough noyau et le cache
d'écriture sont désactivés. Les fichiers utilisent des accès directs FUSE ;
les mappings mémoire partagés ne font pas partie du contrat initial.

Les fichiers natifs conservent leur format et les opérations rename/fsync
sont déléguées au filesystem du SPARK. Au remontage, un scan reconstruit le
compteur, refuse les types interdits et refuse une limite inférieure à l'usage.
La preuve vérifie le montage utilisateur, l'accès Docker rootless, la
saturation, les voies alternatives, le remontage et l'interruption. Aucun
runtime ne doit démarrer sur un simple répertoire lorsque son montage manque.

## Exploitation et preuves

Contrôle Python, stockage de métadonnées SQLite WAL local, API unique et
console React/Vite. Le contrôle est seul détenteur du socket Docker. Les
fonctions ne montent ni ce socket, ni les données ou secrets du contrôle.
Le contrôle utilise le réseau hôte du SPARK afin de conserver son pair TCP,
alors que les fonctions restent dans leurs réseaux Docker. Le transport des
commandes d'exécution passe par l'API locale Docker ; il ne suppose pas que
les adresses internes rootless soient routables depuis le SPARK.
Les journaux portent service, fonction, révision et invocation ; ils sont
bornés et accessibles selon les mêmes ACL. Les métriques distinguent usage,
allocation et plafond. Toutes les valeurs propres au SPARK viennent des deux
fichiers de cellule ; les variables de fonctions sont des données applicatives.

Chaque unité inclut ses scénarios E2E nominaux et négatifs sur les vrais
composants, exécutés en série. Les parcours UI commencent à l'accueil et
passent par le véritable SSO. Les preuves comportent les empreintes des sources,
les versions d'images et des résultats sans secrets. Une fonctionnalité sans
preuve reste en cours ; l'absence d'un prérequis ne produit pas de test ignoré.
