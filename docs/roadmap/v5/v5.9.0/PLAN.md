# v5.9.0 — DX.* — Native CLI hygiene (Windows install findings)

**Status:** PLANNING
**Breaking:** Yes (DX.5 only — `mnc file.mn` default changes from
emit-IR to run-program; gated behind a one-release deprecation
warning if the user wants the conservative path)
**Prerequisite:** v5.8.8 shipped (independent surface — Apple
AArch64 ABI work in v5.8.8 does not touch `mapanare/self/main.mn`
command dispatch). v5.9.0 can ship in parallel with v5.8.8 if the
two land on different branches; recommended to ship sequentially
to keep release notes clean.
**Estimated effort:**
- Phase 1 (DX.2 — `__MN_VERSION__` substitution) — 1-2h
- Phase 2 (DX.1 — `--help` / `-h`) — 1h
- Phase 3 (DX.4 — Windows `cache stats` portability) — 1-2h
- Phase 4 (DX.3 — clang-missing error message) — 1h
- Phase 5 (DX.6 — `mnc` vs `mapanare.exe` naming audit) — 1h
- Phase 6 (DX.5 — default-command behavior) — 1-2h **OR defer**
- Phase 7 (validation matrix + seed eval) — 1-2h
- **Total:** 7-11 hours across 1-2 focused sessions

---

## Goal

Close the user-visible CLI gaps surfaced by the v5.8.7 Windows
install probe. The Windows native binary works for the **happy
path** (compile a `.mn` file, get IR), but every adjacent surface
— `--help`, `--version`, `cache stats`, missing-clang, default
behavior — is broken or confusing. None of these are compiler
correctness bugs; all of them are first-impression bugs that
greet every new Windows user before they've written a line of
Mapanare.

This release is **dispatch-layer hygiene only**. Zero changes to
the parser, semantic checker, MIR, lowerer, optimizer, or
emitters. The full surface lives in `mapanare/self/main.mn`
(the native CLI driver) and `packaging/install.ps1` (the
PowerShell installer).

After this release:
- `mnc --help` prints actual help text instead of "cannot read
  file '--help'"
- `mnc version` prints `mapanare 5.9.0` instead of
  `mapanare __MN_VERSION__`
- `mnc cache stats` works on Windows (currently
  "-d was unexpected at this time" — a `cmd.exe` error)
- `mnc run file.mn` (when clang is missing) prints "install
  LLVM via `winget install LLVM.LLVM`" instead of bare
  "error: clang failed"
- `install.ps1`'s success-path message uses the right binary
  name, and the version string it prints is correct

---

## What broke (recap from Windows install probe)

User installed the published v5.8.7 Windows binary and reported
the following developer-notes summary:

> **Bugs Found**
>
> 1. **Version placeholder not replaced:** `mnc version` outputs
>    `mapanare __MN_VERSION__` instead of the actual version.
>    The build pipeline isn't substituting the placeholder.
> 2. **Cache stats command broken on Windows:** `mnc cache stats`
>    throws `-d was unexpected at this time` — looks like a batch
>    script or shell syntax issue.
>
> **UX Issues**
>
> 1. **No `--help` / `-h` support:** The CLI treats flags as
>    filenames (`error: cannot read file '--help'`).
> 2. **Default command dumps IR instead of running:**
>    `mnc file.mn` outputs LLVM IR rather than executing.
> 3. **Missing clang dependency is a hard stop:** All
>    `run`/`compile`/`build`/`test` commands fail silently with
>    "clang failed" if clang isn't installed. Most Windows users
>    won't have clang.

Cross-reference with source:

| Bug | File:line | Cause |
|---|---|---|
| `__MN_VERSION__` literal | `main.mn:37` | Placeholder; substitution in `scripts/build_stage1.py:46-65` runs against a tempdir copy of the source tree. The published Windows binary should pass through this — needs investigation. Even if the Python build path works, the **self-hosted** path admits in `main.mn:471-475` that it doesn't substitute. Either way, the structural fix is to eliminate the placeholder dance entirely and bake the version into the C runtime. |
| `cache stats` cmd error | `main.mn:760` | Shells out via `__mn_system` to `if [ -d .mnc_cache ]; then ... fi` — a POSIX shell conditional. On Windows, `__mn_system` invokes `cmd.exe`, which interprets `[` as the start of a path expansion and `-d` as an unknown switch. |
| `--help` / `-h` | `main.mn:711-720, 777, 783` | Subcommand dispatch checks string-equality against `test`, `build`, `run`, `cache`, `compile`, `version`, `--version`. There is no `--help` / `-h` branch. The default-falls-through branch at `:783` treats arg1 as a filename and errors. |
| Default = IR dump | `main.mn:782-801` | The default branch emits IR to stdout. Useful for compiler developers; surprising for everyone else. |
| `clang failed` opaque | `main.mn:420, 528, 573, 633, 692` | All print bare `error: clang failed\n`. None distinguish "clang exited non-zero" from "clang isn't installed". None tell the user how to fix it. |
| `mnc` vs `mapanare.exe` | `install.ps1:86, 93-97` | The installer's success-path runs `& $MapanareBin --version` against a path it derives as `mapanare.exe`, and the getting-started message tells users to run `mapanare init` / `mapanare run` / `mapanare build`. The published binary, per the user, is invoked as `mnc`. Either install.ps1 references a stale name or the binary ships under both names; in either case the docs and the reality disagree. |

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **DX.1** | MEDIUM (UX) | `mnc --help` and `mnc -h` print usage text and exit 0. `mnc <subcommand> --help` prints subcommand-specific help. Currently both fall through the default-IR-emit branch and print `error: cannot read file '--help'`. | 1h |
| **DX.2** | HIGH (first-impression) | `mnc version` returns the actual version (`mapanare 5.9.0`), not the literal placeholder. Structural fix: add a new C-runtime export `__mn_version_string()` that returns a baked-in constant set at C-runtime compile time. `version()` in `main.mn` calls the export instead of returning a string-literal-with-placeholder. Eliminates the build-time text-substitution dance entirely. Same dispatch shape as v5.8.6 We.1's `__mn_host_is_windows()`. | 1-2h |
| **DX.3** | MEDIUM (UX) | When clang exits non-zero in `run` / `compile` / `build` / `test`, distinguish "clang not on PATH" from "clang ran but failed". For the missing case, print platform-specific install instructions (`winget install LLVM.LLVM` on Windows, `apt install clang` on Debian/Ubuntu, `brew install llvm` on macOS, plus a fallback link to llvm.org). For the failed case, surface clang's actual stderr (currently swallowed via `2>/dev/null`). | 1h |
| **DX.4** | MEDIUM (Windows portability) | `mnc cache stats` works on Windows. Replace the bash-conditional shell-out with native Mapanare directory inspection: walk `.mnc_cache` via `__mn_dir_list` (or add the export if missing), count files, sum sizes. No shell-out, no platform divergence. | 1-2h |
| **DX.5** | LOW-MEDIUM (UX, breaking) | `mnc file.mn` defaults to **run** instead of **emit IR**. Keep the IR dump under `mnc emit-llvm file.mn` (parallel to the existing `mapanare emit-llvm` Python CLI subcommand). **Decision below.** | 1-2h or defer |
| **DX.6** | LOW (docs/install) | Audit `install.ps1` references to `mapanare.exe` vs the actual published binary name (`mnc.exe` per the user's invocation). Pick one canonical name; update install.ps1, README, getting-started docs to match. If both names ship as a transition: add an `mnc.exe` → `mapanare.exe` shim (or vice versa) for one release, with a deprecation warning on stderr the first time the deprecated name is used. | 1h |
| **DX.7** | LOW | Update `install.ps1` getting-started message to reflect actual subcommand names (the script currently lists `mapanare build main.mn` which assumes a binary name that may not match reality post-DX.6). Drop the `requires LLVM` parenthetical if v5.10.0 lands the bundled toolchain — but that's a v5.10.0 follow-up, not v5.9.0 work. | 30 min |

---

## Phase plan

### Phase 1 — DX.2 (`__MN_VERSION__` structural fix)

**Highest-impact item; do first.** Every Windows user sees the
broken version string at install time (install.ps1 prints
`--version` on success).

1. Add `__mn_version_string()` to `runtime/native/mapanare_core.c`:
   ```c
   // Compile-time bake. Set via -DMAPANARE_VERSION="\"5.9.0\""
   // in the build-stage1 / publish workflow clang invocation.
   #ifndef MAPANARE_VERSION
   #define MAPANARE_VERSION "unknown"
   #endif

   const char *__mn_version_string(void) {
       return MAPANARE_VERSION;
   }
   ```
2. Add the export to the runtime declaration block in
   `mapanare/emit_llvm_text.py` (and the self-hosted
   `mapanare/self/emit_llvm.mn`) so Mapanare-level code can call
   it. Mirror the v5.8.6 We.1 pattern for
   `__mn_host_is_windows()` — find that decl and add the new one
   adjacent.
3. Wire the build flag in:
   - `scripts/build_stage1.py` — pass
     `-DMAPANARE_VERSION="\"$(cat VERSION)\""` to the clang
     invocation that compiles `runtime/native/mapanare_core.c`
   - `.github/workflows/publish.yml` — same flag in the
     `build-native` job's clang step
   - `Makefile` — same flag in the runtime build target
4. Update `mapanare/self/main.mn:36-38`:
   ```mn
   fn version() -> String {
       return "mapanare " + __mn_version_string()
   }
   ```
5. **Decide:** does the OLD `__MN_VERSION__` placeholder + the
   `_substitute_version()` block in `scripts/build_stage1.py:46-65`
   stay or go?
   - **Recommend: delete.** The whole point of DX.2 is to
     eliminate the placeholder dance. Leaving the placeholder
     creates two paths to the version (the C-runtime export AND
     the in-source substitution) which will drift. Drop the
     placeholder and the substitution function in the same commit.
   - This means the v5.8.6 bootstrap seed (which has the old
     placeholder baked in) gets superseded by a refresh. Same
     break shape as v5.8.4 → v5.8.5 → v5.8.6: the new builtin
     call to `__mn_version_string()` doesn't exist in the seed.
     Bb.3 seed refresh per `bootstrap/seed/README.md`.
6. Validation gate before Phase 2:
   - `mnc version` on a fresh build prints `mapanare 5.9.0` (or
     whatever VERSION reads at the time)
   - `mnc --version` does the same
   - install.ps1 dry-run (extract a built ZIP, run from extracted
     path) prints the right version
   - Goldens 66/66 preserved

### Phase 2 — DX.1 (`--help` / `-h`)

1. `main.mn:721` — before the existing `arg1 == "test"` branch,
   add:
   ```mn
   if arg1 == "--help" || arg1 == "-h" || arg1 == "help" {
       print_help_text()
       return
   }
   ```
2. New function `print_help_text()` near `version()` in `main.mn`.
   Output the existing usage block (currently at `main.mn:712-718`)
   plus a one-line description per subcommand. Keep it ≤ 30 lines
   so it fits in a 80x24 terminal.
3. Subcommand-specific help: when `__mn_argv(2) == "--help"`
   inside any subcommand branch, print just that subcommand's
   usage. Cheapest implementation: pass `--help` as a sentinel
   arg through and print from inside `run_build` / `run_compile`
   / etc. Keep the per-subcommand help to 5-10 lines each.
4. Update the `argc < 2` usage block at `main.mn:711-719` to
   include `mnc --help` in the listed commands and to mention
   `mnc help <subcommand>` for per-subcommand details.
5. Validation: `mnc --help`, `mnc -h`, `mnc help`, `mnc help
   build`, `mnc build --help` all exit 0 with help text. None of
   them error or fall through to the default branch.

### Phase 3 — DX.4 (`cache stats` Windows portability)

1. Audit `mapanare/self/main.mn` for **all** `__mn_system` shell-
   outs that use POSIX-only syntax. Catalog before fixing.
   - `:760` (cache stats) — `if [ -d ... ]` conditional
   - `:755` (cache clean) — `rm -rf` (Windows: `rmdir /s /q`)
   - `:390-394` (link_with_runtime) — `gcc ... 2>/dev/null`
     (Windows: `2>NUL`)
   - `:416, 525-526, 567, 690-691, 631` (clang invocations) —
     `2>/dev/null` (Windows: `2>NUL`)
   - `:537` (strip) — POSIX `strip`; Windows uses `llvm-strip` or
     similar
2. **Strategy decision:** patch each shell-out to detect host OS
   and emit the right syntax, OR replace shell-outs with native
   Mapanare runtime calls.
   - **Recommend:** native runtime calls for `cache stats` /
     `cache clean` (the bug-source surface). Add
     `__mn_dir_list(path) -> List<String>` and
     `__mn_file_size(path) -> Int` exports to
     `runtime/native/mapanare_core.c` if they don't exist; then
     rewrite the cache-stats body in pure Mapanare. No shell-out,
     no platform divergence, no escaping nightmare.
   - For the clang/gcc/strip invocations: portability shim. Add
     a `__mn_dev_null_redirect()` helper that returns
     `" 2>/dev/null"` on POSIX and `" 2>NUL"` on Windows.
     Concatenate it into the command strings instead of
     hardcoding.
3. Validation: `mnc cache clean` then `mnc cache stats` works on
   both Linux (existing behavior) and Windows (currently broken).
   Builds via `mnc build <dir>` produce cache, `mnc cache stats`
   reports correct file count + size.

### Phase 4 — DX.3 (clang-missing error)

1. Helper function `check_clang_available() -> Bool` in `main.mn`.
   Probes via `__mn_system("clang --version > /tmp/.mnc_probe
   2>&1")` (or the platform-portable equivalent post-Phase 3).
   Returns true if exit 0, false otherwise.
2. New helper `print_clang_install_instructions()`. Detect host
   OS via `__mn_host_is_windows()` (already exported per v5.8.6)
   and print:
   - Windows: `winget install LLVM.LLVM` (or
     `https://llvm.org/builds`)
   - macOS: `brew install llvm` (or `xcode-select --install` for
     Apple clang)
   - Linux: `apt install clang` / `dnf install clang` / `pacman
     -S clang` (one suggestion suffices; users on other distros
     will recognize the pattern)
3. Wrap each `__mn_system("clang ...")` call site in `main.mn`
   (`:416, 525-526, 567, 631, 690-691`) with an early
   `check_clang_available()` probe. On miss:
   ```
   error: clang not found.
   Mapanare needs clang to compile to native binaries.
   Install LLVM and try again:
     Windows: winget install LLVM.LLVM
     macOS:   brew install llvm
     Linux:   apt install clang  (or your distro's equivalent)
   See https://llvm.org/builds for direct downloads.
   ```
4. On hit (clang found but exited non-zero): preserve the existing
   `error: clang failed` BUT stop swallowing stderr. Currently
   `2>/dev/null` hides the real error. Strategy: pipe to
   `/tmp/.mnc_clang_stderr`, then on non-zero, read and reprint.
5. Validation: rename `clang.exe` out of PATH on a Windows VM
   (or run in a Docker container with no clang); `mnc run
   hello.mn` prints the install instructions. Restore clang;
   same command works.

### Phase 5 — DX.6 (`mnc` vs `mapanare.exe` audit)

1. Find ground truth: what does `.github/workflows/publish.yml`
   actually name the binary in the Windows ZIP? Read the
   `build-native` job and trace the artifact names.
2. Find every reference in `packaging/install.ps1`:
   - `:86` `$MapanareBin = Join-Path $InstallDir "mapanare.exe"`
   - `:93-97` getting-started message
3. Find every reference in `README.md`, `README.es.md`,
   `README.pt.md`, `README.zh-CN.md`, `docs/SPEC.md`,
   `docs/manifesto.md`, getting-started docs.
4. **Decision:** pick one canonical binary name.
   - **Recommend `mnc`** (matches user's actual invocation,
     matches `mnc-stage1`, matches `scripts/mnc-build.sh`,
     matches the self-hosted compiler's identity). Migrate
     install.ps1 + docs to say `mnc`.
   - If the binary already ships as `mapanare.exe` post-build,
     add a rename step in `publish.yml` (or ship both names via
     a `copy mnc.exe mapanare.exe` step, with `mapanare.exe`
     deprecated and emitting a one-time stderr warning).
5. Validation: install.ps1 success message references the right
   binary name; running the suggested first command from
   getting-started works without "command not found".

### Phase 6 — DX.5 (default-command behavior) — **OPTIONAL**

This is the only behavior change in v5.9.0 that breaks an
existing workflow (compiler developers and CI scripts that pipe
`mnc file.mn > out.ll` will need to update to
`mnc emit-llvm file.mn > out.ll`).

**Decision below.** If we ship it:

1. New subcommand `emit-llvm` in `main.mn`, parallel to the
   existing `compile` / `build` / `run` branches. Body lifts
   the current default-fall-through code at `:782-801` verbatim.
2. Default branch (when `arg1` doesn't match any subcommand and
   doesn't start with `-`) becomes:
   ```mn
   // Treat as "mnc run <file>" for newcomers.
   // Print a one-line deprecation warning to stderr the first
   // time, so existing scripts get a heads-up before v5.10.0.
   if arg1.ends_with(".mn") {
       __mn_str_eprint("note: implicit 'run' is the default in v5.9+; use 'mnc emit-llvm' for IR output\n")
       run_program(arg1)
       return
   }
   ```
3. CHANGELOG.md `[5.9.0]` entry calls out the default change as
   a **breaking change** in bold so anyone scanning the notes
   sees it.
4. Validation: `mnc hello.mn` runs `hello.mn` (prints "Hello,
   world!" or whatever the program does); `mnc emit-llvm
   hello.mn` prints IR.

### Phase 7 — DX.7 + validation matrix + seed eval

1. Update `packaging/install.ps1` getting-started block (lines
   93-97) to reflect post-DX.5 / post-DX.6 reality. If DX.5
   ships, change `mapanare run main.mn` → `mnc main.mn`. If
   DX.6 picks `mnc`, change `mapanare init` → `mnc init`.
2. Full validation matrix:
   - `make lint` clean
   - `make test` non-bootstrap pytest: 0 failures, baseline
     preserved
   - Goldens 66/66 preserved (this release should not touch any
     compiler path that affects IR emission — gate on byte-
     identical IR diff vs v5.8.8 for at least 5 representative
     goldens)
   - `bash scripts/verify_fixed_point.sh` NEAR or strict
   - `check_struct_registry.py` clean
   - Sanitizer matrix (valgrind, ASan) — no new regressions vs
     v5.8.8 baseline. Note: this release adds runtime exports
     (`__mn_version_string`, optionally `__mn_dir_list` /
     `__mn_file_size` / `__mn_dev_null_redirect`); each is a new
     allocation/probe surface.
3. Bootstrap seed: refresh per `bootstrap/seed/README.md` if
   Phase 1's recommendation lands (Bb.3). Skip if Phase 1 keeps
   the old placeholder dance as a fallback.
4. Manual smoke test on a clean Windows VM:
   - Download v5.9.0 ZIP
   - Run `irm <URL>/install.ps1 | iex`
   - Confirm install.ps1 success message shows `mapanare 5.9.0`
   - `mnc --help` works
   - `mnc cache stats` works (on a project with a cache, or on
     a fresh dir prints "No cache")
   - `mnc run hello.mn` (without LLVM installed) prints the
     install-clang instructions
   - `mnc run hello.mn` (with LLVM installed via winget) runs
     and prints "Hello, world!"

---

## Decisions

### Decision 1: structural fix vs minimal patch for DX.2

The user's report says "the build pipeline isn't substituting
the placeholder." A minimal patch would investigate why
`scripts/build_stage1.py:_substitute_version()` didn't run on
the published Windows binary, fix the workflow, and call it done.

The structural fix (Phase 1 above) eliminates the placeholder
entirely in favor of a C-runtime export. **Recommendation:
structural fix.**

Rationale:
- The placeholder dance has produced two known bugs across the
  project's history: this one (v5.8.7 publish) and the v4.28.0
  forensics (`docs/roadmap/v4/v4.28.0/FORENSICS.md`) where the
  hardcoded version went 19 minor versions stale. The mechanism
  is fragile.
- The C-runtime export pattern is already the project's lingua
  franca for build-time-baked constants (v5.8.6 We.1's
  `__mn_host_is_windows()`, `__mn_host_arch_bits()`).
- The placeholder substitution requires every build path
  (Python bootstrap, self-hosted, CI publish, install scripts)
  to participate. The C-runtime export requires only the
  C-runtime build, which already participates in every path.
- Comment at `main.mn:471-475` already flags the substitution
  as a self-hosted-compiler gap. Eliminating the placeholder
  closes the gap by removing the requirement.

Cost: bootstrap seed refresh (Bb.3). Same one-day cost as
v5.8.5 (Bb.1) and v5.8.6 (Bb.2).

### Decision 2: ship DX.5 (default-command change) in v5.9.0?

DX.5 is the only behavior break. Shipping it now means:
- Existing compiler dev workflows that pipe `mnc file.mn >
  out.ll` for IR inspection break (need
  `mnc emit-llvm file.mn`).
- CI scripts in dependent ecosystems (Dato, Mapanare-Research/
  examples, etc.) may break.
- New users get a much better first impression (`mnc hello.mn`
  prints "Hello, world!" instead of dumping IR).

**Recommendation: defer DX.5 to v5.9.1.** v5.9.0 is already a
6-item release; adding the only-breaking-item compounds risk.
Ship DX.1-4 + DX.6-7 in v5.9.0 (additive only); ship DX.5 as
v5.9.1's headline a week later, after dust settles on v5.9.0.

If shipping in v5.9.0 is preferred (single-release theme is
"DX hygiene"), gate DX.5 behind a stderr deprecation warning
for one release to give downstream a heads-up. **The PLAN
includes Phase 6 either way; mark it Phase 6 OPTIONAL and let
the implementer's judgment apply.**

### Decision 3: DX.4 strategy — shell-out portability shim vs native Mapanare rewrite?

For `cache stats` specifically, the native Mapanare rewrite is
~30 lines and eliminates a Windows-specific bug surface
permanently. Recommendation: native rewrite for cache stats +
clean.

For the clang/gcc/strip invocations (a separate `2>/dev/null`
vs `2>NUL` issue), a portability shim is cheaper than rewriting
each one. Add `__mn_dev_null_redirect()` and concatenate.

The `link_with_runtime` shell-out at `:390-394` is more
involved: it builds a multi-flag gcc command. Port to a builder
helper that picks `gcc` vs `clang` vs `cl.exe` based on host
OS, but **only if v5.10.0's bundled-clang work doesn't subsume
it.** Defer to v5.10.0 if there's overlap.

### Decision 4: bump VERSION immediately or last?

**Recommendation: last.** Same reasoning as v5.8.8: bumping
early forces a re-bump if implementation slips into v5.9.0.1.
DX.2 specifically tests the version string mid-release; bump
at end of Phase 7 validation.

### Decision 5: docket name (DX) vs functional name (CLI)?

The project's existing dockets are mostly two-letter codes
(Da.*, We.*, Bb.*, Sh.*, Ge.*, Lk.*, Own.*, Cb.*, Ve.*). DX
follows the pattern. **Recommendation: keep DX.\*.**

If a longer-form ID is preferred for the
`docs/roadmap/v5/PARITY_GAPS.md` ledger, "DX" can map to
"Developer Experience" in the ledger header. Existing dockets
have similar mappings (Sh = self-hosting, Ge = generics, etc.).

---

## What ships in v5.9.0

- **Source changes:**
  - `mapanare/self/main.mn` — `--help` branch, version() rewrite,
    cache-stats portability, clang-missing detection
  - `runtime/native/mapanare_core.c` — `__mn_version_string()`
    export, optionally `__mn_dir_list` / `__mn_file_size` /
    `__mn_dev_null_redirect`
  - `mapanare/emit_llvm_text.py` — runtime decl block updated
    for new exports (mirrors v5.8.6 We.1 pattern)
  - `mapanare/self/emit_llvm.mn` — same, parallel
  - `scripts/build_stage1.py` — `-DMAPANARE_VERSION` flag wired
    to clang; `_substitute_version()` block deleted (per
    Decision 1)
  - `Makefile` — same flag in runtime build
  - `.github/workflows/publish.yml` — same flag in build-native
  - `packaging/install.ps1` — getting-started message + binary
    name corrected (DX.6, DX.7)
- **Docs:**
  - `docs/roadmap/v5/v5.9.0/PLAN.md` (this file)
  - `docs/roadmap/v5/v5.9.0/PROMPT.md` (execution prompt;
    drafted alongside, gitignored, not committed)
  - `docs/roadmap/v5/v5.9.0/SESSION_REPORT.md` (closeout
    narrative once shipped)
  - `CHANGELOG.md` — `[5.9.0]` block
  - `docs/known_issues.md` — DX.1-DX.6 rows added then flipped
    to CLOSED v5.9.0
  - `CLAUDE.md` release-history bullet
  - `README.md` + localized variants (es, pt, zh-CN) — binary
    name update if DX.6 picks differently
- **Bootstrap:**
  - **Bb.3 seed refresh** if Decision 1 lands on the structural
    fix (it should). Otherwise no seed change.
- **Version:** 5.8.8 → 5.9.0 at end of Phase 7.

## What does NOT ship in v5.9.0

- **DX.5 default-command change** if Decision 2 defers it. v5.9.1
  picks it up.
- **Bundled LLVM toolchain.** That's v5.10.0's headline (Win.1b).
  If this release adds clang-missing detection (DX.3) and v5.10.0
  bundles clang, the detection still runs but always passes — the
  message becomes a fallback for users who explicitly disabled the
  bundle.
- **NSIS / WiX installer.** Punted indefinitely; install.ps1 +
  v5.10.0 bundle covers the demand signal.
- **macOS installer parity.** macOS users currently install via
  `packaging/install.sh` (mirroring install.ps1). Audit it for
  the same DX.6 naming inconsistencies in v5.9.0; the rest is
  out-of-scope.
- **Cross-platform `__mn_dir_list` etc.** Only added if DX.4
  Phase 3 needs them. If the cache-stats rewrite uses different
  exports that already exist, skip the new ones.
- **Compiler / parser / semantic / MIR / lower / emitter
  changes.** Zero. v5.9.0 is dispatch-layer only. If any item
  drifts into compiler internals, split it to a v5.9.x follow-up.

---

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| DX.R1 | Phase 1's seed refresh introduces a new bug (the new builtin export interferes with self-hosted compilation). | Same break shape as Bb.1/Bb.2 from v5.8.5/v5.8.6, both of which closed cleanly. Follow the documented refresh procedure exactly. Validate with full goldens 66/66 + fixed-point on Linux before Phase 2. |
| DX.R2 | Phase 1 deletes the placeholder dance, but a downstream tool (Dato, ecosystem packages) reads `__MN_VERSION__` directly from the source tree. | Grep for `__MN_VERSION__` across the entire ecosystem (`Mapanare-Research/dato`, `mapanare/stdlib/*`) before deleting. If any consumer exists, leave the placeholder in source AND wire the new export — drift becomes the consumer's problem to fix. |
| DX.R3 | Phase 2's `--help` code lands but the help text drifts from reality the next time a subcommand changes. | Add `tests/test_cli_help.py` (Python pytest) that runs the native binary with `--help` and asserts each subcommand is mentioned. Catches drift via CI. |
| DX.R4 | Phase 3's native cache-stats rewrite needs runtime exports (`__mn_dir_list`, etc.) that don't exist, requiring runtime work that pulls in extra surface. | Audit existing exports first. If the project already has `__mn_file_*` exports that scan directories, reuse. If not, the addition is small (10-20 LOC of C) and isolated. |
| DX.R5 | Phase 4's clang-missing probe adds a probe-per-invocation overhead (every `mnc run` now runs `clang --version` first). | Probe once per process invocation, cache result in a module-level static. Cost: <10 ms on cold start. Acceptable. |
| DX.R6 | Phase 5 audit reveals `mapanare.exe` IS the canonical name and `mnc` is a dev convenience alias the user happens to invoke. Migrating in either direction breaks half the docs. | Source-of-truth check is `.github/workflows/publish.yml`'s `build-native` job. Whatever it produces is canonical for end users. Do the migration to match canonical, not the other way around. |
| DX.R7 | Phase 6 (DX.5 default change) breaks a CI script in a dependent repo and the user only finds out post-release. | Ship DX.5 as v5.9.1 per Decision 2. v5.9.0 stays additive-only and reversible. |
| DX.R8 | install.ps1 fix introduces a Windows-VM-only bug (PowerShell 5.1 vs 7+ syntax). | Test against both PowerShell versions on a Windows 10 + Windows 11 VM matrix. install.ps1 currently uses syntax compatible with both; preserve that. |
| DX.R9 | The user's reported `__MN_VERSION__` bug doesn't reproduce after Phase 1's structural fix because the underlying workflow issue (Decision 1's "minimal" path) was different and we never investigated. | Phase 1 validation includes "install the published v5.9.0 ZIP on a Windows VM and confirm the version string." If it shows correctly, the structural fix worked regardless of root cause. The structural fix is robust to whatever the original workflow bug was. |

---

## Closure checklist for v5.9.0

### Phase 1 (DX.2)

- [ ] `__mn_version_string()` exported from
      `runtime/native/mapanare_core.c`
- [ ] `MAPANARE_VERSION` define wired in `scripts/build_stage1.py`,
      `Makefile`, `.github/workflows/publish.yml`
- [ ] `mapanare/self/main.mn:36-38` uses the new export
- [ ] Old `__MN_VERSION__` placeholder deleted from `main.mn`
- [ ] `_substitute_version()` deleted from
      `scripts/build_stage1.py`
- [ ] Bootstrap seed refreshed (Bb.3) if Decision 1 → structural
- [ ] `mnc version` prints correct version on Linux + Windows

### Phase 2 (DX.1)

- [ ] `mnc --help`, `mnc -h`, `mnc help` all work
- [ ] `mnc help <subcommand>` works for every subcommand
- [ ] `mnc <subcommand> --help` works
- [ ] `tests/test_cli_help.py` exists and passes

### Phase 3 (DX.4)

- [ ] `mnc cache stats` works on Windows
- [ ] `mnc cache clean` works on Windows
- [ ] All other `__mn_system` shell-outs audited; portability
      shim or native rewrite applied where needed
- [ ] No `2>/dev/null` literals remain in `main.mn` (replaced
      with `__mn_dev_null_redirect()` calls)

### Phase 4 (DX.3)

- [ ] `mnc run hello.mn` (no clang) prints install instructions
- [ ] `mnc run hello.mn` (with broken clang) surfaces clang's
      stderr, not just "clang failed"
- [ ] Per-platform install instruction strings tested on Windows,
      macOS, Linux

### Phase 5 (DX.6)

- [ ] Canonical binary name decided (recommend: `mnc`)
- [ ] `install.ps1` references match canonical
- [ ] All README variants reference canonical
- [ ] Getting-started docs reference canonical
- [ ] `publish.yml` produces the canonical name (or rename
      step added)
- [ ] `mnc.exe` and `mapanare.exe` (if both ship) work; the
      deprecated one prints stderr warning

### Phase 6 (DX.5) — IF SHIPPED

- [ ] `mnc file.mn` runs the file
- [ ] `mnc emit-llvm file.mn` prints IR
- [ ] CHANGELOG.md flags the change as **BREAKING**
- [ ] One-line deprecation warning printed by the implicit-run
      path for one release

### Phase 7 (validation + release)

- [ ] `make lint` clean
- [ ] `make test` non-bootstrap pytest: 0 failures
- [ ] Goldens 66/66 preserved
- [ ] 5+ representative goldens byte-identical IR vs v5.8.8
- [ ] `bash scripts/verify_fixed_point.sh` NEAR or strict
- [ ] `check_struct_registry.py` clean
- [ ] Sanitizer matrix (valgrind, ASan) — no new regressions
- [ ] Bootstrap seed: clean `bash scripts/build_from_seed.sh`
      OR refreshed (Bb.3)
- [ ] Windows VM smoke test: install.ps1, then `mnc --help`,
      `mnc version`, `mnc cache stats`, `mnc run hello.mn`
      (with + without clang)

### Documentation + release

- [ ] `CHANGELOG.md` `[5.9.0]` block filled in
- [ ] `docs/known_issues.md` DX.* rows flipped to CLOSED v5.9.0
- [ ] `CLAUDE.md` release-history bullet added
- [ ] `docs/roadmap/v5/v5.9.0/SESSION_REPORT.md` written
- [ ] `VERSION` bumped 5.8.8 → 5.9.0
- [ ] `git tag v5.9.0` per the user-approval-required rule

---

## What this plan trusts vs. what it gates

**Trusts:**
- The user's report accurately describes Windows install behavior.
  Reproduction on a Windows VM is Phase 7's smoke-test gate; if
  reproduction fails, investigate before claiming a fix.
- `runtime/native/mapanare_core.c` accepts `-DMAPANARE_VERSION`
  cleanly. (Standard C; trivially true.)
- The C-runtime export pattern from v5.8.6 We.1
  (`__mn_host_is_windows()`) is reusable for the version export.
- `__mn_system` shell-outs on Windows invoke `cmd.exe` (the
  observed `-d unexpected` error confirms this).
- `install.ps1`'s success-path printing the version is the
  primary first-impression surface for Windows users — fixing
  DX.2 is the highest-impact item.

**Gates on Phase validation:**
- Bootstrap seed refresh works cleanly (Bb.3).
- Goldens 66/66 preserved across all phases.
- `mnc --help` doesn't introduce new parser ambiguity (e.g., a
  user with a file literally named `--help.mn` shouldn't break;
  test this edge case).
- Phase 4's clang probe doesn't slow down `mnc run` cold-start
  noticeably.
- Phase 5's binary-name migration doesn't break any CI scripts
  in the repo itself (search `.github/workflows/*.yml` for
  hardcoded references).

---

## Cross-version coordination

This release is **independent of v5.8.8** (Apple AArch64). The
two surfaces don't overlap:
- v5.8.8: ABI dispatch in `abi.py`, `emit_llvm_text.py`,
  `emit_llvm.mn`. Compiler internals.
- v5.9.0: command dispatch in `main.mn`, runtime exports in
  `mapanare_core.c`, install script. Driver layer.

If v5.8.8 hasn't shipped when v5.9.0 is ready, ship sequentially
(v5.8.8 first to keep release notes clean) but it is not
technically blocked.

This release is a **prerequisite for v5.10.0** in two ways:
- DX.3 (clang-missing error) becomes the fallback path for
  v5.10.0's bundled-toolchain logic. If the bundle is present,
  use it; if absent (user disabled it via env var), fall through
  to DX.3's install instructions.
- DX.6 (`mnc` vs `mapanare.exe`) needs to be settled before
  v5.10.0's bundled toolchain extends `install.ps1`, otherwise
  v5.10.0 inherits the same naming inconsistency.

The `docs/roadmap/v5/v5.10.0/PLAN.md` Win.1b items reference
v5.9.0 closures by docket ID.
