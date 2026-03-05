# Hardening AI-Orchestrated Workflows

> **Status:** Pattern validated in production (Mar 2026). Applicable to any multi-step workflow where an AI agent executes business-critical operations.
>
> **Last updated:** 2026-03-05

## Problem

AI agents orchestrating multi-step workflows (data pipelines, deployments, document generation) tend to **rediscover the same failure modes** every session. Without guard clauses, each session relies on the operator remembering what went wrong last time. This creates:

- **Silent failures** — missing config, incomplete data, stale state
- **Irreversible mistakes** — mutations applied before validation (e.g., an API that snapshots data at creation time; can't fix after)
- **Double-application bugs** — idempotency violations when retrying or resuming
- **AI improvisation in customer-facing output** — non-deterministic email text, wrong formatting

## Root Cause

Workflow instructions (SKILL.md, runbooks) describe *what* to do but not *what to check first*. The agent fills gaps with improvisation, which works until it doesn't.

## The Pattern: Lessons → Functions → Gates

### Step 1: Capture Lessons Systematically

After each workflow execution, record failures as structured lessons:

| # | What Went Wrong | Root Cause | Prevention |
|---|----------------|------------|------------|
| 1 | Addresses incomplete on document | API snapshots at creation | Validate BEFORE creation |
| 2 | PDF crashed on em-dash | Font renderer ASCII-only | Sanitize text input |
| 3 | Duplicate records created | No check for existing drafts | Preflight query |

**Key insight:** Most workflow failures fall into 4 categories:
1. **Missing prerequisite** — config field, API credential, upstream data
2. **Stale state** — cached data, previous session artifacts, wrong branch
3. **Irreversible mutation** — API call that can't be undone (snapshot, send, publish)
4. **Format/encoding** — character sets, date formats, currency precision

### Step 2: Extract Deterministic Helper Functions

Convert each lesson into a **pure or near-pure function** with a clear contract:

```
lesson → function(inputs) → deterministic output
```

Good helper functions are:
- **Preflight checks** — validate all prerequisites before any mutation. Return `list[str]` of warnings (empty = all clear).
- **Sanitizers** — transform data into safe format (encoding, precision, character replacement). Pure functions, no I/O.
- **Calculators** — derive values from config + inputs (due dates, rates, totals). Pure functions with explicit error handling.
- **Lookups** — resolve known-good data from config files (addresses, mappings). Deterministic given the same config.

**Anti-patterns to avoid:**
- Functions that silently swallow errors (return `False` with no logging)
- Catch-all `except Exception` — use specific exception types
- Functions typed as `Any` when a concrete type exists — use `TYPE_CHECKING` imports if needed

### Step 3: Add Approval Gates

Structure the workflow with explicit **human-in-the-loop gates** before irreversible operations:

```
Phase 1: Gather + Validate
  → run_preflight() — check all prerequisites
  → show preview to user
  ↓ GATE 1: User approves data (or requests changes)

Phase 2: Transform + Review
  → sanitize, calculate, format
  → show deliverables to user
  ↓ GATE 2: User approves deliverables

Phase 3: Mutate + Confirm
  → create/update external resources
  → show results to user
  ↓ GATE 3: User confirms state transition (draft→sent, pending→active)
```

**Gate rules:**
- Never combine validation and mutation in the same step
- After any mutation, re-fetch fresh state (don't trust local cache)
- Gates are blocking — the agent must not proceed without explicit approval

### Step 4: Validate with Types

Use your language's type system to catch config errors at load time:

```python
# Bad: silent fallthrough on typos
payment_rule: str | None = None

# Good: Pydantic catches invalid values before execution
payment_rule: Literal["end_of_month", "net_30", "net_10"] | None = None
```

For functions that handle config-driven branching, raise on unknown values instead of defaulting:

```python
# Bad: unknown rule silently becomes the default
if rule == "net_30":
    return base_date + timedelta(days=30)
return base_date + timedelta(days=10)  # catch-all

# Good: unknown rule fails fast
if rule is None or rule == "net_10":
    return base_date + timedelta(days=10)
raise ValueError(f"Unknown rule: {rule!r}")
```

### Step 5: Hardcode Customer-Facing Output

Templates for emails, reports, and notifications should be **literal strings in the skill definition**, not AI-generated:

```markdown
## Email Template
Subject: {document_type} {period} – {company}
Body: Dear {recipient}, please find attached...
```

**Why:** AI-generated customer-facing text varies between sessions. A hardcoded template ensures consistency and allows the business owner to review once, not every time.

## Decision Matrix: When to Apply This Pattern

| Signal | Action |
|--------|--------|
| Same failure occurred twice | Extract to helper function |
| Workflow has irreversible API calls | Add approval gate before mutation |
| Config field accepts free-form strings | Constrain with Literal/enum type |
| Agent improvises customer-facing text | Hardcode template in SKILL.md |
| Session starts by re-discovering prerequisites | Add preflight check |

## Testing Strategy

Helper functions extracted by this pattern are inherently testable:

- **Pure functions** (sanitizers, calculators) — unit test with edge cases, no mocks needed
- **Lookup functions** — test with fixture config files (exact match, case-insensitive, missing)
- **Preflight functions** — mock external API calls, test all warning paths + happy path
- **Approval gates** — not testable in isolation (they're orchestration), but the functions they call are

## Checklist: Applying to a New Workflow

- [ ] Run the workflow manually 2-3 times, recording all failures
- [ ] Categorize failures (missing prerequisite / stale state / irreversible mutation / format)
- [ ] Extract one helper function per failure category
- [ ] Add preflight check that runs before any mutation
- [ ] Add approval gates before irreversible operations (minimum: 1 before mutations, 1 before state transitions)
- [ ] Constrain config fields with Literal/enum types
- [ ] Hardcode customer-facing templates
- [ ] Write tests for all helper functions
- [ ] Update SKILL.md with guard clauses referencing the functions

## Real-World Results

Applying this pattern to a multi-step document generation workflow with external API integrations:

- **4 helper functions** extracted (sanitizer, calculator, lookup, preflight)
- **3 approval gates** (after preview, after deliverables, before state transition)
- **Pydantic Literal types** on all config-driven branching fields
- **Hardcoded templates** for all customer-facing output
- **28 new tests** covering all helper functions

Result: workflow went from "requires operator memory of past failures" to "deterministic execution with explicit guard clauses."

## Cross-References

- [Best Practices](best-practices.md) — convention 4 (Skills) covers SKILL.md structure
- [Agent Reliability](agent-reliability.md) — complementary pattern for error handling and retries
- [Secrets Management](secrets-management.md) — preflight checks can verify credential availability
