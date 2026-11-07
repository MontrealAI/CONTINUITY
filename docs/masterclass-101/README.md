# CONTINUITY Ω MasterClass 101, edition 1.0

**English** · [Français](README.fr.md) · [Documentation](../README.md#english)

Eight bilingual lessons on defining a customer promise, constructing an alternative way to deliver, and examining evidence, costs and funding. Suggested live session: 180 minutes including a 10-minute break. No coding prerequisite. Edition dated 7 November 2026.

Read the [limitations, sources and reuse boundary](STATUS.md#english) first. All 164 supplied files and the original ZIP bytes are preserved unchanged (the ZIP is stored in a lossless XZ wrapper).

## Read and download

- [Complete PDF, 73 pages](edition-1/CONTINUITY_OMEGA_MasterClass_101_Complete_Course_EN.pdf)
- [Original bilingual ZIP in an XZ wrapper (.zip.xz)](CONTINUITY_OMEGA_MasterClass_101_Complete_Bilingual.zip.xz?raw=true)
- [Interactive offline reader](edition-1/START_HERE.html) · [Instructions](edition-1/START_HERE.txt)

## Choose a format

- **Learn:** [PDF, 35 pages](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Learner_Guide_EN.pdf) · [Word](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Learner_Guide_EN.docx)
- **Practise:** [PDF, 18 pages](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Workbook_EN.pdf) · [Word](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Workbook_EN.docx)
- **Facilitate and check answers:** [PDF, 20 pages](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Facilitator_Guide_EN.pdf) · [Word](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Facilitator_Guide_EN.docx)
- **Quick reference:** [PDF, 2 pages](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Quick_Reference_EN.pdf)
- **Present:** [PDF, 24 pages](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Slides_EN.pdf) · [PowerPoint, 24 slides](edition-1/01_English/CONTINUITY_OMEGA_MasterClass_101_Slides_EN.pptx)
- [AI prompts](edition-1/01_English/AI_Prompts_EN.txt)

The separate workbook PDF contains 108 blank fields. The complete PDF is a continuous reading edition, not an interactive form. Test saving with a form-capable PDF reader. Slides include speaker notes. Attempt exercises before reading the answers; the 12 questions and rubric are formative, unvalidated learning tools.

## Offline use and privacy

**Recommended no-code path (macOS, Linux and Windows):** use GitHub’s **Code → Download ZIP** for this repository, extract it, and open `docs/masterclass-101/edition-1/START_HERE.html`. Keep the full course directory together. Individual PDF/Office downloads above remain directly usable.

The supplied course ZIP is stored as `.zip.xz` in a lossless XZ wrapper. This is an XZ-compressed original ZIP, not a renamed ZIP. Decompress the XZ layer with an XZ-capable archive utility, then extract the resulting ZIP. Alternatively, reconstruct the exact original ZIP with Python 3, from the downloaded repository’s root. Choose a new output path outside the source tree:

- macOS/Linux: `python3 scripts/restore_masterclass_archive.py --output "$HOME/Downloads/CONTINUITY_OMEGA_MasterClass_101_Complete_Bilingual.zip"`
- Windows PowerShell, with the Python launcher installed: `py -3 scripts/restore_masterclass_archive.py --output "$env:USERPROFILE\Downloads\CONTINUITY_OMEGA_MasterClass_101_Complete_Bilingual.zip"`

Python’s standard library is sufficient; no `xz` command is assumed to be installed. The destination folder must already exist. If the output already exists, select another filename rather than overwriting it. The helper verifies the exact original ZIP hash and refuses to overwrite an existing output. The [manifest](IMPORT_MANIFEST.json) records both stored-wrapper and original identities.

Extract the resulting whole course ZIP, keep its folders together and open `START_HERE.html` in a browser. GitHub displays HTML source; this import deploys no new public site. JavaScript is needed for the interactive reader, not for PDFs or Office files.

The reader sends no answers. It stores answers and progress in browser local storage when available. Storage may be blocked for local files or cleared by the browser. Export the notebook as JSON regularly and keep those backups safe. Import replaces the current notebook; reset loses answers. Switching languages does not translate answers. If clipboard access is blocked, copy prompts manually. Print produces only the current view.

Never publish or commit confidential completed workbooks, exported notebooks or customer data to this repository. Prompts do not automatically contact an AI service; copying them into another service is subject to that service’s privacy rules. External links open only when you choose them.

## Sources and verification

- [Editable Markdown and JSON sources](edition-1/04_Editable_Sources) · [Seven figures per language, 42 PDF/SVG/PNG files](edition-1/06_Visuals)
- [Five original papers](edition-1/03_Original_Papers) · [Source register](edition-1/SOURCE_REGISTER.json)
- [Supplied index](edition-1/PACKAGE_INDEX.json) · [Supplied checksums](edition-1/SHA256SUMS.txt) · [Import manifest](IMPORT_MANIFEST.json)
- [Separate document collection, edition 2](../collection/README.md)

From the repository root: `python3 scripts/verify_masterclass.py --language en` (Python 3.10+, no additional dependencies). This checks files, archive, index, sources, reader links and structured consistency. It does not certify learning, commercial success or operational recovery. Supplied historical scripts are not executed.
