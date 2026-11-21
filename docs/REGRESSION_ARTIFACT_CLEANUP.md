# Conservation des artefacts pendant la campagne complète

Contrat de [SLS-106](BACKLOG.md#sls-106), préalable opérationnel à105 et078.
Constat du21novembre2026 après l’arrêt execution-ui : les compteurs sont nuls,
les services sains et l’intégrité correcte, mais le lecteur natif refuse
l’inventaire original attendu5982/SHA846904e1. La cause et le sens de cet écart
ne sont pas encore établis. Aucun effacement ou changement original déduit.

## Instruire sans mutation

Conserver le résultat du worker, les rapports exacts des phases et leurs SHA,
les identités originales et la configuration. Relever l’inventaire courant en
lecture seule et le comparer à un inventaire original5982 déjà scellé avant
la campagne ; conserver les listes exactes manquantes/modifiées/ajoutées.
Rattacher chaque révision ajoutée à sa fonction, son namespace, sa campagne
et ses reçus, à partir des rapports et de SQLite RO sous propriétaire.
Une différence sans appartenance certaine reste protégée.

## Correction bornée

Persister la cause et la décision avant code ou nettoyage. Si un client conserve
encore son code après archive malgré son succès cleanup, corriger son finally
pour attendre sa vraie purge API et la vérifier physiquement. Supprimer uniquement
les objets créés par cette campagne et identifiés explicitement ; aucune purge
d’archive étrangère, aucune suppression SQL, aucun effacement manuel d’artefacts.
Si un original manque ou change, conserver l’incident et définir sa restauration
avec preuve d’identité avant toute mutation ; ne jamais remplacer la plateforme
entière pour faire disparaître l’écart.

Rejouer le client responsable sur vrai code déployé, puis25communs. Joindre ses
purges/révocations, états natifs et captures pertinentes, invariants de contrôle,
référence, configuration et5982artefacts. Tous les essais incomplets restent
exclus des comptes de qualification. Une preuve manquante garde106[~] et interdit
la reprise de la campagne543. Aucune cause ou réussite n’est présumée ici.
