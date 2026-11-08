# Incohérences hors de l’unité en cours

## INC-002 — Client du canal privé interrompu avant lecture du refus HTTP

La première suite commune SLS-067 s’arrête sur `BrokenPipeError` dans
`e2e/instance-lifecycle.py:59`, lors de l’envoi du corps `text/plain` à `/result`.
Trois campagnes sont terminées (101 groupes) et dix groupes du cycle de vie
passent avant cet arrêt ; le dernier groupe reste non qualifié. Le nettoyage
du rapport est réussi ; relevé natif : répertoire de travail, conteneurs et
réseaux d’instances absents, contrôle/référence sains, agent actif.

Le client HTTP envoie les en-têtes puis le corps séparément. Le vrai serveur
peut rendre 415 et fermer dès les en-têtes, sans attendre ce corps ; ce chemin
constitue une explication plausible, mais sa réponse n’a pas été lue pendant
l’arrêt. Ne pas convertir un BrokenPipe en 415 ni accepter None pour cette
assertion. Instruire une requête complète petite et une lecture bornée de la
vraie réponse ; prouver aussi explicitement le refus anticipé avant envoi du
corps. Le contrat serveur et les assertions sur les identifiants étrangers,
doublons, tailles et connexions restent inchangés.
