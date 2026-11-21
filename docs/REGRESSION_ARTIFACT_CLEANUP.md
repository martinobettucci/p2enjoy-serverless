# Conservation des artefacts pendant la campagne complète

Contrat de [SLS-106](BACKLOG.md#sls-106), préalable opérationnel à105 et078.
La [qualification finale](evidence/regression-artifact-cleanup-dev-2026-11-21.json) passe79groupes
au gel72059cb,450sourcesaaf0784a et51captures inspectées.
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

## Diagnostic recoupé et décision avant code

Le relevé RO1795267783292962291 compare les5982chemins/SHA du journal104
0a3798d2 avec le courant : aucun manque, aucune modification, exactement deux
ajouts. Ils appartiennent à la révision d9d07c5b-ecbe-449e-beb2-c84c5f0d4f29,
fonction4ba58f4d-d0c3-4953-a3a8-406de1b6f5c6, namespaceb8e06c8a-c6af-4217-9e7d-7227e420f559
invocation-144a134f. Fonction/parents supprimés, purged_atNULL et16384octets
encore comptés. first_promoted_atNULL recoupe séparément l’hypothèse105.

La chaîne execution-ui→storage-archives→function-storage-faults archive-cleanup
purge seulement l’agent de volumes. Les quatre clients control-admin, control-ui,
execution-ui et publication-ui utilisent ce helper partagé. Corriger ce helper,
plutôt que dupliquer une purge dans un seul client. Son interface à deux UUID
reste stable ; ajouter les traces106 aux consommateurs sans modifier leurs
scénarios. Le protocole opérateur ancien reste distinct, pour ses preuves propres.

Après relecture SSO réelle, la remise en état de l’essai existant vise uniquement
le UUID fonction ci-dessus, par GET archive/If-Match/nom exact puis un POST purge
UUID neuf et son suivi GET. Le contrat public065 accepte un agent déjà purgé
par le protocole opérateur. Conserver cette trace et l’inventaire5982 rétabli ;
aucun unlink ou SQL de réparation. Cette action opérationnelle précède le replay.

Le helper corrigé utilise la session de purge distincte du vrai SSO, requête
CSRF/Origin, vérification UUID/namespace de l’archive, attente d’absence de garde,
un seul POST et suivi du même UUID. Après résultat incertain il ne fabrique pas
un nouvel UUID. Une purge déjà terminée se vérifie par son reçu existant ; une
opération de purge déjà en cours est rejointe, pas redemandée.

Un lecteur DEV RO par fonction vérifie appartenance au namespace exact et au
préfixe des quatre clients, fonction supprimée/purgée, reçu public completed,
configuration/variables/secrets propres effacés, révisions et candidats vidés,
aucune instance/garde active, état/receipt agent corrélés et aucun fichier de
code/volume/montage/canal/conteneur/réseau de cette fonction. Les parents peuvent
encore être actifs à cet instant ; le lecteur ne demande pas un inventaire
complet de namespace ni ne modifie les bornes du collecteur existant.

Qualification106 indépendante de105 : un client dédié crée/publie/promeut une
fonction originale avec le handler scheduled-storage, écrit réellement données
et cache par invocation Docker, archive puis exerce le helper et son inspection
native. Trois groupes ciblés, puis les19control-admin,11control-ui et21publication-ui,
enfin25communs ; conserver à part la remise en état de l’ancien UUID. La préparation
six instances reste à qualifier dans105 après106 : ne pas l’exiger pour clore
106 ni modifier sa préparation dans ce changement. Les lecteurs/sourceimages,
captures et5982artefacts sont recoupés à chaque phase ; un échec reste conservé.

## Sens des volumes archivés et preuve de conservation

L’essai b74f486b au gel01fa6e1 exécute réellement le handler et écrit les deux
records, puis échoue dans son deuxième groupe sur enabled=true. Son finally
purge complètement par le nouveau helper ; le lecteur natif réussit et les5982
originaux sont conservés. Ce premier essai reste incomplet, zéro groupe qualifié.

La source agent_volumes.archive met explicitement enabled=0 après arrêt des
volumes, sans retirer quota ou backing. L’assertion du nouveau client confondait
activation et conservation. Avant code du replay, décider : conserver d’abord
le GET archive dans le rapport, exiger désactivation/unmounted/quotas2Mio et
ajouter un mode RO --retained au lecteur dédié. Il vérifie namespace/fonction
archivés, absence de garde/instance/bail, ZIP au SHA déclaré, fichier de code au
SHA de la fixture et les deux vrais backings record par taille/SHA. Le client
compare ces SHA aux valeurs effectivement écrites par le handler. Aucun contenu
ni configuration/secrets n’est exporté. Le mode purgé garde ses contrôles stricts.
Cette observation remplace l’assertion incorrecte, sans réduire la preuve de
conservation ni changer le produit. Les trois groupes entiers et les régressions
prévues sont à rejouer après ce correctif du banc.

## Qualification finale du21novembre2026

La [preuve79](evidence/regression-artifact-cleanup-dev-2026-11-21.json) recoupe au gel
72059cb527379a01ada12c92745bb4e192ada8cf les3groupes dédiés,19control-admin,
11control-ui,21publication-ui puis8manuel/8public/9connexion, en série.
450sources, indexaaf0784a458185facf2de009f8821f7526c8bba2df6e350e196a32d44b513a2d,
imageb452 inchangée. Aucun mock ni groupe ignoré ; les sessions SSO restent des
prérequis. Les sources exécutables ne changent pas après qualification ; les
présentes métadonnées de résultat forment une époque documentaire séparée.

Le handler original écrit vraiment les deux records. Le lecteur RO en relève
les tailles/SHA dans les backings, puis la purge publique et le second passage
du helper partagent le même UUID de commande, avec deux reçus d’observation
distincts. Au total, neuf fonctions sont purgées dans les quatre phases ciblées,
dix observations du helper et une seule commande par fonction. Configuration,
secrets, code, backings, montages, canaux, conteneurs et réseaux sont absents
pour chacune, avec corrélation du reçu agent et de l’installation.

Les51captures sont rouvertes individuellement pour cette campagne :7gestionUI,
22publication,16manuel,6connexion. SHA/fraîcheur source dans chaque phase ;
les13captures non déclarées par les anciens rapports restent explicitement
distinguées de leurs38captures déclarées. Aucun masquage ou débordement
bloquant observé. Les captures ne prouvent pas les faits natifs de purge.
Le manuel18chapitres/74paragraphes concorde avec source/rendu ; les longs
hashes/noms, journaux, confirmations et erreurs sont lisibles aux formats testés.

Les5982artefacts antérieurs restent identiques, tous les compteurs actifs sont
nuls, dix migrations et intégrités/FK sont recoupées. Mêmes CID/images de
contrôle/référence et fichiers officiels ; le redémarrage du contrôle est prévu
par control-admin, sa naissance passe de14:04:44 à14:46:26UTC, sans recréation
ni changement d’image. La référence garde sa naissance du6novembre. Les38
backends,4web servis et trois notes conservées sont recoupés ; aucune adoption
de note prétendue. Aucun produit/UI/manuel modifié.

La restauration antérieure de la seule révision d9d07c5b est conservée à part :
5984→5982, aucun original manquant/modifié, purge API corrélée à la fonction
4ba58f4d et0groupe ajouté. Les essais b74f486b et05d9f312 restent archivés et
exclus du total79. SLS-106 est terminée ; six instances et37groupes105, puis
543groupes078 et clôture095 restent distincts.
