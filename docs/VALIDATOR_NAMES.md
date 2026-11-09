# Noms d’exploitation des validateurs Docker

Unité [SLS-076](BACKLOG.md#sls-076), en préparation. Contrat de responsabilité :
[DEPLOYMENT_NAMES](DEPLOYMENT_NAMES.md#conteneurs-de-validation). Le seul
changement produit est le préfixe `serverless-code-validator-`, suivi du même
UUID aléatoire hexadécimal. Labels, isolation, protocole, délais, suppression
par identifiant ou nom et réconciliation ne changent pas. Aucun effet sur le
hash canonique, le schéma, les ressources ou les valeurs des fonctions.

## Plan séquentiel avant code

1. Recouper installation, quiescence, sources et images du seul SPARK DEV.
   Conserver l’image008 actuelle sous un tag de référence explicite avant
   reconstruction du contrôle. Construire la nouvelle image pendant que
   l’ancienne continue de servir ; ne pas reconstruire les runtimes/CLI.
2. Créer par HTTPS une fonction originale de campagne avec données/cache,
   variable publique et secret synthétique. Publier son code stable sur
   l’ancienne image, le promouvoir explicitement et l’invoquer. Conserver
   configuration, cible, hash, alias et compteurs avant la bascule.
3. Préparer un vrai upload pilote dont l’import attend60 secondes. Observer
   son marqueur exécuté, candidat validating, nom p2-v, labels exacts et montages.
   Armer une garde indépendante du contrôle avant SIGKILL. Interrompre uniquement
   serverless-api, confirmer l’orphelin encore présent, puis recréer le seul
   contrôle avec la nouvelle image et les deux fichiers officiels Compose DEV.
   Le premier redémarrage doit être celui de la nouvelle image, afin que son
   ready() fournisse la preuve de reprise de l’ancien nom.
4. Confirmer santé/image, candidat interrompu, réserve nulle, ancien conteneur
   et canal absents. Invoquer encore le stable : même hash/cible/configuration,
   données/cache conservés. Le compteur doit continuer, sans restauration
   artificielle des fichiers ni réécriture d’état applicatif.
5. Avec la nouvelle image, trois vrais uploads code seul : import réussi
   identique (déduplication), import qui lève une exception, import60 secondes
   expirant sous le délai réel15 secondes. Chaque import écrit un marqueur
   original avant d’attendre pour rendre son conteneur vivant observable. Lire
   nom complet, labels, montages/isolation et ID par Docker ; exiger le nouveau
   préfixe et un UUID, puis sa disparition et celle du canal. Vérifier réponse
   publique et candidat durable, pas seulement l’absence du processus.
6. Réinvoquer le stable après chaque issue ; alias/hash/promotion, ressources,
   configuration et compteurs doivent être préservés. Supprimer puis purger
   la fonction et recouper volumes/artefacts/canaux/conteneurs/réseaux et reçus.
7. Rejouer en série le composant de validation36, l’API versions12 et la CLI
   versions5 sur la nouvelle image, puis recouper leurs nettoyages. Ces preuves
   connexes ne remplacent pas la régression complète008 encore au backlog.

## Garde de remise en service

Avant l’interruption, une garde systemd locale au seul SPARK est armée avec
l’ID de l’ancien contrôle, l’empreinte de la nouvelle image, les montages et
empreintes des deux fichiers officiels. Le programme de reprise est figé dans
un dossier privé. Il n’administre ni Forge, ni route, ni variable, ni secret.
Une échéance de90 secondes remet le contrôle en service par le manifeste DEV
normal si le pilote disparaît. Une reprise nominale explicite utilise le même
programme avant l’échéance. Un verrou commun sérialise les deux chemins.

Le programme vérifie l’identité du SPARK, du projet/service Compose et des
images admises avant mutation ; il refuse une configuration concurrente. Il
peut terminer un démarrage déjà réussi après recoupement, sans créer un second
contrôle. Les résultats incertains sont relus, jamais convertis en succès
automatique. La garde doit être désarmée et sa fin confirmée après reprise.
L’interruption sous ce garde-fou vise un seul contrôle008 DEV sans migration.

Un échec d’inspection Docker, y compris une absence inattendue, n’autorise
aucune recréation. L’ancien ID doit être arrêté en137 avec son StartedAt initial.
Une intention synchronisée précède l’unique commande Compose. Si son résultat
est incertain mais la nouvelle image est déjà présente, la reprise attend la
santé de ce même ID ; elle ne le recrée pas. Montages, réseau, limites,
commande et empreinte d’environnement effectif sont comparés avant/après.
L’environnement lui-même n’est jamais imprimé ni conservé dans la preuve.
Le client choisit et persiste l’identifiant unique de garde avant l’appel
d’interruption. Une perte de stdout ne peut donc pas effacer son identité ;
une remise en service non confirmée bloque le nettoyage et conserve la fixture.
Un timer déjà collecté n’est reconnu absent qu’après LoadState=not-found et
ActiveState=inactive natifs ; un code non nul seul ne suffit pas.

Les réponses d’upload interrompues restent des issues de transport, corrélées
ensuite au candidat durable. Un échec conserve ses reçus et déclenche le suivi
de remise en service avant le nettoyage des objets. Le nominal de cette garde
est éprouvé par la bascule ; sa propre perte/expiration reste distincte et ne
sera pas revendiquée sans injection réelle.

## Preuves et limites

Le banc ne modifie pas le code ni les données des projets de référence. Ses
fixtures originales restent dans qualification/artifacts ; chaque handler est
chargé et invoqué par la plateforme réelle. Sources et images sont relevées
avant/après chaque phase. La bascule explique seule la différence d’image
contrôle ; comparaison du backend limitée au préfixe/commentaire de validator,
assets web, manuel, référence/runtime/CLI et configurations inchangés.

Aucune réussite n’est acquise à ce stade. SLS-074, ses autres pannes et ses
régressions complètes conservent leur périmètre ; SLS-076 ne les clôture pas.
