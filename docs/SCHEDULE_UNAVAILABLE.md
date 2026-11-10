# Tir pendant une opération de stockage en cours

Complément de [SLS-078](BACKLOG.md#sls-078) et de
[SCHEDULES](SCHEDULES.md#preuves-e2e-attendues). Décision opératoire du10 novembre2026,
avant code. Une vraie commande publique de cache reste en attente sous une faute
physique bornée ; aucun état SQL, résultat d'agent ou code du moteur n'est remplacé.

## Préparation et garde

SPARK DEV au repos, aucune fonction étrangère. Créer une fonction originale dans
`storage-recovery-<8hex>` pour respecter le périmètre du helper existant
`storage-command-faults.py`.0,05CPU/128Mio,min0,max1,idle0,deadline10s,file5s,
données/cache2Mio, données exclusives. Publier normalement le handler
`scheduled-storage.handler`, avec HTTP POST et cron `*/5 * * * *` préparé comme
pilote. Première version promue sans cron ; un HTTP réel écrit les fichiers
`record` de données et cache, synchronisés, puis l'instance et son bail disparaissent.

Choisir W avec au moins60s de marge ; si nécessaire attendre une frontière avant
promotion du cron pour ne produire aucun tir préparatoire. Avant faute : code et
génération promus, empreintes des deux records, identité/propriété/mode du cache,
configuration, allocations et état des services relevés nativement.

Vers W−25s, armer le mode existant deny-cache sur le seul UUID. Sa garde systemd
indépendante100s précède la faute, le helper attend au plus85s ; aucune durée
n'est changée. L'agent reste vivant ; seul le backing cache identifié devient
root/mode000. L'identité du même répertoire et les contenus sont recoupés sous faute.

Le client SSH possède son groupe de processus, un délai de connexion10s et des
keepalives10s/2. Sa jonction locale est bornée à135s ; après dépassement, arrêter
le seul groupe client possédé et attendre sa fin au plus10s. Cette borne dépasse
la garde100s, sans prétendre que son échéance prouve la restitution. Erreurs de
trame/stdin ramenées dans le flux async, jamais levées hors du finally. Un reçu
manquant ou une jonction inconnue interdit le nettoyage métier.

## Refus et reprise

Envoyer une seule commande `POST /api/functions/{id}/cache-clear`, UUID neuf et
If-Match courant. Avant W et jusqu'au refus, exiger le même reçu
pending/volumes/storage_io_error, function_operations decision=commit, version
agent connue et intention pending corrélée. Les instances/baux restent absents.

À W, le curseur progresse et le tir du bon hash/génération devient
refused_unavailable/execution_unavailable, invocation_idNULL. Ce code fixe est
celui du dispatch actuel pour le HTTPException du verrou d'opération. Vérifier
qu'aucune invocation, réservation ou effet du handler ne correspond à ce tir.
La santé peut être dégradée pendant la commande ; la progression du scheduler
doit être observée, jamais déduite de healthz.

Restituer explicitement via le helper, attendre son événement restored et sa
fin, puis les unités inactives. La restitution vérifie le même inode avant
chown/chmod ; le worker peut ensuite remplacer normalement le cache vidé.
Attendre le même reçu completed sans nouveau POST, retrait de function_operations,
reçu agent corrélé, cache record absent et donnée permanente identique.
Version de code/génération et configurations restent conservées.

À W+300, un nouveau tir du même hash réussit dans Docker. Son journal original
recoupe ID d'appel, POST, corps{}, trigger/slot, donnée conservée et cacheNULL.
Un HTTP sain relit ces valeurs. Le premier tir reste refusé, lienNULL, sans rejeu.
Retirer le cron par publication/promotion normale. Total : deux tirs et trois
invocations réussies (HTTP préparatoire, planifiée, HTTP de lecture).

## Preuves et nettoyage

Quatre groupes : préparation réelle, commande/refus sous faute, restitution et
prochain tir, purge publique et absence physique. Le lecteur natif strict accepte
un namespace, un UUID et une seule unité de garde ; SQLite sous propriétaire,
identités des répertoires/records, états agent/commande et contrôle, ressources,
processus exact du helper et unités systemd. Aucun secret ni corps privé dans
les journaux ou rapports.

Après restitution connue seulement : révoquer le jeton, archiver/purger par API,
supprimer parents ; code/volumes/conteneur/réseau/canal/bail absents et compteurs
nuls,5982 artefacts antérieurs/backend/images/services/configuration conservés.
Un échec libère et rejoint le helper avant tout nettoyage ; si la restitution
est inconnue, conserver les ressources et diagnostiquer sans purge ni relance.

Cette campagne ne provoque ni SIGKILL du helper ni arrêt du contrôle ; leurs
preuves antérieures restent distinctes. Aucun budget, fichier officiel,
migration, UI/manuel ou image produit modifié. Plafond global (SLS-099),
rétention réelle, états UI et régression complète gardent SLS-078 ouverte.

## Résultats qualifiés

La [preuve DEV du10 novembre2026](evidence/schedule-unavailable-dev-2026-11-10.json),
client5cb8564, passe quatre groupes sur322 sources figées et même image b9ad872a.
À20:55UTC, commande clear-cache pending/volumes/storage_io_error et garde commit,
cache du même inode root/mode000, contenu conservé, aucune instance ni bail.
Le tir devient refused_unavailable/execution_unavailable, lienNULL et aucune
invocation supplémentaire ; le curseur a franchi sa fenêtre.

Après restitution explicite confirmée, le même UUID termine sans nouveau POST :
version agent1 connue dans la garde et l'intention, reçu expected1/version2,
opération retirée, donnée identique et cache vidé. Configuration et génération
planifiée sont conservées. À21:00, le tir du même hash réussit, POST/corps{},
donnée conservée et cacheNULL recoupés dans son journal. Un HTTP sain relit ces
valeurs ; le premier tir reste refusé, sans rejeu. Total : deux tirs, trois
invocations réussies (deux HTTP/une planifiée).

La fonction est purgée publiquement ; code/volumes/conteneur/réseau/canal/bail
absents, compteurs nuls, helper et unités terminés. Les34 backends,5982 artefacts,
images/services/démarrages et fichiers officiels sont conservés. Aucun build
produit, UI/manuel ou capture nouveau. La revue préalable a corrigé jonction
SSH, erreurs de flux et chaîne des versions ; leurs pannes propres ne sont pas
prétendues provoquées par cette campagne nominale. Maximum sous HTTP non exclusif,
réutilisation préchauffée, plafond global (SLS-099), rétention, UI et régression
restent à recouper avant clôture078.
