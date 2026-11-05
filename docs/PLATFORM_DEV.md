# Déploiement DEV de la plateforme

## Baseline

Le banc de qualification est déployé selon `QUALIFICATION_DEV.md`. La
plateforme n'est pas encore installée. La cible est le SPARK `infra-serverless`
et le répertoire `/srv/p2enjoy-serverless`, administré par `spark-docker` pour
Docker. Le dossier de cellule fourni reste la référence `dev-spark.md`.

## Ordre de réalisation

1. Qualifier un disque de fonction à taille bornée dans le SPARK, monté via
   FUSE puis lu/écrit depuis Docker rootless. L'expérience emploie des images
   de disque et des conteneurs dédiés supprimés après démontage.
2. Déclarer la route DEV et le client SSO dans leurs interfaces autorisées.
3. Proposer les paramètres du contrôle dans les fichiers `.?` de la cellule,
   puis les appliquer par sa console. Aucun secret n'est conservé au dépôt.
4. Construire et déployer le contrôle et le runtime, appliquer les migrations
   SQLite versionnées, puis déployer l'application témoin via l'adaptateur.
5. Exécuter les campagnes ciblées puis complète et mettre à jour les notes.

## Intégration à préparer

Client OIDC prévu : `p2enjoy-serverless-dev`, application serveur confidentielle,
PKCE S256, callback `/auth/retour`, déconnexion `/`, rôles `verified` et `admin`.
Le domaine doit être résolu et exposé avant de fournir la déclaration finale.
Le secret doit porter le nom `OIDC_CLIENT_SECRET`, selon `sso.md`.

État observé le 5 novembre 2026 : découverte du SSO accessible ;
`serverless-dev.lelabs.tech` ne résout pas ; console locale sur le port 5175
indisponible. Ces constats ne prouvent pas une panne de la FORGE. Les actions
de configuration restent limitées au scope du SPARK.

## Reprise et retour arrière

L'expérience de quota ne remplace aucun volume existant. Son nettoyage suit
l'ordre arrêt des conteneurs, démontage FUSE, suppression des fichiers propres
à l'expérience. Un échec de montage arrête cette expérience sans modifier les
volumes du banc. L'installation définitive et ses procédures de reprise seront
documentées avec l'implémentation retenue.
