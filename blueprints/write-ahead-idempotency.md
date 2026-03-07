# Write-Ahead Idempotency for External API Calls

> **Status:** Production-tested pattern for protecting non-idempotent external calls in agent pipelines.
>
> **Last updated:** 2026-03-05

## The Problem

Agent pipelines often chain local operations with external API calls. If the process crashes mid-pipeline, retrying can create duplicates in the external system — duplicate files, duplicate records, duplicate charges.

Some APIs offer built-in dedup (e.g., idempotency keys, HTTP 409 on re-upload), but many don't. The agent needs crash-safe idempotency without relying on the remote API.

```
Local DB write → External API call → Local DB update
                       ↑
              crash here = duplicate on retry
```

## The Pattern: Write-Ahead Record

Insert a record with a "pending" status **before** the non-idempotent external call. On retry, detect the pending record and skip the external call.

### State Machine

```
(no record) ──[pre-upload]──→ uploading ──[complete]──→ done
                                  ↑
                    (retry finds 'uploading')
                     → skip external call
                     → complete locally
                     → update to 'done'
```

### Implementation

```python
# 1. Check existing state
record = get_record(db, content_hash)

if record is not None:
    if record.status == "done":
        return "duplicate"
    if record.status == "uploading":
        # Recovery: skip external call, complete locally
        logger.warning("Recovering — external upload may be missing. Verify manually.")
        complete_record(db, content_hash)
        return "recovered"

# 2. Write-ahead: record intent before external call
insert_record(db, content_hash, status="uploading")
db.commit()  # must be durable before the external call

# 3. Non-idempotent external call (now protected)
external_api.upload(file)

# 4. Complete
update_record(db, content_hash, status="done")
db.commit()
```

### Schema

```sql
-- Add to existing tracking table
ALTER TABLE processed_items ADD COLUMN status TEXT NOT NULL DEFAULT 'done';
```

Existing rows get `status='done'` via DEFAULT. No data migration needed.

### Recovery Function

Use a targeted UPDATE for recovery instead of a full upsert — this preserves metadata (category, timestamps) that was captured during the write-ahead phase:

```python
def complete_record(db, content_hash: str) -> None:
    cursor = db.execute(
        "UPDATE processed_items SET status = 'done', completed_at = ? WHERE content_hash = ?",
        (int(time.time()), content_hash),
    )
    if cursor.rowcount == 0:
        raise ValueError(f"No record found for {content_hash!r}")
```

## When to Use This

**Use when ALL of these are true:**
- The external API has no idempotency mechanism (no idempotency keys, no dedup)
- The external call has side effects (creates resources, sends messages, charges money)
- You already have a local database for tracking state
- Retrying the external call would create unwanted duplicates

**Manufacturing example:** Reporting a non-conformance to an external quality system (SAP QM, MES). The agent detects an out-of-spec measurement, creates a write-ahead record locally, then posts the NCR to SAP. If the process crashes after the SAP call but before local completion, retry finds the pending record and skips the duplicate NCR creation.

**Don't use when:**
- The external API supports idempotency keys — just use those
- The external API deduplicates naturally (e.g., HTTP 409 on conflict)
- The operation is naturally idempotent (PUT, DELETE by ID)
- You don't have a local database — add one or use a different pattern

## Edge Cases

| Scenario | Behavior | Acceptable? |
|----------|----------|-------------|
| Crash after external call, before `done` | Retry finds `uploading`, skips external call, completes locally | Yes — external call succeeded, local state catches up |
| Crash after write-ahead, before external call | Retry finds `uploading`, completes locally. **External system never received the data** | Depends — log a WARNING so operators can verify |
| Concurrent processes on same item | First inserter wins (UPSERT), second sees `uploading` and skips | Yes — but consider advisory locks if concurrency is common |
| Stuck `uploading` record | Operator clears with `DELETE WHERE status='uploading'` | Yes — if DB is a rebuildable cache |

The key trade-off: **crash between write-ahead and external call** means the external system missed the data. For most agent pipelines, a WARNING log + manual verification is the right trade-off. The alternative (always re-uploading in recovery) defeats the pattern's purpose and creates the duplicates you're trying to prevent.

## Hardening

### Validate status values

Prevent silent bugs from typos:

```python
_VALID_STATUSES = {"uploading", "done"}

def insert_record(db, content_hash, *, status="done"):
    if status not in _VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}")
    # ... INSERT
```

### Use a NamedTuple for query results

Avoid fragile positional indexing:

```python
from typing import NamedTuple

class ProcessedRecord(NamedTuple):
    status: str
    filename: str
    category: str | None
```

### Log warnings on recovery

The recovery path should always warn — the operator needs to know an external upload may have been skipped:

```python
if record.status == "uploading":
    logger.warning("Recovering %s — external upload may be missing. Verify manually.", item_id)
```

### Log warnings on unexpected status

If the status field ever holds a value outside your state machine, log it and fall through to reprocessing (safest default):

```python
logger.warning("Unexpected status %r for %s, treating as unprocessed", record.status, item_id)
```

## Design Decisions

**Why not track every pipeline step?** Most pipeline steps are either idempotent or have their own dedup. One checkpoint before the single non-idempotent step is sufficient. Adding more checkpoints increases complexity without proportional safety.

**Why not store the external system's response ID?** Only add columns when a consumer exists. If no code reads the external ID today, don't store it (YAGNI). Add it when a reconciliation tool needs it.

**Why not add a staleness timeout for pending records?** If the DB is a rebuildable cache, stuck records are trivially cleared with a DELETE. Time-based recovery logic adds complexity for a scenario that requires operator judgment anyway.

**Why a separate recovery function instead of reusing the upsert?** The upsert overwrites all fields. The recovery path may not have all the original metadata (it was captured during write-ahead). A targeted `UPDATE SET status='done'` preserves existing data.

## Related

- [Agent Reliability Blueprint](agent-reliability.md) — why per-step reliability matters in agent chains
- [Secrets Management](secrets-management.md) — protecting API credentials used in external calls
