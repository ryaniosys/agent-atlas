# An Approval Must Write State

> **Status:** Production-tested. Derived from a live incident where a human approved four
> items, the agent did the work in a way that produced no record, and the next day's run
> asked for the same approval again.
>
> **Last updated:** 2026-07-30

## The Problem

A recurring agent shape: a scheduled job proposes items, a human approves them in chat, and
a deterministic command executes the approval.

```
job proposes  ->  human replies "do 1,3"  ->  approve command executes
                                              ^ creates the thing
                                              ^ AND stamps the source record
```

The stamp is easy to read as bookkeeping. It is not. **It is the only durable evidence the
human ever said yes.** The created artifact lives in an external system; the ledger entry is
what the *next* run reads.

So there are two independent ways this loop silently reverts:

1. **The agent reaches the goal by another route.** It creates the items with a hand-written
   API call instead of the approve command. Even when that works, no stamp is written, so
   the next run re-proposes everything. The human sees their approval ignored.
2. **A correction lands after the record was written.** The human corrects a term, the fix
   reaches future inputs, and every already-stored record keeps the old wording forever.

Both look identical from the outside: *the agent ignored what I told it.*

## Why It Happens

**The side effect feels like the point.** "Create four tickets" sounds complete when four
tickets exist. Whether the ledger knows they exist is invisible until tomorrow. Nothing fails
loudly, so the failure surfaces a day later as a repeated question.

**The bypass route is usually more discoverable than the sanctioned one.** A general-purpose
API helper is in the agent's context for many tasks. A narrow `approve` command is in exactly
one skill. When the model is weak, tired of a long prompt, or the sanctioned command errors
once, the general tool is right there. Skill prose saying "always use X" competes with a tool
that is simply present.

**Corrections are modelled as input filters.** Terminology fixes are naturally applied where
data enters. Records already stored were written by a past run and nothing re-reads them, so
"apply the correction" quietly means "apply it to the future".

## The Pattern

### 1. Treat the state write as the deliverable

The approval command must do both, and the artifact without the stamp is a failed run, not a
partial success. Store enough to answer later questions:

```python
# not just: created_id
record["approved_artifact"] = {
    "id": issue["id"],
    "url": issue["url"],
    "title": issue["title"],   # what it was created AS
}
```

Storing the title as-created is what later lets you detect that a correction has made the
live artifact's name stale.

### 2. Put the refusal in the door you do not want used

Prose in the sanctioned path cannot stop a model that never reads it. The bypass path can:

```python
def assert_not_a_staged_proposal(title, pending_file=PENDING):
    """Refuse to create something the proposal loop already staged."""
    for entry in load(pending_file):
        if similarity(title, entry["title"]) >= 0.5:
            raise StagedProposalError(
                f"Refusing: {title!r} matches a staged proposal "
                f"({entry['id']}). File it with: <the sanctioned command>. "
                "Only that path records the approval. If it errors, report "
                "the error - do not create it here."
            )
```

Three properties matter more than the matching logic:

- **The error names the correct command.** A refusal that only says no invites a third route.
- **It says what to do when the sanctioned path fails.** Otherwise the first error becomes
  justification for the bypass, which is exactly how the original incident ran.
- **It fails open on its own errors.** A guard protecting one flow must never become a new
  way for unrelated work to break. Wrap it so a malformed state file cannot block anything.

Deliberately **no override flag**. A false positive means the request is close enough to a
staged item to risk a duplicate, so the sanctioned path is the right answer anyway. An
override becomes the substitution route the moment the guard is inconvenient.

### 3. Make corrections rewrite stored state, at the moment of approval

Apply the correction where the human vouches for it, not only where data enters:

```python
def correct_stored_records(ledger, corrections):
    """Re-apply the full correction set to open records. Pure and idempotent."""
```

Design notes that turned out to matter:

- **Apply the whole correction set, not just the new batch.** The pass is idempotent, so
  re-applying everything also heals records that predate an older correction. A repair to the
  correction source then self-heals on the next scheduled run, with nobody asking.
- **Cover every entry point.** If corrections can enter by two doors (an explicit approval
  *and* an auto-accept path), wiring only the obvious one leaves the same bug alive in the
  other. In the source incident the second door was found only after the first was fixed.
- **Leave closed records alone.** Their text is history.
- **Give the destination argument no default.** A path like `--ledger` with a sensible default
  is a forgotten flag away from rewriting production state during a test run.

### 4. Surface, do not silently repair, anything already published

When a correction implies an externally visible artifact is now misnamed, report it and let a
human trigger the rename:

```
stale_titles: [{id, current, suggested}]     # from the approval command
retitle --ids ID1,ID2                        # separate, explicit, no --all
```

Rewriting stored state is bookkeeping. Renaming something other people are looking at is an
outward-facing act, and it should stay a choice.

## Testing It

The failure mode hides from ordinary tests, because everything passes when the *sanctioned*
path is exercised. Test the shapes that actually broke:

- The approve command **stamps the record**, not merely that it returned an id.
- The bypass door **refuses** a staged item, **allows** an unrelated one, and **allows
  everything** when its state file is missing or malformed.
- A correction approved *after* a record was written reaches that record.
- Re-running the correction is a no-op the second time.

One more, learned the hard way: assert the **exact payload** your code sends to an external
API, not that some identifier appears somewhere in the request. A mock asserting a substring
of the request passes for both the working and the broken request shape, and will keep a
production-broken call green indefinitely.

## When This Applies

Any loop where a human's decision is captured in one system and acted on in another:
approve-to-create, approve-to-send, approve-to-deploy, terminology or glossary approvals,
triage decisions replayed by a later run.

The tell is a scheduled job that re-asks something a human already answered. Before adjusting
the prompt, check whether the answer was ever written down.

## The Honest Summary

An approval is not a side effect, it is a fact that must be recorded. If the only trace of a
human saying yes lives in an external system's object, the loop has no memory of the decision
and will ask again. And when a model can reach the goal by a route that skips the recording
step, the route itself has to refuse, because instructions to prefer the other route are
advice, and advice competes with whatever tool is closest to hand.
