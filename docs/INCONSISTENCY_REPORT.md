# Incohérences de publication en cours de résolution

## SLS-063-OBS-2 — succès ancien après actualisation

La capture `publication-ui-storage-confirmation-pending.jpg` montre la nouvelle
publication en attente de confirmation avec un succès d’activation précédent.
Ce message sans date peut être lu comme la confirmation du nouvel état, alors
que son quota a changé. Même preuve de revue ci-dessus.

Issue retenue : une actualisation ou sélection explicite efface le message de
succès précédent. Les diagnostics d’erreur et l’avis de stockage restent portés
par leurs états propres. La preuve vérifie l’absence d’un ancien succès dans
les lectures en erreur et pendant la confirmation de stockage en attente.
