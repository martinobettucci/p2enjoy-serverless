# Quatre alias temporaires pour la pagination réelle

Proposition opératoire de SLS-066, non appliquée. Le périmètre actuellement
autorisé porte sur les seuls serverless.lelabs.tech et functions.lelabs.tech.
La seconde page de cinq domaines de la console et de la CLI exige six domaines
réels ; aucune duplication de ligne ou réponse simulée ne remplace ces noms.

## Proposition concrète

Les quatre noms suivants décrivent leur usage de qualification de pagination :

| Domaine temporaire | SPARK | Port | Transport |
| --- | --- | --- | --- |
| functions-pagination-1.lelabs.tech | infra-serverless | 18090 | TLS |
| functions-pagination-2.lelabs.tech | infra-serverless | 18090 | TLS |
| functions-pagination-3.lelabs.tech | infra-serverless | 18090 | TLS |
| functions-pagination-4.lelabs.tech | infra-serverless | 18090 | TLS |

Pour chacun : A exact vers 51.158.54.202, zone lelabs.tech, TTL 300. La console
et le SSO restent sur leur domaine canonique. L’ensemble à six domaines est
temporaire ; après qualification, retirer les quatre routes et uniquement
leurs quatre enregistrements A créés pour cette preuve, puis revenir aux deux
domaines permanents. Aucune modification d’un autre nom, type DNS, SPARK ou
système de FORGE n’est proposée.

Le précontrôle normal du 9 novembre trouve les quatre noms libres dans le
rapprochement exact/générique des routes et leurs quatre A absents dans
l’aperçu du fournisseur configuré. Ce contrôle ne fait aucune mutation et
n’interroge pas le résolveur natif pour des noms encore absents, afin de ne
créer aucun nouveau cache négatif avant publication.

## Autorisation et garde-fous d’application

L’autorisation explicite de ces quatre noms, de leur DNS et de leur nettoyage
est requise avant toute création. La proposition routes.? reste inerte. Elle
conserve les autres demandes et retire seulement les deux lignes propres déjà
acceptées/appliquées pour les domaines permanents. Le fichier officiel ne change pas.

Après autorisation : nouvelle lecture de disponibilité et des valeurs exactes,
créations par la console normale, aucun remplacement de valeur différente ni
rejeu aveugle après réponse perdue. Attendre les vraies résolutions et HTTPS
vérifiés. Conserver les identifiants et valeurs DNS exacts pour ne retirer que
ce qui est créé et toujours possédé au nettoyage. Une identité ou valeur changée
interrompt cette suppression ; ne jamais reprendre une propriété étrangère.

La preuve réutilisera les fonctions originales du dépôt. Parcours UI depuis
l’accueil, seconde page de cinq puis un domaine, copies natives et invocations
réelles ; CLI parcourant les deux pages et conservant le succès de publication
si le catalogue change après sa première page. Les scénarios et leurs sources
seront figés avant exécution. Aucun de ces résultats n’est encore acquis.
