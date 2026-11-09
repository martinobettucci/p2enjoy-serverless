# Publication, promotion et exécution d’une version par hash

Spécification de la suite de [SLS-074](BACKLOG.md#sls-074), après le
[registre qualifié](FUNCTION_VERSION_REGISTRY.md). Le contrôle008 est déployé en DEV pour qualification :
publication et promotion sont séparées, et la sélection par hash est raccordée.
La migration réelle et sa reprise passent deux groupes ciblés, puis douze groupes
API passent sur240 sources recoupées. Les autres preuves restent ouvertes. Les critères de [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md)
restent tous applicables.

## Livraison cohérente

La publication sans promotion est raccordée à l’admission par hash avant sa
bascule DEV : un pilote doit pouvoir essayer le code préparé. L’unité comprend
le registre d’état des versions, déduplication, promotion, sélection HTTP/pools,
archivage/restauration/suppression, catalogue d’URL et commandes CLI/UI utiles.
Les extensions éditeur/client HTTP/monitoring conservent leurs unités propres.
Le cron reste suivi par SLS-050 ; son exigence de cible courante n’est pas supprimée.

Les fichiers produit sont préparés ensemble dans le dépôt, puis construits et
qualifiés sur le seul SPARK DEV. L’image007 nommée, la base, les artefacts et le
registre de volumes sont conservés avant migration. Aucun déploiement partiel
ne change silencieusement la sémantique de l’upload en service.

## Autorité persistante et migration

La migration008 crée `function_versions`, clé `(function_id, code_hash)`, avec
révision canonique, date initiale, état `available`/`archived`/`deleted` et date de
modification. Le hash reste celui du format canonique v1 ; la nouvelle table
porte la disponibilité et les actions, pas un autre calcul d’identité.

Les groupes connus de007 sont repris sans fusion ni suppression des UUID.
La révision canonique est l’alias actif, sinon le premier disponible, sinon le
premier historique à date/UUID. Elle reste stable lors d’une promotion ; seule
une nouvelle conservation explicite d’un hash supprimé peut la remplacer par
une nouvelle révision validée. Les tombstones sans hash ne créent pas de version.
L’état est available si un alias non supprimé conserve son code, deleted sinon.
La cible existante est conservée exactement pendant la migration.

`functions.first_published_code_hash` identifie la première publication réussie.
`functions.first_promoted_at` établit durablement qu’une promotion a déjà existé.
Ces champs ne sont pas remis à zéro en désactivant la cible ou supprimant la
fonction. Pour l’historique antérieur, toute révision publiée a été activée par
l’ancien contrat : la première date de révision marque cette promotion passée.
Le premier hash publié est pris sur la première révision historique, s’il est
connu ; une identité inconnue ne redevient pas une première promotion Create.
Les nouvelles fonctions commencent avec les deux champs NULL.

La migration ajoute aux invocations les hashes demandé et résolu. Le résolu
historique vient du cache de sa révision, s’il existe ; le demandé reste NULL
puisqu’aucun sélecteur n’existait. Les instances exposent leur hash par le cache
immuable de leur révision et par leur snapshot, sans réécrire leurs identités.
Les insertions de révisions/candidats/instances utilisent des colonnes explicites.

## Publication et déduplication

Le serveur reçoit, extrait et valide réellement le paquet avant déduplication.
Les bornes globales de candidats, réservations temporaires et marge disque
restent appliquées. Le plafond définitif de vingt versions conservées compte
les hashes available et archived, non les alias UUID. Il est contrôlé après
calcul : un doublon disponible reste admis au plafond, un nouveau hash est refusé.

Sous la transaction qui revérifie identité, portée, fonction/service et versions
attendues, un hash disponible réutilise la révision canonique, sans toucher sa
date initiale ni déplacer la cible. Un hash nouveau conserve une nouvelle
révision et son état available. Le premier succès fixe first_published_code_hash.
Un hash archived exige une restauration explicite ; un hash deleted exige une
réimportation explicitement liée à ce hash et réellement validée. L’upload normal
ne restaure aucun de ces états en silence.

Le candidat garde son UUID, son audit, `code_hash`, `code_changed`, la révision
retenue, la version résultante de fonction et la cible par défaut observée à
publication. Ces métadonnées décrivent ce moment ; la lecture actuelle de la
fonction reste l’autorité de la cible présente. Une réutilisation conserve une
responsabilité de nettoyage du paquet reçu : ses octets restent réservés jusqu’à
effacement physique confirmé. Le sweep reprend aussi ces candidats published
réutilisant un autre UUID. Le nettoyage général respecte toujours la garde de purge.

La publication seule ne change ni active_revision_id, ni la génération de
configuration, ni updated_at de la fonction. Elle modifie le catalogue de versions
et ses propres dates. Cela permet aux candidats de code identiques concurrents
de converger sous SQLite sans faire échouer le second pour une fausse mutation
de configuration. Au plus quatre uploads sont admis simultanément ; leur réception et extraction
sont bornées et réservées séparément. Une seule validation Docker s’exécute à la
fois, avec attente asynchrone des autres candidats admis. Deux uploads identiques
réellement admis et concurrents, avec configuration inchangée et mêmes versions
attendues, aboutissent ainsi au même hash et à la même révision, dont un seul
crée le code. Une mutation de configuration concurrente conserve son conflit
d’ETag normal. Un refus429 à la capacité ne vaut pas succès
de convergence et se relance explicitement. Le contrôle suit ses uploads vivants
pour que sa maintenance ne les classe jamais comme interrompus.

Un déploiement complet peut aussi demander des ressources/variables/secrets.
Cette mutation demeure séparée du choix du code et respecte SLS-031 et la décision
durable de stockage. Si elle change réellement ces valeurs, elle met à jour le
parent et son ETag ; les champs handler/runtime de la cible restent ceux de la
version promue. Le mode code seul ne réapplique aucune de ces valeurs.

La préparation de code seul accepte des événements optionnels : leur absence
reprend ceux de la cible promue, ou l’événement implicite initial sans cible.
Des événements explicites permettent un pilote avec un autre descripteur.
Les deux préparations acceptent restore_code_hash pour la réimportation explicite.
Le candidat conserve code_only pour distinguer les mutations demandées ; son
résultat expose également version_restored et la cible observée à publication.

Create couvre la première publication. Un candidat Create déjà préparé peut
converger vers ce même premier hash disponible, sans autre mutation ; il ne peut
pas créer B après A, modifier la configuration existante, ni restaurer une version.
Les droits sont revérifiés après validation et dans la transaction définitive.
Les mutations incertaines ne sont jamais rejouées automatiquement.

## Promotion et droits

`POST /api/functions/{id}/versions/{hash}/promote`, avec If-Match de la fonction,
choisit atomiquement une version available de cette fonction. La première
promotion de first_published_code_hash est autorisée par Create tant que
first_promoted_at est NULL. Toute autre promotion exige Update, y compris celle
de B préparé par Update avant toute promotion de A. Read seul reste refusé.

La décision vérifie la portée avant exposition de l’existence du hash puis dans
la transaction. Elle fixe active_revision_id, handler/runtime par défaut,
first_promoted_at s’il était NULL, updated_at et audit. Promouvoir le hash déjà
courant ne remplace pas son alias et ne redémarre aucune instance inutilement.
Les UUID historiques restent présents ; les actions par UUID résolvent leur hash
et passent par la même autorité, sans contourner l’archivage ou la suppression.
Le résultat nomme le hash et l’alias effectivement sélectionnés.
Le rollback historique par UUID conserve Update ; seule la route promote/hash
porte l’exception Create initiale. La suppression historique par UUID résout
le groupe de ce hash, exige If-Match et conserve son refus de cible active sans
remplacement explicite ; aucun alias ne contourne l’état de version.

## Sélection HTTP et admission

Le segment `/invoke/{uuid}@{hash}` sélectionne exactement 64 caractères hexadécimaux minuscules.
Le segment sans suffixe sélectionne la cible promue à l’admission. Un suffixe
vide, multiple, abrégé ou mal formé ne devient jamais un appel sans tag.
L’UUID de fonction sert d’abord aux droits Read ; le sélecteur est ensuite validé
et résolu. Un hash inconnu, archived ou deleted donne un refus constant sans repli.

Le préflight conserve son contrat origine/IP et consulte les événements de la
version demandée, sans invocation. Les appels authentifiés revérifient jeton,
portée, politique, disponibilité et chemin à réception, enfilement et admission.
Une version archivée pendant l’attente est refusée. Un appel déjà admis garde
son snapshot jusqu’à terminaison, promotion ou archivage ultérieurs compris.

Le snapshot compose les ressources, noms et variables/secrets courants du
service/fonction avec le handler/runtime/image/événements de la version choisie.
Le hash demandé et le hash résolu sont persistés séparément. L’alias effectivement
utilisé par l’instance reste corrélé dans l’invocation. Le hash exécuté est exposé
par un en-tête réservé X-Serverless-Code-Hash après admission ; le handler ne peut
pas l’écraser. L’authentification métier et les chemins/query restent intacts.

## Pools, minima et budgets

La génération distingue hash et configuration effective, sans faire d’un alias
UUID équivalent un autre code. Une instance conserve son alias physique réel ;
les nouvelles observations et invocations la référencent effectivement. Une
instance ne sert jamais deux hashes différents. Le moteur conserve CPU, mémoire,
concurrence, file, stockage et maximum d’instances communs à toute la fonction.

Le sweep considère toutes les versions available, pas seulement la cible active.
Les changements de configuration retirent les générations devenues obsolètes ;
promotion seule ne retire pas le pool d’un hash encore disponible. Les minima
concernent uniquement la cible promue. Les autres pools démarrent à la demande.

La demande d’invocation a priorité sur le préchauffage. Avec minimum=maximum=1,
un appel pilote peut faire retirer l’instance stable prête afin de libérer sa
place ; une invocation active n’est jamais interrompue pour cela. Au repos,
le minimum de la cible est rétabli dans les budgets. Le délai d’inactivité est
un plafond de conservation des instances excédentaires ; une pression réelle
de file, de minimum ou de budget peut libérer une instance prête plus tôt.
Les compteurs restent par fonction, toutes versions confondues, à chaque décision.

## Archivage, restauration et suppression

Les routes POST archive/restore et DELETE d’une version exigent Update et
If-Match de la fonction. Leurs décisions modifient le parent et son ETag.
Archiver conserve les fichiers mais interdit immédiatement les admissions.
Restaurer une archive dont les fichiers sont conservés rétablit available par
une action explicite et auditée. Une suppression logique est immédiate, puis
le nettoyage attend les consommateurs avant de retirer les fichiers.

La cible courante est protégée : archive/delete exigent soit un autre hash
available de la même fonction comme remplacement, soit disable_default explicite.
Ces choix sont exclusifs et traités dans la même transaction. Ils ne remettent
jamais first_promoted_at à NULL. Les appels déjà admis terminent normalement.

Les triggers de rétention d’alias restent en place. Une version deleted cesse
d’être invocable par son état autoritaire ; ses alias ne sont marqués supprimés
et nettoyés que lorsque leurs consommateurs permettent cette transition. Les
historiques et hashes restent présents après l’effacement. Les octets et les
responsabilités physiques ne sont acquittés qu’après suppression confirmée.
Une réimportation précise restore_code_hash ; le hash recalculé doit correspondre.
Elle attend la fin du nettoyage d’une suppression encore en cours, puis conserve
un nouvel alias physique du même tag, sans changer sa date de création initiale.
Le résultat distingue version_restored de code_changed ; restaurer une identité
connue ne la présente pas comme une nouvelle version.

## Catalogue, CLI, console et manuel

Le catalogue de SLS-066 accepte un paramètre version optionnel, contrôlé par la
même résolution. Il calcule les chemins de ce hash sur les domaines officiels du
SPARK. Le résultat distingue sélection, hash sélectionné et cible par défaut.
Une consultation versionnée peut fournir les URL du premier upload non promu.
Sans paramètre, la réponse conserve les URL sans suffixe de la cible courante.

La CLI propose publication pilote de code/descripteur seul et promotion explicite.
`deploy --code-only` exige les fonctions déjà créées et ne résout pas les valeurs
provider/variables/secrets inutilisées ; il publie les handlers et événements du
manifeste sans changer leur configuration. `promote --function UUID --code-hash HASH`
relit la fonction puis exige son If-Match, sans manifeste ni promotion automatique.
La CLI compare le hash retourné au calcul canonique de son inventaire empaqueté,
du descripteur demandé et de l’image réellement validée par le contrôle.
Le déploiement complet garde ses mutations de configuration rapportées séparément.
Le résultat indique code_changed, hash préparé et cible observée, sans présenter
publié comme promu. Le catalogue après upload est demandé pour le hash retenu ;
une panne facultative de ce catalogue ne rejoue pas la publication réussie.

La console groupe et pagine côté serveur cinq versions par hash. La carte
disponible mène aux adresses avec `?version=HASH`. Le retour à la cible par défaut
est un geste explicite ; une redirection canonique conserve aussi une sélection
invalide sous une forme refusée, sans l’effacer au profit du défaut. Un retrait
de cible recueille remplacement ou désactivation dans un dialog puis confirme.
La restauration d’une archive conservée est directe et auditée ; la réimportation
recueille un vrai ZIP lié au hash et à son descripteur conservé.
Le suivi lit le candidat avant le catalogue de versions, puis confirme l’ETag
de fonction après ce catalogue. Un candidat terminal published ne peut ainsi
arrêter son polling sur un catalogue lu avant sa publication : le code seul ne
change pas l’ETag du parent. Les refus de préparation restent dans le formulaire ;
après prise en charge de l’envoi, son suivi porte les refus d’upload et le hash
de réimportation demandé, sans renvoi automatique du ZIP.

La facette de code présente des versions par hash, cible par défaut, état et dates.
Elle permet publication puis promotion séparées, archive/restore/delete et
réimportation explicite ; les confirmations nomment fonction et hash. Les UUID
restent des références techniques complémentaires. Les états de copie/lecture,
focus, mobile et refus suivent le design existant. Le manuel canonique est
modifié avec les comportements effectivement construits et déployés.

## Preuves réelles

Conserver les critères de FUNCTION_VERSIONS et ajouter les cas discriminants :

- premier upload A avec Create, appel sans tag refusé, appel A par hash réussi ;
  B publié par Update avant promotion : Create ne peut promouvoir B ; promotion
  A par Create puis désactivation : Create ne retrouve jamais un droit initial ;
- A stable/B pilote avec handlers et événements différents, appels simultanés,
  promotion/rollback pendant une invocation déjà admise et sans redémarrage de A
  sur réupload identique ; recompression et renommage sans nouvelle version ;
- doublon disponible au plafond, nouveau hash refusé, convergence réelle et
  responsabilité du paquet réutilisé sous EACCES/SIGKILL avec reprise des octets ;
- validation dont le conteneur ne peut être retiré avec un second upload déjà
  admis : aucun autre validateur ne démarre avant réconciliation confirmée ;
- Read/CRUD, portées, révocation, origine/IP, préflight, hash mal formé/inconnu/
  archivé/supprimé : aucun code de repli ni fuite avant autorisation ;
- état archivé pendant attente, suppression pendant appel vivant, fin et nettoyage,
  restauration explicite et réimportation du même hash après effacement ;
- maximum commun saturé par plusieurs hashes, minimum=maximum=1, file et budgets
  globaux, partage des volumes/caches attachés au même UUID de fonction ;
- migration007→008 depuis de vraies publications/promotions historiques, alias,
  pointeur, données et audit conservés ; reprise des purges encore corrélées ;
- CLI, URL et UI depuis l’accueil, code seul préservant les configurations,
  confirmations, presse-papiers, manuel, mobile et captures réellement inspectées.

Les scénarios sont séquentiels et utilisent les vrais composants. Les attentes
historiques qui supposent l’activation à l’upload ou vingt doublons sont adaptées
au nouveau comportement ; les bancs des anciennes images restent historiques.
Aucun succès conditionnel, mock, stub ou réponse remplacée.
