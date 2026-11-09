# Développement et exploitation du SPARK

Le dépôt de travail est `/home/p2enjoy/Documents/VSCodeProjects/p2enjoy-serverless`. La copie exécutée est `/srv/p2enjoy-serverless`. Lire les README, CLAUDE_PROJECT et les contrats de docs/ avant intervention. Cette cellule DEV est la seule cible autorisée ; aucun profil PREPROD/PROD, aucune administration de la FORGE.

## Configuration et données

La configuration consommée vient exclusivement de `/etc/spark/env` et `/run/spark/secrets`. Proposer les changements dans les fichiers voisins `.?`, puis utiliser la console SPARK pour les appliquer. La même procédure s’applique aux trois notes. Aucun `.env`, secret en dépôt ou surcharge de conteneur de substitution.

Le contrôle conserve sa base et ses artefacts dans `/srv/p2enjoy-serverless/state`. La clé `SERVERLESS_MASTER_KEY` reste liée à cette base. Le schéma courant porte les migrations001 à008. Les sauvegardes natives avant005/006 sont décrites dans `docs/PLATFORM_DEV.md` ; celles avant008 et sa migration ciblée sont recoupées dans `docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json`. Les écritures postérieures empêchent une restauration implicite. SLS-031 ne demande aucune nouvelle migration.

L’agent possède `/srv/p2enjoy-serverless/storage-state`, schéma 004. Son canal `/srv/p2enjoy-serverless/storage-channel` est privé et monté readonly dans le contrôle. Ne jamais monter les backings natifs dans un workload : acquérir un bail et utiliser son chemin FUSE. Budget logique 32768 Mio, marge physique 8192 Mio, plafond 64 montages. Les valeurs officielles restent l’autorité.

## Construire et déployer

Comme `spark-docker`, depuis `/srv/p2enjoy-serverless`, exécuter séparément :

```sh
bash control/dev.sh build
bash control/dev.sh up
bash control/dev.sh status
```

`logs` consulte les traces ; `stop` conserve les données. L’image du contrôle courant est `sha256:178394abb337bd70ca9c18a139fc65ab2c1f83d3ad41eed5d5bf79bed2dc0f5e`. Le runtime de plateforme configuré est immuable ; ne pas le confondre avec l’exécuteur de référence. La CLI reconstruite est `sha256:77a3c302eb0d6cb6f0f592dbaae2a682943a8c9eb0a0bbdc2e84b2646a581106` ; son image cliente E2E est `sha256:a986c0d0fb238af7d076b011f596c844e102bb8df107277f67aac6629b1d430c`.

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

La preuve native du Host est acquise en boucle locale. Le couple de domaines TLS, son retrait d’alias et ses détours sont vérifiés ; restent
seconde page sur six domaines et source perturbée.
Le GET CLI 401 après publication est qualifié séparément ci-dessous. Le build nominal CLI est
qualifié ; sa branche d’expiration/perte SSH reste à éprouver. SLS-066 demeure
ouverte. L’alias functions.lelabs.tech vers 18090 TLS est appliqué par la
console normale du seul SPARK ; son certificat et sa résolution native sont vérifiés. Aucun nouveau secret, variable ou schéma ; la configuration
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


## Maintenir et qualifier le catalogue global

Contrat : docs/FUNCTION_CATALOGUE.md ; lectures API dans app/catalogue.py et
console dans web/src/catalogue.jsx. Aucune migration, dépendance, variable ou
secret ajouté. Le contrôle embarque 27 fichiers Python/migrations recoupés.
Les quatre fichiers web servis en HTTPS sont identiques aux octets de l’image.

Depuis le dépôt du poste, python3 -B e2e/execution-suite.py --scope function-catalogue
rejoue le parcours intégral : 37 campagnes, 489 groupes attendus et six
prérequis distincts. La preuve courante conserve 30 campagnes (447 groupes)
aux clients inchangés et sept réexécutées (42 groupes), sur les mêmes images.
Le pilote function-catalogue-completion.py est borné à l’archive et aux écarts
exacts du gel de cette preuve ; il ne remplace pas une nouvelle qualification
si une source produit, fixture ou image change. Les statuts documentaires
postérieurs ont leurs empreintes séparées.

Les 98 captures actives sont inspectées, dont les trois positions de table
mobile et le dialog plein viewport. Le manuel compilé vient de docs/manual.md :
15 chapitres, 46 paragraphes, empreinte recoupée. Les collecteurs lisent trois
jeux séparés d’UUID (10/32, 7/32, 6/27 namespaces/fonctions), sans relâcher leurs
limites. Le nettoyage de 39 fonctions des résultats écartés reste distinct.
Les deux arrêts précédents restent incomplets ; ils ne sont pas transformés
en succès. La preuve du canal privé corrige seulement son client HTTP.

Les configurations restent dans /etc/spark/env et /run/spark/secrets, avec
/etc/spark monté readonly dans l’API. L’alias functions.lelabs.tech est désormais
appliqué par la console normale du seul SPARK, selon le complément ci-dessous.
Ces notes restent des propositions.


## Deux domaines TLS — complément SLS-066

https://functions.lelabs.tech et https://serverless.lelabs.tech visent désormais
le port 18090 du même contrôle. La console et le SSO gardent leur domaine
canonique serverless.lelabs.tech. Le DNS A exact de functions et sa route TLS
sont posés par la console normale autorisée ; les deux HTTPS sont vérifiés
sans substitution de DNS ni contournement de certificat. La projection officielle
porte les deux lignes, lisibles depuis le montage readonly du contrôle.

Les huit groupes API/CLI et six parcours UI passent sur les deux domaines :
publication, appels Docker des adresses émises, droits, chemins/méthodes,
révisions et rollback. Leurs quatre fonctions sont purgées dans deux namespaces
et recoupées nativement. Sources de preuve :
docs/evidence/invocation-domains-dev-2026-11-08.json. Ce complément ne clôture
pas SLS-066. Les cinq cycles ultérieurs qualifient retrait, détours et API locale
vide local ; le complément UI ci-dessous qualifie le parcours public vide.
Source perturbée et pages UI/CLI sur six domaines restent ouvertes.

La première déclaration est conservée comme interrompue pendant une comparaison
trop stricte de applied_at ; sa reprise en lecture seule vérifie les propriétés
matérielles inchangées et les vrais HTTPS, sans second POST. Le premier départ
API sur session expirée est également conservé, avant création de ressources ;
le replay utilise une nouvelle connexion SSO réelle. Aucun nouveau secret,
variable, schéma ou build du contrôle. Les notes sont proposées sans adoption.


## Garde vérifiée avant perturbation

Les trois déclencheurs de garde passent sur la résolution native rétablie :
restauration explicite, SIGKILL du seul pilote avec restauration indépendante,
et échéance avec pilote vivant. Chaque scénario confirme les deux HTTPS et la
fin de la garde. Les ports restent à 18090 ; aucun détour, retrait ou
rétablissement d’alias n’est qualifié par ces trois groupes.

La première échéance échouée et son diagnostic DNS restent conservés séparément.
Après expiration du cache négatif en amont, les deux domaines résolvent
nativement vers l’adresse attendue ; aucune adresse ni aucun résolveur n’est
forcé dans les tests. Preuve : docs/evidence/invocation-route-guard-dev-2026-11-08.json.
Les perturbations réelles passent les cinq cycles ci-dessous ; le parcours public vide est qualifié ci-dessous, les fautes de source restent à éprouver.
Aucune nouvelle variable, secret, route ou image applicative dans cette étape.
Ces trois notes restent proposées, sans adoption revendiquée.


## Cinq cycles réels des routes — 9 novembre

Cinq groupes sérialisés passent sur 203 sources inchangées et les mêmes images :
pages API de taille un et appels des deux domaines, détour de l’alias,
restauration indépendante après SIGKILL du pilote, retrait/rétablissement de
l’alias et détour des deux routes avec catalogue HTTP local réellement vide.
Sept appels exécutent le handler Docker depuis les URL émises. Les quatre gardes
sont terminées, la fonction est purgée dans son namespace et ses parents supprimés.
Les deux routes sont rétablies à 18090 TLS ; la recréation renouvelle l’identifiant
de l’alias. Preuve : docs/evidence/invocation-route-cycles-dev-2026-11-09.json.

Aucun build, variable ou secret ajouté ; les deux fichiers officiels et les
services sont inchangés. Le vide UI public est qualifié ci-dessous ; les fautes
de source et la seconde
page UI/CLI restent ouverts. Les quatre alias temporaires de pagination sont
une proposition locale en attente d’autorisation, sans création DNS ni route.
Ces trois notes sont proposées individuellement, sans adoption revendiquée.


## Pause et reprise natives — deux groupes qualifiés

Le vrai GET HTTPS est retenu après recvfrom puis libéré. Il survit aussi au
SIGKILL du traceur, avec confirmation de reprise par le programme indépendant. Les deux groupes passent sur 205 sources ;
la même requête termine à 200 avec deux domaines, sans mesure de sa fin par
rapport au SIGCONT de garde. Le timer déjà collecté est
reconnu uniquement par son absence/inactivité natives. L’essai initial arrêté
et le diagnostic restent distincts du replay. Deux fonctions sont purgées dans
deux namespaces ; quatre helpers et quatre paires timer/service sont terminés.
Contrôle non tracé, PID/démarrage/images et configuration officielle inchangés.
Preuve : docs/evidence/invocation-request-pause-dev-2026-11-09.json.
Aucune route, DNS, variable, secret ni build nouveau dans ce complément natif.
Le parcours public vide est qualifié ci-dessous ; fautes propres du pilote, source
et pagination UI/CLI restent ouverts.
Ces notes sont proposées, sans adoption revendiquée.


## Catalogue public vide — trois groupes qualifiés

Création/publication depuis l’accueil par les formulaires, vrai GET du bouton
Actualiser retenu pendant détour normal des deux routes vers 18091, puis réponse
200/source disponible/total zéro. Les cinq JPEG sont inspectés : aide vide utile
sans URL/copie sur desktop et mobile, retour lisible des deux domaines après
restauration 18090 TLS. L’adresse copiée invoque réellement le handler Docker.
Trois groupes passent sur 206 sources et les mêmes images. Une fonction est
purgée dans son namespace ; helper natif, timer/service et garde de routes sont
terminés. Contrôle non tracé et sans redémarrage, référence/configuration inchangées.
Preuve : docs/evidence/invocation-empty-ui-dev-2026-11-09.json.
Aucun domaine/DNS, variable, secret ni build nouveau. Les erreurs propres du
client, les fautes de source et les pages sur six domaines restent à éprouver.
Ces notes sont proposées individuellement, sans adoption revendiquée.


## Alias public et vrai SSO — trois groupes qualifiés

L’alias redirige accueil/login/console vers la canonique sans y poser de cookie ;
son API session anonyme reste à 200 sans redirection. Les contextes desktop et
mobile entrent par son accueil, se connectent au vrai SSO puis se déconnectent
par l’UI. Le même POST réel est observé par CDP durable : 200, signed_out et
sso_signed_out vrais. Trois groupes passent sur 207 sources et les mêmes images ;
six captures sont inspectées. Deux sessions/flows du replay sont fermés, plus
les deux autres des essais arrêtés conservés séparément. Aucun cookie de reprise
nominal, donnée métier, route, DNS, variable, secret ou build nouveau.
Preuve : docs/evidence/invocation-alias-entry-dev-2026-11-09.json.
Services et fichiers officiels inchangés ; fautes de source, six domaines et
pannes propres du client restent ouverts. Ces notes sont proposées sans adoption.


## Garde des permissions du relevé — trois groupes

Le seul fichier officiel de routes subit chmod 000, puis le contrôle constate
réellement errno 13. Les trois scénarios release/SIGKILL/SIGSTOP passent sur
210 sources, mêmes images. Signaux noyau observés, copies figées et reçus
immuables ; trois helpers/timers/services terminés. Nom/inode/contenu/uid/gid,
mode 0640 et mtime restitués ; ctime change comme attendu. Deux HTTPS sains et
services/démarrages inchangés. Preuve :
docs/evidence/invocation-source-guard-dev-2026-11-09.json.
Aucun workload, route/DNS, variable, secret ou build nouveau. Reçus/programmes
de preuve et verrou privés sous /run ; aucun daemon permanent. Les refus API/UI
restent à qualifier. Ces notes sont proposées, sans adoption revendiquée.


## Catalogue sous refus de lecture — quatre groupes API

Quatre groupes réels passent sur 211 sources et les mêmes images. Publication
par adaptateur, errno 13 du contrôle, diagnostic source_forbidden borné pour
Read/admin et six refus sans diagnostic. Les deux URL connues exécutent Docker
pendant la faute ; restitution explicite puis même catalogue et deux appels.
Quatre invocations et une fonction purgée sont recoupées, helper et unités finis.
Source d’origine au mode 0640, contenu/inode/mtime inchangés ; ctime changée.
Preuve : docs/evidence/invocation-source-api-dev-2026-11-09.json.
Aucun ajout de variable/secret, changement route/DNS, service ou build. Le rendu
UI et les autres fautes restent ouverts. Notes proposées sans adoption annoncée.


## Refus de lecture dans la console — trois groupes navigateur

Trois groupes réels passent sur 212 sources et les mêmes images, depuis
l’accueil/formulaires/publication jusqu’à source_forbidden puis reprise.
Alerte utile desktop/mobile, anciennes adresses/copies/succès absents ; cinq
JPEG frais. Après restitution explicite, une URL copiée invoque Docker.
Une invocation, une fonction purgée et garde finie recoupées nativement ;
parents supprimés, mode 0640 et source/configurations/services inchangés.
Preuve : docs/evidence/invocation-source-ui-dev-2026-11-09.json.
Aucune variable/secret, route/DNS ou build ajouté. Autres fautes/six domaines
restent ouverts. Notes proposées individuellement sans adoption annoncée.


## Identité canonique du paquet — composant qualifié

Bibliothèque function_code_hash.py et CLI Docker d’extraction : sept groupes
ciblés, 45 de régression et neuf invocations réelles sur 222 sources. Contextes
de build limités et prouvés, deux essais arrêtés conservés séparément. Dix-neuf
conteneurs runtime, 37 clients nommés et leurs canaux sont absents. Douze fonctions supprimées
et volumes purgés ; 33 archives de code conservées vérifiées.
Preuve : docs/evidence/function-code-hash-dev-2026-11-09.json.
Aucune variable/secret ou route/DNS ajouté. Services et configuration officiels
inchangés ; seules les images calcul/packaging sont reconstruites. L’API garde
son comportement actuel ; déduplication/promotion/appels par hash restent en cours.
Notes proposées individuellement, sans adoption revendiquée.

Sept groupes rejoués après nommage explicite ; 45 conservés aux clients inchangés,
deux époques de 222 sources et mêmes sources produit/images.


## Registre007 de l’identité du code — historique

La migration 007 et le cache code_hash sont déployés. Les alias UUID historiques
et la cible courante sont conservés ; le premier backfill reconnaît aussi les
purges 006 décidées et fortement corrélées, sans inventer de hash ni retirer les
compteurs/gardes avant leur nettoyage normal. La carte Code et révisions montre
et copie le hash complet. GET /api/functions/{id}/versions fournit une lecture
Read/admin groupée et paginée, sans code ni secrets. À ce checkpoint007, les uploads activaient encore
leur révision. Le checkpoint008 ci-dessous décrit le fonctionnement actuel.

Preuve : docs/evidence/function-version-registry-dev-2026-11-09.json. 359 groupes
sur deux époques de 233 sources aux mêmes fichiers produit et image, dont 46 ciblés
et historiques et 313 communs. 69 captures recoupées : 47 nouvelles inspections,
22 références SHA identiques. Le manuel servi correspond à 15 chapitres et
47 paragraphes. L’ancien checkpoint au repos 328 reste distinct. Le premier arrêt
WAL, son nettoyage natif et le replay 15 groupes du poller sont conservés séparément.
Les six fonctions du registre sont purgées dans six namespaces recoupés ; les
régressions ont leur propre nettoyage dans leurs rapports.

Image de ce checkpoint007 : fe75c9e7, conservée aussi sous
p2enjoy-control:purge-recovery-reference. La référence 006 est reconstruite depuis
le vrai Git f56d79e, vérifiée et conservée sous historical-schema-006. Vérifier
l’image effectivement portée après build/up ; si up garde l’ancien conteneur,
recréer explicitement le seul contrôle par Compose, avec les deux env-file
officiels, puis confirmer image/santé. Après 007 commise, le retour à une image
antérieure exige base/fichiers/volumes cohérents ; après rollback de 007 refusée,
reprendre 006 sur la même base préserve les décisions déjà prises.

Aucune variable, secret ou route ajouté. Les deux domaines TLS restent sur 18090.
Les fichiers officiels, l’agent et le runtime de référence sont conservés ; aucun
daemon permanent nouveau. Les trois notes sont proposées individuellement,
sans revendiquer leur adoption. Configuration par les deux fichiers de cellule ;
aucun .env, ENV/ARG ou environment de configuration ajouté.


## Versions par hash — checkpoint ciblé008

Le contrôle008 prépare une version sans la promouvoir. L’upload identique
réutilise son hash disponible et sa date ; un hash archivé se restaure
explicitement, un hash supprimé se réimporte avec son ZIP validé. Promouvoir
choisit la cible des appels sans tag ; les pilotes utilisent le hash explicite.
Le rollback de code conserve ressources, variables/secrets et volumes courants.
Les appels déjà admis terminent avec leur snapshot ; les pools des versions
partagent les budgets et limites de leur fonction.

La preuve docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json
réunit71 groupes :2 migration/reprise,12 API,5 CLI authentifiés depuis le poste,
6 UI,8 manuel et38 packaging/refus dans les images CLI. Les28 captures sont
inspectées ; manuel15 chapitres/52 paragraphes. Dix fonctions sont purgées,
les dossiers d’artefacts absents et les ressources actives à zéro. Les31 fichiers
Python/SQL backend sont identiques entre époques API/CLI/UI. Les preuves007
ci-dessus restent historiques. Le complément CLI authentifié passe désormais
cinq groupes par image, vingt commandes et douze invocations sur245 sources :
docs/evidence/function-version-cli-images-dev-2026-11-09.json. Deux nouvelles
fonctions sont purgées ; aucun client, réseau/volume ou définition Compose
résiduel. Le premier lanceur direct est remplacé par Compose DEV pour lire les
valeurs citées des deux fichiers officiels, qui ne changent pas. Les pannes du
helper CLI conteneurisé et la régression complète restent ouvertes ; SLS-074 demeure en cours.

Image contrôle courante :178394abb337, référence007 retenue sous
before-function-version-promotions. Après migration008 commise, ne pas remettre
seule une ancienne image : une restauration exige base, artefacts et volumes
cohérents. La sauvegarde native privée avant008 est conservée sous
/srv/p2enjoy-serverless/qualification-history/.

Aucune variable, secret ou route ajouté ; les deux domaines TLS restent18090.
Configuration par les deux fichiers officiels de cellule, aucun .env, ENV/ARG ou
environment de configuration. Agent et runtime de référence sont conservés.
Les trois notes sont proposées individuellement ; leur adoption n’est pas revendiquée.


## Reprise de validation sous faute — quatre groupes qualifiés

La preuve docs/evidence/function-version-validation-recovery-dev-2026-11-09.json
passe quatre groupes sur248 sources : A/B admis, refus socket puis canal isolé,
B refusé avant validation et reprise normale sans redémarrer le contrôle. Le
canal est restitué par garde indépendante après SIGKILL du helper. Les deux
fenêtres Docker ne montrent que le create de A ; cinq invocations retrouvent
stable/pilote, configuration et données/cache. Deux fonctions d’essai/replay
sont purgées et leurs artefacts absents, deux helpers/gardes du replay terminés,
réservations et ressources actives à zéro. Le socket conserve inode/UID/GID/mode
après restitution. Les31 fichiers backend, images, démarrages et fichiers
officiels restent inchangés. Aucun build, variable, secret ou route nouveau.
Les arrêts de prérequis et du premier client restent distincts. Autres pannes
et régression complète restent ouvertes ; les trois notes sont proposées,
sans adoption revendiquée.
