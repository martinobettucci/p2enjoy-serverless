# Rétention réelle des tirs planifiés

Contrat de preuve de [SLS-078](BACKLOG.md#sls-078), complément de
[SCHEDULES](SCHEDULES.md#réalisation-du-moteur-et-migration-009). DEV uniquement,
preuves sérielles, aucune date ni ligne métier fabriquée, aucune horloge remplacée.

## Capture authentique avant vieillissement

Le mode terminal-capture de schedule-recovery-operator.py reprend les précontrôles,
le traceur natif et la garde indépendante déjà qualifiés. Une seule fonction
vivante, dans scheduled-functions-<UUID court>, porte */5 * * * * ; données/cache
désactivés. Le handler original scheduled-retention attend réellement deux
secondes avant sa réponse, pour rendre son état running observable. Le pilote
attend handler_started/running par lecture RO avant d’attacher le traceur :
le démarrage froid Docker reste exécuté à sa vitesse normale. Un vrai appel HTTP terminé avant le tir fournit le témoin non protégé.
Le traceur ne remplace aucun registre, tampon ou résultat système. Il suspend
le contrôle seulement lorsque les lectures natives confirment le tir exact
dispatched/non clos et son invocation succeeded, handler démarré, completed_at
renseigné. Le hash, les UUID, le créneau et les logs reçus sont recoupés.

Créer à cet instant une sauvegarde SQLite native depuis une connexion mode=ro,
sous l’identité propriétaire, dans un dossier privé de qualification-history.
Vérifier l’intégrité et le même prédicat dans la sauvegarde elle-même, ainsi que
le témoin HTTP terminal antérieur. Garder les dates réelles et calculer le premier
instant éligible à l’épreuve : max(completed_at des deux appels)+604800s+1s.
Détacher et reprendre immédiatement le contrôle, sans le tuer. La garde restitue
aussi sa santé en cas de perte du traceur ; aucune base originale n’est restaurée.
Comparer CID/image/démarrage et empreintes officielles avant/après ; joindre
le pilote et désarmer timer/service avant toute autre commande de preuve.

Après reprise, vérifier la clôture normale du même tir, sans nouvel appel. Copier
les artefacts immuables de cette installation dans le dossier privé avec inventaire
SHA avant/après ; un écart est un échec. Sauvegarder aussi le registre de stockage
au repos, sans bail ni volume de la fonction témoin. Puis archiver/purger réellement
la fixture par API et vérifier son absence physique. La sauvegarde de capture et
les artefacts restent conservés pour le vieillissement ; ils ne sont pas des
objets actifs de la plateforme et ne sont jamais publiés dans Git. Le rapport public
porte seulement identités de campagne, dates, états et empreintes sans secret.

## Épreuve après sept jours

Le replay devra employer une copie privée de la sauvegarde et des artefacts,
sur l’image immuable capturée. Il sera réalisé dans une fenêtre gardée exclusive :
contrôle habituel arrêté, originaux par identité conservés, zéro conteneur/réseau/
bail d’exécution de l’installation originale avant démarrage, agent sur registre
privé. Une simple deuxième base contre le Docker/registre actif est interdite :
l’installation-id cloné ferait viser les consommateurs originaux par recover.
Le pilote de replay et ses pannes seront spécifiés et qualifiés avant cet usage.

Le passage de rétention doit être observé avant la clôture du tir : témoin HTTP
ancien supprimé, source ancienne conservée tant que son tir reste non terminal,
puis clôture normale et source devenue éligible. La clôture attribue au tir une
nouvelle date réelle ; son propre délai de sept jours repart alors. Cette capture
ne prouve donc ni l’âge d’un tir déjà terminal, ni le plafond numérique.

## Autres preuves requises

Les bornes10000 des invocations et des tirs terminaux sont globales, pas par
fonction. Dépasser ces bornes exige de vrais appels et de vraies fenêtres sur
plusieurs fonctions ; chaque fonction doit rester individuellement sous10000
pour distinguer la portée globale. Les sources des tirs non clos restent hors
du comptage éligible des invocations. Les générations retirées et les tirs déjà
terminaux doivent aussi franchir sept jours réels. Leur préparation reste à
réaliser ; aucun résultat ne découle de la seule capture initiale.

SLS-078 reste[~] jusqu’à ces preuves, au critère adaptateur.7 et à sa régression.


## Premier essai et frontière d’attachement

Le premier essai894df09 atteint le tir03:20UTC mais échoue avant le handler :
invocation failed/runtime_unavailable, handler_started=0, puis expiration du
traceur45s. Il avait attaché le traceur avant le démarrage froid. Les originaux
et gardes sont rétablis et la fixture est purgée ; aucune capture ni preuve
de vieillissement n’est retenue. Le diagnostic ne reconstitue pas l’exception
interne exacte du runtime. La correction borne l’observation à la fin du handler :
attendre son démarrage réel sans traceur, puis observer sa réponse et son commit.
Le délai de garde et le délai d’observation ne sont pas augmentés.


## Capture qualifiée le11 novembre2026

La [preuve5056167](evidence/schedule-retention-capture-dev-2026-11-11.json) passe
quatre groupes sur331sources figées et imagec59b8616 : SSO et vrai HTTP témoin,
capture RO du succès non encore clos, reprise du même contrôle sans redémarrage,
purge publique et absence physique. Le tir03:30UTC, son invocation et les logs
recoupent le même hash/UUID/créneau.5990 fichiers d’artefacts sont copiés et
vérifiés ; le registre privé est sauvegardé au repos. Les timers/services sont
inactifs et le pilote est terminé. L’essai894df09 reste échoué et hors total.

Capture privée schedule-retention-9a2a4cd1eb134c20b4e1c5a1a1bdc7c0. Le premier
instant éligible est le18 novembre2026 à03:30:26.355818UTC. Le vieillissement
reste réel et incomplet ; aucune rétention ni borne10000 n’est déclarée prouvée.

Conserver aussi les deux images contrôle/runtime par export Docker natif dans
ce dossier privé, avec leurs SHA et identités d’image. Cela protège le replay
d’un remplacement futur des tags. Passer les deux sauvegardes SQLite en lecture
seule et placer le dossier sous propriétaire root0700, sans modifier aucun
octet ni mode des artefacts copiés. Un reçu privé recoupe les empreintes de
capture, registre et inventaire avant/après. Cette conservation ne démarre
aucun conteneur et n’administre pas FORGE.

Restent : pannes propres de la capture et régressions du helper historique,
pilote gardé de replay, vieillissement des tirs terminaux/générations retirées,
protection après passage réel de rétention, bornes10000, concurrence078.4,
adaptateur078.7 et campagne complète.


### Conservation native vérifiée

Les deux images ont été exportées en série par docker image save dans le
dossier privé de capture : contrôle59558400 octets, runtime81080320 octets,
SHA des archives dans la preuve liée. Les5990 artefacts et les deux SQLite
restent aux empreintes acquises ; dossier root0700, sauvegardes SQLite0400.
Les deux services sont healthy avec mêmes CID/images/démarrages avant/après
ces exports. Le reçu preservation.json reste privé ; sa copie sans secret
figure sous native_preservation dans la preuve publique. Aucun groupe
fonctionnel supplémentaire n’est compté pour cette conservation.

Pour le replay, lire capture.json et preservation.json dans le dossier privé ;
vérifier SHA des SQLite, inventaire et archives avant toute copie. Les exports
control-image.tar et runtime-image.tar conservent les images immuables malgré
le remplacement ultérieur de leurs tags. Les originaux de capture restent en
lecture seule ; tout replay utilise un autre dossier et son propre journal.
