# v4.34.0 Design Document — Decision-Tree Pattern Matching

> **Phase 0 artifact.** No code ships until this document is reviewed
> by Cobra (data-structure review) and Rattler (emission-rule review).
> Every implementation decision in Phases 1–2 traces back to a section
> here.

---

## 1. Algorithm Reference

This design adapts the algorithm from:

- **Maranget, Luc.** "Compiling Pattern Matching to Good Decision Trees."
  *ML '08: Proceedings of the 2008 ACM SIGPLAN Workshop on ML*, 2008.
  doi:10.1145/1411304.1411311

The algorithm compiles a *pattern matrix* — where rows are match arms
and columns are the sub-expressions being scrutinized — into a
*decision tree* that minimizes branching. It is the standard approach
used by OCaml, Rust (`rustc_mir_build::build::matches`), Haskell
(GHC), Swift, and Scala.

### Deviations from Maranget

1. **Single-column matrices only (v4.34.0).** Mapanare's `match`
   scrutinizes one expression. The pattern matrix has exactly 1 column
   at the top level. Column explosion occurs only when constructor
   patterns have sub-patterns (e.g., `Rect(w, h)` explodes the column
   into 2 sub-columns). The full multi-column generality of Maranget's
   algorithm is present in the implementation (for nested patterns) but
   the top-level entry point always starts with 1 column.

2. **No or-patterns (v4.34.0).** Or-patterns (`A | B => ...`) are
   v4.35.0 scope. The specialization step does not need to handle
   disjunctive patterns. Each row has exactly one pattern per column.

3. **No guards (v4.34.0).** Match guards (`case x if x > 0 => ...`)
   are v4.35.0 scope. The `PatternRow` struct reserves a `guard` field
   (always `None` in v4.34.0) for forward compatibility.

4. **Column selection heuristic.** Maranget proposes several heuristics
   (§5). We use **necessity-based with leftmost-most-distinct tiebreak**:
   pick the column with the most distinct constructors; break ties by
   choosing the leftmost column. This is deterministic and simple. The
   heuristic matters for multi-column matrices that arise from nested
   pattern specialization.

---

## 2. Pattern Matrix Representation

### 2.1 Data Structures (Python)

```python
@dataclass
class PatternRow:
    """One row of the pattern matrix = one match arm."""
    patterns: list[Pattern]   # length = number of columns
    action_idx: int           # index into the original MatchExpr.arms list
    # v4.35.0: guard: Expr | None = None

@dataclass
class PatternColumn:
    """Metadata for one column being scrutinized."""
    value: Value              # MIR value for this sub-expression
    ty: MIRType               # type of the sub-expression

@dataclass
class PatternMatrix:
    """The core data structure: rows of patterns over columns of scrutinees."""
    rows: list[PatternRow]
    columns: list[PatternColumn]
```

### 2.2 Column Operations

Two operations define the recursion:

**Specialize by constructor `C` with arity `a`** — `specialize(matrix, col, C, a)`:
- Keep only rows where column `col` has constructor `C` (or a wildcard/variable).
- For rows with constructor `C`: replace the single pattern in column `col`
  with `a` sub-patterns (the constructor's arguments). The matrix gains
  `a - 1` new columns (the original column is replaced by the `a` sub-columns).
- For rows with wildcard/variable: replace column `col` with `a` wildcard patterns
  (the wildcard matches any constructor, so it matches `C` with any sub-patterns).
- **Sub-column types for wildcard expansion:** The `a` new columns need types.
  These are obtained from the constructor `C`'s payload signature (via
  `_infer_payload_type` / `infer_variant_payload_type`), not from the
  wildcard pattern itself (which carries no type information). The
  constructor being specialized against determines the column types.

**Default** — `default_matrix(matrix, col)`:
- Keep only rows where column `col` is a wildcard or variable (not a specific constructor).
- Remove column `col` from those rows (the column has been "consumed" by the
  default path).

### 2.3 Pattern Classification

Every pattern falls into one of three categories for the algorithm:

| Category | AST type | Algorithm role |
|----------|----------|---------------|
| **Constructor** | `ConstructorPattern(name, args)` | Provides a tag to split on; has `len(args)` sub-patterns |
| **Wildcard** | `WildcardPattern` | Matches anything; included in every specialization and in the default matrix |
| **Variable** | `IdentPattern(name)` where `name` is NOT an enum variant | Same as wildcard for splitting, but also binds `name` to the scrutinee |
| **Variant-as-ident** | `IdentPattern(name)` where `name` IS an enum variant | Treated as `ConstructorPattern(name, [])` — a zero-arity constructor |
| **Literal** | `LiteralPattern(value)` | Treated as a constructor with tag = the literal value and arity 0 |

The `IdentPattern` ambiguity (variant name vs. binding) is resolved by
consulting the enum variant registry, exactly as the current lowerer does
via `_is_enum_variant()`.

**Known limitation (inherited, not new):** The current `_is_enum_variant`
searches all registered enums regardless of the scrutinee type. If two
enums share a variant name (e.g., both have `Red`), a bare `Red` pattern
is classified as variant-as-ident even when matching the wrong enum. The
`PatternColumn.ty` field provides the correct enum type for scoped lookup,
but fixing this is a follow-up, not a v4.34.0 scope item.

---

## 3. Constructor Enumeration

For each type that appears as a scrutinee column, the algorithm needs
to know whether the type is *closed* (finite, enumerable set of
constructors) or *open* (infinite/unbounded).

### 3.1 Closed Types

| Type | Constructors | Arity |
|------|-------------|-------|
| `Bool` | `true`, `false` | 0, 0 |
| `Option<T>` | `Some`, `None` | 1, 0 |
| `Result<T, E>` | `Ok`, `Err` | 1, 1 |
| User-defined `enum E { A, B(T), C(T, U) }` | `A`, `B`, `C` | 0, 1, 2 |

For user-defined enums, the constructor set is obtained from the
`EnumDef` AST node via the semantic checker's scope (same lookup path
as the current `_check_match_exhaustiveness`).

### 3.2 Open Types

| Type | Treatment |
|------|-----------|
| `Int` | Each literal value is a distinct "constructor" with arity 0. The set is infinite. A default arm is always required. |
| `Float` | Same as `Int`. |
| `String` | Same as `Int`. |
| `List<T>` | Not destructured in v4.34.0. Treated as open. |
| `Map<K, V>` | Not destructured. Treated as open. |
| Any other | Treated as open. |

**Rule:** For open types, the decision tree must always have a default
branch. If it doesn't (no wildcard/variable arm covers the column), the
tree produces a `Fail(NonExhaustive)` node. For closed types, the
default branch is only needed if not all constructors are covered.

### 3.3 Determining "All Constructors Covered"

Given column `col` of type `T`:
1. Collect all distinct constructor tags appearing in column `col`
   across all rows.
2. If `T` is closed, compare against the full constructor set. If every
   constructor is present, the column is *fully covered* and no default
   branch is needed.
3. If `T` is open, the column is never fully covered (default is always
   needed).

---

## 4. Decision-Tree Node Types

```python
@dataclass
class DTLeaf:
    """Match arm reached — execute the action."""
    action_idx: int     # index into MatchExpr.arms

@dataclass
class DTFail:
    """No arm matches — non-exhaustive or unreachable."""
    witness: list[Pattern]   # the missing pattern (for diagnostics)

@dataclass
class DTSwitch:
    """Branch on a scrutinee column."""
    column_idx: int                          # which column to inspect
    cases: list[tuple[str, DecisionTree]]    # (constructor_tag, subtree) — ordered by tag
    default: DecisionTree | None             # taken when no case matches

DecisionTree = DTLeaf | DTFail | DTSwitch
```

### 4.1 Why `cases` Is an Ordered List, Not a Dict

The byte-identity invariant (§7) requires deterministic iteration
order. Python dicts preserve insertion order (CPython 3.7+), but to
make the contract explicit and mirror-friendly for the self-hosted
implementation, `cases` is a list of `(tag, subtree)` pairs. The
insertion order is the order in which constructors appear in the enum
definition (not the order in which they appear in the match arms).
This ensures both Python and self-hosted implementations iterate in
the same order regardless of arm ordering.

### 4.2 Ordering Convention for `cases`

For each `DTSwitch` node, the `cases` list is ordered by the
**enum definition order** of the constructor tags:

1. For `Option<T>`: `[("Some", ...), ("None", ...)]`
2. For `Result<T, E>`: `[("Ok", ...), ("Err", ...)]`
3. For user-defined enums: the order variants appear in the `enum` definition
4. For literal-based switches (Int/String/Bool): order of first
   appearance in the match arms (source order, top to bottom). See §12.3.

This is the canonical ordering. Both implementations must produce
cases in this order.

---

## 5. The Algorithm: `build_decision_tree`

```
function build_decision_tree(matrix: PatternMatrix) -> DecisionTree:
    // Base case 1: no rows — non-exhaustive
    if matrix.rows is empty:
        return DTFail(witness = build_witness(matrix))

    // Base case 2: first row is all wildcards/variables — it matches
    if is_all_wildcards(matrix.rows[0]):
        return DTLeaf(action_idx = matrix.rows[0].action_idx)

    // Recursive case: choose a column and split
    col = select_column(matrix)
    col_type = matrix.columns[col].ty

    // Collect constructors appearing in this column
    ctors_in_column = collect_constructors(matrix, col)

    // Get the full constructor set for closed types
    all_ctors = enumerate_constructors(col_type)  // empty for open types

    // Build cases for each constructor that appears
    cases = []
    for ctor in sort_by_definition_order(ctors_in_column, col_type):
        arity = constructor_arity(ctor, col_type)
        specialized = specialize(matrix, col, ctor, arity)
        subtree = build_decision_tree(specialized)
        cases.append((ctor.tag, subtree))

    // Build default branch if needed
    default = None
    if is_open_type(col_type) or not covers_all(ctors_in_column, all_ctors):
        defaulted = default_matrix(matrix, col)
        default = build_decision_tree(defaulted)

    return DTSwitch(column_idx = col, cases = cases, default = default)
```

### 5.1 `select_column` — Column Selection Heuristic

```
function select_column(matrix: PatternMatrix) -> int:
    best_col = 0
    best_score = -1
    for col in 0 .. len(matrix.columns):
        score = count_distinct_constructors(matrix, col)
        if score > best_score:
            best_score = score
            best_col = col
        // Tiebreak: leftmost column wins (deterministic)
    return best_col
```

A wildcard/variable pattern contributes 0 to the distinct-constructor
count. A constructor or literal pattern contributes 1 (per unique tag).

For v4.34.0 with single-column top-level entry, `select_column` always
returns 0 at the top level. It becomes non-trivial only in recursive
calls where constructor specialization has created multi-column matrices.

### 5.2 `is_all_wildcards`

A row is "all wildcards" if every pattern in the row is a
`WildcardPattern` or a non-variant `IdentPattern`. This check must
consult the enum variant registry to distinguish variant-as-ident from
true variable bindings.

### 5.3 `build_witness` — Missing Pattern Construction

When the matrix is empty (no rows match), we reconstruct which pattern
*would* have matched by walking back up the specialization stack:

```
function build_witness(matrix: PatternMatrix) -> list[Pattern]:
    // matrix.columns tells us how many sub-expressions we're matching.
    // Return one wildcard per column — the simplest pattern that would match.
    // The caller (at the DTSwitch level) refines this by wrapping in the
    // constructor that led to this empty matrix.
    return [WildcardPattern() for _ in matrix.columns]
```

At each `DTSwitch` node, if a constructor `C` leads to `DTFail`, the
witness is `ConstructorPattern(C, fail.witness)`. If the default branch
leads to `DTFail`, the witness is a wildcard (for open types) or the
first missing constructor (for closed types where we know which
constructors are absent).

**Display format:** `Err(_)`, `Some(Ok(_))`, `None`, `42`, `_`.
Wildcards inside witnesses render as `_`. Constructor witnesses render
as `Tag(sub1, sub2, ...)`. Literal witnesses render as the literal value.

---

## 6. Emission Rules: Decision Tree to MIR

### 6.1 Overview

The decision tree maps to MIR basic blocks as follows:

| Node | MIR output |
|------|-----------|
| `DTLeaf(action_idx)` | Jump to the pre-built action block for arm `action_idx` |
| `DTFail(witness)` | `unreachable` instruction (should never execute at runtime; the semantic pass already errored) |
| `DTSwitch(col, cases, default)` | `EnumTag` + `Switch` instruction with one target block per case |

### 6.2 Action Blocks

Before emitting the decision tree, pre-build one action block per match
arm. Each action block:

1. Binds pattern variables (payload extraction via `EnumPayload`).
2. Lowers the arm body (expression or block).
3. Jumps to the merge block (if not terminated by `return`/`break`).

Action blocks are named `match_<N>_action_<I>` where `N` is the
match counter and `I` is the arm index (0-based). They are emitted
in arm order (0, 1, 2, ...).

### 6.3 Switch Emission

For a `DTSwitch` node at depth `D` (0 = top level):

1. **Tag extraction.** Emit `EnumTag` to extract the tag from the
   scrutinee value at `columns[col]`.

2. **Case blocks.** For each `(tag, subtree)` in `cases`:
   - Create a block named `match_<N>_switch_<D>_<tag>`.
   - In that block, recursively emit the subtree. For `DTLeaf`
     subtrees, this is a jump to the action block. Payload extraction
     happens in the action blocks (see §6.6 Rule 6), not in the case
     blocks. For nested `DTSwitch` subtrees, the case block contains
     the next level's tag extraction and switch.

3. **Default block.** If `default` is not None:
   - Create a block named `match_<N>_switch_<D>_default`.
   - Recursively emit the default subtree.
   - If `default` is None (all constructors covered), the Switch
     instruction's default target is `unreachable_<N>_<D>`.

4. **Switch instruction.** Emit `Switch(tag, cases, default_block)`.

### 6.4 Merge Block

After all action blocks, a merge block `match_<N>_merge` collects
results via a `Phi` instruction:

```
match_<N>_merge:
    %match_result = phi [action_0_exit: %val_0, action_1_exit: %val_1, ...]
```

If all arms terminate (all have `return`/`break`), the merge block is
unreachable. In that case, emit a dummy value via `Alloca` + `Load`
of zeroed memory (matching the current convention in both Python and
self-hosted lowerers).

### 6.5 Block Ordering

Blocks are emitted in this deterministic order:

1. **Entry block** (the block active when `_lower_match` is called) —
   contains the top-level `EnumTag` + `Switch`.
2. **Switch case blocks** — in definition order of the constructors,
   depth-first. For nested switches, inner switch blocks are emitted
   before moving to the next outer case.
3. **Unreachable blocks** — immediately after the last case block at
   each depth level (for fully-covered switches where no default arm
   exists).
4. **Action blocks** — in arm order (0, 1, 2, ...).
5. **Merge block** — last.

This ordering is canonical. Both implementations must produce blocks
in exactly this order.

### 6.6 Worked Example

Given:
```
enum Shape { Circle(Int), Rect(Int, Int) }
match s {
    Circle(r) => { return r * r * 3 },
    Rect(w, h) => { return w * h }
}
```

Decision tree:
```
DTSwitch(col=0, cases=[
    ("Circle", DTLeaf(action=0)),
    ("Rect",   DTLeaf(action=1))
], default=None)
```

MIR blocks (match counter N=0):
```
entry:
    %tag = enum_tag %s
    switch %tag [Circle => match_0_switch_0_Circle,
                 Rect   => match_0_switch_0_Rect]
                default match_0_switch_0_unreachable

match_0_switch_0_Circle:
    jump match_0_action_0

match_0_switch_0_Rect:
    jump match_0_action_1

match_0_switch_0_unreachable:
    unreachable

match_0_action_0:              // Circle(r)
    %r = enum_payload %s::Circle:0
    %tmp = mul %r, %r
    %result = mul %tmp, 3
    ret %result

match_0_action_1:              // Rect(w, h)
    %w = enum_payload %s::Rect:0
    %h = enum_payload %s::Rect:1
    %result = mul %w, %h
    ret %result

match_0_merge:                 // unreachable (both arms return)
    %match_result.dummy = alloca ...
    %match_result = load %match_result.dummy
```

### 6.7 Simplified Emission for Flat Switches

When the decision tree is a single `DTSwitch` with all `DTLeaf`
children (no nesting, no multi-level specialization), the switch case
blocks can be eliminated — the `Switch` instruction targets the action
blocks directly:

```
entry:
    %tag = enum_tag %s
    switch %tag [Circle => match_0_action_0,
                 Rect   => match_0_action_1]
                default match_0_merge
```

This optimization is applied when:
- The `DTSwitch` has no nested `DTSwitch` children.
- Every case is a `DTLeaf`.
- No payload extraction is needed in the case blocks (zero-arity
  constructors only), OR the payload extraction can be moved into the
  action blocks.

**For v4.34.0:** Apply this optimization. The current match lowering
already produces this flat shape for simple matches. Preserving it
avoids unnecessary IR bloat and keeps the emitted IR close to the
current output (reducing the diff noise in golden test regeneration).

**Rule for flat-vs-nested:** If the decision tree is a single-level
`DTSwitch` where every case is `DTLeaf`, emit the flat form (Switch
targets action blocks directly). Otherwise, emit the full form with
intermediate switch case blocks.

For flat emission, the action blocks absorb payload extraction:
```
match_0_action_0:              // Circle(r)
    %r = enum_payload %s::Circle:0
    ...
```

This is exactly what the current lowerer does. The decision-tree
rewrite preserves this shape for flat matches and only introduces
intermediate blocks for nested patterns.

---

## 7. Byte-Identity Invariant

> **This is the load-bearing section.** A6 closes if and only if both
> implementations (Python bootstrap in `lower.py` and self-hosted in
> `lower.mn`) produce byte-identical MIR from the same input. The rules
> below define "byte-identical" precisely.

### 7.1 What Must Be Identical

Given the same `.mn` source file compiled through:
- Path A: Python bootstrap (`emit_llvm_text.py` via `lower.py`)
- Path B: `mnc-stage1` (self-hosted `lower.mn` → `emit_llvm.mn`)

The LLVM IR output must be **byte-identical** for every function that
contains a `match` expression.

### 7.2 Sources of Divergence (Current, Pre-v4.34.0)

The 69-line diff between stage2 and stage3 comes from:

1. **Block naming.** Python uses `match_arm_<N>` / `match_merge_<N>`;
   self-hosted uses `match_arm<N>` / `match_merge<N>`. The counter
   increment rules differ.
2. **Unreachable merge materialization.** Python emits `Const(None)`;
   self-hosted emits `Alloca + Load`. Both are correct but different.
3. **PHI entry ordering.** Python adds entries in arm order;
   self-hosted may add the default→merge zeroinitializer entry at a
   different position.
4. **Void arm handling.** Self-hosted replaces void arm results with
   `zeroinitializer` and skips PHI if all arms are void; Python emits
   `Const(None)`.

### 7.3 Convergence Rules

The following rules eliminate all sources of divergence:

**Rule 1: Block naming.**
All blocks use the counter from `_fresh_block` / `fresh_block_label`.
The naming scheme is:

| Block | Name |
|-------|------|
| Action block for arm `I` | `match_<N>_action_<I>` |
| Switch case block at depth `D` for tag `T` | `match_<N>_switch_<D>_<T>` |
| Default block at depth `D` | `match_<N>_switch_<D>_default` |
| Unreachable block at depth `D` | `match_<N>_switch_<D>_unreachable` |
| Merge block | `match_<N>_merge` |

Where `N` is the match-expression counter (monotonically increasing
per function). Both implementations increment the same counter in the
same way.

**For flat emission** (§6.7), the switch case blocks and unreachable
blocks are absent. The Switch instruction targets action blocks
directly, with the merge block as default (if not all constructors are
covered) or an unreachable block named `match_<N>_unreachable` (if
fully covered).

**Rule 2: Unreachable merge.**
When all arms terminate (no arm reaches the merge block), both
implementations emit:
```
match_<N>_merge:
    %match_result.dummy = alloca <fn_return_type>
    %match_result = load <fn_return_type>, ptr %match_result.dummy
```
No `Const(None)`. No `zeroinitializer` in the PHI. Alloca + Load.

**Implementation note:** The Python MIR does not currently have
`Alloca`/`Load` instruction dataclasses (the self-hosted side does via
`Instruction::Alloca`/`Instruction::Load`). The Python lowerer must
either (a) add `Alloca` and `Load` MIR instruction types with
corresponding emitter dispatch entries, or (b) use `Const(dest, ty,
value=None)` and have the LLVM emitter map that to alloca+load. Option
(a) is preferred for clarity.

**Rule 3: PHI entry ordering.**
PHI entries are emitted in **arm order** (arm 0, arm 1, ...). If a
default→merge path exists (the Switch default targets the merge block),
its PHI entry is appended **last**, after all arm entries.

**Rule 4: Void arm handling.**
When an arm body produces a void value (the body is a statement block
with no expression value), the PHI entry for that arm uses
`zeroinitializer` with the type of the first non-void arm's result.
If ALL arms are void, skip the PHI entirely and emit the unreachable-
merge pattern (Rule 2).

**Rule 5: Constructor tag values.**
The `Switch` instruction cases use the same tag values. Both
implementations must use the same `_vtag` / `vtag` mapping from
variant names to integer tag values. The existing convention (variant
index in enum definition order, 0-based) is preserved.

**Rule 6: Instruction ordering within action blocks.**
Within each action block, instructions are emitted in this order:
1. Payload extraction (`EnumPayload` instructions, one per bound variable)
2. Variable binding (`Alloca` + `Store` for each bound name)
3. Arm body instructions

Both implementations must emit payload extractions in sub-pattern
order (left to right in the source: `Rect(w, h)` → extract `w` first,
then `h`).

### 7.4 Verification Protocol

After every change to match lowering in either implementation:

```bash
bash scripts/verify_fixed_point.sh 2>&1 | tail -5
# Expected: "FIXED POINT: stage2.ll and stage3.ll are identical"
# If not: culebra diff /tmp/stage2.ll /tmp/stage3.ll
```

---

## 8. Error Diagnostics

### 8.1 Non-Exhaustive Match

**When:** The decision tree contains a `DTFail` node.

**Where:** Reported by the semantic checker (`semantic.py`), not the
lowerer. The semantic checker builds the decision tree (without
emitting MIR) solely to check for `DTFail` nodes.

**Message format:**
```
error[E0004]: non-exhaustive match: pattern `<witness>` is not covered
  --> src/foo.mn:12:5
   |
12 |     match result {
   |     ^^^^^^^^^^^^^^
13 |         Ok(x) => x + 1,
   |
   = help: add a `case <witness> => ...` arm, or use `case _ => ...` to match all remaining cases
```

**Witness display rules:**
- Constructor with all-wildcard args: `Some(_)`, `Err(_)`, `Circle(_)`
- Constructor with no args: `None`, `Red`, `Blue`
- Nested constructor: `Some(Err(_))`, `Some(Ok(_))`
- Literal: `42`, `"hello"`, `true`
- Wildcard (for open types): `_`
- Multiple missing patterns: list them comma-separated: `Err(_), None`

### 8.2 Unreachable Arm

**When:** An arm's pattern row is never reached by any path through the
decision tree (it is "dominated" by earlier rows).

**Severity:** Warning (not error). Unreachable arms are a code smell
but not a correctness bug.

**Detection:** After building the decision tree, check which
`action_idx` values appear in `DTLeaf` nodes. Any arm index not
appearing in any leaf is unreachable.

**Message format:**
```
warning: unreachable match arm
  --> src/foo.mn:15:9
   |
15 |         Some(42) => special_case(),
   |         ^^^^^^^^ this arm will never be reached
   |
   = note: arm at line 14 already matches all `Some` values
```

### 8.3 Self-Hosted Exhaustiveness (v4.34.0 scope)

The self-hosted semantic checker (`semantic.mn`) gets the same
exhaustiveness logic, but it is NOT wired into `compile()` until
A7 lands (v4.52.0). The code exists, is tested via the Python
bootstrap's golden tests, but is dormant in the self-hosted binary.

---

## 9. Shared Helper vs. Duplicated Logic

**Decision: shared helper in `mapanare/pattern_matching.py`.**

A new file `mapanare/pattern_matching.py` contains:
- `PatternRow`, `PatternColumn`, `PatternMatrix` data structures
- `DTLeaf`, `DTFail`, `DTSwitch` decision-tree nodes
- `build_decision_tree(matrix) -> DecisionTree`
- `specialize(matrix, col, ctor, arity) -> PatternMatrix`
- `default_matrix(matrix, col) -> PatternMatrix`
- `select_column(matrix) -> int`
- `build_witness(matrix) -> list[Pattern]`
- `find_unreachable_arms(tree, num_arms) -> set[int]`

Both `semantic.py` and `lower.py` import from this file:
- `semantic.py` calls `build_decision_tree` for exhaustiveness checking
  and `find_unreachable_arms` for warnings.
- `lower.py` calls `build_decision_tree` for MIR emission.

The shared helper avoids two independent implementations of the
algorithm on the Python side. The self-hosted side (`lower.mn`) has
its own implementation that mirrors the shared helper byte-for-byte.

---

## 10. Migration Path

### 10.1 Python Side

1. Add `mapanare/pattern_matching.py` with the shared helper.
2. Replace `_lower_match` in `lower.py` wholesale. The old method body
   is deleted entirely — no dual-path period, no feature flag.
3. Replace `_check_match_exhaustiveness` in `semantic.py` with a call
   to the shared `build_decision_tree` + `DTFail` check.
4. Delete dead helpers: any function in `lower.py` that was only called
   from the old `_lower_match`.

### 10.2 Self-Hosted Side

1. Add decision-tree types and builder to `lower.mn` (inline, not a
   new module — the self-hosted compiler doesn't support multi-module
   compilation at the match-rewrite level yet).
2. Replace `lower_match` and `build_match_arms` wholesale.
3. Delete dead helpers.

### 10.3 No Backward Compatibility

The old match lowering is deleted. There is no `--legacy-match` flag.
If the decision-tree lowering produces incorrect IR, it is a bug to
fix, not a reason to keep the old code.

---

## 11. Nested Patterns

### 11.1 Grammar Audit

The current Mapanare grammar supports:
```
constructor_pattern: NAME LPAREN (pattern (COMMA pattern)*)? RPAREN
```

This allows arbitrary nesting: `Some(Ok(Pair(x, y)))` parses as
`ConstructorPattern("Some", [ConstructorPattern("Ok", [ConstructorPattern("Pair", [IdentPattern("x"), IdentPattern("y")])])])`.

### 11.2 Algorithm Impact

Nested patterns cause column explosion during specialization. For
example, specializing by `Some` in `Option<Result<Int, String>>`
produces a sub-matrix with 1 column of type `Result<Int, String>`.
That column may then be split by `Ok`/`Err`, producing further
sub-columns.

The recursion depth equals the nesting depth of patterns. For
Mapanare's current usage (at most 2-3 levels of nesting in practice),
this is not a concern. The algorithm handles arbitrary depth by
construction.

### 11.3 Nested Pattern in Golden Tests

The new `48_match_nested_exhaustive.mn` golden test exercises:
```
match opt_result {
    Some(Ok(v))  => { ... },
    Some(Err(e)) => { ... },
    None         => { ... }
}
```

This produces a 2-level decision tree:
```
DTSwitch(col=0, cases=[
    ("Some", DTSwitch(col=0, cases=[
        ("Ok",  DTLeaf(0)),
        ("Err", DTLeaf(1))
    ], default=None)),
    ("None", DTLeaf(2))
], default=None)
```

---

## 12. Literal Patterns

### 12.1 Treatment

Integer, float, string, and boolean literals are treated as zero-arity
constructors. Each distinct literal value is a unique "constructor tag."

For `Bool`, the type is closed: constructors are `true` and `false`.
Exhaustiveness works normally.

For `Int`, `Float`, `String`: the type is open. A default arm is
always required. If missing, `DTFail` is produced and the semantic
checker reports a non-exhaustive error.

### 12.2 Switch Emission for Literals

The existing `Switch` MIR instruction already handles literal cases:
`cases: list[tuple[Any, str]]` where the first element can be an
integer, string, or other literal. The LLVM emitter's `_do_switch`
already handles both variant-name and integer cases. No changes needed.

### 12.3 Literal Ordering

For the byte-identity invariant, literal cases in the `Switch`
instruction are ordered by their **first appearance in the match arms**
(top to bottom, source order). This matches the current behavior in
both Python and self-hosted lowerers and is deterministic. See §4.2
item 4 for the cross-reference.

---

## 13. Out of Scope for v4.34.0

| Feature | Target |
|---------|--------|
| Match guards (`case x if x > 0`) | v4.35.0 |
| Or-patterns (`case A \| B`) | v4.35.0 |
| Range patterns (`case 1..10`) | v5.x backlog |
| Pattern bindings (`case x @ Some(42)`) | v5.x backlog |
| Active patterns (F#-style) | v5.x backlog, likely not |
| Struct destructuring (`case Point { x, y }`) | v5.x backlog |
| Tuple destructuring (`case (a, b)`) | v5.x backlog |

The `PatternRow` struct includes a `guard` field (always `None`) and
the `PatternMatrix` operations are designed to accommodate guards
(Maranget §6), but guard-related code paths are not implemented.

---

## 14. Interaction with `?` Operator (v4.33.0)

The `?` operator desugars to a match expression internally:
```
let v: Int = expr?
// desugars to:
match expr {
    Ok(__try_val) => __try_val,
    Err(__try_err) => { return Err(__try_err) }
}
```

The v4.34.0 match rewrite applies to this desugared form. The IR
produced by `?` will change shape (new block naming, cleaner structure)
but the semantics are identical. The `47_try_operator.mn` golden test's
reference IR will be regenerated.

---

## 15. MIR Instruction Changes

### 15.1 No New Instructions

The decision-tree lowering uses the existing MIR instruction set:
- `EnumTag` — extract tag for switch
- `Switch` — multi-way branch
- `EnumPayload` — extract payload after tag check
- `Jump` — unconditional branch
- `Phi` — merge values from multiple predecessor blocks
- `Alloca` / `Load` — unreachable merge dummy values

No new MIR instructions are introduced in v4.34.0.

### 15.2 MIR Verifier

No verifier changes needed. The existing `Switch` validation (each
case label exists as a block, default block exists) is sufficient.

---

## 16. Testing Strategy

### 16.1 Unit Tests for the Algorithm

`tests/unit/test_pattern_matching.py`:
- `test_single_wildcard` — matrix with one wildcard row → `DTLeaf`
- `test_two_constructors` — Option Some/None → `DTSwitch` with 2 cases
- `test_nested_option_result` — `Option<Result>` → 2-level tree
- `test_open_type_requires_default` — Int match without default → `DTFail`
- `test_closed_type_no_default` — all enum variants covered → no default
- `test_witness_construction` — verify witness pattern is correct
- `test_column_selection` — verify leftmost-most-distinct heuristic
- `test_unreachable_detection` — dominated arm detected

### 16.2 Semantic Tests

`tests/semantic/test_match_exhaustive.py`:
- 13 cases as specified in PLAN.md Phase 3.1

### 16.3 Golden Tests

- All existing match-related golden tests regenerated (07, 10, 17, 19,
  24, 32, 47)
- New `48_match_nested_exhaustive.mn`

### 16.4 Fixed-Point Test

```bash
bash scripts/verify_fixed_point.sh
```
Must return 0-line diff. This is the A6 closure evidence.

---

## Appendix A: Worked Example — Non-Exhaustive Detection

Input:
```
match opt {
    Some(x) => { print(str(x)) }
}
```

Pattern matrix (1 column, type `Option<Int>`):
```
Row 0: [ConstructorPattern("Some", [IdentPattern("x")])]  action=0
```

Algorithm:
1. Not empty, not all-wildcards → split.
2. `select_column` → 0 (only column).
3. Constructors in column: `{"Some"}`.
4. `Option<Int>` is closed: `{"Some", "None"}`.
5. Build case for "Some":
   - `specialize(matrix, 0, "Some", 1)` → matrix with 1 column (sub-pattern), 1 row: `[IdentPattern("x")]` action=0
   - `build_decision_tree(specialized)` → `is_all_wildcards(row 0)` → `DTLeaf(0)`
6. Not all constructors covered (`None` missing) → build default:
   - `default_matrix(matrix, 0)` → matrix with 0 columns, 0 rows (no wildcard rows exist)
   - `build_decision_tree(defaulted)` → empty matrix → `DTFail(witness=[])` → wrapped as `ConstructorPattern("None", [])` at the switch level

Result:
```
DTSwitch(col=0, cases=[
    ("Some", DTLeaf(0))
], default=DTFail(witness=[ConstructorPattern("None", [])]))
```

Diagnostic: `error: non-exhaustive match: pattern 'None' is not covered`

---

## Appendix B: Worked Example — Nested Pattern Specialization

Input:
```
match x {
    Some(Ok(v))  => { ... },     // arm 0
    Some(Err(e)) => { ... },     // arm 1
    None         => { ... }      // arm 2
}
```

Type: `Option<Result<Int, String>>`

**Step 1:** Initial matrix (1 column, type `Option<Result<Int, String>>`):
```
Row 0: [ConstructorPattern("Some", [ConstructorPattern("Ok", [IdentPattern("v")])])]   action=0
Row 1: [ConstructorPattern("Some", [ConstructorPattern("Err", [IdentPattern("e")])])]  action=1
Row 2: [ConstructorPattern("None", [])]                                                 action=2
```

**Step 2:** Split on column 0. Constructors: `{Some, None}`. Both present → fully covered, no default.

**Step 3a:** Specialize by `Some` (arity 1):
New matrix (1 column, type `Result<Int, String>`):
```
Row 0: [ConstructorPattern("Ok", [IdentPattern("v")])]    action=0
Row 1: [ConstructorPattern("Err", [IdentPattern("e")])]   action=1
```

Recurse → split on column 0. Constructors: `{Ok, Err}`. Fully covered.
- Specialize by `Ok` (arity 1): matrix = `[[IdentPattern("v")]]` action=0 → all wildcards → `DTLeaf(0)`
- Specialize by `Err` (arity 1): matrix = `[[IdentPattern("e")]]` action=1 → all wildcards → `DTLeaf(1)`

**Step 3b:** Specialize by `None` (arity 0):
New matrix (0 columns):
```
Row 0: []   action=2
```
All wildcards (trivially) → `DTLeaf(2)`.

**Final tree:**
```
DTSwitch(col=0, cases=[
    ("Some", DTSwitch(col=0, cases=[
        ("Ok",  DTLeaf(0)),
        ("Err", DTLeaf(1))
    ], default=None)),
    ("None", DTLeaf(2))
], default=None)
```

Exhaustive: no `DTFail` nodes. Semantic check passes.

---

## Sign-Off

- [x] **Cobra** — PASS WITH NOTES. Data structures sound; PatternRow.bindings
  removed per review; sub-column type resolution for wildcard expansion
  documented; `_is_enum_variant` scope limitation noted as known.
- [x] **Rattler** — PASS WITH NOTES. Emission rules sound for LLVM IR;
  literal ordering contradiction resolved (source-order wins); unreachable
  blocks added to §6.5 ordering; §6.3 payload extraction clarified;
  Python MIR Alloca/Load gap noted.
