# Changelog

## [Non publié]

- Routes DEV de préparation, upload ZIP, validation Node, publication atomique,
  historique, rollback et suppression des révisions inactives. Migration 003,
  relecture des droits/versions au commit, verrou d’état et réservations
  conservées jusqu’au nettoyage confirmé.
- Huit groupes HTTPS publics et trente scénarios réels de démarrage/panne
  réussis sur la nouvelle image, dont exclusivité et reprise SQLite. Client
  de publication ajouté ; sa campagne reste en échec de prérequis sans session
  SSO réelle. CLI deploy, vues de révisions et invocation restent à réaliser.

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
