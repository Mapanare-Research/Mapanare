# Carry-Forward Queue

> **v4.31.0 Phase 3.5.** The v4.26.0 seven-reviewer panel called the
> carry-forward situation "the worst carry-forward performance in
> project history" — six emitter items at their 7th review cycle,
> resolution rate down from ~100% at v3.47.0 to ~10% at v4.26.0. This
> file is the single source of truth for open carry-forwards across
> reviews. Every recovery release's SESSION_REPORT updates it.

## Legend

- **Severity**: CRITICAL / HIGH / MEDIUM / LOW (from the originating panel)
- **Cycles**: how many review cycles the item has survived. **Bold** when ≥ 3
- **Status**: OPEN / CLOSED / STALE / DEFERRED
- **Owner**: release that is scheduled to close it, or the person currently responsible

## Items resolved in the v4.27.0 → v4.31.0 recovery arc

These are the items the v4.26.0 panel flagged that have been **CLOSED**
in a specific recovery release. Each row names the release + the
commit/section in the CHANGELOG where the fix landed.

| # | Item | First reported | Severity | Resolved in | Evidence |
|---|------|----------------|----------|-------------|----------|
| 1 | FFI `.replace("define internal ", "define ")` strips all linkage | v4.26.0 | CRITICAL | v4.27.0 | `ffi_mode` path in `_compile_to_llvm_ir` sets `defn.public = True` in-AST |
| 2 | `libmapanare_rt.a` not `-fPIC` | v4.26.0 | CRITICAL | v4.27.0 | `Makefile build-rt` compiles with `-fPIC` |
| 3 | `mapanare bind --lang python` generates ctypes without argtypes/restype | v4.26.0 | CRITICAL | v4.27.0 | bind.py emits `argtypes=[...]`, `restype=...` |
| 4 | FFI DCE drops non-`main`-reachable functions from the shared library | v4.26.0 | CRITICAL | v4.27.0 | DFE respects `is_public`; `ffi_mode` marks all top-level fns public |
| 5 | `@gpu` / `@cuda` / `@vulkan` raises `NotImplementedError` at `lower.py:986` | v4.26.0 | CRITICAL | v4.27.0 | Decorators rejected at parse time (decorated_def rule) |
| 6 | `MIRVerifier` dead code (defined in v4.5.0, zero call sites) | v4.26.0 | CRITICAL | v4.27.0 | `_verify_mir_or_exit` wired into all compile entrypoints |
| 7 | `const` keyword is a parser alias with no `ConstDef` AST node | v4.26.0 | CRITICAL | v4.27.0 | `const` removed from grammar; module-level `let` is canonical |
| 8 | CHANGELOG v4.18.0–v4.26.0 advertise tests that don't exist | v4.26.0 | CRITICAL | v4.27.0 | Entries rewritten in stricken form |
| 9 | `__mn_signal_set` reads/writes `value` outside the lock | v4.26.0 | HIGH | v4.28.0 | All three operations now run under the signal mutex |
| 10 | Agent inbox SPSC ring used as MPSC without producer lock | v4.26.0 | HIGH | v4.28.0 | New `inbox_producer_lock` serializes the producer side |
| 11 | Type registry global hash table has no locking | v4.26.0 | HIGH | v4.28.0 | Reader-writer lock added; `get_*` returns a snapshot copy |
| 12 | `mn_init_tag_strings` once-init race | v3.47.0 | HIGH | v4.28.0 | `pthread_once` / `InitOnceExecuteOnce` — closes 7-cycle carry-forward |
| 13 | Matmul shape NULL check + dimension validation (27 versions overdue) | v3.47.0 | HIGH | v4.28.0 | Shape malloc NULL checks + `__int128` overflow guard + flat-length check |
| 14 | GLSL temp file race (`/tmp/mn_gpu_shader.*`) | v4.26.0 | HIGH | v4.28.0 | `mkstemps` / `GetTempFileNameW` per-invocation unique paths |
| 15 | Windows GPU init race (propagated to signal mutex site) | v4.26.0 | HIGH | v4.28.0 | `InitOnceExecuteOnce` at both sites |
| 16 | `main.ll` version string 19 releases stale | v4.26.0 | HIGH | v4.28.0 | Wired via build-time substitution |
| 17 | `mapanare_db.c` (1,130 lines) orphaned from build | v4.26.0 | HIGH | v4.29.0 | `Makefile build-rt` + `build_stage1.py` + `_RUNTIME_FN_ATTRS` |
| 18 | `mapanare_html.c` (812 lines) orphaned from build | v4.26.0 | HIGH | v4.29.0 | Same wiring as db; smoke tests added |
| 19 | `extern "Python" fn` silently xfailed (79 tests) since v4.2.0 | v4.26.0 | HIGH | v4.29.0 | Feature removed (Path B); `mapanare bind --lang python` is canonical |
| 20 | DWARF debug info not implemented (38 silent skips) | v4.26.0 | HIGH | v4.29.0 | Claim struck (Path B); `-g` flag prints deferred-to-v5.x warning |
| 21 | `--no-check` silently bypasses semantic analysis | v4.26.0 | HIGH | v4.29.0 | `_resolve_no_check` prints stderr warning with suppressed classes |
| 22 | `verify_fixed_point.sh` unfalsifiable (`EXIT=0` unconditional) | v4.26.0 | HIGH | v4.29.0 | `set -euo pipefail` + `DIFF_THRESHOLD` ratchet + exit propagation |
| 23 | CHANGELOG/ROADMAP advertise non-existent tests | v4.26.0 | HIGH | v4.29.0 | New `scripts/check_changelog_honesty.py` CI gate |
| 24 | Makefile `build-rt` on 4th carry-forward cycle | v3.47.0 | HIGH | v4.29.0 | `RUNTIME_SOURCES` enumeration + `check-runtime-sources` drift gate |
| 25 | `await` is identity lowering (`lower.py:1392`) | v4.26.0 | HIGH | v4.30.0 | Syntax removed (Path B); deferred to v5.0.0 |
| 26 | `_emit_agent_wrap` no-op stub returning 0 | v4.26.0 | HIGH | v4.30.0 | Wrapper dispatches to `{Agent}_handle`; regression gate pinned |
| 27 | Optimizer non-convergence emits `logging.warning` | v4.26.0 | HIGH | v4.30.0 | `MIROptimizerNonConvergence` ICE replaces warning |
| 28 | `stream_fusion` runs outside the fixpoint loop | v4.26.0 | HIGH | v4.30.0 | Moved inside the unified loop |
| 29 | Self-hosted dead block elim never calls `clean_phis_in_block` | v4.26.0 | HIGH | v4.30.0 | Invoked on every surviving block; mnc_all.mn regenerated |
| 30 | `i64*` opaque pointer migration (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | v4.30.0 | Re-verified clean via `culebra scan --id typed-pointer-legacy` |
| 31 | `void ()*` opaque pointer migration (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | v4.30.0 | Same |
| 32 | List `bitcast` cleanup (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | v4.30.0 | Every `bitcast` occurrence is now a comment |
| 33 | Missing `nsw` flags on int arithmetic (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | v4.30.0 | `BinOpKind.ADD/SUB/MUL` emit `add nsw` / `sub nsw` / `mul nsw` |
| 34 | `__mn_map_new` 3-param arity mismatch (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | v4.30.0 | 4-arg alignment verified on both sides |
| 35 | Missing `noalias`/`willreturn` attrs (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | v4.30.0 | +70 attribute annotations across 55 runtime symbols |
| 36 | `const_def` parser collapses `TypeExpr` to `.name` | v4.26.0 | HIGH | v4.27.0 | Moot after `const` removal |
| 37 | SPEC line 121 `di` mislabeled (5th cycle) | v3.47.0 | LOW (CARRY) | v4.31.0 | Fixed in this release |
| 38 | Bilingual keywords table missing from SPEC (3rd cycle) | v3.47.0 | LOW (CARRY) | v4.31.0 | Added in this release |
| 39 | `docs/README.es.md` stale (5+ cycles) | v3.47.0 | LOW (CARRY) | v4.31.0 | Synced in this release |
| 40 | `mapanare/emit_c.py` docstring 27 versions stale | v4.26.0 | LOW | v4.31.0 | Updated or file deleted in this release |
| 41 | User-Agent string `Mapanare/3.42` (5+ minor stale) | v4.26.0 | LOW | v4.31.0 | Wired to `MAPANARE_VERSION` macro + smoke test |
| 42 | `__mn_list_oob_buf` 4KB dead workaround | v4.26.0 | LOW | v4.31.0 | Deleted; v4.14.0 regression test still passes |
| 43 | Empty `[Unreleased]` CHANGELOG / no v4.26.0 SESSION_REPORT | v4.26.0 | LOW | v4.27.0 | All recovery releases ship a SESSION_REPORT |
| 44 | `mapanare_db.c` duplicate filesystem helpers vs `core.c` | v4.29.0 | LOW | v4.29.0 | Deleted from `db.c` in favour of canonical `core.c` impls |
| 45 | Agent DFE elimination (methods referenced only by wrapper) | v4.30.0 | MEDIUM | v4.30.0 | DFE seeded with `agent_info.method_names` |
| 46 | DCE removed one layer per call — `emit_llvm__emit_binop` non-convergent | v4.30.0 | MEDIUM | v4.30.0 | DCE iterates internally to a fixed point |
| 47 | `test_any_plus_any_error` silently red since v3.26.0 | v4.29.0 | LOW | v4.29.0 | Source wrapped in `fn main()` so `_check_binary` runs |
| 48 | Stale `mapanare/self/stage3.ll` (zero bytes from March 21) | v4.26.0 | LOW | v4.29.0 | Deleted; `.gitignore`'d |

## Items open after v4.31.0

These are the items the v4.31.0 panel is expected to surface OR the
items that were explicitly deferred out of the recovery arc.

| # | Item | First reported | Severity | Cycles | Status | Tracking version |
|---|------|----------------|----------|--------|--------|------------------|
| A1 | Real `await` coroutine lowering (LLVM coroutine intrinsics) | v4.19.0 | MEDIUM | **2** | DEFERRED | v5.0.0 |
| A2 | DWARF debug info emission | v0.7.0 | MEDIUM | **6** | DEFERRED | v5.x |
| A3 | Deprecated Python emitter removal (`PythonMIREmitter`) | v4.2.0 | LOW | **5** | DEFERRED | v5.0.0 |
| A4 | llvmlite JIT emitter removal | v4.2.0 | LOW | **5** | DEFERRED | v5.0.0 |
| A5 | Culebra `list-element-size-undercount` template tightens | v4.30.0 | LOW | 1 | OPEN | Culebra project, not Mapanare |
| A6 | Residual 69-line match-lowering shape diff between stage2 and stage3 | v4.28.0 | LOW | **3** | OPEN | v5.x rewrite of match lowering |
| A7 | Self-hosted semantic analysis never wired into `compile()` | v4.26.0 | LOW | **3** | OPEN | v5.0.0 self-hosted maturity sprint |
| A8 | Split `UNKNOWN` into `UNRESOLVED` + `ERROR` in semantic.py | v4.26.0 | LOW | **3** | OPEN | v5.0.0 |
| A9 | `emit_c.mn` (770 lines) references non-existent MIR types | v4.2.0 | LOW | **5** | OPEN | v5.0.0 — delete or rewrite |

## Items resolved in pre-v4.27.0 releases

Retained for traceability so the full panel can see which historic
carry-forwards finally drained. Not a complete list — see the
corresponding release CHANGELOG entries for detail.

| # | Item | First reported | Resolved in |
|---|------|----------------|-------------|
| P1 | llvmlite MIR emitter (5,000 LOC deprecated) | v2.0.0 | v4.2.0 |
| P2 | Two parallel diagnostic systems | v4.5.0 | v4.27.0 |
| P3 | AST-based `emit_llvm.py` (2,883 LOC) | v0.8.0 | v4.2.0 |
| P4 | `_coerce_arg` 36-site raw memory reinterpretation | v4.0.0 | v4.2.0 |

---

## Update protocol

Whenever a recovery or normal release ships, the SESSION_REPORT.md
must append to the "Items resolved" table above with:

1. The release version the fix landed in
2. A one-line evidence pointer (Culebra finding, test name, commit)

Items that are deferred must move to the "Items open" table with an
explicit `tracking version`. Items that are stuck (≥ 3 cycles, no
movement) get bolded. The arc-ending full panel uses this file as its
carry-forward input — if this file is out of date, the panel cannot
certify the arc.
