# Qualification isolée du plafond d’instances

Contrat de correction de [SLS-099](BACKLOG.md#sls-099), préalable au test du
plafond global de [SLS-078](SCHEDULES.md). Cible unique : SPARK DEV
infra-serverless. Aucun changement de FORGE ni écriture de variable officielle.

## Décision du 11 novembre 2026

Le scénario abandonné abaissait le plafond officiel de32 à2, puis réécrivait32.
Sa restitution pouvait écraser une édition concurrente. Le refus préventif a
été qualifié, mais demander une écriture conditionnelle à FORGE était une
mauvaise dépendance : elle protégeait une mutation introduite par le test,
pas une nécessité du moteur. Cette demande est retirée.

Qualifier la même règle sur une installation temporaire de la plateforme,
configurée dès son démarrage avec un plafond de deux instances. Le plafond de
l’installation habituelle reste32. Le budget1CPU empêcherait de tester isolément
32 instances à0,05CPU chacune : le refus CPU interviendrait en premier.

## Installation temporaire réelle

Réutiliser la fenêtre gardée de `e2e/storage-legacy-environment.py`, décrite dans
[STORAGE_LEGACY_PROOF](STORAGE_LEGACY_PROOF.md#fenêtre-et-conservation-des-données),
avec un mode distinct `instance-limit`. Aucun ancien serveur ni fausse dépendance :
l’image immuable est exactement celle du contrôle servi, avec ses migrations,
son SSO, son ordonnanceur, son runtime Docker et son agent de stockage réels.

- Précontrôle au repos, sauvegardes natives et identités des trois répertoires
  contrôle/artefacts, stockage et canal ; référence conservée en fonctionnement.
- Garde indépendante armée avant arrêt du contrôle habituel et de l’agent.
  Les originaux sont conservés par renommage, puis des répertoires neufs
  appartenant au propriétaire réel sont placés aux mêmes chemins. La nouvelle
  installation reçoit son UUID par le démarrage applicatif normal.
- Le conteneur `serverless-api-instance-limit` sert temporairement le même18090
  par les routes HTTPS existantes. Le contrôle habituel est arrêté et conservé
  par ID ; il ne partage aucune base ni aucun volume avec cette installation.
- Les deux fichiers officiels restent les sources de configuration et de secrets.
  La définition Compose temporaire fixe uniquement
  `SERVERLESS_FUNCTION_INSTANCE_LIMIT: "2"` pour son propre conteneur.
  Cette configuration de déploiement DEV est explicite ; aucun fichier `.env`,
  proposition `.?`, PUT console ou réglage de test dans le code applicatif.
- Le banc vérifie la valeur réellement consommée2, les budgets CPU/RAM inchangés,
  l’égalité de l’image au contrôle habituel et les identités distinctes des données.
- Nouvelle connexion SSO normale depuis l’accueil public, sans transfert de session
  ni insertion SQL. Les objets, jetons, publications et promotions passent par
  les vraies API ; les handlers originaux sont exécutés dans Docker.

Cette fenêtre interrompt temporairement la console DEV habituelle, comme le
banc historique existant. Les commandes de preuve sont strictement en série.
Le client E2E sollicite le déploiement ; il ne démarre aucun serveur applicatif
local ni ne remplace le calcul d’admission.

## Scénarios requis

1. Deux fonctions à0,25CPU/128Mio occupent deux instances réelles ; la troisième
   ne peut pas démarrer, alors que ses CPU/RAM tiendraient encore. Son appel
   HTTP expire en file avec429, sans handler ni troisième conteneur.
2. Une mutation de minimum3 est refusée409 sans changer la fonction ; après
   libération des deux appels, la troisième s’exécute et les budgets se libèrent.
3. À une vraie frontière UTC, le tir planifié d’une troisième fonction est
   `refused_capacity`, sans invocation. Après libération, le prochain tir
   réussit sans rejeu du précédent ; événements et hash exécuté recoupés.
4. Restitution nominale puis EOF, SIGTERM et SIGKILL réels du pilote : originaux
   retrouvés par identité, même contrôle/image avec redémarrage attendu, agent
   sain, référence inchangée, fichiers officiels/propositions conservés.
5. Perte du pilote avec un vrai consommateur Docker : retirer uniquement les
   conteneurs/réseaux de l’installation temporaire, libérer ses baux par le
   véritable agent avant l’arrêt de celui-ci, puis restaurer les originaux.

La garde reprend celle du banc existant : code figé, journal durable, verrou
hérité des commandes bornées, jonction avant restitution, identités vérifiées.
Un répertoire inconnu ou une modification officielle inattendue interdit une
restitution aveugle et reste un échec explicite ; aucune valeur n’est réécrite.
Le retrait complet de l’installation temporaire après panne n’est pas présenté
comme une purge métier réussie. Les purges du nominal passent par les API.

## Intégration et portée des preuves

Le cas de plafond est déplacé du scénario qui modifiait la cellule vers cette
campagne dédiée ; toutes ses assertions sont conservées. La suite publique
et la matrice complète doivent appeler cette campagne : aucun test supprimé,
ignoré ou annoncé réussi par sa seule séparation. Le refus de l’ancien helper
reste maintenu tant que ses appelants ne sont pas remplacés.

Avant clôture : tests propres du nouveau mode, cas HTTP et planifié, reprises,
purges et recoupement des originaux, puis campagnes connexes. Sources locales,
distantes et embarquées, images, rapports et nettoyages sont liés à chaque époque.
Aucune preuve nouvelle n’est acquise par cette décision documentaire.

## Refus avant toute mutation

L’ancien helper reste désactivé pour ses appelants non encore migrés. Il peut
inspecter la cellule, mais ne modifie ni variable ni proposition. Il n’attend
plus une évolution externe : le nouveau parcours le remplace.

### Preuve ciblée du refus

La [preuve du10 novembre2026](evidence/instance-limit-safety-dev-2026-11-10.json),
client6e573c0, passe deux groupes réels restore/EOF avant mutation sur317 sources.
Le namespace est supprimé, budgets32/1CPU/8192Mio, services, quatre fichiers
et5982 artefacts antérieurs conservés. Elle qualifie uniquement ce refus,
pas le déploiement temporaire, les pannes ni la restitution indépendante.
Le nominal32→2→32 antérieur garde sa propre époque ; il n’est pas rejoué.


## Déploiement et restitutions qualifiés le11 novembre2026

La [preuve de fenêtre](evidence/instance-limit-environment-dev-2026-11-11.json)
passe dix groupes sur327 sources figées : même imagec59b8616, installation neuve
à plafond2 et HTTPS, puis restitution nominale, EOF, SIGTERM, SIGKILL et échéance.
Les trois dernières sont réellement indépendantes du pilote ; timers/services
et processus sont terminés. Fichiers officiels/proposition conservés ; registres
et artefacts originaux comparés avant le redémarrage attendu du même contrôle.
Référence inchangée. Aucune fonction ni session SSO créée par ces dix groupes.
Les admissions HTTP/cron, la perte avec consommateur et le raccordement à la
suite restent à qualifier ; aucun succès de ces scénarios n’est déduit ici.


## Admissions réelles qualifiées le11 novembre2026

La [preuve d’admission](evidence/instance-limit-admission-dev-2026-11-11.json),
clientf2d48d6, passe quatre groupes sur328 sources figées, même imagec59b8616.
Nouvelle connexion SSO depuis l’accueil ; trois fonctions originales publiées
et promues. Deux handlers occupent deux conteneurs à0,25CPU/128Mio chacun ;
la troisième admission expire429/queue_timeout, sans handler ni troisième instance,
alors que les budgets CPU/RAM restent libres. Minimum3 est refusé409 sans
changer updated_at. Après libération, le troisième appel réussit au hash attendu.

À01:35UTC, deux nouveaux appels HTTP occupent les deux places et le tir est
refused_capacity/schedule_capacity sans invocation. À01:40UTC, le tir suivant
réussit au hash planifié, POST/JSON{}, sans authentification injectée. Le premier
refus reste strictement identique ; aucun rejeu. Sept invocations au total,
dont six handlers réussis et une réception rejetée, deux tirs. Les trois purges
publiques terminent, puis la fenêtre retire ses données temporaires et restitue
les originaux. Même contrôle/image avec redémarrage attendu, agent sain,
référence et fichiers officiels/proposition conservés ; zéro écriture de variable.

Les dix groupes de fenêtre gardent leur époque327 distincte ; ils ne sont pas
réattribués au client328. Restent la perte avec consommateur vivant, le transfert
du cas depuis la suite publique et ses régressions. SLS-099 reste[~].


## Perte avec consommateur et raccordement — réalisation

Décision du11 novembre2026 avant code. Le client d’admission ajoute un mode
`--consumer-loss` : nouvelle fenêtre à garde120s, même SSO normal, fonction
originale publiée, puis handler45s démarré vers85s après armement. Le pilote
est tué par SIGKILL après observation running/handler_started et du conteneur.
La garde capture elle-même l’état natif avant retrait du contrôle temporaire :
le même appel doit encore tourner, avec sa fin normale encore future. Elle
retire ensuite son conteneur/réseau et libère le bail réel. Le mode status
retourne ces seuls relevés sans secret pour recouper identités, suppressions,
libération et restitution indépendante. Les ressources étrangères restent
refusées par les contrôles d’appartenance existants. Aucun succès métier ni
purge publique n’est attribué à cette interruption et au retrait de ses données.

La suite publique devient une orchestration en série : trente groupes HTTP
existants, nettoyage complet, puis quatre groupes du plafond isolé. Le contrat
historique du dernier groupe reste un groupe public parent portant le détail
des quatre groupes isolés, sans addition des mêmes assertions au bilan.
Le rapport public conserve ses31 groupes et ajoute le rapport isolé corrélé,
avec ses trois fonctions dans une autre installation, distinctes des quinze
fonctions HTTP. Le rapport HTTP seul porte un nom distinct et ne constitue
pas une campagne publique complète. Une entrée privée SSO est nécessaire au
lanceur ; elle n’entre ni dans ses arguments, ni dans les fichiers ou rapports.
La suite générale transmet cette entrée au lanceur. Les anciens rapports
restent conservés ; une étape échouée ou un nettoyage incertain invalide le
rapport public et interdit la suite. Aucun ancien contrôle n’est ignoré.

Qualification : perte réelle avec consommateur, puis orchestration publique
complète sur sources figées. Les cinq modes de restitution sans consommateur
sont rejoués sur le helper final ; le cas planifié repasse dans l’orchestration.
Les régressions des modes historiques touchés restent nommées jusqu’à leur
exécution. Aucune clôture sur le seul déplacement du test.


### Échec du relevé diagnostique

La revue de b35ffcd constate qu’un échec docker-exec/SQLite du témoin ferait
quitter la garde avant restitution. Corriger ce point dans099 : l’erreur de
capture est persistée par son type, sans donnée sensible, puis la restitution
continue sous ses contrôles d’identité/labels inchangés. Le nominal exige
une capture complète ; un témoin manquant ne devient jamais une preuve réussie.

Un mode `--observer-unavailable` suspend réellement le contrôle temporaire par
Docker pause après un relevé positif et avant SIGKILL du pilote. L’exec doit
alors être réellement refusé, tandis que la garde retire le conteneur suspendu,
son consommateur/réseau/bail et restitue les originaux. Ce mode qualifie la
restauration sous diagnostic indisponible ; il ne prétend pas une capture
positive pendant la faute. La suspension est limitée à l’ID du contrôle isolé,
jamais à celui du contrôle habituel. Réussites nominale et fautée sont distinctes.


### Refus d’appartenance obligatoire

La seconde revue confirme qu’un catch général pourrait absorber le refus
`foreign_namespace`. Seule l’indisponibilité technique du Docker exec est
capturée ; identités, configuration et lecture d’appartenance restent des
préconditions obligatoires. Le namespace est vérifié avant l’exec et de nouveau
après arrêt du contrôle, avant nettoyage des consommateurs. Les erreurs SQLite
qui empêchent de connaître la propriété restent des refus de restitution.

Le mode `--foreign-namespace` crée réellement un second namespace par API,
demande la restitution et exige son refus sans retrait du contrôle temporaire
ni disparition de ce namespace. Le client supprime ensuite son propre objet
de faute par API avant une restitution explicite réussie. Ce parcours ne
s’attribue ni suppression d’un objet tiers ni succès du premier refus.
