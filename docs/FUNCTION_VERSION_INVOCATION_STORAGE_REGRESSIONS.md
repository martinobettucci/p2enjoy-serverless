# Régression008 des invocations et des mutations de stockage

Suite de SLS-074 après la [tranche CLI/reprise](FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md).
Statut : spécifiée avant code, pas encore qualifiée. Conserver les quinze groupes
function-storage et les trente et un groupes public-invocations, soit 46 groupes.
Les parcours de console et le banc historique de stockage restent séparés.

## Publication et volumes

Conserver les vraies mutations, écritures, quotas, refus, baux, confirmations
indisponibles, contention SQLite et reprises avant/après décision de stockage.
Le groupe publication distingue le code et les ressources : publier A avec quota
6 Mio prépare une version sans cible ; appel par hash, promotion explicite puis
appel par défaut. Le même code avec quota7 Mio reste A, avec hash et révision
canonique identiques. La vraie confirmation indisponible conserve son503, les
marqueurs de décision acquise et le nouveau quota ; A reste cible. L'appeler.

Pour conserver une vraie régression de rollback, modifier un marqueur empaqueté
et publier B avec les mêmes ressources. Appeler B par hash, promouvoir et appeler
B par défaut, puis utiliser le rollback UUID hérité vers A et l'appeler. Les
sept invocations Echo recoupent UUID et hash réservé ; la valeur secrète n'est
pas prétendue vérifiée par cette fixture. La lecture Docker des fichiers keep
recoupe les 1 310 720 octets et les empreintes des données/cache, sans nouvelle
écriture métier. Quota7 Mio et reçu de stockage restent identiques après rollback.
Le délai d'inactivité zéro permet de joindre les consommateurs avant suppression.

Les deux fonctions de cette campagne sont purgées complètement par l'API
publique, après libération des vrais clients/baux de stockage. La suppression
métier et sa conservation d'archive sont d'abord éprouvées, avant purge finale.

## Sélection et pools d'invocation

Le helper de publication prépare puis promeut explicitement, sauf les deux
fenêtres pilotes du groupe génération et du groupe publication pendant appel.
Conserver les UUID utilisés par Lambda functionVersion, mais suivre aussi les
hashes de publication et les cibles par défaut. Le premier pilote B est appelé
par hash pendant que A reste cible, puis promu et invoqué avant rollback A.

Pendant un vrai appel A de7s observé running/handler_started, publier B (doublon
connu) sans déplacer A. Une suppression UUID de la cible A avec If-Match courant
reste refusée409. Promouvoir B, constater encore le handler A actif, puis retirer
A avec If-Match courant : décision acquise, nettoyage physique en attente.
Le nouvel appel sans tag doit exécuter B ; le handler A déjà admis termine son
instantané A. Les nouvelles admissions par hash A sont refusées. Attendre la
fin des consommateurs de A et ses octets conservés à zéro. La promotion seule
ne sert plus de preuve de drainage des pools encore disponibles. Le compteur
des données conservées reste1.

Tous les autres contrats des31 groupes restent exécutés : ACL, événement Lambda,
corps/réponses binaires et limites, politique origine/IP, préflights, exceptions,
logs, délais et files, révocation, minima, budgets CPU/mémoire, stockage et
concurrence, contention SQLite, perte de connexion, arrêt actif, réceptions
HTTP/1.1 et HTTP/2 et plafond global d'instances via la console normale du SPARK.
Cette dernière fenêtre recrée normalement le contrôle pour appliquer/restaurer
sa configuration : le CID final peut changer, contrairement à l'image runtime
et à l'image applicative. Les fichiers officiels doivent retrouver leurs SHA.
La référence et les routes restent identiques.

## Preuves et portée des opérateurs

Les opérateurs de fautes existants sont conservés dans cette tranche ; leurs
protocoles nommés de pause, reprise, SIGKILL, arrêt gracieux et garde de configuration
sont rejoués, sans leur attribuer les garanties supplémentaires du nouvel opérateur
d'upload. Les pertes/délais propres de ces bancs restent distincts des pannes
produit provoquées. Toute anomalie réelle est conservée et instruite avant relance.
Pas de mock, interception, dépendance substituée, skip ou faux résultat.

Un pilote maintenu lance SSO réel puis les deux campagnes en série, avec rapports
antérieurs préservés et sources/images figées avant/après. Les7 appels de stockage
et toutes les réponses d'invocation du client public sont suivis et recoupés en
base avec leurs états, hashes et début du handler. Les réponses de préflight et
les appels interrompus ne sont pas comptés comme succès handler. Le nombre exact
des succès publics sera établi par le rapport, sans le supposer à partir des
seules fonctions utilitaires.

Le contrôle génère aussi un UUID de réponse avant toute réservation pour les
refus d'identité/route/limite et pour les préflights ; cet UUID n'est alors pas
une ligne invocations. La collecte doit le distinguer explicitement des appels
persistés et ne pas fabriquer un état. Les résultats métier non2xx peuvent être
des handlers réussis : seul l'état durable et handler_started font autorité.
L'appel client abandonné après admission peut terminer succeeded sans réponse
reçue ; son UUID observé running puis succeeded est conservé séparément.

Une réponse502 du proxy pendant le SIGKILL peut aussi ne porter aucun UUID
d'invocation ni hash. Le client doit relier sa propre connexion, par identifiant
local, au témoin natif du handler running au moment de la coupure, puis au même
appel devenu interrupted. Conserver séparément statut transport et statut durable.
Une règle générale acceptant toute réponse502 sans identifiant est interdite.
La perte de réponse n'est jamais comptée comme succès handler.

Dix-huit fonctions attendues dans deux namespaces sont purgées entièrement par
les API :2 stockage et16 invocation. Recouper agent, volumes, code, registre,
baux, instances, réseaux et canaux. Préserver les5 982 artefacts antérieurs,
la référence et les configurations officielles après restitution des gardes.
Les sources exécutables de livraison doivent rester celles qualifiées ; les
compléments documentaires ont leur époque explicite. Aucun changement produit,
UI ou manuel prévu ; les autres régressions008 et SLS-074 restent en cours.
