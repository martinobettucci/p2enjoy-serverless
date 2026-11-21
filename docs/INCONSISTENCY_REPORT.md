# Registre des incohérences

## IR-004 — Ancienne assertion indéterminable et préalable de reprise111

Unité en cours : [SLS-111](BACKLOG.md#sls-111). Sources :
[MANAGED_STORAGE_REGRESSIONS](MANAGED_STORAGE_REGRESSIONS.md#diagnostic-avant-décision),
[qualification112](evidence/managed-invocation-watch-dev-2026-11-21.json),
[SCHEDULE_REGRESSIONS](SCHEDULE_REGRESSIONS.md#rapports-frais-et-conservation).

Constat mesuré : le rapport scellé61f05271 du cinquième078 contient six succès
puis une AssertionError sans ligne ni résultat deadline conservé. Plusieurs
assertions du septième groupe sont possibles. Le diagnostic isolé14 et le
préfixe contextuel162 passent sans reproduction ; aucun ne révèle l’ancienne
cause. L’instrumentation95d2e16 conserve désormais les discriminants. La course
produit distincte112 est reproduite séparément, corrigée et qualifiée82 sur433,
dont le sous-ensemble39 satisfait111.3.111.1/.2 restent ouverts et le texte111
se dit préalable au prochain078, alors que le registre078 dépend de040/074.

Incohérence à instruire : demander une cause historique non observable comme
préalable de tout nouveau passage complet empêche de recueillir de nouvelles
preuves sans autoriser une attribution inventée. Les contrats111 demandent
simultanément de laisser111ouverte si le défaut ne se reproduit pas. Les
exigences réelles (14groupes inchangés, fautes natives, diagnostics, nettoyages,
25communs, campagne078 complète fraîche) doivent rester intactes.

Issue à décider selon CLAUDE.md §5 : préciser le résultat qualifiable de la
reprise du banc et le traitement de l’incertitude historique, à partir des
précédents locaux ; aucune clôture111 ni modification de scénario appliquée
par cette entrée. Ne pas assimiler112 à l’ancienne assertion, ne pas relancer
un test pour effacer son échec et ne retirer aucun critère produit utilisateur.
