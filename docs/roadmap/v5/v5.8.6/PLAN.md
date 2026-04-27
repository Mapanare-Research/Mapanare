# v5.8.6 — We.1 Win32 (i686) ABI plan

**Status:** PLANNING-ONLY (no implementation in this release)
**Breaking:** No (planning doc adds zero source changes)
**Prerequisite:** v5.8.5 shipped (Bb.1 — bootstrap seed refresh).
**Estimated planning effort:** 2–4 hours (this PLAN + PROMPT).
**Estimated implementation effort (if approved):** 6–12 hours
across 1–2 focused sessions, gated on a real demand signal.

---

## Goal

Quantify the Win32 (i686) ABI gap that v5.8.4's Wb.2 closure
left behind, decide whether to support 32-bit Windows at all,
and lay out the implementation surface if the answer is yes.
This release writes only `PLAN.md` + `PROMPT.md`; no code edits,
no version bump's worth of compiler/runtime changes.

The user surfaced this question during v5.8.5 review:

> "this is set for win64 like hardcoded but why not win32?"

Short answer: v5.8.4's `__mn_host_is_win64()` **claims** to detect
Win64, but **reads `_WIN32`** — a macro defined for both 32-bit
and 64-bit Windows builds. On `x86_64-w64-mingw32` (Mapanare's
actual Windows target) `_WIN32` and `_WIN64` are both defined and
the function returns 1 correctly. On `i686-w64-mingw32` (the
hypothetical 32-bit Windows target) `_WIN32` is defined but
`_WIN64` is not — the function still returns 1, triggering Win64
sret/sarg ABI rules which are wrong for i686 cdecl.

This is a latent-correctness gap. Mapanare ships only the
x86_64-w64-mingw32 binary; nobody cross-compiles for i686 today.
But the naming + the misleading macro choice mean a future
contributor wiring up `i686-w64-mingw32` would silently get a
broken ABI emission. This release plans the closure.

---

## Context — what the Win64 path does today

After v5.8.4 (Wb.2) + v5.8.5 (Bb.1), the self-hosted emitter is
target-aware via `EmitState.is_win64`:

```mapanare
// mapanare/self/emit_llvm.mn:5885 (concatenated copy at mnc_all.mn:20783)
let host_w64: Int = __mn_host_is_win64()
if host_w64 != 0 {
    st.is_win64 = true
}
```

The C-runtime side at `runtime/native/mapanare_core.c:2987`:

```c
MN_EXPORT int64_t __mn_host_is_win64(void) {
#ifdef _WIN32
    return 1;
#else
    return 0;
#endif
}
```

`_WIN32` is the load-bearing macro. From the MSVC + MinGW
documentation:

| Macro | i686-w64-mingw32 | x86_64-w64-mingw32 | Linux/macOS |
|---|---|---|---|
| `_WIN32` | defined | defined | undefined |
| `_WIN64` | undefined | defined | undefined |
| `__i386__` | defined | undefined | architecture-dependent |
| `__x86_64__` | undefined | defined | architecture-dependent |

So `__mn_host_is_win64()` returns 1 on **both** Windows
architectures, but the ABI rules it triggers are correct for
**only** x86_64.

The Python emitter (`mapanare/emit_llvm_text.py:1226`) has the
same pattern with the same gap:

```python
@property
def _win64(self) -> bool:
    return "windows" in self._triple
```

`"windows" in "i686-w64-windows-gnu"` is also true. Same
latent-correctness gap; same x86_64-only surface today.

What `is_win64=true` triggers downstream:
- `mapanare/self/emit_llvm.mn::declare_runtime_fn` (line ~378):
  aggregate-by-value params > 8 bytes get rewritten to `ptr`
  via `win64_rewrite_decl_params`; aggregate returns > 8 bytes
  become `void` with a leading `ptr sret(<T>)` parameter.
- `emit_rt_call` / `emit_rt_call_void` (line ~558): aggregate
  args at call sites get rewritten via `win64_sarg_rewrite_args`
  + `win64_sarg_advance_state` (alloca + store + ptr); aggregate
  returns alloc'd locally as sret destination.
- `abi_classify_return_sret` (line ~2243): hardcoded triple
  `"x86_64-w64-windows-gnu"` when `st.is_win64` is true.
- Module header: `target triple = "x86_64-w64-windows-gnu"` when
  `st.is_win64` is true.

For i686 cdecl, **none** of these are right.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **We.1** | LOW (no demand signal yet) | Decide: support `i686-w64-mingw32` (Win32) as a build target, or document the gap as an explicit non-goal. If yes: rename `is_win64` → `is_windows` + add an arch field; rename `__mn_host_is_win64()` → `__mn_host_windows_arch()` (or split into `__mn_host_is_windows()` + `__mn_host_arch_bits()`); port the i686 ABI classifier (cdecl, 32-bit pointers, `_BYREF_BYTES` recompute, no `noalias` on aggregate returns); update `target datalayout` + `target triple`; add an i686 release pipeline; refresh seed for the new C-runtime export name. | Decision: 1h. Implementation: 6–12h. |
| **We.2** | LOW | Update `mapanare/emit_llvm_text.py` Python emitter mirror so the bootstrap-stage1-builds-stage2 cycle on i686 produces the same ABI shape as the self-hosted emitter does on i686. Mirrors the v5.8.4 Wb.2 closure pattern. | 2-3h. Tightly coupled to We.1. |
| **We.3** | LOW | Audit `runtime/native/mapanare_*.c` for any code paths that assume 64-bit pointers (`uintptr_t` is 32-bit on i686; `size_t` is `unsigned long` on Linux but `unsigned int` on i686-mingw). Add CI for i686 cross-compile so the warnings surface. | 2-4h. |

## What this release decides

### Decision 1: ship We.1?

**Recommendation: NO, until a real demand signal arrives.**
Reasoning:
- Mapanare's stated targets in `CLAUDE.md` §"GPU / WASM / Mobile":
  `aarch64-apple-ios`, `aarch64-linux-android`, `x86_64-linux-android`.
  Win32 (i686) is not in the list.
- Modern Windows is essentially all 64-bit. 32-bit Windows 10 was
  discontinued at the v22H2 servicing channel; Windows 11 is
  64-bit only. Microsoft's own data shows < 2% of active Windows
  installs run a 32-bit OS as of 2025.
- The current Win64 path produces correct IR for the only
  Windows target Mapanare actually ships
  (`x86_64-w64-mingw32`); the gap is *purely* latent — no user
  is hitting it.
- Implementation cost (~10h) is non-trivial against zero
  observed demand.

**If someone needs i686-w64-mingw32 in the future**, the v5.8.6
PROMPT.md is ready to be picked up. Until then, this PLAN +
PROMPT exist as a parked design doc.

### Decision 2: rename now, even without We.1?

**Recommendation: NO.** A rename without changing the underlying
behavior would be churn. The misleading-macro-name issue is
purely cosmetic until i686 is actually a target. Bundle the
rename with the implementation when it lands.

### Decision 3: document the gap?

**YES.** Add a paragraph to `docs/known_issues.md` flagging
We.1 as a latent gap, and add an explicit non-goal line to
`mapanare/targets.py` near the Windows target definition. This
release does that documentation only — no other source changes.

Wait — this is a planning-only release. The "documentation"
edit would be a source change. Per `What does NOT ship` rule:
**no source changes.** The known_issues.md note rides with the
v5.8.5 commit if not done already; if the user wants the gap
flagged in `docs/known_issues.md`, do it as a tiny v5.8.5.1 doc
edit or fold into v6.0 prep.

---

## What ships in v5.8.6

- `docs/roadmap/v5/v5.8.6/PLAN.md` (this file)
- `docs/roadmap/v5/v5.8.6/PROMPT.md` (execution prompt for We.1
  if/when approved)

## What does NOT ship

- `VERSION` bump. v5.8.6 is a planning-only artifact — version
  stays at 5.8.5 until We.1 actually implements.
- Source code changes (mapanare/, runtime/, scripts/).
- README badge updates.
- CHANGELOG entry (no user-visible change yet).
- CLAUDE.md release-history bullet (no shipped release yet).
- Seed refresh.
- Tests (the i686 path has no tests today; tests come with the
  We.1 implementation).

## Why no version bump

`docs/roadmap/v5/CLOSEOUT_ARC.md` and the SemVer policy in
`CHANGELOG.md`'s header link both treat the version number as
"shipped artifacts." A PLAN+PROMPT pair is research/design
output. The repo has prior precedent for planning-only releases
(see the v5.5.3 entry in CLAUDE.md: "**Self-hosted coroutine
emission design (docs-only).** Zero code changes. Ships one
480-line `DESIGN.md`...") — but those got a version bump
because the design doc was committed and tagged. v5.8.6 follows
the v5.5.3 pattern: PLAN+PROMPT artifacts are committed under
`docs/roadmap/v5/v5.8.6/`, but **without** a version bump,
because the user explicitly framed this as "create plan and
prompt for win32" — not "ship a release." If we ship a release
later that picks up We.1, that release gets the version number;
if We.1 never ships, this directory stays as a frozen design.

---

## Risk register (for the PLANNING decision, not the
   implementation)

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Writing a PLAN we never execute creates documentation rot. | Acceptable: PLAN+PROMPT pairs cost ~3 hours; they're low-rot if frozen with a clear "PLANNING-ONLY" status banner. The repo already has stale plan docs (e.g. v5.5.3 design doc shipped with no follow-up). |
| R2 | The PLAN's "support i686?" decision changes once Mapanare gets distribution data. | Acceptable: re-read the PLAN at that point; the framework + cost estimate stay valid even if the decision flips. |
| R3 | Win32 work, when implemented, breaks the v5.8.4/.5 Win64 path. | Mitigated in PROMPT.md: We.1 must be feature-flagged (`is_windows` + arch) so Win64 stays the default for `x86_64-w64-mingw32`. Goldens 66/66 + Windows fixed-point are the regression gates. |

---

## Notes on i686 cdecl vs Win64 (technical reference)

This is the substantive ABI difference table. PROMPT.md cites
it for the implementation surface.

| Aspect | x86_64-w64-windows-gnu (Win64) | i686-w64-windows-gnu (Win32 cdecl) |
|---|---|---|
| Pointer size | 64 bits | 32 bits |
| Register args | RCX, RDX, R8, R9 (4 ints) + XMM0–3 (4 floats) | None (all on stack, cdecl) |
| Return: int ≤ 8 B | RAX | EAX (32-bit), EAX:EDX (64-bit packed) |
| Return: float | XMM0 | ST(0) (x87 stack) |
| Return: struct ≤ 8 B | RAX | EAX:EDX (packed into 2 registers) |
| Return: struct > 8 B | hidden ptr in RCX (sret) | hidden first arg (caller-allocated) |
| Stack alignment | 16 B at call | 4 B at call (16 B at frame for SSE) |
| Caller cleanup | yes (cdecl-style) | yes (cdecl) |
| `__attribute__((sysv_abi))` available? | yes (compiler intrinsic) | n/a |
| `__attribute__((stdcall))` | n/a (Win64 has one cc) | yes (`@stdcall`, callee cleans up) |
| LLVM IR `target datalayout` | `e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128` | `e-m:x-p:32:32-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:32-n8:16:32-a:0:32-S32` |
| LLVM IR `target triple` | `x86_64-w64-windows-gnu` | `i686-w64-windows-gnu` |
| `noalias` on aggregate ptr returns | accepted | accepted (rare in cdecl-returned aggregates anyway) |
| sret semantics in IR | `void @F(ptr sret(<T>) %retbuf, ...)` | same shape, but caller-allocates and passes-as-first-arg without the `sret(...)` attribute mattering for cdecl ABI legality (LLVM still honors the attribute as a hint for SROA) |
| `_BYREF_BYTES` threshold | 64 (per `emit_llvm_text.py:1244`) | unclear — needs empirical fit; cdecl is happy passing larger structs by value than Win64 sret tolerates |
| `MnString {ptr,i64}` (16B) | passed as `ptr` (sarg) | passed as `{ptr, i64}` value (cdecl is fine with 8-byte+8-byte stack passing) |

The implication for We.1: i686 needs an entirely separate ABI
classifier path — not just a "Win64 with smaller pointers"
variant. The Wb.2 closure architecture (`is_win64` flag +
target-aware `declare_runtime_fn` + target-aware
`emit_rt_call`) is the right scaffold; we extend it to a
`{is_windows: Bool, win_arch: Int}` pair (or equivalent enum).

PROMPT.md spells out the full implementation surface.
