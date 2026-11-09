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

## Livraison et limites

Recouper l'image courante avant/après, ses fichiers embarqués, la référence,
les fichiers officiels, les identités originales, les tables et artefacts
conservés, les ressources libérées et la fermeture des gardes. Conserver les
sauvegardes privées des véritables états d'entrée pour les refus de corrélation
ultérieurs. Les résultats, sources exactes, tentatives exclues, commandes et
limites sont liés à la preuve. Actualiser README, backlog, journal, changelog et
les trois notes proposées au SPARK, sans adoption implicite.

La variante premier hash inconnu suivi d'un connu, les autres fenêtres de panne
et la campagne complète restent dans SLS-074. Aucune évolution UI ou du manuel
n'est introduite par ce banc ; aucune nouvelle qualification visuelle n'en découle.
