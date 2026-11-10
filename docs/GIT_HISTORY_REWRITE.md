# Retrait du briefing privé de l'historique Git

## Décision et périmètre

Le10 novembre2026, le responsable demande d'ignorer docs/dev-spark.md et de
réécrire l'historique avant sa publication GitHub. Le fichier reste disponible
localement ; son contenu est retiré de tous les commits et références locales.
Les autres coordonnées DEV présentes dans les scripts et preuves restent dans
le périmètre public déjà signalé par l'audit ; cette opération vise ce fichier.

Une sauvegarde Git et une copie du fichier sont conservées dans .local ignoré,
avec permissions privées. La réécriture porte sur les références locales, sans
créer de branche ni de remote et sans opération sur les services du SPARK.
Après contrôle, les références de sauvegarde créées par Git et les reflogs
anciens sont retirés, puis les objets devenus inaccessibles sont collectés.

## Sources historiques et preuves

Trois bancs lisent un commit historique par git archive ou git show. Leurs
lectures sont remappées vers les nouveaux commits. L'identité historique déjà
employée par les attestations et preuves reste stable ; source_revision indique
le commit Git effectivement lu après réécriture. Les preuves datées existantes
restent intactes. Une table ancien→nouveau permet leur interprétation.

## Vérifications requises

Le fichier local conserve ses octets et son mode ; git check-ignore le couvre,
git ls-files ne le suit plus, aucune entrée du chemin ou de son blob ne reste
dans les commits/références accessibles. Comparer chaque arbre avant/après en
excluant seulement ce chemin ; vérifier les parents, auteurs, dates et messages.
Les sources historiques sélectionnées doivent conserver exactement leurs objets
control/web/manual/validator. Vérifier aussi git fsck, l'archive de publication,
l'état propre et l'absence de remote. Les vérifications utilisent le vrai dépôt.
