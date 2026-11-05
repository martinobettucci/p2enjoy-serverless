# Backlog

## SLS-000

Statut : [x] — socle importé, hooks standard activés, 45 contrôles Git réels
réussis. Provenance : [factory-import.json](evidence/factory-import.json).

Importer le socle opérationnel de `P2Enjoy/software-factory-base` au commit
`886ba5a28a834a5f08fd1a01ec8dd78787317559`, sans formation, publication de
formation ni design system pédagogique. Conserver les contrats globaux et
documenter les contraintes locales prioritaires. Inclure hooks exécutables,
scripts, rôles des agents et preuve réelle de leur fonctionnement avec Git.
Conserver une provenance par fichier. Spécification : [Méthode](METHODE.md).

La qualification complète QLF-001 exige zéro test ignoré et la couverture des
comportements livrés : erreurs, limites, saturation, configuration, stockage
et cycle de vie. Une dépendance absente fait échouer la campagne ; elle ne
la transforme pas en succès partiel.

## QLF-001

Statut : [x] — 38 tests HTTP E2E et 28 contrôles Docker/pannes réussis,
zéro échec et zéro test ignoré. Smoke et recréation avec reprise complète du
worker réussis. Les secrets réels sont configurés. Sources locales et déployées
identiques. [Preuve complète](evidence/qualification-dev-2026-11-05-complete.json).
Les résultats 17/19 restent historiques.

Créer un service synthétique dans `qualification/`, sans dépendance au client,
avec manifeste `serverless.yml`, handlers CommonJS et exécuteur de référence
DEV. Spécification : [DAT — Qualification](DAT.md#qualification).

Critères d'acceptation :

- contrats HTTP, événement/contexte/réponse, callback et authentification métier ;
- données persistantes par identifiant stable et cache invalidable séparément ;
- worker coopératif, interruption extérieure d'une invocation non coopérative,
  erreurs maîtrisées et invocation saine après un échec ;
- scénario synthétique d'appel entre fonctions, sans accès externe ;
- parcours E2E HTTP automatisés sur la pile réelle, sans mocks, exécutés
  séquentiellement ; aucun test ignoré, tous les prérequis exigés ;
- build et exécution Docker dans le seul SPARK DEV autorisé, puis preuve de
  conservation des données après recréation du conteneur ;
- documentation d'exploitation et trois propositions de notes dans la cellule ;
- aucune modification de FORGE et aucune utilisation du client comme fixture.

Le banc n'implémente ni SSO, ni jetons CRUD de plateforme, ni ordonnanceur cron,
ni autoscaling, ni isolation Docker par fonction. Ces exigences demeurent dans
le cadrage et feront l'objet d'unités propres à la plateforme.

Les preuves initiales sont conservées comme historique. La campagne complète
suit [la matrice](TEST_MATRIX.md) et doit vérifier chaque contrat présent avec
le code réel. Le banc ne vaut pas preuve des fonctionnalités de plateforme
non encore implémentées.


## SLS-001

Statut : [~] — objectif autonome actif ; réalisation détaillée ci-dessous.

Spécifier puis livrer par unités cohérentes les fonctions confirmées du produit :
SSO admin, namespaces/services/functions, jetons CRUD et invocations avec jeton,
règles origine/IP, gestion du code/configuration/secrets, adaptateur
serverless.yml, allocation Docker, mémoire, disques durables/cache par ID,
deadline d'invocation et extinction des instances. Chaque comportement livré
exige sa preuve E2E réelle, notamment les refus et cycles de vie.
Le banc QLF-001 constitue l'application indépendante pour cette qualification.
Aucun de ses résultats ne clôture ces fonctionnalités de plateforme absentes.

Spécification commune : [Contrat de plateforme](PLATFORM.md).

## SLS-010

Statut : [~] — composant de quota livré et qualifié par 31 contrôles réels,
zéro échec/skip ; intégration SSO et domaine DEV en attente d'accès externe.
Preuve : [stockage DEV](evidence/storage-dev-2026-11-05.json).

Qualifier le quota dur par fonction, le montage dans Docker rootless et sa
persistance. Préparer l'intégration SSO réelle, le domaine DEV et les variables
de cellule. Preuves : écriture jusqu'au plafond, isolation entre deux volumes,
remontage, nettoyage des seules ressources de l'expérience. Un accès SSO
manquant est nommé ; aucun fournisseur d'identité de remplacement.

## SLS-020

Statut : [ ] — contrôle, identité et objets.

API Python/SQLite avec migrations, SSO admin réel, sessions/CSRF, CRUD des
namespaces/services/fonctions et tokens. E2E : persistance après redémarrage,
matrice de permissions, restriction interservice/fonction, expiration,
révocation, renouvellement et refus SSO. Références : PLATFORM organisation
et identité ; schéma à persister avant implémentation.

## SLS-030

Statut : [ ] — révisions et adaptateur.

Packaging YAML, héritage, upload immuable, secrets chiffrés, validation du
handler, CJS/ESM et dépendances réelles. E2E : déployer le service témoin par
l'adaptateur, rejeter archives invalides, mettre à jour/rollback en préservant
l'identifiant. Référence : PLATFORM adaptateur.

## SLS-040

Statut : [ ] — passerelle et moteur Docker.

Invocation authentifiée, limites réelles, admission atomique, min/max/idle,
deadline, descendants, drainage et réconciliation. CORS/IP ET/OU côté backend.
E2E : succès/refus, saturation, mémoire/CPU/PIDs, délais, extinction/reprise,
authentification métier, chaînes proxy, crash du contrôle et absence de rejeu.
Références : PLATFORM origines et exécution.

## SLS-050

Statut : [ ] — stockage, crons et exploitation.

Volumes par ID, quotas et modes, archive/purge, crons UTC, logs bornés et
métriques. E2E : concurrence, saturation disque, cache, déploiement/rollback,
redémarrage, cron réellement déclenché et diagnostic autorisé/refusé.
Références : PLATFORM stockage et exploitation.

## SLS-060

Statut : [ ] — console et campagne complète.

Parcours d'administration sur les API réelles : connexion, objets, jetons,
code, variables/secrets, limites, état, stockage, historique et journaux.
Lire et appliquer les deux design systems avant implémentation. Tester depuis
l'accueil, clavier/souris, états vides/erreurs/données longues et mobile ;
inspecter les captures. Exécuter la campagne complète, mettre à jour manuel,
notes SPARK, installation/reprise, preuves et backlog. Zéro échec et zéro skip.
