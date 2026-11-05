# Déploiement DEV de la plateforme

## Baseline

Le banc de qualification est déployé selon `QUALIFICATION_DEV.md`. Le composant
de quota est construit dans `storage/`, testé par 31 contrôles puis laissé
sans montage permanent. La plateforme n'est pas encore installée.
La cible est le SPARK `infra-serverless`
et le répertoire `/srv/p2enjoy-serverless`, administré par `spark-docker` pour
Docker. Le dossier de cellule fourni reste la référence `dev-spark.md`.

## Ordre de réalisation

1. Déclarer la route DEV et le client SSO dans leurs interfaces autorisées.
2. Proposer les paramètres du contrôle dans les fichiers `.?` de la cellule,
   puis les appliquer par sa console. Aucun secret n'est conservé au dépôt.
3. Construire et déployer le contrôle et le runtime, appliquer les migrations
   SQLite versionnées, puis déployer l'application témoin via l'adaptateur.
4. Exécuter les campagnes ciblées puis complète et mettre à jour les notes.

## Intégration à préparer

Client OIDC prévu : `p2enjoy-serverless-dev`, application serveur confidentielle,
PKCE S256, callback `/auth/retour`, déconnexion `/`, rôles `verified` et `admin`.
Déclaration prête à importer dans l'interface SSO, onglet Intégrations :
[OIDC_DEV.txt](OIDC_DEV.txt). Domaine retenu pour DEV :
`serverless-dev.lelabs.tech`, à faire résoudre vers l'entrée de la cellule et
à déclarer par sa console sur le port HTTP 18090 avec TLS public.
Le secret doit porter le nom `OIDC_CLIENT_SECRET`, selon `sso.md`, et être
saisi directement comme secret de ce SPARK. Il ne doit pas transiter en chat.

État observé le 5 novembre 2026 : découverte du SSO accessible ;
`serverless-dev.lelabs.tech` ne résout pas ; console locale sur le port 5175
indisponible. Ces constats ne prouvent pas une panne de la FORGE. Les actions
de configuration restent limitées au scope du SPARK.
La tentative publique d'autorisation avec le client prévu retourne
« Client non trouvé ». L'accès administrateur au SSO est donc nécessaire pour
enregistrer cette intégration ; le navigateur de la session est indisponible.

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
