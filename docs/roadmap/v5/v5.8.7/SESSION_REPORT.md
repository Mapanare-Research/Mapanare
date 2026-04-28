# v5.8.7 — Da.0 closure (macOS arm64 native binary deferred)

**Status:** SHIPPED (v5.8.7)
**Tag:** pending user approval
**Author:** Claude Opus 4.7 (1M ctx) under user direction
**Date:** 2026-04-27
**Estimated:** 30-60 min (Da.0 CI workaround — Track A in PROMPT).
**Actual:** ~45 min for Track A; Track B (Da.1 Phase 0 empirical
probe) deferred — requires user's Mac, cannot run from
WSL/Linux.

---

## TL;DR

- **Da.0 CLOSED with deferral.** v5.8.7 ships the v5.8.6
  follow-up CI fixes (target-count tests, changelog honesty
  checker, macOS publish workflow runner switch) but **does not
  ship a macOS arm64 native binary**. The matrix entry is
  removed; the release-notes Apple Silicon row points to "Build
  from source," mirroring the Intel row.
- **Da.1 Apple AArch64 ABI closure deferred to v5.8.8.** The
  `macos-13 → macos-latest` runner switch (commit `5c5636f`)
  exercised the macOS arm64 native build for the first time
  ever and surfaced a real ABI bug — `__mn_list_push received
  corrupted list (data=0x40 ...)` SIGABRT during self-compile of
  `mnc_all.mn`. Root-cause hypothesis: SysV-vs-AAPCS64 by-value
  parameter divergence for aggregates > 16 B. The bug was
  latent across the entire v5.0.3 → v5.8.6 arc because the
  macos-13 runner was hung in GitHub's deprecation queue and
  never reached the build step.
- **This release is structurally a docs + CI release.** No
  source code changes to `mapanare/`, `runtime/`, or
  `mapanare/self/`. Three files committed in the Da.0 commit
  (`8148ea7`); all source baselines (goldens 66/66, fixed-point
  NEAR, llvm-as clean, lint clean) preserved by construction
  (no source touched).
- **Forward-looking PLAN written.** `docs/roadmap/v5/v5.8.8/PLAN.md`
  drafted at 585 lines covering Da.1.A-E + Da.2 + Da.3 + Da.4
  in 6 phases, gated on `PHASE_0_FINDINGS.md` from the user's
  Mac. The empirical probe instructions are already in v5.8.7
  PROMPT.md §B; v5.8.8 implementation is gated on the findings.

---

## What v5.8.7 ships

The release covers three commits across April 27, 2026:

### Commit `cc7b723` — "Bump target count to 10 and update changelog"

Fixes uncovered while preparing the release:

1. **Target-count tests.** v5.8.6's We.1 work added a 10th
   target (`i686-windows-gnu`) to `mapanare/targets.py`, but
   `tests/targets/test_targets.py::test_total_target_count` and
   `tests/targets/test_wasm_targets.py` still asserted
   `len(TARGETS) == 9`. Bumped the assertions; refreshed the
   docstring on `test_total_target_count` to "5 desktop + 2 WASM
   + 3 mobile."
2. **Changelog honesty checker.** v5.8.6's CHANGELOG bullet for
   the strict fixed-point test put a shell command and a path
   inside one set of backticks
   (`` `bash scripts/build_from_seed.sh: stage1 IR == stage2 IR` ``),
   which `scripts/check_changelog_honesty.py` interpreted as a
   single missing path and rejected. Split the command from the
   path.

### Commit `5c5636f` — "Bump to v5.8.7; update release/CI info"

The version bump itself, plus the CI change that surfaced Da.0:

1. **VERSION** 5.8.6 → 5.8.7.
2. **README badges** updated in `README.md` + `docs/README.es.md`
   + `docs/README.pt.md` + `docs/README.zh-CN.md`.
3. **CHANGELOG** stub for `[5.8.7]` (empty Added/Changed/Fixed
   sections; filled in by commit `8148ea7`).
4. **publish.yml runner switch.** `macos-13` was on GitHub's
   deprecation runway and was hanging in the runner queue
   indefinitely — the macOS Intel publish job never reached the
   build step on any v5.x release, so neither
   `mnc-darwin-arm64` (which had been promised in the
   release-notes table since v5.0.3) nor `mnc-darwin-x64` was
   ever actually built or published. Both download links in
   release notes were 404s. The fix swapped the matrix entry
   to `macos-latest` (Apple Silicon arm64) and updated the
   release-notes Intel row to "Build from source."
5. **The fix surfaced Da.0.** Run #41 of the publish workflow
   (the first run with `macos-latest` actually allocating a
   runner) failed at "Self-compile to stage2 (native binary)"
   with the corrupted-list SIGABRT documented in v5.8.7 PLAN
   §"What broke."

### Commit `8148ea7` — "v5.8.7: Da.0 — defer macOS arm64 native binary; ship CI fixes"

The Track A workaround per `docs/roadmap/v5/v5.8.7/PROMPT.md`
§A:

1. **`publish.yml` build-native matrix.** Removed the
   `macos-latest / mnc-darwin-arm64 / aarch64-apple-darwin` row.
   Matrix is now Linux x86_64 + Windows x86_64 only.
2. **`publish.yml` release-notes table.** Apple Silicon row
   downgraded to "Build from source ([instructions](...))",
   mirroring the Intel row. The Full CLI link (built by the
   separate `build-cli` job on `macos-latest`, which works
   correctly) is preserved — only the Native Compiler column
   changed.
3. **`CHANGELOG.md`** `[5.8.7]` block filled in:
   - `### Fixed` — three bullets covering the target-count
     tests fix, the changelog honesty checker fix, and the
     macOS publish workflow runner switch.
   - `### Notes` — Da.0 deferral note explaining why no macOS
     arm64 binary ships in v5.8.7 and pointing forward to
     v5.8.8 for Da.1 closure.
   - `scripts/check_changelog_honesty.py` clean against the
     new entries.
4. **`docs/roadmap/v5/v5.8.7/PLAN.md`** committed. (PROMPT.md
   intentionally not committed — `.gitignore` excludes
   `PROMPT.md` files as ephemeral session input.)
5. **Side cleanup:** normalized `publish.yml` from CRLF to LF
   line endings. The working tree had CRLF endings from a
   prior session that would have produced a 1255-line diff;
   normalization shrank the actual content diff to 5 lines (1
   modification + 4 deletions), matching the prompt's intent
   exactly.

### Commit `1057e2d` — "Add v5.8.8 roadmap plan; update GitNexus stats"

Forward-looking artifact:

1. **`docs/roadmap/v5/v5.8.8/PLAN.md`** added (585 lines)
   covering Da.1.A-E (Apple AArch64 ABI dispatch) + Da.2
   (macOS self-compile CI gate) + Da.3 (publish.yml re-enable)
   + Da.4 (bootstrap seed evaluation) in 6 phases, gated on
   `PHASE_0_FINDINGS.md` from the user's Mac. The PLAN treats
   the SysV-vs-AAPCS64 by-value parameter divergence as a
   hypothesis throughout — Phase 0 confirms or refines.
2. **`AGENTS.md` + `CLAUDE.md`** GitNexus stat refresh to
   reflect the new symbol/relationship totals after the v5.8.7
   PLAN + v5.8.8 PLAN landed.

---

## What v5.8.7 does NOT ship

Per the v5.8.7 PLAN §"What does NOT ship in v5.8.7 regardless of
decision":

- **Da.1 implementation** — real Apple AArch64 ABI dispatch in
  `mapanare/abi.py` + `mapanare/emit_llvm_text.py` +
  `mapanare/self/emit_llvm.mn`. Deferred to v5.8.8.
- **Da.2** — the missing CI smoke test for stage1 self-compile
  on macOS. Bundled with Da.1 in v5.8.8 (per v5.8.8 PLAN
  Decision 2).
- **Apple AArch64 native binary** in the release artifacts. The
  `mnc-darwin-arm64` build is gone from the matrix; users on
  Apple Silicon build from source until v5.8.8.
- **Re-enabling the macOS arm64 download link** in release
  notes. Deferred to v5.8.8 Phase 5.
- **macOS x86_64 build resurrection.** Posture unchanged from
  v5.8.6 (build-from-source). GitHub no longer provides Intel
  Mac runners on the free tier; revisit only on a real demand
  signal.
- **Source code changes.** Zero edits to `mapanare/`,
  `runtime/`, or `mapanare/self/`. Validated by
  `git diff v5.8.6..HEAD -- mapanare/ runtime/` returning 0
  lines (excluding pre-existing modifications carried in the
  working tree from prior sessions, which were intentionally
  not staged in commit `8148ea7`).
- **VERSION bump beyond 5.8.7.** The bump landed in commit
  `5c5636f`; no further bump in this release.

---

## What was attempted but NOT done in this session

The session split into two tracks per v5.8.7 PROMPT.md:

- **Track A (Da.0 CI workaround) — DONE** in this Linux/WSL
  environment. Documented above.
- **Track B (Da.1 Phase 0 empirical probe) — DEFERRED.** The
  PROMPT.md §B header explicitly states: "Run this on the
  user's Apple Silicon Mac. Do NOT run on WSL/Linux." From a
  Linux/WSL agent environment, the steps that are physically
  impossible:
  - `xcode-select --install` / Apple's clang+lldb
  - Building a Mach-O arm64 `mnc-stage1` binary (would need to
    cross-compile to arm64-apple-macos from Linux, which the
    current `build_stage1.py` doesn't support — and even if it
    did, the bug only reproduces *running* the binary, not
    building it)
  - Capturing `lldb` register state at the
    `__mn_list_push`-corruption frame
  - `otool -tvV` disassembly comparison of AAPCS64 vs SysV
    lowering
  - `clang -target ...` per-target ABI probe (B.4 of PROMPT.md)
  - `strace`-style probing on Darwin

  The user holds the Mac; the empirical probe is theirs to
  run. The output goes into a new
  `docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md` per PROMPT.md
  §B.6, which v5.8.8 implementation is gated on (per v5.8.8
  PLAN Phase 0 gate).

---

## Metrics

Source-touching baselines (preserved by construction since no
source changed):

- **Goldens:** 66/66 preserved (no compiler edits).
- **Fixed-point:** NEAR preserved (no compiler edits).
- **`llvm-as`:** clean (no compiler edits).
- **`make lint`:** clean (no source edits to gate).
- **`check_struct_registry.py`:** 25/25/91 clean (Reg.1
  unchanged from v5.8.6).
- **`scripts/check_changelog_honesty.py`:** clean against
  `[5.8.7]`.

CI/release surface:

- **`build-native` matrix:** 3 entries (Linux + Windows +
  macOS-arm64) → 2 entries (Linux + Windows).
- **Release-notes table:** 4 rows (Linux + Mac-arm64 + Mac-Intel
  + Windows). Native Compiler column: 4 download links → 2
  download links + 2 "Build from source" rows.
- **Files committed in `8148ea7`:** 3 (`publish.yml`,
  `CHANGELOG.md`, `docs/roadmap/v5/v5.8.7/PLAN.md`).
  - `publish.yml`: 1 insertion + 4 deletions (after CRLF
    normalization; bulk diff was 1255 lines pre-normalization).
  - `CHANGELOG.md`: 30 insertions + 3 deletions.
  - `PLAN.md`: 282-line new file.
- **Files committed in `1057e2d`:** 3
  (`AGENTS.md`, `CLAUDE.md`, `docs/roadmap/v5/v5.8.8/PLAN.md`).
- **Total v5.8.6 → v5.8.7 commit count:** 3 (cc7b723, 5c5636f,
  8148ea7) + 1 forward-looking (1057e2d).

Pre-existing modifications in the working tree at session start
(intentionally not staged; carried forward from prior sessions):

- `AGENTS.md`, `CLAUDE.md` (eventually staged in `1057e2d` for
  GitNexus stat refresh)
- `benchmarks/system/enum_match.ll`
- `docs/known_issues.md`
- `docs/roadmap/v5/v5.8.3/PLAN.md`,
  `docs/roadmap/v5/v5.8.3/SESSION_REPORT.md`,
  `docs/roadmap/v5/v5.8.3/Wb1_BACKTRACE.txt`
- `mapanare/self/emit_llvm.mn`
- `runtime/native/mapanare_core.c`
- `tests/native/test_c_runtime.c`

These remain unstaged after v5.8.7 ships. Likely belong to
in-progress v5.8.3 follow-up or v5.8.8 Phase 0 prep work; out of
scope for this release.

---

## Risk register (from PLAN — outcome)

| ID | Risk | Outcome |
|---|---|---|
| R1 | Da.0 Option A misread as "we don't support macOS." | Mitigated. CHANGELOG `### Notes` block names the deferral explicitly with a forward pointer to v5.8.8 Da.1. Release-notes table preserves the Full CLI download link (built by `build-cli` on `macos-latest`); only the Native Compiler column is downgraded. |
| R2 | Phase 0 probe identifies a different root cause. | Open. Awaits user's Mac probe. v5.8.8 PLAN Phase 0 gate is explicit. |
| R3 | Da.1 implementation introduces Linux x86_64 regression. | Out of scope for v5.8.7 (Da.1 is v5.8.8). Mitigation specified in v5.8.8 PLAN R3: SysV branch in `classify_param` is a no-op; default-arg `target=host_target_name()` returns `x86_64-linux-gnu` on Linux, so the AAPCS64 branch never fires. |
| R4 | Apple AArch64 ABI corners not captured in Phase 0 probe. | Out of scope for v5.8.7. v5.8.8 PLAN R6 + R7 (datalayout staleness, clang version drift) cover this. |
| R5 | `build_stage1.py` text-patch approach structurally wrong. | Confirmed (PLAN §"Root-cause hypothesis" describes this). v5.8.8 Phase 3 deletes the patch in favor of triple plumbing through `compile_multi_module_mir`. |
| R6 | Phase 0 needs the user's Mac and a debugger workflow. | Confirmed. Track B deferred to user. PROMPT.md §B walks through `lldb` invocation + IR diffing. |

---

## Pattern recap — why this release exists

v5.8.7 is the third release in the v5.8.x post-We.1 trail
(v5.8.5 Bb.1 + v5.8.6 We.1 + v5.8.7 Da.0) where shipping a new
target-aware emitter exposes a follow-up CI gap. Each release
fixes the immediate bleed and queues the structural closure for
the next:

| Release | Trigger | Closure |
|---|---|---|
| v5.8.5 | v5.8.4 Wb.2 added a Mapanare-level call to `__mn_host_is_win64()`; v5.8.4 seed didn't know it. | Bb.1 — bootstrap seed refresh (mandatory). |
| v5.8.6 | v5.8.4 Wb.2's `_WIN32` macro choice was correct for x86_64 Windows but silently miscompiled for i686 Windows (which nobody actually targets — latent gap). | We.1 — 3-way ABI dispatch (SysV / Win64 / i686). |
| v5.8.7 | v5.8.6's We.1 added a 10th target; tests asserted 9. CHANGELOG honesty checker rejected a v5.8.6 bullet's backtick formatting. macos-13 deprecation forced a switch to macos-latest, exercising the macOS arm64 build for the first time and surfacing a SysV-vs-AAPCS64 ABI bug. | Da.0 — defer the macOS arm64 binary one release; queue Da.1 for v5.8.8. |
| v5.8.8 (planned) | v5.8.7 Da.0 deferral. | Da.1 — Apple AArch64 ABI dispatch + Da.2 macOS self-compile CI gate. |

Each closure follows the same discipline: **empirical probe
before implementation** (v5.8.6 We.1 Phase 0 used real
`i686-w64-mingw32-gcc 13` traces; v5.8.8 Da.1 Phase 0 will use
real `lldb` traces from the user's Mac). The discipline caught
v5.8.6's `{ptr, i64}` truncation that would have shipped
otherwise; v5.8.8 Phase 0 catches whatever the macOS arm64
specifics turn out to be.

---

## Carry to v5.8.8

**Required before Phase 1:**

- `docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md` written from the
  user's Mac probe (per v5.8.7 PROMPT.md §B). Captures: repro
  command + observed output, environment (macOS version + clang
  version + Python version + M-series chip), `file mnc-stage1`
  + `otool -L` confirmation of arm64 Mach-O, `lldb` capture at
  the `__mn_list_push`-corruption frame, IR inspection of
  `__mn_list_push` decl + a representative call site,
  aggregate-by-value disassembly delta (B.4) +
  variadic disassembly (B.5) if relevant, hypothesis
  confirmed/refined, and an implementation surface mapping into
  v5.8.8 PLAN's Da.1.A-E items.
- The findings document is the spec for v5.8.8 implementation.
  Without it, v5.8.8 implementation guesses at the bug shape.

**Decision pending (v5.8.8 PLAN Decision 1):**

- C-runtime probe (`__mn_host_is_apple_aarch64()`) vs.
  build-pipeline triple plumbing for setting
  `EmitState.is_apple_aarch64`. Recommendation: build-pipeline
  (avoids seed refresh).

**Out of scope for v5.8.7, in scope for v5.8.8:**

- Da.1.A `classify_param` in `abi.py`
- Da.1.B `compile_multi_module_mir(target=...)` plumbing +
  `build_stage1.py` text-patch removal
- Da.1.C-E Python + self-hosted emitter Apple AArch64 dispatch
- Da.2 `macos-self-compile` CI job
- Da.3 `publish.yml` macos-latest re-enable
- Da.4 bootstrap seed evaluation

**Out of scope for v5.8.8, queued for later:**

- iOS arm64 ABI work (separate from macOS arm64 due to PIC +
  variadic corners)
- Generic AAPCS64 dispatch decoupled from "Apple"
  (Linux ARM64 / `aarch64-linux-android34` already ships
  through the Android NDK cross-compile path; bundle if Phase
  0 finds a Linux ARM64 issue too, otherwise defer)
- HFA/HVA aggregate handling (Mapanare uses i64/ptr-only
  aggregates today; relevant only if a future tensor-returning
  ABI surfaces)
- macOS x86_64 (Intel) build resurrection (no demand signal)
- Generic `compile_multi_module_mir` per-CLI-command target
  plumbing refactor (v5.9.0+; Da.1.B fixes Apple AArch64
  specifically)

---

## Closure

v5.8.7 ships as a CI + docs release. The macOS arm64 native
binary download is intentionally absent. The v5.8.8 PLAN exists
as a forward-looking artifact gated on the user's Mac probe
findings; until that probe runs, v5.8.8 stays in PLANNING.

The pattern v5.8.5 → v5.8.6 → v5.8.7 → v5.8.8 follows the
"empirical probe → structural closure" discipline that has held
across the v5.8.x arc. Da.0 is the immediate-bleed close; Da.1
is the structural one.

The tag (`v5.8.7`) awaits user approval per the project's
"never bump to v5 or create v5 tags without explicit user
approval" rule.
