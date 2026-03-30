# Research → Challenge → Deepen

## Pattern

When exploring a complex domain (e.g., enterprise software, fintech, logistics), run parallel broad research first, synthesize findings, then challenge initial conclusions with targeted follow-up research that stress-tests assumptions.

This extends the [Parallel Research Pattern](parallel-research-pattern.md) with a second phase that prevents premature conclusions.

## Structure

```
Phase 1: BROAD PARALLEL RESEARCH
   → N independent topics, one subagent each
   → Each produces a structured report with cited sources
   → All run concurrently

Phase 2: SYNTHESIZE
   → Combine findings into implications document
   → Map findings to existing strategy/architecture
   → Identify initial conclusions

Phase 3: CHALLENGE ASSUMPTIONS
   → Review synthesis for claims that rest on inference rather than evidence
   → Identify "we assumed X does Y" statements
   → Launch targeted follow-up research to verify or falsify

Phase 4: REVISE
   → Update synthesis with corrected findings
   → Explicitly mark reversed conclusions (strikethrough + correction)
   → Document what changed and why
```

## Why the Challenge Phase Matters

Broad research tends to produce optimistic generalizations. When you research "how does the market handle X?", the results often describe vendor *positioning* rather than verified *capabilities*. The challenge phase forces a second pass that asks: "but do they actually do this specific thing?"

Common failure modes the challenge phase catches:
- **Capability inflation**: Vendor marketing says "AI-powered" but the actual feature is rule-based
- **Category confusion**: "Supports integrations" could mean pre-built connectors or just an open API with no docs — very different things
- **Assumed coverage**: "Serves enterprise customers" doesn't mean it covers your specific vertical or use case
- **Gap blindness**: Initial research finds who does X, but misses that nobody does Y — the gap is the insight

## Key Design Decisions

### Synthesis before challenge
Don't challenge individual research outputs in isolation. Synthesize first, then challenge the synthesis. The interesting assumptions live in the connections between topics, not within individual reports.

### Explicit reversal tracking
When the challenge phase contradicts an initial finding, don't silently edit — use strikethrough + correction so the evolution of understanding is visible. This builds trust and prevents future sessions from re-discovering the same false assumptions.

### Follow-up research must be zero-assumption
The challenge phase prompt must explicitly state: only report verified claims with cited sources. If information cannot be found, state "not found" rather than inferring. This is the key discipline that makes the challenge phase valuable.

## When to Use

- Market/competitive analysis where vendor positioning may diverge from actual capabilities
- Technology evaluation where "supports X" needs verification of what "supports" actually means
- Strategic planning where initial conclusions will drive investment decisions
- Any research where being wrong is expensive and being precise matters more than being fast

## When NOT to Use

- Well-defined factual questions with clear answers
- Time-sensitive research where "good enough" beats "precisely verified"
- Exploratory brainstorming where you want breadth, not precision

## Subagent Configuration

```
Phase 1 agents: run_in_background: true (broad, parallel)
Phase 3 agents: foreground or background depending on scope
               (targeted, may be fewer but deeper)
```

## Example

MES vendor selection for a mid-market manufacturer:
1. **Broad phase**: 6 parallel agents research vendor capabilities, pricing models, integration depth, cloud vs. on-premise, compliance features, customer references
2. **Synthesize**: Combine into vendor comparison — initial finding: "all 6 vendors claim full API coverage, differentiation is mainly UX and pricing"
3. **Challenge**: "But do they actually expose write APIs for shop-floor control, or only read-only dashboards?" → Launch targeted research on actual API capabilities per vendor
4. **Revise**: Only 2 of 6 vendors expose write APIs to production systems. The other 4 market "API coverage" but mean reporting endpoints only. Initial "commoditized market" conclusion reversed to "significant capability gap hidden by marketing language." The gap was the real insight, invisible at the category level.
