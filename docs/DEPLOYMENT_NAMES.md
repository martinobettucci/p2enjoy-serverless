# Noms d’exploitation et domaine de la plateforme

Unité SLS-011. La cible reste le SPARK de développement `infra-serverless`.
Le domaine `lelabs.tech` désigne déjà cette infrastructure ; l’adresse de la
console est `https://serverless.lelabs.tech`.

| Nom Docker visible | Rôle | Entrée |
| --- | --- | --- |
| `serverless-api` | API de gestion, SSO et console web | HTTP 18090, route TLS publique |
| `serverless-runtime-reference` | Exécuteur Node autonome des douze fonctions de qualification | Boucle locale 127.0.0.1:18080 |

Les tests sont des clients éphémères distincts. Le runtime de référence exécute
réellement les handlers. Il reste séparé du pilote d’instances Docker de la
plateforme, dont le raccordement aux invocations publiques est en cours.

Les noms explicites `container_name` remplacent les noms générés par Compose.
Les identifiants de projet et de service Compose restent stables : ils
identifient les ressources existantes, notamment les trois volumes du banc et
son DNS interne `qualification`. Le bind durable `/state`, les volumes,
les ports, les images et les profils DEV sont conservés. Les scripts opérateur
qui ciblent un nom Docker utilisent les nouveaux noms. Les preuves historiques
gardent les noms observés à leur date.

La bascule de domaine associe la route TLS sur **18090**, la variable officielle
`SERVERLESS_PUBLIC_URL` et les URL OIDC de retour/déconnexion. Le client existant
`p2enjoy-serverless-dev` garde son identifiant et son secret. La déclaration
complète est mise à jour sans recréer le client. L’ancien domaine peut rester
temporairement routé pendant la transition ; sa suppression ne précède pas
la vérification de la nouvelle entrée HTTPS et du retour SSO accepté.

## Preuve de migration

1. Relever les images, montages, volumes, identité durable et santé avant
   changement. Créer compteur, cache et travail partiel par HTTP avec le client
   existant `probe.cjs before-recreate`.
2. Recréer chaque service en série avec son nom explicite. Vérifier les mêmes
   volumes et les observations HTTP conservées avec `after-recreate`, dont la
   reprise du calcul et le nettoyage de ses seules ressources.
3. Appliquer route et variable via les propositions officielles du SPARK.
   Vérifier TLS normal, santé, ressources UI, anonymat, OIDC/PKCE et provenance
   réseau sur le nouveau domaine ; rejouer les 38 tests HTTP du banc.
4. Exiger une connexion SSO réelle pour la session du nouveau domaine. Une
   session de l’ancien domaine ne se copie pas et ne vaut pas preuve du nouveau
   parcours authentifié. Nommer séparément toute preuve encore ouverte.
5. Actualiser puis relire les trois notes de cellule. Conserver les empreintes
   et résultats expurgés dans une nouvelle preuve, sans modifier l’historique.

Un retour aux anciens noms utilise les mêmes projets, services et montages.
Un retour d’URL exige une route et des URL OIDC encore autorisées. Aucun geste
de cette migration ne supprime de volume ni ne change le schéma SQLite.
