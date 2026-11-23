# Préparation de la preuve des six instances de console

Contrat de [SLS-105](BACKLOG.md#sls-105), préalable à la campagne complète078.
La [qualification finale](evidence/execution-console-warmup-dev-2026-11-21.json) passe37groupes
au gel93bc53d,450sources6f09e175 et34captures inspectées.
Constat réel du21novembre2026 au gelfbafb11/286d296, imageb452 : execution-ui
passe son accueil/vide puis échoue « Six instances prêtes requises » après
publication. La suite termine1 à272groupes antérieurs validés ; ce passage
incomplet ne qualifie pas la campagne543. Rapport exact et capture vide archivés.

## Diagnostic et décision avant correction

Le client utilise encore POST deployments puis PUT artifact et attend six
instances sans promotion explicite dans ce groupe. Depuis008, upload et
promotion sont séparés. Hypothèse à recouper par les métadonnées natives de la
fonction et du candidat : un pilote ne commande pas le préchauffage. Ne pas
attribuer cet échec à l’admission ou au moteur sans cette observation.

Conserver le refus actuel, last_instances, UUID/hash/configurations, données
et reçus encore présents après la purge. Si un rejeu diagnostic est nécessaire,
créer la fixture par ses vrais flux et conserver les observations avant assertion,
sans fabriquer d’état SQL ni de réponse. Persister la conclusion et son motif
avant le code qui la corrige.

## Résultat exigé

Respecter la séparation upload/promotion, puis obtenir réellement six instances
ready distinctes,0,05CPU/128Mio chacune, sous les budgets1CPU/8192Mio/32instances.
Conserver pagination5+1, mesures Docker positives, focus, longs noms, états
réseau, extinction, journaux et reprise des douze groupes du client. Ne pas
réduire six à cinq ou supprimer la pagination pour passer la preuve.

Rejouer12groupes UI puis25communs, captures fraîches inspectées et nettoyage
natif de tous les objets propres ; original et artefacts antérieurs conservés.
La conservation des5982artefacts est d’abord instruite dans106. Les attentes
actualisées et nouveaux gestes sont documentés avant leur code. Aucun défaut
produit ni correction de produit n’est présumé ;078 reste ouvert.

## Cause recoupée et décision du21novembre2026

Le rapport execution-ui exactfed55b06343f0e95e5687f9fbb4a1a0526328d8c7bd3cfd91e42cfcc11550c0f
porte fonction4ba58f4d-d0c3-4953-a3a8-406de1b6f5c6,
révisiond9d07c5b-ecbe-449e-beb2-c84c5f0d4f29 et last_instances.total=0.
Le relevé natif1795267783292962291, conservé dans la
[preuve106](evidence/regression-artifact-cleanup-dev-2026-11-21.json),
retrouve ce même UUID, le code publié
5b5565898d16e050476b691dffcacec9c2fe506affb3f0f7030bc1997bf8a0d3,
active_revision_idNULL et first_promoted_atNULL. CPU0,05/mémoire128 et
min=max=concurrence6 sont bien ceux de la préparation. La révision est publiée
mais jamais promue. La purge106 ultérieure ne remet pas ces marqueurs à zéro.

Le code actuel execution.tick ne place dans son ensemble de minima que les
fonctions ayant une cible par défaut ; FUNCTION_VERSION_EXECUTION impose cette
règle. L’attente du banc était donc celle d’une cible qui n’existait pas. Ce
recoupement attribue le défaut au montage de qualification, sans modifier
le moteur ni sa politique d’admission.

Décision avant code : conserver la préparation API/packager originale, les
douze groupes et tous les gestes des facettes. Après PUT artifact, conserver
UUID de candidat, alias canonique et hash retournés. Relire catalogue, fonction
et instances ; attester pilote disponible, aucune promotion/aucune cible et
zéro instance. Puis un seul POST versions/HASH/promote, avec ETag de fonction
fraîchement lu, choisit explicitement cette cible. Cette mutation appartient à
la préparation API du groupe2 déjà spécifiée ; aucun geste UI de consultation
n’est remplacé par une API. Les réponses et observations sont persistées avant
assertions.

Après promotion, vérifier hash/alias choisis et cible observée, puis six UUID
d’instance distincts ready sur ce hash/alias, allocations50millions de nanos
CPU/128Mio, mesures Docker positives et rendu5+1. Ne pas réduire les six
instances, les budgets ou les douze scénarios. La qualification rejoue ensuite
les25communs, soit37groupes, sous budgets natifs32/1CPU/8192Mio, avec captures
nouvelles, code réellement déployé et purge publique106 contrôlée nativement.
L’ancien essai et sa restauration106 restent des époques distinctes, sans
groupe ajouté à ce replay.

## Qualification du21novembre2026

La [preuve37](evidence/execution-console-warmup-dev-2026-11-21.json) passe les douze groupes
exécution, puis8manuel/8public/9connexion, en série, au gel
93bc53da160a803123105b6e7421d1a91a5b1b8e.450sources, index
6f09e17542a3407a2493c217ae92aa633ffce42ffe4d43075261377c0dfacca1,
imageb452 inchangée ; aucun scénario ignoré.

Le hash5b556589 est publié pilote : catalogue disponible, aucune cible,
first_promoted_atNULL et zéro instance. Le POST explicite choisit ce hash
et son alias ; sa décision est confirmée par un seul audit natif
function.version_promote. Six UUID ready portent ce hash/alias, chacun
50millions nanosCPU/128Mio. Leurs créations suivent la promotion. Trois des
six mesures mémoire sont positives dans le relevé initial ; les autres
indisponibilités ne sont pas présentées comme des mesures. Le rendu compare
chaque valeur au relevé serveur, puis montre cinq cartes et la sixième sur la
page suivante, avec focus du titre. Les budgets restent32/1CPU/8192Mio.

Les douze groupes conservent réseau/chargement/reprise, extinction/recalage,
journaux expurgés/tronqués et texte HTML, démarrage Oui/Non/Non confirmé,
interruption réelle et mesures indisponibles, refus de session et suppression.
Le lecteur natif relève dix invocations terminales : sept succeeded, deux
failed et une rejected ; un HTTP503 métier reste succeeded. Le jeton est
révoqué et la purge publique106 confirme code/backings/montages/canaux/
conteneurs/réseaux absents et configuration/secrets vides.

Les34captures sont rouvertes individuellement pour105 :12exécution,16manuel,
6connexion. SHA/fraîcheur de phase recoupés,28déclarées et6PNG non déclarés
distingués. Les images montrent cinq cartes et le total6, sans capture de la
sixième : les assertions E2E portent cette dernière preuve. Noms/hash/logs
restent contenus à390px et les états sont lisibles, sans défaut bloquant.
Le manuel18chapitres/74paragraphes correspond à la source/rendu, marque à
trois blocs visible. Aucun produit/UI/manuel modifié.

Compteurs0,5982artefacts antérieurs exacts, dix migrations, intégrités/FK,
mêmes CID/images/naissances, fichiers officiels,38backends et4web servis sont
recoupés. Les trois notes sont conservées, sans adoption prétendue. Les
exécutables restent ceux du gel ; ces résultats documentaires sont postérieurs.

L’échec initialfed55b06 et la restauration106 restent distincts. Le collecteur
complémentaire refuse d’abord sa chaîne locale mal délimitée avant tout SSH,
puis deux lectures RO qui cherchent un nom d’audit incorrect ; le nom émis
function.version_promote est recoupé avant correction du lecteur. Une seule
trace détaillée est conservée dans le brut ; le premier code de sortie1 est
observé par l’opérateur sans stderr retenu, sans revendiquer deux traces
indépendantes. Ces diagnostics n’ont aucune mutation et ajoutent zéro groupe. SLS-105 est
terminée ; la campagne49/543 de078 et la clôture095 restent distinctes.

## Parité de collecte sur011 — SLS-141

Le [refus du socle courant](evidence/schedules-execution-ui-log-state-first-failed-dev-2026-11-23.json)
sur470b6ea/529sources/f016 atteint sixinstances et quatre groupesUI, puis attend
un ancien texte de journalvide absent du composant depuis072. Les douze groupes
du21novembre gardent leur imageb452 et ne qualifient pas les nouvelles branches
de collecte011. La réponse exacte du GET fautif n'a pas été conservée.

La correction décidée avant code conserve les douze scénarios, sixinstances,
pagination5+1, vrais gestes depuisl'accueil et tous les refus/nettoyages. Le
DTO du GET réellement émis par la page est conservé avant assertions sous une
projection sûre (UUID/état/statutHTTP/collecte/troncature/taille et SHA du buffer).
Le métier503 doit être succeeded/collected avec buffer vide ; le refus avant
dispatch not_started et la perte runtime unavailable sont recoupés dans leurs
scénarios existants, puis leurs libellés exacts sont vérifiés dans le mêmearticle.
Trois nouvellesJPEG de détail complètent les douze captures antérieures.

Rejouer12UI/25communs sur leur nouveau gel, sans groupes uniques ajoutés au
socle49, puis reprendre ce dernier depuis son premier prérequis. Les pilotes
exec et leurs délais sont ceux de141 ; les programmes/source/rapports sont
figés et les unités/PID/naissances/cgroups joints avant chaque phase suivante.
Cette correction ne change aucun composant de produit ni la qualification
historique105. Les états expirés/anciens conservent leurs preuves propres072.
