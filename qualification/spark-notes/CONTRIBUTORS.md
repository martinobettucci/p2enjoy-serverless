# Développement et exploitation du SPARK

Le dépôt de travail est `/home/p2enjoy/Documents/VSCodeProjects/p2enjoy-serverless`. La copie exécutée est `/srv/p2enjoy-serverless`. Lire les README, CLAUDE_PROJECT et les contrats de docs/ avant intervention. Cette cellule DEV est la seule cible autorisée ; aucun profil PREPROD/PROD, aucune administration de la FORGE.

## Configuration et données

La configuration consommée vient exclusivement de `/etc/spark/env` et `/run/spark/secrets`. Proposer les changements dans les fichiers voisins `.?`, puis utiliser la console SPARK pour les appliquer. La même procédure s’applique aux trois notes. Aucun `.env`, secret en dépôt ou surcharge de conteneur de substitution.

Le contrôle conserve sa base et ses artefacts dans `/srv/p2enjoy-serverless/state`. La clé `SERVERLESS_MASTER_KEY` reste liée à cette base. Le schéma courant porte les migrations 001 à 005 ; la sauvegarde native préalable est `state/backups/before-005-20261106T203759Z-a85aa7.sqlite3`, vérifiée intègre en mode 0600. Les écritures postérieures empêchent une restauration implicite.

L’agent possède `/srv/p2enjoy-serverless/storage-state`, schéma 003. Son canal `/srv/p2enjoy-serverless/storage-channel` est privé et monté readonly dans le contrôle. Ne jamais monter les backings natifs dans un workload : acquérir un bail et utiliser son chemin FUSE. Budget logique 32768 Mio, marge physique 8192 Mio, plafond 64 montages. Les valeurs officielles restent l’autorité.

## Construire et déployer

Comme `spark-docker`, depuis `/srv/p2enjoy-serverless`, exécuter séparément :

```sh
bash control/dev.sh build
bash control/dev.sh up
bash control/dev.sh status
```

`logs` consulte les traces ; `stop` conserve les données. L’image du contrôle courant est `sha256:52d17fa14b7fe92ac5bad61695114f687dd702ebff5a57c8d7e3a6e69c1116d6`. Le runtime de plateforme configuré est immuable ; ne pas le confondre avec l’exécuteur de référence.

Pour l’agent, construire par `bash storage/dev.sh build` comme spark-docker ; installer par `bash storage/dev.sh install` comme root du SPARK. L’installation exige un agent sain, sans bail, intention ni montage et ferme les mutations par quiesce. Le paquet courant est `e116f761cadf8a04a59d1f45d729ef29edcb7b1e41e3a81afab43eda4422b255`. Les paquets précédents sont conservés ; aucun retour de schéma implicite.

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
node e2e/publication-recovery.mjs
python3 -B e2e/public.py
```

La suite complète du moteur et de ses régressions se lance aussi par `python3 e2e/execution-suite.py` depuis le poste. Elle exécute quatorze campagnes en série et rattache chaque rapport fraîchement écrit à l’image et aux empreintes des sources locales/distantes avant et après la commande. Aucun fichier source ne doit être modifié pendant la suite.

Comme spark-docker dans le SPARK : `python3 -B e2e/control-operations.py`. Comme root dans le SPARK, séparément : `python3 -B e2e/storage-preparations.py`, `bash storage/dev.sh agent-test`, `bash storage/dev.sh limits-test`, puis `python3 -B e2e/managed-storage.py`.

Attendre la fin complète de chaque commande. Les campagnes de panne visent seulement les composants de cette cellule ; leurs timers indépendants et finally restaurent les services. Après `docker kill`, le pilote appelle explicitement `docker start`. Un rapport incomplet ou un nettoyage échoué est un échec, jamais un succès partiel.

Les objets se créent et se suppriment par leurs vraies API. Une purge de qualification vérifie la fonction, son namespace exact, sa suppression logique et l’absence de consommateur avant d’appeler l’agent. Les archives de code sont conservées et vérifiées séparément. Ne pas nettoyer globalement par préfixe.

Le banc de référence possède ses commandes dans qualification/README.md ; ses volumes nommés restent durables. Les suites de composant, packaging et extraction ont leurs commandes dans adapter/, runtime/, storage/ et control/README.md. Le backlog décrit les preuves encore ouvertes.

## Budgets et reprise du moteur

Les budgets officiels des fonctions sont 1 CPU, 8192 Mio et 32 instances ; les attentes sont bornées à 128 globalement et 16 par fonction. Contrôle, stockage et validation sont exclus de ces réservations. Le moteur vérifie que les minima de toutes les fonctions actives tiennent ensemble. Les anciennes générations et nettoyages en attente restent comptés.

Le répertoire state/execution contient les canaux privés liés aux UUID de réservation. Ne pas supprimer manuellement ses entrées ni les lignes SQLite. Un redémarrage confirme la destruction de ses conteneurs/réseaux et la restitution des baux avant réouverture des admissions. Un appel interrompu n’est jamais rejoué automatiquement.

La campagne publique utilise la console SPARK locale pour réduire temporairement le plafond à deux, puis restaurer trente-deux et relire la valeur consommée. Ne pas éditer cette clé simultanément. Ses gardes sont restaurées sur fin de scénario, EOF ou délai ; les rapports exigent le nettoyage complet. HTTP/1.1 derrière le proxy peut attendre la fin d’un corps avant de transmettre le 408 déjà décidé ; HTTP/2 reçoit ce refus anticipé après trente secondes.

## Qualification de publication et maintenance du guide

`python3 -B e2e/execution-suite.py --scope publication` réunit les 18 campagnes du moteur et de la console sans doublons. Les 312 groupes passent avec les mêmes sources et image. Les rapports frais, la revue visuelle et les ressources restantes sont recoupés dans `docs/evidence/publication-console-dev-2026-11-07.json`. Les 18 campagnes ont terminé à zéro ; l’enveloppe de lancement a renvoyé 143 après le rapport atomique complet. Cette anomalie de cause inconnue est conservée dans la preuve avec la collecte indépendante réussie des rapports, sources, image et nettoyages.

`publication-cleanup-fault.py` refuse temporairement l’ouverture du parent d’une seule révision inactive possédée par sa campagne. Il vérifie l’inode, les permissions et le refus EACCES réel dans Docker. Une garde systemd indépendante restaure le mode après interruption ; le test confirme ensuite la maintenance normale. Ne pas lancer une autre campagne ni redémarrer le contrôle sous cette faute. Le scénario de confirmation de stockage suspend l’agent réel pendant l’expiration de confirmation, puis vérifie sa reprise avant tout nettoyage.

Maintenir `docs/manual.md` dans le même changement que chaque comportement utilisateur. Le build de console l’embarque directement, avec son empreinte ; le navigateur doit retrouver ses chapitres, paragraphes et tableaux. Les trois notes de cellule sont maintenues dans `qualification/spark-notes/`, proposées par les fichiers `.?`, appliquées par la console SPARK puis relues.
