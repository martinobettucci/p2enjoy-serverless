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
