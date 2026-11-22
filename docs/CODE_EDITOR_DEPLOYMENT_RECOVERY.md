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

## Diagnostic et choix de reprise avant code

La [preuve négative](evidence/editor-adoption-image-preparation-failed-dev-2026-11-22.json)
conserve le transport initial terminé et le diagnostic en lecture seule au gel
bc4fe1b. L’inspection de l’image433 dit actuellement No such image ; candidate046
et tag p2enjoy-control:dev sont disponibles. Le contrôlea9/image433 reste sain
au même démarrage, comme la référenceaf6. Deux sauvegardes intègres sous1001/0600,
38backend/quatreweb/notes/configuration/budgets et5982originaux inchangés.

La préparation employait l’empreinte d’un conteneur sans vérifier que le magasin
Docker pouvait encore fournir cette image. Ce prérequis est maintenant absent.
Le stderr interne du premier tag n’a pas été imprimé : ne pas affirmer l’identité
de ce message manquant avec celui du diagnostic actuel, ni expliquer sans preuve
la disparition de l’enregistrement Docker. Aucune instruction FORGE n’est requise
pour disposer ici d’une image de retour valide.

Décision : construire dans un contexte privé original de63fichiers, avec un
nouveau UUID/tag propre, l’ancienne application actuellement servie. Le Dockerfile
et ses bases verrouillées par digest restent ceux du dépôt. Les seuls fichiers
à remplacer dans cette copie proviennent du commit4dcd24b :

| Fichier | SHA historique exigé |
| --- | --- |
| web/src/code-editor.jsx | ca20fbd1cdba4a196dfc02637745f06469612aa8c888567292d8ac6a87cfdf88 |
| docs/manual.md | 8a50ffa0431e70cfd8162f5d94f049ef46afb1a65c55bb53630b082d60bb3bd2 |

Les autres entrées Docker n’ont pas changé depuis4d ; les38backend courants
correspondent exactement à ceux du contrôle433. Ne remplacer aucun module de
stockage par une version plus ancienne : le précédent historique de reconstruction
portait sur une autre image et un autre changement. Le contexte contient neuf
fichiers fixes (Dockerfile/ignore/requirements/function_code_hash/manual et quatre
entrées web),27modules app, dix migrations,16sources web et le favicon. Inventaire
exact, SHA/types/propriétaires/modes recoupés ; aucun fichier officiel/secret,
base ou volume n’entre dans ce contexte. Sources courantes laissées intactes.

Inspecter la vraie image reconstruite dans un conteneur readonly sans réseau,
capacités ni privilège, borné128Mio/0,25CPU/32PID, retiré puis joint. Elle doit
porter exactement les38SHA backend et les quatre ressources web du live :
favicon7d98024b, index7c50faae, CSS2ec633a8, JS27715dab (index-C9YIqRyw.js).
Comparer l’environnement par défaut à la candidate046, sans exporter ses valeurs ;
le build depuis fichiers suivis ne copie pas l’environnement injecté du conteneur.
Le tag candidat046 et les deux services restent inchangés pendant cette construction.

Avant la nouvelle bascule, exiger disponibilité du tag et du digest de cette
image de retour, recouper encore le live et conserver sa propre identité. Si son
digest diffère de433, le qualifier d’image reconstruite équivalente par ses
octets applicatifs, jamais d’empreinte originale retrouvée. L’opérateur suivant
retiendra ce digest comme retour, avec son UUID d’opération neuf ; il conserve
les gardes de conteneur, configuration et délais décidées pour115. Une nouvelle
sauvegarde native précède la bascule. Ni le premier tag raté ni ses sauvegardes
ne sont réutilisés ou retirés.

## Reconstruction réelle constatée —22novembre2026

Au gel bf4ba5b/463sources, le contexte privé de63fichiers produit l’image de
retour `sha256:aa21417933694da6ac9789140f9567dfddc9e898aad1b0512d090ec8fc1fd5a1`.
Les38backend et quatre ressources web sont exactement ceux du live433 et du
diagnostic, y compris les noms et SHA complets. Les six attributs de configuration
d’image (dont Env/Cmd/Entrypoint) correspondent à046, sans valeur exportée.
Le conteneur d’inspection est retiré, son client termine sortie0 et est joint.
Tag candidat046, contrôlea9/433, référenceaf6, configuration et5982originaux
restent inchangés. Cette construction ajoute zéro groupe fonctionnel.

La nouvelle bascule exigera explicitement046 comme candidate etaa214179 comme
retour validé. Elle n’essaie plus de taguer le digest433 absent ; elle recoupe
tag+digest du retour disponible et ses octets applicatifs contre le live avant
les nouvelles sauvegardes. Le retour éventuel recrée l’application ancienne
avec aa214179, sans prétendre restaurer l’ancien digest433. Nouvel UUID,
étiquette propre, identités complètes, bornes et fichiers officiels restent requis.
116 et115 restent ouverts jusqu’à bascule et36groupes qualifiés.

La nouvelle bascule5c106957 est ensuite terminée sortie0 et jointe : API046/CIDe219f789,
référence inchangée, sauvegardes contrôle/registre intègres, tables/migrations,
fichiers officiels, budgets et5982originaux conservés. Tag et digestaa sont
recoupés avant sauvegardes et nouveau tag propre. Le contenu embarqué046 est
vérifié après démarrage ; aucune branche de retour n’est exécutée ni qualifiée
par ce nominal. La campagne36 reste requise avant clôture116/115.

## Retour au fichier et attentes UI qualifiés —22novembre2026

La [preuve36](evidence/code-editor-adoption-focus-dev-2026-11-22.json) clôt **SLS-115 et SLS-116** : onze groupes ciblés puis
25communs frais sur463sources `ce8540a`, image04604089/CIDe219f789. Les68entrées
produit sont identiques au buildd028 ; les gels ultérieurs changent le pin du
client et les contrats de preuve. Les62captures sont ouvertes individuellement :
40JPEG ciblés,16JPEG du manuel déclarés et six PNG complémentaires non déclarés.

Les quatre adoptions garder/remplacer en1440/390px donnent huit mesures sur le
textarea connecté et focalisé avant/après réponse tardive. Huit variantes de
lecture/existence/absence focalisent le h2 courant ; version UI/serveur, texte/SHA,
chemin et lecture seule sont recoupés, sans PUT implicite. Sauvegarde, surface,
adoption et abandon écartent les anciens200. Focus volontaire, recalage détaillé
5+2 avec origine conservée, vrais404/429 puis reprise sont recoupés.18gardes et
24lecteurs sont joints ; seize instantanés tardifs sont conservés.

Neuf invocations distinctes sont succeeded/handler_started1/HTTP200. Fonction,
jeton et deux parents retirés ; purge physique du seul UUID, ressources Docker/
réseaux/canaux/backings/baux et réservations recoupées.38backend/quatreweb HTTPS
no-store, dix migrations/intégrités/FK, notes, budgets, configuration/référence et
5982originaux sont conservés. Manuel canonique servi :18chapitres/74paragraphes,
SHA8d2434cff30235f0a6849f312764432581afb78659b71a328d51ee5416365d6b.

Les prérequis build046, reconstruction de retouraa214179 et bascule5c106957 sont
liés aux reçus exacts, zéro groupe ajouté. Les63entrées du retour reproduisent
38backend/quatreweb du live433, avec deux seules copies Git4d ; l’image de retour
reste distincte du digest433 absent. Sauvegardes contrôle/registre sous1001,
référenceaf6 et originaux conservés. Le nominal n’exécute pas de rollback de
bascule ni de nouvelles fautes de gardien. Les deux échecs préliminaires restent
séparés et exclus, zéro groupe ajouté. Leurs limites de diagnostic sont conservées.

Les images corroborent lisibilité et contours ; DOM/HTTP/FD/handlers/effets sont
portés par les rapports natifs. Certaines vues mobiles ne cadrent pas le texte
adopté et le nouveau passage du manuel n’est pas cadré spécifiquement. Les
assertions vérifient le contenu canonique rendu ; aucun texte caché ou paragraphe
supplémentaire n’est déduit des seules images.070 conserve ses critères de
persistance après redémarrage et d’interruption de publication à qualifier.
