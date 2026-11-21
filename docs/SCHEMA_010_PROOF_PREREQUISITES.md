# Préconditions des preuves courantes sur010

Contrat de [SLS-103](BACKLOG.md#sls-103), préalable à la campagne complète de078.
Décision du21novembre2026 avant code. Aucun changement du produit, schéma,
manuel, configuration officielle, routes ou captures authentiques. DEV seul,
preuves et opérations sérielles par le principal, aucun mock ni skip.

## Préconditions figées devenues fausses

La migration010 des brouillons est réellement déployée. Le composant
`control-operations.py` exige pourtant exactement001→008 ; le parcours099 du
helper `storage-legacy-environment.py` exige001→009 hors mode rétention.
Leur refus préalable ne mesure plus le produit courant. La correction conserve
les contrôles et leurs scénarios ; elle nomme l’état courant exact. Une simple
acceptation de toute version supérieure affaiblirait la preuve et est écartée.

## Résultat attendu

Le composant courant vérifie les dix noms/ordres des migrations001→010 et la
persistance après relance. Ses55groupes existants, contraintes et erreurs de
configuration restent obligatoires. Les références historiques explicites
006/007/008 restent propres à leurs images et copies privées.

Le mode099 ordinaire exige l’image effectivement servie et le schéma exact010 ;
la fenêtre temporaire utilise cette même image et applique010 au démarrage.
Ses métadonnées nomment010 sans altérer le comportement des modes historiques
ni l’exception déjà qualifiée des replays de rétention sur009. Avant toute
mutation, vérifier services/repos/configuration/identités/absence consommateurs.
Aucune base ou date fabriquée. Le reçu capacity/ready expose
`schema_migrations` (liste ordonnée des dix noms) ; les clients de déploiement
et d’admission la recoupent. La lecture du helper refuse tout autre jeu dans
le mode courant ; le replay historique conserve son propre jeu009.


La garde indépendante est copiée et figée avant la fenêtre. Les décisions de
restitution, identités, bases/artefacts originaux et interdiction de retirer des
ressources étrangères restent identiques ; le nouveau schéma ne les relâche pas.
Les anciennes sources de rétention restent scellées et inchangées.

## Preuves exigées

1. Les55groupes de control-operations sur l’image courante, schéma010 exact,
   intégrité/FK et sortie réelle ; refus existants conservés.
2. Les gardes099 nominal/EOF/SIGTERM/SIGKILL/échéance, déplacements partiels et
   sûreté consommateur/namespace étranger concernés, en série sur010.
3. Admission099 : deux handlers réellement occupés, troisième refusé sans
   invocation, minimum3 refusé ; prochain HTTP sain, cron refusé puis prochain
   créneau réussi sans rejeu ; purge et restitution natives.
4. Relevés de sources/images avant/après et nettoyages physiques ; rapports
   originaux et essais échoués conservés, aucun groupe inventé.

Le raccordement de la campagne complète reste dans078.5. L’absence actuelle de
scope schedules dans execution-suite.py est un reste explicite de ce critère,
pas une preuve fournie par ces préconditions.095 demeure la clôture globale.
