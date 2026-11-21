# Surveillance du stockage et fermeture de l’invocation

Contrat de [SLS-112](BACKLOG.md#sls-112), découvert pendant le diagnostic111.
Les passages isolé14 et contextuel162 réussissent ; l’ancienne assertion reste
inconnue. Ce constat de code distinct ne les transforme pas en reproduction.

## Ordre possible et discriminant

Instance.invoke atteint son timeout puis appelle self.close virtuel. Le pilote
géré détruit Docker et libère son bail avant de rendre le résultat interne.
Le watcher reste actif jusqu’au finally externe, sans lire closing ni le verrou
de stockage. L’agent sérialise release/check, mais un check après release voit
lease_unknown. Si le watcher termine ainsi avant les tests watcher.done, le
except StorageError externe peut remplacer invocation_timeout par
storage_unavailable. Aucun verrou ni branche ne l’exclut dans les sources lues.
Les ordres où le watcher est annulé avant sa réponse conservent le timeout.

Lire intégralement managed_instances.py, instances.py, storage_client.py,
les opérations release/check et leur verrou dans agent.py/agent_volumes.py,
[EXECUTION](EXECUTION.md#canal-privé-et-terminaison) et
[STORAGE_AGENT](STORAGE_AGENT.md#instances-avec-baux-gérés). Une fermeture volontaire
ne constitue pas une perte de stockage ; une vraie perte avant fermeture reste
une erreur. Une suppression non confirmée conserve cleanup_failed et ses baux.

Observer les vraies tâches asyncio appartenant à la même instance : coroutine,
identité self/UUID, références retenues et callbacks de terminaison. Ne conserver
aucun local de frame ni corps/log ; projections allowlistées du résultat interne
et final, exception fixe du watcher, états closing/lease_possible et identité
corrélée du bail. Les instants de lecture sont des observations monotones, pas
une reconstruction du moment exact des événements internes. Ne wrapper ni
remplacer storage.call, le pilote, Docker, FUSE ou l’agent.

Le triplet watcher=lease_unknown, interne=invocation_timeout et final=
storage_unavailable pour le même appel établirait l’écrasement. Une autre erreur
reste un autre diagnostic. Sans triplet, ne pas prétendre la course reproduite.

## Expérience bornée avant correction

Sur le vrai pilote embarqué et le handler original volume-operations.cjs,
une seule campagne de dix cas distincts, deadlines 1,75 /1,80 /1,85 /1,90 /1,95 /
2,00 /2,05 /2,10 /2,15 /2,20 secondes et sommeil applicatif30s. Chaque cas crée
un vrai consommateur/UUID et fichier distincts, observe les tâches puis rejoint
le nettoyage. Les données/cache/quota FUSE et l’agent restent réels. Le résultat
attendu reste invocation_timeout, retrait complet et écriture relue ; tout refus
ou différence échoue sans réessai et conserve ses observations avant assertion.
Cette variation exerce les phases de la surveillance0,5s sans charge artificielle,
simulation d’horloge ou modification du programme produit. Les14groupes de111
restent séparés et conservent strictement2s/30s.

Conserver code/source/image, rapport, sorties et repos natif avant/après. Purger
les seules fonctions originales de cette campagne et confirmer ressources,
baux, processus et chemins absents. Arrêter au premier échec ; aucun rejeu
conditionnel. Un passage nominal ne prouve pas l’absence générale de course.
Toute correction produit attend un diagnostic établi et sa décision committée.
Les pannes réelles FUSE/agent, annulations et drainage doivent rester qualifiées,
puis25communs et nouvelles captures ouvertes individuellement. La campagne
entière078 et toutes les autres unités gardent leurs preuves propres.
