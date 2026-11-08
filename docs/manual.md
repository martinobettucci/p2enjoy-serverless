# Manuel d’usage

La console [P2Enjoy Serverless](https://serverless.lelabs.tech) permet de gérer
les services et leurs fonctions, leurs accès, leurs ressources et leurs exécutions.
Ce guide décrit les opérations disponibles dans la version déployée.

Après connexion, choisir **Manuel d’usage** dans la navigation principale.
Sur mobile, ouvrir d’abord **Menu**. Le sommaire mène aux chapitres ; leur adresse
peut être conservée pour y revenir. **Namespaces** ramène à la gestion.

## Se connecter

Ouvrir la console puis choisir **Se connecter**. La connexion se déroule sur
le SSO lelabs ; le compte doit posséder les rôles `verified` et `admin`.
Un refus de connexion revient à l'accueil avec son motif. La session de console
expire au plus tard après huit heures ; la déconnexion la ferme immédiatement.

## Organiser les fonctions

Depuis **Namespaces**, créer un namespace puis ouvrir sa fiche. Créer un service
dans ce namespace, puis une fonction dans le service. Les noms de namespaces
et services sont en minuscules ; ceux des fonctions conservent leur casse.
Une fonction créée sans révision de code est un brouillon.

Les fiches permettent de modifier l'identité, les variables et les secrets.
La fiche de fonction expose aussi mémoire, CPU, durées, concurrence, instances
et stockage. Les erreurs de validation restent dans le formulaire. Si un
autre onglet a modifié l'objet entre-temps, l'enregistrement est refusé pour
préserver la version récente ; annuler puis rouvrir le formulaire pour la relire.

Une variable est visible en lecture. Un secret montre uniquement son nom et
sa présence ; sa valeur enregistrée n'est pas réaffichée. Les secrets et les
variables de service servent de configuration commune aux fonctions. Une
surcharge de fonction doit être explicite.

Pour définir une valeur commune, ouvrir le service puis **Configuration**.
Pour définir une exception, ouvrir la fonction puis sa **Configuration**.
Retirer la valeur propre à la fonction rétablit celle du service. Une modification
commune s’applique aux nouveaux appels ; un appel déjà admis termine avec les
valeurs qu’il avait reçues. Les jetons se gèrent dans l’onglet **Jetons** du service.

## Régler le stockage

Dans la fiche de fonction, ouvrir « Modifier le stockage ». Les données permanentes
et le cache ont chacun une activation et une allocation en Mio. L’enregistrement
vérifie les quotas réels avant confirmation. Un quota inférieur à l’usage est
refusé ; désactiver un volume conserve ses fichiers et son allocation. Une
modification ferme les instances au repos ; elle est refusée à 409 tant
qu’une invocation admise est active.

Si le message indique que la modification est enregistrée mais attend sa
confirmation, relire la fonction avant de recommencer. Une nouvelle mutation
incompatible reste refusée jusqu’à la fin de cette opération. Un redémarrage
reprend la décision persistée ; il ne rétablit pas arbitrairement l’ancienne valeur.
Un rollback du code conserve les réglages et les volumes courants.

## Consulter et vider le cache

Dans la fiche de fonction, ouvrir **Stockage**. Chaque volume indique son
allocation, son état et sa dernière occupation mesurée. Cette occupation est
une mesure logique ; elle peut avoir changé depuis le relevé. Une mesure
indisponible reste signalée. **Actualiser** consulte de nouveau le serveur.
Les quotas et modes se modifient dans **Configuration → Modifier le stockage**.

**Vider le cache** demande une confirmation nommant la fonction. Les données
permanentes, le code, les quotas et les réglages sont conservés. Les instances
au repos sont arrêtées ; une invocation en cours fait refuser l’opération.
Le droit Update est nécessaire via l’API. Un cache désactivé peut encore
contenir des fichiers conservés ; il peut également être vidé.

Le suivi distingue préparation, attente, terminaison et abandon. Une demande
en attente est déjà enregistrée et reprend automatiquement après une panne.
Actualiser relit son résultat. L’adresse contient l’identifiant de l’opération :
la conserver permet de retrouver ce suivi après rechargement. Une réponse
perdue ne signifie pas que rien n’a changé ; consulter le suivi avant de
demander un nouvel effacement. **Ne plus suivre cet identifiant** revient à la
dernière opération de la fonction sans annuler une demande enregistrée.

## Donner un accès à un service

Dans la fiche du service, créer un jeton, choisir ses droits CRUD, sa portée
et éventuellement son expiration. Une portée limitée à des fonctions exclut
le droit Create. La confirmation rappelle les droits accordés.

La valeur complète n'est affichée qu'à la création ou au renouvellement.
La copier avant de fermer son affichage. Chaque valeur nouvellement créée
reste visible indépendamment des autres jusqu'à sa fermeture. Révoquer un
jeton interdit ses nouvelles requêtes ; renouveler révoque l'ancien et fournit
une nouvelle valeur.

| Droit | Usage |
| --- | --- |
| Create | Créer une fonction et sa première révision |
| Read | Lire les objets autorisés et invoquer les fonctions |
| Update | Modifier configuration, secrets et révisions |
| Delete | Supprimer les fonctions autorisées |

Les appels portent `X-Serverless-Token`. L'en-tête `Authorization` reste
disponible pour l'authentification métier du handler. La publication du code
s’effectue dans **Code et révisions**, avec la commande `deploy` de l’adaptateur
ou avec l’API.
Les fonctions publiées sont invocables. Leurs instances et journaux se
consultent dans les facettes Instances et Invocations de la fiche de fonction.

## Publier une archive dans la console

Dans la fiche de fonction, ouvrir **Code et révisions**, puis **Publier une
archive**. Choisir un ZIP de 64 Mio maximum contenant le code et ses dépendances
prêtes à exécuter, puis vérifier le handler : chemin du module et export à appeler.
Confirmer l’archive et la fonction affichées. Les ressources, variables, secrets,
volumes et routes courants sont conservés ; le déploiement d’un manifeste complet
avec l’adaptateur permet aussi de modifier ces paramètres.

La tentative affiche son identifiant et les états réellement observés : attente
d’archive, réception, validation, publication ou échec. **Validation et journal**
ouvre le résultat de chargement et les traces expurgées. **Actualiser** relit l’état.
Une nouvelle consultation efface le message de succès de l’action précédente.
L’adresse de la page conserve la tentative suivie ; elle peut être réouverte.

Quitter ou recharger la page peut interrompre l’envoi. Revenir sur cette adresse
pour consulter le résultat avant de republier : un problème réseau n’implique
pas que la publication a échoué. Le navigateur ne renvoie pas automatiquement
l’archive. Une tentative encore en attente d’archive peut être abandonnée avec
confirmation ; choisir ensuite une nouvelle archive pour recommencer. Une
tentative absente se ferme avec **Fermer le suivi** avant une nouvelle publication.

Si la fonction ou son service a changé entre préparation et publication, le
serveur refuse le candidat. Relire la configuration avant une nouvelle tentative.
Une publication enregistrée peut encore attendre une confirmation de stockage ;
son message reste visible jusqu’à résolution de cette opération.

## Gérer les révisions

**Code et révisions** affiche la révision active et les révisions conservées par
pages de cinq. Les métadonnées donnent le handler, le runtime, l’espace stocké,
l’empreinte SHA256 de l’archive et ses événements. **Activer cette révision**
revient au code choisi après confirmation, en conservant les ressources, variables,
secrets et volumes courants. Les événements de cette révision redeviennent actifs.

**Supprimer cette révision** retire définitivement une archive de code inactive.
La révision active ne peut pas être supprimée ; une instance qui utilise encore
une ancienne révision peut également empêcher sa suppression. Attendre son arrêt,
puis actualiser. En cas de réponse perdue, relire l’historique avant toute nouvelle
opération. Un nettoyage physique peut rester à reprendre alors que la révision
est déjà retirée de la liste ; le message du serveur le précise.

## Publier le code avec l’adaptateur

La commande de déploiement lit `P2_SERVERLESS_URL` et `P2_SERVERLESS_TOKEN`
dans son environnement. Depuis le projet de fonctions, lancer
`python3 -m adapter deploy --config serverless.yml --service UUID_DU_SERVICE`.
Le nom du service doit correspondre au manifeste. Pour publier une fonction,
le jeton requiert Read et Create pour sa première révision, Read et Update
pour les suivantes.

Les variables et secrets déclarés dans `provider` sont enregistrés dans le
service ; les déclarations des fonctions définissent uniquement leurs surcharges.
Modifier une catégorie commune exige Update sur le service. Une catégorie absente
du provider conserve les valeurs du service ; une catégorie déclarée vide les
retire. Dans une fonction, une clé à null retire sa surcharge et rétablit
l’héritage. Les secrets ne figurent pas dans le plan ou le rapport.

Le rapport distingue la configuration commune des publications individuelles.
Si une fonction refuse son nouveau code, elle conserve son ancienne révision ;
la configuration commune déjà appliquée reste utilisée. Corriger l’import puis
relancer le déploiement. Un refus de modification commune arrête la commande
avant toute publication de fonction.

Le rapport distingue les fonctions publiées, refusées et celles dont l’issue
est inconnue après une rupture réseau. Dans ce dernier cas, consulter le
candidat indiqué avant de relancer. Les valeurs de configuration restent
absentes des sorties et des descripteurs locaux.

La plateforme accepte jusqu'à 64 candidats en attente, avec huit par fonction.
Une fonction conserve vingt révisions. Au plafond, l'upload est refusé avant
réception ; supprimer explicitement une révision inactive permet de publier
de nouveau. Après interruption du contrôle pendant réception ou validation,
le candidat devient `failed` avec `control_interrupted`. Consulter son état
avant de préparer une nouvelle publication ; la révision active précédente
reste conservée.

## Consulter les instances et les journaux

Ouvrir une fonction depuis son service. **Configuration** conserve ses réglages ;
**Instances** affiche les conteneurs réservés, leur état, les allocations et les
mesures disponibles. Le temps CPU est cumulé depuis la création de l’instance.
« Indisponible » signifie qu’aucune mesure n’a pu être obtenue pour ce relevé.

**Invocations** présente les appels les plus récents, leur état et leur statut
HTTP séparément. Ouvrir « Détails et journal » pour lire la chronologie,
la révision, l’instance, le diagnostic et les traces expurgées. « Non confirmé »
signifie que le début du handler n’a pas été observé avec certitude. Une réponse
métier HTTP 503 peut correspondre à une exécution terminée normalement.

Chaque page contient cinq éléments. **Actualiser** relit la page ; la date du
relevé reste visible. Si des instances disparaissent, la pagination revient
à une page existante. Un journal tronqué est signalé ; les traces longues
se parcourent dans leur cadre, y compris au clavier. Les liens de facette
peuvent être conservés pour retrouver la même fonction.

## Invoquer et suivre une fonction

Après publication, appeler `/invoke/UUID_DE_FONCTION` si le manifeste déclare
un alias implicite, ou `/invoke/UUID_DE_FONCTION/chemin` pour un chemin déclaré.
La méthode HTTP doit figurer dans cette déclaration. Envoyer le jeton du service
dans `X-Serverless-Token` ; une session administrateur seule n’autorise pas
l’invocation. L’authentification métier peut rester dans `Authorization`.

Le délai de file précède le délai maximal d’exécution. Une file pleine ou
une attente expirée donne 429 ; un dépassement du délai d’exécution donne 504.
Un client déconnecté après admission peut avoir déclenché des écritures :
ne pas rejouer automatiquement son appel. L’identifiant de réponse
`X-Serverless-Request-ID` permet de retrouver son observation.

Les listes `/api/functions/UUID_DE_FONCTION/instances` et
`/api/functions/UUID_DE_FONCTION/invocations` sont accessibles avec Read ou la
session administrateur. `limit` vaut 20 par défaut, au plus 100 ; `offset` permet
la pagination. L’historique conserve états, début observé, erreurs fixes et logs
expurgés. Une mesure Docker indisponible est signalée ; elle ne devient pas
une consommation estimée à partir de l’allocation. Les facettes de la console utilisent ces mêmes observations.

Un corps incomplet est refusé après trente secondes. Sur l’entrée DEV, HTTP/2
transmet immédiatement le 408 ; HTTP/1.1 peut attendre la fin du corps côté
proxy pour le recevoir. Cette attente n’occupe plus de place dans le moteur.

## Définir les restrictions d'appel

La politique du service accepte des origines exactes, par exemple
`https://app.johndalia.com`, et des adresses IP ou CIDR. Choisir ET pour
exiger les deux critères actifs, OU pour accepter l'un des deux. Une liste
vide désactive son critère ; deux listes vides laissent le jeton comme
condition d'accès. Cette politique est appliquée à l’entrée publique et relue avant admission.
Un changement peut refuser un appel encore en file ; il n’interrompt pas un
appel déjà admis.

## Consulter les archives et les purger

Ouvrir **Archives de fonctions** dans la navigation principale. Les filtres
**Conservées**, **Purgées** et **Toutes** et la pagination permettent de retrouver
une fonction supprimée, même si son service ou son namespace a été supprimé
ensuite. Le détail affiche leurs noms et identifiants, la date de suppression,
le stockage et l’espace du code encore occupé ou réservé. Deux objets peuvent
porter le même nom ; leurs identifiants les distinguent.

**Purger les archives** est réservé aux administrateurs. Saisir exactement le
nom affiché puis confirmer. Cette opération efface définitivement les données,
le cache, le code, les variables, les secrets et les réglages propres à la
fonction. Elle conserve les traces de gestion et les identifiants ; elle ne
modifie pas les autres fonctions, les réglages du service ni les sauvegardes.
La console ne propose pas de restauration de ces archives.

Le suivi indique l’effacement des volumes puis du code. Tant que le nettoyage
n’est pas confirmé, l’opération reste en attente et les ressources encore
conservées restent comptées. Un diagnostic permet de signaler une reprise
nécessaire ; **Actualiser** relit l’avancement. Une purge terminée reste
consultable dans le filtre **Purgées**. Conserver l’adresse de suivi permet
également de retrouver le résultat après une interruption de connexion.

Si le stockage a changé de manière inattendue pendant une purge, son suivi reste
en attente avec un diagnostic. Les fichiers de code encore présents restent
conservés et comptés, y compris après un redémarrage. Faire examiner ce diagnostic
par l’administrateur ; une nouvelle demande ne résout pas le changement constaté.

## Consulter les changements et supprimer

L'activité du service présente les mutations et refus attribuables à une
identité connue. Les listes sont paginées.
La suppression demande confirmation. Un service doit être vide de fonctions
actives ; un namespace doit être vide de services actifs. Supprimer une fonction
archive ses données et son cache, en conservant leur allocation. Leur purge est
une opération distincte, accessible aux administrateurs dans **Archives de fonctions**.
