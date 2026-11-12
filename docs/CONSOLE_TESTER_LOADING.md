# Testeur HTTP : lecture réellement en attente

Complément de [SLS-071.2](BACKLOG.md#sls-071) après la qualification du
[refus réel des domaines](CONSOLE_TESTER_SOURCE.md). Le libellé « Lecture en
cours… » est qualifié par la preuve réelle ci-dessous. Ce complément ne modifie
aucun comportement produit.

## Décision avant code

Réutiliser la suspension native du mode `watchdog` de
`e2e/function-http-client-recovery-operator.py`, avec `NativeObserver` et sa
restauration indépendante existants. Aucun Docker pause, nouveau démon, faux
réseau, interception de réponse ou modification de limite de ressources.
La vraie boucle HTTP du contrôle reste suspendue pendant la lecture ; aucun
registre, buffer, résultat de syscall ni contenu applicatif n’est modifié.

La fonction originale de campagne appartient au namespace
`function-http-client-recovery-loading-XXXXXXXX`, avec nonce UUID dans sa
description et celle de son service. Ce scope conserve le contrôle de propriété
existant du helper ; il n’assouplit pas le scope source-access de la garde EACCES.
Tous les objets sont créés/purgés par les API normales, sur le seul SPARK DEV.

La revue constate que le watchdog ne relit pas immédiatement CID/image/StartedAt,
naissance et cgroup avant attachement ; la branche cut ne relit pas le cgroup à
cet endroit. Corriger ces deux frontières avant la nouvelle suspension. Armer
et constater la garde avant l’attachement ; revérifier l’identité après le stop
et exposer seulement PID/naissance/SHA du cgroup, TracerPid et état natif. Le
restaurateur expose aussi la survie du PID original avec naissance/cgroup et
TracerPid réel. Aucun champ healthy seul ne prouve cette conservation.

Les deux changements de l’opérateur imposent de rejouer ses sept scénarios
existants de reprise, puis les régressions communes. Le contrôle peut changer
son PID/démarrage dans le scénario de KILL déjà contractuel ; cette mutation
reste distincte de la suspension de chargement, qui conserve son propre PID et
son propre démarrage. Ne pas confondre leurs reçus et fenêtres.

## Matrice fonctionnelle

1. Vrai SSO depuis l’accueil ; publier/promouvoir une fonction originale et
   créer son Read temporaire. Ouvrir Tester par la navigation, envoyer un vrai
   appel et constater positivement hash, UUID, URL, cURL, réponse, téléchargement
   et confirmation de copie native. Attendre le repos de son instance.
2. Armer le watchdog et constater le TID principal réellement arrêté sous le
   bon traceur. Préparer une promesse observant la réponse GET du catalogue,
   avec rejet traité dès création, puis cliquer Actualiser sans attendre cette
   réponse. Constater pendant la suspension : « Lecture en cours… » dans Hash
   courant, lecture annoncée, rafraîchissement/envoi désactivés, anciennes URL,
   cURL, résultat, téléchargement et confirmation retirés, jeton conservé.
   Une requête catalogue, aucune réponse encore reçue et aucune invocation
   automatique. Deux JPEG desktop/mobile, sans débordement horizontal.
3. Les vérifications de la phase suspendue portent des échéances courtes et
   une borne globale inférieure aux huit secondes du helper. En cas de retard,
   échouer et rejoindre sa restitution ; ne pas déduire une perte native d’une
   simple expiration. Envoyer `lose-observer`, constater le SIGKILL réel du seul
   helper et sa fin137/255, puis joindre la garde indépendante de douze secondes.
   Le retour de la lecture peut précéder cette garde après détachement par le
   noyau : conserver ces observations séparément, sans attribuer le retour HTTP
   nécessairement au timer.
4. Vérifier catalogue disponible, même hash et saisies, un seul GET et sa
   réponse, mêmes CID/image/StartedAt et PID/naissance/cgroup, TracerPid zéro,
   santé, timer/service joints. Émettre explicitement un nouvel appel réel et
   vérifier son UUID/hash natifs ; aucun rejeu automatique de l’appel initial.
5. Purger la fonction, révoquer le jeton et supprimer les parents uniquement
   après restitution connue ; recouper intégrité/FK/migrations, réservations,
   instances, baux, gardes et artefacts antérieurs. Une restitution inconnue
   conserve la fixture et son diagnostic.

## Attribution et limites

Le client de chargement est original et indépendant du client EACCES. La durée
huit secondes et le timer douze secondes sont ceux du helper qualifié ; les
sources seront relues et leurs fenêtres respectées. L’exception inattendue
avec contrôle vivant de071.6 reste une preuve séparée. Une réussite ici ne
clôture ni les autres causes du lecteur093, ni la campagne complète095, ni les
défauts visuels101/102. Statut : critère071.2 qualifié, exception071.6 et campagne complète ouvertes.

## Qualification réelle du chargement

La [preuve37](evidence/function-http-client-loading-dev-2026-11-12.json) lie le commit
b39e30f,397sources6b9cb2bc et l’image60938093 inchangée :7groupes de reprise,
5de chargement et25régressions communes. Les deux clients ciblés passent
après relecture de leurs frontières natives ;30captures sont inspectées,
8ciblées par le principal et22communes par le vérificateur en lecture seule.

Le TID1007466 est réellement en état`t`, sous le helper1009054. Une seule
requête catalogue reste sans réponse pendant les assertions et les captures
desktop/mobile, achevées en233ms dans la borne4500ms. Le helper reçoit le vrai
SIGKILL et termine255 ; la réponse GET revient à1794470865483ms après
détachement noyau, la garde indépendante est jointe à1794470879093ms. Aucun
retour HTTP n’est attribué à tort au timer. Deux reçus natifs prouvent PID,
naissance508864062, cgroup, CID/image/StartedAt identiques, TracerPid0 et santé.
Les métadonnées/invocations sont identiques ; un nouvel appel explicite donne
200avec hash et nouvel UUID natifs. Les deux handlers du chargement réussissent.

Le replay de reprise possède sa propre coupure137 du contrôle et son
redémarrage à08:05:20.159372646UTC. Cette mutation est antérieure au chargement
et ne prouve pas sa conservation du PID : les reçus sont séparés. Trois
handlers de reprise, dont un interrompu puis deux succès, sont recoupés.
Trois fonctions des deux campagnes sont purgées et deux jetons révoqués ;
parents supprimés, trois observateurs terminés, zéro activité/bail/réservation/
garde. Dix migrations, intégritéok/FKvide,38backend/4web, fichiers officiels,
manuel18chapitres/74paragraphes et5982artefacts antérieurs sont conservés.

Le lanceur commun a disparu pendant son repos avant connexion ; son absence
est confirmée par la perte du handle et l’absence du processus. Les16groupes
manuel/public déjà terminés sont conservés ; seul login9 est repris, avec son
nouveau snapshot et ses fenêtres. Aucune preuve n’est déduite du repos.
Les PNG de connexion n’ont pas de SHA déclaré ; leurs octets courants et mtimes
sont liés à la phase exécutée. Les défauts101/102 ne sont pas déclarés corrigés.

## Client HTTP livré après qualification du dernier critère

Le [complément31](evidence/function-http-client-task-exception-dev-2026-11-12.json) qualifie071.6 :
6groupes ciblés et25régressions,401sources67215a2b/image60938093,26vues
inspectées. VraiEMFILE puis OSError de tâche, ressources rendues avant Python,
même PID et quatre relais actifs/cinquième429 puis succès. Le
[contrat d’exception](CONSOLE_TESTER_TASK_EXCEPTION.md#qualification-finale-de0716)
lie les reçus originaux, les12handlers et les nettoyages. SLS-071 est livré avec
les preuves43/46/42/32/37 conservées par critère, sans réaddition. Manuel et
produit inchangés pendant ce complément ;101/102 et095 restent ouverts.
