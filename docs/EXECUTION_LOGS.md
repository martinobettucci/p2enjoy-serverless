# Journaux d'exécution, recherche et corrélation

Contrat de [SLS-072](BACKLOG.md#sls-072), décidé le 22 novembre 2026 avant code.
Complète [CONSOLE_USABILITY](CONSOLE_USABILITY.md#journaux-et-corrélation),
[EXECUTION](EXECUTION.md#événement-réponse-et-journaux) et
[CONTROL](CONTROL.md#gestion). Produit à la décision : API 046, schéma 010, éditeur 070
et testeur 071 qualifiés ; journal avancé non implémenté à ce checkpoint.

Mise à jour du22novembre2026,11h00UTC : le code préparé est déployé sur
API1aa70214 et la migration011 est appliquée par la
[bascule gardée](EXECUTION_LOG_DEPLOYMENT.md). Les sauvegardes, le contenu de
l'image et la conservation des anciennes colonnes sont recoupés. Les12API,
10UI,25communs et régressions restent à exécuter ;072 reste `[~]`.

## Sources et frontières

Le runtime fournit aujourd'hui un buffer final stdout/stderr fusionné,64 Kio
par invocation, puis `validator.redact_logs` expurge les secrets effectifs avant
persistance. Ce chemin reste l'autorité de cette collecte : pas de second
drainage Docker, pas de substitution de logger ou de processus applicatif.
Une publication a son diagnostic privé ; les audits métier et commandes de
stockage sont des sources distinctes. La réservation d'instance disparaît
après extinction : son cycle doit désormais laisser des événements durables.

Décision : un registre dédié, typé et borné, dans la base du contrôle. Il évite
de transformer l'audit de sécurité en copie de stdout et permet des index
fonction/service/date. Les traces Docker du contrôle restent hors de cette
API ; aucune lecture brute de leurs fichiers n'est ajoutée. Les diagnostics
d'import et de stockage protégés par Update/créateur/admin ne sont pas copiés
dans un journal Read. Seuls leurs événements fixes et identifiants publics
rejoignent le registre. Aucun corps, en-tête libre, cookie ou jeton n'est
ajouté par l'instrumentation de plateforme.

## Modèle et migration 011

La migration additive `011_execution_logs.sql` crée :

- `execution_log_events` : séquence interne entière autoincrémentée, UUID
  public unique, service/fonction nullable selon le sujet, source application
  ou platform, type d'événement, niveau nullable, état, date observée UTC,
  invocation/requête/instance/révision/hash/candidat/opération nullable,
  message texte expurgé, métadonnées publiques fixes, indicateurs de troncature
  et taille UTF-8 comptabilisée. Index de période et de sujet, ordre stable
  par date puis séquence ; la séquence ne se réinitialise pas lors des purges.
- `execution_log_state` : ligne unique de collection, UUID durable, début réel
  de collecte, compte/octets réservés et dernier effacement par capacité.
- `service_log_policies` : service unique, rétention, version positive, date
  de modification, frontière d'expiration irréversible et dernier effacement
  du périmètre. Défaut sept jours ; aucune réécriture des dates antérieures.

`invocations.logs_collection_state` distingue pending, collected, unavailable,
not_started, expired et unknown. Les anciennes lignes non vides attestent une
collecte ; un ancien buffer vide reste unknown. Une réponse runtime réellement
validée atteste collected même sans message ; un runtime perdu sans résultat
atteste unavailable. Un appel jamais dispatché est not_started. Le restart
marque unavailable les appels interrompus concernés, sans rejouer le handler.
La rétention d'observation 7 jours/10000 invocations et son exception pour tir
planifié actif restent distinctes de la rétention du contenu du journal.

Le registre commence à l'installation de 011. Il ne fabrique pas un historique
de démarrages/extinctions passés et ne copie pas des diagnostics privés.
La lecture indique le début de collecte lorsque la période le précède.
Les anciens audits et métadonnées métier restent intacts.

## Collecte et événements

Les producteurs inscrivent un événement avec leur décision SQL lorsqu'elle
existe ; un rollback ne laisse pas une réussite dans le journal. Les transitions
répétées et la reprise ne dupliquent pas une même observation durable.
Les champs viennent de projections explicites, jamais d'un dict métier libre.

Événements attendus : publication préparée/publiée/refusée/interrompue,
promotion ou retrait de cible, réservation/démarrage/disponibilité/extinction
confirmée d'instance et échec de nettoyage ; réception/admission/dispatch/fin
d'appel, timeout, refus d'admission connu ; préparation/phase/fin des commandes
publiques de stockage. La corrélation conserve les UUID effectifs et le hash
résolu, non le hash de la cible relu après coup. Un refus précoce authentifié
peut avoir un request_id sans invocation créée : ce fait est explicite.
Un trafic anonyme ne remplit pas ce registre ; le logger borné existant demeure.
Chaque événement conserve les références connues lors de sa transition. Pour un
appelHTTP nominal, received/queued précèdent la résolution : hash, révision et
instance restent null. L'admission inscrit les références résolues qui se
retrouvent dans admitted/dispatched/completed. Un hash demandé n'est pas un hash
résolu ; une lecture ultérieure ne complète pas ces événements avec la cible
courante. La purge d'une autre fonction ne modifie aucun de ces événements.


Classification séparée : réponse applicative (y comprisHTTP 500 rendu par le
handler avec état succeeded), exception/import de code, refus d'admission,
timeout et défaut d'infrastructure. Le statut HTTP seul ne décide pas la classe.
Les événements de plateforme portent leur niveau défini ; pour l'application,
seul un champ JSON explicite non ambigu `level` ou `severity`, chaîne parmi
trace/debug/info/warn/warning/error/fatal, fournit un niveau. `warn` devient
warning. Nombre, valeur inconnue, contradiction ou doublon restent non renseignés.
stdout/stderr fusionnés n'autorisent aucune déduction de sévérité.

Le texte exact reste échappé. Un JSON valide peut être présenté lisiblement ;
une entrée invalide, trop profonde, tronquée ou ambiguë reste du texte, sans
erreur de collecte. Aucun rendu HTML actif. Un timestamp déclaré par le code
reste une donnée du message ; l'ordre du registre utilise la date observée.
Les lignes applicatives sont observées à la fin de l'invocation ; ce temps ne
prétend pas être l'instant exact de chaque `console.log`. Le suivi n'annonce
pas du streaming pendant un handler encore actif.

Bornes :64 Kio au buffer existant,1024 lignes projetées au plus par invocation,
4096 octets UTF-8 par message de registre et 2048 octets de métadonnées publiques.
Chaque limite produit son indicateur ; la vue d'invocation conserve son buffer
original jusqu'à expiration, avec sa propre limite de collecte 64 Kio.
Pas de perte silencieuse entre projection partielle et buffer original.
La borne de65536 octets porte sur la capture brute du runtime ; le buffer
original exposé est déjà expurgé, donc sa taille peut être inférieure. Si la
capture est tronquée et que des secrets sont effectifs, le validateur retire
encore `max(longueur UTF-8 des secrets)-1` octets à sa fin avant remplacement,
pour ne pas exposer le préfixe d'un secret coupé. Il conserve le drapeau de
troncature. La conversion UTF-8 et les remplacements restent bornés à65536.
L'égalité65536 à la frontière brute se teste dans un service sans secrets ;
le même dépassement avec secrets vérifie séparément le retrait de protection.
Décision120, après [huit mesures réelles](evidence/execution-journal-buffer-diagnostic-dev-2026-11-22.json) :
corriger le client, conserver le runtime et le validateur. Exiger une taille
brute après expurgation obligerait à affaiblir une protection existante.
L'expurgation de secrets précède toute analyse/indexation/troncature du message.
Elle protège les secrets effectifs connus ; un code qui imprime volontairement
des données métier inconnues reste responsable de ce contenu.

## Conservation par service et budget

Rétention normale sept jours, réglable par administrateur du service entre une
minute et sept jours, par minutes entières. Ce réglage opérationnel permet
de réduire la conservation ; sa preuve utilise réellement une minute, jamais
une horloge modifiée ni des timestamps injectés. Il ne prouve pas sept jours
écoulés : le défaut et la même règle paramétrée sont recoupés séparément.

Le registre entier est plafonné à 10000 événements et 16 Mio de messages/métadonnées
comptabilisés. Avant d'exposer une écriture qui dépasse le budget, retirer les
plus anciens événements nécessaires et conserver une frontière de perte. Les
compteurs et suppressions sont transactionnels. Le nombre d'objets, leur taille
et le travail par collecte sont bornés ; aucun cache mémoire non borné.

Précision décidée avant qualification : 16 Mio remplace le premier choix de
32 Mio. Le buffer final de 64 Kio et les événements de plateforme par appel
rendent les deux frontières trop proches avec 32 Mio ; 16 Mio permet d'isoler
le volume avant 10000 événements, et le nombre avec des messages courts, par
de vrais handlers. Cette limite réduit aussi le contenu conservé. La preuve
emploie deux corpus réels pour la borne exacte et une entrée augmentée d'un
octet, sans édition SQL des événements. Les dates de métadonnées publiques
sont formatées en ISO UTC à microsecondes fixes, à partir des vrais temps du
contrôle : leur représentation est lisible et de taille prévisible, sans
modifier l'horloge ni les dates métier. La colonne observée reste en secondes.

Réduire la rétention fixe une frontière durable maximale ; l'augmenter ensuite
ne ressuscite pas du contenu expiré. Les lectures l'appliquent immédiatement.
La maintenance efface le contenu expiré des événements et des buffers
d'invocation, par lots bornés, sans supprimer avant terme leur chronologie.
Elle conserve l'état expired après effacement. La purge d'une fonction retire
ses contenus de journal dans la décision de purge ; les références publiques
fixes d'audit gardent leur propre contrat. Supprimer un service vide retire
sa politique et ses contenus de journal. Aucun effacement de logs d'un autre
service n'est assimilé à une purge du service courant.

Une page/suivi devenu incomplet par expiration, purge ou budget est signalé,
jamais présenté comme une recherche complète. Une absence de message collected,
une collecte unavailable, un historique unknown et un contenu expired sont
des états distincts. Les quotas/rétention sont exposés avec période et unités.

## API, droits et snapshots

- `GET /api/functions/{id}/logs` et `/api/services/{id}/logs` : session admin
  ou Read du périmètre, contrôle avant existence et recontrôle après IO.
  Un jeton limité à des fonctions ne reçoit que celles-ci ; aucun élargissement
  par filtre, curseur, export ou identifiant deviné. La fonction de consultation
  est vivante, comme l'observation existante. Le service est vivant.
- `GET .../logs/export?format=jsonl|text` : mêmes droits/filtres/snapshot.
  Téléchargement attaché, no-store/nosniff,1000 événements et 1 Mio UTF-8 maximum
  par lot ; indicateur de résultat partiel et position suivante explicites.
  JSONL reste du JSON échappé ; le texte quote les messages pour ne pas fabriquer
  de fausses lignes de plateforme. Aucun CSV ni HTML interprété.
- `GET /api/services/{id}/log-policy` : Read/admin. `PUT` : session admin,
  CSRF et If-Match de la version de politique ; refus 409 sans changement si
  obsolète. Mutation atomique, non rejouée après réponse inconnue. Une écriture
  identique ne prétend pas modifier la valeur. La fonction/son ETag ne changent pas.

L'écriture de politique utilise aussi un worker SQL joint, nommé
`journal-write`, avec deadline2s et attente SQLite bornée ; elle ne bloque pas
la boucle HTTP et ne consomme pas l'une des deux places de lecture. Un refus
503 ou une réponse perdue impose une relecture avant toute nouvelle mutation :
la réception d'une erreur de transport ne démontre pas l'absence de commit.

Filtres combinables : from/to UTC finis, période maximale sept jours, source,
niveau connu ou non renseigné, état, invocation UUID, instance UUID, version
(hash complet de 64 caractères hexadécimaux minuscules), type d'événement et texte
littéral avec casse respectée (200 caractères). Aucun regex ni requête SQL libre.
Défaut dernière heure ; sans période explicite, un lien filtré par invocation,
instance ou version porte sur les sept derniers jours pour retrouver un objet
historique encore conservé. Le comportement est identique en API et console.
Presets 15 minutes/1 heure/24 heures/7 jours. La réponse nomme
la période effective, la source, le début de collecte et la rétention disponible.

Pagination historique :1–20 événements (UI 5), offset 0–10000, ordre date/séquence
décroissant. Premier relevé : plafond de séquence et filtres scellés dans un
snapshot opaque signé, lié au périmètre et à l'acteur ; nouvelles insertions
ne déplacent pas les pages. Une suppression rendant ce snapshot incomplet
provoque 410 avec motif de rétention/purge/budget, pas un saut silencieux.
Un snapshot altéré, étranger ou incohérent est refusé après autorisation.
La query partageable conserve filtres/page ; une reprise de snapshot expiré
demande un nouveau relevé explicite.

Le premier relevé renvoie `items`, `total`, `snapshot`, `next_offset`,
`follow_cursor`, `period`, `collection` et `limits`. Le snapshot expire au bout
de quinze minutes ; sa date, la collection, l'acteur et sa portée sont signés
avec la clé existante du contrôle, sans nouvel état de session. Les filtres
effectifs sont retournés pour éviter toute interprétation du client. Une
frontière d'effacement par service invalide conservativement les anciens
snapshots de ce service, même lorsque leurs seuls filtres auraient évité les
lignes retirées. C'est un refus explicite, pas une prétention d'exhaustivité.

L'export porte les en-têtes `X-Log-Count`, `X-Log-Partial`,
`X-Log-Next-Offset` (vide en fin), `X-Log-Snapshot` et `X-Log-Collection`.
Le corps contient uniquement les événements : un objet JSON par ligne JSONL ;
en texte, date, source, niveau et identifiants fixes puis message encodé comme
chaîne JSON. La taille est comptée après sérialisation UTF-8 réelle, nouvelle
ligne comprise. Un lot plein fournit une reprise explicite avec le même
snapshot et le prochain offset ; aucun téléchargement ne déclenche de boucle
serveur illimitée. La lecture historique et le suivi sont eux aussi plafonnés
à 1 Mio sérialisé, sans transformer une page tronquée en page complète.

Suivi : un curseur signé parcourt les nouvelles séquences en ordre croissant,
100 événements maximum par lecture et bornes de réponse conservées. Chaque GET
réautorise ; pas de flux SSE conservant un ancien rôle. Le client sérialise ses
lectures (intervalle 2 s), rattrape les lots, déduplique les UUID et garde 200 entrées
au plus en mémoire, avec indication de sa fenêtre. Pause/arrêt ne mutent pas
les données. Après coupure, reprendre au dernier curseur confirmé ; une lacune
de conservation reste signalée et exige de repartir explicitement.

Le curseur initial de suivi est séparé du snapshot historique : il part du
plafond de séquence du relevé, daté de sa création, et reprend ses filtres de
contenu et de sujet. Il ne conserve pas le `to` figé de la recherche. Chaque
lecture de suivi a pour borne supérieure son instant serveur courant ; sa
borne de reprise est exclusivement la dernière séquence acquittée. Les dates
de début et de lecture sont informatives, sans filtre temporel qui pourrait
perdre une transaction déjà commencée et commitée après le relevé initial.
Le plafond de séquence est relu dans la transaction de chaque lecture. Son
horizon reste l'instant de création plus sept jours. La réponse nomme ces
bornes et le mode actif. L'UI annonce le
passage de la période historique aux nouveaux événements. Au-delà des sept
jours, le curseur donne 410 `follow_horizon_expired`, demande un nouveau relevé
et ne saute pas silencieusement une période. Un curseur historique expiré
n'interdit pas la reprise d'un curseur de suivi encore valide et sans lacune.

Deux lectures/requêtes d'export concurrentes au plus, capacité rendue seulement
après jonction de l'IO. Une troisième est refusée 429/Retry-After 2. Travail SQL
et transformation hors boucle HTTP, données finies/limites et budget monotone
de 2 s contrôlés ; un IO suspendu conserve sa responsabilité jusqu'à jonction.
Timeout/coût excessif ou stockage indisponible donnent un refus contrôlé 503,
sans anciennes lignes exposées ni succès de secours. ACL et visibilité sont
relues après l'IO ; modification du contexte/politique refuse le résultat périmé.

Précision d'implémentation décidée avant correction : le budget monotone de
deux secondes est partagé par tous les nouveaux IO SQL du journal, y compris
sujet et vérification finale. La même deadline est transmise aux workers,
délais SQLite et progress handlers. Le protocole OIDC commun (réseau et
stockage des identités) garde ses bornes existantes ; ce budget ne promet pas
une réponse HTTP totale de deux secondes pendant un renouvellement SSO.

Après le worker principal et la nouvelle autorisation réelle, une courte
transaction `BEGIN IMMEDIATE`, hors boucle HTTP, vérifie ensemble visibilité,
politique et droits courants. Cette réservation empêche une révocation ou
purge de committer entre les SELECT de cette décision. Les droits sont relus
en dernier ; la transaction est entièrement jointe avant restitution de la
place. Son commit constitue le point de décision de lecture. Une révocation
acceptée avant ce point refuse le contenu ; une écriture concurrente qui doit
attendre cette réservation est ordonnée après la lecture et protège les appels
suivants. Aucun verrou n'est conservé pendant l'envoi réseau de la réponse.
Une simple transaction de lecture WAL, ou une suite de SELECT sur son ancien
snapshot, ne fournit pas cette frontière : ce choix est écarté pour ce motif.
La réservation ne change aucune donnée métier et reste sous la même deadline.
Références de sémantique : [transactions SQLite](https://www.sqlite.org/lang_transaction.html)
et [isolation WAL](https://www.sqlite.org/isolation.html), consultées le 22 novembre 2026.

La preuve distingue le changement accepté avant la décision finale (refus du
résultat), celui accepté après son commit mais avant la réponse réseau (lecture
encore valide puis refus du snapshot aux appels suivants), et la réponse de
politique perdue après son commit réellement constaté. Les phases natives de
fin de worker et les résultats HTTP/versions/audits recoupent ces ordres. Elle
ne fait pas passer un timeout ou une requête seulement envoyée pour une preuve
de droits ou de commit, et n'exige pas un EAGAIN noyau pour un conflit que SQLite
peut résoudre à l'intérieur du même processus.

Les messages applicatifs de fonctions supprimées ne sont pas ouverts par cette
API. Une vue service peut conserver les résumés fixes de plateforme selon les
ACL de l'audit existant ; noms inaccessibles et diagnostics privés sont retirés.
Un lien vers un objet indisponible devient une référence nommée, pas un lien mort.

## Console et manuel

Facette **Journaux** dans fonction et service ; le catalogue et la query de
retour restent conservés. Filtres près de la collection, états chargement/vide/
erreur/sans droits/partiel distincts, aucune pagination périmée pendant lecture
ou refus. Date UTC, niveau, source/type, état, sujet et corrélation restent
lisibles ; les UUID/hashes complets se replient. Un événement de plateforme
et un message applicatif diffèrent aussi par leur forme/libellé.

Le détail se déplie dans le flux : texte/JSON, troncature, provenance du temps,
appel, hash réellement exécuté, instance et chronologie. Le résultat du testeur
rejoint cette consultation filtrée sans nouvelle invocation. Lecture et export
ne présentent pas une attente arrêtée comme une annulation du handler.
Le suivi garde le focus et n'accumule pas indéfiniment le DOM ; le compteur
de nouvelles entrées est annoncé poliment. Les réponses d'une ancienne query
ne remplacent ni la nouvelle liste ni les saisies de filtre.

La pause protectrice du focus concerne seulement la limite de fenêtre200,
jamais un retrait exigé par conservation ou visibilité. Dans ce dernier cas,
retirer le contenu et rendre le focus au titre. Un export refusé pour droits
ou relevé incomplet invalide aussi l'état principal : pas d'anciennes lignes,
totaux, curseur ni reprise d'export. Une page refusée rend son focus au titre.
Les liens par instance et par hash ouvrent leur journal historique filtré,
sans promettre qu'un conteneur ou un paquet supprimé est encore disponible.

Conservation du service : Facts, commande Modifier ouvrant un dialog limité à
la politique. Saisie numérique en minutes (plus de 400 crans, pas de faux curseur),
refus conservant la saisie ; réduction confirmée dans le flux en nommant le
service et le contenu qui expirera. Échap/annulation rendent le focus. Aucun
réglage de variables/secrets ni durée de fonction n'est confondu avec cette politique.

Socle [DESIGN_SYSTEM](DESIGN_SYSTEM.md) et extension locale obligatoires ; mêmes
Section/Field/Facts/Resource/Pages/dialogs, icônes Lucide et marque trois blocs.
Desktop/tablette/mobile 390, code défilant localement avec indication, aucun
débordement global. Manuel canonique mis à jour et recompilé dans l'image ;
les anciennes observations restent une destination compatible, avec les nouveaux
libellés de collecte/expiration, sans exposer les contenus supprimés.

## Déploiement et retour

Le [protocole de bascule011](EXECUTION_LOG_DEPLOYMENT.md) définit la supervision,
les deux sauvegardes natives et les frontières avant arrêt/avant migration.

011 est additive : anciennes colonnes et valeurs restent lisibles par 046 au
niveau structurel, mais 046 ne connaît pas la rétention du contenu. Une sauvegarde
SQLite native, l'intégrité et l'image précédente sont vérifiées avant migration.
La garde ne peut remettre 046 que si 011 n'a pas été commitée. Dès ce commit,
tout retour automatique à 046 est interdit, même avant la première modification
de politique : la collecte et la rétention par défaut peuvent déjà avoir changé
la visibilité. La reprise utilise la même image compatible 011 ou une correction
en avant. Un éventuel futur retour exige une image dont la rétention est
compatible et qualifiée ; le volume et la base ne sont jamais restaurés
automatiquement sur des écritures acceptées.

La collecte se raccorde à la décision de terminaison du moteur, pas à un
consommateur asynchrone susceptible d'oublier son message. Les anciens appels
silencieux ne deviennent pas artificiellement collected. L'indicateur interne
de réponse runtime validée est propagé jusqu'à la transaction de terminaison ;
les erreurs de protocole et pertes de canal ne sont pas inférées d'un texte vide.

## Découpage et qualification réels

1. Contrat/schema/UI/manuel/backlog et décisions persistés avant code.
2. Registre 011, producteurs, API/relecture d'ACL, politique/rétention/export.
   Fixtures originales Docker ; aucune écriture de données de test par SQL.
3. Facettes/service/fonction et liens du testeur, contrôles d'accessibilité,
   erreurs et suivi ; aucune commande morte avant backend disponible.
4. Image DEV et image de retour vérifiées, sauvegarde native, déploiement gardé ;
   actualisation des seules préconditions courantes 010→011 avant leur exécution,
   en conservant les branches historiques 003/006/007/008/009 et captures scellées.
5. Douze groupes API et dix UI spécifiques, puis 25 communs frais (47), sans skip.
   Couvrir vrais texte/JSON/Unicode/HTML inerte, niveaux connus/inconnus, secrets,
   bornes 64 Kio/4096 octets/1024 lignes et+1, budgets 10000/16 Mio, filtres/pages/snapshots,
   ACL directes/scopes/révocation, états silence/perte/expiration, politique 60 s
   réelle et concurrence/CSRF/perte de réponse, limites de lectures, exports,
   événements publication/instance/timeout/stockage, coupure du contrôle et reprise
   sans invocation rejouée. Captures fraîches toutes ouvertes individuellement.
6. Régression sur 011 du socle nommé `execution-suite.py --scope schedules`,
   soit 49 campagnes/543 groupes, puis des consommateurs ajoutés depuis ce socle.
   Les clients éditeur, testeur, versionnement et surveillance d'instance font
   l'objet d'un inventaire distinct avant adaptation de leurs préconditions.
   Le total est celui de cet inventaire, jamais 543 présenté comme couverture
   complète. Les 25 communs rejoués ne s'ajoutent pas deux fois ; époques et
   rapports restent séparés. Toute divergence devient une unité avant correction.

Les groupes détaillés reprennent les cinq critères 072 : droits/recherche,
formats et collecte, cycle/corrélation, bornes/rétention/exports, suivi/reprise,
concurrence/versions et parcours UI. Les tests de comportement passent tous
par le vrai SSO/API/passerelle/Docker/FUSE ; ni mock, stub, interception réseau,
faux serveur, horloge modifiée ou seed SQL. Gardes indépendantes, vrais signaux,
identités natives et consommateurs joints avant réussite. Un échec reste scellé.

Répartition des groupes spécifiques, fixée avant les clients :

| Groupe | Preuve propre |
| --- | --- |
| API 01 | Vrais buffers texte/JSON/Unicode, silence attesté et niveaux connus ou inconnus |
| API 02 | Read, mauvais droits, autre service, fonctions limitées, révocation et identifiants devinés |
| API 03 | Filtres combinés, limites exactes et +1, ordre et pages stables sous nouvelles écritures |
| API 04 | Collecte 64 Kio, messages 4096 octets et 1024 lignes, troncatures distinctes et secrets expurgés |
| API 05 | Budget 10000 événements, premier dépassement, compteurs et perte explicite |
| API 06 | Budget 16 Mio, borne exacte puis entrée +1 octet dans deux corpus réels, sérialisation et compteurs réconciliés |
| API 07 | Expiration réelle 60 s, buffer effacé, augmentation sans résurrection et snapshot 410 |
| API 08 | Politique admin/CSRF/If-Match, conflit, écriture identique et réponse perdue sans rejeu |
| API 09 | Exports JSONL/texte, lots 1000/1 Mio, reprise, échappement et mêmes ACL |
| API 10 | Suivi, pause, nouvelles séquences, reprise après coupure, curseur altéré et contexte étranger |
| API 11 | Publication, code en erreur, réponseHTTP 500, admission, instance, timeout et stockage corrélés |
| API 12 | Deux vrais IO de lecture retenus, troisième 429, délai, jonction et reprise après défaut réel |
| UI 01 | Entrée accueil → fonction/service → Journaux, contexte et retour catalogue |
| UI 02 | Filtres, pages et période partageables, vide et nouvelle requête |
| UI 03 | Chargement, refus et perte de conservation sans anciennes lignes ni totaux |
| UI 04 | Détails texte/JSON, troncature, temps observé et références complètes |
| UI 05 | Corrélation depuis le résultat du testeur sans nouvelle invocation |
| UI 06 | Suivi/pause/reprise et fenêtre bornée sans perte de focus |
| UI 07 | Politique, confirmation de diminution, conflit conservant la saisie et relecture |
| UI 08 | Exports réels et poursuite explicite du lot |
| UI 09 | Clavier, Échap, restitution du focus et texte agrandi |
| UI 10 | Desktop/tablette/mobile, longues lignes locales et absence de débordement global |

L'observation native d'un IO retenu n'injecte pas de résultat : elle suspend
uniquement ses vrais threads par ptrace, avec identité de naissance et garde
indépendante de restitution, puis constate les réponses et leur jonction.
Une précondition physique manquée échoue ; aucun délai artificiel ou endpoint
de test n'est ajouté au produit. Les écritures de corpus passent par les handlers.

Les sources et images effectivement déployées, backend/web/manuel, intégrité/FK,
onze migrations, notes/configuration/référence/5982 originaux et purge physique
des seuls UUID possédés sont recoupés. Aucun profil PREPROD/PROD ni opération
FORGE. Régression manquante, capture non inspectée ou preuve résiduelle garde
072 `[~]`. Aucune réalisation ni nouvelle preuve n'est acquise par ce contrat.

### Instrumentation native des lectures

Décision avant les opérateurs : ils portent des noms propres au journal et ne
modifient pas les programmes ou reçus historiques de l'éditeur. Un opérateur
vérifie l'image/génération Docker, la naissance et le cgroup du contrôle, les
seuls UUID de son namespace original et les empreintes des configurations
officielles. L'accès opérateur à SQLite reste en lecture seule sous UID1001.
Les fichiers de garde sont privés, immuables pendant la fenêtre et recoupés par
empreinte ; une garde systemd indépendante peut tuer le seul traceur possédé
par pidfd, restituer ses ressources puis constater la libération de ses threads.

Correction121 décidée après les mesures500/501 : les modes ci-dessous sont
implémentés dans le banc ; leurs preuves restent à produire sur le corpus réel.
Le produit1aa70214 reste inchangé. Les noms de workers existants suffisent ;
aucun nouveau point d'arrêt, endpoint, nom diagnostique ou flag n'est ajouté.

Les travailleurs du produit portent les noms `journal-subject`, `journal-read`,
`journal-verify`, `journal-policy` et `journal-write`. Le mode `read` retient
l'entrée réelle openat du SQLite principal dans journal-read ; `write` fait de
même dans journal-write pour éprouver l'autorité retirée avant l'écriture.
Les nouvelles frontières utilisent le prctl(PR_SET_NAME) qui restitue le nom
précédent dans le finally de reader_name, après retour du callback et contrôle
de sa deadline. Le comm courant identifie le worker qui se termine. Ptrace
n'en change ni arguments, registres, résultat ni mémoire. Les autres threads
sont détachés dès acquisition de la frontière, et tous sont joints ensuite.

- `read-result` : fin du worker journal-read, avant la nouvelle autorisation
  et la transaction finale. Une politique réellement modifiée et acceptée
  pendant cette retenue doit donner410/log_policy_changed après libération,
  sans anciennes lignes ni timeout de substitution.
- `read-decision` : fin de journal-verify après retour de final_check. Le même
  thread doit avoir acquis puis libéré le verrou WAL d'écriture réel (bon
  inode/byte120, fcntl réussis), avant le prctl de restauration. Le PUT concurrent
  est réellement committé alors que la réponse GET reste retenue. Après
  libération, GET200 demeure valide et son ancien snapshot donne410. Le code
  de succès et le chemin final_check qui committe avant retour distinguent
  cette issue d'une erreur qui passerait aussi par le finally.
- `policy-commit` : fin de journal-write, avec acquisition/libération WAL et
  prctl de restauration. Version et audit sont relus pendant la retenue et
  attestent le commit. La vraie connexion HTTP est ensuite détruite, puis le
  worker libéré : erreur cliente, même unique version/audit et aucun POST rejoué.
- `sqlite-reservation` : arrêt au retour réussi du F_SETLK exclusif byte120,
  réservé à la faute de garde122. Ce point peut encore être dans le mutex
  interne SQLite ; il ne sert pas à prouver l'ordre des requêtes concurrentes.

L'ancien discriminant journal-write/F_SETLK→EAGAIN est écarté : SQLite peut
refuser le verrou entre connexions sœurs avec SQLITE_BUSY avant tout fcntl.
Le point d'arrêt au retour du fcntl peut aussi précéder la libération de son
mutex interne et empêcher l'autorisation SQL du PUT d'atteindre journal-write.
La [mesure501](evidence/execution-journal-independent-guard-closure-dev-2026-11-22.json)
et le [diagnostic500](evidence/execution-journal-final-lock-diagnostic-dev-2026-11-22.json)
conservent ce qui a été réellement observé, sans attribuer une pile native non
capturée. Cette correction porte le banc, pas l'application ni ses transactions.
Références : [source SQLite unixShmLock](https://sqlite.org/src/doc/trunk/src/os_unix.c)
et le code réellement déployé reader_name/io/final_check/write_policy.

L'observateur attend les arrêts natifs par un réveil SIGCHLD sur pipe non
bloquant (`signal.set_wakeup_fd`), puis lit tous les statuts réels par waitpid.
Le pipe ne compte pas des événements : ses octets servent seulement au réveil.
L'attente select reste bornée par la même échéance ; le gestionnaire, le wakeupfd
précédent et les deux FD sont restitués après détachement. Cette décision121
supprime le sommeil fixe0,5ms dont le coût pouvait empêcher d'atteindre la phase
finale sous le budget produit. Elle ne modifie aucun registre/résultat ni budget.
Référence de mécanisme : [documentation Python3.14](https://docs.python.org/3.14/library/signal.html#signal.set_wakeup_fd).
La [mesure500sources](evidence/execution-journal-final-lock-diagnostic-dev-2026-11-22.json)
précède la correction ; les mesures501 attestent ensuite l'acquisition du verrou
avec réveil natif, sans qualifier l'ancien scénario writer. Les nouvelles
frontières de fin de worker restent à éprouver sur le corpus réel.

Acquisition au plus40s, retenue totale45s, alarme50s et secours60s ; la lecture
du produit garde son propre budget2s, qui n'est jamais étendu par ce banc. Une
preuve d'ACL doit donc accepter le changement et libérer la première barrière
avant sa deadline ; sinon elle échoue, même si le refus final est503. Deux IO
retenus peuvent dépasser2s pour prouver429, responsabilité jusqu'à jonction et
retour de capacité. Libération explicite, EOF et perte réelle du traceur sont
recoupés avec absence de tracer/arrêt sur tous les threads et santé de l'API.

Le défaut natif de stockage est un vrai `EMFILE` au `openat` observé : arrêt
borné des autres threads, limite réelle de descripteurs abaissée, constat du
résultat noyau négatif, puis limites initiales rétablies **avant** reprise de
Python. Aucune écriture de registre ni remplacement de syscall. La garde
restitue aussi cette limite si le traceur disparaît. L'échec contrôlé503 et la
lecture suivante réussie sont des preuves HTTP séparées de l'observation native.

La clôture du client sépare toujours la fermeture locale (API, contextes,
navigateur, paquet temporaire) de la purge métier. Un finally externe ferme
les ressources locales même si la jonction native ou la sauvegarde du rapport
échoue. La purge exige les gardes réellement jointes ; sans cette preuve, les
UUID restent au rapport rouge pour récupération explicite. Après un échec de
santé immédiat, le client peut observer le reçu de la garde déjà armée jusqu'à
125s depuis le lancement du helper (60s+55s existants et10s de jonction), avec
statuts/identités/threads/santé recoupés avant finish. Le scénario n'est pas
rejoué, les bornes40/45/50/60 et les2s du produit restent identiques. Les erreurs
de tentative et d'observation sont conservées ; une récupération acquise rend
le nettoyage possible mais ne transforme pas l'échec primaire en réussite.
Contrat et preuve propre de ce flux : [SLS-122](BACKLOG.md#sls-122).
Le restorer attend HTTP200 et Dockerhealthy dans son alarme55s existante ; une
photographie Docker encore unhealthy ne suffit pas à abandonner une reprise.
Il conserve128sondes au plus, leur dépassement et le dernier état. L'expiration
globale utilise une exception distincte des timeouts réseau et ne peut pas être
absorbée par une nouvelle sonde. Chaque reçu identifie le PID/naissance/cgroup
du restorer et son origine exacte. `independent` demeure le mode rescue ; une
preuve de timer recoupe l'ID du reçu et le PID avec le journal de l'unité
systemd. Le marqueur d'échec conserve ce rattachement même si la garde échoue ;
le mode recover-low-fds traité garde un unique JSON stdout.
Le client de preuve isolé peut attendre exclusivement la garde indépendante
après un SIGSTOP réel du seul helper possédé. Cette option est dans le banc,
jamais dans le produit. Elle n'émet aucun secours actif avant le timer60 et
reste sous la borne client125s ; le GET503 demeure rouge après purge réussie.

Pour la coupure du contrôle, le handler original du compteur écrit et fsync son
compteur, puis écrit et fsync un reçu portant son vrai identifiant d'appel et
la valeur acquittée, avant son attente métier. Seul ce reçu postérieur au fsync
autorise le signal. Sa présence n'est pas un résultat de passerelle ni une
réponse applicative : la preuve de non-rejeu compare les UUID et la lecture
ultérieure explicite du compteur. Aucun hook de test n'est ajouté au produit.

Cette coupure garde le protocole déjà qualifié45s/180s/10s (déclenchement du
secours/alarme de restitution/sonde du reçu), avec nom propre au journal. La
garde conserve le CID et l'image011 effectivement observés ; elle ne reconstruit
ni046 ni un conteneur d'une autre image. Un mutateur Docker séparé conserve le
verrou hérité jusqu'à son reçu137 et sa jonction. La restitution joint le seul
traceur reconnu, attend ce verrou, contrôle le CID/génération/référence, puis
redémarre ce même conteneur si nécessaire. Un démarrage est borné par ses vrais
instants de demande/retour. Reçu terminal durable et garde entièrement jointe
sont requis avant le nettoyage des fonctions. Les programmes historiques de
coupure restent inchangés ; leurs résultats ne s'ajoutent pas à cette campagne.


Diagnostic d'armement123 : le helper conserve phase, type/errno, SHA du message
et fichiers/lignes de traceback dans son répertoire /run possédé, et émet ce
reçu avec unit. Les seules métadonnées de compteur observées sont type/UID/mode,
empreinte du reçu déjà synthétique, identifiant et état de l'invocation. Aucun
stderr brut, buffer applicatif, cookie, argument privé ou écritureSQL. Les
photographies transitoires restent observées avant de décider de leur cause ;
les bornes30/35/40/45/180 et la condition fsync avant signal restent inchangées.


Décision123 après diagnostic réel : la présence du reçu fsync peut précéder
l'acquittement asynchrone /started. running avec handler_started=null, mêmeUUID,
même fonction, non terminé et unique actif reste en attente dans la borne30s
existante. Le signal exige toujours handler_started=1 ;0 ou toute contradiction
reste un échec. Le reçu cut conserve premier tuple d'attente et acquittement
suivant. Aucun runtime, délai produit ou condition durable n'est modifié.


Pour éprouver cette attente123 sans dépendre de son ordonnancement spontané,
le banc prépare une instance réellement disponible, sans invocation préalable.
Il observe uniquement le principal, avec NativeObserver et garde déjà armée,
jusqu'au retour read/recvfrom sur le socketUNIX du canal de cette instance.
L'inode est recoupé dans /proc/net/unix et le chemin est celui de
/state/execution/INSTANCE/i-…/control.sock. La lecture mémoire est bornée à la
seule ligne exacte `POST /started HTTP/1.1\r\n`, sans en-tête ni corps ; pas de
modification de mémoire, registre, résultat ou protocole. Fermer le suivi d'un
FD à sa réutilisation. Le retour reste retenu au plus1s et dans l'acquisition30s
existante pendant que le handler publie son vrai reçu. Un tuple null constaté
avec les mêmes identités est conservé, puis le principal est immédiatement
détaché pour permettre son vrai acquittement1 ; sinon échec et restitution.
La fixture passe ensuite minimum0/idle0 après le redémarrage avant les lectures
du compteur. Le runtime ne reçoit aucun indicateur ni branche de test.


Diagnostic complémentaire123 : le seul helper de coupure conserve nombres de
stops et syscalls, heures de début/fin, retours de lecture et au plus32inodesUNIX
rencontrés. Les chemins en clair restent dans /state/execution ; tout autre nom
est haché. L'instance correspondante est explicite ; aucun octet applicatif ou
en-tête supplémentaire n'est lu. Le premier relevé garde le poll1ms partagé,
avant décision de sa correction ; les époques et sources restent distinctes.


Après mesure du poll123, NativeWakeup déjà utilisé par121 est extrait à
l'identique dans un moduleE2E commun. Le CounterObserver remplace uniquement son
sommeil fixe par ce réveil SIGCHLD, sans modifier le matcher ni ses bornes.
waitpid demeure l'autorité ; pipe/handlers/wakeupfd sont fermés/restaurés en
finally et le module est épinglé avec les programmes des deux gardes. Les
mesures restent présentes et la prochaine acquisition doit être réelle.


Sélecteur de canal123 : un socketUNIX accepté peut appartenir au namespace
réseau du client ; `unix_stream_connect` crée le nouveau socket depuis ce netns
puis lui copie l'adresse de l'écouteur. [SourceLinux af_unix.c](https://github.com/torvalds/linux/blob/master/net/unix/af_unix.c).
C'est une explication du flux, pas une attestation du noyau déployé.
Le banc épingle le seul runtime chaud : labelsfonction/instance/révision,
CID/image/PID/naissance/cgroup et inode netns, unique bind /protocol en lecture
seule issu du canal state/execution/INSTANCE/i-… ; il vérifie ces identités avant
chaque lecture candidate. Le FD réellement lu du principal fournit son inode,
cherché dans les tablesUNIX du contrôle et de ce seul runtime. L'inode, le chemin
exact control.sock et l'instance doivent tous concorder avant de lire la seule
ligne /started. Le reçu nomme le netns fournissant cette correspondance.
Les deux lectures de tables et les métadonnées restent bornées, sans accès à
un autre runtime, contenu d'en-tête ou corps ; les plafonds existants demeurent.


Le client préparatoire de lecteurs/budgets peut exécuter API12/05/06 isolément,
avec les mêmes fonctions/classes et corpus réels. Il ajoute zéro groupe qualifié
et ne remplace pas les douze groupes de la campagne finale ni les25communs frais.
Un prérequis absent reste un échec, sans skip ni variante simulée.
