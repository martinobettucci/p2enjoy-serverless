# Bascule gardée du registre de journaux

Contrat de [SLS-072.6](BACKLOG.md#sls-072), avant le code de bascule. Complète
[EXECUTION_LOGS](EXECUTION_LOGS.md#déploiement-et-retour). Cible : seul SPARK DEV,
configuration officielle et service `serverless-api` sur18090 ; référence inchangée.

## État constaté et image construite

Le22novembre2026, le contrôle réellement actif reste04604089, CIDe219f789,
schéma001→010, santé et intégrités correctes, compteurs actifs nuls. L'image
`p2enjoy-control:execution-journal-schema011` est construite et inspectée sous
empreinte immuable
`sha256:1aa70214be1ba72bd75bea301fac23a3dbcdaf6547de1b3521c9547c8ac35292`.
Ses42fichiers backend sont identiques aux sources préparées. Elle contient
quatre fichiers web, dont `assets/index-DpcIaa1t.js`, et le manuel compilé.
Le conteneur d'inspection est sans réseau ni volumes, retiré et joint.
Cela atteste les octets de l'image ; aucune migration ni preuve fonctionnelle
de cette image n'est acquise par sa construction.

Les identités exactes et la configuration sont recontrôlées au moment de la
bascule. Les empreintes historiques de cet état ne remplacent pas ce contrôle.

## Choix et motif

Le pilote de bascule est un processus ponctuel supervisé par systemd dans le
SPARK. Une commande `ExecStopPost` gelée assure la restitution après sa sortie,
même anormale. Le périmètre du cgroup comprend ses clients Docker, pas le démon
rootless ni les conteneurs applicatifs. `KillMode=control-group` et
`KillSignal=SIGKILL` demandent la terminaison des processus de commande restants.
Le traitement de fin vérifie leur absence avant toute restitution : son entrée
ne vaut pas, à elle seule, preuve de jonction. Le pilote garde un maximum140s ; le traitement de fin
dispose de200s et d'une alarme propre180s. La perte du terminal qui attend le
résultat ne détruit ni la supervision ni son reçu.

Les clients Docker de cette unité sont lancés directement avec les UID/GID et
groupes supplémentaires de `spark-docker`, par les options natives du processus
Python. Ils gardent le cgroup hérité ; aucun `runuser`/PAM ne peut les déplacer
vers une autre session. Le socket et le répertoire de configuration Docker sont
explicites ; aucune réaffectation de HOME. PID/naissance/UID/cgroup de chaque
client et des descendants observés sont conservés. Avant toute manipulation
dans le post, vérifier l'absence de l'ancien pilote et des clients enregistrés,
ainsi que le cgroup courant en excluant le seul post. Un survivant interdit la
restitution. Après la sortie, contrôler aussi les éventuels sous-groupes.

Ce choix évite un secours dépendant du terminal et un groupe de mutateurs
orphelins. Sémantique vérifiée dans les documentations primaires
[ExecStopPost](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#ExecStopPost=)
et [KillMode](https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html#KillMode=).
La version installée et les propriétés réelles de l'unité sont recoupées avant
de compter la restitution comme jointe.

## Préparation et possession

Avant toute commande qui change le service :

- vérifier le CID/image/génération et la santé046, la référence, les montages,
  budgets, commande, environnement haché et labels Compose ;
- vérifier les sources de l'image011 inspectée, la configuration officielle
  hachée et les dix migrations exactes ; refuser tout travail actif ;
- créer un répertoire privé root, nonce d'opération, avec copies gelées du
  pilote et du helper d'accès SQLite, empreintes et fichiers de reçus durables ;
- faire une première sauvegarde SQLite native sous UID1001, vérifier intégrité,
  FK et contenu de toutes les tables ; les fichiers sont privés ;
- enregistrer l'intention de l'unité avant son lancement. Une réponse de
  lancement inconnue conduit à inspecter cette unité, pas à en lancer une autre.

Aucun secret n'est recopié dans les reçus ou la ligne de commande. Le répertoire
de sauvegarde reste hors du contexte Docker. Les sources sont sauvegardées
séparément par leur outil de synchronisation ; la base n'est jamais remplacée
automatiquement par un ancien fichier.

## Deux frontières explicites

Le pilote vérifie encore le repos puis écrit durablement `stop-intent.json`
avant l'arrêt de046. Après l'arrêt confirmé du CID possédé, il recoupe la base
et produit une seconde sauvegarde native, finale, sur le schéma010 arrêté.
Le contenu et l'intégrité de cette sauvegarde sont vérifiés avant la suite.

Il écrit ensuite durablement `migration-intent.json`, **avant** tout changement
d'image ou lancement011. À partir de cette frontière, toute restitution utilise
l'image011 inspectée et la base existante, y compris si le commit011 est encore
inconnu. Ce choix conservateur évite de remettre046 pendant qu'une requête de
création Docker déjà acceptée pourrait encore faire démarrer le nouveau code.

L'image est sélectionnée par SHA, sans reconstruction ni changement des deux
fichiers env_file officiels. Le Compose habituel conserve chemins, quotas,
protections, port et noms. Son client est joint ; la santé HTTP réelle,
les onze migrations exactes, la collection UUID, les compteurs et intégrités,
les42fichiers backend et les ressources web servies sont recoupés. Le succès
primaire est publié durablement avant la sortie du pilote.

## Traitement de fin

Il conserve le résultat et le code de sortie primaires. Sa propre réussite ne
transforme pas un déploiement primaire échoué en campagne réussie.

1. Aucun `stop-intent` : vérifier046 exactement inchangée et saine ; aucune
   commande de restitution inutile.
2. Arrêt demandé, aucune intention de migration : vérifier d'abord la portée,
   arrêter/joindre le seul CID046 possédé si son arrêt était indéterminé, puis
   lire la base réelle arrêtée. Seulement si elle est intègre et exactement010,
   redémarrer ce même CID046 ; une lecture en erreur ne vaut jamais «011 absente».
3. Intention de migration présente : sélectionner exclusivement l'image011
   inspectée, sur le même volume et la base existante. En cas d'issue inconnue,
   reprendre le Compose vers cette même cible, puis vérifier la santé et011.
   Ne jamais remettre046, copier la sauvegarde sur la base active ni effacer
   des écritures acceptées. Si cette image ne démarre pas, conserver l'échec
   et corriger en avant avec une nouvelle image compatible.
4. Succès primaire présent : vérifier le CID/image/génération de son reçu,
   la santé et les mêmes invariants ; ne pas recréer un service déjà confirmé.

Toute identité étrangère, configuration divergente ou état de schéma inconnu
interdit de manipuler ce qui ne peut plus être attribué à l'opération. Le reçu
précise le point d'arrêt et les invariants acquis. Le pilote et le traitement
de fin doivent être absents, l'unité inactive avec MainPID/ControlPID0 et son
cgroup vide avant toute campagne suivante. Les sauvegardes restent conservées.

## Portée des preuves suivantes

La bascule fournit un prérequis, sans groupe fonctionnel ajouté. Les12groupes
API et10UI, puis25communs frais, restent requis. La vraie coupureAPI10 et son
secours sur le même CID011 éprouvent aussi la capacité de reprise de cette image
sur les écritures nouvellement acceptées. Le socle49/543 et les consommateurs
supplémentaires gardent leurs campagnes distinctes, dont la précondition
[091.3](BACKLOG.md#sls-091) de rétention courante. Aucune de ces preuves n'est
acquise par le présent contrat.
