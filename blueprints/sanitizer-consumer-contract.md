# Absent ≠ Excluded: Sanitizer–Consumer Semantic Contracts

> **Status:** Production-tested — caught (and later fixed) a live rendering regression in a static-site CMS build pipeline.
>
> **Last updated:** 2026-07-19

## The Problem

When you sanitize data at a serialization chokepoint — stripping secrets, drafts, or hidden content before it ships — it is tempting to **delete** the offending field. But deletion changes the *shape* of the output, and a downstream consumer may interpret "field absent" differently from "field present but flagged." If a consumer falls back to a default when a field is absent, deleting a *hidden* object can invert its meaning: **hide** becomes **show-the-default**.

### Concrete failure

A content system lets authors hide a page section by setting a flag on its metadata object:

```json
{ "callToAction": { "visible": false, "title": "…", "body": "…" } }
```

The renderer hides the section with a presence-tolerant guard:

```js
// renders UNLESS explicitly visible:false
{ data?.callToAction?.visible !== false && <CallToAction … /> }
```

A build-time sanitizer is then added to keep hidden content out of the public output. It **deletes** any `{ visible: false }` object:

```js
if (isHidden(value)) continue; // ← drops the key entirely
```

Now `data.callToAction` is `undefined`. The guard reads `undefined !== false` → **true**, and the component renders its **hardcoded fallback** copy. The section the author deliberately hid is suddenly visible — with default text. The sanitizer was "correct" in isolation (no hidden payload ships) yet broke the consumer's invariant, and it shipped to production.

## The Pattern: Tombstone, Don't Delete

Preserve the shape the consumer keys on; strip only the payload.

- **Object property** guarded by `x?.flag !== false` → replace with a **flag-only tombstone** `{ flag: false }`. The guard still evaluates to "exclude," and no payload ships.
- **Array element** rendered by `.map()` → **drop it entirely**. A hidden list item must vanish; a tombstone would render as an empty row.

```
Two consumer patterns → opposite output shapes:

  list (iterated):   [ {flag:false, …}, {…} ]  → DROP element  → [ {…} ]
  single-object      { cta: {flag:false, …} }  → TOMBSTONE     → { cta: {flag:false} }
  (presence guard):                              (NOT delete → undefined → fallback)
```

The rule: **a sanitizer must emit whatever shape each consumer's guard expects for "excluded"** — which is not always "absent."

## Guard It With a Negative CI Assertion

A "the output shipped" test is not enough. Presence assertions catch neither inverted meaning nor leaked payload. Assert on the **actual built output**, at two layers:

1. **Leak assertion (data layer).** Walk every shipped file; fail if any excluded object still carries payload beyond its flag, or any draft/non-published item is present at all. Allow a bare tombstone (`{ flag: false }` with no other keys); fail on `{ flag: false, …payload }`.
2. **Regression assertion (render layer).** Build the page and assert the rendered output *shows what should be visible* and *does not contain* the fallback or stripped copy of excluded sections.

The render-layer assertion is the one that would have caught the failure above: the sanitizer's own unit tests were green, but the **page** was wrong. Test the outcome the user sees, not just the intermediate artifact.

## When This Applies

- Any transform that strips secrets, drafts, PII, or feature-flagged content before publishing.
- Anywhere a consumer distinguishes "field absent" from "field present but false/empty": nullable columns, optional config, feature flags, i18n fallbacks, selective field projection in an API.
- Multi-stage pipelines where producer and consumer live in different layers and can drift apart over time.

## Checklist

- [ ] For each field the sanitizer removes, ask: *does any consumer branch on its absence?*
- [ ] Prefer tombstoning (keep the discriminator, drop the payload) over deletion when a consumer guards on presence.
- [ ] Drop, don't tombstone, for collection elements rendered by iteration.
- [ ] Add a negative CI assertion on the built output — both a leak check and a render check.
- [ ] Unit-test the sanitizer's *excluded* shape explicitly (tombstone vs. drop), not merely "payload gone."
- [ ] When the sanitizer and the consumer are owned by different layers, write down the shape contract where both can see it.

## Related

- [`write-ahead-idempotency.md`](write-ahead-idempotency.md) — another build/pipeline integrity pattern where a naive implementation is subtly unsafe.
- [`enforcement-hooks.md`](enforcement-hooks.md) — CI-as-guardrail philosophy for turning a one-time fix into a standing invariant.
