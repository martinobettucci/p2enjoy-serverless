# Console : recherche, édition et exploitation

Périmètre demandé le 8 novembre 2026. Unités
[SLS-067 à SLS-073](BACKLOG.md#sls-067), rattachées à SLS-060.
Ce document spécifie les parcours à livrer. Leur état de réalisation reste dans
le backlog ; le manuel décrit les fonctionnalités effectivement disponibles.

## État de départ

La console possède la hiérarchie namespaces/services/fonctions, la publication
ZIP avec handler, les révisions, les instances et les invocations. Les journaux
expurgés se consultent dans le détail d’une invocation. Les mesures Docker
actuelles sont des relevés manuels ; l’allocation et la consommation sont
distinctes. Le catalogue et la recherche globale SLS-067 sont implémentés et
qualifiés à leur checkpoint. Favoris, actions en masse, éditeur de fichiers,
client HTTP intégré, journaux avancés et monitoring historique restent à
implémenter. Le [suivi des demandes](DEMANDES_ET_LIVRAISON.md) expose ces absences.

Le parcours cible est : retrouver une fonction, lire sa configuration effective,
modifier son code, publier, appeler sa véritable URL puis retrouver les journaux
et mesures du même appel. Les droits, révisions et identifiants de corrélation
accompagnent ce parcours.

## Catalogue et recherche

SLS-067 ajoute un catalogue global de fonctions, destiné à devenir l’entrée
opérationnelle après connexion. La gestion des namespaces reste une destination
de structure. Les fiches et leurs adresses existantes restent accessibles.

La recherche couvre les noms de fonction, service et namespace, l’identifiant
stable, le handler et les descriptions. Les filtres de namespace, service et
état se combinent. Le serveur recherche dans tout le périmètre autorisé avant
pagination ; les valeurs de secrets sont exclues de la recherche et de l’index.
Le tri est stable, les totaux et filtres actifs sont visibles. Une recherche
vide, sans résultat ou en erreur possède son état propre.

L’URL conserve recherche, filtres, tri et page. Un retour depuis une fiche
retrouve la liste précédente. Une réponse ancienne ne remplace pas une recherche
plus récente. Le champ et les résultats sont utilisables au clavier, avec
contexte du service visible lorsque plusieurs fonctions portent le même nom.
Le [contrat détaillé SLS-067](FUNCTION_CATALOGUE.md) fixe les champs existants,
API, bornes, sélection des filtres et navigation à réaliser.

## Favoris personnels

SLS-068 permet d’épingler namespaces, services et fonctions. Les favoris sont
personnels, persistés côté serveur et rattachés à l’identité SSO stable, afin
de suivre la personne entre appareils. Leur ordre est conservé. Ils référencent
les UUID et suivent donc un renommage.

La navigation donne un accès direct aux favoris et permet leur retrait. Un
objet supprimé ou devenu inaccessible est indiqué comme indisponible, sans
divulguer ses informations à une identité qui n’y a plus droit. La personne
peut retirer cette référence. Les jetons techniques de service ne modifient
pas les préférences personnelles d’un administrateur.

## Opérations en masse

SLS-069 ajoute sélection et actions aux listes de fonctions, services et
namespaces, par type d’objet. Sélectionner une page désigne ses seuls objets ;
l’interface montre les noms et le nombre exacts de la sélection. Un lot porte
au plus 256 UUID explicites et leurs versions. Une nouvelle recherche n’étend
pas silencieusement une sélection existante.

Le renommage propose préfixe, suffixe, remplacement de texte et correction
individuelle dans un aperçu ancien nom/nouveau nom. Le serveur valide droits,
versions, grammaire et collisions dans chaque parent avant application. Un lot
de renommage est atomique. Les UUID, volumes, références de jetons et historiques
sont conservés. Les appels admis gardent leur contexte ; les suivants utilisent
le nouveau nom. Le parcours fournit les changements de manifeste nécessaires
pour que le prochain déploiement réutilise les mêmes UUID. Le contrat de
l’adaptateur ajoute pour cet export `p2enjoy.function_id` : l’UUID explicite est
résolu avant le nom et son appartenance au service est vérifiée. L’aperçu rappelle
la mise à jour du manifeste utilisé par le projet. La preuve inclut un nouveau
déploiement du manifeste exporté, avec conservation des UUID et des volumes.

La suppression présente les objets et leurs effets avant confirmation. Pour
une fonction, elle conserve la sémantique d’archivage ; la purge reste une action
administrateur distincte. Les parents occupés restent soumis à leurs règles.
La progression et le résultat sont suivis par objet : terminé, refusé, en attente
ou interrompu. Les réussites et refus restent consultables après rechargement.
Une opération corrélée reprend ses décisions durables sans appliquer deux fois
une suppression ni ressusciter un objet après un échec partiel.

## Éditeur de code et handler

Le [contrat détaillé](CONSOLE_EDITOR.md) fixe API, droits, brouillons privés,
conservation de la base, bornes, diff, publication et preuves de SLS-070.

SLS-070 ouvre l’arborescence du code d’une fonction avec édition des fichiers
texte, recherche dans le fichier et réglage du handler. L’accès aux sources
requiert les droits de publication existants : Create sur un brouillon initial,
Update sur une fonction publiée, ou la session administrateur. Le jeton Read
d’invocation seul ne donne pas accès aux sources ni à leur téléchargement.

Une édition crée un brouillon à partir d’une révision identifiée. L’utilisateur
distingue brouillon enregistré et code déployé, voit le diff et les conflits de
version, et retrouve son brouillon après une fermeture. Les saisies non
enregistrées sont signalées avant de quitter. Les limites de fichiers et de
contenu s’appliquent aussi au navigateur ; fichiers binaires et dépendances
sont identifiés comme tels.

Publier crée une nouvelle révision immuable par le pipeline de validation Docker
existant. Le handler est validé avec les véritables modules et dépendances de
l’artefact. Une modification de dépendances ne promet pas une installation
automatique ; l’archive doit contenir les dépendances exécutables correspondantes.
Un import refusé conserve la révision active et le brouillon à corriger. Le
parcours permet de consulter le diagnostic, de tester la révision publiée et
de revenir à une révision précédente.

Le versionnement de [SLS-074](FUNCTION_VERSIONS.md) s’applique aussi à l’éditeur :
un paquet inchangé réutilise son hash ; un changement crée une version après
validation. Publier prépare une version invocable par hash ; seule une promotion
explicite modifie la cible des appels sans tag. Le retour à un ancien hash conserve les
configurations et volumes courants.

## Client HTTP par fonction

SLS-071 ajoute une facette Tester, avec choix de méthode et d’URL issue de
[SLS-066](SERVICE_CONFIGURATION_URLS.md#domaines-du-spark-et-chemins-dappel),
paramètres de chemin/query, en-têtes, corps texte/JSON et fichiers admis par
la passerelle. Elle montre la révision effectivement appelée, le statut,
les en-têtes, le corps, la durée et l’identifiant de requête. Une réponse
volumineuse ou binaire conserve une restitution et un téléchargement bornés.
Avec SLS-074, le sélecteur choisit la cible courante ou un hash disponible ;
l’adresse versionnée reste dans le périmètre de cette même fonction et la
réponse indique le hash effectivement appelé. Une version indisponible ne
provoque jamais de repli vers un autre code.

Le mode par défaut exécute un véritable appel HTTP depuis le serveur de console,
comme un client d’API. L’utilisateur connaît cet emplacement et l’origine
déclarée ; l’adresse IP évaluée est celle de cet appel. Seules les adresses
publiques calculées pour cette installation sont des destinations possibles.
Le choix de chemin ne transforme pas ce client en relais HTTP arbitraire.
La destination utilise `/invoke/UUID_DE_LA_FONCTION`, ou avec SLS-074
`/invoke/UUID_DE_LA_FONCTION@HASH_VALIDÉ`. L’UUID et le hash sont vérifiés
séparément ; aucune autre fonction n’est une destination de ce testeur. Les
redirections ne sont pas suivies. Les cookies de console ne sont pas transmis à la fonction.
Un mode navigateur permet de vérifier le comportement CORS depuis la véritable
origine de la console. Les deux contextes sont explicitement distingués.

Chaque appel utilise un jeton Read réel et traverse la passerelle normale, avec
les règles d’origine/IP et l’authentification métier dans Authorization. Un
administrateur peut fournir un jeton ou créer explicitement un jeton temporaire
limité à cette fonction, expirant après quinze minutes. Sa valeur reste en
mémoire de la page ; elle est retirée des exemples copiés, journaux et erreurs.
Les corps et en-têtes sensibles d’une requête ne sont pas enregistrés dans les
préférences ni dans l’historique de la console.

L’appel renvoie vers son observation et ses journaux. Une annulation distingue
l’arrêt de l’attente de l’issue du handler déjà admis. L’interface respecte les
refus de la passerelle et ne rejoue pas automatiquement une invocation incertaine.
Les exemples cURL et paramètres non sensibles peuvent être copiés pour reproduire
un appel depuis le véritable client métier.

## Journaux et corrélation

SLS-072 complète les journaux existants par une consultation par fonction et
service : période, sévérité lorsqu’elle est connue, état et identifiant d’appel.
Le suivi des nouveaux événements peut être activé ou mis en pause. Les formats
texte et JSON sont lisibles ; un niveau absent reste non renseigné.

Un appel relie fonction, service, révision et hash exécuté, instance, requête, chronologie et
diagnostic. Les événements de plateforme permettent aussi de retrouver une
publication, un démarrage, une extinction, un dépassement de délai ou une
opération de stockage. Les erreurs de code se distinguent des refus d’admission
et des défaillances d’infrastructure. Recherche et export respectent les ACL.

Collecte, taille, durée de conservation, historique interrogé et exports sont
bornés. Les secrets connus sont expurgés et les valeurs d’authentification ainsi
que les corps métier ne sont pas journalisés automatiquement. La console
signale troncature, rétention expirée et collecte indisponible. Les journaux
restent du texte échappé, accessible au clavier et lisible sur mobile.

## Monitoring et alertes

SLS-073 ajoute des vues plateforme, namespace, service et fonction, avec séries
historiques : nombre d’appels, erreurs, refus, délais dépassés, latence et
percentiles avec taille d’échantillon, attente, démarrages à froid, instances,
CPU, mémoire et stockage. Chaque grandeur conserve unité, période, source et
distinction entre allocation, plafond et consommation. Une donnée manquante ou
un échantillon insuffisant est indiqué.

Les vues rapprochent ces séries de la santé du contrôle, du moteur Docker, de
l’agent de stockage et des nettoyages en attente. Des seuils configurables
produisent des alertes consultables dans la console, avec état, début, fin et
lien vers les objets et journaux concernés. Les alertes se dédupliquent et leur
rétablissement est visible. Le rafraîchissement peut être suspendu.

Collecte et agrégation utilisent les mesures réelles, une rétention et un budget
bornés. Leur coût est mesuré sur le SPARK ; les graphes exposent l’intervalle et
les lacunes de collecte. Le parcours mène d’un incident à ses appels et à leur
révision. Les dates, filtres et liens permettent de partager le même diagnostic.

## Livraison et preuves

SLS-031 et SLS-065 sont qualifiées. Les URL SLS-066 sont déployées ; leurs
preuves résiduelles de source restent ouvertes. Le catalogue SLS-067 est
qualifié : 37 campagnes uniques / 489 groupes, deux époques de clients sur les
mêmes images, 98 captures inspectées. Les campagnes de routes à deux puis six domaines ont été exécutées ; SLS-066
conserve d'autres preuves résiduelles de source. Favoris, opérations en masse,
éditeur/client HTTP et journaux/monitoring restent absents de l'implémentation. Cette progression ne clôture ni
ne dispense les preuves restantes de SLS-066. Les vues de journaux et mesures
existantes restent le socle des parcours intermédiaires.

Chaque unité livre API, interface, persistance ou migrations nécessaires, manuel
affiché et preuves E2E sur le SPARK DEV. Les parcours partent de l’accueil réel
avec le SSO ; les captures sont inspectées sur ordinateur et mobile. Couvrir
droits et accès directs, concurrence, versions obsolètes, erreurs, limites,
redémarrage, réponse perdue et récupération des ressources selon l’opération.
Les données, fichiers, requêtes et mesures de qualification sont réels et créés
par les interfaces normales. Les préférences, brouillons et suivis persistants
sont vérifiés après reconnexion et redémarrage.
