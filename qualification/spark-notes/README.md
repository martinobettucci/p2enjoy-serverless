# Application de qualification P2Enjoy Serverless — DEV

Cette cellule porte le banc de qualification indépendant de P2Enjoy Serverless.
Les douze fonctions et les données sont synthétiques. Aucun code, secret ou
artefact de client n'est déployé.

Le banc sert à vérifier les contrats de handlers HTTP/CommonJS, contexte,
callback, données persistantes, cache, échéance, erreurs et appel entre
fonctions. Il n'est pas encore la plateforme de management : pas de SSO,
d'ACL CRUD, d'autoscaling ou de conteneur par fonction.

Toutes les preuves fonctionnelles sont E2E : un conteneur client distinct
appelle la vraie application déployée, sans mock ni faux service. Une
configuration absente fait échouer la campagne complète ; aucun cas n'est ignoré.
Les scénarios de panne utilisent des conteneurs isolés portant la même image.

Le service Docker est p2enjoy-qualification-dev/qualification. Il est accessible
uniquement sur la boucle locale de la cellule, port 18080. Aucune route
publique ni aucun port de FORGE n'est nécessaire. Il ne dépend d'aucun service
client. La FORGE ne doit pas être modifiée pour exploiter ce banc.
