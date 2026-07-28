# Spec-Defect Blindness

> A passing test suite proves the code matches the specification. It says nothing about whether the specification is right - and when it is wrong, the tests encode the error faithfully and completely.

## The Problem

You build an agent test-first. Every requirement gets tests. Every test passes. You ship
it, and on its first run against real data it does nothing useful at all.

This is not a testing failure in the usual sense. Nothing was untested. The tests were
thorough, specific, and green - they simply asserted a rule that was wrong about the
world.

A worked case: an agent that proposed calendar slots against a busy professional
calendar. The requirement read *"kill an entire day's candidates when that day carries
an all-day **or** out-of-office event"*. That `or` was the defect. In the user's actual
calendar, out-of-office was used as a **timed** block for travel, so a three-hour morning
flight wrote off the whole day. Eight such blocks killed eight days, every candidate was
dropped, and the agent produced empty output. Over 600 tests passed throughout.

The second defect, found the same way a day later, was the same shape: everything except
`free` counted as unavailability, so a colleague's fortnight-long absence invitation
blanked two weeks. **No test ever exercised the `tentative` value**, because the spec had
never contemplated it. The suite was complete against a rule that was simply false.

Six defects in total reached production behind a green suite. Not one was found by a
test; every one was found by using the agent.

## Why Tests Cannot See This

A test is written from the same understanding that produced the requirement. When that
understanding is wrong, the test inherits the error and then defends it. Three specific
mechanisms:

**The suite is complete against the wrong rule.** Coverage measures which code paths ran,
not which real-world inputs exist. A value the spec never imagined has no path to cover.

**Fixtures encode the author's belief, not the world.** A test that builds its own input
cannot detect an error in the translation *from* external data. If a fixture is
hand-authored and named "the real payload shape", it can be confidently wrong - and it
will then argue against correct code. In the same project, a mis-shaped fixture convinced
two independent expert reviewers that a safety check was dead. Their reasoning was sound;
the premise was fiction.

**Silence is a valid output.** An agent designed to say nothing when nothing changed is
indistinguishable, from the outside, from one that is broken. This is the most dangerous
property, because the failure mode is *absence*, and absence never triggers an alert.

## The Pattern

### 1. Treat "tests pass" as the start of verification

For anything consuming real-world data, budget explicitly for a first live run and for
**reading its output as a human artifact** - wording, rendering, noise, plausibility -
not just checking an exit code. Several defects in the worked case were visible in three
seconds of looking at real output and invisible to every assertion.

### 2. Count the real input distribution before writing the rule

Before writing a filter, measure what it will actually filter:

```
47 events in the window
   2  all-day
   8  timed out-of-office     <- the rule assumed these were rare
   6  tentative               <- the rule assumed these did not exist
  32  busy
```

Two of the six defects were visible in that table on day one. This is cheap, it is
read-only, and it is the single highest-value step in the list.

### 3. Instrument the funnel, because silence needs a witness

Any pipeline that can legitimately produce nothing needs a way to ask *why* it produced
nothing, showing the count surviving each stage and the specific reason each item was
dropped:

```
classes fetched      : 216
after allowlist      : 20
inside a time window : 20
after calendar gate  : 0        <- here
   DROPPED  Fri 12:00  overlaps 11:30-12:00
   DROPPED  Fri 16:30  day-killed by an all-day block
```

Build this before you need it. Reasons must be specific - "overlaps 13:00-14:00", not
"filtered". Ship it as a first-class read-only verb, not a debugging script, so it is
there at 6am when the agent went quiet.

### 4. Drive tests through the real parsing boundary

A test that constructs the internal type directly cannot see a defect in the mapping from
external data to that type - which is exactly where spec defects live. Enter through the
same function production does.

In the worked case, a fixture proving the parser handled server-expanded recurring events
would still have passed with the request element missing. The load-bearing assertion was
on the **outgoing request**, not the incoming fixture.

### 5. Give fixtures provenance

A fixture claiming to represent a real payload must record where and when it was
captured, in a comment on the test that loads it. Never hand-author one and name it "the
real shape". When a review finding rests on a fixture, verify the fixture against the
live artifact before acting on the finding.

### 6. Record spec corrections rather than editing them away

When a requirement turns out to be wrong, correct it *and* keep a note of what it said,
what the real data showed, and that it was found live. The pattern is more instructive
than the fix, and the next person will otherwise assume the requirement was always right.

## When This Applies

Highest value where an agent consumes messy real-world input that the author does not
fully control: calendars, mailboxes, third-party APIs, user-authored text, anything with
an enum whose values you learned from documentation rather than from counting.

Lower value for pure computation over inputs you define yourself - there, the spec and
the world are the same thing.

## The Honest Summary

Testing proves internal consistency. Only contact with reality proves external
correctness. Budget for both, and treat the first live run as a required step rather than
a formality.
