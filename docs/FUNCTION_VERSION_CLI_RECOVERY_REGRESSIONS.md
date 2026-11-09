# Régression008 du déploiement CLI et des publications interrompues

Suite de [SLS-074](BACKLOG.md#sls-074), après la
[première tranche](FUNCTION_VERSION_PUBLICATION_REGRESSIONS.md). Statut :
spécifiée avant code, pas encore qualifiée. Conserver les sept groupes
adapter-deploy et les quatre groupes publication-recovery, soit onze groupes.
Aucun changement produit prévu avant les résultats du banc.

## Déploiements et promotions CLI

Le vrai processus Python déploie onze fonctions, ce qui conserve la pagination,
les UUID, le service commun, ses variables/secrets et les résultats partiels.
La première publication n'a pas de cible : invoquer chaque hash puis promouvoir
avec le vrai promote CLI et Create, enfin invoquer par défaut. Un Create ne peut
republier une fonction dont le premier code existe. Read ne modifie pas le service.

Le deuxième vrai paquet modifie son marqueur empaqueté. Il prépare B sans déplacer
A ; invoquer A par défaut et B par hash pour chaque fonction, promouvoir B par
Update, puis l'invoquer par défaut. L'import défaillant de la première fonction
conserve sa cible ; les dix autres publications du même contenu dédupliquent B.
La mutation commune du service reste appliquée et les onze cibles B sont invoquées.
La reprise du brouillon après import refusé conserve son UUID ; son premier code
est appelé par hash, promu avec Create, puis appelé sans tag.

Soixante-huit invocations réussies prévues :22 premières,33 de transition,
11 après résultat partiel et2 de brouillon réparé. Le hash réservé effectivement
exécuté et l'UUID d'invocation sont comparés, ainsi que la présence du secret
commun ; cette fixture ne prétend pas vérifier sa valeur par empreinte.
Douze fonctions sont purgées complètement par les API à la fin.

## Plafonds et identité du code

Le premier groupe conserve neuf fonctions et64 candidats préparés : le65e est
refusé ; supprimer/purger une fonction libère huit places, une nouvelle préparation
réussit, puis tous les objets sont purgés. Le contrôle et l'agent réels font autorité.

Le second groupe publie vingt paquets originaux distincts, avec marqueur propre.
A est explicitement promue ; les autres uploads restent pilotes. Un doublon est
validé et accepté au plafond en conservant hash/révision et cible. Un21e hash
est refusé après validation, sans artefact ni réservation, et le candidat terminal
failed n'est pas confondu avec prepared. Le retrait d'un hash inactif exige If-Match ;
attendre son effacement, puis un nouveau hash est admis. Libérer encore deux
versions inactives pour les publications de reprise. Les dates/UUID des versions
restantes et les premiers marqueurs sont conservés.

La fixture originale qualification/artifacts/publication-recovery.cjs renvoie
marqueur, UUID, libellé et empreinte du secret de reprise. Le marqueur optionnel
d'import attend réellement8s, bornés, dans Node ; aucun faux serveur ou résultat
n'est substitué. Le vrai packager conserve un fichier aléatoire de256Kio pour
permettre un envoi partiel de192Kio physiquement non vide.

## Coupures physiques gardées

Le nouvel opérateur publication-recovery-operator.py est limité au SPARK
infra-serverless, au namespace publication-recovery-XXXXXXXX et aux UUID exacts
de fonction/candidat. Il lit SQLite sous son propriétaire. Les neuf fonctions
de capacité sont déjà purgées ; seule la fonction de reprise est vivante. Pas
d'instance, invocation, opération ni upload étranger pendant l'armement.

Avant envoi de l'upload, armer un timer indépendant et figer les programmes
KILL_CONTROL/RESTORE issus du banc de transport, adaptés au seul préfixe
serverless-restore-publication-upload-UUID. Conserver CID/image/démarrage,
PID/naissance/cgroup du contrôle, référence, configurations par SHA et verrou.
Le petit mutateur d'arrêt garde le FD hérité jusqu'à la fin confirmée du client
Docker et à son reçu137. Une issue inconnue interdit une reprise présentée comme
réussie. Les programmes figés et identités sont root privés ; aucune route,
variable, configuration ou administration de FORGE n'est modifiée.

Recevoir : le client annonce le ZIP entier, écrit192Kio et garde la connexion
ouverte. Exiger état receiving et octets réellement présents dans archive.zip.
Valider : envoyer le ZIP entier et exiger état validating avec le vrai validateur
vivant, image/installation et bind /code exactement liés au candidat. L'observateur
natif attache brièvement le vrai contrôle après ce constat, sans écrire de buffer,
registre ou résultat, pour constater la mort native SIGKILL et Docker137.
Une fenêtre manquée échoue et reste conservée ; aucun skip ni rejeu automatique.

Le troisième groupe interrompt la réception puis restitue explicitement le même
contrôle. Le quatrième interrompt la validation puis tue réellement le helper ;
la garde indépendante restitue le contrôle après cette perte. Les deux reçus
sont recoupés ; helper, timer et service doivent être terminés avant nettoyage
ou fenêtre suivante. Les requêtes et processus locaux sont joints avec bornes.
Une restitution incertaine conserve les objets et le diagnostic, sans purge aveugle.

Après chaque reprise : candidat failed/control_interrupted, aucun code publié,
configuration temporaire effacée, réservation et répertoire retirés, validateurs
et canaux absents ; cible A, configuration et premiers marqueurs inchangés.
Invoquer A puis publier explicitement un nouveau paquet, l'invoquer par hash
sans déplacer A. Le secret de reprise est comparé par empreinte. Huit appels
réussis sont prévus dans les quatre groupes, dont quatre pour le plafond et
deux par reprise. Dix fonctions sont purgées, y compris les neuf de capacité.

## Livraison et limites

Un pilote maintenu exécute les deux campagnes en série après SSO réel depuis
l'accueil ; le prérequis reste distinct des onze groupes. Anciennes preuves et
rapports sont conservés avant régénération, jamais les fichiers privés de cookie.
Sources/images et rapports frais sont liés ; collecte indépendante des22 purges,
76 invocations réussies, deux coupures/gardes et artefacts antérieurs conservés.
Les démarrages du contrôle changent comme attendu ; CID/image et référence restent
identiques. Les trois notes SPARK restent des propositions sans adoption implicite.

Les pertes, délais et erreurs propres du pilote/restaurateur ne sont pas déduits
du nominal. Expiration réelle, marge disque, autres clients API/stockage et
régression complète de console restent dans SLS-074. Aucun nouveau parcours visuel
ni changement du manuel n'est prévu ; toute correction produit découverte est
reproduite et spécifiée avant code. Cette tranche ne clôture pas le projet global.
