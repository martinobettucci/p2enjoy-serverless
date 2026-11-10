# Demandes confirmées et état réel de livraison

Revue du10 novembre2026, après signalement du responsable sur les demandes
manquantes. Périmètre : conversation, spécifications, backlog et sources du
dépôt courant. Les constats initiaux viennent de la revue statique ; les livraisons suivantes
sont actualisées ci-dessous avec leurs preuves DEV propres.

## Ce qui manque dans le produit

Onze demandes explicites restent à implémenter ou à démontrer, même si leurs
contrats existent :

| Demande | État constaté | Suivi |
| --- | --- | --- |
| Favoris personnels persistants | Aucune route, persistance ou interface de favoris | SLS-068 |
| Renommage et suppression en masse | Actions individuelles seulement ; sélection, aperçu et traitement de lot absents | SLS-069 |
| Éditer le code et le handler sur place | Upload ZIP et champ handler présents ; arborescence, éditeur, brouillons et diff absents | SLS-070 |
| Client HTTP intégré par fonction, type Postman | Catalogue d'URL/copie présent ; facette de test, requête et réponse interactives absentes | SLS-071 |
| Logging d'exploitation | Logs par invocation présents ; recherche, période, suivi, export et vue de service absents | SLS-072 |
| Monitoring | Relevés Docker ponctuels présents ; séries historiques, tableaux de bord et alertes absents | SLS-073 |
| Planifications (crons) du manifeste | Moteur et facette déployés ; [checkpoint réel](evidence/schedules-checkpoint-dev-2026-11-10.json), [cycle des versions](evidence/schedule-versions-dev-2026-11-10.json) [grammaire numérique](evidence/schedule-calendar-dev-2026-11-10.json) et [coupures/reprises](evidence/schedule-recovery-dev-2026-11-10.json), puis [admission CPU/exclusif/recouvrement](evidence/schedule-admission-dev-2026-11-10.json), [RAM/version en file](evidence/schedule-memory-version-dev-2026-11-10.json), [files pleines16/128](evidence/schedule-queues-dev-2026-11-10.json) et [commande de cache en cours](evidence/schedule-unavailable-dev-2026-11-10.json) qualifiés séparément ; plafond global d’instances, refus résiduels, rétention, états UI et qualification complète ouverts | SLS-078 |
| Jobs serverless : payload fixe, gabarits composés dans l'UI, crontab par fenêtres de 5 minutes | Absents | SLS-081 |
| Parité avec toutes les fonctionnalités de Scaleway Serverless | Matrice sourcée établie ; limites, en-têtes, runtimes, déclencheurs de messages et autres écarts ouverts | SLS-082 à SLS-088 |
| Compatibilité démontrée du projet de référence | Audit et matrice faits ; fixtures et preuves absentes ; capacité CPU à adapter | SLS-080 |
| Exploitation complète et reproductible | Informations dispersées dans des comptes rendus de campagne ; guide rejoué absent | SLS-079 |

Ces travaux appartiennent au périmètre confirmé. Ils n'attendent pas une nouvelle
demande du responsable. Une unité inscrite dans le backlog n'est pas une unité
livrée, et un nombre de groupes de tests ne mesure pas la couverture du produit.

## Méthode importée

`docs/.routine` et le rôle `factory_verifier` avaient été remplacés par des
versions affaiblies sans que le responsable l'ait demandé. Ils sont restaurés à
l'identique de l'original le 10 novembre 2026 ; voir
[SLS-000](BACKLOG.md#sls-000) et [METHODE](METHODE.md).

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
| Pilote par hash et cible stable sans tag | Upload sans promotion, invocation exacte du hash, promotion explicite | Les crons suivent la cible promue ; pilote, promotion et retour de hash éprouvés dans SLS-078.3 |
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

## Ordre de reprise

Le [registre des unités ouvertes](BACKLOG.md#registre-des-unités-ouvertes) du
backlog porte l'ordre, la nature, les dépendances et les critères de chaque
unité ; ce document ne porte ni ordre ni statut. Les demandes ci-dessus y sont
des unités, comme les écarts SSO ([SLS-089](BACKLOG.md#sls-089)), les restes de
qualification ([SLS-090 à 094](BACKLOG.md#sls-090)), le manuel déployé
([SLS-096](BACKLOG.md#sls-096)), l'API documentée ([SLS-097](BACKLOG.md#sls-097)) et
la campagne complète de clôture ([SLS-095](BACKLOG.md#sls-095)). La compatibilité
du manifeste de référence, les écarts SSO et la campagne E2E complète demeurent
des critères de clôture, pas des demandes optionnelles.
