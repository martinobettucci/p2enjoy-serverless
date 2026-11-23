# Diagnostic réel du débit d’invocation

Contrat de SLS-133.2, décidé le22novembre2026 avant code. Complément de
RETENTION_SCHEMA_011 et INVOCATION_SOURCE_RETENTION_VOLUME. Le rouge9406 reste
inchangé ; aucun résultat de ce diagnostic ne valide le nominal10001HTTP+1cron.

## Question et données disponibles

La mesureRO de l’original restauré contient2999invocations, aucun événement du
journal et au plus248appels pour une fonction. La sélection d’attente utilise
invocation_function ; les recherches d’expiration et de borne numérique
parcourent les métadonnées, avec un tri temporaire pour cette dernière. Ce sont
des coûts réels de cette base, sans attribution suffisante du ralentissement
observé à8511appels dans l’installation temporaire disparue. Le corpus saturé
du rouge n’a pas été sauvegardé ; il n’est pas reconstruit depuis son JSON.

## Passage diagnostique décidé

Ajouter au client réel existant le seul mode explicite --production-profile.
Il conserve accueil/SSO, installation isolée f73/runtime réels, garde2700,
deux fonctions chaudes et deux flux sériels HTTP indépendants. Chaque fonction
reçoit3000appels, soit6000réponses originales, dont corps, UUID, séquence et hash
sont vérifiés. Les limites métier, budgets et cadence ne sont pas changés.
Le futur créneau du témoin demeure planifié, mais le diagnostic purge et
restitue avant lui : aucun cron n’est attribué à ce passage.

Aux jalons du premier flux256/1024/2048, puis après les6000réponses, un opérateur
RO mesure le vrai contrôle temporaire. Les nombres réellement présents sont
conservés : le second flux peut progresser pendant un prélèvement. L’opérateur
exige le work/campaign reconnu, mode instance-limit sans replay, image/CID,
répertoires/configuration et namespace/fonctions exacts du passage. Il lit les
deux tables de configuration du banc pour l’identité, jamais les valeurs
de secrets. Son programme ne modifie aucune ligne ni index et n’appelle aucune
maintenance directement. Aucun remplacement de réponse, clock ou dépendance.

Dans le Python/SQLite du conteneur réellement exécuté : connexionmodeRO,
query_only, transaction de lecture cohérente, schéma011 exact et inventaire des
deux fonctions. Recueillir les horodatages réellement enregistrés, plansEQP,
tempsmonotone/CPU du processus de mesure, pasVDBE àquantum100 et nombre de
résultats pour les requêtes exactes d’admission, expiration et candidats aux
deux rétentions. Chaque SELECT a une limite d’instructions explicite et reste
RO. Comparer des mesures successives authentiques, jamais des corpus reconstruits
par suppression ou insertion. Conserver les deux répétitions chaudes et la
première séparément, sans prétendre reproduire son état de cache initial.

Les intervalles created→queued→admitted→dispatched→completed sont conservés
comme durées de phases, pas comme tempsCPU du handler. Les périodes de mesure
et leur effet possible sur la charge sont nommés. Les écritures/COMMIT/fsync
ne sont pas quantifiées par des SELECTRO ; si cette piste reste nécessaire,
une observationnative distincte du PID/naissance/cgroup réellement recoupés sera
contractualisée avant code. Les anciens compteurs de PID nonattribués sont exclus.

## Résultat et nettoyage

Le rapport porte production-profile et zéro groupe de qualification. Les deux
contrôles diagnostiques (production avec relevés, puis purge/restitution) ne
deviennent pas les trois groupes du nominal. RapportUUID et stdout distincts ;
un wrapper gèle sources/image/installation avant/après et joint le vrai client.
Il n’y a aucun rejeu automatique. Toute marge/frontière manquée reste rouge.

La clôture réutilise exactement le chemin existant : min0/idle0, disparition des
instances, révocation du jeton, deux purges publiques, retraitservice/namespace,
contrôle physique puis restitution nominale, driver/timer/service joints.
Original011/collection, référence, configuration et5982artefacts sont recoupés.
Les modes nominaux et les quatre diagnostics d’observateur gardent leurs
options, seuils et assertions. Le module de clôture partagé évite de recopier
une version affaiblie du nettoyage.

Une mesure concluante motive une décision de correction avant code produit.
Le profil ne clôt pas133 : nominal3, régressions affectées et campagnescomplètes
demeurent nécessaires.


## Portée du compteur CLI à corriger — SLS-133.7

La synthèse du client nomme real_http_handlers le nombre d’éléments du tableau
responses, qui contient les réponses de charge. Le vrai command-timeout
078126da affiche0 pour ce champ, alors que son reçu natif conserve une
invocation HTTP et une planifiée réellement démarrées. Cette synthèse ne doit
pas présenter un compteur de réponses comme un nombre de démarrages observés.
La clarification sera décidée et codée avec le profilage productif133.6, puis
éprouvée sur ses vrais passages. Les rapports passés et leur comptage de groupes
restent intacts ; ce libellé n’est pas utilisé pour qualifier les pannes134.
