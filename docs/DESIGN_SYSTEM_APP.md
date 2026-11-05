# Design system du produit

## Statut

Le socle global est importé dans `DESIGN_SYSTEM.md`. Aucune interface de
management n'est encore implémentée ni qualifiée visuellement.

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

Les captures de référence et mesures seront ajoutées après exécution des
parcours sur la vraie console DEV. Aucune validation visuelle n'est acquise.
