# Adaptateur P2Enjoy

Implémentation SLS-030 en cours. Contrat : [DEPLOYMENT](../docs/DEPLOYMENT.md).
Hôte Linux, Python 3.13+ et PyYAML 6.0.3 ; les archives utilisent ZIP de la bibliothèque
standard. Les handlers sont préparés par le projet avant le packaging.

Depuis la racine, les commandes disponibles sont :

```sh
python3 -m adapter plan --config qualification/serverless.platform.yml
python3 -m adapter package --config qualification/serverless.platform.yml
```

`deploy` sera ajouté avec les révisions. Les preuves CLI exécutent le vrai processus ;
les preuves de déploiement utilisent la véritable API DEV et une identité SSO.
Chaque campagne est séquentielle. Les sorties locales vont dans .serverless-p2
du projet et sont exclues des archives. Les valeurs de secrets restent hors
des descripteurs et de la sortie standard.

Installation Python dans un environnement isolé : `python3 -m pip install
--require-hashes -r adapter/requirements.txt`. Sur le SPARK DEV, depuis
`/srv/p2enjoy-serverless/adapter`, exécuter successivement `bash dev.sh build`,
`bash dev.sh plan`, `bash dev.sh package`, `bash dev.sh test`. Chaque commande
attend la précédente. Les deux images se construisent en série. La cible E2E
ajoute ses fichiers de preuve à l'image réelle de la CLI et ne lance aucun
serveur de substitution. Le rapport est conservé dans `adapter/reports/`.
