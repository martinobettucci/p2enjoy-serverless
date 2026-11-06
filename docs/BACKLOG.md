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

## SLS-011

Statut : [x] — noms et domaine appliqués, persistance et connexion SSO réelle
sur la nouvelle adresse vérifiées.

Rendre les noms Docker explicites par rôle et adopter `serverless.lelabs.tech`
dans le SPARK de développement. Contrat : [noms d’exploitation](DEPLOYMENT_NAMES.md).
Conserver les données et les identifiants Compose, qualifier la recréation
réelle, la route TLS 18090, la configuration officielle et le parcours SSO.
Le nouveau callback est accepté par le vrai fournisseur le 6 novembre ; la
route a été corrigée vers 18090 par le responsable. Les deux conteneurs sont
healthy sous leurs nouveaux noms, avec les mêmes images, volumes, objets et
identité de base. Compteur, cache et checkpoint sont retrouvés par HTTP ; le
calcul reprend jusqu’au résultat complet. 38 tests HTTP, neuf contrôles
navigateur, huit groupes publics, quatre chemins réseau et quatorze contrôles
CLI passent. La connexion personnelle sur le nouveau domaine produit une
session authentifiée et l’API administrateur des namespaces répond 200.
[Preuve de migration](evidence/deployment-names-dev-2026-11-06.json).

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
limites de connexion sont éprouvés. La [preuve de gestion authentifiée](evidence/control-management-dev-2026-11-06.json)
recoupe 19 groupes API, 11 parcours UI et huit groupes publics sur l'image
déployée. Nettoyages confirmés, sept captures relues. Le nom maximal du fil
d’Ariane mobile revient à la ligne et les trois gestes de fermeture du menu
rendent le focus au bon contrôle, y compris après passage au desktop.
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

Statut : [~] — publication API/CLI, plafonds de candidats/révisions et deux reprises après SIGKILL qualifiés ; autres limites et UI ouvertes.

Packaging YAML, héritage, upload immuable, secrets chiffrés, validation du
handler, CJS/ESM et dépendances réelles. E2E : déployer le service témoin par
l'adaptateur, rejeter archives invalides, mettre à jour/rollback en préservant
l'identifiant. Référence : PLATFORM adaptateur et [DEPLOYMENT](DEPLOYMENT.md).
La session SSO réelle est disponible pour les preuves d'upload et de publication.
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
La [preuve authentifiée](evidence/deployment-authenticated-dev-2026-11-06.json)
recoupe onze groupes API et sept groupes CLI : droits, refus, import et logs
expurgés, révocation/conflits pendant validation, admission unique, rollback,
suppression de révisions inactives et huit candidats par fonction. Les 35
archives conservées des campagnes sont vérifiées sur disque ; aucun objet
actif, candidat non terminal, réservation, canal ou conteneur de validation
ne subsiste à ce checkpoint. La [preuve de reprise](evidence/publication-recovery-dev-2026-11-06.json)
ajoute quatre groupes : 64 candidats globaux, vingt révisions, SIGKILL pendant
réception partielle puis pendant validation Docker vivante. Les candidats
interrompus échouent sans publication, les configurations et archives
précédentes sont intactes, les ressources sont libérées et de nouveaux uploads
réussissent. Les 53 archives antérieures et vingt nouvelles archives conservées
sont recoupées. Expiration, budget/marge disque, déconnexion concurrente et
arrêt pendant nettoyage restent à qualifier.
La commande deploy est désormais implémentée : sa [preuve ciblée](evidence/adapter-deploy-dev-2026-11-06.json)
conserve 14 contrôles de prérequis et de refus HTTPS réel, plus les 24 scénarios
plan/package rejoués. Les sept groupes CLI authentifiés réussissent onze
premières publications, la pagination, les mises à jour à UUID conservé,
les refus de droits, le résultat partiel et la reprise du même brouillon.
Rupture après envoi, modification locale concurrente, réponse trop grande et
redirection restent à éprouver. Les vues de révisions et le moteur restent
à réaliser ; l'exécution du code après rollback n'est pas encore qualifiée.

## SLS-040

Statut : [~] — pilote d’instances implémenté ; admissions et passerelle en réalisation.

Invocation authentifiée, limites réelles, admission atomique, min/max/idle,
deadline, descendants, drainage et réconciliation. CORS/IP ET/OU côté backend.
E2E : succès/refus, saturation, mémoire/CPU/PIDs, délais, extinction/reprise,
authentification métier, chaînes proxy, crash du contrôle et absence de rejeu.
Références : PLATFORM origines et exécution, [EXECUTION](EXECUTION.md).
La tranche initiale fournit le superviseur chaud, son enfant neuf et le pilote
Docker réel. Les campagnes d’invocation et de courses de cycle sont présentes,
avec régression du chargeur partagé : 31 + 11 + 36 contrôles réels réussis,
zéro échec et zéro test ignoré. La [preuve](evidence/instances-dev-2026-11-06.json)
est conservée séparément des parcours API. Le pilote est maintenant raccordé
aux baux de l’agent FUSE, avec quatorze groupes réels. Les admissions, min/max/idle,
générations et invocation authentifiée restent à intégrer et qualifier.

## SLS-050

Statut : [~] — agent local installé en DEV ; raccordements et preuves de reprise à poursuivre.

Volumes par ID, quotas et modes, archive/purge, crons UTC, logs bornés et
métriques. E2E : concurrence, saturation disque, cache, déploiement/rollback,
redémarrage, cron réellement déclenché et diagnostic autorisé/refusé.
Références : PLATFORM stockage et exploitation, [STORAGE_AGENT](STORAGE_AGENT.md).
Le registre durable, les baux et la supervision FUSE sont implémentés. Quinze
groupes de cycle, huit de limites et les 31 contrôles du proxy passent, avec
nettoyage confirmé, zéro échec et zéro skip. La [preuve recoupée](evidence/storage-agent-dev-2026-11-06.json)
est complétée par quatorze groupes de raccordement au pilote d’instances :
[preuve](evidence/managed-storage-dev-2026-11-06.json). Les mutations publiques
et les admissions restent à raccorder. Les quotas préparés et leurs reçus sont
implémentés ; dix groupes vérifient les décisions, réservations, SIGKILL pendant
préparation et reprise d'abandon partiel avec conservation des données.
La [preuve recoupée](evidence/storage-preparations-dev-2026-11-06.json) ajoute
37 groupes de régression, avec nettoyages confirmés, zéro échec et zéro skip.
L'acquisition partielle après interruption, la marge physique et les pannes de registre
restent à qualifier ; aucune clôture de SLS-050 ne repose sur ces seuls composants.

## SLS-060

Statut : [ ] — console et campagne complète.

Parcours d'administration sur les API réelles : connexion, objets, jetons,
code, variables/secrets, limites, état, stockage, historique et journaux.
Lire et appliquer les deux design systems avant implémentation. Tester depuis
l'accueil, clavier/souris, états vides/erreurs/données longues et mobile ;
inspecter les captures. Exécuter la campagne complète, mettre à jour manuel,
notes SPARK, installation/reprise, preuves et backlog. Zéro échec et zéro skip.
