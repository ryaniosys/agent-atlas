# Enforcement Hooks

> **Status:** Production-ready pattern, deployed globally.
>
> **Last updated:** 2026-07-28

## Purpose

PreToolUse hooks that enforce workflow constraints the agent might otherwise ignore. Unlike advisory instructions in CLAUDE.md (which the agent can override), hooks execute as external processes and provide hard blocks — the tool call never runs.

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

## Design Considerations

1. **Keep hooks fast** — they run on every matched tool call. Target <50ms.
2. **Be specific in Bash matching** — broad regex on Bash commands causes false positives. Match write-like commands (`cat >`, `tee`, `cp`, `mv`) rather than any mention of a path.
3. **Stderr is the feedback channel** — the message in stderr is shown to the agent. Make it actionable: say what's blocked AND what to do instead.
4. **Layer with instructions** — hooks catch violations, but a CLAUDE.md instruction prevents the agent from even attempting the blocked action most of the time. Use both.

## Cross-References

- [secrets-management.md](secrets-management.md) — PreToolUse hooks for secret file protection (same pattern, different use case)
- [branch-protection-hooks.md](branch-protection-hooks.md) — git pre-push hooks (related but different: git hooks vs Claude Code hooks). See also "Guarding the Hook Config Itself" above, where a git hook is the *only* workable enforcement point
- [best-practices.md](best-practices.md) — Convention #2 (Security & Privacy)
