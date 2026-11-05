# Exploitation du banc DEV

Le code source de l'application est dans `qualification/` de ce dépôt. Le
SPARK n'en reçoit qu'une copie d'exécution. Le client John Dalia et la FORGE
sont exclus de toute modification ou déploiement.

## Cible et accès

Le seul SPARK autorisé est celui décrit dans [dev-spark.md](dev-spark.md).
Utiliser `spark-docker` pour Docker ; le compte root n'a servi qu'à créer le
répertoire dédié `/srv/p2enjoy-serverless/qualification` avec son propriétaire.
Le rebond SSH transporte la connexion : aucune commande n'est lancée sur la
FORGE elle-même.

```sh
ssh -J ubuntu@51.158.54.202 spark-docker@10.77.0.24
cd /srv/p2enjoy-serverless/qualification
bash dev.sh --spark status
```

Pour accéder au banc depuis le poste, ouvrir un tunnel puis garder cette
commande active :

```sh
ssh -N -J ubuntu@51.158.54.202 -L 18080:127.0.0.1:18080 spark-docker@10.77.0.24
```

Les points d'entrée sont alors `http://127.0.0.1:18080/healthz`, `/catalog` et
`/functions/<nom>`. Aucune interface de management n'existe encore ; ces routes
sont celles d'un outil DEV. Ne pas créer de route publique pour cet exécuteur.

## Transférer une version

Depuis la racine du dépôt, ne transférer que cette liste explicite. Elle exclut
les fichiers de contexte, données, `.env`, caches et tout dépôt client :

```sh
tar -C qualification -cf - README.md package.json package-lock.json serverless.yml Dockerfile .dockerignore compose.dev.yml compose.spark.yml dev.sh src runner tests |
  ssh -J ubuntu@51.158.54.202 spark-docker@10.77.0.24 'tar -xf - -C /srv/p2enjoy-serverless/qualification'
```

Puis, dans le répertoire distant, une commande à la fois :

```sh
bash dev.sh --spark build
bash dev.sh --spark up
bash dev.sh --spark check
bash dev.sh --spark test
bash dev.sh --spark probe
bash dev.sh --spark recreate-proof
bash dev.sh --spark operations
```

Le profil est exclusivement `dev`. `recreate-proof` conserve les volumes ;
aucun `down -v`, prune ou suppression de volume n'est nécessaire. Pour revenir
à une version de code conservée, retransférer ses sources puis build/up, en
conservant les données ; ce geste ne restaure pas une ancienne donnée.

## Configuration et notes

Les deux `env_file` obligatoires sont définis dans `compose.spark.yml` pour
l'application et le client E2E. Aucune route publique n'est proposée.
QUALIFICATION_PUBLIC_LABEL est configuré comme variable publique ;
QUALIFICATION_BUSINESS_TOKEN et QUALIFICATION_SYNTHETIC_SECRET comme secrets.
Ils ont été créés via l'API normale de la console déjà en fonctionnement,
limitée à `infra-serverless`, puis les conteneurs ont été recréés. Aucune
valeur de secret n'est conservée dans le dépôt ou les preuves. La campagne
complète échoue si ces prérequis manquent, sans test ignoré.

La campagne E2E utilise un conteneur client séparé et des requêtes HTTP au vrai
service. Aucun import de handler par le client, mock ni substitution de
fonction. La campagne `operations` démarre également des conteneurs isolés du
même exécuteur pour de vraies pannes de configuration, de fichiers et de
capacité de création de processus. Elle ne modifie pas les volumes du banc.
Elle nécessite Python 3 sur le SPARK. Les conteneurs de panne sont supprimés
à la fin ; le service principal doit être sain pour que la campagne réussisse. Les données de chaque campagne sont créées/supprimées par leurs
API avec des identifiants propres. Le volume qualification-reports conserve
uniquement les observations du client entre les étapes de recréation.

Les trois textes de notes sont conservés dans `qualification/spark-notes/`.
Ils doivent être déposés comme propositions dans `/etc/spark/notes/*.md.?`.
Ils ne remplacent pas directement les notes officielles : leur adoption reste
un geste de console. Ne jamais toucher aux fichiers réécrits par le plan de
contrôle ou à sa configuration sur la FORGE.
