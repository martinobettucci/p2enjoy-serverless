# Exploitation de la plateforme

Contrat de l'unité [SLS-079](BACKLOG.md#sls-079), exigence 7 de l'objectif :
rendre l'exploitation complète et reproductible. **État : contrat seulement.** Le
guide d'exploitation n'est pas encore écrit ; ce document fixe son contenu et ses
preuves, il sera remplacé par le guide lui-même.

## État constaté

Les informations d'exploitation existent mais sont dispersées et mêlées au récit
des campagnes : le README (plus de 500 lignes de checkpoints), les READMEs de
composant, `DEPLOYMENT.md`, `PLATFORM_DEV.md` et les notes destinées à la cellule
du SPARK (`qualification/spark-notes/INSTALL.md`, une quarantaine de chapitres
dont la plupart sont des comptes rendus de preuve). Le briefing du SPARK
(`docs/dev-spark.md`) est volontairement hors du dépôt public. Une personne qui
reprend la plateforme ne trouve pas, en un seul endroit, comment l'installer, la
mettre à jour, la redémarrer, la diagnostiquer, la sauvegarder et la restaurer.

## Contenu exigé du guide

Un seul document d'exploitation, rédigé pour un exploitant qui n'a pas suivi le
développement. Les récits de campagne restent dans le journal et les preuves ; ils
sont déplacés, jamais supprimés.

1. **Prérequis et accès** : cible autorisée, comptes, outils, fichiers de
   configuration de cellule (contrat officiel, sans valeur secrète).
2. **Configuration** : tableau de **toutes** les variables et secrets de cellule et
   de composant avec rôle, format, caractère obligatoire, valeur par défaut et
   exemple non sensible. Le tableau est comparé au code qui les lit.
3. **Installation depuis zéro** : construction des images, création des volumes et
   du registre, migrations, agent de stockage, démarrage, première connexion SSO,
   création du premier service et du premier jeton, vérification de santé.
4. **Mise à jour** : contrôle, runtime, agent de stockage, adaptateur ; ordre,
   migrations, sauvegarde préalable, vérification, retour arrière.
5. **Redémarrage et reprise** : arrêt propre, redémarrage du contrôle, de l'agent,
   de l'hôte ; ce que la réconciliation rétablit seule et ce qui exige une action.
6. **Sauvegarde et restauration** : base de métadonnées, volumes données/cache,
   archives de code et d'archives de fonctions ; fréquence, vérification, restauration.
7. **Secrets** : où ils vivent, chiffrement, création, **rotation** (client SSO,
   clés de chiffrement, jetons de service) et effet de chaque rotation.
8. **Persistance** : emplacement de chaque donnée et ce que perd une recréation.
9. **Intégration au SPARK** : ports, routes et domaines (la gestion de routes se
   limite à ce que le contrat local autorise), TLS, propositions `.?` à émettre.
10. **Diagnostic** : santé et disponibilité, où lire les journaux, état des
    instances, tableau symptôme → cause → action (publication refusée, saturation,
    disque plein, SSO indisponible, routes absentes, instance bloquée, migration
    interrompue), et ressources résiduelles à reconnaître.
11. **Désinstallation et purge** d'une installation temporaire.

## Règles de rédaction

Chaque commande est exacte, copiable, sans variable implicite. Aucune valeur
secrète. Les noms respectent la règle de nommage du contrat local. Le README
redevient une porte d'entrée courte (objectif, prérequis, commandes principales,
structure, limites, liens). Les notes de la cellule du SPARK sont réduites à ce
dont le propriétaire du SPARK a besoin ; leur historique reste dans le journal.

## Preuves attendues

Le guide est **rejoué**, pas relu : une installation temporaire, distincte de
l'installation servie et de la configuration officielle, est créée en suivant
uniquement le guide, puis mise à jour, redémarrée de force, sauvegardée, détruite
partiellement et restaurée, enfin purgée. Chaque commande du guide est exécutée
ou, si elle est destructive, exécutée dans cette installation. Un symptôme du
tableau de diagnostic est provoqué pour de vrai pour au moins cinq entrées. Le
tableau de configuration est vérifié contre les variables réellement lues. Un
relecteur n'ayant pas suivi le développement exécute les chapitres 3 à 6 sans aide.
Si l'autorité du SPARK ne permet pas une installation temporaire, ce blocage est
nommé au backlog ; il ne se transforme pas en preuve partielle.
