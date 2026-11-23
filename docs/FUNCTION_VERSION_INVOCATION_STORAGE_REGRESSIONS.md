# Régression008 des invocations et des mutations de stockage

Suite de SLS-074 après la [tranche CLI/reprise](FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md).
Statut : qualifiée par le replay DEV de46 groupes ci-dessous. Conserver les quinze groupes
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

## Résultat qualifié sur DEV

La [tranche invocation/stockage008](evidence/function-version-invocation-storage-regressions-dev-2026-11-10.json)
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

## Diagnostic du refus de commit ZIP — SLS-146

Le [premier refus courant](evidence/zip-storage-commit-barrier-first-failed-dev-2026-11-23.json)
conserve le helper1/commit_not_observed et l’upload200 attendu503. Le reçucommitted
11→12 et le candidatpublished dédupliqué sont établis ultérieurement ; ils ne
reconstituent pas le dernier SELECT ni l’instant du commit. Le client a perdu
les stderr et le corps/en-têtes de cette réponse ; ses assertions de release
puis nettoyage remplacent l’échec initial. La cause de la non-observation reste
inconnue ; le masquage et les pertes de diagnostic sont des défauts établis du banc.

Décision avant code du23novembre2026 : instrumenter ces deux fichiers du banc,
sans modifier le contrôle, l’agent, ControlObserver/ControlWriter, les transactions,
les SELECT, les signaux ni leurs conditions d’acquisition. Conserver25s pour
l’intention,3s pour prepared,5s pour commit,35s côté client et la garde110s
(5s pour watchdog). Aucune relance de PUT, augmentation de délai ou acceptation
de200 dans le scénario de confirmation perdue.

Le helper conserve un diagnostic borné en mémoire : version, mode, fonction,
opération déjà observée, phase, bornes et compteurs des boucles, dernières valeurs
issues des SELECT existants, entrée/retour des writers et lectures, émission des
signaux. Horloges monotones et instantsUTC sont conservés sans arrondi JSON.
Émettre la synthèse à la fin ou au premier échec, avant le nettoyage ; aucun
fichier ou événement par tour de boucle, aucun SELECT de diagnostic ajouté et
aucune attente supplémentaire pour acquitter SIGSTOP. Un signal envoyé ne vaut
pas preuve que le processus cible s’est arrêté.

Le premier échec natif reste celui levé. Chaque fermeture de registre/writer/
observer, restitutionSIGCONT et fermeturepidfd reste tentée, même si une autre
étape échoue. Si SIGCONT échoue hors cible déjà terminée, conserver le timer
indépendant armé : sa restitution reste nécessaire. Sinon tenter son arrêt.
Les erreurs de finalisation sont séparées et
ne remplacent pas la primaire. Une finalisation échouée sans primaire fait
échouer le helper. Les identités du helper et de l’agent, PID/naissance/cgroup,
accompagnent l’armement ; elles ne sont pas déduites après disparition.

Le client conserve avant assertion le statutHTTP, les identifiants publics
normalisés de requête/opération/fonction, le marqueur de décision, taille/SHA
du corps et sa classification existante. Aucun corps métier, configuration,
secret ou jeton n’est exporté. Capturer les vrais stdout/stderr de chaque
transport avec octets totaux, SHA de flux et suffixe borné64Kio, troncature
explicite ; événements structurés séparés, ligne de protocole bornée64Kio dès
réception des octets, avant assemblage jusqu’au saut de ligne. Valider le
protocole et les commandes réellement envoyées pour chaque transport joint,
y compris watchdog et diagnosticSIGTERM. Une jointure d’enfant déjà clos
n’envoie pas de commande. Protocole ou envoi invalide fait échouer le bilan.
Préserver les erreurs des requêtes concurrentes, de l’attente, de release et
du nettoyage, avec l’échec initial relancé après toutes les restitutions.
Un échec de sauvegarde/dispose ne doit pas remplacer cette primaire.

La qualification conserve quinzegroupes nominaux et septappels Echo, puis
25communs frais et leurs captures inspectées. Les nouveaux diagnostics sont
recoupés avec les états réels, les identités et la clôture physique ; les
succès ne valent pas reproduction de l’ancien timing. Un diagnostic distinct
peut interrompre réellement parSIGTERM une gardecommit possédée aprèswatching,
sans soumettre de mutation : il vérifie la primaire native et la restitution,
compte zéro groupe et ne remplace aucun des quinzegroupes. Toute nouvelle faute
reste conservée et instruite, sans retry.49/543/18 puis32/276 restent dus.

L’instrumentation est implémentée dans les deux fichiers du banc ; syntaxe
Python/Node contrôlée, sans qualification fonctionnelle à ce checkpoint. Les
troisP2 de la première revue ont leur correction dans l’arbre : secours conservé
si SIGCONT échoue, validation de chaque transport joint, parseur borné par
octets avant assemblage de ligne. Relecture sansP1/P2 résiduel ; aucune E2E
encore exécutée sur ces octets.
Le diagnostic séparé se lance avec
`node e2e/function-storage.mjs --diagnose-guard-interruption`, après création
d’une vraie session administrateur par le prérequis SSO existant. Il écrit
`function-storage-guard-interruption.json`, avec zéro groupe fonctionnel ; le
nominal sans argument conserve `function-storage.json` et ses quinzegroupes.
Le mode natif interrupt-guard vérifie PID/naissance/cgroup et les arguments du
helpercommit possédé, via pidfd, avant le vraiSIGTERM. Ces deux parcours restent
à exécuter sur le SPARK DEV, avec clôtures physiques propres et25communs frais.
