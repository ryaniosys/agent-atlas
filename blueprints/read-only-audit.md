# Read-Only Audit of Side-Effecting Systems

> How to verify a resolver, router, or classifier against real production data — without mutating anything, and without lying to yourself.

## The Problem

You have a component that decides where things go: a router that files documents into collections, a classifier that assigns records to buckets, a resolver that maps inputs to destinations. Over time its config evolves, so some already-processed items are now in the "wrong" place. You want to **find the drift** and **verify a fix** against live data.

Two traps make this deceptively hard:

1. **The logic has side effects.** Running it for real creates collections, writes index state, sends requests. You can't just "run it and see."
2. **Re-deriving the logic diverges from the real path.** If you reimplement the decision in your audit script, you silently omit the layers the real code has — priority overrides, scoped rules, fallbacks. Your audit then reports drift that isn't real (false positives) and misses drift that is (false negatives).

A third trap turns a careful audit into a confident lie — covered under [Always paginate](#gotcha-always-paginate-list-apis).

---

## Technique 1: The No-Create Wrapper

Run the **real** decision code, but wrap its effectful client so every mutating call becomes a read.

```python
class ReadOnlyClient:
    def __init__(self, real):
        self._real = real
    # find-or-create -> find only. Returns existing id, or None if it doesn't exist.
    def find_or_create(self, name, **_):
        return self._real.find_by_name(name)      # never creates
    def find_by_name(self, name):
        return self._real.find_by_name(name)
    def create(self, *a, **k):
        raise RuntimeError("read-only audit: create blocked")
    def move(self, *a, **k):
        raise RuntimeError("read-only audit: move blocked")
```

Then call the **actual** resolver with this wrapper, and point any persistence it does at a throwaway path:

```python
decision = real_resolver(record, config, ReadOnlyClient(client), persist_path="/tmp/throwaway")
```

Because the destinations you're auditing already exist, `find-or-create` resolves to the real id with zero mutation. A `None` return means "this decision would need to CREATE something" — itself a useful signal (flag it, don't act on it).

**Why this beats re-deriving:** you exercise the real priority order, the real scoped overrides, the real fallbacks. What the audit reports is exactly what production would do.

---

## Technique 2: Reconcile Recorded State vs. Current Decision

Don't ask "where should everything go?" from scratch. Compare what the system **recorded** (its ledger / index / manifest — the source of truth for where each item currently lives) against what the current logic **would decide** now:

```
for each item in ledger:
    recorded   = ledger[item].destination
    intended   = read_only_resolve(item)        # real logic, no side effects
    if intended is not None and intended != recorded:
        drift.append((item, recorded, intended))
```

Present `drift` for human review **before** mutating anything. Reconciliation scales to "what changed since the config evolved" and naturally ignores items that are already correct.

---

## Gotcha: Always Paginate List APIs

The single most dangerous bug in an audit is a **silently truncated list**. List endpoints commonly default to a page size (often 100) with no error when there are more. An audit that reads one page will:

- report a collection of 108 items as "100, all clean,"
- and **miss the 8 items past the cap** — including any misfiled ones.

A truncated audit is **worse than no audit**: it produces false confidence. Always paginate to exhaustion, or assert the returned count equals an independently known total.

```python
def list_all(client, container):
    out, offset = [], 0
    while True:
        page = client.list(container, limit=100, offset=offset)
        out += page
        if len(page) < 100:
            return out
        offset += 100
```

The same cap bites the production code, not just audits: a "find the existing parent / dedup key" search that reads only the first page can fail to find an item that exists on page 2, and create a duplicate. Fix both.

---

## When To Use

- Auditing a router/classifier/resolver after its config or rules changed.
- Verifying a fix against real data before a bulk migration.
- Any "is production actually in the state we think?" question where re-running the real path would mutate state.

## Anti-Patterns

- **Reimplementing the decision logic in the audit.** It drifts from the real path; you end up auditing your reimplementation, not the system. Wrap the real code instead.
- **Trusting a single-page list.** See above. Paginate or assert the count.
- **Auto-fixing from the audit.** Separate detection from mutation. The audit produces a reviewed list; a deliberate second step acts on it (with backups, and ideally idempotent so re-runs are safe — see [`write-ahead-idempotency.md`](write-ahead-idempotency.md)).
- **Pinning items to where they already are without a rule.** A manual per-item override is a fine escape hatch, but if the underlying rule still disagrees, a later re-process can move it back. Prefer fixing the rule; use pins as the safety net, not the strategy.

## Related

- [`repo-to-runtime-sync.md`](repo-to-runtime-sync.md) — deploying the fixed logic to the running system.
- [`write-ahead-idempotency.md`](write-ahead-idempotency.md) — making the mutation step safe to re-run.
- [`tdd-wave-pattern.md`](tdd-wave-pattern.md) — building the fix test-first before deploying it.
