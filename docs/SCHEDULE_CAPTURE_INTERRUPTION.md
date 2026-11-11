# Interruption réelle du copieur de capture

Contrat complémentaire de [SLS-078.5](BACKLOG.md#sls-078) et de
[SCHEDULE_FIRING_VOLUME](SCHEDULE_FIRING_VOLUME.md#préparation-authentique-et-conservation).
Décision du11 novembre2026 avant code. Ce scénario vise le copieur de capture
initiale, distinct du chargement de replay déjà qualifié. DEV uniquement,
commandes en série, aucune ligne/date fabriquée, aucun mock ni serveur substitué.

## Préparer et exercer les deux voies du copieur

Ajouter le mode explicite --copy-loss au client schedule-firing-volume-capture.mjs.
Il conserve la vraie préparation SSO/API :16 fonctions,16 crons chacune, première
frontière UTC256 tirs/deux handlers réussis/254 refus, puis zéro consommateur.
Dans la même fenêtre gardée900s, exécuter d'abord une capture complète normale
et vérifier ses témoins, bases, artefacts, images et protections. Cette nouvelle
copie reste une preuve du nominal ; elle ne remplace pas la source6:15UTC déjà
scellée ni sa date d'éligibilité9:30UTC.

Puis solliciter la seule variante loss=control-backup de capture-firing-history.
Le module natif utilise la vraie API SQLite backup, pages=1 et son callback
progress, uniquement pour ce cas d'interruption. Au premier progrès avec des
pages restant à copier, écrire un reçu durable privé puis SIGSTOP du copieur.
Le callback ne modifie aucune donnée, date, registre ou résultat système.
La voie normale conserve sa copie complète sans callback de faute.

La sortie interrompue porte un nom distinct :
qualification-history/schedule-firing-capture-interrupted-<32hex de campagne>.
Elle est privée sous spark-docker0700 à ce stade, sans les protections finales
d'une capture terminée. Le reçu identifie campagne, fenêtre, témoins source,
pages restantes/totales, dossier et inode de sortie, PID/naissance du copieur et
de son wrapper timeout, identité du verrou hérité. Il est écrit dans ce dossier,
car le callback s'exécute sous le propriétaire SQLite. stdout ne sert pas de
signal : command() le conserve jusqu'à la fin du mutateur.

## Éprouver l'attente réelle de la garde

Le client doit constater le reçu ET l'arrêt réel du même PID avant de tuer le
pilote avec la primitive pidfd existante. Le copieur reste arrêté et conserve
le verrou ; son wrapper timeout est encore vivant. Déclencher explicitement
le vrai service de garde déjà armé, sans attendre900s. Le rapport nomme ce
déclenchement manuel ; il ne revendique pas l'expiration du timer900.

Pendant au moins deux secondes mesurées : service de garde vivant, pilote mort,
copieur arrêté, verrou indisponible à une autre ouverture, restored=false,
trois originaux conservés aux mêmes identités, remplacements encore aux chemins
officiels et contrôle original arrêté. Cette observation doit précéder toute
restitution. La copie en cours concerne une sortie privée, jamais CONTROL actif.

Tuer ensuite le copieur par SIGKILL avec pidfd/naissance exacts, avant son
timeout40s ; constater aussi la mort du wrapper par pidfd. Leur disparition
libère réellement les descripteurs, puis la garde indépendante doit rétablir
les originaux. Ne pas lancer en parallèle un second remote restore qui masquerait
le blocage observé. Le finally de secours tue/joint le mutateur identifié avant
sa restitution ; un secours ne transforme jamais l'essai en succès.

## Preuves et limites

Cinq groupes : préparation SSO/publications ; première fenêtre réelle ; capture
complète normale ; perte du pilote avec garde bloquée derrière le copieur ;
SIGKILL/jonction du copieur et du wrapper puis restitution indépendante.

La restitution recoupe bases/artefacts/configuration/proposition/référence,
même contrôle/image avec redémarrage attendu, santé, retraits physiques et unités
terminées. La sortie interrompue reste incomplète : pas de capture.json terminé,
pas de registre/artefacts de capture, aucune intégrité complète prétendue pour
la SQLite partiellement copiée. Après jonction, protéger ses fichiers privés
sous root et conserver identités/SHA pour l'échec provoqué. Elle n'est jamais
acceptée comme source de replay. La copie normale et la source6:15 sont recoupées
inchangées ; aucune purge métier des16 fonctions n'est revendiquée après perte.

Cette preuve qualifie l'interruption pendant la copie CONTROL et l'attente du
verrou hérité. Elle ne vaut ni rétention10000, ni sept jours, ni interruption à
chaque instruction du copieur. Le scénario et les régressions pertinentes doivent
passer avant de qualifier cette frontière ; SLS-078 reste ouverte.
