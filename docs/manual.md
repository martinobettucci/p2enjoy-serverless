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
Si un rôle manque, **Accès en attente** explique la demande à adresser à un
administrateur du SSO : faire vérifier le compte, puis obtenir le rôle
d'administration si vous devez exploiter la plateforme. Après son intervention,
choisir **Vérifier mon accès**. L'attribution des rôles reste une intervention
humaine ; la page d'attente ne donne accès à aucun objet de gestion.

Une erreur de connexion revient à l'accueil avec son motif. Si la vérification
de la session est temporairement indisponible, choisir **Réessayer** après
quelques instants. La session de console expire au plus tard après huit heures ;
la déconnexion la ferme immédiatement.

## Retrouver une fonction

Après connexion, **Fonctions** présente le catalogue de vos services. La recherche
porte sur les noms et identifiants de fonction, service et namespace, le handler
et les descriptions des namespaces et services. La casse et les accents ne
changent pas les résultats. Plusieurs mots doivent tous être présents ; ils
peuvent appartenir à des champs différents. La recherche accepte huit mots et
200 caractères ; `%` et `_` sont recherchés littéralement. Variables, secrets,
code et journaux ne sont pas recherchés dans ce catalogue.

Choisir un **Namespace** ou un **Service** ouvre sa sélection : rechercher,
parcourir les pages de cinq choix, sélectionner puis **Appliquer**. Choisir
un autre namespace retire le filtre de service précédent. **État** distingue
brouillon et fonction déployée ; **Trier par** classe par nom ou modification.
Le total et les pages de 25 fonctions portent sur tous les résultats des
filtres. Le contexte de service et namespace distingue les noms identiques.

L’adresse conserve la recherche, les filtres, le tri et la page. Elle peut être
partagée ou rechargée. Ouvrir une fonction conserve **Revenir au catalogue**
dans ses différentes facettes. Le retour retrouve la liste filtrée ; si une
suppression a vidé sa dernière page, la liste revient à une page disponible.
**Réinitialiser les filtres** retrouve la liste générale. **Actualiser** relit
le serveur ; une erreur de consultation retire les anciennes lignes et propose
de réessayer. **Namespaces** reste l’entrée pour créer les espaces et services.

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
| Create | Créer une fonction, publier puis promouvoir son premier hash une seule fois |
| Read | Lire les objets autorisés et invoquer les fonctions |
| Update | Modifier configuration et secrets ; publier, promouvoir et gérer les versions suivantes |
| Delete | Supprimer les fonctions autorisées |

Les appels portent `X-Serverless-Token`. L'en-tête `Authorization` reste
disponible pour l'authentification métier du handler. La publication du code
s’effectue dans **Code et révisions**, avec la commande `deploy` de l’adaptateur
ou avec l’API.
Les hashes disponibles sont invocables ; la cible sans tag exige une promotion. Leurs instances et journaux se
consultent dans les facettes Instances et Invocations de la fiche de fonction.

## Publier une archive dans la console

Dans la fiche de fonction, ouvrir **Code et révisions**, puis **Publier une
archive**. Choisir un ZIP de 64 Mio maximum contenant le code et ses dépendances
prêtes à exécuter, puis vérifier le handler : chemin du module et export à appeler.
Confirmer l’archive et la fonction affichées. Les ressources, variables, secrets,
volumes et routes courants sont conservés ; le déploiement d’un manifeste complet
avec l’adaptateur permet aussi de modifier ces paramètres.

Une publication prépare un hash disponible sans le promouvoir. Le résultat
distingue nouvelle version, code inchangé et version réimportée.
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

**Code et révisions** présente les versions par hash, par pages de cinq. Chaque
carte indique sa disponibilité, sa date initiale, son handler, le runtime et
l’espace réellement conservé. **Métadonnées de la version** ouvre les événements,
l’image Node et les références internes des alias historiques. La cible par
défaut est nommée séparément ; sans première promotion, elle est absente.

Le **Hash du code** identifie le contenu exécutable, ses dépendances, son handler
et son descripteur d’exécution. Deux archives recompressées du même paquet ont
le même hash, même si le SHA256 de leurs octets ZIP diffère. **Copier le hash du
code** copie ses 64 caractères ; si le navigateur refuse, sélectionner le texte
affiché et le copier. Actualiser retire la confirmation de copie. Un upload
identique réutilise le hash disponible et sa date initiale ; il ne crée pas de
nouvelle version et ne déplace pas la cible par défaut.

**Promouvoir cette version** demande confirmation du hash et de la fonction,
puis choisit la cible des appels sans tag. Publier A, le promouvoir, puis publier
B permet de conserver A pour les appels courants et d’essayer B depuis
**Adresses de cette version**. Promouvoir B bascule ensuite les appels sans tag ;
promouvoir de nouveau A réalise le rollback. Ressources, variables, secrets,
volumes et données restent courants. Les appels déjà admis terminent avec leur
code et leur configuration d’admission.

**Archiver cette version** conserve son paquet mais refuse ses nouveaux appels,
y compris ceux en attente. **Restaurer cette version** la rend disponible sans
la promouvoir. **Supprimer cette version** retire son accès puis attend la fin
de ses consommateurs pour effacer le code ; le hash et son historique restent
visibles. Pour archiver ou supprimer la cible courante, choisir un autre hash
disponible de la fonction ou désactiver explicitement les appels sans tag,
puis confirmer. Les autres hashes disponibles restent appelables.

**Réimporter cette version** demande le ZIP original d’un hash supprimé. Le
handler et les événements conservés sont repris ; le serveur recalcule et exige
le même hash, après terminaison du nettoyage antérieur. Une archive conservée se
restaure directement. Un upload normal ne restaure pas silencieusement une
version archivée ou supprimée. En cas de réponse perdue, relire la tentative et
le catalogue avant toute nouvelle opération ; une publication incertaine n’est
jamais renvoyée automatiquement.

## Modifier le code dans la console

Ouvrir une fonction puis **Éditeur**, ou choisir **Modifier ce code** sur une
version conservée dans **Code et révisions**. Le contexte distingue la source
publiée, votre brouillon personnel et la cible promue. **Choisir une version
source** permet de parcourir les hashes disponibles ou archivés ; une version
supprimée n’est pas une source. Sans cible sur une fonction déjà publiée,
choisir un hash conservé. Seule une fonction jamais publiée peut partir vide.

**Créer mon brouillon** conserve la base choisie. Un brouillon existant n’est
pas remplacé par une autre source : choisir **Ouvrir mon brouillon**, ou
l’abandonner explicitement. Il appartient à votre compte et reste sur le
serveur après fermeture. Son enregistrement possède un compteur de concurrence,
distinct du hash d’une version publiée. Les sources et brouillons exigent le
droit de publication ; Read d’invocation ne donne pas accès au code.

Parcourir les dossiers ou **Rechercher un chemin**, puis choisir un fichier.
Les listes ont cinq éléments par page. Les dépendances, binaires, tailles et
empreintes sont identifiés. Un binaire ou un fichier de plus de1Mio n’est pas
éditable ; ses octets sont conservés à la publication. Un texte s’ouvre en
lecture. Dans votre brouillon, **Modifier le fichier**, saisir, puis
**Enregistrer le fichier**. Le compteur limite chaque texte à1Mio UTF-8 ; le
brouillon conserve128chemins et4Mio de texte au plus. Les fins de ligne
existantes et l’absence éventuelle de fin de ligne finale sont conservées.

**Rechercher dans le fichier** effectue une recherche littérale sensible à la
casse. **Occurrence précédente** et **Occurrence suivante** sélectionnent le
texte et indiquent sa ligne et sa colonne. Le code large défile dans son cadre.
**Ajouter un fichier** demande un chemin relatif et crée un texte vide ; un
chemin déjà occupé est refusé. **Modifier le handler du brouillon** règle le
module et son export. Retirer un fichier, le rétablir depuis la base ou abandonner
le brouillon demande confirmation. Un fichier ajouté rétabli depuis la base
est retiré du brouillon. Aucune dépendance n’est installée automatiquement.

Une saisie locale est signalée avant changement de fichier, navigation,
déconnexion ou fermeture. Annuler conserve le texte. **Terminer l’édition**
revient à la lecture après enregistrement ou abandon explicite des saisies.
Un refus conserve votre texte ; **Contenu déjà enregistré** signifie qu’aucun
octet n’a changé. Des frappes pendant l’enregistrement restent locales et ne
sont pas présentées comme déjà sauvegardées.

Après un conflit ou une réponse incertaine, **Relire le brouillon serveur**
permet de consulter son nouvel enregistrement sans écraser votre saisie.
Comparer son contenu puis adopter explicitement cette version en gardant votre
texte pour une prochaine sauvegarde, ou choisir le texte du serveur. Une
nouvelle modification concurrente peut encore refuser l’écriture ; il n’y a
ni fusion silencieuse ni répétition automatique.

**Voir le diff avec la cible** compare le brouillon enregistré à la cible
promue actuelle ; les deux hashes et handlers sont indiqués. Choisir un chemin
ouvre son diff textuel borné. Binaires, gros textes et dépassement des limites
sont signalés ; les saisies non enregistrées ne sont pas dans cette comparaison.

**Publier le brouillon** demande confirmation de la fonction, de sa base et du
handler. Le pipeline vérifie réellement le paquet dans Docker. Code inchangé :
même hash ; code modifié : version disponible par hash. La cible promue reste
stable. Un import refusé conserve le brouillon et la cible ; **Validation et
journal** permet de diagnostiquer la tentative. Son UUID est dans l’adresse
avant l’envoi. Après interruption ou réponse perdue, **Relire cette tentative**,
sans renvoyer la publication. Une préparation orpheline peut être abandonnée.
**Adresses de la version publiée** ouvre le pilote ; **Versions, promotion et
retour à un hash** mène aux gestes explicites de promotion et rollback.

L’historique exact de saisie conserve au plus64 gestes et8Mio de fragments
de texte, comptés en UTF-16. Ses compteurs apparaissent pendant l’édition.
Les raccourcis natifs d’annulation et de rétablissement conservent les fins de
ligne exactes. Si une annulation dépasse l’historique disponible, le texte reste
inchangé et un avertissement le signale. Relire un fichier réinitialise cet
historique local ; le brouillon enregistré reste sur le serveur.

Pour annuler le retrait d’un fichier sans abandonner les autres modifications,
ouvrez **Voir le diff avec la cible**, choisissez son chemin puis confirmez
**Rétablir ce chemin depuis la base**. Le même geste retire un fichier ajouté
au brouillon ; il ne modifie aucun autre fichier.

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
Si une fonction refuse son nouveau code, sa cible par défaut est conservée ;
la configuration commune déjà appliquée reste utilisée. Corriger l’import puis
relancer le déploiement. Un refus de modification commune arrête la commande
avant toute publication de fonction.

Le rapport distingue les fonctions publiées, refusées et celles dont l’issue
est inconnue après une rupture réseau. Dans ce dernier cas, consulter le
candidat indiqué avant de relancer. Les valeurs de configuration restent
absentes des sorties et des descripteurs locaux.

Pour un pilote de code, lancer `python3 -m adapter deploy --code-only --config
serverless.yml --service UUID_DU_SERVICE`. Les fonctions doivent déjà exister.
Ce mode transmet seulement code, handler et événements ; il conserve la
configuration du service et des fonctions, sans résoudre les valeurs de variables
ou secrets inutilisées. Le rapport fournit `code_hash`, `code_changed`, la
révision interne conservée et la cible observée au moment de publication.
La CLI vérifie le hash depuis son paquet et le descripteur validé par le contrôle.

Promouvoir séparément avec `python3 -m adapter promote --function
UUID_DE_FONCTION --code-hash HASH_COMPLET`. La commande relit la fonction et
contrôle sa version avant décision. Elle ne charge pas le manifeste. La première
promotion du premier hash exige Create ; toutes les suivantes exigent Update,
même après désactivation de la cible. Read reste nécessaire aux lectures CLI.

## Planifications du manifeste

Les événements `schedule` du manifeste utilisent une expression cron numérique
à cinq champs, en UTC (listes, plages, pas et `*`, dimanche 0 ou 7). La plateforme
contrôle ces expressions aux frontières de cinq minutes : un créneau prévu à
12:02 part à 12:05, jamais avant. Plusieurs créneaux de la même fenêtre sont
fusionnés en un tir ; leur nombre figure dans l'historique. Quand jour du mois et
jour de semaine sont tous deux restreints, l'un ou l'autre suffit.

Ouvrir une fonction puis **Planifications** pour consulter les déclarations de
sa version promue, le prochain créneau nominal, sa frontière de lancement et le
dernier résultat. **Actualiser** relit ces observations. Pendant la lecture ou
en cas d'erreur, les anciennes valeurs et leur pagination sont retirées.
**Réessayer** relit la même page après résolution du problème. L'**Historique des tirs**
présente les créneaux, le retard mesuré, le hash du code et le résultat ; ses
pages et le lien d'invocation permettent de retrouver les journaux. Une expression
se modifie dans le manifeste, puis par publication et promotion de la nouvelle
version. Un upload pilote seul ne crée aucun déclenchement. Une promotion ou un
retour à un hash remplace les planifications de la version précédente.

Le corps reçu par le handler est la chaîne JSON `{}`, avec méthode `POST`, chemin
`/`, en-têtes `x-p2enjoy-trigger: schedule` et `x-p2enjoy-schedule-slot` en UTC.
Aucun jeton plateforme n'est transmis. Les restrictions d'origine/IP concernent
les clients HTTP ; un tir interne conserve les budgets, la concurrence, le verrou
de stockage, la file et le délai d'exécution des fonctions. Une déclaration
`enabled: false`, une cible désactivée ou une fonction supprimée ne déclenche
plus de nouveau travail. Un appel déjà admis conserve son code et termine.

Il n'y a aucun rattrapage ni rejeu automatique : après un arrêt, les fenêtres
manquées sont marquées « Ignoré pendant l'arrêt ». Si le tir précédent de la même
planification tourne encore, le suivant est ignoré pour recouvrement. Une capacité
insuffisante est consignée comme refus. Un échec ou une interruption n'assure
pas l'absence d'effets métier : vérifier l'invocation avant toute relance manuelle.

La plateforme accepte jusqu’à 64 candidats en attente, avec huit par fonction,
et quatre uploads simultanément admis ; une seule validation Docker s’exécute à
la fois. Une fonction conserve vingt hashes disponibles ou archivés. Un doublon
disponible reste admis au plafond après réception, extraction et validation ; un
nouveau hash est refusé sans déplacer la cible. Supprimer une version libère sa
place, puis ses octets après nettoyage confirmé. Les réservations temporaires et
la marge disque restent nécessaires même pour un paquet identique.
Après interruption du contrôle pendant réception ou validation, le candidat
échoue sans publication automatique ; consulter son état avant toute relance.

## Consulter les instances et les journaux

Ouvrir une fonction depuis son service. **Configuration** conserve ses réglages ;
**Instances** affiche les conteneurs réservés, leur état, les allocations et les
mesures disponibles. Le temps CPU est cumulé depuis la création de l’instance.
« Indisponible » signifie qu’aucune mesure n’a pu être obtenue pour ce relevé.

**Invocations** présente les appels les plus récents, leur état et leur statut
HTTP séparément. Ouvrir « Détails et journal » pour lire la chronologie,
le hash demandé et exécuté, la révision interne, l’instance, le diagnostic et
les traces expurgées. La sélection sans tag est nommée « Cible par défaut ». « Non confirmé »
signifie que le début du handler n’a pas été observé avec certitude. Une réponse
métier HTTP 503 peut correspondre à une exécution terminée normalement.

Chaque page contient cinq éléments. **Actualiser** relit la page ; la date du
relevé reste visible. Si des instances disparaissent, la pagination revient
à une page existante. Un journal tronqué est signalé ; les traces longues
se parcourent dans leur cadre, y compris au clavier. Les liens de facette
peuvent être conservés pour retrouver la même fonction.

## Adresses d’appel

Depuis le service, choisir **Adresses d’appel** sous le nom de la fonction,
ou ouvrir cette facette dans sa fiche. Les domaines sont présentés par pages
de cinq avec les méthodes et chemins de la sélection affichée. Par défaut, ils
suivent la cible promue. Depuis **Code et révisions**, **Adresses de cette version**
fixe un hash dans l’adresse de la page, même avant sa première promotion.
**Utiliser la cible par défaut** retire explicitement cette sélection.
**Actualiser** relit domaines, sélection et cible courante. Une version inconnue,
archivée ou supprimée affiche un refus sans proposer les URL d’un autre code.

**Copier l’adresse** copie l’URL complète. **Copier l’exemple curl** copie une
commande avec `VOTRE_JETON` à remplacer par un jeton Read du service. **Exemple curl**
affiche cette commande ; en cas de refus du presse-papiers, sélectionner le
texte pour le copier. Le jeton enregistré n’est jamais ajouté automatiquement.

« HTTPS déclaré » ou « HTTP déclaré » décrit la route du relevé ;
« Disponibilité non vérifiée » indique que ce catalogue ne contrôle ni le
certificat ni l’accès réseau. Un relevé indisponible demande une actualisation
ou une intervention de l’administrateur du SPARK. L’absence de domaine applicable
demande une route vers la passerelle. Un domaine générique sans hôte concret
n’offre pas d’adresse copiable. La console et le SSO gardent leur adresse
canonique ; les domaines supplémentaires servent aux appels.

Le résultat de `deploy` expose également `invocation_urls` pour le hash publié
de chaque fonction, avec son suffixe explicite. Si cette consultation échoue ou si les domaines/la révision changent
pendant la lecture, la publication reste réussie et le rapport signale seulement
les adresses indisponibles. Consulter la facette puis actualiser, sans republier
le code pour obtenir ses adresses.

## Invoquer et suivre une fonction

Après promotion, appeler `/invoke/UUID_DE_FONCTION` si le manifeste déclare
un alias implicite, ou `/invoke/UUID_DE_FONCTION/chemin` pour un chemin déclaré.
La méthode HTTP doit figurer dans cette déclaration. Envoyer le jeton du service
dans `X-Serverless-Token` ; une session administrateur seule n’autorise pas
l’invocation. L’authentification métier peut rester dans `Authorization`.

Pour fixer un code disponible, appeler `/invoke/UUID_DE_FONCTION@HASH_COMPLET`
ou `/invoke/UUID_DE_FONCTION@HASH_COMPLET/chemin`. Le hash est constitué de 64
caractères hexadécimaux minuscules ; une abréviation ou un tag indisponible est
refusé. Les contrôles de jeton, portée, origine et IP restent identiques. La
réponse après admission porte `X-Serverless-Code-Hash`, corrélé avec son journal.
Stable et pilote partagent volumes, limites d’instances, concurrence et budgets.
Les minima préchauffent uniquement la cible promue ; un appel pilote peut faire
arrêter une instance prête pour obtenir sa place, sans interrompre un appel actif.

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
