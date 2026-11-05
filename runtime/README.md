# Runtime Node DEV

Chargeur de handlers et validation Docker de SLS-030, qualifiés par 36 scénarios
réels sur le SPARK DEV le 6 novembre 2026, zéro échec et zéro test ignoré.
La publication des révisions et le moteur d'invocation restent en développement.
Contrat : [DEPLOYMENT](../docs/DEPLOYMENT.md). Le superviseur contacte le contrôle
par HTTP sur un socket Unix privé monté readonly ; un enfant distinct importe le code. Les logs ne valent
jamais résultat de validation. Le pilote du contrôle impose la limite de quinze
secondes et supprime le conteneur avant de rendre son résultat.

Depuis `/srv/p2enjoy-serverless/runtime`, sur le seul SPARK DEV :

```sh
bash dev.sh build
bash dev.sh test
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
