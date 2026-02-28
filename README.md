# Agent Atlas

Architecture snapshots and evolution tracking for the iosys multi-agent ecosystem.

## Structure

```
.claude/skills/snapshot/
  SKILL.md                  ← /snapshot skill definition
  scripts/
    scan_repos.py           ← auto-scanner (zero deps, outputs JSON)
    build_snapshot.py       ← HTML assembly + PDF render (needs PyYAML)
content/
  current.yaml              ← manually-authored qualitative sections
diagrams/                   ← Mermaid sources (.mmd) and rendered SVGs
snapshots/
  2026-02/                  ← monthly architecture snapshots
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

# 4. Output lands in snapshots/YYYY-MM/
```

## Content Model

- **Quantitative data** (skill counts, LOC, MCP servers) — auto-scanned by `scan_repos.py`
- **Qualitative content** (purposes, primitives, tensions, skill impacts) — manually maintained in `content/current.yaml`

## Repos Tracked

| Repo | Purpose |
|------|---------|
| `personal-agent` | CEO hub: TODOs, calendar, email, billing, meetings |
| `cso-agent` | Sales: HubSpot pipeline, forecasting |
| `cfo-agent` | Finance: cashflow, bank imports, invoicing |
| `content-creator` | LinkedIn posts, case studies, video, images |
| `teaching-agent` | Moodle LMS, Marp lecture slides |
| `optiverser` | Meeting transcript pipeline (Windmill) |
