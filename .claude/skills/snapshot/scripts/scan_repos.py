#!/usr/bin/env python3
"""
Scan agent repos for quantitative metrics.

Zero dependencies — stdlib only. Outputs JSON to stdout or file.

Usage:
    python3 scan_repos.py [--output /tmp/scan.json]
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPOS_DIR = Path.home() / "git_repos"
REPO_NAMES = [
    "personal-agent",
    "cso-agent",
    "cfo-agent",
    "content-creator",
    "teaching-agent",
    "optiverser",
]

EXCLUDE_DIRS = {"venv", ".venv", "__pycache__", "node_modules", ".git", ".mypy_cache"}


def count_skills(repo: Path) -> int:
    """Count .claude/skills/*/SKILL.md files."""
    skills_dir = repo / ".claude" / "skills"
    if not skills_dir.is_dir():
        return 0
    return sum(1 for d in skills_dir.iterdir()
               if d.is_dir() and (d / "SKILL.md").is_file())


def parse_mcp_servers(repo: Path) -> dict:
    """Parse .mcp.json for server count and names."""
    mcp_path = repo / ".mcp.json"
    if not mcp_path.is_file():
        return {"count": 0, "names": []}
    try:
        data = json.loads(mcp_path.read_text())
        servers = data.get("mcpServers", {})
        return {"count": len(servers), "names": sorted(servers.keys())}
    except (json.JSONDecodeError, KeyError):
        return {"count": 0, "names": []}


def count_python_loc(repo: Path) -> int:
    """Count Python lines of code, excluding typical non-source dirs."""
    total = 0
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".py"):
                try:
                    total += sum(1 for line in open(os.path.join(root, f),
                                                    encoding="utf-8", errors="ignore")
                                 if line.strip() and not line.strip().startswith("#"))
                except OSError:
                    pass
    return total


def count_solution_docs(repo: Path) -> int:
    """Count docs/solutions/**/*.md files."""
    solutions_dir = repo / "docs" / "solutions"
    if not solutions_dir.is_dir():
        return 0
    return sum(1 for _ in solutions_dir.rglob("*.md"))


def count_test_files(repo: Path) -> dict:
    """Count test files and total test LOC."""
    test_files = 0
    test_loc = 0
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.startswith("test_") or f.endswith("_test.py") or f.endswith("_spec.rb"):
                test_files += 1
                try:
                    test_loc += sum(1 for line in open(os.path.join(root, f),
                                                       encoding="utf-8", errors="ignore")
                                    if line.strip())
                except OSError:
                    pass
    # Also check tests/ directory for any .py files
    tests_dir = repo / "tests"
    if tests_dir.is_dir():
        for f in tests_dir.rglob("*.py"):
            if f.name not in ("__init__.py", "conftest.py"):
                if not any(p.name in EXCLUDE_DIRS for p in f.parents):
                    # Avoid double-counting if already matched by name pattern
                    if not (f.name.startswith("test_") or f.name.endswith("_test.py")):
                        test_files += 1
                        try:
                            test_loc += sum(1 for line in open(f,
                                                               encoding="utf-8", errors="ignore")
                                            if line.strip())
                        except OSError:
                            pass
    return {"files": test_files, "loc": test_loc}


def check_conventions(repo: Path) -> dict:
    """Check for standard convention files."""
    return {
        "agents_md": (repo / "AGENTS.md").is_file(),
        "config_template": (repo / "config.template.yaml").is_file(),
        "env_template": (
            (repo / ".env.template").is_file()
            or (repo / ".env.example").is_file()
        ),
    }


def last_commit(repo: Path) -> dict:
    """Get last commit date and message."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI\t%s"],
            cwd=repo, capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            date, msg = result.stdout.strip().split("\t", 1)
            return {"date": date, "message": msg}
    except (subprocess.TimeoutExpired, ValueError):
        pass
    return {"date": None, "message": None}


def scan_repo(name: str) -> dict:
    """Scan a single repo and return its metrics."""
    repo = REPOS_DIR / name
    if not repo.is_dir():
        return {"name": name, "exists": False}

    skills = count_skills(repo)
    mcp = parse_mcp_servers(repo)
    loc = count_python_loc(repo)
    docs = count_solution_docs(repo)
    tests = count_test_files(repo)
    conventions = check_conventions(repo)
    commit = last_commit(repo)

    return {
        "name": name,
        "exists": True,
        "skills": skills,
        "mcp_servers": mcp,
        "python_loc": loc,
        "solution_docs": docs,
        "tests": tests,
        "conventions": conventions,
        "last_commit": commit,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan agent repos for metrics")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    repos = {}
    for name in REPO_NAMES:
        repos[name] = scan_repo(name)

    totals = {
        "repos": len([r for r in repos.values() if r.get("exists")]),
        "skills": sum(r.get("skills", 0) for r in repos.values()),
        "mcp_servers": sum(r.get("mcp_servers", {}).get("count", 0) for r in repos.values()),
        "python_loc": sum(r.get("python_loc", 0) for r in repos.values()),
        "solution_docs": sum(r.get("solution_docs", 0) for r in repos.values()),
    }

    output = {
        "scan_date": datetime.now().isoformat(),
        "repos": repos,
        "totals": totals,
    }

    json_str = json.dumps(output, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(json_str)
        print(f"Scan written to {args.output}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
