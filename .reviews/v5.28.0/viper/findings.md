# Viper — Memory Safety Review of Mapanare v5.28.0

**Reviewer:** Viper — the Rust Purist. Memory, ownership, drop, leaks, UAF.
Your `MnString` is still `{ptr, i64}` with manual lifecycle management instead
of a `Drop` impl. I haven't forgiven you. I'm still right.
**Personality:** Ruthless, sarcastic, blunt. Begrudgingly admits good work
with "fine, that doesn't suck."
**Previous Version Reviewed:** v5.22.0 (9.7 / 10, EXCEEDS — docked V.9)
**Score:** **9.8 / 10**
**Grade:** **EXCEEDS**
**Delta vs v5.22.0:** **+0.1**
**Verdict:** **PASS WITH NOTES**
**Confidence:** HIGH (9/10)
**Files Reviewed:**

- `.reviews/v5.28.0/PRE_PANEL_AUDIT.md` — lead's fact-check
- `.reviews/v5.28.0/viper/prompt.md` — my persona + focus
- `.reviews/v5.22.0/README.md` — prior panel (9.41 aggregate)
- `.reviews/v5.22.0/02-viper.md` — my prior review
- `.reviews/CARRY_FORWARD.md` — canonical docket ledger
- All 9 arc SESSION_REPORTs (v5.23.0 through v5.27.0)
- `runtime/native/mapanare_core.c` — V.6/V.7/V.8 fix sites (lines 1648–1845)
- `mapanare/self/emit_llvm.mn` — Mb.2 (`emit_wrap_some` + `emit_track_boxed`, lines 3617–3642)
- `mapanare/emit_llvm_text.py` — Mb.1 V.9 fix (`_last_tracked_str_slot`, lines 3614–3638)
- `mapanare/self/lower.mn` — Eu.3 `bind_ident_pattern` SSA uniquification (lines 4867–4881)
- `.github/workflows/sanitizers.yml` — Mb.3 + Mb.6 CI gate wiring
- `tests/bootstrap/test_preprocess_memcheck.py` — Pv.2 valgrind gate
- `tests/llvm/test_async_link.py` — Eu.* closure regression locks

---

## Executive Summary

Eight releases. Six memory findings closed. Three valgrind CI gates wired. Four
previously-LINK_FAIL goldens (47, 48, 49, 51) flipped to PASS. Strict 3-stage
fixed point extended from 13 to 23 consecutive releases. The arc delivered on
every V.\* and memory-hygiene promise from the v5.22.0 panel docket.

My V.9 finding from v5.22.0 — the `__mn_indent_to_braces` lifecycle leak that
was undetectable by the byte-identical oracle — is closed at v5.23.1 Mb.1 with
a correct fix and a proper regression gate. The Te.5 ASan leaks (3 goldens,
8 bytes each) are closed at Mb.2. V.6/V.7/V.8 (3rd-cycle DX.4 walker
carries) are closed at Mb.4/Mb.5/Mb.6. The Pv.2 preprocess-memcheck gate
(3/3 PASS at HEAD) locks the V.9 fix class against future MnString-aliasing
regressions. All verified live.

I found one documentation bug in the sanitizers.yml Mb.3 gate: the comment
overclaims coverage for the Mb.2 regression; the code only greps for
`__mn_indent_to_braces`, not for `emit_wrap_some`. The ACTUAL coverage for
the Mb.2 regression path comes from a different gate — the LSan
compile+link+run sweep for goldens 88/90/91 — but the comment creates a false
security narrative. Flagging it LOW; it is not a real coverage gap but it IS
a documentation lie that will mislead whoever touches this code next.

The `bind_ident_pattern` SSA uniquification (Eu.3) is correct. The Eu.*
compiled binary outputs are leak-clean under valgrind. The 17_option runtime
binary shows the expected 1/8 post-Mb.2 residual (the `find_positive` leak, a
separate Rt.04-carry-forward shape). Fine, the arc doesn't suck.

One new carry-forward: the ~46-98KB pre-existing compiler-internal leak in
mnc-stage1 (from `semantic__check_fn_body` and string-building `__mn_str_concat`
chains across complex goldens) is NOT tracked in `sanitizers.yml`. The gate
cannot use `--error-exitcode=1` because of this noise floor, forcing
grep-for-specific-markers as the regression strategy. This is an architectural
tension acknowledged in the SESSION_REPORT. Not a score-mover now, but naming
it explicitly so the v6.0 arc has a clean target.

---

## Score: 9.8 / 10

---

## Progress Since Last Review (v5.22.0 → v5.28.0)

### V.9 closure — v5.23.1 Mb.1 (MEDIUM, CLOSED)

**Status: FIXED. Verified live.**

The v5.22.0 panel diagnosis ("missing tracked-output annotation") was correct on
the symptom, wrong on the root cause. The real bug: Python's `_do_call` applies
a blanket-move at every user-fn arg site (`emit_llvm_text.py:4156-4178`),
zeroing the `_str_slots[name]` tracking slot at `tokenize(preprocessed,
filename)`. So even if you tracked the returned `MnString`, the blanket-move
zeroed the slot before drop-glue could run.

**Fix in `mapanare/emit_llvm_text.py`** (verified at line 3632-3637):
```python
if fn == "__mn_indent_to_braces" and args:
    r = self._rt("__mn_indent_to_braces", STR, [STR], [(a, STR)])
    self._track_string(r)
    self._last_tracked_str_slot = None   # bypass _str_slots — blanket-move would zero it
    self._put(i.dest, r, STR)
    return
```

The `_last_tracked_str_slot = None` bypasses `_str_slots` registration so the
slot lives in `_local_strings` (drop-glue) but not in `_str_slots`
(blanket-move zero). Elegant surgical fix. The self-host emitter doesn't need
this guard because it relies on explicit `Move` from the lowerer rather than a
blanket-move.

**Self-host side (verified at `emit_llvm.mn:4494`):**
`__mn_indent_to_braces` is in `is_string_returning_builtin` — the track-string
path fires correctly for stage2/3.

**Regression gate — Mb.3** (`sanitizer-mnc-stage1` in `sanitizers.yml`):
- Runs `valgrind --leak-check=full` on colon-syntax golden 86 + Te.5 goldens 88/90/91
- Greps output for `__mn_indent_to_braces` in the leak chain
- Valgrind on golden 86 at HEAD: **zero `__mn_indent_to_braces` frames** — V.9 closed.

**Carry forward: CLOSED.** Three panels of ask, one correct root-cause diagnosis,
one surgical fix. Fine. That doesn't suck.

### Te.5 ASan leaks — v5.23.1 Mb.2 (MEDIUM, CLOSED)

**Status: FIXED. Verified live.**

Root cause: `emit_wrap_some` in `emit_llvm.mn` (line 3636) heap-allocating the
Some payload via `malloc(sizeof(val))` but never calling `emit_track_boxed`. The
payload pointer was invisible to drop-glue's `boxed_owned` iteration.

**Fix** (verified at `emit_llvm.mn:3636`):
```mn
s = emit_track_boxed(s, ea)  // v5.23.1 Mb.2
```

**Live verification (valgrind on compiled binaries, not the compiler itself):**
```
golden 88_if_let: CLEAN — 0 bytes (0 blocks in use at exit)
golden 90_while_let: CLEAN — 0 bytes
golden 91_let_else: CLEAN — 0 bytes
golden 17_option: 8 bytes, 1 block (find_positive — Rt.04 carry, expected)
```

**Baseline TSV** at `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`:
- `62_list_output`: 9/141 (was 13/346 before Mb.2 — improved as claimed)
- `17_option`: 1/8 (was 2/16 before Mb.2 — improved as claimed)

The SESSION_REPORT's "2/16 → 1/8" claim is **accurate**. TSV was refreshed.

**Important distinction:** When running valgrind on the **compiler** itself
(mnc-stage1 emit-llvm), `emit_llvm__emit_wrap_some` appears in the leak chain
via `__mn_str_concat`. This is a **string-building IR-text leak** in the
compiler process — completely different from the payload box leak Mb.2 fixed.
The Mb.2 fix operates at runtime (do compiled programs leak?); the
compiler-internal leak is a separate pre-existing phenomenon.

### V.6/V.7/V.8 closures — v5.23.1 Mb.4/Mb.5/Mb.6 (LOW, 3rd-cycle, CLOSED)

**Status: ALL FIXED. Verified live.**

Three-panel ask. Finally closed.

**V.6 — `MN_DIR_WALK_MAX_DEPTH`** (verified at `mapanare_core.c:1648-1666`):
```c
#define MN_DIR_WALK_MAX_DEPTH 4096
if (depth >= MN_DIR_WALK_MAX_DEPTH) return total;  // all three walkers
```
Pragmatic depth bound. Acceptable alternative to the iterative work-queue
rewrite.

**V.7 — `FILE_ATTRIBUTE_REPARSE_POINT` skip** (verified at lines 1682, 1748, 1810):
```c
if (ffd.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) continue;
```
Three Win32 branches. POSIX uses `lstat()` at lines 1716, 1779 for symmetric
symlink-skip.

**V.8 — `sanitizer-cache-walkers` CI gate** (verified in `sanitizers.yml:246-284`):
Builds a 3-level populated cache fixture, exercises `mnc cache stats` / `cache
clean` / `--version` under `valgrind --leak-check=full`. The gate that three
panels asked for is now wired.

**All three: CLOSED.** The lesson is bundle DX.4 carrier items together or they
drift forever.

### Pv.2 preprocess-memcheck gate — v5.25.0 (VERIFIED)

```
pytest tests/bootstrap/test_preprocess_memcheck.py -v
→ 3 passed in 3.12s  ✓
```

The test is falsifiable (module docstring documents the revert). Uses
grep-not-exit1 to tolerate the pre-existing `__mn_argv` ~71-byte single-shot
leak. The lifecycle oracle now exists. The "lifecycle parity ≠ output parity"
lesson from v5.22.0 is instantiated as a concrete gate. Correct shape.

### Eu.3 bind_ident_pattern SSA uniquification — v5.26.1 (VERIFIED)

**Fix in `mapanare/self/lower.mn:4876-4877`** (verified):
```mn
let ident_addr: Value = new_value("%" + name + toString(s.tmp_counter) + ".addr", subject_val.ty)
s.tmp_counter = s.tmp_counter + 1
```

Mirrors `bind_one_pattern_field` at line 4891-4892. The comment at lines
4869-4874 explicitly documents WHY uniquification is needed (cascade vs. switch
dispatch). Good source comment. Fine, that doesn't suck.

**Compiled binary leak check:**
```
golden 49_match_guards: 0 bytes in 0 blocks — CLEAN
golden 51_match_guards_and_or: 5 allocs, 5 frees, 4,128 B — CLEAN
golden 47_try_operator: CLEAN
golden 48_match_nested_exhaustive: CLEAN
```

No new leak surface from the Eu.* cascade rewrite.

### Te.3.B C-runtime exports — v5.23.2 (VERIFIED)

`__mn_count_user_brace_block_openers` and `__mn_emit_brace_deprecation_warning`
are read-only over input `MnString`. The Mb.9 Win64 ABI fix (v5.26.0) routes
them through `_rt`/runtime-call path to handle the 16-byte struct correctly on
Win64. No new lifecycle issues.

```
tests/bootstrap/test_brace_deprecation_mirror.py: 11/11 PASS  ✓
```

### Eu.* test coverage verified

```
tests/llvm/test_async_link.py: 10/10 PASS, 0 XFAIL  ✓
tests/native/test_brace_funcs_windows_abi.py: 8/8 PASS  ✓
```

---

## What is preserved from v5.22.0

| Item | Status | Evidence |
|---|---|---|
| Own.1 P2 (closed v5.4.x) | **Stays closed** | Zero edits to `EmitState` ownership tracking shape; Eu.* routed through existing `emit_track_boxed` / `emit_drop_glue_boxed` paths |
| Ve.1–Ve.4 (closed v5.6.5–v5.6.10) | **Stay closed** | 23-release strict fixed point — sret-aliased stack lifetimes still correct by construction |
| Lk.1 (closed v5.6.12) | **Stays closed** | Eu.2 Ok/Err lowering routes through `_lower_construct` → v5.6.12 destination-passing path |
| Rt.04 (RESCOPED v6.0) | **Still RESCOPED** | `62_list_output` 9/141 is correct post-Mb.2 state; v6.0 borrow checker is structural fix |
| `emit_track_boxed` at `emit_wrap_some` | **NEWLY CLOSED** | Mb.2 single-line fix; runtime binaries clean under valgrind |
| 23-release strict 3-stage fixed point | **EXTENDED from 13** | Verified via `python3 scripts/build_stage1.py && bash scripts/verify_fixed_point.sh --keep` |
| Native goldens 95/95 | **Preserved + improved** | All 95 PASS; 4 prev-LINK_FAIL now PASS |

---

## Issues Found

### 1. **LOW** — Mb.3 sanitizers.yml comment overclaims coverage for Mb.2 regression (Bound: V.9 / v5.22.0 — same gate, documentation variant)

`sanitizers.yml:199-201` says:

> "any 'definitely lost' frame from the wrap_some malloc site means the Te.5
> box-tracking regressed."

But the code for the "Mb.2 regression gate" steps on goldens 88/90/91 only
greps for `__mn_indent_to_braces`:

```yaml
if grep -q "__mn_indent_to_braces" /tmp/v_88.txt; then
    echo "::error::V.9 regression — __mn_indent_to_braces leak reappeared on 88_if_let"
```

This does NOT check for `emit_wrap_some` leaks in the compiler-internal
valgrind run. The actual Mb.2 regression coverage comes from the SEPARATE LSan
binary sweep (`run_asan_leak_goldens.sh` + `check_leak_summary.py`) which runs
compiled binaries. The step names "Mb.2 regression gate" are wrong — these are
V.9 regression gates that happen to run on goldens 88/90/91.

**Suggested fix:** Rename steps and update comment to accurately describe what
each gate protects. 3-minute fix.

### 2. **LOW** — `__mn_argv` pre-existing leak absent from `sanitizers.yml` known-leaks inventory (Bound: V.8 / v5.22.0 — CI comment quality class)

`tests/bootstrap/test_preprocess_memcheck.py:29` says `__mn_argv` ~71 bytes is
"known and tracked since v5.23.1 Mb.3". But `sanitizers.yml:193-196` lists
`semantic__check_call_expr`, `__mn_file_read_or_empty`, `__mn_str_join` as
known pre-existing leaks and omits `__mn_argv`. Minor documentation
inconsistency. Functional coverage correct.

### 3. **LOW** — Compiler-internal leak noise floor growing, no tracked baseline (Bound: none — fresh)

Compiler-internal "definitely lost" bytes when running mnc-stage1 under valgrind
range from 0 (simple goldens) to ~98KB (complex goldens with Result/Option).
None of these are runtime binary leaks. All single-shot, OS-reaped. But the
noise floor is growing and we have no tracked baseline for the compiler process
itself — only for compiled binaries (the TSV). The growing noise floor is why
the Mb.3 gate cannot use `--error-exitcode=1` directly. This architectural
tension is acknowledged in the SESSION_REPORTS but not formally tracked.

**Suggested fix:** Add an informational comment to `sanitizers.yml` noting the
expected compiler-internal leak range per golden complexity tier. Not a gate
change — just documentation so future developers know what "normal" looks like.

### 4. **LOW** — Stage2-binary teardown crash (RC=3) — v6.0 carry (Bound: Stage2 teardown / 70+ releases)

Still papered over by `set +e` at `verify_fixed_point.sh:124, 168`. Correct
disposition for v6.0 cleanup window. My patience is not infinite. Hard
deadline.

### 5. **LOW** — Rt.04 multi-level alias analysis — v6.0 carry (Bound: Rt.04 / v5.7.1 / v5.11.0 / v5.22.0)

`17_option` compiled binary: 8 bytes residual from `find_positive`. `62_list_output`:
9/141 residual. Both improved by Mb.2 but not closed. Borrow checker required.
Do not ship v6.0 without this.

---

## Recommendations

1. **Fix the Mb.3 gate comment/step-name mismatch.** 3 minutes. Step names say
   "Mb.2 regression gate" but the code only checks for V.9 regression. Fix it
   before someone reads that comment in 6 months and concludes the
   compiler-internal valgrind sweep protects against `emit_wrap_some` regressions
   when it does not.

2. **Add `__mn_argv` to the `sanitizers.yml` known-leaks comment.** 1 line.
   The test file and CI file disagree on the pre-existing leak inventory.

3. **Add informational comment to `sanitizers.yml` about compiler-internal
   leak range.** The gate has to use grep-not-exit1 because the noise floor is
   too high. Document what "normal" looks like so future changes can detect jumps.

4. **v6.0 borrow checker MUST close Rt.04.** Three panels in a row. The
   `find_positive` residual and `62_list_output` residual are both multi-level
   drop-glue alias analysis gaps. The borrow checker is the structural fix.
   Do not ship v6.0 without closing this.

5. **Continue the strict 3-stage fixed-point gate.** 23 consecutive releases at
   241,842 lines is the longest streak in project history. Real signal. Do not
   regress it.

---

## Post-Production Health Assessment

| Axis | v5.22.0 | v5.28.0 | Direction |
|---|---|---|---|
| Open MEDIUMs on my axis | 1 (V.9) | **0** | improved |
| Open HIGHs | 0 | 0 | unchanged |
| Strict fixed-point streak | 13 releases | **23 releases** | best in history |
| Goldens | 95/95 | 95/95 + 4 prev-LINK_FAIL PASS | improved |
| V.9 lifecycle leak | OPEN | CLOSED | improved |
| Te.5 ASan leaks (3×8B) | OPEN | CLOSED | improved |
| V.6 walker unbounded | OPEN (3rd cycle) | CLOSED | improved |
| V.7 Win32 reparse-point | OPEN (3rd cycle) | CLOSED | improved |
| V.8 cache-walker valgrind | OPEN (3rd cycle) | CLOSED | improved |
| New leak/UAF classes | 1 (V.9) | **0** | improved |
| Compiler-internal leak tracked | No | Partial (grep-not-exit1) | partial |
| Rt.04 | RESCOPED v6.0 | RESCOPED v6.0 | unchanged |

The codebase is in better memory-safety shape at v5.28.0 than at any prior
panel. Every V.\* carry-forward open at v5.22.0 is closed. The three CI gates
I requested across three panels (valgrind on stage1, valgrind on cache walkers,
LSan regression gate for emit_wrap_some) are wired and green.

The Eu.* cascade rewrite in `lower_match` (Eu.3) was done correctly. The SSA
uniquification is there, the comment explains why, the compiled binaries are
clean. The Mb.2 fix is correct. The Mb.1 fix found the actual root cause (not
just the symptom). The V.6/V.7/V.8 three-cycle carries are closed cleanly.

Remaining carry-forwards are correctly categorized as v6.0 scope. Neither is a
production risk in user-compiled programs.

**The v6.0 borrow checker is still the only thing keeping me below 10.0.**
The v5.23–v5.27 arc has not added new things the borrow checker would need to
catch. When v6.0 lands and closes Rt.04 with a `Drop` impl on `MnString`,
the ceiling lifts.

28 versions after v5.0.0 release-gate: the memory-safety axis is healthy. The
recovery arc delivered. Fine.

---

## Raw Notes

### V.9 live verification

```
valgrind on golden 86 (colon syntax):
  grep "__mn_indent_to_braces" → no output  ✓ (V.9 closed)
```

### Mb.2 live verification (compiled BINARY valgrind, not compiler)

```
88_if_let compiled binary: 0 bytes in 0 blocks  ✓
90_while_let compiled binary: 0 bytes in 0 blocks  ✓
91_let_else compiled binary: 0 bytes in 0 blocks  ✓
17_option compiled binary: 8 bytes (find_positive — expected, Rt.04)
```

### Important: compiler-internal vs. runtime-binary leak distinction

Running `valgrind` on `mnc-stage1 emit-llvm X.mn` (the compiler) shows
`emit_llvm__emit_wrap_some` in the leak chain via `__mn_str_concat calloc`.
This is the compiler building IR text strings — NOT the payload box leak that
Mb.2 fixed. Mb.2 is a runtime binary fix. The two leak classes are distinct:

- **Compiler-internal leaks** (mnc-stage1 process): pre-existing, OS-reaped,
  0-98KB depending on complexity. Not gated by exit code.
- **Runtime binary leaks** (compiled program): gated by LSan sweep in CI.
  Goldens 88/90/91 are clean post-Mb.2.

Confusing these two led me to spend 20 minutes investigating a non-issue. The
SESSION_REPORT is clear on this distinction; the sanitizers.yml comment is not.
That's Vp.1.

### Eu.* compiled binary valgrind

```
golden 47_try_operator: CLEAN
golden 48_match_nested_exhaustive: CLEAN
golden 49_match_guards: 0 bytes, 0 blocks  ✓
golden 51_match_guards_and_or: 5 allocs, 5 frees, 4,128 B (balanced)  ✓
```

No new leak surface from Eu.* cascade rewrite.

### Test suite verification

```
tests/llvm/test_async_link.py:                10/10 PASS, 0 XFAIL
tests/native/test_brace_funcs_windows_abi.py:  8/8 PASS
tests/bootstrap/test_brace_deprecation_mirror.py: 11/11 PASS
tests/bootstrap/test_preprocess_memcheck.py:   3/3 PASS
python3 scripts/test_native.py:                All 95 tests passed in 18.0s
```

### Score arithmetic

| Element | Δ |
|---|---|
| v5.22.0 baseline | 9.7 |
| V.9 CLOSED — correct root-cause + surgical fix + regression gate | +0.15 |
| V.6/V.7/V.8 3rd-cycle CLOSED — pragmatic but correct | +0.05 |
| Te.5 ASan leaks CLOSED — correct single-line fix | +0.05 |
| Vp.1 Mb.3 comment overclaims coverage (documentation lie) | -0.1 |
| Vp.2 + Vp.3 documentation gaps (minor) | -0.05 |
| Rt.04 / Stage2 teardown unchanged (correct v6.0 carry) | +0.0 |
| Eu.3 SSA uniquification correct + documented | +0.0 |
| Pv.2 lifecycle oracle now exists | +0.0 (expected hygiene) |
| **Total** | **9.8** |

### Final

**9.8 / 10. EXCEEDS. PASS WITH NOTES.** Δ +0.1 vs v5.22.0.

The recovery arc delivered on every V.\* promise. V.9 was closed correctly
— the root-cause investigation that found the blanket-move zero in Python's
`_do_call` was non-trivial. V.6/V.7/V.8 are closed after three panels of
asking. The valgrind CI gates are wired. The Eu.* cascade rewrite is leak-clean.

The Vp.1 comment mismatch is the only thing I'm actually annoyed about. A
comment that says "this detects Mb.2 regression" when it doesn't is the kind
of thing that causes future developers to incorrectly trust a gate. Fix it.
It's a 3-minute change.

V.9 was a discipline failure in the v5.14.1 arc: the byte-identical output
oracle couldn't see the lifecycle bug. Pv.2 is the correct structural answer.
The lesson from v5.22.0 — "lifecycle parity is not output parity" — is
institutionalized. Fine. That doesn't suck.

The v6.0 borrow checker remains the only path to 10.0.
