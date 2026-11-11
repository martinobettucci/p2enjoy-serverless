# Attente de droits et reprise des sessions SSO

Contrat de réalisation [SLS-089](BACKLOG.md#sls-089), décidé le11 novembre2026
avant implémentation. Les preuves réelles encore absentes laissent l'unité ouverte.

## Attente de droits

Le serveur valide les signatures, issuer, audience, azp, nonce et concordance
des subjects avant de décider des rôles. Il exige toujours `verified` et `admin`.
Un rôle absent donne403 avec `access_requirement`, enum `verification` ou
`administration`. Ce résultat métier se distingue des erreurs techniques.

Un callback valide sans ces droits redirige le navigateur vers
`/auth/attente?reason=verification` ou `reason=administration`. Cette page publique
est purement informative : ni identité, ni jeton CSRF, ni accès aux objets.
Elle explique la demande à adresser à un administrateur du SSO et propose
**Vérifier mon accès**, qui reprend `/auth/login` et obtient des rôles frais.
Elle n'affirme pas qu'une attribution sera automatique. Une URL saisie à la main
n'établit aucune identité. Une raison inconnue est refusée à400.

Après validation complète de l'identité et du nonce au callback, la précédente
session de ce navigateur est révoquée avant la décision de droits. Un callback
malformé ou à signature invalide ne ferme pas cette session. Un refus de rôle
en cours de session ferme cette session et efface son cookie ; le client se
dirige vers la page d'attente fixe correspondant à l'enum, sans cible libre.

Ce choix évite une nouvelle catégorie de session autorisée partiellement et
la conservation de jetons OAuth pour des comptes auxquels la console est fermée.

## Identité du destinataire

L'access token exige toujours `azp` égal au client configuré. L'ID token exige
son audience ; si `azp` est présent, sa valeur doit être le même client. Avec
plusieurs audiences, `azp` est obligatoire. Une audience unique peut l'omettre.
Ce contrôle complète la signature et ne s'y substitue pas ; voir
[OIDC Core3.1.3.7](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation).

## Clés et renouvellement temporairement indisponibles

Le cache JWKS dure300s et les tentatives sont espacées de2s, mesurées sur
l'horloge monotone. Un `kid` absent ou un cache périmé dans cette fenêtre donne
503 avec `Retry-After` de1 ou2 secondes. Aucune clé périmée ne contourne ce refus.
Une clé encore inconnue après une consultation JWKS réussie reste un401.
Un503 ne révoque pas la session, ne prolonge aucun `exp` et n'accorde aucun accès.
La console propose **Réessayer** pour relire sa session, sans imposer une connexion.

Si l'échange réel de rafraîchissement a reçu de nouveaux jetons mais que leur
validation échoue temporairement à503, le serveur conserve `pending_tokens`
dans le payload déjà chiffré de la session. Il ne change ni subject, ni CSRF,
ni expiration d'accès vérifiée, ni échéance absolue. Au prochain appel il
revalide ces jetons avant tout autre échange. Cela conserve un refresh token
que le fournisseur peut avoir fait tourner, sans tenir des claims non vérifiés
pour une autorisation. Un401/403 détruit toujours la session.

L'écriture est un UPDATE conditionné à la présence, au cipher courant et à
l'expiration de la session, jamais un INSERT. Une déconnexion concurrente ne
ressuscite aucune session. Le verrou par session sérialise ses renouvellements ;
le recheck d'une opération refuse un cipher modifié. La déconnexion tente la
fin de session avec le refresh pending lorsqu'il existe, après révocation locale.
Le format est additif dans `tokens_cipher` : aucune migration SQL ni variable
de cellule. La perte du corps de réponse avant réception reste une panne
différente ; elle n'est pas présentée comme résolue par cette conservation.

## Qualification réelle et données de test

Seul le compte administrateur déjà autorisé est disponible. Les profils sans
`verified` et avec `verified` seul, ainsi qu'une rotation réelle de signature,
demandent l'autorité externe du cas4. Aucun compte ni rôle n'est créé ou retiré
par cette application ; aucune API d'administration Keycloak n'est appelée.
Il n'existe pas de seed local d'identités, de clés privées ou de faux fournisseur.

Le client E2E reçoit les identifiants par stdin privée. Il parcourt l'accueil,
le SSO et les API réelles, mesure `exp-iat=300` sur le JWT effectivement émis
et vérifié, attend l'échéance réelle puis observe le renouvellement sans changer
le cookie de plateforme. Seuls durées, dates et empreintes utiles quittent le
serveur ; aucun jeton OAuth ou secret n'entre dans les rapports.

Les vues publiques d'attente peuvent être parcourues directement au clavier
sur ordinateur/mobile ; ces captures ne prouvent pas la décision d'autorisation
pour un compte réel sans rôle. Un JWT dont on change le payload sans signature
valide ne discrimine pas le contrôle azp : son rejet ne clôture pas ce critère.
Les parcours discriminants des deux profils et de rotation restent explicitement
ouverts jusqu'à leur exécution, sans mock, simulation ni test ignoré.
