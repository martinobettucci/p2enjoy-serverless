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
Compléter par le défaut900 sans option et deux refus réels du helper avant
toute fenêtre :120+1800 simultanés, et1800 hors mode instance-limit. Les refus
ne créent aucun répertoire de campagne et conservent les identités des services.
Le client de ces trois groupes est `e2e/instance-limit-guard-options.py`.

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

## Franchissement réel qualifié

La [preuve228a99c](evidence/invocation-retention-volume-dev-2026-11-11.json)
passe trois groupes sur337sources, même imagec59b8616.10016 handlers réussis,
5008 par fonction. Le relevé avant borne conserve9984 observations ; après
les32 appels supplémentaires et la maintenance normale, exactement10000 UUID
restent, les16 plus anciens sont absents. Le tri par dates réelles/id et les
comptes natifs par fonction sont rapprochés de toutes les réponses HTTP.
Les10016 observations proviennent exactement des deux instances préchauffées.

Deux purges publiques terminées, code/volumes/conteneurs/réseaux/canaux absents,
restitution des originaux et timer/service joints. Même contrôle/image et
référence, redémarrage attendu du contrôle ; données, artefacts et configurations
officielles conservés. Le parcours complet dure1554,343s, préparation et
nettoyage compris ; aucun débit stable ou maximum de plateforme n'en est déduit.

Le rapport intégral de10265074 octets est conservé dans
[l'archive JSON gzip](evidence/invocation-retention-volume-dev-2026-11-11.raw.json.gz),
sans secret. SHA du JSON décompressé et de l'archive sont dans la preuve ; gzip
est déterministe (mtime0). Il contient les10016 réponses et les deux relevés
natifs complets. Les trois groupes ne sont pas recomptés par ses sous-assertions.

Portée : borne numérique des observations HTTP terminales ordinaires. Les
sources de tir non clos sous cette borne, les10000 tirs planifiés, les sept
jours et les replays gardés restent à qualifier. Les régressions de restitution
du helper modifié sont qualifiées séparément ci-dessous.

## Gardes et options qualifiées

La [preuve des gardes](evidence/invocation-retention-guard-regressions-dev-2026-11-11.json)
passe14 groupes : dix pour release/EOF/SIGTERM/SIGKILL/échéance à120s, un pour
la perte après premier renommage à60s, trois pour deux refus d'options avant
mutation et le défaut900 réellement programmé/restitué. Le journal natif de
partial confirme60s et le même SHA de helper figé. Les deux refus ne créent
aucun répertoire et conservent les identités complètes des services.

Deux époques :337sources pour les onze régressions,338 pour les trois options ;
les337 sources communes, le helper et les images sont identiques. Le volume
à1800s garde sa propre preuve de trois groupes :17 groupes au total de cette
étape, sans addition des assertions internes. Les pannes propres des nouveaux
clients ne sont pas déduites des nominaux ; aucune campagne complète revendiquée.
