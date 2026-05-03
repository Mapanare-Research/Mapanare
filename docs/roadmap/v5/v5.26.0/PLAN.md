# v5.26.0 — Mb.7 + Mb.9 — codegen + Win64 ABI fixes

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.25.0 shipped (Pv.\* prevention gates in place).
**Estimated effort:** 1–2 sessions (~5–10 hours; two real
codegen investigations, not mechanical).
**Arc context:** Closes the **Mb.\*** arc (memory-bug closures).
Mb.7 has been deferred from v5.23.1 → v5.24.0 → v5.25.0.
Mb.9 surfaced fresh in publish run #48 (Windows
`build-native (windows-latest, mnc-win-x64.exe, x86_64-w64-mingw32)`)
and bundles here because both items are codegen / ABI bugs in
the same emit-side surface.

---

## Why this exists

### Mb.7 — i64/i1 tag-emit (3-release carry)

The 9 LINK_FAIL goldens **47 / 48 / 49 / 51 / 55 / 56 / 57 / 58 /
59** trip an i64/i1 tag-emit bug in `mapanare/self/emit_llvm.mn`
when compiled through `mnc-stage1`. The Python bootstrap path
emits correct IR for the same inputs; only the self-host
emitter is wrong. Quoting v5.23.1 SESSION_REPORT verbatim:

> Mb.7 deferred to v5.24.0: investigation found the 9 LINK_FAIL
> goldens (47, 48, 49, 51, 55-59) trip an i64/i1 tag-emit bug
> in self-host `emit_llvm.mn` — unrelated to PIC reloc,
> unrelated to memory hygiene.

It then deferred again to v5.24.0 (which became Hy.\* hygiene)
and to v5.25.0 (Pv.\* prevention). v5.26.0 is the dedicated
release. **2 releases overdue.**

The 9 affected goldens cluster in the async / Option-payload
boxing surface (per v5.23.1 Mb.2 investigation, `emit_wrap_some`
heap-allocates the `{i1, ptr}` Option representation). The
suspected mismatch site: somewhere in the Option / Result tag
emission, the self-host emitter writes `i64 0` where
`i1 false` is expected, or vice versa. The Python emitter has
the right type; the self-host's `emit_llvm.mn` was ported with
a subtle width error.

### Mb.9 — Windows OOM in `__mn_count_user_brace_block_openers`

Publish run #48 surfaced a Windows-only OOM in the **v5.23.2
Te.3.B.2** native function `__mn_count_user_brace_block_openers`:

```
mapanare: oom in count_user_brace_block_openers
warning: HEAP[mnc-stage1.exe]:
warning: Invalid allocation size - 65746172656e6567 (exceeded 7ffffffdefff)
```

The hex `65746172656e6567` decodes to ASCII `"etareneg"` —
little-endian "generate". A `char*` payload is being read as
a `uint64_t` length. Classic Win64 ABI mismatch: the function
takes an `MnString` parameter, and the v5.23.2 implementation
predates a complete sret/sarg audit against v5.8.6 We.1 Win64
ABI. Linux (SysV AMD64) and macOS (AAPCS64) pass `MnString`
in two registers and were unaffected; Win64 routes the same
struct differently and reads the wrong eightbyte as the
length field, then `malloc(length)` blows up.

The fix lives in `runtime/native/mapanare_core.c` (and
possibly `mapanare_core.h` for any declaration mismatch).
Sister symbol `__mn_emit_brace_deprecation_warning` (also
v5.23.2 Te.3.B.2; takes `MnString` filename) is suspect too
and should audit alongside.

---

## Goals

1. **Mb.7.A** Phase 0 root-cause: identify the exact i64/i1
   mismatch site in `mapanare/self/emit_llvm.mn`.
2. **Mb.7.B** Fix the type-tag emission. Likely small diff
   (1–10 LOC) once the site is identified.
3. **Mb.7.C** All 9 LINK_FAIL goldens compile + link + run
   correctly through `mnc-stage1`.
4. **Mb.7.D** New `tests/llvm/test_async_link.py` that exercises
   the full mnc-stage1 → llc → ld linker pipeline on each of
   the 9 goldens. Fails if any future edit re-breaks the
   linker contract.
5. **Mb.7.E** Strict 3-stage fixed point preserved at v5.25.0's
   line count after `mnc_all.mn` regeneration. Bb.\* seed
   refresh required iff the fix touches a C-runtime export
   (unlikely for Mb.7 — but Mb.9 will trigger it).
6. **Mb.7.F** Update `tests/golden/BENCHMARKS.md`: 9 goldens
   move from LINK_FAIL → PASS. Goldens 95/95 — count
   unchanged but quality improves.
7. **Mb.9.A** Phase 0 root-cause: identify the exact Win64 ABI
   mismatch site for `__mn_count_user_brace_block_openers`.
   Audit sister symbol `__mn_emit_brace_deprecation_warning`
   in lockstep.
8. **Mb.9.B** Fix the C-runtime ABI handling so MnString
   parameters survive the Win64 calling convention end-to-end.
9. **Mb.9.C** New `tests/native/test_brace_funcs_windows_abi.py`
   regression guard exercising both v5.23.2 functions on
   real fixtures (skipped on non-Windows hosts via marker;
   informational on Linux/macOS via direct call from the
   Python ctypes binding).
10. **Mb.9.D** Bb.\* seed refresh: required (Mb.9 changes a
    C-runtime call shape; mirror v5.17.0 Sh.E precedent).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Mb.7.A** | HIGH (investigation) | **Phase 0 root-cause.** For one representative golden (e.g. `47`), capture: (a) Python bootstrap IR via `python -m mapanare emit-llvm`; (b) self-host IR via `./mapanare/self/mnc-stage1 emit-llvm`. `diff` the two outputs. Find the i64/i1 mismatch site. Capture the failing linker error verbatim — `nm`/`readelf` on the unlinked object to confirm the symbol-type mismatch. Document in `docs/roadmap/v5/v5.26.0/AUDIT.md`. | 2–3h |
| **Mb.7.B** | HIGH | **Fix the type-tag emission** in `mapanare/self/emit_llvm.mn`. Expected to be a small `i64` → `i1` (or vice versa) on one or two emit-site lines, possibly in `emit_wrap_some` / `emit_match_arm_tag` / `emit_option_extract` (exact site identified in Mb.7.A). Validate the fix against all 9 goldens individually — each must move from LINK_FAIL to PASS. | 1h |
| **Mb.7.C** | HIGH | **Stage2/3 fixed point.** After Mb.7.B, regenerate `mnc_all.mn`, build stage1, validate stage2.ll == stage3.ll at the same line count (or +/- the IR delta from the type-tag fix — should be 0 lines unless the fix changes a metadata constant). | 30 min |
| **Mb.7.D** | MEDIUM (structural) | New `tests/llvm/test_async_link.py` (~120 LOC). Each of the 9 goldens parametrized: compile via `mnc-stage1 emit-llvm`, hand to `clang` for object + link, run `nm` to assert no `undefined reference to` errors. Permanent regression guard. | 1h |
| **Mb.7.E** | LOW | If Mb.7.B changes any C-runtime call shapes, refresh `bootstrap/seed/linux-x86_64/mnc` per Bb.\* precedent (v5.17.0 Sh.E pattern). Expected: NOT required for Mb.7 — but Mb.9.D triggers it (see below). | 15 min (Mb.7-side) |
| **Mb.7.F** | LOW | Update `tests/golden/BENCHMARKS.md` table — 9 LINK_FAIL → PASS markers. Update CLAUDE.md release notes mentioning the link-failure → pass migration. | 15 min |
| **Mb.9.A** | HIGH (investigation) | **Phase 0 root-cause for Mb.9.** Audit `runtime/native/mapanare_core.c::__mn_count_user_brace_block_openers` against the v5.8.6 We.1 Win64 ABI rules. Cross-check with the working v5.14.1 B.5 `__mn_indent_to_braces` (also takes `MnString`, works on Windows post-v5.23.1). Possible failure modes: (a) MnString parameter passed by-value vs by-pointer mismatch; (b) length field eightbyte index swapped; (c) declaration in `mapanare_core.h` doesn't match the definition signature. Audit sister symbol `__mn_emit_brace_deprecation_warning` in the same pass. Document findings in `docs/roadmap/v5/v5.26.0/AUDIT.md`. | 1–2h |
| **Mb.9.B** | HIGH | **Fix the C-runtime ABI handling.** Likely shape: align the function signature with `__mn_indent_to_braces`'s working pattern (same `MnString` parameter, same return convention). Confirm via `objdump -d` on the Windows-compiled object that the prologue reads `rcx`/`rdx` (or stack slots) in the correct order. May require a cross-platform conditional `#ifdef _WIN32` if the SysV vs Win64 layouts genuinely diverge for the function body. | 1–2h |
| **Mb.9.C** | MEDIUM (structural) | New `tests/native/test_brace_funcs_windows_abi.py` (~80 LOC). Two tests, parametrized over `__mn_count_user_brace_block_openers` and `__mn_emit_brace_deprecation_warning`. Loads `libmapanare_rt.so` (or `.dll` on Windows) via ctypes; constructs a known-good MnString; calls each function with a fixture file; asserts the return value matches the expected count and no SIGABRT / OOM occurs. Runs on every CI host but only the Windows host catches the actual bug — Linux/macOS provide the regression-detection contract via direct ctypes call (no compiler involved). | 1h |
| **Mb.9.D** | LOW | **Bb.\* seed refresh.** Mb.9.B changes the call shape of two C-runtime exports the v5.10.0-vintage seed cannot re-emit. Refresh `bootstrap/seed/linux-x86_64/mnc` from the Mb.9.B HEAD `mnc-stage1` per v5.17.0 Sh.E precedent. Plus `.sha256` regeneration. | 15 min |

---

## Phase plan

### Phase 0 — root-cause investigation (Mb.7.A)

```bash
# Reproduce LINK_FAIL on one golden
python scripts/build_stage1.py
./mapanare/self/mnc-stage1 emit-llvm tests/golden/47_*.mn > /tmp/native.ll
python -m mapanare emit-llvm tests/golden/47_*.mn -o /tmp/python.ll
diff /tmp/python.ll /tmp/native.ll | head -100  # find the divergence

# Try linking the native output
clang /tmp/native.ll -L runtime/native -lmapanare_rt -o /tmp/golden47 2>&1 | tee /tmp/link.err
# Capture the exact "undefined reference" or type-mismatch error
```

Expected output: a specific symbol or type-cast site where the
two differ. Document in `AUDIT.md` before writing the fix.

**Hard exit criterion**: do not proceed to Mb.7.B until the
diff identifies the exact `emit_*` function in
`mapanare/self/emit_llvm.mn` that emits the wrong type tag.

### Phase 1 — surgical fix (Mb.7.B)

One-line or small-block edit in `mapanare/self/emit_llvm.mn`.
Keep the diff minimal — no opportunistic refactoring of nearby
code. The Python emitter is the contract.

### Phase 2 — corpus validation (Mb.7.C)

Each of the 9 goldens must move from LINK_FAIL → PASS individually.
Stage2/3 fixed point preserved.

### Phase 3 — regression test + docs (Mb.7.D + Mb.7.F)

The test is the durable artifact. Without it, the next async-path
edit could regress silently.

### Phase 4 — Mb.9 root-cause + fix (Mb.9.A + Mb.9.B)

Sequence is intentional: ship Mb.7 first (self-host emitter
work, no C-runtime involvement), then take on Mb.9 (C-runtime
ABI work). Bundling them in one phase risks confusing two
unrelated investigations.

```bash
# Reproduce the Windows OOM via cross-platform proxy first
# — call the function from Linux ctypes with a known input
python3 -c "
import ctypes
lib = ctypes.CDLL('runtime/native/libmapanare_runtime.so')
class MnString(ctypes.Structure):
    _fields_ = [('data', ctypes.c_char_p), ('len', ctypes.c_uint64)]
src = b'fn main() { print(1) }'
s = MnString(src, len(src))
lib.__mn_count_user_brace_block_openers.argtypes = [MnString]
lib.__mn_count_user_brace_block_openers.restype = ctypes.c_int64
print(lib.__mn_count_user_brace_block_openers(s))
"
# expected on Linux: 1 (works); the Windows manifestation is
# ABI-routing-specific. Use the Linux-side call as the contract
# the Windows path must match.
```

Then audit the C signature, fix, verify the Linux-side ctypes
call still returns 1, and validate the Windows publish job goes
green on the next push (Mb.9.C makes this catchable locally
even on non-Windows hosts).

### Phase 5 — Mb.9 regression test + seed refresh (Mb.9.C + Mb.9.D)

```bash
$EDITOR tests/native/test_brace_funcs_windows_abi.py

# Regenerate seed (Mb.9.B changes call shapes)
python3 scripts/build_stage1.py
cp mapanare/self/mnc-stage1 bootstrap/seed/linux-x86_64/mnc
sha256sum bootstrap/seed/linux-x86_64/mnc \
    > bootstrap/seed/linux-x86_64/mnc.sha256
bash scripts/build_from_seed.sh  # must succeed with new seed
```

---

## Out of scope

- **Refactor of async lowering generally** — focused fix only.
- **Tensor or GPU codegen paths** — different surface; not on
  the LINK_FAIL list.
- **Coroutine scheduler changes** — runtime-side; the bug is
  in IR emission, not the scheduler.
- **Python bootstrap parity work beyond what the diff
  surfaces** — if the diff shows other minor divergences
  in the same goldens, document but defer.

---

## Risk

**Real codegen work** — this is the first v5.x release in the
v5.13–v5.27 window that touches `mapanare/self/emit_llvm.mn`
materially since the v5.17.0 Sh.\* mechanical rewrite. Risks:

1. **Fix surfaces a deeper bug.** If the i64/i1 mismatch is the
   *symptom* of a broader Option-representation drift, the fix
   might cascade. Mitigation: Phase 0 audit must confirm the
   minimal-fix hypothesis before proceeding.
2. **Stage2/3 fixed-point break.** If the IR delta from the
   fix is non-zero, the strict-fixed-point streak breaks.
   Mitigation: contained type-tag changes shouldn't perturb
   line count; if they do, document as expected and resume the
   streak from the new baseline.
3. **Goldens 47–59 are the canary.** If the fix makes them pass
   but breaks any of the existing 86 passing goldens, Mb.7 must
   be reverted and rescoped.

---

## Success criteria

- ✅ Goldens 95/95 with all 9 previously-LINK_FAIL goldens now
  PASS through `mnc-stage1` end-to-end.
- ✅ `tests/llvm/test_async_link.py` passes 9/9 (regression
  guard).
- ✅ `tests/native/test_brace_funcs_windows_abi.py` passes
  on every CI host (Linux/macOS/Windows); the Mb.9 publish-run-#48
  Windows OOM cannot recur.
- ✅ Strict 3-stage fixed point preserved (or: documented
  baseline change with approved line-count delta).
- ✅ No regression in the 86 previously-passing goldens.
- ✅ `mnc_all.mn` regenerated; bootstrap from seed succeeds
  (with refreshed seed per Mb.9.D).
- ✅ Windows publish job (`build-native (windows-latest,
  mnc-win-x64.exe, x86_64-w64-mingw32)`) green on next push.

---

## Carry-forward delta

Closes:
- **Mb.7** (3-release carry: v5.23.1 → v5.24.0 → v5.25.0 →
  closed at v5.26.0).
- **Mb.9** (fresh from publish run #48; closed in same release
  as discovered).
- Mb.\* arc closeout — every memory- and ABI-related panel
  finding through v5.22.0 + v5.23.2's Te.3.B.2 follow-on closed.

No new opens.
