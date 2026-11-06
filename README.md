# CONTINUITY Ω / CONTINUITÉ Ω

[English](#english) · [Français](#français)

## English

**CONTINUITY Ω: Keep the promise.** Research, local execution, evidence and bilingual publications by Vincent Boucher, MONTREAL.AI / QUEBEC.AI.

### Harness v0.1 — execute and verify

The separately versioned **CONTINUITY Ω Harness** exercises real disposable processes and durable local storage with synthetic packaging-label orders. It reconstructs outstanding obligations, restores the primary service or uses an authorized backup, and freshly verifies the resulting software artifacts against a separately retained contract. The route may change; the customer promise must not silently change with it.

[Harness setup and commands](docs/harness/README.md) · [Architecture](docs/harness/ARCHITECTURE.md) · [Threat model and limitations](docs/harness/THREAT_MODEL.md) · [Requirements and tests](docs/harness/REQUIREMENTS.md) · [Preregistered experiment](docs/harness/EXPERIMENT.md)

Linux x86_64, Python 3.10+ and seccomp BPF are required for the candidate boundary. No additional Python packages, API keys, model download or paid services are required. From a clean checkout:

```sh
git clone https://github.com/MontrealAI/CONTINUITY.git
cd CONTINUITY
python3 -m continuity_harness --language en demo --out /tmp/continuity-harness-demo-001
python3 -m continuity_harness --language en verify-suite --in-dir /tmp/continuity-harness-demo-001
python3 -m continuity_harness --language en compare --out /tmp/continuity-harness-comparison-001
python3 -m continuity_harness --language en verify-suite --in-dir /tmp/continuity-harness-comparison-001
python3 -m continuity_harness --language en challenge --out /tmp/continuity-harness-challenges-001
python3 -m unittest discover -s tests -p 'test_harness*.py' -v
```

Always choose a new output directory. Each run retains durable evidence, a machine-readable result, and complete English/French Passports. The three base controls cover feasible recovery, feasible alternate fulfillment, and constrained capacity with concurrency, lost acknowledgment, process termination and restart. The constrained contract requires 1,900 units but provides only 1,500 units of backup capacity: completing 1,100 units and safely refusing 800 is **partial fulfillment**, even when the expected safety test passes.

The registered comparison gives a competent conventional procedure and the Harness-supported procedure the same tools, information and faults. AI performance is **NOT RUN** without a suitable already-authorized local model. These local JSON outputs are not printed goods, customer delivery or commercial validation. Host, controller, service, authored journal, clock and verifier remain trusted. See the guide for exact conditions, measured resources and unknown costs.

### Start here

- [Prototype and limitations](docs/continuity-omega/README.md) · [Quick start](docs/continuity-omega/QUICKSTART.md)
- [Research paper, edition 1.1.1](docs/continuity-omega-paper/README.md)
- [English paper PDF](docs/continuity-omega-paper/CONTINUITY_OMEGA.pdf) · [French paper PDF](docs/continuity-omega-paper/CONTINUITY_OMEGA_FR.pdf)
- [Read saved reports](docs/continuity-omega/OUTPUTS.md) · [Proposed real pilot](docs/continuity-omega/REAL_PILOT.md)
- [Original English web reader](https://montrealai.github.io/AGI-Alpha-Invention-Flywheel-Lab/continuity-omega.html) · [Original French web reader](https://montrealai.github.io/AGI-Alpha-Invention-Flywheel-Lab/continuity-omega-fr.html)
- [Original bilingual publication](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/releases/tag/continuity-omega-v1.1.1) · [Original reading companion](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/releases/tag/continuity-omega-reading-v1.0.1)

### Run locally

Python 3.10+; no packages, network, API keys or paid services are needed for the prototype. The complete test suite additionally requires Node.js for website JavaScript checks; no npm packages are needed.

```sh
python3 scripts/continuity.py --language en demo --case nominal --out /tmp/continuity-new-example
python3 scripts/continuity.py --language en verify --in-dir /tmp/continuity-new-example
python3 scripts/continuity_passport.py --in-dir /tmp/continuity-new-example --language en
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

Choose a new output directory; the bilingual demo also creates a separate sibling `<output>-reports` directory containing both language reports. Neither destination may already exist. For French reports, use `--language fr`. The reader displays saved records; it does not perform a fresh audit. See the paper guide for separate TeX build and pinned historical reproduction requirements.

### Copy and publication boundary

This repository began with a byte-preserved copy of 78 dedicated files from [Lab commit de6839a](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/tree/de6839a4da2275dbe4cda00c2d3b5625210e02c5). [PROVENANCE.json](PROVENANCE.json) lists every original copied path, SHA-256 and Git blob. Documented website adaptations are tracked separately in [LOCALIZATION.json](LOCALIZATION.json). [MIGRATION.md](MIGRATION.md) explains the boundary.

The original repository, papers, releases, links and ongoing work remain unchanged. This copy does not deprecate or replace that work. Published manifests, source pins, citations and original URLs retain their historical meaning. Website sources and media are preserved under `docs/research/`; their bilingual local navigation now links to original foundational research where needed. No new Pages deployment or duplicate historical release is created here.

**Historical research prototype:** the preserved `continuity_omega` implementation uses authored synthetic inputs and establishes no real recovery, supplier reservation, customer delivery, revenue or external certification. The separate Harness adds actual local software execution; it does not strengthen old evidence retroactively. The original checker weaknesses and counterexamples remain disclosed. This copy does not integrate the separately proposed PR #279 hardening or qualify it. Same-authorship separate code paths are not third-party assurance.

No new license is asserted: the source snapshot contains no root license, and existing notices and authorship are preserved. Public availability alone does not grant additional reuse rights.

### Complete language paths

[Bilingual CLI](docs/BILINGUAL_CLI.md) · [Research tools](docs/RESEARCH_TOOLS.md) · [Language coverage and historical exceptions](BILINGUALITY.md#english) · [Local website entry](docs/research/index.html). HTML files are supplied source, not a newly deployed website.

---

## Français

**CONTINUITÉ Ω : Tenir parole.** Recherche, exécution locale, preuves et publications bilingues de Vincent Boucher, MONTREAL.AI / QUEBEC.AI.

### Banc d’essai et de vérification v0.1 — exécuter et vérifier

Le **banc d’essai et de vérification CONTINUITÉ Ω**, versionné séparément, exécute de véritables processus jetables et un stockage local durable avec des commandes synthétiques d’étiquettes. Il reconstitue les obligations restantes, restaure le service principal ou emprunte une voie de secours autorisée, puis vérifie les résultats logiciels actuels par rapport à un contrat conservé séparément. La voie peut changer ; la promesse client ne doit pas changer silencieusement avec elle.

[Installation et commandes du banc d’essai](docs/harness/README.fr.md) · [Architecture](docs/harness/ARCHITECTURE.fr.md) · [Modèle de menace et limites](docs/harness/THREAT_MODEL.fr.md) · [Exigences et tests](docs/harness/REQUIREMENTS.fr.md) · [Expérience préenregistrée](docs/harness/EXPERIMENT.md#français)

Linux x86_64, Python 3.10 ou ultérieur et seccomp BPF sont nécessaires à l’isolation du candidat. Aucun paquet Python supplémentaire, clé API, téléchargement de modèle ou service payant n’est requis. Depuis une nouvelle copie :

```sh
git clone https://github.com/MontrealAI/CONTINUITY.git
cd CONTINUITY
python3 -m continuity_harness --language fr demo --out /tmp/continuite-banc-demo-001
python3 -m continuity_harness --language fr verify-suite --in-dir /tmp/continuite-banc-demo-001
python3 -m continuity_harness --language fr compare --out /tmp/continuite-banc-comparaison-001
python3 -m continuity_harness --language fr verify-suite --in-dir /tmp/continuite-banc-comparaison-001
python3 -m continuity_harness --language fr challenge --out /tmp/continuite-banc-epreuves-001
python3 -m unittest discover -s tests -p 'test_harness*.py' -v
```

Toujours choisir un nouveau répertoire. Chaque exécution conserve les preuves durables, un résultat lisible par machine et des passeports complets en français et en anglais. Les trois contrôles de base couvrent la reprise réalisable, l’exécution alternative réalisable et la capacité insuffisante avec concurrence, perte d’accusé de réception, interruption et redémarrage de processus. Le contrat contraint exige 1 900 unités mais ne dispose que de 1 500 unités de secours : réaliser 1 100 unités et refuser correctement les 800 restantes constitue une **réalisation partielle**, même si le test de sûreté attendu réussit.

La comparaison préenregistrée fournit à une procédure conventionnelle compétente et à celle appuyée par le banc d’essai les mêmes outils, informations et pannes. La performance de l’IA porte la mention **NON EXÉCUTÉE** sans modèle local approprié déjà autorisé. Ces fichiers JSON locaux ne sont ni des biens imprimés, ni une livraison client, ni une validation commerciale. L’hôte, le contrôleur, le service, le journal synthétique, l’horloge et le vérificateur restent des composants de confiance. Le guide précise les conditions, ressources mesurées et coûts inconnus.

### Commencer

- [Prototype et limites](docs/continuity-omega/README.fr.md) · [Démarrage rapide](docs/continuity-omega/QUICKSTART.fr.md)
- [Article, édition 1.1.1](docs/continuity-omega-paper/README.fr.md)
- [Article français en PDF](docs/continuity-omega-paper/CONTINUITY_OMEGA_FR.pdf) · [Article anglais en PDF](docs/continuity-omega-paper/CONTINUITY_OMEGA.pdf)
- [Lire les rapports enregistrés](docs/continuity-omega/OUTPUTS.fr.md) · [Pilote réel proposé](docs/continuity-omega/REAL_PILOT.fr.md)
- [Lecteur français original](https://montrealai.github.io/AGI-Alpha-Invention-Flywheel-Lab/continuity-omega-fr.html) · [Lecteur anglais original](https://montrealai.github.io/AGI-Alpha-Invention-Flywheel-Lab/continuity-omega.html)
- [Publication bilingue originale](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/releases/tag/continuity-omega-v1.1.1) · [Compagnon original](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/releases/tag/continuity-omega-reading-v1.0.1)

### Exécution locale

Python 3.10 ou ultérieur. Le prototype ne nécessite aucun paquet supplémentaire, accès réseau, clé API ou service payant. La suite complète de tests exige aussi Node.js pour les contrôles JavaScript du site ; aucun paquet npm n’est nécessaire.

```sh
python3 scripts/continuity.py --language fr demo --case nominal --out /tmp/continuite-nouvel-exemple
python3 scripts/continuity.py --language fr verify --in-dir /tmp/continuite-nouvel-exemple
python3 scripts/continuity_passport.py --in-dir /tmp/continuite-nouvel-exemple --language fr
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

Choisir un nouveau répertoire de sortie ; la démonstration bilingue crée aussi un répertoire voisin distinct `<sortie>-reports` contenant les rapports dans les deux langues. Aucun des deux emplacements ne doit déjà exister. Le lecteur affiche des enregistrements sauvegardés, sans nouvel audit. Le guide de l’article décrit les exigences TeX et la reproduction historique séparées.

### Périmètre de la copie

Les 78 fichiers dédiés ont été copiés sans changement depuis [le commit de6839a du dépôt Lab](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/tree/de6839a4da2275dbe4cda00c2d3b5625210e02c5). [PROVENANCE.json](PROVENANCE.json) fournit chaque chemin original, son empreinte SHA-256 et son identifiant Git blob. Les adaptations web sont suivies séparément dans [LOCALIZATION.json](LOCALIZATION.json). Le dépôt original, les publications, les liens et les travaux en cours restent inchangés. Cette copie ne remplace ni ne déprécie ce travail.

Les sources web et médias sous `docs/research/` offrent une navigation locale bilingue et renvoient aux travaux fondateurs originaux lorsque nécessaire. Aucun nouveau site Pages ni doublon des publications historiques n’est créé ici. Les sources figées, citations et manifestes gardent leur portée historique.

**Prototype de recherche historique :** l’implémentation préservée `continuity_omega` emploie des données synthétiques, sans établir de reprise réelle, réservation fournisseur, livraison client, revenus ou certification externe. Le banc d’essai distinct ajoute une exécution logicielle locale réelle ; il ne renforce pas rétroactivement les anciennes preuves. Les faiblesses du vérificateur et les contre-exemples restent documentés. Le renforcement proposé dans la PR #279 n’est ni intégré ni qualifié par cette copie. Des chemins de code séparés sous une même responsabilité de recherche ne constituent pas une assurance tierce indépendante.

Aucune nouvelle licence n’est déclarée : la source ne contient pas de licence à la racine. Les notices et attributions existantes sont préservées ; la disponibilité publique ne crée pas de droits supplémentaires.

### Parcours linguistiques complets

[Interface bilingue](docs/BILINGUAL_CLI.fr.md) · [Outils de recherche](docs/RESEARCH_TOOLS.fr.md) · [Couverture linguistique et exceptions historiques](BILINGUALITY.md#français) · [Accueil du site local](docs/research/index-fr.html). Les fichiers HTML sont des sources fournies, pas un nouveau site déployé.
