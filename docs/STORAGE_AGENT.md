# Agent local des volumes

Contrat SLS-050, en cours de réalisation. Il complète le stockage de
[PLATFORM](PLATFORM.md#stockage) et [EXECUTION](EXECUTION.md#stockage-associé).
Le proxy FUSE et le pilote d’instances sont déjà qualifiés séparément ; ce
contrat définit leur raccordement. Aucun parcours de gestion publique ne se
considère qualifié par la seule preuve opérateur.

## Propriété et exécution

Un agent Python standard supervise le binaire Go de quota dans la cellule,
sous le même UID que Docker rootless. Son code installé et le binaire sont
possédés par root, non modifiables par cet UID. Python est lancé en mode isolé.
La capacité CAP_SYS_ADMIN est limitée à ce service de montage ; les fonctions
et le contrôle la gardent absente. Le service lit les deux fichiers officiels
EnvironmentFile de cellule. Aucun service applicatif n’est lancé dans la FORGE.

L’agent partage le namespace de montage de la cellule pour rendre ses montages
visibles au démon Docker. Les options systemd créant un namespace de fichiers
privé ne sont donc pas employées. La propriété est mesurée par les inodes de
namespace et par un bind Docker réel ; une option déclarée seule ne suffit pas.
Les sources de cette contrainte sont la [documentation systemd.exec](https://www.freedesktop.org/software/systemd/man/259/systemd.exec.html#PrivateMounts=)
et le comportement du [cycle systemd.kill](https://www.freedesktop.org/software/systemd/man/259/systemd.kill.html#KillMode=).
Le service utilise KillMode=control-group : un arrêt de service retire aussi
ses enfants. Une maintenance normale draine d’abord les instances ; un restart
avec consommateurs est traité comme une panne de stockage, jamais comme une
reprise transparente de leurs anciens binds.

Le socket Unix reste dans un répertoire 0700 avec un socket 0600. L’agent
contrôle SO_PEERCRED et refuse un UID autre que le sien, même si une connexion
arrive. Le contrôle est le client de confiance de ce canal ; il conserve
l’autorité CRUD et administrateur des API publiques. Le socket Docker reste
au contrôle. Une libération de bail lui impose d’avoir confirmé la suppression
Docker avant d’envoyer la demande ; elle n’est pas déduite d’un délai écoulé.

## Registre et chemins

Un registre SQLite WAL durable, protégé par flock, recense fonctions, volumes,
quotas, générations de montage, processus et baux. Un seul agent possède une
racine. Les états intermédiaires sont persistés avant leurs opérations système ;
les transactions SQLite sont courtes et ne traversent pas les attentes.
Le lancement d’un processus précède nécessairement l’écriture de son PID : la
reprise peut donc retrouver un enfant orphelin par le binaire, ses arguments
exacts et sa génération déjà inscrite. Un PID seul n’est jamais une identité.
L’identité inclut boot_id, date de naissance /proc et pidfd lorsque disponible.

Les requêtes acceptent des UUID et les types data/cache, jamais un chemin ou
une commande fournis par le client. L’agent dérive backing et mount depuis sa
racine configurée. Le backing est privé ; seul le chemin du montage est rendu
au contrôle détenteur d’un bail. Les racines et parents ne sont pas des liens.
Les volumes restent associés à l’UUID de fonction, indépendamment des révisions.

Chaque lancement FUSE porte un FsName contenant un UUID de génération. Le
mountinfo doit correspondre à ce nom, au chemin et au type attendus. Le flag
supplémentaire du binaire conserve son comportement précédent par défaut.
Un montage étranger est signalé ; il n’est ni adopté ni démonté implicitement.

## Opérations et baux

Le canal échange un objet JSON par connexion, terminé par un saut de ligne,
avec une requête bornée à 16 Kio, une réponse bornée à 64 Kio et au plus seize
connexions. Les lectures initiales ont une échéance de trois secondes. Les
mutations sont sérialisées ; une contention excessive rend une erreur explicite.
Les erreurs retournent des codes fixes, sans message système brut ni contenu
applicatif. Les états sont consultables après une réponse perdue ; aucune
mutation avec effet n’est rejouée automatiquement par le client.

La configuration d’une fonction porte ses deux volumes enabled/quota_mib.
Elle refuse toute différence pendant qu’un bail existe. Chaque nouveau quota
est réellement validé par le proxy, avec montage et rescan des données, avant
commit du nouvel état. Les deux volumes sont préparés avant le commit commun.
Un échec conserve les anciens quotas inscrits et les fichiers. Une configuration
identique est idempotente. Les générations attendues empêchent une mutation
sur un état devenu périmé.

La préparation démonte l’ancienne génération avant de lancer un candidat sur
le même backing. Chaque candidat est arrêté et son démontage confirmé avant
le commit commun. Une intention durable bloque toute acquisition pendant cette
préparation. Si le second volume échoue, les candidats du premier sont aussi
retirés ; les anciens quotas restent publiés et seront remontés à la prochaine
acquisition. Un nettoyage non confirmé garde l’intention et un état dégradé.
La reprise retire ces seules générations identifiées avant de lever le blocage ;
elle ne présente pas le seul état SQLite comme une compensation achevée.

Un bail porte l’UUID du consommateur, celui de son contrôle et la fonction.
Il est durable avant création Docker et protège les deux montages demandés.
L’acquisition vérifie quotas et état courants, limite de montages, identité FUSE
et santé réelle, puis rend les générations et chemins. Une demande identique
avec le même UUID de consommateur retrouve son bail ; une demande différente
est refusée. Il n’y a pas de TTL libérant un consommateur encore vivant.

La libération intervient après la destruction confirmée du consommateur.
Le dernier bail permet de démonter et d’arrêter FUSE pour restituer ses ressources.
Les données et le quota alloué restent enregistrés. Un échec de démontage ou
de nettoyage conserve un état dégradé et bloque la réutilisation jusqu’à reprise.
L’arrêt n’utilise pas de démontage paresseux. Un conteneur simplement arrêté
n’est pas considéré comme supprimé.

Le pilote d’instances reçoit un client réel d’agent et sa configuration de
volumes. Il acquiert le bail avant Docker, monte seulement les chemins retournés,
et confirme FUSE au bootstrap comme auparavant. Il ne libère le bail qu’après
son propre nettoyage confirmé, y compris après échec de démarrage ou annulation.
Un bail acquis dont la réponse est perdue est retrouvé/libéré par son UUID
après confirmation de l’absence de ce consommateur. Les montages fournis au
diagnostic opérateur restent distincts de ce parcours géré.

## Santé et reprise

Une présence dans mountinfo n’est pas une preuve de santé. Une sonde réelle
statfs/stat vérifie l’usage logique, la capacité et l’identité de périphérique.
Elle s’exécute dans un processus séparé, avec une échéance, pour qu’un appel FUSE
bloqué n’immobilise pas la boucle de l’agent. Les sondes simultanées sont bornées ;
un processus impossible à terminer est conservé dans le registre et empêche
l’accumulation de nouvelles sondes. Les résultats sont recoupés avec la même
génération et le même mountinfo après la sonde.

L’usage affiché est l’usage logique du proxy, qui compte aussi les fichiers
supprimés encore ouverts. Un scan du backing ne remplace pas cette mesure sur
un volume monté. Après le dernier consommateur et démontage, le rescan du proxy
fait autorité pour une réduction de quota. Une valeur inconnue reste inconnue.

Après mort d’un démon FUSE, ses baux restent présents et de nouvelles acquisitions
sont refusées. Le contrôle retire ses consommateurs avant libération. L’agent
peut alors retirer le montage déconnecté, reconstruire le compteur et fournir
une nouvelle génération. Les fichiers sont conservés. Après redémarrage de
l’agent, les baux persistent ; un démon encore vivant ne peut être adopté que
sur identité complète. Un reboot ne valide jamais un ancien PID réutilisé.
La reprise du contrôle réconcilie ses instances Docker avant de restituer ses
baux orphelins. Elle ne rejoue aucune invocation interrompue.

## Conservation et budgets

Désactiver un volume conserve ses fichiers et son allocation. Le réactiver
retrouve le même contenu, sous réserve du quota demandé. Le cache suit cette
même règle de conservation ; son caractère reconstructible autorise un vidage
explicite après drainage, pas une suppression implicite au changement de mode.

Archiver une fonction désactive ses volumes, interdit les nouveaux baux et
conserve données et cache. L’archivage refuse tant qu’un bail subsiste ; le
contrôle ferme les admissions et termine le drainage avant de le demander.
La purge exige l’état archivé et l’absence de bail.
Elle est réservée aux administrateurs par le contrôle. L’agent sépare la mise
à l’écart atomique des fichiers et leur suppression effective ; la réservation
n’est libérée qu’après nettoyage confirmé. Un échec conserve un état reprenable.
Le vidage explicite du cache conserve sa configuration et son quota. Les UUID
de fonctions purgées restent des tombstones ; aucune recréation implicite sous
le même UUID n’efface cette histoire.

Les quotas des volumes actifs, désactivés, archivés et en nettoyage comptent
dans le budget global. Le défaut est 32 Gio, avec 8 Gio de marge de libre espace
sur le filesystem de la racine avant une nouvelle allocation. Une augmentation
est refusée si ces contraintes ne tiennent pas. La limite de montages simultanés
vaut 64 par défaut ; un volume conservé sans bail ne garde pas un démon inutile.
Les préparations et démarrages réservent aussi une place avant le lancement,
et un arrêt non confirmé la conserve. Une préparation réserve durablement
chaque augmentation de quota en plus des allocations publiées ; une baisse
n’est libérée qu’au commit. Cette règle peut refuser un transfert entre deux
volumes lorsque sa préparation dépasse temporairement le budget disponible.
Les quotas de volume gardent la plage publique de 1 à 65 536 Mio. La limite
agrégée peut donc refuser une allocation individuelle pourtant valide.

Paramètres de cellule : SERVERLESS_STORAGE_ROOT_HOST et
SERVERLESS_STORAGE_SOCKET_DIR_HOST sont requis ; SERVERLESS_STORAGE_BUDGET_MIB
(défaut 32768), SERVERLESS_STORAGE_RESERVE_MIB (8192) et
SERVERLESS_STORAGE_MAX_MOUNTS (64) sont facultatifs. L’installation conserve les
artefacts exécutables sous un répertoire root non modifiable par l’agent ;
le binaire de quota est celui du même paquet installé. Les valeurs DEV sont
proposées et appliquées par la console avant démarrage.

## Réalisation et preuves

1. Construire le registre, la supervision, le canal et les opérations de volume,
   installer le service DEV et qualifier avec le vrai proxy FUSE et Docker.
2. Raccorder les baux au pilote d’instances et exercer de vrais handlers sur
   data/cache : quota, persistance, défaut FUSE, redémarrage de l’agent, nettoyage.
3. Raccorder les mutations publiques et admissions avec leur relecture de droits
   et versions ; qualifier par les API authentifiées et la console.

La première campagne comprend double propriétaire, refus d’UID, entrées
malformées, baux idempotents, mutations refusées pendant consommation,
saturation, quotas trop petits, conservation après désactivation et archive,
vidage/purge explicites, montée de génération, processus FUSE arrêté ou tué,
sonde bloquée, reprise de service et réservations conservées sur erreur.
Les preuves de composants ne ferment pas les parcours publics ni SLS-050.
