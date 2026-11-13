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

## Réalisation du passage de frontières

Décision du13novembre avant ses sources : cinq fonctions de campagne, quatre
frontières et une petite fonction distincte pour confirmer la capacité après413.
Sept groupes ciblés sont prévus : accueil/SSO, préparation des vrais paquets,
compression, volume extrait, nombre de fichiers, parents, recoupements natifs.
Six handlers sont exigés : ZIP exact puis retour admissible, contrôle après413,
et un par frontière restante. Les25communs suivent en série.

Le générateur `code-editor-archive-fixtures.py` et le handler original
`editor-archive-limits.cjs` sont montés readonly dans un conteneur temporaire de
l’image exacte du contrôle. Aucun module produit n’est importé. Le conteneur
est sans réseau, readonly, sans capacité, à1CPU/512Mio/64PID ; timeout interne
600s puis kill5s, --rm. Il écrit seulement sa sortie privée de campagne, sous
UID hôte1001. Le pilote `code-editor-archive-fixtures-run.py` vérifie le SPARK,
le UUID, l’image et les identités de dossiers ; il conserve un reçu root privé
avant lancement. Le nettoyage ne vise que cette sortie et ce conteneur nommés,
avec identités et propriété contrôlées. Aucun service applicatif n’est lancé.

La sortie contient ZIP d’entrée, ZIP prédit et manifestes normalisés A/B, plus
marqueurs privés. Seuls comptes, tailles, empreintes, versions Python/zlib et
SHA de zipfile sont exportés. Les octets sont transférés vers le client local
par SSH et vérifiés avant upload. Le nettoyage du dossier et l’absence du
conteneur sont recoupés à la fin. Un UUID déjà préparé est refusé sans génération.

La prédiction reproduit le chemin ZipInfo explicite de l’éditeur, sortie
seekable, noms triés, date1980, mode0444, DEFLATE et file_size. Elle n’utilise
ni _for_archive ni open(nom) : le ZipInfo fourni garde son niveau de compression
None, comme le produit. Les marqueurs modifiés sont écrits en un seul appel,
les autres fichiers par blocs65536. La calibration incompressible est bornée
à16ajustements ; l’archive fermée doit faire exactement64Mio et l’entrée STORE
rester dessous. La paire de marqueurs doit réellement ajouter un octet comprimé.

Le refus64Mio+1 est comparé au brouillon débordant déjà enregistré. Les autres
+1 sont refusés au PUT et comparés à l’état antérieur. L’inspection contrôle
intégralement les fichiers/modes/SHA et parents contre les manifestes A/B,
puis exporte leurs SHA canoniques et comptes ; elle recoupe aussi l’archive
conservée et revisions.archive_sha256. Les invocations Docker retournent les
comptes réels et les SHA des données/du marqueur, sans code ni secret.

## Clôture et portée

Sources/images,38backend, quatre ressources HTTPS, manuel18/74, configuration,
référence et5982artefacts initiaux sont recoupés avant/après. Les inspecteurs
sont en lecture seule sous UID1001 pour SQLite ; aucun code, jeton, cookie,
secret ou ciphertext n’est exporté. Les fenêtres et compteurs restent bornés.
Les critères070.1/.3/.4/.5 restent ouverts tant que leurs autres preuves manquent.
La capacité est qualifiée ci-dessous ; les frontières du paquet restent à produire.

## Capacité globale qualifiée —13 novembre2026

La [capacité globale de publication éditeur](evidence/code-editor-build-capacity-dev-2026-11-13.json) passe **29 groupes réels** :
4 ciblés puis 25 communs, sur 423 sources `0856f1be` et l’image `b452ef16`.
Un POST reste retenu au vrai read ; les nouveaux POST sur A et B font429 en
118/130ms, Retry-After5, sans candidat ni mutation des brouillons. Après libération,
le même POST A termine dédupliqué puis une nouvelle publication B réussit.
Trois handlers et22captures communes sont recoupés ; deux fonctions, un jeton,
deux parents et un helper sont nettoyés.38backend/quatreweb, services, manuel
18/74, configuration, référence et5982artefacts initiaux sont conservés.
Les frontières ZIP64Mio/256Mio/20000fichiers/parents et la capacité après413
restent à éprouver ; aucun critère supplémentaire de070 n’est clôturé.

La fonction A est seule avant armement, B apparaît après le held natif. Un
worker reste tracé sur FD12/inode571353, fichier65octets ;131072octets sont la
taille demandée au read, pas celle du fichier. La santé répond en171ms. Les
refus exacts sont118,342ms et130,439ms, avec UUID absents par API et en SQLite.
Fonctions, brouillons, audits de mutation, révisions et candidats sont identiques
avant/après ces refus. Le premier appel est toujours en attente à ce point.

La libération rejoint helper, garde et même requête. Le reçu commence environ
4,36s après le read retenu, sous45s. Le premier UUID publie la révision d’origine
avec code_changed=false ; le nouvel UUID B publie sa propre révision puis est
invoqué par hash. Les trois handlers ont leurs lignes succeeded/handler_started1/
HTTP200 et leurs révisions. Les deux UUID refusés restent absents au final.

Le relevé final recoupe helper d’origine disparu, sept threads libres, compteurs
nuls, intégrité/FK et dix migrations. Les22originaux communs sont ouverts
individuellement, Git propre avant/après :16JPEG liés aux SHA déclarés et6PNG
aux octets/fraîcheur de phase. Ces images ne prouvent aucune concurrence.

Le passagebe791eed au gel7ff7221 est suivi des25communs sur le même gel.
Les bornes de taille ne sont pas déduites de ce petit paquet. Aucun autre
critère de070 ne ferme ; le second passage de frontières reste entièrement dû.
