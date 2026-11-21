# Registre des incohérences

## IR-001 — URL versionnées encore décrites comme futures

Constat du21novembre2026, hors unité108 en cours.
SERVICE_CONFIGURATION_URLS, section Domaines du SPARK et chemins d’appel,
annonce encore que l’extension par hash « reste à implémenter », alors que
FUNCTION_VERSION_EXECUTION et control/app/invocation_urls.py portent déjà
la sélection version et ses chemins. Le client CLI demande ce catalogue
après publication ; la préparation de invocation-urls en est directement
affectée. L’audit RO ne démontre pas un défaut du moteur.

Mesure : un paragraphe contradictoire dans ce contrat historique ; sources
implémentées et preuves propres074 à rapprocher avant rédaction.
Issue proposée : rattacher sa clarification à109, déjà inscrite, préserver
les époques historiques et décrire le comportement courant sans prétendre
074 complètement clos. Entrée à instruire par la boucle CLAUDE§5 après les
preuves ciblées vertes de108, avant le passage complet078. Aucune modification
de ce paragraphe n’est encore appliquée.
