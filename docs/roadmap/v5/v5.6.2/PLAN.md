# Mapanare v5.6.2 — "Sh.6 Phase 3: Tensor Broadcast + Scalar Binops"

> **Close golden 51_tensor_broadcast by routing tensor-tensor and
> tensor-scalar `+` / `-` / `*` / `/` through the existing
> `__mn_tensor_{op}_{broadcast,scalar}_{f64,i64}` runtime family.**
> Second of three Sh.6 continuation releases (after v5.6.1's
> multi-dim indexing).

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.1 shipped (multi-dim indexing; golden 50 PASS)
**Estimated work:** 1 session (~2–4 hours). Smallest of the v5.6.x
trio — the runtime already exists, the Python recipe is 40 LOC, and
no parser changes needed.
**Owner docket:** Sh.6 (opened v4.111.0; Phases 1–2 closed v5.6.0/5.6.1)

---

## Why this release exists

### The failing golden

Baseline after v5.6.1:

| Test | mnc-stage1 | bootstrap | Disposition |
|---|---|---|---|
| `50_tensor_indexing` | PASS | OK | Closed v5.6.1 |
| `51_tensor_broadcast` | **FAIL (emit — ptr/i64)** | OK | **Closes here** |
| `53_linear_regression` | FAIL (binop + `.sum()`) | OK | Partial close (binops) |

Exact self-hosted emitted IR on golden 51 today (v5.6.0):

```
; ModuleID = '51_tensor_broadcast'
...
%t14 = add nsw i64 %a_val12, %b_val13
; 'a_val12' defined with type 'ptr' but expected 'i64'
```

Root cause: `lower.mn::lower_binop` has no branch for
`lhs.ty.kind == TENSOR || rhs.ty.kind == TENSOR`. It falls through
to the generic integer add, which takes the pointer values of the
two tensor operands and tries to add them as i64. `llvm-as`
correctly rejects.

The Python bootstrap has the exact recipe at
`mapanare/lower.py:2843-2882` — `_lower_tensor_binop`. 40 LOC.
Routes to one of:

- `__mn_tensor_{add,sub,mul,div}_broadcast_{f64,i64}` — tensor op tensor
- `__mn_tensor_{add,sub,mul,div}_scalar_{f64,i64}` — tensor op scalar
- `__mn_tensor_{rsub,rdiv}_scalar_{f64,i64}` — scalar op tensor for non-commutative ops

### Also relevant: 53_linear_regression

Golden 53 uses `X * w + b` (tensor * scalar + scalar), `pred - y`
(tensor - tensor), `error * X` (tensor * tensor), `.sum()` (reduction
— v5.6.3), and `* 2.0 / n` (scalar chain). After v5.6.2 closes the
binops but not reductions, 53 still fails because `.sum()` is
missing. That's fine — 53 gets its structural pieces here; the
method-call close happens in v5.6.3.

### Runtime state — already complete

`runtime/native/mapanare_gpu_builtins.c:549-720` — all 16 op×type
broadcast fns + 16 scalar fns exist and are tested. `emit_llvm_text.py`
declares them (`emit_llvm_text.py:357-390`).

### Sizing

| File | ~LOC |
|---|---:|
| `mapanare/self/lower.mn` — `lower_tensor_binop` helper + dispatch in `lower_binop` | ~80 |
| `mapanare/self/semantic.mn` — binop result-type for tensor operands | ~20 |
| `mapanare/self/emit_llvm.mn` — 20 new runtime declarations + attrs + call routing | ~70 |
| Tests | ~40 |
| **Total** | **~210** |

---

## Scope

### What ships

#### 9.2a — Semantic: tensor binop result type

`semantic.mn`:

- In `infer_binop` (or equivalent), add a case: if either operand is
  `TENSOR<T>`, the result type is `TENSOR<T>`.
- For tensor-scalar, the tensor's element type must match the scalar
  type (Float tensor ⊕ Float scalar, Int tensor ⊕ Int scalar).
  Python currently allows implicit int→float promotion; this release
  mirrors that behavior.

#### 9.2b — Lower: `lower_tensor_binop` helper

`lower.mn`:

```mn
fn lower_tensor_binop(st: LowerState, op: String, lhs: Value, rhs: Value) -> LowerResult {
    let op_suffix: String = tensor_op_suffix(op)  // "add" | "sub" | "mul" | "div"
    let tensor_val: Value = if is_tensor_ty(lhs) { lhs } else { rhs }
    let elem_kind: String = tensor_elem_kind_of(tensor_val)  // "Int" | "Float"
    let ty_suffix: String = if elem_kind == "Int" { "i64" } else { "f64" }

    let both_tensor: Bool = is_tensor_ty(lhs) && is_tensor_ty(rhs)
    let mut s: LowerState = st
    let dest: Value = make_value_typed(s, tensor_val.ty, "tbop")

    if both_tensor {
        let fn_name: String = "__mn_tensor_" + op_suffix + "_broadcast_" + ty_suffix
        s = emit_instr(s, Instruction::Call(dest, fn_name, [lhs, rhs]))
    } else {
        if is_tensor_ty(lhs) {
            // tensor op scalar
            let fn_name: String = "__mn_tensor_" + op_suffix + "_scalar_" + ty_suffix
            s = emit_instr(s, Instruction::Call(dest, fn_name, [lhs, rhs]))
        } else {
            // scalar op tensor
            if op == "+" || op == "*" {
                // Commutative — reuse forward scalar fn, swap args
                let fn_name: String = "__mn_tensor_" + op_suffix + "_scalar_" + ty_suffix
                s = emit_instr(s, Instruction::Call(dest, fn_name, [rhs, lhs]))
            } else {
                // Non-commutative — reverse scalar fn (rsub / rdiv)
                let fn_name: String = "__mn_tensor_r" + op_suffix + "_scalar_" + ty_suffix
                s = emit_instr(s, Instruction::Call(dest, fn_name, [lhs, rhs]))
            }
        }
    }
    return new_lower_result(dest, s)
}
```

Dispatch in `lower_binop` before falling through to the numeric /
string path:

```mn
if is_tensor_ty(lhs_r.value) || is_tensor_ty(rhs_r.value) {
    if op == "+" || op == "-" || op == "*" || op == "/" {
        return lower_tensor_binop(s, op, lhs_r.value, rhs_r.value)
    }
}
```

#### 9.2c — Emit: 20 runtime declarations

`emit_llvm.mn::declare_all_runtime`:

```
// Broadcast (tensor ⊕ tensor)
s = declare_runtime_fn(s, "__mn_tensor_add_broadcast_f64", "ptr", "ptr, ptr")
s = declare_runtime_fn(s, "__mn_tensor_sub_broadcast_f64", "ptr", "ptr, ptr")
s = declare_runtime_fn(s, "__mn_tensor_mul_broadcast_f64", "ptr", "ptr, ptr")
s = declare_runtime_fn(s, "__mn_tensor_div_broadcast_f64", "ptr", "ptr, ptr")
s = declare_runtime_fn(s, "__mn_tensor_add_broadcast_i64", "ptr", "ptr, ptr")
s = declare_runtime_fn(s, "__mn_tensor_sub_broadcast_i64", "ptr", "ptr, ptr")
s = declare_runtime_fn(s, "__mn_tensor_mul_broadcast_i64", "ptr", "ptr, ptr")
s = declare_runtime_fn(s, "__mn_tensor_div_broadcast_i64", "ptr", "ptr, ptr")

// Scalar (tensor ⊕ scalar)
s = declare_runtime_fn(s, "__mn_tensor_add_scalar_f64", "ptr", "ptr, double")
s = declare_runtime_fn(s, "__mn_tensor_sub_scalar_f64", "ptr", "ptr, double")
s = declare_runtime_fn(s, "__mn_tensor_mul_scalar_f64", "ptr", "ptr, double")
s = declare_runtime_fn(s, "__mn_tensor_div_scalar_f64", "ptr", "ptr, double")
s = declare_runtime_fn(s, "__mn_tensor_add_scalar_i64", "ptr", "ptr, i64")
s = declare_runtime_fn(s, "__mn_tensor_sub_scalar_i64", "ptr", "ptr, i64")
s = declare_runtime_fn(s, "__mn_tensor_mul_scalar_i64", "ptr", "ptr, i64")
s = declare_runtime_fn(s, "__mn_tensor_div_scalar_i64", "ptr", "ptr, i64")

// Reverse scalar (scalar - tensor, scalar / tensor — non-commutative)
s = declare_runtime_fn(s, "__mn_tensor_rsub_scalar_f64", "ptr", "ptr, double")
s = declare_runtime_fn(s, "__mn_tensor_rdiv_scalar_f64", "ptr, double", "ptr, double")
s = declare_runtime_fn(s, "__mn_tensor_rsub_scalar_i64", "ptr", "ptr, i64")
s = declare_runtime_fn(s, "__mn_tensor_rdiv_scalar_i64", "ptr", "ptr, i64")
```

Matching `runtime_fn_attrs` rows: `" nounwind"` or
`" nounwind noalias"` per Python's pattern
(`emit_llvm_text.py:357-374`).

Verify all 20 fns actually exist in the C runtime:

```bash
grep -c '^MN_EXPORT mapanare_tensor_t \*__mn_tensor_\(add\|sub\|mul\|div\|rsub\|rdiv\)_\(broadcast\|scalar\)_\(f64\|i64\)' runtime/native/mapanare_gpu_builtins.c
```

If any are missing (likely `rsub_scalar_i64` / `rdiv_scalar_i64`),
add them to the runtime as ~8 LOC each, mirror the f64 twins. The
Python side's fallback may include an emulation path — check before
assuming.

### What does NOT ship

- **Reductions.** `.sum()`, `.mean()`, `.max()`, `.min()`,
  `.argmax()`, `.argmin()` — v5.6.3.
- **Slicing.** `a[1..3]`, `a[_]`, `a[0..2, _]` — v5.6.3.
- **Type promotion between Int and Float tensors.** Same-type only
  for v5.6.2. Python may already mixed-allow; match its actual
  behavior, don't extend.
- **Broadcasting shape-mismatch diagnostics at compile time.**
  Runtime raises; semantic pass doesn't know shapes.
- **GPU-variant dispatch.** `@gpu` annotated binops stay as GPU
  builtins — no impact on v5.6.2.

---

## Exit criteria

1. `mnc-stage1` emits `llvm-as`-clean IR for
   `51_tensor_broadcast.mn`.
2. `lli` output byte-identical to Python bootstrap. Expected
   sequence: `11 44 9 36 10 10 101 104 2 8 11 33`.
3. Harness: 64/66 → **65/66** — `51_tensor_broadcast` FAIL → PASS.
4. Harness: `53_linear_regression` remains structurally emittable
   (its binops compile; the test still FAILs because `.sum()`
   unresolved until v5.6.3).
5. No regression in 49, 50 tensor goldens.
6. stage2.ll `llvm-as` clean; self-hosting preserved.
7. `make lint` clean; `check_struct_registry.py` clean.

---

## Design decisions

### D1 — Route through MIR `Call`, not a dedicated `TensorBinOp` node

Same rationale as v5.6.1: fewer MIR variants, smaller registry. A
dedicated `TensorBinOp` would be cleaner for MIR-level optimization
(e.g., `a * 2.0 * 3.0` → `a * 6.0` constant fold), but v5.6.x isn't
the release for it. v6.0 typed-MIR can unify.

### D2 — Element-type suffix pick

Element kind (Int vs Float) determined from the **tensor** operand's
element type, not the scalar's. `Tensor<Float>[1.0, 2.0] + 5` picks
`f64` suffix and expects the runtime to coerce the Int 5 to double.
Confirm Python behaves identically — if it rejects the mixed-type
case, we reject too.

### D3 — Non-commutative scalar-first: `rsub` / `rdiv`

`5.0 - a` is not the same as `a - 5.0`. The Python recipe uses
`__mn_tensor_rsub_scalar_f64` (`lower.py:2879`). Check runtime —
v4.47.0 notes say these were added post-launch. If missing, add.

### D4 — No implicit shape broadcasting between tensors of different rank

`Tensor<Float>[[1, 2], [3, 4]] + Tensor<Float>[10, 20]` — NumPy would
broadcast the 1D vector across rows. The Python runtime handles
this via `__mn_tensor_add_broadcast_f64`. We inherit the behavior —
no semantic-layer shape check. The runtime raises on shape mismatch
that can't be resolved.

### D5 — Design context: how other languages do binops on tensors

- **NumPy:** operators overloaded, broadcasting follows the
  right-aligned dim-rules. `+` is `__add__`, `*` is `__mul__`. Ubiquitous.
- **Rust ndarray:** operators overloaded via `Add`, `Sub`, `Mul`,
  `Div` traits. Broadcasting is explicit (`.broadcast()`), not
  automatic. Non-broadcasting ops require same shape.
- **Julia:** operators overloaded. Broadcasting with the `.` prefix:
  `a .+ b` explicit. Non-dot `+` requires same shape.
- **Go gonum:** no operator overloading. Must write
  `mat.Add(&c, &a, &b)`. Scalar by function `m.Scale(x)`.
- **Eigen (C++):** operators overloaded; templated at compile time
  for shape info. No runtime broadcasting surprises.
- **TensorFlow / PyTorch:** NumPy-style with implicit broadcasting.

Mapanare picked implicit NumPy-style in v4.44.0. We maintain that
stance — not changing surface, just finishing the self-hosted plumbing.

---

## Risks

- **R1 — Missing `rsub_scalar_i64` / `rdiv_scalar_i64` in runtime.**
  Mitigation: grep before coding. If missing, write 8 LOC each in
  `mapanare_gpu_builtins.c`.
- **R2 — Scalar operand type detection.** `a + 100.0` — the `100.0`
  lowers to a Const of some MIR type. Semantic step must not have
  already coerced it to TENSOR. Mitigation: test with both `a + 2.0`
  (float literal) and `a + two` (let-bound float) to validate.
- **R3 — Ownership / drop-glue.** Tensor binop produces a fresh
  `ptr` that the runtime malloc'd. v5.4.x drop-glue must free it on
  scope exit. Confirm: does `emit_track_*` already cover
  TENSOR-typed locals? If not, add a tracking hook — leaks-only
  (not UAF) — or gate v5.6.2 goldens on a known-leak baseline row
  in `scripts/check_leak_summary.py`.
- **R4 — Self-compilation.** `mnc_all.mn` doesn't use tensor binops,
  so stage2.ll unchanged structurally. Verify via line-count diff.
- **R5 — 51_tensor_broadcast harness claims PASS at function-match
  level today (v5.6.0).** It's emitting broken IR that the harness
  doesn't check structurally — the PASS was function-count parity,
  not correctness. Make sure the v5.6.2 close is true correctness:
  `lli` output diff against Python bootstrap.

---

## What NOT to do

- **Do not add reductions.** `.sum()` is tempting (the runtime fn
  exists); v5.6.3 scope. Keep binop & reduction closure separate —
  cleaner dockets, cleaner fixed-point signals.
- **Do not add slicing.** No `..` range in subscripts. v5.6.3.
- **Do not touch `emit_llvm_text.py`.** Python works.
- **Do not skip the `scalar op tensor` case.** `100.0 + a` must
  work, not just `a + 100.0`. Python does both; test 51 uses both.
- **Do not fold `rsub` / `rdiv` into `add` / `mul` with negation.**
  `0 - x` on a tensor allocates an extra tensor; that's the whole
  point of `rsub`. Stay faithful to Python.
- **Do not declare fns that don't exist in the runtime.** Grep the
  C file before emitting a declaration for something you can't link.
