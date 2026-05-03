# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Mapanare is an AI-native compiled language with first-class agents,
signals, streams, and tensors. Compiles to LLVM IR (primary) and C
(fallback via gcc). WebAssembly backend for browser/server targets.
Self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in
`mapanare/self/`. The compiler compiles itself —
`bash scripts/build_from_seed.sh` builds from source with no Python.

**Current version:** see `VERSION` file.

## Current Version & Roadmap

Most recent releases. Full history at
`docs/roadmap/ROADMAP.md` and
`docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` per release:

- **v5.33.0** (ready, not tagged) — **Nu.1 + Nu.2 + Nu.3 + Nu.4
  + Nu.5 + Nu.6 — ship native `mnc` in the Linux x86_64 and
  macOS arm64 release tarballs.** Mirror of v5.32.0 Nw.\*
  applied to the two existing Unix tarballs. Closes the
  asymmetry where Windows had the fix and Unix didn't —
  release-tarball users on Linux x86_64 and macOS arm64
  no longer hit the Python bootstrap on `mnc --version`,
  `mnc run`, or `mnc build`. **Zero compiler edits. Zero
  runtime edits. Zero `mapanare/self/*.mn` source edits.**
  Strict 3-stage fixed point preserved by construction at
  v5.32.0's **241,898 lines / 0 diff** (28-release strict
  streak from the v5.7.1 baseline). Goldens **95/95**.
  **Nu.1 + Nu.2 deviation from PROMPT.** PROMPT scoped
  four arches: Linux x86_64 + Linux aarch64 + macOS x86_64
  + macOS arm64. v5.33.0 ships only the two arches that
  already build natively in `build-native` (Linux x86_64
  on `ubuntu-latest`, macOS arm64 on `macos-latest`).
  Linux aarch64 and macOS x86_64 are **deferred to v5.34.0**.
  Reasons: (a) `scripts/build_stage1.py` has no `--target`
  / `--output` flags — it always builds for the host;
  cross-compile would need new infrastructure that exceeds
  v5.32.0's "lift the proven path" precedent; (b) Linux
  aarch64 needs a cross-compile + qemu smoke pipeline that
  doesn't exist; (c) macOS x86_64 needs a separate
  `macos-13` runner and a brand-new tarball name in the
  release matrix. Mirrors v5.32.0's own "deviation from
  PROMPT" (build-native reuse vs. PROMPT's cross-compile
  recipe — same logic: prefer the validated path; preserve
  the more ambitious recipe for the next minor when it's
  motivated). **Nu.1 + Nu.2 plumbing**: `build-native`
  Linux + macOS jobs upload `mnc-linux-x64` /
  `mnc-darwin-arm64` as workflow artifacts (mirrors the
  `mnc-windows-x64-native` Nw.2 upload, single-day
  retention, `if-no-files-found: error`). `build-cli`
  Linux + macOS paths download the matching artifact, run
  three guards before staging — ELF / Mach-O magic
  (`7f454c46` for ELF; `cffaedfe` for Mach-O 64-bit
  little-endian) + 20 MB size ceiling (native is ~3-4 MB;
  PyInstaller-copy regression would be ~30 MB) +
  non-zero-bytes check — then copy to
  `dist/mapanare/mnc` (sibling of the existing
  `dist/mapanare/mapanare` PyInstaller binary; bundle-root
  layout matching the v5.32.0 Nw.2 decision rather than
  the PROMPT's `bin/mnc` shape). macOS path also runs
  ad-hoc `codesign -s -` so Gatekeeper doesn't quarantine
  the binary on first run after tar extraction; proper
  Developer ID notarization is a v5.34.0+ LOW.
  **Nu.4** smoke gates: two layers, both load-bearing.
  **Layer 1 in-job** (`build-cli` "Clean Linux/macOS native
  mnc smoke before archiving"): on the staging directory,
  asserts `dist/mapanare/mnc --version` (a) contains the
  expected version string from `VERSION`, (b) does not
  spawn a new Python interpreter (snapshots `pgrep -fl
  python` count before / after — same anti-pattern Windows
  Nw.4 closes). **Layer 2 published** (extends existing
  `linux-tarball-smoke` + `macos-tarball-smoke` jobs which
  already gate on `windows-sdk-smoke`'s shape): downloads
  the published tarball from the GitHub Release, runs the
  same magic / size / version-string / no-Python-spawn
  checks. Per-platform stat flag (`stat -c%s` Linux vs.
  `stat -f%z` macOS). The no-Python assertion is the
  load-bearing one — that's the specific anti-pattern
  v5.33.0 closes for the Unix release tarballs.
  **Nu.5** fallback-wrapper audit: `mapanare/__main__.py`
  refactored to extract `_native_binary_name(os_name=...)`
  (4 LOC). Pre-v5.33.0 the suffix-selection logic
  (`"mnc.exe" if os.name == "nt" else "mnc"`) was inlined
  in `_native_binary` and only host-OS-testable —
  monkeypatching `os.name` globally to test the *other*
  branch crashes pathlib (`NotImplementedError: cannot
  instantiate 'WindowsPath' on your system`). The new
  helper takes `os_name` as a parameter so tests can pin
  the value without touching pathlib. New
  `tests/test_native_fallback.py::test_native_binary_suffix_per_platform`
  parametrizes over (`posix` → `mnc`, `nt` → `mnc.exe`)
  so a Linux CI worker validates the Windows lookup and
  vice versa. 5/5 GREEN. Falsifiability: hardcoding the
  wrong suffix flips one of the two parametrized cases.
  **Nu.6** docs: README.md install section gains a
  paragraph noting v5.33.0+ ships native `mnc` on Linux
  x86_64 + macOS arm64; macOS-quarantine workaround
  (`xattr -d com.apple.quarantine`) documented inline.
  CLAUDE.md "Native-First Philosophy" updated; this
  release-notes entry added. **Localized READMEs
  (es/pt/zh-CN) deliberately not updated** — v5.32.0
  followed the same pattern (English README only); the
  v5.28.0 panel H.4 finding tracks localized README
  updates as a bookkeeping cycle, not per-release work.
  Source delta: ~120 LOC YAML in `.github/workflows/publish.yml`
  (Nu.1+Nu.2 + Nu.3 staging + Nu.4 in-job smoke + extended
  `linux-tarball-smoke` / `macos-tarball-smoke`); ~10 LOC
  Python in `mapanare/__main__.py` (Nu.5 refactor); ~25 LOC
  test in `tests/test_native_fallback.py` (Nu.5 parametrized
  case); ~15 LOC docs (README + CLAUDE). Aggregate state
  entering v5.34.0: 0 HIGH / 2 MEDIUM (Tn.1 — 5-release
  overdue, escalates to HIGH per v5.32.0 directive; macOS
  notarization, new from Nu.2 ad-hoc-signing shortcut) /
  ~6 LOW (deferred Linux aarch64 + macOS x86_64 tarballs
  added). Cadence unchanged: next routine panel still due
  v5.33.0 cadence-gap-acknowledged at v5.34.0 if not
  bundled. See
  `docs/roadmap/v5/v5.33.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.32.0** (ready, not tagged) — **Nw.2 + Nw.3 + Nw.4 + Nw.5
  + Nw.6 — ship native `mnc.exe` in the Windows SDK ZIP.**
  Closes the structural "Python is the front door on Windows
  release installs" problem that v5.31.0 only papered over.
  v5.12.0 shipped the *toolchain* bundle (`sdk\bin\clang.exe` —
  LLVM-MinGW). v5.32.0 ships the *frontend* bundle: `mnc.exe`
  in `mapanare-${V}-win-x64-sdk.zip` and `-minimal.zip` is now
  the native compiler binary, not a PyInstaller copy of
  `mapanare.exe`. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage
  fixed point preserved by construction at v5.31.0's **241,898
  lines / 0 diff** (27-release strict streak from the v5.7.1
  baseline). Goldens **95/95**. After this release a fresh
  Windows SDK install never invokes Python for `mnc --version`,
  `mnc run`, or `mnc build`. **Nw.1 deviation from PROMPT:**
  PROMPT recommended approach (a) cross-compile from Linux CI
  via `clang --target=x86_64-w64-mingw32`. v5.32.0 uses
  approach (b) — reuses the existing `build-native` Windows
  job's `mnc-win-x64.exe` artifact (full stage1 → stage2
  self-compile cycle on a `windows-latest` runner via w64devkit
  MinGW). Reasons: PROMPT explicitly allows fallback to (b)
  "if cross-compile produces ABI mismatches" — doing (b)
  directly avoids a discovery cycle; existing path is validated
  across 30+ releases and runs the full self-compile cycle
  (stronger Win64-ABI validation than cross-compile);
  smaller diff — no third Windows-build code path. Trade-off:
  ~5-10 min of serial CI on the Windows publish path
  (`build-cli` now `needs: [release, build-native]`).
  Cross-compile remains available for v5.33.0+ when Linux /
  macOS native-frontend bundling motivates a unified job.
  **Nw.2** publish.yml wiring: `build-native` Windows path
  uploads `mnc-win-x64.exe` as the `mnc-windows-x64-native`
  workflow artifact (in addition to the existing GitHub
  Release upload). `build-cli` Windows path downloads it and
  stages as `dist/mapanare/mnc.exe` with two guards:
  MZ-header check (PE32+ DOS-stub `0x4D 0x5A`) and 20 MB size
  ceiling (native is ~3-4 MB; PyInstaller copy is ~30 MB —
  20 MB reliably distinguishes). Replaces the pre-v5.32.0
  `Copy-Item dist/mapanare/mapanare.exe dist/mapanare/mnc.exe`
  alias-shape. **Nw.3** native-binary fallback wrapper:
  `mapanare/__main__.py` rewritten with a 25-LOC preamble
  that detects a sibling `bin/mnc[.exe]` and `os.execv`s to
  it. `MAPANARE_FORCE_PYTHON=1` opts out for dev/debug. Also
  fixes a pre-v5.32.0 bug where `cli.main()` ran at module-
  import time (no `if __name__ == "__main__":` guard) — pytest
  collection of the new fallback tests would have hit
  argparse `SystemExit` otherwise. New
  `tests/test_native_fallback.py` (3 cases) locks the
  detection logic and the env-var bypass. **Nw.4** smoke gate:
  augmented existing `Clean Windows SDK smoke before archiving`
  (in build-cli) and `windows-sdk-smoke` (post-publish, on
  the published ZIP) with three new gates — MZ-header +
  size-ceiling check on `mnc.exe`; version-string match
  against `VERSION`; no-new-Python-process assertion across
  the `--version` call (snapshots `Get-Process | Where-Object
  { $_.Name -match '^python' }` count before / after). The
  no-Python assertion is the load-bearing one — that's the
  specific anti-pattern v5.32.0 closes. **Nw.5** minimal ZIP
  also ships native `mnc.exe` automatically — minimal-ZIP
  staging archives `dist/mapanare/` *after* Nw.2 staging has
  swapped the binary, so no separate code path needed.
  **Nw.6** docs: CLAUDE.md Native-First Philosophy section
  gains a paragraph; README.md install section calls out the
  v5.32.0+ native shipping; CHANGELOG.md `## [5.32.0]` filled
  in with full Nw.\* details + the deviation note;
  `check_changelog_honesty.py` GREEN. **Layout decision:**
  PROMPT specified `bin\mnc.exe`; v5.32.0 keeps `mnc.exe`
  at the bundle root because the bundled SDK lives at
  `sdk/bin/clang.exe` (not `bin/sdk/bin/clang.exe`) — PROMPT's
  layout assumption didn't match v5.12.0's existing structure.
  Aggregate state entering v5.33.0: 0 HIGH / 1 MEDIUM (Tn.1,
  4-release overdue; v5.32.0 deferred to keep scope tight;
  escalates to HIGH at v5.33.0 per v5.31.0 cadence note) /
  ~5 LOW. Cadence unchanged: next routine panel still due
  v5.33.0. See
  `docs/roadmap/v5/v5.32.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.31.0** (ready, not tagged) — **Bn.1 + Bn.2 + Bn.3 +
  Bn.4 + Bn.5 — banner hotfix; kill the "[dev mode]" lie.**
  Pure UX hotfix. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage
  fixed point preserved by construction at v5.30.0's
  **241,898 lines / 0 diff** (26-release strict streak from
  the v5.7.1 baseline). Goldens **95/95**. Closes the
  publish-run-#50-shaped report where a fresh Windows SDK
  install ran `mnc --version` and got `[dev mode] Using
  Python bootstrap compiler. For native speed: mnc run
  <file.mn>` printed before the version string — three
  things wrong: "[dev mode]" was a lie on a release install,
  "for native speed: mnc run <file.mn>" was incoherent on a
  metadata command, and the banner fired unconditionally
  before argparse ran. The Python bootstrap was fine — it
  just announced itself wrong. **Bn.1**: new
  `_should_show_dev_banner(argv)` argv-peek in
  `mapanare/cli.py::main` skips the banner when the first
  non-flag token is in `NO_BANNER_COMMANDS = frozenset({
  "--version", "--help", "-h", "init", "list"})`; honest-
  default policy is "when in doubt, don't fire". **Bn.2**:
  new `_is_release_install()` helper (`@lru_cache(1)`):
  primary signal is `MAPANARE_RELEASE=1` env var; fallback
  is the absence of `pyproject.toml` + `.git` directory at
  the repo root (the parent of `mapanare/`). Release
  installs never see the banner. **Bn.3**: dev-clone
  banner reworded to honestly describe the situation:
  `[mapanare dev] running from source clone (.../mapanare/
  cli.py). Set MAPANARE_RELEASE=1 or install via the SDK to
  silence.` Path embedded so a developer with multiple
  checkouts can tell which one they're hitting. Misleading
  "for native speed: mnc run <file.mn>" suggestion removed.
  **Bn.4**: new `tests/test_cli_banner.py` (5 cases) locks
  all four matrix cells {dev clone, release install} ×
  {metadata cmd, compile cmd} plus the new wording.
  Falsifiability: removing either gate in `cli.py`
  reproduces the publish-run-#50 anti-pattern. **Bn.5**:
  `packaging/pyinstaller-entry.py::main()` calls
  `os.environ.setdefault("MAPANARE_RELEASE", "1")` before
  importing `mapanare.cli`. Single edit covers Linux
  tarball, macOS bundle, and Windows SDK ZIP — every
  release platform ships via the PyInstaller bundle so all
  inherit the env var. The Bash shim
  (`packaging/mapanare-shim.sh`) `exec`s the bundled
  binary directly so the env var set inside the entry
  point is the process's own env. `setdefault` (not
  unconditional set) means a user who explicitly unsets
  `MAPANARE_RELEASE` for testing can still trigger the
  path-heuristic fallback. **v5.31.0 ≠ v5.32.0** — the
  native `mnc.exe` shipping work (which makes the Python
  path *unused* on release installs, not just *quiet*)
  is v5.32.0. Source delta: ~115 LOC of behavior change
  across 3 files (`cli.py` +37/-5, new
  `test_cli_banner.py` +75, `pyinstaller-entry.py` +9/-1)
  — well under PLAN's 50–80 LOC target with the test file
  the bulk of the new code. **Lesson captured for future
  bump-only releases**: rebuild stage1 via
  `python3 scripts/build_stage1.py` between
  `bump_version.py` and `verify_fixed_point.sh` — first
  fixed-point run after the bump showed a spurious 4-line
  VERSION-placeholder NEAR diff (`!0 = !{!"5.30.0"}` vs
  `!0 = !{!"5.31.0"}`) because cached stage1 still
  embedded pre-bump VERSION; rebuild restored STRICT.
  Aggregate state entering v5.32.0: 0 HIGH / 1 MEDIUM
  (Tn.1 still 3-release overdue; bumped from "overdue"
  toward "escalate to HIGH at v5.33.0 if not landed";
  deliberately deferred to keep v5.31.0 scope tight) /
  ~5 LOW. Cadence unchanged: next routine panel still
  due v5.33.0. See
  `docs/roadmap/v5/v5.31.0/{PLAN.md, SESSION_REPORT.md}`.

- **v5.30.0** (ready, not tagged) — **Vb.\* — packaging-only
  release: version bump.** **Zero compiler edits. Zero runtime
  edits. Zero `mapanare/self/*.mn` source edits.** Strict
  3-stage fixed point preserved by construction at v5.29.0's
  **241,898 lines / 0 diff** (25-release strict streak from
  the v5.7.1 baseline). Goldens **95/95**. Advances the
  published version surface (VERSION, README badges in
  en/es/pt/zh-CN, CHANGELOG.md) so the next `dev` → `main`
  merge carries a clean v5.30.0 number; the substantive
  deliverable is the refreshed PR description covering
  v5.13.0 → v5.30.0 cumulative scope (currently `main` is
  stuck at v5.13.0). All real fix / feature work shipped at
  v5.29.0 (Mb.10 self-host emitter routing for
  `__mn_indent_to_braces` Win64 ABI; Pv.7 / Pv.8 already on
  `dev` pre-v5.29.0). NO seed refresh required (no C-runtime
  export changes — no `.mn` source touches the C side at
  all). `make ci-gates` GREEN (9 sub-gates); `make lint`
  clean. See `docs/roadmap/v5/v5.30.0/{PLAN.md,
  SESSION_REPORT.md, PR_BODY.md}`.

- **v5.29.0** (ready, not tagged) — **Mb.10 + Pv.7 + Pv.8 —
  Win64 ABI closeout + CI race prevention.** Three findings,
  three fixes, one release. Reopens the **Mb.\*** arc (declared
  closed at v5.26.1) for one residual Win64 ABI gap and closes
  it **structurally** this time. **Strict 3-stage fixed point
  preserved by construction at 241,898 lines / 0 diff** (24-
  release strict streak; restored from v5.28.0's NEAR — the
  prior NEAR was a v5.9.0 DX.2 artifact from a stale stage1
  binary linked against a v5.27.0-vintage runtime, not actual
  divergence). Goldens **95/95**. **Mb.10**: closes
  publish-run-#50 Windows SIGSEGV in `__mn_indent_to_braces`.
  Sister fix to v5.26.0 Mb.9 (which routed the brace-deprecation
  siblings `__mn_count_user_brace_block_openers` and
  `__mn_emit_brace_deprecation_warning` but missed the parent
  function with the same Win64 ABI shape). Pre-fix mechanism:
  `emit_mir_call`'s user-call fallthrough uses the 64-byte
  `is_byref_type_st` threshold for arg classification; `MnString`
  is 16 bytes, so on Win64 the call site emitted the struct by
  value while `declare_runtime_fn` already declared the function
  with `ptr` parameter via `win64_rewrite_decl_params` (8-byte
  threshold). gcc lowered `MnString source` per Win64 ABI as
  pass-by-hidden-pointer with rcx pointing into the struct's
  data buffer instead of into a valid `MnString` — SIGSEGV on
  the first `source.len` read. The Python emitter has had this
  routing since v5.23.1 Mb.1 (`emit_llvm_text.py:3632`); the
  self-host side was missed. The Mb.9 Python comment at
  `mapanare/self/emit_llvm.mn:3778` even names the missing
  routing as the pattern Mb.9 mirrored — but Mb.9's author only
  added the routing for the brace-deprecation pair, not for the
  parent function. Bug stayed latent because Linux/macOS publish
  jobs hide the mismatch via SysV register-passing, and Windows
  publish wasn't reaching the stage2-self-compile step for
  v5.23.1 → v5.27.0 (failing earlier on other things). v5.28.0
  RE-PANEL did not surface Mb.10 (test gap; covered by Tn.1
  panel rec). 3-LOC fix in `mapanare/self/emit_llvm.mn` (12-line
  block including explanatory comment) inserted after the Mb.9
  brace-deprecation routing at line 3786, mirroring the same
  shape — only the return type differs (`llvm_string()` i.e.
  `{ptr, i64}` MnString here, vs `"i64"` for the counter).
  `emit_rt_call` uses `win64_sarg_rewrite_args` (8-byte
  threshold matching `win64_rewrite_decl_params`), producing
  the correct `sret+sarg` shape on Win64 and a no-op on Linux
  SysV. **Mb.10.C** new
  `tests/llvm/test_indent_to_braces_win64_abi.py` (6 cases
  mirrors v5.26.0 Mb.9.C's `test_brace_funcs_windows_abi.py`):
  3 IR-shape gates under Win64 triple via the Python emitter
  (load-bearing); 1 SysV negative gate pinning the by-value
  shape so future emitter refactors don't accidentally rewrite
  it; 3 ctypes contract cases against
  `runtime/native/mapanare_core.c` for runtime-side correctness.
  Falsifiability round-trip verified — reverting the v5.23.1
  Python handler triggers the IR-shape gate failure exactly
  matching the publish-run-#50 anti-pattern (`call ... ({ptr,
  i64} %l.0)`). **Bb.\* seed refresh: NOT required** (no
  C-runtime export changes; the v5.10.0-vintage seed has no
  view of how `mnc-stage1` emits the call). **Pv.7**: closes
  `clean-build-test` race against parallel `pytest -n auto`
  workers. Pre-fix, the `rm -f libmapanare_rt.a && make
  build-rt` sequence in `clean-build-test` left a 1-3 second
  window where the canonical archive was missing; surfaced as
  flake on `tests/bootstrap/test_chained_cmp_mirror.py`
  (gw0 hit the race window). **Already shipped on dev as
  commit `bc3bc7b`** between v5.28.0 and v5.29.0. Fix
  parameterizes `build-rt` with `RT_OUTPUT ?=
  runtime/native/libmapanare_rt.a`, rebuilds into a sandbox
  path on the same filesystem (`runtime/native/.libmapanare_rt
  .cbt-tmp.a`), then atomic `mv -f` into the canonical path.
  Race-window evidence captured in v5.29.0 SESSION_REPORT:
  200-poll watcher at 20 ms cadence over the full 4-second
  rebuild produced **0 MISSING reports**. **Pv.8**: closes
  agent-state timing races in `tests/native/test_c_runtime.c`'s
  `test_agent_pause_resume` (`:712`) and
  `test_agent_failing_handler` (`:738`). `mapanare_agent_pause()`
  is a guarded transition that silently no-ops if the agent
  isn't yet RUNNING; the worker thread sets state=RUNNING only
  after the OS schedules the new thread, and the test's fixed
  `usleep(50000)` was sometimes insufficient under CI load.
  **Already shipped on dev as commit `f119c43`** between
  v5.28.0 and v5.29.0 (the PROMPT/PLAN were drafted assuming
  the fix was uncommitted; verified at Phase 0 that it had
  landed cleanly). Fix adds 4 polling helpers
  (`wait_for_agent_state`, `wait_for_messages_processed`,
  `wait_for_agent_recv`, `wait_for_counter` + `test_sleep_ms`)
  plus 7 fixed-delay sleeps converted to bounded polls
  (`test_agent_lifecycle`, `test_agent_send_recv`,
  `test_agent_pause_resume`, `test_agent_failing_handler`,
  `test_agent_metrics`, `test_shutdown_with_agents`,
  `test_pool_basic` + `test_pool_saturation`). Generous
  timeouts (1000 ms for state, 2000 ms for FAILED /
  messages-processed, 5000 ms for 500-task pool stress) —
  returns on first match; only consumes the full budget if the
  worker is genuinely stuck. Plain + ASan + TSan all green
  (3/3); `gcc -O2 -g -pthread -Wall -Wextra -Werror` clean.
  Pv.8.B (preemptive sweep of 11 same-shape sites in
  `tests/native/test_agent_scheduler.py`) **deferred** to
  v5.30.0+ if a flake materializes; reactive-only fix
  discipline preserved. **Mb.\* arc CLOSED structurally** —
  v5.26.0's "Mb.\* arc CLOSED" claim was strictly correct for
  Mb.7+Mb.9 but missed `__mn_indent_to_braces`; v5.29.0 closes
  the arc for real. Aggregate state entering v5.30.0: 0 HIGH /
  1 MEDIUM (Tn.1 escalated per v5.28.0 panel directive — not
  picked up here, deliberately deferred to keep Mb.10 scope
  tight) / ~5 LOW. Cadence unchanged: next routine panel still
  due v5.33.0. See `docs/roadmap/v5/v5.29.0/{SESSION_REPORT.md,
  PLAN.md, AUDIT.md}`.

- **v5.28.0** (ready, not tagged) — **RE-PANEL — v5.23.0 →
  v5.27.0 recovery + prevention + arc-closeout arc graded.**
  Panel-only release. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage fixed
  point preserved by construction at v5.27.0's 241,842 lines / 0
  diff. 7 reviewers graded the v5.23.0 → v5.27.0 arc (8 releases,
  9 SESSION_REPORTs) using the v5-gate mechanical decision rule.
  **Aggregate: 9.72 / 10. Decision: Option A.** Fourth
  consecutive Option A under the v5-gate framework, **largest
  single-arc recovery in v5 history (+0.31 vs v5.22.0's 9.41
  floor)**, and **first panel above the v5.7.1 / v5.8.0 9.66
  ceiling in the v5 series**. Score trajectory: 9.66 → 9.62 →
  9.41 → **9.72** — 3-consecutive-panel downward trend (-0.04,
  -0.21) broken with +0.31. **Per-reviewer:** Rattler 9.90
  (+0.05), Viper 9.80 (+0.10), **Anaconda 9.60 (+1.20 — load-
  bearing recovery; the v5.22.0 -1.30 dock was driven by 3
  silently-RED CI gates that v5.23.0 RC.\* + v5.24.0 Hy.\* +
  v5.25.0 Pv.\* closed structurally, not symptomatically)**,
  Cobra 9.70 (+0.15), Coral 9.70 (+0.15), **Boa 9.55 (+0.55 —
  largest single-panel Boa improvement in project history;
  Bo.18r 3-consecutive-panel persistence finally structurally
  closed)**, Mamba 9.80 (-0.05). 7 EXCEEDS / 0 MEETS / 0 NEEDS
  WORK; 7 PASS WITH NOTES. **0 NEW HIGH, 0 NEW MEDIUM, ~14 NEW
  LOW** (mostly process polish). **v5.22.0 docket: 25/25 items
  CLOSED at v5.28.0 HEAD** (highest closure rate in v5 history
  across a single recovery arc). Mb.\* / Mc.\* / Eu.\* arcs all
  CLOSED entering this panel; 4 prev-LINK_FAIL goldens
  (47/48/49/51) flipped to PASS via Eu.1..Eu.4. **Phase 2 H.\*
  hygiene closures** (committed `069ff24` ahead of panel cut,
  per Bo.27 / Wd.8 cross-reference convention codified at
  `.reviews/PANEL_AUDIT_TEMPLATE.md`): H.1/H.2/H.3 (Bo.18r-class)
  README.md fixed-point status paragraphs at lines 175 / 183 /
  196-197 bumped to v5.27.0 / 241k / 23 consecutive releases;
  H.4 (Bo.17r-class) 3 localized READMEs (es/pt/zh-CN) native-
  compiler subsection rewritten with v5.23-v5.27 arc summary;
  H.5 (Bo.10-class) `docs/known_issues.md` Last-updated bumped;
  H.6 (An.1-class) `.reviews/CARRY_FORWARD.md` v5.25-v5.27
  closure rows appended (4-release update-protocol drift caught
  + fixed); H.7 cadence-gap acknowledgment in PROMPT.md +
  PRE_PANEL_AUDIT.md preambles. **Cadence-gap closure 1 minor
  late on purpose** — v5.24.0 Hy.3 cadence-enforcement gate
  fired hard at v5.27.0 (5+ minor threshold); v5.28.0 closes
  the gap because bundling formatter polish (Mc.8+Mc.9+Tk.1)
  with a panel cycle was rejected during v5.27.0 PLAN drafting.
  Two reviewers (Anaconda, Coral) independently judged the
  framing honest. **Convergent recommendation (Cobra Cb.New1 +
  Rattler Ra.Inf1 — independent reviewers, same finding shape)**:
  extend `tests/llvm/test_async_link.py` link-and-run pattern
  to all 95 goldens via new `test_llvm_link_all.py` (Tn.\*
  generalization). Closes the structural gap that hid Eu.1..Eu.4
  for 3 releases. **Escalate to MEDIUM at v5.29.0 if not picked
  up in a Pv.\* follow-on.** Other LOW recommendations: M.1
  (Mamba — `.h` vs `.c` header asymmetry recurrence; Pv.7-style
  structural gate); A.1 (Anaconda — new
  `check_carry_forward_freshness.py` gate); Ra.New1 (Rattler —
  Stage2 teardown narrowed to stdout-redirect-specific SIGSEGV;
  investigation tractable, consider closing in v5.29.0 rather
  than v6.0). **Cadence reset:** next routine panel due v5.33.0.
  See `.reviews/v5.28.0/{README.md, V5_DECISION.md, PRE_PANEL_AUDIT.md}`,
  7× `<reviewer>/findings.md`, and
  `docs/roadmap/v5/v5.28.0/SESSION_REPORT.md`.

- **v5.27.0** (ready, not tagged) — **Mc.8 + Mc.9 + Tk.1 —
  formatter polish; Mc.\* parity arc CLOSED.** Three formatter /
  rewriter polish items shipping together because they all live
  in `mapanare/format.py` and ship without compiler edits. Closes
  the v5.13.0 Mc.\* parity gap docket (Mc.8 + Mc.9, 12-release
  carry each) and the v5.24.1 Wd.2 latent rewriter bug (Tk.1,
  3-release carry). **Strict 3-stage fixed point preserved by
  construction at 241,842 lines / 0 diff** (23-release strict
  streak — same line count as v5.26.1 because zero
  `mapanare/self/*.mn` source edits in v5.27.0; the existing
  argv-forwarding loop in `main.mn` carries the new flags through
  the native dispatch unchanged). Goldens **95/95**. **Mc.8**
  (`mapanare fmt --line-length N`): **detect-only** long-line
  reporter. Phase 0 surfaced that Mapanare's grammar is strictly
  single-line for all expressions — newlines are not implicit
  continuations inside `(`/`[`/`{`/`#{` — so an auto-wrap
  rewriter cannot satisfy the v5.13.0 Mc.2 AST-preservation
  invariant. Pure read-only scan; never modifies source; default
  mode reports overlong lines on stderr; under `--check` causes a
  non-zero exit so CI gates can enforce the ceiling; `N=0` (the
  default) disables the check. Auto-wrap rescoped to a future
  release that also adds newline-tolerant grammar inside grouping
  delimiters. **Mc.9** (`mapanare fmt --sort-imports`): sorts
  contiguous top-level `import` blocks alphabetically. Block
  boundaries are any non-import line (blank, comment, or other
  statement), so the user's existing groupings (e.g. stdlib /
  third-party / local separated by blanks) function as the
  de-facto group structure: each group sorts independently.
  Comments inside an import block split the surrounding block
  into sub-blocks — neither side reorders across the comment.
  Idempotent. AST-preserving up to `ImportDecl` declaration
  order; load-bearing corpus check sorts the 8-import block in
  `mapanare/self/main.mn` and asserts `ImportDecl` multiset
  preservation. **Tk.1** (`to_terse` empty `#{}` rewriter bug):
  surgical 6-LOC fix in `mapanare/format.py::to_terse` —
  `endswith("{}")` branch now applies the same
  `_looks_like_stmt_block_opener` filter the `endswith(" {")`
  branch relies on via `_find_match_verbatim_lines`, so
  expression-context empty literals (`let m: Map<String, Int> =
  #{}`, `let p = Point {}`) survive verbatim instead of
  collapsing to grammatically invalid `... = #:` + indented
  `pass`. v5.24.1 Wd.2 sidestepped this latent bug by leaving
  SPEC §17.1 unrewritten; with Tk.1 fixed, `to_terse_markdown
  (SPEC.md)` is now safe to run end-to-end. Falsifiability
  round-trip verified: 3 unit tests (`test_to_terse_preserves_
  empty_map_literal`, `test_to_terse_empty_map_literal_idempotent`,
  `test_to_terse_preserves_empty_struct_literal`) all fail on
  pre-fix `format.py` with the exact pre-fix bug shape; all 3
  pass after the fix. **Source delta:** Python only —
  `mapanare/format.py` ~95 LOC (Tk.1 ~6 + `find_long_lines` ~30
  + `sort_imports` ~50 + `__all__`); `mapanare/cli.py` ~30 LOC
  (argparse + per-file detector wiring); 4 new test files /
  extensions (~525 LOC tests, 47 new test cases); ~90 LOC docs
  in `docs/guides/formatter.md`. **Cadence-gate hard fire**:
  `scripts/check_cadence.py` fires hard at v5.27.0 HEAD (5+
  minor versions since v5.22.0 panel). **Acknowledged and
  informational** — the v5.28.0 RE-PANEL closes the cadence gap
  one minor late on purpose; bundling formatter polish with a
  panel cycle was rejected during PLAN drafting (formatter work
  is the wrong scope to mix with a panel review cycle).
  **Mc.\* parity arc CLOSED** — every Mc.\* item from the
  v5.13.0 parity gap docket is now resolved. See
  `docs/roadmap/v5/v5.27.0/SESSION_REPORT.md` and `PLAN.md`.

- **v5.26.1** (ready, not tagged) — **Eu.1..Eu.4 — close
  v5.26.0-deferred LINK_FAIL bug classes; Eu.\* arc closeout.**
  Four small-but-distinct codegen / lowering fixes that move
  goldens 47, 48, 49, 51 from LINK_FAIL → PASS. Each was a
  pre-existing latent bug surfaced by v5.26.0's Phase 0 audit
  and tracked as `xfail(strict)` in
  `tests/llvm/test_async_link.py`. Per-bug Phase 0 investigations
  honored — bundled in one release for efficiency, not conflated
  (mirrors v5.26.0 Mb.7/Mb.9 split discipline). **Strict 3-stage
  fixed point preserved at 241,842 lines / 0 diff** (22-release
  strict streak; +1,849 lines vs v5.26.0's 239,993 from the new
  lowerer/emitter arms). Goldens **95/95**.
  `tests/llvm/test_async_link.py` 10/10 PASS, 0 XFAIL.
  **Eu.1**: `emit_unwrap` on `Result<T, E>` did one
  `extractvalue ..., 1` returning the inner aggregate `{Ok_ty,
  Err_ty}` rather than the Ok payload at field 0 of that inner
  aggregate. Fixed at both `mapanare/emit_llvm_text.py::_do_unwrap`
  and `mapanare/self/emit_llvm.mn::emit_unwrap` — for `TK_RESULT`
  subjects, do TWO `extractvalue` ops. Closes golden 47 (`?`
  operator on Result). **Eu.2**: standalone `Ok(...)` / `Err(...)`
  literals at call-arg sites (e.g., `classify(Ok(42))` from
  `main`) lowered with empty `dest.ty.args` because the caller
  wasn't a Result-returning fn — `emit_wrap_ok` then derived the
  outer wrapper type from `resolve_mir_type` (fallback `{i1, {ptr,
  ptr}}`) while the inner aggregate used real Ok/Err widths
  (`{i64, ptr}`) — three disagreeing `insertvalue` widths in one
  chain. Fixed at `mapanare/self/lower.mn` Ok/Err lowering to
  default missing args mirroring `mapanare/lower.py:2398`
  (`Result<T, String>` for `Ok(T)` and `Result<Int, T>` for
  `Err(T)`). Closes golden 48. **Eu.3**: `match` on a primitive
  (Int / Bool / String) subject emitted `EnumTag` which lowered
  to `extractvalue i64 %v, 0` — LLVM rejects (i64 is not
  aggregate). Fixed at `mapanare/self/lower.mn::lower_match`:
  primitive subjects bypass the switch entirely and emit a
  sequential test cascade — jump to `arm[0]`; arms with literal
  patterns gain an implicit `subject == LIT` check at entry; the
  existing v4.79.0 P3 guard fall-through is preserved. Also
  `bind_ident_pattern` uniquifies its alloca SSA name with
  `tmp_counter` (mirrors `bind_one_pattern_field`'s pattern) so
  multiple `Some(x) if guard` arms don't collide on `%x.addr`
  under cascade dispatch. Closes golden 49. **Eu.4**: `match`
  with or-pattern + guards (e.g., `Some(0) | None | Some(x) if g
  | ...`) emitted N duplicate `i64 1` switch cases — LLVM rejects
  "duplicate case value in switch". Fixed via two coordinated
  changes in `mapanare/self/lower.mn`: (1) `build_match_arms`
  dedups switch entries by tag value (first arm wins; subsequent
  same-tag arms remain reachable through fall-through), default
  label set once (wildcard wins over earlier ident-non-enum); and
  (2) or-pattern arms with a literal-bearing alt emit a per-alt
  entry switch at the arm body — constructor alts with no payload
  (e.g., `None`) → direct match; constructor alts with literal
  sub-args (e.g., `Some(0)`) → payload-check block; default →
  next arm. New helper `is_builtin_variant_name` recognises
  `None`/`Some`/`Ok`/`Err` as variants when they appear as
  `IdentPat` (the parser does not wrap them in `ConstructorPat`).
  Closes golden 51. **Bb.\* — no seed refresh** (no C-runtime
  call shape changes). **Eu.\* arc CLOSED** — every v5.23.1 →
  v5.26.0 LINK_FAIL bug class is now a regression-locked PASS
  via `tests/llvm/test_async_link.py::test_deferred_link_failures`
  (10/10 PASS at HEAD; the four `pytest.xfail` short-circuits
  were removed). Source delta: ~17 LOC Python + ~14 LOC self-host
  (Eu.1) + ~10 LOC self-host (Eu.2) + ~95 LOC self-host (Eu.3) +
  ~150 LOC self-host (Eu.4) = ~286 LOC total (above the per-fix
  30-LOC ceiling but kept in scope to close the arc structurally;
  alternative was four small releases over 1–2 weeks).
  See `docs/roadmap/v5/v5.26.1/SESSION_REPORT.md` and `AUDIT.md`.

- **v5.26.0** (ready, not tagged) — **Mb.7 + Mb.9 — codegen +
  Win64 ABI fixes; Mb.\* arc closeout.** Two real codegen fixes
  in the same release. Mb.7 closes the 3-release carry (v5.23.1
  → v5.24.0 → v5.25.0) of the i64/i1 tag-emit bug in
  `mapanare/self/emit_llvm.mn::emit_enum_tag`: the function
  zexted Result/Option i1 tags to i64 unconditionally, but the
  try-operator path declared its dest as `mir_bool()` (i1) and
  consumed it in `Branch`, producing invalid `br i1 %i64_val`.
  Surgical 5-LOC fix — honors `dest.ty.kind`: emit i1 directly
  for `TK_BOOL` consumers (try-op), keep zext for `TK_RESULT`/
  `TK_OPTION`/`TK_ENUM` (match → `switch i64`). Mb.9 closes the
  publish-run-#48 Windows OOM in the v5.23.2 Te.3.B.2 functions
  `__mn_count_user_brace_block_openers` and
  `__mn_emit_brace_deprecation_warning`: Python's `_do_call`
  uses a 64-byte byref threshold but `_decl_fn` uses 8 bytes on
  Win64 — the 16-byte `MnString` was passed by-value at the
  call site while the declaration said `ptr`, and gcc's Win64
  pass-by-hidden-pointer semantics for `MnString source` then
  read the data buffer's bytes 8..16 as the length. For
  `mnc_all.mn` (`// Auto-generated:`) those bytes are
  `g e n e r a t e` → `0x65746172656e6567` → `malloc(7e+18)` →
  OOM. Fixed via explicit handlers in Python's `_do_call` AND
  self-host's `emit_mir_call` routing both functions through
  the runtime-call path (mirrors the v5.23.1 Mb.1 pattern for
  `__mn_indent_to_braces`). **No C-runtime edits**; the C side
  was always correct. **No Bb.\* seed refresh** (no call shapes
  change); this corrects the PLAN. **Phase 0 disclosure** — the
  v5.23.1 SESSION_REPORT premise ("9 LINK_FAIL goldens share
  one bug") was wrong: only golden 47 had Mb.7's bug; goldens
  55-59 (the async cluster) never had it (always linked); 47/48/
  49/51 fail for distinct reasons (Eu.1..Eu.4 rescoped to
  v5.26.1). **Strict 3-stage fixed point preserved by
  construction at 239,993 lines / 0 diff** (21-release strict
  streak; +158 lines vs v5.25.0's 239,835 from the new dispatch
  arms). Goldens **95/95**. New `tests/llvm/test_async_link.py`
  (10 tests: 6 PASS + 4 documented xfail) — IR-invariant gate
  for the i64/i1 anti-pattern, link-and-run sanity for the async
  cluster, xfail markers documenting the four v5.26.1-rescoped
  bug classes (XPASS-strict so future fixes auto-flip them).
  New `tests/native/test_brace_funcs_windows_abi.py` (8 PASS)
  — IR-shape gate under forced Win64 triple plus Linux ctypes
  contract proving the C side is correct on SysV. **Mb.\* arc
  CLOSED** — every memory- and ABI-related panel finding
  through v5.22.0 + v5.23.2's Te.3.B.2 follow-on closed. See
  `docs/roadmap/v5/v5.26.0/SESSION_REPORT.md` and `AUDIT.md`.

- **v5.25.0** (ready, not tagged) — **Pv.\* — CI prevention
  infrastructure.** First release in the new **Pv.\*** sub-arc
  (structural pattern parallel to v5.24.0's **Hy.\***). Closes
  the class of failure where a CI-only test path catches a bug
  that could have been caught locally — typically because (a) a
  stale local artifact masks the bug on the developer machine,
  (b) a feature ships without an end-to-end test exercising it
  through the .mn-caller side, or (c) a test asset only runs on a
  non-Windows CI job. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage fixed
  point preserved by construction at **239,835 lines / 0 diff**
  (20-release strict streak; same line count as v5.24.1 because
  no source under `mapanare/self/` changed). Goldens **95/95**.
  **Pv.1**: new `tests/test_runtime_lib_lookup.py` (3 cases)
  locks `mapanare.test_runner._find_runtime_lib()` against
  re-introduction of v3.x-era `libmapanare_core.*` candidate
  names; sweeps stale shadows, asserts canonical name resolution,
  end-to-end links a tiny IR fragment that references
  `__mn_str_eq` against whatever archive the lookup returned.
  Pre-fix (commit `9dcbbb5` shipped on `dev` between v5.24.1 and
  v5.25.0) the lookup silently returned `None` because the
  candidate list still mentioned the v3.x names; a stale local
  `libmapanare_core.so` masked the regression on developer
  machines for 11+ releases. **Pv.2**: new
  `tests/bootstrap/test_preprocess_memcheck.py` (3 parameterized
  cases — brace-only, colon-only, mixed) runs `mnc-stage1
  preprocess` under valgrind. Locks the
  `__mn_indent_to_braces` brace-only fast-path against
  MnString-aliasing regressions; pre-fix the fast path returned
  the input MnString aliased and produced a double-free at
  function-end drop glue. Mirrors v5.23.1 Mb.3's grep-for-symbol
  pattern rather than `--error-exitcode=1` because `mnc-stage1`
  has a pre-existing single-shot leak from `__mn_argv` (~71 bytes,
  known and tracked since v5.23.1) that would otherwise produce a
  100% noise floor. **Pv.3**: extended `make ci-gates` (v5.24.0
  Hy.1) with new `clean-build-test` sub-gate — 9 sub-gates total,
  up from 8. Removes
  `runtime/native/libmapanare_*.{a,so,dylib,dll}` (the explicit
  `rm -f` is what makes the rebuild meaningful — `make clean`
  alone does not touch the archive), runs `make build-rt`, then
  runs `pytest tests/test_at_test_runtime.py
  tests/test_runtime_lib_lookup.py`. Catches the runtime-archive
  rename / relocation class structurally before any PR lands.
  **Pv.4**: new `scripts/validate_wsl.sh` runs the Linux pytest
  path end-to-end (`make build-rt` + `python3
  scripts/build_stage1.py` + `pytest tests/ -x -n auto`) from any
  CWD by resolving the repo root from the script's own location.
  New `dev.ps1 validate-wsl` mode shells out via `wsl -d Ubuntu`
  so a Windows host can produce the Linux pytest signal without
  leaving the dev loop. Optional pre-push hook at
  `scripts/hooks/pre-push.sample` (commented opt-in; not enabled
  by default — forcing the full suite on every push kills the dev
  loop and produces resentment, not safety). **Pv.5**: removed
  the v5.13.1 entry from CLAUDE.md "Planned / in-progress"
  section. The runtime-lib wiring (At.1's only remaining open
  item) shipped on `dev` between v5.24.1 and v5.25.0; the `@test`
  runtime is fully functional end-to-end. **Pv.6**: closes
  publish run #48 Linux + macOS tarball-smoke job failures.
  `.github/workflows/publish.yml` Linux + macOS smoke fixtures
  rewritten from `echo 'fn main(): print("...")' > /tmp/hello.mn`
  (single-line `fn x(): y` was the v5.14.0 SPEC §1009 forward
  promise that v5.21.1 H.4 explicitly rescoped to v6.0 — fixture
  authored against an unshipped feature) to multi-line colon via
  `printf 'fn main():\n    print(...)\n'`. New
  `tests/test_publish_smoke_fixtures.py` (2 cases) extracts every
  inline `.mn` fixture across four shapes (bash echo, bash
  printf, PowerShell here-string, bash heredoc) and parses each
  through `mapanare.parser.parse`; first test guards against a
  regex update silently dropping every fixture. **5 fixtures
  locked at v5.25.0 HEAD**. **Falsifiability**: every Pv.\* test
  documents a revert-and-restore round-trip in its module
  docstring; verified red-then-green for Pv.1 / Pv.2 / Pv.6 in
  the release session. **Out of scope** (held): Mb.7 (i64/i1
  tag-emit, 9 LINK_FAIL goldens) — v5.26.0; `to_terse` empty
  `#{}` rewriter bug — v5.27.0; `mnc fmt` long-line wrap +
  import sort — v5.27.0. See
  `docs/roadmap/v5/v5.25.0/SESSION_REPORT.md` and `PLAN.md`.

> Older release notes elided. See `docs/roadmap/ROADMAP.md` for the
> full ledger and `docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` for any
> specific release.

### Planned / in-progress

- **v5.12.0** — **Mc.6 / Wk.* — Windows SDK split.** Default
  Windows installs move to `mapanare-${V}-win-x64-sdk.zip`, which
  bundles one curated LLVM-MinGW/UCRT x86_64 SDK under `sdk/` so
  clean-machine `mnc run` / `mnc build` keep working. The opt-in
  `mapanare-${V}-win-x64-minimal.zip` is app-only and requires a
  user/system compiler. `MAPANARE_NO_BUNDLED_TOOLCHAIN=1` and legacy
  `MAPANARE_NO_BUNDLED_LLVM=1` select minimal. `toolchain/` must not
  appear in v5.12.0 Windows release ZIPs. See
  `docs/roadmap/v5/v5.12.0/WINDOWS_TOOLCHAIN_AUDIT.md`.

**Terseness arc — v5.13–v5.21 (shipped).** All terseness arc
releases (v5.13.0 → v5.21.0, plus the Sh.\* self-host rewrite at
v5.17.0 → v5.17.2) have shipped. See per-release SESSION_REPORTs
under `docs/roadmap/v5/v5.13.0/` through `docs/roadmap/v5/v5.21.0/`
for details, or `CHANGELOG.md` for summaries. The terseness thesis
is now visible in real code: cumulative source shrink of −13.8%
across `mapanare/self/` from v5.13.0 baseline.

- **v5.19.0** — **Te.3 + Dk.* — closeout.** Soft-deprecate
  `{}` (still parses, emits warning); hard removal scheduled
  for v6.0. Ship `mapanare/builder` + `mapanare/runtime`
  Docker images. See `docs/roadmap/v5/v5.19.0/PLAN.md`.
- **v6.0** — Borrow checker / multi-level alias analysis. Hard
  removal of `{}` (Te.3 from v5.19.0 was soft deprecation only).
  Closes Rt.04 (multi-level drop-glue alias analysis, rescoped
  v5.6.6 — struct→list→string depth-2). The only remaining
  v5.6.x v6.0 carry now that v5.6.12 closed Lk.1 at the
  source via destination passing.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and
`docs/roadmap/v5/PARITY_GAPS.md`.

## Pre-Push Validation (MANDATORY)

Run the full validation suite before any commit/push. Mirrors CI.
Writes results to `error.log`.

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT
.\dev.ps1 validate -Watch  # Validate then watch
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only
.\dev.ps1 fmt              # Auto-format
.\dev.ps1 e2e              # End-to-end tests
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for `examples/wasm/*.mn`
— catches WASM CI failures locally. `pytest` alone is NOT sufficient.

Quick partial checks:

```bash
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
black --check . && ruff check . && mypy mapanare/ runtime/
pytest tests/semantic/test_types.py -v
pytest tests/parser/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v  (add -n auto for parallel)
make lint             # ruff + black + mypy
make fmt              # black + ruff --fix
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches + egg-info
```

### Core workflows

```bash
# Golden test harness (WSL for stage1)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Full rebuild cycle (WSL)
bash scripts/rebuild.sh              # concat + build + goldens

# Self-hosted fixed-point (WSL)
python scripts/build_stage1.py
bash scripts/verify_fixed_point.sh --keep
```

### Debug tooling

Full command reference: **`docs/guides/tools_reference.md`**.

- `python scripts/ir_doctor.py <cmd>` — per-function IR diagnostics,
  baselines, valgrind mapping, stage2 pipeline
- `python scripts/mir_trace.py <file.mn> <fn>` — trace type inference
  in the Python lowerer
- `culebra <cmd>` — 49+ templates for IR + C diagnostics (Rust binary,
  WSL)

## Testing the Native Compiler

Golden corpus at `tests/golden/*.mn` (66 programs). Reference IR at
`tests/golden/*.ref.ll`.

Workflow:
1. Edit `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. `python scripts/build_stage1.py`
3. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. Harness compares mnc-stage1 output against Python bootstrap —
   shows which functions are missing or different.

Every run updates `tests/golden/BENCHMARKS.md`. Commit to track
regressions.

**Current baseline (v5.7.1):** **66/66 — preserved.** Sh.7
(closure-typed parameters) and B (or-pattern + identifier `None`
resolution) both closed in v5.7.0; v5.7.1 is a docs/polish release
with no compiler edits. The closure arc is closed; every test in
the corpus that defines "self-hosting" now passes through
`mnc-stage1`.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I), **MyPy** strict
- Target Python 3.11+ (bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source
  → Lark LALR parser → AST (dataclasses)
  → Semantic checker
  → MIR lowering
  → MIR optimizer (O0–O3)
  → Emitter:
      ├→ emit_llvm_text.py  → LLVM IR (text)
      ├→ emit_c.py          → C source
      └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:

| File | Role |
|---|---|
| `cli.py` | Entry point — command dispatch |
| `parser.py` | Lark transformer: parse tree → AST |
| `ast_nodes.py` | AST node definitions |
| `semantic.py` | Two-pass type checker + scope resolver |
| `mir.py` / `mir_builder.py` | MIR data + builder |
| `lower.py` | AST → MIR lowering |
| `mir_opt.py` | MIR optimizer passes |
| `emit_llvm_text.py` | LLVM IR generation |
| `emit_c.py` | C source generation |
| `emit_wasm.py` | WebAssembly (WAT) generation |
| `wasm_linker.py` | wasm-ld multi-module linking |
| `types.py` | **Single source of truth** for type system |
| `mapanare.lark` | LALR grammar, 13-level precedence |
| `tracing.py` | OpenTelemetry-compatible tracing |
| `diagnostics.py` | Rust-style structured error output |

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`,
`result.py`, `deploy.py`. **Legacy — being replaced by native .mn
stdlib.**

**Native C runtime** (`runtime/native/`): arena memory (no GC),
lock-free SPSC ring buffers, thread pool with work-stealing, coop
scheduler (mobile), agent lifecycle, TCP sockets, TLS (OpenSSL via
dlopen), file I/O, event loop (epoll/select), string interning,
memory profiling. Used by the LLVM backend.

## LLVM Backend Status

**Working:** functions, structs, enums, pattern matching, control
flow, type inference, generics, Result/Option, print, builtins, lists,
maps (Robin Hood), agents, signals (full reactivity), streams,
closures (env struct capture), traits, module imports, pipes,
multi-agent pipe definitions, string methods, GPU kernel dispatch.

**Not yet on LLVM:** tensor reshape, mutable views, stepped slices
(v5.x). Tensor surface stable since v4.45.0.

New LLVM features target `emit_llvm_text.py` (sole LLVM emitter).

## Type System (`mapanare/types.py`)

Single source of truth:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP,
  OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int,
  float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare → Python name mapping for emitters
- `PYTHON_TYPE_MAP`: Type → Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, ~14,000 lines of Mapanare. Mirrors the Python bootstrap:

| Module | ~LOC | Role |
|---|---:|---|
| `ast.mn` | 781 | AST node definitions |
| `lexer.mn` | 575 | Tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser |
| `semantic.mn` | 1,729 | Type checker + scope resolver |
| `mir.mn` | 791 | MIR data structures |
| `lower_state.mn` | 587 | Lowerer state |
| `lower.mn` | 3,602 | AST → MIR lowering |
| `emit_llvm_ir.mn` | 258 | LLVM type constants + IR builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter |
| `main.mn` | 537 | Compiler driver |

**Patterns:** constructor functions (`let r: T = first_field; return
r`), state-threading, no struct literal syntax in grammar yet.

**Fixed-point:** NEAR (stage2.ll == stage3.ll except VERSION
placeholder). Strict hit at v4.134.0; currently NEAR per v5.3.2.

## Key Conventions

- Grammar: `mapanare/mapanare.lark` (bootstrap copy at `bootstrap/`)
- Emitters detect used features (agents/signals/streams) and import
  only as needed
- Builtins dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted sources: `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Manifesto: `docs/manifesto.md` |
  RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs:
  `docs/roadmap/v0/` → `docs/roadmap/v5/`
- Version: `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

- **Stdlib in .mn:** new stdlib modules are `.mn`, compiled via LLVM.
  No more Python `.py` stdlib files.
- **C runtime as foundation:** OS primitives (sockets, TLS, file I/O)
  in C. Everything above (HTTP, JSON, routing) in Mapanare.
- **Test on LLVM:** every test runs on the LLVM backend.
- **Python entrypoint is bootstrap-only on release installs (v5.32.0+).**
  Windows SDK ZIPs ship a real native `mnc.exe` (built from
  `mapanare/self/` via the stage1 → stage2 self-compile cycle).
  **v5.33.0 extends this to Linux x86_64 and macOS arm64 release
  tarballs** — both ship `dist/mapanare/mnc` (native ELF / Mach-O)
  alongside the existing PyInstaller `mapanare` binary. The native
  `mnc` is invoked directly; no Python interpreter starts on
  `mnc --version`, `mnc run`, or `mnc build`. Linux aarch64 + macOS
  x86_64 tarballs are deferred to v5.34.0+ (no native runner /
  cross-compile infrastructure yet). The Python `mapanare`/`mnc`
  console-script remains for clean clones, pip-installs without
  the SDK, and the `bash scripts/build_from_seed.sh` bootstrap
  path. `mapanare/__main__.py` detects a sibling `bin/mnc[.exe]`
  and `os.execv`s to it; `MAPANARE_FORCE_PYTHON=1` opts out for
  dev/debug.

## GPU / WASM / Mobile (v2.0.0)

- **GPU** — CUDA + Vulkan via dlopen; `@gpu`/`@cuda`/`@vulkan`
  annotations; PTX/SPIR-V codegen; `stdlib/gpu/`.
- **WASM** — `mapanare/emit_wasm.py` → WAT, `wasm_linker.py` for
  wasm-ld. Targets: `wasm32-unknown-unknown`, `wasm32-wasi`.
- **Mobile** — `aarch64-apple-ios`, `aarch64-linux-android`,
  `x86_64-linux-android`. Coop scheduler + smaller defaults (4 KB
  arenas, 256-slot rings, 4 K string intern cap).

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame package
  (pandas+numpy replacement), in .mn
- `net/crawl`, `security/scan`, `security/fuzz` — agents-based
- AI/LLM drivers: `stdlib/ai/` (LLM, embeddings, RAG)

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — black → ruff → mypy → pytest. Matrix: Python 3.11/3.12
- **native** — C runtime: gcc, ASan, TSan
- **wasm** — WAT emit → wat2wasm → wasmtime WASI examples
- **android** — NDK cross-compile: ARM64 + x86_64 `.o` + ELF verify

5,400+ tests across the full pipeline.

## Skills (slash commands)

| Skill | Description |
|---|---|
| `/golden` | 15/15 golden suite through mnc-stage1 + llvm-as |
| `/stage2` | Compile self-hosted modules + validate stage2 IR |
| `/rebuild` | concat + build mnc-stage1 + run goldens |
| `/ir-audit` | LLVM IR pathology audit with baselines |
| `/valgrind-map` | Valgrind + auto-map offsets to struct fields |
| `/bump-version` | Bump VERSION, README, CHANGELOG, localized docs |
| `/code-review` | 7-reviewer panel review |
| `/create-pr` | PR title + description from commits |
| `/simplify` | Review + fix changed code |
| `/autoresearch` | Autonomous experiment loop |
| `/culebra-scan` | Culebra v2.4.0 — 49+ templates (ABI / IR / Binary / Bootstrap / C). Workflow guide: `docs/guides/culebra.md` |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (31250 symbols, 66124 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
