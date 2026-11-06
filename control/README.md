# Plan de contrôle

Implémentation en cours de SLS-020. Contrats : [API](../docs/CONTROL.md),
[schéma](../docs/SCHEMA.md), [SSO](../docs/sso.md).

Python 3.14, FastAPI, SQLite WAL et authentification OIDC confidentielle.
Les identités et les objets de gestion persistent sous `/state`. La clé
maîtresse et le secret client proviennent de la cellule, avec les autres
paramètres documentés dans CONTROL. Aucun profil PREPROD/PROD.

Depuis `/srv/p2enjoy-serverless/control` dans le SPARK DEV, comme spark-docker,
exécuter séquentiellement :

```sh
bash dev.sh build
bash dev.sh up
bash dev.sh status
```

`bash dev.sh logs` affiche les logs bornés ; `bash dev.sh stop` arrête le
contrôle en conservant la base. Le build utilise les sources voisines `web/`
et ses dépendances verrouillées. L'image sert la console et l'API sur 18090,
dans le réseau hôte du SPARK ; `/state` monte le répertoire durable de métadonnées.
Les deux env_file officiels de la cellule fournissent la configuration.

Les contrôles publics, de l'accueil, du réseau, des limites SSO et les
17 scénarios de panne ont réussi sur DEV. Les scénarios authentifiés restent
à qualifier avec une session SSO. Ce répertoire n'est
donc pas encore un contrôle intégralement qualifié. Les preuves SLS-020
emploient le vrai SSO et les véritables API, sans authentification substituée.

`app/validator.py` fournit le pilote de chargement Node de SLS-030. Sa CLI
est qualifiée sur le SPARK avec le runtime isolé, selon
[runtime/README.md](../runtime/README.md). Elle n'est pas encore reliée aux
routes du contrôle ni incluse dans son image déployée ; l'upload et les
révisions restent la prochaine étape.

`app/artifacts.py` fournit l'extraction bornée des ZIP classiques. Sa CLI
vérifie les en-têtes, les tailles réelles, les CRC et les chemins, écrit dans
un candidat privé puis publie un répertoire readonly sans écraser une
destination existante. L'image dédiée ne remplace pas le contrôle en service.
Depuis ce répertoire dans le SPARK DEV, construire puis qualifier en série :

```sh
bash artifacts-dev.sh build
bash artifacts-dev.sh test
```

La campagne appelle l'image immuable, le packager existant et le validateur
Node ; 112 contrôles réussissent, zéro échec et zéro test ignoré sur le SPARK
le 6 novembre 2026. La [preuve conservée](../docs/evidence/artifacts-dev-2026-11-06.json)
recoupe les sources locales/distantes et le code embarqué.
Son rapport `artifacts-proof.json` n'est valide que si `completed` et
`cleanup` valent true. Cette étape ne fournit pas encore les routes d'upload
et de publication des révisions.
