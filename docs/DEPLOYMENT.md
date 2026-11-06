# Révisions et adaptateur de déploiement

Contrat SLS-030, en cours de réalisation. Il complète PLATFORM et CONTROL.
Le checkpoint SLS-020 reste ouvert pour ses preuves administrateur ; les
parties indépendantes de cette unité progressent avec les mêmes composants
réels. Une qualification d'archive ou de CLI ne remplace pas les preuves
authentifiées d'upload, de droits et de publication.

## Outil et manifeste

L'adaptateur est une CLI Python 3.13 ou plus récente, dans `adapter/`, avec
PyYAML 6.0.3 verrouillé. ZIP, HTTP, empreintes et sélection des chemins utilisent
la bibliothèque standard. Le code Node est construit explicitement par son
projet avant packaging ; aucun plugin YAML, script npm ou commande de build
n'est exécuté par la CLI.
L'installation utilise un environnement Python avec pip et le fichier de
dépendances à empreintes, ou l'image Docker Python épinglée de l'adaptateur.
Sa cible de qualification ajoute les vrais fichiers de test à cette même
image ; elle exécute la CLI complète et conserve son rapport dans un montage
dédié. Les deux services Compose DEV lisent les fichiers officiels de cellule.

Le fichier par défaut est `serverless.yml`. `--config` sélectionne un autre
manifeste dans le même projet. `plan` valide et affiche noms, contrats,
noms de variables/secrets et diagnostics. `package` produit les archives et
un descripteur sans valeurs d'environnement. `deploy` résout de nouveau la
configuration en mémoire et effectue les opérations HTTPS sur un service
existant, désigné par UUID. Le jeton de plateforme est lu dans
`P2_SERVERLESS_TOKEN`, jamais dans un argument de commande ou un fichier
d'artefact. La cible HTTPS est fournie par `P2_SERVERLESS_URL` ; la CLI ne
désactive pas la vérification TLS et ne suit pas les redirections d'upload.

La CLI générale exige Read pour retrouver les fonctions par nom, puis Create
pour les fonctions nouvelles et Update pour les existantes. L'API conserve
également le parcours Create seul : créer un brouillon, puis sa première
révision à partir de l'identifiant retourné. Une CLI ne crée pas implicitement
un namespace ou un service depuis un jeton de service.

Les correspondances sont explicites :

| YAML | Contrat de plateforme |
| --- | --- |
| service, clés de functions | Nom de service vérifié, noms de fonctions et casse conservés |
| provider.name | p2enjoy, aws ou scaleway ; lecture du manifeste, aucune API du fournisseur appelée |
| runtime | Node 24 Linux x64 ; Node 20/22 exige `--runtime node24` explicite |
| handler | chemin/module.export, conservé et vérifié par Node |
| environment ou env | Héritage provider puis fonction, clés locales prioritaires |
| secret | Même héritage, transfert séparé du code et stockage chiffré |
| memorySize ou memoryLimit | Mémoire en Mio |
| timeout | Secondes, nombre ou chaîne suffixée s ; fractions conservées |
| minScale, maxScale | Nombre minimal et maximal d'instances |
| events.http | Méthode simple ou any, chemin relatif exact de la fonction |
| events.schedule | rate cron à cinq champs, enabled, UTC |
| p2enjoy | CPU, idle, concurrence, attente, stockage avec quotas explicites |
| package.patterns | Inclusions/exclusions ordonnées du contenu livré |

Deux alias présents au même niveau sont refusés. Un mapping environment/env
ou secret vide ou null conserve l'héritage ; une valeur null d'une clé retire
cette clé héritée. Une collision finale entre variable et secret est refusée.
Les valeurs sont des chaînes, sans conversion implicite d'un booléen YAML.
Seules les références `${env:NOM}` sont résolues, à partir des noms explicitement
déclarés ; les autres expressions sont refusées. Une variable manquante ne
devient pas une chaîne vide.

YAML est lu en mode sûr, avec refus des clés dupliquées, ancres, aliases et
tags spécifiques. Le manifeste est limité à 1 Mio. Les champs inconnus
susceptibles de modifier le déploiement sont refusés avant tout upload.
Les plugins et les options d'identification du fournisseur sont énumérés
comme non exécutés ; leurs valeurs ne sont pas affichées ou transmises.
`configValidationMode: off` ne désactive pas les validations de l'adaptateur.
Les options Scaleway `custom_domains`, `httpOption`, `privacy` ne sont pas
appliquées silencieusement : leur présence exige `--accept-provider-differences`
après lecture du plan, ou une adaptation explicite du manifeste. L'option
accepte uniquement ces différences connues, qui restent affichées avant upload.
L'authentification par jeton reste obligatoire pour les invocations.

Les méthodes initiales sont GET, POST, PUT, PATCH, DELETE, HEAD et OPTIONS.
Un chemin HTTP est relatif au point d'invocation de la fonction ; pas de
paramètres de chemin, wildcard ou intégration API Gateway avancée dans cette
unité. En l'absence d'événement HTTP, la fonction possède son endpoint implicite.
Les crons sont enregistrés comme contrat de révision ; leur déclenchement
effectif relève de SLS-050.

## Application de qualification

`qualification/serverless.platform.yml` réutilise les douze handlers du dépôt
avec variables publiques, secrets et quotas déclarés explicitement. Son
packaging livre `src/` et le package nécessaire au chargement Node. Les noms
d'identifiants et les sélections d'environnement propres à l'exécuteur de
référence restent dans son manifeste `serverless.yml` ; ils ne sont pas des
UUID de plateforme. La plateforme attribue et conserve ses UUID par fonction.

Des variantes originales sous `qualification/artifacts/` éprouvent ESM,
CommonJS, une véritable dépendance packagée, un export absent, une dépendance
absente, une exception et un blocage à l'import. Les variantes défaillantes
contiennent réellement ces défauts ; elles n'imitent aucune dépendance externe.

## Artefact

Une archive ZIP correspond au code d'une révision de fonction. Le même code
de service peut être empaqueté pour plusieurs fonctions. Les dépendances
nécessaires doivent être déjà présentes ou bundlées ; aucune réinstallation
implicite ne réintroduit les fichiers exclus par le projet.

Les motifs de packaging acceptent `*`, `?`, classes de caractères et `**`,
sur des chemins POSIX relatifs. Ils sont appliqués dans l'ordre, avec `!` pour
exclure. Les extensions de glob non prises en charge sont refusées. La sélection
commence par les fichiers ordinaires du projet. `.git`, `.aws`, les `.env*`,
les sorties `.serverless`/`.serverless-p2`, les manifestes serverless et les
liens sont exclus ou refusés explicitement. Ces exclusions de chemins ne
prétendent pas détecter une valeur confidentielle codée dans un source.

Limites initiales : 64 Mio de ZIP, 256 Mio décompressés, 20 000 fichiers,
512 octets par chemin et 64 Mio par fichier. Rejet des liens, fichiers
spéciaux, ZIP chiffrés, méthodes de compression hors stored/deflate, chemins
absolus, segments . ou .., antislash, caractères de contrôle et doublons
après normalisation. Les collisions fichier/répertoire sont refusées.
La limite réelle d'extraction est recomptée pendant la lecture, même si les
tailles annoncées sont mensongères. Les permissions finales ne conservent
que le caractère exécutable éventuel ; aucun bit privilégié n'est repris.

L'entrée serveur accepte ZIP classique monovolume, STORED ou DEFLATE, avec
ou sans data descriptor (signature facultative). ZIP64, préfixe exécutable,
concaténation et enregistrements supplémentaires sont refusés explicitement :
les limites du produit et le packager fourni n'en ont pas besoin. Le répertoire
central est parcouru en flux avant toute extraction ; ses 16 Mio maximum et
ses 20 000 entrées incluent les répertoires explicites. Au plus 20 000 répertoires
explicites ou implicites peuvent être créés. Les noms UTF-8 ou CP437 sont conservés ; aucune
normalisation silencieuse d'un chemin interdit. Les composants suivent aussi
la borne Linux de 255 octets.

Les extras admis sont les timestamps, UID/GID et métadonnées NTFS ignorés,
ainsi que le chemin Unicode Info-ZIP uniquement lorsqu'il confirme exactement
le nom principal et son CRC. Un extra inconnu ou un nom alternatif contradictoire
est refusé. Les en-têtes locaux, centraux et descripteurs doivent être cohérents,
et les zones de données ne doivent ni se chevaucher ni laisser de contenu
intermédiaire non décrit.

Le serveur lit les flux STORED/DEFLATE avec struct et zlib, sans extractall ni
ZipExtFile : celui-ci peut tronquer aux tailles annoncées avant son CRC et
ne suffit pas à prouver une taille réelle mensongère. Les compteurs, CRC et
fin de flux sont vérifiés avant conservation de chaque fichier. Les écritures
utilisent des descripteurs de répertoire sans suivre de liens. Une destination
préexistante est refusée ; un répertoire temporaire privé est publié par
renameat2 NOREPLACE sous Linux après succès. Un échec supprime uniquement ce
candidat et conserve l'ancienne destination. Les fichiers sont readonly,
avec exécution conservée lorsqu'elle était demandée ; les répertoires sont 0555.
La synchronisation du parent fait partie du succès : si elle échoue après
le renommage, seule la nouvelle destination, identifiée par son inode, est
retirée. Les répertoires de travail appartiennent au contrôle et restent privés ;
les fonctions n'y ont jamais de montage en écriture. Une interruption brutale
du processus laisse éventuellement un candidat privé à réconcilier au démarrage,
comme les uploads interrompus ; elle ne produit pas un succès de publication.

L'extracteur est d'abord qualifié comme vraie CLI dans une image Python épinglée,
avec le packager et le validateur Node réels. Son intégration HTTP et la
réservation globale restent dans le parcours de publication décrit ci-dessous.
Le pilote E2E s'exécute sur le SPARK et appelle l'image de la CLI pour chaque
archive. Il crée de vrais ZIP, provoque des erreurs de disque dans un tmpfs
limité et exerce une collision concurrente de destination. Aucune dépendance
ou primitive du système n'est substituée.
Sa charge de stockage compte les fichiers et répertoires par blocs logiques
de 4 Kio, en plus du ZIP ; l'admission conservera la marge libre de 1 Gio.

L'inventaire enregistré comprend chemins, tailles et SHA256 ; la révision
conserve aussi l'empreinte du ZIP, runtime, architecture, handler et image
Node utilisés. Le code est monté en lecture seule lors de son utilisation.
Les valeurs de configuration sont transférées dans la requête de préparation,
puis chiffrées en base ; elles ne font pas partie du ZIP ni de son inventaire.

## Préparation, validation et publication

1. `POST /api/functions/{id}/deployments` prépare un candidat : configuration
   complète, variables/secrets désirés et événements. `If-Match` est obligatoire
   et porte updated_at de la fonction. Le candidat expire après une heure.
2. `PUT /api/deployments/{id}/artifact` envoie le ZIP brut en application/zip.
   Le contrôle vérifie l'identité avant de lire le flux, le borne, extrait
   dans un répertoire neuf et lance la validation Docker.
3. Après validation, une transaction courte revérifie droits, état de la
   fonction et version attendue, puis publie la révision et sa configuration.
   Un conflit conserve intégralement la fonction précédemment active.

Le candidat conserve aussi la version du service utilisée pour ses variables
communes : une modification de cette configuration pendant la validation
refuse la publication. La configuration de fonction fournie par un déploiement
est complète et remplace les valeurs de ce niveau, y compris les anciens
secrets absents du manifeste. La console conserve ses mutations partielles
documentées dans CONTROL.

Create autorise la première révision d'un brouillon sans révision publiée ;
Update autorise les suivantes. Le candidat appartient à son créateur : seul
ce créateur encore autorisé, ou un administrateur, peut envoyer son artefact.
Les candidats simultanés d'une même fonction ne peuvent tous deux publier
sur la même version. Révocation du jeton, suppression ou modification pendant
la validation interdisent sa publication. Les candidats échoués gardent un
diagnostic borné, sans code ni secret dans les réponses d'erreur.

Les déploiements sont atomiques par fonction. La CLI présente le résultat de
chaque fonction d'un service et échoue si l'une échoue ; elle ne promet pas
une transaction globale sur toutes les fonctions. Une fonction nouvellement
créée peut rester brouillon après un upload refusé.

Une seule extraction/validation est admise à la fois sur le SPARK initial ;
la suivante reçoit 429 et Retry-After. Les candidats en attente sont bornés
à 64 au total et huit par fonction. Le stockage d'artefacts dispose d'un
budget global de 4096 Mio par défaut, ajustable via la cellule sous
SERVERLESS_ARTIFACT_BUDGET_MIB ; réservation avant extraction et restitution
après échec. Les contrôles de disque gardent une marge libre de 1 Gio.
Le contrôle réconcilie les seuls candidats et conteneurs portant ses labels
après arrêt, sans publier un résultat interrompu.

La révision fige code, handler, runtime, routes et schedules. Les ressources,
variables et secrets courants restent configurables ; changer le handler ou
runtime d'une fonction ayant du code passe par un nouveau déploiement.
Un rollback restaure une révision de code validée et ses événements, conserve
les ressources et les valeurs de configuration courantes et garde l'UUID et
les volumes. Il ne restaure pas d'anciens secrets.

`GET /api/functions/{id}/revisions` fournit l'historique selon Read.
`POST /api/functions/{id}/rollback` exige Update et If-Match.
Les révisions inactives et non utilisées peuvent être supprimées explicitement
avec Update ; vingt révisions conservées par fonction constituent la limite
initiale. La publication refuse de dépasser ce plafond sans purger silencieusement
l'historique.

## Chargeur et validation Docker

Le même chargeur est utilisé pour valider puis invoquer. Un chemin avec
extension .js/.cjs/.mjs est exact ; sans extension, une seule correspondance
parmi ces trois extensions est requise. Les ambiguïtés sont refusées.
L'import dynamique respecte le package Node. Un export nommé ESM ou une
propriété propre de module.exports CommonJS doit être callable ; une
propriété héritée ne constitue pas un handler.

La validation exécute donc du code au chargement. Elle reçoit les véritables
variables/secrets applicatifs désirés, sans configuration ambiante du contrôle.
Elle s'exécute sans réseau et sans volume métier, avec /tmp borné, code readonly,
capabilities retirées, no-new-privileges, 512 Mio, 0,25 CPU et 64 PIDs.
Un import qui exige une connexion réseau doit déplacer cette opération dans
le handler. Aucune donnée factice n'est fournie pour rendre un import valide.

Le contrôle impose une échéance externe de quinze secondes comprenant
démarrage et import ; son expiration détruit le conteneur et ses descendants.
Le résultat de validation passe par un canal séparé des logs applicatifs et
requiert un message explicite du chargeur : un exit(0) du module ne vaut pas
validation. Les logs sont bornés, et les valeurs de secrets connues sont
expurgées. Le conteneur ne possède ni socket Docker, ni base du contrôle,
ni secret de SSO. Le socket local Docker appartient au contrôle uniquement.

Le transport choisi est HTTP sur un socket Unix privé par conteneur, créé par
le contrôle dans un répertoire de protocole distinct du code. Ce répertoire
est monté readonly : le runtime peut se connecter au socket, mais ne peut pas
y écrire des fichiers qui échapperaient aux quotas. Il fonctionne avec le contrôle en
réseau hôte et les fonctions en réseau Docker isolé, sans dépendre du routage
des adresses de bridge. Les bind mounts utilisent les chemins du SPARK vus
par le daemon ; leur correspondance avec `/state` est explicite.

Le superviseur Node ne charge pas le code applicatif. Il retire une seule fois
sa configuration par GET, lance un enfant avec canal IPC, puis remet son résultat
par POST. Le contrôle expose aussi un statut sans configuration. Les requêtes
et connexions sont bornées et expirent sous la même échéance globale.
stdout/stderr de l'enfant sont consommés et bornés à 64 Kio en mémoire ; ils
ne constituent jamais le protocole de résultat. Les logs Docker de ce conteneur
sont désactivés pour ne pas persister les valeurs applicatives brutes. Le
contrôle expurge les valeurs de secrets avant d'enregistrer ces diagnostics.
Une sortie sans message de chargement réussi échoue, même avec le code zéro.

Les variables applicatives sont transmises par le socket, puis installées dans
l'enfant après son bootstrap. Elles ne deviennent ni la configuration du
superviseur, ni des arguments de commande, ni l'environnement enregistré par
Docker. Le chargeur refuse les chemins ambigus, liens et sorties de l'archive.
L'interopérabilité CommonJS utilise l'export `module.exports` identifié par
Node 24 et le format constaté par son hook de chargement ; un objet default
ESM n'est pas assimilé à un module CommonJS. Un résultat d'import qui n'est
pas un namespace Node est refusé, notamment si un export `then` détourne la
résolution de Promise. Les variables interprétées au démarrage de Node sont
lisibles comme valeurs applicatives, mais n'altèrent pas rétroactivement son
bootstrap. L'IPC sépare les logs du protocole ; il ne constitue pas une
attestation contre un module qui falsifierait délibérément son propre processus.

Le pilote Python utilise l'API HTTP locale Docker, sans shell ni nouvelle
dépendance. Il résout une image existante en identifiant immuable, crée un
conteneur étiqueté, attend le résultat sous une échéance externe puis supprime
le conteneur avec ses descendants avant de rendre la validation. Une erreur
de nettoyage est un échec, jamais une validation réussie. Les scénarios de
chargement autonomes utilisent exactement ce pilote et ce runtime déployés ;
ils ne prouvent pas encore les autorisations de publication de l'API.

## Preuves

Les CLI sont exécutées comme de véritables processus sur les fichiers du
service témoin. L'upload et la publication passent par la véritable API et
les jetons issus du parcours SSO. Archives malformées, dépendance absente,
import bloqué, sortie prématurée, surcharge, révocation et conflit sont
exercés avec leurs causes réelles. Un refus laisse le précédent état intact.
Les E2E HTTP du moteur éprouveront les dépendances chargées pendant l'invocation,
que la validation de l'import ne suffit pas à prouver.

Références primaires : [PyYAML](https://pypi.org/project/PyYAML/),
[glob pathlib](https://docs.python.org/3.14/library/pathlib.html#pathlib.PurePath.full_match),
[API Docker](https://docs.docker.com/reference/api/engine/),
[interopérabilité Node](https://github.com/nodejs/node/blob/v24.x/doc/api/esm.md).
Le format du module est constaté via les
[hooks de chargement Node](https://github.com/nodejs/node/blob/v24.x/doc/api/module.md#moduleregisterhooksoptions).
