# Cycles réels des deux routes d’invocation

Complément de SLS-066, après les trois déclencheurs sans perturbation qualifiés
dans [la preuve de garde](evidence/invocation-route-guard-dev-2026-11-08.json).
L’autorisation de CLAUDE_PROJECT porte sur les seuls serverless.lelabs.tech et
functions.lelabs.tech d’infra-serverless. Ce contrat n’élargit pas ce périmètre.

## Fixture et préconditions

Un client E2E original crée un namespace invocation-route-cycles suivi de huit
chiffres hexadécimaux, un service et une fonction route-entry. La description
des parents porte un nonce complet de propriété. Les identités sont conservées
immédiatement ; une récupération après réponse perdue exige ce nonce et le
nom exact, jamais un autre objet au nom voisin.

Le client publie le handler original invocation-addresses.cjs avec son fichier
revision.json par la véritable CLI et un jeton Create/Update/Read du seul service.
Un second jeton Read limité à la fonction effectue les lectures et invocations.
Le manifeste conserve minScale zéro, maxScale un et idle_seconds un : attendre
l’absence réelle d’instance avant chaque perturbation, sans invocation active.
Le catalogue global doit ne contenir que la fonction possédée à cette frontière.
Pas de nouveau code applicatif, variable de cellule, secret, build ou mode clair.

Vérifier les deux résolutions et HTTPS réels, la révision publiée, les deux
routes à 18090 TLS et la garde prête avec identité/naissance reconnues avant
chaque cycle. Utiliser le relais local normal et son paramètre serveur fixe.
Les lignes officielles sont rafraîchies par le chemin suggestions normal et
relues par l’API existante ; aucun fichier ni résultat n’est remplacé.

## Cinq groupes E2E sérialisés

1. Deux domaines : pages API de taille un aux offsets zéro et un, total deux,
   même empreinte et révision, domaines distincts. Invoquer réellement le code
   Docker depuis chacune des deux URL émises et contrôler sa révision de fixture.
2. Détour du seul alias vers 18091, avec propriétaire principal vivant : le
   catalogue HTTPS canonique ne garde que son domaine, le vrai HTTPS de l’alias
   échoue vers le port sans application. Demander la restauration explicite,
   confirmer la fin de garde, relire deux domaines puis invoquer l’alias.
3. Un pilote distinct arme sa propre garde puis détourne seulement l’alias.
   Il annonce la mutation complètement confirmée avant d’attendre. Le parent
   recoupe le catalogue réduit, tue ce seul pilote par SIGKILL et exige une
   restauration owner_gone sans restore.request, avec fin de garde et invocation
   de l’alias. Ne tuer aucun processus pendant une mutation de console inconnue.
4. Retirer l’alias par DELETE normal, constater son absence du registre et du
   catalogue canonique, conserver son DNS. Le rétablir par POST normal ; exiger
   un nouvel identifiant connu de la garde et la même révision de fonction.
   Restaurer explicitement puis invoquer l’alias. La canonique n’est jamais retirée.
5. Détourner les deux routes vers 18091 sous garde. Le client opérateur existant
   invocation-url-host.py consulte le vrai contrôle en HTTP local 18090, avec
   jeton Read sur stdin SSH privée : source disponible, total zéro, items vides
   et révision conservée. Restaurer les deux routes, confirmer la fin de garde,
   retrouver deux domaines et invoquer Docker par les deux URL réelles.

Le cinquième groupe qualifie le catalogue vide de l’API locale réelle ; il ne
qualifie pas un affichage UI sur une connexion publique retenue. Ce dernier
parcours et le futur pilote pause/libération restent distincts. Deux domaines
suffisent à cette pagination API, sans qualifier la seconde page UI/CLI de cinq.

## Responsabilités et nettoyage

La garde existante sérialise ses actions ; chaque scénario conserve ses reçus,
identités, états avant/après et déclencheur réel. Une restauration explicite
de secours ne peut faire réussir le scénario de perte du pilote. Aucune mutation
n’est automatiquement rejouée sur erreur ou perte de réponse. Les issues
inconnues restent des erreurs avec relecture, pas des succès reconstruits.

Avant toute suppression de fixture, confirmer toutes les gardes terminées,
les deux routes restaurées et le HTTPS canonique sain. Sinon conserver les
ressources et le diagnostic pour reprise opérateur. Supprimer puis purger
uniquement la fonction possédée, attendre son reçu, puis supprimer les parents
et révoquer leurs jetons par les API. Le collecteur natif ajoute seulement ce
préfixe possédé à son contrôle existant, conserve les inventaires exacts et
recoupe fichiers, secrets vides, volumes, instances et réservations libérés.

Le rapport complet exige cinq groupes réussis, zéro skip, nettoyages confirmés
et sources/images identiques avant/après. Conserver séparément tout essai
interrompu. Les pannes propres du nouveau client restent à éprouver par leurs
scénarios réels ; ce contrat ne leur attribue aucune réussite anticipée.

## Résultats réels du 9 novembre

Les cinq groupes passent en série sur 203 sources et les mêmes images avant/après.
Sept appels utilisent les chaînes URL réellement émises et exécutent le handler
Docker attendu. Les quatre gardes sont terminées : trois reprises explicites
et une indépendante après SIGKILL du pilote. Le retrait/rétablissement donne
un nouvel identifiant de route à l’alias, tandis que la canonique conserve le sien.
Les deux lignes finales ciblent 18090 TLS ; services, démarrages et configuration
officielle restent inchangés. La fonction est purgée dans son namespace, avec
reçu de stockage et absences physiques recoupés.

La [preuve](evidence/invocation-route-cycles-dev-2026-11-09.json) distingue les
cinq succès de la première collecte physique interrompue. Celle-ci comparait
strictement des nanosecondes Python à leur représentation après JSON JavaScript :
dix-huit seuls champs started_at_ns/finished_at_ns dépassent la précision entière
exacte de JavaScript. Le collecteur recoupe leur même valeur numérique et borne
l’écart à un pas de représentation ; tous les autres champs restent identiques.
Les huit fichiers natifs de garde sont archivés byte pour byte avec leurs SHA,
et restent l’autorité pour les nanosecondes. Aucune donnée applicative, réponse,
route ou résultat de scénario n’est remplacé. La seconde collecte est en lecture
seule ; les cinq scénarios ne sont pas artificiellement rejoués ou requalifiés.

Le catalogue vide est prouvé sur le vrai HTTP local, pas encore dans le parcours
UI public retenu. Les six domaines UI/CLI et les pannes propres du nouveau pilote
restent ouverts dans SLS-066.
