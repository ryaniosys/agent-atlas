# Continuous Improvement Skill Loop

A pattern for agent skill chains that implement PDCA (Plan-Do-Check-Act) across recurring workflows. Each cycle's output feeds the next cycle's input, compounding improvements over time.

## The Problem

Recurring workflows (training cycles, quarterly reviews, onboarding batches, sprint ceremonies) generate improvement signals after each iteration — participant feedback, scoring patterns, broken processes, commitments made. Without a structured loop, these signals get lost between cycles. The next iteration repeats the same mistakes because the predecessor plan is reused without cross-referencing what actually happened.

## The Pattern

A closed-loop skill chain that implements PDCA (Plan-Do-Check-Act) with agent skills at each phase:

```
                 ┌──────────────┐
                 │    PLAN      │
                 │  /prep skill │◄──────────────┐
                 └──────┬───────┘               │
                        │                       │
                        v                       │
                 ┌──────────────┐               │
                 │     DO       │               │
                 │  (execute)   │               │
                 └──────┬───────┘               │
                        │                       │
              ┌─────────┼─────────┐             │
              v                   v             │
       ┌──────────────┐   ┌──────────┐          │
       │    CHECK     │   │  CHECK   │          │
       │ /post skill  │   │ /eval    │          │
       │ (outcomes)   │   │ skill    │          │
       └──────┬───────┘   └────┬─────┘          │
              │                │                │
              v                v                │
       ┌─────────────────────────────┐          │
       │           ACT               │          │
       │      /retro skill           │──────────┘
       │  (improvement analysis)     │
       └─────────────────────────────┘
```

### Skill Responsibilities

| PDCA Phase | Skill | Input | Output |
|---|---|---|---|
| **Plan** | `/prep` | Previous retro analysis + predecessor materials | Informed briefing with known issues flagged |
| **Do** | (manual) | Briefing | Session executed |
| **Check** | `/post` | Outcome data (scores, feedback) | Reflection: what worked, what didn't |
| **Check** | `/eval` | Rubric + deliverables + optional transcript | Per-item scoring with explainable feedback |
| **Act** | `/retro` | Reflection + eval + predecessor plan + promises | Improvement recommendations for next cycle |

### The Retro Skill: Root Cause Analysis

The retro skill closes the loop. It performs a structured root cause analysis:

1. **Reads** the post-cycle reflection (outcomes)
2. **Reads** eval results (which criteria scored low — process gap?)
3. **Reads** the predecessor plan for the *next* cycle
4. **Extracts** commitments made during the current cycle
5. **Cross-references** with previous retros for recurring deviations
6. **Outputs** two files:
   - **Cycle analysis:** recommended changes for the next iteration
   - **Cumulative patterns file:** recurring deviations across all cycles

The cumulative patterns file is the equivalent of a **control chart** — it tracks process deviations over time. When the same problem appears in 2+ cycles, it surfaces as a structural issue requiring a design change, not just a local fix.

### The Dual-Folder Pattern

Recurring workflows generate two categories of artifacts:

| Category | Storage | Rationale |
|----------|---------|-----------|
| **Methods** (skills, templates, reflections) | Version-controlled repo | Reusable, no sensitive data |
| **Sensitive** (deliverables, scores, transcripts) | Local/private storage | Contains PII or confidential data |

Skills must know which storage to target. The eval skill writes to private storage; the reflection goes in the repo. Mixing these up leaks sensitive data into version history.

## Why a Closed Loop?

The naive approach is linear: plan, execute, done. Improvements happen ad-hoc, if at all. The closed loop ensures:

- **Nothing gets lost** — feedback, broken processes, and commitments are captured immediately after each cycle
- **Predecessor analysis is automatic** — the retro skill flags inherited problems before they repeat
- **Patterns compound** — the cumulative file builds institutional knowledge across iterations
- **The prep skill is informed** — it reads retro findings, so the next cycle starts with known issues pre-flagged

## When to Use

- Any domain with **recurring cycles** that build on each other
- Workflows where **predecessor materials** exist but need iterative improvement
- Situations where **multiple check signals** (qualitative reflection + quantitative scoring) are available

## When NOT to Use

- One-off processes with no feedback loop
- Fully automated pipelines where the agent has no agency to change the process
- Workflows where no outcome data is captured

## Implementation Tips

1. **Start with Check, not Plan.** Build the `/post` and `/eval` skills first — they generate the data that makes the retro valuable. Without outcome data, the retro has nothing to cross-reference.

2. **The retro skill should read, not guess.** It cross-references concrete artifacts (reflections, scores, predecessor plans), not vibes. Every recommendation should cite its source.

3. **Keep the cumulative patterns file append-only.** Date-stamp each update. Don't overwrite previous entries — the value is in seeing patterns emerge over time.

4. **Wire the loop explicitly.** The prep skill must actively check for retro output. A retro that nobody reads is waste. Add a step to the prep skill: "Check for retro analysis file. If found, include findings in briefing."

5. **Separate the two Check skills.** The reflection (qualitative) and the eval (quantitative) serve different purposes. The reflection captures what the operator experienced; the eval captures what the deliverables show. The retro triangulates between them.

## Related Patterns

- [TDD Wave Pattern](tdd-wave-pattern.md) — similar separation of concerns (test vs. implement is analogous to check vs. act)
- [Decision Log / Learning Loop](decision-log-learning-loop.md) — the retro skill is a specialized learning loop for recurring processes
- [Skill Authoring Checklist](skill-authoring-checklist.md) — each skill in the chain should follow this checklist
