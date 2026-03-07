# Decision Log Learning Loop

A pattern for agent skills that make recurring decisions on behalf of users. The agent logs each decision, accumulates patterns, and proposes defaults in future sessions.

## Problem

Agent skills that triage, categorize, or route items (emails, tabs, tickets, files) start from zero context each session. The user re-teaches the same preferences every time.

## Solution

Log user decisions in a structured format. After N sessions (typically 3), the agent reads prior decisions and proposes defaults based on accumulated patterns.

## Architecture

```
Session 1-3: Pure user input → log decisions
Session 4+:  Read log → pattern match → propose defaults → user confirms/overrides → log decisions
```

## Decision Log Format

Append-only markdown file with dated sections:

```markdown
## YYYY-MM-DD — N items processed

| Pattern | Item | Decision | Target |
|---------|------|----------|--------|
| domain.com/* | Page Title | action | destination |
```

- **Pattern**: URL pattern, sender domain, file type, or similar grouping key
- **Item**: Specific instance (title, subject, filename)
- **Decision**: What the user chose (close, distribute, archive, keep)
- **Target**: Where it went (repo, Linear label, folder, etc.)

## Pattern Matching Rules

Before presenting options, read the log and apply:

1. **Frequency match**: If pattern X led to decision Y in 3+ sessions, suggest Y as default
2. **Recency bias**: Recent decisions (last 5 sessions) weighted higher than older ones
3. **Domain reputation**: Track which patterns produce items that get kept vs. discarded
4. **Always show basis**: "Based on N prior sessions, suggesting X (chosen M/N times)"

## Bootstrapping

- Sessions 1-3: No suggestions. Pure user input builds the initial dataset.
- Session 4+: Propose defaults. User always has final say.
- Show confidence: "high" (>80% consistency), "medium" (50-80%), "low" (<50%)

## Key Principles

1. **User always decides** — suggestions are never auto-applied
2. **Transparency** — always show why a suggestion was made
3. **Append-only** — never edit or delete prior decisions
4. **Privacy-aware** — log patterns and titles only, never full content
5. **Graceful degradation** — works fine without a log (just no suggestions)

## Applicable Skills

Any skill that processes a stream of items with user-guided decisions:
- Email triage and routing
- Browser tab management
- File organization and classification
- Ticket routing and prioritization
- Content curation
- Incoming inspection disposition (accept, rework, reject, quarantine)
- Production order scheduling and machine assignment
- Non-conformance categorization and corrective action routing

## Manufacturing Examples

**Incoming Quality Inspection:** An agent inspects purchase order receipts against specs. Each lot gets a disposition decision (accept / rework / reject / quarantine). After 3+ sessions, the agent learns that supplier X's material Y is consistently accepted and proposes auto-accept as a default, while supplier Z's shipments frequently need rework — flagging them for closer inspection.

**Production Scheduling:** An agent assigns work orders to machines or lines. The operator repeatedly moves high-priority orders to Line A and batches small orders on Line B. Over time, the agent proposes routing rules: "Orders >500 units → Line A, orders <100 units → batch on Line B."

**Non-Conformance Routing:** When defects are logged, the agent asks the quality engineer how to categorize and route each one (root cause category, corrective action owner). After accumulating decisions, it suggests defaults: "Dimensional issues → machining team, surface defects → finishing team."
