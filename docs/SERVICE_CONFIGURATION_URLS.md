# Configuration commune des services et adresses d’appel

Décision du 8 novembre 2026, à la suite de la précision du responsable.
Unités : [SLS-031](BACKLOG.md#sls-031) et [SLS-066](BACKLOG.md#sls-066).
Ce contrat décrit les corrections à réaliser ; il ne constitue pas une preuve
de livraison. Le manuel continue de décrire le comportement disponible.

## État constaté

La console possède déjà les onglets Configuration et Jetons dans la fiche du
service (`web/src/management.jsx`). L’API conserve les variables et les secrets
chiffrés dans le service, et les jetons portent son identifiant
(`control/app/api.py`). Le moteur fusionne la configuration du service et les
surcharges de fonction (`Deployments.effective`, appelé par l’exécution).

L’adaptateur possède toutefois un défaut de représentation : `adapter/manifest.py`
fusionne le provider et chaque fonction, puis `adapter/deploy.py` publie ces
valeurs fusionnées dans la configuration de chaque fonction. Les valeurs communes
deviennent donc des surcharges qui masquent les évolutions ultérieures du service.
La référence fournie comporte bien `provider.env` et `provider.secret`.

Le contrôle ne connaît actuellement qu’une URL publique configurée. La console
ne présente pas de catalogue d’adresses d’invocation calculées depuis les routes
du SPARK. La passerelle possède déjà les chemins `/invoke/{function_id}` et
`/invoke/{function_id}/{path}`.

## Configuration de service et surcharges

Le service est le niveau commun de gestion des jetons, variables et secrets.
La fonction ne porte que ses différences explicites. Les jetons restent attachés
au service, avec restriction facultative aux fonctions ; il n’est pas nécessaire
de créer un jeton distinct par fonction. Leurs droits CRUD restent inchangés.

L’adaptateur conserve séparément la configuration de `provider` et celle des
fonctions : `provider.env`/`environment` et `provider.secret` alimentent le service,
les déclarations locales alimentent seulement la fonction. Une valeur locale
prend le dessus pour sa catégorie ; une collision variable/secret dans la
configuration effective est refusée. Retirer une surcharge rétablit l’héritage.
Les lectures ne retournent jamais les valeurs des secrets enregistrés.

La publication doit contrôler les droits nécessaires avant toute mutation
commune : un jeton restreint à des fonctions ne peut modifier le service. Un
changement commun exige Update sur le service. Les modifications concurrentes
doivent être détectées ; un échec partiel est rapporté sans annoncer un
déploiement atomique de toutes les fonctions.

Les nouvelles invocations utilisent la configuration commune courante. Une
invocation déjà admise conserve sa configuration jusqu’à sa fin. Les preuves
doivent couvrir les instances chaudes et le redémarrage. La reprise des
déploiements anciennement aplatis ne doit pas déduire qu’une valeur égale à
celle du service est forcément héritée : elle peut être une surcharge volontaire.
Le manifeste explicite sert à rétablir cette distinction lors du redéploiement.

## Domaines du SPARK et chemins d’appel

La source d’autorité est le registre de routes effectivement affectées au SPARK,
exposé par son contrat de cellule, notamment `/etc/spark/routes`. Une proposition
dans `routes.?` n’est pas une route active. L’intégration reste en lecture seule
et ne réalise aucune administration de FORGE.

Retenir seulement les domaines dont la route vise le port de la passerelle
serverless de cette cellule. Un autre service hébergé dans le même SPARK ne
constitue pas une adresse d’invocation. Lire les changements de routes de façon
à supporter leur remplacement par le plan de contrôle. Le mode de publication
TLS ou clair est explicite ; ne pas annoncer un certificat prêt sur la seule
base de la déclaration d’une route.

Pour chaque domaine applicable et chaque événement HTTP de la révision active,
calculer l’URL complète à partir de l’origine publique et du chemin existant :

```text
https://<domaine-affecté>/invoke/<uuid-fonction>
https://<domaine-affecté>/invoke/<uuid-fonction>/<chemin-déclaré>
```

Présenter les méthodes autorisées. Un chemin paramétré reste un modèle à
compléter. Une fonction sans publication ou sans événement HTTP ne reçoit pas
de fausse adresse appelable. Ne pas dériver la liste de confiance d’un en-tête
Host ou X-Forwarded-Host reçu. L’URL SSO canonique reste distincte des domaines
d’invocation supplémentaires ; leur ajout ne modifie pas les callbacks OIDC.

La fiche de fonction affiche les adresses et permet de les copier ; la fiche
du service permet de retrouver les adresses de ses fonctions. Le résultat de
déploiement expose la même information. Les exemples d’appel utilisent un
emplacement pour `X-Serverless-Token`, jamais un jeton ou secret enregistré.
L’absence de domaine applicable est affichée explicitement.

## Preuves et manuel

SLS-031 exige des publications réelles de plusieurs fonctions partageant variables
et secrets, leurs surcharges puis leur retrait, la modification commune après
déploiement, une rotation de secret et les refus de droits. Vérifier les effets
par invocation Docker réelle, la persistance, l’absence de divulgation et les
parcours de console depuis l’accueil. Vérifier aussi le redéploiement d’un
manifeste précédemment aplati et les échecs partiels/concurrents.

SLS-066 exige des appels HTTPS réels à partir des URL copiées, les méthodes et
chemins, plusieurs domaines réellement affectés, l’exclusion des routes vers
un autre port, les retraits de routes et l’absence de route. Aucun domaine,
DNS, TLS, fournisseur SSO ou registre de routes simulé ne vaut preuve. Une
dépendance externe indisponible reste une limite de qualification explicite.

Les deux unités mettent à jour `docs/manual.md` avec le comportement livré,
reconstruisent son affichage dans l’application et vérifient sa correspondance
avec la source. L’interface explique où une valeur est définie et quelle
surcharge est appliquée, sans exposer les valeurs des secrets.
