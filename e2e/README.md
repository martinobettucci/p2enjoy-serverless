# Qualification de la plateforme

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

`native_control_observer.py` porte la classe pure partagée avec le pilote
historique `service-transport-observer.py`. Son corps est déplacé sans changement.
Synchroniser le module dans le même répertoire E2E avant le pilote consommateur.
La [preuve d’extraction](../docs/evidence/invocation-native-observer-dev-2026-11-08.json)
passe `node e2e/invocation-url-transport.mjs` puis `node e2e/service-transport.mjs`
en série : neuf groupes, 201 sources recoupées, six fonctions purgées et six
gardes terminées. Le nouveau pilote pause/libération reste à implémenter ;
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
garde cet arrêt et son diagnostic séparés. Aucun détour ni retrait n’est encore
qualifié ; les actions correspondantes du pilote de garde ne doivent pas être
confondues avec ses trois scénarios réussis sans perturbation.

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
d’administration de FORGE. Les retraits/détours et pages sur six domaines
restent à éprouver séparément ; SLS-066 demeure ouverte.

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
Les sources perturbées, six domaines
réels pour une seconde page et les cycles de routes restent à éprouver.
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
`node e2e/function-storage.mjs`, puis `node e2e/public-invocations.mjs`.
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
node e2e/public-invocations.mjs
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

`instance-limit-guard.py`, piloté par cette même campagne, applique temporairement
32 → 2 par les propositions et l’API normale de la console SPARK locale, puis
restaure 32 et recrée le contrôle. Il refuse une proposition préexistante sur
cette clé, des fonctions étrangères ou des consommateurs actifs. Garder cette
clé sans édition concurrente pendant la campagne. La console locale est donc
un prérequis de preuve ; son absence fait échouer la campagne. Les budgets CPU
et mémoire officiels et consommés sont recoupés pour isoler le plafond testé.

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
