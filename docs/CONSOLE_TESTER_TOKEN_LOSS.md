# Jetons temporaires : réponses réellement perdues

Complément de [SLS-071.3 et071.8](BACKLOG.md#sls-071), décidé avant code après
le checkpoint42. Il garde389sources039c4c97/image96e5dc4e et ses groupes propres.
Cette nouvelle preuve ne réadditionne aucun des checkpoints43/46/42.

## Résultat attendu

Depuis Tester, une création ou révocation dont la réponse est perdue reste
explicitement non confirmée. La confirmation demeure ouverte, aucun succès
n'est affiché et aucune requête n'est rejouée automatiquement. Fermer la
confirmation puis consulter les jetons du service permet de retrouver les
seules métadonnées. La valeur d'un jeton créé à réponse perdue est irrécupérable
et n'est jamais lue dans SQLite, les buffers de réponse, les logs ou un fichier.
Le responsable décide ensuite d'une nouvelle action explicite.

## Matrice réelle

Un client original `e2e/function-http-client-token-loss.mjs` part de l'accueil,
effectue le vrai SSO et publie son handler original par les vraies API. Un
namespace `function-http-client-token-loss-UUID` possède ses seuls objets.
Le contrôle DEV est seul au repos, référence et captures de rétention conservées.

| Action UI | Barrière native | Discriminant après reprise |
| --- | --- | --- |
| Créer temporaire | Après réception de la ligne publique, avant exécution | Aucun nouvel UUID ni audit token.create |
| Créer temporaire | Avant premier envoi de réponse, après commit | Un seul nouvel UUID Read/fonction900s et un seul audit token.create |
| Révoquer temporaire actif | Après réception de la ligne publique, avant exécution | revoked_at reste nul, aucun nouvel audit token.revoke ; jeton encore utilisable |
| Révoquer temporaire actif | Avant premier envoi de réponse, après commit | revoked_at non nul et un seul audit token.revoke ; vrai401 avec la valeur déjà détenue |

Les quatre réponses perdues doivent afficher le message non confirmé pertinent,
sans succès ni second POST. La liste est visitée par les liens et gestes UI
normaux après fermeture volontaire de la confirmation ; la lecture directe API
recoupe ses métadonnées. Les deux jetons de préparation de révocation sont
créés par l'UI avec une réponse201 réellement reçue ; leur valeur reste en
mémoire du client/page. Elle sert uniquement aux véritables invocations avant
et après la panne. Les valeurs ne figurent jamais dans arguments, environnement,
rapports, captures ou logs du client. Toute valeur connue est révoquée en cleanup.
Le jeton perdu après création est révoqué par son UUID public, sans sa valeur.

## Observation native et restauration

`e2e/function-http-client-token-operator.py` reprend la barrière existante de
`function-version-state-observer.py` et les gardes renforcées de
`function-http-client-recovery-operator.py`. Le principal seul l'exécute.

Avant action : santé, absence d'autres fonctions actives ou consommateurs,
base/registre intègres et sans travaux/baux/réservations, empreintes officielles,
CID/image/StartedAt, référence, PID/naissance/cgroup et programmes exacts.
Timer indépendant armé et actif avant attachement. Une revalidation immédiate
CID/image/StartedAt et PID/naissance/cgroup précède `observer.start`, aussi pour
le watchdog ; une vérification après attachement serait trop tardive.
Les précontrôles exigent explicitement intégrité/FK de contrôle et registre,
et SUM(reserved_bytes)=0, pas seulement absence de candidats actifs. Il restaure le même CID/image,
sans rebuild, config ni ancienne base ; la génération qu'il démarre lui-même
reste épinglée jusqu'à sa santé et son reçu final. Aucun autre SPARK ni aucune
administration FORGE ; celle-ci reste uniquement le rebond SSH.

L'observateur x86_64 reconnaît seulement la ligne publique exacte POST vers
`/api/functions/UUID/test-token` ou `/api/tokens/UUID/revoke` sur le véritable
socket local18090. `match_line` s'arrête au CRLF, même si des en-têtes partagent
le buffer. Aucun header Cookie/CSRF, corps entrant, pointeur sortant ou secret
n'est lu. Les FD sont invalidés sur close et après écritures ; seule l'entrée du
premier write/writev/sendto/sendmsg sur le FD reconnu constitue la barrière après
commit. Aucun octet, registre, résultat syscall ni code applicatif n'est remplacé.
La barrière avant coupe le processus arrêté immédiatement après réception,
avec état durable encore identique au snapshot précédent.

La projection SQLite indépendante n'extrait ni digest ni prefix : UUID, service,
droits, portée, dates et état de révocation, audit corrélé, empreinte des autres
objets et métadonnées d'invocation seulement. Le snapshot précédent est conservé ;
la barrière après exige le seul changement attendu et son audit commis. Le KILL
ne part qu'après commande bornée du client, encore à l'arrêt natif. Le mutateur
Docker est joint, waitpid constate SIGKILL et Docker137 ; un reçu natif est
persisté atomiquement avant stdout et restitution du verrou.

Un premier watchdog perd réellement l'observateur suspendu, avant mutation,
pour éprouver le chemin indépendant de cette spécialisation. Les phases avant
et après réutilisent exactement les mêmes programmes de KILL et restauration.
Toute perte du pilote déclenche secours vérifié et jonction du seul SSH local.
Sorties retenues au plus1Mio, commandes et délais bornés ; dépassement = échec.
Timer/service sont joints, service MainPID0 et timer inactif ; l'absence du champ
MainPID du timer reste une propriété systemd connue, pas un succès conditionnel.

## Preuve et limites

Le résultat public lie sources locales/distantes, image réellement installée,
rapports frais, captures JPEG inspectées et données natives avant/après. Les
25régressions manuel/public/connexion sont rejouées en série. Les fonctions,
jetons et parents sont nettoyés par leurs vraies API, avec recoupement physique,
base saine, réservations/baux/gardes nuls et artefacts antérieurs préservés.
Les quatre barrières et le watchdog doivent tous passer ; aucun skip ou succès
conditionnel. Une faute du banc reste un reçu préliminaire distinct.

Ce complément vise les pertes de réponse des mutations temporaires. Il ne prouve
ni la source/routes indisponible, ni l'exception inattendue d'une tâche Python
vivante, ni toute la campagne de plateforme. Ces restes demeurent inscrits dans
071.2/.6 et les unités transversales. Statut : opérateur et client implémentés,
relecture ciblée en cours ; non exécutés, aucun nouveau scénario qualifié.

## Premier passage3c50e181 — attente du rendu à corriger

Le premier passage sur96e5dc4e passe accueil/préparation, watchdog et création
avant commit. La barrière de création après commit confirme aussi une seule
ligne/audit, SIGKILL natif, reprise et message inconnu, puis le client échoue
sur `count()==0` au lieu d'une ligne dans la liste de service. Il comptait
immédiatement après navigation et lecture API, avant le rendu asynchrone de
Resource ; la capture d'échec est encore au chargement. Attendre le panneau
et le nombre exact de lignes rendues, sans remplacer la réponse ou réduire
l'assertion. Les états affichés restent ensuite comparés aux métadonnées réelles.

Une fonction est physiquement purgée, le jeton dont la valeur est perdue est
révoqué par son UUID public, parents supprimés et gardes jointes. Aucun problème
produit ni succès de révocation n'est revendiqué. Le reçu incomplet et ses
captures restent préliminaires ; les quatre cas sont rejoués après correction.
