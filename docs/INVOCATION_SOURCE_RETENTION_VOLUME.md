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
et les régressions du helper restent requises avant de qualifier sa sûreté.
Aucun succès acquis par ce contrat ou par les contrôles syntaxiques.

### Garde2700 et refus qualifiés

La [preuve f59a8d3](evidence/source-retention-guard-options-dev-2026-11-11.json)
passe cinq groupes sur346sources inchangées : quatre refus avant mutation,
puis programmation2700s et restitution nominale jointe. Même contrôle/image,
configuration et référence conservés, pilote et garde terminés. L'expiration2700
n'est pas revendiquée. Le collecteur initial a échoué sur un glob incluant son
checkpoint ; le rapport E2E terminé0 est conservé et recoupé avant/après sans
rejouer les tests. Charge10000, frontières, pannes propres et régressions restent
à qualifier ; aucun succès de rétention déduit de ces cinq groupes.

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
