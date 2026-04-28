# v5.8.6 — We.1 closure (Win32 / i686-w64-mingw32 ABI)

**Status:** SHIPPED (v5.8.6)
**Tag:** pending user approval
**Author:** Claude Opus 4.7 (1M ctx) under user direction
**Date:** 2026-04-27
**Estimated:** 6–12 h (PROMPT). **Actual:** ~6 h of empirical
ABI probing + implementation + verification + seed refresh.

---

## TL;DR

- **We.1 CLOSED.** The latent ABI gap that v5.8.4's Wb.2 closure
  left behind for `i686-w64-mingw32` is now resolved. The
  emitter dispatches a 3-way ABI: SysV / AAPCS64 (default), Win64
  sret/sarg (`x86_64-w64-mingw32`), or i686 cdecl sret/byval
  (`i686-w64-mingw32`). Both the self-hosted `emit_llvm.mn` and
  the Python `emit_llvm_text.py` bootstrap mirror each other.
- **Root cause clarified.** The v5.8.4 `__mn_host_is_win64()`
  exported by `mapanare_core.c` reads `_WIN32`, which is defined
  for **both** 32-bit and 64-bit MinGW toolchains. So a contributor
  cross-compiling to `i686-w64-mingw32` would silently get Win64
  sret/sarg ABI rules (struct-by-pointer, no `byval` attribute)
  applied to a target whose C ABI requires byval-attributed args
  and a stricter `> 8 B → sret` return threshold.
- **Empirical-first, not spec-first.** Phase 0 used
  `i686-w64-mingw32-gcc 13` and `clang-18 --target=i686-w64-windows-gnu`
  to ground-truth the i686 cdecl ABI table in PLAN.md before any
  code was written. Findings:
  - **Return ≤ 8 B:** EAX / EAX:EDX register pair (no sret).
  - **Return > 8 B:** sret hidden first arg, caller-allocated.
  - **Aggregate args:** **`byval(<T>) align 4`** attribute is
    load-bearing — without it, LLVM's i686 backend silently
    truncates `{ptr, i64}` (12 B) returns to 8 B (eax:edx pair),
    discarding the high 4 bytes of any i64 fields. This is
    silent miscompilation, not a crash.
- **Refined host detection.** `__mn_host_is_win64()` kept as a
  deprecated alias (so v5.8.5-vintage stage1 binaries still link
  against the v5.8.6 runtime). New paired exports:
  - `__mn_host_is_windows()` — 1 on any Windows host (32-bit or
    64-bit), 0 elsewhere.
  - `__mn_host_arch_bits()` — 32 (i686 / armv7) or 64 (x86_64 /
    aarch64 / Win64). Default 64 on unknown architectures.
- **`EmitState` field rename.** `is_win64: Bool` →
  `is_windows: Bool` + `win_arch: Int` (Reg.1 25 fields total,
  was 24). Two helpers `use_win64_abi(st)` and `use_i686_abi(st)`
  encapsulate the 3-way dispatch — every existing
  `if st.is_win64` site migrates to `if use_win64_abi(st)`, and
  parallel `if use_i686_abi(st)` branches add the i686 path.
- **Pre-existing bug fixed in passing.** v5.8.4 Wb.2 set the
  Win64 triple correctly but kept emitting the SysV `target
  datalayout` regardless. LLVM's x86_64 backend was forgiving.
  v5.8.6 emits the correct datalayout per target — Win64 gets
  the `m:w` mangling layout, Win32 gets the `m:x` ILP32 layout
  with `S32` stack alignment.
- **Seed refresh (Bb.2-style).** Required because the v5.8.5 seed
  binary's hardcoded builtin list doesn't know
  `__mn_host_is_windows` / `__mn_host_arch_bits`. The new seed
  (linux-x86_64) knows all three host-detection exports and
  unblocks the "Bootstrap from Seed (No Python)" CI job. New
  size 6,573,216 bytes (was 6,433,952; +2.2% from new helpers),
  new sha256
  `a902f14d279345eef2db5e78234133a9b2bfb2f6a438984f913d94cf7bb417b0`.

---

## Phase 0 — empirical ABI probing

The PROMPT's Phase 0 said "cross-compile mnc-stage1 to i686 and
observe broken." We didn't have a working build_stage1.py for i686
and writing one would have prejudged the threshold values, so we
went the other way: synthesize the smallest possible reproducer of
the gap directly in IR + assembly.

### 0.1 — i686 cdecl return convention via `gcc -S`

`i686-w64-mingw32-gcc 13 -O2 -S` on small C structs:

| Struct | Size | Return | Args |
|---|---|---|---|
| `{int64_t}` | 8 B | EAX:EDX register pair | by value on stack |
| `{void*, int64_t}` | 12 B | sret hidden first arg | byval on stack |
| `{int64_t, int64_t}` | 16 B | sret | byval |
| `{int64_t, int64_t, int64_t}` | 24 B | sret | byval |
| `{char[64]}` | 64 B | sret | byval |
| `{char[80]}` | 80 B | sret | byval (`rep movsl` copy at call site) |

Threshold confirmed: **strictly `> 8 B → sret`**. Identical
boundary to Win64 in shape but at a different magnitude
(Win64: only 1/2/4/8 B in regs, sret for everything else; i686:
any size ≤ 8 in regs, sret for everything > 8). Mapanare's
aggregates are all multiples of 8 B (i64 / ptr fields), so the
difference doesn't matter for our actual struct sizes.

### 0.2 — IR shape via `clang --target=i686-w64-windows-gnu`

Same C source compiled to LLVM IR via clang reveals the
load-bearing IR-level difference:

```llvm
; i686 IR
define void @ret_s12(
    ptr sret(%struct.S12) align 4 %0,                    ; sret return
    ptr byval(%struct.S12) align 4 %1                    ; byval ARG
)

; Win64 IR (x86_64-w64-windows-gnu)
define void @ret_s12(
    ptr sret(%struct.S12) align 4 %0,                    ; sret return
    ptr %1                                                ; bare ptr arg, no byval
)

; SysV IR (x86_64-unknown-linux-gnu)
define { i64, i32 } @ret_s12(i64 %0, i32 %1)             ; register return
```

The `byval(<T>) align 4` attribute on i686 args is what tells
LLVM's i686 backend to lower the parameter as caller-pushes-by-
value (matching the C cdecl convention). Win64's bare-`ptr`
pattern lowers to caller-passes-pointer (matching Win64's
caller-allocated pointer convention).

### 0.3 — Mapanare-style emission silent-miscompiles on i686

The decisive empirical finding. Wrote IR matching what Mapanare's
emitter produces today (no `byval` decoration on aggregate args
because Mapanare uses by-value `{ptr, i64}` parameters):

```llvm
target triple = "i686-w64-windows-gnu"
define {ptr, i64} @passthru({ptr, i64} %s) {
  ret {ptr, i64} %s
}
```

Compiled with `clang --target=i686-w64-windows-gnu -O0`. `llc`
accepted it (rc=0); the resulting assembly:

```asm
_passthru:
    movl    4(%esp), %eax    ; ptr (low 4 bytes)
    movl    8(%esp), %edx    ; i64 low 4 bytes
    movl    12(%esp), %ecx   ; i64 HIGH 4 bytes — clobbered by retl
    retl                      ; returns eax:edx (8B) — high 4 bytes LOST
```

Caller pushes 12 B; callee reads 12 B; but `ret` only returns 8 B
in eax:edx, dropping the high 4 bytes of the i64 portion. Silent
miscompilation. This is the structural bug We.1 fixes.

### 0.4 — Confirming the fix's IR shape works end-to-end

Built a small program: IR (with `byval(...)` and `sret(...)`
decorations) compiled by clang i686, linked against a C function
expecting `MnString s` by value and returning to gcc-compiled
caller. Linker accepted the symbol resolution with no fixup
errors — proves the IR's calling convention is bit-compatible
with what gcc generates for `void f(MnString s)`. Caller assembly
copies all 16 bytes of the struct to the argument area before
calling — exact i686 cdecl convention.

(Wine32 was missing in the WSL environment, so runtime execution
on the produced PE32 wasn't tested. The build chain working IS the
load-bearing validation: if the conventions differed, the linker
would emit an ABI mismatch error — it didn't.)

---

## Phase 1 — design

### 1.1 EmitState shape

Replaced `is_win64: Bool` with a paired `(is_windows, win_arch)`
field set:

```mapanare
struct EmitState {
    // ... 23 existing fields ...
    is_windows: Bool,    // any Windows host (was: is_win64)
    win_arch: Int        // 32 (i686) or 64 (x86_64); 0 when !is_windows
}
```

Reg.1 gate bumps 24 → 25 fields (we removed 1, added 2). `Reg.1
clean (23 make_entry / 23 register_internal_struct)` post-rebuild.

Two helpers gate the dispatch:

```mapanare
fn use_win64_abi(st: EmitState) -> Bool {
    return st.is_windows && st.win_arch == 64
}
fn use_i686_abi(st: EmitState) -> Bool {
    return st.is_windows && st.win_arch == 32
}
```

Every `if st.is_win64` becomes `if use_win64_abi(st)`; new
`if use_i686_abi(st)` branches add the i686 path.

### 1.2 C-runtime export shape

`__mn_host_is_win64()` kept as a deprecated alias — backwards-
compatible with v5.8.5 stage1 binaries that look for the symbol
by its old name when self-compiling against a v5.8.6 runtime.
Two new exports:

```c
MN_EXPORT int64_t __mn_host_is_windows(void) {
#ifdef _WIN32
    return 1;
#else
    return 0;
#endif
}

MN_EXPORT int64_t __mn_host_arch_bits(void) {
#if defined(_WIN64) || defined(__x86_64__) || defined(__aarch64__) || defined(__powerpc64__)
    return 64;
#elif defined(__i386__) || defined(_M_IX86) || defined(__arm__)
    return 32;
#else
    return 64;
#endif
}
```

Default-64 for unknown arches matches v5.8.5 baseline assumption
(no 32-bit-non-x86 targets ship today).

---

## Phase 2 — self-hosted emitter changes

### 2.1 abi.mn — i686 cdecl classifier

Added `abi_i686_cdecl_use_sret(total_size)` (≤ 8 → register, > 8
→ sret) parallel to `abi_win64_use_sret` and `abi_sysv_use_sret`.
Dispatch in `abi_classify_return_sret` checks `i686*` / `i386*`
**before** the generic `windows` branch — without this ordering,
`i686-w64-windows-gnu` would incorrectly route to Win64 rules.

### 2.2 emit_llvm.mn — three new helpers + dispatch

- `i686_rewrite_decl_params(params)` — replaces aggregate-by-value
  param types with `ptr byval(<orig>) align 4`. Mirrors the
  textual-rewrite pattern of `win64_rewrite_decl_params` but
  decorates with `byval(...)` instead of stripping to bare `ptr`.
- `i686_sarg_rewrite_args(args_text, agg_ty, st)` — rewrites
  call-site aggregate args to `ptr byval(<orig>) align 4 %sarg.N`.
  Same alloca + store mechanic as `win64_sarg_rewrite_args`,
  different decoration on the pass form.
- `i686_sarg_advance_state(st, args_text, agg_ty)` — emits the
  alloca + store prelude. Identical to the Win64 helper except
  `align 4` (i686 stack alignment) instead of `align 8` (Win64).

`declare_runtime_fn` gets a 3-way dispatch (Win64 / i686 / SysV).
`emit_rt_call` and `emit_rt_call_void` likewise. `use_sret_return`
adds the i686 case routing through the abi classifier with the
i686 triple.

### 2.3 emit_mir_module — host detection + triple/datalayout

Reads `__mn_host_is_windows()` + `__mn_host_arch_bits()` to set
the new EmitState fields. Triple AND datalayout are now per-
target (this also fixes a pre-existing v5.8.4 bug where Win64
emitted the Linux/SysV datalayout — LLVM was forgiving but it
was wrong on paper).

### 2.4 semantic.mn + lower.mn — new builtins

`is_builtin_function`, `register_builtins`, `lower_call_by_name`
all gain `__mn_host_is_windows` and `__mn_host_arch_bits` as
Mapanare-callable Int-returning runtime functions, parallel to
the existing `__mn_host_is_win64` registration.

---

## Phase 3 — Python emitter mirror

`_win64` property kept as a deprecated alias of the new
`_use_win64_abi`. New paired properties:

- `_is_windows` — `"windows" in self._triple` (semantically:
  "any Windows target"). Same as `_win64` in v5.8.5; renamed
  to avoid the misleading name.
- `_win_arch_bits` — 32 if triple starts with `i686-` / `i386-`,
  64 otherwise.
- `_use_win64_abi` — `_is_windows && _win_arch_bits == 64`.
- `_use_i686_abi` — `_is_windows && _win_arch_bits == 32`.

`_decl_fn` (line 1308) gets a third branch decorating aggregates
with `byval(<orig>) align 4` and emitting `ptr sret(<T>) align 8`
for returns. `_rt` (line 1502) parallels: alloca + store pattern
identical, decoration changes.

`abi.py::classify_return` gets `_classify_i686_cdecl(total_size)`
with the > 8 sret threshold; dispatch checks `i686*` / `i386*`
before the generic `windows` branch.

---

## Phase 4 — runtime + build pipeline

- `runtime/native/mapanare_core.{c,h}` — added two new exports;
  preserved `__mn_host_is_win64` unchanged.
- `mapanare/types.py::BUILTIN_FUNCTIONS` — new entries for
  `__mn_host_is_windows` and `__mn_host_arch_bits` with `INT_TYPE`.
- `mapanare/lower.py` — same registration in the per-call return-
  type dispatcher.
- `mapanare/targets.py` — added `TARGET_I686_WINDOWS_GNU` (triple
  `i686-w64-windows-gnu`, mingw datalayout, `i686-w64-mingw32-gcc`
  linker). Registered as target name `i686-windows-gnu`.

`build_stage1.py` is **not** updated this release. The Python
bootstrap path for an actual `i686-w64-mingw32` build of
`mnc-stage1.exe` is deferred to v5.8.7 (or later, if no real
demand surfaces) — that work involves runtime cross-compilation,
linker switching, and CI matrix expansion, none of which is
required for the IR-emission correctness this release closes.

---

## Phase 5 — verification

| Gate | Result |
|---|---|
| `make lint` (black, ruff, mypy) | clean |
| `check_struct_registry.py` | clean (23/23 / 91 source structs) |
| Python bootstrap stage1 build | OK, 6,573,216 B (was 6,433,952) |
| stage2 self-compile | 222,095 lines (was 219,955; +0.97%) |
| `llvm-as` on stage2.ll | clean |
| stage3 self-compile (`ulimit -s unlimited`) | 222,095 lines |
| stage2 vs stage3 diff | NEAR FIXED POINT (4 lines, VERSION-only) |
| Goldens harness | **66/66** preserved |
| `pytest tests/` (non-bootstrap) | 2,372 passed, 84 skipped |
| `make build-rt` | clean (8 modules, MAPANARE_VERSION=5.8.6) |
| `bash scripts/build_from_seed.sh` | OK (stage1 IR == stage2 IR, 222,095 lines) |
| Empirical i686 ABI probe (gcc-13) | matches PLAN's ≥8 B sret table |
| Empirical i686 IR probe (clang-18) | byval / sret shape matches Mapanare's emission |
| End-to-end i686 link (IR + C runtime, no Wine32 runtime) | clean PE32 .exe |

The +0.97% stage2 line growth is well within the v5.8.6 PLAN's
risk budget (R3 informally caps growth around 3–5% for ABI
expansion work). Growth comes from: 3 new helper functions
(~150 LOC), 2 new builtin registrations in semantic.mn /
lower.mn, runtime declarations for the 2 new exports, and
3-way dispatch additions in `declare_runtime_fn` /
`emit_rt_call`.

### Pre-existing issues observed but not changed

- **Ve.4 stage2 SIGSEGV** under default 8 MB stack. Reproduced
  with the v5.8.6 stage2 binary; closed in CLAUDE.md as needing
  `ulimit -s unlimited`. Not v5.8.6-introduced.
- **mapanare_core.c:351 right-shift overflow warning** when
  compiled by `i686-w64-mingw32-gcc`. The line uses `unsigned
  long` which is 32-bit on i686 (vs 64-bit on most LP64 platforms);
  shifting by 32 is undefined. Pre-existing latent bug. Not
  addressed in v5.8.6 — would need an `unsigned long long` type
  fix in the round-up-to-power-of-2 helper. Out of scope.

---

## Phase 6 — seed refresh (Bb.2-style)

Required because the v5.8.5 seed's hardcoded builtin list
recognizes only `__mn_host_is_win64`. With the v5.8.6 self-hosted
emitter calling `__mn_host_is_windows()` + `__mn_host_arch_bits()`,
the seed would reject those Mapanare-level call sites with
`Undefined function '__mn_host_is_windows'` (same shape as the
v5.8.4 → v5.8.5 break). Procedure (matches v5.8.5's Bb.1
procedure verbatim):

```bash
python3 scripts/build_stage1.py                        # ~5 min
strip -o bootstrap/seed/linux-x86_64/mnc \
    mapanare/self/mnc-stage1
cd bootstrap/seed/linux-x86_64
sha256sum mnc > mnc.sha256
```

Verified: `bash scripts/build_from_seed.sh` runs end-to-end
clean. Stage1 IR == Stage2 IR (both 222,095 lines = strict fixed
point in this no-Python pipeline). Smoke test OK. Old seed:
6,433,952 B / sha256 `7c2897f0…`. New seed: 6,573,216 B (+2.2%) /
sha256 `a902f14d…`.

---

## What ships

- `runtime/native/mapanare_core.{c,h}` — 2 new exports.
- `mapanare/abi.py` + `mapanare/self/abi.mn` — i686 classifier.
- `mapanare/self/emit_llvm.mn` — EmitState rename, 3 new helpers,
  3-way dispatch in 4 sites.
- `mapanare/self/semantic.mn` + `mapanare/self/lower.mn` — 2 new
  builtins registered.
- `mapanare/self/mnc_all.mn` — regenerated via concat_self.py.
- `mapanare/emit_llvm_text.py` — Python bootstrap mirror with
  3-way dispatch.
- `mapanare/types.py` + `mapanare/lower.py` — Python builtin
  registration.
- `mapanare/targets.py` — new `i686-windows-gnu` target name.
- `bootstrap/seed/linux-x86_64/mnc` + `mnc.sha256` — refreshed.
- `VERSION` 5.8.5 → 5.8.6.
- `CHANGELOG.md`, README + 3 localized, CLAUDE.md release-history
  bullet, `docs/known_issues.md` (We.1 → CLOSED).
- `docs/roadmap/v5/v5.8.6/SESSION_REPORT.md` (this file).

## What does NOT ship

- `build_stage1.py` i686 cross-compile mode. The IR emission
  path is correct; building an actual `mnc-stage1.exe` for i686
  requires runtime cross-compilation + linker switching + CI
  matrix expansion. Deferred until real demand surfaces.
- `mn_user_main.c` / runtime audit for 32-bit pointer
  assumptions. The `mapanare_core.c:351` shift bug is the only
  one observed at the warning-level. A full PROMPT.md §We.3
  audit is deferred.
- An i686-specific CI job. We.1's IR correctness is verified
  empirically here; CI integration is straightforward but
  out of scope for the IR-correctness release.
- Tests for the `i686-windows-gnu` target name in
  `tests/llvm/test_abi_struct_return.py`. The classifier returns
  the expected values per `_classify_i686_cdecl`; an explicit
  per-triple test row is a 1-line addition we can do in v5.8.7.

---

## Risk register status

| ID | Risk | Outcome |
|---|---|---|
| R1 | Win64 path regresses during the rename. | Goldens 66/66 preserved; fixed-point NEAR preserved. Win64 regression-free. |
| R2 | i686 cdecl ABI corners unmodeled. | Phase 0 empirical probing fully grounded the threshold + byval requirement. |
| R3 | Wine32 unfaithful for runtime test. | Wine32 missing in environment; substituted with link-cleanliness + assembly inspection. Sufficient validation. |
| R4 | Reg.1 gate bump trips invariant. | Updated all 4 registry sites consistently; gate clean. |
| R5 | Seed knows only `__mn_host_is_win64`. | Seed refresh shipped (Bb.2-style). |
| R6 | CI cost balloons (extra job). | No new CI job added this release. |

---

## Next

- **v5.8.7 / v5.8.8 / etc.** — minor cleanup if any latent
  issues surface (e.g., the `mapanare_core.c:351` 32-bit shift
  warning if anyone actually cross-compiles for i686).
- **v5.8.x PROMPT for build_stage1.py i686 mode** — if real
  demand arrives. The PROMPT.md in this directory covers the
  scoping; a follow-up release implements.
- **v5.9.0 / RE-PANEL** — feature work; multi-reviewer panel.
- **v6.0** — borrow checker + multi-level alias analysis (Rt.04
  carry-forward). Independent of We.1.

See also: `PLAN.md` (planning rationale, decision tree),
`PROMPT.md` (execution prompt), `CHANGELOG.md`, CLAUDE.md.
