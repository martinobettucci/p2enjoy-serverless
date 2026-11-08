# Registre d’incohérences

## INC-004 — Le pilote d’alias confond date d’application et configuration

Le premier `apply-authorized-alias` a créé le DNS exact puis la route TLS
autorisée. La projection normale est lisible. Le client s’arrête ensuite parce
que `after.canonical == before.canonical` compare aussi `applied_at` : la console
a réappliqué ses routes et actualisé cette date de 2026-11-06T15:46:27+00:00 à
2026-11-08T21:44:18+00:00. Identifiant, domaine, propriétaire, IP, port 18090,
TLS et activation sont identiques. Le reçu incomplet reste conservé sous
`.local/e2e/invocation-domain-installation.json` ; aucune mutation n’est rejouée.

Issue retenue avant correction : comparer tous les champs matériels de la route,
conserver séparément la date observée ; ajouter une commande de vérification
strictement en lecture seule pour cette installation déjà déclarée. Elle relit
les identités et DNS exacts, compare les propriétés matérielles avec le reçu
initial et attend les vrais HTTPS vérifiés des deux domaines. Le résultat est
distinct de l’essai interrompu. Le recoupement natif et les campagnes API/UI
restent nécessaires avant qualification de cette étape. Retirer l’entrée après
correction et preuve ciblée ; aucun correctif produit ou de FORGE n’est requis.
