# Known Issues — User-Facing

Last updated: v5.4.2.

## Self-hosted compiler feature gaps

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Sh.4 | async code compiles through Python bootstrap only | use Python bootstrap for async programs | v5.x |
| Sh.5 | `const` in function bodies partially supported in self-hosted | use `let` in fn bodies; `const` works at module level | v5.x |
| Sh.6 | tensor literals not yet in self-hosted emitter | Python bootstrap works; self-hosted emits through boxed path | v5.x |
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
| Rt.04 | v5.4.4 landed lowerer Move emission + drop-glue `moved_locals` check via slot-source parallel arrays in both emitters (infrastructure). Attempted one-level `%struct.*` field walk + guard opening caused stage2 runtime instability (mnc-stage2 segfault before stage3 emission); walk and guard-lift were rescoped — `%struct.*` returns remain conservatively skipped. 62_list_output still LEAK 9 objs / 141 B. v5.4.5+ will re-lift the guard once the walk is gated on function size. | extract intermediate concats into let-bindings outside the struct-returning function's body | v5.4.5+ |

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
