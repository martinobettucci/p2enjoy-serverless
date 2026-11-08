# Backlog

## Suivi des demandes du responsable

Toute demande produit, correction ou contrainte reçue est inscrite ici dès sa
réception, dans l’unité existante correspondante ou dans une nouvelle unité
identifiée. Chaque unité précise le résultat attendu, ses critères et les
preuves requises. Les corrections complètent le contrat existant ; elles ne
disparaissent pas derrière une nouvelle reformulation. Les statuts restent
`[ ]` non commencé, `[~]` en cours ou insuffisamment vérifié, `[x]` terminé et
vérifié. Les valeurs de secrets ne sont jamais consignées dans le backlog.

Les demandes confirmées sont rattachées aux unités suivantes. Leur état et
leurs preuves font autorité dans le détail de chaque unité.

| Demande confirmée | Unités et contrats concernés |
| --- | --- |
| Méthode Software Factory importée dans le dépôt, hors module de séminaire | [SLS-000](#sls-000), [METHODE](METHODE.md) |
| Plateforme Docker compatible avec l’exploitation des projets existants, handlers conservés et adaptateur `serverless.yml` | [SLS-001](#sls-001), [SLS-030](#sls-030), [DEPLOYMENT](DEPLOYMENT.md) |
| Application de qualification et sources présentes dans ce dépôt | [QLF-001](#qlf-001) |
| Toutes les fonctionnalités livrées testées E2E sur les vrais composants, sans mock ni skip | [QLF-001](#qlf-001), [SLS-001](#sls-001), critères E2E de chaque unité |
| SPARK DEV autorisé, FORGE limitée au rebond, référence client en lecture seule, aucun lancement PREPROD/PROD | [Contrat local](../CLAUDE_PROJECT.md), [QUALIFICATION_DEV](QUALIFICATION_DEV.md) ; contraintes de toutes les unités |
| Noms significatifs par fonction et usage, domaine `serverless.lelabs.tech`, route sur 18090 | [SLS-011](#sls-011), [DEPLOYMENT_NAMES](DEPLOYMENT_NAMES.md), règle de nommage du contrat local |
| SSO réel, rôles verified/admin, namespaces, services, fonctions et gestion des jetons CRUD de service | [SLS-020](#sls-020), [SLS-060](#sls-060), [CONTROL](CONTROL.md) |
| Jeton Read pour invoquer, droits Create/Update/Delete, authentification métier indépendante | [SLS-020](#sls-020), [SLS-030](#sls-030), [SLS-040](#sls-040), [PLATFORM](PLATFORM.md) |
| Jetons, variables et secrets au niveau service, avec surcharges par fonction | [SLS-020](#sls-020), [SLS-031](#sls-031), [configuration commune](SERVICE_CONFIGURATION_URLS.md) |
| Restrictions par origine web et/ou IP, configurables au niveau service | [SLS-040](#sls-040), [PLATFORM](PLATFORM.md) |
| CPU, mémoire, concurrence, durée maximale d’exécution et délai d’arrêt après inactivité | [SLS-040](#sls-040), [SLS-060](#sls-060), [EXECUTION](EXECUTION.md) |
| Disque par identifiant stable, données permanentes et cache configurables, quotas, archive et purge | [SLS-010](#sls-010), [SLS-050](#sls-050), [SLS-064](#sls-064), [SLS-065](#sls-065) |
| Manuel d’usage maintenu et consultable dans l’application | [SLS-062](#sls-062), [CONSOLE_MANUAL](CONSOLE_MANUAL.md) ; mise à jour avec chaque livraison |
| Chemins d’appel calculés depuis les domaines réellement affectés au SPARK | [SLS-066](#sls-066) |
| Recherche, filtres et catalogue opérationnel | [SLS-067](#sls-067) |
| Favoris personnels | [SLS-068](#sls-068) |
| Suppression et renommage en masse | [SLS-069](#sls-069) |
| Édition du code et du handler sur place | [SLS-070](#sls-070) |
| Client HTTP intégré par fonction, avec réponse et diagnostic d’appel | [SLS-071](#sls-071) |
| Logging, recherche et corrélation des journaux | [SLS-072](#sls-072) |
| Monitoring historique et alertes | [SLS-073](#sls-073) |
| Version par hash du code changé, upload identique dédupliqué, invocation épinglée, rollback et pilote stable | [SLS-074](#sls-074), [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md) |

## SLS-000

Statut : [x] — socle importé, hooks standard activés, 45 contrôles Git réels
réussis. Provenance : [factory-import.json](evidence/factory-import.json).

Importer le socle opérationnel de `P2Enjoy/software-factory-base` au commit
`886ba5a28a834a5f08fd1a01ec8dd78787317559`, sans formation, publication de
formation ni design system pédagogique. Conserver les contrats globaux et
documenter les contraintes locales prioritaires. Inclure hooks exécutables,
scripts, rôles des agents et preuve réelle de leur fonctionnement avec Git.
Conserver une provenance par fichier. Spécification : [Méthode](METHODE.md).

La qualification complète QLF-001 exige zéro test ignoré et la couverture des
comportements livrés : erreurs, limites, saturation, configuration, stockage
et cycle de vie. Une dépendance absente fait échouer la campagne ; elle ne
la transforme pas en succès partiel.

## QLF-001

Statut : [x] — 38 tests HTTP E2E et 28 contrôles Docker/pannes réussis,
zéro échec et zéro test ignoré. Smoke et recréation avec reprise complète du
worker réussis. Les secrets réels sont configurés. Sources locales et déployées
identiques. [Preuve complète](evidence/qualification-dev-2026-11-05-complete.json).
Les résultats 17/19 restent historiques.

Créer un service synthétique dans `qualification/`, sans dépendance au client,
avec manifeste `serverless.yml`, handlers CommonJS et exécuteur de référence
DEV. Spécification : [DAT — Qualification](DAT.md#qualification).

Critères d'acceptation :

- contrats HTTP, événement/contexte/réponse, callback et authentification métier ;
- données persistantes par identifiant stable et cache invalidable séparément ;
- worker coopératif, interruption extérieure d'une invocation non coopérative,
  erreurs maîtrisées et invocation saine après un échec ;
- scénario synthétique d'appel entre fonctions, sans accès externe ;
- parcours E2E HTTP automatisés sur la pile réelle, sans mocks, exécutés
  séquentiellement ; aucun test ignoré, tous les prérequis exigés ;
- build et exécution Docker dans le seul SPARK DEV autorisé, puis preuve de
  conservation des données après recréation du conteneur ;
- documentation d'exploitation et trois propositions de notes dans la cellule ;
- aucune modification de FORGE et aucune utilisation du client comme fixture.

Le banc n'implémente ni SSO, ni jetons CRUD de plateforme, ni ordonnanceur cron,
ni autoscaling, ni isolation Docker par fonction. Ces exigences demeurent dans
le cadrage et feront l'objet d'unités propres à la plateforme.

Les preuves initiales sont conservées comme historique. La campagne complète
suit [la matrice](TEST_MATRIX.md) et doit vérifier chaque contrat présent avec
le code réel. Le banc ne vaut pas preuve des fonctionnalités de plateforme
non encore implémentées.


## SLS-001

Statut : [~] — objectif autonome actif ; réalisation détaillée ci-dessous.

Spécifier puis livrer par unités cohérentes les fonctions confirmées du produit :
SSO admin, namespaces/services/functions, jetons CRUD et invocations avec jeton,
règles origine/IP, gestion du code/configuration/secrets, adaptateur
serverless.yml, allocation Docker, mémoire, disques durables/cache par ID,
deadline d'invocation et extinction des instances. Chaque comportement livré
exige sa preuve E2E réelle, notamment les refus et cycles de vie.
Le périmètre inclut le manuel intégré, le calcul des URL du SPARK et les
demandes d’ergonomie et d’observabilité détaillées dans SLS-062 et SLS-066 à SLS-073,
ainsi que versions par hash, invocation épinglée et pilote dans SLS-074.
Le banc QLF-001 constitue l'application indépendante pour cette qualification.
Aucun de ses résultats ne clôture ces fonctionnalités de plateforme absentes.

Spécification commune : [Contrat de plateforme](PLATFORM.md).

## SLS-010

Statut : [x] — composant de quota qualifié par 31 contrôles réels,
zéro échec/skip ; client SSO créé, authentification du client vérifiée,
variables/secret de cellule appliqués, DNS et TLS DEV opérationnels.
Preuve : [stockage DEV](evidence/storage-dev-2026-11-05.json).

Qualifier le quota dur par fonction, le montage dans Docker rootless et sa
persistance. Préparer l'intégration SSO réelle, le domaine DEV et les variables
de cellule. Preuves : écriture jusqu'au plafond, isolation entre deux volumes,
remontage, nettoyage des seules ressources de l'expérience. Un accès SSO
manquant est nommé ; aucun fournisseur d'identité de remplacement.

## SLS-011

Statut : [x] — noms et domaine appliqués, persistance et connexion SSO réelle
sur la nouvelle adresse vérifiées.

Rendre les noms Docker explicites par rôle et adopter `serverless.lelabs.tech`
dans le SPARK de développement. Contrat : [noms d’exploitation](DEPLOYMENT_NAMES.md).
Conserver les données et les identifiants Compose, qualifier la recréation
réelle, la route TLS 18090, la configuration officielle et le parcours SSO.
Le nouveau callback est accepté par le vrai fournisseur le 6 novembre ; la
route a été corrigée vers 18090 par le responsable. Les deux conteneurs sont
healthy sous leurs nouveaux noms, avec les mêmes images, volumes, objets et
identité de base. Compteur, cache et checkpoint sont retrouvés par HTTP ; le
calcul reprend jusqu’au résultat complet. 38 tests HTTP, neuf contrôles
navigateur, huit groupes publics, quatre chemins réseau et quatorze contrôles
CLI passent. La connexion personnelle sur le nouveau domaine produit une
session authentifiée et l’API administrateur des namespaces répond 200.
[Preuve de migration](evidence/deployment-names-dev-2026-11-06.json).

## SLS-020

Statut : [~] — contrôle et console initiale déployés ; qualification en cours.

API Python/SQLite avec migrations, SSO admin réel, sessions/CSRF, CRUD des
namespaces/services/fonctions et tokens. E2E : persistance après redémarrage,
matrice de permissions, restriction interservice/fonction, expiration,
révocation, renouvellement et refus SSO. Références : PLATFORM organisation
et identité ; [schéma](SCHEMA.md) et [API du contrôle](CONTROL.md).
La tranche de console associée expose ces objets et le parcours SSO dès cette
unité ; SLS-060 complète ses facettes d'exécution et la campagne transversale.
Les parcours publics, l'accueil navigateur, la provenance réseau et les
limites de connexion sont éprouvés. La [preuve de gestion authentifiée](evidence/control-management-dev-2026-11-06.json)
recoupe 19 groupes API, 11 parcours UI et huit groupes publics sur l'image
déployée. Nettoyages confirmés, sept captures relues. Le nom maximal du fil
d’Ariane mobile revient à la ligne et les trois gestes de fermeture du menu
rendent le focus au bon contrôle, y compris après passage au desktop.
Le [checkpoint du 6 novembre](evidence/control-dev-checkpoint-2026-11-06.json)
regroupe six groupes HTTP, neuf contrôles navigateur, quatre chemins réseau,
six scénarios de limite par client, deux de capacité globale et dix-sept
de panne/reprise. Deux contrôles supplémentaires éprouvent l'interruption
du pilote de preuve. Les dépendances verrouillées sont auditées.

La revue du contrat OIDC du client créé précise les travaux SLS-020 restants :
état d'attente distinct d'une erreur technique pour verified/admin manquant,
contrôle de l'azp de l'ID token en complément de son audience, et réponse
temporaire préservant la session lorsqu'un nouveau kid arrive dans la fenêtre
anti-refresh JWKS de deux secondes. Les comptes réels et une rotation réelle
maîtrisée sont nécessaires aux preuves correspondantes ; aucune n'est déclarée
réussie. La durée de 300 secondes se mesure sur le jeton réellement émis.

## SLS-030

Statut : [~] — publication API/CLI, plafonds de candidats/révisions et deux reprises après SIGKILL qualifiés ; autres limites ouvertes ; interface livrée par SLS-063.

Packaging YAML, héritage, upload immuable, secrets chiffrés, validation du
handler, CJS/ESM et dépendances réelles. E2E : déployer le service témoin par
l'adaptateur, rejeter archives invalides, mettre à jour/rollback en préservant
l'identifiant. Référence : PLATFORM adaptateur et [DEPLOYMENT](DEPLOYMENT.md).
La compatibilité du projet de référence reste à établir explicitement : audit
en lecture seule du manifeste, des contrats de handlers, dépendances, événements,
variables et secrets ; matrice des comportements pris en charge, adaptations
nécessaires et écarts bloquants. Reproduire ces contrats avec des fixtures
originales du dépôt et les déployer/invoquer réellement sur la plateforme.
La preuve identifie les adaptations nécessaires au client, dont le jeton
d’invocation ; les résultats du banc seuls ne valent pas compatibilité complète.
La déduplication des uploads, le hash public, la publication sans activation
et les résultats de version relèvent de l’extension SLS-074.
La session SSO réelle est disponible pour les preuves d'upload et de publication.
Le [checkpoint CLI](evidence/adapter-package-dev-2026-11-06.json) comporte
24 scénarios réels réussis dans Docker sur le SPARK, avec source et images
identifiées. Le [checkpoint du chargeur](evidence/runtime-validation-dev-2026-11-06.json)
ajoute 36 scénarios réels : formats CJS/ESM, dépendances, confinement, logs,
échéance extérieure, protocole Unix et destruction des descendants.
Le [checkpoint d'extraction](evidence/artifacts-dev-2026-11-06.json) ajoute
112 contrôles réels : formats et refus, limites exactes, disque saturé,
courses sur les chemins et la source, puis packaging/extraction/chargement
Node des douze fonctions. Le [checkpoint du contrôle de publication](evidence/deployment-control-dev-2026-11-06.json)
intègre les routes de préparation, upload, historique, rollback et suppression,
la migration 003, le budget et la reprise. Huit groupes publics et trente
contrôles réels de configuration/démarrage/panne passent sur l'image déployée.
La [preuve authentifiée](evidence/deployment-authenticated-dev-2026-11-06.json)
recoupe onze groupes API et sept groupes CLI : droits, refus, import et logs
expurgés, révocation/conflits pendant validation, admission unique, rollback,
suppression de révisions inactives et huit candidats par fonction. Les 35
archives conservées des campagnes sont vérifiées sur disque ; aucun objet
actif, candidat non terminal, réservation, canal ou conteneur de validation
ne subsiste à ce checkpoint. La [preuve de reprise](evidence/publication-recovery-dev-2026-11-06.json)
ajoute quatre groupes : 64 candidats globaux, vingt révisions, SIGKILL pendant
réception partielle puis pendant validation Docker vivante. Les candidats
interrompus échouent sans publication, les configurations et archives
précédentes sont intactes, les ressources sont libérées et de nouveaux uploads
réussissent. Les 53 archives antérieures et vingt nouvelles archives conservées
sont recoupées. Expiration, budget/marge disque, déconnexion concurrente et
arrêt pendant nettoyage restent à qualifier.
La commande deploy est désormais implémentée : sa [preuve ciblée](evidence/adapter-deploy-dev-2026-11-06.json)
conserve 14 contrôles de prérequis et de refus HTTPS réel, plus les 24 scénarios
plan/package rejoués. Les sept groupes CLI authentifiés réussissent onze
premières publications, la pagination, les mises à jour à UUID conservé,
les refus de droits, le résultat partiel et la reprise du même brouillon.
Rupture après envoi, modification locale concurrente, réponse trop grande et
redirection restent à éprouver. Les vues de révisions sont livrées et vérifiées par SLS-063. Le moteur est déployé ; son exécution après rollback est vérifiée dans
la [campagne publique](evidence/execution-dev-2026-11-06.json).

## SLS-040

Statut : [~] — admissions publiques et reprises éprouvées ; preuves résiduelles ouvertes ; vues de consultation livrées par SLS-061.

Invocation authentifiée, limites réelles, admission atomique, min/max/idle,
deadline, descendants, drainage et réconciliation. CORS/IP ET/OU côté backend.
E2E : succès/refus, saturation, mémoire/CPU/PIDs, délais, extinction/reprise,
authentification métier, chaînes proxy, crash du contrôle et absence de rejeu.
Références : PLATFORM origines et exécution, [EXECUTION](EXECUTION.md).
L’invocation d’une version par hash, ses admissions, pools et budgets partagés
avec la cible courante sont détaillés dans SLS-074.
La tranche initiale fournit le superviseur chaud, son enfant neuf et le pilote
Docker réel. Les campagnes d’invocation et de courses de cycle sont présentes,
avec régression du chargeur partagé : 31 + 11 + 36 contrôles réels réussis,
zéro échec et zéro test ignoré. La [preuve](evidence/instances-dev-2026-11-06.json)
est conservée séparément des parcours API. Le pilote est maintenant raccordé
aux baux de l’agent FUSE, avec quatorze groupes réels. Les admissions, min/max/idle, générations et invocations authentifiées sont
intégrées et déployées sur DEV. La [preuve du moteur](evidence/execution-dev-2026-11-06.json)
recoupe 31 groupes HTTPS et 221 groupes de régression, avec zéro échec/skip
dans la suite finale : budgets CPU/RAM/instances, 128 réceptions, générations,
déconnexions, contention SQLite, SIGKILL et arrêt gracieux sans rejeu.
Les scénarios échoués pendant le développement restent conservés séparément.
La rétention à sept jours/10 000 observations et les chemins résiduels de
nettoyage/reprise doivent encore recevoir leurs preuves ciblées. Les vues
d’exécution sont livrées et vérifiées par SLS-061.

## SLS-050

Statut : [~] — agent local installé en DEV ; raccordements et preuves de reprise à poursuivre.

Volumes par ID, quotas et modes, archive/purge, crons UTC, logs bornés et
métriques. E2E : concurrence, saturation disque, cache, déploiement/rollback,
redémarrage, cron réellement déclenché et diagnostic autorisé/refusé.
Références : PLATFORM stockage et exploitation, [STORAGE_AGENT](STORAGE_AGENT.md).
Les futurs crons suivent uniquement la cible courante de SLS-074 ; publier
une version pilote sans l’activer ne double pas les déclenchements.
Le registre durable, les baux et la supervision FUSE sont implémentés. Quinze
groupes de cycle, huit de limites et les 31 contrôles du proxy passent, avec
nettoyage confirmé, zéro échec et zéro skip. La [preuve recoupée](evidence/storage-agent-dev-2026-11-06.json)
est complétée par quatorze groupes de raccordement au pilote d’instances :
[preuve](evidence/managed-storage-dev-2026-11-06.json). Les créations, modifications
de quotas, suppressions et publications sont raccordées à une décision SQL durable
(migration 004). Treize groupes HTTPS et une preuve ciblée du pilote couvrent les reprises avant/après commit,
la révocation, les fichiers réels, la publication et le rollback. Le protocole
de l’agent compte douze groupes avec la neutralisation d’un prepare retardé.
La [preuve du raccordement](evidence/function-storage-dev-2026-11-06.json)
recoupe aussi les régressions et la console. Les admissions et observations API sont éprouvées par les 31 groupes publics
de la [preuve du moteur](evidence/execution-dev-2026-11-06.json). Les
commandes publiques de purge/cache et leurs vues de console sont déployées
et qualifiées dans SLS-065. Les crons restent
à réaliser.
Les quotas préparés et leurs reçus sont
implémentés ; la preuve initiale de dix groupes vérifie décisions, réservations, SIGKILL pendant
préparation et reprise d'abandon partiel avec conservation des données.
La [preuve recoupée](evidence/storage-preparations-dev-2026-11-06.json) ajoute
37 groupes de régression, avec nettoyages confirmés, zéro échec et zéro skip.
L'acquisition partielle après interruption, la marge physique et les pannes de registre
restent à qualifier ; aucune clôture de SLS-050 ne repose sur ces seuls composants.

## SLS-060

Statut : [~] — gestion, exécutions, manuel et publication livrés ; qualifications de purge/cache, crons, ergonomie avancée et campagne transversale ouverts.

Parcours d'administration sur les API réelles : connexion, objets, jetons,
code, variables/secrets, limites, état, stockage, historique et journaux.
Lire et appliquer les deux design systems avant implémentation. Tester depuis
l'accueil, clavier/souris, états vides/erreurs/données longues et mobile ;
inspecter les captures. Exécuter la campagne complète, mettre à jour manuel,
notes SPARK, installation/reprise, preuves et backlog. Zéro échec et zéro skip.
Les demandes de recherche, favoris, actions en masse, édition du code, client
HTTP et observabilité sont spécifiées dans [CONSOLE_USABILITY](CONSOLE_USABILITY.md)
et découpées dans SLS-067 à SLS-073.
Le versionnement par hash, les appels épinglés et le pilote de versions sont
définis dans SLS-074 ; ils complètent les révisions et le rollback déjà livrés.

## SLS-061

Statut : [x] — facettes déployées ; 40 groupes réels réussis, zéro échec/skip,
25 captures relues, sources et image recoupées, nettoyages confirmés.
[Preuve](evidence/console-execution-dev-2026-11-07.json).

Tranche bornée de SLS-060 : [contrat de consultation](CONSOLE_EXECUTION.md).
Facettes de la fonction, mesures distinctes des allocations, pagination réelle,
états et journaux expurgés, focus, mobile, erreur/reprise et preuves de console.
La publication depuis l’UI, purge/cache et crons appartiennent aux autres tranches.

## SLS-062

Statut : [x] — manuel intégré et maintenu depuis sa source unique ; 48 groupes
réels réussis, zéro échec/skip, 33 captures relues.
[Preuve](evidence/manual-console-dev-2026-11-07.json).

[Contrat du manuel intégré](CONSOLE_MANUAL.md). Source éditoriale unique,
construction automatique, entrée de navigation, sommaire et ancres accessibles,
guide autonome, rendu responsive et preuve E2E de concordance avec le document.

## SLS-063

Statut : [x] — publication depuis la console déployée et vérifiée : 18 campagnes,
312 groupes réels, zéro échec/skip, 54 captures inspectées, sources et image
recoupées, nettoyages confirmés et notes SPARK appliquées.
[Preuve](evidence/publication-console-dev-2026-11-07.json).

[Publication dans la console](CONSOLE_PUBLICATION.md). ZIP et handler avec
conservation serveur de la configuration, suivi corrélé et abandon des candidats
préparés, historique, activation et suppression des révisions. Parcours UI réels,
droits et conflits, invocation après activation, réponses perdues, reprises de
nettoyage physique et de confirmation du stockage, candidat étranger et longs
journaux. Les deux incohérences de lecture découvertes à la première revue sont
corrigées puis requalifiées ; le registre est résolu. Le manuel et les notes
SPARK décrivent les parcours livrés. Les preuves résiduelles des unités parentes
restent ouvertes.
L’identification publique par hash, la déduplication et le pilote sans activation
ne font pas partie de cette preuve historique ; ils sont suivis dans SLS-074.

## SLS-064

Statut : [x] — paquet installé et migration 004 vérifiée ; sept campagnes,
106 groupes réels, zéro échec/skip, reprises et nettoyage recoupés.
[Preuve](evidence/storage-discard-dev-2026-11-07.json).

[Effacement corrélé](STORAGE_DISCARD.md) : reçus de vidage/purge, versions et
propriétaire, réponse perdue, erreur physique et interruption ; suppression
hors verrou global. Migration 004 agent, installation DEV et preuves réelles.

## SLS-065

Statut : [x] — déployé et qualifié en DEV ; replay complet, complément API,
captures, nettoyages, trois notes proposées et revue finale recoupés.

Catalogue consultable après suppression des parents, purge administrateur
confirmée, vidage sous droit Update, drainage et relecture des droits/versions
avant décision durable. API, console et manuel sont déployés avec la migration
006 et le protocole agent 004. Contrat : [CONSOLE_STORAGE](CONSOLE_STORAGE.md).

La [preuve complète](evidence/storage-console-dev-2026-11-08.json) réunit
29 campagnes et 397 groupes réels en série, sans échec/skip, puis un complément
distinct de neuf groupes API. Celui-ci couvre quatorze corps invalides de purge,
une ancienne version positive réellement lue avec UUID neuf et nom exact, les
refus du helper de lecture et l’égalité des fichiers, configurations, versions,
commandes, gardes, reçus et audit de purge avant/après. Ses assertions ne sont
pas attribuées rétroactivement aux 397 groupes.

Les 24 fonctions de six namespaces du replay et les quatre de deux namespaces
du complément sont purgées et recoupées physiquement ; ressources et allocations
globales libérées. Les deux fenêtres historiques restaurent les tables, fichiers,
identités et services originaux. La purge contradictoire de leur installation
temporaire reste volontairement en attente : elle ne devient pas une purge
métier réussie par le retrait de cette installation.

La pagination crée onze brouillons depuis l’UI, les archive et recoupe dix UUID
propres sur deux pages après coupure réseau. Le runner prépare une paire SSO au
début puis une autre juste avant la décision, sans changer les durées SSO.
Quatre prérequis restent hors du compte des groupes. Les 173 sources sont liées
avant/après chaque phase, avec deux sources E2E renforcées pour le complément ;
les 25 fichiers du contrôle embarqué et la même image sont recoupés. Les deux
mises à jour documentaires finales de statut sont distinguées des sources testées.

Les 72 captures sont recoupées : 55 nouvelles images observées et 17 images
régénérées identiques à celles déjà inspectées. Le manuel correspond à ses
treize chapitres et 39 paragraphes. Les trois notes SPARK sont proposées et
recoupées ; leur adoption n’est pas annoncée.

Checkpoints conservés : [initial](evidence/storage-console-checkpoint-dev-2026-11-07.json),
[commandes sous panne](evidence/storage-command-recovery-dev-2026-11-07.json),
[validation vivante](evidence/storage-validation-recovery-dev-2026-11-07.json),
[décisions](evidence/storage-decision-recovery-dev-2026-11-07.json),
[correctif historique](evidence/storage-legacy-recovery-dev-2026-11-07.json),
[intégration ciblée](evidence/storage-console-focused-dev-2026-11-08.json) et
[premier replay arrêté sur prérequis SSO](evidence/storage-console-incomplete-dev-2026-11-08.json).
SLS-064 seul ne qualifie aucun parcours public d’effacement.


<a id="sls-031"></a>
## SLS-031 — Préserver la configuration commune du service au déploiement

Statut : [x] — déployé et qualifié, y compris l’issue inconnue sous vraie coupure.

L’adaptateur conserve les valeurs communes du provider dans le service et
uniquement les surcharges dans les fonctions. Le rapport distingue les deux
étapes. L’API remplace explicitement un jeu de secrets et contrôle les
configurations effectives avant mutation ; la CLI borne les fusions connues,
y compris leur représentation Unicode au runtime. Contrat :
[SERVICE_CONFIGURATION_URLS](SERVICE_CONFIGURATION_URLS.md).
La [preuve](evidence/service-configuration-dev-2026-11-08.json) recoupe treize
groupes ciblés : héritage, surcharges, rotation pendant appel admis, droits,
échec partiel, reprise d’un ancien déploiement aplati, limites et redémarrage.
Les régressions portent le total à 191 groupes sur douze campagnes en série ;
24 groupes plan/package et quatorze de refus public sont rejoués dans Docker.
Zéro échec/skip, 165 sources recoupées, 25 fichiers embarqués du contrôle et cinq
de la CLI conformes. Les deux fonctions ciblées et onze répertoires d’artefacts
sont purgés, sans réservation ou conteneur résiduel. Le manuel affiche ses
39 paragraphes ; les 21 captures de gestion et de lecture sont inspectées.
Le [complément de transport](evidence/service-configuration-transport-dev-2026-11-08.json)
ajoute cinq groupes natifs : garde indépendante, coupure avant traitement et après
commit, puis deux relances explicites avec publication et invocation Docker.
La vraie CLI rend `unknown` et ne tente que les trois connexions HTTPS attendues,
sans rejeu ni fonction/candidat créé. Les treize groupes de configuration sont
ensuite rejoués. Ces dix-huit groupes passent sans échec/skip sur la même image,
avec 167 sources identiques avant/après ; aucune source produit du checkpoint
de 191 groupes n’a changé. Le recoupement physique couvre les quatre fonctions,
treize artefacts absents et les réservations à zéro ; les trois gardes sont inactives.
Les deux preuves conservent leurs index historiques distincts. Le
[banc](SERVICE_CONFIGURATION_URLS.md#preuve-de-transport) ne couvre ni une panne
de la FORGE ni les autres scénarios résiduels de SLS-030.

<a id="sls-066"></a>
## SLS-066 — Afficher les URL d’appel issues des domaines du SPARK

Statut : [~] — catalogue, console et résultat CLI déployés en DEV ; régression
complète de 35 campagnes / 467 groupes réussie, qualification multi-domaines
et résiduelle ouverte.

Découvrir les routes effectivement affectées à la passerelle dans le SPARK,
calculer les adresses par fonction et événement HTTP, les afficher et les
rendre copiables dans la console ainsi que dans le résultat de déploiement.
Distinguer les domaines d’invocation du domaine SSO canonique. Contrat, limites
d’infrastructure et preuves E2E :
[SERVICE_CONFIGURATION_URLS](SERVICE_CONFIGURATION_URLS.md) et
[INVOCATION_URLS](INVOCATION_URLS.md). Le [checkpoint DEV](evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
réunit huit groupes API/CLI, six UI, 36 régressions et 38 groupes CLI Docker,
avec 31 captures recoupées.
Le manuel de ce checkpoint comporte 14 chapitres et 43 paragraphes ; le guide
courant qualifié par SLS-067 en comporte quinze et 46. Les preuves multi-domaines,
retrait et absence exigent les vraies routes et l’autorité bornée du SPARK ;
aucune substitution du registre n’est admise. Restent également les sources
perturbées. La consultation CLI refusée par révocation 401 est qualifiée
ci-dessous. Le manuel
est reconstruit et qualifié pour les parcours actuellement éprouvés.

L’autorisation bornée de gestion des routes du seul SPARK depuis sa console
normale est confirmée le 8 novembre 2026 : alias functions.lelabs.tech, deux
routes vers 18091 temporairement, garde et restauration à 18090. Le périmètre
est inscrit dans CLAUDE_PROJECT ; l’alias est appliqué, tandis que les preuves
de retrait et détours restent à exécuter après la campagne SLS-067.

SLS-067 est clôturée. La reprise commence par le DNS exact et la route TLS de
l’alias autorisé via la console normale, puis les huit groupes API/CLI et six UI
sur les deux domaines. Le [contrat opératoire](INVOCATION_URLS.md#console-normale-et-mise-en-service-de-lalias-autorisé)
sépare cette mise en service des perturbations et de leur garde à éprouver.
Le DNS exact et l’alias sont maintenant appliqués ; les deux HTTPS et la
projection lisible depuis le contrôle sont vérifiés. Les huit groupes API/CLI
et six UI passent, avec quatre fonctions purgées dans deux namespaces.
La [preuve à deux domaines](evidence/invocation-domains-dev-2026-11-08.json)
conserve ses arrêts initiaux et la reprise sans mutation ; elle ne clôture
pas les critères résiduels de SLS-066.
La prochaine étape suit le [contrat de garde et cycles](INVOCATION_URLS.md#garde-de-restauration-et-cycles-autorisés) :
garde sans perturbation, mort du pilote après détour d’alias confirmé,
retrait/rétablissement puis deux ports détournés et catalogue vide local réel.
Le vide UI public exige ensuite sa propre pause/libération native, distincte
du pilote historique de destruction ; aucune de ces preuves n’est acquise.

La garde est implémentée en qualification. Deux scénarios sans perturbation
passent : restauration explicite et SIGKILL réel du pilote avec restauration
indépendante, deux HTTPS et fin confirmée. Le scénario d’échéance déclenche
effectivement sa restauration mais échoue à son dernier contrôle HTTPS de
l’alias (URLError) ; il n’est pas compté réussi. Le diagnostic ultérieur trouve
un cache DNS natif négatif ancien, alors que les deux autoritaires rendent le
bon A. Les ports restent tous deux 18090 ; aucun détour/retrait n’a commencé.
Le [checkpoint de garde](evidence/invocation-route-guard-checkpoint-dev-2026-11-08.json)
conserve les deux réussites, l’arrêt et le diagnostic séparément. Rejouer
l’échéance sur résolution native rétablie avant toute perturbation.
Pendant cette attente, préparer les [preuves de pause/libération natives](INVOCATION_URLS.md#barrière-native-de-pause-et-libération)
sur la requête canonique, sans changer de route : module NativeObserver commun,
replay de ses neuf groupes historiques, pause/libération puis SIGKILL du traceur
et reprise indépendante de la vraie requête. Ces nouveaux parcours restent
à implémenter et qualifier.

La [suite `invocation-urls`](evidence/invocation-urls-regressions-dev-2026-11-08.json)
passe 35 campagnes / 467 groupes, zéro échec/skip, avec six prérequis non comptés,
186 sources et les images contrôle/CLI recoupées avant/après chaque phase.
Les 32 fonctions suivies sont purgées dans dix namespaces ; les deux restaurations
historiques sont distinctes. Les 79 captures fraîches sont recoupées : 61
observations et 18 identités SHA avec une référence inspectée. Le premier replay
des pannes est arrêté après 51 groupes à cause d’un client suivant la redirection
canonique ; sa correction et la preuve native du Host sont définies dans
INVOCATION_URLS. Le client de panne corrigé passe 55 groupes ; les huit groupes API
passent avec le vrai Host en boucle locale, puis dans la suite complète.
Les preuves de routes publiques restent ouvertes, ainsi que la branche
d’expiration/perte SSH du build borné, dont seul le parcours nominal est qualifié.

Le [complément de transport](evidence/invocation-url-transport-dev-2026-11-08.json)
passe trois groupes de transport du catalogue, avec perte
de l’observateur, coupure du GET après réception puis avant émission, publication
durable conservée, six connexions CLI sans rejeu et invocation Docker après
reprise. Contrat : [perte native](INVOCATION_URLS.md#perte-native-du-catalogue-après-publication-cli).
Les cinq groupes de transport historique et huit API/CLI repassent ensuite :
16 groupes au total, 187 sources et images liées avant/après chaque phase,
huit fonctions purgées dans trois namespaces, six gardes terminées et 26 fichiers
embarqués recoupés. Les vrais 502 ne changent pas le succès de publication.
Le refus reste distinct de ces coupures ; le vrai 401 est qualifié ci-dessous.
Les branches
d’expiration/sortie excessive/lancement et nettoyage après réponses perdues
du nouveau client ne sont pas déclarées acquises.

Le [complément de révocation](evidence/invocation-url-refusal-dev-2026-11-08.json)
ajoute le quatrième groupe de transport :
CLI retenue nativement avant sa sixième connexion, publication durable vérifiée,
révocation API du jeton puis vrai GET 401 sans requalification ni rejeu.
Contrat : [révocation avant GET](INVOCATION_URLS.md#révocation-avant-le-get-facultatif).
Le replay passe 4 + 5 + 8 = 17 groupes, sans échec/skip, avec 188 sources/images
stables et neuf fonctions purgées dans trois namespaces ; six gardes et 26
fichiers embarqués recoupés. Le premier essai incomplet reste séparé, cause
de barrière inconnue, deux fonctions et deux gardes nettoyées. Le refus 403
et les pannes propres du pilote/diagnostic ne sont pas revendiqués.

<a id="sls-067"></a>
## SLS-067 — Catalogue de fonctions et recherche globale

Statut : [x] — API/console déployées et qualifiées ; 37 campagnes uniques /
489 groupes réussis en deux époques contrôlées, recoupements physiques,
documentation et revue finale terminés.

Catalogue global, recherche serveur, filtres namespace/service/état, tri,
pagination et contexte conservé dans l’URL. Le [contrat](FUNCTION_CATALOGUE.md)
et la [preuve](evidence/function-catalogue-dev-2026-11-08.json) couvrent les
API administrateur, le nouvel accueil et les retours depuis les six facettes.
Recherche globale, Unicode/UUID/handler, filtres combinés, homonymes et tris
stables, refus, vraie latence réseau, erreurs de saisie corrigées, historique,
rechargement, suppressions et recalage, clavier/mobile sont éprouvés.

La qualification retient 30 campagnes aux clients inchangés (447 groupes) et
sept réexécutées (42), soit 37 uniques / 489 groupes, sans échec/skip dans cet
ensemble. Six prérequis sont distincts. Les époques 196/197 et mêmes images
produit/CLI sont recoupées ; les deux arrêts précédents et l’ancien résultat
positif remplacé restent séparés, sans succès rétroactif. Le
[correctif du client privé](evidence/private-channel-lifecycle-dev-2026-11-08.json)
garde sa propre preuve de onze groupes.

Les 98 captures sont inspectées, dont les trois positions de table à 390 px et
le dialog plein viewport. Le guide compilé compte 15 chapitres et 46 paragraphes.
91 fonctions suivies purgées dans 23 namespaces, quinze jeux variables/secrets
de services vidés et restaurations historiques sont recoupés. Les 39 fonctions
des jeux écartés ont leur relevé séparé. Sources produit, référence et configuration
officielle inchangées ; 27 fichiers embarqués et quatre fichiers web HTTPS
correspondent à l’image. La remarque de titre d’archive après purge est suivie
dans SLS-075. SLS-066 conserve ses preuves indépendantes.

<a id="sls-068"></a>
## SLS-068 — Favoris personnels persistants

Statut : [ ] — contrat défini, implémentation à réaliser.

Épingler et ordonner namespaces/services/fonctions par identité SSO stable,
avec persistance entre appareils et traitement des objets devenus indisponibles.
Contrat : [favoris](CONSOLE_USABILITY.md#favoris-personnels).
E2E : deux sessions réelles du même compte, isolation entre comptes réels,
renommage/suppression/retrait d’accès, redémarrage et parcours clavier/mobile.

<a id="sls-069"></a>
## SLS-069 — Renommage et suppression en masse

Statut : [ ] — contrat défini, implémentation à réaliser.

Sélection explicite, aperçu, droits et versions, renommage atomique et suivi
durable de suppression par objet. Préserver UUID, révisions et volumes ; fournir
la correspondance de manifeste pour l’adaptateur après renommage. Contrat :
[opérations en masse](CONSOLE_USABILITY.md#opérations-en-masse).
E2E : sélection multi-pages, collisions/échanges de noms, version obsolète,
limite du lot, fonctions occupées, parents non vides, résultat partiel, reprise
après réponse perdue/SIGKILL, redéploiement exporté et état physique des données.

<a id="sls-070"></a>
## SLS-070 — Édition du code et du handler dans la console

Statut : [ ] — contrat défini, implémentation à réaliser.

Arborescence de fichiers, édition texte, handler, brouillon persistant, diff et
publication par le pipeline réel de révisions immuables. Contrat :
[éditeur](CONSOLE_USABILITY.md#éditeur-de-code-et-handler).
E2E : lecture autorisée/refusée, modification et export CJS/ESM, conflits,
contenus binaires/volumineux, chemins invalides, import réellement défaillant,
publication puis invocation Docker, rollback, rechargement et perte de réponse.

<a id="sls-071"></a>
## SLS-071 — Client HTTP intégré par fonction

Statut : [ ] — contrat défini, implémentation à réaliser.

Facette Tester avec méthode, URL calculée, paramètres, en-têtes, corps, réponse,
durée et lien vers l’appel et ses journaux. Contextes serveur et navigateur
explicites ; vrais jetons Read, politiques et authentification métier. Contrat :
[client HTTP](CONSOLE_USABILITY.md#client-http-par-fonction).
E2E : appels réels, corps texte/JSON/binaire, CORS/origine/IP, droits et expiration,
destinations interdites/redirections, erreur/timeout/annulation, corrélation,
expurgation des identifiants et rendu sur ordinateur/mobile.

<a id="sls-072"></a>
## SLS-072 — Journaux recherchables et corrélation d’exploitation

Statut : [ ] — extension des journaux d’invocation existants à réaliser.

Vues fonction/service, période, sévérité connue, recherche, suivi activable,
export et corrélation appel/révision/instance/publication. Collecte, taille et
rétention bornées. Contrat : [journaux](CONSOLE_USABILITY.md#journaux-et-corrélation).
E2E : vrais logs texte/JSON et erreurs Docker, droits, secrets expurgés,
troncature/rétention, pagination/recherche, suivi interrompu puis repris,
redémarrage, export et diagnostic depuis un appel déclenché dans la console.

<a id="sls-073"></a>
## SLS-073 — Monitoring historique et alertes dans la console

Statut : [ ] — extension des relevés Docker existants à réaliser.

Tableaux de bord plateforme/namespace/service/fonction, séries d’appels,
latences/erreurs/refus, CPU/mémoire/stockage, santé et alertes à seuils
configurables. Contrat : [monitoring](CONSOLE_USABILITY.md#monitoring-et-alertes).
E2E : charge réelle et pannes, valeurs agrégées recoupées aux appels et mesures,
échantillons insuffisants/collecte indisponible, rétention, seuils et retour à la
normale, droits, redémarrage, coût de collecte mesuré et inspection des graphes.

<a id="sls-074"></a>
## SLS-074 — Versions par hash, appels épinglés et pilote de code

Statut : [ ] — demande et contrat définis ; déduplication et invocation par tag absentes.

Contrat : [FUNCTION_VERSIONS](FUNCTION_VERSIONS.md). Une nouvelle version n’est
créée que si le paquet exécutable a changé ; son tag public est son hash SHA256
canonique, vérifié côté serveur. Un upload identique réutilise la version, sans
doublon durable ni activation inutile. Les métadonnées sans effet du ZIP sont
exclues ; fichiers, dépendances et descripteur d’exécution sont pris en compte.
Un renommage conserve le hash ; un doublon reste admis au plafond de versions.

Sans tag, appeler la dernière version promue, mise à jour uniquement par
promotion/rollback explicite. L’upload prépare une version sans déplacer cette
cible, y compris au premier upload. Avec un hash, appeler exactement cette version
disponible, sans aucun repli si elle est archivée ou supprimée. Conserver les
droits Read, politiques origine/IP et authentification métier. Les URL
versionnées sont calculées avec SLS-066 et proposées dans SLS-071.
Create couvre la première publication et sa première promotion ; Update les suivantes et le cycle des
versions, y compris leur suppression individuelle. Delete reste la suppression
de la fonction. Le handler/runtime/image/événements viennent du hash sélectionné,
les ressources et configurations applicatives restent courantes.

Séparer publication et promotion pour un pilote, puis promouvoir ou revenir
à un ancien hash depuis la fiche de fonction. La CLI propose le même parcours
de code seul, sans mutation implicite des variables/secrets communs. Les clients
épinglés au hash stable continuent à l’appeler pendant le pilote. Configurations
et volumes restent attachés à la fonction ; le rollback concerne son code.

Prévoir archivage/restauration/suppression par version, protection de la cible
courante, consommateurs vivants et rétention explicite. Compter les ressources
et limites de toutes les versions ensemble ; isoler leurs pools d’exécution et
corréler le hash réellement exécuté dans logs et monitoring. Migrer les révisions
actuelles sans perte de pointeur, références ou données.

E2E : upload identique et ZIP différent de même contenu, modifications réelles,
renommage sans nouveau hash, doublon au plafond, handlers A/B distincts,
concurrence et déduplication, stable/pilote simultanés, appel sans tag, activation,
rollback sous appel vivant, droits/refus et aucune substitution de version,
archive/restauration/suppression, saturation entre versions, migration, réponse
perdue/SIGKILL et nettoyage physique. Parcours UI complets, captures et manuel
compilé requis. Dépendances : SLS-030/040/063 ; raccordements SLS-066/070 à SLS-073.

<a id="sls-075"></a>
## SLS-075 — Nommer la fiche d’archive sans ambiguïté après purge

Statut : [ ] — correction mineure issue de la revue SLS-067, à réaliser avec
une prochaine livraison UI et sa nouvelle qualification.

Le titre actuel « Archives conservées » apparaît aussi au-dessus de l’état
Purgée, de zéro révision et zéro Mio. Le badge et le reçu sont corrects ; aucune
défaillance de purge n’est constatée. Source : `web/src/storage.jsx:96` ;
capture contrôlée `storage-ui-purged-mobile.jpg`, empreinte
`ae744c550e6e636e91163047b3768840f310d943d728a621102bee6121fa2285`.

Employer un titre neutre décrivant la fiche, par exemple « Archive de la
fonction », et conserver les états Conservée/Purge en cours/Purgée dans le
badge. Ne changer ni rétention, ni commandes, ni allocation pour ce libellé.
La correction concerne un composant antérieur au catalogue ; elle requiert une
nouvelle image de console, donc elle est séparée de la preuve produit figée.

E2E : ouvrir une vraie archive après suppression de ses parents, observer le
titre en état conservé puis effectuer sa purge réelle et relire titre/badge,
volumes, code et reçu. Captures desktop/mobile, noms complets, focus et guide
recoupés. Raccordement : SLS-065 et prochain changement de console.
