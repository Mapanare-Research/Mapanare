# v4.54.0 Decision — `emit_c.mn` Path B (Delete)

**Date:** 2026-04-12
**Decision:** Path B — confirm deletion, close A9
**Decided by:** Lead

## Context

`mapanare/self/emit_c.mn` (770 lines) was created in v3.0.0 Phase 2.2 as a
self-hosted C emitter for portable bootstrapping. It was deleted in v4.2.0
(commit `405b27e`) as part of the emitter consolidation that removed 3
dead emitters totaling ~13,000 lines.

Despite the deletion, carry-forward item A9 remained OPEN because several
documentation files still claimed the self-hosted compiler had 11 modules
(including `emit_c.mn`). v4.54.0 formally closes A9 by correcting all stale
documentation claims.

## Alternatives considered

**Path A — Rewrite `emit_c.mn` against the current MIR.**
Rejected. No user demand exists for `mnc emit-c` through the self-hosted path.
The Python-side `mapanare/emit_c.py` (2,408 lines) is maintained and covers the
same surface. Rebuilding 770 lines of self-hosted C emitter adds debt for zero
current payoff. If demand emerges, v5.x+ can rebuild fresh against the current
MIR without legacy baggage.

**Path B — Confirm deletion, strike stale claims.**
Accepted. The file is already deleted since v4.2.0. The remaining work is
documentation honesty: fix the 6 places that still say "11 modules" and the
README that still lists `emit_c.mn` as a current module.

## Open question

**What if a future release needs a self-hosted C backend?**
Rebuild from scratch against the current MIR. The v4.2.0 deletion was the right
call — resurrecting 770 stale lines would have been worse than starting fresh.

## Migration path for users

None required. `mnc emit-c` was never functional through the self-hosted
pipeline. Users who want C output use `mapanare emit-c` (Python backend),
which is unaffected.
