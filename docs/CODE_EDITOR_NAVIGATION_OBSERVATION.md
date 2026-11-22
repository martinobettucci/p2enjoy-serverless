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
