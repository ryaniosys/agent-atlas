# Enforcement Hooks

> **Status:** Production-ready pattern, deployed globally.
>
> **Last updated:** 2026-07-29

## Purpose

PreToolUse hooks that enforce workflow constraints the agent might otherwise ignore. Unlike advisory instructions in CLAUDE.md (which the agent can override), hooks execute as external processes and provide hard blocks — the tool call never runs.

> **Runtime caveat, added 2026-07-29.** "Hooks are hard blocks" is a property of the *runtime*, not of
> hooks as an idea. Before relying on a hook as a boundary on any other agent runtime, read
> [Verify the Failure Mode](#verify-the-failure-mode-before-trusting-a-hook-as-a-boundary). On at least
> one other runtime the equivalent hook can block, but **fails open**.

## Why Instructions Alone Aren't Enough

| Layer | Mechanism | Reliability |
|-------|-----------|-------------|
| CLAUDE.md instruction | "Do NOT use EnterPlanMode" | Advisory — agent may ignore under pressure |
| Deny rule in settings.json | `"deny": ["Write(.claude/plans/*)"]` | Medium — only blocks one tool, fragile patterns |
| PreToolUse hook | External process, exit code 2 = hard block | High — tool call never executes |

Instructions are "trust me bro" — they work most of the time but break under edge cases, long conversations, or conflicting system prompts. Hooks are structural enforcement.

## Pattern: PreToolUse Blocker

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash path/to/hook.sh"
          }
        ]
      }
    ]
  }
}
```

The hook script receives tool input as JSON on stdin. Exit codes:
- `0` — allow the tool call
- `2` — block (stderr shown to the agent as the rejection reason)

## Example: Block Writes to a Directory

Prevent the agent from writing plan files to `.claude/plans/` (plans should go in the repo's `plans/` directory instead):

```bash
#!/bin/bash
INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

case "$TOOL" in
  Write|Edit)
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
    ;;
  Bash)
    CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
    if echo "$CMD" | grep -qE '(cat\s*>|echo\s.*>|tee\s|cp\s|mv\s|mkdir\s).*\.claude/plans/'; then
      echo "Blocked: write to .claude/plans/. Use plans/ in the repo instead." >&2
      exit 2
    fi
    exit 0
    ;;
esac

if echo "$FILE_PATH" | grep -qE '\.claude/plans/'; then
  echo "Blocked: write to .claude/plans/. Use plans/ in the repo instead." >&2
  exit 2
fi
exit 0
```

## Pattern: Guarding the Hook Config Itself

Everything above treats `settings.json` as the place you *write* enforcement. It is also a target.

Agent tooling commonly installs itself by writing `PreToolUse` / `UserPromptSubmit` / `Stop` entries
into `.claude/settings.json`, usually leaving a `settings.json.bak` beside it. That is ordinary
behaviour for a CLI that wants to hook the agent loop. It becomes a problem when the file is
**committed**, because a hook is arbitrary code execution and the file ships to every clone: an
entry written on one machine runs on every machine that pulls.

The enforcement therefore cannot live in `settings.json`, and it cannot be a PreToolUse hook either
(the write may happen outside any agent turn, at tool-install or session-boot time). It has to sit
where the change is published, which is a git hook:

```bash
# .githooks/pre-commit
if git diff --cached --name-only --diff-filter=ACMR | grep -qx ".claude/settings.json"; then
  has_hooks=$(git show ":.claude/settings.json" 2>/dev/null | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(2)          # unparseable: let the textual fallback decide
print("yes" if isinstance(data, dict) and data.get("hooks") else "no")
' 2>/dev/null)

  # python3 missing, or a truncated write. Fall back rather than waving it through.
  if [ -z "$has_hooks" ]; then
    git show ":.claude/settings.json" 2>/dev/null |
      grep -qE '"(hooks|PreToolUse|UserPromptSubmit|Stop)"' && has_hooks=yes
  fi

  [ "$has_hooks" = "yes" ] && { echo "Blocked: hooks in a committed settings.json." >&2; exit 1; }
fi
```

This works because session hooks belong in `.claude/hooks.json`. Keeping the two files separate is
what makes the rule unambiguous: a `hooks` key in `settings.json` is then always either injection or
a mistake, never a legitimate config.

Three things this pattern depends on, each of which has been observed failing in practice:

1. **Do not gitignore the `.bak`.** It appearing as untracked in `git status` is often the only
   visible signal that something rewrote your settings. Block committing it; do not hide it.
2. **Do not let an optional config short-circuit the hook.** A pre-commit that opens with
   `[ -f "$DENY_FILE" ] || exit 0` makes every later check inert whenever that file is absent, which
   is the default state on a fresh clone. Guard the optional block with `if`, do not exit.
3. **A committed hook file is not a running hook.** `.githooks/` is inert until wired
   (`git config core.hooksPath .githooks`, or a per-hook symlink into `.git/hooks/`). Verify by
   running it, not by reading it: a hook that was never wired can sit in a repo for months looking
   like protection.

Prefer per-hook symlinks over `core.hooksPath` when the repo also ships hooks that are
machine-specific (a deploy `post-merge`, a checkout-time indexer), since `core.hooksPath` activates
the whole directory on every clone.

## When to Use This Pattern

- **Workflow enforcement** — redirect the agent away from bad habits (wrong directories, wrong tools, wrong commands)
- **Safety rails** — block destructive operations the agent shouldn't perform (see also [secrets-management.md](secrets-management.md) for secret file protection)
- **Convention compliance** — enforce repo conventions that the agent tends to violate

## Verify the Failure Mode Before Trusting a Hook as a Boundary

A hook is only a boundary if it denies when it breaks. That is a per-runtime property, and it is worth
checking before you design around it, because the failure is invisible: nothing errors, the guarded
action simply happens.

Ask four questions of any runtime's hook system:

| Question | Why it decides the design |
|---|---|
| **What happens on crash, non-zero exit, or timeout?** | Fail-closed means the hook is a boundary. **Fail-open means it is a smoke detector.** One runtime documents exactly this: malformed output, non-zero exit codes and timeouts "log a warning but never abort the agent loop" |
| **Which tools does it actually see?** | A matcher on file-write tools is bypassed entirely by a shell tool running `cp`, `mv`, `sed -i` or `rm`. If the runtime's shell tool runs as the same OS user, path-based write guards do not constrain it |
| **Is consent bound to the script's contents or its path?** | If the allowlist keys on the command *string* rather than a content hash, an approved guard script can be edited afterwards and stays approved |
| **Does the same guard apply to sub-agents and scheduled runs?** | Hook config often lives per-profile. A delegated worker or cron job may run without it |

Contrast with the sibling mechanism on the same runtime: its *approval* system fails **closed to deny**
on timeout, and defaults scheduled jobs to deny. Same product, opposite failure direction. Do not
generalise from one subsystem to another.

## Put the Boundary Outside What It Protects

The design rule that follows. A hook running inside the agent's own process, configured in a file the
agent can read and reach, guarding that agent, sits **inside the blast radius**.

```
what actually holds            what only advises
──────────────────             ─────────────────
kernel (ro mount, container)   pre-tool-call hook
  fails closed                   may fail open
  covers every syscall           covers some tools
  agent cannot edit it           config is in reach
```

So:

- **Irreversible or destructive scope → put it where the agent cannot reach.** Read-only mount flags,
  a container, a separate host, a credential that simply lacks the permission. One runtime's own docs
  say its filesystem guards are "defense-in-depth, not a hard boundary" and point at containers for
  real isolation.
- **Rules the filesystem cannot express → hooks are the right tool**, accepting they are advisory.
  "Content read from this path must not be sent to a third-party model" has no kernel equivalent.
- **Pair a fail-open hook with an audit trail.** If you cannot reliably prevent, at least record, so
  the gap is visible after the fact instead of never.

The same reasoning applies to prose guards: a prohibition written inside the skill that implements the
safe path only reaches an agent already doing the right thing. Prohibitions belong in the always-loaded
conduct doc; procedures belong in the skill. See
[constraint-not-preference.md](constraint-not-preference.md).

## Design Considerations

1. **Keep hooks fast** — they run on every matched tool call. Target <50ms.
2. **Be specific in Bash matching** — broad regex on Bash commands causes false positives. Match write-like commands (`cat >`, `tee`, `cp`, `mv`) rather than any mention of a path.
3. **Stderr is the feedback channel** — the message in stderr is shown to the agent. Make it actionable: say what's blocked AND what to do instead.
4. **Layer with instructions** — hooks catch violations, but a CLAUDE.md instruction prevents the agent from even attempting the blocked action most of the time. Use both.

## Cross-References

- [secrets-management.md](secrets-management.md) — PreToolUse hooks for secret file protection (same pattern, different use case)
- [branch-protection-hooks.md](branch-protection-hooks.md) — git pre-push hooks (related but different: git hooks vs Claude Code hooks). See also "Guarding the Hook Config Itself" above, where a git hook is the *only* workable enforcement point
- [best-practices.md](best-practices.md) — Convention #2 (Security & Privacy)
