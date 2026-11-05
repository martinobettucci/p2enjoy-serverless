# Configuration du banc de qualification

Sources originales : dossier qualification/ du dépôt de travail
p2enjoy-serverless du responsable. Copie d'exécution dans
/srv/p2enjoy-serverless/qualification, compte spark-docker.

Depuis ce répertoire : bash dev.sh --spark build, puis up, check, test, probe,
recreate-proof, operations, status. Exécuter une commande à la fois. logs consulte les
traces et stop arrête le banc sans supprimer ses volumes.

compose.dev.yml définit le profil dev, les limites du banc et les volumes ;
compose.spark.yml charge /etc/spark/env et /run/spark/secrets par env_file.
Le serveur peut démarrer sans secret mais le parcours positif de business requiert
QUALIFICATION_BUSINESS_TOKEN. QUALIFICATION_SYNTHETIC_SECRET permet la preuve
d'injection de secret présent, sans renvoyer sa valeur. QUALIFICATION_PUBLIC_LABEL
est une variable publique facultative. Ne jamais fabriquer ces valeurs dans
les tests pour simuler leur injection. Aucun .env ni environment de
substitution ne doit être créé. Les modifications de configuration de cellule
se proposent uniquement dans les fichiers .? prévus par son contrat.

Image Node 24 verrouillée par digest ; YAML verrouillé dans package-lock.json.
Build depuis les seules sources du banc, sans scripts npm de dépendances.
Les données persistent dans les volumes Docker
p2enjoy-qualification-dev_qualification-data et
p2enjoy-qualification-dev_qualification-cache. Ne pas supprimer ces volumes
pour déployer une nouvelle version. Le conteneur e2e n'a aucun montage des
volumes de l'application : il crée et nettoie ses ressources nommées par HTTP.
Le volume qualification-reports lui est réservé pour les observations entre
les étapes d'une recréation. Il ne démarre aucun serveur privé et n'importe
aucun handler. Aucun mock ni doublure n'est autorisé.

Le conteneur est non-root, en lecture seule hors volumes/tmpfs, limité à
384 Mio, 0,5 CPU et 96 processus. Ces limites portent sur le banc complet.
Seuls les profils DEV sont autorisés ; PREPROD et PROD sont interdits.

La console a configuré le label et les deux secrets au seul niveau de ce Spark.
operations nécessite Python 3 et vérifie les vrais logs, cgroups, arrêt actif,
redémarrage, erreurs de manifeste et défauts isolés de stockage et processus.
La recréation vérifie aussi le checkpoint du worker et sa reprise complète.
