# Déploiement DEV de la plateforme

## Baseline

Le banc de qualification est déployé selon `QUALIFICATION_DEV.md`. Le composant
de quota est construit dans `storage/`, testé par 31 contrôles puis laissé
sans montage permanent. Le contrôle et la console initiale sont déployés en
DEV ; leurs parcours administrateur restent à qualifier avec une session SSO.
La cible est le SPARK `infra-serverless`
et le répertoire `/srv/p2enjoy-serverless`, administré par `spark-docker` pour
Docker. Le dossier de cellule fourni reste la référence `dev-spark.md`.

## Ordre de réalisation

1. Proposer les paramètres supplémentaires du contrôle dans les fichiers `.?` de la cellule,
   puis les appliquer par sa console. Aucun secret n'est conservé au dépôt.
2. Construire et déployer le contrôle et le runtime, appliquer les migrations
   SQLite versionnées, puis déployer l'application témoin via l'adaptateur.
3. Exécuter les campagnes ciblées puis complète et mettre à jour les notes.

## Intégration appliquée

Client OIDC créé : `p2enjoy-serverless-dev`, application serveur confidentielle,
PKCE S256, callback `/auth/retour`, déconnexion `/`, rôles `verified` et `admin`.
Déclaration prête à importer dans l'interface SSO, onglet Intégrations :
[OIDC_DEV.txt](OIDC_DEV.txt). Domaine retenu pour DEV :
`serverless-dev.lelabs.tech`, résolu vers l'entrée de la cellule et déclaré
sur le port HTTP 18090 avec TLS public. Le secret `OIDC_CLIENT_SECRET` est
appliqué dans le SPARK, avec `OIDC_CLIENT_ID` et `SERVERLESS_PUBLIC_URL`.

État vérifié le 5 novembre 2026 : découverte SSO accessible ; callback accepté
par le client, PKCE exigé ; l'authentification du client au token endpoint est
acceptée (code d'autorisation invalide volontairement, erreur invalid_grant).
La route DNS et HTTPS répond et le contrôle écoute sur 18090. Les notes de
cellule du banc et du stockage sont appliquées. La console
locale est accessible sur 5175. Le parcours utilisateur SSO reste à vérifier
avec le contrôle, dans SLS-020 et SLS-060.

## Conservation de l'adresse cliente

La mesure sur le contrôle DEV constate que le proxy TLS et l'accès direct
depuis le SPARK arrivent tous deux avec le pair `172.19.0.1` tant que le proxy
utilisateur Docker est actif. Caddy reconstruit X-Forwarded-For sur l'entrée
TLS, mais un accès direct peut le fournir lui-même. Ce pair commun ne doit
donc pas entrer dans SERVERLESS_TRUSTED_PROXIES.

La désactivation de userland-proxy est écartée : Docker refuse de démarrer
sans `/proc/sys/net/bridge/bridge-nf-call-iptables`, absent de cette cellule.
La configuration initiale du démon est restaurée. Les réseaux Compose,
devenus incohérents au redémarrage refusé, ont été recréés sans retirer les
volumes ; les deux piles DEV sont revenues saines.

Le choix retenu est `network_mode: host` pour le seul contrôle. Docker 29.9.3
permet ici de partager le réseau réel du SPARK : la preuve utilise le vrai
contrôle, un état SQLite temporaire et les deux env_file officiels lus par
Compose. Le pair loopback reste 127.0.0.1 et l'inode de namespace réseau du
conteneur correspond à celui du SPARK. Les fonctions gardent un réseau Docker
isolé ; leur commande d'exécution passera par l'API locale Docker.

Le contrôle écoute directement sur 18090, sans publication de port Docker.
Les chemins TLS et directs sont mesurés : le pair TLS est `10.77.0.1`, le
loopback `127.0.0.1`, et un client Docker bridge arrive depuis `10.77.0.24`.
Caddy remplace X-Forwarded-For même lorsque le client le falsifie. La proposition
`SERVERLESS_TRUSTED_PROXIES=10.77.0.1/32` est appliquée par la console SPARK,
puis le contrôle est recréé. La campagne réelle des limites de connexion
vérifie ensuite les refus et la persistance des compteurs au redémarrage. Aucun
paramètre de FORGE ni garde de filtrage noyau n'est modifié. Les expériences
de conteneurs temporaires sont supprimées après chaque mesure.

## Reprise et retour arrière

Le binaire de montage s'exécute comme `spark-docker`. Le helper fusermount3
installé perd son descripteur de communication au passage exec dans cette
cellule (trace réelle : dup3 réussi, puis fd 3 absent au démarrage du helper).
Le mode direct est qualifié avec CAP_SYS_ADMIN attribuée exclusivement
au processus de montage dans le SPARK, sous ce même UID. Les workloads et la
construction restent dans Docker. Le montage reste accessible au seul UID
propriétaire, qui correspond au root interne des conteneurs rootless ; les
capacités des workloads sont retirées. Le montage n'expose aucune API réseau.

L'expérience de quota ne remplace aucun volume existant. Son nettoyage suit
l'ordre arrêt des conteneurs, démontage FUSE, suppression des fichiers propres
à l'expérience. Un échec de montage arrête cette expérience sans modifier les
volumes du banc. L'installation définitive et ses procédures de reprise seront
documentées avec l'implémentation retenue.
