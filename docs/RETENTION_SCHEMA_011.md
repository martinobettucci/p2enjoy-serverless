# Rétentions sur le contrôle courant011

Contrat de [SLS-132](BACKLOG.md#sls-132), décidé le22novembre2026 avant code.
Complément courant de [RETENTION_HISTORY_REPLAY](RETENTION_HISTORY_REPLAY.md),
[SCHEDULE_FIRING_VOLUME](SCHEDULE_FIRING_VOLUME.md) et
[INVOCATION_SOURCE_RETENTION_VOLUME](INVOCATION_SOURCE_RETENTION_VOLUME.md).
Les commandes, captures et preuves historiques gardent leurs sources et résultats.

## Époque et autorité

L'image à qualifier est f73efa6e4e2b944b0cbc02f207c6cda0258138df1a7718579a9b0396d02e68d0,
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
