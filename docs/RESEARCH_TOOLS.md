# Research maintenance tools

**English** · [Français](RESEARCH_TOOLS.fr.md) · [Repository home](../README.md)

Use `scripts/research.py` from the repository root for English or French help, argument validation, execution notices and success/failure summaries. Python 3.10+ is required. The interface calls only the six supported historical paper tools and checks the SHA-256 identities of their seven Python source files against `docs/continuity-omega-paper/PUBLICATION.json` before execution.

```sh
python3 scripts/research.py --language en --help
python3 scripts/research.py --language fr --help
```

## Two different language choices

- `--language en` or `--language fr` selects the **maintenance interface language**, including help and validation errors. The default is English. This option works before or after the command.
- `build --paper-language en`, `fr` or `all` selects the **manuscripts to compile**. The default is `all`, independently of the interface language.
- Command names, option names, paths, identifiers, machine-readable evidence and historical source bytes stay unchanged. No language selection changes an experimental result or a historical failure.

For example, French guidance can accompany an English-only build:

```sh
python3 scripts/research.py --language fr build --paper-language en
```

## Raw historical diagnostics are not translated

The interface provides a localized outcome, not a translation of the old scripts’ detailed diagnostics. The historical tools and their dependencies can emit English or bilingual technical text and stable JSON keys. To retain that exact technical output, request a new log file explicitly:

```sh
python3 scripts/research.py --language en verify --raw-log /tmp/continuity-verify-NEW.log
```

The log combines the tool’s standard output and standard error without translating their text. Its parent directory must already exist. The path must be absolute, new, outside this repository, outside any supplied source snapshot, and outside the requested output directory. Existing files and symbolic links are refused. Without `--raw-log`, the tool’s console output is discarded; the localized summary remains visible. This option does not suppress logs and evidence that the historical tool normally writes in its own output directory.

On failure, the interface reports the exit code and the requested output/log locations without presenting an incomplete run as successful. Inspect the raw log or the tool’s output evidence for the technical cause. To rerun a command that creates output, choose another new output directory and another new log file. Failure outputs are not erased.

## Supported operations

### Verify the historical publication

```sh
python3 scripts/research.py --language en verify --raw-log /tmp/continuity-verify-NEW.log
python3 scripts/research.py --language en verify --check-build --raw-log /tmp/continuity-build-check-NEW.log
```

`verify` checks publication identities, recorded scope, authored arithmetic and translation structure. It requires Poppler’s `pdfinfo` and `pdftotext`. It does not rerun the source prototypes, authenticate the supplied scenario, certify real cyber resilience or establish commerce.

`--check-build` additionally compares the extracted text of **both** rebuilt manuscripts with their respective canonical PDFs. Build both languages first. This option does not itself launch a TeX build.

### Build manuscripts without publication

```sh
python3 scripts/research.py --language en build --paper-language all --raw-log /tmp/continuity-build-NEW.log
```

The historical builder always writes generated files into `docs/continuity-omega-paper/build/`. Existing generated build files may be replaced. This fixed output location is displayed before execution; `--output` is not a build option. Symbolic links in the build directory are refused by the interface. The canonical PDFs and the original Lab repository are not updated. `--publish` is deliberately unsupported.

Requirements are `pdflatex` and the TeX packages listed in the [paper’s build guide](continuity-omega-paper/README.md#build-and-verify), including French Babel for French builds. TeX shell escape remains disabled. A successful build is not a new reviewed edition or a publication action.

### Package the historical publication

```sh
python3 scripts/research.py --language en package --output /tmp/continuity-package-NEW --raw-log /tmp/continuity-package-NEW.log
```

The original packager runs the publication verifier and produces both canonical PDFs and `CONTINUITY_OMEGA_SOURCE.zip`. It needs the verification dependencies above. The output must be a new absolute directory outside this repository. The ZIP preserves the historical publication inventory; it does **not** include this new interface, its guides or its tests. No remote release is created.

### Reproduce the pinned synthetic engineering

Offline, supply both previously downloaded historical source snapshots:

```sh
python3 scripts/research.py --language en reproduce --output /tmp/continuity-reproduction-NEW --source277 /absolute/pinned/source277 --source278 /absolute/pinned/source278 --raw-log /tmp/continuity-reproduction-NEW.log
```

To allow downloads of missing pinned public source files, opt in explicitly:

```sh
python3 scripts/research.py --language en reproduce --download-sources --output /tmp/continuity-reproduction-NEW --raw-log /tmp/continuity-reproduction-NEW.log
```

Without both local snapshots or `--download-sources`, invocation is refused before execution. With one local snapshot and the download option, only the missing snapshot is downloaded. The historical reproducer verifies both SHA-256 and Git blob identities before running copied source code; all generated sources, logs and fixtures go into the new output directory. Sources must match the paper’s pinned revisions, not the current localized prototype.

A successful reproduction means the pinned synthetic results were reproduced. It is not a live recovery, physical delivery, payment, independent certification or qualification of a later repair.

### Replay the historical counterexamples

```sh
python3 scripts/research.py --language en counterexamples --source278 /absolute/pinned/source278 --output /tmp/continuity-counterexamples-NEW --raw-log /tmp/continuity-counterexamples-NEW.log
```

The local historical PR 278 snapshot is required and its identities are verified by the original tool. No download option is available for this command. A successful exit means the five expected observations, including the checker weaknesses, were reproduced. **It does not mean the checker is qualified.** The separate historical 29-test suite is not rerun by this command.

### Compute the authored pooling example

```sh
python3 scripts/research.py --language en pooling --raw-log /tmp/continuity-pooling-NEW.log
```

This standard-library-only calculation uses exact arithmetic. Its original numerical JSON is in the requested raw log. The example requires at least three buyers to cover costs while simultaneous capacity can serve at most two; no buyer count meets both conditions. It establishes no actual prices, demand, scheduling or commerce.

## Output and execution boundaries

- `package`, `reproduce` and `counterexamples` require `--output`: a new absolute directory outside this repository and any supplied source snapshot. Parent directories may be created by the original tool. Existing output directories are never reused or removed.
- `build` uses the fixed generated-file directory described above. `verify` and `pooling` create no output directory; the optional raw log is separate.
- Arguments are validated in the selected language. Unknown commands, unrelated options, duplicate options, arbitrary command strings, passthrough arguments and `--publish` are rejected. The interface launches a fixed script with an argument list, never a shell command, and disables Python bytecode writes and user-site imports.
- Historical scripts and their imported local helpers must retain their published identities. A mismatch is refused before launch; restore the published bytes instead of editing the publication manifest to bypass the check.
- Exit `0` means the selected historical command completed successfully within its stated scope. The interface returns `2` for its own invocation/validation errors, `1` if it cannot launch the tool, and `130` when interrupted. Historical nonzero exit codes are preserved; a signal termination is represented as `128 + signal`. An underlying command can also return `1` or `2`.

## Lightweight interface tests

```sh
python3 -B -m unittest discover -s tests -p 'test_research_tools.py' -v
```

The focused tests exercise both languages, supported command routing, output protection, manifest checks, raw logs and failure handling. Expensive or networked tools are mocked; one real pooling calculation runs offline. These tests do not perform a TeX build, download pinned sources, publish anything, or establish new scientific results. They complement, rather than replace, the [historical paper verification](continuity-omega-paper/README.md) and the repository’s provenance checks.

The complete repository test suite (`python3 -m unittest discover -s tests -p 'test_*.py' -v`) additionally requires Node.js for website JavaScript checks. No npm packages are needed. The prototype and focused Python interface tests remain Python-only.
