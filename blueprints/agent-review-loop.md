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

**Relay only *actionable* reviews, not every review.** A review-on-push reviewer posts a fresh review on every push, including a clean pass once the author has converged. Relaying that clean review wakes the author for nothing and burns a convergence round on an already-done PR. Classify each review before relaying: changes-requested, or carrying inline comments or a non-empty review body, is actionable and relays; approved or empty is convergence, so advance the stored review id but do not relay and do not count a round.

**Bind the PR to its tracked issue authoritatively, not from a parseable string.** To relay, the poller has to map the PR back to the issue whose trigger channel wakes the author. Deriving that from the branch name or PR body is forgeable: a crafted or accidental string can point the relay at the wrong issue and fire the agent against unrelated work. Resolve it from the tracker's own PR link (its native attachment), and treat any identifier parsed from the branch or body as a cross-check only, enforced within the same project namespace.

**Escalate on stall, not only on the round cap.** The convergence cap trips when rounds reach N, but rounds only advances when a new review arrives. If a relayed session errors, or replies without pushing, it produces no new review, so rounds never moves and a cap-only escalation never fires: the PR stalls silently below the cap with no human ever told. Record the time of each relay and escalate if a relayed round yields no new review within a bounded window, independent of the counter.

**Fail loud; a silent relay skip must not read as healthy.** If the relay reports liveness with a dead-man ping, a per-PR failure (the tracker link not present yet, an API error, an unresolved binding) must make the run exit non-zero and skip the ping, not swallow the error while the ping stays green. Otherwise a relay that quietly stopped relaying looks perfectly healthy. Separate a transient "not ready yet" (retry next tick, no alarm) from a real failure (alarm).

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
- **Relaying clean reviews.** A clean re-review is convergence, not work; relaying it burns a round and wakes the author for nothing. Classify actionable vs clean first.
- **Resolving the PR to its issue from the branch name.** Forgeable, and can misroute the agent to unrelated work. Bind via the tracker's native PR link.
- **Cap-only escalation.** A stalled or errored session never produces a new review, so a round-counter cap never trips. Add a time-based stall escalation.
- **A dead-man ping that swallows per-PR failures.** The relay looks healthy while it has quietly stopped relaying. Make a real per-PR failure fail the run loudly.

## Related

- [`enforcement-hooks.md`](enforcement-hooks.md) — gating and guardrails at the automation layer.
- [`write-ahead-idempotency.md`](write-ahead-idempotency.md) — making re-triggered actions safe to repeat.
- [`agent-reliability.md`](agent-reliability.md) — supervision and durability for long-running agents.
