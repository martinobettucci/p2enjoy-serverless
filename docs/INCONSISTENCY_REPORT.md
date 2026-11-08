# Incohérences hors de l’unité en cours

## INC-003 — Titre de fiche d’archive après purge

Revue visuelle du 8 novembre : `storage-ui-purged-mobile.jpg` présente le titre
« Archives conservées » au-dessus du badge « Purgée », de zéro révision et zéro
Mio de code. Le reçu de purge terminé et les volumes absents sont explicites ;
ce constat ne remet pas en cause l’effacement physique éprouvé.

Vérification principale : `web/src/storage.jsx:96` choisit ce titre pour toute
fiche d’archive, sans tenir compte de `purged_at`, tandis que le badge en tient
compte à la ligne 100. Le titre devrait nommer la fiche sans affirmer une
rétention de contenu déjà purgé. Le code est antérieur à SLS-067 et aucune
source produit n’est modifiée pendant sa qualification.
