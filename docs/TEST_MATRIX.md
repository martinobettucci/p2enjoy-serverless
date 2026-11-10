# Matrice de qualification réelle

## Application témoin QLF-001

Chaque ligne doit être exercée contre le vrai service. `tests/e2e.test.cjs`
désigne le client HTTP dans un conteneur séparé ; `tests/operations.py` pilote
Docker et HTTP sur le SPARK DEV. Aucun test ignoré n'est accepté.

| Contrat livré | Preuve E2E |
| --- | --- |
| Catalogue, douze handlers, IDs, mémoire déclarée, stockage | Catalogue complet comparé au contrat |
| Événement HTTP, query répétée/vide/Unicode, corps, contexte | Appels echo depuis le réseau Docker réel |
| Entrée et sortie binaires, HEAD sans corps | Octets exacts, en-têtes et statut |
| Callback, Promise, retour synchrone, callback tardif et erreur | Modes du vrai handler callback ; première réponse gagnante |
| Auth métier configurée, absente, invalide, même longueur | Vrais secrets de cellule ; conteneur sans déclaration d'environnement |
| Configuration et allowlist des secrets | Valeur publique réelle, présence bornée, absence chez echo, logs |
| Compteur CRUD, validation, deux écritures, clés séparées | API réelle et observation des valeurs persistées |
| Cache hit, invalidation, indépendance, reconstruction | API réelle et changement de génération |
| Worker, bornes d'entrées, conflit, checkpoints et tous résultats | Calcul PBKDF2 réel ; 1, 64 et 128 entrées ; reprise HTTP |
| Worker, compteur et cache après recréation | probe avant/après, observations dans volume client uniquement |
| Erreur synchrone, rejet, exit, réponse invalide | Vrais handlers ; invocation suivante saine |
| Deadline sur sommeil et boucle CPU | Exécution réelle, SIGKILL du processus, reaping vérifié |
| Relais nominal, payload, erreurs 500/504/429 | Appels aux vrais pairs, aucune doublure réseau |
| Saturation d'admission et retour au service | Seize vraies requêtes incomplètes ; dix-septième refusée |
| Délai après passage en file, déconnexion client | Charge d'un seul scénario, santé observée, aucun délai arbitraire |
| Routes, méthodes, taille exacte et flux fragmenté | 404/405/413 exacts ; 262144 octets acceptés, 262145 refusés |
| Arrêt actif et en file, redémarrage | SIGTERM réel du conteneur puis HTTP sain |
| Logs, confidentialité et fin des enfants | Docker logs/top réels corrélés aux réponses |
| Confinement Docker et écoute locale | Cgroups réels, écriture EROFS et connexions réseau effectives |
| Refus de manifestes invalides | Démarrages de la même image avec vraies configurations erronées |
| Stockage corrompu, illisible, non inscriptible, compteur maximal | Fichiers réels d'un volume isolé, résultat observé par HTTP |
| Épuisement des processus | Vrai plafond cgroup abaissé dans le seul conteneur isolé, puis restauré |

La matrice qualifie les comportements de l'application témoin et de son
exécuteur de référence. Elle ne mesure pas une couverture de lignes et ne
prouve pas les fonctionnalités propres à la plateforme : SSO, ACL CRUD, UI,
adaptateur de déploiement, règles origine/IP, quotas individuels, instances
chaudes et extinction automatique. Ces fonctionnalités ont leurs campagnes
distinctes, preuves datées et limites suivies au backlog.

## Méthode SLS-000

`tests/git-hooks/test-hooks` exerce les vrais scripts, index Git, commits,
hooks installés, pushes vers un dépôt bare local et garde de fin de session.
Les dépôts sont temporaires ; aucun dépôt client ni remote public n'est modifié.
La présence et l'activation locale des hooks sont vérifiées séparément.

Les résultats datés et les empreintes sont dans `docs/evidence/` ; les résultats
des campagnes antérieures restent historiques et ne qualifient pas un code
modifié depuis leur exécution.

### Instances et baux de stockage — SLS-040/050

Le client `e2e/managed-storage.py` vérifie quatorze groupes réels dans l'image
active du contrôle : acquisition/binds, persistance chaud/froid, quotas data
et cache, partage/isolation/refus de mutation, invocation concurrente et double
démarrage, échec Docker, deadline, annulation pendant acquire, annulation
pendant check, SIGKILL FUSE, arrêt/reprise agent avec nettoyage différé,
volumes désactivés, pagination de 51 baux, diagnostic CLI/EOF. Les ressources appartiennent à une
installation de preuve distincte ; le contrôle conserve son ID durant les pannes.
La simultanéité exacte du résultat métier et de l'échec du watcher est couverte
par revue structurelle ; aucune synchronisation factice n'est présentée comme
une reproduction E2E de cette course.

`e2e/storage-installation.py` vérifie la garde de racine avec agent réellement
arrêté, refus avant création, restauration via propositions de cellule et
identité de registre conservée. Les démarrages invalides associés au nouveau
canal sont vérifiés par les conteneurs isolés de `control-operations.py`.

### Décisions de quotas — SLS-040/050

`e2e/storage-preparations.py` exerce les vrais RPC, montages et écritures Docker.
La réservation de l'ancien quota reste comptée lors d'une baisse, y compris
avec le budget global saturé. Les refus portent sur les mutations concurrentes,
le propriétaire, les baux actifs, la version et la taille réellement occupée.
Commit/abort sont rejoués et une décision opposée est refusée. Le scénario
SIGKILL vérifie preparing après SIGSTOP avant de tuer l'agent ; une préparation
déjà achevée ferait échouer ce contrôle. Le restart après préparation conserve
la décision en attente. L'abandon partiel retire d'abord un cache vide, puis
rencontre une donnée inattendue : le restart doit préserver cette donnée et
l'allocation, avant résolution explicite. Un répertoire antérieur vide est
conservé. Les régressions agent, limites et instances gérées sont exécutées
séparément, en série ; ces preuves ne remplacent pas celles de l'API publique.

### Console de publication et manuel — SLS-062/063

| Contrat livré | Preuve E2E réelle |
| --- | --- |
| Préparation du code, conservation serveur, droits et versions | Dix groupes de `e2e/code-publications.mjs` |
| ZIP depuis la console, suivi, abandon, activation et suppression | 21 groupes de `e2e/publication-ui.mjs`, invocations Docker après activation |
| Réponses perdues après commit, retour sans rejeu | Transport réel, sortie de page puis retour et état serveur recoupé |
| Nettoyage physique refusé, garde et reprise | EACCES Docker réel, 503 après suppression logique, SIGKILL/SIGSTOP du helper et maintenance normale |
| Publication enregistrée avec confirmation de stockage retardée | Suspension bornée de l’agent, 503 réel, décision conservée puis quota confirmé |
| Liste/suivi cohérents et succès antérieur retiré | Observation DOM atomique et cinq gestes indépendants après succès réel |
| Manuel au checkpoint SLS-063 du7 novembre | Huit groupes de `e2e/manual-ui.mjs`, SHA256, onze chapitres, 28 paragraphes, tableau, clavier et formats d’écran |
| Régression commune | `python3 -B e2e/execution-suite.py --scope publication` : 18 campagnes, 312 groupes, zéro échec/skip |

La [preuve finale](evidence/publication-console-dev-2026-11-07.json) recoupe les
rapports frais avec les sources et l’image, les 54 captures inspectées, les
archives conservées, le nettoyage et les notes appliquées au SPARK.

## Planifications et concordance du manuel — SLS-078/096

Checkpoint courant : [preuve009](evidence/schedules-checkpoint-dev-2026-11-10.json).
Exécuter en série, après connexion SSO réelle :

1. `node e2e/schedules.mjs` : six groupes, deux frontières UTC réelles, cron
   Unicode, prévision nominal passé/frontière future, fusion, droits, pilote,
   état désactivé, handler Docker et console depuis l'accueil.
2. `node e2e/manual-ui.mjs` : huit groupes ; concordance du SHA,16 chapitres et
   56 paragraphes, tableau, focus, ancres, formats et session.
3. `python3 -B e2e/public.py` : huit groupes publics.

Vingt-deux groupes courants uniques ; cinq groupes d'une première image restent
distincts, ainsi que le refus Unicode reproduit avant correction. Les neuf
fonctions de tous les essais sont recoupées purgées. Vingt et une captures
courantes sont inspectées ; SLS-096 est clos. Les scénarios de panne,
grammaire complète, recouvrement, saturation, exclusif, rétention et
états UI complémentaires restent à exécuter pour SLS-078. Cette tranche ne
remplace aucune campagne de régression de la plateforme. La campagne complète
SLS-095 doit inclure ces nouveaux clients et cibler les migrations réellement
installées, en conservant les bancs historiques008 dans leur périmètre propre.

Complément indépendant : `node e2e/schedule-versions.mjs`, cinq groupes sur307
sources figées, quatre frontières réelles, cinq handlers et trois fonctions
physiquement purgées. Pilote, promotion, retour par archivage avec remplacement,
retrait, désactivation et suppression sont recoupés ; les appels déjà admis
terminent avec leur hash initial. L'inspection native vérifie l'absence de tirs
après suppression au-delà du404 public. [Preuve](evidence/schedule-versions-dev-2026-11-10.json).
Même image, ID et démarrages,34 backends, configuration officielle et5982
artefacts conservés ; aucune nouvelle preuve visuelle. Les22 groupes précédents
ne sont pas rejoués ni ajoutés à ces cinq groupes. SLS-078.3 est qualifiée.
