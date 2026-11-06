# CONTINUITY Ω Harness v0.1 — Continuity Passport

[English](PASSPORT.en.md) · [Français](PASSPORT.fr.md)

**Local software execution · synthetic business data**

This Passport presents the supplied fresh assessment. It is a saved report of that assessment; use the verification command below to inspect the current evidence again.

A completed artifact is a durable local JSON software output. It is not printed goods, customer acceptance, a real supplier reservation, revenue, or external certification.

## Assessment

| Field | Recorded value |
| --- | --- |
| Test assertion | `PASSED` — Expected test behavior observed |
| Target verdict | `PARTIAL` — Partial result |
| Evidence stage | `LOCAL_SOFTWARE_EXECUTION` — Local software execution with synthetic data |
| Complete-promise claim | `FAILED` — Failed |
| Safety within the tested model | `DEMONSTRATED` — Demonstrated within the declared stage |
| Authority binding | `DEMONSTRATED` — Demonstrated within the declared stage |
| Fresh verification status | `COMPLETE` — Completed record |
| Every obligation completed | No |
| Commercial value | `NOT_ESTABLISHED` — Not established |
| Authenticity of real customer instructions | `NOT_ESTABLISHED` — Not established |

Test behavior, target output, evidence stage, and the business claim are separate. A correctly refused request can satisfy a safety test while leaving an obligation unfulfilled. A passing test that exposes a false acceptance does not qualify the defective checker.

## Per-obligation outcomes

| Order | Recipient | Required units | Observed units | Accepted units | Outcome | Route |
| --- | --- | --- | --- | --- | --- | --- |
| LBL-100 | CUSTOMER-A | 1100 | 1100 | 1100 | `COMPLETED` — Completed | `backup` — Backup route |
| LBL-200 | CUSTOMER-B | 800 | 0 | 0 | `REFUSED` — Refused | NOT RECORDED / UNKNOWN |

### Order `LBL-100`

| Field | Recorded value |
| --- | --- |
| Product | LABEL-A |
| Final specification SHA-256 | 1b590fba52dad5b09041ead75f1b3057b233d8b1ac35d9d9d37905696fc9675c |
| Logical deadline (ticks) | 100 |
| Completion position (ticks) | 5 |
| Post-export monotonic observation (ns) | 25304882005406 |

**Durable completion observed no later than:** 212.879 ms (212878776 ns)

**Producer transition before commit (elapsed):** 167.702 ms (167701629 ns)

**Recorded reasons:**

None recorded.

### Order `LBL-200`

| Field | Recorded value |
| --- | --- |
| Product | LABEL-A |
| Final specification SHA-256 | a813e867578702ddec11b49ace3a5fd745ff391a2f5c95e7fe8af1c1f6b6c0e2 |
| Logical deadline (ticks) | 100 |
| Completion position (ticks) | NOT RECORDED / UNKNOWN |
| Post-export monotonic observation (ns) | NOT RECORDED / UNKNOWN |

**Durable completion observed no later than:** NOT RECORDED / UNKNOWN

**Producer transition before commit (elapsed):** NOT RECORDED / UNKNOWN

**Recorded reasons:**

- `CAPACITY_EXCEEDED`: Refused: insufficient remaining capacity; no excess allocation is implied.
- `NO_DURABLE_OUTPUT`: No accepted durable output exists for this obligation.

## Totals for the retained promise

| Field | Recorded value |
| --- | --- |
| Required obligations | 2 |
| Accepted obligations | 1 |
| Required units | 1900 |
| Observed output units | 1100 |
| Accepted units | 1100 |
| Units not accepted | 800 |
| Late obligations | 0 |
| Incorrect obligations | 0 |
| Duplicated obligations | 0 |
| Unsupported completed obligations | 0 |

## Observed failures

| Machine code | Explanation | Order | Original technical detail |
| --- | --- | --- | --- |
| `ALL_OBLIGATIONS_NOT_COMPLETED` | The complete customer promise was not fulfilled. | NOT RECORDED / UNKNOWN |  |

## Unresolved evidence and claims

None recorded.

## Frozen conditions

| Field | Recorded value |
| --- | --- |
| Contract identifier | CONTRACT-labels-base-constrained |
| Contract schema | continuity-harness/contract/v1 |
| Contract version | 1 |
| Declared exercise mode | SYNTHETIC_LOCAL_EXECUTION |
| Source events SHA-256 | 1f5119db7e2bd8f280a98b97ae72aecf3cc859750cbe6ced7710d48608eb2bca |
| Source observation cutoff | 5 |
| Authored source-completeness declaration | Yes |
| Logical deadline (ticks) | 100 |
| Configured wall deadline (ms) | 30000 |
| Configured recovery objective (ms) | 15000 |
| Capacity window [start, end) | {"end":100,"start":0} |
| Reservation lease (ticks) | 20 |
| Declared route capacities (units) | {"backup":1500,"primary":3000} |
| Allowed routes | ["primary","backup"] |
| Declared permissions | {"activation":true,"sharing":true} |
| Declared route dependencies | {"backup":"GRID-A-INDEPENDENT","primary":"GRID-A"} |
| Unavailable dependencies | ["GRID-A"] |
| Configured fixture currency | USD |
| Configured fixture budget (minor units) | 0 |
| Frozen comparison conditions | {"fixture_id":"labels-base","held_out":false,"information":"EQUAL","resource_policy":"SHARED_SERVICES","suite_id":"CONTINUITY-HARNESS-001"} |

Ticks are controller-owned logical schedule positions, not measured hours. Milliseconds and nanoseconds below refer to monotonic local measurements. Durable completion uses the trusted post-export observation as a conservative upper bound, distinct from the producer's precommit transition timestamp. Observation delay can reject a late bound even if persistence actually occurred earlier. The configured wall deadline and recovery objective are acceptance limits, not achieved durations.

## Fault schedule and observations

| Machine code | Action | Target | Observed |
| --- | --- | --- | --- |
| `PRIMARY_UNAVAILABLE` — Primary route disabled | DISABLE | primary | Yes |
| `CONCURRENT_FINAL_CAPACITY` — Concurrent competition for final capacity | RACE | backup | Yes |
| `ACK_LOST_AFTER_DURABLE_FULFILLMENT` — Acknowledgment lost after durable fulfillment | DROP_ACK | service | Yes |
| `RETRY_WHILE_OUTCOME_UNKNOWN` — Retry while the original outcome remains unknown | RETRY | service | Yes |
| `SERVICE_KILLED_AFTER_COMMIT` — Service process terminated after commit | KILL | service | Yes |
| `CANDIDATE_KILLED_AFTER_REQUEST` — Candidate process terminated after its request | KILL | candidate | Yes |
| `RESTART_RECONCILIATION` — Restart and reconcile durable state | RESTART | candidate | Yes |

The complete event and intervention record is in controller.json. A listed schedule is not evidence that its faults occurred; the observed column records exact matches in the supplied controller record.

## Measurements and accounting gaps

| Field | Recorded value |
| --- | --- |
| Measured execution wall time | 300.662 ms (300662295 ns) |
| Observed child CPU: user | 275.806 ms (275806000 ns) |
| Observed child CPU: system | 62.260 ms (62260000 ns) |
| Observed controller CPU: user | 14.943 ms (14942999 ns) |
| Observed controller CPU: system | 4.021 ms (4021000 ns) |
| Peak resident memory (bytes) | NOT RECORDED / UNKNOWN |
| Measured run storage before final reports (bytes) | 180884 |
| Candidate broker requests | 9 |
| Recorded retries | 1 |
| Recorded worker restarts | 2 |
| Human interventions during this run | 0 |
| Recorded preparation labor (seconds) | NOT RECORDED / UNKNOWN |
| Recorded integration labor (seconds) | NOT RECORDED / UNKNOWN |
| Complete monetary cost | NOT RECORDED / UNKNOWN |
| Measured recovery/readiness time (ms) | NOT RECORDED / UNKNOWN |

Wall time is measured for the controller's local execution interval. Child and controller CPU values are separate process-usage deltas where recorded. Verification/reporting CPU and development work are not included. Storage is the measured run content before final controller/report files and suite-index metadata, excluding separately retained authority. Broker requests count candidate requests; internal controller operations remain in the event record. Zero human interventions concerns this autonomous run only.

Preparation and integration labor, unmeasured memory use, monetary rates, and complete business costs remain unknown when not recorded. The configured currency and budget are fixture inputs, not measured spending or a customer's budget. No price or savings is inferred. One bounded observation per method and fixture does not establish a stable performance advantage.

| Field | Recorded value |
| --- | --- |
| Maximum simultaneous allocation by route | {"backup":1100,"primary":0} |
| Verified durable history transitions | 5 |
| Primary reconstruction verified | No |

## Identity, versions, and environment

| Field | Recorded value |
| --- | --- |
| Run identifier | labels-base-constrained-harness-c3af39df0a42 |
| Candidate method | `harness` — Harness-supported procedure |
| Scenario | `constrained` — Constrained disruption and recovery |
| Recorded seed | 101 |
| Controller state | `COMPLETE` — Completed record |
| Execution start (UTC) | 2026-11-06T20:38:26.770841+00:00 |
| Retained contract SHA-256 | 6566ecb28c8e0d5a768812a4b3f41220cada58d01f1ab8f48de60ef623d9730a |
| Observed reference SHA-256 | ec9f72beb31959636b8039bea70dfcf241091890ece0184e2bd7ecf51fb037e0 |
| Fresh verifier version | 0.1.0 |
| Verification-result schema | continuity-harness/verification/v1 |
| Retained-reference schema | continuity-harness/reference/v1 |
| Independently supplied reference pin | ec9f72beb31959636b8039bea70dfcf241091890ece0184e2bd7ecf51fb037e0 |
| Canonical structured-result SHA-256 | 47135b4f767ff6e40410b7c3a904192ef5de3fec9aeb2da7b6d358eb5c0d0d04 |
| Implementation version | 0.1.0 |
| Recorded Git commit | fa9da1f54acfaa82510a4b6b805c2980d3e5b31d |
| Working tree had uncommitted changes | No |
| Recorded Python runtime | 3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ] |
| Recorded platform and kernel | Linux-6.18.57-x86_64-with-glibc2.39 |
| Recorded SQLite version | 3.53.1 |
| Recorded working directory | /workspace/scratch/b1d5891eb025/continuity-harness-qualified-v2 |

### Implementation source identities

| Path | SHA-256 |
| --- | --- |
| continuity_harness/__init__.py | `577ece33903d70ce17189e594370916b485efec1e66ee07f099b4f62ebd4219e` |
| continuity_harness/__main__.py | `c89523d1e0bbfc47bdcef086a06fabefacde32b7aca6be132e79d78b11e003c8` |
| continuity_harness/adapters.py | `ba0be575481384b74dfbc407c4e575bb8f561c50f1235fdf51f0b4b9c19865b0` |
| continuity_harness/candidate.py | `938d73f546c774452b22823639beda4b0f89d911abe429da48039bf1808e3141` |
| continuity_harness/challenges.py | `d14ec02a127eaab94bf440ccb76b38aa735983f393d6ccae80eb6fcdb1215a5d` |
| continuity_harness/controller.py | `7bbc8a87d34b64d8e9e621de5a907f3b123a3a0e973745c73385b73f3a52d1fd` |
| continuity_harness/fixtures.py | `4464f7c9b151300858703f2332049f83c2df429684326b5be3f4e45e7da11b9e` |
| continuity_harness/reporting.py | `e89eee75a923f9489112e243f140f17adba916627d3c02ff6ac2b58e9a1f8645` |
| continuity_harness/rpc.py | `36e48a53bd6c99a51f85fe1183f6e6e3ff9b0c3f3501c3d8c080ab1ff099b745` |
| continuity_harness/sandbox.py | `7ae5423afd96847b1c38c746a7c417f938624e32acf97273c27757b46e3d556f` |
| continuity_harness/schema.py | `4ad738e4b1ef001d039d92ffad897241be7605189b579abd69e38cfe3660427c` |
| continuity_harness/service.py | `6b2c1816e71b6d0768024ed2a2273d98929fd42c223853eff7f7ccd63108055c` |
| continuity_harness/suite.py | `bac676e2886e2ca434b775fe58a0f87b33c4c97f32badd5d2c63659323a5c4dc` |
| continuity_harness/verifier.py | `2177652f986f9a305d7d3c90e808ba15651a58280c4a6bfd3f37da028542df38` |
| experiments/harness-v0.1/PROVENANCE.json | `0c8697da8cd4eb8635cf5413c0f3e0b4c2dc82ea6cd7d8bc6cac194bed7f5f32` |
| experiments/harness-v0.1/spec.json | `8f08c8d524ab4aab9528728725d528eaa5f7e701403c9e176e8dff9b17380880` |

## Current evidence identities

| Path | SHA-256 |
| --- | --- |
| evidence/artifacts/LBL-100.json | `16bbece2f62fec92a1aa60a09e15ffc64a244a1ee71e85aaa537164af0c35c8f` |
| evidence/service.sqlite | `cf86f8ef0d75d92658ccd51ae0aa3aa26ae47afe85d40955c3efed0525a8c2d7` |

The verifier compares current file bytes with the separately retained execution seal. These hashes identify bytes; they do not authenticate a real customer instruction or prove real-world completeness.

## Fresh verification and recorded commands

```sh
python3 -m continuity_harness --language en verify --run /workspace/scratch/b1d5891eb025/harness-delivery-v0.1/attempt-2/comparison/runs/labels-base-constrained-harness-c3af39df0a42 --authority /workspace/scratch/b1d5891eb025/harness-delivery-v0.1/attempt-2/comparison/authority/labels-base-constrained-harness-c3af39df0a42 --reference-sha256 ec9f72beb31959636b8039bea70dfcf241091890ece0184e2bd7ecf51fb037e0
```

Run from the recorded implementation checkout. Supply the independently retained reference pin from the suite index; do not derive a replacement pin from candidate-controlled data. Verification does not overwrite this saved Passport.

### Other commands recorded for this execution

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m continuity_harness --language en compare --out /workspace/scratch/b1d5891eb025/harness-delivery-v0.1/attempt-2/comparison
```


## Trust assumptions and remaining limits

| Field | Recorded value |
| --- | --- |
| Candidate-isolation mechanism | SECCOMP_BPF |
| Isolation applied | Yes |
| Isolation probe observations | {"authority_open_denied":true,"network_denied":true,"process_inspection_denied":true,"spawn_denied":true,"workspace_open_denied":true} |
| Declared trust scope | TRUSTED_HOST_CONTROLLER_CLOCK_AND_VERIFIER_AUTHORED_SYNTHETIC_SOURCE |

The host, controller, authored journal, local services, clock, and acceptance verifier are trusted within the declared failure model. Shipped candidate code and imports are trusted before seccomp activation; no arbitrary third-party plugin is supported. The candidate receives bounded data after filtering and performs effects only through the allowlisted broker. This does not protect against a malicious host administrator.

Source identity, custody, completeness, and byte integrity are different properties. A finite set of local tests is not a general proof, universal exactly-once delivery, independent external certification, or commercial validation. A synthetic transfer establishes only the measured transfer under its recorded conditions.

No AI performance is established by an unavailable model, a mock, or a recorded response. The AI arm is NOT RUN unless an actual authorized local capability was executed and measured.

Structured records: [RESULT.json](RESULT.json) · [controller.json](controller.json). Both language Passports are derived from the same structured result.
