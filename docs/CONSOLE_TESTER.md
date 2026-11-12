# Tester une fonction par sa passerelle HTTP

Contrat de réalisation de [SLS-071](BACKLOG.md#sls-071), décidé le 12 novembre
2026 avant code. Complète [CONSOLE_USABILITY](CONSOLE_USABILITY.md#client-http-par-fonction).
L'unité partage l'ordre 3 avec l'éditeur ; elle fournit le parcours manquant de
070.6. Les autres preuves ouvertes de 070 restent dans leur unité.

## Parcours

La fiche de fonction reçoit la destination `/console/functions/UUID/tester`.
Les versions disponibles et une publication réussie dans l'éditeur y mènent
avec `version=HASH`. Le catalogue de retour est conservé. Seuls version et UUID
d'invocation peuvent entrer dans une adresse partageable : aucun jeton, corps,
en-tête, paramètre de requête métier ou résultat n'y est enregistré.

La surface comporte les sections Destination, Requête, Accès et Réponse. C'est
un outil de composition éphémère, pas un formulaire modifiant la configuration.
Les saisies sont donc sur place ; cet écart au socle est motivé dans le design
du produit. Méthode, origine calculée, chemin, query, en-têtes, corps absent,
texte UTF-8, JSON ou fichier sont composés explicitement. Le JSON est validé
sans reformater silencieusement ses octets. Les chemins HTTP actuels sont
exacts, sans syntaxe de paramètres dynamiques ; le manuel le précise.

La destination utilise le catalogue officiel courant de SLS-066, paginé par
cinq, avec cible promue ou hash explicite. Un hash indisponible ne se transforme
jamais en sélection par défaut. L'URL exacte est lisible et sélectionnable.
Le mode initial est **Serveur de console** ; **Navigateur** est un choix distinct.
L'origine déclarée n'est modifiable qu'en mode serveur. En mode navigateur,
elle vaut réellement l'origine de la console. L'IP reste celle du transport
effectif ; le testeur ne fabrique aucun en-tête de proxy.

Un envoi est une action explicite, sans retry automatique. Pendant l'envoi, le
snapshot reste visible et une commande **Arrêter l'attente** est proposée.
Un arrêt, timeout ou transport perdu signifie issue inconnue, pas échec certain
du handler. Les invocations admises peuvent terminer ; le lien vers la liste
permet de les retrouver. Un résultat HTTP, y compris 3xx/4xx/5xx, reste une
réponse avec son véritable statut, jamais un succès métier simulé.

## API de la console

Routes nouvelles, administration SSO et CSRF obligatoires avant lecture du
corps. Les jetons techniques ne donnent pas accès au relais de console.

| Route | Contrat |
| --- | --- |
| POST `/api/functions/{UUID}/test-token` | Corps `{}` strict ; crée par le mécanisme normal un jeton Read, limité à cette seule fonction, avec expiration serveur à maintenant + 900 s. Retour201, mêmes métadonnées et valeur unique que les jetons de service. Aucun droit, portée ou délai choisi par le client. |
| POST `/api/functions/{UUID}/test-invocation` | Corps strict décrit ci-dessous ; effectue un seul véritable appel HTTP sortant et restitue son résultat borné. Aucun appel direct au moteur ni handler importé. |
| GET `/api/functions/{UUID}/invocations/{INVOCATION_UUID}` | Même droit Read/admin que la liste, fonction vivante et appartenance vérifiées ; projection identique de l'invocation et de ses journaux.404 si absente, retirée par rétention, étrangère ou refus antérieur à sa création. |

Le POST de test prend : `origin` (origine officielle exacte), `version` (null ou
64 caractères hexadécimaux minuscules), `path` (null pour l'endpoint implicite,
sinon chemin relatif exact), `query` (liste ordonnée de couples name/value),
`method` (GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS), `headers` (couples name/value),
`token` (Read fourni), `body_base64`, `max_response_wait_seconds` (1–900, défaut30).
Le serveur construit lui-même `/invoke/UUID[@HASH][/path]` : aucun champ URL,
autre UUID, userinfo, fragment, port arbitraire ou redirection ne fournit une
destination. Le chemin reste dans la grammaire relative de l'adaptateur ; les
chemins non déclarés et méthodes non admises sont refusés par la vraie passerelle.

L'origine est relue depuis `/spark/routes`, filtrée par le port ASGI réel et
concrète (aucune wildcard). Source absente/refusée/invalide :503 avant émission ;
origine hors catalogue :422. Le handler peut retourner une redirection ; elle
est affichée mais jamais suivie. Le client HTTP est isolé par appel, utilise
TLS vérifié, `trust_env=False`, aucun cookie de console/OAuth, aucun cookie jar
réutilisé et zéro relance. La dépendance httpx verrouillée existante suffit.

En-têtes de transport, Cookie, CSRF, Host, X-Serverless-Token, X-Request-ID,
X-Serverless-Request-ID, proxy-*, sec-* et les en-têtes Forwarded sont réservés.
Le jeton dédié produit exactement un X-Serverless-Token. Authorization reste
l'authentification métier fournie. Les noms sont ASCII valides, sans doublon
insensible à la casse ; valeurs sans contrôles ni espaces de bordure. L'origine
serveur utilise le champ Origin normal, une seule fois. Le contenu sensible ne
rejoint ni audit, log automatique du testeur, préférences ni historique.

## Bornes et résultats

| Grandeur du testeur | Borne |
| --- | --- |
| Corps envoyé | 1 Mio réel, borne actuelle de la passerelle |
| JSON de transport autorisé | 2 Mio, seulement après administration ; autres JSON inchangés |
| Réceptions/envois simultanés serveur | 4 globaux, admission avant allocation du corps ; cinquième429 |
| Réception du JSON | 30 s puis408, libération garantie après jonction |
| Query | 128 couples, 8 Kio UTF-8 cumulés noms/valeurs |
| En-têtes utilisateur | 64, 16 Kio cumulés ; nom128 caractères, valeur8192 octets |
| Corps de réponse conservé/téléchargé | 6 Mio ; lecture d'un octet supplémentaire pour signaler la troncature |
| En-têtes reçus présentés | 128 / 32 Kio ; dépassement explicitement signalé |
| Aperçu texte | 64 Kio ; le téléchargement garde les octets conservés |
| Attente de réponse | 1–900 s, indépendante de la durée d'exécution de la fonction |

Le serveur retourne200 avec `state: response`, statut HTTP distant, en-têtes
bornés, corps base64, nombre d'octets conservés, troncatures, durée monotone,
identifiant de requête et hash exposés par la passerelle. Une erreur de transport
ou échéance retourne `state: unconfirmed`, code neutre, durée, sans inventer
statut, UUID d'invocation ou hash. Les erreurs de validation/authentification du
testeur conservent leurs propres401/403/404/408/413/422/429/503.

Un seul résultat vit en mémoire de la page ; un nouvel envoi retire l'ancien.
Les corps sont du texte échappé ou des octets, jamais du HTML/SVG exécuté.
Le téléchargement est un Blob local, supprimé avec le résultat. Le serveur
conserve les octets HTTP bruts, sans décompression implicite ; fetch navigateur
peut décompresser nativement. Cette distinction est indiquée si Content-Encoding
est présent. Les réponses opaques CORS ou redirections masquées par fetch n'ont
aucun faux statut200 : elles sont décrites comme non lisibles/inconnues.

La composition valide les mêmes bornes et interdictions avant les deux modes :
noms ASCII originaux, doublons insensibles à la casse, valeurs, en-têtes réservés,
8Kio de query et16Kio d'en-têtes. Le navigateur ne contourne pas ces règles.
Les refus HTTP propres au testeur restent des erreurs de gestion ; seules une
enveloppe de transport inconnue ou une absence de réponse produisent l'issue inconnue.

Le mode navigateur utilise fetch `credentials:omit`, `redirect:manual`,
`mode:cors`, `cache:no-store`, `referrerPolicy:no-referrer`, AbortController et
lecture de réponse bornée. Les cookies de gestion ne sont jamais joints, même
sur le domaine canonique. Un GET/HEAD ne porte pas de corps dans les deux modes.

## Jetons, copie et corrélation

L'administrateur fournit un jeton ou crée explicitement le jeton temporaire.
Le serveur fixe ses900s ; la page montre la portée et l'échéance. Valeur masquée,
gardée en mémoire seulement ; sa révocation explicite réutilise la route normale.
Quitter la page retire la valeur locale ; le jeton expire au plus tard à son
échéance et reste administrable dans la liste de service. Un secret de création
dont la réponse est perdue n'est jamais recherché dans SQLite ni recréé en boucle.

L'exemple cURL contient des placeholders pour le jeton, les en-têtes et valeurs
de query ; le corps est un fichier à fournir. Les valeurs du jeton, des en-têtes,
de query et du corps ne sont pas copiées ; domaine, chemin et noms restent lisibles.
La réponse nomme le hash exécuté et l'ID réels. Un lien ouvre l'invocation exacte
dans la facette existante avec son journal déplié ; les refus avant admission
peuvent n'avoir aucune observation, ce qui est indiqué sans inventer de ligne.
Ce lien prépare la corrélation de SLS-072 sans annoncer ses recherches absentes.

La passerelle expose désormais X-Request-ID, X-Serverless-Request-ID et
X-Serverless-Code-Hash à CORS, y compris les IDs des refus. La CSP des documents
de console autorise `connect-src 'self'` et les seules origines concrètes
officielles du port réel, sans wildcard ni politique générique https:.
Source indisponible : self seul ; les anciennes adresses ne sont pas réutilisées.
La redirection canonique conserve version du testeur et UUID de corrélation.

## Réalisation et preuves

Ordre : contrat committé/poussé ; serveur et réutilisation des jetons ; facette
et liens ; fixture originale et clients de preuve ; revue/build/bascule DEV
avec sauvegarde native ; API puis UI réels ; régressions communes et preuve.
Aucune migration, nouvelle variable/secret, route SPARK, dépendance ou nouvelle
instance d'infrastructure n'est nécessaire. L'image remplace seulement le contrôle.
Le contrôle032ca071 est déployé après sauvegarde native SQLite, schéma010
inchangé. La [première tranche](evidence/function-http-client-dev-2026-11-12.json)
passe43groupes :18ciblés et25régressions, sur382sources46a59128.27handlers,
trois publications et expiration900s réelle sont recoupés.27captures sont
inspectées (cinq par le principal,22par factory_verifier) ; le manuel servi
correspond à18chapitres/74paragraphes. Deux fonctions nominales et deux du
premier passage sont purgées, huit jetons révoqués et5982artefacts conservés.
Les13groupes du premier passage047e33 restent exclus : le banc ouvrait la
mauvaise destination de catalogue. Le replay4824d4a2 utilise sa vraie URL.
Les recoupements embarqués viennent après le ciblé puis avant/après régressions,
pas avant le ciblé. Certaines captures ne cadrent qu’une partie de la réponse ;
le corps du chapitre Tester n’est pas cadré. SLS-071 reste ouverte pour les
compléments UI, CORS refusé, politiques IP, saturation, troncature et SIGKILL.

Les intentions de création du client sont enregistrées avant POST, avec absence
du nom UUID et parent vérifiés. Une réponse perdue ou5xx est réconciliée en
lecture par ce seul nom/parent, sans rejeu ; un refus4xx certain n'est pas adopté.
Chaque fermeture est tentée même si la précédente échoue ; le reçu ne devient
complet qu'après purges, recoupements et fermeture des clients.

Les tests créent et publient un handler original du dépôt : texte, JSON, binaire,
Unicode/query/en-têtes, Authorization par empreinte, absence cookies/jeton de
plateforme, statut métier non2xx, redirection vers une seconde vraie fonction
dont le compteur doit rester inchangé, gros corps/réponse et attente réelle.
Les API refusent sans émission les destinations étrangères et en-têtes réservés,
notamment les noms Unicode qui deviennent ASCII après lower() (signe Kelvin).
La validation porte sur le nom original ; la jonction annule d'abord les deux
tâches, recueille leurs sorties puis restitue la capacité dans un finally externe,
y compris si une tâche relève une exception inattendue. Cette correction de
revue avant déploiement et ses appels suivants sont suivis dans071.6.
Les tests couvrent aussi
les modèles inconnus, mauvais CSRF/droits, bornes exactes/+1. Les versions A/B,
archivage entre sélection et appel, jeton révoqué/expiré et politiques origine/IP
passent par la vraie passerelle. L'expiration du jeton temporaire est vérifiée
après ses quinze minutes réelles, sans changement d'horloge/SQL.

L'UI part de l'accueil et du SSO, compose et envoie dans les deux contextes,
teste l'alias HTTPS réel, CORS autorisé/refusé, timeout/annulation sans rejeu,
copie sans secret, téléchargement exact et corrélation. Clavier, focus, erreurs,
vide, données longues, mobile/tablette et JPEG inspectés font partie du reçu.
SIGKILL/reprise durable et limites d'admission sont éprouvés séparément quand
le serveur est raccordé. Sources/images, données antérieures, nettoyage physique
et manuel servi sont recoupés. Rien n'est clôturé par ce seul contrat.

## Compléments UI et admission — décision avant intégration

La tranche43 reste immuable avec son époque382sources. Les deux clients
`e2e/function-http-client-ui.mjs` et `e2e/function-http-client-admission.mjs`
ouvrent chacun leurs propres objets, publient le fixture canonique original
puis purgent et recoupent leur seul périmètre. Le même contrôle032ca071 suffit ;
aucune nouvelle image produit, configuration, route ou dépendance n’est requise.
Chaque reçu garde sa propre époque de sources et ses prérequis ; ces préparations
ne sont pas ajoutées aux43groupes déjà qualifiés.

Le fixture ajoute une origine IP observée, une réponse gzip dont la décompression
fait6Mio+1,128en-têtes et une réponse brute de6Mio+1. La borne HTTP de6Mio de la
passerelle empêche d’atteindre la troncature brute défensive du relais : le
supérieur doit être refusé par le vrai moteur. Le gzip passe cette borne brute
et exerce réellement la troncature du navigateur après décompression. Le corps
serveur téléchargé est comparé à un autre vrai appel brut et son contenu
décompressé au SHA attendu ; le navigateur garde6Mio et un aperçu64Kio. Aucun
serveur de substitution ne contourne la passerelle pour forcer une branche.

Le client UI compose texte/JSON/fichier, query hors borne, doublons et noms
réservés dans les deux modes sans émission. Il change la politique du seul
service de sa campagne pour éprouver origine autorisée/refusée, CORS refusé,
IP réellement observée et ET/OU ; restauration de politique avant la suite.
L’annulation attend un handler démarré, arrête l’attente puis retrouve une unique
invocation terminée, sans rejeu. Révocation au clavier, repli de focus,404 de
corrélation expliqué, liens de versions et nouvelles vues du manuel restent
éprouvés par leurs gestes réels. Les captures cadrent les corps/sections utiles,
au lieu de déduire leur lisibilité d’une vue partielle.

Le client d’admission adapte le précédent TLS réel de l’éditeur : session SSO,
Origin/CSRF, POST du testeur, JSON annoncé2Mio, premier octet envoyé ; quatre
réceptions, cinquième sans corps429 puis quatre408 après30s. Tous les sockets
et promesses sont joints avant de vérifier cinq appels sains. Un second groupe
occupe quatre relais sortants par quatre handlers réellement lents, observe
leurs quatre invocations actives puis refuse le cinquième429. Les promesses
reçoivent dès leur création un collecteur de rejet, avant tout sondage ; leur
jonction est aussi garantie au finally. Ces deux groupes forment chacun une
seule charge concurrente, jamais deux scénarios exécutés en parallèle.

Statut : le [complément46](evidence/function-http-client-ui-admission-dev-2026-11-12.json)
passe16UI,5admission et25régressions sur384sources8285798e et8c761c5e.
35handlers, sept candidats publiés et six révisions conservées avant purge sont
recoupés. Huit fonctions des passages nominal/intermédiaire sont purgées, six
jetons révoqués ;38images inspectées. Quatre réceptions donnent quatre408
après30,088–30,103s, cinquième429 en128ms avant corps ; les quatre sorties
actives rendent aussi leur capacité.071.7 et070.6 sont qualifiés,071reste
ouverte pour SIGKILL, confidentialité native, source indisponible, délais UI et
régression complète. La tranche43 et l’intermédiaire21ne sont pas réadditionnés.

## Messages de composition périmés — correction071.7

La revue des16vues du passage UI f4908538 constate une alerte de fichier>1Mio
encore affichée après passage au corps JSON. Le message concerne une saisie
ancienne et brouille l’état courant. Décision avant code : tout changement de
champ de composition retire l’erreur et la confirmation de copie associées.
Les erreurs d’un nouvel envoi restent visibles tant que la composition ne change
pas ; elles ne disparaissent pas simplement parce que leur état est rendu.
Les résultats HTTP déjà observés gardent leur statut réel ; aucun appel n’est
relancé. Les confirmations d’émission/révocation de jeton gardent leur propre
suivi. Une sélection de fichier invalide conserve son refus jusqu’à la prochaine
correction ; le changement d’objet fichier ne doit pas effacer ce refus aussitôt.
La revue relève aussi le pluriel «1octets» : le compteur prend le singulier
pour un seul octet, sans modifier sa mesure UTF-8.
Cette correction UI est déployée sur8c761c5e après backup natif, backend38sources
inchangé, puis16+5groupes et25régressions passent. Les16vues ciblées nominales
ne montrent plus ces défauts, complétées par22vues de régression inspectées.
071.7 est qualifiée. Le passage21initial reste intermédiaire et exclu des46.
Le manuel compilé avec la règle actualisée correspond à18chapitres/74paragraphes.
Les recoupements embarqués/HTTPS encadrent cette fois l’ensemble des campagnes ;
configurations, référence et5982artefacts antérieurs sont conservés.

## Provenance des refus et coupure après admission

Le replay réel80eca655 sur8c761c5e reproduit un502 de proxy après SIGKILL du
contrôle avec handler démarré, mal présenté comme refus certain par Tester.
La reprise native garde une seule invocation et le même hash actif.
La [correction071.8](CONSOLE_TESTER_FAILURES.md#défaut-reproduit-après-admission--correction0718)
marque les véritables réponses API du contrôle et reconnaît leur erreur JSON ;
les pertes du trajet de gestion restent inconnues. Le statut HTTP seul ne
suffit plus, y compris pour les mutations de jeton temporaire. Un vrai503 du
contrôle avant émission reste un refus visible, éprouvé par verrou SQLite
sans écriture de données. La [preuve42](evidence/function-http-client-recovery-confidentiality-dev-2026-11-12.json)
qualifie cette distinction pour l’invocation sur96e5dc4e/389sources039c4c97 :
7reprise,10confidentialité et25régressions,12handlers,27captures inspectées.
Le reçu80eca655 reste échoué. Les mutations temporaires sont ensuite
qualifiées dans32, comme décrit ci-dessous.071.1/.4/.5 sont qualifiés avec
leurs références43/46/42 distinctes ;071reste ouverte. Aucun groupe antérieur
n’est réadditionné.

## Réponses perdues des mutations temporaires qualifiées

La [matrice native](CONSOLE_TESTER_TOKEN_LOSS.md) est qualifiée par la
[preuve32](evidence/function-http-client-token-loss-dev-2026-11-12.json) sur392sourcescf5244f5/image96e5dc4e :
création/révocation avant et après commit, watchdog et25régressions. Les
confirmations restent ouvertes avec l’issue non confirmée, sans succès ni rejeu ;
la liste UI retrouve les métadonnées, pas la valeur perdue. Les appels de jeton
préparé donnent200/401 selon la décision durable.32captures inspectées,
deux fonctions des passages nominal/préliminaire purgées, quatre jetons révoqués
et huit observateurs morts.071.3/.8 sont qualifiés avec les références43/42/32
propres ; les groupes des checkpoints ne sont pas additionnés. Le produit et
le manuel18chapitres/74paragraphes restent ceux de42.071.2/.6 demeurent ouverts.

## Domaines refusés et métadonnées courantes qualifiés

Le [complément source](CONSOLE_TESTER_SOURCE.md) qualifie le refus EACCES réel et
la correction du hash sur60938093 : [32groupes](evidence/function-http-client-source-access-dev-2026-11-12.json),
7ciblés/25régressions,395sources28105d2b et32captures inspectées. Hash exact
courant conservé, URL/résultat retirés,503 avant émission, vrais appels témoins,
retour via alias, absence sans code et pilote archivé404 sont recoupés. Les six
handlers, deux révisions et nettoyage natif sont confirmés. Le premier passage
échoué0bb9553f demeure séparé. Le manuel18chapitres/74paragraphes compilé porte
la nouvelle règle. Les anomalies visuelles101/102 restent ouvertes.071.2 garde
la preuve dédiée du chargement ;071.6 l’exception inattendue d’une tâche, et
la clôture exige toujours la campagne complète. Les anciens groupes ne sont
pas réadditionnés et leurs images restent historiques.
