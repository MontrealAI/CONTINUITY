# CONTINUITY Ω Harness — Invent the economy of continuity

[Français](README.fr.md) · [Architecture](ARCHITECTURE.md) · [Threat model](THREAT_MODEL.md) · [Digital product](PRODUCT.md) · [Registration](EXPERIMENT.md) · [Requirements and tests](REQUIREMENTS.md)

**Version 0.2.0 is a separately registered digital-product experiment.** It asks whether a permitted arrangement among modeled participants actually delivers the same specified digital product, whether that arrangement satisfies their authored economic constraints, and whether its method improves on a competent conventional procedure. These are three separate claims. A positive synthetic margin does not establish a sale, real demand or a method advantage.

The new obligation is a bounded JSON label-job package containing substantive English/French content for every unit. A separate receiving process retains the bytes, imports the labels, checks literal content against its retained contract and records acceptance durably. This is semantic digital acceptance in a synthetic exercise. It does not establish rendered appearance, print readiness, physical delivery or authentic customer authorization. Historical v0.1 metadata artifacts keep their original meaning.

## Prerequisites and clean checkout

Use Linux x86_64, Python 3.10 or newer, the standard-library SQLite implementation, and a kernel permitting the seccomp BPF filter. The candidate must pass all five denial probes: authority file access, workspace file access, networking, spawning another process and process inspection. The controller refuses qualification when this boundary is unavailable. No Python package installation, API keys, model downloads or paid services are required. Node.js is also needed for the repository's existing website tests; no npm packages are required.

Check out the exact qualified revision recorded in the results report. While this work is under review, the branch is `feat/continuity-economy-v0.2`; a moving branch name alone is not a reproducibility identity.

```sh
git clone https://github.com/MontrealAI/CONTINUITY.git
cd CONTINUITY
git checkout feat/continuity-economy-v0.2
git rev-parse HEAD
python3 -m continuity_economy --language en --help
python3 -m continuity_economy --language en experiment --out /tmp/continuity-economy-complete-001
python3 -m continuity_economy --language en verify-suite --in-dir /tmp/continuity-economy-complete-001
```

`experiment` executes the registered base comparison, separately registered successor and adversarial controls. It requires the successor registration to exist and never silently substitutes or omits it. Choose a new output directory outside the checkout every time. Existing attempts are refused rather than overwritten. Authority directories are siblings of candidate execution directories; the candidate receives only the public view through its restricted pipes.

## Separate commands

```sh
# Seven base controls, Harness procedure only.
python3 -m continuity_economy --language en demo --out /tmp/continuity-economy-demo-001

# Seven fixtures × conventional, Harness, no-purchase and explicit AI NOT RUN.
python3 -m continuity_economy --language en compare --out /tmp/continuity-economy-comparison-001
python3 -m continuity_economy --language en verify-suite --in-dir /tmp/continuity-economy-comparison-001

# Fresh successor with the same interfaces and permitted reusable materials.
python3 -m continuity_economy --language en successor --out /tmp/continuity-economy-successor-001

# Actual fault executions, retained evidence interventions and verifier mutations.
python3 -m continuity_economy --language en challenge --out /tmp/continuity-economy-challenges-001
python3 -m continuity_economy --language en verify-suite --in-dir /tmp/continuity-economy-challenges-001

# One registered case and one independently selected procedure.
python3 -m continuity_economy --language en run --fixture constructed-continuity --method conventional --out /tmp/continuity-economy-one-001

# Fresh verification of one run: copy its original reference pin from trusted custody.
python3 -m continuity_economy --language en verify --run /tmp/continuity-economy-one-001/run --authority /tmp/continuity-economy-one-001/authority --reference-sha256 ORIGINAL_REFERENCE_SHA256

python3 -m unittest discover -s tests -p 'test_economy*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

`ORIGINAL_REFERENCE_SHA256` is a placeholder for the independently retained digest, not a value to recompute from a possibly altered package. Omitting the pin leaves authority **NOT ESTABLISHED**. Suite indexes retain the exercise pins for replay under the trusted controller/host model; protect a separately copied index or its digest when moving evidence. A malicious host administrator is outside this model.

Exit code `0` means the declared test assertion matched, including a correctly observed negative outcome. It does not mean every customer obligation or trade succeeded. Exit `3` indicates a failed suite assertion or a nonfavorable individual fresh assessment; exit `2` indicates command/admission failure. Check `claims`, `assessment`, `per_obligation`, `failures` and `unresolved`, rather than treating an exit code as the business verdict. AI records say **NOT RUN**: no suitable already-authorized local model was available. The callable AI adapter permits later integration without embedding credentials or requiring a paid API; a unit stub tests plumbing only.

## The seven registered base cases

| Case | Purpose |
| --- | --- |
| `primary-recovery` | Restore the stale primary from protected event history and fulfill the final amended digital obligation. |
| `conventional-better` | Make the existing competent backup economically preferable to a constructed alternative. Both methods may select it. |
| `constructed-continuity` | Fail the initially selected backup, preserve its canceled agreement costs, construct an eligible split, lose an acceptance acknowledgment and restart the candidate. |
| `repair-after-rejection` | Interrupt a durable production export, retry the same identity, reject incorrect content and pay/reserve for a distinct correction. |
| `technical-no-trade` | Reject the modeled purchase while an explicitly authorized, separately funded technical control completes the digital product. |
| `no-deal` | Keep an 800-unit total alternative capacity below the 1,900-unit promise. No full arrangement exists in that modeled domain. |
| `uncertain-value` | Retain a buyer-value interval spanning acceptability; do not select a convenient value and call it consent. |

DL-100 requires 1,100 units at revision 2; DL-200 requires 800 at revision 1; DL-300 is canceled. The source history and exact bilingual materialized content are in each registered contract. Eligible fixed lots are 500 units or a final remainder. Splitting is an explicit original permission; it cannot be added after failure. The base logical deadline is tick 500, observation cutoff 800 and elapsed deadline 60,000 ms. Both logical and monotonic observation conditions apply. Ticks are modeled operations, not seconds; advancing to a capacity window is a recorded simulation-clock action. Actual process wall/CPU time is measured separately.

## Modeled participation and cost interpretation

All monetary fields are exact integer **SMU minor units**; 100 fictional minor units form one SMU. No exchange rate or real price is implied. Each provider has costs, outside profit, consent expiry, funds and a liability limit. The coordinator has operating cost and a participation threshold. The buyer has a value interval, outside utility, price limit and available funds. Policies are retained independently and cannot be rewritten by a candidate. A proposal is distinct from a separately recorded participant decision and a funded agreement.

For each provider, the offered minimum covers initial work, the full permitted one-correction financial allowance and the larger of minimum profit or outside profit. The coordinator fee covers current operating cost, its participation threshold and any unreimbursed canceled coordination cost. The buyer accepts only when the modeled value less total price meets the outside utility, the price limit holds and funding is available. For uncertain value `[L,U]`, a price `P` is definitely acceptable only if `L ≥ P + outside utility`, possibly acceptable if `U ≥ P + outside utility`, subject to the other constraints. The verifier reports the region; it does not invent willingness to pay.

Buyer escrow and provider working-fund holds cannot be counted twice. Incurred modeled production and correction costs flow to an explicit cost sink; transfers conserve the modeled ledger total. An unused correction hold is not an incurred cost. Financial provision for correction is distinct from guaranteed future physical capacity: each correction needs a new authorized capacity reservation. Rejection, cancellation and abandoned work remain in campaign accounting. Accrued partial acceptance prevents silent agreement cancellation: escrow and liabilities remain active; consented partial settlement is not implemented. A participant may consent to bounded failure exposure even when a failed arrangement produces a realized loss; report both observations.

## Fair comparison and transferable knowledge

The conventional method enumerates the complete bounded eligible assignment domain. The Harness method searches the same domain using capacity and nonnegative-price pruning. Both receive the same public contract, policies, service observations, funding information, capacity opportunities, tools, retries and request limits. Both may restore, use the ordinary backup or construct an eligible arrangement. The hidden retained acceptance reference is unavailable to both. Search exhaustion is distinct from proven infeasibility. Finite-domain enumeration is not a general proof or an AI performance result.

The no-purchase method executes no production or financial arrangement. AI performance is **NOT RUN**. One observation per registered cell and fixed method order cannot establish statistically reliable speed differences. Measured child/controller CPU, wall time, requests, restarts, storage and fresh-verification work are reported. The controller measurement stops before its final record/seal and Passport rendering; that overhead remains an explicit accounting gap. Preparation, integration, adaptation and verification labor are unknown when unmeasured. No method is called cheaper on incomplete cost accounting.

The successor must be authored after the first base execution and a versioned freeze of reusable implementation, interfaces, documentation and permitted knowledge. It may reuse the same algorithms and general schemas, with equivalent access for the conventional control. Completed products, receiver data, hidden answers and successor-specific executor fixes are excluded from its starting material. Record any later fix as adaptation, retaining the failed first attempt. One synthetic transfer does not establish general discovery, autonomy, a supplier network or commercial scalability.

## Evidence and limitations

Each run retains the contract and policies, original reference, protected execution seal, controller events, subprocess logs, actual SQLite databases, produced/inbox content, raw receipts, semantic acceptance, participant decisions and transfers. `RESULT.json`, `PASSPORT.en.md` and `PASSPORT.fr.md` derive from one structured assessment. The fresh verifier replays durable evidence; it does not trust those reports or the producer's PASS label. Test assertions, component verdicts, evidence stages and claim status stay separate.

The host, controller, synthetic source journal, clock and service custody remain trusted. Producer, receiver and verifier are separate implementations/processes under shared authorship, not third-party certification. Tests cover enumerated transition hooks and sampled faults, not every possible interleaving, hardware failure or operating system. See the threat model and requirements matrix for the exact boundary. Only Harness-owned disposable resources are closed; failed runs and partial files remain inspectable. No real customer, supplier, money or production system is contacted.
