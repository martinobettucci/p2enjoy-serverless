# Développement et exploitation du SPARK

Le dépôt de travail est `/home/p2enjoy/Documents/VSCodeProjects/p2enjoy-serverless`. La copie exécutée est `/srv/p2enjoy-serverless`. Lire les README, CLAUDE_PROJECT et les contrats de docs/ avant intervention. Cette cellule DEV est la seule cible autorisée ; aucun profil PREPROD/PROD, aucune administration de la FORGE.

## Configuration et données

La configuration consommée vient exclusivement de `/etc/spark/env` et `/run/spark/secrets`. Proposer les changements dans les fichiers voisins `.?`, puis utiliser la console SPARK pour les appliquer. La même procédure s’applique aux trois notes. Aucun `.env`, secret en dépôt ou surcharge de conteneur de substitution.

Le contrôle conserve sa base et ses artefacts dans `/srv/p2enjoy-serverless/state`. La clé `SERVERLESS_MASTER_KEY` reste liée à cette base. Le schéma courant porte les migrations 001 à 006 ; les sauvegardes natives avant 005 et 006 et leurs vérifications sont décrites dans `docs/PLATFORM_DEV.md`. Les écritures postérieures empêchent une restauration implicite. SLS-031 ne demande aucune nouvelle migration.

L’agent possède `/srv/p2enjoy-serverless/storage-state`, schéma 004. Son canal `/srv/p2enjoy-serverless/storage-channel` est privé et monté readonly dans le contrôle. Ne jamais monter les backings natifs dans un workload : acquérir un bail et utiliser son chemin FUSE. Budget logique 32768 Mio, marge physique 8192 Mio, plafond 64 montages. Les valeurs officielles restent l’autorité.

## Construire et déployer

Comme `spark-docker`, depuis `/srv/p2enjoy-serverless`, exécuter séparément :

```sh
bash control/dev.sh build
bash control/dev.sh up
bash control/dev.sh status
```

`logs` consulte les traces ; `stop` conserve les données. L’image du contrôle courant est `sha256:1ef637d7b9f111f5a7324c99c99ff365e9e043ff3c28fed16d8f5946c045dd4a`. Le runtime de plateforme configuré est immuable ; ne pas le confondre avec l’exécuteur de référence. La CLI reconstruite est `sha256:2317812323104076be3511b602cafc07b3c6d09d064c92605d700603853c44fa` ; son image cliente E2E est `sha256:bb9965b48a6db60e24da61d9f2f081443d5b03e100081f7a6a4188ee3cb0395e`.

Pour l’agent, construire par `bash storage/dev.sh build` comme spark-docker ; installer par `bash storage/dev.sh install` comme root du SPARK. L’installation exige un agent sain, sans bail, intention ni montage et ferme les mutations par quiesce. Le paquet courant est `8bf1292fb61b28d1644d7488351b527ed9429e06c1f247685514ce52710d1dc4`. Les paquets précédents sont conservés ; aucun retour de schéma implicite.

Un arrêt brutal de l’agent conserve baux et fichiers mais invalide les anciens binds. Détruire et confirmer l’absence des consommateurs Docker avant de libérer leurs baux. Une erreur de nettoyage conserve la responsabilité ; ne pas supprimer de ligne du registre pour la masquer.

## Qualifier en série

Synchroniser les sources e2e/ avant exécution. Depuis le dépôt du poste, avec la vraie session de console enregistrée sous `.local/e2e/admin-session.json` :

```sh
node e2e/public-invocations.mjs
node e2e/function-storage.mjs
node e2e/control-admin.mjs
node e2e/control-ui.mjs
node e2e/deployments.mjs
node e2e/code-publications.mjs
node e2e/publication-ui.mjs
node e2e/manual-ui.mjs
node e2e/adapter-deploy.mjs
node e2e/service-configuration.mjs
node e2e/publication-recovery.mjs
python3 -B e2e/public.py
```

La suite commune du moteur et de ses régressions se lance aussi par `python3 e2e/execution-suite.py` depuis le poste. Elle exécute quatorze campagnes en série et rattache chaque rapport fraîchement écrit à l’image et aux empreintes des sources locales/distantes avant et après la commande. La configuration commune conserve ses campagnes distinctes. Le stockage public est intégré par `--scope storage-console` : 29 campagnes, 397 groupes, quatre prérequis non comptés et 173 sources liées avant/après. Lire `e2e/README.md` pour les deux phases de qualification. Aucun fichier source ne doit être modifié pendant une suite.

Comme spark-docker dans le SPARK : `python3 -B e2e/control-operations.py`. Comme root dans le SPARK, séparément : `python3 -B e2e/storage-preparations.py`, `bash storage/dev.sh agent-test`, `bash storage/dev.sh limits-test`, puis `python3 -B e2e/managed-storage.py`.

Attendre la fin complète de chaque commande. Les campagnes de panne visent seulement les composants de cette cellule ; leurs timers indépendants et finally restaurent les services. Après `docker kill`, le pilote appelle explicitement `docker start`. Un rapport incomplet ou un nettoyage échoué est un échec, jamais un succès partiel.

Les objets se créent et se suppriment par leurs vraies API. Une purge de qualification vérifie la fonction, son namespace exact, sa suppression logique et l’absence de consommateur. La commande publique purge les volumes, le code et la configuration de cette fonction ; son reçu et le nettoyage physique sont recoupés. Les archives métier restent conservées jusqu’à leur purge explicite. Ne pas nettoyer globalement par préfixe.

Le banc de référence possède ses commandes dans qualification/README.md ; ses volumes nommés restent durables. Les suites de composant, packaging et extraction ont leurs commandes dans adapter/, runtime/, storage/ et control/README.md. Le backlog décrit les preuves encore ouvertes.

## Budgets et reprise du moteur

Les budgets officiels des fonctions sont 1 CPU, 8192 Mio et 32 instances ; les attentes sont bornées à 128 globalement et 16 par fonction. Contrôle, stockage et validation sont exclus de ces réservations. Le moteur vérifie que les minima de toutes les fonctions actives tiennent ensemble. Les anciennes générations et nettoyages en attente restent comptés.

Le répertoire state/execution contient les canaux privés liés aux UUID de réservation. Ne pas supprimer manuellement ses entrées ni les lignes SQLite. Un redémarrage confirme la destruction de ses conteneurs/réseaux et la restitution des baux avant réouverture des admissions. Un appel interrompu n’est jamais rejoué automatiquement.

La campagne publique utilise la console SPARK locale pour réduire temporairement le plafond à deux, puis restaurer trente-deux et relire la valeur consommée. Ne pas éditer cette clé simultanément. Ses gardes sont restaurées sur fin de scénario, EOF ou délai ; les rapports exigent le nettoyage complet. HTTP/1.1 derrière le proxy peut attendre la fin d’un corps avant de transmettre le 408 déjà décidé ; HTTP/2 reçoit ce refus anticipé après trente secondes.

## Qualification de publication et maintenance du guide

`python3 -B e2e/execution-suite.py --scope publication` réunit les 18 campagnes du moteur et de la console sans doublons. Les 312 groupes passent avec les mêmes sources et image. Les rapports frais, la revue visuelle et les ressources restantes sont recoupés dans `docs/evidence/publication-console-dev-2026-11-07.json`. Les 18 campagnes ont terminé à zéro ; l’enveloppe de lancement a renvoyé 143 après le rapport atomique complet. Cette anomalie de cause inconnue est conservée dans la preuve avec la collecte indépendante réussie des rapports, sources, image et nettoyages.

`publication-cleanup-fault.py` refuse temporairement l’ouverture du parent d’une seule révision inactive possédée par sa campagne. Il vérifie l’inode, les permissions et le refus EACCES réel dans Docker. Une garde systemd indépendante restaure le mode après interruption ; le test confirme ensuite la maintenance normale. Ne pas lancer une autre campagne ni redémarrer le contrôle sous cette faute. Le scénario de confirmation de stockage suspend l’agent réel pendant l’expiration de confirmation, puis vérifie sa reprise avant tout nettoyage.

Maintenir `docs/manual.md` dans le même changement que chaque comportement utilisateur. Le build de console l’embarque directement, avec son empreinte ; le navigateur doit retrouver ses chapitres, paragraphes et tableaux. Les trois notes de cellule sont maintenues dans `qualification/spark-notes/`, proposées par les fichiers `.?`, appliquées par la console SPARK puis relues.

## Effacements corrélés du stockage

Le registre 004 ajoute les reçus start-discard/discard-operation. Sauvegarde
native avant migration : `/srv/p2enjoy-serverless/storage-state/backups/before-004-20261107T030639Z.sqlite3`. Son intégrité, l’identité et les
lignes préexistantes sont recoupées. L’ancien agent refuse ce schéma ; ne pas
remplacer simplement le paquet pour revenir en arrière.

La commande `python3 -B e2e/execution-suite.py --scope storage`, depuis le poste,
exécute actuellement sept campagnes et 107 groupes réels. Le checkpoint historique SLS-064 conserve ses 106 groupes sans échec/skip. Elle exige
la vraie session SSO pour les régressions HTTPS. La campagne ciblée peut se
lancer comme root DEV par `python3 -B e2e/storage-discard.py`. Elle crée un
arbre de 150 000 fichiers, exerce permissions, verrou SQLite, restart et
SIGKILL ; ses gardes restaurent les permissions. Attendre sa fin avant une
autre intervention. Rapport : storage/discard-proof.json.

Le reçu corrélé retrouve une opération après réponse perdue sans effacer un
cache reconstruit. La suppression récursive laisse le verrou de registre
disponible. Une exception de worker SQLite produit le diagnostic JSON
`storage_discard_worker_failed`, avec UUID et code fixe, puis une reprise.
Les routes publiques et leurs commandes de console sont déployées ; leurs
preuves et limites sont suivies dans SLS-065. La campagne historique reconstruit
une ancienne image et restaure les trois répertoires originaux après sa fenêtre
de test, avec garde indépendante. Lire `docs/STORAGE_LEGACY_PROOF.md` et
`e2e/README.md` avant son lancement ; elle ne s’exécute jamais avec une autre
campagne active.

## Qualification de configuration commune

La preuve `docs/evidence/service-configuration-dev-2026-11-08.json` porte 191
groupes : 153 sur le poste puis 38 rejoués dans les clients Docker, en série.
Les 165 sources sont identiques avant/après chaque campagne ; les 25 fichiers
Python/migrations du contrôle et cinq modules de la CLI sont recoupés dans les
images exécutées. Le contrôle et l’agent sont sains au repos ; les deux fonctions
ciblées et onze répertoires d’artefacts sont purgés, les réservations à zéro.
Les 21 captures de gestion et du manuel sont inspectées.
SLS-031 est qualifiée par le complément
`docs/evidence/service-configuration-transport-dev-2026-11-08.json` : cinq groupes
natifs puis treize groupes rejoués sur la même image, avec 167 sources recoupées.
`node e2e/service-transport.mjs` lance le vrai client CLI et suspend le contrôle
avant traitement ou après commit, puis SIGKILL et restauration du conteneur
original. Il exige strace sur le poste, root et PTRACE sur ce seul DEV x86_64.
L’installation doit être au repos, sans autre campagne ; une garde systemd
indépendante borne la perturbation. Les deux CLI rendent unknown sans rejeu,
les relances publient et invoquent Docker. Quatre fonctions et treize artefacts
des deux campagnes sont purgés, les trois gardes inactives et les réservations
à zéro. Lire `e2e/README.md` et `docs/SERVICE_CONFIGURATION_URLS.md` avant usage.

## Qualification complète du stockage public

Depuis le poste, `python3 -B e2e/execution-suite.py --scope storage-console`
reçoit les identifiants SSO en JSON sur stdin privée, sans écho, argument,
variable ni fichier contenant cette saisie. Le client ouvre deux connexions
réelles au début, puis renouvelle une paire juste avant la campagne qui ferme
la session de purge. Le build historique, ces deux préparations et le collecteur
physique ne gonflent pas les 397 groupes des 29 campagnes. Les rapports sont
invalidés avant exécution et rattachés aux 173 sources et à l’image.

Le complément `node e2e/storage-console-api.mjs` rejoue neuf groupes avec SSH
root DEV : quatorze corps de purge invalides, version périmée avec UUID neuf et
comparaison native avant/après. Le mode inspect-api-refusals est seulement en
lecture et borné au namespace API exact ; les modes de perturbation restent
bornés à storage-recovery. Ses quatre fonctions s’ajoutent aux 24 du replay,
avec purges physiques recoupées et ressources globales libérées. Les deux phases
et les deux mises à jour documentaires de statut postérieures sont explicites
dans docs/evidence/storage-console-dev-2026-11-08.json. Les 72 images sont
recoupées ; les captures de connexion/manuel régénérées sont identiques aux
images déjà inspectées. Aucun nouveau déploiement applicatif ni migration.

## Adresses d’appel en qualification

SLS-066 lit la projection officielle des routes par le montage readonly
`/etc/spark:/spark:ro`. La facette Adresses d’appel et son lien depuis le
service affichent URL, méthodes et transport déclaré. La copie native propose
un emplacement de jeton, sans valeur réelle ; les erreurs retirent les
anciennes adresses. Le résultat CLI ajoute la même information après publication.
La console et le SSO gardent leur origine canonique.

Le checkpoint `docs/evidence/invocation-urls-checkpoint-dev-2026-11-08.json`
passe 88 groupes réels : huit API/CLI, six UI, 36 régressions et 38 groupes CLI Docker. Les 31 captures
sont recoupées ; le manuel à 14 chapitres et 43 paragraphes est compilé et
vérifié. Les neuf fonctions des essais/replays sont purgées et les 26 sources
Python/SQL embarquées recoupées. Ce checkpoint ne clôture pas l’unité.

La régression complète `docs/evidence/invocation-urls-regressions-dev-2026-11-08.json`
passe ensuite 35 campagnes et 467 groupes, zéro échec/skip. Six prérequis sont
non comptés ; 186 sources et images contrôle/CLI sont identiques avant/après
chaque phase. Les 32 fonctions suivies sont purgées dans dix namespaces ; les
deux restaurations historiques restent distinctes. Les 79 captures fraîches
sont recoupées : 61 observations et 18 identités SHA avec une référence inspectée.
Le contrôle et la référence sont sains, l’agent actif, les réservations et
allocations globales à zéro. Les archives historiques étrangères restent conservées.

La preuve native du Host est acquise en boucle locale. Restent les changements
réels de routes/TLS, seconde page sur six domaines et source perturbée.
Le GET CLI 401 après publication est qualifié séparément ci-dessous. Le build nominal CLI est
qualifié ; sa branche d’expiration/perte SSH reste à éprouver. SLS-066 demeure
ouverte. L’alias functions.lelabs.tech vers 18090 TLS est proposé dans routes.? ;
il n’est pas appliqué. Aucun nouveau secret, variable ou schéma ; la configuration
reste dans les deux fichiers de cellule. Ces trois notes sont proposées,
sans revendiquer leur adoption.

Rejouer séparément et en série `node e2e/invocation-urls.mjs` puis
`node e2e/invocation-urls-ui.mjs`. Ces commandes exigent la session SSO réelle
et utilisent le contrôle déployé, la vraie CLI, les publications Docker et
le presse-papiers natif. Leur périmètre est celui des domaines réellement
affectés, sans registre ou réponse substitué.


## Transport du catalogue après publication

Le complément `docs/evidence/invocation-url-transport-dev-2026-11-08.json`
passe trois nouveaux groupes puis treize de régression en série, zéro échec/skip.
Les deux vrais HTTP 502 du catalogue conservent la publication et ses UUID ;
six connexions HTTPS CLI sont comptées, sans rejeu. Après reprise, catalogue
et invocation Docker fonctionnent. Les 187 sources/images sont recoupées avant
et après chaque phase, huit fonctions purgées dans trois namespaces, six gardes
terminées et 26 fichiers embarqués conformes. La référence conserve son identité,
son image et son démarrage. Aucun changement produit, build du contrôle,
migration, variable, secret ou route appliquée pour ce complément.

Le refus 401 après publication est qualifié ci-dessous ; le 403 reste distinct. Les branches d’expiration,
sortie excessive, lancement et nettoyage après réponses de création/purge perdues
du nouveau client ne sont pas déclarées acquises. Le client exige la disparition
de tout le groupe CLI avant nettoyage et reprend une purge par son UUID conservé.
La preuve complète de 467 groupes reste distincte. SLS-066 demeure ouverte.


## Révocation avant le catalogue facultatif

La preuve `docs/evidence/invocation-url-refusal-dev-2026-11-08.json` passe
quatre groupes de transport puis treize de régression, soit 17, sans échec/skip.
La CLI est retenue avant sa sixième connexion ; le jeton révoqué par l’API donne
un vrai 401 sans changer la publication réussie ni ses UUID, avec six connexions
sans rejeu. Un autre Read retrouve le catalogue et invoque Docker. Les 188 sources
et images sont recoupées, neuf fonctions purgées dans trois namespaces, six gardes
terminées et 26 fichiers embarqués conformes. Le premier essai incomplet est
conservé séparément : barrière manquée de cause inconnue, deux fonctions et deux
gardes nettoyées. Aucun changement produit, migration, build du contrôle,
variable, secret ou route appliquée. Le 403, les pannes du pilote et les branches
de confidentialité/illisibilité du diagnostic restent non éprouvés. SLS-066
reste ouverte. Les trois notes sont proposées, sans revendiquer leur adoption.
