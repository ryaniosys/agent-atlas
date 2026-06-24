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

## When To Use

- Before shipping a skill that cheaper models will run in production.
- After hardening a skill, to verify the fixes actually help the weak executor (re-run and confirm the specific failure is gone).
- As a periodic regression check when a skill is edited.

## Why It Works

Capability hides defects. A strong model is a poor test harness for instruction quality precisely because it's good at filling gaps. Constraining the executor to a weaker model turns "the skill plus the model's judgment" back into "just the skill," which is what you're actually trying to evaluate.

## Related

- `continuous-improvement-skill-loop.md` — the broader PDCA loop this slots into as a CHECK step.
