# v5.33.0 — Nu.\* — Linux + macOS prebuilt `mnc` binaries in release tarballs

**Status:** PLANNING
**Type:** Packaging + CI release. Mirrors v5.32.0's Windows
treatment for Linux and macOS.
**Breaking:** No. Same fallback shape — Python entrypoint stays as
the dev-clone path; release tarballs ship a native `mnc` that the
console-scripts wrapper execs into.
**Prerequisite:** v5.32.0 shipped (`mnc.exe` in Windows SDK ZIP;
fallback wrapper in place; smoke gate green).
**Estimated effort:** 1 session (~3-5h). Less than v5.32.0 because
the publish.yml plumbing pattern, the smoke-job pattern, and the
fallback wrapper are already in place — Nu.\* is "do the same thing,
twice."

---

## Why this exists

v5.32.0 closed Windows: a fresh SDK install never invokes Python
for `mnc --version`, `mnc run`, or `mnc build`. Linux and macOS
release tarballs still have the gap — they ship the Python module
+ a console-scripts shim, no native binary. Less *visible* on Unix
because Python startup is faster and users don't notice the banner
the way Windows users do — but the same structural problem exists.

After v5.33.0:

- `mapanare-${V}-linux-x86_64.tar.gz` ships `bin/mnc` (native ELF).
- `mapanare-${V}-linux-aarch64.tar.gz` ships `bin/mnc` (native ELF).
- `mapanare-${V}-macos-x86_64.tar.gz` ships `bin/mnc` (native Mach-O).
- `mapanare-${V}-macos-aarch64.tar.gz` ships `bin/mnc` (native Mach-O).

`mapanare/` Python tree becomes officially **bootstrap-only** on
all three platforms. Fresh release-tarball installs never start a
Python interpreter.

---

## Goals

1. **Nu.1** — Build `mnc` for Linux x86_64 + Linux aarch64 in CI.
   Native build on each runner (no cross-compile complexity for
   Linux — the runners exist).
2. **Nu.2** — Build `mnc` for macOS x86_64 + macOS aarch64 in CI.
   Native build on macOS runners; aarch64 via Apple Silicon runner
   if available, otherwise cross-compile via `clang -arch arm64`
   from x86_64 runner.
3. **Nu.3** — Wire all four binaries into the appropriate release
   tarballs in `publish.yml`. Layout: `bin/mnc` (no `.exe`).
4. **Nu.4** — Extend Nw.4 smoke job to Linux + macOS publish jobs.
   Same checks: `--version`, `init`, `run`, no Python in process
   tree.
5. **Nu.5** — `mapanare/__main__.py` fallback wrapper from Nw.3
   already detects platform and looks for `bin/mnc` (Unix) or
   `bin\mnc.exe` (Windows). Confirm cross-platform path resolution
   in Nu.5 — small audit, no new code if Nw.3 was written
   correctly.
6. **Nu.6** — Doc updates: `docs/install/linux.md`,
   `docs/install/macos.md` add "What's in the tarball" sections.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Nu.1** | HIGH | **Linux x86_64 + aarch64 builds.** Two new jobs in `publish.yml`: `build-mnc-linux-x86_64` (ubuntu-latest) and `build-mnc-linux-aarch64` (`ubuntu-latest` + qemu OR a real aarch64 runner if available). Each job runs `python3 scripts/build_stage1.py` then renames the output to `mnc`, strips it (`strip mnc` or `llvm-strip`) for size, and uploads as artifact. | 2h |
| **Nu.2** | HIGH | **macOS x86_64 + aarch64 builds.** Two new jobs: `build-mnc-macos-x86_64` (macos-13 runner = Intel) and `build-mnc-macos-aarch64` (macos-14 = Apple Silicon). Same shape as Nu.1: `build_stage1.py` → rename → strip → upload artifact. Sign with ad-hoc identity (`codesign -s - mnc`) so Gatekeeper doesn't quarantine it on extract; user-installable signing comes later. | 2h |
| **Nu.3** | HIGH | **Tarball staging.** Each platform-publish job downloads its matching `mnc` artifact and stages at `bin/mnc` before `tar czf`. Verify `tar tzf | grep mnc` returns exactly one entry per tarball. | 1h |
| **Nu.4** | HIGH (gate) | **Smoke jobs for Linux + macOS.** Mirror Nw.4 across both platforms. Each job extracts the published tarball into `$RUNNER_TEMP/mn-smoke`, runs `bin/mnc --version`, `bin/mnc init testproj`, `bin/mnc run testproj/main.mn`. **Gates the publish.** Aarch64 smoke runs under qemu emulation if no native runner (slower, still required). | 2h |
| **Nu.5** | LOW | **Fallback wrapper audit.** Confirm `mapanare/__main__.py` (post-Nw.3) handles all four Unix layouts (Linux x86_64/aarch64, macOS x86_64/aarch64). Single test added to `test_native_fallback.py` (or wherever Nw.3 put its test) parameterizing over platforms. | 30 min |
| **Nu.6** | LOW | **Doc updates.** Refresh `docs/install/linux.md` and `docs/install/macos.md`. Add a one-line note to `README.md` (en/es/pt/zh-CN): "v5.33.0+ release tarballs include a prebuilt native `mnc` — Python is bootstrap-only." | 30 min |

---

## Phase plan

- **Phase 0** — Pre-flight. v5.32.0 HEAD clean; Windows smoke job
  green for at least one publish run.
- **Phase 1** — Nu.1 Linux jobs. Local proof: `python3
  scripts/build_stage1.py` on the dev WSL box already produces
  Linux x86_64 binary. Aarch64 needs qemu or runner.
- **Phase 2** — Nu.2 macOS jobs. Trickier because dev box probably
  isn't macOS — first reliable verification is the CI run itself.
  Drive iteratively via `act` (local GH Actions runner) if
  available, otherwise PR + observe.
- **Phase 3** — Nu.3 + Nu.4 staging + smoke. Must be in same PR
  as Nu.1/Nu.2 so a publish dry-run validates end-to-end.
- **Phase 4** — Nu.5 fallback audit + Nu.6 docs.
- **Phase 5** — Bump + tag.

---

## Out of scope

- **Mobile binaries (iOS, Android NDK).** The native compiler
  isn't a user-facing tool on those platforms — Mapanare *targets*
  them, doesn't run *on* them. v5.33.0 covers the host platforms
  only.
- **Universal macOS binary (lipo'd fat binary).** Two separate
  tarballs is the standard pattern (see Rust, Go, Swift). One
  tarball per arch is simpler for the smoke gate.
- **Code signing for distribution.** Ad-hoc signing (Nu.2) is
  enough to avoid Gatekeeper quarantine on extract; proper
  Developer ID signing for distributable installers is a v5.34.0+
  conversation.
- **`mapanare-${V}-source.tar.gz` (source release).** Source
  releases stay Python-bootstrap-only by definition — that's what
  source means.
- **Tn.1, M.1, A.1, Ra.New1, Pv.8.B** — carry forward.

---

## Risk

1. **macOS aarch64 runner availability.** GitHub macos-14 runners
   are Apple Silicon but billing tier matters. Mitigation: if
   macos-14 is unavailable, cross-compile via `clang -arch arm64`
   from macos-13; smoke-test under Rosetta as a stopgap and
   rely on user reports for native validation.
2. **Aarch64 Linux smoke under qemu.** qemu emulation is slow
   and occasionally produces ABI mis-execution that doesn't
   reproduce on real hardware. Mitigation: qemu smoke is "good
   enough"; flag a v5.33.1 follow-up if an issue surfaces in
   the wild.
3. **Strip too aggressive.** `strip` on stage1 binaries has
   bitten before (see v3.x era). Mitigation: `strip --strip-debug
   --strip-unneeded` only; preserve symbol table needed for
   `dlsym`-based runtime calls.
4. **macOS code-signing surprises.** Ad-hoc signing is `codesign
   -s -`; on some macOS versions this still triggers Gatekeeper
   when extracting from a tarball downloaded over the network
   (xattr `com.apple.quarantine`). Mitigation: docs note that
   users may need `xattr -d com.apple.quarantine bin/mnc` on
   first run; fix properly in v5.34.0+ with notarization.

---

## Success criteria

- ✅ All four release tarballs (linux-x86_64, linux-aarch64,
  macos-x86_64, macos-aarch64) contain `bin/mnc`.
- ✅ Smoke job green on all four publish jobs.
- ✅ Fresh extract → `bin/mnc --version` → exit 0, version printed,
  no Python invoked.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.
- ✅ `make ci-gates` GREEN; `make lint` clean.

---

## Carry-forward delta

**Closes:**
- "Python is the front door on Linux/macOS release installs."
- The platform asymmetry where Windows had the fix and Unix
  didn't.

**Inherits to v5.34.0:**
- Tn.1 (now 4-release overdue — escalating to HIGH per v5.32.0
  PLAN's escalation rule; **MUST** ship at v5.34.0 or be the
  exclusive scope of an unscheduled v5.33.1 hotfix).
- M.1, A.1, Ra.New1, Pv.8.B.
- macOS notarization (new LOW from Nu.2's ad-hoc signing
  shortcut).

**Native-First Philosophy milestone:** with v5.33.0 shipped,
"Mapanare ships its own toolchain end-to-end" is true on all three
desktop platforms. The `mapanare/` Python tree is officially
bootstrap-only, used once at clean clone, then dormant for the
entire user lifecycle.

**Aggregate state entering v5.34.0:** 0 HIGH / 2 MEDIUM (Tn.1
escalated; macOS notarization) / ~5 LOW.
