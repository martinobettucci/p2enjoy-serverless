# Stockage des fonctions

`p2-quota` monte un répertoire natif avec un plafond de taille logique. Il passe
31 contrôles E2E réels dans le SPARK DEV. Un agent local de volumes est
installé en DEV ; le raccordement au pilote d’instances est qualifié, avant
son intégration aux admissions publiques. [Preuve](../docs/evidence/storage-dev-2026-11-05.json).
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

## Agent local de volumes

Quinze groupes de cycle de vie et huit groupes de limites passent en DEV, avec
nettoyage confirmé, zéro échec et zéro test ignoré. Les 31 contrôles historiques
du proxy repassent sur le binaire modifié. [Preuve recoupée](../docs/evidence/storage-agent-dev-2026-11-06.json).

Le contrat est [STORAGE_AGENT](../docs/STORAGE_AGENT.md). Le service
`p2enjoy-storage-dev.service` expose un socket Unix privé à `spark-docker`,
avec contrôle d’UID, quotas data/cache, baux durables et opérations explicites
de conservation, archive, purge et vidage du cache. Il possède sa propre base
SQLite WAL (migrations 001, 002 et 003), distincte de celle du contrôle.
Le binaire accepte `-name` pour identifier chaque génération dans mountinfo ;
son défaut reste `p2quota` pour les commandes existantes.

Sur le SPARK DEV seulement, depuis `/srv/p2enjoy-serverless/storage` :

```sh
# Comme spark-docker, après copie des sources :
bash dev.sh build
# Comme root de la cellule, après application des variables par la console :
bash dev.sh install
bash dev.sh agent-test
bash dev.sh limits-test
bash dev.sh status
```

Attendre la fin complète de chaque commande. Les campagnes utilisent le
service installé, son socket réel, les montages FUSE et des conteneurs Docker.
`agent-test` vérifie les opérations et les pannes, y compris des consommateurs
vivants lors de la mort de FUSE et du restart. `limits-test` remplit le budget
logique, monte réellement 64 volumes, crée 51 baux, sature les connexions et
vérifie une arborescence de 4 200 répertoires avec permissions `000`.
Les rapports `agent-proof.json` et `agent-limits-proof.json` sont invalidés au
démarrage ; leur succès exige completed/cleanup vrais et failed/skipped à zéro.
Les rapports bruts et le binaire exporté ne sont pas versionnés.

| Variable | Usage et format | Défaut |
| --- | --- | --- |
| SERVERLESS_STORAGE_ROOT_HOST | Répertoire absolu privé de l’état et des volumes | Requis |
| SERVERLESS_STORAGE_SOCKET_DIR_HOST | Répertoire privé durable hors des données et de /run | Requis |
| SERVERLESS_STORAGE_BUDGET_MIB | Budget logique total, entier de 1 à 1048576 Mio | 32768 |
| SERVERLESS_STORAGE_RESERVE_MIB | Marge physique avant allocation, entier de 0 à 1048576 Mio | 8192 |
| SERVERLESS_STORAGE_MAX_MOUNTS | Montages ou préparations réservées, entier de 1 à 256 | 64 |

La configuration entre par les deux EnvironmentFile de cellule. L’installateur
conserve les paquets immuables, possédés par root, sous
`/usr/local/lib/p2enjoy-serverless/storage/<empreinte>`. Il ferme atomiquement
les mutations par quiesce après avoir préparé le paquet ; toute consommation,
mutation ou génération montée empêche cette maintenance normale. Un échec de
remplacement tente resume. Aucun socket ni port TCP n’est exposé.

Un restart avec baux constitue une panne : il conserve les baux et fichiers,
mais le contrôle doit supprimer les anciens conteneurs avant release et
réacquisition. Les montages déconnectés ne se réparent pas dans un ancien bind.
Une opération en attente garde sa réservation ; diagnostiquer son code et ses
permissions avant de réessayer, sans supprimer la base ni monter le backing.
L’arrêt normal d’exploitation doit d’abord drainer les consommateurs.

Le raccordement aux instances passe quatorze groupes réels :
[preuve](../docs/evidence/managed-storage-dev-2026-11-06.json). Les mutations publiques de
création, quotas, publication et suppression sont raccordées au contrôle.
Les admissions et commandes de purge/cache de la console restent à intégrer.
L'acquisition partielle après interruption et la marge de filesystem restent
à qualifier. Une coupure électrique et un processus bloqué
dans un appel noyau impossible à tuer ne sont pas reproduits par ces campagnes.

Le canal installé est `/srv/p2enjoy-serverless/storage-channel`, privé 0700 et
séparé des backings. Le Docker rootless du SPARK a son propre `/run` ; ce canal
partagé permet au contrôle de retrouver le socket après restart de l'agent.
Le répertoire demeure en place et seul le socket est recréé. L'unité conserve
la racine installée dans une annotation de garde, comparée à la configuration
officielle même lorsque l'agent est arrêté. Cette annotation n'injecte aucune
variable d'exécution. Une migration de racine exige une procédure explicite.

## Préparation des quotas avant publication

L'agent expose `prepare-configuration`, `commit-configuration`,
`abort-configuration` et `configuration-operation`. Une préparation sonde les
vrais quotas mais conserve la configuration et l'allocation précédentes jusqu'à
la décision. Les commandes portent les UUID de fonction, d'opération et
d'installation ; préparer exige aussi la version courante du registre.
Les répertoires nouveaux ne sont retirés à l'abandon que s'ils sont vides.
Le reçu durable permet de retrouver une décision après perte de réponse ;
la version progresse même après abandon, pour refuser une ancienne demande.

Comme root du SPARK DEV, lancer `python3 -B
/srv/p2enjoy-serverless/e2e/storage-preparations.py`. La campagne utilise le
client embarqué dans le contrôle, l'agent installé, les montages et des clients
Docker réels. Elle interrompt réellement l'agent pendant une préparation,
redémarre un abandon partiel et conserve une donnée inattendue avant résolution.
Son rapport `storage/preparations-proof.json` exige completed/cleanup vrais,
zéro échec et zéro skip. Exécuter ensuite les régressions en série.
Le protocole et sa reprise sont définis dans [ADMISSION](../docs/ADMISSION.md).
La preuve initiale conserve dix groupes de préparation et 37 régressions :
[preuve](../docs/evidence/storage-preparations-dev-2026-11-06.json). La campagne
actuelle compte douze groupes : elle vérifie aussi l’abandon avant réception
d’un prepare retardé, sans allocation, et ses refus de version/propriétaire/bail.
Le raccordement aux mutations publiques est décrit dans
[control](../control/README.md#mutations-de-stockage-des-fonctions) et sa
[preuve](../docs/evidence/function-storage-dev-2026-11-06.json).
