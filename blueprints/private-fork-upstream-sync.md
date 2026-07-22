# Private Fork of a Public Dependency, Kept in Sync

> Vendor a public upstream tool into a **private, patchable** copy without losing the ability to pull upstream changes — using a mirror, a merge-based sync script, and a watch job that notifies instead of auto-merging.
>
> **Status:** Production-tested pattern.
>
> **Last updated:** 2026-07-22

## The Problem

You depend on an open-source tool — say a third-party MCP server, a CLI, or a library — that you need to **modify**: disable a policy check that fights your conventions, add a flag, patch a selector, carry a fix upstream hasn't merged. You also want that copy **private** (internal notes, unreleased patches, a different CI posture).

The obvious move — GitHub's **Fork** button — fails two ways at once:

1. **A native fork can't be private.** Forks of a public repo are always public, with no setting to change that. Your patches and internal CI are exposed.
2. **A one-time copy rots.** If you just clone and forget the origin, you're frozen at one commit. Upstream ships security fixes and features; you either re-clone-and-re-patch by hand (painful, error-prone) or drift into an unmaintained snapshot.

What you actually want: a private repo you can patch freely, that still knows where it came from and tells you when to catch up — **notify, don't silently auto-merge**, because a merge that touches your patched files needs a human.

## Pattern 1: Private Mirror, Not a Fork

Seed a private repo from the upstream's full history with a mirror push:

```bash
git clone --mirror https://host/upstream/repo.git
cd repo.git
# create an empty PRIVATE repo at your org first, then:
git push --mirror https://host/you/your-fork.git
```

Then work from a normal clone of *your* repo and add upstream as a read-only remote:

```bash
git clone https://host/you/your-fork.git
cd your-fork
git remote add upstream https://host/upstream/repo.git
```

You lose the native "Sync fork" button and the PR-to-upstream link — an acceptable trade for privacy and a sync path you control. Your custom patches live as **ordinary commits on `main`, on top of upstream history**, so a merge Just Works.

> **Prune the mirror.** `push --mirror` drags in *every* upstream branch and tag, and rejects `refs/pull/*` with "deny updating a hidden ref" (harmless — branches and tags still land). Immediately delete the noise down to your default branch, or the branch list becomes a graveyard of stale upstream WIP that will never update again.

## Pattern 2: Merge-Based Sync Script That Stops on Conflict

A single script is the whole update path. It fetches upstream, merges into your default branch, and **halts on conflict** — never auto-resolves, never auto-pushes:

```
1. ensure the `upstream` remote exists
2. refuse to run on a dirty working tree
3. fetch upstream
4. if already up to date -> exit quietly
5. show the incoming commits, then merge
6. clean merge   -> tell the human to review, test, and push
   conflicted    -> leave the merge in progress, explain, exit non-zero
```

Conflicts arise **only** where one of your patches touches a file upstream also changed — which is exactly the case a human must adjudicate. Keep patches minimal and the conflict surface stays near zero.

Pair the script with a **patch registry** file in the repo (a short table: *what we changed, and why*). When a conflict does land, the registry tells the resolver which local intent to preserve instead of reverse-engineering it from a diff.

## Pattern 3: Watch Job That Notifies, Not Merges

A scheduled CI job (weekly is plenty, plus a manual trigger) computes how far behind upstream you are and, when behind, opens or refreshes **one** tracking issue:

```
behind = count(HEAD..upstream/default)
if behind == 0: exit
ensure a dedicated label exists
if an open tracking issue exists: update its title + comment the new commits
else: open one, listing the incoming commits and how to sync
```

Two rules make this pleasant rather than noisy:

- **Idempotent — one issue, refreshed.** Reuse a labelled issue instead of filing a new one every week, or the tracker fills with duplicates and everyone mutes it.
- **Notify, never auto-merge on the default branch.** Auto-merging an upstream that may collide with your patches, unattended, is how a fork silently breaks. The job's job is to *raise a hand*; a human runs the sync script.

## When to Use

- You must patch a public dependency and keep the patched copy private.
- You want to track upstream — pull its fixes deliberately — without a standing re-clone-and-re-patch chore.
- The dependency is something you *run* (a server, a tool), not just import at a pinned version through a package manager. (For a pinned library, a lockfile bump is simpler; reach for this when you need to change the source.)

## Anti-Patterns

- **Using the native Fork for something that must be private.** It can't be, and you'll notice only after pushing internal patches.
- **Clone-and-forget.** No `upstream` remote means no path back; you've adopted an orphan.
- **Auto-merging upstream unattended.** The one time it conflicts with a patch, it breaks at 3 a.m. with no one watching. Notify instead.
- **Leaving the mirror's imported branches in place.** They never update and disguise real branches; prune to your default branch on day one.
- **Undocumented patches.** A diff shows *what* changed, not *why*. Without a registry, the next upstream merge re-litigates every local decision.
- **Letting upstream CI dictate your conventions.** A mirror inherits upstream's workflows verbatim — including checks written for *their* contribution policy (commit-trailer rules, DCO gates, attribution checks). Disable the ones that fight your house style, and log the removal in the patch registry. Note that for a `pull_request` event the workflow file is read from the PR's head branch, so deleting such a workflow in the same PR stops it running for that PR.

## Related

- [`repo-to-runtime-sync.md`](repo-to-runtime-sync.md) — the *outbound* direction: syncing your repo to a runtime host. This blueprint is the *inbound* direction: syncing an upstream into your repo.
- [`branch-protection-hooks.md`](branch-protection-hooks.md), [`enforcement-hooks.md`](enforcement-hooks.md) — other git-level guardrails around a repo.
- [`write-ahead-idempotency.md`](write-ahead-idempotency.md) — the same "one durable record, refreshed idempotently" instinct applied to external side effects.
