# P2Enjoy Serverless

**La plateforme demandée n'est pas encore entièrement livrée.** Favoris,
actions en masse, éditeur de code intégré, client HTTP par fonction, journaux
avancés et monitoring historique restent à implémenter. Le moteur des crons du manifeste est
déployé et sa qualification DEV est en cours ; les jobs de console, la compatibilité
complète du projet de référence, la parité avec Scaleway Serverless
([matrice](docs/SCALEWAY_PARITY.md)) et un guide d'exploitation rejoué restent à
livrer. Le moteur, la gestion, les versions et les preuves ciblées ne clôturent pas
ces demandes. Voir [l'état réel de livraison](docs/DEMANDES_ET_LIVRAISON.md) et le
[registre des unités ouvertes](docs/BACKLOG.md#registre-des-unités-ouvertes), qui
porte l'ordre de reprise, avant les checkpoints techniques détaillés ci-dessous.

Le [premier checkpoint de planification](docs/evidence/schedules-checkpoint-dev-2026-11-10.json)
qualifie22 groupes réels :6 ciblés,8 du manuel,8 publics. La facette Planifications
est disponible ; le manuel servi correspond à16 chapitres et56 paragraphes.
Un [complément de cinq groupes](docs/evidence/schedule-versions-dev-2026-11-10.json)
qualifie les cycles de promotion/retour de hash, le retrait des crons et l'arrêt
après désactivation ou suppression, en conservant les appels admis.
Les critères résiduels de SLS-078 restent ouverts.
SLS-096 (concordance du manuel) est corrigée et vérifiée.
La [grammaire numérique des crons](docs/evidence/schedule-calendar-dev-2026-11-10.json)
passe aussi cinq groupes distincts : fusion, règle jour/semaine, refus et
prévisions calendaires ; SLS-078.2 est qualifiée.
Les [coupures et reprises](docs/evidence/schedule-recovery-dev-2026-11-10.json)
passent cinq groupes distincts : garde indépendante, trois SIGKILL du contrôle,
fenêtres manquées sans rattrapage, absence de rejeu et trois tirs suivants réussis.
Une fonction est purgée physiquement, quatre gardes terminées.
L'[admission planifiée](docs/evidence/schedule-admission-dev-2026-11-10.json)
passe cinq groupes distincts : refus CPU sans invocation, files exclusives,
deadline après démarrage, recouvrement315s et extinction mesurée. Sept handlers
réussis et cinq fonctions purgées ; les deux essais antérieurs restent séparés.
La [suite RAM/version](docs/evidence/schedule-memory-version-dev-2026-11-10.json)
qualifie cinq groupes supplémentaires : refus mémoire sans invocation, changement
de hash pendant la file, vraie allocation8192Mio, libération puis prochains tirs
sans rejeu. Quatre handlers réussis et trois fonctions purgées. Plafond global
d'instances, rétention et régression complète restent
à éprouver dans SLS-078 ; la garde du plafond est suivie dans SLS-099.
La qualification du plafond sera isolée dans un déploiement temporaire de la
même image, configuré à deux instances dès le démarrage, sans modifier le plafond
officiel du SPARK : [contrat](docs/INSTANCE_LIMIT_RESTORATION.md). La demande
antérieure d’évolution de FORGE est retirée ; cette nouvelle preuve reste à réaliser.
Les [files pleines des tirs](docs/evidence/schedule-queues-dev-2026-11-10.json)
passent quatre groupes sur319 sources :16 réceptions individuelles,128 globales,
deux refus sans invocation puis deux succès HTTP et deux planifiés après libération.
Les144 réceptions déconnectées et les neuf purges physiques sont recoupées.
Le [refus sous vidage de cache](docs/evidence/schedule-unavailable-dev-2026-11-10.json)
passe quatre groupes sur322 sources : commande réellement pending, tir refusé
sans invocation, même reçu terminé après restitution puis prochain tir sain.
Trois handlers conservent la donnée ; fonction purgée et garde terminée.
Le [maximum individuel et la réutilisation](docs/evidence/schedule-instance-reuse-dev-2026-11-10.json)
passent quatre groupes sur325 sources : refus sous HTTP non exclusif avec budgets
globaux libres, minimum préchauffé puis deux instances/CID réutilisés à la frontière
suivante. Quatre handlers réussis et deux purges physiques ; SLS-078 reste ouverte.
La [console des planifications](docs/evidence/schedule-console-dev-2026-11-10.json)
passe19 groupes sur326 sources : trois ciblés, huit du manuel et huit publics
rejoués. Six vrais tirs22:10UTC donnent les pages5+1 ; vide, nom63, clavier,
mobile et vrai401→Réessayer200 passent après correction de la pagination périmée.
Nouvelle imagec59b8616 avec manuel conforme16 chapitres/56 paragraphes ;31 captures
recoupées (17 inspections,14 références SHA), deux purges physiques. SLS-078.6
est qualifiée ; rétention, plafond global, adaptateur.7 et régression restent ouverts.


Plateforme de fonctions conteneurisées, destinée à être déployée dans un SPARK
de FORGE. La console et le plan de contrôle sont en cours de qualification
dans **[control/](control/README.md)** et **[web/](web/README.md)**. Une première
application indépendante de qualification et son exécuteur de référence DEV
sont disponibles dans **[qualification/](qualification/README.md)**, avec
handlers, manifeste `serverless.yml`, Docker, tests et commandes d'exploitation.
L'[adaptateur](adapter/README.md) prépare les plans, archives ZIP et publications
HTTPS via sa commande `deploy`, dont les sept groupes authentifiés passent. La
configuration commune du manifeste est conservée dans le service, avec uniquement
les surcharges dans les fonctions. Cette évolution et ses régressions passent
191 groupes en série sur DEV, avec 21 captures relues :
[preuve de configuration commune](docs/evidence/service-configuration-dev-2026-11-08.json).
Son [complément](docs/evidence/service-configuration-transport-dev-2026-11-08.json)
ajoute cinq groupes sous vraies coupures puis treize groupes rejoués : issue
inconnue sans rejeu, état durable recoupé et relances explicites réussies. La
validation Node dans Docker est disponible dans [runtime/](runtime/README.md),
avec 36 scénarios réels réussis. Les routes de publication, d'historique et de
rollback sont déployées en DEV ; onze groupes authentifiés passent :
[preuve de publication](docs/evidence/deployment-authenticated-dev-2026-11-06.json).
Les plafonds de candidats/révisions et les reprises après SIGKILL pendant
réception/validation passent quatre groupes supplémentaires :
[preuve de reprise](docs/evidence/publication-recovery-dev-2026-11-06.json).
Expiration, budget et interruption pendant nettoyage restent à éprouver.
Le pilote Docker d’instances chaudes passe 31 contrôles d’invocation et
11 de cycle de vie : [preuve DEV](docs/evidence/instances-dev-2026-11-06.json).
Le raccordement des instances aux baux de volumes passe quatorze groupes réels :
[preuve](docs/evidence/managed-storage-dev-2026-11-06.json). La passerelle et les admissions sont déployées sur DEV ; les 31 groupes HTTPS
et 221 groupes de régression passent dans la [preuve du moteur](docs/evidence/execution-dev-2026-11-06.json). Les préparations de quotas et leurs décisions
durables ont fait l’objet d’une première campagne de dix groupes réels,
avec 37 groupes de régression :
[preuve](docs/evidence/storage-preparations-dev-2026-11-06.json). Les créations, changements de quotas, suppressions et publications sont
raccordés à une décision durable du contrôle : [contrat](docs/ADMISSION.md),
[preuve des mutations publiques](docs/evidence/function-storage-dev-2026-11-06.json). L'extracteur ZIP serveur dans
[control/](control/README.md) passe 112 contrôles réels, dont les limites,
les erreurs de disque et les douze archives chargées ensuite par Node.
Le composant de [stockage à quota](storage/README.md)
est disponible et qualifié sur le SPARK DEV : 31 contrôles réels réussis,
dont saturation, concurrence et reprise après interruption. Son agent local
de volumes est installé en DEV ; les baux, budgets et reprises font l’objet
de campagnes réelles de composant. Leur raccordement aux admissions publiques
est désormais déployé et éprouvé par la campagne publique.

## Objectif

Exploiter et déployer les projets P2Enjoy avec une compatibilité Lambda ciblée,
sans rechercher une reproduction complète des API AWS. Docker constitue le
socle d'exécution. La console gère namespaces, fonctions, allocations, mémoire,
stockage permanent par identifiant de fonction et durées du cycle d’exécution.
Elle donne accès au code et aux révisions, aux instances et aux invocations,
ainsi qu’au manuel d’usage.

Les évolutions demandées pour la console comprennent catalogue et recherche,
favoris, opérations en masse, édition du code et du handler, client HTTP par
fonction, journaux recherchables et monitoring historique. Leur
[contrat de parcours](docs/CONSOLE_USABILITY.md) et les unités SLS-067 à SLS-073
du backlog définissent la livraison. Le catalogue SLS-067 est déployé et qualifié
en DEV : recherche globale, filtres paginés, tri et retour à la liste depuis les
six facettes. Sa [preuve](docs/evidence/function-catalogue-dev-2026-11-08.json)
réunit 37 campagnes uniques / 489 groupes réels, six prérequis distincts et
98 captures inspectées. Elle distingue 447 groupes conservés aux clients
inchangés et 42 réexécutés, avec deux époques de sources et les mêmes images.
Les 91 fonctions suivies sont purgées dans 23 namespaces ; le manuel servi
correspond à ses 15 chapitres et 46 paragraphes. Les autres extensions restent
à implémenter.

Le [versionnement par hash](docs/FUNCTION_VERSIONS.md), suivi dans SLS-074,
complète l’historique et le rollback existants : déduplication des uploads
identiques, invocation d’un hash précis, archivage de version et publication
pour un pilote sans déplacer la cible par défaut. Son [calcul canonique](docs/FUNCTION_CODE_HASH.md)
est implémenté et qualifié : sept groupes ciblés, 45 de régression et neuf
invocations Docker. Les sept groupes sont rejoués après nommage des clients ;
les 45 régressions restent dans leur époque distincte, sur les mêmes sources
produit et images. Le [registre persistant](docs/FUNCTION_VERSION_REGISTRY.md) est maintenant
implémenté et qualifié : migration 007, alias historiques conservés, lecture
Read groupée et hash complet copiable dans la console. Sa
[preuve](docs/evidence/function-version-registry-dev-2026-11-09.json) passe
359 groupes sur deux époques de clients, avec la même image applicative :
46 ciblés/historiques et 313 de régression. Les 69 captures sont recoupées,
dont 47 nouvelles inspections et 22 références identiques par SHA. Le manuel
compilé comporte 15 chapitres et 47 paragraphes. Le checkpoint antérieur au repos
conserve ses 328 groupes dans son époque distincte ; ils ne s’ajoutent pas comme
groupes uniques au total 359. Le contrôle008 est maintenant déployé pour qualification : déduplication,
promotion séparée, sélection/pools par hash et gestion d’état sont implémentés.
Le [checkpoint ciblé008](docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json)
réunit71 groupes :2 migration/reprise,12 API,5 CLI authentifiés depuis le poste,
6 UI,8 manuel et38 packaging/refus dans les images CLI. Les28 nouvelles captures
sont inspectées ; le manuel comporte15 chapitres et52 paragraphes. Les dix
fonctions des campagnes et essais interrompus sont purgées. Le
[complément CLI Docker](docs/evidence/function-version-cli-images-dev-2026-11-09.json)
passe ensuite les mêmes cinq groupes dans chacune des deux images : vingt
commandes et douze invocations réelles, deux nouvelles fonctions purgées. Il
complète la matrice d’environnements sans ajouter dix comportements nouveaux.
Le [nettoyage avec attente](docs/evidence/function-version-validation-recovery-dev-2026-11-09.json)
passe quatre groupes supplémentaires ciblés : refus socket/canal, garde de
validation et reprise indépendante après SIGKILL, avec cinq invocations.
Les autres pannes et la régression complète restent ouvertes.
La preuve359 et ses captures décrivent le checkpoint007.

Le [complément de capacité](docs/evidence/function-version-upload-capacity-dev-2026-11-09.json)
passe quatre groupes sur267 sources : quatre uploads réellement admis, cinquième429,
attente supérieure30s, validations Docker sérialisées, convergence et relance
explicite. Quatre appels conservent stable/pilote et compteurs données/cache1–4.
Les trois fonctions des essais sont physiquement purgées. Image19cfe884,
configuration officielle et services restent identiques ; SLS-074 reste en cours.

La [reprise des doublons](docs/evidence/function-version-duplicate-recovery-dev-2026-11-09.json)
ajoute quatre groupes réels sur 271 sources : publication200 sous EACCES,
réservation conservée, nettoyage par maintenance, puis SIGKILL après commit et
restitution/redémarrage indépendants du même contrôle. Cinq appels conservent
la version et les compteurs données/cache1–5. La fonction est purgée physiquement,
les deux gardes sont terminées et les ressources actives sont libérées. L'image
reste19cfe884 ; les autres pannes et la campagne complète restent dans SLS-074.

La [reprise de migration008](docs/evidence/function-version-migration008-recovery-dev-2026-11-09.json)
complète le premier checkpoint : dix groupes sur copies privées de la vraie007,
dont six refus transactionnels, témoin, verrou/reprise, contraintes et SIGKILL
après écriture WAL avant commit. La relance du même conteneur conserve les
données et2882/4418 backfills. L'image corrigée def45648f9e7 est ensuite déployée
sur DEV avec sauvegarde native ; les17 tables et le schéma déjà008 sont identiques
après remplacement. Les12 groupes API et5 CLI passent, avec16 invocations
réussies et un refus attendu. Deux fonctions sont purgées physiquement. Les
gardes nominales sont désarmées ; leurs pannes propres et la régression complète
restent ouvertes dans SLS-074. Le [complément de purges historiques008](docs/evidence/function-version-purge-migration008-dev-2026-11-09.json)
passe22 groupes réels : quatre fenêtres006/007→008 en volumes/artifacts, une
restitution indépendante après perte du pilote et trois refus avant interruption.
HashesNULL/connus, anciens champs, registre deleted, reçus et octets sont recoupés.
Les quatre purges normales terminent ; la cinquième installation temporaire est
retirée par restitution gardée. Originaux,17 tables et5982 artefacts sont conservés.
Même image et même conteneur original, nouveau démarrage attendu ; cinq gardes
inactives et ressources actives nulles. Les [corrélations007](docs/evidence/function-version-purge-correlation008-dev-2026-11-09.json)
passent ensuite42 groupes de composant sur283 sources :40 refus transactionnels
et2 témoins avec relance du même conteneur. Les backups/sidecars,17 tables et
services vivants restent identiques, copies retirées. Le complément de première identité inconnue est qualifié ci-dessous ;
les autres pannes restent à éprouver.

La [première identité inconnue](docs/evidence/function-version-unknown-first-dev-2026-11-09.json) passe17 groupes sur286 sources :
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

Les [réponses perdues des décisions de version](docs/evidence/function-version-state-transport-dev-2026-11-09.json) passent9 groupes
sur290 sources figées : promotion par la vraie CLI, archivage et suppression
avec remplacement, chacun avant traitement puis après décision avant réponse.
Les six SIGKILL sont constatés nativement et par Docker137 ; même conteneur/image
redémarrés, référence et fichiers officiels conservés. La CLI retourne unknown
avec exactement deux connexions HTTPS, sans rejeu. Avant traitement, métier
inchangé puis relance explicite ; après commit, pointeur/état/ETag/audit persistés
ensemble sans renvoi. Le delete est observé après sa tentative de nettoyage,
sans prétendre une interruption avant effacement physique.

Seize appels réussis retrouvent les handlers A/B, configuration, secret par
empreinte et compteurs données/cache1–16 après les reprises. Les réimports B
gardent hash et date initiale ; les premiers marqueurs restent immuables.
Une perte SIGKILL de l'observateur éprouve la garde indépendante sans mutation.
Les sept gardes et helpers sont terminés ; les six arrêts ont leurs reçus root.
Une fonction est purgée publiquement, volumes/artefacts et ressources actives
absents. Les deux bootstraps arrêtés avant garde restent archivés avec leurs
purges physiques, zéro groupe ajouté. Aucun produit/UI/manuel ni configuration
modifié ; la lecture sous-propriétaire recoupe les31 backends et le web.
SLS-074 reste[~] pour les autres interruptions et la régression complète008.

La [première tranche de régression008](docs/evidence/function-version-publication-regressions-dev-2026-11-09.json) passe76 groupes sur292
sources figées :55 contrôles du vrai composant Docker et21 groupes HTTPS des
publications complètes/code seul. Le prérequis SSO réel reste distinct. Les huit
migrations, intégrité, verrou et refus de configuration sont conservés ; les11
et10 groupes de publication gardent droits, propriété, conflits, révocation,
import réel, abandon, course et pagination.

Upload et promotion sont distingués, y compris première promotion Create. Une
observation native recoupe deux candidats validating/réservés et le seul validateur
vivant du premier ; le doublon réutilise le hash et la révision canonique sans
changer la cible. Rollback et pilote sont réellement invoqués. Sept appels
recoupés en base vérifient hashes demandés/résolus, handlers et configuration.
Les cinq appels de code seul vérifient l’empreinte du secret ; les deux appels
de publication complète contrôlent sa présence puis son absence. Le compteur
POST reste1 lors des GET après promotion.

Quatre fonctions sont purgées par l'API publique, code/volumes/réservations absents
et parents supprimés. Les empreintes avant purge ne prétendent pas représenter
des archives encore conservées. Les5982 artefacts antérieurs et les services,
ID/images/démarrages, fichiers officiels et backend/web embarqués restent identiques.
Les anciens rapports restent préservés par SHA. Aucun build produit ni nouveau
parcours visuel ; les autres clients et la régression complète restent dans
SLS-074, toujours[~].

Pour SLS-074, un upload prépare une version disponible par hash ; seule une
promotion explicite change la version appelée sans tag, selon le choix confirmé.

Le stockage propose des modes configurables par fonction pour les données
métier et le cache reconstructible. Le [contrat de plateforme](docs/PLATFORM.md)
définit concurrence, rétention, quotas et suppression ; son implémentation suit
les unités du [backlog](docs/BACKLOG.md).

Le premier projet de référence est `johndalia/jd_serverless`, actuellement
déployé sur Scaleway. La décision confirmée est de conserver ses handlers et
de réutiliser `serverless.yml` avec un adaptateur P2Enjoy.

Le [catalogue des adresses d’appel](docs/INVOCATION_URLS.md), SLS-066, est déployé
en DEV : facette de fonction, copie d’URL/curl et résultat CLI issus des routes
du SPARK. Le [checkpoint](docs/evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
passe 88 groupes sur le domaine courant. La qualification multi-domaines et
les preuves résiduelles restent ouvertes ; SLS-066 n’est pas clôturée. La
[preuve à deux domaines](docs/evidence/invocation-domains-dev-2026-11-08.json)
ajoute huit groupes API/CLI et six UI sur `serverless.lelabs.tech` et
`functions.lelabs.tech`, désormais tous deux vérifiés en HTTPS vers 18090.
Les quatre fonctions de ces campagnes sont purgées dans deux namespaces ;
sept nouvelles captures sont inspectées. Les [cinq cycles de routes](docs/evidence/invocation-route-cycles-dev-2026-11-09.json)
qualifient ensuite le retrait/rétablissement de l’alias, les détours vers 18091,
la restauration indépendante après SIGKILL du pilote et le catalogue API local
vide. Sept appels exécutent Docker depuis les URL émises ; les deux routes sont
rétablies à 18090 TLS et la fonction de campagne est purgée. La [pagination réelle sur six domaines](docs/evidence/invocation-pagination-dev-2026-11-09.json)
passe huit groupes de cycle/UI/CLI et trois prérequis de garde distincts, avec
14 invocations, sept captures inspectées et deux fonctions purgées. Les quatre
routes/A temporaires sont retirés par garde indépendante après SIGKILL réel
du propriétaire ; les deux domaines permanents restent18090TLS. Les autres
fautes de source restent à éprouver. La
[garde de permissions](docs/evidence/invocation-source-guard-dev-2026-11-09.json)
passe trois groupes réels préalables : EACCES, release, perte ou suspension du
helper et restitution du même fichier. Le [refus API](docs/evidence/invocation-source-api-dev-2026-11-09.json)
passe ensuite quatre groupes : diagnostic borné, droits vérifiés avant lecture,
invocations réelles pendant EACCES et catalogue restitué ; une fonction purgée.
Le [parcours UI du refus](docs/evidence/invocation-source-ui-dev-2026-11-09.json)
passe trois groupes : alerte utile desktop/mobile, résultats précédents retirés,
restitution puis invocation d’une URL copiée ; une fonction purgée et garde finie.
La [barrière native](docs/evidence/invocation-request-pause-dev-2026-11-09.json)
passe deux groupes supplémentaires : libération du vrai GET HTTPS et reprise
après SIGKILL du traceur, sans redémarrage du contrôle. Le [parcours UI vide](docs/evidence/invocation-empty-ui-dev-2026-11-09.json)
passe ensuite trois groupes : vrai GET navigateur conservé pendant changement
des routes, rendus desktop/mobile, restauration puis invocation d’une URL copiée.
La fonction est purgée et les deux gardes sont finies. L’[entrée SSO par l’alias](docs/evidence/invocation-alias-entry-dev-2026-11-09.json)
passe trois groupes supplémentaires : redirections canoniques et connexions/
déconnexions réelles desktop/mobile, six captures inspectées et sessions propres
fermées. Les deux essais de mesure interrompus restent séparés du replay. La
[régression complète](docs/evidence/invocation-urls-regressions-dev-2026-11-08.json)
passe 35 campagnes en série et 467 groupes, sans échec ni test ignoré :
186 sources recoupées avant/après chaque phase, 79 captures fraîches recoupées
(61 observations et 18 identités SHA avec une référence inspectée) et 32 fonctions
suivies purgées dans dix namespaces. Les six prérequis sont distincts du total.
Le [complément de transport](docs/evidence/invocation-url-transport-dev-2026-11-08.json)
passe ensuite trois nouveaux groupes et treize de régression : une perte du GET
des adresses après publication conserve le succès et les UUID, sans rejeu CLI.
Le [complément de révocation](docs/evidence/invocation-url-refusal-dev-2026-11-08.json)
qualifie ensuite le vrai 401 après publication : succès/UUID conservés et six
connexions sans rejeu. Son replay passe 17 groupes avec 188 sources recoupées ;
le premier essai incomplet reste conservé séparément avec son nettoyage.

## Accès confirmé

- La console d'administration utilise le SSO du domaine avec le rôle `admin`.
- Les administrateurs créent des jetons propres à la plateforme, limités à un
  service, avec des droits CRUD.
- `Create` et `Update` permettent la création ou modification des fonctions,
  du code, des variables, des secrets et des configurations, suivant le droit.
- `Delete` supprime une fonction en archivant ses données persistantes ; la
  purge des archives constitue une opération administrateur distincte.
- `Read` autorise l'invocation. Une invocation peut avoir des effets métier en
  écriture ; ce droit ne signifie pas que le handler est sans effet de bord.
- L'authentification métier reste indépendante et peut être implémentée dans
  chaque fonction. John Dalia devra transmettre le jeton de la plateforme en
  plus de son authentification existante.
- Chaque service doit permettre de limiter les appels aux fonctions à des
  origines web autorisées (par exemple `https://app.johndalia.com`) et/ou à
  des adresses IP autorisées, en complément du jeton. L'origine web n'est pas
  une preuve d'identité pour les clients hors navigateur. Le détail proposé
  de la combinaison des règles est consigné dans le journal.

Le contrat d'intégration fourni est [docs/sso.md](docs/sso.md).
Les décisions, preuves de lecture et questions sont dans
[docs/JOURNAL.md](docs/JOURNAL.md).

## Méthode

Les noms décrivent obligatoirement la fonction réelle et l’usage de chaque
élément. La [règle de nommage](CLAUDE_PROJECT.md#nommage-obligatoire) s’applique
au code, aux ressources déployées et aux libellés de la console.

Référence : [P2Enjoy Software Factory Base](https://github.com/P2Enjoy/software-factory-base).
Le module de formation, ses supports et ses exports de séminaire sont exclus.
Le socle est importé ici : `CLAUDE.md`, `AGENTS.md`, rôles `.codex/` et
`.claude/`, `.githooks/`, `scripts/git-hooks/`, `tests/git-hooks/`, contrats
d'automatisation, de design et de worker. Provenance et adaptations :
[docs/METHODE.md](docs/METHODE.md). Le worker planifié est inactif.
Validation de l'outillage : `bash tests/git-hooks/test-hooks` utilise de vrais
dépôts temporaires et un remote Git local, sans réseau ni mock.

## Exécution et validation

La console DEV est accessible sur [serverless.lelabs.tech](https://serverless.lelabs.tech).
Le conteneur `serverless-api` sert cette console et l’API. Le conteneur
`serverless-runtime-reference` exécute les handlers de qualification sur la
boucle locale ; ses clients de test sont éphémères. Les
[noms d’exploitation](docs/DEPLOYMENT_NAMES.md) précisent leurs rôles.
La gestion authentifiée passe 19 groupes API et 11 parcours de console,
avec persistance après redémarrage, droits CRUD, secrets et rendu mobile.
Les cycles de rôles, de renouvellement et de clés SSO restent à qualifier.
Les commandes du contrôle figurent dans [control/README.md](control/README.md).
Les clients de preuve de plateforme vivent dans [e2e/](e2e/README.md).
Les facettes **Instances** et **Invocations** affichent allocations, mesures Docker,
états et journaux expurgés dans la fiche de fonction. Leur [preuve de console](docs/evidence/console-execution-dev-2026-11-07.json)
passe 40 groupes réels, avec 25 captures relues.
La [preuve de gestion](docs/evidence/control-management-dev-2026-11-06.json)
recoupe les sources déployées, les campagnes, les ressources web servies et
les sept captures relues. Le [manuel](docs/manual.md) décrit la console et se
consulte depuis **Manuel d’usage** dans sa navigation, à
[serverless.lelabs.tech/console/manual](https://serverless.lelabs.tech/console/manual).
Ce même fichier est compilé avec chaque version de la console ; le contrat local
impose sa mise à jour à chaque évolution fonctionnelle. La [preuve du manuel](docs/evidence/manual-console-dev-2026-11-07.json)
passe 48 groupes réels avec 33 captures relues.
La facette **Code et révisions** permet maintenant de publier une archive ZIP,
suivre ou abandonner une préparation, activer et supprimer des révisions.
Le manuel comprend ces nouveaux parcours. Leur [preuve finale](docs/evidence/publication-console-dev-2026-11-07.json)
passe 18 campagnes en série, 312 groupes réels, sans échec ni test ignoré,
avec 54 captures inspectées. Les sources, l’image servie, les nettoyages et les
notes SPARK sont recoupés. Les commandes publiques de purge/cache sont déployées
et font l’objet de la qualification complète SLS-065 décrite ci-dessous.
Les crons et les preuves résiduelles de plateforme restent suivis au backlog.

**Il est interdit de lancer l'application avec un profil PREPROD ou PROD,
quelles que soient les circonstances.**

Prérequis pour le banc : Docker Engine avec Compose et Bash. Aucun runtime
Node ni service externe requis sur l'hôte. Depuis ce dépôt, exécuter chaque
commande après la fin de la précédente :

```sh
cd qualification
bash dev.sh build
bash dev.sh up
bash dev.sh check
bash dev.sh test
bash dev.sh probe
bash dev.sh recreate-proof
bash dev.sh status
```

Arrêt : `bash dev.sh stop`. Les volumes sont conservés. Les tests utilisent des
ressources nommées créées puis supprimées par leurs vraies API. **Aucun mock :
toute fonctionnalité testée est vérifiée E2E contre le code réellement déployé.**
Un conteneur client distinct appelle la pile en fonctionnement. Les pannes
de configuration, de stockage et de processus sont exercées dans de vrais
conteneurs isolés de la même image. Un prérequis absent fait échouer la
qualification ; aucun test n'est ignoré.
Sur le SPARK autorisé, chaque commande prend `--spark` avant l'action et lit
les deux fichiers de configuration de la cellule. Aucun `.env` n'est utilisé.

Le code source est **ici dans `qualification/`**, puis copié pour exécution dans
`/srv/p2enjoy-serverless/qualification` du seul SPARK DEV autorisé. Voir
[le guide de qualification](qualification/README.md) et
[le déploiement DEV](docs/QUALIFICATION_DEV.md). L'accès HTTP est local au SPARK,
sans route publique. La FORGE sert uniquement de rebond SSH ; aucune opération
d'administration n'y est autorisée.

## Structure

```text
adapter/
  manifest.py             Lecture sûre du manifeste et correspondances
  archive.py              Packaging ZIP et inventaire SHA256
  deploy.py               Publication HTTPS en série et résultats partiels
  dev.sh                  Construction et qualification CLI dans le SPARK
control/
  app/                    API, SSO, sessions, objets et droits
  app/artifacts.py         Extraction ZIP bornée et publication readonly
  app/deployments.py       Candidats, validation Docker et publication SQLite
  app/execution.py         Admission, réservations, instances et reprise
  app/invocation_routes.py Passerelle HTTP et observations autorisées
  artifacts-dev.sh         Construction et qualification de l'extracteur
  migrations/             Schéma SQLite versionné
  compose.spark.yml       Contrôle DEV sur le port 18090
web/
  src/                    Console React, formulaires et navigation
e2e/
  artifacts.py            Preuves ZIP, disque, courses et parcours des 12 fonctions
  public.py               HTTPS public et refus OIDC réels
  login-ui.mjs            Accueil, clavier, responsive et SSO
  control-admin.mjs        Campagne API authentifiée
  control-ui.mjs           Parcours de gestion dans le navigateur
  deployments.mjs          Publication et courses par les véritables API
  adapter-deploy.mjs       Parcours de la commande deploy avec jetons réels
storage/
  agent.py                Service local, baux et registre durable des volumes
  agent_discard.py        Effacements corrélés, reçus et reprise hors verrou
  install-dev.py          Installation du paquet protégé et maintenance
  agent-proof.py          Campagnes réelles de cycle de vie et de limites
  main.go                 Proxy de quota FUSE sur les fichiers natifs
  client.py               Client de preuve dans un conteneur Docker isolé
  prove.py                Campagne de montage, quota, crash et reprise
runtime/
  loader.mjs              Chargeur commun Node : CommonJS et ESM
  invoke-supervisor.mjs   Instances chaudes avec enfant neuf par invocation
  validate-supervisor.mjs Supervision d'import et protocole Unix privé
  dev.sh                  Construction et qualification sur le SPARK
qualification/
  serverless.yml          Manifeste du service synthétique
  serverless.platform.yml Manifeste de packaging pour la plateforme
  src/handlers.cjs         Les douze fonctions originales
  runner/                 Exécuteur de référence, sans SSO ni ACL plateforme
  tests/                  Client E2E HTTP et preuve de recréation Docker
  compose.dev.yml          Pile DEV, ports uniquement sur boucle locale
  compose.spark.yml        Injection des deux fichiers de cellule
  dev.sh                  Commandes reproductibles
docs/
  DAT.md                  Architecture et limites des preuves
  BACKLOG.md              Unités de travail
  JOURNAL.md              Décisions et constats
  dev-spark.md             Dossier du SPARK fourni par le responsable
  sso.md                   Contrat d'intégration SSO
```

Les effacements corrélés de l’agent sont qualifiés dans la preuve historique
[SLS-064](docs/evidence/storage-discard-dev-2026-11-07.json), avec 106 groupes.
Le catalogue d’archives, les commandes de cache/purge, leur console et leur
manuel passent la [preuve complète SLS-065](docs/evidence/storage-console-dev-2026-11-08.json) :
29 campagnes en série, 397 groupes réussis, zéro échec et zéro test ignoré.
Un complément distinct rejoue neuf groupes API avec quatorze corps invalides
de purge, une version périmée et des relevés natifs sans mutation.

Les 24 fonctions du replay et les quatre du complément sont purgées dans huit
namespaces ; les deux restaurations historiques restent distinctes. La preuve
recoupe 173 sources avant/après chaque phase, les 25 fichiers du contrôle
embarqué et 72 captures : 66 JPEG et six PNG de connexion. Les 17 images de
connexion/manuel régénérées sont identiques aux images déjà inspectées ; les
55 autres sont inspectées sur ce replay. Le manuel servi correspond à ses
treize chapitres et 39 paragraphes sources.

`python3 -B e2e/execution-suite.py --scope storage-console` prépare les sessions
SSO par stdin privée, puis renouvelle une paire juste avant le scénario qui
ferme sa session de purge. Le build historique et les deux préparations SSO
restent des prérequis sans groupes artificiels. L’[arrêt initial](docs/evidence/storage-console-incomplete-dev-2026-11-08.json)
après 388 groupes est conservé séparément ; le replay complet termine à zéro.
Les trois notes SPARK sont maintenues dans `qualification/spark-notes/` et leur
proposition finale est recoupée ; leur adoption n’est pas revendiquée.


Le [nommage des validateurs](docs/VALIDATOR_NAMES.md) est déployé et qualifié
sur l’image19cfe884642a : `serverless-code-validator-<uuid>`, avec reprise des
anciens p2-v par labels. Les57 groupes réels, cinq appels de conservation et
les purges des trois fonctions du replay sont recoupés dans la
[preuve](docs/evidence/validator-names-dev-2026-11-09.json). Ce complément ne
clôture pas les autres pannes ni la régression complète des versions008.

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

Le briefing d'exploitation `docs/dev-spark.md` est fourni localement par le
propriétaire du SPARK et ignoré par Git. Son retrait de l'historique public et
la correspondance des commits sont documentés dans
[la préparation Git](docs/GIT_HISTORY_REWRITE.md).
