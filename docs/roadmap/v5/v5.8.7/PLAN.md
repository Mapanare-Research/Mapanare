# v5.8.7 — Da.0 macOS arm64 publish gate + Da.1 Apple AArch64 ABI plan

**Status:** PLANNING (Da.0 quick CI fix may ship in this release;
Da.1 full ABI work parked for v5.8.8 pending Phase 0 evidence)
**Breaking:** No (Da.0 is CI-only; Da.1 is a planning doc)
**Prerequisite:** v5.8.6 shipped (We.1 — Win32 ABI closure + the
3-way SysV / Win64 / i686 dispatch this builds on)
**Estimated effort:**
- Da.0 (CI workaround) — 30-60 min
- Da.1 Phase 0 (empirical Mac probe) — 1-2 hours on user's Mac
- Da.1 implementation (if Phase 0 confirms gap) — 4-8 hours

---

## Goal

Two related items, sequenced:

1. **Da.0** — Stop the v5.8.7 publish workflow from breaking on the
   macOS arm64 native binary build. Either skip the
   `mnc-darwin-arm64` artifact for one release, gate it behind
   `continue-on-error: true`, or revert the macos matrix entry to
   docs-only. Pick whichever closes the immediate bleed without
   over-promising.
2. **Da.1** — Quantify and close the Apple AArch64 ABI gap that
   surfaced when v5.8.7's switch to `macos-latest` (arm64) actually
   exercised the macOS native build for the first time. Ship as a
   v5.8.8+ closure once empirical probing on the user's Mac confirms
   the gap shape.

This release writes PLAN.md + PROMPT.md and (per user decision) may
also ship the Da.0 workaround. Da.1 implementation does NOT ship in
v5.8.7.

---

## What broke

Run #41 of the binary distribution workflow — first run with the
new `macos-latest` / `mnc-darwin-arm64` matrix entry — failed at
"Self-compile to stage2 (native binary)" with:

```
FATAL: __mn_list_push received corrupted list (data=0x40
       len=-9223372036853859795 cap=105553143477536
       esz=-9223372036854775784)

[CRASH] SIGABRT during compile at mapanare/self/mnc_all.mn
0   mnc-stage1   0x00000001051bf3d8  mnc-stage1 + 3847128
1   libsystem_platform.dylib  _sigtramp + 56
3   libsystem_c.dylib  abort + 124
```

The C runtime's defensive guard in `__mn_list_push` (added vN.x to
catch exactly this class of bug) tripped: `data=0x40` is a small
constant (looks like a struct field offset interpreted as a
pointer); `len`, `cap`, and `esz` are all values that look like
either pointers or stack garbage interpreted as `i64`. Classic
signature of a struct field being read at the wrong offset, or an
aggregate parameter being passed/received via a different ABI on
caller vs callee.

The crash is in `mnc-stage1` (built natively on the macos-latest
arm64 runner), running on `mapanare/self/mnc_all.mn`. The Python
bootstrap (`scripts/build_stage1.py`) produced a binary that links
and starts but corrupts list state on the first non-trivial
operation.

---

## Why this didn't show up before

- `macos-13` (Intel) was in the matrix from v5.0.3 through v5.8.6
  but **was already broken** — the runner queue couldn't allocate
  it ahead of GitHub's deprecation, so the job hung at "waiting for
  a runner" and never reached the build step. The release notes
  table advertised both `mnc-darwin-x64` and `mnc-darwin-arm64`
  download links, but neither binary was actually being built or
  published. Both download links were 404s.
- Goldens on macOS run via the `ci.yml` "macOS & iOS
  Cross-Compilation" job which compiles individual `.mn` files —
  it **never** exercised stage1 self-compiling its own source. The
  bug only manifests at the moment mnc-stage1 has to compile
  ~38,000 lines of Mapanare and exercise enough of the runtime
  surface to hit the corrupted-list path.
- Linux x86_64 + Windows x86_64 publish builds work because the
  Python bootstrap emits IR with `target triple =
  "x86_64-unknown-linux-gnu"` (default) and then on Windows
  rewrites it to `"x86_64-w64-mingw32"`. SysV (Linux) and Win64
  (after v5.8.4 Wb.2) both have first-class ABI dispatch in
  `abi.py` and `emit_llvm.mn`. Apple AArch64 falls through to a
  text-only triple/datalayout patch with **no ABI re-emission**.

---

## Root-cause hypothesis

`scripts/build_stage1.py:103-108` emits IR via `compile_multi_module_mir`
which internally calls the Python emitter with the default
target triple (`x86_64-unknown-linux-gnu`). At emission time,
`mapanare/abi.py::classify_return` dispatches on this triple and
classifies all aggregate returns + parameters using **SysV AMD64
rules** (`_classify_sysv` — > 16 B → sret).

Then `build_stage1.py:122-136` rewrites:
- `target triple = "x86_64-unknown-linux-gnu"` → `"arm64-apple-macos"`
- The Linux x86 datalayout → the macOS arm64 datalayout

But the **function signatures and call sites are unchanged** —
they reflect SysV decisions baked in at IR-emit time. Specifically:
- Aggregates exactly equal to 16 B (`{ptr, i64}`) — both SysV and
  AAPCS64 return in 2 GP registers; agreement, no bug.
- Aggregates > 16 B (`{ptr, i64, i64, i64}` = 32 B — the list
  struct shape) — SysV uses sret hidden first arg; AAPCS64 uses
  x8 indirect result register, which is also a hidden first arg
  but with a different register convention. **Functionally
  equivalent at the IR level**, no bug here either.
- **Aggregates ≤ 16 B passed as parameters** — SysV passes in 2
  GP registers (RDI/RSI etc.); AAPCS64 passes in 2 GP registers
  (X0/X1 etc.). Agreement.
- **Aggregates > 16 B passed as parameters** — SysV passes by
  value on the stack (callee reads from stack); AAPCS64 passes by
  reference (caller copies struct to a temporary and passes the
  pointer). **THIS IS A REAL DIVERGENCE.** If the IR has
  `void @foo(%struct.Foo %s)` for a 32-byte struct, clang's arm64
  backend will lower it differently from clang's x86_64-Linux
  backend. The caller and callee in the SAME translation unit
  will agree because the same backend lowers both — but if one
  side sets up the call expecting SysV semantics and the other
  side reads it expecting AAPCS64 semantics, fields are at the
  wrong offsets.

The list struct `{ptr, i64, i64, i64}` (32 B) is a strong
candidate. Need empirical confirmation on the Mac.

Adjacent hypothesis: variadic argument passing on Darwin
AAPCS64 differs from Linux AAPCS64 (Darwin passes ALL variadics
on the stack; Linux uses registers). If any Mapanare runtime
function takes `...`, this could also corrupt state. Less likely
to manifest as the observed signature though.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Da.0** | HIGH (CI broken) | Close the immediate bleed: either skip the macOS arm64 native binary in v5.8.7 publish (matrix entry deleted; release notes Apple Silicon row says "Build from source"), or set `continue-on-error: true` so the rest of the release ships even if mnc-darwin-arm64 fails. Pick one; ship v5.8.7 with whichever. | 30-60 min |
| **Da.1** | MEDIUM (correctness) | Phase 0 empirical probe on user's Mac to confirm the SysV-vs-AAPCS64 divergence hypothesis. Build mnc-stage1 locally, capture the crash with debugger, identify the exact function whose signature differs between IR (SysV) and arm64 codegen (AAPCS64). Document findings. Implementation: extend `mapanare/abi.py` + `emit_llvm.mn` to detect Apple AArch64 host and emit AAPCS64-shaped IR from the start (NOT a post-emit text patch). Add `EmitState.is_apple_aarch64` field; mirror the v5.8.6 We.1 pattern. | Phase 0: 1-2h. Implementation: 4-8h. Total: ~1 session. |
| **Da.2** | LOW (test coverage) | Add a CI job that exercises `mnc-stage1` self-compiling `mnc_all.mn` on a non-x86_64-Linux platform. The current macOS CI compiles individual goldens — it doesn't exercise the stage1 self-compile path that the publish workflow does. This is the gap that let Da.1 stay latent until v5.8.7. Either add to existing `macos:` job in `ci.yml` or create a new `macos-self-compile:` job. | 1-2h. Independent of Da.1. |
| **Da.3** | LOW (docs) | The release notes table at `publish.yml:111-112` advertised both arm64 and x64 macOS binaries from v5.0.3 through v5.8.6, but only x64 was wired into the matrix (and even x64 was broken from macos-13 deprecation). Audit other release-notes claims against the actual build matrix. | 30 min. |

---

## What this release decides

### Decision 1: ship Da.0 in v5.8.7?

**Recommendation: yes.** v5.8.7 is already a release in flight (the
version got bumped after the v5.8.6 CI fixes — target counts +
changelog honesty + macOS publish matrix). Without Da.0, every
v5.8.7+ publish run will fail at the macOS arm64 build step. Two
sub-options:

**Option A: drop the macOS arm64 matrix entry entirely.**
- Edit `publish.yml:340-342` to remove the macos-latest row.
- Edit `publish.yml:111` to make the Apple Silicon row also say
  "Build from source" (matching Intel).
- Pros: no broken artifact promised. Clean signal.
- Cons: Apple Silicon Mac users get no binary download. Same
  state as v5.8.6 effectively (where arm64 was promised but never
  built).

**Option B: keep the matrix entry but mark `continue-on-error: true`.**
- Edit `publish.yml:340-342` to add `continue-on-error: true` on
  the macos-latest row.
- Pros: if Da.1 lands mid-release-cycle, the next push starts
  publishing arm64 binaries automatically. Release notes table
  stays consistent.
- Cons: the macOS step will keep failing red on every release run
  until Da.1 closes. Noise in the actions UI.

**Recommendation: Option A.** Cleaner; matches the pattern from
v5.8.7 commit where Intel was explicitly downgraded to "Build from
source." Flip the Apple Silicon row to the same; restore both rows
when Da.1 closes.

### Decision 2: implement Da.1 in v5.8.7 or v5.8.8?

**Recommendation: v5.8.8.** Da.1 needs Phase 0 empirical probing
on the user's actual Mac before code is written. The v5.8.6 We.1
PLAN explicitly required Phase 0 ground-truthing for the same
class of bug (Win32 cdecl ABI) and that discipline caught the
silent `{ptr, i64}` truncation that would have shipped otherwise.
Apple AArch64 has its own corners (Darwin variadic ABI; HFA/HVA
rules; bool/char promotion rules) that need empirical probing
before code lands.

If the user has time on a Mac during v5.8.7's window, Phase 0
probing CAN happen now and inform whether Da.1 is a v5.8.8 micro-
release or whether a workaround unlocks it sooner.

### Decision 3: implement Da.2 in v5.8.7 or v5.8.8?

**Recommendation: v5.8.8 with Da.1.** Da.2 only matters once
Da.1 actually produces a working binary — there's nothing to
gate against until then. Ship them together.

### Decision 4: macOS x86_64 (Intel) future

Currently x86_64 macOS is "build from source." GitHub no longer
provides Intel Mac runners on the free tier and the Intel Mac
share of dev machines is collapsing. Recommendation: leave Intel
as build-from-source indefinitely; revisit only if a real demand
signal arrives. Same posture as v5.8.6 took for i686-Windows.

---

## What does NOT ship in v5.8.7 regardless of decision

- Da.1 implementation (real Apple AArch64 ABI dispatch in
  `abi.py` + `emit_llvm.mn`).
- Da.2 (the missing self-compile CI smoke test on macOS).
- Apple AArch64 native binary in the release artifacts.
- Re-enabling the macOS arm64 download link in release notes.
- macOS x86_64 build resurrection.

---

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Da.0 Option A is misread as "we don't support macOS." | Release notes table already says "Build from source" for the Intel row; Apple Silicon joining matches that pattern. Add a CHANGELOG line explicitly noting both Mac arches are build-from-source pending v5.8.8. |
| R2 | Phase 0 probe identifies a different root cause than the SysV-vs-AAPCS64 hypothesis. | That's the entire point of Phase 0 — measure, don't assume. The hypothesis is well-supported by the crash signature but not proven. PLAN treats it as a hypothesis throughout. |
| R3 | Da.1 implementation introduces a regression on Linux x86_64 self-compile (the dominant path). | The 3-way ABI dispatch from v5.8.6 We.1 is the template — preserves SysV as the default branch. Da.1 adds an `is_apple_aarch64` branch parallel to `is_windows`. Linux code paths untouched. |
| R4 | Apple AArch64 ABI has corners that aren't captured in the user's Phase 0 probe. | Same mitigation v5.8.6 used: the empirical Phase 0 probe is the spec. If the panel finds gaps later, micro-release them. |
| R5 | The `build_stage1.py` text-patch approach (rewrite triple+datalayout post-emission) is structurally wrong for any non-default target, not just Apple. | True. The proper fix is to plumb the host triple through to `compile_multi_module_mir` so abi.py classifies correctly from the start. Da.1 should fix this for Apple specifically; v5.9.0+ should generalize the pattern. |
| R6 | Phase 0 needs the user's Mac and a debugger workflow they may not be set up for. | PROMPT.md walks through the exact `lldb` invocation + IR diffing steps. The Mac is recent enough (whatever the user has) to run `clang`, `lldb`, and `llvm-dis` from Apple's developer tools. |

---

## Closure checklist for v5.8.7 (Da.0 only)

- [ ] `publish.yml` macos-latest matrix entry removed OR
      `continue-on-error: true` (per Decision 1).
- [ ] `publish.yml` release-notes Apple Silicon row updated to
      match the chosen state.
- [ ] CHANGELOG `## [5.8.7]` entry filled in with the v5.8.6 CI
      fix bullets (target counts, changelog honesty, macOS
      publish matrix) + a Da.0 line.
- [ ] `make lint` clean.
- [ ] No source code changes to `mapanare/`, `runtime/`, or
      `mapanare/self/`.
- [ ] CI run passes on the next push (Linux + Windows artifacts
      published; macOS skipped or marked allowed-fail).

## Closure checklist for v5.8.8 (Da.1 + Da.2)

- [ ] Phase 0 empirical probe on user's Mac documented in
      `docs/roadmap/v5/v5.8.8/SESSION_REPORT.md` §Phase 0.
- [ ] `mapanare/abi.py` adds Apple AArch64 dispatch (separate
      from generic AArch64 if Phase 0 finds Darwin-specific
      divergences).
- [ ] `mapanare/emit_llvm_text.py` plumbs the host triple
      through so abi.py classifies before IR is emitted.
- [ ] `mapanare/self/emit_llvm.mn` adds `is_apple_aarch64` field
      to EmitState (Reg.1 25 → 26 fields) with parallel helpers
      (`use_apple_aarch64_abi(st)`, etc.).
- [ ] `scripts/build_stage1.py` removes the text-patch-after-emit
      approach in favor of passing the triple to the emitter.
- [ ] mnc-stage1 self-compiles `mnc_all.mn` cleanly on user's
      Mac.
- [ ] Goldens 66/66 preserved on Linux + Windows + macOS arm64.
- [ ] Fixed-point NEAR preserved on Linux.
- [ ] CI macOS job exercises stage1 self-compile (Da.2).
- [ ] `publish.yml` re-adds macos-latest matrix entry; release
      notes Apple Silicon row points to a real binary.
- [ ] Bootstrap seed refresh evaluated (likely not needed —
      Da.1 doesn't add new builtins, just dispatches existing
      ones; but verify with a clean `bash scripts/build_from_seed.sh`
      run).
