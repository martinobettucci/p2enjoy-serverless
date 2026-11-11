# Rétention réelle des tirs planifiés

Contrat de preuve de [SLS-078](BACKLOG.md#sls-078), complément de
[SCHEDULES](SCHEDULES.md#réalisation-du-moteur-et-migration-009). DEV uniquement,
preuves sérielles, aucune date ni ligne métier fabriquée, aucune horloge remplacée.

## Capture authentique avant vieillissement

Le mode terminal-capture de schedule-recovery-operator.py reprend les précontrôles,
le traceur natif et la garde indépendante déjà qualifiés. Une seule fonction
vivante, dans scheduled-functions-<UUID court>, porte */5 * * * * ; données/cache
désactivés. Un vrai appel HTTP terminé avant le tir fournit le témoin non protégé.
Le traceur ne remplace aucun registre, tampon ou résultat système. Il suspend
le contrôle seulement lorsque les lectures natives confirment le tir exact
dispatched/non clos et son invocation succeeded, handler démarré, completed_at
renseigné. Le hash, les UUID, le créneau et les logs reçus sont recoupés.

Créer à cet instant une sauvegarde SQLite native depuis une connexion mode=ro,
sous l’identité propriétaire, dans un dossier privé de qualification-history.
Vérifier l’intégrité et le même prédicat dans la sauvegarde elle-même, ainsi que
le témoin HTTP terminal antérieur. Garder les dates réelles et calculer le premier
instant éligible à l’épreuve : max(completed_at des deux appels)+604800s+1s.
Détacher et reprendre immédiatement le contrôle, sans le tuer. La garde restitue
aussi sa santé en cas de perte du traceur ; aucune base originale n’est restaurée.
Comparer CID/image/démarrage et empreintes officielles avant/après ; joindre
le pilote et désarmer timer/service avant toute autre commande de preuve.

Après reprise, vérifier la clôture normale du même tir, sans nouvel appel. Copier
les artefacts immuables de cette installation dans le dossier privé avec inventaire
SHA avant/après ; un écart est un échec. Sauvegarder aussi le registre de stockage
au repos, sans bail ni volume de la fonction témoin. Puis archiver/purger réellement
la fixture par API et vérifier son absence physique. La sauvegarde de capture et
les artefacts restent conservés pour le vieillissement ; ils ne sont pas des
objets actifs de la plateforme et ne sont jamais publiés dans Git. Le rapport public
porte seulement identités de campagne, dates, états et empreintes sans secret.

## Épreuve après sept jours

Le replay devra employer une copie privée de la sauvegarde et des artefacts,
sur l’image immuable capturée. Il sera réalisé dans une fenêtre gardée exclusive :
contrôle habituel arrêté, originaux par identité conservés, zéro conteneur/réseau/
bail d’exécution de l’installation originale avant démarrage, agent sur registre
privé. Une simple deuxième base contre le Docker/registre actif est interdite :
l’installation-id cloné ferait viser les consommateurs originaux par recover.
Le pilote de replay et ses pannes seront spécifiés et qualifiés avant cet usage.

Le passage de rétention doit être observé avant la clôture du tir : témoin HTTP
ancien supprimé, source ancienne conservée tant que son tir reste non terminal,
puis clôture normale et source devenue éligible. La clôture attribue au tir une
nouvelle date réelle ; son propre délai de sept jours repart alors. Cette capture
ne prouve donc ni l’âge d’un tir déjà terminal, ni le plafond numérique.

## Autres preuves requises

Les bornes10000 des invocations et des tirs terminaux sont globales, pas par
fonction. Dépasser ces bornes exige de vrais appels et de vraies fenêtres sur
plusieurs fonctions ; chaque fonction doit rester individuellement sous10000
pour distinguer la portée globale. Les sources des tirs non clos restent hors
du comptage éligible des invocations. Les générations retirées et les tirs déjà
terminaux doivent aussi franchir sept jours réels. Leur préparation reste à
réaliser ; aucun résultat ne découle de la seule capture initiale.

SLS-078 reste[~] jusqu’à ces preuves, au critère adaptateur.7 et à sa régression.
