# Known Issues — User-Facing

Last updated: v5.6.9 (Ve.3 root cause CLOSED; new Ve.4 opened — match-arm verifier error in self-hosted compiled lowerer).

## Self-hosted compiler feature gaps

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Sh.4 | async code compiles through Python bootstrap only | use Python bootstrap for async programs | v5.x |
| Sh.5 | `const` in function bodies partially supported in self-hosted | use `let` in fn bodies; `const` works at module level | v5.x |
| ~~Sh.6~~ | ~~tensor literals not yet in self-hosted emitter~~ **CLOSED v5.6.3** — tensor literals (v5.6.0), multi-dim indexing (v5.6.1), broadcast binops (v5.6.2), slicing + reductions (v5.6.3). All 5 tensor goldens 49/50/51/52/53 run byte-identical to expected output through `mnc-stage1 → llc → clang`. | n/a | CLOSED v5.6.3 |
| Sh.7 | closure-typed function parameters: self-hosted declines | use concrete fn types | v5.x |
| Sh.9a | async emitter bug: see `docs/guides/async.md` for workaround | documented workaround in async guide | v5.x |
| Sh.9b | async emitter bug #2: see `docs/guides/async.md` | documented workaround in async guide | v5.x |

## Grammar / language

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Gr.1 | multi-line list/tensor literals parse-error | put literal on one line; wrap in parens on next | v5.x |

## Runtime

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Rt.2 | `dir_create(recursive=true)` ignores the flag | call `dir_create` per path level | v5.x |
| Rt.3 | `tmpfile_path` returns literal `/tmp/mn_tmp_XXXXXX` without calling `mkstemp` | use `io_tmpfile()` which returns a real handle | v5.x |
| Rt.01 | `gpu_available()` on a CUDA-capable host leaks 260 B of libcuda driver state per process (one-shot init, reclaimed by kernel at exit) | no action required — suppressed in `scripts/asan_leak_suppressions.txt` | n/a (third-party) |
| Rt.02 | Vulkan / Mesa ICD loader retains ~50 KB of per-process state after `vkDestroyInstance`; `vkDestroyInstance` does not release it | no action required — baseline-gated in `scripts/check_leak_summary.py` (frames show as `<unknown module>`, not symbolic-suppressable) | n/a (third-party) |
| Rt.03 | **CLOSED v5.4.3** — free-before-store in `emit_track_string` / `_boxed` / `_closure` when `loop_depth > 0` (both emitters). 22_string_builder transitions LEAK → CLEAN under LSan; baseline refreshed. | n/a | CLOSED v5.4.3 |
| Rt.04 | **v5.6.6 ATTEMPTED + RESCOPED.** v5.4.4 left infrastructure for a one-level `%struct.*` field walk gated on struct-size and slot-count thresholds. v5.6.6 attempted the re-lift at three threshold settings (N=8/M=50 → 10% stage2.ll growth; N=4/M=20 → 3.67%; N=4/M=10 → 2.39% under PLAN budget). All three reproduced a confirmed heap-use-after-free in `62_list_output` under ASan: drop glue extracts the returned struct's `List<String>` field as a list-alias, but the **individual Strings inside the list** are tracked separately and freed prematurely → caller's `__mn_str_join` reads freed memory. The leak (9 objs / 141 B) and the UAF are mutually exclusive at this walk depth — the resource lives at struct→list→string (depth 2), not depth 1. Closing Rt.04 requires multi-level alias extraction or a borrow checker. v5.6.6 ships only the `ret_ty_is_aggregate` signature change `(ret_ty) → (st, ret_ty)` to plumb state through for the future fix; gate body reverts to v5.4.4's conservative skip. 62_list_output stays LEAK (baseline-gated). See `docs/roadmap/v5/v5.6.6/SESSION_REPORT.md`. | extract intermediate concats into let-bindings outside the struct-returning function's body | v6.0 (borrow checker) |
| Rt.05 | **CLOSED v5.5.7** — AwaitSuspend inner-coroutine leak. v5.5.5 emitted no `coro.destroy` + `free` in `aw.ready.N` because `%aw.hdl.N` was loaded only on the `aw.drive.N` edge and did not dominate fast-path / scheduler-resume entries; this leaked 56 B per inner await across 56/57/58/59 (~10 leaks in 59_async_fanout). v5.5.7 hoists the `getelementptr + load ptr` of the inner handle into the entry BB before the fast-path branch, so `%aw.hdl.N` dominates all three entries to `aw.ready.N`. Cleanup mirrors v5.5.6's BlockOn (`coro.destroy + free(box) + free(future)`). All 5 Sh.4 goldens now valgrind-clean (e.g., 59 = 36 allocs / 36 frees / 0 lost), ASan-clean, LSan-clean, TSan-clean. | n/a | CLOSED v5.5.7 |
| ~~Ve.1~~ | **Primary overflow CLOSED v5.6.5.** Root-caused NOT in `parse_fn_body` itself but in `llvm_type_size()`: a hardcoded `256`-byte fallback for any `%struct.*` type (a "safe upper bound" that was false for `FnDefData = 264 bytes`). Every `Definition::FnDef(fd)` boxing `malloc(256)` + `store %struct.FnDefData` overflowed the heap block by 8 bytes. v5.6.5 rewrites the sizing pipeline to defer ABI computation to LLVM via the GEP-trick (`ptrtoint ptr getelementptr (%T, ptr null, i32 1) to i64`) and typed field GEPs — the same pattern Clang uses for opaque-size emission. 435 hardcoded `malloc` sites → 2; ASan confirms 0 heap-buffer-overflow errors on both `lower.mn` and `mnc_all.mn`. **Fixed-point not yet restored** — see Ve.2 for the residual blocker (lowerer elem_ty propagation). See `docs/roadmap/v5/v5.6.5/SESSION_REPORT.md`. | n/a | CLOSED v5.6.5 |
| Ve.2 | **PARTIALLY CLOSED v5.6.7** — `lower_list_typed(st, elements, hint)` helper added; `lower_let` now threads the `let xs: List<T> = []` type annotation as an element hint, eliminating 95% of 384-byte fallback allocations (387 → 18 sites). Also fixed a misfiring heuristic in `emit_list_init_checked` that dropped correctly-typed `List<Struct>` literals. 18 residual 384-byte sites remain — empty lists in contexts that don't route through `lower_let` (struct field defaults, call arguments, return expressions); scoped for v5.6.9+. Does NOT fix the stage2 runtime OOM — see Ve.3. | n/a for the closed class; use `mnc-stage1` for self-host | PARTIAL v5.6.7, residuals v5.6.9+ |
| Ve.3 | **CLOSED v5.6.9** — drop-glue UAF on `List<Enum>` returns. Root cause: `emit_drop_glue` for a list-return function (`{ptr, i64, i64, i64, i64}`) iterates `boxed_owned` and unconditionally frees every tracked heap-boxed payload via `@free(ptr)`. The list elements are `%enum.Instruction = type {i64, ptr}` — Instructions stored as `{tag, payload_ptr}` pairs where the payload_ptr IS one of the freed boxes. The single-level alias check in `drop_glue_boxed` compares against `ret_box_ptrs` (empty for list returns) — the inner refs through list elements are invisible. Caller's `instr_dest(inst)` reads the enum's `{tag, payload_ptr}` and dereferences the dangling payload to extract the Value's `name: String` field, getting uninitialised memory. The "third Alloca" from v5.6.8's investigation was the first inliner-cloned Alloca (`%_inl0_2_a.addr`) — direct lowerer Allocas (`%a.addr` / `%b.addr` from `bind_fn_params`) returned via LowerState (struct, conservatively skipped) survive; inliner-cloned ones returned via `clone_instr_for_inline` (List<Instruction>) had their boxed payloads freed. Same multi-level aliasing class as v5.6.6 Rt.04 (List<String> in returned struct, 2 levels deep); v5.6.9 fix is the matching RESCOPE: skip drops conservatively when `ret_ty == llvm_list_rt() && len(boxed_owned) > 0`. Cost: intermediate boxes NOT in returned list leak (accepted per v5.6.6 RESCOPE — UAF prevention > leak prevention). 25 LOC in `emit_llvm.mn:4763`. Closes the v5.6.4-era OOM/SIGSEGV symptom; goldens 64/66 preserved; ASan/valgrind/LSan baselines unchanged. See `docs/roadmap/v5/v5.6.9/SESSION_REPORT.md`. | n/a — fix shipped | CLOSED v5.6.9 |
| Ve.4 | **OPENED v5.6.9** — match-arm lowering produces empty BasicBlocks in self-hosted compiled lowerer. With Ve.3 closed, `mnc-stage2 mnc_all.mn` (and any program with non-trivial match expressions, e.g. a 2-arm enum match in a small `apply` test program) hits the MIR verifier error `<fn>::match_arm<N>: block has no instructions` before stage3 emission can begin. Reproduces on the **original v5.6.8 mnc-stage2 binary** with the same error pattern — confirming this bug existed in v5.6.8 but was masked by Ve.3's earlier OOM. Default 8 MB stack causes a SIGSEGV at a stack address (0x7ffc...range) before the verifier fires; `ulimit -s unlimited` lets the verifier surface the actual cause. Python-built stage1 lowers correctly (goldens 64/66 pass through stage1+lli), so the bug is in how stage1 compiled the self-hosted lowerer's match-arm-handling code into stage2.ll — source code is correct, but the compiled binary's match-arm lowering loses some instruction emissions. Hypothesis: a pass after lowering (likely `dead_block_elim_function` or interaction with `inline_small_functions`) drops instructions from match arms whose body is a single tail expression. Note: broadening the v5.6.9 Ve.3 fix to also include `len(str_owned) > 0` reproduces the same error on programs as small as a 2-arm match — Ve.4 is independent of the fix's breadth. | use `mnc-stage1` for self-host work; `verify_fixed_point.sh` still fails at Stage 2 | v5.6.10 |
| Rt.06 | **CLOSED v5.6.4** — tensor drop-glue ported. Self-hosted emitter gains `EmitState.tensor_owned` + `tensor_owned_source` lists, `emit_track_tensor` helper (with v5.4.3 loop-depth free-before-store parity), and `emit_drop_glue_tensors` helper wired into `emit_drop_glue` at return edges. 22 tensor-allocating runtime fns tracked via `is_tensor_allocating_fn` predicate (1 alloc + 1 slice + 20 binop fns). Full LSan sweep across all 5 tensor goldens reports 0 objs / 0 B; baseline TSV flipped from LEAK-allowed to CLEAN-required so future tensor-allocation patterns that skip tracking now fail CI. | n/a | CLOSED v5.6.4 |

## Ecosystem

**Package registry (v5.2.0+):** `mapanare install <pkg>@<ver>` and
`mapanare publish` are available. Team-only publishing for MVP;
open publishing tracked for v5.3+. See `docs/guides/packages.md`.

## Python transpiler (`mapanare build file.py`)

The transpiler handles pure-compute Python (functions, loops, conditionals, arithmetic). Known limitations:

| Feature | Status | Workaround |
|---|---|---|
| `import` statements | Not supported | Write self-contained scripts |
| Classes with inheritance | Struct only, no inheritance | Flatten to functions |
| `try`/`except` | Commented out | Use Result types in .mn |
| `*args`, `**kwargs` | Not supported | Use explicit parameters |
| List comprehensions | Not supported | Rewrite as `for` loop + `.append()` |
| Generators / `yield` | Not supported | Use explicit loops |
| `with` statements | Not supported | — |
| C extensions (numpy, pandas) | Not supported | Use Dato (v5.x) |
| Float formatting | May differ in last digits | Use integer outputs for exact match |

**Best results with:** type-annotated functions, simple data types (int, float, bool, str), `for`/`while` loops, arithmetic.

Last verified: v5.3.1 (2026-04-22).
