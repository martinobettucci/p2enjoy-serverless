# Manuel d’usage dans la console

Contrat SLS-062, implémenté et vérifié le 7 novembre 2026 sur le SPARK DEV.
[Preuve](evidence/manual-console-dev-2026-11-07.json) : 48 groupes réels, dont
huit propres au manuel, zéro échec/skip et 33 captures relues.

## Source et maintenance

`docs/manual.md` est l’unique source éditoriale du manuel d’usage. Chaque évolution
fonctionnelle met à jour ses explications et procédures dans le même changement.
Le build de la console lit ce fichier directement : aucune copie éditable n’est
maintenue dans `web/`. Une modification du manuel reconstruit les ressources web
de l’image, dont la preuve recoupe l’empreinte SHA256 du document source.

Le guide décrit les opérations disponibles et leurs limites, avec des mots et
commandes utilisables. Les références de chantier (backlog, preuves) appartiennent
aux documents de développement. Les liens du guide sont des ancres de chapitre ou
des URL HTTPS explicites ; un lien relatif vers le dépôt fait échouer le build.

## Parcours et présentation

Après connexion, la navigation principale propose **Manuel d’usage**, destination
`/console/manual`. Le lien courant est marqué uniquement sur la bonne destination.
La page conserve la navigation, propose un sommaire de chapitres et rend titres,
paragraphes, emphases, code et tableaux. Les liens de sommaire amènent le focus
au titre du chapitre ; l’ancre reste partageable et fonctionne au rechargement,
après résolution de la session. Un lien permet de revenir au sommaire.

La lecture utilise une largeur bornée à 72 caractères environ. Le sommaire est
adjacent sur desktop et précède le contenu sous 1024 px. Les commandes longues
reviennent à la ligne ; aucun défilement horizontal de page. Les styles réutilisent
les tokens du produit. Aucune modale, saisie ou recherche artificielle n’est ajoutée.

La page suit la session de console existante. Le contenu documentaire, dépourvu
de données privées, est embarqué dans les ressources publiques de l’application ;
cette page n’est pas une barrière de confidentialité du texte.

## Construction

`markdown-it` 15.0.3, licence MIT, est une dépendance verrouillée de construction
uniquement. Son parseur standard évite de maintenir un dialecte Markdown maison.
Le HTML brut est désactivé ; seuls les liens HTTPS ou ancres locales sont acceptés.
Les identifiants des chapitres sont dérivés de leurs titres, sans accents, avec
détection des doublons. Le document doit comporter un titre et des chapitres.
Le parseur n’est pas livré au navigateur. Le contexte Docker inclut explicitement
ce seul document et la configuration Vite, sans ouvrir l’ensemble des docs.

## Preuves attendues

Depuis l’accueil réel et la session SSO : navigation clavier et souris, sommaire,
focus, ancres après rechargement, retour aux namespaces, tableau des droits,
commandes et texte intégral. Comparer l’empreinte source à celle de la vue déployée,
et tous les chapitres/paragraphes au document. Vérifier le menu mobile, desktop,
tablette, largeur de 390 px et agrandissement mesuré du corps de texte à 200 % ;
ce dernier contrôle ne prétend pas mesurer le zoom global du navigateur.
Inspecter les captures. Après retrait réel
des cookies puis rechargement, la page revient à la connexion. Aucun mock/skip.
Rejouer séquentiellement les parcours publics, de connexion, de gestion et de
consultation, affectés par la navigation commune. Les rapports identifient sources,
image et résultat de chaque groupe ; les contrôles de dépendances restent distincts
des preuves fonctionnelles.

## Concordance rétablie avec009

SLS-096 est corrigée le10 novembre2026 avec la reconstruction du contrôle et du
manuel : [preuve](evidence/schedules-checkpoint-dev-2026-11-10.json). Huit groupes
du manuel passent sur l'image b9ad872a,16 chapitres et56 paragraphes comparés
intégralement, empreinte source égale au guide servi. Les16 captures du guide
sont inspectées sur desktop, mobile, tablette et corps agrandi. Chaque nouvelle
modification du manuel doit à nouveau reconstruire/déployer la console et
rejouer cette concordance dans sa propre livraison.
