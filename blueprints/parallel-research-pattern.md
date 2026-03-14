# Parallel Research via Background Subagents

## Pattern

When an agent needs to research N independent topics (vendors, competitors, candidates, technologies), launch N parallel background subagents rather than researching sequentially.

## Structure

```
1. Derive a MATCHING BRIEF from structured requirements
   → User confirms brief before compute is spent

2. Propose candidates in TIERS to prevent selection bias
   → Primary (strong expected fit), Benchmark (expected by stakeholders), Challenger (dark horse)

3. Launch N PARALLEL BACKGROUND SUBAGENTS
   → One per research target
   → Each gets: matching brief + output template + output path
   → All run concurrently via run_in_background: true

4. VALIDATE outputs for consistency
   → Check required frontmatter fields
   → Check required section headers
   → Flag outliers (poor fit, missing data)

5. Present SUMMARY TABLE to user
```

## Key Design Decisions

### Subagent per target, not one big pass
Each target gets its own focused context window. Parallel execution is 5-8x faster than sequential and produces more consistent output because the agent doesn't conflate targets.

### Matching brief as confirmation gate
Forces user validation of selection criteria before burning compute on N parallel agents. Prevents researching against wrong criteria.

### Prescriptive output templates
Without exact section headers in the subagent prompt, agents produce inconsistent structures that break downstream parsing. Specify verbatim headers (e.g., `## Company Overview`, not "a section about the company").

### Tier classification
Ensures results include obvious choices AND alternatives. Prevents groupthink and gives stakeholders the "we considered X" defensibility.

### Soft cap on parallelism
7-8 targets is a practical sweet spot. Beyond that, the synthesis step becomes unwieldy and the marginal research value drops.

## Subagent Configuration

```
Agent type: voicemode:papa-bear (thorough research model)
Execution: run_in_background: true
Output: One file per target in a shared output directory
Duration: ~5-7 minutes per target (web search heavy)
```

**Gotcha:** Subagent types must be fully qualified (e.g., `voicemode:papa-bear`, not just `papa-bear`).

## When to Use

- Vendor/competitor research (ERP selection, market analysis)
- Candidate background research (hiring, freelancer vetting)
- Technology evaluation (framework comparison, tool selection)
- Any N-of research where targets are independent and output structure is standardized

## When NOT to Use

- Sequential dependencies between research targets
- Small N (1-2 targets): overhead of parallel setup not worth it
- Exploratory research where you don't know the targets yet

## Anti-Patterns

- **No matching brief**: Researching without structured criteria leads to inconsistent, unfocused profiles
- **Loose output templates**: "Write about the company" produces wildly different structures. Be prescriptive.
- **No validation step**: Subagents can fail silently (empty sections, missing frontmatter). Always validate.
- **Mixing research and scoring**: Research populates a knowledge base (reusable). Scoring evaluates against specific requirements (per-engagement). Keep them separate.

## Reference Implementation

- erp-selector: `/erp-vendor-research` skill
- Solution doc: `docs/solutions/workflow-patterns/parallel-vendor-research-pattern.md`
