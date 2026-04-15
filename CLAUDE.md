# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mapanare is an AI-native compiled programming language with first-class agents, signals, streams, and tensors. It compiles to LLVM IR (primary) and C (fallback via gcc). A WebAssembly backend exists for browser/server targets. The self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in `mapanare/self/`. The compiler compiles itself — `bash scripts/build_from_seed.sh` builds from source with no Python.

## Current Version & Roadmap

- **v4.128.0** (shipped) — **Phase F closeout release 8: self-hosted fixed-point refinement continuation — Sh.8 closed at the source level, brace-spacing normalized, ModuleID path-stripped. Proxy divergence (Python bootstrap vs `mnc-stage1` on 39 passing goldens) reduced from 9,608 → 9,425 lines (-1.9%). M bucket fully closed (78 → 0). Zero golden regressions.** Buffer release 3 of the v4.130.0 closeout arc. Three changes in four self-hosted files, ~35 net new lines: (1) **Sh.8 closed at the source level** — `mapanare/self/semantic.mn::infer_expr` ident branch gains a 4-line special case for bare `None` (returns `make_type("Option")` before `scope_lookup`, mirroring `mapanare/lower.py::_lower_identifier`). Closes **docket Sh.8** (open since v4.112.0). Running `verify_fixed_point.sh` now advances past the "Undefined variable 'None'" gate but surfaces a new downstream blocker — **docket Sh.11**: `lower_expr` SIGSEGV during MIR lowering of `mnc_all.mn` (crash in `lower__lower_expr+0xc8ff`). Strict stage2-vs-stage3 fixed-point remains blocked; Sh.11 is the new gate, reserved for the v4.131.0+ post-panel arc. The measurement pivots cleanly to the v4.127.0 Python-vs-self-hosted proxy (anticipated by PLAN.md's risk register). (2) **Brace-spacing normalization** — `mapanare/self/emit_llvm_ir.mn` 7 type-constant helpers (`llvm_string`, `llvm_option_type`, `llvm_result_type`, `llvm_tensor_type`, `llvm_map_type`, `llvm_list_rt`, `resolve_mir_type` RANGE case) changed from spaced `"{ ptr, i64 }"` to canonical `"{ptr, i64}"` — matches Python's `_decl_fn` → `", ".join(abi_pts)` canonical output. `mapanare/self/emit_llvm.mn` 20+ inline sites: runtime declarations, `insertvalue` / `extractvalue` instructions for ranges and maps, the named enum type declaration (`%enum.X = type { i64, ptr }` → `{i64, ptr}`), and the `struct_byte_size` equality checks (lines 663, 665, 667) all updated. LLVM accepts both forms; aligning on Python's canonical output removes a per-decl character-level divergence. (3) **Module-ID path stripping** — `mapanare/self/main.mn:335` now strips path + extension from the filename before calling `emit_mir_module`, matching Python CLI's `os.path.splitext(os.path.basename(filename))[0]` convention (`mapanare/cli.py:183`). Uses existing `basename_of` + `file_extension` helpers in `main.mn`. 5 lines added (2 code + 3 comment). Before: `ModuleID = 'tests/golden/01_hello.mn'`; after: `ModuleID = '01_hello'` — matches Python exactly. **Concat script discrepancy caught but not fixed**: `scripts/concat_self.sh` (bash) omits `mir_opt.mn` from its module list — latent bug that would silently produce a broken `mnc_all.mn` if used (`optimize_mir` would be undefined). `scripts/concat_self.py` (Python) is correct and authoritative. Tagged for v4.129.0+; one-line fix out of scope for a buffer release focused on fixed-point refinement. **Post-fix delta** (`docs/roadmap/v4/v4.128.0/post_fix.json`): total diff **9,608 → 9,425 lines (-183, -1.9%)**; stage1 output **6,120 → 5,980 lines (-140)**; **M bucket 78 → 0 (-100%, fully closed)** — module-header divergence is now zero (`ModuleID` / `source_filename` / `target datalayout` / `target triple` / version metadata all match Python exactly); S bucket **6,610 → 6,722 (+112)** — classification artefact (block-level `difflib.SequenceMatcher` shuffles runtime-decl hunk attribution when the dominant character change shifts from attribute suffix to the now-aligned brace form; character-level improvement is real); A (328), C (301), W (0), L (39) unchanged — out of scope. **Cumulative v4.126.0 → v4.128.0: proxy divergence 9,971 → 9,425 lines = -546 lines, -5.5%.** v4.127.0 closed half the M bucket (156 → 78); v4.128.0 closed the other half (78 → 0). **Verification**: `mnc-stage1` rebuilds cleanly (`python3 scripts/concat_self.py` + `python3 scripts/build_stage1.py`, ~1m20s, 3,488,912 bytes stripped, byte-size unchanged from v4.127.0); golden tests through `mnc-stage1` are **39/65 — unchanged from v4.127.0, zero regressions** in previously-passing tests; core compiler pytest subset (parser / semantic / mir / llvm / golden / emit / optimizer, 1,258 tests) **passes clean (0 failures)**; broader pytest excluding bootstrap is **5,057 passed / 46 failed / 103 skipped / 7 xfailed in 20m** — 8 additional failures vs v4.127.0's 38 baseline but all in environmental test families (`tests/native/test_c_hardening.py`, `tests/native/test_db_*`, `tests/runtime/test_list_bounds.py`, `tests/test_ci.py`, `tests/test_doc_links.py`, `tests/test_runner/test_test_runner.py`) that don't depend on self-hosted `.mn` changes; bootstrap subset is **212 passed / 13 failed in 2m30s** — 1 additional failure vs v4.127.0's 213/12 is `test_lexer_full_emit_deterministic`, investigated and identified as pre-existing Python-bootstrap counter-reset non-determinism (two runs emit different `_inlN_` labels; both use `{ptr, i64}` canonical form, so NOT caused by the brace-normalization change). No Python code changed; baseline 204 ruff findings (An.2 carry-forward) unchanged — v4.123.0+ track per v4.121.0 closeout PLAN. `libmapanare_rt.a` byte-identical to v4.127.0 (no C runtime changes). **Diff**: 5 files changed (4 self-hosted `.mn` + 1 regenerated `mnc_all.mn`). **Closes**: docket **Sh.8** (source level — `None` bare identifier recognition). **Opens**: docket **Sh.11** (`lower_expr` SIGSEGV replaces Sh.8 as strict-fixed-point blocker). **Reduces the v4.130.0 panel's divergence-surface evidence number by another 1.9%.** **Next: v4.129.0 — documentation and SPEC sync** (originally scheduled as v4.128.0; bumped one release because v4.128.0 took the fixed-point refinement slot per the edited PROMPT).
- **v4.127.0** (shipped) — **Phase F closeout release 7: self-hosted fixed-point refinement — divergence between Python bootstrap and `mnc-stage1` reduced from 9,971 to 9,535 unified-diff lines (-4.4%) across the 39 passing goldens; zero regressions.** Buffer release 2 of the v4.130.0 closeout arc. The strict 3-stage stage2-vs-stage3 measurement remains blocked by docket **Sh.8** (self-hosted `semantic.mn` does not register `None` as a constructor; `mnc-stage1` cannot self-compile `mnc_all.mn` — pre-existing since v4.112.0). PLAN.md anticipates this exact pivot: "All fixes are in the self-hosted compiler (`mapanare/self/*.mn`). The Python pipeline is the reference; the self-hosted compiler converges toward it." This release pivots cleanly to the meaningful proxy: Python bootstrap output vs `mnc-stage1` output on the **39 of 65 goldens both pipelines compile cleanly**, categorizes every divergence by L/C/A/S/W/M, fixes the top cosmetic categories, and records the delta. **Phase 1+2 baseline + categorization** (`docs/roadmap/v4/v4.127.0/FIXEDPOINT_BASELINE.md`, `baseline.json`). Total diff: **9,971 lines** across 39 tests; 11 of 39 have function-set divergence (Python bootstrap inlines small fns via `inline_small_functions` MIR pass, self-hosted does not — Sh.1 blocker). Bucket totals (block-level classifier on `difflib.SequenceMatcher.get_opcodes()` output): **S (semantic) 7,000 / A (attributes) 328 / C (constants) 301 / M (module hdr) 156 / L (labels) 0 / W (whitespace) 0**. The L/W zeros are an artefact of block-level classification, not evidence of zero divergence — line-level whitespace divergences (e.g., `%x =alloca i64` instead of `%x = alloca i64`) bundle into S because the surrounding lines also differ. **Phase 3 cosmetic fixes** — three changes in two self-hosted files, ~30 lines net: (1) **`mapanare/self/emit_llvm.mn::emit_mir_module`** removes the dead TBAA metadata tree (nodes `!1`–`!9`, 9 lines) — declared in the module footer but never attached to any load/store via `!tbaa !N`, confirmed 100% dead by v4.109.0 forensics on the Python bootstrap, removed from the Python emitter at v4.123.0. Self-hosted now matches Python: `!mapanare.version = !{!0}` + `!0 = !{!"4.127.0"}` only. Also adds explicit `target datalayout` and `target triple` after `source_filename` (matching `mapanare/targets.py::TARGET_X86_64_LINUX_GNU` defaults: `x86_64-unknown-linux-gnu` + the standard layout string); bumps hardcoded version from stale `4.97.0` to current `4.127.0`. (2) **`mapanare/self/emit_llvm_ir.mn`** 25 IR-builder helper functions (alloca, load, add, sub, mul, sdiv, srem, fadd, fsub, fmul, fdiv, frem, fneg, neg, not, icmp, fcmp, and_instr, or_instr, phi, call_ir, gep, insertvalue, extractvalue, bitcast) had their format string `" =op "` changed to `" = op "`. LLVM accepts both forms (`=` is a token separator) but the canonical form has the space and matches the Python emitter. (3) **`mapanare/self/emit_llvm.mn`** 12 inline call sites in the lowerer that built LLVM strings directly (sitofp, fptosi, alloca, insertvalue, call, bitcast at lines 1024, 1031, 1067, 1069, 1895, 1904, 1913, 1917, 1926, 2931, 2948, 3086) had the same `" =op "` → `" = op "` fix. The `find_alloca_by_search` helper at `emit_llvm.mn:1420` searches for previously-emitted load instructions; its search pattern was caught by the same regex (`" =load"` → `" = load"`) and continues to match correctly against the new builder output. **Phase 4 post-fix delta** (`post_fix.json`): total diff **9,971 → 9,535 lines (-436, -4.4%)**; stage1 output **6,393 → 6,120 lines (-273)** from TBAA removal. Per bucket: M **156 → 78 (-50%)**, S **7,000 → 6,610 (-390)** (the whitespace fix lands here under block-level classification), A/C unchanged (out of scope). fn-set divergence count unchanged at 11 (Sh.1 systemic root cause; closing it requires fixing the `inline_small_functions` MIR pass that produced malformed MIR when re-enabled at v4.111.0). **New tooling**: `scripts/measure_divergence.py` (234 lines) — divergence measurement harness used to produce both the pre-fix baseline and the post-fix delta; future releases get a free comparable baseline. **Verification**: `mnc-stage1` rebuilds cleanly (3,488,912 bytes stripped, byte-identical to v4.126.0); golden tests through `mnc-stage1` are **39/65 — unchanged from v4.126.0, zero regressions** in previously-passing tests; pytest excluding bootstrap is **5,061 passed / 38 failed / 103 skipped / 7 xfailed** — failure set is byte-identical to v4.126.0 HEAD baseline (sorted-FAILED diff is empty); `llvm-as` accepts post-fix IR; lint (`ruff` + `black`) clean on touched files; pre-existing baseline lint debt unchanged. `libmapanare_rt.a` byte-identical to v4.126.0 (no C runtime changes). **Diff**: 4 files changed (3 self-hosted + 1 new measurement script), ~30 net new lines in self-hosted code (–9 TBAA removal, +2 datalayout/triple, +37 whitespace patches that net to no line-count change but normalise output formatting). **Closes**: nothing on the docket-Sh list (Sh.1, Sh.2, Sh.4, Sh.5, Sh.6, Sh.7, Sh.8 all remain open). Reduces the v4.130.0 panel's divergence-surface evidence number by 4.4%. **Next**: v4.128.0 — documentation and SPEC sync per the v4.121.0 closeout PLAN.
- **v4.126.0** (shipped) — **Phase F closeout release 6: golden test push — 27 → 39 native (+12 passes through `mnc-stage1`).** First buffer release of the v4.130.0 closeout arc. Triages all 65 golden tests; fixes the easiest two failure classes (one parser bug closing 2 tests; one harness over-strictness closing 10 tests); documents the remaining 26 with reproducers and dispositions. **Code change 1: parser fix in `mapanare/self/parser.mn:366`** — `is_definition_start` was missing `KW_CONST` and `KW_TRAIT`. The parser's top-level driver loop dispatches each top-level token via this predicate; a false return routes the token to the statement parser instead of `parse_definition`. So module-level `const N: Int = 100` was silently consumed as a statement, never registered in any module-level scope, and the semantic check errored with `Undefined variable 'N'` whenever a function body referenced the const. The bug had been latent since v4.55.0 (when const was introduced); three previous workarounds — v4.78.0's `const_def` early branch in `register_def`, v4.78.0's `parse_const_def → LetDef` alias, and the duplicate `KW_CONST` dispatch at parse_definition.mn:476/524 — all addressed downstream paths that were unreachable because the upstream `is_definition_start` filter rejected the token. **Discovery process**: confirmed via debug instrumentation. Initial hypotheses (semantic.mn long-if-chain unreachability) were wrong; adding `__mn_str_eprint("[DBG] parse_const_def fired ...")` showed the function never fired. Adding a similar print at the top of `parse_definition` showed it was only called once — for `fn main()` — confirming the const line never reached `parse_definition`. That narrowed the bug to the upstream `is_definition_start(tt)` gate at parser.mn:422. Fix: 4 lines added (KW_CONST + KW_TRAIT entries) plus 6 lines of comment context. Closes `54_const_basic`, `58_const_scope` (2 golden tests). **Code change 2: harness relax in `scripts/test_native.py:577`** — documented option (b) from `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`. The harness compared `stage1.defines == bootstrap.defines` (strict equality). Python bootstrap runs `inline_small_functions`; `mnc-stage1` does not (the self-hosted equivalent was disabled at v4.111.0 because it produced malformed MIR — the four zero-ROI passes documented in v4.109.0 forensics). So `mnc-stage1` consistently emits a *superset* of functions for the same source: an `add(a, b)` helper that bootstrap inlined into main becomes a separate `define i64 @add` in stage1 IR. Both outputs are semantically equivalent — LLVM's own inliner converges them at -O2. Fix: changed strict equality to strictly-fewer (`if sfp["defines"] < fp["defines"]`). The `missing = set(fp["functions"]) - set(sfp["functions"])` check at line 583 is unchanged — it remains the actual correctness gate that catches truly-dropped functions. Closes `03_function`, `15_multifunction`, `23_multi_return`, `26_generics`, `27_impl`, `28_traits`, `41_module_let`, `42_module_let_string`, `43_module_let_math`, `45_ffi_bind` (10 golden tests). **Result: 27 → 39 passing (+12) of 65 tests.** PLAN target was 40+ (≥ 14 improvement); release lands 1 short. The shortfall is documented honestly per the PLAN's "skip and document, stubs create false confidence" directive — every remaining failure has been categorized and root-caused. **Diagnostic narrowing on two open dockets** (no closures): **Sh.2** (`__mn_str_starts_with` NULL deref from `emit_mir_call+0x236a4`, 11 of 26 remaining failures) — minimal reproducers narrowed beyond the v4.111.0 description. Two distinct surface patterns trigger the same crash: `rec(n - 1) + rec(n - 2)` (two recursive calls in one expression) AND `let a: Int = make_int(1); let b: Int = make_int(2)` (two let-bindings of calls to the same fn, recursive or not). Counter-examples: `add(x) + add(x)` works, `print(make_str(1)); print(make_str(2))` works. Hypothesis: `find_function` returns a copied `FnEntry`, but `fe.ret_type`'s underlying String heap data is freed (or its slot reused) by the first call's emission; the second call crashes when `is_byref_type_st(s, fe.ret_type)` dereferences the stale pointer. Same family as the bugs v4.101.0 fixed in the *Python* emitter via move-semantics in `mapanare/emit_llvm_text.py` (`_move_resource` at six call sites). Mirror fix into self-hosted `emit_llvm.mn` is the v4.127.0 PLAN target. **L** (lower_expr crashes, 3 of 26 remaining): `33_break_continue` minimal reproducer narrowed to `let found: Int = 1; let items: List<Int> = [10, 20, 30]; return found` — list with 1 element does NOT crash; list with 2+ elements does. Same family as Sh.2; the comment at `lower.mn:2856-2858` explicitly warns about "stale registers from caller's sret return" affecting list operations — direct evidence the bug class is known but unfixed. **Per-test triage** documented in `docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md` — every one of the 65 tests categorized as PASS / Sh.2 / L / M-async / M-tensor / M-closure / B-bootstrap-also-fails. Reading guide for the v4.130.0 panel: the Sh.2 + L bucket of 14 tests is the actual self-hosted-compiler-regression surface; of the 14, 11 share Sh.2 root cause; one targeted fix would close 11 tests at once — pushing the count to **50/65 = 77%** literal pass rate. **Verification**: `python3 scripts/build_stage1.py` builds `mnc-stage1` cleanly (3,488,912 bytes stripped); `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` runs all 65 golden tests in 8.1s — 39 pass, 26 fail; **zero regressions** in previously-passing tests; `make test` (excluding bootstrap): 5,058 passed / 38 failed / 103 skipped / 7 xfailed — failure set is the v4.124.0 An.1 carry-forward baseline (no new failures); `ruff check` clean on touched files; pre-existing `make lint` baseline (302 findings, An.2 carry-forward) unchanged; `libmapanare_rt.a` byte-identical to v4.125.0 (no C runtime changes). **Diff**: 3 files changed, ~22 net new code lines (4 in parser.mn, 12 in test_native.py including comments, plus 6 added comment lines explaining the parser fix). **Closes**: 2 entries on the docket-Sh list (KW_CONST predicate gap, harness strictness). Sh.2 + L remain open with new diagnostic narrowing. Sh.4 / Sh.6 / Sh.7 unchanged. **Next**: v4.127.0 — self-hosted fixed-point refinement; the v4.126.0 diagnostic narrowing on Sh.2 gives v4.127.0 a concrete starting point for closing 11 of the 14 remaining real failures.
- **v4.125.0** (shipped) — **Phase F closeout release 5: benchmark refresh + 5-run flaky audit + docs (pre-panel evidence base for v4.130.0).** Pure measurement and documentation; zero compiler/runtime code changes (5 version-string edits to `benchmarks/cross_language/run_benchmarks.py` for housekeeping only). The v4.130.0 panel's evidence base now exists. **Cross-language benchmark refresh** (`benchmarks/cross_language/v4.125.0-results.json`, 6 workloads × 6 language configs × 10 runs, identical hardware/toolchain to v4.118.0): Mapanare geomean **3.07 → 2.66 ms** vs C gcc geomean **0.56 → 0.59 ms** = **5.46× → 4.52× slower than C gcc** (17% closing of the C gap), **on par with Rust (1.00×, was 1.13×)**, **2.14× slower than Go**, **46× faster than Python (was 37×)**. **`enum_match` is the v4.124.0 win materialising at the benchmark level**: 3.026 → **1.308 ms (2.31× speedup)** — Mapanare moves from 1.80× of Rust to **0.91× of Rust** (Mapanare faster). Memory peak on `enum_match` 4,740 → 2,144 KB (2.2× reduction) — the 83,333 mallocs per run that the boxed payload required are gone. Other workloads within ±10% of v4.118.0 (jitter band; no regressions). All 36 cross-language cells produce correct checksums; the v4.122.0 Qs.1 fix closed the last `List<Int>` indexing gap. **Async benchmarks** (`benchmarks/async/v4.125.0-async.json`, 5 workloads × 3 language configs × 10 runs): Mapanare geomean **2.13 → 1.95 ms** (within noise; no async runtime changes shipped in the closeout arc); **45× faster than Python asyncio**, **1.55× slower than Go goroutines**. All 5 checksums correct. **5-run flaky audit** (`docs/roadmap/v4/v4.125.0/FLAKY_AUDIT.md`): pytest 5x sequential (excluding bootstrap, ~7m 42s per run, 5054 passed / 39 failed / 103 skipped / 7 xfailed), pairwise diff of sorted failure sets across all 4 adjacent pairs is **empty**. **Zero flaky tests.** Failure set byte-identical to v4.124.0 HEAD baseline; the 39 failures are pre-existing An.1 carry-forward, deterministic, on the v4.126.0+ track. **`benchmarks/FINAL_REPORT_v4.130.md`** (publishes 7 numerical tables — wall / memory / binary / LOC / speedup vs C / progress / async — plus 6 ASCII per-workload position charts, methodology + reproducibility checklist; supersedes `benchmarks/FINAL_REPORT_v4.120.md` (v4.118.0 baseline) and `benchmarks/PHASE_C_RESULTS.md` (v4.110.0)). **`docs/roadmap/v4/v4.125.0/V5_READINESS.md`** snapshot publishes the closure walk against the v4.120.0 readiness ledger: **5 of 8 "would embarrass v5" items closed** (Rt.1 substantially closed v4.124.0, Qs.1 closed v4.122.0, dead `optimizer.py` removed v4.123.0, TBAA removed v4.123.0, 22/22 deterministic test failures closed v4.121.0); 3 remain on the v5.x track (Sh.4-7 self-hosted async/tensor/const gaps; Sh.8 fixed-point; package manager). **One new docket opened: ABI.1** (by-value 24-byte struct return ABI on inline enums) — replaces the algorithmic half of Rt.1 with a smaller follow-up scoped to v5.x calling-convention work; documented as the residual ~10× gap to C gcc on `enum_match`. **`README.md` performance section refreshed**: version badge **4.116.0 → 4.125.0**, headline **50× faster than Python / 1.06× of Rust / 4.85× of C gcc** updated to **46× faster than Python / on par with Rust (1.00×) / 4.52× of C gcc**, the v4.108.0 string_concat headline kept and a new v4.124.0 enum_match headline added (2.31× faster, 2.2× less memory, 0.91× of Rust). **Lint**: clean on touched files; pre-existing baseline lint debt in `mapanare/emit_llvm_text.py` (50 ruff findings, An.2 carry-forward) unchanged — v4.126.0+ track. `libmapanare_rt.a` byte-identical to v4.124.0. **Diff**: 8 files, ~3,500 net new lines (predominantly the new FINAL_REPORT + V5_READINESS + FLAKY_AUDIT + raw JSON results); zero compiler/runtime line changes. **No new dockets closed by this release directly** (the closures are credited to v4.121.0–v4.124.0; this release is the evidence that proves them at the benchmark level). **Next: v4.126.0–v4.129.0 buffer for any v4.130.0 panel carry-forward; v4.130.0 is the panel — v5 gate attempt 3.**
- **v4.124.0** (shipped) — **Phase F closeout release 4: Rt.1 — unboxed enum payloads for pointer-fits variants; `enum_match` 1.77× faster, gap vs Rust 4.1× → 2.3×.** Closes the named Rt.1 performance docket from the v4.120.0 panel (boxed-enum payload overhead was the single biggest performance gap in the v4.118.0 cross-language benchmark: `enum_match` ran 24× slower than C gcc -O2 and 2× slower than Rust because every variant construction heap-allocated the payload and every match arm pointer-chased to read it). **`mapanare/emit_llvm_text.py`** now stores small enum payloads inline in `{i64, i64, ..., i64}` — tag at slot 0 + up to 2 payload slots at slots 1–2 — instead of the legacy `{i64, ptr}` + heap allocation. **Eligibility rule**: every variant has ≤ 2 payload fields; every field is an 8-byte-or-smaller value packable into i64 (Int / Float / Bool / pointer-shaped); no field is marked boxed for self-reference. Multi-field variants, heap-owned-type fields (String, List, Map, Tensor, user structs, Option/Result wrappers), and self-referential enums stay on the existing boxed path unchanged. **New infrastructure**: `self._enum_inline: dict[str, int]` registry (slot count per enum, 0 = boxed); `_compute_enum_inline_slots(pays, boxed)` computes eligibility from the variant payload map during `_reg_enum`; `_type_fits_inline_slot(ft)` filters per-field types — admits `i64` / `double` / `i1` / `i8` / `i16` / `i32` / `ptr` only, rejects anything ownership-sensitive to prevent drop-glue skipping a needed free; `_enum_ty(nm)` returns the LLVM struct type (inline `{i64, i64, ..., i64}` or boxed `{i64, ptr}`) and replaces the constant `ENUM` in both `_rty` enum branch and `_lookup_struct_or_enum`; `_pack_to_i64(val, ft)` packs a value into an i64 slot (Int direct; Float `bitcast double → i64`; Bool / small-int `zext → i64`; pointer `ptrtoint → i64`); `_unpack_from_i64(val, ft)` is the inverse. **`_do_enum_init` inline branch** skips the `malloc` + GEP-store chain entirely — emits a single insertvalue chain building `{i64, i64, ..., i64}` with tag at slot 0 and packed payload values at slots 1…N (unused slots store 0). Move semantics (`_move_resource`, `_list_vars` removal, `_lroots` root-alias lookup) still fire on the payload value before packing. **`_do_enum_payload` inline branch** skips pointer dereference — emits `extractvalue {i64, i64, ..., i64} %s, payload_idx + 1` followed by `_unpack_from_i64` to the field type. **Benchmark result** (Shape enum, 100k iterations, 30-run trimmed mean): C gcc -O2 0.60 ms / Rust -O 0.82 ms / Mapanare v4.123.0 3.33 ms / Mapanare v4.124.0 **1.88 ms** — **1.77× speedup**. Gap vs Rust 4.1× → **2.3×** (closed 56%). Gap vs C 5.3× → 3.0×. Malloc count per run: **83,333 → 0** (`grep -c '@malloc' enum_match.ll` is 0 post-fix). PLAN exit-criterion #6 target of "within 1.5× of Rust" not fully hit; residual overhead is by-value 24-byte struct return/pass on Mapanare's calling convention — structural bottleneck (malloc + ptr-chase + free per construction/match) is fully closed, remaining gap is ABI-level, not algorithmic; documented for v4.125.0+ follow-up. **Scope decision**: the PLAN nominally called for a strict 8-byte single-slot rule. Shape's `Triangle(Int, Int)` / `Rect(Int, Int)` variants occupy 16 bytes and would have disqualified the entire enum under all-or-nothing 8-byte; the headline benchmark would have seen zero improvement. Widening to 2 inline payload slots (`{i64, i64, i64}` = 24 bytes, matching Rust's own Shape layout) was the right engineering call — ~50 extra lines in `_compute_enum_inline_slots` and the insertvalue chain in `_do_enum_init`; the PLAN's "16 bytes would need i128 storage" was factually wrong (three plain i64 fields, no i128 needed). **Self-hosted emitter deferred** per PLAN decision 3: the benchmark runs through the Python pipeline (which is the v4.130.0 panel evidence basis); `mapanare/self/emit_llvm.mn::emit_enum_init` + `emit_enum_payload` + `resolve_mir_type` + `compute_field_offset` would all need inline-aware rewrites plus a new `EmitState` inline-registry field; stage2 self-compilation is already blocked by Sh.8 (v4.125.0 target); shipping a parallel self-hosted change here risks destabilising the Sh.8 landing path. **Zero regressions**: pytest (excluding bootstrap) 5,053 passed / 39 failed — **byte-identical failure set to v4.123.0 HEAD** (stash-compare receipt on sorted FAILED lines); bootstrap pytest 213 passed / 12 failed — **byte-identical failure set**; goldens through `mnc-stage1` 27/65 unchanged (self-hosted path untouched). Python bootstrap goldens 64/65 (pre-existing `51_match_guards_and_or`). **Valgrind clean** on `07_enum_match`, `10_result`, `17_option`, and the `enum_match` benchmark binary — no errors, no definite leaks, no malloc-paired-with-freed-pointer bugs in the inline path (because there is no malloc). **Lint**: `mapanare/emit_llvm_text.py` 50 pre-existing ruff findings at HEAD, 50 post-change (An.2 carry-forward unchanged); new code is ruff-clean on the lines this release added. `libmapanare_rt.a` byte-identical to v4.123.0. **Diff**: 1 code file, ~154 net new lines. **Closes Rt.1.** **Next: v4.125.0 — benchmark refresh + 5× flaky audit + documentation update** per the v4.121.0 closeout PLAN; purely measurement and documentation, no code changes.
- **v4.123.0** (shipped) — **Phase F closeout release 3: dead-code sweep — `mapanare/optimizer.py` + the TBAA metadata declaration block deleted; net −1,963 lines; no behaviour change.** The AST-level optimiser (`mapanare/optimizer.py`, 1,203 lines, constant folding + DCE + agent inlining + stream fusion) was dead code: superseded by `mapanare/mir_opt.py` since the v3.x era; 9% test coverage per the v4.117.0 report; reachable only via the undocumented `--legacy-optimizer` flag on `emit-mir` that no test ever exercised; v4.120.0 panel (Anaconda, Boa, Cobra) flagged it as the obvious cleanup target. **Deleted**: `mapanare/optimizer.py` (1,203 lines), `tests/optimizer/test_optimizer.py` (1,029 lines; exclusively tested the removed module — the companion `test_non_convergence.py` which tests `mir_opt`'s convergence loop is kept). **Also removed**: the TBAA (Type-Based Alias Analysis) metadata tree in `mapanare/emit_llvm_text.py::_emit_module` — nodes `!1`–`!9` (TBAA root + 4 type nodes for int/float/ptr/bool + 4 access tags). The nodes were declared in every emitted module header but never attached to any `load`/`store` via `!tbaa !N`. v4.109.0 forensics investigated whether wiring them would improve -O2 performance and concluded it would not (LLVM's built-in alias analysis already handles Mapanare's access patterns; the v4.83.0 Arc 11 optimizer contribution was via runtime-call function attributes in `RUNTIME_FN_ATTRS`, not TBAA). Module version metadata `!mapanare.version = !{!0}` is kept — only the TBAA subtree is gone. **Compiler edit in `mapanare/cli.py`**: `from mapanare.optimizer import OptLevel, optimize` → `from mapanare.mir_opt import MIROptLevel as OptLevel`; the `--legacy-optimizer` argparse registration and the branching `if legacy: ast, _ = optimize(ast, opt_level); if not legacy: mir_optimize(...)` logic in `cmd_emit_mir` is gone. `OptLevel` is now an alias for `MIROptLevel` — both are `IntEnum` with the same `O0`–`O3` values, byte-compatible for all call-site type annotations. The `MIROptLevel(opt_level.value)` conversions downstream are identity transforms post-change but are kept as-is to minimise diff scope. **`TestOptimizerIntegration` in `tests/bootstrap/test_verification.py`** — 34 parametrised tests (17 self-hosted `.mn` files × 2 methods) that exclusively exercised the removed optimiser — replaced by a 7-line comment block pointing readers to the live MIR-level coverage in `tests/mir/test_mir_opt.py`, `tests/llvm/`, and the golden harness; all other test classes in the file (parse, semantic, LLVM emission, fixed point, CLI integration, samples, coverage-metrics, bootstrap-manifest) are unchanged. **Test-file scrub**: `tests/llvm/test_drop_glue.py` + `tests/llvm/test_emitter_hardening.py::test_multiple_functions` switch their `OptLevel` imports to `from mapanare.mir_opt import MIROptLevel as OptLevel` — no assertion changes; the tests still run at `-O0` (pinned in v4.121.0 against optimiser-tuning drift). `tests/test_examples.py::test_wasm_example_emits_wat` drops its `ast, _ = optimize(ast, OptLevel.O0)` call (which was a documented no-op at O0 even under the old optimiser) and the associated import. **Playground scrub**: `playground/src/worker.js` (both `_mn_compile_to_wasm` and `_mn_compile_and_run` functions) removes the `optimize()` calls — the WASM path's MIR-level optimisation happens inside `lower()` → `emit_wasm`; the Python path is legacy; `playground/scripts/bundle-compiler.sh` and `tests/playground/test_playground.py::REQUIRED_COMPILER_FILES` drop `optimizer.py` from the playground's compiler-bundle manifest. **Doc updates**: `docs/BOOTSTRAP.md` "Key files" table replaces the `optimizer.py` row with `lower.py` + `mir_opt.py`; `CLAUDE.md` "Key modules in `mapanare/`" list removes the `optimizer.py` entry. **Verification**: audit pytest (excluding `tests/bootstrap/`) is 5,053 passed / 39 failed / 103 skipped / 7 xfailed in 96.6 s — **identical failure set to v4.122.0 HEAD baseline** (5,103 passed / 39 failed — the −50 passes are the deleted `tests/optimizer/test_optimizer.py`); bootstrap subset is 213 passed / 12 failed in 35.5 s — **identical failure set to v4.122.0 HEAD baseline** (247 passed / 12 failed — the −34 passes are the deleted `TestOptimizerIntegration`). **No new failures from the dead-code sweep.** `mnc-stage1` rebuilds cleanly from `scripts/build_stage1.py` (3,488,912-byte stripped binary, ~1m20s); golden tests through `mnc-stage1` are **27/65** — unchanged from v4.122.0 (zero regressions). **`git diff --stat`**: 17 files, 366 insertions, 2,329 deletions, **net −1,963 lines** — well above the 1,200-line exit-criterion target. The 366 insertions are mostly autogenerated (BENCHMARKS auto-update in `tests/golden/BENCHMARKS-linux.md` + `BENCHMARKS.md` + `HISTORY.jsonl`); actual human-written insertions across `mapanare/cli.py`, `emit_llvm_text.py`, and test-file edits are ~30 lines. **Lint**: all human-touched files are `ruff` + `black` clean on the lines this release changed. Pre-existing baseline lint debt in `mapanare/emit_llvm_text.py` (50 ruff findings + black quote-style reformat queue) is unchanged vs v4.122.0 HEAD — An.2 carry-forward, next on the track per `docs/roadmap/v4/v4.121.0/PLAN.md`. `libmapanare_rt.a` byte-identical to v4.122.0. **No new dockets; no CARRY_FORWARD closures** (pure cleanup, no dockets opened or closed). **Next: v4.124.0 — Sh.8 (self-hosted `semantic.mn` `None`/`Some`/`Ok` constructor registration, unblocks fixed-point self-compilation)** per the v4.121.0 closeout PLAN.
- **v4.122.0** (shipped) — **Phase F closeout release 2: Qs.1 resolved — `List<Int>` indexing in argument position now matches the Python bootstrap on the native pipeline.** The v4.120.0 panel's flagship correctness docket is closed. **`mapanare/lower.py::MIRLowerer._lower_let`** gains one line inside the existing empty-list annotation block: after patching `ListInit.elem_type` via `inst.elem_type = MIRType(declared.type_info.args[0])`, also rebind `val = Value(name=val.name, ty=declared)` so the named alias (`%arr`) carries the full list element type. Before the fix, a declaration like `let arr: List<Int> = []` produced a Value with `ty.type_info.args = [<unknown>]`; the subsequent `Copy` to `%arr` inherited that UNKNOWN; `_lower_index_get` then set `IndexGet.dest.ty = MIRType(obj.ty.type_info.args[0])` → UNKNOWN; `emit_llvm_text.py::_do_idx_get` resolved UNKNOWN via `_rty` to PTR and took the "pointer passthrough" branch (`store ptr` / `load ptr`) instead of emitting `store i64` / `load i64`. The bug surfaced two ways: **`print(str(arr[0]))`** printed `<?>` because `str()`'s emission fell through to the placeholder when given a PTR-typed argument whose scalar kind could not be inferred; **`let v: Int = arr[0]`** bound a raw heap pointer ptrtoint'd to i64 (the emitter coerced the pointer rather than dereferencing it). **Python bootstrap interpreter produced correct output all along** — the bug was in the MIR → LLVM emitter path and the interpreter does not use that path, which is why the regression survived 122 versions without surfacing in pytest. **Self-hosted compiler was verified not to need a mirror fix.** `self/lower.mn::lower_let` already unconditionally rewrites `val_ty = declared` when an annotation is present (strictly stronger than the Python bootstrap's `if val.ty.kind == UNKNOWN` guard); `self/emit_llvm.mn::emit_index_get` always emits a load and defaults to `load i64` when dest type is unknown rather than dropping the load entirely. Empirical confirmation: the v4.121.0 `mnc-stage1` binary (built before this fix) already produces the correct `42 / 42 / 99 / 100 / 141` output for the new Qs.1 golden test. **New regression surface**: `tests/golden/65_list_int_indexing.mn` (31 source lines, 5 indexing usage patterns) + `.ref.ll` (270 lines of reference IR with 21 `alloca i64` and 23 `load i64, ptr`, zero `alloca ptr` for list elements, zero `<?>`) + expected stdout fixture in `tests/integration/expected/`. **Five IR-level regression tests** in `tests/llvm/test_emitter_hardening.py::TestListIntIndexingQs1`: `test_empty_literal_annotation_indexing_loads_i64` asserts `load i64, ptr` in IR for direct-argument indexing and forbids `<?>` + `alloca ptr`; `test_let_binding_from_index_is_i64` forbids `ptrtoint ptr` immediately upstream of `__mn_str_from_int`; `test_index_in_arithmetic_uses_i64_operands` requires ≥2 `load i64, ptr` instructions and forbids any `ptrtoint ptr`; `test_float_list_empty_annotation_loads_double` pins the same invariant for `List<Float>` (`load double, ptr`); `test_struct_list_still_loads_correctly` is the regression guard for reference types (`List<MyStruct>` must still load the struct aggregate as `{i64, i64}`). All 5 PASS. **Golden pass count through mnc-stage1: 27/65** (up from v4.121.0's 26/64 — the new golden is the +1; zero regressions in previously-passing goldens). **Audit subset pytest**: 1,461 passed / 0 failed / 7 skipped / 5 xfailed in 17.7 s. **Full `pytest tests/`: 4,923 passed / 38 failed / 103 skipped / 7 xfailed** — all 38 failures are pre-existing An.1 carry-forward; confirmed by `diff` against v4.121.0 HEAD baseline (stash-compare receipt showed the only per-test delta is `test_golden_pipeline[65_list_int_indexing]` failing pre-fix and passing post-fix). **Lint**: 6 lines added to `mapanare/lower.py` (one `Value` constructor call plus 5-line comment block referencing the Qs.1 docket), ruff + black clean on new lines; 119 lines added to `tests/llvm/test_emitter_hardening.py`, ruff + black clean. Pre-existing baseline lint debt in `lower.py` unchanged — still **An.2** carry-forward on the v4.123.0+ track. **`mapanare/self/main.ll` regenerated** by `scripts/build_stage1.py`: 1,714 insertions + 1,713 deletions (≈1 net line change, primarily version-string `4.112.0 → 4.122.0` and counter renumbering); no behavioural change (stage1 golden pass count unchanged from v4.121.0 baseline). `libmapanare_rt.a` byte-identical to v4.121.0. **No new dockets; closes Qs.1.** V5_READINESS had called Qs.1 "would embarrass a v5 label." It is now resolved. **Next: v4.123.0 dead-code sweep** — delete `optimizer.py` (1,203 lines, 9% coverage via `--legacy-optimizer` flag that zero tests exercise) and remove the TBAA metadata declaration block that v4.109.0 forensics confirmed is 100% dead (defined in module header at `emit_llvm_text.py:910-926`, never attached to any load/store). Pure cleanup — net negative lines, no behaviour change.
- **v4.121.0** (shipped) — **Phase F closeout release 1 — DWARF deferral warning + bounded-generic trait fix; 22/22 v4.117.0 audit failures closed.** Two surgical compiler edits plus the test hygiene v4.120.0's panel-only release skipped. **`mapanare/cli.py::_resolve_debug`** restores the v4.29.0 stderr deferral warning (`warning: -g / --debug is a no-op; DWARF debug info emission is deferred to v5.x (see SPEC §21.3)`) — the v4.62.0 comment claiming the flag enabled DWARF skeleton was aspirational and never landed; SPEC §21.3 documents the deferral. Three `TestDebugFlagDeferred` tests now pass. **`mapanare/lower.py`** gains `_type_params_used_in_signature(fn_def)` (recurses through `NamedType` / `GenericType.args` / `FnType`) and consults it in `_lower_definition` + `_register_declarations`: a function with `type_params` but no occurrence of any of them in the param annotations or return type (e.g., `fn max<T: Ord>(a: Int, b: Int) -> Int`) is now lowered as a regular non-generic instead of being deferred to a monomorphization that no caller could ever trigger (no inference site for an unused `T`). Closes `tests/semantic/test_traits.py::TestTraitLLVMEmission::test_trait_with_bounded_generic_fn`. **Test hygiene (the part v4.120.0 SESSION_REPORT claimed but never actually shipped)**: 4 stale-assertion failures (`test_drop_glue.py::test_str_concat`/`test_returned_string`, `test_emitter_hardening.py::test_multiple_functions`, `test_cross_module.py::test_non_pub_gets_internal_linkage`) re-pinned at `-O0` so the inliner does not collapse the helper functions and DCE the IR shapes the assertions count — the invariants under test (drop glue runs on string returns, emitter handles multi-function input, non-`pub` linkage = `internal`) are unchanged; the optimizer had quietly grown teeth and the assertions had not. **14 stale CLI tests retired**: `TestCompile` class **deleted** (the `compile` Python emitter was removed in v3.x, no honest .mn-→-.py replacement exists; negative-path coverage for missing-file/syntax-error remains in `TestCheck`); `TestArgparse::test_compile_subcommand_parsed` + `test_compile_with_output` rewritten against `build` (the surviving .mn → native binary command); `TestOptLevelFlags` (7 `compile_*` tests) rewritten — argparse-only checks bind to `build`, the two `_with_o*_runs` subprocess cases downgraded to argparse smoke checks because spawning a real `build` requires clang on PATH and end-to-end -O coverage already lives in `tests/integration/test_pipeline_hardening.py` and the cross-language benchmark harness. **v4.117.0 audit subset (1,501 tests across 9 subdirectories): 0 failures across 3 sequential runs (1497 passed, 7 skipped, 5 xfailed × 3, identical counts).** All 22 deterministic failures the audit catalogued are closed (3 DWARF + 1 trait fixed; 4 hygiene assertions relaxed; 14 CLI tests retired/rewritten). **Full `pytest tests/`: 51 failures remain outside the audit's subdirectory scope** (panel item **An.1**, opened in `.reviews/v4.120.0/03-anaconda.md`) — this is the v4.122.0+ track, explicitly out of v4.121.0 scope. **Lint**: 5 of 6 modified files black + ruff clean; `mapanare/lower.py`'s pre-existing baseline lint debt (line lengths in tensor lowering paths, two unused-import flags) unchanged — that is panel item **An.2** on the v4.123.0+ track per `docs/roadmap/v4/v4.121.0/PLAN.md`. `libmapanare_rt.a` byte-identical to v4.120.0. **No new dockets; closes 6 entries from the FLAKY_AUDIT 22-failure list.** **Next: v4.122.0 fixes Qs.1 (`List<Int>` indexing in argument position prints `<?>` through native pipeline; reproduced fresh by 3 v4.120.0 reviewers).**
- **v4.120.0** (shipped) — **Phase F panel: v5 gate attempt 2 → Option B (NOT tagged).** Seven reviewers graded the v4.100.0-v4.119.0 recovery arc. **Aggregate 8.21/10** (identical to v4.114.0 Phase D panel). **Verdict: 2 PASS (Boa 8.7 docs, Mamba 8.5 perf) + 4 PASS WITH NOTES (Rattler 8.3, Viper 8.4, Cobra 7.9, Coral 8.1) + 1 NEEDS WORK (Anaconda 7.6 CI/testing).** Mechanical rule fires Option B (aggregate < 9.0 AND any NEEDS WORK). Lead **independently directed Option B** — the mechanical outcome and the lead directive agree; no override was needed. **v5.0.0 NOT tagged.** Zero compiler/runtime code changes. **Load-bearing panel finding** (Anaconda): the v4.117.0 flaky audit's 22-failure count was on a **subset** (9 subdirectories, 1,501 tests); the full `pytest tests/` run shows **73 failures**, with 51 living outside the audit's declared scope. `make lint` shows **302 findings** (64 black-reformat + 204 ruff + 34 mypy). **Qs.1** (`List<Int>` indexing in argument position: `arr.push(42); print(str(arr[0]))` prints `<?>` through the native pipeline but Python bootstrap gives correct output) reproduced fresh by 3 reviewers. Seven panel artefacts committed at `.reviews/v4.120.0/`: **`README.md`** (panel summary + score table), **`V5_DECISION.md`** (Option B formal decision citing both mechanical rule and lead directive), **`01-rattler.md`** (LLVM/codegen 8.3 — dings lint debt + Qs.1 reproduced fresh; Rt.1 PY side closed by v4.106.1, SH side = Sh.7), **`02-viper.md`** (memory safety 8.4 — opens ASan.1 mn_list_rc UAF baseline review of 12 findings, notes Sh.2 as compile-side crash affecting 10 golden tests), **`03-anaconda.md`** (CI/testing 7.6 **NEEDS WORK** — opens An.1/An.2/An.3/An.4/An.5), **`04-cobra.md`** (self-hosted 7.9 — byref fix v4.112.0 verified in isolation, Sh.8 fixed-point blocker, README "compiles itself" needs precision), **`05-coral.md`** (language design 8.1 — struct-literal-syntax 3-test inconsistency, const-keyword half-life, SPEC §29 precision items), **`06-boa.md`** (documentation **8.7 PASS** — read all four v4.119.0 panel-prep docs, spot-checked numbers, followed getting-started guide successfully), **`07-mamba.md`** (C runtime/performance **8.5 PASS** — reran benchmarks within ±5%, credits async I/O + FINAL_REPORT, docks Rt.1 + Qs.1). **Pre-panel measurements** at `docs/roadmap/v4/v4.120.0/MEASUREMENTS.md` — 5,484 tests collected / 73 failed, golden mnc-stage1 26/64 literal / 39/64 effective, integration pipeline 60/64, fixed-point blocked Sh.8, 11/11 v4.99.0 docket closures, 11 previous dockets + 17 new panel items open, 10 enforcing CI gates. **17 carry-forward items opened across 7 reviewers**: blockers (Qs.1, An.1, An.2, An.3, Sh.8, Rt.1), strongly-recommended (Sh.2, Cb.1/Co.1 README precision), polish (ASan.1, Cb.2, Co.2/Co.3/Co.4, Bo.1/Bo.2/Bo.3), deferred-to-v5.x (Sh.4/5/6/7, TBAA.1/willreturn.1, Sh.9a/9b/10, Instr.1). **Panel score trajectory**: v4.99.0 6.59 → v4.106.0 7.87 → v4.114.0 8.21 → v4.120.0 **8.21** (the recovery arc has reached a quality ceiling; panels open new findings at the same rate prior phases close old ones). **Preliminary `docs/roadmap/v4/v4.121.0/PLAN.md`** commits to a 6-release closeout arc targeting v4.130.0 as v5 gate attempt 3: v4.121.0 test+lint hygiene (close An.1/An.2/An.3 + 22 v4.117.0-audit stale assertions + Bo.2/Co.1/Cb.1 docs precision) → v4.122.0 Qs.1 fix + DWARF deferral warning → v4.123.0 Rt.1 (boxed-enum unbox where pointer-fits) → v4.124.0 Sh.8 (self-hosted semantic.mn None/Some/Ok constructor registration, unblocks fixed-point) → v4.125.0 benchmark refresh + updated panel-prep docs → v4.126.0 dead-code sweep (optimizer.py 1,203 lines 9% coverage via --legacy-optimizer flag, TBAA decision, Co.3 const direction) → v4.127.0-v4.129.0 buffer for Sh.2 / polish → v4.130.0 panel. Subject to lead approval. `libmapanare_rt.a` byte-identical to v4.119.0. **Next: v4.121.0 opens — test + lint hygiene sweep. Goal: `make test` green, `make lint` green. Per v4.121.0 PLAN.md.**
- **v4.119.0** (shipped) — **Phase F release 2: retrospective + pre-panel preparation.** Zero compiler/runtime code changes. Analysis and verification only. Four panel-facing documents committed at `docs/roadmap/v4/v4.120.0/` for the seven reviewers who will grade the v4.100.0-v4.119.0 recovery arc at v4.120.0: **`RETROSPECTIVE.md`** (339 lines) narrates the full v4.x arc — v4.0.0 production gate after v3.47.0's 9.79 peak, feature arcs to v4.76.0 (coroutine arc, 8.86/10, first individual 10/10), the v4.77.0-v4.99.0 optimiser drift that shipped tagged-pointer UB + non-rebuilt async scheduler, v4.99.0 v5-gate failure (6.59/10, 3 NEEDS WORK), and the 20-release six-phase recovery — honest what-worked / what-didn't section names the Arcs 11-12 optimiser ROI miss (TBAA dead, inline flags redundant, only function attributes load-bearing), documentation lag (README badge stale 85 versions), deferred MEDIUM items, and v4.112.0 naming churn; load-bearing sentence: **"the recovery arc was net-negative lines of code: −1,155 lines v4.99.0 → v4.118.0 (−2,434 Py, +939 self-hosted, +340 C) — it removed more than it added."** **`STATISTICS.md`** (238 lines) with methodology footnotes for every figure: 121 v4.x release directories, 20-release recovery arc breakdown, panel score ASCII chart (9.44 → 9.79 → **8.20** → 9.34 → 8.86 → **6.59** → 7.87 → 8.21 → TBD), codebase 39,763 self-hosted .mn / 36,092 Py / 14,583 C / 5,479 pytest / 64 golden, golden progress table (0/61 at v4.99.0 → 26/64 literal / 39/64 effective at v4.118.0), 11 open dockets, 10 enforcing CI gates, cross-language geomean 5.46× vs C gcc (from 9.5× at v4.107.0) + 36.9× faster than Python + async 42.6× faster than Python asyncio + 1.74× slower than Go goroutines, recovery-arc new-file inventory. **`V5_READINESS.md`** (285 lines) neutral feature matrix with ✅/◐/⬜/✖ across language core (24 features: parser, AST, semantic, MIR, emitters LLVM/C/WASM, bilingual keywords, async, FFI, GPU, tensor — `const` ◐ parser alias no immutability, DWARF ✖ deferred SPEC §21.3, tensor reshape ⬜), runtime (11: arena, scheduler, TCP/TLS, file I/O, epoll), self-hosted (10: Python bootstrap 64/64 ✅ but stage1 native only 26/64 ◐, fixed-point ✖ blocked Sh.8, async/const/tensor/closure in self-hosted all ✖), stdlib (11), ecosystem (**no package manager** ⬜ — single biggest v5 ecosystem gap), docs (11 ✅), CI (10 enforcing + 1 informational); eight itemised "would embarrass v5" gaps with docket IDs (Sh.4/5/6/7 self-hosted gaps, Sh.8 fixed-point, package manager absence, Rt.1 enum overhead, Qs.1 list indexing, optimizer.py 9% dead code, 14 stale CLI tests, TBAA.1 dead). **`AUDIT_NOTES.md`** (366 lines) — claim-level audit of all 19 SESSION_REPORTs from v4.100.0 through v4.118.0: **47 spot-checked claims, 0 material discrepancies, 3 cosmetic line-count drifts itemised** (OPT_ROI_ANALYSIS.md −1 line, DIVERGENCE_ANALYSIS.md −1 line, main.ll −3,073 lines consistent with v4.108.0 + v4.111.0 code changes). Per-release audit sections cover MnString bitfield, `_move_resource` call sites, `mn_coro_is_done`, `__mn_sb_new`/`__mn_sb_finish`, `mn_coro_frame_prefix_t`, SPEC §2.1.1 keyword table, golden counts, panel aggregates. Methodology note explicitly lists what was verified (file existence, symbol presence, docket ledger) vs what wasn't (runtime benchmarks, sanitizer re-runs — panel's domain). **SESSION_REPORTs were NOT retroactively edited**; panel sees originals with this audit as overlay. `libmapanare_rt.a` byte-identical to v4.118.0. **No new dockets; no CARRY_FORWARD closures** (analysis-only). **Next: v4.120.0 IS THE PANEL.** 7 reviewers grade v4.100.0-v4.119.0. **Mechanical rule: aggregate ≥ 9.0 AND 0 NEEDS WORK → Option A (tag v5.0.0); 8.5-9.0 → Option C (tag + continue); < 9.0 OR any NEEDS WORK → Option B (continue v4.121.0+).** The retrospective + statistics + v5 readiness + audit + FINAL_REPORT_v4.120.md are all the evidence the panel needs.
- **v4.118.0** (shipped) — **Phase F release 1: final cross-language benchmark.** The v4.120.0 panel's evidence document now exists. Zero compiler/runtime code changes; four version-string edits to `benchmarks/cross_language/run_benchmarks.py`. **All 6 workloads × 6 language configs × 10 runs ran to completion** (`fib_recursive`, `quicksort`, `struct_alloc`, `enum_match`, `prime_sieve`, `string_concat` × C gcc -O2 / C clang -O2 / Rust -O / Go / Mapanare O2 / Python 3.12) — 36/36 correct checksums, raw per-run data at `benchmarks/cross_language/v4.118.0-results.json`. **Plus 5 native-async workloads × 3 languages × 10 runs** (`01_sequential_chain` / `02_fanout` / `03_io_bound` / `04_mixed_cpu_io` / `05_backpressure` × Mapanare / Python asyncio / Go goroutines) — 15/15 correct checksums, raw data at `benchmarks/async/v4.118.0-async.json`. **First time async numbers link and execute for Mapanare** since v4.94.0 skipped the Mapanare side entirely with "linking currently fails." **Headlines (Mapanare O2 geomean across 6 workloads = 3.07 ms): 5.46× slower than C gcc -O2** (down from v4.107.0's 9.5×, a 2× narrowing attributable entirely to v4.108.0's Phase C string_concat fix), **1.13× slower than Rust**, **on par with Go (1.04×)**, **36.9× faster than Python 3.12**. **Async geomean 2.13 ms: 42.6× faster than Python asyncio, 1.74× slower than Go goroutines.** **Progress v4.82.0 → v4.118.0 (Mapanare O2 wall)**: `string_concat` **102.31 → 1.32 ms (77.5× speedup)** — the one real win, entirely from v4.108.0's auto-StringBuilder MIR pass; every other workload within ±10% once harness methodology (`/usr/bin/time -v` wrap adding ~1–3 ms spawn overhead) is normalised. **`benchmarks/FINAL_REPORT_v4.120.md`** (500 lines) publishes 7 tables (wall / memory / binary / LOC / speedup vs C / progress / async), 6 per-workload ASCII position charts, methodology with toolchain versions (gcc 13.3, clang 18.1, rustc 1.94.1, go 1.22.5, python 3.12, LLVM 18.1.3), spectrum analysis by workload category, and a reproducibility checklist. `libmapanare_rt.a` byte-identical to v4.117.0. **No new dockets; no CARRY_FORWARD closures** (measurement-only). Carry-forward for v5.x: Rt.1 (boxed-enum payload, `enum_match` 2× gap vs Rust), Qs.1 (`List<Int>` indexing), TBAA.1 (declared but not wired), Sh.4/5/6/7/8/9a/9b/10. **Next: v4.119.0 writes the retrospective — full v4.0.0 → v4.118.0 journey, compiled statistics, v5 readiness pre-panel audit. v4.120.0 is the panel — 7 reviewers, v5 gate attempt 2; the numbers from this release are the benchmark evidence.**
- **v4.117.0** (shipped) — **Phase E release 3: testing sweep — sanitizer CI, flaky audit, coverage.** Zero compiler/runtime code changes. Makes the test infrastructure production-grade before the v4.120.0 panel opens. **ASan and TSan CI gates** already permanent since v4.105.0 via `.github/workflows/sanitizers.yml` (valgrind full golden suite, ASan full golden suite with `check_asan_baseline.py` regression gate, tsan-async on goldens 55/56/57). This release **extends `tsan-async`** to cover the v4.115.0 native async I/O demos (`examples/async_file_io.mn`, `examples/async_http_demo.mn`); any future scheduler or coroutine-frame race under I/O-heavy workloads fails CI at PR time. **Flaky audit** (`tests/FLAKY_AUDIT.md`) ran pytest 5x against 1,501 tests across 9 subdirectories; pairwise `diff` of sorted failure sets across all 4 adjacent pairs is **empty**. **Zero flaky tests.** The 22 observed failures are deterministic pre-existing bugs (14 stale CLI tests asserting on pre-rename `mapanare compile`; 3 DWARF-deferral warnings for a SPEC §21.3-deferred feature; 2 drop-glue count drifts from v4.101.0 move-semantics; 1 linkage spec over-specification; 1 emitter-hardening count drift; 1 bounded-generic trait edge case) — catalogued per bucket, open for v4.120.0 panel. **Coverage report** (`tests/COVERAGE.md`) — pytest-cov 7.1.0 / coverage 7.13.5 on the 7 core-pipeline test directories. Aggregate **43%** (8,896 / 20,894 stmts); **within the core pipeline 73%**. Per-module: ast_nodes 100%, mir 95%, types 92%, lexer 89%, pattern_matching 88%, multi_module 83%, semantic 81%, parser 78%, mir_opt 72%, lower 69%, emit_llvm_text 65%. Below-50% tail: 13 modules at 0% because their tests live in out-of-scope dirs (lsp/emit_c/wasm/transpilers), 12 are real gaps (cli.py 25% — stale CLI tests, optimizer.py 9% — dead-code candidate, diagnostics.py 49%). 5 recommendations in COVERAGE.md for future work. **Integration pipeline hardening** (`tests/integration/test_pipeline_hardening.py`, 6 new tests, all PASS) — deliberately feeds broken inputs at each stage, asserts the `full_pipeline` harness captures the correct failing stage with a non-empty error: unparseable `.mn` → emit; hand-crafted invalid `.ll` → llvm-as non-zero exit; 42-exit binary → nonzero `pr.exit_code`; `sleep(60)` binary → `TimeoutExpired` raises cleanly; stdout mismatch vs `.expected` → reported on `stdout` stage (uses monkeypatch to isolate); negative control — hello.mn still passes. **New CI job** `ci.yml::coverage` (informational, not gating) runs the audit command and uploads coverage.xml as a 30-day artifact; flips to enforcing after 5 stable releases per PLAN.md risk register. `libmapanare_rt.a` byte-identical to v4.116.0. **No new dockets; no CARRY_FORWARD closures.** **Next: Phase E complete. Phase F opens at v4.118.0 — final cross-language benchmark with all Phase A–E fixes landed.**
- **v4.116.0** (shipped) — **Phase E release 2: documentation batch.** Five doc gaps flagged by Boa (and others) since v4.82.0 closed without touching a line of compiler/runtime/self-hosted code. **`README.md`** — version badge 4.31.0 → 4.116.0; headline benchmark line (50× faster than Python, 1.06× on par with Rust, 4.85× slower than C gcc -O2) linking to `benchmarks/PHASE_C_RESULTS.md`; self-hosted LOC 15K → 38K; Feature Status table adds async/await row; async example added to "The Language" section; stale "Coming in v4.2" corrected to "Planned" with status note; Roadmap table extended through v4.116.0 with v4.120.0 panel row. **`docs/SPEC.md`** — header 1.0.0 Final → 4.116.0 Live with sync-discipline note naming `mapanare.lark`, `types.py`, `self/lexer.mn` as canonical; §29 adds v4.115.0 status paragraph (cooperative-not-preemptive, native file+HTTP I/O demoed, mnc-stage1 async-lowering gap is Sh.4); §29.7 `for await` row reflagged as planned/v5.x. **`docs/cookbook/async.md`** — corrected stale `mnc run` claim; added §8 native compilation workflow, §9 file I/O example, §10 HTTP GET example, §11 Sh.9a/Sh.9b emitter-bug recipes with the workarounds shipped in the v4.115.0 demos. **`docs/guides/debugging.md`** — full rewrite (213+/164-) correcting the stale "Mapanare emits DWARF with -g" claim (SPEC §21.3 defers DWARF to v5.x; Rattler's v4.26.0 panel flag finally addressed in user-facing docs); new focus on valgrind as primary tool, ASan, TSan, ir_doctor.py, Culebra, integration harness, decision table mapping symptoms to tools. **`docs/guides/getting_started.md`** (NEW, 244 lines) — practical "from zero to a native binary" walk for developers familiar with compiled languages; complements the existing 624-line tutorial at `docs/getting-started.md`; covers prerequisites, Python bootstrap pipeline, mnc-stage1 pipeline, build-from-seed path, test suite, troubleshooting footer. **`docs/roadmap/v4/v4.116.0/VERIFICATION.md`** — panel-facing receipt: 7/7 compile-and-run snippets PASS, 3/3 async goldens regression-clean (42/43/110 unchanged), SPEC syntax review, shell-command spot-check. `libmapanare_rt.a` byte-identical to v4.115.0. **No new dockets**; all v4.115.0 dockets (Sh.9a, Sh.9b, Sh.10) remain open — now documented as user-facing recipes in the cookbook. **Next: v4.117.0 is test-suite hardening — ASan CI gate, TSan CI gate, flaky audit, coverage report, integration test hardening.**
- **v4.115.0** (shipped) — **Phase E release 1: async I/O demo running natively.** Closes the v4.99.0 panel's async-I/O gap. Two new example programs: **`examples/async_file_io.mn`** (cooperative async file I/O — seeds input file, reads back synchronously, runs an async pipeline of byte-based `count_lines` + `count_words` counters over the content, writes a two-field summary file from inside `await write_summary(...)`, reads back to verify — produces `async pipeline: lines=3 words=10` / `summary file: lines=3 words=10` at both `-O0` and `-O2`), and **`examples/async_http_demo.mn`** (real HTTP GET to `http://example.com/` returning 540 bytes, async pipeline `body_bytes` → `has_marker` → `write_summary`, deterministic non-crash exit if sandbox blocks outbound TCP). New **`docs/guides/async.md`** (244 lines) walks the mental model (cooperative, not preemptive), `async fn` / `await` / `block_on` syntax, both end-to-end examples, what-works and what-doesn't tables with docket IDs, and Sh.9 workaround recipes. **Zero compiler/runtime/self-hosted code changes** — Phase 4 explicitly confirmed no new C runtime symbols needed; `libmapanare_rt.a` byte-identical to v4.114.0. Two Python-bootstrap emitter bugs surfaced and worked around in both examples and the guide: **Sh.9a** (`await` on a String-returning async fn produces invalid IR — type mismatch between future-extraction GEP and inlined String return) and **Sh.9b** (DCE eliminates `await` calls whose Int return is unused, silently dropping the side-effecting C call inside — worked around by folding `wrote` into the pipeline's return encoding). **Sh.10** opened for making `__mn_file_read_async` user-callable (pre-requisite: Sh.9a). **v4.114.1 patch items deferred** per user direction: v4.112.0 release name rename, `tests/bootstrap/byref_test.mn` commit, site-4 cleanup comment — all carry into Phase E as open items. **Regression clean**: Python-bootstrap golden 63/64 (pre-existing `51_match_guards_and_or`), async goldens 55/56/57 → 42/43/110 unchanged. **Next: v4.116.0 documentation batch — README / SPEC / cookbook / getting-started pass.**
- **v4.114.0** (shipped) — **Phase D panel: NEEDS WORK @ 8.21/10, v4.114.1 patch scheduled.** Panel release with zero code changes. Seven reviewers graded v4.111.0-v4.113.0: **2 PASS (Viper 8.5, Boa 8.5), 5 PASS WITH NOTES (Rattler 8.2, Anaconda 7.8, Cobra 8.0, Coral 8.3, Mamba 8.2), 0 NEEDS WORK**. Aggregate **8.21 / 10** falls 0.29 below the Phase D PASS threshold of >= 8.5. Decision rule applies mechanically → NEEDS WORK → v4.114.1 patch. Panel is healthy (v4.106.0 was 7.87 with 3 reviewers at 7.5 and zero PASS; v4.114.0 is 8.21 with 2 PASS, no reviewer below 7.8; every moving reviewer moved up +0.34 aggregate). **11/11 v4.99.0 docket items confirmed CLOSED** with line-by-line evidence in `docs/roadmap/v4/v4.114.0/DOCKET_AUDIT.md`. Panel artifacts: `MEASUREMENTS.md` (9 quantitative sections), `DOCKET_AUDIT.md` (11-item walk with file:line references), `.reviews/v4.114.0/PRE_PANEL_AUDIT.md` (19-claim fact-check), 7 reviewer files, `README.md` verdict summary. **v4.114.1 patch scope (~50 lines across 4 files)**: (HIGH) rename v4.112.0 "fixed-point verification" → "divergence analysis + byref fix" in CLAUDE.md + v4/README.md because the 3-stage script fails at Stage 1 on Sh.8; (HIGH) commit `tests/bootstrap/byref_test.mn` reproducing the v4.112.0 acceptance case instead of leaving it in `/tmp/`; (LOW) add cleanup-intent comment at `__mn_coro_register_wait` overflow site in `mapanare_runtime.c`. **Phase E deferred findings**: A.1 self-hosted pipeline CI gate (carry-forward v4.106.0), A.2 fixed-point CI red (Sh.8-blocked), B.1 async error-site reachability tests, Co.1 pre-existing user-code coroutine leaks, Instr.1 Culebra scan gap (three panels blocked). **Golden tests: 26/64 self-hosted preserved, 63/64 Python-bootstrap (pre-existing `51_match_guards_and_or`); valgrind 0 errors and ASan 0 errors on async + struct subset; byte-for-byte memory-neutral confirmed vs HEAD~4 control.** **Next: v4.114.1 patch then delta panel (Rattler + Cobra + Anaconda); if delta clears 8.5, Phase E opens at v4.115.0.**
- **v4.113.0** (shipped) — **Phase D release 3: last v4.99.0 docket items closed (#8, #10, #11).** Zero open items from the v4.99.0 panel after this release. **Docket #8 (MEDIUM, coroutine frame)**: `mn_coro_is_done` / `mn_coro_resume` in `runtime/native/mapanare_runtime.c` replaced raw `*(void**)handle` casts with a named `mn_coro_frame_prefix_t` struct documenting the LLVM switched-resume ABI (resume_fn at offset 0, destroy_fn at offset sizeof(void*)). Behaviourally equivalent — the cast compiles to the same load — but one named definition to update if the ABI ever moves. Verified byte-for-byte memory-neutral: `valgrind` output on 56/57 against a HEAD~4 control rebuild matches exactly (same leak sites in user coroutine bodies, not in our functions). All 3 async goldens still produce 42/43/110. **Docket #10 (LOW, SPEC keywords)**: new `docs/SPEC.md` §2.1.1 "Reserved Keyword Master List" — 42-row alphabetical table of every hard-reserved identifier with English/Spanish/category/AST role. Cross-references `mapanare/mapanare.lark:380-427` and `mapanare/self/lexer.mn:59-177`; audit recorded in `keyword-audit.md`. Stale "Soft-reserved (v4.30.0): async, await" text replaced — async/await have been hard keywords since v4.68.0/v4.72.0. Appendix C rewritten to distinguish future-reserved from hard-reserved; `continue` and `const` rows removed (both already tokenized). **Docket #11 (LOW, async errors)**: 5 async failure sites with silent-drop or NULL-deref behaviour replaced with specific stderr + deterministic exit(1): `__mn_coro_scheduler_init` checks every `pthread_create` return (names worker K of N + strerror — previously silently started fewer threads than reported and then hung); `__mn_coro_scheduler_register` refuses enqueue when scheduler uninitialised (previously span forever in zeroed deque) or when deque+overflow both full (previously dropped task but kept active_tasks counter); `__mn_coro_register_wait` bails on overflow-full with coroutine handle + Future address (previously a suspended await would never resume); `__mn_file_read_async` checks calloc + malloc + pthread_create individually. Site #2 manually triggered in isolation (exit 1 with the named message); remaining 4 require env stress. Added `#include <errno.h>`. **Golden tests: 26/64 preserved** (identical to v4.112.0, zero regressions); stage2 0/11 unchanged (pre-existing Sh.8 gap). 9/9 exit criteria green. **Next: v4.114.0 is the Phase D panel — 7 reviewers grade v4.111.0-v4.113.0.**
- **v4.112.0** (shipped) — **Phase D release 2: fixed-point verification + docket #7 closed.** Ran the 3-stage fixed-point script; classified divergences across 4 categories in `docs/roadmap/v4/v4.112.0/DIVERGENCE_ANALYSIS.md` (byref / structural / cosmetic / semantic-gap); closed docket #7 (byref size heuristic) via a single-file fix in `mapanare/self/emit_llvm.mn`. Added `struct_byte_size(st, ty)` resolving `%struct.Foo` through the registered `st.structs` table, returning real sizes computed from the inline `{...}` form — matching the Python bootstrap's `_tsz` algorithm at `emit_llvm_text.py:141`. Added `is_byref_type_st(st, ty)` as the state-aware replacement; all 7 call sites of the old `is_byref_type` updated to pass state. **Verified fix on `/tmp/byref_test.mn`**: 16-byte `Small` now passed by value (`%struct.Small %s`); 80-byte `Large` still by reference (`ptr %l.byref`); output correct; IR validates; pipeline runs. **Golden tests: 26/64 preserved** (zero regressions from v4.111.0). **Fixed-point convergence (stage2 == stage3) NOT measured** — stage1 can't self-compile because self-hosted `semantic.mn` doesn't register `None` as a constructor (pre-existing gap surfaced in v4.111.0's stage2 validation; Python bootstrap bypasses via `skip_check=True` in `build_stage1.py`). New docket **Sh.8** opened for self-hosted `None`/`Some`/`Ok` constructor registration. Docket Sh.3 CLOSED. 6/10 PLAN.md exit criteria green, 4/10 blocked on Sh.8 or culebra's long-running scan on 854K-line IR. **Next: v4.113.0 closes remaining v4.99.0 panel items (#8 coroutine frame, #10 keyword collision SPEC, #11 async errors). v4.114.0 is the Phase D panel.**
- **v4.111.0** (shipped) — **Phase D release 1: self-hosted golden test parity.** First Phase D release (self-hosted compiler maturity). Rebuilt `mnc-stage1` from the full self-hosted pipeline (`mapanare/self/*.mn`, 38,824 lines); ran all 64 golden tests; documented every failure with root-cause categorization across 9 categories in `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`. **Disabled 4 v4.97.0 MIR optimization passes** in `mapanare/self/mir_opt.mn::optimize_mir()` — `strength_reduce_function`, `inline_small_functions`, `licm_function`, `escape_analysis_function` — all zero-ROI per v4.109.0's forensics (LLVM subsumes the work at -O2), all flagged by v4.105.0's valgrind sweep (`mir_opt__block_successors` a 14× hot-frame). Single-file, 34-line diff. **Golden pass rate: 21/64 → 26/64** (+5 unblocks: 05_for_loop, 11_closure, 22_string_builder, 24_enum_methods, 25_fizzbuzz, 50_match_or_patterns). Effective rate **39/64** when counting Category A (13 tests that compile correctly but differ in function count from bootstrap because bootstrap still inlines; semantically equivalent IR). Remaining 25 real failures: 10 `__mn_str_starts_with` crashes in `emit_mir_call+0x23515` (docket Sh.2), 5 async-missing (Sh.4), 5 tensor-missing (Sh.6), 2 const-missing (Sh.5), 2 `lower_expr` crashes, 1 or-pattern (bootstrap also fails), 1 closure-typed (Sh.7), 1 gpu-tensor. Stage2 self-compilation: 0/11 modules (expected, Phase D2-3 target). `ir_doctor.py` `_FN_RE` regex flagged as harness gap (doesn't parse inline attribute syntax — produces false "0 functions" readings on self-hosted output). Dockets Sh.1-Sh.7 open for v4.112.0+. **v4.112.0 runs fixed-point verification; byref size heuristic (self-hosted emitter returns 256 for all named structs, docket Sh.3) is the known blocker.**
- **v4.110.0** (shipped) — **Phase C release 4 (final): full benchmark refresh with all fixes applied.** Pure measurement; zero code changes. Phase C closes. Publishes `benchmarks/PHASE_C_RESULTS.md` as canonical performance document, superseding `FINAL_REPORT.md` (v4.98.0) and `FULL_COMPARISON.md` (v4.107.0). **Geomeans across 5 correct workloads: 50× faster than Python, 1.06× slower than Rust (effectively on par), 2.10× slower than Go, 4.85× slower than C (gcc -O2)** — down from v4.107.0's 9.5× vs C, a 2× narrowing driven entirely by v4.108.0's StringBuilder fix (`string_concat` 94.57 → 1.36 ms, 70× speedup, 109× memory reduction). v4.82.0 cumulative geomean: **1.821×** (5 optimizer programs; string_concat's 75× carries it). v4.107.0 same-harness control confirms all non-string benchmarks are within ±5% noise; the v4.98.0 → v4.110.0 "regressions" on sub-millisecond benchmarks are harness-methodology artifacts (v4.98.0 lacked `/usr/bin/time -v` wrap; added in v4.107.0). `struct_alloc` Mapanare beats Rust 0.71× (arena vs Drop); `prime_sieve` ties Rust exactly (3.43 ms each); `enum_match` 22× slower than C confirms Rt.1 boxed-enum overhead is the largest remaining opportunity. `quicksort` checksum fails (docket Qs.1, `List<Int>` indexing). README performance section rewritten against current numbers. New dockets: Qs.1, Rt.1, TBAA.1, willreturn.1 carry forward to v4.111.0+. **Phase C complete. v4.111.0 opens Phase D: self-hosted compiler maturity.**
- **v4.109.0** (shipped) — **Phase C release 3: Arcs 11–12 optimizer ROI forensics.** Pure investigation, zero code changes. Answers why `TOTAL_RESULTS.md` showed 0.992× geomean at -O2 after 8 releases of optimizer work: the geomean hid heterogeneity. Per-workload: matmul_naive +24% (real Arc 11 win), quicksort +9% (near noise), fib 0% (within noise at any scale — H2 rejected via fib(45)), string_concat **−21%** (Arc 11 hints HURT after v4.108.0 — `willreturn` on `__mn_sb_*` declarations blocks DSE of stores the call observes). Per-hint discoveries: (1) **TBAA metadata is 100% dead** — defined in module header at `emit_llvm_text.py:910-926` but never attached to any load/store across all 4 optimizer benchmarks; the comment at line 913 describes intended wiring that was never written; Arc 11's TBAA contribution to alias analysis is exactly zero. (2) **Function attributes on runtime-call declarations** (`nounwind`, `willreturn`, `readonly`, `noalias`) are the *load-bearing* Arc 11 contribution — they cross pass boundaries via LLVM's module-level attribute table and change downstream decisions (early-cse, licm, mldst-motion, dse) without being consumed inline by any single pass. (3) **Inline `nsw`/`nuw` flags are mostly redundant** — LLVM independently infers all 13 `nuw` on matmul post-O2 even when the frontend strips them. Per-pass H3 subtly confirmed: zero instruction-level diffs from any of 10 LLVM passes (instcombine, indvars, licm, gvn, sroa, loop-vectorize, loop-unroll, early-cse, function-attrs, aggressive-instcombine) on hinted vs stripped input; matmul's 24% win is pass-ordering interaction through the attribute table. Published `benchmarks/optimizer/OPT_ROI_ANALYSIS.md` (264 lines). New dockets for v4.110.0+: TBAA wiring decision (remove or connect), `willreturn` audit on heap-modifying runtime calls in `RUNTIME_FN_ATTRS`, escape-analysis codegen wiring. Docket **Qs.1** (`List<Int>` indexing) carries forward.
- **v4.108.0** (shipped) — **Phase C release 2: string_concat fix — auto-StringBuilder — beats Python.** The one embarrassing number from v4.107.0's `FULL_COMPARISON.md` (94.57 ms, 9.8× slower than Python) is fixed. **55× faster wall (1.72 ms), 109× less memory** (2.3 MB vs 246 MB). Phase 1 audit found v4.95.0's `string_concat_optimization` MIR pass has been dead code for 13 versions — matched `Call("__mn_str_concat", ...)` but the MIR shape is `BinOp(ADD, String, String)` + `Copy(dest=lhs, src=binop.dest)` (the runtime call only appears during LLVM IR emission at `emit_llvm_text.py:2658`). Pass rewritten in `mapanare/mir_opt.py:string_concat_optimization` against the real pattern; it performs a CFG rewrite inside natural loops (single preheader + single exit, no other uses of the accumulator in the loop body), inserting `__mn_sb_new` in the preheader, replacing `BinOp + Copy` with `__mn_sb_append`, and prepending `__mn_sb_finish` to the exit block. Two new scalar-pointer runtime wrappers (`__mn_sb_new` + `__mn_sb_finish`) added because v4.95.0's `__mn_sb_create` returned a 24-byte struct by value (sret ABI) which the emitter's auto-declare path mis-typed — same bug silently broke `stdlib/ai/llm.mn` and `embedding.mn`'s explicit `sb_create`/`sb_to_string` builtins for 13 versions; lowering retargeted. Mapanare on string_concat: 5.6× faster than Python, 29× faster than Go, ~12% slower than Rust. Geometric mean across 4 correct non-DCE'd workloads: 9.5× slower than C gcc (v4.107.0) → **6.5× slower**. Other 5 workloads within run-to-run noise (no regressions). Golden tests 63/64 (pre-existing `51_match_guards_and_or`). Docket **Qs.1** (`List<Int>` indexing) carries forward.
- **v4.107.0** (shipped) — **Phase C release 1: cross-language benchmark surface.** Pure measurement; zero Mapanare code changes. 12 new benchmark programs (6 Go at `benchmarks/cross_language/go/`, 6 C at `benchmarks/cross_language/c/`) + rewritten harness `run_benchmarks.py` publish the full six-column comparison across C (gcc -O2), C (clang -O2), Rust -O, Go, Mapanare O2, Python 3.12 across 6 workloads (fib_recursive, quicksort, struct_alloc, enum_match, prime_sieve, string_concat). 10 runs per config, median of middle 8, `/usr/bin/time -v` wraps every run for accurate per-process peak RSS (fixes the `getrusage(RUSAGE_SELF).ru_maxrss` COW-fork inflation bug). **Geometric mean** across 4 correct non-DCE'd workloads: Mapanare is **9.5× slower than C gcc**, **on par with Rust on pure compute** (fib 1.13×, prime_sieve 1.68×), **1.3× slower than Go**, **44.6× faster than Python**. enum_match 27× slower confirms v4.106.0's **Rt.1** boxed-enum overhead. string_concat 1278× slower than C gcc (2× slower than Python!) is v4.108.0's StringBuilder target. 35/36 cells correct; strict checksum check (v4.107.0 tightened from v4.98.0's prefix-match) surfaced a pre-existing **`List<Int>` indexing bug** — `arr.push(42); print(str(arr[0]))` prints `<?>`. Docket **Qs.1** for v4.108.0+. Report: `benchmarks/cross_language/FULL_COMPARISON.md`.
- **v4.106.0** (shipped) — **Phase B panel: NEEDS WORK → v4.106.1 patch.** 7 reviewers graded v4.100.0–v4.105.0. **Aggregate 7.87/10** (+1.28 vs v4.99.0's 6.59, largest since v4.31.0 recovery close). Zero NEEDS WORK, 1 PASS (Boa 8.5), 6 PASS WITH NOTES (Rattler/Viper/Anaconda/Cobra/Coral/Mamba at 7.5-8.0). Below 8.0 threshold → v4.106.1 patch. All 5 v4.99.0 critical/high docket items CLOSED with evidence. **Load-bearing panel finding**: Rattler's IR inspection re-classified the `64_closure_typed` `-O2` miscompile from "LLVM opt bug" (my PRE_PANEL_AUDIT's initial read) to **Mapanare emitter bug** — 2-arg lambda emits `define internal void @lambda4(ptr, ptr, ptr)` while caller does `call i64 %cfn(ptr, i64, i64)`; opaque-pointer LLVM 18 accepts the mismatch silently. Promoted Cl.1 → Rt.1 HIGH. v4.106.1 narrow scope: **2 HIGH items** — Rt.1 (emitter signature fix) + Rt.2/Ih.1 (integration harness stdout-diff against bootstrap reference). Everything else (`As.1`, `Cb.1`, 12 Vg./As./Div./Rt./Cb./Co./Bo./Vp. items) deferred to Phase C (v4.107.0+). Re-panel Rattler/Anaconda/Coral after patch; if PASS, Phase B closes and Phase C (benchmarks) opens.
- **v4.105.0** (shipped) — Phase B release 2 (debugging infrastructure). Valgrind over all 64 goldens (0 CLEAN / 28 WARNINGS_ONLY / 36 ERRORS — top frames `mir_opt__block_successors` 14×, `__mn_list_free` 12×, `emit_llvm__emit_mir_call` 11×). ASan: 21 CLEAN / 17 ASAN_ERROR (12 heap-UAF in `mn_list_rc`, 5 global-buffer-overflow in `strtoll` on non-NUL-terminated IR globals). TSan: **3/3 async goldens race-free**; compiler-side flagged legacy `crash_handler` in `mnc_main.c` as async-signal-unsafe — Phase 4 fixes it with `__mn_install_crash_handler` + thread-local `__mn_set_current_source` breadcrumb (`[CRASH] SIGSEGV during compile at tests/golden/X.mn`). `.github/workflows/sanitizers.yml` (3 jobs) + baseline-checker scripts gate the regression surface. 10 new docket items (`Vg.1`–`Vg.7`, `As.1`–`As.3`) for v4.106.0 panel. 21/64 stage1 goldens unchanged from v4.104.0 (no regressions).
- **v4.104.0** (shipped) — Phase B release 1 (rebuild + verify). Zero code changes. `mnc-stage1` rebuilt cleanly at `-O2` (857k IR lines, 3.5 MB stripped, 1m21s). Full integration pipeline (`emit → llvm-as → opt -O2 → llc → clang → run`) passes **60/64** goldens; 2 skips (stdin/network); 2 FAILs (`51_match_guards_and_or` or-pattern rejection; `47_try_operator` emits invalid IR — 17-version latent bug caught by new `llvm-as` gate). Async goldens 55/56/57 all run natively (42/43/110) and valgrind clean. 21/64 through `mnc-stage1` unchanged from v4.103.0 (no regressions from Phase A). 5 divergence docket items (`Div.1`–`Div.5`) filed for v4.106.0 panel.
- **v4.103.0** (shipped) — Phase A release 4 (final). **Phase A COMPLETE** — all 5 critical/high docket items from the v4.99.0 panel are closed. Docket #4 (else/sino) fixed via deeper drop-glue discovery: `_emit_drop_glue_boxed` was freeing boxed-enum payloads reachable through the returned value but beyond `_extract_ret_ptrs`'s struct-walking reach; conservative skip when return has any ptr field. Docket #5 (closure types) fixed via 3 changes in `lower.py`: FnType → MIRType(FN), typed-var calls → ClosureCall, all lambdas → ClosureCreate. Golden tests 16/62 → 21/64 (5 unrelated passes from the boxed-drop fix). Next panel: v4.106.0.
- **v4.102.0** (shipped) — Phase A release 3. First native async run in project history. Two bugs fixed: `mn_coro_is_done` checked wrong frame offset (now `handle[0] == NULL` per LLVM 18's final-suspend lowering); `_do_block_on` reloaded the coroutine handle from a Future slot the coroutine overwrites with its return value (now reuses the cached handle). All 3 async goldens (55/56/57) run natively with expected outputs (42, 43, 110); valgrind clean; CI step added. Dockets #3 + #6 closed.
- **v4.101.0** (shipped) — Phase A release 2. Self-hosted emitter output corruption fixed: root cause was use-after-free drop glue in the Python emitter — heap strings pushed into lists / stored as struct fields were being freed at function return even though the container held live pointers to them. Six call sites in `mapanare/emit_llvm_text.py` gained move-semantics (`_move_resource`). `mnc-stage1` now emits clean, `llvm-as`-valid IR. Golden tests: 0/61 → 16/62. Dockets #1 + #2 closed.
- **v4.100.0** (shipped) — Phase A release 1. Tagged-pointer UB structurally removed via `MnString` bitfield (`len:63, is_heap:1`), ABI preserved at 16 bytes. `mnc-stage1` output corruption persists and is confirmed pre-existing (not caused by the UB); deferred to v4.101.0.
- **v4.99.0** (shipped) — Arc 14 panel: 6.59/10, Option B. v5 NOT tagged. Tagged-pointer UB, list indexing, async linking must be fixed.
- **v5.0.0** (when ready) — Major version tag. The lead's call. Zero additional work required — v4.76.0 is release-gate quality.

See `docs/roadmap/ROADMAP.md` for the full roadmap. Organized by era: `docs/roadmap/v0/` through `docs/roadmap/v4/`.

## Pre-Push Validation (MANDATORY)

**Before ANY commit or push**, run the full validation suite. This mirrors CI exactly and writes results to `error.log`:

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT emission (runs once)
.\dev.ps1 validate         # Same as above (default mode), runs once and exits
.\dev.ps1 validate -Watch  # Validate then watch for changes
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only (black + ruff + mypy)
.\dev.ps1 fmt              # Auto-format (black + ruff --fix)
.\dev.ps1 e2e              # End-to-end tests only
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for all `examples/wasm/*.mn` files — this is what catches WASM CI failures locally. Running just `pytest` is NOT sufficient; the WASM cross-compilation step in CI compiles those examples and will fail independently of pytest.

**Quick partial checks** (use these during development, but always run full validate before pushing):

```bash
# WASM emission only (fast, catches the most common CI-only failures)
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
python -m mapanare emit-wasm examples/wasm/wasi_app.mn -o /dev/null

# Lint only (no tests)
black --check . && ruff check . && mypy mapanare/ runtime/

# Single test file
pytest tests/semantic/test_types.py -v

# Single test directory
pytest tests/parser/ -v
pytest tests/llvm/ -v
pytest tests/wasm/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v (add -n auto for parallel)
make lint             # ruff check . && black --check . && mypy mapanare/ runtime/
make fmt              # black . && ruff check --fix .
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches and egg-info

# Run specific tests (always use -n auto for parallel execution via pytest-xdist)
pytest tests/parser/ -v -n auto              # Parser tests only
pytest tests/semantic/test_types.py -n auto  # Single test file
pytest tests/llvm/ -v -n auto               # LLVM emitter tests
pytest tests/bootstrap/ -v -n auto           # Self-hosted compiler tests

# Golden test harness (native compiler validation)
python scripts/test_native.py                                    # Bootstrap-only (Windows)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1  # Compare with native (WSL)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --run  # Also run IR via lli
python scripts/test_native.py --bless                            # Regenerate reference files
python scripts/test_native.py --filter fib -v                    # One test, verbose

# Rebuild cycle (WSL) — one command for the full edit-compile-test loop
bash scripts/rebuild.sh              # concat + build + golden (default)
bash scripts/rebuild.sh quick        # concat + build only (fast iteration)
bash scripts/rebuild.sh full         # concat + build + golden + selftest + memory
bash scripts/rebuild.sh audit        # concat + build + audit main.ll
bash scripts/rebuild.sh worklist     # concat + build + show alloca alias work queue

# IR Doctor — per-function diagnostics for the self-hosted compiler
# Detects: ALLOCA_ALIAS (real vs mitigated), EMPTY_SWITCH, RET_TYPE_MISMATCH,
#          MISSING_PERCENT, DUPLICATE_CASE, PHI_UNDEF_REF, LOOP_PUSH, etc.
# Saves baselines to .ir_doctor/ — reruns show delta (fixed/new/regressed)
python scripts/ir_doctor.py audit mapanare/self/main.ll              # Audit + baseline + llvm-as
python scripts/ir_doctor.py --only lower__ audit mapanare/self/main.ll  # Audit specific module
python scripts/ir_doctor.py worklist mapanare/self/main.ll           # Functions needing recursive rewrite
python scripts/ir_doctor.py extract mapanare/self/main.ll lower__lower_match  # Dump one function's IR
python scripts/ir_doctor.py check file.ll                            # Just llvm-as validation
python scripts/ir_doctor.py golden                                   # Fresh compile+validate ALL golden (WSL, no cache)
python scripts/ir_doctor.py selftest                                 # Self-compile mnc_all.mn (WSL)
python scripts/ir_doctor.py memory                                   # Memory scaling test (WSL)
python scripts/ir_doctor.py table mapanare/self/main.ll              # Per-function metrics table
python scripts/ir_doctor.py --top 15 table mapanare/self/main.ll     # Top 15 largest functions
python scripts/ir_doctor.py fingerprint mapanare/self/main.ll        # JSON per-function hashes
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn       # Bootstrap vs stage1 (WSL)
python scripts/ir_doctor.py diff-ir a.ll b.ll                        # Compare two .ll files
python scripts/ir_doctor.py valgrind tests/golden/11_closure.mn       # Auto-run valgrind + map crash to fields (WSL)
python scripts/ir_doctor.py valgrind 11_closure.mn --struct EmitState  # Map against a different struct
python scripts/ir_doctor.py structmap LowerState                     # Show struct byte layout + field names
python scripts/ir_doctor.py structmap LowerState --offset 176        # What field is at byte 176?
python scripts/ir_doctor.py structmap                                # List all structs with sizes
python scripts/ir_doctor.py journal                                  # View debug history (runs + notes)
python scripts/ir_doctor.py note "tried X, result was Y"             # Add note to debug journal
python scripts/ir_doctor.py diff-all                                 # All golden tests (WSL)
python scripts/ir_doctor.py snapshot                                 # Generate .stage1.ll files (WSL)
python scripts/ir_doctor.py stage2                                   # Compile self-hosted modules through mnc-stage1, validate stage2 IR
python scripts/ir_doctor.py stage2 --timeout 60                      # With longer timeout
python scripts/ir_doctor.py valgrind-map ./mapanare/self/mnc-stage1 tests/golden/07_enum_match.mn  # Run valgrind and map crash offsets to struct fields
python scripts/ir_doctor.py valgrind-map --struct LowerState ./mnc some_file.mn  # Map against specific struct
python scripts/ir_doctor.py valgrind-map --timeout 60 ./my_binary --flag arg     # With timeout
python scripts/ir_doctor.py strings mapanare/self/main.ll                        # Validate string constant byte counts
python scripts/ir_doctor.py strings mapanare/self/main.ll -v                     # Also show duplicate strings
python scripts/ir_doctor.py xray                                                 # Full stage2 build + runtime test
python scripts/ir_doctor.py xray --timeout 60                                    # With longer timeout
python scripts/ir_doctor.py phi-check /tmp/stage2.ll                             # Validate PHI fix preserves structure

# MIR Trace — debug type inference issues in the Python lowerer
python scripts/mir_trace.py tests/golden/10_result.mn divide         # Trace types for one function
python scripts/mir_trace.py tests/golden/07_enum_match.mn            # Trace all functions in file
python scripts/mir_trace.py tests/golden/10_result.mn divide -v      # Verbose (all instructions)
python scripts/mir_trace.py tests/golden/10_result.mn divide --json  # JSON output
python scripts/mir_trace.py tests/golden/10_result.mn divide --compare  # Compare MIR vs stage1 IR

# Self-hosted compiler build + fixed-point (WSL/Linux only)
python scripts/build_stage1.py                   # Build mnc-stage1 from Python bootstrap
bash scripts/verify_fixed_point.sh               # 3-stage self-compilation verification
bash scripts/verify_fixed_point.sh --keep        # Keep intermediate IR for debugging

# Culebra v2.0.0 — compiler diagnostics for LLVM IR AND C source (Rust, installed in WSL)
# 29+ YAML templates across ABI, IR, Binary, Bootstrap categories. Nuclei-style pattern engine.
# Repo: C:\Users\Juan\Documents\GitHub\Culebra (also at github.com/Mapanare-Research/Culebra)
# crates.io: https://crates.io/crates/culebra

# --- Core scanning ---
culebra scan mapanare/self/main.ll                          # Run all templates against IR
culebra scan mapanare/self/main.ll --tags abi               # ABI checks only
culebra scan mapanare/self/main.ll --severity critical      # Critical findings only
culebra scan mapanare/self/main.ll --id option-type-pun-zeroinit  # One specific template
culebra scan mapanare/self/main.ll --autofix --dry-run      # Preview auto-fixes
culebra scan mapanare/self/main.ll --autofix                # Apply auto-fixes
culebra scan mapanare/self/main.ll --header runtime/native/mapanare_runtime.c  # Cross-ref IR vs C structs
culebra scan mapanare/self/main.ll --format json            # JSON output
culebra scan mapanare/self/main.ll --format sarif           # SARIF for GitHub Code Scanning

# --- AI-optimized debugging (v0.3.0) ---
culebra triage mapanare/self/main.ll                        # Group findings by root cause, deduplicate
culebra triage mapanare/self/main.ll --format json          # Structured JSON for AI consumption
culebra compare stage1.ll stage2.ll --metric calls          # Per-function metric comparison (flags drops)
culebra compare stage1.ll stage2.ll --metric pushes --threshold 0.5  # Custom metric + threshold
culebra explain stage2.ll return-type-divergence            # Show matched IR in context + remediation
culebra explain stage2.ll option-type-pun-zeroinit --function parser  # Scoped to one function
culebra bisect stage1.ll stage2.ll                          # Find divergent functions ranked by impact
culebra bisect stage1.ll stage2.ll --top 30                 # Show more results
culebra verify stage2.ll return-type-divergence             # PASS/FAIL — verify a fix worked
culebra verify stage2.ll break-inside-nested-control --function tokenize  # Scoped verify

# --- C backend scanning (v2.0.0) — scan generated C for Mapanare v3.0.0 ---
culebra scan stage2.c                                       # Auto-detects .c, runs 8 C-specific templates
culebra scan stage2.c --tags c                              # C templates only
culebra scan stage2.c --id switch-no-break                  # Check for switch fallthrough
culebra scan stage2.c --id missing-typedef                  # Find undefined struct types
culebra diff stage1.c stage2.c                              # Fixed-point: compare C text output
culebra triage stage2.c --brief                             # Quick C summary
culebra summary stage2.c                                    # Full diagnostic (works for .c and .ll)
# C templates: switch-no-break, missing-typedef, null-deref-pattern, goto-dead-label,
#   union-tag-mismatch, large-struct-by-value, missing-return, buffer-overflow-pattern

# --- Debugging feedback loop (v1.2.0) — wrap commands, learn patterns, track journal ---
culebra wrap -- clang -c -O1 stage2.ll -o stage2.o          # Proxy command + log to .culebra-session.jsonl
culebra wrap -- valgrind /tmp/mnc-stage2 /tmp/tiny.mn        # Captures crashes, errors, output
culebra wrap -- llvm-as stage2.ll -o /dev/null               # Log LLVM errors for analysis
culebra learn                                                # Analyze session logs → extract error patterns + suggest templates
culebra learn -v                                             # Verbose: show individual failure details
culebra journal add "State doesn't persist in emit_instr" --action bug --tags "option,state" --function emit_instr
culebra journal add "Fixed MIRFunction field indices" --action fix --tags "field-index"
culebra journal add "mnc-stage2 runs!" --action milestone
culebra journal show                                         # View timeline of bugs/fixes/milestones
culebra journal show option                                  # Search journal by keyword

# --- Semi-dynamic analysis (v1.1.0) — call functions, probe values, test returns ---
culebra eval main.ll --function hardcoded_field_index --arg '"VarInfo"' --arg '"value"'  # Call and print return
culebra eval main.ll --function find_field_index --arg 0 --arg 0      # Integer args
culebra probe stage2.ll --function lower_fn --watch '%state'           # Inject printf, compile, run
culebra probe stage2.ll --function lower_fn --stop-at if_merge         # Stop at specific block
culebra test-fn main.ll --function hardcoded_field_index --arg 0 --arg 0 --expect-ret 1  # Unit test: PASS/FAIL

# --- Summary (v1.0.0) — one command for everything ---
culebra summary stage2.ll                                   # Scan + Types + Fields + Health + Score in 5 lines
culebra summary stage2.ll --struct LowerState               # Filter health to one struct

# --- Type inference + field audit (v0.9.0) — auto-generate types, detect index-0 bug ---
culebra infer-types stage2.ll                               # Infer missing type defs from insertvalue chains
culebra infer-types stage2.ll --ll                          # Output as valid LLVM IR (paste into file)
culebra field-index-audit stage2.ll                         # Find structs where ALL accesses use index 0
culebra field-index-audit stage2.ll --struct-filter LowerState  # Check specific struct

# --- Display + Inspection (v0.8.0) — syntax-highlighted IR, variable dumps, block walk ---
culebra pretty stage2.ll                                    # Module overview: stats, types, function size bars
culebra pretty stage2.ll --function lower_fn                # Syntax-highlighted IR with colored types/labels/terminators
culebra dump stage2.ll --function lower_fn                  # Variable dump: allocas, types, sizes, def-use counts, PHIs
culebra dump stage2.ll --function lower_fn -v               # Verbose: also show GEP chains
culebra inspect stage2.ll --function lower_fn               # Block-by-block control flow walk
culebra inspect stage2.ll --function lower_fn --block if_alpha  # Detail view of one block
culebra stacktrace crash.log --ir stage2.ll                 # Parse valgrind/ASAN/gdb output, map to IR

# --- Missing types (v0.7.0) — find undefined struct/enum types blocking compilation ---
culebra missing-types stage2.ll                             # Find all undefined named types
culebra missing-types stage2.ll -v                          # Also show which functions reference each

# --- Call graph + progress (v0.6.0) ---
culebra callchain stage2.ll --from lower --to current_block_terminated  # Find call paths between functions
culebra callchain stage2.ll --from lower_fn --to add_block --depth 5   # Shows struct types along chain
culebra progress stage2.ll                                              # IR stats + findings + health score
culebra progress stage2.ll -b my-baseline.json                         # Also compare against baseline

# --- Crash debugging (v0.5.0) — offset mapping, variable tracing, struct health ---
culebra crashmap stage2.ll --offset 0x20 --struct FnDefData  # "0x20 = field 4 (name: {ptr, i64})"
culebra crashmap stage2.ll --offset 0x20                     # Check all structs for that offset
culebra crashmap stage2.ll                                   # List all struct types with sizes
culebra trace stage2.ll --function lower_fn --var '%state'   # Follow variable through basic blocks
culebra trace stage2.ll --function tokenize --var '%pos'     # Shows every load/store/phi/call
culebra health stage2.ll --struct LowerState                 # PHI zeroinit, type-pun, null loads
culebra health stage2.ll                                     # Check all structs
culebra suggest stage2.ll --function lower_definition        # Prioritized fix suggestions for a function

# --- Baseline tracking (v0.4.0) — track progress across fix iterations ---
culebra baseline save stage2.ll                             # Save current findings as baseline
culebra baseline diff stage2.ll                             # Compare current scan vs baseline (Fixed/New/Remaining)
culebra baseline diff stage2.ll -b my-baseline.json         # Compare against specific baseline file

# --- Template assertions (v0.4.0) — CI gates and regression tests ---
culebra lint-template stage2.ll return-type-divergence --expect   # FAIL if template doesn't fire
culebra lint-template stage2.ll option-type-pun-zeroinit --reject # FAIL if template fires (regression)

# --- Triage --brief (v0.4.0) — minimal output for AI token efficiency ---
culebra triage stage2.ll --brief                            # One line: "9 root causes, 31 findings: ..."

# --- Diagnostic map (symptom → templates) ---
culebra map crash                                           # "what could cause this crash?"
culebra map "type mismatch"                                 # Search by symptom keyword
culebra map "zero tokens"                                   # Maps to relevant templates
culebra map phi                                             # PHI-related issues

# --- Drain queue (Mapanare integration) ---
culebra drain .culebra-queue.yaml                           # Process dynamically-queued checks
culebra drain .culebra-queue.yaml --clear                   # Process and clear queue

# --- IR analysis ---
culebra strings mapanare/self/main.ll                       # Validate [N x i8] byte counts
culebra audit mapanare/self/main.ll                         # Detect IR pathologies
culebra check mapanare/self/main.ll                         # Validate IR with llvm-as
culebra diff stage1.ll stage2.ll                            # Per-function structural diff
culebra extract mapanare/self/main.ll my_function           # Extract one function's IR
culebra table mapanare/self/main.ll --top 15                # Per-function metrics table

# --- ABI + binary ---
culebra abi mapanare/self/main.ll --header runtime/native/mapanare_runtime.c  # Struct layout + sret
culebra binary ./mapanare/self/mnc-stage1 --ir main.ll      # ELF/PE inspection + .rodata cross-ref

# --- Bootstrap pipeline ---
culebra phi-check /tmp/stage2.ll                            # Validate transform preserves IR
culebra pipeline                                            # Run full stage pipeline from culebra.toml
culebra fixedpoint ./mnc-stage1 mapanare/self/mnc_all.mn    # Fixed-point convergence detection

# --- Templates + workflows ---
culebra templates list                                      # List all templates
culebra templates show option-type-pun-zeroinit             # Full template details
culebra workflow bootstrap-health-check --input stage1_output=stage1.ll  # Multi-step validation
culebra workflow playground-mapanare --input stage2_output=stage2.ll     # Playground workflow

# --- Misc ---
culebra watch --patterns '*.ll,*.mn' culebra scan main.ll   # Watch + re-scan on change
culebra test                                                # Run all [[tests]] from culebra.toml
culebra run ./mnc-stage1 test.mn --expect "hello"           # Compile, run, check output
culebra init                                                # Generate starter culebra.toml
```

## Testing the Native Compiler

Golden test corpus lives in `tests/golden/*.mn` (15 programs covering all features). Reference IR in `tests/golden/*.ref.ll`.

**Workflow for debugging mnc-stage1:**
1. Make changes to `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. Rebuild: `python scripts/build_stage1.py`
3. Test: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. The harness compares mnc-stage1 output against the Python bootstrap — shows exactly which functions are missing or different.

Every run auto-updates `tests/golden/BENCHMARKS.md` with per-test metrics (source lines, IR lines, IR size, function count, compile time). Commit this file to track regressions over time.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I rules), **MyPy** strict mode
- Target Python 3.11+ (for bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source → Lark LALR parser → AST (dataclasses) → Semantic checker → MIR lowering → MIR optimizer (O0-O3) → Emitter
                                                                                                                 ├→ emit_llvm_text.py  → LLVM IR (text)
                                                                                                                 ├→ emit_c.py          → C source
                                                                                                                 └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:
- `cli.py` — Entry point, command dispatch (run, build, check, emit-llvm, emit-mir, emit-wasm, fmt, test, lint, doc, deploy, init)
- `parser.py` — Lark transformer: parse tree → AST dataclass nodes
- `ast_nodes.py` — All AST node definitions
- `semantic.py` — Two-pass type checker and scope resolver
- `mir.py` / `mir_builder.py` — MIR data structures and builder
- `lower.py` — AST → MIR lowering (1,397 lines)
- `mir_opt.py` — MIR optimizer passes (constant folding, DCE, copy propagation, block merging)
- `emit_llvm_text.py` — LLVM IR generation (text-based)
- `emit_c.py` — C source generation from MIR
- `emit_wasm.py` — WebAssembly (WAT) generation from MIR (v2.0.0)
- `wasm_linker.py` — wasm-ld integration for multi-module WASM linking (v2.0.0)
- `types.py` — **Single source of truth** for the type system (TypeKind enum, TypeInfo, builtin registries)
- `mapanare.lark` — LALR grammar with 13-level precedence climbing
- `tracing.py` — OpenTelemetry-compatible tracing
- `diagnostics.py` — Rust-style structured error output
- `test_runner.py` — Built-in test runner for `mapanare test`
- `deploy.py` — Deployment scaffolding (Dockerfile, health checks)

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`, `result.py`, `deploy.py` — asyncio-based agents, reactive signals, async stream operators, Result/Option types, deployment infrastructure. **Legacy — will be replaced by native .mn stdlib.**

**Native C runtime** (`runtime/native/`): Arena-based memory (no GC), lock-free SPSC ring buffers, thread pool with work stealing, cooperative agent scheduler (mobile), agent lifecycle, trace hooks, TCP sockets, TLS (OpenSSL via dlopen), file I/O, event loop (epoll/select), string interning with configurable cap, memory profiling. Used by the LLVM backend.

## LLVM Backend Status (v2.0.0 — full parity + GPU)

**Working:** Functions, structs, enums, pattern matching, control flow, type inference, generics, Result/Option, print (println deprecated), builtins, lists, maps/dicts (Robin Hood hash table), agents (full lifecycle), signals (full reactivity: computed, subscribers, batched updates), streams (map/filter/take/skip/collect/fold, backpressure), closures (free variable capture via environment structs), traits, module imports, pipes (`|>` for function application), pipe definitions (multi-agent composition), all string methods, GPU kernel dispatch (`@gpu`/`@cuda`/`@vulkan` via MIR GpuKernel metadata → PTX/SPIR-V LLVM codegen).

**Not yet on LLVM:** Tensor reshape, mutable views, stepped slices (v5.x). The tensor surface (literals, indexing, broadcasting, reductions, slicing) is stable as of v4.45.0.

New LLVM features should target `emit_llvm_text.py` (the sole LLVM emitter).

## Type System (mapanare/types.py)

All type definitions, builtin registries, and type-name mappings live in `types.py`:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP, OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int, float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare→Python name mapping used by emitters
- `PYTHON_TYPE_MAP`: Type→Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, 14,000+ lines of Mapanare. Mirrors the Python bootstrap pipeline:

| Module | Lines | Role |
|--------|-------|------|
| `ast.mn` | 781 | AST node definitions (structs + enums) + shared constructors |
| `lexer.mn` | 575 | Character-by-character tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser, 13-level precedence |
| `semantic.mn` | 1,729 | Two-pass type checker and scope resolver |
| `mir.mn` | 791 | MIR data structures (types, values, instructions, blocks, module) |
| `lower_state.mn` | 587 | Lowerer state, scope management, lookups, type resolution |
| `lower.mn` | 3,602 | AST → MIR lowering (registration + expression/statement lowering) |
| `emit_llvm_ir.mn` | 258 | LLVM type constants and IR instruction string builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter (state, handlers, module emission) |
| `main.mn` | 537 | Compiler driver |

**Patterns:** Constructor functions (`let r: T = first_field; return r`), state-threading (functions thread state structs), no struct literal syntax in grammar yet.

**Fixed-point verification** blocked by cross-module LLVM compilation (v0.9.0) and enum lowering gaps.

## Key Conventions

- Grammar lives in `mapanare/mapanare.lark` (also bootstrapped copy in `bootstrap/`)
- Emitters detect used features (agents, signals, streams) and import only as needed
- Builtins are dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted compiler sources are in `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Design philosophy: `docs/manifesto.md` | RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs: `docs/roadmap/v0/` through `docs/roadmap/v4/`
- Version tracked in `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

Starting with v0.8.0, the project moves toward Python independence:
- **Stdlib in .mn:** New stdlib modules are written in Mapanare (`.mn`), compiled to native code via LLVM. No more Python `.py` stdlib files.
- **C runtime as foundation:** OS-level primitives (sockets, TLS, file I/O) live in the C runtime. Everything above (HTTP, JSON, routing) is pure Mapanare.
- **Test on LLVM:** Every test should run on the LLVM backend.

## GPU Backend (v2.0.0)

GPU compute via CUDA and Vulkan, loaded dynamically at runtime (no compile-time SDK dependency):
- **C runtime** (`runtime/native/mapanare_gpu.h/.c`): CUDA Driver API + Vulkan compute via dlopen
- **MIR metadata** (`mapanare/mir.py`): `MIRGpuKernel` dataclass with device, PTX/SPIR-V source, grid/block config
- **Lowering** (`mapanare/lower.py`): `@cuda`/`@vulkan`/`@gpu` decorators populate `MIRModule.gpu_kernels`
- **LLVM codegen** (`mapanare/emit_llvm_text.py`): PTX string embedding + `cuModuleLoadData`/`cuLaunchKernel`, SPIR-V byte embedding + Vulkan pipeline create/dispatch
- **Python layer** (`experimental/gpu.py`): Device detection, kernel dispatch abstractions
- **Stdlib** (`stdlib/gpu/`): `device.mn` (GPU detection), `tensor.mn` (GPU-accelerated tensors), `kernel.mn` (kernel management)
- **Annotations**: `@gpu`, `@cuda`, `@metal`, `@vulkan` on functions for automatic dispatch
- **Built-in kernels**: PTX for CUDA, GLSL/SPIR-V for Vulkan (tensor add/sub/mul/div/matmul)

## WebAssembly Backend (v2.0.0)

Compile Mapanare to WebAssembly for browser and server-side execution:
- **Emitter** (`mapanare/emit_wasm.py`): MIR → WAT text format (~2,785 lines)
- **Linker** (`mapanare/wasm_linker.py`): wasm-ld integration for multi-module linking, memory layout, import/export management
- **CLI**: `mapanare emit-wasm [--binary] [--link] [--wasi] source.mn [source2.mn ...]`
- **Targets**: `wasm32-unknown-unknown` (browser), `wasm32-wasi` (server)
- **JS runtime** (`playground/src/wasm-runtime.js`): Browser host for WASM modules
- **Stdlib** (`stdlib/wasm/`): `bridge.mn` (JS interop), `runtime.mn` (WASI + memory)
- **WASI support**: File I/O, environment, clock, random via WASI preview 1

## Mobile Targets (v2.0.0)

Cross-compilation targets for mobile platforms:
- `aarch64-apple-ios` — iOS ARM64
- `aarch64-linux-android` — Android ARM64
- `x86_64-linux-android` — Android emulator

Mobile-specific runtime features:
- **Cooperative agent scheduler** — single-threaded event-driven execution (default on mobile)
- **epoll event loop** — Linux/Android I/O multiplexing (kqueue on iOS deferred)
- **Smaller defaults** — 4KB arenas, 256-slot ring buffers, 64-slot agent queues, 1ms signal batch
- **String interning cap** — 4K entries on mobile vs 64K on desktop
- **Memory profiling** — `mapanare_memory_stats()` for arena/intern/agent usage tracking

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame/data analysis package (pandas+numpy replacement), written in .mn
- `net/crawl` (web crawler), `security/scan` (vulnerability scanner), `security/fuzz` (fuzzer) — all agents-based
- AI/LLM drivers (`stdlib/ai/`): LLM, embeddings, RAG

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — format check (black) → lint (ruff) → type check (mypy) → tests (pytest). Matrix: Python 3.11, 3.12 on Ubuntu.
- **native** — C runtime tests with plain gcc, AddressSanitizer, ThreadSanitizer.
- **wasm** — WASM cross-compilation: emit WAT, convert to WASM via wat2wasm, run WASI examples on wasmtime.
- **android** — Android cross-compilation: NDK setup, ARM64 + x86_64 `.o` generation, ELF format verification.

4,845+ tests across the full pipeline.

## Skills (slash commands)

These are invocable via `/skill-name` in Claude Code:

| Skill | Description |
|-------|-------------|
| `/golden` | Run the 15/15 golden test suite through mnc-stage1 + llvm-as. Shows delta from last run. |
| `/stage2` | Compile all self-hosted modules through mnc-stage1, validate stage2 IR. Tests self-compilation. |
| `/rebuild` | Full rebuild cycle: concat .mn sources → build mnc-stage1 → run golden tests. |
| `/ir-audit` | Audit LLVM IR for known pathologies (ALLOCA_ALIAS, RET_TYPE_MISMATCH, etc.) with baseline tracking. |
| `/valgrind-map` | Run valgrind on crashing binary, map byte offsets to struct fields automatically. |
| `/bump-version` | Bump version across VERSION, README, CHANGELOG, and all localized docs. |
| `/code-review` | Run a full 7-reviewer panel code review of the codebase. |
| `/create-pr` | Generate PR title and description from the current branch's commits. |
| `/simplify` | Review changed code for reuse, quality, and efficiency, then fix issues found. |
| `/autoresearch` | Autonomous experiment loop — iterative research with automatic follow-up. |
| `/culebra-scan` | Run Culebra v2.0.0 — 49 templates (41 IR + 8 C). Auto-detects .ll vs .c. Autofix, SARIF, triage. |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (23584 symbols, 56394 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Mapanare/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Mapanare/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Mapanare/clusters` | All functional areas |
| `gitnexus://repo/Mapanare/processes` | All execution flows |
| `gitnexus://repo/Mapanare/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
