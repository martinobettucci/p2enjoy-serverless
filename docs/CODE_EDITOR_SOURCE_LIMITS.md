# Sources et limites réelles de l’éditeur

Complément de [SLS-070](BACKLOG.md#sls-070), décidé le12novembre2026 avant
son client de preuve. Le contrat produit reste [CONSOLE_EDITOR](CONSOLE_EDITOR.md).
Les preuves antérieures de quotas, sauvegarde et lien Tester conservent leurs
époques ; leurs groupes ne sont pas ajoutés à ceux de ce complément.

## Périmètre et progression

La qualification restante de070 suit ces ensembles cohérents :

1. Sources et bornes HTTP : source archivée conservée, fichier supérieur à1Mio
   conservé lors d’une publication, chemins512octets/segments255octets,
   diff2000lignes/128Kio et enveloppeJSON8Mio. Ce document définit ce passage.
2. Compléments console : source archivée dans le dialog et versions au-delà de
   cinq, pagination du diff, adoption de la version serveur en gardant la saisie.
3. Bornes de reconstruction ZIP et concurrence réelle :64Mio compressés,
   256Mio extraits,20000entrées/répertoires, quatre lecteurs/une reconstruction,
   révocation pendant lecture et purge face à un lecteur vivant.
4. Persistance et publication : redémarrage réel du contrôle, perte de réponse,
   consultation du même UUID sans nouveau POST, préparation seule/abandon,
   receiving/validating interrompus et instantané publié distinct des éditions
   ultérieures du brouillon.

Ce découpage ordonne les preuves, sans réduire les critères de070. Aucun de
070.1–.5 ne ferme avec les seules bornes HTTP. La campagne complète reste requise.

## Campagne HTTPS de sources et bornes

Une campagne UUID utilise un namespace/service/fonction originaux sur le seul
SPARK DEV autorisé. Elle part de l’accueil puis du vrai SSO administrateur.
Les accès directs HTTPS qualifient les bornes serveur ; ils ne sont pas une
preuve de l’ergonomie des écrans, conservée dans le second ensemble.

Le paquet reprend la dépendance YAML2.9.1 réellement installée dans la référence
inchangée, avec un handler original du dépôt. Des fichiers de données originaux
définissent les frontières ; aucune source applicative, réponse, dépendance,
horloge ou base de données n’est substituée. Aucun code client n’est exécuté.

- Un texte UTF-8 de1048577octets est identifié `text_limit`, sans champ `text`.
  Remplacement/retrait sont refusés sans modifier le brouillon. Le handler
  Docker lit réellement sa taille et son SHA, avant et après reconstruction.
  Le lecteur natif vérifie aussi tous les octets et modes des artefacts.
- Un chemin Unicode de512octets possède des segments de255,254 et1octet.
  Le chemin513octets, dont tous les segments restent valides, est refusé.
  Un segment255octets passe et256octets échoue. Deux noms Unicode visuellement
  proches, composés et décomposés, restent distincts et gardent leurs octets.
- Le diff traite2000lignes par côté ;2001sur le côté avant ou après produit
  `line_limit`, sans diff trompeur. Deux lignes de65500caractères sous le chemin
  `diff-output.txt` donnent exactement131072octets de diff avec leurs en-têtes.
  Un octet supplémentaire exige `output_limit` et `truncated:true`. La
  troncature retire une pièce entière ; sa longueur n’est pas forcée à128Kio.
- Un objet JSON valide de petite taille est complété par des espaces JSON
  jusqu’à8388608octets. Il est accepté avec son vrai Content-Type JSON ; un
  octet supplémentaire est refusé413. Ce remplissage isole l’enveloppe de la
  borne1Mio du fichier et4Mio des patches. Le refus conserve version, dates,
  handler, ciphertext et audits de mutation, recoupés nativement.
- La sourceA est publiée puis une sourceB promue. A est archivée par sa vraie
  API, consultée explicitement et choisie comme nouvelle base après abandon
  du brouillon précédent. Une modification produit un nouveau candidatC,
  validé dans Docker et invoqué par hash ; B reste la cible des appels sans tag.
  Le gros fichier, le binaire, la dépendance et les modes sont conservés.

Les refus vérifient le codeHTTP et les états avant/après, sans succès conditionnel
ni rejeu. Les UUID d’intention sont enregistrés avant création ; le nettoyage
rapproche les réponses perdues sans adopter une ressource préexistante.
Les jetons propres à la campagne sont révoqués et les fonctions purgées par les
API normales. Le reçu reste incomplet jusqu’aux jonctions et nettoyages.

## Preuves et portée

Les sources indexées, l’image, les fichiers embarqués/servis, les configurations
officielles et les artefacts antérieurs sont recoupés avant/après. Les vrais
handlers ont leurs lignes natives. Les rapports UUID privés ne contiennent ni
code, jeton, cookie, secret ni ciphertext ; seuls tailles, empreintes et états
utiles sont exportables. Les échecs restent séparés des replays.

Après le passage ciblé : manuel, routes publiques et connexion sont rejoués
en série, avec inspection individuelle des captures. Le manuel et le schéma
restent inchangés tant qu’aucun comportement produit ne change. Une limite
infirmée impose une reproduction conservée et une décision avant correction.

## Revue du banc avant exécution

La revue relève deux faiblesses de preuve, corrigées avant son gel : un statut
5xx ne prouve pas l’absence de création, et chaque inventaire pris seul ne
prouve pas la conservation entre révisions. Le rapprochement d’une intention
dont le nom était absent consulte donc aussi les issues5xx ; seuls les refus4xx
certains évitent l’adoption. Le namespace UUID isole les noms de campagne.
Le lecteur retourne les métadonnées d’inventaire sans contenu ; la comparaison
exige exactement A + changements attendus pour B et C, avec chaque chemin,
taille, SHA et mode. Une omission ou une modification avec inventaire cohérent
reste ainsi détectée. Cette revue n’est pas une preuve E2E acquise.

## Premier passage interrompu dans le lecteur natif

Le passage2373aeb2 au gel3e7b1e0 passe l’entréeSSO, les prérequis, la création
du paquet et la première publication/invocation ; il échoue pendant le premier
contrôle natif de refus. Le programme distant utilise UUID sans l’importer :
un NameError réel est recoupé par une lecture de diagnostic. La
[preuve échouée](evidence/code-editor-source-limits-reader-failed-dev-2026-11-12.json)
conserve406sources identiques avant/après et zéro groupe qualifié. Le lecteur
corrigé confirme ensuite la fonction purgée, l’artefact absent, le jeton révoqué,
aucun brouillon ni activité ; les deux parents sont supprimés par API.
Aucun groupe de ce passage ne qualifie le complément.
Correction décidée avant code : importer UUID dans le programme distant du
lecteur, vérifier les ressources résiduelles, terminer les parents par API,
puis geler à nouveau les sources et exécuter l’ensemble sans addition de groupes.

## Résultat qualifié et suites

Le [replay DEV](evidence/code-editor-source-limits-dev-2026-11-12.json) bb741a51
au commit53a6a9b passe38groupes :13ciblés puis8manuel/8public/9connexion.
Les406sources59dd4591 et l’image60938093 sont identiques avant/après chaque
campagne ;38backend/quatre ressources HTTPS, même CID/démarrage, référence,
fichiers officiels et5982artefacts initiaux sont recoupés.

Les frontières sont observées aux valeurs annoncées :1048577octets non éditables
et conservés, chemins512/513/segments255/256, Unicode distinct, diff2000/2001
de chaque côté,131072octets exacts de diff puis `output_limit` avec65570octets
conservés, JSON8388608/+1. Les refus et no-op conservent les métadonnées,
ciphertexts et audits de mutation. Cinq invocations réussies sont liées à leurs
vraies révisions. L’inventaireA possède246fichiers, B250 (quatre ajouts et marqueur),
C246 (marqueur seul depuis Aarchivée) ; aucun autre chemin, octet ou mode ne change.
B reste promue pendant publicationC ; Aarchivée refuse l’invocation tout en
restant une source de brouillon consultable.

Les22captures communes sont ouvertes individuellement par le vérificateur RO,
Git propre avant/après. Les16JPEG ont leurs SHA déclarés ; les6PNG sont liés
à leurs octets courants et mtime de phase, sans SHA déclaré dans login.
Ces images ne qualifient pas les compléments de console du second ensemble.
Le manuel servi correspond à18chapitres/74paragraphes et son SHA source inchangé.

La fonction et le jeton nominaux sont nettoyés, comme ceux du passage échoué :
deux fonctions purgées, deux jetons révoqués et deux couples de parents supprimés.
Aucun brouillon, activité, bail, réservation ou garde ; intégritéok/FKvide,
dix migrations et propriétaire1001 recoupés. Le probe writer ne fait aucunDML
et ferme sa connexion ; la disparition normale WAL/SHM après fermeture est
distinguée de la vérification de leur propriétaire pendant ouverture.

Les trois notes SPARK et propositions sont conservées : image, installation,
interfaces et configuration inchangées, aucune adoption revendiquée. Aucun
build produit, migration, variable, secret ou route n’est nécessaire. Les
ensembles2–4 et la campagne complète restent à produire ;070.1–.5 restent ouverts.
