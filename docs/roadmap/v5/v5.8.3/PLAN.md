# v5.8.3 — Windows runtime SIGSEGV on self-compile (Wb.1)

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.8.2 shipped (build-cli green; build-native failed
at the new SIGSEGV)
**Estimated work:** 3–6 hours (investigation-heavy, fix small)

---

## Goal

Land `build-native (windows-latest, mnc-win-x64.exe)` green so the v5.x
release pipeline produces a working Windows compiler binary. Every
other publish.yml job is already green at v5.8.2; this is the last
Windows gate.

---

## Context — what v5.8.2 actually did

| publish.yml job | v5.8.1 | v5.8.2 |
|---|---|---|
| `build-cli (windows-latest)` | ❌ link error: `undefined reference to __mn_str_println` | ✅ Tc.1 closed |
| `build-native (windows-latest)` — `Build mnc-stage1 via Python` step | ❌ `-Werror` UCRT `fopen`/`strncpy` deprecation | ✅ Tc.2 closed |
| `build-native (windows-latest)` — `Self-compile to stage2` step | (never reached — earlier step failed) | ❌ **NEW**: `mnc-stage1.exe mnc_all.mn` SIGSEGV (exit 139) |
| All other matrix jobs (Linux + macOS) | ✅ | ✅ |

Tc.1 + Tc.2 did their job. v5.8.2 isn't a regression — it's a partial
fix that exposed the next failure in the chain. The new failure is the
freshly-built `mnc-stage1.exe` segfaulting when fed `mapanare/self/mnc_all.mn`.

The v5.8.2 PROMPT's decision rule explicitly anticipated this:

> If gcc is present but the build still fails, scope creeps into v5.8.3.

gcc is present, the build of `mnc-stage1.exe` succeeded, but running
the binary fails. Same outcome — v5.8.3.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Wb.1** | HIGH | `mnc-stage1.exe` SIGSEGV self-compiling `mnc_all.mn`. Build succeeds; runtime fails. Root cause unknown — investigation drives the fix. | 2–6 hours |
| **Wb.1.dx** | LOW | Add `gdb -batch -ex run -ex bt` and `dumpbin /headers` instrumentation to publish.yml's `Self-compile to stage2` step so future Windows runtime failures self-diagnose in CI logs. Cheap, paid back at first reuse. | 30 min |
| **Version bump + READMEs** | LOW | `VERSION` 5.8.2 → 5.8.3; sync badges across `README.md` + `docs/README.{es,pt,zh-CN}.md`; CHANGELOG entry. | 10 min |

## What does NOT ship in v5.8.3

- Compiler / runtime / IR / lowerer feature work — the project is in a
  release-pipeline closeout, not a feature cycle. Whatever Wb.1's fix
  turns out to be, the bar is "smallest change that turns the Windows
  job green" — same scope discipline as v5.8.2.
- Reverting Tc.2. v5.8.1 demonstrated that clang-on-Windows blows up on
  the runtime build under `-Werror`. Reverting Tc.2 sends us back to
  that wall. Wb.1 is solved by **fixing the gcc path**, not by going
  back to clang.
- A new Linux / macOS gate. Both are green at v5.8.2 and stay green.

---

## Hypothesis matrix

The PROMPT bisection paths frame the investigation; this section
catalogs hypotheses with empirical falsifiers.

| ID | Hypothesis | Falsifier | Cost |
|---|---|---|---|
| **H1** | gcc-built C runtime + clang-built IR object link cleanly but disagree on x64 sret ABI for aggregate returns. The first call-boundary hitting a struct return crashes. | If `mnc-stage1.exe hello.mn` (1-fn no-aggregate-returns) succeeds AND `mnc-stage1.exe with_struct_return.mn` fails, the boundary is sret. | 30 min |
| **H2** | gcc + clang disagree on `__chkstk` / stack probing for large-frame functions. mnc_all.mn has fns with deep frames; hello.mn does not. | If raising the linked stack from 64 MB to 128 MB makes the SIGSEGV go away or move, stack/probe is implicated. | 20 min |
| **H3** | The MinGW gcc and clang LLVM-MinGW differ on `__udivti3` / `__divti3` / `__multi3` long-double / 128-bit-int helpers. Self-compile uses these in the lowerer's MIR pretty-printer; hello.mn does not. | `dumpbin /imports mnc-stage1.exe` listing — missing or duplicate-but-divergent helper symbols means H3. | 15 min |
| **H4** | This isn't gcc-vs-clang at all — it's a real, pre-existing bug in the self-hosted compiler that crashes on Windows-target IR for any compiler combo, but was never observed because v5.x has never produced a working Windows mnc-stage1 binary before v5.8.2 cleared the build wall. | If clang-built C runtime (with `_CRT_SECURE_NO_WARNINGS` to bypass Tc.2's reason-to-exist) ALSO crashes self-compiling mnc_all.mn, H4 is confirmed and the fix is in `mapanare/self/*.mn`, not the toolchain. | 1 hour |
| **H5** | Stage1's `mnc_all.mn` parse trips on Windows-specific path or filesystem behavior (CRLF, drive letters, path separators) even before the compile. The binary segfaults in I/O, not codegen. | `mnc-stage1.exe < mnc_all.mn` (read from stdin) vs `mnc-stage1.exe mnc_all.mn` (read from file) — if the first path doesn't crash and the second does, H5. | 20 min |

H4 is the most expensive but also the most likely to require *no* v5.8.3
toolchain edits — the fix lives in `mapanare/self/` and fits the project's
existing v6.0 borrow-checker / Windows-self-host arc.

H1 is the most likely lower-cost win. The project already has a
documented Windows ABI surface (Cb.15 closed in v5.0.4 ported the
per-target sret classifier; c62fffe at v5.8.2 manually fixed sret in
`benchmarks/system/enum_match.ll`).

---

## Investigation plan (first session, ≤ 1 hour)

1. **Reproduce locally** (~10 min). `python scripts/build_stage1.py` on
   a Windows runner with the bundled toolchain on PATH. Verify SIGSEGV
   on `mnc-stage1.exe mnc_all.mn`. If it doesn't reproduce, the bug is
   GH-Actions-specific; investigate the runner image's clang/gcc
   version drift.
2. **Capture a crash backtrace** (~20 min). Run under gdb:
   `gdb -batch -ex 'set args mapanare/self/mnc_all.mn' -ex run -ex 'bt 30' mapanare/self/mnc-stage1.exe`.
   The first frame inside Mapanare code names the offending function.
   The frame just below it (in `mapanare_*.c` or in the IR-emitted
   object) names the call boundary — confirm or rule out H1 immediately.
3. **Minimal-input bisect** (~15 min). Run `mnc-stage1.exe` against:
   - `echo 'fn main() { print("hi") }' > tiny.mn` — most basic
   - a 100-LOC subset of mnc_all.mn (pick any single self-hosted module,
     e.g. `mapanare/self/lexer.mn` standalone)
   - the full `mnc_all.mn`
   The smallest-input that crashes scopes the next step.
4. **Branch on outcome** (~15 min). If H1: c62fffe-style ABI fix at the
   self-hosted emitter. If H2: bump linker stack reservation. If H3:
   add explicit `-static-libgcc` to the link line. If H4: file the bug
   under known_issues.md, do not block v5.8.3 on it; ship a v5.8.3
   that re-routes Windows native build to a Linux-cross-build path so
   the .exe is produced by a known-good Linux toolchain and the
   release artifact reaches users while we work on H4 in parallel.
5. **Write up** in `SESSION_REPORT.md` with the hypothesis-falsifier
   matrix annotated.

---

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **R1** — Wb.1's root cause is H4 (real self-hosted bug surfaced by Windows). Fix lands in compiler code, not toolchain — much larger blast radius. | MEDIUM | Decision rule: if Phase 4 lands H4, v5.8.3 ships a Linux-cross-build workaround for the .exe artifact; H4's actual fix scopes to v5.8.4 with a proper PLAN. Don't paper over a compiler bug under release-pipeline pressure. |
| **R2** — Reverting Tc.2 is tempting if Wb.1 is hard. Easy way out is `-DCRT_SECURE_NO_WARNINGS` + back-to-clang. | LOW | Explicit "What does NOT ship" guard: this is a forbidden path. Tc.2 was the right call; v5.8.1 proves clang on Windows under -Werror is unsustainable. |
| **R3** — Investigation eats more than 6 hours and the user pivots to "just ship without Windows native binary." | LOW-MEDIUM | The build-cli (Windows) artifact already ships and works. Native binary (`mnc-win-x64.exe`) is for `mnc run`/`mnc build` direct-binary users; CLI bundle is the broader path. v5.8.3 can ship build-cli green + build-native carry-forward to v5.8.4 if H4 is real. |
| **R4** — gdb / dumpbin not in the GH-hosted Windows runner image. | LOW | `choco install mingw` includes gdb; dumpbin is in any MSVC build tools install. Add a one-liner install step to `Wb.1.dx` if needed. |
| **R5** — The fix accidentally regresses Linux / macOS native builds, which were green. | LOW | publish.yml runs the full matrix on every tag — any regression surfaces in the same run. The `-DCRT_SECURE_NO_WARNINGS`-style escape hatch (R2) IS the way to regress macOS, where `_CRT_*` is undefined. Don't go there. |

---

## Exit criteria

- [ ] `publish.yml` `build-native (windows-latest)` job lands green.
- [ ] `publish.yml` Linux / macOS native + all CLI matrix jobs remain
      green (no collateral regression).
- [ ] `mnc-win-x64.exe` self-compile produces a stage2.ll byte-identical
      to the input within Dr.1 tolerance (4-line VERSION-only diff at
      most). Same fixed-point gate publish.yml already enforces at
      line 436.
- [ ] `mnc-win-x64.exe --version` outputs `5.8.3`.
- [ ] `mnc-win-x64.exe mnc_smoke.mn` produces an `llvm-as`-clean .ll
      output (the smoke test publish.yml already runs).
- [ ] `VERSION` reads `5.8.3`.
- [ ] README badges (en / es / pt / zh-CN) all read `5.8.3`.
- [ ] CHANGELOG.md has a v5.8.3 section listing Wb.1.
- [ ] `make lint` clean.
- [ ] WSL `python scripts/build_stage1.py` still succeeds.
- [ ] `SESSION_REPORT.md` written documenting hypothesis matrix
      outcome and root cause.

---

## Decision rule

If, after the v5.8.3 publish run:

- **build-native still fails AND root cause is H1/H2/H3** → ship is
  blocked; investigate further within v5.8.3 (re-tag once fixed).
- **build-native still fails AND root cause is H4** (real compiler
  bug) → ship v5.8.3 as a Linux-cross-build for the .exe artifact;
  scope the H4 root-cause fix to v5.8.4 with its own PLAN. Tag the
  workaround clearly in CHANGELOG so a v6.0 borrow-checker / Windows
  self-host arc has a clean handoff point.
- **build-native passes** → SESSION_REPORT, push tag, done.

Do NOT:

- Add `-DCRT_SECURE_NO_WARNINGS` and revert Tc.2 to "make clang work."
- Disable `-Werror` in the C runtime build to "let the deprecation
  warnings through."
- Skip the Windows native job in publish.yml. The point of v5.8.3 is
  to have a passing Windows native job, not to lower the bar.
- Force-push the v5.8.2 tag. v5.8.3 is the clean way forward.

---

## Why a separate release (not folded into v5.8.2)

v5.8.2 is already tagged at `fc2508e`. Per `feedback_v5_tag_timing.md`,
tags don't get rewritten. v5.8.3 inherits the unfinished work the
clean way — new tag, new release run, new artifacts.
