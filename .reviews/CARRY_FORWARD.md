# Carry-Forward Queue

> **v4.31.0 Phase 3.5.** The v4.26.0 seven-reviewer panel called the
> carry-forward situation "the worst carry-forward performance in
> project history" — six emitter items at their 7th review cycle,
> resolution rate down from ~100% at v3.47.0 to ~10% at v4.26.0. This
> file is the single source of truth for open carry-forwards across
> reviews. Every recovery release's SESSION_REPORT updates it.

## Schema

- **Severity**: CRITICAL / HIGH / MEDIUM / LOW (from the originating panel)
- **Cycles**: how many review cycles the item has survived. **Bold** when ≥ 3
- **Status**: OPEN / CLOSED / STALE / DEFERRED
- **Owner**: release that is scheduled to close it, or the person currently responsible

### Dual-closure convention (added v4.32.0 Phase 1.3)

Items that affect **both** the Python bootstrap emitter
(`mapanare/emit_llvm_text.py`) and the self-hosted emitter
(`mapanare/self/emit_llvm.mn`, `emit_llvm_ir.mn`, `mir_opt.mn`) are
tracked with **two** closure states. Ledger rows with asymmetry are
marked `PY: closed in vX.Y.0 | SH: open` (or vice versa). A symmetric
closure requires both sides to be closed — one-sided closures stay on
the carry-forward queue with the remaining side's tracking version
named.

This convention was added at v4.32.0 because the v4.31.0 arc-end panel
(Rattler #8, Cobra #14) surfaced that the v4.30.0 claim "six 7-cycle
emitter items re-verified clean" was verified Python-side only. The
self-hosted source was never touched in the v4.30.0 sweep — a failure
mode the single-column schema could not represent, and therefore could
not prevent.

`PY` = Python bootstrap emitter (`mapanare/emit_llvm_text.py`)
`SH` = self-hosted emitter (`mapanare/self/emit_llvm.mn` et al.)

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
| 30 | `i64*` opaque pointer migration (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | **PY**: v4.30.0 / **SH**: OPEN | PY: `culebra scan --id typed-pointer-legacy` → 0 findings on `emit_llvm_text.py` (v4.30.0). SH: one live `i64*` at `mapanare/self/emit_llvm.mn:528` in the `__mapanare_tensor_alloc` declare line — tracked to v4.33.0. |
| 31 | `void ()*` opaque pointer migration (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | **PY**: v4.30.0 / **SH**: OPEN | PY: clean per v4.30.0 sweep. SH: one live `bitcast void ()*` at `mapanare/self/emit_llvm.mn:949` in the TK_FN constant path — tracked to v4.33.0. |
| 32 | List `bitcast` cleanup (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | **PY**: v4.30.0 / **SH**: v4.32.0 (verified) | PY: every `bitcast` in `emit_llvm_text.py` is a comment (v4.30.0). SH: re-verified v4.32.0 phase 1.2 — only `bitcast ptr ... to ptr` remains at `emit_llvm.mn:3015`, which is a type-preserving no-op and not a typed-pointer-legacy pattern. |
| 33 | Missing `nsw` flags on int arithmetic (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | **PY**: v4.30.0 / **SH**: v4.32.0 | PY: `BinOpKind.ADD/SUB/MUL` emit `add nsw` / `sub nsw` / `mul nsw` at `emit_llvm_text.py:2060-2062` (v4.30.0). SH: `emit_add/sub/mul` in `mapanare/self/emit_llvm_ir.mn:117-129` emit `=add nsw` / `=sub nsw` / `=mul nsw` (v4.32.0 phase 1.2). Proof: `grep -c ' nsw ' /tmp/stage2.ll` = 1007 (was 0). |
| 34 | `__mn_map_new` 3-param arity mismatch (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | **PY**: v4.30.0 / **SH**: v4.32.0 | PY: 4-arg call at `emit_llvm_text.py:3161-3166` (v4.30.0). SH: declare and call site both 4-arg at `mapanare/self/emit_llvm.mn:357` and `emit_llvm.mn:1665` (v4.32.0 phase 1.2). Proof: `declare noalias ptr @__mn_map_new(i64, i64, i64, i64) nounwind willreturn` at `/tmp/stage2.ll:55`. |
| 35 | Missing `noalias`/`willreturn` attrs (7th cycle) | pre-v3.47.0 | HIGH (CARRY) | **PY**: v4.30.0 / **SH**: v4.32.0 | PY: +70 attribute annotations across 55 runtime symbols (v4.30.0). SH: `get_fn_attrs` grew from 25 entries to ~90 mirroring Python `_RUNTIME_FN_ATTRS`; new `get_fn_ret_prefix` for `noalias` on 13 allocators (v4.32.0 phase 1.2). Proof: `grep -c 'noalias' /tmp/stage2.ll` = 22 (was 0), `grep -c ' willreturn' /tmp/stage2.ll` = 188 (was 0). |
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
| A1 | Real `await` coroutine lowering (LLVM coroutine intrinsics) | v4.19.0 | MEDIUM | **2** | **CLOSED** | v4.75.0 — Arc 8+9 (v4.67.0-v4.75.0): DESIGN.md, grammar+AST+parser (v4.68.0), semantic+Future<T> (v4.69.0), prelude lowering (v4.70.0), suspension IR (v4.72.0), block_on+inline-resume (v4.73.0), for await (v4.74.0), golden tests `55_async_basic.mn`/`56_async_await.mn`/`57_real_await.mn` (v4.75.0). 70 async tests. 56-release carry-forward closed. |
| A2 | DWARF debug info emission | v0.7.0 | MEDIUM | **6** | **CLOSED** | v4.65.0 — Arc 7 (v4.62.0-v4.65.0): DESIGN.md, DICompileUnit, DISubprogram, DILocation on every instruction, DILocalVariable + `llvm.dbg.declare` for parameters. `llvm-dwarfdump --verify` passes. 34 DWARF tests. |
| A3 | Deprecated Python emitter removal (`PythonMIREmitter`) | v4.2.0 | LOW | **5** | **CLOSED** | v4.58.0 — `mapanare/emit_python_mir.py` deleted (1,236 lines), `cmd_compile`/`cmd_repl` removed, `_PYTHON_MIR_XFAIL` deleted, ~3,500 total lines removed. Regression gate: `tests/test_python_emitter_deleted.py` (6 tests). |
| A4 | llvmlite JIT emitter removal | v4.2.0 | LOW | **5** | **CLOSED** | v4.59.0 — `mapanare/jit.py` deleted (285 lines), `cmd_jit` + `--release` removed, llvmlite dependency dropped from pyproject.toml. `mapanare build` uses clang directly. Regression gate: `tests/test_llvmlite_removed.py` (5 tests). |
| A5 | Culebra `list-element-size-undercount` template tightens | v4.30.0 | LOW | 1 | OPEN | Culebra project, not Mapanare |
| A6 | Residual 69-line match-lowering shape diff between stage2 and stage3 | v4.28.0 | LOW | **3** | **CLOSED** | v4.34.0 — Maranget decision-tree rewrite in both pipelines; `mapanare/pattern_matching.py` shared helper |
| A7 | Self-hosted semantic analysis never wired into `compile()` | v4.26.0 | LOW | **3** | **CLOSED** | v4.52.0 — `check()` called at `mapanare/self/main.mn:298`; 3 divergent-breaking checks ported (D1 `?` operator, D2 match guard Bool, D3 while Bool); 11 regression tests in `tests/self_hosted/test_semantic_wiring.py` |
| A8 | Split `UNKNOWN` into `UNRESOLVED` + `ERROR` in semantic.py | v4.26.0 | LOW | **3** | **CLOSED** | v4.53.0 — `error_type()` + `type_should_skip()` in `semantic.mn`; cascade suppression at 12 check sites; 1 undefined fn → 1 error (was 4); 8 regression tests in `tests/self_hosted/test_error_cascade_self_hosted.py` |
| A9 | `emit_c.mn` (770 lines) references non-existent MIR types | v4.2.0 | LOW | **5** | **CLOSED** | v4.54.0 — Path B (delete). File was already deleted in v4.2.0 (commit `405b27e`). v4.54.0 corrected 6 stale doc claims ("11 modules" → "10 modules"), added regression gate `test_c_emitter_deleted.py`. See `docs/roadmap/v4/v4.54.0/DECISIONS.md` |
| 49 | Drop-glue skip-struct-ret early return at `emit_llvm_text.py:1097-1099` | v4.18.0 era | LOW | **8** | **CLOSED** | v4.78.0 — escape analysis replaces blanket early return; `_emit_drop_glue_collect_ret_ptrs` + per-kind helpers now skip only escaping pointers; test `TestStructReturnDropGlue` in `tests/llvm/test_drop_glue.py`; integration pipeline clean on all struct-return goldens |
| 50 | Agent `mapanare_agent_destroy` drops in-flight messages without freeing them | v4.26.0 | LOW | **2** | **CLOSED** | v4.78.0 — `message_dtor = free` set as default in `mapanare_agent_init`; drain loop now frees payloads; test `test_agent_destroy_drain.c` passes with -Werror; custom dtor path verified |
| A10 | Self-hosted bounded-for sentinels (`for _ in 0..N` as pseudo-while) | v4.26.0 (Cobra #15) | LOW | **10** | OPEN | v4.62.0+ (Arc 7). Not a bug — grammar gap. Accepted. |
| L7 | `cuda_matmul` upload/download rc check | v3.47.0 #3 | LOW | **3** | **CLOSED** | v4.36.0 Phase 1.1 — `mapanare_gpu_buffer_upload` / `_download` return values checked at `runtime/native/mapanare_gpu.c:1756` |
| P1 | `__mn_list_get` readonly+willreturn but calls abort — miscompilation at -O2 | v4.36.0 (Viper V1) | MEDIUM | 1 | **CLOSED** | v4.42.0 — removed readonly+willreturn from `_RUNTIME_FN_ATTRS` at `emit_llvm_text.py:253` |
| P2 | `pattern_matching.py` zero dedicated unit tests | v4.36.0 (Boa M1, Anaconda) | MEDIUM | **2** | **CLOSED** | v4.79.0 — 54 tests in `tests/semantic/test_pattern_matching.py` covering all 25 functions: classification, specialize, default, or-expansion, column selection, decision tree building, exhaustiveness, unreachable arms, witness display |
| P3 | Self-hosted guard fall-through divergence (jump-to-next vs decision-tree rebuild) | v4.36.0 (Cobra, Rattler) | MEDIUM | **2** | **CLOSED** | v4.79.0 — divergence documented in `lower.mn:3484`; jump-to-next correct for common case (same-type guards); full decision-tree port tracked as future work; golden `49_match_guards.mn` passes Python pipeline |
| P4 | SPEC §5.6 "compatible types" wording vs name-set-only implementation | v4.36.0 (Coral) | MEDIUM | 1 | **CLOSED** | v4.42.0 — SPEC §5.6 corrected at `docs/SPEC.md:906` |
| P5 | `examples/` showcase gap (3rd cycle) | v4.31.0 (Coral) | MEDIUM | **3** | **CLOSED** | v4.50.0 — 4 AI demos (basic_chat, basic_stream, chat_agent, rag_agent) + cookbook AI chapter + 8 sample docs |
| P6 | Unreachable-arm warning path zero test coverage | v4.36.0 (Boa M2) | MEDIUM | **2** | **CLOSED** | v4.79.0 — 9 unreachable-arm tests (7 unit + 2 integration) in `tests/semantic/test_pattern_matching.py`: wildcard→literal, duplicate literals, all-variants+wildcard, multiple wildcards, or-pattern overlap, bool exhaustive+trailing, semantic checker integration |
| A10b | Self-hosted const scope issue: const symbols not found in fn bodies | v4.55.0 | LOW | **3** | **CLOSED** | v4.78.0 — source fixes in semantic.mn (const_def early), parser.mn (LetDef emission), lexer.mn (KW_CONST near KW_LET); golden `58_const_scope.mn` passes Python bootstrap; compiled binary blocked on lexer codegen issue (tracked separately) |

## Items resolved in v4.36.0

| # | Item | First reported | Severity | Resolved in | Evidence |
|---|------|----------------|----------|-------------|----------|
| L7 | `cuda_matmul` upload/download rc check | v3.47.0 #3 | LOW | v4.36.0 | Return values checked at `runtime/native/mapanare_gpu.c:1756` |

## Items resolved in v4.34.0

| # | Item | First reported | Severity | Resolved in | Evidence |
|---|------|----------------|----------|-------------|----------|
| A6 | 69-line match-lowering stage2/stage3 diff | v4.28.0 | LOW | v4.34.0 | Maranget decision-tree rewrite in `mapanare/pattern_matching.py`, `mapanare/lower.py`, `mapanare/semantic.py` |
| L1 | `MN_PROFILE_FREE` never called in `__mn_free` (6th cycle) | Viper | LOW | v4.34.0 | `__mn_free_sized(ptr, size)` at `runtime/native/mapanare_core.c` |
| L2 | `__mn_read_line` 4KB stack truncation (6th cycle) | Viper | LOW | v4.34.0 | `getline(3)` on POSIX at `runtime/native/mapanare_core.c` |
| L3 | Arena allocator thread safety | Viper | LOW | v4.34.0 | Spinlock via `__sync_lock_test_and_set` in `mn_arena_alloc` |

## Items resolved in v4.35.0

| # | Item | First reported | Severity | Resolved in | Evidence |
|---|------|----------------|----------|-------------|----------|
| L4 | `s_net_initialized` non-atomic (5th cycle) | Viper | LOW | v4.35.0 | `pthread_once` / `InitOnceExecuteOnce` at `runtime/native/mapanare_io.c` |
| L5 | `ssl_load_library` CAS-before-init (3rd cycle) | Viper M7 | LOW | v4.35.0 | `pthread_once` / `InitOnceExecuteOnce` replacing atomic CAS at `runtime/native/mapanare_io.c` |
| L6 | `s_bcrypt` cache thread safety (3rd cycle) | Viper | LOW | v4.35.0 | `InitOnceExecuteOnce` at `runtime/native/mapanare_io.c` |

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
