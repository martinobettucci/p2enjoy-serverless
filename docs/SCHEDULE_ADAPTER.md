# Déclenchement après déploiement par l'adaptateur

Contrat de preuve de [SLS-078.7](BACKLOG.md#sls-078), selon
[SCHEDULES](SCHEDULES.md#contrat) et [DEPLOYMENT](DEPLOYMENT.md#commande-deploy).
Décision du11 novembre2026, avant code : le moteur et le retrait du diagnostic
obsolète sont déjà déployés ; éprouver leur raccordement par la véritable CLI.

## Campagne réelle

Deux fonctions originales `cron-enabled` et `cron-disabled` utilisent le handler
`scheduled-capacity.handler` du dépôt,0,05CPU/128Mio, min0/max1, idle0,
deadline10s, stockage partagé et données/cache désactivés. Le manifeste Node24
déclare le même cron `*/5 * * * *`, enabled vrai ou faux. Ajouter l'option connue
privacy à la première pour vérifier que son avertissement reste présent.

Quatre groupes :

1. Vrai processus `python3 -B -m adapter plan --accept-provider-differences` :
   événements normalisés exacts, avertissement privacy présent, aucun diagnostic
   de planification non déclenchée. Contrôler que le manuel canonique décrit
   l'exécution réelle et ne porte plus cette limitation.
2. Avec un jeton Read/Create/Update créé par la vraie session SSO, exécuter
   `adapter deploy` sur un service propre. Le rapport et stderr conservent
   l'avertissement privacy, les deux candidats sont publiés sans promotion.
   Les planifications courantes sont encore vides. UUID/hash recoupés via API.
3. Promouvoir les deux hashes par `adapter promote` avant une vraie frontière W,
   marge80s. À W, un seul tir réel de cron-enabled, succès du hash préparé ;
   cron-disabled ne produit aucun tir ni invocation. Le curseur natif doit
   avoir franchi W, les déclarations exactes restent consultables. Recouper
   POST/corps{}, trigger/slot, UUID et journaux du handler Docker.
4. Révoquer le jeton, attendre les instances, archiver/purger les deux fonctions
   puis retirer les parents par les vraies API. Lecteur natif strict des deux
   UUID : absence physique,5982 artefacts, backend embarqué et services conservés.

Les processus CLI du poste utilisent les sources identiques à celles copiées
sur DEV ; les images CLI sont recoupées sans prétendre une exécution dans ces
images. Aucune nouvelle image, API, UI, variable officielle ou migration.
Chaque relevé est persisté avant assertion ; rapports privés UUID, secrets
uniquement en mémoire des processus, aucun rejeu automatique d'une mutation.
Un échec rejoint ses processus et nettoie les objets déjà créés ; la reprise
ne transforme pas ce premier essai en réussite.

## Résultat qualifié

La [preuve91d4606](evidence/adapter-schedules-dev-2026-11-11.json) passe quatre
groupes sur334sources figées et l'imagec59b8616. Quatre vrais processus Python :
plan, deploy et deux promote. Les deux fonctions restent pilotes avant promotion.
À04:05UTC, le seul cron actif réussit sur son hash publié ; curseur au-delà de W,
déclaration désactivée sans tir ni invocation. POST/corps{}, UUID, trigger/slot
et logs du handler sont recoupés. Le diagnostic privacy est conservé ; aucun
avertissement de moteur absent dans les sorties ou la limitation du manuel.
Deux purges publiques et absence physique,5982 artefacts antérieurs, backend,
services/images/démarrages et fichiers officiels conservés. Aucune image reconstruite,
aucun parcours visuel nouveau. Le critère078.7 est qualifié ; l'unité reste ouverte.
