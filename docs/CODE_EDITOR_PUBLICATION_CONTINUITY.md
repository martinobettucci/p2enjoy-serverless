# Continuité de publication depuis le brouillon enregistré

Complément de [SLS-070.3/.5](BACKLOG.md#sls-070), décidé le22novembre2026
avant son client. Le [contrat éditeur](CONSOLE_EDITOR.md#publication-et-réponses-perdues)
définit un POST unique : reconstruction hors boucle HTTP, préparation durable,
puis vrai upload interne. Les anciens tests POST préparation puis PUT archive
ne prouvent pas ces raccordements. La preuve36 clôt les attentes UI et le focus ;
elle ne prouve pas ces phases ni la persistance après redémarrage.

## Découpage et autorité

Première tranche : mutation pendant reconstruction, instantané après préparation,
réponse perdue dans le navigateur et candidat préparé sans admission d’upload.
Aucun redémarrage dans cette tranche. La seconde tranche de coupures receiving/
validating et conservation du brouillon après redémarrage gardera un contrat
natif spécifique avant toute adaptation d’opérateur.070.3/.5 restent ouvertes
jusqu’à rapprochement de toutes leurs preuves, sans addition artificielle.

Seul SPARK infra-serverless DEV, API04604089, référence inchangée. Aucun changement
produit, image, schéma, dépendance, secret officiel, route ou configuration de
cellule prévu. Les deux design systems s’appliquent aux parcours existants ;
aucune surface nouvelle. Les mutations passent par les vraies API et les vrais
contrôles de console, sous une session SSO administratrice réelle. Le jeton
technique propre au service n’est employé qu’en mémoire. Aucun mock, interception,
état React injecté, seed SQL, horloge ou réponse substituée.

Une fonction initiale originale et un service dans code-editor-read-concurrency-
<nonce> réutilisent les préconditions fermées de la barrière native qualifiée :
namespace et service portent le même UUID de campagne, fonction nommée
editor-reader-lifecycle-<nonce>. Le service nomme l’usage editor-publication-continuity.
Aucune extension de l’opérateur de lecture n’est nécessaire. Seule cette fonction
est vivante ; idle_seconds0 et retour au repos avant chaque armement.

Le paquet conserve le handler reader-lifecycle et reader-gate.txt du dépôt,
puis le vrai handler publication-recovery.cjs et son publication-marker.json.
Ce dernier lit son marqueur packagé et attend réellement au plus8000ms à
l’import dans Node. Changer son JSON par le brouillon fournit des instantanés
observables par invocation Docker. Aucun sommeil dans un faux serveur.
Le paquet contient aussi256Kio de données aléatoires réelles, conservées dans
le code publié ; elles permettent les préfixes192Kio des uploads partiels.
Le packager du client produit un ZIP original dans son répertoire privé et
conserve SHA, tailles, modes et inventaire ; ces octets sont réellement publiés.
La cible stable reste le handler initial de lecteur et son hash A explicitement
promu. Les publications suivantes restent pilotes. Les variables/secret propres
au service ou à la fonction sont créés par API ; seules leurs présences/empreintes
entrent dans les observations, jamais les valeurs.

## Sept groupes ciblés, puis25communs frais

1. Accueil public et SSO réel ; session administrative confirmée sans cookie,
   mot de passe ni jeton dans les rapports.
2. Création par API, vraie publication du paquet, promotion explicite A, brouillon
   personnel et invocation A. Les intentions sont écrites avant chaque mutation.
3. **Mutation avant préparation** : retenir le vrai read de reader-gate.txt lors
   du POST éditeur, au moyen de la barrière existante et de son secours inchangés.
   Exiger HTTP de santé/gestion réactif et aucun candidat de cet UUID. Modifier
   un autre fichier par PUT du même propriétaire pendant ce maintien. Libérer
   et joindre : POST409, UUID absent API/SQL, aucune préparation/audit pour cet
   UUID, nouveau texte/version conservés et cible/ETag inchangés. Invoquer A.
   Les FD/inode/TID/naissances et toutes les fins de garde restent recoupés.
4. **Instantané après préparation** : enregistrer handler de reprise et marqueur B
   avec import8000ms. Commencer le vrai POST ; observer le candidat validating
   par API et lier son UUID/version de brouillon préparée. Pendant que la réponse
   manque encore, enregistrer marqueur C par le même compte dans un autre accès.
   Joindre la publication B puis comparer brouillon C/version/date et lien à B.
   Invoquer B par hash : marqueur B ; invoquer sans tag : A. Les deux décisions
   durables restent distinctes, sans promotion implicite ni sauvegarde écrasée.
5. **Réponse perdue UI**, en1440×1000 puis390×844 : ouvrir le brouillon proprement
   enregistré avec un nouveau marqueur et publier par confirmation réelle.
   Observer dans le navigateur UUID dans l’adresse avant le POST, un seul POST
   avec ce même UUID, puis validating via GET réel et absence de réponse POST.
   Capturer cette attente, recontrôler que la réponse POST manque encore juste
   avant le départ réel du document, puis revenir à l’adresse
   exacte portant cet UUID. Le navigateur rejoint le même candidat par GET ;
   aucun nouveau POST/envoi et aucun nouveau candidat ne sont permis. Exiger
   publication terminale, diagnostic/handler et marqueur attendu par invocation
   du hash, puis A sans tag. Conserver événements request/response/requestfailed,
   statuts et instants sans en-tête ni corps privé. Une navigation ne prouve pas
   à elle seule l’annulation du travail serveur ; son résultat durable fait foi.
6. **Préparation sans admission** : préparer par API quatre autres candidats
   propres à cette fonction, puis quatre connexions HTTPS partielles réelles
   vers leur PUT artifact. Longueur annoncée du ZIP entier, préfixe envoyé non
   vide et jamais achevé ; exiger quatre receiving et octets natifs présents.
   Le POST éditeur reconstruit alors son vrai ZIP et prépare son propre UUID,
   puis reçoit429/Retry-After5 avant admission de ce cinquième upload. Exiger son
   état prepared, réservation0, configuration_cipher présente en SQLite,
   aucun dossier d’archive (le ZIP reconstruit en mémoire n’a pas été admis),
   lien last_deployment_id/version du brouillon et cible/ETag conservés.
   Fermer/jointer les quatre connexions ; leurs candidats doivent être terminaux,
   sans réservation, configuration_cipher ni fichier avant la suite. La console consulte
   l’UUID orphelin par GET, affiche prepared et interdit une nouvelle publication ;
   captures ordinateur/mobile puis abandon explicite par sa confirmation réelle.
   Exiger failed/candidate_abandoned sans publication, brouillon intact et A invoqué.
   Aucune capacité ni coupure artificielle ne remplace les quatre vrais uploads.
7. Consolidation native : neuf invocations distinctes succeeded/handler_started1/
   HTTP200 et hashes attendus ; candidats admis/refusés/abandonnés, nombre exact
   de publications et lien du brouillon. Relever intégrités/FK, migrations,
   source/backend/web et absence de ressources actives avant purge physique.

Le groupe5 conserve trois captures par viewport : contexte enregistré, validation
avant navigation, suivi terminal au même UUID. Le groupe6 ajoute prepared et
abandon terminal dans les deux viewports, soit dix captures ciblées inspectées
individuellement. Le focus, les textes, les UUID/versions, les requêtes et les
effets serveur sont mesurés dans DOM/HTTP/SQL et jamais déduits des images.
Le groupe5 est un seul groupe avec ses deux variantes ; aucune variante ni
invocation supplémentaire ne gonfle les sept groupes.

## Bornes, jonctions et conservation

La barrière de lecture conserve acquisition<40s, maintien≤45s, alarme50s et
secours indépendant60s. Elle n’est combinée à aucun verrou SQL ni upload partiel.
Les quatre uploads du groupe6 sont ouverts après préparation des quatre candidats,
avec des sockets TLS vérifiés ; timeout client30s et fermeture explicite après
le refus du cinquième. Les lecteurs de réponses sont bornés et les requêtes
jointes ; l’échéance serveur120s reste un filet et ne constitue pas la preuve
nominale attendue. Une admission non observée ou un résultat incertain échoue,
sans relance silencieuse. Ne jamais purger avant jonction de la garde/connexions.

Au finally : réconcilier chaque intention possédée, libérer/reprendre la seule
garde créée, joindre tous les transports et appels, abandonner les préparations
propres encore ouvertes, puis purge publique de la fonction, révocation du seul
jeton et suppression des parents. Recoupement natif par UUID : brouillon/payloads,
réservations, artefacts, Docker/réseaux/canaux/backings/baux et montages absents.
Un objet étranger interdit le nettoyage global ; toute perte de confirmation
reste un échec conservé, jamais une réussite par drapeau de cleanup.

Gel propre committé/poussé/synchronisé, index de sources augmenté du contrat et
client avant exécution. Sept ciblés puis huit manuel/huit public/neuf connexion,
en série, rapports neufs reliés aux trois programmes de collecte et phases.
38backend/quatreweb HTTPS no-store, manuel18chapitres/74paragraphes SHA8d2434cf,
dix migrations, mêmes CID/images/démarrages, référence/configuration/budgets,
notes actives/proposées de livraison cfc94ca et5982originaux conservés. Les images
communes sont également ouvertes individuellement. Les preuves négatives restent
séparées à zéro groupe ; un défaut découvert rejoint le backlog avant correction.

## Banc implémenté, non encore exécuté

`e2e/code-editor-publication-continuity.mjs` porte les sept groupes ;
`e2e/code-editor-publication-package.py` produit les cinq fichiers originaux et
leur inventaire exact, dont le payload256Kio. Le collecteur existant
`code-editor-build-inspect.py` ajoute seulement les candidats détaillés et les
audits de préparation/publication/abandon de la fonction possédée, sans valeur
de configuration exportée. Les quatre candidats d’upload sont préparés et
alimentés par le même jeton Read/Update ; les candidats de l’éditeur appartiennent
à la session administratrice. Cette distinction respecte l’accès par acteur.

Index466sources prévu après ajout de ce contrat et des deux programmes ;
syntaxes JS/Python contrôlées. Aucun paquet généré, groupe E2E, invocation,
capture ou nettoyage de ce nouveau passage encore exécuté. Les compteurs attendus
avant purge sont neuf candidats (quatre publiés/cinq échoués), quatre révisions,
neuf audits de préparation, quatre de publication et un abandon ; l’UUID refusé
avant préparation n’y figure pas. Les coupures et restart restent à réaliser
selon leur futur contrat distinct.
