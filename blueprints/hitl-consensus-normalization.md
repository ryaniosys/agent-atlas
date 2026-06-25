# HITL Consensus Normalization Blueprint

> In a human-in-the-loop consensus pipeline, **canonicalize before you compare**. Most "disagreements" are formatting, not content — normalize them away so the human sees only genuine conflicts.

## The Core Problem: Formatting Noise Drowns Signal

A common pattern for trustworthy output: run **N independent models** over the same input, treat agreement as auto-accept, and route **disagreements to a human** for review. It works — until you discover that the dominant source of "disagreement" is **formatting, not content**. The two models *read the same value* and merely render it differently:

| Both models are right, but… | Model A | Model B |
|------------------------------|---------|---------|
| number locale | `1'234.50` | `1234.5` |
| date format | `05.11.2026` | `2026-11-05` |
| field granularity | city `"99999 Springfield"` | city `"Springfield"` |
| embedded prefix | postal `"DE-99999"` | postal `"99999"` |
| code vs name | country `"Germany"` | country `"DE"` |
| repeated structure | a page-footer block captured **once** | …captured **twice** |

Route these raw to a human and you flood the queue with non-issues. Reviewers fatigue, lose trust, and miss the *real* errors hiding among the noise.

## The Fix: A Deterministic Layer Beneath the Model

Insert a **deterministic normalization layer** *below* the models, applied **before comparison/voting**:

```
N model outputs → normalize (canonicalize values, dedup, canonicalize keys) → vote → only genuine conflicts → human
```

- **Canonicalize values:** numbers, dates, locale formats, units, casing/whitespace, code-vs-name maps (country, currency), strip embedded prefixes.
- **Dedup repeated structures** before voting (e.g., a header/footer block captured on every page).
- **Canonicalize alignment keys** so you compare like with like (align line items by a stable id, address blocks by role, etc.).

Compare the **canonical** forms. Only disagreements that survive normalization — genuine content differences — reach the human.

### Normalize, don't suppress

Canonicalizing is **not** the same as silently picking one value. Picking one hides real errors; normalizing only collapses values that are *provably equivalent*. Keep an audit trail (record the raw candidates + why they were considered equal) so a human can verify the equivalence.

## It Converges: Peel Off One Noise Class at a Time

Treat normalization as an iterative loop, not a one-shot:

1. Run the pipeline; inspect the cells still flagged as disagreements.
2. Identify the **dominant remaining formatting class** (e.g., "country code vs name").
3. Add one normalizer for it.
4. Repeat.

Each pass removes a class of noise. It **converges**: after a few passes, what's left flagged is genuine signal — real misreads, true ambiguity, actual conflicts. (In one run this took a number → date → locale-split → code/name → dedup sequence before only real disagreements remained.)

## Gate Review Granularity: Carry All, Review the Few

Two independent decisions — don't conflate them:

- **What to carry into the output:** *everything* the models produce (don't drop fields — a curated subset silently loses data).
- **What to put in front of a human:** only **key** fields (the ones that are scored / matter downstream), and only on a **genuine shared conflict** — both sources produced a value *and* they differ.

Explicitly **do not** force review on:

- **`[value, None]` "enumeration" mismatches** (one source emitted the item, the other didn't). That's a *coverage* question about whether the item should exist — wrong granularity for a per-field review prompt, and it floods the queue.
- **Low-value fields** (incidental ids, free-text notes, contact channels) — carry them as provenance, don't gate the human on them.

## Anti-patterns

- ❌ Routing **raw** (un-normalized) disagreements to humans → noise, fatigue, lost trust.
- ❌ **Suppressing** disagreements by silently choosing one → hides real errors.
- ❌ Reviewing **every** field equally → reviewer fatigue; the important conflicts get buried.
- ❌ Treating a **missing-in-one-source** field as a per-field conflict → wrong granularity.

## Checklist

- [ ] Normalize before compare/vote: numbers, dates, locale formats, casing, units, code↔name maps.
- [ ] Dedup repeated structures before voting; align by stable keys, not position.
- [ ] Keep an audit trail of raw candidates + the canonical form (normalize ≠ suppress).
- [ ] Carry *all* fields into the output; gate human review to key fields on genuine conflicts only.
- [ ] Iterate: inspect residual disagreements, add the next normalizer, until only signal remains.

## Related

- [eval-harness-fidelity.md](eval-harness-fidelity.md) — make the harness faithful *first*, or you'll normalize away artifacts that were never real.
- [agent-reliability.md](agent-reliability.md) — deterministic steps beat stochastic ones wherever judgment isn't required.
