# Registre des incohérences

## IR-002 — Contrat des adresses encore rédigé avant les versions par hash

Constat documentaire du 21 novembre 2026 pendant la boucle IR-001, en lisant
le contrat requis de SLS-109. INVOCATION_URLS.md, section API et calcul commun,
annonce encore que SLS-074 « ajoutera les versions par hash et la promotion »
et décrit sa résolution seulement comme révision active. Son chapitre de
transport historique nomme aussi le GET sans version et une cible active.
Les sources courantes et FUNCTION_VERSION_EXECUTION décrivent déjà le
catalogue explicite d’un pilote et la promotion séparée.

Mesure : les paragraphes de contrat courant ne distinguent pas suffisamment
le comportement actuel des preuves historiques. Aucune preuve historique ni
aucun client de transport complémentaire n’est modifié par IR-001.
Issue à instruire dans la prochaine boucle après preuve ciblée verte de109 :
clarifier le contrat courant et marquer l’époque des preuves de transport,
sans réécrire les résultats acquis ni présumer leur qualification actuelle.
Un écart exécutable distinct découvert doit recevoir une unité avant correction.
