# Adaptateur P2Enjoy

Implémentation SLS-030 en cours. Contrat : [DEPLOYMENT](../docs/DEPLOYMENT.md).
Hôte Linux, Python 3.13+ et PyYAML 6.0.3 ; les archives utilisent ZIP de la bibliothèque
standard. Les handlers sont préparés par le projet avant le packaging.

Depuis la racine, les commandes disponibles sont :

```sh
python3 -m adapter plan --config qualification/serverless.platform.yml
python3 -m adapter package --config qualification/serverless.platform.yml
python3 -m adapter deploy --config qualification/serverless.platform.yml --service UUID_DU_SERVICE
```

`deploy` lit l’origine HTTPS dans `P2_SERVERLESS_URL` et le jeton de service
dans `P2_SERVERLESS_TOKEN`. Le service doit déjà exister et porter le nom du
manifeste. Read est nécessaire pour rechercher les fonctions ; Create publie
la première révision et Update les suivantes. Les valeurs `${env:NOM}` sont
résolues depuis l’environnement du processus, sans fichier `.env`.

La CLI valide et empaquette tout avant mutation, puis publie en série. Elle
conserve les UUID, refuse les redirections et n’applique la configuration
active qu’avec la validation du candidat. Les erreurs donnent un code de sortie
non nul et un résultat JSON par fonction tentée. Une réponse perdue est signalée
`unknown`, avec l’identifiant du candidat connu, sans rejouer la mutation.
Consulter ce candidat avant toute relance. Les avertissements précèdent les
appels sur stderr ; stdout contient le rapport final sans configuration ni logs.

Les preuves CLI exécutent le vrai processus ; les preuves de déploiement
utilisent la véritable API DEV et une identité SSO. Les publications positives
de cette commande restent à qualifier.
Chaque campagne est séquentielle. Les sorties locales vont dans .serverless-p2
du projet et sont exclues des archives. Les valeurs de secrets restent hors
des descripteurs et de la sortie standard.

Installation Python dans un environnement isolé : `python3 -m pip install
--require-hashes -r adapter/requirements.txt`. Sur le SPARK DEV, depuis
`/srv/p2enjoy-serverless/adapter`, exécuter successivement `bash dev.sh build`,
`bash dev.sh plan`, `bash dev.sh package`, `bash dev.sh test`, puis `bash dev.sh deploy-public-test`. Chaque commande
attend la précédente. Les deux images se construisent en série. La cible E2E
ajoute ses fichiers de preuve à l'image réelle de la CLI et ne lance aucun
serveur de substitution. Le rapport est conservé dans `adapter/reports/`.

`deploy-public-test` exerce les erreurs locales et un véritable refus 401
sur https://serverless.lelabs.tech, avec validation TLS normale. Un jeton
volontairement invalide n’est jamais accepté comme identité. Le rapport est
`adapter/reports/adapter-deploy-public.json`. Cette campagne ne prouve aucune
publication. Depuis le dépôt du poste, `node e2e/adapter-deploy.mjs` utilise
la session SSO réelle pour créer ses jetons, puis exécute la CLI et les
validations Docker : pagination, mises à jour, résultats partiels et reprise
de brouillon. Une session SSO réelle est disponible sur le nouveau domaine ;
cette campagne authentifiée reste à exécuter.
