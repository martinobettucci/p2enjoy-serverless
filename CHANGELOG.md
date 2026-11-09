# Changelog

## [Non publié]

- Versionnement par hash en qualification DEV008 : upload préparé, déduplication,
  promotion explicite, pools et sélection épinglée, archivage et réimportation.
  Le checkpoint ciblé réunit71 groupes :2 migration/reprise,12 API,5 CLI
  authentifiés depuis le poste,6 UI,8 manuel et38 packaging/refus CLI Docker.
  Les28 captures sont inspectées ; manuel15 chapitres/52 paragraphes. Les vrais
  refus409/404 conservent le focus, et le suivi de publication relit le candidat
  avant le catalogue. Dix fonctions sont purgées,31 sources backend identiques
  entre époques. Le complément CLI authentifié passe cinq groupes par image,
  vingt commandes et douze invocations, sur245 sources. Deux fonctions de plus
  sont purgées ; aucun client, définition ou réseau/volume Compose résiduel.
  Les valeurs citées de cellule sont lues par Compose DEV. Les pannes et la
  régression complète restent ouvertes ; SLS-074 n’est pas clôturée.

- Registre persistant du hash des révisions : migration 007, alias historiques,
  lecture Read groupée et copie native dans la console.359 groupes réels passent
  sur l’image finale, avec69 captures recoupées et manuel15 chapitres/47 paragraphes.
  Les purges 006 engagées reprennent sans hash inventé, compteur effacé ni garde
  contournée. Le banc 003→007 et les refus de corrélation sont éprouvés. Le premier
  arrêt WAL est conservé ; les gardes utilisent une observation RO persistante
  qualifiée sous SIGTERM et SIGKILL. Déduplication/promotion/appels par hash restent
  dans SLS-074. Déploiement DEV uniquement.

- Identité canonique des paquets : bibliothèque commune et CLI d’extraction
  Docker qualifiées par sept groupes ciblés et 45 de régression, sur 222 sources.
  Inventaire du packager enrichi du mode exécutable ; neuf invocations réelles.
  Contextes de build bornés aux fichiers requis ; deux essais arrêtés conservés
  séparément. Le versionnement public complet SLS-074 reste en cours.

- Refus de lecture dans la console : trois groupes navigateur passent sur
  212 sources, depuis création/publication UI jusqu’au vrai source_forbidden,
  retrait des anciennes adresses/copies/succès, restauration et invocation
  de l’URL copiée. Cinq JPEG frais, une fonction purgée et garde finie recoupés.

- Catalogue sous refus réel de lecture : quatre groupes API passent sur
  211 sources, diagnostic source_forbidden borné, six refus d’autorisation,
  appels Docker par les deux domaines pendant EACCES puis catalogue restitué.
  Quatre invocations, une fonction purgée et garde terminée recoupées nativement.
  Le rendu UI de cette panne reste à qualifier.

- Garde du refus de lecture des routes : trois groupes réels passent sur
  210 sources, chmod du seul fichier officiel, EACCES du contrôle puis mode
  0640/lecture/santé restitués après release, SIGKILL ou SIGSTOP du helper.
  Signaux noyau et reçus immuables recoupés ; aucun contenu ou service modifié.

- Entrée publique de l’alias : trois groupes HTTPS/SSO réels passent sur
  207 sources, avec login/logout desktop/mobile et six captures inspectées.
  Les deux sessions du replay et celles des deux essais de mesure arrêtés sont
  fermées et recoupées séparément. Aucune route ou configuration modifiée.

- Catalogue vide du parcours public : trois groupes UI réels passent sur
  206 sources. Le GET navigateur survit au détour des deux routes ; aide vide
  desktop/mobile, restauration et invocation de l’URL copiée sont vérifiées.
  Une fonction purgée et les deux gardes terminées sont recoupées nativement.

- Pause/reprise native d’un vrai GET HTTPS : deux groupes E2E passent sur
  205 sources, dont SIGKILL du traceur et reprise indépendante. Le contrôle
  conserve son démarrage ; deux fonctions sont purgées et quatre gardes finies.
  Le premier essai arrêté sur un timer déjà collecté et son diagnostic restent
  distincts du replay. Le parcours UI vide public est qualifié par son complément ci-dessus.

- Cinq cycles réels des deux routes qualifiés : pagination API, alias vers
  18091 avec reprise explicite puis perte du pilote, retrait/rétablissement
  et deux ports vers 18091 avec catalogue vide local réel. Sept invocations
  Docker des URL émises, quatre gardes terminées, une fonction purgée et
  deux routes restaurées à 18090 TLS ; 203 sources et mêmes images recoupées.
  L’identifiant d’alias est renouvelé ; la canonique conserve le sien.
  [Preuve](docs/evidence/invocation-route-cycles-dev-2026-11-09.json).

- Traceur natif partagé extrait sans changement de son corps : quatre groupes
  transport des adresses et cinq de configuration passent sur 201 sources,
  six fonctions purgées dans deux namespaces et six gardes terminées. Aucun
  nouveau build applicatif ; le pilote de pause/libération est qualifié dans son complément.
  [Preuve](docs/evidence/invocation-native-observer-dev-2026-11-08.json).

- Trois déclencheurs de garde vérifiés sans perturbation : restauration
  explicite, SIGKILL du seul pilote et échéance avec pilote vivant, deux HTTPS
  et fin confirmée. Le premier arrêt HTTPS et le cache DNS négatif restent
  conservés séparément ; la reprise utilise la résolution native rétablie
  après expiration du cache. Aucun détour/retrait ni nouveau déploiement
  applicatif ; SLS-066 reste ouverte.
  [Preuve positive](docs/evidence/invocation-route-guard-dev-2026-11-08.json).

- Alias functions.lelabs.tech appliqué en DEV par la console normale vers
  18090 TLS, avec DNS exact et certificats réellement vérifiés sur les deux
  domaines. Huit groupes API/CLI et six UI passent ; quatre fonctions purgées
  dans deux namespaces, sept captures inspectées. Le premier reçu de déclaration
  interrompu et le départ API sur session expirée restent séparés. La reprise
  de vérification n’envoie aucune mutation. Les cycles de retrait/détours sont qualifiés ci-dessus ; SLS-066 reste ouverte
  pour la source perturbée et les pages suivantes sur six domaines.
  [Preuve](docs/evidence/invocation-domains-dev-2026-11-08.json).

- Catalogue global SLS-067 qualifié en DEV : accueil Fonctions, recherche
  serveur, filtres paginés, tri/état et contexte de retour dans les six facettes.
  La preuve retient 37 campagnes uniques / 489 groupes réels, six prérequis
  distincts et 98 captures inspectées : 447 groupes aux clients inchangés puis
  42 réexécutés, deux époques explicites et mêmes sources produit/images.
  91 fonctions suivies purgées dans 23 namespaces ; quinze jeux de variables/
  secrets de services effacés ; manuel compilé à 15 chapitres et 46 paragraphes.
  Les deux arrêts précédents sont conservés, sans succès rétroactif.
  [Preuve](docs/evidence/function-catalogue-dev-2026-11-08.json).

- Refus du catalogue après publication qualifié en DEV : CLI retenue avant sa
  sixième connexion, jeton révoqué par l’API, vrai 401 conservant publication
  et UUID sans rejeu. Le replay passe 17 groupes en série, 188 sources/images
  stables, neuf fonctions purgées dans trois namespaces et six gardes terminées.
  Un premier essai échoué à une barrière reste archivé, cause non prouvée,
  avec ses deux fonctions et gardes nettoyées séparément. Diagnostics nominaux
  conservés ; branches d’erreur du pilote non éprouvées.
  [Preuve](docs/evidence/invocation-url-refusal-dev-2026-11-08.json).

- Complément de transport du catalogue qualifié en DEV : trois groupes réels
  avec garde indépendante et coupures après publication, puis treize groupes
  de régression, tous réussis. Les vrais HTTP 502 conservent la publication
  et les UUID ; six connexions HTTPS CLI sans rejeu. Les 187 sources/images
  sont liées, huit fonctions purgées dans trois namespaces et six gardes terminées.
  La reprise de purge par UUID et la fin du groupe CLI bornent le nettoyage ;
  leurs branches d’erreur restent à éprouver. Le refus après publication est
  qualifié séparément ci-dessus par révocation 401. [Preuve](docs/evidence/invocation-url-transport-dev-2026-11-08.json).

- Suite complète des adresses réussie en DEV : union sans doublon de
  35 campagnes / 467 groupes, zéro échec/skip, six prérequis non comptés,
  186 sources et images contrôle/CLI figées avant/après chaque phase.
  Les 32 fonctions suivies sont purgées dans dix namespaces ; les deux
  restaurations historiques sont séparées. Les 79 captures sont recoupées,
  dont 61 observations et 18 identités avec une référence inspectée.
  Le client de panne corrigé passe 55 groupes et les huit
  groupes API éprouvent maintenant le Host réel et les redirections natives.
  Le build distant nominal est qualifié ; son expiration reste à éprouver.
  Une issue inconnue interdit un rejeu sans diagnostic.
  [Preuve](docs/evidence/invocation-urls-regressions-dev-2026-11-08.json).

- Catalogue des adresses d’appel déployé en DEV : routes officielles lues via
  montage readonly, facette de fonction et lien de service, copie d’URL/curl,
  résultat CLI séparé du succès de publication et entrée console/SSO canonique.
  Le checkpoint passe 88 groupes réels et recoupe 31 captures ; manuel à
  14 chapitres et 43 paragraphes. Les preuves multi-domaines et sources perturbées
  restent ouvertes dans SLS-066 ; le refus 401 est qualifié séparément ci-dessus.

- Stockage public qualifié en DEV : 29 campagnes en série, 397 groupes réussis,
  puis neuf groupes API renforcés de quatorze corps invalides de purge et d’une
  version périmée. Snapshots natifs identiques avant/après les refus, 28 fonctions
  des huit namespaces publics purgées, restaurations historiques et ressources
  recoupées. 72 captures vérifiées ; manuel à treize chapitres et 39 paragraphes.
  Les deux phases et les mises à jour documentaires de statut ont leurs empreintes
  distinctes. [Preuve](docs/evidence/storage-console-dev-2026-11-08.json).

- La première suite complète de stockage conserve son arrêt réel après 388
  groupes : prérequis de session de purge devenu invalide avant la campagne de
  décision. Le runner prépare une nouvelle paire SSO juste avant cette campagne,
  avec un rapport distinct, sans changer les durées d’authentification ni compter
  un groupe fictif. La nouvelle campagne complète termine avec succès dans la preuve finale.

- Suite publique de stockage intégrée : sept campagnes et 37 groupes E2E passent
  sur l’image du contrôle inchangée. Deux sessions SSO réelles préparées par stdin
  privée, onze archives créées via UI pour la pagination, 24 fonctions purgées,
  restaurations historiques recoupées et quatorze captures inspectées.
  [Checkpoint](docs/evidence/storage-console-focused-dev-2026-11-08.json).
  L’union complète et le complément sont recoupés dans la preuve finale.

- Versionnement par hash, déduplication, appels épinglés et pilote sans activation
  spécifiés dans SLS-074 et FUNCTION_VERSIONS. Les raccordements console, éditeur,
  client HTTP, journaux, budgets et crons sont consignés ; l’extension reste
  à implémenter au-dessus des révisions et du rollback existants. Le responsable
  confirme la dernière version promue pour le sans-tag : upload et promotion
  constituent deux actions distinctes, sans activation automatique.

- Suivi systématique des demandes du responsable dans le backlog, avec une
  table de correspondance vers les unités existantes et la règle persistée
  dans le contrat local. Critères de compatibilité du projet de référence
  explicités dans SLS-030 ; état de la purge/cache harmonisé avec SLS-065.

- Qualification réelle des réponses perdues de modification commune : coupures
  du contrôle avant traitement et après commit, issue CLI `unknown`, trois
  connexions HTTPS sans rejeu, aucune publication et relances explicites réussies.
  Cinq groupes natifs puis treize groupes de configuration passent sur la même
  image que le checkpoint de 191 groupes. Garde indépendante et nettoyage des
  quatre fonctions recoupés ; SLS-031 clôturée.
  [Complément de preuve](docs/evidence/service-configuration-transport-dev-2026-11-08.json).

- Les variables et secrets du `provider` sont désormais conservés dans le service
  lors d’un déploiement ; les fonctions portent seulement leurs surcharges.
  Le rapport distingue la modification commune des publications individuelles.
  L’API permet le remplacement du jeu de secrets et refuse les collisions ou
  dépassements effectifs avant mutation. La CLI borne aussi la représentation
  JSON Unicode du runtime. Treize groupes ciblés et les régressions passent :
  191 groupes en série, zéro échec/skip, 21 captures inspectées et manuel actualisé.
  [Preuve DEV](docs/evidence/service-configuration-dev-2026-11-08.json).

- Correction d’un effacement prématuré du code lors d’une purge bloquée par
  un changement inattendu du stockage. Le nettoyage général respecte désormais
  la garde de purge pour les révisions et candidats, y compris au redémarrage.
  Le défaut est reproduit avec une vraie ancienne publication puis migration ;
  22 groupes passent après correction et douze captures du manuel sont relues.
  [Preuve](docs/evidence/storage-legacy-recovery-dev-2026-11-07.json).

- Décisions publiques de stockage éprouvées avec une vraie session admin fermée
  pendant purge, refus du transport après commit, writer SQLite occupé et
  redémarrage indépendant du contrôle : quatre groupes nouveaux et sept groupes
  de reprise rejoués. Gardes du helper renforcées avec jonction du mutateur,
  restauration et attentes bornées. Six fonctions purgées et services rétablis :
  [preuve](docs/evidence/storage-decision-recovery-dev-2026-11-07.json).

- Purge pendant validation Docker vivante qualifiée : deux groupes réels,
  restauration indépendante du socket après perte du helper, conservation des
  réservations jusqu’au nettoyage et effacement du diagnostic tardif. Les neuf
  groupes API repassent avec conflit de type d’UUID et réutilisation des noms.
  Huit fonctions purgées et neuf répertoires de code absents recoupés dans la
  [preuve](docs/evidence/storage-validation-recovery-dev-2026-11-07.json).
  L’image du produit reste inchangée ; les preuves suivantes sont réunies dans la qualification finale SLS-065.

- Commandes publiques de stockage qualifiées sous révocation, collision,
  indisponibilité, SIGKILL et erreurs physiques : sept groupes réels, avec
  quinze groupes de régression et huit du manuel. Nettoyage des trois fonctions
  recoupé, onze captures du manuel relues. Fermeture interrompue et identité
  SQLite des helpers corrigées et éprouvées. Ce
  [checkpoint](docs/evidence/storage-command-recovery-dev-2026-11-07.json)
  est complété par les scénarios et régressions de la preuve finale SLS-065.

- SLS-065 déployée en DEV après contrat et migration 006 contrôlée : catalogue
  d’archives, vidage du cache, purge volumes/code/configuration, droits et reçus
  publics durables. Les neuf groupes API, neuf parcours navigateur et huit groupes
  du manuel passent. Le manuel affiche treize chapitres depuis sa source unique.
  Les pannes, reprises et régressions élargies sont recoupées dans la preuve finale.

- Protocole corrélé de vidage/purge, reçu durable, reprise et worker unique
  supprimant hors verrou du registre ; migration 004 agent et campagne réelle
  SLS-064 installés et qualifiés sur DEV : sept campagnes, 106 groupes réels,
  zéro échec/skip et nettoyage recoupé. [Preuve](docs/evidence/storage-discard-dev-2026-11-07.json).

- Console de publication vérifiée sur le SPARK DEV : 18 campagnes en série,
  312 groupes réels, zéro échec/skip et 54 captures inspectées. Sources, image,
  archives et nettoyages recoupés ; trois notes SPARK appliquées et relues.
  [Preuve finale SLS-063](docs/evidence/publication-console-dev-2026-11-07.json).

- Les consultations de publication effacent le succès précédent tout en
  conservant les diagnostics. Cinq gestes qualifiés séparément, manuel mis à
  jour et 29 groupes ciblés réussis après corrections (SLS-063-OBS-2).

- Concordance du candidat suivi avec sa ligne de liste, vérifiée pendant une
  vraie validation Docker et sur la capture rendue (SLS-063-OBS-1).

- Qualification de publication étendue à 21 groupes navigateur et dix API,
  avec vraies pannes de transport, permissions disque et confirmation de stockage.
- Première régression commune : 18 campagnes, 312 groupes réussis. La
  [revue initiale](docs/evidence/publication-console-review-dev-2026-11-07.json)
  des 54 captures a relevé deux incohérences de lecture, corrigées puis
  requalifiées dans la preuve finale ci-dessus.

- Publication ZIP depuis la console, conservation serveur de la configuration,
  suivi corrélé des candidats et abandon explicite, historique, activation et
  suppression des révisions. Le manuel décrit ces parcours (SLS-063).
- 32 groupes ciblés réels passent : dix API, quatorze navigateur et huit manuel,
  avec 21 captures relues. Sources, image et nettoyages recoupés dans la
  [preuve intermédiaire](docs/evidence/publication-console-checkpoint-dev-2026-11-07.json).
  Ce checkpoint précède l’extension et la qualification finale de SLS-063.

- Manuel d’usage intégré à la navigation, sommaire et ancres accessibles,
  rendu responsive compilé depuis l’unique source `docs/manual.md`.
- Maintenance du manuel imposée par le contrat local et concordance de son
  contenu avec la version déployée vérifiée E2E. 48 groupes passent avec zéro
  échec/skip et 33 captures relues : [preuve](docs/evidence/manual-console-dev-2026-11-07.json).

- Facettes Instances et Invocations dans la fiche de fonction : allocations,
  mesures réelles ou indisponibles, état et HTTP séparés, détails et journaux
  expurgés/tronqués, pagination, rafraîchissement manuel, clavier et mobile.
- 40 groupes réels réussis dans la suite de console, avec 25 captures relues,
  notes SPARK appliquées et code servi recoupé :
  [preuve](docs/evidence/console-execution-dev-2026-11-07.json).
- Le pilote de suite valide aussi le contenu des rapports frais ; les attentes
  réseau sont jointes aux gestes UI et le nettoyage retrouve les créations
  même si la navigation échoue.

- Moteur public déployé en qualification : migration 005, réservations CPU/RAM
  et instances, file bornée, minimum/maximum/inactivité, générations et reprise
  sans rejeu. Les appels admis restent possédés après déconnexion du client.
- Passerelle Lambda HTTP avec jeton Read, politiques origine/IP, corps/réponses
  bornés et observations paginées. Les droits métier sont conservés.
- 252 groupes réels réussis dans la suite finale : 31 groupes HTTPS et 221
  régressions, exécutés en série et liés aux sources, à l’image et aux rapports
  fraîchement écrits. Sept captures relues, trois notes SPARK appliquées ;
  [preuve](docs/evidence/execution-dev-2026-11-06.json).
- Gardes SQLite exécutées sous l’identité du propriétaire de la base, avec
  restauration root vérifiée. Les diagnostics et échecs initiaux sont conservés.
  La limite de réponse anticipée HTTP/1.1 du proxy DEV est documentée.

- Créations, changements de quotas, suppressions et publications raccordés à
  l’agent de stockage réel. Migration 004 du contrôle, décision commune avec
  l’objet, reprises abort/commit et relecture des droits après préparation.
- Confirmation perdue après commit signalée sans déclarer la publication
  abandonnée. Une panne d’audit conserve la réponse ; les publications sans
  changement de volumes n’exigent aucun verrou écrivain pour clôturer leur garde.
- Archivage conservant données et allocation à la suppression. Les campagnes
  vérifient les archives puis purgent leurs seuls volumes ; leurs archives de
  code restent conservées. Gardes de panne indépendantes, restaurations et
  erreurs de nettoyage explicites. [Preuve](docs/evidence/function-storage-dev-2026-11-06.json).
- 161 groupes réels réussis dans cette qualification, zéro échec et zéro test
  ignoré : 149 groupes rejoués en série sur le contrôle final et douze groupes
  de préparation sur le même paquet de stockage. Sept captures JPEG relues,
  sources et ressources déployées recoupées, trois notes de cellule actualisées.

- Quotas préparés avant publication : configuration précédente conservée,
  budget réservé jusqu'à décision, commit/abort idempotents et reçus versionnés.
  La migration 003 de l'agent garde les décisions après interruption ; un abandon
  retire uniquement les répertoires nouveaux restés vides.
- Dix groupes réels et 37 groupes de régression passent avec nettoyage confirmé,
  zéro échec et zéro skip : SIGKILL pendant préparation, restart après préparation
  ou abandon partiel, données conservées et refus sous bail actif.
  [Preuve](docs/evidence/storage-preparations-dev-2026-11-06.json).
  Le raccordement public figure dans la tranche décrite ci-dessus.

- Instances raccordées aux baux de l’agent : quatorze groupes réels réussis,
  avec persistance data/cache, quotas Linux, partage/isolation, pagination,
  annulations, timeout, perte FUSE et arrêt/reprise de l’agent. Destruction
  Docker confirmée avant libération ; nettoyage différé repris après panne.
- Canal privé migré hors du /run isolé de Docker rootless, par la configuration
  officielle du SPARK. Garde de racine installée vérifiée avec agent arrêté,
  puis variable et service restaurés. Les noms des instances indiquent leur fonction.
- 118 groupes de cette tranche et de ses régressions réussis, zéro échec/skip ;
  [preuve](docs/evidence/managed-storage-dev-2026-11-06.json), sources et ressources
  recoupées, trois notes de cellule appliquées et relues. Le raccordement public
  est livré dans la tranche du moteur décrite ci-dessus.

- Plafonds et reprises de publication : quatre groupes E2E réels réussis,
  avec 64 candidats, vingt révisions, puis SIGKILL pendant réception et
  validation Docker. Redémarrage, non-publication des candidats interrompus,
  configuration et archives intactes, nettoyage et publications suivantes vérifiés.

- Publication authentifiée : onze groupes API et sept groupes CLI réussis,
  dont concurrence réelle, droits, rollback, pagination, résultats partiels
  et reprise de brouillon. Le client rejoint ses uploads avant nettoyage ;
  une fixture écrit réellement un secret pour prouver l'expurgation des logs.
  Sources, archives et état Docker recoupés ; limites et interruptions ouvertes.

- Gestion authentifiée qualifiée : 19 groupes API, 11 parcours UI et huit
  groupes publics, nettoyage confirmé et sept captures relues. Noms longs
  lisibles sur mobile et restitution du focus après fermeture du menu corrigés.
  Sources, image, ressources web et configuration recoupées sur le SPARK DEV.
  Cycles SSO, publication authentifiée et intégration du moteur encore ouverts.

- Contrat OIDC courant fourni par le responsable : URL sur serverless.lelabs.tech,
  origine et accueil explicites ; déclaration synchronisée avec le client enregistré.

- Règle de nommage obligatoire dans le contrat local : rôle réel et usage
  compréhensibles, vocabulaire cohérent et qualificatifs justifiés ; lien
  depuis le README pour les prochains développements et leurs revues.

- Noms Docker explicites `serverless-api` et `serverless-runtime-reference`,
  avec conservation des volumes, de l’identité et des objets de la base.
- Entrée `https://serverless.lelabs.tech` appliquée dans la configuration SPARK ;
  clients E2E, documentation et trois notes de cellule actualisés. Persistance
  et reprise réelles, 38 tests HTTP, neuf contrôles navigateur, huit groupes
  HTTPS, quatre chemins réseau et quatorze contrôles CLI réussis. Connexion
  SSO personnelle et accès administrateur confirmés sur le nouveau domaine.

- Agent local de stockage DEV : registre WAL, générations FUSE, baux durables,
  quotas data/cache, conservation, archivage, purge et vidage explicites.
  Canal Unix borné avec contrôle d’UID ; maintenance fermant les mutations.
- Installation d’un paquet root immuable et de son unité systemd dans le SPARK.
  Corrections issues des preuves réelles : équité du verrou de surveillance
  à 64 montages et déplacement des répertoires en mode 000 avant suppression.
  Quinze groupes de cycle, huit de limites et 31 régressions FUSE réussis,
  zéro échec/skip et ressources nettoyées. Raccordement au pilote, API/UI et
  preuves d’interruptions intermédiaires ouverts.

- Pilote d’instances Docker chaudes avec enfant Node neuf, canal privé,
  deadlines monotones, réponses bornées, logs expurgés et mesures Docker.
  Récolte des descendants, fermeture coordonnée et nettoyage confirmé/reprenable.
- 31 contrôles réels d’invocation et 11 contrôles de cycle de vie réussis,
  avec les 36 régressions du chargeur partagé. Gros corps, OOM, PIDs, signaux,
  résultat tardif après suspension du contrôle et courses réellement exercés.
  Admission, volumes par fonction et passerelle authentifiée sont intégrés et qualifiés.

- Commande CLI deploy : cible HTTPS vérifiée, pagination, conservation des UUID,
  packaging avant mutation, publications en série et rapport des résultats
  partiels ou inconnus sans rejeu automatique. Valeurs résolues en mémoire.
- 14 contrôles réels de prérequis et de refus HTTPS, plus 24 scénarios
  plan/package rejoués dans les nouvelles images. Client authentifié ajouté
  pour pagination, publications successives et reprise de brouillon ; sa
  qualification authentifiée passe désormais ses sept groupes.

- Routes DEV de préparation, upload ZIP, validation Node, publication atomique,
  historique, rollback et suppression des révisions inactives. Migration 003,
  relecture des droits/versions au commit, verrou d’état et réservations
  conservées jusqu’au nettoyage confirmé.
- Huit groupes HTTPS publics et trente scénarios réels de démarrage/panne
  réussis sur la nouvelle image, dont exclusivité et reprise SQLite. Client
  de publication authentifié qualifié ; vues de révisions et invocation disponibles.

- Extraction ZIP serveur bornée : tailles réelles, cohérence des en-têtes,
  CRC, refus des liens et publication readonly sans écrasement. Correction
  du drainage DEFLATE et borne de lecture du hash d'entrée.
- 112 contrôles réels sur le SPARK DEV, incluant les limites de volume,
  20 000 fichiers, saturation disque, courses et les douze archives du
  packager chargées par Node. Intégration aux API de révision réalisée et qualifiée.

- Contrat OIDC du client DEV créé conservé dans le dépôt et rapproché du code.
  La campagne publique ajoute la découverte et les clés asymétriques réelles ;
  les points d'attente de rôle, azp ID token et rotation restent dans SLS-020.

- Chargeur Node 24 CJS/ESM et validation Docker avec transport Unix readonly,
  configuration applicative privée, logs expurgés et délai extérieur de quinze
  secondes. 36 scénarios E2E réels, dont dépendances, imports bloqués, limites,
  secrets recoupés, données binaires et destruction des descendants.
- Correction de confinement du canal, de troncature des secrets et de fermeture
  des connexions partielles. Intégration aux révisions réalisée et qualifiée.

- Première CLI d'adaptation YAML et de packaging ZIP, avec héritage explicite,
  descripteurs sans valeurs de configuration, inventaires SHA256, chemins bornés
  et publication des fichiers par descripteurs de répertoire.
- Manifeste plateforme des douze fonctions de qualification ; 24 scénarios CLI
  réels sur le SPARK, dans une image installée avec dépendances à empreintes.
  Upload et publication encore en développement.

- Checkpoint DEV du contrôle Python/SQLite et de la console React : parcours
  SSO réel, modèles de gestion, sessions/CSRF, jetons CRUD et formulaires.
  Qualification administrateur encore ouverte ; moteur et adaptateur à venir.
- Preuves publiques et navigateur, provenance réseau, limites SSO persistantes,
  pannes réelles de configuration/SQLite et interruption du client de preuve.
  Refus HTML conservant leur statut, journaux expurgés et rapports incomplets
  invalidés dès le démarrage. Dépendances verrouillées auditées sans avis connu.

- Stockage FUSE à quota logique : réservations avant extension, fichiers et
  répertoires ouverts après suppression comptés, refus des mutations hors
  contrat, verrou exclusif et conservation des fichiers natifs.
- Campagne DEV de 31 contrôles réels de stockage, Docker rootless, saturation,
  concurrence, arrêt brutal, remontage et configurations refusées.

- Contrat de plateforme et découpage SLS-010 à SLS-060 : identité, objets,
  adaptation YAML, moteur Docker, stockage, exploitation et console.

- Méthode software-factory-base importée : contrats, rôles Codex/Claude, hooks,
  scripts et campagne Git réelle. Formation et workflow pédagogique exclus.
- Hooks standard activés dans le dépôt Git initialisé par le responsable.
- Campagne E2E élargie aux bornes, refus, saturation réelle, logs, arrêt actif,
  reprise du worker, manifestes invalides et défauts réels de disque/processus.
- Corps métier limités aux objets JSON ; lancement du handler signalé après
  chargement ; garde d'arrêt avant création d'un enfant ; délais HTTP observés.

- Cadrage et spécification du service de qualification indépendant QLF-001.
- Application synthétique dans `qualification/` : douze handlers, manifeste,
  exécuteur de référence, Docker et commandes DEV.
- Qualification convertie en parcours E2E sur le conteneur réellement déployé,
  sans mock ni appel direct aux handlers depuis le client HTTP.
- Compteurs, caches et jobs nommés manipulés par HTTP ; calcul réel et reprise
  du worker ; propagation des erreurs de pairs réels.
- Authentification par marqueur public retirée ; secret de cellule requis pour
  le parcours positif du handler business ; secrets désormais configurés dans
  le seul Spark DEV via le contrat normal de la console. Aucun test ignoré.

## [Publié]

_Aucune version de production publiée._
