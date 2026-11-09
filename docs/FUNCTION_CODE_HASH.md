# Identité canonique du paquet de fonction

Première étape de [SLS-074](BACKLOG.md#sls-074), en cours d’implémentation.
`function_code_hash.py` porte l’algorithme commun, bibliothèque standard seule.
L’extracteur et le packager restent les autorités de leurs fichiers réellement
lus. Aucun hash fourni par un client ne constitue une preuve serveur.

## Format v1

La préimage est UTF-8 strict, sans BOM ni newline, de l’objet JSON
`{"format":"p2enjoy.function-code/1","files":[...],"execution":{...}}`.
Clés triées, séparateurs virgule/deux-points sans espaces, Unicode littéral
(`ensure_ascii=False`), entiers et booléens JSON, aucun NaN/Infinity.
Le tag est SHA256 de ces octets, hexadécimal minuscule complet.

Files contient exactement path/size/sha256/executable par fichier, trié selon
les octets UTF-8 du chemin. Size et sha256 viennent des octets réellement lus ;
executable est le bit conservé par les modes normalisés readonly 0444/0555 du
packager et de l’extracteur. Aucun doublon de chemin, nom dangereux, SHA mal
formé, inventaire vide ou taille hors des bornes de l’extracteur. Ne pas
normaliser Unicode : deux vrais noms différents restent différents. Les
répertoires vides, dates et autres métadonnées du ZIP ne participent pas.

Execution contient exactement handler/runtime/architecture/image_id/events.
Runtime node24, architecture linux-x64, image immuable sha256 suivi de 64 hex.
Http regroupe les méthodes d’un même endpoint, les trie et déduplique ; les
endpoints sont triés. L’entrée implicite contient implicit=true et methods,
sans path dérivé du nom. L’entrée explicite garde implicit=false/path/methods.
Schedules garde cron aux espaces normalisés, enabled et timezone UTC ; trier
et dédupliquer les mêmes entrées. Cette normalisation ne change pas le chemin
métier actuellement transmis au handler. Les configurations, secrets, quotas,
noms et UUID ne font pas partie du descripteur.

Le packager hors connexion ne connaît pas l’image du serveur et ne promet donc
pas encore un tag complet. L’intégration ultérieure comparera son calcul depuis
l’inventaire local et le descripteur validé retourné par le contrôle. Le serveur
recalculera depuis son extraction et son image réellement validée.

## Calcul opérateur et preuve réelle

La CLI reçoit --archive, --destination neuve et --execution (fichier JSON public
borné à 64 Kio). Elle utilise l’extracteur maintenu, sans accepter d’inventaire
ou hash client. Le résultat porte code_hash, canonical et le résultat d’extraction.
Refuser les clés JSON dupliquées, descripteurs incomplets/supplémentaires ou
invalides. Erreur : sortie non nulle, diagnostic fixe sans contenu sensible.
Le répertoire extrait appartient à l’appelant, qui le conserve ou le nettoie.

La campagne `e2e/function-code-hash.py` tourne dans le seul SPARK DEV, en série.
Elle utilise les vrais processus packager/calculateur, l’extraction et le runtime
Docker. Cas : ZIP original/recompressé/réordonné, renommage implicite, vrais
changements de source/dépendance/exécutable/handler/événement/image, exclusion
des valeurs applicatives du paquet, noms Unicode et erreurs réelles de ZIP ou
descripteur. Invoquer le code extrait et observer ses résultats ; comparer les
hashs du packager et de l’extracteur par le même algorithme. Vérifier absence de
ressources après nettoyage et l’image de contrôle inchangée. Ce checkpoint seul
ne qualifie pas déduplication, promotion, migration ou invocation publique épinglée.

## Construction isolée

Le calculateur n’admet dans son contexte que function_code_hash.py et
control/app/artifacts.py, vérifiés par un vrai COPY complet du contexte.
Le build de l’adaptateur est également borné aux cinq modules Python, requirements,
deux clients E2E et trois fichiers de qualification explicitement nécessaires.
Les ancêtres réinclus sont réexclus avant leurs feuilles ; aucune réinclusion
récursive ou dossier de sauvegarde privé n’appartient au contexte. Ce resserrement
répond au build réellement refusé sur une sauvegarde root privée, qui reste intacte.
Les preuves de contexte/build sont des prérequis, distincts des groupes fonctionnels.
Le rapport natif et ses fichiers temporaires vivent sous control, répertoire
de travail du compte opérateur ; ne pas supposer la racine du dépôt inscriptible.
