# CONTINUITY Ω Harness v0.1 — Executed results

**English** · [Français](RESULTS.fr.md) · [Reproduction guide](README.md) · [Requirements matrix](REQUIREMENTS.md)

**Qualification date: 6 November 2026 (UTC). Qualified source: [fa9da1f54acfaa82510a4b6b805c2980d3e5b31d](https://github.com/MontrealAI/CONTINUITY/commit/fa9da1f54acfaa82510a4b6b805c2980d3e5b31d).**

The bounded local milestone was demonstrated on the second qualification attempt. Both the conventional and Harness-supported procedures restored and fulfilled feasible obligations, used the authorized backup when required, and preserved partial failure when backup capacity could not satisfy every order. Their functional outcomes tied in all 12 registered pairs. The first attempt remains unqualified because separate fresh verification detected unsealed SQLite sidecars in one transfer run; its earlier favorable summary has not been rewritten.

The delivered evidence supports local software execution with synthetic data. It does not establish printed labels, a paying customer, physically independent suppliers, complete economic cost, incremental AI value, or general cyberresilience. All 12 AI comparison entries are **NOT RUN**. Complete cost, comparative advantage and commercial value remain **NOT ESTABLISHED**.

The [machine-readable delivery record](../../evidence/harness-v0.1/RESULTS.json) and [complete evidence archive](../../evidence/harness-v0.1/continuity-harness-v0.1-evidence.tar.xz) retain both qualification attempts, individual results and bilingual Passports, authority, durable artifacts, commands, failures and captured validation logs. Archive paths in this report are relative to the extracted top directory `continuity-harness-v0.1-evidence/`. A saved Passport describes a past assessment; the separate fresh-verification receipts establish what was checked afterward.

## 1. Version, preregistration and qualification history

The actual starting repository revision was `8776d70ba091f71dab12fc9d3195baf7fc789676`. The new package is separately versioned as `continuity_harness` 0.1.0. The experiment specification was locally committed before comparative results as `318f6d76868fa63ce3e25805e1c11bbfc057f981`; its identical content tree was published as `0b9eac772d8088a0ee44605aead85fa5d36dd93b` through the connected GitHub workflow. Remote publication followed preliminary engineering controls and preceded the complete comparison. This does not erase earlier development observations. The registration and publication distinction is recorded in [AMENDMENTS.md](AMENDMENTS.md).

Both comparison attempts use the same version-1 specification, whose canonical SHA-256 is `5b4304d1c855cd241a08f4ffc0bd83f95ee3c8ce3af9a06cb40b679f418edabc`. Its raw file SHA-256 is `8f08c8d524ab4aab9528728725d528eaa5f7e701403c9e176e8dff9b17380880`; these identify different serializations of the same specification. Hypotheses, order quantities, capacities, allowed routes, faults, acceptance criteria and comparison conditions were not relaxed after the first failure.

| Attempt | Source revision | Initial comparison | Separate fresh comparison | Qualification |
| --- | --- | --- | --- | --- |
| 1, archived at the delivery root | `5c92fd03a258a3f4845c50a5b37e7a14cd2aa40c` | 24 executions, 12 AI not run; saved gate PASSED | FAILED; exit 3; one transfer cell lost sufficient evidence integrity | **Not qualified; retained unchanged** |
| 2, archived under `attempt-2/` | `fa9da1f54acfaa82510a4b6b805c2980d3e5b31d` | 24 executions, 12 AI not run; gate PASSED | PASSED; exit 0; no failed assertions or non-established safety cells | **Qualified within the declared local model** |

### The first failure and the bounded correction

The affected first-attempt run was `labels-transfer-a-constrained-harness-8b9332cbc97f`. Its producer reported `PARTIAL`, and the saved verification initially accepted the 700-unit first order. Separate verification found unsealed `service.sqlite-wal` and `service.sqlite-shm` files. It reported `UNSEALED_EVIDENCE` and `DATABASE_NOT_CHECKPOINTED`, changed accepted quantity to 0 of 1,600, and left both obligations **UNRESOLVED**. Safety became **NOT_ESTABLISHED**. The summary's `critical_safety_failures` list is a qualification gate; this observation does not demonstrate actual over-allocation or duplicate fulfillment.

This unfavorable observation remains part of the comparison history: all 12 conventional expected assertions passed fresh verification, while only 11 of 12 Harness assertions did. Fresh acceptance totals were 17,200 units for conventional and 16,500 for Harness, because the latter's 700-unit output lacked sufficient trustworthy evidence. It is an observed qualification failure of that Harness attempt, not evidence of universal method inferiority. It has not been discarded, relabeled a tie, or pooled into the second attempt.

The sealed main database's byte hash still matched. Inspection of isolated copies found `last_tick=8` in the sealed main state and `last_tick=5` when the stale WAL was applied. The cause of the sidecars' reappearance is **NOT ESTABLISHED**. No unsupported attribution to a process, storage layer or host actor is made. The saved favorable summary, separate failed receipt and diagnostic result remain available in `comparison/` and `validation/compare-fresh*`.

The new finalization procedure captures the live service's complete state before closure, stops all owned workers, backs up the actual SQLite runtime database, requires equality with the captured state, converts the evidence copy to standalone DELETE-journal form, synchronizes it, and only then publishes the closed database in `evidence/`. Runtime files remain separate. A mismatch or failed backup prevents completed qualification. The verifier continues to reject a nonempty journal beside evidence; the fix does not ignore sidecars or loosen the journal guard. Nine focused finalization tests cover these boundaries, including stale runtime WAL, actual committed WAL recovery, post-close state changes and failed finalization. This is a tested mitigation, not a proof of every host/storage failure or an explanation of the original cause. See [the implementation](../../continuity_harness/controller.py) and [finalization tests](../../tests/test_harness_finalization.py).

### Completed qualification commands

Attempt 2 ran in a clean checkout before and after execution, using Python **3.12.14**, SQLite **3.53.1**, and **Linux 6.18.57 x86_64, glibc 2.39**. The record contains exact interpreter paths, argv and working directory. These command durations include their process startup and reporting scope; they are not candidate-only timings.

| Command | Start UTC | Wall (ms) | Exit |
| --- | --- | --- | --- |
| demo (fr) | 2026-11-06T20:38:24Z | 967.963 | 0 |
| verify-suite / demo (en) | 2026-11-06T20:38:25Z | 114.918 | 0 |
| compare (en) | 2026-11-06T20:38:25Z | 6,089.120 | 0 |
| verify-suite / comparison (fr) | 2026-11-06T20:38:31Z | 365.171 | 0 |
| challenge (fr) | 2026-11-06T20:38:31Z | 816.276 | 0 |

Source: `attempt-2/QUALIFICATION.json` and its `validation/*.stdout.json` receipts. The demonstration executed three Harness controls; comparison executed 24 real method cells; the challenge suite executed four new local service runs supporting eight cases. Copied challenge evidence is not another execution. Both attempts remain separate observations, not pooled independent favorable trials.

## 2. Which obligations were actually preserved

The retained base journal amends `LBL-100` for `CUSTOMER-A` to 1,100 units and its final specification, restores missing `LBL-200` for `CUSTOMER-B` at 800 units, and cancels `LBL-300`. The stale snapshot contains the old first order, omits the second and still contains the canceled order. Transfer fixtures change quantities, capacity, dependency identifiers and a second-order specification amendment. The verifier independently reconstructs the retained source; a candidate cannot redefine the obligation by rewriting its own package.

The following outcomes were identical for both real methods in attempt 2. Every completed entry has the correct retained recipient, product/specification, quantity and completed state. A refusal accepts zero units. No canceled third order was fulfilled.

| Fixture | Control | LBL-100 / CUSTOMER-A | LBL-200 / CUSTOMER-B | Accepted total |
| --- | --- | --- | --- | --- |
| labels-base | Recovery | 1,100/1,100 — completed | 800/800 — completed | 1,900 |
| labels-base | Alternate | 1,100/1,100 — completed | 800/800 — completed | 1,900 |
| labels-base | Constrained | 1,100/1,100 — completed | 0/800 — refused | 1,100 |
| labels-transfer-a | Recovery | 700/700 — completed | 900/900 — completed | 1,600 |
| labels-transfer-a | Alternate | 700/700 — completed | 900/900 — completed | 1,600 |
| labels-transfer-a | Constrained | 700/700 — completed | 0/900 — refused | 700 |
| labels-transfer-b | Recovery | 600/600 — completed | 500/500 — completed | 1,100 |
| labels-transfer-b | Alternate | 600/600 — completed | 500/500 — completed | 1,100 |
| labels-transfer-b | Constrained | 600/600 — completed | 0/500 — refused | 600 |
| labels-transfer-c | Recovery | 1,200/1,200 — completed | 1,000/1,000 — completed | 2,200 |
| labels-transfer-c | Alternate | 1,200/1,200 — completed | 1,000/1,000 — completed | 2,200 |
| labels-transfer-c | Constrained | 1,200/1,200 — completed | 0/1,000 — refused | 1,200 |

The constrained backup capacities are 1,500, 1,000, 700 and 1,300 units respectively. The deterministic schedule lets the first-priority transaction proceed; the remaining capacities—400, 300, 100 and 100—cannot cover the second orders. Reversing the barrier winner is tested separately. The comparison is not a random allocation-policy contest.

Across each method's 12 cells, **20 of 24 obligations** and **17,200 of 20,400 units** were accepted. The four refused second orders leave **3,200 units unfulfilled**. These sums span separate synthetic contracts; they are not one customer's production volume. Incorrect, duplicate, late and unsupported completed obligations were each recorded as zero in the qualified comparison. No critical safety failure was observed within that tested model.

| Control | Test assertion | Target verdict | Evidence stage | Full-promise claim | Safety |
| --- | --- | --- | --- | --- | --- |
| Feasible recovery | PASSED | COMPLETED | LOCAL_SOFTWARE_EXECUTION | DEMONSTRATED | DEMONSTRATED |
| Feasible alternate route | PASSED | COMPLETED | LOCAL_SOFTWARE_EXECUTION | DEMONSTRATED | DEMONSTRATED |
| Constrained disruption | PASSED | PARTIAL | LOCAL_SOFTWARE_EXECUTION | **FAILED** | DEMONSTRATED |

A safe refusal preserved the capacity invariant but did not preserve the second customer's obligation. The constrained cases are not complete fulfillment. This distinction is present in the machine results and both language Passports.

All constrained cells observed the declared primary outage, concurrent final-capacity competition, lost acknowledgment after durable fulfillment, retry while the outcome was unknown, real service termination, candidate termination and restart reconciliation. Each recorded one retry and two worker restarts. Stable keys and durable receipts reconciled completed work without creating a second fulfillment. This is local duplicate suppression under tested interruptions, not universal exactly-once delivery.

## 3. Timing, resources and complete-cost gaps

The contract's logical deadline is tick 100; wall deadline is 30,000 ms; primary recovery objective is 15,000 ms. These are configured acceptance limits, not business estimates. Completion uses an exact trusted observation after artifact export/fsync as a conservative upper bound. The earlier receipt transition timestamp is reported separately. Missing observations remain unestablished; a late upper bound can conservatively reject persistence that may have occurred earlier. Recovery acceptance compares the exact trusted monotonic observation to the inclusive nanosecond limit, not rounded display milliseconds.

The table lists all 12 method pairs. Wall time covers the run's measured controller interval. The output bound is the latest **accepted** artifact observation relative to run start; for constrained cells it describes only the completed first order, not completion of the whole promise. Values are milliseconds, rounded to three decimals; exact nanoseconds remain in the JSON records.

| Fixture | Control | Conventional wall | Harness wall | Conventional output bound | Harness output bound |
| --- | --- | --- | --- | --- | --- |
| labels-base | Recovery | 185.704 | 192.737 | 138.536 | 154.133 |
| labels-base | Alternate | 154.521 | 141.992 | 117.311 | 105.038 |
| labels-base | Constrained | 301.391 | 300.662 | 206.149 | 212.879 |
| labels-transfer-a | Recovery | 123.234 | 126.309 | 95.191 | 98.162 |
| labels-transfer-a | Alternate | 140.151 | 137.607 | 104.924 | 98.523 |
| labels-transfer-a | Constrained | 316.363 | 326.561 | 214.913 | 208.516 |
| labels-transfer-b | Recovery | 183.216 | 176.334 | 137.212 | 126.816 |
| labels-transfer-b | Alternate | 152.341 | 114.990 | 114.448 | 88.244 |
| labels-transfer-b | Constrained | 339.709 | 324.555 | 241.190 | 213.372 |
| labels-transfer-c | Recovery | 153.450 | 161.540 | 114.199 | 122.837 |
| labels-transfer-c | Alternate | 148.381 | 159.699 | 115.286 | 121.098 |
| labels-transfer-c | Constrained | 329.290 | 271.192 | 229.499 | 191.075 |

Displayed primary recovery times for base, transfer A, B and C were respectively **124/140**, **84/85**, **113/114** and **101/109 ms** for conventional/Harness. Alternate and constrained runs do not claim restored primary service and record no primary recovery duration.

### Resource accounting for both attempts

Each method column sums its 12 execution records. Attempt 1 remains unqualified; its resource observations are retained as costs of an actual attempt, not favorable acceptance evidence. CPU values are separately observed user/system usage deltas for children and controller. Concurrent child CPU may exceed elapsed wall time. Storage counts run contents at the recorded measurement boundary, before final controller/reports and suite-index metadata, excluding separately retained authority. Attempt 2 additionally retains runtime state and a separate durable evidence database, so its storage scope is materially different.

| Metric | A1 conventional | A1 Harness | A2 conventional | A2 Harness |
| --- | --- | --- | --- | --- |
| Execution wall (ms) | 2,121.971 | 2,125.257 | 2,527.752 | 2,434.178 |
| Child CPU user (ms) | 1,724.224 | 1,683.202 | 1,886.864 | 1,796.073 |
| Child CPU system (ms) | 388.474 | 495.574 | 448.857 | 457.749 |
| Controller CPU user (ms) | 82.160 | 82.456 | 159.312 | 164.946 |
| Controller CPU system (ms) | 16.174 | 18.859 | 35.993 | 28.168 |
| Recorded storage (bytes) | 941,419 | 941,259 | 2,336,441 | 2,335,721 |
| Broker requests | 104 | 104 | 104 | 104 |
| Retries | 4 | 4 | 4 | 4 |
| Worker restarts | 8 | 8 | 8 | 8 |
| Human interventions during execution | 0 | 0 | 0 | 0 |

Both methods used **104 broker requests, four retries and eight worker restarts per attempt**. Zero recorded human interventions refers only to autonomous execution. It does not mean zero engineering, investigation, preparation, integration or review work. The first attempt's failed qualification and subsequent repair required development work whose labor time was not recorded.

Peak memory, preparation/integration labor, verification/reporting CPU, monetary rates, prices and complete business costs remain unknown. Fresh suite verification wall times and individual challenge verification wall times are measured separately; they cannot fill those missing categories. The configured USD currency and zero fixture budget are inputs, not customer budgets or measured spending. There is no justified savings estimate or claim that either method is cheaper.

The timings sometimes favor either method. One sequential observation per cell on a shared host, the fixed conventional → Harness → AI order, shared cache/interpreter/filesystem effects and changed finalization between attempts prevent a stable speed claim. Small byte-count differences partly reflect recorded identifiers; they do not establish a storage-efficiency advantage. No critical failure is averaged into a favorable score.

## 4. Fair comparison, ablation and transfer

The conventional method received the same journal and stale snapshot, permissions, capacity/dependencies, tool interface, fault schedule and observation opportunities. It uses ordinary source reconciliation, transactions, stable idempotency keys and durable-state lookup. The Harness method adds a recovered-state cross-check. Both use the same service infrastructure and fresh verifier; the oracle and retained acceptance evidence are inaccessible to both candidates. Shared machinery therefore contributes to both methods' outcomes. The comparison does not isolate a benefit from branding or from selectively withholding ordinary safeguards.

The **12 functional pairs tied**. The registered comparative hypothesis remains **NOT ESTABLISHED** as an improvement claim: this suite demonstrates executable methods and evidence discipline, not superior accepted outcomes or complete resource savings from the additional Harness check.

The three transfer fixtures contributed nine executed controls per method and the same outcomes under ordinary conventional reuse. Their 15 accepted obligations per method total 12,300 of 14,700 required units; the constrained missing quantity is 2,400. The combined measured execution intervals were 1,886.135 ms conventional and 1,798.787 ms Harness, with 78 broker requests, three retries and six restarts each. These describe this reuse, not a measured reduction in adaptation labor.

No fixture-specific executor edit was needed during the second registered suite: quantities, specification changes and dependencies are inputs, and the checkout remained clean. Preparation and integration effort were not timed. The second attempt did require a general evidence-finalization change after the first failure, which is recorded rather than attributed to free transfer. The held-out fixtures were reserved from the demonstration but public, authored, small and structurally related. Dependency identifiers vary; this does not establish a new physical supply network or discovery advantage for unrelated businesses.

No suitable already-authorized local model was supplied; neither `ollama` nor `llama-cli` was found. The AI adapter and bounded tool protocol exist, but all **12 AI cells are NOT RUN**, with no simulated performance result. Running that arm would require an inspected local model/runtime, explicit capability identity, equivalent confinement and observations, and a newly recorded execution. The implementation assistance used to develop this repository is not an AI-adapter benchmark.

## 5. Retained adversarial results and checker mutations

The challenge suite preserves eight cases, one positive control and four new local executions in total. Other cases copy the positive-control evidence, including old favorable Passports. Their execution resources must not be counted repeatedly. `TARGET_RESULT.json`, `REFERENCE_RESULT.json` and `CHALLENGE.json` remain distinct. Every outer assertion passed; three deliberately defective checker qualification claims failed as intended.

| Case | Assertion | Target verdict | Stage | Component claim | Reference promise | Accepted/required units |
| --- | --- | --- | --- | --- | --- | --- |
| no-journal-ablation | PASSED | PARTIAL | LOCAL_SOFTWARE_EXECUTION | FAILED | FAILED | 0/1,900 |
| rewritten-1850 | PASSED | PARTIAL | LOCAL_SOFTWARE_EXECUTION | DEMONSTRATED | FAILED | 1,100/1,900 |
| missing-reference-pin | PASSED | NOT_ESTABLISHED | FRESH_VERIFICATION_CHALLENGE | DEMONSTRATED | NOT_ESTABLISHED | 0/1,900 |
| changed-artifact | PASSED | FAILED | FRESH_VERIFICATION_CHALLENGE | DEMONSTRATED | FAILED | 0/1,900 |
| shared-failed-dependency | PASSED | REFUSED | LOCAL_SOFTWARE_EXECUTION | DEMONSTRATED | FAILED | 0/1,900 |
| mutant-ignores-byte-integrity | PASSED | DEMONSTRATED | CHECKER_MUTATION_EXERCISE | FAILED | FAILED | 0/1,900 |
| mutant-ignores-revocation | PASSED | DEMONSTRATED | CHECKER_MUTATION_EXERCISE | FAILED | FAILED | 0/1,900 |
| mutant-rejects-valid-recovery | PASSED | FAILED | CHECKER_MUTATION_EXERCISE | FAILED | DEMONSTRATED | 1,900/1,900 |

The no-journal ablation keeps ordinary service safeguards and refuses stale obligations, accepting 0/1,900. It demonstrates the necessity of source reconciliation in this fixture, not incremental AI value. The coherent 1,850-unit candidate rewrite still leaves a retained 1,900-unit contract: only the unchanged first order's 1,100 units are accepted. Missing a reference pin keeps the underlying business claim **NOT ESTABLISHED**, while the checker correctly preserves uncertainty.

For the byte-integrity and revocation mutants, `PASSED` means the adversarial assertion successfully exposed false acceptance. The tested mutant reports `DEMONSTRATED`, but its qualification claim is **FAILED**. The positive-control mutant falsely rejects valid work and is also unqualified. The revocation mutation is a declared synthetic edit of copied controller evidence with a privileged test reseal, not a live service revocation experiment; actual live revocation has separate boundary tests. No scoped mutant changes the installed verifier source.

Independent review also exposed a separate development defect: controller admission and verification shared a semantic order-replay helper. A common-helper mutation produced and falsely accepted 1,850 units against original 1,900-unit authority. That counterexample and the corrected verification are retained under `development/harness-review-shared-replay-usdotr7w/`. The final verifier uses its own source replay and does not import the producer's outstanding-obligation decision helper. This is an additional producer semantic mutation, distinct from the three surgical checker mutants above. Independent code paths within this project are not third-party certification.

## 6. Tests actually run and preserved history

The consolidated offline run passed **245 tests in 15.384 seconds, with no skips**: **160 Harness tests and 85 existing regressions**. The actual log is `validation/finalization-complete-tests.log`.

| Test file | Count | Scope |
| --- | --- | --- |
| [test_harness_boundaries.py](../../tests/test_harness_boundaries.py) | 14 | Protocol, permissions, timeouts and actual processes |
| [test_harness_challenges.py](../../tests/test_harness_challenges.py) | 11 | Retained adversarial, ablation and mutation records |
| [test_harness_cli.py](../../tests/test_harness_cli.py) | 10 | Bilingual CLI and fresh suite coverage |
| [test_harness_controller.py](../../tests/test_harness_controller.py) | 14 | Executed controls, adapters, fairness and transfer |
| [test_harness_finalization.py](../../tests/test_harness_finalization.py) | 9 | Closed database evidence and failed finalization |
| [test_harness_reporting.py](../../tests/test_harness_reporting.py) | 16 | English/French facts, uncertainty and challenge scope |
| [test_harness_services.py](../../tests/test_harness_services.py) | 34 | Durable ledger, concurrency, crashes and 432 finite traces |
| [test_harness_verifier.py](../../tests/test_harness_verifier.py) | 52 | Independent authority/source/output acceptance and mutations |
| [test_bilingual_cli.py](../../tests/test_bilingual_cli.py) | 17 | Existing bilingual command interface |
| [test_bilingual_repository.py](../../tests/test_bilingual_repository.py) | 5 | Existing repository language policy |
| [test_continuity_omega.py](../../tests/test_continuity_omega.py) | 29 | Historical research prototype |
| [test_continuity_passport.py](../../tests/test_continuity_passport.py) | 14 | Existing Passport behavior |
| [test_research_tools.py](../../tests/test_research_tools.py) | 19 | Existing research/publication tooling |
| [test_web_interactions.py](../../tests/test_web_interactions.py) | 1 | Existing bilingual website interactions |

The source-revision CI runs also passed: [Harness comparison and challenges](https://github.com/MontrealAI/CONTINUITY/actions/runs/42289983351), and [repository regressions and historical verification](https://github.com/MontrealAI/CONTINUITY/actions/runs/42289983392). Their recorded success is included in the machine-readable delivery record.

The finite ledger test exhausts **432 three-step traces**: two capacities × six actions cubed, two one-unit obligations, ticks 0/1/2 and expiry at 2. It does not exhaust arbitrary quantities, longer histories, every second-order transition or operating-system schedule. Real concurrency, crash points, partial writes, deadline edges, mutations and held-out variations are selected additional checks. A finite passing suite is not a general proof.

The copy validation verified **74 unchanged files and four already documented website adaptations** in the 78-file migration boundary. Historical paper consistency remained edition 1.1.1, English 27 pages/French 29 pages, with 31 recorded file hashes; historical companion validation remained packaged presentation only. The Harness does not strengthen the original papers, PDFs, evidence identities, releases, original tests or commercial claims retroactively. The original Lab repository was not modified.

Development failures are retained in [VALIDATION_HISTORY.md](VALIDATION_HISTORY.md): the intermediate 95-test metadata/schema run had 24 failures and two errors; its complete raw log was not captured and has not been invented. A separate 48-test mutation-cleanup run had three errors, followed by a corrected passing run; both logs are retained. Earlier receipt-hash convention outputs remain under their original source identity. Their preservation does not make them qualified current results.

## 7. Reproduce and verify independently

Use a new checkout and new output paths. The Harness requires Python 3.10+ on Linux x86_64 with working seccomp BPF; it uses the standard library and SQLite, with no paid API, secret or model download. Git records the implementation revision; Node.js is additionally needed for the existing website regression.

```sh
git clone https://github.com/MontrealAI/CONTINUITY.git CONTINUITY-harness-review
cd CONTINUITY-harness-review
git checkout --detach fa9da1f54acfaa82510a4b6b805c2980d3e5b31d
python3 -m continuity_harness --language fr demo --out /tmp/continuity-demo-v0.1
python3 -m continuity_harness --language en verify-suite --in-dir /tmp/continuity-demo-v0.1
python3 -m continuity_harness --language en compare --out /tmp/continuity-comparison-v0.1
python3 -m continuity_harness --language fr verify-suite --in-dir /tmp/continuity-comparison-v0.1
python3 -m continuity_harness --language fr challenge --out /tmp/continuity-challenges-v0.1
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

For an individual run, use the paths and independently retained pin in its `INDEX.json` or Passport:

```sh
python3 -m continuity_harness --language en verify --run RUN_DIRECTORY --authority AUTHORITY_DIRECTORY --reference-sha256 RETAINED_REFERENCE_SHA256
```

Do not replace the pin with a new digest calculated from candidate-controlled data. Individual verification of correct partial fulfillment returns exit 3 because the complete promise failed; the enclosing constrained test can still pass. `verify-suite` applies to demonstration/comparison indexes. For a challenge, ordinary verification reproduces the unchanged reference checker; rerunning `challenge` in a new directory reproduces scoped mutants. Existing run directories and saved reports are not overwritten. New run IDs, host timings and resulting hashes may differ while the specified business outcomes remain comparable.

| Archived file | SHA-256 |
| --- | --- |
| `attempt-2/QUALIFICATION.json` | `f68d465beba111a3b95c3d7ce40b0b66f7af6a40a0499c7e289b9a9cc3605456` |
| `attempt-2/demonstration/SUMMARY.json` | `c47e80fce83c6bd318fe132a869104e5a35f2bded8c266bbb0a0c4cc8a741227` |
| `attempt-2/comparison/SUMMARY.json` | `17596a837f221db72988da0d701e903802326d78a14022aa57157f2f0c66af82` |
| `attempt-2/challenges/SUMMARY.json` | `3fcf5138f0324edf6114dbf2e5be97fa014f0be8476765ed3782ea1d4ff01cd2` |

The evidence archive is **313,736 bytes**, with SHA-256 `a7115c8d499377152d6e4c1e83e44ca5997b5452ff3847ad061e73b4bac711b9`. After extraction, all **1,722 manifest-listed files** matched their hashes. A separate fresh verification of the extracted comparison returned exit 0, 24 executed runs, 12 not run, and no failed assertions or non-established safety cells. A later separate verification before packaging also passed. These receipts are retained in [PACKAGE_CHECK.json](../../evidence/harness-v0.1/PACKAGE_CHECK.json) and the delivery record.

After downloading the archive, inspect its retained comparison with:

```sh
tar -xJf continuity-harness-v0.1-evidence.tar.xz -C /tmp
python3 -m continuity_harness --language en verify-suite --in-dir /tmp/continuity-harness-v0.1-evidence/attempt-2/comparison
```

These are raw byte hashes of the named archived files, not real-customer authentication or an external signature. Per-run authority pins and full evidence manifests remain in the archive and machine-readable delivery record.

## 8. Publication state and remaining evidence

The qualified code revision is published on [`feat/continuity-harness-v0.1`](https://github.com/MontrealAI/CONTINUITY/tree/feat/continuity-harness-v0.1). This report identifies that exact code revision; the later documentation/evidence publication is a separate commit. Pull-request and merge state belong to the final publication receipt and are not implied by branch publication. No production deployment, customer contact, real capacity reservation, paid service, credential creation or external access-permission change forms part of these experiments.

The unresolved first-attempt sidecar cause remains a limitation. The accepted second attempt establishes the tested finalization path and retained evidence at the observed times, not immunity to a hostile host or every future storage fault. The host, kernel, trusted launcher/imports, controller, service, authored journal, clock and verifier remain trusted. Candidate seccomp isolation is exercised after trusted imports; arbitrary third-party Python plugins and complete host denial-of-service isolation are not qualified. Logical routes share a host and ledger, and local artifacts are software outputs, not physical goods.

Before an authorized real-world rehearsal, the smallest additional evidence is:

1. Genuine order authority, source custody and completeness through an agreed cutoff, including amendments and cancellations.
2. A qualified provider's actual capacity window and dependency/failure-domain evidence, with explicit activation and data-sharing permission.
3. Agreed real output acceptance, recipient/specification/quantity checks, deadlines and clocks, plus reconciliation for uncertain external fulfillment.
4. A disposable or explicitly isolated rehearsal environment, named operators, recorded interventions, rollback boundaries and permission to run the exercise.
5. Measured preparation, integration, verification and operational effort, explicit prices/rates and complete commercial obligations before any savings or viable-market claim.

The next decision can now use an executable, inspectable local system. Whether it reduces another business's continuity-establishment effort, improves on a competent conventional procedure, or supports a commercially viable arrangement remains an empirical question requiring that additional evidence.
