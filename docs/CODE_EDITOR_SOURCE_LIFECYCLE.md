# Révocation et purge pendant une lecture de code

Complément de [SLS-070](BACKLOG.md#sls-070), décidé le 13 novembre 2026 avant
son client E2E. Il reprend la barrière de lecture réellement qualifiée par les
[34 groupes](evidence/code-editor-read-concurrency-dev-2026-11-12.json), sans
changer son protocole ni ses gardes. Les contrats produit sont
[CONSOLE_EDITOR](CONSOLE_EDITOR.md#parcours-et-droits) et sa
[conservation des fichiers](CONSOLE_EDITOR.md#persistance-concurrence-et-conservation).

## Portée et ressources

Une seule campagne UUID sur le SPARK DEV utilise un namespace et un service
propres, une fonction `editor-reader-lifecycle-<nonce>`, le paquet original
`code-editor-read-package.py` et son handler Docker. Le namespace et le service
portent le même UUID dans leur description, suivant les préconditions de
l’observateur livré. Les ressources sont créées par les véritables API et
rapprochées de leurs intentions avant nettoyage en cas de réponse perdue.

La connexion passe par l’accueil et le vrai SSO administrateur. Les requêtes
HTTPS directes qualifient les droits et les états serveur ; aucun nouveau
parcours visuel n’est revendiqué par ces assertions. Le client crée un jeton
Read pour les invocations et deux jetons Update successifs limités à la fonction.
Leur valeur demeure en mémoire ; seuls leurs UUID et métadonnées sont exportés.

Aucun code produit, manuel, schéma, variable, secret, route ou conteneur n’est
modifié par ce complément. Les sources et l’image sont gelées avant/après chaque
phase ; les artefacts initiaux et la configuration officielle sont conservés.

## Révocation entre autorisation et réponse

1. Publier et promouvoir le paquet original, appeler son handler Docker et lire
   la source exacte avec le jeton Update A. Le jeton Read seul est refusé sur
   arborescence, fichier, résumé de brouillon et diff : 403, aucun code retourné.
2. A crée son brouillon personnel depuis le hash publié. Une lecture de son
   fichier source est engagée et maintenue à l’entrée du vrai `read` de son
   worker, sur le FD/inode de cette révision. La boucle HTTP reste disponible.
3. L’administrateur révoque A pendant ce maintien. La révocation et son horodatage
   sont relus nativement. De nouvelles requêtes de A sont refusées en 401 ; la
   première requête reste en attente sur son FD, sans réponse substituée.
4. Libérer le worker puis joindre la requête initiale : elle doit elle aussi
   recevoir 401, sans objet fichier, texte ou code. Une autorisation acquise
   avant l’IO ne doit pas survivre à la révocation commise pendant cet IO.
5. Créer Update B par l’API. Sa lecture de source réussit, son résumé de brouillon
   est vide et il crée un nouveau brouillon. Les deux UUID de brouillon et leurs
   propriétaires A/B sont recoupés : aucun transfert de propriété. Le handler
   reste invoquable par le jeton Read indépendant, avec la même réponse exacte.

Les refus conservent leur véritable objet d’erreur ; aucune réponse de source
n’est fabriquée ni réinterprétée comme un succès. Les noms d’en-têtes et valeurs
d’authentification ne sont pas exportés dans le rapport.

Le gestionnaire HTTP commun sérialise ces refus dans `{error: texte}`. Le client
exige un texte non vide et cette seule clé, en plus du statut attendu. Il ne
suppose pas la forme `detail` par défaut de FastAPI.

## Purge confirmée face à un lecteur vivant

1. Engager avec B une nouvelle lecture et retenir son worker sur le même fichier.
   Constater fichier régulier, inode et FD exacts, thread réellement tracé ;
   conserver cette identité pour la comparaison après purge.
2. L’administrateur supprime la fonction, attend l’archivage puis confirme la
   purge normale. Le POST de purge doit répondre 202. Attendre l’état durable
   `pending`, phase `artifacts`, de cette commande précise ; ce n’est pas une
   simple attente chronométrée.
3. À ce point, la décision de purge a retiré les deux brouillons et les
   inventaires ; les révisions sont marquées supprimées, mais leurs octets
   restent comptés et le fichier/FD du lecteur garde le même inode. La fonction
   n’est pas encore marquée purgée. Le contrôle continue de répondre.
4. Les nouvelles lectures administratrices sont refusées en 404. B reçoit 403
   pour les nouvelles lectures : la recherche préalable d’une fonction vivante
   ne fournit plus de service autorisé à son jeton. Ces statuts correspondent
   au flux actuel de `authorization` et ne divulguent aucun code.
5. Libérer le worker et joindre la requête initiale : son second contrôle de
   fonction vivante doit répondre 404 sans code. Attendre la même commande de
   purge `completed`, puis constater `purged_at`, zéro octet conservé et absence
   physique du répertoire et du fichier. Le FD peut être fermé ou réutilisé ;
   il ne doit plus désigner cet inode. Aucun nouveau POST de purge n’est rejoué.

L’inspecteur natif est en lecture seule, sous l’identité SQLite1001, borné au
namespace et à l’unité de garde de campagne. Il exporte les états SQL, tailles,
SHA, propriétaire des brouillons et métadonnées du fichier/FD, jamais le code,
un ciphertext ou un secret. Il vérifie le PID/naissance/cgroup et la génération
du contrôle. Il n’envoie aucun signal et ne modifie aucun registre ou fichier.

## Matrice et clôture de preuve

Cinq groupes ciblés sont prévus : accueil/SSO, préparation et droits initiaux,
révocation/replacement, purge vivante, recoupements natifs. Deux invocations
Docker distinctes doivent être jointes à leurs lignes `succeeded`,
`handler_started=1`, HTTP200 et au hash attendu. Deux unités de garde doivent
être réellement terminées, ainsi que les requêtes et leurs transports SSH.

Le finally joint chaque garde avant les purges de secours, révoque tous les
jetons de campagne, vérifie les ressources physiques puis supprime les parents.
Le rapport reste incomplet jusqu’à ces jonctions. Une erreur est conservée avec
sa restitution avant toute correction et un nouveau gel ; les passages ne
s’additionnent pas. Aucun mock, stub, interception, seed SQL ou skip.

Après les cinq groupes : rejouer en série manuel, routes publiques et connexion,
puis inspecter leurs originaux. Le manuel doit correspondre à sa source inchangée.
Recouper les sources, l’image, les fichiers embarqués/servis, la référence, les
configurations officielles et les 5 982 artefacts initiaux. Les compteurs globaux
et les gardes doivent être à zéro, intégrité/FK et dix migrations conformes.

Ce complément ne clôture pas seul 070.1–.5 : reconstruction unique et limites ZIP,
lectures UI maintenues et reprises de publication restent exigées. La preuve
antérieure des lecteurs conserve sa propre époque et ses 34 groupes.

## Réalisation et premier passage

Le client et l’inspecteur natif sont implémentés, leurs syntaxes Python/Node
contrôlées, y compris le programme distant embarqué. La revue statique ne relève
aucun bloqueur. Le [premier passage](evidence/code-editor-source-lifecycle-error-field-failed-dev-2026-11-13.json)
échoue avant sa première invocation : le refus403 passe mais le client cherche
`detail` au lieu du champ `error` du gestionnaire commun. Un groupe SSO passé,
zéro groupe qualifié ; fonction purgée, deux jetons révoqués, deux parents
supprimés et conservation native recoupée. Aucune garde n’a été créée.

Décision du13 novembre avant correction : vérifier la forme publique `error`
et sa seule clé, sans changer les statuts ni réduire les exigences de refus.
Les durées cumulées sous la garde45s et les états attendus restent à établir
par le replay réel ; aucun résultat E2E nouveau n’est revendiqué.
