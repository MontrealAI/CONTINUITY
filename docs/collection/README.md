# CONTINUITY Ω bilingual collection, edition 2

**English** · [Français](README.fr.md) · [Documentation](../README.md#english) · [Repository home](../../README.md)

Five volumes in each language, with complete PDFs, editable Word files, fillable workbooks, an offline reader, sources, figures and five original papers. Edition dated 7 November 2026.

**Read the [collection status](STATUS.md#english) first.** All 106 files are preserved as supplied. Their snapshot predates the merged PRs #3 and #4; current repository documentation retains later qualifications and the unresolved local failure. This is an editorial collection, not new deployment or commercial-demand evidence.

## Read or download

- [Complete English PDF, 48 pages](edition-2/CONTINUITY_OMEGA_Complete_Collection_EN.pdf)
- [Complete French PDF](edition-2/CONTINUITE_OMEGA_Collection_Complete_FR.pdf)
- [Complete bilingual ZIP, 6.8 MB](CONTINUITY_OMEGA_Complete_Bilingual_Collection.zip?raw=true)
- [Offline bilingual HTML reader](edition-2/START_HERE.html) · [Instructions](edition-2/START_HERE.txt)

For offline reading, download and extract the ZIP, then open `CONTINUITY_OMEGA_Collection/START_HERE.html` in a browser. Keep the folders together. GitHub displays HTML source, not a deployed site. The reader supports language and volume selection and section search. Its workbook areas are reading examples and do not save answers.

To fill and save a workbook, download the separate volume 04 PDF and use a compatible PDF reader, or edit its Word version. Fields are blank; illustrative cases remain fictional. Verify saving in your chosen reader and keep sensitive completed responses out of the public repository.

## Choose a volume

| Volume | Reading | Formats |
| --- | --- | --- |
| 01 | **Keep the promise**<br>A clear introduction to CONTINUITY Ω | [PDF, 6 pages](edition-2/01_English/01_CONTINUITY_OMEGA_Executive_Brief_EN.pdf) · [Word](edition-2/01_English/01_CONTINUITY_OMEGA_Executive_Brief_EN.docx) · [Markdown](edition-2/04_Editable_Sources/01_CONTINUITY_OMEGA_Executive_Brief_EN.md) |
| 02 | **The story and the method**<br>From a disrupted order to a viable way to deliver | [PDF, 13 pages](edition-2/01_English/02_CONTINUITY_OMEGA_Complete_Guide_EN.pdf) · [Word](edition-2/01_English/02_CONTINUITY_OMEGA_Complete_Guide_EN.docx) · [Markdown](edition-2/04_Editable_Sources/02_CONTINUITY_OMEGA_Complete_Guide_EN.md) |
| 03 | **Make the pilot real**<br>One promise. A usable route. A result someone can accept. | [PDF, 10 pages](edition-2/01_English/03_CONTINUITY_OMEGA_Pilot_Playbook_EN.pdf) · [Word](edition-2/01_English/03_CONTINUITY_OMEGA_Pilot_Playbook_EN.docx) · [Markdown](edition-2/04_Editable_Sources/03_CONTINUITY_OMEGA_Pilot_Playbook_EN.md) |
| 04 | **Your pilot workbook**<br>Turn assumptions into agreements, observations and decisions | [PDF, 12 pages](edition-2/01_English/04_CONTINUITY_OMEGA_Field_Templates_EN.pdf) · [Word](edition-2/01_English/04_CONTINUITY_OMEGA_Field_Templates_EN.docx) · [Markdown](edition-2/04_Editable_Sources/04_CONTINUITY_OMEGA_Field_Templates_EN.md) |
| 05 | **Evidence you can check**<br>Understand the results, challenge the claim and see what proof comes next | [PDF, 10 pages](edition-2/01_English/05_CONTINUITY_OMEGA_Evidence_Dossier_EN.pdf) · [Word](edition-2/01_English/05_CONTINUITY_OMEGA_Evidence_Dossier_EN.docx) · [Markdown](edition-2/04_Editable_Sources/05_CONTINUITY_OMEGA_Evidence_Dossier_EN.md) |

## Sources and figures

- [Editable Markdown and JSON sources](edition-2/04_Editable_Sources)
- [Six figures per language, in PDF/SVG/PNG](edition-2/06_Visuals)
- [Source register](edition-2/SOURCE_REGISTER.json) · [Index and page counts](edition-2/COLLECTION_INDEX.json)
- [Historical repository snapshots](edition-2/05_Repository_Snapshot) · [Archive boundary](STATUS.md#english)

## Original papers

Preserved unchanged in their original languages, attributed to Vincent Boucher. The bilingual collection does not claim to translate every foundational paper.

- [CONTINUITY Ω](edition-2/03_Original_Papers/C1_CONTINUITY_OMEGA_Research_EN.pdf) · Research edition 1.1.1 · 6 November 2026
- [CONTINUITÉ Ω](edition-2/03_Original_Papers/C2_CONTINUITE_OMEGA_Recherche_FR.pdf) · Édition de recherche 1.1.1 · 6 novembre 2026
- [Transformational Intelligence](edition-2/03_Original_Papers/F1_Transformational_Intelligence.pdf) · Learning to Change the Game · October 2026
- [Invent the Economy](edition-2/03_Original_Papers/F2_Invent_the_Economy.pdf) · Transformational Intelligence for Creating Viable Markets · October 2026
- [ALPHA GENESIS FLYWHEEL Ω](edition-2/03_Original_Papers/F3_ALPHA_GENESIS_FLYWHEEL_OMEGA_v2.pdf) · Research edition 2.0 · 4 November 2026

## Verify the copy

```sh
python3 scripts/verify_collection.py --language en
```

Run from the repository root with Python 3.10+ and no additional dependencies. The check verifies the ZIP, all 106 extracted files, source hashes, index references, and local links in the reader and editable volumes. It does not rerun an experiment or certify scientific or commercial claims.

[Import manifest](IMPORT_MANIFEST.json) · [Supplied checksums](edition-2/CHECKSUMS.sha256) · [Status, rights and limitations](STATUS.md#english)
