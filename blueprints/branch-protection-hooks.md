# Branch Protection Hooks

> **Status:** Production-ready pattern, deployed across multiple repos.
>
> **Last updated:** 2026-03-07

## Purpose

A local git `pre-push` hook that blocks direct pushes to `main`, enforcing a PR-based workflow. This complements GitHub's remote branch protection rules with fast, offline feedback.

## Why Both Local Hook AND Remote Protection Matter

| Layer | Mechanism | Feedback speed | Enforcement strength |
|-------|-----------|---------------|---------------------|
| Local | `pre-push` hook | Instant (< 1s) | Advisory -- can be bypassed with `--no-verify` |
| Remote | GitHub branch protection rules | After push attempt (network round-trip) | Authoritative -- cannot be bypassed by the pusher |

**Local hooks** catch mistakes before they hit the network. The developer (or agent) gets an immediate error message with a clear instruction ("Create a PR instead"), avoiding a confusing remote rejection. This is especially valuable for Claude Code agents, which follow instructions literally -- a fast, clear rejection prevents wasted cycles.

**Remote protection** is the real enforcement. Even if someone bypasses the local hook with `--no-verify`, GitHub rejects the push. Remote rules also enforce review requirements, status checks, and other policies that local hooks cannot.

**Use both.** Local for fast feedback, remote for enforcement.

## The Hook Script

Create `scripts/hooks/pre-push`:

```bash
#!/bin/bash
# Block direct pushes to main — all changes must go through PRs.

while read local_ref local_sha remote_ref remote_sha; do
    if [ "$remote_ref" = "refs/heads/main" ]; then
        echo "ERROR: Direct push to main is blocked. Create a PR instead."
        exit 1
    fi
done
```

The script reads push info from stdin (git's pre-push protocol), checks if any ref targets `refs/heads/main`, and exits non-zero to abort the push.

## Setup Instructions

### 1. Add the hook script to the repo

```bash
mkdir -p scripts/hooks
# Create the script (content above)
chmod +x scripts/hooks/pre-push
git add scripts/hooks/pre-push
git commit -m "chore(hooks): add pre-push hook to block direct pushes to main"
```

### 2. Symlink into `.git/hooks/`

```bash
ln -sf ../../scripts/hooks/pre-push .git/hooks/pre-push
```

The symlink uses a relative path so it works regardless of where the repo is cloned. Since `.git/hooks/` is not version-controlled, each developer (or setup script) must create the symlink after cloning.

### 3. Document in AGENTS.md / CLAUDE.md

Add a note to the repo's setup instructions so new contributors know to create the symlink:

```markdown
## Setup
After cloning, enable git hooks:
```bash
ln -sf ../../scripts/hooks/pre-push .git/hooks/pre-push
```
```

### 4. (Optional) Automate symlink creation

For repos with multiple hooks, a setup script avoids manual symlink creation:

```bash
#!/bin/bash
# scripts/setup-hooks.sh
HOOKS_DIR="$(git rev-parse --show-toplevel)/.git/hooks"
SCRIPTS_DIR="$(git rev-parse --show-toplevel)/scripts/hooks"

for hook in "$SCRIPTS_DIR"/*; do
    hook_name=$(basename "$hook")
    ln -sf "../../scripts/hooks/$hook_name" "$HOOKS_DIR/$hook_name"
    echo "Linked $hook_name"
done
```

## Design Decisions

### Why `scripts/hooks/` and not `.githooks/`?

Git 2.9+ supports `core.hooksPath`, which could point to a committed `.githooks/` directory. However:

- `core.hooksPath` is a per-user git config setting -- it still requires manual setup after cloning
- Placing hooks in `scripts/hooks/` keeps them alongside other project scripts (e.g., `pre-commit` for config validation, `protect-secrets.sh` for secret protection)
- The symlink approach is explicit and works with any git version

### Why not `--no-verify` protection?

The `--no-verify` flag bypasses all local hooks by design. There is no way to prevent this locally. This is acceptable because:

- The local hook is advisory, not enforcement (that is GitHub's job)
- Blocking `--no-verify` would require OS-level controls, adding complexity for no real security gain
- Claude Code's CLAUDE.md instructions explicitly say "NEVER skip hooks (--no-verify)" -- agent compliance is instruction-based

## Repos Using This Pattern

- Financial agent repo -- `scripts/hooks/pre-push` + `scripts/hooks/pre-commit` (config validation)
- Cookiecutter template repo -- included in cookiecutter template for all new agent repos

## Cross-References

- [best-practices.md](best-practices.md) -- git workflow conventions
- [secrets-management.md](secrets-management.md) -- PreToolUse hooks (related hook pattern for security)
- Agent repos: each repo's `AGENTS.md` --> Git Workflow section
