# Régression008 des publications et du contrôle

Première tranche de la régression complète de [SLS-074](BACKLOG.md#sls-074),
selon [FUNCTION_VERSION_EXECUTION](FUNCTION_VERSION_EXECUTION.md#preuves-réelles).
Statut : première tranche implémentée et qualifiée en DEV par76 groupes. Les autres clients courants
et les parcours de console restent dans la matrice complète à réaliser.

## Périmètre et fidélité

Adapter uniquement control-operations.py, deployments.mjs et code-publications.mjs.
Conserver leurs55,11 et10 groupes respectifs :76 groupes réels prévus, dont21
par les API HTTPS du contrôle servi et55 sur le vrai contrôle Docker isolé.
La session préalable est établie par dev-sso-sessions.mjs depuis l'accueil/SSO
réels ; ce prérequis ne s'ajoute pas aux76 groupes. Aucun produit, route,
configuration, migration, image ou UI ne change pour cette tranche.

Les sources des bancs historiques006/007 restent inchangées. Les55 contrôles
courants exigent maintenant les huit migrations exactes et gardent intégrité,
UUID, verrou, refus de configuration, permissions et nettoyage. La même image
immuable sert les copies réelles, aucune dépendance n'est remplacée.

## Publications complètes

Le premier upload Create est publié sans cible. Vérifier l'appel sans tag refusé,
l'appel épinglé exécuté dans Docker, puis la première promotion explicite Create.
L'historique Read reste expurgé et montre correctement l'état actif après promotion.
Les droits, propriété du candidat, erreurs d'import, révocation et conflits
service/fonction pendant validation restent réellement éprouvés.

L'ancien cas de capacité suppose à tort un seul upload admis. Le contrat008
admet jusqu'à quatre uploads et sérialise leur validation. Deux candidats déjà
préparés et deux vrais uploads doivent être observables : le premier en validation,
le second admis en attente, puis deux publications terminales. Une lecture native
couplée doit constater les deux lignes validating et leurs réservations positives,
avec un seul validateur Docker vivant lié au premier candidat ; deux lectures
HTTP successives ne suffisent pas à prouver cette fenêtre. Le paquet déjà
connu réutilise sa révision/hash sans déplacer la cible. Le cas complet de quatre
admissions et cinquième429 possède sa preuve dédiée ; cette tranche ne le remplace
ni ne le réadditionne. Un rejeu du candidat terminal reste409.

Promouvoir ensuite le code différent par Update pour que le rollback par UUID
constitue un vrai changement de cible. Vérifier par une invocation réelle le
retour du handler initial avec configuration courante, et le hash effectivement
exécuté. Les suppressions par UUID conservent les refus Read, sans If-Match,
ETag périmé et cible active ; l'ETag correct permet le retrait inactif. Attendre
la fin physique avant comparer l'historique. Les huit candidats maximum restent
éprouvés sur leur fonction distincte.

## Publications de code seul

Après le premier code Create, prouver cibleNULL, absence d'appel sans tag,
appel épinglé puis promotion Create ; ressources, variables et secret par
empreinte restent ceux de la fonction. Pour le code Update, la préparation de
configuration et d'événements stable est d'abord publiée, puis promue explicitement.
Le nouveau paquet est publié sans déplacer cette cible. Appeler la cible encore
ancienne et le pilote épinglé, comparer configuration/événements/compteur, puis
promouvoir explicitement et invoquer par défaut.

Conserver les UUID corrélés, CRUD/portées/CSRF/ETag/modèle strict, propriété,
abandon, diagnostics expurgés, conflit et révocation pendant le vrai import.
La course upload/abandon garde un seul gagnant ; une publication gagnante peut
réutiliser un hash et ne change jamais la cible. Les six candidats de pagination
restent comparés aux lignes durables, avec configurations temporaires et octets
réservés effectivement effacés.

Sept invocations réussies sont prévues dans les deux clients : deux dans
la publication complète, cinq dans le code seul. Le compteur de la fixture
publication est incrémenté par POST seulement ; les GET suivants doivent lire
la même valeur persistante. Les refus ne s'ajoutent pas aux appels réussis.

## Preuves et reprise

Le pilote maintenu function-version-publication-regressions.py exécute les trois
campagnes en série et refuse son propre rapport préexistant. Les anciens rapports
locaux et natifs sont conservés par copie/empreinte avant régénération, sans
copier les fichiers privés de session. Les sources/images et fraîcheur de chaque
rapport sont recoupées ; un échec arrête la matrice, aucun skip ou rejeu automatique.
Les processus et requêtes engagés sont joints, les UUID de campagne conservés.
Les diagnostics supplémentaires enregistrent phase/type/code/coordonnées et
empreinte, sans message brut pouvant citer un secret.

Les deux clients utilisent la purge publique complète après suppression de leur
fonction ; leur ancien helper de purge directe de volumes ne suffit pas à
prouver effacement du code et reçu de décision du contrôle. Les empreintes
des révisions avant purge sont conservées comme telles, pas comme archives
encore présentes. Les helpers historiques ne changent pas de comportement.

La collecte finale indépendante lit les quatre fonctions des deux campagnes,
leurs reçus de purge, révisions, candidats, réservations, invocations et baux.
Les helpers opérateurs historiques restent limités à leurs namespaces autorisés.
Le contrôle servi, son image et son démarrage, la référence, le backend/web et
les fichiers officiels doivent rester identiques. Les trois notes de SPARK sont
proposées sans adoption implicite. Les essais interrompus restent séparés.

Cette tranche ne qualifie pas encore les autres clients API/CLI, les coupures
publication-recovery, les consommateurs vivants de public-invocations, la console
ou la suite complète. Elle maintient SLS-074[~], sans nouveau résultat visuel
ni changement de manuel. Toute contradiction produit révélée est reproduite et
spécifiée avant correction ; un test n'est jamais assoupli pour obtenir du vert.


## Résultats retenus

La [première tranche de régression008](evidence/function-version-publication-regressions-dev-2026-11-09.json) passe76 groupes sur292
sources figées :55 contrôles du vrai composant Docker et21 groupes HTTPS des
publications complètes/code seul. Le prérequis SSO réel reste distinct. Les huit
migrations, intégrité, verrou et refus de configuration sont conservés ; les11
et10 groupes de publication gardent droits, propriété, conflits, révocation,
import réel, abandon, course et pagination.

Upload et promotion sont distingués, y compris première promotion Create. Une
observation native recoupe deux candidats validating/réservés et le seul validateur
vivant du premier ; le doublon réutilise le hash et la révision canonique sans
changer la cible. Rollback et pilote sont réellement invoqués. Sept appels
recoupés en base vérifient hashes demandés/résolus, handlers et configuration.
Les cinq appels de code seul vérifient l’empreinte du secret ; les deux appels
de publication complète contrôlent sa présence puis son absence. Le compteur
POST reste1 lors des GET après promotion.

Quatre fonctions sont purgées par l'API publique, code/volumes/réservations absents
et parents supprimés. Les empreintes avant purge ne prétendent pas représenter
des archives encore conservées. Les5982 artefacts antérieurs et les services,
ID/images/démarrages, fichiers officiels et backend/web embarqués restent identiques.
Les anciens rapports restent préservés par SHA. Aucun build produit ni nouveau
parcours visuel ; les autres clients et la régression complète restent dans
SLS-074, toujours[~].

Les clients et le pilote ont été relus avant campagne. La preuve d'attente
exige le relevé natif couplé, au lieu de deux états lus séparément. Le pilote
joint son processus local même après une erreur de capture et déclare une issue
distante inconnue si cette jonction expire. Ces branches d'erreur propres du
pilote restent distinctes : leur revue statique ne vaut pas qualification E2E.
Les sources de la partie006/007 des bancs historiques ne sont pas réécrites.
