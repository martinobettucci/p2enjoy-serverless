# Journal de cadrage

## 2026-11-08 — Intégration des campagnes publiques de stockage

Après les preuves de reprise et d’archives historiques, SLS-065 doit réunir ses
sept campagnes dans la suite commune. La campagne UI dépend encore d’archives
préexistantes pour ses deux pages. Décision persistée avant code : elle crée
onze brouillons et les archive par les parcours UI, recoupe leurs UUID sur les
deux pages, puis purge uniquement ses objets. Elle passe de neuf à dix groupes.
Le runner prépare deux vraies connexions SSO distinctes depuis une entrée stdin
privée et réutilise ces identifiants en mémoire pour le banc historique.

Deux scopes sont retenus : ciblé pour les sept campagnes SLS-065 et complet
pour leur union avec les régressions publication/console et stockage agent.
Le build historique est un prérequis frais, sans compter un groupe inexistant.
Les dépendances Playwright rejoignent l’index de sources. Les mappings de
campagne sont exhaustifs ; l’installation historique conserve son contrôle de
restauration distinct, car ses UUID temporaires n’existent pas dans la cellule
habituelle. Les erreurs SSO ne doivent jamais réémettre une saisie sensible.
Le produit reste inchangé ; seule la qualification est étendue à ce stade.

## 2026-11-08 — Version de code par hash et pilote d’utilisateurs

Le responsable demande de créer une version seulement si le code uploadé change,
d’utiliser son hash comme tag, de revenir à une ancienne version dans la fiche
et d’invoquer un tag précis tant qu’il reste disponible. Objectif : faire
coexister un pilote et un code de production stable. SLS-074 et FUNCTION_VERSIONS
capturent ce périmètre avant implémentation, avec liens vers les unités existantes.

Le produit actuel crée des révisions à UUID et possède le rollback, mais résout
les invocations vers la seule révision active. La nouvelle preuve devra couvrir
déduplication, tags, archive individuelle, pools simultanés et migration ; les
preuves de révisions existantes ne sont pas étendues implicitement.

Le responsable confirme la dernière version promue pour les appels sans tag.
L’upload prépare une version disponible par hash sans modifier la cible, même
au premier upload. La promotion est une action explicite et distincte dans la
console et la CLI. Le pilote appelle le nouveau hash pendant que le sans-tag
reste stable. Le rollback remplace la cible courante ; les appels portant un
hash ne la suivent jamais. La règle de dernière version uploadée est écartée
par ce choix explicite du responsable. Aucun tag refusé ne déclenche un autre code.

Le hash porte sur le paquet exécutable canonique et son descripteur, sans les
métadonnées sans effet du ZIP ni les valeurs de configuration. Les variables,
secrets, ressources et volumes restent ceux du service/de la fonction ; le mode
pilote publie le code seul pour préserver cette configuration. Les budgets sont
communs aux versions, les pools les distinguent et les futurs crons suivent la
seule cible courante. Les URL avec UUID@hash évitent une collision avec les
chemins métier existants. Modification documentaire uniquement, statut non commencé.

La revue du contrat fait préciser quatre invariants vérifiés dans les sources
actuelles : le snapshot devra prendre handler/runtime/image/événements de la
version choisie, séparément des ressources et variables courantes ; le cycle
des versions garde Update, première publication et sa première promotion Create, invocation Read et
suppression de fonction Delete ; un doublon est admis au plafond de versions,
avec consommation définitive après déduplication ; le chemin d’événement
implicite dérivé du nom est exclu de l’empreinte, afin qu’un renommage conserve
le hash. Les preuves correspondantes sont ajoutées. Le calcul d’URL conserve
aussi le point implicite des fonctions sans événement HTTP déclaré.

## 2026-11-08 — Inscription systématique des demandes au backlog

Le responsable demande que toutes ses demandes soient ajoutées au backlog.
La règle est persistée dans CLAUDE_PROJECT.md et en tête de BACKLOG.md : chaque
demande produit, correction ou contrainte complète une unité existante ou crée
une unité identifiée, avec critères et preuves. Une table rattache les demandes
confirmées aux unités, y compris SLS-067 à SLS-073 déjà spécifiées. Les valeurs
de secrets restent exclues. SLS-001 reprend explicitement manuel, URL du SPARK
et ergonomie ; SLS-030 explicite l’audit de compatibilité en lecture seule et
sa preuve par fixtures originales. La mention périmée de purge/cache à réaliser
dans SLS-050 est alignée sur leur livraison en SLS-065, encore en qualification.
Modification documentaire uniquement ; aucun statut de livraison n’est avancé.

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

La première campagne SLS-030 atteint trois groupes réussis, dont une vraie
publication par Create, puis échoue sur le marqueur d’expurgation absent.
La lecture du candidat confirme import_failed, zéro octet de logs et
container_removed=true. Le module throws.cjs ne fait que lever une exception ;
le chargeur remplace son message par un code fixe sans l’écrire. Le nettoyage
du client réussit et conserve une archive conformément au contrat.
L’exploration indépendante confirme la cause. Décision : une fixture distincte
log-secret-then-throw.cjs écrit le secret injecté par writeSync sur stderr,
avec préfixe public, avant son exception. L’assertion vérifie ce préfixe expurgé
et le nettoyage Docker. throws.cjs conserve son rôle de simple exception dans
les autres campagnes. Le contrat de preuve est précisé avant cette correction.

La campagne corrigée passe ses onze groupes, puis la CLI réelle passe ses
sept groupes, exécutés en série. La revue confirme l'attente des quatre
uploads et l'expurgation des octets réellement écrits par la nouvelle fixture.
Issue du registre : corrigée ; l'entrée finishUpload est retirée avec sa preuve.
Le contrôle applicatif n'a pas changé depuis ca47c39. Le recoupement compare
50 sources locales/distantes et 19 fichiers embarqués, les mêmes images,
quatre ressources HTTPS et les neuf paramètres officiels. Les 35 révisions
archivées sont présentes avec leurs SHA256 ; aucun objet actif, candidat
non terminal, réservation, canal ou conteneur de validation ne subsiste.
Les trois notes sont proposées, appliquées et relues. Aucun nouveau réglage
de cellule. Aucun remote Git configuré, donc conservation locale sans push.

La preuve deployment-authenticated-dev-2026-11-06.json clôt ces parcours,
pas SLS-030 : expiration réelle, plafonds, interruptions, déconnexion
concurrente et interface de révisions restent ouverts, ainsi que l'invocation
après publication/rollback dans SLS-040. Les cas CLI de transport et de
modification locale concurrente sont également explicites. Cette unité apporte
une progression fonctionnelle vérifiée ; la prochaine porte sur les limites
et la reprise de publication avant le raccordement du moteur.

## Plafonds et reprise de publication — décision du 2026-11-06

Le checkpoint bdf81fb est une progression fonctionnelle vérifiée. L'exploration
des quatre prochaines preuves confirme les compteurs et leur point de contrôle :
64 candidats globaux à la préparation, vingt révisions à l'upload. Le principal
relit les suppressions, le démarrage et les réservations. Le contrat précise
des coupures après observation physique, la fenêtre courte de quatre secondes
du module existant, l'attente de la requête interrompue et le redémarrage dans
le nettoyage. Les seules lectures privées portent sur états, empreintes et
présence de fichiers ; aucune écriture de base ni simulation d'horloge.
La nouvelle campagne sera exécutée seule sur le contrôle DEV, sans modifier
les variables de cellule. Budget, expiration et autres interruptions restent
des preuves séparées, explicitement ouvertes.

Le premier passage réussit les plafonds globaux et de révisions. Le troisième
scénario refuse de couper : receiving est observé, mais les 16 Kio envoyés
n'atteignent pas le fichier pendant ses huit secondes d'observation. Aucun
SIGKILL n'a été émis ; le nettoyage réussit, sans candidat ni réservation
restants. L'image Python réelle annonce io.DEFAULT_BUFFER_SIZE=131072.
Le fragment passe à 192 Kio dans une archive contenant 256 Kio de vrais octets
aléatoires, afin de dépasser le tampon tout en maintenant le corps incomplet.
Le critère physique est conservé ; aucune attente ni assertion n'est supprimée.

Le second passage réussit les quatre groupes. La première coupure observe
88 903 octets effectivement reçus sur disque ; la seconde observe le conteneur
de validation vivant et son montage du candidat. Les deux SIGKILL donnent
un contrôle arrêté en code 137, suivi du démarrage réel et du retour de santé.
Chaque candidat devient failed/control_interrupted, sans révision ; payload
temporaire, réservation, artefact, canal et conteneur sont éliminés. La
configuration chiffrée et la révision précédentes restent identiques, puis
la publication suivante réussit. La revue indépendante confirme les gardes,
le finally de rétablissement et la portée limitée de la preuve.

La preuve publication-recovery-dev-2026-11-06.json conserve quatre groupes,
zéro échec/skip, les nettoyages, 51 sources concordantes, 19 fichiers embarqués,
les deux services healthy et les mêmes paramètres officiels. Les 53 archives
antérieures sont intactes ; vingt archives supplémentaires restent conservées.
Les six sources Node correspondent toujours à l'image immuable qualifiée.
Les trois notes de cellule sont appliquées puis relues, sans nouveau réglage.
Le registre d'incohérences est vide. Ce checkpoint constitue une progression
fonctionnelle vérifiée, avec arbre et preuves prêts pour un commit local.
Expiration, budget, déconnexion concurrente et arrêt pendant nettoyage restent
ouverts ; le raccordement de l'admission, des volumes et de la passerelle est
la principale partie fonctionnelle restante avant la campagne transversale.

## Raccordement des instances aux volumes — 2026-11-06

Reprise sur 6833c9a, arbre propre, deux conteneurs healthy et agent actif.
Le tour précédent constitue une progression vérifiée : gestion, publications,
plafonds et reprises qualifiés. La lecture des contrats d'exécution/stockage et
les explorations indépendantes confirment le prochain raccordement nécessaire :
un bail durable avant Docker, une destruction confirmée avant libération,
et un contrôle des volumes durant les invocations. Les canaux d'instances
doivent rester distincts de validation ; le futur moteur coordonnera aussi
leurs générations, références de révision et drainage.

Le Compose ne monte pas le canal de stockage. L'agent recrée son socket et
systemd peut aussi recréer son répertoire : décision de monter le répertoire
readonly et de le conserver à l'arrêt par RuntimeDirectoryPreserve=yes.
La documentation primaire systemd confirme ce comportement ; le restart sera
éprouvé depuis le même contrôle. Les deux variables requises sont déjà celles
de la cellule. L'UUID de l'agent et celui du contrôle restent distincts.
La libération sera confirmée par bail absent et état des volumes, car une
réponse already_released seule ne prouve pas leur démontage. Cette tranche
branche les classes de production et leurs preuves Docker ; la passerelle,
l'admission et les mutations publiques restent l'étape suivante.

### SLS-050 — canal visible depuis Docker rootless

Le premier essai dans l'image du contrôle a échoué avant création de fonction :
`storage_transport`. Le socket existait sur la cellule (0700/0600, UID1001),
mais /storage-agent dans Docker montrait un autre inode, un répertoire vide
0755 et un autre périphérique. Le /run du démon rootless est distinct de celui
du service systemd. La conservation du répertoire systemd ne résout pas cette
frontière. Décision réversible : canal privé dans
/srv/p2enjoy-serverless/storage-channel, hors du registre/backing. Configuration
par la proposition de cellule, installateur vérifiant le service actif à son
ancien chemin avant quiesce/restart. La racine de données reste identique.
Le pilote de preuve reçoit une échéance externe et restaure l'agent même si
son dialogue échoue. Le défaut de transport est enregistré comme échec réel,
jamais comme preuve réussie ; les campagnes seront rejouées après correction.

### SLS-050 — premiers résultats du raccordement réel

Les treize groupes de managed-storage passent dans la véritable image du
contrôle : baux, binds FUSE, enfants neufs, recréations, quotas data/cache,
partage/isolation, refus de mutation, courses, échec Docker, timeout,
annulations pendant acquire/check, mort FUSE, arrêt/démarrage agent, volumes
désactivés et diagnostic CLI avec EOF. Nettoyage confirmé, zéro échec/skip.
Le contrôle conserve le même ID et le répertoire du socket le même inode
pendant stop/start de l'agent. Le chemin officiel est maintenant
/srv/p2enjoy-serverless/storage-channel ; l'installateur a migré le canal après
quiesce du service actif, avec racine de données inchangée.

Deux défauts du client de preuve ont été corrigés après échecs réels : Node
rend EDQUOT sous code UNKNOWN/errno -122 (le handler reconnaît l'errno Linux,
les assertions le contrôlent) ; le nom FUSE contient l'UUID sans tirets. Son
garde-fou a refusé la coupure avant correction, et la procédure de secours a
restauré l'agent, rejoint le worker et nettoyé tous ses consommateurs/baux.
La copie par docker cp étant interdite sur rootfs readonly, le script de
preuve est déposé dans le seul tmpfs /tmp via docker exec, puis supprimé.

La revue a corrigé la garde avant le premier await d'invocation, le traitement
prioritaire d'une panne du watcher et la fermeture sur annulation du check
préalable. La course exacte résultat/panne simultanés reste vérifiée par la
structure du code ; les pannes réelles sont déclenchées pendant un handler
actif. Régressions et recoupement des preuves restent en cours à ce stade.

### SLS-040/050 — checkpoint du pilote avec stockage

La campagne complétée ajoute la pagination de 51 vrais baux et les refus
configuration_conflict/function_unknown avant Docker : quatorze groupes passent.
Les régressions passent en série : 31 invocations, onze cycles de vie, quinze
groupes de l'agent, 38 démarrages/opérations du contrôle, huit groupes HTTPS.
La garde de racine avec agent arrêté passe un groupe séparé via la vraie console.
Total de ce checkpoint : 118 groupes, zéro échec/skip, nettoyages confirmés.
La revue finale ne relève plus d'anomalie dans la garde de l'installateur.

La preuve managed-storage-dev-2026-11-06.json recoupe 60 sources locales/distantes,
21 fichiers embarqués, les ressources web servies, le paquet protégé de stockage
et les rapports. Image de contrôle :
sha256:aaf50a012184335e331acb40ccecdf5cedbe4b360eedb3bf31fe193d812c9bef.
Les 73 archives de publication sont intactes. Aucun bail, montage, allocation,
instance, réseau d'instance, conteneur de validation ni espace de preuve restant.
Les deux conteneurs permanents et l'agent sont sains ; les ressources de console
sont identiques au checkpoint relu visuellement de gestion.

Les valeurs consommées sont conformes à /etc/spark/env et /run/spark/secrets.
Le chemin du canal a été appliqué via la console ; les secrets sont vérifiés
sans être publiés. Route actuelle : serverless.lelabs.tech vers 18090 avec TLS.
README, CONTRIBUTORS et INSTALL de cellule ont été proposés, appliqués puis relus.
Les incohérences de visibilité /run et de garde sur agent arrêté sont résolues.
Le dépôt ne possède aucun remote ; ce checkpoint est conservé en commit local.

SLS-040/050 restent ouverts : admission et réservations durables, générations,
min/max/idle, reprise du contrôle, invocation publique avec ACL origine/IP,
mutations de stockage par API/console, crons et métriques d'exploitation.
La prochaine tranche raccorde l'admission et la passerelle au pilote réel avec
baux ; aucune campagne de composants ne vaut clôture du goal de plateforme.

### SLS-040 — admission, passerelle et frontière de commit

Le tour précédent est classé progrès : bfcb264 déployé, 118 groupes vérifiés.
L'arbre est propre au démarrage de cette tranche ; les deux conteneurs et l'agent
sont sains. La cellule confirme memory.max=17179869184 et cpu.max sans plafond ;
son contrat garantit 1 CPU partagé. Les budgets de fonctions proposés sont donc
1 CPU, 8192 Mio et 32 instances, hors contrôle/agent/validation, avec 128 attentes
globales et 16 par fonction. Le fichier ADMISSION.md fixe la comptabilité, la
file, les minima/idle, les états durables, la reprise et la passerelle.

Les explorations ont confirmé trois défauts à corriger pour l'entrée publique :
repli admin du helper authorize, limite générique de 256 Kio et port Origin :0
canonisé à tort. Elles ont aussi identifié les CIDR IPv4-mapped et les alias
implicites concurrents. Les références des instances doivent protéger les archives.

Le raccordement des mutations exige une vraie décision durable entre SQLite et
l'agent. configure(old) n'est pas un rollback sûr : nouveaux volumes conservés
et budget libéré déjà réutilisable. Décision : préparer et sonder les quotas sans
publier ni libérer l'ancienne allocation ; revalider les droits avant le commit
SQL de l'objet et de sa décision ; confirmer ensuite commit dans l'agent. Avant
cette décision, une interruption entraîne abort. Après, elle reprend commit.
Cette étape sert directement les créations, mises à jour et publications réelles
avant activation de la passerelle ; le goal garde son périmètre complet.

### SLS-040/050 — préparations de quotas installées et qualifiées

Les contrats 4a80ce2, 5e54c37 et 2660a45 précèdent cette réalisation. La revue
confirme la réservation de l'ancien quota jusqu'à décision, la compensation
limitée aux répertoires nouveaux vides et la reprise de preparing/prepared
sans décision implicite. Le contrat ADMISSION est aligné sur le maintien d'un
état vide versionné après abandon ; un reçu remplacé ne permet pas le rejeu
d'une ancienne préparation. Le registre de stockage passe à sa migration 003.

Le paquet protégé installé porte l'empreinte
4ba9e4bf5626d221596725566102d919047d19c43a944bfa20cd1a12bd8a3d34.
La nouvelle campagne passe dix groupes réels : préparation et publication,
propriété, baux actifs, réservation sous saturation, versions et décisions
répétées/opposées, fichiers conservés lors des refus, restart après prepared,
SIGKILL pendant preparing observé, abandon partiel après retrait du cache
et préservation d'un répertoire antérieur. Le signal vise le pidfd vérifié du
seul agent DEV ; aucun état de registre n'est fabriqué pour provoquer la panne.

La revue du banc a corrigé avant exécution son nettoyage : conserver les
correspondances conteneur/bail/fonction, bloquer release/abort/purge après un
échec de destruction, collecter les erreurs indépendantes et enregistrer les
identifiants des refus avant les appels. Une connexion SQLite de surveillance
est maintenant fermée explicitement ; la version finale du scénario est
rejouée intégralement. Ces corrections concernent le client de preuve.

Les régressions passent en série : quinze groupes de l'agent, huit groupes de
limites et quatorze groupes du pilote avec baux, soit 47 groupes avec la nouvelle
campagne. Zéro échec/skip, nettoyages confirmés. La preuve
storage-preparations-dev-2026-11-06.json recoupe 62 sources locales/distantes,
21 fichiers embarqués et le paquet installé. Les 73 archives antérieures sont
intactes. Aucun bail, montage, allocation, intention, conteneur/réseau d'instance,
validation ni espace temporaire de campagne ne subsiste.

L'image du contrôle reste aaf50a012184335e331acb40ccecdf5cedbe4b360eedb3bf31fe193d812c9bef.
Les deux conteneurs permanents et l'agent sont sains. La configuration consommée
concorde avec /etc/spark/env et /run/spark/secrets ; la route reste
serverless.lelabs.tech vers 18090 avec TLS. Les trois notes sont proposées,
appliquées par la console puis relues. Le registre d'incohérences étant vide,
son fichier est retiré conformément au contrat. Aucun remote Git n'est configuré.

Prochaine réalisation : intentions durables du contrôle et raccordement des
créations, modifications, suppressions et publications, avec relecture des
droits/versions après préparation. La publication SQL doit porter sa décision ;
une perte d'ACK après commit ne peut pas annoncer que l'ancienne configuration
est conservée. Admission, min/max/idle, passerelle, observations et parcours UI
restent ensuite à terminer. Le goal demeure actif et conserve tout son périmètre.

### SLS-040/050 — décision SQL des mutations publiques

Le tour précédent est classé progrès : 0a94d22 déployé et 47 groupes vérifiés.
L'arbre et les services sont sains au début de ce raccordement. La migration
004 du contrôle est spécifiée : intention invisible avant création, quota cible
sans secrets, versions internes et décision commise avec l'objet. La maintenance
résout les opérations abandonnées ; une réponse perdue après commit ne promet
pas une conservation de l'ancienne configuration.

Une fenêtre supplémentaire est fermée dans le contrat : après réponse incertaine,
une consultation inconnue ne prouve pas qu'un prepare retardé n'arrivera pas.
Abort peut donc porter la configuration et la version initiale pour inscrire un
reçu d'abandon sans préparer ni allouer. La requête retardée retrouve ce reçu.
Le contrôle persiste la version avant tout envoi ; sans version inscrite, aucun
prepare n'a pu partir. Cette extension utilise la migration 003 existante de
l'agent et sera éprouvée par les vrais RPC et les reprises HTTP du contrôle.

### SLS-040/050 — raccordement public et défauts de preuve corrigés

Les créations, modifications de quotas, suppressions et publications utilisent
maintenant function_operations. Les décisions de publication et d’archive sont
persistées avec l’objet ; les droits et versions sont relus après préparation.
La migration 004 est appliquée après une sauvegarde native SQLite vérifiée
(before-004-20261106T190408Z-793ab4.sqlite3, intégrité, mode 0600 et 73 archives).
L’extension de l’agent neutralisant un prepare retardé passe douze groupes réels.

La première campagne HTTPS a révélé un défaut du banc : docker kill est un
arrêt demandé au démon et le pilote n’appelait pas start. Les deux UUID de
cette campagne ont été récupérés après redémarrage et vérification de la décision
aborted, puis archivés et purgés explicitement. Le rapport initial reste en
échec ; sa récupération est conservée séparément. Le banc arme désormais sa
restauration avant le signal, confirme exited/137, puis redémarre avant nettoyage.
Le timer indépendant produit une trace corrélée confirmant que l’agent était
suspendu avant son SIGCONT ; une reprise du finally ne suffit plus à valider ce cas.

La revue a aussi corrigé le départ de tâches propriétaires lors de la fermeture
et la portée du try SQLite d’audit. Une vraie contention de l’écrivain après
commit confirme le maintien du 503, des identifiants de décision et d’une trace
audit.unavailable corrélée. La publication avec ACK perdu reste published,
conserve sa nouvelle révision et permet ensuite un rollback sans modifier les quotas.

Un dernier défaut a été reproduit avant le correctif (référence de configuration
du build bffa36bc) : même sans mutation de
volumes, resolve prenait un verrou d’écriture avant de constater l’absence
confirmée d’intention. Sous BEGIN IMMEDIATE réel, la responsabilité embarquée
rendait 503 avec Mutation-Committed:false. La correction lit d’abord l’UUID exact ;
elle ne prend le verrou écrivain que pour une intention existante. Le garde de
propriété et les erreurs de lecture sont conservés. La preuve ciblée appelle
le vrai pilote embarqué et la vraie base ; elle est distinguée des parcours HTTPS.

Les campagnes précédentes sont adaptées à l’archivage désormais effectif :
DELETE est suivi d’une purge opérateur de leurs seuls UUID, rattachés au namespace
exact. Les états archivés et allocations sont conservés dans les rapports avant
purge ; les archives de code demeurent. Les nettoyages indépendants continuent
après erreur, et une purge échouée peut être retentée sans relire une fonction
logiquement supprimée. Les captures de console sont désormais produites en JPEG.

### SLS-040/050 — preuve finale des mutations et de leurs régressions

Les quatorze groupes ciblés passent sur le contrôle final. Les onze campagnes
de la séquence complète terminent avec code zéro, soit 149 groupes, auxquels
s’ajoutent les douze préparations déjà vérifiées sur le même paquet d’agent.
La preuve function-storage-dev-2026-11-06.json totalise 161 groupes réussis,
zéro échec et zéro skip. Le contrôle opérationnel en compte 38, la gestion 19,
la console 11, les publications 11, l’adaptateur 7, les reprises 4, le public 8,
l’agent 15, ses limites 8 et le pilote avec volumes 14. Les nettoyages sont confirmés.

Les sept nouvelles captures JPEG sont observées : vide, nom maximal mobile,
conflit de configuration conservant la saisie, jetons, fonction desktop/mobile
avec stockage réellement alloué, et activité. Les ressources web sont identiques
à la baseline de gestion ; aucune modification visuelle n’est déduite du seul build.

La consolidation vérifie 82 sources locales/distantes, 23 fichiers embarqués,
le paquet protégé e116f761 et les 136 archives de code conservées. Aucun objet
de gestion actif, intention, bail, montage, allocation, conteneur ou réseau
d’instance, validation ni espace temporaire de campagne ne subsiste. Les bases
sont intègres ; les deux conteneurs permanents et l’agent sont sains.

L’identifiant Docker déployé est 922b2be19b240df60ed4dec7397b4f87c5902a7a97d9d23592ef825bf57e8cb2.
La valeur 31e13832 relevée au build désigne son blob de configuration, confirmé
dans l’export de cette même image ; elle n’est pas l’identifiant Docker. La
baseline et la note d’exploitation utilisent maintenant la référence déployée.
La preuve avant/après conserve ses références initiales en explicitant leur nature.

Les trois notes sont proposées, appliquées par la console puis relues. Les
paramètres consommés concordent avec les deux fichiers officiels ; la route
reste serverless.lelabs.tech vers 18090 avec TLS. La revue finale ne relève
aucun défaut bloquant sur la clôture et ses procédures. Aucun registre
d’incohérences ouvert ni remote Git configuré.

Cette tranche clôt le raccordement des mutations, pas SLS-040/050. Le moteur
d’admission, les budgets et générations, min/max/inactivité, la passerelle
authentifiée, les observations et commandes de console restent à réaliser.
Le goal demeure actif avec l’ensemble de ses exigences.

### SLS-040 — raccordement du moteur et de l'entrée publique

Le tour précédent est classé progrès : f5fc86b, 161 groupes qualifiés, arbre
propre et copie documentaire recoupée. La prochaine unité raccorde les pilotes
existants à la réservation durable, la file, les générations et la passerelle.
Les explorations en lecture seule confirment les interfaces utilisables et
l'absence actuelle de reprise d'instances dans le nettoyage de validation.

Le contrat précise la migration 005, le canal par UUID réservé, les observations
publiques autorisées et la persistance de la notification du handler. L'UUID
d'instance sera fourni au constructeur avant tout effet externe ; modifier son
id après construction laisserait ses labels et son nom incohérents. La reprise
inventorie réseaux et baux même lorsqu'aucun conteneur n'a pu être créé.

Les preuves de cette unité passeront par HTTPS avec de vrais jetons et handlers
de qualification : chaud/froid, limites et file, déconnexion, min/max/inactivité,
générations, révocation en attente, stockage, origine/IP, reprise et logs. Les
budgets de cellule seront proposés et appliqués par la console normale avant
le déploiement ; aucune preuve de composant ne remplace cette qualification.

La revue initiale a identifié deux pertes possibles de responsabilité sous panne
SQL : arrêt interrompu avant fermeture des instances, et finalisation laissant
une instance busy sans propriétaire. Le moteur joint maintenant une tâche
portant toute la fermeture ; la finalisation garde sa responsabilité jusqu'à
publication atomique de l'état terminal et du retour ready, ou fermeture puis
reprise des métadonnées. Ses transactions échouent immédiatement sur contention
pour laisser sa boucle traiter les autres propriétaires. ArtifactError du
nettoyeur fait partie des refus récupérables. Ces corrections restent à éprouver.

La session SSO arrivée à expiration est renouvelée par le parcours normal avec
l'accès déjà autorisé ; seul le cookie de plateforme est conservé. La première
requête d'invocation sur la baseline donne bien 404, sans identifiant
d'invocation. Son rapport reste en échec. Le client utilisait une route de
révocation inexistante ; il est corrigé vers POST /tokens/{id}/revoke. Les deux
jetons exacts sont révoqués et les suppressions de fonction/namespace confirmées
dans une preuve de récupération distincte. Aucun succès n'est attribué à ce run.

Les cinq budgets sont appliqués par la console. La sauvegarde native avant
005 est intègre, mode 0600, conserve 136 archives et confirme l'absence d'objet
actif et d'intention de stockage avant migration.

Le premier démarrage de 005 révèle un appel d'inventaire Docker avec une borne
de réponse que Docker.call ne transmettait pas. La santé reste à 503 ; la
signature est corrigée et le démarrage suivant devient sain. Les onze groupes
nominaux passent ensuite. La campagne élargie passe vingt-deux groupes et son
nettoyage ; son dernier groupe échoue : le refus de corps incomplet est bien
persisté après trente secondes mais le client HTTP/1.1 ne reçoit rien avant
son propre timeout. Ce rapport reste en échec.

Un diagnostic réel distinct mesure le 408 HTTP/1.1 après terminaison du corps
(30,197 s, après observation du refus durable), puis le 408 HTTP/2 sans terminer
le corps (30,123 s). Le proxy d'entrée attend donc encore les octets du corps
HTTP/1.1 ; le contrôle a déjà libéré sa place. Ce comportement correspond au
[contrat Caddy de communication HTTP/1](https://github.com/caddyserver/caddy/blob/master/modules/caddyhttp/server.go).
Décision : documenter et mesurer les deux transports, sans modifier la FORGE.
Le délai du contrôle demeure trente secondes et aucune invocation n'est admise.
Le diagnostic conserve ses deux groupes réussis et son nettoyage, séparément
de la campagne échouée. La preuve finale ne prétendra pas qu'HTTP/1.1 reçoit
un refus anticipé avant la fin de son corps sur cette infrastructure.

Une relecture ciblée relève le rejet secondaire sous contention SQLite :
l’erreur d’enqueue tente un reject, dont l’écriture échoue à nouveau. La
réponse sort alors de l’enveloppe publique et perd UUID/CORS. Le diagnostic
HTTPS reproduit le message générique à la place de execution_unavailable ;
son nettoyage réussit et le rapport reste en échec. La décision de rejet est
déjà conservée en mémoire avant l’écriture ; les routes peuvent donc différer
la seule persistance en conservant la responsabilité de reprise. La correction
protège les trois appels de rejet/déconnexion contre sqlite3.Error, sans
rendre silencieux les autres appelants du moteur ni retirer l’attente tôt.

Le correctif de rejet passe le même diagnostic HTTPS sur l’image
9bd48a3183b98c01bdaca28641995fe4ac4e1912ff2bdd9065f6334bf5fee04d :
503, UUID, CORS et reprise des états durables sont vérifiés. La preuve finale
ajoute une déconnexion réellement en file et exige, avant restitution SQL,
les événements corrélés de décision différée pour les deux déconnexions et
le rejet. Ces événements fixes sont émis une seule fois par rejet en attente.

Le scénario global de réception a connu un passage incomplet : seules trois
fonctions avaient reçu des demandes, sans résidu après nettoyage. Son rejeu
isolé atteint les 128 réceptions. Le banc ouvre désormais les connexions par
lots de seize, attend leur observation réelle, puis exige toujours 128
réceptions simultanées et le refus de la suivante. Les états de transport
client sont conservés pour diagnostiquer un nouvel échec ; aucune pause
arbitraire ni réduction du plafond attendu n’est introduite.

La campagne complète observe bien 128 réceptions simultanées avec cette
ouverture par lots. L’instrumentation du client ajoutait toutefois un listener
secureConnect à chaque réutilisation d’un socket déjà connecté, d’où un
avertissement Node sans échec des requêtes. Elle n’installe désormais ce
listener que pendant une connexion effective. La campagne finale sera rejouée
avec cette correction du client ; l’application déployée n’est pas modifiée
par cette instrumentation.

La première régression du stockage après les 31 groupes d’invocation passe
12 groupes puis échoue pendant la publication avec confirmation suspendue :
503 de la base du contrôle, avant observation de storage_version par le garde.
Le rapport reste en échec, y compris son garde ; les volumes, baux et objets
créés sont néanmoins supprimés et la santé du stockage est recoupée à zéro.
Le diagnostic isolé création/écriture/publication/rollback/suppression passe
ses quatre groupes sur la même image. Pour identifier une éventuelle course,
le journal database.unavailable ajoute le nom d’erreur SQLite et la dernière
position statique du code ; aucun SQL, argument ou contenu de requête n’est
journalisé. La campagne complète doit être rejouée avec ce diagnostic.

Le rejeu intégral du stockage sur l’image de diagnostic d7621027 passe les
14 groupes avec nettoyage confirmé. Il ne reproduit pas l’erreur initiale.
La contention transitoire liée aux ouvertures/fermetures WAL reste une
hypothèse de revue, pas une cause établie ni un défaut annoncé corrigé.
La clôture conserve cet échec et ses deux diagnostics séparément des rapports
frais de la suite finale ; celle-ci rattache les treize commandes à leurs
sources, image et empreintes de rapports avant/après exécution.

Le deuxième passage sériel échoue au groupe de confirmation avec audit occupé,
après observation de la préparation. Le diagnostic corrélé à la requête révèle
SQLITE_READONLY au BEGIN de transaction, et non SQLITE_BUSY. Les lectures root
répétées de la base du contrôle sont donc instruites. Une trace strace réelle
sur le SPARK observe openat(O_RDWR|O_CREAT) du WAL puis fchown(1001,1001), et
la même séquence pour SHM. Leur propriétaire final correct n’exclut pas la
fenêtre de création sous root. La règle de diagnostic est précisée dans
ADMISSION : tous les accès CONTROL des gardes utilisent l’identité effective
du compte propriétaire, avant de retrouver root pour les signaux et systemd.
La preuve doit rejouer les gardes réelles et contrôler la restauration des
identités ; aucune reprise SQLITE_BUSY n’est ajoutée au moteur sur cette base.

Le contexte propriétaire est appliqué aux lectures et writers des gardes de
stockage, d’exécution et de plafond, ainsi qu’au collecteur final. Une preuve
système réelle effectue trente lectures puis un writer sur CONTROL : UID/GID
1001, WAL/SHM 1001, restauration complète de root et des groupes ; la trace ne
contient plus de fchown après création. Les clients E2E exigent ces identités
pour leurs gardes. La revue ne relève pas de fuite de connexion ou d’identité ;
le prérequis de synchronisation inclut maintenant control_database.py.

La suite finale du moteur termine ses treize campagnes en série : 252 groupes
réussis, zéro échec et zéro skip. Les empreintes fraîches sont recoupées pour
chaque rapport avec l’image et les 93 sources locales/distantes avant et après
sa commande. Les sept JPEG sont observés et les trois notes appliquées puis
relues par la console. La preuve execution-dev-2026-11-06.json vérifie aussi
les artefacts embarqués, la configuration consommée, les archives de code
retenues et l’absence de ressources actives résiduelles. Elle conserve les
diagnostics antérieurs séparément ; aucun échec n’est requalifié en succès.
SLS-040/SLS-050 restent partiels pour les éléments explicités dans le backlog.
Aucun remote Git n’est configuré ; le changement est conservé en commit local.

Le hook de commit relève ensuite le lien de backlog manquant dans le commentaire
`@spec` de `e2e/control_database.py`. Ce seul commentaire est complété ; le
reste du fichier et son code compilé sont identiques. Les empreintes avant/après
sont conservées séparément dans la preuve finale, sans réécrire les captures de
sources prises pendant les treize campagnes ni rejouer celles-ci pour un commentaire.

### Console des exécutions — décision de tranche

Après le commit moteur 675de3e et ses 252 groupes réussis, SLS-061 ajoute les
facettes Instances et Invocations à la fonction. Les deux explorations de sources
confirment que les API existantes suffisent. Cinq lignes bornent les mesures
Docker séquentielles et les journaux inclus dans chaque réponse. Le rafraîchissement
reste manuel ; une scrutation accumulerait des requêtes et déplacerait le contenu
pendant la lecture. Les états et métriques manquantes ne sont jamais convertis
en zéro. Les liens de facette préservent la configuration actuelle et évitent
d’allonger sa page avec les historiques. La décision et les preuves attendues
sont persistées avant implémentation. Aucun remote Git n’est configuré.

La relecture détecte deux descriptions périmées : CONTROL présentait encore les
paramètres comme seulement stockés et e2e annonçait la qualification finale en
cours. Ces descriptions sont corrigées vers la preuve moteur déjà enregistrée.

### Console des exécutions — qualification du 7 novembre

Les facettes partagent l’identité de fonction et les sections de configuration
existantes. La revue corrige le focus d’Actualiser lors du recalage automatique
d’une page disparue, puis renforce les preuves de mesures rendues, défilement
clavier et suivi des créations en cas de navigation échouée. Les lectures
de corps Playwright après navigation échouaient réellement ; le banc retient
le statut et retrouve l’objet par son nom exact dans l’API avant de contrôler
la destination. Les promesses de réponse sont jointes immédiatement aux gestes.

Les tentatives initiales ont révélé des prérequis de banc : If-Match à la
publication, mesures Docker parfois partielles, attente des lignes effectivement
rendues après pagination et drainage de génération avant un appel avec file
réglée à zéro. Les rapports échoués et leurs nettoyages restent sous .local/e2e.
Un premier passage ciblé termine douze groupes. La capture pleine page du
journal est ensuite prise depuis le haut de page, conservant son défilement
interne, pour éviter l’inclusion hors viewport du lien d’évitement fixe.

La revue du runner détecte qu’un exit zéro ne suffisait pas à établir completed.
Il relit désormais le JSON dont l’empreinte est recoupée : nombre attendu, états,
fin, échecs/skips et nettoyage selon le schéma. La suite finale termine ses
quatre campagnes avec 40 groupes réussis, zéro échec et zéro skip ; chaque
rapport est frais et son contenu validé. L’image finale est `sha256:ff953f8e39871c060618482f6ecb4a88fc8026d2da93f80efe1565f83be30b21`.

Le principal observe les douze nouvelles captures ; le vérificateur observe
les sept captures de gestion et six de connexion. Leurs SHA256 sont recoupés ;
l’état Git avant/après cette vérification est identique. Les vingt-cinq vues
ne présentent pas d’anomalie bloquante dans les états capturés. Les limites de
capture pleine page et l’état de chargement du namespace mobile sont nommés.

La preuve console-execution-dev-2026-11-07.json vérifie 96 sources, 27 fichiers
embarqués, 286 archives conservées, ressources servies et configuration
officielle. Elle confirme l’identité du backend avec la preuve moteur et
l’absence de ressources actives de campagne. Trois notes sont appliquées et
relues par la console normale. SLS-061 est clos ; SLS-060 et l’objectif global
restent ouverts. Aucun registre d’incohérences ne subsiste pour cette tranche.
Aucun remote Git n’est configuré ; le commit reste local.

### Manuel accessible depuis l’application — décision du 7 novembre

La demande révèle une lacune : le manuel est maintenu dans docs/manual.md mais
aucune page de console ni entrée Docker ne l’embarque. L’exploration indépendante
confirme le constat. SLS-062 le raccorde au build Vite et à une destination de
navigation avec sommaire. Le document unique évite une divergence éditoriale ;
le rendu à la construction évite une route serveur et un parseur navigateur.
Ce texte d’usage n’est pas confidentiel. Les liens de chantier sont retirés du
guide ; les liens non servis sont refusés au build. markdown-it 15.0.3 est retenu
comme dépendance de construction verrouillée (MIT, publication vérifiée dans le
registre npm) ; audit des dépendances et preuves réelles précèdent la livraison.
Les deux design systems ont été lus ; la publication UI reprendra après cette
unité. Aucun remote Git n’est configuré.

### Manuel intégré — preuve et clôture du 7 novembre

Le build lit directement docs/manual.md, compile ses neuf chapitres et exclut
le parseur de l’artefact navigateur. Le guide est autonome et son entrée de
navigation possède un état courant distinct de Namespaces. Les ancres sont
partageables, focalisées et restaurées après rechargement de la session.

La revue indépendante renforce deux preuves : toutes les cellules du tableau
sont comparées au source et le corps de texte à 200 % est mesuré, sans prétendre
être un zoom du navigateur. Le client autonome refuse aussi une erreur JavaScript
reçue tardivement, après fermeture. La mention de qualification interne restante
est retirée du guide. Les deux constats sont fermés à la relecture.

Huit groupes ciblés passent. La première inspection révèle que deux captures
d’entrée montraient le sommaire après son ancre ; le banc rouvre alors le manuel
par sa navigation avant de photographier son titre, avec scrollY égal à zéro.
La suite finale rejoue cinq campagnes et passe 48 groupes, zéro échec et zéro
skip. Les sept captures du manuel sont relues, puis une huitième vue du tiroir
mobile est capturée depuis l’accueil et inspectée séparément. Elle n’ajoute
pas un groupe au total. Les 25 captures de régression sont relues par les
vérificateurs ; l’arbre Git est identique avant/après leurs lectures.

La preuve manual-console-dev-2026-11-07.json recoupe sources, image, documents,
rapports frais, 33 captures, archives conservées et ressources nettoyées.
Les notes SPARK sont appliquées par la console normale puis relues. Le manuel
affiché correspond à la source, avec 22 paragraphes et le tableau vérifiés.
L’audit des dépendances verrouillées ne signale aucune vulnérabilité connue.
SLS-062 est clos, l’objectif global reste actif. Aucun registre d’incohérences
ne subsiste pour cette unité ; aucun remote Git ne permet un push.

### Publication depuis la console — cadrage du 7 novembre

Les explorations indépendantes des API et des preuves existantes sont recoupées
dans les sources. La préparation complète remplace les secrets de fonction ;
la console ne peut donc pas la reconstruire depuis sa lecture expurgée. Une
route additive de publication du code capture côté serveur la configuration
courante et les événements, avec le handler choisi. Le contrat CLI reste stable.

Un UUID choisi avant envoi permet de retrouver la préparation après réponse
perdue ; son unicité refuse le rejeu. La liste des candidats reste réservée aux
administrateurs pour conserver la confidentialité des diagnostics entre jetons.
L’abandon d’un candidat préparé libère explicitement sa place. Les états et le
schéma existants suffisent ; aucune migration ni dépendance n’est nécessaire.

SLS-063 conserve l’upload ZIP réel, les droits et versions existants. Le suivi
ne promet pas de reprise de transport après rechargement. L’historique borné à
vingt révisions suffit à une pagination locale de cinq ; les tentatives utilisent
une pagination serveur. Lecture de code et éditeur ne font pas partie de ce
parcours. Le manuel évoluera avec l’implémentation ; aucune preuve n’est encore
revendiquée pour cette unité. La réponse précédente au sujet du manuel était
un état des lieux, sans progrès supplémentaire du produit ; cette unité reprend
le travail concret après revalidation de l’arbre propre à d8e7dcf.

### Publication UI — checkpoint ciblé du 7 novembre

Les routes additives et la facette Code et révisions sont déployées. La
préparation capture les réglages et secrets côté serveur ; le navigateur suit
l’UUID créé avant envoi. Le manuel passe à onze chapitres et décrit les gestes
de publication et d’historique. Aucun schéma ni dépendance n’est ajouté.

Les campagnes ont révélé des défauts de preuve et d’interface : lecture de
réponse après navigation, ancienne page de résultats affichée sous le nouveau
numéro, réessai de la même page après erreur sans nouvelle lecture. Le banc
recoupe désormais les créations par leurs noms/UUID et les listes par leurs
identifiants exacts. L’interface ne change le numéro affiché qu’avec les données
reçues, rend immédiatement le chargement visible et relit aussi une sélection
identique. Une préparation refusée à 4xx conserve le fichier et le formulaire.

La rupture de réponse est éprouvée en quittant réellement le document après
commit observé ; la latence Chromium seule ne garantissait pas l’annulation
de la requête. Le retour retrouve le même candidat préparé sans upload.
Les rapports d’essais échoués et leurs nettoyages sont conservés sous .local.

La preuve intermédiaire recoupe dix groupes API, quatorze navigateur et huit
manuel, tous réussis sans skip. Les 109 sources sont restées identiques au build
durant ces campagnes ; image, fichiers embarqués et ressources servies sont
recoupés. Deux revues indépendantes inspectent 21 captures et retrouvent l’arbre
inchangé. La capture nommée validating montre encore la réception et ne prouve
donc pas le libellé de validation. Les dimensions JPEG ne sont pas présentées
comme des tailles de viewport. Les 336 archives de code sont inventoriées ;
aucun objet actif, bail, réservation, instance ou workspace de test ne subsiste.

SLS-063 reste en cours : réponses perdues de mutation, 503 de nettoyage réel,
candidat d’une autre fonction, journal long/tronqué mobile, régression complète
et notes SPARK restent à terminer. Ce commit constitue un checkpoint conforme
au §13 de la méthode, sans clôture d’unité. Aucun remote Git n’est configuré.

### Publication UI — choix de la panne physique

L’exploration du DELETE et de remove_tree confirme que le parent artifacts/UUID
est ouvert avant tout fchmod ou unlink. Un mode 000 sur ce seul parent permet
de prouver le 503 après commit sans toucher au contenu. Le vrai processus
Docker doit confirmer EACCES et ses capabilities nulles ; son UID root dans
l’espace rootless ne suffit pas à déduire le résultat.

Le garde indépendant termine le seul helper éphémère identifié par PID et
naissance avant restauration à échéance, afin d’empêcher un chmod tardif après
une suspension du helper. La reprise se constate par la maintenance normale,
pas par une écriture SQL ni un appel direct au nettoyage. Les préconditions
excluent les consommateurs et nettoyages étrangers. Cette décision complète
les preuves de SLS-063 ; elle ne change pas le comportement du produit.

### Publication UI — régression commune

Les campagnes moteur et console partagent les parcours publics et de gestion.
La qualification de publication les réunit dans un scope dédié, dédupliqué par
nom de campagne, afin que chaque preuve soit exécutée une fois sur les mêmes
sources et image. Cela évite aussi d’écraser un rapport utilisé par une première
suite lors de l’exécution d’une seconde. Les scopes existants restent utilisables.

### Publication UI — première régression et constats visuels

Les dix-huit campagnes passent 312 groupes, sans échec ni skip. Les 144 sources
restent identiques pendant la suite ; l’image b969a756, les fichiers embarqués,
ressources servies et 434 archives sont recoupés. Aucun objet actif, bail,
montage, opération pendante ou instance de qualification ne subsiste.

La revue de 54 captures constate deux défauts : la liste peut afficher un état
antérieur à celui du suivi du même candidat, et une ancienne confirmation de
succès reste visible après une actualisation portant sur une autre publication.
Le principal confirme les captures et le flux de lecture ; les issues retenues
sont persistées dans CONSOLE_PUBLICATION et le registre avant correction.
La capture de confirmation de stockage, limitée par une condition de nom trop
large, sera aussi reprise en pleine page ; seule la modale de confirmation
mobile doit conserver sa capture de viewport.

Les rapports et images de cette première suite sont conservés sous
.local/e2e/publication-regression-first-312 et leur bilan recoupé est versionné.
SLS-063 reste ouvert. Une nouvelle qualification suivra la correction de ces
incohérences ; aucune clôture ne repose sur les seuls comptes de tests.

### Publication UI — résolution SLS-063-OBS-1

La lecture individuelle du candidat suivi remplace sa ligne de liste dans le
même cycle d’affichage. L’assertion DOM lit les deux badges en une observation
et exige leur concordance pendant la vraie validation Docker. Les 21 groupes
navigateur passent ; la capture est inspectée et montre les deux libellés de
validation pour le même UUID. La preuve ciblée est
`evidence/publication-observation-correction-dev-2026-11-07.json`.

L’image 52d17fa1 contient aussi la correction de succès, résolue séparément dans
le commit suivant. Les empreintes de cet arbre qualifié sont conservées ;
aucune preuve n’est attribuée au seul arbre intermédiaire du premier commit.
La campagne complète et la clôture SLS-063 restent à faire. Aucun remote
Git n’est configuré.

### Publication UI — résolution SLS-063-OBS-2

Les consultations explicites effacent le succès précédent sans effacer les
diagnostics d’erreur ni la confirmation de stockage en attente. Une revue a
relevé que les assertions initiales arrivaient après plusieurs gestes : la
preuve constate désormais un succès réel avant chacun des cinq parcours, puis
sa disparition après un seul geste (actualisation, autre tentative, pagination
des révisions, des tentatives et actualisation hors ligne).

La campagne navigateur rejouée passe ses 21 groupes ; le manuel reconstruit
passe huit groupes et 28 paragraphes recoupés. Le principal inspecte les
captures de stockage en attente, d’erreur réseau et du manuel. La preuve ciblée
est `evidence/publication-success-correction-dev-2026-11-07.json`. Les rapports
et 29 captures sont conservés sous .local/e2e/publication-consistency-29.
Le registre devenu vide est supprimé. La régression commune de 18 campagnes,
la revue complète et les notes SPARK restent nécessaires avant clôture.
Aucun remote Git n’est configuré.

### Publication UI — qualification finale

Après les corrections b4d260c et 6934f80, les dix-huit campagnes sont rejouées
séquentiellement : 312 groupes réussis, zéro échec et zéro cas ignoré. Les 144
sources et l’image restent identiques avant/après chaque campagne. La revue des
54 nouvelles captures confirme les corrections et les parcours de console ;
son relevé recoupe les fichiers et l’absence de modification de l’arbre.

L’enveloppe d’exécution a renvoyé 143 après l’écriture du rapport atomique
complet. Les dix-huit commandes y ont toutes un retour zéro. Le collecteur
indépendant, terminé à zéro, recoupe les rapports frais, sources, image et
nettoyages ; cette anomalie d’enveloppe est conservée dans la preuve, sans
cause inventée ni déclaration d’un retour zéro pour l’enveloppe initiale.

Les trois notes de cellule sont maintenues dans qualification/spark-notes,
proposées via les fichiers .? puis appliquées par la console normale du SPARK.
Leur contenu officiel est relu et recoupé. Le manuel reste la source unique,
avec ses onze chapitres et 28 paragraphes vérifiés dans l’application.
Le collecteur final vérifie code embarqué, ressources servies, archives et
absence de ressources actives de campagne ; ses détails sont versionnés dans
`evidence/publication-console-dev-2026-11-07.json`. Les rapports et les
54 images de cette exécution sont conservés sous
`.local/e2e/publication-console-qualified-312`.

SLS-063 est clôturée. Les unités parentes conservent leurs preuves résiduelles,
les commandes de purge/cache et les crons ; le goal de plateforme reste actif.
Aucune migration ni nouvelle variable n’est nécessaire. Aucun remote Git
n’est configuré ; le commit reste local.

### 7 novembre — reprise fiable des effacements

Après SLS-063, deux explorations bornées relisent les opérations de stockage
et les précédents de décision du contrôle. Le principal recoupe le code :
purge/clear-cache n’ont pas de reçu corrélé et erase garde le verrou global.
La répétition d’un cache vidé pourrait effacer une nouvelle écriture.

Décision : SLS-064 ajoute start-discard/discard-operation, un reçu versionné
par fonction et un worker unique supprimant hors verrou. La version initiale
obligatoire empêche un rejeu après remplacement du reçu ; une phase finalizing
protège la recréation du cache. Le protocole historique est conservé pour ses
clients opérateur. Une répétition aveugle et une simple inférence depuis la
version sont écartées car elles ne prouvent pas l’issue d’un UUID donné.

SLS-065 raccordera ensuite droits, catalogue d’archives et parcours de console
avec le manuel. Ce découpage isole une garantie nécessaire avant les effets
publics irréversibles. Spécification, schéma, installation et backlog sont
persistés avant code. Aucun remote configuré ; commit local uniquement.

### Effacements — première qualification et précision de preuve

Le paquet agent 409d887c est installé après backup natif du registre 003 ;
la migration 004 conserve l’identité de stockage. La première campagne passe
12 groupes et nettoie ses ressources. La revue corrige auparavant la référence
de worker terminée en erreur et le fsync du parent après disparition du montage.

La preuve SQLite initiale reste trop indirecte (attente puis pending). Décision :
ajouter un diagnostic JSON fixe lors de l’observation effective de l’exception
du worker et l’exiger sous le vrai verrou SQLite. Garantir la fermeture continue
du writer et recouper tous les UUID sur disque au nettoyage. La campagne sera
rejouée avec six régressions en série ; le premier rapport reste un checkpoint.

### Effacements — qualification finale de SLS-064

La suite storage termine à zéro : 12 groupes propres aux effacements, puis
15 de cycle agent, 8 de limites, 12 de préparations, 14 de baux gérés,
14 de mutations publiques et 31 d’invocations HTTPS. Les sept campagnes
restent sérielles, sans substitution ni test ignoré. L’exception SQLite du
worker est effectivement observée dans le journal sous writer réel ; sa
reprise conserve le même PID. La phase erasing est observée lors du check,
de la libération puis de la réacquisition d’un autre bail.

La preuve finale recoupe le registre 004, le paquet installé, les empreintes
des sources, l’image du contrôle, les rapports frais et les ressources
libérées. Les lignes antérieures à migration sont comparées au backup natif.
Les archives de code suivent leur rétention ; elles sont vérifiées sur disque.
Les notes SPARK sont mises à jour par leurs propositions et relues après
application. Le registre d’incohérences ne contient aucune entrée ouverte.

Cette unité livre le protocole privé de l’agent ; SLS-065 portera le catalogue
d’archives, les droits publics et les parcours de console avec leur manuel.
Aucune interface n’a changé dans SLS-064 ; sa vérification est celle des
composants et API réels. Le goal de plateforme reste actif. Aucun remote Git
n’est configuré, donc le commit reste local.

### Stockage public — décisions de SLS-065

Les explorations en lecture seule recoupent trois obligations : la purge de
code est déjà prescrite par DEPLOYMENT ; les parents supprimés restent en base
mais sont masqués par les lectures ordinaires ; le résolveur de garde traite
actuellement tout type non configuration comme archive. Ajouter un bouton ou
seulement un type SQL ne suffit donc pas.

Décision : reçus publics persistants distincts des gardes, UUID connu avant
POST et If-Match obligatoire, relecture des droits après drainage, décision
SQL avant tout effacement et confirmation séparée des volumes et du code.
Le reçu public ne dépend pas de la rétention du dernier reçu agent. La purge
efface aussi la configuration propre inutilisable d’une fonction supprimée,
en conservant audit et métadonnées de diagnostic ; elle ne touche pas celles
des parents. Une lecture d’archive reste possible après leur suppression.
Ces choix évitent une répétition destructive et une libération fictive de budget.

La console ajoute Stockage et Archives de fonctions ; confirmations dans le
flux, nom exact pour la purge irréversible, suivi par URL et aucune mutation
automatique au rechargement. Les deux design systems ont été lus intégralement.
CONSOLE_STORAGE, schéma, architecture, déploiement, backlog et design local
portent ces décisions avant implémentation. Le manuel changera avec les écrans.
La vérification du manuel existant vient de repasser ses huit groupes réels,
zéro skip, 28 paragraphes recoupés et sept captures relues. Aucun remote Git.

La revue du contrat relève un upload invalidé qui peut encore réécrire son
diagnostic après la décision de purge. Décision : effacement terminal des
résultats après jonction du propriétaire, en plus de l’effacement initial.
La synchronisation du parent doit couvrir tous les nettoyeurs existants,
même lorsque le répertoire a disparu. Enfin storage_absent désigne seulement
function_unknown, jamais un registre connu avec volumes vides. Contrat
précisé avant les corrections correspondantes, avec leurs preuves attendues.

La reprise du moteur et la maintenance peuvent demander la résolution du
même UUID. Une propriété de résolution en mémoire, distincte de la garde
durable, sérialise cette activité. Un UUID déjà pris est rejeté avant entrée
dans la responsabilité async, afin qu’un refus ne résolve pas la garde d’un
autre propriétaire. Ces invariants complètent le contrat avant raccordement.

### Stockage public — déploiement et checkpoint de qualification

Le contrôle applique 006 après sauvegarde native et contrôle d’inactivité.
Les anciennes lignes et les 2 705 fichiers d’archives sont préservés et recoupés.
La revue conduit à joindre le nettoyage réel des validateurs avant les artefacts,
à revérifier l’absence d’une ligne agent et à restituer le focus après le rendu.
La console distingue le nouvel UUID du reçu précédent et bloque une pagination
en erreur jusqu’à reprise de la page demandée.

Les premiers essais UI ont révélé deux erreurs du banc : libellé « Nom du jeton »
mal ciblé, puis comparaison des UUID avant le rendu après reprise réseau. Les
rapports échoués restent sous `.local/e2e/`. Les assertions corrigées sont
rejouées intégralement. Neuf groupes API et neuf groupes UI passent, avec
nettoyage. Le manuel repasse huit groupes : treize chapitres, 34 paragraphes,
source SHA256 identique au document servi. Quatorze captures stockage et onze
du manuel sont inspectées, dont les deux nouveaux chapitres sur mobile.
Les onze groupes de gestion passent ensuite ; leurs sept captures sont relues.

Le collecteur opérateur en lecture seule rattache les quatre fonctions aux
deux rapports, vérifie trois répertoires d’artefacts absents, volumes, montages,
canaux, Docker, gardes et compteurs. Il déchiffre les secrets uniquement dans
le conteneur et ne produit que des booléens de vide. Son premier passage refuse
une hypothèse erronée de propriétaire root du registre ; l’installateur et le
service réel imposent spark-docker. La lecture sous cette identité, avec
restauration de root et contrôle des WAL/SHM, réussit ensuite. Les réservations
globales d’instances/CPU/mémoire et les allocations de stockage valent zéro.

Le [checkpoint](evidence/storage-console-checkpoint-dev-2026-11-07.json) conserve
ces 37 groupes réussis et 32 captures inspectées. SLS-065 demeure ouverte :
révocation avant décision, collisions sous garde, pannes et reprises publiques,
validation encore vivante, apparition inattendue d’une ligne agent et régressions
élargies restent à éprouver. Le goal de plateforme reste actif.

### Identité du registre dans les anciens clients de preuve

La vérification de SLS-065 recoupe l’installateur, systemd et les fichiers :
le registre agent et ses WAL/SHM appartiennent à spark-docker. La mention root
du README E2E était erronée. Deux anciens helpers ouvrent encore ce registre
sous root, dont un writer de contention. Le contrat ADMISSION est précisé
avant correction : ouvrir, lire, rollback et fermer sous son propriétaire,
puis retrouver root pour les signaux. Les campagnes concernées seront rejouées.

La première régression des quatorze groupes réussit. La revue du helper relève
toutefois une fenêtre entre l'abandon de sa référence au writer du registre
et sa fermeture : un signal opérateur peut empêcher le `finally` de retrouver
ce writer. Le helper conservera donc sa responsabilité jusqu'à fermeture
effective, avec fermeture répétable et signaux d'interruption différés pendant
la transition d'identité. Une preuve exercera un vrai SIGTERM durant cette
transition, puis exigera la libération du verrou et les propriétaires WAL/SHM.
La régression complète sera rejouée après cette correction du banc.

### Reprises publiques du stockage et vérification du manuel

Sept groupes réels passent : perte du helper avec reprise de l’agent par sa
garde indépendante, agent suspendu et abandon avant décision, révocation Update,
collision avec la garde d’une autre fonction, SIGKILL avant décision, panne cache
après commit avec révocation et SIGKILL, puis artefacts inaccessibles avec reprise
de purge. Le code exécuté appartient aux fixtures du dépôt. Les mêmes reçus
terminent après reprise ; rejouer le vidage après reconstruction conserve le cache.

La correction d’identité des anciens helpers est qualifiée par quinze groupes
de mutation : les quatorze existants et un vrai SIGTERM pendant fermeture du
writer. La revue relève ensuite une lecture `in_transaction` sous root dans
la seule assertion du probe ; elle est replacée sous propriétaire et ce probe
rejoué avec succès. La lecture du registre par le helper d’invocation est aussi
exécutée sur une fonction de campagne existante. Le validateur de la suite
accepte le rapport réel de quinze groupes. La suite complète n’est pas rejouée
à ce checkpoint ; cette distinction est conservée dans la preuve.

La demande sur le manuel est vérifiée sur la console réelle, depuis l’accueil :
huit groupes, treize chapitres, 34 paragraphes et empreinte identique à la source.
Les onze captures ordinateur/tablette/mobile sont inspectées par le principal.
Le premier lancement de Chromium est refusé par le sandbox avant tout parcours ;
la relance avec l’autorisation système normale réussit. Aucun changement du
guide ni du rendu n’est nécessaire : la source unique et la règle de maintenance
sont déjà en place.

Le [checkpoint](evidence/storage-command-recovery-dev-2026-11-07.json) conserve
ces trente groupes et la chronologie exacte des sources. Le collecteur confirme
la purge des trois fonctions de reprise, l’absence de leurs fichiers et ressources,
et les budgets globaux à zéro. Les 25 fichiers Python/migrations embarqués sont
recoupés avec l’image inchangée. SLS-065 reste ouverte pour ses pannes résiduelles,
la validation vivante, les régressions élargies et les notes SPARK. Aucun remote
Git n’est configuré ; le checkpoint reste local.

### Purge pendant validation Docker encore active

Le tour précédent constitue un progrès vérifié : checkpoint `066ca0c`, sept
groupes de reprise, quinze de mutation et huit du manuel. La prochaine preuve
de SLS-065 vise la fenêtre entre DELETE, la fin d’un upload en validation et
son nettoyage. La revue des sources confirme que `busy` retient les artefacts
pendant l’upload, puis `cleanup_error` doit continuer à les retenir si Docker
n’est pas joignable. Le diagnostic de validation peut arriver après la décision
de purge ; la transaction terminale doit l’effacer de nouveau.

Décision de banc, persistée avant code : import réel de soixante secondes avec
marqueur, refus temporaire du seul socket rootless par permissions, restauration
indépendante systemd avant perturbation. Les inspections sous panne passent par
root sur le même daemon ; le contrôle doit constater EACCES. L’upload commence
avant l’attente du marqueur par le helper. Après restauration, aucun nettoyage
opérateur ne doit se substituer à celui du produit. Un scénario distinct éprouve
la garde par perte réelle du helper. Le contrat des preuves détaille ces bornes.

Le premier précontrôle refuse une hypothèse du banc avant toute perturbation :
le socket Docker relève d’UID 1001 et GID 1987, tandis que SQLite est 1001:1001.
Le daemon est bien rootless et le montage du contrôle correspond au fichier
officiel. L’identité du socket doit donc vérifier son utilisateur propriétaire
puis conserver son groupe réellement observé, sans l’assimiler à celui de la base.
Le mode observé est 01660 et devra être restauré exactement. Les deux fonctions
de cet essai sont purgées par leurs API, avec nettoyage réussi. Le rapport échoué
est conservé ; le précontrôle sera corrigé puis la campagne entière relancée.

La campagne relancée passe ses deux groupes ; le socket est restauré, le
nettoyage des quatre fonctions des deux essais est recoupé et les budgets
globaux sont à zéro. La revue de couverture relève deux exigences existantes
encore peu discriminées par les preuves : conflit d’UUID entre vidage et purge,
et réutilisation des noms après suppression des parents. La campagne API sera
complétée par ces assertions avant sa régression : le même UUID doit rester
attaché à son type ; une nouvelle chaîne namespace/service/fonction portant
les anciens noms possède d’autres UUID et conserve ses données lorsque l’ancienne
archive est purgée. Son rapport recensera chaque namespace et ses fonctions.

### Validation vivante et identité des archives — résultats recoupés

Les deux groupes de validation passent sur le vrai contrôle : la perte du helper
déclenche une restauration indépendante du socket, puis l’import atteint son
délai normal avec nettoyage du validateur. Dans le second groupe, la purge est
commise alors que le marqueur de l’import est vivant. Le refus Docker maintient
le reçu en attente, les réservations, le ZIP et le code. L’upload écrit ensuite
un diagnostic `cleanup_failed` ; après restauration, le produit termine le même
reçu, efface ce diagnostic tardif et libère fichiers, canaux et réservations.
La fonction voisine conserve code, données et cache.

Les neuf groupes API renforcés passent ensuite : réemployer l’UUID d’un vidage
pour une purge est refusé sans altérer le reçu ; recréer les trois niveaux sous
les mêmes noms attribue d’autres UUID, et purger l’ancienne archive conserve les
fichiers de la nouvelle fonction. Le rapport porte un mapping exact `campaigns`
pour les deux namespaces. Le collecteur recoupe quatre namespaces, huit fonctions
et neuf répertoires d’artefacts absents, avec budgets globaux à zéro. Il inclut
les deux fonctions de l’essai initial échoué au précontrôle et correctement nettoyé.

La [preuve](evidence/storage-validation-recovery-dev-2026-11-07.json) conserve
les onze groupes, les rapports complets, leurs empreintes et la chronologie des
sources. Chaque campagne possède le même inventaire de 159 sources avant/après ;
seul le client API a changé entre les deux campagnes. La synchronisation distante
comprend aussi le contrat, soit 160 fichiers. L’image du contrôle reste identique
au checkpoint précédent et ses 25 sources Python/migrations n’ont pas changé.
Les trois constats de revue sur les gardes ont été corrigés avant exécution :
PID réutilisé, attente de fin du helper avant restauration et nettoyage API
conditionné à la restauration effective du socket.

La vérification du manuel retrouve sa source unique, sa règle de maintenance et
ses huit groupes E2E déjà enregistrés au checkpoint précédent ; le guide et son
rendu n’ont pas changé. Aucun nouveau parcours UI n’est revendiqué ici. SLS-065
reste ouverte pour les pannes résiduelles, les régressions élargies et les notes
SPARK. Aucun remote n’est configuré ; ce checkpoint est conservé localement.

### Décisions publiques de stockage — prochaines preuves résiduelles

Le tour précédent est un progrès vérifié : commit `605c15f`, onze groupes
réussis et inventaire physique des huit fonctions nettoyées. Le contrat source
confirme la relecture de session après préparation et la reprise par le même
UUID après commit. Décision de banc avant code : campagne dédiée aux décisions,
avec une seconde vraie connexion SSO pour la purge révoquée. La déconnexion
supprime la session locale avant l’échange fournisseur ; le banc attend ce refus
local puis rend l’agent disponible avant l’expiration normale de sa lecture.

Les pannes après commit partent d’un vidage retenu par l’erreur physique déjà
qualifiée. Le refus du socket agent doit produire `storage_transport` ; le worker
agent peut continuer de son côté. Un writer réel du contrôle, sans écriture,
doit ensuite empêcher l’enregistrement du résultat malgré le reçu agent terminé.
Son diagnostic est recoupé dans les journaux par UUID. Après libération, le même
reçu doit terminer et son rejeu préserver le cache reconstruit. Le helper du writer
est tué pour éprouver sa garde indépendante. Le secours de redémarrage du contrôle
est également forcé, sans reprise opérateur anticipée. Les identités, gardes,
nettoyages et sessions séparées font partie des prérequis de cette campagne.

La revue avant lancement identifie une course entre le timer de secours et
un arrêt Docker retardé. Le restaurateur doit joindre le mutateur avant de
redémarrer. Le seul PID du helper ne couvre pas son enfant CLI ; décision :
verrou `flock` transmis au processus d’arrêt, encapsulé dans un `timeout`
indépendant. Le restaurateur attend ce verrou après terminaison du helper,
puis redémarre et retire le fichier privé. Le client attend aussi le retour
HTTP et borne la fermeture de SSH. Ces corrections précèdent toute perturbation.

### Décisions publiques — quatre nouveaux groupes et régression réussis

La seconde session SSO est obtenue depuis l’accueil réel, avec un cookie distinct.
Le premier lancement du navigateur n’avait pas de stdin maintenu ouvert ; le
processus est constaté terminé puis relancé avec une entrée privée, écho désactivé.
Aucun identifiant ni cookie n’entre dans les preuves versionnées.

Les quatre groupes passent au premier lancement de la campagne. Pendant purge,
la déconnexion ferme la session locale avant la décision ; le reçu est abandonné,
les fichiers, révisions et l’empreinte de configuration sont conservés. Sous refus
du socket, le reçu public porte `storage_transport` tandis que l’agent termine
son effacement. Sous vrai writer SQLite, le journal porte l’UUID attendu avec
`control_database_unavailable` ; la garde termine après libération. Le helper
du writer est tué et sa restauration indépendante est constatée, puis une nouvelle
acquisition prouve l’absence de verrou retenu. Le contrôle sorti en 137 est
redémarré par son timer ; le verrou du mutateur est joint et retiré.

Les mêmes UUID et versions terminent après reprise ; un rejeu conserve le cache
reconstruit. Les sept groupes de reprise existants passent ensuite pour vérifier
le helper commun modifié. Les rapports sont frais, les 160 sources identiques
avant/après chaque campagne et entre campagnes, avec la même image immuable.
La [preuve](evidence/storage-decision-recovery-dev-2026-11-07.json) conserve ces
onze groupes, l’état intermédiaire, les diagnostics et les empreintes des sources.

Le collecteur recoupe six fonctions purgées, six répertoires de code absents,
ressources libérées et budgets globaux à zéro. Un contrôle de restauration séparé
confirme agent actif, contrôle sain, exécuteur de référence actif, accès aux deux
sockets, six timers corrélés inactifs et absence de verrou de redémarrage.
SLS-065 reste ouverte pour l’apparition inattendue après `storage_absent`, la suite
commune et ses régressions élargies, puis les notes SPARK. Le produit, le manuel
et les écrans n’ont pas changé dans ce checkpoint. Aucun remote Git configuré.

### Archive antérieure au registre — décision de banc avant implémentation

Le tour précédent est un progrès vérifié : commit `148bb57`, onze groupes et
restauration physique recoupés. Le dernier cas de panne SLS-065 exige une archive
dont l’absence agent a été réellement persistée, puis contredite par une création
opérateur. L’ancienne version `93f88e5c543be4ad41e4ca22d08cbedbabec73c5` produit
cet état par ses API ; les schémas de requête et l’absence d’appel agent ont été
relus. Son authentification et ses dépendances Python sont identiques aux actuelles.

Le briefing actuel du SPARK confirme l’interdiction des surcharges de configuration.
Décision : conserver les trois répertoires par renommage, propriétaires arrêtés,
et créer l’installation temporaire aux mêmes chemins officiels. Une garde
indépendante restaure les originaux par identité avant de relancer l’agent puis
le contrôle original. La variante à chemins injectés est écartée car elle ne
respecterait pas ce contrat. Un montage par-dessus les répertoires est également
écarté, car sa visibilité dans les espaces de montage rootless serait ambiguë.

Le [contrat dédié](STORAGE_LEGACY_PROOF.md) précise les précontrôles, backups,
étapes partielles, versions, deux archives et nettoyage. Le cas contradictoire
ne peut pas terminer par une purge métier : l’agent conserve même les tombstones.
Il est donc cantonné aux registres temporaires, qui seront retirés entièrement.
La garde sera réellement exercée après le premier déplacement, avant le parcours
historique complet. Aucune preuve de redémarrage complet du SPARK n’est revendiquée.

### Archive historique — défaut réel du nettoyage général

L’image exacte de `93f88e5` est reconstruite avec ses sources et dépendances.
Le client Docker actuel diffère seulement par la limite de réponse optionnelle,
recoupée explicitement. Un premier précontrôle a refusé à tort le mode 0750
du répertoire de contrôle, avant toute interruption ; il conserve désormais ce
mode original. Un second essai a rencontré le cwd `/root` inaccessible à Compose
sous spark-docker ; les originaux ont été restaurés puis le cwd fixé au projet.
Ces essais restent distingués des groupes fonctionnels.

La mort du pilote après le premier renommage passe : garde indépendante,
identités des trois répertoires, empreintes logiques des bases et inventaire des
artefacts identiques, API et agent sains, exécuteur de référence inchangé.
Le parcours complet ouvre une vraie session SSO de l’ancienne API, publie deux
ZIP validés dans Docker, supprime les fonctions puis applique 004–006 normalement.
La session et les archives persistent ; la première purge termine avec absence
agent persistée et aucun reçu inventé.

Pour la seconde archive, le refus réel d’accès à l’artefact retient la phase
artifacts. Le protocole `configure` crée réellement une ligne agent, puis les
permissions sont rétablies. Le reçu reste `pending/storage_state_changed`, mais
le redémarrage efface le répertoire de révision et libère ses 36 Kio. La
[preuve avant correction](evidence/storage-legacy-cleanup-defect-dev-2026-11-07.json)
conserve les relevés intermédiaires, l’échec et la restauration des originaux.

Décision : le nettoyage général laisse les artefacts d’une fonction portant une
garde de purge à son seul résolveur. Cette règle vaut pour révisions et candidats,
au démarrage comme en maintenance. Elle empêche de contourner le contrôle du
stockage tout en permettant le nettoyage après abandon/terminaison de la garde.
Le contrat CONSOLE_STORAGE est corrigé avant l’implémentation. Le statut SLS-065
reste ouvert ; aucun résultat de cette campagne en échec n’est présenté comme
une qualification du comportement corrigé.

### Correctif du nettoyage historique — checkpoint vérifié

`Deployments.clean_candidate()` et le nettoyage des révisions consultent
désormais la garde de purge de la fonction avant tout effacement ou libération
de compteurs. Le résolveur de purge conserve son accès direct au nettoyage,
avec relecture du stockage et verrou d’activité ; il ne se bloque pas lui-même.
La revue ciblée confirme ce chemin, y compris après validation tardive.

Le contrôle corrigé et le manuel sont construits puis déployés en DEV. Les
quatre groupes historiques passent ; le même cas qui effaçait le code conserve
son répertoire et ses 36 Kio après redémarrage, avec le même reçu en attente.
Les deux groupes de validation vivante puis les sept groupes de panne passent
en série. La garde de restauration est réexercée après le premier renommage,
puis les huit groupes du manuel sont rejoués. Au total : 22 groupes, aucun
échec/skip sur cette image. Les essais antérieurs en échec restent conservés
séparément et ne sont pas comptés comme réussites.

La [preuve corrigée](evidence/storage-legacy-recovery-dev-2026-11-07.json)
recoupe les rapports frais, les 163 sources identiques avant/après et entre les
cinq campagnes, l’image immuable et les 25 fichiers Python/migrations embarqués.
Le collecteur confirme la restauration des deux fenêtres finales et leurs gardes
inactives. Cinq fonctions de régression, sept répertoires de code et les budgets
libérés sont vérifiés physiquement. Les onze captures du manuel et une capture
supplémentaire de son nouveau paragraphe mobile sont inspectées ; les 35 paragraphes
affichés correspondent à la source. L’essai ponctuel de capture lancé depuis la
racine sans chemin de résolution Playwright a échoué avant ouverture du navigateur ;
la dépendance existante de `e2e/` a ensuite été utilisée normalement.

SLS-065 reste ouverte pour l’intégration de toutes ses campagnes au runner commun,
les régressions élargies et les notes SPARK. Aucune nouvelle migration ni
configuration de cellule. Aucun remote Git configuré ; aucun push effectué.

La revue finale a relevé un chemin d’erreur du client de preuve qui relançait
l’exception Playwright originale après restauration. Sa sortie est remplacée
par un diagnostic fixe ; une entrée JSON invalide portant une valeur synthétique
est réellement refusée sans reproduire cette valeur dans stdout, stderr ou le
rapport. Ce contrôle du client précède toute fenêtre et reste distinct des
groupes de plateforme. Les cinq campagnes et leurs 22 groupes sont ensuite
rejoués en série ; les rapports finaux et le recoupement physique correspondent
à ce client corrigé. Aucun changement supplémentaire de l’image du produit.


## 2026-11-08 — Configuration commune et domaines d’invocation

Le responsable rappelle que jetons, variables et secrets doivent être gérés au
niveau du service, et demande le calcul des URL depuis les domaines du SPARK.
Lecture de la console, de l’API, du moteur et de l’adaptateur : les trois objets
existent au niveau du service, mais le déploiement YAML aplatit la configuration
provider dans chaque fonction. La référence présente bien provider.env et
provider.secret. Le catalogue d’URL multi-domaines manque.

Décision persistée dans SERVICE_CONFIGURATION_URLS.md : préserver la
configuration commune et les surcharges explicites, lire les routes affectées
à la passerelle sans administrer la FORGE, exposer les URL calculées et maintenir
le manuel compilé. Conversion des deux écarts en unités SLS-031 et SLS-066,
non commencées. Les scénarios réels requis sont nommés dans le contrat.
Cette inspection et cette spécification ne sont ni un déploiement ni une
nouvelle preuve E2E ; les modifications de purge en cours restent distinctes.

### SLS-031 — Sémantique de remplacement avant implémentation

Une catégorie provider absente préserve le service ; une catégorie présente
remplace ses clés. Les valeurs locales null rétablissent l’héritage, ce qui
remplace l’ancien masquage produit par l’aplatissement. La configuration commune
est appliquée après préparation locale et avant les publications en série,
avec Update et If-Match. Son résultat est séparé dans le rapport : un import
refusé conserve son ancien code mais n’annule pas une modification commune
déjà appliquée. Les valeurs de secrets ne pouvant être comparées, leur déclaration
exige toujours Update. Ces règles rendent les droits et les échecs partiels
explicites sans inventer de transaction multi-fonctions.

Le scénario SLS-031 reproduit le défaut sur l’image `9110295` : deux publications
réussies, service sans valeurs communes, héritage copié dans les fonctions.
Les deux archives du second essai sont purgées par l’API publique. Le premier
essai utilisait un helper dont la liste de préfixes refusait la nouvelle campagne ;
ses deux archives ont ensuite été purgées par l’API, sans élargir le helper.
Avant correction, décision supplémentaire : un drapeau `replace_secrets` propre
au service rend son remplacement atomique et permet le renouvellement de 128
noms sans cumuler anciens retraits et nouveaux noms dans la même limite de 128.
Le comportement partiel de l’édition existante est conservé par défaut.

La revue SLS-031 relève deux validations complémentaires : les mutations de
gestion doivent vérifier la configuration effective dans leur transaction ;
la CLI doit borner la fusion connue avant de modifier le service. Le premier
défaut est reproduit : dix groupes passent puis une variable commune entrant
en collision avec un secret local est acceptée à 200 au lieu de 422. La campagne
purge ensuite ses deux fonctions. Décision : partager la fusion existante du
déploiement entre gestion et moteur, et contrôler côté CLI les valeurs connues.

### SLS-031 — Correction et qualification finale

Le contrôle partage désormais la fusion entre gestion, validation et moteur.
La configuration de service vérifie toutes ses fonctions dans la transaction ;
les créations/modifications vérifient aussi leur résultat avant et après une
préparation de stockage. Le remplacement explicite des secrets conserve le
mode d’édition partiel existant par défaut.

Le contrôle de taille de la CLI a été complété après une reproduction Unicode :
la requête UTF-8 tenait dans la limite mais son JSON échappé de bootstrap la
dépassait. L’essai avait modifié le service et créé un brouillon avant refus.
La preuve avant correction conserve cette observation et sa purge. Les deux
représentations sont maintenant bornées avant mutation.

Treize groupes ciblés passent : provider au service, surcharges, rotation
pendant un appel admis, droits, retraits, échec partiel, reprise d’un ancien
déploiement aplati, limites et vrai redémarrage. Les régressions et clients
Docker portent la série finale à 191 groupes sur douze campagnes, zéro échec
et zéro skip. Les 165 sources sont recoupées entre commandes ; les images
contiennent les 25 fichiers Python/migrations et les cinq modules CLI attendus.
Les deux fonctions ciblées et onze répertoires d’artefacts sont purgés,
les réservations sont à zéro et aucun conteneur de l’installation ne reste.

Les campagnes intermédiaires restent distinctes de cette série finale : un
oracle utilisait LOCAL_ONLY alors que le handler lit LOCAL_LABEL ; le lanceur
local omettait d’abord le marqueur synthétique du refus public puis interprétait
à tort les perturbations volontaires du rapport stockage comme des erreurs UI.
Ces défauts de banc ont été corrigés ; la série finale a été intégralement
rejouée sur l’état figé, avec des noms de fonctions décrivant leur usage.

La revue en lecture seule a confirmé les corrections de fusion, taille Unicode
et ordre d’application, sans nouveau défaut produit. Les 21 captures sont
inspectées, dont sept images du manuel strictement identiques à celles déjà
relues. Le guide rendu comporte treize chapitres et 39 paragraphes conformes
à sa source ; les textes communs sont lisibles sur ordinateur et mobile.
La preuve complète est `evidence/service-configuration-dev-2026-11-08.json`.

Les trois notes de cellule ont été actualisées et proposées dans leurs voisins
`.?`, après comparaison aux notes actives et vérification de propositions vides
de contenu. Leurs empreintes sont recoupées ; leur adoption reste du ressort
du registre. Aucune variable, secret, route ni migration n’a été ajouté.
L’interface d’adresses multi-domaines reste l’unité SLS-066.

### SLS-031 — Issue de la vérification et banc résiduel

Le vérificateur en lecture seule confirme les 191 groupes, leur ordre sans
chevauchement, fraîcheur, empreintes, images et nettoyages. Les états Git avant
et après sa mission sont identiques. Il relève une lacune de couverture : le
nouvel état `service_configuration = unknown` n’a pas été provoqué par une vraie
perte de réponse de mutation commune. SLS-031 reste donc ouverte ; les 191
groupes constituent un checkpoint et ne prouvent pas ce parcours.

Le contrat décrit le banc résiduel avant son implémentation : observation native
du contrôle réel, puis SIGKILL avant traitement ou après commit mais avant
émission de réponse, garde indépendante et reprise du conteneur original.
La CLI doit rapporter l’issue inconnue, arrêter les publications et ne rien
rejouer automatiquement. Une relance explicite doit fonctionner ensuite.
Les outils strace, ss, nsenter, nft, tc et ip existent dans le SPARK ; ses
capacités natives ont été relevées. Ce relevé n’est pas la preuve du banc.

## 2026-11-08 — Ergonomie, édition et exploitation de la console

Le responsable demande recherche, favoris, suppression/renommage en masse,
édition du code et du handler sur place, client de requêtes par fonction,
logging et monitoring. Ces besoins entrent dans le périmètre de la console
SLS-060 et sont découpés dans SLS-067 à SLS-073, tous non commencés.
Le contrat est persisté dans CONSOLE_USABILITY.md avant implémentation.

La console possède déjà les journaux d’invocation, les relevés d’instances et
la publication ZIP. Les extensions ajoutent un catalogue opérationnel, des
préférences liées au compte, des lots suivis, des brouillons de code validés
avant publication, un vrai client de passerelle et des historiques de mesures.
Le chemin utilisateur relie recherche, édition, publication, appel, journaux
et diagnostic. Le design system local décrit ces parcours futurs séparément
des écrans actuellement déployés.

Décisions : favoris persistés par identité SSO ; renommage conservant les UUID
avec export de correspondances pour l’adaptateur ; suppression archivant les
fonctions selon le contrat existant ; édition créant des révisions immuables ;
appels avec un vrai jeton Read et contexte serveur/navigateur explicite ;
journaux et métriques avec rétention et coût bornés. Les journaux existants
ne sont pas présentés comme un monitoring historique déjà livré.

Le manuel affiché évoluera avec chaque livraison effective. Cette modification
documentaire ne change ni code, ni service, ni preuve E2E existante. L’ordre
de réalisation conserve les preuves de fiabilité et les URL actuellement
ouvertes avant les nouvelles tranches d’ergonomie. Chaque tranche exige ses
parcours E2E réels, refus, reprises et inspection visuelle.

## 2026-11-08 — Réponse perdue de configuration commune et clôture SLS-031

Le checkpoint de 191 groupes laissait l’état CLI `unknown` sans preuve de vraie
perte de réponse commune. Le banc retenu est implémenté ici dans
`e2e/service-transport.mjs` et `e2e/service-transport-observer.py`, contre le
contrôle inchangé. Son contrat natif est persisté avant code ; le comptage des
connexions CLI complète les audits, car un rejeu refusé 409 n’ajouterait pas
d’audit. La revue a aussi renforcé la preuve de disparition du pilote, les
bornes de restauration, la santé Docker et le StartedAt de la référence.

Les essais préparatoires ont échoué explicitement : session SSO expirée,
sélecteur retenant aussi docker-init, attente incorrecte d’un code SSH 137 lors
d’un SIGKILL distant et arrêt non idempotent d’un timer déjà collecté. La session
est renouvelée par le vrai SSO ; le ciblage vérifie l’exécutable Python ; la
disparition native est confirmée par la garde indépendamment du code SSH ; les
résultats de garde sont écrits atomiquement et son arrêt vérifié inactif. Les
objets API vides de l’essai interrompu pendant collecte ont été supprimés après
confirmation de restauration. Aucun de ces essais n’est compté comme réussi.

La campagne finale passe cinq groupes en série. Le pilote est réellement perdu
par SIGKILL pendant suspension ; la garde indépendante confirme sa disparition
et l’état sain. Le contrôle est ensuite arrêté à la sortie de recvfrom avant
traitement : aucune mutation. Puis à l’entrée de sendto après commit : une
mutation durable et son audit. Les deux vrais ingress renvoient 502 ; la CLI
rend unknown et results vide. Strace ne voit que trois tentatives HTTPS par
commande, soit les deux lectures et le seul PUT, sans publication ni rejeu.
Les deux relances explicites publient et invoquent le handler original dans
Docker. Les treize groupes de configuration passent ensuite sur la même image.

Le complément conserve 167 empreintes avant/après, image et 25 sources embarquées,
quatre fonctions purgées, treize artefacts absents, réservations et allocation
à zéro et trois gardes inactives. La revue ne trouve aucun défaut bloquant.
Les sources produit, buildfiles, fixtures, dépendances et manuel sont identiques
à la preuve de 191 groupes ; les différences sont le contrat UX futur, le
préfixe supplémentaire de l’inspecteur et les deux nouveaux clients E2E.
Les campagnes et leurs index restent distincts, sans prétendre à une nouvelle
suite unique de 209 groupes. SLS-031 est clôturée ; les autres unités restent
suivies indépendamment. Aucun nouveau parcours UI n’est livré par ce banc.

Les trois notes SPARK sont reproposées après comparaison des empreintes des
propositions précédentes et des notes actives. Leur adoption reste en attente ;
aucune variable, aucun secret ni route n’est proposé ou modifié. La configuration
reste dans les deux fichiers de cellule. Aucun remote Git n’est configuré.
