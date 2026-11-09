# Registre persistant de l’identité du code

Checkpoint additif de l’étape 2 de [SLS-074](BACKLOG.md#sls-074), après
[l’identité canonique qualifiée](FUNCTION_CODE_HASH.md). Il prépare la
déduplication et la promotion sans modifier encore la publication ni les appels.
La livraison complète reste définie par [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md).

## Migration et conservation

La migration `007_function_code_hash.sql` ajoute `revisions.code_hash` et son
index par fonction/hash/date/UUID. Le calcul utilise la bibliothèque canonique
commune, l’inventaire original de l’extracteur et le descripteur immuable stocké
avec chaque révision. Il s’exécute dans la transaction de migration, avant que
le contrôle accepte des requêtes. Un inventaire ou descripteur invalide fait
échouer et annuler cette migration ; aucun hash approximatif n’est fabriqué.

Un tombstone déjà purgé, supprimé, sans octet conservé et dont l’inventaire
a été effacé reste à `NULL` : le contenu inconnu ne peut être reconstitué.
Une révision active ou dont le code reste disponible ne bénéficie jamais de cette
exception. La correction en qualification reconnaît aussi une purge 006 déjà
décidée et fortement corrélée : fonction supprimée sans pointeur, même opération,
service, propriétaire et versions de commande/garde. Le code déjà retiré du
catalogue garde alors une identité inconnue pendant son nettoyage, sans effacer
ses compteurs ni contourner sa garde. Les critères et la preuve des phases
volumes/artifacts sont définis dans [FUNCTION_VERSION_PURGE_UPGRADE](FUNCTION_VERSION_PURGE_UPGRADE.md).
Les nouveaux inserts exigent un hash canonique ; un hash connu ne peut être
modifié ni effacé, y compris lors d’une purge ultérieure.

L’index n’est pas unique : deux UUID historiques peuvent désigner le même
contenu. Les fusionner physiquement ferait perdre les références de candidats,
d’invocations et d’audit. Le registre regroupe ces alias sans changer leurs UUID,
le pointeur actif, la date, les fichiers, les volumes ni la configuration.
Cette représentation permettra ensuite de réutiliser un alias disponible à
l’upload sans créer un nouveau doublon. La déduplication des nouveaux uploads
et la séparation publication/promotion sont le checkpoint suivant de l’étape 2.

## Lecture autorisée

`GET /api/functions/{id}/revisions` ajoute `code_hash` à chaque révision.
`GET /api/functions/{id}/versions?limit=5&offset=0` offre une vue groupée :
`function_id`, `service_id`, `active_revision_id`, `active_code_hash`, `items`,
`total`, `limit`, `offset`. Les bornes sont 1–100 et 0–10000, comme l’historique.

Chaque item fournit `code_hash`, `revision_id` représentatif, `revision_count`,
`created_at` initial, `active` et `state` (`available` ou `deleted`). Le représentant
est d’abord l’alias actif, sinon le premier alias disponible, sinon le premier
historique, à date puis UUID. Un alias est disponible s’il n’est pas supprimé
et conserve ses fichiers comptabilisés. Le tri des groupes est date initiale
décroissante puis hash ; le total est calculé avant pagination. Les tombstones
sans identité connue ne deviennent pas des versions et ne figurent pas dans ce
total. L’API ne fournit ni inventaire, ni sources, ni configuration ou secrets.

Session administrateur ou jeton Read de la bonne portée sont requis. Les droits,
la disponibilité de la fonction, du service et du namespace sont revérifiés dans
le même snapshot que le pointeur et les groupes. Une fonction inconnue ou d’un
autre service ne révèle pas son catalogue à un jeton non autorisé.

## Console et manuel

La carte de chaque révision montre le hash complet avec **Copier le hash du
code**, utilisant le presse-papiers natif et les composants existants. Une copie
réussie seule affiche une confirmation ; un refus laisse le texte sélectionnable
et un diagnostic utile. Le retour de copie est retiré à la prochaine observation
ou navigation. Aucun nouveau contrôle d’invocation ou de promotion n’anticipe
le comportement restant à réaliser. Le manuel décrit l’identité sans confondre
hash du paquet exécutable et SHA256 des octets ZIP.

## Déploiement et retour arrière

Avant mise à jour, produire via les API existantes une fonction avec A, A
identique et B, puis un rollback vers le second alias A, ainsi qu’une archive
de fonction effectivement purgée. Effectuer une sauvegarde native SQLite avec
`Connection.backup`, intégrité vérifiée, et relever les anciennes colonnes,
inventaires de fichiers et configuration/volumes sous leur propriétaire.
La sauvegarde est privée au SPARK, jamais copiée dans les preuves publiques.
La référence historique 006 est reconstruite depuis son arbre Git vérifié et
conservée sous un tag dédié ; sa présence est contrôlée avant toute bascule.

Construire et démarrer uniquement le contrôle DEV par ses commandes normales.
Ne pas revenir à une ancienne image seule après migration : une restauration
demande arrêt, base sauvegardée, fichiers/volumes correspondants et ancienne
image. Aucun down SQL destructif automatique. La migration additive est
transactionnelle ; un refus laisse le schéma 006 utilisable par l’ancienne image.

## Preuves réelles requises

Le client maintenu prépare la fixture avant upgrade, puis vérifie après upgrade :
les trois UUID et leurs références, les deux hashes, l’alias actif conservé,
configuration et données persistantes, aucune réécriture des artefacts,
tombstone sans hash, nouveau code calculé par le serveur, groupement/pagination,
refus d’accès et bornes. Un redémarrage réel confirme la persistance sans recalcul
des identités déjà migrées. Les hash attendus viennent des vrais paquets extraits,
pas d’un inventaire envoyé par le client à l’API.

`function-version-migration-faults.py` démarre aussi la vraie application dans
des conteneurs sans réseau sur des copies privées du backup 006 : inventaire
absent/invalide et descripteur invalide. Chaque refus doit précéder l’ouverture
HTTP et annuler entièrement 007. Une copie migrée par la vraie bibliothèque
éprouve les contraintes SQLite (hash requis, format et immutabilité, y compris
NULL), avec insertion valide témoin et rollback des seules écritures de sonde.
Le backup d’origine et la base partagée ne sont jamais modifiés par ce client.

Avant la régression commune, les clients HTTP de preuve de démarrage, le
concurrent de verrou et les conteneurs sources des fixtures runtime reçoivent
un nom de responsabilité explicite avec suffixe d’unicité. La règle locale
de nommage s’applique aussi à ces anciens clients. Les vues desktop/mobile
du chapitre Gérer les révisions ciblent directement le nouveau paragraphe,
en complément de la comparaison de contenu du manuel entier.

La qualification UI part de l’accueil et des formulaires, publie réellement,
copie le hash au clavier, constate le refus natif du presse-papiers et inspecte
desktop/mobile. Le manuel compilé est recoupé. Les campagnes de publication et
de schéma concernées sont rejouées en série ; les listes de migrations attendent
007, tout en conservant l’ancien schéma initial du banc historique.
Rapports incomplets et erreurs restent conservés séparément ; aucune simulation,
interception réseau ou réussite conditionnelle. L’API, Docker, SQLite et l’agent
de stockage sont ceux du seul SPARK DEV. Le checkpoint ne clôt pas SLS-074.
