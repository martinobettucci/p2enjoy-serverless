# Image de retour avant la bascule de l’éditeur

Contrat de [SLS-116](BACKLOG.md#sls-116), découvert le22novembre2026 avant
la bascule du [correctif115](CODE_EDITOR_ADOPTION_FOCUS.md).

## Premier arrêt conservé

Gel7b2b541ee3dd99e9f542190b1105f110b62bd552, image candidate04604089.
Opérationa8c7f410d1284a6b8875f6e0dcff0166, transport local
editor-adoption-focus-deploy-1795317751919525181. Sortie1, transport joint,
fin distante confirmée, aucune expiration. Le programme s’arrête ligne48 sur
docker tag433da150 vers le tag de retour de cette opération. Compose n’est
pas encore appelé ; aucun groupe fonctionnel qualifié.

Le dossier possédé est qualification-history/before-editor-adoption-focus-
a8c7f410d1284a6b8875f6e0dcff0166. Lire sans mutation ses deux sauvegardes et son
complément Compose, leurs types/identités/propriétaires/modes/SHA/intégrités.
Conserver le programme, intention, transport, stdout/stderr exacts. Aucun
contenu de secret ou d’environnement de conteneur n’est exporté.

## Instruction avant correction

Lire les identités natives actuelles du contrôle433 et de la référenceaf6,
santé/démarrages et empreintes réellement embarquées/HTTPS. Interroger séparément
le magasin Docker pour l’ancienne empreinte, la candidate046 et le tag de retour
possédé. Une empreinte du conteneur n’est pas une preuve d’image disponible.
Conserver code/diagnostic de chaque consultation ; ne pas retenter le tag ou
la bascule pour obtenir un autre résultat. Repos/configuration/notes et5982
originaux sont recoupés. Aucun nettoyage des sauvegardes ni remplacement du tag
candidat ne découle de ce premier échec.

Une reconstruction éventuelle aura une décision, ses fichiers d’entrée explicites,
ses identités et son tag propres avant code. Elle devra reproduire les38backend
et les quatre ressources web du contrôle réel, sans copier ses secrets,
configuration injectée, bases ou volumes. Ne pas employer docker commit qui
embarquerait l’environnement du conteneur. Une image de retour reconstruite a
sa propre identité ; ne pas la présenter comme l’ancienne empreinte originale.
La référence de runtime des fonctions reste distincte et inchangée.

Le nouveau passage repart d’un nouveau gel et de nouveaux UUID après diagnostic
et précontrôle positif. Le premier arrêt et ses sauvegardes restent conservés,
zéro groupe ajouté. La qualification11+25 de115 reste entièrement requise.
