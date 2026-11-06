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

Statut : [x] — composant de quota qualifié par 31 contrôles réels,
zéro échec/skip ; client SSO créé, authentification du client vérifiée,
variables/secret de cellule appliqués, DNS et TLS DEV opérationnels.
Preuve : [stockage DEV](evidence/storage-dev-2026-11-05.json).

Qualifier le quota dur par fonction, le montage dans Docker rootless et sa
persistance. Préparer l'intégration SSO réelle, le domaine DEV et les variables
de cellule. Preuves : écriture jusqu'au plafond, isolation entre deux volumes,
remontage, nettoyage des seules ressources de l'expérience. Un accès SSO
manquant est nommé ; aucun fournisseur d'identité de remplacement.

## SLS-020

Statut : [~] — contrôle et console initiale déployés ; qualification en cours.

API Python/SQLite avec migrations, SSO admin réel, sessions/CSRF, CRUD des
namespaces/services/fonctions et tokens. E2E : persistance après redémarrage,
matrice de permissions, restriction interservice/fonction, expiration,
révocation, renouvellement et refus SSO. Références : PLATFORM organisation
et identité ; [schéma](SCHEMA.md) et [API du contrôle](CONTROL.md).
La tranche de console associée expose ces objets et le parcours SSO dès cette
unité ; SLS-060 complète ses facettes d'exécution et la campagne transversale.
Les parcours publics, l'accueil navigateur, la provenance réseau et les
limites de connexion sont éprouvés. Les scénarios administrateur préparés
attendent une connexion au vrai SSO ; ils ne sont pas déclarés réussis.
Le [checkpoint du 6 novembre](evidence/control-dev-checkpoint-2026-11-06.json)
regroupe six groupes HTTP, neuf contrôles navigateur, quatre chemins réseau,
six scénarios de limite par client, deux de capacité globale et dix-sept
de panne/reprise. Deux contrôles supplémentaires éprouvent l'interruption
du pilote de preuve. Les dépendances verrouillées sont auditées.

La revue du contrat OIDC du client créé précise les travaux SLS-020 restants :
état d'attente distinct d'une erreur technique pour verified/admin manquant,
contrôle de l'azp de l'ID token en complément de son audience, et réponse
temporaire préservant la session lorsqu'un nouveau kid arrive dans la fenêtre
anti-refresh JWKS de deux secondes. Les comptes réels et une rotation réelle
maîtrisée sont nécessaires aux preuves correspondantes ; aucune n'est déclarée
réussie. La durée de 300 secondes se mesure sur le jeton réellement émis.

## SLS-030

Statut : [~] — CLI de packaging et composants qualifiés ; publication DEV intégrée, preuve authentifiée ouverte.

Packaging YAML, héritage, upload immuable, secrets chiffrés, validation du
handler, CJS/ESM et dépendances réelles. E2E : déployer le service témoin par
l'adaptateur, rejeter archives invalides, mettre à jour/rollback en préservant
l'identifiant. Référence : PLATFORM adaptateur et [DEPLOYMENT](DEPLOYMENT.md).
Cette unité poursuit les parties indépendantes pendant l'attente de session
SSO de SLS-020. Les preuves d'upload/publication exigent toujours cette session.
Le [checkpoint CLI](evidence/adapter-package-dev-2026-11-06.json) comporte
24 scénarios réels réussis dans Docker sur le SPARK, avec source et images
identifiées. Le [checkpoint du chargeur](evidence/runtime-validation-dev-2026-11-06.json)
ajoute 36 scénarios réels : formats CJS/ESM, dépendances, confinement, logs,
échéance extérieure, protocole Unix et destruction des descendants.
Le [checkpoint d'extraction](evidence/artifacts-dev-2026-11-06.json) ajoute
112 contrôles réels : formats et refus, limites exactes, disque saturé,
courses sur les chemins et la source, puis packaging/extraction/chargement
Node des douze fonctions. Le [checkpoint du contrôle de publication](evidence/deployment-control-dev-2026-11-06.json)
intègre les routes de préparation, upload, historique, rollback et suppression,
la migration 003, le budget et la reprise. Huit groupes publics et trente
contrôles réels de configuration/démarrage/panne passent sur l'image déployée.
Le client authentifié échoue au prérequis de session SSO : aucun de ses onze
groupes n'est déclaré réussi. Admission globale, expiration, limites de révisions,
crash pendant upload/validation et arrêt pendant nettoyage restent à qualifier.
La commande deploy, les vues de révisions et le moteur restent à réaliser.

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
