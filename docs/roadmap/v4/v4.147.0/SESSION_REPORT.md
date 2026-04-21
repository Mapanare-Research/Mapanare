# v4.147.0 Session Report — E3: parameter-level noalias

**Release:** v4.147.0
**Experiment:** E3 of E1-E8 (perf arc)
**Outcome:** DEAD END
**Date:** 2026-04-19
**Duration:** Single session

---

## 1. Pre-flight state

- VERSION bumped from 4.146.0 to 4.147.0
- `make build-rt` → `libmapanare_rt.a` (8 modules, MAPANARE_VERSION=4.147.0)
- `python3 scripts/build_stage1.py` → `mnc-stage1` (3,566,736 bytes stripped)
- Non-bootstrap pytest: 5,233 passed / 0 failed / 115 skipped / 9 xfailed
- Goldens: 54/66 (12 failed — unchanged from v4.146.0)
- Lint: ruff 0, black 349 unchanged, mypy 0 errors across 52 files
- Fixed-point: NEAR FIXED POINT (4 diff lines, version metadata only)
- ASan: 55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN
- Valgrind: 0 CLEAN / 62 WARNINGS_ONLY / 4 ERRORS (Ge.1 residuals)

## 2. Baseline measurements

Full 6-bench sweep, 20 runs each:

| Benchmark     | Mapanare (ms) | Rust (ms) | Ratio |
|---------------|--------------|-----------|-------|
| fib_recursive | 23.347       | 18.338    | 1.27x |
| quicksort     | 2.384        | 0.368     | 6.48x |
| struct_alloc  | 1.159        | 0.016     | 72.4x |
| enum_match    | 1.344        | 0.284     | 4.73x |
| prime_sieve   | 3.395        | 1.756     | 1.93x |
| string_concat | 1.660        | 0.040     | 41.5x |

Vectorization diagnostics (opt -O3 -pass-remarks):
- quicksort: 0 vectorized / 5 failed
- prime_sieve: 0 vectorized / 1 failed
- struct_alloc: 0 vectorized / 0 failed (no loops to vectorize)

## 3. The critical discovery: LLVM noalias only applies to ptr parameters

The PLAN.md hypothesis was: "MIR-level escape analysis proves List<T>
parameters non-aliasing → emitting `noalias` unblocks LLVM loop-vectorize
→ 15-40% wall improvement."

This hypothesis collapsed during the IR diff phase. Three facts:

### Fact 1: Mapanare passes compounds by value, not by reference

The emitter's `_use_byref()` function determines how parameters are
passed. It checks `_BYREF_BYTES = 64`:

```python
@staticmethod
def _use_byref(ty: str) -> bool:
    return ty.startswith("{") and ty.endswith("}") and _tsz(ty) > 64
```

All key types are under 64 bytes:
- `List<T>` → `{ptr, i64, i64, i64, i64}` → 40 bytes → **by value**
- `String` → `{ptr, i64}` → 16 bytes → **by value**
- `Map<K,V>` → Robin Hood table → 48 bytes → **by value**
- `Enum` → `{i64, ptr}` → 16 bytes → **by value**

Rust, by contrast, passes `Vec<i64>` as `ptr noalias ... dereferenceable(24)`.

### Fact 2: noalias is a pointer parameter attribute

From the LLVM LangRef:

> This indicates that objects accessed via pointer values **based on
> the argument** or the return value are not also accessed, during the
> execution of the function, via pointer values not based on the
> argument or return value.

The key phrase: "pointer values based on the argument." The argument
must be a pointer. LLVM does not accept `noalias` on aggregate types
like `{ptr, i64, i64, i64, i64}`. The attribute is syntactically
invalid for non-pointer parameters.

### Fact 3: The vectorization barriers are not aliasing

Even if `noalias` could be applied to the aggregate parameters, the
`loop-vectorize` pass fails for unrelated reasons:

1. **quicksort/partition:** "control flow cannot be substituted for a
   select" — the conditional swap `if arr[j] < pivot { swap(arr, i, j) }`
   contains an irregular control flow pattern that the vectorizer can't
   convert to a select instruction.

2. **prime_sieve/is_prime:** "could not determine number of loop
   iterations" — the loop `while d * d <= n` has a data-dependent
   trip count that the vectorizer can't analyze.

3. **struct_alloc/main:** No vectorization remarks at all — the loop
   body calls `make_point(i)` which is a function call, and the
   vectorizer doesn't vectorize across function boundaries (without
   inlining + re-analysis).

## 4. Decision: implement anyway, document the dead end

Despite the dead end, I implemented the escape analysis pass for three
reasons:

1. **The pass is sound and will activate for future ABI changes.**
   If E5/ABI.1 (v4.149.0) lowers `_BYREF_BYTES` to 24 or 16, List
   and String parameters will become `ptr`-typed, and the noalias
   marking will fire.

2. **Closure env pointers are already `ptr`-typed.** The pass marks
   closure environment pointers (`ptr %__env_ptr`) when they pass
   escape analysis. This could benefit closure-heavy workloads.

3. **The escape analysis precision rules are the artifact that matters
   most.** This is the experiment where the precision documentation
   matters more than the delta. Future experiments can reference these
   rules instead of re-deriving them.

## 5. Implementation details

### 5.1 MIRParam.attrs field (mir.py)

Added a `attrs: set[str]` field to `MIRParam`. This is the first
parameter-level metadata in the MIR. Uses a set for extensibility
(future attributes like `readonly`, `nocapture` can reuse this).

```python
@dataclass(slots=True)
class MIRParam:
    name: str = ""
    ty: MIRType = field(default_factory=mir_unknown)
    attrs: set[str] = field(default_factory=set)  # v4.147.0 E3
```

### 5.2 mark_noalias_params pass (mir_opt.py)

~134 logic lines. Module-level pass (needs visibility into all call
sites). Runs after DFE so dead functions don't pollute the analysis.

**Helper functions:**

- `_param_escapes(param_name, fn)` — checks 6 escape criteria:
  Return, FieldSet, IndexSet, ListPush, ClosureCreate, AgentSend,
  and unknown function calls. Uses the same `_NON_CAPTURING_FNS`
  allowlist as the existing heap-to-stack escape analysis.

- `_param_self_aliased_in_recursive_call(param_name, fn)` — checks
  if the function calls itself with the same parameter name. This
  catches `qsort(arr, lo, hi)` calling `qsort(arr, lo, p-1)`.

- `_call_sites_pass_distinct_args(module, target_fn, param_idx)` —
  checks all call sites in the module to verify no two arguments
  at different parameter positions share the same SSA name. This
  catches `compare(list_a, list_a)` patterns.

**Main pass:**
For each non-main function, for each non-scalar, non-Signal/Stream/Agent
parameter:
1. Check escape → skip if escapes
2. Check recursive self-aliasing → skip if aliased
3. Check call-site distinctness → skip if same SSA passed twice
4. Mark `noalias_ok` in `p.attrs`

**Excluded types:** Signal, Stream, Agent — the runtime may internally
share pointers on these paths (e.g., signal subscriber lists, agent
message rings).

### 5.3 Emitter hook (emit_llvm_text.py)

Two insertion points:

1. **byref params** (line ~2450): If `p.attrs` contains `noalias_ok`,
   emit `ptr noalias %name.byref` instead of `ptr %name.byref`.

2. **direct ptr params** (line ~2459): If `ty == PTR` and `p.attrs`
   contains `noalias_ok`, emit `ptr noalias %name` instead of
   `ptr %name`. This covers closure env pointers.

### 5.4 Pipeline integration

`mark_noalias_params(module)` is called in `optimize_module()` after
`dead_function_elimination()`. Gated behind `level >= O2`. Does not
participate in the per-function fixpoint loop (it's a module-level
pass, runs once, and is idempotent).

## 6. Precision rules considered but rejected

### 6.1 Alias scope metadata instead of parameter attributes

LLVM has `!alias.scope` and `!noalias` metadata that can be attached
to individual load/store instructions. This would allow saying "the
load through the List data pointer does not alias stores through other
pointers" even when the List is passed by value.

**Rejected because:** This requires tracking pointer provenance through
the emitter — which field of which aggregate was loaded, and whether
that field could overlap with another aggregate's field. The complexity
is O(params^2 * instructions) and the implementation risk is high.
Reserved for a dedicated experiment if E5/ABI.1 doesn't close the gap.

### 6.2 Lowering _BYREF_BYTES to enable noalias on List params

If `_BYREF_BYTES` were lowered from 64 to 24, List (40 bytes) and Map
(48 bytes) would be passed by reference (`ptr`), enabling `noalias`.

**Rejected for E3 because:** This is an ABI change that affects every
function in the compiler. It's the right fix — but it's E5's scope
(v4.149.0), not E3's. E3 was scoped to "can we get a win with just
an attribute, without changing the ABI?"

### 6.3 Marking returned parameters noalias (caller-side)

Some callers could benefit from knowing that a callee's return value
doesn't alias the callee's parameters. This would require interprocedural
analysis beyond what E3 implements.

**Rejected because:** The return value already has its own `noalias`
via `_RUNTIME_FN_ATTRS` for allocator functions. User functions that
return fresh allocations are a small minority, and the benefit is
speculative.

### 6.4 noalias on sret parameters (already done)

The emitter already marks sret parameters as `noalias` since v4.84.0:

```python
param_parts.append(f"ptr noalias sret({self._fn_sret_ty}) {self._sret_ptr}")
```

This is correct: the caller allocates the return slot, so it cannot
alias any other pointer the callee can observe.

## 7. Test coverage

16 new tests in `tests/mir_opt/test_noalias_pass.py`:

| Test | What it verifies |
|------|-----------------|
| `test_non_escaping_list_param_marked` | Basic positive case |
| `test_returned_param_not_marked` | Return = escape |
| `test_recursive_self_call_not_marked` | Recursive aliasing |
| `test_closure_captured_param_not_marked` | Closure capture = escape |
| `test_field_stored_param_not_marked` | FieldSet = escape |
| `test_same_ssa_passed_twice_not_marked` | Call-site aliasing |
| `test_two_distinct_allocas_marked` | Multi-param positive case |
| `test_signal_param_excluded` | Runtime type exclusion |
| `test_stream_param_excluded` | Runtime type exclusion |
| `test_agent_param_excluded` | Runtime type exclusion |
| `test_scalar_param_not_marked` | Scalar = not pointer |
| `test_agent_sent_param_not_marked` | AgentSend = escape |
| `test_list_pushed_param_not_marked` | ListPush = escape |
| `test_index_stored_param_not_marked` | IndexSet = escape |
| `test_main_function_skipped` | main always skipped |
| `test_idempotent` | Pass is idempotent |

All 16 pass. The test suite covers all 6 escape criteria and all 3
exclusion rules (scalar, runtime types, main).

## 8. Post-patch verification

| Gate | Before | After | Status |
|------|--------|-------|--------|
| Non-bootstrap pytest | 5,233 / 0 | 5,251 / 0 (+16 tests +2 dir) | PASS |
| Goldens (mnc-stage1) | 54 / 66 | 54 / 66 | PASS |
| Fixed-point | NEAR (4 lines) | NEAR (4 lines) | PASS |
| ASan ASAN_ERROR | 0 | 0 | PASS |
| Valgrind ERRORS | 4 | 4 | PASS |
| Lint (ruff/black/mypy) | clean | clean | PASS |
| 5% rule (target benches) | — | 0% (binary identical) | **FAIL** |

## 9. What this teaches for the rest of the arc

1. **E5/ABI.1 (v4.149.0) is the correct vehicle for noalias wins.**
   Lowering `_BYREF_BYTES` to pass List/String/Map by reference will
   enable parameter-level `noalias` without any additional escape
   analysis work — the pass implemented here will activate automatically.

2. **The vectorization barriers are orthogonal to aliasing.** Even after
   E5 adds `noalias`, the quicksort and prime_sieve loops won't
   vectorize because of control flow and trip count issues. Vectorization
   is not the right metric for E5; load/store elimination and LICM are.

3. **Subprocess-spawn overhead dominates short benchmarks.** The
   fib_recursive and string_concat runs showed 13-20% variance between
   baseline and patched measurements of the SAME binary. The
   `__BENCH_METRICS__` internal timing methodology (used by Go, C,
   Python) is more reliable for benchmarks under 5ms.

4. **Dead ends narrow the search space.** E3 rules out parameter-level
   attributes as a lever. The remaining options for the Rust gap are:
   - ABI changes (E5)
   - Allocator throughput (E7)
   - MIR-level pass re-enablement (E8)
   These are all architectural changes, not attribute tweaks.

## 10. Files changed

| File | Lines added | Lines removed | What |
|------|-----------|-------------|------|
| `mapanare/mir.py` | 1 | 0 | `attrs: set[str]` field on MIRParam |
| `mapanare/mir_opt.py` | 134 | 0 | `mark_noalias_params` pass + helpers |
| `mapanare/emit_llvm_text.py` | 4 | 2 | noalias emission on ptr params |
| `tests/mir_opt/__init__.py` | 0 | 0 | New test directory |
| `tests/mir_opt/test_noalias_pass.py` | 290 | 0 | 16 precision tests |
| `docs/roadmap/v4/v4.147.0/` | ~550 | 0 | BASELINE, IR_DIFF, HYPOTHESIS, RESULTS, SESSION_REPORT |
| `docs/roadmap/v4/PERF_EXPERIMENTS.md` | 1 | 0 | E3 ledger entry |

Total: ~139 logic lines of compiler code, 290 test lines, ~550 doc lines.

## 11. Carry-forward

- **No new dockets opened.** The pass is sound, safe, and tested.
- **E5 dependency noted.** When `_BYREF_BYTES` is lowered, the noalias
  marking will activate automatically on List/String/Map parameters.
  No additional work needed in mir_opt.py.
- **Closure noalias is latent.** The pass marks closure env pointers
  `noalias_ok` today, but no benchmark exercises this path yet. A
  closure-heavy benchmark would be needed to measure the impact.
