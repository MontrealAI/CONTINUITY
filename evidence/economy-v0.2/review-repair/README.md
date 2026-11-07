# CONTINUITY Ω — Post-review repair evidence

[Français](#français) · [Qualification index](QUALIFICATION.json) · [Repair report](../../../docs/economy/REVIEW_REPAIR.md) · [Preserved review](REVIEW.json)

## English

This package records the aggregate experiment-coverage repair at **`f9e56c7dd9627b322406e05c53b4f6537d434262`**. It preserves favorable and unfavorable observations separately. A `PASSED` assertion concerns its stated test; it does not establish method superiority or commercial demand.

| Observation | Retained result |
| --- | --- |
| Two incomplete experiments: all three roles alias one base demo or one base comparison | Old source `46c2e0b2123cb56f24dd956b2dbfb79a7f7fbecd` accepted both, exit 0. The counterexample assertions passed; the old checker's coverage qualification **failed**. |
| Same counterexample inputs after repair | **1,955 files unchanged**; both cases refused with exit 2 / `SUITE_COVERAGE` in English and French. The initial AFTER record identifies an uncommitted repair; separate clean-source records repeat the refusals. |
| Corrected source regression and hosted checks | **436 tests passed**; **six completed successful hosted checks** at the exact corrected commit. These are observations of that source, not certification of a later integration commit. |
| Fresh checks of original historical evidence and downloaded CI evidence | Both **PASSED**. CI evidence has **28 base, 4 successor and 26 challenge records**. |
| One preregistered `/tmp` complete confirmation | Execution and separate fresh verification **PASSED**, with **28 / 4 / 26** records; all **3,024 copied files** matched. |
| Separate local complete replay and fresh verification | Both **FAILED**, exit 3. The `constructed-continuity` / `conventional` cell's qualified outcome and service feasibility remain `NOT_ESTABLISHED`. |

The failed replay retains a main-database/WAL inconsistency: the main-only view matches the captured digest, while the WAL-aware view lacks the final 100-unit capacity action. Why the stale WAL remained or reappeared is unresolved. One bounded lifecycle probe did not reproduce it. The passing CI and `/tmp` observations do not resolve or reclassify this failure. The original 42-file successor freeze remains historical; this later repair changes `continuity_economy/suite.py`, leaving 41 frozen files identical. No new held-out successor or pooled timing result is claimed.

### Files and provenance

[BUILD.json](BUILD.json) and [EXTRACTION.json](EXTRACTION.json) are byte-for-byte copies of the original records, including historical absolute paths. [QUALIFICATION.json](QUALIFICATION.json) maps the observations to hashed archive members. [final-audit/AUDIT.json](final-audit/AUDIT.json) and its unchanged stdout/stderr files retain the later independent checks: 12 suite tests passed, the extracted `/tmp` confirmation passed, the failed replay still failed, and the aliased demo was refused. These audit files are outside the sealed archive; verify them with [SHA256SUMS](final-audit/SHA256SUMS).

The sealed [coverage-repair.tar.xz](coverage-repair.tar.xz) is **4,534,760 bytes**. SHA-256:

```text
15fa4213b47b063074f77a416d20a5c0fd2cbf1c200403da33ecac483bfe2b01
```

It contains **11,200 payload files plus `MANIFEST.json`**, totaling **978,022,718 payload bytes** after decompression. The manifest SHA-256 is `8603045b20f284d6a423801277a721f1c58f8a1c24fa72491f75657c2eb978b2`.

| Archive path | Evidence |
| --- | --- |
| `before/` | Predeclaration, copied counterexample inputs, old source, original outputs and inventories |
| `after/` | Focused regression attempts and explicit uncommitted-repair checks of unchanged inputs |
| `qualification/` | Clean-source plan, six hosted check records, 436-test log, positive historical check, retained failed replay and fresh refusals |
| `ci-positive/extracted/complete/` | Downloaded complete CI evidence; download and fresh-verification records are in `ci-positive/` |
| `tmp-confirmation/complete/` | Single bounded positive confirmation; predeclaration, result and copy manifest are in `tmp-confirmation/` |
| `digest-investigation/`, `finalization-investigation/` | Preserved failed bytes, diagnostic scripts, distinct database views and unsuccessful reproduction probe |
| `packaging/`, `run_qualification.py` | Original packaging and qualification scripts |

The historical complete evidence remains in [../attempts.tar.xz](../attempts.tar.xz), with instructions in [../README.md](../README.md). It is not duplicated here.

## Français

### CONTINUITÉ Ω — Preuves de la correction après revue

[English](#english) · [Index de qualification](QUALIFICATION.json) · [Rapport de correction](../../../docs/economy/REVIEW_REPAIR.fr.md) · [Revue conservée](REVIEW.json)

Ce dossier documente la correction du contrôle agrégé de couverture à **`f9e56c7dd9627b322406e05c53b4f6537d434262`**. Les observations favorables et défavorables restent distinctes. `PASSED` désigne la réussite de l’assertion indiquée, sans établir une supériorité de méthode ni une demande commerciale.

| Observation | Résultat conservé |
| --- | --- |
| Deux expériences incomplètes : les trois rôles désignent une seule démonstration de base ou une seule comparaison de base | L’ancienne source `46c2e0b2123cb56f24dd956b2dbfb79a7f7fbecd` accepte les deux, code 0. Les assertions des contre-exemples réussissent ; la qualification de couverture de l’ancien vérificateur **échoue**. |
| Mêmes entrées après correction | **1 955 fichiers inchangés** ; les deux cas sont refusés avec le code 2 / `SUITE_COVERAGE`, en anglais et en français. Le premier dossier APRÈS identifie la correction non encore enregistrée dans un commit ; des dossiers distincts reprennent les refus depuis la source propre. |
| Régression et contrôles hébergés de la source corrigée | **436 tests réussis**, **six contrôles hébergés terminés avec succès** au commit corrigé exact. Cela ne certifie pas un commit d’intégration ultérieur. |
| Vérifications fraîches des preuves historiques et CI téléchargées | Les deux sont **PASSED**. Les preuves CI comportent **28 enregistrements de base, 4 du successeur et 26 épreuves**. |
| Une confirmation complète préenregistrée sous `/tmp` | Exécution et vérification fraîche distincte **PASSED**, avec **28 / 4 / 26** enregistrements ; les **3 024 fichiers copiés** correspondent. |
| Reproduction locale complète distincte et vérification fraîche | Les deux sont **FAILED**, code 3. Le résultat qualifié et la faisabilité du service de la cellule `constructed-continuity` / `conventional` restent `NOT_ESTABLISHED`. |

La reproduction échouée conserve une incohérence entre la base principale et le journal WAL : la base principale seule correspond à l’empreinte capturée, tandis que la vue avec WAL omet la dernière action de capacité de 100 unités. La raison de la persistance ou de la réapparition de cet ancien WAL reste inconnue. Un essai diagnostique borné n’a pas reproduit l’anomalie. Les réussites CI et `/tmp` ne résolvent ni ne reclassent cet échec. Le gel initial de 42 fichiers demeure une observation historique ; cette correction ultérieure modifie `continuity_economy/suite.py`, les 41 autres fichiers restant identiques. Aucun nouveau successeur tenu à l’écart ni résultat de durées fusionnées n’est revendiqué.

### Fichiers et provenance

[BUILD.json](BUILD.json) et [EXTRACTION.json](EXTRACTION.json) reproduisent les dossiers originaux octet pour octet, y compris leurs chemins absolus historiques. [QUALIFICATION.json](QUALIFICATION.json) relie chaque observation aux membres de l’archive et à leurs empreintes. [final-audit/AUDIT.json](final-audit/AUDIT.json), avec les sorties et erreurs inchangées, conserve les contrôles indépendants ultérieurs : 12 tests réussis, confirmation `/tmp` extraite réussie, reproduction échouée toujours en échec et démonstration réutilisée refusée. Ces fichiers sont extérieurs à l’archive scellée ; [SHA256SUMS](final-audit/SHA256SUMS) permet de les vérifier.

L’[archive scellée](coverage-repair.tar.xz) compte **4 534 760 octets**, avec l’empreinte SHA-256 `15fa4213b47b063074f77a416d20a5c0fd2cbf1c200403da33ecac483bfe2b01`. Elle contient **11 200 fichiers de charge utile et `MANIFEST.json`**, soit **978 022 718 octets** de charge utile décompressée. L’empreinte SHA-256 du manifeste est `8603045b20f284d6a423801277a721f1c58f8a1c24fa72491f75657c2eb978b2`.

| Chemin dans l’archive | Preuves |
| --- | --- |
| `before/` | Déclaration préalable, copies des entrées des contre-exemples, ancienne source, sorties initiales et inventaires |
| `after/` | Tentatives de régression ciblées et contrôles explicites des entrées inchangées avec la correction non encore enregistrée dans un commit |
| `qualification/` | Plan depuis la source propre, six contrôles hébergés, journal des 436 tests, contrôle historique positif, reproduction échouée conservée et refus vérifiés à nouveau |
| `ci-positive/extracted/complete/` | Preuves CI complètes téléchargées ; métadonnées de téléchargement et vérification fraîche sous `ci-positive/` |
| `tmp-confirmation/complete/` | Unique confirmation positive bornée ; déclaration préalable, résultat et manifeste de copie sous `tmp-confirmation/` |
| `digest-investigation/`, `finalization-investigation/` | Octets échoués conservés, scripts diagnostiques, vues distinctes des bases et essai n’ayant pas reproduit l’anomalie |
| `packaging/`, `run_qualification.py` | Scripts initiaux d’assemblage et de qualification |

Les preuves historiques complètes restent dans [../attempts.tar.xz](../attempts.tar.xz), avec les instructions dans [../README.md](../README.md#français). Elles ne sont pas dupliquées ici.

## Reproduce / Reproduire

Run these commands from the root of a Git checkout containing the recorded corrected commit. They extract into new temporary directories and select that exact source without changing Git refs. The repair payload alone needs 978,022,718 bytes after decompression; allow additional space for the historical payload, source and verification logs. Python 3.10 or later is required, matching the repository setup. The original qualification environment is recorded in `qualification/PREDECLARATION.json`.

Exécuter depuis la racine d’une copie Git contenant le commit corrigé consigné. Les commandes extraient les fichiers dans de nouveaux répertoires temporaires et sélectionnent cette source exacte sans changer les références Git. La charge utile de correction seule occupe 978 022 718 octets décompressés ; prévoir également l’espace des preuves historiques, de la source et des journaux. Python 3.10 ou ultérieur est requis, conformément à l’installation du dépôt. L’environnement initial figure dans `qualification/PREDECLARATION.json`.

```sh
set -eu
export REPAIR_EVIDENCE="$(mktemp -d /tmp/continuity-repair-evidence.XXXXXX)"
export HISTORICAL_EVIDENCE="$(mktemp -d /tmp/continuity-historical-evidence.XXXXXX)"
export REPAIR_SOURCE="$(mktemp -d /tmp/continuity-repair-source.XXXXXX)"
export REPAIR_LOGS="$(mktemp -d /tmp/continuity-repair-logs.XXXXXX)"
python3 - <<'PY'
from pathlib import Path
import hashlib
archives = {
    'evidence/economy-v0.2/review-repair/coverage-repair.tar.xz':
        '15fa4213b47b063074f77a416d20a5c0fd2cbf1c200403da33ecac483bfe2b01',
    'evidence/economy-v0.2/attempts.tar.xz':
        'a96c6b7c25e0e17ed1c1f7d0fcf13b70c338159ae9c10c5f825699b9e186db25',
}
for name, expected in archives.items():
    digest = hashlib.sha256()
    with Path(name).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    assert digest.hexdigest() == expected, name
    print('SHA256 OK:', name)
PY
tar --no-same-owner -xJf evidence/economy-v0.2/review-repair/coverage-repair.tar.xz -C "$REPAIR_EVIDENCE"
tar --no-same-owner -xJf evidence/economy-v0.2/attempts.tar.xz -C "$HISTORICAL_EVIDENCE"
git archive f9e56c7dd9627b322406e05c53b4f6537d434262 | tar -xf - -C "$REPAIR_SOURCE"
python3 - <<'PY'
from pathlib import Path
import hashlib, json, os
root = Path(os.environ['REPAIR_EVIDENCE'])
manifest_bytes = (root / 'MANIFEST.json').read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest() == '8603045b20f284d6a423801277a721f1c58f8a1c24fa72491f75657c2eb978b2'
files = json.loads(manifest_bytes)['files']
assert len(files) == 11200
for name, expected in files.items():
    path = root / name
    assert path.stat().st_size == expected['bytes'], name
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    assert digest.hexdigest() == expected['sha256'], name
print('11,200 payload lengths and SHA256 digests match')
PY
(cd evidence/economy-v0.2/review-repair/final-audit && sha256sum -c SHA256SUMS)
```

Fresh verification of the three positive packages and the retained negative cases follows. Exit **2** is the expected coverage refusal; exit **3** is the still-failed local replay. The script checks these separate expectations and preserves every stdout/stderr in `REPAIR_LOGS`. Its success does not turn the failed replay into a passing experiment. It does not execute a new production experiment or a broad test suite. To display French explanations, change `language = 'en'` to `'fr'`.

La suite vérifie fraîchement les trois dossiers positifs et les cas négatifs conservés. Le code **2** correspond au refus de couverture attendu ; le code **3** conserve l’échec local. Le script contrôle ces attentes distinctes et conserve chaque sortie dans `REPAIR_LOGS`. Sa réussite ne transforme pas la reproduction échouée en expérience réussie. Aucune nouvelle expérience de production ni suite générale de tests n’est exécutée. Pour les explications françaises, remplacer `language = 'en'` par `'fr'`.

```sh
python3 - <<'PY'
from pathlib import Path
import json, os, subprocess, sys
root = Path(os.environ['REPAIR_EVIDENCE'])
logs = Path(os.environ['REPAIR_LOGS'])
language = 'en'
cases = [
    ('historical', Path(os.environ['HISTORICAL_EVIDENCE']) / 'qualification/complete-attempt-1', 0),
    ('ci', root / 'ci-positive/extracted/complete', 0),
    ('tmp', root / 'tmp-confirmation/complete', 0),
    ('alias-demo', root / 'before/inputs/experiment-roles-alias-base-demo', 2),
    ('alias-comparison', root / 'before/inputs/experiment-roles-alias-base-comparison', 2),
    ('failed-local-replay', root / 'qualification/complete-replay-1', 3),
]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONPATH', None)
for name, directory, expected in cases:
    result = subprocess.run(
        [sys.executable, '-m', 'continuity_economy', '--language', language,
         'verify-suite', '--in-dir', str(directory)],
        cwd=os.environ['REPAIR_SOURCE'], env=env, capture_output=True)
    (logs / (name + '.stdout')).write_bytes(result.stdout)
    (logs / (name + '.stderr')).write_bytes(result.stderr)
    assert result.returncode == expected, (name, result.returncode, expected)
    document = json.loads(result.stderr if expected == 2 else result.stdout)
    if expected == 2:
        assert document['code'] == 'SUITE_COVERAGE', name
    else:
        assert document['fresh'] is True, name
        assert document['test_assertion'] == ('PASSED' if expected == 0 else 'FAILED'), name
    print(name, 'exit', result.returncode, 'matches retained expectation')
print('Logs:', logs)
PY
```

The old-checker false acceptances are retained under `before/outputs/`; source and invocation provenance are in `before/`. Reproducing those old acceptances requires the reviewed source `46c2e0b2123cb56f24dd956b2dbfb79a7f7fbecd`, not the corrected source selected above.

Les fausses acceptations de l’ancien vérificateur sont conservées sous `before/outputs/`, avec source et commandes sous `before/`. Leur reproduction exige la source examinée `46c2e0b2123cb56f24dd956b2dbfb79a7f7fbecd`, différente de la source corrigée sélectionnée ci-dessus.
