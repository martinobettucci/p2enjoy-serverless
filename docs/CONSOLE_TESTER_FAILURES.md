# Testeur HTTP : échéances, confidentialité et coupure réelle

Complément de [SLS-071](BACKLOG.md#sls-071), après les tranches43 et46.
Ces checkpoints restent immuables ; aucun de leurs groupes n’est réadditionné.
Le plan initial part de8c761c5e. La correction déployée et le replay qualifié
sont décrits ci-dessous ; les paragraphes de décision gardent leur contexte.

## Résultat qualifié du complément42

La [preuve42](evidence/function-http-client-recovery-confidentiality-dev-2026-11-12.json) porte389sources039c4c97 du commit515f54a
et l’image96e5dc4e :7groupes de reprise,10de confidentialité,25régressions,
12handlers et27captures inspectées. Le SIGKILL est constaté nativement avant
fin minimale du handler, Docker137, reprise du même CID/image et observation
unique sans rejeu. Le502 du proxy sans marque donne Issue inconnue ; le vrai503
du contrôle sous verrou SQLite sans DML reste un refus visible sans invocation.
Le watchdog indépendant, les trois processus opérateurs et leurs gardes sont
joints. Les délais UI1s expirent avec un handler4s, qui termine une seule fois.
Huit sentinelles/variantes sont absentes des vrais logs/audits ; la trace publique
positive est détectée par index/SHA. Les deux captures des délais sont inspectées.
Quatre fonctions nominales et huit préliminaires sont purgées, neuf jetons sont
révoqués et parents supprimés ; intégrité/FK, dix migrations et5982artefacts
antérieurs recoupés. Aucune variable, secret ou route n’est modifiée.

Les quatre passages préliminaires et les checkpoints43/46 ne sont pas ajoutés
aux42.071.1/.4/.5 sont qualifiés avec leurs références propres. Au checkpoint42,
071.2/.3/.6/.8 restaient ouverts. Le [complément32](evidence/function-http-client-token-loss-dev-2026-11-12.json)
qualifie ensuite les pertes des mutations temporaires et071.3/.8 ; source/routes
indisponible, exception inattendue d’une tâche et campagne complète restent ouverts.
L’expiration réelle900s reste la preuve43, pas une nouvelle mesure dans42.

## Périmètre

Deux clients indépendants utilisent les vrais SSO, API, console, passerelle et
handlers originaux de ce dépôt. Le premier complète les échéances UI et recherche
les valeurs sensibles dans les vraies observations ; le second coupe réellement
le seul contrôle DEV pendant une invocation confirmée. Pas de mock, réponse
interceptée, dépendance remplacée ou changement d’horloge.

Le seul SPARK reste infra-serverless. Les fichiers officiels et routes sont
inchangés, FORGE reste un rebond SSH. Les captures de rétention protégées, la
référence et les autres services sont conservés. Les objets de chaque campagne
portent un namespace descriptif unique, sont créés par API puis purgés par API,
avec recoupement natif. Une réponse de création inconnue se réconcilie en lecture
sans rejeu ; refus certain et objet préexistant ne sont pas adoptés.

## Échéances UI et confidentialité

Le client `e2e/function-http-client-confidentiality.mjs` compose des valeurs de
campagne distinctes pour le jeton Read, Authorization, query, en-tête métier et
corps. Les valeurs complètes restent en mémoire ; ni arguments de commande,
environnement, fichiers de session/rapport ni capture ne les contiennent en
clair. Le fixture ne les journalise pas. Sa réponse métier peut refléter query,
en-tête et corps base64 ; elle reste en mémoire du client, avec les empreintes
nécessaires au contrôle et l’identifiant public de requête. Une réponse reste
une donnée de l’utilisateur, jamais une garantie d’expurgation du code métier.

Les attentes de1s sont réellement dépassées par un handler de4s, en mode serveur
puis navigateur. Le client vérifie l’issue inconnue, une unique invocation admise,
sa terminaison et aucun rejeu. Les erreurs de gestion certaines (CSRF, droits,
modèle, admission) restent distinctes d’une perte de transport.

`e2e/function-http-client-private-inspect.py` reçoit les seules sentinelles de
campagne sur stdin privée, au plus16chaînes et64Kio au total. Il contrôle le
namespace et ses fonctions puis lit les logs d’invocation, audits et logs Docker
réels depuis un relevé horaire du SPARK pris avant les requêtes. Les lectures
sont bornées ; une borne dépassée échoue au lieu de considérer la partie absente
comme expurgée. Aucune ligne brute n’est retournée : nombres de lignes/octets,
SHA et booléens d’exposition, avec indexes des sentinelles seulement. Les
événements de refus ne restituent qu’un UUID attendu, un statut entier borné et
le SHA de route avec indicateur de template attendu : même un champ de log qui
contient une fuite n’est jamais recopié brut sur stdout. Les
variantes ASCII/JSON/base64 utiles sont comparées en mémoire. La preuve exige
absence des valeurs et de leurs représentations pertinentes ; les identifiants
et traces de refus attendus doivent exister, pour éviter un succès sur logs vides.
Le prérequis prend l’heure réelle du SPARK ; l’horloge n’est jamais modifiée.
Après la recherche négative, une fonction témoin journalise volontairement une
valeur publique `public-log-witness-UUID`, distincte de tous les identifiants
confidentiels. Un second passage du lecteur doit la trouver dans les logs
réels et ne restituer que son index/SHA. Ce contrôle positif prouve que le
lecteur ne conclut pas toujours à l’absence ; il n’expose aucun vrai jeton et
n’entre pas dans la revendication d’absence des sentinelles confidentielles.

Les refus422, scopes étrangers sur le détail d’invocation, UUID étranger et
révocation sont éprouvés par requêtes réelles. Le manuel et les captures
complètent les assertions. Ce client ne qualifie pas une perte de contrôle.

## Coupure réelle du contrôle

Le client `e2e/function-http-client-recovery.mjs` utilise
`e2e/function-http-client-recovery-operator.py`, exécuté par le principal sur le
seul SPARK DEV. L’opérateur ne reçoit que namespace/fonction et commandes bornées,
jamais jeton ou contenu de requête. Il réutilise `NativeObserver` sans altérer
buffers, registres ni résultats de syscall ; aucun octet de requête ou secret
n’est lu pour cette frontière sémantique.

Avant toute action : installation saine, absence d’autre activité/consommateur,
registre sain, UID/GID attendus, identité exacte CID/image/démarrage du contrôle
et de la référence, PID Python/naissance/cgroup, empreintes officielles et des
programmes. Une garde systemd indépendante est écrite dans un répertoire privé
`/run/serverless-restore-http-client-UUID`, avec verrou identifié et programmes
vérifiés. Son timer est armé et constaté actif avant l’émission de la requête.

Le scénario public émet un seul appel lent depuis Tester. `running` seul ne
suffit pas : l’opérateur exige la confirmation persistée `handler_started=1`,
l’UUID appartenant à la fonction de sa campagne et une marge réelle suffisante
avant la fin attendue. Il attache alors l’observateur au seul Python identifié,
vérifie encore cette frontière et émet le KILL du seul CID. Le client Docker est
joint, le signal natif est constaté par `waitpid` et `WTERMSIG==SIGKILL`, puis
Docker confirme arrêté/137. L’événement et le reçu du mutateur sont persistés
avant restitution du verrou.

La restauration, nominale ou indépendante après perte du pilote, vérifie les
identités/empreintes et joint le mutateur par verrou/reçu avant de démarrer le
même CID et la même image. Aucun rebuild, remplacement d’image, écrasement de
variable ou rétablissement d’une ancienne base n’intervient. Elle attend santé
du contrôle et référence inchangée. Timer/service sont ensuite joints et leurs
MainPID doivent être nuls. Une identité changée ou un mutateur non joint fait
échouer la preuve et reste explicitement signalé ; aucune propriété étrangère
n’est reprise.

La relecture de l’opérateur avant exécution relève une lacune de génération :
le démarrage initial était enregistré sans être revérifié par les programmes
de KILL/restauration. Le même CID/image peut avoir redémarré entre-temps. Avant
tout signal, exiger aussi le StartedAt initial ; après notre propre reprise,
n’accepter que le StartedAt d’un reçu de restauration déjà écrit sous le même
verrou. Un démarrage concurrent sans ce reçu fait échouer la preuve. Vérifier
aussi les empreintes des programmes opérateur/observateur conservées dans
l’identité. Cette correction du banc précède toute coupure réelle.
La même revue exige une échéance de jonction pour le client SSH local, même
après secours validé : fermer puis terminer ce seul processus si nécessaire,
et confirmer sa sortie avant clôture. Les bornes stdout/stderr arrêtent aussi
la rétention mémoire, avec échec explicite ; fermer stdin seul ne suffit pas.
Le constat waitpid/SIGKILL et son horodatage sont écrits atomiquement dans un
reçu natif avant restitution du verrou ; stdout seul n’est pas une preuve
durable. Une perte avant ce reçu n’interdit pas la restauration sûre déjà
couverte par le reçu du mutateur, mais ne qualifie pas cette frontière native.

Un premier cas perd réellement le pilote après armement, avant appel, pour
vérifier la restitution indépendante. Le second coupe après handler démarré.
La reprise doit conserver une seule observation, son hash et la confirmation
de démarrage ; état `interrupted/control_interrupted` et HTTP503 sont les
observations de récupération, distinctes de la réponse intermédiaire du proxy.
Un appel neuf confirme les droits et la capacité après reprise ; aucune relance
invisible du premier appel n’est autorisée. Purges et état physique sont ensuite
recoupés avant succès.

## Provenance d’une erreur HTTP du premier trajet

Avant correction sur8c761c5e, la revue statique constate que `api()` attribue un statut à tout non2xx, y
compris un HTML502 de proxy, puis que `send()` traite ce statut comme un refus
de gestion. Aucun marqueur de provenance n’existait alors. Cette limite est ensuite
reproduite par80eca655, corrigée et rejouée dans42.

Le test exige une issue inconnue lorsqu’une coupure après admission prive la
console du résultat du contrôle. Il ne suffit pas de classer tous les503 comme
inconnus : un503 réellement produit avant émission par le contrôle doit garder
son message de gestion. Toute correction nécessaire sera inscrite dans le
backlog avant code et distinguera ces deux provenances sur des réponses réelles,
sans inférer un échec certain du handler depuis le seul statut du proxy.

## Hors de ce complément

L’indisponibilité de `/spark/routes` et les dernières bornes/non-régressions
restent des preuves distinctes. Ni ce plan ni un SIGKILL seul ne clôturent071.
Les messages, tableaux d’état et preuves distinguent implémenté, exécuté,
inspecté et qualifié. Les9groupes5f3ace72 puis10groupesdd3b50db restent des
passages préliminaires sur8c761c5e ; le replay84287810 est inclus dans42 sur
96e5dc4e, avec inspections et régressions. Les coupures3360afcd/80eca655 restent
échouées ; le replay993fbeda qualifie la reprise et le classement UI corrigé.

## Premier passage réel du banc de reprise

Le reçu3360afcd échoue au watchdog avant toute invocation/coupure du contrôle :
le pilote auto-tué par SIGKILL remonte255 via SSH, alors que le client attendait
strictement137. Le précédent `function-version-state-transport.mjs` accepte
137/255 avec événement SIGKILL et reçu indépendant ; réutiliser cette exigence
complète, pas le statut seul. La restitution est réelle, même CID/image et
StartedAt, et les deux fonctions sont purgées. Le nettoyage déclare ensuite
une anomalie parce que le timer n’expose pas MainPID ; son unité est absente
et inactive, le service porte MainPID0. Exiger inactive pour les deux et PID0
pour le service, accepter l’absence de ce champ du timer comme le précédent.
Les parents sont ensuite supprimés par API réelle (reçu3360afcd-parents-cleanup),
le jeton est révoqué.

Le rapport doit conserver les événements/identités et empreintes de sortie
de chaque opérateur même lorsqu’une assertion échoue avant son ajout aux
observations nominales. Ajouter cette sauvegarde systématique avant replay,
sans réécrire le premier reçu ni compter ses trois préparations comme preuve
de récupération. Aucun défaut produit n’est encore reproduit par ce passage.

## Défaut reproduit après admission — correction071.8

Le replay80eca655 sur8c761c5e passe le watchdog puis constate réellement le
SIGKILL natif avant la fin minimale du handler, Docker137 et la restauration du
même CID/image. Le proxy répond502, corps vide, sans marque de contrôle. La
console affiche «Le serveur a refusé la requête (502)» au lieu d’Issue inconnue.
La base conserve une unique invocation démarrée, reprise en
`interrupted/control_interrupted` HTTP503 ; configuration/hash actif inchangés.
Deux fonctions sont purgées, parents supprimés, jeton révoqué et gardes jointes.
Ce reçu échoué et ses captures restent préliminaires, sans qualification071.4.

Décision avant code : les réponses réellement produites sur `/api/` portent
`X-Serverless-Control-Response: 1`, ajouté par le contrôle et sans valeur issue
de la requête. Le helper `api()` garde son statut pour les autres consommateurs,
et indique séparément la provenance : marque présente et erreur JSON de forme
attendue. Le testeur, l’émission et la révocation temporaires n’affichent un
refus certain que pour ces erreurs reconnues ; une réponse proxy/illisible ou
perte de transport reste non confirmée. Aucun rejeu automatique. Ce marqueur
n’est ni un secret ni une autorisation ; les handlers `/invoke/` ne le reçoivent
pas par cette règle. Les autres lecteurs de console ne changent pas de contrat.

Le replay doit aussi distinguer un vrai503 du contrôle avant toute émission.
Le mode `refusal-lock` de l’opérateur prend un vrai verrou SQLite
`BEGIN IMMEDIATE` sous le propriétaire normal, sans DML ni changement de
configuration. Installation au repos et namespace de campagne exclusivement.
La requête UI rencontre la vraie échéance SQLite5s et reçoit le503 documenté ;
le client exige sa provenance, son message visible et zéro nouvelle invocation.
Le verrou est borné à15s, alarme20s, et libéré sur release/EOF/échéance/entrée
invalide avec rollback/fermeture et zéro total_changes. Une garde systemd ne
rajoute pas de sûreté à ce verrou : la mort du détenteur libère SQLite via le
système. Le processus SSH doit néanmoins être joint avec échéance. Le manuel
explique les deux issues ; les vraies reprises, refus et régressions sont rejoués
sur l’image reconstruite avant de qualifier la correction.
