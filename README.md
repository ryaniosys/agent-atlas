# Agent Atlas

> [!WARNING]
> **Experimental** — This project is under active development and subject to breaking changes, refactoring, and restructuring without notice. It is provided as-is with no warranty of any kind. Use at your own risk.

Architecture blueprints and best practices for building multi-agent systems — developed while building our own agent ecosystem at [iosys](https://iosys.swiss).

## Why This Exists

Scaling from one AI agent to many that collaborate reliably is an architectural challenge, not just a technical one. Agent Atlas documents the conventions, patterns, and pitfalls we encounter along the way — so we (and others) don't repeat the same mistakes.

## What's Inside

- **`blueprints/`** — Conventions and audit checklists for agent repositories (see [best-practices.md](blueprints/best-practices.md))
- **`snapshots/`** — Point-in-time architecture snapshots tracking how the ecosystem evolves
- **`diagrams/`** — System architecture visualizations (Mermaid sources + rendered SVGs)

## Who This Is For

- **Teams exploring multi-agent architectures** — patterns to consider before building
- **Our own team** — this is our living reference, evolving with every iteration

## Structure

```
.claude/skills/snapshot/
  SKILL.md                  <- /snapshot skill definition
  scripts/
    scan_repos.py           <- auto-scanner (zero deps, outputs JSON)
    build_snapshot.py       <- HTML assembly + PDF render (needs PyYAML)
content/
  current.yaml              <- manually-authored qualitative sections
diagrams/                   <- Mermaid sources (.mmd) and rendered SVGs
config.template.yaml        <- copy to config.local.yaml and customize
```

## Setup

```bash
cp config.template.yaml config.local.yaml
# Edit config.local.yaml with your org name, repo list, and output directory
```

## Generating a Snapshot

Use the `/snapshot` skill in Claude Code, or manually:

```bash
# 1. Scan repos for quantitative data
python3 .claude/skills/snapshot/scripts/scan_repos.py -o /tmp/agent-atlas-scan.json

# 2. (Optional) Render Mermaid diagrams to SVG
for f in diagrams/*.mmd; do
  mmdc -i "$f" -o "${f%.mmd}.svg" -t dark -b transparent --width 1200 \
    -p /dev/stdin <<< '{"executablePath": "/usr/bin/chromium", "args": ["--no-sandbox"]}'
done

# 3. Build HTML and render PDF
python3 .claude/skills/snapshot/scripts/build_snapshot.py \
  --scan /tmp/agent-atlas-scan.json \
  --content content/current.yaml

# 4. Output lands in configured output_dir (or snapshots/{month} by default)
```

## Content Model

- **Quantitative data** (skill counts, LOC, MCP servers) — auto-scanned by `scan_repos.py`
- **Qualitative content** (purposes, primitives, tensions, skill impacts) — manually maintained in `content/current.yaml`

## Example Repos Tracked

| Repo | Purpose |
|------|---------|
| `hub-agent` | Orchestration hub: TODOs, calendar, email, meetings |
| `sales-agent` | Sales: CRM pipeline, forecasting |
| `finance-agent` | Finance: cashflow, bank imports, invoicing |
| `content-agent` | Social posts, case studies, video, images |
| `education-agent` | LMS platform, lecture slides |
| `pipeline-agent` | Meeting transcript processing pipeline |

## License

MIT — see [LICENSE](LICENSE).
