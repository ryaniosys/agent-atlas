# Agent Repo Best Practices Blueprint

> Living document. Updated each `/snapshot` cycle.
> Starter repo: [`ryaniosys/template-agent`](https://github.com/ryaniosys/template-agent)

## How to Use This Document

- **New repos:** Clone `template-agent`, follow its README setup guide
- **Existing repos:** Audit against the checklist below
- **Monthly:** Review during agent-atlas `/snapshot` cycle, update audit matrix
- **After corrections:** If a pattern emerges from `tasks/lessons.md` across multiple repos, promote it here

---

## Conventions

### 1. Instruction Architecture

- [ ] `CLAUDE.md` is a one-liner `@AGENTS.md` redirect — never put content here
- [ ] `AGENTS.md` is the primary agent instruction doc (loaded into context every session)
- [ ] `README.md` is the human-facing doc (setup, rationale, references)
- [ ] Two audiences, two files: `README.md` for humans, `AGENTS.md` for agents
- [ ] Progressive disclosure: `AGENTS.md` → `instructions/*.md` → `docs/solutions/*`
- [ ] `PRD.md` for product vision, capability map, and roadmap

**Why:** Agents and humans need different things. Agents need lean, structured instructions optimized for context windows. Humans need rationale, design decisions, setup guides, and external references. Mixing the two wastes context tokens on content the agent doesn't need, or leaves humans without the "why". The `CLAUDE.md` file is strictly a hook — `@AGENTS.md` redirect, nothing else.

**Template ref:** `CLAUDE.md`, `AGENTS.md`, `README.md`, `PRD.md`, `instructions/`

**Refs:** [Claude Code Settings](https://code.claude.com/docs/en/settings) (official settings hierarchy)

**Origin:** personal-agent (2025-Q3), adopted across all repos by 2025-Q4. Two-audience split formalized in template-agent (2026-03).

---

### 2. Security & Privacy

- [ ] `.claude/settings.json` hard-denies `.env` file reads
- [ ] `AGENTS.md` includes "NEVER read .env" instruction (defense in depth)
- [ ] `.gitignore` blocks secrets, customer data, local configs
- [ ] Three-tier data boundary: committed (anonymized) / gitignored / never-leave-machine
- [ ] Anonymization patterns documented for committed files

**Why:** Advisory instructions in AGENTS.md can be overridden by the agent. `settings.json` provides actual enforcement. The three-tier model prevents accidental data leaks at each level.

**Template ref:** `.claude/settings.json`, `.gitignore`

**Origin:** personal-agent credential incident (2025-Q4). Hardened after teaching-agent also leaked a Moodle token.

---

### 3. Configuration

- [ ] `config.template.yaml` committed as documented schema
- [ ] `config.local.yaml` gitignored for user-specific values
- [ ] `.env.example` committed with placeholder values
- [ ] `.env` gitignored
- [ ] All user-specific paths parametrized via AGENTS.md `## Configuration` section

**Why:** Keeps repo portable across machines and users. Skills read paths from AGENTS.md, never hardcode them.

**Template ref:** `config.template.yaml`, `.env.example`

**Origin:** personal-agent (2025-Q3). cfo-agent and cso-agent adopted same pattern.

---

### 4. Skills

- [ ] Located at `.claude/skills/{name}/SKILL.md` (not `skills/`)
- [ ] YAML frontmatter: `name`, `description`
- [ ] Standard sections: Triggers, Context Sources, Workflow, Output, Guidelines, Anti-Patterns
- [ ] Agent-native: explicit tool names, prerequisite checks, async waits
- [ ] Registered in AGENTS.md skills table
- [ ] Supporting files in `.claude/skills/{name}/scripts/` or `.claude/skills/{name}/templates/`

**Why:** `.claude/skills/` is the Claude Code convention for slash commands. YAML frontmatter enables discovery. Agent-native authoring prevents silent failures when an LLM executes the skill.

**Template ref:** `.claude/skills/example-skill/SKILL.md`

**Checklist:** See `personal-agent/docs/solutions/skill-creation/agent-native-skill-authoring-checklist.md`

**Origin:** Ecosystem-wide from initial setup. Agent-native checklist added after `/book-event` skill failures (2026-02).

---

### 5. Python Execution

- [ ] `scripts/run_in_venv.sh` for consistent venv management
- [ ] Venv in `/tmp/{repo-name}-venv` (not project-local)
- [ ] `requirements.txt` in `scripts/`
- [ ] Scripts source `.env` explicitly when needed

**Why:** Shared venv avoids per-script setup. `/tmp` location keeps the repo clean and avoids `.gitignore` bloat. Auto-installs deps on first run.

**Template ref:** `scripts/run_in_venv.sh`

**Known tension:** cfo-agent uses project-local `.venv` with `uv` instead. Consider standardizing.

**Origin:** personal-agent (2025-Q3). Generalized in template-agent.

---

### 6. Knowledge Base

- [ ] `docs/solutions/{category}/{slug}.md` pattern
- [ ] Categories: `integration-issues/`, `integration-patterns/`, `workflow-patterns/`, `skill-creation/`
- [ ] Each doc: problem → investigation → root cause → solution → gotchas
- [ ] Cross-referenced from AGENTS.md where relevant

**Why:** Captures institutional knowledge. Prevents solving the same problem twice. Structured format makes docs discoverable by agents.

**Template ref:** `docs/solutions/README.md`

**Origin:** personal-agent (~80 solution docs). No other repo has adopted this yet — biggest compliance gap.

---

### 7. Task Tracking

- [ ] `tasks/lessons.md` for self-improvement loop
- [ ] `plans/` gitignored for ephemeral planning

**Why:** The self-improvement loop (use → observe friction → refine → document) is what makes agent repos get better over time. `lessons.md` is the persistence layer for this loop.

**Template ref:** `tasks/lessons.md`, `plans/`

**Origin:** personal-agent (2025-Q4). Adopted by cfo-agent, cso-agent.

---

### 8. Git & Commits

- [ ] Conventional commits: `type(scope): description`
- [ ] Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`
- [ ] Never commit: API keys, `.env` files, customer data, business metrics
- [ ] Commit and push after every change (unless told otherwise)

**Why:** Consistency across repos. Conventional commits enable automated changelogs. Branch prefixes make PRs scannable.

**Template ref:** AGENTS.md → Git Workflow section

**Origin:** Ecosystem-wide standard from `~/CLAUDE.md`.

---

### 9. MCP Integration

- [ ] `.mcp.json` for server config (committed, no secrets)
- [ ] `.env.mcp` for MCP secrets (gitignored)
- [ ] `.env.mcp.template` or docs listing required env vars
- [ ] MCP servers documented in AGENTS.md table

**Why:** MCP config is code (committed). Secrets are separate (gitignored). The table in AGENTS.md makes it scannable.

**Template ref:** Create `.mcp.json` when needed (not included in template by default).

**Origin:** personal-agent, teaching-agent.

---

### 10. Documentation Hygiene

- [ ] Shard markdown files >300 lines by time period
- [ ] Keep AGENTS.md agnostic — general patterns, not specific cases
- [ ] Update after corrections (don't repeat mistakes)
- [ ] `README.md` for humans: setup guides, design rationale, external references
- [ ] `AGENTS.md` for agents: lean structured instructions, reference tables, paths
- [ ] Never duplicate content between the two — link instead

**Why:** Long files get truncated in context windows. Sharding keeps content accessible. The two-audience split (see also Convention #1) ensures agents get lean context while humans get the "why" and setup instructions they need.

**Template ref:** AGENTS.md → Updating Documentation section, `README.md`

**Origin:** personal-agent AGENTS.md grew past 500 lines (2026-01). Sharding pattern documented in `docs/solutions/workflow-patterns/markdown-file-sharding.md`. Two-audience split formalized in template-agent (2026-03).

---

### 11. Agent-Native Design

- [ ] **Action Parity:** anything a user can do, the agent can do
- [ ] **CRUD Completeness:** create, read, update, delete for all entities
- [ ] **Context Injection:** agent can access all relevant context
- [ ] **Tools as Primitives:** no business logic in data-access layers
- [ ] **Prompt-Native:** reasoning lives in SKILL.md, not in code

**Why:** The agent is the primary user of these repos. If the agent can't execute a workflow without human intervention, the skill is incomplete.

**Template ref:** Example skill follows these principles.

**Audit framework:** See personal-agent `/compound-engineering:agent-native-audit` skill for formal scoring.

**Origin:** Formalized in agent-atlas v1.0 (2026-02). Emerged from observing which skills succeed vs. fail in autonomous execution.

---

## Repo Audit Matrix

| # | Convention | personal-agent | cso-agent | cfo-agent | content-creator | teaching-agent | optiverser |
|---|-----------|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | Instruction arch | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| 2 | Security | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| 3 | Configuration | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 4 | Skills | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| 5 | Python exec | ✅ | ✅ | ⚠️ | ❌ | ❌ | ✅ |
| 6 | Knowledge base | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 7 | Task tracking | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 8 | Git & commits | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9 | MCP integration | ✅ | N/A | N/A | N/A | ✅ | N/A |
| 10 | Doc hygiene | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| 11 | Agent-native | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ |

**Legend:** ✅ Compliant | ⚠️ Partial | ❌ Missing | N/A Not applicable

**Last audited:** 2026-03-02

---

## Feedback Loop

```
template-agent (starter)
    ↓ new repos clone from here
agent repos (production)
    ↓ patterns emerge from use
agent-atlas (this blueprint)
    ↓ codified conventions
template-agent (updated)
    ↓ existing repos audited
agent repos (improved)
```

**Monthly cycle:**
1. `/snapshot` scans all repos quantitatively
2. Review this blueprint against scan results
3. Update audit matrix
4. Create Linear tickets (`infra` label) for compliance gaps
5. Fixes flow back as blueprint refinements → template updates
