# Raccordement du parcours de publication à la facette des versions

Contrat de [SLS-107](BACKLOG.md#sls-107), préalable à106 et078.
Constat réel du21novembre2026 au gel0a5e020,449sources et imageb452 :
publication-ui échoue dès son premier groupe par timeout du texte exact
« Aucune révision publiée. ». Le parcours courant expose les versions par hash
selon FUNCTION_VERSION_EXECUTION, alors que ce client garde des attentes
historiques. Le rapport et son diagnostic sont conservés ; aucun défaut produit
n’est déduit du seul timeout. Cleanup=true et native0/5982 sont recoupés.

## Diagnostic avant correction

Lire le contrat de publication et les versions, puis rapprocher chaque groupe
du client de ses widgets, libellés et comportements réellement servis. Conserver
la reproduction initiale et établir la correspondance des21groupes : création
et vide, formulaire/confirmation, publication pilote, version/hash/promotion,
refus, pertes et reprises, détail, focus, mobile, confidentialité et nettoyage.
Nommer les attentes périmées ; persister la décision avant le code correspondant.
Ne pas modifier le produit pour rétablir une ancienne terminologie du banc.

## Résultat exigé

Le parcours entre par l’accueil avec le vrai SSO, crée ses objets par la console,
uploade réellement ses ZIP et agit sur les confirmations et widgets existants.
Les règles en vigueur prévalent : upload pilote, promotion explicite, liste par
hash et UUID conservés dans les détails. Aucun groupe supprimé ou rendu vide,
aucune action UI remplacée par une mutation API pour contourner son interface.
Les préparations API déjà prescrites restent des préparations identifiées.

Tous les21groupes et25communs doivent passer sur le code réellement déployé,
avec captures fraîches desktop/mobile ouvertes individuellement, source/rendu du
manuel recoupés et code/volumes/parents purgés par les API. Le helper106 et son
lecteur natif sont conservés ;5982artefacts antérieurs, référence et configuration
restent intacts. Les observations de panne sont persistées avant assertions.
Une incohérence produit découverte est inscrite au backlog avant son traitement.

107 ne ferme ni105, ni106, ni la campagne complète078. Après sa livraison,
106 peut terminer ses79groupes ;078 doit encore terminer son assemblage entier.

## Décision de raccordement du21novembre2026

Les sources servies `web/src/publications.jsx` et
`control/app/function_versions.py` recoupent le contrat actuel
FUNCTION_VERSION_EXECUTION : publication pilote, catalogue par hash incluant
les tombstones deleted, promotion distincte, nettoyage asynchrone. Ce contrat
prime les formulations historiques063 encore présentes dans CONSOLE_PUBLICATION.
On précise ces dernières avant le client ; le produit ne change pas.

Le client conserve séparément UUID de tentative, UUID de révision canonique et
hash. Un réupload de A peut réutiliser son alias initial : candidate.id ne vaut
pas nécessairement revision_id. Le suivi expose ces deux identités dans des
champs distincts ; la région de code expose la cible par hash. Un helper de
lecture retrouvera la page de la carte par le catalogue réel, sans mutation API.

Correspondance des21groupes, dans leur ordre conservé :

| Groupe | Parcours et preuve actuels |
| --- | --- |
| 1 | Création UI et navigation normales ; « Aucune version publiée. » et vide des tentatives. |
| 2 | Vrais422/409 ; ZIP/handler conservés ; « Revenir à la saisie » avant correction ou nouvelle confirmation. |
| 3 | A pilote, hash/SHA/alias et focus ; défaut absent et appel sans tag refusé, appel épinglé réussi ; promotion UI puis appel sans tag. |
| 4 | ZIP invalide et import réel refusés, logs expurgés, cible A conservée. |
| 5 | B pilote invoqué par hash, défaut A intact ; promotion B puis retour A par confirmations UI, configuration/secrets/données courants. |
| 6 | Vrais logs tronqués, mobile/clavier ; cible A conservée après upload, appel A. |
| 7 | Annulation de suppression B, suppression confirmée ; carte Supprimée conservée, appels B refusés ; retrait de A exige choix explicite dans sa modale, annulée. |
| 8 | Bascule réelle vers un autre hash puis réponse de promotion A perdue après commit ; retour sans rejeu et invocation A. |
| 9 | Réponse DELETE hash perdue ; tombstone relu sans second DELETE, cible A intacte. |
| 10 | Même faute physique et pertes SIGKILL/arrêt du helper ; identité/inode/mode/fichiers et garde restaurés. |
| 11 | Même EACCES réel ; DELETE hash200 avec cleanup_pending, notice « Version retirée. Nettoyage physique en attente. », carte Supprimée ; lectures fonction/catalogue après décision, un seul DELETE ; octets conservés puis effacés par maintenance ; nouvel upload pilote invoqué puis promotion/retour A explicites. |
| 12 | Déploiement complet modifiant quota avec réupload A ;503 réel de confirmation de stockage, candidat published et alias A réutilisé, cible A inchangée ; reprise et invocation vérifiées. |
| 13 | Validation réelle en cours, états liste/suivi cohérents puis conflit409 ; A et modification concurrente conservés. |
| 14 | Rechargement pendant validation, même candidat, aucune préparation/upload supplémentaire ; issue terminale observée et pointeur A invariant, hash pilote si publié. |
| 15 | Préparation API prescrite, sélection dans liste puis abandon UI. |
| 16 | Catalogue hash >5 : pages serveur distinctes ; suppression d’un hash inactif page2, total et page conservés car tombstone, focus titre, retour page1 ; pagination des tentatives distincte. |
| 17 | Vraie panne réseau, reprise exacte de page, promotion UI d’un hash disponible inactif ; actualisation hors ligne et session absente refusées, reconnexion. |
| 18 | Réponse de préparation perdue au transport Chromium, même UUID retrouvé sans PUT ni second POST, abandon UI. |
| 19 | UUID absent, erreur explicite sans nouvelle préparation, fermeture du suivi. |
| 20 | Candidat étranger refusé sans détails/actions ni modification. |
| 21 | Mobile390px, long nom, métadonnées hash/alias/SHA, confirmations au clavier, retour du focus, aucune fuite dans rendu/stockage navigateur. |

Deux attentes impossibles sont remplacées par leurs discriminants actuels,
sans retirer de groupe : le503 historique de suppression de révision appartient
à l’ancienne route UUID ; la route hash actuelle acquitte la décision200 et
annonce explicitement le nettoyage en attente. Le503 de stockage du groupe12
reste exigé. Le catalogue garde les hashes supprimés : supprimer sa sixième
entrée ne peut pas le ramener à une page. Le groupe16 prouve donc maintien
du total, état deleted, stabilité de page, focus et aller-retour sans doublon.
Les artefacts physiques et les gardes restent éprouvés exactement sous faute.

Qualification prévue :21groupes de publication puis8manuel,8public et9connexion,
en série avec vrai SSO, soit46groupes. Les sources indexées comprennent ce
contrat ; les captures et reçus natifs sont conservés avant toute réécriture.

## Premier essai107 : synchronisation de page

Le gel4f5b886 passe15groupes puis échoue dans16 ;46groupes non qualifiés.
Rapport exact29f9e1b571ce5b3dde885024c89e324210b3d1706b1eb24579c0563fc7a2852c,
checkpoint6887328d. Les deux réuploads A observés distinguent bien tentative
et alias ; le dernier est code_changed=false. L’échec compare les3hashes
de page2 aux5hashes attendus page1, après le retour par Précédente.
Nettoyage public sans erreur ; lecteur natif après échec completed, counts0,
5982originaux et même installation/configuration.

La lecture de CodePublications explique l’attente insuffisante du client :
change versions fixe revisionPage avant que son effet ne mette loading, tandis
que Pages utilise revisionPage et les cartes utilisent encore state.data.
Le compteur peut donc annoncer la page demandée avant ses cartes. ready(), qui
attend seulement l’absence de loading et un bouton actif, ne distingue pas cet
intervalle. Ce constat n’établit pas un défaut produit permanent.

Décision avant correction : le groupe16 attend une observation cohérente du
numéro de page ET des hashes exacts attendus de son GET serveur, avec échéance
finie et diagnostic persisté ; il compare ensuite explicitement les deux listes.
Il conserve les clics réels, cinq cartes/page, tombstone, total, focus et
contrôles de doublon. Aucun délai arbitraire ni baisse du nombre de cartes.
Les46groupes seront rejoués au nouveau gel ; cet essai incomplet reste distinct.
