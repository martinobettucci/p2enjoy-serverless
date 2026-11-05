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
