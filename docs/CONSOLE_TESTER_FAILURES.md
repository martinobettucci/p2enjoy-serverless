# Testeur HTTP : échéances, confidentialité et coupure réelle

Complément de [SLS-071](BACKLOG.md#sls-071), après les tranches43 et46.
Ces checkpoints restent immuables ; aucun de leurs groupes n’est réadditionné.
La source produit actuelle est8c761c5e. Ce document fixe la preuve avant code
supplémentaire, sans revendiquer un scénario encore non exécuté.

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

Un premier cas perd réellement le pilote après armement, avant appel, pour
vérifier la restitution indépendante. Le second coupe après handler démarré.
La reprise doit conserver une seule observation, son hash et la confirmation
de démarrage ; état `interrupted/control_interrupted` et HTTP503 sont les
observations de récupération, distinctes de la réponse intermédiaire du proxy.
Un appel neuf confirme les droits et la capacité après reprise ; aucune relance
invisible du premier appel n’est autorisée. Purges et état physique sont ensuite
recoupés avant succès.

## Provenance d’une erreur HTTP du premier trajet

La revue statique constate que `api()` attribue un statut à tout non2xx, y
compris un HTML502 de proxy, puis que `send()` traite ce statut comme un refus
de gestion. Aucun marqueur de provenance n’existe actuellement. C’est une
limite à mesurer lors de la coupure, pas une preuve de réponse déjà reçue.

Le test exige une issue inconnue lorsqu’une coupure après admission prive la
console du résultat du contrôle. Il ne suffit pas de classer tous les503 comme
inconnus : un503 réellement produit avant émission par le contrôle doit garder
son message de gestion. Toute correction nécessaire sera inscrite dans le
backlog avant code et distinguera ces deux provenances sur des réponses réelles,
sans inférer un échec certain du handler depuis le seul statut du proxy.

## Hors de ce complément

L’indisponibilité de `/spark/routes` et les dernières bornes/non-régressions
restent des preuves distinctes. Ni ce plan ni un SIGKILL seul ne clôturent071.
Les messages, tableaux d’état et preuves continuent à distinguer implémenté,
exécuté, inspecté et qualifié. Statut : premier passage de9groupes réussi, avec deux fonctions purgées et
valeurs en mémoire uniquement ; reçu5f3ace72 conservé comme intermédiaire.
Le contrôle positif du lecteur est ajouté avant qualification finale ; sa
réalisation et son replay restent à faire. Le client
et l’opérateur de coupure restent spécifiés, non implémentés.
