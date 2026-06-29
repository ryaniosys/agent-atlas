# Second-Pass QA: Parallel Subagents Eyeball an Artifact Against Its Source

## Pattern

After producing a structured artifact that is *supposed* to be correct — a ground-truth dataset, a data migration, a transcription, a generated config — run a **second, independent pass**: fan out parallel subagents that each open the **authoritative source** and compare it field-by-field against the derived artifact, reporting concrete discrepancies only.

The premise: a single review pass leaks errors, even a careful human one. The producer (model or person) is blind to its own systematic mistakes — a mis-keyed value, a duplicated field, a confusion between two adjacent concepts. A fresh independent reader catches cheaply what the original pass cannot see.

## Structure

```
1. ENUMERATE the artifact set and map each item → its authoritative source
   → e.g. record id → source document path (+ page count)

2. BATCH into groups of ~5-6 items per subagent

3. Launch N PARALLEL SUBAGENTS, each given:
   → the id → source-path map for its batch (so it never has to search)
   → the EXACT field checklist to compare
   → the comparison rules (meaning, not formatting)
   → a strict output contract: per item, "match" or terse "field: artifact=X | source=Y"

4. CONSOLIDATE: collect flags, group by error class

5. VERIFY load-bearing corrections yourself before applying
   → re-open the source for the specific value; never apply a subagent's
     proposed value blind

6. APPLY fixes through the validating schema, with an assertion on prior state
   → back up the artifact first
```

## Key Design Decisions

### Independent fresh eyes, not self-review
The value is in the *independence*. Whoever produced the artifact (an extraction model, a human certifier) shares the blind spot that created the error. A subagent reading only the source and the result has no such investment and flags what the producer normalized away.

### Concrete-discrepancies-only output
Tell subagents to emit a one-line verdict per item (`match`) or a terse bulleted diff (`field: artifact=X | source=Y`). This keeps signal density high, makes the consolidation step trivial, and discourages narration. Demand a strict, parseable contract.

### Compare meaning, not formatting
The single biggest false-positive source. Spell out what is NOT an error: normalized dates, parsed numbers (`1'234.50` → `1234.5`), `null` vs empty string, label/role fields that are intentionally unscored. Without this rule the report drowns in noise and reviewers stop trusting it.

### Map, don't search
Give each subagent the exact item → source-path mapping and field list. If subagents have to discover sources or infer the schema, coverage becomes inconsistent and batching non-deterministic.

### Verify before apply — subagents flag well, value-guess poorly
A subagent reliably tells you *that* a field is wrong, but its proposed *correct value* can be subtly off (a misread letter, a transposed token). For any load-bearing fix, the orchestrator re-opens the source and confirms the exact value itself. Flag = cheap and trustworthy; replacement value = verify.

### Apply through the schema with an assertion
Write fixes via the same validating model/schema the artifact uses, asserting the prior state first (`assert field == old_value`). This re-validates the record, guards against editing the wrong item or stale state, and keeps the on-disk format identical to the producer's output.

## Subagent Configuration

```
Execution: parallel (one subagent per batch of ~5-6 items)
Input: id→source map + field checklist + comparison rules + output contract
Source reading: render ALL pages / the full source, not an excerpt
Output: strict per-item verdict; concrete diffs only; "illegible" not a guess
```

Use a model capable of faithful visual/source reading — the task is careful comparison, not generation.

## When to Use

- Verifying an extraction/ground-truth dataset against its source documents
- Auditing a data migration against the legacy records it came from
- Checking a transcription against the original audio/scan
- Validating generated config/code against the spec it implements
- Any artifact you can place side-by-side with an authoritative source

## When NOT to Use

- No authoritative source to compare against (nothing to verify against)
- The artifact is subjective — there is no single correct answer
- Trivially small N, where one careful pass already suffices
- The source itself is the thing in doubt (verify the source first)

## Anti-Patterns

- **Treating one review pass as final** — human certification and model output both leak errors; the second pass exists precisely because the first is trusted too much.
- **Letting subagents guess** — instruct them to report "illegible/uncertain" rather than invent a value. A confident wrong flag is worse than an honest gap.
- **Applying proposed values blind** — always re-verify load-bearing corrections against the source yourself.
- **Formatting-sensitive comparison** — without an explicit "normalized forms are equal" rule, the report fills with false positives and loses credibility.
- **Editing without a backup** — snapshot the artifact before applying fixes, especially when it represents expensive human-review effort.
- **Loose output contract** — "describe any problems" yields unparseable prose. Specify the verdict format verbatim.

## Why It Compounds

Two things outlast the run. First, the **error classes** the pass surfaces are reusable: recurring confusions become explicit rules for the producer (a prompt constraint, a post-validation check, a UI affordance) so the same class never recurs. Second, the pass itself becomes a **standing gate** — cheap to re-run after every regeneration of the artifact, turning "we think it's right" into "we checked it against the source."

## Example Use Case

A dataset of structured records has just been certified correct by a human reviewing each one. Before using it as the yardstick to score a system, fan out parallel subagents — each handed ~6 records, the matching source-document paths, and the field checklist — to read every source and diff it against the certified record. They surface a handful of errors the human missed, clustering into two or three classes (a field-confusion pattern, an input-corruption pattern). The orchestrator re-verifies each load-bearing fix against the source, applies them through the schema with assertions, and feeds the recurring classes back as producer-side rules so the next batch is right the first time.
