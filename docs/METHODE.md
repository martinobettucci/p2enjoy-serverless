# Adoption de la méthode

## Provenance

Source : https://github.com/P2Enjoy/software-factory-base ; commit vérifié
`886ba5a28a834a5f08fd1a01ec8dd78787317559`.
La copie locale correspond à ce commit. Les contrats globaux, rôles, hooks et
scripts sont importés dans leurs emplacements opérationnels, sans formation,
son workflow Pages ni son compagnon DESIGN_SYSTEM_APP. Le README et
l'historique du présent projet sont conservés.

`docs/AUTOMATION.md` est présent dans la copie locale mais absent de l'arbre
GitHub de ce commit : provenance locale et empreinte sont consignées
séparément. Il décrit les scripts effectivement importés.

## Application locale

Lire README, CLAUDE et CLAUDE_PROJECT avant d'agir. Les instructions explicites
du responsable priment : DEV uniquement, aucun mock et toutes les fonctions
livrées testées E2E sur les vrais composants. La recommandation générique de
tests unitaires et l'autorisation générique de certains mocks sont remplacées
ici par cette exigence plus stricte. Les contrôles statiques restent distincts.

Une unité suit spécification/backlog, implémentation, preuves ciblées réelles,
revue, traitement des incohérences, campagne complète et documentation.
L'agent principal écrit et opère seul ; les délégations de cette session sont
en lecture seule. Les scénarios sont séquentiels.

`docs/.routine` est le fichier de la méthode, identique octet pour octet à
l'original (blob `715d2d3c1109e84d5a8d1e33edb99245a6a66e46`). Ce dépôt ne
configure aucune planification : la présence du fichier ne lance rien. Une
session déclenchée par `docs/.routine` applique `docs/CloudWorker.md` avec les
adaptations de [CLAUDE_PROJECT.md](../CLAUDE_PROJECT.md#adaptation-de-cloudworker) :
la pile à démarrer, à peupler et à prouver est le SPARK DEV, pas un Docker
local, et les commandes viennent du README.

Le rôle `factory_verifier` est celui de la méthode : exécution et analyse d'une
preuve ciblée sur un arbre stabilisé. Les preuves qui touchent le SPARK DEV ou
tout service partagé restent exécutées par l'agent principal, seul et en série.

## Validation

Les scripts sont exercés avec de vrais dépôts Git temporaires, de vrais hooks,
commits et pushes vers un dépôt bare temporaire local. Aucun serveur Git ni
commande Git n'est simulé. Ces preuves ne modifient pas l'historique du produit.
La qualification applicative s'exécute séparément dans le seul SPARK DEV.

La provenance, les adaptations et les résultats effectifs sont consignés dans
`docs/evidence/`. L'activation des hooks est vérifiée dans Git séparément de
leur présence sur disque.


## Résultat d'adoption

Les 26 fichiers du socle retenus et le complément local AUTOMATION sont présents.
Les empreintes et adaptations sont dans `evidence/factory-import.json`.
Les hooks standard sont activés dans le Git initialisé par le responsable.
Le harnais réel des garde-fous obtient 45 succès et zéro échec. Le remote
`origin` (branche `main`) est configuré ; chaque commit validé est poussé.
La qualification du code est enregistrée indépendamment de cette publication.
