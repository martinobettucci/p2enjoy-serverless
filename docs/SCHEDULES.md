# Moteur de planification

Contrat de l'unité [SLS-078](BACKLOG.md#sls-078). Il précise la ligne « crons » de
[PLATFORM](PLATFORM.md#exécution) et l'exigence de l'adaptateur
([DEPLOYMENT](DEPLOYMENT.md)) qui accepte déjà `events: - schedule`. Les jobs
configurés dans la console ([SLS-081](BACKLOG.md#sls-081),
[SERVERLESS_JOBS](SERVERLESS_JOBS.md)) s'appuient sur ce moteur.

## État constaté

L'adaptateur valide `schedule.rate` (cron à cinq champs) et `schedule.enabled`,
le contrôle les enregistre dans les événements de la révision. **Aucun composant
ne les déclenche.** Aucun avertissement n'est émis à la publication ; le manuel
et le README décrivent cette limite. Le projet de référence en dépend :
deux de ses treize fonctions sont planifiées
([compatibilité](REFERENCE_COMPATIBILITY.md#planifications)).

## Décisions

Tranchées le 10 novembre 2026 à partir des critères du contrat local (simple,
uniforme, réversible, aucune perte silencieuse) et de la précision du responsable :
l'expression est contrôlée **par fenêtres de 5 minutes**, un léger décalage est
acceptable. Chaque décision reste révisable.

| Sujet | Décision | Motif et alternatives écartées |
| --- | --- | --- |
| Résolution | Le moteur se réveille aux frontières UTC de 5 minutes (:00, :05, :10…). Un créneau nominal tombant dans la fenêtre écoulée `]frontière précédente, frontière courante]` est lancé à la frontière courante | Demande du responsable ; un tir tardif de 0 à 5 min est un décalage accepté, jamais un tir en avance. Une scrutation à la seconde coûte plus et n'est pas demandée |
| Expressions plus fines que 5 min | Acceptées. Plusieurs créneaux d'une même fenêtre sont **fusionnés** en un seul tir, le nombre fusionné étant consigné (`coalesced`) | Refuser `* * * * *` surprendrait un utilisateur de cron ; la fusion est explicite, visible et jamais silencieuse |
| Pas de tir en avance | Un créneau n'est jamais lancé avant son instant nominal | Cron attend cela ; la fenêtre ne fait que retarder |
| Base de temps | UTC uniquement, déjà imposé par le modèle (`timezone: UTC`) | Un fuseau par fonction ajoute une configuration obligatoire sans demande ; ajoutable plus tard sans casser l'existant |
| Syntaxe | Cinq champs : listes, plages, pas, `*` ; dimanche = 0 ou 7 | Sous-ensemble déjà validé par l'adaptateur et le contrôle ; pas de noms de mois/jours ni `@hourly`, refusés comme aujourd'hui |
| Jour du mois et jour de la semaine | Si les deux sont restreints, l'un **ou** l'autre déclenche (cron historique) | Comportement attendu de quiconque connaît cron ; un ET surprendrait |
| Rattrapage | Aucun. Les fenêtres manquées pendant un arrêt sont ignorées et consignées `skipped_downtime` | Déjà dit par PLATFORM : pas de rafale au redémarrage |
| Recouvrement | Un tir n'est pas lancé si le précédent de la même planification tourne encore ; consigné `skipped_overlap` | Évite l'empilement d'un travail long ; une file cacherait la dérive |
| Rejeu | Jamais. Un tir est « réclamé » durablement avant l'envoi ; un arrêt entre réclamation et envoi n'est pas rejoué | Même règle que toute invocation interrompue : les effets métier ont pu avoir lieu |
| Refus d'admission | Consigné `refused_capacity` (ou `refused_*` selon la cause) ; aucun retry | Un retry masquerait la saturation et la rendrait non reproductible |
| Origines | Manifeste et console alimentent le même moteur : un seul calcul de créneaux, une seule table de tirs | Deux ordonnanceurs donneraient deux comportements pour le même cron |

## Contrat

**Deux origines, un moteur.** Une planification a une origine :

- `manifest` : déclarée par `events: - schedule` de la version. Elle suit la
  version actuellement promue de la fonction
  ([FUNCTION_VERSIONS](FUNCTION_VERSIONS.md#appel-par-défaut-et-appel-par-tag)).
  Publier un pilote ne déclenche rien ; promouvoir ou revenir à un hash remplace
  l'ensemble des planifications de cette origine à l'instant de la décision.
  Le corps est `{}`.
- `console` : un job de [SERVERLESS_JOBS](SERVERLESS_JOBS.md), propre à la fonction,
  indépendant des versions. Le corps est son payload évalué.

Une fonction désactivée, supprimée ou archivée ne se déclenche plus ; un tir déjà
admis termine dans sa deadline. `enabled: false` conserve la déclaration sans tir.

**Événement.** Le tir est une invocation produite par le contrôle, sans jeton ni
politique origine/IP (aucun client HTTP n'est en jeu). Elle passe par la même
admission que les appels HTTP : budgets CPU/RAM/instances, file, concurrence,
verrou de stockage exclusif, deadline `timeout_seconds`, extinction après
`idle_seconds`. L'événement est un événement HTTP v1 synthétique :
`httpMethod: POST`, `path: /` comme les déclencheurs CRON de Scaleway (ou
l'endpoint choisi pour un job), `body` chaîne JSON valide, `isBase64Encoded: false`,
aucun en-tête `Authorization`, `requestContext.requestId` fourni par le contrôle
et les en-têtes `x-p2enjoy-trigger` (`schedule`, `job` ou `manual`) et
`x-p2enjoy-schedule-slot` (instant nominal UTC ISO). Un handler qui fait `JSON.parse(event.body)` ou lit
`event.httpMethod` fonctionne donc sans adaptation.

**Décalage.** Le tir part à la frontière de 5 minutes suivant le créneau nominal,
avec une tolérance de cinq secondes tant que le contrôle est vivant. Créneau
nominal, instant du tir et retard sont consignés.

**Persistance.** Chaque tir possède un enregistrement durable (fonction, version
ou job, origine, expression, créneau nominal, fenêtre, état, instant réel,
`coalesced`, invocation liée). États : `claimed`, `dispatched`, `succeeded`,
`failed`, `skipped_downtime`, `skipped_overlap`, `refused_*`. Une migration
versionnée l'introduit, avec mise à jour du schéma ([SCHEMA](SCHEMA.md)), du
contrat de déploiement et du seed. La rétention suit celle des invocations.

**Consultation.** L'invocation porte `trigger: schedule`, l'origine, l'expression
et le créneau ; elle apparaît dans la liste des invocations, ses journaux et le
monitoring ([SLS-072](BACKLOG.md#sls-072), [SLS-073](BACKLOG.md#sls-073)). La
fiche de fonction affiche ses planifications actives avec prochain tir, dernier
résultat et état, en lecture avec le droit Read. Les planifications d'origine
`manifest` se modifient par un déploiement ou une promotion, jamais par la console.

**Adaptateur.** Tant que le moteur n'est pas déployé, `plan` et `deploy` émettent
un avertissement explicite par fonction planifiée (« planification enregistrée,
non déclenchée »). Cet avertissement disparaît au déploiement du moteur ; le
manuel est mis à jour dans le même changement.

## Preuves E2E attendues

Horloge réelle, handler réel dans Docker sur le SPARK DEV, sans mock ni attente
arbitraire. La résolution de 5 minutes rend chaque attente coûteuse : tous les
fonctions, jobs et planifications d'un scénario sont créés **avant** la frontière
suivante, puis observés ensemble ; une attente est bornée par l'événement observé.

- `*/5 * * * *` : deux tirs consécutifs, corps `{}` et méthode POST observés par
  le handler, retard consigné ≤ tolérance, invocation visible dans l'API et la console ;
- `* * * * *` : un seul tir par fenêtre, `coalesced` égal au nombre de créneaux
  fusionnés, aucun tir en avance sur le créneau nominal ;
- une expression à un instant UTC précis (heure et jour de semaine) ne tire ni
  avant ni après sa fenêtre ; jour du mois OU jour de la semaine ; `enabled: false` ;
- pilote publié non promu : aucun tir ; promotion : tir sur le nouveau code ;
  retour à l'ancien hash : tir sur l'ancien code ; planification retirée par une
  nouvelle version : plus de tir ; jobs de la console inchangés par ces changements ;
- fonction désactivée, supprimée puis archivée : plus de tir, aucun résidu ;
- SIGKILL du contrôle avant puis après la réclamation d'un tir : aucun doublon,
  aucun rattrapage, état durable cohérent, reprise aux fenêtres suivantes ;
- arrêt couvrant plusieurs fenêtres : un `skipped_downtime` par fenêtre manquée
  et par planification, jamais de rafale au redémarrage ;
- handler plus long que l'intervalle : `skipped_overlap`, un seul en cours ;
- saturation des budgets : `refused_capacity` consigné, aucune invocation créée,
  budgets restitués ; stockage exclusif occupé par une invocation HTTP ;
- droits : lecture avec Read, aucune mutation sans Update, session non
  administratrice refusée par requête directe ;
- parcours UI depuis l'accueil réel (fiche de fonction, prochain tir, dernier
  résultat, vide, long nom, mobile), captures inspectées ;
- fixtures originales reproduisant les deux fonctions planifiées de la référence
  ([REFERENCE_COMPATIBILITY](REFERENCE_COMPATIBILITY.md#planifications)).

## Réalisation du moteur et migration 009

Décision de réalisation du 10 novembre 2026, avant code. Le premier checkpoint
livre le calcul commun, la migration, le moteur et ses lectures API ; la facette
et sa qualification visuelle suivent dans cette même unité, qui reste `[~]`
jusqu'à toutes ses preuves. Il ne constitue pas une clôture de SLS-078.

- `schedule_calendar.py` compile les cinq champs sans dépendance supplémentaire.
  Un pas sur un nombre (`5/10`) progresse de ce nombre à la borne du champ ;
  un pas sur une plage reste dans cette plage. Un champ littéralement `*` est
  non restreint pour la règle jour/mois OU semaine ; les autres sont restreints.
  Le créneau retenu est le dernier nominal de la fenêtre, `coalesced` compte
  tous les nominaux éligibles. Activation exclusive, retrait inclusif : aucun
  créneau antérieur à la promotion n'est rattrapé.
- La migration 009 conserve des générations de planifications `manifest`
  (fonction, révision, hash, événements, dates d'activation et de retrait).
  Des triggers SQLite suivent le pointeur promu dans la transaction de la
  décision ; une mutation de variables ou un upload pilote ne les remplace pas.
  Les pointeurs déjà présents démarrent à l'application de 009, sans rattrapage.
- Un curseur durable global enregistre la dernière frontière traitée. Le premier
  démarrage initialise ce curseur à la frontière précédente ; aux reprises, les
  frontières écoulées sont marquées `skipped_downtime`, jamais envoyées. Le
  traitement avance par lots bornés pour ne pas bloquer le contrôle lors d'un
  arrêt long. Un saut d'horloge en arrière ne recalcule pas une fenêtre acquise.
- Une réclamation porte un UUID et une unicité génération/index/fenêtre.
  L'invocation est liée au tir dans sa transaction de réception, après la
  réclamation. Une réclamation interrompue sans invocation devient
  `failed/control_interrupted` ; un lien présent se réconcilie à l'état durable
  de l'invocation. Aucun de ces états ne provoque de nouvel envoi.
- L'entrée interne est inaccessible par HTTP. Elle relit la génération promue,
  les parents et les intentions de stockage à la réception puis à l'admission.
  Elle fournit `POST /`, JSON `{}` même sans événement HTTP déclaré, sans jeton,
  et conserve la file, les réservations, les deadlines et le pilote Docker
  existants. Une promotion avant admission refuse l'ancien tir ; après admission
  l'instantané termine normalement.
- Pour le cas de saturation sans invocation demandé par les preuves, le contrôle
  vérifie avant création qu'une instance prête de la bonne génération est
  utilisable ou qu'une nouvelle réservation tient dans les budgets. Si aucune
  place n'existe, seul le tir `refused_capacity` est conservé. Ce précontrôle
  réutilise le calcul de capacité du moteur ; l'admission atomique reste l'autorité
  finale. Un stockage exclusif occupé conserve l'attente bornée ordinaire.
- `invocations` reçoit `trigger` (défaut `http`), `schedule_firing_id`,
  `schedule_origin`, `schedule_expression` et `schedule_slot`. Les valeurs de
  corps et les secrets ne sont pas copiés dans le registre de tirs.
- `GET /api/functions/{id}/schedules` expose les déclarations courantes, leur
  index, hash, activation, état et prochain nominal/effectif ;
  `GET /api/functions/{id}/schedule-firings` expose l'historique (pagination
  20 par défaut, 1–100, offset 0–10000). Read sur cette fonction ou session admin
  obligatoire, vérifié avant lecture. Aucun endpoint public de déclenchement
  artificiel ni de réglage de l'horloge n'est ajouté.
- Le moteur clôture les tirs depuis les invocations terminales. Rétention sept
  jours et 10 000 tirs terminaux ; actifs conservés. Les générations retirées
  sont supprimées après leur rétention lorsqu'aucun tir ne les référence.
  Le moteur démarre après la reprise d'exécution et s'arrête avant elle.
  Une maintenance impossible dégrade `/healthz`, sans rejouer les tirs.

Déploiement : image du contrôle reconstruite, sauvegarde SQLite native préalable,
application de 009 au redémarrage DEV ; aucune variable, route ou secret nouveau.
L'ancienne image est conservée ; revenir avant 009 exige une restauration explicite
avec prise en compte des écritures nouvelles, jamais une rétro-migration automatique.
