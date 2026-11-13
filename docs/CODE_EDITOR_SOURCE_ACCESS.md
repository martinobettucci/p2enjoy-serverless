# Droits de source avant publication et sans cible promue

Complément de [SLS-070.2](BACKLOG.md#sls-070), décidé le 13 novembre 2026 avant
son client E2E. Le contrat produit existe déjà dans
[CONSOLE_EDITOR — parcours et droits](CONSOLE_EDITOR.md#parcours-et-droits).
La [preuve de lecture vivante](evidence/code-editor-source-lifecycle-dev-2026-11-13.json)
conserve son époque : révocation pendant IO, propriétaires distincts et purge.
Ce passage ne la réexécute pas et n’en additionne aucun groupe.

## Cas et ressources

Une campagne UUID part de l’accueil puis du vrai SSO administrateur et crée
par API un namespace `code-editor-source-access-<nonce>`, un service de droits
sur les sources, une fonction originale et une seconde fonction de portée.
Le paquet original `code-editor-read-package.py` et son handler Docker sont
réutilisés ; aucune source client ni dépendance de remplacement.

Les jetons restent uniquement en mémoire : Create initial, Read, Update,
Update limité à l’autre fonction et Create nouvellement émis après archivage.
Les jetons Create portent sur tout le service, conformément à TokenCreate.scope ;
Read et Update gardent leur portée par fonction. Le rapport ne conserve que leurs UUID. Les intentions de création sont écrites
avant POST, rapprochées avant nettoyage si une réponse s’est perdue. Les valeurs
SSO entrent sur stdin privée ; aucun en-tête confidentiel ni code ne figure
dans le rapport. L’inspecteur relit SQLite sous UID1001, sans DML ni signal.

## Matrice des droits

Avant publication, Create lit une source vide et crée son brouillon initial ;
Read, Update et l’anonyme sont refusés. Une vraie publication ZIP avec Create
passe la validation Docker ; la promotion administratrice puis l’invocation
Read vérifient le hash et les octets du paquet. L’administrateur et Update
créent chacun leur propre brouillon depuis ce hash.

Les six GET sont éprouvés : `code-sources`, `code-sources/file`, `code-draft`,
`code-draft/files`, `code-draft/file` et `code-draft/diff`. Après publication,
l’administrateur et Update ont leurs vrais résultats ; Create et Read font403,
le jeton de portée étrangère403, l’anonyme401. Chaque refus exige exactement
`{error: texte non vide}`, sans code. Les POST/PUT/DELETE de brouillon et POST
de publication sont aussi refusés à Create et Read, avec de vrais corps et
versions, sans modifier les brouillons ni leurs audits de mutation.

Les mutations administratrices sont éprouvées avec CSRF incorrect, CSRF absent
et origine étrangère, chacune sur les quatre mutations ci-dessus. Les cookies
restent ceux de la vraie session ; les réponses403 et l’absence de mutation
sont exigées. Ces cas ne sont pas présentés comme des profils OIDC négatifs.

## Archivage, restauration et historique

Archiver le seul hash promu avec `disable_default:true` retire réellement la
cible. Le catalogue et la lecture native doivent confirmer l’absence de cible,
le hash archivé et les marqueurs historiques de première publication/promotion.
L’arborescence sans hash réclame un choix explicite. Update et l’administrateur
peuvent encore lire le hash archivé et leurs brouillons personnels.

La même matrice de refus reste exigée, y compris pour le nouveau jeton Create :
la disparition de la cible n’autorise pas l’accès initial. L’invocation Read sans hash est refusée409 (`function_not_deployed`) ;
sur le hash archivé, elle est refusée404 (`version_unavailable`). Restaurer le hash conserve
la cible absente ; le pilote épinglé fonctionne, Create reste refusé. Promouvoir
explicitement le hash rend de nouveau l’appel sans tag fonctionnel. Trois
handlers réussis distincts sont joints à leurs lignes natives et au même hash.

## Preuve et clôture

Sept groupes ciblés : accueil/SSO, Create initial, publication, droits publiés,
CSRF et absence de mutation, retrait/restauration de cible, recoupements natifs.
Puis25groupes communs en série, avec leurs22originaux inspectés. Les sources,
images,38fichiers backend, quatre ressources HTTPS, manuel18/74, configuration,
référence et5982artefacts initiaux sont recoupés avant/après.

Le finally purge les deux fonctions, révoque les cinq jetons, vérifie les fichiers
et brouillons absents, puis supprime les parents et ferme tous les clients.
Un échec reste incomplet et conservé avant correction. Aucun mock, interception,
seed SQL, horloge modifiée ou skip. Aucun changement produit, UI, manuel, schéma,
route ou configuration n’est requis par ce complément.

Le replay et ses régressions sont qualifiés ci-dessous ; le rapprochement avec
les droits pendant IO permet de clôturer070.2.070.1/.3/.4/.5 et la campagne
complète gardent leurs exigences propres.

## Premier passage et correction de préparation

Le [premier passage](evidence/code-editor-source-access-scope-failed-dev-2026-11-13.json)
au gelc40626f passe le SSO puis reçoit422 sur le premier jeton Create : le
client lui attribue function_ids malgré le contrat de portée service. Deux
fonctions sans révision sont purgées, parents supprimés ; aucun jeton, handler
ou groupe qualifié. Sources/image,38backend/quatreweb, configuration, référence
et5982artefacts sont conservés.

Décision avant correction : omettre function_ids pour les deux jetons Create.
La portée de Read/Update et le cas Update limité à l’autre fonction restent
inchangés. Le refus422 est conforme ; le produit n’a pas à changer.

## Second passage : absence de cible distincte du hash indisponible

Le [second passage](evidence/code-editor-source-access-default-status-failed-dev-2026-11-13.json)
au gel0e99bea passe cinq groupes et les matrices sans cible, puis attend404
à tort sur l’appel sans hash. Son message d’assertion correspond exactement
au digest de409/404 ; execution.snapshot et declared_path portent déjà409
function_not_deployed. Le hash archivé conserve son404 version_unavailable.
Un handler réussi, deux fonctions/cinq jetons/deux parents nettoyés ; baseline
conservée, zéro groupe qualifié. Aucun résultat partiel ne s’ajoute au replay.

Décision avant correction : exiger ces deux statuts et codes publics distincts,
les enregistrer avant l’assertion, puis poursuivre restauration/pilote/promotion.
La distinction existante ne requiert aucun changement produit.

## Qualification DEV du 13 novembre 2026

Les [droits d’accès aux sources](evidence/code-editor-source-access-dev-2026-11-13.json) passent **32 groupes réels** :
7 ciblés puis 25 communs, sur 420 sources `70f21df4` et l’image `b452ef16`.
Les matrices couvrent 78 cas de lecture (24 admis, 54 refusés) et 32 mutations
refusées sans effet, dont 12 pour les variantes CSRF. Create reste refusé après
retrait de cible, même nouvellement émis ; restauration, pilote et promotion
sont distincts. Trois handlers Docker et 22 captures communes sont recoupés.
Les trois passages sont nettoyés : six fonctions, dix jetons et six parents ;
les deux échecs gardent zéro groupe qualifié. Les 5 982 artefacts, configurations,
services et manuel 18 chapitres/74 paragraphes sont conservés.
**070.2 est clôturé**, avec la preuve antérieure de droits pendant IO conservée
sans réaddition. 070.1/.3/.4/.5 restent ouverts pour ZIP, attentes UI et reprises.

Le gel84e3dd37 est identique avant/après chaque phase, incluant les images CLI.
Les deux matrices contiennent36 puis42GET ; les cinq séries de mutations
refusées contiennent8/4/4/4/12cas. Chaque série recoupe fonctions, brouillons,
audits de mutation, révisions, versions et candidats natifs sans changement.
Les refus sans cible409/function_not_deployed et épinglé404/version_unavailable
sont conservés explicitement dans le rapport avant assertion.

Le catalogue et SQLite confirment l’historique et l’absence de cible après
archivage ; la restauration garde cette absence avant le pilote puis promotion.
Les trois handlers réussis sont joints au même hash. Sept threads libres,
compteurs globaux nuls, intégrité/FK et dix migrations sont recoupés au final.
Les seize JPEG ont leur SHA déclaré ; les six PNG ont leurs SHA actuels et
fraîcheur de phase. Les22originaux sont ouverts individuellement, Git propre
avant/après ; aucun nouveau parcours UI ciblé n’est déduit de ces images.

Les46sources control de la preuve30 sont identiques à ce passage : routage,
authentification, éditeur, modèles et émission des jetons compris. Cette preuve
liée garde ses propres groupes et les scénarios IO/purge effectivement joués.
Aucun endpoint d’export ZIP source n’est livré ; les sixGET de code/brouillon
refusent Read. Le complément qualifie070.2 sans clôturer l’ensemble de070.
