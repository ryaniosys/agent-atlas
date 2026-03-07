# Enforcement Hooks

> **Status:** Production-ready pattern, deployed globally.
>
> **Last updated:** 2026-03-07

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
- [branch-protection-hooks.md](branch-protection-hooks.md) — git pre-push hooks (related but different: git hooks vs Claude Code hooks)
- [best-practices.md](best-practices.md) — Convention #2 (Security & Privacy)
