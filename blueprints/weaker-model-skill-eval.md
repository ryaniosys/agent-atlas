# Weaker-Model Skill Eval

A technique for answering "is this skill detailed enough that a *less capable* model could execute it later?" — by actually running it with a weaker model as the executor, instead of reasoning about it abstractly.

## The Problem

When you write a skill (a reusable instruction document for an agent), you usually test it with a strong model — often the same one that helped author it. That model fills gaps from its own judgment: it infers missing steps, disambiguates vague instructions, and silently works around bad examples. The result looks great, so you ship it.

Then a weaker or cheaper model runs the skill in production and fails in ways you never saw, because it only does what the skill *literally says*. The skill was never really tested — the strong model was compensating for it.

## The Pattern

Run the skill with a deliberately weaker model as the executor, against a real task, and compare to a no-skill baseline:

```
        same realistic task
        ┌──────────────────────┐
        v                      v
┌───────────────┐      ┌───────────────┐
│ weak model    │      │ weak model    │
│  + the skill  │      │  no skill     │   <- baseline
└───────┬───────┘      └───────┬───────┘
        │                      │
        v                      v
   grade both against known ground truth
        │
        v
  with-skill should lift PROCESS/JUDGMENT
  over baseline; gaps it can't cover are
  the skill's real defects
```

- Spawn two executors **in parallel**, same prompt, one given the skill and one without.
- Prefer a **read-only / extraction task** for the eval so no live system is mutated.
- Grade against ground truth you already know. The baseline shows what the skill is actually adding; the with-skill failures show what the skill still under-specifies.

## What a Weak Executor Reliably Exposes

- **Under-specification.** Steps the author assumed were "obvious" that the weak model skips or does wrong.
- **Example contamination.** Worked examples with near-real values get **copied over the actual input**. A weak model trusts a concrete example in the skill more than the messy real data in front of it. Keep all examples *obviously fictional* (use placeholder domains like `acme-corp.example`) so they can't be mistaken for input.
- **Missing guardrails.** Where the baseline does something unsafe (e.g. uses an invalid field, skips a confirmation), the skill should explicitly prevent it — if it doesn't, that's a gap.
- **Inherent model limits** (e.g. OCR/transcription noise on fine print) that no instruction fully removes — mitigate with explicit "transcribe carefully + cross-check" steps and a human confirm-gate as backstop.

## Two-Tier Attribution: Capability vs Architecture

The weak-executor eval above asks "is the skill under-specified?". The same harness answers a
second, higher-leverage question: **"is this even a model problem?"**

Run the identical inputs through **both** a weak and a strong model, with all state mutations
stripped, then sort each symptom:

| Outcome | Diagnosis | What to do |
|---|---|---|
| Strong model fixes it | Capability-shaped | Solvable by a better model, and therefore also solvable by handing the weak model a **pre-computed answer** |
| Fails identically on **both** | Policy or architecture gap | **No model upgrade will ever fix it.** Stop tuning the prompt and change the system |

That second row is the payoff. A failure that survives a large capability jump is not a prompting
problem, and no amount of rewording will move it. It is usually a missing rule, a missing input, or
an impossible ask.

### Worked example

A scheduled job summarized a team standup transcript and cross-checked it against the issue
tracker. Six symptoms all looked like "the local model is too weak". The two-tier A/B showed:

- **Capability:** the strong model attributed speakers correctly and rendered tracker links; the
  weak one did neither.
- **Architecture:** *neither* model emitted the "proposed tickets" section, against a backlog of
  commitments that had been open for over a week. That single shared failure proved it was a
  missing rule, not intelligence. It had been mis-read as a prompt problem for weeks.

The strong model also took 16m49 against the weak model's 2m32, so "just use the strong model" was
never viable for a job on a tight schedule anyway. Runtime is part of the attribution.

### The fix that follows: anything a script can decide, a script decides

Once you know which failures are architectural, the remedy is to move work out of the model until
what remains fits the cheap model:

- **Deterministic substitution** instead of "remember these 61 correction rules". A vetted
  correction applied in code always lands; asked to apply it from memory, the model produced a
  third spelling that was in neither the input nor the rule set.
- **A rule** instead of a judgment call. "Aged past threshold AND nothing filed AND nothing
  matching" is three booleans, not a decision.
- **A pre-computed join** instead of "search this haystack". Narrowing a 407-item candidate list to
  the 46 that could possibly be relevant turned an impossible question into a lookup.
- **Pre-rendered artifacts.** Emit a ready-made `link` field rather than asking the model to
  assemble `[id](url)` from two other fields. Asked to build them, it wrote one of three as plain
  text.

Result in the worked example: the weak local model went from 0 tracker links, wrong attribution and
no proposals, to **beating the strong model** (9 links vs 6) at 1/16th the runtime.

### Prompt length is itself a variable

Measured in the same exercise: a condensed prompt got the *same* weak model to apply a correction
that the full 423-line skill failed to apply. When a weak model is the production target, shrinking
the skill is a functional change, not tidying. Every instruction you can delete by moving work into
code buys back attention for the part only the model can do.

### Keep the harness

The sandbox built for the A/B is the acceptance test. Re-run it after the rebuild and require the
weak model to hit the strong model's numbers before shipping. Without that, "it feels better now" is
the only evidence you will have.

## When To Use

- Before shipping a skill that cheaper models will run in production.
- After hardening a skill, to verify the fixes actually help the weak executor (re-run and confirm the specific failure is gone).
- As a periodic regression check when a skill is edited.

## Why It Works

Capability hides defects. A strong model is a poor test harness for instruction quality precisely because it's good at filling gaps. Constraining the executor to a weaker model turns "the skill plus the model's judgment" back into "just the skill," which is what you're actually trying to evaluate.

## Related

- `continuous-improvement-skill-loop.md` — the broader PDCA loop this slots into as a CHECK step.
