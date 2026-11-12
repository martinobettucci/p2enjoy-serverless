# Éditeur de code et brouillons persistants

Contrat de réalisation [SLS-070](BACKLOG.md#sls-070), décidé le11 novembre2026
avant code. Complète [CONSOLE_USABILITY](CONSOLE_USABILITY.md#éditeur-de-code-et-handler)
et le parcours courant de [publication par hash](FUNCTION_VERSION_EXECUTION.md).
Le serveur et la migration010 sont déployés et partiellement qualifiés en DEV
par [45groupes réels](evidence/code-editor-server-dev-2026-11-12.json). La première facette console est déployée et partiellement qualifiée sura77b6b4e.
Les critères070.7 et070.8 sont clôturés ; les autres restent ouverts.
La campagne de capacité réelle est détaillée dans
[CODE_DRAFT_CAPACITY](CODE_DRAFT_CAPACITY.md), décision avant son client E2E.

## Parcours et droits

La fiche de fonction possède une facette **Éditeur**, distincte de **Code et
révisions**. Elle présente la version source choisie, la cible promue et le
brouillon personnel enregistré. Depuis une carte de version, **Modifier ce code**
sélectionne son hash ; une version archivée conservée peut servir de base.
Une version supprimée ne peut pas devenir une nouvelle base. Sans cible sur une
fonction déjà publiée, choisir explicitement un hash conservé. Seule une
fonction jamais publiée peut commencer avec un code vide.

Toutes les routes de source, fichier, diff et brouillon exigent le droit de
publication : Create si aucune révision historique n'existe, Update sinon,
ou une session administratrice. Une cible désactivée ne rétablit pas Create.
L'authentification et la portée sont contrôlées avant toute lecture de source,
puis revérifiées sur la transaction utilisée. Read seul reste refusé, y compris
par requête directe et pour les téléchargements éventuels. Une fonction ou son
parent supprimé, une purge ou une opération de stockage incompatible interdit
l'accès. L'éditeur ne reçoit aucune valeur de variable ou secret applicatif.

Un brouillon appartient à `(fonction, type d'acteur, identité stable)` : subject
SSO pour une personne, UUID du jeton pour un accès technique. Un seul par cette
clé. Deux onglets du même compte retrouvent le même brouillon ; un autre acteur
ne le lit pas. Révoquer un jeton retire son accès sans transférer sa propriété
au jeton de remplacement. Les administrateurs retrouvent leur propre brouillon,
sans liste des brouillons privés d'autrui dans cette facette.

## Source, limites et modifications

L'arborescence reprend l'inventaire immuable validé. Dossiers et fichiers sont
parcourus par chemin, avec pagination, recherche de chemin et total. Le fichier
ouvert indique sa taille, son empreinte, son caractère exécutable et son
appartenance éventuelle à `node_modules`. Les dépendances sont de vrais fichiers
conservés ; aucune installation automatique de paquet n'est annoncée.

Un texte UTF-8 d'au plus1Mio s'édite ; octets nuls, contrôles hors tabulation/
CR/LF ou UTF-8 invalide sont traités comme binaires. Un fichier plus gros est
identifié hors limite d'édition, jamais chargé en entier dans la zone de texte.
Les binaires et gros fichiers non modifiés sont intégralement conservés lors de
la publication. Les fichiers texte peuvent être ajoutés, modifiés, retirés ou
rétablis depuis la base. Un fichier nouveau a le mode0444 ; une modification
conserve le bit exécutable de sa base. Les retours à la ligne et le dernier
caractère sont conservés exactement. Aucun fichier publié n'est édité sur place.

Les chemins suivent exactement les bornes de l'extracteur : relatifs POSIX,
512octets, segment255octets, aucun segment vide/dot/dotdot, drive, antislash ni
contrôle. Pas de normalisation Unicode silencieuse. Les collisions fichier/
dossier sont refusées avant enregistrement. Un nom ne peut jamais devenir un
chemin hôte arbitraire ; chaque composant est ouvert sans suivre de lien.
La taille et le SHA réels d'un fichier sont recoupés avec l'inventaire.

Bornes propres à l'éditeur :

| Grandeur | Borne |
| --- | --- |
| Fichier texte modifié | 1Mio UTF-8 |
| Modifications conservées par brouillon | 128chemins et4Mio de texte UTF-8 |
| Brouillons | 128globaux,32par acteur |
| Payloads chiffrés conservés | 64Mio globaux, comptés sur les octets réellement stockés |
| Corps d'enregistrement | 8Mio, seulement après autorisation serveur ; autres JSON inchangés à256Kio |
| Page d'arborescence ou de diff | 1–100éléments,25par défaut |
| Recherche de chemin | 200caractères |
| Lectures de source / reconstructions simultanées | 4lecteurs,1reconstruction de ZIP |
| Diff textuel | 2000lignes par côté,128Kio de résultat ; dépassement explicitement signalé |

Le ZIP reconstruit reste soumis aux bornes communes :64Mio compressés,256Mio
extraits,20000entrées et répertoires calculés. Ses écritures sont bornées avant
allocation au-delà de64Mio. Le module standard
[zipfile Python3.14](https://docs.python.org/3.14/library/zipfile.html) écrit du
DEFLATE classique sans ZIP64 ; les modes et octets conservés sont repris, les
métadonnées de transport n'entrent pas dans l'identité canonique. Il n'ajoute
aucune dépendance. La réservation et la marge de1Gio restent celles du pipeline.
Les sauvegardes de brouillon gardent aussi cette marge avant une écriture WAL.
La capacité des quatre lecteurs est acquise avant réception du JSON autorisé ;
la réception et son décodage disposent de 30 secondes. Une admission refusée ne
lit pas le corps et un dépassement renvoie408. La garde est libérée après
annulation/jonction, afin de borner aussi les gros enregistrements concurrents.

## Persistance, concurrence et conservation

La migration additive010 crée `code_drafts` : UUID, fonction, acteur, révision
de base nullable uniquement pour un départ vide initial, version de fonction
observée à la création, descripteur de base, handler courant, changements
chiffrés, octets de texte, compteur de version du brouillon, dates, dernier UUID
candidat et version de brouillon publiée. La clé propriétaire est unique ; une
référence de base doit appartenir à la même fonction. Aucun seed SQL d'identité,
code ou exécution n'est injecté pour les preuves.

Le chiffrement réutilise le Vault et la clé de cellule. Le navigateur ne
persiste pas le code dans localStorage, sessionStorage, cookie ou URL. Une
réponse perdue ne supprime pas la saisie. Relire le brouillon permet de comparer
la version et le contenu enregistrés ; aucune écriture n'est rejouée en silence.
Un enregistrement réellement inchangé ne modifie ni version ni date et renvoie
`changed:false`. La confirmation de l'interface distingue ce cas d'une écriture.

La version du brouillon est indépendante de l'ETag de fonction : une publication
code-only ne change pas ce dernier. `If-Match` du brouillon empêche l'écrasement
entre onglets. Un conflit409 conserve les saisies locales et propose de relire
la version serveur. Il n'y a ni fusion silencieuse ni rebase automatique.
Une promotion ou modification concurrente de fonction garde son propre conflit
d'ETag pendant la publication. Le diff prend la cible promue **actuelle**, pas
seulement la base historique du brouillon ; les deux hashes sont nommés.

Une ligne de brouillon retient sa révision de base, même si le hash est ensuite
supprimé : ses nouvelles invocations restent refusées, ses octets restent
comptés jusqu'à abandon du brouillon. Les lectures et reconstructions vivantes
retiennent brièvement leurs fichiers. Le nettoyage général et la purge
respectent ces lecteurs ; le compteur est acquis avant toute attente et libéré
après jonction réelle des travaux hors boucle HTTP. Il n'est pas un verrou SQL
maintenu pendant les entrées/sorties. Un redémarrage conserve les références
persistantes de brouillon ; il ne reprend aucune publication automatiquement.

La purge confirmée d'une fonction supprime ses brouillons et leur contenu
chiffré dans sa décision SQL, puis conserve le protocole de purge existant.
Elle rejoint les lecteurs avant l'effacement physique. Une simple suppression
avec archivage conserve les brouillons dans cette archive ; leurs sources ne
redeviennent pas accessibles par les routes de fonction vivante. Abandonner un
brouillon retire sa rétention ; la maintenance normale reprend le nettoyage
d'une version supprimée. Le budget d'artefacts inclut déjà ces octets retenus.
La copie complète de chaque ZIP dans SQLite est écartée : elle dupliquerait les
dépendances et allongerait les écritures sous le verrou commun sans utilité.

## API

Préfixe `/api/functions/{UUID}`. Les réponses ne divulguent ni l'identité des
autres propriétaires ni le contenu d'un fichier non demandé. Tous les modèles
sont stricts. Les mutations administratrices exigent l'origine et le CSRF.

| Méthode et suffixe | Contrat |
| --- | --- |
| GET `code-sources` | `version` hash optionnel, `directory` relatif ou vide, `search`, `limit`, `offset`. Source promue par défaut, ou `selection_required` sans cible sur une fonction déjà publiée. Retour : descripteur, hashes sélectionné/promu, versions conservées et page de dossiers/fichiers. |
| GET `code-sources/file` | Même sélection, `path` obligatoire. Métadonnées et texte si éditable ; sinon raison binaire/hors limite, sans faux contenu vide. |
| GET `code-draft` | Brouillon personnel nullable, version, dates, base, handler, dernière publication, contexte actuel de fonction. Aucun contenu de fichier dans ce résumé. |
| POST `code-draft` | `base_code_hash` nullable ; `If-Match` de fonction obligatoire. Crée depuis le hash explicite ou le départ vide initial.201 ;409 si un brouillon existe ou si le contexte a changé. |
| PUT `code-draft` | `If-Match` de brouillon. Handler optionnel et au plus une mutation de fichier `{action:write/delete/revert,path,text?}`. Authentifier avant de lire le corps borné. Retour : résumé actualisé et `changed`. |
| DELETE `code-draft` | `If-Match` de brouillon. Abandon explicite confirmé ; ne retire aucun code déployé. |
| GET `code-draft/files` | Page de l'arborescence effective base+modifications, mêmes paramètres et bornes de navigation. |
| GET `code-draft/file` | `path` obligatoire. Contenu effectif d'un seul fichier selon les mêmes bornes. |
| GET `code-draft/diff` | Comparaison avec la cible promue actuelle ; page de chemins ajoutés/modifiés/retirés. `path` optionnel fournit le diff textuel borné et les deux descripteurs. Binaires/gros textes restent représentés par leurs métadonnées et un motif. |
| POST `code-draft/publish` | `deployment_id` UUID produit par le client, `draft_version` attendu ; `If-Match` de fonction. Reconstruit l'instantané enregistré puis prépare et envoie son vrai ZIP par le pipeline existant. Aucun octet non enregistré n'est publié. |

`401/403` refusent identité ou droit ; `404` une ressource/une version non
consultable ; `409` un conflit, une base retirée pour une nouvelle création ou
un UUID déjà utilisé ; `413` une borne de contenu ; `422` chemin, handler ou
structure invalides ; `428` un If-Match absent ; `429` capacité occupée ; `507`
budget de brouillon/artefact ou marge disque insuffisants. Les erreurs ne
réaffichent jamais un corps de code ou une valeur confidentielle.

## Publication et réponses perdues

L'UUID candidat est placé dans l'adresse de l'éditeur **avant** le POST. Il
permet la consultation normale par GET candidat après réponse perdue. Le
brouillon et le candidat restent distincts. La préparation attache atomiquement
le candidat et la version de brouillon à sa ligne, après recontrôle de ses
versions et droits. Un changement entre reconstruction et préparation donne409,
sans candidat créé. Une fois préparé, le ZIP en mémoire est un instantané ; une
modification ultérieure du brouillon ne change pas cet envoi.

La reconstruction s'exécute hors boucle HTTP, sous une capacité unique et une
garde de lecteur. Sa mémoire ZIP est plafonnée ; il n'y a pas de dossier
intermédiaire non réservé à réconcilier. Après reconstruction, le véritable
`Deployments.upload` consomme ces octets en flux et garde ses admissions,
réservations, extraction, validation Docker, recontrôles et décisions durables.
Le handler et les événements viennent de la base choisie avec le handler édité ;
configuration, variables, secrets et volumes restent courants. Aucune copie de
Request ni dépendance substituée ne contourne l'autorisation du pipeline.

Le contrôle ne change ni cible active ni ETag de fonction sur cette publication
code-only. Paquet inchangé : même hash/révision canonique après validation ;
changement réel : nouvelle version disponible par hash. Un import refusé garde
cible et brouillon, avec les vrais diagnostics du candidat. Archive/restauration
et réimportation d'un hash supprimé conservent leurs gestes explicites existants.
Le runtime et l'image de validation courants restent contrôlés par le pipeline ;
un changement d'image peut légitimement changer l'identité d'exécution.

Après perte de réponse ou rechargement, consulter le même candidat, sans refaire
POST ni envoi. Une préparation restée seule s'abandonne explicitement avant une
nouvelle tentative ; le serveur ne reconstitue pas une ancienne saisie perdue.
Après SIGKILL, receiving/validating échouent et se nettoient par la reprise
courante, le brouillon enregistré et la cible antérieure restant intacts.

## Interface et preuves

L'éditeur est une surface de travail explicitement ouverte, avec mode lecture
puis **Modifier** le fichier/handler. L'arborescence et le contexte restent
visibles ; les saisies et leurs commandes ne se confondent pas avec le code
déployé. L'écart au §6.27 pour l'édition de source sur place plutôt qu'en modale
est documenté dans le design du produit : cette surface possède une destination
propre et doit permettre la comparaison avec les fichiers du même brouillon.
Ajout de fichier, modification du handler et abandon recueillent leurs
paramètres/confirmations dans les composants existants, sans modales imbriquées.

Recherche dans le fichier, sélection de résultat, diff et diagnostic sont
utilisables au clavier. Les états chargement, vide, non sélectionné, binaire,
hors limite, refus, conflit et envoi sont explicites. Une saisie non enregistrée
est signalée avant changement de fichier, navigation ou fermeture. Sur mobile,
arborescence et zone de texte s'empilent, le code défile localement ; aucun
contenu essentiel n'est caché pour faire tenir le desktop. Une requête incertaine
n'est jamais rejouée automatiquement. Les confirmations nomment fonction et
hash lorsqu'une promotion ou un rollback est engagé.

Après publication, les parcours donnent les adresses du hash, promotion explicite
et retour à un hash. **Tester la version publiée** ouvre la facette071 sur ce
hash ; le [complément46](evidence/function-http-client-ui-admission-dev-2026-11-12.json)
suit réellement ce lien après validation Docker et invoque son code. Avec les
promotions/pilotes/retour A de la tranche43,070.6 est qualifiée. Les autres
critères ouverts de070 gardent leurs preuves propres.

Les preuves E2E créent des fonctions originales CJS/ESM par les vraies API et
formulaires, avec vraie dépendance packagée et fichier binaire. Elles vérifient
Read refusé, Create/Update et portées, versions obsolètes, chemin interdit,
1Mio exact/+1,128changements/+1,4Mio/+1 et capacité des brouillons ; conservation
des octets/modes/dépendances au hash inchangé, diff, reprise entre onglets,
publication puis invocation Docker, import réellement cassé, pilote/promotion/
rollback, perte de réponse et SIGKILL. Les captures partent de l'accueil et du
vrai SSO, sur ordinateur/mobile, et sont inspectées. Sources/images et nettoyage
physique sont recoupés ; aucun mock, serveur de remplacement ou test ignoré.
La validation de chaque borne représente sa propre preuve ; les preuves qui
manquent maintiennent l'unité ouverte. Le manuel canonique, la parité et la
fixture éditable sont mis à jour avec le comportement effectivement livré.

## Réalisation en cours

Le serveur `control/app/code_editor.py` expose les sources, patches chiffrés,
diffs et publication par le pipeline réel. La migration010 est appliquée
sur DEV, avec sauvegarde native préalable et intégrité vérifiée. Le client `e2e/code-editor.mjs` prépare une campagne propre, avec
lecture native limitée à son namespace et dépendance YAML2.9.1 issue du
conteneur de référence inchangé. Les fixtures CJS/ESM sont dans le dépôt.
Le résultat de première tranche est consigné ci-dessous. Les quotas globaux,
la concurrence purge/lecture, les interruptions et l’interface restent à qualifier.

### Investigation de réception partielle —12novembre2026

Le premier passage a réussi12groupes puis échoué au13e sur le délai socket
client45s. Les logs natifs portent un429 et quatre408, sans erreur serveur ;
ils ne remplacent pas les réponses HTTPS absentes du rapport. Les deux fonctions
sont purgées et l’intégrité physique est recoupée. Le défaut est enregistré
sous070.7, sans clôture des bornes de réception.

Le client de preuve utilisera un vrai socket TLS vérifié avec une requête
HTTP/1.1 explicite, Connection:close, Content-Length8Mio et zéro octet de corps
pour la cinquième demande. Il lira les en-têtes et la longueur réelle de réponse
sous64Kio, avec délai45s et jonction de tous les sockets. Cela évite de faire
dépendre la lecture d’un ClientRequest Node dont l’envoi reste volontairement
incomplet. Aucun serveur, réponse, horloge ou dépendance n’est substitué ; la
passerelle HTTPS et l’API déployées restent effectivement traversées. Toute
absence de réponse demeure un échec et impose une nouvelle investigation.

## Première tranche serveur qualifiée —12novembre2026

La [preuve DEV](evidence/code-editor-server-dev-2026-11-12.json) lie367sourcesa983b2f et l’image7c5c6f4b,
36fichiers serveur embarqués et quatre ressources HTTPS identiques avant/après.
20groupes ciblés puis8manuel/8public/9connexion passent strictement en série.
Huit invocations réussies ont leurs lignes natives, quatre publications réussies
et un import réellement cassé ; les candidats sont terminaux et leurs valeurs
confidentielles/diagnostics purgés selon le contrat de purge. Les deux fonctions
du passage réussi et les deux du premier échec sont purgées physiquement.

Le paquet original contient238fichiers, YAML2.9.1 réel, Unicode, CRLF, texte
sans fin de ligne, binaire et bit exécutable. La reconstruction inchangée retrouve
le même hash et la même révision ; le pilote, sa promotion, le rollback et ESM
sont réellement invoqués. Les bornes1Mio/+1,4Mio/+1 et128chemins/+1 passent ;
Read/Create historique/portée/CSRF, conflit, no-op et rechargement sont éprouvés.
Une base supprimée reste intégralement lisible et comptée via les brouillons,
puis son abandon libère effectivement les fichiers. Les purges retirent aussi
le brouillon Create initial devenu inaccessible après publication.

Les cinq requêtes TLS exactes ont leurs refus natifs : cinquième429 en107ms,
zéro octet de corps envoyé ; quatre408 entre30,140 et30,197s. Le premier client
ClientRequest avait expiré45s malgré les refus enregistrés côté serveur : son
échec est conservé et n’est pas compté dans les45groupes. Le client TLS corrigé
lit de vraies réponses complètes et joint toutes ses connexions.

Les22captures de régression sont inspectées individuellement :16JPG liés par
SHA déclaré,6PNG liés par leurs octets actuels et leur fraîcheur dans la phase
login (le rapport login ne déclare pas leur SHA). Aucun défaut visuel bloquant ;
ces vues ne qualifient aucune facette Éditeur. Le manuel reste16chapitres et
57paragraphes, inchangé et effectivement servi. Aucun contenu d’éditeur annoncé
à tort dans ce guide. Les5982artefacts antérieurs, la référence et les fichiers
officiels sont conservés ; contrôle/stockage sains, zéro ressource active.

Restent à livrer/éprouver : interface complète, recherche dans le fichier et
avertissements de saisie, lien Tester071, quotas128globaux/32acteur/64Miochiffrés,
corps JSON8Mio/+1, ZIP64Mio/256Mio/20000entrées aux bornes, fichier hors limite
conservé, diff2000lignes/
128Kio aux bornes, sélection archivée, révocation en cours de lecture, publication
perdue/SIGKILL et reprise de brouillon après redémarrage, purge sous lecteur vivant,
fixture proposée dans la console et campagne complète de régression. Les critères
070.1–.6 restent ouverts ; cette tranche ne prétend pas clore SLS-070.

## Détail de la facette console —12novembre2026, avant code

La route est `/console/functions/{UUID}/editor`. La navigation de fonction et
les cartes de versions disponibles ou archivées proposent **Éditeur** ou
**Modifier ce code**. `version=HASH` sélectionne explicitement une source en
lecture. Sans sélection explicite, le brouillon personnel existant est ouvert ;
sinon la source promue, ou le départ vide initial. `view=source|draft` conserve
le choix de surface, `file=CHEMIN` le fichier ouvert, `deployment=UUID` le suivi.
Ces paramètres ne contiennent jamais de code ni d’identifiant d’accès. Ils sont
remplacés dans l’adresse sans ajouter d’entrées intermédiaires à l’historique.
Le retour validé du catalogue est conservé. Le contexte courant reste monté
pendant les relectures : aucun reload parent ne démonte une saisie inline.

Les sections sont : contexte source/brouillon/cible, fichiers et contenu,
comparaison du brouillon enregistré avec la cible, puis tentative suivie.
Le choix de source est un dialog avec versions paginées par cinq ; supprimée
n’est jamais choisissable. L’arborescence et le diff sont également paginés par
cinq. Recherche de chemin explicite, navigation de dossiers et sélection de
fichier restent distinctes de la recherche littérale dans son texte.
Une base différente ne remplace jamais un brouillon existant : ouvrir celui-ci,
ou l’abandonner explicitement avant de créer une autre base.

Le fichier s’ouvre en lecture ; **Modifier le fichier** active la saisie.
**Enregistrer le fichier** sauvegarde son seul contenu dans le brouillon.
Le compteur porte sur les octets UTF-8, au plus1Mio ; l’état distingue saisie
locale, brouillon enregistré et code publié. Ajouter un fichier demande son
chemin dans le dialog existant, crée un texte vide puis permet son édition.
Le handler possède son propre dialog. Retirer un texte, le rétablir depuis la
base et abandonner le brouillon demandent leur confirmation nommée. Aucun
bouton d’installation de dépendance n’est annoncé. Après publication réussie,
le lien Tester071 utilise le hash effectivement publié.

Un textarea utilise des LF pour sa valeur API, selon le
[standard HTML](https://html.spec.whatwg.org/multipage/form-elements.html#the-textarea-element).
Le modèle conserve donc le texte exact séparément de cette représentation :
chaque modification identifie préfixe/suffixe inchangés dans la vue normalisée,
les rattache à leurs positions dans le texte original et n’y remplace que la
portion éditée. Les fins de ligne existantes restent exactes, même mixtes ;
les nouvelles suivent la première forme rencontrée, LF pour un nouveau fichier.
Aucune fin de ligne n’est ajoutée implicitement à la fin du fichier. La preuve
passe par une vraie saisie navigateur puis relecture API/invocation, jamais par
un import du calcul client présenté comme E2E.

Une garde commune demande confirmation avant de perdre une saisie lors d’un
changement de fichier/source/surface, d’un lien de navigation ou d’une déconnexion.
Elle utilise un dialog natif unique ; annuler garde texte et focus. Rechargement,
retour navigateur et fermeture utilisent aussi beforeunload natif. Les liens
internes de défilement ne quittent pas la surface. Aucun code n’est persisté
dans le stockage web. La déconnexion consulte la garde **avant** d’appeler le
serveur. Les enregistrements en cours conservent les nouvelles frappes ; seule
la valeur effectivement confirmée devient le contenu enregistré de référence.

Un conflit ou une écriture incertaine conserve la saisie et bloque sa répétition.
**Relire le brouillon serveur** récupère son résumé et son fichier sans écraser
le texte local. Pour repartir d’une version différente, un geste explicite
adopte la version relue, ou remplace la saisie par le contenu serveur après
confirmation. Il n’y a ni fusion silencieuse ni changement de base automatique.
Une réponse sans changement affiche **Contenu déjà enregistré**.

La publication concerne seulement le brouillon enregistré et demande une
confirmation nommant fonction, base et handler. L’UUID est inscrit avant POST,
y compris lorsque la reconstruction n’a pas encore créé de candidat. Un404
pendant la requête signifie **Préparation en cours**, pas un nouvel envoi.
Après une issue incertaine, relire le même UUID, sans POST automatique. Une
préparation orpheline se consulte et s’abandonne par la vraie API. Le composant
candidat existant fournit états et diagnostics ; les adresses du hash et la
facette Code et révisions donnent pilote, promotion et rollback réels.

Disposition : arborescence de largeur240px (token de navigation existant) et
contenu flexible sur grand écran, sections empilées sous1024px. Le textarea
possède une hauteur de lecture locale26rem, police mono, fond distinct en
lecture seule, défilement local signalé quand nécessaire. Noms et hashes
complets reviennent à la ligne. Les champs de recherche ont leur libellé ;
Précédent/Suivant sélectionnent l’occurrence et nomment sa ligne/colonne.
Le manuel ajoutera un chapitre propre avec cette réalisation. Aucune API,
migration, dépendance ou variable de cellule nouvelle.

### Corrections issues de la revue de console —12novembre2026

La relecture relève quatre défauts avant preuve UI : copie serveur réutilisable
sur un autre chemin, publication autorisée pendant résolution d’un UUID suivi,
absence de rétablissement d’un chemin retiré et ambiguïté des fins de ligne
identiques. Aucun de ces parcours n’est déclaré qualifié.

La copie relue est liée à sa surface, son chemin et une génération de lecture.
Un changement de fichier ou de surface invalide cette copie ; une réponse tardive
ne peut plus être adoptée. Toute tentative sélectionnée interdit une publication
pendant son GET et tant que son état reste inconnu ; fermer le suivi attend aussi
la fin de cette lecture. Le diff propose le rétablissement confirmé d’un chemin,
y compris retiré, avec le même If-Match et sans modifier les autres patches.

Le calcul de texte utilise d’abord la sélection et le type de l’événement natif
beforeinput, pour rattacher la plage effectivement remplacée aux octets originaux.
C’est nécessaire lorsque plusieurs fins de ligne visibles sont identiques : le
préfixe/suffixe seul ne distingue pas laquelle a été supprimée. L’historique des
valeurs exactes reste en mémoire pour les gestes natifs annuler/rétablir. La
preuve comporte une suppression dans `a\r\n\nb`, une saisie sur les lignes
mixtes et une relecture des octets enregistrés. Aucun contenu n’est persisté par
le navigateur. Les contrôles statiques/build précèdent une campagne UI réelle.

### Premier parcours navigateur interrompu avant édition

Le premier essai de console échoue au premier groupe dans le client de preuve :
Chromium ne conserve plus le corps du POST après la navigation de création.
Zéro groupe acquis. Le namespace créé est à rapprocher explicitement puis retirer.
Le pilote doit persister chaque intention de création avant le POST, lire statut
et URL effectivement atteinte puis l’objet par sa vraie API. Le nettoyage relit
ces intentions, y compris si l’affectation locale n’a pas fini ; un booléen de
nettoyage sans ce rapprochement n’est pas une preuve. Aucun produit modifié par
cette correction du banc ; le premier rapport reste conservé hors des succès.

Le second passage passe le groupe de formulaires mais s’arrête sur le corps de
la réponse d’upload, évincé du cache d’inspection Chromium. Sa fonction est
purgée et ses trois intentions rapprochées ; aucun groupe d’éditeur acquis.
Les observations de mutation liront statut et URL sans corps Chromium, puis
reliront le candidat ou le fichier par la véritable API canonique. Les réponses
GET du client API et les octets relus restent les autorités de comparaison.

Le troisième passage passe huit groupes et quatre handlers réels puis s’arrête
sur l’hypothèse du client selon laquelle la première URL copiée porterait le
domaine de console. Le catalogue classe les routes officielles : l’alias
functions.lelabs.tech est légitime. La preuve compare désormais la copie à
l’entrée exacte du catalogue courant, HTTPS et chemin/hash, puis l’invoque.
La fonction et ses deux révisions sont physiquement purgées ; cet essai reste
séparé du replay et ne clôture aucun critère.

### Historique exact borné —décision avant correction

La seconde revue confirme les quatre corrections mais relève qu’une copie
intégrale par frappe alloue une mémoire non bornée. L’historique conservera
uniquement les différences exactes (position, texte retiré et inséré), au plus
64 gestes et8Mio de caractères UTF-16 comptés à deux octets par unité, cumulés
sur annulation/rétablissement. Les états les plus éloignés sont retirés en
premier. Le texte courant et les buffers natifs de Chromium restent distincts.

Un undo/redo natif peut regrouper plusieurs frappes. Le modèle rejoue ses
patches en mémoire jusqu’à retrouver exactement la représentation visible
obtenue par le navigateur. Si ce geste dépasse l’historique disponible, il
conserve le texte exact précédent, le réaffiche et annonce la limite ; aucune
normalisation approximative n’est enregistrée. Compteurs et avertissement sont
visibles dans la surface d’édition. Une nouvelle lecture/adoption de fichier
réinitialise cet historique. La preuve vérifie les annulations natives déjà
prévues,64 gestes/+1, la borne mémoire et le contenu relu par la vraie API.

Le quatrième essai UI s’arrête sur la demande hors borne `limit=100` du client
pour le catalogue d’adresses (borne réelle20) ; huit groupes acquis seulement
sur cet essai, objets purgés. La consultation de recoupement utilisera la même
page5 que la console. Ce défaut de banc et le changement d’historique imposent
un nouveau gel de sources et une nouvelle image, sans addition des essais.

### Replay serveur : sondage concurrent du quatrième lecteur

Le replay de serveur sura77b6b4e passe12groupes puis échoue au sondage de
capacité `four_readers_not_admitted`. Deux fonctions sont purgées et l’intégrité
native passe. Les refus natifs de son intervalle portent un429 PUT code-draft,
sans les quatre408 attendus ; ce résultat ne qualifie pas cette fenêtre.

Par lecture du code, le GET code-sources utilisé comme sonde acquiert lui-même
un lecteur. Il peut donc prendre la quatrième place avant un PUT partiel et
faire refuser celui-ci : le banc perturbe sa propre admission. Le correctif
attendra la fin d’écriture TLS des quatre en-têtes/premiers octets puis ouvrira
la cinquième connexion, sans GET consommateur. Seules les cinq réponses complètes
font preuve : cinquième429 sous5s sans corps, quatre408 entre29 et40s, puis
lecture normale et purge. Aucun refus n’est remplacé/réessayé automatiquement.
Les observations et échecs précédents restent conservés ; le backend ne change
pas. Les12groupes UI acquis au gel48e0f1f restent leur époque distincte.

## Première facette console qualifiée —12novembre2026

La [preuve](evidence/code-editor-console-dev-2026-11-12.json) contient57groupes réussis, strictement en série :
12parcours UI au gel48e0f1f puis20serveur et25régressions au gelde56dfc.
Les370sources de chaque époque sont recoupées avant/après. Seuls le client
code-editor.mjs et ce contrat changent entre les deux ; les sources produit,
le manuel servi et l’imagea77b6b4e restent identiques. Les cinq premiers essais
échoués ne s’ajoutent pas aux57groupes ; leurs ressources sont rapprochées.

La console passe les vrais formulaires/SSO, arborescence5+pagine, binaire,
dépendance YAML2.9.1, EOL mixtes, suppression ambiguë et undo/redo, absence de fin
ajoutée,65gestes→64retenus, neuf textes1Mio→8Mio exacts de patches, garde avant
fichier/source/lien/logout/reload, conflit409entre deux onglets et invalidation
A→B, ajout/refus de chemin, retrait/revert isolé, no-op et déduplication. Pilote,
URL officielle copiée/invoquée, promotion/rollback, handler ESM et import cassé
sont éprouvés. Neuf appels UI et huit serveur sont recoupés nativement ; quatre
publications et un import refusé pour chacune des deux campagnes ciblées.

Le replay serveur sans sonde consommatrice reçoit le cinquième429 en132ms,
zéro octet envoyé, et quatre408entre30,115 et30,148s ; les cinq UUID ont leurs
refus natifs. Son premier replay échoué reste distinct. Le paquet courant a
240fichiers originaux/dépendance, dont les deux nouvelles fixtures de lignes.
Huit fonctions de tous les essais sont purgées physiquement ; le premier
namespace vide a sa correction de nettoyage distincte. Les5982artefacts
antérieurs et leurs SHA, les fichiers officiels et la référence sont conservés.
Dix migrations, intégrité, clés étrangères et actifs nuls ont leur reçu explicite.

Les41images inspectées sont12captures Éditeur,22régressions et7lectures du
chapitre nouveau. Les35JPG ont leurs SHA déclarés ; les6PNG de connexion sont
liés à leurs octets actuels et mtime dans leur phase, sans SHA déclaré par le
rapport login. Les7lectures de chapitre ajoutent zéro groupe fonctionnel. Le
manuel canonique servi correspond à17chapitres et67paragraphes. Une première
capture mobile avec tuile non peinte est reprise après frames/capture natives ;
seules les images finales effectivement inspectées sont attestées.

Reste UX constaté sur la capture unsaved-preserved : le succès historique
« Brouillon enregistré » reste visible avec une nouvelle saisie locale. Le
badge signale celle-ci mais la notification doit être retirée à la frappe et
aux nouvelles lectures ; suivi070.8, aucun correctif encore revendiqué.
Restent aussi les parcours source archivée/dialog/pagination de diff aux bornes,
adoption en gardant le texte, frappes durant sauvegarde, préparation/inconnu,
réponses perdues et SIGKILL/restart, quotas globaux et autres bornes de ce contrat,
purge avec lecteur vivant et campagne complète. Le lien Tester dépend de071.
Les critères070.1–.6/.8 restent ouverts ; seule070.7 demeure clôturée.

## Retrait des confirmations périmées —070.8 en qualification

La décision est portée par070.8 avant cette correction. La notification de
sauvegarde est retirée à toute nouvelle saisie et consultation explicite :
fichier, dossiers/recherche/page, diff, contexte, brouillon ou tentative.
La lecture automatique du contexte après publication conserve le résultat de
publication acquis. Si de nouvelles frappes arrivent pendant la sauvegarde,
seul le snapshot envoyé devient la référence ; aucune notification générale
« Brouillon enregistré » ne doit prétendre sauvegarder le texte désormais local.
Le scénario UI ajoute des assertions après frappe et changement de fichier ;
le manuel suit ce comportement. Code implémenté, preuve de070.8 à produire.

Pendant les mutations autres que l’enregistrement du fichier ouvert, la zone de
texte est en lecture seule. Cela évite qu’un retrait/abandon en cours efface une
frappe arrivée après sa confirmation. L’enregistrement explicite du fichier
reste le seul envoi qui accepte de nouvelles frappes, conservées comme saisies
locales. Le scénario vérifiera ce mode pendant une vraie sauvegarde et un vrai
retrait ; aucune latence ni réponse substituée n’est nécessaire.

Le parcours de070.8 recharge aussi, après l’entrée normale et les publications,
une URL de source inconnue pour obtenir un vrai404. Un enregistrement de handler
inchangé fournit une confirmation ; Réessayer la lecture des fichiers doit la
retirer même si la source reste404. Le dialog de choix d’un hash conservé rétablit
ensuite la lecture et le brouillon existant. Cette épreuve ne substitue aucune
réponse ni dépendance et ne prétend pas couvrir les sources archivées.

### Fenêtre réelle de sauvegarde —décision avant banc

Le premier passage070.8 sur6e1584f2 passe quatre groupes puis s’arrête parce que
la réponse est arrivée avant la frappe observée. La fonction est purgée ; cet
échec ne qualifie pas la branche de frappe pendant envoi.

Le banc utilisera un vrai verrou d’écriture SQLite via ControlWriter existant,
sans instruction d’écriture ni seed, sur le seul SPARK DEV. Il vérifie la
fonction et son namespace de campagne avant le verrou. Le propriétaire de la
base est conservé. Le verrou attend la libération du pilote ou EOF, au plus
trois secondes : en cas de perte du processus, SQLite ferme la connexion et
libère nativement le verrou. Aucun service ni variable officielle n’est arrêté.
Le reçu conserve identité du processus/base, zéro changement SQL et motif de
fermeture ; une nouvelle acquisition confirme la libération.

Les sorties normales, EOF, échéance et pertes SIGTERM/SIGKILL du seul helper
seront éprouvées réellement et en série avant l’utilisation. Le signal cible
un pidfd après vérification PID/naissance/commande exacte/UUID ; aucune autre
ressource n’est signalée. Le client ouvre ensuite un verrou, commence la vraie
sauvegarde HTTP, tape pendant que sa réponse reste absente, libère le verrou
puis compare le snapshot enregistré et le texte local. Le même observateur
permet de dater la lecture seule avant réponse lors du retrait. Aucun délai
réseau, réponse ou dépendance n’est substitué. Une borne ou jonction absente
fait échouer la campagne ; aucun rejeu automatique ni succès conditionnel.

Le passage nominal suivant réussit14groupes, dont six sorties réelles du verrou
et les deux observations HTTP avant réponse. Il reste préliminaire : la revue
relève une entrée de commande partielle pouvant attendre au-delà de3s et un
reçu de signal non exigé si le client SSH était déjà terminé. Le banc est durci
avec une échéance monotone commune pour toute lecture de commande, un reçu
signal/PID/naissance obligatoire, puis des épreuves réelles de fragment sans LF,
refus de signaux après EOF et refus de naissance périmée. Le prochain replay
conservera ces contrôles ; ce nominal n’est pas additionné à son total.

## Confirmations de sauvegarde qualifiées —070.8

Le [complément DEV](evidence/code-editor-save-confirmation-dev-2026-11-12.json) passe 39 groupes au gel0080af6 :
14 UI, puis8manuel/8public/9connexion, sur371sources identiques avant/après.
L’image6e1584f2 sert le correctif et le manuel actualisé. Les36fichiers serveur
embarqués sont identiques au checkpoint57 ; cette preuve ne réadditionne pas
ses20groupes serveur. La première tentative trop rapide et les14groupes du
nominal préliminaire restent distincts du total39.

Les notifications sont retirées à la frappe, à la lecture et au retry d’une
source réellement404. Le choix d’un hash par le vrai dialog rétablit la source
puis le brouillon. Une vraie sauvegarde sous verrou SQLite conserve le snapshot
1Mio−1 envoyé ; la frappe supplémentaire reste locale avec badge et sans faux
succès. La sauvegarde suivante enregistre ce texte1Mio exact. Lors du retrait,
le champ est readonly avant réponse ; les autres patches restent présents.
Neuf invocations CJS/ESM/YAML, quatre publications et un import refusé sont
recoupés nativement. Les trois fonctions des passages sont physiquement purgées.

Le banc passe huit sorties : libération, EOF, échéance sans commande, fragment
sans LF, SIGTERM, SIGKILL, commande invalide et33octets contre borne32. Les
échéances mesurées sont3,007354s et3,007353s, avec0et4octets reçus. Chaque signal
possède son reçu PID/naissance/pidfd ; un signal après EOF et une naissance
périmée sont refusés. Les treize helpers finaux et huit du nominal préliminaire
sont absents. Le probe final peut prendre le writer, ne change aucune ligne,
ferme sa connexion et vérifie les propriétaires1001 de SQLite/WAL/SHM pendant
l’ouverture. Les journaux peuvent ensuite disparaître normalement ; leur absence
après fermeture n’est pas présentée comme une conservation physique de fichiers.

Les44images inspectées sont15UI,22régressions et7lectures du chapitre mis à jour.
Les38JPG ont leurs SHA déclarés ; les6PNG login restent liés aux octets courants
et à la fraîcheur dans leur phase. Les sept lectures de guide n’ajoutent aucun
groupe fonctionnel. Le manuel servi correspond à17chapitres et67paragraphes.
Les5982artefacts antérieurs, la référence et les fichiers officiels sont identiques.
Dix migrations, intégrité, clés étrangères, stockage sain et compteurs actifs nuls
sont recoupés.070.8est clôturée ;070reste ouverte pour quotas globaux, limites,
reprises/transport, source archivée, pagination au-delà de cinq et Tester071.

## Capacité des brouillons qualifiée —12novembre2026

La [preuve DEV](evidence/code-draft-capacity-dev-2026-11-12.json) passe42groupes sur375sources25a4152 :
17ciblés et25régressions (8manuel,8public,9connexion), sans test ignoré.
Le contrôle6e1584f2, ses36sources backend, ses quatre ressources web et le manuel
servi sont identiques au checkpoint39. Les22captures de régression sont ouvertes
individuellement ; le manuel conserve17chapitres/67paragraphes.

Les API réelles atteignent32brouillons par propriétaire,128globaux, puis
67108864octets de ciphertext. Les429 et507 ne changent ni lignes, versions,
dates, handler, longueurs/SHA des ciphertexts ni audits de mutation du brouillon.
Le PUT inchangé reste accepté au plafond. Libérer100octets permet une création
vide ;80octets ne suffisent pas ; réduire20octets la rend à nouveau possible.
Quatre patches Unicode de moins de4Mio et un brouillon vide remplissent le budget
exact. Ce calcul préparatoire est recoupé sur les longueurs réellement stockées.

Un brouillon initial produit un vrai candidat publié puis une invocation Docker
par hash, sans ZIP client ni promotion. L'archive conserve les quatre brouillons
restants de la fonction ; la purge les retire. Le conflit409 réel n'adopte pas
l'UUID existant dans son intention de nettoyage. Le reçu reste incomplet jusqu'à
la fermeture des clients et au nettoyage. Les33fonctions nominales sont purgées,
ainsi que les33du passage préliminaire. Ses17groupes ne sont pas additionnés.

Au final : aucun brouillon, invocation active, instance, candidat actif, bail,
opération ou réservation ; dix migrations, intégrité/FK et propriétaires1001
recoupés. Les5982artefacts antérieurs, leurs SHA, les trois configurations, les
CID/images/dates de démarrage et la santé des deux conteneurs sont conservés.
Le probe writer final ferme sa connexion et n'effectue aucun DML. Les journaux
WAL/SHM sont vérifiés pendant ouverture ; leur disparition normale reste distincte.

Ce résultat qualifie les plafonds dans070.3, sans clôturer ce critère ni070.
Reprises/pertes de réponse du contrôle, limites restantes de diff/ZIP, purge sous
lecteur vivant, sélection archivée, compléments UI et Tester071 restent ouverts.

## Parcours éditeur vers Tester qualifié

Le [complément46](evidence/function-http-client-ui-admission-dev-2026-11-12.json)
sur8c761c5e/384sources8285798e ouvre Tester depuis une version pilote et depuis
une publication Docker de l’éditeur. Les marqueurs exécutés confirment les hashes
sélectionnés ; une version archivée est refusée sans repli. La tranche43 sur le
même backend38sources prouve publication B sans promotion, promotion B et retour
A. Les campagnes conservent leurs époques distinctes, sans réaddition de groupes.
070.6 est clôturée ; les bornes, reprises et lectures vivantes restantes de070
restent ouvertes. Les sections de résultats antérieurs conservent leur date,
leurs images et leurs restes de qualification propres au checkpoint décrit.
