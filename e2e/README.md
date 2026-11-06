# Qualification de la plateforme

Les clients de ce répertoire visent exclusivement le déploiement DEV réel.
Ils n'importent pas les handlers, ne créent pas de serveur substitué et
n'interceptent aucune réponse réseau. Le navigateur utilise la connexion SSO
normale. Un accès absent est une erreur de prérequis, jamais un test ignoré.

Installer les dépendances par `npm ci`, puis le navigateur par
`npx playwright install chromium`. Exécuter un seul scénario à la fois.
Les captures et fichiers contenant une session sont conservés uniquement
sous `.local/`, ignoré par Git. Ne jamais publier un état de navigateur.

Depuis la racine du dépôt, chaque commande attend la fin de la précédente :

```sh
python3 e2e/public.py
node e2e/login-ui.mjs
node e2e/authorize.mjs
node e2e/control-admin.mjs
node e2e/control-ui.mjs
node e2e/deployments.mjs
node e2e/adapter-deploy.mjs
```

`python3 e2e/proxy.py --expected-proxy 10.77.0.1` s'exécute depuis le poste et
mesure les chemins réseau via HTTPS et SSH. Les pilotes `login-limits.py`,
`login-capacity.py` et `control-operations.py` s'exécutent comme `spark-docker`
dans le SPARK DEV. Les deux premiers exercent les limites SSO ; `login-limits`
redémarre aussi le contrôle. Le dernier utilise des conteneurs temporaires de son image immuable pour les
pannes de configuration, de clé et de base, le verrou exclusif d’état et la
reprise de maintenance après une contention SQLite réelle. Les fichiers `.proof-*.json`
produits sous `/srv/p2enjoy-serverless/control` contiennent les résultats
expurgés. Leurs ressources temporaires sont nettoyées après chaque campagne.
`python3 e2e/report-interruption.py`, depuis le poste après `public.py`, tue
réellement un client de preuve après son premier échange HTTP, vérifie que
l'ancien rapport réussi est invalidé, puis rejoue la campagne publique.
Les rapports ne valent que lorsque `completed` est vrai et les nettoyages
réussis ; leur initialisation précède les prérequis externes.

`authorize.mjs` ouvre Chromium sur l'accueil de la console et laisse jusqu'à
huit heures au détenteur du compte pour démarrer la connexion SSO. Aucun flow
OAuth n'est créé avant son clic, ce qui évite une expiration pendant l'attente.
Le script ne lit aucun champ de mot de passe.
Il conserve seulement le cookie de plateforme, sous `.local/e2e/` en mode
0600, puis ferme le navigateur. Les cookies du fournisseur ne sont pas
exportés. Les campagnes de gestion et de publication exigent cette vraie session ; son
absence fait échouer leur prérequis.

`control-admin.mjs` crée ses propres objets, qualifie les droits CRUD et
redémarre le conteneur de contrôle du SPARK DEV pour éprouver la persistance.
`control-ui.mjs` crée ses objets depuis la console et augmente temporairement
la latence réelle de Chromium pour vérifier un envoi en cours ; il ne remplace
aucune réponse. Les deux nettoient uniquement les objets qu'ils ont créés.

Les scripts et preuves sont ajoutés au rythme de SLS-020 à SLS-060. Les premiers
contrôles publics, les 19 groupes API administrateur et les 11 parcours UI
ont réussi avec nettoyage confirmé. La [preuve de gestion](../docs/evidence/control-management-dev-2026-11-06.json)
recoupe l'image et les sources ; les cycles de rôles et de clés SSO ainsi que
la campagne complète de plateforme restent ouverts.
La campagne publique comporte huit groupes : découverte OIDC et clés réelles,
santé TLS, ressources de la console, refus anonymes, callbacks malformés,
flows et refus du fournisseur, bornes des corps, puis refus anonymes des routes
de publication. Un upload HTTPS utilisant Expect: 100-continue est refusé
avant l’envoi du corps de 64 Mio annoncé. La cible d'autorisation
est comparée à la découverte fraîchement lue. Les règles de client et de rôle
restent à éprouver par leurs parcours authentifiés.

`python3 e2e/adapter.py` exécute les vraies commandes plan/package sur une
copie temporaire des fichiers de qualification. Il examine les ZIP produits
et exerce les refus, les liens physiques/symboliques ainsi qu'une course
réelle sur le répertoire de sortie. Le même pilote est inclus dans l'image
E2E de l'adaptateur et lancé sur le SPARK par `bash adapter/dev.sh test`.
Sa preuve porte sur la CLI et les fichiers ; elle n'invoque aucun handler et
ne remplace pas les preuves HTTP de déploiement ou d'exécution à venir.

`runtime-validation.py`, lancé sur le SPARK par `bash runtime/dev.sh test`,
exécute le pilote Docker réel de validation. Il utilise les variantes originales
de `qualification/artifacts/`, la vraie dépendance YAML, les valeurs applicatives
de cellule et le contrôle déjà déployé pour éprouver les permissions du socket.
Il vérifie chargement, refus, limites, logs et destruction des descendants ;
son rapport est `runtime/validation-proof.json` sur le SPARK. Il ne prouve pas
encore les autorisations de publication ni l'invocation des handlers.

`artifacts.py`, lancé dans le SPARK par `bash control/artifacts-dev.sh test`,
fabrique des archives réelles et appelle la CLI d'extraction dans son image
Python. Il vérifie les fichiers produits, leurs empreintes et permissions,
les erreurs de format, les bornes, une saturation effective du disque et
des courses sur les destinations et la source. Le dernier parcours empaquette
l'application de qualification, extrait son ZIP puis charge son handler avec
le véritable runtime Node. Le rapport est `control/artifacts-proof.json`.

`deployments.mjs` empaquette les handlers originaux par la CLI réelle, puis
crée namespace, service, fonctions et jetons par les API de gestion normales.
Le chargement asynchrone de `qualification/artifacts/deployment-delay.mjs`
permet les modifications concurrentes réelles pendant la validation Docker.
Les assertions portent sur droits, candidats, import, révisions, révocation,
conflits, admission unique, rollback et suppression des révisions inactives.
Les archives conservées à la suppression d’une fonction sont recensées dans
le rapport ; ce nettoyage de gestion n’est pas une purge d’archives.
Cette campagne exige la session SSO et n’est pas encore réussie. Les limites
globales, l’expiration, la reprise après crash et les parcours CLI/UI complets
restent des preuves distinctes à ajouter et exécuter.

`adapter-deploy-public.py`, exécuté sur le SPARK par `bash adapter/dev.sh
deploy-public-test`, appelle de vrais processus CLI pour les prérequis,
les bornes de configuration et le refus 401 de la véritable API HTTPS DEV.
`adapter-deploy.mjs` crée ses jetons par la session SSO puis lance la vraie
commande deploy : onze fonctions imposent une pagination, un import qui
lève réellement une erreur produit un résultat partiel, et un brouillon
refusé est repris avec Read/Create. Les révisions archivées à la suppression
sont recensées. La campagne authentifiée reste en échec de prérequis.

`runtime-instances.py` exerce le diagnostic réel en processus séparé : enfants
neufs dans un conteneur chaud, corps aux limites, callbacks, ESM et dépendances,
confinement, logs, mesures Docker, HTTPS sortant, descendants, mémoire/PIDs,
timeouts, signaux et imports bloquants. Une suspension SIGSTOP/SIGCONT du pilote
vérifie qu’un résultat en attente ne devient pas un succès après la deadline.
`instance-lifecycle.py` appelle les méthodes réelles du pilote avec Docker et
son canal Unix pour les courses de démarrage/fermeture, annulations répétées,
nettoyage filesystem refusé puis repris, IDs étrangers, doublons et bornes du
canal. La clé testée est celle de cette instance réelle ; aucun jeton public
ni handler de substitution n’est créé. Un second démarrage refusé doit laisser
l’instance existante utilisable. Les commandes sont `bash runtime/dev.sh
instances-test` puis `bash runtime/dev.sh lifecycle-test`, sur le SPARK.
Les rapports se trouvent dans `runtime/`. La passerelle et les admissions
restent hors de ces preuves de composants.
