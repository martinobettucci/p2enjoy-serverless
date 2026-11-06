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
```

`python3 e2e/proxy.py --expected-proxy 10.77.0.1` s'exécute depuis le poste et
mesure les chemins réseau via HTTPS et SSH. Les pilotes `login-limits.py`,
`login-capacity.py` et `control-operations.py` s'exécutent comme `spark-docker`
dans le SPARK DEV. Les deux premiers exercent les limites SSO ; `login-limits`
redémarre aussi le contrôle. Le dernier utilise des conteneurs temporaires de son image immuable pour les
pannes de configuration, de clé et de base. Les fichiers `.proof-*.json`
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
exportés. Les deux campagnes suivantes exigent cette vraie session ; son
absence fait échouer leur prérequis.

`control-admin.mjs` crée ses propres objets, qualifie les droits CRUD et
redémarre le conteneur de contrôle du SPARK DEV pour éprouver la persistance.
`control-ui.mjs` crée ses objets depuis la console et augmente temporairement
la latence réelle de Chromium pour vérifier un envoi en cours ; il ne remplace
aucune réponse. Les deux nettoient uniquement les objets qu'ils ont créés.

Les scripts et preuves sont ajoutés au rythme de SLS-020 à SLS-060. Les premiers
contrôles publics ont réussi ; les campagnes administrateur et la campagne
complète de plateforme ne sont pas encore réussies.
La campagne publique comporte sept groupes : découverte OIDC et clés réelles,
santé TLS, ressources de la console, refus anonymes, callbacks malformés,
flows et refus du fournisseur, puis bornes des corps. La cible d'autorisation
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
