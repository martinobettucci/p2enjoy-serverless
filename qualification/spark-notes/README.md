# P2Enjoy Serverless

Ce SPARK héberge la plateforme de fonctions Docker sur l’infrastructure de développement LeLabs.

## Services et accès

- https://serverless.lelabs.tech : console React et API Python, servies par `serverless-api` sur le port 18090 derrière la route TLS.
- `serverless-runtime-reference` : exécuteur des douze handlers synthétiques du dépôt, accessible sur la boucle locale du SPARK, port 18080.
- `p2enjoy-storage-dev.service` : agent de quotas et de volumes persistants par UUID de fonction, avec socket Unix privé.
- Les validateurs de code, instances de fonctions et clients de qualification sont des conteneurs distincts, identifiés par leur rôle et leur propriétaire.

## Fonctions disponibles

Le SSO LeLabs exige les rôles `verified` et `admin`. La console gère namespaces, services, fonctions, politiques d’origine/IP, variables, secrets et jetons CRUD limités au service ou à certaines fonctions.

L’adaptateur Python lit `serverless.yml`, prépare des archives et publie les fonctions par HTTPS. Le contrôle valide réellement le handler dans Node/Docker, conserve les révisions et fournit historique et rollback. Le rollback du code conserve les réglages applicatifs et les volumes courants.

Les créations, changements de quotas, publications et suppressions sont raccordés à l’agent réel. La décision durable du contrôle et l’objet sont commis ensemble. Avant cette décision, une interruption reprend l’abandon ; après, elle confirme la mutation. La suppression archive données et cache en conservant leur allocation. Leur purge est distincte.

## État de réalisation

Le moteur public exécute les fonctions publiées avec un jeton Read. Il réserve CPU, mémoire et place d’instance avant Docker, applique minimum/maximum/concurrence et extinction après inactivité, puis réconcilie ses ressources au redémarrage sans rejouer les appels incertains. Les générations de code et configuration conservent les appels déjà admis ; les changements de stockage drainent les instances au repos et refusent les invocations actives.

La passerelle applique les politiques d’origine/IP et CORS. Les API d’observation exposent états, allocations, mesures Docker et journaux expurgés. Les facettes Instances et Invocations montrent les allocations, mesures, états et journaux expurgés dans la fiche de fonction. La facette Code et révisions permet de publier un ZIP, suivre ou abandonner une préparation, consulter les métadonnées, activer et supprimer les révisions. Les commandes publiques de purge/cache et le catalogue d’archives sont déployés ; leur qualification transversale reste ouverte dans SLS-065. Les crons, cycles SSO et pannes résiduelles sont recensés dans le backlog.

Preuve moteur : `docs/evidence/execution-dev-2026-11-06.json` dans le dépôt du projet. Elle recoupe sources, image, rapports, archives, ressources web et configuration officielle. Les campagnes sont sérielles, sans mock, doublure ou test ignoré. Les archives de code conservées sont distinguées des volumes de qualification explicitement purgés.

La publication de code conserve côté serveur les ressources, variables, secrets, volumes et routes courants. Son UUID est connu avant l’envoi ; revenir sur la même adresse permet de consulter son issue sans rejouer la publication. La console relit l’état après une erreur de mutation et distingue une publication enregistrée dont la confirmation de stockage attend encore.

La qualification `python3 -B e2e/execution-suite.py --scope publication` passe 18 campagnes en série et 312 groupes réels, sans échec ni cas ignoré. Elle réunit moteur et console sans répéter les campagnes communes. La preuve `docs/evidence/publication-console-dev-2026-11-07.json` recoupe sources, image, rapports frais, captures relues, archives et ressources nettoyées. Les pannes de nettoyage sont éprouvées sur les seules révisions de campagne, avec garde indépendante puis maintenance normale.

Le manuel d’usage se consulte dans la navigation, à /console/manual. Ses treize chapitres et 39 paragraphes viennent de l’unique source `docs/manual.md`, compilée avec chaque version de la console et mise à jour avec les comportements utilisateur. La campagne E2E compare le contenu rendu et son empreinte à ce fichier.

L’agent de stockage dispose maintenant d’effacements corrélés : reçu durable,
répétition sans second vidage et reprise après erreur physique ou interruption.
Le schéma agent est 004. Sept campagnes et 106 groupes réels passent, avec
nettoyage recoupé : docs/evidence/storage-discard-dev-2026-11-07.json.
Ces opérations sont raccordées aux commandes publiques de cache/purge
et au catalogue d’archives. Les reprises ciblées de SLS-065 sont éprouvées ;
la suite commune élargie reste à terminer. La purge conserve les artefacts
tant que sa garde existe, y compris après redémarrage si le stockage a changé.

La configuration du provider est conservée dans le service ; les fonctions
portent seulement leurs surcharges. Les jetons restent gérés au niveau service.
Treize groupes ciblés couvrent héritage, secrets, droits, limites, échec partiel
et redémarrage. Avec les régressions et les clients Docker, la preuve
`docs/evidence/service-configuration-dev-2026-11-08.json` réunit 191 groupes
en série et 21 captures inspectées. Les adresses d’appel multi-domaines restent
suivies dans SLS-066.
