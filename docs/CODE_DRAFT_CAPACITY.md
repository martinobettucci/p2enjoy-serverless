# Capacité réelle des brouillons

Complément de qualification de [SLS-070.3](BACKLOG.md#sls-070), conforme aux
bornes de [CONSOLE_EDITOR](CONSOLE_EDITOR.md). Décision du12novembre2026,
persistée avant le client de campagne. Le serveur déjà déployé est éprouvé ;
aucun changement de quota, de schéma ou de produit n'est décidé ici.

## Périmètre et observation

Le seul SPARK DEV infra-serverless est utilisé, par HTTPS et le vrai SSO.
La campagne crée un namespace `code-draft-capacity-<uuid>`, un service
`draft-capacity-limits`,33fonctions `draft-capacity-01` à`33` et cinq jetons
Create `draft-owner-01` à`05`. Toutes les mutations passent par les API normales.
Jetons en mémoire seulement, aucun secret ni texte de source dans les rapports.
Fonctions sans volume, zéro instance minimale, idle0. Les intentions sont
enregistrées avant les POST, après lecture paginée attestant l'absence du nom.
Le namespace porte l'UUID complet. Une réponse certaine autre que201 interdit
le rapprochement ; seules une création acquittée ou une réponse perdue peuvent
être rapprochées dans ce périmètre neuf. Aucun objet extérieur n'est supprimé.
Un vrai409 sur le nom d'une fonction de la campagne vérifie qu'une intention
refusée n'adopte aucun UUID et laisse l'objet initial accessible et inchangé.

L'opérateur natif lit SQLite sous l'identité de son propriétaire, dans une
transaction de lecture cohérente : compteurs globaux, métadonnées des seuls
brouillons de campagne, versions/dates/handler, octets UTF-8, longueurs et SHA
des ciphertexts. Aucun ciphertext ni déchiffrement ni DML n'est rendu/autorisé.
Les refus comparent ces lignes et audits de mutation de brouillon, pas toute la
base : `last_used_at` et diagnostics de refus peuvent légitimement évoluer.
Le prérequis exige zéro brouillon et au moins1Gio+512Mio libres :1Gio pour la
garde produit,512Mio pour les pages SQLite/WAL successives, afin de distinguer
la borne logique d'une pénurie physique. Un prérequis absent fait échouer le test.
La capacité logique compte les lignes, sans exiger que SQLite rende ses pages.

## Nombre de brouillons

1. Le propriétaire01 crée32brouillons sur les fonctions01–32. Le33e reçoit429 ;
   lecture vide, lignes et audits de mutation inchangés. Abandonner le32e permet
   de créer le33e ; recréer le32e échoue.
2. Trois autres propriétaires créent chacun32brouillons :128globaux. Le
   cinquième, sans brouillon, reçoit429. Un abandon permet sa création ; le
   propriétaire libérateur reste refusé à128globaux, malgré ses31brouillons.
3. Les abandons normaux conservent les cinq brouillons de la fonction01.
   Un brouillon vide occupe100octets chiffrés, à observer réellement dans SQLite.

## Frontière exacte de64Mio chiffrés

Quatre fichiers `utf8-payload-01.txt` à`utf8-payload-04.txt` (19caractères ASCII),
mode0444. Le JSON compact actuel du Vault échappe les Unicode :😀 occupe4octets
UTF-8 et12octets JSON. L'enveloppe des quatre entrées compte197octets.
Fernet conserve `4 × ceil((57 + 16 × (floor(n / 16) + 1)) / 3)` octets pour n
octets JSON. La formule prépare les vraies entrées ; la preuve utilise les
longueurs réellement stockées dans SQLite.

| Propriétaires | Fichiers01–03 | Fichier04 | Texte UTF-8 total | JSON | Ciphertext |
| --- | --- | --- | ---: | ---: | ---: |
| 01–03 chacun | 262144😀 chacun | 262134😀 et10`x` | 4194274 | 12582999 | 16777420 |
| 04 | 262144😀 chacun | 262078😀 | 4194040 | 12582317 | 16776504 |
| 05 | brouillon vide | — | 0 | 2 | 100 |

`3×16777420+16776504+100=67108864`, exactement64Mio. Fichiers sous1Mio,
brouillons sous4Mio UTF-8, requêtes sous8Mio, écritures séquentielles.

À cette frontière, trois`x` de plus sur le dernier fichier du propriétaire04
exigent20octets chiffrés supplémentaires. Le PUT change aussi le handler :507,
ligne/version/date/handler/texte/audit inchangés. Une création vide sur une autre
fonction reçoit507 ; un PUT inchangé reste200/changed:false, sans nouvelle
version/date. Les GET de fichier recoupent longueur et SHA après ces refus.

Abandonner le brouillon vide libère100octets : sa recréation réussit et revient
exactement au plafond. Après un second abandon, ajouter les trois`x` réussit ;
les80octets libres ne permettent plus une création vide (507). Rétablir le texte
antérieur libère20octets et permet à nouveau cette création.

## Publication, conservation et nettoyage

Après libération d'un gros brouillon, le propriétaire01 prépare sur la fonction33
un module CommonJS original `draft-capacity.cjs`, publié depuis son brouillon
initial, sans ZIP envoyé par le client. Un vrai jeton Read invoque son hash ;
réponse, hash, invocation et handler_started sont recoupés nativement. Pas de
promotion implicite. Le brouillon Create devient inaccessible après publication.

L'archive de01 conserve ses quatre brouillons et leur poids ; sa purge normale
les retire. La purge de33 retire le code, les artefacts et le brouillon initial.
Les31autres fonctions, service et namespace sont nettoyés par API. Les compteurs
finaux, intégrité/FK, absence d'instances, baux, candidats actifs et répertoires
d'artefacts de campagne sont vérifiés. Les5982artefacts antérieurs, images/CID du
contrôle et de la référence, configurations et sources indexées restent identiques.
Le collecteur externe complète explicitement l'inspecteur ciblé : inventaire/SHA
des5982fichiers, sources embarquées et HTTPS, empreintes des trois fichiers de
configuration, CID/image/date/état des deux conteneurs, registre de stockage
(baux et commandes en attente), santé et ownership SQLite. Ces observations ne
sont pas déduites des seuls compteurs `busy` du client.

Cette tranche ne clôt pas seule070.3 ni070 : limites, reprises, compléments UI
et dépendance071 restent suivis dans le contrat principal.
