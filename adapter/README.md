# Adaptateur P2Enjoy

Implémentation SLS-030 en cours. Contrat : [DEPLOYMENT](../docs/DEPLOYMENT.md).
Hôte Linux, Python 3.13+ et PyYAML 6.0.3 ; les archives utilisent ZIP de la bibliothèque
standard. Les handlers sont préparés par le projet avant le packaging.

Depuis la racine, les commandes disponibles sont :

```sh
python3 -m adapter plan --config qualification/serverless.platform.yml
python3 -m adapter package --config qualification/serverless.platform.yml
python3 -m adapter deploy --config qualification/serverless.platform.yml --service UUID_DU_SERVICE
```

`deploy` lit l’origine HTTPS dans `P2_SERVERLESS_URL` et le jeton de service
dans `P2_SERVERLESS_TOKEN`. Le service doit déjà exister et porter le nom du
manifeste. Read est nécessaire pour rechercher les fonctions ; Create publie
la première révision et Update les suivantes. Les valeurs `${env:NOM}` sont
résolues depuis l’environnement du processus, sans fichier `.env`.

La configuration de `provider` est conservée dans le service. Sa modification
exige également Update non limité à certaines fonctions. Les fonctions portent
seulement leurs surcharges. Une catégorie provider absente préserve le service ;
une catégorie présente remplace ses clés. Le rapport `service_configuration`
indique `preserved`, `applied`, `failed` ou `unknown`. Une modification commune
appliquée reste effective même si l’import d’une fonction échoue ensuite.
Les parcours sont qualifiés dans [SLS-031](../docs/BACKLOG.md#sls-031), y compris
une vraie réponse perdue avant traitement et après commit : `unknown`, état
durable recoupé et absence de rejeu. Le
[complément](../docs/evidence/service-configuration-transport-dev-2026-11-08.json)
ajoute cinq groupes natifs puis treize groupes de configuration rejoués sur la
même image que le checkpoint de 191 groupes.
Le plan et le descripteur exposent les noms des valeurs communes, les noms
effectifs connus et les noms des surcharges locales, sans leurs valeurs.
La [preuve DEV](../docs/evidence/service-configuration-dev-2026-11-08.json)
réunit treize groupes ciblés et les régressions : 153 groupes sur le poste,
puis 24 de plan/package et quatorze de refus public rejoués dans Docker.

La CLI valide et empaquette tout avant mutation, puis publie en série. Elle
conserve les UUID et refuse les redirections. La configuration commune s’applique
avant les publications ; les surcharges de fonction s’activent seulement après
validation de leur candidat. Les erreurs donnent un code de sortie
non nul et un résultat JSON par fonction tentée. Une réponse perdue est signalée
`unknown`, avec l’identifiant du candidat connu, sans rejouer la mutation.
Consulter ce candidat avant toute relance. Les avertissements précèdent les
appels sur stderr ; stdout contient le rapport final sans configuration ni logs.

Les preuves CLI exécutent le vrai processus ; les preuves de déploiement
utilisent la véritable API DEV et une identité SSO. Les sept groupes authentifiés
passent : [preuve de publication](../docs/evidence/deployment-authenticated-dev-2026-11-06.json).
Chaque campagne est séquentielle. Les sorties locales vont dans .serverless-p2
du projet et sont exclues des archives. Les valeurs de secrets restent hors
des descripteurs et de la sortie standard.

Installation Python dans un environnement isolé : `python3 -m pip install
--require-hashes -r adapter/requirements.txt`. Sur le SPARK DEV, depuis
`/srv/p2enjoy-serverless/adapter`, exécuter successivement `bash dev.sh build`,
`bash dev.sh plan`, `bash dev.sh package`, `bash dev.sh test`, puis `bash dev.sh deploy-public-test`. Chaque commande
attend la précédente. Les deux images se construisent en série. La cible E2E
ajoute ses fichiers de preuve à l'image réelle de la CLI et ne lance aucun
serveur de substitution. Le rapport est conservé dans `adapter/reports/`.

`deploy-public-test` exerce les erreurs locales et un véritable refus 401
sur https://serverless.lelabs.tech, avec validation TLS normale. Un jeton
volontairement invalide n’est jamais accepté comme identité. Le rapport est
`adapter/reports/adapter-deploy-public.json`. Cette campagne ne prouve aucune
publication. Depuis le dépôt du poste, `node e2e/adapter-deploy.mjs` utilise
la session SSO réelle pour créer ses jetons, puis exécute la CLI et les
validations Docker : pagination, mises à jour, résultats partiels et reprise
de brouillon. Les ruptures après envoi, modifications concurrentes des fichiers,
redirections et réponses trop grandes restent à éprouver avec leurs causes réelles.
L’invocation du code publié est qualifiée séparément par le moteur public et
les parcours de publication de la console : [preuves E2E](../e2e/README.md).

Le résultat de chaque publication réussie inclut maintenant `invocation_urls`,
obtenu par le catalogue Read du contrôle. La lecture parcourt les domaines
par cinq et exige la même révision et empreinte de source entre pages. Une
lecture refusée, perdue ou changeante donne `invocation_urls.state=unavailable`
sans requalifier la publication réussie ni renvoyer de code. Les cas courants
passent dans le checkpoint SLS-066. La perte réelle est qualifiée dans le
[complément de transport](../docs/evidence/invocation-url-transport-dev-2026-11-08.json) :
deux vrais 502 après publication, succès/UUID conservés, six connexions sans
rejeu et invocation Docker après reprise. Le
[complément de révocation](../docs/evidence/invocation-url-refusal-dev-2026-11-08.json)
qualifie le vrai GET 401 après publication, avec succès/UUID conservés et
six connexions sans rejeu ; un autre Read invoque Docker. Les pages suivantes
restent à éprouver ; le 403 n’est pas revendiqué. [Contrat](../docs/INVOCATION_URLS.md).
Les campagnes courantes sont aussi rejouées dans la
[suite de 35 campagnes / 467 groupes](../docs/evidence/invocation-urls-regressions-dev-2026-11-08.json),
avec les deux images Docker reconstruites en série et figées avant/après chaque
campagne. Les cinq modules CLI embarqués correspondent aux sources. Cette
réussite ne qualifie pas les pages supplémentaires ; les pertes de lecture
sont établies séparément par le complément de transport.
