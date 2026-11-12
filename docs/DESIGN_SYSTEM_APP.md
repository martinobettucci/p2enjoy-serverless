# Design system du produit

## APP-DS-002 — Composition de requête HTTP

SLS-071 suit [CONSOLE_TESTER](CONSOLE_TESTER.md). Sa facette Tester est un outil
éphémère avec destination propre, sections Destination/Requête/Accès/Réponse.
Les paramètres se composent sur place : ils ne modifient aucune configuration
enregistrée. Cet écart au §6.27 évite d'enfermer la requête à comparer avec sa
réponse dans une modale. Les jetons et la requête restent uniquement en mémoire.

Les composants Section/Field/Facts/Resource, les confirmations et tokens existants
sont réutilisés. Un envoi explicite nomme le contexte et la version ; l'arrêt
porte sur l'attente. Résultat, refus de la passerelle et issue inconnue sont
distincts. Corps monospace avec défilement local et aperçu64Kio, téléchargement
borné ; aucun rendu HTML actif. Champs et actions s'empilent sur mobile, noms,
hashes et URL restent entiers. Le lien de corrélation ouvre les détails et le
journal existants. Source indisponible retire les anciennes adresses et résultats.
La [première tranche43groupes](evidence/function-http-client-dev-2026-11-12.json)
recoupe27captures inspectées, dont cinq du testeur. Certaines ne cadrent qu’une
partie de la réponse. Le [complément46](evidence/function-http-client-ui-admission-dev-2026-11-12.json)
ajoute38images inspectées, dont16vues du testeur et du corps de son manuel :
clavier/tablette, refus CORS, annulation, gzip et messages périmés corrigés.
071.7 est qualifiée. La [preuve42](evidence/function-http-client-recovery-confidentiality-dev-2026-11-12.json)
ajoute27captures inspectées, dont cinq des délais, coupure, refus certain et
réponse après reprise. Le502 proxy après admission montre Issue inconnue ;
le vrai503 du contrôle avant émission conserve son alerte. Aucun nouveau
style ni composant n’est ajouté. Les critères071.1/.4/.5 sont qualifiés avec
leurs checkpoints propres. Le [complément32](evidence/function-http-client-token-loss-dev-2026-11-12.json)
recoupe dix vues ciblées de jetons et22régressions inspectées : confirmation
non confirmée conservée, absence de succès, listes vide/actif/révoqué et deux
vues mobiles lisibles. La dernière ligne d’une liste se poursuit verticalement.
071.3/.8 sont qualifiés ; source indisponible et exception de tâche gardent
l’unité ouverte.

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

<a id="serverless-identity"></a>
## Identité Serverless SLS-100 qualifiée en DEV

La marque suit [SLS-100](BACKLOG.md#sls-100) : trois blocs blancs reliés par deux
branches sur la pastille bleue P2Enjoy. Ils représentent les fonctions et leurs
relations. Les détails isométriques sont écartés pour la lisibilité du favicon.
`web/public/favicon.svg` est la source unique du favicon, de l'accueil et de la
navigation ; le texte P2Enjoy Serverless reste le libellé, l'image adjacente garde
son alt vide. Le fichier est autonome et sa route existante est servie no-store.

La [preuve DEV](evidence/application-icon-dev-2026-11-11.json) qualifie29groupes sur356sources
b1ee473 et l'image779aef7b :4 ciblés accueil/SSO/navigation/déconnexion en1440×1000
et390×844,8manuel,8publics et9connexion. Le backend34fichiers et les trois autres
ressources web sont strictement identiques ; seul le SVG change. Le manuel
textuel conserve ses16chapitres/56paragraphes, recoupés avec sa source.

Les26captures fraîches sont inspectées : quatre viewports dédiés par le principal,
16JPEG du guide et six PNG de connexion par le vérificateur ; le principal recoupe
également tablette, droits mobile et refus SSO. Marque lisible, états d'erreur et
limite contenus dans la carte, aucune coupure horizontale ni superposition
bloquante confirmée. Le tiroir mobile recouvre légitimement le contenu principal ;
la marque peut être hors cadrage dans une vue de guide déroulée ou menu fermé.
Le SSO externe conserve sa propre marque.

Le SVG réellement servi, recoupé par SHA, est aussi rendu à16/32/64px et inspecté
séparément : trois blocs identifiables, contraste blanc/bleu mesuré9,03:1.
Ces previews rasterisées sont des inspections d'asset, pas des captures applicatives.
Les interactions, le cache et les réponses réseau restent prouvés par leurs
assertions E2E ; les images seules ne les prouvent pas. Les captures historiques
restent conservées dans leur époque, avant ce changement de marque.

## Attente de droits SSO en qualification SLS-089

Le [contrat](SSO_SESSION_RECOVERY.md#attente-de-droits) réutilise la carte publique
448px, sa marque unique et ses espacements. L’attente porte un titre explicite,
un texte neutre et l’action **Vérifier mon accès**, sans alerte rouge ni navigation
d’administration. Elle ne consulte ni session ni CSRF, même ouverte manuellement
par un administrateur. La vérification technique temporairement indisponible
propose **Réessayer** ; sa branche 503 réelle n’est pas encore qualifiée.

La [preuve partielle DEV](evidence/sso-session-recovery-dev-2026-11-11.json) sur e81007c5 passe 33 groupes : 8 ciblés,
8 du manuel, 8 publics, 9 de connexion. 30 captures recoupées : 6 ciblées par le principal
(dont console après renouvellement identique par SHA à l’initiale), 24 ouvertes
individuellement par le vérificateur (16 JPEG manuel, 6 PNG connexion, 2 JPEG du
chapitre Se connecter). Les deux vues de chapitre ajoutent 0 groupe. Manuel servi :
16 chapitres et 57 paragraphes. Attente neutre lisible en 1440×1000 et 390×844, actions
visibles, aucun défaut visuel bloquant confirmé ; texte à 200 % et tableau contenus.
Les 6 PNG login n’ont pas de SHA déclaré dans leur rapport : leurs octets actuels
et mtime dans la phase sont recoupés séparément. Les autres JPEG correspondent
aux SHA déclarés. Aucune vue 503 réelle, aucun refus de profil sans rôle et aucune
rotation de signature ne sont prouvés par ces images. Les interactions restent
étayées par les assertions E2E. Les captures historiques gardent leur époque.

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
Le catalogue SLS-067 est qualifié en DEV avec l’accueil Fonctions ;
les autres changements restent planifiés.

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

## Versions par hash et pilote en qualification

[SLS-074](FUNCTION_VERSIONS.md) complète la facette Code et révisions : hash
complet copiable avec retour à la ligne, cible courante et disponibilité de
chaque version en texte. Le résultat distingue code inchangé et nouvelle
version ; « Publier une version » et « Promouvoir cette version » sont deux
actions distinctes. Seule la promotion change la cible sans tag, après confirmation
nommant la fonction et le hash. Promotion/rollback, archivage/restauration
et suppression sont des actions distinctes par version, avec confirmations
dans le flux selon le socle. Les appels déjà admis et les pools d’autres versions
ne sont pas présentés comme ayant changé de code.

Le client HTTP prévu par SLS-071 devra proposer cible courante ou hash explicite
et montrer la version effectivement appelée. La facette Adresses d’appel livre
déjà les URL épinglées et le refus sans substitution ; ses parcours008 sont
recoupés dans le checkpoint ciblé ci-dessous.

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
ne représente pas les seules fonctions du replay. Les limites de routes, source refusée et pagination du catalogue d’adresses
sont traitées par leurs compléments distincts ; les autres fautes restent ouvertes.

## Catalogue global SLS-067 qualifié

[FUNCTION_CATALOGUE](FUNCTION_CATALOGUE.md) ajoute Fonctions en tête de la
navigation, avec table sémantique, recherche et filtres locaux à la liste.
Les dialogues Namespace/Service recueillent un choix radio dans une collection
recherchée et paginée, avec un seul engagement Appliquer ; ils suivent le §6.27.
Les tableaux larges défilent dans leur conteneur, les noms complets reviennent
à la ligne. Les états chargement/vide/erreur, les totaux, la page et le focus
sont explicites. La query de retour accompagne les liens des six facettes.
API et console sont construites, déployées et qualifiées en DEV. Les preuves
antérieures décrivent encore leur accueil Namespaces historique.

La table conserve une largeur minimale locale de 720 px, exprimée par
`--size-catalogue-table`, pour ses six colonnes ; les noms reviennent à la ligne
et le défilement reste dans la table sur mobile, sans élargir la page.

Le checkpoint initial de quatorze images reste distinct de la preuve active.
La [qualification](evidence/function-catalogue-dev-2026-11-08.json) retient
37 campagnes uniques / 489 groupes, six prérequis et deux époques de clients
sur les mêmes sources produit/images. Les 98 images actives sont inspectées
individuellement : sept de gestion, six de connexion, douze d’exécution,
22 de publication, quatorze du manuel, sept d’adresses, seize de catalogue et
quatorze de stockage. Le manuel servi correspond à 15 chapitres / 46 paragraphes.

Les seize vues du catalogue comprennent huit vrais viewports, dont la table
mobile à gauche, au milieu et à droite. Elles montrent les six colonnes lisibles
à ces positions successives, et le dialog plein écran sans contrôle recouvert.
Les autres colonnes partiellement recoupées aux bords ne sont pas présentées
comme simultanément lisibles. Le contexte de retour et la page recalée après
suppression relèvent aussi des assertions, car la pagination peut être sous
le viewport d’une capture. Les images ne remplacent pas les preuves d’interaction,
de réseau, de droits ou de nettoyage. Les vues après refus peuvent garder le
cadre précédemment chargé ; les mesures absentes restent distinctes des zéros.

Aucun défaut visuel bloquant confirmé. La fiche d’archive Purgée porte encore
le titre Archives conservées ; cette remarque mineure est suivie dans SLS-075.
Les totaux d’archives incluent l’historique et ne représentent pas seulement
les jeux de cette preuve. Les modes pilote et versions par hash sont en qualification008.

## Identité du code dans les révisions

Le [registre SLS-074](FUNCTION_VERSION_REGISTRY.md#console-et-manuel) ajoute à la
carte existante une donnée Facts « Hash du code » complète, police mono avec
retour à la ligne natif, et le bouton texte/icône Lucide « Copier le hash du
code ». Success et ErrorMessage portent le résultat du vrai presse-papiers.
Le texte reste sélectionnable après refus. Le résultat appartient à l’observation
courante : relecture, changement de page ou de facette le retire. Aucun token
visuel nouveau ni exception au socle. La
[preuve du registre](evidence/function-version-registry-dev-2026-11-09.json)
recoupe69 captures fraîches :47 nouvelles images inspectées et 22 identités SHA
avec des références inspectées. Les six images ciblées du hash montrent copie,
refus natif et reprise, dont deux vrais viewports relus aussi par le principal.
Les captures du manuel cadrent directement le paragraphe sur desktop/mobile ;
son contenu servi correspond à 15 chapitres et 47 paragraphes. Les pertes de
réponse, les droits, le nettoyage et le presse-papiers exact restent des preuves
d’assertions ; les images pleines pages prolongent leur viewport. Aucun défaut
visuel bloquant confirmé. Cette preuve007 reste historique ; promotion, déduplication et appels par hash
sont désormais déployés pour qualification dans la suite de SLS-074.

## Publication et sélection par hash en qualification

L’image008 DEV suit [FUNCTION_VERSION_EXECUTION](FUNCTION_VERSION_EXECUTION.md).
Les cartes sont groupées par hash, paginées par cinq côté serveur, avec cible par
défaut, disponibilité et date initiale. Les UUID d’alias restent dans les
métadonnées. Les commandes nomment leur version et leur fonction. Promotion et
archivage/suppression se confirment dans le flux ; restauration simple suit
le §6.24. Une promotion emploie le bouton primaire, la suppression le destructif.

Retirer la cible courante ouvre un dialog limité à son remplacement : hash
disponible à saisir ou désactivation explicite, puis confirmation. Réimporter
une version supprimée ouvre le dialog ZIP/handler associé au hash et aux
événements conservés. Les refus de préparation et de mutation conservent saisie
et confirmation ; les erreurs d’upload après prise en charge restent dans le
suivi de tentative. Les cartes
stables ne sont pas remontées à chaque lecture, mais le retour de copie l’est.

Chaque carte disponible mène à ses adresses versionnées, avec sélection dans
la query partageable. La facette nomme hash sélectionné et cible courante ; un
lien explicite retrouve la cible par défaut. Les sélections invalides donnent
leur refus, y compris après redirection canonique depuis un alias de domaine.
Instances et invocations montrent hash demandé/résolu et alias technique réel.
Le [checkpoint ciblé008](evidence/function-version-execution-checkpoint-dev-2026-11-09.json)
passe six groupes UI et huit du manuel. Les28 JPEG sont inspectés : desktop,
mobile390px, tablette et corps agrandi200%. Les refus409/404 conservent
confirmation, saisie et focus ; le dialog garde son hash quand sa carte quitte
la page. Les messages nouvelle/réutilisée/réimportée et le presse-papiers sont
recoupés avec leurs effets réels. Aucune superposition bloquante ni débordement
horizontal observé. Les listes longues exigent un défilement vertical ; les
captures pleines pages complètent leurs viewports. Les pannes et régressions
complètes restent ouvertes.

Le catalogue est lu après le candidat suivi et avant la confirmation finale de
la fonction. Une publication de code seul n’ayant pas d’effet sur l’ETag parent,
cet ordre empêche l’arrêt du polling sur une liste antérieure au candidat publié.
Le hash demandé d’une réimportation reste lisible dans son suivi, même en échec.
Après refus, la commande de correction reçoit le focus une fois redevenue
disponible. Une désactivation temporaire ne laisse pas le clavier sur le body ;
la confirmation dans le flux attend aussi la levée du fieldset désactivé.


## Deux pages réelles des domaines — qualification008

La [preuve six domaines](evidence/invocation-pagination-dev-2026-11-09.json)
recoupe trois groupes UI depuis l’accueil : formulaires, vraie publication puis
promotion explicite, cinq domaines et le sixième sur la seconde page. Les copies
natives sont invoquées, la sélection par hash reste présente sur les deux pages
mobiles et le focus revient au titre après navigation clavier. Les deux boutons
restent présents, désactivés à leurs extrémités.

Les sept JPEG sont inspectés personnellement : première/seconde page desktop,
pagination dans son viewport1440×1000, première/seconde page mobile390px et deux
viewports390×844. Ces deux derniers fichiers sont identiques par SHA. Les noms,
hash et URL complets reviennent à la ligne sans élargir la page ; les pleines
pages prolongent leur viewport et les listes demandent un défilement vertical.
La première page mobile mesure3733px de haut ; elle n’est pas présentée comme
simultanément visible. Aucun défaut visuel bloquant constaté. Les images ne
prouvent pas seules les copies, appels, droits, pertes ou nettoyages : leurs
assertions et reçus natifs restent dans la preuve. Les anciennes captures
citées plus haut conservent leur périmètre historique.

## Planifications du manifeste SLS-078

La facette **Planifications** est une destination de lecture de la fonction,
selon [SCHEDULES](SCHEDULES.md#facette-planifications). Elle compose les sections,
Facts, badges, états Resource et pagination existants ; aucun token ni écart
nouveau. Les états de tir portent un libellé français, les créneaux et frontières
portent UTC, les empreintes complètes restent sélectionnables et reviennent à la
ligne. Les listes d'historique ont cinq éléments et restaurent le focus au titre
après changement de page. Les preuves sont détaillées ci-dessous.
Chargement et erreur retirent aussi le total et le rang affichés ; Réessayer
conserve la page demandée en interne et la présente après une lecture réussie.

Le [checkpoint du10 novembre](evidence/schedules-checkpoint-dev-2026-11-10.json)
recoupe cinq JPEG de la facette et seize du manuel, tous inspectés. Desktop et
mobile390px : noms et hash lisibles avec retour à la ligne, états nommés et pas
de débordement mesuré. Les deux captures desktop de la facette ont le même cadrage ;
la lecture de l'historique mobile nécessite son défilement. Les fenêtres réelles
et le presse-papiers ne sont pas déduits des images. États vides, erreurs, longs
noms et seconde page sont qualifiés dans le complément ci-dessous. Le guide sert16 chapitres et
56 paragraphes ; tablette et corps de texte200% sont aussi inspectés.


## Deux pages et reprise des planifications qualifiées

Le [complément](evidence/schedule-console-dev-2026-11-10.json) recoupe31 images :
17 inspections personnelles (12 console, trois manuel ciblé, deux autres vues
du guide) et14 identités SHA avec le checkpoint inspecté. Deux pages réelles5+1,
nom63, expressions et hashes complets, focus au titre et commandes aux extrémités.
Le vrai401 retire aussi la pagination ; Réessayer retrouve la page demandée.
Desktop et390px restent sans débordement mesuré ni superposition bloquante.
Les pleines pages prolongent leur viewport : mobiles7135/4568px ; leurs éléments
fixes sont à la position de capture, pas simultanément visibles dans l'usage.
Les vues de navigation dans leur viewport recoupent la disposition réelle.
L'image après reprise montre les premières déclarations ; le rang2 et son unique
tir sont recoupés par assertions. Le paragraphe du manuel se poursuit verticalement
sur mobile. Aucun défaut visuel bloquant confirmé. Nouvelle imagec59b8616 ; guide
conforme16 chapitres/56 paragraphes. Les preuves antérieures gardent leur époque.

## APP-DS-001 — Édition de source sur place, prévue pour SLS-070

Décision du11 novembre2026 avant code ; socle§6.27. La facette Éditeur possède
une destination propre et distingue source, brouillon enregistré et saisies.
L'édition explicite d'un fichier s'effectue sur place pour conserver son
arborescence et sa comparaison ; enfermer le code dans une modale retirerait
ce contexte et comprimerait inutilement le travail. Le mode lecture précède
Modifier, puis Enregistrer le brouillon. L'ajout, le handler et l'abandon
réutilisent les dialogs et confirmations existants. Aucun formulaire général
permanent ne mélange ces saisies avec les valeurs de production.

Le [contrat](CONSOLE_EDITOR.md) fixe les états, bornes et gestes. Bureau :
arborescence et fichier/diff ; mobile : sections empilées, code défilant dans
sa surface, noms complets repliés dans le contexte. Police mono, tokens et
composants existants, focus conservé, recherche nommée et sélection de résultat.
La limite et la taille du fichier sont explicites ; binaire et hors limite ne
se présentent pas comme un texte vide. Les modifications non enregistrées
demandent un choix avant départ, sans effacer la saisie sur refus. Preuves et
captures à produire ; aucune qualification visuelle revendiquée à ce stade.

### Facette Éditeur — réalisation UI prévue

Le détail est dans [CONSOLE_EDITOR](CONSOLE_EDITOR.md#détail-de-la-facette-console--12novembre2026-avant-code).
L’écart APP-DS-001 conserve lecture puis édition sur place. Sections séparées,
arborescence240px et hauteur de lecture26rem (token local de composant), puis
empilement sous1024px. Ces dimensions donnent une zone de code lisible sans
comprimer la navigation ; elles ne modifient pas l’échelle d’espacement.
Recherches nommées, occurrence sélectionnée, compteur UTF-8 et état de saisie
restent près du fichier. Les textes binaires/hors limite n’ont pas de faux
éditeur vide. Une garde native unique protège le départ ; beforeunload conserve
son avertissement navigateur. Les refus et conflits gardent les saisies.
Les captures et preuves de cette facette restent à produire.

### Compléments de console à qualifier

Le [contrat](CODE_EDITOR_CONSOLE_EXTENSIONS.md) exige deux pages de choix de
source et de diff, avec hash/état complets, archive sélectionnable et version
supprimée désactivée. L’adoption conservant la saisie confirme sa portée locale,
sans prétendre enregistrer le texte. La pagination de source rend le focus au
titre **Versions de la fonction** ; celle du diff doit le rendre à **Comparer
le brouillon enregistré**, selon les §§9.5/14.3 du socle. La disparition de ses
commandes pendant lecture rend nécessaire ce point d’ancrage. Le parcours réel
doit d’abord reproduire l’absence éventuelle de restitution ; aucune correction
ni qualification visuelle de ce complément n’était revendiquée avant le passage.

Le [passage échoué](evidence/code-editor-console-focus-failed-dev-2026-11-12.json)
reproduit quatre focusBODY. Ses25JPEG sont inspectés : seconde page de sources
avec archive/supprimée, archive lue, texte local conservé après adoption et
diff5+2 desktop/mobile lisibles. Les images seules ne prouvent ni le focus ni
l’absence dePUT, recoupés par leurs observations. Deux cadrages de pagination
sont aussi ouverts par le principal ; leur titre est hors champ supérieur,
ce qui ne permet aucune déduction d’élément actif.17groupes passent dans cet
échec mais zéro groupe n’est qualifié. Les vues pleines pages prolongent leur
viewport ; aucun autre défaut bloquant n’est constaté.

La correction réutilise `Section.headingRef` et un h3 de détail : titre de
comparaison après page/retry, chemin reçu après ouverture de détail, repli au
titre en cas de refus. L’intention appartient à la seule génération encore
valide, après rendu ; changer surface/brouillon l’annule. Le correctif et ses
captures focalisées restent à qualifier. Concurrence de lecture/mutation et
focus d’adoption gardent leurs preuves spécifiques à produire dans070.
La réalisation réutilise ces deux refs et l’effet de layout, sans nouveau style
ou token. Le manuel et le client E2E sont actualisés ; build local réussi,
nouveau rendu DEV encore à qualifier. Les captures de l’échec restent leur époque.

## Hash courant du testeur sous erreur de domaines — décision0712

La [preuve échouée](evidence/function-http-client-source-access-failed-dev-2026-11-12.json)
montre un hash déclaré absent malgré les métadonnées courantes. Le
[contrat de correction](CONSOLE_TESTER_SOURCE.md#hash-courant-sous-lecture-indisponible--correction0712)
réserve cette absence à une réponse confirmée : lecture en cours, indisponibilité
sans métadonnées et hash courant confirmé sont distincts. En cas de source
refusée, conserver le hash de cette seule réponse et retirer URL/cURL/résultat ;
aucun envoi autorisé. Correction et manuel déployés sur60938093, avec
[32groupes réels](evidence/function-http-client-source-access-dev-2026-11-12.json).
Les huit JPEG ciblés et24vues de guide/connexion sont inspectés individuellement.
Hash complet et refus lisibles en desktop/mobile ; le badge parent périmé101
et la typographie des quantités102 restent suivis. Les images ne prouvent pas
le transitoire de chargement, encore ouvert dans071.2.

## Lecture en attente qualifiée après la preuve de source

Le [complément37](evidence/function-http-client-loading-dev-2026-11-12.json) qualifie le reste
chargement de071.2 sur397sources6b9cb2bc/image60938093 :7reprise,5chargement et
25régressions,30vues inspectées. Vrai GET sans réponse pendant les vues desktop/
mobile, perte native du helper, garde jointe et même PID/naissance/cgroup ;
un seul GET, aucune invocation rejouée, puis nouvel appel explicite200.
Le [contrat et les reçus](CONSOLE_TESTER_LOADING.md#qualification-réelle-du-chargement)
distinguent le retour réseau du détachement et la fin de garde.071.2 est fermé
avec les preuves43/46/32 conservées ;071.6,101/102 et clôture complète restent
ouverts. Ce complément ne modifie ni le produit ni le manuel déployés.

## Exception du testeur : issue inconnue et retour explicite qualifiés

La [preuve31](evidence/function-http-client-task-exception-dev-2026-11-12.json) complète SLS-071 sans
changement de rendu : quatre JPEG ciblés inspectés par le principal,
22vues communes par le vérificateur RO. Après le vrai500 de l’exception TLS,
Issue inconnue, délai et consigne de consultation sont lisibles en desktop et
à390px ; saisies conservées, pas de succès ou rejeu annoncé. Le dernier appel
explicite montre200, hash complet, UUID, corps et téléchargement. Les quatre
vues n’ajoutent pas de défaut bloquant ;101/102 restent connus et non corrigés.
Leur clôture séparée et la campagne complète095 restent requises. Le corps
agrandi du manuel ne constitue pas une preuve de zoom global du navigateur.
