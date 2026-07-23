# Agent Review Loop

> Close the loop between a background coding agent that opens pull requests and an independent AI reviewer, so review feedback gets addressed automatically, without a human relaying it, and without the loop running forever.

## The Problem

You run two agents on your pull requests:

- an **authoring agent** — a background coding agent that picks up a task and opens a PR (e.g., an issue-tracker-driven coding agent), and
- a **reviewing agent** — an independent AI code reviewer that comments on the PR.

Independence is the point. A reviewer that shares the author's model and context rubber-stamps its own blind spots; a different vendor or model applies real adversarial pressure and catches what the author missed.

But the two rarely talk. The authoring agent is usually woken by **one** event channel (issue-tracker webhooks, an @mention), while the reviewer's feedback lands in a **different** one (version-control review events). Nothing carries the review back to the author, so the loop stalls: the reviewer comments, and the PR sits with the feedback unaddressed until a human pokes the author.

## The Pattern: relay the review into the author's trigger channel

Don't try to make the authoring agent listen on the reviewer's channel. Instead, **relay** the review event into whatever channel already wakes the author.

```
authoring agent  ──opens PR──▶  reviewer comments (version-control review event)
                                        │
                              relay  (review event → author's native trigger)
                                        │
                                        ▼
        authoring agent re-triggered ──▶ reads review, pushes fix, replies on the PR
```

The relay is small: it reacts to a review event, checks a few guards, and emits the author's native trigger (often an @mention on the tracked issue or the PR). The authoring agent then does what it already knows how to do — read the thread, push a fix, reply.

## Constraints learned the hard way

**Re-review needs auto-review-on-push, not a one-shot request.** Many reviewers let you request a review programmatically once, but a *re*-request after the first review does nothing — only a standing "review on every push" rule re-reviews subsequent commits. Without it the loop runs exactly once (review → fix → silence). Configure the reviewer to review on push, or the loop cannot iterate.

**Bound the rounds.** Reviewer → fix → re-review → fix is a genuine loop and will ping-pong. Add a **convergence cap**: after N rounds on the same PR, stop and escalate to a human. Track rounds in the relay's state, keyed per PR.

**Gate the relay.** Fire only on the *reviewer's* comments, never on human reviews — otherwise the author starts arguing with teammates. Scope to an explicit allowlist of repositories. Recognize the authoring agent's own PRs (a marker in the PR body) so the relay never chases PRs it shouldn't touch.

**Prefer event-relay over in-session babysitting.** It is tempting to keep the authoring session alive, polling its own PR until the review lands. That holds a worker/session open for the whole review cycle, dies on any restart, and does not survive the agent runtime ending its turn. A stateless relay that re-triggers a *fresh*, short-lived session is more durable and cheaper.

**Centralize the relay; don't scatter it per repo.** A per-repo CI job or webhook config drifts and must be re-added to every new repository. One relay — a scheduled poller or a single account/org-level webhook receiver — with a repo allowlist covers all repositories, present and future, from one place. A scheduled poller also avoids standing up an inbound endpoint at all (no signature/verification surface to secure) and survives restarts trivially; opt for it unless you need sub-minute latency.

## When To Use

- You have a background coding agent opening PRs and want an independent reviewer's feedback addressed without a human in the middle.
- You want author and reviewer to be different models or vendors for adversarial coverage.
- The two agents are triggered by different event systems and don't natively talk to each other.

## Anti-Patterns

- **Same model reviews its own work.** No independent pressure; it approves its own mistakes. Use a different reviewer.
- **One-shot review request expecting iteration.** Without review-on-push the loop runs once. See the constraint above.
- **No convergence cap.** The review↔fix loop churns a PR indefinitely. Always bound it and escalate to a human.
- **Per-repo relay wiring.** Drifts, and every new repo needs it re-added. Centralize with an allowlist.
- **Long-lived babysitting session.** Holds resources and dies on restart. Relay to a fresh session instead.
- **Firing on human reviews.** The author ends up arguing with teammates. Gate to the reviewer bot only.

## Related

- [`enforcement-hooks.md`](enforcement-hooks.md) — gating and guardrails at the automation layer.
- [`write-ahead-idempotency.md`](write-ahead-idempotency.md) — making re-triggered actions safe to repeat.
- [`agent-reliability.md`](agent-reliability.md) — supervision and durability for long-running agents.
