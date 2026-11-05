# Stockage des fonctions

`p2-quota` monte un répertoire natif avec un plafond de taille logique. Il passe
31 contrôles E2E réels dans le SPARK DEV ; son intégration au moteur reste à
réaliser. [Preuve](../docs/evidence/storage-dev-2026-11-05.json).
Contrat : [PLATFORM, stockage](../docs/PLATFORM.md#stockage).

Prérequis : Linux, `/dev/fuse`, `fusermount3`, Docker pour construire le binaire.
Le propriétaire du répertoire exécute le binaire. Aucun accès à un périphérique
bloc ni au stockage de la FORGE n'est nécessaire.

```sh
docker build -t p2enjoy-quota-build:dev storage
docker create --name p2enjoy-quota-export p2enjoy-quota-build:dev
docker cp p2enjoy-quota-export:/p2-quota /tmp/p2-quota
docker rm p2enjoy-quota-export
mkdir -p /tmp/quota-data /tmp/quota-mount
/tmp/p2-quota -backing /tmp/quota-data -mount /tmp/quota-mount -bytes 16777216
```

Le processus reste au premier plan. `-direct` utilise l'appel mount du noyau
et exige CAP_SYS_ADMIN dans la cellule ; ce mode sert lorsque le helper
fusermount3 ne fonctionne pas dans l'environnement. Cette capacité appartient
au seul processus de montage, jamais aux fonctions Docker.
SIGTERM/SIGINT démonte proprement ; un
montage occupé doit être libéré par l'arrêt de ses consommateurs. Les données
restent dans le backing. Deux propriétaires simultanés du même backing sont
refusés par `flock`. Le scan initial refuse une limite sous l'usage, les liens
et fichiers spéciaux. Le répertoire du montage doit être vide et distinct.

Le plafond compte chaque taille logique arrondie à 4 Kio, plus 4 Kio par fichier
ou répertoire. Un fichier supprimé mais encore ouvert reste facturé jusqu'au
dernier close. Un dépassement rend EDQUOT ; des opérations hors contrat rendent
EOPNOTSUPP. Les données sont écrites dans les fichiers natifs du SPARK.

Les runtimes ne doivent monter que le chemin FUSE, après vérification de son
type. Ils ne reçoivent jamais le backing, qui reste privé à l'agent de stockage.
`client.py` effectue les opérations à travers ce montage réel depuis un
conteneur Docker distinct. `prove.py` orchestre la campagne séquentielle,
conserve `proof.json`, arrête ses processus et nettoie ses ressources jetables.
La campagne demande deux montages et 1 Mio par volume ; elle produit aussi
un arrêt brutal du démon pour vérifier les consommateurs existants, le refus
de nouveaux montages Docker et la récupération des données acquittées.

Sur le SPARK DEV, après build et extraction du binaire dans `storage/p2-quota`,
exécuter comme root de la cellule (l'hôte FORGE n'intervient pas) :

```sh
setpriv --reset-env --reuid=1001 --regid=1001 --init-groups \
  --inh-caps=+sys_admin --ambient-caps=+sys_admin \
  python3 /srv/p2enjoy-serverless/storage/prove.py
```

Les UID/GID ci-dessus sont ceux vérifiés du compte `spark-docker` de ce DEV.
Le helper conserve le même propriétaire de fichiers et utilise la capacité
uniquement pour les montages. Les clients Docker n'ont aucune capacité, aucun
réseau et une racine en lecture seule. Les sources de l'outil sont versionnées ;
le binaire exporté et les rapports bruts restent des artefacts locaux.
