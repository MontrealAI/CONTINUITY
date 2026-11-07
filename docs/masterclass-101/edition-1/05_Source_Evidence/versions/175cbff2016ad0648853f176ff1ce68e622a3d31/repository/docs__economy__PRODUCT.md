# CONTINUITY Ω — Digital label-job product and acceptance specification

[Français](PRODUCT.fr.md) · [Architecture](ARCHITECTURE.md) · [Threat model](THREAT_MODEL.md)

## The product being promised

The obligation is a **digital job package containing literal, substantive label content for specified units**. A separate local receiving process actually reads its bytes and imports accepted content into durable SQLite rows. Quantity metadata, a specification digest, a completion status or a self-issued receipt cannot satisfy this contract alone.

This is a new digital obligation. It does not fulfill the historical physical-label promise. Its acceptance establishes exact semantic content and unit coverage in the supported format. It does not establish visual layout, rendering, fonts, barcode readability, print readiness, print quality, adhesion, packaging performance, physical goods or external customer acceptance.

The original acceptance specification is retained outside candidate control. Every active obligation fixes its recipient, revision, quantity, deadline and materialized specification. Amendments are replayed from the retained source journal before the contract freezes; canceled obligations remain canceled. Zero units may be lost through recovery.

## Supported version and content

The product and specification format identifier is `continuity-economy/label-job/v1`. Files are bounded UTF-8 JSON, at most 1 MiB each. Unsupported schema versions, fields or feature requests are refused. JSON objects have unique keys; quantities and ordinals are exact integers, never strings or Booleans. Non-finite values, floating-point values, malformed structure and invalid ranges are refused.

Both direct service constructors and their command-line entry points admit the complete neutral `continuity-economy/contract/v1` schema before creating any database or output directory. This includes source replay, identifiers, providers, windows, bounds and prohibited top-level fields. Their retained contract is copied against later caller mutation. The supported complete exercise has at most 8 obligations and 8 active fixed lots; the full declaration is in [the contract schema](../../continuity_economy/schema.py). Shared admission is not shared content acceptance.

The materialized specification has exactly these fields:

| Field | Meaning |
| --- | --- |
| `format` | Supported format identifier |
| `sku` | Exact product reference |
| `name_en`, `name_fr` | Exact English and French product names |
| `instructions_en`, `instructions_fr` | Exact English and French substantive instructions |
| `lot` | Exact material lot identity |
| `serial_prefix` | Prefix for unique, ordinal-bound serials |

Literal text is bounded to 160 characters and excludes control characters. The root contract imposes its stricter identifier constraints as well. No translation, abbreviation, normalization or substitution is allowed during production: both retained language strings must match literally. Each obligation has at most 2,000 units.

A product envelope contains exactly:

```text
schema, run_id, contract_id, contract_sha256,
obligation_id, revision, recipient,
production_id, arrangement_id, provider_id, delivery_id,
capacity_key, lot_id, attempt, first_unit, last_unit, supersedes, labels
```

The `labels` array has one object for each ordinal in the declared inclusive range, in order. Every object contains exactly:

```text
ordinal, serial, sku, name_en, name_fr, instructions_en, instructions_fr, lot
```

Each `serial` is the retained `serial_prefix` followed by its ordinal padded to six digits. Repeated ordinals, repeated serials, gaps, reordered units or mismatched literal fields fail inspection. A packet for 100 units must contain 100 substantive label objects; a lone `quantity:100` declaration is insufficient.

## Lots and correction identities

If `allow_split` is true, the frozen `lot_size` partitions each active obligation’s ordinal range. The final lot may be smaller. If splitting is false, the whole obligation is one lot even when its quantity exceeds `lot_size`. Exact ranges are derived from the retained contract and are not candidate-selected flexibility.

For lot `ORDER.L001` in agreement `proposal-001`:

| Stage | First attempt | Supported correction |
| --- | --- | --- |
| Production and capacity key | `proposal-001.ORDER.L001.A1` | `proposal-001.ORDER.L001.A2` |
| Delivery | `proposal-001.ORDER.L001.A1.D` | `proposal-001.ORDER.L001.A2.D` |
| `supersedes` | `null` | `proposal-001.ORDER.L001.A1.D` |

The correction must refer to an existing, durably **rejected** first delivery of the same agreement and lot. An initial `A2`, correction of an accepted delivery, changed range or cross-agreement predecessor is refused. The maximum is two attempts when the contract allows correction. Repair cannot overwrite a previous file, receipt, decision or accepted row.

A new attempt requires its own capacity reservation and production charge. A retry of the same stable request reconciles the earlier attempt without charging or generating a second copy. A different request under an existing key is a conflict, not an authorized amendment.

A different agreement can begin a new `A1` only after the broker establishes durable cancellation of the old agreement and no prior accepted work, and the new agreement is separately accepted and funded. The fresh verifier rechecks those conditions and all sunk costs. The receiver checks that new A1’s content without confusing it with A2; it does not itself decide economic authorization.

If some content is already accepted and remaining work fails, the agreement stays `ACTIVE`. The broker refuses cancellation after any actual accepted receiver decision, including an acceptance whose timing or acknowledgment remains uncertain. This version has no partial-settlement operation: remaining escrow, liabilities and the accepted subset remain durable and unresolved. This is neither full delivery nor a completed payment. Resolving that state requires an explicitly authorized settlement procedure; silently discarding acceptance or releasing its funding is not supported.

## Materialization, receipt and acceptance

The producer persists the complete generated payload in its database before export. It exports the same bytes through a temporary file, file synchronization, atomic creation and directory synchronization. A kill during export leaves the durable payload and any partial file for inspection. Restart reuses that payload; an already existing conflicting artifact is refused.

The controller authorizes transfer, checks the exported bytes against the producer record and copies them to the receiver inbox. The receiver’s `receive` operation retains the actual bytes and receipt metadata without declaring semantic acceptance. Corrupt or truncated bytes are still evidence of a received attempt and may later be rejected; they are not discarded.

The separate `inspect` operation:

1. Validates the bounded envelope and exact run, contract, obligation, revision, recipient, lot, attempt and capacity-key binding.
2. Checks that the retained obligation is active, its source evidence is declared complete and its range matches the frozen lot.
3. Independently checks every literal label field, ordinal and serial against the retained specification.
4. Verifies the permitted correction predecessor and excludes units already accepted through any other delivery.
5. Checks logical timing, records the decision and transactionally imports the actual literal units.
6. Records a separate durable post-commit monotonic observation. Both the logical deadline and the elapsed-time deadline must be met for timely acceptance.

The receiver does not import the producer’s generation function. The fresh verifier independently implements its own semantic checks and reconciles the receiver’s imported rows against actual product bytes. All these implementations share authorship and host trust; this is not third-party certification.

## Durable records and service interface

The producer keeps `productions`, request `attempts`, materialization `observations` and `events`. The receiver keeps raw `receipts`, immutable `decisions`, post-commit `observations`, literal `imported_units` and `events`. Metadata binds reopening a database to the same retained contract.

| Process | Start command | Operations |
| --- | --- | --- |
| Producer | `python3 -m continuity_economy.producer --db DB --artifacts PRODUCTS --contract CONTRACT` | `produce`, `status`, `snapshot`, `checkpoint` |
| Receiver | `python3 -m continuity_economy.receiver --db DB --inbox INBOX --contract CONTRACT` | `receive`, `inspect`, `status`, `snapshot`, `checkpoint` |

These are trusted internal process interfaces. Operators normally use the main `python3 -m continuity_economy` commands. Requests use `{"id":"request-1","op":"inspect","args":{"delivery_id":"…","now_tick":1},"hooks":[]}`. Responses preserve the request identity and return either structured results or stable error codes with English/French explanations. Service help displays both languages.

Snapshot responses contain bounded metadata and counts, not all label bytes or rows. Final evidence contains the actual standalone databases and product files, so a fresh verifier inspects substantive content without trusting the snapshot summary.

## Timing and failure meaning

Contract deadlines are inclusive. The acceptance observation must occur no later than the obligation’s logical deadline and the retained elapsed-time limit. Producer timestamps and receipt timestamps cannot stand in for post-commit acceptance timing.

A crash after decision commit but before its observation leaves timing unestablished until a later observation. That observation can establish lateness; it cannot invent an earlier successful time. A lost acknowledgment after a durable timely observation is resolved through the existing delivery identity, preserving the original decision and time. Replays never insert a second accepted unit.

Rejected requested units, actually materialized units, receipt attempts and accepted units are separate measures. A truncated packet can have a known requested range but zero independently validated substantive units. Missing evidence is not zero work and is not favorable proof.

The [product tests](../../tests/test_economy_product.py) exercise substantive 1,900-unit import, wrong content with correct metadata, corruption, truncation, duplicate units, stale revisions, wrong recipients, cancellation, explicit repair, concurrent duplicates and real process interruption. They also mutate the generation output to show that independent acceptance detects the changed content. These are bounded executable controls, not a universal delivery guarantee.
