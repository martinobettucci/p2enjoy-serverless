# Acquisition des deux phases de publication de l'éditeur

Contrat de [SLS-118](BACKLOG.md#sls-118), préalable au complément
[SLS-070.3/.5](CODE_EDITOR_CONTROL_INTERRUPTION.md). Décision du 22 novembre
2026, persistée avant toute correction du banc.

## Échec conservé et diagnostic borné

Le [premier passage](evidence/code-editor-control-interruption-window-failed-dev-2026-11-22.json),
gel `4a5d67d` / 473 sources / API `04604089`, termine avec sortie 1 sous le
pilote 11034, joint. Deux groupes passent puis le troisième échoue : **zéro
groupe qualifié**, aucun commun lancé. Le client échoue ligne 53, SHA de message
`75648f4b82211d3298dc2026f75185a758d0ec8dceb4a25534d0eff0898296d6` ;
l'opérateur échoue sur `physical_phase_not_observed`, SHA
`43052d5207541f35a937519b4089c468bb3bb5b2e399a4eefe77197f1a058821`.

La coupure `receiving` est réellement observée : ZIP complet de 18 002 entrées,
mode `0444` et CRC, SIGKILL natif/code Docker 137, HTTP 502 puis candidat
`failed/control_interrupted`, restitution nominale et brouillon relu par API/UI.
Trois invocations réussies et deux JPEG desktop inspectés restent des observations
de cet essai ; aucune vue mobile ni coupure `validating` n'est acquise.

Pour la seconde phase, 1 535 sondes se terminent après 20,007976929 secondes.
Le candidat apparaît `prepared` à 6,674983774 s, puis le fichier complet
`receiving/0444` de 4 133 951 octets est observé à 6,728039519 s. Aucun
`validating` n'est capturé avant l'échéance. Le thread principal n'est pas
retenu et aucun programme de coupure n'est déclenché. Les fichiers natifs
confirment l'absence de `kill-started`, `kill-result`, `interrupted` et de reçu
indépendant pour cette garde. La requête se termine ensuite HTTP 200, publiée.
Le moment précis de fin de l'extraction et la cause système de sa durée ne sont
pas conservés ; aucune panne produit ou lenteur précise ne leur est attribuée.

Quatre candidats (trois publiés/un échoué), trois révisions, une fonction purgée,
un jeton révoqué et deux parents supprimés sont recoupés physiquement. Deux
gardes et helpers sont terminés, compteurs nuls. Même CID/image après l'unique
restart, référence/configuration/budgets/notes et 5 982 originaux conservés ;
38 modules backend/quatre ressources HTTPS/dix migrations recoupés. Le
collecteur RO supplémentaire a d'abord supposé `MainPID` sur un timer : son
KeyError est conservé, puis le champ optionnel est traité comme dans le
protocole existant. Aucun scénario n'a été rejoué pour cette collecte.

## Décision avant correction

Garder **20 secondes** d'acquisition, le timer de **45 secondes**, la confirmation
indépendante de **235 secondes**, les programmes RESTORE/KILL_CONTROL strictement
inchangés et les vrais événements natifs. Aucun allongement de fenêtre, rejeu,
mock, attente serveur ajoutée ou suppression d'un groupe.

Le grand paquet est utile pour retenir `receiving` après fsync ; il laisse
trop peu de fenêtre observée pour acquérir ensuite `validating` dans cet essai.
Employer deux bases de code réelles, avec la même fonction et la même cible A :

1. Conserver le paquet original de 18 002 entrées pour le scénario `receiving`,
   sa sauvegarde persistante, sa réouverture desktop et son nouveau pilote B.
2. Une fois ce scénario entièrement terminé, publier explicitement un ZIP
   **compact de deux fichiers** : `publication-recovery.cjs` original et son
   marqueur JSON sans délai d'import. C est un nouveau pilote par hash, jamais
   promu ; le défaut A et l'ETag de fonction restent identiques.
3. Abandonner explicitement le seul brouillon possédé, avec sa version courante,
   puis en créer un nouveau, rattaché à la véritable révision C. Ce changement
   volontaire de base arrive après la preuve de conservation du premier
   brouillon ; il ne répare ni n'acquitte sa publication interrompue.
4. Sauvegarder le marqueur `validating-pilot`, avec l'attente d'import réelle
   de 8 000 ms, dans ce nouveau brouillon. Armer avant son POST, acquérir
   `validating` et le validateur vivant, puis réaliser la seconde coupure et la
   perte du helper selon le contrat existant. La fenêtre manquée échoue encore.

Le packager possède deux modes explicites : sa commande habituelle génère le
grand ZIP ; `--compact` génère seulement les deux fichiers originaux. Dans les
deux cas, noms, compte, taille, SHA, CRC et mode des fichiers sont attestés.
L'opérateur exige exactement 18 002 entrées pour `receiving`, exactement deux
pour `validating`, sans retirer les contrôles de ZIP complet ni le recoupement
du même validateur vivant **après** les mesures ZIP/SHA/CRC.

Avant la seconde garde, exiger les compteurs au repos, le nouveau brouillon
personnel dont la base est C, son ID/version/acteur et l'UUID candidat absent.
Après restart, préserver et relire ce même brouillon C modifié, la cible A et
toutes les versions antérieures, dont C et B. Le pilote de reprise D et la
déduplication finale restent des actions explicites avec nouveaux UUID.

## Replay et critères de preuve

Les quatre groupes du contrat principal restent distincts : préparation A,
receiving/reprise B puis préparation réelle de la base C, validating/reprise D,
déduplication/consolidation. Exiger **six invocations**, **sept candidats**
exactement possédés (cinq publiés/deux échoués), **quatre révisions** A/B/C/D,
une fonction, un jeton et les deux parents purgés/supprimés comme auparavant.
La validation Docker réelle de C est conservée ; elle n'ajoute ni invocation
fictive ni groupe. A demeure le défaut pour tous les appels sans hash.

Puis huit manual-ui, huit public et neuf login-ui, frais et en série : **29
groupes**, quatre JPEG ciblés et 22 captures communes ouvertes individuellement.
Le premier échec, ses deux groupes passés, trois handlers et deux captures ne
s'ajoutent jamais à ce replay. Les preuves antérieures 45/43/39/36/32 gardent
leurs époques ; leur rapprochement vérifie les mêmes modules, sans addition.

Les trois orchestrateurs du premier essai restent gelés dans leur état et leur
copie archivée. Le replay utilise trois nouveaux programmes et un nouveau
répertoire UUID, le seul nouveau rapport UUID, les sources synchronisées
figées (index attendu 474 avec ce contrat) et les artefacts du nouveau passage.
Son précontrôle prend pour génération de départ le `native_final` du manifeste
échoué, et recoupe CID/image/référence/configuration/budgets/originaux avec
l'installation et la construction qualifiées. Le changement StartedAt déjà
acquis n'est pas confondu avec un déploiement ou un nouveau redémarrage.

Les deux nouveaux changements de génération restent exigés séquentiellement,
avec les deux vrais signaux 9, sorties 137 et reçus de garde. Aucun secours
n'acquitte l'indépendance. Le cleanup public refuse tout candidat étranger,
joint transports/helpers/mutateurs/gardes et recoupe la purge physique, les
38 backend, quatre ressources no-store, schéma010/intégrité/FK, manuel18/74/SHA,
notes actives/proposées et 5 982 originaux, sans changer l'image produit.

Le premier échec et la présente décision sont acquis ; aucun code de correction
ni replay positif n'est encore livré à ce checkpoint. SLS-118 et SLS-070 restent
ouverts jusqu'au passage réel et au rapprochement complet des critères.
