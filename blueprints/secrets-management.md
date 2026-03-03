# Secrets Management for Claude Code Agents

> **Status:** No built-in solution exists (as of March 2026). This blueprint covers the threat model, available mitigations, and recommended patterns.
>
> **Last updated:** 2026-03-03

## Threat Model

The agent (Claude Code) is the threat. It can:

1. **Read `.env` files** — even when `.claudeignore` blocks them ([Knostic disclosure][knostic])
2. **Dump environment variables** — via `env`, `printenv`, `echo $SECRET` in bash
3. **Exfiltrate during debugging** — inject credentials into `curl` commands when troubleshooting auth errors
4. **Access any file on disk** the user's shell can access

The goal: **Application code reads secrets at runtime via `os.environ.get()`, but the agent never sees the actual values.**

## Current State of Claude Code

There is **no first-class secrets mechanism** in Claude Code today. Relevant open issues:

| Issue | Proposal | Status |
|-------|----------|--------|
| [#25053][gh-25053] | `sensitive` config — pattern-match env vars, show `*****` | Open |
| [#29910][gh-29910] | Built-in secrets manager with pluggable backends | Open (2026-03-01) |
| [#23642][gh-23642] | Native `op://` secret references in settings.json | Open |
| [#2695][gh-2695] | Zero-trust architecture with client-side detection | Open |

The official [security docs][claude-security] cover permission prompts and sandboxing but say nothing about redacting env var values from the model's context.

## Why Deny Rules Alone Are Not Enough

Deny rules are the obvious first step, but they have three fundamental problems:

### 1. Permissions are tool-scoped, not file-scoped

Each tool is a separate permission check. Denying one tool does not block another from reaching the same file.

```json
"deny": ["Read(.env)"]
```

This blocks Claude's `Read` tool. It does **not** block `Bash(cat .env)`, `Grep` searching inside `.env`, or any other tool. To protect a file, you must deny **every tool** that could reach it ([source][claude-permissions]):

```json
"deny": [
  "Read(.env)",
  "Read(.env.*)",
  "Bash(cat *.env*)",
  "Bash(head *.env*)",
  "Bash(tail *.env*)",
  "Bash(source *.env*)",
  "Bash(. .env*)"
]
```

> `Read` deny rules propagate to `Grep` and `Glob` on a "best-effort" basis per the docs — but "best effort" is not a guarantee.

### 2. Bash deny patterns are fragile

Bash deny rules match against the **command string**, not file paths. `Bash(.env)` only matches a command literally named `.env` — it does not match `cat .env`.

Even with wildcard patterns like `Bash(cat *.env*)`, the agent can bypass them:

```bash
python3 -c "print(open('.env').read())"    # not matched by cat pattern
head -c 999 .e?v                            # glob avoids literal ".env"
base64 .env | base64 -d                     # indirect read
```

The [official docs][claude-permissions] acknowledge this: Bash patterns that constrain command arguments are inherently fragile.

### 3. Deny rules have enforcement bugs

Multiple open issues report `Read` deny rules being silently ignored:

| Issue | Version | Status |
|-------|---------|--------|
| [#6699][gh-6699] | — | Open |
| [#24846][gh-24846] | — | Open |
| [#27040][gh-27040] | v2.1.49 (Feb 2026) | Open |

**Bottom line:** Use deny rules as a first layer (they cost nothing), but do not rely on them as your only defense.

---

## Options

### Option A: Bubblewrap Sandbox (Linux)

**Security: High** | **Complexity: Low** | **Platform: Linux only**

Bind-mount `/dev/null` over secret files at the OS level. The agent literally cannot read them.

```bash
bwrap \
  --ro-bind /dev/null "$PROJECT_DIR/.env" \
  --ro-bind /dev/null "$PROJECT_DIR/.env.local" \
  -- claude
```

Application code runs separately via a wrapper script that loads secrets outside the agent's process.

**Pros:** Structurally impossible to bypass. No application-level trust required.
**Cons:** Linux only. Doesn't protect env vars inherited by the shell — combine with Option D.

**Ref:** [Patrick McCanna — bubblewrap approach][bubblewrap-blog]

---

### Option B: AgentSecrets Proxy

**Security: High** | **Complexity: Medium** | **Platform: Cross-platform**

Zero-knowledge proxy that stores secrets in the OS keychain (GNOME Keyring / macOS Keychain). A localhost proxy intercepts HTTP calls and injects credentials at the transport layer. The agent only sees API responses, never credential values. Has an MCP server integration for Claude Code.

**Pros:** Architecturally sound — secrets never enter the agent's context.
**Cons:** Only protects HTTP-based secrets (API tokens sent in headers). Doesn't help with secrets used in non-HTTP contexts (e.g., database passwords in connection strings).

**Ref:** [AgentSecrets on GitHub][agentsecrets]

---

### Option C: PreToolUse Hook (Recommended)

**Security: Medium-High** | **Complexity: Medium** | **Platform: Cross-platform**

PreToolUse hooks intercept tool calls **before execution**, independently of the permission system. Unlike deny rules, hooks are not subject to the enforcement bugs documented in [#6699][gh-6699] / [#27040][gh-27040]. A hook script receives the tool call as JSON on stdin and exits with code 2 to block it (stderr is shown to the agent as the rejection reason).

Register in `.claude/settings.json` or `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash|Read|Grep|Glob",
      "hooks": [{
        "type": "command",
        "command": "scripts/hooks/protect-secrets.sh"
      }]
    }]
  }
}
```

The hook script inspects the tool input and blocks access to sensitive files (`.env*`, `*.pem`, `*.key`) and env-dumping commands (`printenv`, `env`, `set`). It operates on the actual tool input JSON, so it can inspect file paths for `Read`/`Grep`/`Glob` calls and command strings for `Bash` calls in one place.

**Why hooks are more reliable than deny rules:**
- Hooks execute as an external process — not subject to Claude Code's permission-matching bugs
- A single hook covers all tools (Read, Bash, Grep, Glob) with file-scoped logic
- The hook sees the full command/path, enabling regex matching instead of fragile glob patterns
- Exit code 2 is a hard block — the tool call never executes

**Cons:** Must anticipate access patterns. Deny-list approach (block known-bad) is inherently weaker than allow-list. Adds ~50ms latency per tool call.

**Ref:** [cc-filter on GitHub][cc-filter] (full implementation), [Claude Code hooks docs][claude-hooks]

---

### Option D: Wrapper Script + Deny Rules

**Security: Medium** | **Complexity: Low** | **Platform: Cross-platform**

Secrets stored in a CLI-accessible password manager. A wrapper script loads them and execs the Python tool. Claude Code never runs the wrapper — the user does.

```bash
#!/bin/bash
# scripts/run-with-secrets.sh — user runs this, NOT the agent

# Example: Bitwarden CLI
export API_TOKEN=$(bw get password "my-api-token")

# Example: 1Password CLI
export API_TOKEN=$(op read "op://Vault/Item/token")

exec .venv/bin/python "$@"
```

Combined with deny rules in `.claude/settings.json`:

```json
{
  "permissions": {
    "deny": [
      "Read(.env*)",
      "Bash(cat *env*)",
      "Bash(printenv*)",
      "Bash(env)",
      "Bash(set)"
    ]
  }
}
```

**Pros:** Simple. No extra dependencies. Password manager provides encrypted-at-rest.
**Cons:** If user launches Claude Code in the same shell after `source`-ing secrets, the agent can still read env vars via bash. Deny rules can be worked around.

**Important:** Use `exec` (not `source`) so secrets exist only in the child process, not in the shell where Claude Code runs.

---

### Option E: LLM Secrets (Encrypted .env)

**Security: Medium-High** | **Complexity: Medium** | **Platform: Windows (TPM/Hello), Linux (experimental)**

Encrypts `.env` files with AES-256-CBC using hardware-backed keys. Secrets decrypted only in isolated subprocesses at runtime. Auto-generates a `CLAUDE.md` listing secret names without values.

**Pros:** Secrets encrypted at rest with hardware keys.
**Cons:** Early-stage project. Windows-focused (TPM/Hello integration). Linux support experimental.

**Ref:** [LLM Secrets][llmsecrets]

---

### Option F: Devcontainer Isolation

**Security: High** | **Complexity: High** | **Platform: Cross-platform (Docker)**

Run Claude Code inside a purpose-built container. Secrets are NOT passed as env vars or mounted files. Application code reads secrets from a mounted Unix socket or volume at runtime, which the container's entrypoint populates but Claude Code cannot access.

**Pros:** Strongest official Anthropic recommendation. Full filesystem + network isolation.
**Cons:** Docker overhead. Slower iteration. Complex setup.

**Ref:** [Claude Code devcontainer docs][claude-devcontainer], [Trail of Bits devcontainer][trailofbits]

---

## Recommendation

**Layered defense.** No single mechanism is sufficient today.

| Layer | Mechanism | What it blocks | Reliability |
|-------|-----------|----------------|-------------|
| 1 | Deny rules in settings.json | Casual reads of `.env`, `printenv` | Low — has enforcement bugs |
| 2 | PreToolUse hook script | All tool-based access to secret files | High — external process, not subject to permission bugs |
| 3 | Remove `load_dotenv()` from code | Agent-triggered `.env` reads during import | High — structural |
| 4 | Wrapper script with `exec` | Secrets only in child process, never in agent's shell | High — structural |
| 5 | Bubblewrap (optional, Linux) | OS-level `.env` file access | Highest — kernel enforcement |

**Minimum viable setup:** Layers 1 + 2 + 3 + 4. Add 5 for maximum assurance on Linux.

### What to do today

1. Add deny rules to settings.json — cheap first layer, even if imperfect
2. Add a PreToolUse hook script — the most reliable application-level defense
3. Remove `load_dotenv()` / equivalent from application code — read `os.environ` only
4. Store secrets in a CLI-accessible password manager (`pass`, `bw`, `op`, etc.)
5. Create a wrapper script that loads secrets via CLI and `exec`s the application
6. Never `source` secrets into the shell where Claude Code runs

### What to watch for

- **[#25053][gh-25053]** — if `sensitive` config ships, it replaces layers 1 + 4 with a built-in solution
- **[#29910][gh-29910]** — full secrets manager would make this blueprint obsolete

---

## Cross-References

- [best-practices.md § 2. Security & Privacy](best-practices.md) — convention checklist
- [best-practices.md § 3. Configuration](best-practices.md) — `.env` / config split
- Agent repos: each repo's `AGENTS.md` → Security Rules section

---

## Sources

[knostic]: https://www.knostic.ai/blog/claude-loads-secrets-without-permission "Knostic — Claude loads secrets without permission"
[claude-security]: https://code.claude.com/docs/en/security "Claude Code Security Docs"
[claude-permissions]: https://code.claude.com/docs/en/permissions "Claude Code Permissions Docs"
[claude-hooks]: https://code.claude.com/docs/en/hooks "Claude Code Hooks Docs"
[claude-devcontainer]: https://code.claude.com/docs/en/devcontainer "Claude Code Devcontainer Docs"
[gh-25053]: https://github.com/anthropics/claude-code/issues/25053 "GitHub #25053 — Mark sensitive env vars"
[gh-29910]: https://github.com/anthropics/claude-code/issues/29910 "GitHub #29910 — Built-in secrets manager"
[gh-23642]: https://github.com/anthropics/claude-code/issues/23642 "GitHub #23642 — 1Password op:// references"
[gh-2695]: https://github.com/anthropics/claude-code/issues/2695 "GitHub #2695 — Zero-trust architecture"
[gh-6699]: https://github.com/anthropics/claude-code/issues/6699 "GitHub #6699 — Deny permissions not enforced"
[gh-24846]: https://github.com/anthropics/claude-code/issues/24846 "GitHub #24846 — Read deny not enforced for .env"
[gh-27040]: https://github.com/anthropics/claude-code/issues/27040 "GitHub #27040 — Deny permissions ignored (Feb 2026)"
[bubblewrap-blog]: https://patrickmccanna.net/a-better-way-to-limit-claude-code-and-other-coding-agents-access-to-secrets/ "Patrick McCanna — Bubblewrap approach"
[agentsecrets]: https://github.com/The-17/agentsecrets "AgentSecrets — Zero-knowledge proxy"
[cc-filter]: https://github.com/wissem/cc-filter "cc-filter — Hook-based secret protection"
[llmsecrets]: https://llmsecrets.com "LLM Secrets — Encrypted .env"
[trailofbits]: https://github.com/trailofbits/claude-code-devcontainer "Trail of Bits claude-code-devcontainer"
