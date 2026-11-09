# Nettoyage de validation avec un upload déjà admis

Complément de [SLS-074](BACKLOG.md#sls-074), du
[contrat de publication](FUNCTION_VERSION_EXECUTION.md#publication-et-déduplication)
et de ses [preuves réelles](FUNCTION_VERSION_EXECUTION.md#preuves-réelles).
La garde du verrou est implémentée ; sa preuve physique reste à produire.

## Périmètre et quiescence

Le scénario utilise uniquement le SPARK DEV, une fonction créée par l’API dans
un namespace `version-validation-` suivi de huit hexadécimaux, ses candidats,
son stockage et les validateurs identifiés par installation et montage exact
/code. Il exige l’absence d’autre fonction active, d’instance, d’invocation,
d’opération et d’upload étranger. Le runtime de référence continue à tourner.
Aucun fichier interne du démon Docker n’est modifié.

Une version stable S est publiée puis explicitement promue et invoquée. Deux
uploads A/B de code seul sont ensuite admis : A importe réellement le module
original `storage-validation-delay.mjs`, B a sa réservation et son code extrait
et attend le verrou. Le helper observe leurs deux états validating, le marqueur
d’import de A et un seul conteneur monté sur le code de A avant d’armer la faute.
Les mutations métier de la plateforme passent toutes par HTTPS.

## Deux erreurs de nettoyage distinctes

1. Retirer temporairement les permissions du socket Docker monté dans le
   contrôle. Le refus errno13 est constaté depuis le vrai conteneur du contrôle.
   Le validateur de A expire puis ne peut retirer son conteneur : le candidat A
   échoue à422, diagnostic cleanup_failed et container_removed=false. Le socket
   concerne tout le contrôle ; la quiescence est donc impérative. L’opérateur
   root garde son accès pour observer et restituer.
2. Retirer les permissions du seul répertoire du canal /protocol de A,
   identifié par ses montages et son inode. Docker demeure accessible. Après
   expiration, A retire réellement son conteneur mais son rmtree du canal
   échoue avec EACCES ; A échoue à503 et son diagnostic de validation reste NULL.
   Ce cas ne constitue pas une preuve de container_removed=false : aucun résultat
   de validate n’est retourné. Le canal et les octets restent sous responsabilité.

B doit, dans les deux cas, recevoir503 avec le diagnostic précis « Un nettoyage
de déploiement doit être repris avant validation. », error_code=request_rejected
et validation_json=NULL. C’est le discriminant de la garde après verrou : un
simple défaut Docker aurait le diagnostic générique et deployment_failed.
Le constat isolé « aucun second conteneur » serait insuffisant sous refus global
du socket. Le journal réel des événements Docker, borné au cycle et à cette
installation, doit aussi ne montrer que le create de A ; il est particulièrement
discriminant dans le second cas, où Docker reste accessible.

Un troisième candidat C envoyé après l’échec doit être refusé avant admission :
état prepared et réservation nulle. Il est abandonné explicitement, sans rejeu
de son PUT. Les états et paquets de A/B, leurs réservations et canaux sont
recoupés par lecture native. La cible stable, son ETag et sa configuration
restent inchangés. Les octets de A ne sont pas libérés avant la réconciliation.

## Restitution et reprise

La permission initiale est enregistrée avec type, device/inode, UID/GID. Une
garde systemd indépendante est armée et vérifiée avant le retrait de permission.
La restitution normale du socket conserve cette identité. Pour le canal, le
scénario tue réellement le helper par SIGKILL ; la garde restitue l’inode attendu
et son reçu est relu dans le journal. La garde peut arrêter le helper après
vérification pidfd/naissance, puis restaurer ; elle ne vise aucun autre processus.
Les délais bornés et restaurations reprennent le précédent réel de SLS-065.

La maintenance normale, sans redémarrage du contrôle, réconcilie Docker, efface
les canaux puis les paquets et libère les réservations. Attendre la disparition
physique, pas seulement un statut terminal. Un nouveau candidat D est publié
une seule fois après cette reprise. Son hash est invoqué tandis que S reste la
cible sans tag. Le second cycle republie ce même pilote et doit réutiliser sa
révision. Les appels vérifient aussi données/cache et configuration courante.

## Campagne et preuves

`node e2e/function-version-validation.mjs` crée et nettoie ses objets ;
`function-version-validation-faults.py` opère uniquement les permissions et
observations bornées décrites ci-dessus. La préparation stable est un prérequis,
les quatre groupes couvrent faute/reprise socket puis faute/reprise canal avec
SIGKILL du helper. Une étape manquée, un événement absent, une restauration non
confirmée ou un nettoyage incomplet fait échouer la campagne, sans skip.

Les sources/images sont figées avant/après. La preuve comprend états HTTP et
durables, événements Docker, inode et modes, reçus de garde, disparition des
unités/helpers/canaux/paquets, invocations corrélées et purge de la fonction par
les API. Aucun résultat de protocole, appel système ou réponse n’est remplacé.
La bibliothèque d’observation SQLite garde l’identité réelle du propriétaire.
Aucune nouvelle interface, image ou configuration de déploiement n’est requise.
Les autres pannes et la régression complète restent ouvertes dans SLS-074.
