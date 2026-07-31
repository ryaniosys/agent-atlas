# Selection Is Not Adjudication

> A signal too weak to judge one entity can still be strong enough to choose which entities to look at. The two uses have different error costs, so a signal that fails as a judge should be measured again as a selector before it is discarded.

## The Problem

An enrichment or scoring pipeline acquires a new external signal: a directory, a
registry, a membership list, a public dataset. The obvious next question is "how
accurate is it?", so the signal gets evaluated as a **judge**: given one entity, does
this signal tell us the truth about it?

Very often the answer is the same disappointing shape:

- **Not necessary.** Absence proves nothing. Plenty of qualifying entities are missing
  from the list.
- **Not sufficient.** Presence proves nothing either. The list contains entries that
  clearly do not qualify.

Two responses follow, and both are incomplete:

1. **Discard it.** "Neither necessary nor sufficient" reads as "useless".
2. **Hedge it down.** Keep it, but weight it so low, and freeze on so many conditions,
   that its measured effect on any individual record rounds to nothing.

Hedging is usually the *correct* call for the judging use. The mistake is treating that
conclusion as final, because the signal has a second job with a completely different
error profile.

## The Asymmetry

| | Adjudication | Selection |
|---|---|---|
| Question it answers | "Is this entity X?" | "Which entities should we look at next?" |
| Output goes into | a curated record humans trust | the ordering of a work queue |
| Cost of one error | a wrong value written into that record | one wasted unit of work |
| Error visibility | low; a wrong field looks like a right field | high; it shows up as throughput |
| Error persistence | until someone notices and corrects it | gone after the item is processed |
| Blast radius | every downstream consumer of the field | that one item |

A wrong adjudication is expensive because it is **durable and quiet**. It contaminates
a record that other systems and people treat as ground truth, and nothing about the
record announces that it is wrong.

A wrong selection is cheap because it is **transient and loud**. The entity gets looked
at, fails whatever real evaluation follows, and is dropped. The only cost is the work
spent looking. If that happens often, throughput says so.

So the same 80%-accurate signal can be simultaneously too weak to write with and
plenty strong enough to sort with.

## Worked Case

A pipeline classifies companies in a CRM and writes firmographic fields. A new source
arrives: an industry-association member directory, joined to the CRM by domain.

**As an adjudicator** it disappoints exactly as above. Association membership is not
required to be a manufacturer, and the directory also carries a training academy and
a couple of holding entities. Measured agreement with the real classification is around
80%. The pipeline ends up hedging it hard: a small score contribution, and a freeze
whenever the source contradicts the model. Correct, and nearly invisible in effect.

**As a selection input the same directory is the most valuable thing in the pipeline.**
Roughly three quarters of the directory's members were not in the CRM at all. The
non-CRM members with a resolvable domain formed a pre-filtered candidate list about
two thirds the size of the entire existing CRM.

The pipeline's candidate query, meanwhile, was "records already in the CRM that have
the identifier we need and have not been assessed recently". **The CRM was the
ceiling.** An excellent-fit company nobody had heard of could not become a candidate,
no matter how well it fit.

The wrong entries cost nothing worth defending against. Classifying a training academy
and discarding it costs one classification. Writing "manufacturer" onto that academy's
CRM record costs a wrong field that some later prep document, score or outreach list
will quietly believe.

## The Rule

**When a signal fails the adjudication test, run a second measurement before discarding
it: how much would it change the candidate pool?**

The two measurements are different and neither substitutes for the other:

- **Adjudication quality** is measured per entity: agreement rate, precision, recall
  against a known label.
- **Selection value** is measured over the pool: how many candidates does this signal
  add that the current query cannot see, and what fraction of them are plausible?

A signal can score badly on the first and be transformative on the second, because
selection value scales with *coverage* while adjudication value scales with *accuracy*,
and those are independent properties.

## Two Traps

**1. The pool is often the real constraint, not per-item accuracy.** Teams tune the
classifier because that is the visible, interesting part. But if the candidate query
draws from a set that is one twenty-fifth of the addressable universe, no amount of
classifier improvement reaches the other 96%. Measure the pool before tuning the judge.

**2. Widening selection while a downstream gate is throttling just scales the waste.**
If a write gate is currently discarding most of what reaches it, multiplying the
candidate count multiplies the discarding, not the value. Sequence the gate measurement
first, or measure both together and report yield per candidate rather than raw
candidate count.

The second trap is the more expensive one, because a widened funnel *looks* like
progress. Throughput goes up. Cost goes up. Delivered value does not move.

## How To Tell Which Use You Are In

One question separates them:

> Does this output get written into a record that a human or another system will later
> treat as fact, or does it only reorder a queue whose items are all going to be
> evaluated properly anyway?

If it is written, you are adjudicating and the accuracy bar is high. If it only orders
work, you are selecting and the bar is "better than random, cheap to be wrong".

Beware of the middle case: a queue that nobody re-evaluates is not a queue, it is a
record. If items are processed straight from the ordering without an independent check,
the selection has quietly become an adjudication and needs the higher bar.

## Checklist

- [ ] For each external signal, state which use it is for: judging, selecting, or both.
- [ ] Measure adjudication quality per entity, and selection value over the pool. Do not
      let one number stand in for the other.
- [ ] Before discarding a "neither necessary nor sufficient" signal, measure how many
      candidates it adds that the current query cannot see.
- [ ] Write down what the candidate query's ceiling actually is. If the pool is the
      existing record set, say so explicitly, because it is easy not to notice.
- [ ] Check for a throttling gate downstream before widening the pool. Report yield per
      candidate, not candidate count.
- [ ] Confirm that queue items really are independently evaluated. If they are not, the
      selection needs adjudication-grade accuracy.

## See Also

- [decision-log-learning-loop.md](decision-log-learning-loop.md): logging the decision
  stream is what makes the pool-versus-accuracy measurement possible after the fact.
- [ground-truth-qa-eyeball.md](ground-truth-qa-eyeball.md): how to get the labels the
  adjudication measurement needs.
