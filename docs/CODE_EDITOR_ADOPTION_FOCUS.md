# Retour du focus après adoption du brouillon

Contrat de [SLS-115](BACKLOG.md#sls-115), découvert le22novembre2026 dans
le [banc d’attentes UI](CODE_EDITOR_UI_CONCURRENCY.md). Les règles de focus
du socle§§9.5/14.3 et l’écart APP-DS-001 du produit restent applicables.

## Défaut réel conservé

La [preuve négative](evidence/code-editor-adoption-focus-failed-dev-2026-11-22.json)
porte le gel4dcd24b66855b36a8b7a706b0d2afdf8d030d6f9,461sources/image433da150,
campagne66c0ba0c-5270-43b8-8fee-5bc439f1baec. Rapport SHA
f88cf074064f61795a5406075b4194d17d3d26e809bf52e720a7e2c9186c0d81.
Neuf groupes passent et le dixième échoue ; zéro groupe qualifié, communs non lancés.
Le pilote8525fefc est terminé sortie1 et joint.32JPEG ouverts individuellement,
y compris les deux couples mobiles de SHA identiques.18gardes restaurées,
24lecteurs, seize instantanés tardifs et huit invocations Docker recoupés.
Fonction/jeton/parents et ressources physiques nettoyés ;38backend/quatreweb,
010, manuel18/74SHA8a50ffa0, notes/configuration/référence et5982originaux conservés.

Les quatre variantes garder/remplacer×ordinateur/mobile ont chacune deux
projections DOM après rendu : BODY/on_fieldfalse avant puis après libération.
Le texte choisi et la version sont corrects, l’adoption n’émet aucun PUT.
BODY avant la réponse tardive distingue ce défaut d’un vol de focus causé par
cette réponse ; ni la capture ni le seul message haché ne fondent la cause.

## Cause et choix avant code

`adoptServer()` retire conflict, donc le bloc contenant ses deux Confirm.
La restauration de Confirm appartient au composant démonté et ne peut plus
atteindre son déclencheur. Le parent n’établit aucun relais vers le fichier.
Les refs fileArea/fileHeading et les intentions focusEdit/focusFile existent
déjà, avec un effet de layout après commitDOM. Le textarea en édition reste
monté pendant les quatre variantes mesurées.

Décision réversible : après les validations de l’adoption réussie, confier au
parent une intention de focus de fichier. Au rendu courant, le textarea reçoit
le focus si le fichier reste éditable et en édition ; sinon le h2 stable du
fichier le reçoit. Réutiliser les refs/effet existants. Aucune restitution dans
un finally ni focus direct sur une ancienne référence de confirmation. Les
lectures périmées restent annulées par invalidateDiff ; leur réponse ne doit
ni réinstaller le détail ni modifier le focus rendu.

Garder/remplacer ne sauvegarde pas et ne change pas les droits, le texte choisi,
la version serveur ou la base. Annuler ferme la confirmation et rend le focus
au déclencheur selon Confirm ; un refus la conserve ouverte et refocalise son
contrôle. Aucun de ces deux chemins n’arme l’intention de focus fichier.
Aucun changement global de Confirm, CSS, dépendance, schéma,
configuration, route ou secret. Le manuel canonique et le design du produit
décriront ce retour au fichier dans le même changement que le composant.

## Nouveau passage requis

Conserver les dix groupes originaux du banc, ses18gates/24lecteurs, quatre
couples d’adoption face à la réponse retenue et assertions sans PUT. Ajouter
avant la consolidation un onzième groupe pour le repli du focus : fichier
ouvert en lecture, existence/absence serveur et garder/remplacer, dans chaque
viewport, soit huit variantes. Préparer par API un nouveau brouillon, ouvrir
le fichier par l’UI sans Modifier ; un autre onglet/API modifie ou retire ce
fichier. Actualiser le contexte puis Relire le brouillon serveur et confirmer
l’adoption par les contrôles réels. Mesurer le h2 du fichier encore nommé, ou
Contenu du fichier après retrait de sa sélection. Relever séparément texte
affiché, version/texte serveur et leurs SHA ; aucune écriture implicite.
Un résultat inattendu devient un reste identifié avant traitement.

Une invocation après ce groupe apporte neuf invocations au total. Il ne
contient aucun gate supplémentaire. Huit JPEG de repli s’ajoutent aux32ciblés,
puis25communs frais : onze+25=36groupes,40JPEG ciblés et22captures communes.
Tous sont inspectés individuellement. Le passage échoué reste exclu, sans
réutilisation de groupes, de captures ou de reçus. Aucun mock/interception.

Construire et déployer le seul contrôle DEV après sauvegarde SQLite native
sous propriétaire1001, au repos, sans garde ; conserver les données, paramètres,
référence et originaux. Le changement intentionnel d’image/CID/démarrage est
séparé de la baseline du nouveau passage. Le client exige l’image exacte
nouvellement construite ; aucun pin découvert silencieusement. Nouveau gel
committé/poussé/synchronisé et nouveaux UUID avant les36groupes, avec les mêmes
recoupements sources/images/38backend/quatreweb/no-store/010/manuel/notes/budgets/
configuration/référence/5982originaux et nettoyages physiques.

115 ne ferme qu’après ces preuves ;070 reste ouvert pour la persistance après
redémarrage et les interruptions de publication, qui ne sont pas prouvées ici.

## Image construite et préparation de bascule —22novembre2026

Build au gel d028cb8/462sources : image exacte
`sha256:04604089a8cb61d6015be0cde1671f29265878ff4f6f081509542ebc126055fc`.
38backend identiques aux sources et quatre ressources web identiques au build
local ; manuel18/74SHA8d2434cf. API433/CIDa9c2bb4d et référence af6 restent
inchangés pendant le build, avec repos/configuration/originaux recoupés.
Le client de qualification exigera explicitement04604089 ; ce changement de
pin et les métadonnées de bascule n’affectent aucun octet applicatif construit.

Avant recréation : vérifier les identités/démarrages exacts du relevé final,
repos et absence de garde ; sauvegarder SQLite contrôle et registre avec
intégrités sous propriétaire1001. Conserver les comptes de tables, migrations,
fichiers officiels et inventaire des5982originaux. Retenir l’image433 dans un
tag de retour propre à cette seule opération, et comparer les environnements
par défaut des deux images, sans exporter de valeurs.

La commande Compose du seul service control emploie les deux fichiers officiels,
--no-build et --wait90s. En cas d’échec de bascule/recoupement, vérifier qu’aucun
autre opérateur n’a remplacé l’image attendue avant de rétablir le tag de
composition vers433 et recréer le seul contrôle. Ne restaurer aucune base :
le changement de focus n’ajoute pas de migration. Conserver l’échec et son
reçu de retour, sans relance E2E automatique. Ce retour borné évite qu’une
erreur d’image laisse le contrôle indisponible ; il ne touche pas la référence.
Une image, un conteneur ou une configuration d’origine inconnue interdit ce
retour automatique et conserve les observations pour instruction.

La bascule attache au seul conteneur control une étiquette d’opération unique,
via un complément Compose privé dans le dossier de sauvegarde. Ce fichier ne
contient que cette étiquette ; les deux fichiers officiels, l’environnement et
le service de référence restent inchangés. Le retour admet uniquement le CID/
démarrage initial exact, ou le conteneur portant l’étiquette acquise de cette
opération et l’image candidate ; il conserve CID/création/démarrage/PID/naissance
observés puis les recontrôle avant recréation. Une même image sans ce lien
ne prouve pas la propriété. Le fichier et son SHA sont conservés dans le reçu.

Budget distant principal300s, secours180s, publication/jonction et marge de
transport120s : SSH600s. L’alarme distante et les commandes partagent la borne
de leur phase ; un changement de phase de secours conserve son reçu. Même sur
expiration locale, terminer/joindre le seul transport possédé, conserver son
résultat et ne pas revendiquer la fin distante sans observation. Aucune campagne
E2E ne part d’un état de bascule ou de secours non confirmé.
