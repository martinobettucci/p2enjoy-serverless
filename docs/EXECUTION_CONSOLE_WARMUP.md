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
