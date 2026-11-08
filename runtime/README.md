# Runtime Node DEV

Chargeur de handlers et validation Docker de SLS-030, qualifiés par 36 scénarios
réels sur le SPARK DEV le 6 novembre 2026, zéro échec et zéro test ignoré.
Le pilote d’instances chaudes et son superviseur sont implémentés ; leurs
campagnes réelles passent 31 contrôles d’invocation et 11 de cycle de vie,
avec les 36 régressions du chargeur : [preuve](../docs/evidence/instances-dev-2026-11-06.json). La passerelle authentifiée et les admissions passent 31 groupes HTTPS dans
la [preuve du moteur](../docs/evidence/execution-dev-2026-11-06.json). Les instances avec baux
de stockage passent quatorze groupes réels, selon [la preuve de raccordement](../docs/evidence/managed-storage-dev-2026-11-06.json).
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
le conteneur réel du contrôle ; l'intégration aux API de publication passe
les onze groupes de la [preuve authentifiée](../docs/evidence/deployment-authenticated-dev-2026-11-06.json).

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
par fonction utilise désormais ManagedInstance et le client réel de l’agent.

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
secondes. SIGKILL du diagnostic exige une réconciliation par l’exploitant. Les instances
créées par la plateforme sont réconciliées automatiquement au démarrage de
son moteur, avant réouverture des admissions.

`instances-test` utilise la CLI en processus séparé, les handlers originaux
embarqués dans l’image de qualification, le réseau HTTPS réel et Docker.
`lifecycle-test` exerce directement les méthodes du même pilote pour les
appels concurrents, sans importer les handlers ni remplacer un composant.
Ses refus de suppression proviennent de permissions réellement retirées puis
rétablies. L’avertissement Python de retrait du socket refusé est attendu dans
ce seul scénario. La campagne dispose d’une alarme indépendante de 90 secondes.
Les rapports sont `instances-proof.json` et `lifecycle-proof.json` ; `completed`
et `cleanup` doivent valoir true, `failed` et `skipped` zéro.

Le [complément du canal privé](../docs/evidence/private-channel-lifecycle-dev-2026-11-08.json)
rejoue les onze groupes de cycle de vie sur le même serveur. Le client envoie
ses petites requêtes complètes sur le vrai socket et lit la réponse bornée :
415 reçu avant le corps annoncé, puis vingt vrais 415 sans rejeu. Cela corrige
un BrokenPipe du client qui séparait en-têtes et corps ; sa cause exacte reste
une inférence, faute de réponse lue dans l’arrêt initial. Cet arrêt est conservé
séparément, avec dix groupes partiels et nettoyage natif recoupé. Aucun code
du pilote, du superviseur ou des handlers ne change pour ce complément.

Ces preuves de composants ne qualifient pas la file, l’autoscaling, les ACL d’invocation,
les générations, les montages fonctionnels ni les opérations de console.

## Baux de stockage

Le diagnostic exécuté dans le contrôle accepte `--managed-storage`. Sa première
trame contient `environment`, `secrets` et `storage`, avec exactement `data`
et `cache`, chacun défini par `enabled` et `quota_mib`. Les quotas doivent déjà
avoir été configurés par l'agent pour l'UUID de fonction. Les chemins libres
`mounts` sont alors refusés ; les binds proviennent uniquement de l'acquisition
réelle du bail. `--docker-socket /docker.sock`, `--work` dans `/state` et
`--host-work` désignent les chemins respectivement vus par le contrôle et Docker.
Cette entrée exige l'accès opérateur Docker.

Sur le SPARK DEV, comme root et après la fin des autres campagnes :

```sh
python3 -B /srv/p2enjoy-serverless/e2e/managed-storage.py
```

Ce client charge la classe réellement embarquée dans le contrôle et invoque
les handlers Docker. Il provoque des suspensions de l'agent, la mort d'un démon
FUSE appartenant à sa fonction, puis un arrêt/démarrage de l'agent. Il restaure
le service, détruit ses instances et purge ses fonctions temporaires. Son
rapport `runtime/managed-storage-proof.json` exige completed/cleanup vrais,
failed/skipped à zéro. Il vérifie aussi la CLI gérée et sa fermeture sur EOF.
