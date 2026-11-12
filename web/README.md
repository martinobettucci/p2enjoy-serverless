# Console web

Le [correctif de focus de l’éditeur](../docs/CODE_EDITOR_CONSOLE_EXTENSIONS.md)
est qualifié après la reproduction réelle de quatre focusBODY. Refs des titres,
intention par génération et invalidation des comparaisons remplacées sont relues ;
les builds local/SPARK passent. Manuel et client18groupes suivent le code.
Le [replay](../docs/evidence/code-editor-console-focus-dev-2026-11-12.json) passe
18groupes UI puis25communs sur407sources6600150c/imageb452ef16 ;51images sont
inspectées. Quatre H2 et deux H3 focalisés, source5+2 archive/supprimée, adoption
sans PUT puis sauvegarde et diff5+2 passent en desktop/mobile. Les lectures
maintenues et le focus après adoption restent à qualifier dans070.3/.4.

Le client HTTP **Tester une fonction (SLS-071)** est livré et qualifié en DEV.
La [preuve finale du dernier critère](../docs/evidence/function-http-client-task-exception-dev-2026-11-12.json) passe **31 groupes réels** :
6 ciblés et 25 régressions sur 401 sources 67215a2b, image 60938093 inchangée ;
26 captures inspectées. Un vrai `openat` échoue avec `EMFILE` ; les limites sont
rendues avant reprise Python, qui lève un `OSError` dans le constructeur TLS.
Le même PID conserve quatre places, refuse le cinquième appel en 429 puis
réussit les appels suivants. Douze handlers nominaux et nettoyages natifs sont
recoupés ; les trois passages échoués restent séparés, sans groupe réadditionné.
Les huit critères s’appuient aussi sur leurs preuves43/46/42/32/37 distinctes.
Manuel18chapitres/74paragraphes conforme, schéma010 et5 982artefacts conservés.
Les défauts101/102 et la campagne complète095 restent ouverts. Les paragraphes
historiques ci-dessous gardent leur époque ; ils ne remplacent pas ce statut.

Le [complément de source du testeur](../docs/CONSOLE_TESTER_SOURCE.md) est
qualifié sur60938093 : [32groupes réels](../docs/evidence/function-http-client-source-access-dev-2026-11-12.json),
395sources28105d2b, six handlers et32captures inspectées. Hash confirmé sous
EACCES, vrai503 avant émission, retrait UI, retour de l’alias, absence sans code
et pilote404 sont éprouvés. Manuel18chapitres/74paragraphes conforme ; dix
migrations, deux fonctions/tokens nettoyés et5982artefacts conservés. Le
chargement dédié071.2, l’exception071.6 et les défauts101/102 restent ouverts.

Le [complément UI/admission du testeur](../docs/CONSOLE_TESTER.md) est qualifié en
DEV sur8c761c5e : [46groupes réels](../docs/evidence/function-http-client-ui-admission-dev-2026-11-12.json),
16UI,5admission et25régressions, sur384sources8285798e.35handlers et38captures
inspectées recoupent corps, CORS/IP, annulation, gzip, limites et liens par hash.
Quatre réceptions JSON partielles donnent429 au cinquième en128ms sans corps,
puis quatre408 après30,088–30,103s ; quatre relais actifs refusent aussi le
cinquième puis rendent leur capacité. Les messages périmés et «1octets» sont
corrigés ;071.7 et le lien éditeur070.6 sont qualifiés. Huit fonctions de tous
les passages du complément sont purgées, six jetons révoqués et5982artefacts
conservés. SLS-071 reste ouverte pour SIGKILL, confidentialité native, source
indisponible et temporisation UI notamment. Les checkpoints plus bas gardent
leurs propres sources/images ; leurs groupes ne sont pas additionnés.

Le premier client HTTP [Tester une fonction](../docs/CONSOLE_TESTER.md) a été qualifié
sur032ca071. Sa [première preuve](../docs/evidence/function-http-client-dev-2026-11-12.json)
passe43groupes réels :18ciblés et25régressions sur382sources46a59128.
27handlers Docker, expiration réelle900s, corps1Mio/réponse6Mio, refus bornés,
redirection sans suivi et parcours serveur/CORS sont recoupés.27captures sont
inspectées ; manuel18chapitres/74paragraphes, quatre fonctions de tous les
passages purgées, huit jetons révoqués et5982artefacts antérieurs conservés.
CORS refusé, politiques IP, annulation UI, saturation et SIGKILL restent ouverts ;
SLS-071 reste[~]. Les checkpoints ci-dessous gardent leurs images et époques.

La facette [Éditeur SLS-070](../docs/CONSOLE_EDITOR.md) a été qualifiée sur
6e1584f2. Son [complément070.8](../docs/evidence/code-editor-save-confirmation-dev-2026-11-12.json) passe
39 groupes réels : 14 UI et 25 régressions, neuf invocations Docker et 44 vues
inspectées. Notifications retirées à la frappe/lecture, snapshot envoyé distinct
des frappes ultérieures et readonly pendant retrait sont éprouvés. Le vrai404
et le dialog de source sont qualifiés ; lors de ce checkpoint, le manuel porte17chapitres/67paragraphes.
Les371sources et l’image restent identiques avant/après ; trois fonctions des
passages sont purgées et21helpers terminés sont recoupés. Le checkpoint57 sur
a77b6b4e garde ses preuves propres.070.8est clôturée ; les critères070.1–.6 restent
ouverts pour quotas, limites, interruptions et compléments UI. La tranche071décrite en tête est déployée depuis ce checkpoint.

SLS-089 est déployée sur e81007c5, après sauvegarde native SQLite et sans
changement de schéma ou configuration de cellule. La [preuve partielle](../docs/evidence/sso-session-recovery-dev-2026-11-11.json) passe 33 groupes
sur 359 sources : 8 ciblés SSO, 8 du manuel, 8 publics, 9 de connexion. 30 captures sont recoupées,
manuel : 16 chapitres et 57 paragraphes. Seul 089.4 est qualifié : durée réelle 300 s et
renouvellement après expiration. Les profils sans droits, négatifs azp/aud et
rotation/pending503 restent ouverts. Les checkpoints ci-dessous gardent leur
image et leur époque historiques.

L'icône SLS-100 est déployée sur l'image779aef7b : trois blocs reliés partagent
`public/favicon.svg` pour le favicon et la marque. La
[preuve](../docs/evidence/application-icon-dev-2026-11-11.json) qualifie29groupes réels et26captures
inspectées :4 ciblés,8manuel,8publics,9connexion. Le backend et les trois autres
ressources web restent identiques. La commande dédiée et son entrée privée sont
décrites dans [e2e](../e2e/README.md#identité-visuelle-serverless).

La suite SLS-074 est déployée pour qualification en DEV : versions groupées par hash,
publication/promotion séparées, archive/restore/delete, réimportation explicite
et adresses épinglées. Le manuel source accompagne ces changements. Le build
Vite local et Docker passent ; six groupes navigateur et huit du manuel passent
dans le [checkpoint008](../docs/evidence/function-version-execution-checkpoint-dev-2026-11-09.json),
avec28 captures inspectées. Les vrais409/404 conservent confirmation, saisie et
focus ; un dialog reste ouvert lorsque sa carte quitte la page pendant une
publication externe. Pannes et régression complète restent à éprouver.
Le checkpoint007 ci-dessous reste historique.

Console React/Vite servie par le contrôle sur la même origine. Contrats :
[CONTROL](../docs/CONTROL.md), [design du produit](../docs/DESIGN_SYSTEM_APP.md)
et [socle visuel](../docs/DESIGN_SYSTEM.md).

Le build est inclus dans `control/Dockerfile`, lancé dans le SPARK DEV avec
`bash control/dev.sh build`. Aucun serveur de données local ni interception
API : les parcours de qualification ciblent la console réellement déployée.
Les 11 parcours de gestion de `node e2e/control-ui.mjs` passent sur le SPARK,
dont les noms longs à 390 px, les trois gestes de fermeture du menu et le
retour du focus. Sept captures ont été relues : [preuve de gestion](../docs/evidence/control-management-dev-2026-11-06.json).
Les facettes Instances et Invocations sont déployées : allocations et mesures
séparées, détails des appels et journaux expurgés, pagination et rafraîchissement
manuel. Le [contrat](../docs/CONSOLE_EXECUTION.md) et la
[preuve](../docs/evidence/console-execution-dev-2026-11-07.json) recoupent 12 groupes
propres à ces vues et 28 groupes de régression, avec 25 captures relues.
La facette **Code et révisions** est déployée et vérifiée : ZIP/handler,
suivi de publication, abandon, métadonnées, activation et suppression.
Son [contrat](../docs/CONSOLE_PUBLICATION.md) conserve les réglages et secrets
côté serveur. Ses 21 groupes navigateur passent, avec les dix groupes API et
les huit groupes du manuel, dans la [preuve finale](../docs/evidence/publication-console-dev-2026-11-07.json) :
18 campagnes en série, 312 groupes réels et 54 captures inspectées. Les deux
écarts de lecture relevés à la première revue sont corrigés et requalifiés.

Depuis la racine, avec la session SSO réelle :

```sh
node e2e/execution-ui.mjs
node e2e/publication-ui.mjs
python3 -B e2e/execution-suite.py --scope console
```

Ces commandes sont des campagnes distinctes ; la suite rejoue les observations
et la publication avec les parcours publics, de connexion, de gestion et du
manuel. `python3 -B e2e/execution-suite.py --scope publication` ajoute les
régressions du moteur dans une suite commune sans répéter les campagnes partagées.

## Manuel d’usage

La navigation ouvre `/console/manual`, avec sommaire, ancres partageables et
retour au sommaire. `docs/manual.md` est la seule source à éditer ;
`vite.config.mjs` la compile en contenu HTML sans HTML brut, avec son empreinte.
Le contexte Docker inclut explicitement ce document. `markdown-it` est verrouillé
en dépendance de build et n’est pas inclus dans le navigateur. Mettre à jour le
guide avec chaque comportement utilisateur, puis reconstruire la console.

`node e2e/manual-ui.mjs` vérifie huit groupes réels. La
[preuve initiale](../docs/evidence/manual-console-dev-2026-11-07.json) précède la
publication UI : 48 groupes, zéro échec/skip et 33 captures relues. La suite
de console comprend désormais aussi les 21 groupes de publication.
Le guide courant compte quinze chapitres, dont Retrouver une fonction, le
vidage du cache, la purge et les adresses d’appel. La campagne SLS-067 recoupe
son empreinte, ses quinze chapitres, 46 paragraphes, le tableau et la commande.
Quatorze captures du guide sont inspectées, dont trois vues du nouveau chapitre ;
le chapitre Adresses d’appel possède aussi son viewport mobile dédié. La [qualification complète du stockage public](../docs/evidence/storage-console-dev-2026-11-08.json)
recoupe ces huit groupes, dix parcours UI stockage, les régressions et leurs captures.
La [preuve du correctif de purge](../docs/evidence/storage-legacy-recovery-dev-2026-11-07.json)
rejoue ces huit groupes et ajoute une capture de lecture mobile du nouveau
paragraphe sur une purge en attente après changement du stockage. Les douze
captures sont inspectées ; le document affiché correspond à sa source.

La [preuve de configuration commune](../docs/evidence/service-configuration-dev-2026-11-08.json)
rejoue les onze groupes de gestion et les huit du manuel, puis complète la lecture
des niveaux service/fonction et du déploiement. Ses 21 captures sont inspectées,
dont les sept vues de gestion, onze du guide et trois lectures complémentaires.

## Adresses d’appel en qualification

La fiche de fonction présente la facette **Adresses d’appel**, également liée
depuis sa ligne du service. Le catalogue officiel fournit méthodes, URL et
transport déclaré. Les copies natives ont leurs confirmations et refus ; une
erreur de consultation retire les anciennes adresses. Le manuel contient le
chapitre correspondant. Le [checkpoint SLS-066](../docs/evidence/invocation-urls-checkpoint-dev-2026-11-08.json)
passe six groupes propres au parcours navigateur et ses régressions, avec
sept captures inspectées. Les changements réels de routes sont qualifiés par les cinq cycles ultérieurs.
Le [complément six domaines](../docs/evidence/invocation-pagination-dev-2026-11-09.json)
passe trois groupes UI008 : accueil/formulaires, promotion explicite, cinq puis
un domaine, clavier/copies/appels réels et sélection par hash mobile. Les sept
JPEG sont inspectés ; les autres fautes restent ouvertes.
La [régression complète](../docs/evidence/invocation-urls-regressions-dev-2026-11-08.json)
recoupe 79 captures fraîches de l’ensemble des parcours : 61 observations
visuelles et 18 identités SHA avec les références inspectées, sans défaut
bloquant constaté. Le manuel servi correspond aux 14 chapitres et 43 paragraphes
de sa source. Les limites d’observation sont précisées dans le design du produit.


## Catalogue global qualifié

L’accueil Fonctions et /console/functions présentent la table globale ;
Namespaces possède sa destination /console/namespaces. Recherche temporisée,
filtres recherchés/paginés, tri, état et page sont partageables dans la query.
Le retour depuis une fiche traverse ses six facettes et se recale après une
suppression. Les erreurs retirent les anciennes lignes ; une session admin
reste obligatoire pour les trois lectures de catalogue.

La [preuve SLS-067](../docs/evidence/function-catalogue-dev-2026-11-08.json)
retient 37 campagnes uniques / 489 groupes réels et six prérequis : 447 groupes
aux clients inchangés puis 42 réexécutés sur les mêmes sources produit/images.
Deux époques de clients restent déclarées. Les 98 images sont inspectées, dont
seize du catalogue avec les trois positions de table mobile et le dialog en
viewport. Les noms complets restent lisibles sans élargir le document.
La remarque mineure de titre d’archive après purge est suivie dans SLS-075.


## Hash du code dans les révisions

La carte montre le hash64 complet, distinct du SHA des octets ZIP, et sa copie
native avec confirmation/refus utiles. Le résultat disparaît à la prochaine
observation. Le manuel canonique est compilé avec la console :15 chapitres et
47 paragraphes recoupés. La [preuve](../docs/evidence/function-version-registry-dev-2026-11-09.json)
qualifie trois groupes ciblés et les régressions ; six nouvelles captures hash,
dont deux viewports réels. Avec les campagnes communes :69 captures recoupées,
47 nouvelles inspections et 22 références SHA strictes. L’upload garde son activation
actuelle ; la promotion distincte et les appels par hash restent en cours.


## Console des planifications qualifiée le10 novembre2026

Le contrôle sert désormaisc59b8616, migration009, après sauvegarde SQLite native.
Le [complément de console](../docs/evidence/schedule-console-dev-2026-11-10.json)
passe19 groupes réels : trois ciblés, huit manuel et huit publics ; six handlers
22:10UTC, vide/nom63, pages5+1, clavier/mobile et vrai401→Réessayer200. Pagination
périmée corrigée et manuel servi conforme16 chapitres/56 paragraphes.31 captures
recoupées,17 inspectées personnellement et14 références SHA ; deux fonctions
purgées,34 backends et5982 artefacts conservés. L'unité078 reste ouverte pour
rétention, plafond global099, adaptateur.7 et régression complète. Les checkpoints
cités plus haut conservent leur image et leur époque historique.
