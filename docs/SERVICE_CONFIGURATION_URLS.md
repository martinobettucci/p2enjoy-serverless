# Configuration commune des services et adresses d’appel

Décision du 8 novembre 2026, à la suite de la précision du responsable.
Unités : [SLS-031](BACKLOG.md#sls-031) et [SLS-066](BACKLOG.md#sls-066).
La configuration commune SLS-031 est déployée et ses parcours ciblés qualifiés
sur DEV : [preuve](evidence/service-configuration-dev-2026-11-08.json). La perte
réelle d’une réponse de modification commune reste à éprouver avant clôture.
Les adresses
multi-domaines SLS-066 restent à réaliser. Le manuel décrit le comportement livré.

## État constaté

La console possède déjà les onglets Configuration et Jetons dans la fiche du
service (`web/src/management.jsx`). L’API conserve les variables et les secrets
chiffrés dans le service, et les jetons portent son identifiant
(`control/app/api.py`). Le moteur fusionne la configuration du service et les
surcharges de fonction (`Deployments.effective`, appelé par l’exécution).

Le défaut initial de représentation de l’adaptateur est reproduit dans la
[preuve avant correction](evidence/service-configuration-defect-dev-2026-11-08.json) :
le provider et chaque fonction étaient fusionnés puis publiés au niveau fonction.
La correction qualifiée conserve maintenant les deux niveaux ; les valeurs
communes ne deviennent plus des surcharges masquant les évolutions du service.
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

Une catégorie absente du provider laisse la configuration de service existante
intacte. Une catégorie explicitement déclarée, même vide ou null, remplace les
clés de cette catégorie au niveau du service. Les clés absentes de la catégorie
déclarée sont retirées. Pour une fonction, une clé locale null retire sa
surcharge et rétablit la valeur du service ; elle ne masque pas cette valeur.
Cette règle remplace l’ancien retrait d’une clé héritée pendant l’aplatissement.
Elle permet de modifier la valeur commune sans redéployer chaque fonction.

La publication doit contrôler les droits nécessaires avant toute mutation
commune : un jeton restreint à des fonctions ne peut modifier le service. Un
changement commun exige Update sur le service. Les modifications concurrentes
doivent être détectées ; un échec partiel est rapporté sans annoncer un
déploiement atomique de toutes les fonctions.

Le rapport distingue l’application de la configuration commune des publications
individuelles. La CLI valide et empaquette tout avant d’appliquer cette
configuration. Elle utilise la version lue du service et demande explicitement
le remplacement du jeu de secrets lorsqu’il est déclaré. Une déclaration de secrets exige Update,
même si les noms sont inchangés : leur valeur enregistrée n’est pas comparable.
Un refus de configuration commune arrête la commande avant toute mutation de
fonction. Après application commune, un échec d’import conserve le code actif
de la fonction concernée, mais la configuration commune a déjà changé pour
toutes les fonctions. Cet effet est visible dans le rapport.

L’API de configuration du service accepte `replace_secrets: true` avec un champ
`secrets` explicite : le mapping remplace alors le jeu précédent dans une seule
transaction. Sans ce drapeau, les ajouts, remplacements et retraits individuels
existants restent disponibles. Ce remplacement autorise notamment 128 nouveaux
noms après 128 anciens sans dépasser la limite de clés de la requête. Le drapeau
est propre au service ; il est refusé dans la configuration d’une fonction.

Avant de modifier le service, vérifier dans la transaction les configurations
effectives de toutes ses fonctions actives, y compris les brouillons. Une collision
variable/secret, un dépassement de 128 clés par catégorie ou de la taille cumulée
autorisée refuse toute la modification sans changer sa version. Les créations et
modifications de fonction appliquent le même contrôle avec le service courant,
notamment après une préparation de stockage. La fusion reste définie en un seul
endroit pour la gestion, la publication et l’exécution.

La CLI borne aussi avant toute mutation la configuration effective qu’elle peut
calculer depuis le manifeste ; deux mappings séparément valides ne rendent pas
leur fusion valide. Les valeurs communes préexistantes absentes du manifeste
restent contrôlées par le serveur, qui est seul détenteur des secrets enregistrés.

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

## Preuve de transport

La preuve de 191 groupes ne couvre pas encore l’état `unknown` d’une mutation
commune dont la réponse est perdue. Ce comportement reste une exigence de SLS-031.
Il faut observer le résultat de la vraie CLI, l’état durable du service et son
audit, puis démontrer qu’aucune publication ni répétition automatique ne suit.

Le banc retenu lance la CLI réelle et observe le processus réel du contrôle
dans le seul SPARK DEV, à une frontière d’appel système. L’interruption avant
traitement de la requête et l’interruption après commit mais avant émission de
sa réponse forment deux scénarios distincts. Un SIGKILL du contrôle réalise la
coupure ; le démarrage de son conteneur original puis sa santé sont confirmés.
Le contrôle et son image restent inchangés pour ce banc.

L’observation native est limitée au processus du contrôle et à la ligne de
requête publique contenant l’UUID du service de campagne. Les identifiants et
secrets d’authentification restent hors des traces. Le registre SQLite est lu
sous son propriétaire pour constater l’état avant et après décision. Les
requêtes et les réponses métier restent produites par les véritables composants.

Avant toute suspension, vérifier la cellule, le conteneur, son image, le service
de campagne et l’absence d’autres travaux actifs. Une garde indépendante borne
la durée de l’observateur, libère une suspension et redémarre le contrôle après
perte du pilote. Sa restauration est elle-même éprouvée. Les identités natives
des processus et conteneurs empêchent d’agir sur un propriétaire remplacé.

Après retour de l’API, vérifier le nombre exact de mutations communes, l’absence
de fonction/candidat créé par la commande interrompue et l’état `unknown` sans
configuration ni secret dans le rapport. Une relance explicite par l’opérateur
doit ensuite publier et invoquer le handler de qualification normalement. Les
ressources sont purgées par l’API et recoupées au repos. Les capacités natives
et outils de diagnostic du SPARK ont été relevés ; le banc reste à implémenter
et à qualifier, sans succès présumé sur ces scénarios.
