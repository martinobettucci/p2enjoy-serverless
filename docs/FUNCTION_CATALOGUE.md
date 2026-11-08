# Catalogue global des fonctions

Contrat SLS-067, déployé en DEV et en qualification. La console affiche désormais
l’accueil Fonctions ; cette mise en service ne clôture pas les preuves. SLS-066 reste ouverte
pour ses preuves de routes ; ce catalogue ne dépend pas de leur modification.

## Lecture et périmètre

`GET /api/functions` exige la session administrateur réelle, comme la liste des
namespaces. Un jeton technique Read ne donne pas accès au catalogue global ;
il conserve `/api/services/{id}/functions` pour son périmètre de service.
Toutes les lectures excluent fonctions, services et namespaces supprimés.

La recherche couvre noms et UUID des trois niveaux, handler courant et
descriptions existantes des namespaces/services. Le modèle de fonction ne porte
pas de description ; ce changement n’en invente pas. Aucune variable, valeur
secrète, configuration chiffrée, source ou journal n’est lu pour rechercher.
Recherche Unicode sans distinction de casse ni d’accents : NFKD, retrait des
marques combinatoires et casefold. Références standard :
[unicodedata](https://docs.python.org/3.14/library/unicodedata.html#unicodedata.normalize)
et [fonctions SQLite Python](https://docs.python.org/3.14/library/sqlite3.html#sqlite3.Connection.create_function).
Les mots séparés par des espaces se combinent par ET, chacun pouvant figurer
dans un champ différent. `%`, `_` et guillemets sont des caractères littéraux.

Paramètres : `q` de 0 à 200 caractères, au plus huit mots, sans caractère de
contrôle ; `namespace_id` et `service_id` UUID facultatifs ; `state` facultatif
draft/published ; `sort` parmi name_asc/name_desc/updated_asc/updated_desc,
par défaut name_asc ; `limit` 1..100 par défaut 25 ; `offset` 0..2147483647.
Valeurs invalides : 422. Filtres combinés par ET avant pagination. Un UUID absent,
supprimé ou un service hors du namespace demandé donne zéro résultat, sans
élargissement silencieux. L’état published signifie révision active valide,
non supprimée et appartenant à cette fonction ; sinon draft.

Le résultat contient items, total, limit, offset, critères normalisés et parents
sélectionnés (nom/contexte ou disponibilité inconnue). Chaque ligne expose
seulement UUID/nom de fonction, service et namespace, handler, état, UUID de
révision active et date de modification. Tri stable complété par les noms de
parents et UUID ; total, page et sélections proviennent du même snapshot SQL.
Requêtes paramétrées et tris en liste fermée. La normalisation est locale à la
connexion de lecture du catalogue ; aucune migration, table d’index, dépendance
supplémentaire ni changement des lectures existantes.

## Choisir les filtres

`GET /api/catalogue/namespaces` et `/api/catalogue/services` exigent aussi la
session administrateur. Recherche q avec les mêmes règles ; limit 1..50 par
défaut 5, offset borné comme le catalogue. Services filtrables par namespace_id.
Retour items/total/limit/offset ; UUID, nom, description existante et contexte
de parent seulement. Recherche, tri et total avant pagination, parents actifs.
Ces sélecteurs ne chargent jamais une collection entière dans le navigateur.

## Parcours et adresses

Après connexion, `/` affiche Fonctions ; `/console/functions` est son adresse
partageable explicite. Namespaces devient `/console/namespaces`, avec accès
latéral conservé. Les adresses des fiches, facettes, archives et manuel restent
stables. Les fils d’Ariane et retours après suppression nomment la bonne liste.

Le catalogue utilise une table sémantique : fonction, service, namespace,
handler, état, modification. Contexte des homonymes toujours visible. Recherche,
état, tri et filtres actifs appartiennent à cette liste. Namespace/service se
choisissent dans un dialog de saisie : recherche serveur, cinq choix radio par
page, choix Tous et un seul engagement Appliquer. Annulation, focus et mobile
suivent le composant DialogForm et le socle ; aucune nouvelle commande métier.
Choisir un autre namespace retire explicitement le filtre service précédent.

L’URL conserve q, namespace_id, service_id, state, sort et page (base 1, 25 lignes).
La saisie est temporisée de 300 ms ; ses frappes utilisent replaceState, les
filtres/tri/pages pushState. Retour/précédent relisent l’URL. AbortController et
génération neutralisent les réponses anciennes. Chargement et erreur retirent
les anciennes lignes ; vide global et aucun résultat filtré sont distincts.
Page devenue hors limites : recalage sans nouvelle entrée d’historique et focus
sur un élément encore visible. Totaux et rang de page sont écrits.

Une fiche ouverte depuis cette liste porte `catalogue`, uniquement la query
canonique bornée de retour, au plus 4096 caractères. Ce contexte traverse ses
six facettes et fournit Revenir au catalogue ; après suppression depuis ce
contexte, revenir à la même liste, qui se recale. Aucun chemin/hôte libre, jeton
ou stockage navigateur supplémentaire. Les paramètres deployment/operation
gardent leur rôle propre. Une valeur de retour invalide est ignorée, pas suivie.
La redirection HTML vers l’origine canonique conserve ce contexte validé et les
critères valides de l’adresse `/console/functions`, sans redirection ouverte.

## Réalisation et preuves

Unité unique : préciser le contrat, livrer la lecture API puis la console et
le manuel, adapter les anciens clients au parcours via navigation, construire
et déployer sur DEV, qualifier API/UI puis régressions, inspecter les captures
et recouper sources/image/ressources avant clôture. Les noms SLS-067 restent
des références de preuve, pas des libellés utilisateur.

API réelle : session et refus des jetons, recherche globale au-delà d’une page,
UUID/handler/descriptions/Unicode, mots combinés et caractères littéraux,
filtres croisés, homonymes, tris stables, bornes, parents supprimés, brouillon,
publication Docker puis rollback, renommage et absence de données sensibles.
Navigateur depuis l’accueil : catalogue, choix paginés, recherche rapide sous
vrai délai réseau, historique, partage/rechargement, fiche et six facettes,
retour après suppression, erreurs réseau/session, noms longs, clavier, focus,
ordinateur/tablette/mobile, captures observées et manuel compilé recoupé.
Mesurer le coût de lecture sur les données réelles de campagne ; ne pas
présenter une optimisation théorique comme une performance démontrée.

Les clients existants doivent ouvrir Namespaces par la navigation après le
nouvel accueil, et conserver leurs scénarios métier. Le focus desktop du menu
revient au premier lien désormais Fonctions. Les liens Fonctions du service
sont sélectionnés dans leur navigation contextuelle pour éviter toute ambiguïté.
SSO courant et restaurations historiques restent éprouvés avec leurs vrais
accueils respectifs. Aucun mock, interception ou skip ; seules les ressources
explicitement créées par les campagnes sont supprimées puis purgées.

## Suite commune de qualification

Le scope `function-catalogue` de `e2e/execution-suite.py` reprend les 35
campagnes et 467 groupes de la suite `invocation-urls`, puis ajoute les huit
groupes API et quatorze groupes navigateur du catalogue : 37 campagnes et
489 groupes attendus, en série, zéro échec et zéro skip. Les six prérequis
SSO/builds/relevé physique restent distincts des groupes fonctionnels. Chaque
phase conserve ses empreintes de sources locales/distantes, image et rapport
frais. Toute adaptation du banc conserve les scénarios historiques, notamment
la vraie connexion des restaurations sur leur ancien accueil.

Le relevé physique garde les limites de sécurité du collecteur : dix namespaces
et 32 fonctions des campagnes de stockage/adresses, sept namespaces et 32
fonctions du catalogue API, puis six namespaces et 27 fonctions du catalogue UI,
recoupés par trois appels séparés sur leurs UUID exacts. Total : 23 namespaces
et 91 fonctions, distincts des installations historiques restaurées. Les deux
nouveaux jeux incluent des parents vides et vérifient aussi l’effacement réel
des configurations des quinze services synthétiques. Aucun relâchement global
de la limite du collecteur n’est nécessaire.

Les captures de listes longues comprennent des vues au format du viewport pour
garder les textes et le dialog mobile lisibles. Le parcours mobile défile la
table au clavier jusqu’à sa dernière colonne : les captures gauche/droite
complètent la mesure d’absence de débordement du document. Ces images sont
inspectées après exécution ; ni le seul scrollLeft positif ni un JPEG pleine
page réduit ne prouvent la lecture de toutes les colonnes dans le viewport.

## Continuation après correction des seuls clients de preuve

Le replay du 8 novembre s’arrête dans storage-console-ui après 31 campagnes
complètes (461 groupes) : une attente conserve l’ancien retour `/` après
suppression d’un namespace, alors que l’application revient correctement à
`/console/namespaces`. Sept groupes de ce client passent ; les trois suivants
ne sont pas qualifiés. L’essai et ses rapports restent archivés comme incomplets.
Le relevé natif confirme les 39 fonctions purgées des jeux catalogue UI et
stockage UI, dans sept namespaces, sans allocation/réservation restante.

La lecture des captures relève aussi que le viewport mobile initial montre
les filtres, mais pas les lignes de gauche. Ajouter deux vues après focus de
la table : bord gauche puis milieu après défilement clavier réel, avant le
bord droit déjà éprouvé. Les trois positions doivent permettre de lire toutes
les colonnes ; les 16 captures du client gardent ses quatorze groupes.

La continuation conserve uniquement les 30 campagnes réussies dont le client
reste inchangé, soit 447 groupes. Le client catalogue retouché est réexécuté :
son ancien résultat positif reste séparé, hors du total. Sept campagnes sont
alors exécutées en série : catalogue UI (14), stockage UI (10), reprise des
commandes (7), validation vivante (2), décisions (4), historique partiel (1)
et historique complet (4). Résultat attendu : 37 campagnes uniques et 489
groupes, puis le relevé physique final ; six prérequis distincts au total.

`e2e/function-catalogue-completion.py` contrôle la provenance avant tout test :
archive exacte de l’essai, rapports conservés recoupés par SHA et validateur
existant, empreintes avant/après de chaque phase, mêmes images contrôle/CLI.
Les seuls écarts autorisés avec le premier gel sont les deux clients UI,
le présent contrat de preuve et le nouveau pilote de continuation. Toute
autre différence, notamment source produit, manuel compilé, fixture ou image,
refuse cette continuation et exige une nouvelle qualification adaptée.

La preuve conserve les deux époques de sources et l’ordre chronologique réel.
Elle ne prétend pas qu’une commande monolithique initialement en échec a passé.
Chaque campagne retenue doit avoir terminé et nettoyé, zéro échec et zéro skip ;
aucun résultat incomplet ni ancien résultat du client retouché n’entre dans
les 37 résultats actifs. Les nouveaux rapports sont frais sur le nouveau gel.
La séquence nommée complète ne clôture l’unité qu’après inspection des 98 images,
recoupement des ressources, documentation et revue finale.
