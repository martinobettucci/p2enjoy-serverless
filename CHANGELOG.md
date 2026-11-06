# Changelog

## [Non publié]

- Règle de nommage obligatoire dans le contrat local : rôle réel et usage
  compréhensibles, vocabulaire cohérent et qualificatifs justifiés ; lien
  depuis le README pour les prochains développements et leurs revues.

- Noms Docker explicites `serverless-api` et `serverless-runtime-reference`,
  avec conservation des volumes, de l’identité et des objets de la base.
- Entrée `https://serverless.lelabs.tech` appliquée dans la configuration SPARK ;
  clients E2E, documentation et trois notes de cellule actualisés. Persistance
  et reprise réelles, 38 tests HTTP, neuf contrôles navigateur, huit groupes
  HTTPS, quatre chemins réseau et quatorze contrôles CLI réussis. Connexion
  SSO personnelle et accès administrateur confirmés sur le nouveau domaine.

- Agent local de stockage DEV : registre WAL, générations FUSE, baux durables,
  quotas data/cache, conservation, archivage, purge et vidage explicites.
  Canal Unix borné avec contrôle d’UID ; maintenance fermant les mutations.
- Installation d’un paquet root immuable et de son unité systemd dans le SPARK.
  Corrections issues des preuves réelles : équité du verrou de surveillance
  à 64 montages et déplacement des répertoires en mode 000 avant suppression.
  Quinze groupes de cycle, huit de limites et 31 régressions FUSE réussis,
  zéro échec/skip et ressources nettoyées. Raccordement au pilote, API/UI et
  preuves d’interruptions intermédiaires ouverts.

- Pilote d’instances Docker chaudes avec enfant Node neuf, canal privé,
  deadlines monotones, réponses bornées, logs expurgés et mesures Docker.
  Récolte des descendants, fermeture coordonnée et nettoyage confirmé/reprenable.
- 31 contrôles réels d’invocation et 11 contrôles de cycle de vie réussis,
  avec les 36 régressions du chargeur partagé. Gros corps, OOM, PIDs, signaux,
  résultat tardif après suspension du contrôle et courses réellement exercés.
  Admission, volumes par fonction et passerelle authentifiée restent à intégrer.

- Commande CLI deploy : cible HTTPS vérifiée, pagination, conservation des UUID,
  packaging avant mutation, publications en série et rapport des résultats
  partiels ou inconnus sans rejeu automatique. Valeurs résolues en mémoire.
- 14 contrôles réels de prérequis et de refus HTTPS, plus 24 scénarios
  plan/package rejoués dans les nouvelles images. Client authentifié ajouté
  pour pagination, publications successives et reprise de brouillon ; sa
  qualification reste en échec de prérequis SSO.

- Routes DEV de préparation, upload ZIP, validation Node, publication atomique,
  historique, rollback et suppression des révisions inactives. Migration 003,
  relecture des droits/versions au commit, verrou d’état et réservations
  conservées jusqu’au nettoyage confirmé.
- Huit groupes HTTPS publics et trente scénarios réels de démarrage/panne
  réussis sur la nouvelle image, dont exclusivité et reprise SQLite. Client
  de publication ajouté ; sa campagne reste en échec de prérequis sans session
  SSO réelle. Vues de révisions et invocation restent à réaliser.

- Extraction ZIP serveur bornée : tailles réelles, cohérence des en-têtes,
  CRC, refus des liens et publication readonly sans écrasement. Correction
  du drainage DEFLATE et borne de lecture du hash d'entrée.
- 112 contrôles réels sur le SPARK DEV, incluant les limites de volume,
  20 000 fichiers, saturation disque, courses et les douze archives du
  packager chargées par Node. Intégration aux API de révision encore en cours.

- Contrat OIDC du client DEV créé conservé dans le dépôt et rapproché du code.
  La campagne publique ajoute la découverte et les clés asymétriques réelles ;
  les points d'attente de rôle, azp ID token et rotation restent dans SLS-020.

- Chargeur Node 24 CJS/ESM et validation Docker avec transport Unix readonly,
  configuration applicative privée, logs expurgés et délai extérieur de quinze
  secondes. 36 scénarios E2E réels, dont dépendances, imports bloqués, limites,
  secrets recoupés, données binaires et destruction des descendants.
- Correction de confinement du canal, de troncature des secrets et de fermeture
  des connexions partielles. Intégration aux révisions encore en cours.

- Première CLI d'adaptation YAML et de packaging ZIP, avec héritage explicite,
  descripteurs sans valeurs de configuration, inventaires SHA256, chemins bornés
  et publication des fichiers par descripteurs de répertoire.
- Manifeste plateforme des douze fonctions de qualification ; 24 scénarios CLI
  réels sur le SPARK, dans une image installée avec dépendances à empreintes.
  Upload et publication encore en développement.

- Checkpoint DEV du contrôle Python/SQLite et de la console React : parcours
  SSO réel, modèles de gestion, sessions/CSRF, jetons CRUD et formulaires.
  Qualification administrateur encore ouverte ; moteur et adaptateur à venir.
- Preuves publiques et navigateur, provenance réseau, limites SSO persistantes,
  pannes réelles de configuration/SQLite et interruption du client de preuve.
  Refus HTML conservant leur statut, journaux expurgés et rapports incomplets
  invalidés dès le démarrage. Dépendances verrouillées auditées sans avis connu.

- Stockage FUSE à quota logique : réservations avant extension, fichiers et
  répertoires ouverts après suppression comptés, refus des mutations hors
  contrat, verrou exclusif et conservation des fichiers natifs.
- Campagne DEV de 31 contrôles réels de stockage, Docker rootless, saturation,
  concurrence, arrêt brutal, remontage et configurations refusées.

- Contrat de plateforme et découpage SLS-010 à SLS-060 : identité, objets,
  adaptation YAML, moteur Docker, stockage, exploitation et console.

- Méthode software-factory-base importée : contrats, rôles Codex/Claude, hooks,
  scripts et campagne Git réelle. Formation et workflow pédagogique exclus.
- Hooks standard activés dans le dépôt Git initialisé par le responsable.
- Campagne E2E élargie aux bornes, refus, saturation réelle, logs, arrêt actif,
  reprise du worker, manifestes invalides et défauts réels de disque/processus.
- Corps métier limités aux objets JSON ; lancement du handler signalé après
  chargement ; garde d'arrêt avant création d'un enfant ; délais HTTP observés.

- Cadrage et spécification du service de qualification indépendant QLF-001.
- Application synthétique dans `qualification/` : douze handlers, manifeste,
  exécuteur de référence, Docker et commandes DEV.
- Qualification convertie en parcours E2E sur le conteneur réellement déployé,
  sans mock ni appel direct aux handlers depuis le client HTTP.
- Compteurs, caches et jobs nommés manipulés par HTTP ; calcul réel et reprise
  du worker ; propagation des erreurs de pairs réels.
- Authentification par marqueur public retirée ; secret de cellule requis pour
  le parcours positif du handler business ; secrets désormais configurés dans
  le seul Spark DEV via le contrat normal de la console. Aucun test ignoré.

## [Publié]

_Aucune version de production publiée._
