# Reconstruction ZIP : capacité globale et bornes réelles

Complément de [SLS-070](BACKLOG.md#sls-070), décidé le 13 novembre 2026 avant
ses clients E2E. Le contrat produit est [CONSOLE_EDITOR](CONSOLE_EDITOR.md),
sections Source/limites et Publication. Les preuves de lecteurs, de droits et
de sources conservent leurs époques ; aucun de leurs groupes n’est réadditionné.

## Deux passages complémentaires

1. Capacité de publication : retenir le véritable read pendant la reconstruction
   d’une fonction, refuser deux nouveaux UUID — même fonction et autre fonction —,
   puis joindre la première publication et réussir une tentative explicite sur
   l’autre fonction. Ce passage réutilise la barrière déjà qualifiée sans la
   modifier. Il ne prétend pas qualifier les bornes de taille.
2. Frontières du paquet reconstruit :64Mio compressés,256Mio extraits,20000fichiers
   et20000parents implicites. Chaque cas exact est publié par le POST éditeur,
   validé dans Docker puis invoqué ; son dépassement et la capacité restituée
   sont contrôlés. Les tests CLI de l’extracteur ne remplacent pas ce passage.

Ces passages sont sériels, sur le seul SPARK DEV. Le code produit, le manuel,
le schéma, les services et la configuration ne changent pas pour ce banc.
Chaque passage possède un rapport UUID complet et ses nettoyages. Les échecs
sont conservés avant correction ; aucun mock, interception, seed SQL ou skip.

## Capacité entre fonctions

La campagne part de l’accueil et du vrai SSO administrateur. Un namespace
`code-editor-read-concurrency-<nonce>`, son service de capacité de publication
et une seule fonction `editor-reader-lifecycle-<nonce>` respectent les
préconditions initiales de `code-editor-read-operator.py`. Le paquet original,
son handler et reader-gate.txt sont ceux déjà qualifiés. Un jeton Read propre
au service permet les vraies invocations ; ses valeurs restent en mémoire.

Après publication/promotion et création du brouillon A, armer la garde native
avant le POST éditeur. Le seul appel engagé sur reader-gate.txt est ce POST.
Le worker doit être retenu à l’entrée de read sur le FD/inode exact ; la réponse
reste absente et la boucle HTTP répond. Aucun buffer ni résultat n’est modifié.

Une fois le read retenu, créer B et son brouillon initial par les API ordinaires,
avec les deux fichiers originaux enregistrés. La précondition «une fonction
vivante» est ainsi satisfaite à l’armement ; le helper et son secours ne sont
pas élargis. Aucune publication de B ne démarre avant son refus attendu.

Deux POST avec des UUID distincts, l’un sur A et l’autre sur B, doivent répondre
429 avec le message de publication occupée et Retry-After5. Leurs candidats
restent absents ; ni le dernier UUID candidat des brouillons ni leurs versions
ne changent. Le service reste sain et le premier POST reste en attente.

Libérer la barrière, joindre le helper et la même requête, puis constater la
publication de A, sa déduplication et son invocation. Un nouvel UUID explicite
pour B doit ensuite publier et son hash être invoqué. Trois handlers nominaux
sont joints à leurs lignes natives. La garde doit être inactive et le helper
absent avant les purges/révocation/suppression des parents et fermeture clients.
Quatre groupes ciblés sont prévus : entrée, préparation, capacité globale et
recoupements natifs. Manuel/public/connexion ajoutent25groupes, inspectés à part.

## Frontières du paquet

Un générateur de données originales utilisera le même Python/zipfile et zlib
que l’image de contrôle pour prédire la taille, sans importer CodeEditor ni
simuler l’API. La prédiction ne fait pas preuve : un lecteur natif recoupera
l’archive.zip réellement conservée, son SHA avec revisions.archive_sha256,
les inventaires complets normalisés et les résultats des handlers Docker.

Le cas64Mio part d’un binaire incompressible en ZIP STORE, sous la borne d’entrée.
Le brouillon modifie un petit marqueur pour produire un nouveau hash conservé,
sans déduplication vers l’ancien ZIP. Le ZIP DEFLATE reconstruit doit atteindre
exactement67108864octets. Un marqueur dont la compression ajoute un octet doit
faire refuser la publication413 sans candidat ni mutation du brouillon ; après
retour à la valeur admissible, publier et invoquer pour confirmer la restitution.

Pour256Mio, quatre binaires compressibles d’au plus64Mio gardent le ZIP sous64Mio.
Handler et marqueur sont inclus dans les268435456octets exacts ; leur changement
à taille égale produit une vraie nouvelle révision. Ajouter un octet au marqueur
est refusé413 à la sauvegarde, avant mutation : un état impossible à enregistrer
n’est pas injecté pour forcer une publication invalide.

Les cas20000fichiers et20000parents sont indépendants : le handler et le marqueur
comptent parmi les fichiers. Des chemins à deux niveaux créent20000parents avec
moins de20000fichiers. Un fichier racine supplémentaire isole la première borne ;
un nouveau parent isole la seconde, sans atteindre d’abord la borne des fichiers.
Les dossiers ZIP explicites vides ne servent pas de discriminant : l’éditeur
reconstruit les parents depuis son inventaire effectif.

## Clôture et portée

Sources/images,38backend, quatre ressources HTTPS, manuel18/74, configuration,
référence et5982artefacts initiaux sont recoupés avant/après. Les inspecteurs
sont en lecture seule sous UID1001 pour SQLite ; aucun code, jeton, cookie,
secret ou ciphertext n’est exporté. Les fenêtres et compteurs restent bornés.
Les critères070.1/.3/.4/.5 restent ouverts tant que leurs autres preuves manquent.
Aucun résultat de ce complément n’est encore qualifié.
