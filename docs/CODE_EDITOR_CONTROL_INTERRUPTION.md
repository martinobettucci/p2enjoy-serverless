# Brouillon et publication après interruption réelle du contrôle

Contrat de qualification des critères [SLS-070.3 et SLS-070.5](BACKLOG.md#sls-070),
persisté le 22 novembre 2026 avant le client et son opérateur. La continuité
sans redémarrage reste acquise par [ses 32 groupes](evidence/code-editor-publication-continuity-dev-2026-11-22.json).
Le [replay29](evidence/code-editor-control-interruption-dev-2026-11-22.json) est qualifié sur474sourcesef71eb7/API046.
Le premier passage reste [échoué](evidence/code-editor-control-interruption-window-failed-dev-2026-11-22.json),
zéro groupe ajouté ; [SLS-118](CODE_EDITOR_CONTROL_WINDOW.md) est close après
sa correction contractuelle et son replay réel. Le présent complément ne modifie aucun comportement utilisateur, schéma,
manuel, image produit, route ou configuration officielle.

## Décision et frontières observables

Exercer le véritable POST `code-draft/publish`, avec un UUID de déploiement
nouveau déclaré avant l'appel, puis deux SIGKILL physiques du même contrôle :
`receiving` et `validating`. L'ancien opérateur exige déjà un candidat préparé
avant l'armement ; il ne couvre donc pas directement ce POST qui prépare son
candidat après reconstruction. Un opérateur distinct arme sa garde avant
l'appel et accepte uniquement l'apparition du candidat précisément possédé.
L'ancien opérateur et ses preuves restent inchangés.

Le pipeline conserve `receiving` pendant l'extraction du ZIP entièrement reçu
(`Deployments.upload`, après fsync, avant sa transaction `validating`).
L'extraction est un vrai sous-processus ; retenir le seul thread principal
n'en suspend pas l'exécution. La première coupure prouve donc l'interruption
d'un candidat durable `receiving` dont l'archive complète est présente, sans
prétendre couper une réception partielle ni un extracteur encore vivant.
Ce choix satisfait le contrat [de reprise de l'éditeur](CONSOLE_EDITOR.md),
qui impose la reprise de ces deux états, sans imposer un upload partiel.
Les quatre connexions partielles et leur orphelin sont une autre preuve,
déjà qualifiée dans les 32 groupes précités.

Pour `receiving`, le paquet original utilise le handler `publication-recovery.cjs` du dépôt,
son marqueur JSON et 18 000 fichiers texte originaux déterministes, non vides,
dans un seul répertoire. Ce volume reste dans les limites qualifiées de
20 000 fichiers et de 256 Mio extraits. Il allonge le vrai travail d'extraction
sans fausse attente du serveur, sans substitution de dépendance et sans
garantir artificiellement l'acquisition de la fenêtre. Une fenêtre manquée
fait échouer l'essai ; aucun rejeu automatique ni coupure d'un état suivant.
Pour `validating`, publier d’abord un vrai pilote compact C à deux fichiers
et créer explicitement un nouveau brouillon sur cette base, après la preuve
de conservation et la publication de reprise B du grand brouillon. A reste
le défaut et son ETag est conservé. Ce brouillon C modifié utilise la vraie
attente d’import de8 000ms déjà bornée par le handler, pour observer un
validateur Docker vivant. Le détail et le motif sont dans le contrat118.

## Propriété et armement avant POST

Le namespace s'appelle `code-editor-control-interruption-` suivi des huit
premiers caractères hexadécimaux de l'UUID de campagne. Une seule fonction
vivante dans l'installation ; service et fonction sont reliés à ce namespace.
Le client journalise avant création noms, UUID, absence constatée et intentions.
L'opérateur recoupe les identifiants et la filiation en lecture seule.

Avant armement : aucun candidat actif, aucune réservation, instance, invocation
active, opération de fonction, validation Docker, canal ou bail de stockage.
Le nouvel UUID n'existe dans aucune ligne de déploiement ni dossier d'artefact.
Le brouillon exact existe, avec sa version, son acteur et sa base ; sa dernière
tentative éventuelle est terminale. Recouper la cible, les versions/révisions,
les archives, le hash de configuration, la ligne de brouillon chiffrée et les
empreintes de ses fichiers. Aucun contenu déchiffré ni secret au rapport.

Épingler l'API `sha256:04604089a8cb61d6015be0cde1671f29265878ff4f6f081509542ebc126055fc`,
son CID et sa génération de départ ; identifier le vrai PID Uvicorn par son
exécutable, cmdline, naissance et cgroup. Lire séparément l'image runtime de
validation et l'identité complète de `serverless-runtime-reference`.
Vérifier les SHA de configuration officielle, l'installation et les migrations.

Les programmes indépendants RESTORE et KILL_CONTROL sont copiés à l'octet
depuis `publication-recovery-operator.py`, sans import de ce programme à effets.
Leurs SHA exécutés restent respectivement
`d5fd248602d77a2928048f920c270b6b81b2ad549b0b567a1f07f11580a8459b`
et `19359bde933e5eebf10de80d04eb7585a7b2a81fabf28f05c7370b877571321b`.
Conserver le répertoire privé `/run/serverless-restore-publication-upload-UUID`,
le contrat d'identité, le verrou hérité et les reçus exacts de ces gardes.
Le timer indépendant est actif avant d'autoriser l'envoi du POST.

## Acquisition et coupure gardées

Après `armed`, le client ouvre le vrai POST HTTPS puis donne `observe` sur le
canal de l'opérateur. Celui-ci attend au plus 20 secondes cette commande, puis
au plus 20 secondes l'état ; les commandes externes sont bornées. Le timer
reste de 45 secondes à compter de l'armement. Aucune attente HTTP ou UI ne se
place entre la rétention du thread principal et l'instruction `interrupt`,
attendue au plus 8 secondes. La garde prime si l'acquisition ne tient pas
dans cette enveloppe ; un essai qui perd sa fenêtre n'est jamais qualifié.

Le sondage de phase est léger : lecture SQL de l'UUID exact, identité et état,
liaison atomique brouillon/candidat, réservation positive, lstat de la seule
archive possédée. Pas de hash de toutes les archives, d'intégrité complète ou
d'inventaire Docker général à chaque passage. Conserver les temps monotones,
le nombre de sondes et les états discriminants avant toute assertion.

Pour `receiving`, observer un fichier ordinaire non vide sous le dossier exact
du candidat, sans lien symbolique, déjà en mode `0444`. Le code ne pose ce mode
qu’après fin du flux, flush et fsync, avant extraction. Le recouper après
rétention du thread, puis vérifier le ZIP complet (répertoire central, compte
exact des fichiers (18 002pour receiving, deux pour validating) et CRC de chaque entrée), avec SHA et taille stables entre
les deux relevés. Un fichier encore inscriptible n’acquitte pas cette frontière.

Pour `validating`, identifier un seul
conteneur de validation vivant, de la vraie image runtime, de la même
installation, avec `/code` lié au chemin exact du candidat. Retenir ensuite
le thread principal par `NativeObserver`, puis recouper immédiatement le même
état durable et, pour `validating`, le même validateur encore vivant.
La complétude est attestée par ce point de cycle de vie et le contrôle ZIP ;
son SHA et sa taille sont conservés à cette frontière ;
cette mesure reste distincte de l'activité du sous-processus d'extraction.

Déclencher le programme KILL_CONTROL inchangé, garder le verrou jusqu'à la
jonction du client Docker, constater signal natif 9 par waitpid puis état
Docker arrêté/code 137. Le candidat n'est ni abandonné ni supprimé pour
fabriquer cette frontière. Dans la variante `validating`, perdre ensuite
réellement le helper par SIGKILL pour exercer la restitution indépendante.

## Reprise et conservation du brouillon

La garde relance le même CID et la même image, jamais un conteneur recréé.
Exiger sa santé, une nouvelle génération StartedAt/PID, la référence inchangée,
la fin du mutateur et celle du timer/service, MainPID à zéro. Pour la perte du
helper, exiger le reçu **indépendant**, `observer_gone`, la coupure liée et le
protocole qualifié par [SLS-110](PUBLICATION_RECOVERY_GUARD_REGRESSIONS.md) :
45 s de timer + 180 s d'alarme + 10 s de sonde, soit 235 s monotones au plus,
chaque sonde bornée à 10 s et au temps restant. Un secours nettoie sans
acquitter la preuve d'indépendance. Joindre aussi les transports SSH/HTTPS.

Après la santé retrouvée, lire le même UUID sans POST automatique : `failed`,
`control_interrupted`, aucune révision publiée, configuration du candidat
effacée, réservation nulle, dossier/archive, validateur et canaux absents.
La cible A et l'ETag, la configuration et les révisions antérieures sont
inchangés. Le brouillon conserve ID, version, base, acteur, handler, fichiers
et contenu chiffré ; seuls les champs de liaison à la tentative nouvellement
préparée diffèrent du relevé avant POST. Vérifier cette liaison avant et après
restart, sans effacement ou réécriture SQL.

Par API réelle puis depuis l'accueil de la console, rouvrir ce brouillon et
son fichier, vérifier la saisie enregistrée et la tentative échouée au même
UUID. Ordinateur 1 440 px pour `receiving`, mobile 390 px pour `validating` ;
captures JPEG de la tentative et du contenu, absence de débordement global,
navigation clavier et souris. Aucun accès UI pendant la suspension.
Le POST initial reste en échec de transport ou HTTP 5xx, avec son issue
conservée ; une réponse inconnue ne devient pas un succès déduit de la reprise.

Invoquer A sans tag après chaque restart. Déclencher ensuite une **nouvelle
action explicite**, nouvel UUID, sur le brouillon conservé, publier son pilote
et invoquer son hash ; A reste le défaut. Un dernier POST explicite sans
modification revalide le même hash/révision canonique et ne crée pas de version.
Il ne sert jamais à remplacer une publication échouée dans le rapport.

## Quatre groupes ciblés puis 25 communs frais

1. SSO réel depuis l'accueil, ressources originales, publication et promotion
   explicite de A, première invocation Docker et brouillon enregistré.
2. POST éditeur interrompu en `receiving`, restitution nominale, conservation
   native/API/UI sur ordinateur, invocation de A puis publication explicite du
   brouillon et invocation de son hash pilote B ; publication du pilote compact C
   puis abandon/création explicites du nouveau brouillon sur C.
3. POST éditeur interrompu en `validating`, perte du helper et restitution
   indépendante, mêmes preuves sur mobile, invocation de A puis nouveau pilote.
4. Revalidation sans changement, même hash/révision, six invocations distinctes,
   sept candidats exactement possédés (cinq publiés, deux échoués), quatre
   révisions et deux gardes/coupures ; conservations et repos natif recoupés.

Puis huit groupes manual-ui, huit public et neuf login-ui, frais, en série :
29 groupes au total, sans additionner les preuves historiques. Le prérequis
SSO et les contrôles statiques ne sont pas des groupes supplémentaires.
Toute erreur reste dans son rapport immuable, sans skip ou rejeu automatique.

La purge finale de la seule fonction et la révocation du jeton passent par
les API publiques ; supprimer ensuite les deux parents. Recouper physiquement
UUID, artefacts, stockage, baux, Docker, réseaux, canaux et réservations, ainsi
que l'absence de consommateurs et la jonction des processus/gardes.
Vérifier les sources synchronisées figées, 38 modules backend, quatre ressources
web no-store, dix migrations/intégrité/FK, manuel canonique 18/74 et son SHA,
budgets officiels, notes actives et proposées, référence et 5 982 originaux.
Ouvrir individuellement toutes les nouvelles captures, en conservant leurs
limites visuelles distinctes des observations DOM/HTTP/natives.

Le manuel et le produit restent inchangés. La clôture de 070.3/.5 exige cette
preuve positive et un rapprochement explicite avec leurs preuves déjà acquises
(conflits, saisie non enregistrée, CJS/ESM, import refusé, hash/déduplication).
Sans ces pièces, SLS-070 reste `[~]`.

## Premier passage échoué et état courant

Après le contrat3b0b520 poussé, le client et son opérateur distinct ont été
committés4a5d67d, synchronisés puis exécutés sur473sources figées. Le premier
[rouge scellé](evidence/code-editor-control-interruption-window-failed-dev-2026-11-22.json)
conserve receiving coupé137/repris et sa saisie relue API/UI, puis acquisition
validating expirée sans deuxième coupure. Deux groupes passent, zéro qualifié,
aucun commun ; trois handlers/deux captures desktop et purge physique recoupés.
Les programmes de garde restent inchangés, notes/config/référence/originaux
conservés. La durée système exacte de l’extraction reste inconnue.

Le client `node e2e/code-editor-control-interruption.mjs`, depuis la racine,
reçoit le SSO sur stdin privée en mémoire. Il utilise son packager et
`code-editor-control-interruption-operator.py` comme root sur le seul SPARK DEV.
L’opérateur lit les gardes par AST sans import, exige leurs SHA figés, recoupe
le validateur après ZIP/CRC et conserve les erreurs primaire/secours distinctes.
Le lecteur physique commun garde ses contrôles UUID/inventaire complet.

La décision118 prépare le replay4+25 sur deux bases réelles et les nouveaux
comptages ci-dessus. Après9a35d3d, les modes compact/grand, la création de
base C et les comptes/audits sont implémentés dans le client, syntaxes
contrôlées et index474sources. Le replay29 est désormais acquis ; produit, manuel et image restent inchangés.
Le rapprochement des critères dans CONSOLE_EDITOR clôt070.3/.5.

## Résultat du replay du22novembre2026

[Preuve29 et brut scellé](evidence/code-editor-control-interruption-dev-2026-11-22.json) :474sourcesef71eb7,
pilote47037 sortie0/joint, quatre ciblés puis25communs frais et26images ouvertes
individuellement. Deux coupures natives137/HTTP502 ;18 002entrées complètes en
receiving, deux en validating avec même validateur vivant après mesures.
Deux gardes et helpers terminés, aucun secours ; indépendante50,289497s/83sondes
dans235s. Mêmes ID/version/acteur/base/ciphertext dans chaque phase et cibleA
préservée. B/D explicites, C réellement publiée puis choisie comme nouvelle
base après abandon explicite ; déduplication D exacte. Six handlers, sept
candidats5pub/2failed, quatre révisions et audits2/2/1, purge physique/repos0.
38backend/quatreweb no-store/010/intégrités/FK, manuel18/74SHA8d2434cf, notes,
configuration, budgets, référence et5982originaux sont recoupés. Le premier
rouge et ses inconnues restent séparés ;118et070 clos après rapprochement.
