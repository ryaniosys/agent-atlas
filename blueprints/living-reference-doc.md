# Living Reference Doc Pattern

> **Status:** Production-tested pattern for decoupling external knowledge from skills.
>
> **Last updated:** 2026-03-25

## The Problem

Skills that depend on external knowledge (API behavior, vendor documentation, protocol specs, machine interface docs) tend to embed that knowledge inline. When the external source changes, every skill that references it needs a rewrite. Worse, the embedded knowledge carries no provenance: you can't tell when it was last verified or where it came from.

In manufacturing and industrial contexts, this is especially painful. PLC communication protocols evolve across firmware versions. ERP vendor APIs add fields between releases. Machine spec sheets get revised when hardware is upgraded. A skill that hardcodes OPC UA node IDs or REST endpoint schemas becomes stale the moment the shop floor changes.

## The Pattern

Extract external knowledge into a standalone **living reference doc** that skills read at runtime. The doc carries its own metadata, verification instructions, and source links.

### Structure

```markdown
---
last_checked: 2026-03-25
sources:
  - url: https://vendor.example.com/api/v3/docs
    description: Official REST API reference for shop-floor gateway
  - url: https://opcfoundation.org/developer-tools/documents/
    description: OPC UA specification (Part 8 - Data Access)
---

# Shop-Floor Gateway API Reference

## Authentication
Bearer token via `/auth/token` endpoint. Tokens expire after 3600s.
Refresh with grant_type=refresh_token (added in firmware v2.4).

## Endpoints

### GET /machines/{id}/status
Returns current machine state. Response includes:
- `state`: enum [RUNNING, IDLE, FAULT, MAINTENANCE]
- `cycle_time_ms`: current cycle time in milliseconds
- `oee`: real-time OEE percentage (0-100)

### POST /machines/{id}/orders
Links a production order to a machine. Required fields:
- `order_id`: string (ERP order reference)
- `quantity`: integer
- `priority`: enum [NORMAL, URGENT, EXPEDITE]

Note: `EXPEDITE` priority was added in gateway firmware v3.1.
Earlier versions reject it with HTTP 422.

---

## Maintenance

### How to re-verify this document
1. Check the vendor changelog at {url} for API updates
2. Compare endpoint schemas against this doc
3. Test authentication flow against staging gateway
4. Update `last_checked` in frontmatter
5. If endpoints changed, update the relevant sections and
   notify dependent skills by grepping for this filename

### Known quirks
- The `/machines/{id}/status` endpoint returns HTTP 200 with
  an empty body (not 404) when the machine ID doesn't exist.
  Skills must check for empty response, not status code.
```

### Key Elements

| Element | Purpose |
|---------|---------|
| `last_checked` frontmatter | Shows when a human or agent last verified accuracy |
| `sources` array | Links to authoritative external docs for re-verification |
| Structured knowledge body | Formatted for agent consumption (tables, enums, field lists) |
| Maintenance section | Step-by-step instructions for re-verifying the entire doc |
| Known quirks | Gotchas discovered through use, not documented upstream |

## How Skills Reference It

A skill's instruction file simply reads the reference doc at runtime:

```
## Dependencies
Read `docs/references/shop-floor-gateway-api.md` before making any
gateway API calls. Pay attention to the "Known quirks" section.

Do NOT hardcode endpoint schemas. The reference doc is the
single source of truth for gateway behavior.
```

Multiple skills can reference the same doc. When the gateway firmware is upgraded, you update one file and every skill that reads it picks up the change.

## Manufacturing Examples

### PLC Protocol Reference
A reference doc for Siemens S7 communication:
- Supported data block types and addressing formats
- Connection pooling limits per PLC model
- Byte-order quirks for REAL vs DINT types
- Re-verification: check against TIA Portal release notes

### ERP Integration Reference
A reference doc for your ERP system's REST API:
- Order creation endpoint and required fields
- BOM structure format (flat vs nested, version differences)
- Rate limits and retry behavior
- Re-verification: compare against vendor's API changelog

### Machine Spec Index
A reference doc cataloging CNC machine capabilities:
- Axis counts, travel limits, spindle speed ranges
- Supported G-code dialects per controller model
- Tool changer capacity and indexing behavior
- Re-verification: cross-check with machine datasheets after maintenance

## Benefits

1. **Single update point**: Change one doc, all dependent skills stay current. No skill rewrites needed when an API adds a field or deprecates an endpoint.

2. **Self-documenting**: The doc carries its own provenance (when checked, where sourced) and its own verification instructions. A new team member can re-verify without tribal knowledge.

3. **Portable across machines**: Reference docs are plain markdown files. Sync them via cloud storage and every workstation has the same knowledge base.

4. **Audit trail**: Git history on the reference doc shows exactly when knowledge changed and why. The `last_checked` field flags staleness at a glance.

5. **Separation of concerns**: Skills define behavior (what to do). Reference docs define context (how the external world works). Neither needs to know the other's internals.

## When to Use

- External API that changes across versions (vendor upgrades, firmware updates)
- Vendor documentation that's incomplete or has undocumented quirks
- Protocol specs referenced by 2+ skills
- Machine or device specs that change with hardware revisions
- Any knowledge that has a "shelf life" and needs periodic re-verification

## When NOT to Use

- Static configuration (use config files instead)
- Internal logic that changes with your own code (just update the code)
- One-off knowledge used by exactly one skill (embed it; extraction adds overhead)
- Secrets or credentials (use env vars and secret management)

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Do This Instead |
|-------------|---------------|-----------------|
| Copy-paste into every skill | N skills to update when the API changes | Single reference doc, N skills read it |
| No `last_checked` date | Can't tell if info is 2 weeks or 2 years old | Always include frontmatter with date |
| No sources | Can't re-verify without knowing where to look | Always link to authoritative upstream docs |
| No maintenance section | Next person doesn't know how to re-check | Write step-by-step verification instructions |
| Mixing reference + skill logic | Doc becomes coupled to one skill's workflow | Keep reference docs pure knowledge, no behavior |

## Freshness Workflow

For high-change environments (e.g., a gateway API that ships monthly firmware updates), consider a periodic review cadence:

1. **Weekly or monthly**: Agent checks `last_checked` dates across all reference docs
2. **Flag stale docs**: Anything older than the review threshold gets flagged
3. **Re-verify**: Follow each doc's maintenance section to check for upstream changes
4. **Update or confirm**: Either update the doc content or bump `last_checked` to confirm it's still accurate

This can be triggered manually or integrated into a recurring review workflow.

## Related Patterns

- [Skill Authoring Checklist](skill-authoring-checklist.md) — broader checklist for skill design
- [Continuous Improvement Skill Loop](continuous-improvement-skill-loop.md) — feeding learnings back into skills
- [Secrets Management](secrets-management.md) — what NOT to put in reference docs
