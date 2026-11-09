# Reprise des purges historiques pendant la transition008

Complément de [SLS-074](BACKLOG.md#sls-074) et de
[FUNCTION_VERSION_EXECUTION](FUNCTION_VERSION_EXECUTION.md#autorité-persistante-et-migration).
Le banc006→007 de [FUNCTION_VERSION_PURGE_UPGRADE](FUNCTION_VERSION_PURGE_UPGRADE.md)
reste une preuve historique distincte. L'image servie au début de ce complément
est def45648 ; aucune modification produit ni construction d'image n'est prévue.

## Décision et invariants

Réutiliser la fenêtre DEV gardée de storage-legacy-environment.py, avec les
sources et images historiques réellement qualifiées. Les répertoires originaux
state/storage/channel sont conservés par identité, avec tables et artefacts
recoupés avant leur restitution. Le contrôle original garde son ID et son image ;
son démarrage change après chaque restitution. L'agent de stockage réel et les
fichiers officiels restent les autorités. Aucune route ni configuration nouvelle.

Deux sources de migration sont nécessaires. Une vraie API006 publie puis supprime
et engage la purge du code : son identité est inconnue au passage007/008. Une
vraie API007 réalise le même parcours avec un hash déjà calculé : la migration008
doit conserver ce cache connu. Produire007 par SQL ou effacer manuellement un
marqueur de migration est exclu. La référence007 fe75c9e7 est attestée avant arrêt
de service : fichiers embarqués comparés aux SHA de la preuve du registre,
sept migrations exactes, image et tag dédiés conservés dans un reçu root protégé.
L'attestation006 existante est conservée.

Le client et l'opérateur reçoivent des options explicites source007/cible008.
Le parcours historique sans ces options garde ses attentes006→007. Une cible
incompatible avec le schéma actuellement servi est refusée avant armement,
arrêt ou déplacement. Les nouveaux rapports portent source et cible dans leur
nom et refusent l'écrasement. Les sources sont figées pendant chaque campagne.

## Matrice réelle

Quatre fenêtres :006→008 et007→008, chacune avec entrée volumes puis artifacts.
La publication utilise le ZIP original du dépôt et sa validation Node/Docker.
Suppression et purge sont engagées par les vraies API, avec EACCES sur le seul
répertoire d'artefact corrélé. La phase volumes est capturée par le même
rendez-vous réel que le banc historique ; aucune phase n'est fabriquée par SQL.
Après arrêt du contrôle temporaire, attendre la fin de l'agent et vérifier son
absence de bail, montage ou intention avant la migration.

Chaque fenêtre conserve quatre groupes : préparation publique historique,
migration avec API lisible sous rétention, libération/purge et persistance après
redémarrage, puis restitution vérifiée de l'installation d'origine. Une cinquième
fenêtre007→008/artifacts comprend trois groupes et éprouve la restitution
indépendante après perte réelle du pilote. Total prévu19, sans addition des
anciens replays006→007. Une fenêtre ratée reste un échec conservé, jamais un skip.

Pour les deux sources : UUID, dates, pointeurNULL, commande pending, garde commit
corrélée, charge d'octets et artefact retenu restent identiques. Après008,
first_promoted_at conserve la première publication historique même si la fonction
est supprimée. Depuis006, code_hash et first_published_code_hash restentNULL et
aucune ligne function_versions n'est inventée. Depuis007, les deux caches gardent
le hash connu et le registre porte une version deleted, avec révision canonique
et date historiques exactes. Les anciens champs des publications sont conservés ;
leurs nouveaux code_hash correspondent au cache réel. Les autres données
historiques ne sont pas réécrites.

Après restitution de l'inode par descripteur, le résolveur normal termine :
commande completed, garde absente, octets0, artefact absent, état agent purged,
aucun volume/bail/montage temporaire. Un restart doit conserver ces faits et le
hash connu ou inconnu. Le mode indépendant joint le pilote par pidfd/naissance,
laisse la garde figée restaurer les originaux et vérifie ses reçus et unités.
Les autres pertes ou pannes propres de garde ne sont pas déduites de ce cas.

## Refus avant la fenêtre

Après les cinq fenêtres figées, trois groupes supplémentaires exercent le vrai
opérateur avec des paramètres invalides : cible implicite007 sur installation008,
source007 sans cible008 explicite et image007 présentée comme source006. Chaque
refus doit précéder armement, arrêt et déplacement ; aucun événement guard-armed,
aucun journal de restitution ni unité active. Un éventuel répertoire de travail
vide créé avant le refus est retiré uniquement après identité, propriétaire,
mode et absence de journal vérifiés. Les services, leurs démarrages, les fichiers
officiels et les identités des répertoires restent strictement identiques.
Ces trois groupes portent leur propre époque documentaire et ne transforment
pas les essais interrompus en succès. Total prévu22, dont19 groupes de fenêtres et3 refus.

## Refus de corrélation sur copies007

Décision : partir des deux sauvegardes007 réelles, en volumes et artifacts,
produites par les fenêtres précédentes et identifiées dans leur preuve. Vérifier
journal root restauré, source007, empreinte de backup, propriétaire1001/mode0600,
sept migrations et cache connu. Les originaux s'ouvrent en lecture immutable ; un WAL présent doit être vide,
régulier, non symlink et appartenir au propriétaire1001. Le SHM éventuel est
relevé puis conservé : il n'est pas une source de pages pour cette lecture. Les
empreintes et tailles des sidecars sont recoupées avant/après ; aucune suppression
ou checkpoint de l'archive. Un WAL non vide reste un refus. Chaque mutation porte
uniquement sur une copie privée conservant les contraintes
réelles. Aucun marqueur de schéma ni état de purge n'est fabriqué pour la source.

Chaque phase comprend vingt refus et un témoin positif, soit42 groupes au total :

| Copie fautée | Altération réelle attendue |
| --- | --- |
| missing-purge-guard | Garde retirée |
| different-operation-id | UUID de garde différent |
| aborted-purge-guard | Décision abort |
| different-guard-function | Fonction de garde différente |
| different-guard-service | Autre service réel de la fixture |
| different-command-service | Autre service de commande |
| different-function-service | Autre service de fonction |
| different-guard-kind | Garde clear-cache |
| different-command-kind | Commande clear-cache |
| uncommitted-command | Commande preparing |
| before-purge-phase | Phase draining |
| different-installation | Installation différente |
| different-result-version | Version résultante différente |
| different-command-version | Version attendue de commande différente |
| different-guard-version | Version attendue de garde différente |
| function-not-deleted | Fonction redevenue vivante |
| function-has-active-pointer | Révision rendue non supprimée puis pointeur actif |
| revision-not-deleted | Révision redevenue non supprimée |
| events-not-cleared | Valeur d'événements différente de la purge |
| inventory-not-purge-value | Inventaire JSON vide de représentation différente |

Le cas pointeur respecte le trigger007 en rendant aussi la révision non supprimée ;
il prouve ce cas combiné. Il doit être refusé par historical_active_version_required.
Les autres cas attendent le refus UDF de l'inventaire historique, avant toute
transformation de008. Toutes
les références étrangères restent valides : un autre service réel est réutilisé.
Les contraintes restent activées pendant les altérations et chaque entrée copiée
est vérifiée avant démarrage.

Le véritable uvicorn de l'image servie démarre dans Docker, sous les deux env_file
officiels, réseau none, readonly, mémoire512M/CPU1/PIDs64. Seuls la copie/state et
un tmpfs sont montés ; aucun socket ou volume vivant. Chaque refus exige une
sortie non nulle, le diagnostic exact, aucune application prête, sept marqueurs,
aucun registre008 et un snapshot logique/schéma/tables strictement identique à la
copie fautée avant démarrage. Un échec ultérieur de socket n'est pas un refus.

Le témoin non fauté applique008, conserve les anciennes colonnes des seize tables,
UUID, hash connu, garde/commande et dates ; la version est deleted et les nouveaux
champs de publication/invocation correspondent au vrai cache. Son échec attendu
sur reconcile_docker faute de socket vient après la migration et n'est pas un
succès HTTP. Une relance explicite du même conteneur conserve exactement l'état008
sans rejouer la migration. Ce témoin constitue un seul groupe par phase.

Chaque conteneur est identifié par nom/ID/image/labels/montage avant suppression.
Les rapports refusent l'écrasement. Copies retirées, backups originaux identiques,
contrôle servi/référence/démarrages/configuration et compteurs actifs identiques
avant/après. Une panne du banc arrête la campagne et conserve son échec ; aucun
rejeu automatique ou skip. Aucun nouveau déploiement produit n'est prévu.

## Livraison et limites

Recouper l'image courante avant/après, ses fichiers embarqués, la référence,
les fichiers officiels, les identités originales, les tables et artefacts
conservés, les ressources libérées et la fermeture des gardes. Conserver les
sauvegardes privées des véritables états d'entrée pour les refus de corrélation
ultérieurs. Les résultats, sources exactes, tentatives exclues, commandes et
limites sont liés à la preuve. Actualiser README, backlog, journal, changelog et
les trois notes proposées au SPARK, sans adoption implicite.

La variante premier hash inconnu est qualifiée par le complément dédié ;
les autres fenêtres de panne et la campagne complète restent dans SLS-074. Aucune évolution UI ou du manuel
n'est introduite par ce banc ; aucune nouvelle qualification visuelle n'en découle.


## Résultats qualifiés

La [preuve](evidence/function-version-purge-migration008-dev-2026-11-09.json)
retient22 groupes sans échec/skip :19 groupes de fenêtres sur280 sources puis3 refus sur281
sources. L'attestation007 compare29 backends historiques et conserve tag et reçu
root. Sa première tentative arrêtée avant reçu sur Path.open(opener) reste
archivée ; builtinsopen corrige le pilote, sans changement produit ou de service.

Les quatre fenêtres normales conservent exactement cacheNULL/connu, UUID/dates,
garde et charge, puis terminent purge et restart. La cinquième conserve ces faits
pendant008 puis restitue par garde indépendante après perte du pilote. Les cinq
restitutions retrouvent17 tables et5982 artefacts originaux identiques, ainsi que
le registre de stockage. Le contrôle e661516b garde def45648, avec démarrage
2026-11-09T18:52:49.904838248Z. Les cinq gardes sont inactives, drivers absents,
référence et fichiers officiels conservés, aucun consommateur temporaire ni
ressource active. Les sauvegardes privées d'entrée restent en0600 et identiques.

Les trois refus vérifient strictement tables, services et démarrages inchangés ;
le premier retire son seul dossier vide créé avant refus. Aucune garde armée.
Les31 backends et quatre fichiers HTTPS du contrôle restitué sont identiques
au checkpoint précédent. Aucun nouveau parcours visuel ou changement du manuel.
Les corrélations007 et la première identité inconnue sont qualifiées par leurs
compléments dédiés. Les autres pannes et la campagne complète restent ouvertes
dans SLS-074.


## Résultats des corrélations007

La [preuve](evidence/function-version-purge-correlation008-dev-2026-11-09.json)
retient42 groupes sans échec/skip sur283 sources figées. Les deux sauvegardes007
réelles des phases volumes/artifacts fournissent chacune20 refus et1 témoin.
Les38 refus UDF et2 CHECK du pointeur sont observés avant transformation008,
avec snapshots logiques/schéma/tables strictement identiques en007. Le cas du
pointeur reste explicitement combiné, sous le vrai trigger d'entrée.

Les témoins conservent les anciennes colonnes des16 tables, le hash connu, sa
version deleted, premières dates/hash et backfills. Après008, chaque même
conteneur redémarre et conserve exactement cet état. Son échec ultérieur sur
reconcile_docker faute de socket n'est pas une disponibilité HTTP. La reprise
publique de la purge est portée par la preuve22 précédente, qui n'est pas
réadditionnée au total42.

Les archives principales, WAL0 et SHM32768 restent identiques par SHA, taille,
mode et identité. Aucun sidecar n'est effacé ou checkpointé. Les42 conteneurs
et leurs copies sont retirés. Le contrôle e661516b/def45648, la référence, leurs
démarrages, les17 tables vivantes et fichiers officiels restent identiques ;
aucun bail/montage/intention ni ressource active. Les31 backends et quatre
fichiers HTTPS correspondent à l'image courante précédente.

Le premier essai artifacts s'était arrêté avant copie/conteneur sur une
précondition trop stricte d'absence de sidecars. Il reste archivé, zéro groupe
ajouté ; la lecture immutable avec WAL vide attesté corrige le banc. Une sortie
avant rapport distant reste désormais explicite dans le checkpoint du lanceur.
Les pertes/timeouts du banc et nettoyages en erreur ne sont pas déduits de ces
parcours. Les autres interruptions et la campagne complète restent ouvertes dans SLS-074.


## Complément première identité inconnue

La [première identité inconnue](evidence/function-version-unknown-first-dev-2026-11-09.json) passe17 groupes sur286 sources :
un témoin entièrement issu des API006, une variante de données anciennes déclarée
qui retire seulement deux métadonnées de A déjà supprimée dans la copie privée,
puis une restitution indépendante pendant un handler008 observé actif. Les vraies
images006→007→008 conservent pointeur B, UUID/dates et marqueurs ; le premier hash
resteNULL dans la variante, sans rétablir les droits Create. C pilote reste
invocable par hash, B demeure stable jusqu'à promotion explicite. Deux purges
publiques terminent ; la troisième installation temporaire est retirée par garde.
Les23 appels réussis recoupent configuration, secret par empreinte et compteurs
données/cache. Les originaux,17 tables et5982 artefacts sont conservés ; même
contrôle def45648/e661516b, nouveau démarrage attendu 2026-11-09T20:16:45.245982432Z. La garde indépendante
retire exactement une instance, un réseau et un bail par le vrai agent ; les trois
gardes sont inactives, ressources actives nulles. Les essais antérieurs restent
séparés du replay final. Les pannes propres de garde, autres interruptions et
la régression complète008 restent dans SLS-074, toujours[~].
