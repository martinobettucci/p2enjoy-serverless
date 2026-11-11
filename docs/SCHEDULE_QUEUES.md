# Files pleines des tirs planifiés

Complément de [SLS-078](BACKLOG.md#sls-078), selon
[SCHEDULES](SCHEDULES.md#preuves-e2e-attendues). Décision opératoire du10 novembre2026,
avant code. Aucun budget de cellule modifié ; aucun recours à la garde SLS-099.

## Campagne réelle

Créer par HTTPS neuf fonctions originales,0,05CPU/128Mio,min0,max1,concurrence1,
idle0,deadline10s,file5s. Publier/promouvoir le vrai handler
`scheduled-admission.capacity`, HTTP POST et sans cron initialement. Deux cibles,
index0 et8, possèdent aussi un hash pilote avec `*/5 * * * *`. Les sept autres
servent seulement à répartir les réceptions globales.

W est une frontière UTC de cinq minutes choisie après préparation, avec une marge
d'au moins60s. Tous les objets précèdent la première frontière. Activer le cron
de0, puis, vers W−15s, ouvrir16 requêtes HTTPS POST réellement reçues pour0 :
Content-Length16, aucun octet de corps envoyé. Relever les16 états receiving en
API et SQL RO avant W, zéro instance/réservation ; les autres plafonds restent
disponibles. Le tir W de0 doit être refused_capacity/queue_full, sans lien ni
invocation planifiée. Aucun état schedule_capacity ne qualifie cette file.

Après ce refus, déconnecter les16 clients et attendre les16 états
disconnected/client_disconnected/499 sans handler ni admission. Promouvoir le
hash sans cron de0, puis le cron de8 avant W+300.

Vers W+300−18s, ouvrir16 réceptions pour chacune des fonctions0 à7, soit128 au
total. La cible8 a zéro réception. Relever en API et SQL la distribution16×8 et
le plafond global128 avant la frontière ; aucun budget d'instance/CPU/RAM
consommé. À W+300,8 doit être refused_capacity/queue_full sans invocation : son
plafond individuel reste libre. Les30s normales de réception ne sont pas
prolongées ; constater le refus avant leur échéance, puis déconnecter les128.

Attendre les128 états disconnected/499 sans handler, tous les compteurs d'attente
et réservations à zéro. Deux vrais POST complets sur0 et8 doivent réussir dans
Docker. Après extinction et libération, réactiver le cron de0 ; à W+600, les
deux cibles réussissent. Retirer leurs crons par promotion, relire les deux
refus initiaux inchangés : aucun rejeu, quatre tirs et deux succès planifiés.

## Discriminants et nettoyage

Le lecteur natif strict porte les neuf UUID et leur namespace ; il ne fabrique
aucune ligne, horloge ou réponse. Le mode d'observation des files n'effectue que
les lectures SQL sous propriétaire rootless, pour respecter les30s réelles.
Les API et SQL doivent recouper les144 UUID HTTP reçus avant interruption,
leurs dates, états et absence d'admission/handler ; leurs corps ne sont jamais
envoyés. Les requêtes sont toutes rejointes après déconnexion. Les jetons restent
en mémoire, absents du rapport et des diagnostics.

Les deux succès HTTP et deux planifiés, hashes, corps/méthode, contexte et logs
sont recoupés. Total attendu148 invocations, dont144 déconnectées avant handler,
quatre réussites ; les deux tirs refusés n'ont aucune invocation.

Archiver/purger les neuf fonctions par les API réelles, révoquer le jeton et
supprimer parents. Vérifier code/volumes/conteneurs/réseaux/canaux/baux absents,
compteurs nuls,5982 artefacts antérieurs, sources/backend/images/services et
fichiers officiels conservés. Un échec conserve sa preuve, déconnecte et rejoint
ses requêtes, puis nettoie avant toute relance explicite.

Ce complément ne clôture pas SLS-078. Le refus sous commande de stockage et le
maximum/réutilisation sont qualifiés séparément dans [SCHEDULE_UNAVAILABLE](SCHEDULE_UNAVAILABLE.md)
et [SCHEDULE_INSTANCE_REUSE](SCHEDULE_INSTANCE_REUSE.md). Plafond global (SLS-099),
rétention réelle, adaptateur.7 et régression restent ouverts.

## Résultats qualifiés

La [preuve DEV](evidence/schedule-queues-dev-2026-11-10.json), client8ebbf66,
passe quatre groupes sur319 sources figées, même image b9ad872a et budgets
inchangés. Fenêtres20:25/30/35UTC. Le refus individuel est observé avec16
réceptions présentes, environ14s avant la première échéance normale ; le refus
global avec128 réparties16×8 et zéro sur la cible, plus ancienne réception âgée
d'environ19s. Les deux tirs sont refused_capacity/queue_full, lienNULL et aucune
invocation planifiée ; zéro instance et budget CPU/RAM disponible.

Les144 HTTP incomplets deviennent disconnected/client_disconnected/499 sans
admission ni handler ; leurs connexions sont rejointes. Deux HTTP complets puis
deux tirs20:35 réussissent en Docker ; les deux refus initiaux restent inchangés,
aucun rejeu. Total natif : quatre tirs,148 invocations, quatre handlers réussis.
Neuf purges publiques et absence physique recoupées, ressources actives nulles.
Les34 backends,5982 artefacts antérieurs et identités/images/démarrages/fichiers
officiels sont conservés. Aucun build produit, UI/manuel ou capture modifié.

La revue avant lancement a fait corriger la route de révocation, l'attente de
confirmation d'archive et le nettoyage d'un namespace sans service. Aucun échec
de ces branches n'est prétendu provoqué ; les fautes propres du banc et la
régression complète restent distinctes de cette campagne nominale réussie.

Le [complément de console](evidence/schedule-console-dev-2026-11-10.json) qualifie
les états vides/erreur, nom63, pagination et reprise401→200 sur la nouvelle image
c59b8616. Les preuves de ce document conservent leur image historique ; elles
ne sont pas présentées comme rejouées par ce complément.
