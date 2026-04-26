# v5.8.2 — Windows release pipeline hardening

**Status:** PLANNED
**Breaking:** No (Windows-only behavior changes; Linux / macOS unaffected)
**Prerequisite:** v5.8.1 shipped (or partially shipped — the v5.8.1
release run failed on both Windows publish jobs; v5.8.2 fixes the
underlying causes and re-runs)
**Estimated work:** 1 hour (2 small source edits + version bump +
release re-run)

---

## Goal

Make the v5.x release pipeline land green on Windows, and make the
distributed Windows CLI bundle actually work for end users with a
stray system MinGW on PATH.

The v5.8.1 release run surfaced two Windows-only issues in the
release pipeline that pre-date v5.8.x but only became user-visible
when v5.8.0 → v5.8.1 triggered a publish:

1. `build-native (windows-latest)` job — `scripts/build_stage1.py`
   invokes the system `clang.exe` (LLVM at `C:\Program Files\LLVM\`),
   which defaults to the `x86_64-pc-windows-msvc` triple. Compiling
   `runtime/native/mapanare_core.c` under `-Werror` against the MSVC
   UCRT trips `-Wdeprecated-declarations` on `fopen` and `strncpy`
   (7 sites total), failing the build before stage1 finishes.
2. `build-cli (windows-latest)` job — the bundled CLI's smoke test
   (`mapanare build smoke.mn -o smoke.exe`) emits an undefined
   reference to `__mn_str_println`. Root cause is in
   `mapanare/toolchain.py::detect_toolchain`: it checks system PATH
   *before* the bundled `toolchain/`, so on the GH Windows runner
   (which has a system MinGW at `C:/mingw64`) the CLI links against
   a gcc that has no `libmapanare_rt.a`. Any end user with a stray
   system MinGW hits the same bug.

Both are pre-existing latent bugs, not v5.8.x regressions. v5.8.2
closes them at the source so the next release tag lands clean.

---

## Items

| ID | Severity | Fix | Effort |
|----|----------|-----|--------|
| **Tc.1** | HIGH | `mapanare/toolchain.py::detect_toolchain` checks system PATH before bundled toolchain. Swap order: bundled wins. The bundle ships `toolchain/lib/libmapanare_rt.a` alongside `toolchain/bin/gcc.exe`; selecting the bundled gcc when one is present guarantees the runtime archive is also reachable. Self-sufficiency is the whole point of bundling. | 15 min |
| **Tc.2** | HIGH | `scripts/build_stage1.py:25` resolves CC as `which("clang") or "gcc"` unconditionally. On Windows, `which("clang")` finds system LLVM clang first (MSVC target by default → MSVC headers → `fopen`/`strncpy` deprecated → `-Werror` blows up). Make the CC default platform-aware: prefer `gcc` on win32 (w64devkit's MinGW headers are clean under `-Werror`); keep clang-first on Linux / macOS where the macOS Apple-Clang vs Homebrew-clang ABI concern documented at `build_stage1.py:22-24` still applies. | 15 min |
| **Version bump + READMEs** | LOW | `VERSION` 5.8.1 → 5.8.2; sync badges across `README.md` + `docs/README.{es,pt,zh-CN}.md`; CHANGELOG entry. | 10 min |
| **Release re-run** | — | Tag + push triggers `publish.yml`. v5.8.2 is the first run that exercises the new code paths on Windows. | (CI time) |

## What does NOT ship in v5.8.2

- Compiler / runtime / IR / lowerer edits — none of the failures
  involve compiler logic. Pure build / distribution plumbing.
- Linux / macOS behavior changes. Both fixes guard on
  `sys.platform == "win32"` or only matter when a bundled toolchain
  exists (which only happens on Windows release builds today).
- Bundle layout changes (the spec already conditionally bundles
  `toolchain/` if present — that is correct, just not load-bearing
  for the discovery bug).

---

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **R1** — Bundled gcc on Windows turns out to be subtly different from system gcc and breaks an end-user flow that used to work via system PATH. | LOW | The bundle ships w64devkit's MinGW gcc — the same toolchain the release pipeline already uses for the runtime archive. Pre-v5.8.2 users with bundled toolchain were *already* getting it for `libmapanare_rt.a` linkage; only the compiler invocation was bypassing it. Consistency increases, not decreases. |
| **R2** — Preferring gcc over clang on Windows changes IR codegen ABI in a way that breaks self-compile fixed-point. | LOW | `build_stage1.py` only uses CC for the C runtime + main wrapper compile (steps 4–5) and the final link (step 6). LLVM IR → object code is done by `clang` directly at step 3, with `--target=x86_64-w64-mingw32` already explicit (line 416 of publish.yml). Tc.2 doesn't touch IR codegen. |
| **R3** — A Windows user has *no* gcc anywhere, only LLVM clang, and Tc.2 makes their previously-working `python scripts/build_stage1.py` invocation fail with "gcc not found." | LOW | Code falls back to clang when gcc is absent: `which("gcc") or which("clang") or "gcc"`. Behavior is preserved for the no-gcc case. |
| **R4** — End user has zero MinGW anywhere AND no bundled toolchain (e.g. running from a source checkout on Windows without staging the toolchain). | UNCHANGED | Tc.1 only changes precedence when *both* bundled and system are present. With neither, the `Known install roots` fallback at step 3 of `detect_toolchain` (winget / scoop / msys2 / chocolatey / LLVM) still runs. |

---

## Exit criteria

- [ ] `mapanare/toolchain.py::detect_toolchain` swaps step 1 and 2:
      bundled toolchain checked before system PATH.
- [ ] `scripts/build_stage1.py:25` CC default is platform-aware:
      `which("gcc") or which("clang") or "gcc"` on `win32`,
      `which("clang") or "gcc"` elsewhere.
- [ ] `VERSION` reads `5.8.2`.
- [ ] README badges (en / es / pt / zh-CN) all read `5.8.2`.
- [ ] `CHANGELOG.md` has a v5.8.2 section listing Tc.1 + Tc.2.
- [ ] `make lint` clean.
- [ ] `python -m doctest scripts/build_stage1.py` clean (if doctests
      exist; skip if none).
- [ ] Local Linux/WSL `python scripts/build_stage1.py` still
      succeeds (ensures we didn't break the non-Windows path).
- [ ] `publish.yml` Windows jobs land green:
      - `build-native (windows-latest, mnc-win-x64.exe, ...)` — passes
      - `build-cli (windows-latest, mapanare-win-x64, ...)` — passes
        with the smoke test linking `smoke.exe` cleanly.
- [ ] SESSION_REPORT written post-merge confirming above.

---

## Decision rule

If, after the v5.8.2 publish run, **either** Windows job still fails:

- **build-native still fails** → bisect: is CC actually gcc?
  Print `which gcc` and `gcc --version` from the workflow before
  invoking `build_stage1.py`. If gcc is present but the build still
  fails, scope creeps into v5.8.3.
- **build-cli still fails** → check whether the bundled toolchain
  was actually staged into `dist/mapanare/toolchain/` by PyInstaller.
  Spec already conditionally bundles it (line 36-37 of `mapanare.spec`),
  but verify with `ls -R dist/mapanare/toolchain/` in the workflow
  before the smoke test. If absent, spec fix scopes to v5.8.3.

Do **not** add CI-only path-prepending hacks (`export PATH=$PWD/toolchain/bin:$PATH`
in the smoke test step). The fix has to live in the CLI for end users
to benefit. CI workflow remains a thin invoker of the bundled binary,
matching what end users do.

---

## Why a separate release (not folded into v5.8.1)

v5.8.1 is already tagged. Re-tagging would force-push a tag, which
violates the "never overwrite published refs" hygiene the project
holds (`feedback_v5_tag_timing.md`). v5.8.2 is the clean way:
new tag, new release run, new artifacts, no rewrite of v5.8.1's
published-but-broken artifacts.
