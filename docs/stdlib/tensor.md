# Tensor (builtin)

`Tensor<T>` is a built-in language type — not a stdlib module —
representing contiguous row-major numeric data. v5.45.0 closes the
shape-manipulation surface: reshape (aliasing), view (aliasing),
stepped slice (copy). After v5.45.0 the "Not yet on LLVM" line in
CLAUDE.md no longer mentions tensor mutable views or stepped slices.

**Backend:** the C runtime in `runtime/native/mapanare_gpu_builtins.c`
exposes `__mn_tensor_*` exports; `mapanare_tensor_t` lives in
`runtime/native/mapanare_runtime.h`. v5.45.0 extends
`mapanare_tensor_t` with append-only refcount + is_view + parent
fields (40 → 64 bytes; pre-v5.45.0 fields preserved at original
offsets).

**v5.45.0 ships:** `t.view(shape)`, `t[start..end:step]`, and a
breaking semantic swap on `t.reshape(shape)` (copy → alias).
Strided / non-contiguous tensors, reverse iteration, and
`.transpose()` / `.permute()` are reserved for v6.0+.

> **Migration note (v5.41.0 → v5.45.0).** `t.reshape(shape)` shipped
> at v5.41.0 with copy semantics: the result was an independent
> tensor, and writes to it did not affect the source. v5.45.0 swaps
> to alias semantics: the result shares the source's data buffer,
> and writes are visible in both. The surface API is unchanged.
> Phase 0 audit confirmed zero production callers relied on copy
> semantics — golden 96 (the v5.41.0 reshape test) does not write
> to either tensor between the reshape and the read, so it stays
> robust to the swap. If your code requires the v5.41.0 copy
> behavior, see "Explicit copy" below.

---

## Quick reference

```mn
// Construction (v4.42.0)
let a: Tensor<Float> = Tensor<Float>[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
let b: Tensor<Float> = Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]
let c: Tensor<Int> = Tensor<Int>[1, 2, 3, 4]

// Inspection (v4.42.0)
let r: Int = tensor_rank(a)           // 1
let n: Int = tensor_size(a)           // 6
let d0: Int = tensor_shape_dim(b, 0)  // 2

// Elementwise read (v4.43.0; flat row-major index)
let x: Float = tensor_get_f64(a, 0)   // 1.0
let y: Int   = tensor_get_i64(c, 3)   // 4

// Multi-axis read + write (v4.43.0)
let v: Float = b[0, 1]                // 2.0
let mut m: Tensor<Float> = b
m[1, 1] = 99.0                        // mutates m

// Reductions (v4.45.0)
let s: Float = a.sum()
let mn: Float = a.min()
let mx: Float = a.max()
let i: Int = a.argmax()

// Slicing (v4.45.0)
let sub: Tensor<Float> = a[0..3]      // first 3 elements (copy)
let row: Tensor<Float> = b[0..1, _]   // wildcard `_` = all
let col: Tensor<Float> = b[_, 1..2]   // column 1

// v5.45.0 — alias-flavor reshape
let r1: Tensor<Float> = a.reshape([2, 3])
r1[0, 0] = 99.0                       // visible in `a`!
print(str(tensor_get_f64(a, 0)))      // 99

// v5.45.0 — explicit alias view
let v1: Tensor<Float> = a.view([2, 3])
v1[1, 2] = 42.0                       // visible in `a`

// v5.45.0 — stepped slice (copy)
let evens: Tensor<Float> = a[0..6:2]  // [a[0], a[2], a[4]]
evens[0] = 999.0                      // does NOT mutate `a`
```

---

## Type and API reference

### Construction

| Form | Description |
|---|---|
| `Tensor<T>[v0, v1, ...]` | 1-D tensor literal |
| `Tensor<T>[[...], [...]]` | N-D nested literal (rank inferred) |

`T` is `Float` (`f64`, default) or `Int` (`i64`).

### Inspection (free functions)

| Function | Returns |
|---|---|
| `tensor_rank(t)` | `Int` |
| `tensor_size(t)` | `Int` (total element count) |
| `tensor_shape_dim(t, d)` | `Int` (size of dimension `d`) |
| `tensor_get_f64(t, idx)` | `Float` |
| `tensor_get_i64(t, idx)` | `Int` |

### Indexing (operator)

| Form | Semantics | Lifetime |
|---|---|---|
| `t[i]` | Single-axis read | n/a (scalar) |
| `t[i, j, ...]` | Multi-axis read | n/a (scalar) |
| `t[i, j] = v` | Multi-axis write | mutates `t` |
| `t[a..b]` | Single-axis slice | **copy** (v4.45.0) |
| `t[a..b, c..d]` | Multi-axis slice | **copy** |
| `t[_]` / `t[_, c..d]` | Wildcard axis (full range) | **copy** |
| `t[a..b:k]` (v5.45.0) | Stepped slice | **copy** |
| `t[a..b:k, c..d:m]` (v5.45.0) | Multi-axis stepped slice | **copy** |

### Methods

| Method | Returns | Lifetime | v |
|---|---|---|---|
| `t.reshape(shape)` | `Tensor<T>` | **alias** | v5.45.0 swap |
| `t.view(shape)` | `Tensor<T>` | **alias** | v5.45.0 |
| `t.sum()` | `T` (or `f64`) | n/a | v4.45.0 |
| `t.min()` | `T` | n/a | v4.45.0 |
| `t.max()` | `T` | n/a | v4.45.0 |
| `t.mean()` | `Float` | n/a | v4.45.0 |
| `t.argmax()` | `Int` | n/a | v4.45.0 |
| `t.argmin()` | `Int` | n/a | v4.45.0 |

### Elementwise arithmetic

`Tensor<T> + Tensor<T>`, `*`, `-`, `/`, scalar broadcast — all
elementwise, all return a fresh tensor (copy).

---

## Lifetime model

`mapanare_tensor_t` carries a refcount, an `is_view` flag, and a
parent pointer:

```c
typedef struct mapanare_tensor {
    void    *data;       /* element buffer                   */
    int64_t  ndim, *shape, size, elem_size;
    int64_t  refcount;   /* 1 on alloc; bumped by views      */
    uint8_t  is_view;    /* 0 = owns data; 1 = view          */
    struct mapanare_tensor *parent;  /* root if view, else NULL */
} mapanare_tensor_t;
```

**Drop-glue rules:**

1. Every fresh tensor (allocated by `Tensor<T>[...]`, reductions,
   elementwise arithmetic, or stepped slice) starts with
   `refcount = 1` and owns its data.
2. `t.view(shape)` and `t.reshape(shape)` create a view: a separate
   tensor metadata that aliases the parent's data buffer.
   The view starts with `refcount = 1`; the parent's refcount is
   incremented by 1.
3. Views are **single-hop**: `view_of_view = leaf.view([...])`
   walks the parent chain and refcounts the **root**, never the
   intermediate. The intermediate view's refcount stays at 1.
4. Dropping a view decrements the view's own refcount; on zero, it
   frees its metadata + shape array (NOT the data) and recurses,
   decrementing the parent's refcount.
5. Dropping an owner decrements its refcount; on zero, frees data +
   shape + metadata.

The refcount layer means a view can outlive its parent's local
scope without the data being freed. The buffer lives until the
last reference (parent or any view) drops.

---

## Cookbook

### 1. Reshape — alias

```mn
fn main():
    let mut original = Tensor<Float>[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    let reshaped = original.reshape([2, 3])
    reshaped[0, 0] = 99.0
    print(str(tensor_get_f64(original, 0)))   // 99 — same data!
```

`.reshape()` returns a view; the new shape's element count must
match the source's (`__mn_tensor_reshape` aborts on mismatch with
"cannot reshape size N to size M"). The source's lifetime is
extended by the view's refcount.

### 2. View — explicit aliasing

```mn
fn main():
    let mut buf = Tensor<Float>[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    let mat = buf.view([2, 3])
    let row = buf.view([6])           // same data, different shape
    mat[1, 2] = 42.0
    print(str(tensor_get_f64(row, 5)))   // 42
```

Use `.view()` when the intent is explicit aliasing; use `.reshape()`
when the intent is "give me this shape, don't care about lifetime."
Both behave identically at v5.45.0 — `.reshape()` delegates to
`__mn_tensor_view` internally. They diverge in v6.0+ if reshape
gains shape-inferring overloads (`reshape([-1, 3])` etc.).

### 3. Stepped slice — sliding window

```mn
fn sliding_window(t: Tensor<Float>, stride: Int) -> Tensor<Float>:
    return t[0..tensor_size(t):stride]

fn main():
    let signal = Tensor<Float>[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    let downsampled = sliding_window(signal, 2)
    // downsampled = [1.0, 3.0, 5.0, 7.0]
    print(str(tensor_size(downsampled)))   // 4
```

Stepped slices are **copies**, not views. The result is a fresh
contiguous tensor independent of the source. Stride 1 is a no-op
(equivalent to `t[a..b]`). Step ≤ 0 is rejected: literal at lower
time, non-literal at runtime.

### 4. Explicit copy — when you need v5.41.0 reshape semantics back

There is no `.copy()` method at v5.45.0 (deferred to v5.47.0+). If
you need an independent copy of a tensor (or a reshape that does
NOT alias), construct one manually:

```mn
fn copy_tensor_f64(src: Tensor<Float>) -> Tensor<Float>:
    let n = tensor_size(src)
    // Allocate a fresh tensor of the same shape and total size.
    // Loop and copy element by element.
    let mut dst = Tensor<Float>[0.0]
    // ... see future v5.47.0+ for a single-call shortcut.
    return dst
```

In practice, an idiomatic-but-verbose pattern is to build a fresh
literal from the source's contents. `tensor_set_f64_nd` (the
runtime-level setter; multi-index `t[i, j] = val` lowers to it) is
the right primitive once the destination is allocated. v5.47.0 will
likely add `t.copy()` and `t.clone()` as ergonomic sugar.

### 5. Refcount mental model

```mn
fn main():
    let mut buf = Tensor<Float>[1.0, 2.0, 3.0, 4.0]   // refcount = 1
    let v = buf.view([2, 2])                          // buf.refcount = 2; v.refcount = 1
    let r = buf.reshape([4])                          // buf.refcount = 3; r.refcount = 1
    // ... use buf, v, r ...
    // At end of scope (in declaration-reverse order):
    //   r drops:  r.refcount = 0 → free r metadata; buf.refcount = 2
    //   v drops:  v.refcount = 0 → free v metadata; buf.refcount = 1
    //   buf drops: buf.refcount = 0 → free buf data + metadata
```

The order in which scopes drop doesn't matter for correctness — a
view dropped before its parent leaves the parent's refcount intact;
a parent dropped before its views leaves the parent's data alive
until the last view drops.

### 6. Drop-glue discipline (what NOT to do)

- **Don't manually free a view's data buffer.** The runtime's
  `__mn_tensor_free` only frees the data when the owner's refcount
  hits zero. You should never see direct `free()` calls on a tensor
  in user code.
- **Don't pass a view across an FFI boundary that takes ownership.**
  An FFI function that wants to claim a tensor's data must be
  passed a fresh-allocated tensor (or a reshape's result, which is
  *technically* a view — there's no current ergonomic way to
  declare "the FFI consumer takes ownership"). Until borrow-check
  arrives in v6.0+, the user is responsible for this discipline.
- **Don't mutate a view while iterating the parent.** Same hazard
  as Python's "modify while iterate" — the runtime won't catch it
  but the read may see torn data.

---

## Aliasing safety

v5.45.0 ships the **runtime substrate** for view aliasing — the
refcount + drop-glue + shape validation. It does NOT ship static
borrow-checking for view aliasing. A view that outlives its parent's
last write and a view that observes a write through another view
are both legal at v5.45.0.

The borrow checker is a v6.0 deliverable. Until it arrives, the
discipline in section 6 above is the user's responsibility.

---

## What's not here yet

- **`.copy()` / `.clone()`** — explicit-independent-copy method.
  Ergonomic sugar over the manual pattern in cookbook section 4.
  v5.47.0+ candidate.
- **Strided / non-contiguous tensors.** Required for general
  `.transpose()` / `.permute()` / negative stepped slices. ABI
  change on `mapanare_tensor_t`. v6.0+ only — significant
  cross-cutting impact (every existing tensor op has to learn
  about strides).
- **Reverse iteration via negative step.** Reserved syntax at the
  language level. v6.0+ alongside strides.
- **GPU `Tensor.view()`.** The stdlib `GpuTensor` type (separate
  from the language-builtin `Tensor`) ships its own `reshape` but
  the surfaces are not unified. v6.0+.
- **Borrow checker on view aliasing.** v6.0.
- **`Tensor<Int>` slice + tensor builtin chaining (e.g.,
  `tensor_size(int_slice_result)`)** triggers a parse error — a
  pre-existing v5.44.1 grammar bug that v5.45.0 surfaced (does not
  affect Float tensors). v5.46.0+ candidate.

See `docs/roadmap/v5/v5.45.0/{PLAN.md, PROMPT.md,
PRE_PHASE_AUDIT.md, SESSION_REPORT.md}` for the full release
notes.
