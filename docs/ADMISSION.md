# Admission et mutations du moteur

Contrat de réalisation SLS-040/050, complément d'EXECUTION et STORAGE_AGENT.
Le contrôle reste un processus unique, propriétaire du verrou durable de cellule.

## Budgets et attente

Cinq valeurs de cellule bornent les fonctions, en excluant contrôle, agent et
validations : SERVERLESS_FUNCTION_CPU_BUDGET (défaut 1, de 0.05 à 64),
SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB (8192, de 128 à 1048576),
SERVERLESS_FUNCTION_INSTANCE_LIMIT (32, de 1 à 256),
SERVERLESS_WAITING_CALL_LIMIT (128, de 1 à 4096) et
SERVERLESS_FUNCTION_WAITING_CALL_LIMIT (16, de 1 à 256, <= plafond global).
La première configuration DEV conserve ces défauts sur la cellule de 16 Gio.
CPU est réservé en nano-CPU entiers, par arrondi supérieur, avant Docker.
Les minima de toutes les fonctions actives de gestion, brouillons compris,
doivent tenir simultanément dans les trois budgets. Seules les fonctions ayant
une révision active font effectivement démarrer leurs instances minimales.

Une place d'attente est réservée après autorisation et avant réception du corps,
avec un plafond de 1 Mio et un délai de réception de trente secondes. Cette
place couvre receiving puis queued. Le délai de file commence après réception
complète et conserve la valeur alors courante de queue_timeout_seconds.
Zéro signifie une seule tentative immédiate ; un démarrage Docker reste permis
si ses ressources peuvent être réservées immédiatement. File pleine et délai
de file expiré rendent 429. Aucun corps, en-tête métier ou jeton brut n'est
persisté dans la file. Les demandes attendent en ordre d'arrivée par fonction ;
une fonction bloquée ne bloque pas les demandes admissibles des autres fonctions.

La déconnexion avant admission retire la demande. Après admission, une tâche du
moteur conserve la responsabilité de l'appel et de ses effets jusqu'au résultat
ou à sa deadline, même si son client HTTP disparaît. Aucun rejeu automatique.

## Réservations et générations

La migration du contrôle ajoute execution_instances, invocations et
function_operations. Une ligne d'instance conserve UUID, fonction, révision,
génération, CPU, RAM, état, instants et instantané chiffré de configuration.
Elle existe avant toute création Docker ou acquisition de bail et disparaît
seulement après destruction et libération confirmées. Les références de ces
lignes empêchent suppression logique et physique de leur révision.

Les états sont starting, ready, busy, draining et cleanup_failed. Tous comptent
dans les budgets globaux et le maximum de la fonction, anciennes générations
comprises. L'admission relit dans une transaction courte les droits, la politique,
le service, la fonction, sa révision, les opérations en cours et les budgets.
Elle affecte une instance ready de même génération ou réserve une nouvelle.
La concurrence compte les appels admis, y compris pendant leur démarrage.
Le mode data exclusif s'applique à toutes les générations du même UUID.

La génération est une empreinte canonique de révision, nom, configuration de
fonction et environnement/secrets effectifs ; un chiffrement aléatoire ne
provoque pas à lui seul un changement de génération. L'empreinte privée ne sert
pas à exposer les secrets. Les appels admis utilisent leur instantané jusqu'au
bout ; les anciennes instances au repos sont retirées. Les instances occupées
sont retirées après terminaison. Les minima de nouvelle génération attendent
les ressources réellement libérées par les anciennes.

L'inactivité commence quand l'instance devient prête ou termine son dernier
appel. idle_seconds=0 retire immédiatement les instances excédant le minimum.
Les instances minimales restent chaudes. Sous pression, des instances prêtes
au-dessus du minimum de leur fonction peuvent être retirées, les plus anciennes
d'abord. Leur budget reste réservé jusqu'à fermeture confirmée.

## Reprise et observations

Les invocations conservent identité d'acteur, service/fonction/révision/instance,
état, instants, code d'erreur fixe, statut HTTP, handler_started et logs expurgés
bornés à 64 Kio. Les corps et réponses métier ne sont pas conservés. L'historique
est borné à 10000 invocations terminales et sept jours ; les appels actifs ne
sont jamais supprimés par rétention. Les logs ne rejoignent pas l'audit de gestion.

Au démarrage, avant admission : retirer les seuls conteneurs et réseaux de
cette installation, libérer leurs baux, nettoyer leurs canaux, puis restituer
leurs réservations et références. Un échec conserve les réservations et dégrade
la santé. Les attentes perdues deviennent interrupted avec handler_started=false ;
les appels dispatchés perdus gardent true si observé, sinon null. Aucune échéance
monotone enregistrée n'est réutilisée après redémarrage. Les opérations de
fonction sont réconciliées avant réouverture de leurs admissions.

## Configuration de stockage en deux phases

Un inverse configure(old) après un configure(new) ne garantit pas un rollback :
il peut conserver un volume nouveau désactivé ou manquer du budget libéré puis
consommé par un tiers. Le protocole prépare donc la mutation sans publier sa
configuration, sans libérer son ancienne allocation et sans permettre de bail.

L'agent ajoute prepare-configuration, commit-configuration et abort-configuration,
avec function_id et operation_id UUID. Préparer prend configuration et version
attendue du registre. L'agent conserve dans son intention durable la configuration
cible, les nouveaux types de volumes, la création initiale éventuelle de fonction,
l'ancien état et la réservation supplémentaire. Il arrête les anciens montages,
sonde réellement ancien usage et quotas cibles, puis inscrit prepared avant de
répondre. Les lignes de volumes gardent leur ancienne allocation jusqu'au commit.
La configuration courante reste inchangée ; acquire et les mutations concurrentes
sont refusés pour cette fonction.

Commit exige le même UUID d'opération et une préparation achevée. Il publie
atomiquement quotas, activation et configuration, incrémente la version, libère
la réservation de préparation et écrit le reçu committed. Abort conserve les
volumes antérieurs et leurs données ; il retire uniquement les volumes créés par
cette préparation après confirmation de leur absence de consommation et de leur
vacuité. Une donnée inattendue interdit la suppression et garde une erreur
récupérable. Une fonction initialement absente et restée vide peut être retirée.
Un reçu par fonction conserve operation_id et committed/aborted ; la répétition
de la même décision est idempotente, la décision opposée est refusée. Une nouvelle
préparation peut remplacer le reçu précédent après résolution de son intention.

Une préparation interrompue survit au restart de l'agent. Celui-ci arrête ses
éventuels démons partiels, conserve sa réservation et attend la décision du
contrôle ; il ne transforme pas implicitement une préparation en commit ou abort.
Un commit exige toujours la marque prepared durable. Un abandon reprend son
nettoyage après panne, sans effacer de fichier antérieur ni baisser le budget tôt.
Le configure direct historique reste atomique côté agent et garde ses commandes
d'opérateur ; sa compensation retire aussi les lignes nouvelles restées vides.

Côté contrôle, function_operations ferme les nouvelles admissions avant une
mutation de stockage. Les appels actifs rendent 409 ; les instances au repos
sont fermées et leurs baux libérés. Préparer est effectué hors transaction SQL.
Après cette attente, droits et versions sont relus. La transaction de publication
modifie l'objet et marque la décision commit dans function_operations ensemble.
L'agent reçoit ensuite commit ; l'intention n'est retirée qu'après confirmation.
Un crash avant la décision entraîne abort ; un crash après entraîne commit.
Une révocation après la décision ne défait pas une mutation déjà autorisée et
commise. L'admission reste fermée tant que cette décision n'est pas réconciliée.

Les mutations sans changement de stockage publient leur nouvelle génération
sans interrompre les appels admis. Les modifications de service refusent une
opération de fonction concurrente incompatible. Les créations configurent leurs
volumes avant de rendre la fonction disponible ; une création abandonnée ne
laisse aucune allocation, instance ou fonction visible.

La suppression de fonction exige aussi le drainage des instances au repos et
refuse des appels actifs. Sa décision logique ferme durablement l'admission et
porte l'intention d'archive ; cette décision précède l'archivage irréversible.
Le cache se vide et les données archivées se purgent par opérations explicites,
avec contrôle administrateur pour la purge. Aucun appel d'agent n'est effectué
pendant une transaction SQLite du contrôle.

## Entrée HTTP

La passerelle utilise exclusivement X-Serverless-Token avec Read, quelle que soit
la méthode HTTP ; le cookie admin ne remplace pas ce jeton. Elle refuse les
occurrences multiples de ce jeton ou d'Origin. Le résolveur IP existant reste
l'autorité : pair TCP et chaîne X-Forwarded-For uniquement depuis un proxy approuvé.
Les CIDR IPv4-mapped de préfixe >=96 sont convertis en IPv4 comme les adresses.
Les origines HTTP(S) sont exactes, le port zéro refusé. Ces normalisations sont
partagées entre configuration et comparaison de la passerelle.

Les chemins sont les chemins décodés ASGI exacts ; aucun retrait implicite de
slash final ni correspondance par préfixe. Une révision ne peut déclarer deux
alias implicites pour la même méthode. L'événement v1 utilise /<chemin déclaré>,
y compris pour un alias implicite ; requestContext.identity.sourceIp et
requestContext.requestId viennent du contrôle. Les dictionnaires simples gardent
la dernière occurrence ; les dictionnaires multiValue conservent toutes les
occurrences. Une collection vide et un corps vide utilisent respectivement null
et une chaîne vide. Les cookies de contrôle sont retirés individuellement ; les
cookies métier et Authorization sont conservés.

Le préflight demande une méthode déclarée et au plus 64 noms HTTP valides dans
4096 octets, sans doublon après normalisation. Les noms autorisés sont ceux que
le navigateur peut émettre, dont content-type, authorization et x-serverless-token ;
les noms de contrôle x-csrf-token, cookie et les champs hop-by-hop sont refusés.
CORS renvoie l'origine explicite si la politique ET/OU accepte cette requête,
sans credentials. Vary porte Origin, Access-Control-Request-Method et
Access-Control-Request-Headers pour le préflight, Origin pour les autres réponses.

Les réponses de fonction conservent leurs en-têtes métier validés ; les en-têtes
de sécurité propres à la console ne les écrasent pas. Le contrôle réserve
X-Request-ID et X-Serverless-Request-ID. Une absence de code donne 409, un chemin
absent 404, une méthode absente 405, une attente refusée 429, une erreur du handler
ou de réponse 502, une panne du runtime/stockage 503 et une deadline 504.
Les erreurs publiques exposent un code fixe et l'identifiant d'invocation ; aucun
message de processus ou secret n'y est copié. HEAD retire le corps final.
