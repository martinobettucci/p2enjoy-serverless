# Compléments de console de l’éditeur

Ensemble2 de [SLS-070](BACKLOG.md#sls-070), après la
[qualification de sources38](evidence/code-editor-source-limits-dev-2026-11-12.json).
Le contrat reste [CONSOLE_EDITOR](CONSOLE_EDITOR.md), avec les règles de clavier,
focus, confirmations et mobile du design du produit et du socle global.
Décision du12novembre2026 persistée avant le client de preuve.

## Parcours retenus

La campagne complète `e2e/code-editor-ui.mjs` conserve ses quatorze groupes
existants puis ajoute quatre groupes ciblés. Elle part de l’accueil et du vrai
SSO, utilise formulaires, publications et confirmations de la console. Les
lectures API/natives recoupent les effets ; elles ne remplacent aucun geste
du parcours visuel. Les objets et handlers sont originaux et exécutés dans
Docker ; aucun seed SQL, interception, réponse ou dépendance substituée.

### Source archivée et version supprimée sur la seconde page

Les trois versions déjà produites sont complétées par quatre publications UI
réelles, distinctes par leur texteYAML, chacune invoquée. La dernière est
promue explicitement ; les deux plus anciennes sont respectivement archivées
et supprimées par leurs commandes de version. Le catalogue conserve sept
hashes, triés par création : cinq sur la première page, deux sur la seconde.

Le brouillon est d’abord recréé depuis la dernière cible. Depuis Éditeur, le
dialog **Choisir une version source** est ouvert au clavier : cinq lignes,
Précédente désactivée, puis vraie lecture offset5 et deux lignes. La source
archivée reste sélectionnable ; la supprimée est visible et désactivée.
La sélection de l’archive persiste après aller/retour entre pages. Ouvrir cette
source montre son hash et son contenu ; cela ne change ni cible ni base du
brouillon existant. Après abandon explicite, créer un nouveau brouillon depuis
cette archive produit sa vraie référence de base. Le dialog et sa seconde page
sont également parcourus à390px, avec captures dans le viewport et défilement
local. Les GET sont joints sur offset, pas seulement pathname ou titre.

### Conflit et adoption en conservant la saisie

Un brouillon neuf est recréé depuis la cible courante. Deux onglets du même
compte ouvrent le même fichier. A garde une saisie locale ; B enregistre un
autre texte. Le PUT de A donne409, conserve sa saisie et interdit de réécrire.
**Relire le brouillon serveur** montre la version et le texteB sans remplacer A.

Le bouton **Adopter cette version en gardant ma saisie** est ouvert puis confirmé
dans le flux, sans second dialog. Cette action est locale : aucune attente PUT
n’est installée, et le compteur de mutations doit rester inchangé. La référence
adoptée correspond à B, le textarea conserve A, le badge de saisie reste visible
et la sauvegarde est à nouveau permise. Une lecture serveur avant sauvegarde
confirme encore B et sa version/date. Seul le clic explicite **Enregistrer le
fichier** produit le nouveau PUT200 ; sa relecture puis son rechargement
confirment A. Le fichier est ensuite rétabli explicitement depuis la base pour
ne pas ajouter une huitième différence au parcours suivant.

### Diff paginé sur ordinateur et mobile

Sept petits fichiers nommés sont ajoutés et enregistrés par les dialogs et
champs réels, sur un brouillon basé sur la cible courante. Le bouton de
comparaison ouvre exactement sept différences, sans marqueur de version
parasite. Première page cinq lignes ; seconde page deux, avec vraie lecture
offset5. L’union des deux pages vaut exactement les sept chemins attendus.

Un chemin de la seconde page ouvre son propre détail ; le hash comparé et le
texte sont recoupés. Revenir à la première page retire le détail ancien. Les
commandes restent présentes aux extrémités, leurs états sont vérifiés. Le même
parcours se fait à390px, avec captures de la page, de la navigation et du détail,
sans débordement horizontal de document.

### Focus après pagination

La pagination du dialog de sources rend déjà le focus au titre **Versions de
la fonction** après lecture. Pour le diff, le précédent cohérent est le titre
**Comparer le brouillon enregistré** : après chaque changement de page achevé,
ce titre doit recevoir le focus. Le bouton disparaît pendant la lecture ; un
focus laissé sur body enfreindrait les §§9.5/14.3 du socle.

La lecture statique montre que `readDiff` retire son contenu pendant la requête
sans restitution explicite de focus. Ce constat reste une hypothèse de défaut
jusqu’au parcours réel. Le client relève les éléments actifs et les captures,
termine les trois parcours précédents puis exige le focus au titre dans un
groupe propre. Un refus reste un échec conservé ; aucune correction produit
n’est faite avant sa reproduction et sa décision persistée.

## Preuves et clôture

Sources/image/embarqués/HTTPS, même installation et configuration officielle,
invocations natives, helpers des groupes existants et nettoyage complet sont
recoupés avant/après. Les intentions de création et les identifiants conservés
permettent de nettoyer aussi un échec. Les groupes précédents ne sont pas
additionnés : le nouveau passage doit réussir ses dix-huit groupes propres.
Le manuel, les routes publiques et la connexion sont ensuite rejoués en série.
Chaque capture ciblée et commune est inspectée individuellement.

La preuve de console complète070.1/.3/.4 ;070.4 ne ferme qu’après recoupement
avec ses preuves serveur/chemins/diff/recherche antérieures et la concurrence
résiduelle décrite ci-dessous.070.1/.2/.3/.5 et l’unité restent ouverts pour
ZIP/concurrence, droits pendantIO et reprises.
Un changement produit éventuel actualise le manuel et les contrats, est
construit/déployé sur le SPARK DEV et qualifié sur sa nouvelle image. Aucun
changement de variable, secret, route ou schéma n’est prévu par ces parcours.

## Perte de focus reproduite sur60938093

Le [passage3a293344](evidence/code-editor-console-focus-failed-dev-2026-11-12.json)
au gel3a21c6b/407sources échoue au dix-huitième groupe. Les quatre observations
après pagination donnent `BODY`, en pages1/2 et1440/390px. Les17groupes précédents
passent, dont les trois nouveaux parcours, mais aucun groupe n’est qualifié dans
cet échec.25JPEG sont inspectés individuellement ;14handlers sont recoupés,
huit candidats publiés/un import réellement refusé. La fonction et ses sept
révisions sont purgées, le jeton révoqué, les deux parents supprimés et les13
helpers terminés. Même image/CID/démarrage,38backend/quatreweb, configuration,
référence et5982artefacts initiaux sont conservés. Zéro activité/bail/réservation/
garde, intégritéok/FKvide et dix migrations ; aucune régression commune ajoutée.

## Correction décidée avant code

La cause est le démontage de `{diff&&…}` dans `readDiff` avant la requête : les
boutons de pagination et de détail disparaissent alors qu’ils détiennent le
focus. `Section.headingRef` fournit déjà un h2 focalisable ; les fichiers et
sources utilisent déjà des refs et un effet après rendu. Aucun composant global,
token, dépendance ni migration supplémentaire n’est nécessaire.

La correction conserve une intention liée à la génération de la lecture :

- page, comparaison initiale ou nouvelle tentative : titre **Comparer le
  brouillon enregistré** après la lecture achevée ;
- détail réussi : h3 du chemin effectivement reçu, focalisable ;
- refus ou détail absent : repli vers le h2 stable ;
- réponse remplacée, surface changée, brouillon adopté/modifié/abandonné :
  annuler l’intention et la lecture logique, sans focus tardif ni réinstallation
  de cette ancienne comparaison.

Le déplacement attend le commitDOM courant et vérifie génération et chemin ;
un `finally` inconditionnel est écarté, car il peut focaliser une réponse périmée.
Le recalage automatique d’une page hors limite transmet l’intention à sa nouvelle
lecture. Le manuel et le design du produit suivent ces gestes. Le prochain
replay étend les assertions aux détails et aux captures du titre focalisé,
puis rejoue l’ensemble sur la nouvelle image construite et déployée en DEV.
Si la personne a déjà placé le focus dans un autre contrôle pendant la lecture,
ce choix est conservé : la restitution vise seulement le déclencheur encore
actif ou le focus retombé surbody. L’origine du geste est conservée lors du
recalage automatique, afin que celui-ci ne transforme pas une autre saisie en
nouvelle intention de focus.

## Risques statiques à éprouver dans la suite de070

La relecture observe que les effacements du diff par `saveMutation`,
`chooseSurface`, `adoptServer` et `removeDraft` n’invalident pas tous sa génération.
Le correctif doit les unifier pour que son focus reste lié à une lecture encore
valide. Une lecture réellement maintenue en attente face à une mutation reste
à qualifier avec l’ensemble3 ; ce constat statique n’est pas une panne runtime
prouvée par le passage ci-dessus.070.4 reste ouvert jusqu’à cette preuve.

Le bloc de confirmation d’adoption disparaît aussi après son action locale :
son retour de focus est à observer dans070.3, sans attribuer à ces captures une
mesure qui n’y figure pas. Ces restes sont suivis dans le backlog avant toute
correction correspondante ; ils ne sont pas présentés comme qualifiés.
