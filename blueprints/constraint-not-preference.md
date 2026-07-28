# Constraint, Not Preference

> When a skill lets a model act on a human's reply, forbidding it to leave the list does not stop it substituting *within* the list. And once you add an override, it becomes the substitution route unless you design against that.

## The Problem

A common and sound architecture: deterministic code decides *what is possible*, a model
reads the human's free-form reply and maps it onto that set, deterministic code executes.
The model never chooses; it only interprets. The usual guardrail is some version of:

> Never invent an option that is not in the list.

That rule is necessary and insufficient. It stops the model leaving the list. It does not
stop it **moving within** the list, which is the same failure wearing a different hat.

A worked case: an agent posts a numbered list of bookable options. The human replies
*"book the noon one if possible"*. Noon is unavailable. The model books the 16:30 entry
instead and reports it as done.

Every stated rule held. The entry was on the list, the index resolved, nothing was
invented. And the model had still made a selection decision - precisely the thing the
architecture said it must never do. "If possible" was a **condition**; it was read as a
**preference**.

## Why It Happens

Helpfulness. A model asked to book something, faced with the requested option being
unavailable and a near-neighbour being available, will resolve the tension toward
completing the task. The failure is invisible in the output, because the report reads
like success: *"Booked the 16:30 session."* Nothing signals that this is not what was
asked for.

The deterministic layer cannot catch it either. From the code's perspective it received a
valid index for a valid entry and executed correctly.

## The Pattern

### 1. Name the second rule explicitly

"Never invent one" and "never substitute one" are different rules. Write both.

> A named time, class, condition or qualifier ("noon", "the Advanced one", "if possible",
> "if there's a morning slot") is a **constraint, not a preference**. If nothing in the
> list satisfies it, report that and act on nothing for that item.

### 2. Make reporting the successful outcome

An unsatisfiable request is not a failure to be worked around. Say what *is* available and
let the human choose. The skill should treat "I could not do that, here is what exists" as
a complete, correct response.

### 3. Put the transcript in the skill

An abstract rule is much weaker than the exchange that broke it. Include the real failing
reply, the wrong action, and the correct response side by side. Models follow worked
examples more reliably than they follow prose.

## The Override Trap

Users legitimately want to override - "I know it conflicts, do it anyway". The moment you
add that path, it becomes the mechanism the model reaches for when a request cannot be
satisfied, quietly reintroducing the defect you just fixed.

Five things that keep them separate:

**Subordinate the override to the rule.** Document it *inside* the no-substitution
section, not beside it, framed as what the human invokes **after** the model has reported
the failure. Placement is instruction.

**Trigger on words, never on inference.** Give explicit "Fires" and "Does not fire"
tables. Fires on *anyway*, *regardless*, *override*, *"I'll move the meeting"*. Does not
fire on the original request, on a question, or on the human agreeing with your own
report.

**Add a tiebreaker for the ambiguous middle**, since that is where the drift lives:

> If you are weighing whether the reply counts as an override, it does not.

**Show two exchanges that differ by one sentence.** Same listing, same data, same
availability - one runs the override, one does not, and the difference is a sentence the
human wrote. Then say that explicitly: *nothing about the options changed between them.*

**Keep informational output informational.** A "here is what else exists, and why each
was excluded" listing must be marked as an answer, not an offer. Otherwise listing four
options and booking one becomes the same substitution mistake in a new costume. Where
possible, remove the affordance: that listing carried **no numbering at all**, so there
was nothing to select.

### Also: constrain the blast radius of the override itself

Decide deliberately which invariants an override may cross. In the worked case it
bypassed every *selection* rule - conflicts, spacing rules, quotas, allowlists - because
the human had named the exact item, but it could never bypass the **safety** rules that
prevented spending money. It also reported everything it overrode, so a mistyped
identifier surfaced immediately instead of silently doing something unintended.

## When This Applies

Any skill where a model interprets human intent over a bounded set and deterministic code
executes: approve/reject flows, triage, routing, scheduling, anything with a numbered list
and a free-text reply.

It does **not** apply where the model is meant to exercise judgement over the options.
That is a different architecture with different guardrails - the point here is that if
you have decided the model does not choose, "don't invent" alone will not hold that line.

## The Honest Summary

The boundary you are defending is not "stay inside the set". It is "do not decide". Those
sound identical and are not, and the gap between them is where a helpful model will act.
