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

## Refus du périmètre cloné

Le mode client `foreign-namespace` reprend la source vivante en mode helper
`preflight`, avec garde120 et mêmes limites UTC. Il reçoit les identifiants
SSO par stdin privée. Quatre groupes : chargement/observation ; SSO/API ;
namespace hors périmètre préservé au refus ; restitution explicite après retrait
de la seule fixture. Aucune nouvelle option du helper ni relaxation de portée.

Après le SSO, lire la liste initiale des namespaces et la recouper avec les
UUID canoniques. Avant POST, conserver ce témoin et le nom composé avec l'UUID
complet de campagne. Créer par API un namespace vide ; retrouver ensuite sa
seule correspondance exacte par API, exiger un UUID absent du témoin initial,
confirmer nom/UUID et absence de services. Ce même chemin de réconciliation
est utilisé en nominal et en secours si la réponse POST est indéterminée ;
une liste tronquée, plusieurs correspondances ou un objet ambigu interdisent
DELETE. La réponse POST n'est pas l'unique source d'autorité pour le nettoyage. Demander restore via le helper normal : celui-ci termine
le pilote, puis doit refuser avec foreign_namespace avant retrait du contrôle
temporaire. Vérifier le pilote terminé, restored=false, le même conteneur
temporaire encore en marche, l'original arrêté et l'objet visible par API.
Supprimer ce seul namespace par API, vérifier son absence, puis demander une
restitution explicite avant D+110. Son independent=true décrit l'appel hors du
pilote ; ce cas n'est pas une nouvelle preuve d'expiration du timer.

Conserver les diagnostics du refus, les identités natives et les dates. Après
restitution, vérifier sources/captures/images/configuration et originaux, pilotes
et garde terminés, copies retirées. En cas d'erreur, tenter le retrait API de
la seule fixture créée avant le secours ; un objet inconnu reste une interdiction
de restitution, jamais un prétexte à effacer des données. La fonctionnalité est
qualifiée par quatre groupes réels, liés dans le résultat de périmètre ci-dessous.

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

La [preuve des replays](evidence/retention-history-replay-preflight-dev-2026-11-11.json)
passe treize groupes sur351sources identiques : neuf au client cbdcf4a pour huit refus
d'options et deux refus d'âge
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

Les deux pertes sur la source vivante passent quatre groupes supplémentaires
au client3125ad1 : après publication du registre/avant CONTROL, puis après attache
native au Python. SIGKILL des pilotes/mutateurs, canaux SSH255 sans attribution
d'un code natif137, gardes120 indépendantes et mêmes originaux/captures restitués.
Les [journaux natifs](evidence/retention-history-loss-timings-dev-2026-11-11.json)
recoupent les bornes : seed arméD+48,348, contrôle absentD+168,804, restitution
D+178,383 ; observateur arméD+11,357, retraitD+132,296, absenceD+132,475 et
restitutionD+145,018. Le seed ne prétend aucun retrait de contrôle jamais créé.
Ces inspections ajoutent zéro groupe aux treize. Le contrôle final13:12:18UTC
conserve deux services sains, référence inchangée,5982 artefacts et tous actifs0.

Le refus du namespace supplémentaire est qualifié séparément ci-dessous ;
les régressions communes sont qualifiées séparément ci-dessous. L'âge réel et la campagne
complète restent ouverts ; les preuves antérieures gardent leurs époques distinctes.

## Périmètre cloné qualifié

La [preuve9f3e7da](evidence/retention-history-namespace-scope-dev-2026-11-11.json)
passe quatre groupes, dont deux préflights rejoués et deux de périmètre. Les
351sources sont identiques avant/après ; seuls les deux clients changent par
rapport à l'époque des treize groupes, helper/image inchangés. Le vrai SSO
et la recherche API retrouvent la fixture de nom UUID complet, absente des
UUID canoniques et sans service. Restore refuse foreign_namespace/code1,
l'objet reste visible, le même temporaire en marche et l'original arrêté.

Après retrait API de cette seule fixture et GET404, restore explicite réussit
et toutes les gardes/pilotes sont joints. D=13:30UTC : créationD+57,205,
retrait du contrôleD+61,282, absenceD+61,492 et restitutionD+74,183 ; garde
arméeD+11,120 pour120s. Ce succès précède son expiration. Sources/captures/
originaux/configuration conservés, contrôle natif final13:31:07UTC,2healthy,
actifs0,5982 artefacts et aucune garde. HTTP perdu, sept jours et campagne
complète restent non qualifiés ; les régressions communes sont qualifiées ci-dessous.

## Régressions finales des fenêtres de restitution

La [preuve au commit f908640](evidence/retention-history-guard-regressions-dev-2026-11-11.json)
passe 25 groupes sur 351 sources identiques avant/après : onze fenêtres/partiel,
trois options/défaut 900, cinq options 2700 et six consommateur vivant/pause/
namespace. Onze campagnes distinctes, images conservées. Les confirmations
SIGTERM (15) et SIGKILL (9) ont pidfd lisible puis pilote absent de /proc, mesurées
10, 765 ms et 28, 345 ms ; gardes de 120 s et restitutions attendues jointes. Les
options 900/2700 s sont programmées puis restituées, pas laissées expirer.

Les trois essais antérieurs sont exclus ; le ciblé SIGKILL de deux groupes n'est pas ajouté
au même cas de cette matrice. Le contrôle final garde le même conteneur 68a8 et image c59,
redémarrage à 14:26:18 UTC, référence inchangée, deux services sains, actifs à zéro, 5 982 artefacts
et aucune garde. Cette preuve qualifie les fenêtres communes ; pannes
propres de capture et d'observateur source, âge et campagne complète restent
ouverts dans 078.5. Les preuves antérieures conservent leurs époques distinctes.
