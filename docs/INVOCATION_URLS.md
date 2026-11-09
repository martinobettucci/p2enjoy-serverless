# Adresses d’appel des fonctions

La prochaine qualification de source suit le
[contrat de refus réel de lecture](INVOCATION_SOURCE_PERMISSIONS.md) : permissions
du fichier officiel seulement, garde indépendante avant chmod et trois preuves
de restitution avant les parcours API/UI. Les trois gardes passent sur le SPARK.
Le [complément API](evidence/invocation-source-api-dev-2026-11-09.json) passe
quatre groupes réels : source_forbidden, refus sans diagnostic, appels Docker
pendant la faute et restitution du catalogue. Son rendu UI reste à éprouver.

Contrat SLS-066. Catalogue, console, CLI et montage readonly sont déployés sur
le SPARK DEV. Le [checkpoint](evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
passe 88 groupes réels sur le seul domaine alors affecté. La
[régression complète](evidence/invocation-urls-regressions-dev-2026-11-08.json)
passe ensuite 35 campagnes et 467 groupes, sans échec ni test ignoré. L’unité
reste en qualification. Le [complément de cinq cycles](evidence/invocation-route-cycles-dev-2026-11-09.json)
qualifie les changements des deux routes autorisées et le vide de l’API locale.
Le [parcours public vide](evidence/invocation-empty-ui-dev-2026-11-09.json)
passe ensuite trois groupes ; les pages suivantes UI/CLI et les autres preuves
résiduelles ci-dessous restent ouvertes.

## Source officielle et limites

Lire exclusivement la projection `/etc/spark/routes` de la cellule, par le
montage de répertoire `/etc/spark:/spark:ro` dans le contrôle. La configuration
continue d’entrer par les deux env_file officiels. Aucun daemon supplémentaire,
registre copié, fichier de remplacement, modification de FORGE ou lecture de
`routes.?` pour calculer une adresse. Le répertoire permet de rouvrir le fichier
à chaque consultation, y compris après un changement d’inode.

Constat du 8 novembre : une ligne `serverless.lelabs.tech 18090 tls`, fichier
0640 root:1001 lisible par spark-docker. Un conteneur rootless de l’image
courante lit les mêmes octets, refuse une ouverture en écriture et disparaît
après le probe. Le modèle infra écrit cependant d’abord root:root 0600 puis
réouvre au groupe dans certains chemins ; une erreur de permission reste donc
un état normal de source indisponible, jamais un registre vide.

Le fichier porte des lignes domaine/port/tls|clair, avec tls par défaut lorsqu’il
est omis. Il représente les routes enregistrées et enabled, sans applied_at ni
confirmation Caddy/certificat. La projection peut devancer l’application ou
rester ancienne après un PATCH/une erreur. L’atomicité de son remplacement n’est
pas garantie par le code infra. Les URL sont des adresses issues du relevé,
leur disponibilité et leur certificat restent non vérifiés par ce catalogue.

Lecture bornée à 64 Kio et 512 lignes de route, fichier ordinaire sans lien,
UTF-8 strict. Rouvrir, lire puis recouper identité/taille/mtime du descripteur et du nom
courant sans suivre un lien ; un changement
observé ou une ligne invalide rend la lecture indisponible, sans ancien résultat
réutilisé. Un en-tête tronqué sans ligne ne vaut pas registre vide : le marqueur
officiel d’absence est requis dans ce cas. Une coupure entre deux lignes valides
reste indétectable sans génération transactionnelle du producteur ; le relevé
ne revendique pas cette garantie. Les diagnostics publics sont fixes et sans
contenu brut, chemin hôte ou donnée de configuration.

Normaliser les noms DNS ASCII en minuscules suivant la grammaire infra, valider
port 1..65535 et mode. Doublons identiques dédupliqués ; déclarations contradictoires
refusées. Seuls les domaines visant le port réel de réception ASGI sont retenus.
Le Compose qualifié utilise le réseau hôte : ce port est celui du SPARK, sans
nouveau réglage ni dépendance à Host/X-Forwarded-Host. Les domaines génériques
sont recensés séparément, sans inventer un hôte concret ni une URL copiable.

## API et calcul commun

Ajouter `GET /api/functions/{UUID}/invocation-urls?limit=5&offset=0` : session
administrateur ou Read sur cette fonction. Create/Update/Delete seuls, portée
étrangère et anonymat restent refusés avant de révéler l’existence de l’objet.
Fonction ou parent supprimé : 404 après autorisation ; un jeton ne pouvant
identifier un service autorisé reçoit le refus de portée habituel.
Limite 1..20 domaines par page, offset 0..10000 ; tri par domaine.

Une seule lecture SQL joint fonction active, service actif et révision active
non supprimée. Les chemins et méthodes viennent de cette révision, avec son
UUID dans le résultat. Pas de valeurs de variables, secrets, jetons, code,
chemins hôte ou résultat de handler. Les horaires distinguent lecture du
registre et révision observée ; une consultation n’exécute pas de fonction.

Le résultat contient function_id, service_id, revision_id, function_state
(draft/published), console_url canonique, source (state, observed_at, mtime,
sha256, error_code éventuel), items de domaines avec origine/transport et leurs
URL/méthodes, total/limit/offset et domaines génériques non concrétisés.
Une source absente/interdite/invalide/changeante donne source indisponible et
aucune URL ; ce diagnostic ne dégrade pas le moteur d’invocation ni sa santé.
Un fichier valide sans domaine applicable donne un résultat vide explicite.
Un brouillon ne reçoit aucune URL à appeler.

Pour un événement exact, construire `/invoke/{UUID}/{chemin}`. Pour un événement
implicite, proposer `/invoke/{UUID}` avec ses méthodes ; le nom dérivé stocké
n’est pas nécessaire à ce point stable. Le routage actuel ne supporte que les
chemins exacts : aucun gabarit paramétré inexistant n’est annoncé. Préserver la
casse et les méthodes ; une URL sans tag suit la révision active actuelle.
[SLS-074](FUNCTION_VERSIONS.md) ajoutera les versions par hash et la promotion ;
aucune URL versionnée n’est émise avant son implémentation.

La source et la construction sont communes à la console et à l’adaptateur.
La CLI consulte ce catalogue après publication, avec le même jeton Read, et
parcourt les pages de cinq domaines tant que source et révision restent identiques. Une lecture
indisponible, un changement de catalogue/révision ou un refus après publication
rend seulement l’information d’adresses indisponible avec diagnostic : une
publication déjà réussie reste published, sans nouveau ZIP ni mutation rejouée.
Les exemples utilisent un emplacement X-Serverless-Token, jamais une valeur réelle.
L’exemple curl préfère GET lorsqu’il est autorisé ; sinon il reprend une méthode
déclarée. Le classement alphabétique ne choisit pas DELETE lorsqu’un GET existe.

## Console et domaine canonique

Facette partageable Adresses d’appel dans la fonction, et lien explicite depuis
chaque fonction de la fiche service. Domaines paginés par cinq, méthodes et URL
complètes avec retour à la ligne, copie d’adresse et d’exemple curl. Un échec de
presse-papiers conserve le texte sélectionnable. Actualiser/pagination retirent
les anciens succès ; erreur, session absente ou source indisponible retirent les
adresses obsolètes et empêchent leur copie. Recalage d’une page devenue vide,
focus sur un contrôle visible, clavier et mobile 390 px.

Afficher HTTPS déclaré ou HTTP déclaré et disponibilité non vérifiée, sans
badge de certificat prêt. Aucun domaine applicable, brouillon et erreur de
lecture ont des messages distincts avec action utile. Aucun stockage navigateur
supplémentaire ni secret dans les adresses, exemples, URL ou messages.

Le SSO et la console conservent SERVERLESS_PUBLIC_URL. Une entrée HTML ou
/auth/login sur un autre hôte rejoint cette origine configurée, sans fabriquer
une cible depuis un en-tête. La redirection des fiches conserve les UUID valides
de suivi deployment/operation ; les paramètres non reconnus sont écartés.
L’entrée /auth/login rejoint uniquement ce chemin canonique. API de jetons et /invoke restent utilisables sur
les domaines d’appel ; les règles de CSRF, origine/IP et Read ne sont pas modifiées.

## Qualification réelle et autorité

Vérifier API, scopes/CRUD, brouillon, publication A/B et rollback, chemins et
méthodes, nom modifié sans perte du point implicite, pagination, Host falsifié,
source réellement indisponible, source changée, CLI et absence de divulgation.
Depuis l’accueil, naviguer namespace/service/fonction, copier puis invoquer en
HTTPS le véritable handler Docker ; clavier, refus de copie, données longues,
mobile, erreurs, captures observées et manuel compilé avec sa source.

Les preuves multi-domaines, retrait et absence exigent des changements normaux
des vraies routes. Leur source n’est jamais éditée, remplacée ou simulée. Le
contrat local interdit les opérations de FORGE à l’agent. Le responsable a
explicitement autorisé le 8 novembre 2026 la gestion des routes du seul
infra-serverless depuis sa console normale, selon le périmètre inscrit dans
CLAUDE_PROJECT. Cette autorisation ne constitue pas une route appliquée ni une
preuve TLS. Les opérations suivent la qualification courante SLS-067 en série.

Plan borné proposé pour infra-serverless (10.77.0.24) : ajouter
functions.lelabs.tech vers 18090 en TLS, après vérification de disponibilité du
nom dans la console ; qualifier les deux domaines et l’entrée SSO canonique.
Retargeter temporairement seulement ces deux routes vers 18091 pour éprouver
l’exclusion de l’autre port et l’absence de domaine applicable, puis rétablir
18090. Retirer et rétablir l’alias pour qualifier son retrait réel. Le mode clair
et les quatre domaines supplémentaires ne font pas partie de l’autorisation reçue.
Aucun autre SPARK ni route
n’est modifié, aucun fichier/configuration système de FORGE n’est administré.

Avant perturbation : installation au repos, identité des routes et du SPARK,
état initial sauvegardé et garde indépendante de restauration vérifiée. Conflit
avec une route d’un autre SPARK : arrêt sans reprise de sa propriété. Conserver
les sessions/tokens de contrôle dans les canaux privés autorisés, sans mot de
passe en fichier, argument, environnement ou rapport. Rétablir la route canonique
avant de terminer ; ne pas confondre panne DNS/TLS avec retrait du registre.

Un appel de catalogue déjà reçu peut être retenu nativement avant sa lecture
pendant le changement réel de routes, puis rendu sur sa connexion HTTPS admise.
Ce chemin permet d’observer l’état vide dans l’UI sans registre, DNS ni réponse
substitués et passe les trois groupes du complément public ci-dessous.
Pour les preuves résiduelles, une impossibilité ne devient pas un succès
ni une dispense de preuve. Les limites d’accès et les preuves manquantes restent
explicites dans SLS-066.

La proposition courante à deux domaines suffit au multi-domaine et à la
pagination API avec limit=1, pas à une seconde page console/CLI. Ces deux
preuves demandent six domaines réels : quatre alias supplémentaires devront
être inclus explicitement dans le périmètre autorisé avant création. Elles
restent ouvertes tant que ces routes ne sont pas disponibles. La CLI consulte
par cinq comme la console, plutôt que d’exiger vingt et un domaines pour
éprouver son changement de page.

## Console normale et mise en service de l’alias autorisé

Le catalogue SLS-067 étant qualifié, reprendre SLS-066 par étapes sérialisées.
La console normale déjà ouverte sur le poste expose son relais local ; il
constitue le même chemin d’administration que ses formulaires. Aucun accès
direct au registre, à Caddy ou au système de FORGE n’est utilisé. Le navigateur
intégré de la session étant indisponible, les opérations passent par cette API
de console existante, sans démarrer ni reconfigurer son serveur.

Première étape, sans perturbation de la route canonique : vérifier le serveur
sélectionné, l’identité infra-serverless / 10.77.0.24, sa protection, les routes
exactes et génériques déjà affectées, puis l’aperçu DNS du seul alias autorisé.
Le relevé du 8 novembre trouve functions.lelabs.tech absent, la zone lelabs.tech
active et l’aperçu d’un A functions vers 51.158.54.202 à créer, TTL 300. Le DNS
est une dépendance de l’alias HTTPS autorisé. Poser uniquement cet enregistrement
par la fonction DNS normale de la console ; ne remplacer aucune valeur existante
différente, ne toucher à aucun autre nom ou type. Relever l’effet réel et attendre
la résolution native, sans forcer Host, DNS ou validation de certificat.

Déclarer ensuite functions.lelabs.tech vers 18090 TLS pour ce seul SPARK.
Une réponse de mutation perdue ne déclenche aucun renvoi automatique : relire
l’état durable et diagnostiquer. Un nom possédé ailleurs interrompt l’opération.
La projection officielle est rafraîchie par le chemin suggestions qu’utilise
normalement la facette Routes ; seule sa métadonnée cell_read est conservée,
jamais son corps contenant d’autres propositions ou secrets. Recouper ensuite
les vraies lignes de /etc/spark/routes et leur lisibilité depuis le contrôle.
Attendre un vrai HTTPS public vérifié et une réponse de l’application sur les
deux domaines. Une route déclarée ne vaut pas certificat prêt.

Conserver les résultats et empreintes dans un reçu d’exploitation distinct.
Rejouer ensuite les huit groupes API/CLI existants : leur boucle invoque déjà
chaque adresse émise et vérifie les chemins, révisions et méthodes. Les six
groupes navigateur repartent de l’accueil, créent et publient leur fonction,
copient et invoquent le code Docker sur le catalogue réellement à deux domaines.
Leur preuve reste distincte du catalogue SLS-067 figé, avec rapports frais,
captures observées et collecte native des seules ressources créées.

Cette première étape n’exerce aucun retrait ni détour vers 18091. Leur
complément ultérieur suit [le contrat des cinq cycles](INVOCATION_ROUTE_CYCLES.md)
et sa garde indépendante éprouvée. L’autorisation ne couvre pas de nouvelles
variables de cellule, d’adoption de notes ou d’administration d’autres SPARKs.

La console peut actualiser applied_at sur les routes lors de sa réapplication
normale. Le pilote compare les propriétés matérielles (identité, propriétaire,
domaine, IP, port, TLS, activation), en conservant cette date comme observation.
Après déclaration effective et arrêt d’une vérification, une commande distincte
verify-installed-alias reprend uniquement les lectures et le HTTPS. Elle exige
le reçu de déclaration, recoupe les mêmes identifiants et ne renvoie aucune
mutation. Le reçu initial reste incomplet ; son diagnostic et sa reprise sont
conservés séparément. Un changement matériel demeure un échec.

## Qualification du couple de domaines TLS

Le [complément réel](evidence/invocation-domains-dev-2026-11-08.json) passe huit
groupes API/CLI puis six groupes navigateur sur serverless.lelabs.tech et
functions.lelabs.tech. Les 198 sources et les mêmes images contrôle/CLI sont
recoupées avant/après les deux campagnes. Les appels parcourent effectivement
toutes les adresses émises, avec handlers Docker, chemins/méthodes, révisions,
renommage et rollback. Les sept nouvelles captures sont inspectées : deux
domaines lisibles, copies, refus natif du presse-papiers, réseau, mobile et guide.
Les quatre fonctions sont purgées dans deux namespaces ; reçus, ressources
physiques et secrets de fonction sont recoupés. Les services gardent leur
identité et démarrage, et les deux fichiers de configuration sont inchangés.

Le DNS A exact et les deux réponses HTTPS vérifiées sont conservés séparément
des tests métier. Le contrôle lit les deux lignes du vrai fichier officiel
par son montage readonly. Le premier essai de mise en service reste incomplet :
la déclaration réussit, puis l’assertion de date d’application s’arrête. Une
reprise strictement en lecture seule recoupe son SHA et ses identités et confirme
les vrais HTTPS, sans second POST. INC-004 est corrigée dans ce seul client ;
la date reste enregistrée sans servir de propriété matérielle de configuration.

Le premier départ API sur session expirée reste également distinct : zéro groupe,
avant création de ressources. Une nouvelle connexion SSO réelle précède le
replay positif. Aucun de ces essais n’est réécrit en réussite.

Ce premier complément à deux domaines ne prouve pas le retrait ni les détours ;
ils sont qualifiés par les cinq cycles ultérieurs, avec le vide de l’API locale.
Le parcours UI public vide est qualifié par le complément ultérieur. Restent
la source indisponible et les pages suivantes sur six domaines. L’entrée
HTML/SSO depuis l’alias est qualifiée dans le complément public ci-dessous.
La preuve native du Host/redirection reste
celle de la boucle locale. Les scénarios résiduels et leur garde maintiennent
SLS-066 ouverte. Le mode clair n’a pas été activé.

## Garde de restauration et cycles autorisés

Étape suivante, après le checkpoint à deux domaines : un pilote de console
borné aux deux noms et au seul SPARK, avec une garde locale indépendante de
son processus. Chaque requête de relais conserve explicitement le serveur
spark-experiment ; une autre sélection d’onglet ne change jamais sa cible.
Vérifier l’entrée serveur par nom/IP/port et le SPARK par identifiant/IP, sans
exiger que servers.current reste sélectionné pendant une restauration.

La garde mémorise identité et naissance du pilote, route canonique par son
identifiant stable, alias par ses identifiants successifs autorisés, propriétaire,
port 18090, TLS et activation. applied_at reste une observation. Répertoire
privé, reçu atomique, verrou local : une seule action du pilote ou de la garde
peut modifier une route à la fois. La garde est démarrée et reconnue prête
avant toute perturbation ; perte du pilote ou échéance bornée demande la
restauration. Ne désarmer qu’après lecture des propriétés matérielles, projection
officielle rafraîchie et deux réponses HTTPS vérifiées, puis fin confirmée de
la garde. Aucun secret ou contenu de suggestions ne rejoint ses reçus.

Restaurer seulement ce qui appartient toujours au SPARK et aux identités
possédées. Ne supprimer jamais la canonique ; ne créer que l’alias exact s’il
est absent et libre, après contrôle des génériques. Ne pas modifier un autre
propriétaire ni lever une protection 423. Une réponse de mutation perdue ou
refusée exige une relecture : le PATCH peut avoir commis avant son 502, alors
que DELETE confirme Caddy avant suppression du registre. Aucun rejeu aveugle.
Une restauration non confirmée reste en échec explicite ; la garde dépend
encore du poste, de la console normale et de son tunnel, et ne prétend pas
survivre à leur disparition. Le verrou ne protège que les propres actions
du pilote : le chemin normal n’offre pas de comparaison atomique If-Match
contre une intervention concurrente d’une autre console.

Preuves sérialisées : armer/restaurer sans perturbation ; détourner seulement
l’alias vers 18091, constater son exclusion du vrai catalogue puis tuer le
pilote après fin confirmée de la mutation et vérifier la restauration indépendante ;
retirer/rétablir l’alias avec nouvel identifiant et même comportement d’appel ;
enfin détourner les deux routes avec garde déjà éprouvée, constater le vrai
catalogue vide sur l’entrée locale réelle, puis restaurer et invoquer Docker.
Les scénarios suivent leur fonction originale de qualification et ne nettoient
que ses objets. Rapports, identités, changements effectifs et nettoyages sont
conservés par scénario ; aucune réussite n’est déduite d’un seul fichier prêt.

L’état vide dans la console publique possède sa preuve distincte ci-dessous.
Le pilote de pause retient le vrai GET admis après sa réception et avant lecture
du fichier officiel, selon le précédent NativeObserver, puis libère la requête,
sans commande cut, destruction du contrôle, modification de mémoire, registre
ou résultat système. La survie de sa connexion pendant la réapplication normale
de Caddy est éprouvée par les trois groupes UI. Le mode catalogue-before historique n’est
pas réutilisé tel quel : il détruit le contrôle et sa garde ne rétablit pas
les routes. Les perturbations sont qualifiées par les cinq cycles du 9 novembre ;
sa pause et le parcours public sont qualifiés dans les compléments ci-dessous.

Le [premier checkpoint de garde](evidence/invocation-route-guard-checkpoint-dev-2026-11-08.json)
passe la restauration explicite puis le SIGKILL réel du pilote sans demande
explicite de restauration. Les deux scénarios gardent les ports inchangés,
confirment deux HTTPS et la fin de la garde. Le scope d’échéance déclenche
deadline mais échoue sur la dernière vérification HTTPS de l’alias ; il reste
incomplet. Le diagnostic suivant observe une ancienne réponse DNS native
négative, avec les deux autoritaires corrects. Aucun détour/retrait n’a commencé.
La [reprise positive](evidence/invocation-route-guard-dev-2026-11-08.json)
rejoue ensuite les trois scopes sur la résolution native réellement rétablie :
trois groupes réussis, deux HTTPS et fin de garde confirmés, avec 201 sources
et les mêmes images. L’expiration du cache ancien est observée ; aucun
enregistrement correct n’est réécrit, aucune adresse forcée et aucun TLS contourné.
Ce résultat qualifie les déclencheurs sans perturbation, avant les cycles réels.

## Barrière native de pause et libération

Pendant l’attente de résolution native de l’alias, préparer la barrière sans
changer de route. Le namespace original de preuve porte le préfixe
invocation-route-pause suivi de huit chiffres hexadécimaux, avec un service et
une fonction possédés. Les identifiants et l’inventaire exact sont vérifiés en
lecture native avant attachement ; aucune invocation, instance, publication
active ni opération de stockage n’est admise à cette frontière.

Extraire NativeObserver du pilote historique dans un module de preuve commun,
en conservant son corps et son ABI. Le script historique effectue des opérations
au chargement et ne constitue pas un module importable. Cette extraction évite
une seconde implémentation du traceur ; elle n’altère ni les modes historiques,
ni les commandes de destruction de leur propre preuve. Les quatre groupes de
transport des adresses et les cinq de configuration doivent être rejoués après
ce déplacement. L’API à huit groupes qui invoque aussi l’alias reste distincte
et attend la résolution native disponible.

Le nouveau pilote de pause s’exécute uniquement dans infra-serverless, sous
root, sur x86_64. Il identifie l’unique processus ASGI de l’image attendue, son
conteneur, sa naissance et son cgroup, et refuse un autre traceur présent.
PTRACE_SEIZE sans EXITKILL, observation des syscalls et lecture mémoire bornée
à la ligne publique du GET exact : aucun en-tête, cookie, jeton, corps, registre
ou résultat système n’est lu ou remplacé au-delà de ce périmètre. Identifier le
vrai socket TCP de réception 18090, retenir après recv complet et avant reprise
du traitement applicatif. Publier la barrière avec ses seules métadonnées.

Un protocole release détache et laisse terminer cette même requête, sans cut
ni destruction du contrôle. Un programme indépendant figé et son timer local
sur le SPARK sont armés avant attachement : perte du traceur ou échéance doit
confirmer sa fin puis reprendre seulement le processus ASGI d’origine, après
vérification de naissance/conteneur/image/cgroup. Il ne restaure aucune route
et ne remplace pas la garde de console. Le timer normal dispose de soixante-dix
secondes ; son scénario de perte du traceur utilise douze secondes. Le reçu,
les processus et la fin effective du timer sont recoupés avant nettoyage.

Premiers scénarios sans changement de route : vraie requête HTTPS canonique
retenue puis libérée avec catalogue à deux domaines ; perte SIGKILL du traceur
retenu puis reprise par son seul programme indépendant. Les lectures de santé
passent par le vrai contrôle et sa boucle locale, sans dépendre du DNS de
l’alias. Les rapports conservent les identités et l’issue de la requête admise,
sans qualifier le détournement Caddy encore absent. Aucune erreur ne peut être
convertie en résultat réseau ou applicatif fabriqué. Les parcours UI publics
et les changements de routes suivront après leurs prérequis qualifiés.

Le premier pilote implémenté retient et libère réellement le GET, mais son
premier essai reste en échec : disarm tente un second arrêt du timer transitoire
déjà collecté. Le diagnostic séparé reçoit HTTP 200 pour la même requête puis
reproduit le refus systemctl de cet arrêt. Un timer déjà déchargé constitue un
état terminal uniquement après confirmation native LoadState=not-found et
ActiveState=inactive ; aucun autre échec d’arrêt n’est toléré. Arrêter ou constater
cette absence avant de confirmer aussi la fin du service indépendant. Conserver
l’essai initial et le diagnostic séparément du replay après correction.

## Extraction du traceur commun vérifiée

La [preuve du déplacement](evidence/invocation-native-observer-dev-2026-11-08.json)
rejoue quatre groupes de transport des adresses puis cinq de configuration,
avec 201 sources et les mêmes images avant/après chaque phase. Le corps de
NativeObserver est strictement identique à celui du pilote antérieur ; seul
son emplacement et l’import changent. Les six fonctions des deux namespaces
sont purgées, les six gardes locales terminées et les observateurs absents.
Les 27 fichiers embarqués correspondent toujours au contrôle. Leurs pannes
recréent de vrais arrêts/reprises du contrôle, avec référence inchangée.

Cette extraction et ses neuf régressions sont vérifiées ; le nouveau protocole
de pause/libération est désormais implémenté et ses deux premiers scénarios
sont qualifiés dans le complément ci-dessous. Le premier
essai d’échéance reste conservé incomplet. L’invalidation locale n’avait pas
rétabli le DNS ; après expiration du cache en amont, la reprise positive des
trois déclencheurs est qualifiée ci-dessus. Aucun domaine ni réponse n’est forcé.

## Pause et reprise natives qualifiées

Le [replay du 9 novembre](evidence/invocation-request-pause-dev-2026-11-09.json)
passe deux groupes réels sur 205 sources inchangées : GET HTTPS canonique retenu
après recvfrom puis libéré, et SIGKILL du traceur au même point suivi de la reprise
avec confirmation de reprise par son programme indépendant. Dans les deux cas,
la même requête admise termine
à 200 avec la révision attendue et les deux domaines du registre réel.
Le scénario de perte confirme la survie du GET et l’exécution indépendante ;
il ne date pas la réponse par rapport au SIGCONT et ne prouve pas que le timer
soit la cause exclusive de sa libération.
Le correctif reconnaît le timer collecté par son état natif explicite ; les reçus
conservent ses codes d’arrêt, et le service indépendant est fini avant nettoyage.

Le premier essai échoué et le diagnostic HTTP 200 suivi du refus de désarmement
restent distincts et ne sont pas comptés dans ces deux succès. Les deux fonctions
des deux namespaces sont purgées ; les quatre helpers et quatre paires timer/service
sont absents ou inactifs. Le contrôle conserve PID, naissance, conteneur, image,
démarrage et cgroup, sans traceur ; référence et configuration officielle inchangées.
Aucun changement de route, DNS, variable, secret ou build dans ce complément.

Ces deux groupes fournissent la barrière préalable. La survie du GET navigateur
pendant réapplication Caddy est qualifiée séparément par les trois groupes UI
ci-dessous.
Échéance sans commande, EOF, commande partielle/trop longue, conflits/refus et
autres erreurs propres du pilote restent à éprouver. SLS-066 demeure ouverte.

## Parcours public du catalogue vide sous vraies routes

Le prochain client navigateur réutilise le préfixe possédé invocation-route-pause,
avec nonce dans les descriptions du namespace et du service request-pause-fixture,
et la fonction route-entry attendue par le pilote natif. Il crée ces objets et
publie le ZIP original depuis l’accueil, par les formulaires et la navigation
normale. Les lectures API servent au recoupement et au nettoyage ; elles ne
remplacent pas la création, la publication ou l’accès à la facette dans le parcours.

Trois groupes sérialisés :

1. Création/publication UI puis facette Adresses d’appel à deux domaines, avec
   capture desktop du catalogue initial.
2. Armer d’abord la garde des deux routes, puis la pause native. Le bouton
   Actualiser engage le vrai GET HTTPS. Après sa barrière recv complète,
   détourner les deux seules routes autorisées vers 18091 via la console normale
   et sa projection officielle. Libérer le même GET, exiger son vrai 200 avec
   source disponible, total zéro, révision identique. L’interface affiche l’aide
   Aucun domaine d’appel applicable, sans anciennes URL ni actions de copie ;
   inspecter les captures desktop et mobile, le focus et l’absence de débordement.
3. Confirmer la fin de la pause, restaurer les routes et attendre la fin de leur
   garde avec les deux HTTPS sains. Actualiser par l’UI, retrouver les deux
   domaines et exécuter Docker depuis une URL copiée, avec le jeton Read scoped.
   Recouper les captures de retour et la révision réelle du handler.

Sur toute erreur, libérer/confirmer d’abord le contrôle avant d’attendre la
restauration des routes, qui dépend de sa santé HTTPS. Une identité ou mutation
inconnue interdit le nettoyage ; conserver la fixture et les diagnostics.
Supprimer/purger seulement les UUID possédés après fin des deux gardes, puis
recouper nativement le stockage. Aucun fichier source de routes, résultat de
GET ou transport n’est substitué. L’application et ses images ne changent pas.
La survie effective de la connexion pendant la réapplication Caddy est une issue
de ce vrai test ; son résultat qualifié est décrit ci-dessous.

## Suite complète de preuve

Le scope `invocation-urls` de `e2e/execution-suite.py` compose l’union
sans doublon de 35 campagnes, soit 467 groupes : socle stockage/console 397,
adresses API 8 et UI 6, transport commun 5 puis configuration commune 13,
CLI Docker plan/package 24 et refus public 14. Cette union passe intégralement
sur DEV, avec zéro échec et zéro test ignoré ; elle ne remplace pas les essais
nécessitant des routes réelles.

L’ordre ajoute transport, configuration puis adresses avant les campagnes
ciblées de stockage et leurs restaurations historiques. Aucun service de
campagne ne reste actif à la frontière d’une faute. Une paire SSO réelle
fraîche précède le transport ajouté ; la paire avant décision de stockage est
conservée. Les identifiants transitent seulement sur stdin privée et restent
hors des fichiers/arguments/environnements/rapports.

Les prérequis non comptés sont la paire SSO initiale, le build historique,
la construction séquentielle des deux images CLI avec leurs cinq modules
recoupés, la paire avant transport, la paire avant décision de stockage et
le recoupement physique final. Les images CLI sont figées après leur build
et revérifiées avant/après leurs campagnes. L’image du contrôle et les
sources locales/distantes restent identiques sur toute la suite ; l’index
ajoute les fichiers de construction CLI, le manifeste de qualification et
le présent contrat. Une erreur arrête la suite et conserve le rapport incomplet.

Le recoupement détaillé final couvre dix namespaces et 32 fonctions : six/24
du stockage, un/trois de l’API des adresses, un/un de son UI, un/deux de la
configuration et un/deux du transport. Ces noms et inventaires sont vérifiés
contre les rapports frais, sans inclure les UUID historiques temporaires.
Les autres campagnes gardent leur propre reçu de nettoyage et le contrôle
global exige zéro fonction, instance, invocation active et réservation.
Les conteneurs clients adapter éphémères doivent également être absents.

Le replay réussi recoupe 186 sources avant/après chacune des 41 phases
(35 campagnes et six prérequis) et l’image du contrôle. Les deux images CLI
sont figées après leur build, puis recoupées sur les 35 campagnes.
Les 32 fonctions suivies sont purgées ; les deux restaurations historiques
restent distinctes. Les 26 fichiers Python/migrations embarqués correspondent
aux sources. Les 79 captures fraîches sont recoupées : 61 observations visuelles
et 18 réemplois par identité SHA256 avec une référence inspectée. Le manuel
servi correspond à ses 14 chapitres et 43 paragraphes. Les catalogues globaux
peuvent conserver des archives historiques étrangères à ces fonctions purgées.

Ces 35 campagnes ne qualifient pas elles-mêmes les cycles de routes et leur TLS,
éprouvés par les compléments ultérieurs. Restent les pages console/CLI sur six
domaines et la source officielle réellement perturbée. Le refus 401 après publication
CLI est qualifié dans le complément de révocation ci-dessous. La preuve native
du Host est acquise sur
la boucle locale ; elle ne qualifie pas un alias HTTPS public. Le build nominal
est qualifié ; sa branche d’expiration ou de perte SSH reste non éprouvée.
Ces limites maintiennent SLS-066 en cours.

## Preuve native du Host et des clients de panne

La vérification du véritable Host n’a pas besoin de fabriquer un domaine.
Un client opérateur du SPARK appelle l’API réelle sur la boucle locale 18090,
avec le jeton Read de sa fonction de campagne transmis sur stdin privée et
un Host étranger. Les adresses doivent toujours provenir du registre et du
port ASGI réel. Cet appel HTTP local vérifie cette frontière du contrôle ;
il ne prétend pas éprouver la route publique ou le TLS d’un alias absent.
Le même client vérifie les redirections HTML/login vers l’origine fixe,
les UUID de suivi conservés et l’absence de cookie de flow créé sur l’autre
hôte. Aucun registre, DNS, réponse ou fournisseur n’est remplacé.

Les clients des pannes du contrôle isolé portent le Host canonique lu dans
la configuration effective et refusent les redirections automatiques. Cela
garde la requête de panne SQLite dans le vrai conteneur de preuve ; suivre
une redirection jusqu’au SSO du contrôle principal ne constitue pas sa preuve.
L’échec réel avant correction est conservé séparément avec 51 groupes passés,
arrêt à la lecture de connexion attendue 503 ayant donné 200 après redirections,
et nettoyage confirmé. Seul le client est corrigé ; le produit n’est pas changé.

Le build CLI utilise une borne distante de 780 secondes avec arrêt forcé 15 secondes
plus tard, sous une enveloppe SSH de 900 secondes. Un échec/une expiration de
l’enveloppe ne prouve pas l’arrêt du mutateur distant ou du build Docker :
le rapport porte alors remote_state=unknown et interdit un nouveau build
automatique. Avant toute reprise, l’opérateur doit inspecter les processus
et opérations Docker réels, confirmer leur fin et archiver ce rapport avec
ce diagnostic. Un simple délai écoulé ou fichier d’état ne suffit pas. Le
parcours nominal confirme le retour de chaque build, ses images et contenus.

## Perte native du catalogue après publication CLI

Le [complément DEV](evidence/invocation-url-transport-dev-2026-11-08.json)
passe trois groupes propres avec `node e2e/invocation-url-transport.mjs`, puis
cinq groupes de transport historique et huit API/CLI, en série. Il réutilise
l’observateur natif et la garde indépendante du
transport de configuration, avec des modes bornés à un namespace
`invocation-url-transport-XXXXXXXX`, son service et l’UUID exact d’une seule
fonction brouillon précréée. L’installation ne doit porter aucune autre fonction
active, publication en préparation, invocation ou réservation. Aucun réglage
commun n’est déclaré dans le manifeste de ce scénario.

Retenir le vrai processus de contrôle sur la ligne publique exacte du GET
`/api/functions/{UUID}/invocation-urls?limit=5&offset=0`, soit après réception
avant traitement, soit juste avant émission de la réponse sur cette même
connexion. À chaque barrière, recouper par lecture native sous le propriétaire
SQLite le candidat publié unique, sa révision unique, la cible active, l’archive
sur disque et son hash ; aucune opération de stockage ne doit rester en attente.
L’observateur ne lit ni en-tête de jeton ni contenu de réponse.

Tuer le seul contrôle DEV identifié, puis le restaurer avec la garde native.
Le diagnostic réel peut être un HTTP 502 de l’ingress ou une erreur de transport :
ne pas le transformer en erreur réseau fabriquée. La CLI doit terminer à zéro,
`completed=true`, résultat `published` avec les mêmes UUID de candidat/révision
et `invocation_urls.state=unavailable`. Compter nativement ses six connexions
HTTPS : lectures service/liste/fonction, préparation, upload et catalogue ;
aucun rejeu de mutation ni tentative supplémentaire. L’audit et les lignes
durables doivent confirmer une seule publication. Après reprise, lire normalement
le catalogue avec un jeton Read distinct, invoquer le handler Docker par HTTPS,
puis supprimer et purger les seules ressources possédées.

Éprouver aussi la perte SIGKILL de l’observateur suspendu dans ce nouveau
périmètre, avec restauration indépendante et garde terminée. Le refus réel
après publication est une preuve distincte, qualifiée par le vrai 401 de
révocation ci-dessous ; une coupure du contrôle ne la remplace pas. Le checkpoint
de 467 groupes reste intact ;
ce complément conserve ses sources, image, rapports et nettoyages propres.
Ses 187 sources et les images contrôle/CLI sont identiques avant/après chaque
phase. Les deux coupures donnent réellement HTTP 502, avec publication réussie,
mêmes UUID et six connexions CLI sans rejeu. Les deux catalogues relus et
invocations Docker répondent normalement après reprise. Huit fonctions sont
purgées dans trois namespaces ; six gardes sont terminées et les 26 fichiers
embarqués sont recoupés. Le brut du relevé physique et son wrapper enrichi
ont des empreintes séparées. Aucun comportement produit n’est modifié.

Le nettoyage suit l’UUID possédé même après suppression logique : retrouver
l’archive et consulter une purge déjà engagée avant toute relance explicite,
avec un UUID d’opération conservé. Une création dont la réponse est perdue
se retrouve uniquement par le nom exact dans le service possédé. Aucun service
n’est déclaré nettoyé avant confirmation de la purge de sa fonction.

Le processus CLI et son traceur appartiennent à un groupe isolé. Une expiration
arrête ce groupe, et sa disparition doit être confirmée avant tout nettoyage.
La fin du traceur seul ne prouve pas celle de Python. Une fin non confirmée
produit un diagnostic d’état inconnu et interdit le nettoyage automatique.
Ces chemins d’échec restent distincts du résultat nominal et ne sont pas
déclarés éprouvés avant leurs scénarios réels.

## Révocation avant le GET facultatif

Le client de transport passe désormais quatre groupes réels dans le
[complément de révocation](evidence/invocation-url-refusal-dev-2026-11-08.json).
Un pilote local
`e2e/adapter-catalogue-barrier.py` démarre la véritable CLI en enfant tracé,
compte ses appels système connect vers le port 443 et la retient à l’entrée
du sixième. Les cinq connexions précédentes doivent avoir terminé ; la
publication unique est recoupée par le diagnostic natif du SPARK avant toute
révocation. Aucun syscall, argument, registre, mémoire ou résultat réseau
n’est modifié. Seule l’exécution du client est retenue ; le contrôle reste sain.

L’administrateur révoque alors le jeton utilisé par la CLI par la véritable
route de gestion et confirme son refus 401. Libérer le client : son GET reçoit
à son tour le vrai 401, mais son résultat conserve completed=true, published,
les UUID déjà commis et invocation_urls.state=unavailable. Toujours six
connexions, aucun renvoi de code. Un autre jeton Read relit le catalogue et
invoque le handler Docker. Purger les seules ressources possédées.

Le pilote lit seulement les sockaddr des connect et les sorties de son enfant,
jamais les buffers TLS. Sorties et métadonnées sont bornées. TRACE_SYSGOOD
identifie les arrêts syscall ; EXITKILL termine la CLI si son pilote disparaît,
selon la [référence Linux ptrace](https://man7.org/linux/man-pages/man2/ptrace.2.html).
Une attente de libération a un délai borné ; erreur/EOF entraîne l’arrêt et la
jonction de l’enfant, puis la disparition du groupe reste exigée par le parent
avant nettoyage. Cette nouvelle branche ne convertit pas une impossibilité de
traçage en succès. Ses pannes propres restent non éprouvées avant exécution.
Le refus 403 n’est pas revendiqué par une révocation, qui produit 401.

En cas d’échec avant une barrière, conserver aussi les événements de chaque
observateur et le résultat CLI déjà terminé, après contrôle d’absence de jeton.
Un résultat illisible ou contenant un identifiant sensible se résume par codes
fixes et empreintes, jamais par sa sortie brute. Une barrière non atteinte ne
prouve ni une publication échouée ni sa cause ; les audits natifs et le nettoyage
sont recoupés avant toute relance explicite.

Le replay réussi passe 17 groupes en série : quatre de transport, cinq de
transport historique et huit API/CLI. Les 188 sources et images sont identiques
avant/après chaque phase. Le vrai 401 conserve completed/published, les UUID,
l’archive unique et les six connexions CLI ; un autre Read invoque Docker.
Neuf fonctions sont purgées dans trois namespaces, six gardes terminées et
26 fichiers embarqués recoupés. Le brut physique est archivé avant enrichissement.

L’essai initial reste un échec distinct : watchdog passé, barrière suivante
manquée avant le nouveau scénario, cause non prouvée faute de diagnostic CLI
conservé dans cette version. Ses deux fonctions et deux gardes sont recoupées
nettoyées séparément. Le replay réussi ne prouve aucune correction du produit.
La conservation nominale des diagnostics est exécutée ; ses branches sensibles,
illisibles et les pannes propres du pilote restent non éprouvées. SLS-066 reste ouverte.


## Catalogue public vide — trois groupes réels passés

Le [complément du 9 novembre](evidence/invocation-empty-ui-dev-2026-11-09.json)
passe trois groupes sur 206 sources et les mêmes images avant/après. Namespace,
service et fonction sont créés depuis l’accueil par les formulaires ; le ZIP est
publié dans Code et révisions. Le GET du bouton Actualiser, réellement retenu
après recvfrom, survit à la réapplication normale des deux routes vers 18091.
La même réponse navigateur termine à 200 : source disponible, zéro domaine,
même révision. Desktop et mobile affichent l’aide utile sans anciennes URL
ni actions de copie. Les routes sont restaurées à 18090 TLS, l’UI retrouve deux
domaines et l’adresse copiée exécute réellement le handler Docker attendu.

La fonction est purgée dans son namespace, avec reçus/absences physiques recoupés.
Le helper natif, son timer/service et la garde de routes sont terminés ; contrôle
non tracé et sans redémarrage, référence/configuration officielles inchangées.
Les deux fichiers originaux de la garde conservent leurs nanosecondes exactes
en texte UTF-8 avec SHA. Les cinq captures ont leur fenêtre de fraîcheur ; leur
inspection et la revue finale sont consignées dans la preuve. Ce checkpoint
ne couvre ni la perte de confirmation propre au nouveau client, ni les fautes
de source, ni les pages UI/CLI sur six domaines. SLS-066 demeure ouverte.

## Entrée publique de l’alias et SSO réel

Le prochain complément n’administre aucune route. Il utilise le HTTPS réel de
functions.lelabs.tech et trois groupes sérialisés :

1. Requêtes publiques sans suivre les redirections : accueil et auth/login
   renvoient 303 vers les destinations fixes de serverless.lelabs.tech ; une
   entrée console ne conserve pas un paramètre de retour étranger. Aucun cookie
   de flow/session n’est posé sur l’alias. Son API session reste une API, à 200
   avec authenticated=false pour ce client anonyme, sans redirection HTML.
2. Navigateur desktop neuf, entrée par l’accueil de l’alias, page anonyme sur
   le domaine canonique puis clic Se connecter avec le SSO. Vrai fournisseur,
   code+PKCE S256 et redirect_uri canonique, saisie privée autorisée, retour au
   catalogue Fonctions. Vérifier cookie plateforme host-only sécurisé uniquement
   sur la canonique ; se déconnecter par la confirmation UI et constater la
   session fermée. Captures accueil, console connectée et retour déconnecté.
3. Même parcours intégral dans un nouveau contexte mobile 390×844, menu normal
   pour se déconnecter, trois nouvelles captures et absence de débordement.

Les identifiants sont reçus seulement par stdin privée et gardés en mémoire.
Ne journaliser ni URL d’autorisation complète, state, nonce, code, cookie,
jeton ni erreur Playwright pouvant reprendre la saisie. Le rapport conserve
uniquement les métadonnées publiques et empreintes des deux sessions propres
pour recouper leur révocation en lecture native. Aucun storageState fournisseur
n’est écrit ; le parcours nominal n’écrit aucun cookie. Si une fermeture de
session échoue, conserver uniquement son cookie plateforme canonique dans un
fichier privé 0600 de reprise, hors Git, puis signaler le nettoyage incomplet.
Ce fichier permet de fermer cette seule session par l’API normale, puis est
supprimé après confirmation ; aucun cookie fournisseur n’y entre.
Si un parcours s’arrête après connexion, fermer sa seule session par l’API normale
avec son cookie/CSRF en mémoire avant de fermer son contexte ; ne toucher à
aucune session antérieure. Ne créer aucune fonction ni donnée métier.
Les trois groupes passent dans le replay qualifié ci-dessous ; ses six captures
sont inspectées. Les deux essais arrêtés restent séparés de ce résultat.

Le premier essai passe les redirections anonymes et atteint la console après
SSO, puis s’arrête dans la vérification de déconnexion desktop. Il reste
incomplet, avec seulement la classe d’erreur conservée pour protéger les saisies.
Sa seule session est fermée et son flow absent, recoupés nativement ; aucun
changement de route. Le diagnostic suivant conserve des phases nommées et des
classes d’erreur prédéfinies, jamais les messages ou stacks Playwright. Ne
déduire aucune réussite de déconnexion UI de ce premier groupe arrêté.

Le diagnostic réel distinct identifie logout-body/response_body_unavailable,
après le HTTP 200 du POST normal ; sa session et son flow sont également fermés.
La page navigue après ce POST, ce qui rend sa réponse ancienne indisponible à
la lecture tardive du client. Conserver ces deux essais incomplets séparément.
Le correctif de preuve observe le même POST via CDP Network et son tampon de
réponses durable, activé uniquement après connexion et borné en mémoire. Lire
le corps réel après loadingFinished, sans interception, renvoi, remplacement,
pause de la page ou modification applicative. Exiger encore signed_out et
sso_signed_out vrais, session anonyme et cookies supprimés après la confirmation
UI. Ne collecter ni corps de login, headers d’authentification ni URL sensible.
Référence primaire : [protocole Chromium Network](https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/pdl/domains/Network.pdl),
configureDurableMessages et getResponseBody ; le protocole livré avec Playwright
déclare les mêmes commandes. Une commande absente ou un corps perdu fait échouer
le scénario ; aucune vérification n’est ignorée.


## Alias HTTPS et SSO — replay qualifié

Le [replay du 9 novembre](evidence/invocation-alias-entry-dev-2026-11-09.json)
passe trois groupes sur 207 sources et les mêmes images. Les vraies réponses
HTTPS de l’alias redirigent accueil/login/console vers les destinations canoniques
fixes, sans cookie sur l’alias. Son API session anonyme répond 200 sans redirection.
Les deux contextes neufs desktop/mobile entrent par l’alias, se connectent au vrai
fournisseur avec code/PKCE S256 et retour canonique, puis se déconnectent par l’UI.
Le même POST de déconnexion est lu par l’observation CDP durable : HTTP 200 et
signed_out/sso_signed_out vrais ; état anonyme et cookies supprimés ensuite.

Six JPEG frais sont personnellement inspectés, avec quatre empreintes distinctes :
les retours déconnectés sont visuellement identiques aux accueils correspondants.
Chaque fichier est néanmoins inspecté. La capture connectée mobile est une
pleine page de 1102 pixels, issue du viewport 390×844. Les JPEG n’incluent ni
barre d’adresse, ni saisie fournisseur, ni confirmation ouverte ; URL, PKCE,
cookies et résultat réel sont des assertions distinctes du client.

Le recoupement natif confirme les deux sessions et flows propres absents après
replay, plus les deux sessions/flows des essais arrêtés séparément. Aucun fichier
de reprise n’est créé dans ces parcours. Aucune fonction, route, DNS, variable,
secret ni image modifiée ; services et fichiers officiels restent inchangés.
La première phase non localisée et le diagnostic logout-body restent incomplets ;
aucun de leurs groupes n’est ajouté aux trois succès du replay. Les pannes
propres du client et du tampon CDP, la source et les six domaines restent ouverts.
