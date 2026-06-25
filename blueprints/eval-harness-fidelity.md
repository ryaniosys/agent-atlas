# Eval-Harness Fidelity Blueprint

> When a harness evaluates a deployed system, it must reproduce the system's **full runtime input**, not just the static parts — otherwise it measures the harness's blind spots, not the system's errors.

## The Core Problem: Assembly Skew

You build a harness to find a deployed system's errors — e.g., re-running an LLM pipeline with one or more **independent** models and comparing their output to the system's. The obvious move is "use the same prompt." But most systems don't have *a* prompt; they **assemble** their model input at request time:

```
runtime input = static template
              + injected context (caller/tenant identity, retrieved docs, prior results)
              + heuristics (few-shot examples, hints)
              + tool/function results
```

If the harness feeds only the **static template**, the independent model runs with *less information than the real system*. The disagreements you surface are then **harness artifacts** — the harness's blind spots — not the system's errors. This is the eval-time analogue of train/serve skew.

### Worked example (generic)

A system extracts structured data from documents. At request time it prepends a small **context block** identifying which party is the recipient, so it can assign roles correctly (who is buyer vs seller, sender vs addressee). A benchmark re-runs extraction with two independent models but sends only the static template. The two models can't disambiguate the roles, so they **disagree and swap them** — which looks like an extraction error. In reality the deployed system, *with* its context block, gets the roles right every time. The "error" lives in the harness, not the system.

**Fix:** pull the same dynamic context the system injects (from the same config/API the system reads) and prepend it in the harness. The sharpened principle:

> "Share the system's exact prompt" → **"Share the system's exact prompt *assembly*."**

## Mirror ground-truth context; be deliberate about heuristics

Not every assembled component should be mirrored. Split them:

| Component type | Example | Mirror in harness? |
|----------------|---------|--------------------|
| **Ground-truth / identity context** | caller/tenant identity, retrieved facts, locale | **Yes** — a human evaluator would have it too; omitting it manufactures false errors |
| **Internal heuristics** | few-shot examples, frequency hints, self-conditioning | **Decide per-component** — these improve the system's *guess*, not the ground truth; mirroring them can *mask* real model weaknesses you wanted to find |
| **Tool/function results** | DB lookups, API enrichment | Mirror if deterministic and part of the real path |

Rule of thumb: **mirror what makes the answer more *correct* (and that a human ground-truther would also know); think twice about mirroring what merely makes the model more *confident*.**

## Detection

You likely have an assembly gap when:

- The harness produces many "disagreements" or "errors" that, on inspection, the **real system gets right**.
- Errors cluster on fields that depend on *context the document/input alone doesn't fully determine* (roles, units, defaults).
- A single injected block (identity, locale) would resolve a whole class of disagreements at once.

**Verification test:** before trusting a harness finding, confirm it reproduces on the *real* system. If it doesn't, the harness — not the system — is wrong.

## Checklist

- [ ] Enumerate **every** component the system assembles into its model input at runtime (read its request-building code, not just its prompt file).
- [ ] Classify each component: ground-truth/identity context (mirror) vs internal heuristic (decide).
- [ ] Pull dynamic context from the **same source** the system uses (shared config/API), not a hardcoded copy that silently drifts.
- [ ] Spot-check that harness "errors" reproduce on the real system; treat non-reproducing ones as assembly gaps, not findings.
- [ ] Document any deliberate divergence (a component you chose **not** to mirror) and why.

## Related

- [hitl-consensus-normalization.md](hitl-consensus-normalization.md) — once the harness is faithful, strip formatting noise before routing disagreements to a human.
- [tdd-wave-pattern.md](tdd-wave-pattern.md) — build the harness test-first.
