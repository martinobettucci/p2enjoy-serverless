# Runtime Node DEV

Chargeur de handlers et validation Docker de SLS-030, qualifiés par 36 scénarios
réels sur le SPARK DEV le 6 novembre 2026, zéro échec et zéro test ignoré.
Le pilote d’instances chaudes et son superviseur sont implémentés ; leurs
campagnes réelles passent 31 contrôles d’invocation et 11 de cycle de vie,
avec les 36 régressions du chargeur : [preuve](../docs/evidence/instances-dev-2026-11-06.json). La passerelle
authentifiée, les admissions et les volumes par fonction restent à intégrer.
Contrat : [DEPLOYMENT](../docs/DEPLOYMENT.md). Le superviseur contacte le contrôle
par HTTP sur un socket Unix privé monté readonly ; un enfant distinct importe le code. Les logs ne valent
jamais résultat de validation. Le pilote du contrôle impose la limite de quinze
secondes et supprime le conteneur avant de rendre son résultat.

Depuis `/srv/p2enjoy-serverless/runtime`, sur le seul SPARK DEV :

```sh
bash dev.sh build
bash dev.sh test
bash dev.sh instances-test
bash dev.sh lifecycle-test
```

Exécuter ces commandes séquentiellement. La construction utilise Node 24 épinglé
et la cible de qualification embarque les variantes originales du dépôt avec
la dépendance YAML verrouillée de l'application témoin. Le pilote E2E lance le
vrai validateur en processus séparé, qui contacte Docker et le superviseur par
leurs sockets réels. Aucun serveur de remplacement ni authentification factice.

Le superviseur tourne en UID 0 interne, correspondant à `spark-docker` dans
Docker rootless, comme le contrôle. Son répertoire de socket est 0700 et son
socket 0600. Toutes les capacités sont retirées ; code readonly, réseau coupé,
512 Mio, 0,25 CPU, 64 PIDs et `/tmp` 16 Mio. Le transport est vérifié depuis
le conteneur réel du contrôle ; son intégration aux API reste à réaliser.

La commande `python3 -m control.app.validator` reçoit sur stdin un objet JSON
avec `environment` et `secrets`, et retourne un diagnostic JSON expurgé. Les
arguments désignent seulement l'image, le code, le répertoire de travail et le
handler. La campagne ne prouve pas encore l'upload ni la publication authentifiés.

## Instances chaudes

Contrat : [EXECUTION](../docs/EXECUTION.md). `control/app/instances.py` pilote
le véritable démon Docker ; `invoke-supervisor.mjs` garde le conteneur prêt,
`invoke-child.mjs` lance chaque handler dans un enfant neuf. Le conteneur et son
réseau dédié sont supprimés après timeout, disparition ou défaut du protocole.
La fermeture rejoint les opérations système et confirme la suppression avant
retrait du canal. Les montages déclarés exigent le type FUSE réel ; leur gestion
par fonction dépend encore de l’agent de stockage.

Le diagnostic s’exécute depuis la racine du dépôt sur le SPARK :

```sh
python3 -B -m control.app.instances --image SHA256_IMAGE --code CHEMIN_CODE_HOTE \
  --work REPERTOIRE_PRIVE --installation UUID_INSTALLATION --function-id UUID_FONCTION \
  --revision-id UUID_REVISION --handler invoke.cjs.handler --function-name diagnostic
```

Il exige le socket Docker de l’opérateur. Le premier objet JSON sur stdin porte
`environment`, `secrets` et éventuellement `mounts`. Les suivants portent
`operation: invoke` avec `event` et `timeout_seconds`, `operation: stats` ou
`operation: close`. Les résultats JSON restent privés : une réponse métier
peut contenir les informations que son handler choisit de renvoyer. Seuls les
logs sont expurgés des secrets déclarés. La clé du canal n’est jamais imprimée.
SIGTERM et SIGINT rejoignent le nettoyage ; stdin et stdout n’immobilisent pas
la boucle de contrôle. Une sortie consommée trop lentement est bornée à dix
secondes. SIGKILL exige une réconciliation par l’exploitant ; l’intégration de
cette réconciliation au démarrage du moteur reste à réaliser.

`instances-test` utilise la CLI en processus séparé, les handlers originaux
embarqués dans l’image de qualification, le réseau HTTPS réel et Docker.
`lifecycle-test` exerce directement les méthodes du même pilote pour les
appels concurrents, sans importer les handlers ni remplacer un composant.
Ses refus de suppression proviennent de permissions réellement retirées puis
rétablies. L’avertissement Python de retrait du socket refusé est attendu dans
ce seul scénario. La campagne dispose d’une alarme indépendante de 90 secondes.
Les rapports sont `instances-proof.json` et `lifecycle-proof.json` ; `completed`
et `cleanup` doivent valoir true, `failed` et `skipped` zéro.

Ces preuves ne qualifient pas encore la file, l’autoscaling, les ACL d’invocation,
les générations, les montages fonctionnels ni les opérations de console.
