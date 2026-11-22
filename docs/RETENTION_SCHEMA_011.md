# Rétentions sur le contrôle courant011

Contrat de [SLS-132](BACKLOG.md#sls-132), décidé le22novembre2026 avant code.
Complément courant de [RETENTION_HISTORY_REPLAY](RETENTION_HISTORY_REPLAY.md),
[SCHEDULE_FIRING_VOLUME](SCHEDULE_FIRING_VOLUME.md) et
[INVOCATION_SOURCE_RETENTION_VOLUME](INVOCATION_SOURCE_RETENTION_VOLUME.md).
Les commandes, captures et preuves historiques gardent leurs sources et résultats.

## Époque et autorité

La première époque011 qualifiée utilise f73efa6e4e2b944b0cbc02f207c6cda0258138df1a7718579a9b0396d02e68d0,
le runtime1e64b4af9ae7d5b753505a23370ab83345fdfee1f1587a15a4e723b2cd6a8a9a.
Les empreintes complètes des modules exécutés et des sources du banc sont figées
avant chaque campagne. Un changement produit impose de nouveaux passages affectés.
La seule cible est infra-serverless ; les opérations sont sérielles, avec les
vrais SSO, API, Docker, agent et horloges. Aucune ligne/date métier ni réponse
système ou HTTP de remplacement. Les contrôles statiques et préparations ne
comptent pas comme rétention qualifiée.

Les préconditions **courantes** instance-limit deviennent001..011 ; les listes
SCHEMA_006/007/008/010 restent disponibles aux branches historiques explicites.
Le schéma courant est vérifié intégralement, pas seulement par longueur. Aucun
retrait d'assertion ni comparaison permissive à plusieurs schémas. L'identité de
collection et toutes les tables originales011 restent dans leurs répertoires
originaux conservés. La restitution reconnaît dev/inode, remet ces mêmes dossiers
et redémarre le même CID/image ; elle ne copie jamais une base009 sur011.

## Préservation des images avant la capture numérique

Un outil natif DEV distinct exporte les deux images immuables dans un dossier
neuf `qualification-history/retention-images-<hash complet du contrôle>`.
Il vérifie API/référence sains, CID/image/démarrage et onze migrations, zéro
fonction vivante/instance/appel actif/opération et registres sans bail. Chaque
`docker image save` réel est borné40s ; échéance globale90s, sans service
arrêté. Chaque export possède une session/groupe natif ; le helper subreaper
retire et joint timeout/runuser/Docker en finally, y compris sur alarme, avant
tout retour. Le nettoyage est borné5s et une jonction manquante reste un échec. Le dossier est root0700, archives/reçu root0400, chemins canoniques sans
symlink ; espace libre vérifié, fichiers fsync puis reçu terminé publié en dernier.
Le reçu contient SHA/octets/image réelle pour chaque archive, empreinte de
l'opérateur et observations avant/après identiques. Une interruption garde un
dossier incomplet refusé : jamais de réexport ou écrasement automatique.
Une archive existante complète est vérifiée en lecture seule, pas recréée.
Les archives et reçus historiques restent intacts ; aucun tag n'est déplacé.

Le client de capture vérifie cette préservation **avant d'ouvrir sa fenêtre**.
Le snapshot courant la sélectionne seulement pour target_schema011 et exige
l'égalité contrôle exécuté/runtime témoin avec les deux images préservées.
Le snapshot historique conserve sa sélection de5056167 et son égalitéc59.
Le reçu de capture nomme la source réelle de préservation et les migrations
constatées dans la sauvegarde, sans changer les témoins SQL historiques.

## Nouvelle source numérique authentique

`node e2e/schedule-firing-volume-capture.mjs` conserve ses quatre groupes :16
publications/promotions réelles, première fenêtre256tirs avec2succès/254refus,
backup natif protégé puis16purges et restitution jointe. Les refus de capacité,
UUID, indices, hashes et logs sont identiques au contrat initial. Min0 et idle0
imposent zéro consommateur avant copie. Le lecteur hérite du verrou ;30s/40s
restent les limites de capture, garde900 inchangée. L'image est celle servie.

Les fichiers canoniques ne sont ensuite jamais retouchés. C est le curseur
capturé : count devient éligible à C+39*300, après3h15 réelles et avant septjours.
Aucun contrôle ou fonction de cette installation temporaire ne reste actif
pendant l'attente. Les autres preuves indépendantes peuvent avancer en série.
Le reçu/public manifeste courant est distinct du manifeste du11novembre.
La CLI numérique sélectionne ce manifeste par l'argument explicite
--target-schema011 ; sans lui, elle conserve le manifeste historique009.
L'opérateur reconnaît uniquement ces deux manifestes nommés et leurs reçus
égaux, jamais une source arbitraire ou la dernière preuve d'un glob.

La vérification du replay reconnaît explicitement soit le manifeste historique,
soit le nouveau manifeste courant ; elle exige leur reçu complet égal au canonique,
leurs migrations exactes et leurs images respectives. Elle ne cherche pas une
preuve quelconque par glob. Avant tout arrêt : SHA/modes/root, SQLite immutable
sans sidecars, intégrité/FK, inventaire complet artefacts, registre quiet et
archives réelles. Le contrôle courant exige le schéma011 dans la source numérique
et l'égalité avec l'image servie ; aucune migration n'est nécessaire pour count.

Les options existantes --firing-history/--firing-observation restent explicites,
par paires et garde120 obligatoire. Fenêtre D+10..120, marge D+150, secours120,
observation25/alarme35/commande40 inchangés. Le relevé avant borne et le suivant
au même curseur doivent donner10240 ou10496 selon le lot complet, puis10000 UUID
exacts suivant completed_at DESC,id DESC ; toutes fenêtres/indices/générations,
les deux seules invocations initiales et aucune nouvelle invocation sont recoupés.
SSO neuf et pagination exhaustive, source intacte, originaux et gardes joints.
Les refus avant39fenêtres et les pertes seed/observer restent nécessaires.

## Âge authentique sur copies migrées

Les captures009 source9a2a4cd1 et terminala3993b7d sont réellement éligibles depuis
le18novembre. Elles gardent tous leurs SHA, reçus et exportsc59 ; leur nouveau
replay est une voie **explicite011** distincte de l'ancienne voie009/c59.
La vérification RO complète des canoniques demeure obligatoire. L'image d'origine
atteste les données ; l'image courante exécute le replay. Confondre les deux est
refusé. Le mode courant exige installation et témoin de clé identiques en mémoire
à l'original, sans exposer valeur/cipher, et onze migrations sur l'original.

Ajouter une option explicite --retention-target-schema011 seulement avec la paire
retention-history/observation ; refuser option isolée, autre mode, doublon ou
mauvaise image avant mutation. Les observations age/seed-loss/observer-loss sont
permises sur les sources éligibles. Le préflight jeune historique conserve son
refus aujourd'hui ; sa preuve n'est pas renommée. Un préflight courant RO vérifie
les sources et l'image avant toute fenêtre, sans revendiquer l'absence d'expiration
sur des données aujourd'hui anciennes.
La CLI `source|terminal preflight --target-schema011` appelle verify-current
en lecture seule, sans garde ni fenêtre. Les treize refus de la CLIinvalid
couvrent les huit historiques et cinq cas propres : cible seule, cible avec
seule pairefiring, vraie mauvaiseimage, imagecourante sanscible explicite et
préflightjeune sursource réellement âgée. Les modesâge/perte/namespace gardent
leurs fenêtres ; namespace utiliseage sur la voie courante.

La fenêtre exclusive reste D+10..60, garde120 ; source/contrôle original même
installation ne sont jamais simultanément consommateurs. Original/API et agent
arrêtés, aucun conteneur même arrêté/réseau/bail de l'identité clonée ; originaux
renommés et identités journalisées. Copies artefacts puis registre puis CONTROL
009 complètes fsync/rename, sous1001 ; aucune réécriture SQL de préparation.
Le vrai startup de f73 applique transactionnellement010 puis011 avant ses moteurs.
L'observateur est attaché avant readiness ; aucune observation de009/010 ne peut
valider une étape courante. Il enregistre les onze migrations committées et la
collection011 créée réellement dans la copie. Délais25/35/40 inchangés : une
frontière manquée reste un rouge, sans relance automatique ou allongement.

Oracle source : jusqu'à clôture du tir, les **métadonnées** de l'invocation source
restent exactement celles du témoin, le HTTP ancien expire, puis le même tir se
clôture normalement et la source est retirée. Le buffer `logs` ne fait pas partie
de cette égalité de métadonnées :072 exige au contraire son effacement réel et
`logs_collection_state=expired` même pendant la protection de sa chronologie.
Conserver séparément ces deux assertions, sans réécrire l'oracle009 historique.
Oracle terminal : mêmes tirs terminaux et générations retirées authentiques,
puis retraits d'âge normaux et absence de nouveau handler. API réelle après
nouveau SSO, sans invocation directe de maintenance. Les témoins copiés ne sont
jamais recomptés comme des handlers nouvellement exécutés.

Pertes : vrais SIGKILL après registre/avantCONTROL et après attache ; mutations
et timeout joints avant restauration grâce au verrou hérité. La garde120 doit
retirer les copies avant D+240 et terminer la restitution avant D+270, sans
atteindre le prochain créneau D+300. Le refus de namespace étranger demeure ;
seul le namespace original de fixture créé par l'API peut être retiré par le
client pour permettre la restitution. Aucun marqueur booléen ne donne propriété
sur une installation ou un dossier. Référence/configuration officielle inchangées.
Une perte peut laisser la copie009 ou010 avant commit011. Après vérification
stricte image/campagne/répertoires/périmètre, l'observation de restitution
nomme cette migration incomplète comme diagnosticindisponible et permet le
retrait de la copie possédée. Un schéma inconnu reste refusé ; seul l'oracle
nominal exact011 donne une preuve fonctionnelle courante.

## Source sous plafond et rattachement final

Le nominal courant de source sous plafond garde le vrai client10001HTTP+1cron,
sa garde2700, ses trois vecteurs10002→10001→10000, l'observation native25/35/40,
les métadonnées/UUID et deux plus anciens HTTP retirés exactement. Il ne reconstruit
aucune base depuis un JSON historique. Rejouer les pannes et consommateurs des
opérateurs partagés qui ont changé ; leurs preuves sont distinctes du nominal.

Les trois nouvelles preuves de rétention portent leurs sources exécutées exactes,
image011, brut gzip vérifié et contrôle de restitution. La garde de régressions
courante ne les accepte qu'avec égalité stricte des modules execution/schedules/
calendar actuels ; les anciennes preuves restent consultables avec leurs époques,
sans substitution d'empreinte ni ajout de groupes. Tant qu'une des trois manque,
SLS-132 et072 restent ouverts. Les49campagnes/543groupes/18prérequis et l'inventaire
des consommateurs supplémentaires sont exécutés ensuite sur le code courant figé.


## Discriminant de perte avant commit011

Précision du22novembre avant code : pour le seul observer-loss courant, relever
les migrations committées au premier arrêt natif et exiger009 ou010 exactes.
À ce point, suspendre le seul conteneur temporaire par Dockerpause et confirmer
Paused=true, mêmeCID/image/PID/naissance/cgroup et mêmes répertoires reconnus.
Le [freezer cgroup réel](https://docs.docker.com/reference/cli/docker/container/pause/)
maintient cette copie incomplète après la mort de l’observateur ; aucun syscall
ou étatSQL n’est remplacé. Puis vrais SIGKILL pilote/observateur. La garde120
doit rencontrer le diagnosticretention_copy_migration_incomplete, retirer le
seul conteneur possédé et restituer les originaux011. Le
[retrait forcé Docker](https://docs.docker.com/reference/cli/docker/container/rm/)
utiliseSIGKILL ; son résultat est à constater réellement, jamais supposé.
Le client exige schéma incomplet au point de perte ET diagnostic de la garde,
absence du CID, source canonique intacte et bornesD+240/D+270. Le modehistorique
et les nominaux ne suspendent pas le contrôle. Motif : une simple perte du
traceur peut laisser le startup finir avant120s et ne prouverait pas ce chemin.


## Diagnostics des bornes propres de l’exporteur

Avant code : trois cas natifs cli90, join5 et alarm-join5, chacun dans sa seule
unitérootDEV oneshot, sansrestart, RemainAfterExit, TimeoutStart180s,
TimeoutStop30s et KillModecontrol-group. L’opérateur recoupe ces propriétés
réelles, MainPIDself et cgroup avant toute action. Aucun de ces cas n’appelle
preserve ni n’écrit dans les dossiers d’images canoniques.

CLI90 exécute verify original, observe son armement90 puis retient l’openat
/etc/spark/env dans son try. Après90s réelles, SIGALRM doit êtrepending ;
libération sans supprimer ce signal, erreur réelle1/TimeoutError et terminaison
au plus1s après le gate. Aucun signal d’alarme ou résultat n’est fabriqué.

Les deux autres cas appellent export_image original, sortie du vrai image-save
vers un pipe noyau non drainé. Le threadDocker doit être réellement bloqué sur
ce même pipe avant arrêt du seul wrapper timeout. Le descendant runuser est
retenu à son vrai PTRACE_EVENT_EXIT, statutcomplet et GETEVENTMSG de SIGKILL
exigés. Le finally du helper doit produire image_export_group_not_joined ;
la durée EXIT→terminaison est comprise entre4,5 et5,5s (tolérance d’observation
native0,5s autour de5). cause_timeout égale min(45,tempsrestant réellementlu),
à1e-9 de représentation près. Une erreur de nettoyage10s ou un faux45 àla
place du restant44 ne peut pas passer.

Pour alarm-join5, le helper est retenu avant son getitimer jusqu’à46s après le
vrai armement90. Il lit ensuite son propre tempsrestant (~44s). SIGALRM doit
être àlafois bloqué etpending pendant la jonction, après la mort du wrapper et
pendant le vrai EXIT-stop. Aucun arrêt du helper pendant ces5s. L’erreur de
nettoyage garde priorité sur l’alarme et la causeTimeoutExpired, comme dans le
code exécuté. Un noyau ne donnant pas l’événement exigé garde le cas rouge.

PID/naissance/parent/PGID/SID/cgroup/argv/pidfd sont recoupés avant les signaux ;
aucune action sur le daemon ou les applications. La sortie retenue est libérée
parCONT, jamais par un secondSIGKILL supposé ; tous les descendants sont
récollectés soussubreaper et le groupe est vide. Chaque cas recoupe ensuite les
mêmes services/CID/image/démarrage/configuration/collection et les mêmes reçus,
SHA et modes canoniques. La qualification attend aussi l’état terminal puis
l’arrêt et la jonction réels de sa seule unitéroot ; diagnostic = zéro groupe de
clôture, aucune rétention historique réadditionnée.


## Exécuteur courant après optimisation133

La bascule gardée du22novembre à22:25:50UTC sert désormais
`sha256:f016a1b71cb055c4f4c4e2fb2a2622c67c93f7a6ec26b39ec7e663cd9de4c0c7`.
Ses42backend diffèrent def73 seulement par execution_logs.py ; quatreweb et
migrations sont identiques. Le contexte de build réel est gelé. Cette image et
le runtime1e64 ont leurs propres exports canoniques, vérifiés avant toutefenêtre.
Les huit clients/opérateurs courants d’éditeur et de fixtures pinés sur f73
utilisent maintenant ce seul exécuteur approuvé ; leurs oracles restent stricts.
Le profiler133 et le diagnostic90/5 conservent leur imagef73 de mesure historique.

Pour les seules sources numériques011 du manifeste nommé a5a8fc06, vérifié
intégralement par verify_capture, l’imagef73 scellée atteste le dataset tandis que
f016 l’exécute. Avant mkdir/guard/arrêt, vérifier imageoriginale saine égale à
f016, migrations001..011 exactes, sources embarquées égales aux sources locales
synchronisées, runtime égal aux exports et préservationf016 vérifiée. Le retour
source garde tous ses champs inchangés ; l’exécuteur est enregistré séparément
et l’observateur exige cette même imageoriginale gelée. Les branches009 restent
liées à leur imagecapturée, sans acceptation générique d’un autre dataset.
Les deux pins du replayâge courant suivent f016 ; sources009/c59 inchangées.

Les modesinvalid courants prouvent, avantfenêtre, le refus de l’ancienf73 pourtant
disponible et de la vraieimageruntime comme exécuteurs. Les huit refus numériques
existants deviennent dix ; les treize refusâge deviennent quatorze. Comptages
propres et noms des groupes suivent ces nombres, sans réaddition historique.
La préflight numérique1..38 reste réservée à un âge réel compatible ; a5a8fc06
ayant dépassé39fenêtres ne peut plus la réussir. Son refus historique conserve
sa portée. Aucune horloge ni date ne change pour fabriquer cette éligibilité.

Trois chemins publics courants sont fixés avant code de garde :
`evidence/schedule-firing-retention-count-schema011-query-dev-2026-11-22.json`,
`evidence/invocation-source-retention-volume-schema011-query-dev-2026-11-22.json`,
`evidence/schedule-retention-age-schema011-query-dev-2026-11-22.json`.
Leurs bruts gzip sont nommés dans chaque manifeste. La garde exige completed,
imagef016 exacte et quatre modules courants exacts : execution.py, schedules.py,
schedule_calendar.py et execution_logs.py. Elle vérifie SHA compressé et SHA
noncompressé en lisant le gzip intégralement ; aucun glob de dernièrepreuve ni
réécriture d’une preuvef73. Un chemin manquant reste un refus. Chaque preuve
reste ciblée (3numériques,3source,6âge) ; aucun de ses groupes n’est ajouté au
socle49/543. Les nouveaux refus/pertes et les régressions012API/10UI/25communs,
49/543/18 puis32/276 restent distincts et requis.
