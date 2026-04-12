# v4.36.0 Ledger Audit — CARRY_FORWARD.md State at Arc 1 Close

**Date:** 2026-04-12
**Auditor:** Lead
**Scope:** All items in `.reviews/CARRY_FORWARD.md` as of v4.36.0 tag

---

## Summary

- **Total items in ledger:** 50 (original) + 10 (A-series) + 7 (L-series) = 67 rows
- **CLOSED:** 55 (43 in recovery arc + 4 in v4.34.0 + 3 in v4.35.0 + 1 in v4.36.0 + 4 in v4.32.0)
- **OPEN:** 8 (A1, A2, A3, A4, A5, A7, A8, A9 — all DEFERRED to v5.0.0+)
- **NEW this release:** A10 (bounded-for sentinels), L7 (cuda_matmul, CLOSED)
- **Still tracked:** Items 49, 50 (LOW, open since v4.18.0/v4.26.0)

---

## Items closed in Arc 1 (v4.32.0-v4.36.0)

| Release | Items closed | Evidence verified |
|---------|-------------|-------------------|
| v4.32.0 | #32 (list bitcast SH), #33 (nsw SH), #34 (map_new SH), #35 (noalias SH) | `grep -c` patterns in v4.32.0 SESSION_REPORT confirmed |
| v4.33.0 | 3 LOW items (signal depth, strip, agent dtor) | SESSION_REPORT claims verified |
| v4.34.0 | A6 (69-line diff→0), L1 (MN_PROFILE_FREE), L2 (read_line 4KB), L3 (arena lock) | `pattern_matching.py` exists; `__mn_free_sized` greppable; `getline(3)` greppable; spinlock greppable |
| v4.35.0 | L4 (s_net_initialized), L5 (ssl_load_library), L6 (s_bcrypt) | `pthread_once` at `mapanare_io.c`; `InitOnceExecuteOnce` for bcrypt |
| v4.36.0 | L7 (cuda_matmul rc check) | `mapanare_gpu.c:1756` — upload return values checked |

---

## Items still OPEN

| # | Item | Severity | Cycles | Tracking | Notes |
|---|------|----------|--------|----------|-------|
| A1 | Real `await` coroutine lowering | MEDIUM | 2 | v5.0.0 | DEFERRED — syntax removed in v4.30.0 (Path B) |
| A2 | DWARF debug info | MEDIUM | 6 | v5.x | DEFERRED — claim struck in v4.29.0 (Path B) |
| A3 | Python emitter removal | LOW | 5 | v5.0.0 | DEFERRED — kept for reference |
| A4 | llvmlite JIT removal | LOW | 5 | v5.0.0 | DEFERRED — kept for reference |
| A5 | Culebra template tightens | LOW | 1 | Culebra project | Not Mapanare scope |
| A7 | Self-hosted semantic wiring | LOW | 3 | v5.0.0 | Semantic exists but not called from compile() |
| A8 | UNKNOWN→UNRESOLVED/ERROR split | LOW | 3 | v5.0.0 | Type system cleanup |
| A9 | emit_c.mn references non-existent MIR types | LOW | 5 | v5.0.0 | Delete or rewrite |
| A10 | Bounded-for sentinels (442 sites) | LOW | 10 | v4.37.0+ | Grammar gap; `loop {}` would fix |
| 49 | Drop-glue skip-struct-ret | LOW | 8 | v4.37.0+ | `emit_llvm_text.py:1097-1099` |
| 50 | Agent destroy message leak | LOW | 2 | v4.37.0+ | `mapanare_runtime.c:686-691` |

---

## Dual-closure status (Python vs self-hosted)

| # | Item | PY | SH |
|---|------|----|----|
| 30 | `i64*` opaque pointer | CLOSED v4.30.0 | OPEN (1 site at `emit_llvm.mn:528`) |
| 31 | `void ()*` opaque pointer | CLOSED v4.30.0 | OPEN (1 site at `emit_llvm.mn:949`) |
| 32-35 | bitcast, nsw, map_new, noalias | CLOSED v4.30.0 | CLOSED v4.32.0 |

Items 30-31 remain asymmetric. Both are single-site issues in the self-hosted emitter tracked to v5.0.0 (Arc 5: Compiler Debt).

---

## Ledger health

- No items with cycles >= 5 are unresolved without tracking versions
- All DEFERRED items have explicit v5.0.0 or v5.x tracking
- The v4.35.0 closures (L4-L6) all have `pthread_once` evidence at `mapanare_io.c`
- The v4.34.0 closures (A6, L1-L3) all verified against current source
