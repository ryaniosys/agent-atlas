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
