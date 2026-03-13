# Iterative Challenge Document

A pattern for agent skills that pressure-test a decision over multiple rounds. Each round incorporates new data, updates a scoring system, and refines the recommendation. The output is a living document that grows with each round.

## Problem

High-stakes decisions (hiring, vendor selection, investment, architecture) often get evaluated once and then rubber-stamped. When new information surfaces days or weeks later, it doesn't get systematically integrated into the original analysis. The decision maker re-evaluates from scratch or ignores the new data.

## Solution

Structure the analysis as a numbered series of rounds in a single living document. Each round challenges the previous assessment with new data, updates a scoring table, and recalibrates the recommendation. The document grows over multiple sessions, with agent memory bridging the gaps.

## Architecture

```
Session 1:  Round 1 (initial challenge) → user pushback → Round 2 (updated)
Session 2:  New data arrives → Round 3 (incorporate + re-score)
Session 3:  More data → Round 4 → decision converges
```

The document lives in a domain folder (not git), with an `_agent_memory.md` file enabling cold-start resumption across sessions.

## Document Structure

Each round follows a consistent template:

```markdown
## Round N: <Descriptive Name> (YYYY-MM-DD)

### New Information
What changed since the last round.

### What This Changes
How the new data updates previous assumptions.

### Updated Scoring

| Dimension | Previous | Updated | Reason |
|-----------|----------|---------|--------|
| ...       | X/10     | Y/10    | ...    |

### Updated Bottom Line
Current recommendation with confidence level.
```

## Scoring System

Maintain a table of scored dimensions that evolves across rounds:

- **Start with 5-7 core dimensions** relevant to the decision type
- **Add dimensions** as new data reveals them (e.g., "cultural fit" only scoreable after an on-site visit)
- **Never remove dimensions**, only update scores
- **Show the trajectory**: include a "Previous" column so readers can see how scores shifted
- **Score on /10 scale** with one-line rationale

The final round includes a full trajectory table across all rounds.

## Round Types

Not all rounds come from the same source. Common triggers:

| Trigger | Round Focus |
|---------|-------------|
| User pushback / reframing | Recalibrate based on strategic context the agent missed |
| External document (resume, profile, spec) | Fact-check prior assumptions, correct errors |
| Transcript / recording | Behavioral signals, cultural indicators, unscripted insights |
| Reference / interview notes | Third-party validation of claimed strengths and risks |
| Meeting outcome | Resolve remaining unknowns, final calibration |

## Adversarial First Round

The first round must genuinely challenge the decision. This is the core value of the pattern. The agent is not a validator; it is a sparring partner.

Structure for Round 1:

1. **Financial framing**: What does this really cost? Is there a cheaper alternative?
2. **Role/scope challenge**: Is the full scope needed, or could a subset achieve 80% of the value?
3. **Timing challenge**: Is now the right time, or would waiting 3-6 months change the equation?
4. **Central question**: Frame the core tension as a direct quote (e.g., "Are you building X or Y? Your strategy says X. Your actions say Y.")
5. **Lean alternative**: Always present the minimum-commitment version

The user's rebuttal to Round 1 often produces the strongest framing for the decision. That rebuttal becomes Round 2.

## Cross-Session Continuity

The document spans multiple sessions. Bridge the gaps with:

1. **Agent memory file** (`_agent_memory.md`) in the same folder:
   - Current status (which round, what's pending)
   - Key file index
   - External IDs (CRM records, transcript IDs)
   - Next actions (checkbox format)
   - Key context (5-7 bullets, decision-relevant only)

2. **Round numbering** provides a natural resume point: "Last session ended at Round 5. New data available for Round 6."

3. **The document itself is the context**: reading the analysis file from the top gives any agent (or human) the full decision history without needing conversation logs.

## Handling External Documents

When new data arrives (profiles, transcripts, reports), always cross-check against prior rounds:

1. **Identify factual corrections** (wrong titles, missing experience, incorrect dates)
2. **Update surrounding documents** that reference the corrected facts
3. **Note corrections in the round** so readers understand what changed and why

Never silently correct prior rounds. Document all corrections in the current round with explicit "was X, actually Y" notation.

## Decision Convergence

The analysis should converge on a clear outcome. Include a decision framework:

| Outcome | Criteria |
|---------|----------|
| **Proceed** | Score >= threshold, no unresolved blockers |
| **Trial / limited commitment** | Score moderate, or concerns testable in a bounded period |
| **Pass** | Score below threshold, or blockers that bounded testing can't resolve |

State the remaining gates explicitly: "Two gates remain: (1) X and (2) Y. Everything else points to proceed."

## Key Principles

1. **Challenge first, validate second** — Round 1 is adversarial, not confirmatory
2. **Show your work** — every score change includes a one-line reason
3. **Preserve history** — never edit prior rounds, only add new ones
4. **Separate analysis from synthesis** — the challenge doc is for the decision maker; team-facing summaries are separate documents updated from the analysis
5. **Cross-check external data** — documents like resumes or profiles often contain errors; always verify against primary sources
6. **State limitations** — if a data source can only validate some dimensions, say so explicitly

## Applicable Skills

Any skill that supports a multi-factor decision over days or weeks:

- Hiring evaluations (candidate fit, reference validation, team chemistry)
- Vendor or tool selection (feature comparison, pricing, integration risk)
- Architecture decisions (build vs. buy, platform selection, migration planning)
- Investment decisions (market entry, product bets, partnership evaluation)
- Supplier qualification (capability audit, quality history, risk assessment)
- Production line design (capacity analysis, automation trade-offs, layout options)

## Manufacturing Examples

**Supplier Qualification:** An agent evaluates a new raw material supplier across 4 rounds. Round 1: cost comparison against incumbents. Round 2: site audit findings (quality system maturity, capacity). Round 3: sample testing results (dimensional accuracy, surface finish). Round 4: commercial terms negotiation outcome. Each round updates scores for cost, quality capability, delivery reliability, and risk. Final recommendation: qualify for non-critical parts first, expand to critical parts after 6-month track record.

**Equipment Investment:** An agent challenges a proposal to purchase a new CNC machining center. Round 1: financial challenge (ROI at current utilization vs. outsourcing). Round 2: production planning input (capacity bottleneck data validates need). Round 3: vendor comparison (3 options scored on precision, lead time, service network). Round 4: integration assessment (IT/OT connectivity, operator training). Scoring evolves from pure financial to include operational and strategic dimensions.
