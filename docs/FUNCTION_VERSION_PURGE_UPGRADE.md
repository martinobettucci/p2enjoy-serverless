# Reprendre une purge engagée pendant le premier upgrade du registre

Complément de [SLS-074](BACKLOG.md#sls-074), implémenté et vérifié par 31 groupes
ciblés réels. Le registre et son upgrade 006 → 007 au repos sont éprouvés ; la
correction accepte aussi les états intermédiaires 006 valides décrits ici.
La régression commune 313 groupes et le replay 003→007 de 5 groupes passent
sur l’image finale fe75c9e7. La [preuve du registre](evidence/function-version-registry-dev-2026-11-09.json)
conserve les deux constructions, les époques de clients et leurs diagnostics.

## Constat et décision

La décision durable de purge efface inventaire et événements avant l’effacement
physique. Une interruption laisse donc légitimement `inventory_json=[]`,
`events_json={}`, une révision supprimée et des octets encore comptabilisés.
Le backfill de la première image 007 refusait cette ligne avant la reprise du résolveur.
Ce n’est pas un inventaire de code invocable à reconstruire : sa fonction est
déjà supprimée et sa purge décidée. Une installation déjà migrée garde son hash
et ne réexécute pas 007 ; le défaut concerne le premier passage depuis 006.

Décision : reconnaître uniquement cette purge durable et corrélée, conserver
une identité inconnue `NULL`, puis laisser le résolveur normal terminer. Ne pas
fabriquer un hash depuis des fichiers dont le descripteur a été effacé, ni
accepter toute révision vide encore comptabilisée. Le pointeur courant, les
autres révisions et les compteurs ne sont pas réécrits par cette reconnaissance.

La corrélation exige la même fonction supprimée et sans pointeur actif, le même
service, le même UUID d’opération entre commande et garde, le type purge, une
décision `commit`, une commande `pending` dans `volumes` ou `artifacts`, le même
propriétaire d’installation, la version résultante égale à celle de la fonction
et les versions attendues de commande/garde concordantes. L’inventaire et les
événements doivent être ceux réellement effacés par la purge. Une corrélation
absente ou contradictoire conserve le refus transactionnel.

La correction porte sur le calcul de la première transition 007, sans nouveau
format SQLite. Une migration suivante seule ne pourrait pas réparer un refus
qui survient avant elle. Les installations déjà marquées 007 la sautent et
conservent leurs identités immuables. Les preuves distingueront les deux images
et les époques de sources ; la première campagne ne devient pas rétroactivement
une preuve de cette correction.

## Banc historique réel et borné

Réutiliser la fenêtre gardée de `storage-legacy-environment.py`, avec l’image
006 construite depuis le véritable arbre Git
`f56d79ebe3d1d84731bfd262d1e6a9d5b5a680c0`, les fichiers officiels de cellule
et le SSO normal. Ses sources produit sont comparées au checkpoint conservé
avant le registre, ses six migrations et ses fichiers embarqués sont vérifiés.
Le tag dédié `p2enjoy-control:historical-schema-006` et une attestation root
protégée conservent cette référence, sans modifier le tag du contrôle en service.
Vérifier l’image et l’attestation avant d’arrêter un service ou déplacer un original.
Les originaux, leurs tables et artefacts, la configuration et l’exécuteur de
référence sont restaurés par la garde existante, sans administration de FORGE.
Les modes historiques actuels gardent leur attente de santé verte.

Le nouveau parcours crée ses fonctions et leur code original par les API.
Une vraie publication Node/Docker précède suppression et purge publiques.
`deny-artifact` retient le seul dossier corrélé avec EACCES. Observer les
compteurs, l’inventaire effacé, la garde et le reçu plutôt que simuler ces états.

Pour la phase `artifacts`, attendre la fin de l’agent et le reçu de contrôle
encore pending. Pour `volumes`, synchroniser le sweep réel par un vidage de cache
terminé, puis supprimer la fonction et engager sa purge. La responsabilité du
POST engage réellement l’agent et peut recevoir son état pending avant la fin du
worker. Arrêter le contrôle alors que son reçu est encore en `volumes`, puis
vérifier ce même état après arrêt. L’agent continue et termine indépendamment ;
attendre son reçu terminé, l’absence de volumes/baux/pending et de montages avant
la migration et le contrôle des références. Le nouveau contrôle reprend ainsi
la décision déjà terminée côté agent, encore en `volumes` côté contrôle. Les
volumes de cette fixture sont désactivés et aucune instance ne la consomme.
Si la fenêtre attendue
n’existe pas, le scénario échoue ; aucun passage n’est déclaré ou ignoré
conditionnellement. La phase n’est jamais changée par SQL pour fabriquer le cas.

Une attente « API lisible » explicite vérifie image/ID/vie du seul conteneur
temporaire et le vrai GET anonyme `/api/session` avec Host canonique. Elle ne
confond pas santé 503 due à la purge retenue et échec de migration. Un refus
attendu vérifie sortie non nulle de l’application, schéma exact 006, absence de
colonne/marqueur 007, intégrité et mêmes anciennes lignes après son arrêt.

La reprise de l’image 006 sur la même base n’est permise qu’après ce rollback
constaté. Elle est interdite dès que 007 est commise. Le relâchement d’artefact
ouvre le dossier NOFOLLOW, vérifie device/inode, restaure son mode par fchmod
pendant qu’il appartient encore à root, puis fchown en dernier. Sa disparition
immédiate est normale ; le reçu public et les octets à zéro confirment la fin.

<a id="preuves-à-terminer"></a>
## Contrat de preuve

1. Référence actuelle : vraie purge 006 retenue, refus de 007, rollback complet,
   reprise de 006 sans restauration de base, relâchement et fin normale.
2. Correction : mêmes parcours pour les phases d’entrée volumes et artifacts,
   007 appliquée pendant EACCES, commande/garde conservées, aucun hash inventé,
   compteurs maintenus ; relâchement, reçu terminé et persistance après restart.
3. Copies privées des vrais états intermédiaires : erreurs réelles de
   corrélation et vrai démarrage refusé, transaction annulée. Aucun remplacement
   de serveur, dépendance ou réponse. Sauvegardes privées jamais publiées.
4. Restauration et perte du pilote : originaux et configuration identiques,
   agent et contrôle sains, volumes/baux/instances temporaires absents ; la
   nouvelle fenêtre reste compatible avec la garde indépendante.
5. Rejouer les campagnes concernées sur la nouvelle image, y compris le banc
   003 → 007 ; conserver séparément la campagne précédente sur l’ancienne image.

Le mode de fenêtre porte un nom de responsabilité propre, avec namespace
`code-purge-migration-<nonce>`, service/contrôle temporaire identifiés et garde
privée. Les modes historiques conservent leurs conventions et leurs contrôles.
Les copies des vrais états 006 retenus sont sauvegardées par SQLite sous leur
propriétaire, en 0600, hors des répertoires temporaires ensuite retirés. Elles
permettent les fautes de corrélation sans altérer l’installation partagée.

La première tentative n’a démarré aucun contrôle historique : l’ancien digest
de l’image006 n’était plus présent dans Docker. Ses originaux sont entièrement
restaurés et le rapport reste en échec, zéro groupe compté. Reconstituer la vraie
image depuis ses sources figées est un prérequis de build, jamais une doublure.
Les prochaines procédures d’upgrade doivent nommer et conserver l’image de
retour avant bascule ; la simple mémorisation d’un digest ne garantit pas sa présence.

Si 007 est annulée, conserver la base 006 et reprendre l’ancienne image : une
restauration de sauvegarde risquerait de revenir avant la purge déjà décidée.
Si 007 est commise, le downgrade exige le plan cohérent base/fichiers/volumes
et ancienne image ; une ancienne image seule ne constitue pas un retour arrière.

## Résultats ciblés

L’image corrigée `78eb24d7c082b76f0f9081b24a4c3f2fcffd4b486e84248f37948c6274c57781`
passe les deux fenêtres de quatre groupes, en artifacts et volumes, puis trois
groupes avec perte du pilote et restauration indépendante. Les 36 864 octets
du code restent comptabilisés, son identité inconnue reste NULL et sa garde
subsiste pendant EACCES ; le relâchement termine la purge et le restart conserve
le reçu. Les originaux, données, artefacts, configuration et référence sont
identiques après chaque restauration ; timers et services de garde sont inactifs.

Vingt copies du véritable backup artifacts éprouvent chaque corrélation rompue,
dont UUID d’opération, trois services et versions. Le second service est créé
par la vraie API avant la fixture. Chaque application refuse au démarrage et
annule intégralement sa migration. La sauvegarde originale reste inchangée.
Le cas « pointeur actif » comprend aussi une révision non supprimée pour
respecter le vrai trigger SQLite ; il prouve le refus de cet état combiné,
sans prétendre isoler la seule clause SQL du pointeur.

Les seize premiers contre-exemples constituent une époque de client distincte,
conservée avant le complément à vingt, sans les additionner au total courant.
Le diagnostic antérieur de quatre groupes reste sur l’image précédente et ne
qualifie pas rétroactivement la correction. Le checkpoint au repos conserve
également ses 328 groupes et sa propre époque de sources.


Les 31 groupes ciblés sont rejoués sur l’image finale fe75c9e7. Une reconstruction
après commentaire de traçabilité a changé l’identifiant d’image ; ses 34 fichiers
applicatifs et leurs modes sont identiques au conteneur précédent. L’ancienne
image n’était plus disponible dans l’inventaire Docker. La nouvelle est
conservée sous p2enjoy-control:purge-recovery-reference avant sa recréation
explicite par Compose ; les 1494 UUID/hashes existants sont inchangés. Un up qui
avait gardé l’ancien conteneur a été détecté par le contrôle d’identité.


## Reprise ultérieure vers008

Ce document conserve la qualification006→007. Le complément
[FUNCTION_VERSION_PURGE_MIGRATION_008](FUNCTION_VERSION_PURGE_MIGRATION_008.md)
éprouve ensuite22 groupes sur def45648 : sources006/007 et phasesvolumes/artifacts,
restitution indépendante et refus avant interruption. Il distingue identitéNULL
et hash connu conservé dans le registre deleted. Les anciens31 groupes ciblés
ne sont pas réadditionnés au total22. Les [refus sur copies007](evidence/function-version-purge-correlation008-dev-2026-11-09.json)
passent depuis42 groupes distincts, sans les ajouter à l’ancien total31.


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
