# CONTINUITÉ Ω : collection bilingue, édition 2

[English](README.md) · **Français** · [Documentation](../README.md#français) · [Accueil](../../README.fr.md)

Cinq volumes dans chaque langue, avec PDF complets, fichiers Word modifiables, cahiers à remplir, lecteur hors ligne, sources, figures et cinq articles originaux. Édition du 7 novembre 2026.

**Lire d’abord [l’état de la collection](STATUS.md#français).** Les 106 fichiers sont conservés tels que fournis. Leur instantané précède la fusion des PR nº 3 et nº 4 ; les documents actuels du dépôt conservent les qualifications ultérieures et l’échec local non résolu. Cette collection est éditoriale, sans nouvelle preuve de déploiement ou de demande commerciale.

## Lire ou télécharger

- [PDF français complet, 48 pages](edition-2/CONTINUITE_OMEGA_Collection_Complete_FR.pdf)
- [PDF anglais complet](edition-2/CONTINUITY_OMEGA_Complete_Collection_EN.pdf)
- [Collection bilingue complète en ZIP, 6,8 Mo](CONTINUITY_OMEGA_Complete_Bilingual_Collection.zip?raw=true)
- [Lecteur HTML bilingue hors ligne](edition-2/START_HERE.html) · [Instructions](edition-2/START_HERE.txt)

Pour le lecteur hors ligne, télécharger et extraire le ZIP, puis ouvrir `CONTINUITY_OMEGA_Collection/START_HERE.html` dans un navigateur. Conserver les dossiers ensemble. GitHub affiche le code HTML, pas un site déployé. Le lecteur permet de changer de langue et de volume et de rechercher des sections. Ses zones de cahier servent à la lecture et ne sauvegardent pas les réponses.

Pour remplir et enregistrer un cahier, télécharger le PDF séparé du volume 04 et utiliser un lecteur PDF compatible, ou modifier sa version Word. Les champs sont vierges ; les cas illustratifs restent fictifs. Vérifier la sauvegarde dans le lecteur choisi et conserver les réponses sensibles hors du dépôt public.

## Choisir un volume

| Volume | Lecture | Formats |
| --- | --- | --- |
| 01 | **Tenir parole**<br>Une introduction claire à CONTINUITÉ Ω | [PDF, 6 pages](edition-2/02_Francais/01_CONTINUITE_OMEGA_Synthese_FR.pdf) · [Word](edition-2/02_Francais/01_CONTINUITE_OMEGA_Synthese_FR.docx) · [Markdown](edition-2/04_Editable_Sources/01_CONTINUITE_OMEGA_Synthese_FR.md) |
| 02 | **L’histoire et la méthode**<br>De la commande interrompue à une solution de livraison viable | [PDF, 13 pages](edition-2/02_Francais/02_CONTINUITE_OMEGA_Guide_FR.pdf) · [Word](edition-2/02_Francais/02_CONTINUITE_OMEGA_Guide_FR.docx) · [Markdown](edition-2/04_Editable_Sources/02_CONTINUITE_OMEGA_Guide_FR.md) |
| 03 | **Réaliser le pilote**<br>Une promesse. Une voie utilisable. Un résultat acceptable. | [PDF, 10 pages](edition-2/02_Francais/03_CONTINUITE_OMEGA_Guide_Pilote_FR.pdf) · [Word](edition-2/02_Francais/03_CONTINUITE_OMEGA_Guide_Pilote_FR.docx) · [Markdown](edition-2/04_Editable_Sources/03_CONTINUITE_OMEGA_Guide_Pilote_FR.md) |
| 04 | **Cahier du pilote**<br>Transformer les hypothèses en accords, observations et décisions | [PDF, 12 pages](edition-2/02_Francais/04_CONTINUITE_OMEGA_Fiches_Pratiques_FR.pdf) · [Word](edition-2/02_Francais/04_CONTINUITE_OMEGA_Fiches_Pratiques_FR.docx) · [Markdown](edition-2/04_Editable_Sources/04_CONTINUITE_OMEGA_Fiches_Pratiques_FR.md) |
| 05 | **Des preuves vérifiables**<br>Comprendre les résultats, éprouver l’affirmation et savoir quelle preuve établir ensuite | [PDF, 10 pages](edition-2/02_Francais/05_CONTINUITE_OMEGA_Dossier_Preuve_FR.pdf) · [Word](edition-2/02_Francais/05_CONTINUITE_OMEGA_Dossier_Preuve_FR.docx) · [Markdown](edition-2/04_Editable_Sources/05_CONTINUITE_OMEGA_Dossier_Preuve_FR.md) |

## Sources et figures

- [Sources modifiables Markdown et JSON](edition-2/04_Editable_Sources)
- [Six figures dans chaque langue, en PDF/SVG/PNG](edition-2/06_Visuals)
- [Registre des sources](edition-2/SOURCE_REGISTER.json) · [Index et pagination](edition-2/COLLECTION_INDEX.json)
- [Instantanés historiques du dépôt](edition-2/05_Repository_Snapshot) · [Périmètre de ces archives](STATUS.md#français)

## Articles originaux

Conservés sans modification dans leur langue d’origine, avec attribution à Vincent Boucher. La collection bilingue ne prétend pas traduire chacun des articles fondateurs.

- [CONTINUITY Ω](edition-2/03_Original_Papers/C1_CONTINUITY_OMEGA_Research_EN.pdf) · Research edition 1.1.1 · 6 November 2026
- [CONTINUITÉ Ω](edition-2/03_Original_Papers/C2_CONTINUITE_OMEGA_Recherche_FR.pdf) · Édition de recherche 1.1.1 · 6 novembre 2026
- [Transformational Intelligence](edition-2/03_Original_Papers/F1_Transformational_Intelligence.pdf) · Learning to Change the Game · October 2026
- [Invent the Economy](edition-2/03_Original_Papers/F2_Invent_the_Economy.pdf) · Transformational Intelligence for Creating Viable Markets · October 2026
- [ALPHA GENESIS FLYWHEEL Ω](edition-2/03_Original_Papers/F3_ALPHA_GENESIS_FLYWHEEL_OMEGA_v2.pdf) · Research edition 2.0 · 4 November 2026

## Vérifier la copie

```sh
python3 scripts/verify_collection.py --language fr
```

Exécuter depuis la racine du dépôt, avec Python 3.10 ou ultérieur, sans dépendance supplémentaire. Le contrôle vérifie le ZIP, les 106 fichiers extraits, les empreintes sources, les références de l’index, les liens locaux du lecteur et des volumes modifiables. Il ne réexécute pas une expérience et ne certifie pas les affirmations scientifiques ou commerciales.

[Manifeste d’import](IMPORT_MANIFEST.json) · [Empreintes fournies](edition-2/CHECKSUMS.sha256) · [État, droits et limites](STATUS.md#français)

[Apprendre avec la Masterclass 101 distincte en huit leçons](../masterclass-101/README.fr.md).
