# Adresses d’appel des fonctions

Contrat SLS-066. Catalogue, console, CLI et montage readonly sont déployés sur
le SPARK DEV. Le [checkpoint](evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
passe 88 groupes réels sur le seul domaine actuellement affecté. La
[régression complète](evidence/invocation-urls-regressions-dev-2026-11-08.json)
passe ensuite 35 campagnes et 467 groupes, sans échec ni test ignoré. L’unité
reste en qualification : les changements de routes, pages suivantes et autres
preuves résiduelles ci-dessous ne sont pas couverts par ces campagnes.

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
18090. Retirer et rétablir l’alias pour qualifier son retrait réel. Un mode clair
de l’alias peut qualifier le schéma HTTP déclaré. Aucun autre SPARK ni route
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
substitués. Il reste à qualifier ; une impossibilité ne devient pas un succès
ni une dispense de preuve. Les limites d’accès et les preuves manquantes restent
explicites dans SLS-066.

La proposition courante à deux domaines suffit au multi-domaine et à la
pagination API avec limit=1, pas à une seconde page console/CLI. Ces deux
preuves demandent six domaines réels : quatre alias supplémentaires devront
être inclus explicitement dans le périmètre autorisé avant création. Elles
restent ouvertes tant que ces routes ne sont pas disponibles. La CLI consulte
par cinq comme la console, plutôt que d’exiger vingt et un domaines pour
éprouver son changement de page.

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

Restent les cycles de routes et leur TLS, les pages console/CLI sur six domaines
et la source officielle réellement perturbée. Le refus 401 après publication
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
