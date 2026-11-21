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
