# Design system du produit

## Statut

Le socle global est importé dans `DESIGN_SYSTEM.md`. La console de gestion
SLS-020 est déployée en DEV. Les 11 parcours de gestion passent, et leurs
sept captures desktop/mobile ont été relues le 6 novembre 2026.

## Périmètre confirmé

La console gère namespaces, services, fonctions, jetons CRUD,
variables et secrets, allocations, mémoire, stockage par identifiant,
durée d'invocation et extinction des instances. Elle utilise le SSO du
domaine et le rôle administrateur. Les règles d'origine web et d'IP sont
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
La [preuve](evidence/manual-console-dev-2026-11-07.json) vérifie les neuf chapitres,
22 paragraphes et toutes les cellules du tableau depuis la source unique.
Huit captures du manuel et du tiroir sont relues par le principal ; les 25
captures de régression sont relues par les vérificateurs. Le titre est visible
dans les captures d’entrée desktop/tablette ; les chapitres visés par ancre
défilent dans la page. Le corps de texte agrandi est mesuré à 200 %, sans prétendre
modifier les titres en px ni mesurer le zoom global du navigateur.
La nouvelle capture des namespaces montre leur chargement ; celle du namespace
mobile montre désormais les services vides. Ces états sont nommés dans la preuve.

## Publication et révisions SLS-063

La facette **Code et révisions** suit [CONSOLE_PUBLICATION](CONSOLE_PUBLICATION.md).
L’édition ZIP/handler utilise le dialog natif existant et une confirmation nommant
la fonction et l’archive. Le suivi, les diagnostics et les détails de révision
restent dans le flux de la page. Les états serveur sont libellés en français ;
aucun pourcentage de progression n’est estimé. L’état d’envoi navigateur se
distingue du dernier état serveur observé.

Listes de cinq éléments, actions par révision et confirmations dans leur carte,
UUID et empreintes complets avec retour à la ligne, logs bornés avec défilement
local. L’action d’actualisation et sa date restent visibles. Les pages et erreurs
de lecture restent indépendantes du formulaire en cours. L’activation conserve
le focus dans la liste ; une suppression rend le focus à son titre si la carte
disparaît. Sur mobile, champs et actions s’empilent ; pas de débordement de page.

## Stockage et archives SLS-065

Console déployée, parcours qualifiés en DEV : [CONSOLE_STORAGE](CONSOLE_STORAGE.md#console-et-manuel).
Stockage devient une facette de fonction ; Archives de fonctions une destination
générale indépendante des parents supprimés. Listes de cinq, filtre et total
explicites. Dernières mesures, inconnues et allocations restent distinctes.
La confirmation de purge exige le nom exact ; celle de cache nomme sa portée
sans ressaisie. Suivi partageable sans rejeu au rechargement, noms/UUID complets,
états français et focus sur un élément encore monté, selon le socle global.

## Parcours d’efficacité et d’exploitation à réaliser

Le [contrat d’ergonomie](CONSOLE_USABILITY.md) couvre SLS-067 à SLS-073.
Le catalogue global de fonctions devient l’entrée opérationnelle ; namespaces
et services donnent leur contexte aux objets. La navigation principale conserve
des destinations nommées, dont favoris et monitoring. Les facettes de fonction
intègrent progressivement édition du code, client HTTP et journaux corrélés.
Ces changements sont planifiés ; l’accueil actuellement déployé reste celui
des namespaces.

Recherche et filtres appartiennent à la liste qu’ils affectent. Les liens
conservent leur contexte au retour d’une fiche. Favoris et sélection de masse
sont deux états distincts ; chacun possède libellé, état accessible et commandes
au clavier. Une sélection montre sa portée exacte avant toute action.

Les aperçus de renommage et résultats de lot utilisent des tableaux sémantiques,
avec anciens/nouveaux noms ou résultat par objet. La confirmation d’une
suppression nomme ses objets et effets. Le suivi d’une opération reste une
destination partageable ; une consultation ne rejoue pas la mutation.

L’éditeur distingue source déployée, brouillon et diff, avec commandes nommées
pour enregistrer puis publier. Le client HTTP indique la révision appelée et
le contexte navigateur/serveur ; la réponse ouvre ses journaux par corrélation.
Les graphes conservent unités, période, source et valeurs accessibles sous forme
textuelle. Mesure absente, zéro et collecte interrompue ont des états distincts.
Ces parcours appliquent les règles du socle sur clavier, focus, confirmations,
retour d’erreur, mobile et vérification visuelle.

## Versions par hash et pilote à réaliser

[SLS-074](FUNCTION_VERSIONS.md) complète la facette Code et révisions : hash
complet copiable avec retour à la ligne, cible courante et disponibilité de
chaque version en texte. Le résultat distingue code inchangé et nouvelle
version ; « Publier une version » et « Promouvoir cette version » sont deux
actions distinctes. Seule la promotion change la cible sans tag, après confirmation
nommant la fonction et le hash. Promotion/rollback, archivage/restauration
et suppression sont des actions distinctes par version, avec confirmations
dans le flux selon le socle. Les appels déjà admis et les pools d’autres versions
ne sont pas présentés comme ayant changé de code.

Le client HTTP propose cible courante ou hash explicite et montre la version
effectivement appelée. Ses exemples copiés conservent le tag choisi. Une version
indisponible affiche le refus réel sans substitution. Ces parcours restent
planifiés ; aucune commande absente du backend n’est ajoutée aux écrans actuels.

## Adresses d’appel SLS-066 en qualification

La facette **Adresses d’appel** suit [INVOCATION_URLS](INVOCATION_URLS.md).
Une destination partageable dans la fonction et un lien depuis sa ligne de
service rendent le catalogue découvrable. Cinq domaines par page ; méthodes,
adresses et exemples complets reviennent à la ligne. La copie confirme le
résultat natif du presse-papiers et conserve le texte sélectionnable en cas
de refus. Aucun jeton réel dans les exemples.

Chargement, source indisponible, absence de domaine applicable et brouillon
sont distincts. « HTTPS déclaré » / « HTTP déclaré » et « Disponibilité non
vérifiée » qualifient le relevé sans prétendre vérifier un certificat. Une
erreur ou nouvelle lecture retire les anciennes adresses et les succès de
copie. Pagination et actualisation conservent le focus sur un contrôle visible,
y compris après retrait du dernier domaine d’une page. Le parcours complet,
clavier, mobile à 390 px et refus de copie exigent des preuves réelles.

L’exemple curl préfère GET lorsqu’il existe. La redirection depuis un domaine
d’appel préserve les identifiants UUID de suivi de publication ou de stockage
des fiches ; elle n’efface pas le contexte déjà partageable de ces parcours.

Le [checkpoint DEV](evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
recoupe sept nouvelles captures de cette facette, sept de gestion, onze du
manuel et six PNG de connexion. Vingt images sont inspectées sur ce checkpoint ;
onze sont strictement identiques à la référence SLS-065 inspectée. Le chapitre
Adresses d’appel est aussi lu dans un vrai viewport mobile 390 × 844 après
navigation. Ces images ne couvrent pas encore plusieurs domaines, leur retrait,
la source inaccessible ou une seconde page.

La [régression complète](evidence/invocation-urls-regressions-dev-2026-11-08.json)
renouvelle 79 captures : sept de gestion, douze d’exécution, 22 de publication,
quatorze de stockage, sept d’adresses, onze du manuel et six de connexion.
Les vérificateurs observent 61 images ; les 18 autres sont strictement identiques
par SHA256 aux références inspectées. Les rapports et heures de génération
sont recoupés. Le manuel servi conserve ses 14 chapitres et 43 paragraphes.

Les captures d’exécution ne montrent pas la seconde page finalement chargée,
vérifiée par les assertions du parcours. Les vues après perte de réponse
montrent l’état relu ; elles ne prouvent pas seules la perte ou l’absence de
rejeu. Les vues sans session peuvent conserver la structure déjà chargée.
Le catalogue de stockage affiche aussi des archives historiques ; son total
ne représente pas les seules fonctions du replay. Les limites de routes,
source inaccessible et pagination du catalogue d’adresses restent ouvertes.
