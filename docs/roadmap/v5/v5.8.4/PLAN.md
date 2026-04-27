# v5.8.4 — Wb.2 closure + WASM CI hygiene

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.8.3 shipped (Wb.1 closed via decomposed-arg
`__mn_str_free`; mnc-stage1.exe runs end-to-end on Windows producing
217,879-line stage2.ll; mnc-stage2 still blocked by Wb.2; WASM CI
job started failing on Wa.1)
**Estimated work:** 4–8 hours (Wb.2 main fix is bounded by the
existing v5.0.4 Cb.15 Python-side blueprint; Wa.1 is ~30 min)

---

## Goal

Close **Wb.2** — make the self-hosted `mapanare/self/emit_llvm.mn`
target-aware so stage2.ll on Windows is Win64-ABI-correct
end-to-end. Re-enable the Windows `Self-compile to stage2` step in
`.github/workflows/publish.yml`. Bundle **Wa.1** (WASM CI wasmtime
install pin) as a small CI-hygiene fix riding along — it's blocking
dev-branch CI today and unrelated to the Wb.x arc, but cheap to
fold in.

By v5.8.4 ship:
- `build-native (windows-latest)` runs the FULL self-compile +
  fixed-point cycle and lands green
- `mnc-win-x64.exe` artifact is genuinely the self-built
  mnc-stage2 (not the v5.8.3 mnc-stage1.exe carry-forward)
- Windows fixed-point validation produces ≤4-line diff (same Dr.1
  tolerance as Linux)
- WASM CI job stops silently mis-installing wasmtime; the install
  step fails fast on regression instead of skipping
- Linux + macOS native stay green; goldens 66/66 preserved

---

## Context — what v5.8.3 closed and what's left

| publish.yml / ci.yml job | v5.8.2 | v5.8.3 | v5.8.4 target |
|---|---|---|---|
| `build-cli (windows-latest)` | ✅ Tc.1 | ✅ | ✅ |
| `build-native` Build mnc-stage1 (Windows) | ✅ Tc.2 | ✅ | ✅ |
| `build-native` Self-compile to stage2 (Windows) | ❌ Wb.1 SIGSEGV | ⏸️ skipped (Wb.2 carry) | ✅ closed |
| `build-native` Smoke test (Windows) | ❌ never reached | ✅ on mnc-stage1.exe | ✅ on mnc-stage2 |
| `build-native` Fixed-point (Windows) | ❌ never reached | ⏸️ skipped (Wb.2 carry) | ✅ NEAR ≤4-line diff |
| Linux / macOS native | ✅ | ✅ | ✅ |
| **NEW:** WASM Cross-Compilation | ✅ | ❌ Wa.1 wasmtime install drift | ✅ pinned install |

v5.8.3 closed Wb.1 with a 25-LOC C-runtime patch (decomposed
`__mn_str_free` signature). It uncovered Wb.2 underneath: the
self-hosted emitter (`mapanare/self/emit_llvm.mn`) hardcodes the
SysV ABI classifier at line 2243
(`abi_classify_return_sret(true, sz, "x86_64-unknown-linux-gnu")`),
so stage2.ll declares ~37 runtime functions with aggregate returns
instead of Win64 sret. The Python emitter
(`mapanare/emit_llvm_text.py`) became target-aware in v5.0.4 / Cb.15
via `_use_sret`/`_rt`/`_is_large_struct`; that work was never
ported to the self-hosted emitter (the .mn world).

Wa.1 surfaced separately on the v5.8.3 commit's CI run: the
wasmtime install step in `ci.yml:400-408` curl-pipes
`wasmtime.dev/install.sh` and verifies inside an
`if [ -d "$HOME/.wasmtime/bin" ]` guard. The install path drifted
(probable wasmtime.dev install.sh behavior change post-v32+
release); the guard silently passes; the next `wasmtime` invocation
fails with `command not found`. Pre-existing on dev — would have
failed on a CI run of v5.8.2 had one been triggered.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Wb.2** | HIGH | Port the v5.0.4 / Cb.15 ABI classifier from `mapanare/emit_llvm_text.py` (`_use_sret`, `_rt`, `_is_large_struct`, byref classification) to `mapanare/self/emit_llvm.mn` (`use_sret_return`, `is_byref_type_st`, `abi_classify_return_sret` already exist as scaffolding but hardcode SysV at line 2243). Make stage2.ll Win64-ABI-correct: aggregate returns become `void @F(ptr sret(<T>), ...)`, aggregate args become `ptr` with caller-side sarg alloca + store, byref classification kicks in on Win64 too. Re-enable Windows self-compile step in publish.yml. Verify fixed-point holds. | 3–6 hours |
| **Wa.1** | LOW | Pin wasmtime install in `ci.yml:400-408`. Replace the silent-skip `if -d` guard with explicit fail-fast. Two equivalent fixes: (a) download the binary directly from `github.com/bytecodealliance/wasmtime/releases` at a pinned version; or (b) use the `bytecodealliance/actions-wasmtime@v1` GitHub Action. Recommend (a) — no new action dependency. | 30 min |
| **Version bump + READMEs** | LOW | `VERSION` 5.8.3 → 5.8.4; sync badges across `README.md` + `docs/README.{es,pt,zh-CN}.md`; CHANGELOG entry. | 10 min |

## What does NOT ship in v5.8.4

- Compiler / runtime / IR / lowerer feature work — same release-pipeline-closeout discipline as v5.8.2 and v5.8.3.
- Reverting the v5.8.3 `__mn_str_free` decomposed signature. Wb.1 closed correctly; the C signature stays decomposed.
- Reverting v5.8.2's gcc-on-Windows preference (Tc.2). Same wall as v5.8.1.
- A new Linux / macOS gate. Both green at v5.8.3 and stay green.
- Goldens regressions. 66/66 stays.

---

## Hypothesis matrix (Wb.2)

Wb.2's root cause is **already known** from v5.8.3's Phase 0
investigation — no exploration needed. The IR pattern is:

```
declare {ptr, i64} @__mn_argv(i64)
%v = call {ptr, i64} @__mn_argv(i64 %i)
```

LLVM lowers `{ptr, i64}` aggregate return at the IR level by
decomposition: rax+rdx on SysV (matches gcc's SysV C ABI for 16-byte
struct return), rax+rdx on Win64 (decomposed style). But Win64's C
ABI for 16-byte aggregate return is **sret** — caller allocates,
passes a hidden pointer in `%rcx` shifting other args. Mismatch.

Same structural bug class as Wb.1, but on the return side and across
~37 functions instead of one.

The fix path is also already known — port the Python emitter's
v5.0.4 Cb.15 work. The work is mechanical: identify the call sites
in `emit_llvm.mn` that currently emit `call {ptr, i64} @F(...)` and
add a target-aware branch that emits the sret pattern when the
target triple is Win64. Mirror Python's `_rt()` at line 1502
(`if self._win64: ... ptr sret(...) sret_arg ...`).

What's NOT predetermined:
- **Detection mechanism for target triple inside the self-hosted
  emitter.** Python uses `self._triple` set by `LLVMTextEmitter`'s
  constructor from `get_target()`. Self-hosted has no equivalent
  state field today. Options: add an `is_win64: Bool` field to
  `EmitState` (Reg.1 gate adjustment), thread a triple through
  `compile()` from the C wrapper (`mnc_main.c`), or substitute a
  build-time placeholder à la `__MN_VERSION__`.

| Option | Pros | Cons |
|---|---|---|
| **OS-1** | Add `is_win64: Bool` to `EmitState`. Set from `compile()` based on a host check (e.g., a runtime call like `__mn_host_is_win64()` exposed by the C runtime, returning `_WIN32` macro state). | Cleanest at the source; no build-script changes; runs identically regardless of where the binary executes. | Reg.1 gate bump (24 → 25 fields); cross-host self-compile produces host-targeted IR (mnc-stage1 on Windows targets Windows; mnc-stage1 on Linux targets Linux — matches today's reality). |
| **OS-2** | Build-time placeholder substitution. `build_stage1.py` substitutes `__MN_TARGET_TRIPLE__` in `emit_llvm.mn` source with the host triple. | Mirrors `__MN_VERSION__` precedent at v4.28.0. | Cross-host build is host-specific; if you build mnc-stage1 on Linux and copy to Windows, the IR target is wrong. (Same problem the project already lives with for the Python emitter, so OK.) |
| **OS-3** | Thread triple via CLI flag (`mnc-stage1 --target=...`). `mnc_main.c` parses, passes to `compile()`. | Caller-controlled, supports cross-targeting. | Wider change to `mnc_main.c` + `main.mn` CLI parsing; new flag for users to know about. |

**Recommendation: OS-1.** Smallest blast radius; preserves the
self-hosting story (mnc-stage1 emits IR for the host it's running
on). Reg.1 gate bump is a documented one-time cost. v6.0 borrow
checker will likely add multiple state fields anyway; one more here
is acceptable.

---

## Investigation plan (v5.8.4 first session, ≤ 1 hour)

1. **Verify Wb.2 reproduction state still matches v5.8.3 SESSION_REPORT** (~10 min). Build mnc-stage1.exe on Windows; produce stage2.ll; compile to mnc-stage2 candidate; run it on `tiny.mn`; confirm crash inside `__mn_argv` per the decomposed/sret mismatch theory. If the crash signature has shifted, re-triage.
2. **Inventory the call sites in `emit_llvm.mn`** that currently emit `declare {AGGR} @F` and `call {AGGR} @F` for runtime functions (~10 min). Mirror this against `mapanare/emit_llvm_text.py`'s `_rt()` to confirm the structural mapping. Estimated ~6-10 functions; each with declaration + call-site emission paths.
3. **Pick OS-1 mechanism**: add `is_win64: Bool` to `EmitState`; expose `__mn_host_is_win64()` from the C runtime (one-line `#ifdef _WIN32`). Update Reg.1 gate to 25 fields if OS-1 chosen (~5 min).
4. **Implement the per-call-site Win64 branches** mirroring Python `_rt()`. Run the goldens on each iteration to confirm no regression on Linux (~2-3 hours).
5. **Re-enable the publish.yml self-compile step** with the Wb.1.dx gdb instrumentation block (paid forward from v5.8.3 PROMPT) so any future Windows runtime crash self-diagnoses in CI logs (~10 min).

Wa.1 in parallel (independent, ~30 min):
1. Download wasmtime via direct GitHub release URL with a pinned version (v32+ as of 2026-04). Install to `/usr/local/bin/wasmtime`.
2. Drop the `if -d "$HOME/.wasmtime/bin"` silent-skip guard.
3. Add `wasmtime --version` as the FIRST step's verification — fail fast.

---

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **R1** — Wb.2's port re-discovers a Win64-ABI subtlety the Python emitter didn't catch (e.g., misclassifies a struct that's exactly 8 bytes; missing byref; tensor-runtime types). | MEDIUM | Goldens 66/66 on Linux is the regression net; sanitizer matrix on Linux catches behavior changes; Windows fixed-point is the correctness gate. The Python emitter's classifier is well-tested at scale; portability is structural. |
| **R2** — OS-1 detection (calling `__mn_host_is_win64()` from compiler-time code) creates a chicken-and-egg: stage1's IR has to build before the call exists. | LOW | The call is from the *running* compiler binary, not from emitted IR. mnc-stage1.exe links against mapanare_core.c which exports `__mn_host_is_win64()`. The self-hosted compiler call resolves at runtime. No bootstrap problem. |
| **R3** — Reg.1 gate bump (24 → 25 EmitState fields) breaks something. | LOW | Reg.1 is gated by `check_struct_registry.py`; gate has been bumped many times across v4.x without incident. |
| **R4** — Windows fixed-point gate fails because the new sret-style stage2.ll has a different line count than the old aggregate-style. | LOW-MEDIUM | The fixed-point check compares stage2.ll to stage3.ll BOTH produced by the same binary, so structural choices match between them. The 4-line VERSION-only diff carries forward. |
| **R5** — Wa.1's pinned wasmtime version goes stale within months. | LOW | Acceptable; CI hygiene is iterative. The pin is auditable; Dependabot or a periodic /loop can flag drift. |
| **R6** — v5.8.3's `mnc-win-x64.exe = mnc-stage1.exe` carry-forward doesn't get cleanly reverted; confused artifact identity. | LOW | publish.yml diff is small and reviewable. Re-enable the self-compile-to-stage2 step verbatim; remove the v5.8.3 skip block. |

---

## Exit criteria

- [ ] `publish.yml` `build-native (windows-latest)` job lands green
      end-to-end including the Self-compile to stage2 step and
      fixed-point gate (≤10-line diff threshold).
- [ ] `publish.yml` Linux / macOS native + all CLI matrix jobs
      remain green (no collateral regression).
- [ ] `mnc-win-x64.exe` artifact size ≈ Linux mnc-linux-x64 size
      (no longer the larger mnc-stage1.exe carry from v5.8.3).
- [ ] `mnc-win-x64.exe --version` outputs `5.8.4`.
- [ ] `mnc-win-x64.exe mnc_smoke.mn` produces `llvm-as`-clean .ll
      output.
- [ ] `ci.yml` WASM Cross-Compilation job lands green (Wa.1 closed).
- [ ] `VERSION` reads `5.8.4`.
- [ ] README badges (en / es / pt / zh-CN) all read `5.8.4`.
- [ ] CHANGELOG.md has a v5.8.4 section listing Wb.2 + Wa.1.
- [ ] `make lint` clean.
- [ ] `check_struct_registry.py` clean (Reg.1 gate adjusted to 25
      if OS-1).
- [ ] WSL `python scripts/build_stage1.py` still succeeds.
- [ ] Goldens 66/66 preserved.
- [ ] `docs/known_issues.md` Wb.2 row flipped to CLOSED v5.8.4.
- [ ] `SESSION_REPORT.md` written documenting OS-1/2/3 decision,
      port scope (which functions + LOC), and verification matrix.

---

## Decision rule

If, after the v5.8.4 publish run:

- **Windows self-compile + fixed-point pass** → SESSION_REPORT, push tag, done. Wb.2 closed; Windows arc done.
- **Self-compile passes but fixed-point shows >10-line drift** → investigate within v5.8.4. Drift may indicate a cross-stage IR-emission inconsistency (rare but possible). Re-tag once resolved.
- **Self-compile still fails on a NEW signature class** (e.g., closure env, signal struct, tensor — anything beyond the ~37 runtime fns) → file as **Wb.3** in `docs/known_issues.md` for v5.8.5; revert publish.yml self-compile to skip; ship v5.8.4 with Wa.1 only. Don't paper over a compiler bug under release-pipeline pressure.
- **Wa.1 fix doesn't take** (wasmtime install regresses) → keep digging on the install path; Wa.1 is small enough to iterate inline.

Do NOT:

- Re-introduce the v5.8.3 Wb.2 carry-forward unless v5.8.4 hits Wb.3.
- Add the `if -d` silent-skip pattern back to the wasmtime install.
- Force-push v5.8.3's tag.
- Skip the Windows fixed-point gate in publish.yml — that's the
  point of v5.8.4.

---

## Why a separate release (not folded into v5.8.3)

v5.8.3 is already tagged. Per `feedback_v5_tag_timing.md`, tags
don't get rewritten. v5.8.4 inherits the unfinished work cleanly —
new tag, new release run, new artifacts. The Wb.2 fix is also
substantial enough (~150-200 LOC across 6-10 self-hosted functions)
to warrant its own release boundary, separate from v5.8.3's narrow
25-LOC C-runtime fix.

Wa.1 rides along because it's blocking dev-branch CI today and
costs ~30 min. Folding into a separate v5.8.3.1 patch would mean
two release ceremonies for ~5 LOC of CI yaml.
