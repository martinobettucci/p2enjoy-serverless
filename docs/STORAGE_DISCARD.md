# Effacement de stockage corrélé

Spécification SLS-064, décidée avant code. Prérequis des commandes publiques
de cache et d’archives SLS-065 ; aucun nouveau bouton ni droit public livré ici.

## Décision et périmètre

Répéter clear-cache après perte de réponse peut supprimer du cache reconstruit.
`start-discard` exige function_id, operation_id, installation_id, kind
(`clear-cache` ou `purge`) et expected_version. `discard-operation` consulte
les trois UUID, y compris pendant la récupération. L’UID du canal reste
contrôlé ; installation_id identifie le contrôle, responsable des droits
publics et de sa décision irréversible préalable. Il n’y a pas d’annulation.

Une demande identique retrouve l’intention ou le reçu sans second effacement,
même après de nouvelles écritures. Changer propriétaire, type ou version avec
le même UUID est refusé. Les identifiants encore connus dans une intention ou un reçu ne se
réutilisent pas entre configuration et effacement. Les anciennes commandes restent compatibles ;
les futures routes publiques utilisent exclusivement le protocole corrélé.

Un reçu par fonction est conservé, séparément du reçu de configuration. Le
prochain effacement le remplace à sa terminaison. Une demande ancienne porte
alors une version périmée et sa consultation rend operation_unknown. La version
progresse aussi pour un cache absent ou une fonction déjà purgée : leur reçu
acquitte une décision sans allocation supplémentaire. Une réutilisation volontaire
d’un ancien UUID oublié avec une version actuelle n’est pas une répétition
demande/réponse et n’est pas détectable par cette rétention bornée. Le contrôle
génère un UUID neuf par décision et conserve les paramètres initiaux à la reprise.

## États et effets

Après recherche du reçu ou de l’intention identique, une nouvelle demande
vérifie version, absence d’intention et absence de tout bail.
clear-cache exige active ; purge exige archived ou purged. Elle inscrit
l’intention avant toute opération physique et rend pending ; un cas sans
contenu à retirer produit directement completed. Les acquisitions et mutations
de la fonction restent bloquées. Purge place la fonction en purging.

Un worker unique traite les intentions corrélées en ordre stable. Sous le
verrou du registre, il arrête les volumes, confirme les démontages et détache
le backing vers sa corbeille identifiée : cache seul ou les deux volumes.
Le déplacement et ses parents sont synchronisés avant l’état erasing.
La suppression récursive se déroule hors du verrou global : les autres
fonctions peuvent acquérir, vérifier ou libérer leurs baux. La maintenance ne
lance aucun effacement concurrent sur la même corbeille. Les anciennes
intentions gardent leur chemin de reprise historique.

Après suppression et synchronisation de la corbeille, finalizing est persisté
avant de recréer le cache vide : une reprise ne le redétache pas. Reçu completed,
nouvelle version, retrait d’intention et allocations finales sont atomiques.
clear-cache conserve données, configuration et quotas ; purge libère les
allocations après nettoyage confirmé et conserve le tombstone.

Une erreur physique garde l’intention, sa réservation et un code fixe ; la
maintenance reprend. La consultation rend state pending, phase
stopping/erasing/finalizing et error_code, ou completed et error_code null.
Elle inclut UUID, kind, expected_version et version, sans chemin système.
La déconnexion n’annule rien. Un restart reprend la même intention. Un arrêt
gracieux rejoint le worker avant fermeture SQLite ; une interruption par la
borne systemd conserve l’intention. Les baux existants restent protégés.

## Migration et installation

Migration 004 du registre agent : discard_receipts avec function_id unique
référencé, operation_id unique, installation_id, kind, expected_version et
version. pending_json conserve les identifiants, la phase et error_code.
Le paquet immuable inclut migration et module. Aucune variable, dépendance ou
migration du contrôle. Installation saine sans bail, montage ni intention ;
conservation des données/identités et sauvegarde native préalable du registre.
Un ancien agent refuse la version 004 ; revenir exige une restauration
cohérente explicitement préparée, pas le seul remplacement du paquet.

## Qualification réelle

Client dans le seul SPARK DEV, socket installé sous UID autorisé, vrais
conteneurs Docker et montages FUSE. Rapport invalidé avant prérequis, UUID
propres suivis, fautes restaurées et nettoyage confirmé ; zéro échec/skip.
Groupes : trames strictes/champs/UUID/types/versions/états ; baux et préparations
concurrents ; propriétaire et identifiants croisés ; vidage/data conservées/quota
et cache désactivé ; cache absent/purge/tombstone/budget ; réponse réellement
perdue puis consultation/rejeu après nouvelle écriture ; remplacement de reçu
et refus d’ancienne version ; erreur de permissions et reprise ; restart et
SIGKILL avec intention observée ; effacement volumineux observé simultanément
à l’usage des baux d’une autre fonction ; persistance et migration recoupées.

Régressions en série : agent-test, limits-test, storage-preparations,
managed-storage, puis function-storage et public-invocations HTTPS. Les preuves
de composant ne ferment ni SLS-050 ni SLS-065. Le manuel utilisateur change
avec les commandes publiques et n’anticipe pas leur disponibilité.
