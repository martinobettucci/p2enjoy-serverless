# Première identité inconnue et versions ultérieures connues

Complément de [SLS-074](BACKLOG.md#sls-074), du
[contrat008](FUNCTION_VERSION_EXECUTION.md#autorité-persistante-et-migration)
et des preuves de [purge historique](FUNCTION_VERSION_PURGE_MIGRATION_008.md).
Aucune modification produit n'est prévue avant les résultats du banc.

## Constat et décision

L'API006 conserve inventaire et événements lors de la suppression individuelle
d'une révision : seuls deleted_at puis stored_bytes changent. Le hash de A reste
donc calculable après A/B puis suppression de A. Les versions de publication
antérieures consultées depuis003 ont le même comportement. La purge publique006
vide ces métadonnées pour toute la fonction déjà supprimée ; aucune restauration
publique de cette fonction ne permet ensuite B active. Le scénario API seul ne
produit pas « première identité inconnue, B connue et active ».

Décision : qualifier deux entrées distinctes. Le témoin réel est entièrement
produit par les API006 : A, invocation A, B, invocation B, suppression A et
nettoyage. La variante contrôlée part de ce même état sur l'installation privée
de qualification arrêtée. Elle retire uniquement inventory_json et events_json
de A, déjà supprimée, sans octet ni artefact, et conserve B active. La sauvegarde
API006 originale reste séparée et intacte. Cette variante est une préparation
de données anciennes admises par le schéma, pas un résultat attribué à l'API006.
Elle n'est jamais appliquée à l'installation servie ni à un backup original.

Les deux chemins passent ensuite par la vraie image007 attestée puis l'image008
courante. Observer une vraie base007 avec cacheNULL pour A et cache connu pour B
avant008. Les migrations, serveurs, SSO, agent de stockage et handlers Docker sont
les composants réels ; aucune dépendance ou réponse n'est remplacée. Les fichiers
et champs modifiés par la préparation sont explicitement identifiés et vérifiés.

## Fenêtre et conservation

Étendre la fenêtre gardée de storage-legacy-environment.py par un mode nommé
function-version-unknown-first. Son répertoire, projet, namespace, conteneur
API temporaire et garde portent des noms de responsabilité distincts des purges.
Vérifier références006/007 et cible008, disponibilité des images et repos avant
interruption. Conserver le contrôle original par ID/image, les identités des
répertoires state/storage/channel, leurs tables et artefacts. La garde figée
restaure ces originaux ; leur démarrage change et doit être recoupé.

La configuration reste exclusivement celle des deux env_file officiels. Ni route
ni variable nouvelle. Une seule fenêtre/test à la fois. Le mode historique et
les gardes précédentes restent compatibles ; les journaux restaurés existants
restent lisibles. Une précédente fenêtre non restaurée interdit la suivante.

Avant chaque bascule, attendre la disparition des instances et baux réels, arrêter
le seul contrôle temporaire et vérifier l'absence de consommateurs. Conserver
les backups SQLite natifs006 et007 en0600 sous propriétaire1001, avec empreintes
et anciennes colonnes de tables. La préparation de A s'effectue sous ce même
propriétaire, contraintes activées et transaction unique, après vérification du
pointeur B et de l'absence d'artefact A. L'UPDATE doit toucher exactement A ;
les autres champs et lignes sont conservés. Aucun cache007 n'est réécrit.

## Matrice publique et marqueurs

Deux fenêtres normales de sept groupes chacune :

1. API006 : SSO, service/configuration/secrets et jetons réels, publications A/B,
   deux invocations, suppression A et effacement physique, B toujours active.
2. Migration : sauvegarde006, préparation déclarée selon variante, vraie007,
   invocation B puis vraie008, pointeur/UUID/dates et anciens champs conservés.
3. Lecture008 : registre, premiers marqueurs, invocation B par défaut et par hash,
   événements et configuration/service/secrets conservés par empreinte.
4. Droits et pilote : Create/Read ne publient ni ne promeuvent ; Update publie C
   sans déplacer B, C invocable par hash. Les marqueurs historiques ne changent pas.
5. Désactivation puis restauration : B archivée avec disable_default explicite,
   appel sans tag refusé, Create ne retrouve aucun droit de première promotion,
   restauration et promotion Update réussies avec les marqueurs inchangés.
6. Persistance et nettoyage : restart réel008, B/C et compteurs données/cache
   persistants ; suppression et purge publiques terminées, artefacts/volumes absents.
7. Restitution : originaux, tables, artefacts et configuration identiques ; contrôle
   et agent sains, ressources temporaires absentes et garde désarmée.

Une troisième fenêtre de trois groupes reprend la variante inconnue jusqu'à008
puis éprouve la restitution indépendante après perte réelle du pilote. Elle
retire son installation temporaire ; elle ne compte pas comme purge publique
terminée. Total prévu17 groupes, sans ajouter les campagnes antérieures.

Le témoin garde A connue et deleted dans le registre. La variante conserve
first_published_code_hash=NULL et first_promoted_at=date de A, jamais la date de B.
A inconnue ne crée aucune version de remplacement ; seule B est disponible avant C.
Le pointeur reste B. Les invocations historiques d'A gardent un résoluNULL pour
la variante ; celles de B conservent son hash. Le demandé historique resteNULL.
Les marqueurs résistent à upload C, archivage, désactivation, restauration,
promotion, redémarrage et suppression/purge. Les deux flux gardent leurs UUID.

Les appels exécutent le handler original function-versions.cjs dans le vrai
runtime Docker, avec compteur/data et compteur/cache, variables et secret par
empreinte. Le header de hash est exigé seulement après008. Les contrôles d'accès
utilisent de vrais jetons Create/Read/Update limités à la fonction. Une erreur
ou une fenêtre manquée reste un échec conservé, aucun skip ni rejeu automatique.

## Livraison et limites

Rapports frais liés aux sources, images et références ; nettoyer puis recouper
les états physiques, backups, gardes et originaux. Les trois notes de SPARK sont
proposées sans adoption implicite, avec le nouveau démarrage du contrôle. README,
backlog, journal, schéma, changelog et preuves distinguent données API réelles
et préparation contrôlée, sans requalifier les anciennes campagnes.

Aucun nouveau parcours UI ni changement de manuel attendu. Les autres fenêtres
d'interruption, pannes propres de garde et la régression complète restent dans
SLS-074. Les garde-fous déjà qualifiés sur les autres modes ne remplacent pas
les preuves du nouveau mode.
