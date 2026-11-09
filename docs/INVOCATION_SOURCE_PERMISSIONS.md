# Refus réel de lecture du relevé officiel

Complément de SLS-066. Cible unique : `/etc/spark/routes` du SPARK DEV
infra-serverless, monté readonly sous `/spark/routes` dans le contrôle.
Le précontrôle du 9 novembre confirme un fichier régulier root:1001, mode
0640, 779 octets/SHA identiques depuis le contrôle sans capacités effectives.
Il ne prouve pas à lui seul un refus ou une restitution. Les trois preuves de
garde ultérieures sont qualifiées ci-dessous. Le complément API passe aussi ;
le rendu UI reste à qualifier.

## Périmètre et invariants

Provoquer EACCES par fchmod(000) du fichier officiel ouvert, sans modifier son
contenu, nom, inode, propriétaire/groupe, routes, DNS, variables, secrets ou image.
Aucune source copiée/remplacée ni réponse substituée ; aucune administration FORGE.
Ouvrir les parents par descripteur sans lien puis la feuille NOFOLLOW/NONBLOCK.
Recouper FD et nom : régularité, dev/ino/uid/gid, lien unique, taille, SHA, mtime
et mode initial. Chmod change ctime : l’observer sans prétendre la rétablir.
Encoder les nanosecondes des reçus en chaînes décimales pour préserver leur
précision dans JavaScript. Ne pas reprojeter les routes pendant la faute.

Avant faute : contrôle/référence sains, image/démarrage attendus, montage readonly,
CapDrop/no-new-privileges et nouvel open réussi dans le contrôle. La preuve
initiale exige zéro fonction active, invocation, instance, publication ou
opération de stockage en cours. Les futurs parcours API/UI n’autoriseront que
leur fonction possédée, namespace source-access suivi de huit chiffres hexadécimaux
et nonce complet dans les descriptions des parents.

## Garde indépendante avant modification

Un verrou global root privé sous /run sérialise les opérateurs. Écrire dans un
répertoire root 0700 une copie figée autonome du programme et son SHA ; la
restauration ne dépend d’aucun import du dépôt mutable. Armer et confirmer le
timer systemd du SPARK avant fchmod, programme figé sous Python isolé.
Aucun daemon permanent. Protocole stdin borné par octets/longueur/délai et EOF.

La garde indépendante vérifie pidfd/naissance/commande du helper, ne signale
jamais un PID réutilisé et tue/joint le seul helper original avant son verrou.
Restituer le fichier avant les contrôles Docker : leur panne ne doit pas
empêcher le retour du mode sur l’identité strictement liée. Puis vérifier nouvel
open du contrôle, santé locale et identités contrôle/référence ; une validation
échouée reste un échec, même si le mode est déjà restitué.

Restaurer seulement si FD et nom gardent identité, SHA, taille, propriétaire,
groupe et mtime ; mode zéro ou déjà initial. Ne recréer aucun fichier disparu,
ne pas adopter une nouvelle identité ou permission concurrente. Reçu privé
avec état complet/incomplet et classe d’erreur, sans données sensibles.
Le chemin normal restitue sous verrou, le libère puis arrête le timer et attend
le service inactif. Stop code 5 accepté seulement si lecture native exacte :
LoadState=not-found, ActiveState=inactive.

## Trois preuves de garde avant les parcours fonctionnels

Client séquentiel, installation au repos :

1. Faute, timer 60 secondes, nouvel open réel donnant errno 13, libération
   explicite ; mode, lecture et santé restitués.
2. Faute, timer 12 secondes, SIGKILL du seul helper après fault-active ; garde
   indépendante, mêmes restitutions.
3. Faute, timer 12 secondes, SIGSTOP du helper ; la garde doit le tuer et le
   joindre avant les mêmes restitutions.

Un FD déjà ouvert n’est pas révoqué : confirmer le nouvel open errno 13 avant
fault-active. Conserver les reçus natifs exacts et exiger fin du helper, timer
et service, deux HTTPS publics sains et source restituée. Ces trois cas ne
qualifient pas encore le catalogue API/UI. Un arrêt reste séparé, aucun skip.

## Parcours suivants

Après qualification de la garde, créer/publier le handler original du dépôt.
Sous faute : vrai catalogue unavailable/source_forbidden, aucune adresse ou
détail interne ; après restitution : même révision et URL. Vérifier les refus
de droit avant divulgation. Le parcours UI crée/publie depuis l’accueil ; après
fault-active, Actualiser affiche Lecture des domaines refusée et son aide,
sans anciennes URL/copies, avec focus et captures desktop/mobile. Restituer,
actualiser puis invoquer l’URL copiée. Purger seulement la fixture possédée après
fin des gardes, puis recouper le stockage nativement. Source manquante/changée
et pannes propres du nouvel opérateur restent distinctes. Ces parcours API/UI
ne sont pas encore qualifiés par les trois preuves de garde.


## Observation des signaux et conservation des tentatives

La sortie SSH seule, notamment 255, ne prouve pas le signal reçu par le helper.
Un parent de preuve distant lance le vrai helper comme enfant et observe son
waitpid avec WUNTRACED : arrêt SIGSTOP puis terminaison SIGKILL, ou sortie normale
pour release. Recouper le PID observé avec celui de la garde. Le parent ne lit
pas le protocole stdin du helper, ne modifie aucun fichier et ne rejoue rien.
Exiger sa fin normale et les statuts noyau attendus dans le client de preuve.

Chaque tentative de restauration produit un fichier de reçu unique immuable,
y compris si Docker/santé échouent après retour du mode. Une récupération ne
remplace jamais le reçu initial ; l’observation courante sélectionne la dernière
tentative terminée par horloge monotone, tout l’historique restant disponible.
Le programme et le contexte systemd doivent disposer de la capacité DAC d’ouvrir
la source 000. Le précontrôle transitoire réel confirme cette capacité et la fin
de son unité ; ce constat ne remplace pas les restaurations à éprouver.

## Trois gardes réelles qualifiées le 9 novembre

La [preuve](evidence/invocation-source-guard-dev-2026-11-09.json) passe les trois
cas en série sur 210 sources et les mêmes images. Chaque faute donne un nouvel
open réel du contrôle à errno 13, puis lecture normale après restitution.
Le parent observe nativement SIGSTOP puis SIGKILL pour le helper suspendu,
SIGKILL pour celui qui se tue et sortie zéro pour release ; leurs PID concordent.
Trois reçus immuables et copies figées sont recoupés ; helpers, timers/services
terminés, deux HTTPS sains. Nom, inode, contenu, propriétaire/groupe, mode 0640 et
mtime restent ceux d’origine ; ctime change comme attendu. Services, démarrages,
routes et fichiers de configuration restent inchangés, aucune fonction créée.
Le refus public source_forbidden et son rendu UI restent à éprouver ensuite.

## Catalogue public sous refus de lecture

Le client `invocation-source-api.mjs` éprouve quatre groupes en série, après
les trois gardes qualifiées. Une seule fonction originale est publiée par
l’adaptateur dans le namespace possédé `source-access-XXXXXXXX`, avec nonce
complet dans les descriptions du namespace et du service `source-access-fixture`.
Le helper reçoit ces trois UUID via un argument SSH correctement cité ; son
précontrôle natif exige cette fonction seule et aucune opération en cours.

1. Publication réelle, catalogue disponible avec les deux domaines HTTPS et
   révision active identique à celle retournée par l’adaptateur.
2. Faute réelle et nouvel open errno 13 : catalogue HTTP 200 pour administrateur
   et jeton Read, source unavailable/source_forbidden, items/wildcards vides,
   total zéro, même révision. La source ne porte que state/observed_at/error_code,
   sans chemin ni métadonnées de fichier. Anonymat, jeton invalide, droits CRUD
   sans Read et jeton révoqué restent 401/403, sans diagnostic de source.
3. Les deux URL connues avant la faute invoquent réellement le handler Docker
   pendant celle-ci. Un nouveau catalogue reste refusé après ces appels.
4. Libération explicite et fin du helper/timer/service, source et lecture
   restituées ; catalogue et URL identiques à l’origine, puis appels réels.

Le timer indépendant est armé pour 120 secondes avant chmod. Un dépassement,
une restauration indépendante prématurée ou une réponse inattendue fait échouer
la campagne. Le nettoyage conserve la fixture si la restitution n’est pas
confirmée ; sinon DELETE/purge normaux et recoupement physique en lecture seule.
Conserver les reçus figés et empreintes des sources/images avant/après.
Ce complément ne qualifie ni le rendu UI ni les autres classes de panne source.

## Catalogue API qualifié le 9 novembre

Les quatre groupes passent sur 211 sources et les mêmes images, sans échec
ni test ignoré : [preuve](evidence/invocation-source-api-dev-2026-11-09.json).
Une fonction originale est publiée par l’adaptateur. Sous EACCES confirmé,
Read et administrateur reçoivent HTTP 200/unavailable/source_forbidden sans
adresse ni métadonnée interne ; six refus restent 401/403 sans diagnostic.
Les deux URL connues appellent réellement le handler pendant la faute. Après
restitution explicite, le catalogue/relevé/révision identiques et deux nouveaux
appels sont vérifiés. Les quatre invocations réussies sont recoupées en SQLite.
La fonction est purgée, son service et son namespace supprimés ; absence physique des ressources,
helper/timer/service terminés, même fichier/mode 0640 et configurations/services
inchangés sont confirmés nativement. Ctime change comme attendu. Le rendu UI,
les autres classes de source et les branches d’échec de récupération restent ouverts.

## Parcours navigateur du refus de lecture

`invocation-source-ui.mjs` éprouve trois groupes distincts de la preuve API.
Depuis l’accueil normal, créer namespace/service/fonction par les formulaires,
puis publier le ZIP original par Code et révisions. Même propriété nonce/scope
que le client API, une seule fonction et aucune opération active avant faute.

1. Ouvrir Adresses d’appel, observer les deux domaines, copier réellement une
   adresse et constater son succès ; conserver une capture desktop initiale.
2. Armer la garde qualifiée avant chmod puis confirmer errno 13. Cliquer
   Actualiser, attendre sa vraie réponse HTTP 200/source_forbidden, révision
   inchangée, items/total vides. L’alerte explique « Lecture des domaines refusée. »
   et propose actualisation/contact administrateur ; aucune ancienne adresse,
   commande de copie ou réussite ne demeure. Vérifier le focus DOM sur le titre,
   l’absence de débordement et captures desktop 1440/mobile 390. Les captures
   ne prouvent pas seules les interactions ni un contour de focus visible.
3. Restitution explicite et fin des processus/unités, puis Actualiser retrouve
   les deux domaines. Captures mobile/desktop, copie native et invocation HTTPS
   du handler Docker à l’URL copiée. Recouper cette invocation et la purge physique.

Le timer de 120 secondes et les règles de conservation/nettoyage sont ceux du
client API. Le client ne retient ni n’intercepte la requête et ne modifie aucune
route ou réponse. Cinq JPEG frais sont personnellement relus avant qualification.
Les autres fautes de source et branches de récupération demeurent distinctes.

Le client prend en charge immédiatement le rejet de chaque attente HTTP créée
avant un clic, sans changer son résultat nominal. Il suit ces promesses et les
joint après fermeture du navigateur ; une erreur de clic ne doit pas provoquer
un rejet non géré pendant la restitution ou empêcher l’écriture du rapport.
