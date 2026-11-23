# Diagnostic réel du débit d’invocation

Contrat de SLS-133.2, décidé le22novembre2026 avant code. Complément de
RETENTION_SCHEMA_011 et INVOCATION_SOURCE_RETENTION_VOLUME. Le rouge9406 reste
inchangé ; aucun résultat de ce diagnostic ne valide le nominal10001HTTP+1cron.

## Question et données disponibles

La mesureRO de l’original restauré contient2999invocations, aucun événement du
journal et au plus248appels pour une fonction. La sélection d’attente utilise
invocation_function ; les recherches d’expiration et de borne numérique
parcourent les métadonnées, avec un tri temporaire pour cette dernière. Ce sont
des coûts réels de cette base, sans attribution suffisante du ralentissement
observé à8511appels dans l’installation temporaire disparue. Le corpus saturé
du rouge n’a pas été sauvegardé ; il n’est pas reconstruit depuis son JSON.

## Passage SQL historique f73

Ajouter au client réel existant le seul mode explicite --production-profile.
Il conserve accueil/SSO, installation isolée f73/runtime réels, garde2700,
deux fonctions chaudes et deux flux sériels HTTP indépendants. Chaque fonction
reçoit3000appels, soit6000réponses originales, dont corps, UUID, séquence et hash
sont vérifiés. Les limites métier, budgets et cadence ne sont pas changés.
Le futur créneau du témoin demeure planifié, mais le diagnostic purge et
restitue avant lui : aucun cron n’est attribué à ce passage.

Aux jalons du premier flux256/1024/2048, puis après les6000réponses, un opérateur
RO mesure le vrai contrôle temporaire. Les nombres réellement présents sont
conservés : le second flux peut progresser pendant un prélèvement. L’opérateur
exige le work/campaign reconnu, mode instance-limit sans replay, image/CID,
répertoires/configuration et namespace/fonctions exacts du passage. Il lit les
deux tables de configuration du banc pour l’identité, jamais les valeurs
de secrets. Son programme ne modifie aucune ligne ni index et n’appelle aucune
maintenance directement. Aucun remplacement de réponse, clock ou dépendance.

Dans le Python/SQLite du conteneur réellement exécuté : connexionmodeRO,
query_only, transaction de lecture cohérente, schéma011 exact et inventaire des
deux fonctions. Recueillir les horodatages réellement enregistrés, plansEQP,
tempsmonotone/CPU du processus de mesure, pasVDBE àquantum100 et nombre de
résultats pour les requêtes exactes d’admission, expiration et candidats aux
deux rétentions. Chaque SELECT a une limite d’instructions explicite et reste
RO. Comparer des mesures successives authentiques, jamais des corpus reconstruits
par suppression ou insertion. Conserver les deux répétitions chaudes et la
première séparément, sans prétendre reproduire son état de cache initial.

Les intervalles created→queued→admitted→dispatched→completed sont conservés
comme durées de phases, pas comme tempsCPU du handler. Les périodes de mesure
et leur effet possible sur la charge sont nommés. Les écritures/COMMIT/fsync
ne sont pas quantifiées par des SELECTRO ; si cette piste reste nécessaire,
une observationnative distincte du PID/naissance/cgroup réellement recoupés sera
contractualisée avant code. Les anciens compteurs de PID nonattribués sont exclus.

## Résultat et nettoyage

Le rapport porte production-profile et zéro groupe de qualification. Les deux
contrôles diagnostiques (production avec relevés, puis purge/restitution) ne
deviennent pas les trois groupes du nominal. RapportUUID et stdout distincts ;
un wrapper gèle sources/image/installation avant/après et joint le vrai client.
Il n’y a aucun rejeu automatique. Toute marge/frontière manquée reste rouge.

La clôture réutilise exactement le chemin existant : min0/idle0, disparition des
instances, révocation du jeton, deux purges publiques, retraitservice/namespace,
contrôle physique puis restitution nominale, driver/timer/service joints.
Original011/collection, référence, configuration et5982artefacts sont recoupés.
Les modes nominaux et les quatre diagnostics d’observateur gardent leurs
options, seuils et assertions. Le module de clôture partagé évite de recopier
une version affaiblie du nettoyage.

Une mesure concluante motive une décision de correction avant code produit.
Le profil ne clôt pas133 : nominal3, régressions affectées et campagnescomplètes
demeurent nécessaires.


## Portée du compteur CLI à corriger — SLS-133.7

La synthèse du client nomme real_http_handlers le nombre d’éléments du tableau
responses, qui contient les réponses de charge. Le vrai command-timeout
078126da affiche0 pour ce champ, alors que son reçu natif conserve une
invocation HTTP et une planifiée réellement démarrées. Cette synthèse ne doit
pas présenter un compteur de réponses comme un nombre de démarrages observés.
La clarification sera décidée et codée avec le profilage productif133.6, puis
éprouvée sur ses vrais passages. Les rapports passés et leur comptage de groupes
restent intacts ; ce libellé n’est pas utilisé pour qualifier les pannes134.


## Profilage du coût d’invocation courant — SLS-133.6

Décision avant code : conserver la voie historique ci-dessus et ajouter deux
options uniques au client existant : --invocation-cost-profile=smoke et
--invocation-cost-profile=full, plus parser-loss pour la seule preuve de reprise
décrite ci-dessous. Elles correspondent à deux campagnes distinctes,
avec deux puis6000 réponses HTTP validées (une puis3000 par fonction). Le passage
court doit prouver fermeture, validité des statistiques et restitution avant
le lancement du plein. Le nom décrit la mesure ; l’environnement reste DEV.
Le nominal10001HTTP+cron et l’ancienne option --production-profile gardent leurs
valeurs, délais et portée. Aucune image applicative ou dépendance ne change.

Le helper n’accepte cette option que pour instance-limit, garde2700 et image
originale f016 immuable, sans replay ni option historique. Mode inconnu,
combinaison, durée incorrecte, autre image ou autre mode sont refusés avant
répertoire/journal/garde/arrêt. Les durées900/120/60 existantes sont préservées.
La fenêtreW30–35min, margeW−60 et le refus de toute frontière manquée restent
inchangés ; aucun débit garanti ne découle de la limite6000.

Le nouveau module d’infrastructure e2e/invocation_cost_profile.py est gelé dans
la fenêtre avec son SHA, le helper et control_database avant armement. Les
opérations et la restauration indépendante utilisent cette copie reconnue.
L’index commun compte alors528 sources. Les preuves527 restent dans leur époque,
sans réétiquetage. Le module n’importe aucun handler applicatif et ne remplace
aucune fonction, connexion, résultat, dépendance, signal ou horloge.

### Démarrage et identité du seul clone

La définition Compose officielle, le Dockerfile, les42backend et quatreweb,
les variables/secrets/routes, quotas et la référence restent identiques. La
seule définition éphémère reçoit la commande python -B -m cProfile -o
/qualification-profile/control.pstats -m uvicorn, suivie des mêmes arguments
applicatifs du CMD f016. init=true, racineRO, /tmp16Mio et toutes les limites
existantes sont conservés.

La sortie est work/invocation-cost-profile, hors des trois répertoires officiels
à permuter. Son intention est journalisée avant création ; dossier canonique
sans lien, propriétaire1001/groupe1001/mode700 et identitédev/inode conservés.
Seul le clone reçoit son bindRW vers /qualification-profile. Le fichierpstats
doit être absent au départ et juste avant fermeture ; aucune statistique
préexistante n’est acceptée. Ce choix permet l’écriture sans rendre la racine
ou l’état officiel plus permissifs.

Au démarrage puis avant fermeture : CID/image/projet/montages/commande exacts,
manifestes42+4 et Python3.14/Uvicorn0.54 recoupés ; cProfile/_lsprof sont ceux du
runtime. Le PID State.Pid est celui de Tini. Parcourir ses descendants de façon
bornée et sélectionner l’unique Python de la commande cProfile exacte, avec
naissance/cgroup stables. Lire NSpid dans son vrai status pour relier le PID
hôte au PID affiché par Uvicorn. Aucune mesureCPU du Tini n’est attribuée à
l’API ; aucun ptrace ou import de handler n’est nécessaire à cette identité.

### Charge et mesures SQL/client

Même SSO réel, deux publications originales, minima chauds, droits Read de
service et appels Docker/runtime/agent publics. Les fonctions et le service
sont nommés selon l’analyse de coût. Le témoin futur reste planifié ; aucun tir
n’est attendu et la purge/restitution doit finir avantW. Le passage court
attend deux invocationsHTTP réussies ; le plein6000, aucune autre invocation.

Le plein conserve les quatre relevés256/1024/2048/complete ; les trois premiers
sont déclenchés par le premier flux, le second peut progresser pendant le relevé.
Le court prend un seul relevéfinal2. L’opérateurSQL possède une option explicite
--current-cost-profile : f016 et contexteprofilé reconnus, même lectureRO/query_only,
transaction cohérente et seuilVDBE. Sa requête logs_expiration utilise exactement
la formulation actuelle service_log_policies CROSS JOIN execution_log_events et
ses mêmes paramètres/prédicats/ordre/LIMIT ; l’ancien JOIN f73 reste dans sa voie.
Les autres requêtes et limites restent identiques. Les valeurs observées sont
conservées, sans fabriquer des cardinalités de jalon. Les coûts de ce processus
RO ne deviennent pas des coûts productifs du processus API.

Pour chaque réponse de la nouvelle voie : horodatages monotones avantPOST,
retour de awaitpost et fin des assertions/validationJSON, plus les dateswall_ms
réelles. Les nanosecondes sont des chaînes décimales et leurs différences sont
prises dans le seul domaine client. Le retourAPIResponse est une réponse
disponible pour le client, pas un instant isolé d’arrivée des headers. Ces
intervalles composites ne sont pas nommés réseau pur. Les UUID, séquences,
corps, hashes de code et compteurs natifs restent les vrais oracles.

### Fermeture et statistiques fraîches

Après minima0/idle0, zéro instance/conteneur, révocation, deux purges publiques,
retrait service/namespace et contrôle physique, le client demande l’opération
finish-invocation-cost-profile au helper avant la restitution habituelle.
L’opération vérifie sa fenêtre reconnue, exactement deux UUID de fonctions,
les2/6000 invocationsHTTP réellement réussies, aucune activité ni tir, W−60 et
identité/commande du même clone. Elle ne modifie aucune table.

Ouvrir un pidfd de l’API identifiée, recouper naissance/commande/cgroup/CID puis
envoyer un seul SIGINT par ce pidfd. Attendre sa terminaison native au plus15s,
mesurée ; les inspectionsDocker et la collecte qui suivent gardent leurs bornes
opérateur distinctes. Constater ensuite le conteneur sorti, le pidfd fermé et
le code réel du processus cProfile. Le succès exige séparément les marqueurs
Uvicorn de démarrage et shutdown applicatif complets, puis Finished server
process pour le bon NSpid. Refuser traceback, échec de lifespan/shutdown,
timeoutgraceful ou erreur de fermeture. cProfile peut absorber SystemExit :
son code0 ou un pstats valide ne prouvent pas seuls la réussite applicative.

Le fichier nouvellement apparu doit être régulier, sans lien, nlink1, de la
bonne identité et≤32Mio. Conserver absenceavant, stataprès, SHA et horodatages
natifs en chaînes. Le brut n’entre jamais dans Git ou un rapport public.
La lecturepstats se fait dans un conteneur éphémère de la même imagef016 et du
même Python3.14, après l’arrêt de l’API. Aucun parseur hôte n’est substitué.

### Propriété et retrait du parser

Nom serverless-invocation-cost-parser-UUID, label propre
tech.p2enjoy.qualification.invocation-cost-profile=UUID ; aucun label installation
ni faux kind validation/runtime. Le nettoyage des consommateurs exige l’image
runtime et ne peut pas posséder ce conteneur contrôle. Le journal existant porte
l’intention complète avant dockercreate (nom, image, commande, montage, dossier,
id=null), puis le CID exact avant dockerstart. Si le pilote meurt entre ces
étapes, la restauration retrouve seulement ce nom et vérifie toute l’identité
avant retrait parCID ; un objet non reconnu reste un refus de propriété.

Parser sans réseau ni variable/secrets officiels, racineRO, capacités retirées,
no-new-privileges, mémoire256Mio, CPU0,5 et pids32. Seul le dossierpstats est
montéRO ; aucun état, canal ni socketDocker n’est monté. Son vrai SIGALRM20
borne la lecture/projection ; la commande opérateur conserve son timeout40.
Capturer séparément retourCLI et State.ExitCode réel, exiger0 et état sorti.
Le finally retire le seulCID reconnu et confirme son absence. La restauration
indépendante effectue ce même retrait avant le nettoyage applicatif. Aucun
nouveau framework de processus ou service permanent n’est introduit.

Le parser utilise pstats.Stats du runtime sans arrondir par get_stats_profile.
Conserver toutes les fonctions et liens de callers : fichier/ligne/nom, appels
primitifs/totaux et temps exclusif/cumulé. La formeStats est cc,nc,tt,ct ; la
forme des callers cProfile est nc,cc,tt,ct, recoupée dans pstats du runtime.
Maximum20000 fonctions/100000 liens et projectionJSON≤16Mio ; un dépassement
refuse sans fabriquer ni tronquer la preuve. Conserver version/SHA des modules,
Python/SQLite et du brut ; le SHA du fichier doit être égal avant/après et dans
le parser. Référence primaire : https://github.com/python/cpython/blob/3.14/Lib/pstats.py .

Après validation et retrait du parser, sceller dossierroot700/fichierroot400,
fsync et reçuJSONroot600. Le work de qualification conserve ce brut hors des
répertoires remplacés. Le rapport public ne porte que la projection et ses
identités/empreintes, jamais arguments/locals/valeursSQL/headers/secrets.
Une erreur de collecte reste rouge ; elle ne crée pas de statistiques pendant
restore et ne bloque pas la restitution normale des originaux. Les échecs de
propriété du seul parser demeurent des refus, pas des effacements permissifs.

### Périmètre des mesures, compteur et qualification

cProfile utilise son timer réel par défaut, pasCPU. Le profil couvre le thread
principal et tout son cycle : préparation, appels, mesures, purges et shutdown.
Sa surcharge est déclarée. Les cumtime se chevauchent ; leur somme n’est pas un
CPUtotal et les résumptions de coroutine ne sont pas des invocations. Le temps
du générateur Database.transaction n’inclut pas automatiquement le corpsyieldé.
Les Cexecute productifs et leurs callers viennent de cette API ; les SELECTRO
restent séparés. Les données réelles décideront de ce qui est établi en133.2.

Pour133.7, le seul compteur responses.length s’appelle ordinary_http_responses
dans la synthèseCLI. Il ne devient jamais un nombre de handlers démarrés ;
aucun total natif n’est déduit quand il n’a pas été observé. Les anciens rapports
restent intacts. Les assertions et les comptages de groupes restent identiques.

Qualification : refusCLI sans mutation des combinaisons interdites ; vrai
passage smoke2 avec un relevéRO, pstats frais/lisibles et toutes les fermetures ;
puis full6000 avec quatre relevés et compteurs/timings recoupés. Nettoyage public
et restitution nominale, guard/driver/acteurs/parser absents, originaux011,
collection/config/référence/5982 et huitcompteurs0. Le wrapper externe est une
unité localeexec avec cgroup et timeout, retourcontrôleur capturé puis clôture
externe avant tout autre test. Aucune exception, horloge ou dépendance simulée,
aucun retry ou replay automatique. Les modes historiques touchés ont leur
régression nommée ; le nominal10001+cron et les campagnes produit demeurent
indépendants et ne sont pas qualifiés par ce diagnostic.


### Perte réelle après création du parser — SLS-133.6

Le parser est une ressource durable nouvelle : sa reprise doit être éprouvée,
pas seulement relue. Le mode explicite --invocation-cost-profile=parser-loss
reprend la charge courte2, son relevéRO final et le vrai shutdown. Il n’est
ni le smoke réussi de lisibilité ni le plein6000. La fenêtre reste f016/2700,
sans modifier le timer ni aucun environnement officiel.

Après dockercreate, identité vérifiée et CID journalisé, avant dockerstart,
le helper émet l’événement du parser réellement créé puis s’arrête lui-même
par le vrai SIGSTOP. La source, le CID, le nom/label, l’étatcreated et le reçu
durable sont recoupés ; aucun faux résultat n’est renvoyé. Le client demande
ensuite restore par la voie indépendante existante, qui tue le seul pilote
reconnu et reprend depuis le journal gelé. Ce n’est pas une expiration2700.

La restauration retire le seulCID du parser après vérification complète,
puis le clone et les ressources de sa fenêtre, et restitue les mêmes originaux.
Le fichierpstats déjà écrit peut être scellé comme diagnostic existant après
retrait du parser ; aucune lecturepstats réussie ni statistique complète n’est
revendiquée dans ce mode. Un fichier manquant ou inconnu n’est pas fabriqué.
Deux groupes support : préparation réelle2, puis perte/retrait/restauration
indépendante et jonctions. Parser absent, pilote nonvivant, gardes et unités
terminées, configuration/collection/5982 et huitcompteurs0 sont recoupés.

Exécuter les refus avant mutation, le smoke2 normal, cette perte, puis le plein
6000. Régression nommée du défaut sansoption : release/EOF sur le helper final,
même image et restitution sans profilage. Les autres campagnes produit et
consommateurs gardent leurs obligations propres. Aucun retry automatique,
aucun processus ou signal substitué n’est ajouté pour qualifier cette reprise.
