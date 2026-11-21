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

## Instrumentation préparée avant première exécution

Le client e2e/managed-invocation-watch.py écrit son worker dans le tmpfs du
contrôle et utilise exclusivement les classes de production embarquées.
L’observateur identifie les deux vraies coroutines par leur nom et self, retient
leurs références et pose des callbacks de fin ; aucun appel produit remplacé.
Dix cas et leurs relectures réelles sont définis, observations avant assertion,
nettoyage de tous les consommateurs puis archive/purge de la fonction propre.

Le parent borne240s puis SIGTERM exact et jointure60s. Il conserve les flux
binaires exacts dans un dossier0700/fichiers0600, même après échéance ; parsing
et rapport final restent exécutés. Un échec parent/jointure interdit completed,
un second timeout reste inconnu avec l’identité du script conservée. Aucun rm
sur une simple réévaluation tardive du client. Les contrôles natifs restent
indispensables : la seule sortie du client ne prouve pas le nettoyage distant.
Revue statique et syntaxe conformes après correction des deux pertes de
traçabilité du parent ; aucune branche de délai ou aucun cas réel exécuté ici.
Contrat et client ajoutés à l’index,457sources ; produit et image inchangés.

## Reproduction et décision du 21 novembre 2026, avant correction

Au gel `5f8e6d3` / 457 sources / image b452, le premier cas réel à 1,75 s
échoue : consommateur `44b51897-d279-4348-b68f-84b6c91eff0c`, invocation
`db2edc59-ee3c-4998-862a-eb5585b25cda`. Le watcher termine avec `lease_unknown`
et `closing=true`, puis l’interne rend `invocation_timeout` ; l’externe conserve
ces UUID et remplace le code par `storage_unavailable`. Les observations de fin
sont espacées de 1,131 ms, sans prétendre l’instant exact du RPC. Début observé,
conteneur retiré, bail absent et relecture conforme. Rapport rouge, zéro groupe
qualifié ; worker joint, script retiré, flux exacts conservés, fonction purgée
physiquement et nominal / 5 982 originaux préservés. Ce défaut est établi ;
l’ancienne assertion muette111 reste indéterminable.

Choix : classifier étroitement le seul `lease_unknown` **au moment où le watcher
l’observe**, si une fermeture gérée est déjà engagée. Un sous-type privé
`LeaseMissingDuringClose` conserve le code et l’incertitude de StorageError.
Le catch externe ne déduit jamais ce contexte de son propre appel ultérieur
à close : une erreur observée avant fermeture reste une panne réelle, même si
le traitement de son exception est retardé jusqu’après le début de fermeture.
Aucun autre code de stockage n’est reclassifié.

Après jointure de la fermeture et de l’invocation interne, préserver son résultat
terminal original seulement si la destruction est confirmée, `lease_possible`
est faux, `cleanup_error` est faux et `instance_available` est exactement faux.
Cela vaut pour le résultat terminal du timeout ou d’une fermeture extérieure,
et pour un résultat accepté dont l’instance doit être recyclée. Aucun champ
d’observation, UUID, log, durée ou cause interne n’est réécrit. Si ces conditions
ne tiennent pas, garder le chemin existant de panne / cleanup_failed et ses
ressources de reprise. Les autres StorageError, annulations et pertes réelles
FUSE/agent suivent strictement leur chemin actuel.

Motif : corriger la classification du résultat sans modifier le cycle de vie du
watcher, les RPC, verrous, échéances ou confirmations. Arrêter/annuler le watcher
depuis close demanderait une coordination plus large, risquerait une attente
circulaire et une confusion avec une erreur déjà produite. Une priorité au seul
invocation.done ne couvre pas l’ordre rouge observé. Aucun masque général de
StorageError pendant closing n’est admis.

## Qualification de la correction et bascule DEV

Conserver les dix phases du client rouge, puis ajouter un onzième groupe de
fermeture extérieure : écriture préalablement acquittée, nouvelle invocation
active réellement observée, fermeture partagée avant son échéance de 5 s,
résultat `instance_stopped`, non-réutilisation, relecture et retrait confirmés.
Aucun succès conditionnel selon le résultat ; les mêmes tâches réelles sont
observées. Les dix phases gardent leurs valeurs et leurs assertions.

Sur les nouvelles sources figées et l’image réellement déployée, exécuter en
série les 11 groupes ciblés, les 14 gérés inchangés (dont 2 s, annulations, vrai
SIGKILL FUSE et arrêt/reprise de l’agent), les 31 groupes de la passerelle réelle,
puis 25 communs : **81 groupes uniques attendus**. Le sous-détail isolé du plafond
garde ses quatre assertions dans un seul de ces 31 groupes. Le sous-ensemble
14 + 25 fournit aussi la régression39 de111, sans somme supplémentaire. Les
preuves rouges,14isolée et162contextuelle restent exclues de ces81.

Construire uniquement le contrôle DEV, sources épinglées, puis sauvegarde native
SQLite au repos avant remplacement du seul serverless-api. Conserver empreintes
du registre, tables, backend/web, fichiers officiels, référence et 5 982 artefacts.
Aucune migration, variable, route ou restauration automatique de base. Le nouveau
CID/image du contrôle est attendu ; le runtime de référence et ses dates restent
identiques. Vérifier les 38 fichiers backend dont le seul delta produit attendu
est managed_instances.py ; les quatre ressources web et le manuel restent ceux
précédemment servis. Les captures communes fraîches sont ouvertes individuellement.
Relever les ressources physiques de tous les essais et les consommateurs réellement
terminés. Une preuve manquante garde112[~] et078 garde son passage entier distinct.
