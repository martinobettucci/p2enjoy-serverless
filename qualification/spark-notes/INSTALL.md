# Points d'entrée du banc DEV

Ce SPARK n'expose aucun service public. Un opérateur autorisé peut utiliser un
tunnel SSH vers 127.0.0.1:18080 de cette cellule, sans changement de FORGE.

HTTP local :
- GET /healthz : état du serveur de référence ;
- GET /catalog : douze fonctions, identifiants et limites déclaratives ;
- /functions/<nom> : invocation HTTP du handler de qualification.

Les noms sont echo, binary, callback, business, configuration, state, cache,
worker, failure, sleep, spin, relay. Les méthodes figurent dans serverless.yml.
Le handler reçoit event.httpMethod, path, queryStringParameters, headers,
body, isBase64Encoded et un context avec identifiant et temps restant. Il
renvoie statusCode, headers, body et éventuellement isBase64Encoded.

Il n'existe pas encore de jeton de plateforme ni d'intégration SSO. business
exige le secret réel QUALIFICATION_BUSINESS_TOKEN injecté par la cellule, dans
Authorization: Bearer <jeton>. Sans configuration, il répond 503 ; le marqueur
public de l'ancienne démonstration n'est plus une identité acceptée.
Les fonctions failure, sleep et spin sont intentionnellement conçues pour
tester les erreurs et interruptions ; ne pas exposer ce banc sur Internet.

Les données et le cache survivent aux recréations. state, cache et worker
acceptent ?key=<identifiant> ; DELETE supprime seulement la ressource nommée.
Un job worker reçoit items (1 à 128 textes) et calcule réellement ses résultats
PBKDF2 avec checkpoint. Le même job se reprend ; des entrées différentes pour
son identifiant existant sont refusées. Aucun endpoint ne supprime toutes
les données ou les volumes. Aucun appel sortant vers un client ou un cloud
métier n'est nécessaire ; relay vise uniquement les pairs locaux réels echo,
failure ou sleep. Il propage leurs véritables erreurs et timeouts.
