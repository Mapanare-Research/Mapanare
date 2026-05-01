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

## Items resolved in v4.143.0 (post-rc1 panel fast-wins)

| # | Item | First reported | Severity | Resolved in | Evidence |
|---|------|----------------|----------|-------------|----------|
| Sp.1 | SPEC "Python transpiler backend" ghost at lines 25, 37, 39, 1792 + §18.2 | v4.143.0 panel (Coral) | MEDIUM | v4.143.0 | Four ghost lines rewritten; §18.2 redirected to `mapanare bind --lang python` canonical path |
| Co.1r | SPEC Appendix B "strict byte-identical" stale vs NEAR FIXED POINT | v4.143.0 panel (Coral) | LOW | v4.143.0 | Appendix B rewritten: v4.134.0 strict checkpoint + v4.139.0-present near-fixed-point with 4-line Dr.1 diff |
| Sem.2 | E420 ParseError not caught by `parse_recovering` | v4.143.0 panel (Coral) | LOW | v4.143.0 | `except ParseError` at fast-path + chunk-path in `mapanare/parser.py`; verified clean frame at `python3 -m mapanare check` |
| An.6 | `scripts/check_docs_drift.py` failing CI 4 consecutive releases | v4.143.0 panel (Anaconda) | MEDIUM | v4.143.0 | 7 module-level `let mut` blocks wrapped in `fn main()` across `docs/SPEC.md` + `docs/reference.md`; gate reports 142 blocks clean |
| An.7 | `scripts/check_silent_skips.py` blind to `_TR1_REASON` named-constant pattern | v4.143.0 panel (Anaconda) | LOW | v4.143.0 | Gate extended to resolve `reason=_NAME` identifiers; scans constant body + comment window above definition |
| An.8 | `tmp*.py` local scratch files break `make lint` | v4.143.0 panel (Anaconda) | LOW | v4.143.0 | Added to `tool.black.extend-exclude`, `tool.ruff.exclude`, `tool.mypy.exclude` in `pyproject.toml` |
| Bo.4-drift | README Tests badge `4845+` while localized READMEs at `5139+` | v4.143.0 panel (Boa) | LOW | v4.143.0 | Bumped to `5160+` |
| Bo.6-drift | `docs/guides/getting_started.md` test count `4,845+` and golden `53/65` | v4.143.0 panel (Boa) | LOW | v4.143.0 | Bumped to `5,160+` and `54/66`; fixed-point description updated to near-fixed-point |
| Bo.8 | SPEC header `Version: 4.139.0` | v4.143.0 panel (Boa) | LOW | v4.143.0 | Bumped to `4.143.0 (2026-04-18)` |
| Bo.10 | `docs/known_issues.md` footer `Last updated: v4.138.0` | v4.143.0 panel (Boa) | LOW | v4.143.0 | Bumped to `v4.143.0 (2026-04-18)` |
| Bo.11 | README main-blurb "strict 3-stage fixed point … at v4.134.0" | v4.143.0 panel (Boa) | LOW | v4.143.0 | Updated to near-fixed-point wording (4-line version-metadata diff) |
| Bn.1 | Cross-language benchmark harness spawn-tax corrupts Rust numbers | v4.143.0 panel (Mamba) | MEDIUM | v4.143.0 | All 10 Rust benches instrumented with `__BENCH_METRICS__` (`std::time::Instant` around `main`); `run_rust` uses `_run_with_metrics`; live-verified `enum_match` 0.43ms internal vs 10ms prior subprocess-pinned |
| Gr.3 | `Tensor` keyword collides with user type in generic position | v4.143.0 panel (Coral) | MEDIUM | v4.143.0 | Coral's Option 2: renamed stdlib `Tensor` struct → `GpuTensor` in `stdlib/gpu/tensor.mn` (63×) + `kernel.mn` (3×); `TensorError` preserved |
| Reg.1 | No CI gate for `build_internal_struct_list` drift (Ge.1 root cause pattern) | v4.143.0 panel (Rattler) | MEDIUM | v4.143.0 | New `scripts/check_struct_registry.py` (23/23 registry entries × 89 source structs cross-checked); caught 3 real latent drifts on first run (`MIRType` name/kind swap × 2 sites, `VerifyError` block_name → block_label × 2 sites); gate wired into `.github/workflows/ci.yml` + `tests/test_ci.py::TestToolsRunLocally` |
| Mar.1 | README benchmark citation drift (v4.136 vs v4.143) | v4.143.0 panel (Coral) | LOW | v4.143.0 | Implicitly closed by Bn.1 — Rust numbers are externally citable again; Mar.1 becomes a regeneration task, not a blocker |

## Items resolved in v4.149.0 (perf arc E5)

| # | Item | First reported | Severity | Resolved in | Evidence |
|---|------|----------------|----------|-------------|----------|
| ABI.1 | Register return for small aggregates per SysV/Win64/AAPCS64 | v4.125.0 benchmark refresh (re-flagged v4.136.0 panel, v4.143.0 panel) | LOW | v4.149.0 | New `mapanare/abi.py` classifier; 25 tests in `tests/llvm/test_abi_struct_return.py`; sret convention matches Clang on all three targets |

## Items opened by v4.143.0 panel, still open (all LOW polish)

| # | Item | First reported | Severity | Cycles | Status | Tracking |
|---|------|----------------|----------|--------|--------|----------|
| Cb.5-tests | `_enum_inline` has only integration-level checksum coverage | v4.143.0 panel (Rattler / Cobra) | LOW | 1 | OPEN | v5.0.0-final polish |
| Cb.6–Cb.10 | Five LOW items from Cobra's v4.143.0 review | v4.143.0 panel (Cobra) | LOW each | 1 | OPEN | v5.0.0-final polish |
| Own.1 | Self-hosted lowerer lacks compile-time move-semantics enforcement (Ge.1 class root pattern) | v4.143.0 panel (Viper) | LOW | 1 | OPEN | v5.x refactor |

## Items resolved in the v5.13.0 → v5.21.1 terseness arc

The v5.13–v5.21 arc closed each Mc.\* / Te.\* / Sh.\* / Dk.\* item
the v5.11.0 panel left open or that surfaced during arc execution.
v5.21.1 hygiene closes 12 docs-surface findings the v5.22.0 panel
would otherwise dock at fresh; structural closure prevents the
Bo.18r-style two-consecutive-panel regression. Each row names the
release the item closed in.

| # | Item | First reported | Severity | Resolved in | Evidence |
|---|------|----------------|----------|-------------|----------|
| Mc.2 | `mnc fmt` formatter: idempotent, AST-preserving whitespace canonicalizer | v5.11.0 panel docket (terseness-arc precondition) | LOW | v5.13.0 | New `mapanare/format.py`; 704 corpus assertions + 13 unit rules + 7 CLI integration tests in `tests/test_format.py` |
| Te.1 | Colon-block syntax: indent-based blocks alongside `{}` for every block-introducing construct | v5.13.0 PLAN | MEDIUM | v5.14.0 | `mapanare/parser.py::_indent_to_braces` preprocessor + `pass` keyword; 208 cross-style tests in `tests/test_colon_blocks.py` |
| Te.1.B | Bootstrap colon-block mirror: `mnc-stage1` accepts colon syntax | v5.14.0 SESSION_REPORT (deferred) | MEDIUM | v5.14.1 | New `__mn_indent_to_braces` C-runtime preprocessor + `pass` lex/parse/lower; `tests/bootstrap/test_indent_preprocessor.py` 201/201 (count refreshed v5.23.0 RC.13; was 142 at v5.14.1) |
| Te.2 | Comprehensions, terse lambdas, implicit-return one-liner | v5.13.0 PLAN | MEDIUM | v5.15.0 | New `Comprehension` / `CompClause` AST + `LambdaExpr` / one-line `fn name(args) = expr`; `tests/test_comprehensions.py` 11/11, `tests/test_lambdas.py` 6/6 |
| Te.2.B | Bootstrap comprehension mirror | v5.15.0 SESSION_REPORT (deferred) | MEDIUM | v5.15.1 | `Expr::Comprehension` + `parse_list_comp_tail` / `parse_map_comp_tail` + `lower_comprehension`; `tests/bootstrap/test_comprehension_mirror.py` 10/10 |
| Te.4 | Self-host string-interpolation parity (Python ↔ `mnc-stage1`) | v5.13.0-prep audit | MEDIUM | v5.16.0 | New `Expr::InterpString` + `lower_interp_string` + lexer `\$` escape fix; `tests/bootstrap/test_string_interp_mirror.py` 10/10 |
| Sh.B | Mechanical `mnc fmt --to-terse` rewrite of self-host modules | v5.13.0 PLAN | LOW | v5.17.0 | All 17 `mapanare/self/*.mn` modules colon-style; **-3,781 lines (-13.2%)**; strict 3-stage fixed point preserved at every per-module commit |
| Sh.C/D/G | Per-site comprehension upgrades, implicit-return upgrades, SPEC/README example refresh | v5.17.0 SESSION_REPORT (deferred) | LOW | v5.17.1 | 159 ONELINER + 121 BLOCK_SHORT implicit-return conversions + 3 comp-shape rewrites; **-169 lines** on top of v5.17.0 |
| Sh.H | Defensive-iteration cleanup (11 sites in `lower.mn`/`emit_llvm.mn`/`parser.mn`) | v5.17.1 COMPREHENSION_SITES.md | LOW | v5.17.2 | All 11 catalogued sites rewritten; **-38 lines**; cumulative shrink **-3,988 lines (-13.9%)** off the pre-Sh.B-immediate baseline (post-Te.4); **-2,285 lines (-8.18%)** net v5.13.0 → v5.21.1 |
| Mc.1 | LSP server (pygls) verified end-to-end | v5.18.0 PLAN (verify-and-fill) | LOW | v5.18.0 | 3,020-line pygls package + new JSON-RPC stdio smoke `tests/lsp/test_initialize_roundtrip.py` (117/117) |
| Mc.3 | `mapa init` template scaffolding | v5.18.0 PLAN | LOW | v5.18.0 | New `mapanare/templates/init/` + `{{NAME}}` substitution + project-name validation; 10/10 in `tests/test_init.py` |
| Mc.4 | `mapa check --all` recursive walk | v5.18.0 PLAN | LOW | v5.18.0 | `--all` flag with skip-list (`.git/`, `dist/`, `build/`, `node_modules/`); 10/10 in `tests/test_check.py` |
| Mc.1.G | VSCode extension v0.5.0 wiring `mapa init` / `mapa check --all` commands | v5.18.0 PLAN | LOW | v5.18.0 | Sibling repo `Mapanare-Research/mapanare-vscode` v0.5.0; `mapanare.init` + `mapanare.checkAll` commands |
| Te.3 | `{}` soft-deprecation: parse-time warning + `mnc fmt` auto-migration default | v5.18.0 closeout (originally v5.17.x) | MEDIUM | v5.19.0 | One-warning-per-file at parse time + `MAPANARE_NO_BRACE_WARNING=1` opt-out + `mnc fmt --keep-braces`; hard removal scheduled v6.0 |
| Dk.\* | GHCR Docker images (`mapanare-builder`, `mapanare-runtime`) + `mnc init --docker` overlay | v5.10.0 closeout (Dk.\* split from v5.19.0) | LOW | v5.19.1 | New `.github/workflows/publish-docker.yml` + multi-stage hello-world ~115 MB final image; `docker-smoke` CI job |
| Te.5 | Struct ergonomics: field shorthand, struct update, let destructuring, if-let / while-let / let-else (Python side) | v5.13.0 PLAN | MEDIUM | v5.20.0 | 4 surface forms desugared at lower time; 11 new goldens at `tests/golden/81…91`; **+477 lines Python** total |
| Te.5.F | Bootstrap Te.5 mirror: `mnc-stage1` parses + lowers all four Te.5 forms identically | v5.20.0 SESSION_REPORT (deferred) | MEDIUM | v5.20.1 | New `Expr::ConstructUpdate` + `Stmt::LetDestructure` + `Expr::IfLet` / `Stmt::WhileLet` / `Stmt::LetElse` AST variants; `tests/bootstrap/test_te5_mirror.py` 12/12; **+742 lines** total |
| Te.6 | Chained comparisons (`0 < x < 10`) with once-evaluation + L4-merge of equality and ordering operators | v5.13.0 PLAN | MEDIUM | v5.21.0 | New `Expr::ChainedCmp(operands, ops)` AST + `_lower_chained_compare`; bootstrap mirror at v5.21.0 in lockstep; goldens 91/91 → 95/95; strict fixed point preserved |
| H.1–H.13 | Pre-panel docs-surface drift across SPEC, README, localized READMEs, CARRY_FORWARD ledger | v5.22.0 PRE_PANEL_AUDIT.md | HIGH (4) / MEDIUM (1) / LOW (8) | v5.21.1 | This row's release: SPEC re-synced from v5.7.1 → v5.21.0 cut; §4.0 documents Te.3; §1009 broken `if x: y` promise rescoped to v6.0; 4 localized READMEs prose-synced; `examples/chained_cmp.mn`; `tests/bootstrap/test_chained_cmp_mirror.py` 10/10; `format.py` chained-cmp invariant tests; CARRY_FORWARD arc append (this row) |

## v5.22.0 panel — closures verified

The v5.22.0 panel ran the v5.13–v5.21 terseness-arc closeout
review (16-release surface, 7 reviewers, aggregate **9.41 / 10
Option A**, third consecutive Option A under the v5-gate
mechanical rule). The panel verified the v5.21.1 H.\* hygiene
closures and re-graded every v5.11.0 panel docket item against
v5.22.0 HEAD.

**v5.11.0 panel docket — final disposition at v5.22.0:**

| # | Item | Severity at v5.11.0 | Status at v5.22.0 | Closing release | Evidence |
|---|------|---|---|---|---|
| Bo.21 | Version badges stuck at 5.8.7 across 4 READMEs | HIGH | **CLOSED, STAYS CLOSED** | v5.21.1 H.1 (via `bump_version.py` sweep) | Verified: all 4 READMEs at 5.21.1 |
| Bo.18r | README internal contradiction — fixed-point status paragraph | MEDIUM | **CLOSED v5.23.0 RC.2** | v5.23.0 RC.2 (line 188-192 + line 176; rounded `239k` framing) | Both lines now consistent with native-compiler section |
| Bo.17r | Localized READMEs frozen at v5.7.1 content | MEDIUM | **CLOSED ~80% structurally** | v5.21.1 H.3 | es/pt/zh-CN bodies now have 95/95 + Te.1–Te.6 subsection + STRICT 238k status |
| Coral SPEC re-sync | SPEC.md header reads 5.7.1 against v5.11.0 codebase | MEDIUM | **CLOSED** | v5.21.1 H.2 / H.5 | SPEC header at v5.21.0 cut; §2.2 / §3.7 / §4.0 / §4.3.1 current |
| Mc.\* docket | Native `mnc` missing 18/25 subcommands | MEDIUM | **CLOSED** | v5.18.0 | `mnc lsp` / `fmt` / `init` / `check` all reachable through native dispatch |
| Pk.1.A | Linux/macOS versioned-tarball smoke gates missing | LOW | **STILL OPEN — 11 releases** | — | v5.13.0 alias-drop deadline cited in 6 written locations did not ship |
| Cobra per-PR fixed-point gate (3rd-time ask) | Per-PR fixed-point CI gate not wired | LOW | **CLOSED** (mea culpa from v5.8.0 / v5.11.0 — was always wired) | v4.29.0 | `.github/workflows/ci.yml:858`; Cobra confirmed at v5.22.0 panel |
| Cobra `>= 45` magic | Hard-coded threshold in `build_from_seed.sh:159` | LOW | **STILL OPEN — 3rd panel** | — | Threshold drifting from corpus year-over-year (now ~50–55 vs 95-corpus) |
| Viper V.6 | DX.4 walkers unbounded recursion | LOW | **CLOSED v5.23.1 Mb.4** | v5.23.1 Mb.4 | `MN_DIR_WALK_MAX_DEPTH` (4096) cap parameter added to all 3 walkers — pragmatic alternative to plan's full iterative work-queue rewrite |
| Viper V.7 | Win32 walkers follow reparse points | LOW | **CLOSED v5.23.1 Mb.5** | v5.23.1 Mb.5 | `FILE_ATTRIBUTE_REPARSE_POINT` skip in 3 Win32 sites; POSIX `stat()` → `lstat()` for symmetric symlink-skip |
| Viper V.8 | No ASan/valgrind sweep on v5.10.0+ deltas | LOW | **CLOSED v5.23.1 Mb.6** | v5.23.1 Mb.6 | `sanitizer-cache-walkers` CI job exercises `mnc cache stats` / `cache clean` / `version` under valgrind |
| Boa Bo.22 | `mapanare run` vs `mnc run` in README Hello World | LOW | **CLOSED v5.23.0 RC.14** | v5.23.0 RC.14 | All 5 invocations + alias note ("`mapanare` is also installed as an alias for `mnc`.") added |
| Boa Bo.19 | Test count drift (badge/body/measurement triple) | LOW | **CLOSED v5.23.0 RC.2** | v5.23.0 RC.2 (incidental closure same paragraph) | 5,800+ in body now matches badge |
| Boa Bo.20 | README links to `benchmarks/FINAL_REPORT_v4.153.md` | LOW | **CLOSED v5.23.0 RC.2** | v5.23.0 RC.2 (incidental closure same paragraph) | Updated to `benchmarks/FINAL_REPORT.md` |
| Mamba Pe.1 | stage2.ll growth scaling | LOW | **REFRAMED v5.24.0 Hy.6** | v5.24.0 Hy.6 | "Curve flattening" framing retired per Mamba's v5.22.0 #2: growth is proportional to bootstrap-side AST additions across the Te.\* arc, not a v6.0 budget concern at current rate (need another 30+ releases at +0.5%/release before doubling). |
| Anaconda informational LOWs | Coverage gate / Windows CI lane / self-compile pytest smoke / MIR destination-passing tests / inliner-kinds whitelist | LOW each | **STILL OPEN** | — | 53/38/etc-release deferred status quo unchanged |

**v5.22.0 panel — new findings:**

| # | Item | Severity | Reported by | Cycles | Status | Tracking version |
|---|------|----------|-------------|--------|--------|------------------|
| Reg.1 | `check_struct_registry.py` regex hard-codes brace headers (`struct Name {`); inert since v5.17.0 Sh.\* mechanical rewrite. 23 violations at HEAD; **5 releases of silent registry blindness** during the largest feature-velocity arc in v5 history. The gate v4.143.0 commissioned to catch Ge.1-class drift is the same gate that became inert when Sh.B mechanically rewrote every struct definition. | HIGH | Anaconda §2.A + Cobra #1 | 1 | **CLOSED v5.23.0 RC.1** | — |
| Bo.18r-3 | `README.md:188-192` benchmarks-section lead-in paragraph still v5.7.1-vintage. v5.21.1 H.1 closed sibling line 176 (the line the lead's audit cited); panel-flagged 188-192 was not in the audit. **3rd consecutive panel of the same paragraph.** Severity escalated MEDIUM → HIGH at v5.22.0 per process-discipline signal. | HIGH | Boa #1 | 3 | **CLOSED v5.23.0 RC.2** (rounded `239k` framing; line 176 also updated) | — |
| Bo.25 | Goldens badge `66/66` across all 4 READMEs while body says `95/95`. Same systematic-skill-gap fingerprint as v5.11.0 Bo.21. Three releases of badge lag. Structural fix: extend `bump_version.py` to auto-discover `tests/golden/*.mn` count. | HIGH | Boa #2 | 1 | **CLOSED v5.23.0 RC.3** (one-shot + structural; `tests/test_bump_version.py` 5/5) | — |
| V.9 | `__mn_indent_to_braces` MnString lifecycle leak: returned `joined` buffer is not drop-glue tracked at the `parser.mn::parse` call site. Bounded to single-shot in `mnc-stage1`; unbounded if embedded in long-lived process. The byte-identical oracle `test_indent_preprocessor.py` cannot detect lifecycle issues — class blind spot. **Mandatory CI follow-up:** valgrind regression gate. | MEDIUM | Viper V.9 | 1 | **CLOSED v5.23.1 Mb.1** | v5.23.1 Mb.1 (Python `_do_call` blanket-move bypass) + Mb.3 (`sanitizer-mnc-stage1` regression gate) |
| Te.5 ASan leaks | 3 NEW LEAK regressions on `tests/golden/{88_if_let, 90_while_let, 91_let_else}.mn` — surfaced post-v5.22.0 panel via the LeakSanitizer CI workflow. Root cause was self-host `emit_wrap_some` malloc'ing the Some payload but never calling `emit_track_boxed`. Latent on baseline 17_option since v5.4.2. | MEDIUM | LeakSanitizer CI (post-panel) | 1 | **CLOSED v5.23.1 Mb.2** | v5.23.1 Mb.2 (`s = emit_track_boxed(s, ea)` after malloc; baseline TSV refreshed) |
| Te.3 hollow / asymmetric closure | Brace-deprecation warning misses single-line `{...}` shape; native `mnc-stage1` has zero brace-deprecation logic. PRE_PANEL_AUDIT.md's own canonical pre-flight test command demonstrates the gap. **Asymmetric closure**: PY: closed | SH: open. Three independent reviewers flagged. | MEDIUM | Coral M1 / Anaconda §3 / Rattler #1 | 1 | **CLOSED v5.23.2 Te.3.B.1–.5** | v5.23.2 Te.3.B.1 (Python detector rewritten as char-walker w/ rules a/b/c) + Te.3.B.2 (C-runtime mirror via `__mn_count_user_brace_block_openers` + `__mn_emit_brace_deprecation_warning`) + Te.3.B.3 (`tests/bootstrap/test_brace_deprecation_mirror.py` 11/11 byte-identity contract) + Te.3.B.4 (PRE_PANEL_AUDIT.md update) + Te.3.B.5 (Bb.\* seed refresh, mirrors v5.17.0 Sh.E). Strict 3-stage fixed point preserved at 239,835 lines / 0 diff. |
| Hollow-feature gate calibration | `check_no_hollow_features.py` step 3 fails on `CompClause` (v5.15.0 Te.2) + `FieldPattern` (v5.20.0 Te.5.D) — whitelist calibration miss. Same 5+/2+ release silent-fail pattern as Reg.1. | MEDIUM | Anaconda §2.B | 1 | **CLOSED v5.23.0 RC.4** | — |
| Manifesto coherence (M2) | `docs/manifesto.md:31` "Curly braces for blocks" untouched against brace-deprecated codebase. **3rd consecutive panel of manifesto drift.** | MEDIUM | Coral M2 | 3 | OPEN | v5.22.x |
| SPEC example corpus (M3) | 26 of 36 block-openers in `docs/SPEC.md` are brace-style against §4.0 declaring colon-canonical (72%). v5.21.1 hygiene closed prose but not examples. | MEDIUM | Coral M3 | 1 | OPEN | v5.23.0 |
| Cadence skip (process) | 5-minor (v5.16.0) AND 5-language-feature (v5.20.0) triggers fired and were not honored at trigger; documented as overdue but not run on schedule. | MEDIUM | Anaconda §1 | 1 | OPEN | v5.23.0 (CI gate enforcement) |
| Sh.\* shrink baseline labeling | "−13.9% off v5.13.0" cited across v5.17.x SR + CARRY_FORWARD.md + CLAUDE.md actually measures pre-Sh.B-immediate baseline (post-Te.4); net v5.13.0 → v5.21.1 is **−8.18% (-2,285 lines)**. Headline shrink is real; baseline label is not. | MEDIUM | Cobra #2 / Rattler #4 | 1 | **CLOSED v5.23.0 RC.12** (dual-baseline framing; `CARRY_FORWARD.md` row Sh.H + `CLAUDE.md:381` updated) | — |
| `check_docs_drift.py` SPEC.md:1456 | `fn id(y) = y` doesn't parse via current grammar (untyped param). Annotate `y: Int` or add `<!-- pseudo -->` opt-out marker. | LOW | Anaconda §2.C | 1 | **CLOSED v5.23.0 RC.5** (`fn id<T>(y: T) -> T = y`) | — |
| `make ci-gates` Makefile target | Pre-release checklist needs single command running full CI gate inventory locally. Eliminates wired-but-unchecked failure mode. | MEDIUM (structural) | Anaconda §2.D | 1 | OPEN | v5.22.x |
| `check_doc_freshness.py` CI gate | Structural fix for the H.\* / Bo.\* drift class. Closes the closure-by-hygiene-release ceiling that v5.7.1 / v5.11.0 / v5.22.0 panels all hit at 9.5–9.66. | MEDIUM (structural) | Coral / Boa Bo.27 | 1 (carry from v5.11.0 "Do.\*" recommendation) | OPEN | v5.23.0 |
| `__mn_indent_to_braces` not in `.h` | `MN_EXPORT`'d in `mapanare_core.c` but no public-API header decl. | LOW | Mamba #1 | 1 | **CLOSED v5.23.0 RC.10** | — |
| v5.19.0 SESSION_REPORT missing | `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` does not exist on disk despite Te.3 having shipped (3 commits in log). | LOW | Rattler #2 / Anaconda LOW | 1 | **CLOSED v5.23.0 RC.11** (backfilled from PLAN/PROMPT/DOCKER_DESIGN + 3 commits) | — |
| `tests/bootstrap/test_indent_preprocessor.py` count refresh | PRE_PANEL_AUDIT.md and CARRY_FORWARD.md cite suite at 142; live collection shows 201. | LOW | Cobra #4 | 1 | **CLOSED v5.23.0 RC.13** | — |
| Bo.26 (guides discoverability) | `docs/guides/formatter.md` and `docs/guides/init.md` not linked from any README or SPEC. | LOW | Boa #5 | 1 | **CLOSED v5.23.0 RC.15** (4 guides linked: formatter, init, lsp, docker) | — |
| Bo.27 (audit cross-reference column) | PRE_PANEL_AUDIT.md should add a "Closes prior-panel finding" column at next pre-panel audit. Process observation behind H.\* / Bo.\* mismatch driving Bo.18r persistence. | LOW (process) | Boa #6 | 1 | OPEN | v5.27.0 audit |
| Cadence enforcement gate | CI gate or pre-release script firing when ≥5 minor versions OR ≥5 language-feature releases ship without a panel. | LOW (process) | Anaconda §1 | 1 | OPEN | v5.23.0 |
| Coral L1–L5 / TR1 | SPEC §27 deprecation crosslink, broken-promise wording, `mnc fmt --keep-braces` flag mention, generic-bound trait sketch, examples directory micro-organization. | LOW each | Coral L1–L5 | 1 each | OPEN | v5.23.0+ |
| Stage2-binary teardown crash (RC=3) | Papered over by `set +e` in `verify_fixed_point.sh:124-137`. **70+ releases stale** since v4.30.0 PLAN. | LOW (carry) | Rattler #5 | 70+ | OPEN | v6.0 cleanup window |

**Aggregate state entering v5.22.x:**
- **4 HIGH** open (2 carried from v5.11.0 panel, 2 new at v5.22.0)
- **8 MEDIUM** open (1 carried from v5.11.0 panel, 7 new at v5.22.0)
- **~12 LOW** open (mix of carries and new findings)
- **1 v6.0-rescoped** (Rt.04 multi-level alias analysis, status unchanged)

**Aggregate state entering v5.24.x (post-v5.23.0 RC.\* closeout):**
- **0 HIGH** open (4 closed: Reg.1, Bo.18r, Bo.25, plus the inherited
  Pk.1.A — wait, Pk.1.A is still LOW + carry; HIGH count is now 0)
- **4 MEDIUM** open: V.9 (v5.23.1 Mb.1), Te.3 hollow-surface (v5.23.2),
  Manifesto coherence M2 (v5.24.1), SPEC corpus M3 (v5.24.1),
  Cadence skip / `make ci-gates` / `check_doc_freshness.py` (v5.24.0
  Hy.\* — counts as one structural cluster)
- **~7 LOW** open: Pk.1.A (11+ release carry, deferred to v5.24.0
  Hy.5), `>= 45` magic, V.6/V.7/V.8 (3rd cycle), Coral L1–L5 / TR1
  (v5.24.1), Bo.27 (v5.27.0 audit), Stage2 teardown (v6.0)
- **1 v6.0-rescoped** unchanged
- **15 RC.\* closed in v5.23.0** (RC.1–RC.15 in one mechanical session)

**Aggregate state entering v5.24.x (post-v5.23.2 Te.3.B closeout):**
- **0 HIGH** open
- **3 MEDIUM** open: Manifesto coherence M2 (v5.24.1), SPEC corpus
  M3 (v5.24.1), Cadence skip / `make ci-gates` /
  `check_doc_freshness.py` (v5.24.0 Hy.\* — one structural cluster).
  V.9 closed v5.23.1; Te.3 hollow / asymmetric closure CLOSED
  v5.23.2 (this row).
- **~7 LOW** open: same as above row; v5.23.2 did not close any LOW.
- **1 v6.0-rescoped** unchanged.
- **5 v5.23.2 closures**: Te.3.B.1 (Python detector rewrite) +
  Te.3.B.2 (native mirror) + Te.3.B.3 (cross-bootstrap mirror test
  11/11) + Te.3.B.4 (PRE_PANEL_AUDIT.md update) + Te.3.B.5 (Bb.\*
  seed refresh).

**Aggregate state entering v5.24.x (post-v5.23.1 Mb.\* closeout):**
- **0 HIGH** open
- **3 MEDIUM** open: Te.3 hollow-surface (v5.23.2), Manifesto
  coherence M2 (v5.24.1), SPEC corpus M3 (v5.24.1), Hy.\* cluster
  (v5.24.0). V.9 + Te.5 ASan leaks closed.
- **~4 LOW** open: Pk.1.A, `>= 45` magic, Coral L1–L5 / TR1, Bo.27,
  Stage2 teardown. **V.6 / V.7 / V.8 closed** (3rd-cycle exit).
  Mb.7 (ASan-gate llc aborts) added as a new tracked v5.24.0+
  LOW (i64/i1 tag-emit bug, async-codegen llc class, pre-existing,
  unrelated to memory hygiene).
- **1 v6.0-rescoped** unchanged
- **6 Mb.\* closed in v5.23.1** (Mb.1–Mb.6); Mb.7 deferred.

**Cadence reset:** next routine panel due at **v5.27.0** (5
minors past v5.22.0).

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
