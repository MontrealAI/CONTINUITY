# CONTINUITY Ω — Post-review experiment coverage repair

[Français](REVIEW_REPAIR.fr.md) · [Original results](RESULTS.md) · [Repair evidence](../../evidence/economy-v0.2/review-repair/QUALIFICATION.json) · [Review finding](https://github.com/MontrealAI/CONTINUITY/pull/3#discussion_r4498755611)

## The defect and its actual counterexamples

Automated review of `46c2e0b2123cb56f24dd956b2dbfb79a7f7fbecd` found that the complete-experiment verifier required the names `base`, `successor` and `challenges`, but did not bind their children to the required suite types. A passing child could therefore be reused under all three names. The original complete experiment did contain its required evidence; the defect was the checker's willingness to qualify an incomplete replacement.

The defect was reproduced against the unchanged published source using physical copies of real historical evidence, with expectations recorded before invoking that checker:

| Retained counterexample | Unique historical evidence supplied | Required coverage absent | Old checker |
| --- | --- | --- | --- |
| Three names refer to one base demonstration | Seven Harness-only base cells | Conventional/outside/AI comparison cells, successor, challenges | `PASSED`, exit 0 |
| Three names refer to one base comparison | Twenty-eight base comparison cells | Successor and challenges | `PASSED`, exit 0 |

Both outer counterexample assertions passed because they exposed the defect. The old checker's qualification is **FAILED** for complete-experiment coverage. This is an evidence intervention, not new production, and does not erase legitimate acceptance within the original individual runs. The old stdout, stderr, inputs, source and command records remain in the separate repair archive.

## The repair

Source correction `f9e56c7dd9627b322406e05c53b4f6537d434262` changes the aggregate verification module to require:

- The supported outer experiment version, an object containing exactly the three required member names, and distinct safe child paths.
- A base **comparison** suite in the **base** cohort.
- A successor **comparison** suite in the **successor** cohort.
- The registered **challenge** suite.
- Fresh child verification of each registry, required cell/control, retained contract and policy, and durable evidence. Saved favorable labels remain insufficient.

A nested experiment cannot substitute for any child. The role check consumes the same comparison index that fresh verification uses. The existing independent product, receiver, capacity and economic checks remain intact.

The exact retained counterexamples now return **exit 2 / `SUITE_COVERAGE`** in both English and French. All **1,955 input files** remained byte-identical. The initial AFTER record explicitly identifies its uncommitted source; separate qualification records identify the clean published correction. Neither source state is presented as the other.

## Historical freeze and claim boundaries

The first successor ran at `3494becbbfaf15ae571a71df05a49b9ce982cc84` with all 42 frozen implementation/interface/documentation files unchanged. That historical observation remains true. This later repair changes **one** of those files, `continuity_economy/suite.py`; the other **41** remain identical. The current repaired verifier is therefore not described as the original unchanged 42-file implementation.

Contracts, participant policies, fixture hashes, the original freeze and the original evidence archive are unchanged. The original archive SHA-256 remains `a96c6b7c25e0e17ed1c1f7d0fcf13b70c338159ae9c10c5f825699b9e186db25`. Experiment and evidence format version `0.2.0` is retained; exact source commits distinguish this pre-release correction. No earlier result, source identity or published v0.1 release is replaced.

The later complete executions are **regression replays**, not further fresh held-out successors and not statistical comparisons pooled with the first observations. Neither the repair nor its tests establish a method advantage, complete-cost saving or real voluntary demand. Human repair and review labor were not timed.

## Validation and requirements mapping

Twelve targeted aggregate-coverage tests and the eight existing CLI tests passed before clean-source qualification. The targeted tests explicitly stub leaf judgments to isolate admission; they are not new production evidence. The retained counterexamples and separate fresh checks of actual durable evidence assess the repair beyond those admission tests. The exact source, commands and retained results are identified in [QUALIFICATION.json](../../evidence/economy-v0.2/review-repair/QUALIFICATION.json).

### Observed qualification at the corrected source

The following observations refer to clean source `f9e56c7dd9627b322406e05c53b4f6537d434262`. A successful CI job and a successful local replay are separate observations; both favorable and unfavorable evidence are retained.

| Observation | Observed result | Scope |
| --- | --- | --- |
| Full local regression suite | **436 tests passed in 76.716 seconds** | Existing regressions and the new coverage tests |
| CI workflows for push and pull request | **All six passed** | The exact corrected source; this does not erase the separate local failure below |
| Actual downloaded CI artifact `13551894820`, from run `42319942290` | **Independent fresh verification PASSED** | 28 base cells, 4 successor cells and 26 challenges |
| Original historical complete experiment | **Fresh verification PASSED** | The corrected checker still accepts the original complete durable evidence |
| Local `complete-replay-1` | **FAILED**, exit 3; its separate fresh verification also **FAILED**, exit 3 | One base cell could not finalize its evidence; no favorable qualification of that cell |

The [downloaded CI artifact](https://github.com/MontrealAI/CONTINUITY/actions/runs/42319942290/artifacts/13551894820) was **11,631,638 bytes**, with SHA-256 `6cf6fc794789be983e320dba11b4c344cc2e708822d3c280ab8b5cddba00344a`; **3,022 files** were extracted. Verification ran against those downloaded files, rather than relying on a workflow label or saved Passport. The [CI run](https://github.com/MontrealAI/CONTINUITY/actions/runs/42319942290), download metadata and fresh-verification record identify this positive observation separately from the local replay.

### Preserved local finalization failure

In `qualification/complete-replay-1`, the `constructed-continuity.conventional` cell recorded recipient acceptance of all **1,900 units** and settlement, then failed during evidence export with **`DATABASE_STATE_CHANGED`** for `runtime/capacity/COMPAT-A.W0.sqlite`. The controller returned an error, and the incomplete evidence package left both **outcome** and **service feasibility** **NOT ESTABLISHED**. Its separate fresh verification also failed. Earlier execution records are not a substitute for the missing qualified evidence copy.

Forensic inspection used preserved physical copies. The main database alone matched the retained pre-close logical digest and contained the final capacity action. Opening the same main database with its residual write-ahead log (WAL) instead exposed an older state missing the final **100-unit** lot's reservation, commitment and fulfillment. The older state was also reproduced without the copied shared-memory sidecar. This establishes an inconsistent retained main/WAL pair; it does not establish why the older WAL remained or reappeared after the recorded successful checkpoints and normal worker closures.

One bounded lifecycle probe used **two distinct capacity databases**, explicit transaction barriers and the unchanged digest/checkpoint/close/backup sequence. It **did not reproduce** the anomaly. The checkpoints reduced each WAL to zero, normal worker closure removed it, and both exported logical digests matched their retained values. No checkpoint, digest or evidence-acceptance guard was weakened, and this investigation did not justify an additional runtime source correction. The original failed bytes, diagnostic script and boundary observations remain retained.

The failed local replay used the shared workspace for its live databases; the documented clean-checkout command uses `/tmp`, and CI uses its runner's temporary directory. A single confirmation on the documented `/tmp` path has been preregistered. **That single confirmation and its separate fresh verification both passed: 28 base records, four successor records and 26 challenges. All 3,024 files matched after the closed run was copied into the retained evidence.** The location difference motivates that bounded check; it is not a demonstrated explanation of the failure.

The positive CI evidence and the failed local attempt remain separate records. They are not pooled with each other or with the first comparative observations. One conventional-method cell's finalization failure does not establish a Harness method advantage, and the positive CI result does not resolve the unexplained local main/WAL inconsistency.

### Requirements mapping

| Requirement | Executable coverage in `tests/test_economy_suite.py` |
| --- | --- |
| Valid complete evidence remains acceptable despite saved labels | `test_complete_registered_children_are_verified_freshly_despite_saved_failed_labels` |
| Demonstrations, copies and base comparisons cannot replace required roles | Tests beginning `test_passing_base_demo_` and `test_passing_base_comparison_` |
| Cohorts and child schemas remain binding | `test_swapped_comparison_cohorts_are_refused`; `test_passing_nested_experiment_cannot_replace_any_required_child` |
| Strict outer admission, supported versions and safe distinct paths | Tests beginning `test_experiment_requires_`, `test_nonobject_indexes_`, `test_member_paths_`, and `test_all_child_versions_` |
| Missing cells/controls and changed contracts fail qualification | `test_missing_cell_or_challenge_cannot_be_hidden_by_saved_passes`; `test_child_metadata_does_not_replace_independent_contract_binding` |
| A fresh failed child cannot be replaced by a saved PASS | `test_failed_fresh_run_or_challenge_cannot_be_hidden_by_saved_passes` |

```sh
python3 -m unittest discover -s tests -p 'test_economy_suite.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m continuity_economy --language en experiment --out /tmp/continuity-economy-repaired-001
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuity-economy-repaired-001
```

Choose a new output directory. Reproduction instructions for the preserved BEFORE/AFTER packages accompany the repair archive. The trust model and unresolved economic, settlement and initialization limits in the original report remain applicable; a finite regression suite is not a general proof.
