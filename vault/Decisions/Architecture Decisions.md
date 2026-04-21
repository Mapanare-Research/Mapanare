---
aliases: [ADRs, Decisions]
---

# Architecture Decisions

Key decisions made during v4.x development. Each links to the version where the decision was taken.

## [[ADR-001 Bitfield vs int8 for is_heap]]

**When**: [[v4.100.0]]
**Context**: Plan said add `int8_t is_heap` to MnString. That grows struct from 16 to 24 bytes, crossing SysV AMD64 register boundary — breaks every call site.
**Decision**: Use C bitfield `uint64_t len:63; uint64_t is_heap:1` instead. Same 16 bytes, ABI preserved.
**Consequence**: LLVM IR still sees `{ ptr, i64 }` and needs bit masking for `.len`. But no sret/byval rewrite needed.

## [[ADR-002 Cooperative vs Full Async]]

**When**: [[v4.67.0]] (design), [[v4.72.0]]-[[v4.76.0]] (implementation)
**Context**: DESIGN.md offered Option A (cooperative inline-resume) and Option B (full suspension with scheduler).
**Decision**: Ship Option A first (v4.76.0). Option B planned for [[v4.92.0]]-[[v4.93.0]].
**Consequence**: Single-threaded async works. I/O-bound async deferred.

## [[ADR-003 Single Emitter]]

**When**: [[v4.2.0]]
**Context**: Three dead LLVM emitters (~13K lines) accumulated. Python emitter deprecated.
**Decision**: Delete all but `emit_llvm_text.py`. One emitter, one truth.
**Consequence**: 13,263 lines removed. No more emitter drift.

## [[ADR-004 Panel System]]

**When**: [[v4.26.0]] (crisis) -> [[v4.31.0]] (recovery)
**Context**: 6 hollow features shipped because no one was checking. Panel aggregate 8.2, 4 NEEDS WORK.
**Decision**: 7-reviewer panel every 5 releases. Carry-forward ledger. DESIGN.md before implementation.
**Consequence**: No hollow features since. 50-release recovery arc. Process works.

## [[ADR-005 No v5 at 4.99.0]]

**When**: [[v4.99.0]]
**Context**: Panel scored 6.59/10. Tagged-pointer UB, list indexing, async linking all broken.
**Decision**: Option B — continue v4.100.0+. v5.0.0 not tagged.
**Consequence**: 21 more releases planned (v4.100.0-v4.120.0) with 3 panels at milestones.
