# feat: Local-Only Snapshot Overlay for Public Repo Hygiene

> **v2** - Revised after plan review (DHH, Kieran, Simplicity). Collapsed 3 phases / 8 files into 1 phase / 4 files. Approach B: HTML-level name substitution.

## Overview

agent-atlas is a **public** GitHub repo. The snapshot skill generates architecture PDFs. Committed content uses generic names (`hub-agent`, `sales-agent`). Locally, the PDF should show real repo names and org info without any committed file ever containing private data.

## Problem Statement

Running `/snapshot` today requires editing `content/current.yaml` with real names, then reverting before commit. The pre-commit hook catches mistakes, but the workflow itself is error-prone. Real names should flow from gitignored config only.

## Proposed Solution: HTML-Level Name Substitution

Keep all YAML and Mermaid source files generic. Apply a single `re.sub` pass on the **final rendered HTML** before Chromium converts it to PDF. This means:

- `content/current.yaml` stays generic (committed as-is)
- `diagrams/*.mmd` stay generic (committed as-is)
- No content overlay, no deep merge, no temp diagram files
- One substitution function, applied once, right before PDF render

The name mapping and org override come from `config.local.yaml`, which is already gitignored.

## Technical Approach

### 1. Extend `config.local.yaml` with a `name_mapping` section

Add a flat dict mapping generic display names to real names, plus org override:

```yaml
org:
  name: "Acme Corp"          # overrides "Example Corp" in content YAML

# Map committed generic names to real names for local PDF rendering
name_mapping:
  hub-agent: acme-hub
  sales-agent: acme-sales
  finance-agent: acme-finance
  content-agent: acme-content
  education-agent: acme-edu
  pipeline-agent: acme-pipeline
```

Also add `display_name` to each repo entry so `scan_repos.py` can key its output by the generic name (matching `content/current.yaml` keys):

```yaml
repos:
  - name: acme-hub             # real folder name on disk
    display_name: hub-agent     # generic name used in content/current.yaml
    purpose: "Orchestration hub"
```

Update `config.template.yaml` with comments documenting both fields.

Files: `config.template.yaml` (edit), `config.local.yaml` (edit, gitignored)

### 2. Update `scan_repos.py` to key output by `display_name`

Currently `scan_repo(name)` returns `{"name": name, ...}` and the output dict is keyed by `name` (the real folder name). Change it so the output key uses `display_name` when available, falling back to `name`.

This is ~5 lines changed in `main()`:

```python
for repo_entry in repo_list:
    name = repo_entry["name"] if isinstance(repo_entry, dict) else repo_entry
    display = repo_entry.get("display_name", name) if isinstance(repo_entry, dict) else name
    repos[display] = scan_repo(name)
    repos[display]["display_name"] = display
```

Now scan output keys match `content/current.yaml` repo keys, so `build_snapshot.py`'s `render_repo_table()` lookup (`scan["repos"].get(name)`) works without changes.

File: `.claude/skills/snapshot/scripts/scan_repos.py`

### 3. Add HTML substitution in `build_snapshot.py`

After `build_html()` produces the full HTML string and before Chromium renders the PDF, apply name substitution:

```python
def substitute_names(html: str, config: dict) -> str:
    """Replace generic names with real names in rendered HTML.

    Single-pass regex, longest keys first to prevent partial matches.
    Only runs if config has name_mapping; otherwise returns html unchanged.
    """
    mapping = config.get("name_mapping", {})
    # Also substitute org name
    org_override = config.get("org", {}).get("name")
    if org_override:
        mapping["Example Corp"] = org_override
    if not mapping:
        return html
    pattern = re.compile(
        "|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True))
    )
    return pattern.sub(lambda m: mapping[m.group(0)], html)
```

In `main()`, between HTML generation and Chromium PDF render (~3 lines added):

```python
html = build_html(scan, content, args.month)
html = substitute_names(html, config)     # <-- new
html_path.write_text(html)
```

Config loading in `main()` reads `config.local.yaml` if present (~5 lines):

```python
config = {}
config_path = REPO_ROOT / "config.local.yaml"
if config_path.is_file():
    config = yaml.safe_load(config_path.read_text()) or {}
```

Output dir resolution from config (~3 lines, before existing `output_dir` logic):

```python
if not args.output_dir and config.get("output_dir"):
    args.output_dir = str(Path(config["output_dir"]).expanduser())
```

File: `.claude/skills/snapshot/scripts/build_snapshot.py`

### 4. Update SKILL.md workflow notes

Minor wording changes:
- Step 2: "Review `content/current.yaml`. Use generic names only. Real names come from `config.local.yaml` automatically."
- Step 3: No changes (diagrams render as before with generic names; substitution happens in HTML)
- Step 7: "Commit updated YAML if qualitative content changed (new primitives, tensions). Real names never appear in committed files."

File: `.claude/skills/snapshot/SKILL.md`

## Acceptance Criteria

- [ ] `/snapshot` without `config.local.yaml` produces a PDF with generic names (backward compatible)
- [ ] `/snapshot` with `config.local.yaml` (including `name_mapping`) produces a PDF with real names and real org
- [ ] Output PDF lands in `output_dir` from config when set
- [ ] No real repo names in any committed file (pre-commit hook still enforces this)
- [ ] `content/current.yaml` and `diagrams/*.mmd` are never modified during a local build
- [ ] Scan output keys match `content/current.yaml` repo keys via `display_name`

## Files Changed

| File | Action | Lines Changed |
|------|--------|---------------|
| `config.template.yaml` | Edit | Add `name_mapping`, `display_name`, `org.name` with comments |
| `.claude/skills/snapshot/scripts/scan_repos.py` | Edit | ~5 lines in `main()` for `display_name` keying |
| `.claude/skills/snapshot/scripts/build_snapshot.py` | Edit | ~15 lines: config loading, `substitute_names()`, output_dir from config |
| `.claude/skills/snapshot/SKILL.md` | Edit | ~5 lines of wording updates |

**Not created:** `config_utils.py`, `content/local.yaml`, `content/local.yaml.example`

## What Was Cut (v1 to v2)

| Removed | Why |
|---------|-----|
| `config_utils.py` module | Unnecessary abstraction for two scripts |
| `deep_merge()` | No content overlay needed; YAML stays generic |
| `content/local.yaml` + gitignore entry | No content overlay needed |
| `content/local.yaml.example` | No content overlay needed |
| `build_name_mapping()` | Replaced by flat `name_mapping` dict in config |
| Temp `.mmd` file rendering to `/tmp/` | Substitution happens on HTML, not Mermaid source |
| `--local` CLI flag | Config auto-detected from `config.local.yaml` |
| `alias` field in repo entries | Replaced by simpler `display_name` |

## Edge Cases

- **No `config.local.yaml`:** Everything works as before. Generic names, default output dir.
- **Partial `name_mapping`:** Only mapped names get substituted. Unmapped generic names pass through unchanged.
- **New repo added:** Add generic entry to `content/current.yaml`, add `display_name` + `name_mapping` entry to `config.local.yaml`.
- **`name_mapping` key appears in HTML boilerplate:** Low risk given naming conventions (`hub-agent` won't appear in CSS/HTML tags). Worth a quick scan of output if concerned.

## Dependencies

No new dependencies. stdlib `re` + PyYAML (already required).

## References

- `scan_repos.py:32-44` (existing config.local.yaml loading)
- `build_snapshot.py:305-340` (HTML build + PDF render pipeline)
- `.githooks/pre-commit` + `.sensitive-terms:20-31` (deny-list enforcement)
