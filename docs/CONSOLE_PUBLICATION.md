# Publication du code dans la console

Contrat SLS-063, implémenté et vérifié sur le SPARK DEV le 7 novembre 2026.
Complète [DEPLOYMENT](DEPLOYMENT.md) et [CONTROL](CONTROL.md).
La [preuve finale](evidence/publication-console-dev-2026-11-07.json) recoupe
18 campagnes en série, 312 groupes réels et 54 captures inspectées, sans échec
ni test ignoré. Les deux incohérences de lecture sont corrigées et requalifiées.

## Parcours et conservation

La fiche de fonction ajoute la facette partageable **Code et révisions**.
Elle affiche la révision active, ses métadonnées, les tentatives de publication
et les révisions conservées. Une fonction sans code affiche un état vide et
l’action **Publier une archive**. Le formulaire demande un ZIP local et le
handler, initialisé avec la valeur courante. Le récapitulatif confirme le nom
de fonction, l’archive et le handler avant toute préparation.

Cette publication conserve les ressources, variables, secrets, volumes et
événements courants. Le serveur capture ces valeurs sous le verrou qui prépare
le candidat ; le navigateur ne reçoit ni ne ressaisit les valeurs des secrets.
Seul le handler peut changer dans ce parcours. Le manifeste complet reste
déployable par l’adaptateur. Les événements d’un brouillon reçoivent l’endpoint
implicite déjà défini par DEPLOYMENT.

Les trois opérations publiques ajoutées sont :

- `POST /api/functions/{id}/code-deployments`, corps strict
  `{handler, deployment_id: UUID}` et `If-Match` obligatoire. Create pour la
  première révision, Update ensuite. Le serveur construit le payload complet
  à partir de la fonction et de sa révision active, puis applique les mêmes
  droits, versions, limites, chiffrement et audit que la préparation complète.
  Réponse 201 : candidat public. Un UUID déjà utilisé est refusé à 409, sans
  rejeu ni remplacement, même pour le même contenu.
- `GET /api/functions/{id}/deployments`, réservé à la session administrateur,
  `limit` 1–100 (20 par défaut), `offset` 0–10000. Réponse `{items,total}`
  cohérente, tri date décroissante puis UUID. La projection est identique à
  GET du candidat ; aucun champ de configuration n’est exposé. Les diagnostics
  des autres créateurs ne deviennent pas accessibles aux jetons de service.
- `DELETE /api/deployments/{id}` abandonne uniquement un candidat `prepared`.
  Créateur encore autorisé avec son droit initial, ou admin ; revérification
  en transaction. Passage à `failed`, code `candidate_abandoned`, chiffrement
  temporaire effacé, date de fin et audit. Tout autre état donne 409. Une course
  avec l’admission de l’upload a un seul gagnant. Cette opération ne vérifie pas
  les anciennes versions de configuration, afin de libérer aussi un candidat
  devenu périmé après modification de la fonction.

Le schéma reste inchangé. La préparation complète utilisée par la CLI conserve
son comportement de remplacement intégral. Les UUID sont normalisés par le
modèle serveur ; aucun chemin client arbitraire n’est accepté.

## Suivi et réponses perdues

Le navigateur crée l’UUID avant le POST et le conserve dans l’adresse
`/console/functions/{id}/code?deployment=UUID`. Les valeurs de configuration,
le contenu du ZIP et les jetons ne sont pas conservés dans le stockage web.
La consultation de cet UUID est possible même si la réponse de préparation
est perdue. Une absence 404 est affichée sans préparer automatiquement un
autre candidat. Un UUID d’une autre fonction n’est pas associé à cet écran.

Après préparation, le navigateur envoie le vrai ZIP par le PUT existant.
L’interface présente les états serveur, sans pourcentage inventé, et observe
le candidat en série pendant l’envoi/validation. Les erreurs de lecture sont
visibles et permettent de relire. Fermer ou recharger la page peut interrompre
l’envoi ; cela ne promet ni annulation serveur ni reprise d’octets. La nouvelle
page consulte le même candidat et attend son issue, sans renvoyer le ZIP.

Un candidat préparé peut être abandonné explicitement. Pour renvoyer une
archive après un refus d’admission, on abandonne le candidat puis prépare une
nouvelle tentative. Une réponse d’upload perdue impose de relire candidat,
fonction et historique avant une nouvelle action. Un état publié avec une
opération de stockage en attente est annoncé comme enregistré, confirmation
en attente ; il n’est pas présenté comme une ancienne version conservée.

Dans un cycle de consultation, le candidat suivi est lu après la liste. Son
observation plus récente remplace aussi sa ligne dans cette liste : le même
candidat ne porte pas deux états différents dans l’écran. Une actualisation
ou sélection explicite efface les messages de succès d’une action antérieure,
afin de ne pas les présenter comme confirmation du nouvel état consulté.

## Révisions

La liste conserve les identifiants complets, handler/runtime, dates, SHA256,
taille stockée et événements dans des détails de lecture. Les vingt révisions
maximum sont chargées ensemble puis affichées par pages de cinq ; le pointeur
actif reste identifiable même lorsqu’il vise une ancienne page. Les tentatives
sont paginées côté serveur par cinq, avec leur total.

**Activer cette révision** utilise le rollback existant et la version lue de la
fonction. La confirmation rappelle que les réglages, variables, secrets et
volumes courants sont conservés. **Supprimer cette révision** demande une
confirmation ; l’active ne propose pas cette action. Le serveur refuse aussi
les révisions utilisées par une instance. La dernière page se recale après
suppression. Un conflit conserve le diagnostic et invite à actualiser.

Après une réponse perdue ou un 503 de mutation, l’écran relit l’état avant de
permettre une nouvelle mutation. Une suppression peut déjà être enregistrée
alors que son nettoyage physique attend : la disparition de l’historique ne
prouve pas à elle seule la fin de ce nettoyage.

## Preuves requises

Les preuves passent par le contrôle et les conteneurs réels du SPARK DEV :
droits Create/Update/Read, portée, révocation, CSRF, doublon d’UUID, versions,
conservation effective des secrets/configurations/événements, abandon et course
contre upload. Les routes complètes et l’adaptateur sont rejoués en régression.

Depuis l’entrée normale de console : création, publication via input file,
validation réelle, archive invalide, import en erreur et logs expurgés, conflit
réel, rechargement pendant son propre upload, consultation du même candidat,
publication A/B puis activation A effectivement invoquée, suppression inactive,
pagination, refus d’autorisation, panne réseau réelle et reprise de lecture.
Captures inspectées sur ordinateur et mobile, focus/clavier, noms et logs longs.
Le manuel est mis à jour et sa concordance reconstruite est rejouée.

Les rapports frais et leurs sources/image sont recoupés. Le nettoyage rejoint
les requêtes, supprime uniquement les objets de campagne et recense les archives
de code conservées. Aucun mock, scénario ignoré ou succès conditionnel.

La clôture utilise `python3 -B e2e/execution-suite.py --scope publication` :
union séquentielle des campagnes du moteur et de la console, chaque campagne
commune exécutée une seule fois. Son rapport dédié conserve les empreintes
avant/après et la fraîcheur des rapports. Les scopes moteur et console restent
disponibles pour leurs qualifications propres.

### Nettoyage physique refusé

La preuve de 503 après suppression logique vise uniquement le répertoire parent
d’une révision inactive créée par la campagne, sans instance utilisatrice.
L’opérateur relève identité, mode et empreintes, puis retire temporairement
les permissions du parent ; le vrai contrôle doit observer EACCES avant toute
suppression de fichier. Aucun contenu ni état SQL n’est fabriqué.

Une garde systemd indépendante est armée avant le changement de mode. Elle
identifie le processus éphémère par PID, naissance et commande, le termine à
échéance pour empêcher une faute tardive, puis restaure uniquement l’inode
attendu. Le chemin ne peut être remplacé ni recréé. EOF, signal et exception
du pilote restaurent aussi le mode avant désarmement. Une première preuve tue
le pilote sous faute et attend la restauration par cette garde.

Le DELETE normal de console doit répondre 503 après son commit, afficher le
diagnostic et relire l’historique avant une nouvelle mutation. SQL et disque
doivent montrer la suppression logique avec octets toujours comptés et contenu
intact. Après restauration, la maintenance normale supprime les octets ; une
nouvelle publication réelle prouve la reprise. Le gestionnaire bloque les
uploads pendant cette faute : la campagne est seule et ne redémarre pas le
contrôle tant que la permission n’est pas restaurée.
