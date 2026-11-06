# CONTINUITY Ω

**English** · [Français](README.fr.md)

**Keep the promise.** A dedicated home for the CONTINUITY Ω research, offline synthetic business-continuity prototype, bilingual reading companion and visual materials by Vincent Boucher, MONTREAL.AI / QUEBEC.AI.

## Start here

- [Prototype and limitations](docs/continuity-omega/README.md) · [Quick start](docs/continuity-omega/QUICKSTART.md)
- [Research paper, edition 1.1.1](docs/continuity-omega-paper/README.md)
- [English paper PDF](docs/continuity-omega-paper/CONTINUITY_OMEGA.pdf) · [French paper PDF](docs/continuity-omega-paper/CONTINUITY_OMEGA_FR.pdf)
- [Read saved reports](docs/continuity-omega/OUTPUTS.md) · [Proposed real pilot](docs/continuity-omega/REAL_PILOT.md)
- [Original English web reader](https://montrealai.github.io/AGI-Alpha-Invention-Flywheel-Lab/continuity-omega.html) · [Original French web reader](https://montrealai.github.io/AGI-Alpha-Invention-Flywheel-Lab/continuity-omega-fr.html)
- [Original bilingual publication](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/releases/tag/continuity-omega-v1.1.1) · [Original reading companion](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/releases/tag/continuity-omega-reading-v1.0.1)

## Run locally

Python 3.10+; no packages, network, API keys or paid services are needed for the prototype.

```sh
python3 -m continuity_omega demo --case nominal --out /tmp/continuity-new-example
python3 -m continuity_omega verify --in-dir /tmp/continuity-new-example
python3 scripts/continuity_passport.py --in-dir /tmp/continuity-new-example --language en
python3 -m unittest discover -s tests -p 'test_continuity*.py' -v
python3 scripts/verify_copy.py
```

Choose a new output directory. For French reports, use `--language fr`. The reader displays saved records; it does not perform a fresh audit. See the paper guide for separate TeX build and pinned historical reproduction requirements.

## Copy and publication boundary

This repository begins with a byte-preserved copy of 78 dedicated files from [Lab commit de6839a](https://github.com/MontrealAI/AGI-Alpha-Invention-Flywheel-Lab/tree/de6839a4da2275dbe4cda00c2d3b5625210e02c5). [PROVENANCE.json](PROVENANCE.json) lists every copied path, SHA-256 and Git blob. [MIGRATION.md](MIGRATION.md) explains the boundary.

The original repository, papers, releases, links and ongoing work remain unchanged. This copy does not deprecate or replace that work. Published manifests, source pins, citations and original URLs retain their historical meaning. Website sources and media are preserved under `docs/research/`; their research-library navigation belongs to the original site. No new Pages deployment or duplicate historical release is created here.

**Research prototype only:** authored synthetic inputs, no real recovery, supplier reservation, customer delivery, revenue or external certification. The original checker weaknesses and counterexamples remain disclosed. This copy does not integrate the separately proposed PR #279 hardening or qualify it. Same-authorship separate code paths are not third-party assurance.

No new license is asserted: the source snapshot contains no root license, and existing notices and authorship are preserved. Public availability alone does not grant additional reuse rights.
