# Agent Repo Best Practices Blueprint

> Living document. Updated each `/snapshot` cycle.
> Starter repo: `your-org/template-agent`

## How to Use This Document

- **New repos:** Clone `template-agent`, follow its README setup guide
- **Existing repos:** Audit against the checklist below
- **Monthly:** Review during agent-atlas `/snapshot` cycle, update audit matrix
- **After corrections:** If a pattern emerges from `tasks/lessons.md` across multiple repos, promote it here
- **Cross-industry:** These conventions apply equally to service-industry agents (CRM, email, content) and manufacturing agents (quality, scheduling, supply chain). Examples throughout use both domains.

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

**Origin:** Hub agent, adopted across all repos. Two-audience split formalized in template-agent.

---

### 2. Security & Privacy

- [ ] `.claude/settings.json` hard-denies `.env` file reads
- [ ] `AGENTS.md` includes "NEVER read .env" instruction (defense in depth)
- [ ] `.gitignore` blocks secrets, customer data, local configs
- [ ] Three-tier data boundary: committed (anonymized) / gitignored / never-leave-machine
- [ ] Anonymization patterns documented for committed files

**Why:** Advisory instructions in AGENTS.md can be overridden by the agent. `settings.json` provides actual enforcement. The three-tier model prevents accidental data leaks at each level.

**Template ref:** `.claude/settings.json`, `.gitignore`

**Deep dive:** [secrets-management.md](secrets-management.md) — threat model, mitigation options, and layered defense recommendations.

**Origin:** Hardened after credential leaks observed in production agents.

---

### 3. Configuration

- [ ] `config.template.yaml` committed as documented schema
- [ ] `config.local.yaml` gitignored for user-specific values
- [ ] `.env.example` committed with placeholder values
- [ ] `.env` gitignored
- [ ] All user-specific paths parametrized via AGENTS.md `## Configuration` section

**Why:** Keeps repo portable across machines and users. Skills read paths from AGENTS.md, never hardcode them.

**Template ref:** `config.template.yaml`, `.env.example`

**Origin:** Hub agent. Adopted by finance and sales agents.

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

**Checklist:** See [skill-authoring-checklist.md](skill-authoring-checklist.md).

**Reliability:** See [agent-reliability.md](agent-reliability.md) for the determinism ladder — push each skill step to the highest rung possible.

**Origin:** Ecosystem-wide from initial setup. Agent-native checklist added after skill failures in autonomous execution.

---

### 5. Python Execution

- [ ] `scripts/run_in_venv.sh` for consistent venv management
- [ ] Venv in `/tmp/{repo-name}-venv` (not project-local)
- [ ] `requirements.txt` in `scripts/`
- [ ] Scripts source `.env` explicitly when needed

**Why:** Shared venv avoids per-script setup. `/tmp` location keeps the repo clean and avoids `.gitignore` bloat. Auto-installs deps on first run.

**Template ref:** `scripts/run_in_venv.sh`

**Known tension:** Some repos use project-local `.venv` with `uv` instead. Consider standardizing.

**Origin:** Hub agent. Generalized in template-agent.

---

### 6. Knowledge Base

- [ ] `docs/solutions/{category}/{slug}.md` pattern
- [ ] Categories: `integration-issues/`, `integration-patterns/`, `workflow-patterns/`, `skill-creation/`
- [ ] Each doc: problem → investigation → root cause → solution → gotchas
- [ ] Cross-referenced from AGENTS.md where relevant

**Why:** Captures institutional knowledge. Prevents solving the same problem twice. Structured format makes docs discoverable by agents.

**Template ref:** `docs/solutions/README.md`

**Origin:** Hub agent (~80 solution docs). Biggest compliance gap across other repos.

---

### 7. Task Tracking

- [ ] `tasks/lessons.md` for self-improvement loop
- [ ] `plans/` gitignored for ephemeral planning

**Why:** The self-improvement loop (use → observe friction → refine → document) is what makes agent repos get better over time. `lessons.md` is the persistence layer for this loop.

**Template ref:** `tasks/lessons.md`, `plans/`

**Origin:** Hub agent. Adopted by finance and sales agents.

---

### 8. Git & Commits

- [ ] Conventional commits: `type(scope): description`
- [ ] Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`
- [ ] Never commit: API keys, `.env` files, customer data, business metrics
- [ ] Commit and push after every change (unless told otherwise)

**Why:** Consistency across repos. Conventional commits enable automated changelogs. Branch prefixes make PRs scannable.

**Template ref:** AGENTS.md → Git Workflow section

**Origin:** Ecosystem-wide standard.

---

### 9. MCP Integration

- [ ] `.mcp.json` for server config (committed, no secrets)
- [ ] `.env.mcp` for MCP secrets (gitignored)
- [ ] `.env.mcp.template` or docs listing required env vars
- [ ] MCP servers documented in AGENTS.md table

**Why:** MCP config is code (committed). Secrets are separate (gitignored). The table in AGENTS.md makes it scannable.

**Template ref:** Create `.mcp.json` when needed (not included in template by default).

**Origin:** Hub agent, education agent.

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

**Origin:** Hub agent AGENTS.md grew past 500 lines. Sharding pattern documented in `docs/solutions/workflow-patterns/markdown-file-sharding.md`. Two-audience split formalized in template-agent.

---

### 11. Agent-Native Design

- [ ] **Action Parity:** anything a user can do, the agent can do
- [ ] **CRUD Completeness:** create, read, update, delete for all entities
- [ ] **Context Injection:** agent can access all relevant context
- [ ] **Tools as Primitives:** no business logic in data-access layers
- [ ] **Prompt-Native:** reasoning lives in SKILL.md, not in code

**Why:** The agent is the primary user of these repos. If the agent can't execute a workflow without human intervention, the skill is incomplete.

**Template ref:** Example skill follows these principles.

**Audit framework:** Use a formal agent-native audit skill for scoring.

**Origin:** Formalized in agent-atlas v1.0. Emerged from observing which skills succeed vs. fail in autonomous execution.

---

## Multi-Agent Patterns

### 12. Parallel Plan Review with Scope Constraints

When reviewing plans, PRDs, or design docs, launch 3+ specialized reviewer agents in parallel — each with a fixed scope and distinct perspective.

- [ ] Scope is locked upfront: "scope is fixed, no negotiation — improvements and blind spots only"
- [ ] Each reviewer has a distinct lens (e.g., architecture, simplicity, domain-specific)
- [ ] Reviewers run in parallel, writing to separate output files
- [ ] Main agent synthesizes findings into a prioritized action table: bugs, high-value improvements, simplifications, nice-to-haves
- [ ] Fixes are applied, then a final pass verifies no ambiguity remains

**Why:** A single reviewer misses things. Multiple sequential reviews are slow and context-heavy. Parallel reviewers with locked scope prevent scope creep while surfacing blind spots from different angles. The synthesis step forces prioritization instead of a flat list of nitpicks.

**Example:**

```
main agent
  ├── reviewer-1: "architecture — are boundaries clean?"
  ├── reviewer-2: "simplicity — what can be removed?"
  └── reviewer-3: "domain expert — does this match how the domain works?"
  │
  └── synthesize → action table → apply fixes → verify
```

**Origin:** Emerged from PRD review workflows where single-pass reviews consistently missed cross-cutting concerns.

---

### 13. Run-Scoped Temporary Directories for Multi-Agent Workflows

When multiple subagents write output files in parallel, use a timestamped run directory to isolate their work.

- [ ] Create a run directory: `/tmp/{workflow}-{ISO-timestamp}/`
- [ ] Each subagent writes to disjoint files within the run dir (no shared paths)
- [ ] Main agent is the single writer to persistent storage (no concurrent writes to final locations)
- [ ] Subagents write `.done` or `.error` sentinel files for partial failure detection
- [ ] Main agent consolidates results after all subagents complete
- [ ] Entire run dir is cleaned up after successful consolidation

**Why:** Without run isolation, stale files from prior failed runs or concurrent invocations cause silent data corruption. Timestamped directories make each run independent. Sentinel files let the main agent detect partial failures without parsing output content. Single-writer to persistent storage eliminates race conditions.

**Example:**

```
/tmp/plan-review-2026-03-06T14:30:00/
  ├── reviewer-arch.md          # subagent 1 output
  ├── reviewer-arch.done        # sentinel: success
  ├── reviewer-simplicity.md    # subagent 2 output
  ├── reviewer-simplicity.done  # sentinel: success
  ├── reviewer-domain.md        # subagent 3 output
  └── reviewer-domain.error     # sentinel: failure (main agent handles gracefully)
```

**Origin:** Discovered after concurrent subagent runs collided on shared `/tmp` paths, producing merged output from different workflow invocations.

---

### 14. MCP Large Response Subagent Isolation

When an MCP tool returns large payloads (>10KB), call it from a subagent instead of the main agent. MCP tool results always embed in the caller's context window with no way to redirect to a file. A subagent processes the data, writes results to a temp file, and returns only a summary to the main agent.

- [ ] Identify MCP calls likely to return large payloads (bulk work order queries, full ERP item catalogs, IoT sensor dumps, large issue lists)
- [ ] Wrap those calls in a subagent with a focused task: "call tool X, extract Y, write to /tmp/Z"
- [ ] Subagent writes structured results to a temp file (JSON, markdown, or CSV)
- [ ] Subagent returns a short summary to the main agent (count, key findings, file path)
- [ ] Main agent reads the temp file only if it needs specific details
- [ ] Never call high-volume MCP tools directly from the main agent context

**Why:** MCP tool responses have no streaming or file-redirect option. They land entirely in the caller's context window. A single 500-record work order export or full ERP item catalog can consume 10-20% of the context budget, crowding out instructions and conversation history. Subagents absorb this cost in a disposable context, returning only the distilled result.

**Example:**

```
main agent: "reschedule overdue work orders"
  └── subagent: "query MES for open work orders, group by production line, write to /tmp/wo-summary.json"
       ├── calls MCP tool (large response stays in subagent context)
       ├── filters and groups 500+ work orders by line and priority
       ├── writes /tmp/wo-summary.json
       └── returns: "523 open work orders across 8 lines, 41 overdue, results in /tmp/wo-summary.json"
  └── main agent reads /tmp/wo-summary.json selectively
```

**Origin:** Observed in shop floor and ERP integration workflows where MCP responses (bulk sensor readings, work order lists, item catalogs) consumed significant context budget, degrading instruction-following in subsequent steps.

---

### 15. User Preference Feedback Loops

When a skill generates multiple options (drafts, variants, designs), log the user's selection to build a preference profile over time.

- [ ] Generate multiple variants (3+ with genuinely different angles, not rewording)
- [ ] Present variants with clear labels describing each angle
- [ ] Log selections to a persistent preference file (markdown, not code)
- [ ] Include: date, topic, selected/rejected variants, angle preference, user feedback
- [ ] Periodically review the log and promote patterns to the skill's style guide
- [ ] Use preference history to weight future generation toward preferred angles

**Why:** Single-variant generation is a coin flip. Multi-variant with logging creates a compounding feedback loop: the agent gets better at predicting what the user wants without explicit style rules. The preference log also serves as an audit trail for style evolution.

**Example structure:**
```
~/Documents/personal/content-drafts/variant-preferences.md

## 2026-03-06: acme-blog-post

**Selected:** A (direct), B (reflective)
**Rejected:** C (hot take)
**Angle preference:** Prefers depth over provocation in DE
```

**Origin:** Content authoring workflows where multi-variant generation with preference tracking produced measurably better first-draft acceptance rates over time.

**See also:** [decision-log-learning-loop.md](decision-log-learning-loop.md) — extends this pattern to any decision stream (triage, routing, categorization) with structured logging and pattern-based suggestions.

**See also:** [iterative-challenge-document.md](iterative-challenge-document.md) — a multi-round adversarial analysis pattern for high-stakes decisions (hiring, vendor selection, architecture). Each round incorporates new data, updates a scoring system, and refines the recommendation across sessions.

---

### 16. Domain Folder Memory

Place an `_agent_memory.md` file in non-git domain folders (sales accounts, project folders, event folders) that agents work in across multiple sessions. The file serves as a session bootstrapper: minimum context to go from cold to productive in one file read.

- [ ] Named `_agent_memory.md` (leading underscore sorts to top, signals meta-file)
- [ ] Contains: current status, key file index, external IDs (CRM, ticket, API), next actions (checkboxes), key context bullets, active guidance
- [ ] Created when a folder has multi-session workflows with external IDs, 3+ files, or pending next actions
- [ ] NOT created for one-shot folders, archives, or reference-only material
- [ ] Updated at end of session (capture skill or manual), read first at session start
- [ ] Excludes: detailed history (separate docs), general rules (belong in AGENTS.md), secrets

**Why:** Without a memory file, each new session burns time re-reading large documents, re-querying CRM IDs, and re-discovering folder structure. A 20-line memory file replaces 5+ minutes of expensive re-lookups and prevents the agent from making stale assumptions about project status.

**Example structure:**

```markdown
# Agent Memory: Acme Corp

## Status
Phase 1 in progress. Kickoff done, waiting on data export from client.

## Key Files
- `proposal_v2.pdf` - signed proposal (CHF 25k, 3 phases)
- `meeting_notes_2026-03-01.md` - kickoff notes
- `requirements.md` - validated requirements

## External IDs
- HubSpot Deal: 123456789
- Linear Project: ACM-42
- Contact: jane.doe@acme-corp.example.com

## Next Actions
- [ ] Follow up on data export (promised by 2026-03-14)
- [ ] Draft Phase 1 milestone plan

## Context
- Client prefers async updates over calls
- Technical contact is not the decision maker
```

**Origin:** Emerged from sales and project workflows where agents repeatedly spent the first 2-3 exchanges reconstructing context that was already known from prior sessions.

---

### 17. Auto-Memory Backup via Symlink

Claude Code stores per-project auto-memory in `~/.claude/projects/*/memory/` which is local-only and not backed up. Symlink each project's memory dir to a file-synced folder so memory survives machine loss.

- [ ] Set `memory_backup_dir` in `config.local.yaml` pointing to a file-synced folder
- [ ] SessionStart hook checks if `memory/` is already a symlink; if not, moves existing files and creates one
- [ ] Naming convention: backup dir mirrors Claude Code's path-encoded project names (e.g., `-home-user-git-repos-my-agent`)
- [ ] No manual setup needed for new repos if using the template-agent SessionStart hook

**Why:** Auto-memory files contain cross-session learnings, workflow preferences, and system knowledge accumulated over dozens of sessions. Losing them means the agent starts cold on every convention and pattern it previously learned. Unlike git-committed docs, auto-memory is the only place for user-specific preferences and corrections.

**Important:** Auto-memory files may contain customer names, contact details, and deal values. They must NOT be committed to git. The backup folder should be file-synced (e.g., Nextcloud, Dropbox), not version-controlled.

**Origin:** Discovered when reviewing data persistence: auto-memory had no backup path, meaning a disk failure would erase all accumulated agent knowledge.

---

## Repo Audit Matrix

| # | Convention | hub-agent | sales-agent | finance-agent | content-agent | education-agent | pipeline-agent |
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
4. Create tickets for compliance gaps
5. Fixes flow back as blueprint refinements → template updates
