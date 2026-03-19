# Skill: /snapshot

Generate a monthly architecture snapshot PDF for the agent-atlas repo.

## Triggers

- `/snapshot`
- "generate snapshot", "monthly snapshot", "architecture snapshot"

## Workflow

### 1. Scan repos

```bash
python3 .claude/skills/snapshot/scripts/scan_repos.py -o /tmp/agent-atlas-scan.json
```

Review the totals — sanity-check skill counts and repo presence.

### 2. Review content YAML

Read `content/current.yaml`. If anything has changed since last snapshot (new primitives, resolved tensions, new repos, maturity changes), update the YAML before proceeding. Use generic names only. Real names come from `config.local.yaml` name_mapping automatically at PDF render time. Ask the user if unsure.

### 3. Re-render Mermaid diagrams

Only if `.mmd` files have changed since last SVG render:

```bash
for f in diagrams/*.mmd; do
  mmdc -i "$f" -o "${f%.mmd}.svg" -t dark -b transparent --width 1200 \
    -p /dev/stdin <<< '{"executablePath": "/usr/bin/chromium", "args": ["--no-sandbox"]}'
done
```

### 4. Build PDF

```bash
python3 .claude/skills/snapshot/scripts/build_snapshot.py \
  --scan /tmp/agent-atlas-scan.json \
  --content content/current.yaml \
  --month YYYY-MM
```

Output lands in configured `output_dir` from `config.local.yaml`, or `snapshots/{month}` by default.

### 5. Deliver

Open the generated PDF for the user.

### 6. Blueprint audit (optional)

Review `blueprints/best-practices.md` audit matrix against scan results:
- Check each repo against the 11 conventions
- Update status in the matrix
- Update `last_full_audit` date in `content/current.yaml`
- Create tickets for any new compliance gaps

Skip this step if pressed for time — it can be done separately.

### 7. Commit and push

Commit updated YAML (if changed) and any re-rendered SVGs. Never commit `config.local.yaml` or files containing real repo names. The pre-commit hook enforces this via `.sensitive-terms`.

## Notes

- Scanner is zero-dep (stdlib only), build script needs PyYAML
- Diagrams 02-05 are qualitative — can't be auto-generated from scan data
- Diagram 01 stats can optionally be updated from scan data by editing the `.mmd` file
- The scan JSON is ephemeral (`/tmp/`) — not committed
- Repo list is configurable via `config.local.yaml` (falls back to example names)
