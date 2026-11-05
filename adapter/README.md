# Adaptateur P2Enjoy

Implémentation SLS-030 en cours. Contrat : [DEPLOYMENT](../docs/DEPLOYMENT.md).
Python 3.13+ et PyYAML 6.0.3 ; les archives utilisent ZIP de la bibliothèque
standard. Les handlers sont préparés par le projet avant le packaging.

Depuis la racine, la CLI s'utilisera avec `python3 -m adapter plan --config
qualification/serverless.platform.yml`, puis `package` et `deploy`.
Les commandes sont ajoutées et qualifiées progressivement ; ce dossier n'est
pas encore un adaptateur livré. Les preuves CLI exécutent le vrai processus ;
les preuves de déploiement utilisent la véritable API DEV et une identité SSO.
Chaque campagne est séquentielle. Les sorties locales vont dans .serverless-p2
du projet et sont exclues des archives. Les valeurs de secrets restent hors
des descripteurs et de la sortie standard.
