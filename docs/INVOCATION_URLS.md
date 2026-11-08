# Adresses d’appel des fonctions

Contrat SLS-066, décidé avant implémentation. Le calcul et les nouveaux écrans
restent à réaliser. La source et le montage sont vérifiés sur le SPARK DEV ;
ce relevé de capacité ne constitue pas une qualification fonctionnelle des URL.

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
contrat local actuel interdit les opérations de FORGE à l’agent : une action du
propriétaire ou une autorisation bornée de la console du seul SPARK est nécessaire.
La lecture locale et le développement indépendant continuent pendant cette étape.

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
