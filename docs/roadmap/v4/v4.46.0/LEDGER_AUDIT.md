# v4.46.0 Ledger Audit

**Date:** 2026-04-12

Audit of `.reviews/CARRY_FORWARD.md` — verifies tracking accuracy of all OPEN items.

## Items Found CLOSED (stale tracking)

| Item | Carry-Forward Status | Actual Status | Evidence |
|------|---------------------|---------------|----------|
| A7 | OPEN | **CLOSED** | Self-hosted semantic wired into `main.mn:296-309` — `check(resolved, filename)` invoked in compilation pipeline |
| A9 | OPEN | **CLOSED** | `emit_c.mn` deleted from `mapanare/self/` — only `emit_llvm.mn` and `emit_llvm_ir.mn` remain |
| #50 | OPEN | **CLOSED** | `mapanare_agent_destroy` at `mapanare_runtime.c:686-696` now drains inbox/outbox via `message_dtor` callback (v4.33.0 Phase 4.3, Viper M5) |

## Items Requiring Tracking Update

| Item | Issue | Correction |
|------|-------|------------|
| A8 | Marked OPEN, but Python side is CLOSED | Should be dual-closure: `PY: closed (UNRESOLVED+ERROR in types.py:57-59) | SH: open (semantic.mn still uses unknown_type())` |
| A10 | Count cited as "442 sites" | Actual count: **589** across 12 self-hosted modules (growth from expanded self-hosted compilation) |

## Items Accurately Tracked (OPEN)

| Item | Description | Status |
|------|-------------|--------|
| #49 | Drop-glue skip-struct-ret early return (`emit_llvm_text.py:1157-1158`) | OPEN — early return still present, 8th cycle |
| P2 | `pattern_matching.py` zero dedicated unit tests | OPEN — no `test_pattern_matching.py` exists |
| P3 | Self-hosted guard fall-through divergence | OPEN — no overlapping guard test corpus to validate |
| P5 | `examples/` showcase gap (no agent/signal/stream demos) | OPEN — 20+ examples but no first-class primitive demos |
| P6 | Unreachable-arm warning zero test coverage | OPEN — function exists in `pattern_matching.py`, no test |

## Deferred Items (No Action Required)

| Item | Description | Tracking |
|------|-------------|----------|
| A1 | Real `await` coroutine lowering | DEFERRED to v5.0.0 |
| A2 | DWARF debug info emission | DEFERRED to v5.x |
| A3 | Deprecated Python emitter removal | DEFERRED to v5.0.0 |
| A4 | llvmlite JIT emitter removal | DEFERRED to v5.0.0 |
