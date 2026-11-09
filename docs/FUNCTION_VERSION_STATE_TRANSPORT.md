# Réponses perdues des décisions de version

Complément de [SLS-074](BACKLOG.md#sls-074), de
[FUNCTION_VERSION_EXECUTION](FUNCTION_VERSION_EXECUTION.md#promotion-et-droits)
et du [précédent de transport réel](SERVICE_CONFIGURATION_URLS.md#preuve-de-transport).
Statut : banc implémenté et qualifié en DEV par les neuf groupes ci-dessous.
Aucun changement produit révélé par cette unité.

## Décision et frontières

Qualifier promotion, archivage avec remplacement et suppression avec remplacement
sur le contrôle008 réellement servi dans le seul SPARK DEV. Ces décisions sont
atomiques dans FunctionVersions ; le nettoyage physique de delete se produit
après la transaction et avant son retour HTTP. Une barrière HTTP après décision
ne sera donc jamais présentée comme une coupure avant effacement physique.

L'opérateur function-version-state-observer.py réutilise NativeObserver sans le
modifier. Il suit uniquement la ligne publique exacte du POST promote/archive
ou du DELETE du hash B de la fonction de campagne. Il ne lit aucun en-tête ou
corps, ne modifie ni buffer, registre, résultat système ou état applicatif.
Deux frontières sont distinguées : retour recvfrom/read avant traitement, puis
entrée du premier write/writev/sendto/sendmsg sur le même socket après commit.
L'inode du socket amont et le port18090 sont vérifiés. Le contrôle est tué par
SIGKILL seulement après constat du discriminant attendu. Mort native signal9 et
Docker137 sont exigées ; le même conteneur et la même image redémarrent.

La CLI réelle promote est employée pour les deux pertes de promotion. Son état
unknown doit conserver UUID/hash sans prétendre que la promotion a échoué ou
réussi. Une trace native limitée aux connexions HTTPS, sans buffers TLS, exige
exactement deux connexions : lecture puis unique tentative de mutation. Aucun
rejeu automatique, même refusé, ne doit être masqué par un simple compte d'audits.
Archivage et suppression passent par les vraies requêtes HTTPS authentifiées.
Une perte ne vaut jamais succès du client ; l'état durable est relu séparément.

## Périmètre et restauration

Namespace version-state-transport-XXXXXXXX, service et fonction propres au banc,
uniques fonctions vivantes avant toute suspension. Aucune invocation, instance,
validation, réservation ou opération de stockage active pendant l'attachement.
Les fixtures originales function-versions.cjs, leur dépendance marqueur, l'agent,
les volumes données/cache, les jetons et le SSO sont réels. A utilise primary,
B utilise secondary ; aucune copie du code client de référence.

Une garde serverless-restore-version-state-UUID est armée avant ptrace. Son
programme figé conserve ID/image du contrôle, PID/naissance/cgroup du processus,
identité de la référence et verrou de mutation. Elle peut tuer le seul observateur
exact, libérer une suspension puis démarrer le contrôle original. Le verrou
joint toute mutation d'arrêt avant restauration. Un programme d'arrêt figé hérite
explicitement de son FD, attend le vrai client Docker borné, puis écrit un reçu
root avant de le libérer. Si cet arrêt a été demandé, la restauration exige son
reçu de succès avec Docker137 ; une issue inconnue interdit de redémarrer le
contrôle et n'est jamais présentée comme stop_mutator_joined. Timer et service
doivent être inactifs avant la fenêtre suivante, et le helper local est joint
avec une borne explicite. Préfixes, UUID, propriétaire,
droits et absence de remplacement sont vérifiés. Aucun fichier officiel, route,
variable ou secret de cellule n'est modifié.

Un cas distinct tue l'observateur pendant la suspension, sans requête métier,
puis exige reçu indépendant, contrôle sain, état métier identique et garde finie.
Le client joint chaque helper et chaque requête même en échec. Si la restitution
n'est pas confirmée, il conserve les objets plutôt que lancer leur purge.
Erreurs bornées par phase/type/code/coordonnées/empreinte, sans message brut,
corps privé, jeton, mot de passe ou pile Playwright dans les rapports.

## Matrice et discriminants

Neuf groupes prévus, exécutés séquentiellement :

1. Depuis l'accueil et le vrai SSO, créer namespace/service/fonction/configuration,
   publier A/B par l'adaptateur et les API, promouvoir A, invoquer A/B ; refus
   directs de mutations avec Read et sans If-Match. Variables, secret par empreinte
   et authentification métier sont recoupés. Les six refus initiaux conservent
   toutes les données métier et ajoutent exactement six audits request.denied ;
   ces audits de sécurité ne sont pas confondus avec une mutation de version.
2. Perte de l'observateur suspendu et restauration indépendante, sans mutation.
3. Promotion B par la CLI : perte avant traitement ; A et ETag/audit inchangés,
   CLI unknown sans rejeu, puis relance explicite réussie et appels B/A.
4. Promotion B par la CLI : perte après commit avant réponse ; B et ETag/audit
   persistés une fois, CLI unknown sans rejeu ; relecture et appels sans renvoi.
5. Archivage B courant avec remplacement A : perte avant traitement, B disponible
   et courant sans changement ; relance explicite puis A appelée/B refusée.
6. Même archivage, perte après commit : A courant et B archivé atomiquement,
   audit unique et code conservé ; pas de renvoi, restauration B puis appel épinglé.
7. Suppression B courant avec remplacement A : perte avant traitement, aucune
   décision ; relance explicite puis effacement confirmé et B refusée.
8. Même suppression, perte après décision avant réponse : A courant/B deleted,
   audit unique ; reprise du nettoyage si nécessaire, sans renvoi de la mutation.
   Réimportation explicite et validée de B conserve son hash et sa date initiale.
9. Relecture finale, appels A/B avec compteurs données/cache persistants, purge
   publique de la fonction et des parents, vérification physique et gardes finies.

Chaque fenêtre de mutation part d'un état disponible connu. Promotion part de A,
archivage/delete de B avec remplacement explicite A. Les anciennes versions sont
remises en état par les API entre fenêtres ; ces opérations préparatoires sont
identifiées, jamais confondues avec la mutation interrompue. Les premiers hash et
date de promotion restent immuables. Avant traitement, snapshot métier exact.
Après décision, pointeur/handler/runtime, état, ETag et audit exactement corrélés ;
configurations/variables/secrets, candidats et autres versions sont conservés.
Les mutations de last_used_at d'un jeton ne sont pas des décisions métier.

Seize appels réussis sont prévus : deux initiaux, deux par fenêtre, deux finaux.
Les refus ne s'ajoutent pas à ce total. Les six coupures du contrôle vérifient
la persistance des deux compteurs. Aucun HTTP502 attendu ne devient un succès
métier ou une preuve de ce qui n'a pas été reçu par le client.

## Livraison et limites

Rapports function-version-state-transport{,-checkpoint}.json sous .local/e2e,
refus d'écrasement et sources/images recoupées avant/après. Les reçus root des
sept gardes, audits, versions, révisions, octets et invocations sont recoupés par
une collecte indépendante en lecture seule. Les trois notes du SPARK sont
proposées avec le démarrage final, sans adoption implicite. Backlog, README,
journal, changelog et preuve conservent les tentatives exclues séparément.

Le banc ne prouve ni coupure au milieu d'un commit WAL, ni perte avant nettoyage
physique de delete, ni panne propre du restaurateur. Les premières promotions
Create interrompues, autres fenêtres de publication et la régression complète008
restent dans SLS-074. Aucun nouveau parcours UI, manuel, migration ou build
produit n'est prévu pour cette unité. Toute correction produit révélée est
spécifiée et reproduite avant changement, puis qualifiée séparément.


## Résultats retenus

Les [réponses perdues des décisions de version](evidence/function-version-state-transport-dev-2026-11-09.json) passent9 groupes
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

Les six refus initiaux sont403/428 et ajoutent exactement six request.denied :
leurs statuts et modèles de route internes sont comparés par SHA, toutes les
anciennes entrées et autres données métier conservées. Les deux premiers essais
s'étaient arrêtés sur cet attendu du banc : égalité globale des audits, puis
préfixe public /api ajouté à tort au modèle interne. Les snapshots, sources et
nettoyages sont conservés séparément. Aucun défaut produit n'est attribué à ces
écarts. Les corrections de garde/verrou/diagnostics précèdent la campagne.

Le démarrage final du contrôle est 2026-11-09T20:51:15.542532163Z. Les branches de timeout du client
Docker, de secours SSH et de nettoyage en erreur restent non provoquées ; les
revues statiques n'en constituent pas une preuve E2E. Le cas indépendant nominal
n'éprouve pas une panne propre de son restaurateur.
