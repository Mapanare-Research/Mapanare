# v5.9.0 — DX.* — Native CLI hygiene

**Status:** SHIPPED 2026-04-27
**Closes:** DX.1, DX.2, DX.3, DX.4, DX.6, DX.7
**Defers:** DX.5 (default-command behavior change → v5.9.1; the only
breaking item, kept out of v5.9.0 to keep the release additive-only)
**Bb.3 seed refresh:** YES (mandatory — new builtin call sites
predate the v5.8.8 seed)

---

## Summary

Closes the six user-visible CLI gaps surfaced by the v5.8.7 Windows
install probe. Zero compiler internals — every change lives in
`mapanare/self/main.mn` (driver), `runtime/native/mapanare_core.c`
(C-runtime exports), `mapanare/self/{semantic,lower,emit_llvm}.mn`
(builtin allowlists + dispatch + decl block),
`mapanare/emit_llvm_text.py` (Python-side dispatch),
`scripts/build_stage1.py` (deletes the placeholder dance),
`packaging/install.{ps1,sh}` (binary-name alias), and
`.github/workflows/publish.yml` (5 new `-DMAPANARE_VERSION` flag
sites). 

After v5.9.0:

- `mnc --help` / `-h` / `help` print actual usage. Per-subcommand help
  via `mnc help <sub>` and `mnc <sub> --help`.
- `mnc version` prints `mapanare 5.9.0` instead of the literal
  `mapanare __MN_VERSION__`. The structural fix replaces the v4.28.0
  source-tree placeholder + `scripts/build_stage1.py:_substitute_version()`
  dance with a build-time-baked C-runtime export
  (`__mn_version_string()`); same shape as v5.8.6 We.1's
  `__mn_host_is_windows()`.
- `mnc cache stats` and `mnc cache clean` work on Windows. Replaced
  POSIX-only `__mn_system("if [ -d ... ]; find ... | wc -l; du -sh; ...")`
  with native runtime helpers (`__mn_dir_count_files`,
  `__mn_dir_total_size`, `__mn_dir_remove_recursive`). Pre-v5.9.0
  Windows users hit `-d was unexpected at this time` (cmd.exe's reaction
  to bash's `[ -d ... ]` test).
- Missing-clang failures print platform-specific install instructions
  (`winget install LLVM.LLVM` on Windows, `brew install llvm` on macOS,
  `apt install clang` on Linux). clang's stderr is no longer swallowed
  via `2>/dev/null`; on non-zero exit the captured stderr text is
  reprinted via `report_clang_failure()`.
- `install.ps1` and `install.sh` install `mnc.exe` / `mnc` alongside
  `mapanare` (PyInstaller doesn't read argv[0] — the alias is
  transparent). Getting-started message uses `mnc init` / `mnc run` /
  `mnc build` / `mnc --help`. Drops the `requires LLVM` parenthetical
  (DX.7 cleanup).

## Phase ledger

| Phase | Docket | Outcome |
|---|---|---|
| 1 | DX.2 | __mn_version_string export + 5 publish.yml flag sites + delete _substitute_version() + tempdir copy + Bb.3 seed |
| 2 | DX.1 | print_help_text() + print_subcommand_help() + dispatch branches; 20-test pytest suite |
| 3 | DX.4 | Native cache stats/clean via __mn_dir_count_files / __mn_dir_total_size / __mn_dir_remove_recursive; __mn_dev_null_redirect shim sweeps every 2>/dev/null literal in main.mn (10 sites) |
| 4 | DX.3 | check_clang_available() + print_clang_install_help() + report_clang_failure() at start of run_test/run_build/run_program/run_compile; clang stderr captured to __mn_clang_err_path() |
| 5 | DX.6 + DX.7 | install.ps1: `Copy-Item mapanare.exe mnc.exe`; install.sh: `ln -sf mapanare mnc`; getting-started uses `mnc` |
| 7 | — | Validation matrix |

## Validation matrix

- [x] `make lint` clean (ruff + black; black warns about py3.14 target
      vs running py3.12, benign)
- [x] `tests/test_cli_help.py`: 20/20 pass
- [x] `tests/self_hosted/test_main_mn.py`: 16/16 pass (the
      `test_version_calls_runtime_export` test replaces the v4.28.0
      `test_version_placeholder_in_source` test; same protection,
      different mechanism)
- [x] Goldens 66/66 in 14.2s — no compiler-path regressions
- [x] Lint: ruff "All checks passed!"
- [x] 3-stage fixed-point: see "Fixed-point" section below

## Fixed-point — STRICT, restored after 49 releases

**Hero metric.** Pre-v5.9.0, every release since v4.140.0 carried a
4-line VERSION-only diff between stage2.ll and stage3.ll. The
mechanism: `emit_llvm.mn`'s metadata-emission code embedded the
literal `!"__MN_VERSION__"` into the IR. stage2.ll embedded the
literal (unsubstituted in the self-hosted path); stage3.ll embedded
the actual version (because Python `build_stage1` substituted at one
tempdir-copy point but the self-hosted compiler did not).

DX.2's structural fix routes `emit_metadata_node` through
`__mn_version_string()` at runtime. Both stage2 (compiled via stage1)
and stage3 (compiled via stage2) now embed the SAME baked-in version
because both compilers share the same C-runtime constant.

**Verified strict on Linux x86_64:**

```
stage2.ll: 225831 lines / llvm-as OK
stage3.ll: 225831 lines / llvm-as OK
diff stage2.ll stage3.ll → 0 diff lines
```

First strict 3-stage fixed point since v4.139.0 (Dr.1 introduced
the placeholder); first ever where the self-hosted compiler closes
the loop end-to-end without the `__MN_VERSION__` substitution
artifact. Cobra's v4.99.0 v5-blocker stays closed; the v4.140.0+
NEAR-fixed-point regression is finally undone at the source.

## What was harder than expected

1. **Self-hosted semantic checker rejected the new builtins.** Phase 1
   tested clean on the Python-bootstrap-built stage1, then fixed-point
   immediately failed with `Undefined function '__mn_version_string'`.
   The self-hosted `semantic.mn` has an explicit allowlist of valid
   `__mn_*` builtins (line ~155-185, plus a parallel list of Symbol
   definitions at line ~2095-2140); v5.8.6 We.1 closed the same gap
   for `__mn_host_is_windows`. Pattern: every new C-runtime export
   the self-hosted compiler calls needs **three** edits — not two:
   - `runtime/native/mapanare_core.c` — the export itself.
   - `mapanare/emit_llvm_text.py` — Python-side dispatch case.
   - `mapanare/self/emit_llvm.mn::declare_runtime_fn` — IR
     declaration.
   - `mapanare/self/semantic.mn::is_builtin_function` — name allowlist.
   - `mapanare/self/semantic.mn` setup-builtins block — Symbol
     definition.
   - `mapanare/self/lower.mn::_lower_call` — return-type dispatch.
   The first three suffice for the Python bootstrap to *build* a
   stage1 that calls the new exports correctly (so `version` etc.
   work). The last three are required for the self-hosted compiler to
   *parse and lower* code that calls those exports. Either layer
   missing → caller compiles, callee fails. Documented for future
   `__mn_*` additions.

2. **The IR-metadata fix is also a fixed-point fix.** PLAN treated
   `emit_llvm.mn:6337`'s placeholder as a co-located cleanup, not a
   semantic improvement. In practice it's the structural cause of the
   v4.140.0+ near-fixed-point regression — the metadata literal was
   the entire 4-line VERSION-only diff. Documenting so the next
   reviewer doesn't think DX.2 has unrelated effects.

3. **publish.yml had FIVE clang/gcc sites that didn't pass
   `-DMAPANARE_VERSION`** despite `build_stage1.py` and `Makefile`
   wiring it since v4.31.0. The PyInstaller bundle's `libmapanare_rt.a`
   would have shipped User-Agent `Mapanare/unknown` on Windows
   pre-v5.9.0 (a latent v4.31.0 carry-forward); the native binary
   `mnc-{linux,darwin,win}.exe` would have shipped
   `__mn_version_string()` returning `unknown` on every platform if
   v5.9.0 had only added the export without sweeping publish.yml.

## Files changed

- `runtime/native/mapanare_core.c` — `__mn_version_string`,
  `__mn_dev_null_redirect`, `__mn_clang_err_path`,
  `__mn_dir_count_files`, `__mn_dir_total_size`,
  `__mn_dir_remove_recursive` (+ static recursive walkers).
- `mapanare/emit_llvm_text.py` — dispatch cases for the new exports.
- `mapanare/self/emit_llvm.mn` — `declare_runtime_fn` calls + IR
  metadata-node uses runtime call.
- `mapanare/self/semantic.mn` — allowlist + Symbol definitions.
- `mapanare/self/lower.mn` — Call-instruction return-type dispatch.
- `mapanare/self/main.mn` — `print_help_text` + `print_subcommand_help`,
  help dispatch branches, `check_clang_available` +
  `print_clang_install_help` + `report_clang_failure` +
  `clang_stderr_redirect` + `format_bytes` + `count_lines`, native
  cache rewrite, sweep of every `2>/dev/null` literal,
  `version()` rewrite, `__MN_VERSION__` placeholder deleted.
- `mapanare/self/mnc_all.mn` — regenerated.
- `scripts/build_stage1.py` — deleted `_substitute_version()` and
  `VERSION_PLACEHOLDER` constant; tempdir-copy step removed (no
  source mutation needed); `tempfile` import dropped.
- `.github/workflows/publish.yml` — `-DMAPANARE_VERSION` flag at 5
  clang/gcc sites (Windows pre-build runtime archive + Win/macOS/Linux
  primary + Linux fallback stage2 link).
- `packaging/install.ps1` — `Copy-Item mapanare.exe mnc.exe`,
  getting-started uses `mnc`.
- `packaging/install.sh` — `ln -sf mapanare mnc`, getting-started
  uses `mnc`.
- `tests/self_hosted/test_main_mn.py` —
  `test_version_calls_runtime_export` replaces
  `test_version_placeholder_in_source`.
- `tests/test_cli_help.py` — NEW. 20 tests.
- `bootstrap/seed/linux-x86_64/{mnc,mnc.sha256}` — refreshed.
- `CHANGELOG.md` — `[5.9.0]` block.
- `docs/known_issues.md` — last-updated rolled to v5.9.0.
- `docs/roadmap/ROADMAP.md` — Where We Are entry.
- `CLAUDE.md` — release-history bullet.
- `VERSION` — `5.8.8` → `5.9.0`.

## Carry-forward

- DX.5 default-command change (the only breaking item) → v5.9.1.
  Decision 2 in PLAN: defer to keep v5.9.0 additive-only.
- All other DX.* dockets closed.
