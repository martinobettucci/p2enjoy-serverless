# Registre des incohérences

## Noms abrégés des conteneurs de validation

Constat hors du complément de reprise : `control/app/validator.py:136` construit
le nom `p2-v-` suivi d’un UUID. Le nom ne décrit pas le rôle du conteneur dans
l’exploitation, contrairement à `CLAUDE_PROJECT.md` §Nommage obligatoire. Le
contrôle de l’image embarquée recoupe ce fichier avec la source ; les quatre
groupes de reprise utilisent réellement ce pilote. Le constat porte sur le nom,
aucune défaillance d’exécution ou de propriété n’est établie.

Issue proposée pour la boucle après commit du complément : convertir en unité
bornée de backlog, avec nom décrivant la validation du code, compatibilité des
labels de reprise, build DEV et preuve E2E d’un import réussi/refusé/expiré puis
reprise. La correction nécessite une nouvelle image applicative et ne doit pas
être mêlée à la preuve produit figée du complément en cours.
