# CONTINUITY Ω Harness — Threat model and limits

**English** · [Français](THREAT_MODEL.fr.md) · [Architecture](ARCHITECTURE.md) · [Requirements](REQUIREMENTS.md)

## Security claim in scope

The scoped claim is that a candidate process cannot redefine the retained exercise contract, read hidden acceptance evidence through its permitted execution interface, or turn changed local outputs into accepted completion of the original promise. The controller and fresh verifier must also expose incomplete or contradictory evidence.

This is a claim about the specified local software exercise. It is not protection against a malicious host administrator, kernel compromise, a hostile controller, physical storage failure, fraudulent real-world business records, or an external supplier. The implementation and tests must be consulted before treating an intended boundary as established.

## Trusted and untrusted components

| Component | Trust assumption | Failure implication |
| --- | --- | --- |
| Host kernel and Python runtime | Enforce process isolation and execute the programs as specified. | A compromised host can alter memory, code, evidence, or observations; outside this threat model. |
| Exercise authority | Retains the agreed synthetic contract and original reference independently of the candidate. | Missing or mismatched authority prevents a favorable integrity conclusion. |
| Controller and broker | Enforce operation allowlists, clocks, resource bounds, and fault schedules; record actual transitions. | Fabricated controller observations invalidate the exercise; separate audit is required to assess a hostile controller. |
| Authored event journal | Supplies the declared synthetic observations through the frozen cutoff. | A matching hash proves identity with that fixture, not authenticity or completeness of real customer instructions. |
| SQLite, filesystem, and local services | Provide the documented transactional and persistence behavior under tested process interruption. | Process-kill experiments do not establish hardware or power-loss durability on every storage stack. |
| Clock | Host monotonic observations are trustworthy within one exercise; logical ticks follow the frozen controller schedule. | Missing or inconsistent clock evidence leaves relevant deadline claims unestablished. |
| Acceptance verifier | Implements independent source replay and checks current durable outputs. | It needs its own counterexamples and mutation tests; a passing candidate cannot qualify its verifier. |
| Candidate | May return malformed requests, change its visible inputs, make an incorrect plan, retry, or crash. | Every action still requires broker/service validation; its statements are not acceptance evidence. |
| Saved Passport | Is a presentation of a particular past assessment. | It is never an oracle for a fresh verification. |

All components share this project's authorship unless a record explicitly identifies an external assessor. Separate code paths and separate AI workstreams are not third-party certification.

## Candidate isolation

The v0.1 implementation uses a Linux x86_64 seccomp BPF filter installed inside the candidate process after its required modules are loaded. The shipped launcher, candidate module, and imports are trusted during that initial loading phase. Arbitrary third-party Python plugins or untrusted imports are not supported. Candidate data arrives through bounded standard input after the filter is active.

The candidate communicates through inherited standard-input/standard-output pipes to a constrained broker. It has no filesystem operations, including direct writes to its own workspace. All durable effects occur through allowlisted broker operations. It does not receive arbitrary database, socket, or process-control operations.

The filter's allowlist denies filesystem opens, process inspection, new process execution, and network creation. The launcher closes descriptors 3 through 65,535, and the controller starts it with `close_fds=True`; only the declared standard streams remain. Denying a new file open alone would not invalidate an already-open authority descriptor. The broker rejects operations such as service initialization, full administrative snapshots, authority registration, arbitrary paths, fault injection, and caller-controlled clocks.

Every normal candidate launch records actual denial probes for the retained authority file, candidate workspace file, socket creation, process creation, and `process_vm_readv` inspection of its parent. The authority pathname is supplied to the probe; it is the access that is denied, not knowledge of the filename. The controller requires all five observations, and the fresh verifier checks their presence. [`ExecutedControls.test_kernel_isolation_is_actually_probed_for_each_method`](../../tests/test_harness_controller.py) covers both methods. [`test_harness_boundaries.py`](../../tests/test_harness_boundaries.py) exercises prohibited or malformed operations and bounded candidate-process behavior. Landlock returned `ENOSYS` in the implementation environment and is not the mechanism claimed here. No account, credential, or persistent system permission change is part of the process-local filter.

The supported platform and required kernel capability are explicit runtime preconditions. If the filter cannot be installed or the platform is unsupported, the protected candidate exercise must refuse to proceed with a favorable isolation claim. Schema, historical regression, and other unaffected checks can still run. There must be no silent fallback to a candidate that can read the oracle.

The host, controller, and services retain broader access by design. This boundary does not make an arbitrary privileged local program safe or provide protection against an administrator. Shared service infrastructure remains trusted. Access confinement and bounded protocol/time limits do not establish a complete denial-of-service boundary: v0.1 does not claim independently enforced host memory, CPU or disk quotas for a hostile candidate.

## Authority and source properties are different

| Property | What the Harness can establish within the exercise | What it does not establish |
| --- | --- | --- |
| Byte integrity | Current content matches a retained digest and supported canonical form. | Truth of that content. |
| Source identity | The source matches the registered authored fixture. | A real client's identity or signature. |
| Custody | The candidate cannot access the protected authority through the exercised interface. | Independent legal custody or protection from the trusted host. |
| Completeness | The fixture declares and checks its observation cutoff and completeness conditions. | Absence of undisclosed real-world orders, manual amendments, or competing reservations. |

The suite retains authority outside each candidate run and pins the reference separately. Fresh verification requires that reference and its recorded digest. Computing a replacement digest from candidate-controlled data would only establish a new internal consistency relation.

The execution seal binds current durable files after service shutdown and database checkpoint. Its storage is protected from candidates by the exercised process boundary; it is not an externally signed timestamp or immutable host-administrator store. Distinct suite invocations use distinct run identities, while their fault seeds and business conditions remain registered and comparable. A deliberately privileged test can reseal altered evidence to challenge semantic verification; that fixture does not give an ordinary candidate resealing permission.

An absent authoritative reference, missing required source coverage, or incomplete verification produces **NOT ESTABLISHED** for the relevant claim. A positively observed mismatch is a failure. Neither is equivalent to a proof that all possible continuity routes are impossible.

## Failures that must be observable

- Rewriting order events and all candidate-side hashes must not satisfy the original contract.
- Invalid types, duplicate JSON keys, unknown fields, non-finite values, unsafe paths, and unsupported versions must be rejected before state changes.
- A missing amendment, revived cancellation, wrong recipient/specification, duplicate artifact, or mixed-run receipt must fail acceptance.
- Competing reservations must not exceed capacity in any exercised overlap; repeat release or expiry must not create capacity.
- A committed action with a lost acknowledgment is uncertain until reconciled. Retrying must not create another completed obligation.
- A crash between durable receipt creation and artifact export must remain detectable and recoverable through reconciliation.
- An unavailable or withdrawn route and a shared failed dependency must affect execution; a declared backup is not necessarily an independent backup.
- A deadline violation, terminated verifier, timeout, incomplete controller, or changed artifact must not become a favorable full-promise assessment.

The [requirements matrix](REQUIREMENTS.md) identifies the executable evidence and its current status for these cases. A finite test suite samples behavior or exhausts an explicitly bounded model; it is not a general proof of safety or universal exactly-once delivery.

## Scope of commercial and transfer conclusions

No default command contacts customers or suppliers, reserves real capacity, reads production orders, spends money, downloads a model, or changes external access permissions. Cleanup is restricted to owned disposable processes; prior run evidence remains available.

Local software completion does not establish physical production, delivery, customer acceptance, revenue, profitability, or a viable supplier network. A held-out synthetic exercise demonstrates only the measured transfer under those conditions. Comparison against a competent conventional method can tie or favor the conventional method. Unknown labor and monetary rates remain unknown.

The next real-world stage requires separately obtained order authority, source custody, provider capacity, permitted disclosure, acceptance terms, operational evidence, and complete obligations as described in the [proposed pilot](../continuity-omega/REAL_PILOT.md). The Harness does not grant that authority.
