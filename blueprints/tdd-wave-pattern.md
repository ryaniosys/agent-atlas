# TDD Wave Pattern for Multi-Agent Code Changes

> **Status:** Production-tested pattern for TDD with parallel subagents.
>
> **Last updated:** 2026-03-13

## The Problem

When an agent writes both tests and implementation, it can subtly adjust tests to match its output rather than the spec. This creates false confidence — tests pass, but the intent is wrong. Additionally, implementation agents that add parameters with permissive defaults can create "silent success" where all tests pass but callers never forward the values.

## The Pattern: Three Waves

```
Wave 1 (parallel)
├── Test Agent ──→ writes failing tests from spec
├── Housekeeping Agent ──→ independent cleanup tasks
└── Research Agent ──→ gather context (optional)

Wave 2 (sequential, after Wave 1)
└── Implementation Agent ──→ modifies production code to pass tests

Wave 3 (main agent)
└── Verify ──→ run full suite, catch wiring gaps, fix integration seams
```

### Why Three Waves?

| Wave | Purpose | Key Constraint |
|------|---------|----------------|
| 1 | Define expected behavior as tests | Tests must be written from the spec, not the code |
| 2 | Make tests pass | Implementation agent cannot modify test files |
| 3 | Catch what agents missed | Main agent has full context both agents lacked |

Wave 3 is not optional. The implementation agent works in isolation — it doesn't see the caller context. It will add parameters with defaults that satisfy unit tests without actually being wired through.

## The "Silent Success" Anti-Pattern

When extracting functions, implementation agents often add parameters with safe defaults:

```python
def process_document(file_path, result, cfg, conn,
                      *, doc_id: int = 0, fhash: str = ""):
    if not fhash:
        fhash = compute_hash(file_path)  # fallback recomputes
```

All tests pass because the default triggers fallback behavior. But the caller still does:

```python
# Bug: doc_id and fhash not forwarded
new_name = process_document(file_path, result, cfg, conn, client)
```

**Fix**: Wave 3 catches this by running integration tests that verify parameter forwarding end-to-end.

**Prevention**: Write integration tests that assert the caller passes expected values, not just that the callee works with defaults:

```python
def test_orchestrator_forwards_hash(self):
    with patch("process_document") as mock_fn:
        orchestrate(pdf, cfg, conn, api_client)
    _, kwargs = mock_fn.call_args
    assert kwargs.get("fhash")  # must be non-empty
    assert kwargs.get("doc_id") == 10  # from upload
```

## When to Use

- Non-trivial refactors (3+ functions changing)
- Extracting shared functions (SPOT compliance)
- Code review finding resolution (batch fixes)
- Any change where test coverage matters more than speed

## When NOT to Use

- Simple bug fixes (1-2 lines)
- Documentation-only changes
- Config changes
- Single-file changes where test + impl are trivial

## Practical Tips

1. **Test agent gets the spec, not the code**: Describe what functions SHOULD do, not what they currently do. The test agent writes from intent.

2. **Implementation agent cannot touch test files**: Hard constraint. If a test seems wrong, the impl agent must make the code match the test, not vice versa.

3. **Conftest refactoring goes in Wave 1**: Moving shared helpers to `conftest.py` is a test-only change. Do it before writing new tests so they use the shared helpers.

4. **Group findings by file conflict**: If 6 of 9 findings touch the same file, they must be in the same agent — not parallel agents that create merge conflicts.

5. **Run full suite in Wave 3**: Not just the files you changed. A wiring fix in one function broke an integration test in a completely different test file.

## Real-World Results

First deployment (9 code review findings across a document processing pipeline):
- Wave 1: 63 existing tests pass + 11 new failing tests written
- Wave 2: All 74 tests pass after implementation
- Wave 3: Caught 2 wiring gaps (parameter forwarding + stale test file)
- Final: 548/548 tests pass, 0 failures

## Related Patterns

- [Write-Ahead Idempotency](write-ahead-idempotency.md) — protecting non-idempotent external calls
- [Agent Reliability](agent-reliability.md) — broader agent robustness principles
