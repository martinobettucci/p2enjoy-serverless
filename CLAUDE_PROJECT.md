# Contrat local

- Lire le README racine et celui du premier sous-dossier concerné avant agir.
- Ne jamais lancer de profil PREPROD ou PROD, même pour une qualification.
- John Dalia est exclusivement une référence : ne modifier, copier ou déployer
  aucun code, configuration, donnée ou secret du client. Les fixtures sont
  originales, synthétiques et conservées dans ce dépôt.
- La seule cible distante autorisée est le SPARK DEV décrit dans
  `docs/dev-spark.md`. La FORGE ne sert que de rebond SSH : aucune commande
  d'administration, modification de route ou autre opération sur elle.
- Appliquer le contrat de configuration et les propositions `.?` du SPARK.
- Un seul build, test ou scénario à la fois ; attendre sa fin complète.
- Aucun mock, stub, faux serveur, interception réseau ou remplacement d'une
  dépendance. Toute fonctionnalité testée doit l'être E2E sur le vrai code
  effectivement déployé. Le client de test ne démarre pas son propre serveur
  applicatif et n'importe pas les handlers pour contourner l'entrée HTTP.
- Toutes les fonctionnalités livrées doivent être testées E2E. Aucun skip ni
  succès conditionnel : un prérequis absent fait échouer la campagne. Les
  parcours positifs, refus, limites et cycles de vie font partie de la preuve.
- Cette instruction utilisateur remplace les tests unitaires obligatoires et
  les mocks parfois autorisés par le contrat global. Les contrôles statiques
  restent distincts des preuves fonctionnelles.
- L'agent principal est le seul écrivain. Les délégations de revue sont en
  lecture seule, sans lancement de tests ni opération distante.
- Aucun résultat du banc ne prouve la compatibilité complète du client ni une
  fonction de plateforme qui n'existe pas encore.

## Nommage obligatoire

Tout nom décrit la fonction réelle de l’élément et son usage. Une personne
qui découvre le projet doit comprendre ce qu’il fait en lisant son nom,
sans explication orale ni connaissance de l’historique de développement.
Cette règle s’applique aux conteneurs, images, services, domaines, ressources,
répertoires, fichiers, fonctions de code, variables et libellés d’interface.

- Nommer d’abord la responsabilité : API, runtime, agent de stockage,
  client de tests, délai maximal d’exécution, délai d’arrêt après inactivité.
- Distinguer le composant qui exécute une fonction du client qui le teste.
  Un runtime ne s’appelle pas « tests » parce qu’il sert à la qualification.
- Employer des termes précis et cohérents entre le code, Docker, la console
  et la documentation. Éviter les noms arbitraires, abréviations inventées,
  mots vagues et empilements de préfixes ou suffixes.
- Ajouter un qualificatif d’usage ou d’environnement seulement s’il distingue
  réellement deux éléments. Ne pas ajouter systématiquement « dev », « test »
  ou « qualification » ; `lelabs.tech` indique déjà l’infrastructure de
  développement, d’où `serverless.lelabs.tech`.
- Un identifiant technique nécessaire à l’unicité complète le nom descriptif ;
  il ne remplace pas l’indication du rôle dans les vues d’exploitation.
- Vérifier le nom avant chaque création ou modification et lors de la revue.
  Corriger un nom ambigu avant livraison ; un commentaire explicatif ne suffit
  pas à rendre acceptable un nom trompeur.

Exemples : `serverless-api` pour l’API et la console, `serverless-runtime`
pour le moteur d’exécution, `serverless-storage-agent` pour l’agent de stockage ;
`max_execution_seconds` et `idle_shutdown_seconds` distinguent deux délais
qu’un nom générique comme `timeout` confondrait.

## Application de la méthode

Le manuel d’usage canonique est `docs/manual.md`. Toute modification d’un
comportement utilisateur met à jour ce document dans le même changement.
La console affiche le contenu généré depuis ce fichier à la construction,
selon `docs/CONSOLE_MANUAL.md` ; aucune copie éditoriale parallèle n’est maintenue.
La qualification recoupe son contenu et son empreinte avec l’application déployée.

La méthode est importée depuis `P2Enjoy/software-factory-base` ; provenance et
adaptations : `docs/METHODE.md`. La routine planifiée est inactive. Aucun
bootstrap de FORGE, démon local, contournement TLS ou lancement PREPROD/PROD
mentionné dans CloudWorker n'est applicable ici. Les opérations restent
limitées au SPARK DEV autorisé et à son contrat normal de configuration.
Les preuves Git utilisent des dépôts jetables locaux. Aucun remote du produit
n'est créé ni poussé implicitement. L'absence de remote est signalée.

La consigne de commits de la méthode s'applique avec l'identité configurée du
responsable. L'absence de remote n'autorise pas à en inventer un : la preuve
locale et le commit sont conservés, et l'absence de push est déclarée.
