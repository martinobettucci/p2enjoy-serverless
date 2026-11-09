# Registre d’incohérences

## SLS-050-GATE-WAL — Décision commit non atteinte par la garde de preuve

Statut : ouverte, issue retenue dans
[ADMISSION](ADMISSION.md#observation-durable-des-intentions-par-les-gardes).

Le scénario attend un commit observé ; le vrai PUT a rendu503 avec
SQLITE_BUSY_RECOVERY dans BEGIN IMMEDIATE après SIGKILL, avant le gate attendu.
Le site appelant exact et la responsabilité du poller restent inconnus.
Le nettoyage natif est établi séparément ; le rapport initial reste en échec.

Issue : conserver une connexion de lecture autocommit réelle, préalablement
observée, au lieu de rouvrir la base à chaque milliseconde. Garder les mêmes
prédicats, writers, décisions, signaux et appel HTTPS ; aucun rejeu automatique.
Retirer cette entrée après preuve réelle des gates, du SIGKILL après décision
et de leur nettoyage. Un succès n’attribue pas rétrospectivement la course WAL
au poller et ne constitue pas une modification du comportement produit.
