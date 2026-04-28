# v5.8.7 — Phase 0 empirical probe findings (Da.1 prereq)

**Status:** COMPLETE — written from user's Apple Silicon Mac.
**Date:** 2026-04-27
**Author:** Claude Sonnet 4.6 under user direction
**Source artifacts:**
- mnc-stage1 binary (built locally via `python scripts/build_stage1.py`,
  STRIP=0 to retain debug symbols)
- `mapanare/self/main.ll` — 1,994,027-line emitted IR
- `/tmp/stage1_stderr.log` — captured crash stderr
- clang ground-truth IR + arm64 assembly probes via `/opt/homebrew/opt/llvm@18`

This document is the spec for v5.8.8 Da.1 implementation. It **refines
the v5.8.8 PLAN's hypothesis**: the PLAN assumed the bug was
SysV-vs-AAPCS64 by-value *parameter* divergence; reality is the bug is
**aggregate-by-value return** for runtime functions returning > 16 B.
Implementation surface in §8 differs accordingly.

---

## 1. Environment

| Field | Value |
|---|---|
| OS | macOS 26.3 (build 25D125) |
| Kernel | Darwin 25.3.0 |
| Chip | Apple M2 Pro |
| Arch | arm64 |
| Apple clang (system) | 17.0.0 (clang-1700.6.3.2) — `/usr/bin/clang` |
| Homebrew LLVM | 18.1.8 — `/opt/homebrew/opt/llvm@18/bin/{clang,llc,llvm-as}` |
| Python | 3.12.13 (via pyenv) |
| Mapanare repo | branch `dev`, HEAD `5c5636fd` (v5.8.7) |
| VERSION file | `5.8.7` |

The probe used Homebrew clang-18 + llc-18 for AAPCS64 vs SysV
ground-truth diffs (Apple Clang 17 disagrees with Homebrew Clang 18 on
nothing relevant for this analysis, but using the same toolchain
Mapanare links against eliminates a variable).

---

## 2. Build + binary identity

`python scripts/build_stage1.py` succeeded cleanly on Mac in ~30 s:

```
[1/6] Generating LLVM IR from mapanare/self/*.mn ...
  IR: 1994027 lines -> mapanare/self/main.ll
[2/6] Post-processing IR (external linkage for entry points) ...
[3/6] Compiling LLVM IR -> object code ...
  Object: 4090824 bytes (clang -O2)
[4/6] Compiling C runtime ...
[5/6] Compiling C main wrapper ...
[6/6] Linking mnc-stage1 ...
  Binary: mapanare/self/mnc-stage1 (3812520 bytes)
```

```
$ file mapanare/self/mnc-stage1
mapanare/self/mnc-stage1: Mach-O 64-bit executable arm64

$ otool -L mapanare/self/mnc-stage1 | head -3
mnc-stage1:
  /usr/lib/libSystem.B.dylib
  /System/Library/Frameworks/Metal.framework/...
```

Confirms: native arm64 Mach-O, links against macOS system libs +
Metal/Foundation. No cross-compile shenanigans.

The text-patch in `scripts/build_stage1.py:122-136` ran (sys.platform
== "darwin"; arch == "arm64") and rewrote the triple from
`x86_64-unknown-linux-gnu` → `aarch64-apple-macos`, plus the
datalayout from the Linux x86 form to
`e-m:o-i64:64-i128:128-n32:64-S128-Fn32`. **Inspecting the resulting
`main.ll` confirms the function signatures retained their SysV-shaped
aggregate-return form** — this is the bug.

---

## 3. Reproducer

```
$ ./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2.ll
FATAL: __mn_list_push received corrupted list
       (data=0x40 len=-9223372036853859795 cap=4350393200
        esz=-9223372036854775784)

[CRASH] SIGABRT during compile at mapanare/self/mnc_all.mn
0   mnc-stage1     mn_crashdiag_handler + 720
1   libsystem_platform.dylib  _sigtramp
2   libsystem_pthread.dylib   pthread_kill
3   libsystem_c.dylib         abort
4   mnc-stage1     __mn_list_push + 672
5   mnc-stage1     lexer__tokenize + 740
...
$ echo $?
134

$ wc -l /tmp/stage2.ll
       0
```

**Identical to the publish.yml run #41 failure** documented in v5.8.7
SESSION_REPORT. The MnList struct fields are corrupted at the moment
of the push:

| Field | Observed value | Hex / interpretation |
|---|---:|---|
| `data` | `0x40` | 64 — small constant, not a heap pointer |
| `len`  | `-9223372036853859795` | `0x80000000…` — pointer-shaped value read as i64 |
| `cap`  | `4350393200` | `0x1037caa30` — looks like lower 33 bits of an arm64 heap pointer |
| `esz`  | `-9223372036854775784` | `0x80000000…0x18` — sentinel-like |
| `managed` | (not printed) | — |

The pattern (`0x40` then `0x80000000…` then heap-pointer-shaped) is
consistent with **uninitialised register contents being read as
struct fields after a return-ABI mismatch**, not with random heap
corruption. See §5 for the structural explanation.

---

## 4. lldb capture — what worked, what didn't

`lldb --batch -s <script>` with breakpoint on `__mn_list_push`
followed by command stream did not produce post-stop register/frame
output; the batch driver appears to disconnect after `run` once the
breakpoint hits. This is a known wart of lldb's batch mode for
breakpoint-then-action scripts.

Workaround attempts (recorded for v5.8.9+ tooling work):
- `breakpoint command add 1 ... DONE` — script source loads, but
  commands don't fire on hit under `--batch`.
- `breakpoint set --name abort` — same hang.
- Conditional breakpoint with `list->cap > 100000000 || ...` — same.

**This did not block the analysis.** The crash output (§3) plus IR
inspection (§5) plus clang ground-truth (§6) gave more reliable
evidence than register dumps would have. lldb capture is left as
optional v5.8.8+ tooling polish.

---

## 5. IR inspection — root cause

### 5.1 `__mn_list_push` declaration (the crashing callee)

```llvm
declare void @__mn_list_push(ptr, ptr) nounwind
```

Two pointers. Not the bug. AAPCS64 + SysV agree on `ptr` parameter
passing — both go in x0, x1 (or rdi, rsi).

### 5.2 `__mn_list_push` call sites

```llvm
call void @__mn_list_push(ptr %t0.a.1, ptr %ea.62)
call void @__mn_list_push(ptr %t0.a.1, ptr %ea.85)
call void @__mn_list_push(ptr %visited.addr, ptr %ea.10)
call void @__mn_list_push(ptr %t1.a.4, ptr %ea.183)
```

Pointer to MnList + pointer to element. Not the bug.

### 5.3 `__mn_list_new` declaration — **THE BUG**

```llvm
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
```

Returns a **first-class LLVM aggregate** of 5 × 8 B = 40 B. The C
runtime's signature is:

```c
typedef struct MnList {
    char   *data;
    int64_t len;
    int64_t cap;
    int64_t elem_size;
    int64_t managed;
} MnList;  /* 40 bytes */

MN_EXPORT MnList __mn_list_new(int64_t elem_size);
```

clang's ground-truth lowering for **both** AAPCS64 (Apple) and SysV
(Linux x86_64) is the same:

```llvm
declare void @__mn_list_new(
    ptr dead_on_unwind writable sret(%struct.MnList) align 8,
    i64 noundef
)
```

**Both ABIs use the sret pattern** — caller allocates 40 B, passes
the address as a hidden first argument; callee writes there. This is
canonical for > 16 B aggregate returns.

Mapanare's emitter chose the *first-class aggregate return* form.
This shape works on x86_64 SysV by accident: LLVM's x86_64 backend
identifies 40-byte aggregates as "memory class" per AMD64 SysV
§3.2.3 and silently rewrites the call to use sret-style memory
return. The IR is "wrong" but the lowering compensates.

**On AAPCS64, LLVM does NOT compensate the same way.**

### 5.4 `__mn_list_new` call sites in IR

```llvm
%ln.0 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 16)
%ln.3 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 16)
%ln.5 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 16)
```

Caller expects to receive 5 i64-sized values "as the call's result
SSA." LLVM arm64 backend lowers this as **register-pair return** —
reads x0..x4 after the `bl` instruction. See §5.5.

### 5.5 arm64 assembly produced — proof of the divergence

Compiling a synthetic test case that mirrors Mapanare's IR shape:

```llvm
target triple = "aarch64-apple-macos"
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64)
declare void @__mn_list_push(ptr, ptr)

define void @caller(i64 %sz, ptr %elem) {
  %lst = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 %sz)
  %tmp = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} %lst, ptr %tmp, align 8
  call void @__mn_list_push(ptr %tmp, ptr %elem)
  ret void
}
```

Through `llc --mtriple=aarch64-apple-macos -O0`:

```asm
_caller:
    stp  x29, x30, [sp, #48]
    bl   ___mn_list_new
    mov  x9, x0           ; reads field 0 (data) from x0
    mov  x8, x1           ; reads field 1 (len) from x1
    ldr  x1, [sp]         ; ??? loads from prior stack
    str  x9, [sp, #8]     ; spills only field 0 to local
    str  x8, [sp, #16]    ; spills only field 1 to local
    bl   ___mn_list_push  ; passes the partially-initialised local
```

LLVM's arm64 backend lowers this aggregate return as **only x0 and x1
are valid** — fields 2–4 are NOT being read out of return registers.
The `ldr x1, [sp]` line is reading uninitialised stack content. Then
fields 2–4 of the local copy are simply never assigned.

Compare with the canonical sret form for an equivalent IR shape:

```llvm
%struct.MnList = type { ptr, i64, i64, i64, i64 }
declare void @__mn_list_new_correct(ptr sret(%struct.MnList) align 8, i64)

define void @caller_correct(i64 %sz) {
  %lst = alloca %struct.MnList, align 8
  call void @__mn_list_new_correct(ptr sret(%struct.MnList) align 8 %lst, i64 %sz)
  ret void
}
```

```asm
_caller_correct:
    add  x8, sp, #8                  ; x8 = address of stack alloca
    bl   ___mn_list_new_correct      ; callee writes 40 B to *x8
```

This is the canonical AAPCS64 indirect-result pattern. Caller passes
the destination address in x8; callee writes there.

**The C runtime's `__mn_list_new`, compiled by clang from C source,
returns via x8 indirect (canonical AAPCS64).** When called from
Mapanare's IR using the first-class aggregate form, the caller reads
x0..x4 expecting return data, but the callee wrote to *x8 — caller
gets whatever junk happened to be in x0..x4 at return time.

This **exactly explains the corruption signature** in §3:
- `data=0x40` — leftover x0 from some earlier calculation
- `len=-9223…` — leftover x1 (looks like a kernel/TLS pointer)
- `cap=…` — leftover x2 (looks like a lower-half heap pointer)
- `esz=-9223…` — leftover x3

---

## 6. clang AAPCS64 ground-truth (§B.4 of v5.8.7 PROMPT)

**Per-target IR comparison for the same C source** (40-byte struct
returned by value, 40-byte struct passed by value):

```c
typedef struct MnList {
    char *data; int64_t len, cap, esz, mgd;
} MnList;
extern MnList __mn_list_new_C(int64_t esz);
extern void   __mn_list_push_C(MnList *l, const void *e);
extern void   use_list(MnList l);

void caller_ret(int64_t esz, const void *e) {
    MnList l = __mn_list_new_C(esz);
    __mn_list_push_C(&l, e);
}
void caller_param(void) { MnList l = {0}; use_list(l); }
```

| Convention | AAPCS64 (aarch64-apple-macos) | SysV (x86_64-unknown-linux-gnu) |
|---|---|---|
| 40 B return | `sret(%struct.MnList) align 8` (hidden 1st arg) | `sret(%struct.MnList) align 8` (hidden 1st arg) |
| 40 B by-value param | **`ptr noundef`** (caller alloca + memcpy + ptr) | **`ptr noundef byval(%struct.MnList) align 8`** |

**Returns: AAPCS64 = SysV** (both use sret). `_classify_aapcs64` in
`mapanare/abi.py` is correct.

**Parameters: AAPCS64 ≠ SysV.** AAPCS64 passes by *implicit pointer*
(caller alloca + memcpy + pass ptr); SysV uses LLVM's `byval` attribute
for stack passing. This *is* the divergence the v5.8.8 PLAN's
hypothesis described — but it is **not** the cause of the observed
crash.

### 6.1 16 B aggregate returns (`{ptr, i64}` MnString) are fine

Verified separately: `declare {ptr, i64} @__mn_str_concat(...)` lowers
correctly on AAPCS64 — values returned in x0, x1 directly. clang's
C-equivalent uses `[2 x i64]` shape; both work.

---

## 7. Hypothesis — confirmed and refined

### 7.1 What the v5.8.8 PLAN claimed

> For aggregates > 16 B returned by value: both ABIs use a hidden
> first-arg pointer (SysV: explicit `sret`; AAPCS64: `x8` indirect
> result register, IR-level equivalent). **No bug.**
>
> For aggregates > 16 B passed BY VALUE: SysV passes on the stack;
> AAPCS64 passes BY REFERENCE (caller copies struct to a temporary,
> passes the pointer). **REAL DIVERGENCE.**

### 7.2 What is actually true

**The PLAN's claim about returns is wrong.** The IR-level equivalence
the PLAN assumed only holds when the IR is *already* in sret shape.
Mapanare's IR uses the first-class aggregate return form, which LLVM
arm64 lowers to register-tuple return (x0..x4) — NOT to x8-indirect.

The C runtime, compiled by clang from C source, *does* use x8-indirect
(canonical AAPCS64). The caller↔callee disagreement is the bug.

**The PLAN's claim about parameters is correct in principle but is
not currently triggering**, because:
- All > 16 B aggregate-by-value parameters in the IR are between
  *Mapanare-emitted callers and Mapanare-emitted callees*. Both sides
  use the same first-class aggregate parameter shape; LLVM's arm64
  backend lowers both consistently (it doesn't matter which lowering
  it picks, as long as it's the same on both sides).
- The crash is reached on the *first* call to `__mn_list_new` during
  `lexer__tokenize`, which happens before any Mapanare-level call
  passes a 40 B aggregate by value crosses an ABI boundary.

If we fix only the return bug (this release's scope), the param bug
*may* still surface if any future change introduces a Mapanare↔C call
that passes a > 16 B aggregate by value. None exist today.

### 7.3 Why the bug stayed latent on Linux

`scripts/build_stage1.py:122-136` text-patches the triple from
`x86_64-unknown-linux-gnu` → `aarch64-apple-macos` *after* IR
emission. On Linux (no patch), the IR keeps SysV triple, and LLVM
x86_64 backend's "memory class" rule for > 16 B returns silently
rewrites first-class-aggregate returns to sret-style memory return.
**The IR is "wrong" on Linux too**, just compensated for by the
backend.

On AAPCS64, the LLVM arm64 backend does not have an equivalent
silent rewrite path — it lowers the IR literally as register-tuple
return. The bug surfaces.

---

## 8. Implementation surface — refined for v5.8.8

The v5.8.8 PLAN's Da.1.A-E items are scoped to **parameters**
(`classify_param`, `byref` rewrite). Those items address a real
latent gap, but they do **not** fix the observed crash. This findings
document REFINES the implementation surface as follows:

### 8.1 Da.1.A — `classify_return` integration (NEW emphasis)

`mapanare/abi.py::classify_return` already exists and is correct
(`_classify_aapcs64`: > 16 B → `_SRET`). The gap is that the **emitter
does not consult it** for runtime function declarations and call
sites. Two specific runtime declarations need rewriting:

| Function | Current IR (broken on AAPCS64) | Required IR (canonical) |
|---|---|---|
| `__mn_list_new` | `declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64)` | `declare void @__mn_list_new(ptr sret({ptr, i64, i64, i64, i64}) align 8, i64)` |
| `__mn_str_split` | `declare {ptr, i64, i64, i64, i64} @__mn_str_split({ptr, i64}, {ptr, i64})` | `declare void @__mn_str_split(ptr sret(...) align 8, {ptr, i64}, {ptr, i64})` |

Call sites must change from:
```llvm
%lst = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 16)
```
to:
```llvm
%sret.lst = alloca {ptr, i64, i64, i64, i64}, align 8
call void @__mn_list_new(ptr sret(...) align 8 %sret.lst, i64 16)
%lst = load {ptr, i64, i64, i64, i64}, ptr %sret.lst, align 8
```

Or, if the called value is consumed only as a struct (no extractvalue
chain), keep it on the stack and use the alloca pointer directly.

### 8.2 Da.1.A — emit on ALL targets, not gated on AAPCS64

The clang ground-truth confirms **clang emits sret form on BOTH
AAPCS64 and SysV** for > 16 B returns. Emitting sret-form
declarations unconditionally produces canonical IR on all platforms.
Two upsides:
1. No per-target dispatch needed for return shape — simpler emitter.
2. Linux IR becomes structurally correct (it currently relies on the
   x86_64 backend's silent rewrite, which is a latent fragility).

This **simplifies** the v5.8.8 PLAN's Da.1.A from "add `classify_param`
with 4 ABI branches" to "fix runtime aggregate returns at emission".

### 8.3 Da.1.A — parameter divergence stays scoped, but not load-bearing

The > 16 B by-value parameter divergence (AAPCS64 byref vs SysV
byval) IS real but is **not currently triggering any crash**. Two
options for v5.8.8:

**Option A** — fix returns only (this release's MVP). Mapanare↔C
boundary becomes correct on AAPCS64. Mapanare↔Mapanare by-value
parameter passing stays as-is (consistent on both sides, works on
both ABIs).

**Option B** — also add `classify_param` per the original v5.8.8
PLAN, even though no crash currently triggers, to close the latent
gap proactively. Mirrors v5.8.6 We.1's empirical-but-also-defensive
posture for i686.

**Recommendation: Option A.** Smaller surface; lower regression risk;
the param divergence has no observed bite. Defer to v5.8.9 if a
future change surfaces it. If user prefers defensive closure (v5.8.6
posture), Option B adds maybe ~1.5 h.

### 8.4 Updated Da.1.A-E breakdown

| Item | Original PLAN | Updated based on Phase 0 |
|---|---|---|
| **Da.1.A** | Add `classify_param` to `abi.py` | **Different bug.** Add helpers `is_aggregate_sret_return(ir_ty, target)` + emit sret declarations & call shapes for runtime fns whose C signature returns > 16 B by value. `classify_return` already exists; just consult it. |
| **Da.1.B** | Plumb `target` through `compile_multi_module_mir`, delete text-patch | UNCHANGED. Still required — text-patch is structurally wrong even if returns are fixed. Datalayout still needs target plumbing. |
| **Da.1.C** | Python emitter Apple AArch64 dispatch | NARROWER. Only need to update runtime declaration emission (the loop that emits `declare {ptr, i64, ...} @__mn_list_new(i64)` etc.) to emit sret form. Per-target dispatch is OPTIONAL (sret on all targets is canonical). |
| **Da.1.D** | Self-hosted emitter parallel | NARROWER. Same scope as Da.1.C in `mapanare/self/emit_llvm.mn`. Also: the field `is_apple_aarch64` may not be needed if we go target-agnostic per Da.1.C. |
| **Da.1.E** | New `__mn_host_is_apple_aarch64()` C-runtime export | LIKELY NOT NEEDED. If dispatch is target-agnostic (sret-on-all-targets), the C-runtime export is unnecessary. **Avoids bootstrap seed refresh** (Decision 1 → Option B in v5.8.8 PLAN). |
| **Da.2** | macOS self-compile CI | UNCHANGED. Still load-bearing — without it, future regressions stay latent the same way Da.1 did. |
| **Da.3** | publish.yml re-enable | UNCHANGED. Gated on Da.1 closure. |
| **Da.4** | Bootstrap seed eval | LIKELY NO REFRESH NEEDED if Da.1.E is dropped. |

### 8.5 Affected runtime functions — final list

Two functions to rewrite. Both return `MnList` (40 B) by value:

1. `__mn_list_new(i64 elem_size) -> MnList` — the proximate cause
   of the crash.
2. `__mn_str_split({ptr, i64} s, {ptr, i64} delim) -> MnList` —
   declared but not transitively called from the lexer code path
   that crashes; latent same-bug-shape.

Other MnList-returning runtime fns (`__mn_list_clone`,
`__mn_list_concat`, `__mn_list_str_new`, `__mn_dir_list_strings`,
`__mn_map_keys`, `__mn_stream_collect`, `__mn_list_deep_clone`)
are present in C runtime source but **not declared in the emitted
IR** — they aren't reachable from the self-hosted compiler today.
If/when they become reachable, the same fix applies; the emitter's
sret-on-all-targets policy will cover them automatically.

`__mn_str_replace` returns `{ptr, i64}` (16 B) — fits in registers on
both ABIs. Not affected.

### 8.6 Risk register update

| ID | Risk | Status post-Phase-0 |
|---|---|---|
| Da.R1 | Phase 0 identifies a different root cause than the param-divergence hypothesis. | **REALIZED.** Hypothesis refined; implementation surface updated per §8. |
| Da.R2 | Apple Darwin variadic ABI is also a divergence. | NOT REALIZED. No `__mn_str_format` / `__mn_str_concat` variadic shape in the IR. `__mn_str_concat` declared as fixed 2-arg `{ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64})`. Skip variadic work in v5.8.8. |
| Da.R3 | Linux x86_64 SysV regression. | LOW RISK. Sret-form returns are what clang emits anyway — strictly more canonical. Will validate by byte-identical IR diff modulo the canonicalised runtime decls. |
| Da.R6 | Apple datalayout in `targets.py` is wrong. | Not realized. `e-m:o-i64:64-i128:128-n32:64-S128-Fn32` matches Apple Clang 17's emission. |

---

## 9. Open questions (v5.8.8 user-decision before Phase 1)

1. **Option A (returns-only) vs Option B (returns + params).** §8.3.
   Recommendation: A.
2. **Emit sret-form on all targets, or gate on AAPCS64.** §8.2.
   Recommendation: all targets (canonical IR, simpler emitter).
3. **Skip Da.1.E (`__mn_host_is_apple_aarch64`) and Da.4 (seed
   refresh).** §8.4. Recommendation: skip both.

These three "yes" recommendations together collapse the v5.8.8 PLAN
from 8-12 h to **roughly 4-6 h**:
- Da.1.A: 1 h (just consult existing `classify_return` from emitter)
- Da.1.B: 2 h (target plumbing + delete text-patch)
- Da.1.C: 1 h (rewrite runtime decl emission)
- Da.1.D: 1 h (mirror in self-hosted)
- Da.2: 1-2 h (CI job)
- Da.3: 30 min (publish.yml)
- Da.4: ~0 (no seed refresh needed)
- Phase 6 validation: 1 h

---

## 10. Conclusion

The v5.8.7 macOS arm64 SIGABRT is caused by a **return-value ABI
mismatch** between Mapanare's IR (first-class aggregate return) and
the C runtime (canonical AAPCS64 x8-indirect sret). The bug stayed
latent on Linux because LLVM's x86_64 backend silently rewrites
first-class aggregate returns to sret-style memory return per AMD64
SysV's "memory class" rule. LLVM's arm64 backend does not have an
equivalent rewrite, so the bug surfaced the moment the macOS arm64
runner build pipeline was actually exercised in CI (publish.yml
run #41).

The fix is narrower than the v5.8.8 PLAN anticipated: rewrite
`__mn_list_new` and `__mn_str_split` declarations + their call sites
to use sret form, in both `mapanare/emit_llvm_text.py` and
`mapanare/self/emit_llvm.mn`. Plumb the target triple through
`compile_multi_module_mir` and delete the text-patch in
`scripts/build_stage1.py`. Add the macOS self-compile CI job. No new
C-runtime exports; no bootstrap seed refresh.

This document is the spec for v5.8.8 implementation. Phase 1 is
unblocked.
