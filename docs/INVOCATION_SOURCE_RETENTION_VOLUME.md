# Sources de tirs et borne globale des invocations

Contrat de preuve de [SLS-078.5](BACKLOG.md#sls-078), partagé avec
[SLS-091.1](BACKLOG.md#sls-091). Décision du11 novembre2026 avant code.
SPARK DEV exclusivement, horloge et données réelles, scénario unique en série.

## Discriminant retenu

Une source récente peut survivre à une borne incorrecte parce qu'elle figure
parmi les10000 dernières invocations. Exiger trois ensembles observés nativement :

1.10001 HTTP ordinaires terminés et une invocation planifiée réussie P, soit
10002 lignes terminales, avec son tir dispatched et non clos.
2.10000 HTTP ordinaires et la même P, soit10001 lignes : exactement le plus
ancien HTTP retiré par la maintenance normale, même tir encore non clos.
3.Après clôture normale du même tir,9999 HTTP et P, soit10000 lignes : exactement
le deuxième plus ancien HTTP retiré. P reste récente et conserve sa date de fin.

Le premier retrait prouve l'exclusion de la source du comptage ; le deuxième
prouve son retour dans ce comptage après clôture. Un DELETE sans effet ou une
simple attente ne constituent pas une preuve du passage de maintenance.
Aucune source de capture ancienne n'est fusionnée avec les observations HTTP.
Les sept jours constituent une preuve distincte.

## Parcours réel

Réutiliser l'installation isolée `instance-limit`, même image immuable, plafond2,
SSO/API/runtime/agent réels, originaux conservés et restauration indépendante.
La durée explicite2700s est réservée à ce mode pour la charge et l'attente de
frontière ; défaut900,120,1800 et partial60 sont inchangés. Les durées sont
exclusives, interdites aux autres modes ; un replay de capture exige toujours120.
Qualification de2700 par son armement réel et sa restitution nominale, refus des
combinaisons et régressions ciblées du helper avant clôture de cette extension.

Deux fonctions originales à0,5CPU/128Mio, min=max=concurrence1, stockage partagé,
données/cache désactivés. Le handler `protected-retention-observation.handler`
renvoie et journalise requestId, sequence et marqueur. Les HTTP ordinaires
répondent immédiatement. Un dernier HTTP attend réellement jusqu'à `hold_until` ;
le cron attend jusqu'au créneau reçu plus3s. Les deux attentes bornées à10s
utilisent l'horloge réelle ; aucune valeur du temps ni ligne métier n'est injectée.

Choisir avant publication un créneau UTC W situé30 à35min après la préparation.
Seule B porte un cron numérique minute/heure correspondant à W ; aucun tir ne
peut précéder W après son activation. Produire5000 réponses HTTP par fonction,
chacun des deux flux attend sa réponse avant l'appel suivant. Arrêter et joindre
les flux, recouper10000 UUID/dates/hash et zéro tir. Si la charge n'est pas terminée
au moins60s avant W, échouer et restituer ; ne pas déplacer W automatiquement.
Chaque fonction reste sous10000 observations sur tout le scénario.

À W-1s, lancer le dernier HTTP de A avec hold_until=W+3s. Après le vrai dispatch
cron de B, attendre handler_started/running des deux appels, puis attacher le
traceur natif RO au Python exact du contrôle temporaire. Il ne remplace aucun
registre, tampon, instruction ni résultat système et n'arrête pas séparément
l'ordonnanceur. Les arrêts aux syscalls permettent de lire les états commis.
Acquérir les trois ensembles et leurs UUID/dates, dans cet ordre ; le tir doit
rester non clos aux deux premières frontières. Les deux commits de handlers et
les maintenances sont naturellement concurrents : un rendez-vous W+3 ne garantit
pas leur ordre. Toute frontière manquée est un échec conservé, sans relance
automatique, modification de dates ou invocation directe de maintenance.

Observation25s, alarme35s et commande40s, verrou de fenêtre hérité. Détachement
finally, jonction du mutateur avant restauration. Le rapport conserve les vecteurs
complets ; après détachement, la réponse du dernier HTTP A et le résultat du cron B
sont recoupés avec les logs, hash et identités natives. Désactiver
les minima, attendre zéro consommateur, révoquer le jeton, purger les fonctions
et parents via API ; code/volumes/canaux absents. Restituer les originaux, mêmes
identités/images, configuration officielle et référence inchangées, garde jointe.

Trois groupes : SSO/préparation et10000 HTTP authentiques ; trois frontières et
clôture sans rejeu ; purges et restitution. Les pannes propres du nouvel opérateur
restent requises avant de qualifier sa sûreté. Les régressions de sa fenêtre
commune ont leur preuve distincte de 25 groupes ci-dessous.
Aucun succès acquis par ce contrat ou par les contrôles syntaxiques.

### Garde2700 et refus qualifiés

La [preuve f59a8d3](evidence/source-retention-guard-options-dev-2026-11-11.json)
passe cinq groupes sur346sources inchangées : quatre refus avant mutation,
puis programmation2700s et restitution nominale jointe. Même contrôle/image,
configuration et référence conservés, pilote et garde terminés. L'expiration2700
n'est pas revendiquée. Le collecteur initial a échoué sur un glob incluant son
checkpoint ; le rapport E2E terminé0 est conservé et recoupé avant/après sans
rejouer les tests. Charge10000 et frontières sont qualifiées séparément ci-dessous ;
pannes propres encore requises et régressions communes qualifiées séparément.
Ces cinq groupes seuls ne prouvent
pas la rétention.

## Essai interrompu et pilote durable

L'[essai028d134d](evidence/invocation-source-retention-interrupted-dev-2026-11-11.json) reste interrompu :
9730 réponses sauvegardées localement,9883 invocations succeeded dans le relevé
natif avant retrait, aucun tir et aucun groupe terminé. Handle local disparu,
cause non établie. Restitution nominale du pilote distant, deux conteneurs/réseaux/
baux retirés, mêmes originaux et346sources/images après recoupement. Aucun
succès de rétention ni purge métier déduit de cet essai.

Décision avant code : le prochain lanceur est une tâche systemd utilisateur locale
transitoire `serverless-source-retention-proof-UUID`, indépendante du terminal
qui la crée. Il exécute le même client Node, sans serveur ni dépendance de
remplacement. Il ne planifie aucune récurrence et ne modifie pas FORGE.
Délai global3600s, client borné3000s et garde distante2700s restent distincts.
Le service n'est jamais déclaré terminé sur la seule disparition de son handle.

Une entrée privée lit les identifiants sur stdin masquée puis les transmet en
mémoire à la tâche par socket AF_UNIX. Vérifier UID et PID du serveur contre
MainPID systemd avant transmission ; le serveur vérifie l'UID du client et borne
la taille et l'attente. Aucun secret dans fichier, argument, environnement,
journal ou reçu ; le socket ne persiste aucun contenu. Le canal se ferme après
un message et les valeurs sont abandonnées après transmission au client Node.

Le worker conserve checkpoint et progression privés, sources/images avant/après,
rapport Node original, code retour et état terminal systemd. Les résultats ne
comptent que si les trois groupes, les10001 réponses HTTP, la source planifiée et
la restitution réelle réussissent. Un worker interrompu reste un échec ; vérifier
la restitution distante avant toute autre opération. Le lanceur de contrôle se
termine après réception, puis un processus distinct doit constater le même
MainPID/naissance/cgroup vivant : preuve réelle d'indépendance du terminal.
Le service est oneshot : TimeoutStartSec3600 borne son exécution et
RemainAfterExit conserve le résultat réel après la fin du processus. Aucune
collecte automatique avant preuve : `finish UUID` exige MainPID0, état exited
ou failed, ExecMainCode/ExecMainStatus et checkpoint cohérents, persiste le reçu,
puis arrête cette seule unité et recoupe sa disparition/inactivité. Une autre
commande `status UUID` recoupe le cgroup vivant dans /proc avec celui du reçu,
en plus du PID et de sa naissance. Une interruption finale du worker interdit
la réussite même si Node avait écrit completed=true.
Avant le nouveau nominal long, qualifier la perte réelle du worker avec le même
client : connexion SSO, deux fonctions/instances et au moins un checkpoint de
réponses réelles, puis SIGKILL du seul MainPID de cette unité utilisateur. Le vrai
résultat systemd doit être signal/9 et finish doit conserver/finaliser l'échec,
même si le worker n'a pas pu écrire finished_at_ns. Recouper le nettoyage distant
et les originaux avant de poursuivre ; aucune purge métier ni rétention déduite.
Trois groupes : lancement/indépendance ; SIGKILL/résultat exact ; restitution et
sources/images inchangées. Pas de faux worker, faux serveur ou réponse remplacée.
L'écriture atomique synchronise le fichier et son dossier avant arrêt de l'unité.
Aucune réussite nouvelle acquise par cette décision.

## Premier essai du worker et inventaire de retrait

L'[essai200ea30](evidence/source-retention-worker-loss-failed-dev-2026-11-11.json) échoue au troisième groupe ;
aucun de ses groupes n'est retenu dans un bilan de réussite.511 réponses réelles
sauvegardées, indépendance confirmée et SIGKILL9 correctement finalisé en échec.
La garde indépendante observe deux conteneurs avant retrait du contrôle ; son
nettoyage trouve déjà zéro conteneur, puis retire deux réseaux et libère deux
baux. Originaux et348sources/images recoupés, référence conservée. L'assertion
exigeait deux retraits par la garde elle-même ; l'acteur du retrait préalable
des conteneurs n'est pas établi par ces seuls relevés.

Correction avant code : conserver par lecture Docker réelle les deux conteneurs,
réseaux et identifiants de consommateurs juste avant SIGKILL, avec installation,
fonction, révision et image recoupées. Après restitution, vérifier l'absence de
chacun de ces identifiants, de tout conteneur/réseau étiqueté pour l'installation
temporaire et de tout bail correspondant dans le registre réel. Garder séparément
les retraits explicitement enregistrés par la garde, sans lui attribuer ceux
qu'elle a trouvés déjà effectués. Le nombre de consommateurs initial reste deux ;
la propriété à prouver est leur absence finale et la restitution des originaux.
Le relevé terminal est persisté avant ses assertions, même si une assertion échoue.

### Perte du pilote durable qualifiée

La [preuve bbe9d0e](evidence/source-retention-worker-loss-dev-2026-11-11.json) passe trois groupes
sur348sources figées :512 réponses HTTP réelles, contrôleur initial terminé et
worker indépendant recoupé, SIGKILL MainPID avec résultat signal/Code2/Status9
conservé comme échec. Deux conteneurs/réseaux et consommateurs sont inventoriés
avant faute puis réellement absents après restitution ; les deux retraits de
chaque classe sont aussi enregistrés par la garde dans ce cas. Restitution
indépendante terminée, mêmes données/configuration/images et référence, garde
et unité locale jointes. Le premier essai échoué reste exclu. Ces trois groupes
qualifient la perte et sa restitution ; nominal numérique qualifié séparément ci-dessous, sept jours encore requis.

## Source protégée sous borne qualifiée

La [preuve d860cc5](evidence/invocation-source-retention-volume-dev-2026-11-11.json) passe trois groupes
sur348sources identiques avant/après et les mêmes images.10001 réponses HTTP
réelles et un handler cron donnent10002 observations terminales,5001 par fonction.
Le passage de rétention retire exactement le plus ancien HTTP et conserve10001
lignes, source incluse mais hors comptage tant que le tir reste strictement non
clos. Après clôture normale du même tir, le deuxième plus ancien HTTP est retiré :
10000 lignes, source désormais comptée et strictement inchangée. Les trois vecteurs
complets sont recoupés par completed_at DESC,id DESC ; observation12,335898s sous25s.

Deux purges publiques et contrôles physiques d'absence terminent, puis restitution
nominale jointe des originaux. Le vrai worker oneshot quitte0 ; son résultat
systemd success/Code1/Status0 est conservé avant arrêt de l'unité.348sources/images
inchangées, configuration et référence conservées. Le brut complet compressé
contient les vecteurs et reçus ; essais interrompu/échoué exclus. Sept jours,
pannes propres résiduelles et campagne complète restent ouverts :078.5 non clôturée.

## Régressions finales des fenêtres de restitution

La [preuve au commit f908640](evidence/retention-history-guard-regressions-dev-2026-11-11.json)
passe 25 groupes sur 351 sources identiques avant/après : onze fenêtres/partiel,
trois options/défaut 900, cinq options 2700 et six consommateur vivant/pause/
namespace. Onze campagnes distinctes, images conservées. Les confirmations
SIGTERM (15) et SIGKILL (9) ont pidfd lisible puis pilote absent de /proc, mesurées
10,765 ms et 28,345 ms ; gardes de 120 s et restitutions attendues jointes. Les
options 900/2700 s sont programmées puis restituées, pas laissées expirer.

Les trois essais antérieurs sont exclus ; le ciblé SIGKILL de deux groupes n'est pas ajouté
au même cas de cette matrice. Le contrôle final garde le même conteneur 68a8 et image c59,
redémarrage à 14:26:18 UTC, référence inchangée, deux services sains, actifs à zéro, 5 982 artefacts
et aucune garde. Cette preuve qualifie les fenêtres communes ; pannes
propres de capture et d'observateur source, âge et campagne complète restent
ouverts dans 078.5. Les preuves antérieures conservent leurs époques distinctes.

## Refus réel après attachement de l'observateur

Décision du 11 novembre 2026, avant code, pour le reste SLS-078.5 déjà inscrit
au backlog : ajouter au client existant le mode explicite `--observer-refusal`.
Le mode nominal conserve ses 10 000 appels, sa fenêtre de 30 à 35 minutes et
ses trois frontières. Le mode de refus utilise les deux mêmes fonctions et
le même handler original, mais ne produit aucun HTTP ordinaire. Il choisit
un prochain créneau UTC à au moins 120 secondes et prépare les deux vraies
instances avant W-30. À W-1, un HTTP attend W+3 ; le vrai cron attend aussi W+3.

L'opérateur est celui du nominal, sans option de faute ni remplacement : il
constate les deux handlers running, s'attache au même processus Python exact,
puis sa vérification de 10 002 observations refuse naturellement l'historique
qui ne contient que deux appels. Nommer ce refus `retention_history_incomplete`.
Conserver avant l'assertion le PID/naissance de l'opérateur, le TracerPid réel,
les deux identités d'appel et les comptes initiaux. Aucun enregistrement de
capture, donnée SQL, horloge, code applicatif ou résultat système n'est modifié.

Dans le finally de cet opérateur, fermer le lecteur SQLite même si detach
lève. Conserver les résultats effectivement constatés : même PID/naissance du
contrôle, TracerPid égal à zéro après detach, descripteur mémoire fermé,
connexion du lecteur passée à None après retour effectif de close. Un drapeau
attached=false ne suffit pas. Un défaut de nettoyage demeure un échec. Ces
mesures concernent aussi les retours nominaux et restent privées dans la fenêtre
validée ; le reçu final imprimé doit être écrit après ce nettoyage.

Le helper existant conserve son refus, son code 1 et son finally de restitution :
aucune nouvelle opération ni dérogation à completed n'est ajoutée. Le client
attend sa fin, lit le reçu durable de l'opérateur et son état terminal via SSH,
recoupe les deux consommateurs réels avant faute puis leur absence physique,
les réseaux, baux, artefacts et canaux, ainsi que la restitution des originaux,
les mêmes données/configuration/images et la référence. Les deux appels lancés
sont joints ; l'issue de leur réponse pendant restitution reste enregistrée.

Deux groupes : SSO/préparation réelle sans appel ordinaire ; refus naturel après
attache, fermeture/détachement mesurés, code 1 conservé et restitution jointe.
Le client de qualification peut réussir ce scénario de refus, mais l'opérateur
et le helper restent explicitement échoués. Cette preuve n'ajoute aucun succès
de rétention numérique, de purge métier ou d'expiration 35/40 secondes. Syntaxe
et revue ne valent pas E2E ; les autres pannes et l'âge réel restent ouverts.

## Refus après attachement qualifié

La [preuve 956498a](evidence/invocation-source-observer-refusal-dev-2026-11-11.json)
passe deux groupes sur 351 sources identiques avant/après. Le scénario du
créneau réel 15:00 UTC ne produit aucun HTTP ordinaire : un vrai HTTP et un
vrai cron sont running, leur tir/UUID/fonction recoupés. L'opérateur constate
l'historique insuffisant après attache : TracerPid 471960 sur le contrôle
470002/naissance 502682872, puis zéro après detach ; mémoire et lecteur fermés.
Son reçu garde completed=false et AssertionError/retention_history_incomplete.
Le code retour individuel de l'opérateur n'est pas enregistré ; celui du
helper est bien 1, avec l'assertion exacte conservée en privé et son SHA.

Le client de qualification termine 0 après ce refus attendu et la restitution
nominale jointe, sans ajouter de succès de rétention ni de purge métier. Deux
conteneurs, deux réseaux et deux baux sont corrélés puis retirés, canaux et
artefacts absents. Contrôle final : même conteneur/image, redémarrage attendu
15:00:08 UTC, référence inchangée, deux services sains, actifs à zéro, 5 982
artefacts et aucune garde active. Seuls les deux fichiers de cet observateur/
client diffèrent des 25 régressions précédentes ; helper et images inchangés.

Ce refus qualifie une panne après attache et son nettoyage normal. Il ne
qualifie pas une erreur de detach, l'alarme 35 s, la coupure 40 s, l'attente
native 25 s sans événement ni l'âge de sept jours. Le nominal numérique garde
sa preuve distincte au commit d860cc5 ; la campagne complète reste requise.

## Mesure de l'attente native sans événement

Décision du 11 novembre 2026 avant code pour le reste078.5 inscrit : mesurer
la vraie classe partagée `schedule_firing_volume_replay.BlockingNativeObserver`
sur le contrôle temporaire vide du mode instance-limit existant, même image
applicative et garde120. Cette preuve porte sur l'observateur, pas sur la
rétention ni sur un handler ; aucun jeu de 10 000 lignes n'est fabriqué.

Le probe valide la fenêtre, son verrou hérité, le contrôle original arrêté,
les répertoires de remplacement et le CID/image/PID/naissance/cgroup du seul
contrôle temporaire. Il ouvre le lecteur réel sous son propriétaire, attache
l'observateur et consomme l'arrêt initial. Un timer systemd indépendant28s,
code de dégel figé et reçu root0600, est armé avant Docker pause. Il cible
uniquement ce CID/PID validé, sans attendre le verrou retenu par le probe.

Après Paused=true confirmé, reprendre par PTRACE_SYSCALL et vérifier dans le
processus traceur qu'aucun statut n'attend avec WNOHANG. Un statut immédiat
est une précondition échouée, sans preuve d'absence d'événement. Persister
l'entrée monotone, l'échéance25s, le temps restant de l'alarme globale35 et
l'échéance réelle du timer ; exiger plus de26s avant son dégel programmé.
Appeler ensuite la vraie méthode wait, sans remplacer waitpid ni les signaux.

Conserver son résultat ou exception et sa durée avant tout nettoyage. Si le
retour n'arrive qu'au dégel de secours après25s, il établit un dépassement,
pas une expiration de l'alarme35. Après un retour anticipé, déclencher le
même service indépendant de dégel puis attendre son reçu. Toujours confirmer
Paused=false avant detach ; enregistrer séparément exception d'attente,
erreurs de nettoyage, TracerPid final, mémoire et lecteur fermés. Conserver
le résultat terminal du service avant de joindre timer/service.

La commande extérieure reste bornée40s et la fenêtre120 possède sa restitution
indépendante existante. Le client recoupe l'installation vide réelle, le reçu
de mesure puis les originaux restitués, données/configuration/images identiques
et tous les processus joints. Trois groupes attendus par campagne : installation,
mesure de défaut ou borne corrigée explicitement choisie, restitution. Aucun
résultat n'est acquis par cette spécification ; 35/40 propres à l'opérateur
source, erreur de detach et rétention restent des preuves distinctes.

### Dépassement reproduit et décision de correction

La [reproduction c64fdd7](evidence/native-observer-deadline-reproduce-dev-2026-11-11.json)
passe trois groupes sur353sources/images identiques. Sans statut en attente,
le vrai wait25 reste bloqué28,202s : l'erreur native_stop_not_observed arrive
après le dégel systemd28 du contrôle temporaire. L'alarme globale avait encore
34,903s à l'entrée ; ce n'est pas une expiration35. Même PID/naissance,
TracerPid0 après dégel confirmé, mémoire/lecteur fermés, acteur terminal
success/Code1/Status0 joint et originaux restitués. Aucun handler exécuté.

Décision avant code : remplacer l'attente waitpid bloquante de cette classe
par une attente de vrais SIGCHLD bornée. Bloquer temporairement SIGCHLD dans
le thread, consulter waitpid(WNOHANG) avant chaque attente, puis utiliser
sigtimedwait avec le temps monotone restant. Un signal d'un autre enfant ne
vaut jamais arrêt du contrôle : seul le waitpid de son PID décide. Restaurer
le masque initial dans un finally. Ne modifier ni handler SIGALRM ni minuterie
globale, pour conserver le délai35 et les interruptions propres du caller.
Cette approche évite une temporisation à chaque syscall et ne réserve aucun
second timer global ; aucun signal ou retour système n'est fabriqué.

Le même probe bounded doit ensuite échouer à25–26s sans attendre le secours28,
mesurer le masque de signaux identique avant/après, l'alarme35 encore active
avec son temps restant cohérent et son handler conservé. Puis dégel indépendant,
détachement réel et restitution comme dans la reproduction. Rejouer ensuite
les consommateurs et scénarios connexes de la classe ; cette borne isolée ne
clôture ni078.5 ni les pannes35/40 propres de l'opérateur source.

### Borne corrigée qualifiée isolément

Les [trois groupes46e216d](evidence/native-observer-deadline-bounded-dev-2026-11-11.json)
passent sur353sources/images identiques : même pause réelle et WNOHANG0,
attente levée à25,000182476s avant le secours28. Masque[] avant/après,
handlerSIGALRM conservé ; alarme restante34,902153→9,901989s, cohérente avec
la durée mesurée. Le vrai service indépendant dégèle le contrôle avant detach,
termine success/Code1/Status0 et est joint. TracerPid0, mémoire/lecteur fermés,
originaux restitués et aucune erreur de nettoyage.

Seuls les deux fichiers du probe et la classe partagée changent depuis la
reproduction c64fdd7. Brut98 371/gzip38 128. Aucun handler exécuté ; deux
services sains, actifs à zéro et5 982 artefacts conservés. La borne isolée
est qualifiée ; les consommateurs de la classe, les pannes35/40 propres à
l'opérateur source, detach en erreur, l'âge et la campagne finale restent ouverts.

### Régressions des consommateurs sur les mêmes353sources

Les [onze groupes96dcca0](evidence/native-observer-consumers-dev-2026-11-11.json)
passent sur les mêmes353sources/images que la borne isolée, identiques
avant/après. Quatre campagnes réelles et sérielles :

- Borne des tirs, trois groupes :132fenêtres réellement manquées ; observation
  de la frontière limitée aux40 premières,10 496→10 000 au même curseur,
  exacts496plus anciens retirés. Observation13,526s, nouveau SSO/lectures
  paginées, reprise finale au curseur courant et restitution.
- Source protégée, trois groupes : capture canonique reprise en préflight,
  observation9,189s, mêmes témoins avant sept jours, nouveau SSO/API et
  restitution. Capture conservée.
- Historique terminal, trois groupes : capture canonique exacte, préflight
  observé en0,005624s, nouveau SSO/API, restitution et source conservée.
- Refus source, deux groupes : aucun HTTP ordinaire, mais deux vrais handlers
  HTTP/cron running ; refus après attache, TracerPid0 et lecteur/mémoire fermés.
  Helper échoué1 conservé, client0, deux conteneurs/réseaux/baux retirés et
  neuf contrôles physiques réussis, restitution jointe.

Brut33 679 951octets/gzip2 063 211. Les invocations déjà présentes dans les
captures ne sont pas recomptées comme des handlers nouveaux ; seuls les deux
handlers de la campagne de refus démarrent pendant ces quatre replays. Deux
services sains, actifs à zéro,5 982artefacts conservés et aucune garde finale.
Cette preuve qualifie ces consommateurs ; le nominal numérique complet de la
source protégée reste à rejouer sur cette époque, ainsi que35/40 propres,
detach en erreur, l'âge réel et la campagne complète. Aucune modification UI/produit.

## Pannes propres de l'alarme35 et de la commande40

Décision du11 novembre2026 avant code, pour le reste078.5 déjà inscrit. Reprendre
la préparation authentique à deux handlers HTTP/cron du mode observer-refusal,
sans appels ordinaires. Après attache et premier reçu durable (deux running,
tir dispatched/non clos, mêmes UUID), un mode de faute explicite arrête le vrai
opérateur par SIGSTOP avant l'assertion10002 et avant la boucle25. Le nominal
et le refus sans option gardent leur flux. Aucune exception ni minuterie n'est
remplacée ; les limites35/40 restent celles du code réel.

Le reçu de porte porte les identités/PID/naissances, SHA, point monotone, vrai
getitimer et masque de signaux. Un acteur systemd indépendant, figé et prêt avant
SIGSTOP, ouvre un pidfd sur cet opérateur exact et confirme son étatT. Il ne
prend pas le verrou de fenêtre. La marge entre le début réel de timeout40,
l'armement de35 et la reprise prévue doit laisser au moins2s pour nettoyage ;
sinon le scénario échoue sans allonger les durées.

- Alarme35 : l'acteur attend l'échéance réelle calculée depuis le timer restant,
  augmentée de0,5s, recoupe SIGALRM pending dans SigPnd/ShdPnd, puis envoie un
  seul SIGCONT par pidfd. La reprise délivre le vrai SIGALRM ; conserver
  TimeoutError/native_observation_deadline avant nettoyage, puis même contrôle
  TracerPid0, mémoire/lecteur fermés et aucune erreur de nettoyage. Le retard
  lié à SIGSTOP est mesuré : ne pas prétendre une exécution de Python à35,000s.
- Commande40 : l'acteur confirme la même suspension et le signal pending mais
  n'envoie pas SIGCONT. Le vrai timeout --foreground --signal=KILL40s termine
  l'opérateur. Conserver son code réel avant assertion du helper, sa durée,
  wrapper joint et opérateur absent. Mesurer PID/naissance/TracerPid0 du même
  contrôle avant que restore ne le retire. Aucune fermeture Python explicite
  ni écriture finale de l'opérateur tué n'est revendiquée.

Le helper conserve un reçu propre de la commande native avant refus, sans
extrapoler son code depuis celui du helper. Le code du wrapper est à mesurer,
pas à déduire de SIGKILL : avec le binaire réel du SPARK, sans preserve-status,
timeout retourne124 à l'expiration. Le helper doit ensuite échouer1 et restituer les originaux ;
son erreur reste distincte de l'exception source et du résultat de l'acteur.
Préserver séparément erreur primaire et erreurs de nettoyage. Conserver les
résultats systemd terminaux avant jonction des seules unités de l'acteur.

Les fonctions ont leurs limites réelles : l'HTTP peut échouer pendant la pause ;
conserver ce résultat et les deux identités running au point de porte sans
annoncer un succès métier. Pour chaque cas, recouper les deux conteneurs,
réseaux et baux avant faute puis leur absence physique, les originaux identiques,
gardes et processus joints. Deux groupes par cas : préparation réelle, puis
faute exacte et restitution. Aucun résultat ne découle de cette spécification ;
ces pannes ne qualifient ni rétention, ni boucle25, ni erreur de detach.

### Remplacements après suspension et inventaire de restitution

L'[essai ad70d47](evidence/source-observer-deadline-failed-dev-2026-11-11.json)
reste échoué, zéro groupe qualifié : vraie alarme levée après35,719s, lecteur
fermé et contrôle détaché, mais assertion finale limitée aux deux instances
initiales. Après reprise, les délais des handlers expirent et le moteur crée
des remplacements pour maintenir minimum1. Ces identités nouvelles sont légitimes.

Décision avant correction : conserver l'inventaire initial et enrichir, pour
ces deux seuls modes de faute, le reçu natif du nettoyage avec les labels
installation/fonction/révision/instance, image, montage code et réseaux de chaque
ressource tardive. Le contrôle temporaire est retiré avant cet inventaire :
aucune nouvelle instance ne peut ensuite être créée par lui. Valider les
remplacements contre les mêmes deux fonctions/révisions et l'image runtime,
sans exiger qu'ils portent les anciens identifiants. Les réseaux et baux
peuvent survivre au retrait antérieur de leur conteneur ; conserver leur
corrélation native au lieu d'exiger des classes de même taille.

Après restitution, exiger par lectures réelles l'absence de tous les CID,
réseaux et consommateurs de l'union initiale/tardive, de leurs canaux et de
toute ressource Docker portant l'installation temporaire. Les neuf contrôles
physiques existants restent exigés. Les retraits enregistrés par la garde
restent distincts des absences déjà acquises. Ne modifier ni minima, ni délais,
ni assertions des modes nominal et observer-refusal pour éviter ces remplacements.

### Code réel du wrapper timeout

L'[essai f22d217](evidence/source-observer-timeout-status-failed-dev-2026-11-11.json)
reste une matrice échouée, zéro groupe qualifié dans son bilan :35 passe ses
contrôles, mais40 échoue sur124 attendu à tort137. La commande réelle dure
40,013982s, rapporte l'envoi KILL, joint le wrapper et constate l'opérateur
absent/TracerPid0 avant restitution. Les contrôles physiques du client40 ne
sont pas atteints ; l'état global final est sain et les originaux sont restitués.

Décision avant code : conserver la même commande40 et son échec réel124,
le signal demandé9, la durée, le diagnostic natif KILL, le pidfd terminé et
l'absence du processus. Ne pas convertir124 en137, ni ajouter preserve-status
pour obtenir le nombre initialement attendu. Le reçu conservera le chemin
résolu, la version et le SHA du vrai binaire timeout. Le relevé DEV identifie
uutils0.10.0, /usr/lib/cargo/bin/coreutils/timeout, SHA
f84e76ea4da1e0c4e92254bd0d7dccdabe2c8b3098e734f27997dae3ee5d8e02.
La [source primaire uutils0.10.0](https://github.com/uutils/coreutils/blob/0.10.0/src/uu/timeout/src/timeout.rs)
retourne CommandTimedOut sans preserve-status après expiration ; le statut du
wrapper ne doit pas être présenté comme un statut individuel du fils Python.
Rejouer35/40/refus après correction, sans réutiliser la matrice échouée.

### Bornes35/40 et régression qualifiées

La [preuve e45126b](evidence/source-observer-deadlines-dev-2026-11-11.json)
passe six groupes réels sur354sources/images identiques avant/après :
35 à18:30UTC,40 à18:35UTC, refus sans option à18:40UTC. L'alarme donne
TimeoutError/native_observation_deadline après35,683720s, lecteur/mémoire
fermés. Le timeout40 retourne réellement124 après40,009839s, diagnostic KILL
et opérateur absent ; aucune fermeture Python ni waitstatus individuel137
n'en sont déduits. Chemin/version/SHA du binaire sont liés au SHA de l'exécutable
réel du wrapper lu dans /proc.

Les deux cas mesurent TracerPid0 du même contrôle avant restitution et joignent
leurs acteurs. L'union des deux instances initiales et des deux remplacements
est physiquement absente : quatre CID/réseaux/consommateurs par cas, neuf
contrôles existants et sept contrôles exacts supplémentaires. Le refus sans
option conserve son erreur d'historique, lecteur fermé et retrait des deux
consommateurs. Trois refus CLI précoces sont distincts, sans groupe E2E ajouté.

Brut466439octets/gzip156743. Les deux matrices échouées restent exclues.
Originaux restitués, même contrôle/image, démarrage18:40:06UTC attendu,
référence inchangée, deux services sains, actifs/baux à zéro,5982artefacts et
aucune garde. Les bornes propres35/40 sont qualifiées ; detach en erreur et
reprise historique finale ont leurs preuves distinctes ci-dessous. Nominal
numérique courant, âge18novembre et campagne complète restent requis dans078.5.

## Fermeture du lecteur malgré une erreur native de detach

L'[essai34b8815](evidence/source-observer-detach-failed-dev-2026-11-11.json)
reste échoué, zéro groupe qualifié. Docker pause et WNOHANG0 sont observés,
mais detach réussit sans exception : TracerPid0, mémoire/lecteur fermés et
commande1 en1,606436s. L'acteur dégèle après mort de l'opérateur et les originaux
sont restitués. Les contrôles physiques du client ne sont pas atteints ; état
final sain,5982artefacts et aucune garde. La pause du contrôle seule ne suffit
pas à empêcher le traitement de PTRACE_INTERRUPT sur ce SPARK.

Décision révisée avant code : garder le mode explicite --observer-detach-failure,
les deux vrais handlers et le refus naturel d'historique. Armer l'acteur figé
indépendant avec pidfd avant Docker pause. Après attache/pause, la vraie reprise
ptrace doit encore donner WNOHANG0. Affecter au seul observateur de cette faute
un point de suspension au prochain wait. La méthode detach reste inchangée.

Dans BlockingNativeObserver.wait, après calcul de son échéance par detach et
blocage natif de SIGCHLD, ce point optionnel conserve l'échéance reçue, le temps
monotone, les identités et mémoire déjà fermée, puis envoie un vrai SIGSTOP à
l'opérateur. L'algorithme d'attente, son échéance5, SIGALRM35 et timeout40 ne
changent pas ; aucune exception, réponse système ni horloge n'est fabriquée.
Sans ce mode, aucun point de suspension n'est armé et le flux reste ordinaire.

L'acteur recoupe le reçu d'entrée et l'étatT du même opérateur. Il attend
l'échéance5 réelle plus0,25s, puis envoie un seul SIGCONT par pidfd. À la reprise,
la vraie vérification d'échéance de wait doit lever native_stop_not_observed,
mesurée5–7s dans detach. Une reprise avant échéance, un statut déjà présent
avant la faute ou un reçu non corrélé invalide la campagne.

Conserver séparément l'erreur primaire retention_history_incomplete, l'erreur
de detach avec entrée/sortie monotones et raison, puis native_tracer_retained
dans detach-state. Le finally extérieur doit effectivement fermer le lecteur
SQLite et enregistrer reader_closed=true ; la mémoire doit aussi être fermée.
L'opérateur/helper restent échoués1. Le TracerPid encore présent dans ce finally
n'est pas présenté comme un detach réussi : après mort de l'opérateur, l'acteur
constate pidfd terminé et même contrôle TracerPid0 encore Paused=true, puis le
dégèle réellement. Son résultat et sa jonction précèdent la restitution.

L'acteur borne à15s l'attente totale de la faute. En échec, il reprend par pidfd
le seul opérateur encore arrêté et dégèle le contrôle ; ce secours explicite
interdit tout succès. Unité oneshot30s, jonction bornée30 de ce seul mode, durées
35/40 et minima inchangés. Les ressources tardives et l'absence exacte de l'union
initiale/tardive restent exigées sans imposer un nombre de remplacements.
Deux groupes : préparation SSO/deux handlers, puis vraie erreur/lecteur fermé/
dégel/restitution ; refus sans option à rejouer. Nominal numérique, consommateurs
de la classe partagée et âge sont des preuves distinctes, toujours requises.

### Erreur native de detach et lecteur fermé qualifiés

Les [quatre groupes b5f0825](evidence/source-observer-detach-failure-dev-2026-11-11.json)
passent sur355sources/images identiques avant/après : faute à19:10UTC puis refus
sans option à19:15. Vrai SIGSTOP après entrée dans wait et échéance5 calculée
par detach ; SIGCONT pidfd après échéance+.25. La vraie exception de délai
survient après5,255020512s ; erreur primaire d'historique conservée, puis
native_tracer_retained pendant le finally. Mémoire/lecteur fermés malgré ces
erreurs, masque[] restitué après SIGCHLD17 bloqué au point de faute.

L'acteur constate ensuite opérateur mort et même contrôle Trace0 encore gelé,
puis dégèle sans secours, termine0 et est joint. Neuf contrôles physiques et
sept exacts passent ; le refus sans option conserve son chemin normal. L'essai
34b8815 sans exception reste exclu. Brut250841/gzip80995 ; originaux restitués,
contrôle démarré19:15:07UTC, référence inchangée, actifs/baux nuls,5982artefacts
et aucune garde. Cette preuve clôt le cas lecteur/detach, sans qualifier à elle
seule les consommateurs modifiés, le nominal numérique, l'âge ni078.5 entière.

La borne25 sans faute, les consommateurs count/source/terminal/refus/35/40 et
l'historique final du helper sont qualifiés séparément ci-dessous. Le nominal
source numérique courant reste requis.
Les captures canoniques d'âge restent conservées jusqu'au18novembre.

### Classe courante et six consommateurs requalifiés

La [borne25 courante](evidence/native-observer-detach-bounded-dev-2026-11-11.json)
passe trois groupes sur355sources4ad78da :25,000300307s sans armer la faute,
masque/handler conservés, alarme restante cohérente, dégel avant detach et
restitution. Les [quinze groupes consommateurs](evidence/native-observer-detach-consumers-dev-2026-11-11.json)
passent ensuite sur les mêmes355sources/images, en six campagnes sérielles :

- count19:20 :157fenêtres réellement manquées, frontière observée après40,
  10 496→10 000 au même curseur et exacts496 plus anciens retirés,12,758454s ;
- source préflight19:25 :9,476869s, témoins et capture canonique conservés ;
- terminal préflight19:30 :0,005154s, témoins et capture conservés ;
- refus19:35 : erreur naturelle, lecteur fermé et absence physique ;
- alarme19:40 :35,679350s/commande1, mémoire/lecteur fermés ;
- commande19:45 :40,009936s/wrapper124, diagnostic KILL et opérateur absent.

SSO/API, ressources et restitutions passent. Les deux derniers cas mesurent
Trace0 avant retrait, joignent les acteurs et vérifient neuf contrôles
physiques et sept exacts ; aucun waitstatus137 du fils n'est déduit. Six
handlers réellement démarrés, distincts des observations copiées des captures.
Brut34040469/gzip2154883 pour les consommateurs. Originaux restitués, contrôle
démarré19:45:45UTC, référence inchangée, deux services sains, actifs/baux nuls,
5982artefacts et aucune garde. Historique final qualifié ci-dessous ; nominal
numérique complet, âge18novembre et campagne complète restent requis ;078.5 reste ouverte.

### Reprise historique sur les sources courantes

Les [cinq groupes ef98a9f](evidence/schedule-recovery-detach-regression-dev-2026-11-11.json)
passent sur les mêmes355sources/images que la borne25 et les quinze consommateurs.
Trois coupures137, trois échéances manquées sans invocation et trois tirs
suivants réussis sans rejeu ; claimed sans invocation, linked interrompu avant
handler. Trois handlers réussis, quatre gardes terminées et une purge physique.
Worker réel terminal0 puis arrêté, originaux et captures canoniques conservés.
Cette régression ne qualifie pas le nominal numérique source courant ni l'âge.
