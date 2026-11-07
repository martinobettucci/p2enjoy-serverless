# Incohérences de publication en cours de résolution

## SLS-063-OBS-1 — état différent du même candidat

La première régression commune passe 312 groupes. Sa revue visuelle observe
cependant le même UUID en « Validation du handler » dans le suivi et en
« Réception de l’archive » dans la liste. Les GET sont séquentiels et la
transition du candidat ne modifie pas la version de fonction qui déclenche
une nouvelle lecture. Preuve : `publication-ui-validating.jpg`, empreinte et
constat dans [la revue](evidence/publication-console-review-dev-2026-11-07.json).

Issue retenue : la lecture individuelle plus récente du candidat suivi remplace
sa ligne dans le même cycle d’affichage. Une observation DOM atomique vérifie
la concordance des deux badges pendant une vraie validation Docker.

## SLS-063-OBS-2 — succès ancien après actualisation

La capture `publication-ui-storage-confirmation-pending.jpg` montre la nouvelle
publication en attente de confirmation avec un succès d’activation précédent.
Ce message sans date peut être lu comme la confirmation du nouvel état, alors
que son quota a changé. Même preuve de revue ci-dessus.

Issue retenue : une actualisation ou sélection explicite efface le message de
succès précédent. Les diagnostics d’erreur et l’avis de stockage restent portés
par leurs états propres. La preuve vérifie l’absence d’un ancien succès dans
les lectures en erreur et pendant la confirmation de stockage en attente.
