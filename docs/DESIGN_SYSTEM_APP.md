# Design system du produit

## Statut

Le socle global est importé dans `DESIGN_SYSTEM.md`. La console de gestion
SLS-020 est déployée en DEV. Les 11 parcours de gestion passent, et leurs
sept captures desktop/mobile ont été relues le 6 novembre 2026.

## Périmètre confirmé

La future console gérera namespaces, services, fonctions, jetons CRUD,
variables et secrets, allocations, mémoire, stockage par identifiant,
durée d'invocation et extinction des instances. Elle utilisera le SSO du
domaine et le rôle administrateur. Les règles d'origine web et d'IP seront
visibles dans la configuration des services et appliquées côté serveur.

## Console SLS-020

L'accueil public présente une carte de connexion autonome (§6.17 du socle),
le nom P2Enjoy Serverless et l'action « Se connecter avec le SSO ». Une erreur
SSO apparaît à côté de cette action. Le profil authentifié porte son nom et
la déconnexion ; les jetons OAuth restent hors de l'interface.

Une barre latérale donne accès aux namespaces. Chaque namespace ouvre une
destination partageable qui liste ses services. Le service ouvert présente
ses facettes par liens : Fonctions, Configuration, Jetons et Activité.
La fonction possède une destination propre, avec sections Identité, Exécution,
Stockage et Configuration. Tant qu'aucune révision n'est active, son état
affiché est « Brouillon ». Aucun bouton d'invocation ou de déploiement n'est
affiché avant que l'opération existe.

Les listes ont les états chargement, vide, erreur et chargé ; les commandes
de pagination affichent leur page. L'identité se modifie en mode édition
explicite (§6.5) ; les sections se modifient dans un dialog natif (§6.27).
Les erreurs conservent la saisie. Annuler des modifications ouvre une
confirmation dans le même dialog. Suppression, révocation, rotation et
déconnexion demandent une confirmation dans le flux qui nomme leur portée.

Les valeurs de secrets sont saisies par champs password, jamais relues.
La configuration affiche leurs noms. Un jeton créé ou renouvelé est montré
une seule fois dans la section, avec copie et fermeture explicites. Il ne
rejoint ni localStorage ni sessionStorage ; après fermeture, seule sa liste
expurgée persiste. Les droits CRUD et la portée sont visibles avant création.

Tokens de dimensions locaux : navigation 240 px, contenu maximal 1280 px,
carte de connexion 448 px et dialog 640 px. Ces largeurs bornent les surfaces ;
les espacements intérieurs utilisent l'échelle du socle. Sous 1024 px la
navigation devient un tiroir à libellés ; sous 768 px les dialogs occupent
l'écran et les sections s'empilent. Les tableaux défilent localement avec une
indication de débordement. Icônes Lucide, favicon SVG propre au produit.

La [preuve de gestion](evidence/control-management-dev-2026-11-06.json)
conserve les empreintes des sept captures initiales et des ressources servies.
Le raccordement du stockage est aussi vérifié par les onze parcours de console ;
ses sept nouvelles captures JPEG sont relues, avec le quota réellement appliqué,
les états vides, les noms longs, le conflit conservant la saisie et les jetons.
Leurs empreintes figurent dans la [preuve de stockage](evidence/function-storage-dev-2026-11-06.json).
Les captures restent sous `.local/e2e/`. Le nom maximal est vérifié à 390 px,
avec `scrollWidth <= innerWidth`, depuis la création dans la console.

## Noms longs dans la navigation

Le fil d’Ariane conserve les noms complets des namespaces, services et
fonctions, y compris leur longueur maximale de 63 caractères. Ses segments
se réduisent à la largeur disponible et leurs mots longs reviennent à la ligne.
La page ne défile pas horizontalement, conformément au §8 du socle ; aucun
nom n’est masqué pour obtenir ce résultat. La campagne du contrôle mesure
le rendu à 390 px depuis la création d’un namespace par la vraie console.

## Focus du menu mobile

L’ouverture rend le contenu principal inerte et place le focus sur « Fermer
le menu ». La fermeture par Échap, bouton ou fond retire cet état inerte avant
de rendre le focus au bouton « Menu ». Un passage au palier desktop ferme le
tiroir et place le focus sur le lien de navigation visible. La fermeture
rétablit aussi le défilement de la page ; elle ne laisse pas le focus sur un
contrôle masqué.

La campagne de régression du moteur rejoue ces onze parcours et renouvelle
les sept captures, relues sans modification des ressources web. La
[preuve du moteur](evidence/execution-dev-2026-11-06.json) conserve leurs
empreintes et les états inspectés. Les facettes d’exécution sont livrées
dans SLS-061 ci-dessous.

## Consultation des exécutions SLS-061

Contrat réalisé : [CONSOLE_EXECUTION](CONSOLE_EXECUTION.md). La fiche de
fonction répartit Configuration, Instances et Invocations par liens partageables.
Les listes sont bornées à cinq éléments et les détails de journal se déplient
dans le flux. Les états, inconnues, focus et mesures suivent les §§6.13, 6.27
et 14 du socle ; aucune modale n’est ouverte pour une simple lecture.

La [preuve de console](evidence/console-execution-dev-2026-11-07.json) lie 25
captures relues à leurs SHA256 : douze nouvelles vues examinées par le principal,
sept vues de gestion et six de connexion examinées par le vérificateur. Le
nom maximal, les mesures partielles, les journaux longs et les états d’erreur
sont lisibles ; la capture mobile du namespace montre encore le chargement.
Les captures pleine page dépassant le viewport distinguent cette extension
du rendu effectif du voile de modale.

## Manuel d’usage SLS-062

Le [contrat du manuel](CONSOLE_MANUAL.md) ajoute une destination de lecture dans
la navigation principale. Le texte est borné à 72ch pour la lisibilité ; le sommaire
utilise la largeur de navigation de 240 px sur desktop et s’empile avant le guide
sous 1024 px. Titres ancrés et focus explicite suivent les §§5.1, 9 et 1.5 bis
du socle. Le contenu est généré depuis `docs/manual.md` lors de la construction.
Implémentation et captures restent à qualifier.
