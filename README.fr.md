# CONTINUITÉ Ω

[English](README.md#english) · [Français dans le README principal](README.md#français)

## Français

**CONTINUITÉ Ω : Tenir parole.** Recherche, exécution locale, preuves et publications bilingues de Vincent Boucher, MONTREAL.AI / QUEBEC.AI.

### Banc d’essai et de vérification v0.1 — exécuter et vérifier

Le **banc d’essai et de vérification CONTINUITÉ Ω**, versionné séparément, exécute de véritables processus jetables et un stockage local durable avec des commandes synthétiques d’étiquettes. Il reconstitue les obligations restantes, restaure le service principal ou emprunte une voie de secours autorisée, puis vérifie les résultats logiciels actuels par rapport à un contrat conservé séparément. La voie peut changer ; la promesse client ne doit pas changer silencieusement avec elle.

[Installation et commandes du banc d’essai](docs/harness/README.fr.md) · [Architecture](docs/harness/ARCHITECTURE.fr.md) · [Modèle de menace et limites](docs/harness/THREAT_MODEL.fr.md) · [Exigences et tests](docs/harness/REQUIREMENTS.fr.md) · [Expérience préenregistrée](docs/harness/EXPERIMENT.md#français)

**Preuves exécutées :** [Résultats complets](docs/harness/RESULTS.fr.md) · [Télécharger et inspecter les preuves](evidence/harness-v0.1/README.md#français) · [Passeport du cas contraint](evidence/harness-v0.1/passports/constrained/PASSPORT.fr.md). La révision qualifiée a réussi 245 tests du dépôt et une comparaison de 24 exécutions donnant 12 égalités fonctionnelles ; les 12 entrées IA portent explicitement la mention NON EXÉCUTÉE. Les deux tentatives sont conservées, dont l’échec de vérification distincte de la première. L’archive finale a aussi réussi une vérification après extraction.

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
