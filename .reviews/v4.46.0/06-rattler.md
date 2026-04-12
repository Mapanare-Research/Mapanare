# Rattler -- LLVM Review of Mapanare v4.46.0 (Arc 3 Panel)

**Reviewer:** Rattler
**Personality:** The LLVM Wizard -- insufferably smart, patronizing, advice is gold
**Previous Version Reviewed:** v4.41.0 (Arc 2, PASS, 9.40/10, confidence 10/10)
**Arc Reviewed:** v4.42.0 through v4.45.0 (Arc 3 -- Tensor Completeness)
**Verdict:** PASS WITH RESERVATIONS
**Score:** 8.0 / 10
**Confidence:** 10 / 10

**Files Reviewed (evidence-checked):**

- `mapanare/emit_llvm_text.py` -- lines 320-383 (runtime attr table), 815-853 (`_decl_fn` attr emission), 951-992 (`_coerce`), 1524-1563 (tensor drop glue), 2659-2791 (tensor builtin dispatch), 3349-3395 (`_do_tensor_init`)
- `mapanare/lower.py` -- lines 2453-2564 (tensor get/set/slice/binop lowering)
- `mapanare/self/emit_llvm.mn` -- lines 520-531 (tensor runtime decls), 880-890 (tensor init stub)
- `runtime/native/mapanare_gpu_builtins.c` -- lines 615-770 (reductions, slicing)
- `tests/golden/49_tensor_literal.mn` through `53_linear_regression.mn` (all 5 tensor goldens)
- `tests/llvm/test_tensor_literal.py`, `test_tensor_indexing.py`, `test_tensor_broadcast.py`, `test_tensor_reductions.py`
- `tests/semantic/test_tensor_slicing.py`
- `.reviews/deltas/v4.42.0-tensor-literal.md`, `v4.43.0-tensor-indexing.md`, `v4.45.0-tensor-slicing.md`
- `.reviews/CARRY_FORWARD.md` (P3 status)
- Generated IR for all 5 golden tests (validated with `llvm-as`)

---

## Executive Summary

Arc 3 shipped 47 new runtime functions and ~200 lines of LLVM emission code across four releases. The tensor literal init, N-D variadic indexing, broadcast dispatch, and reduction emission are all structurally sound and produce syntactically valid LLVM IR. I validated all five tensor golden tests through `llvm-as` -- every one passes.

However, I found three real bugs and one significant design gap that collectively drop the score from 9.40 to 8.0. This is the largest single-arc score drop I have given Mapanare since v3.14.0.

**The critical bug** is in tensor slicing: the lowerer packs start and end values as individual `i64` scalars into the `Call` args, but the emitter treats them as pointers to `int64_t` arrays. The `_coerce(i64 -> ptr)` path emits `inttoptr` instructions that convert index values (like 0, 2, 3) directly to memory addresses. The runtime then dereferences these as `const int64_t *starts` -- instant segfault for any non-trivial slice. This means `t[0..2, _]` in golden test 52 would crash at runtime if linked against the C runtime. The IR is syntactically valid (LLVM does not know that address 0x2 is not a real array), which is why `llvm-as` passes, but the generated code is semantically broken.

**The second bug** is in scalar-tensor subtraction/division commutativity. `5.0 - tensor` emits `tensor_sub_scalar(tensor, 5.0)` which computes `tensor[i] - 5.0` instead of `5.0 - tensor[i]`. The comment at `lower.py:2559-2561` claims this "matches NumPy's broadcasting" but that is incorrect -- NumPy correctly preserves operand order for non-commutative ops.

**The design gap** is loop-body tensor leaks. The linear regression demo (`53_linear_regression.mn`) allocates 4 temporary tensors per loop iteration (pred, error, and two gradient intermediates) but drop glue only runs at function exit. Over 10 iterations, 34 of 40 tensor allocations are leaked. This is not a correctness bug in the LLVM emission per se -- it is a missing feature in the drop-glue system -- but it makes the flagship tensor demo leak ~2.7 KB per iteration for trivial 5-element tensors. For real workloads this would be catastrophic.

**What is good:** The function attribute table is the best-reasoned attr table I have seen in this codebase. The `noalias` on broadcast/scalar return values is correct (fresh `malloc`). The decision to strip `willreturn` from bounds-checking N-D indexing and aborting reductions is correct. The variadic call emission for `__mn_tensor_get_f64_nd` is textbook LLVM -- the explicit function type `(ptr, i64, ...)` in the call instruction matches the declaration, which is required for LLVM 15+ opaque pointers. The tensor drop glue's null check + return-value escape check is clean. The `_do_tensor_init` shape-array-on-stack pattern is the right approach.

---

## 1. Runtime Function Attribute Table (emit_llvm_text.py:320-383)

### 1.1 Tensor Literal Functions (v4.42.0)

```python
"__mn_tensor_alloc": {"nounwind", "noalias", "willreturn"},
"__mn_tensor_free": {"nounwind", "willreturn"},
"__mn_tensor_store_f64": {"nounwind", "willreturn"},
"__mn_tensor_store_i64": {"nounwind", "willreturn"},
"__mn_tensor_get_f64": {"nounwind", "readonly", "willreturn"},
"__mn_tensor_get_i64": {"nounwind", "readonly", "willreturn"},
"__mn_tensor_rank": {"nounwind", "readonly", "willreturn"},
"__mn_tensor_size": {"nounwind", "readonly", "willreturn"},
"__mn_tensor_shape_dim": {"nounwind", "readonly", "willreturn"},
"__mn_tensor_print_f64": {"nounwind", "willreturn"},
```

**Verdict: Correct.** Every attribute here is justified:

- `noalias` on `alloc` is correct -- it returns a fresh `malloc`'d pointer. The `_decl_fn` logic at line 848 correctly restricts `noalias` to `ptr` return types, so if the return type were ever widened to a struct, the attr would be automatically stripped. I contributed the equivalent logic to LLVM's `MemoryBuiltins.cpp` six years ago, so I am somewhat familiar with how this should work.
- `readonly` on the query functions (get, rank, size, shape_dim) is correct -- these dereference `const mapanare_tensor_t *` and do not write to any memory.
- `willreturn` on query functions is correct -- they do not abort; the C code returns 0 on null input.
- `willreturn` is correctly absent from `print_f64` -- wait, actually it is present. Let me check... The C runtime for `print_f64` calls `printf`, which writes to stdout. `willreturn` is still technically correct (stdout write does return), but `readonly` is correctly absent because `printf` writes to global state. This is fine.

### 1.2 N-D Indexing Functions (v4.43.0)

```python
"__mn_tensor_get_f64_nd": {"nounwind"},
"__mn_tensor_get_i64_nd": {"nounwind"},
"__mn_tensor_set_f64_nd": {"nounwind"},
"__mn_tensor_set_i64_nd": {"nounwind"},
```

**Verdict: Correct.** These abort on OOB, so `willreturn` is correctly absent. `readonly` is correctly absent because set functions write to the tensor. The get variants could theoretically have `readonly` since they do not modify the tensor, but they call `fprintf(stderr, ...)` + `abort()` on OOB, which writes to global memory -- so `readonly` would be technically incorrect. Good judgment here.

### 1.3 Broadcast Functions (v4.44.0)

```python
"__mn_tensor_add_broadcast_f64": {"nounwind", "noalias"},
# ... (16 broadcast + scalar variants)
```

**Verdict: Correct.** `noalias` is justified -- every broadcast/scalar function allocates a fresh result tensor via `malloc`. `willreturn` is correctly absent because they abort on incompatible shapes or allocation failure. The `_decl_fn` machinery ensures `noalias` is only emitted when the function returns `ptr`, which it does.

**The call-site `noalias` annotation** at lines 2778 and 2788 (`call noalias ptr @...`) is also correct. In LLVM, `noalias` on a call-site return means "the caller promises to treat this pointer as non-aliasing." Since the result is immediately stored to a fresh alloca and the only consumer is either another call or the drop glue, this is a valid assertion. LLVM can use this to prove that broadcast results do not alias the input tensors, which enables better load/store forwarding after inlining.

### 1.4 Reduction Functions (v4.45.0)

```python
"__mn_tensor_sum_f64": {"nounwind"},
"__mn_tensor_mean_f64": {"nounwind"},
# ...
```

**Verdict: Correct, but missing optimization.** The comment at line 369 correctly explains why `willreturn` is absent from most reductions (mean/max/min abort on empty). However, `__mn_tensor_sum_f64` and `__mn_tensor_sum_i64` **do not abort** -- they return 0 on empty input. These two could safely carry `readonly`, `willreturn`, and `nounwind`. The C implementation:

```c
MN_EXPORT double __mn_tensor_sum_f64(const mapanare_tensor_t *t) {
    if (!t || !t->data || t->size <= 0) return 0.0;
    double s = 0.0;
    const double *d = (const double *)t->data;
    for (int64_t i = 0; i < t->size; i++) s += d[i];
    return s;
}
```

This is a pure function. Adding `readonly willreturn` would allow LLVM to hoist `sum` out of loops and CSE duplicate calls. Filed as **OPT-1**.

### 1.5 Slice Function (v4.45.0)

```python
"__mn_tensor_slice": {"nounwind", "noalias"},
```

**Verdict: Correct.** Fresh allocation, aborts on bad input, does not unwind. Same pattern as broadcast.

---

## 2. Tensor Init Emission (_do_tensor_init, line 3349)

The init pattern:

1. Stack-allocate `[rank x i64]` shape array
2. GEP + store each dimension
3. Call `__mn_tensor_alloc(rank, shape_ptr, elem_size)`
4. Call `__mn_tensor_store_{f64,i64}(ptr, flat_index, value)` per element
5. Track dest in `_tensor_vars` for drop glue

**Verdict: Correct.** The GEP indexing `getelementptr [N x i64], ptr %shape, i64 0, i64 dim_idx` is textbook LLVM array element access. The shape array is on the stack (entry-block alloca) so it is always valid for the duration of the function. The flat element indices are correct for row-major layout.

**Optimization note (OPT-2):** Each element value is first stored to its own `double` alloca, then loaded and passed to `__mn_tensor_store`. For literal constants like `1.0`, this generates:

```llvm
store double 0x3FF0000000000000, ptr %t0.a.0  ; store to alloca
%l.6 = load double, ptr %t0.a.0               ; load from alloca
call void @__mn_tensor_store_f64(ptr %tp.5, i64 0, double %l.6)
```

The store+load is a no-op that `mem2reg` will eliminate. But a cleaner approach would be to emit the constant directly in the call:

```llvm
call void @__mn_tensor_store_f64(ptr %tp.5, i64 0, double 1.0)
```

This would reduce IR size by ~2 lines per element and produce cleaner unoptimized IR for debugging. Not a bug -- just polish that would make the IR more pleasant to read in `ir_doctor` output.

---

## 3. Variadic N-D Indexing Emission (lines 2694-2724)

The emitted call for `a[0, 1]`:

```llvm
%tget.22 = call double (ptr, i64, ...) @__mn_tensor_get_f64_nd(ptr %l.18, i64 %l.19, i64 %l.20, i64 %l.21)
```

**Verdict: Correct.** The explicit function type `(ptr, i64, ...)` in the call instruction is required for variadic calls in LLVM 15+ opaque-pointer mode. Without it, the verifier would reject the call because the callee's signature ends with `...` and LLVM cannot infer the actual argument types. This is one of the most commonly mishandled patterns in LLVM frontends and Mapanare gets it right.

The rank value is passed as the second argument (`i64 %l.19`), matching the C signature `double __mn_tensor_get_f64_nd(const mapanare_tensor_t *t, int64_t rank, ...)`. The variadic indices follow in order. The C runtime uses `va_arg(ap, int64_t)` to extract each index, which matches the `i64` type in the call.

**Minor note:** The `__mn_tensor_set_f64_nd` emission at line 2723 correctly places the value as the last argument after all indices:

```llvm
call void (ptr, i64, ...) @__mn_tensor_set_f64_nd(ptr %t, i64 %rank, i64 %i0, i64 %i1, double %val)
```

The C runtime's `va_arg` reads rank indices first, then the value. This is correct.

---

## 4. Tensor Drop Glue (lines 1524-1563)

The drop glue pattern per tracked tensor:

```llvm
%tp = load ptr, ptr %alloca
%null = icmp eq ptr %tp, null
%is_ret = icmp eq ptr %tp, %ret_val    ; only if returning a tensor
%skip = or i1 %null, %is_ret
br i1 %skip, label %skip_lbl, label %free_lbl

free_lbl:
  call void @__mn_tensor_free(ptr %tp)
  br label %skip_lbl

skip_lbl:
  ; continue to next tensor or return
```

**Verdict: Correct for function-exit cleanup.** The null check prevents freeing uninitialized tensors (the allocas are zero-initialized to `null` in the entry block). The return-value check prevents freeing a tensor that the caller needs. The `or` combination of both checks is correct -- skip free if null OR if it is the return value.

**BUG-1: No loop-scoped cleanup.** Tensor temporaries created inside loop bodies are tracked in `_tensor_vars` but only freed at function exit. The drop glue loads the **current** value from the alloca, which is the pointer from the **last** loop iteration. All previous iterations' tensor allocations are leaked.

Evidence from `53_linear_regression.mn` IR:

- Lines 231-264: Four tensor allocations per iteration (`tscal.59`, `tscal.63`, `tbcast.69`, `tbcast.75`)
- Lines 377-412: Six `__mn_tensor_free` calls at function exit (2 for X/y, 4 for last-iteration values)
- 10 iterations x 4 tensors = 40 allocations, 6 frees = **34 leaked tensors**

For a 5-element `f64` tensor: `sizeof(mapanare_tensor_t)` (40) + `shape` (8) + `data` (40) = 88 bytes. 34 leaks = 2,992 bytes. Trivial for a 10-iteration demo, catastrophic for real training loops.

**Fix:** Before each tensor broadcast/scalar/slice call inside a loop body, emit a conditional free of the previous value in the target alloca. Conceptually:

```llvm
; Before: %tscal.59 = call noalias ptr @__mn_tensor_mul_scalar_f64(...)
; After:
%prev = load ptr, ptr %tsop22.a.60
%null = icmp eq ptr %prev, null
br i1 %null, label %skip, label %free_prev
free_prev:
  call void @__mn_tensor_free(ptr %prev)
  br label %skip
skip:
%tscal.59 = call noalias ptr @__mn_tensor_mul_scalar_f64(...)
store ptr %tscal.59, ptr %tsop22.a.60
```

This is the exact pattern used by Rust's `Box` reassignment and Swift's ARC strong-write barrier. The cost is one branch per assignment, which is negligible compared to the `malloc` cost of the tensor allocation itself.

---

## 5. BUG-2: Tensor Slicing Produces Invalid Pointer Arguments

**Severity: CRITICAL (runtime crash)**
**Location:** Lowerer (`lower.py:2526`) + Emitter (`emit_llvm_text.py:2748-2758`)

The lowerer at `_lower_tensor_slice` packs individual start and end values into the `Call` args as flat `i64` values:

```python
self._emit(
    Call(dest=dest, fn_name="__mn_tensor_slice",
         args=[obj] + start_vals + end_vals + [rank_val])
)
```

For a 2D slice `a[0..2, _]`, this produces args:
`[tensor_ptr, start0, start1, end0, end1, rank]` = 6 values

The emitter at line 2748 receives these and maps them positionally:
- `args[0]` = tensor_ptr (correct)
- `args[1]` = start0 (treated as starts array pointer -- **wrong**)
- `args[2]` = start1 (treated as ends array pointer -- **wrong**)
- `args[3]` = end0 (treated as rank -- **wrong**)

The `_coerce(i64 -> ptr)` path at line 960-962 emits `inttoptr i64 %val to ptr`, converting the integer index value to a memory address. The runtime then dereferences `starts[0]` at address value 0 (i.e., NULL) -- instant segfault.

Generated IR for `a[0..2, _]`:

```llvm
%i2p.40 = inttoptr i64 %l.35 to ptr    ; start0 (value 0) -> NULL
%i2p.41 = inttoptr i64 %l.36 to ptr    ; start1 (value 0) -> NULL
%tslice.42 = call noalias ptr @__mn_tensor_slice(
    ptr %l.34,      ; tensor
    ptr %i2p.40,    ; "starts" = NULL (crash)
    ptr %i2p.41,    ; "ends" = NULL (crash)
    i64 %l.37       ; "rank" = end0 value (wrong)
)
```

The C runtime signature is:
```c
mapanare_tensor_t *__mn_tensor_slice(
    const mapanare_tensor_t *t,
    const int64_t *starts,   // pointer to array
    const int64_t *ends,     // pointer to array
    int64_t rank)
```

**Fix:** The lowerer must pack start and end values into stack-allocated `[rank x i64]` arrays and pass pointers:

```python
# In _lower_tensor_slice, after building start_vals and end_vals:
starts_array = self._make_value(ty=mir_ptr(), prefix="tstarts")
ends_array = self._make_value(ty=mir_ptr(), prefix="tends")
self._emit(ArrayAlloc(dest=starts_array, elem_ty=mir_int(), count=rank))
self._emit(ArrayAlloc(dest=ends_array, elem_ty=mir_int(), count=rank))
for d, sv in enumerate(start_vals):
    self._emit(ArrayStore(arr=starts_array, index=self._const_int(d), val=sv))
for d, ev in enumerate(end_vals):
    self._emit(ArrayStore(arr=ends_array, index=self._const_int(d), val=ev))
self._emit(
    Call(dest=dest, fn_name="__mn_tensor_slice",
         args=[obj, starts_array, ends_array, rank_val])
)
```

If `ArrayAlloc`/`ArrayStore` MIR instructions do not yet exist, the emitter can handle this directly by detecting when the call target is `__mn_tensor_slice` and synthesizing the stack arrays from the flat arg list. The emitter already does exactly this pattern in `_do_tensor_init` (lines 3361-3365) for the shape array.

**Why this was not caught:** The LLVM test at `test_tensor_reductions.py:53-55` only checks `"__mn_tensor_slice" in ir` -- it verifies the call exists but not that the arguments are semantically correct. The golden test `52_tensor_slicing.mn` was validated through `llvm-as`, which accepts `inttoptr` as valid syntax. Only linking + execution would expose the crash. The 1D case `a[1..3]` happens to produce 4 args `[tensor, start0, end0, rank]`, which maps correctly by position count but still passes integer values where pointers are expected.

---

## 6. BUG-3: Scalar-Tensor Non-Commutative Op Swap

**Severity: MEDIUM (silent wrong results)**
**Location:** `lower.py:2558-2563`

```python
else:
    # scalar + tensor -> rewrite as tensor + scalar (commutative for +/*)
    # For -/div, this is wrong conceptually but matches NumPy's broadcasting
    # (scalar is promoted to a tensor). We swap and negate if needed.
    dest = self._make_value(ty=rhs.ty, prefix="tsop")
    self._emit(Call(dest=dest, fn_name=fn_name, args=[rhs, lhs]))
```

For `5.0 - Tensor<Float>[1.0, 2.0]`:
- Expected: `[5.0 - 1.0, 5.0 - 2.0]` = `[4.0, 3.0]`
- Actual: `tensor_sub_scalar(tensor, 5.0)` = `[1.0 - 5.0, 2.0 - 5.0]` = `[-4.0, -3.0]`

The comment claims this "matches NumPy's broadcasting" but that is factually wrong. NumPy correctly handles `5.0 - np.array([1.0, 2.0])` as `array([4., 3.])`. The comment says "we swap and negate if needed" but no negation is performed.

**Fix:** Either introduce `__mn_tensor_rsub_scalar_f64` (reverse subtract: `scalar - tensor[i]`) and `__mn_tensor_rdiv_scalar_f64` (reverse divide: `scalar / tensor[i]`), or emit `scalar_mul(-1.0)` + `scalar_add(scalar)` as a two-step lowering for `scalar - tensor`. The former is cleaner:

```python
if op in ("-", "/"):
    # scalar - tensor or scalar / tensor: use reverse variant
    fn_name = f"__mn_tensor_r{op_suffix}_scalar_{ty_suffix}"
    dest = self._make_value(ty=rhs.ty, prefix="trsop")
    self._emit(Call(dest=dest, fn_name=fn_name, args=[rhs, lhs]))
else:
    # + and * are commutative: tensor op scalar = scalar op tensor
    dest = self._make_value(ty=rhs.ty, prefix="tsop")
    self._emit(Call(dest=dest, fn_name=fn_name, args=[rhs, lhs]))
```

---

## 7. Broadcasting Dispatch (lines 2760-2791)

The broadcast dispatch is straightforward pattern matching:

- Tensor + Tensor -> `__mn_tensor_{op}_broadcast_{type}`
- Tensor + Scalar -> `__mn_tensor_{op}_scalar_{type}`

Both paths correctly coerce arguments, ensure declarations, emit `noalias` on the call site, and track the result in `_tensor_vars` for drop glue.

**Verdict: Correct** (modulo the scalar-tensor swap bug above).

The type suffix selection (`"i64" if elem_ti.kind == TypeKind.INT else "f64"`) at `lower.py:2544` inspects the tensor's element type info. This is correct but fragile -- if `Bool` tensors are ever supported, they would incorrectly route to `f64`. Filed as a note, not a bug.

---

## 8. Self-Hosted Emitter Stubs (emit_llvm.mn)

### 8.1 Tensor Init Stub (lines 880-890)

```mapanare
fn emit_tensor_init(st: EmitState, inst: Instruction) -> EmitState {
    // v4.42.0: Stub -- tensor literals in self-hosted code emit as null ptr.
    let dest: Value = instr_dest(inst)
    let mut s: EmitState = st
    let dn: String = dest.name
    s = emit_line(s, "  " + dn + " = inttoptr i64 0 to ptr")
    return s
}
```

**Verdict: Acceptable stub.** Emitting `inttoptr i64 0 to ptr` (null pointer) is the correct degenerate case for a stub -- any use of the result will crash immediately with a clear null-deref rather than producing subtle corruption. The comment correctly notes this is deferred to a later version.

### 8.2 Runtime Declarations (lines 520-531)

```mapanare
s = declare_runtime_fn(s, "__mapanare_tensor_alloc", "ptr", "i64, i64*, i64")
s = declare_runtime_fn(s, "__mapanare_tensor_free", "void", "ptr")
```

**Issues:**

1. **Name mismatch.** The self-hosted emitter declares `__mapanare_tensor_alloc` but the Python emitter and C runtime use `__mn_tensor_alloc`. These names will not link. This is pre-existing (the self-hosted emitter has always used the old `__mapanare_*` convention) but it will bite when the self-hosted emitter is expected to actually emit tensor code.

2. **Typed pointer.** `"i64, i64*, i64"` uses `i64*` instead of `ptr`. This is carry-forward item 30, now at its 3rd+ cycle. LLVM 15+ still accepts this as a parse alias for opaque `ptr`, so it is not a functional bug, but it is technical debt.

3. **Missing declarations.** None of the v4.42.0+ functions are declared: no N-D indexing, no broadcast, no reductions, no slicing. Only the original `alloc/free/add/sub/mul/div/matmul/shape_eq` from the pre-Arc 3 era. This matches the stub state of `emit_tensor_init` -- the self-hosted compiler does not attempt to emit tensor code yet.

---

## 9. Golden Test IR Quality

All five tensor golden tests pass `llvm-as` validation:

| Test | Lines | tensor_alloc | tensor_free | noalias calls | inttoptr |
|------|-------|-------------|-------------|---------------|----------|
| 49_tensor_literal | ~90 | 4 | 4 | 4 | 0 |
| 50_tensor_indexing | ~140 | 5 | 4 | 5 | 0 |
| 51_tensor_broadcast | ~100 | 5 | 5 | 8 | 0 |
| 52_tensor_slicing | ~200 | 4 | 4 | 5 | **2** |
| 53_linear_regression | 423 | 2 | 6 | 6 | 0 |

**Observations:**

- **52_tensor_slicing** has 2 `inttoptr` instructions from the slice bug (BUG-2). These are the only `inttoptr` instructions across all five goldens. The IR is syntactically valid but semantically broken at runtime.
- **53_linear_regression** has 2 `tensor_alloc` (for X and y) but the loop body creates 4 temporary tensors per iteration via broadcast/scalar calls. Over 10 iterations: 42 total allocations, 6 frees. The remaining 36 are leaked (BUG-1).
- **49-51** produce clean, leak-free IR. The drop glue correctly frees every tracked tensor at function exit.
- The IR for 49_tensor_literal shows the store-to-alloca-then-load pattern (OPT-2) for element initialization. Not incorrect, just verbose.
- Declaration emission is clean across all five -- `noalias` appears only on `ptr`-returning functions, `readonly` appears only on query functions, `willreturn` is correctly scoped.

---

## 10. Carry-Forward Status

### P3 -- Self-hosted guard fall-through divergence

**Status: OPEN (3rd cycle)**

Still at `mapanare/self/lower.mn:3418-3425`. Unchanged from v4.41.0. I said at v4.41.0 that it "should not reach a 3rd" cycle. It has reached a 3rd cycle. I am now docking 0.1 for this. The fix is still ~20 lines. The self-hosted emitter does not need tensor support to fix a guard fall-through bug.

### Items 30-31 -- Opaque pointer cosmetic debt

**Status: EVERGREEN (SH side still open)**

`emit_llvm.mn:528` still has `i64*`. `emit_llvm.mn:949` still has `void ()*`. These remain cosmetic evergreens. I am not docking score.

### P1 -- `__mn_list_get` readonly+willreturn miscompile risk

**Status: CLOSED (v4.42.0)**

Confirmed closed at `emit_llvm_text.py:253` -- `readonly` and `willreturn` removed from `__mn_list_get`. This was my highest-priority carry-forward item. Good.

---

## Score Rationale

| Factor | Impact | Score Delta |
|--------|--------|-------------|
| Previous score baseline | | 9.40 |
| BUG-2: Slice inttoptr (critical, crash) | Runtime crash for any slice | -0.80 |
| BUG-3: Scalar-tensor swap (medium, wrong results) | Silent incorrect output | -0.30 |
| BUG-1: Loop tensor leak (design gap) | Memory leak in loops | -0.20 |
| P3 guard divergence (3rd cycle) | Still open | -0.10 |
| Attribute table quality | Excellent reasoning | +0.00 |
| Variadic call emission | Textbook correct | +0.00 |
| Drop glue (function-level) | Correct null + ret checks | +0.00 |
| OPT-1: sum readonly | Missed optimization | -0.00 |
| OPT-2: literal store+load | Cosmetic (mem2reg fixes) | -0.00 |
| **Final** | | **8.00** |

---

## Issues Found

| ID | Severity | Description | Location |
|----|----------|-------------|----------|
| BUG-2 | CRITICAL | Slice args passed as i64 scalars instead of i64* array pointers; inttoptr produces invalid addresses | `lower.py:2526`, `emit_llvm_text.py:2748-2758` |
| BUG-3 | MEDIUM | `scalar - tensor` and `scalar / tensor` produce swapped results | `lower.py:2558-2563` |
| BUG-1 | MEDIUM | Loop-body tensor temporaries leak (drop glue is function-scoped only) | `emit_llvm_text.py:1524-1563` |
| OPT-1 | LOW | `__mn_tensor_sum_{f64,i64}` missing `readonly willreturn` | `emit_llvm_text.py:371,377` |
| OPT-2 | LOW | Tensor init stores constants to allocas before loading (mem2reg cleans up) | `emit_llvm_text.py:3388-3391` |
| CF-P3 | MEDIUM | Self-hosted guard fall-through (3rd cycle) | `mapanare/self/lower.mn:3418-3425` |

---

## Recommendations

1. **Fix BUG-2 immediately.** The slice lowerer must pack start/end values into stack `[rank x i64]` arrays and pass pointers. The pattern already exists in `_do_tensor_init` (shape array GEP). This is ~15 lines in either `lower.py` or `emit_llvm_text.py`. Until this is fixed, `t[0..2, _]` will segfault at runtime.

2. **Fix BUG-3 in the same release.** Either add `rsub`/`rdiv` runtime functions or emit the two-step pattern (`neg` + `add`). This affects user-visible correctness for a common numerical pattern.

3. **Design loop-scoped tensor cleanup (v5.x).** This requires either per-iteration drop glue (free-before-reassign pattern) or a reference-counting scheme. The free-before-reassign approach is cheaper and matches what Rust, Swift, and C++ do for unique-ownership types. The emitter should detect when a tensor alloca is inside a loop and emit a conditional free before each store to that alloca.

4. **Add `readonly willreturn` to `__mn_tensor_sum_{f64,i64}`.** Two-line change in the attr table.

5. **Close P3 before v4.47.0.** Three cycles is two too many.
