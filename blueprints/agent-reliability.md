# Agent Reliability Blueprint

> Principles for building agent systems that hold up in production.

## The Core Problem: Compounding Failure

Agent systems are chains. Each step's reliability multiplies through the chain:

```
End-to-end reliability = step_1 * step_2 * ... * step_n
```

A 7-step process with 98% per-step accuracy delivers only **86.8% end-to-end**. This is why agents that "work great in demos" fail in production — the math works against you at scale.

| Approach | Per-step | 7 steps | End-to-end |
|----------|----------|---------|------------|
| Manual / basic RPA | 97% | 0.97^7 | **80.8%** |
| Pure agentic (LLM at every step) | 98% | 0.98^7 | **86.8%** |
| Hybrid (5 deterministic + 2 agentic) | 5 × 99.5% + 2 × 97% | mixed | **96.5%** |

The insight: **not "deterministic or stochastic" — but "which steps need which approach."**

Sources: [Rabanser et al., 2026](#sources) for the reliability framework; compounding error model widely discussed in [O'Reilly](#sources), [Serokell](#sources), and industry literature.

---

## The Hybrid Principle

Use **deterministic tools** for structured, repeatable steps. Use **stochastic processes** (LLMs, agents) for steps requiring judgment, flexibility, or natural language understanding.

### When to Use Deterministic Tools

- **Structured data lookups** — API calls, database queries, config reads
- **Template-based generation** — filling known fields into known formats
- **Routing and classification** with finite, known categories
- **File operations** — create, move, rename, parse
- **Calendar/scheduling** — availability checks, event creation
- **Calculations** — pricing, date math, aggregations

**Reliability profile:** 99%+ per step. Failures are infrastructure issues (API down, network timeout), not logic errors.

### When to Use Stochastic Processes

- **Natural language understanding** — interpreting intent, extracting entities from unstructured text
- **Judgment calls** — triage priority, tone matching, relevance scoring
- **Creative generation** — drafting emails, summarizing meetings, writing content
- **Ambiguous classification** — when categories aren't cleanly separable
- **Multi-step reasoning** — connecting dots across sources, strategic analysis

**Reliability profile:** 95–98% per step. Failures are hallucination, misinterpretation, or inconsistency.

---

## Decision Framework

For each step in a workflow, ask:

```
Is the input structured and the output deterministic?
  → YES: Use a tool (API call, script, template)
  → NO: Does it require language understanding or judgment?
    → YES: Use an LLM
    → NO: Use a tool with validation
```

### The Determinism Ladder

Prefer higher rungs. Drop to lower rungs only when the task demands it.

| Rung | Mechanism | Per-step reliability | Example |
|------|-----------|---------------------|---------|
| 1 (highest) | Direct API call | ~99.9% | Create calendar event via Graph API |
| 2 | Script with validation | ~99.5% | Parse CSV, validate schema, insert |
| 3 | LLM with constrained output | ~98% | Classify email into 5 categories |
| 4 | LLM with structured tools | ~97% | Extract entities, call APIs based on result |
| 5 (lowest) | Free-form LLM generation | ~95% | Draft a response to an ambiguous request |

---

## Patterns from Production

### Pattern 1: Deterministic Shell, Stochastic Core

Wrap LLM judgment inside deterministic scaffolding:

```
[Deterministic] Fetch emails via API
[Deterministic] Parse headers, extract metadata
[Stochastic]    Classify intent and priority (LLM)
[Deterministic] Route to correct queue based on classification
[Deterministic] Create ticket via API with structured fields
[Stochastic]    Draft response (LLM)
[Deterministic] Save draft via API
```

5 deterministic steps (99.5% each) + 2 stochastic steps (97% each) = **96.5%** end-to-end.

Compare: all 7 steps as LLM calls (98% each) = **86.8%**.

**Manufacturing variant — Incoming Goods Inspection:**

```
[Deterministic] Fetch purchase order and spec sheet from ERP
[Deterministic] Read measurement data from gauge/sensor
[Stochastic]    Classify defect from inspection photo (LLM vision)
[Deterministic] Log measurement results against tolerance limits
[Stochastic]    Recommend disposition: accept / rework / reject (LLM judgment)
[Deterministic] Create quality record in MES via API
[Deterministic] Update lot status in ERP
```

5 deterministic + 2 stochastic = same reliability math as the email example.

### Pattern 2: Validate After Every Stochastic Step

Never chain LLM outputs without a validation checkpoint:

```
[Stochastic]    Extract meeting time from email
[Deterministic] Validate: is this a valid ISO datetime?
[Stochastic]    Extract attendee list
[Deterministic] Validate: are these real email addresses?
[Deterministic] Check calendar availability via API
[Deterministic] Create event via API
```

The deterministic validation steps are nearly free (99.9% reliability) but catch the ~2-5% of LLM failures before they cascade.

### Pattern 3: Progressive Autonomy

Start with human-in-the-loop, earn autonomy through reliability:

| Stage | Reliability threshold | Autonomy level |
|-------|----------------------|----------------|
| Pilot | < 95% | Agent drafts, human executes |
| Supervised | 95–97% | Agent executes, human reviews |
| Autonomous | > 97% | Agent executes, human audits sample |

Only promote when measured reliability (not estimated) exceeds the threshold consistently across multiple runs.

### Pattern 4: Alert Only on Persistent Failure

An unattended monitor that alerts on *transient* failures is worse than no monitor: recurring false alarms train the recipient to mute it, so the one real alert is ignored too. Separate transient failures (rate limits, timeouts, 5xx) from persistent ones.

- **Ride through transient failures.** Retry with exponential backoff, honoring any `Retry-After` header the API returns. A rate-limited usage/cost API can throttle a burst of queries for tens of seconds; a generous retry budget (e.g. ~6 attempts, backoff capped near a minute) lets a single run absorb the throttle and still return a correct result.
- **Fail loud only when the retry budget is exhausted** — that is now a genuine, actionable problem worth paging on, not noise.
- **Stay silent when there's nothing to say.** A guardrail that fires only on a real breach (threshold, forecast, anomaly) must emit *nothing* otherwise. An empty run is the success case, not an occasion for a heartbeat message.

```
[Transient error?] --yes--> backoff + retry (honor Retry-After), up to N
                   --no---> fail loud immediately (real, non-retryable error)
[Retries exhausted] ------> fail loud: persistent failure, worth paging
[Nothing tripped]  ------> emit nothing (silent success)
```

The failure mode this prevents: a monitor that cries wolf on every rate-limit blip until everyone mutes the channel — including for the one alert that mattered.

### Pattern 4b: Wire Silence and Loudness to the Runtime's Own Channels

"Stay silent on success, fail loud on failure" stays a principle until you decide *which channel carries which signal*. Most schedulers already hand you three, and using them as intended is less code than inventing your own reporting.

| Channel | Carries | Rule |
|---------|---------|------|
| **stdout** | the delivered message | Emit nothing on a healthy run. Empty output should mean "no notification", not "empty notification". |
| **stderr** | diagnostics | Typically discarded on a zero exit and attached to the alert on a non-zero one, which makes it the right home for a "nothing to report" note that a human running the job by hand still wants to see. |
| **exit code** | the alarm | Non-zero triggers the runtime's own failure path: a visually distinct alert plus a failed status on the job record. Better than printing your own "ERROR:" line into the normal report stream, where it reads like every other message. |

Four things this reliably gets wrong in practice:

- **A no-op line is not silence.** "0 items found", "no changes since yesterday", "nothing to do" are the single most common source of scheduled-job noise. Route them to stderr and let stdout stay empty.
- **A per-job instruction can silently override a runtime-level silence contract.** If the platform injects "reply with the silence sentinel when there is nothing to report" but the job's own prompt says "if nothing changed, say *No changes today*", the specific instruction wins and the job notifies on every run. When a job is noisy, audit its own configuration for a no-op fallback before concluding the mechanism is broken.
- **A cooldown must gate the alarm, not just the message.** On a high-frequency schedule, an upstream outage that alerts on every tick is the cry-wolf failure in a new costume. Gate the *exit code* on the same cooldown as the message, and keep writing every suppressed run to the job's own log so the history stays complete.
- **Unhandled exceptions bypass your gate.** A crash exits non-zero too, so a systemic failure that raises before reaching your cooldown logic alerts on every tick while your carefully gated per-item failures stay quiet. Funnel every failure path through a single exit point that owns logging, gating, and the return code. Keep interactive runs raising normally so a human debugging by hand still gets the traceback.

```
[Healthy run]               -> stdout empty, exit 0       (no notification)
[Nothing to report]         -> note to stderr, exit 0     (no notification)
[Failure, cooldown elapsed] -> detail to stderr, exit N   (runtime alert + failed status)
[Failure, within cooldown]  -> log only, exit 0           (no notification, history intact)
```

Verify the loud path without spamming a real channel: create a throwaway job pointing at a script that only does `exit 1`, aim its delivery at a local or scratch target, fire it once, and read what the runtime rendered. That proves the alert wiring end to end without a single message reaching the team.

There is a matching optimization on the quiet side. If the runtime supports a pre-check script whose output decides whether the expensive step runs, put a cheap deterministic check in front of an LLM-driven job. On a quiet run it skips the model entirely, so silence costs nothing instead of costing a full inference that ends in "nothing to report".

---

## Anti-Patterns

### 1. "The LLM Can Handle It"

Using an LLM for tasks that have deterministic solutions:

- **Bad:** LLM extracts a date from a structured JSON field
- **Good:** `jq '.event.start_date'` — zero ambiguity, zero failure

### 2. Chaining Without Checkpoints

Running 5+ LLM calls in sequence without validating intermediate results:

- **Bad:** Extract → Classify → Route → Draft → Send (all LLM, no validation)
- **Good:** Extract → **Validate** → Classify → **Validate** → Route → Draft → **Review** → Send

### 3. Overfit to Demo Success

A workflow that works 9/10 times in testing will fail 1/10 times in production — at scale, that's hundreds of failures per day.

- **Bad:** "It worked in my tests, ship it"
- **Good:** Run 50+ varied inputs, measure per-step and end-to-end reliability, identify the weakest link

### 4. Symmetry Assumption

Assuming all steps have equal reliability and optimizing globally instead of targeting the weakest link:

- **Bad:** "Our overall reliability is 90%, let's improve everything"
- **Good:** "Step 3 (entity extraction) fails 8% of the time — fix that first"

### 5. Using Agents for Lookup Tables

If the answer is in a table, read the table. Don't ask an LLM to reason about it.

- **Bad:** "What's the VAT rate for Switzerland?" → LLM
- **Good:** `config['vat_rates']['CH']` → 8.1%

- **Bad:** "What's the tolerance for part XYZ-100?" → LLM
- **Good:** `spec_sheet['XYZ-100']['tolerance_mm']` → ±0.05mm

---

## Measuring Reliability

The Princeton HAL framework ([Rabanser et al., 2026](#sources)) decomposes reliability into:

| Dimension | What it measures |
|-----------|-----------------|
| **Consistency** | Same input → same output across runs |
| **Robustness** | Handles edge cases, malformed input, environment changes |
| **Safety** | Doesn't cause harm, respects boundaries |
| **Calibration** | Confidence matches actual accuracy |

Key finding: **consistency is the weakest dimension** across all frontier models (correlation between accuracy improvements and consistency improvements: r = 0.02). Models are getting more capable but not more predictable.

Implication: deterministic tools don't just improve reliability — they improve **consistency**, which is the dimension LLMs struggle with most.

---

## Applying This to Agent Repos

When authoring skills (see [Convention #4](best-practices.md#4-skills) and the [skill authoring checklist](skill-authoring-checklist.md)):

1. **Map the workflow** — list every step
2. **Classify each step** — deterministic or stochastic?
3. **Push steps up the determinism ladder** — can any LLM step be replaced with a tool?
4. **Add validation checkpoints** after every stochastic step
5. **Measure** — run the skill 10+ times with varied inputs, log per-step success
6. **Target the weakest link** — improve the lowest-reliability step first

---

## Sources

- Rabanser, S., Kapoor, S., Kirgis, P., Liu, K., Utpala, S., & Narayanan, A. (2026). *Towards a Science of AI Agent Reliability*. arXiv:2602.16666. https://arxiv.org/abs/2602.16666
- Princeton HAL Interactive Reliability Dashboard. https://hal.cs.princeton.edu/reliability
- O'Reilly Radar. *The Hidden Cost of Agentic Failure*. https://www.oreilly.com/radar/the-hidden-cost-of-agentic-failure/
- Serokell. *The Real Limits of AI Agents in 2025*. https://serokell.io/blog/the-real-limits-of-ai-agents-in-2025
- Prodigal Tech. *Why Most AI Agents Fail in Production: The Compounding Error Problem*. https://www.prodigaltech.com/blog/why-most-ai-agents-fail-in-production
