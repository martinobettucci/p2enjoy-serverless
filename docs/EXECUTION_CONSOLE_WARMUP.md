# Préparation de la preuve des six instances de console

Contrat de [SLS-105](BACKLOG.md#sls-105), préalable à la campagne complète078.
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
