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

`logs` consulte les traces ; `stop` conserve les données. L’image du contrôle courant est `sha256:62ad2b7f13f0e274b7365daa39c1b5f3fcf524a32e82fa27d4acf582e7187900`. Le runtime de plateforme configuré est immuable ; ne pas le confondre avec l’exécuteur de référence. La CLI reconstruite est `sha256:3304f057c81d7dd5169752f8cef7d15c6b9f5788b30d513dbdcd05f11b91277c`.

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

La suite commune du moteur et de ses régressions se lance aussi par `python3 e2e/execution-suite.py` depuis le poste. Elle exécute quatorze campagnes en série et rattache chaque rapport fraîchement écrit à l’image et aux empreintes des sources locales/distantes avant et après la commande. Les campagnes de configuration commune et de stockage public se lancent séparément selon `e2e/README.md` ; leur intégration complète à cette suite reste à faire. Aucun fichier source ne doit être modifié pendant une suite.

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
exécute sept campagnes et 106 groupes réels avec zéro échec/skip. Elle exige
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

## Checkpoint de configuration commune

La preuve `docs/evidence/service-configuration-dev-2026-11-08.json` porte 191
groupes : 153 sur le poste puis 38 rejoués dans les clients Docker, en série.
Les 165 sources sont identiques avant/après chaque campagne ; les 25 fichiers
Python/migrations du contrôle et cinq modules de la CLI sont recoupés dans les
images exécutées. Le contrôle et l’agent sont sains au repos ; les deux fonctions
ciblées et onze répertoires d’artefacts sont purgés, les réservations à zéro.
Les 21 captures de gestion et du manuel sont inspectées.
SLS-031 reste ouverte : la vraie perte d’une réponse de modification commune
et l’issue inconnue de la CLI doivent encore être éprouvées, avant et après
la décision durable. Le banc résiduel est décrit dans
`docs/SERVICE_CONFIGURATION_URLS.md`.
