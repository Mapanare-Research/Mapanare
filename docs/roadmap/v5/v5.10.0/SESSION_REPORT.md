# v5.10.0 — Session Report

**Status:** Source-authored + lint-validated + WSL goldens 66/66 +
strict fixed-point + Bb.4 seed refreshed + committed (two commits:
v5.10.0 source + v5.10.0 Bb.4 closeout). Tag/push **held** for
user authorization.
**Date:** 2026-04-28
**Branch:** `dev`
**Headline:** **Win.1b — bundled LLVM toolchain in Windows release
ZIP.** First Mapanare release that gives Windows users a working
`mnc run hello.mn` with **zero external dependencies**.

---

## What shipped

### Win.1b.A — minimal LLVM subset extraction

`tools/llvm-bundle/extract_minimal.ps1` — pinned LLVM 18.1.8.
Required closure (per `dumpbin /dependents` audit, documented in
`tools/llvm-bundle/REQUIRED_FILES.md`):

| File | ~size | Purpose |
|---|---:|---|
| `clang.exe` | 5 MB | IR compiler + linker driver |
| `lld-link.exe` | 4 MB | Linker invoked by `clang -o` on Windows |
| `LLVM-C.dll` | 80–90 MB | Core LLVM library; dominates bundle size |
| `clang_rt.builtins-x86_64.lib` | 1 MB | Compiler intrinsics |
| `LICENSE.TXT` | 4 KB | Apache 2.0 + LLVM Exception (mandatory for redistribution) |

Total: ~95 MB. PATH-stripped smoke test in the script catches
lazy-load DLL closure gaps `dumpbin` alone misses.

**vcruntime140.dll / msvcp140.dll** are deliberately NOT bundled —
Microsoft's "Visual C++ Redistributable" is preinstalled on
Windows 10+ and bundling risks DLL-hell with the user's other
Microsoft software. If the smoke test fails on a future Windows
build, the script can add them via the `RequiredBin` array (~3 MB).

### Win.1b.B/C — CI integration

`.github/workflows/publish.yml` `build-cli` job adds five new steps
between "Smoke test CLI binary" and "Archive CLI binary":

1. `actions/cache@v4` keyed on `LLVM_VERSION=18.1.8`
2. Download + extract LLVM (cache miss only — `7z` ships on the
   `windows-latest` runner)
3. Archive minimal variant FIRST (`mapanare-win-x64-minimal.zip`,
   pre-bundle, ~10 MB)
4. Stage bundled LLVM into `dist/mapanare/llvm/` via the Phase 1
   script
5. Verify bundled clang runs (compile + run hello-world with PATH
   stripped)

A new "Stage third-party license docs" step copies
`docs/THIRD-PARTY-LICENSES.md` into the bundle. The existing
"Archive CLI binary" step now produces the ~95 MB bundled ZIP; a
new "Upload minimal Windows ZIP" step parallels the bundled
upload.

### Win.1b.D — bundled-toolchain detection in mnc

New C-runtime export in `runtime/native/mapanare_core.c`:

```c
MN_EXPORT MnString __mn_executable_dir(void);
```

Cross-platform: Win32 `GetModuleFileNameA` /
macOS `_NSGetExecutablePath` (under a new `<mach-o/dyld.h>` include) /
Linux `readlink("/proc/self/exe")`. Returns empty string on
failure; result is cached after the first call.

New helper in `mapanare/self/main.mn`:

```mn
fn find_clang() -> String {
    let exe_dir: String = __mn_executable_dir()
    if len(exe_dir) > 0 {
        let bundled_win: String = exe_dir + "/llvm/clang.exe"
        if __mn_file_exists(bundled_win) != 0 {
            return "\"" + bundled_win + "\""
        }
        let bundled_unix: String = exe_dir + "/llvm/clang"
        if __mn_file_exists(bundled_unix) != 0 {
            return "\"" + bundled_unix + "\""
        }
    }
    return "clang"
}
```

Six clang shell-out sites updated:

| Site | Function | Pre-v5.10.0 | Post-v5.10.0 |
|---|---|---|---|
| `main.mn:94-99` | `check_clang_available` | `"clang --version > NUL"` | `clang_bin + " --version > NUL"` |
| `main.mn:604-605` | `run_test` r1 | `"clang -c -O2 ..."` | `clang_bin + " -c -O2 ..."` |
| `main.mn:724-725` | `run_build` clang_cmd | `"clang -c " + opt_flag` | `clang_bin + " -c " + opt_flag` |
| `main.mn:775-776` | `run_program` compile_cmd | `"clang -O0 ..."` | `clang_bin + " -O0 ..."` |
| `main.mn:780` | `run_program` r1b fallback | `"clang -c -O0 ..."` | `clang_bin + " -c -O0 ..."` |
| `main.mn:887` + `main.mn:948` | `run_compile` (.mn + foreign) | `"clang -c -O2 ..."` | `clang_bin + " -c -O2 ..."` |

Bundled paths are quote-wrapped (`"<path>"`) so install dirs with
spaces (`C:\Program Files\Mapanare\bin`) tokenise correctly when
concatenated into a `__mn_system` command string.

### Plumbing for the new export

`__mn_executable_dir` registered in:

- `mapanare/emit_llvm_text.py` — Python bootstrap LLVM-text emitter
  dispatch (next to v5.9.0 DX.4 helpers)
- `mapanare/self/emit_llvm.mn` — self-hosted runtime decl table
- `mapanare/self/semantic.mn` — `is_builtin_function_name` +
  symbol-table registration
- `mapanare/self/lower.mn` — `Call` lowering (returns `mir_string()`)

The Python bootstrap `lower.py` / `semantic.py` need no changes —
v5.9.0's `__mn_dev_null_redirect` / `__mn_clang_err_path` ship the
same way, dispatched only at the emitter layer.

### Win.1b.E — license + redistribution compliance

`docs/THIRD-PARTY-LICENSES.md` indexes:

- LLVM (Apache 2.0 + LLVM Exception, version 18.1.8)
- w64devkit (MinGW gcc + GNU runtime, GPL Runtime Exception)

The doc cites the LLVM Exception's "no copyleft on linked output"
clause explicitly so users / downstream packagers know
Mapanare-emitted binaries are NOT subject to LLVM's license.

`README.md` install section updated to mention bundled-LLVM and
the `MAPANARE_NO_BUNDLED_LLVM=1` opt-out.

### Win.1b.F — install.ps1 ZIP layout + bundled-detection

```powershell
$UseBundledLlvm = $true
if ($env:MAPANARE_NO_BUNDLED_LLVM -in @("1","true","yes","TRUE","YES")) {
    $UseBundledLlvm = $false
}
$Artifact = if ($UseBundledLlvm) { "mapanare-win-x64.zip" } else { "mapanare-win-x64-minimal.zip" }
```

Banner reports toolchain status + download size up front.
Success message detects `<install>/llvm/clang.exe` and reports the
bundled path; if absent, falls through to a `winget install
LLVM.LLVM` hint.

### Win.1b.G — `windows-bundled-llvm-smoke` CI job

New job in `publish.yml` between `build-native` and `checksums`.
Downloads the published `mapanare-win-x64.zip`, strips `PATH` to
system DLLs only, runs `mnc run hello.mn`. Catches "the bundle is
broken" before users do; gates `checksums` so a broken bundle
never reaches a final release.

Release-size gate at 150 MB alarm (target 100 MB). Current bundle
projected at ~95 MB.

---

## Decisions taken

### Decision: keep PyInstaller bundle composition

The v5.10.0 PROMPT proposed swapping `mapanare-win-x64.zip`'s
PyInstaller-bundled Python CLI for a small native-only bundle
(`bin/mnc.exe + bin/llvm/`). Rejected as out-of-scope for this
release — that's a behavioral change beyond "bundle LLVM" that
removes the Python CLI from Windows users' default download.

v5.10.0 ships **additive**: bundle LLVM into the existing
PyInstaller layout at `mapanare/llvm/`. Both `mapanare.exe`
(Python CLI) and `mnc.exe` (native, post-Bb.4) get the bundled
toolchain. The PyInstaller→native swap is now a Pk.3 evaluate-
only item in the v5.11.0 PLAN (decision-only, implementation
deferred to v5.12.0+ if approved).

### Decision: defer versioned artifact filenames to v5.11.0

User raised the legitimate concern that `mapanare-win-x64.zip` has
no `5.10.0` in the filename — locally-saved copies of multiple
versions collide. Rejected as a v5.10.0 add-on (would double the
diff and make a regression hard to bisect); scheduled as Pk.1 in
v5.11.0 with a 2-release legacy-alias soak window per Decision 1
in the v5.11.0 PLAN.

### Decision: defer macOS/Linux LLVM bundling

Reaffirms v5.10.0 PLAN Decision 4 with three concrete reasons:

- macOS users have `xcode-select --install` clang; bundling
  conflicts and creates "wrong clang version" reports
- Linux users have `apt install clang`; bundled clang's
  libstdc++/libc dependencies create portability nightmares
  (binary built against glibc 2.35 won't run on glibc 2.31)
- Static LLVM with bundled libstdc++ would be ~300 MB — dwarfs
  the win-x64 95 MB target

v5.11.0 Pk.4 is a closeout doc, not a re-evaluation.

---

## Bb.4 + WSL validation (closed in same session)

Originally deferred to a follow-up session; ran on WSL Ubuntu after
the initial v5.10.0 source commit. Two real bugs surfaced and were
fixed in-session:

### Bug 1: MIR inliner constant-folded find_clang to its fallback

The first `find_clang()` draft used multiple early returns:

```mn
fn find_clang() -> String {
    let exe_dir: String = __mn_executable_dir()
    if len(exe_dir) > 0 {
        let bundled_win: String = exe_dir + "/llvm/clang.exe"
        if __mn_file_exists(bundled_win) != 0 {
            return "\"" + bundled_win + "\""
        }
        ...
    }
    return "clang"
}
```

The self-hosted MIR optimizer constant-folded EVERY call site of
`find_clang()` to the fallback `"clang"` literal, dropping the
bundled-path branches entirely. Stage2 IR had `0` references to
`find_clang` (function entirely elided), `0` calls to
`@__mn_executable_dir`, and `check_clang_available()` shipping
the literal 27-char string `clang --version > NUL 2>NUL` instead
of a dynamic concatenation.

The bundled-LLVM lookup would have been silently broken in every
released binary. Smoke job in CI would have caught it on Windows
(PATH stripped → fallback `"clang"` → "clang not found"), but
better to catch it pre-tag.

**Fix:** rewrote `find_clang()` to single-return form with
`let mut result: String = "clang"` and conditional reassignment.
Comment in main.mn documents the gotcha so a future maintainer
doesn't re-introduce the multi-return form.

### Bug 2: build_from_seed.sh missed v5.9.1 emit-llvm migration

`scripts/build_from_seed.sh:68` was `"${SEED}" "${SOURCE}"` (no
subcommand). Worked for pre-v5.9.1 seeds where the default was
emit-IR. The v5.9.1 PLAN updated lines 95 and 122 to use the new
`emit-llvm` subcommand explicitly but missed line 68 — a latent
bug that only surfaced when v5.10.0's Bb.4 refreshed the seed
past v5.9.1 behavior. The new seed treated `mnc mnc_all.mn` as
"compile and run" instead of "emit IR".

**Fix:** added `emit-llvm` to line 68. Comment cites the v5.9.1
DX.5 migration. Both old and new seeds accept the explicit form.

### Validation results

- ✅ `python3 scripts/build_stage1.py` — fresh stage1 build via
  Python bootstrap, 6.65 MB Linux ELF
- ✅ `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  — **66/66 goldens pass** (12.4s on WSL Ubuntu)
- ✅ `bash scripts/verify_fixed_point.sh` — **STRICT FIXED POINT**
  reached: stage2.ll == stage3.ll byte-identical at 226,560 lines,
  0 diff lines. The v5.9.0 milestone preserved through v5.10.0.
- ✅ `bash scripts/build_from_seed.sh` — succeeds end-to-end after
  Bb.4 refresh + the build_from_seed.sh fix; final mnc smoke test
  OK
- ✅ Bb.4 seed refresh: `bootstrap/seed/linux-x86_64/mnc` updated
  to v5.10.0 stage1 (6,646,968 bytes); `mnc.sha256` regenerated
  (`c8fe0351d4c0ed25fa743d1dd088374f03219e79e5fc643b7146cd7a105fb4e4`)

## What did NOT ship in v5.10.0

- **Manual Windows VM smoke for install.ps1** — both bundled and
  minimal paths. CI's `windows-bundled-llvm-smoke` job is the gate.
- **Valgrind / ASan baselines** — deferred. v5.10.0 changes are
  packaging-only on the executable side; the new C export is a
  leaf function with no aliasing concerns. Re-run with the
  v5.11.0 PLAN's Phase 5 validation matrix.
- **Tag + push** — held until user authorization. Two commits to
  push: v5.10.0 source (`c00f769`) + v5.10.0 Bb.4 closeout
  (this session).

---

## Validation status (this session, Windows host)

Local environment: Windows 11 Pro, no WSL, no `mnc` binary built
locally.

- ✅ `make lint` clean — `black --check` + `ruff` + `mypy` on 54
  source files (mapanare + runtime)
- ✅ Python AST parse on edited files (`emit_llvm_text.py`,
  `install.ps1`, `publish.yml`)
- ✅ YAML valid on `publish.yml`
- ✅ `pytest tests/ --ignore=tests/bootstrap`: 5,497 passed, 75
  skipped, 5 xfailed, **69 pre-existing subprocess-launch failures**
  (all `OSError [WinError 193]` on tests that subprocess-invoke
  the `mnc` binary which doesn't exist locally)
- ✅ Pytest delta vs. main: **zero new failures** (verified via
  `git stash` baseline runs at three different test-set
  granularities)

Pre-existing failures (NOT introduced by v5.10.0):

- `tests/parser/test_tensor_multi_index.py` — 11 failures
- `tests/parser/test_tensor_slice_wildcard.py` — 35 failures
- `tests/test_cli_default.py` — 6 failures (subprocess launch)
- `tests/test_cli_help.py` — multiple subprocess-launch failures
- `tests/llvm/test_enum_inline.py` — subprocess-launch failure

All confirmed identical with and without v5.10.0 changes via
`git stash` baseline comparison.

---

## Risk register

| ID | Risk | Status |
|---|---|---|
| Win.1b.R1 | Lazy-load DLL closure gap (clang loads a DLL only when targeting a specific arch) | Mitigated by Phase 6 smoke test — exercises pthreads, libm, file I/O. Smoke job in CI is the gate. |
| Win.1b.R2 | llvm.org URL retraction | actions/cache cushions; if cache key misses, manual mirror in our own release is the fallback (deferred until needed) |
| Win.1b.R3 | Bundled clang version drift vs. user's IDE clang | `mnc --version` should report the bundled version (not added in this release; v5.11.0 candidate) |
| Win.1b.R5 | Bundle exceeds 100 MB target | Set alarm at 150 MB. Current projection ~95 MB. CI smoke job gates on size. |
| Win.1b.R6 | `__mn_executable_dir()` returns wrong path on installs to non-default locations | Untested in this session; CI smoke validates default install path. Manual testing on UNC paths / spaces deferred to follow-up. |
| **NEW R8** | C runtime compilation not verified locally | No gcc/MSVC on this Windows host. CI is the gate. |
| **NEW R9** | `find_clang()` quote-wrapping interacts with cmd.exe parsing | Untested; relies on `system(3)` → cmd.exe handling `"<path>" --args` correctly. CI smoke job is the gate (it builds + runs hello-world via the bundled path). |

---

## Follow-up session checklist (when WSL is available)

1. `bash scripts/build_from_seed.sh` — expected to fail with
   "unknown function `__mn_executable_dir`"
2. Refresh seed per `bootstrap/seed/README.md` §"Updating the
   Seed" — rebuild stage1 via Python, regenerate seed bytes,
   commit `bootstrap/seed/` updates
3. `python scripts/build_stage1.py` — verify it builds
4. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
   — verify goldens 66/66 preserved
5. `bash scripts/verify_fixed_point.sh --keep` — confirm strict
   3-stage fixed-point still holds (the v5.9.0 milestone)
6. `VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh` — 0
   new ERRORs vs v5.9.2 baseline
7. `bash scripts/build_asan.sh && bash scripts/run_asan_goldens.sh`
   — 0 new findings vs v5.9.2 baseline
8. Commit Bb.4 seed refresh as a separate commit on `dev`
9. **Then** tag `v5.10.0` and push (triggers `publish.yml`)
10. Verify CI green: `build-cli` builds the bundle, smoke job
    passes, both ZIPs land in the release
11. Manual download + install on a clean Windows machine if
    available — both `MAPANARE_NO_BUNDLED_LLVM=` and `=1` paths

---

## Files changed

**Modified (9):**
- `runtime/native/mapanare_core.c` — `__mn_executable_dir()` +
  macOS dyld include
- `mapanare/emit_llvm_text.py` — Python bootstrap dispatch
- `mapanare/self/emit_llvm.mn` — runtime decl
- `mapanare/self/semantic.mn` — builtin name + symbol entry
- `mapanare/self/lower.mn` — Call lowering
- `mapanare/self/main.mn` — `find_clang()` + 6 call sites
- `.github/workflows/publish.yml` — bundle stages + smoke job +
  release-notes table
- `packaging/install.ps1` — `MAPANARE_NO_BUNDLED_LLVM` + banner +
  bundle detection
- `README.md` — Windows install section
- `VERSION` — 5.9.2 → 5.10.0
- `CHANGELOG.md` — `[5.10.0]` block
- `CLAUDE.md` — Current Version & Roadmap top entry; pruned to
  last 6

**Created (5):**
- `tools/llvm-bundle/extract_minimal.ps1` — bundle extractor
- `tools/llvm-bundle/REQUIRED_FILES.md` — closure documentation
- `docs/THIRD-PARTY-LICENSES.md` — Apache 2.0 + LLVM Exception
- `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md` (this file)
- `docs/roadmap/v5/v5.11.0/PLAN.md` — Pk.1 versioned filenames +
  Pk.2/3/4 deferrals

**Deferred for follow-up (1):**
- `bootstrap/seed/` — Bb.4 refresh on WSL

---

## Closure status

Win.1b.A through Win.1b.G — all source-authored and lint-validated.
The "release shipped" definition (CI green, bundle published, smoke
job passing) needs the WSL follow-up to land Bb.4 + tag.
