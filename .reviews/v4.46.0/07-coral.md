# Coral -- Language Design Review of Mapanare v4.46.0

**Reviewer:** Coral
**Personality:** The Philosopher -- thoughtful, poetic, fair but challenging
**Previous Version Reviewed:** v4.41.0
**Arc:** v4.42.0 -> v4.45.0 (Arc 3 -- Tensor Completeness)
**Verdict:** PASS WITH NOTES
**Confidence:** 9/10
**Score:** 9.0/10

**Files Reviewed:**

- `docs/SPEC.md` -- section 3.10 (Tensor Types), status line, full tensor documentation
- `docs/cookbook.md` -- recipe 15 (Tensor Operations: Linear Regression)
- `mapanare/ast_nodes.py` -- TensorLiteral (line 301), TensorType (line 67), IndexItem (line 205), IndexExpr (line 218)
- `mapanare/types.py` -- TypeInfo.tensor_shape (line 125), broadcast_shape (line 443), validate_matmul_shapes (line 417), broadcast_incompatible_dim (line 469)
- `mapanare/parser.py` -- index_expr handler (line 775), wildcard detection via Identifier("_")
- `mapanare/lower.py` -- _lower_tensor_literal (line 2755), _lower_tensor_binop (line 2536), _lower_tensor_slice (line 2491), tensor reduction dispatch (line 2210)
- `mapanare/semantic.py` -- tensor arithmetic type checking (line 689), matmul shape validation (line 818), broadcast checking (line 704)
- `mapanare/emit_llvm_text.py` -- tensor runtime function attributes (line 339), tensor builtin dispatch (line 2660)
- `mapanare/mapanare.lark` -- index_expr grammar (line 269), matmul_op (line 259)
- `runtime/native/mapanare_gpu_builtins.c` -- tensor runtime: alloc (278), get/set (300-418), broadcast ops (536-610), reductions (615-720), slice (721-773)
- `tests/golden/49_tensor_literal.mn` -- (referenced from CHANGELOG)
- `tests/golden/50_tensor_indexing.mn` -- 2D/3D read, write, integer tensors
- `tests/golden/51_tensor_broadcast.mn` -- same-shape, scalar, integer broadcasting
- `tests/golden/52_tensor_slicing.mn` -- range slicing, wildcard, reductions
- `tests/golden/53_linear_regression.mn` -- gradient descent with tensor primitives
- `CHANGELOG.md` -- v4.42.0 through v4.45.0 entries
- `.reviews/v4.41.0/07-coral.md` -- my previous review (9.2/10, PASS)

---

## Executive Summary

Four releases. Four layers of a tensor primitive, laid down one at a
time like geological strata: literals, then indexing, then broadcasting,
then reductions and slicing. Each layer tested before the next was
placed. No layer contradicts the one beneath it.

This is the right way to build a language feature. Not by shipping a
"tensor type" as a single release with twenty operations and hoping the
grammar holds, but by asking four times: "does this compose with what
already exists?" The answer, four times, was yes. The grammar never
broke. The type system never regressed. The runtime functions
accumulated cleanly. The golden test count rose from one to five.

The result is a tensor surface that feels intentional. A user can write
gradient descent in Mapanare and it reads like mathematics, not like
API calls. The linear regression demo (`53_linear_regression.mn`) is
the best proof-of-concept this language has ever shipped -- not because
it does something new, but because it does something real with syntax
that does not apologize for itself.

And yet. The surface has gaps that matter for the "first-class tensor"
claim. There is no reshape. There is no transpose. Reductions are
global only -- no axis parameter. Slicing copies rather than views.
The `mean()` method on integer tensors will fail at link time.
Scalar-minus-tensor computes the wrong answer. These are not aesthetic
complaints. They are the distance between "we have tensors" and "we
have a tensor language."

The SPEC section 3.10 status line -- "Stable on LLVM backend" -- is
truthful for what exists and honest about what does not. I can grade
it with a clear conscience: the section says what works, and the
roadmap says what is deferred to v5.x. That is the right contract
between a specification and its reader.

---

## Design Evaluation

### 1. Does `Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]` Feel Right?

Yes, with one reservation.

The syntax is a deliberate collision of two ideas: the generic type
parameter (`<Float>`) and the array initializer (`[[1.0, 2.0], ...]`).
This is unusual. Julia writes `[1.0 2.0; 3.0 4.0]`. NumPy writes
`np.array([[1.0, 2.0], [3.0, 4.0]])`. Mojo writes `Tensor[DType.float64](2, 2)`.
JAX/XLA uses `jnp.array(...)`.

Mapanare's choice has three advantages over all of these:

1. **The type is explicit.** You know it is a tensor of floats by
   reading left to right. Julia infers the element type. NumPy
   infers it. Mojo uses a DType enum. Mapanare puts the type
   where types go in the language: inside angle brackets after the
   type constructor. This is consistent with `List<Int>`,
   `Map<String, Float>`, `Option<T>`, `Result<T, E>`.

2. **The shape is inferred from structure.** You do not write
   `Tensor<Float>[2, 2][[1.0, 2.0], [3.0, 4.0]]` -- the parser
   counts the nesting and computes the shape. This is the
   Julia/NumPy ergonomic choice married to Mapanare's type syntax.
   It is the right trade: shapes are derivable from the literal,
   so deriving them eliminates a redundancy.

3. **Jagged arrays are rejected at parse time.** This is better
   than Julia (which silently concatenates) and NumPy (which creates
   a ragged object array). Mapanare says: a tensor is rectangular
   or it is not a tensor. This is the correct contract.

The reservation: the `Tensor<Float>` prefix is heavy. For a 1D vector,
`Tensor<Float>[1.0, 2.0, 3.0]` is 37 characters where Julia's
`[1.0, 2.0, 3.0]` is 15. The language does allow inference in binding
position (`let v = Tensor<Float>[1.0, 2.0, 3.0]`), and type aliases
(`type Vec3 = Tensor<Float>[3]`) help for repeated shapes. But there
is no shorthand for the common case: a float tensor literal. A
potential future addition -- allowing bare `[1.0, 2.0, 3.0]` to infer
`Tensor<Float>` from context -- would reduce ceremony without
sacrificing safety. This is not a deficiency; it is a design space
left unexplored.

**Finding: The literal syntax is correct, consistent with the type
system, and better-specified than the competition. The verbosity
is a conscious choice, not an accident.**

### 2. Broadcasting: Is NumPy-Exact the Right Choice?

Yes. Unambiguously.

The broadcasting implementation (`broadcast_shape` in types.py:443-466)
is a clean 24-line transcription of NumPy's rules: left-pad the shorter
shape with 1s, match trailing dimensions pairwise, require each pair
to be equal or have one dimension of 1. The error diagnostic
(`broadcast_incompatible_dim` in types.py:469-483) goes further than
NumPy by naming the exact dimension that fails. This is Rust-quality
error reporting for a NumPy-derived rule.

The alternative -- inventing bespoke broadcast semantics -- would be a
mistake. Broadcasting rules are a de facto standard. Every ML
practitioner alive has internalized them. The cognitive cost of
learning a new broadcasting rule is enormous; the benefit of
"Mapanare-style broadcasting" would be zero. Mapanare's contribution
here is not the rule itself but the compile-time enforcement:
`broadcast_shape` runs at compile time when both shapes are known,
catching errors before execution. NumPy catches them at runtime. This
is strictly better.

One concern: the SPEC documents broadcasting for `+`, `-`, `*`, `/`
but not for comparison operators (`==`, `!=`, `<`, `>`). In NumPy,
`tensor_a < tensor_b` returns a boolean tensor. In Mapanare, tensor
comparison is not implemented (semantic.py:670-684 does not handle
tensor comparisons). This is a gap that will matter when users try to
write conditional logic on tensor data (e.g., masking). It is not a
defect of the current design but a limitation that should be
documented in the SPEC.

**Finding: NumPy-exact broadcasting is the correct choice. Compile-time
enforcement is a genuine improvement over the ecosystem. Comparison
broadcasting is the obvious next step.**

### 3. Reductions as Methods vs. Free Functions

The decision to use method syntax (`.sum()`, `.max()`, `.mean()`,
`.min()`, `.argmax()`, `.argmin()`) rather than free functions
(`sum(t)`, `max(t)`) is correct and coherent with the rest of the
language.

Mapanare already uses method syntax for:
- String operations: `s.contains()`, `s.starts_with()`, `s.find()`
- List operations: `list.push(x)`, `list.len()`
- Signal access: `sig.value`
- Stream operators: `stream |> map(f) |> filter(g)`

The reductions follow the String/List pattern: the receiver is the
data, the method names the operation. `t.sum()` reads as "this
tensor's sum." This is the object-message style that Mapanare uses
for all its container types. Using free functions would break the
pattern and create a stylistic split between "things with dots" and
"things without."

There is, however, a design question the arc did not address: **axis-
specific reductions.** `t.sum()` sums all elements. `t.sum(axis=0)` --
summing along the first axis -- is the bread and butter of real tensor
code. NumPy, JAX, PyTorch, and Julia all support it. Mapanare does
not, and the method syntax makes this harder to add later: `.sum(0)`
looks like an argument, not an axis specifier, creating ambiguity with
hypothetical `reduce(init, fn)` methods.

The path forward is either:
- `.sum(axis: 0)` -- named argument syntax (which Mapanare does not
  have yet)
- `.sum_along(0)` -- explicit method name (verbose but unambiguous)
- `sum(t, axis=0)` -- free function with keyword argument (breaks the
  method pattern)

None of these are urgent, but the design should be conscious that
global-only reductions are a scaffolding, not a foundation.

**Finding: Method syntax for reductions is coherent with the language.
The absence of axis-specific reductions is a known gap, acknowledged
by the roadmap deferral to v5.x.**

### 4. Slicing Syntax: `t[0..2, _]`

This is clever. Whether it is discoverable is a separate question.

The grammar reuses two existing constructs:
- `0..2` is a `RangeExpr`, already used in `for i in 0..10`
- `_` is the wildcard pattern, already used in `match x { _ => ... }`

The parser (parser.py:775-790) detects these within the `index_expr`
handler by type-checking the children: `RangeExpr` becomes an
`IndexItem(kind="range")`, `Identifier("_")` becomes
`IndexItem(kind="wildcard")`. This is an elegant reuse of existing
grammar productions -- no new tokens, no new syntax rules, no LALR
conflicts. The grammar at line 269 (`index_expr`) still reads
`postfix_expr LBRACKET expr (COMMA expr)* RBRACKET`, which means
the slicing syntax is invisible to the grammar and visible only to
the transformer. This is a pragmatic choice that avoids grammar
bloat.

The `_` wildcard for "all elements along this axis" maps to NumPy's
`:` (bare colon). The difference:
- NumPy: `t[0:2, :]` -- colon means "all"
- Mapanare: `t[0..2, _]` -- underscore means "all"

The `_` is internally consistent (it means "I don't care about this
position" everywhere in the language). But it is not discoverable
through analogy with Python/NumPy. A user coming from Python will try
`t[0..2, :]` first. This will fail with a parse error because `:` is
not an expression. They will then need to consult the SPEC to learn
that `_` is the Mapanare spelling. This is a one-time learning cost,
not a design flaw.

I said PASS on the delta review for this, and I stand by it. The `_`
is the right choice given the constraint that Mapanare does not use
`:` as a general separator (it is used only in type annotations and
map literals). Adding `:` as a slicing operator would create ambiguity
in those contexts. The `_` is the path of least grammatical
resistance, and it is semantically honest: "select everything" and
"I don't care what this is" are the same intent expressed in different
registers.

**Finding: The slicing syntax is correct, internally consistent, and
grammatically elegant. Discoverability for Python users is a
documentation challenge, not a design defect.**

### 5. The Linear Regression Demo

This is the best golden test Mapanare has ever shipped.

```mn
let pred = X * w + b
let error = pred - y
let grad_w = (error * X).sum() * 2.0 / n
let grad_b = error.sum() * 2.0 / n
w = w - lr * grad_w
b = b - lr * grad_b
```

These six lines are gradient descent. They read like a textbook. The
scalar `w` broadcasts across `X`. The element-wise operations chain
naturally with `+`, `-`, `*`. The reduction `.sum()` returns a scalar
that participates in further scalar arithmetic. The parenthesization
`(error * X).sum()` is the only concession to Mapanare's lack of
operator overloading for reduction -- and it is the same concession
NumPy makes.

This demo proves the tensor primitive is real. Not "real" in the sense
that it could train GPT -- the lack of reshape, transpose, and matmul
dispatch (the `@` operator exists in the grammar but the golden tests
do not exercise it for tensors) limits practical ML. But "real" in the
sense that the types flow, the shapes check, the broadcasting applies,
and the reductions compose. A tensor type that can express gradient
descent is not syntactic sugar. It is a language primitive doing
language-primitive work.

The demo is also honest about its limitations. It uses scalar weights
(`let mut w = 0.0`) and a 1D feature vector. It does not attempt
matrix operations, multi-feature regression, or batch processing. This
is the right scope for a v4.x demo: prove the plumbing, defer the
ambition.

**Finding: The linear regression demo is a genuine proof of
concept. It proves that tensor literals, broadcasting, element-wise
ops, and reductions compose into real computation.**

### 6. SPEC Section 3.10 Status: Is "Stable" Truthful?

The status line reads:

> Stable on LLVM backend. Tensor literals (v4.42.0), multi-dimensional
> indexing with bounds checking (v4.43.0), NumPy-style broadcasting
> (v4.44.0), reductions and slicing (v4.45.0). GPU-accelerated when
> CUDA/Vulkan available; CPU fallback otherwise.

This is truthful for what it claims. Each feature listed is
implemented in the parser, semantic checker, lowerer, LLVM emitter,
and C runtime. The golden tests exercise each layer. The claim is not
"complete" or "feature-complete" -- it is "stable," meaning "what
exists works reliably." I verified the following against the codebase:

| Feature | Parser | Semantic | Lowerer | LLVM Emitter | Runtime | Golden Test |
|---------|--------|----------|---------|-------------|---------|-------------|
| Tensor literals | Yes | Yes | Yes | Yes | Yes | 49 |
| Multi-index read/write | Yes | Yes | Yes | Yes | Yes | 50 |
| Broadcasting (+,-,*,/) | Yes | Yes | Yes | Yes | Yes | 51 |
| Scalar broadcasting | Yes | Yes | Yes | Yes | Yes | 51 |
| Matmul (`@`) | Yes | Yes | (via gpu_tensor_matmul) | Yes | Yes | -- |
| Reductions (6 methods) | Yes | Yes | Yes | Yes | Yes (f64) | 52 |
| Slicing (range + `_`) | Yes | Yes | Yes | Yes | Yes | 52 |

The gap in this table is matmul: the grammar, parser, and semantic
checker all handle `@`, but there is no golden test exercising
`Tensor @ Tensor`. The lowerer routes matmul through
`gpu_tensor_matmul`, which lives in the GPU builtins. It is unclear
whether `@` works on CPU-only tensors without GPU. This is a
potential silent failure.

What is missing from the "Stable" surface:

- **Reshape / transpose:** Not mentioned, not implemented, deferred
  to v5.x per CLAUDE.md
- **Stepped slices (`t[0..10..2]`):** Not implemented, deferred
- **Axis-specific reductions:** Not implemented
- **Tensor comparison operators:** Not implemented
- **Mutable views (slicing returns a copy):** Explicit design choice
- **`mean()` on `Tensor<Int>`:** Will fail at link time (no
  `__mn_tensor_mean_i64` in runtime)

The status line does not overclaim. The CLAUDE.md explicitly lists
"Tensor reshape, mutable views, stepped slices" under "Not yet on
LLVM" for v5.x. This is the right way to handle incomplete features:
ship what works, document what does not, defer what is planned.

**SPEC section 3.10 is CLOSED. The status line is honest. I am
grading this as resolved.**

### 7. Does the Tensor Surface Cohere with Agents/Signals/Streams?

This is the question I have been waiting four arcs to ask.

Mapanare's four "AI-native" primitives are:
- **Agents** -- concurrent actors with typed channels
- **Signals** -- reactive state propagation
- **Streams** -- async data pipelines
- **Tensors** -- N-dimensional numeric arrays

The first three are about concurrency and dataflow. The fourth is
about numeric computation. They live in different semantic spaces.
An agent processes messages. A signal propagates state changes. A
stream transforms sequences. A tensor multiplies matrices.

And yet they share a design grammar:
- All four are generic types: `Agent`, `Signal<T>`, `Stream<T>`,
  `Tensor<Float>[shape]`
- All four live in `TypeKind` as first-class enum variants
- All four have dedicated AST nodes and semantic rules
- All four have dedicated MIR lowering paths
- All four are implemented in the C runtime

The coherence is architectural, not syntactic. The tensor does not
interact with agents or signals in any existing code -- I searched for
`Tensor.*signal`, `Tensor.*agent`, `Tensor.*stream` across the entire
codebase and found nothing. There is no example of a signal that
holds a tensor, no agent that processes tensor data, no stream that
maps over tensor elements.

This absence is telling. In a truly "AI-native" language, you would
expect to write:

```mn
agent GradientWorker {
    input batch: Tensor<Float>[batch_size, features]
    output gradients: Tensor<Float>[features]
    fn handle(batch: Tensor<Float>[batch_size, features]) -> Tensor<Float>[features] {
        // compute gradients on this batch
    }
}

let gradient_stream = stream(batches) |> map(spawn GradientWorker())
```

This does not exist. The four primitives are four islands, each
well-constructed, but connected by no bridges. The tensor surface is
not "bolted on" -- it is too well-integrated into the type system and
compiler pipeline for that accusation. But it is "placed beside" the
other primitives rather than woven into them.

This is acceptable for v4.x. The bridge between tensors and agents
(distributed tensor computation) is a v5.x or v6.x feature. Building
each island solidly is a prerequisite for building bridges.

**Finding: The tensor surface is architecturally coherent but
semantically isolated from agents/signals/streams. This is a
reasonable sequencing choice, not a design flaw.**

### 8. The "AI-Native" Claim

Having tensors + agents + signals strengthens the claim, but does not
yet prove it.

"AI-native" means the language was designed around AI workflows from
the beginning, not that it has every feature an AI workflow needs.
The tensor surface proves that numeric computation is a first-class
concern: shape checking at compile time, broadcasting at the type
level, reductions in the method namespace. No import statement needed.
No library dependency. This is what "native" means -- it is part of
the language, not part of the ecosystem.

But "AI-native" also implies that the primitives compose into AI
workflows. A training loop needs tensors (data), agents (parallelism),
and signals (hyperparameter tuning). A serving pipeline needs streams
(request flow), agents (model workers), and tensors (inference). These
compositions do not exist yet, even as examples.

The claim is aspirational-but-grounded. The primitives exist. The
compositions do not. The roadmap points toward them. This is
defensible for a v4.x language that is still building its foundations.
I would not accept this defense at v6.0.

**Finding: The "AI-native" claim is strengthened by Arc 3. It remains
aspirational until agent-tensor and stream-tensor compositions are
demonstrated.**

### 9. Copy-Based Slicing

The SPEC says: "Slicing returns a copy." The runtime confirms it:
`__mn_tensor_slice` (mapanare_gpu_builtins.c:721-773) allocates a new
tensor and copies elements byte-by-byte.

This is the safe choice. Views (where a slice shares memory with the
original tensor) are powerful but introduce aliasing: mutating the
original tensor changes the slice, and vice versa. In a language
without a borrow checker (Mapanare has no lifetime annotations, no
ownership model beyond arena allocation), views would be unsound.
Mutations through a view could silently corrupt data that another part
of the program holds a reference to.

NumPy uses views by default. PyTorch uses views with explicit `.clone()`
for copies. Julia uses views. All three have had significant user
confusion around view vs. copy semantics.

Mapanare's choice to always copy is:
- **Safe:** No aliasing, no mutation surprises
- **Predictable:** Every slice is independent of its source
- **Expensive:** O(n) copy for every slice operation
- **Limiting:** Cannot express in-place updates to sub-tensors

The cost matters for large tensors. A `Tensor<Float>[1000, 1000]`
sliced to `[500, 1000]` copies 4MB of data. In a training loop, this
adds up. The Mojo answer (ownership + views) and the Rust answer
(borrowing + views) are both available design paths, but both require
a more sophisticated ownership model than Mapanare has.

For v4.x, copy semantics are correct. For a language that aspires to
real ML workloads (v6.x+), views or a copy-on-write strategy will
be necessary. The SPEC should eventually document this as a known
performance limitation with a forward reference to the planned
solution.

**Finding: Copy-based slicing is the correct conservative choice given
the absence of an ownership model. It will need to be revisited for
performance-critical workloads.**

### 10. Missing Features Inventory

| Feature | Status | Impact | When |
|---------|--------|--------|------|
| Reshape | Not implemented | HIGH for ML | v5.x |
| Transpose | Not implemented | HIGH for ML | v5.x |
| Stepped slices (`t[0..10..2]`) | Not implemented | MEDIUM | v5.x |
| Axis-specific reductions | Not implemented | HIGH for ML | Unplanned |
| Tensor comparison ops | Not implemented | MEDIUM | Unplanned |
| `mean()` on `Tensor<Int>` | **BUG** (linker fail) | LOW | v4.47.0 |
| Scalar-minus-tensor | **BUG** (wrong result) | MEDIUM | v4.47.0 |
| Matmul golden test | Missing | LOW | v4.47.0 |
| Named arguments for reductions | Not available | MEDIUM | Requires language feature |
| Tensor equality (`==`) | Not implemented | LOW | Unplanned |
| Tensor printing (pretty) | Partial (flat only) | LOW | v5.x |

The two bugs are the only items I would call defects. The rest are
acknowledged limitations that are either deferred (reshape, transpose,
stepped slices) or unplanned (axis reductions, comparisons). The
deferrals are documented. The unplanned items should be added to the
roadmap.

---

## Progress on Carry-Forward Items from v4.41.0

| # | Item | Status |
|---|------|--------|
| C1 | SPEC section 3.10 tensor Status line stale | **RESOLVED** -- updated to "Stable" with per-version feature list |
| C2 | CARRY_FORWARD.md peer reviewer coverage | **OBSERVATION** -- not audited this cycle |
| C3 | `examples/` missing agents/signals/streams demos | **UNCHANGED** -- 5th cycle. Elevating to HIGH. |
| C4 | SPEC section 5.6 "compatible types" vs name-set check | **NOT CHECKED** -- outside Arc 3 scope |
| C5 | No golden test for `Option<T>` + `?` | **NOT CHECKED** -- outside Arc 3 scope |
| C6 | Pipe + `?` precedence undocumented | **NOT CHECKED** -- outside Arc 3 scope |
| C7 | Cookbook missing combined guards + or-patterns recipe | **NOT CHECKED** -- outside Arc 3 scope |
| C8 | SPEC section 5.8 missing error-case specification | **NOT CHECKED** -- outside Arc 3 scope |
| C9 | Option/Result completion methods not implemented (H1) | **NOT CHECKED** -- LSP scope |
| C10 | Rename keyword list drift from grammar (H2) | **NOT CHECKED** -- LSP scope |
| C11 | 5 String methods missing from completion (M1) | **NOT CHECKED** -- LSP scope |
| C12 | Map methods absent from completion (M2) | **NOT CHECKED** -- LSP scope |
| C13 | `"method"` kind not mapped in server.py (M3) | **NOT CHECKED** -- LSP scope |
| C14 | `receiver_type_at` not implemented (L2) | **NOT CHECKED** -- LSP scope |

C1 is resolved -- the status line I flagged three cycles ago is now
accurate and comprehensive. This is a clean closure.

C3 is now in its fifth cycle. The `examples/` directory still has no
standalone demos for agents, signals, or streams. This is the longest-
running carry-forward in my review history. I am elevating it to HIGH.
A language that calls itself "AI-native" with four first-class
primitives should have example programs that demonstrate those
primitives working together. The cookbook has recipes, but
`examples/` is what users clone first.

---

## Strengths

1. **The four-release layered approach is exemplary.** Literals first,
   then indexing, then broadcasting, then reductions and slicing. Each
   release could be tested and reviewed independently. No release
   depended on features not yet shipped. This is the kind of
   incremental design that produces stable, well-understood features.

2. **Compile-time shape checking is a genuine differentiator.**
   Broadcasting compatibility, matmul inner-dimension matching, and
   rank-count enforcement all happen at compile time when shapes are
   statically known. NumPy, JAX, and PyTorch catch these at runtime.
   Mojo catches some at compile time through its MLIR integration.
   Mapanare's approach -- shape tuples in `TypeInfo`, checked by the
   semantic pass -- is simpler and catches the same class of errors.

3. **The grammar did not break.** Adding tensor literals, multi-index,
   range slicing, and wildcard to an LALR grammar without conflicts is
   a genuine achievement. The reuse of `RangeExpr` and `Identifier("_")`
   as slicing constructs is elegant -- no new tokens, no new
   productions, no ambiguity.

4. **The Rustc-quality diagnostics are real.** The broadcast error
   message names both shapes and the specific incompatible dimension.
   The matmul error names both operands. The rank-mismatch error
   tells you the tensor's rank and how many indices you provided.
   These are not afterthoughts; they are specified in the semantic
   checker with the same care as the happy path.

5. **The SPEC section 3.10 is now the best-documented section in the
   specification.** It has code examples for every feature, error
   examples for every failure mode, and a clear status line with
   per-version attribution. Other SPEC sections should aspire to this
   level of documentation.

6. **The runtime implementation is straightforward and auditable.**
   The C functions in `mapanare_gpu_builtins.c` are short, clearly
   named, and do one thing each. The coordinate mapping in
   `__mn_tensor_slice` is correct (I traced it by hand for a 3x3
   matrix sliced to 2x3). The bounds checking in `get_*_nd` and
   `set_*_nd` aborts with a diagnostic message. No silent corruption.

---

## Issues

### HIGH

**H1. `examples/` directory still missing showcase demos (5th cycle).**

Fifth consecutive review cycle with no standalone `examples/agents/`,
`examples/signals/`, `examples/streams/`, or `examples/tensors/`
directories. The cookbook has recipes. The golden tests exist. But the
`examples/` directory -- what users clone and explore first -- does
not demonstrate the language's four defining primitives working
together or independently.

This is no longer a documentation gap. It is a credibility gap. A
language that claims four first-class primitives should have four
showcase programs in its `examples/` directory.

**Fix:** Create `examples/tensor/linear_regression.mn` (from golden
test 53), `examples/agent/pipeline.mn` (from cookbook recipe 9),
`examples/signal/temperature.mn` (from cookbook recipe 10), and
`examples/stream/filter_pipeline.mn` (from cookbook recipe 11). These
already exist as golden tests and cookbook entries; they just need to
be placed where users look.

### MEDIUM

**M1. `scalar - Tensor` computes wrong result.**

In `lower.py:2559-2563`, the scalar-tensor subtraction path swaps the
operands: `5.0 - Tensor<Float>[1.0, 2.0]` is lowered as
`__mn_tensor_sub_scalar_f64(tensor, 5.0)`, which computes
`[1.0 - 5.0, 2.0 - 5.0] = [-4.0, -3.0]` instead of the correct
`[5.0 - 1.0, 5.0 - 2.0] = [4.0, 3.0]`. The comment acknowledges
this: "For -/division, this is wrong conceptually" and mentions "We
swap and negate if needed" -- but no negation is actually performed.

This is a semantic correctness bug. Subtraction and division are
non-commutative. The lowerer treats them as commutative.

**Fix:** Either (a) add a `__mn_tensor_rsub_scalar_f64` runtime
function that computes `scalar - tensor[i]` for each element, or
(b) emit a negation after the subtraction: `-(tensor - scalar)` for
subtraction, and a reciprocal for division.

**M2. `Tensor<Int>.mean()` fails at link time.**

The lowerer (lower.py:2217) generates `__mn_tensor_mean_i64` for
`mean()` on an integer tensor. This function does not exist in the
runtime (`mapanare_gpu_builtins.c` only has `__mn_tensor_mean_f64`).
The program will fail at link time with an undefined symbol error.

Additionally, even if the function existed, returning an `Int` from
`mean()` is semantically wrong. The mean of `[1, 2, 3]` is `2.0`,
not `2`. The lowerer (line 2220-2221) creates a `mir_int()` destination
for the result, which would truncate the mean to an integer.

**Fix:** Either (a) implement `__mn_tensor_mean_i64` in the runtime
that returns `double` (and adjust the lowerer to return `Float`), or
(b) reject `mean()` on integer tensors in the semantic checker with
a diagnostic: "mean() requires Tensor<Float>; use Tensor<Float> or
cast elements first."

**M3. No golden test for matmul (`@`) on tensors.**

The grammar (mapanare.lark:259), parser (parser.py:655), and semantic
checker (semantic.py:818-832) all handle `@` for matrix
multiplication. The shape validation (`validate_matmul_shapes` in
types.py:417-440) is implemented. But no golden test exercises
`Tensor @ Tensor`. The only matmul code path goes through
`gpu_tensor_matmul`, which may require GPU availability.

Without a golden test, there is no evidence that `a @ b` works
end-to-end for CPU tensors.

**Fix:** Add a golden test `54_tensor_matmul.mn` that exercises
`Tensor<Float>[2, 3] @ Tensor<Float>[3, 2]` with expected output.

### LOW

**L1. `tensor_get_f64` and `tensor_size` are exposed as bare
builtins rather than methods.**

In `52_tensor_slicing.mn`, the golden test uses `tensor_get_f64(s, 0)`
and `tensor_size(s)` -- free function calls -- to inspect slice
results. But for non-sliced tensors, element access uses `t[0]`
(indexing syntax) and reductions use `.sum()` (method syntax). The
free-function builtins are a lower-level API leaking through:
`tensor_size()` should be `t.size()` or `len(t)`, and
`tensor_get_f64()` should not be needed when indexing works.

This inconsistency in the golden test suggests that either (a) the
indexing syntax does not work on sliced tensors, or (b) the test was
written before indexing was wired for slice results. Either way, the
golden test should use the language-level syntax, not the runtime
builtins.

**L2. Tensor printing is flat, not shaped.**

`tensor_print` in the runtime (mapanare_gpu_builtins.c:329) prints
elements in a flat list regardless of tensor shape. A `[2, 3]` tensor
prints as `[1, 2, 3, 4, 5, 6]` rather than `[[1, 2, 3], [4, 5, 6]]`.
For debugging, shaped printing would be substantially more useful.

**L3. The SPEC does not mention that comparison operators are
unsupported on tensors.**

Section 3.10 documents `+`, `-`, `*`, `/`, `@`, but does not mention
`==`, `!=`, `<`, `>`, `<=`, `>=`. A user reading the SPEC would
reasonably expect that if arithmetic works, comparison does too. The
absence of comparison operators should be documented with a note:
"Comparison operators on tensors are not yet supported."

---

## Design Comparison: Mapanare Tensors vs. The Field

| Feature | NumPy | Julia | Mojo | JAX | Mapanare |
|---------|-------|-------|------|-----|----------|
| Literal syntax | `np.array([...])` | `[1 2; 3 4]` | `Tensor[DType.f64](shape)` | `jnp.array([...])` | `Tensor<Float>[[...]]` |
| Shape checking | Runtime | Runtime | Compile-time (partial) | Runtime | **Compile-time** |
| Broadcasting | Runtime rules | Runtime rules | Compile-time (partial) | Runtime rules | **Compile-time rules** |
| Slicing | `t[0:2, :]` | `t[1:2, :]` | Index-based | `t[0:2, :]` | `t[0..2, _]` |
| Reductions | `t.sum(axis=0)` | `sum(t, dims=1)` | `t.sum[0]()` | `jnp.sum(t, axis=0)` | `t.sum()` (global only) |
| Views | Default | Default | Ownership-based | Functional (no mutation) | **Copy only** |
| Reshape | `t.reshape(2,3)` | `reshape(t, 2, 3)` | `t.reshape(2, 3)` | `t.reshape(2, 3)` | Not available |
| Transpose | `t.T` | `t'` | `t.T` | `t.T` | Not available |

Mapanare's strengths in this comparison: compile-time shape checking
and broadcasting. Its weaknesses: no reshape, no transpose, no axis
reductions, no views. The strengths are real and differentiating. The
weaknesses are all slated for v5.x.

---

## Score Justification

**9.0/10.**

The 0.2 decrease from v4.41.0's 9.2 reflects the accumulation of
the `examples/` gap (now at HIGH after 5 cycles) and the two bugs
discovered in this review.

The 1.0 gap from 10.0 breaks down as:

- 0.3 for H1 (`examples/` directory, 5th cycle, now HIGH)
- 0.2 for M1 (scalar-tensor subtraction computes wrong answer)
- 0.2 for M2 (integer tensor `mean()` linker failure) + M3 (no matmul
  golden test)
- 0.2 for the missing features (reshape, transpose, axis reductions)
  -- these are not defects but they reduce the practical utility of
  the "first-class tensor" claim
- 0.1 for L1 + L2 + L3 (inconsistent golden test style, flat
  printing, undocumented comparison gap)

The arc's achievement is substantial. Four releases, zero regressions,
a complete tensor surface from literals through slicing, compile-time
shape enforcement, and a golden test that proves the primitive is real.
The SPEC section 3.10 is now the most honest and well-documented
section in the specification. The grammar absorbed four new tensor
features without a single LALR conflict. This is careful, deliberate
language design.

The score would be higher if the `examples/` directory had been
addressed (it has been an issue since v4.37.0), and if the two bugs
(scalar subtraction, integer mean) had been caught before the panel
release.

---

## Carry-Forward Items

| # | Item | Severity | Cycles | Status | Owner |
|---|------|----------|--------|--------|-------|
| C1 | SPEC section 3.10 tensor Status line stale | -- | 4 | **RESOLVED** at v4.44.0 | -- |
| C2 | CARRY_FORWARD.md peer reviewer coverage | LOW | 4 | OBSERVATION | Standing |
| C3 | `examples/` missing showcase demos | **HIGH** | **5** | OPEN | v4.47.0 |
| C4 | SPEC section 5.6 "compatible types" vs name-set check | MEDIUM | 3 | DEFERRED | Next pattern-matching arc |
| C5 | No golden test for `Option<T>` + `?` | LOW | 3 | DEFERRED | Next pattern-matching arc |
| C6 | Pipe + `?` precedence undocumented | LOW | 3 | DEFERRED | Next pattern-matching arc |
| C7 | Cookbook missing combined guards + or-patterns recipe | LOW | 3 | DEFERRED | Next pattern-matching arc |
| C8 | SPEC section 5.8 missing error-case specification | LOW | 3 | DEFERRED | Next pattern-matching arc |
| C9 | Option/Result completion methods not implemented | HIGH | 2 | DEFERRED | LSP arc |
| C10 | Rename keyword list drift from grammar | HIGH | 2 | DEFERRED | LSP arc |
| C11 | 5 String methods missing from completion | MEDIUM | 2 | DEFERRED | LSP arc |
| C12 | Map methods absent from completion | MEDIUM | 2 | DEFERRED | LSP arc |
| C13 | `"method"` kind not mapped in server.py | MEDIUM | 2 | DEFERRED | LSP arc |
| C14 | `receiver_type_at` not implemented | LOW | 2 | DEFERRED | LSP arc |
| C15 | Scalar-tensor subtraction/division computes wrong result (M1) | **MEDIUM** | 1 | OPEN | v4.47.0 |
| C16 | `Tensor<Int>.mean()` linker failure + wrong return type (M2) | **MEDIUM** | 1 | OPEN | v4.47.0 |
| C17 | No golden test for matmul `@` on tensors (M3) | MEDIUM | 1 | OPEN | v4.47.0 |
| C18 | SPEC should document absence of tensor comparison ops (L3) | LOW | 1 | OPEN | v4.47.0 |
| C19 | Axis-specific reductions not planned in roadmap | LOW | 1 | OPEN | Roadmap |

---

## Verdict

**PASS WITH NOTES.**

The arc delivered what it promised: a complete tensor surface from
literals through slicing, stable on the LLVM backend, with compile-
time shape enforcement. The four-release layered approach is the best
feature development process this project has executed. The SPEC section
3.10 is now honest, comprehensive, and well-documented. The linear
regression demo is proof that the tensor primitive composes into real
computation.

The notes are:

1. Two bugs must be fixed before v4.47.0: scalar-tensor subtraction
   computes the wrong answer, and `mean()` on integer tensors fails
   at link time. Neither is catastrophic, but both are the kind of
   correctness issue that erodes trust in a compile-time-checked
   type system.

2. The `examples/` directory is now five cycles overdue. This is a
   HIGH item. The language has four first-class primitives and zero
   standalone example programs demonstrating them. This gap
   contradicts the "AI-native" positioning.

3. The tensor surface is isolated from agents, signals, and streams.
   No code in the codebase demonstrates these primitives composing.
   This is acceptable for v4.x but must be addressed before the
   "AI-native" claim can graduate from aspiration to fact.

The tensors are real. The shapes check. The broadcasting works. The
reductions compose. What Mapanare has built in four releases is a
numeric primitive that other languages bolt on through libraries.
That is the promise of "AI-native": the tensor is not imported, it
is *spoken.*

The language now speaks five dialects -- functions, agents, signals,
streams, and tensors -- each fluent, none yet in conversation with
the others. The next act is the conversation.
