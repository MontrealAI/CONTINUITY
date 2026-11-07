# CONTINUITY Ω

## Evidence you can check

Understand the results, challenge the claim and see what proof comes next

Edition 2 · 7 November 2026


## What the evidence lets you say

**The public repository supports an executed local continuity exercise.** Its software reconstructs specified obligations, tries a permitted route and checks the resulting artifacts against the retained promise. That is a useful, inspectable engineering result. Its meaning depends on the exact exercise and the evidence behind it. [R1, R2, R3]

![Each broader claim needs additional observations. The public main-branch evidence reaches executed local software; customer delivery and a repeatable commercial service require their own proof. [R2, R4, R6]](../06_Visuals/evidence_ladder_en.png)

### Outcome

Did the specified work meet the original acceptance conditions?

### Service feasibility

Can willing participants provide the permissions, capacity, timing and funding the arrangement needs?

### Market evidence

Do actual purchases, accepted delivery and complete costs support the commercial claim?

> **The scope of this book**
> The sources were checked on 6 November 2026 at 20:36 Toronto time. Main remained at 396227d8. This editorial review did not rerun repository tests or a business exercise. The precise revision and commands appear later.


## One order book makes the idea concrete

A restored application can run while its order book is wrong. The base exercise exposes that problem with three label orders. The retained event history contains an amendment and a cancellation that the stale restore has missed. [R2]

| Order | Retained obligation | Stale restored record |
| --- | --- | --- |
| A | 1,100 units | 1,000 units |
| B | 800 units | Missing |
| C | Canceled | 600 units still shown |
The authoritative total is **1,900 units in two orders**. Correct reconciliation must restore B, use A’s amended quantity and keep C canceled. A route cannot improve its apparent result by quietly removing an obligation. [R2, R3]

| Route exercised | Recorded outcome |
| --- | --- |
| Feasible primary recovery | Both obligations completed: 1,900/1,900. |
| Authorized backup with 2,100 units of capacity | Both obligations completed: 1,900/1,900. |
| Constrained backup with 1,500 units of capacity | A completed: 1,100. B refused: 800. Only 400 units remained after A. |
> **Two verdicts can both be correct**
> In the constrained run, the tested capacity constraint is respected and the full promise fails. Refusing an order prevents overbooking; the unfulfilled 800 units remain visible. A passing test assertion can correctly report that partial outcome. [R2, R3]

These counts refer to durable local software outputs. The exercise does not establish printed labels or delivery to real customers. Physical production and customer acceptance need their own observations. [R2, R3]


## Read the record without losing its history

| Record | Meaning |
| --- | --- |
| Research prototype · a755d037 | 29 authored tests passed; separate probes exposed input and source-authenticity weaknesses. Synthetic handoff only. [R7] |
| First Harness qualification · 5c92fd03 | A favorable saved summary failed later fresh verification. The attempt remains unqualified and preserved. [R3] |
| Qualified Harness · fa9da1f5 | Second attempt: 245 tests and 24 comparison executions. All 12 conventional/Harness pairs tied. [R3] |
| Current main · 396227d8 | Later route-permission and queue-lease repairs; 253 local tests reported. Historical results retain their identities. [R5, R9] |
The repairs allow authorized primary recovery without requiring backup-provider sharing permission. Both methods also reserve bounded batches so queued leases do not all age at once. Short leases, deadlines and insufficient capacity remain real constraints. [R5]

The historical count of **245** and the later count of **253** describe different revisions. The registered comparison establishes executable methods, with **12 functional ties**. All **12 AI entries are NOT RUN**; an incremental AI or complete-cost advantage is not established. [R1, R3, R5]

> **Pending v0.2 review**
> At the source check, PR 3 was open and unmerged, with review head f9e56c7dd9627b322406e05c53b4f6537d434262. It proposes a separate digital-product and modeled-participation experiment. Those review-branch claims are kept outside this volume’s main-branch result table. The preserved status is dated; a later reader should check for a subsequent decision. [R10, R11]


## What “independent” means here

Here, the useful separation is concrete: **the verifier reconstructs the obligations through its own source replay and checks current durable outputs against a separately retained contract and reference**. A candidate’s assertion that it succeeded is not sufficient acceptance evidence. [R2, R4]

![Construct, challenge and check against the original promise. A repair is tested again; the verdict stays scoped to the evidence actually examined. [R2, R3, R4]](../06_Visuals/verification_loop_en.png)

- Retain the original authority outside the candidate’s permitted control; changing a candidate-side copy must not change the obligation.

- Read current artifacts when checking again. A saved Passport describes a past assessment.

- Challenge the verifier itself, including false acceptance and false rejection. A checker that refuses every result is not qualified.

> **The trust boundary remains explicit**
> The host, controller, services, authored journal, clock and verifier remain trusted. Separate code paths under shared project authorship are not third-party certification. Matching hashes establish byte identity, not authentic or complete real customer instructions. [R3, R4]


## Give a critic a decisive test

A useful objection identifies an observation that would change the verdict. The documented challenge families below make that practical. They are a reading and review guide to retained experiments, not new experiments performed for this book. [R2, R3]

| Challenge | What the check should establish |
| --- | --- |
| Change a candidate’s 1,900-unit obligation to 1,850 while retaining the original authority. | The changed package cannot satisfy the original full promise. Coherent candidate-side hashes do not make the rewrite authoritative. |
| Alter an output while keeping an old favorable Passport. | Fresh verification must assess the changed artifact. The old report cannot certify its present state. |
| Remove the independently retained reference pin. | Authority remains NOT ESTABLISHED. Recomputing a convenient replacement pin does not close the gap. |
| Make the backup share the failed dependency. | An unavailable logical backup cannot support completed fulfillment through that route. |
| Present a valid positive control to a deliberately defective checker. | False rejection must also disqualify a checker. Successful evidence should be accepted when the stated conditions are met. |
| Give a competent conventional method the same tools and information. | A tie does not establish improvement. Any advantage claim must survive the complete comparison and its cost boundary. |
For a reproducible challenge, preserve the original authority, identify the altered copy or test mutation, record the target’s answer, then retain the separate reference verdict. State precisely which claim fails. The project’s shared-helper counterexample—accepting 1,850 against an original 1,900—shows why checking the checker matters. [R3, R9]

> **Read the right verdict**
> An adversarial test can pass because it exposed false acceptance. In that same record, the defective checker’s qualification fails. Test success and business success answer different questions. [R2, R3]


## Reproduce the pinned software record

Use Linux x86_64 with seccomp BPF, Python 3.10 or later, and Node.js for the repository-wide website tests. The default exercise uses local synthetic data and standard-library components. Choose unused output paths; previous attempts are preserved. These commands were not executed for this editorial collection. [R2, R5]

```sh
git clone https://github.com/MontrealAI/CONTINUITY.git
cd CONTINUITY
git checkout --detach \
  396227d8da2f55f674f479de16089c7ce28ef290
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m continuity_harness --language en demo \
  --out /tmp/continuity-evidence-demo-001
python3 -m continuity_harness --language en verify-suite \
  --in-dir /tmp/continuity-evidence-demo-001
python3 -m continuity_harness --language en compare \
  --out /tmp/continuity-evidence-comparison-001
python3 -m continuity_harness --language en verify-suite \
  --in-dir /tmp/continuity-evidence-comparison-001
python3 -m continuity_harness --language en challenge \
  --out /tmp/continuity-evidence-challenges-001
```
Read the structured result and each obligation. Suite exit 0 means the expected assertions passed; it can include an expected partial outcome. Individual verification of a partial promise returns 3. Exit 2 indicates a command error. Historical qualification uses its own code and archive pins in R3. [R2, R3]

> **One distinction that prevents a false recheck**
> In this v0.1 interface, verify-suite applies to indexed demo/comparison outputs, not challenge directories. For an individual challenge, use its exact verify command, authority path and original reference digest. Keep that pin independently of candidate-controlled data. [R2]


## The next decisive proof

The next useful observation is an authorized rehearsal for one real business, with an actual provider and a capable alternative. The repository’s printer pilot is a proposal without real approvals. Its value is the falsifiable test it defines. [R6]

| Decision | Evidence that would change it |
| --- | --- |
| Was the promise met? | An authentic order, frozen acceptance terms and an authorized assessor’s decision about the output actually produced. Distinguish a rehearsal substitute from physical customer delivery. |
| Was the arrangement feasible? | Real participant consent; lawful data use; qualified capacity net of other commitments; usable dependencies; funded production, correction and remaining obligations. |
| Was this commercially worthwhile? | The buyer’s actual purchase decision, collected payment, complete campaign costs and residual liabilities, compared with the same-promise conventional alternative and no purchase. |
Count preparation, failed attempts, integration, staff time, reservations, execution, verification, transport where relevant, financing, support and refunds. Record when funds are needed and when they clear. A positive modeled margin cannot establish these observations. [R6, R7]

> **The claim should grow with the evidence**
> One paid, accepted pilot supports a claim about that transaction. A repeatable service needs further evidence about continued demand, available capacity and complete economics. A useful retained method needs a separate fresh task and a fair comparison before it earns a successor-benefit claim. [R6]

A conventional winner, a no-buy decision or a failed exercise is still a decisive finding. Preserve the conditions and the reason. The next experiment can address the demonstrated obstacle rather than assume the market already exists. [R6, R8]


## Leave an evidence package another person can use

A reader should be able to locate the original promise, the execution, the current check and the claim being made. The Harness separates these records so a later review can inspect the result again. [R2]

| Record | What to inspect |
| --- | --- |
| INDEX.json | The run list, completeness and retained reference pins. Preserve its custody when transferring the evidence. |
| Retained authority | The contract, source history and original reference. Identify which facts are authored and which have external authentication. |
| Durable evidence and controller record | The actual database, artifacts, observed transitions, interruptions and timing within the declared trust model. |
| RESULT.json and bilingual Passports | The assessed outcome, failed or missing conditions and exact verification command. A saved presentation is a record of its assessment. |
| Fresh verification receipt | Which revision, current files and retained reference were checked, what the verdict was, and when the check occurred. |
### Understand the executed result

Start with the guide, full results and later repair notes: R2, R3 and R5.

### Test the claim’s foundations

Read the threat model, registered experiment and retained validation history: R4, R8 and R9.

### Decide on the next field step

Use the proposed pilot R6, with R7’s historical boundaries and R1’s repository map.

> **Source custody for this edition**
> Complete pinned source snapshots accompany the collection. Their Git blob identities and SHA-256 records establish faithful copying. They do not establish the truth of every source assertion or a new execution of its experiments. Main and the pending review branch have separate records.


## Sources

- R1: Repository overview. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/README.md
- R2: Harness guide. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/README.md
- R3: Executed qualification results. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/RESULTS.md
- R4: Threat model and trust limits. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/THREAT_MODEL.md
- R5: Route and queue repairs. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/REPAIR_NOTES.md
- R6: Proposed real pilot. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/continuity-omega/REAL_PILOT.md
- R7: Historical prototype guide. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/continuity-omega/README.md
- R8: Registered comparison protocol. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/EXPERIMENT.md
- R9: Validation history. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/VALIDATION_HISTORY.md
- R10: Pull request 3 — open, unmerged review status. https://github.com/MontrealAI/CONTINUITY/pull/3
- R11: Pending v0.2 experiment guide — review branch. https://github.com/MontrealAI/CONTINUITY/blob/f9e56c7dd9627b322406e05c53b4f6537d434262/docs/economy/README.md
