# Rétention réelle des tirs planifiés

Contrat de preuve de [SLS-078](BACKLOG.md#sls-078), complément de
[SCHEDULES](SCHEDULES.md#réalisation-du-moteur-et-migration-009). DEV uniquement,
preuves sérielles, aucune date ni ligne métier fabriquée, aucune horloge remplacée.

## Capture authentique avant vieillissement

Le mode terminal-capture de schedule-recovery-operator.py reprend les précontrôles,
le traceur natif et la garde indépendante déjà qualifiés. Une seule fonction
vivante, dans scheduled-functions-<UUID court>, porte */5 * * * * ; données/cache
désactivés. Le handler original scheduled-retention attend réellement deux
secondes avant sa réponse, pour rendre son état running observable. Le pilote
attend handler_started/running par lecture RO avant d’attacher le traceur :
le démarrage froid Docker reste exécuté à sa vitesse normale. Un vrai appel HTTP terminé avant le tir fournit le témoin non protégé.
Le traceur ne remplace aucun registre, tampon ou résultat système. Il suspend
le contrôle seulement lorsque les lectures natives confirment le tir exact
dispatched/non clos et son invocation succeeded, handler démarré, completed_at
renseigné. Le hash, les UUID, le créneau et les logs reçus sont recoupés.

Créer à cet instant une sauvegarde SQLite native depuis une connexion mode=ro,
sous l’identité propriétaire, dans un dossier privé de qualification-history.
Vérifier l’intégrité et le même prédicat dans la sauvegarde elle-même, ainsi que
le témoin HTTP terminal antérieur. Garder les dates réelles et calculer le premier
instant éligible à l’épreuve : max(completed_at des deux appels)+604800s+1s.
Détacher et reprendre immédiatement le contrôle, sans le tuer. La garde restitue
aussi sa santé en cas de perte du traceur ; aucune base originale n’est restaurée.
Comparer CID/image/démarrage et empreintes officielles avant/après ; joindre
le pilote et désarmer timer/service avant toute autre commande de preuve.

Après reprise, vérifier la clôture normale du même tir, sans nouvel appel. Copier
les artefacts immuables de cette installation dans le dossier privé avec inventaire
SHA avant/après ; un écart est un échec. Sauvegarder aussi le registre de stockage
au repos, sans bail ni volume de la fonction témoin. Puis archiver/purger réellement
la fixture par API et vérifier son absence physique. La sauvegarde de capture et
les artefacts restent conservés pour le vieillissement ; ils ne sont pas des
objets actifs de la plateforme et ne sont jamais publiés dans Git. Le rapport public
porte seulement identités de campagne, dates, états et empreintes sans secret.

## Épreuve après sept jours

Le replay devra employer une copie privée de la sauvegarde et des artefacts,
sur l’image immuable capturée. Il sera réalisé dans une fenêtre gardée exclusive :
contrôle habituel arrêté, originaux par identité conservés, zéro conteneur/réseau/
bail d’exécution de l’installation originale avant démarrage, agent sur registre
privé. Une simple deuxième base contre le Docker/registre actif est interdite :
l’installation-id cloné ferait viser les consommateurs originaux par recover.
Le pilote de replay et ses pannes seront spécifiés et qualifiés avant cet usage.

Le passage de rétention doit être observé avant la clôture du tir : témoin HTTP
ancien supprimé, source ancienne conservée tant que son tir reste non terminal,
puis clôture normale et source devenue éligible. La clôture attribue au tir une
nouvelle date réelle ; son propre délai de sept jours repart alors. Cette capture
ne prouve donc ni l’âge d’un tir déjà terminal, ni le plafond numérique.

## Autres preuves requises

Les bornes10000 des invocations et des tirs terminaux sont globales, pas par
fonction. Dépasser ces bornes exige de vrais appels et de vraies fenêtres sur
plusieurs fonctions ; chaque fonction doit rester individuellement sous10000
pour distinguer la portée globale. Les sources des tirs non clos restent hors
du comptage éligible des invocations. Les générations retirées et les tirs déjà
terminaux doivent aussi franchir sept jours réels. Leur capture complémentaire
est qualifiée ci-dessous ; aucun résultat d'âge ne découle des seules captures.

SLS-078 reste[~] jusqu’à ces preuves et à sa régression complète.

La [borne numérique HTTP ordinaire](INVOCATION_RETENTION_VOLUME.md#franchissement-réel-qualifié)
est qualifiée par10016 vrais appels/5008 par fonction : exacts10000 survivants,
16 plus anciens retirés, deux purges publiques et restitution des originaux.
Trois groupes sur337sources ; quatorze groupes de garde/options sont qualifiés
séparément. Cela ne qualifie pas les sources de tir non clos sous la borne
numérique ni les sept jours ; la borne des tirs a sa preuve distincte ci-dessous.

La [borne des tirs](SCHEDULE_FIRING_VOLUME.md) a son protocole distinct de
préparation : sauvegarde native de256 déclarations actives, puis39 fenêtres
manquées réellement écoulées avant replay gardé. La
[préparation31b9102](evidence/schedule-firing-volume-capture-dev-2026-11-11.json)
passe quatre groupes sur340sources,256 tirs06:15UTC et16 purges/restitution ;
replay éligible09:30UTC le11 novembre. Les
[vingt groupes du helper](evidence/schedule-firing-volume-guard-regressions-dev-2026-11-11.json)
passent sur les mêmes340sources. La [copie interrompue](evidence/schedule-capture-interruption-dev-2026-11-11.json)
est qualifiée par cinq groupes sur342sources. Le
[replay numérique](evidence/schedule-firing-retention-count-dev-2026-11-11.json) passe trois groupes
sur342sources :10240→10000 tirs,240 plus anciens retirés au même curseur09:30UTC,
640 tirs initiaux par fonction,112 pages API et restitution jointe. Cette borne
globale est qualifiée ; source protégée sous borne qualifiée séparément ci-dessous, sept jours encore ouverts.
Aucune date métier n'est modifiée.


## Premier essai et frontière d’attachement

Le premier essai894df09 atteint le tir03:20UTC mais échoue avant le handler :
invocation failed/runtime_unavailable, handler_started=0, puis expiration du
traceur45s. Il avait attaché le traceur avant le démarrage froid. Les originaux
et gardes sont rétablis et la fixture est purgée ; aucune capture ni preuve
de vieillissement n’est retenue. Le diagnostic ne reconstitue pas l’exception
interne exacte du runtime. La correction borne l’observation à la fin du handler :
attendre son démarrage réel sans traceur, puis observer sa réponse et son commit.
Le délai de garde et le délai d’observation ne sont pas augmentés.


## Capture qualifiée le11 novembre2026

La [preuve5056167](evidence/schedule-retention-capture-dev-2026-11-11.json) passe
quatre groupes sur331sources figées et imagec59b8616 : SSO et vrai HTTP témoin,
capture RO du succès non encore clos, reprise du même contrôle sans redémarrage,
purge publique et absence physique. Le tir03:30UTC, son invocation et les logs
recoupent le même hash/UUID/créneau.5990 fichiers d’artefacts sont copiés et
vérifiés ; le registre privé est sauvegardé au repos. Les timers/services sont
inactifs et le pilote est terminé. L’essai894df09 reste échoué et hors total.

Capture privée schedule-retention-9a2a4cd1eb134c20b4e1c5a1a1bdc7c0. Le premier
instant éligible est le18 novembre2026 à03:30:26.355818UTC. Le vieillissement
reste réel et incomplet ; aucune rétention ni borne10000 n’est déclarée prouvée.

Conserver aussi les deux images contrôle/runtime par export Docker natif dans
ce dossier privé, avec leurs SHA et identités d’image. Cela protège le replay
d’un remplacement futur des tags. Passer les deux sauvegardes SQLite en lecture
seule et placer le dossier sous propriétaire root0700, sans modifier aucun
octet ni mode des artefacts copiés. Un reçu privé recoupe les empreintes de
capture, registre et inventaire avant/après. Cette conservation ne démarre
aucun conteneur et n’administre pas FORGE.

Restent : interruptions pendant backup/copie de la capture initiale et
régressions de son helper distinct schedule-recovery-operator.py, vieillissement des tirs terminaux/générations retirées,
protection après passage réel de rétention à sept jours et campagne complète.
La source protégée sous borne10000 a sa preuve distincte ci-dessous.
Concurrence078.4 et adaptateur078.7 ont leurs preuves distinctes du11 novembre.


### Conservation native vérifiée

Les deux images ont été exportées en série par docker image save dans le
dossier privé de capture : contrôle59558400 octets, runtime81080320 octets,
SHA des archives dans la preuve liée. Les5990 artefacts et les deux SQLite
restent aux empreintes acquises ; dossier root0700, sauvegardes SQLite0400.
Les deux services sont healthy avec mêmes CID/images/démarrages avant/après
ces exports. Le reçu preservation.json reste privé ; sa copie sans secret
figure sous native_preservation dans la preuve publique. Aucun groupe
fonctionnel supplémentaire n’est compté pour cette conservation.

Pour le replay, lire capture.json et preservation.json dans le dossier privé ;
vérifier SHA des SQLite, inventaire et archives avant toute copie. Les exports
control-image.tar et runtime-image.tar conservent les images immuables malgré
le remplacement ultérieur de leurs tags. Les originaux de capture restent en
lecture seule ; tout replay utilise un autre dossier et son propre journal.

## Capture des tirs terminaux et générations retirées

Décision du11 novembre2026, avant code. Réutiliser les objets authentiques de
la preuve CLI91d4606 : un tir succeeded à04:05UTC et deux générations retirées
par les purges publiques, dont une déclaration désactivée sans aucun tir.
Leurs dates et UUID sont déjà recoupés dans la preuve ; ne créer aucune ligne
et ne modifier aucune date. L'opérateur `e2e/schedule-terminal-history-capture.py`
reçoit le chemin de cette preuve publique puis travaille sur le seul SPARK DEV.

- Précontrôle SQL RO sous propriétaire et Docker : aucune fonction vivante,
  invocation active, instance, opération, réservation ou bail ; contrôle et
  référence healthy. Vérifier exactement les fonctions purgées, générations,
  tir et invocation par rapport au relevé natif de la preuve fournie.
- Sauvegarde SQLite native par connexion mode=ro, intégrité et même prédicat
  dans la copie. Sauvegarde native du registre sans bail, copie exacte des
  artefacts, inventaires SHA/taille/mode avant/après. Fichiers privés uniquement
  sous un nouveau dossier UUID `qualification-history/schedule-terminal-history-*`.
- Réutiliser les exports immuables de la capture source5056167, dont les SHA,
  tailles et images doivent correspondre au contrôle courant et au runtime de
  l'invocation témoin. Ne pas réexporter les images ni modifier ces archives.
- Comparer les identités/démarrages/santés des services, fichiers officiels et
  témoins avant/après. Fermer les copies, passer les SQLite en root0400 et le
  dossier en root0700 ; écrire le reçu terminé en dernier. Une interruption
  laisse seulement un dossier privé incomplet, sans effet sur les originaux.

Ce mode ne suspend ni ne redémarre aucun service et ne rétablit aucune base ;
aucune garde d'administration n'est nécessaire à cette lecture/copie. Son
processus et SSH sont bornés ; aucune relance automatique après un échec.
Le reçu public porte dates, identités et empreintes, jamais bases ou secrets.
Trois groupes : préconditions et identité des vrais témoins ; sauvegardes et
inventaires vérifiés ; fermeture/protection et conservation des originaux.

L'éligibilité est calculée séparément pour le tir (`completed_at +604801`) et
chaque génération (`retired_at +604801`). Le replay gardé, à spécifier et
qualifier avant usage, doit observer la suppression du tir terminal ancien et
des générations retirées, dont celle sans tir, sur la même image capturée.
Cette préparation ne prouve ni les sept jours, ni les bornes10000, ni la reprise
après panne du futur replay. Les données privées sont conservées jusqu'à preuve.

### Témoins terminaux capturés

La [preuve39862b9](evidence/schedule-terminal-history-capture-dev-2026-11-11.json)
passe trois groupes de préparation réels sur335sources, mêmec59b8616. Capture
privée `schedule-terminal-history-a3993b7d64f14650933cf03960c3d3b0` : un tir
terminal succeeded et générations99/100 retirées, dont99 sans tir ; métadonnées
strictement identiques à la campagne CLI. Les deux sauvegardes sont intègres et
root0400,5982 artefacts copiés aux mêmes SHA/taille/mode, exports contrôle/runtime
existants recoupés. Même contrôle/référence, images/démarrages et fichiers
officiels ; aucun arrêt, nouveau handler ou fonction créée pour cette capture.

Éligibilité réelle : tir18 novembre2026 à04:05:09.014643UTC ; générations99 et100
à04:05:11.530622UTC et04:05:13.358459UTC. La borne commune est cette dernière
date. La capture de source non close5056167 garde sa propre borne03:30:26UTC.
Ces trois groupes prouvent la conservation initiale ; l'âge, l'effacement,
les bornes10000, les interruptions propres et les replays restent ouverts.


## Inspection des sources avant le pilote d'âge

L'[inspection native RO](evidence/schedule-retention-source-inspection-dev-2026-11-11.json)
mesure dans les deux SQLite scellées le même installation-id que l'original,
0492c433-a9ed-43b2-bb0a-fa0482185757. La première conserve une fonction vivante,
une ancienne ligne d'instance ready et les namespaces lelabs et scheduled-functions ;
la seconde ne conserve aucune fonction vivante ni instance. Les bases sont
intègres et ouvertes immutable, sans sidecar ; cette inspection compte zéro
groupe fonctionnel et ne qualifie aucun replay.

Les deux registres ont zéro volume, bail, probe ou intention pendante ; les
contrôles ont zéro appel actif, opération ou réservation. Le futur pilote doit
faire reprendre normalement l'ancienne ligne ready, sans créer de consommateur
contre les originaux. Les refus d'identité clonée du helper de volume ne peuvent
être simplement retirés : l'autorisation exige la fenêtre exclusive du contrat,
les répertoires privés reconnus et les consommateurs originaux absents. Un
pilote dédié et ses refus sont qualifiés par les
[treize groupes](evidence/retention-history-replay-preflight-dev-2026-11-11.json),
dont neuf refus/préflights et quatre pour les deux pertes/restaurations indépendantes.
Le [namespace supplémentaire](evidence/retention-history-namespace-scope-dev-2026-11-11.json)
a sa preuve distincte de quatre groupes, dont deux préflights rejoués ; les
régressions communes ont maintenant leur preuve de 25 groupes ci-dessous.

## Source protégée sous borne qualifiée

La [preuve d860cc5](evidence/invocation-source-retention-volume-dev-2026-11-11.json) passe trois groupes
sur348sources identiques avant/après et les mêmes images.10001 réponses HTTP
réelles et un handler cron donnent10002 observations terminales,5001 par fonction.
Le passage de rétention retire exactement le plus ancien HTTP et conserve10001
lignes, source incluse mais hors comptage tant que le tir reste strictement non
clos. Après clôture normale du même tir, le deuxième plus ancien HTTP est retiré :
10000 lignes, source désormais comptée et strictement inchangée. Les trois vecteurs
complets sont recoupés par completed_at DESC,id DESC ; observation12,335898s sous25s.

Deux purges publiques et contrôles physiques d'absence terminent, puis restitution
nominale jointe des originaux. Le vrai worker oneshot quitte0 ; son résultat
systemd success/Code1/Status0 est conservé avant arrêt de l'unité.348sources/images
inchangées, configuration et référence conservées. Le brut complet compressé
contient les vecteurs et reçus ; essais interrompu/échoué exclus. Sept jours,
pannes propres résiduelles et campagne complète restent ouverts :078.5 non clôturée.

## Régressions finales des fenêtres de restitution

La [preuve au commit f908640](evidence/retention-history-guard-regressions-dev-2026-11-11.json)
passe 25 groupes sur 351 sources identiques avant/après : onze fenêtres/partiel,
trois options/défaut 900, cinq options 2700 et six consommateur vivant/pause/
namespace. Onze campagnes distinctes, images conservées. Les confirmations
SIGTERM (15) et SIGKILL (9) ont pidfd lisible puis pilote absent de /proc, mesurées
10,765 ms et 28,345 ms ; gardes de 120 s et restitutions attendues jointes. Les
options 900/2700 s sont programmées puis restituées, pas laissées expirer.

Les trois essais antérieurs sont exclus ; le ciblé SIGKILL de deux groupes n'est pas ajouté
au même cas de cette matrice. Le contrôle final garde le même conteneur 68a8 et image c59,
redémarrage à 14:26:18 UTC, référence inchangée, deux services sains, actifs à zéro, 5 982 artefacts
et aucune garde. Cette preuve qualifie les fenêtres communes ; pannes
propres de capture et d'observateur source, âge et campagne complète restent
ouverts dans 078.5. Les preuves antérieures conservent leurs époques distinctes.

## Refus après attachement qualifié

La [preuve 956498a](evidence/invocation-source-observer-refusal-dev-2026-11-11.json)
passe deux groupes sur 351 sources identiques avant/après. Le scénario du
créneau réel 15:00 UTC ne produit aucun HTTP ordinaire : un vrai HTTP et un
vrai cron sont running, leur tir/UUID/fonction recoupés. L'opérateur constate
l'historique insuffisant après attache : TracerPid 471960 sur le contrôle
470002/naissance 502682872, puis zéro après detach ; mémoire et lecteur fermés.
Son reçu garde completed=false et AssertionError/retention_history_incomplete.
Le code retour individuel de l'opérateur n'est pas enregistré ; celui du
helper est bien 1, avec l'assertion exacte conservée en privé et son SHA.

Le client de qualification termine 0 après ce refus attendu et la restitution
nominale jointe, sans ajouter de succès de rétention ni de purge métier. Deux
conteneurs, deux réseaux et deux baux sont corrélés puis retirés, canaux et
artefacts absents. Contrôle final : même conteneur/image, redémarrage attendu
15:00:08 UTC, référence inchangée, deux services sains, actifs à zéro, 5 982
artefacts et aucune garde active. Seuls les deux fichiers de cet observateur/
client diffèrent des 25 régressions précédentes ; helper et images inchangés.

Ce refus qualifie une panne après attache et son nettoyage normal. Il ne
qualifie pas une erreur de detach, l'alarme 35 s, la coupure 40 s, l'attente
native 25 s sans événement ni l'âge de sept jours. Le nominal numérique garde
sa preuve distincte au commit d860cc5 ; la campagne complète reste requise.

## Pertes avant la commande de capture

Décision du 11 novembre 2026 avant code, pour les pannes de capture initiale
encore ouvertes dans SLS-078.5. Étendre uniquement le client
`e2e/schedule-retention-capture.mjs` avec deux options exclusives :
`--eof-after-gate` et `--observer-loss-after-gate`. Sans option, le nominal
conserve sa capture et ses quatre groupes. Aucun changement de l'opérateur,
du handler, du moteur ni des captures canoniques déjà conservées.

Les deux cas reprennent la même préparation réelle : connexion SSO normale,
fonction publiée/promue, HTTP témoin terminé puis vrai cron UTC. Attendre le
handler running puis le point gated, avec invocation succeeded et tir encore
dispatched/non clos, hash et UUID recoupés. La commande capture n'est pas envoyée :
aucun dossier schedule-retention supplémentaire ne doit être produit par ces cas.

- EOF : fermer réellement stdin du helper à ce point ; conserver son code 1 et
  son assertion capture_command_required. Exiger la restitution normale par
  finally, même CID/image/démarrage et configuration, TracerPid réel à zéro du
  même PID/naissance ; pilote terminé et timer/service joints.
- Perte : un acteur SSH root distinct ouvre le pidfd du seul helper désigné
  dans identity.json, après recoupement du mode, des UUID, de l'argv exacte,
  du PID/naissance/cgroup du contrôle et de son TracerPid égal au helper.
  Envoyer un seul SIGKILL par pidfd, confirmer la mort par ce même descripteur,
  puis mesurer le TracerPid zéro du contrôle encore identique. Attendre la
  vraie garde indépendante de 80 secondes, sans la remplacer par rescue ;
  recouper son reçu puis joindre timer/service. Conserver le vrai code SSH,
  sans le transformer en 137 lorsqu'il vaut 255.

Après chaque faute : attendre la clôture normale du même tir, une seule
invocation liée et les mêmes deux appels HTTP/cron, sans rejeu. Archiver/purger
la fixture par les API réelles et vérifier code, canaux, conteneurs, réseaux,
baux et volumes absents. Les captures canoniques et leurs empreintes restent
inchangées ; le banc n'en déduit ni rétention d'âge ni sauvegarde interrompue.

Quatre groupes par cas : préparation/témoin HTTP ; faute exacte après gated
et restitution ; contrôle repris/tir clos sans rejeu ; purge physique. Les
captures interrompues pendant backup ou copie et les régressions historiques
du helper demeurent distinctes. Une erreur conserve le rapport et interdit
la relance automatique. Le prérequis SSO est fourni par le client existant
`dev-sso-sessions.mjs`, identifiants en mémoire et seuls cookies de plateforme
conservés dans les fichiers privés habituels. Ces cas ne remplacent pas la
campagne complète et ne clôturent pas SLS-078.5.

### EOF, perte du pilote et nominal rejoué qualifiés

La [preuve 20ffc09](evidence/schedule-retention-gate-losses-dev-2026-11-11.json)
passe huit groupes (quatre par cas) sur 351 sources/images figées. EOF après
le point gated donne le vrai code 1 ; SIGKILL du seul helper est confirmé par
pidfd et SSH 255, suivi de la garde indépendante 80 s. TracerPid 477828/479746
puis zéro du même contrôle 472612/naissance 502712875, même démarrage 15:00:08 UTC.
Les deux UUID/dates restent identiques, tirs clos sans rejeu et deux purges
physiques terminées. Aucun nouveau dossier de capture dans ces deux cas ;
les inventaires canoniques sont identiques avant/après. Revue RO : RAS.

Le [nominal rejoué](evidence/schedule-retention-capture-regression-dev-2026-11-11.json)
passe ensuite quatre groupes sur la même époque : vraie capture RO du succès
avant clôture, reprise sans redémarrage et purge publique. Trois refus CLI
précoces (option inconnue, options multiples, doublon) passent séparément,
sans groupe E2E ajouté. La capture privée 9d2956df25784454a8a2b6da271b2d39 est
un témoin de non-régression ; elle ne remplace pas les deux sources canoniques,
et ses images ne sont pas exportées. Les dates d'éligibilité initiales du
18 novembre restent inchangées. Ces preuves ne couvrent pas backup/copie
interrompus, les cinq régressions historiques ni l'âge réel.

## Interruptions pendant sauvegarde et copie

Décision du 11 novembre 2026 avant code, pour le reste déjà inscrit de 078.5.
Après le rejeu historique actif, ajouter deux options exclusives au seul mode
terminal-capture : `--capture-loss=control-backup` et
`--capture-loss=artifact-copy`. Sans option, conserver le parcours nominal.
L'opérateur et son client sont modifiés après la fin du rejeu figé, jamais pendant.

Les points de faute exécutent le vrai travail avant un SIGSTOP du helper :

- Contrôle : appeler réellement `source.backup(destination,pages=16,progress=...)`.
  Le premier callback non final conserve statut, total et restant bruts avec
  `0 < remaining < total`. Les pages peuvent être en cache : aucune taille
  physique positive de destination n'est exigée. Le contrôle reste tracé au
  point acquis ; le fichier partiel n'est pas ouvert pour récupération SQLite.
- Artefacts : une fonction de copie appelle réellement `shutil.copy2`, vérifie
  le fichier obtenu, puis suspend après un fichier conforme et avant la fin
  de l'arbre. Le reçu porte le chemin relatif, SHA/taille/mode et les nombres
  copiés/attendus avec `0 < copied < expected`. Le contrôle est déjà détaché,
  le même tir clos et aucune instance ne subsiste. Ce cas ne revendique pas
  une interruption au milieu d'un fichier.

Le callback SQLite s'exécute sous l'EUID propriétaire du contrôle. Préouvrir
sous root un reçu 0600 dans le dossier protégé de la garde, synchroniser son
entrée de répertoire, puis écrire complètement et fsync sur ce FD dans le
callback. Aucun accès par chemin à /run n'est tenté sous l'EUID abaissé.
Émettre le reçu réel après synchronisation, fermer le FD, puis SIGSTOP ; un
SIGCONT inattendu termine en échec, sans publication de capture complète.
Les backups préparatoire et du registre restent hors de ces hooks.

Le client utilise le même SSO, HTTP témoin et vrai cron. Après la commande
capture, il attend le point de faute, recoupe le reçu durable, le PID/naissance,
l'état arrêté du helper et son EUID, puis le TracerPid attendu du contrôle.
Attendre la véritable garde 80 s : elle doit tuer et joindre ce helper avant
restitution. Conserver son signal et le vrai code SSH, mesurer TracerPid zéro
et même contrôle/image/démarrage. SIGKILL saute le finally : aucune fermeture
Python explicite de lecteur ni attente de flock n'est revendiquée.

Chaque cas crée exactement son nouveau dossier partiel identifié. Après garde,
conserver son inventaire brut et l'absence de manifeste final capture.json ou
d'événement retention-captured. Le cas artefacts peut avoir émis
control-resumed-after-capture ; il ne suit donc pas le refus avant commande.
Les captures canoniques restent identiques. Protéger uniquement ces nouveaux
artefacts de faute, sans changer leurs octets ; aucune source partielle ne
remplace une source d'âge. Clôture normale du même tir, mêmes deux UUID/dates,
purge publique et absence physique terminent chaque cas.

Quatre groupes par cas : préparation réelle ; progrès interrompu et garde ;
reprise sans rejeu et dossier partiel ; purge. Rejouer le nominal après ces
options. Les preuves de chaque époque restent distinctes ; régression complète
et âge réel restent requis avant clôture. Aucun succès acquis par ce contrat.
