# Mapanare v4.35.0 — Match Guards + Or-Patterns

> **Two new syntactic forms.** Delta review is mandatory per
> `REVIEW_CADENCE.md`. Both features build directly on v4.34.0's
> decision-tree infrastructure — Maranget's algorithm handles
> or-patterns natively (column specialization walks through
> alternatives), and guards are a post-match check that fits cleanly
> between the `Leaf` node and the action jump.

**Status:** PLANNED
**Breaking:** No (additive syntax; existing matches keep working unchanged)
**Prerequisite:** v4.34.0 (decision-tree match lowering must be byte-identical between pipelines first — A6 closed)
**Delta review:** **YES** — Coral lens, with Rattler cross-check on the guard lowering. Two new syntactic forms means the reviewer verifies both.
**Full panel:** No (cadence fires at v4.36.0, which is the arc-1 close release)
**Estimated work:** 1.5 sprints
**Theme:** Last growth release of Arc 1. Expressive match patterns on top of v4.34.0's correctness work.

---

## Why this is one release (and not two)

Guards and or-patterns are separable features, and in many other languages they shipped in different releases. The v4.35.0 case for combining them:

1. **They share a design constraint.** Both need to interact correctly with exhaustiveness checking. A guard can "fail" at runtime without the overall match being non-exhaustive (the guard failure falls through to the next arm — or to a non-exhaustive error if there is no next arm). Or-patterns broaden coverage by compiling to multiple rows in the decision tree. Both change what the exhaustiveness checker must track.
2. **The delta review is cheaper done together.** Two features, one reviewer session, one verdict. The reviewer reads the grammar once, the semantic checker once, the lowering once.
3. **v4.36.0 is the arc-1 panel release** and has to ship soon after v4.35.0. Splitting guards and or-patterns into v4.35.0 and v4.35.1 (point release) works structurally, but the anti-rush rule says don't split if the combined scope is sprint-sized and coherent. This is.

**Counterargument accepted:** if the delta reviewer at Phase 6 says "no, split these — the guard semantics need their own review cycle," the lead can slip or-patterns to v4.35.1 without drama. The PLAN.md below is written so either split is executable from the same codebase.

---

## Part A — Match guards

### What they look like

```mapanare
match opt {
    Some(x) if x > 0 => print("positive"),
    Some(x) if x < 0 => print("negative"),
    Some(0) => print("zero"),
    None => print("absent"),
}
```

A `case` arm can have an optional `if <expr>` clause between the pattern and the `=>`. The guard is a boolean expression evaluated after the pattern matches. If the guard is `false`, the match falls through to the next arm. If the guard is `true`, the arm's body executes. If no arm matches (all guards fail and patterns don't cover everything), the behavior is defined by the exhaustiveness checker: v4.34.0's rule applies — compile-time error unless there's a catch-all arm.

### The subtlety

**Exhaustiveness with guards is tricky.** A pattern with a guard does not "cover" that pattern for exhaustiveness purposes — the exhaustiveness check has to assume the guard could be false. Concretely:

```mapanare
match x {
    Some(v) if v > 0 => ...,
    None => ...,
    // ERROR: the arm `Some(v)` is not exhaustively covered
    //        (when v <= 0, neither arm matches)
}
```

The correct exhaustiveness rule: **a guarded arm contributes zero coverage.** The unguarded pattern beneath it (if any) is what provides coverage. If no unguarded pattern covers the case, the match is non-exhaustive.

Rust handles this with a clever trick: a guarded arm specializes the decision-tree column as if it were unguarded for the purposes of coverage computation, BUT still emits the runtime guard check. So the exhaustiveness walk "sees" the pattern as fully matching, while the runtime code path includes the fall-through-on-guard-failure behavior.

**Mapanare's v4.35.0 rule:** follow Rust. Guards don't affect exhaustiveness analysis. A guarded arm emits a pattern-match-then-guard-check; guard failure jumps to the next arm's decision-tree path.

### Grammar

```
case_arm: "case" pattern guard? "=>" expr_or_block
guard: "if" expression
```

The `guard` is optional. `expression` must evaluate to `Bool`. No new terminals — `if` is already a keyword.

### AST

```python
@dataclass
class CaseArm:
    pattern: Pattern
    guard: Optional[Expr]  # NEW in v4.35.0
    action: Expr  # or Block
    span: Span
```

The `guard: Optional[Expr]` field is new. Existing call sites that construct `CaseArm` need to pass `guard=None`.

### Semantic

- [ ] `mapanare/semantic.py` — in `check_match_expr`:
  - For each arm with a guard, type-check the guard expression in a scope that includes the pattern bindings. The guard can reference names bound by the pattern.
  - The guard's type must be `Bool`. Anything else is a compile error with a rustc-quality message ("guard must have type Bool, got X").
  - Exhaustiveness check: build the pattern matrix **as if guards were absent** — i.e., a `PatternRow` with a guard contributes its unguarded pattern to the matrix for coverage purposes. The guard is attached to the row for lowering but not for exhaustiveness.
  - If the resulting matrix is non-exhaustive, fire the rustc-quality error as in v4.34.0.

### Lowering

- [ ] `mapanare/lower.py` — the decision tree's `Leaf` node gains an optional guard field:

  ```python
  @dataclass
  class Leaf:
      action_idx: int
      guard: Optional[Expr]  # NEW in v4.35.0
  ```

- [ ] `_emit_decision_tree` — when emitting a `Leaf`, if `guard` is present, emit:
  1. Lower the guard expression in the current block (the pattern bindings are in scope).
  2. Branch on the guard result: `true` → jump to the action block; `false` → jump to the "fall-through" block of the enclosing decision tree.
- [ ] The "fall-through" block is the next alternative in the decision tree. For the top-level match, it's the "retry the next row of the pattern matrix" block — which, in decision-tree compilation terms, means re-running the remaining rows of the matrix.
- [ ] **This is the trickiest part of the lowering.** Maranget's original paper does not handle guards because ML doesn't have them. The Rust compiler handles them by running the decision-tree algorithm per-arm and sewing together the resulting trees with fall-through edges. Reference `rustc_mir_build::build::matches::test` for the canonical implementation.
- [ ] For v4.35.0, the simplest correct approach: guard failure = re-run the decision tree starting from the next row after the current arm. This is O(n²) in arm count, but arm counts are small (typically < 20 in real code) and the clarity wins over cleverness. If profiling later shows it's a bottleneck, optimize.

### MIR

- [ ] `mapanare/mir.py` — no new instruction kinds. The guard is a boolean expression that lowers to existing MIR (compare, BrCond).
- [ ] `MIRVerifier` — no changes.

### Self-hosted mirror

- [ ] `mapanare/self/ast.mn` — add `guard: Option<Expr>` to `CaseArm`. Follow the project convention: the field is present but nullable, constructor functions default to `None`.
- [ ] `mapanare/self/parser.mn` — accept optional `if <expr>` between the pattern and the `=>`.
- [ ] `mapanare/self/semantic.mn` — guard type check + exhaustiveness-as-if-unguarded rule. As with v4.34.0, the self-hosted semantic is not yet called from `compile()` (A7 = v4.52.0), so this is ready-for-later.
- [ ] `mapanare/self/lower.mn` — decision-tree `Leaf` node's guard field. Same "re-run from next row" approach.
- [ ] **Byte-identity invariant still holds.** Both pipelines must produce the same IR for a guarded match.

---

## Part B — Or-patterns

### What they look like

```mapanare
match token {
    TOK_PLUS | TOK_MINUS => print("additive"),
    TOK_MUL | TOK_DIV | TOK_MOD => print("multiplicative"),
    TOK_EOF => print("end"),
    _ => print("other"),
}
```

A `case` arm's pattern can be a disjunction of patterns separated by `|`. All alternatives share the same RHS (action). All alternatives must bind the same set of variable names with compatible types (if any alternative binds `x`, every alternative must bind `x` with the same type).

### The subtlety

**Or-patterns compose with exhaustiveness trivially, but bindings are tricky.**

Composing with exhaustiveness: an or-pattern `A | B | C` covers the same cases as three separate rows `A => ...`, `B => ...`, `C => ...` with the same action. Maranget's specialization step handles this by "exploding" an or-pattern row into multiple rows during matrix construction. Zero special-case logic needed in the exhaustiveness check.

Bindings: this is the hard part. Consider:

```mapanare
match x {
    Some(v) | None => print(v),  // ERROR: v is only bound in Some
}
```

The or-pattern `Some(v) | None` cannot work because `None` does not bind `v`. The semantic check must enforce: **every alternative in an or-pattern must bind the same set of names with compatible types.**

Valid:
```mapanare
match pair {
    (Some(x), None) | (None, Some(x)) => print(x),  // x bound consistently
}
```

Here both alternatives bind `x` with the same type (`T` from the relevant `Option<T>`). This is the "or-patterns as symmetry" use case that makes the feature valuable — without it, you'd duplicate the action across two separate arms.

### Grammar

```
pattern: pattern_alt ( "|" pattern_alt )*
pattern_alt: /* existing pattern forms: literal, wildcard, constructor, struct, tuple, binding */
```

The top-level `pattern` becomes a disjunction of `pattern_alt` (the pre-v4.35.0 pattern form). An un-or'd pattern is just `pattern_alt` with one element, so existing code keeps parsing unchanged.

**Precedence note:** `|` in a pattern context must not conflict with bitwise OR. In Mapanare, bitwise OR in expression position is `|` but pattern context is unambiguous by grammar position. Verify with a specific test case where both appear.

### AST

```python
@dataclass
class Pattern:  # base class stays
    span: Span

@dataclass
class OrPattern(Pattern):
    alternatives: list[Pattern]  # NEW in v4.35.0; each alt is a non-or pattern
    span: Span
```

An un-or'd pattern is NOT wrapped in `OrPattern` — it stays as its base form. Only actual disjunctions get the wrapper. This keeps existing code paths unchanged.

Alternative design: always wrap, `OrPattern.alternatives` has length 1 for single patterns. **Not chosen** because it cascades changes through every existing `isinstance(pat, ...)` call site. The "wrap only when needed" design is more surgical.

### Semantic

- [ ] `mapanare/semantic.py` `check_or_pattern`:
  - Recurse into each alternative, compute its pattern-level scope (the names it binds + their types).
  - Verify all alternatives bind the same set of names with compatible types (equality for v4.35.0 — no widening).
  - If mismatched, rustc-quality error: "or-pattern alternative binds different names" with per-alternative name lists.
  - Return the unified binding scope (shared across all alternatives).
- [ ] Exhaustiveness integration: when the decision-tree builder specializes a column, expand or-patterns by splitting rows. A row `(A | B | C, rest) => action` becomes three rows `(A, rest) => action`, `(B, rest) => action`, `(C, rest) => action`. The action index is shared; only one action block is emitted.

### Lowering

- [ ] `mapanare/lower.py` — row expansion happens during matrix construction, not during tree emission. This is the clean Maranget-native approach.
- [ ] `_build_initial_matrix` — when processing a `CaseArm` with an `OrPattern` top-level pattern, emit one `PatternRow` per alternative, all pointing at the same action index.
- [ ] Alternatives deeper in a pattern (e.g., `Some(A | B)`) are expanded similarly: specialize the outer constructor, then recurse into the inner or-pattern by expanding its rows.
- [ ] Binding extraction in the action block: the pattern bindings from any alternative should work the same way — they're the same names with the same types, so the action block sees consistent bindings regardless of which alternative matched.

### Self-hosted mirror

- [ ] `mapanare/self/ast.mn` — add `OrPattern { alternatives: List<Pattern> }` as a new variant of the `Pattern` enum.
- [ ] `mapanare/self/parser.mn` — parse disjunction: collect `pattern_alt ("|" pattern_alt)*` and wrap in `OrPattern` if more than one.
- [ ] `mapanare/self/semantic.mn` — same binding-compatibility check as Python side.
- [ ] `mapanare/self/lower.mn` — same row-expansion approach.
- [ ] **Byte-identity invariant holds.** Or-patterns compile to multiple rows in the matrix in both pipelines; the matrix build is deterministic; the decision-tree output is deterministic; the IR is byte-identical.

---

## Phase 0 — pre-commit sanity

- [ ] Confirm v4.34.0 tag is clean: all 20 exit criteria green, fixed-point diff = 0 lines, A6 closed in `CARRY_FORWARD.md`.
- [ ] `bash scripts/verify_fixed_point.sh` — **0 lines diff confirmed.**
- [ ] Read `.reviews/CARRY_FORWARD.md` — confirm A6 is CLOSED and the row's evidence points at v4.34.0.
- [ ] Read `docs/roadmap/v4/v4.34.0/DESIGN.md` — the decision-tree algorithm doc. v4.35.0 builds on it.
- [ ] Choose delta reviewer: **Coral** primary (language design, new syntax), **Rattler** secondary (lowering scrutiny). Coral reviews first; Rattler cross-checks the guard-fall-through lowering.

---

## Phase 1 — Guards implementation

### Phase 1.1: Grammar

- [ ] `mapanare/mapanare.lark` — add optional guard to `case_arm`:

  ```
  case_arm: "case" pattern guard? "=>" expr_or_block
  guard: "if" expression
  ```

- [ ] Verify that `if` in guard position doesn't conflict with `if` in expression position. It shouldn't — the grammar is unambiguous from context (guard is after `pattern`, before `=>`).
- [ ] Update any lexer/parser tests that check `case_arm` structure.

### Phase 1.2: AST

- [ ] `mapanare/ast_nodes.py` — add `guard: Optional[Expr]` to `CaseArm`. Update the dataclass field list.
- [ ] Audit every existing call site that constructs `CaseArm`. Python has no default for optional fields unless specified, so make `guard: Optional[Expr] = None`. Or: update every call site to pass `guard=None`. Prefer the default for minimal change.
- [ ] Update `CaseArm.__repr__` or equivalent if it's used for debugging.

### Phase 1.3: Parser transformer

- [ ] `mapanare/parser.py` — the `case_arm` transformer reads the optional guard child. If present, attach to the `CaseArm`. If absent, pass `None`.

### Phase 1.4: Semantic check

- [ ] `mapanare/semantic.py` `check_case_arm`:
  - After checking the pattern and establishing the pattern's binding scope, check the guard (if present) in that scope.
  - Guard's inferred type must be `Bool`. Otherwise rustc-quality error:

    ```
    error: guard must have type `Bool`, got `Int`
      --> src/foo.mn:15:20
       |
    15 |         Some(x) if x => ...,
       |                    ^ guard has type `Int`, not `Bool`
       |
       = help: compare the value: `if x > 0` or `if x != 0`
    ```

  - Exhaustiveness rule: when building the pattern matrix for exhaustiveness, **ignore the guard**. The row's pattern alone determines coverage.

### Phase 1.5: Lowering

- [ ] `mapanare/lower.py` — extend `PatternRow` with `guard: Optional[Expr]`:

  ```python
  @dataclass
  class PatternRow:
      patterns: list[Pattern]
      guard: Optional[Expr]  # NEW
      action_idx: int
      source_span: Span  # helpful for error messages
  ```

- [ ] `_build_decision_tree` — when reducing a matrix to a `Leaf`, check if the leaf's row has a guard:
  - If no guard: `Leaf(action_idx)` — unchanged from v4.34.0
  - If guard: `Leaf(action_idx, guard=...)` — new

- [ ] `_emit_decision_tree` — when emitting a `Leaf` with a guard:
  1. Compute the "fall-through target" — the block the decision-tree walker should jump to if the guard fails. Maranget-style: this is the next sub-tree that the walker would visit if the current row didn't exist.
  2. Lower the guard expression in the current block.
  3. Emit `BrCond(guard_value, action_block, fallthrough_block)`.
  4. The fallthrough block is then the entry point for the "remaining matrix" decision tree.

- [ ] **Implementation detail:** computing the fallthrough target correctly is the hard part. The simplest correct approach:
  - Before starting decision-tree construction, sort the pattern matrix such that each row knows its "next row." Then a guard failure on row N jumps to a decision-tree rooted at the sub-matrix starting from row N+1.
  - This is O(N) additional decision trees per match (one per guarded row). The trees share structure — Rust's implementation memoizes the sub-trees to avoid exponential blowup.
  - v4.35.0 is allowed to NOT memoize for simplicity; the overhead is small for realistic matches (< 20 arms). Note the limitation in DESIGN.md addendum.

### Phase 1.6: Self-hosted mirror

- [ ] `mapanare/self/ast.mn` — `CaseArm.guard: Option<Expr>` field added
- [ ] `mapanare/self/parser.mn` — optional `if <expr>` parsed between pattern and `=>`
- [ ] `mapanare/self/semantic.mn` — guard type check (ready-for-A7-wiring)
- [ ] `mapanare/self/lower.mn` — guard-aware leaf lowering with fall-through

### Phase 1.7: Rebuild + validate

- [ ] `python scripts/build_stage1.py` — rebuild
- [ ] Existing goldens still pass
- [ ] New guard goldens (Phase 3) pass
- [ ] `bash scripts/verify_fixed_point.sh` — **still 0 lines diff.** If guards introduce a divergence between Python and self-hosted pipelines, the byte-identity invariant from v4.34.0 is broken. Fix before moving on.

---

## Phase 2 — Or-patterns implementation

### Phase 2.1: Grammar

- [ ] `mapanare/mapanare.lark` — add or-pattern:

  ```
  pattern: pattern_alt ("|" pattern_alt)*
  pattern_alt: /* existing pattern forms */
  ```

- [ ] **Precedence test:** in a match arm like `case 1 | 2 | 3 if x > 0 => ...`, the grammar should parse as `(1 | 2 | 3) if (x > 0)`, not `(1 | 2 | (3 if x > 0))`. Verify with a specific unit test.
- [ ] **Binary-OR test:** `case (a | b) => ...` in a match context. The `|` here is pattern-OR, not bitwise-OR, because we're in a pattern position. The grammar should be unambiguous. If there's a parse conflict with expression-level `|`, the grammar needs explicit disambiguation. Resolve if so.

### Phase 2.2: AST

- [ ] `mapanare/ast_nodes.py` — new dataclass:

  ```python
  @dataclass
  class OrPattern(Pattern):
      alternatives: list[Pattern]  # each is a non-or Pattern
      span: Span
  ```

- [ ] Invariant: `len(alternatives) >= 2`. A single-alternative case uses the base pattern directly, not an `OrPattern` wrapper.

### Phase 2.3: Parser transformer

- [ ] `mapanare/parser.py` — `pattern` transformer:

  ```python
  def pattern(self, children):
      # children is a list of pattern_alt results
      if len(children) == 1:
          return children[0]
      return OrPattern(alternatives=children, span=merge_spans(children))
  ```

- [ ] Span merging: the `OrPattern`'s span covers from the first alternative's start to the last alternative's end.

### Phase 2.4: Semantic check

- [ ] `mapanare/semantic.py` `check_or_pattern`:

  ```python
  def check_or_pattern(self, pat: OrPattern, expected_type: Type) -> BindingScope:
      scopes: list[BindingScope] = []
      for alt in pat.alternatives:
          scope = self.check_pattern(alt, expected_type)
          scopes.append(scope)

      # Verify all alternatives bind the same names with same types
      ref_names = set(scopes[0].names())
      for i, scope in enumerate(scopes[1:], start=1):
          names = set(scope.names())
          if names != ref_names:
              missing = ref_names - names
              extra = names - ref_names
              msg = f"or-pattern alternative binds different names: "
              if missing:
                  msg += f"missing {sorted(missing)}; "
              if extra:
                  msg += f"extra {sorted(extra)}"
              self._error(SemanticError(
                  line=pat.alternatives[i].span.line,
                  column=pat.alternatives[i].span.column,
                  end_line=pat.alternatives[i].span.end_line,
                  end_column=pat.alternatives[i].span.end_column,
                  message=msg,
                  suggestion="every alternative in an or-pattern must bind the same set of variables",
              ))

      # For each shared name, verify type compatibility across alternatives
      for name in ref_names:
          types = [scope.get_type(name) for scope in scopes]
          if not all(types_compatible(t, types[0]) for t in types[1:]):
              self._error(SemanticError(
                  ...,
                  message=f"or-pattern alternative binds `{name}` with different types: {types}",
                  suggestion="the types must match across alternatives",
              ))

      return scopes[0]  # return the unified scope
  ```

### Phase 2.5: Lowering (row expansion)

- [ ] `mapanare/lower.py` `_build_initial_matrix` — when processing a `CaseArm` whose pattern is an `OrPattern`, emit one `PatternRow` per alternative. All rows share the same `action_idx` (the action block is compiled exactly once).

- [ ] For nested or-patterns (e.g., `Some(A | B)`), the expansion is recursive: specialize on the outer constructor `Some`, then recurse into the inner or-pattern and expand its rows. Maranget's specialize step naturally handles this if the row expansion is done at matrix construction time.

- [ ] **Bindings from alternatives:** when an alternative matches, the row's pattern provides the binding. If the action block references `x` and the matched alternative binds `x`, the action sees the right value. Each alternative row in the matrix tracks its own binding scope during the decision-tree walk; at emit time, the binding extraction for the action block reads from whichever alternative actually matched.

### Phase 2.6: Self-hosted mirror

- [ ] `mapanare/self/ast.mn` — `OrPattern` variant added
- [ ] `mapanare/self/parser.mn` — pattern disjunction parsed
- [ ] `mapanare/self/semantic.mn` — binding-compatibility check
- [ ] `mapanare/self/lower.mn` — row expansion during matrix construction

### Phase 2.7: Rebuild + validate

- [ ] `python scripts/build_stage1.py` — rebuild
- [ ] Existing goldens still pass
- [ ] New or-pattern goldens (Phase 3) pass
- [ ] `bash scripts/verify_fixed_point.sh` — **still 0 lines diff.** Byte-identity preserved.

---

## Phase 3 — Tests

### Phase 3.1: Golden tests

- [ ] `tests/golden/49_match_guards.mn` — NEW:

  ```mapanare
  fn classify(n: Int) -> String {
      match n {
          x if x < 0 => "negative",
          0 => "zero",
          x if x > 0 && x < 10 => "small",
          x if x >= 10 => "large",
          _ => "unreachable",
      }
  }

  fn main() {
      print(classify(-5))  // "negative"
      print(classify(0))   // "zero"
      print(classify(3))   // "small"
      print(classify(42))  // "large"
  }
  ```

- [ ] `tests/golden/50_match_or_patterns.mn` — NEW:

  ```mapanare
  enum Token {
      Plus,
      Minus,
      Star,
      Slash,
      Mod,
      Eof,
      Ident(String),
  }

  fn category(t: Token) -> String {
      match t {
          Token::Plus | Token::Minus => "additive",
          Token::Star | Token::Slash | Token::Mod => "multiplicative",
          Token::Eof => "end",
          Token::Ident(_) => "name",
      }
  }

  fn main() {
      print(category(Token::Plus))         // "additive"
      print(category(Token::Slash))        // "multiplicative"
      print(category(Token::Eof))          // "end"
      print(category(Token::Ident("x")))   // "name"
  }
  ```

- [ ] `tests/golden/51_match_guards_and_or.mn` — NEW, combining both:

  ```mapanare
  fn describe(opt: Option<Int>) -> String {
      match opt {
          Some(0) | None => "zero or absent",
          Some(x) if x > 0 && x < 10 => "small positive",
          Some(x) if x > 0 => "large positive",
          Some(x) if x < 0 => "negative",
          _ => "unreachable",
      }
  }

  fn main() {
      print(describe(Some(0)))    // "zero or absent"
      print(describe(None))       // "zero or absent"
      print(describe(Some(5)))    // "small positive"
      print(describe(Some(42)))   // "large positive"
      print(describe(Some(-1)))   // "negative"
  }
  ```

### Phase 3.2: Parser tests

- [ ] `tests/parser/test_match_guards.py`:
  - `test_simple_guard_parses`
  - `test_guard_with_complex_expression_parses` — `if x > 0 && y < 10`
  - `test_guard_with_function_call_parses` — `if is_valid(x)`
  - `test_guard_before_arrow` — `case x if x > 0 => ...` not `case x => if x > 0 ...`
  - `test_guard_cannot_be_missing_condition` — `case x if =>` is a parse error

- [ ] `tests/parser/test_match_or_patterns.py`:
  - `test_simple_or_pattern_parses` — `A | B`
  - `test_or_of_three_parses` — `A | B | C`
  - `test_or_in_constructor_parses` — `Some(A | B)`
  - `test_or_with_wildcard_parses` — `A | _` (useful pattern)
  - `test_mixed_or_and_bind` — `Some(x) | None` (should error at semantic, but parse cleanly)
  - `test_or_with_guard_parses` — `A | B if x => ...`

### Phase 3.3: Semantic tests

- [ ] `tests/semantic/test_match_guards.py`:
  - `test_guard_bool_accepted`
  - `test_guard_int_rejected` — expect rustc-quality error "guard must have type Bool"
  - `test_guard_string_rejected`
  - `test_guard_sees_pattern_bindings` — `case Some(x) if x > 0 =>` works because `x` is in scope
  - `test_unguarded_exhaustive_passes` — unguarded arms provide full coverage
  - `test_only_guarded_arms_non_exhaustive` — guard-only coverage triggers non-exhaustive error
  - `test_guard_fall_through_semantics` — a guarded arm that fails falls to the next arm

- [ ] `tests/semantic/test_match_or_patterns.py`:
  - `test_or_same_bindings_accepted` — `(Some(x), None) | (None, Some(x))` — `x` bound consistently
  - `test_or_different_bindings_rejected` — `Some(v) | None` — `v` only in one alt, error
  - `test_or_different_types_rejected` — `(Some(x: Int), None) | (None, Some(x: String))` — type mismatch, error
  - `test_or_no_bindings_accepted` — `Plus | Minus` — no bindings, trivial consistency
  - `test_or_exhaustive_coverage` — or-pattern expands to multiple rows, exhaustiveness includes all

### Phase 3.4: LLVM/runtime tests

- [ ] `tests/llvm/test_match_guards.py`:
  - `test_guard_compiles_to_brcond` — inspect emitted IR, verify `br i1` pattern
  - `test_guard_fall_through_runtime` — compile + run, verify first guard failure falls to second arm
  - `test_guard_with_side_effects_in_condition` — guard evaluates in the right order, side effects visible

- [ ] `tests/llvm/test_match_or_patterns.py`:
  - `test_or_compiles_to_one_action_block` — inspect emitted IR, verify the action block is emitted exactly once
  - `test_or_runs_all_alternatives` — each alternative reaches the action at runtime when matched
  - `test_or_with_bindings_runs_correctly` — the action block sees the right binding

### Phase 3.5: Self-hosted regression

- [ ] `tests/self_hosted/test_match_guards_or.py` — compile all three new goldens through `mnc-stage1`, verify output.

---

## Phase 4 — LOW item sweep

v4.35.0 sweeps 3 more LOW items from the v4.31.0 panel tail.

### Phase 4.1: `ssl_load_library` CAS-before-init (3rd cycle, Viper M7)

- [ ] `runtime/native/mapanare_io.c:317-369` — the `loaded = 1; available = ...; ...` pattern CAS's `loaded` before `available` gets its final value. A loser thread can observe `loaded == 1, available == 0` during the winner's mid-init window.
- [ ] Fix: use `pthread_once` / `InitOnceExecuteOnce` (the pattern v4.28.0 used everywhere else). The init callback sets both fields before marking the once-init complete.
- [ ] Test: stress-test `__mn_http_get` from 8 threads simultaneously; verify no thread observes an inconsistent `(loaded, available)` state.
- [ ] This was flagged at v3.47.0 by Viper as LOW, re-flagged at v4.26.0, and it's surprising that the v4.28.0 `pthread_once` sweep missed it. v4.35.0 closes it.

### Phase 4.2: `s_bcrypt` cache thread safety (3rd cycle)

- [ ] `runtime/native/mapanare_io.c:1241-1249` — `static HMODULE s_bcrypt`, `static fn_BCryptGenRandom s_bcrypt_gen`, non-atomic check-then-set pattern.
- [ ] Fix: same `pthread_once` / `InitOnceExecuteOnce` pattern. Move the load into a once-init callback.
- [ ] Test: Windows-specific, may be skipped in CI but the POSIX equivalent (if any) needs the same fix.

### Phase 4.3: `s_net_initialized` non-atomic (5th cycle)

- [ ] `runtime/native/mapanare_io.c:89-116` — `s_net_initialized` is a plain `int`, checked at lines 92, 115, 150 without atomic ops.
- [ ] Fix: same `pthread_once` pattern. Move net init into a callback.
- [ ] Test: stress-test from multiple threads that each call a net-init-dependent function; verify init runs exactly once.
- [ ] 5th cycle — this has been open since v3.47.0.

---

## Phase 5 — Documentation

- [ ] `docs/SPEC.md` §Pattern Matching — new subsections:
  - **Guards** — document the syntax, the `Bool` type requirement, the fall-through semantics, the "guards don't affect exhaustiveness" rule
  - **Or-patterns** — document the syntax, the binding-compatibility rule, the action-shared semantics, the interaction with exhaustiveness
- [ ] `docs/cookbook.md` §Pattern Matching — add "Guards" and "Or-patterns" subsections with practical examples:
  - Guards: classifying integers by sign and magnitude
  - Or-patterns: lexer token categorization (the v4.35.0 `50_match_or_patterns.mn` example, abbreviated)
  - Combined: option/result destructuring with symmetry (the v4.35.0 `51_match_guards_and_or.mn` example)
- [ ] `docs/reference.md` §Pattern syntax — update to include guards + or-patterns
- [ ] `check_docs_drift.py` — the new code blocks in SPEC/cookbook/reference must parse. Run the gate.

---

## Phase 6 — Delta review

- [ ] `.reviews/deltas/v4.35.0-guards-or-patterns.md` — prep file:
  - PR diff summary
  - Links to the three new goldens
  - Specific design decisions to fact-check:
    - Guard fall-through semantics (does a guard failure really jump to the next arm's decision tree, not the next arm's action?)
    - Exhaustiveness rule for guards (guards don't count toward coverage — is this what the reviewer expects?)
    - Or-pattern binding compatibility (names + types must match across alternatives — stricter than some languages; Swift allows type subsumption)
    - Or-pattern row expansion vs decision-tree native handling (which did we pick, and why?)
    - Byte-identity invariant still holds after adding two new syntactic forms

- [ ] **Delta reviewer: Coral** (language design, new syntax, comparison to Rust/Swift/OCaml)
- [ ] **Cross-check reviewer: Rattler** (the guard lowering is the risky part — a guard failure that doesn't correctly reach the next arm's decision-tree root is a subtle bug that produces wrong runtime behavior)

- [ ] Reviewer verdict recorded. FAIL blocks merge. PASS WITH NOTES is acceptable if notes are filed as v4.36.0 (the panel release) items.

---

## Phase 7 — Closeout

- [ ] Full validation: black, ruff, mypy, pytest, golden, stage2, fixed-point (**must still be 0**), CHANGELOG honesty, docs drift, hollow features, silent skips
- [ ] `bash scripts/verify_fixed_point.sh` — 0 lines diff. If guards or or-patterns introduced a divergence, this fails and the release slips until it converges.
- [ ] `VERSION` bumped to 4.35.0
- [ ] `CHANGELOG.md [4.35.0]` entry — honest, every backticked path resolves, every test name exists
- [ ] `docs/roadmap/v4/v4.35.0/SESSION_REPORT.md` — written, fact-checkable
- [ ] `.reviews/CARRY_FORWARD.md` — 3 LOW rows CLOSED (Viper M7, s_bcrypt, s_net_initialized)
- [ ] `.reviews/deltas/v4.35.0-guards-or-patterns.md` — committed with delta review verdict

---

## Exit criteria (22 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Guards parse at the right precedence (after pattern, before `=>`) | `tests/parser/test_match_guards.py` all cases pass |
| 2 | Or-patterns parse at pattern level | `tests/parser/test_match_or_patterns.py` all cases pass |
| 3 | Guard semantic check requires `Bool` type | `test_guard_int_rejected`, `test_guard_string_rejected` pass |
| 4 | Or-pattern semantic check requires consistent bindings | `test_or_different_bindings_rejected`, `test_or_different_types_rejected` pass |
| 5 | Guards don't affect exhaustiveness | `test_only_guarded_arms_non_exhaustive` passes |
| 6 | Or-patterns expand row coverage correctly | `test_or_exhaustive_coverage` passes |
| 7 | Guards lower to post-match BrCond with fall-through | `test_guard_compiles_to_brcond` passes |
| 8 | Or-patterns compile the action block exactly once | `test_or_compiles_to_one_action_block` passes |
| 9 | Guard fall-through runtime behavior is correct | `test_guard_fall_through_runtime` passes |
| 10 | Or-pattern runtime behavior is correct for all alternatives | `test_or_runs_all_alternatives` passes |
| 11 | Self-hosted pipeline compiles guards | `scripts/test_native.py --stage1` passes |
| 12 | Self-hosted pipeline compiles or-patterns | same |
| 13 | **Fixed-point diff is still 0 lines** | `verify_fixed_point.sh` output |
| 14 | `49_match_guards.mn` golden runs and produces expected output | golden harness |
| 15 | `50_match_or_patterns.mn` golden runs | same |
| 16 | `51_match_guards_and_or.mn` golden runs | same |
| 17 | Delta review returns PASS (or PASS WITH NOTES) | `.reviews/deltas/v4.35.0-guards-or-patterns.md` |
| 18 | SPEC + cookbook + reference updated, `check_docs_drift.py` clean | CI gate |
| 19 | LOW: `ssl_load_library` uses `pthread_once` | Phase 4.1 evidence |
| 20 | LOW: `s_bcrypt` uses `pthread_once` (or Windows equivalent) | Phase 4.2 evidence |
| 21 | LOW: `s_net_initialized` uses `pthread_once` | Phase 4.3 evidence |
| 22 | `SESSION_REPORT.md` written | file exists |

---

## What v4.35.0 explicitly does NOT do

- **Range patterns** (`case 1..10 => ...`) — out of scope. Natural for a follow-up release if user feedback demands it; the decision-tree infrastructure can handle it.
- **Pattern bindings with `@`** (`case x @ Some(42) => ...`) — "bind the whole value, also match the pattern." Useful but not urgent. v5.x backlog.
- **Implicit `From` conversion for or-pattern types** — if alternatives bind `x: Int32` and `x: Int64`, we reject rather than widen. Strict rule; can be relaxed later if painful.
- **Guards that move values** — Rust's guard-before-bind-by-move dance doesn't apply here because Mapanare doesn't have move semantics the way Rust does. Ignore.
- **Exhaustiveness warnings for guard-only coverage** — we upgrade to compile errors. Consistent with the v4.34.0 exhaustiveness upgrade.
- **Dual-path lowering** to allow the old behavior — no. Wholesale replacement, same as v4.34.0.
- **Guards on or-pattern alternatives individually** (`case A | B if foo => ...` — does the guard apply to both alternatives, or just B?). Answer: **the guard applies to the whole arm**, following Rust. `A | B if foo` means "A or B, and also foo is true." Document explicitly.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Guard fall-through semantics is subtly wrong | medium | high | Rattler cross-check; `test_guard_fall_through_runtime` is a specific regression test for the fall-through path; Rust's implementation is the reference |
| The byte-identity invariant breaks when guards are added | medium | high | Both pipelines must use the same guard-lowering algorithm; Phase 1.7 and Phase 2.7 are dedicated fixed-point checks; if either fails, the release slips |
| Or-pattern parsing conflicts with bitwise-OR at expression level | low | medium | Grammar position disambiguates; Phase 2.1 includes a specific parse-conflict test |
| Or-pattern binding-type-compatibility rule is stricter than users expect | medium | low | SPEC explicitly documents; if user feedback demands widening, it's a v4.36.0+ relaxation |
| Guards interact badly with or-patterns in an edge case we didn't anticipate | medium | medium | `51_match_guards_and_or.mn` goldens combine them; delta reviewer specifically tests the interaction |
| Delta reviewer says "split this into two releases" | low-medium | low | Acceptable: or-patterns become v4.35.1 point release. Or-pattern implementation is isolated enough to split without surgery |
| LOW sweep items in `mapanare_io.c` uncover a larger systemic issue | low | medium | Phase 4 items are all the same pattern (`pthread_once`); if they cascade, time-box and file the residual as a new HIGH for v4.36.0 |

---

## Reference

- [`docs/roadmap/v4/v4.34.0/DESIGN.md`](../v4.34.0/DESIGN.md) — the decision-tree algorithm this release builds on
- [`docs/roadmap/v4/POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 1 — roadmap context
- [`.reviews/REVIEW_CADENCE.md`](../../../../.reviews/REVIEW_CADENCE.md) §Delta triggers — why two new syntactic forms need delta review
- Rust Reference §Match expressions — https://doc.rust-lang.org/reference/expressions/match-expr.html (reference for guard semantics and or-pattern bindings)
- Maranget (2008) — same paper referenced in v4.34.0 DESIGN.md; §5 covers or-patterns
- OCaml manual §6.8 "Pattern matching" — or-patterns are called "or-patterns" there too; syntax is identical

---

## After v4.35.0

v4.36.0 is the **arc-1 panel release** — the first 5-minor cadence panel since v4.31.0. Scope is deliberately quiet:
- Sweep the residual LOW items from the v4.31.0 panel tail that didn't land in v4.32.0–v4.35.0
- Drain `CARRY_FORWARD.md` of items closed opportunistically in the arc
- Documentation polish (cookbook chapters for `?`, match guards, or-patterns should all be complete)
- Measurement refresh: fresh `culebra summary`, benchmark run
- Pre-panel audit: every v4.32.0–v4.35.0 SESSION_REPORT claim fact-checked against file:line
- **Full 7-reviewer panel runs against v4.36.0 tag**
- Arc 1 officially closes on the panel verdict

See [`docs/roadmap/v4/v4.36.0/PLAN.md`](../v4.36.0/PLAN.md) (to be written as v4.36.0 approaches — the panel release pattern is well-established and doesn't need to be written weeks in advance).
