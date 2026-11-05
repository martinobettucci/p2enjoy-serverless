# Changelog

## [Non publié]

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
