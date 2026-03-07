# Agent-Native Skill Authoring Checklist

How to write Claude Code skills that an LLM agent can execute without ambiguity.

## The Problem

Skills written for human readers often fail when executed by an agent because:
- Tool names are shorthand (agent can't resolve them)
- Prerequisites aren't verified before use
- Async operations don't have explicit waits
- Instructions use ambiguous language ("look for", "find")

## The Gap: Human vs. Agent Execution

| Aspect | Human | Agent |
|--------|-------|-------|
| Tool names | Infers from context | Needs explicit full names |
| Missing config | Notices immediately | Fails silently |
| Page load timing | Waits naturally | Executes sequentially |
| Ambiguous instructions | Interprets from context | Follows literally |

## Checklist

### 1. MCP Tool Discovery

- [ ] Include "Step 0: Load Tools" with explicit ToolSearch
- [ ] Document full tool identifiers or reference ToolSearch results
- [ ] Never use shorthand names without explanation

**Pattern:**
```markdown
Load Playwright browser tools:
Use ToolSearch with query: "+pw browser"
Use exact tool names returned (e.g., mcp__plugin_...__browser_navigate).
```

### 2. Prerequisites Verification

- [ ] Check required files exist before referencing
- [ ] Source environment variables explicitly
- [ ] Validate config sections have required fields
- [ ] Provide recovery instructions for missing prerequisites

**Pattern:**
```markdown
### Step 0: Verify Prerequisites

1. Source credentials:
   source /path/to/.env

2. Verify config:
   test -f config.local.yaml && grep -q "section:" config.local.yaml && echo "OK"

3. If missing: "Create config.local.yaml from template and fill required fields."
```

**Manufacturing pattern:**
```markdown
### Step 0: Verify Prerequisites

1. Check OPC-UA endpoint connectivity:
   curl -s http://opcua-gateway:4840/status | grep -q "running" && echo "OK"

2. Verify ERP API credentials:
   source /path/to/.env && test -n "$ERP_API_KEY" && echo "OK"

3. If OPC-UA unreachable: "Check gateway status — sensor data will not be available."
```

### 3. Timing & Async Operations

- [ ] Identify all async operations (page loads, API calls)
- [ ] Add explicit waits after each async operation
- [ ] Document wait duration expectations

**Pattern:**
```markdown
Click submit button:
browser_click: { "element": "Submit", "ref": "{ref}" }

Wait for page to load:
sleep 5

Take snapshot:
browser_snapshot
```

### 4. Deterministic Instructions

- [ ] Never use "look for" or "find" without algorithm
- [ ] Specify priority/fallback order for element matching
- [ ] Define success criteria for each step
- [ ] Include "If no match: ask user" fallback

**Pattern:**
```markdown
Find registration button using this priority:
1. Button with text matching: "Register", "Sign up", "Book now"
2. Link with same text patterns
3. Any clickable element with matching text

If multiple matches: prefer button over link.
If no match: ask user to identify element ref.
```

### 5. Input Validation & Security

- [ ] Use `printf '%s\n'` instead of `echo` for user input
- [ ] Validate URL/path format before processing
- [ ] Document security boundaries (automated vs. manual)

**Pattern:**
```bash
# Safe URL sanitization
CLEAN_URL=$(printf '%s\n' "$URL" | sed -E 's/[?&](utm_[^&]*)//g')
```

### 6. Error Handling

- [ ] Document failure modes for each step
- [ ] Provide fallback instructions for each failure
- [ ] Clarify "ask user" questions (what info is needed?)
- [ ] Avoid silent failures

## Quick Reference

| Issue | Bad | Good |
|-------|-----|------|
| Tool names | `browser_navigate` | `mcp__plugin_...__browser_navigate` or ToolSearch |
| Prerequisites | Assume config exists | `test -f config.yaml && grep -q "section:"` |
| Async ops | Click then snapshot | Click, `sleep 3`, then snapshot |
| Element finding | "Look for Register button" | Priority list with fallback to ask user |
| User input | `echo "$URL"` | `printf '%s\n' "$URL"` |

## Reliability Connection

This checklist directly supports the [determinism ladder](agent-reliability.md#the-determinism-ladder) from the Agent Reliability Blueprint. Each checklist item pushes skill steps toward higher rungs:

- **Tool discovery** → ensures deterministic tool resolution (rung 1–2)
- **Prerequisites** → eliminates silent failures from missing config (rung 2)
- **Deterministic instructions** → replaces ambiguous LLM interpretation with explicit algorithms (rung 2–3)
- **Validation** → catches stochastic errors before they cascade (rung 3–4)

## Testing

Before merging a new skill:

1. Have an LLM agent execute it following instructions exactly
2. Verify ToolSearch queries return expected tools
3. Verify prerequisites are checked before use
4. Verify page loads are properly timed
5. Verify no ambiguous instructions cause misinterpretation

## Origin

Derived from reviewing skills where critical issues blocked agent execution despite the skill being perfectly readable by humans. Four P1 (critical) issues were found in a single skill audit — all rooted in the human-vs-agent execution gap documented above.
