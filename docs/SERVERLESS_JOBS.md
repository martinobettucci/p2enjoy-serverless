# Jobs serverless

Contrat de l'unité [SLS-081](BACKLOG.md#sls-081), demande du responsable du
10 novembre 2026 : exécuter une fonction avec **un payload fixe complété de
quelques gabarits composés dans l'UI**, selon une **expression crontab contrôlée
par fenêtres de 5 minutes** (un léger décalage est accepté). Un job est le
déclencheur CRON avec arguments JSON de Scaleway Functions
([parité](SCALEWAY_PARITY.md#déclencheurs)) ; son moteur est celui de
[SCHEDULES](SCHEDULES.md), qui fixe les fenêtres, états, fusions, recouvrements,
absence de rejeu et de rattrapage.

## Définition

Un job appartient à **une fonction** (UUID stable) et porte :

| Champ | Règle |
| --- | --- |
| `name` | Unique dans la fonction, mêmes caractères que les noms de fonction, 1 à 63 |
| `description` | Facultative, texte, 512 caractères au plus |
| `enabled` | Booléen ; faux conserve la définition sans tir |
| `cron` | Cinq champs UTC (listes, plages, pas, `*`), grammaire de [SCHEDULES](SCHEDULES.md#décisions) |
| `endpoint` | Chemin d'un événement HTTP déclaré par la version promue acceptant `POST` ; défaut `/`, comme Scaleway |
| `payload` | Objet JSON de 64 Kio au plus après sérialisation ; les valeurs texte peuvent contenir des gabarits |
| versions | `updated_at` sert d'`If-Match`, comme les autres ressources |

Initialement : 16 jobs par fonction, 512 par installation (variable de cellule
documentée si modifiée). Le job ne dépend d'aucune version : il appelle la cible
**promue au moment du tir**, jamais un pilote. Si une promotion retire l'endpoint
choisi, le tir est consigné `refused_endpoint`, aucune invocation n'est créée et
l'interface signale le job « à corriger ». Supprimer une fonction supprime ses
jobs ; la renommer les conserve. Un job ne transporte ni en-tête personnalisé,
ni `Authorization`, ni valeur de variable ou secret : l'authentification métier
d'un tir planifié passe par la configuration de la fonction.

## Gabarits

Les gabarits sont une liste fermée, remplacée dans les **valeurs texte** du
payload à chaque tir. Aucune expression, boucle, appel, accès aux variables ou
secrets. Un gabarit inconnu est refusé à l'enregistrement, jamais au tir.

| Gabarit | Valeur |
| --- | --- |
| `{{slot}}` | Créneau nominal UTC, `2026-11-10T21:00:00Z` |
| `{{slot.date}}`, `{{slot.time}}` | `2026-11-10`, `21:00` |
| `{{slot.epoch}}` | Secondes Unix du créneau nominal |
| `{{previous_slot}}` | Créneau nominal précédent de ce job, calculé depuis l'expression ; `null` s'il n'existe pas |
| `{{fired_at}}` | Instant UTC réel du tir |
| `{{run.id}}` | Identifiant unique du tir |
| `{{job.name}}`, `{{job.id}}` | Nom et UUID du job |
| `{{function.id}}`, `{{function.name}}`, `{{service.name}}` | Identité de la cible |

Une valeur qui est **exactement** un gabarit prend son type JSON : `slot.epoch`
devient un nombre, `previous_slot` peut devenir `null`. Dans un texte plus long
tout est texte. `{{{{` produit le texte `{{`. Le payload est stocké en clair et
lisible avec le droit Read : l'interface l'indique et n'y accepte aucun champ de
secret.

## Composition dans l'interface

Depuis la fiche de fonction, l'onglet **Jobs** liste les jobs et ouvre un
formulaire accessible au clavier :

1. **Planification.** Modèles courants (toutes les 5 minutes, chaque heure,
   chaque jour à une heure UTC, jours ouvrés, hebdomadaire) qui remplissent
   l'expression, plus saisie libre. Une phrase en français décrit l'expression et
   la liste des cinq prochains tirs montre pour chacun le créneau nominal et
   l'instant effectif de la fenêtre de 5 minutes. Une expression plus fine que
   5 minutes est acceptée avec un avis : les créneaux d'une même fenêtre sont
   fusionnés.
2. **Payload.** Éditeur JSON avec validation en direct, compteur de taille et
   palette de gabarits (liste décrite, insertion au curseur à la souris et au
   clavier). Un aperçu montre le corps exact qui serait envoyé au prochain tir.
3. **Cible.** Choix de l'endpoint parmi ceux de la version promue.
4. **Activation** puis enregistrement. Les erreurs de serveur (409 de version,
   gabarit inconnu, taille, limite) s'affichent près du champ concerné sans
   perdre la saisie.

La liste affiche nom, phrase de planification, état, prochain tir (nominal et
effectif), dernier résultat. Le service affiche aussi la liste de tous ses jobs.
États vide, erreur, chargement, longs noms et mobile sont traités.

## Historique et exécution manuelle

Chaque tir produit un enregistrement du moteur et, s'il est admis, une invocation
liée (`trigger: job`, nom du job, créneau nominal, retard). L'historique du job
affiche créneau, instant réel, retard, état, raison, durée, statut HTTP de la
réponse, nombre de créneaux fusionnés, et mène à l'invocation et à ses journaux.
Le vocabulaire reprend celui des exécutions de jobs Scaleway : `succeeded`
(réponse 2xx), `failed` avec une raison (`exited_with_error`, `timeout`,
`memory_usage_exceeded`, `technical_error`, `invalid_request`), `quota_exceeded`
pour un refus de capacité et les états `skipped_*` du moteur.

**Exécuter maintenant** lance un tir `trigger: manual` avec le payload évalué
pour l'instant courant, sous les mêmes admissions que les tirs planifiés. Il est
refusé en 409 tant qu'un tir du même job est en cours. Il exige Update.

## Droits

Read : lire définitions, aperçus et historique. Update : créer, modifier,
activer, désactiver, supprimer et exécuter maintenant. Un jeton restreint à des
fonctions n'agit que sur leurs jobs. Une session administratrice a les deux
droits. Tout est contrôlé côté serveur et prouvé par requête directe, sans
l'interface.

## API

`GET|POST /api/functions/{key}/jobs`, `GET|PUT|DELETE /api/jobs/{key}`,
`POST /api/jobs/{key}/run`, `GET /api/jobs/{key}/runs`,
`POST /api/jobs/preview` (valide expression et payload, renvoie les prochains
tirs et le corps résolu, sans rien enregistrer). Les mutations sont auditées au
service. Migration, schéma, seed, manuel, `DESIGN_SYSTEM_APP.md` (éditeur,
palette, liste de tirs) et contrat de déploiement sont mis à jour avec l'unité.

## Preuves E2E attendues

Parcours depuis l'accueil réel avec le SSO, fonction de qualification et handler
qui enregistre le corps reçu dans son volume de données. Les jobs d'un scénario
sont créés **avant** la frontière de 5 minutes suivante et observés ensemble.

- création par l'UI : expression composée, gabarits insérés à la souris puis au
  clavier, aperçu, enregistrement ; le handler reçoit au tir le corps exact avec
  `slot`, `fired_at`, `previous_slot` et `slot.epoch` cohérents, en `POST` sur `/` ;
- aucun tir en avance, retard borné, fusion d'une expression à la minute,
  `enabled: false`, modification et suppression prises en compte à la fenêtre suivante ;
- refus : JSON invalide, gabarit inconnu, texte non conforme, payload de 64 Kio + 1,
  17e job, cron hors grammaire, `If-Match` périmé en 409, doublon de nom ;
- droits par requêtes directes : Read ne mute pas, jeton d'une autre fonction
  refusé, session non administratrice refusée, aucun secret ni jeton dans les
  réponses ou journaux ;
- exécuter maintenant : tir manuel, 409 pendant un tir, invocation et journaux liés ;
- promotion, retour de hash et pilote : le job suit la cible promue ; endpoint retiré
  → `refused_endpoint` et alerte UI ; fonction désactivée, renommée, supprimée ;
- SIGKILL du contrôle, arrêt de plusieurs fenêtres, recouvrement, saturation de
  budgets : mêmes garanties que [SCHEDULES](SCHEDULES.md#preuves-e2e-attendues) ;
- captures desktop et mobile inspectées : liste vide, erreur, longs noms, aperçu,
  historique, focus clavier ; manuel compilé et seed à jour.
