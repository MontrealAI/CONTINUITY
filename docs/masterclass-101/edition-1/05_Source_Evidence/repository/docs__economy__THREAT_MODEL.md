# CONTINUITY Ω — Economy experiment threat model and limits

[Français](THREAT_MODEL.fr.md) · [Architecture](ARCHITECTURE.md) · [Product specification](PRODUCT.md)

## Security claim being tested

Within a disposable local exercise, a candidate must not turn an altered promise, unsupported arrangement or invalid output into independently verified success by editing candidate-controlled inputs, recomputing hashes, replaying a favorable status or retrying an uncertain action. Verification must preserve missing evidence and distinguish an execution failure from a successful test that detected that failure.

The protected obligation is the new digital product defined by the retained contract. The scope does not include real customer authentication, physical labels, malicious host administration, external payment systems or certified third-party acceptance.

## Assets and trust

| Asset or component | Trust placed in it | What it does not establish |
| --- | --- | --- |
| Host, kernel and local filesystem | Correct syscall confinement, clocks, SQLite/filesystem durability and process termination | Protection against root, a compromised kernel, hardware faults or every power-loss behavior |
| Controller and startup imports | Honest contract retention, policy custody, fault application, broker authorization and evidence finalization | Candidate safety before trusted initialization, independent organizational oversight |
| Synthetic authority and journal | Authored events represent the exercise’s retained instructions; completeness is explicitly supplied and checked | Authentic customer instructions or complete real-world source capture |
| Clock | One trusted monotonic clock for observed durations and recorded logical ticks | A distributed trusted timestamp or real supplier deadline measurement |
| Participant services | Policies cannot be changed through candidate operations; decisions and transfers are durably recorded | Real legal consent, contracts, finance or willingness to pay |
| Receiver | Independently implemented inspection with retained specification and durable literal imports | Independent authorship, external customer endorsement or physical testing |
| Fresh verifier | Correct separate checking of authority, actual content, timing, ledgers and records | General mathematical proof or immunity to a verifier implementation defect |
| Reporter | Faithful bilingual presentation of one record | New proof from a saved Passport |

All actors share a local host and development authorship. Separate processes create control and state boundaries; they do not create third-party certification.

## Actual isolation mechanism

The authority and execution directories must be disjoint. The authority retains the original contract, policies, source-bound reference, capacity inputs and final execution seal. The caller retains the original reference SHA-256 outside candidate control. Supplying a newly computed digest from an untrusted rewritten package does not establish that original.

The unchanged qualified baseline’s `continuity_harness/sandbox.py` installs a Linux x86-64 seccomp-BPF allowlist after trusted imports and descriptor closure. The candidate is restricted to its preexisting standard streams and permitted computation syscalls. Path opens, network creation, process spawning and cross-process inspection are denied. The filter changes no account, credential, file mode or host access policy.

Before candidate operations, the controller requires five successful denial probes: authority open, workspace open, network, spawn and process inspection. An unsupported platform or failed probe cannot produce a qualified run. Candidate visible contract and policies arrive through the pipe after isolation; retained acceptance evidence and reference seals are not supplied.

The broker accepts a bounded set of validated operations and derives production, capacity and delivery identities itself. Internal service fault hooks and policy administration are controller capabilities, not arbitrary candidate commands. Identical confinement and broker permissions apply to both implemented methods.

This mechanism trusts startup code and the kernel. It is not a sandbox for arbitrary unreviewed Python import code, a container boundary against administrators or protection against every side channel. Denial probes are observations of those specific paths and syscalls, not exhaustive kernel verification.

## Adversaries, faults and defenses

| Challenge | Required response or evidence |
| --- | --- |
| Coherent candidate rewrite of 1,900 units to 1,850 with new hashes | Original external reference and retained obligations still govern; altered bytes cannot satisfy them |
| Missing authority, original pin or source completeness | `NOT_ESTABLISHED` rather than favorable acceptance |
| Correct metadata with wrong, missing or corrupt substantive content | Receiver and fresh verifier parse the real bytes and compare every literal unit |
| Stale revision, wrong recipient, canceled obligation or lost amendment | Replay retained source state and bind every accepted unit to the frozen obligation |
| Duplicate JSON keys, Boolean money, string quantities, unknown fields, unsafe paths or unsupported versions | Structured refusal before affected state changes |
| Competing requests, overlapping capacity or withdrawn resources | Transactional ledger invariants and independently replayed evidence |
| Shared failed dependency | Both affected routes remain unavailable; naming a second provider does not prove independence |
| Uncertain acknowledgment, retry or process crash | Reconcile the original stable identity and durable state; never assume the action failed |
| Corrupted export, truncated transfer or interruption | Preserve actual bytes, partial files and stage history; no fabricated complete product |
| Rejection followed by repair | Same-agreement/lot rejected A1 predecessor, distinct A2 capacity and cost, both records retained |
| Revoked consent, changed price/liability or removed funding | Evaluate the effective policy and available funds at the affected action; preserve earlier decisions |
| Replayed acceptance, mixed-run artifacts or stale favorable Passport | Recheck run/contract/content/recipient/timing bindings from durable evidence |
| Cancellation after an accepted subset | Broker refusal, retained active agreement/escrow/liabilities and an unresolved partial-settlement state |
| Verifier crash, missing snapshot or uncheckpointed state | Incomplete verification or `NOT_ESTABLISHED`, never an inferred pass |
| Defective checker mutation | A passing detection test leaves the defective checker’s qualification failed |

The producer’s completion, recipient’s receipt and recipient’s acceptance are separate stages. In particular, a rejected product can consume capacity and modeled costs. A correct refusal can preserve safety while the full customer obligation remains unfulfilled.

## Consent, liabilities and timing

Participant policy versions are retained. Consent is active while the action tick is strictly before `consent_until_tick`; a revocation at tick `t` blocks its affected action at `t` and later. An agreement’s original accepted terms remain recorded. Price, funding and liability changes cannot be hidden by rewriting a proposal or account balance.

Historical actions are never erased retroactively. A replay of an already completed action retrieves its existing record. A new production, transfer or acceptance action requires authorization under the effective conditions. A deliberately funded technical control is distinct from trade and requires its own permission.

Logical product deadlines are inclusive, while proposal expiry and consent expiry are exclusive. A retained decision without a post-commit observation cannot prove timely acceptance. Retries after a durable timely observation preserve that original time; observations created after a crash use the later actual time. The verifier also checks the declared observation cutoff.

Modeled liability and outside-option assumptions are explicit fixture inputs. Amounts are exact synthetic minor units, with **100 minor units per fictional `SMU`**; the reports do not rescale the stored integers. Money is conserved across accounts, holds and modeled transfers; funds cannot be counted twice. This ledger does not settle legal obligations or discover real preferences. Positive synthetic margins never establish real voluntary demand or commercial advantage.

The current settlement protocol requires complete accepted work. Once any receiver acceptance has accrued, the broker blocks cancellation even if the remaining work fails or acceptance timing is unresolved. The agreement remains `ACTIVE`, and remaining escrow and liabilities stay recorded. No partial-settlement protocol is implemented. The verifier must expose this unresolved state, not interpret held funds as completed payment, erase accepted work or release liabilities through silent cancellation.

## Fresh verification and evidence custody

The fresh verifier reads actual finalized SQLite files and raw output, not producer labels, snapshot summaries or saved results. It separately checks source replay, literal content, capacity records, participant decisions, monetary conservation, acceptance references and observations. Shared strict schemas and serialization are neutral infrastructure; producer generation and receiver decision functions are not verification oracles.

The controller captures full logical database digests at idle boundaries, checks checkpoints, closes writers and backs up committed state into standalone evidence. The verifier refuses incomplete SQLite sidecars and checks read-only database integrity. Execution seals bind the resulting files to the retained authority. Changes during verification are detected where checked; concurrent hostile host rewriting is outside the trust model.

Hash equality establishes **byte integrity**, not customer source identity, custody independence or source completeness. Those properties are separate inputs and claims. A missing original authority reference cannot be repaired by trusting a candidate’s self-consistent replacement.

Failed and incomplete runs, canceled proposals, rejected products and corrections remain inspectable. Reassessment appends or preserves earlier reports rather than rewriting history into success. Only Harness-owned disposable processes are terminated; generated evidence is not automatic cleanup.

## Evidence limits and next boundary

Tests cover declared bounded fixtures, explicit transition hooks, deterministic races and selected mutations. Finite enumeration applies only to the stated finite domain; sampled crash schedules do not prove all interleavings, universal exactly-once delivery, unrestricted route planning or malicious-host resistance. Process-kill durability is not a full power-loss campaign.

Measured local execution and verification resources exclude unrecorded engineering and adaptation labor; shared-host child CPU accounting can include concurrent exercises. A capability unavailable on the host remains `NOT_RUN` or not established. A simulated or recorded AI trace is not AI performance.

Before an authorized real rehearsal, the additional evidence must include an authenticated customer’s new digital obligation, a genuinely separate recipient acceptance implementation and custody arrangement, actual provider permissions and dependency evidence, observed capacity windows, explicit participant agreements and rework liabilities, funded terms and measured integration/adaptation effort. Any physical-output claim additionally requires a retained physical acceptance protocol and observed physical tests. This release supplies none of those real-world observations.
