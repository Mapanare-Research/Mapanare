# Known Issues — User-Facing

Last updated: v5.8.6 (We.1 closure — i686-w64-mingw32 ABI support. v5.8.4's Wb.2 left a latent gap: `__mn_host_is_win64()` reads `_WIN32` (defined for both Win32 and Win64), so a contributor cross-compiling to `i686-w64-mingw32` would silently get Win64 sret/sarg ABI rules applied to a target whose C ABI requires `byval(<T>) align 4` on aggregate args and a stricter `> 8 B → sret` return threshold. v5.8.6 dispatches a 3-way ABI: SysV / AAPCS64 (default), Win64 sret/sarg, or i686 cdecl sret/byval. New paired exports `__mn_host_is_windows()` + `__mn_host_arch_bits()` replace the misleading-named v5.8.4 single export (kept as deprecated alias). EmitState `is_win64: Bool` → `is_windows: Bool` + `win_arch: Int`. Pre-existing v5.8.4 datalayout-not-target-aware bug fixed in passing. Bb.2 seed refresh shipped (mandatory; the v5.8.5 seed knows only `__mn_host_is_win64`). Goldens 66/66 preserved; fixed-point NEAR; pytest 2,372 passed.).

## Self-hosted compiler feature gaps

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Sh.5 | `const` in function bodies partially supported in self-hosted | use `let` in fn bodies; `const` works at module level | v5.x |
| Sh.9a | async emitter bug: see `docs/guides/async.md` for workaround | documented workaround in async guide | v5.x |
| Sh.9b | async emitter bug #2: see `docs/guides/async.md` | documented workaround in async guide | v5.x |
| ~~Wb.2~~ | ~~Self-hosted emit_llvm.mn hardcodes SysV ABI at line 2243~~ | — | **CLOSED v5.8.4** (port complete; aggregate-returning runtime fns emit Win64 sret on Windows; aggregate args use the sarg ptr pattern; Windows fixed-point holds within the same Dr.1 tolerance as Linux) |
| ~~We.1~~ | ~~v5.8.4 `__mn_host_is_win64()` reads `_WIN32` (defined for both Win32 and Win64), so cross-compiling to `i686-w64-mingw32` silently triggers Win64 sret/sarg ABI rules — wrong for i686 cdecl which needs `byval(<T>) align 4` on aggregate args and a stricter `> 8 B → sret` return threshold.~~ | Use `x86_64-w64-mingw32` (the only Windows target Mapanare actually shipped through v5.8.5) | **CLOSED v5.8.6** (3-way ABI dispatch SysV / Win64 / i686; new paired exports `__mn_host_is_windows()` + `__mn_host_arch_bits()`; EmitState `is_win64` → `is_windows + win_arch`; Bb.2 seed refresh) |

> **v5.4.0 → v5.7.0 closures** (moved out of the active table; full
> traces in their per-release SESSION_REPORTs):
>
> - **Sh.4** (async self-hosted) — CLOSED v5.5.4–v5.5.7 across the
>   coroutine arc. Self-hosted emitter ships full LLVM-coroutine
>   lowering; all 5 Sh.4 goldens valgrind / ASan / LSan / TSan clean.
> - **Sh.6** (tensor self-hosted) — CLOSED v5.6.0–v5.6.3.
>   Literals (v5.6.0), multi-dim indexing (v5.6.1), broadcast (v5.6.2),
>   slicing + reductions (v5.6.3). 5 tensor goldens 49/50/51/52/53
>   pass through `mnc-stage1`.
> - **Sh.7** (closure-typed parameters) — CLOSED v5.7.0. Four
>   self-hosted changes: `parser.mn` extracts multi-param lambdas,
>   `lower.mn` routes calls through fn-typed locals via indirect-call
>   SSA name, `emit_llvm_ir.mn::emit_call_ir` recognises `%`-prefixed
>   callees, `mir_opt.mn` renames Call's fn_name during inlining.
> - **B** (or-pattern + identifier `None`) — CLOSED v5.7.0.
>   `_is_enum_variant_name` short-circuits to True for built-in
>   `None`/`Some`/`Ok`/`Err`; `Identifier("None")` resolves to `Option`
>   in both `_infer_expr` and `_lower_identifier`.

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
| Rt.04 | Multi-level alias analysis for drop-glue. v5.6.6 attempted a one-level `%struct.*` field walk and reproduced a UAF in `62_list_output` — the resource lives at struct→list→string (depth 2). Fix needs the v6.0 borrow checker. 62_list_output stays LEAK (baseline-gated, 13 obj / 346 B refreshed v5.6.12). | extract intermediate concats into let-bindings outside the struct-returning function's body | v6.0 (borrow checker) |

> **Closed since v5.4.0** (full traces in per-release
> SESSION_REPORTs): Rt.03 (loop-reassignment leak, v5.4.3),
> Rt.05 (AwaitSuspend inner-coroutine leak, v5.5.7),
> Rt.06 (tensor drop-glue, v5.6.4), Ve.1 (parse_fn_body
> overflow, v5.6.5), Ve.2 (empty-list elem_ty floor, v5.6.7
> partial → v5.6.12 closed), Ve.3 (drop-glue UAF on
> List<Enum> returns, v5.6.9), Ve.4 (match-arm empty
> BasicBlocks via elem_size mismatch, v5.6.11), Lk.1
> (alloca-aliasing leak via destination-passing semantics,
> v5.6.12).

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

Last verified: v5.7.1 (2026-04-26).
