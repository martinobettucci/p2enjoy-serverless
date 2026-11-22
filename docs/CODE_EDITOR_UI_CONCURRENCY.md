# Réponses de comparaison et focus pendant les actions de console

Complément de [SLS-070.3/.4](BACKLOG.md#sls-070), décidé le22novembre2026
après la clôture des sources/limites070.1. Contrats : [éditeur](CONSOLE_EDITOR.md),
[compléments console](CODE_EDITOR_CONSOLE_EXTENSIONS.md) et
[barrière native qualifiée](CODE_EDITOR_READ_CONCURRENCY.md).
Les deux design systems ont été lus intégralement avant ce choix. Aucun code
produit, comportement, schéma, manuel ou paramètre n’est modifié pour ce banc.

## Préparation et autorité de la preuve

Nouveau client `e2e/code-editor-ui-concurrency.mjs`, sur le seul SPARK DEV,
image exacte433da150, un scénario à la fois. Accueil puis vrai SSO administrateur.
Créations préparatoires par les API ordinaires : namespace
code-editor-read-concurrency-<nonce>, service editor-reader-lifecycle, descriptions
UUID identiques, fonction editor-reader-lifecycle-<nonce> unique. Ces identités
respectent les gardes existantes ; aucun élargissement de l’opérateur n’est prévu.
Paquet original `code-editor-read-package.py`, véritable publication/promotion,
jeton Read propre au service et invocation Docker. Le handler et reader-gate.txt
sont ceux du dépôt ; aucune dépendance ou réponse n’est substituée.
Configuration idle_seconds0 ; après chaque invocation, attendre réellement
zéro instance/invocation active/opération/candidat actif et les seuls deux
conteneurs officiels avant le prochain armement.

Chaque parcours recrée explicitement son brouillon depuis la même cible par
les API. Les patches de préparation ajoutent un petit fichier de travail et
modifient reader-gate.txt pour le rendre présent dans la liste des différences.
Les actions mesurées passent ensuite par les contrôles de l’UI. Les mutations
externes utilisent le même compte, comme un autre onglet ; ni SQL ni fichiers
applicatifs ne sont écrits par l’opérateur.

## Lecture effectivement retenue

Le détail GET code-draft/diff avec path=reader-gate.txt lit d’abord les octets de
la cible promue. C’est cette lecture physique qui est retenue ; son côté patch
peut être en mémoire. Une liste de métadonnées sans path ne lit pas le fichier
et n’est jamais présentée comme maintenue. Une lecture openFile met fileLoading
dans locked : elle n’est pas employée à la place du détail pour les mutations.

Finir les lectures préparatoires avant l’armement. Après armed, la seule requête
susceptible de lire ce FD est le GET de détail observé dans le navigateur. Lier
sa méthode, son URL complète, l’absence de réponse et l’événement held aux
FD/inode/TID/naissance exacts. La santé et la gestion doivent répondre pendant
ce maintien. L’observateur ne reconnaît pas l’identité HTTP : la corrélation
repose aussi sur l’absence de toute autre lecture de reader-gate.txt.
Exception du429 : les quatre GET de source du banc, sous session administratrice,
sont les seules lectures autorisées à atteindre ce FD ; la cinquième demande
UI doit être refusée avant sa lecture physique. Le jeton Read ne lit pas de source.

L’opérateur et son secours restent inchangés : garde avant SEIZE, mêmes images,
CID/démarrage/PID/naissance/cgroup/référence, acquisition<40s, maintien≤45s depuis
armement, alarme50s et secours indépendant60s. Aucun buffer, registre, fichier
ou résultat syscall n’est altéré. La libération rend la vraie réponse serveur.
Les transports, lecteurs, timer/service et garde sont joints avant la suite.
Ne pas combiner cette barrière avec le verrou SQLite de sauvegarde.

## Dix groupes ciblés, ordinateur et mobile

Les sept premiers parcours suivants sont exécutés à1440×1000 et390×844, après
les deux groupes accueil/SSO puis publication originale/invocation. Une seule
invocation nominale termine chaque groupe après ses deux viewports : huit
invocations distinctes au total. Le huitième parcours est un groupe unique de
consolidation, après tous les précédents. Chaque variante d’adoption/recalage
repart d’un brouillon neuf et de son UI préparée dans chaque viewport.

1. **Sauvegarde** : fichier de travail déjà ouvert en édition, détail retenu,
   PUT UI réellement achevé, puis libération. L’ancien200 ne réinstalle ni
   comparaison ni focus et le texte sauvegardé reste courant.
2. **Surface** : détail retenu, Lire le code publié réellement appliqué, puis
   libération. URL/surface restent courantes ; ancienne comparaison absente.
3. **Adoption** : conflit409 réel, saisie locale conservée, copie serveur relue.
   Ouvrir ensuite le détail retenu et confirmer l’adoption depuis le flux.
   Éprouver garder la saisie et utiliser le texte serveur séparément. Aucune
   mutation PUT ne vient de cette adoption locale. Relever le focus immédiatement
   après disparition de la confirmation, puis après la réponse tardive : il doit
   être exactement sur le textarea en édition du fichier courant, sans être
   repris par l’ancien détail. Ces mesures restent
   distinctes de la conservation du texte et de la version serveur.
4. **Abandon** : détail retenu, DELETE UI confirmé et achevé, puis libération.
   Brouillon absent et source ouverte ; l’ancien200 ne réinstalle pas la section.
5. **Choix volontaire du focus** : détail retenu, focus et saisie dans la
   recherche de chemin sans soumettre ; libération. Le H3 reçu apparaît mais
   ne vole pas le focus ni la saisie de ce contrôle.
6. **Recalage** : afficher une vraie page5+2, reader-gate.txt sur la seconde.
   Les six autres chemins sont triés avant lui ; vérifier réellement les deux pages.
   Un autre onglet/API réduit les différences à≤5 sans actualiser cette UI,
   en conservant ce chemin. Cliquer son ancien bouton produit le vrai GET
   offset5&path puis, après libération, offset0&path. Le détail courant reçoit
   H3 quand le focus était retombé sur body. Rejouer avec focus volontaire dans
   un autre contrôle : la seconde requête conserve l’origine du premier geste,
   et ce contrôle garde le focus. Aucun recalage de liste n’est inventé.
7. **Refus et reprise** : chemin ajouté affiché puis réellement retiré par
   l’autre onglet/API ; son ancien bouton donne404, avec repli H2 et retry sain.
   Puis quatre vrais lecteurs retenus rendent le détail UI cinquième demande :
   vrai429, Retry-After2 et repli H2. Libérer/joindre les quatre réponses avant
   le retry réussi. Le404 ne prétend pas avoir traversé la barrière.
8. **Consolidation du focus** : conserver toutes les mesures d’adoption et
   vérifier leurs quatre couples avant/après libération. Un BODY constitue un
   échec réel, pas une réussite du banc. Les observations précédentes restent
   conservées même si cette dernière assertion échoue.

Les déclencheurs de détail et confirmations sont activés au clavier ; les
autres actions utilisent les vrais champs/boutons. Captures JPEG dans le viewport
des attentes, refus, focus, adoption et reprise, inspectées individuellement.
Aucune donnée sensible n’entre dans les captures ou rapports ; jeton/session
et credentials restent seulement en mémoire. Le focus est mesuré dans le DOM,
pas déduit d’une capture. Aucun état React, listener, timer applicatif ou API
de navigation n’est manipulé pour installer artificiellement un état.

## Jonction, nettoyage et clôture

Toute intention de helper est conservée avant son lancement. Même en échec,
libérer ou récupérer le seul helper possédé, joindre les requêtes et le secours,
puis purger la fonction par les API publiques, révoquer le jeton et supprimer
service/namespace. Inventaire SQL et ressources physiques de cet UUID sont
recoupés ; aucun nettoyage global des objets étrangers. Huit invocations sont
rapprochées de leurs lignes natives et du hash actif, sans nouvelle publication.

Le recoupement physique emploiera le collecteur partagé storage-console-inspect
via native_state(mapping), comme ZIP32. Sa liste fermée n’admet pas encore le
namespace de lecteur ; ajouter seulement code-editor-read-concurrency suivi
de huit hexadécimaux avant son premier usage. UUID du rapport et inventaire
exhaustif doivent correspondre. Aucun contrôle de reçus, secrets vides, chemins,
montages/backings, Docker/réseaux/canaux/baux n’est retiré. Cette admission de
nom dans le collecteur de preuve ne change pas l’opérateur de maintien ni ses
préconditions. Le nouveau contrat et le client rejoignent l’index des sources.

Après les dix groupes,25communs frais en série. Gel propre committé/poussé,
sources/image identiques avant/après chaque phase ;38backend/quatreweb no-store,
manuel18/74SHA8a50ffa0,010/intégrités/FK, notes actives/proposées, budgets,
configuration/référence et5982originaux conservés. Une preuve incomplète reste
échouée et n’ajoute aucun groupe. Sa cause est instruite et inscrite au backlog
avant correction ; tout nouveau passage part d’un nouveau gel et de nouveaux UUID.
070.3/.4 ne ferment qu’après rapprochement avec leurs preuves antérieures ;
la persistance après redémarrage070.3 et les interruptions de publication070.5
restent distinctes et ouvertes.

## Premier passage et reprise115

Le [passage échoué](evidence/code-editor-adoption-focus-failed-dev-2026-11-22.json)
au gel4dcd24b/461sources/image433 passe neuf groupes puis échoue à la consolidation :
quatre adoptions, huit mesures BODY avant/après libération.18gates/24lecteurs et
huit handlers, purge complète,32captures inspectées ; zéro groupe qualifié et
communs non lancés. La [correction115](CODE_EDITOR_ADOPTION_FOCUS.md) conserve
ce premier passage et décide le retour au fichier avant code. Son nouveau
passage ajoute un groupe de repli au banc initial, soit11+25et neuf invocations.
