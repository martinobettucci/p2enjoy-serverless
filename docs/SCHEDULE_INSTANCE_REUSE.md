# Maximum par fonction et réutilisation d'instances planifiées

Complément de [SLS-078](BACKLOG.md#sls-078), selon
[SCHEDULES](SCHEDULES.md#preuves-e2e-attendues). Décision opératoire du10 novembre2026,
avant code. Budgets officiels inchangés ; aucune dépendance à la garde SLS-099.

## Campagne réelle

Créer deux fonctions originales par HTTPS,0,05CPU/128Mio,max1,concurrence1,
deadline60s,file5s, données/cache désactivés et concurrence de stockage shared.
Préparer deux hashes par fonction : HTTP POST avec/sans cron `*/5 * * * *`.
L'upload reste pilote. Choisir W avec au moins80s de marge ; attendre une frontière
avant promotion si nécessaire pour éviter un tir préparatoire.

- **Minimum préchauffé** : min1,idle0. Après promotion du cron, observer une
  instance ready avant toute invocation, son conteneur et ses réservations.
- **Maximum occupé** : min0,idle360s. Vers W−20s, un HTTP réellement admis attend
  jusqu'à W+20s dans le handler. Observer running/handler_started, la seule
  instance busy et son conteneur avant W. Le délai du handler est borné45s et
  ne modifie aucune horloge ni deadline du moteur.

Avant W, les seules deux instances réservent0,1CPU/256Mio ; une troisième
resterait sous les plafonds globaux1CPU/8192Mio/32instances. Les files sont vides.
La cible occupée possède déjà sa place maximale1, sans verrou data exclusif.
Son tir W doit être refused_capacity/schedule_capacity, sans lien ni invocation.
Pendant ce refus, le même HTTP reste running et la même instance busy.

À W, le minimum préchauffé doit exécuter son tir sur l'instance et le conteneur
ready relevés avant W. L'UUID du tir/invocation, le hash, POST/corps{} et le
trigger/slot sont recoupés. Le HTTP occupé termine ensuite normalement ; son
instance redevient ready, sans changement de génération ni création de remplaçante.

À W+300, les deux tirs réussissent en réutilisant exactement leurs instances et
conteneurs antérieurs. Pour la cible occupée, last_used_at+360 reste futur ;
pour le minimum, min1 maintient le préchauffage. Le premier refus reste inchangé,
sans rejeu. Total : quatre tirs (trois succès/un refus) et quatre invocations
réussies (un HTTP/trois planifiées).

## Discriminants et nettoyage

Le lecteur natif accepte les deux UUID et leur namespace scheduled-functions.
Il relève SQL RO sous propriétaire, configurations, instances, Docker,
réservations, files, baux, réseaux et canaux. Les UUID des minima sont conservés
même sans invocation, pour contrôler leur libération. Un succès seul ne prouve
pas la réutilisation : instance_id et CID doivent correspondre aux relevés initiaux.

Après les tirs, passer min0/idle0 par PUT normal, attendre la libération puis
promouvoir les hashes sans cron. Révoquer le jeton, archiver/purger par API et
supprimer parents ; ressources physiques et compteurs nuls,5982 artefacts,
backend/images/services/fichiers officiels conservés. Un échec termine ses HTTP
et libère les minima avant nettoyage, sans relance automatique.

Quatre groupes : préparation/occupation, premier refus et succès préchauffé,
réutilisation aux prochains tirs, deux purges publiques/absence physique.
Ce complément ne clôture pas SLS-078 : plafond global (SLS-099), rétention réelle,
régression complète restent ouverts. Aucun produit, budget, image,
migration ou comportement UI/manuel modifié.

## Résultats qualifiés

La [preuve DEV du10 novembre2026](evidence/schedule-instance-reuse-dev-2026-11-10.json),
client832b20e, passe quatre groupes sur325 sources et même image b9ad872a.
Fenêtres21:20/21:25UTC. Avant W : deux instances réservent0,1CPU/256Mio, files
vides et budgets globaux libres. Le minimum ready n'a encore aucune invocation ;
l'autre instance est busy sous HTTP non exclusif et déjà au maximum1.

À21:20, la cible occupée reçoit refused_capacity/schedule_capacity sans
invocation, tandis que le HTTP reste running. Le premier tir du minimum utilise
l'instance et le CID relevés avant W. Après terminaison HTTP, son instance devient
ready avec même CID ; générations et configurations restent identiques.
À21:25, les deux tirs réutilisent exactement ces deux instances/CID. Le refus
reste inchangé, sans rejeu. Quatre tirs et quatre handlers réussis : un HTTP,
trois planifiés. Identifiants, hashes et slots sont recoupés.

Minima/idles libérés par PUT normal avant promotion sans cron, puis deux purges
publiques ; code/volumes/conteneurs/réseaux/canaux/baux absents, compteurs nuls.
Les34 backends,5982 artefacts et services/images/démarrages/fichiers officiels
sont conservés. Aucun build produit, UI/manuel ou capture nouveau. La revue a
renforcé les comparaisons de générations/configurations et la corrélation du
premier tir avant lancement ; les pannes propres du banc ne sont pas déduites
du nominal. Rétention réelle et régression complète gardent l'unité ouverte ; plafond099
et adaptateur.7 ont leurs preuves distinctes.

Le [complément de console](evidence/schedule-console-dev-2026-11-10.json) qualifie
les états vides/erreur, nom63, pagination et reprise401→200 sur la nouvelle image
c59b8616. Les preuves de ce document conservent leur image historique ; elles
ne sont pas présentées comme rejouées par ce complément.
