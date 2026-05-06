# v5.45.0 — Phase 0 audit

**Audit branch:** dev @ f7644b72 (Release v5.44.1)
**HEAD VERSION:** 5.44.1 (PROMPT/PLAN written assuming v5.44.0;
v5.44.1 was a Ps.11+Ps.12 hotfix shipped between PLAN drafting
and execution — line counts, goldens, fixed point identical
because v5.44.1 had zero compiler / runtime / `mapanare/self/*.mn`
edits)
**Goldens at HEAD:** 96/96 GREEN
**STRICT 3-stage fixed point:** preserved at 242,338 lines / 0 diff
**Working tree dirt at audit time:** AGENTS.md + CLAUDE.md
(mechanical gitnexus stat counter bumps + duplicate gitnexus
block deduplication; not v5.45.0 work)

This audit re-runs the v5.41.0 PRE_PHASE_AUDIT protocol against
v5.44.1 HEAD. v5.41.0 caught four PLAN/PROMPT premise errors at
once; v5.45.0 surfaces **five** (most cosmetic; two
load-bearing).

---

## v5.41.0 reshape surface at HEAD

**C runtime:** `runtime/native/mapanare_gpu_builtins.c:819-858`
(`__mn_tensor_reshape`; ~40 LOC; copy semantics; allocates fresh
tensor + memcpy; aborts on size mismatch). Forward-doc'd at
:809-818 with explicit "v5.41.1 introduces refcount-based
aliasing so reshape can share data in O(1) without changing
user-visible semantics" — v5.45.0 closes that contract 4
releases late.

**Python lower:** `mapanare/lower.py:4063-4070`
(`_lower_method_call` TENSOR + "reshape" branch). 8 LOC.

**Python emit handler:** `mapanare/emit_llvm_text.py:3953-3964`
(special-case fn_name == "__mn_tensor_reshape"). Hardcodes
the literal string `call noalias ptr @__mn_tensor_reshape(...)`
at line 3964 — `noalias` is in the printed IR text, not just
in the attribute set.

**Python attribute set:** `mapanare/emit_llvm_text.py:393-396`
(`"__mn_tensor_reshape": {"nounwind", "noalias"}`).

**Self-host lower:** `mapanare/self/lower.mn:2539-2557`
(method == "reshape" branch). 19 LOC.

**Self-host emit handler:** `mapanare/self/emit_llvm.mn:3984-3997`.
Hardcodes `call noalias ptr @__mn_tensor_reshape(...)` at :3997.

**Self-host attribute table:**
- `mapanare/self/emit_llvm.mn:866` — `if name == "__mn_tensor_reshape"
  { return "noalias " }`
- `mapanare/self/emit_llvm.mn:1042` — `if name == "__mn_tensor_reshape"
  { return " nounwind" }`
- `mapanare/self/emit_llvm.mn:1277` — `s = declare_runtime_fn(s,
  "__mn_tensor_reshape", "ptr", "ptr, ptr")`
- `mapanare/self/emit_llvm.mn:4641` — special-case predicate

**Goldens:** `tests/golden/96_tensor_reshape.mn` exercises
`.reshape()` end-to-end. **Golden 96 does NOT actually test the
copy-vs-alias distinction** — see PLAN deviation #1 below.

---

## `mapanare_tensor_t` shape at HEAD

**Definition:** `runtime/native/mapanare_runtime.h:421-428`.

```c
typedef struct mapanare_tensor {
    void    *data;       /* pointer to contiguous element buffer */
    int64_t  ndim;       /* number of dimensions                 */
    int64_t *shape;      /* heap-allocated shape array (ndim)    */
    int64_t  size;       /* total number of elements             */
    int64_t  elem_size;  /* size of each element in bytes        */
} mapanare_tensor_t;
```

5 fields, all 8 bytes on x86_64 Linux, **40 bytes total, 8-byte
aligned**.

**Post-v5.45.0 expected layout** (Ts.2.A append-only):

```c
typedef struct mapanare_tensor {
    void    *data;       /* offset  0 — preserved              */
    int64_t  ndim;       /* offset  8 — preserved              */
    int64_t *shape;      /* offset 16 — preserved              */
    int64_t  size;       /* offset 24 — preserved              */
    int64_t  elem_size;  /* offset 32 — preserved              */
    int64_t  refcount;   /* offset 40 — NEW (Ts.2.A)           */
    uint8_t  is_view;    /* offset 48 — NEW (Ts.2.A)           */
    uint8_t  _pad[7];    /* offset 49..55 — alignment          */
    struct mapanare_tensor *parent; /* offset 56 — NEW         */
} mapanare_tensor_t;
```

**Total post-v5.45.0:** 64 bytes (40 → 64; +24 bytes, not the
PLAN's stated +16). Surface this in CHANGELOG; binary-compat
regression test pins exact size.

### Consumer audit

| Site | File:Line | Pattern | Action at v5.45.0 |
|---|---|---|---|
| `mapanare_tensor_alloc` | `mapanare_runtime.c:1059` | proper field-by-field init | Add `t->refcount = 1; t->is_view = 0; t->parent = NULL;` |
| `mapanare_tensor_free` | `mapanare_runtime.c:1086` | unconditional `free(data); free(shape); free(t)` | Refcount-aware rewrite |
| `tensor_from_list` (helper) | `mapanare_gpu_builtins.c:54-66` | direct `malloc(sizeof(mapanare_tensor_t))`; borrow tensor (data not owned) | Zero-init via `*t = (mapanare_tensor_t){0};` to avoid garbage in new fields |
| `__mn_gpu_tensor_matmul` ta/tb | `mapanare_gpu_builtins.c:229-258` | direct `malloc` + field-by-field; borrow tensor | Same zero-init treatment |
| GPU CUDA / Vulkan ops | `mapanare_gpu.c:471..1957` | all by `const mapanare_tensor_t *`; allocate via `mapanare_tensor_alloc` | No edit needed |
| `tensor_borrow_free` | `mapanare_gpu_builtins.c:69-73` | `free(t->shape); free(t)` directly (data borrowed) | No edit needed — bypasses refcount path; never registered in refcount system |

**Hardcoded offset accesses:** ZERO. All access by field name.
Append-only extension is structurally safe.

**By-value passes:** ZERO. All `mapanare_tensor_t *` or
`const mapanare_tensor_t *`.

**`malloc(sizeof(mapanare_tensor_t))` direct sites:** 4 total
(`mapanare_runtime.c:1062` proper alloc; `mapanare_gpu_builtins.c:56,
229, 230` borrow tensors). All 4 grow automatically with the
struct. Borrow-tensor sites (3) need explicit zero-init of new
fields per v5.45.0.

---

## `.reshape()` callers at HEAD

| Caller | Location | Relies on copy? | Action at v5.45.0 |
|---|---|---|---|
| `tests/golden/96_tensor_reshape.mn` | line 15, 25, 34, 42, 49, 50, 58 | NO — never writes to source after reshape | **No flip needed.** See PLAN deviation #1 |
| `tests/llvm/test_tensor_reshape.py` | inline `.mn` fixture line 186 | NO | No edit |
| `tests/tensor/test_tensor.py` | Python tensor lib (NOT the LLVM-backed builtin Tensor) | N/A | Out of scope — different type |
| `mapanare/self/*.mn` | ZERO callers (matches are comments + handler code) | N/A | N/A |
| `stdlib/*` | ZERO callers | N/A | N/A |
| `examples/*` | ZERO callers | N/A | N/A |

**Conclusion:** zero production-code reliance on the v5.41.0
copy-semantics stopgap. The semantic swap is breaking only in
theory; in practice the only Mapanare-side caller is golden 96
which does not exercise the distinction.

---

## Range / IndexItem / parser surface at HEAD

**Grammar** (`mapanare/mapanare.lark:280-282`):

```lark
?range_expr: add_expr
           | add_expr RANGE add_expr -> range_op
           | add_expr RANGE_INCL add_expr -> range_incl_op
```

`COLON` token already exists at line 537 (`COLON: ":"`). **No new
lexer token needed for `:step`** — re-use `COLON`. PROMPT's
"new lexer token (e.g., RANGE_STEP_SEP)" is unnecessary
complexity.

**AST** (`mapanare/ast_nodes.py`):
- `IndexItem` (line 230-240): `kind: str = "scalar"|"range"|"wildcard"`,
  `expr/start/end: Expr | None`. **No `inclusive` field**
  (pre-existing latent inconsistency: `..=` produces `RangeExpr`
  with `inclusive=True` but IndexItem.kind="range" loses that
  bit; not a v5.45.0 concern but noted).
- `RangeExpr` (line 264-269): `start, end, inclusive: bool`.

**Parser**:
- `range_op` constructor: `mapanare/parser.py:865-869`
- `range_incl_op` constructor: `mapanare/parser.py:871-875`
- `index_expr` translates `RangeExpr → IndexItem(kind="range")`
  at `mapanare/parser.py:933-952`. Adding `step` here is one
  line: `step=c.step`.

**Self-host AST + parser:** mirrors expected at
`mapanare/self/ast.mn` + `mapanare/self/parser.mn`. Verified
parser.mn:2430 has the Tensor-literal handler. Range-step
addition mirror sites to be enumerated in Phase 5.

**Bootstrap grammar** (`bootstrap/mapanare.lark:202-204`):

```lark
?range_expr: add_expr
           | add_expr RANGE add_expr -> range_op
           | add_expr RANGE_INCL add_expr -> range_incl_op
```

Identical shape. **Bootstrap parser DOES load this file at
runtime** (`bootstrap/parser.py:1399-1400` —
`_GRAMMAR_PATH = Path(__file__).parent / "mapanare.lark"; Lark(...)`).
However, the bootstrap is "frozen at v0.6.0" per CLAUDE.md and
nothing in the v5.45.0 build flow parses post-v5.45.0 source
through the bootstrap parser. Updating the bootstrap grammar is
**optional** — see PLAN deviation #2.

---

## Self-host tensor usage

`grep` against `mapanare/self/*.mn` (excluding the
auto-generated `mnc_all.mn`):

- `.reshape(` calls in source code: **ZERO** (only comment
  text in `lower.mn:2539` and `parser.mn` matches
  unrelated text)
- `.view(` calls: **ZERO**
- Stepped slice usage: **ZERO**
- Tensor type instantiation in self-host source: **ZERO**
  outside grammar / lowering / emitter handlers

**Conclusion:** self-host source itself never constructs or
operates on tensors. The reshape-semantic-swap and Ts.3.B
stepped-slice runtime additions cannot affect self-host source
behavior. STRICT preservation is at risk only from the
*self-host mirror edits themselves* (the new view/step/noalias-
drop branches in lower.mn / emit_llvm.mn / parser.mn / ast.mn
add LOC to the self-host source, which feeds into stage2
compiling stage3 — fixed point depends on the new branches
producing identical IR through both passes).

---

## PLAN / PROMPT deviations surfaced

### Deviation 1 — Golden 96 does NOT flip (load-bearing)

**PROMPT claim** (multiple places): "the v5.41.0 source-
unmodified-after-reshape test in golden 96 EXPECTED to flip —
that's the aliasing swap; document explicitly" + "Golden 96
update: the source-unmodified-after-reshape assertion FLIPS.
Update test to assert source IS modified (aliasing); add
`t.copy()` or equivalent for explicit-copy case."

**Reality at HEAD:** Golden 96 lines 56-60:

```mn
// Source tensor unmodified after reshape (copy semantics)
let f = Tensor<Float>[1.0, 2.0, 3.0, 4.0]
let f2 = f.reshape([2, 2])
print(str(tensor_get_f64(f, 0)))
print(str(tensor_get_f64(f2, 0)))
```

This prints `1` and `1`. **There is no write to either tensor
between `reshape` and the reads.** Under copy semantics: both
reads return 1.0 from independent buffers. Under alias
semantics: both reads return 1.0 from a shared buffer. **Same
output either way.** The comment is misleading — the test does
not actually exercise the copy-vs-alias distinction.

**No `t.copy()` API exists at HEAD.** The PROMPT-suggested
"add `.copy()` or equivalent for explicit-copy case" requires a
net-new public API. v5.45.0 PROMPT did NOT scope a `.copy()`
addition.

**Resolution:** golden 96 stays unchanged. The aliasing-visible
assertion lives in NEW golden 99
(`99_tensor_reshape_aliased.mn`) which writes to f2 via
`tensor[i, j] = val` (the existing v4.43.0 surface) and reads
from f. Falsifiability locked: revert the noalias drop +
__mn_tensor_view routing, and golden 99 fails.

`t.copy()` becomes an open question for v5.46.0+. Without it,
users cannot opt back into v5.41.0's copy semantics through a
clean surface — they have to construct a new tensor and copy
elements manually. Document this in the cookbook + CHANGELOG
`### Changed` as a v5.46.0+ candidate.

### Deviation 2 — Bootstrap grammar update is optional

**PROMPT claim:** "Bootstrap copy of grammar in `bootstrap/`
updated in lockstep" (multiple places) + "Bootstrap grammar
copy: yes (Ts.3.A)" in checklist.

**Reality:** `bootstrap/mapanare.lark` is loaded only by
`bootstrap/parser.py` which is frozen at v0.6.0 and not
involved in compiling v5.45.0 sources. The single test that
references it (`tests/bootstrap/test_phase5_self_hosted.py:242`)
just asserts file existence. Updating `bootstrap/mapanare.lark`
to include `range_step_op` is harmless but not load-bearing.

**Resolution:** v5.45.0 ships the grammar update in
`bootstrap/mapanare.lark` for consistency, but does NOT update
`bootstrap/parser.py` constructors. If a future test ever runs
v5.45.0+ source through the bootstrap parser, the bootstrap
parser will fail with a clear "unexpected token COLON in
range_op" error pointing at the missing constructor. Document
in PRE_PHASE_AUDIT for v5.46.0+ bootstrap-modernization release.

### Deviation 3 — Three direct-malloc tensor sites need init

**PROMPT claim:** focuses solely on `mapanare_tensor_alloc` for
refcount initialization.

**Reality:** Three additional direct
`malloc(sizeof(mapanare_tensor_t))` sites exist in
`mapanare_gpu_builtins.c` (lines 56, 229, 230). These create
"borrow tensors" (the data pointer aliases an MnList's buffer,
not heap-allocated). They do field-by-field init and bypass
the alloc helper. Post-v5.45.0 the new fields (refcount,
is_view, parent) would be uninitialized memory — UB if any
later code reads them.

**Resolution:** add explicit zero-init at each site:
`*t = (mapanare_tensor_t){0};` immediately after `malloc`,
then field-by-field set as before. Does not perturb existing
behavior. These borrow tensors are freed via `tensor_borrow_free`
which calls `free(t->shape); free(t)` directly — the refcount
machinery is bypassed (correct: borrow tensor data is owned by
the caller's MnList, not the tensor).

### Deviation 4 — Struct grows by +24 bytes, not +16

**PLAN claim:** "the `mapanare_tensor_t` struct grows by ~16
bytes (refcount + view flag + parent pointer)."

**Reality:** refcount (8) + is_view (1) + 7 padding bytes for
8-byte alignment of parent + parent (8) = **24 bytes**. The
PLAN underestimated by 8 bytes (alignment padding overlooked).

**Resolution:** binary-compat regression test pins exact size
(40 → 64 bytes); CHANGELOG / SPEC sync note the actual delta;
no behavioral consequence.

### Deviation 5 — `IndexItem` has no `inclusive` field (pre-existing latent)

**Reality:** `IndexItem.kind = "range"` does not preserve the
`inclusive: bool` field of the source `RangeExpr`. So
`tensor[a..=b]` lowers identically to `tensor[a..b]` in the
existing IndexItem flow — likely a pre-existing latent bug
from v4.45.0 multi-index support. Not a v5.45.0 introduction.

**Resolution:** out of scope. Note in PRE_PHASE_AUDIT for a
future cleanup release. v5.45.0's `step` addition does not
worsen the situation; both `..` and `..=` will accept `:step`
with the same caveat that `..=` semantics aren't observed by
indexing.

---

## Estimated LOC delta (refined from PLAN's ~150)

| Layer | LOC | Notes |
|---|---|---|
| `mapanare_runtime.h` struct + decls | ~10 | append-only |
| `mapanare_runtime.c` alloc/free rewrite | ~30 | refcount-aware |
| `mapanare_gpu_builtins.c` view + step_slice + reshape route | ~120 | net-new C |
| `mapanare/lower.py` view branch + step branch | ~40 | |
| `mapanare/emit_llvm_text.py` 2 new handlers + noalias drop | ~60 | |
| `mapanare/mapanare.lark` step rule | ~3 | |
| `mapanare/ast_nodes.py` step field | ~4 | |
| `mapanare/parser.py` step constructor | ~10 | |
| `mapanare/self/ast.mn` step field | ~6 | |
| `mapanare/self/parser.mn` step parsing | ~30 | |
| `mapanare/self/lower.mn` view + step + noalias drop | ~80 | |
| `mapanare/self/emit_llvm.mn` 2 new handlers + noalias drop | ~110 | |
| `bootstrap/mapanare.lark` (optional) | ~1 | grammar only; parser.py NOT updated |
| Tests (3 goldens + 2 pytest + 1 binary-compat) | ~600 | |
| Cookbook | ~350 | |
| C smoke harness | ~80 | |
| Docs / CHANGELOG / SESSION_REPORT / SPEC | ~250 | |
| **Total** | **~1,800** | (PLAN budget was 3-5 days) |

---

## Compiler-edit tier: UB-risk

Per `docs/roadmap/v5/PROMPT_TEMPLATE.md`:
- **TSan run** — required (no concurrent scenarios in v5.45.0
  but runtime stays TSan-clean)
- **ASan run** on every Ts.4 view test — required
- **valgrind run** on every Ts.4 view test — required
- **Binary-compat regression test** —
  `tests/runtime/test_tensor_struct_compat.py` net-new

## Self-host edits required

Yes (Ts.7). First release since v5.40.0 to touch
`mapanare/self/*.mn` source files. STRICT preservation
mandatory; rebuild stage1 between each Phase 5 milestone.

## Bootstrap grammar copy

Optional (see Deviation 2). v5.45.0 ships the update for
consistency; not a structural prerequisite.

---

## Aggregate readiness

**Phase 0 GREEN.** No structural blockers surfaced. Five
deviations documented; deviations 1 and 4 are load-bearing for
test design / SPEC accuracy; deviations 2, 3, 5 are
informational / micro-edits.

**Recommendation:** proceed to Phase 1 (Ts.2.A C runtime
refcount surgery).

**Open question for lead before proceeding:** Deviation 1
removes the PROMPT-described `t.copy()` opt-out for the
copy-semantics regime. Without it, users cannot easily
recover v5.41.0 behavior. Two options:
- **(A)** Ship v5.45.0 without `.copy()`; defer to v5.46.0+
  as a small ergonomic addition.
- **(B)** Bundle `.copy()` into v5.45.0 (~30 LOC additional:
  Python lower branch + emit handler + self-host mirror +
  golden + cookbook entry).

Option A keeps v5.45.0 scope honest and tracks the gap as a
LOW carry. Option B closes the regression-recovery story
within the same release. Default to A unless lead picks B.
