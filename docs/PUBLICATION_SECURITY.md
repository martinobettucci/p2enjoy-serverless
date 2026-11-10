# Audit de confidentialité avant publication publique

Audit du 10 novembre 2026, demandé pour évaluer une publication GitHub publique.
Résultat : aucun secret exploitable détecté dans le périmètre vérifié. La
publication publique elle-même reste une décision du responsable.

## Périmètre et résultat

L'audit porte sur HEAD `803870d`, les modifications de travail et le nouveau
pilote E2E alors non suivi : 475 fichiers, ainsi que les 1 969 blobs de tout
l'historique accessible par les références Git locales, environ 107 Mo.
Aucun fichier d'archive ou de base binaire n'est nommé dans cet historique.

Recherche de clés privées, jetons de fournisseurs, jetons p2s, JWT, identifiants
dans les URL, affectations de secrets et chaînes opaques ; comparaison exacte
avec les deux valeurs confidentielles précédemment fournies pour le DEV, reçues
sur stdin privée. Aucune de ces deux valeurs n'est trouvée. Aucun jeton réel
ou clé privée n'est détecté.

Les 79 candidats distincts ont été classés : 54 empreintes d'intégrité des
package-lock, 21 préfixes immédiatement complétés par randomUUID dans les tests,
une URL factice destinée à être refusée, une fixture du garde Git et deux
libellés de formulaire. Les affectations supplémentaires correspondent au code
ou à un exemple vide. Leurs valeurs ne sont pas reproduites dans ce document.

Les empreintes des candidats sont aussi comparées, dans le seul SPARK DEV,
aux quatre variables confidentielles actives OIDC_CLIENT_SECRET,
QUALIFICATION_BUSINESS_TOKEN, QUALIFICATION_SYNTHETIC_SECRET et
SERVERLESS_MASTER_KEY. Aucune correspondance ; les valeurs actives restent
sur le SPARK. Cette comparaison porte sur les candidats détectés et ne constitue
pas une preuve universelle d'absence de toute forme d'encodage ou d'obfuscation.

## Fichiers locaux et informations d'exploitation

.local est exclu par .gitignore. Il contient des sessions de navigateur et des
artefacts privés de qualification ; il doit rester hors du dépôt public et des
archives de diffusion. Aucun fichier de session, .env réel ou clé privée suivi
n'a été trouvé.

L'audit initial identifiait docs/dev-spark.md comme suivi. Il contient adresses, comptes, rebond SSH,
empreinte de clé publique et détails de cellule. Ces données exposent la
configuration DEV ; le responsable a autorisé leur retrait avec le fichier.
La procédure et ses contrôles sont dans GIT_HISTORY_REWRITE.md. Les coordonnées DEV apparaissent aussi
dans les scripts, notes et preuves : retirer ce seul fichier ne les retire pas
de l'ensemble du dépôt ni de son historique.

docs/OIDC_DEV.txt et docs/OIDC_DEV.llms.txt contiennent la déclaration et les
points d'entrée publics du client, sans son secret. Les identifiants de client,
issuer et URL de retour ne sont pas des mots de passe.

Aucune réécriture d'historique, rotation d'accès ou publication effectuée par
cet audit. Le résultat décrit les vérifications ciblées réalisées, sans
certifier une absence absolue de secret inconnu.
