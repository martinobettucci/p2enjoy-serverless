# Changelog

## [Non publié]

### Garde du plafond d'instances

- Le helper refuse la baisse avant toute mutation tant que la console SPARK ne
  sait pas conditionner l'écriture à la version active. Le test E2E du refus est
  ajouté et passe deux groupes réels restore/EOF sur317 sources, namespace
  supprimé, budgets/services/fichiers conservés. Restitution indépendante et
  scénarios de panne restent ouverts dans SLS-099, sans modification de FORGE.

### Planifications en cours de qualification

- La facette retire sa pagination périmée pendant une lecture ou après erreur,
  en conservant la page demandée pour Réessayer. Le vrai401 a reproduit le défaut ;
  correctif et manuel sont à déployer puis requalifier sur une nouvelle image.

- Maximum individuel et réutilisation qualifiés sur325 sources : refus sans
  invocation sous HTTP non exclusif, minimum déjà prêt réutilisé puis deux
  instances/CID conservés à la frontière suivante. Quatre groupes, quatre
  handlers réussis, deux purges physiques ; aucun budget de cellule changé.

- Refus pendant un vidage de cache qualifié sur322 sources : vraie faute bornée,
  commande commit/pending, tir refused_unavailable sans invocation, restitution
  connue puis prochain tir sain avec donnée conservée et cache vide. Quatre
  groupes, trois handlers réussis, une purge et une garde terminées ; SLS-078 ouverte.

- Files pleines qualifiées sur319 sources par quatre groupes réels :16 attentes
  individuelles puis128 globales, deux tirs queue_full sans invocation,144
  déconnexions avant handler et quatre succès après libération. Neuf fonctions
  purgées ; mêmes services/fichiers et5982 artefacts conservés. SLS-078 reste ouverte.

- Moteur déployé en DEV : fenêtres de cinq minutes, réclamation et historique durables
  (migration 009), admission interne commune au moteur Docker, sans rejeu.
- Lectures Read, facette Planifications et manuel reconstruits ;
  premier checkpoint de22 groupes réels qualifié,21 captures inspectées.
  SLS-096 est corrigée ; SLS-078 reste `[~]` pour ses critères résiduels.
- Cycle des versions planifiées qualifié séparément par cinq groupes E2E réels :
  pilote, promotion, retour de hash, retrait, désactivation et suppression ;
  cinq handlers conservent leur code admis, trois fonctions purgées physiquement.
  SLS-078.3 est qualifiée sur la même image ; les autres critères restent ouverts.
- Grammaire numérique qualifiée par cinq groupes réels sur le client final :
  huit tirs de fenêtre, fusion et règle jour/semaine, douze refus d'expressions,
  prévisions dimanche0/7 et dates limites. SLS-078.2 est qualifiée ; premier
  passage et rejeu final conservent leurs rapports et leurs purges séparés.
- Coupures natives du contrôle et reprise qualifiées par cinq groupes réels :
  trois SIGKILL aux frontières SQL, trois fenêtres manquées sans invocation,
  absence de rejeu et trois prochains tirs réussis. Garde indépendante éprouvée
  après perte de l'observateur ; quatre gardes terminées, une fonction purgée.
  Même produit/image, référence et configuration conservées ; SLS-078 reste ouverte.
- Admission planifiée qualifiée par cinq groupes sur313 sources : deux refus CPU
  sans invocation, deux files exclusives, deadline après démarrage, recouvrement
  d'un handler315s et deux extinctions idle10s mesurées nativement. Sept handlers
  réussis, cinq fonctions purgées ; essais incomplets nettoyés et conservés séparément.
  Précontrôles RAM/instances, autres refus, rétention, UI et régression restent ouverts.
- RAM et changement de version en file qualifiés par cinq groupes sur316 sources :
  refus mémoire sans invocation, A rejetée après promotion B, allocation réelle8192Mio,
  retour A avec compteur conservé et aucun rejeu. Quatre handlers réussis, trois
  fonctions purgées. Plafond global d'instances et critères résiduels restent ouverts ;
  la correction de sa garde de qualification est suivie dans SLS-099.


### Méthode, parité Scaleway et planifications (documentation)

- `docs/.routine` et le rôle `factory_verifier` sont restaurés à l'identique de la
  méthode ; CloudWorker est adapté au SPARK DEV dans `CLAUDE_PROJECT.md`.
- Contrats persistés : moteur de planification (SLS-078), jobs de console avec
  gabarits (SLS-081), parité sourcée avec Scaleway Serverless (SLS-082 à 088),
  compatibilité du projet de référence (SLS-080), exploitation (SLS-079).
- Backlog réorganisé en source unique du travail : registre des unités ouvertes
  (nature, ordre, dépendances), critères communs, décisions en attente, unités au
  squelette uniforme avec critères cochables et tests exigés, restes de
  qualification extraits en unités SLS-089 à SLS-097. `docs/OBJECTIF_AUTONOME.md`
  porte un goal permanent qui repart du backlog, sans liste d'unités.
- Le manuel est reconstruit avec la console et décrit désormais le moteur de
  planification déployé en DEV ; sa concordance est vérifiée dans SLS-096.

### Réconciliation des demandes et de la livraison

- Vue explicite des fonctions encore absentes : favoris, masse, éditeur, client
  HTTP, journaux avancés et monitoring ; crons et compatibilité de référence
  incomplets. Les synthèses de versionnement, recherche et routes sont corrigées.
- Le README et le backlog exposent ces manques avant les checkpoints de tests.


### Préparation de la publication GitHub

- Le briefing privé docs/dev-spark.md devient un fichier local ignoré ; son
  retrait des263 commits et des instantanés internes est vérifié. Les lectures
  Git historiques sont remappées et les preuves datées conservées.


- Première tranche de régression008 des publications qualifiée :76 groupes,
 55 de composant et21 HTTPS, prérequis SSO distinct ; sept appels Docker et
  quatre fonctions purgées publiquement. Promotion Create explicite, pilote,
  rollback, attente native de deux admissions et déduplication sont recoupés.
  Services, fichiers officiels et5982 artefacts antérieurs restent identiques.
  [Preuve](docs/evidence/function-version-publication-regressions-dev-2026-11-09.json).

- Décisions de version sous perte réelle de réponse qualifiées :9 groupes,
  six coupures natives promotion CLI/archivage/suppression, garde indépendante,
  16 appels persistants et sept gardes terminées. Métier/audit atomiques,
  CLI unknown sans rejeu, dates des réimports conservées ; une fonction purgée.
  Deux bootstraps interrompus et purgés restent distincts. Même image produit.
  [Preuve](docs/evidence/function-version-state-transport-dev-2026-11-09.json).

- Première identité de code inconnue puis version connue qualifiée :17 groupes
  réels006→007→008, témoin API et variante de données préparée déclarés distincts.
  Marqueurs, droits, B stable/C pilote et23 appels recoupés ; deux purges publiques
  et une restitution indépendante avec instance/réseau/bail retirés. Originaux
  conservés, même image produit. Diagnostics du client durcis puis matrice rejouée.
  [Preuve](docs/evidence/function-version-unknown-first-dev-2026-11-09.json).

- Refus de corrélations de purge007 qualifiés sur l'image008 courante :42 groupes,
  40 rollbacks007 exacts et2 témoins migrés/rejoués dans le même conteneur. Les
  anciennes colonnes des16 tables, hashes/dates et registre deleted sont recoupés.
  Backups/WAL vides/SHM intacts,42 conteneurs/copies retirés,17 tables et services
  vivants inchangés, actifs nuls. L'essai arrêté avant copie reste distinct.
  [Preuve](docs/evidence/function-version-purge-correlation008-dev-2026-11-09.json).

- Reprise des purges historiques jusqu'à008 qualifiée :22 groupes réels, dont
  quatre fenêtres006/007→008 en volumes/artifacts, une restitution indépendante
  après perte du pilote et trois refus avant interruption. HashesNULL/connus,
  UUID/dates, registre deleted et anciens champs conservés ; quatre purges
  terminées et persistantes, cinquième installation temporaire retirée par garde.
  Les17 tables, le registre de stockage et5982 artefacts originaux sont identiques.
  Même image def45648/ID e661516b, nouveau démarrage attendu, cinq gardes inactives,
  actifs nuls. Les essais interrompus restent distincts ; SLS-074 reste en cours.
  [Preuve](docs/evidence/function-version-purge-migration008-dev-2026-11-09.json).

- Gardes de première transition008 déployées en DEV : refus de cible active
  incohérente, références orphelines et cache altéré, défaut reproduit avant
  correction. Dix groupes réels sur copies007 couvrent refus, témoin, verrou,
  contraintes et SIGKILL après écriture WAL avant commit, puis reprise du même
  conteneur. La bascule vers def45648 conserve les17 tables et le schéma déjà008.
  Douze groupes API et cinq CLI passent ensuite ;16 invocations réussies, un
  refus attendu et deux fonctions purgées physiquement. Le seul delta backend
  est008, web identique ; référence et fichiers officiels conservés. Les essais
  interrompus restent distincts, les pertes propres des gardes et autres pannes
  restent ouvertes dans SLS-074.
  [Preuve](docs/evidence/function-version-migration008-recovery-dev-2026-11-09.json).

- Reprise des paquets dédupliqués qualifiée en DEV : quatre groupes, cinq appels,
  commits200 sous EACCES avec réservation conservée puis nettoyage normal, et
  reprise après SIGKILL du contrôle et du helper par garde indépendante.
  Même ID/image/configuration, nouveau démarrage attendu, référence et fichiers
  officiels conservés ; données/cache1–5 et nouvelle déduplication confirmés.
  Une fonction purgée physiquement, deux gardes terminées, ressources actives et
  réservations nulles. 271 sources figées ; pertes SSH, faute propre de garde
  et coupure pendant unlink restent distinctes, SLS-074 en cours.
  [Preuve](docs/evidence/function-version-duplicate-recovery-dev-2026-11-09.json).

- Capacité des uploads qualifiée sur le contrôle DEV008 inchangé : quatre groupes
  réels, quatre admissions et cinquième429 avant réception, attente supérieure30s,
  un validateur Docker à la fois, convergence puis relance explicite du candidat
  refusé. Quatre appels conservent la cible promue et les compteurs données/cache1–4.
  Trois fonctions des essais purgées physiquement ;267 sources figées et mêmes
  images/services/configuration. Le premier essai incomplet et le replay
  intermédiaire ne gonflent pas les quatre groupes finaux. SLS-074 reste en cours.
  [Preuve](docs/evidence/function-version-upload-capacity-dev-2026-11-09.json).

- Conteneurs de validation nommés `serverless-code-validator-<uuid>` en DEV.
  L’image19cfe884642a reprend aussi les anciens p2-v après interruption réelle.
  Quatre groupes ciblés et36/12/5 régressions passent, soit57 sans échec/skip,
  avec cinq appels conservant données/cache, hash et configuration. Trois
  fonctions du replay sont physiquement purgées. Web/runtime/configuration
  conservés ; le premier arrêt Compose et son retrait restent séparés.
  [Preuve](docs/evidence/validator-names-dev-2026-11-09.json).

- Pagination réelle sur six domaines qualifiée en DEV : huit groupes de
  cycle/UI/CLI, trois prérequis de garde distincts, 14 invocations et sept
  captures inspectées. La CLI conserve la publication après changement réel
  entre pages et après révocation401. Quatre routes/A temporaires retirés
  indépendamment après SIGKILL du propriétaire ; deux fonctions purgées
  physiquement, 253 sources figées et mêmes services/images. L’essai DNS arrêté
  et son retrait explicite restent distincts du replay. SLS-066 reste ouverte.
  [Preuve](docs/evidence/invocation-pagination-dev-2026-11-09.json).

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
  Les valeurs citées de cellule sont lues par Compose DEV. Quatre groupes de
  reprise validation passent sous refus réel du socket et du canal isolé :
  second upload refusé avant validation, octets conservés, garde indépendante
  après SIGKILL et reprise normale, avec cinq invocations. Deux fonctions sont
  purgées et deux gardes du replay terminées. Les autres pannes et la régression
  complète restent ouvertes ; SLS-074 n’est pas clôturée.

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
  pour les autres fautes de source et de pilotes. La pagination sur six domaines
  est qualifiée par son complément distinct ci-dessus.
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

### Régression008 de la CLI et des publications interrompues

La [tranche CLI et reprise008](docs/evidence/function-version-cli-recovery-regressions-dev-2026-11-09.json)
passe 11 groupes réels sur 296 sources figées : sept déploiement/promotion CLI et
quatre plafonds/reprises. Le prérequis SSO réel reste distinct. Les 68 appels CLI
recoupent hash, UUID et présence du secret commun ; huit appels de reprise
comparent aussi marqueur, configuration et empreinte du secret. Vingt codes
réellement distincts remplissent le plafond ; un doublon est admis sans nouvelle
version ni changement de cible, un nouveau hash est refusé puis admis après retrait.

Deux SIGKILL du contrôle sont constatés nativement et par Docker137, en réception
partielle puis avec validateur Docker vivant lié au candidat, à son installation
et à l'image runtime configurée. La seconde perte du helper déclenche réellement
la restitution indépendante. Les candidats deviennent failed/control_interrupted,
sans réservation, configuration temporaire, code, validateur ou canal restant.
La cible stable, les premiers marqueurs et la configuration privée sont conservés ;
les uploads suivants restent pilotes jusqu'à promotion explicite.

Les 22 fonctions sont purgées publiquement dans deux namespaces ; 76 invocations
réussies uniques, dont 27 épinglées, sont recoupées en base. Helpers, timers et
services des deux gardes sont terminés. Les 5 982 artefacts antérieurs et fichiers
officiels restent identiques ; contrôle de même CID/image, démarrage attendu
2026-11-09T22:00:26.747122276Z, référence inchangée. Aucun build produit, changement
d'UI/manuel ni nouvelle preuve visuelle. Les autres clients, les pannes propres
du banc et la régression complète008 restent dans SLS-074, toujours [~].

### Régression008 des invocations et du stockage

La [tranche invocation/stockage008](docs/evidence/function-version-invocation-storage-regressions-dev-2026-11-10.json)
passe 46 groupes réels sur 298 sources figées : 15 mutations de stockage et
31 invocations publiques. Le prérequis SSO reste distinct. Sept appels Echo
recoupent A pilote/promue, doublon malgré quota modifié, B pilote/promue et
rollback A. Quota7 Mio, reçu de stockage et fichiers données/cache sont conservés.
La confirmation indisponible conserve son vrai503 et sa décision acquise.

Pendant un handler A observé actif, publier B ne déplace pas la cible. Après
promotion B, retirer A empêche ses nouvelles admissions tout en laissant finir
son instantané ; le nettoyage reste en attente puis efface A après libération.
Les31 groupes conservent ACL, HTTP/Lambda, politiques origine/IP, files, minima,
quotas, concurrence, budgets réels, contention SQLite, arrêts et réceptions bornées.
Le plafond d'instances est appliqué puis restitué par la console du seul SPARK.

La collecte recoupe 85 handlers succeeded, dont78 publics et7 Echo ; deux réponses
métier non2xx et un succès après déconnexion restent classés selon l'état durable.
Les107 réponses publiques comprennent16 UUID avant réservation. Le vrai502 du
proxy sans UUID est lié par l'identité locale de sa connexion au témoin natif
running puis au même appel interrupted ; son statut durable503 reste distinct.

Les18 fonctions finales sont purgées par les API. L'essai initial avait passé
46 groupes mais échoué à la collecte de ce502 ; il reste séparé et ne s'ajoute
pas au total. Ses18 fonctions sont également purgées : les36 sont recoupées
physiquement dans quatre namespaces. Les5 982 artefacts antérieurs, fichiers
officiels, images, backend/web et référence sont conservés. Les budgets consommés
sont rétablis à32 instances,1 CPU et8 192 Mio, sans garde active. La recréation
attendue du contrôle change son CID et son démarrage, pas son image.

Les sources exécutables du replay restent celles livrées ; seules les deux
pages de contrat reçoivent les résultats dans l'index de sources. Les opérateurs
historiques conservent leurs limites. Aucun nouveau parcours visuel ni changement
produit/UI/manuel ; console, historique et régression complète008 restent ouverts.
SLS-074 conserve [~].
