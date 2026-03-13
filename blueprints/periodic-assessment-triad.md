# Periodic Assessment Triad

A pattern for agent-assisted continuous improvement using three complementary periodic assessments: structure, capability, and culture. Each assessment has its own cadence, audience, and output, but they cross-feed to create a complete picture of operational health.

## Problem

Operations track quantitative metrics (throughput, yield, utilization, revenue) but rarely track the qualitative dimensions that determine long-term health. When they do, it's ad-hoc: a quarterly management review, an auditor's checklist, or a crisis-driven root cause analysis. The assessments don't connect, so structural problems get diagnosed as people problems, cultural erosion gets missed until it causes a safety incident or quality escape, and individual development lacks organizational context.

This applies equally to a factory floor and a software team. The pattern is domain-agnostic.

## Solution

Three periodic assessment agents, each focused on a different operational lens:

| Assessment | Lens | Cadence | Audience | Core Question |
|-----------|------|---------|----------|---------------|
| **Structure Snapshot** | Organizational & resource design | Quarterly | Management | Do we have the right roles, equipment, and capacity? |
| **Capability Review** | Per-unit development | Monthly | Per-unit owner (+ supervisor gate) | How is each unit performing and developing? |
| **Culture Snapshot** | Collective behavior & values | Quarterly | Plant manager / founder | Are our stated principles showing up in daily operations? |

"Unit" is deliberately generic: a person, a work cell, a machine, a team, a production line. The pattern works at any granularity.

The triad works because each lens reveals what the others miss:
- Structure tells you **what** the operation looks like on paper
- Capability tells you **what each unit can actually do**
- Culture tells you **how work actually happens** when nobody's auditing

## Architecture

```
            ┌────────────────────────────┐
            │     Observation Sources    │
            │  (logs, reports, records)  │
            └──────────────┬─────────────┘
                           │
            ┌──────────────▼─────────────┐
            │    Unit Observation Logs   │
            │  (structured per-unit data)│
            └──┬───────────┬───────────┬─┘
               │           │           │
      ┌────────▼───┐ ┌─────▼─────┐ ┌───▼───────┐
      │ Structure  │ │ Capability│ │  Culture  │
      │ Snapshot   │ │ Review    │ │  Snapshot │
      └──────┬─────┘ └─────┬─────┘ └──────┬────┘
             │             │              │
             └─────────────┼──────────────┘
                           │
            ┌──────────────▼──────────────┐
            │     Cross-Feed Outputs      │
            │   (recommendations flow     │
            │    between assessments)     │
            └─────────────────────────────┘
```

### Shared Data Layer

All three assessments read from the same observation source: **unit observation logs** populated from operational data. This is critical. The assessments don't rely on surveys, self-reports, or separate data collection. They analyze the same data through different lenses.

**Manufacturing examples:**
- Shift handover logs (what happened, what was escalated, what was improvised)
- Quality reports (defects, root causes, corrective actions)
- Maintenance records (planned vs. unplanned, workarounds applied)
- Production meetings (decisions made, priorities set, blockers raised)

**Software/org examples:**
- Standup notes, planning sessions, retrospectives
- Incident reports, post-mortems, code reviews
- Project status updates, architecture decisions

The key insight: **existing operational records already contain the signals**. The agent extracts structured observations from unstructured sources, not the other way around.

### Cross-Feed Pattern

Each assessment produces recommendations that feed into the others:

| From | To | What Flows |
|------|----|-----------|
| Structure → Capability | Resource gaps inform where to cross-train or invest |
| Structure → Culture | Layout or team changes trigger culture impact assessment |
| Capability → Culture | "Cell 3 consistently self-corrects without supervisor intervention" is a culture signal |
| Culture → Capability | "Quality ownership is weak on night shift" becomes a development focus |
| Culture → Structure | Cultural gaps may indicate missing roles or wrong resource allocation |
| Capability → Structure | Growth trajectories inform hiring, investment, or rebalancing |

## Implementation Pattern

### 1. Observation Collection (Continuous)

Agent processes operational records and extracts per-unit observations into structured logs. Each entry is tagged with source and date.

```markdown
### YYYY-MM-DD [Source Type]

**Observations:**
- What happened, with specific evidence

**Flags:**
- GREEN: Pattern worth reinforcing or standardizing
- YELLOW: Pattern worth monitoring (not yet a problem)
- RED: Pattern requiring intervention before next review cycle
```

**Manufacturing example:**
```markdown
### 2026-03-10 [Shift Handover - Line 2]

**Observations:**
- Operator detected label misalignment 20 units before the quality gate caught it.
  Stopped the line, recalibrated, resumed in 8 minutes.
- Maintenance workaround on conveyor belt tensioner is now 3 weeks old.
  Formal repair keeps getting bumped.

**Flags:**
- GREEN: Proactive quality catch by operator — faster than automated detection
- YELLOW: Workaround longevity on tensioner — technical debt accumulating
```

### 2. Structure Snapshot (Quarterly)

Reads: resource definitions, current roster/equipment list, previous snapshot, capacity plans.
Outputs: resource tables, layout diagram, strengths/gaps/risks, investment priorities, delta.

Key sections:
- Resource roster (people, equipment, capacity, utilization)
- Organizational or layout structure (visual)
- Strengths, gaps, and risks (numbered by severity)
- Investment or hiring priorities
- "What to Watch" checklist for next quarter

### 3. Capability Review (Monthly)

Reads: unit observation logs (last 4 weeks), skill matrices or equipment specs, previous reviews.
Outputs: per-unit development report.

Key design decisions:
- **Minimum observation threshold** — skip if insufficient data for meaningful assessment
- **Supervisor review gate** — reviews for junior units go through supervisor before delivery
- **Trend over snapshot** — always compare against previous review, not just absolute state
- **Actionable recommendations** — each review ends with 1-3 specific development actions

### 4. Culture Snapshot (Quarterly)

Reads: stated values/principles, unit observation logs, dynamics patterns, previous snapshot.
Outputs: values scorecard, propagation map, health indicators, recommendations.

Key sections:
- **Values Alignment Scorecard:** Each principle scored (Strong / Moderate / Weak / Absent) with trend direction
- **Propagation Map:** How far each principle has spread across organizational levels or shifts
- **Health Indicators:** Qualitative signals that reveal how work actually happens

Typical health indicators (adapt to domain):

| Indicator | Manufacturing | Software/Org |
|-----------|--------------|-------------|
| Escalation quality | Do operators flag issues early or hide them? | Do engineers raise blockers proactively? |
| Knowledge flow | Is expertise shared across shifts or siloed? | Is knowledge bidirectional or top-down? |
| Decision speed | How fast are production issues resolved? | How long do disagreements take to resolve? |
| Failure response | Is root cause analysis blame-free? | Are post-mortems learning or blame? |
| Autonomy gradient | Who improvises solutions vs. waits for supervisor? | Who self-selects work vs. waits for direction? |

## Design Principles

### 1. Same Data, Different Lenses

Never create separate data collection for each assessment. One observation source, three analytical perspectives. This keeps the system lightweight and avoids survey fatigue or audit overhead.

### 2. Evidence Over Vibes

Every score, rating, and recommendation must cite specific dates and examples. "Line 2 has good quality culture" is useless. "Operator on Line 2 caught label misalignment 20 units before the quality gate on March 10 and self-corrected in 8 minutes" is evidence.

### 3. Honest, Not Diplomatic

These are internal reflection tools, not audit reports for external stakeholders. Inflated scores waste everyone's time. A "Moderate" rating with a clear improvement path is more useful than a fake "Strong."

### 4. Delta Is King

The first snapshot of each type establishes a baseline. Every subsequent snapshot's most valuable section is the delta: what changed, why, and what to do about it. Snapshots without deltas lose half their value.

### 5. Propagation, Not Compliance

Culture assessments track whether principles are **spreading organically**, not whether people are following procedures. The question is "does the night shift stop the line for quality issues because they've internalized the principle?" not "does the night shift follow the line-stop procedure?"

Compliance can be measured by audits. Culture can only be measured by observing what people do when the auditor isn't watching.

### 6. Audience-Appropriate

Structure snapshots are for management. Capability reviews are for the unit owner (and optionally their supervisor). Culture snapshots may be leadership-only. Design each output for its actual reader.

## Cadence Alignment

```
Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
 │    │    │    │    │    │    │    │    │    │    │    │
 C    C    C    C    C    C    C    C    C    C    C    C   ← Capability (monthly)
 │         │              │              │              │
 S    ·    S    ·    ·    S    ·    ·    S    ·    ·    S   ← Structure (quarterly)
 │         │              │              │              │
 K    ·    K    ·    ·    K    ·    ·    K    ·    ·    K   ← Culture (quarterly)
```

Structure and Culture snapshots run in the same quarter but can be offset by a week. Capability reviews run monthly, feeding fresh observations into the quarterly assessments.

**Event-triggered runs:** Beyond the fixed cadence, trigger additional snapshots when:
- A new unit is onboarded (person hired, machine commissioned) and has 4+ weeks of data
- A unit is decommissioned or someone leaves
- A significant operational change occurs (new product line, shift restructuring, reorganization)

## Example: Manufacturing Plant

A mid-size manufacturer with 3 production lines, 40 operators across 2 shifts, and 5 supervisors.

**Observation sources:** Shift handover logs (daily), quality reports (per-batch), maintenance tickets (continuous), production meetings (weekly).

| Assessment | What It Reveals |
|-----------|----------------|
| Structure Snapshot | Line 3 is running at 120% capacity with no buffer. Night shift has 2 fewer operators than day shift but same targets. Maintenance backlog is 3x what it was last quarter. |
| Capability Review | Operator A on Line 2 is ready for cross-training on Line 3. The new CNC machine has 40% more unplanned downtime than the vendor promised. Junior operators on night shift are improving but still need supervisor sign-off for changeovers. |
| Culture Snapshot | Day shift stops the line for quality issues without hesitation (strong). Night shift tends to push questionable units through and flag them at handover (weak, eroding). Knowledge sharing between shifts is one-directional: day → night via handover log, but night shift insights rarely flow back. Root cause analysis is blame-free on Line 1 and 2 (supervisor models it) but punitive on Line 3 (different supervisor). |

**Cross-feed in action:**
- Culture reveals Line 3's blame culture → Capability review for Line 3 supervisor focuses on coaching style → Structure snapshot flags Line 3 supervisor as a single point of failure for that line's culture
- Capability reveals Operator A is ready for Line 3 → Structure snapshot recommends the cross-training to reduce Line 3 capacity pressure → Culture snapshot next quarter tracks whether Operator A brings Line 2's quality culture to Line 3

## Anti-Patterns

- **Assessment theater.** Running the assessments without acting on recommendations. Each output should produce concrete next actions with owners and deadlines.
- **Over-indexing on one lens.** Structure without culture misses how work actually happens. Culture without structure misses whether the operation can execute. Capability without both misses context.
- **Separate data collection.** Creating new forms, surveys, or audits for each assessment instead of analyzing existing operational records. If you need new data collection, the operation has a bigger problem than assessments can solve.
- **Cheerleading.** Assessments that only highlight strengths. The value is in surfacing what needs attention before it becomes a crisis.
- **Skipping the delta.** Running assessments without comparing to previous snapshots. Trend is more important than absolute score. A "Weak" that was "Absent" last quarter is progress.
- **Confusing culture with compliance.** Procedure adherence is measurable by audit. Culture is observable in how people behave when the procedure doesn't cover the situation.

## When to Use This Pattern

The triad is most valuable for:
- **Small-to-mid operations (5-50 units)** where management can act directly on findings
- **Fast-changing environments** where structure risks outpacing culture (rapid hiring, new product lines, shift restructuring)
- **Principle-driven organizations** that want to verify their principles are lived, not just posted on the wall
- **Distributed or multi-shift operations** where behavioral signals are harder to observe casually

It's less useful for:
- Large enterprises with mature continuous improvement programs (they have their own frameworks)
- Operations without regular records to analyze (insufficient data source)
- Organizations that haven't articulated their operating principles (start there first)

## Adapting to Your Domain

The pattern is domain-agnostic. Replace the specifics:

| Concept | Manufacturing | Software | Services |
|---------|--------------|----------|----------|
| Unit | Operator, machine, cell, line | Engineer, team, service, repo | Consultant, project, account |
| Observation source | Shift logs, quality reports, maintenance records | Standups, PRs, incidents, retros | Client calls, project reports, timesheets |
| Structure | Plant layout, shift roster, equipment list | Org chart, team topology, tech stack | Account structure, team allocation, service catalog |
| Capability | Skill matrix, machine uptime, changeover time | Shipping velocity, code quality, on-call readiness | Utilization, client satisfaction, domain expertise |
| Culture | Line-stop behavior, knowledge sharing, blame response | Escalation patterns, failure ownership, autonomy | Client advocacy, knowledge reuse, quality standards |

The principles stay the same. The data sources and vocabulary change.
