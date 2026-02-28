#!/usr/bin/env python3
"""
Build architecture overview PDF from scan data + qualitative content.

Reads two inputs:
  --scan    JSON from scan_repos.py (quantitative metrics)
  --content YAML file (qualitative descriptions, primitives, tensions)

Renders HTML with inline SVG diagrams, then PDF via Chromium headless.

Usage:
    python3 build_snapshot.py --scan /tmp/scan.json --content content/current.yaml
    python3 build_snapshot.py --scan /tmp/scan.json --content content/current.yaml --month 2026-03
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent  # scripts -> snapshot -> skills -> .claude -> repo root
DIAGRAMS_DIR = REPO_ROOT / "diagrams"

MATURITY_BADGES = {
    "production": '<span class="badge badge-prod">Production</span>',
    "mvp": '<span class="badge badge-mvp">MVP</span>',
    "operational": '<span class="badge badge-ops">Operational</span>',
}

CSS = """
@page { size: A4; margin: 20mm 18mm; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'IBM Plex Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 10px; line-height: 1.5; color: #e0e0e0;
  background: #0d1117; padding: 40px; max-width: 210mm; margin: 0 auto;
}
h1 { font-size: 22px; color: #e94560; border-bottom: 2px solid #e94560; padding-bottom: 8px; margin-bottom: 4px; }
.subtitle { font-size: 11px; color: #888; margin-bottom: 30px; }
h2 { font-size: 15px; color: #58a6ff; margin-top: 28px; margin-bottom: 10px; border-left: 3px solid #58a6ff; padding-left: 10px; }
h3 { font-size: 12px; color: #79c0ff; margin-top: 18px; margin-bottom: 6px; }
p, li { font-size: 10px; color: #c9d1d9; margin-bottom: 6px; }
ul { margin-left: 16px; margin-bottom: 10px; }
li { margin-bottom: 3px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 16px 0; font-size: 9px; }
th { background: #161b22; color: #58a6ff; text-align: left; padding: 6px 8px; border: 1px solid #30363d; font-weight: 600; }
td { padding: 5px 8px; border: 1px solid #30363d; color: #c9d1d9; vertical-align: top; }
tr:nth-child(even) td { background: #0d1117; }
tr:nth-child(odd) td { background: #161b22; }
.diagram { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin: 12px 0; text-align: center; page-break-inside: avoid; }
.diagram svg { max-width: 100%; height: auto; }
.diagram-caption { font-size: 9px; color: #666; margin-top: 6px; font-style: italic; }
.primitive { background: #161b22; border-left: 3px solid #533483; padding: 8px 12px; margin: 8px 0; page-break-inside: avoid; }
.primitive strong { color: #d2a8ff; }
.primitive p { margin-bottom: 3px; }
code { background: #1f2937; padding: 1px 4px; border-radius: 3px; font-size: 9px; color: #79c0ff; }
.page-break { page-break-before: always; }
.tension { background: #1a1412; border-left: 3px solid #e94560; padding: 8px 12px; margin: 6px 0; page-break-inside: avoid; }
.badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 8px; font-weight: 600; }
.badge-prod { background: #0a3d2e; color: #00b894; }
.badge-mvp { background: #3d2e0a; color: #ffc107; }
.badge-ops { background: #1a1a2e; color: #58a6ff; }
"""


def read_svg(name: str) -> str:
    """Read SVG file, strip XML declaration for HTML embedding."""
    svg_path = DIAGRAMS_DIR / f"{name}.svg"
    if not svg_path.exists():
        print(f"Warning: {svg_path} not found, skipping")
        return f'<p style="color:#e94560;">Diagram {name} not found</p>'
    content = svg_path.read_text()
    lines = [l for l in content.splitlines()
             if not l.strip().startswith('<?xml') and not l.strip().startswith('<!DOCTYPE')]
    return "\n".join(lines)


def fmt_loc(n: int) -> str:
    """Format LOC number with comma separator, or dash if zero."""
    if not n:
        return "&mdash;"
    return f"{n:,}"


def fmt_audit(score) -> str:
    """Format self-audit score percentage."""
    if score is None:
        return "&mdash;"
    return f"{score}%"


def render_header(month: str, totals: dict) -> str:
    meta_line = (
        f"{totals['repos']} repos &middot; "
        f"{totals['skills']} skills &middot; "
        f"{totals['mcp_servers']} MCP servers &middot; "
        f"~{totals['solution_docs']} solution docs"
    )
    return f"""
<h1>Multi-Agent Architecture Overview</h1>
<p class="subtitle">iosys AG &mdash; Personal Agent Ecosystem &mdash; {month}<br>
{meta_line}</p>
"""


def render_hub_spoke(content: dict, svg: str) -> str:
    diag = content["diagrams"]["hub_spoke"]
    return f"""
<h2>1. Architecture: Hub-and-Spoke</h2>
<p><code>personal-agent</code> is the orchestration hub. {diag['intro']}</p>
<div class="diagram">
{svg}
<div class="diagram-caption">{diag['caption']}</div>
</div>
"""


def render_repo_table(scan: dict, content: dict) -> str:
    rows = []
    for name in ["personal-agent", "cso-agent", "cfo-agent",
                 "content-creator", "teaching-agent", "optiverser"]:
        repo_scan = scan["repos"].get(name, {})
        repo_content = content["repos"].get(name, {})

        purpose = repo_content.get("purpose", "")
        skills = repo_scan.get("skills", 0)
        loc = fmt_loc(repo_scan.get("python_loc", 0))
        mcp = repo_scan.get("mcp_servers", {}).get("count", 0)
        maturity = MATURITY_BADGES.get(repo_content.get("maturity", ""), "")
        audit = fmt_audit(repo_content.get("self_audit"))

        rows.append(
            f'<tr><td><strong>{name}</strong></td><td>{purpose}</td>'
            f'<td>{skills}</td><td>{loc}</td><td>{mcp}</td>'
            f'<td>{maturity}</td><td>{audit}</td></tr>'
        )

    return f"""
<h2>2. Per-Repo Summary</h2>
<table>
<tr><th>Repo</th><th>Purpose</th><th>Skills</th><th>LOC</th><th>MCP</th><th>Maturity</th><th>Self-Audit</th></tr>
{''.join(rows)}
</table>
"""


def render_dependencies(content: dict, svg: str) -> str:
    rows = []
    for dep in content["dependencies"]:
        rows.append(
            f'<tr><td>{dep["from"]}</td><td>{dep["to"]}</td>'
            f'<td><code>{dep["flow"]}</code></td></tr>'
        )
    caption = content["diagrams"]["dependencies"]["caption"]
    return f"""
<h2>3. Cross-Repo Dependency Map</h2>
<div class="diagram">
{svg}
<div class="diagram-caption">{caption}</div>
</div>
<table>
<tr><th>From</th><th>To</th><th>What Flows</th></tr>
{''.join(rows)}
</table>
"""


def render_email_pipeline(content: dict, svg: str) -> str:
    diag = content["diagrams"]["email_pipeline"]
    return f"""
<div class="page-break"></div>
<h2>4. Data Flow: Email &rarr; Action Pipeline</h2>
<p>{diag['intro']}</p>
<div class="diagram">
{svg}
<div class="diagram-caption">{diag['caption']}</div>
</div>
"""


def render_filesystem(content: dict, svg: str) -> str:
    diag = content["diagrams"]["filesystem"]
    return f"""
<h2>5. Shared Filesystem Map</h2>
<p>{diag['intro']}</p>
<div class="diagram">
{svg}
<div class="diagram-caption">{diag['caption']}</div>
</div>
"""


def render_skills_tables(content: dict, scan: dict) -> str:
    html_parts = ['<div class="page-break"></div>', '<h2>6. Most Impactful Skills</h2>']

    for repo_name, repo_data in content["impactful_skills"].items():
        # Build label — use dynamic count from scan if available
        label = repo_data.get("label", "")
        if label and "{count}" in label:
            count = scan["repos"].get(repo_name, {}).get("skills", "?")
            label = f" ({label.format(count=count)})"
        elif label:
            label = f" ({label})"

        html_parts.append(f'<h3>{repo_name}{label}</h3>')
        html_parts.append('<table>')
        html_parts.append('<tr><th>Skill</th><th>Impact</th></tr>')
        for skill in repo_data["skills"]:
            html_parts.append(
                f'<tr><td><code>{skill["name"]}</code></td>'
                f'<td>{skill["impact"]}</td></tr>'
            )
        html_parts.append('</table>')

    return "\n".join(html_parts)


def render_primitives(content: dict, svg: str) -> str:
    caption = content["diagrams"]["primitives"]["caption"]
    prims = []
    for i, p in enumerate(content["primitives"], 1):
        desc = p["description"]
        # Wrap code-like references in <code> tags
        prims.append(
            f'<div class="primitive"><strong>{i}. {p["name"]}</strong>\n'
            f'<p>{desc}</p></div>'
        )

    return f"""
<div class="page-break"></div>
<h2>7. Emergent Primitives</h2>
<p>{len(content['primitives'])} patterns that crystallized organically while building the system.</p>
<div class="diagram">
{svg}
<div class="diagram-caption">{caption}</div>
</div>

{''.join(prims)}
"""


def render_tensions(content: dict) -> str:
    items = []
    for i, t in enumerate(content["tensions"], 1):
        items.append(
            f'<div class="tension"><strong>{i}. {t["name"]}</strong>\n'
            f'<p>{t["description"]}</p></div>'
        )

    return f"""
<div class="page-break"></div>
<h2>8. Key Tensions / Tech Debt</h2>
{''.join(items)}
"""


def render_maturity_table(scan: dict, content: dict) -> str:
    rows = []
    for name in ["personal-agent", "cfo-agent", "cso-agent",
                 "content-creator", "teaching-agent", "optiverser"]:
        repo_scan = scan["repos"].get(name, {})
        repo_content = content["repos"].get(name, {})

        maturity = MATURITY_BADGES.get(repo_content.get("maturity", ""), "")
        skills = repo_scan.get("skills", 0)
        tests = repo_scan.get("tests", {})
        test_info = f"{tests.get('files', 0)} files" if tests.get("files") else "0"
        if tests.get("loc"):
            test_info += f" ({fmt_loc(tests['loc'])} LOC)"
        docs = repo_scan.get("solution_docs", 0)
        mcp = repo_scan.get("mcp_servers", {}).get("count", 0)
        audit = fmt_audit(repo_content.get("self_audit"))

        rows.append(
            f'<tr><td>{name}</td><td>{maturity}</td><td>{skills}</td>'
            f'<td>{test_info}</td><td>{docs}</td><td>{mcp}</td><td>{audit}</td></tr>'
        )

    return f"""
<h2>9. Maturity Spectrum</h2>
<table>
<tr><th>Repo</th><th>Maturity</th><th>Skills</th><th>Tests</th><th>Solution Docs</th><th>MCP</th><th>Self-Audit</th></tr>
{''.join(rows)}
</table>
"""


def render_footer(month: str) -> str:
    return f"""
<div style="margin-top: 40px; padding-top: 16px; border-top: 1px solid #30363d; color: #555; font-size: 8px;">
  Generated {month} &middot; iosys AG &middot; Multi-Agent Architecture Reference v1.1
</div>
"""


def build_html(scan: dict, content: dict, month: str) -> str:
    svg_hub = read_svg("01-hub-spoke")
    svg_deps = read_svg("02-dependencies")
    svg_email = read_svg("03-email-pipeline")
    svg_fs = read_svg("04-filesystem")
    svg_prims = read_svg("05-primitives")

    sections = [
        render_header(month, scan["totals"]),
        render_hub_spoke(content, svg_hub),
        render_repo_table(scan, content),
        render_dependencies(content, svg_deps),
        render_email_pipeline(content, svg_email),
        render_filesystem(content, svg_fs),
        render_skills_tables(content, scan),
        render_primitives(content, svg_prims),
        render_tensions(content),
        render_maturity_table(scan, content),
        render_footer(month),
    ]

    body = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Multi-Agent Architecture Overview — iosys</title>
<style>
{CSS}
</style>
</head>
<body>
{body}
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Build architecture snapshot PDF")
    parser.add_argument("--scan", required=True, help="JSON file from scan_repos.py")
    parser.add_argument("--content", required=True, help="YAML content file")
    parser.add_argument("--month", default=datetime.now().strftime("%Y-%m"),
                        help="Snapshot month label (default: current month)")
    parser.add_argument("--output-dir", help="Output directory (default: snapshots/{month})")
    args = parser.parse_args()

    scan = json.loads(Path(args.scan).read_text())
    content = yaml.safe_load(Path(args.content).read_text())

    output_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "snapshots" / args.month
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / "architecture-overview.html"
    pdf_path = output_dir / "architecture-overview.pdf"

    html = build_html(scan, content, args.month)
    html_path.write_text(html)
    print(f"HTML: {html_path} ({len(html):,} bytes)")

    result = subprocess.run([
        "/usr/bin/chromium", "--headless", "--disable-gpu", "--no-sandbox",
        f"--print-to-pdf={pdf_path}", "--print-to-pdf-no-header",
        f"file://{html_path}"
    ], capture_output=True, text=True)

    if pdf_path.exists():
        print(f"PDF:  {pdf_path} ({pdf_path.stat().st_size:,} bytes)")
    else:
        print(f"Error: PDF generation failed\n{result.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
