# CONTINUITY Ω Harness v0.1

**English** · [Français](README.fr.md) · [Architecture](ARCHITECTURE.md) · [Threat model](THREAT_MODEL.md) · [Requirements](REQUIREMENTS.md)

**Keep the same promise. Test the route. Inspect the evidence.**

The Harness exercises a packaging-label order service using synthetic business data, disposable local processes, and durable storage. Recovery and fulfillment execute as software operations. The resulting JSON fulfillment artifacts stand for completed local software work; they are not printed labels, supplier commitments, customer acceptance, or revenue.

The separately versioned `continuity_harness` package executes the three controls below and generates a fresh structured assessment plus complete English/French Passports. The [requirements matrix](REQUIREMENTS.md) connects each claim to its implementation and tests. A suite can pass its declared test assertions while correctly showing that a constrained customer promise was not completely fulfilled.

## What the exercise asks

A frozen contract identifies the recipient, final specification, outstanding quantity, deadline, capacity window, permitted routes, and observation cutoff. A procedure can restore the original service or use an authorized alternative. It cannot silently replace the original obligation with an easier one.

Three controls make this distinction observable:

| Exercise | Conditions | Required interpretation |
| --- | --- | --- |
| Feasible recovery | The primary database is restored from a stale snapshot and reconciled against the protected event journal. Enough capacity exists. | All outstanding obligations must have correct, durable outputs within the contract. |
| Feasible alternative | The primary route is unavailable. A permitted backup has sufficient declared capacity and an unaffected declared dependency. | The same obligations must be fulfilled through the backup. |
| Constrained disruption | Two orders compete for insufficient backup capacity; an acknowledgment is lost after a durable action; a worker is terminated and restarted. | Report each completed, refused, delayed, or unresolved obligation. Safe refusal is not complete fulfillment. |

The base demonstration contains `LBL-100` for `CUSTOMER-A` (1,100 units) and `LBL-200` for `CUSTOMER-B` (800 units), totaling 1,900 units. The stale snapshot has the first order's earlier 1,000-unit specification, omits the second order, and includes `LBL-300` (600 units) before its cancellation. Replaying the retained five-event journal restores the amended first order and missing second order and removes the canceled obligation. The new Harness defines its own explicit fixture contract. The historical paper's supplied lead times, prices, and commercial claims do not become measurements of this execution.

The base primary capacity is 3,000 units. Backup capacity is 2,100 in the feasible controls and 1,500 in the constrained control. The deterministic constrained schedule gives the first-priority order the initial transaction: its 1,100 units fit, while the remaining 400 cannot cover the second order's 800. Both routes are logical local services using the same trusted host and ledger; these fixtures do not establish physically independent suppliers.

## Setup and commands

Use Python 3.10 or later on **Linux x86_64 with seccomp BPF available**. The Harness uses Python's standard library and the bundled SQLite library; no package download, secret, account, model, or paid service is required. Existing repository-wide website tests also require Node.js. Other architectures and operating systems are not supported for the confined candidate exercise in v0.1. If the required filter cannot be installed, the exercise refuses favorable isolation; there is no unconfined fallback. See the [threat model](THREAT_MODEL.md).

From the repository root, use a new output directory for every experiment:

```sh
python3 -m continuity_harness --language en demo --out /tmp/continuity-harness-demo-001
python3 -m continuity_harness --language en verify-suite --in-dir /tmp/continuity-harness-demo-001
python3 -m continuity_harness --language en verify --run RUN_DIRECTORY --authority AUTHORITY_DIRECTORY --reference-sha256 REFERENCE_SHA256
python3 -m continuity_harness --language en compare --out /tmp/continuity-harness-comparison-001
python3 -m continuity_harness --language en verify-suite --in-dir /tmp/continuity-harness-comparison-001
python3 -m continuity_harness --language en challenge --out /tmp/continuity-harness-challenges-001
python3 -m unittest discover -s tests -p 'test_harness*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

`RUN_DIRECTORY`, `AUTHORITY_DIRECTORY`, and `REFERENCE_SHA256` are the exact run path, retained-authority path, and independently recorded reference digest from the suite's `INDEX.json`. The authoritative reference is retained separately from the candidate's work. Do not replace the pin with a digest recomputed from an untrusted candidate package. Missing the pin cannot produce a favorable authority assessment. Use `--language fr` for the French interface. Machine identifiers, commands, schemas, and evidence hashes remain shared across languages.

`demo` executes the three base controls with the Harness-supported method. `compare` executes 24 conventional/Harness runs over four fixtures and three controls, and retains 12 explicit AI **NOT RUN** entries. `verify-suite` reads each current run and retained reference again; it does not trust saved results. Use `--help` on the main command or a subcommand for complete localized help.

Exit code **0** means the requested suite's expected assertions passed, or an individual verification demonstrated complete fulfillment. Code **3** means that suite gate or individual full-promise claim was not established successfully. Consequently, fresh verification of a correctly constrained, partially fulfilled run returns **3**, while the demonstration can return **0** because it observed exactly that declared partial outcome. Code **2** indicates an invalid command or command-level error. Always read the structured fields; an exit code alone does not describe each obligation.

Each new suite directory contains:

| Record | Purpose |
| --- | --- |
| `INDEX.json` | Run locations and separately recorded reference pins; suite completeness. |
| `ATTEMPTS.jsonl` | Started and finished attempts, retained if the suite is interrupted. |
| `SUMMARY.json`, `SUMMARY.en.md`, `SUMMARY.fr.md` | Structured suite comparison and its two language summaries. |
| `runs/RUN/RESULT.json` | Fresh acceptance result for the run. |
| `runs/RUN/PASSPORT.en.md`, `PASSPORT.fr.md` | Two full presentations of the same result, including the exact fresh-verification command. |
| `runs/RUN/evidence/` and `controller.json` | Closed durable database, fulfillment artifacts, and observed execution/fault record. |
| `authority/RUN/` | Retained contract, reference, journal and execution seal, inaccessible to candidates. |

Existing output directories are refused. Use a new path to preserve an earlier unsuccessful or incomplete attempt. Only processes created by this Harness invocation are cleaned up.

Fresh verification reads current durable evidence. Opening a saved Passport only reads a past report. A changed artifact, missing authority, incomplete run, verifier error, or unsupported version must remain visible in the new assessment.

## Read a result correctly

Every run separates these fields:

| Field | Meaning |
| --- | --- |
| Test assertion | Whether the test observed its declared expected behavior. |
| Target verdict | What the tested component reported. |
| Evidence stage | Which exercise or observation actually occurred. |
| Claim status | Whether the specified claim was demonstrated, failed, or remains not established at that stage. |
| Per-obligation outcome | What happened to each recipient's exact obligation. |

A successful test can reproduce a defective checker's false acceptance. A correctly refused capacity request can demonstrate a safety property while leaving an order unfulfilled. Neither permits a complete-continuity claim.

## Comparison and costs

The conventional and Harness-supported procedures receive equivalent candidate-visible information, services, permissions, and fault schedules. Ordinary reconciliation, transactions, and idempotency are available to the conventional procedure. Every method uses the same fresh acceptance verifier and isolated starting state.

An AI adapter is a separate comparison arm. Without a suitable explicitly configured local capability, its performance result is **NOT RUN**. A recorded response or stub can exercise the interface but cannot establish AI performance. No model download, paid API, account creation, or credential is required by the default demonstration.

Execution wall time, child-process and controller CPU, run storage, broker requests, retries, and worker restarts are recorded with their collection boundaries. Configured logical ticks are not measured wall-clock hours. Accepted completion time is a conservative trusted observation after artifact export/fsync, distinct from the receipt's earlier producer transition timestamp. Peak memory, separate verification effort, preparation, integration, human labor, monetary rates, and external business costs remain unknown unless actually recorded. The recorded zero human interventions concerns the autonomous run only. Missing costs prevent an unqualified claim that one method is cheaper.

The three preregistered transfer fixtures change quantities to 700/900, 600/500, and 1,200/1,000 units, change capacities and dependency identifiers, and add a second-order specification amendment. Both real methods reuse the same interfaces and derive their orders from the input journal. These are held out from the base demonstration, not hidden repository data or a representative sample of businesses. One observation per method/control/fixture can establish that execution's output; it cannot establish a stable performance or discovery advantage.

## Retained adversarial and ablation evidence

`challenge` preserves eight separately labeled controls: no-journal recovery ablation; a coherently resealed 1,850-unit candidate package; an omitted reference pin; changed artifact bytes with a stale favorable Passport; shared failed dependency; and three deliberately defective verifiers that ignore byte integrity, ignore permission revocation, or reject valid recovery. The ablation retains ordinary service validation and transactions. Its failure is not evidence of incremental AI value.

This noncomparative suite creates four new local executions: one positive control and three procedure challenges. The remaining cases reuse copies of the positive control's evidence. Copied execution costs must not be added as new measurements. Fresh verification durations for the challenge are measured separately in its structured record.

The output contains `CHALLENGE_SPEC.json`, `ATTEMPTS.jsonl`, `SUMMARY.json` and bilingual summaries; `positive-control/run` and `positive-control/authority`; and `cases/CASE/` for each challenge. Each case retains its own `run/`, `authority/`, `TARGET_RESULT.json`, `REFERENCE_RESULT.json`, `CHALLENGE.json`, and full English/French Passports. The outer assertion and scoped claim assess the named procedure/checker property; the unchanged reference record supplies the underlying obligation outcomes. A test exposing false acceptance can pass while the mutated checker's qualification fails.

Use the exact `verify` command and independently recorded pin in a case Passport to inspect its current durable evidence with the unchanged verifier. Deliberately omit the pin to reproduce the missing-pin case. Ordinary `verify` reproduces the reference assessment; rerun `challenge` in a new directory to reproduce a deliberately mutated target. `verify-suite` applies to the indexed demonstration/comparison format, not this challenge directory. No mutant changes the installed verifier source.

## Preserved history and next evidence

This is a separately versioned implementation alongside the preserved `continuity_omega` research prototype. The [migration boundary](../../MIGRATION.md), [provenance manifest](../../PROVENANCE.json), original PDFs, evidence records, releases, and links retain their historical meaning. The [historical counterexamples](../continuity-omega-paper/EVIDENCE.md) are not erased by a new implementation.

Before any real-world rehearsal, the remaining evidence includes genuine authority over an order, permitted source custody and disclosure, an actually qualified backup provider and capacity window, an agreed acceptance procedure, measured operational conditions, and complete commercial obligations. The [proposed pilot](../continuity-omega/REAL_PILOT.md) describes that separate stage. A local synthetic transfer does not establish a paying customer or supplier network.
