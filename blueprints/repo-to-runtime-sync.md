# Repo-to-Runtime Sync & Self-Healing Deploy

> Keep a repo as the single source of truth for tooling that a long-running agent runtime executes, and make the deploy path self-healing so drift and upgrades cannot silently break it.
>
> **Status:** Production-tested pattern.
>
> **Last updated:** 2026-07-20

## The Problem

An agent runtime — a gateway or daemon that schedules jobs and runs agent sessions — executes helper scripts and skills from runtime directories it discovers at startup, not from your repo. The repo is where you edit, review, and version; the runtime dir is what actually runs. Bridging the two by hand ("copy the file to the host after every change") drifts immediately: someone forgets, someone hot-edits the deployed copy, an upgrade wipes it.

Four failure modes recur:

1. **Deploy drift** — repo and runtime copy diverge; nobody knows which is real.
2. **Lost hot-fixes** — a fix made directly on the runtime is overwritten on the next deploy.
3. **Upgrades silently drop optional deps** — a runtime that lazy-installs optional integrations reinstalls "lean" on upgrade, and a component that only loads its dependency at startup gets *disabled* instead of repaired.
4. **Agent-invoked subprocesses miss their env** — scheduled jobs that run through a wrapper get their secrets sourced; the same script invoked *by an agent* does not, because the runtime does not export secrets into the OS environment.

The four patterns below address these in order.

## Pattern 1: Pull-to-Deploy Sync Hook

Put a `post-merge` git hook in the repo (enabled with `core.hooksPath`). On every `git pull` on the runtime host, it copies the repo's tooling into the runtime's discovery dirs. Properties that make it safe to ship to *every* checkout of the repo:

- **Additive, never destructive.** No `--delete`. Runtime-only files (state, secrets, virtualenvs, a skill authored directly on the host) are never removed.
- **Drift-backed-up, not clobbered.** If a deployed copy differs from the repo (a hot-edit), back it up to a timestamped path and warn before overwriting — so a host experiment is never silently lost.
- **No-op off-host.** Guard on the discovery dir existing, so laptops and CI that pull the same repo do nothing.
- **Structure-preserving** for nested assets (a skill directory plus its `references/` travel together).

Deploy becomes: merge PR → `git pull` on the host. No manual copy.

> **Why a hook and not a symlink?** Many runtimes reject symlinked tooling — they resolve the link and refuse a target outside the discovery dir as path traversal. Real copies plus a sync hook sidesteps that while keeping the repo authoritative.

## Pattern 2: Self-Healing PATH Stubs

Some synced scripts must be runnable by name from `$PATH`, but the discovery dir is not on `$PATH`. Do **not** copy the script into a `$PATH` dir — that copy is not hook-updated and will drift. Instead, have the hook create a **stable stub** that `exec`s the synced file:

```bash
#!/usr/bin/env bash
exec bash "$RUNTIME_DIR/tool.sh" "$@"
```

Write it idempotently (only when missing or wrong). A fresh host or a wiped `$PATH` dir now self-heals on the next pull, while the tool's logic still updates through the synced file. The stub never changes; the pointer target does.

## Pattern 3: Upgrade Wrapper That Preserves Optional Extras

If the runtime is installed from a package that adopted a lazy-install model, its updater installs the base lean and expects optional integrations (a chat-platform adapter, a vision backend, a search provider) to install on demand. But if a component checks its dependency only at **startup** and *disables itself* on a missing import — instead of triggering the lazy install — a version bump silently kills that integration. It looks fine until the next time that integration is needed, hours later.

Do not run the bare updater. Wrap it:

```
1. run the real update
2. reinstall the extras THIS host relies on
   (via the package's own extras, so version pins track the installed version)
3. restart the services
4. verify the integration actually loaded — fail loud if not
```

Route every upgrade through the wrapper, and add each optional extra the host depends on to its list. This converts a silent "why did delivery stop?" into a loud failure at upgrade time, at the one moment someone is watching.

## Pattern 4: Agent-Invoked Scripts Self-Load Their Env

A subtle asymmetry catches teams that mix scheduled and agent-driven execution:

- A **scheduled** job usually runs through a wrapper script that sources the runtime's env file, so it has its secrets.
- The **same** script invoked *by an agent* (the agent shells out to it) has **no** wrapper — and the runtime typically does **not** export its env file into the OS process environment.

So the agent's subprocess is missing `SOME_API_KEY` and fails, even though the identical command works from a scheduled job.

**Rule:** any script an agent may invoke must **self-load its own config** — read the runtime's env file itself when the key is absent from the environment, never overriding an already-set var, and no-op if the file is missing (so it stays portable to CI and dev machines).

This class of bug hides well: it only fires on the code path that actually needs the secret. A smoke test that exits early ("nothing to do right now") never reaches it. **Test the path that uses the secret, with the secret stripped from the environment** — that is the only test that would have caught it.

## When to Use

- You deploy tooling to a long-running host (an agent gateway, a scheduler, an edge box) and want the repo to stay the source of truth without manual copies.
- Your runtime lazy-installs optional integrations and you have been bitten — or want to avoid being bitten — by an upgrade dropping one.
- You have both scheduled (wrapped) and agent-invoked (unwrapped) entry points into the same scripts.

## Anti-Patterns

- **Symlinking the discovery dir at the repo.** Convenient, but many runtimes reject symlinked tooling, and it couples the runtime's lifecycle to your checkout's location.
- **A destructive mirror (`rsync --delete`).** Deletes host-only state and any legitimately host-authored asset. Prefer additive + drift-backup.
- **Copying `$PATH` entry-points instead of stubbing them.** They fall out of sync the moment the logic changes.
- **Trusting lazy-install to backfill an optional dep after an upgrade.** It only backfills if something reaches the `ensure`/install call at runtime; a startup check that disables the component never gets there.

## Related

- [`write-ahead-idempotency.md`](write-ahead-idempotency.md) — the same "back up before you overwrite, make retries safe" instinct applied to external API calls.
- [`branch-protection-hooks.md`](branch-protection-hooks.md), [`enforcement-hooks.md`](enforcement-hooks.md) — other git-hook-based guardrails.
- [`agent-reliability.md`](agent-reliability.md) — why the deterministic scaffolding around an agent (deploy, env, verification) is where reliability is won or lost.
