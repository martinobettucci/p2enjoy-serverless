# Journal de cadrage

## Reprise complète et import du socle — 2026-11-05

Le responsable exige de tester TOUT le comportement livré, sans mock ni test
ignoré, et signale l'absence de l'import réel de la méthode. La campagne
17/19 reste une preuve partielle historique. Décision : import opérationnel
du socle vérifié, couverture des erreurs, limites, saturation, configuration,
stockage, arrêt/reprise et logs, uniquement sur le DEV autorisé.

## 2026-11-05 — Périmètre et accès

### Exigences confirmées par le responsable

1. Utiliser la méthode `P2Enjoy/software-factory-base`, hors module de formation
   réservé aux séminaires.
2. Construire une plateforme serverless Docker compatible avec l'exploitation
   et le déploiement des projets P2Enjoy ; la compatibilité intégrale AWS est
   hors objectif.
3. Déployer dans un SPARK de FORGE. Réutiliser l'exposition des URL et les
   sauvegardes déjà prises en charge dans l'environnement du responsable.
4. Gérer depuis l'UI les namespaces, fonctions, allocations, mémoire, espace
   permanent par ID de fonction et durées avant extinction.
5. Conserver les handlers et réutiliser `serverless.yml` avec un adaptateur
   P2Enjoy.
6. Authentifier les administrateurs par le SSO avec le rôle OAuth `admin`.
7. Permettre aux administrateurs de créer des jetons de plateforme limités à un
   service, portant des droits CRUD. `Create`/`Update` couvrent fonctions,
   upload du code, variables, secrets et configuration ; `Delete` permet la
   suppression ; `Read` permet l'invocation.
8. L'authentification de la plateforme précède le handler et reste indépendante
   de son éventuelle authentification métier. John Dalia devra évoluer pour
   fournir le jeton de plateforme.
9. Ne jamais lancer l'application avec un profil PREPROD ou PROD.
10. Couvrir les données métier et le cache reconstructible par des modes de
    stockage configurables par fonction. Le responsable a confirmé les deux
    usages ; aucune politique de purge automatique n'en découle encore.
11. Permettre à chaque service de restreindre les appels à une origine web
    précise, comme `https://app.johndalia.com`, et/ou à une adresse IP précise,
    en complément de l'authentification plateforme.

### Sources examinées et faits observés

- Méthode : README, AGENTS et CLAUDE de
  [software-factory-base](https://github.com/P2Enjoy/software-factory-base).
  La méthode distingue références globales et compagnons propres au produit,
  demande de persister les décisions avant le code et de vérifier le parcours
  réel de l'interface. Aucun contenu de formation n'a été importé.
- `../johndalia/jd_serverless/README.md`, `package.json`,
  `serverless.example.yml` : fournisseur actuel Scaleway, runtime déclaré
  `node20`, 13 fonctions déclarées, handlers CommonJS, HTTP et deux crons,
  mémoire 128/256 Mio, durées déclarées 10/120/300 secondes, min/maxScale.
  Les valeurs de secrets des sources ne font pas partie de ce cadrage.
- `../johndalia/jd_serverless/src/lambdas/syncWorker/handler.js:80` : le worker
  utilise `context.getRemainingTimeInMillis()` pour arrêter de prendre du
  travail avant son échéance. L'arrêt du moteur doit correspondre au temps
  annoncé au handler.
- Même fichier, lignes 201–218 : un effet blockchain peut précéder la
  confirmation en base. Un arrêt ne prouve donc pas l'absence d'effet métier.
- `../johndalia/jd_frontend/src/helpers/serverCall.jsx:58` et
  `src/Global/resources/admin.jsx:109` : les appels existent côté navigateur ;
  l'identité métier est transmise dans le corps ou dans `Authorization`.
- `../johndalia/jd_serverless/src/libs/commons.js:26` et `:85` : CORS et appels
  entre fonctions devront aussi intégrer le mécanisme d'accès plateforme.
- Aucun usage direct de disque persistant n'a été repéré dans les handlers
  métier inspectés. Cette capacité demandera des scénarios de validation
  propres à la plateforme.
- `../spark-environment/README.md` et `docs/DAT.md:90` : un SPARK est une
  cellule Incus avec son propre Docker. La pile serverless peut s'y installer
  avec Compose et piloter les conteneurs de fonctions dans ce Docker.
- `../spark-environment/docs/manuel/M7-domaine.md` : contrat domaine → SPARK
  → port. Les certificats wildcard nécessitent une validation DNS qui n'est
  pas réalisée par le produit décrit ; ne pas présumer ce mécanisme disponible.
- `../spark-environment/docs/DAT.md:130` : le quota disque documenté porte sur
  le rootfs du SPARK. Un quota dur par fonction à l'intérieur de la cellule
  n'est pas démontré par cette lecture.
- [sso.md](sso.md), fourni dans ce projet : découverte OIDC, issuer exact du
  realm `lelabs`, rôles dans `realm_access.roles`, plancher `verified`, droits
  d'administration pour `admin`, possibilité de restreindre l'application aux
  admins, Authorization Code avec PKCE S256, secret client côté serveur.

### Propositions à discuter, non validées

- Hiérarchie possible : namespace → service correspondant à un déploiement
  `serverless.yml` → fonction stable → révisions et instances Docker.
- Passerelle d'invocation permanente, API/UI de gestion, moteur Docker isolé
  et état durable. Le composant d'exécution serait le seul à piloter Docker.
- Authentification plateforme via un en-tête distinct, par exemple
  `X-Serverless-Token`, consommé par la passerelle ; conserver l'en-tête
  `Authorization` métier. Aucun nom d'en-tête n'est encore contractualisé.
- Jetons opaques révocables, secrets montrés une fois, stockage de leur
  empreinte ; références de secrets visibles sans lecture de leur valeur.
- Séparer délai d'attente, délai de démarrage, durée d'invocation, extinction
  après inactivité et grâce d'arrêt. Le superviseur doit pouvoir arrêter une
  fonction même si son processus ne coopère pas.
- Une invocation active par conteneur au départ ; concurrence globale et
  nombre d'instances configurables. Pour un disque mutable partagé, politique
  d'écriture explicite entre invocations et entre versions.
- Volume attaché à un identifiant stable, conservé après extinction et
  redéploiement. Un rollback de code ne restaure pas automatiquement les données.
- Admission suivant budgets SPARK, namespace et fonction, avec marge pour le
  contrôle, les images et les logs ; distinguer plafond, allocation et usage.
- Reprise après redémarrage par réconciliation de l'état durable et des
  conteneurs existants ; distinguer résultat inconnu et échec certain avant
  tout éventuel rejeu.

### Questions produit ouvertes

- Relations entre namespace et service ; portée exacte des opérations de
  consultation et des opérations CRUD sur les fonctions.
- Jeton d'invocation navigateur : clé publiable qui identifie l'application,
  ou jeton confidentiel conservé derrière un relais serveur. Une clé remise au
  navigateur ne peut pas être considérée comme secrète.
- Un jeton Read couvre-t-il toutes les fonctions de son service, ou peut-il
  être restreint à certaines fonctions ? Ce point importe notamment pour
  distinguer fonctions appelées par le public et traitements internes.
- Politique de suppression des données persistantes et concurrence d'écriture.

### État des vérifications et persistance

Lecture statique seulement. Aucune application, aucun test, build, migration,
déploiement ou profil PREPROD/PROD n'a été exécuté. Aucun accès distant à une
FORGE et aucune configuration SSO n'ont été réalisés. Les propriétés décrites
dans les dépôts de référence ne constituent pas une mesure actuelle de la cible.

Les décisions confirmées sont enregistrées dans ce journal et le README. Aucun
code applicatif n'a été écrit. `git status` a indiqué que le répertoire de
travail n'était pas un dépôt Git exploitable dans le contexte présent ; aucun
commit ni push n'a été réalisé.

## 2026-11-05 — Restrictions d'origine et d'adresse IP

### Demande confirmée

Le responsable demande un contrôle par service des origines web et/ou adresses
IP autorisées. Ces restrictions s'ajoutent aux jetons et aux droits du service.

### Sémantique proposée, à distinguer de la demande confirmée

- L'UI expose des listes d'origines exactes et d'adresses IP, avec une extension
  possible aux plages CIDR IPv4/IPv6.
- Une origine désigne protocole, hôte et port. Elle ne désigne pas un chemin de
  page ; aucun contrôle de chemin par `Referer` n'est proposé comme garantie.
- Pour plusieurs entrées d'une même liste, une correspondance suffit.
- Si les deux critères sont activés, proposer le mode **ET** par défaut,
  avec un mode **OU** explicitement sélectionnable. En mode OU, satisfaire
  l'un des critères suffit ; aucune garantie du critère non satisfait ne doit
  alors être annoncée.
- Une invocation exige toujours un jeton valide, le droit Read sur le service
  ciblé et la satisfaction de la politique d'accès. Une origine ou une IP
  autorisée ne remplace jamais le jeton.
- Un critère activé avec une liste vide ne doit pas devenir permissif : refuser
  cette configuration. Pour la branche origine, une valeur absente, `null`,
  malformée ou multiple échoue. En mode OU, seule une correspondance IP
  explicite peut alors satisfaire la politique.
- Le contrôle se fait dans la passerelle avant mise en file et démarrage d'un
  conteneur. Les refus sont journalisés sans jetons ni secrets. Les en-têtes
  CORS autorisent uniquement une origine explicitement admise.
- Le préflight CORS valide est traité par la passerelle sans invocation du
  handler et sans exiger le jeton absent du préflight. Vérifier origine,
  méthode, en-têtes et les contraintes réseau applicables. La requête réelle
  repasse tous les contrôles. Ne pas dispenser tous les appels OPTIONS
  d'authentification.
- Déterminer l'IP cliente depuis la connexion ou une chaîne de proxies
  explicitement approuvés. Ne pas accepter un `X-Forwarded-For` arbitraire ni
  assimiler l'IP de Caddy à celle de l'appelant. Protéger les chemins directs
  qui contourneraient la passerelle et cette chaîne de confiance.

### Limites utiles au choix produit

Un navigateur impose l'en-tête Origin à son code web, mais un client HTTP hors
navigateur peut déclarer cette valeur lui-même. Le contrôle d'origine et CORS
ne prouvent donc pas qu'un appel a réellement été émis par le site autorisé.
Une clé distribuée dans le navigateur reste publiable, pas confidentielle.

Un appel direct depuis le navigateur porte l'IP publique de l'utilisateur ou de
sa sortie réseau, pas celle de l'hébergeur de `app.johndalia.com`. Une restriction
à l'IP du serveur applicatif suppose que l'appel passe effectivement par ce
serveur. Une origine web et une IP réseau ne désignent pas le même objet.

### Références et état

- [MDN — Origin](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin)
  : composition de l'origine, absence de chemin, cas `null` ou absent.
- [MDN — CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
  : préflight, contrôles navigateur et requête réelle.
- [Caddy — trusted proxies](https://caddyserver.com/docs/caddyfile/options#trusted-proxies)
  : confiance des proxies et extraction de l'IP cliente.

Modification documentaire uniquement ; politique non implémentée et non testée.
Aucune application ni profil PREPROD/PROD lancé.

## 2026-11-05 — Application témoin indépendante et SPARK DEV

Le responsable autorise l'usage du seul SPARK décrit dans `dev-spark.md` pour
les déploiements et tests DEV, interdit toute modification de FORGE et précise
que John Dalia est une référence uniquement : aucun déploiement ni modification
de son code. La première unité est une application synthétique de qualification
dans ce dépôt, QLF-001, spécifiée dans DAT avant implémentation.

Décision d'implémentation : handlers Node.js 24 CommonJS originaux, manifeste
YAML, exécuteur de référence à processus enfants, accès HTTP local uniquement,
volumes distincts pour données et cache. Le futur moteur Docker par fonction
reste hors de cette unité. Aucun secret de déploiement n'est nécessaire au
démarrage. Les données d'authentification de démonstration sont publiques et
strictement synthétiques.

Lecture distante effectuée sur le SPARK autorisé : briefing actuel, Docker
rootless 29.9.3, cgroup v2 avec pilote systemd, absence de conteneur existant et
de route publique. Le rebond SSH n'exécute aucune commande sur la FORGE.
Le répertoire de travail local n'est toujours pas un dépôt Git exploitable ;
les spécifications sont persistées sur disque avant le code, sans commit/push.

### Résultat de QLF-001

Le code original est créé localement dans `qualification/`, puis copié dans
le répertoire dédié du SPARK. Les empreintes de seize fichiers d'exécution
locaux et distants correspondent. Aucun fichier client n'est transféré.

Le build est réussi avec Node 24.22.2, Docker rootless 29.9.3 et YAML 2.9.1
verrouillé ; l'audit npm ne relève aucune vulnérabilité connue au moment du
contrôle. La revue a conduit à corriger le rejet HTTP 413 (ne pas détruire le
flux avant la réponse) et à propager le statut d'erreur du pair de `relay`.
Les tests vérifient aussi l'entrée effective du handler avant interruption et
une contention de deux écritures dans un seul scénario dédié.

Campagne finale séquentielle : 7 tests unitaires et 14 tests HTTP réussis ;
manifeste de douze fonctions valide ; smoke de la pile déployée réussi ;
compteur à 2 et génération du cache conservés après recréation du conteneur.
Le service est sain, exécuté comme `node`, limité à 384 Mio, 0,5 CPU et 96
processus, publié uniquement sur 127.0.0.1:18080 dans le SPARK. Aucune route
publique. Le temps d'exécution et la persistance sont prouvés dans ce banc,
pas dans un moteur de plateforme complet.

Les trois propositions README.md.?, CONTRIBUTORS.md.? et INSTALL.md.? sont
déposées et relues dans la cellule, sans remplacer les notes officielles.
Aucune variable, secret ou route supplémentaire n'est proposé. Les deux
env_file de cellule sont respectés ; aucun .env, ENV/ARG de configuration
ou environment Compose. Aucune commande d'administration sur la FORGE,
aucun démarrage PREPROD/PROD et aucune action sur le code du client.

Preuve : `docs/evidence/qualification-dev-2026-11-05.json`. Pas de commit/push,
faute de dépôt Git exploitable ; QLF-001 reste [~] pour cette formalité de
clôture, malgré ses preuves techniques réussies.

## 2026-11-05 — Qualification exclusivement E2E sans mocks

Le responsable interdit tout mock et exige que chaque fonctionnalité testée
soit vérifiée E2E sur du vrai code. Cette règle remplace la stratégie de tests
unitaires et de serveur privé utilisée précédemment. L'audit a identifié une
doublure HTTP renvoyant systématiquement 429 dans le test du relais : elle est
retirée. Les anciennes preuves ne constituent pas la nouvelle qualification.

Décision avant modification : client de tests séparé, appels HTTP au conteneur
effectivement déployé, ressources applicatives nommées créées/supprimées par
leurs vraies routes, et vraie exception d'une fonction pour vérifier le relais.
Retirer l'authentification par marqueur public ; employer un vrai jeton de
configuration de cellule. En l'absence de configuration, signaler les parcours
non qualifiés au lieu de fabriquer des secrets ou de simuler une connexion.
Les fonctionnalités de plateforme absentes restent non testées.

### Preuve intermédiaire de la conversion — remplacée par la campagne complète

Le faux pair HTTP et les tests par appel direct sont supprimés. Le client ne
démarre et n'importe plus l'application. Il utilise un conteneur distinct sans
montage des volumes applicatifs. Compteurs, caches et jobs sont manipulés par
leurs véritables API avec des identifiants uniques et nettoyés par HTTP.
Le worker calcule réellement des résultats PBKDF2, persiste le job dès son
acceptation puis ses checkpoints ; relay appelle les vrais pairs echo,
failure et sleep. Aucun substitut de fournisseur ou serveur de test.

Lors de cette campagne intermédiaire : 19 parcours enregistrés,
17 réussis, zéro échec, deux explicitement non qualifiés car les secrets réels
QUALIFICATION_BUSINESS_TOKEN et QUALIFICATION_SYNTHETIC_SECRET manquent.
Le smoke de la pile et la conservation des données/cache après une vraie
recréation ont réussi. Le snapshot attendu appartient uniquement au client.
Les seize empreintes de sources locales et distantes correspondent.

Les trois propositions de notes sont mises à jour et vérifiées. La variable
QUALIFICATION_PUBLIC_LABEL et les deux secrets sont proposés dans les fichiers
.? de la cellule, sans écrire les fichiers gérés par le plan de contrôle et
sans inventer de valeur de secret. Aucune route publique. La documentation du
SPARK impose une configuration durable depuis sa console ; les parcours
positifs correspondants restent non qualifiés jusqu'à cette configuration.

Preuve intermédiaire historique : `docs/evidence/qualification-dev-2026-11-05-e2e.json`.
L'ancienne preuve est marquée historique avec sa portée corrigée. Aucune
fonctionnalité de plateforme encore absente n'est présentée comme vérifiée.
Aucun code client modifié/déployé, aucune administration de FORGE, aucun
profil PREPROD/PROD, aucun commit ou push.


## 2026-11-05 — Méthode intégrée et campagne complète réussie

Le socle au commit 886ba5a28a834a5f08fd1a01ec8dd78787317559 est importé :
26 fichiers suivis upstream plus AUTOMATION provenant de la copie locale,
avec provenance explicite de ce dernier. Formation, publication Pages et
compagnon de design pédagogique exclus. Les règles locales imposent E2E
réels, zéro skip, DEV seul et un seul opérateur de tests. Les profils verifier
sont adaptés en analyse lecture seule. Le responsable a initialisé Git ; les
hooks standard sont activés. Le harnais des vrais scripts Git obtient 45
succès et zéro échec, avec commits et pushes vers des dépôts temporaires locaux.

Les secrets QUALIFICATION_BUSINESS_TOKEN et QUALIFICATION_SYNTHETIC_SECRET
ont été générés et configurés par l'API de la console locale déjà accessible,
au seul scope Spark infra-serverless ; le label public est configuré également.
Aucun paramètre global, service FORGE ou autre Spark n'a été modifié. Le banc
a été recréé pour relire les fichiers de cellule. Aucun secret n'est conservé
ici. Le défaut sans configuration a été observé avant configuration puis
retesté par un vrai déploiement sans déclaration de variables de fonction.

L'élargissement E2E a révélé un blocage de boucle réseau du client dû au calcul
synchrone de tous les résultats attendus ; ce calcul est désormais asynchrone,
sans retry d'invocation. Les corps métier non objets sont refusés, le signal
de lancement suit le chargement du handler et l'arrêt est revérifié avant fork.
La fréquence de vérification des délais HTTP est explicite ; les expirations
réelles du corps et des en-têtes sont prouvées.

Campagne complète : 38 tests HTTP réussis, 0 échec, 0 ignoré ; 28 contrôles
Docker/lifecycle/pannes réussis ; smoke réussi ; recréation avec compteur,
cache et checkpoint worker conservés puis reprise complète réussie. Les vrais
logs et processus, les cgroups, les 21 manifestes invalides, les fautes de
stockage et le refus réel de fork sous plafond de processus sont vérifiés.
Les 19 empreintes de fichiers exécutables/configuration locales et distantes
coïncident. Un seul conteneur du banc reste actif, sain, sans invocation ni
admission en cours. Les trois propositions de notes sont mises à jour et
relues ; leurs fichiers officiels restent gérés par la console.

Preuve actuelle : docs/evidence/qualification-dev-2026-11-05-complete.json.
Les preuves 17/19 sont historiques. La matrice porte sur le banc réellement
livré ; elle ne vaut ni couverture de lignes à 100 %, ni qualification du SSO,
de l'UI et des fonctions de plateforme encore non implémentés.

## 2026-11-05 — Objectif autonome et contrats de plateforme

L'objectif actif est la livraison complète du contrôle, du runtime et de la
console, avec leurs preuves E2E sur le SPARK. Les anciennes propositions de
cadrage sont tranchées par PLATFORM.md : namespace/service/fonction UUID,
jetons X-Serverless-Token, restriction facultative aux fonctions, Read incluant
consultation et invocation, archivage durable à la suppression, purge admin,
ET par défaut pour les politiques origine/IP, exclusivité des données par
défaut et partage explicite, révisions immuables et aucun rejeu après crash.

Le contrôle Python/SQLite est retenu pour la cellule unique ; l'ordonnancement
sera centralisé avec réservations atomiques courtes. Un processus applicatif
neuf par invocation évite les connexions globales périmées ; le conteneur peut
rester prêt. Un timeout recycle tout le conteneur pour supprimer ses descendants.
La compatibilité de référence inclut les champs Scaleway, HTTP implicite,
cron à cinq champs, héritage env/secret et artefacts compilés avec dépendances.
Node 20 n'est pas assimilé silencieusement à Node 24.

Les revues indépendantes ont identifié le quota dur comme risque d'hébergement.
/dev/fuse et fusermount3 sont présents dans le SPARK. Décision : qualifier un
filesystem de taille bornée et son montage Docker avant de retenir le mécanisme.
SLS-010 couvre cette preuve et les prérequis SSO. Les autres unités sont
persistées dans BACKLOG avant leur implémentation. Le SSO public répond ; le
domaine envisagé ne résout pas et la console locale ne répond plus sur 5175.
Aucune preuve de plateforme n'est déduite du banc existant.

### Choix du quota pour SLS-010

Les sources primaires confirment que fuse2fs ne journalise pas ses écritures,
et que NTFS-3G documente des limites de récupération et de renommage. JuiceFS
synchronise les usages entre clients avec délai. Ces options ne sont pas
retenues pour imposer le contrat de cette cellule. Choix : proxy go-fuse
v2.12.1, un propriétaire par volume, octets logiques arrondis et coût par entrée,
comptabilité d'inodes ouverts supprimés, contrôle avant mutation et fichiers
natifs conservés. Les fonctionnalités POSIX hors contrat sont explicitement
refusées. La preuve inclura crash, remontage, saturation et Docker rootless.
Sources : dépôts primaires hanwen/go-fuse, tytso/e2fsprogs, tuxera/ntfs-3g ;
JuiceFS docs/en/guide/quota.md. L'implémentation n'est pas encore qualifiée.

### Premier build et diagnostic de montage

Le build réel réussit. La première campagne échoue avant montage, sans skip.
La trace strace dans le SPARK montre dup3(socket,3,0) réussi puis le descripteur
3 absent après exec du helper fusermount3 ; la cause de cette fermeture reste
indéterminée. Décision réversible : qualifier le mode de montage direct fourni
par go-fuse, sous spark-docker avec la seule capacité de montage accordée au
processus. Aucun changement de politique de sécurité de FORGE ni de runtime.
La revue identifie également le transfert ioctl hérité des répertoires ; son
refus explicite et sa preuve sont inclus dans le composant.

### Stockage qualifié sur le SPARK

Le montage direct avec la capacité de montage limitée au processus fonctionne
sous spark-docker. La revue a fermé le transfert ioctl des répertoires et les
réservations après mutation ; les tailles maximales sont maintenant réservées
avant syscall. La preuve a reproduit un autre défaut : un répertoire supprimé
resté ouvert était décompté (0 au lieu de 4096 octets). Le handle de répertoire
conserve désormais sa référence jusqu'à Releasedir, en gardant fsyncdir natif.

La campagne finale passe 31 contrôles, zéro échec et zéro skip. Elle vérifie
quotas, concurrence, fichiers et répertoires ouverts supprimés, copies noyau
avec repli, restrictions POSIX, SIGKILL du démon, consommateurs existants et
nouveaux, remontage, données acquittées, configurations invalides et verrou
exclusif. Les six empreintes de sources locales/déployées correspondent.
Preuve : evidence/storage-dev-2026-11-05.json. Go 1.27.3, image et modules
épinglés. govulncheck v1.9.0 : zéro chemin ou paquet importé affecté ; un avis
x/sys Windows hors cible Linux, documenté dans le DAT.

Les propositions de cellule portent OIDC_CLIENT_ID, SERVERLESS_PUBLIC_URL,
OIDC_CLIENT_SECRET vide et la route serverless-dev.lelabs.tech vers 18090 TLS.
Les trois notes .? décrivent le composant qualifié et l'état de la plateforme.
Aucun montage de preuve ne reste actif. Le SSO nécessite encore la création du
client et le secret via l'interface externe ; demande d'accès envoyée au
responsable, sans bloquer la poursuite des unités indépendantes.

### Prérequis SSO et domaine appliqués ; démarrage de SLS-020

Le responsable a créé le client SSO et appliqué les propositions via la console.
Lecture actuelle des fichiers officiels : OIDC_CLIENT_ID, SERVERLESS_PUBLIC_URL
et OIDC_CLIENT_SECRET présents ; trois notes et route 18090 TLS appliquées.
Le fournisseur DNS porte le sous-domaine attendu, puis la résolution locale et
la connexion HTTPS réussissent (502, contrôle encore absent). Le callback est
accepté avec exigence PKCE ; l'échange de code volontairement invalide retourne
invalid_grant après authentification du client, ce qui valide ses identifiants
sans délivrer de session utilisateur. Aucun secret n'est enregistré au dépôt.
SLS-010 est clôturée pour ces prérequis et la preuve de quota ; le parcours de
connexion administrateur reste dans SLS-020/SLS-060.

SLS-020 est spécifiée avant implémentation dans CONTROL.md et SCHEMA.md :
API Python, migrations SQLite, sessions OAuth chiffrées, CSRF, objets et
jetons scoped CRUD. La politique réseau et l'administration des jetons restent
réservées au SSO ; les jetons limités à des fonctions ne changent pas les
variables globales d'autres fonctions. Pas de mode d'authentification de
secours pour les preuves.

### Premier contrôle DEV et revue de l'identité

Le contrôle répond désormais en HTTPS : santé 200, session anonyme 200,
namespaces refusés à 401. OIDC_ISSUER et SERVERLESS_MASTER_KEY ont été proposés
puis importés par l'API normale de la console, dans le seul infra-serverless.
Les dépendances Python sont verrouillées avec empreintes dans Python 3.14.
La revue détecte un callback Unicode qui produit 500 ; la reproduction HTTP
réelle le confirme. La correction conserve un format state base64url borné.
Les autres constats à traiter sont l'issuer exclusif du contrat, l'audit des
refus associés à une identité et la saturation des flows de connexion.

La console initiale rejoint SLS-020 afin que les preuves de gestion empruntent
l'entrée normale SSO. React/Vite suit la préférence du contrat global ; son
build est servi par le contrôle, ce qui conserve les cookies de même origine
et évite un second service d'interface. Les décisions de navigation et de
saisie sont persistées dans DESIGN_SYSTEM_APP avant leur implémentation.

La revue UI relève qu'une mise à jour complète issue d'un second onglet peut
réécrire une autre section devenue obsolète. La console transmet désormais
la version lue via If-Match et le serveur la compare après authentification,
avant la mutation. Un conflit conserve la saisie et les données actuelles.
Les champs d'une modale sont indisponibles pendant sa soumission pour qu'une
nouvelle frappe ne soit pas effacée par la fermeture de la requête précédente.

### Adresse cliente et saturation des connexions

La revue réseau établit que FORGE génère un reverse_proxy Caddy sans règle
personnalisée de confiance des en-têtes. L'adresse vue après Docker reste à
mesurer. RootlessKit 3.3.0 est installé sur le SPARK ; sa documentation annonce
la conservation TCP avec le driver builtin depuis v3, à condition de désactiver
userland-proxy dans Docker. La configuration du démon n'est pas encore changée.
Références primaires : [Docker rootless](https://docs.docker.com/engine/security/rootless/troubleshoot/)
et [pilotes RootlessKit](https://github.com/rootless-containers/rootlesskit/blob/master/docs/port.md).

Le contrôle retiendra le pair TCP par défaut, puis X-Forwarded-For uniquement
depuis des CIDR de confiance mesurés et injectés par la cellule. Ce même calcul
servira aux ACL et aux limites SSO : huit flows actifs et trente ouvertures par
minute par client, avec compteurs durables. Cette borne empêche un seul client
de réserver les 256 flows globaux. Les autres en-têtes d'adresse ne portent
aucune autorité. La qualification doit vérifier les falsifications sur la
vraie route et les appels directs ; un simple contrat de proxy ne suffit pas.

La mesure réelle confirme le risque : TLS public et loopback direct arrivent
tous deux de 172.19.0.1 ; seul TLS remplace le X-Forwarded-For falsifié par
l'adresse réelle. Cette adresse commune reste non approuvée. Le réglage
userland-proxy=false est retenu dans le seul démon rootless du SPARK, avec
reprise des deux conteneurs DEV et retour arrière si la preuve échoue.

L'essai userland-proxy=false échoue faute de br_netfilter visible ; aucun
contournement du garde Docker n'est appliqué. Après restauration, Compose down
puis up a recréé les deux réseaux devenus incohérents, sans retirer les volumes.
La santé des deux piles est rétablie. L'alternative host est ensuite qualifiée
sur le vrai contrôle dans une pile temporaire : pair 127.0.0.1 conservé et
namespace réseau identique au SPARK. Elle est retenue pour le contrôle seul.
La première tentative de ce probe lisait les env_file avec docker run, qui
conserve leurs guillemets ; elle a été corrigée en passant par Compose,
conformément au contrat de la cellule. Ce refus de configuration n'était pas
une défaillance du réseau hôte.

La pile permanente en réseau hôte passe les quatre mesures de provenance.
Le seul proxy approuvé est désormais 10.77.0.1/32, appliqué via la proposition
officielle du SPARK. Les six scénarios de limitation SSO passent, dont la
falsification d'en-têtes et le compteur conservé au redémarrage ; la campagne
publique (six groupes) et l'accueil navigateur (huit contrôles) repassent.
La fenêtre de connexion administrateur a expiré sans authentification. Les
preuves authentifiées restent en attente de cet accès ; aucune identité n'est
injectée pour les remplacer. Les pannes de configuration seront qualifiées
sur des conteneurs isolés de la même image et un état créé par cette image,
avec les deux fichiers officiels puis une altération ciblée du processus.

La revue de SLS-020 relève deux écarts corrigés dans le checkpoint : le refus
429 de connexion HTML était transformé en 303, et certains rapports de panne
ne distinguaient pas une interruption d'une campagne finie. Décision : garder
le statut/Retry-After à l'entrée login tout en servant le véritable accueil,
et enregistrer une fin explicite avec les échecs. Le retour OAuth conserve
sa redirection pour retirer code/state de l'URL. La panne de volume SQLite
readonly refuse effectivement le démarrage avec « unable to open database
file » lors de l'ouverture WAL ; l'attendu de preuve est aligné sur ce
diagnostic observé, sans changer le refus de l'application.

## Checkpoint du contrôle — 2026-11-06

Le code initial du contrôle et de la console est conservé dans le dépôt, avec
les pilotes E2E. Les sept rapports consolidés sont complets dans leur périmètre
et sans test ignoré ; SLS-020 reste ouvert pour la session et les parcours
administrateur. La comparaison SHA256 confirme les sources applicatives
effectivement déployées. Les dépendances npm et les 21 dépendances Python
verrouillées ne présentent aucun avis de vulnérabilité connu lors de l'audit.
L'auditeur Python isolé a nécessité un tmpfs exécutable pour ses modules natifs
et un cache explicite ; ces réglages ne concernent pas le contrôle déployé.

L'accueil, son état d'erreur et le refus 429 mobile sont inspectés visuellement.
Un vrai SIGKILL du client après sa première requête confirme que le rapport
précédent n'est plus réputé complet. Les trois notes officielles du SPARK sont
appliquées puis relues. Le tunnel local de sa console a été rouvert par son
API normale après expiration ; aucune administration de la FORGE.

La seule dépendance externe restante de cette unité est une connexion réelle
et les comptes nécessaires aux variantes de rôle SSO. Les opérations de
gestion préparées ne sont donc pas présentées comme validées. L'exploration
de SLS-030 précise les mappings de manifeste à formaliser pour poursuivre
les parties indépendantes. Aucun remote Git n'est configuré pour publier
les commits locaux.

## Révisions et packaging — 2026-11-06

Décisions SLS-030 : CLI Python avec PyYAML verrouillé et ZIP standard, sans
exécution de build ou de plugin ; manifeste de qualification explicite
serverless.platform.yml réutilisant les handlers originaux. Les motifs glob
ont un sous-ensemble documenté, les options non appliquées sont signalées,
et la conversion Node 20/22 vers Node 24 exige une option explicite.

La publication est atomique par fonction : candidat chiffré, upload borné,
validation Node dans Docker, relecture des droits et versions, puis transaction
de publication. Create permet de terminer la première révision ; Update sert
aux suivantes. La révision fige code/handler/événements ; un rollback conserve
les ressources et secrets courants. Une version de service protège aussi
les variables communes contre une course pendant l'import.

Le chargeur est commun à la validation et au futur runtime, avec résolution
CJS/ESM non ambiguë et propriétés propres seulement. L'import utilise les
vraies valeurs applicatives, un conteneur borné et sans réseau ni données
métier ; les connexions réseau doivent commencer dans le handler. Cela permet
de vérifier le vrai export tout en bornant les effets du chargement. La preuve
d'invocation restera nécessaire pour les dépendances importées tardivement.

La première CLI plan/package passe 24 scénarios réels. La revue a fait corriger
l'exclusion du manifeste sélectionné avec --config et de ses liens physiques,
la publication par descripteur de répertoire pour résister à son remplacement,
le quota explicite des volumes et les entiers YAML hors bornes. Une course
réelle à deux processus confirme qu'un lien substitué à la sortie ne détourne
pas les écritures. Le poste ne fournit pas ensurepip ; la vérification d'une
installation vierge se poursuit dans l'image Docker épinglée, sans installer
de paquet système sur le poste.

## Chargeur Docker — 2026-11-06

Le validateur Node est implémenté dans `runtime/` et piloté par la CLI réelle
`control/app/validator.py`. Le contrôle crée un socket Unix privé, monté
readonly dans le conteneur ; le superviseur retire une fois sa configuration,
charge dans un enfant et remet un résultat distinct des logs. Ce sens de
connexion ferme l'écriture non bornée que permettait un répertoire de socket
créé par le runtime. Le format CJS/ESM est constaté par Node, y compris pour
les fichiers JS sans type déclaré ; un namespace substitué par un export
then et un default synthétique CommonJS sont refusés.

La campagne finale passe 36 scénarios réels, zéro échec et zéro test ignoré.
Les sources du SPARK correspondent aux 36 fichiers comparés ; les trois
modules exécutables de l'image runtime correspondent aussi au dépôt. Le
contrôle et le banc restent sains ; aucun conteneur de validation ne subsiste.
La comparaison avec les quatre valeurs confidentielles connues ne relève
aucune occurrence dans ces sources. Les trois notes officielles de cellule
sont proposées, appliquées via sa console et relues.

Les revues et preuves font corriger la troncature des secrets complets puis
superposés, l'attente des connexions partielles avant leur annulation, et une
erreur de type dans un résultat privé malformé. Le masque conserve désormais
les offsets bruts avant la coupe. Une mesure réelle révèle aussi 65 538 octets
de logs binaires convertis pour une borne de 65 536 ; la correction retire
l'ultime caractère UTF-8 incomplet, et la régression passe. Les descendants
sont observés puis leur disparition vérifiée après destruction du conteneur.

Ce checkpoint ne change ni l'image ni les routes du contrôle en service.
L'extraction, l'upload, les révisions et la réconciliation après interruption
du contrôle restent dans SLS-030. La session SSO administrateur manque encore
pour leurs preuves authentifiées. Le registre d'incohérences hors unité est
vide ; les défauts relevés ici sont corrigés avec leurs preuves. Aucun remote
Git n'est configuré ; les checkpoints sont conservés localement.

L'aide de connexion de qualification ouvre désormais l'accueil et attend le
clic du détenteur du compte jusqu'à huit heures. Le flow SSO ne vieillit donc
plus avant ce clic. La fenêtre a atteint l'état prêt dans Chromium ; aucun
cookie administrateur n'est encore enregistré. Le script n'exportera que les
cookies du domaine de plateforme après une réponse de session authentifiée.

## Contrat du client OIDC créé — 2026-11-06

Le responsable transmet le llms.txt de `p2enjoy-serverless-dev`, conservé dans
OIDC_DEV.llms.txt. Le flux code, S256, scopes, callback et les rôles vérifiés
correspondent à l'implémentation lue. Le secret reste fourni par la cellule.
Le TTL annoncé de 300 secondes est une propriété du fournisseur : sa mesure
attend un jeton obtenu par une connexion réelle, et ne se déduit pas du TTL
local de session de huit heures. La découverte globale ne remplace pas une
preuve des règles particulières de ce client.

La revue relève trois points conservés explicitement dans SLS-020 : attente
de rôles distincte d'une erreur, azp de l'ID token, et 401 transitoire de kid
inconnu pouvant révoquer une session pendant la fenêtre anti-refresh. Ils
appartiennent à l'unité SSO ouverte et à sa campagne authentifiée ; la mise
à disposition de ce contrat ne les transforme pas en contrôles réussis.
Les sept groupes publics passent après ajout de la découverte obligatoire,
des clés asymétriques publiées et de la comparaison de la cible de redirection
à cette découverte. La preuve est conservée dans
`evidence/sso-contract-dev-2026-11-06.json`. Aucun composant de remplacement
n'intervient dans ces échanges HTTPS.

Le responsable confirme la route et les paramètres posés. Le contrôle live du
6 novembre à 00:09 UTC constate déjà le certificat Let’s Encrypt valide, la
route TLS vers 18090 et une santé 200. Les valeurs du conteneur et de ses deux
env_file correspondent, y compris les secrets comparés en mémoire : la
recréation serait inutile. Les sept groupes publics passent sur cet état.

## Extraction ZIP serveur — 2026-11-06

Le contrat est persisté avant implémentation : ZIP classique borné, lecture
centrale en flux, tailles réelles, écritures par FD et publication sans
écrasement. L'extracteur reçoit une image séparée pour qualifier ce composant
avant de le relier aux API de publication. La revue borne aussi le hash
d'entrée et vérifie les cas de nettoyage après renommage.

La campagne réelle reproduit le refus d'un DEFLATE valide de 65 537 octets :
le flux a encore une sortie interne alors que son entrée est consommée.
Une reproduction ciblée retourne zip_deflate_incomplete, sans candidat
résiduel. Le drainage rappelle désormais zlib tant que la sortie remplit son
tampon, y compris avec une entrée vide. Les six frontières autour de 64 et
128 Kio repassent, ainsi que les fichiers de 64 Mio.

La revue renforce aussi le pilote : inventaire attendu indépendant, borne de
chemin exactement 512 octets, suivi du conteneur de packaging, statut processus
en échec pour un rapport incomplet et contrôle des douze archives. Le lecteur
zipfile de Python ne sait pas relire le commentaire valide de 65 535 octets
contenant une fausse signature de fin ; l'attendu des fixtures provient donc
de leurs données originales. Le second lecteur reste utilisé sur les ZIP
produits par l'adaptateur réel. Ces corrections n'utilisent aucun mock.

Résultat final : 112 contrôles réussis, zéro échec, zéro test ignoré. La
campagne atteint réellement 64 Mio par fichier, 64 Mio de ZIP, 256 Mio au
total, 20 000 fichiers et 16 Mio de répertoire central. Elle vérifie la
saturation du disque, la préservation d'une destination concurrente,
l'échange du parent, la source augmentée pendant sa lecture et les douze
archives du packager chargées par Node. Six empreintes de sources sont
identiques entre dépôt et SPARK ; celle embarquée dans l'image est recoupée.
Les quatre secrets connus sont recherchés en mémoire dans le rapport sans
correspondance. Les deux services restent healthy ; aucun conteneur de preuve
ne subsiste. La preuve complète est `evidence/artifacts-dev-2026-11-06.json`.

SLS-030 reste ouvert pour les routes authentifiées, la publication, l'admission
globale et la reprise après interruption. Le contrôle permanent n'est pas
recréé. L'erreur matérielle de fsync après renommage n'est pas provoquée par
la campagne ; son traitement reste une propriété relue du code, explicitement
distinguée des pannes effectivement exercées. Aucun défaut hors unité ouvert
dans le registre d'incohérences à ce checkpoint.

La revue finale ne relève aucun défaut bloquant pour la CLI. Elle précise la
répartition entre CRC vérifié par l'extracteur et SHA256 calculés puis recoupés
par la preuve E2E. README, CONTRIBUTORS et INSTALL sont proposés dans les
fichiers .?, appliqués par la console du SPARK puis relus sans écart. Les
README des commandes sont aussi copiés près des sources installées. Aucune
nouvelle variable, secret, route ou migration ; configuration toujours issue
des deux env_file officiels. Aucun remote Git configuré, donc commit local.

## Publication authentifiée — 2026-11-06

La suite de SLS-030 relie les composants qualifiés au contrôle. Le helper SSO
3998 est toujours vivant, mais aucune session administrateur n'est enregistrée.
Les implémentations indépendantes se poursuivent ; aucun substitut d'identité
ne servira de preuve aux routes authentifiées.

La revue du flux confirme qu'authorize ouvre sa propre transaction et peut
attendre le SSO : elle ne peut pas être appelée sous le verrou de publication.
Le contrôle revalide donc avant le commit puis relit la credential exacte,
les droits et versions dans cette transaction. Le candidat partage l'UUID
de sa future révision et écrit dans un dossier privé sous artifacts : la
publication est exclusivement le commit SQLite, sans renommage interposé.
Un processus unique possède l'état par flock ; le démarrage réconcilie ses
seuls labels Docker et conserve le budget des nettoyages échoués.

Découpage retenu : migration et coordination, branchement aux routes et à la
configuration de cellule, commande deploy, puis preuves authentifiées réelles
et intégration console. Les contrats précisent les limites temporelles, les
réservations, les diagnostics et l'archivage de fonction avant le premier code.

La migration 003 et les routes sont maintenant déployées sur le SPARK DEV.
La base a été sauvegardée par l’API SQLite avant migration ; intégrité, modes
privés et versions antérieures ont été recoupés. Les trois variables hôtes/image
passent par les propositions officielles puis leur application en console.
Le socket rootless est monté dans le seul contrôle. Aucun secret ni route ajouté.

La revue a corrigé trois défauts : un nettoyage Docker non confirmé conserve
les fichiers et leur réservation ; les travaux bloquants sont rejoints avant
la libération du verrou, même après annulations répétées ; une erreur SQLite
de maintenance dégrade la santé et laisse la boucle périodique reprendre.
La dernière propriété passe E2E avec un vrai verrou SQL. L’arrêt pendant
nettoyage reste à qualifier ; la double annulation précise est relue sans être
déclarée déclenchée par les signaux normaux du serveur ASGI.

La première campagne opérationnelle étendue échoue dans son pilote : docker
run lit littéralement les guillemets des fichiers de cellule, et la seconde
instance refuse la configuration avant d’atteindre flock. Le scénario utilise
désormais Compose comme le déploiement normal. La campagne complète repasse :
30 contrôles, zéro échec, zéro skip, ressources temporaires nettoyées. Les huit
groupes HTTPS publics passent, dont l’upload anonyme refusé avant lecture du
corps. Les services contrôle et qualification restent healthy.

Le pilote authentifié utilise les vraies API et le packager. La revue a fait
ajouter la prise en charge immédiate des rejets des uploads concurrents,
des contenus d’archives distincts et un changement de noms secrets avant
rollback. La valeur d’un secret sous le même nom et le code effectivement
exécuté après rollback devront encore être observés par le moteur. Le lancement
du client échoue explicitement au prérequis de session SSO, aucune session
n’étant enregistrée ; le navigateur d’autorisation 3998 est toujours vivant.
Aucune de ces assertions authentifiées n’est comptée comme réussie.

La preuve `evidence/deployment-control-dev-2026-11-06.json` recoupe 21 sources
locales/distantes et 14 fichiers embarqués. Les valeurs actives correspondent
aux fichiers officiels ; quatre secrets connus sont recherchés en mémoire
dans les preuves et les sources sans correspondance. SLS-030 reste ouvert.

README, CONTRIBUTORS et INSTALL sont proposés dans leurs fichiers .?, appliqués
par la console du SPARK puis relus sans écart. Les notes distinguent les routes
intégrées des parcours authentifiés non qualifiés. Les anciennes copies de
pilotes sous control/ sont remplacées dans les instructions par e2e/.
Le dépôt n’a pas de remote configuré ; ce checkpoint reste un commit local.

La commande deploy est la tranche suivante de SLS-030. Son contrat précise
la cible HTTPS, la correspondance de service, la pagination, le packaging
avant mutation et les résultats partiels. La configuration active n'est jamais
modifiée avant validation. Une rupture réseau peut suivre un commit serveur :
le client signale cette ambiguïté sans rejouer une mutation. Les chemins de
publication positifs restent soumis au prérequis SSO réel de la campagne.

La revue précise que la borne JSON doit être contrôlée pour toutes les fonctions
avant la première mutation, comme le packaging. Elle fait aussi corriger le port
zéro, la recopie d’un UUID invalide et le classement des succès HTTP inattendus.

La commande deploy est implémentée avec HTTPS standard, sans nouvelle
dépendance. Les quatre défauts relevés sont corrigés et relus. Les avertissements
sont émis avant les appels et le rapport final ne recopie aucun corps distant.
Le packager garde ses 24 contrôles réussis dans la nouvelle image. La campagne
deploy-public-test passe 14 contrôles : arguments, URL, port zéro, identité
absente/invalide, valeurs manquantes, corps trop grand avant packaging et
véritable refus 401 de l’API DEV avec TLS normal. Aucun de ces refus ne prouve
une publication. Les deux services permanents restent healthy.

Le client e2e/adapter-deploy.mjs crée onze fonctions pour exercer la pagination,
les nouvelles révisions et la préservation des UUID, puis un véritable import
défaillant pour les résultats partiels et la reprise d’un brouillon. Son
lancement échoue au prérequis de session SSO réelle. Les sept groupes positifs
restent non qualifiés ; aucune identité de remplacement n’est introduite.
La preuve conservée est evidence/adapter-deploy-dev-2026-11-06.json. Les statuts
2xx inattendus sont une protection relue, pas une réponse inventée pour un test.

Les douze empreintes de sources sont identiques entre dépôt et SPARK, et les
fichiers Python des deux images sont recoupés. Les quatre secrets configurés
sont recherchés en mémoire sans correspondance dans les sources et rapports.
La relecture du client authentifié ne relève pas de défaut supplémentaire ;
elle confirme la portée de ses assertions, sans les transformer en preuves.
Les trois notes officielles sont de nouveau proposées, appliquées via la
console et relues pour inclure deploy. Aucun nouveau paramètre, secret ou route,
aucune recréation du contrôle pour cette tranche. Le commit reste local,
aucun remote n’étant configuré.

## Moteur d’invocation — 2026-11-06

Le tour précédent a livré les checkpoints de publication et de CLI ; l’arbre
est propre à b5717e1. Le helper d’autorisation 3998 est confirmé vivant, mais
aucune session SSO n’est enregistrée. SLS-040 poursuit les travaux indépendants.
Les explorations des contrats, du runtime et du stockage sont en lecture seule.

Le contrat EXECUTION précise les frontières jusque-là ouvertes : un appel en
file n’est pas admis ; l’échéance d’exécution commence sur une instance prête ;
les anciennes générations restent réservées et protègent leur code. Les
mutations de quota longues refusent pendant une invocation active, au lieu de
prétendre avoir appliqué un nouveau plafond. Le port zéro est identifié comme
défaut de la normalisation d’origine à corriger dans cette unité.

Le superviseur chaud conserve un enfant neuf par invocation. Les descendants
sont récoltés avant réutilisation et vérifiés depuis Docker ; un timeout recycle
le conteneur entier. Le canal privé est authentifié après bootstrap et ne
transmet sa clé ni à l’enfant ni à son environnement. Une horloge monotone
commune garde contexte et échéance extérieure cohérents.

L’intégration FUSE exige un agent hôte et des baux de consommation : le type
du montage seul ne prouve pas sa santé, et un remontage ne répare pas un ancien
bind Docker. Le contrôle ne suppose pas voir les nouveaux sous-montages dans
son bind existant. Le pilote d’instance est construit d’abord, puis raccordé
à cet agent et aux admissions réelles ; les preuves de composants ne clôturent
pas la passerelle authentifiée.

La relecture du pilote identifie une expansion JSON incompatible avec les corps
autorisés. Le transport privé encode donc toutes les réponses en base64 et
accepte une enveloppe d’événement de 8 Mio, sans changer les bornes HTTP.
Le début du handler est notifié séparément ; une disparition sans observation
est explicitement inconnue. La fermeture du diagnostic doit aussi interrompre
son attente stdin et rejoindre le nettoyage sur les signaux ordinaires.
Les autres constats portent sur les champs nommés par Connection, la sortie
fatale effective du superviseur et les courses de fermeture. Ils sont intégrés
à la campagne réelle avant qualification de cette tranche.

La première campagne reproduit le refus d’entrée échappée de 1 Mio. Après
correction, ce cas passe ; une réponse de 6 Mio fait encore sortir le superviseur
avec le code générique 1, sans événement OOM. Des codes de sortie fatale fixes
sont ajoutés au contrat pour rendre cette panne observable sans exposer les
messages applicatifs. Le diagnostic est vérifié sur les événements Docker réels.


Le second arrêt sur gros corps provient du diagnostic lui-même : son écriture
stdout synchrone bloque la boucle de contrôle, ce qui expire le canal privé.
Une émission non bloquante bornée et une lecture linéaire du client de preuve
font passer les trois réponses exactes de 6 Mio, dont NUL et retours à la ligne.
Les réponses privées restent encodées en base64 ; les limites HTTP ne changent pas.

Les courses réelles révèlent ensuite un inventaire Docker revenant à 404 après
une fermeture volontaire. Le résultat terminal accepté est maintenant conservé,
et le nettoyage confirmé avant retour. Le verrou de cycle couvre les créations
Docker en cours ; un second start refuse sans fermer l’instance existante.
Une deadline devenue exception pendant une suspension du contrôle est recueillie
même si l’échéance extérieure a déjà déclenché le nettoyage.

La campagne finale passe 31 contrôles d’invocation, 11 contrôles de cycle et les
36 régressions du chargeur partagé, dans cet ordre, sans concurrence entre
campagnes ni test ignoré. Les annulations répétées sont réellement acceptées
sur des tâches encore actives. Les descendants sont comparés à l’inventaire
initial. La saturation mémoire est confirmée par les événements OOM Docker.
Le refus de suppression du canal est provoqué par permissions, puis repris
après leur rétablissement. Le signalement Python de ce refus est attendu.
Le résultat tardif est éprouvé par SIGSTOP/SIGCONT du vrai pilote, après
production du résultat et récolte de son enfant. Les octets secrets sont
cherchés dans les chaînes JSON décodées, y compris avec caractères échappés.

Les preuves restent celles d’un composant opérateur. Les admissions, générations,
min/max/idle, agent de stockage, passerelle et parcours UI sont encore ouverts.
Le débit CPU sous contention et un processus réellement impossible à tuer ne
sont pas revendiqués qualifiés. Aucun registre d’incohérences ne reste ouvert
pour cette tranche ; les travaux d’intégration sont dans le backlog.


L’empreinte runtime qualifiée est appliquée par la proposition officielle
SERVERLESS_RUNTIME_IMAGE, puis le contrôle DEV est recréé et revient healthy.
Les huit groupes HTTPS/OIDC publics repassent. La preuve
`evidence/instances-dev-2026-11-06.json` compare 44 fichiers avec le SPARK et
vérifie les fichiers embarqués des deux images. Les configurations actives
correspondent aux deux fichiers officiels ; les quatre secrets configurés sont
recherchés en mémoire, sans correspondance dans les sources et rapports vérifiés.
Les ressources de qualification sont absentes. README, CONTRIBUTORS et INSTALL
sont proposées, appliquées par la console, puis relues et comparées. Aucun
nouveau secret, route ou migration. Le commit reste local : aucun remote Git.
Le helper d’autorisation reste vivant, sans session administrateur enregistrée.


## Agent local de volumes — 2026-11-06

Le tour précédent constitue une progression vérifiée : checkpoint a3d3c77,
78 contrôles de composants et huit groupes publics, image appliquée et notes
relues. L’arbre est propre à la reprise. Le helper SSO 3998 est confirmé vivant ;
la session administrateur manque encore. Le travail indépendant passe au
raccordement du stockage. Le SPARK présente systemd 259, Python 3.14.4, aucun
montage p2quota ni service d’agent existant ; le binaire qualifié est présent.

Les explorations confirment que PUT de fonction et publication remplacent tous
deux la configuration de stockage ; un rollback conserve ses quotas. L’agent
ne pourra donc pas être raccordé uniquement au PUT. Un montage visible peut
être déconnecté, et un signal TERM n’est pas une confirmation de démontage.
Les baux sont conservés jusqu’à suppression Docker, y compris à la reprise.

Le contrat STORAGE_AGENT tranche les opérations, la conservation après
 désactivation, les archives, le cache explicite et les budgets par défaut.
Le code installé est possédé par root ; seule l’unité de montage reçoit
CAP_SYS_ADMIN. Elle partage le namespace de montage de la cellule, exigence
vérifiée dans les sources systemd et à mesurer sur le service réel. Le choix
KillMode=control-group traite un restart avec consommateurs comme une panne,
avec drainage/recréation et aucune prétendue réparation de leurs binds.
Les sondes FUSE sont des processus bornés plutôt que des threads abandonnés.
Le plan de réalisation est registre/supervision, baux du pilote, puis routes
publiques et admissions ; les preuves de chaque tranche restent distinctes.

La revue du contrat fait expliciter la préparation des deux volumes : retrait
confirmé de chaque candidat avant commit, acquisitions bloquées par intention
durable, compensation du premier si le second échoue. Les places de montage et
augmentations de quota sont réservées avant ces préparations et conservées sur
nettoyage non confirmé. L’archivage refuse sous bail ; le drainage relève du
contrôle. Ces précisions précèdent le code de gestion des volumes.

Le registre de stockage est décrit dans SCHEMA avant sa première installation.
Le canal opérateur précise sa pagination et ses bornes ; une acquisition
interrompue ne doit jamais être déclarée saine à partir d’une liste vide de
montages. La maintenance normale refuse les baux et intentions en cours. Le
paquet root est identifié par son empreinte et son unité borne mémoire,
processus et descripteurs ; ces choix restent propres au service DEV.

La première campagne de l’agent passe quinze groupes réels avec nettoyage,
zéro échec et zéro skip. Elle établit les baux et fichiers après restart, mais
les pannes doivent encore être exercées avec un consommateur Docker vivant.
La revue impose une fermeture atomique des mutations pour la maintenance :
un contrôle ponctuel de l’absence de bail ne suffit pas avant un restart.
Le canal reçoit donc quiesce/resume avec identité d’installation attendue.
La récupération d’une sonde persistante reste consultable même quand sa
terminaison ne peut pas encore être confirmée.


## Preuves de l’agent local — 2026-11-06

Le paquet immuable de l’agent est installé dans le SPARK DEV. Les cinq variables
ont été proposées et appliquées par la console ; aucun secret ni route ajouté.
Quinze groupes de cycle de vie et huit groupes de limites passent, ainsi que
les 31 contrôles historiques du proxy sur son nouveau binaire. Les consommateurs
Docker restent vivants lors de la mort de FUSE et du restart ; leurs anciens
binds échouent, puis la réacquisition retrouve les fichiers après leur suppression.
Les 64 montages, le budget logique plein, 51 baux paginés, une réponse perdue,
un montage étranger, les connexions lentes et les répertoires 000 sont exercés.

La saturation a révélé la monopolisation du verrou par un tour de surveillance
complet. Le verrou est maintenant rendu entre volumes et chaque ligne relue
après acquisition. Le vidage d’un cache 000 échouait au rename avant même sa
suppression : le déplacement vers un autre parent exige son écriture. L’opération
explicite rétablit désormais le mode privé avant ce déplacement. La fixture
échouée a reçu une réparation opérateur limitée de permissions, puis l’ancien
agent a achevé son intention et les vraies opérations archive/purge ont nettoyé
ses fichiers ; la nouvelle campagne repart de nouvelles ressources et passe.

La revue en lecture seule a également fait corriger le bail partiel déclaré
sain, la sonde lancée sans intention préalable, la synchronisation de trash
avant restitution du quota et la course de maintenance. L’installateur tente
resume même si la réponse quiesce se perd. La reprise d’une sonde impossible à
terminer reste consultable. Ces derniers cas extrêmes de crash et blocage noyau
ne sont pas déclarés prouvés par les campagnes courantes. Leur périmètre, comme
le raccordement aux instances et aux API, reste explicite dans SLS-050.

À la demande du responsable, le helper SSO expiré après huit heures a été
relancé. Le binaire Chromium manquait : la version requise par Playwright
1.64.1 a été installée, puis l’accueil a été rouvert dans Chromium en mode graphique.
La connexion administrateur n’est pas encore enregistrée à ce checkpoint.

Trois refus CLI réels complètent les 31 régressions du proxy pour le nouveau
nom de montage : vide, espace et dépassement de la longueur maximale.

La preuve finale recoupe quinze sources locales/distantes, les fichiers du
paquet root installé et les trois rapports réussis (15, 8 et 34 groupes/contrôles).
Le registre est intègre, sans bail, volume, sonde, intention ni fonction active
de preuve ; les montages et conteneurs temporaires ont disparu. Les deux
applications existantes restent saines. Aucun remote Git n’est configuré.

Le tunnel local de la console était rompu et renvoyait tunnel_unavailable.
Son geste normal POST /api/tunnels l’a reconnecté ; les propositions des trois
notes ont ensuite été appliquées et les notes officielles relues identiques.
La réinstallation finale a conservé le même paquet et passe quiesce/restart.

## Noms d’exploitation et domaine — 2026-11-06

Le responsable demande des noms de conteneurs compréhensibles et l’adresse
serverless.lelabs.tech : lelabs est déjà son infrastructure de développement.
Le conteneur permanent de qualification exécute les handlers ; le nommer
« tests » décrirait son client plutôt que son rôle. Les noms retenus sont
serverless-api et serverless-runtime-reference. La mission factory_explorer
confirme que container_name suffit et que renommer le projet Compose créerait
de nouveaux volumes implicites. Les clés internes restent donc stables.

Le relevé courant trouve les deux anciens conteneurs healthy, la variable
publique sur l’ancien domaine et une nouvelle route serverless.lelabs.tech
vers 8080. Le vrai fournisseur accepte déjà le nouveau redirect_uri : une
requête PKCE prompt=none renvoie login_required au nouveau domaine (302).
La migration corrigera la route vers 18090, puis la variable officielle.
Le contrat DEPLOYMENT_NAMES précède les changements de code et de déploiement.

La session administrateur créée par la connexion réelle du responsable est
présente sur l’ancien domaine et ses API répondent 200. Elle n’est pas exportée
vers le nouveau domaine. La qualification authentifiée globale reste ouverte.

Le responsable corrige la route vers 18090 et retire l’ancienne entrée.
La relecture ne trouve que serverless.lelabs.tech 18090 tls. La proposition
SERVERLESS_PUBLIC_URL est appliquée par la console, sans secret supplémentaire.
Les deux Compose reçoivent container_name et les clients opérateur leurs
nouvelles cibles. La revue indépendante ne relève aucun blocage statique.

Avant la recréation, une sauvegarde SQLite native intègre est créée en 0600,
puis les observations HTTP du compteur, du cache et du travail partiel sont
conservées dans le volume du client. Après recréation, les deux conteneurs
reviennent healthy ; images, montages, labels Compose, base, identité et objets
sont identiques. La reprise HTTP du calcul aboutit et nettoie ses ressources.
Le premier passage public a commencé avant la fin de ce client : écart à la
consigne de série, ce résultat public est écarté puis rejoué seul. Le rapport
retenu est celui du second passage, terminé sans autre campagne en cours.

38 tests HTTP du runtime, neuf contrôles Chromium, huit groupes HTTPS/OIDC,
quatre chemins réseau et quatorze contrôles de CLI réussissent sans skip.
L’image du seul client E2E de l’adaptateur est reconstruite pour embarquer le
nouveau domaine. Les images applicatives sont conservées. Les captures de
l’accueil et de l’entrée SSO sont relues ; elles montrent la console et le
formulaire réel du fournisseur. Dix-sept sources locales/distantes concordent,
le TLS est vérifié normalement et neuf paramètres actifs correspondent aux
deux fichiers officiels, comparaison des secrets uniquement en mémoire.

README, CONTRIBUTORS et INSTALL sont proposés, appliqués par la console puis
relus identiques. La fenêtre normale ouverte sur le nouveau domaine reçoit
la connexion personnelle du responsable. Le helper enregistre uniquement son
cookie de plateforme ; une nouvelle requête confirme session authenticated
et namespaces HTTP 200 le 6 novembre à 16:00 UTC. La migration SLS-011 est
qualifiée. Les campagnes administrateur globales restent ouvertes et disposent
maintenant de cette session réelle. Aucun remote Git n’est configuré.

## Consigne durable de nommage — 2026-11-06

Le responsable demande de rendre obligatoire un nommage significatif de la
fonction et de l’usage. La règle est inscrite dans CLAUDE_PROJECT.md, contrat
lu par les agents, et référencée depuis le README. Elle couvre code, ressources
et interface, distingue moteur d’exécution et clients de test, et exige de
justifier les qualificatifs d’environnement. Le nom est vérifié dès la création
et à la revue. Cette modification documentaire ne change aucune ressource
déployée ; sa validation porte sur le contenu, le lien et la propreté du diff.

## Contrat OIDC actualisé — 2026-11-06

Le responsable fournit le bloc d’intégration du client p2enjoy-serverless-dev,
daté du 6 novembre à 15:44:32, avec retour, déconnexion, origine et accueil sur
serverless.lelabs.tech. OIDC_DEV.llms.txt reprend ce bloc courant ; OIDC_DEV.txt
reprend exactement sa déclaration, y compris le nom enregistré, ORIGINE et
ACCUEIL. Le précédent contrat reste accessible dans l’historique Git.
Les exigences PKCE S256, rôles verified/admin, clés asymétriques et durée de
300 secondes sont identiques au contrat déjà reçu. Les URL correspondent à
la connexion réelle vérifiée dans la preuve de migration SLS-011.
Cette mise à jour documentaire n’ajoute aucune nouvelle preuve fonctionnelle ;
la déclaration extraite du bloc est comparée au fichier d’import avant commit.

## Qualification authentifiée et noms longs — 2026-11-06

La reprise trouve l’arbre propre au commit 50b25d2 et les deux conteneurs
healthy, sans campagne active sur le SPARK. Le checkpoint précédent constitue
une progression documentaire : contrat OIDC courant persisté. La vraie session
administrateur permet maintenant les campagnes jusque-là non exécutées.
Les 19 groupes de control-admin passent, dont droits CRUD, portée, secrets,
conflits, expiration, rotation et redémarrage. Le nettoyage est confirmé.

Le parcours UI échoue ensuite à 390 px sur un namespace de 63 caractères.
La reproduction depuis l’accueil mesure scrollWidth=405 pour innerWidth=390 :
le seul élément débordant est le dernier span du fil d’Ariane, large de 389 px.
La capture confirme sa coupure à droite. L’exploration indépendante retrouve
la cause : les titres ont overflow-wrap:anywhere, ce span flex ne l’a pas.
Décision : donner aux segments du fil d’Ariane une largeur minimale réductible
et la coupure des mots longs, sans masquer le contenu ni modifier la taille
des titres. Le contrat local de design est précisé avant la correction CSS.
Les deux design systems ont été lus intégralement.

La console reconstruite supprime le débordement. Le parcours suivant révèle
que fermer le tiroir mobile conserve le focus sur « Fermer le menu », désormais
masqué. La mesure confirme menuExpanded=false et shell.inert=false, avec ce
bouton encore actif. closeMenu appelle focus avant que React retire inert du
contenu contenant le bouton Menu. Décision : effectuer la restitution après
la mise à jour du DOM, dans l’effet de layout de la transition ouvert/fermé.
Le passage desktop rend le focus au lien visible de navigation. Les trois
gestes de fermeture et ce passage de palier seront exercés dans le vrai parcours.

La correction est relue contre les contrats puis déployée dans serverless-api.
Les 11 parcours UI passent, dont inert, verrouillage du défilement et focus
sur les trois fermetures puis le passage desktop. Les sept captures sont
inspectées : nom complet, conflit conservant la saisie, paramètres, jetons et
activité. Les 19 groupes API sont rejoués sur cette image, y compris le
redémarrage, puis les huit groupes publics seuls. Zéro échec et zéro skip ;
aucune erreur de nettoyage ni objet de gestion actif résiduel.

La preuve control-management-dev-2026-11-06.json recoupe 31 sources,
19 fichiers embarqués dont quatre ressources web servies identiques, l’image
90219c44… et neuf paramètres provenant des fichiers officiels. Les deux
conteneurs sont healthy et l’intégrité SQLite est confirmée. README,
CONTRIBUTORS et INSTALL sont proposés, appliqués par la console puis relus.
Aucune variable, secret, route ou migration ajoutée. SLS-020 reste ouvert
pour ses cycles SSO ; les allocations et volumes attendent le raccordement
du moteur. Ce checkpoint constitue une progression fonctionnelle vérifiée.

## Attente des uploads concurrents — décision du 2026-11-06

L’instruction indépendante du registre confirme la récursion de finishUpload.
Le principal vérifie les quatre finally qui doivent rejoindre l’upload déjà
lancé avant le nettoyage. Le contrat de publication exige des modifications
concurrentes réelles puis une revalidation des droits et versions. Décision :
attendre directement pending, conserver son enveloppe valeur/erreur et les
quatre finally. Vérifier également la destruction du conteneur de validation
au terme du scénario d’admission saturée. La résolution sera acquise après
les onze groupes réels, leur nettoyage et la conservation des preuves.
Une réponse HTTP perdue reste un cas distinct : cette attente cliente ne
prouve pas à elle seule l’issue serveur après rupture réseau.
