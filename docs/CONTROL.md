# API du contrôle

Contrat de réalisation SLS-020 ; les preuves et l'état sont dans BACKLOG.
Le contrôle utilise Python/FastAPI, SQLite, HTTPX pour OIDC et PyJWT avec
cryptography pour la validation/chiffrement. Il écoute sur 18090 dans Docker,
avec le réseau hôte du SPARK pour conserver le pair TCP. Les conteneurs de
fonctions gardent leur propre réseau isolé. Un seul processus Uvicorn, sans access log
brut des URLs : le callback OAuth contient des paramètres confidentiels.

## Configuration

Les deux env_file de cellule alimentent le contrôle. Variables requises :
`SERVERLESS_PUBLIC_URL`, `OIDC_ISSUER`, `OIDC_CLIENT_ID`.
Secrets requis : `OIDC_CLIENT_SECRET`, `SERVERLESS_MASTER_KEY` (clé Fernet
aléatoire, encodage URL-safe de 32 octets). Le stockage de métadonnées est
monté dans `/state` ; le chemin interne est constant pour tout déploiement.
Une configuration absente entraîne une erreur explicite, jamais un mode admin
de secours. La clé maîtresse doit rester stable avec la base chiffrée.
L'issuer autorisé par le contrat SSO est exclusivement
`https://oauth.lelabs.tech/realms/lelabs` ; une autre valeur refuse le démarrage.
`SERVERLESS_TRUSTED_PROXIES` est une liste facultative de CIDR séparés par
virgules. Par défaut elle est vide. Le pair TCP fait autorité ; seul un pair
explicitement approuvé permet de lire X-Forwarded-For. Les relais approuvés
sont retirés de droite à gauche ; le premier non approuvé est le client.
Une chaîne absente ou malformée venant d'un proxy approuvé est refusée à 400.
Forwarded et X-Real-IP ne sont jamais utilisés pour identifier le client.

## Connexion

- `GET /healthz` : santé technique et version, sans données d'identité.
- `GET /api/session` : statut authentifié et identité affichable ; un jeton
  CSRF est fourni uniquement à la session correspondante.
- `GET /auth/login` : découverte OIDC, création du flow, cookie temporaire,
  redirection S256 vers le vrai fournisseur.
- `GET /auth/retour` : correspondance state/cookie, consommation du flow,
  échange du code avec verifier, validation ID token (signature, issuer,
  expiration, audience et nonce) et
  access token (issuer, expiration, signature, azp et rôles verified/admin),
  puis session serveur et redirection accueil.
- `POST /auth/logout` : CSRF, révocation locale et fin de session OIDC.

Scopes demandés : openid, profile, email, sans offline_access. Cookies Secure,
HttpOnly, SameSite=Lax, Path=/ ; aucun token OAuth dans le
stockage navigateur. Une session vérifie son expiration à chaque requête.
Au renouvellement du jeton d'accès, les rôles sont revérifiés ; un retrait de
rôle prend donc effet au plus tard à son expiration. Un fournisseur devenu
indisponible n'autorise pas à prolonger un jeton expiré. Le renouvellement est
sérialisé par session, conserve le même subject et ne prolonge pas la limite
absolue de huit heures. La déconnexion locale reste définitive même si le SSO
est injoignable. Les flows de connexion vivants sont bornés à 256 pendant dix
minutes ; un dépassement retourne 429. Le contrôle borne les corps JSON à
256 Kio, y compris les requêtes chunked, et ne renvoie pas leurs valeurs dans
les erreurs de validation.
Les identifiants state et cookies de flow ont exactement 43 caractères
base64url. Une nouvelle tentative remplace le flow précédent du navigateur.
Un callback malformé donne un refus contrôlé, y compris en Unicode.
Une même adresse client ne peut conserver plus de huit flows actifs ni ouvrir
plus de trente flows par fenêtre fixe d'une minute, commencée à sa première
ouverture. Le refus est 429 ; la limite globale reste 256. Les compteurs
persistent avec la base et expirent après leur fenêtre.

## Gestion

Toutes les mutations exigent soit une session admin et un jeton CSRF, soit
le jeton `X-Serverless-Token` portant le droit exact. Les restrictions de jeton
sont vérifiées en base à chaque requête. Les routes globales, les politiques
origine/IP et la gestion de jetons sont réservées aux sessions admin.

- `/api/namespaces` et `/api/namespaces/{id}` : liste, création, modification,
  suppression d'un namespace vide.
- `/api/namespaces/{id}/services` : liste et création des services.
- `/api/services/{id}` : lecture et mise à jour administrateur ; suppression
  d'un service vide. Le Read du service autorise sa lecture expurgée.
- `/api/services/{id}/configuration` : variables et secrets globaux, droit
  Update non restreint à certaines fonctions. La politique d'accès est exclue.
- `/api/services/{id}/functions` et `/api/functions/{id}` : CRUD des brouillons
  de fonctions. Le code et son activation arrivent avec SLS-030/040.
- `/api/services/{id}/tokens`, `/api/tokens/{id}/revoke` et
  `/api/tokens/{id}/rotate` : administration des jetons. Valeur complète
  uniquement dans la réponse de création/rotation ; ensuite id, préfixe,
  droits, portée, expiration et état.
- `/api/services/{id}/audit` : consultation paginée selon Read.

Les listes sont bornées et paginées. Les objets étrangers au service d'un
jeton ne sont jamais accessibles, y compris par ID deviné. Les requêtes de
configuration rejettent les champs inconnus. Les conflits de nom sont des
409, les validations des 422, l'absence d'identité un 401 et l'absence de droit
un 403. L'authentification est vérifiée avant la divulgation des données.
Les noms de fonctions conservent la casse des clés du manifeste ; ils acceptent
lettres ASCII, chiffres, tirets et underscores, avec un premier caractère
alphanumérique et une longueur maximale de 63 caractères.

Les valeurs de secret null demandent leur suppression ; une valeur chaîne
les crée ou remplace. Les lectures montrent uniquement les noms. Une variable
et un secret ne peuvent partager un nom dans le même niveau de configuration.
Les champs de ressources sont des contrats stockés jusqu'à l'intégration du
runtime ; leur seule sauvegarde ne constitue pas une preuve d'application.
Les mises à jour acceptent `If-Match` portant la valeur `updated_at` lue.
La console l'envoie systématiquement : si l'objet a changé depuis l'ouverture,
le serveur refuse à 409 et conserve l'objet courant. La saisie reste ouverte
pour consultation, annulation et relecture ; aucune section obsolète n'est
réécrite silencieusement depuis un autre onglet. Les clients de déploiement
peuvent aussi employer ce contrôle de concurrence.

## Console du contrôle

La première tranche de console appartient à SLS-020 : connexion, consultation
de session, namespaces, services, brouillons de fonctions, configuration et
jetons. Le runtime, le code et les mesures rejoignent les vues au fil des unités
suivantes. La console React/Vite est compilée dans l'image du contrôle ; ses
appels sont de même origine et utilisent exclusivement les API ci-dessus.
L'accueil et `/console/*` servent son document, `/assets/*` ses fichiers figés.
Les erreurs du callback sont présentées sur l'accueil quand le client accepte
HTML, sans mettre code OAuth ni jeton dans l'URL d'erreur. Un refus de l'entrée
`/auth/login` conserve son statut HTTP et Retry-After, y compris dans un
navigateur : la console reçoit le message initial dans un attribut HTML
échappé et l'affiche comme texte. Le callback reste redirigé pour retirer
ses paramètres confidentiels de l'adresse.
Le guide d'utilisation correspondant est [manual.md](manual.md).

## Preuves

La campagne cible le vrai contrôle déployé, la base réelle et le SSO réel.
Les comptes permettent de qualifier admin, verified sans admin et absence de
verified. Les jetons créés depuis le parcours normal servent aux preuves CRUD
et interservice. Les assertions couvrent aussi CSRF, rotation, révocation,
expiration, configuration expurgée, conflits, redémarrage et absence de fuite
dans les journaux. Aucun mode bootstrap authentifié artificiellement n'est
ajouté pour remplacer une preuve de connexion.
La preuve du proxy relève le pair TCP réel, compare le chemin TLS et les
chemins directs, puis forge les en-têtes transmis pour vérifier qu'ils ne
changent pas le client retenu. Une adresse de proxy n'est configurée comme
approuvée qu'après cette mesure. Les logs de refus conservent le pair TCP et
les adresses X-Forwarded-For valides, sous l'étiquette « untrusted », pour
diagnostiquer la chaîne ; aucune valeur libre d'en-tête n'y est recopiée.

Les défauts de démarrage sont exercés sur la même image immuable dans des
conteneurs DEV isolés, alimentés par les deux env_file officiels. Le pilote
retire ou altère explicitement un paramètre dans le seul processus du scénario
négatif, ou rend son propre volume de métadonnées non inscriptible. Il ne
modifie pas les fichiers de cellule ni l'état du contrôle permanent. Une clé
maîtresse différente doit refuser la base créée lors du scénario précédent ;
la clé originale doit permettre sa reprise. Les journaux de ces refus ne
doivent révéler aucune valeur secrète. Ces injections de panne ne remplacent
ni le contrôle, ni sa base, ni le fournisseur SSO par une simulation.
Chaque rapport de campagne comporte un indicateur de fin `completed` et un
échec explicite si le pilote s'interrompt. Un rapport partiel ne constitue
jamais une campagne réussie, même si ses contrôles précédents sont verts.
