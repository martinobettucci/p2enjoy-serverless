# Registre d’incohérences

## SLS-074-PURGE-006 — Purge engagée refusée par le premier backfill

Statut : ouverte, correction décidée dans
[FUNCTION_VERSION_PURGE_UPGRADE](FUNCTION_VERSION_PURGE_UPGRADE.md).

Le backfill de `control/app/db.py` refuse un inventaire vide avec octets
comptabilisés. Or `storage_management.py` efface l’inventaire au commit de purge,
avant l’effacement physique. Un état 006 valide bloque donc 007 avant la reprise
des opérations. L’upgrade au repos déjà effectué et les restarts après 007 ne
sont pas invalidés par ce constat de revue statique ; le parcours intermédiaire
reste à produire réellement et à corriger.

Issue retenue : reconnaître la seule décision de purge fortement corrélée,
garder l’identité inconnue et les compteurs, puis reprendre normalement. Le
contrat précise les phases, la référence refusée, la reprise 006, le vrai banc
historique et ses restaurations. Ne retirer cette entrée qu’après correction
et preuves réelles ciblées ; la suite commune en cours reste sur ses sources
produit/tests/fixtures/manuel figées.
