# Scoring-Model Outcome Validation Blueprint

> Before you trust a heuristic scoring or prioritization model (lead-fit / ICP scoring, ticket priority, risk ranking), **test it against real labeled outcomes** — and know the traps that make a good model look useless (and a useless one look fine).

## The core move

A scoring model assigns a number from attributes. To validate it, join scored entities to their **historical outcomes** and ask whether the score actually separates the good from the bad:

- **Score distribution by outcome** — do "success" entities score higher than "failure" ones?
- **Success-rate by score tier** — bucket by score; is `success / (success + failure)` monotonically higher in higher tiers?
- **Gate-failure rate by outcome** — for hard filters, how many successes did the gates exclude (too strict) vs how many failures they caught (working)?

Simple, cheap, and it turns "we think this is our ideal profile" into evidence.

## The interpretation traps

A flat or noisy result does **not** automatically mean the model is wrong. Four traps produce a misleading read:

### 1. Range restriction

If the population you're testing on was **already filtered by the model** (or a proxy of it), the surviving entities have little variance on the model's dimensions, so the score looks flat across outcomes. This is not evidence the model fails to discriminate — the test is simply under-powered. Example: scoring your *existing* pipeline when leads only enter the pipeline if they already fit. Validate on the **unfiltered top-of-funnel** instead, where the attributes actually vary.

### 2. Missing signal columns

If the model's highest-weighted dimensions **aren't recorded in the data**, the score is computed from the low-variance leftovers and can't discriminate — regardless of how good the model is on paper.

> A score cannot discriminate on variables it cannot see.

The fix is not to re-tune weights; it's to **instrument the missing fields** first, then re-test. A flat result here is a data-collection finding, not a model finding.

### 3. Gates vs. composite

Separate the **hard gates** (pass/fail filters) from the **fine-grained composite** (weighted 0–100). They validate independently and often disagree:

- Gates can validate cleanly — e.g. *never* excluded a success, *did* catch some failures — which justifies keeping them as-is.
- The composite can still fail to separate outcomes (for reasons 1 and 2 above).

Report them separately. "The gates are sound, the composite is unproven on this data" is a common and honest conclusion.

### 4. It's a filter, not a predictor

A fit model predicts **who to pursue**, not **whether you succeed**. High-fit entities will still fail for reasons the attributes don't capture (timing, budget, competition, champion). A pile of high-score failures is *fit ≠ conversion*, not a broken model. Don't expect a targeting score to double as an outcome-probability model.

## Detection

You're likely hitting a trap (not a real failure) when:

- Mean score is nearly identical across outcome classes **and** the test population was pre-filtered by the model (trap 1).
- The model's named top differentiators are absent from the dataset's columns (trap 2).
- The gates separate outcomes cleanly but the composite doesn't (trap 3 — report both).

## Checklist

- [ ] Join scored entities to **real historical outcomes**, not proxies.
- [ ] Report **three** views: score distribution by outcome, success-rate by tier, gate-failure rate by outcome.
- [ ] Check for **range restriction** — was this population already filtered by the model? If so, re-test on the unfiltered funnel.
- [ ] Check for **missing signal columns** — are the top-weighted dimensions actually recorded? Instrument them before blaming the model.
- [ ] Validate **gates and composite separately**; they can pass/fail independently.
- [ ] Treat the model as a **targeting filter**, not an outcome predictor; expect high-fit failures.
- [ ] Output aggregates only when the underlying records are sensitive; never persist raw entity data from the validation run.

## Related

- [eval-harness-fidelity.md](eval-harness-fidelity.md) — validating an *LLM pipeline* against independent models (a different eval flavor).
- [ground-truth-qa-eyeball.md](ground-truth-qa-eyeball.md) — building the labeled ground truth this validation joins against.
