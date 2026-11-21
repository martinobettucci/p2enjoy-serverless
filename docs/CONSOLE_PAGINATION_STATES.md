# Pagination des lectures de console en erreur

Contrat de [SLS-113](BACKLOG.md#sls-113), découvert pendant le sixième passage SLS-078.
La fiche purgée titrée « Archives conservées » appartient déjà à
[SLS-075](BACKLOG.md#sls-075), dont le choix neutre « Archive de la fonction »
reste autoritatif. SLS-113 porte les paginations d’archives et d’observations
d’exécution ; aucun changement d’API,
de droits, de commande de stockage ou de rétention n’est impliqué.

## Constat et cause

Image 433da150, gel 9e1da704c230dcd05c414c4e1013fa882c8fda44,
run 833b57eff42c4b429d06a86161e5fc5b, phase storage-console-ui : 10 groupes réussis,
14 JPEG déclarés et ouverts. Rapport SHA
3f346779432b5dd2cd3e17a135ab44a4d27dd5ecb1e65777df381bfe816f37d3.
storage-ui-pagination-error.jpg,1440×1000,
SHA569351743565ed9243f8ce4b3822ad3b6f8fbe63b76e5f9921e69eeaf01ec7c3 :
cartes et total retirés pendant l’erreur mais « Page 1 sur 161 » antérieure
reste présentée sans indication de fraîcheur ; commandes grisées.
Dates source dans 1795299314559953009→1795299424106362162.

Cause lue : web/src/storage.jsx, composant Archives. Le début de lecture et
le catch conservent state.data ; cartes/total sont dans la branche réussie,
mais la navigation utilise encore cet ancien total en dehors de cette branche.
StorageDetail et son titre sont la cause distincte de SLS-075 ; ne pas les attribuer à SLS-113.
Le client archive() et son assertion de focus encodent aujourd’hui ce titre
erroné ; SLS-075 devra corriger ces attentes sans fermer ses critères sur ces images.

## Autre occurrence recoupée dans les observations

La capture execution-ui-network-error.jpg,1440×1000,
SHA7a7ea8d638e499db76a41877d6fff251d041a1d8ac30e4bd858f9342d7321d85,
run 833b57eff42c4b429d06a86161e5fc5b/038-execution-ui-result, a été ouverte par
le principal : erreur de connexion, aucune carte, « Page 2 sur 2 » et Précédente
active. Ce n’est pas un ancien nombre qualifié comme tel.

Cause lue dans web/src/observations.jsx : ExecutionObservations vide data mais
conserve total pendant lecture/erreur ; sa navigation est rendue hors branche
réussie depuis ce total. Les boutons ne tiennent pas compte de l’erreur. Le
composant est partagé entre Instances et Invocations. Le constat visuel porte
sur Instances ; la correction et ses E2E couvriront explicitement les deux.
Le rapport execution-ui SHA dce27526c92b7b0d491e7b8fd806586c9894a45a3fe873e7f5a120d0973df84c
est celui des 12 groupes et 12 images déjà recoupés, sans nouvelle prise ni groupe ajouté.

## Décision avant code

Retirer la navigation chiffrée pendant chargement et erreur, en la rendant
uniquement avec les données lues avec succès. Le catalogue global et ses
sélecteurs parents utilisent déjà ce principe ; les adresses retirent aussi
les anciennes données. La liste d’observations qui conserve un ancien total
est corrigée selon le même invariant, pas recopiée comme précédent. Les archives et observations sont les deux périmètres instruits. Toute autre
vue non instruite reste hors portée ; un défaut distinct rejoint son unité avant code.

Conserver le filtre et la page demandée en mémoire pour Réessayer et garder le recalage
de page vide existant. Ne jamais présenter l’inconnu comme un zéro actuel.
La navigation revient avec le nombre réellement renvoyé. Les titres H1 des archives et H2 des observations restent montés :
la restitution de focus après changement de page/filtre et après erreur garde
une cible existante ; le bouton de relecture reste utilisable au clavier.
L’option de commandes grises avec un résumé indisponible est écartée ici au
profit du précédent du catalogue, plus simple et sans nombre ambigu.

## Preuves requises

Depuis l’accueil et le SSO réel, garder les 10 groupes storage-console-ui,
leurs vrais objets, volumes et fautes. Groupe 10 : le mode natif du contexte
navigateur passe offline via setOffline(true), puis Suivante provoque un vrai
fetch refusé. Aucun route/fulfill ni serveur de substitution. Vérifier absence
des anciennes cartes, du total et de navigation chiffrée, filtre conservé et
focus sur un élément monté. Capturer l’erreur desktop/mobile. Revenir online,
Réessayer et comparer page/total/identifiants à la réponse API réelle offset 5,
sans fixer 161 ; capturer la reprise responsive. La latence CDP de 10 s du groupe 5
reste une faute distincte inchangée ; elle ne remplace pas cette panne.

Le client execution-ui garde ses 12 groupes et ses fautes natives : lecture en
cours puis erreur réelle du contexte navigateur, reprise et pagination sur les
données API. Ajouter les assertions/captures desktop/mobile qui discriminent
le compteur périmé dans Instances et Invocations ; aucun précédent bouton ne
reste actionnable sur un total non confirmé. La sélection d’une invocation par
UUID et son retour à la liste conservent leur comportement et leurs droits.

SLS-075 garde ses tests propres : titre neutre/badge Conservée, Purge en cours et
Purgée à observer réellement, parents et reçu consultables ; ne pas revendiquer
un état transitoire non capturé. Actualiser archive() et le focus après purge,
conserver le même H2 référencé et compléter desktop/mobile. Toute coordination
d’une livraison de console commune conserve les critères et porteurs distincts,
sans compter deux fois un groupe partagé.

Pour SLS-113 : 10 groupes de stockage, 12 d’exécution et 25 communs, sur le
code réellement déployé et les sources synchronisées,
sans mock, skip ou rejeu. Tous les JPEG frais ouverts individuellement, manuel
canonique servi, backend/web et nettoyages/ressources/configuration/référence/
5 982 originaux recoupés. Le compte reste de 47 si les discriminants enrichissent les
groupes existants ; un groupe distinct serait annoncé avant exécution.
SLS-113 reste non implémentée ; le passage SLS-078 figé conserve son époque et ne qualifie
aucune de ces corrections absentes ni la clôture globale SLS-095.
