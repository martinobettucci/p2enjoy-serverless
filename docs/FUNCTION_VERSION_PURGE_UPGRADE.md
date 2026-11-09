# Reprendre une purge engagée pendant le premier upgrade du registre

Complément de [SLS-074](BACKLOG.md#sls-074), à réaliser après la campagne
commune en cours. Le registre actuel et son upgrade 006 → 007 au repos sont
éprouvés ; ce document prépare la correction d’un état intermédiaire 006 valide.

## Constat et décision

La décision durable de purge efface inventaire et événements avant l’effacement
physique. Une interruption laisse donc légitimement `inventory_json=[]`,
`events_json={}`, une révision supprimée et des octets encore comptabilisés.
Le backfill actuel refuse cette ligne avant que le résolveur puisse reprendre.
Ce n’est pas un inventaire de code invocable à reconstruire : sa fonction est
déjà supprimée et sa purge décidée. Une installation déjà migrée garde son hash
et ne réexécute pas 007 ; le défaut concerne le premier passage depuis 006.

Décision : reconnaître uniquement cette purge durable et corrélée, conserver
une identité inconnue `NULL`, puis laisser le résolveur normal terminer. Ne pas
fabriquer un hash depuis des fichiers dont le descripteur a été effacé, ni
accepter toute révision vide encore comptabilisée. Le pointeur courant, les
autres révisions et les compteurs ne sont pas réécrits par cette reconnaissance.

La corrélation exige la même fonction supprimée et sans pointeur actif, le même
service, le même UUID d’opération entre commande et garde, le type purge, une
décision `commit`, une commande `pending` dans `volumes` ou `artifacts`, le même
propriétaire d’installation, la version résultante égale à celle de la fonction
et les versions attendues de commande/garde concordantes. L’inventaire et les
événements doivent être ceux réellement effacés par la purge. Une corrélation
absente ou contradictoire conserve le refus transactionnel.

La correction porte sur le calcul de la première transition 007, sans nouveau
format SQLite. Une migration suivante seule ne pourrait pas réparer un refus
qui survient avant elle. Les installations déjà marquées 007 la sautent et
conservent leurs identités immuables. Les preuves distingueront les deux images
et les époques de sources ; la première campagne ne devient pas rétroactivement
une preuve de cette correction.

## Banc historique réel et borné

Réutiliser la fenêtre gardée de `storage-legacy-environment.py`, avec l’image
006 réellement conservée, les fichiers officiels de cellule et le SSO normal.
Les originaux, leurs tables et artefacts, la configuration et l’exécuteur de
référence sont restaurés par la garde existante, sans administration de FORGE.
Les modes historiques actuels gardent leur attente de santé verte.

Le nouveau parcours crée ses fonctions et leur code original par les API.
Une vraie publication Node/Docker précède suppression et purge publiques.
`deny-artifact` retient le seul dossier corrélé avec EACCES. Observer les
compteurs, l’inventaire effacé, la garde et le reçu plutôt que simuler ces états.

Pour la phase `artifacts`, attendre la fin de l’agent et le reçu de contrôle
encore pending. Pour `volumes`, utiliser de vrais fichiers à effacer : après
`start-discard` pending, l’agent peut terminer avant le prochain sweep du contrôle.
Le helper constate alors reçu agent terminé, absence de volumes/baux/pending
agent et commande de contrôle encore en `volumes`, puis arrête immédiatement
le contrôle. Cette garde avant arrêt préserve les préconditions du restaurateur.
Si la fenêtre attendue n’existe pas, le scénario échoue ; aucun passage n’est
déclaré ou ignoré conditionnellement.

Une attente « API lisible » explicite vérifie image/ID/vie du seul conteneur
temporaire et le vrai GET anonyme `/api/session` avec Host canonique. Elle ne
confond pas santé 503 due à la purge retenue et échec de migration. Un refus
attendu vérifie sortie non nulle de l’application, schéma exact 006, absence de
colonne/marqueur 007, intégrité et mêmes anciennes lignes après son arrêt.

La reprise de l’image 006 sur la même base n’est permise qu’après ce rollback
constaté. Elle est interdite dès que 007 est commise. Le relâchement d’artefact
ouvre le dossier NOFOLLOW, vérifie device/inode, restaure son mode par fchmod
pendant qu’il appartient encore à root, puis fchown en dernier. Sa disparition
immédiate est normale ; le reçu public et les octets à zéro confirment la fin.

## Preuves à terminer

1. Référence actuelle : vraie purge 006 retenue, refus de 007, rollback complet,
   reprise de 006 sans restauration de base, relâchement et fin normale.
2. Correction : mêmes parcours pour les phases d’entrée volumes et artifacts,
   007 appliquée pendant EACCES, commande/garde conservées, aucun hash inventé,
   compteurs maintenus ; relâchement, reçu terminé et persistance après restart.
3. Copies privées des vrais états intermédiaires : erreurs réelles de
   corrélation et vrai démarrage refusé, transaction annulée. Aucun remplacement
   de serveur, dépendance ou réponse. Sauvegardes privées jamais publiées.
4. Restauration et perte du pilote : originaux et configuration identiques,
   agent et contrôle sains, volumes/baux/instances temporaires absents ; la
   nouvelle fenêtre reste compatible avec la garde indépendante.
5. Rejouer les campagnes concernées sur la nouvelle image, y compris le banc
   003 → 007 ; conserver séparément la campagne précédente sur l’ancienne image.

Si 007 est annulée, conserver la base 006 et reprendre l’ancienne image : une
restauration de sauvegarde risquerait de revenir avant la purge déjà décidée.
Si 007 est commise, le downgrade exige le plan cohérent base/fichiers/volumes
et ancienne image ; une ancienne image seule ne constitue pas un retour arrière.
