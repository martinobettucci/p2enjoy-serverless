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
