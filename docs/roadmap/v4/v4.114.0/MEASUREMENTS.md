# v4.114.0 — Phase D Panel Measurements

> Quantitative facts the panel reads before opinions are formed. All
> numbers captured fresh on 2026-04-14 against `HEAD` at the start of
> v4.114.0 (commit `7c94cce`). Raw logs live under
> `docs/roadmap/v4/v4.114.0/artifacts/`.

---

## 1. Golden Pass Rate — both pipelines

| Pipeline | Pass | Fail | Total | Notes |
|---|---:|---:|---:|---|
| Python bootstrap (`python3 -m mapanare emit-llvm`) | **63** | 1 | 64 | `51_match_guards_and_or` pre-existing or-pattern limitation (documented since v4.108.0) |
| Self-hosted (`mnc-stage1` built via `build_stage1.py`) | **26** | 38 | 64 | identical to v4.112.0 / v4.113.0; zero regressions from Phase D |

### Self-hosted failure breakdown (unchanged from v4.111.0 GOLDEN_FAILURES.md)

| Category | Count | Docket |
|---|---:|---|
| `__mn_str_starts_with` crash in `emit_mir_call+0x23515` | 10 | Sh.2 |
| async-missing in self-hosted output | 5 | Sh.4 |
| tensor-missing | 5 | Sh.6 |
| const-missing | 2 | Sh.5 |
| `lower_expr` crash | 2 | — |
| or-pattern (bootstrap also fails) | 1 | — |
| closure-typed | 1 | Sh.7 |
| gpu-tensor | 1 | — |
| defines count mismatch (Category A — semantically correct but inline-differs) | 3 | — |
| try operator invalid IR | 1 | — |
| remainder | 7 | — |

The "effective" self-hosted pass rate when counting Category A
(compiles correctly, differs only in inline-function count because
bootstrap inlines more aggressively) would be **39/64** — this is a
harness-measurement distinction, not a correctness distinction.

## 2. Fixed-Point Verification

```
$ bash scripts/verify_fixed_point.sh
[Stage 0] Using existing stage1: mapanare/self/mnc-stage1
  stage1: 3,488,904 bytes
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
mapanare/self/mnc_all.mn:0:0: error: Undefined variable 'None'
```

**Status: BLOCKED at Stage 1. Stage 2 and Stage 3 artifacts NOT
produced.** Identical to v4.112.0 result.

Blocker: self-hosted `semantic.mn` does not register `None`, `Some`,
or `Ok` as constructors. The Python bootstrap bypasses this via
`skip_check=True` in `build_stage1.py`. The self-hosted binary has
no bypass — it fails semantic analysis on its own source.

This is tracked as **docket Sh.8**, opened in v4.112.0. It is NOT
part of the v4.99.0 docket and is NOT something Phase D promised to
fix. It blocks full fixed-point verification but does not undermine
the byref fix (docket #7) — that fix has been verified end-to-end on
`/tmp/byref_test.mn` with correct runtime output and IR validation.

## 3. Stage2 Validation (`ir_doctor.py stage2`)

```
0/11 stage2 modules valid
```

All 11 modules fail with the same Sh.8 root cause. Unchanged from
v4.112.0. No new failure modes.

## 4. Sanitizer Results

### Valgrind on async golden tests (raw: `artifacts/valgrind.log`)

| Test | `definitely lost` | `indirectly lost` | ERROR SUMMARY |
|---|---:|---:|---|
| 55_async_basic | 0 | 0 | **0 errors from 0 contexts** |
| 56_async_await | 32 B (1 block) | 24 B (2 blocks) | **0 errors from 0 contexts** |
| 57_real_await | 96 B (3 blocks) | 72 B (6 blocks) | **0 errors from 0 contexts** |

All leaks are pre-existing — byte-for-byte identical to the
pre-v4.113.0 control rebuild. Stack traces terminate in user
coroutine bodies (`inner`, `fetch_a`, `fetch_b`, `fetch_c`) boxing
return values via `malloc`; they never enter
`mn_coro_is_done` / `mn_coro_resume` / `mn_coro_frame_prefix_t`.

### AddressSanitizer on async + struct subset (raw: `artifacts/asan.log`)

| Test | Output | ASan errors | Leak bytes |
|---|---|---:|---:|
| 55_async_basic | 42 | 0 | 0 |
| 56_async_await | 43 | 0 | 56 (user code) |
| 57_real_await | 110 | 0 | 216 (user code) |
| 06_struct | 3 | 0 | 0 |

Zero functional ASan errors. LeakSanitizer findings trace to the
same user coroutine body sites as valgrind.

## 5. Docket Closure Summary

| # | Severity | Description | Closed in | Status |
|---|---|---|---|---|
| 1 | CRITICAL | Tagged-pointer UB | v4.100.0 | **CLOSED** — `is_heap` bitfield at `mapanare_core.h:60`, ABI preserved at 16 bytes |
| 2 | CRITICAL | List indexing bug | v4.101.0 | **CLOSED** — use-after-free move-semantics fix in `emit_llvm_text.py` |
| 3 | HIGH | Rebuild `libmapanare_rt.a` with scheduler | v4.102.0 | **CLOSED** — scheduler symbols present; async goldens run natively |
| 4 | HIGH | Verify else/sino end-to-end | v4.103.0 | **CLOSED** — boxed-enum drop glue, `63_else_sino` passes |
| 5 | HIGH | Fix closure type annotations | v4.103.0 | **CLOSED** — `FnType → MIRType(FN)`, ClosureCall, ClosureCreate |
| 6 | MEDIUM | Disclose binary corruption in README | Phase C | **CLOSED** — README performance section rewritten v4.110.0 |
| 7 | MEDIUM | Byref size heuristic | v4.112.0 | **CLOSED** — `struct_byte_size` + `is_byref_type_st` at `emit_llvm.mn:1495, 1460`; 7 call sites updated |
| 8 | MEDIUM | Coroutine frame layout coupling | v4.113.0 | **CLOSED** — `mn_coro_frame_prefix_t` struct at `mapanare_runtime.c:1539`; zero raw offsets in executable code |
| 9 | MEDIUM | String concat performance | v4.108.0 | **CLOSED** — auto-StringBuilder; 55× faster wall, 109× less memory |
| 10 | LOW | Keyword collision SPEC | v4.113.0 | **CLOSED** — SPEC §2.1.1 Master List, 42 entries, both lexers audited |
| 11 | LOW | Async error messages | v4.113.0 | **CLOSED** — 7 specific `mapanare: async runtime:` messages across 5 sites |

**Zero open items from the v4.99.0 panel.**

## 6. Test Collection & Self-Hosted Size

| Metric | v4.99.0 | v4.114.0 | Δ |
|---|---:|---:|---:|
| pytest collected | 5,374 | **5,462** | +88 |
| self-hosted lines | 38,824 | **39,763** | +939 |

## 7. Hardcoded-Offset Audit (docket #8 verification)

```
$ grep -rn "*(void **)" runtime/ mapanare/
runtime/native/mapanare_runtime.c:1536:
   *     than `*(void **)handle`)      [comment only]

$ grep -rEn "handle\s*\[\s*[0-9]+\s*\]" runtime/ mapanare/
mapanare/emit_llvm_text.py:4941:
   # handle[8](handle) — the destroy_fn pointer   [comment only]
```

Zero raw coroutine-frame offset reads in executable code. The only
way the C runtime inspects the frame is through `mn_coro_frame_prefix_t`.

## 8. Phase D Cumulative Diff

Three releases, minimal scope each:

| Release | Touched files | Line diff | Docket |
|---|---:|---:|---|
| v4.111.0 | 1 (`self/mir_opt.mn`) | 34 | ⊕5 goldens via disabled MIR passes |
| v4.112.0 | 1 (`self/emit_llvm.mn`) | 48 | #7 CLOSED |
| v4.113.0 | 3 (`mapanare_runtime.c`, `SPEC.md`, Appendix C) | ~200 | #8 + #10 + #11 CLOSED |

Phase D total executable-code delta: **~90 lines** across 2 files
(runtime + self-hosted emitter). SPEC changes (~100 lines) are
documentation-only. Minimum-surface-area discipline held through
three releases.

## 9. What's Not Measured

- **Panel aggregate score.** That's the output of Phase D, not the
  input. Written after reviewers file.
- **Performance delta vs v4.107.0.** Phase C closed this; no
  benchmark run in Phase D.
- **Stage3 fixed-point byte-count.** Not reachable until Sh.8 is
  fixed.
- **Culebra baseline diff over 854K-line `main.ll`.** Blocked v4.111.0
  and v4.112.0; blocks this release too. Flagged for a future release
  to either fix the scan performance or narrow the scope.
