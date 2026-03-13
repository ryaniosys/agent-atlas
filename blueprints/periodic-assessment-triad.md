# Periodic Assessment Triad

A pattern for agent-assisted organizational development using three complementary periodic assessments: structure, individuals, and culture. Each assessment has its own cadence, audience, and output, but they cross-feed to create a complete picture.

## Problem

Organizations track metrics (revenue, velocity, headcount) but rarely track the qualitative dimensions that determine long-term health. When they do, it's ad-hoc: a quarterly offsite exercise, a manager's gut feel, or a crisis-driven retrospective. The assessments don't connect, so structural problems get diagnosed as people problems, cultural erosion gets missed until it's a crisis, and individual feedback lacks organizational context.

## Solution

Three periodic assessment skills, each focused on a different organizational lens:

| Skill | Lens | Cadence | Audience | Question It Answers |
|-------|------|---------|----------|-------------------|
| **Structure Snapshot** | Organizational design | Quarterly | Leadership | Do we have the right roles, people, and capacity? |
| **Individual Feedback** | Per-person development | Monthly | Per-person (+ manager gate) | How is each person growing and contributing? |
| **Culture Snapshot** | Collective values & behavior | Quarterly | Founder/CEO | Are our stated values showing up in team behavior? |

The triad works because each lens reveals what the others miss:
- Structure tells you **what** the org looks like
- Individual feedback tells you **who** is doing what
- Culture tells you **how** the org actually operates

## Architecture

```
                    ┌─────────────────────┐
                    │  Meeting Transcripts │
                    │  (Observation Source) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Team Profiles      │
                    │  (Per-Person Logs)   │
                    └──┬──────┬──────┬────┘
                       │      │      │
              ┌────────▼─┐ ┌─▼────────┐ ┌▼──────────┐
              │ Structure │ │Individual│ │  Culture   │
              │ Snapshot  │ │ Feedback │ │  Snapshot  │
              └─────┬─────┘ └────┬─────┘ └─────┬─────┘
                    │            │              │
                    └────────────┼──────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Cross-Feed Outputs     │
                    │ (Recommendations flow    │
                    │  between assessments)    │
                    └─────────────────────────┘
```

### Shared Data Layer

All three skills read from the same observation source: **team profiles** populated from meeting transcripts. This is critical. The assessments don't rely on surveys, self-reports, or separate data collection. They analyze the same behavioral data through different lenses.

Typical observation sources:
- Leadership meetings (strategy, pipeline, hiring decisions)
- Engineering standups (technical decisions, work patterns, blockers)
- Planning sessions (prioritization, architectural choices)
- 1:1s and coaching calls (individual development)

### Cross-Feed Pattern

Each assessment produces recommendations that feed into the others:

| From | To | What Flows |
|------|----|-----------|
| Structure → Individual | Role gaps identified in structure inform individual stretch assignments |
| Structure → Culture | Team composition changes trigger culture impact assessment |
| Individual → Culture | "Acme-Person is a strong carrier of Value X" becomes a culture data point |
| Culture → Individual | "Value Y is weak at engineering level" becomes a development focus |
| Culture → Structure | Cultural gaps may indicate missing roles or wrong org design |
| Individual → Structure | Growth trajectories inform hiring priorities |

## Implementation Pattern

### 1. Observation Collection (Continuous)

Agent processes meeting transcripts and extracts per-person behavioral observations into structured profile files. Each entry is tagged with meeting type and date.

```markdown
### YYYY-MM-DD [Meeting Type]

**Observations:**
- Behavioral observation with specific evidence

**Flags:**
- GREEN: Positive pattern worth reinforcing
- YELLOW: Pattern worth monitoring
- RED: Pattern requiring intervention
```

### 2. Structure Snapshot (Quarterly)

Reads: role definitions, team roster, previous snapshot, financial context.
Outputs: team tables, org chart, strengths/gaps/risks, hiring priorities, delta from previous.

Key sections:
- Team roster with pensum and focus
- Org structure (visual)
- Strengths, gaps, and risks (numbered by severity)
- Hiring priority assessment
- "What to Watch" checklist for next quarter

### 3. Individual Feedback (Monthly)

Reads: team profiles (last 4 weeks of observations), writing style guide.
Outputs: per-person feedback document (PDF + email draft).

Key design decisions:
- **Founder gets self-reflection only** (no email, just PDF for journaling)
- **Manager review gate** for junior team members (feedback goes to manager first)
- **Language follows the person** (feedback in their preferred language)
- **Minimum observation threshold** (skip if insufficient data)

### 4. Culture Snapshot (Quarterly)

Reads: canonical values doc, team profiles, dynamics files, previous snapshot.
Outputs: values scorecard, propagation map, health indicators, recommendations.

Key sections:
- **Values Alignment Scorecard:** Each value scored (Strong/Moderate/Weak/Absent) with trend
- **Propagation Map:** How far each value has spread (Founder → Leadership → Team)
- **Health Indicators:** Psychological safety, information flow, decision speed, failure response, autonomy
- **Growth Impact:** Cultural effect of team changes since last snapshot
- **Delta:** What strengthened, eroded, or emerged

## Design Principles

### 1. Same Data, Different Lenses

Never create separate data collection for each assessment. One observation source, three analytical perspectives. This keeps the system lightweight and ensures consistency.

### 2. Evidence Over Vibes

Every score, rating, and recommendation must cite specific dates, quotes, or behavioral examples. "The team has good psychological safety" is useless. "Acme-Person challenged the CEO on product direction in the Mar 6 meeting and the disagreement resolved in under 3 minutes" is evidence.

### 3. Honest, Not Diplomatic

These are internal reflection tools. Inflated scores waste the founder's time. A "Moderate" rating with a clear growth path is more useful than a fake "Strong."

### 4. Delta Is King

The first snapshot of each type establishes a baseline. Every subsequent snapshot's most valuable section is the delta: what changed, why, and what to do about it. Snapshots without deltas lose half their value.

### 5. Propagation, Not Compliance

Culture skills track whether values are **spreading organically** through the team, not whether people are complying with rules. The question is "does Acme-Person share failures because they've internalized the value?" not "does Acme-Person follow the post-mortem process?"

### 6. Audience-Appropriate

Structure snapshots are for leadership. Individual feedback is for the person (and optionally their manager). Culture snapshots may be founder-only. Design each output for its actual reader.

## Cadence Alignment

```
Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
 │    │    │    │    │    │    │    │    │    │    │    │
 F    F    F    F    F    F    F    F    F    F    F    F   ← Individual (monthly)
 │         │              │              │              │
 S    ·    S    ·    ·    S    ·    ·    S    ·    ·    S   ← Structure (quarterly)
 │         │              │              │              │
 C    ·    C    ·    ·    C    ·    ·    C    ·    ·    C   ← Culture (quarterly)
```

Structure and Culture snapshots run in the same quarter but can be offset by a week. Individual feedback runs monthly, feeding fresh observations into the quarterly assessments.

**Event-triggered runs:** Beyond the fixed cadence, trigger additional snapshots when:
- A new team member has been onboarded for 4+ weeks
- Someone leaves the team
- A significant organizational change occurs (new team, new product line)

## Anti-Patterns

- **Assessment theater.** Running the assessments without acting on recommendations. Each output should produce concrete next actions.
- **Over-indexing on one lens.** Structure without culture misses how work actually happens. Culture without structure misses whether the org can execute. Individual without both misses context.
- **Separate data collection.** Creating surveys or forms for each assessment instead of analyzing existing behavioral data.
- **Cheerleading.** Assessments that only highlight strengths. The value is in surfacing what needs attention.
- **Skipping the delta.** Running assessments without comparing to previous snapshots. Trend is more important than absolute score.

## When to Use This Pattern

The triad is most valuable for:
- **Small teams (3-15 people)** where the founder/CEO can act directly on findings
- **Fast-growing organizations** where culture risks outpacing structure
- **Values-driven companies** that want to verify their values are lived, not just stated
- **Remote or async teams** where behavioral signals are harder to read casually

It's less useful for:
- Large organizations with HR departments (they have their own frameworks)
- Teams without regular meetings to observe (insufficient data source)
- Organizations that don't have articulated values (start there first)
