# Versions de fonction identifiées par leur code

Contrat de [SLS-074](BACKLOG.md#sls-074), demandé le 8 novembre 2026.
Cette extension est à implémenter. Le produit possède déjà des révisions
immuables, leur historique et une activation permettant le rollback ; il ne
fournit pas encore la déduplication par contenu, les tags d’invocation ni
l’archivage individuel décrit ici. Le manuel reste celui du comportement livré.

## Identité et déduplication

La fonction conserve son UUID. Une version possède comme tag public l’empreinte
SHA256 complète de son paquet exécutable, en hexadécimal minuscule sur 64 caractères.
Ce tag est immuable et limité à cette fonction ; connaître un hash d’une autre
fonction ne donne aucun accès à celle-ci. Les UUID internes de révision peuvent
rester utilisés pour l’audit et les migrations, sans devenir des numéros de version.

Le hash est calculé et vérifié par le serveur après extraction sûre. Il porte
sur un inventaire canonique des chemins, contenus et bits exécutables des
fichiers livrés, dépendances comprises, et le descripteur d’exécution immuable :
handler, runtime et architecture, image runtime immuable et événements déclarés.
L’ordre des fichiers, les horodatages, le niveau de compression et les métadonnées
sans effet du ZIP ne créent pas de version. Le format canonique est versionné
et identique dans le packager et le contrôle ; sa sérialisation exacte est
documentée avant l’implémentation. Un changement de handler ou de dépendance
exécutable est donc un changement du paquet, même si le source principal reste identique.
Le nom, l’UUID et le service de rattachement ne participent pas au hash. Un
événement implicite est représenté comme tel, sans chemin dérivé du nom de la
fonction ; un simple renommage suivi du même upload conserve donc le tag.
Les véritables chemins HTTP déclarés restent dans le descripteur de version.

Les variables, secrets, quotas et réglages d’allocation restent distincts du
code ; ils ne sont pas intégrés au hash ni rétablis par un rollback de code.
Une évolution de leur configuration garde le contrat service/surcharges de
SLS-031 et sa génération d’exécution propre.

Après upload d’un paquet identique à une version disponible, l’opération
réutilise son tag et ne crée ni nouvelle version ni doublon durable d’artefact.
Le résultat distingue explicitement code inchangé et nouvelle version, avec le
tag effectivement retenu. Une tentative conserve son audit et son suivi propres.
Deux uploads identiques concurrents convergent vers une seule version de la
fonction. Le serveur ne se fie jamais à un hash simplement annoncé par le client.

Réutiliser un hash ancien encore disponible n’en change pas la date de création
et ne le fait pas passer silencieusement pour un nouveau code. Seule une promotion
explicite peut en faire la cible par défaut, comme un rollback explicite. Un upload
identique à la cible courante ne modifie pas inutilement son pointeur ni ne
redémarre les instances. Toute autre configuration envoyée dans un déploiement
reste une mutation séparée, contrôlée et rapportée selon SLS-031.

## Appel par défaut et appel par tag

Sans tag, l’appel vise la dernière version explicitement promue comme cible
par défaut de la fonction. L’upload valide et prépare une version disponible
par son hash ; il ne déplace jamais ce pointeur, y compris au premier upload.
La promotion constitue une action distincte et met à jour ce pointeur atomiquement.
Sans première promotion, l’appel sans tag indique l’absence de cible ; l’appel
explicite du hash disponible reste possible avec les droits requis.
Le rollback remplace ce même pointeur par le hash choisi ; un appel sans tag
suit alors ce choix explicite, même si son code a été créé plus tôt.

Un appel portant un hash sélectionne exactement cette version, tant qu’elle
est disponible. Il ne suit ni une nouvelle publication, ni un rollback, et ne
se rabat jamais sur la cible par défaut. Un hash mal formé, inconnu, archivé
ou supprimé ne déclenche aucun autre code. Les règles d’authentification et
de non-divulgation s’appliquent avant toute réponse sur sa disponibilité.

Les URL sans tag existantes restent valides. La forme versionnée prévue est
`/invoke/{function_id}@{code_hash}` et, pour un événement HTTP explicite,
`/invoke/{function_id}@{code_hash}/{chemin}`. Le sélecteur est placé dans le
segment d’identité, pour ne pas consommer un chemin métier, un paramètre ou
un en-tête transmis au handler. SLS-066 calcule ces URL pour chaque domaine
d’invocation autorisé. Aucun préfixe abrégé du hash n’est accepté à l’appel.

Le jeton Read, sa portée de service/fonction, sa révocation et les restrictions
origine/IP restent obligatoires. Le hash n’est pas un secret d’accès. Le
préflight utilise les événements de la version demandée, sans exécuter de code.
L’authentification métier conserve son en-tête Authorization.

Create autorise la fonction, sa première publication et la première promotion
de cette version, tant qu’aucune promotion antérieure n’existe. Update autorise les
publications suivantes ainsi que les promotions suivantes, l’activation,
le rollback, l’archivage, la restauration et la suppression individuelle des
versions, dans la continuité des droits existants sur les révisions. Delete
reste le droit de supprimer la fonction. Une portée limitée à des fonctions
est revérifiée pour chaque action et à sa décision durable ; le droit Read
seul ne permet aucune mutation de version ni téléchargement des sources.

La version résolue est figée à l’admission. Promotion, publication ou rollback
ne modifient pas le code d’un appel déjà admis. Le hash demandé et le hash
résolu sont corrélés avec l’invocation, l’instance, les journaux et les mesures.

## Pilote et maintien de la version stable

Les clients de production utilisent l’URL sans tag ou restent fixés sur un hash
stable pendant que les utilisateurs pilotes appellent explicitement le nouveau
hash. Publier un nouveau code ne modifie ni la cible sans tag, ni celle d’un
appel portant un ancien hash.

**Publier une version** valide et conserve le nouveau hash. **Promouvoir cette
version** la rend ensuite courante pour les appels sans tag ; revenir à un hash
antérieur utilise la même opération atomique et auditée. Publication et promotion
sont deux actions distinctes dans la console et la CLI. Le résultat indique le
hash disponible et la cible promue séparément, sans promotion automatique.

Le mode pilote de la CLI publie uniquement le code et son descripteur, en
conservant variables, secrets, quotas et réglages courants. Il ne réapplique pas
les catégories provider du manifeste avant un test de code. Le déploiement
complet garde ses mutations de configuration séparées et visibles.

La version fixe le code exécutable. Les configurations applicatives restent
celles de la fonction et du service à l’admission. Les versions partagent les
volumes attachés à l’UUID de la fonction, selon ses règles données/cache ; un
rollback ne restaure pas les données. Les politiques de stockage et les quotas
restent appliqués à la fonction, y compris entre stable et pilote simultanés.
Le snapshot d’exécution compose ces ressources, variables et secrets courants
avec le handler, le runtime, l’image et les événements provenant exclusivement
de la version sélectionnée. Le handler de la cible courante ne remplace jamais
celui d’un ancien hash invoqué explicitement.

## Instances, limites et archivage

Les pools d’instances distinguent version et génération de configuration.
Un appel épinglé ne réutilise jamais une instance d’un autre code. CPU, mémoire,
maximum d’instances, concurrence, file et espace restent comptés pour toute
la fonction, toutes versions confondues, ainsi que dans les budgets globaux.
Les minima préchauffés concernent la cible par défaut ; les autres versions
démarrent à la demande et suivent le délai d’inactivité configuré.
Les déclenchements cron de SLS-050 suivent uniquement la cible courante ;
publier pour un pilote sans activer ne crée pas de second déclenchement planifié.

Archiver une version conserve son code et son historique mais interdit les
nouveaux appels, y compris ceux en attente d’admission. Les appels déjà admis
peuvent terminer dans leurs limites. Restaurer une archive est une action
explicite ; connaître son tag ou renvoyer le même paquet ne la restaure pas
silencieusement. La suppression retire la version du catalogue invocable et
attend la fin des consommateurs avant l’effacement physique.

La cible par défaut ne peut être archivée ni supprimée sans désigner une autre
version disponible dans la même transaction, ou désactiver explicitement la
fonction. Aucun nettoyage de rétention ne rend un tag indisponible en silence.
La limite de versions bloque une nouvelle publication avec un diagnostic et
les actions d’archivage/suppression possibles ; les doublons ne consomment pas
de place supplémentaire. Les versions archivées restent comptabilisées au budget
réel de code tant que leurs fichiers existent.
Un upload identique reste admis au plafond de versions : la déduplication
précède la consommation définitive d’un emplacement. Les limites globales de
candidats et les réservations temporaires de réception restent appliquées ;
annoncer un hash existant ne permet pas de les contourner. Un paquet réellement
nouveau au plafond échoue sans modifier les versions ou la cible courante.

Une réimportation d’un hash retiré doit suivre un parcours explicite de
restauration ou de nouvelle conservation du même contenu, avec audit et
validation réelle ; elle ne crée pas un second tag pour ce même paquet.
La migration des révisions existantes conserve UUID de fonction, pointeur
courant, code, événements et audit ; elle documente et traite les doublons
historiques sans perte de références ou de données.

## Console, adaptateur et preuves

La fiche **Code et révisions** montre hash complet copiable, cible par défaut,
disponibilité, dates et résultats de validation. Elle permet publication,
promotion/rollback, archivage/restauration et
suppression. Les confirmations nomment la fonction et le hash concerné. Le
client HTTP SLS-071 choisit cible par défaut ou tag précis et montre le hash
effectivement exécuté. L’éditeur SLS-070 réutilise un hash si son paquet n’a pas
changé. Le manuel est mis à jour et reconstruit avec la livraison effective.

Les preuves utilisent les véritables API, CLI, Docker et navigateur du SPARK DEV :

- paquet identique réuploadé et ZIP recompressé/réordonné sans nouvelle version ;
- renommage puis même upload conservant son hash, y compris avec événement implicite ;
- doublon admis au plafond de versions et nouveau code refusé sans modifier la cible ;
- modification de source, dépendance, bit exécutable ou handler créant un hash distinct ;
- deux uploads identiques concurrents, validation refusée et absence de doublon après reprise ;
- appels simultanés à l’ancien hash, au nouveau et sans tag, avec effets distincts observés ;
- handlers différents entre deux versions, avec handler/runtime/événements du hash sélectionné ;
- publication sans activation puis activation et rollback, en conservant un appel déjà admis ;
- première publication invocable par hash, appel sans tag refusé avant promotion, puis première promotion explicite ;
- refus Read/portée, origine/IP, hash inconnu et version archivée/supprimée sans repli ;
- archivage pendant attente/appel vivant, restauration, suppression et nettoyage physique ;
- budgets communs réellement saturés par plusieurs versions et fin des instances au repos ;
- déclenchement cron de la seule cible courante, puis bascule/rollback sans double exécution ;
- migration des révisions historiques et conservation des volumes/configurations ;
- réponse perdue et SIGKILL aux étapes de publication/déduplication/activation/nettoyage ;
- parcours depuis l’accueil, copie du hash et des URL, pilote et rollback au clavier/mobile,
  journaux corrélés, captures inspectées et concordance du manuel compilé.
