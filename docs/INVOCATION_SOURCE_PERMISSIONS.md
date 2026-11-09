# Refus réel de lecture du relevé officiel

Complément de SLS-066. Cible unique : `/etc/spark/routes` du SPARK DEV
infra-serverless, monté readonly sous `/spark/routes` dans le contrôle.
Le précontrôle du 9 novembre confirme un fichier régulier root:1001, mode
0640, 779 octets/SHA identiques depuis le contrôle sans capacités effectives.
Il ne prouve pas encore un refus ou une restitution.

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
et pannes propres du nouvel opérateur restent distinctes. Aucun résultat acquis.


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
