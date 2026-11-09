# Quatre alias temporaires pour la pagination réelle

Plan opératoire de SLS-066, autorisé explicitement par le responsable le9
novembre2026 et non encore appliqué. L’extension porte exactement sur les quatre
alias temporaires, leurs routes18090TLS, leurs A vers51.158.54.202 TTL300 et leur
retrait après qualification. Les deux domaines permanents restent en place.
La seconde page de cinq domaines de la console et de la CLI exige six domaines
réels ; aucune duplication de ligne ou réponse simulée ne remplace ces noms.

## Plan autorisé

Les quatre noms suivants décrivent leur usage de qualification de pagination :

| Domaine temporaire | SPARK | Port | Transport |
| --- | --- | --- | --- |
| functions-pagination-1.lelabs.tech | infra-serverless | 18090 | TLS |
| functions-pagination-2.lelabs.tech | infra-serverless | 18090 | TLS |
| functions-pagination-3.lelabs.tech | infra-serverless | 18090 | TLS |
| functions-pagination-4.lelabs.tech | infra-serverless | 18090 | TLS |

Pour chacun : A exact vers 51.158.54.202, zone lelabs.tech, TTL 300. La console
et le SSO restent sur leur domaine canonique. L’ensemble à six domaines est
temporaire ; après qualification, retirer les quatre routes et uniquement
leurs quatre enregistrements A créés pour cette preuve, puis revenir aux deux
domaines permanents. Aucune modification d’un autre nom, type DNS, SPARK ou
système de FORGE n’est proposée.

Le précontrôle normal du 9 novembre trouve les quatre noms libres dans le
rapprochement exact/générique des routes et leurs quatre A absents dans
l’aperçu du fournisseur configuré. Ce contrôle ne fait aucune mutation et
n’interroge pas le résolveur natif pour des noms encore absents, afin de ne
créer aucun nouveau cache négatif avant publication.

## Autorisation et garde-fous d’application

L’autorisation explicite de ces quatre noms, de leur DNS et de leur nettoyage
est reçue et reportée dans CLAUDE_PROJECT et le backlog. Le
[texte des quatre routes](INVOCATION_DOMAINS_PAGINATION.routes.txt) est conservé
comme description, sans valoir application. Le refus automatique de son écriture
antérieure dans routes.? précédait cette extension ; la commande n’avait pas
démarré et aucun objet n’avait été modifié par cette tentative. Il ne constitue
plus une attente de réponse du responsable.

Avant application : nouvelle lecture de disponibilité et des valeurs exactes,
créations par la console normale, aucun remplacement de valeur différente ni
rejeu aveugle après réponse perdue. Attendre les vraies résolutions et HTTPS
vérifiés. Conserver les identifiants et valeurs DNS exacts pour ne retirer que
ce qui est créé et toujours possédé au nettoyage. Une identité ou valeur changée
interrompt cette suppression ; ne jamais reprendre une propriété étrangère.
Le périmètre ne couvre aucun autre nom, type DNS ou SPARK. Les nouveaux alias
restent18090TLS ; leur cycle borné est création, qualification puis retrait.
Aucun de ces gestes ne vaut administration système de FORGE.

La preuve réutilisera les fonctions originales du dépôt. Parcours UI depuis
l’accueil, seconde page de cinq puis un domaine, copies natives et invocations
réelles ; CLI parcourant les deux pages et conservant le succès de publication
si le catalogue change après sa première page. Les scénarios et leurs sources
seront figés avant exécution. Aucun de ces résultats n’est encore acquis.


## Précontrôle après autorisation et contrat de retrait

Le [précontrôle autorisé](evidence/invocation-pagination-authorized-preflight-dev-2026-11-09.json)
retrouve les quatre noms libres, sans mutation ni requête DNS native sur ces
noms absents. L’inventaire normal de lelabs.tech retourne22 entrées, aucune de
ces quatre étiquettes ; les quatre ajouts restent sous la limite100 du relevé
actuel. Ce relevé ne prouve ni création, ni résolution, ni certificat des alias.

La console normale expose DELETE /api/dns/record avec zone, name et type. Elle
relit l’enregistrement, l’adresse de la Forge et les routes avant suppression ;
elle refuse notamment un DNS encore servi par une route. Le nettoyage retire
donc d’abord les seules routes créées, puis les seuls A exacts encore conformes
à leurs identifiants/nom/type/valeur/TTL enregistrés. Aucun autre type ou nom de
zone n’est retiré. Les deux routes et DNS permanents sont recoupés inchangés.
Une disparition ou modification inattendue reste un diagnostic, pas une preuve
d’appartenance ni une autorisation de remplacement.

Les clients et la garde de nettoyage sont préparés avant création ; les étapes
et réponses incertaines sont persistées. La campagne UI/CLI emploie les
sémantiques008 de publication sans promotion et de sélection de version.
Le contrôle et ses images n’ont pas besoin d’être reconstruits pour ces alias.

## Cycle borné et preuves retenues

Décision du9 novembre2026 avant implémentation : un opérateur dédié conserve
dans un dossier privé0700 le relevé initial, les intentions avant écriture et
les réponses connues, avec écritures atomiques et synchronisées. Il ne gère que
les quatre noms ci-dessus. Un processus indépendant, armé avant toute création,
observe l’identité PID/date de naissance du propriétaire, une demande explicite
et une échéance monotone maximale de30 minutes. Une seule mutation est permise
à la fois sous verrou ; chaque appel console est borné à45 secondes. Si le
verrou reste inaccessible60 secondes, la garde produit un échec explicite et
ne prétend pas avoir nettoyé. La suspension de l’écrivain et la panne durable
de la console restent des limites à qualifier séparément.

La garde retire les objets dont la réponse de création et l’identité relue sont
connues. Une réponse perdue n’autorise ni répétition ni adoption automatique
d’un objet : elle exige un relevé et une décision du principal. Avant chaque
suppression, la route et le DNS sont relus et comparés à leurs identifiants et
valeurs enregistrés. Un changement de propriété entraîne un diagnostic ; les
autres objets encore connus peuvent être retirés. Une absence n’est attendue
que si un retrait réussi est déjà enregistré. Le retrait normal reste routes
puis A. Les deux configurations permanentes, leurs DNS et leurs HTTPS sont
recoupés avant/après ; applied_at des routes est une observation, sans être
une configuration. Les requêtes normales de suppression ne fournissent pas de
comparaison atomique avec le relevé client ; cette limite n’est pas masquée.

Trois prérequis réels sans objets temporaires éprouvent la demande explicite,
l’échéance et la perte du propriétaire. La campagne effective conserve ensuite
un propriétaire vivant et termine par sa perte réelle après les parcours,
pour éprouver le retrait indépendant des objets effectivement créés. Aucun
rejeu automatique d’une création ou suppression n’est prévu.

Le navigateur part de l’accueil, crée namespace/service/fonction et publie une
archive originale par les formulaires. Il promeut explicitement son hash008.
La première page affiche cinq domaines distincts et la seconde un ; navigation
clavier, copies natives, appels Docker des URL et rendus desktop/mobile sont
recoupés. Les captures doivent être inspectées personnellement.

La CLI publie une fonction originale dans un service vide sans configuration
commune : six URL distinctes issues de ses deux GET de catalogue sont attendues.
Un second déploiement conserve le succès et ses identifiants si le catalogue
change après la première page. Le traceur natif existant est paramétré pour
retenir le septième connect HTTPS, après les six précédents ; aucun argument,
résultat, paquet ou réponse n’est modifié. À cette frontière, l’opérateur retire
une seule route temporaire déjà créée et connue, puis libère le vrai appel.
Ce retrait appartient au nettoyage ; la route n’est pas recréée. Le DNS restant
est retiré par la garde finale. Les anciens clients à six connexions conservent
leur valeur par défaut et doivent être rejoués pour ce changement du traceur.

La campagne est figée par empreintes avant exécution. Les preuves de garde,
création/TLS, UI et CLI sont distinctes ; aucun groupe n’est encore déclaré
réussi par le présent contrat. Les nettoyages de fonctions passent par les API
normales puis sont recoupés avec les artefacts natifs, sans compter une simple
suppression logique comme purge physique.
