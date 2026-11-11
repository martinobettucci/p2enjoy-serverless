# Borne globale des tirs planifiés

Contrat de preuve de [SLS-078.5](BACKLOG.md#sls-078), selon
[SCHEDULE_RETENTION](SCHEDULE_RETENTION.md#autres-preuves-requises).
Décision du11 novembre2026 avant code. DEV uniquement, campagnes en série,
horloge réelle, aucune date ni ligne métier fabriquée.

## Préparation authentique et conservation

Préparer une sauvegarde d'installation réellement active, puis laisser passer
les fenêtres nécessaires avant son replay. La reprise normale de l'ordonnanceur
consigne les fenêtres manquées en skipped_downtime sans exécuter leurs handlers.
Ces tirs terminaux participent à la même borne10000 que les succès et refus.
Cette voie éprouve la rétention des tirs ; elle ne prétend pas10000 exécutions.

Réutiliser sans changement le mode instance-limit de storage-legacy-environment.py,
garde900s, image immuable du contrôle servi et installation neuve. Les originaux
restent conservés, leur contrôle arrêté, configuration officielle inchangée.
Ce choix évite un arrêt de plusieurs heures de la console habituelle et toute
modification de FORGE. Aucun second contrôle ne consomme le registre original.

Le client `e2e/schedule-firing-volume-capture.mjs` reçoit les identifiants sur
stdin privée et passe par l'accueil SSO, les API publiques HTTPS, la publication
et la promotion réelles. Namespace exact instance-limit-<UUID court>, service
scheduled-firing-history-limit, fonctions firing-retention-01 à16. Chacune porte
16 déclarations activées */5 * * * *, timezone UTC. Les indices distincts des
déclarations sont conservés ; aucune déclaration supplémentaire hors contrat.
Configuration CPU0,05/mémoire128Mio/min0/max1/concurrence1/idle0/deadline60s,
stockage partagé, données/cache désactivés. Réutiliser le handler original
scheduled-capacity.handler, sans nouveau code métier.

Publier tous les pilotes sans les promouvoir, choisir une frontière W avec
au moins90s de marge, puis promouvoir les16 avant W. Une installation neuve
ne doit contenir aucun tir antérieur. À W :256 tirs, dont deux vrais handlers
réussis et254 refused_capacity/schedule_capacity sans invocation ; aucun autre
état accepté. Les refus viennent du plafond2 et des maxima individuels1, pendant
le dispatch synchrone de cette fenêtre. Recouper indices0..15, génération active,
hash, créneau, UUID des deux appels et logs du handler ; attendre zéro instance,
conteneur et bail avant copie. Chaque fonction porte16 tirs, sous la borne.

`e2e/schedule-firing-volume-snapshot.py`, exécuté sur le seul SPARK DEV, est un
lecteur/copieur natif borné. Il vérifie le journal de fenêtre, les identités des
répertoires temporaires, le contrôle original arrêté et la santé de la référence.
Il exige les16 fonctions exactes, générations actives,256 tirs terminaux à W,
deux succès réels, aucun consommateur ni opération en cours. Il sauvegarde
SQLite depuis mode=ro, vérifie l'intégrité et les mêmes témoins dans la copie,
copie les artefacts avec inventaires SHA/taille/mode égaux, sauvegarde le registre
sans bail. Les images contrôle/runtime sont recoupées avec les exports privés
déjà conservés par la capture5056167, sans les modifier ni les réexporter.

Un dossier neuf qualification-history/schedule-firing-volume-<UUID> conserve
ces copies : racine root0700, SQLite et reçus root0400, aucun secret publié.
Écrire le reçu terminé en dernier, vérifier de nouveau les services, fichiers
officiels et témoins. Une interruption laisse un dossier incomplet, sans changer
les sources ; elle ne constitue pas une capture réussie. Pas de reprise automatique.
Ce lecteur ne modifie ni donnée active ni service. Il est lancé par la seule
opération capture-firing-history du pilote existant, qui lui transmet son verrou
hérité, comme aux autres commandes bornées. La garde attend donc sa jonction
avant tout renommage de restitution, même si le pilote meurt pendant la copie.
Alarme native30s, commande timeout40s et lecture client bornée ; aucun lecteur
externe ne poursuit sa copie pendant la restitution. Les options de garde ne
changent pas ; les restitutions historiques restent à rejouer après ce raccordement.

Après capture, archiver/purger les16 fonctions par les API, supprimer les parents,
recouper l'absence physique du code, volumes, canaux et consommateurs, puis
restituer les originaux et joindre pilote/gardes. Les copies privées actives
gardent leurs générations non retirées ; la purge réelle ne les réécrit pas.

Quatre groupes distincts : SSO/publications avant W ;256 tirs et deux handlers
authentiques ; sauvegarde native vérifiée/protégée ;16 purges et restitution.
Le rapport conserve les sources/images avant/après, dates et empreintes. Cette
préparation seule ne qualifie ni la borne10000, ni l'âge, ni les pannes du client.

## Premier essai et observation durable

L'[essai27221ea](evidence/schedule-firing-volume-capture-failed-dev-2026-11-11.json)
à06:00UTC a produit deux handlers réussis,172 refus de capacité
et82 tirs failed/execution_unavailable. Les journaux signalent OperationalError
dans les maintenances planification/exécution ; SQLite est intègre et les
fichiers appartiennent au bon propriétaire. L'errno et le site exact ne sont
pas capturés : ne pas attribuer rétrospectivement l'échec à une cause certaine.
Aucune sauvegarde validée ni purge métier n'est retenue. La restitution de
secours conserve registres, artefacts, configuration et référence d'origine.

Le poller capacity ouvrait/fermait des connexions RO successives autour du
dispatch de256 tirs. Appliquer au seul mode instance-limit l'observateur durable
déjà défini par [ADMISSION](ADMISSION.md#observation-durable-des-intentions-par-les-gardes) :
ouvrir après démarrage une connexion CONTROL sous propriétaire, en autocommit,
sans transaction retenue ; réutiliser ses lectures puis la fermer dans finally
avant toute restitution. La garde indépendante n'en dépend pas. Motif : réduire
les courses de fin de connexion pendant l'observation, sans délai SQL modifié,
sans réécriture de registre et sans changer l'admission applicative. Cela reste
un correctif du banc à éprouver, pas une preuve de cause ni une correction SQLite.
Le client doit aussi échouer immédiatement sur un état terminal inattendu en
conservant le relevé, au lieu d'attendre la fin du délai d'observation.

## Éligibilité et replay à qualifier

Relever dans la sauvegarde le curseur réel C=W et le nombre initial T0=256.
Avec256 déclarations actives par fenêtre, calculer
N=floor((10000-T0)/256)+1=39. Le premier redémarrage utile doit avoir sa frontière
réelle D>=C+39*300, soit3h15 après C. Ce délai est mesuré sur l'horloge du SPARK,
jamais remplacé par une date injectée. Les témoins restent âgés de moins de sept
jours pour isoler la borne numérique. Chaque fonction reste sous10000 tirs.

Le futur pilote de replay doit être spécifié et qualifié avant son usage :
fenêtre gardée exclusive, données/registre/artefacts copiés avant démarrage de
l'image capturée, originaux conservés et aucun consommateur original partagé.
Ne pas réutiliser une seconde base avec le registre actif de la plateforme.

La preuve devra observer toutes les lignes d'un lot de récupération terminé
avant sa suppression numérique, puis exactement les10000 plus récentes par
completed_at DESC,id DESC au même curseur. L'ordonnanceur traite au plus20
fenêtres par passage ; un relevé au milieu d'un lot ne suffit pas. Recouper
fenêtres, générations/indices, absence de nouvelles invocations, dates authentiques,
portée globale et absence de rejeu. Le mécanisme d'observation natif et ses pannes
restent à qualifier ; aucun succès n'est déduit de ce plan ou de la capture.
