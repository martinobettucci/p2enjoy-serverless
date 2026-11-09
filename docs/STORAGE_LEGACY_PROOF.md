# Qualification des archives antérieures au registre de stockage

Contrat de preuve SLS-065, lié à [CONSOLE_STORAGE](CONSOLE_STORAGE.md#preuves-attendues).
Ce banc reproduit un état réellement produit par une ancienne version, puis le
migre. Il ne fabrique aucune ligne SQL et ne remplace aucun composant applicatif.

## Versions et configuration

La version historique est exactement
`93f88e5c543be4ad41e4ca22d08cbedbabec73c5`. Son API crée et supprime les fonctions
sans registre agent. Son image est construite depuis son propre arbre Git :
contrôle, migrations 001–003, frontend et verrous de dépendances. Les dépendances
Python, l’authentification et le protocole de validation sont comparés avec la
version actuelle avant utilisation. L’image runtime officielle est conservée.
Les dépendances Python, l’authentification et les deux fichiers runtime sont
identiques. Le client Docker du validateur actuel ajoute seulement le paramètre
optionnel `max_bytes=LIMIT`, transmis à sa requête ; sa valeur par défaut et le
protocole de validation historique restent inchangés. Le banc vérifie exactement
cette différence et conserve les deux empreintes, sans qualifier les fichiers
entiers d’identiques.

Le passage ancien → actuel utilise l’image immuable du contrôle actuellement
déployé, qui applique normalement 004–007. L’ancienne API ne doit jamais voir la
base actuelle : ses INSERT sans liste de colonnes n’offrent pas de compatibilité
descendante. Aucun retour à l’ancien code après migration des données temporaires.

Le banc respecte les deux `env_file` officiels, sans fichier parallèle, surcharge
de variable, nouvelle route ni modification de FORGE. La route HTTPS existante
reste dirigée vers 18090. Une fenêtre d’indisponibilité du seul contrôle DEV est
autorisée pour cette qualification. Le conteneur temporaire a une identité
distincte, `serverless-api-archive-migration`, un projet Compose propre et une
image référencée par digest. L’original est conservé par son ID et son image,
sans modification de son tag ni de sa définition. L’exécuteur de référence reste
en fonctionnement.

## Fenêtre et conservation des données

Les trois répertoires officiels — contrôle/artefacts, stockage et canal agent —
sont conservés par renommage dans un espace privé de campagne situé hors d’eux.
Ils sont remplacés temporairement aux mêmes chemins par des répertoires neufs
0700 appartenant à `spark-docker`. L’agent utilise son unité et son paquet protégés
existants ; aucun installateur ni configuration de service n’est modifié.

Avant le premier déplacement, le banc :

1. confirme la cible DEV, les chemins absolus distincts et non imbriqués, sans
   liens symboliques, et la possibilité de renommage dans le même système de fichiers ;
2. vérifie l’absence d’invocations, de fonctions actives, de candidats actifs,
   d’instances, d’intentions, de baux, de montages FUSE, de sondes et de conteneurs
   consommateurs de l’installation ;
3. arrête effectivement le contrôle original puis l’agent, et refait les contrôles
   de référence avant tout déplacement ;
4. conserve une sauvegarde SQLite native sous propriétaire, les empreintes logiques
   des registres et l’inventaire des artefacts, sans sortir leurs contenus ;
5. arme une restauration indépendante et enregistre les identités `(st_dev, st_ino)`,
   propriétaires, modes et emplacements de chaque répertoire.

Les étapes ne sont pas considérées atomiques. Le journal privé et les identités
permettent de retrouver chaque original, qu’il soit encore en place ou déjà à
l’abri. La garde joint le pilote et ses commandes bornées avant de restaurer.
Elle retire le contrôle temporaire et ses seuls validateurs identifiés par son
UUID d’installation, arrête l’agent, confirme l’absence de références, puis
rétablit les trois originaux avant tout redémarrage. Elle relance d’abord l’agent,
puis le contrôle original par son ID. Le contrôle historique ne peut plus être
relancé après cette restauration.

La garde couvre la perte de SSH, la mort du pilote et les déplacements partiels.
Sa branche indépendante est exercée par interruption réelle après le premier
renommage. Elle ne revendique pas une preuve de redémarrage complet du SPARK.
Le journal de reprise reste sur disque, hors des répertoires déplacés ; la
restauration opérateur conserve le même contrôle d’identité.

## Parcours réel

Une nouvelle connexion SSO normale crée la session du contrôle historique. Les
identifiants restent transitoires ; aucun secret ni cookie ne figure dans les
rapports. Le pilote crée deux fonctions originales avec `min_instances=0` et
les deux volumes désactivés. Chaque fonction reçoit un vrai ZIP préparé par
l’adaptateur et chargé dans Docker, puis est supprimée par l’ancienne API.

La préparation historique utilise `/api/functions/{id}/deployments` avec config,
configuration et événements, puis PUT de l’archive. Le serveur génère l’UUID.
La preuve exige publication, validation réussie et conteneur retiré avant DELETE.
Elle vérifie le schéma 001–003 et l’absence des fonctions dans le vrai registre agent.

Après bascule vers l’image actuelle, la même base et la même clé conservent la
session, les UUID et les révisions. Les sept migrations sont constatées, puis
`/api/session` confirme l’authentification. Les archives contiennent du code réel
et exposent `storage.registered=false`, distinct d’un registre connu sans volumes.

- La première purge termine normalement avec `storage_absent=1`, artefacts retirés
  et compteurs libérés, sans reçu d’effacement agent inventé.
- La seconde purge est retenue par un refus réel de permissions sur son artefact.
  Le banc attend la décision commit, la phase artifacts et l’absence persistée.
  Il crée alors la ligne par le véritable protocole `configure` de l’agent, avec
  volumes désactivés, puis restaure les permissions. Le contrôle doit conserver
  le même reçu en attente avec `storage_state_changed`, sans adopter cette ligne,
  supprimer le code ni déclarer la purge terminée. Un redémarrage du contrôle
  temporaire doit conserver cette décision et ce diagnostic.

## Nettoyage et preuve finale

Le [complément de migration de purge 006](FUNCTION_VERSION_PURGE_UPGRADE.md)
réutilise cette fenêtre dans un mode distinct, l’image006 réellement conservée
et un namespace de responsabilité propre. Les modes `partial` et `historical`
ci-dessus restent inchangés. L’attente de leur upgrade reste une santé verte ;
seul le mode de purge dispose des observations natives de refus/rollback, de la
reprise006 avant commit007 et d’une attente API lisible pendant EACCES. Le
relâchement de permissions utilise un descripteur vérifié avec fchown en dernier.
Ce complément reste à qualifier ; la campagne003→007 doit être rejouée après
les extensions du helper.

La commande contradictoire reste volontairement non terminée. Elle n’est ni
abandonnée par SQL ni qualifiée de purge réussie. Son installation temporaire
entière est retirée après observation : propriétaires arrêtés, ressources Docker,
baux, montages et canaux propres absents, puis répertoires temporaires supprimés
après restauration des originaux. Aucune archive historique de l’installation
habituelle n’est purgée.

Le rapport distingue les groupes réussis de cet état produit attendu. Il exige
restauration complète, registres et artefacts originaux recoupés, même image et ID
de contrôle, agent et API sains, exécuteur de référence intact, configuration
officielle inchangée et gardes inactives. La qualification de l’unité reste ouverte
jusqu’aux régressions communes et à la mise à jour des notes SPARK.
