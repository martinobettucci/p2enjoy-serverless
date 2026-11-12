# Qualification de la plateforme

## Client HTTP intégré par fonction — en qualification

`node e2e/function-http-client.mjs` reçoit le JSON SSO sur stdin privée, seul sur
le SPARK DEV au repos. Il publie deux handlers originaux par les API, invoque
réellement les domaines HTTPS, teste les bornes et refus du relais, les versions,
la redirection sans suivi, les jetons et le timeout. Le parcours UI part de
l’accueil et du vrai SSO, découvre Tester, utilise les modes serveur/CORS,
la copie native, le téléchargement, les journaux et le viewport mobile. Prévoir
quinze minutes réelles pour l’expiration du jeton temporaire ; aucune horloge
ou ligne SQLite n’est modifiée. Le rapport UUID reste incomplet jusqu’aux
purges et recoupements natifs ; les captures nécessitent leur inspection.
La [première preuve43groupes](../docs/evidence/function-http-client-dev-2026-11-12.json)
passe18ciblés puis25régressions sur382sources46a59128 et032ca071 ;27handlers,
expiration réelle900s,27captures inspectées, quatre fonctions purgées et huit
jetons révoqués. Le premier passage13reste exclu.
La campagne ne ferme pas seule les autres scénarios du [contrat](../docs/CONSOLE_TESTER.md),
notamment les interruptions et les régressions complètes.

Deux compléments distincts passent avec la correction071.7 :
`node e2e/function-http-client-ui.mjs` pour les corps, refus locaux, politiques,
annulations, gzip, révocation, liens et manuel ;
`node e2e/function-http-client-admission.mjs` pour quatre vrais JSON HTTPS
partiels puis429/408 et quatre relais actifs puis429. Même stdin SSO privée,
objets confinés, purges et reçus UUID. Le fixture canonique est étendu, sans
nouveau produit/conteneur ni source de substitution. Les18groupes initiaux
restent dans leur époque382sources. Le [complément46](../docs/evidence/function-http-client-ui-admission-dev-2026-11-12.json)
passe16UI+5admission+25régressions sur384sources8285798e/8c761c5e,35handlers
et38captures inspectées. Quatre fonctions nominales et quatre intermédiaires
sont purgées ; six jetons révoqués. Les21intermédiaires sont exclus après revue
visuelle puis correction des messages/singulier et replay complet.

## Échéances et confidentialité du testeur — en réalisation

`node e2e/function-http-client-confidentiality.mjs` reçoit les identifiants SSO
sur stdin privée. Le client compose de vraies sentinelles query/Authorization/
corps/en-tête, attend les échéances UI1s et les handlers4s, vérifie les droits du
détail d’invocation puis recherche les valeurs dans les véritables logs/audits.
`function-http-client-private-inspect.py begin|inspect NAMESPACE_UUID` est
strictement lecteur du SPARK ; inspect reçoit ses sentinelles sur stdin privée
et ne renvoie que booléens/SHA et métadonnées corrélées. Les lectures ont des
bornes et une échéance ; un manque fait échouer. Aucune capture n’est effectuée
pendant la saisie confidentielle ; les vues des délais ne portent que delay4.
Un premier passage de9groupes est conservé comme intermédiaire. Le passage
de10groupes dd3b50db réussit aussi le contrôle positif : une vraie trace
volontaire de témoin public est trouvée sans être réémise. Ce passage reste
préliminaire ; le replay qualifié avec régressions est décrit ci-dessous.

`node e2e/function-http-client-recovery.mjs` reçoit la même stdin SSO privée et
utilise `function-http-client-recovery-operator.py` sur le seul SPARK DEV, seul
et au repos. Une garde indépendante vérifie le CID/image, PID/naissance/cgroup
et les empreintes avant une suspension réelle puis perte du pilote. Le second
scénario coupe le contrôle après confirmation persistée du démarrage du handler.
Le signal natif, Docker137, restauration du même CID/image, observation unique
et appel neuf sont requis. Aucun contenu de requête ne transite par l’opérateur.
Le premier passage3360afcd échoue sur les assertions SSH/timer du watchdog ;
la garde restaure réellement la même génération et les deux fonctions sont
purgées, puis leurs parents supprimés par API. Le client reprend les conditions
du précédent natif (SSH137/255 avec événement et reçu, timer sans MainPID).
Le [plan](../docs/CONSOLE_TESTER_FAILURES.md) définit garde, jonction, nettoyage
et distinction entre refus certain et issue inconnue. La coupure après admission
a ensuite reproduit le défaut UI sur80eca655 : proxy502 après SIGKILL, reprise
native unique sans rejeu, mais refus certain affiché. La correction071.8 ajoute
la provenance réelle du contrôle ; le client exige aussi un vrai503 avant
émission sous `refusal-lock`, verrou SQLite15s sans DML, release/EOF/échéance
et processus joints. Build et bascule sont ensuite effectués, puis le replay
corrigé passe sur96e5dc4e.
Ne pas lancer en parallèle d’un autre scénario.

La [preuve42](../docs/evidence/function-http-client-recovery-confidentiality-dev-2026-11-12.json)
qualifie les replays993fbeda/84287810 puis25régressions sur96e5dc4e,
389sources039c4c97 :12handlers,27captures inspectées,12fonctions de tous les
passages purgées et9jetons révoqués. Les trois opérateurs sont joints, gardes
inactives et base saine. Ce résultat est le statut courant de ces replays.
Les pertes de réponse des mutations temporaires et les sources/routes
indisponibles restent des scénarios distincts à réaliser.

## Réponses perdues des jetons temporaires — en réalisation

`node e2e/function-http-client-token-loss.mjs` reçoit le JSON SSO sur stdin
privée, seul sur le SPARK DEV au repos. Il publie une fonction originale,
puis utilise `function-http-client-token-operator.py` pour quatre vraies pertes
de réponse : création/révocation, avant/après commit. L'observateur reconnaît
uniquement la ligne HTTP publique et les métadonnées syscall du FD exact ; il
ne lit ni header secret ni réponse contenant le jeton. Gardes indépendantes,
SIGKILL natif/Docker137, reprise du même CID/image, audit corrélé et absence de
rejeu sont requis. Le client ferme ensuite la confirmation et consulte la liste
par l'UI, sans rechercher la valeur perdue ; les invocations réelles vérifient
l'état des jetons de révocation. Captures desktop/mobile et purges recoupées.
Contrat : [pertes de jeton](../docs/CONSOLE_TESTER_TOKEN_LOSS.md). Code préparé,
le premier3c50e181 échoue sur une liste comptée avant rendu asynchrone, après
les deux coupures natives de création. Fonction/jeton/parents/gardes nettoyés ;
attente du panneau et des lignes exactes ajoutée avant replay des quatre cas.
Le replayabc035c2 passe ensuite7groupes ciblés puis25régressions, avec
32captures inspectées. La [preuve32](../docs/evidence/function-http-client-token-loss-dev-2026-11-12.json)
porte392sourcescf5244f5/image96e5dc4e. Les deux fonctions sont purgées, quatre
jetons révoqués, huit observateurs morts et cinq opérateurs nominaux joints.
071.3/.8 sont qualifiés ; le premier passage reste exclu des32.

## Lecture réellement en attente du testeur — en préparation

`node e2e/function-http-client-loading.mjs SHA_IMAGE_CONTROLEE` reçoit le vrai
SSO sur stdin privée, crée sa fixture originale puis utilise le watchdog natif
existant. Dans sa fenêtre4,5s, Actualiser montre Lecture en cours, retire les
anciennes URL/cURL/réponse et conserve le jeton. Le seul observateur est ensuite
réellement tué ; la réponse et la garde12s sont jointes séparément, même PID/
naissance/cgroup/CID/image/StartedAt recoupés avant le nouvel appel explicite.
Le [contrat](../docs/CONSOLE_TESTER_LOADING.md) impose aussi de rejouer les sept
groupes de reprise après les revalidations d’identité de l’opérateur, puis les
25régressions communes. Code préparé et syntaxe contrôlée ; aucun nouveau
scénario exécuté ou qualifié à ce stade.

## Testeur sous source des domaines refusée — complément qualifié

`node e2e/function-http-client-source-access.mjs SHA_IMAGE_CONTROLEE` reçoit le vrai SSO sur stdin
privée. Le client publie sa fonction originale dans le scope source-access
strict de la garde existante `invocation-source-permissions.py`. Le fichier
réel passe000 puis revient à son mode initial sous garde indépendante ; contenu,
inode, propriétaire et mtime conservés, ctime observé. Sous errno13 confirmé,
POST de test503 avant émission, vrais appels témoins, Actualiser sans anciennes
URL/réponses, CSPself, captures desktop/mobile et restitution sont requis.
`function-http-client-source-inspect.py` recoupe namespace/nonce/descriptions et
métadonnées natives, sans code ni secret. Contrat : [source du testeur](../docs/CONSOLE_TESTER_SOURCE.md).
Le [premier passage réel](../docs/evidence/function-http-client-source-access-failed-dev-2026-11-12.json)
reproduit le faux état « Aucune cible promue » ; il est exclu des qualifications.
Le [replay corrigé](../docs/evidence/function-http-client-source-access-dev-2026-11-12.json)
passe7groupes ciblés puis25régressions sur395sources28105d2b/image60938093,
six handlers et32captures inspectées. Sans code, hash exact sous refus, source
rétablie, pilote archivé404 et retour explicite sont éprouvés ; deux fonctions
et deux jetons des passages nettoyés.071.2 reste ouverte pour le transitoire de
chargement,071.6 pour l’exception inattendue ;101/102 suivent les défauts visuels.

## Capacité réelle des brouillons de code

`node e2e/code-draft-capacity.mjs` reçoit les identifiants du SSO réel sur son
stdin privée. Exécuter seul sur le SPARK DEV au repos, après synchronisation
des sources indexées. Les plafonds32/128 puis64Mio chiffrés sont atteints par
les API ; `code-draft-capacity-inspect.py` ne lit que des métadonnées natives.
Une publication initiale originale est invoquée dans Docker avant les archives
et purges normales. Rapport UUID sous `.local/e2e`, aucun jeton/source dedans.
Préconditions, calcul exact et nettoyage : [CODE_DRAFT_CAPACITY](../docs/CODE_DRAFT_CAPACITY.md).
La [preuve DEV](../docs/evidence/code-draft-capacity-dev-2026-11-12.json) passe17groupes ciblés
puis25régressions sur375sources. Le premier17reste préliminaire/exclu ;33fonctions
nominales et33préliminaires sont purgées.22captures sont inspectées.


## Parcours de console de l’éditeur — première tranche qualifiée

`node e2e/code-editor-ui.mjs` reçoit le JSON SSO sur stdin privée. Le parcours
part de l’accueil et du vrai SSO, crée namespace/service/fonction et jeton Read
par les formulaires, puis publie le paquet original YAML par la console.
Il édite les vraies sources et le handler, relit les octets exacts, provoque un
conflit entre deux vrais onglets, borne l’historique à64 gestes, retire/rétablit un fichier et publie des
versions dédupliquées, pilotes, ESM puis un import réellement cassé. Promotion,
rollback et URL copiée sont invoqués contre Docker. Captures desktop/mobile,
absence de stockage web, brouillon retrouvé et purge native sont requis.
Aucune interception ni dépendance substituée. Les rapports UUID conservent les
échecs sans ajouter leurs groupes à un replay réussi. La [première tranche](../docs/evidence/code-editor-console-dev-2026-11-12.json) passe12groupes UI puis20serveur
et25régressions sura77b6b4e. Deux époques de370sources sont déclarées sans
changement produit.17invocations natives,41captures inspectées et8purges de
fonctions recoupées ; manuel17chapitres/67paragraphes. Les premiers échecs du
banc restent exclus. Quotas, reprises, limites et compléments UI gardent070ouverte.

Le complément070.8 est qualifié : assertions de confirmation à la frappe,
lecture et retry réel404, saisie pendant sauvegarde effective, lecture seule au
retrait, puis choix de source depuis le vrai dialog. La [preuve](../docs/evidence/code-editor-save-confirmation-dev-2026-11-12.json) passe14groupes ciblés
puis25régressions sur371sources0080af6 et6e1584f2. Neuf invocations et44images
sont recoupées ; trois fonctions purgées et21helpers terminés. Le checkpoint57
conserve ses sources/image ; les passages antérieurs ne sont pas additionnés.
`code-editor-save-lock.py hold|probe|stop NAMESPACE FUNCTION` est un opérateur
DEV sans écriture de donnée : verrou SQLite réel au plus3s, libération/EOF/
échéance, ou signal du seul PID/naissance/commande vérifiés. Le client éprouve
les8sorties (dont fragment sans LF, entrée invalide et borne32octets) puis utilise le verrou pour observer les
frappes avant réponse HTTP. Les signaux tardifs après EOF et la naissance
périmée sont refusés et recoupés. Les probes rejoignent le writer natif sous son
propriétaire et recoupent zéro changement et connexion close. Aucun délai
réseau, seed ni réponse remplacée.

## Sources et brouillons de code — première tranche qualifiée

`node e2e/code-editor.mjs` reçoit le JSON SSO sur stdin privée. Il utilise le
vrai accueil puis SSO, les vraies API HTTPS et les conteneurs Docker. Le helper
`code-editor-package.py` reprend uniquement la dépendance YAML2.9.1 déjà
installée dans la référence inchangée et les handlers originaux editor.cjs/mjs.
Le paquet conserve Unicode, CRLF, absence de fin de ligne, mode exécutable et
binaire. Aucune dépendance de substitution, interception réseau ou seed SQL.

Le scénario couvre droits et portée, sauvegarde privée/conflits/no-op, bornes
1Mio/4Mio/128chemins, quatre corps HTTPS réellement partiels puis429/408,
déduplication et invocations pilote/CJS/ESM, promotion/rollback, import cassé,
rétention de base supprimée et purges publiques. Le lecteur natif accepte le
seul UUID namespace et ne renvoie ni source, ni chiffrement, ni jeton.
Les quatre sockets partiels ont fini leur écriture TLS avant le cinquième ;
aucun sondage de source ne concurrence leur capacité. Les rapports UUID ne sont pas écrasés. Une erreur est conservée ; aucun rejeu
silencieux. Quotas globaux/par acteur/chiffrement, interruptions, purge contre
lecteur et interface restent des preuves distinctes. La [première tranche](../docs/evidence/code-editor-server-dev-2026-11-12.json)
passe20groupes ciblés puis25régressions sur367sourcesa983b2f et7c5c6f4b,
22captures inspectées, huit invocations natives recoupées, quatre fonctions
des deux passages purgées et5982artefacts originaux intacts. Le premier passage
a échoué au13e groupe sur le client ClientRequest45s ; cet échec est conservé
et n’ajoute aucun groupe aux45réussis. Le vrai client TLS corrigé reçoit429
en107ms sans corps et quatre408 après30s ; les cinq UUID sont recoupés dans
les logs serveur. Seul070.7 est clôturé. Contrat : [CONSOLE_EDITOR](../docs/CONSOLE_EDITOR.md).

## Attente de droits et renouvellement SSO

`node e2e/sso-session-recovery.mjs` reçoit les identifiants du compte autorisé
sur stdin privée. Huit groupes : quatre vues publiques desktop/mobile, refus
des motifs et alias canonique, vraie connexion administrateur, durée du JWT et
renouvellement après attente réelle d'environ cinq minutes, puis déconnexion.
Les quatre vues ne prouvent aucune décision de rôle. Les flows ouverts pour
les liens de vérification sont annulés par leur vrai callback et consommés.

Le lecteur `python3 -B e2e/sso-session-inspect.py DIGEST_DE_SESSION` lit cette
seule session dans le conteneur installé et vérifie les JWT contre le vrai
JWKS avec le code livré. Il ne renvoie que des métadonnées ; les jetons OAuth
et la clé de chiffrement ne quittent pas Docker. Aucune mutation SQLite, clé
privée de signature, horloge artificielle ou dépendance substituée.

Le rapport UUID conserve explicitement les preuves absentes : comptes sans
`verified`, `verified` seul, refus azp discriminant et rotation réelle de clé.
Ces prérequis externes sont dans SLS-089 ; aucun skip ne les remplace. Les six
JPEG demandent leur inspection distincte. Contrat :
[SSO_SESSION_RECOVERY](../docs/SSO_SESSION_RECOVERY.md). La
[preuve partielle DEV](../docs/evidence/sso-session-recovery-dev-2026-11-11.json)
passe ces 8 groupes puis 25de régression sur 359 sources et e81007c5. 30 captures
recoupées, dont2du chapitre Se connecter ajoutant0 groupe. Les300 s et le
renouvellement après expiration initiale sont qualifiés ; les profils/rotation
et refus azp/aud restent non éprouvés, sans prétendre clore SLS-089.

## Identité visuelle Serverless

`node e2e/application-icon.mjs` prend le JSON SSO sur stdin privée, transmis en
mémoire par le lanceur ; jamais en argument, environnement ou fichier. Quatre
groupes réels depuis l'accueil : marque/favicon anonyme puis connexion SSO,
navigation au clavier vers le manuel et déconnexion, sur1440×1000 et390×844.
Le tiroir mobile et sa restitution de focus sont parcourus normalement.

Le rapport unique `application-icon-UUID.json` sous `.local/e2e/` recoupe le SVG
réellement servi, son SHA et no-store ; quatre JPEG dans leurs viewports sont
générés. L'inspection16/32px du SVG servi complète ces captures, sans être
présentée comme une vue applicative. Contrat :
[SLS-100](../docs/BACKLOG.md#sls-100) et
[identité du produit](../docs/DESIGN_SYSTEM_APP.md#serverless-identity).
La [preuve DEV](../docs/evidence/application-icon-dev-2026-11-11.json) passe4groupes dédiés puis
25de régression :8manuel,8publics,9connexion, sur356sourcesb1ee473 et la même
image779aef7b.26captures sont inspectées ; contraste de l'asset9,03:1 et rendus
16/32/64 recoupés. Les34backends et les trois autres ressources web sont identiques.
Le seul document indexé actualisé après qualification est le design du produit,
pour ses résultats et références ; cette transition documentaire est explicitée
dans la preuve. Aucune ressource servie n'est modifiée après les campagnes.

## Borne globale des 10000 invocations

`node e2e/invocation-retention-volume.mjs` reçoit le JSON SSO sur stdin privée.
Seul sur le SPARK DEV au repos, il ouvre l'installation isolée de même image,
garde1800s, puis exécute5008 vrais HTTP sur chacune de deux fonctions cpu0,5.
Le relevé9984 avant borne et le relevé10000 après10016 réponses permettent de
vérifier les exacts UUID conservés par date de fin/id, sous10000 par fonction.
Trois groupes : préparation, volume réel, purges/restitution des originaux.
Prévoir jusqu'à30minutes de fenêtre DEV ; le débit réel n'est pas présumé.
Les deux flux sont joints avant tout nettoyage, les réponses libérées et la
progression sauvegardée par lots. Rapports UUID sous .local/e2e.
Contrat : [INVOCATION_RETENTION_VOLUME](../docs/INVOCATION_RETENTION_VOLUME.md).

Après fin/restauration de cette campagne, `python3 -B e2e/instance-limit-guard-options.py`
éprouve trois groupes sans SSO : refus réel120+1800, refus1800 hors mode, puis
installation réelle avec garde900 par omission et restitution nominale jointe.
Les deux refus ne créent aucune fenêtre ; les cinq modes120 de
`node e2e/instance-limit-environment.mjs MODE` et le cas historique
`node e2e/storage-legacy-recovery.mjs --partial` restent des régressions distinctes.

## Conservation des témoins terminaux de rétention

Après la campagne CLI réussie et ses purges, au repos sur le seul SPARK DEV :
`python3 -B e2e/schedule-terminal-history-capture.py`. Le chemin de preuve peut
être fourni par `--evidence docs/evidence/adapter-schedules-dev-2026-11-11.json`.
L'opérateur relit les témoins exacts puis conserve des sauvegardes natives,
artefacts et références aux images déjà exportées dans un dossier privé UUID.
Trois groupes de préparation, aucun service arrêté ni original modifié ; le
rapport UUID sous .local/e2e porte les dates réelles d'éligibilité après sept jours.
Une capture réussie ne qualifie pas la rétention : son replay gardé reste requis.
Contrat : [SCHEDULE_RETENTION](../docs/SCHEDULE_RETENTION.md#capture-des-tirs-terminaux-et-générations-retirées).

## Planifications publiées par la CLI

`node e2e/adapter-schedules.mjs`, après le prérequis SSO réel décrit ci-dessous,
exécute les processus Python plan/deploy/promote sur un manifeste original à
deux fonctions. Le cron actif tire sur le hash publié à la frontière UTC,
le cron désactivé reste sans appel. L'avertissement privacy est conservé ; celui
de moteur absent est absent des sorties plan/deploy et du manuel. Quatre groupes,
une frontière, deux purges publiques recoupées physiquement. La preuve concerne
les processus du poste aux sources identiques à DEV ; aucun conteneur CLI lancé.
Contrat : [SCHEDULE_ADAPTER](../docs/SCHEDULE_ADAPTER.md).

## Concurrence partagée entre HTTP et cron

`node e2e/schedule-concurrency.mjs`, seul sur le SPARK DEV au repos, avec une
session administrateur préparée par `node e2e/dev-sso-sessions.mjs` (JSON SSO
sur stdin privée), publie deux fonctions maximum3/shared dont seule la
concurrence1/2 diffère. Deux vrais HTTP occupent la frontière UTC : le premier
cron attend sans handler, le second est observé pendant son handler de cinq
secondes sur une deuxième instance, puis réussit avant la libération des HTTP.
Quatre groupes, une frontière réelle, puis deux purges
publiques et vérification physique. Le rapport UUID `scheduled-functions-*.json`
porte l'observation native discriminante. Aucun budget officiel changé.
Contrat : [SCHEDULE_CONCURRENCY](../docs/SCHEDULE_CONCURRENCY.md).

## États de console des planifications

`node e2e/schedule-console.mjs`, seul sur le SPARK au repos avec session SSO
réelle, part de l'accueil et crée ses deux fonctions par les formulaires. Une
fonction vide et une fonction au nom63 ; six crons publiés/promus par l'API de
code seul donnent six vrais tirs à une frontière UTC. Le navigateur vérifie
deux pages5+1, clavier/focus, mobile et un vrai refus401 après retrait temporaire
des cookies, puis Réessayer après restitution. Prévoir une frontière réelle,
environ cinq minutes ; minimum0,3CPU/768Mio, budgets officiels inchangés.

Chaque rapport et capture JPEG portent leur UUID. Le scénario échoue
si le produit conserve sa pagination après erreur ; aucun succès conditionnel. Les minima sont libérés, les deux fonctions purgées publiquement,
puis le lecteur strict schedule-instance-reuse-inspect.py recoupe l'absence
physique, les5982 artefacts antérieurs et les34 backends. Contrat :
[SCHEDULE_CONSOLE](../docs/SCHEDULE_CONSOLE.md). Les images demandent une inspection
visuelle distincte ; les assertions ne prouvent pas la lisibilité.

## Régression008 du contrôle et des publications

Depuis la racine synchronisée, sur le seul SPARK DEV au repos :

```sh
python3 -B e2e/function-version-publication-regressions.py
```

Le pilote reçoit le JSON SSO sur stdin masquée, conserve les anciens rapports
locaux/natifs puis exécute control-operations, le prérequis dev-sso-sessions,
deployments et code-publications en série. Il refuse son propre rapport déjà
présent, .local/e2e/function-version-publication-regressions008.json. Une erreur
arrête la matrice sans rejeu automatique. Aucun fichier privé de cookie n'est
copié dans les archives de rapports. Les sessions de plateforme restent en0600.
Le lecteur natif de capacité accepte deploy uniquement en mode inspect ; le
lecteur physique conserve son inventaire strict sur les deux namespaces.

La [première tranche de régression008](../docs/evidence/function-version-publication-regressions-dev-2026-11-09.json) passe76 groupes sur292
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

## Pertes de réponse des décisions de version

Depuis la racine synchronisée, sur le seul SPARK DEV au repos :

```sh
python3 -B e2e/function-version-state-transport-run.py
```

Le pilote reçoit le JSON SSO sur stdin masquée et refuse les rapports déjà
présents. Le client part de l'accueil et du SSO puis crée ses propres objets.
Le helper function-version-state-observer.py observe la ligne publique exacte
sur le socket18090 ; aucun buffer, code, état ou résultat n'est remplacé. Ses
programmes figés root d'arrêt/restitution gardent les identités et les reçus.
Le protocole interne inspect/restore/evidence/rescue est réservé à ces UUID et
n'est pas une commande générale d'exploitation. Les rapports privés portent
function-version-state-transport{,-checkpoint}.json. Une issue inconnue de l'arrêt
interdit un redémarrage prétendu réussi ; l'échec reste conservé.

Les [réponses perdues des décisions de version](../docs/evidence/function-version-state-transport-dev-2026-11-09.json) passent9 groupes
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

## Première identité inconnue et versions ultérieures connues

Depuis la racine synchronisée, sur le seul SPARK DEV au repos, exécuter en série :

```sh
python3 -B e2e/function-version-unknown-first-run.py preserved-first
python3 -B e2e/function-version-unknown-first-run.py unknown-first-tombstone
python3 -B e2e/function-version-unknown-first-run.py unknown-first-tombstone --restore-with-guard
```

Les pilotes reçoivent le JSON SSO sur stdin masquée et refusent les rapports déjà
présents. Ils utilisent la référence006 construite et la007 attestée ; aucune
image produit nouvelle. Le contrat [UNKNOWN_FIRST](../docs/FUNCTION_VERSION_UNKNOWN_FIRST.md)
distingue le témoin public et la préparation déclarée, dont seuls inventory_json
et events_json de A changent sous contraintes. Rapports et checkpoints privés :
.local/e2e/function-version-history-VARIANT[-guard]{,-checkpoint}.json.
Les trois backups natifs de chaque fenêtre sont conservés sous history-inputs,
avec SHA, propriétaire1001 et mode0600. Les erreurs du client conservent identité,
coordonnées et empreinte, jamais corps brut ni pile contenant des données privées.
Une promesse terminale couvre GET et lecture du corps avant sa jonction finale.

La [première identité inconnue](../docs/evidence/function-version-unknown-first-dev-2026-11-09.json) passe17 groupes sur286 sources :
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

## Corrélations007 refusées avant transformation008

Depuis la racine synchronisée, sur le seul SPARK DEV au repos, exécuter en série :

```sh
python3 -B e2e/function-version-purge-correlation008-run.py artifacts
python3 -B e2e/function-version-purge-correlation008-run.py volumes
```

Les deux pilotes refusent d'écraser leurs rapports. Ils sélectionnent les backups
007 réellement produits par la [preuve précédente](../docs/evidence/function-version-purge-migration008-dev-2026-11-09.json).
L'opérateur function-version-purge-correlation008.py ouvre l'archive immutable,
recoupe SHA et tables, conserve le WAL vide et le SHM éventuel. Seules des copies
privées sont altérées, contraintes actives, puis démarrées avec le vrai uvicorn
et l'image courante. Aucun socket, port, agent ou volume vivant n'est monté.

Les rapports natifs sont control/function-version-purge-correlation008-PHASE.json ;
rapports et checkpoints privés sous .local/e2e. Chaque phase compte20 refus et1
témoin avec relance du même ID. Le [contrat](../docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#refus-de-corrélation-sur-copies007)
borne les diagnostics attendus et le cas combiné du pointeur actif. La
[preuve](../docs/evidence/function-version-purge-correlation008-dev-2026-11-09.json)
passe42 groupes sur283 sources : rollback007 exact, anciennes colonnes des16
tables conservées dans les témoins008, reprise identique. La panne de socket
postérieure attendue n'est pas un refus ni une disponibilité HTTP. Archives et
sidecars inchangés, copies retirées,17 tables/contrôle/référence/démarrages et
fichiers officiels vivants identiques ; actifs nuls. L'essai initial arrêté
avant copie reste distinct. Pas de nouveau parcours UI ni déploiement produit.

## Purges historiques vers008

Le [contrat](../docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md) réutilise la fenêtre
historique gardée avec les vraies images006/007. Depuis la racine synchronisée,
exécuter chaque commande après la fin complète de la précédente :

```sh
python3 -B e2e/function-version-schema007-reference.py
python3 -B e2e/function-version-purge-migration008-run.py 006 artifacts
python3 -B e2e/function-version-purge-migration008-run.py 006 volumes
python3 -B e2e/function-version-purge-migration008-run.py 007 artifacts
python3 -B e2e/function-version-purge-migration008-run.py 007 volumes
python3 -B e2e/function-version-purge-migration008-run.py 007 artifacts --restore-with-guard
```

Les cinq commandes de fenêtre reçoivent les identifiants SSO autorisés sur stdin
masquée, jamais en argument ou fichier. L'attestation007 compare29 backends à la
preuve du registre et conserve un tag/receipt root protégé, sans changer le
contrôle servi. Les pilotes refusent leurs rapports préexistants ; conserver
l'essai précédent avant relance. Rapports : .local/e2e/function-version-purge-
SOURCE-to-008-upgrade-PHASE[-guard]{,-checkpoint}.json. Le helper distant est
storage-legacy-environment.py, avec source et cible explicites. Ses modes
historiques restent006→007 et refusent une cible implicite incompatible avant
armement, arrêt ou déplacement.

La preuve des refus s'exécute comme root uniquement dans le SPARK autorisé :
`python3 -B /srv/p2enjoy-serverless/e2e/function-version-purge-migration008-preflight.py`.
Son rapport natif est control/function-version-purge-migration008-preflight.json.
Les trois cas confirment services/démarrages, tables, répertoires et configuration
strictement identiques ; seuls les répertoires vides exactement reconnus sont retirés.

La [preuve consolidée](../docs/evidence/function-version-purge-migration008-dev-2026-11-09.json)
retient19 groupes sur280 sources et3 refus sur281 sources, mêmes exécutables
communs et image def45648. Les quatre fenêtres normales terminent la purge et
son restart ; la cinquième restitue indépendamment après perte du pilote.
HashesNULL/connus, dates/UUID, garde et commande corrélées, registre deleted et
charge sont recoupés. Les17 tables et5982 artefacts originaux sont conservés,
référence/configuration/routes inchangées et actifs nuls. Les cinq gardes sont
inactives. L'essai d'attestation interrompu reste séparé, sans groupe ajouté.
Aucun parcours UI frais ; les corrélations007 sont qualifiées ci-dessus. Le complément premier hash inconnu est qualifié ci-dessus ;
les autres pannes restent ouvertes.

## Refus et reprise de migration008

`function-version-migration008-build.py` conserve l'image servie, construit la
candidate et recoupe31 fichiers backend et le web. Depuis la racine synchronisée :

```sh
python3 -B e2e/function-version-migration008-run.py complete-component sha256:def45648f9e74490a18c5d05f79681d838fbd10fdb519bc8942f9fffe4decbe4
```

Les dix groupes s'exécutent en série sur copies privées de la vraie sauvegarde007.
Le helper utilise le propriétaire SQLite et le vrai uvicorn/Docker, réseau none,
sans socket ni volume vivant. Un échec ultérieur de socket ne vaut pas refus.
Les six refus exigent le rollback exact ; témoin, verrou/reprise et contraintes
recoupent données et backfills. Les14 refus SQL et3 contrôles internes du dernier
ne gonflent pas le total. `function_version_migration_wal.py` observe un vrai
pwrite64 sans modifier ses résultats, coupe après écriture d'une frame non
commise, recoupe mort native9/Docker137,007 intact puis008 sur le même conteneur.
Sa garde reste armée jusqu'à suppression confirmée, puis est désarmée.

La [preuve finale](../docs/evidence/function-version-migration008-recovery-dev-2026-11-09.json)
conserve276 sources pour le composant et277 pour bascule/API/CLI. Le pilote
`function-version-migration008-deploy.py` s'exécute comme root uniquement sur
le SPARK autorisé : backup SQLite natif, contrôle du repos, remplacement de
l'image et garde indépendante de retour d'image sans restauration DB.
Cette opération est bornée aux images exactes19cfe884/def45648 et refuse un
rapport préexistant. Elle n'est pas une commande générique de mise à jour.
Les17 tables et le schéma déjà008 sont identiques après bascule ;12 groupes API
et5 CLI passent ensuite, avec deux fonctions physiquement purgées. Les trois
essais WAL et l'essai de bascule arrêté avant garde restent archivés séparément.

Les rapports natifs sont control/function-version-migration008.json et
control/function-version-migration008-deploy.json ; checkpoints dans .local/e2e.
Les pilotes refusent de les écraser. La reproduction rouge et le premier replay
neuf restent dans leurs époques distinctes. Le [contrat](../docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md)
borne ce qui est qualifié : nominal et désarmement, sans prétendre éprouver les
pertes propres des gardes. Le complément de purges ci-dessus couvre leurs reprises normales ; les autres pannes et la campagne
complète restent nécessaires. Aucun nouveau parcours UI.

## Reprise des paquets dédupliqués — complément SLS-074

Depuis la racine, après synchronisation dans le seul SPARK DEV et préparation
de la session SSO réelle, lancer :

```sh
python3 -B e2e/function-version-duplicate-recovery-run.py
```

Le client HTTPS `function-version-duplicate-recovery.mjs` utilise son opérateur
`function-version-duplicate-recovery-operator.py`. Il exige le repos, crée ses
objets par l'API et publie la fixture originale validator-observation en mode
success. Le helper observe son vrai marqueur, arme une garde, puis retire les
permissions du seul répertoire du doublon. Le contrôle doit publier200 et
conserver réservation/paquet jusqu'au nettoyage. Le premier cycle restitue
explicitement ; le second interrompt le contrôle après commit puis tue le
helper. Son parent recoupe waitpid/signal9/PID/naissance ; la garde indépendante
restitue avant docker start du même conteneur. Contrat :
[FUNCTION_VERSION_DUPLICATE_RECOVERY](../docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md).

Les rapports `.local/e2e/function-version-duplicate-recovery.json` et
`-checkpoint.json` doivent être conservés avant relance ; le pilote refuse
de les écraser. La [preuve](../docs/evidence/function-version-duplicate-recovery-dev-2026-11-09.json)
passe quatre groupes, cinq invocations et les compteurs data/cache1–5, sur271
sources figées et19cfe884. Un dernier doublon se nettoie normalement après reprise.
Le journal natif recoupe le résultat de la garde systemd ; les31 backends,
configurations et référence sont conservés. Le contrôle possède un nouveau
démarrage attendu. Une fonction est physiquement purgée, les deux gardes et leurs
helpers terminés, les ressources actives/réservations nulles. Les mises à jour
de résultat du contrat suivent ce gel, sans changement de code exécutable.
Pertes SSH, inode remplacé, pannes propres de garde et SIGKILL pendant unlink
restent des preuves distinctes ; aucun nouveau parcours UI n'est revendiqué.

## Capacité des uploads — complément SLS-074

Depuis la racine du dépôt, après synchronisation des sources dans le seul SPARK
DEV et préparation de la session SSO normale, exécuter en série :

```sh
python3 -B e2e/function-version-upload-capacity-run.py
```

Le pilote utilise `function-version-upload-capacity.mjs` et le helper distant
en lecture seule `function-version-upload-capacity-inspect.py`. Il refuse les
rapports déjà présents : conserver l'essai précédent avant toute relance.
Le rapport privé est `.local/e2e/function-version-upload-capacity.json`, son
recoupement complet porte le suffixe `-checkpoint.json`. Contrat :
[FUNCTION_VERSION_UPLOAD_CAPACITY](../docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md).
Le précontrôle exige le repos et la capacité réelle pour quatre réservations,
puis les API créent, publient et promeuvent explicitement une version stable.

La [preuve finale](../docs/evidence/function-version-upload-capacity-dev-2026-11-09.json)
passe quatre groupes sur267 sources figées : quatre uploads admis, cinquième429
sans artefact, attente encore présente après31,43s, vrai timeout de A et convergence
des trois paquets identiques. Les événements create/destroy confirment un seul
validateur à la fois ; le candidat refusé est ensuite relancé explicitement.
Quatre invocations Docker retrouvent stable/pilote, secret par empreinte et
compteurs data/cache1–4. Le contrôle19cfe884, les31 backends, la référence et les
fichiers officiels sont conservés. Aucun build ni parcours UI nouveau.

Le premier essai échoue pendant la lecture exec du marqueur ; sa cause précise
n'est pas reconstituée. Le polling final n'utilise plus exec ; l'observation
initiale exige A vivant et son marqueur. Un replay vert intermédiaire précède
le dernier durcissement du nettoyage à identité inconnue. Ces deux époques
restent séparées et leurs groupes ne sont pas additionnés au replay final.
Les trois fonctions sont physiquement purgées dans leurs trois namespaces,
et tous les compteurs actifs/réservations sont à zéro. Les pertes de réponse
du banc et les transitions rares d'observation n'ont qu'une revue statique ;
les autres pannes et la régression complète restent au backlog SLS-074.

## Nommage des validateurs — SLS-076 qualifiée

Le [contrat](../docs/VALIDATOR_NAMES.md) fixe le préfixe explicite et la reprise
des anciens noms par labels. `node e2e/validator-names.mjs` exige la nouvelle
image construite mais l’ancien contrôle encore servi, une session SSO réelle
et SSH root du seul SPARK. Le premier groupe observe le vrai p2-v d’un upload
HTTPS, arme la garde, interrompt le contrôle puis démarre la nouvelle image
avant toute ancienne reprise. Trois autres groupes éprouvent un import réussi
dédupliqué, un refus et un timeout, avec noms/marqueurs/isolation vivants relus.
Les compteurs données/cache, configuration et cible stable sont recoupés.

`validator-names-operator.py` est l’opérateur interne : observation, interruption
gardée et remise en service Compose DEV. Il refuse une inspection incertaine,
une configuration différente ou une seconde création aveugle. Les rapports
préexistants doivent être conservés avant essai. Les
[cinq commandes maintenues](../docs/VALIDATOR_NAMES.md#commandes-reproductibles-du-banc)
préparent, construisent, exécutent, rejouent les régressions et collectent la
preuve depuis la racine. Le
[replay qualifié](../docs/evidence/validator-names-dev-2026-11-09.json) passe57
groupes : quatre ciblés et36/12/5 connexes, sur258 sources figées. Trois
fonctions du replay sont purgées ; cinq appels conservent les compteurs1 à5.
Le départ SSO et l’arrêt Compose cwd sont distincts, sans groupe ajouté au
replay. Le web est byte-identique ; aucune capture/UI fraîche n’est revendiquée.
Les pilotes maintenus ont leurs corps exécutés et leur provenance dans le
relevé de livraison, distinct de l’époque258 des clients.

## Migration et exécution des versions par hash — checkpoint ciblé008

`node e2e/function-versions-upgrade.mjs prepare` crée par les API du vrai
checkpoint007 des alias A/A/B, un rollback et des données/cache. Il exige la
session SSO normale, conserve son état privé en0600 et refuse de le remplacer.
Après sauvegarde native, construction et bascule du seul contrôle DEV vers008,
`verify` recoupe alias, cible, marqueurs historiques, appels sans tag et épinglés,
puis données/cache. `persist` exige un redémarrage réel préalable ; `cleanup`
supprime et purge les objets par les API puis leurs parents. Chaque phase est
distincte et séquentielle ; les rapports incomplets restent des échecs.

La fixture originale `qualification/artifacts/function-versions.cjs` est
empaquetée, publiée et exécutée par Docker. Le client ne l’importe pas. Ce banc
qualifie le périmètre ciblé décrit ci-dessous ; les autres critères restent dans [FUNCTION_VERSION_EXECUTION](../docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles).

Le premier replay008 passe les quatre phases, dont préparation et nettoyage
distincts des deux scénarios migration/reprise. `node e2e/function-versions-api.mjs`
passe douze groupes. Son helper `function-version-artifacts.py` lit uniquement
les artefacts et réservations de l’UUID exact dans son namespace de campagne ;
le recoupement physique du doublon avant purge est ajouté après la revue.
`node e2e/function-versions-cli.mjs` passe cinq groupes authentifiés par le vrai
processus Python du poste, avec six appels des URL émises sur les deux domaines.
Cette exécution est distincte des24 groupes plan/package et14 refus publics
dans les deux images CLI. La déclinaison authentifiée passe désormais cinq
groupes par image, selon le complément ci-dessous ; pannes et régression complète
restent nécessaires. Les six groupes UI et huit
du manuel passent désormais, avec28 captures inspectées et nettoyage natif de
dix fonctions. Le [checkpoint71](../docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json)
conserve séparément les images, sources et essais interrompus.

`node e2e/function-versions-ui.mjs` part de l’accueil et des formulaires, puis
éprouve versions, presse-papiers natif, promotions, retraits/réimportations et
dialog conservé pendant la publication réelle d’un sixième hash. Le premier
essai est incomplet sur un corps PUT200 évincé avant sa lecture ; son nettoyage
réel est confirmé. La preuve observe le PUT réel (URL et statut), relit son candidat durable
par l’API authentifiée et recoupe le message réellement affiché par la console.
Le corps PUT n’est pas déclaré observé ; les essais de collecte CDP incomplets
sont conservés avec leurs nettoyages, distincts du replay.

### Commandes CLI authentifiées dans les images — cinq groupes par image

`node e2e/function-versions-cli.mjs --docker cli`, puis séparément
`node e2e/function-versions-cli.mjs --docker qualification`, rejouent les cinq
groupes dans les deux images DEV. SSH vers le seul SPARK et vraie session SSO
sont requis. `function-version-cli-container.py` reçoit les données privées sur
stdin ; les sources et images sont recoupées, le conteneur est borné et son
absence est vérifiée. Les rapports CLI Docker distincts n’écrasent pas le rapport
hôte du checkpoint71. Le [complément qualifié](../docs/evidence/function-version-cli-images-dev-2026-11-09.json)
recoupe245 sources avant/après, vingt clients disparus, douze invocations sur les
deux domaines et deux fonctions purgées. Le premier essai direct est conservé
avec zéro groupe réussi et ses parents nettoyés. Compose DEV lit les valeurs
citées des fichiers officiels ; aucun fichier de cellule n’est modifié. Les
pannes propres du helper et ses délais restent non qualifiés par ces scénarios.

### Nettoyage de validation avec un upload en attente — quatre groupes

`node e2e/function-version-validation.mjs` vise quatre groupes réels : défaut
socket et reprise, défaut du canal isolé et reprise après SIGKILL du helper.
Il utilise la session SSO et SSH root du seul SPARK DEV, exige sa quiescence et
arme une garde indépendante avant chaque changement de permission. Contrat :
[FUNCTION_VERSION_VALIDATION_RECOVERY](../docs/FUNCTION_VERSION_VALIDATION_RECOVERY.md).
Le second upload doit déjà être admis ; son refus503 précis et les événements
Docker évitent une preuve vide. Le [replay qualifié](../docs/evidence/function-version-validation-recovery-dev-2026-11-09.json)
passe quatre groupes, cinq invocations et deux restitutions ; la préparation
stable reste distincte des groupes. Les248 sources sont recoupées, le contrôle
ne redémarre pas. Deux fonctions sont purgées, y compris celle de l’essai sur la
mauvaise clé detail, corrigée vers error. L’arrêt SSO antérieur ne crée aucun
objet. Les helpers, unités, canaux et artefacts du replay sont recoupés absents ;
les autres pannes et la régression complète restent ouvertes.

## Pause et reprise d’une requête réelle

`node e2e/invocation-request-pause.mjs` publie sa fixture originale dans le SPARK
DEV, puis retient le vrai GET HTTPS du catalogue après réception sur 18090.
Deux groupes passent : libération explicite et SIGKILL du traceur avec reprise
confirmée par son programme indépendant. La même requête termine à 200, avec
deux domaines ; sa fin n’est pas datée par rapport au SIGCONT de la garde.
Le helper `invocation-request-pause.py` ne remplace aucune réponse et conserve
le contrôle et son démarrage. SSH root et session SSO réelle sont requis.
Le collecteur recoupe deux fonctions purgées dans deux namespaces et quatre
gardes finies, en incluant séparément le premier essai interrompu et son
diagnostic. [Preuve](../docs/evidence/invocation-request-pause-dev-2026-11-09.json).
Ces deux groupes ne modifient aucune route. Le complément UI ci-dessous prouve
la survie de la connexion pendant réapplication ; les fautes propres du pilote
restent à éprouver.

## Catalogue global SLS-067 qualifié

`node e2e/function-catalogue-api.mjs` passe huit groupes avec 32 fonctions,
recherche globale, filtres, droits, publication A/B, invocation Docker et rollback.
`node e2e/function-catalogue-ui.mjs` passe quatorze groupes avec un jeu de 27
fonctions, départ de l’accueil et créations par la gestion. Ses seize prises
de vue comprennent la table mobile à gauche, au milieu et à droite.
Les nettoyages et les variables/secrets des services sont recoupés physiquement.

`python3 -B e2e/execution-suite.py --scope function-catalogue` prépare le SSO par
stdin privée et lance le parcours intégral : 37 campagnes, 489 groupes attendus
et six prérequis distincts. Les anciens clients rejoignent Namespaces par
la navigation après le nouvel accueil Fonctions ; le banc historique utilise
toujours sa vraie image antérieure et son accueil Namespaces.

La [preuve courante](../docs/evidence/function-catalogue-dev-2026-11-08.json) est
une continuation contrôlée, pas un succès rétroactif de la commande initiale.
Le premier arrêt du canal privé reste séparé ; sa
[correction ciblée](../docs/evidence/private-channel-lifecycle-dev-2026-11-08.json)
passe onze groupes. Le second essai passe 31 campagnes / 461 groupes puis
s’arrête sur l’ancien retour racine dans le client stockage UI ; ses sept
groupes partiels, ses huit images et son nettoyage restent archivés.

`python3 -B e2e/function-catalogue-completion.py` a conservé 30 campagnes aux
clients inchangés (447 groupes), puis réexécuté les deux clients retouchés et
les scénarios restants (42 groupes). Les 37 noms sont uniques, les images et
sources produit identiques, les époques 196/197 explicites. Le pilote exige
l’archive locale exacte et les écarts précis de son gel ; les mises à jour
documentaires postérieures peuvent refuser sa réexécution. Pour une nouvelle
qualification du dépôt livré, utiliser le scope intégral ci-dessus.

Les six prérequis sont distincts des 489 groupes. Le collecteur garde trois
jeux d’UUID bornés : 23 namespaces / 91 fonctions. Les 39 fonctions des jeux
écartés sont recoupées séparément. Les 98 captures actives sont inspectées et
le manuel compilé correspond à 15 chapitres / 46 paragraphes. Contrat détaillé :
[FUNCTION_CATALOGUE](../docs/FUNCTION_CATALOGUE.md).

Les clients de ce répertoire visent exclusivement le déploiement DEV réel.
Ils n'importent pas les handlers, ne créent pas de serveur substitué et
n'interceptent aucune réponse réseau. Le navigateur utilise la connexion SSO
normale. Un accès absent est une erreur de prérequis, jamais un test ignoré.

## Adresses d’appel SLS-066

### Pagination réelle sur six domaines — campagne qualifiée

Le [plan autorisé](../docs/INVOCATION_DOMAINS_PAGINATION.md) borne quatre alias
temporaires à infra-serverless,18090TLS et quatre A exacts. L’opérateur
`invocation-pagination-domains.py` utilise la console normale locale existante,
sans administration système de Forge. Ses reçus privés conservent intentions
et identités ; aucun appel de mutation n’est automatiquement répété.

Le pilote `python3 -B e2e/invocation-pagination-suite.py --guard-prerequisites`
éprouve d’abord release, échéance et perte du propriétaire, sans créer d’objets.
Puis, séparément, `--campaign` exige le même gel de sources/images, crée les
quatre alias, attend DNS natif et TLS réel, exécute UI puis CLI, recoupe les
purges physiques et termine par la perte réelle du propriétaire et le retrait
indépendant. L’exécution nécessite la console normale sur127.0.0.1:5175,
SSH root du seul SPARK, Node/Playwright/Python et une session SSO admin fraîche.
Les rapports existants doivent être conservés avant un nouvel essai.

`invocation-pagination.mjs ui DOSSIER_GARDE` et `cli DOSSIER_GARDE` sont les
clients internes, trois groupes chacun. Le CLI passe d’abord les deux pages,
rejoue la frontière historique six avec révocation réelle, puis retire une
route temporaire connue avant la septième connexion pour faire changer le
catalogue. Le helper natif conserve sa frontière six par défaut. Les captures
JPEG, logs et reçus vivent sous.local/e2e ; leurs assertions ne remplacent pas
leur inspection visuelle. Le [replay qualifié](../docs/evidence/invocation-pagination-dev-2026-11-09.json)
passe huit groupes (deux de cycle, trois UI, trois CLI) et trois prérequis de
garde distincts, sur253 sources figées. Quatorze invocations Docker, sept JPEG
inspectés, deux fonctions physiquement purgées et quatre routes/A retirés
indépendamment après SIGKILL du propriétaire sont recoupés. Les deux captures
viewport mobiles sont identiques par SHA. Le premier A créé puis retiré par le
principal reste un essai arrêté sans groupe UI/CLI ; les deux époques de garde
antérieures ne s’ajoutent pas au total. La transition d’état de zone après
écriture est corrigée ; les pannes résiduelles du banc restent non qualifiées.

`node e2e/invocation-route-cycles.mjs` exerce les seules deux routes autorisées
depuis la console normale existante : cinq groupes réels passent, sept appels
Docker des URL émises, quatre gardes terminées et une fonction purgée dans un
namespace. Le [contrat opératoire](../docs/INVOCATION_ROUTE_CYCLES.md) fixe la
fixture, l’armement et la restauration. La
[preuve](../docs/evidence/invocation-route-cycles-dev-2026-11-09.json) recoupe
203 sources, le catalogue à deux/un/zéro domaines et le nouvel identifiant
d’alias après retrait/rétablissement. Les ports finaux restent 18090 TLS.
Le vide UI public et les pages UI/CLI sur six domaines sont qualifiés par leurs
compléments distincts, décrits dans ce guide.

`native_control_observer.py` porte la classe pure partagée avec le pilote
historique `service-transport-observer.py`. Son corps est déplacé sans changement.
Synchroniser le module dans le même répertoire E2E avant le pilote consommateur.
La [preuve d’extraction](../docs/evidence/invocation-native-observer-dev-2026-11-08.json)
passe `node e2e/invocation-url-transport.mjs` puis `node e2e/service-transport.mjs`
en série : neuf groupes, 201 sources recoupées, six fonctions purgées et six
gardes terminées. Le pilote pause/libération est qualifié dans son complément ci-dessus ;
l’ancien mode `catalogue-before` conserve son comportement de destruction.

La garde des cycles de routes reste en qualification. Depuis ce dépôt sur le
poste qui héberge la console normale, exécuter
séparément `python3 -B e2e/invocation-route-lifecycle.py --guard-baseline-only`,
puis `--guard-owner-loss-only` et `--guard-deadline-only`. Chaque scope refuse
de remplacer son rapport existant : archiver les résultats avant replay.
Les trois passent sur le vrai relais de console et les HTTPS publics, avec
fin confirmée du processus indépendant, sans aucune perturbation de route :
[preuve positive](../docs/evidence/invocation-route-guard-dev-2026-11-08.json).
Le premier essai d’échéance s’est arrêté sur le HTTPS de l’alias ; l’ancien
cache DNS négatif a ensuite expiré avant le replay. Le
[checkpoint incomplet](../docs/evidence/invocation-route-guard-checkpoint-dev-2026-11-08.json)
garde cet arrêt et son diagnostic séparés. Les détours et le retrait font ensuite
l’objet de la preuve séparée des cinq cycles réels décrite ci-dessus.

Le complément à deux domaines réels passe huit groupes API/CLI et six UI sur
`serverless.lelabs.tech` et `functions.lelabs.tech`, tous deux en HTTPS vérifié.
Quatre fonctions sont purgées dans deux namespaces et recoupées nativement.
Sa [preuve distincte](../docs/evidence/invocation-domains-dev-2026-11-08.json)
conserve aussi les arrêts initiaux : déclaration effective suivie d’une
comparaison trop stricte de `applied_at`, puis premier départ API sans session
valide avant création d’objet. La vérification de l’installation et le replay
réussis ne réécrivent aucun de ces essais en succès.

`python3 -B e2e/invocation-domain-console.py inspect` consulte la console normale
déjà en fonctionnement. `apply-authorized-alias` est une opération de mise en
service unique, limitée au nom expressément autorisé ; un reçu existant refuse
son rejeu. Le premier reçu incomplet reste conservé.
`verify-installed-alias` est la reprise en lecture seule de ce reçu précis :
identités, DNS et propriétés matérielles, puis véritables HTTPS des deux noms,
sans renvoyer les créations. Aucun de ces clients ne constitue un chemin
d’administration de FORGE. Les retraits/détours sont qualifiés par les cinq cycles ; les pages sur six
domaines restent à éprouver séparément et SLS-066 demeure ouverte.

Exécuter séparément et en série `node e2e/invocation-urls.mjs` puis
`node e2e/invocation-urls-ui.mjs`, avec la session SSO réelle préparée selon
le protocole stdin ci-dessous. Le premier passe huit groupes API/CLI avec
publication et appels Docker ; le second six groupes depuis la création UI,
publication ZIP, copie native et invocation, refus natif du presse-papiers,
coupure réseau, clavier et mobile. Le collecteur suit la destination UI créée
sans dépendre du corps de réponse libéré par sa navigation. Le nettoyage
retrouve aussi les objets de son nom exact si une réponse est perdue.

Le [checkpoint](../docs/evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
réunit ces quatorze groupes, 36 régressions et 38 groupes dans les deux images
CLI reconstruites, soit 88. Chaque commande est liée à ses sources et image. Il ne constitue
pas une suite complète de plateforme ni une qualification multi-domaines.
Les autres fautes de source restent à éprouver ; la seconde page UI/CLI réelle
sur six domaines est qualifiée par son complément distinct ci-dessus. Les cycles de routes sont
qualifiés séparément dans le complément à cinq groupes décrit ci-dessus.
Aucun de ces manques n’est converti en test ignoré dans les campagnes exécutées.

Le scope complet `python3 -B e2e/execution-suite.py --scope invocation-urls`
est [qualifié en DEV](../docs/evidence/invocation-urls-regressions-dev-2026-11-08.json) :
35 campagnes / 467 groupes sans doublon, zéro échec/skip,
avec le même protocole stdin privée que stockage. Ses six prérequis ne gonflent
pas le décompte ; le recoupement détaillé de dix namespaces / 32 fonctions reste séparé
des nettoyages propres aux autres campagnes. Le contrat
[INVOCATION_URLS](../docs/INVOCATION_URLS.md#suite-complète-de-preuve) fixe ordre,
images CLI, frontières natives et limites de cette suite. Les 186 sources sont
identiques avant/après chaque phase. Les 32 fonctions suivies sont purgées,
les deux restaurations historiques séparées et les 26 fichiers embarqués
recoupés. Les 79 captures fraîches comprennent 61 observations et 18 identités
SHA avec une référence inspectée. Le vrai Host est éprouvé sur la boucle locale,
sans constituer une preuve d’alias public/TLS. Le build CLI nominal passe ; sa
branche d’expiration ou perte SSH reste à éprouver. SLS-066 demeure ouverte.

Le [checkpoint de coupure](../docs/evidence/invocation-url-transport-dev-2026-11-08.json)
passe trois groupes sur le vrai contrôle
DEV avec garde indépendante, publication conservée
malgré le GET interrompu et six connexions HTTPS CLI sans rejeu. Lire son
[contrat](../docs/INVOCATION_URLS.md#perte-native-du-catalogue-après-publication-cli)
avant lancement ; aucune autre campagne ne peut être active. Les cinq groupes
de transport historique puis huit API/CLI repassent, soit 16 groupes en série,
avec 187 sources, huit fonctions purgées dans trois namespaces et six gardes
terminées. Le refus après publication est qualifié séparément par le 401 ci-dessous.
Le rapport propre est
`.local/e2e/invocation-url-transport.json`, sans modifier la preuve des 467 groupes.
La reprise de purge suit l’UUID archivé et le reçu ; le groupe CLI doit avoir
disparu avant nettoyage. Les branches d’expiration/sortie excessive/lancement
et les nettoyages après réponses de création/purge perdues restent non éprouvés.

Le client courant `node e2e/invocation-url-transport.mjs` passe quatre groupes,
dont la révocation décrite dans
[révocation avant GET](../docs/INVOCATION_URLS.md#révocation-avant-le-get-facultatif) :
le pilote local adapter-catalogue-barrier.py retient la véritable CLI avant
sa sixième connexion, puis une révocation API produit le vrai 401.
Le [replay réussi](../docs/evidence/invocation-url-refusal-dev-2026-11-08.json)
passe ensuite cinq groupes historiques et huit API/CLI, soit 17 au total,
avec 188 sources et neuf fonctions purgées dans trois namespaces. Les six gardes
et 26 fichiers embarqués sont recoupés. L’essai initial incomplet est conservé
avec ses deux fonctions et gardes nettoyées ; la cause de sa barrière manquée
reste inconnue. Le brut physique est archivé avant enrichissement. Le refus
403 et les pannes propres du pilote/diagnostic restent non éprouvés.

## Configuration commune du service

`node e2e/service-configuration.mjs` exige la session SSO réelle de
`.local/e2e/admin-session.json`. Ses treize groupes publient les handlers
originaux de `qualification/artifacts/service-configuration.cjs` puis les
invoquent par HTTPS dans Docker. Ils couvrent valeurs communes, surcharges,
rotation pendant un appel, retrait d’une surcharge, droits de service, échec
partiel, reprise d’une configuration aplatie, limites ASCII/Unicode et redémarrage
du contrôle. Les ressources sont purgées par l’API publique ; le rapport conserve
leurs UUID et les opérations de purge. Un prérequis absent fait échouer le banc.

La [preuve SLS-031](../docs/evidence/service-configuration-dev-2026-11-08.json)
recoupe les empreintes avant/après chaque campagne. Rejouer en série depuis la
racine : `node e2e/service-configuration.mjs`, `python3 -B e2e/adapter.py`,
`python3 -B e2e/adapter-deploy-public.py`, `node e2e/adapter-deploy.mjs`,
`node e2e/deployments.mjs`, `node e2e/control-admin.mjs`,
`node e2e/control-ui.mjs`, `node e2e/manual-ui.mjs`,
`node e2e/function-storage.mjs`, puis `python3 -B e2e/public-invocations-suite.py`.
Le client de refus public requiert `QUALIFICATION_SYNTHETIC_SECRET`, une valeur
synthétique privée de qualification fournie au processus. Il ne doit pas recevoir
de secret métier. Cette suite compte 153 groupes ; les images de CLI sont ensuite
construites et ses commandes `test` et `deploy-public-test` rejouent 38 groupes
dans le SPARK, selon [adapter/README](../adapter/README.md).

Les deux fonctions ciblées sont recoupées au repos par
`storage-console-inspect.py`, avec le mapping exact namespace → UUID des fonctions.
La preuve lie aussi les 25 fichiers Python/migrations du contrôle et les cinq
modules CLI embarqués à leurs sources. Le manuel est relu depuis l’accueil et
son empreinte est comparée à `docs/manual.md` ; ses 39 paragraphes sont vérifiés.

Le [complément de transport](../docs/evidence/service-configuration-transport-dev-2026-11-08.json)
qualifie cinq groupes supplémentaires, puis rejoue les treize groupes ci-dessus.
Lancer `node e2e/service-transport.mjs` seul depuis le poste, après synchronisation
des sources E2E dans le SPARK. Il exige `strace` sur le poste, la session SSO et
l’accès root au seul SPARK DEV x86_64. Son helper `service-transport-observer.py`
refuse une installation occupée, arme une garde systemd indépendante, puis
observe le vrai processus Uvicorn. Il le tue avant traitement ou après commit
mais avant émission de réponse, et rétablit son conteneur original. Une perte
du helper éprouve aussi la restauration indépendante. Les connexions HTTPS du
vrai processus CLI sont comptées nativement, sans lecture de ses données TLS.
Aucun serveur, middleware ou réponse n’est substitué. Ce banc interrompt
temporairement la disponibilité de la console DEV ; aucune autre campagne ne
doit être active. Le rapport est `.local/e2e/service-transport.json`.

Après cette commande, rejouer `node e2e/service-configuration.mjs`, puis recouper
les deux mappings namespace → UUID des fonctions avec `storage-console-inspect.py`
sous root dans le SPARK. Les rapports conservent `namespace_id` et `function_ids`.
Le complément recoupe quatre fonctions purgées, treize artefacts absents, les
25 fichiers embarqués du contrôle et les trois gardes inactives. Ses 167 sources
sont liées avant/après chaque campagne ; le checkpoint historique de 191 groupes
conserve son index de 165 sources et ses captures, sur la même image produit.

## Stockage public et manuel

Les commandes `python3 -B e2e/execution-suite.py --scope storage-console-focused`
et `--scope storage-console` intègrent désormais les campagnes ci-dessous.
Le premier scope passe sept campagnes et 37 groupes réels dans le
[checkpoint ciblé](../docs/evidence/storage-console-focused-dev-2026-11-08.json) :
173 sources liées avant/après, 24 fonctions purgées dans six namespaces,
deux restaurations historiques distinctes, 25 sources embarquées et quatorze
captures UI inspectées. Le scope complet passe 29 campagnes et 397 groupes
dans la [preuve complète](../docs/evidence/storage-console-dev-2026-11-08.json),
avec 72 captures recoupées, puis neuf groupes API rejoués et renforcés. Les deux
phases gardent leurs empreintes distinctes ; les nouvelles assertions ne sont
pas attribuées au replay antérieur.

Ces deux scopes reçoivent une ligne JSON `username`/`password` sur stdin privée.
Le runner coupe lui-même l’écho d’un terminal et ne conserve pas cette entrée.
`dev-sso-sessions.mjs` ouvre deux vrais parcours accueil → SSO dans des contextes
neufs, enregistre seulement les cookies de plateforme dans `admin-session.json`
et `purge-admin-session.json` privés, puis vérifie leur différence. Le build
historique et le recoupement physique sont des prérequis, sans groupes ajoutés.
Une nouvelle paire de connexions est préparée immédiatement avant la campagne
de décision ; son rapport distinct est `dev-sso-decision-sessions.json`.
Le cookie de purge inutilisé peut ne plus être renouvelable après une longue
suite : les durées SSO restent appliquées normalement. Les deux scopes comptent
donc quatre prérequis, sans modifier leurs 37 ou 397 groupes fonctionnels.
Les rapports de suite sont `.local/e2e/storage-console-focused.json` et
`.local/e2e/storage-console-regressions.json` ; le recoupement final est
`.local/e2e/storage-console-physical.json`. Les identifiants ne rejoignent ni
arguments de commande, ni variables d’environnement, ni rapports ou fichiers.

Les archives antérieures au registre ont leur [contrat de banc](../docs/STORAGE_LEGACY_PROOF.md).
Après synchronisation des sources, lancer séparément et en série :

```sh
python3 -B e2e/storage-legacy-build.py
node e2e/storage-legacy-recovery.mjs --partial
node e2e/storage-legacy-recovery.mjs --full
```

Le build reconstruit exactement `93f88e5` dans une image historique distincte.
Le mode partiel interrompt réellement le pilote après le premier renommage et
vérifie la restauration indépendante. Le mode complet reçoit les identifiants
de connexion SSO en JSON sur stdin (`username`, `password`), sans les conserver
ni les afficher ; utiliser une entrée sans écho et jamais un argument de commande
ou un fichier versionné. Il ouvre la connexion normale dans le navigateur, puis
publie et supprime deux fonctions via l’ancienne API. Quatre groupes couvrent
ce parcours, sa migration réelle, la purge sans registre et une apparition
contradictoire après décision, avec conservation du code après redémarrage.

Ces commandes ouvrent une fenêtre sur le seul contrôle DEV : les trois répertoires
officiels sont conservés puis restaurés par identité. `storage-legacy-environment.py`
arme la garde indépendante, utilise les deux env_file de cellule et conserve ses
journaux/backups privés sous `qualification-history/storage-absence-<UUID>`.
Le mode `status <UUID>` lit l’état de restauration ; le mode `restore <UUID>`
joint le pilote et ses commandes avant de rétablir les originaux. La commande
contradictoire demeure volontairement en attente dans son installation temporaire,
retirée entièrement après observation. Ce retrait n’est pas une purge métier réussie.

La [preuve corrigée](../docs/evidence/storage-legacy-recovery-dev-2026-11-07.json)
réunit cinq groupes historiques/restauration, deux de validation vivante, sept de
commandes sous panne et huit du manuel. La [preuve avant correction](../docs/evidence/storage-legacy-cleanup-defect-dev-2026-11-07.json)
conserve l’échec réel. Ces campagnes sont maintenant intégrées au scope ciblé ;
les régressions élargies sont recoupées dans la preuve complète du 8 novembre.

Après synchronisation des sources sur le SPARK, exécuter successivement depuis
la racine `node e2e/storage-console-api.mjs`, `node e2e/storage-console-ui.mjs`,
`node e2e/manual-ui.mjs`, puis `node e2e/control-ui.mjs`. Les campagnes ciblées
passaient respectivement neuf, neuf, huit et onze groupes dans le checkpoint initial.
La campagne UI courante passe dix groupes : elle crée onze brouillons et les
archive depuis la console avant d’exercer les deux pages, puis purge ses douze
fonctions. Le rapport `campaigns` contient leur mapping exhaustif. La preuve reste
un [checkpoint SLS-065](../docs/evidence/storage-console-checkpoint-dev-2026-11-07.json) :
les pannes, reprises et régressions figurent désormais dans la preuve complète.

`node e2e/storage-command-recovery.mjs` ajoute sept groupes réels : perte du
helper avec restauration indépendante, indisponibilité de l’agent, révocation
avant décision, collision avec une autre garde, SIGKILL avant/après décision,
pannes physiques de cache et d’artefacts avec reprise. Le reçu garde le même
UUID et un rejeu après reconstruction du cache ne l’efface pas une seconde fois.
Le helper `storage-command-faults.py` borne les perturbations par des gardes
systemd et vérifie le rattachement des fonctions à la campagne avant chaque geste.
Les trois fonctions sont purgées par l’API ; `storage-console-inspect.py`
recoupe ensuite leur nettoyage physique. La
[preuve de reprise](../docs/evidence/storage-command-recovery-dev-2026-11-07.json)
conserve sept groupes de reprise, quinze de régression des mutations et huit du
manuel, exécutés en série. Elle reste un checkpoint ; la validation vivante est
éprouvée par la campagne suivante ; pannes et régressions sont recoupées dans
la preuve complète du 8 novembre.

`node e2e/storage-validation-recovery.mjs` ajoute deux groupes : perte réelle du
helper avec restauration indépendante du socket Docker, puis purge pendant un
import encore vivant et nettoyage du diagnostic tardif. Le module original
`qualification/artifacts/storage-validation-delay.mjs` écrit un marqueur puis
attend soixante secondes à l’import, face au délai normal de validation de quinze
secondes. `storage-validation-faults.py` refuse temporairement le socket rootless
au contrôle, après rattachement du validateur à la campagne et armement d’une
garde systemd ; il conserve le propriétaire, le groupe et le mode réels du socket.
La reprise et les effacements sont réalisés par le produit. Les deux fonctions
sont ensuite purgées via leurs API publiques. Synchroniser ces sources et la
fixture avant de lancer cette campagne seule, après la fin de tout autre test.

La campagne `storage-console-api.mjs` conserve neuf groupes et ajoute le conflit
d’un UUID entre vidage et purge, puis la réutilisation des noms de namespace,
service et fonction avec de nouveaux UUID. Elle vérifie que purger l’ancienne
archive préserve les données et le cache de la nouvelle fonction. Son champ
`campaigns` associe exactement les quatre fonctions aux deux namespaces ; les
champs historiques `namespace_id` et `function_ids` ne forment plus cette relation.
La [preuve](../docs/evidence/storage-validation-recovery-dev-2026-11-07.json)
recoupe ces onze groupes exécutés en série, leurs sources et l’image inchangée.
Elle conserve aussi l’échec initial de précontrôle, corrigé avant la relance,
et le nettoyage physique des huit fonctions et neuf répertoires de code des essais.

`node e2e/storage-decision-recovery.mjs` ajoute quatre groupes : session
administrateur révoquée pendant une préparation de purge, refus du transport
agent après décision, writer SQLite réellement occupé après décision, puis
redémarrage du contrôle par sa garde indépendante. Elle partage le helper
`storage-command-faults.py`, dont les sept groupes de reprise sont rejoués ensuite.
La [preuve des décisions](../docs/evidence/storage-decision-recovery-dev-2026-11-07.json)
recoupe les onze groupes, les six fonctions purgées, la libération des verrous,
la restauration des services/sockets et les sources inchangées entre campagnes.

Cette campagne exige deux connexions SSO indépendantes : conserver l’état de la
première dans `.local/e2e/purge-admin-session.json`, puis obtenir une nouvelle
connexion pour `.local/e2e/admin-session.json`. `authorize.mjs` produit l’état de
chaque connexion réelle ; déplacer son premier résultat avant la seconde connexion.
Le premier cookie est consommé par la véritable déconnexion testée. Il faut donc
une nouvelle connexion de purge avant toute relance ; recopier le cookie actif
de l’observateur est refusé. Les deux fichiers restent privés, en mode 0600.
Les scopes `storage-console-focused` et `storage-console` automatisent ces deux
connexions réelles par `dev-sso-sessions.mjs` à partir de l’entrée privée stdin.

Sous contention, le diagnostic SQLite est lu dans le journal réel, car son
écriture en base peut elle-même échouer. Le writer ne modifie aucune ligne ;
sa libération après SIGKILL est recoupée par une nouvelle acquisition. Le secours
de redémarrage attend un verrou natif conservé par la commande Docker, bornée
par un processus `timeout` indépendant. Il retire le fichier privé après reprise.
Le client attend ensuite le retour de l’API, dont la santé peut rester dégradée
tant que la panne volontaire de cache n’est pas levée.

Les campagnes stockage créent leurs ressources et les purgent par leurs
API publiques. Le rapport exige `completed`, `cleanup` et zéro test ignoré.
La campagne navigateur perd réellement une réponse, conserve l’UUID puis
reprend sa lecture sans second POST ; la pagination subit une vraie coupure
réseau du navigateur. Aucune interception de réponse n’est utilisée.

Au repos, `storage-console-inspect.py` s’exécute comme root du seul SPARK DEV,
avec un argument JSON associant chaque `namespace_id` à la liste exhaustive
de ses fonctions. Lire le champ `campaigns` lorsqu’il existe ; pour les anciens
rapports à un seul namespace, utiliser `namespace_id` et `function_ids` (ou
`[function_id]` pour la campagne UI). Un essai échoué peut aussi être inspecté
si son nettoyage a réussi ; il reste identifié comme échoué dans la preuve.
Le collecteur lit les deux bases sous leur propriétaire `spark-docker`,
recoupe reçus, budgets, artefacts, montages, canaux et ressources Docker, puis
vérifie le vide des secrets dans le conteneur sans en sortir leur valeur.
Les inventaires trash et canaux non attribuables doivent être globalement vides.
Le collecteur ne supprime rien ; toute ressource restante fait échouer la preuve.
L’appelant doit conserver les empreintes des rapports et du collecteur avec
son résultat pour rattacher les UUID aux campagnes effectivement exécutées.

Le manuel est recoupé intégralement avec `docs/manual.md` : treize chapitres,
39 paragraphes et empreinte SHA256. Ses onze captures comprennent les nouveaux
chapitres cache et archives sur ordinateur et mobile ; elles doivent être relues.

## Banc et campagnes

Installer les dépendances par `npm ci`, puis le navigateur par
`npx playwright install chromium`. Exécuter un seul scénario à la fois.
Les captures et fichiers contenant une session sont conservés uniquement
sous `.local/`, ignoré par Git. Ne jamais publier un état de navigateur.

Depuis la racine du dépôt, chaque commande attend la fin de la précédente :

```sh
python3 e2e/public.py
node e2e/login-ui.mjs
node e2e/authorize.mjs
node e2e/control-admin.mjs
node e2e/control-ui.mjs
node e2e/deployments.mjs
node e2e/adapter-deploy.mjs
node e2e/publication-recovery.mjs
node e2e/function-storage.mjs
python3 -B e2e/public-invocations-suite.py
```

`python3 e2e/proxy.py --expected-proxy 10.77.0.1` s'exécute depuis le poste et
mesure les chemins réseau via HTTPS et SSH. Les pilotes `login-limits.py`,
`login-capacity.py` et `control-operations.py` s'exécutent comme `spark-docker`
dans le SPARK DEV. Les deux premiers exercent les limites SSO ; `login-limits`
redémarre aussi le contrôle. Le dernier utilise des conteneurs temporaires de son image immuable pour les
pannes de configuration, de clé et de base, le verrou exclusif d’état et la
reprise de maintenance après une contention SQLite réelle. Les fichiers `.proof-*.json`
produits sous `/srv/p2enjoy-serverless/control` contiennent les résultats
expurgés. Leurs ressources temporaires sont nettoyées après chaque campagne.
`python3 e2e/report-interruption.py`, depuis le poste après `public.py`, tue
réellement un client de preuve après son premier échange HTTP, vérifie que
l'ancien rapport réussi est invalidé, puis rejoue la campagne publique.
Les rapports ne valent que lorsque `completed` est vrai et les nettoyages
réussis ; leur initialisation précède les prérequis externes.

`python3 e2e/execution-suite.py` rejoue en série les quatorze campagnes du
moteur et de régression sur le SPARK DEV. Chaque commande attend la fin de
la précédente ; les rapports sont vérifiés comme fraîchement régénérés et
rattachés à leurs empreintes, aux sources locales et à l’image du contrôle
observée avant et après chaque campagne. Une modification pendant la suite
ou un prérequis absent provoque un échec. Le journal atomique est
`.local/e2e/execution-regressions.json` ; les 31 groupes d’invocations sont
exécutés en dernier. Les propositions de notes et la revue visuelle restent
des étapes de clôture distinctes.

`authorize.mjs` ouvre Chromium sur l'accueil de la console et laisse jusqu'à
huit heures au détenteur du compte pour démarrer la connexion SSO. Aucun flow
OAuth n'est créé avant son clic, ce qui évite une expiration pendant l'attente.
Le script ne lit aucun champ de mot de passe.
Il conserve seulement le cookie de plateforme, sous `.local/e2e/` en mode
0600, puis ferme le navigateur. Les cookies du fournisseur ne sont pas
exportés. Les campagnes de gestion et de publication exigent cette vraie session ; son
absence fait échouer leur prérequis.

`control-admin.mjs` crée ses propres objets, qualifie les droits CRUD et
redémarre le conteneur de contrôle du SPARK DEV pour éprouver la persistance.
`control-ui.mjs` crée ses objets depuis la console et augmente temporairement
la latence réelle de Chromium pour vérifier un envoi en cours ; il ne remplace
aucune réponse. Les deux nettoient uniquement les objets qu'ils ont créés.

Les scripts et preuves sont ajoutés au rythme de SLS-020 à SLS-063. Les premiers
contrôles publics, les 19 groupes API administrateur et les 11 parcours UI
ont réussi avec nettoyage confirmé. La [preuve de gestion](../docs/evidence/control-management-dev-2026-11-06.json)
recoupe l'image et les sources ; les cycles de rôles et de clés SSO ainsi que
la campagne complète de plateforme restent ouverts.
La campagne publique comporte huit groupes : découverte OIDC et clés réelles,
santé TLS, ressources de la console, refus anonymes, callbacks malformés,
flows et refus du fournisseur, bornes des corps, puis refus anonymes des routes
de publication. Un upload HTTPS utilisant Expect: 100-continue est refusé
avant l’envoi du corps de 64 Mio annoncé. La cible d'autorisation
est comparée à la découverte fraîchement lue. Les règles de client et de rôle
restent à éprouver par leurs parcours authentifiés.

`python3 e2e/adapter.py` exécute les vraies commandes plan/package sur une
copie temporaire des fichiers de qualification. Il examine les ZIP produits
et exerce les refus, les liens physiques/symboliques ainsi qu'une course
réelle sur le répertoire de sortie. Le même pilote est inclus dans l'image
E2E de l'adaptateur et lancé sur le SPARK par `bash adapter/dev.sh test`.
Sa preuve porte sur la CLI et les fichiers ; elle n'invoque aucun handler et
ne remplace pas les preuves HTTP de déploiement ou d'exécution à venir.

`runtime-validation.py`, lancé sur le SPARK par `bash runtime/dev.sh test`,
exécute le pilote Docker réel de validation. Il utilise les variantes originales
de `qualification/artifacts/`, la vraie dépendance YAML, les valeurs applicatives
de cellule et le contrôle déjà déployé pour éprouver les permissions du socket.
Il vérifie chargement, refus, limites, logs et destruction des descendants ;
son rapport est `runtime/validation-proof.json` sur le SPARK. Il ne prouve pas
encore les autorisations de publication ni l'invocation des handlers.

`artifacts.py`, lancé dans le SPARK par `bash control/artifacts-dev.sh test`,
fabrique des archives réelles et appelle la CLI d'extraction dans son image
Python. Il vérifie les fichiers produits, leurs empreintes et permissions,
les erreurs de format, les bornes, une saturation effective du disque et
des courses sur les destinations et la source. Le dernier parcours empaquette
l'application de qualification, extrait son ZIP puis charge son handler avec
le véritable runtime Node. Le rapport est `control/artifacts-proof.json`.

`deployments.mjs` empaquette les handlers originaux par la CLI réelle, puis
crée namespace, service, fonctions et jetons par les API de gestion normales.
Le chargement asynchrone de `qualification/artifacts/deployment-delay.mjs`
permet les modifications concurrentes réelles pendant la validation Docker.
Les assertions portent sur droits, candidats, import, révisions, révocation,
conflits, admission unique, rollback et suppression des révisions inactives.
Les archives conservées à la suppression d’une fonction sont recensées dans
le rapport ; ce nettoyage de gestion n’est pas une purge d’archives.
Cette campagne exige la session SSO ; ses onze groupes passent, ainsi que les
sept groupes CLI, dans la [preuve authentifiée](../docs/evidence/deployment-authenticated-dev-2026-11-06.json).
Une fixture écrit réellement un secret avant d'échouer à l'import ; le client
vérifie son expurgation et rejoint ses quatre uploads concurrents avant nettoyage.
Les plafonds globaux/de révisions et la reprise pendant réception/validation
ont leur [complément](../docs/evidence/publication-recovery-dev-2026-11-06.json).
La publication CLI/UI est qualifiée dans
[SLS-063](../docs/evidence/publication-console-dev-2026-11-07.json), puis rejouée
dans SLS-067. Les preuves résiduelles d’expiration, budget et nettoyage de
SLS-030 restent distinctes au backlog.

`adapter-deploy-public.py`, exécuté sur le SPARK par `bash adapter/dev.sh
deploy-public-test`, appelle de vrais processus CLI pour les prérequis,
les bornes de configuration et le refus 401 de la véritable API HTTPS DEV.
`adapter-deploy.mjs` crée ses jetons par la session SSO puis lance la vraie
commande deploy : onze fonctions imposent une pagination, un import qui
lève réellement une erreur produit un résultat partiel, et un brouillon
refusé est repris avec Read/Create. Les révisions archivées à la suppression
sont recensées. Ses sept groupes sont réussis et le nettoyage confirmé.
Le recoupement vérifie les archives sur disque et l'absence de réservations,
de canaux et de conteneurs de validation restants. Les cas de rupture réseau,
de modification locale concurrente, de redirection et de réponse trop grande
restent ouverts.

`publication-recovery.mjs` vise les plafonds de 64 candidats globaux et de vingt
révisions, puis deux arrêts brutaux du seul `serverless-api` DEV pendant un
upload partiel et une validation Docker observée. Il redémarre le contrôle,
rejoint les requêtes interrompues et vérifie les états HTTP, SQLite en lecture
seule, fichiers et conteneurs. Il crée ses objets et conserve les archives
antérieures ; aucune base ni horloge n'est modifiée pour obtenir un résultat.
Le rapport `publication-recovery.json` exige completed et cleanup vrais.
Ses quatre groupes passent sur le SPARK DEV : [preuve de reprise](../docs/evidence/publication-recovery-dev-2026-11-06.json).
Le fragment de 192 Kio dépasse le tampon Python réel de 128 Kio ; le pilote
exige des octets présents sur disque avant de couper. Les vingt publications
du plafond utilisent des UUID distincts et le même artefact réel.

`runtime-instances.py` exerce le diagnostic réel en processus séparé : enfants
neufs dans un conteneur chaud, corps aux limites, callbacks, ESM et dépendances,
confinement, logs, mesures Docker, HTTPS sortant, descendants, mémoire/PIDs,
timeouts, signaux et imports bloquants. Une suspension SIGSTOP/SIGCONT du pilote
vérifie qu’un résultat en attente ne devient pas un succès après la deadline.
`instance-lifecycle.py` appelle les méthodes réelles du pilote avec Docker et
son canal Unix pour les courses de démarrage/fermeture, annulations répétées,
nettoyage filesystem refusé puis repris, IDs étrangers, doublons et bornes du
canal. La clé testée est celle de cette instance réelle ; aucun jeton public
ni handler de substitution n’est créé. Un second démarrage refusé doit laisser
l’instance existante utilisable. Les commandes sont `bash runtime/dev.sh
instances-test` puis `bash runtime/dev.sh lifecycle-test`, sur le SPARK.
Les rapports se trouvent dans `runtime/`. La passerelle et les admissions
restent hors de ces preuves de composants.

`managed-storage.py` s'exécute comme root dans le SPARK DEV. Un worker temporaire
est écrit dans le tmpfs du contrôle readonly, puis charge les classes de
production embarquées sous `/app`. Les quatorze groupes utilisent Docker,
l'agent installé et le handler `volume-operations.cjs` pour les quotas,
la persistance, les consommateurs partagés, les annulations et les pannes.
Le parent limite la durée totale, garde la propriété de la cible FUSE, restaure
l'agent et rejoint le worker même si une commande de panne échoue. Le rapport
et les ressources sont vérifiés avant de déclarer le succès. Cette campagne de composant n'exerce pas la passerelle publique : ses preuves
HTTPS sont portées par `public-invocations.mjs`.

`python3 -B e2e/storage-installation.py`, depuis le poste, utilise la console
SPARK sur 127.0.0.1:5175 et le rebond SSH autorisé. Il arrête l'agent au repos,
propose une autre racine par la vraie console et exige le refus de l'installateur
avant création de cette racine. Il restaure la variable officielle et l'agent,
puis vérifie son identité et le maintien du même contrôle. Son rapport est
`.local/e2e/storage-installation.json` ; ne pas lancer une autre campagne pendant
ce changement de configuration de la cellule.

`storage-preparations.py` s'exécute comme root du SPARK DEV. Il appelle les
commandes réelles du client de stockage embarqué dans le contrôle : préparation,
commit, abort et consultation du reçu. Douze groupes couvrent droits de propriétaire,
baux actifs, versions, quota réduit sous saturation, écritures et conservation,
échec sous usage réel, reprise après restart, SIGKILL pendant preparing observé,
abandon partiel devant un fichier inattendu et répertoire vide antérieur préservé.
Le nettoyage confirme la suppression Docker avant release ; une incertitude
garde le bail et bloque abort/purge de cette fonction. Son rapport
`storage/preparations-proof.json` est invalidé avant les prérequis et conserve
les erreurs de restauration. Il qualifie le protocole de l’agent. Les mutations HTTPS sont exercées
séparément par `function-storage.mjs`.


`function-storage.mjs` vérifie quinze groupes : treize autour des vraies routes
de gestion et de publication, un groupe du pilote embarqué sous verrou SQLite
et un groupe de fermeture du writer sous SIGTERM réel. Ils couvrent quotas,
usages écrits par Docker, baux, refus et révocation,
SIGKILL avant/après décision, confirmation indisponible, contention SQLite,
publication et rollback, archive avec SHA256 des données. Un timer systemd
indépendant est armé avant chaque suspension de l’agent. La preuve du garde
exige sa trace corrélée et un processus réellement suspendu avant SIGCONT.
Le pilote redémarre explicitement le contrôle après `docker kill` et restaure
les composants avant nettoyage, même en cas d’échec. Le rapport conserve UUID,
décisions, gardes, archives et erreurs de nettoyage ; aucun jeton ni secret.
Le writer du registre conserve sa responsabilité jusqu’à sa fermeture sous
`spark-docker`. Le probe `registry-close-interruption` vérifie le signal différé,
le retour root et la reprise du vrai verrou écrivain ; il ne modifie aucune ligne.

Les campagnes de gestion et publication utilisent `storage-archives.mjs`
pour une purge opérateur séparée, après leur DELETE normal. Le helper du SPARK
vérifie les UUID exacts de fonction et namespace, leur rattachement, la suppression
logique et l’absence de bail ou mutation avant d’appeler l’agent réel. Les
rapports `storage_archives` conservent l’état archivé précédant cette purge.
Les archives de **code** recensées dans `retained_archives` restent conservées.
Une erreur de purge fait échouer le nettoyage ; les fonctions indépendantes
continuent d’être traitées. Les UUID des fonctions déjà supprimées restent suivis.

## Moteur public

`public-invocations.mjs` publie les handlers originaux du dépôt, appelle HTTPS
avec les vrais jetons et recoupe les observations avec SQLite, Docker et les
baux. Il couvre les droits, enveloppes et limites HTTP, les files, générations,
allocations, modes de stockage, déconnexions et reprises du contrôle. Les
scénarios de corps incomplet distinguent HTTP/1.1 et HTTP/2 conformément au
[contrat de transport](../docs/ADMISSION.md#budgets-et-attente).

Synchroniser `execution-faults.py`, `function-storage-faults.py` et leur module
`control_database.py` dans le SPARK
avant la campagne. Le premier vérifie installation, namespace et UUID avant
les observations ou interruptions ; il ne modifie aucune ligne SQL. L’arrêt
gracieux est observé sous un vrai verrou écrivain et avec des ressources
présentes avant fermeture. Le code 143 d’Uvicorn n’est accepté qu’avec sa fin
de lifespan observée ; SIGKILL reste un scénario séparé. Les gardes indépendantes
redémarrent le contrôle en cas de perte du pilote.

Le nominal historique de `instance-limit-guard.py` appliquait32→2 puis32.
Le helper maintenu refuse cette mutation. SLS-099 remplace le scénario par une
installation DEV temporaire de la même image, plafonnée à2 au démarrage, sans
écriture de variable officielle. L’évolution conditionnelle de FORGE n’est
plus un prérequis ; fenêtre, admissions HTTP/cron, sûreté et raccordement sont
qualifiés par les preuves SLS-099 liées en fin de document.
[Contrat et preuves exigées](../docs/INSTANCE_LIMIT_RESTORATION.md).

`node e2e/instance-limit-safety.mjs`, depuis le poste avec session SSO réelle,
qualifie le refus avant mutation sur le SPARK au repos : namespace original,
entrées restore puis EOF, budgets/fichiers/propositions/services identiques,
suppression réelle du namespace. `python3 -B e2e/instance-limit-guard.py UUID
--inspect` effectue seulement le précontrôle natif et console. Cette preuve
ne qualifie pas la restitution indépendante, SIGKILL ou une édition concurrente.

Le rapport `.local/e2e/public-invocations.json` conserve des checkpoints atomiques,
les identifiants créés, les archives de code retenues, les gardes et les erreurs.
Le nettoyage attend les états terminaux côté serveur, supprime les seuls objets
créés, purge leurs archives de stockage puis exige l’absence de réservations,
conteneurs, réseaux, baux et canaux résiduels. Un échec de prérequis ou de
nettoyage ne peut pas être déclaré réussi. Les 31 groupes publics et 221 régressions passent dans la
[preuve du moteur](../docs/evidence/execution-dev-2026-11-06.json).

Les gardes root ouvrent les bases du contrôle et du stockage sous l’identité effective du compte
`spark-docker`, puis retrouvent root pour les signaux et systemd. Lectures,
writers et fermetures suivent ce contexte ; les preuves contrôlent les UID du
WAL/SHM et la restauration de l’identité opérateur. Le service de stockage
et son registre appartiennent également à `spark-docker`.

## Console des exécutions

`node e2e/execution-ui.mjs` part de l’accueil et crée ses objets par la console.
Le handler original `qualification/artifacts/observation.cjs` est empaqueté
par l’adaptateur, publié par l’API et invoqué avec un vrai jeton Read. Douze
groupes couvrent six instances sur deux pages, mesures rendues, extinction,
recalage et focus, journaux expurgés/tronqués/HTML texte, mobile, erreurs réseau,
absence de session, suppression, appel actif et démarrage non confirmé.
La panne de métriques tue le seul conteneur de fonction identifié par ses UUID
et labels, pendant une garde SQLite bornée ; le contrôle reprend ensuite ses
ressources. Les attentes de réponse sont jointes immédiatement aux actions UI.
Le nettoyage retrouve les créations par leurs noms exacts même si la navigation
échoue, puis confirme suppression et purge de leurs archives de stockage.

`python3 -B e2e/execution-suite.py --scope console` exécute en série `public`,
`login-ui`, `control-ui`, `execution-ui`, `publication-ui` puis `manual-ui`. Son rapport est
`.local/e2e/console-execution-regressions.json`. Il vérifie la fraîcheur et le
contenu de chaque rapport : fin, nombres de groupes, absence d’échec/skip et
nettoyage selon son schéma. La source et l’image sont recoupées avant/après.
La [preuve initiale des observations](../docs/evidence/console-execution-dev-2026-11-07.json) compte
40 groupes et 25 captures relues. Les mesures Docker partielles sont une donnée
réelle : leur absence doit rester visible, jamais devenir un zéro.

## Manuel intégré

`node e2e/manual-ui.mjs` ouvre le manuel depuis l’accueil réel et sa navigation.
Huit groupes vérifient le contenu intégral (empreinte, chapitres,
paragraphes et tableau), le clavier, le focus, les ancres rechargées, les formats
desktop/tablette/mobile, l’agrandissement mesuré du corps de texte, l’absence de
session et le retour aux namespaces. Les erreurs JavaScript sont contrôlées
après fermeture du navigateur, avant de déclarer le rapport terminé.

La [preuve initiale](../docs/evidence/manual-console-dev-2026-11-07.json) recoupe
48 groupes exécutés en série et 33 captures relues. Le tiroir mobile ouvert
dispose d’une capture visuelle complémentaire prise depuis l’accueil réel ;
elle n’ajoute pas un groupe au total. Les sources du manuel, du build Vite et
du filtre de contexte Docker font partie de l’inventaire avant/après chaque
campagne. Le parseur Markdown n’est pas utilisé par le client de preuve pour
fabriquer son attendu : paragraphes, titres et cellules sont recoupés au document.

## Publication du code dans la console

Depuis la racine, après synchronisation de `publication-state.py` et des helpers
opérateur sur le SPARK, exécuter séparément `node e2e/code-publications.mjs`,
`node e2e/publication-ui.mjs` puis `node e2e/manual-ui.mjs`. Les deux premières
campagnes utilisent `publication-fixtures.mjs` pour empaqueter les handlers
originaux par l’adaptateur ; aucun code applicatif n’est remplacé.

La campagne intermédiaire comportait dix groupes API couvrant droits, versions,
UUID, conservation effective, abandon, conflits, révocation et courses. Ses
quatorze groupes navigateur couvraient
la création depuis la console, les vrais ZIP, import et logs expurgés,
publication A/B et activation A invoquée, historique, pagination, panne réseau,
session absente, rechargement pendant l’upload et retour à une préparation
après interruption de sa réponse. Ce dernier scénario ajoute une latence
Chromium réelle, quitte le document après observation du commit par l’API,
puis retrouve le même UUID sans renvoyer le ZIP. Il ne remplace aucune réponse.

Les campagnes suppriment leurs objets, purgent leurs archives de stockage par
le helper borné et recensent séparément le code conservé. La
[preuve intermédiaire](../docs/evidence/publication-console-checkpoint-dev-2026-11-07.json)
recoupe 32 groupes, 21 captures relues et 109 sources inchangées pendant les
campagnes. La capture nommée `validating` montre encore le libellé de réception ;
la validation est observée par l’API, sans preuve visuelle de ce libellé dans
ce checkpoint. La qualification a été étendue aux scénarios ci-dessous.

Les parcours étendus passent 21 groupes ciblés : réponses perdues d’activation
et suppression, candidat d’une autre fonction, journal long/tronqué et clavier,
validation rendue, nettoyage physique refusé puis repris et confirmation de
stockage en attente. `publication-cleanup-fault.py` vérifie namespace, UUID,
inode et permissions avant son mode 000 ; sa garde indépendante est éprouvée
après SIGKILL et SIGSTOP du seul helper. Le vrai contrôle constate EACCES,
la console reçoit 503 après suppression logique, puis la maintenance reprend.
Le mode commit de `function-storage-faults.py` suspend brièvement l’agent réel
pour qualifier une publication enregistrée dont la confirmation expire ; ce
mode et son inspect exigent l’UUID exact du namespace de publication.

La commande `python3 -B e2e/execution-suite.py --scope publication` réunit les
campagnes moteur et console en série, sans répéter les campagnes communes :
dix-huit campagnes ; le checkpoint historique ci-dessous passe 312 groupes,
et le runner courant en attend 313. Son rapport autonome est
`.local/e2e/publication-regressions.json`. Chaque rapport doit être frais,
complet et nettoyé ; sources locales/distantes et image restent identiques.
La [preuve finale](../docs/evidence/publication-console-dev-2026-11-07.json) recoupe
144 sources, l’image déployée, les ressources web servies, les archives conservées
et l’absence de ressources actives de campagne. Les 54 captures sont inspectées.
La lecture du même candidat est cohérente entre liste et suivi ; cinq gestes
constatent un succès réel puis son effacement après une seule consultation.
Les rapports et images antérieurs sont conservés comme checkpoints distincts.

## Effacements corrélés du stockage

Comme root du SPARK DEV, après installation du paquet SLS-064, exécuter
`python3 -B /srv/p2enjoy-serverless/e2e/storage-discard.py`. La campagne utilise
le client embarqué, le socket installé, Docker et les volumes FUSE : reçus,
versions, droits de propriétaire, collisions de préparation, réponse fermée
sans lecture, quotas, fichiers conservés, cache désactivé, purge et tombstone.
Elle exerce les permissions réelles, un verrou SQLite, restart et SIGKILL en
finalizing, et un arbre de 150 000 fichiers pendant l’usage d’autres baux.
Les permissions ont une garde systemd indépendante ; seuls les UUID de la
campagne sont nettoyés. Le rapport storage/discard-proof.json exige fin et
nettoyage vrais, zéro échec/skip. Les douze groupes ciblés et 94 groupes de
régression passent dans la [preuve](../docs/evidence/storage-discard-dev-2026-11-07.json).
Depuis le poste, `python3 -B e2e/execution-suite.py --scope storage` exécute les
sept campagnes en série, actuellement 107 groupes, avec sources, image et fraîcheur
des rapports vérifiées. Le checkpoint SLS-064 conserve ses 106 groupes historiques.

## Refus directs de purge et absence d’effet

`node e2e/storage-console-api.mjs` exige aussi SSH root vers le seul SPARK DEV.
Ses neuf groupes incluent quatorze corps de purge malformés, une ancienne version
positive réellement lue avec UUID frais et nom exact, puis absence des reçus.
`storage-command-faults.py inspect-api-refusals UUID_FONCTION UUID_NAMESPACE`
lit seulement l’archive exacte de la campagne `storage-console-api-XXXXXXXX`.
Les autres modes gardent leur périmètre `storage-recovery-XXXXXXXX`. Le banc
vérifie le refus de l’ancien mode de lecture sur ce namespace et du nouveau mode
avec un autre namespace. Il compare fichiers data/cache, inventaires d’artefacts,
empreinte de configuration chiffrée, versions, commandes, gardes, reçus et audit
de purge. Les snapshots encadrent aussi les refus d’accès, de CSRF et de confirmation.

Le complément est qualifié après le replay complet, avec ses propres 173 sources
avant/après et le même contrôle. Ses quatre fonctions sont purgées dans deux
namespaces distincts, recoupés par `storage-console-inspect.py`. La preuve complète
conserve les deux phases et les mises à jour documentaires de statut postérieures.
Le manuel et l’application ne changent pas dans ce complément de qualification.


## Catalogue vide du vrai parcours public

`node e2e/invocation-empty-ui.mjs` crée et publie depuis l’accueil et les formulaires.
Il retient le GET du bouton Actualiser, détourne les deux routes autorisées vers
18091 via la console normale, puis libère la même requête. Les trois groupes
passent : création/publication, vrai 200/total zéro avec état vide desktop/mobile,
restauration et invocation de l’URL copiée. Cinq JPEG frais et les reçus natifs
sont recoupés dans la [preuve](../docs/evidence/invocation-empty-ui-dev-2026-11-09.json).
206 sources et images identiques avant/après ; une fonction purgée dans son
namespace, helper et garde de routes terminés. Une mutation non confirmée
conserve la fixture même après restauration de secours. Cette branche propre
du client reste à éprouver ; aucun résultat réseau n’est substitué.


## Entrée publique de l’alias et vrai SSO

`node e2e/invocation-alias-entry.mjs` exige un JSON username/password sur stdin
privée. Le lecteur du banc masque l’écho et transmet ce JSON au seul processus
enfant ; depuis un terminal, sans mettre les valeurs dans la commande :

```sh
python3 -B -c 'import runpy,subprocess; r=runpy.run_path("e2e/execution-suite.py"); c=r["private_credentials"](); raise SystemExit(subprocess.run(["node","e2e/invocation-alias-entry.mjs"],input=c).returncode)'
```

Trois groupes passent : redirections HTTPS/API anonymes de l’alias, puis vrais
login/logout UI desktop et mobile depuis son accueil. Le POST de déconnexion
est observé sans interception via CDP durable, pour conserver son vrai corps
après navigation. Les assertions signed_out/sso_signed_out restent exigées.
[Preuve](../docs/evidence/invocation-alias-entry-dev-2026-11-09.json) : 207 sources
figées, six JPEG inspectés et deux sessions/flows fermés ; deux essais arrêtés
avec deux autres sessions fermées sont conservés séparément. Aucun cookie
fournisseur, identifiant ou URL sensible n’est enregistré. Le parcours nominal
n’écrit aucun cookie ; un échec de fermeture conserve uniquement son cookie
plateforme propre en 0600 pour reprise, avec nettoyage déclaré incomplet. Cette
branche et les autres pannes du client restent à éprouver. Aucune route/donnée
métier/configuration/image changée dans ce complément.


## Garde du refus réel de lecture du relevé

`node e2e/invocation-source-guard.mjs` exige SSH root vers le seul SPARK DEV et
l’installation au repos, sans fonction active. Les trois cas sérialisés passent :
release, SIGKILL puis SIGSTOP du helper. `invocation-source-permissions.py` arme
le programme figé systemd avant chmod 000 du seul fichier officiel ; le contrôle
ouvre réellement sa source avec errno 13. Le parent distant observe les signaux
par waitpid, la garde restitue le mode d’origine et chaque reçu reste immuable.
Trois helpers et timers/services terminés, contenu/inode/mtime/mode 0640 restitués
et deux HTTPS sains sont recoupés dans la
[preuve](../docs/evidence/invocation-source-guard-dev-2026-11-09.json), sur 210 sources.
Ctime change comme attendu. Les futurs parcours de catalogue API/UI ne sont pas
qualifiés par ces trois groupes de garde ; aucune fonction ni route n’est créée.


## Catalogue public sous EACCES réel

`node e2e/invocation-source-api.mjs` exige une session administrateur réelle,
l’installation au repos et les helpers du SPARK synchronisés. Quatre groupes
passent en série : publication via adaptateur, source_forbidden sous chmod du
fichier officiel avec garde préalablement qualifiée, droits avant diagnostic,
appels Docker pendant la faute puis catalogue et appels restitués. Le scope
JSON distant est cité pour OpenSSH. La fixture est conservée si la restitution
ne peut être confirmée. Une fonction purgée, quatre appels et garde terminée
sont recoupés en lecture seule : [preuve](../docs/evidence/invocation-source-api-dev-2026-11-09.json),
211 sources et images identiques. Aucun rendu UI ou autre classe de source
n’est qualifié par ces quatre groupes.


## Refus réel de lecture dans la console

`node e2e/invocation-source-ui.mjs` crée et publie depuis l’accueil normal et
les formulaires. Trois groupes passent : catalogue initial avec copie réussie,
vrai EACCES du relevé puis Actualiser/alerte sans ancien résultat, restitution
et invocation Docker de l’URL copiée. Cinq JPEG frais sont conservés avec SHA
et mtimes ; focus DOM et mesures de débordement sont des assertions distinctes.
Les attentes HTTP sont suivies immédiatement et jointes après fermeture du
navigateur. Une garde qualifiée précède la faute ; la fixture reste conservée
si la restitution ne peut être confirmée. Une fonction purgée, parents supprimés,
un appel et garde finie sont recoupés : [preuve](../docs/evidence/invocation-source-ui-dev-2026-11-09.json),
212 sources et images identiques. Autres fautes de source et branches d’erreur
du client restent distinctes ; aucune réponse/route n’est substituée.


## Identité canonique de paquet

`bash control/code-hash-dev.sh test`, comme spark-docker dans le seul SPARK DEV,
lance `function-code-hash.py`. Sept groupes traversent les vrais packager,
extracteur, calculateur et CLI d’instance Node. Neuf invocations observent les
handlers/dépendances. Réordre/recompression/renommage, changements réels, Unicode
et refus de ZIP/descripteur sont vérifiés sans simulation. Le rapport natif est
`control/function-code-hash-proof.json` ; ses temporaires et canaux courts sont
suivis sous control, puis retirés. Les 24/14 groupes Docker de l’adaptateur et
sept de publication authentifiée sont conservés avec leurs 222 sources figées.
Le replay nommé des sept groupes a sa propre époque, produit/images identiques.
[Preuve](../docs/evidence/function-code-hash-dev-2026-11-09.json) : 52 groupes retenus,
deux essais arrêtés distincts, dix-neuf conteneurs runtime et 37 clients nommés
absents, douze
fonctions supprimées et volumes purgés ; 33 archives de code restent conservées
et vérifiées. Les prérequis de build/contexte ne sont pas ajoutés au total.
Cette preuve de composant ne qualifie pas les futurs appels publics par hash.


## Registre du hash : migrations et campagnes réelles

[Contrat du registre](../docs/FUNCTION_VERSION_REGISTRY.md) et
[banc de purge 006](../docs/FUNCTION_VERSION_PURGE_UPGRADE.md).
Le checkpoint passe 359 groupes : 46 ciblés/historiques et 313communs,69 captures,
deux époques de clients aux mêmes fichiers produit et image. Le checkpoint au
repos antérieur328reste distinct. Le replay ciblé du poller 15est déjà repris
dans la suite commune ; il n’est pas additionné au total 359.

Depuis le poste, construire la vraie référence006 par
python3 -B e2e/function-version-control-build.py. Les clients maintenus
function-version-purge-upgrade.mjs prennent upgrade artifacts, upgrade volumes,
ou upgrade artifacts --restore-with-guard, séparément. Ils créent leurs données
via les API, passent le SSO réel, publient dans Docker et restaurent les originaux.
Leur JSON username/password arrive seulement par stdin protégée. Pour conserver
la saisie terminal sans écho, le lecteur de la suite peut envelopper un client :

```sh
python3 -B -c 'import runpy,subprocess; r=runpy.run_path("e2e/execution-suite.py"); credentials=r["private_credentials"](); result=subprocess.run(["node","e2e/function-version-purge-upgrade.mjs","upgrade","artifacts"],input=credentials); credentials=None; raise SystemExit(result.returncode)'
```

La copie privée du vrai backup intermédiaire sert ensuite à
function-version-purge-correlation.py UUID artifacts, exécuté comme spark-docker
dans le SPARK :20 refus de vrai démarrage, rollback intégral et original inchangé.
function-version-migration-faults.py éprouve aussi les six inventaires/descripteurs
invalides et les contraintes SQLite. Les copies n’ont ni réseau ni socket Docker.

Le parcours function-version-registry.mjs prepare/verify/persist correspond au
premier upgrade depuis006 : A/A/B, rollback, données et cache avant/après. prepare
se lance avant007 ; ce n’est pas une reconstitution SQL sur une base déjà migrée.
Le parcours UI courant est node e2e/function-version-registry-ui.mjs, après
préparation SSO normale. La suite commune reste
python3 -B e2e/execution-suite.py --scope publication. Les assertions de schéma
attendent 001–007 ; le banc storage-legacy conserve son vrai départ 001–003.

## Régression008 CLI, capacité et reprises

Depuis la racine, lancer `python3 -B e2e/function-version-cli-recovery-regressions.py`.
Le lecteur terminal demande le JSON username/password sans écho ; le secret
n'est ni argument, ni variable, ni fichier. Le prérequis SSO réel crée deux
sessions plateforme privées, distinctes des onze groupes. Ne lancer aucun autre
banc en même temps. Le pilote exige l'installation DEV au repos et conserve les
anciens rapports avant le replay. Il refuse une réutilisation de son rapport
brut sans archivage explicite.

La [tranche CLI et reprise008](../docs/evidence/function-version-cli-recovery-regressions-dev-2026-11-09.json)
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

L'opérateur publication-recovery-operator.py est limité au namespace exact et
aux UUID fonction/candidat ; il arme sa garde avant envoi, lie l'arrêt au CID et
joint son mutateur. Une restitution incertaine conserve les fixtures. Les deux
fenêtres physiques ne qualifient pas toutes les pannes propres du banc. Les
inventaires pre_purge_revisions sont pris avant effacement et ne désignent pas
des archives conservées après la purge publique.

## Régression008 des invocations et des mutations de stockage

Depuis la racine : `python3 -B e2e/function-version-invocation-storage-regressions.py`.
Le JSON SSO est saisi sur stdin sans écho ; aucune valeur ne passe dans les
arguments ou rapports. Le pilote exige DEV au repos, conserve les rapports
antérieurs, lance le prérequis puis les deux clients en série. Les opérateurs
existants et la console normale du SPARK sont nécessaires ; aucun autre banc
ne doit tourner. Le rapport brut ne peut pas être écrasé sans archivage explicite.

La [tranche invocation/stockage008](../docs/evidence/function-version-invocation-storage-regressions-dev-2026-11-10.json)
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
Cette époque historique utilisait la console du SPARK pour le plafond ; le
parcours courant est l’installation isolée SLS-099 décrite ci-dessous.

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

La collecte lie tous les handlers succeeded à un transport reçu, aux sept appels
Echo ou à l'unique succès détaché observé. Une réponse avant réservation garde
son UUID sans ligne d'invocation inventée. Un502 sans UUID exige le témoin de
la connexion exacte coupée pendant SIGKILL ; aucune tolérance générale aux502.
Les états failed/interrupted/rejected attendus sont des comportements éprouvés,
pas des groupes ignorés. Les pertes et délais propres du pilote et des anciens
opérateurs restent distincts de leurs cas réellement provoqués.

Après le retrait du briefing privé de l'historique, les lectures Git historiques
utilisent les commits remappés. L'identité revision des attestations reste celle
des preuves datées ; source_revision précise le commit effectivement lu. Voir
[réécriture Git](../docs/GIT_HISTORY_REWRITE.md) et sa table de correspondance.

## Planifications réelles SLS-078

Sur la version du contrôle reconstruite avec la migration 009, session réelle
préparée par `dev-sso-sessions.mjs`, exécuter depuis la racine :
`node e2e/schedules.mjs`. Le client crée ses fonctions originales et jetons par
HTTPS, publie/promet des déclarations sans route HTTP, attend deux frontières
UTC réelles, recoupe les événements consignés par les handlers Docker, ouvre
la facette depuis l'accueil et le manuel, puis archive/purge ses ressources.
Chaque essai porte un UUID, un rapport privé distinct et ses captures JPEG ;
un prérequis absent échoue. Cette première campagne ne couvre pas encore les
promotions multiples, les interruptions, le recouvrement, la saturation ou tous
les états UI de [SCHEDULES](../docs/SCHEDULES.md#preuves-e2e-attendues).

Le cycle des versions planifiées se lance séparément, après la fin de cette
campagne : `node e2e/schedule-versions.mjs`. La session SSO réelle reste requise.
Le client publie les handlers originaux `scheduled-versions.cjs`, prépare B
comme pilote puis observe quatre frontières réelles : A, B après promotion,
A après archivage de B avec remplacement, puis aucun tir après promotion d'un
code sans planification. Les mutations ont lieu pendant les vingt secondes
du handler déjà admis ; son code initial doit terminer. Deux autres fonctions
éprouvent la désactivation de cible et la suppression après leur premier tir.
Le lecteur `schedule-versions-inspect.py` recoupe leurs invocations et tirs
natifs, y compris ceux de la fonction supprimée devenue inaccessible par API.
Après purge publique, il vérifie volumes, code, ressources, sources embarquées,
artefacts originaux et fichiers officiels. Les rapports privés portent le
préfixe `scheduled-functions-<UUID court>` ; les éventuels tirs préparatoires
restent distincts des quatre fenêtres retenues. Aucun état Git ou service
n'est modifié par le lecteur natif.

La grammaire numérique se qualifie séparément par
`node e2e/schedule-calendar.mjs`, avec la session SSO réelle et le SPARK au repos.
Le client passe par les commandes réelles plan/package, publie leurs événements
et promeut trois fonctions utilisant le handler original scheduled-event.cjs.
Il prépare une fenêtre UTC complète avant ses nominaux, vérifie les refus422
des expressions invalides, compare les prévisions dimanche0/7, date impossible
et29février, puis recoupe huit handlers attendus : listes, plages, pas,
combinaisons du OU jour/semaine, heures et mois. Les déclarations exclues ne
doivent produire aucun tir de cette fenêtre. Les éventuels tirs préparatoires
restent distincts. Le lecteur natif existant recoupe les identités et la purge
publique des trois fonctions ; les rapports portent leur préfixe UUID propre.

La reprise du moteur se qualifie ensuite par `node e2e/schedule-recovery.mjs`.
Le [plan de coupures](../docs/SCHEDULE_RECOVERY.md) décrit les prérequis et les
frontières observées. Le client utilise une session SSO réelle, publie une seule
fonction originale, éprouve d'abord la garde indépendante après SIGKILL du
traceur, puis coupe le contrôle DEV avant réclamation pendant trois fenêtres,
après réclamation durable et après lien de l'invocation avant son handler.
Chaque reprise est suivie d'une prochaine frontière exécutée normalement.
Prévoir environ40 minutes d'horloge réelle. Le pilote natif
`schedule-recovery-operator.py` doit être synchronisé sur le SPARK ; il conserve
backup privé, identités, reçus de coupe et restitution dans ses dossiers bornés.
Le client conserve chaque rapport UUID et ses stderr privés, restitue toutes
les gardes avant nettoyage, puis purge par HTTPS et recoupe l'absence physique.
Un échec conserve son rapport et n'entraîne aucun rejeu automatique.

La campagne d'admission se lance séparément : `node e2e/schedule-admission.mjs`.
Elle exige le SPARK au repos et les budgets1CPU/8192Mio/32instances relevés dans
[SCHEDULE_ADMISSION](../docs/SCHEDULE_ADMISSION.md). Cinq fonctions originales
sont publiées avant une fenêtre commune : handler315s, cible1CPU, deux volumes
exclusifs occupés par de vrais HTTP et dépassement du délai d'exécution. Les
deux frontières suivantes éprouvent recouvrement et reprise après libération.
Prévoir15 minutes d'horloge réelle. Aucun budget ni fichier officiel modifié.
Le lecteur `schedule-admission-inspect.py` recoupe les cinq UUID, SQL RO,
conteneurs, réseaux, baux, canaux et allocations ; après les purges publiques,
il vérifie les artefacts antérieurs et les sources embarquées. Chaque rapport
privé porte un UUID ; un échec est conservé et les appels sont terminés avant
nettoyage, sans rejeu automatique.

Le complément RAM/version se lance ensuite, seul :
`node e2e/schedule-memory-version.mjs`. Il exige la session SSO réelle, le SPARK
au repos et les budgets1CPU/8192Mio/32instances. Un minimum128Mio et un HTTP
exclusif occupent réellement le budget avant W ; la cible8192Mio est refusée
sans invocation. Le tir en file est refusé après promotion du pilote sans cron,
puis les deux fonctions réussissent aux fenêtres suivantes après libération
et retour de hash. Le handler d'allocation attend20s pour recouper Docker.
Prévoir environ15 minutes. Le lecteur `schedule-memory-inspect.py` accepte les
trois UUID exacts et vérifie les purges physiques. Aucun budget officiel modifié.
Contrat et discriminants : [SCHEDULE_MEMORY_VERSION](../docs/SCHEDULE_MEMORY_VERSION.md).

## Files pleines des tirs planifiés

`node e2e/schedule-queues.mjs`, seul sur le SPARK au repos et avec une session
SSO réelle, crée neuf fonctions originales puis observe trois fenêtres UTC.
Seize vrais POST HTTPS au corps incomplet remplissent la file de la première
cible ;128 répartis sur huit fonctions remplissent ensuite la file globale,
avec zéro réception sur la seconde cible. Les deux tirs doivent être refusés
queue_full sans invocation ; les clients sont déconnectés/rejoints avant les
succès HTTP et planifiés suivants. Prévoir environ15 minutes d'horloge réelle.

Le lecteur strict `schedule-queue-inspect.py` accepte les neuf UUID et leurs
instances connues ; `--waiting` relève seulement SQL RO, sous propriétaire,
pour recouper les files dans le délai normal30s. Après les neuf purges publiques,
`--purged` recoupe ressources physiques, artefacts et backend embarqué. Sources
et images sont figées pendant la campagne ; aucun budget officiel modifié,
aucune dépendance à la garde SLS-099. Contrat : [SCHEDULE_QUEUES](../docs/SCHEDULE_QUEUES.md).

## Tir pendant un vidage de cache en cours

`node e2e/schedule-unavailable.mjs`, seul sur le SPARK au repos avec une vraie
session SSO, publie une fonction originale avec données/cache synchronisés.
Le helper existant storage-command-faults.py arme sa garde100s avant de refuser
les permissions du seul cache. Une commande cache-clear reste alors réellement
pending sous storage_io_error ; le tir doit être refused_unavailable sans
invocation. La restitution connue précède la fin du même reçu et le prochain
tir réussi, données conservées et cache vidé. Prévoir deux fenêtres réelles,
environ10 minutes ; aucun budget ni fichier officiel modifié.

`schedule-unavailable-inspect.py` accepte le seul UUID du namespace
storage-recovery et la seule unité de garde : SQL RO, inode/modes/empreintes,
commande/intention/reçu agent, processus exact, unités et ressources physiques.
En cas de restitution inconnue, le banc conserve les ressources et échoue ;
aucune purge n'est tentée. Contrat : [SCHEDULE_UNAVAILABLE](../docs/SCHEDULE_UNAVAILABLE.md).

## Maximum individuel et instances planifiées déjà prêtes

`node e2e/schedule-instance-reuse.mjs`, seul sur le SPARK au repos avec session
SSO réelle, publie deux fonctions originales : minimum1 préchauffé sans appel,
et maximum1 occupé par un HTTP non exclusif. À la première frontière, le minimum
est réutilisé et l'autre tir refuse sans invocation, budgets globaux encore libres.
À la suivante, les deux tirs utilisent exactement les mêmes instances/CID.
Quatre groupes, deux fenêtres réelles (environ10 minutes) ; les minima et idles
sont libérés avant les deux purges publiques. Aucun budget de cellule changé.

Le lecteur `schedule-instance-reuse-inspect.py` recoupe les deux UUID, files,
réservations, Docker, baux et canaux, y compris le préchauffage sans invocation.
Sources/images figées, nettoyage après terminaison des HTTP, aucun mock ni skip.
Contrat : [SCHEDULE_INSTANCE_REUSE](../docs/SCHEDULE_INSTANCE_REUSE.md).


## Installation isolée pour le plafond global — SLS-099

Le mode `instance-limit` de storage-legacy-environment.py réutilise la fenêtre
DEV gardée, mais démarre exactement l’image servie avec des données neuves et
le seul plafond2 dans son conteneur temporaire. Aucun PUT de variable officielle.
La route18090 sert temporairement cette installation ; le contrôle habituel
est conservé arrêté. Contrat : [INSTANCE_LIMIT_RESTORATION](../docs/INSTANCE_LIMIT_RESTORATION.md).

Depuis le poste, après synchronisation du helper sur le seul SPARK DEV au repos,
exécuter séparément `node e2e/instance-limit-environment.mjs release`, puis `eof`,
`sigterm`, `sigkill` et `deadline`. Chaque commande crée son rapport UUID privé,
refuse toute simulation et attend la fin de la garde et du pilote. Les trois
pertes/échéance utilisent une vraie garde120s ; prévoir environ deux minutes
par cas. Ce client ne qualifie que déploiement/restitution sans consommateur,
pas encore les admissions HTTP/cron ni la perte avec un handler actif.
Ces cinq modes passent dix groupes réels sur327sources :
[preuve](../docs/evidence/instance-limit-environment-dev-2026-11-11.json).

`node e2e/instance-limit-admission.mjs` reçoit ensuite les identifiants SSO sur
stdin privée, ouvre une nouvelle fenêtre du même mode et se connecte depuis
l’accueil. Trois fonctions originales sont publiées par les API : deux occupent
le plafond, la troisième doit être refusée malgré les budgets CPU/RAM libres.
Le client vérifie aussi minimum3 refusé409, appel sain après libération, refus
à une vraie frontière cron puis prochain tir réussi sans rejeu, et trois purges.
Prévoir deux frontières UTC et la fenêtre gardée900s. Ce client passe quatre groupes sur328sources, six handlers réussis,
refus planifié01:35UTC sans invocation puis succès01:40UTC sans rejeu, trois
purges publiques et restitution des originaux :
[preuve](../docs/evidence/instance-limit-admission-dev-2026-11-11.json).
Ne pas le lancer en parallèle d’un autre banc. Le raccordement à la suite
publique et les modes de sûreté sont qualifiés par les preuves ci-dessous.


Le mode `node e2e/instance-limit-admission.mjs --consumer-loss` utilise l’entrée
privée SSO habituelle et une garde120s. Il démarre un handler45s vers85s après
armement, puis tue réellement le pilote. La garde doit observer le même appel
encore running avant retrait, enlever son conteneur/réseau, libérer son bail et
restituer les originaux. Le retrait des données temporaires ne vaut pas purge
métier ni succès du handler. Ce mode passe les deux groupes liés ci-dessous.

Le mode `--observer-unavailable` exerce la même perte avec Docker pause réel du
contrôle temporaire : relevé positif avant suspension, exec refusé pour la
garde, erreur de capture explicite et restitution attendue. Le nominal conserve
son exigence de témoin complet. Ces deux modes passent chacun deux groupes
distincts dans la preuve liée ci-dessous.

Le mode `--foreign-namespace` crée un namespace synthétique hors du périmètre
attendu, exige le refus de restitution et sa présence par API, puis supprime
ce seul objet par API avant restitution. Les refus d’autorité ne sont jamais
capturés comme diagnostic facultatif. Le stderr des seuls appels SSH opérateur
est conservé en0600 pour diagnostiquer une erreur de transport sans l’exposer.


Le raccordement public est qualifié par la preuve finale liée ci-dessous :
`python3 -B e2e/public-invocations-suite.py` reçoit le JSON SSO privé, prépare
ses deux sessions normales, exécute HTTP30, attend ses purges, puis plafond4.
Il conserve un rapport public31 et le détail du dernier groupe, avec snapshots,
rapports UUID isolés et archivage du rapport précédent. Le client HTTP seul
`node e2e/public-invocations.mjs` écrit public-invocations-http.json et ne prouve
que ses trente groupes. La suite générale transmet l’entrée privée au lanceur.
Les trois modes de sûreté passent six groupes sur328sources :
[preuve](../docs/evidence/instance-limit-consumer-restoration-dev-2026-11-11.json).

Le scope ciblé `python3 -B e2e/execution-suite.py --scope public-invocations`
exécute ce même raccordement via la suite générale, avec sa saisie SSO privée,
ses prérequis, snapshots et vérification du rapport31. Rapport de suite :
.local/e2e/public-invocations-regressions.json. Il ne remplace pas les autres
scopes de la campagne complète.

La [preuve finale329](../docs/evidence/instance-limit-public-integration-dev-2026-11-11.json)
passe le scope public31 (HTTP30 nettoyé puis plafond4), les cinq modes finaux
release/EOF/SIGTERM/SIGKILL/deadline (dix groupes), puis le chemin historique
`node e2e/storage-legacy-recovery.mjs --partial` (un groupe). Toutes ces commandes
sont exécutées en série. Seize fonctions purgées, zéro écriture officielle,
originaux restitués et gardes terminées. Les époques327/328 restent distinctes ;
le premier essai HTTP échoué après17 groupes n’est pas compté comme réussi.
SLS-099 est close ; ces preuves ne remplacent pas la campagne globale.


## Capture authentique de rétention — SLS-078

`node e2e/schedule-retention-capture.mjs` exige une session SSO réelle fraîche
dans le canal privé habituel et le helper synchronisé sur DEV. Il publie une
fonction originale, exécute un témoin HTTP, puis capture à la frontière */5
une invocation réussie dont le tir reste dispatched/non clos. Le traceur
s’attache après running/handler_started du handler original à réponse2s,
sans instrumenter son démarrage froid. Le SQLite backup
utilise une source RO ; hash exécuté, créneau et logs reçus sont recoupés dans
la sauvegarde. Le contrôle est repris sans SIGKILL, même CID/image/démarrage.

Le helper conserve sous qualification-history une copie privée du contrôle,
du registre et des artefacts vérifiés. La fixture active est purgée par API ;
le rapport UUID .local/e2e/schedule-retention-capture-*.json porte la date réelle
éligible sept jours plus tard. Aucun réglage d’horloge ni SQL de préparation.
Une capture réussie ne prouve ni les sept jours ni10000 objets : ces campagnes
restent requises dans [SCHEDULE_RETENTION](../docs/SCHEDULE_RETENTION.md).
La [capture réelle5056167](../docs/evidence/schedule-retention-capture-dev-2026-11-11.json)
passe quatre groupes sur331sources. Âge éligible le18 novembre2026 à03:30:26UTC ;
les propres pannes et régressions du helper restent à exercer.

## Préparation de la borne des tirs planifiés

`node e2e/schedule-firing-volume-capture.mjs` reçoit le JSON SSO sur stdin privée,
ouvre la fenêtre instance-limit900s du même contrôle et publie/promet16 fonctions
portant chacune16 crons. Une frontière UTC réelle doit donner256 tirs, deux
handlers réussis et254 refus de capacité. Le helper lance ensuite le lecteur
`schedule-firing-volume-snapshot.py` avec son verrou hérité : sauvegardes SQLite
RO, artefacts et images immuables vérifiés, copies privées conservées. Les16
fonctions sont purgées par les API avant restitution et jonction des gardes.

Prévoir jusqu'à deux frontières UTC pour préparer les promotions ; lancer seul,
sur le SPARK DEV au repos, après synchronisation des sources. Le rapport UUID
porte l'instant réel d'éligibilité après39 fenêtres manquées. La commande
prépare la preuve ; elle ne teste pas encore le futur replay ni la borne10000.
Contrat : [SCHEDULE_FIRING_VOLUME](../docs/SCHEDULE_FIRING_VOLUME.md).

Le [replay31b9102](../docs/evidence/schedule-firing-volume-capture-dev-2026-11-11.json)
passe quatre groupes sur340sources :256 tirs06:15UTC, sauvegarde protégée,
16 purges et restitution. L'essai27221ea échoué est conservé séparément.
Éligibilité numérique09:30UTC. Les
[vingt groupes de garde/options/sûreté](../docs/evidence/schedule-firing-volume-guard-regressions-dev-2026-11-11.json)
passent sur les mêmes340sources après la capture. Replay numérique et copie
interrompue et source protégée sous borne sont qualifiées séparément ci-dessous ; âge encore ouvert.

## Replay gardé de la borne des tirs

Synchroniser les sources, puis exécuter seul et en série sur le SPARK DEV au
repos : `node e2e/schedule-firing-volume-replay.mjs MODE`.

| MODE | Portée et prérequis réels |
| --- | --- |
| invalid | Huit refus de paramètres/source, avant création de fenêtre ; un groupe |
| not-eligible | Refus count avant39 fenêtres ; à exécuter avant la date réelle d'éligibilité, un groupe |
| preflight |1 à38 fenêtres manquées ; chargement/observation, SSO/API, restitution ; trois groupes |
| seed-loss | SIGKILL du pilote et du copieur après registre, avant CONTROL ; deux groupes |
| observer-loss | SIGKILL après attache réelle du traceur ; deux groupes |
| count | Après39 fenêtres ; observations complètes avant/après pruning au même curseur, SSO/API, restitution ; trois groupes |

Les modes preflight/count reçoivent le JSON SSO sur stdin privée. Les autres
n'en demandent pas. Le client attend si nécessaire la première partie d'une
fenêtre avant mutation ; la garde120 est ensuite obligatoire pour tous les
replays. Les copies privées restent scellées, les rapports UUID sous .local/e2e.
Un prérequis absent échoue, sans skip ni relance automatique. Aucune qualification
n'est acquise par cette implémentation. Contrat :
[SCHEDULE_FIRING_VOLUME](../docs/SCHEDULE_FIRING_VOLUME.md#chargement-gardé-de-la-copie).

Le [replaye53b0d9](../docs/evidence/schedule-firing-replay-preflight-dev-2026-11-11.json)
passe neuf groupes sur342sources : invalid/not-eligible, préflight de18 fenêtres
et4864 tirs,64 pages API après SSO, deux pertes et restitutions indépendantes.
Observation4,46s ; source conservée. Les
[vingt régressions historiques](../docs/evidence/schedule-firing-replay-guard-regressions-dev-2026-11-11.json)
passent sur les mêmes342sources. Count qualifié séparément ci-dessous ; interruption du copieur
initial qualifiée ci-dessous. Les trois tentatives échouées sont conservées séparément.


## Interruption pendant la copie SQLite de capture

`node e2e/schedule-firing-volume-capture.mjs --copy-loss` reçoit le JSON SSO
sur stdin privée et ouvre seul une fenêtre DEV900s. Les trois premiers groupes
exercent le même nominal :16 publications,256 vrais tirs puis capture complète.
Deux groupes supplémentaires arrêtent le copieur au premier progrès SQLite
partiel, tuent le pilote, déclenchent le vrai service de garde et constatent
son blocage pendant au moins2s. Après SIGKILL du copieur et jonction pidfd de
son wrapper timeout, seule la garde restitue les originaux. Les copies normale
et canonique6:15 sont recoupées ; la sortie partielle distincte est protégée et
conservée, sans capture terminée ni purge métier prétendue. Les actions natives
loss-point/block-guard/join-copy/rescue-copy/sealed-state sont réservées à ce journal de
campagne, pas des commandes générales d'administration. Les [cinq groupes réels](../docs/evidence/schedule-capture-interruption-dev-2026-11-11.json)
passent sur342sources dbb840b. Les
[vingt régressions](../docs/evidence/schedule-capture-guard-regressions-dev-2026-11-11.json)
passent sur les mêmes sources :11 restitutions/partial,3 options/défaut900,6
consommateur/diagnostic/namespace étranger. Total25 pour cette étape ; bornes
numérique et âge ne sont pas déduits de ces groupes ; numérique qualifié ci-dessous.
Voir le [contrat](../docs/SCHEDULE_CAPTURE_INTERRUPTION.md).


Le [préflight e23e820 sur deux lots](../docs/evidence/schedule-firing-replay-two-batches-dev-2026-11-11.json)
passe trois groupes sur342sources courantes à09:15UTC :36 fenêtres manquées,
9472 tirs, observation9,94s,96 pages API et restitution. Il reste sous10000 ;
le mode count est réservé à l'éligibilité réelle09:30UTC de la source6:15.

## Résultat du mode count

Le mode `node e2e/schedule-firing-volume-replay.mjs count` passe
[trois groupes réels](../docs/evidence/schedule-firing-retention-count-dev-2026-11-11.json)
sur342sources ef8cb3f :39 fenêtres réellement manquées,10240→10000 tirs au même
curseur09:30UTC,240 plus anciens exactement retirés. Chaque fonction avait640
tirs avant borne ;112 pages API après SSO concordent avec les survivants natifs.
Observation10,82s, deux invocations initiales seules, restitution jointe et source
scellée inchangée. Source protégée sous borne, sept jours et campagne complète
restent ouverts ;078.5 reste non clôturée.

## Source planifiée sous borne des invocations

Contrat : [INVOCATION_SOURCE_RETENTION_VOLUME](../docs/INVOCATION_SOURCE_RETENTION_VOLUME.md).
`node e2e/invocation-source-retention-volume.mjs` reçoit les identifiants SSO sur
stdin privée et déploie une installation isolée de même image, garde2700s.
Deux flux produisent10000 vrais HTTP ; le rendez-vous réel d'un dernier HTTP et
d'un cron permet d'observer10002→10001 (source protégée), puis10000 après clôture.
`python3 -B e2e/source-retention-guard-options.py` éprouve la durée2700 programmée
et quatre refus de combinaisons avant mutation. Exécuter un seul scénario à la
fois sur le SPARK DEV au repos. Les frontières manquées sont des échecs sans
rejeu automatique ; nominal, pannes propres et régressions communes ont leurs
preuves distinctes ci-dessous.

### Garde2700 et refus qualifiés

La [preuve f59a8d3](../docs/evidence/source-retention-guard-options-dev-2026-11-11.json)
passe cinq groupes sur346sources inchangées : quatre refus avant mutation,
puis programmation2700s et restitution nominale jointe. Même contrôle/image,
configuration et référence conservés, pilote et garde terminés. L'expiration2700
n'est pas revendiquée. Le collecteur initial a échoué sur un glob incluant son
checkpoint ; le rapport E2E terminé0 est conservé et recoupé avant/après sans
rejouer les tests. Charge10000 et frontières sont qualifiées séparément ci-dessous ;
pannes propres et régressions communes qualifiées séparément ci-dessous.
Ces cinq groupes seuls ne prouvent
pas la rétention.

## Pilote durable de la preuve longue des sources

`python3 -B e2e/invocation-source-retention-worker.py start` lit les identifiants
SSO sur stdin privée puis lance une seule tâche systemd utilisateur locale,
sans récurrence. Elle exécute le client E2E réel et conserve son checkpoint
dans `.local/e2e/source-retention-worker-UUID/`. Après la sortie du lanceur,
`status UUID` relit MainPID/naissance/cgroup ; une absence de handle ne vaut
pas résultat. `finish UUID` conserve le vrai résultat systemd après la fin du
worker, puis arrête cette seule unité. Une finalisation interrompue reprend
depuis son reçu sans lancer de nouveau test.

Service oneshot borné3600s, Node3000s et garde distante2700s ; identifiants transmis
en mémoire par canal Unix authentifié, aucune valeur sensible persistée. Aucun
autre scénario n'est lancé pendant la tâche. En cas d'échec/interruption, vérifier
la restitution autoritative du SPARK avant toute autre opération. Implémentation
et syntaxe acquises ; indépendance et nominal qualifiés séparément ci-dessous.

Avant le nominal, `python3 -B e2e/source-retention-worker-loss.py` reçoit aussi
les identifiants privés, lance le vrai worker et attend des réponses et deux
fonctions, puis SIGKILL son seul MainPID. Il exige le résultat système signal9,
la finalisation en échec, deux consommateurs retirés et les originaux restitués
avec sources/images identiques. Trois groupes attendus ; aucune rétention ni
purge métier n'est attribuée à cette panne.

### Perte du pilote durable qualifiée

La [preuve bbe9d0e](../docs/evidence/source-retention-worker-loss-dev-2026-11-11.json) passe trois groupes
sur348sources figées :512 réponses HTTP réelles, contrôleur initial terminé et
worker indépendant recoupé, SIGKILL MainPID avec résultat signal/Code2/Status9
conservé comme échec. Deux conteneurs/réseaux et consommateurs sont inventoriés
avant faute puis réellement absents après restitution ; les deux retraits de
chaque classe sont aussi enregistrés par la garde dans ce cas. Restitution
indépendante terminée, mêmes données/configuration/images et référence, garde
et unité locale jointes. Le premier essai échoué reste exclu. Ces trois groupes
qualifient la perte et sa restitution ; nominal numérique qualifié séparément ci-dessous, sept jours encore requis.

## Nominal de source protégée qualifié

Le [nominal de source protégée](../docs/evidence/invocation-source-retention-volume-dev-2026-11-11.json) passe trois
groupes sur348sources d860cc5 :10001 HTTP et un cron,10002→10001 avec tir non
clos puis10000 après clôture. Exacts deux plus anciens HTTP retirés, source
inchangée,5001 lignes par fonction avant borne, observation12,34s, deux purges
publiques et restitution nominale jointe. Sept jours et campagne complète restent
ouverts ; cette preuve ne clôture pas078.5.

## Replay des témoins de rétention

`python3 -B e2e/retention-history-suite.py source|terminal MODE` lance un seul
cas et recoupe les sources/images avant et après. Son client
`retention-history-replay.mjs` vérifie les deux
captures canoniques selon [RETENTION_HISTORY_REPLAY](../docs/RETENTION_HISTORY_REPLAY.md).
Un seul appel à la fois, SPARK DEV au repos. Modes : `invalid` (huit refus
d'options avant mutation), `not-eligible` (refus réel avant sept jours),
`preflight` (témoins encore jeunes), `age` (après échéance réelle), `seed-loss`
et `observer-loss` (SIGKILL réel au point durable, garde indépendante120).
Les modes preflight/age reçoivent par stdin privée les identifiants SSO, jamais
par arguments ou environnement ; l'entrée ne doit pas être un terminal. Le
lanceur habituel `private_credentials` masque la saisie avant transmission.

Le module Python `retention-history-replay.py` vérifie les reçus/SQLite/artefacts/
images, copie CONTROL en dernier et observe les commits réels avant santé. Le
helper historique autorise ce seul clonage d'installation dans une fenêtre
exclusive ; les modes sans options gardent leurs refus d'identité antérieurs.
Échéances communes : source18novembre03:30:26.355818UTC ; terminale04:05:13.358459UTC.
[Treize groupes](../docs/evidence/retention-history-replay-preflight-dev-2026-11-11.json)
qualifient neuf refus/préflights puis quatre groupes pour les pertes avant
CONTROL et après attache, sur les mêmes351sources. SSO/API réels et restitutions
nominales puis indépendantes120 ; captures inchangées. Le namespace supplémentaire
a sa preuve distincte ci-dessous ; régressions communes qualifiées plus bas.
Les preuves de captures et de borne numérique restent dans leurs époques distinctes.

`python3 -B e2e/retention-history-suite.py source foreign-namespace` reçoit
le SSO sur stdin masquée, reprend la source en helper preflight, crée une
seule fixture de namespace et vérifie son maintien au premier refus restore.
Après DELETE API de cette fixture, une restitution explicite est recoupée ;
independent=true décrit la restitution explicite avant expiration du timer. Les
[quatre groupes9f3e7da](../docs/evidence/retention-history-namespace-scope-dev-2026-11-11.json)
passent sur351sources, dont deux préflights rejoués. Réconciliation API exercée,
HTTP perdu non provoqué ; sources et originaux conservés.

## Régressions finales des fenêtres de restitution

La [preuve au commit f908640](../docs/evidence/retention-history-guard-regressions-dev-2026-11-11.json)
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

### Refus après attachement de l'observateur source

Le parcours `node e2e/invocation-source-retention-volume.mjs --observer-refusal`
est spécifié dans [son contrat](../docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#refus-réel-après-attachement-de-lobservateur).
Il utilise le SSO privé sur stdin, deux vrais handlers sans production de
10 000 appels, le refus naturel du même opérateur et le code 1 du helper avec
restitution réelle. Les [deux groupes 956498a](../docs/evidence/invocation-source-observer-refusal-dev-2026-11-11.json)
passent sur 351 sources identiques avant/après, sans changement d'image :
HTTP/cron et tir recoupés, TracerPid puis zéro du même processus, lecteur et
mémoire fermés, helper terminé 1 après refus et restitution jointe. Deux
conteneurs/réseaux/baux réellement retirés et absence physique recoupée.
Cette preuve ne qualifie ni la rétention, ni detach en échec, ni les délais
35/40 secondes, ni l'attente native 25 sans événement.

## Pertes avant la capture initiale de rétention

Le même client accepte deux options exclusives :
`node e2e/schedule-retention-capture.mjs --eof-after-gate` et
`node e2e/schedule-retention-capture.mjs --observer-loss-after-gate`.
Préparer une session privée par le parcours SSO réel de `dev-sso-sessions.mjs`,
puis exécuter un seul cas à la fois. Quatre groupes par cas : vrai témoin HTTP,
faute après le cron réussi mais tir non clos, reprise sans rejeu, purge physique.
Le deuxième cas tue le seul helper par pidfd et attend sa garde indépendante
80 s ; le contrôle garde son PID/démarrage. Le client recoupe les inventaires
réels des captures canoniques avant/après et les deux UUID/dates des appels.
Les [huit groupes réels](../docs/evidence/schedule-retention-gate-losses-dev-2026-11-11.json)
passent au client 20ffc09 sur 351 sources, puis les
[quatre du nominal](../docs/evidence/schedule-retention-capture-regression-dev-2026-11-11.json)
sur la même époque et les mêmes images. Les trois refus CLI d'options sont
mesurés séparément avant création de rapport ; aucun groupe E2E ajouté.
Les mêmes UUID/dates et démarrage du contrôle sont conservés, trois fonctions
purgées physiquement, captures canoniques inchangées. Backup/copie interrompus
et âge restent ouverts ; le rejeu historique est qualifié ci-dessous. Le nominal sans option garde
sa capture de non-régression ; elle ne remplace aucune source canonique d'âge. Contrat :
[SCHEDULE_RETENTION](../docs/SCHEDULE_RETENTION.md#pertes-avant-la-commande-de-capture).

## Rejeu courant de la reprise après coupure

Les [cinq groupes historiques](../docs/evidence/schedule-recovery-regression-dev-2026-11-11.json)
de `schedule-recovery.mjs` passent sur 351 sources 7ed2abe et les mêmes images :
trois coupures Docker 137, trois fenêtres manquées, trois tirs suivants réussis,
claimed/linked sans rejeu, quatre gardes jointes et une purge physique. Quatre
handlers réussis au total incluent le témoin initial ; une invocation liée est
interrompue avant handler_started. Captures canoniques inchangées.

Le worker systemd local finit avec Code1/Status0/Resultsuccess ; son résultat
est enregistré avant arrêt. Le client de lancement a expiré à 20 s, puis
l'observation du même PID/naissance/cgroup a été récupérée sans redémarrage.
Le futur lancement privé ajoute --no-block, sans preuve nominale supplémentaire.
Brut 803 835 octets, gzip 91 578. Aucun produit/UI changé ; interruptions de
copie/backup, âge et campagne complète restent ouverts.

## Interruption de la sauvegarde et de la copie d'artefacts

Le client `schedule-retention-capture.mjs` accepte aussi deux options exclusives :
`--control-backup-loss` et `--artifact-copy-loss`. Préparer les sessions privées
par le vrai parcours SSO, synchroniser helper/client, puis exécuter un seul cas
à la fois sur le SPARK DEV au repos. Chaque cas exige quatre groupes : témoin
HTTP, progrès réel interrompu avec garde indépendante 80 s, même contrôle et
tir clos sans rejeu, purge physique. Les options correspondantes du helper
`--capture-loss=control-backup|artifact-copy` sont réservées à terminal-capture.

Le reçu root0600 précède SIGSTOP et porte soit le progrès SQLite non final,
soit le fichier réellement copié/conforme. Le client inspecte le helper arrêté,
la trace du contrôle, puis la vraie garde tuant/joignant ce helper. Le nouveau
dossier partiel est protégé et conservé sans manifeste final ; les deux sources
canoniques restent identiques. Aucun accès de récupération au SQLite partiel.
Sans option, rejouer ensuite le nominal.
Contrat : [interruptions de copie](../docs/SCHEDULE_RETENTION.md#interruptions-pendant-sauvegarde-et-copie).

Les [douze groupes bca96ab](../docs/evidence/schedule-retention-copy-losses-dev-2026-11-11.json)
passent sur351sources/images identiques : deux pertes réelles (16/4 837 pages,
1/5 990 fichiers) puis nominal16:50. Huit groupes de panne et quatre nominaux ;
six handlers réussis, trois purges physiques, même contrôle sans redémarrage.
Gardes80 indépendantes jointes, TracerPid0, partiels protégés et captures
canoniques conservées. Six refus CLI séparés ne comptent aucun groupe E2E.
Brut491 114/gzip161 179 ; les cinq historiques de l'époque7ed2abe ne sont pas
recomptés à cette époque. Autres pannes d'observation, âge et campagne finale ouverts.

## Délai de l'observateur sans événement natif

`node e2e/native-observer-deadline.mjs reproduce` ouvre le vrai contrôle
temporaire vide de même image, garde120. Son opérateur dédié attaché consomme
l'arrêt initial, arme un dégel systemd28s du seul conteneur temporaire puis
confirme Docker pause et l'absence de statut en attente. Il appelle la vraie
classe partagée avec échéance25s, conserve résultat et durée avant nettoyage,
confirme le dégel et joint le service avant detach/fermeture du lecteur.

Trois groupes attendus : installation, reproduction d'un dépassement réel,
restitution. Le mode `bounded` est destiné à la mesure après correction :
expiration entre25 et26s, même dégel sûr et même restitution. Aucun mode ne
fabrique d'événement ni de données SQL. Exécuter seul sur le SPARK DEV au repos ;
aucune session SSO nécessaire pour ce diagnostic du composant natif. Les budgets
35/40s ne changent pas. Ces contrôles ne
qualifient ni l'opérateur source complet ni sa rétention. Contrat :
[attente sans événement](../docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#mesure-de-lattente-native-sans-événement).

Les [trois groupes reproduce c64fdd7](../docs/evidence/native-observer-deadline-reproduce-dev-2026-11-11.json)
passent sur353sources/images inchangées : dépassement25 effectivement mesuré
à28,202s, après le dégel indépendant28 et avant l'alarme35. Acteur joint,
Trace0/mémoire/lecteur fermés et originaux restitués ; aucun handler. Cette
preuve constate le défaut. Les
[trois groupes bounded46e216d](../docs/evidence/native-observer-deadline-bounded-dev-2026-11-11.json)
passent ensuite sur353sources/images identiques :25,000182s, masque/handler
préservés, alarme restante cohérente et restitution réelle. Régressions des
consommateurs qualifiées séparément ci-dessous ; ni35/40 propres à l'opérateur
ni rétention prouvés par cette borne isolée.

Les [onze groupes consommateurs96dcca0](../docs/evidence/native-observer-consumers-dev-2026-11-11.json)
passent sur les mêmes353sources/images que bounded : trois de
`schedule-firing-volume-replay.mjs count`, trois de
`retention-history-replay.mjs source preflight`, trois du même client
`terminal preflight`, deux de `invocation-source-retention-volume.mjs --observer-refusal`.
Toutes ces commandes reçoivent le SSO sur stdin privée et s'exécutent en série.
10 496→10 000tirs/exacts496plus anciens retirés, observation13,526s ; préflights
source9,189s et terminal0,005624s ; refus naturel après deux vrais running,
détachement/lecteur fermés et ressources physiquement absentes. Quatre
restitutions jointes/captures canoniques conservées. Brut33 679 951/gzip2 063 211.
Le nominal complet10 002→10 001→10 000 de la classe courante a sa preuve355
distincte ci-dessous ; ces onze groupes ne remplacent ni ce nominal ni les pannes propres.

## Pannes propres de l'opérateur source35/40

Le client `invocation-source-retention-volume.mjs` accepte deux nouvelles options
exclusives : `--observer-global-deadline` et `--observer-command-timeout`.
Il reçoit le SSO sur stdin privée, prépare les deux vrais handlers du mode
de refus puis déclenche une suspension native après attachement et reçu durable.
Exécuter un seul mode à la fois sur le SPARK DEV au repos.

Le module `source_observer_deadlines.py` arme un acteur systemd indépendant
figé qui confirme l'étatT et SIGALRM pending. Le premier mode reprend le seul
opérateur par pidfd après l'échéance réelle35+.5 ; le second le laisse arrêté
jusqu'au vrai timeout40. Le helper conserve le code de la commande et mesure
TracerPid0 avant restauration, puis joint l'acteur. Le client distingue ces
statuts, recoupe les deux handlers au point de porte et l'absence physique
après restitution. Deux groupes par mode sont qualifiés par la preuve e45126b
ci-dessous ; aucune rétention ni réussite métier déduite de ces pannes.
Contrat : [bornes source35/40](../docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#pannes-propres-de-lalarme35-et-de-la-commande40).

Le premier essai35 est conservé comme échoué : après expiration des handlers,
les minima créent deux remplacements, rejetés à tort par l'assertion initiale.
Le reçu natif des seuls modes35/40 porte désormais les identités tardives,
labels, montage et réseaux ; le client les corrèle aux mêmes fonctions/révisions
et exige l'absence exacte de l'union initiale/tardive après restitution, en plus
des neuf contrôles physiques existants. Minima et délais restent inchangés.
Correction implémentée et replays E2E35/40/refus qualifiés ci-dessous.

Le wrapper timeout est identifié par chemin/version/SHA dans chaque reçu.
Sans preserve-status, le vrai binaire DEV retourne124 à l'échéance40 ; le
signal demandé KILL9 et le résultat du wrapper sont distincts. Le premier
replay échoue sur l'ancienne attente137, conserve son échec et sa restitution.
Le client corrigé exige124, durée40–43s, diagnostic KILL, opérateur absent,
TracerPid0 avant retrait et contrôles physiques ; les replays passent ci-dessous.

Les [six groupes e45126b](../docs/evidence/source-observer-deadlines-dev-2026-11-11.json)
qualifient désormais35/40 et le refus sans option sur354sources/images figées :
35,683720s/TimeoutError avec lecteur fermé ;40,009839s/wrapper124 et opérateur
absent. TracerPid0 avant retrait, acteurs joints, neuf contrôles physiques et
sept vérifications exactes de l'union initiale/remplacements. Trois refus CLI
séparés ne gonflent pas les groupes. Les deux essais échoués sont exclus ;
aucun waitstatus137 du fils, rétention ni âge déduit. Originaux restitués,
deux services sains, actifs nuls,5982artefacts et aucune garde finale.

## Lecteur fermé après une vraie erreur de detach

`node e2e/invocation-source-retention-volume.mjs --observer-detach-failure`
reçoit le SSO sur stdin privée et prépare les deux handlers réels. Après
attache, un acteur indépendant figé est prêt avant Docker pause ; la vraie
reprise ptrace doit donner WNOHANG0. Le premier essai échoué a montré que
Docker pause seul laisse detach réussir. Le mode corrigé arme un point SIGSTOP
optionnel dans le vrai wait appelé par detach, après calcul de son échéance5.
Le reçu porte cette échéance ; l’acteur recoupeT puis envoie SIGCONT par pidfd
après échéance+.25. La vraie vérification de délai doit alors lever, sans
remplacement de méthode ni exception injectée.
Le client exige lecteur/mémoire fermés malgré l'erreur, mort de l'opérateur,
Trace0 encore gelé puis dégel et jonction de l'acteur avant restitution.
Un secours15s interdit le succès ; l'unité30 est attendue avant arrêt. Deux
groupes, puis refus sans option : les quatre passent dans la preuve ci-dessous.
Contrat : [nettoyage malgré erreur](../docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#fermeture-du-lecteur-malgré-une-erreur-native-de-detach).

La [preuve b5f0825](../docs/evidence/source-observer-detach-failure-dev-2026-11-11.json)
passe quatre groupes sur355sources : erreur native de detach après5,255s,
lecteur/mémoire fermés, masque restitué, dégel sans secours puis refus sans
option rejoué. Neuf contrôles physiques et sept exacts passent, originaux
restitués. L'essai sans exception reste échoué. Bounded et les six consommateurs
et le nominal numérique complet sont qualifiés ci-dessous.

Les [trois groupes bounded courants](../docs/evidence/native-observer-detach-bounded-dev-2026-11-11.json)
passent sans faute à25,000300s, puis les [quinze groupes consommateurs](../docs/evidence/native-observer-detach-consumers-dev-2026-11-11.json)
passent au même gel355 : `schedule-firing-volume-replay.mjs count`, puis
`retention-history-replay.mjs source preflight` et `terminal preflight`, puis
`invocation-source-retention-volume.mjs --observer-refusal`, `--observer-global-deadline`
et `--observer-command-timeout`, toujours en série. Exacts496 tirs retirés,
témoins conservés, mêmes bornes35/40, nettoyages et restitutions passent.
Six handlers nouveaux seulement ; les témoins copiés restent distincts.
Nominal numérique et historique final qualifiés ci-dessous ; âge et campagne
complète restent à exécuter, les époques antérieures sont conservées.

## Rejeu historique final après les consommateurs courants

Le même `node e2e/schedule-recovery.mjs` passe [cinq groupes](../docs/evidence/schedule-recovery-detach-regression-dev-2026-11-11.json)
sur355sources ef98a9f, identiques au bounded et aux quinze consommateurs.
Trois coupures137 et trois tirs suivants réussis sans rejeu, quatre gardes
jointes et une purge physique. Worker local indépendant réellement terminé0,
reçu terminal conservé puis unité arrêtée ; originaux/captures conservés.
Ce rejeu clôt le reste historique du helper, pas le nominal numérique courant,
les sept jours ni la campagne complète de078.5.

## Nominal numérique de la classe courante qualifié

La [preuve6de2a86](../docs/evidence/invocation-source-retention-detach-volume-dev-2026-11-11.json) passe trois groupes
sur355sources/images identiques au bounded et à l'historique final.10001 réponses
HTTP et un cron réels donnent10002 observations terminales,5001 par fonction.
Le tir non clos garde sa source hors comptage :10001 lignes après retrait du
plus ancien HTTP. Après clôture normale, le deuxième plus ancien HTTP disparaît :
10000 lignes et source strictement identique, désormais comptée. Les trois vecteurs
sont recoupés exactement ; observation12,410435700s sous25s.

Deux purges publiques et restitution nominale jointe ; même worker réel terminal0,
reçu conservé puis unité arrêtée. Collectes natives/captures fraîches après cette
finalisation, liées au SHA terminal :2services sains, actifs/baux nuls,5982artefacts
et aucune garde. Captures canoniques inchangées. Brut83048624octets/gzip4228693 ;
ancienne preuve348 préservée. La borne native partagée et son nominal sont
qualifiés ; âge18novembre et campagne complète restent requis,078.5 non clôturée.
