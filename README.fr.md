# CONTINUITÉ Ω

[English](README.md) · **Français**

**Tenir parole.** Un dépôt consacré à la recherche CONTINUITÉ Ω, au prototype synthétique hors ligne de continuité des engagements, au compagnon de lecture bilingue et aux ressources visuelles de Vincent Boucher, MONTREAL.AI / QUEBEC.AI.

## Commencer

- [Prototype et limites](docs/continuity-omega/README.fr.md) · [Démarrage rapide](docs/continuity-omega/QUICKSTART.fr.md)
- [Article, édition 1.1.1](docs/continuity-omega-paper/README.fr.md)
- [Article français en PDF](docs/continuity-omega-paper/CONTINUITY_OMEGA_FR.pdf) · [Article anglais en PDF](docs/continuity-omega-paper/CONTINUITY_OMEGA.pdf)
- [Lire les rapports enregistrés](docs/continuity-omega/OUTPUTS.fr.md) · [Pilote réel proposé](docs/continuity-omega/REAL_PILOT.fr.md)
- [Lecteur français original](https://montrealai.github.io/AGI-Alpha-Invention-Flywheel-Lab/continuity-omega-fr.html) · [Lecteur anglais original](https://montrealai.github.io/AGI-Alpha-Invention-Flywheel-Lab/continuity-omega.html)
- [Publication bilingue originale](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/releases/tag/continuity-omega-v1.1.1) · [Compagnon original](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/releases/tag/continuity-omega-reading-v1.0.1)

## Exécution locale

Python 3.10 ou ultérieur. Le prototype ne nécessite aucun paquet supplémentaire, accès réseau, clé API ou service payant.

```sh
python3 -m continuity_omega demo --case nominal --out /tmp/continuite-nouvel-exemple
python3 -m continuity_omega verify --in-dir /tmp/continuite-nouvel-exemple
python3 scripts/continuity_passport.py --in-dir /tmp/continuite-nouvel-exemple --language fr
python3 -m unittest discover -s tests -p 'test_continuity*.py' -v
python3 scripts/verify_copy.py
```

Choisir un nouveau répertoire de sortie. Le lecteur affiche des enregistrements sauvegardés, sans nouvel audit. Le guide de l’article décrit les exigences TeX et la reproduction historique séparées.

## Périmètre de la copie

Les 78 fichiers dédiés sont copiés sans changement depuis [le commit de6839a du dépôt Lab](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/tree/de6839a4da2275dbe4cda00c2d3b5625210e02c5). [PROVENANCE.json](PROVENANCE.json) fournit chemins et empreintes. Le dépôt original, les publications, les liens et les travaux en cours restent inchangés. Cette copie ne remplace ni ne déprécie ce travail.

Les sources web et médias sous `docs/research/` conservent la navigation du site original. Aucun nouveau site Pages ni doublon des publications historiques n’est créé ici. Les sources figées, citations et manifestes gardent leur portée historique.

**Prototype de recherche uniquement :** données synthétiques, sans reprise réelle, réservation fournisseur, livraison client, revenus ou certification externe. Les faiblesses du vérificateur et les contre-exemples restent documentés. Le renforcement proposé dans la PR #279 n’est ni intégré ni qualifié par cette copie.

Aucune nouvelle licence n’est déclarée : la source ne contient pas de licence à la racine. Les notices et attributions existantes sont préservées ; la disponibilité publique ne crée pas de droits supplémentaires.
