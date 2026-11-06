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
prouve pas les fonctionnalités de plateforme qui restent à construire : SSO,
ACL CRUD, UI, adaptateur de déploiement, règles origine/IP, quotas individuels,
instances chaudes et extinction automatique.

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
