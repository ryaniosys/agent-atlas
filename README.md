# Agent Atlas

Architecture snapshots and evolution tracking for the iosys multi-agent ecosystem.

## Structure

```
snapshots/
  2026-02/              ← monthly architecture snapshots
    architecture-overview.pdf
diagrams/               ← Mermaid sources (.mmd) and rendered SVGs
scripts/
  build-snapshot.py     ← assembles HTML from SVGs, renders to PDF
```

## Generating a Snapshot

```bash
# 1. Render Mermaid diagrams to SVG
for f in diagrams/*.mmd; do
  mmdc -i "$f" -o "${f%.mmd}.svg" -t dark -b transparent --width 1200 \
    -p /dev/stdin <<< '{"executablePath": "/usr/bin/chromium", "args": ["--no-sandbox"]}'
done

# 2. Build HTML and render PDF
python3 scripts/build-snapshot.py

# 3. Output lands in snapshots/YYYY-MM/
```

## Repos Tracked

| Repo | Purpose |
|------|---------|
| `personal-agent` | CEO hub: TODOs, calendar, email, billing, meetings |
| `cso-agent` | Sales: HubSpot pipeline, forecasting |
| `cfo-agent` | Finance: cashflow, bank imports, invoicing |
| `content-creator` | LinkedIn posts, case studies, video, images |
| `teaching-agent` | Moodle LMS, Marp lecture slides |
| `optiverser` | Meeting transcript pipeline (Windmill) |
