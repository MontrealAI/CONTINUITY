# CONTINUITÉ Ω Masterclass 101, édition 1.0

[English](README.md) · **Français** · [Documentation](../README.md#français)

Huit leçons bilingues pour définir une promesse client, construire un autre moyen de la tenir et examiner preuves, coûts et financement. Séance proposée de 180 minutes, dont 10 minutes de pause. Aucun prérequis en programmation. Édition du 7 novembre 2026.

Lire d’abord les [limites, sources et conditions de réutilisation](STATUS.md#français). Les 164 fichiers et les octets du ZIP original sont conservés sans modification (le ZIP est stocké dans une enveloppe XZ sans perte).

## Lire et télécharger

- [PDF complet, 73 pages](edition-1/CONTINUITE_OMEGA_Masterclass_101_Cours_Complet_FR.pdf)
- [ZIP bilingue original dans une enveloppe XZ (.zip.xz)](CONTINUITY_OMEGA_MasterClass_101_Complete_Bilingual.zip.xz?raw=true)
- [Lecteur interactif hors ligne](edition-1/START_HERE.html) · [Instructions](edition-1/START_HERE.txt)

## Choisir un support

- **Apprendre:** [PDF, 35 pages](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Guide_Apprenant_FR.pdf) · [Word](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Guide_Apprenant_FR.docx)
- **Pratiquer:** [PDF, 18 pages](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Cahier_Exercices_FR.pdf) · [Word](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Cahier_Exercices_FR.docx)
- **Animer et corriger:** [PDF, 20 pages](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Guide_Animation_FR.pdf) · [Word](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Guide_Animation_FR.docx)
- **Consulter rapidement:** [PDF, 2 pages](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Aide_Memoire_FR.pdf)
- **Présenter:** [PDF, 24 pages](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Diapositives_FR.pdf) · [PowerPoint, 24 diapositives](edition-1/02_Francais/CONTINUITE_OMEGA_Masterclass_101_Diapositives_FR.pptx)
- [Prompts IA](edition-1/02_Francais/AI_Prompts_FR.txt)

Le cahier PDF séparé contient 108 champs vierges. Le PDF complet est une lecture continue, non un formulaire. Tester l’enregistrement avec un lecteur PDF compatible. Les diapositives comprennent des notes d’animation. Essayer les exercices avant les corrigés; les 12 questions et la grille sont formatives et non validées.

## Utilisation hors ligne et confidentialité

**Parcours recommandé sans programmation (macOS, Linux et Windows) :** utiliser **Code → Download ZIP** sur GitHub pour ce dépôt, extraire le téléchargement puis ouvrir `docs/masterclass-101/edition-1/START_HERE.html`. Garder tout le dossier du cours ensemble. Les PDF et fichiers Office restent téléchargeables directement ci-dessus.

Le ZIP fourni est stocké en `.zip.xz` dans une enveloppe XZ sans perte. Il s’agit du ZIP original comprimé en XZ, pas d’un ZIP renommé. Décompresser d’abord la couche XZ avec un utilitaire compatible, puis extraire le ZIP obtenu. Autre possibilité : restaurer le ZIP original exact avec Python 3 depuis la racine du dépôt téléchargé. Choisir un nouveau chemin hors de l’arborescence des sources :

- macOS/Linux : `python3 scripts/restore_masterclass_archive.py --output "$HOME/Downloads/CONTINUITY_OMEGA_MasterClass_101_Complete_Bilingual.zip"`
- Windows PowerShell, avec le lanceur Python installé : `py -3 scripts/restore_masterclass_archive.py --output "$env:USERPROFILE\Downloads\CONTINUITY_OMEGA_MasterClass_101_Complete_Bilingual.zip"`

La bibliothèque standard Python suffit; aucune commande `xz` préinstallée n’est supposée. Le dossier de destination doit déjà exister. Si le fichier existe, choisir un autre nom sans l’écraser. L’outil vérifie l’empreinte exacte du ZIP original et refuse tout écrasement. Le [manifeste](IMPORT_MANIFEST.json) consigne les identités de l’enveloppe et de l’original.

Extraire tout le ZIP du cours ainsi obtenu, garder les dossiers ensemble et ouvrir `START_HERE.html` dans un navigateur. GitHub affiche le code HTML; aucun nouveau site public n’est déployé. JavaScript est nécessaire pour le lecteur interactif, pas pour les PDF ou fichiers Office.

Le lecteur n’envoie aucune réponse. Il conserve réponses et progression dans le stockage local du navigateur lorsque celui-ci est disponible. Ce stockage peut être bloqué pour les fichiers locaux ou effacé par le navigateur. Exporter régulièrement le carnet en JSON et conserver ces sauvegardes en lieu sûr. L’importation remplace le carnet actuel; la réinitialisation perd les réponses. Changer de langue ne traduit pas les réponses. Si le presse-papiers est bloqué, copier les prompts manuellement. Imprimer ne produit que la vue courante.

Ne jamais publier ni commettre de cahiers remplis confidentiels, de carnets exportés ou de données client dans ce dépôt. Les prompts ne contactent pas automatiquement un service IA; toute copie vers un autre service relève de ses propres règles de confidentialité. Les liens externes s’ouvrent seulement à votre demande.

## Sources et vérification

- [Sources modifiables Markdown et JSON](edition-1/04_Editable_Sources) · [Sept figures par langue, 42 fichiers PDF/SVG/PNG](edition-1/06_Visuals)
- [Cinq articles originaux](edition-1/03_Original_Papers) · [Registre des sources](edition-1/SOURCE_REGISTER.json)
- [Index fourni](edition-1/PACKAGE_INDEX.json) · [Empreintes fournies](edition-1/SHA256SUMS.txt) · [Manifeste d’import](IMPORT_MANIFEST.json)
- [Collection documentaire distincte, édition 2](../collection/README.fr.md)

Depuis la racine du dépôt : `python3 scripts/verify_masterclass.py --language fr` (Python 3.10+, sans dépendance supplémentaire). Le contrôle vérifie fichiers, archive, index, sources, liens du lecteur et cohérence structurée. Il ne certifie ni apprentissage, ni résultat commercial, ni reprise opérationnelle. Les scripts historiques fournis ne sont pas exécutés.
