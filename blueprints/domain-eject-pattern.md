# Domain Eject Pattern

> How to split a growing domain out of a hub agent into its own spoke repo.

## Problem

A hub agent (e.g., a CEO assistant) accumulates domain-specific content over time: plans, skills, solution docs, config sections. Eventually a domain gets heavy enough that it pollutes the hub's context window and deserves its own repo.

## When to Eject

A domain is ready when **2+ of these are true:**
- 3+ skills belonging to the domain
- 5+ plans in `plans/`
- 5+ solution docs under one category
- Dedicated external data folder or remote machines
- Sessions frequently context-switch between hub work and this domain
- Domain has its own external APIs or integrations

**Don't eject if:**
- Fewer than 3 artifacts total (too thin)
- Heavy cross-cutting dependencies (calendar, email)
- One-off project, not ongoing responsibility

## Pattern

### 1. Scan and Manifest

Scan the hub repo for all content belonging to the domain. Produce a transfer manifest:

| File | Type | Action |
|------|------|--------|
| `plans/domain-*.md` | Plan | MOVE |
| `docs/solutions/domain/` | Doc | MOVE |
| `.claude/skills/domain-skill/` | Skill | MOVE |
| `scripts/shared-util.py` | Script | KEEP (cross-ref) |
| AGENTS.md "Domain Section" | Section | REPLACE with pointer |

Actions:
- **MOVE:** Copy to new repo, mark as moved in hub
- **KEEP (cross-ref):** Stays in hub, new repo references it
- **REPLACE with pointer:** Hub section becomes one-liner pointing to new repo

User must approve the manifest.

### 2. Create from Template

Clone the org's template repo, reinitialize git, customize the boilerplate:
- AGENTS.md (domain-specific config, machines, skills)
- PRD.md (vision, hub-and-spoke diagram, roadmap)
- config.template.yaml (domain paths, integrations)
- README.md (setup, skills, structure)

Initial commit on main. Push to remote.

### 3. Migrate Content

Feature branch in new repo. Copy all MOVE items from manifest. Force-add gitignored dirs (like `plans/`). Commit and PR.

### 4. Update Hub

Feature branch in hub repo:
- Add new repo to domain routing table
- Add to distributed memory table
- Mark moved skills as "Moved to {domain}-agent"
- Replace detailed domain sections with pointers
- Remove migrated config sections

Commit and PR.

### 5. Cross-Reference Audit

Check bidirectional consistency across three files:
- Global instructions (e.g., `~/CLAUDE.md`)
- Hub agent instructions (e.g., `hub-agent/AGENTS.md`)
- New spoke instructions (e.g., `domain-agent/AGENTS.md`)

Verify:
- [ ] New repo in global repo table
- [ ] New repo in hub's domain routing + distributed memory
- [ ] Hub-and-spoke diagram in new repo is complete
- [ ] All MOVE items present in new repo
- [ ] All MOVE items marked as moved in hub
- [ ] Domain knowledge transferred (formatting rules, safety warnings, etc.)
- [ ] Shared utilities cross-referenced, not duplicated

Fix all gaps before merging.

### 6. Post-Eject

- Set up distributed memory dir for new repo
- Create `config.local.yaml`
- Install git hooks
- Update architecture snapshots (if maintained)
- Run context capture to document the migration

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Do This Instead |
|-------------|---------------|-----------------|
| Eject too early | Repo with 2 files is overhead | Wait for 2+ readiness criteria |
| Duplicate shared utilities | Two copies drift apart | Cross-reference from hub |
| Skip the audit | Gaps cause confusion in future sessions | Always run bidirectional check |
| Forget global instructions | New repo invisible to other contexts | Update the global file |
| Move customer data to git | Privacy violation | Data stays in synced folders, never git |

## Detection

Add overload detection to your context-capture workflow. Trigger when a session produces 3+ artifacts in a single non-hub domain, or when domain-specific content crosses the readiness threshold. Surface the signal to the user. Don't auto-eject.

## Reference Implementation

First application: extracting infrastructure management from a CEO assistant hub into a dedicated infra spoke (March 2026). Migrated 13 plans, 9 solution docs, 1 skill. Cross-reference audit found 8 gaps, all fixed before merge.
