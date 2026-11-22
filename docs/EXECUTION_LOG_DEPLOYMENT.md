# Bascule gardée du registre de journaux

Contrat de [SLS-072.6](BACKLOG.md#sls-072), avant le code de bascule. Complète
[EXECUTION_LOGS](EXECUTION_LOGS.md#déploiement-et-retour). Cible : seul SPARK DEV,
configuration officielle et service `serverless-api` sur18090 ; référence inchangée.

## État constaté et image construite

Avant la bascule du22novembre2026, le contrôle réellement actif est04604089, CIDe219f789,
schéma001→010, santé et intégrités correctes, compteurs actifs nuls. L'image
`p2enjoy-control:execution-journal-schema011` est construite et inspectée sous
empreinte immuable
`sha256:1aa70214be1ba72bd75bea301fac23a3dbcdaf6547de1b3521c9547c8ac35292`.
Ses42fichiers backend sont identiques aux sources préparées. Elle contient
quatre fichiers web, dont `assets/index-DpcIaa1t.js`, et le manuel compilé.
Le conteneur d'inspection est sans réseau ni volumes, retiré et joint.
Cela atteste les octets de l'image ; aucune migration ni preuve fonctionnelle
de cette image n'est acquise par sa construction.

La bascule nominale est ensuite exécutée à11h00UTC sur cette même image :
CID49a82269, `StartedAt=2026-11-22T11:00:17.493119926Z`, santé correcte,
onze migrations, anciennes colonnes conservées,42fichiers backend et quatre
ressources servies identiques. Les deux sauvegardes ont la même empreinte
`0a517159b2c105a42961125cf182eab1902b86707ad8d664da46a359db0b965c`.
Le post a vérifié le succès primaire ; l'unité est inactive, MainPID/ControlPID0,
cgroup vide. Cette exécution est un prérequis, sans groupe fonctionnel ajouté.
Elle ne remplace pas les tests072 ni une preuve de perte du pilote.

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


## Mise à jour de code compatible011 — SLS-128

Cette voie est distincte de la bascule010→011 historique ci-dessus. Elle part
exclusivement du contrôle1aa70214 sain, conserve ses onze migrations exactes et
une image candidate différente, construite et inspectée avant tout arrêt. Les
fichiersSQL001→011 de la candidate correspondent aux migrations de la baseline.
Elle ne remet ni046 ni une ancienne sauvegarde. Le seul changement attendu
pour128 est execution_logs.py ; le web et tous les autres backend restent
identiques à l'image1aa attestée. Aucun fichier officiel, quota ou montage
n'est modifié, notamment /tmp16Mio.

La précondition accepte l'archive possédée de128 encore retenue mais exige zéro
fonction active, instance, invocation active, opération, candidat ou réservation.
Les métadonnées de cette archive, ses logs et les compteurs du journal sont
conservés pendant le remplacement ; ils ne sont effacés que par sa repriseAPI.
La collectionUUID et le schémaSQL complet sont épinglés. Le pilote commun
expose une préparation explicite prepare-update ; l'intention et le reçu nomment
mode=code-update, sans détourner prepare qui garde son contrat010 historique.

Avant arrêt, produire une sauvegardeSQLite native et un état complet ; après
arrêt du seulCID/StartedAt1aa possédé, produire la sauvegarde finale et comparer
l'intégrité, FK, migrations, schémaSQL et toutes les tables. Le snapshot final
arrêté est la référence de conservation. Les copies restent privées et ne sont
jamais écrites sur la base active. Sources, helpers et paramètres sont gelés
sous nonce/root0700 avec empreintes, comme pour la première bascule.

L'unité de mise à jour possède son nom significatif
serverless-update-journal-code-<nonce>, un label de possession propre sur le
nouveau conteneur, ses commandesDocker et leurs PID/naissance/cgroups. Elle
reprend les bornes140s/200s/alarme180s, UID/GID explicites des clients et
ExecStopPost existants. Une intention code-update-intent est écrite durablement
avant sélection de l'image/recréation ; toute reprise après cette frontière
vise exclusivement la même candidate011 compatible. Avant cette frontière,
après arrêt, le secours peut seulement redémarrer le CID1aa exact, avec sa
nouvelle génération recoupée dans sa propre fenêtre de démarrage. Une image1aa
portée par un autreCID ne suffit pas à donner possession de ce conteneur.

Après création, vérifier configuration, référence, fichiers officiels,
backend42/web4 embarqués et ressourcesHTTP réelles no-store. Recouper toutes
les tables et le schéma à la sauvegarde finale, collectionUUID et comptage
réconcilié inclus ; aucune exemption globale des tables journal. Une variation
inattendue échoue et reste à instruire. Les nouveaux logspérimés ne sont pas
attendus pour ce corpus à septjours. L'ancien CID ne peut être remplacé que
par une candidate portant le label/nonce prévu après l'intention de cette unité.

Le succès primaire et la finalisation restent distincts. Leur reçu exact,
unité inactive/MainPID0/ControlPID0 et cgroup vide précèdent toute qualification.
La réussite d'un secours ne transforme pas l'échec primaire en succès de mise
à jour. RepriseAPI de l'archive128 et campagne12API/10UI/25communs restent des
preuves suivantes ; cette opération est un prérequis de déploiement seulement.


Le lanceur local `python3 -B e2e/execution-journal-update-run.py <reçu-image-privé>`
utilise uniquement prepare-update. La préparation recoupe le manifeste du CID1aa
embarqué avec celui de la candidate avant arrêt : web et migrations identiques,
ensemblebackend égal et seul execution_logs.py différent. La comparaison après
remplacement inclut schema_migrations ; la dispense de migration reste réservée
à010→011. Le runner accepte failed comme fin observable, mais ne peut annoncer
une réussite que pour ActiveStateinactive et Resultsuccess, avec reçus primaire/
post réussis, MainPID/ControlPID0 et cgroup vide. Ces contrôles sont communs aux
deux lanceurs. Leur revue et leur compilation ne prouvent pas encore une bascule.


## Mise à jour du focus — SLS-124

Le profil explicite journal-focus complète la voie011→011 ; le profil initial
purge-rollback de128 reste inchangé. La baseline de ce second profil est
l'imagebf9b61a6 attestée par la reprise128. La candidate doit conserver exactement
les42backend, les onze migrations, le CSS et le favicon ; seuls le JavaScript
Vite (focus et manuel recompilé) et sa référence dansindex.html changent.
Le manifeste embarqué de la baseline et celui de la candidate sont comparés
avant tout arrêt, pas seulement aux sources locales. Une différence backend,
CSS/favicon ou ensemble de types d'assets interdit cette voie.

Le lanceur reçoit le reçu-image privé puis journal-focus et utilise uniquement
prepare-ui-update. L'identité enregistre modecode-update et profiljournal-focus ;
les vérifications de nonce/label/CID/génération, sauvegardes, schema/tables/UUID,
configuration, référence et résultats primaire/post restent celles de la voie
011→011. Avant l'intention, seul le CIDbf exact peut être redémarré ; après
code-update-intent, reprise vers la même candidate compatible exclusivement.
Les trois fichiers officiels, les quotas et /tmp16Mio restent inchangés.

La qualification doit relever les backend42 identiques et les quatre ressources
web servies no-store conformes à la candidate, unitéinactive/Resultsuccess,
MainPID/ControlPID0 et cgroup vide. Elle est suivie du replay réel124 en1440 et
390px, du statut410 du suivi invalidé, des captures inspectées et des campagnes
12API/10UI/25communs fraîches. Construire ou basculer la candidate ne suffit pas
à déclarer le correctif d'ergonomie qualifié.

## Mise à jour du diagnostic de maintenance — SLS-126.5

Le profil explicite maintenance-diagnostics part exclusivement de l'image
sha256:a7d7491a8cb698c9e2ee739339c60dc3846d84c8242b55a13a9e9b4f21edb1d7.
La candidate conserve exactement les quatre ressources web, le manifeste backend42
et ses onze migrations, à l'exception de control/app/execution.py et
control/app/schedules.py : seuls leurs événements de maintenance_failed sont
enrichis selon EXECUTION_LOGS. Une différence supplémentaire interdit cette voie.
Le lanceur reçoit ce profil et utilise prepare-diagnostics-update. Baseline
embarquée, sources et candidate sont recoupées avant arrêt ; le profil est figé
dans l'identité du pilote. Tous les garde-fous011→011 de sauvegarde, possession,
CID/génération, label, reprise vers la même candidate après intention, comparaison
schema/tables/collection, configurations et cgroups restent identiques. Aucun
retourDB, changement de santé, cadence, quota, /tmp ou configuration n'est permis.
Le déploiement est un prérequis de diagnostic, sans groupe fonctionnel qualifié.
