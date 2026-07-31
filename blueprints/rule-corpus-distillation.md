# Rule Corpus Distillation

> **Status:** Production-tested. Deployed across a multi-repo agent ecosystem, 2026-07.
>
> **Last updated:** 2026-07-31

A pattern for keeping an agent's accumulated behavioural rules correct, small and enforced, once
those rules live in more than one repository.

## The Problem

Per-session capture works. An end-of-session skill writes what it learned into that repo's memory
store, and the next session in that repo starts smarter. Run it for six months across a dozen repos
and three things have gone wrong, none of them visible from inside a single session:

1. **The same rule exists in five stores, worded five ways.** Each capture was locally correct. No
   pass ever read across repos, so nobody noticed. One corpus reached 268 rule files, of which 48
   were restatements of a handful of rules.
2. **Rules that get violated keep getting reworded rather than enforced.** A rule can be loaded in
   context for a whole session and violated anyway, because prose is consulted at decision points
   and much generation has no decision point. Rewriting it produces a better sentence, not better
   behaviour.
3. **The corpus only grows.** Nothing retires a rule that stopped mattering, so the always-loaded
   context bill rises forever and the important rules get buried among the dead ones.

## The Pattern

Add a second, low-frequency loop above per-session capture, and give it three ratchets.

```
 session ──► capture skill ──► repo memory ──┐
    ▲                                        │ signals
    │                                        ▼
    │                                  threshold tripped?
    │                                        │ yes
    │                                        ▼
    └──── global rule files ◄──── distillation pass ──► mechanical gate
                    │                                   (hook / test / lint)
                    └──► append-only deletion log
```

| Signal | Ratchet |
|---|---|
| Same rule present in 2+ repo stores | **Elevate** into a global rule file, delete the leaves, repoint references |
| Rule violated again since its last rewrite | **Gate it.** Move it from prose into the tool path |
| Rule with no violations and no references for N months | **Prune**, or demote to the one repo where it still applies |

Elevation without pruning is how the always-loaded files become the next bloated index. The three
ratchets only work together.

## Mechanics that matter

**Split the global layer by audience, not by topic.** One file for how the agent works with its
principal, one for engineering standards. The engineering half is then portable to other executors
(a coding agent, a CI bot, a subagent prompt); the behavioural half is not. Splitting by topic buys
nothing if both files load unconditionally anyway.

**Split each rule from its mechanics.** The global file owns the principle in one or two lines. The
repo memory keeps the commands, recipes and tool quirks. Without this the global files inherit every
detail that made the original memory long, and the budget is gone in a month.

**Measure before judging.** Two mechanical passes, no model:

- *Clustering.* Token-set overlap plus exact-sentence collision across every memory file. Report
  only clusters spanning 2+ repos. Normalise repo identity first: if the same repository appears
  under two directory spellings, every pair looks cross-repo and the pass reports phantom
  duplicates forever.
- *Violation counting.* Extract correction-shaped user turns from session transcripts and map them
  onto rule ids. Keep the matcher crude: its output is a candidate list for judgement, not a
  verdict. Selection is not adjudication, a wrong pick costs one wasted look.

**A rule cannot be violated before it was written.** Count violations only from transcripts newer
than the rule's own timestamp, and reset the counter whenever the rule is rewritten. Otherwise every
new rule is born looking violated by the very history that produced it, and the gate ratchet fires
on noise.

**Scan incrementally, with an overlap sentinel.** Read everything past the watermark plus the single
most recently scanned transcript. If the sentinel's corrections stop being found, the extractor
broke rather than the input going quiet. A watermark with no overlap cannot tell those apart.

**Rule identity must be stable.** References from memories and indexes point at a rule by number, so
renumbering silently breaks them. New rules go at the end of the file; identity is the number,
version is a hash of the body.

**Log before deleting.** Every removed rule file goes into an append-only recovery log with its full
body and the destination it was elevated to. That log is what makes the whole pass safe to run
aggressively.

## Order of operations for one distillation

1. Append the full body of every doomed file to the recovery log.
2. Edit the global rule file. Add at the end, keep numbers stable.
3. Delete the absorbed files.
4. Repoint references. Expect two link syntaxes: wiki-style inside bodies, markdown links in
   indexes. Sweeping one and not the other leaves half the corpus dangling.
5. Rewrite each repo's memory index, leaving one line that says where the cross-repo rules went.
6. Verify zero dangling references mechanically before reporting anything done.
7. Stamp the run and clear the violation counters.

Every step is recoverable only if the one before it happened, which is why the log is first.

## Failure Modes

| Failure | Symptom | Fix |
|---|---|---|
| Elevating without pruning | Global files grow past their budget, rules get skimmed | Budget guard hook plus the dormancy ratchet |
| Trusting the matcher | Rules rewritten because a crude keyword hit said so | Matcher output is a candidate list, a human or a judgement pass decides |
| Counting historical violations | Every rule looks broken the day it is written | Gate counting on the rule's own timestamp |
| Deleting before logging | A nuance is gone with no way to tell what was lost | Append-only log as step 1 |
| Renumbering rules | References across the corpus point at the wrong rule, silently | Append-only numbering |
| Same repo under two directory spellings | Permanent phantom cross-repo clusters | Normalise repo identity in the clusterer |

## When To Use

Worth building when **all three** hold: rules are captured per session, they live in 3+ separate
stores, and the always-loaded context has a real budget. Below that, a single memory file and a
periodic manual read are cheaper than the loop.

## Related

- `enforcement-hooks.md` - what a rule becomes when it graduates out of prose
- `continuous-improvement-skill-loop.md` - the per-cycle loop this sits above
- `selection-vs-adjudication.md` - why the crude matcher is acceptable
- `living-reference-doc.md` - keeping the referenced detail out of the always-loaded layer
