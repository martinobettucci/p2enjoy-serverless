# Borne globale des observations d'invocation

Preuve de [SLS-078.5](BACKLOG.md#sls-078), partagée avec la borne numérique de
[SLS-091.1](BACKLOG.md#sls-091), selon [SCHEDULE_RETENTION](SCHEDULE_RETENTION.md#autres-preuves-requises).
Décision du11 novembre2026 avant code. Les sept jours et la borne des tirs
planifiés restent des preuves distinctes ; aucun résultat d'âge n'est déduit
du volume. Aucune ligne ou date métier n'est fabriquée.

## Installation réelle et garde

Réutiliser le mode `instance-limit` de storage-legacy-environment.py : même
image immuable que le contrôle habituel, installation neuve à plafond2,
vrais SSO/API/runtime/agent et route HTTPS18090 existante. Les originaux sont
conservés par identité et sauvegardes natives, selon
[INSTANCE_LIMIT_RESTORATION](INSTANCE_LIMIT_RESTORATION.md#installation-temporaire-réelle).
La fenêtre interrompt temporairement le contrôle DEV habituel ; la référence
reste en marche. Aucun fichier officiel ou proposition de variable n'est écrit.

Ajouter uniquement l'option explicite `--guard-seconds=1800` au mode existant,
pour borner la charge réelle et son nettoyage. Les durées par défaut900s,
option120s et mode partial60s restent inchangées. Les deux options de durée
sont mutuellement exclusives et interdites aux autres modes. Journal et événement
d'armement portent la durée ; relever aussi la programmation réelle du timer
systemd. Garde indépendante, appartenance et programme figé sont inchangés.
Le cas nominal1800 et les régressions ciblées120/partial doivent être éprouvés.

## Parcours et discriminants

Trois groupes de campagne, strictement en série :

1. Nouvelle connexion SSO normale depuis l'accueil de l'installation temporaire.
   Créer namespace/service, jeton Read et deux fonctions originales avec
   cpu0,5/mémoire128Mio/minimum=maximum=concurrence1/idle0/deadline10s/file30s,
   stockage partagé et données/cache désactivés. Publier/promouvoir leur vrai
   handler `retention-observation.handler`, sans cron. Constater deux conteneurs
   réels, total1CPU/256Mio, aucun appel encore enregistré. Le handler reçoit un
   numéro de séquence et renvoie/journalise ce numéro, son requestId et son marqueur.
2. Deux flux HTTP réels, un par fonction, sans rejeu automatique. Chaque flux
   attend sa réponse avant le suivant ; ce sont deux consommateurs d'un même
   scénario, pas deux campagnes. Arrêter et joindre après4992 appels par fonction
   (9984 au total). Relever toutes les observations natives, leurs UUID et dates
   de fin : aucune suppression avant la borne. Puis16 autres appels par fonction,
   pour10016 au total/5008 chacun. Attendre la maintenance normale, sans l'appeler
   depuis le test, et relever exactement10000 observations terminales.
   Leurs UUID doivent être exactement les10000 plus récents par completed_at DESC,
   id DESC, calculés depuis le relevé9984 et les32 nouveaux appels retrouvés dans
   le relevé final. Les16 plus anciens sont absents. Aucun appel en cours/refusé,
   réponses200, requestId/sequence/hash exécuté exacts pour les10016 handlers.
   Chaque fonction reste sous10000 : le discriminant prouve la portée globale.
3. Passer min0/idle0 par PUT normal, attendre zéro instance, révoquer le jeton,
   archiver/purger les deux fonctions et supprimer leurs parents par API.
   Constater code/volumes/consommateurs absents avant restitution nominale.
   Joindre le pilote, contrôler timer/service inactifs, mêmes originaux/données/
   artefacts/configurations et référence, contrôle sain de même image/ID avec
   redémarrage attendu. Un échec stoppe ses flux et rejoint les requêtes avant
   la restitution ; il est conservé et ne déclenche aucun rejeu automatique.

Le lecteur capacity existant fournit toutes les observations et les CID :
aucun nouveau lecteur SQL ou endpoint applicatif. Rapports locaux UUID privés,
numéros/UUID/dates conservés, sortie de progression bornée. Identifiants SSO
par stdin privée et jeton en mémoire seulement. Sources/images avant et après
doivent concorder ; aucune nouvelle UI, migration, image ou variable officielle.
