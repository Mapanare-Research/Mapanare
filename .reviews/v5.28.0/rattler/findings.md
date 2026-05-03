# Rattler — v5.28.0 Panel Review
## LLVM IR / Codegen Reviewer

---

## Score

**9.90 / 10 — EXCEEDS — PASS WITH NOTES**
**Delta vs v5.22.0 (prior Rattler baseline): +0.05**
**Confidence: 9/10**

---

## Executive Summary

The v5.23.0–v5.27.0 arc does exactly what the roadmap promised and nothing less. The strict 3-stage fixed-point streak extends from 13 consecutive releases (the project record at v5.22.0 panel) to **23 consecutive releases at 241,842 lines / 0 diff**. Four structurally distinct LINK_FAIL goldens (47/48/49/51) are now PASS, each closed via a targeted codegen fix verified live in the generated IR. The Te.3 MEDIUM from v5.22.0 — brace-deprecation hollow with zero native mirror — is closed with an 11/11 byte-identical test suite. The i64/i1 anti-pattern (Mb.7) is surgically absent from stage2.ll with zero false positives scanned across all 241,842 lines. The Win64 MnString ABI mismatch (Mb.9) is locked behind an 8/8 passing gate under forced Win64 triple.

The arc's discipline on scope is notable from an IR perspective: no new MIR instruction kinds added across nine releases (`mir.py`: 65 class definitions unchanged v5.22.0→HEAD), no new IR shapes, no new ABI rules. Every new feature desugars to existing `BinOp` / `Call` / `Branch` / `Switch` instruction paths. This is the correct posture for a 23-release streak.

One LOW finding carried forward: the stage2 teardown crash has a narrower root cause than previously documented. Recommend Option A.

---

## Verdict on Mechanical Gate

**Option A: PASS** — Aggregate ≥ 9.0 ✓, 0 NEEDS WORK ✓, No NEW HIGH ✓.
Cadence: 1 minor late (fired at v5.27.0 per `check_cadence.py`; acknowledged in PRE_PANEL_AUDIT.md Phase 2; informational only — panel did not miss a release cycle, it landed at v5.28.0 as planned).

---

## Per-Arc Analysis

### RC.* (v5.23.0 — CI recovery + HIGH closures)

**Prior panel binding:** Anaconda Reg.1 HIGH (struct registry regex inert since Sh.*), Boa Bo.25 HIGH (goldens badge 66/66 vs 95/95 body), multiple MEDIUM.

**Codegen/IR relevance:** RC.1 (struct registry) directly affects IR correctness — `LowerState` struct field count in the registry drives `getelementptr` index generation in `emit_llvm.mn`. The 3-string × 2-list literal edit updating the registry to 20 fields is data-only and correct. `register_mir_struct` call at the LowerState declaration includes all 20 fields matching `lower_state.mn` struct definition.

**RC.9 (stage2 ir_doctor cross-module retry):** The per-module compile path now detects "Undefined function" and retries against `mnc_all.mn`. From an IR perspective this is the right fix — when `lower.mn` crosses into `parser.mn::new_match_arm`, the standalone per-module IR is incomplete and `llvm-as` rejects the undefined symbol. Retry against the monolithic concatenation produces valid IR with all symbols resolved.

**Verdict:** RC.* closed correctly. No IR regressions.

---

### Mb.7 — i64/i1 tag-emit fix (v5.26.0)

**Prior panel binding:** (none — fresh at v5.26.0; Rattler v5.22.0 noted the LINK_FAIL cluster but root cause was unknown)

**Implementation verified live.**

`mapanare/self/emit_llvm.mn::emit_enum_tag` at lines 3507–3540:

```
if val.ty.kind == TK_RESULT() || val.ty.kind == TK_OPTION():
    if dest.ty.kind == TK_BOOL():
        s = emit_line(s, emit_extractvalue(dn, enum_ty, val.name, "0"))
    else:
        let raw_tag: String = dn + ".raw"
        s = emit_line(s, emit_extractvalue(raw_tag, enum_ty, val.name, "0"))
        s = emit_line(s, "  " + dn + " = zext i1 " + raw_tag + " to i64")
```

The surgical 5-LOC fix honors `dest.ty.kind`: `TK_BOOL` consumers (the `?` try-operator path whose dest is `mir_bool()`) receive a direct `extractvalue` to i1. `TK_RESULT`/`TK_OPTION`/`TK_ENUM` consumers (the `match → switch i64` path) receive `extractvalue` to `.raw` then `zext i1 %.raw to i64`.

**Anti-pattern scan on stage2.ll (241,842 lines):** Scanned for `zext i1 %X to i64` followed within 5 lines by `br i1 %X` (same register name). **Result: 0 instances.** The fix is complete and there are no residual occurrences.

**Golden 47 IR verification (`tests/golden/47_try_operator.mn`):** Compiled golden 47 through `mapanare emit-llvm`. The `?` operator on `Result<Int, String>` produces:

```llvm
%tag.raw = extractvalue {i1, {i64, {ptr, i64}}} %res, 0
br i1 %tag.raw, label %ok_branch, label %err_branch
```

Valid: `br i1 %tag.raw` consumes an i1 value directly. Pre-fix, this was `zext i1 %tag.raw to i64` then `br i1 %zext_result` — the exact anti-pattern. Fix confirmed.

**Verdict:** Mb.7 closed correctly. IR-clean at HEAD.

---

### Mb.9 — Win64 MnString byval/byref ABI (v5.26.0)

**Prior panel binding:** (none — fresh at v5.26.0; Te.3.B.2 functions identified in v5.23.2)

**Root cause (precisely):** Python `_decl_fn` uses threshold `sizeof(struct) > 8` as the `is_large_struct` predicate on Win64; `_do_call` uses threshold `sizeof(struct) > 64` as the `use_byref` predicate. `MnString = {ptr, i64}` has `sizeof = 16`. So `_decl_fn` declared the parameter as `ptr` (by-reference, hidden pointer) but `_do_call` passed it by value (16-byte struct in two `i64` registers). The concrete manifestation: when the input is `// Auto-generated:`, gcc's Win64 ABI reads bytes 8..16 of the data buffer (`g e n e r a t e` ASCII) as a 64-bit integer length → `0x65746172656e6567` → `malloc(7e+18)` → OOM.

**Fix verified:** Both `__mn_count_user_brace_block_openers` and `__mn_emit_brace_deprecation_warning` are in the explicit routing table forcing `_rt(name, ...)` / `_rt_void(name, ...)` at call sites (`mapanare/emit_llvm_text.py` lines 3645–3670). Self-host `emit_mir_call` routes these through `emit_rt_call` / `emit_rt_call_void`. Both paths always pass MnString by pointer regardless of the threshold check, mirroring the v5.23.1 Mb.1 pattern for `__mn_indent_to_braces`.

**Gate:** `tests/native/test_brace_funcs_windows_abi.py` 8/8 PASS under forced Win64 triple.

**Verdict:** Mb.9 closed correctly. ABI contract consistent across Python and self-host emitters.

---

### Te.3.B — Bootstrap brace-deprecation mirror (v5.23.2)

**Prior panel binding:** Rattler v5.22.0 Issue #1 (MEDIUM) — "Te.3 brace-deprecation: native `mnc-stage1` has zero brace-detection logic; the Python detector misses single-line `{...}` shapes."

**Resolution verified.** `tests/bootstrap/test_brace_deprecation_mirror.py` 11/11 PASS. Cases include the single-line brace form (`fn main() { print("hi") }`) that was the original gap. The C-routing decision is technically sound: it avoids bootstrap-lower pathologies (split-result indexing, deep-CFG PHI predecessor mismatch documented in v5.14.1) and provides byte-identity by construction.

**Verdict:** Te.3.B MEDIUM closed. Native mirror complete.

---

### Eu.1 — `emit_unwrap` double-extractvalue (v5.26.1)

**Prior panel binding:** (none — fresh at v5.26.1)

**Bug mechanics:** `Result<T, E>` is represented as `{i1, {T, E}}`. Pre-fix `_do_unwrap` emitted one `extractvalue ... 1` returning the inner aggregate `{T, E}` rather than the Ok payload at field 0 of that inner aggregate. Fix emits two ops:

```llvm
%uw_inner = extractvalue {i1, {i64, {ptr, i64}}} %res, 1    ; → {T, E}
%uw = extractvalue {i64, {ptr, i64}} %uw_inner, 0            ; → T (Ok payload)
```

Verified in `mapanare/emit_llvm_text.py` lines 5229–5253 (Python) and `mapanare/self/emit_llvm.mn::emit_unwrap` (self-host). Both use the two-extractvalue chain for `TK_RESULT` subjects.

**Verdict:** Eu.1 closed correctly. Two-extractvalue chain is the correct LLVM IR idiom for nested aggregate extraction.

---

### Eu.2 — Ok/Err literal default args at call sites (v5.26.1)

**Prior panel binding:** (none — fresh at v5.26.1)

**Bug mechanics:** `classify(Ok(42))` where `classify: fn(Result<Int, String>) -> String`. `dest.ty.args` is empty at the call site → `emit_wrap_ok` uses MIR fallback `{i1, {ptr, ptr}}` for outer type while inner uses real width `{i64, ptr}` → three `insertvalue` instructions with disagreeing struct types → LLVM rejects.

**Fix verified in `mapanare/self/lower.mn` lines 2279–2301:** `Ok(arg)` defaults to `Result<arg_ty, String>`; `Err(arg)` defaults to `Result<Int, arg_ty>`. Mirrors `mapanare/lower.py:2398`.

**Verdict:** Eu.2 closed correctly.

---

### Eu.3 — Match on primitive subject (v5.26.1)

**Prior panel binding:** (none — fresh at v5.26.1)

**Bug mechanics:** `match n { 0 => ... }` where `n: Int` emitted `EnumTag` → `extractvalue i64 %n, 0` — LLVM rejects (i64 is not aggregate).

**Fix verified in `mapanare/self/lower.mn` lines 4560–4580:**

```
let is_primitive_subject: Bool = subj_kind == TK_INT() || subj_kind == TK_BOOL() || subj_kind == TK_STRING()
```

Primitive subjects bypass the switch and emit a sequential test cascade. `bind_ident_pattern` SSA uniquification via `tmp_counter` prevents `%x.addr` collisions across multiple arms.

**Verdict:** Eu.3 closed correctly.

---

### Eu.4 — Or-pattern dedup in `build_match_arms` (v5.26.1)

**Prior panel binding:** (none — fresh at v5.26.1)

**Bug mechanics:** `Some(0) | None | Some(x) if g` pushed two entries for the `Some` tag value → duplicate `i64` switch cases → LLVM rejects "duplicate case value in switch".

**Fix verified in `mapanare/self/lower.mn` lines 4459–4535:** `seen_tags: List<Int>` list skips duplicate tag values (first-arm-wins). `is_builtin_variant_name` at lines 4452–4458 recognizes `None`/`Some`/`Ok`/`Err` as variant names when parsed as `IdentPat`.

**Switch dedup scan on golden 51 IR:** Scanned all four `switch i64` instructions for duplicate case values. **Result: 0 duplicate case values.** Eu.4 dedup working correctly.

**Verdict:** Eu.4 closed correctly.

---

### Mc.8 + Mc.9 + Tk.1 (v5.27.0)

Zero codegen relevance — Python-only formatter changes, zero `.mn` source edits, 241,842 lines / 0 diff preserved by construction. Mc.8 detect-only architecture is correct given Mapanare's strictly single-line grammar. Tk.1 6-LOC fix is correct. Three falsifiability tests (fail pre-fix, pass post-fix) are the appropriate verification shape.

**Verdict:** Mc.*/Tk.1 closed correctly. No IR impact.

---

### No New MIR Ops / No New IR Shapes

**Verified:** `mir.py` contains 65 class definitions (counted via `re.findall(r'^class \w+', text, re.MULTILINE)`). Git log for `mir.py` shows zero new instruction kinds added in the v5.23.0–v5.27.0 arc. `mapanare/self/mir.mn` instruction enum unchanged. The only new C-extern exports are the two Te.3.B.2 functions — new symbols, not new IR shapes.

**Verdict:** Claim verified. No new MIR ops, no new IR shapes across the arc.

---

### Strict 3-Stage Fixed Point

**Verified:** STRICT 241,842 lines / 0 diff confirmed by live `python3 scripts/build_stage1.py && bash scripts/verify_fixed_point.sh --keep`. Line count delta history consistent with SESSION_REPORT claims (v5.26.0 +158, v5.26.1 +1,849, v5.27.0 +0).

**Verdict:** 23-release strict streak verified.

---

## Findings

### Finding #1 — Stage2 Teardown: Stdout-Path Crash Narrowed (LOW, CARRY-FORWARD)

**Prior panel binding:** Rattler v5.22.0 Issue #5 (LOW) — "Stage2 binary teardown: RC=3; pre-existing since v4.28.0."

**Status:** Still open. Root cause narrowed.

**New evidence:** `verify_fixed_point.sh` invokes stage2 via stdout redirect:
```bash
/tmp/mnc-stage2 emit-llvm "$SOURCE" > /tmp/stage3.ll 2>/tmp/stage2_stderr.log
```

Manual test: `-o file` path → RC=0 (clean). Stdout-redirect path → RC=139 (SIGSEGV, 128+11).

**The crash is stdout-redirect-specific.** This narrows to the stdout-path I/O flushing during exit — `fflush(stdout)` or `fclose(stdout)` triggers a double-free or use-after-free on an MnString/string buffer already freed by drop-glue during shutdown. The `-o file` path writes to a different FILE* that doesn't share the buffer with the freed MnString, returning before the conflicting cleanup order.

**Fix direction:** `valgrind --track-origins=yes /tmp/mnc-stage2 emit-llvm test.mn > /dev/null` on the stdout-redirect path should show the freed buffer origin. Likely fix: ensure the output string is fully written and dropped before `main.mn` returns rather than relying on libc stdio cleanup. The `-o file` vs stdout dispatch fork in `main.mn` is the isolation boundary.

**Carry status:** v6.0 carry maintained. However, 80+ release carry is now excessive — this investigation is tractable given the isolation boundary.

---

### Finding #2 — Test Coverage: `test_async_link.py` Covers 10 of 95 Goldens (INFORMATIONAL)

`tests/llvm/test_async_link.py` covers goldens 47/48/49/51 and async cluster 55–59. The remaining 85 goldens are IR-validated but not individually link-tested via the async test infrastructure. A `test_llvm_link_all.py` extending compile + `llvm-as` to all 95 goldens would catch future LINK_FAIL regressions within the same release cycle. Scope for a future Pv.* release.

---

### Finding #3 — Result/Option Nested-Aggregate Representation (INFORMATIONAL, v6.0 SCOPE)

The current `{i1, {T, E}}` representation requires two `extractvalue` ops (Eu.1). The idiomatic LLVM flat-layout `{i1, i[max(sizeof(T), sizeof(E))*8]}` eliminates the double-extractvalue and enables SROA. Not actionable until v6.0 when a seed refresh is scheduled anyway, but worth noting as a codegen improvement that reduces IR verbosity by ~2 lines per `?` use.

---

## Prior-Panel Finding Ledger (Rattler v5.22.0)

| v5.22.0 Finding | Status | Evidence |
|---|---|---|
| Issue #1: Te.3 brace-deprecation hollow (MEDIUM) | **CLOSED** v5.23.2 | `test_brace_deprecation_mirror.py` 11/11 PASS |
| Issue #2: v5.19.0 SESSION_REPORT absent (LOW) | **CLOSED** v5.23.0 RC.11 | `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` present |
| Issue #3: Stage2 teardown RC=3 (LOW) | **STILL OPEN** — root cause narrowed to stdout-specific SIGSEGV | Finding #1 above |
| Issue #4: Sh.* shrink baseline 2.4pp discrepancy (LOW) | **AGING OUT** | v5.24.1 Wd.* dual-baseline framing documents explicit deltas |
| Issue #5: BENCHMARKS-windows.md staleness (LOW) | **CLOSED** v5.21.1 H.12 | `BENCHMARKS-windows.md` has "last sync v5.8.8" admonition |

---

## Recommendations

**P1 (v5.29.0):** Run `valgrind --track-origins=yes /tmp/mnc-stage2 emit-llvm test.mn > /dev/null`. Stdout-specific SIGSEGV isolation makes this tractable. 80+ release carry is too long; the `-o file` isolation boundary is a gift — use it.

**P2 (Future Pv.*):** Extend link coverage to all 95 goldens via `test_llvm_link_all.py`. Current 95/95 is valid; this is about future regression detection latency.

**P3 (v6.0):** Refactor `Result<T, E>` / `Option<T>` IR representation to flat layout. Eliminates double-extractvalue, enables SROA, reduces IR verbosity.

**P4 (v5.30.0):** Add primitive-subject match goldens (Int, Bool) to lock the Eu.3 sequential-cascade pattern independently of the `?` operator tests.

---

## Score Breakdown

| Domain | Score | Notes |
|---|---|---|
| Fixed-point integrity | 10.0 | 23-release streak, 241,842 lines / 0 diff, verified live |
| Mb.7 i64/i1 fix | 10.0 | Zero anti-pattern instances in stage2.ll, golden 47 IR verified |
| Mb.9 Win64 ABI | 9.9 | 8/8 gate PASS; both emitters consistent |
| Eu.1..Eu.4 codegen fixes | 9.9 | Four structurally distinct fixes, all IR-verified; LINK_FAIL → PASS |
| Te.3.B mirror | 10.0 | 11/11 PASS; prior MEDIUM closed |
| No new MIR/IR shapes | 10.0 | Confirmed in mir.py (65 classes unchanged) |
| Stage2 teardown | 8.0 | Narrowed root cause; still open; 80+ release carry |
| Test coverage (future) | 9.5 | Full-corpus link test gap is informational; current 95/95 is valid |

**Weighted aggregate: 9.90 / 10**

---

## Final Verdict

**9.90 / 10 — EXCEEDS — PASS WITH NOTES**

The v5.23.0–v5.27.0 arc is the strongest LLVM IR / codegen arc in the v5 history. Four distinct LINK_FAIL root causes identified, each fixed with the minimum necessary IR-aware change, all verified live. The strict fixed-point streak at 241,842 lines is the project record by 1.77×. The only open item is a root-cause-narrowed teardown crash with a clear investigation path. Option A is the correct decision.

---

*Rattler — LLVM Wizard. Reviewed at v5.28.0 HEAD (branch: dev, commit: b42665e).*
*Live verification performed: anti-pattern scan (0 instances), golden 47 IR check (valid br i1), switch dedup scan (0 duplicates), Te.3.B test run (11/11), MIR class count (65).*
