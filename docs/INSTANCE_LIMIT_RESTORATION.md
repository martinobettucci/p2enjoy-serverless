# Restitution du plafond d'instances de qualification

Contrat de correction de [SLS-099](BACKLOG.md#sls-099), préalable au test du
plafond global de SLS-078. Cible unique : SPARK DEV infra-serverless ; clé unique :
`SERVERLESS_FUNCTION_INSTANCE_LIMIT`. Toute écriture passe par la console normale.

## Autorité de comparaison

Mesure du10 novembre2026 : GET de l'environnement et des suggestions répondent200,
plafond32, origine spark. Les sources de sparkd montrent que PUT env lit seulement
value/secret ; suggestions/apply vérifie le SHA de la proposition, puis importe
sans condition sur l'entrée active. L'UPDATE de poser porte seulement WHERE id.
updated_at est à la seconde. Ces observations ne prouvent aucune course provoquée.

Une lecture de2 suivie d'une écriture de32 peut donc écraser une édition entre
les deux. Un verrou local de garde, un second GET ou un contrôle après écriture
ne garantit pas la conservation de cette édition. Aucun de ces palliatifs n'est
retenu comme correction de SLS-099.2.

La capacité nécessaire est une version d'entrée active, modifiée à chaque
mutation, et une précondition vérifiée par l'autorité dans la même transaction
que l'écriture. Un conflit ne modifie ni le registre ni la projection. Une valeur
revenue à2 après d'autres mutations doit également être distinguée. Le SHA de
proposition continue à protéger la proposition ; il ne remplace pas cette version.

## Refus avant toute mutation

Tant que cette capacité n'est pas fournie et qualifiée, le helper maintenu refuse
la baisse32→2 : sortie2, événement `instance-limit-blocked`, code fixe
`active_environment_precondition_unavailable`, zéro mutation. Il vérifie d'abord
l'identité du SPARK, le namespace de campagne `invocation-<8hex>`, l'absence de
fonction étrangère, appel/instance/opération/réservation active, la cohérence
officielle/consommée et la santé des deux services. Aucune proposition n'est
écrite et aucun Compose n'est lancé, même sur EOF ou réception de `restore`.

Le nominal historique est conservé dans ses preuves et son commit source ; il
n'est pas attribué au helper corrigé. Les campagnes qui ont besoin d'abaisser le
plafond échouent explicitement sur ce prérequis. Elles ne sont ni ignorées ni
annoncées réussies. Les preuves indépendantes continuent.

## Suite après capacité externe

La restitution indépendante reste à réaliser après définition du vrai protocole
conditionnel : garde armée avant baisse, identité/version de l'application,
mutation et restitution sérialisées, aucun rejeu d'une réponse inconnue,
fin des processus/gardes attendue. Une édition concurrente produit une issue de
conflit explicite ; elle n'est ni remplacée ni adoptée silencieusement.

Les preuves exigées restent intégralement32→2→32, EOF, SIGTERM, perte SIGKILL du
helper, échéance et édition concurrente (dont retour à la même valeur). Elles
recoupent valeur active, valeur consommée, autres configurations et référence.
Aucune clôture de SLS-099 sur le seul refus préventif.

## Preuve ciblée du refus

Un namespace original est créé par l'API administrateur réelle. Le vrai helper
est exécuté avec l'entrée `restore`, puis avec EOF ; chacun doit refuser avant
mutation. Les relevés natifs avant/après doivent conserver fichiers officiels,
propositions, services (ID/image/démarrage), budgets et compteurs. Le namespace
est supprimé par l'API réelle. Sources locales/distantes et image sont recoupées.

L'évolution conditionnelle de la console est un accès/capacité externe, cas4 de
CLAUDE : l'administration et la modification de FORGE sont interdites ici.
Le propriétaire fournit cette capacité ; ce dépôt n'altère aucun code de FORGE.

## Résultat ciblé du10 novembre2026

La [preuve DEV](evidence/instance-limit-safety-dev-2026-11-10.json), client6e573c0,
passe deux groupes réels et deux refus restore/EOF, zéro skip/erreur de nettoyage.
Les317 sources locales/distantes sont figées avant/après, mêmes images contrôle
et CLI. Plafond32/CPU1/RAM8192, quatre fichiers officiels/proposition et les deux
services (ID/image/démarrage/santé) restent identiques. Le namespace est supprimé
par HTTPS et recoupé en base ; aucun service associé ni ressource active restante.
Les5982 artefacts antérieurs conservent leur empreinte d'inventaire.

Ce résultat qualifie uniquement le refus préventif. Aucun cycle32→2→32, SIGTERM,
SIGKILL ou conflit d'écriture n'est attribué à ce correctif. La demande de capacité
conditionnelle est transmise ; les autres preuves SLS-078 restent livrables.
