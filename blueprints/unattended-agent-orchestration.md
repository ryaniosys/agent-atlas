# Unattended Agent Orchestration Blueprint

> Designing a multi-agent pipeline that runs **unattended** (scheduled / cron) on a **small or local model**. Extends [agent-reliability.md](agent-reliability.md), which owns the general deterministic-vs-stochastic principle; this blueprint is the sharper set of rules that unattended, weak-model, multi-agent operation forces on you.

## Why "unattended + weak model" changes the rules

When a human is in the loop and the model is frontier-class, agentic multi-step tool-calling is merely *risky*. When the job runs on a schedule with no human watching, on a small local model, the same pattern is *unusable*. Small models routinely: drop required tool arguments, mangle long payloads across a tool boundary, skip a step, or fabricate data to fill a gap. One bad run in an unattended cron is a silent failure, not a retryable hiccup.

So the deterministic-shell principle stops being an optimization and becomes a hard constraint.

## Principle 1: Give the model exactly one fixed command

Push **both** the data fetch and the side-effect into a deterministic script. The script does the server-side-filtered query, the crunching, the rendering, and the write. The model's entire job is to invoke **one fixed command**.

```
Bad  (unattended, weak model):
  model: fetch records → filter → group → render → call send-tool with assembled payload
  → drops an arg / mangles the payload / invents data on some runs

Good:
  script: query (server-side filtered) → crunch → render → send
  model: run `digest.py --send`      # one command, tool_turns = 1
```

The failure mode this kills: a weak model cannot reliably transcribe a long structured payload into a tool call. Don't ask it to. If a step needs bulk data, keep the bulk data out of the model's context entirely (the script fetches it via an API key). Server-side-filter the query so the result is small and exact, rather than fetching a rotating window and filtering in the model.

## Principle 2: Split every agent into "prepare" (autonomous) vs "act" (gated)

Decompose each agent by the **reversibility of the step**, not by its measured reliability:

- **Prepare** = pure computation (fetch, score, enrich, draft). No external side-effect. Safe to run unattended on a schedule.
- **Act** = the irreversible side-effect (send, publish, post, purchase). Never fires on a bare schedule. It either surfaces to a human for one-tap approval, or defers to an interactive session.

This is a different axis from progressive autonomy (promote-by-reliability). Some acts must **never** auto-run regardless of how reliable the agent gets, because the risk isn't model error but the action's own consequences (e.g. an action that gets an account banned when taken from an unattended server, or any spend). Gate those permanently; don't let a rising reliability score unlock them.

```
Agent = prepare()            # cron-safe, autonomous
        └─► act()            # gated: human approval, or interactive-only, or never-auto
```

## Principle 3: Use a shared datastore as the hand-off bus

For a pipeline of agents, do **not** build a message bus. Use an existing shared datastore (a CRM, a database) with a **stage field** on each record. Each agent's scheduled run picks up whatever the upstream agent marked:

```
Agent A (prepare): score records → set stage = "scored"
Agent B (prepare): query stage = "scored" → enrich → set stage = "enriched"
Agent C:           query stage = "enriched" → ...
```

The datastore is simultaneously the queue, the state, and the audit log. Benefits: no new infrastructure, every hand-off is human-inspectable, and stage transitions are naturally idempotent (see [write-ahead-idempotency.md](write-ahead-idempotency.md)). A record's stage is the single source of truth for "who owns this next."

## Anti-patterns

1. **Agentic multi-step orchestration on a weak model, unattended.** The one pattern most likely to fail silently on a cron. Collapse it to one deterministic command.
2. **Auto-executing an irreversible act on a schedule.** Sends, posts, and purchases need a gate, always.
3. **Reliability-unlocking a consequence-gated act.** High reliability doesn't make a ban-risk or a spend safe to automate.
4. **Building a message bus for a handful of agents.** A stage column on the shared datastore is the queue.
5. **Fetching a broad window and filtering in the model.** Filter server-side; hand the model a small, exact result.

## Checklist

- [ ] Every scheduled agent reduces the model's job to **one fixed command**; fetch + crunch + side-effect live in a script.
- [ ] Bulk data never enters the model's context (script fetches via API key).
- [ ] Each agent is split into an autonomous `prepare` and a gated `act`.
- [ ] Acts are classified: human-approval, interactive-only, or never-auto (consequence-gated).
- [ ] Hand-offs run through a stage field on a shared datastore, not a bespoke bus.
- [ ] Queries are server-side filtered so results are small and exact.

## Related

- [agent-reliability.md](agent-reliability.md) — the general hybrid (deterministic/stochastic) principle and the determinism ladder this specializes.
- [write-ahead-idempotency.md](write-ahead-idempotency.md) — make the stage transitions and side-effects safe to re-run.
- [hitl-consensus-normalization.md](hitl-consensus-normalization.md) — patterns for the human-approval gate.
