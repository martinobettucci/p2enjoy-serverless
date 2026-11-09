# Reprise du paquet dédupliqué — SLS-074

## Périmètre et état attendu

Ce complément de [FUNCTION_VERSION_EXECUTION](FUNCTION_VERSION_EXECUTION.md#publication-et-déduplication)
qualifie la responsabilité des octets d'un upload identique après son commit.
Il vise uniquement le SPARK DEV infra-serverless, au repos, une fonction créée
par les API dans `version-duplicate-recovery-<8hex>`, ses candidats et leurs
répertoires. Les autres fonctions doivent être absentes. Le runtime de référence,
les routes, les fichiers officiels et les images restent inchangés.

La fixture originale `validator-observation.mjs`, en mode success, est publiée
puis promue comme version S. Son import écrit un marqueur réel dans /tmp, attend
5s et exporte le handler. Des appels vérifient la configuration, le secret par
empreinte et les compteurs data/cache. Les uploads suivants réutilisent exactement
le même ZIP, handler et événements en mode code seul.

## Deux cycles réels

1. Observer le validateur du doublon vivant, identifié par labels et montage
   exact /code, avec son marqueur d'import. Épingler le répertoire parent du
   candidat par descripteur NOFOLLOW et relever device/inode, UID/GID et mode.
   Armer et vérifier une garde indépendante avant fchmod000 de cet unique inode.
   Le véritable contrôle doit constater errno13 en ouvrant ce répertoire.
   Le code déjà chargé termine sa validation normalement ; le PUT rend200,
   code_changed=false, hash/UUID de S et container_removed=true. Le candidat
   durable reste published, sans configuration chiffrée, avec réservation positive,
   archive et code présents ; aucune révision n'est créée pour son UUID.
   Le GET santé rend503 et un nouvel upload est refusé avant réception.
   Si une maintenance en cours rend429 avant le503, conserver ce refus connu,
   relire prepared/réservation0 puis effectuer une relance explicite après le
   délai annoncé. Aucun résultat inconnu n'est rejoué. Un appel de S doit encore
   réussir. Restituer explicitement le mode, puis laisser la maintenance normale
   retirer le seul paquet réutilisé et libérer sa réservation, sans redémarrage.
2. Reproduire la même faute sur un autre doublon. Après réception du200 et
   recoupement du commit published/réservation positive, écrire l'intention
   d'interruption puis envoyer SIGKILL au seul conteneur de contrôle exact.
   Constater son arrêt/ExitCode137 ; le candidat published reste conservé.
   Tuer ensuite réellement le helper de faute. La garde indépendante restitue
   le mode et redémarre le même conteneur ; aucun remplacement Compose n'est
   demandé. La reprise de démarrage nettoie le doublon publié sans le reclasser
   failed et libère sa réservation. Un nouveau doublon publié après reprise
   réutilise encore S et se nettoie normalement. Les appels conservent les
   compteurs data/cache, la cible et l'empreinte de configuration.

Ce second cycle coupe le contrôle **après commit et échec de nettoyage**, avec
responsabilité encore inscrite ; il ne prétend pas observer un SIGKILL au milieu
d'un unlink. Cette autre fenêtre reste à éprouver séparément.

## Garde et restitution

Le programme de restitution est figé dans un répertoire root privé sous /run,
avec identité et empreinte, verrou et reçu atomique. Avant chaque mutation, il
vérifie l'inode et son propriétaire. Il ouvre la chaîne de répertoires avec
NOFOLLOW puis applique fchmod sur le descripteur ; un remplacement est refusé.
La garde est armée avant le retrait des permissions et conserve PID/naissance
du helper. Elle peut l'arrêter par pidfd après vérification d'identité.

Le redémarrage ne vise que l'ID/image du contrôle d'origine, avec sa configuration
effective inchangée et le runtime de référence inchangé. Il exige une intention
de coupure persistée et l'arrêt137 de la même incarnation. Une intention de
redémarrage est écrite avant docker start ; une reprise de garde relit l'état
réel et ne rejoue pas aveuglément une opération à issue inconnue. Les configurations
officielles et les montages sont recoupés sans enregistrer leurs valeurs privées.
La restitution explicite du premier cycle et l'expiration indépendante du second
sont distinguées dans leurs reçus ; timers/services/helpers doivent terminer.

## Preuves et limites

Quatre groupes : publication sous EACCES, reprise normale, publication conservée
après SIGKILL du contrôle, puis reprise indépendante et nouvelle déduplication.
Préparation stable et purge ne sont pas ajoutées au nombre de groupes.
Le client maintenu et son helper seront sous e2e, avec rapports privés séparés
des autres campagnes. Toute requête ouverte est jointe même en cas d'échec.
Une permission ou reprise non confirmée conserve la fixture et cleanup=false.

La preuve lie sources/images avant et après, réponses HTTPS, états SQL lus sous
l'identité du propriétaire, fichiers et réservations, marqueur, refus errno13,
signaux et reçus de garde, démarrages, invocations et purge physique par les API.
La version S et son archive sont recoupées avant/après chaque faute. Aucun
fichier officiel, résultat de protocole ou appel système n'est remplacé. Aucune
modification UI ni nouvelle image n'est attendue. Les autres pannes/migrations
et la campagne complète restent dans SLS-074.
