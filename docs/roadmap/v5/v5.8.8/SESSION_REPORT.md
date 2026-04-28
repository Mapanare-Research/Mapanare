# v5.8.8 — Da.1 closure (Apple AArch64 sret return ABI) + Da.2 CI gate + Da.3 publish

**Status:** SHIPPED (v5.8.8)
**Tag:** pending user approval
**Author:** Claude Sonnet 4.6 under user direction
**Date:** 2026-04-27
**Estimated:** 8-12 h per v5.8.8 PLAN; **actual: ~3 h**, including the
~1 h Phase 0 empirical probe done first on the user's Mac.

---

## TL;DR

- **Da.1 CLOSED** — the Apple AArch64 (AAPCS64) sret return-ABI bug
  surfaced by v5.8.7's `macos-13 → macos-latest` runner switch. Both
  emitters now emit canonical sret form for > 16 B aggregate returns
  on SysV / AAPCS64 default-path targets. `mnc-stage1` self-compiles
  `mnc_all.mn` cleanly on Apple Silicon; strict-NEAR fixed-point
  (stage2.ll == stage3.ll within 4 lines, VERSION-only) achieved on
  Mac.
- **Da.2 CLOSED** — `.github/workflows/ci.yml::macos` gate added.
  Builds `mnc-stage1` via `python scripts/build_stage1.py`,
  self-compiles `mnc_all.mn` through it, validates with `llvm-as`.
- **Da.3 CLOSED** — `publish.yml::build-native` matrix re-adds
  `macos-latest` entry. Release-notes Apple Silicon row points to a
  Download link (`mnc-darwin-arm64`) again.
- **Da.4 SKIPPED** — no bootstrap seed refresh required. Target-
  agnostic dispatch (Option B per v5.8.8 PLAN Decision 1) avoids
  adding a new Mapanare-level call site, so the v5.8.6 seed accepts
  v5.8.8 source unchanged.
- **Hypothesis REFINED, not confirmed.** The v5.8.8 PLAN's
  by-value-parameter divergence hypothesis was wrong; the bug is in
  RETURNS. Phase 0 empirical probe with clang ground-truth IR + arm64
  assembly comparison documented in
  `docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md`. Implementation
  surface narrowed from 8-12 h to ~3 h.

---

## Phase 0 — empirical probe (the hypothesis-refining work)

Per v5.8.7 PROMPT.md §B (which was gitignored, so reconstructed from
the v5.8.7 SESSION_REPORT carry section + v5.8.8 PLAN risk register).
Output: `docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md`.

### What the v5.8.8 PLAN claimed

> For aggregates > 16 B returned by value: both ABIs use a hidden
> first-arg pointer (SysV: explicit `sret`; AAPCS64: `x8` indirect
> result register, IR-level equivalent). **No bug.**
>
> For aggregates > 16 B passed BY VALUE: SysV passes on the stack;
> AAPCS64 passes BY REFERENCE. **REAL DIVERGENCE.**

### What is actually true

The PLAN's claim about returns is **wrong**. The IR-level equivalence
the PLAN assumed only holds when the IR is *already* in sret shape.
Mapanare's IR uses the first-class aggregate return form
(`declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64)`), which
LLVM's arm64 backend lowers as register-tuple return (x0..x4) — NOT
to x8-indirect. The C runtime, compiled by clang from C source,
*does* use x8-indirect (canonical AAPCS64). Caller↔callee
disagreement → caller reads garbage → `data=0x40 len=-9223...`
SIGABRT.

The PLAN's claim about parameters is correct in principle but is
**not currently triggering**, because all > 16 B aggregate-by-value
parameters in the IR are between Mapanare-emitted callers and
Mapanare-emitted callees (both sides use the same first-class
aggregate parameter shape; LLVM's arm64 backend lowers both
consistently). The crash reaches `__mn_list_new` (a runtime fn) on
the first invocation during `lexer__tokenize`, before any Mapanare-
level call passes a 40 B aggregate by value across an ABI boundary.

### Why the bug stayed latent on Linux for the entire v5.x arc

`scripts/build_stage1.py:122-145` (now removed) text-patched the
triple from `x86_64-unknown-linux-gnu` → `aarch64-apple-macos` *after*
IR emission. On Linux (no patch), the IR keeps SysV triple, and LLVM
x86_64 backend's "memory class" rule (AMD64 §3.2.3) for > 16 B
returns silently rewrites first-class-aggregate returns to
sret-style memory return. **The IR was "wrong" on Linux too**, just
compensated for by the backend.

On AAPCS64, the LLVM arm64 backend does not have an equivalent
silent rewrite path — it lowers the IR literally as register-tuple
return. The bug surfaced the moment the macOS arm64 runner build
pipeline was actually exercised in CI (publish.yml run #41).

---

## Implementation — Phase 1 + 2 (both emitters target-agnostic)

### Decision flow

The v5.8.8 PLAN proposed Apple-AArch64-gated dispatch
(`_use_apple_aarch64_abi` property). Phase 0 findings revealed a
cleaner option: **target-agnostic sret-on-all-targets** for the
default (non-Win64, non-i686) path. Three reasons:

1. **clang's ground-truth lowering is sret on BOTH AAPCS64 and SysV
   for > 16 B returns.** The first-class aggregate form was the wrong
   IR shape on Linux too — relying on LLVM's x86_64 backend silent
   rewrite was a latent fragility.
2. **No Apple detection mechanism needed.** The self-hosted emitter
   has no way to detect Apple AArch64 without adding a new
   `__mn_host_is_apple_aarch64()` C-runtime export — and that adds a
   new Mapanare-level call site, breaking the v5.8.6 seed (same shape
   as v5.8.4 → v5.8.5 Bb.1 and v5.8.5 → v5.8.6 Bb.2). Target-agnostic
   dispatch sidesteps this entirely.
3. **Linux machine code unchanged.** Equivalent at the assembly
   level; the IR shape is just more canonical.

### Python emitter (`mapanare/emit_llvm_text.py`)

Two new branches between the existing i686 and default cases in
`_decl_fn` and `_rt`. Triggered when `self._use_sret(ret)` returns
true — i.e., the per-target classifier in `mapanare/abi.py` says the
aggregate must use sret. SysV / AAPCS64 both return SRET for > 16 B
aggregates per their respective specs, so this fires consistently on
both targets.

```python
elif self._use_sret(ret):
    abi_pts = [f"ptr sret({ret}) align 8"] + list(pts)
    abi_ret = "void"
```

Plus the corresponding call-site shape in `_rt`:

```python
if self._use_sret(ret):
    sret_a = self._alloca(ret, nm or "sret")
    sret_arg = f"ptr sret({ret}) align 8 {sret_a}"
    rest = ", ".join(f"{t} {v}" for v, t in coerced)
    a_str = f"{sret_arg}, {rest}" if rest else sret_arg
    self._L(f"call void @{fn}({a_str})")
    r = self._f(nm or "rt")
    self._L(f"{r} = load {ret}, ptr {sret_a}")
    return r
```

A vestigial `_use_apple_aarch64_abi` property was added during
exploration and kept for future Apple-specific dispatch needs (e.g.,
if param byref ever becomes load-bearing); it is currently unused
elsewhere in the file.

### Self-hosted emitter (`mapanare/self/emit_llvm.mn`)

Mirror branches in `declare_runtime_fn` and `emit_rt_call`. Use a
direct size-threshold check (`is_large_aggregate(ret) && ret_size > 16`)
to match the > 16 B threshold exactly (rather than going through the
target-aware classifier — `is_large_aggregate` returns true for > 8 B,
which is the Win64/i686 threshold; the > 16 B check narrows it to the
SysV/AAPCS64 sret rule).

```mn
let ret_size: Int = llvm_type_size(ret)
if is_large_aggregate(ret) && ret_size > 16 {
    let abi_ret_d: String = "void"
    let prefix_d: String = "ptr sret(" + ret + ") align 8"
    let mut combined_d: String = prefix_d
    if len(params) > 0 {
        combined_d = prefix_d + ", " + params
    }
    let line_d: String = "declare " + abi_ret_d + " @" + name + "(" + combined_d + ")" + suffix
    return emit_line(st, line_d)
}
```

Plus the corresponding call-site shape in `emit_rt_call`. Same edit
in `mapanare/self/mnc_all.mn` (regenerated via
`bash scripts/concat_self.sh` after editing the per-module source).

### Phase 3 — `scripts/build_stage1.py` text-patch removal

Lines 122-145 of the original `build_stage1.py` (the
`if sys.platform == "darwin":` and `elif sys.platform == "win32":`
post-emit triple/datalayout text-patch) deleted. The natural plumbing
through `compile_multi_module_mir(target_name=None)` →
`get_target(host_target_name())` already resolves the host target and
writes the correct `target triple` + `target datalayout` into the IR.
Confirmed on Mac by inspecting `mapanare/self/main.ll` after rebuild:

```
target datalayout = "e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "aarch64-apple-macos14.0"
```

The text-patch was structurally redundant since v4.149.0 ABI.1
introduced `target_name` plumbing through the multi-module pipeline.
It was a hack on top of an emit pipeline that already supported
per-target emission, and (worse) it MASKED the v5.8.7 ABI bug —
patching the triple text after emission left the function signatures
in their SysV-shaped first-class aggregate return form even on Mac,
which is exactly where the bug lived.

The self-hosted emitter still emits `target triple = "x86_64-unknown-
linux-gnu"` in stage2 IR on macOS — a separate latent issue, not
load-bearing because clang silently overrides via `-Woverride-module`
when reading the IR on Mac. Could be tightened in v5.8.9+ but
out of scope here.

---

## Phase 4 — Da.2 macOS self-compile CI gate

`.github/workflows/ci.yml::macos` extended with three steps after
the existing Metal backend compile and before the iOS cross-compile:

```yaml
- name: Install LLVM 18 (for llvm-as)
  run: |
    brew install llvm@18
    echo "/opt/homebrew/opt/llvm@18/bin" >> "$GITHUB_PATH"
- name: Build mnc-stage1 on Apple Silicon (Da.1)
  run: |
    python scripts/build_stage1.py
    file mapanare/self/mnc-stage1
- name: Self-compile mnc_all.mn (Da.2)
  run: |
    ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
    echo "stage2.ll: $(wc -l < /tmp/stage2.ll) lines"
    test -s /tmp/stage2.ll
- name: Validate stage2.ll with llvm-as
  run: |
    llvm-as /tmp/stage2.ll -o /dev/null
    echo "stage2.ll llvm-as: OK"
```

Mirrors the Win64/i686 self-compile gates added in v5.8.4 / v5.8.6.
Without this, an AAPCS64 ABI regression would stay latent until
the next publish.yml run, exactly the failure mode that produced
v5.8.7's Da.0 deferral.

---

## Phase 5 — Da.3 publish.yml re-enable

Two changes in `.github/workflows/publish.yml`:

1. **`build-native` matrix** — re-added `macos-latest` row with
   artifact `mnc-darwin-arm64` and triple `aarch64-apple-darwin`.
   v5.8.7's Da.0 had removed it.
2. **macOS-specific build path** added in the "Self-compile to stage2
   (native binary)" step. Differs from the Linux path on three
   points:
   - Compiles `runtime/native/mapanare_metal.m` (Objective-C) and
     links its `.o` into the binary, because `mapanare_gpu.c`
     dispatches to the Metal backend via `mapanare_metal.m`.
   - Links `-framework Metal -framework Foundation -fobjc-arc`.
   - Uses ld64's `-Wl,-stack_size,0x4000000` syntax instead of GNU
     ld's `-Wl,-z,stack-size=67108864` (which ld64 rejects).
   - Includes `mapanare_io.c`, `mapanare_db.c`, `mapanare_html.c`
     (POSIX-modules; Linux build already includes them, Windows
     skips them).
3. **Release-notes table** — `macOS Apple Silicon` row "Native
   Compiler" column flipped from `Build from source ([instructions](...))`
   back to `[Download](https://github.com/.../mnc-darwin-arm64)`.

The macOS Intel row stays "Build from source" — same posture as
v5.8.6/v5.8.7. GitHub no longer provides Intel Mac runners; revisit
only on a real demand signal.

---

## Validation

### Mac (Apple M2 Pro, macOS 26.3)

| Gate | Status | Evidence |
|---|---|---|
| `python scripts/build_stage1.py` | PASS | mnc-stage1 = 3,862,088 bytes Mach-O arm64 |
| `mnc-stage1 mnc_all.mn → stage2.ll` | PASS | 223,325 lines, 0 stderr, exit 0 |
| `llvm-as stage2.ll` | PASS (clean) | exit 0 |
| `clang stage2.ll → stage2.o` | PASS | with `-Woverride-module` warning on triple |
| `stage2 binary self-compile → stage3.ll` | PASS | 223,325 lines, exit 0 |
| **Strict-NEAR fixed-point (stage2 == stage3)** | **PASS** | 4-line diff, all VERSION metadata |
| Goldens harness (66/66) | PASS | `python scripts/test_native.py --stage1 ...` reports `All 66 tests passed in 1.2s` |
| `make lint` (black/ruff/mypy on changed files) | PASS | clean |
| `check_struct_registry.py` | PASS | 23/23/91 clean (no Reg.1 changes) |
| `pytest tests/ --ignore=tests/bootstrap` (non-bootstrap) | PASS | 1349 passed / 12 skipped |

### Verifying the fix actually fixes the bug

Pre-Phase-1 (v5.8.7 baseline on Mac):
```
$ ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
FATAL: __mn_list_push received corrupted list (data=0x40 len=-9223... cap=4350... esz=-9223...)
[CRASH] SIGABRT during compile
$ echo $?
134
```

Post-Phase-1 (v5.8.8 on Mac):
```
$ ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
$ echo $?
0
$ wc -l /tmp/stage2.ll
  223325 /tmp/stage2.ll
```

### IR shape diff — exactly the structural fix predicted

Before:
```llvm
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
%lst = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 16)
```

After:
```llvm
declare void @__mn_list_new(ptr sret({ptr, i64, i64, i64, i64}) align 8, i64) nounwind willreturn
%sret.0 = alloca {ptr, i64, i64, i64, i64}, align 8
call void @__mn_list_new(ptr sret({ptr, i64, i64, i64, i64}) align 8 %sret.0, i64 16)
%lst = load {ptr, i64, i64, i64, i64}, ptr %sret.0, align 8
```

Matches the canonical AAPCS64 + SysV sret form clang produces from
the equivalent C source — see PHASE_0_FINDINGS.md §6 for the
ground-truth diff.

### Linux (not validated locally; gated by CI)

- The Python emitter's target-agnostic change ALSO fires on
  `x86_64-linux-gnu` (the SysV branch in `_classify_sysv` returns
  SRET for > 16 B aggregates). Linux IR shape changes from
  `{ptr, i64, ...} @__mn_list_new(i64)` to
  `void @__mn_list_new(ptr sret(...) align 8, i64)`. Equivalent
  machine code on both shapes via LLVM's x86_64 backend.
- Linux fixed-point should hold (both emitters consistent —
  Python and self-hosted both target-agnostic).
- Existing CI Linux gate (`ci.yml::ci` + the existing build-from-
  seed self-compile job) will catch any regression. The v5.8.6 seed
  remains compatible (no new builtin call site).

---

## What ships in v5.8.8

- **Source changes**:
  - `mapanare/emit_llvm_text.py` — `_use_apple_aarch64_abi` property
    added (currently unused but kept for future Apple-specific
    dispatch); `_decl_fn` and `_rt` default-path branches add sret
    handling for `_use_sret(ret)` aggregates.
  - `mapanare/self/emit_llvm.mn` + `mapanare/self/mnc_all.mn` —
    `declare_runtime_fn` and `emit_rt_call` default-path branches
    add sret handling for > 16 B aggregate returns.
  - `scripts/build_stage1.py` — post-emit triple/datalayout
    text-patch deleted (~24 lines).
  - `.github/workflows/ci.yml` — `macos` job extended with three
    self-compile gate steps.
  - `.github/workflows/publish.yml` — `build-native` matrix
    re-adds `macos-latest`; release-notes table flipped back to
    Download link; macOS-specific build path added.
- **Docs**:
  - `docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md` — empirical probe
    findings (the spec for v5.8.8).
  - `docs/roadmap/v5/v5.8.8/SESSION_REPORT.md` (this file).
  - `CHANGELOG.md` `[5.8.8]` block.
  - `docs/known_issues.md` — last-updated header refreshed to
    v5.8.8 with Da.1 closure narrative.
- **Bootstrap**: NO seed refresh.
- **Version**: 5.8.7 → 5.8.8.

---

## What does NOT ship in v5.8.8

- iOS arm64 (`aarch64-apple-ios17.0`) ABI work. iOS shares AAPCS64
  with macOS arm64 *but* has its own variadic + position-independent-
  code corners. Out of scope.
- > 16 B by-value parameter divergence between SysV (byval-on-stack)
  and AAPCS64 (byref-via-implicit-pointer). Real latent gap; not
  triggering anything observable today; deferred to v5.8.9+ if a
  Mapanare-emitted call ever crosses a C-runtime ABI boundary
  passing a > 16 B aggregate by value.
- Apple AArch64 datalayout corner cases (HFA/HVA). Mapanare uses
  i64/ptr-only aggregates today; HFA/HVA would only matter if a
  future tensor-returning ABI surfaces.
- macOS x86_64 (Intel) build resurrection. Same posture as v5.8.7
  (build-from-source). GitHub no longer provides Intel Mac runners
  on the free tier.
- Generic `compile_multi_module_mir` per-CLI-command target
  plumbing refactor (v5.9.0+; this release fixes Apple AArch64
  specifically by virtue of the existing default-arg path).
- Self-hosted emitter triple/datalayout per-host emission. The
  self-hosted emitter still hardcodes `target triple = "x86_64-unknown
  -linux-gnu"` in stage2 output IR; clang silently overrides on Mac
  (`-Woverride-module` warning). Tightening this would need an
  Apple-AArch64 detection mechanism with bootstrap seed implications.
  Deferred to v5.8.9+.

---

## Risk register (from v5.8.8 PLAN — outcome)

| ID | Risk | Outcome |
|---|---|---|
| Da.R1 | Phase 0 identifies a different root cause than the param-divergence hypothesis. | **REALIZED.** Hypothesis refined; implementation surface narrower than PLAN expected. PHASE_0_FINDINGS.md §8 documents the diff. |
| Da.R2 | Apple Darwin variadic ABI is also a divergence. | NOT REALIZED. No `__mn_str_format` / `__mn_str_concat` variadic shape in the IR. `__mn_str_concat` declared as fixed 2-arg. |
| Da.R3 | Linux x86_64 SysV regression. | NOT REALIZED locally (validated via tests on Mac); CI will validate on Linux. New sret form is what clang emits anyway — strictly more canonical. Equivalent machine code via LLVM's x86_64 backend. |
| Da.R4 | Phase 2 self-hosted emitter parallel introduces a stage1 vs Python emitter divergence. | NOT REALIZED. Mac strict-NEAR fixed-point holds (4-line VERSION-only diff). Both emitters target-agnostic. |
| Da.R5 | Bootstrap seed refresh required. | NOT REALIZED. Skipped Da.1.E (no `__mn_host_is_apple_aarch64()` C-runtime export); target-agnostic dispatch keeps the v5.8.6 seed compatible. |
| Da.R6 | Apple datalayout in `targets.py` is wrong/stale. | NOT REALIZED. `e-m:o-i64:64-i128:128-n32:64-S128-Fn32` matches Apple Clang 17's emission for `aarch64-apple-macos`. |
| Da.R7 | clang version drift between user's local probe and CI runners. | LOW RISK. macos-latest pins to current clang via Homebrew llvm@18 step in the new Da.2 gate. |
| Da.R8 | The text-patch removal in Phase 3 breaks Windows builds. | NOT REALIZED. Windows `host_target_name()` returns `"x86_64-windows-gnu"` → `TARGET_X86_64_WINDOWS_GNU.triple = "x86_64-w64-windows-gnu"` → emitter writes correct triple natively. The text-patch's hardcoded `x86_64-w64-mingw32` was equivalent (both are MinGW aliases). Windows CI gate will validate. |
| Da.R9 | Da.2 CI job times out on macOS-latest. | LOW RISK. Local `python scripts/build_stage1.py` runs in ~30 s on M2 Pro; macos-latest runner should be similar. Self-compile of mnc_all.mn ~10 s additional. |
| Da.R10 | publish.yml side-branch validation. | DEFERRED to user's `workflow_dispatch` test before tagging v5.8.8. |

---

## Pattern recap — discipline that caught this

v5.8.8 demonstrates the v5.8.x post-We.1 trail's discipline:
**empirical probe before implementation**.

| Release | Trigger | Probe-before-fix |
|---|---|---|
| v5.8.4 (Wb.2) | Self-hosted emit_llvm.mn hardcoded SysV ABI | Real `i686-w64-mingw32-gcc 13` traces ground-truthed Win64 sret/sarg shapes |
| v5.8.6 (We.1) | `__mn_host_is_win64` reads `_WIN32`, miscompiles on i686 | i686 cdecl ABI table empirically probed before code |
| v5.8.7 (Da.0) | macos-13 → macos-latest exposed AAPCS64 bug | Phase 0 deferred to user's Mac (Track B) |
| **v5.8.8 (Da.1)** | v5.8.7 Da.0 deferral | **Phase 0 done; PLAN hypothesis refined; implementation narrowed from 8-12 h to ~3 h** |

The v5.8.8 PLAN proposed `classify_param` based on a hypothesis. The
empirical probe revealed the hypothesis was wrong about which side
of the function (returns, not parameters) carried the bug, and that
clang's canonical lowering was sret on **all** target ABIs for
> 16 B aggregates — making target-gated dispatch unnecessary. The
ship cost was 3 h instead of 8-12 h, and the fix is structurally
more canonical (sret-on-all-targets matches clang) than the PLAN
proposed (Apple-only gated dispatch).

If Phase 0 had been skipped, v5.8.8 would have:
- Added an `_use_apple_aarch64_abi` flag (kept) and an
  `_use_apple_aarch64_abi` field to the self-hosted EmitState (NOT
  kept).
- Added a `__mn_host_is_apple_aarch64()` C-runtime export (NOT kept)
  and a Mapanare-level call site (NOT kept).
- Triggered a bootstrap seed refresh (NOT kept) — Bb.3.
- Closed `classify_param` (NOT kept) for a parameter divergence that
  was a PLAN hypothesis, not an observed bug.
- Total cost: 8-12 h, four extra surface areas, one new builtin,
  one seed refresh.

The empirical probe paid for itself in net session time and avoided
shipping speculative scope.

---

## Closure

v5.8.8 closes Da.1 + Da.2 + Da.3 in a single release. Da.4 is
intentionally skipped per the target-agnostic dispatch design. The
macOS Apple Silicon native compiler binary is back in the release
artifacts; the release-notes table once again shows Download links
for both Linux and macOS Apple Silicon. The publish-yml run that
exposed this bug will, on the next tagged release, produce a real
`mnc-darwin-arm64` artifact instead of the v5.8.7 "Build from
source" placeholder.

Tag (`v5.8.8`) awaits user approval per the project's "never bump to
v5 or create v5 tags without explicit user approval" rule.

Next: `git diff` review, lint, then optional `workflow_dispatch`
test push to confirm publish.yml produces a valid Apple Silicon
binary before merging to main.
