# Agent Atlas

Architecture snapshots and evolution tracking for a multi-agent ecosystem.

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
