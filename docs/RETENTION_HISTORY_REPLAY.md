# Replay des témoins de rétention à sept jours

Contrat de [SLS-078.5](BACKLOG.md#sls-078), partagé avec[SLS-091.1](BACKLOG.md#sls-091).
Décision du11 novembre2026 avant code. Complète[SCHEDULE_RETENTION](SCHEDULE_RETENTION.md).
La borne numérique est qualifiée séparément sur348sources. Ce parcours d'âge
garde ses preuves propres : ses préflights et pertes doivent être exécutés avant
les épreuves à sept jours ; aucun résultat numérique ne les remplace.

## Sources exactes et exclusivité

Seules les deux captures authentiques publiées sont admises :

- source non close : `schedule-retention-9a2a4cd1eb134c20b4e1c5a1a1bdc7c0`,
  preuve `schedule-retention-capture-dev-2026-11-11.json` ;
- terminale : `schedule-terminal-history-a3993b7d64f14650933cf03960c3d3b0`,
  preuve `schedule-terminal-history-capture-dev-2026-11-11.json`.

Vérifier les reçus privés contre leur preuve publique canonique, les deux SHA
SQLite, l'intégrité immutable/RO, l'absence de sidecars, l'inventaire complet des
artefacts (SHA/taille/mode) et les deux exports d'images existants. Racines root0700,
SQLite root0400, chemins canoniques sans lien. Les fichiers capture.json/artifacts.json
de la première capture sont root0600, selon le relevé natif du11novembre12:37UTC ;
seuls ces deux fichiers connus sont admis dans ce format, à l’intérieur de la racine privée
root0700, avec égalité exacte aux empreintes/reçus canoniques. Ceux de la seconde
capture, preservation.json et les exports restent root0400. Vérifier les métadonnées
réelles avant usage, sans durcir ni réécrire les captures. Aucun export ni copie source
réécrit. Pour la première capture, le reçu `retention-captured` est dans les événements
du rapport public ; `completed_after_resume` décrit la reprise, jamais la sauvegarde.
Le reçu séparé de préservation porte ses images. Pour la seconde, `receipt` porte
les témoins et images. Ne pas réutiliser le schéma de reçu du volume des tirs.

Mesurer de nouveau les faits de l'inspection canonique : installation-id, namespaces
actifs par UUID/nom, fonctions vivantes, instances, générations actives, compteurs,
absence d'appel actif, opération, réservation, bail, volume, probe et intention.
La première source autorise seulement sa fonction vivante connue et lelabs vide ;
l'autre n'autorise aucune fonction vivante. Les lignes historiques restent intactes.

Ces captures ont le même installation-id que les originaux. Le loader de volume
continue de refuser cette égalité. Un parcours explicite de replay de rétention
utilise la fenêtre exclusive existante : originaux arrêtés/conservés par identité,
zéro conteneur/réseau/bail/volume original, y compris les conteneurs arrêtés
recherchés par installation-id et les réseaux étiquetés, répertoires neufs par rôle, agent sur
le seul registre copié. La référence reste en fonctionnement. Même port HTTPS18090,
aucune écriture de fichier officiel/proposition, aucune opération sur FORGE.

## Parcours gardé distinct

Réutiliser `instance-limit` uniquement comme fenêtre de répertoires et services,
avec les options distinctes `--retention-history=ID` et
`--retention-observation=preflight|age|seed-loss|observer-loss`, garde120 obligatoire.
Elles sont exclusives des options firing-history/firing-observation et des autres
modes/durées. Le contrôle temporaire s'appelle `serverless-api-retention-replay`,
projet et unité de restauration nommés pour ce replay. Les chemins et le journal
conservent leur format de fenêtre ; aucun changement aux parcours sans ces options.

Avant toute garde/arrêt, vérifier entièrement la source, les images présentes et
les préconditions d'horloge. `age` refuse avant l'éligibilité réelle ; `preflight`
refuse si un témoin d'âge ciblé est déjà éligible. Les modes de perte sont des
preuves de restitution, jamais des preuves de rétention. Les images capturées
peuvent différer de l'image habituelle : les deux identités sont explicites et
contrôlées ; les originaux redémarrent sur leur image d'origine. Le schéma source
009 reste associé à son image capturée ; aucune migration de la source n'est faite
par le test. Une incompatibilité réelle de clé/configuration fait échouer le replay.

Armer dans la première partie d'une fenêtre réelle UTC, de D+10 à D+60s ; relever
l'activation effective du timer et figer D. Après arrêt/contrôle du repos, conserver
les originaux, copier les artefacts et le registre, puis publier CONTROL atomiquement
en dernier. Refaire les empreintes et propriétaires. Le contrôle ne démarre qu'après
publication complète, avec l'image immuable capturée et les vraies dépendances.
L'ancienne instance ready de la première source disparaît par `Execution.recover()` ;
le pilote ne la retire pas par SQL. Aucune ligne ni date métier n'est fabriquée.

L'autorisation d'identité clonée est limitée au journal de ce parcours : source
canonique vérifiée, installation capturée exacte, original arrêté, répertoires
originaux conservés par identité et remplaçants reconnus. Les points de démarrage,
retour d'identité, nettoyage des consommateurs et restitution doivent tous l'appliquer.
Aucun assouplissement général de l'assertion installation!=original. La garde figée
conserve ce contrôle. Avant tout retrait Docker, namespace/fonction/révision/image,
labels et montage /code doivent correspondre exactement aux données temporaires.
Lelabs reste vide. Toute ressource inconnue interdit le retrait/restitution aveugle.

## Observation du premier passage réel

Le lecteur `retention-history-replay.py` démarre Compose et attache l'observateur
natif au Python unique (PID/naissance/cgroup) avant d'attendre la santé. Il ne
remplace ni tampons, registres, SQL, résultats système, horloge ou ordonnanceur.
Observation25s, alarme35s, commande40s avec verrou hérité et jonction imposée.
Les lectures SQLite se déclenchent aux frontières fdatasync des descripteurs
réels du contrôle SQLite et de ses sidecars, reconnus par /proc en lecture
seule à l’entrée du syscall. Les fermetures et verrouillages de lecture ne
déclenchent pas de requêtes sur les témoins : le démarrage de la vraie capture
contient beaucoup de consultations historiques. Les états doivent toujours
être observés commis ; toute frontière manquée reste un échec. Le reçu conserve le nombre
de stops et de frontières SQLite, ainsi que le diagnostic d’échec si la
frontière n’est pas acquise ; aucun délai n’est élargi pour masquer un échec.
Préparer le reçu durable avant reprise ; détacher dans finally. Si une frontière
est manquée, conserver l'échec sans relance automatique.

Source non close après éligibilité commune18 novembre03:30:26.355818UTC :

1. État sauvegardé acquis avant reprise : HTTP et source terminaux présents aux
   dates originales, tir dispatched et completed_at NULL.
2. Après maintenance d'exécution : HTTP ancien absent, source exactement conservée,
   tir encore non clos. Ce retrait est le témoin réel du passage de rétention.
3. Clôture normale du même tir avec une nouvelle date réelle, puis source ancienne
   absente. Le tir maintenant jeune demeure présent. Aucun nouvel appel/handler.

Pour preflight jeune, les deux invocations demeurent strictement identiques après
clôture normale du tir ; zéro preuve d'âge déduite. Dans les deux modes, recover
retire réellement la ligne ready et ne réécrit pas les invocations réussies.

Source terminale après éligibilité commune18 novembre04:05:13.358459UTC : observer
les témoins originaux, puis la disparition commise du tir terminal et des deux
générations retirées99/100, dont99 sans tir. Leurs DELETE appartiennent à la même
transaction : ne pas exiger un état intermédiaire artificiel. L'invocation source
ancienne est aussi éligible. Preflight jeune conserve strictement ces témoins.

La première source conserve une génération active et un curseur ancien : après
sept jours, la reprise normale peut consigner environ2016 fenêtres manquées par
lots20, sans exécuter les handlers. Le test ne force ni ce curseur ni sa fin de
récupération pour prouver les premiers passages d'âge. Aucun arrêt sélectif de tâche.
Le nominal termine ses lectures et demande la restitution avant D+110s. Pour une
perte, la garde se déclenche à armed_at+120s, donc au plus D+180s ; exiger retrait
réel du contrôle temporaire avant D+240s et restitution/jonction avant D+270s.
Le reçu durable relève control_removed_at après suppression Docker lorsqu’un
contrôle a été créé, et control_absent_at après vérification effective de son
absence dans tous les cas. Une perte avant CONTROL ne prétend pas supprimer un
conteneur jamais démarré. Un dépassement
invalide la preuve mais n'abandonne pas la restauration. Aucun nouveau créneau actif
D+300 n'est permis ; un délai insuffisant reste un échec conservé.

## Lecture publique, restitution et preuves propres

Après observation/détachement, attendre la santé puis nouvelle connexion SSO depuis
l'accueil. Pour la source vivante, recouper par API l'état du tir et les témoins
présents/absents ; pour les objets déjà purgés, recouper l'archive et le refus d'accès
comme fonction vivante. Les états natifs exacts restent la preuve des DELETE.
Aucun nouveau déploiement, appel de handler ou purge métier n'est attribué au replay.
Restituer, joindre pilote/garde, recouper les originaux, configuration/proposition,
référence, source scellée et exports ; retirer uniquement les copies temporaires.

Trois groupes par nominal et par source : chargement/observation ; vrai SSO/API ;
restitution/source inchangée. Avant les preuves d'âge : préflight de chaque source,
refus avant mutation (options, source, durée et âge prématuré), puis pertes réelles
après publication du registre/avant CONTROL et après attache native. Pour chaque
perte : pilote/mutateur SIGKILL, point durable réel, garde indépendante120,
consommateurs absents et mêmes originaux restitués, source inchangée. Les gardes
historiques touchées repassent sur le helper final. Une copie de capture non close
ou une donnée inconnue ne devient jamais source de replay.

## Préflights jeunes et refus qualifiés

La [preuve cbdcf4a](evidence/retention-history-replay-preflight-dev-2026-11-11.json)
passe neuf groupes sur351sources : huit refus d'options et deux refus d'âge
regroupés en trois groupes ; chargement, SSO/API et restitution pour chacune
des deux sources en six groupes. Bases/artefacts/images et reçus canoniques
sont vérifiés ; les captures restent strictement inchangées.

Source non close : observation9,859244s,149251 stops et sept frontières fdatasync.
Ces sept points sont des entrées/sorties observées, pas sept syscalls distincts.
L'ancienne instance disparaît par recover, les deux invocations réussies restent
identiques et le même tir se clôt normalement à une nouvelle date réelle ;
aucun nouvel appel. Pour la seconde source sans instance, le premier arrêt
conserve les témoins ; après santé et SSO, tir/générations/archives sont recoupés.
Ce contrôle jeune ne prouve pas un DELETE ni un passage de rétention d'âge.

Deux restitutions nominales jointes, mêmes originaux et référence, fichiers
officiels inchangés ; contrôle natif final à13:00:40UTC, deux conteneurs sains,
agent actif, healthz200,5982 artefacts et tous actifs à zéro. Les
[quatre essais échoués](evidence/retention-history-replay-failed-dev-2026-11-11.json)
restent séparés : mauvais propriétaire attendu, reçu canonique absent du SPARK,
puis deux expirations de l'observateur. Aucun de leurs groupes n'est compté.

Pertes copie/observateur, refus du namespace étranger dans le nouveau contexte
cloné et régressions historiques restent requis. L'âge réel et la campagne
complète restent ouverts ; les preuves antérieures gardent leurs époques distinctes.
