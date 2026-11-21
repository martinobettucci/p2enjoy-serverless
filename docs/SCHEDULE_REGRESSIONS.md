# Campagne complète des planifications sur le contrôle courant

Contrat de clôture de [SLS-078](BACKLOG.md#sls-078), complément de
[SCHEDULES](SCHEDULES.md#preuves-e2e-attendues). Décision du21novembre2026,
après livraison des préalables103/104 et avant code du lanceur.

## Assemblage et comptes

Ajouter `python3 -B e2e/execution-suite.py --scope schedules`. Il conserve
l’union du scope function-catalogue :37campagnes uniques/489groupes, toutes
ses assertions et ses six prérequis. Ajouter ensuite, dans cet ordre :

| Client Node | Groupes | Fonctions | Discriminants principaux |
| --- | --- | --- | --- |
| schedules |6|3|Frontières, fusion, Unicode, événements et droits |
| schedule-calendar |5|3|Grammaire numérique, OU jour/semaine, prévisions |
| schedule-versions |5|3|Pilote, promotions, retour, retrait/désactivation |
| schedule-recovery |5|1|Trois coupes, fenêtres manquées, aucune reprise du tir |
| schedule-admission |5|5|CPU, exclusif, file, deadline,315s et extinction |
| schedule-memory-version |5|3|RAM8192, refus isolé et hash changé avant admission |
| schedule-queues |4|9|16/128 réceptions réelles, refus sans invocation |
| schedule-unavailable |4|1|Cache réellement inaccessible, reçu et données conservés |
| schedule-instance-reuse |4|2|Maximum distinct des budgets, minima et mêmes CID |
| schedule-concurrency |4|2|Seule concurrence1/2 varie, maximum3 et shared identiques |
| adapter-schedules |4|2|Vrais plan/deploy/promote et tir après promotion |
| schedule-console |3|2|Accueil, formulaires, six tirs, pages5+1 et vrai401→200 |

Total attendu :49campagnes/543groupes, dont54groupes propres aux douze clients.
Les36fonctions de ces douze campagnes sont distinctes. Les sous-assertions,
lecteurs natifs, connexions SSO et builds ne deviennent pas des groupes ajoutés.
Ne pas utiliser --unicode-regression-only à la place du nominal6groupes.
Aucun scénario de charge en parallèle avec un autre client ; les réceptions
concurrentes internes à un scénario restent ses véritables consommateurs.

## SSO, durée et repos

Les identifiants restent sur stdin privée puis en mémoire, jamais argument,
environnement, fichier ou rapport. Conserver les préparations SSO du socle.
Avant chacun des douze clients cron, refaire deux connexions depuis l’accueil
avec le helper dev-sso-sessions, purpose scheduled-regressions ; seule la session
plateforme est écrite dans ses fichiers privés habituels. Chaque préparation
a son nom dans le checkpoint et son reçu figé, sans identifiant de session.
Total :18prérequis, dont les douze préparations supplémentaires ; chacun doit
être frais et réussi, sans être compté dans543.

Les durées des contrats restent inchangées : reprise environ40min, admission/
RAM/files environ15min chacune, indisponibilité/réutilisation environ10min.
Le total dépasse deux heures, plus le socle et les autres frontières. Aucun
timeout global600s ni accélération d’horloge. Une exécution reste suivie jusqu’à
la fin réelle de ses processus ; les gardes distantes existantes ne changent pas.
Le lancement long utilise `python3 -B e2e/schedules-worker.py start`, unité
systemd utilisateur transitoire serverless-schedules-regressions-UUID, sans
récurrence ni redémarrage automatique. Type=oneshot, RemainAfterExit=yes,
TimeoutStartSec=21600, TimeoutStopSec=60. Le lanceur transmet les identifiants
uniquement par un pipe stdin directement passé au service (`systemd-run --pipe`),
puis ferme son écriture ; sorties vers fichiers privés0600, processus de lancement
détaché de la session du terminal. Aucun secret dans une propriété systemd.
Le worker conserve les identifiants en mémoire pour les seuls SSO déjà définis.

Relever PID/naissance/cgroup du service et de son client de lancement ; observer
le même worker vivant après le retour du lanceur. `status NOM` lit son état,
`finish NOM` exige MainPID0 et résultat systemd terminal, fige le SHA du rapport,
puis arrête cette seule unité et joint la disparition du client exact. Une
suite completed ne suffit pas si Result/ExecMainCode/ExecMainStatus ne valent
pas success/1/0. Une perte ne relance rien et impose d’abord le recoupement des
gardes et restaurations distantes. Ce lancement ne change aucun scénario,
aucune garde distante ni aucun compte de groupe.

Avant chaque campagne cron, recouper le repos natif : aucune fonction vivante,
instance, opération, invocation active, réservation ni bail ; services sains et
configuration officielle/budgets inchangés. Après chaque campagne, recouper sa
purge physique avant de passer à la suivante. Une issue inconnue arrête la suite.

## Rapports frais et conservation

Rapport principal privé schedules-regressions.json et dossier schedules-run-UUID
neuf0700. Avant tout écrasement d’un rapport existant, conserver ses octets et
ses captures déclarées. Conserver aussi les nouveaux rapports exacts par phase,
SHA, dates, sortie du processus, sources/images avant/après et commit du gel.
Les résultats SSO successifs sont figés avant leur prochain écrasement.

Les douze clients écrivent des noms UUID : onze scheduled-functions-8hex.json,
l’indisponibilité storage-recovery-8hex-schedule.json. Relever l’ensemble des
chemins présents avant le client puis imposer exactement un nouveau rapport
conforme après ; ne jamais sélectionner simplement le dernier fichier. Lier ce
chemin au checkpoint et vérifier sa fraîcheur, son SHA et ses groupes exacts.
Un processus non nul reste un échec même si son rapport se dit terminé. Aucun
rejeu automatique ; conserver l’essai et qualifier une relance séparément.

Trois clients ne déclarent pas cleanup : schedules, calendar et versions.
Ne pas leur inventer ce champ. Exiger completed, zéro skip/échec, tous les
groupes réussis, cleanup_errors vide, puis leur recoupement physique strict.
Calendar/versions ont aussi native_after_purge ; schedules doit recevoir le
même recoupement RO externe de ses trois fonctions. Les neuf autres clients
conservent leur exigence cleanup=true et leurs observations natives propres.
Lire les identifiants singulier/pluriel tels qu’ils sont réellement produits,
avec unicité, compte attendu et namespace propre vérifiés.

## Recoupement physique et visuel

Étendre storage-suite-inspect pour le scope schedules explicite. Conserver
intégralement les10namespaces/32fonctions de stockage/URL et les13/59 du
catalogue : le sous-ensemble reste23/91. Ajouter séparément12namespaces et
36fonctions cron, soit35/127au total, sans inclure les UUID des installations
historiques temporaires. Chaque lecteur storage-console-inspect reçoit un
namespace à la fois pour les crons, conservant ses bornes existantes.

Exiger code/volumes/conteneurs/réseaux/baux/canaux absents, parents supprimés,
générations retirées, aucune commande/candidat/appel/réservation active et
aucune garde/helper vivant. Les reçus de reprise et d’indisponibilité gardent
leurs vérifications propres. Relire dix migrations exactes, intégrité/FK,
38backend et quatre ressources HTTPS ;5982artefacts originaux, référence et
configuration conservés. Le contrôle peut redémarrer aux coupes explicitement
prévues ; son image et son CID restent ceux de l’original.

Indexer les contrats SCHEDULES, SCHEDULE_*.md et RETENTION_HISTORY_REPLAY avec
les sources actuelles. Recouper toutes les captures déclarées, y compris les
formats SHA simple ou objet viewport/full_page ; ouvrir individuellement les
nouveaux originaux desktop/mobile. Les25communs ne remplacent pas cette campagne.

## Rattachement des époques de rétention

Les replays numériques historiques ne sont plus admissibles avec leurs témoins
âgés de plus de sept jours. Ne pas lancer leurs modes jeunes/preflight/refus
pré-éligibilité pour les contourner, changer les dates ou les compter comme skips.
Conserver leurs preuves publiées et les contrôles d’identité de leurs sources :
borne globale des tirs (schedule-firing-retention-count du11novembre), source
protégée sous borne (invocation-source-retention-detach-volume du11novembre),
puis âge réel (schedule-retention-age du21novembre). Les trois modules communs
schedules.py, execution.py et schedule_calendar.py ont été comparés : leurs SHA
sont identiques à ces trois preuves et au produit courant. Relire ces égalités
au gel de la campagne ; une différence invalide ce rapprochement.

Ces preuves gardent leurs images, leurs époques et leurs comptes. Les captures
scellées restent intouchées ; les builds/chargements et restitutions103/104 ne
les transforment pas en nouveaux groupes543. Le rapprochement documente ce qui
est conservé, ce qui est rejoué et ce qui est effectivement servi. Les limites
résiduelles du banc portent091.2 ; elles ne sont pas des preuves produit.

## Livrable de clôture

Une preuve compressée lie les49rapports frais,18prérequis, collectes finales,
captures inspectées, continuité du code des preuves conservées et essais exclus.
Mettre à jour backlog, journal, matrice, DAT, README et déploiement avec les
résultats effectivement obtenus. Toute preuve manquante garde078[~]. La clôture
globale095 et les unités produit encore ouvertes restent distinctes.

## Reprise après les préalables105/106/107

Les trois défauts de montage sont livrés avant la nouvelle campagne :
[107,46groupes](evidence/publication-console-hash-regressions-dev-2026-11-21.json)
raccorde les cartes au hash et aux promotions explicites ;
[106,79groupes](evidence/regression-artifact-cleanup-dev-2026-11-21.json)
remplace la purge des seuls volumes par une purge publique complète recoupée ;
[105,37groupes](evidence/execution-console-warmup-dev-2026-11-21.json)
prépare explicitement la cible avant les six instances réelles. Ces preuves
gardent leurs gels et leurs comptes ; aucune n’est ajoutée aux543 attendus.
Produit b452,38backends et4web restent ceux recoupés ; le code du moteur et les
trois modules de rétention conservés ne changent pas.

Les deux workers précédents sont terminés et finalisés :6d7b0401 est refusé
avant SSO sur deux documents décalés, zéro groupe ; d25a507d passe15campagnes/
272groupes puis s’arrête à execution-ui, rapport exact
c50fd918500cf5a1bb3a4af3228b3a90b93d9e8804bc3dbe5b35653b2f68ce4e.
Sa révision conservée en trop est attribuée puis purgée par106 ;5982originaux
rétablis sans manque/modification. Ces essais restent incomplets et exclus.

Décision de reprise : nouveau worker/UUID et assemblage entier49/543 avec
18prérequis, sources450 figées et état natif au repos. Aucun saut vers les
crons ni réutilisation des272groupes comme résultat du nouveau gel. Le suivi
conserve aussi explicitement les7images contrôleUI non déclarées par son
ancien rapport, avec SHA et fraîcheur source de leur phase, avant toute
réutilisation de fichiers. Les6PNG login restent distingués de ses déclarations.
Les captures scellées de rétention sont intouchées ; seuls les rapprochements
d’identité déjà définis sont exécutés. Résultat complet, finalisation du worker,
reçus des gardes et inspection des captures restent requis avant078[x].

## Nouveau passage entier après SLS-108 et SLS-109

Décision du 21 novembre 2026, après leurs livraisons et les boucles IR-001/002.
La [preuve108](evidence/service-transport-promotion-regressions-dev-2026-11-21.json)
passe 30 groupes et la [preuve109](evidence/modern-client-promotion-regressions-dev-2026-11-21.json)
en passe 106 : configuration, adresses, catalogue et stockage conservent leurs
préparations pilotes puis leurs choix explicites. Les 81 groupes des dix
clients109 restent inchangés. Ces comptes appartiennent à leurs gels propres
et ne s’ajoutent pas aux 543 du passage complet.

Le troisième worker9c509830 est finalisé, unité arrêtée et client joint :
18 campagnes / 313 groupes avant échec service-transport, quatre prérequis.
Rapport de suite exact0399336a9f3f5da9663a9a4bad1e989dcf9cbab571987646d31e55d89c3fb182,
rapport ciblé abb5923490a3db31c819b1085f5a44c5f35e545efca58474a822343085b0bdae.
Ses 63 captures sont inspectées mais ne complètent pas la suite manquante.
Les trois essais précédents restent incomplets et exclus, sans somme entre gels.

Le nouveau worker reçoit un UUID neuf, un arbre propre committé/poussé,
453 sources synchronisées et le même produit b452. Repartir depuis la première
campagne avec les 49 campagnes / 543 groupes et 18 prérequis, sans reprise au
premier cron ni réemploi des 313 groupes. Renouvellements SSO, bornes et durées
réelles restent ceux définis plus haut. Les captures scellées ne sont ni déplacées
ni réécrites ; leurs trois modules de rétention sont recoupés au gel.

Les purges physiques portent sur les fonctions : configurations et secrets
propres effacés, parents supprimés logiquement et jetons révoqués. Conformément
à CONSOLE_STORAGE, elles ne détruisent aucune configuration commune des parents.
Les remises à zéro explicites des quinze services catalogue restent contrôlées.
La collecte ne doit pas inventer une obligation générale de parents vides.

Avant clôture078 : résultat complet du même worker, finalisation systemd/client,
49 rapports et 18 prérequis exacts, toutes les captures fraîches ouvertes,
reçus natifs des fautes et helpers/gardes terminés, 127 fonctions / 35 namespaces
recoupés, 5982 originaux et configuration/référence préservés. Tout reste garde
078 en qualification ; les autres unités et la clôture095 restent distinctes.
