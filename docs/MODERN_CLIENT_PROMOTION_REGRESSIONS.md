# Préparation des dix clients modernes du socle

Contrat de [SLS-109](BACKLOG.md#sls-109), après108 et avant le prochain078.
L’audit RO du21novembre2026 relève dix chemins de préparation qui publient
avec le contrat actuel puis attendent un défaut choisi automatiquement. Ils
n’ont pas été atteints par le passage078 arrêté à service-transport. Ces
constats sont statiques ; aucun nouveau résultat E2E n’est déduit de l’audit.

## Périmètre fermé

| Client | Groupes conservés | Attente à raccorder |
| --- | ---: | --- |
| service-configuration |13|Deux fonctions publiées puis invoquées sans tag ; conserver héritage/surcharges et changements communs.|
| invocation-urls |8|Séparer catalogue du hash pilote et catalogue du défaut ; choisir explicitement la nouvelle cible après changement de chemins.|
| invocation-urls-ui |6|Texte vide courant ; vrai upload puis choix UI du hash ou promotion avant copie/appel des adresses.|
| function-catalogue-api |8|Deux publications A/B avant état published, alias actif et invocation sans tag ; retour explicite conservé.|
| function-catalogue-ui |14|Préparation CLI avant invocation et filtre published ; sélection de défaut explicite.|
| storage-console-api |9|Publication des deux fonctions et remplacement homonyme avant leurs écritures réelles.|
| storage-console-ui |10|Vrai upload UI avant écritures via invocation ; conserver widgets de stockage et choix de cible explicite.|
| storage-command-recovery |7|Deux fonctions puis scénario d’archive ; garder gardes, pertes et purge réelles.|
| storage-validation-recovery |2|Cible et voisine ; distinguer tentative/alias/hash et conserver validation, droits et refus.|
| storage-decision-recovery |4|Trois fonctions avant les fautes de décision/session ; préserver décisions durables et inconnues.|

Total :81groupes ciblés, puis25communs, soit106groupes. Les nombres viennent
du mapping verify_report actuel, pas d’un nouveau découpage. La fixture commune
publication-fixtures empaquette seulement ; elle ne choisit aucune cible et
ne doit pas acquérir un effet caché de promotion. Aucun fichier
invocation-url-fixtures n’a été trouvé : aucune dépendance inventée.

Les deux storage-legacy publient sur la vraie image historique003 avant
upgrade010 : leur activation historique reste attendue. Les quatre clients
stockage bas niveau et les deux campagnes CLI plan/refus ne présentent pas
le chemin fautif identifié ; ne pas leur appliquer une promotion fictive.

## Contrats et décision avant code

Lire intégralement SERVICE_CONFIGURATION_URLS, INVOCATION_URLS,
FUNCTION_CATALOGUE, CONSOLE_STORAGE et FUNCTION_VERSION_EXECUTION, puis les
dix sources et leurs aides pertinentes. Établir le rapprochement complet de
leurs groupes et persister les attentes/gestes avant changement. Distinguer
candidat, alias canonique et hash ; relire l’ETag après la promotion. Un
réupload identique conserve son alias et sa cible ; une configuration commune
ne crée pas à elle seule une nouvelle identité de code.

Le pipeline reste pilote. Préparer explicitement le défaut seulement lorsque
le scénario doit réellement invoquer sans tag ou filtrer published ; une
épreuve de pilote doit rester telle. Ne pas remplacer un geste UI par une
API, changer le produit pour satisfaire l’ancien banc ou retirer des refus.
Aucune fausse réponse, aucun mock ni succès conditionnel. La clarification
IR-001 de SERVICE_CONFIGURATION_URLS décrit désormais les URL par hash déjà
implémentées, en conservant les preuves historiques et les critères ouverts
de SLS-074. Elle ne qualifie aucun des dix clients de cette unité.

## Qualification

Les81groupes et25communs passent en série sur les vrais composants du SPARK
DEV, sources/images figées et reçus exacts. Captures fraîches ouvertes une à
une, manuel source/rendu recoupé, gardes/restaurations physiques et tous les
consommateurs rejoints, code/volumes/secrets purgés par les API, parents
supprimés et jetons révoqués. Recouper5982originaux, référence, configuration,
38backends et4web servis ; aucune image historique changée.

Un défaut distinct découvert devient une unité avant traitement. Une preuve
manquante garde109[~]. Les106groupes de109 ne s’ajoutent pas aux543 de078 :
celui-ci requiert ensuite son passage complet49campagnes/18prérequis au nouveau
gel.105/106/107 et108 conservent leurs propres époques et comptes.

## Décisions détaillées du 21 novembre 2026, avant code

Les dix clients complets et les cinq contrats requis sont rapprochés. La cause
commune est une préparation qui traite published comme une activation ; le
moteur courant conserve au contraire un pilote jusqu’à promotion. Les refus,
concurrences et gestes testés restent ceux du code courant.

Une aide explicite `e2e/promotion-fixtures.mjs`, nommée
`promotePublishedFunction`, pourra mutualiser les préparations API. Elle ne
publie rien : vérifier résultat terminal, hash disponible et alias canonique,
observer le défaut avant, relire la fonction et son ETag juste avant le POST
réel de promotion, puis contrôler résultat, cible et catalogue. Chaque appel
reste écrit au point de préparation du client, avec reçu dans son tableau
observations/evidence. Aucun effet ajouté à publicationArchive ou deploy.
Les deux parcours UI ci-dessous ne passent pas par cette aide.

- **service-configuration** : après le contrôle de placement provider/surcharges,
  constater les deux pilotes et promouvoir explicitement les deux résultats
  du premier deploy. Tous les réuploads suivants conservent le même code ;
  contrôler hash/alias et défaut inchangés, sans promouvoir implicitement à
  chaque deploy. L’import de throws reste refusé et les effets communs partiels
  restent vérifiés sur le code antérieur.
- **invocation-urls** : comparer le catalogue CLI avec `version=HASH`, jamais
  avec le défaut vide. Constater séparément le catalogue sans version avant
  promotion, promouvoir les deux premières fonctions, puis vérifier les URL
  stables sans tag et leurs appels. Au second upload, observer ancien défaut
  et nouveau pilote avec ses nouveaux chemins avant promotion explicite de
  explicit-entry. Le rollback par révision conservé doit rétablir ancien code
  et événements. Le nouveau pilote de l’autre fonction ne déplace pas sa cible.
- **invocation-urls-ui** : contrôler le texte courant « Aucune cible par défaut ».
  Après vrai upload, recouper en lecture le hash disponible et défaut NULL,
  puis cliquer **Adresses de cette version** sur sa carte réelle. Tous les
  parcours copie/curl/appel, refus du presse-papiers, panne réseau, clavier et
  mobile gardent cette sélection `?version=HASH`. Cette preuve reste pilote,
  aucune promotion API ou UI n’est nécessaire à son objet.
- **function-catalogue-api** : chaque deploy A puis B reste pilote ; constater
  le catalogue global inchangé avant de promouvoir explicitement son résultat.
  Vérifier ensuite published, alias courant, hash exécuté et rollback de A.
- **function-catalogue-ui** : sa préparation reste la vraie CLI existante,
  suivie d’une promotion API explicitement nommée avant invocation sans tag et
  filtre published. La création depuis l’accueil et les quatorze parcours de
  liste/filtres/focus/historique gardent leurs vrais gestes ; aucune mutation
  UI de publication n’était revendiquée dans cette préparation.
- **storage-console-api** : les uploads de fn et peer, puis du remplacement
  homonyme, renvoient le résultat terminal au lieu du seul candidat préparé.
  Promouvoir explicitement chaque résultat avant écritures Docker ; conserver
  le candidat séparé pour la lecture du diagnostic après purge.
- **storage-console-ui** : garder vrai upload et réglage des volumes par UI,
  attendre la carte de hash disponible, puis utiliser **Promouvoir cette
  version** et sa confirmation sur cette carte. Observer le vrai POST et la
  cible relue avant le jeton créé par UI et les écritures. Remplacer l’attente
  générale de l’ancien libellé de publication par ces états sémantiques précis.
- **storage-command-recovery** : publier puis promouvoir fn/peer avant les
  fichiers initiaux, ainsi que la troisième fonction avant l’archive fautée.
  Gardes/agent/socket/SIGKILL/rejeux restent identiques ; le refus d’artefact
  cible l’alias canonique publié, pas l’UUID supposé du candidat.
- **storage-validation-recovery** : publier puis promouvoir cible et voisine
  avant le vrai import lent. Garder le candidat des imports fautés séparé des
  alias initiaux ; comparer les révisions conservées avec revision_id terminal,
  jamais avec l’ID de préparation présumé équivalent. Aucune faute supprimée.
- **storage-decision-recovery** : publier puis promouvoir les trois fonctions
  avant fichiers/archivage ; garder deux sessions SSO indépendantes, retrait
  réel de session, agent terminé sous transport refusé, writer occupé et garde
  de redémarrage indépendante. Aucun changement des helpers de faute.

Les captures ciblées ne remplacent pas celles du socle commun : toutes les
nouvelles captures sont ouvertes individuellement. Ajouter le contrat109 à
l’index de sources ; la nouvelle aide y entre par l’inventaire normal e2e.
La source produit et l’image b452 restent inchangées. La qualification complète
106 groupes s’exécute seulement une fois cet arbre relu, figé et déployé.

## Correspondance exhaustive des groupes conservés

Les libellés ci-dessous proviennent des dix sources avant modification. Les
préparations changent, aucun de ces 81 groupes n’est retiré ou fractionné.

### service-configuration — 13 groupes

1. Provider conservé dans le service et seules surcharges dans les fonctions
2. Invocations Docker : héritage et surcharge de secret effectifs
3. Modification commune et rotation : appels admis stables, suivants actualisés
4. Provider absent préservé et suppression de surcharge rétablissant l’héritage
5. Droits : configuration commune refusée avant toute publication
6. Catégories provider vides : retrait des valeurs et secrets communs
7. Échec partiel : code actif conservé et changement commun explicite
8. Redéploiement d’une ancienne configuration aplatie puis nouvelle valeur commune
9. Version obsolète du service et collision effective refusées
10. Remplacement de 128 secrets et validation stricte du drapeau
11. Configurations effectives : collision et dépassement refusés avant mutation
12. Fusion connue trop grande : CLI refusée avant toute modification
13. Redémarrage du contrôle : valeurs communes, surcharges et jeton persistants

### invocation-urls — 8 groupes

1. Brouillon : domaines réels mais aucune URL appelable
2. Read requis : anonymat, droits CRUD seuls, portée, service et révocation
3. Bornes et vrais Host/X-Forwarded-Host sans influence sur les domaines
4. CLI : publication et catalogue identique à celui de la console
5. Appels des vraies adresses : entrée implicite, casse, chemins et méthodes
6. Renommage : l’adresse implicite conserve son UUID
7. Nouvelle révision puis rollback : événements et code de la même révision
8. Suppression : catalogue refusé sans ancienne adresse conservée

### invocation-urls-ui — 6 groupes

1. Accueil normal, création UI et lien des adresses depuis le service
2. Publication UI réelle puis adresses de la révision publiée
3. Presse-papiers natif : adresse et exemple GET, invocation du code Docker
4. Refus natif de presse-papiers : erreur utile et texte sélectionnable
5. Vraie coupure réseau : anciennes adresses retirées et reprise explicite
6. Clavier et mobile 390 px, nom long complet, URL et exemple lisibles

### function-catalogue-api — 8 groupes

1. Session administrateur requise sur les trois catalogues, jetons techniques refusés
2. Recherche globale avant pagination, homonymes et métadonnées minimales
3. Unicode, descriptions, UUID, handler, mots ET, caractères littéraux et absence de secrets
4. Filtres namespace/service/état combinés, UUID inconnus et aucun élargissement
5. Quatre tris stables et pagination sans doublon sous noms identiques
6. Sélecteurs de parents recherchés et paginés sur toutes leurs données
7. Publication réelle A/B, catalogue de la révision active, invocation Docker et rollback
8. Renommage et suppression relus sans index ni résultats obsolètes

### function-catalogue-ui — 14 groupes

1. Accueil normal, vide global et création par la navigation de gestion
2. Jeu réel au-delà d’une page, homonymes et publication exécutée par Docker
3. Recherche globale, contextes des homonymes et pagination au clavier
4. Choix de namespace et de service recherchés, paginés et combinés avec l’état
5. Recherche invalide corrigée vers la recherche appliquée puis vers une saisie vide
6. Saisie rapide sous vrai délai réseau : requête ancienne annulée et résultat récent conservé
7. Tri, historique précédent/suivant et rechargement conservent les critères de l’URL
8. Retour filtré à la page deux conservé dans les six facettes
9. Retour au catalogue par défaut sans perdre le contexte vide
10. Coupure réseau réelle retire les anciennes lignes puis permet une relance explicite
11. Absence réelle du cookie de session et restauration de la session autorisée
12. Tablette et mobile : noms longs, défilement local et choix au clavier
13. Suppression réelle depuis la page deux, retour puis recalage vers la dernière page existante
14. Liens de contexte, stockage navigateur et erreurs JavaScript

### storage-console-api — 9 groupes

1. Stockage et archives : authentification, CRUD, portée et CSRF
2. Versions obligatoires, schéma strict et prérequis de purge
3. Vrais fichiers Docker : cache vidé, données et révision conservées
4. Rejeu corrélé après reconstruction et conflits de commande
5. Invocation active : refus et abandon durable sans effacement
6. Cache absent et cache désactivé conservant son allocation
7. Archivage, schéma strict de purge, version et administration
8. Purge réelle du code et des volumes, reçu terminal et voisin intact
9. Catalogue paginé, parents supprimés et noms réutilisés sans confusion d’archives

### storage-console-ui — 10 groupes

1. Accueil, créations UI et consultation initiale sans volume
2. Onze archives de pagination créées et supprimées depuis les parcours UI
3. Configuration des volumes, publication et jeton depuis la console
4. Confirmation annulée, vidage réel, données conservées et focus
5. Réponse réellement perdue, UUID cohérent et reprise sans second vidage
6. Conflit réel, suivi inconnu et reprise de lecture explicite
7. Session retirée et reprise avec la vraie session
8. Suppression UI des parents et accès autonome aux archives
9. Purge : nom exact, annulation, mobile, terminaison et focus
10. Filtres, pagination après vraie panne réseau et identifiants recoupés

### storage-command-recovery — 7 groupes

1. Garde indépendante : helper tué et agent réellement repris
2. Agent suspendu : observation indisponible et abandon sans effet
3. Révocation pendant préparation : autorisation relue avant décision
4. UUID d’une autre garde : refus sans abandon de son propriétaire
5. SIGKILL avant décision : abandon durable sans effacement
6. Après commit : panne du cache, révocation, SIGKILL et rejeu sans second effet
7. Purge : artefacts refusés, budget conservé et reprise après SIGKILL

### storage-validation-recovery — 2 groupes

1. Socket Docker : SIGKILL du helper puis restauration indépendante et nettoyage du vrai validateur
2. Purge pendant import vivant : attente du nettoyage Docker et effacement du diagnostic tardif

### storage-decision-recovery — 4 groupes

1. Purge : session administrateur fermée pendant préparation, abandon sans effacement
2. Après décision : transport agent refusé, reçu conservé et reprise sans second vidage
3. Après décision : writer contrôle occupé, agent terminé et garde indépendante du writer
4. Contrôle arrêté après décision : redémarrage effectif par garde indépendante
