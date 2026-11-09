# Capacité des uploads de code — SLS-074

## Périmètre et autorité

Cette preuve complète [FUNCTION_VERSION_EXECUTION](FUNCTION_VERSION_EXECUTION.md)
sur le contrôle008 du seul SPARK DEV infra-serverless. Elle utilise les API HTTPS
publiques, une session SSO réelle, les ZIP originaux du dépôt et le véritable
validateur Docker. Elle ne modifie ni service, ni configuration de cellule,
ni route, ni état SQL. Le helper distant est strictement en lecture seule.
Le namespace `version-upload-capacity-<8hex>` contient une seule fonction,
ses cinq candidats concurrents et son jeton Read. Les objets sont créés puis
supprimés/purgés par les API normales.

## Scénario et assertions

Le précontrôle exige l'installation au repos, les images et sources recoupées,
les réservations nulles, le budget pour quatre réservations maximales et la marge
disque réelle. Une version stable est publiée, promue et appelée ; ressources,
configuration chiffrée, ETag, cible, données et cache servent de référence.

1. Préparer cinq candidats de code seul sur le même ETag. Le candidat A utilise
   `storage-validation-delay.mjs` : son vrai import dure60s et atteint la limite
   du validateur15s. B/C/D utilisent le même ZIP `function-versions.cjs`, avec
   un marqueur pilote et un délai d'import réel de12000ms. La fonction accepte
   20s d'exécution pour que cet import reste également invocable.
2. Envoyer A puis B/C/D, chacun observé `validating` avant le suivant. Un relevé
   natif doit trouver quatre réservations maximales, quatre archives/arborescences
   et un seul validateur vivant, appartenant à A, avec son marqueur d'import.
3. Envoyer E pendant ces quatre admissions : exiger429, le message de capacité
   et `Retry-After: 5`. Son candidat reste prepared, réservation nulle, sans
   archive, code ni validation. Aucun rejeu automatique n'est permis.
4. Relire les candidats et la santé au-delà d'une période de maintenance30s,
   pendant que certains attendent encore. A doit échouer avec validation_timeout
   et nettoyage confirmé ; B/C/D terminent sans deployment_interrupted. Le relevé
   ne revendique pas l'instant d'un callback de maintenance non instrumenté.
5. B/C/D convergent vers une seule révision/hash disponible : un code_changed
   vrai, deux faux. Les événements Docker create/destroy doivent montrer quatre
   validateurs et jamais deux vivants simultanément, sans validateur pour E.
   Les réservations et les deux paquets dédupliqués sont physiquement retirés.
   La cible promue, l'ETag et l'empreinte de configuration restent identiques.
6. Relancer explicitement le même candidat E après libération des places :
   publication dédupliquée, même hash/UUID canonique, nettoyage confirmé. Appeler
   stable sans tag et pilote par hash, puis stable ; les compteurs data/cache
   continuent sans rupture et le secret est vérifié uniquement par empreinte.

## Preuves et limites

Le client `e2e/function-version-upload-capacity.mjs` conserve quatre groupes :
admissions/refus, attente/convergence, relance explicite, intégrité et appels.
Le prérequis stable et le nettoyage ne gonflent pas ces quatre groupes.
`function-version-upload-capacity-inspect.py` relève réservations, artefacts,
validateurs et événements natifs pour les seuls UUID du namespace. Les appels
HTTPS sont joints même en cas d'échec. Aucun échec n'est transformé en succès.

La collecte finale recoupe la purge physique, les parents supprimés, le jeton
révoqué, l'absence de validateurs/canaux/instances et les sources/images avant et
après. Cette campagne backend n'ajoute aucun comportement ni parcours UI ;
aucune nouvelle vérification visuelle n'est revendiquée. Les autres fautes,
migrations perturbées et la campagne complète restent obligatoires dans SLS-074.
Les rapports et commandes reproductibles sont documentés après exécution réelle.

L'inspection suit les transitions réelles : après un échec de lecture du marqueur
par exec, elle relit le même identifiant dans Docker. Un404 confirme sa disparition ;
un200 avec Running=false confirme son arrêt, conservé dans le relevé. Un conteneur
encore vivant reste une erreur de collecte. L'observation initiale exige toujours
A vivant et son marqueur présent. Cette règle ne remplace aucune réponse Docker.
