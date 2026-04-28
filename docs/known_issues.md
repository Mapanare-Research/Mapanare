# Known Issues — User-Facing

Last updated: v5.11.0 (Pk.* — packaging hygiene + post-bundle cleanup. Three deferred-from-v5.10.0 cleanups, zero compiler internals. **Pk.1**: release-artifact filenames now include the version (`mapanare-5.11.0-win-x64.zip`, `mnc-5.11.0-linux-x64`, etc.), driven by the VERSION file. install.ps1 / install.sh probe the versioned name first and fall back to the legacy unversioned alias for releases <= v5.10.0 and through a 2-release soak window (drop the fallback in v5.13.0). The legacy unversioned URL keeps resolving so blog-post install scripts that hardcoded it stay green. windows-bundled-llvm-smoke job downloads the versioned ZIP so a missing-versioned-asset failure trips the smoke gate. **Pk.2**: drops the v5.9.1 `mnc <file.mn>` (implicit-run) deprecation stderr line; v5.10.0 carried it as the soak-window concession per the v5.9.1 PLAN's stated cadence. `tests/test_cli_default.py::test_default_prints_deprecation_note` inverted to `test_default_silent_after_v5_11_0`. **Pk.3** (evaluate-only): native `mnc` is missing 18 of `mapanare`'s 25 subcommands (`lsp`, `fmt`, `init`, `check`, `lint`, `emit-c/wasm/mir`, `transpile`, `bind`, `doc`, registry commands). PyInstaller→native bundle swap deferred to v5.12.x+ behind Mc.* (mnc parity). See `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md`. **Pk.4** (closeout-doc): macOS/Linux LLVM bundling stays deferred — system clang remains canonical (xcode-select / apt clang); a static Linux LLVM bundle with libstdc++ is ~300 MB; no demand signal emerged. Re-open if it does. NO seed refresh required (zero new C-runtime exports — first release in 5+ to skip Bb.*). Strict 3-stage fixed-point preserved (the v5.9.0 milestone). Goldens 66/66; `make lint` clean. See `docs/roadmap/v5/v5.11.0/SESSION_REPORT.md`.).

Earlier last-updated: v5.10.0 (Win.1b — bundled LLVM toolchain in the Windows release ZIP. Closes the "missing clang" pain on Windows surfaced by the v5.8.7 install probe; v5.9.0 DX.3 made the failure mode helpful (install hint instead of bare "clang failed"); v5.10.0 removes the dependency entirely. Default `mapanare-win-x64.zip` grows from ~10 MB to ~95 MB by bundling LLVM 18.1.8's minimal redistributable subset (clang.exe + lld-link.exe + LLVM-C.dll + compiler-rt + LICENSE.TXT) into `mapanare/llvm/`. New `__mn_executable_dir()` C-runtime export + `find_clang()` helper in `mapanare/self/main.mn`. Bb.4 seed refresh required for the new export. install.ps1 honors `MAPANARE_NO_BUNDLED_LLVM=1` for opt-out users → `mapanare-win-x64-minimal.zip` (~10 MB). `windows-bundled-llvm-smoke` CI job validates the published ZIP end-to-end with PATH stripped. Linux/macOS artifacts unchanged (PLAN Decision 4 — system clang is canonical there). See `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md`.).

Earlier last-updated: v5.9.2 (hygiene — pre-existing test regex + stale README line. Two fixes carried over from v5.9.1 that didn't fit DX.5's dispatch scope. **Tg.1**: `tests/bootstrap/test_stage1_compile.py`'s quoted-declare regex used `[^"]+` which matches across newlines, producing the latent failure shape `Unresolved cross-module refs: [', align 8\n@.str.NNNN = ...']` (reproduced on v5.9.0 HEAD with index 3025; v5.9.1 HEAD with 3042 — string-table drift confirms the bug tracks compiler output, not the regex). Helper `_extract_quoted_declares` extracted, regex anchored to start-of-line via `re.MULTILINE` and tightened to `[^"\n]+`. New `TestRegexHelper` with 3 cases guards the failure shape. **Dn.1**: `README.md:135` self-host fixed-point line — stale `NEAR (4-line VERSION-metadata diff over a 217k-line stage2.ll)` was the v5.6.x state; v5.9.0 restored STRICT at the source (DX.2's `__mn_version_string()` C-runtime export); v5.9.1 preserved it. README now reads STRICT with v5.9.0 credit. Test + docs only — zero compiler/runtime/dispatch edits. NO seed refresh. Strict 3-stage fixed-point preserved (the v5.9.0 milestone). Goldens 66/66; `test_stage1_compile.py` 20/20 pass (was 19/20 at v5.9.1 HEAD; 3 new `TestRegexHelper` cases ship here); `make lint` clean. See `docs/roadmap/v5/v5.9.2/SESSION_REPORT.md`.).

Earlier last-updated: v5.9.1 (DX.5 closure — `mnc <file.mn>` now runs the program. Pre-v5.9.1 the default was LLVM IR emission to stdout — useful for compiler developers but a hostile first impression for newcomers. The IR-emission path moves to `mnc emit-llvm <file.mn>` (parallel to the Python CLI's `mapanare emit-llvm`); `-o <path>` writes to a file. Non-`.mn` files now error with a migration hint pointing at `mnc emit-llvm` (raw IR) or `mnc compile` (transpilation). One-line stderr deprecation note prints on the implicit-run path for v5.9.1–v5.10.0; removed in v5.11.0. Dispatch-layer only — zero changes to parser/semantic/MIR/lower/optimizer/emitters; same scope discipline as v5.9.0. NO seed refresh required (no new builtin call sites). Strict 3-stage fixed-point preserved (the v5.9.0 milestone). Goldens 66/66 byte-identical; `tests/test_cli_default.py` 6/6 pass; `make lint` clean. **Empties the v5.8.7 Windows install probe DX.* dockets — DX.1–DX.7 all closed.** See `docs/roadmap/v5/v5.9.1/SESSION_REPORT.md`.).

Earlier last-updated: v5.9.0 (DX.* closure — native CLI hygiene. Closes the six user-visible CLI gaps surfaced by the v5.8.7 Windows install probe: `mnc --help` works (DX.1); `mnc version` no longer leaks `__MN_VERSION__` (DX.2 — structural fix via new `__mn_version_string()` C-runtime export, replaces v4.28.0 source-tree placeholder + build_stage1.py substitution dance, eliminates the staleness class that produced the v5.8.7 Windows publish bug); `mnc run` (no clang) prints platform-specific install instructions (DX.3 — `winget install LLVM.LLVM` / `brew install llvm` / `apt install clang`, with clang stderr no longer swallowed); `mnc cache stats` / `cache clean` work on Windows (DX.4 — replaces POSIX-only `[ -d ... ]; find | wc -l; du -sh; rm -rf` shell-out with native runtime exports `__mn_dir_count_files` / `__mn_dir_total_size` / `__mn_dir_remove_recursive`); `install.ps1` / `install.sh` ship `mnc` alongside `mapanare` and the getting-started message uses `mnc` consistently (DX.6 + DX.7). Bb.3 seed refresh shipped. Goldens 66/66 preserved; zero compiler internals touched. DX.5 (default-command change) deferred to v5.9.1 per Decision 2 — the only breaking item. See `docs/roadmap/v5/v5.9.0/SESSION_REPORT.md`.).

Earlier last-updated: v5.8.8 (Da.1 closure — Apple AArch64 (AAPCS64) sret return ABI. Closes the latent bug surfaced in v5.8.7's `macos-13 → macos-latest` runner switch: Mapanare's IR declared 40-byte aggregate returns (`__mn_list_new`, `__mn_str_split`) as first-class aggregates `{ptr, i64, i64, i64, i64} @fn(...)`, which LLVM's x86_64 backend silently rewrites to sret-style memory return per AMD64 §3.2.3 memory class — but LLVM's arm64 backend lowers literally as register-tuple return (x0..x4), while the C runtime returns via x8 indirect (canonical AAPCS64). Mismatch → caller reads x0..x4 as garbage → `FATAL: __mn_list_push received corrupted list (data=0x40 ...)` SIGABRT. Both emitters (`emit_llvm_text.py` + `emit_llvm.mn`) now emit canonical sret form on all SysV / AAPCS64 default-path targets. Da.2 macOS self-compile CI gate added; Da.3 publish.yml macOS arm64 binary re-enabled; release-notes Apple Silicon row points to Download link again. `build_stage1.py` post-emit triple/datalayout text-patch deleted (natural plumbing already present). NO seed refresh required (target-agnostic dispatch avoids new builtin call site). Mac strict-NEAR fixed-point: stage2.ll == stage3.ll within 4 lines (VERSION-only). Goldens 66/66 preserved; non-bootstrap pytest 1,349 passed. See `docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md` and `docs/roadmap/v5/v5.8.8/SESSION_REPORT.md`.).

Earlier last-updated: v5.8.6 (We.1 closure — i686-w64-mingw32 ABI support. v5.8.4's Wb.2 left a latent gap: `__mn_host_is_win64()` reads `_WIN32` (defined for both Win32 and Win64), so a contributor cross-compiling to `i686-w64-mingw32` would silently get Win64 sret/sarg ABI rules applied to a target whose C ABI requires `byval(<T>) align 4` on aggregate args and a stricter `> 8 B → sret` return threshold. v5.8.6 dispatches a 3-way ABI: SysV / AAPCS64 (default), Win64 sret/sarg, or i686 cdecl sret/byval. New paired exports `__mn_host_is_windows()` + `__mn_host_arch_bits()` replace the misleading-named v5.8.4 single export (kept as deprecated alias). EmitState `is_win64: Bool` → `is_windows: Bool` + `win_arch: Int`. Pre-existing v5.8.4 datalayout-not-target-aware bug fixed in passing. Bb.2 seed refresh shipped (mandatory; the v5.8.5 seed knows only `__mn_host_is_win64`). Goldens 66/66 preserved; fixed-point NEAR; pytest 2,372 passed.).

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

## Packaging

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Pk.4 | macOS / Linux release tarballs do not bundle an LLVM toolchain (mirroring the v5.10.0 Windows bundled-LLVM ZIP). | Install system clang via `xcode-select --install` (macOS) or `apt install clang` / package-manager equivalent (Linux). | **Closed by anticipation v5.11.0** — re-open only if a demand signal emerges. Reasons: system clang is canonical on both platforms; bundling clang on Linux requires static libstdc++/libc which pushes the tarball past ~300 MB (vs Windows' 95 MB); no demand signal collected from v5.10.0. Closeout trail: `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md` (PLAN Decision 4) + `docs/roadmap/v5/v5.11.0/SESSION_REPORT.md`. |
| Pk.5 | Native `mnc` covers 7 of `mapanare`'s 25 subcommands. Missing: `lsp`, `fmt`, `init`, `check`, `lint`, `emit-c/wasm/mir`, `transpile`, `bind`, `doc`, registry commands (`install`, `publish`, `search`, `login`), `deploy`, `migrate`, `targets`, `build-multi`. | Use the PyInstaller-bundled `mapanare` CLI for any subcommand `mnc` doesn't have. The bundled Windows ZIP ships both binaries. | v5.12.x+ — Mc.* (mnc parity) docket opens with Mc.1 `mnc lsp`, Mc.2 `mnc fmt`, Mc.3 `mnc init`, Mc.4 `mnc check`, Mc.5 `mnc emit-wasm`. PyInstaller→native bundle swap gated on Mc.1–Mc.5. See `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md`. |

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
