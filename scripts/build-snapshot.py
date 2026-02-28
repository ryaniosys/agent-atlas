#!/usr/bin/env python3
"""
Build architecture overview PDF from Mermaid SVG diagrams.

Usage:
    python3 scripts/build-snapshot.py [--month 2026-02]

Reads SVGs from diagrams/, assembles HTML, renders PDF via Chromium headless.
Output: snapshots/{month}/architecture-overview.pdf
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = REPO_ROOT / "diagrams"


def read_svg(name: str) -> str:
    """Read SVG file, strip XML declaration for HTML embedding."""
    svg_path = DIAGRAMS_DIR / f"{name}.svg"
    if not svg_path.exists():
        print(f"Warning: {svg_path} not found, skipping")
        return f'<p style="color:#e94560;">Diagram {name} not found</p>'
    content = svg_path.read_text()
    # Strip XML/DOCTYPE declarations for inline embedding
    lines = [l for l in content.splitlines()
             if not l.strip().startswith('<?xml') and not l.strip().startswith('<!DOCTYPE')]
    return "\n".join(lines)


def build_html(month: str) -> str:
    svg_hub = read_svg("01-hub-spoke")
    svg_deps = read_svg("02-dependencies")
    svg_email = read_svg("03-email-pipeline")
    svg_fs = read_svg("04-filesystem")
    svg_prims = read_svg("05-primitives")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Multi-Agent Architecture Overview — iosys</title>
<style>
  @page {{ size: A4; margin: 20mm 18mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'IBM Plex Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 10px; line-height: 1.5; color: #e0e0e0;
    background: #0d1117; padding: 40px; max-width: 210mm; margin: 0 auto;
  }}
  h1 {{ font-size: 22px; color: #e94560; border-bottom: 2px solid #e94560; padding-bottom: 8px; margin-bottom: 4px; }}
  .subtitle {{ font-size: 11px; color: #888; margin-bottom: 30px; }}
  h2 {{ font-size: 15px; color: #58a6ff; margin-top: 28px; margin-bottom: 10px; border-left: 3px solid #58a6ff; padding-left: 10px; }}
  h3 {{ font-size: 12px; color: #79c0ff; margin-top: 18px; margin-bottom: 6px; }}
  p, li {{ font-size: 10px; color: #c9d1d9; margin-bottom: 6px; }}
  ul {{ margin-left: 16px; margin-bottom: 10px; }}
  li {{ margin-bottom: 3px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 10px 0 16px 0; font-size: 9px; }}
  th {{ background: #161b22; color: #58a6ff; text-align: left; padding: 6px 8px; border: 1px solid #30363d; font-weight: 600; }}
  td {{ padding: 5px 8px; border: 1px solid #30363d; color: #c9d1d9; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #0d1117; }}
  tr:nth-child(odd) td {{ background: #161b22; }}
  .diagram {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin: 12px 0; text-align: center; page-break-inside: avoid; }}
  .diagram svg {{ max-width: 100%; height: auto; }}
  .diagram-caption {{ font-size: 9px; color: #666; margin-top: 6px; font-style: italic; }}
  .primitive {{ background: #161b22; border-left: 3px solid #533483; padding: 8px 12px; margin: 8px 0; page-break-inside: avoid; }}
  .primitive strong {{ color: #d2a8ff; }}
  .primitive p {{ margin-bottom: 3px; }}
  code {{ background: #1f2937; padding: 1px 4px; border-radius: 3px; font-size: 9px; color: #79c0ff; }}
  .page-break {{ page-break-before: always; }}
  .tension {{ background: #1a1412; border-left: 3px solid #e94560; padding: 8px 12px; margin: 6px 0; page-break-inside: avoid; }}
  .badge {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 8px; font-weight: 600; }}
  .badge-prod {{ background: #0a3d2e; color: #00b894; }}
  .badge-mvp {{ background: #3d2e0a; color: #ffc107; }}
  .badge-ops {{ background: #1a1a2e; color: #58a6ff; }}
</style>
</head>
<body>

<h1>Multi-Agent Architecture Overview</h1>
<p class="subtitle">iosys AG &mdash; Personal Agent Ecosystem &mdash; {month}<br>
6 repos &middot; 59 skills &middot; 7 MCP servers &middot; ~80 solution docs</p>

<h2>1. Architecture: Hub-and-Spoke</h2>
<p><code>personal-agent</code> is the orchestration hub. All other repos are specialized spokes
that share conventions, file paths, and data flows &mdash; but operate independently
in their own Claude Code sessions.</p>
<div class="diagram">
{svg_hub}
<div class="diagram-caption">Fig 1 &mdash; Hub-and-spoke topology with key stats per repo</div>
</div>

<h2>2. Per-Repo Summary</h2>
<table>
<tr><th>Repo</th><th>Purpose</th><th>Skills</th><th>LOC</th><th>MCP</th><th>Maturity</th><th>Self-Audit</th></tr>
<tr><td><strong>personal-agent</strong></td><td>CEO hub: TODOs, calendar, email, billing, meetings</td><td>42</td><td>&mdash;</td><td>6</td><td><span class="badge badge-prod">Production</span></td><td>69%</td></tr>
<tr><td><strong>cso-agent</strong></td><td>Sales: HubSpot pipeline, forecasting, events</td><td>4</td><td>1,150</td><td>0</td><td><span class="badge badge-mvp">MVP</span></td><td>59%</td></tr>
<tr><td><strong>cfo-agent</strong></td><td>Finance: cashflow, bank imports, receipts, invoicing</td><td>3</td><td>5,700</td><td>0</td><td><span class="badge badge-prod">Production</span></td><td>43%</td></tr>
<tr><td><strong>content-creator</strong></td><td>LinkedIn posts, case studies, video collage, images</td><td>6</td><td>1,219</td><td>0</td><td><span class="badge badge-prod">Production</span></td><td>&mdash;</td></tr>
<tr><td><strong>teaching-agent</strong></td><td>Moodle LMS, Marp lecture slides, course validation</td><td>4</td><td>&mdash;</td><td>1</td><td><span class="badge badge-ops">Operational</span></td><td>&mdash;</td></tr>
<tr><td><strong>optiverser</strong></td><td>Meeting transcript pipeline (Windmill &rarr; Teams)</td><td>0</td><td>650</td><td>0</td><td><span class="badge badge-ops">Operational</span></td><td>&mdash;</td></tr>
</table>

<h2>3. Cross-Repo Dependency Map</h2>
<div class="diagram">
{svg_deps}
<div class="diagram-caption">Fig 2 &mdash; Directed data and skill flows between repos</div>
</div>
<table>
<tr><th>From</th><th>To</th><th>What Flows</th></tr>
<tr><td>cso-agent</td><td>personal-agent</td><td><code>/create-closing-offer</code> skill, TODO routing to Eisenhower Matrix</td></tr>
<tr><td>cso-agent</td><td>cfo-agent</td><td>Revenue forecasts inform 13-week cashflow AR assumptions</td></tr>
<tr><td>cfo-agent</td><td>personal-agent</td><td>Financial TODOs, runway alerts</td></tr>
<tr><td>content-creator</td><td>personal-agent</td><td>Reads <code>persona/writing-style.md</code> for LinkedIn tone</td></tr>
<tr><td>content-creator</td><td>presentations</td><td><code>/case-study-presentation</code> skill reference</td></tr>
<tr><td>teaching-agent</td><td>personal-agent</td><td><code>/semester-planning</code> for calendar integration</td></tr>
<tr><td>personal-agent</td><td>optiverser</td><td>Same Optiverse API, different audience</td></tr>
</table>

<div class="page-break"></div>
<h2>4. Data Flow: Email &rarr; Action Pipeline</h2>
<p>The primary intake funnel. Flagged Outlook emails are triaged by
<code>/organize-inbox</code> into Linear tickets (customer/project work) or
TODO items (CEO topics), using rule-based routing defined in <code>rules.md</code>.</p>
<div class="diagram">
{svg_email}
<div class="diagram-caption">Fig 3 &mdash; Email intake and triage pipeline</div>
</div>

<h2>5. Shared Filesystem Map</h2>
<p>The repos don't share code &mdash; they share <em>paths</em>. Multiple agents read
and write to the same directories under <code>~/Documents/iosys/</code>, with
external APIs accessed by multiple repos in parallel.</p>
<div class="diagram">
{svg_fs}
<div class="diagram-caption">Fig 4 &mdash; Filesystem and API access patterns across repos</div>
</div>

<div class="page-break"></div>
<h2>6. Most Impactful Skills</h2>

<h3>personal-agent (top 10 of 42)</h3>
<table>
<tr><th>Skill</th><th>Impact</th></tr>
<tr><td><code>/billing-sync</code></td><td>2,036 LOC script; monthly invoicing pipeline (Toggl &rarr; Bexio)</td></tr>
<tr><td><code>/organize-inbox</code></td><td>Email &rarr; Linear ticket triage; primary intake funnel</td></tr>
<tr><td><code>/weekly-prep</code></td><td>Monday dashboard: calendar + TODOs + Linear</td></tr>
<tr><td><code>/send-meeting-recap</code></td><td>Optiverse &rarr; PDF &rarr; email draft for external stakeholders</td></tr>
<tr><td><code>/organize-meeting-transcripts</code></td><td>PRDs + relationship maps from customer calls</td></tr>
<tr><td><code>/strategic-planner</code></td><td>Strategy-as-YAML with testable hypotheses and confidence levels</td></tr>
<tr><td><code>/create-closing-offer</code></td><td>End-to-end sales closing package (Marp + offer + email)</td></tr>
<tr><td><code>/prep-meeting</code></td><td>Company research + attendee profiles before calls</td></tr>
<tr><td><code>/create-outlook-event</code></td><td>Graph API calendar with dual-calendar pattern</td></tr>
<tr><td><code>/create-linear-ticket</code></td><td>URL/context &rarr; structured Linear ticket</td></tr>
</table>

<h3>cso-agent</h3>
<table>
<tr><th>Skill</th><th>Impact</th></tr>
<tr><td><code>/forecast</code></td><td>Weighted pipeline revenue projections with confidence intervals</td></tr>
<tr><td><code>/pipeline</code></td><td>Stale deal detection, concentration risk, health scoring</td></tr>
<tr><td><code>/event-postprocessing</code></td><td>Business card OCR &rarr; HubSpot contact upsert</td></tr>
</table>

<h3>cfo-agent</h3>
<table>
<tr><th>Skill</th><th>Impact</th></tr>
<tr><td><code>/cashflow</code></td><td>13-week rolling forecast with runway calculation</td></tr>
<tr><td><code>/bank-import</code></td><td>CAMT.053/MT940 parsing into SQLite with dedup</td></tr>
<tr><td><code>/receipt-check</code></td><td>Bexio expense vs receipt reconciliation</td></tr>
</table>

<h3>content-creator</h3>
<table>
<tr><th>Skill</th><th>Impact</th></tr>
<tr><td><code>/linkedin-post-creator</code></td><td>Bilingual posts with distinct DE/EN voice, style-calibrated</td></tr>
<tr><td><code>picture-generator</code></td><td>Gemini API with model fallback chain, brand-consistent imagery</td></tr>
<tr><td><code>video-collage</code></td><td>FFmpeg-based clip assembly for LinkedIn/YouTube (722 LOC)</td></tr>
</table>

<h3>teaching-agent</h3>
<table>
<tr><th>Skill</th><th>Impact</th></tr>
<tr><td><code>/reverse-eng-slides</code></td><td>Story arc extraction &rarr; Marp slides with overflow detection</td></tr>
<tr><td><code>/prep-lecture</code></td><td>Pre-lecture briefing from Moodle enrollment + submissions</td></tr>
</table>

<div class="page-break"></div>
<h2>7. Emergent Primitives</h2>
<p>Eleven patterns that crystallized organically while building the system.</p>
<div class="diagram">
{svg_prims}
<div class="diagram-caption">Fig 5 &mdash; Primitives taxonomy by category</div>
</div>

<div class="primitive"><strong>1. CLAUDE.md &rarr; @AGENTS.md Redirect</strong>
<p>Every repo uses a one-line <code>CLAUDE.md</code> pointing to <code>AGENTS.md</code>. Separates the Claude Code hook from the actual instructions.</p></div>

<div class="primitive"><strong>2. Template-to-Local Config</strong>
<p><code>config.template.yaml</code> (committed) &rarr; <code>config.local.yaml</code> (gitignored). Same for <code>.env.template</code> &rarr; <code>.env</code>. Secrets never leak while keeping structure documented.</p></div>

<div class="primitive"><strong>3. Skill-as-Folder</strong>
<p><code>.claude/skills/&#123;name&#125;/SKILL.md</code> with optional <code>scripts/</code>, <code>templates/</code>, <code>*.yaml</code>. Single-purpose, self-documenting, composable.</p></div>

<div class="primitive"><strong>4. Tools as Pure Primitives, Logic in Prompts</strong>
<p>Data-access layers have zero business logic. Forecasting, health scoring, confidence intervals &mdash; all in SKILL.md files. The agent reasons; code just fetches.</p></div>

<div class="primitive"><strong>5. Solution Docs as Knowledge Base</strong>
<p><code>docs/solutions/&#123;category&#125;/&#123;slug&#125;.md</code> &mdash; ~80 files. Each: problem &rarr; investigation &rarr; root cause &rarr; solution &rarr; gotchas.</p></div>

<div class="primitive"><strong>6. MCP for Auth, Scripts for Reliability</strong>
<p>MCP servers handle authentication; actual operations use direct API calls (Python scripts). Token reuse pattern enables scripts to piggyback on MCP auth.</p></div>

<div class="primitive"><strong>7. Self-Improvement Loop</strong>
<p>Use &rarr; Observe friction &rarr; Refine primitive &rarr; Document in <code>tasks/lessons.md</code>. After every correction, capture the lesson.</p></div>

<div class="primitive"><strong>8. Agent-Native Audit with Scoring</strong>
<p>Formal self-audits scoring 8 principles: Action Parity, CRUD Completeness, Context Injection, Prompt-Native, Tools as Primitives, Shared Workspace, UI Integration, Capability Discovery.</p></div>

<div class="primitive"><strong>9. Data Privacy Boundary Enforcement</strong>
<p>Three-tier: <em>Committed</em> (anonymized), <em>Gitignored</em> (customer data), <em>Never leave machine</em> (financial).</p></div>

<div class="primitive"><strong>10. Dual-Calendar Pattern</strong>
<p>Business events go to both Outlook (Graph API) and Nextcloud B&amp;T (CalDAV). Availability checks query both.</p></div>

<div class="primitive"><strong>11. Progressive Instruction Disclosure</strong>
<p><code>AGENTS.md</code> (skim) &rarr; <code>instructions/*.md</code> (read) &rarr; <code>docs/solutions/*</code> (dive deep). Three layers for context window efficiency.</p></div>

<div class="page-break"></div>
<h2>8. Key Tensions / Tech Debt</h2>

<div class="tension"><strong>1. Dual HubSpot access</strong>
<p>personal-agent (MCP) and cso-agent (Python client) hit the same API without rate-limit coordination.</p></div>

<div class="tension"><strong>2. Optiverser library/flow divergence</strong>
<p>Production-grade library scripts exist but aren't wired into the deployed flow (missing PII redaction, dedup, SSRF protection).</p></div>

<div class="tension"><strong>3. Venv inconsistency</strong>
<p>personal-agent: <code>/tmp/</code> shared venv. cfo-agent: project-local <code>.venv</code> with <code>uv</code>. content-creator: per-skill venvs.</p></div>

<div class="tension"><strong>4. Content-creator dual skill dirs</strong>
<p><code>skills/</code> (legacy) vs <code>.claude/skills/</code> (slash commands) &mdash; some duplicated.</p></div>

<div class="tension"><strong>5. Cross-agent integration is conceptual</strong>
<p>cso &rarr; cfo revenue forecast flow, cso &rarr; personal-agent TODO routing &mdash; documented but not automated.</p></div>

<h2>9. Maturity Spectrum</h2>
<table>
<tr><th>Repo</th><th>Maturity</th><th>Skills</th><th>Tests</th><th>Solution Docs</th><th>MCP</th><th>Self-Audit</th></tr>
<tr><td>personal-agent</td><td><span class="badge badge-prod">Production</span></td><td>42</td><td>1 regression</td><td>~80</td><td>6</td><td>69%</td></tr>
<tr><td>cfo-agent</td><td><span class="badge badge-prod">Production</span></td><td>3</td><td>2,203 LOC (6 files)</td><td>6</td><td>0</td><td>43%</td></tr>
<tr><td>cso-agent</td><td><span class="badge badge-mvp">MVP</span></td><td>4</td><td>0</td><td>1</td><td>0</td><td>59%</td></tr>
<tr><td>content-creator</td><td><span class="badge badge-prod">Production</span></td><td>6</td><td>0</td><td>9</td><td>0</td><td>&mdash;</td></tr>
<tr><td>teaching-agent</td><td><span class="badge badge-ops">Operational</span></td><td>4</td><td>0</td><td>10</td><td>1</td><td>&mdash;</td></tr>
<tr><td>optiverser</td><td><span class="badge badge-ops">Operational</span></td><td>0</td><td>0</td><td>1 plan</td><td>0</td><td>&mdash;</td></tr>
</table>

<div style="margin-top: 40px; padding-top: 16px; border-top: 1px solid #30363d; color: #555; font-size: 8px;">
  Generated {month} &middot; iosys AG &middot; Multi-Agent Architecture Reference v1.0
</div>

</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Build architecture snapshot PDF")
    parser.add_argument("--month", default=datetime.now().strftime("%Y-%m"),
                        help="Snapshot month label (default: current month)")
    args = parser.parse_args()

    snapshot_dir = REPO_ROOT / "snapshots" / args.month
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    html_path = snapshot_dir / "architecture-overview.html"
    pdf_path = snapshot_dir / "architecture-overview.pdf"

    html = build_html(args.month)
    html_path.write_text(html)
    print(f"HTML: {html_path} ({len(html)} bytes)")

    result = subprocess.run([
        "/usr/bin/chromium", "--headless", "--disable-gpu", "--no-sandbox",
        f"--print-to-pdf={pdf_path}", "--print-to-pdf-no-header",
        f"file://{html_path}"
    ], capture_output=True, text=True)

    if pdf_path.exists():
        print(f"PDF:  {pdf_path} ({pdf_path.stat().st_size} bytes)")
    else:
        print(f"Error: PDF generation failed\n{result.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
