# Observer la requête de publication après départ du document

Contrat de [SLS-117](BACKLOG.md#sls-117), découvert dans le premier banc de
[continuité du POST éditeur](CODE_EDITOR_PUBLICATION_CONTINUITY.md). Aucun code
produit ni comportement utilisateur modifié. Le diagnostic précède toute
correction du client et ne qualifie aucun groupe de070.

## Premier rouge conservé

La [preuve négative](evidence/code-editor-navigation-observation-failed-dev-2026-11-22.json)
porte becedfc/466sources, API046/CIDe219. Le pilote89379 termine sortie1 et joint.
Quatre groupes passent puis le cinquième échoue dans until, ligne30, messageSHA
7ce6123c9cb2039fd62752c70a687684450b691adce4ee65a29c412c0c73ade6,
correspondant exactement à original_request_not_joined_after_departure.
Aucun commun, zéro groupe qualifié. Deux JPEG desktop réellement ouverts et
liés à leurs SHA/dates, quatre handlers et une garde avec un lecteur recoupés.
Une fonction et son jeton/parents sont purgés/révoqués ; repos et intégrités,
38backend/quatreweb HTTPS no-store, notes, budgets/fichiers officiels, référence,
manuel18/74SHA8d2434cf et5982originaux conservés. Gzip02baf71c/brut9b446ec7.

Le POST apparaît à41359,041509ms monotones du client, validating est observé
par API, le départ est demandé à41737,316443ms et goto finit à41870,678022ms.
La télémétrie contient un POST et un GET ; ni post-response ni post-requestfailed.
Le client attend cinq secondes un événement de requête puis retire ses listeners
au finally de ce groupe. Le retour à l’éditeur et la variante mobile ne sont pas
atteints. Le candidat apparaît publié lors du nettoyage natif ultérieur : cela
ne date pas la fin de la requête originale et ne prouve pas sa remise au navigateur.

Le handler configuré attend réellement8000ms à l’import ; la fenêtre5s ne couvre
pas à elle seule cette durée configurée. La durée restante à la navigation,
l’instant ou le type de l’éventuel événement tardif et la cause de son absence
restent inconnus. Aucune dernière sonde ni événement manquant n’est inventé.
Ce constat ne justifie pas encore un remplacement arbitraire de délai.

## Diagnostic avant correction

Créer un client dédié `e2e/code-editor-navigation-observation.mjs`, sur le seul
SPARK infra-serverless DEV, sans filtre ni saut d’un groupe de la campagne7+25.
Trois étapes de diagnostic : accueil/SSO réel, fonction/paquet original publié
et promu A, puis une publication éditeur B avec départ réel du document sur
ordinateur. Ce diagnostic ajoute zéro groupe qualifié, même s’il réussit.
Le service et la fonction nomment editor-navigation-observation-<nonce> ;
namespace code-editor-read-concurrency-<nonce>, descriptions UUID de campagne,
compatibles avec le collecteur physique fermé. Aucun changement de cette liste
ni de l’opérateur de lecture ; aucune barrière ni coupure de contrôle ici.

Réutiliser le packager original5fichiers et le vrai handler de reprise avec
son marqueur B/import8000ms. Les modifications passent par API ordinaires,
puis la publication B par les contrôles de la console. Session/secret/jeton
restent en mémoire ; aucun fichier privé de session dans le rapport. La cible A
reste promue et la configuration privée conservée. Un appel A préparatoire,
B par hash après publication et A par défaut donnent trois invocations réelles.

Installer les observations avant le geste de publication, par deux voies :

- Playwright request/response/requestfinished/requestfailed, corrélées par
  méthode POST, chemin exact, UUID du corps connu et objet de requête observé.
  Conserver aussi si l’identité objet est identique, sans supposer que l’absence
  d’un événement signifie une réponse ou une annulation.
- Session CDP native de cette page : Network.enable et Page.enable, événements
  de cycle de page activés. Enregistrer uniquement le POST éditeur attendu,
  son requestId, frameId/loaderId, timestamp, UUID/version ; puis ses
  responseReceived/loadingFinished/loadingFailed. Statut, longueur et code
  d’erreur fixe ou empreinte suffisent ; aucun en-tête, cookie, corps, initiator,
  URL d’authentification ou secret n’entre dans les pièces. Enregistrer la
  navigation du frame principal et ses événements init avec loaderId/timestamp
  pour distinguer l’ancienne page du nouveau document.

CDP est ici un observateur : aucune interception, route, réponse, throttle,
mutation de script, horloge, stockage web ou état applicatif. Les événements
restent ceux du navigateur réel. Source/page, requête et candidat sont reliés
avant toute assertion ; callbacks bornés et exceptions conservées.

L’UUID doit être dans l’adresse avant le POST. Observer validating par GET réel,
absence de réponse originale avant départ, puis capturer l’attente et quitter
réellement le document. Garder les listeners de l’ancienne requête pendant
l’observation suivante et jusqu’à sa jonction/fermeture. Conserver la fin réelle
de goto et la frontière native du nouveau document si elle est disponible ;
ne pas mélanger directement timestamp CDP et performance.now.

Après départ, une observation monotone de vingt secondes au plus attend un
événement terminal CDP du requestId original, en conservant les événements
Playwright associés. Cette borne diagnostique ne garantit ni succès serveur ni
annulation ; elle permet de conserver ce qui manque encore si la fenêtre expire.
Un événement de réponse est distingué de la fin du transfert. Si l’issue
observée contredit la perte de réponse attendue, conserver cette contradiction
sans changer l’oracle en réussite. Un timeout reste un diagnostic échoué, sans
rejeu automatique ni simple allongement opportuniste dans la même exécution.

Lire le candidat par GET et consigner sa décision terminale indépendamment du
transport. Revenir à l’adresse exacte du même UUID, exiger consultation GET sans
nouveau POST ; aucune seconde publication ou nouveau candidat. Les trois
captures desktop sont : marqueur enregistré, attente avant départ et suivi au
retour, toutes ouvertes individuellement. Si une phase n’est pas atteinte, son
image et son résultat ne sont pas inventés. Aucun parcours mobile qualifié par
ce diagnostic : les deux viewports restent exigés dans le replay7+25.

## Conservation et sortie

Le programme conserve chaque observation allowlist avant assertion, les
échéances/instants de lecture, le résultat du candidat et la fin des canaux.
Données sensibles et code hors fixture exclus. Inventaire complet des UUID
possédés avant abandon/purge ; un objet étranger interdit ces mutations.
En finally, joindre tous les appels et attendre la fin native des candidats
possédés ; garder le canal API administrateur vivant pendant purge publique,
révocation du jeton et suppression des parents propres. Fermer ensuite CDP,
contexte et navigateur. Si le canal API appartient au contexte du navigateur,
sa fermeture attend donc la fin des mutations et recoupements de nettoyage.
Recouper la fonction, ses deux révisions attendues, trois invocations et les
ressources physiques, ainsi que compteurs au repos et absence de consommateurs.
Un échec conserve ses états et le nettoyage réel, sans acquitter une preuve manquante.

Avant diagnostic : nouveau gel propre committé/poussé/synchronisé incluant ce
contrat et son client, index468sources prévu. MêmeAPI046/référence/configuration,
38backend/quatreweb,010/intégrités/FK, manuel18/74SHA8d2434cf, notes proposées
cfc94ca et5982originaux recoupés avant/après. Les trois programmes privés de
collecte sont également conservés et figés ; aucun commun du précédent rouge
n’est recyclé. Aucun build produit, migration, variable, route ou secret officiel.

Après diagnostic seulement : inscrire le résultat, ses limites et le choix de
correction avant de modifier le client7+25. Revue et nouveau gel,32groupes frais,
neuf handlers/une garde/quatre uploads et32captures inspectées avec toutes les
conservations habituelles. Le diagnostic et le premier rouge restent séparés à
zéro groupe ajouté.117 ne ferme qu’avec ce replay ;070 garde ses critères de
coupures receiving/validating et de persistance après redémarrage.

## Préparation du diagnostic, sans exécution

Client dédié implémenté, syntaxe JS contrôlée. Observateurs Playwright par
requête et session CDP avec2048événements conservés au plus ; aucune interception.
Les GET du candidat au retour sont relevés séparément du POST original. L’UUID,
la version et le frame/loader initiaux sont recoupés avant départ, et la réponse
est comparée à l’init du nouveau document dans le seul domaine temporel CDP.
L’expiration conserve deadline, dernière sonde, fin réelle et GET indépendant
avant de réémettre l’échec ; la sélection finale ne retient que les événements
déjà reçus avant deadline, aucun événement tardif ne l’acquitte.
Le canal context.request reste vivant pour le nettoyage ; callbacks/listeners,
CDP et navigateur sont fermés ensuite. Trois étapes, trois invocations et trois
captures desktop attendues, zéro groupe qualifié. Index468sources vérifié à
l’écriture ; diagnostic non exécuté, cause et correction toujours non établies.

## Diagnostic20s conservé —22novembre2026

La [preuve négative du diagnostic](evidence/code-editor-navigation-diagnostic-failed-dev-2026-11-22.json)
porte fe02296/468sources/API046. Pilote42224 sortie1/joint ; deux étapes passent,
la troisième échoue native_network_terminal_missing, ligne79, SHA
befe527c7c12f6ebda55a7307d2774e562dde1f4c0f507de4768fd3d2f391910.
Fenêtre20s,390sondes, dernière lecture avant deadline et sélection finale bornée ;
expiredtrue, native_terminalnull. PW porte request/candidate-get, CDP un seul
request : aucun terminal, aucune erreur d’observateur. Nouveau loader/init du
frame principal réels, puis GET indépendant candidatpublished. Retour à l’éditeur
et deux invocations suivantes non atteints ; un handler préparatoire, deux
captures desktop inspectées et purge physique complète. Zéro groupe qualifié,
aucun commun ; services/images,38backend/quatreweb,010, notes/configuration/
budgets/référence, manuel18/74 et5982originaux conservés. Gzipfc631548/brut82938f3c.

Ce rouge reste échoué. L’absence du terminal après navigation n’est ni une
annulation ni une réponse reçue, et le candidat publié ne l’acquitte pas.
Aucune cause du silence CDP n’est établie.

## Décision après diagnostic, avant code de fermeture

Le contrat fonctionnel070 demande de reprendre une publication incertaine par
GET du même UUID, sans nouvel envoi. Il ne promet aucun événement Network d’un
document quitté. Le banc avait ajouté ce terminal comme condition de jonction
du client. Les deux fenêtres5s/20s montrent que ce canal n’apporte pas cette
confirmation dans les parcours observés ; l’agrandir encore ne prouverait pas
la ressource cliente effectivement quittée.

Recoupement local du code installé playwright-core1.64.1, `lib/coreBundle.js` :
la navigation remplace le document et vide l’ensemble inflight du frame
(lignes24518–24546 et24793–24802). Ce chemin n’émet pas de terminal individuel
pour chaque ancienne requête. Les terminaux PW viennent de loadingFinished/
loadingFailed (37714–37757). Ces sources expliquent les limites de l’oracle PW,
sans attribuer une cause au silence CDP. Les déclarations du protocole décrivent
Target.targetDestroyed comme la destruction de la target ; detach seul n’est
pas une destruction. Le succès du seul closeTarget vaut toujourstrue hors erreur
et ne suffit pas non plus. Les lignes citées sont le snapshot de cette version
installée ; elles ne désignent pas un code applicatif ou un événement reconstruit.

Décision réversible : provoquer la perte de réponse en **fermant réellement
l’onglet de publication pendant validating**, puis ouvrir une nouvelle Page
dans le même contexte authentifié à l’adresse exacte du candidat. Prouver la
fin de la ressource cliente par sa Page/target, garder l’état HTTP original
inconnu si aucun terminal n’est observé et éprouver séparément le résultat
serveur/GET. Cette décision corrige l’oracle du banc ; elle ne change ni le
produit ni son contrat de reprise. Les deux rouges gardent zéro groupe qualifié.

<a id="diagnostic-fermeture-page"></a>
## Diagnostic de fermeture Page/target

Nouveau client dédié `e2e/code-editor-page-closure.mjs`, sans changer les deux
clients des passages échoués avant acquisition du résultat. Trois étapes
SSO/préparation originale/perte et reprise, trois invocations A/B/A et trois
captures desktop, zéro groupe qualifié. Index469sources prévu. Service/fonction
nomment editor-publication-page-closure-<nonce>, namespace de campagne fermé
code-editor-read-concurrency-<nonce>. MêmeAPI046, mêmes fixtures originales,
paquet et import8s ; aucune dépendance, réponse ou requête substituée.

Avant POST : les observers PW et CDP de la page sont installés, UUID/version
et loader du POST liés à l’adresse ; les éventuels événements réseau restent
conservés mais ne sont pas requis pour confirmer la fermeture Page/target.
Aucune fin HTTP n’est affirmée sans observation terminale. Une **session CDP
navigateur indépendante** est ouverte ; activer seulement la découverte des
targets. Lire le targetId exact de la Page possédée par Target.getTargetInfo,
exiger typepage et origine de console. Le listener de Target.targetDestroyed
est armé avant fermeture et ne conserve que ce targetId. Ne fermer aucune
Page ou target étrangère ; ne pas assimiler detach ou closeTargetsuccess à la
confirmation.

Lancer le vrai POST par sa confirmation UI, observer validating et absence de
réponse originale ; conserver le marqueur enregistré et l’attente par captures.
Avant fermeture, exiger à nouveau absence de réponse et aucun texte non
sauvegardé. Persister l’intention du seul targetId puis appeler Page.close().
Exiger en10s au plus les trois faits : événementClose de cette Page, close
achevé/isClosedtrue, Target.targetDestroyed du même targetId sur la session
navigateur. Relire Target.getTargets et constater l’absence de ce targetId.
Les réceptions réseau éventuelles restent des observations distinctes ; aucune
réponse originale ne doit avoir été observée avant cette fermeture achevée.
Une confirmation manquante échoue, même si le candidat est ensuite publié.

Créer ensuite une nouvelle Page du même contexte, appliquer le même viewport et
ouvrir l’adresse exacte avec deployment=UUID. Le contexte et context.request
restent vivants : aucune copie persistante de cookie, nouvelle identité ou
session remplacée. Compter les POST sur les deux Pages et les GET de reprise :
un seul POST, même UUID/draft_version, nouvelle Page et GET sans nouvel envoi.
Exiger publication, brouillon/version/lien et cible A inchangés ; invoquer B
par hash et A par défaut. La troisième capture montre le suivi terminal sur
la nouvelle Page. Conserver les identités des deux Pages/targets sans valeurs
confidentielles ni contenu d’autres targets.

Sur timeout/erreur, conserver fenêtre et dernière observation, état Page/target,
GET indépendant du candidat et nettoyage possédé. Une fermeture commencée est
jointe avant fin du diagnostic ; canal API conservé pour le nettoyage, puis
fermeture des observers, des Pages/contexte et navigateur. Si elle n’est pas
confirmée nominalement, la fermeture finale du navigateur est distinguée de
la preuve attendue : aucun succès de diagnostic ne lui est attribué. Les
collectes sources/images/38backend/quatreweb/010/manuel/notes/budgets/référence/
5982originaux et purge physique restent identiques aux exigences précédentes.

Après acquisition seulement : preuve et décision avant adaptation du client
7+25. Ce replay utilisera la même fermeture en1440/390px et gardera neuf
handlers, une garde, quatre uploads partiels, dix captures ciblées/22communes,
zéro cumul avec diagnostics.117 et070 restent ouverts à ce checkpoint.

## Client de fermeture préparé, avant exécution

`e2e/code-editor-page-closure.mjs` est distinct des clients rouges ; trois étapes
et zéro groupe qualifié. Syntaxe JS et index469sources contrôlés. Le contexte API
reste ouvert pour purge et recoupements ; après sa fermeture, la requête de
fermeture Page est jointe et la session navigateur indépendante détachée avant
la fermeture du navigateur. Le reçu nominal10s reste distinct de cette jonction
finale. Diagnostic non exécuté, aucun comportement produit modifié.
