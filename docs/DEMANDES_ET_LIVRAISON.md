# Demandes confirmées et état réel de livraison

Revue du10 novembre2026, après signalement du responsable sur les demandes
manquantes. Périmètre : conversation, spécifications, backlog et sources du
dépôt courant. Cette revue ne constitue pas une nouvelle campagne E2E ni une
vérification de disponibilité de l'installation distante.

## Ce qui manque dans le produit

Six demandes explicites restent à implémenter, même si leurs contrats existent :

| Demande | État constaté | Suivi |
| --- | --- | --- |
| Favoris personnels persistants | Aucune route, persistance ou interface de favoris | SLS-068 |
| Renommage et suppression en masse | Actions individuelles seulement ; sélection, aperçu et traitement de lot absents | SLS-069 |
| Éditer le code et le handler sur place | Upload ZIP et champ handler présents ; arborescence, éditeur, brouillons et diff absents | SLS-070 |
| Client HTTP intégré par fonction, type Postman | Catalogue d'URL/copie présent ; facette de test, requête et réponse interactives absentes | SLS-071 |
| Logging d'exploitation | Logs par invocation présents ; recherche, période, suivi, export et vue de service absents | SLS-072 |
| Monitoring | Relevés Docker ponctuels présents ; séries historiques, tableaux de bord et alertes absents | SLS-073 |

Deux points structurants restent également incomplets : les schedules sont
acceptés et stockés, mais aucun ordonnanceur ne déclenche les crons (SLS-050) ;
la compatibilité d'exploitation avec le projet de référence n'a pas sa matrice
complète ni sa démonstration par contrats reproduits dans les fixtures originales
(SLS-030). Les nombreux tests du moteur ne ferment pas ces deux exigences.

Ces travaux appartiennent au périmètre confirmé. Ils n'attendent pas une nouvelle
demande du responsable. Une unité inscrite dans le backlog n'est pas une unité
livrée, et un nombre de groupes de tests ne mesure pas la couverture du produit.

## Traçabilité des autres demandes

| Demande confirmée | Présence dans le dépôt | Limite réelle |
| --- | --- | --- |
| Méthode Software Factory dans le dépôt, hors formation | Socle, contrats, rôles et hooks importés ; SLS-000 | La méthode ne vaut pas réalisation des fonctions produit |
| Application de qualification originale ici | qualification/, manifeste, handlers et bancs ; QLF-001 | Ses succès ne démontrent pas toutes les fonctions de plateforme |
| Docker comme socle | Contrôle et moteur Docker, runtime et agent de stockage | Certaines pannes et régressions complètes restent à éprouver |
| Namespaces, services, fonctions et UI de gestion | Routes CRUD et formulaires présents | Console globale encore incomplète ; SLS-060 |
| CPU, mémoire, allocations, concurrence, min/max | Modèles, admissions Docker et UI présents | Qualification résiduelle SLS-040/050 |
| Durée d'exécution et arrêt après inactivité | timeout_seconds et idle_seconds séparés, moteur et UI | Ne pas confondre les deux délais ; qualifications datées dans SLS-040 |
| Disque permanent par ID, données/cache et modes configurables | Volumes par UUID stable, quotas, exclusif/partagé, archive/purge et vidage | Reprises/marge physique encore ouvertes dans SLS-050 |
| SSO administrateur et rôles verified/admin | Code, sessions et vérification des rôles présents | Écran d'attente, azp d'ID token et rotation kid ont encore des travaux/preuves ; SLS-020 |
| Jetons CRUD scoped au service et éventuellement aux fonctions | Création, portée, expiration, révocation, renouvellement présents | Le droit Read invoque ; le contexte métier Authorization reste au handler |
| Variables et secrets au service, surcharges par fonction | Héritage et UI présents ; SLS-031 | Les réglages communs ne doivent pas être dupliqués silencieusement |
| Origine web et/ou IP autorisée par service | Politiques ET/OU, CORS et provenance proxy dans la passerelle | Une origine HTTP n'est pas une identité infalsifiable hors navigateur |
| Conserver handlers et réutiliser serverless.yml | Adaptateur et packaging présents | Compatibilité complète du projet de référence non démontrée ; runtime initial Node24 |
| URL calculées depuis les domaines du SPARK | API, UI et CLI présentes ; domaines et pagination réellement éprouvés | SLS-066 garde des fautes de source résiduelles |
| Manuel maintenu et affiché dans l'application | Source canonique docs/manual.md et compilation UI | Doit suivre les futures fonctions, pas annoncer les absentes comme disponibles |
| Recherche, filtres et catalogue | API et UI présents ; SLS-067 qualifiée à son checkpoint | La recherche n'inclut pas les valeurs secrètes |
| Versions par hash, doublon inchangé, retour arrière | Registre, déduplication, promotions et UI/CLI présents | Qualification complète008 et certains scénarios restent ouverts ; SLS-074 |
| Pilote par hash et cible stable sans tag | Upload sans promotion, invocation exacte du hash, promotion explicite | Les prochains crons doivent suivre la cible promue, pas tous les pilotes |
| Tous les comportements testés E2E sans mocks | Bancs réels et critères transversaux présents | La campagne complète de l'état008 n'est pas terminée ; ne pas déclarer toute la plateforme qualifiée |
| SPARK DEV, FORGE limitée, référence client en lecture seule | Contraintes dans CLAUDE_PROJECT et unités | Aucun lancement PREPROD/PROD autorisé |
| Noms significatifs et domaine/port choisis | Règle du contrat local, noms d'exploitation et routes | Les anciennes preuves gardent leurs noms historiques datés |
| Tout consigner dans le backlog | Table des demandes et unités SLS correspondantes | Leur statut doit rester visible sans lire tout l'historique des campagnes |
| Préparer le dépôt public sans dev-spark | Exclusion et réécriture réalisées ; SLS-077 | Les autres coordonnées DEV restent présentes conformément au périmètre demandé |

## Corrections de spécification issues de cette revue

PLATFORM annonçait encore le versionnement par hash à implémenter et une bascule
par redéploiement. Le contrat est corrigé : l'upload prépare, la promotion change
la cible sans tag, les appels admis gardent leur instantané et les appels par
hash restent épinglés. CONSOLE_USABILITY rangeait encore la recherche parmi les
travaux absents et annonçait une campagne de routes déjà exécutée ; ces synthèses
sont actualisées. La qualification globale reste ouverte.

## Priorité de reprise

Le parcours encore manquant éditer→publier→tester→diagnostiquer doit redevenir
visible dans l'avancement : SLS-070, SLS-071 et SLS-072. Favoris, opérations en
masse, monitoring et crons restent obligatoires dans SLS-068/069/073/050.
La compatibilité du manifeste de référence, les écarts SSO et la campagne E2E
complète demeurent des critères de clôture, pas des demandes optionnelles.
Les vérifications accompagnent ces livraisons et restent liées aux sources et
images effectivement testées.
