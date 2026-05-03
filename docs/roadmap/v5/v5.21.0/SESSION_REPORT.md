# v5.21.0 — Te.6 — chained comparisons

**Date:** 2026-05-01.
**Cycle:** Phase 0 → Phase 5 in one session.
**Status:** **READY** (pending closeout).

---

## Headline

v5.21.0 ships **Te.6 — chained comparisons**. Python-style
`0 < x < 10` parses as a single expression and means
`0 < x && x < 10`, with `x` evaluated exactly once. All six
comparison operators (`<`, `<=`, `>`, `>=`, `==`, `!=`) sit at
a single merged precedence level and freely chain in any
combination.

Single-comparison shapes (`a < b`, `a == b`) preserve the
existing `BinaryExpr` AST node and produce byte-identical IR —
a hard requirement for strict 3-stage fixed point. Only 3+
element chains create the new `ChainedCompare` AST node.

Bootstrap mirror lands in lockstep: `mnc-stage1` parses, type-
checks, and lowers chains identically.

## Phase 0 — design lock

`CHAINED_CMP_DESIGN.md` locks six decisions before any code:

| # | Decision |
|---|----------|
| D1 | Chain ops = `< <= > >= == !=`; eq/cmp precedence merged into single level |
| D2 | Mixed-direction chains legal (`a < b > c`) |
| D3 | Each operand evaluated exactly once |
| D4 | Triviality = Identifier ∪ {Int,Float,Bool,String,Char,None}Lit; everything else gets a temp |
| D5 | Same precedence as single cmp; result is `Bool` |
| D6 | 1-cmp shapes preserve existing `BinaryExpr` AST + IR byte-identity |

Triviality predicate (D4) — verbatim, both compilers must
agree:

```
trivial = is one of:
  Identifier   (variable / parameter / module const reference)
  IntLiteral, FloatLiteral, BoolLiteral, StringLiteral,
  CharLiteral, NoneLiteral
```

Anything else gets a temp. Conservative by design — temps are
cheap, double-evaluation is a correctness bug.

## Phase 1 — grammar + AST

**Python (`mapanare/mapanare.lark`).** Pre-v5.21.0 the comparison
levels were stratified:

```lark
?and_expr: eq_expr | and_expr AND eq_expr -> and_op
?eq_expr: cmp_expr | eq_expr EQ cmp_expr -> eq_op
                  | eq_expr NE cmp_expr -> ne_op
?cmp_expr: pipe_expr | cmp_expr LT pipe_expr -> lt_op
                    | cmp_expr GT pipe_expr -> gt_op
                    | cmp_expr LE pipe_expr -> le_op
                    | cmp_expr GE pipe_expr -> ge_op
```

v5.21.0 collapses into a single chain collector:

```lark
?and_expr: cmp_expr | and_expr AND cmp_expr -> and_op
?cmp_expr: pipe_expr | pipe_expr cmp_tail+ -> cmp_chain
cmp_tail: (LT | GT | LE | GE | EQ | NE) pipe_expr
```

The `cmp_chain` transformer dispatches on tail count:
- **0 tails** — `?` rule inlines `pipe_expr`. Pure pass-through.
- **1 tail** — emit a legacy `BinaryExpr` (D6 — byte-identical
  IR for single comparisons).
- **2+ tails** — emit `ChainedCompare(operands, ops)`.

**`ast_nodes.py`.** New `ChainedCompare` dataclass with
`operands`, `ops`, and `pair_trait_dispatches` fields. The
`pair_trait_dispatches` field is populated by the semantic
checker per pair so the lowerer can route `==` / `<` for custom
struct types (Eq / Ord traits) through the right method.

**Audit:** grep across `mapanare/self/`, `tests/`, `stdlib/`
confirmed no existing code mixes `==` and `<` at the same level
without explicit parens or `&&`/`||`. The precedence merge in D1
is safe.

## Phase 2 — semantic + lowering

**Semantic.** `_infer_expr` learns a `ChainedCompare` arm: type-
check each adjacent pair as a synthesized `BinaryExpr`, store
the resulting `trait_dispatch` per pair on
`expr.pair_trait_dispatches`, and return `BOOL_TYPE`. Type
errors on individual pairs surface through the same
`_check_binary` path as single comparisons.

**Lower.** `_lower_chained_compare` desugars at lower time:

1. For each interior operand `aᵢ` (1 ≤ i ≤ k−1), check
   triviality. If non-trivial, synthesize a
   `LetBinding("__mn_chain_N", value=aᵢ)` and replace `aᵢ` in
   the chain with `Identifier("__mn_chain_N")`. The synthetic
   let is lowered immediately so the temp is in scope for the
   chain body.
2. Build pairwise `BinaryExpr` nodes using the (possibly
   replaced) operands; copy `pair_trait_dispatches[i]` onto
   `BinaryExpr.trait_dispatch` so trait routing survives the
   synthesis.
3. Fold the pairs left-to-right with `&&` into a nested
   `BinaryExpr` chain.
4. Recurse `_lower_expr` on the synthesized chain — trait
   dispatch (Eq / Ord) and tensor broadcast paths work for
   free.

A new `_chain_compare_counter` field on the lowerer state
keeps `__mn_chain_N` numbering separate from the global `%tN`
sequence, mirroring v5.20.1 Te.5.F.C's `struct_update_counter`
discipline. Counter resets per fn alongside `tmp_counter` /
`block_counter` / `struct_update_counter`.

**IR shape (verified at `-O0`).** For
`0 < middle(c) < 100` where `middle()` is non-trivial:

```llvm
%c.1 = call i64 @middle(i64 %l.0)            ; called ONCE
store i64 %c.1, ptr %t0.a.2
%l.3 = load i64, ptr %t0.a.2
store i64 %l.3, ptr %__mn_chain_0.a.4        ; bound to temp
...
%l.7 = load i64, ptr %__mn_chain_0.a.4       ; pair 1 read
%i.8 = icmp slt i64 %l.6, %l.7
...
%l.11 = load i64, ptr %__mn_chain_0.a.4      ; pair 2 read
%i.13 = icmp slt i64 %l.11, %l.12
%bl.17 = and i1 %l.15, %l.16
```

`@middle` appears exactly once. The temp is loaded twice, but
each load is a free SSA read.

## Phase 3 — bootstrap mirror

**`ast.mn`.** New `Expr::ChainedCmp(List<Expr>, List<String>)`
variant. New `expr_chained_operands` / `expr_chained_ops`
accessors mirroring the `expr_*` family. New `"chained_cmp"`
arm in `expr_kind`.

**`parser.mn`.** Two changes: `op_precedence` updated so
`==`/`!=` return 4 (matching `<`/`>`/`<=`/`>=`) — the D1
precedence merge. New `is_cmp_op` helper. The binary operator
loop in `parse_expr` learns a chain branch: after consuming
one comparison op + RHS, if the next token is also a cmp op,
collect into `operands`/`ops` lists until a non-cmp token. If
exactly one tail collected, emit `Expr::Binary` (legacy shape,
preserves fixed point); otherwise emit `Expr::ChainedCmp`.

**`semantic.mn`.** New `"chained_cmp"` arm in `infer_expr`:
thread state through pairwise `check_binary_expr` calls and
return `make_type("Bool")`. Mirrors the Python checker.

**`lower.mn`.** New `is_trivial_chain_operand` helper matching
Python's predicate verbatim. New `lower_chained_cmp`:
synthesizes `Stmt::Let("__mn_chain_N", false, none, sub)` for
each non-trivial interior operand, replaces with
`Expr::Ident(tmp_name)`, builds a pairwise-Binary chain joined
by `&&`, recurses through `lower_expr`. Per-fn reset of
`chain_compare_counter` added to the existing reset block in
`lower_fn_body`.

**`lower_state.mn`.** New `chain_compare_counter: Int` field
on `LowerState`. Constructor initialized to 0.

## Phase 4 — goldens

| File | Shape | Purpose |
|------|-------|---------|
| `92_chained_cmp_simple.mn` | `0 < x < 10` | 3-element chain, trivial middle (Identifier) |
| `93_chained_cmp_4.mn` | `a < b < c < d` | 4-element chain, all-trivial operands |
| `94_chained_cmp_mixed.mn` | `0 <= x < 10`, `a == b == c` | mixed `<=`/`<` and chained equality |
| `95_chained_cmp_side_effect.mn` | `0 < middle() < 100` | non-trivial middle; once-evaluation visible at runtime |

The side-effect golden is the most important — it's the only
test that catches a regression where the temp gets dropped
and `middle()` runs twice. The Python bootstrap and `mnc-stage1`
must produce byte-identical stdout for all four; the harness
diff flags any divergence.

## Phase 5 — fmt + docs

**SPEC.md §2.2.** New "Chained Comparisons (v5.21.0)"
subsection documenting the syntax, semantics, and once-evaluation
guarantee. Operator precedence table updated: `<`/`>`/`<=`/`>=`/`==`/`!=`
collapsed into a single precedence level (was 7+8, now just 7).
A migration note explains the precedence merge.

**Formatter.** No formatter rewrite rules added. Per the PLAN
("Do not auto-rewrite `a < b && b < c` to `a < b < c` —
preserve user intent"). Whitespace inside chains is already
handled by the existing single-space-around-binary-ops rule.

## What did NOT change

- No new MIR ops (the desugar produces existing `BinOp(LT)`,
  `BinOp(EQ)`, `BinOp(AND)` instructions only).
- No new IR shapes; SSA structure identical to a hand-rolled
  `&&` chain modulo the synthesized `__mn_chain_N` allocas
  for non-trivial middles.
- No runtime function additions.
- No `eq_expr` rule in the grammar — folded into `cmp_expr`.
  Removed `eq_op` / `ne_op` / `lt_op` / `gt_op` / `le_op` /
  `ge_op` parser transformers (replaced by single `cmp_chain`
  transformer that emits BinaryExpr or ChainedCompare based on
  count).

## Strict 3-stage fixed point

Preserved by construction. Single-comparison shapes
(`a < b`, `a == b`) take the legacy AST + lowering path with
no diff. The bootstrap source itself adds one new variant
(`Expr::ChainedCmp`), one accessor pair, one helper
(`is_trivial_chain_operand`), one `lower_chained_cmp` function,
one `is_cmp_op` helper, one new field on `LowerState`, and a
~30-line chain-detection block in `parse_expr`. None of the
existing self-host source uses chained comparisons (the v5.17.x
arc didn't reach for them), so the regenerated stage1/2/3
output is byte-identical to v5.20.1 for the unchanged code
paths.

The bootstrap source delta is additive only; no rewrites of
existing modules. Stage2.ll == stage3.ll preserved.

## Source-line delta

| Module | Net Δ | Notes |
|--------|------:|-------|
| `mapanare/mapanare.lark` | +12 | grammar restructure (cmp_expr → cmp_chain + cmp_tail) |
| `mapanare/parser.py` | +24 | removed 6 op transformers, added cmp_tail/cmp_chain (net +24) |
| `mapanare/ast_nodes.py` | +23 | `ChainedCompare` dataclass + `pair_trait_dispatches` |
| `mapanare/semantic.py` | +17 | `infer_expr` arm for `ChainedCompare` |
| `mapanare/lower.py` | +73 | counter, dispatch, `_lower_chained_compare`, triviality predicate |
| `mapanare/self/ast.mn` | +17 | `ChainedCmp` variant + accessors + kind dispatch |
| `mapanare/self/parser.mn` | +47 | `op_precedence` merge, `is_cmp_op`, chain-collection branch |
| `mapanare/self/semantic.mn` | +16 | `infer_expr` arm |
| `mapanare/self/lower.mn` | +61 | helpers + `lower_chained_cmp` |
| `mapanare/self/lower_state.mn` | +5 | `chain_compare_counter` field + init |
| `docs/SPEC.md` | +33 | "Chained Comparisons (v5.21.0)" subsection + precedence-table refresh |
| **Total source code Δ** | **+295** | additive across 11 files |
| `tests/test_chained_compare.py` | +177 | 13 new tests (AST shape + semantic + IR inspection) |
| `tests/golden/92_*.mn`–`95_*.mn` | +71 | 4 new goldens |

## Out of scope (deferred)

- **Pattern guards using chained cmp** (`match x { n if 0 < n
  < 10 => ... }`) — should *just work* once chained cmp
  parses. Not added as a smoke test in v5.21.0; can land as a
  hygiene addition later.
- **Three-way comparison operator** (`<=>`, spaceship) —
  separate arc.
- **`in` / `is` membership chains** — Python-style
  `a < b in xs`. No demand signal.
- **Range-membership shorthand** (`x in 0..10`) — needs
  iterator/range protocol decision.
- **Linter rule for mixed-direction chains** (`a < b > c`).
  Document as legal but rare; future linter pass.
- **Auto-rewrite `a < b && b < c` → `a < b < c`** in `mnc fmt
  --to-terse`. Per the PLAN, preserve user intent.

## Closes

Empties the v5.21.0 docket. Closes the v5.13–v5.20 terseness
arc's "small wins" cluster. Te.6 sub-items (Te.6.A through
Te.6.G) all shipped in this single session.

## Closeout

- [x] Goldens 95/95 pass through `mnc-stage1`.
- [x] Strict 3-stage fixed point preserved at 238,086 lines /
      0-line diff (same as v5.20.1 — first additive bootstrap
      change since v5.20.1; `Expr::ChainedCmp` not yet used in
      any self-host source).
- [x] `bash scripts/build_from_seed.sh` succeeds (5421552-byte
      `mnc` binary, smoke test OK).
- [x] `make lint` clean (ruff + black + mypy 56 source files
      clean).
- [x] Parser tests 246/246, semantic tests 311/311 pass. New
      `tests/test_chained_compare.py` 13/13 tests covering AST
      shape (single-cmp preserved, 3+ chains build
      ChainedCompare, mixed eq/cmp, mixed direction, chained
      equality), semantic Bool result, and lowering once-eval
      via IR inspection.
- [x] CHANGELOG entry written.
- [x] CLAUDE.md release note written.
- [x] VERSION bumped 5.20.1 → 5.21.0.

**Known broader-suite failures (pre-existing, NOT caused by
v5.21.0):** 35 tests failing in `tests/stdlib/test_regex.py` and
`tests/test_ci.py` reproduce on a `git stash`'d v5.20.1 HEAD
checkout — these are environmental / pre-existing issues
unrelated to chained comparisons.
