# Reprise de la qualification du stockage géré

Contrat de [SLS-111](BACKLOG.md#sls-111), préalable au nouveau passage entier078.
Le cinquième worker6b215e89 au gel f7b1d2a /454sources /imageb452 est terminal :
cinq campagnes /148groupes et trois prérequis, puis managed-storage échoue après
six sous-groupes réussis. Suite scellée
ae1704fe3bdfa0a75e1b7273fcf43186c31e28fb336a17d451d1ed98123952e9 ; rapport ciblé
61f05271c69c4de6ab81181c9d1b509fa2d450950bafd2ca407844232a5fa1f9.
MainPID0/exit1, seule unité arrêtée et client exact joint ; aucune preuve543.

## Diagnostic avant décision

Conserver rapport exact, sorties, sources/images, installation temporaire,
identités des deux fonctions, receveurs et nettoyages. Le rapport final déclare
completed=false, cleanup=true,6passed/1failed ; il ne contient pas encore le
message précis de l’assertion. Ne pas inventer sa cause. Un avertissement socket
UNIX isolé est également présent dans ce worker ; ne pas l’attribuer au défaut
sans preuve. Aucun replay avant recoupement des ressources et du nominal.

Lire intégralement e2e/managed-storage.py et les helpers qu’il appelle, puis
[STORAGE_AGENT](STORAGE_AGENT.md), [EXECUTION](EXECUTION.md) et les contrats réellement
concernés par l’assertion. Identifier l’endroit exact du septième groupe, ses
réponses et l’état natif conservé. Recouper le finally et l’installation réelle ;
cleanup=true ne remplace ni l’absence physique des ressources ni la fin des
consommateurs. Persister la cause, les discriminants et le choix réversible avant
la correction. Aucun changement produit présumé pour satisfaire un ancien banc.

## Qualification attendue

Conserver les14groupes complets de managed-storage, leur ordre, allocations,
FUSE, données/cache/quota réels, isolation, concurrence, refus et fautes de
stockage/Docker ; aucune simulation, horloge modifiée, suppression d’assertion,
saut ou relance automatique. Tout défaut produit distinct devient une unité
avant traitement. Corriger le défaut établi avec le minimum de portée utile.

Rejouer le client complet, puis8manual-ui/8public/9login-ui, soit39groupes,
en série sur le seul SPARK DEV et les sources synchronisées/figées. Les six
sous-groupes de cet essai incomplet ne s’ajoutent pas au résultat. Captures
communes fraîches ouvertes individuellement, manuel18/74,38backend/quatreweb
et état natif rapprochés. Vérifier nettoyage physique de l’installation isolée,
terminaison des clients/helpers, mêmes services/images, référence/configuration
et5982originaux conservés. La suite078 reste entièrement à rejouer49/543 +18.
