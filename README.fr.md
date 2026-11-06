# CONTINUITÉ Ω

[English](README.md#english) · [Français dans le README principal](README.md#français)

## Français

**CONTINUITÉ Ω : Tenir parole.** Recherche, prototype synthétique hors ligne, preuves et publications bilingues de Vincent Boucher, MONTREAL.AI / QUEBEC.AI.

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

**Prototype de recherche uniquement :** données synthétiques, sans reprise réelle, réservation fournisseur, livraison client, revenus ou certification externe. Les faiblesses du vérificateur et les contre-exemples restent documentés. Le renforcement proposé dans la PR #279 n’est ni intégré ni qualifié par cette copie. Des chemins de code séparés sous une même responsabilité de recherche ne constituent pas une assurance tierce indépendante.

Aucune nouvelle licence n’est déclarée : la source ne contient pas de licence à la racine. Les notices et attributions existantes sont préservées ; la disponibilité publique ne crée pas de droits supplémentaires.

### Parcours linguistiques complets

[Interface bilingue](docs/BILINGUAL_CLI.fr.md) · [Outils de recherche](docs/RESEARCH_TOOLS.fr.md) · [Couverture linguistique et exceptions historiques](BILINGUALITY.md#français) · [Accueil du site local](docs/research/index-fr.html). Les fichiers HTML sont des sources fournies, pas un nouveau site déployé.
