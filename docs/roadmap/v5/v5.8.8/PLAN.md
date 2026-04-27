# v5.8.8 — Da.1 Apple AArch64 ABI closure + Da.2 macOS self-compile CI

**Status:** PLANNING (gated on
`docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md` from user's Mac probe)
**Breaking:** No (additive ABI dispatch, mirrors v5.8.6 We.1
SysV / Win64 / i686 → SysV / Win64 / i686 / Apple-AAPCS64)
**Prerequisite:** v5.8.7 shipped (Da.0 — macOS arm64 native binary
deferred to this release). PHASE_0_FINDINGS.md from v5.8.7
PROMPT.md §B written and committed.
**Estimated effort:**
- Phase 1 (Python emitter dispatch) — 2-3h
- Phase 2 (self-hosted emit_llvm.mn parallel) — 2-3h
- Phase 3 (build_stage1.py text-patch removal) — 1-2h
- Phase 4 (Da.2 CI smoke test) — 1-2h
- Phase 5 (publish.yml re-enable) — 30 min
- Phase 6 (validation matrix + seed eval) — 1-2h
- **Total:** 8-12 hours across 1-2 focused sessions

---

## Goal

Close the Apple AArch64 ABI gap that v5.8.7's Da.0 deferred. Two
items:

1. **Da.1** — Make `mnc-stage1` produce correct LLVM IR when built
   on Apple Silicon (`aarch64-apple-macos`). Currently the Python
   bootstrap emits IR with SysV/Linux ABI decisions baked into
   the function signatures, then text-patches the triple +
   datalayout to Apple AArch64 — leaving callers and callees
   disagreeing on aggregate parameter passing. Fix at the
   structural root: plumb the host triple through to
   `compile_multi_module_mir` so `abi.py::classify_return` and a
   new parameter-passing classifier run on the actual target from
   the start. Mirror in self-hosted `emit_llvm.mn`.
2. **Da.2** — Add a CI job that exercises stage1 self-compiling
   `mnc_all.mn` on macOS arm64. The current `ci.yml` macOS job
   compiles individual goldens; it never exercised the path that
   broke in v5.8.7 publish. Without this, Da.1 stays latent on
   macOS the same way We.1 stayed latent on i686.

After this release, the macOS arm64 native binary in `publish.yml`
is re-enabled and the release-notes Apple Silicon row points to a
real download link again.

---

## What broke (recap from v5.8.7)

`mnc-stage1` built on `macos-latest` (arm64) crashed during
`mnc-stage1 mapanare/self/mnc_all.mn`:

```
FATAL: __mn_list_push received corrupted list
       (data=0x40 len=-9223... cap=105... esz=-9223...)
[CRASH] SIGABRT during compile
```

Root-cause hypothesis (from v5.8.7 PLAN §"Root-cause hypothesis"):

- `compile_multi_module_mir` defaults to triple
  `x86_64-unknown-linux-gnu`, runs `abi.py::_classify_sysv` for
  all aggregates.
- `build_stage1.py:122-136` post-patches `target triple` +
  `target datalayout` strings to `aarch64-apple-macos` after
  emission. **Function signatures retain SysV decisions.**
- For aggregates ≤ 16 B (return + param): SysV and AAPCS64
  agree. No bug.
- For aggregates > 16 B returned by value: both ABIs use a
  hidden first-arg pointer (SysV: explicit `sret`; AAPCS64:
  `x8` indirect result register, IR-level equivalent). No bug.
- For aggregates > 16 B passed BY VALUE: **SysV passes on the
  stack; AAPCS64 passes BY REFERENCE** (caller copies struct to
  a temporary, passes the pointer). **REAL DIVERGENCE.** A
  caller emitting SysV-shaped IR (struct-by-value as register
  pairs) hits a callee that arm64 backend lowered as
  by-reference (loads through a pointer). Field offsets are
  garbage; `data=0x40` reads a small constant where a heap
  pointer should be.

The list struct `{ptr, i64, i64, i64}` (32 B) is the strong
suspect — `__mn_list_push`'s parameters are exactly this shape.

**Adjacent hypothesis:** Apple Darwin variadic argument passing
differs from Linux AAPCS64 (Darwin: all variadics on stack;
Linux: register up to 8th arg). If any `__mn_*` runtime function
takes `...`, this could compound or replace the primary
hypothesis. `__mn_str_format` and `__mn_str_concat` are obvious
candidates to re-check.

**This release does not assume the hypothesis is correct.**
Implementation is gated on PHASE_0_FINDINGS.md from the user's
Mac probe (v5.8.7 PROMPT.md §B).

---

## Existing infrastructure to build on

The good news: Apple AArch64 is **partially plumbed** already.

### `mapanare/abi.py` — return classifier already exists

```python
def classify_return(ir_ty: str, total_size: int, triple: str) -> ReturnABI:
    if triple.startswith("i686") or triple.startswith("i386"):
        return _classify_i686_cdecl(total_size)
    if "windows" in triple:
        return _classify_win64(total_size)
    if triple.startswith("aarch64"):
        return _classify_aapcs64(total_size)   # ← already here
    return _classify_sysv(total_size)


def _classify_aapcs64(total_size: int) -> ReturnABI:
    """AArch64 AAPCS64 return classification.
    Aggregates ≤ 16 bytes return in x0/x1.  Larger use x8 (sret).
    """
    if total_size <= 16:
        return _REG
    return _SRET
```

`_classify_aapcs64` is byte-identical to `_classify_sysv` at the
threshold. Returns are not the problem (consistent with the
hypothesis). **The gap is parameter passing**, not return
classification.

### `mapanare/targets.py` — Apple target already registered

```python
TARGET_AARCH64_APPLE_MACOS = Target(
    triple="aarch64-apple-macos14.0",
    data_layout="e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-n32:64-S128-Fn32",
    description="macOS (ARM64 / Apple Silicon)",
    ...
)
```

`host_target_name()` already correctly resolves Darwin/arm64 →
`"aarch64-apple-macos"`. `get_target("aarch64-apple-macos")`
returns the right datalayout.

### What's missing

1. **Parameter-passing classifier** (`abi.py`). Returns are
   classified; parameters are not. The emitter currently uses
   one of two by-value strategies (Win64 sarg, i686 byval) —
   neither runs when triple is SysV-default. Need a third path
   for AAPCS64 by-reference parameter passing.
2. **`compile_multi_module_mir` triple plumbing.**
   `scripts/build_stage1.py:103` invokes the emitter without
   passing a target/triple. The emitter defaults to SysV. Then
   `:122-136` text-patches the triple after emission. Need to
   replace text-patch with a `target=` kwarg.
3. **`EmitState.is_apple_aarch64`** field in self-hosted
   `emit_llvm.mn` (mirroring `is_windows: Bool` + `win_arch: Int`
   from v5.8.6 We.1). Reg.1 gate 25 → 26 fields.
4. **Helpers** parallel to `use_win64_abi(st)` / `use_i686_abi(st)`:
   `use_apple_aarch64_abi(st)`. Plus the parameter-rewrite
   helpers.
5. **C-runtime export** to detect Apple AArch64 host
   (`__mn_host_is_apple_aarch64()`) — parallel to
   `__mn_host_is_windows()` / `__mn_host_arch_bits()` from
   v5.8.6.
6. **Bootstrap seed refresh** if the new C-runtime export is
   actually called from Mapanare-level code (same break shape as
   v5.8.4 → v5.8.5 and v5.8.5 → v5.8.6). Needs verification —
   if the Python emitter does the dispatch and the self-hosted
   emitter only inherits a pre-set `is_apple_aarch64` flag from
   the build pipeline (rather than calling
   `__mn_host_is_apple_aarch64()` at runtime), no seed refresh
   needed.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Da.1.A** | HIGH (correctness) | Add `classify_param(ir_ty, size, triple)` to `abi.py` parallel to `classify_return`. AAPCS64 branch: > 16 B by-value → "byref" (caller alloca + store + pass ptr). SysV branch: pass on stack (no IR rewrite). Win64 branch: existing `sarg` rewrite. i686 branch: existing `byval` rewrite. | 1-2h |
| **Da.1.B** | HIGH (correctness) | Plumb `target` (or `triple`) kwarg through `compile_multi_module_mir` → `LLVMTextEmitter.__init__`. Default to `host_target_name()` so existing call sites that don't pass it auto-detect. Update `scripts/build_stage1.py` to pass the host triple at invocation. Delete the post-emit text-patch block (`:122-136`). | 2h |
| **Da.1.C** | MEDIUM | `mapanare/emit_llvm_text.py` — add Apple AArch64 dispatch parallel to existing `_win64` / `_i686` / `_sysv` branches. Use `Da.1.A`'s `classify_param` for aggregate parameter rewrite. Emit AAPCS64-correct calling convention attributes. Update return-emission to consult `classify_return` (existing). | 2-3h |
| **Da.1.D** | MEDIUM | `mapanare/self/emit_llvm.mn` — add `is_apple_aarch64: Bool` field to `EmitState` (Reg.1 25 → 26 fields). New helpers `use_apple_aarch64_abi(st)`, `aapcs64_rewrite_decl_params`, `aapcs64_byref_rewrite_args`. Mirror the Python dispatch. Update `compile_multi_module_mir` self-hosted equivalent if any. | 3-4h |
| **Da.1.E** | LOW (only if needed) | New C-runtime export `__mn_host_is_apple_aarch64()` in `runtime/native/mapanare_core.c` reading `__APPLE__` + `__aarch64__`. Skip if dispatch is purely build-pipeline / triple-driven. | 30 min if needed |
| **Da.2** | MEDIUM (gap closure) | New `macos-self-compile` job in `.github/workflows/ci.yml` (or expand existing `macos:` job): build mnc-stage1 via `python scripts/build_stage1.py`, then run `./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll`, then `llvm-as /tmp/stage2.ll -o /dev/null`. Without this, Da.1 stays latent on the next clang version bump. | 1-2h |
| **Da.3** | LOW | `publish.yml` — re-add `macos-latest` matrix entry to `build-native`; flip release-notes Apple Silicon row back to "Download" link. Mirrors v5.8.7's Da.0 reversal. | 30 min |
| **Da.4** | LOW | Bootstrap seed refresh evaluation. If Da.1.E adds a new builtin call site in `mapanare/self/`, refresh per `bootstrap/seed/README.md` §"Updating the Seed". Otherwise verify clean `bash scripts/build_from_seed.sh` and skip. | 30 min - 1h |

---

## Phase plan

### Phase 0 — empirical probe (DONE on user's Mac)

Per v5.8.7 PROMPT.md §B. Output:
`docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md`. This release **does
not start until that file exists**. The findings document refines
or rejects the hypothesis above; if it rejects, this PLAN is
revised before Phase 1.

### Phase 1 — Python emitter dispatch (Da.1.A + Da.1.B + Da.1.C)

1. Add `classify_param(ir_ty, total_size, triple)` to `abi.py`
   with four branches mirroring `classify_return`. The AAPCS64
   branch returns `"byref"` for > 16 B by-value aggregates;
   `"register"` otherwise. Other branches preserve existing
   behavior (Win64 sarg via separate code path; i686 byval via
   separate code path; SysV no rewrite).
2. Plumb `target: str | Target | None = None` kwarg through:
   - `LLVMTextEmitter.__init__` → store `self._triple` from
     resolved target
   - `compile_multi_module_mir(root_source, root_file, *,
     target=None, ...)` → pass to emitter
   - `scripts/build_stage1.py:103` → call with
     `target=host_target_name()`
   - **Delete** `scripts/build_stage1.py:118-145` text-patch
     block (the `if sys.platform == "darwin":` and
     `elif sys.platform == "win32":` post-patch).
3. In `emit_llvm_text.py`, replace `self._triple = "x86_64-..."`
   default with `self._triple = target.triple if target else
   "x86_64-unknown-linux-gnu"`. Update any hardcoded triple
   string in module headers to read from `self._triple`.
4. Add `_apple_aarch64` property mirroring `_win64`:
   ```python
   @property
   def _apple_aarch64(self) -> bool:
       return self._triple.startswith("aarch64-apple")
   ```
5. Update parameter-emission paths to consult `classify_param`
   for AAPCS64 byref rewrite. Mirror `win64_sarg_rewrite_args`
   shape: caller alloca + store + pass-as-ptr; callee param
   declared as `ptr` with size annotation in a comment.
6. Validation gate before moving to Phase 2:
   - `python scripts/build_stage1.py` on Linux still produces
     byte-identical IR to v5.8.7 (modulo VERSION) — the SysV
     branch must not regress.
   - On user's Mac: `python scripts/build_stage1.py` produces
     IR with `target triple = "aarch64-apple-macos14.0"` (no
     post-patch needed) and a different aggregate-param shape
     for the suspect `__mn_list_push` call sites. `mnc-stage1`
     binary self-compiles `mnc_all.mn` cleanly.

### Phase 2 — self-hosted emitter parallel (Da.1.D)

1. Add `is_apple_aarch64: Bool` field to `EmitState` in
   `mapanare/self/emit_llvm.mn`. Reg.1 25 → 26 fields. Mirror
   v5.8.6 We.1's `is_windows` + `win_arch` addition.
2. New helpers:
   - `use_apple_aarch64_abi(st: EmitState) -> Bool` — single
     point of dispatch for AAPCS64 path.
   - `aapcs64_rewrite_decl_params` — declare aggregate-by-value
     params > 16 B as `ptr` (mirrors
     `win64_rewrite_decl_params`).
   - `aapcs64_byref_rewrite_args` — at call sites, alloca +
     store + pass-as-ptr (mirrors `win64_sarg_rewrite_args`,
     using `align 8` for AArch64).
   - `aapcs64_byref_advance_state` — bookkeeping for arg
     position counters.
3. Detection: at `emit_mir_module` start, set
   `st.is_apple_aarch64` based on either the host triple
   (passed in via build pipeline) or by calling a new C-runtime
   export `__mn_host_is_apple_aarch64()`. Decision per Phase 1
   approach.
4. Every existing `if st.is_win64` or `if use_win64_abi(st)`
   site adjacent to parameter rewrites gets a parallel
   `if use_apple_aarch64_abi(st)` branch.
5. Validation gate before Phase 3:
   - `bash scripts/rebuild.sh` on Linux clean — no SysV regression.
   - Goldens 66/66 preserved.
   - On user's Mac: `bash scripts/rebuild.sh` clean; stage2.ll
     exists, `llvm-as` clean; mnc-stage1 self-compiles
     `mnc_all.mn` cleanly.

### Phase 3 — build_stage1.py final cleanup (Da.1.B finalization)

After Phase 1+2 confirmed clean:
1. Delete the post-emit triple/datalayout text-patch block in
   `scripts/build_stage1.py:118-145` if not already done in
   Phase 1.
2. Audit for any other text-patch-after-emit code paths in
   `scripts/`. Either plumb the triple through or document why
   text-patch is acceptable for that specific path.

### Phase 4 — Da.2 CI smoke test

1. Add `macos-self-compile` job to `.github/workflows/ci.yml`,
   or expand the existing `macos:` job:
   ```yaml
   - name: Build mnc-stage1
     run: python scripts/build_stage1.py
   - name: Self-compile mnc_all.mn
     run: |
       ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn \
         > /tmp/stage2.ll
       echo "stage2.ll: $(wc -l < /tmp/stage2.ll) lines"
   - name: Validate stage2.ll
     run: brew install llvm@18 && llvm-as /tmp/stage2.ll -o /dev/null
   ```
2. Run on `macos-latest`. The job must pass before merging Da.1
   work.
3. Optionally: add an analogous `linux-self-compile` job using
   `bash scripts/verify_fixed_point.sh` to catch any SysV
   regression that the existing CI golden suite misses.

### Phase 5 — publish.yml re-enable (Da.3)

1. Re-add the `macos-latest` row to `build-native` matrix (the
   row v5.8.7 deleted).
2. Flip release-notes Apple Silicon row back to a Download link
   (the row v5.8.7 changed to "Build from source").
3. Validate with a `workflow_dispatch` test push on a side
   branch before merging to main.

### Phase 6 — validation matrix + seed eval (Da.4)

1. Full sanitizer matrix on Linux (no regressions vs v5.8.7
   baseline):
   - `make lint` clean
   - `make test` non-bootstrap pytest clean
   - Goldens 66/66 preserved
   - `bash scripts/verify_fixed_point.sh` NEAR or strict
   - `check_struct_registry.py` clean (Reg.1 26 EmitState
     fields if Phase 2 added the field)
2. Mac validation: `mnc-stage1` self-compiles `mnc_all.mn`;
   stage1 binary runs the existing test corpus without
   regressions.
3. Bootstrap seed: run `bash scripts/build_from_seed.sh` end
   to end. If Da.1.E added a Mapanare-level call to a new
   `__mn_host_is_apple_aarch64()` builtin, the v5.8.6 seed
   rejects it (same break shape as v5.8.4 → v5.8.5 and v5.8.5
   → v5.8.6); refresh per `bootstrap/seed/README.md`. If
   dispatch is purely build-pipeline-driven, seed survives —
   skip refresh.

---

## Decisions

### Decision 1: dispatch via C-runtime probe or build-pipeline triple?

Two valid paths to setting `EmitState.is_apple_aarch64`:

**Option A:** New `__mn_host_is_apple_aarch64()` C-runtime
export (parallel to v5.8.6's `__mn_host_is_windows()`). Self-
hosted emitter calls it at module-emit time.
- **Pros:** matches the v5.8.4/v5.8.6 pattern; runtime
  introspection is the lingua franca of host detection.
- **Cons:** **forces a bootstrap seed refresh** (Bb.x). The
  existing v5.8.6 seed has no knowledge of this builtin and
  rejects calls to it. Same break shape as the v5.8.4 → v5.8.5
  and v5.8.5 → v5.8.6 transitions.

**Option B:** Plumb the target triple through the build
pipeline. `compile_multi_module_mir(target=...)` →
emitter sets `_apple_aarch64` from `target.triple`. Self-hosted
emitter receives the flag from a build-time env var or a
preprocessor-style replacement, not a C-runtime call.
- **Pros:** no seed refresh; no new builtin dependency.
- **Cons:** asymmetric with v5.8.4/v5.8.6 dispatch pattern;
  needs a separate plumbing channel in self-hosted emitter for
  the build-time configuration.

**Recommendation: Option B for Phase 2 self-hosted emitter
specifically.** The v5.8.4 → v5.8.5 → v5.8.6 chain demonstrated
the cost of seed-refresh-per-builtin-add: each refresh requires
a clean Linux build chain, increases binary size, and exposes
the project to the kind of latent breakage v5.8.5 cleaned up.
Build-pipeline dispatch is structurally cleaner and avoids the
break.

For Phase 1 Python emitter, the dispatch is already build-
pipeline-driven (`self._triple` is set from constructor args);
no C-runtime call needed there.

### Decision 2: Da.2 in v5.8.8 or v5.8.8.1?

**Recommendation: ship Da.2 in v5.8.8.** Da.1 without Da.2 is
half a closure — the bug stayed latent for the entire v5.x arc
because no CI exercised the path. Shipping the fix without the
gate-against-future-regression is exactly the pattern v5.8.5
flagged as "the failure mode that produced this bug." Cost
estimate is 1-2h; well within the v5.8.8 window.

### Decision 3: Implement `classify_param` as a sibling of `classify_return`, or extend `classify_return`?

**Recommendation: sibling.** Returns and parameters have
genuinely different rules per ABI (Win64 sret vs sarg are
*different* mechanisms even though both use a hidden ptr; SysV
returns >16 B via sret but passes >16 B by stack value not by
reference). Conflating them in one function would force a
parameter-vs-return discriminator argument and obscure the
per-ABI rule structure. Keeping them parallel matches the
existing v5.8.6 We.1 helper pattern
(`win64_rewrite_decl_params` / `win64_sarg_rewrite_args` are
already split).

### Decision 4: bump VERSION to 5.8.8 immediately or last?

**Recommendation: last.** v5.8.6 We.1 ran into a non-trivial
debugging arc with `i686-w64-mingw32-gcc` ABI corners that
needed iteration. v5.8.8 has the same risk shape. Bumping
VERSION early forces a re-bump if the implementation slips into
v5.8.8.1. Bump after Phase 6 validation passes.

---

## What ships in v5.8.8

- **Source changes:**
  - `mapanare/abi.py` — `classify_param()` + helpers
  - `mapanare/emit_llvm_text.py` — Apple AArch64 dispatch +
    triple plumbing
  - `mapanare/self/emit_llvm.mn` — `is_apple_aarch64` +
    helpers
  - `scripts/build_stage1.py` — text-patch removed; triple
    passed
  - `runtime/native/mapanare_core.c` — `__mn_host_is_apple_aarch64`
    if Decision 1 lands on Option A
  - `.github/workflows/ci.yml` — `macos-self-compile` job
  - `.github/workflows/publish.yml` — `macos-latest` re-added
    to `build-native`; release-notes Apple Silicon row reverted
    to Download link
- **Docs:**
  - `docs/roadmap/v5/v5.8.8/PLAN.md` (this file)
  - `docs/roadmap/v5/v5.8.8/PROMPT.md` (execution prompt;
    drafted alongside this PLAN, gitignored, not committed)
  - `docs/roadmap/v5/v5.8.8/SESSION_REPORT.md` (closeout
    narrative once shipped)
  - `CHANGELOG.md` — `[5.8.8]` block
  - `docs/known_issues.md` — Da.1 row flipped to CLOSED v5.8.8;
    Da.2 closure noted
  - CLAUDE.md release-history bullet
- **Bootstrap:**
  - **Seed refresh only if Decision 1 lands on Option A.**
    Otherwise no seed change.
- **Version:** 5.8.7 → 5.8.8 at end of Phase 6.

## What does NOT ship in v5.8.8

- iOS arm64 (`aarch64-apple-ios17.0`) ABI work. iOS shares
  AAPCS64 with macOS arm64 *but* has its own variadic +
  position-independent-code corners. Out of scope.
- Generic AAPCS64 dispatch decoupled from "Apple". Linux ARM64
  (`aarch64-linux-android34`, `aarch64-unknown-linux-gnu`) uses
  the same AAPCS64 rules but ships through the Android NDK
  cross-compile path (`ci.yml` `android` job), not
  `build_stage1.py`. If Phase 0 finds a Linux ARM64 issue too,
  bundle as Da.1 v2; otherwise defer.
- Apple AArch64 datalayout corner cases (HFA/HVA: homogeneous
  float/vector aggregates, returned in `v0-v3`). Mapanare uses
  i64/ptr-only aggregates today; HFA/HVA would only matter if a
  future tensor-returning ABI surfaces. Out of scope.
- macOS x86_64 (Intel) build resurrection. Same posture as
  v5.8.7 (build-from-source). Revisit only if a real demand
  signal arrives.
- Windows ARM64 (`aarch64-pc-windows-msvc`). Out of scope; no
  demand signal.
- Generic compile_multi_module_mir caller-site refactor for
  ALL targets. Da.1.B fixes Apple AArch64 specifically. Per-
  target plumbing of every CLI command remains follow-up work
  (v5.9.0+).

---

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| Da.R1 | PHASE_0_FINDINGS.md identifies a different root cause than the SysV-vs-AAPCS64 by-value parameter divergence hypothesis. | The hypothesis is well-supported by the crash signature but unproven. PLAN treats it as a hypothesis throughout. If Phase 0 rejects, revise PLAN before Phase 1. The Phase 0 → Phase 1 gate is non-negotiable. |
| Da.R2 | Apple Darwin variadic ABI is also (or instead) the bug. | B.5 of v5.8.7 PROMPT covers this. If `__mn_str_format` / `__mn_str_concat` use `...` and lower differently on Darwin, that's a parallel divergence. Mitigate by adding a `_classify_variadic_aapcs64_apple` if Phase 0 finds it. Likely addressable in Da.1.A scope; if larger, split to v5.8.9. |
| Da.R3 | Phase 1 SysV regression on Linux x86_64. | The `classify_param` SysV branch must be a no-op (existing behavior). Default-arg `target=host_target_name()` on Linux returns `x86_64-linux-gnu`, so the AAPCS64 branch never fires. Validate with byte-identical IR diff vs v5.8.7. |
| Da.R4 | Phase 2 self-hosted emitter parallel introduces a stage1 vs Python emitter divergence. The fixed-point test catches structural divergence; the goldens harness catches functional. Both must stay green. | Test on Linux throughout Phase 2 — that's where the fixed-point gate runs. Mac validation is Phase 2's exit criterion only. |
| Da.R5 | Bootstrap seed refresh required (Decision 1 Option A path). | If chosen, follow `bootstrap/seed/README.md` §"Updating the Seed". Same procedure as v5.8.5 (Bb.1) and v5.8.6 (Bb.2). Adds ~30 min to Phase 6. |
| Da.R6 | The Apple datalayout in `targets.py` (`aarch64-apple-macos14.0`, `e-m:o-...`) is wrong or stale. | Cross-check against `clang --target=aarch64-apple-macos -E -dM - < /dev/null \| grep DATALAYOUT` on user's Mac in Phase 0. Adjust before Phase 1 if so. |
| Da.R7 | clang-on-Mac version drift between user's local probe and CI runners. | macOS-latest GitHub runners pin to specific clang versions; document in PHASE_0_FINDINGS.md. Da.2 catches version-specific regressions before they ship. |
| Da.R8 | The text-patch removal in Phase 3 breaks Windows builds (the `elif sys.platform == "win32"` block). | Phase 3 deletes BOTH the darwin and win32 patches. Replaces with `target=host_target_name()` plumbing that already returns `x86_64-windows-gnu` on Windows. Win64 path validated unchanged via existing CI. |
| Da.R9 | Da.2 CI job times out on macOS-latest runner (mnc_all.mn is 38k LOC; self-compile is non-trivial). | Set explicit timeout (15-30 min). If real, optimize: cache LLVM install via `brew install llvm@18` step caching; reuse `python scripts/build_stage1.py` artifacts across jobs. Pre-existing Linux self-compile budget is ~5 min on the same runner class; macOS arm64 should be in the same ballpark. |
| Da.R10 | Re-enabling macOS arm64 native binary in publish.yml passes locally but fails in publish workflow due to release-asset-upload step ordering. | Phase 5 validation runs through `workflow_dispatch` on a side branch before merging. The publish step itself is unchanged from v5.8.6. |

---

## Closure checklist for v5.8.8

### Phase 0 (gate)

- [ ] `docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md` exists and
      is committed.
- [ ] Hypothesis confirmed or refined; PLAN revised if rejected.
- [ ] Implementation surface in PHASE_0_FINDINGS.md §8 matches
      Da.1.A/B/C/D items above.

### Phase 1-3 (Python + self-hosted emitter)

- [ ] `mapanare/abi.py::classify_param` lands; SysV / Win64 /
      i686 / AAPCS64 branches all covered.
- [ ] `compile_multi_module_mir(target=...)` accepts target;
      auto-detects via `host_target_name()` if omitted.
- [ ] `scripts/build_stage1.py` text-patch block removed
      (`if sys.platform == "darwin":` and corresponding win32
      block).
- [ ] `mapanare/emit_llvm_text.py` Apple AArch64 dispatch
      lands; `_apple_aarch64` property mirrors `_win64`.
- [ ] `mapanare/self/emit_llvm.mn` `EmitState.is_apple_aarch64`
      added; Reg.1 26 fields clean.
- [ ] `use_apple_aarch64_abi(st)` + 3 helpers added; mirror
      Win64 helper structure.
- [ ] `__mn_host_is_apple_aarch64()` C-runtime export added IF
      Decision 1 → Option A.

### Phase 4 (Da.2)

- [ ] `.github/workflows/ci.yml` macOS self-compile job runs:
      build mnc-stage1, self-compile mnc_all.mn, llvm-as
      validate.
- [ ] Job passes on `macos-latest` runner.
- [ ] Job pinned in branch protection (so Da.1 regressions
      block merges).

### Phase 5 (publish.yml)

- [ ] `build-native` matrix re-adds `macos-latest` row.
- [ ] Release-notes Apple Silicon row points to Download link
      again (mirrors Linux/Windows row shape).
- [ ] `workflow_dispatch` test on side branch produces a real
      `mnc-darwin-arm64` artifact that runs.

### Phase 6 (validation)

- [ ] `make lint` clean.
- [ ] `make test` non-bootstrap pytest: 0 failures, baseline
      preserved.
- [ ] Goldens 66/66 preserved.
- [ ] `bash scripts/verify_fixed_point.sh` NEAR or strict.
- [ ] `check_struct_registry.py` clean.
- [ ] Sanitizer matrix (valgrind, ASan, LSan) — no new
      regressions vs v5.8.7 baseline.
- [ ] Bootstrap seed: clean `bash scripts/build_from_seed.sh`
      OR refresh per `bootstrap/seed/README.md` if Da.1.E added
      a builtin call.
- [ ] Mac validation: `mnc-stage1` self-compiles `mnc_all.mn`
      cleanly; binary runs the existing test corpus without
      regressions.

### Documentation + release

- [ ] `CHANGELOG.md` `[5.8.8]` block filled in.
- [ ] `docs/known_issues.md` Da.1 row flipped to CLOSED v5.8.8.
- [ ] `CLAUDE.md` release-history bullet added.
- [ ] `docs/roadmap/v5/v5.8.8/SESSION_REPORT.md` written.
- [ ] `VERSION` bumped 5.8.7 → 5.8.8.
- [ ] `git tag v5.8.8` per the user-approval-required rule
      (the tag is the lead's call; this PLAN does not
      auto-tag).

---

## What this plan trusts vs. what it gates

**Trusts:**
- `_classify_aapcs64` in `abi.py` is correct for return values
  (it matches AAPCS64 §6.9 and SysV §3.2.3 — both ≤16 register,
  >16 sret).
- `targets.py::TARGET_AARCH64_APPLE_MACOS` has the right
  datalayout (`e-m:o-...`); confirmed by clang's own emission
  on macOS arm64.
- `host_target_name()` correctly resolves Darwin/arm64. Verified
  in source.
- The v5.8.6 We.1 dispatch pattern (3-way SysV/Win64/i686) is a
  good template for adding the 4th case (Apple-AAPCS64).

**Gates on Phase 0 findings:**
- The SysV-vs-AAPCS64 by-value parameter divergence is the bug.
- The bug appears in `__mn_list_push` specifically (or other
  list-runtime functions taking `MapanareList` by value).
- The fix shape is `classify_param` with byref rewrite for >16 B
  AAPCS64 args, parallel to `win64_sarg_rewrite_args`.
- Apple Darwin variadic ABI is NOT also a divergence (or is
  bundled with Da.1 if it is).
- clang's macOS arm64 backend version on
  `macos-latest` runner is current enough to expose the bug
  consistently; Da.2 catches future regressions.

If any of these gates rejects, revise this PLAN before Phase 1.
The discipline that caught v5.8.6 We.1's silent miscompilation
is the discipline that catches v5.8.8 Da.1's.
