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

## Décision de diagnostic du 21 novembre 2026, avant code

Le recoupement natif après échec confirme les deux tombstones purged, aucun
volume/bail/chemin, conteneur ou réseau appartenant à cette installation, aucun
worker/script ni répertoire de travail temporaire. Compteurs au repos, mêmes
services/images, référence/configuration et5982originaux conservés.

La source montre plusieurs assertions possibles dans le septième groupe :
résultat timeout/handler_started, deux fermetures complètes, relecture de la
valeur écrite. Ni le résultat du timeout ni la ligne de l’exception ne sont
conservés. La deadline commence au dispatch et inclut import/enfant ; son délai
2s ne prouve pas à lui seul que le handler a écrit. Aucune cause précise ne
peut être attribuée à cet essai et aucune durée n’est changée sur cette hypothèse.

Décision réversible : ajouter au seul client un diagnostic allowlisté, avant
assertions. Conserver étape, fichier/ligne/fonction de traceback sans locals,
type d’exception et SHA du message ; projeter uniquement identités, états/codes
fixes, handler_started, durée et indicateurs de nettoyage pour le passage
deadline, plus le booléen de correspondance de la relecture. Aucun log, corps,
configuration ou secret applicatif recopié. Le rapport terminal garde cette
observation et sa cause, au-delà de la seule sortie standard.

Une seule exécution diagnostique complète des14groupes est autorisée après
synchronisation/gel, sans rejeu automatique. Les six groupes antérieurs restent
exclus ; si le défaut ne se reproduit pas, le succès ne prouve aucune cause ni
correction et111reste[~]. Toute correction fonctionnelle attend le diagnostic,
sa décision persistée et ses preuves propres ; les39groupes de qualification
restent dus après correction établie. Aucun changement produit/UI/image.
