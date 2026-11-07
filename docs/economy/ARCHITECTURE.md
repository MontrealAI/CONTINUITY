# CONTINUITY Ω — Economy experiment architecture

[Français](ARCHITECTURE.fr.md) · [Product contract](PRODUCT.md) · [Threat model](THREAT_MODEL.md) · [Registered experiment](EXPERIMENT.md)

## Scope and historical boundary

Version 0.2.0 preserves a newly specified **digital label-job obligation**. It produces substantive bilingual content, transfers the bytes and imports accepted units into a separately controlled recipient database. It also tests whether an authored synthetic arrangement meets the participants’ declared constraints. These are separate assessments. Neither one establishes physical delivery, customer authenticity, real payments or commercial demand.

The qualified recovery baseline remains commit `396227d8da2f55f674f479de16089c7ce28ef290`, tag `continuity-harness-v0.1.0`. Its transactional capacity ledger, strict serialization, subprocess transport and candidate isolation are reused without changing historical code or claims. A baseline fulfillment receipt establishes consumed capacity in this experiment; it is never substituted for digital content or recipient acceptance. Exact reuse attribution is retained in [the experiment provenance](../../experiments/economy-v0.2/PROVENANCE.json) and each controller’s implementation record.

## Responsibilities and control

| Component | Controlled state and responsibility | Boundary |
| --- | --- | --- |
| Exercise authority | Original contract, participant policies, source journal, capacity inputs, reference and execution seal | Outside candidate access; independently supplied reference digest |
| Controller | Disposable processes, recorded clock, broker authorization, replayable faults, durable snapshots | Trusted local orchestration, not an independent organization |
| Candidate adapter | Proposes allocations and terms; invokes permitted operations | Same candidate-visible inputs and broker for conventional and Harness procedures |
| Participant service | Separate policy decisions, consent, agreement versions, funds, holds, incurred costs and modeled transfers | Candidate cannot rewrite policies or self-issue acceptance |
| Capacity services | Per-provider/window reserve, commit, release, expiry and durable capacity fulfillment | Allocation does not establish recipient acceptance |
| Producer | Durable product bytes, generation requests and materialization observations | Cannot establish its own successful delivery |
| Receiver | Original acceptance specification, received bytes, decisions, post-commit observations and imported literal units | Independently implemented content inspection |
| Fresh verifier | Replays retained authority, ledger evidence, actual content and receiver records | Never uses a saved Passport or producer/receiver verdict as its oracle |
| Reporter | English/French Passports from one structured verification record | Presents assessments without upgrading them |

`continuity_economy/schema.py` defines the versioned contract. `policy_schema.py` defines monetary and participation inputs. `controller.py` owns the broker. The producer, receiver and participant service are separate real Python processes with SQLite durable state; candidates communicate only through bounded standard-input/output messages.

## Frozen inputs and stable identities

Before execution, the controller retains the materialized obligations, event cutoff, zero permissible recovery loss, revisions, recipients, exact content fields, deadlines, windows, resources, permissions, allowed actions, revocations, fault schedule and schema versions. The candidate receives the same contract and policy information for both implemented methods. The reference pin, retained execution seal and final acceptance evidence are not candidate inputs.

An obligation has an exact ordinal range `1..quantity`. If splitting is allowed, fixed lots partition that range; otherwise the whole obligation is one lot. Neither executor may make the promise smaller to fit a route. A changed promise needs a new retained contract and assessment.

| Identity | Derivation |
| --- | --- |
| Lot | `{obligation_id}.L{index:03d}`, with index starting at 1 |
| Production and capacity key | `{agreement_id}.{lot_id}.A{attempt}` |
| Delivery | `{production_id}.D` |
| Baseline capacity order | `{lot_id}.A{attempt}` |

The first attempt is `A1`. The sole supported correction, `A2`, names the same agreement and lot’s durably rejected `A1` delivery. Its distinct capacity key and production charge preserve both attempts. Cross-agreement repair of a partially delivered promise is unsupported.

Before any recipient acceptance, a failed agreement may instead be durably canceled and replaced by a separately accepted agreement starting at `A1`. That is new funded production, not a discounted correction. Earlier sunk costs, consumed capacity and rejected bytes remain. The broker and fresh verifier enforce cancellation, non-overlapping commitments and funding; the receiver independently enforces correct content and unique accepted units.

## Executed lifecycle

1. **Recover and propose.** The adapter can restore the primary from its stale state plus the protected journal, use the conventional backup or search permitted compatible allocations. All proposed terms and participant decisions remain records, including rejected proposals.
2. **Accept an arrangement.** The participant service evaluates the buyer’s authored value interval and outside option, provider costs and participation thresholds, coordinator costs, liabilities, consent and currently available funding. A proposal is not an agreement until those decisions and funding holds are durable.
3. **Reserve and produce.** The broker checks route permissions, dependencies, current consent and the chosen window. Capacity is reserved and committed. The participant ledger charges the unique production attempt. The producer persists substantive bytes before exporting an artifact. Capacity fulfillment then records actual local production.
4. **Transfer and receive.** After a fresh authorization, the controller copies the actual file into the receiver’s inbox. The receiver stores those bytes durably. Receipt alone does not accept their content.
5. **Inspect and accept or reject.** The receiver parses the bytes against its retained contract, imports correct unique units transactionally and records a separate post-commit observation. Rejected bytes and decisions remain. A permitted correction requires a new attempt and new resources.
6. **Settle or resolve incomplete work.** Settlement requires one timely accepted delivery for each allocated lot. Before any recipient acceptance, cancellation releases remaining holds but preserves incurred costs and explicitly declared cancellation liabilities. After an accepted recipient decision, the broker refuses cancellation. A failed partial arrangement remains `ACTIVE` with its remaining escrow and liabilities retained; partial settlement is unsupported and unresolved. Accepted work is not erased, held funds are not treated as paid, and a partial promise is not reported as complete. The fresh verifier rechecks every acceptance reference and financial effect.
7. **Finalize and verify.** At explicit idle boundaries, the controller captures logical database digests, checks full checkpoints, closes owned children and exports standalone SQLite backups. It compares logical contents before sealing final evidence. Fresh verification checks those actual files and the separately retained authority.

These stages span several databases. They are **not a distributed atomic transaction**. Stable identifiers, durable stage records and restart reconciliation handle the tested interruption points; unresolved cross-service state remains an incomplete result.

## Timing, faults and uncertainty

Logical ticks drive declared windows, lease expiry, consent and deadlines. A monotonic host clock separately bounds observed execution. An accepted decision without its post-commit observation does not establish timely acceptance. If the acknowledgment is lost after that observation, a retry returns the original durable outcome without accepting units twice.

Faults are registered by event, operation trigger, occurrence and target. Named service hooks create deterministic interruption points around transactions and file export. Tests use process termination and barriers, not arbitrary sleeps to choose race outcomes. A canceled or revoked action remains in history: revocation blocks affected future actions from its effective tick and does not erase an earlier observed action.

Capacity conservation, money conservation and accepted-unit uniqueness have distinct ledgers and checks. Reservations consume capacity until released or expired; committed work follows the baseline semantics, and fulfilled capacity cannot be released. Rejected product can therefore consume real modeled resources without satisfying any customer obligation.

## Economic interpretation and comparison

Every monetary amount is an exact integer in synthetic minor units: **100 minor units equal 1 fictional `SMU`**. Reports preserve those integer values without rescaling. Costs, balances, value intervals, outside options and participant preferences are authored fixtures. The simulated ledger keeps funding holds separate from transfers and production costs. The verifier checks both initial agreement feasibility and realized campaign effects, including canceled arrangements, repair costs and still-held funds.

An explicitly authorized, funded technical control can demonstrate accepted digital content after a trade is rejected. It does not demonstrate a viable trade or real willingness to pay. An uncertain value interval yields possible versus definite modeled feasibility; the implementation must preserve that uncertainty.

The conventional and Harness adapters have the same route domain, tools, permissions and useful reusable material. Their search procedures can differ; execution and verification services are shared. Unavailable direct AI is `NOT_RUN`. A no-purchase control is separate. Measured CPU, elapsed time, requests, storage, retries and failures do not substitute for unmeasured preparation, integration, adaptation or human verification labor. No complete-cost advantage follows while those categories remain unknown.

## Evidence and inspection

The canonical record separates test assertion, component verdict, evidence stage and claim status. It reports each obligation’s production, receipt, rejection and timely accepted quantity; each arrangement’s decisions and terms; modeled campaign accounts; faults; source versions; evidence hashes; measured resources and missing categories.

`PASSPORT.en.md` and `PASSPORT.fr.md` render the same record with translated titles, explanations, quantities and uncertainties. Both include the complete unchanged machine record. Reassessment preserves earlier Passport bytes under `passport-history/`. A passing adversarial test can expose a failed checker; the reporter keeps that qualification distinct.

Implementation links: [controller](../../continuity_economy/controller.py), [producer](../../continuity_economy/producer.py), [receiver](../../continuity_economy/receiver.py), [participants](../../continuity_economy/participants.py), [fresh verifier](../../continuity_economy/verifier.py), [reporter](../../continuity_economy/reporting.py). Product and process controls are in [the product tests](../../tests/test_economy_product.py); reporting parity is in [the reporting tests](../../tests/test_economy_reporting.py).
