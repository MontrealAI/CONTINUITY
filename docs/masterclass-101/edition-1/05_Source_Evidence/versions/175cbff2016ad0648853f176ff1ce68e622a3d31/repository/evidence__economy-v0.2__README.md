# CONTINUITY Ω — Inspectable economy evidence / CONTINUITÉ Ω — Preuves économiques inspectables

[English](#english) · [Français](#français)

## English

This directory accompanies the separately versioned digital-product experiment. [Qualification metadata](qualification.json) identifies the exact source, registries, freeze, commands, actual test results and archive digest. [English results](../../docs/economy/RESULTS.md) and [French results](../../docs/economy/RESULTS.fr.md) explain outcome, modeled service feasibility and method advantage separately.

The complete compressed [evidence archive](attempts.tar.xz) retains the first registered base comparison, the complete qualification experiment, separate fresh verification, development logs and before/after counterexamples. **Earlier failed and incomplete development attempts are deliberately retained. Their presence is evidence of investigation, not qualification of those earlier implementations.** The archive contains actual digital products, raw received content, imported-unit databases, capacity and financial ledgers, retained contracts/policies/pins, fault records and bilingual Passports. It contains synthetic data only.

The sealed archive is **2,879,196 bytes**, with SHA-256 `a96c6b7c25e0e17ed1c1f7d0fcf13b70c338159ae9c10c5f825699b9e186db25`. All **7,416 retained file hashes** matched after extraction. Fresh verification of both extracted experiments passed; the complete machine-readable observations are in [verification](verification/). Later [CI evidence](ci/README.md) is retained separately, including the original startup failure, the test-only readiness correction and [three successful workflows at the corrected source](ci/source-dd005-workflows.json). These later records do not rewrite the sealed experiment archive.

### Extract and freshly verify

From the qualified repository checkout, compare the archive SHA-256 with `qualification.json`, then choose a new extraction directory:

```sh
sha256sum evidence/economy-v0.2/attempts.tar.xz
mkdir /tmp/continuity-economy-evidence-001
tar -xJf evidence/economy-v0.2/attempts.tar.xz -C /tmp/continuity-economy-evidence-001
python3 -m continuity_economy --language en verify-suite --in-dir /tmp/continuity-economy-evidence-001/qualification/complete-attempt-1
python3 -m continuity_economy --language en verify-suite --in-dir /tmp/continuity-economy-evidence-001/qualification/base-attempt-1
```

`MANIFEST.json` inside the archive gives the byte identity of each retained file. The archive digest and independently copied original reference/index must retain trusted custody. Matching bytes do not authenticate a customer, establish completeness of a real source or protect against a malicious host administrator. Fresh verification inspects the databases and products; saved `RESULT.json`, `SUMMARY.json` and Passports are not proof.

### Read the records correctly

The registered base comparison records conventional, Harness, no-purchase and unavailable-AI cells separately. The successor is separately authored after the first experiment and reusable-material freeze. Challenges distinguish actual local executions from deliberate evidence alterations and defective-verifier observations. Each record separates test assertion, component verdict, evidence stage, claim status and obligation outcomes. An outer passing mutation test never qualifies its defective checker. A refusal or partial result may be the expected observation while the digital promise remains unfulfilled.

The first base and later complete replay are distinct retained attempts; do not pool their timings as a preregistered statistical sample or conceal either one. Actual source hashes, logical schedules/seeds, observed timing, intervention/retry counts and recording limits are retained. Run identifiers and monotonic timestamps naturally differ on replay. Preparation, integration, adaptation and verification labor, real monetary rates and final reporting overhead remain unknown where unmeasured. All SMU figures are authored synthetic minor units, with 100 minor units per fictional SMU; no real payment or demand is established.

Publication stages are separate. The source and evidence are prepared on the review branch; a branch or pull request is not a merged release. The qualification metadata and final handoff report the actual stage. Historical Harness v0.1, papers, PDFs, evidence identities and original Lab links are preserved.

## Français

Ce répertoire accompagne l’expérience distincte de produit numérique. Les [métadonnées de qualification](qualification.json) identifient les sources exactes, préenregistrements, gel, commandes, résultats réellement observés et empreinte de l’archive. Les [résultats français](../../docs/economy/RESULTS.fr.md) et [anglais](../../docs/economy/RESULTS.md) distinguent résultat, faisabilité du service modélisé et avantage de méthode.

L’[archive complète des preuves](attempts.tar.xz) conserve la première comparaison de base, l’expérience complète de qualification, les vérifications fraîches distinctes, journaux de développement et contre-exemples avant/après correction. **Les tentatives antérieures échouées ou incomplètes sont volontairement conservées. Elles attestent l’investigation, sans qualifier ces anciennes implémentations.** L’archive contient les produits numériques réels, octets reçus, bases d’unités importées, registres de capacité et financiers, contrats/politiques/empreintes conservés, pannes et passeports bilingues. Toutes les données sont synthétiques.

L’archive scellée compte **2 879 196 octets**, avec le SHA-256 `a96c6b7c25e0e17ed1c1f7d0fcf13b70c338159ae9c10c5f825699b9e186db25`. Les empreintes des **7 416 fichiers conservés** correspondent après extraction. La vérification fraîche des deux expériences extraites a réussi ; les observations complètes lisibles par machine sont dans [verification](verification/). Les [preuves CI ultérieures](ci/README.md) sont conservées séparément, dont l’échec de démarrage initial, la correction limitée à la disponibilité dans les tests et [les trois workflows réussis à la source corrigée](ci/source-dd005-workflows.json). Ces enregistrements ultérieurs ne réécrivent pas l’archive scellée.

### Extraire et revérifier

Depuis le dépôt qualifié, comparer le SHA-256 de l’archive à `qualification.json`, puis choisir un nouveau répertoire d’extraction :

```sh
sha256sum evidence/economy-v0.2/attempts.tar.xz
mkdir /tmp/continuite-economie-preuves-001
tar -xJf evidence/economy-v0.2/attempts.tar.xz -C /tmp/continuite-economie-preuves-001
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuite-economie-preuves-001/qualification/complete-attempt-1
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuite-economie-preuves-001/qualification/base-attempt-1
```

`MANIFEST.json` dans l’archive donne l’identité binaire de chaque fichier conservé. L’empreinte de l’archive et une copie indépendante de la référence/de l’index d’origine doivent rester sous une garde de confiance. Des octets identiques n’authentifient pas un client, n’établissent pas l’exhaustivité d’une source réelle et ne protègent pas d’un administrateur hôte malveillant. La vérification fraîche inspecte bases et produits ; `RESULT.json`, `SUMMARY.json` et les passeports sauvegardés ne font pas preuve.

### Interpréter les enregistrements

La comparaison de base sépare les cellules conventionnelles, du banc, sans achat et d’IA indisponible. Le successeur est rédigé séparément après la première expérience et le gel des éléments réutilisables. Les épreuves distinguent exécutions locales réelles, altérations de preuves et observations de vérificateurs défectueux. Chaque enregistrement sépare assertion, verdict du composant, stade de preuve, état de l’affirmation et résultats par obligation. Une mutation détectée par un test réussi ne qualifie jamais son vérificateur défectueux. Un refus ou résultat partiel peut être attendu alors que la promesse numérique demeure non réalisée.

La première base et la reproduction complète ultérieure sont deux tentatives distinctes conservées ; ne pas fusionner leurs durées en échantillon statistique préenregistré ni en cacher une. Empreintes des sources, calendriers/graines logiques, temps observés, interventions/reprises et limites de mesure sont conservés. Identifiants et temps monotones varient naturellement à la reproduction. Travail de préparation, intégration, adaptation et vérification, tarifs réels et coût du rapport final restent inconnus s’ils ne sont pas mesurés. Tous les montants SMU sont des hypothèses en unités mineures synthétiques, avec 100 unités mineures par SMU fictive ; aucun paiement ni demande réels ne sont établis.

Les étapes de publication sont distinctes. Sources et preuves sont préparées sur la branche de revue ; une branche ou demande de fusion n’est pas une version fusionnée/publiée. Les métadonnées et la remise finale précisent l’étape réelle. Banc historique v0.1, articles, PDF, identités des preuves et liens du Lab original sont préservés.
