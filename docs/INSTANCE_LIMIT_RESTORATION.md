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
